"""Captions as their own layer, for 9:16 (Reels, Shorts, the Instagram cuts).

The rules (docs/lessons.md): captions never take precedence over the video. They sit on the dark, quiet parts of the frame,
never over the subject, and they are plain white words (no particles, no effects that cross the picture). The 3D
masters are rendered caption-free, so the caption-free version of every cut costs nothing extra: it is the same
render with draw() switched off.

    plan(get_frame, lines, W, H)  -> {line index: y}   y = centre of the caption block, as a fraction of H
    draw(img, t, W, H, lines, place)                  img: float32 HxWx3 in 0..1, drawn in place

From the command line (writes the placement file the scene reads, and prints the plan):
    python -m studio.caplayer plan <caption-free master.mp4 | frames dir> <timed.json> <out.json> [--skip 15,31] [--end 30=134.75]
"""
import os, sys, json, math, argparse
import numpy as np, cv2
from . import core as C

FS = 0.037                  # font size as a fraction of H: 71 px at 1920 (the readability floor is 58 px)
LH = 1.18                   # line height, x font size
MAXW = 0.66                 # the caption column: centred, 66% wide, clear of the Reels/Shorts buttons on the right
Y_TOP, Y_BOT = 0.07, 0.86   # the whole caption block stays between these
FONT = C.F_DISPB
WHITE = np.array([0.957, 0.957, 0.949], np.float32)


def fsize(H): return max(int(round(H * FS)), int(math.ceil(58 * H / 1920)))


_LAY = {}
def layout(words, W, H):
    """as few rows as fit the column, then the most even split into that many rows (no lone word on the last row)."""
    key = (tuple(words), W, H)
    if key in _LAY: return _LAY[key]
    fs = fsize(H); sp = C.text_w(" ", FONT, fs); ww = [C.text_w(w, FONT, fs) for w in words]; n = len(words)
    rw = lambda a, b: sum(ww[a:b]) + sp * (b - a - 1)
    import itertools
    best = None
    for nrow in range(1, n + 1):                      # the fewest rows that fit, then the most even split
        for cuts in itertools.combinations(range(1, n), nrow - 1):
            b = (0, *cuts, n); m = max(rw(b[j], b[j + 1]) for j in range(nrow))
            if m > MAXW * W and nrow < n: continue
            m *= 1 - 0.12 * sum(words[c - 1][-1:] in ',.?!:;' for c in cuts)      # break after punctuation when it's close
            if best is None or m < best[0]: best = (m, b)
        if best: break
    b = best[1] if best else (0, n)
    rows = [[(k, words[k], ww[k]) for k in range(b[j], b[j + 1])] for j in range(len(b) - 1)]
    _LAY[key] = (fs, sp, rows); return _LAY[key]


def spans(lines, skip=(), ends=None):
    """(i, on, off) for each captioned line: on a little before the first word, off a little after the line (or just
    before the next one, so two lines never stack)."""
    ends = ends or {}; keep = [i for i in range(len(lines)) if i not in skip]; out = []
    for n, i in enumerate(keep):
        L = lines[i]; nxt = lines[keep[n + 1]]["s"] if n + 1 < len(keep) else 1e9
        off = min(L["e"] + 1.2, nxt - 0.13, ends.get(i, 1e9))
        out.append((i, L["s"] - 0.2, off))
    return out


def block_h(words, W, H):
    fs, sp, rows = layout(words, W, H); return (len(rows) * fs * LH + fs * 0.5) / H, len(rows)


# ------------------------------------------------------------------------------------------ placement
def _features(fr):
    """per-row darkness/quietness features of one frame, on a 270x480 analysis copy: luminance, its 90th percentile,
    and edge density (detail = the subject)."""
    g = cv2.cvtColor(cv2.resize(fr, (270, 480), interpolation=cv2.INTER_AREA), cv2.COLOR_RGB2GRAY).astype(np.float32) / 255
    x0, x1 = int(270 * (0.5 - MAXW / 2 - 0.03)), int(270 * (0.5 + MAXW / 2 + 0.03))
    col = g[:, x0:x1]
    gb = cv2.GaussianBlur(g, (0, 0), 1.0)
    e = np.hypot(cv2.Sobel(gb, cv2.CV_32F, 1, 0), cv2.Sobel(gb, cv2.CV_32F, 0, 1))[:, x0:x1]
    return col, np.clip(e * 2.5, 0, 1)


def plan(get_frame, lines, W, H, fps=30, skip=(), ends=None, step=0.2, prefer=0.78, stick=0.06, avoid=(), middle=0.45, log=print):
    """For each line, the band (of the line's own height) that stays darkest and quietest while the line is on
    screen, judged on the caption-free master. get_frame(frame index) -> RGB uint8 (any size).
    avoid: [(t0, t1, y0, y1)] bands kept clear while they overlap the line (e.g. a Short's hook box in its first 3 s)."""
    ys = np.round(np.arange(Y_TOP, Y_BOT + 1e-6, 0.005), 3); out = {}; prev = None; cache = {}
    for i, a, b in spans(lines, skip, ends):
        bh, nrow = block_h(lines[i]["words"], W, H); half = bh / 2 + 0.012
        cand = ys[(ys - half >= Y_TOP) & (ys + half <= Y_BOT)]
        ts = np.arange(max(0.0, a + 0.1), max(a + 0.11, b), step)
        cost = np.zeros(len(cand)); prevcol = None; nt = 0
        for t in ts:
            fi = int(round(t * fps))
            if fi not in cache:
                if len(cache) > 600: cache.clear()
                cache[fi] = _features(get_frame(fi))
            col, e = cache[fi]
            mot = np.abs(col - prevcol) if prevcol is not None else np.zeros_like(col); prevcol = col
            for n, y in enumerate(cand):
                r0, r1 = int((y - half) * 480), int(math.ceil((y + half) * 480))
                band, be, bm = col[r0:r1], e[r0:r1], mot[r0:r1]
                cost[n] += band.mean() + 0.8 * np.percentile(band, 92) + 1.6 * be.mean() + 2.0 * bm.mean()
            nt += 1
        cost /= max(1, nt)
        for t0, t1, y0, y1 in avoid:
            if a < t1 and b + 0.4 > t0: cost += 10 * ((cand + half > y0) & (cand - half < y1))
        # the subject is framed in the middle: the darkest band of a close-up is often the subject itself (a phone
        # screen, a face, the robot's chest), so the middle third only wins when it is clearly emptier than the edges
        cost += middle * np.clip(1 - np.abs(cand - 0.5) / 0.2, 0, 1)
        cost += 0.08 * np.abs(cand - prefer)                                   # all else equal: the usual lower third
        if prev is not None: cost += stick * (np.abs(cand - prev) > 0.02)       # and don't jump around for nothing
        k = int(np.argmin(cost)); y = float(cand[k]); out[i] = {"y": round(y, 3), "rows": nrow, "cost": round(float(cost[k]), 3)}
        prev = y
        if log: log(f"{i:3d} y={y:.3f} rows={nrow} cost={cost[k]:.3f}  {lines[i]['text']}")
    return out


# ------------------------------------------------------------------------------------------ drawing
def _norm(w): return "".join(ch for ch in w.lower() if ch.isalpha())


def draw(img, t, W, H, lines, place, skip=(), ends=None, redact=(), default_y=0.78):
    """plain white words that fade in as they're sung and fade out together; a soft dark shadow, no box."""
    redact = {_norm(w) for w in redact}; drew = False; flt = C.STATE.get("lyric_filter")
    for i, a, b in spans(lines, skip, ends):
        if t < a or t > b: continue
        if flt is not None and not flt(lines[i]): continue                    # the cuts hide stray lines at their joins
        out = 1 - C.sstep(b - 0.3, b, t)                                     # gone before the next line's first word
        if out <= 0.003: continue
        L = lines[i]; fs, sp, rows = layout(L["words"], W, H); lh = fs * LH
        p = place.get(i, place.get(str(i))) if place else None
        yc = (p["y"] if isinstance(p, dict) else (p if p is not None else default_y)) * H
        f = C.font(FONT, fs); asc, desc = f.getmetrics()
        for ri, row in enumerate(rows):
            rw = sum(r[2] for r in row) + sp * (len(row) - 1); x = (W - rw) / 2
            ymid = yc - (len(rows) - 1) * lh / 2 + ri * lh; ytop = ymid - (asc + desc) / 2
            # over a bright shot (fog, a white sky) white needs more than a drop shadow: a soft, wide dark halo
            # that hugs the words (no box), stronger the brighter the picture under them
            ya, yb, xa, xb = int(max(0, ymid - fs * 0.6)), int(min(H, ymid + fs * 0.6)), int(max(0, x)), int(min(W, x + rw))
            lum = float(img[ya:yb, xa:xb].mean()) if yb > ya and xb > xa else 0.0
            halo = C.sstep(0.32, 0.72, lum)
            for k, w, ww in row:
                op = C.sstep(L["wt"][k] - 0.12, L["wt"][k] + 0.08, t) * out
                if op > 0.01:
                    if _norm(w) in redact:                                    # sung, never shown: a white bar
                        bh = fs * 0.62; y0 = int(ymid - bh / 2); x0 = int(x)
                        reg = img[y0:y0 + int(bh), x0:x0 + int(ww)]; reg *= (1 - op); reg += op * WHITE
                    else:
                        spr = C.sprite(w, FONT, fs, max(2, int(fs * 0.22)))
                        if halo > 0.02: C.shadow(img, C.sprite(w, FONT, fs, max(4, int(fs * 0.55))), x, ytop, 0.75 * halo * op)
                        C.shadow(img, spr, x, ytop + fs * 0.05, 0.92 * op)
                        C.blit(img, spr, x, ytop, WHITE, op)
                    drew = True
                x += ww + sp
    return drew


def load_place(path):
    if not os.path.exists(path): return {}
    d = json.load(open(path)); return {int(k): v for k, v in d.items()}


# ------------------------------------------------------------------------------------------ CLI
class _Src:
    def __init__(self, p):
        self.dir = p if os.path.isdir(p) else None; self.cap = None if self.dir else cv2.VideoCapture(p); self.next = 0
    def __call__(self, fi):
        if self.dir:
            for ext in ("jpg", "png"):
                f = os.path.join(self.dir, f"f_{fi:05d}.{ext}")
                if os.path.exists(f): return cv2.cvtColor(cv2.imread(f), cv2.COLOR_BGR2RGB)
            raise SystemExit(f"missing frame {fi} in {self.dir}")
        if fi != self.next: self.cap.set(cv2.CAP_PROP_POS_FRAMES, fi)
        ok, fr = self.cap.read(); self.next = fi + 1
        return cv2.cvtColor(fr, cv2.COLOR_BGR2RGB) if ok else np.zeros((1600, 900, 3), np.uint8)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("cmd"); ap.add_argument("src"); ap.add_argument("timed"); ap.add_argument("out")
    ap.add_argument("--skip", default=""); ap.add_argument("--end", default=""); ap.add_argument("--W", type=int, default=1080); ap.add_argument("--H", type=int, default=1920)
    a = ap.parse_args()
    lines = json.load(open(a.timed)); skip = {int(x) for x in a.skip.split(",") if x}
    ends = {int(k): float(v) for k, v in (kv.split("=") for kv in a.end.split(",") if kv)}
    res = plan(_Src(a.src), lines, a.W, a.H, skip=skip, ends=ends)
    json.dump({str(k): v for k, v in res.items()}, open(a.out, "w"), indent=1); print("wrote", a.out)
