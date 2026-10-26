"""Typography for Thirsty (The Data Center Next Door).

  subtitles      the lyrics, one line at a time, centred in the lower letterbox bar (Cormorant Garamond SemiBold,
                 dirty ivory). The whole line is up while it is sung; each word comes up from 55 % as it is sung.
                 Lines too wide for the bar are split at their punctuation, on the sung timing. Drawn after the film
                 finish so they stay crisp (like real subtitles).
  ghost          "thirsty" as a large Instrument Serif italic in the picture, with fading echoes (one per sung echo),
                 drawn into the linear image before the finish so it blooms and grains like light in the haze.
  price          $5 / $10 / $25 in Playfair Display SC, growing more confrontational.
  title          the distressed THIRSTY title with pink drips (frame 0), and aditazzz in pink mono.
"""
import os, math, re
from functools import lru_cache
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
import ys_eng as E
from ys_eng import F32, hexc, sstep, clamp, ease_out, ease_io, sample, fbm_tex

F = E.FONTS
F_SUB = os.path.join(F, "CormorantGaramond-SemiBold.ttf")
F_GHOST = os.path.join(F, "InstrumentSerif-Italic.ttf")
F_DIDONE = os.path.join(F, "PlayfairDisplaySC-Regular.ttf")
F_MONO = os.path.join(F, "JBMono-400.ttf")
F_MONOB = os.path.join(F, "JBMono-700.ttf")
F_SANS = os.path.join(F, "Inter-Medium.otf")
IVORY_D = np.array([236, 226, 203], F32) / 255          # display-space ivory for subtitles
PINK_D = np.array([255, 61, 139], F32) / 255

@lru_cache(64)
def font(path, size): return ImageFont.truetype(path, int(size))

@E.byte_lru(160 * 2 ** 20)
def glyphs(text, path, size, track=0):
    """alpha mask of a text line, with a little padding: (mask, ox, oy) where ox/oy is the pen origin offset."""
    f = font(path, size)
    asc, desc = f.getmetrics()
    if track:
        ws = [f.getlength(ch) for ch in text]; w = int(sum(ws) + track * max(0, len(text) - 1)) + 8
    else:
        w = int(f.getlength(text)) + 8
    pad = int(size * 0.35)
    im = Image.new('L', (w + pad * 2, asc + desc + pad * 2), 0); d = ImageDraw.Draw(im)
    if track:
        x = pad
        for ch, cw in zip(text, ws): d.text((x, pad), ch, font=f, fill=255); x += cw + track
    else: d.text((pad, pad), text, font=f, fill=255)
    return np.asarray(im, F32) / 255, pad, pad

def text_w(text, path, size, track=0):
    f = font(path, size)
    return f.getlength(text) + (track * max(0, len(text) - 1) if track else 0)

def blit(img, mask, x, y, col, op=1.0, add=False):
    """composite a mask at top-left (x, y) into img (float)."""
    H, W = img.shape[:2]; h, w = mask.shape
    x, y = int(round(x)), int(round(y))
    x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0 or op <= 0.002: return
    m = mask[y0 - y:y1 - y, x0 - x:x1 - x][..., None] * op
    reg = img[y0:y1, x0:x1]
    if add: reg += m * np.asarray(col, F32)
    else: reg *= (1 - m); reg += m * np.asarray(col, F32)

# ---------------------------------------------------------------- subtitles
def split_lines(lines, maxw, size):
    """split lyric lines wider than maxw at punctuation nearest the middle (keeps word timings)."""
    out = []
    for L in lines:
        words = [w for w in L['words']]
        disp = [re.sub(r"\s*\(thirsty\)\s*", "", w) for w in words]
        keep = [i for i, w in enumerate(disp) if w]
        if not keep: continue
        words2 = [disp[i] for i in keep]; wt2 = [L['wt'][i] for i in keep]
        text = " ".join(words2)
        if text_w(text, F_SUB, size) <= maxw or len(words2) < 4:
            out.append(dict(L, words=words2, wt=wt2, text=text)); continue
        best, bi = 1e9, None
        for i in range(1, len(words2)):
            if words2[i - 1][-1] in ",:;?." or i == len(words2) // 2:
                left = text_w(" ".join(words2[:i]), F_SUB, size); right = text_w(" ".join(words2[i:]), F_SUB, size)
                score = abs(left - right) - (200 if words2[i - 1][-1] in ",:;?." else 0)
                if max(left, right) <= maxw and score < best: best, bi = score, i
        if bi is None: bi = len(words2) // 2
        a = dict(L, words=words2[:bi], wt=wt2[:bi], text=" ".join(words2[:bi]), e=wt2[bi] - 0.05)
        b = dict(L, words=words2[bi:], wt=wt2[bi:], text=" ".join(words2[bi:]), s=wt2[bi])
        out += [a, b]
    return out

class Subs:
    def __init__(s, timing_lines, W=1920, H=1080, band_h=804):
        s.W, s.H = W, H
        s.size = int(round(74 * H / 1080))
        s.maxw = W * 0.86
        s.lines = split_lines([L for L in timing_lines], s.maxw, s.size)
        for j, L in enumerate(s.lines):          # a line always clears for the next sung line, shown or not
            L['_next'] = s.lines[j + 1]['s'] if j + 1 < len(s.lines) else 1e9
        bar = (H - band_h) // 2
        s.cy = H - bar / 2 + s.size * 0.02

    def draw(s, out, t, filt=None, op_mul=1.0, cy=None, col=None):
        """out: display-space frame (H, W, 3) in [0,1]."""
        vis = [L for L in s.lines if filt is None or filt(L)]
        cy = s.cy if cy is None else cy
        col = IVORY_D if col is None else col
        for i, L in enumerate(vis):
            nxt = L.get('_next', vis[i + 1]['s'] if i + 1 < len(vis) else 1e9)
            a0, a1 = L['s'] - 0.18, L['s'] + 0.02
            end = min(L['e'] + 0.25, nxt - 0.10)
            b0, b1 = end, min(end + 0.28, nxt - 0.02)
            if not (a0 <= t <= b1): continue
            op = sstep(a0, a1, t) * (1 - sstep(b0, b1, t)) * op_mul
            if op <= 0.003: continue
            words = L['words']; size = s.size
            sp = font(F_SUB, size).getlength(" ")
            ws = [font(F_SUB, size).getlength(w) for w in words]
            total = sum(ws) + sp * (len(words) - 1)
            x = s.W / 2 - total / 2
            asc, desc = font(F_SUB, size).getmetrics()
            y_top = cy - (asc * 0.72) / 2 - asc * 0.28
            for w, wt, ww in zip(words, L['wt'], ws):
                k = sstep(wt - 0.10, wt + 0.08, t)
                m, ox, oy = glyphs(w, F_SUB, size)
                blit(out, m, x - ox, y_top - oy, col, op * (0.55 + 0.45 * k))
                x += ww + sp

_END_BAD = {"a", "an", "the", "my", "your", "his", "her", "our", "of", "to", "for", "front", "light", "second", "with", "in", "on"}
_START_OK = {"and", "or", "but", "from", "out", "without", "just", "on", "who's", "with", "every", "cause", "gave", "thinks",
             "a", "the", "like", "you", "get", "when", "baby"}

class SubsV:
    """9:16 lyrics: smaller than the 16:9 ones, wrapped onto balanced rows, centred inside the phone-safe frame
    (studio.core.SAFE_9x16: below the top bar, above the caption block, inside the side crop, left of the buttons),
    over a soft constant scrim so they read on any picture."""
    def __init__(s, timing_lines, W=1080, H=1920, size=50, cx=0.45, cy=0.625, maxw=0.62):
        s.W, s.H = W, H; s.size = int(round(size * W / 1080)); s.cx = cx * W; s.cy = cy * H; s.maxw = maxw * W
        s.lines = []
        for L in timing_lines:
            disp = [re.sub(r"\s*\(thirsty\)\s*", "", w) for w in L['words']]
            keep = [i for i, w in enumerate(disp) if w]
            if keep: s.lines.append(dict(L, words=[disp[i] for i in keep], wt=[L['wt'][i] for i in keep]))
        # fades hand over cleanly: a line is gone before the next one (shown or not) starts to fade in, so two lines
        # never sit on top of each other in the same rows
        prev_out = -1e9
        for j, L in enumerate(s.lines):
            nxt = s.lines[j + 1]['s'] if j + 1 < len(s.lines) else 1e9
            L['_a0'] = max(L['s'] - 0.18, prev_out); L['_a1'] = max(L['_a0'] + 0.12, L['s'] + 0.03)
            end = min(L['e'] + 0.25, nxt - 0.24)
            L['_b0'], L['_b1'] = end, max(end + 0.06, min(end + 0.28, nxt - 0.10))
            prev_out = L['_b1']
        s.rows = [s._wrap(L['words']) for L in s.lines]
        s.lh = s.size * 1.34

    def _wrap(s, words):
        f = font(F_SUB, s.size); sp = f.getlength(" "); ws = [f.getlength(w) for w in words]; n = len(words)
        width = lambda a, b: sum(ws[a:b]) + sp * (b - a - 1)
        best = None
        for nrows in (1, 2, 3, 4):
            cands = []
            if nrows == 1: cands = [()]
            elif nrows == 2: cands = [(i,) for i in range(1, n)]
            elif nrows == 3: cands = [(i, j) for i in range(1, n) for j in range(i + 1, n)]
            else: cands = [(i, j, k) for i in range(1, n) for j in range(i + 1, n) for k in range(j + 1, n)]
            for c in cands:
                cuts = (0,) + c + (n,)
                wid = [width(a, b) for a, b in zip(cuts, cuts[1:])]
                if max(wid) > s.maxw: continue
                pen = max(wid) + sum(0 if words[b - 1][-1] in ",.?!:;" else s.size * 1.5 for b in c)
                pen += sum(s.size * 3 for b in c if words[b - 1].lower().strip(",.?!") in _END_BAD)       # no dangling "a / my / light"
                pen -= sum(s.size * 1.2 for b in c if words[b].lower().strip(",.?!'") in _START_OK)      # a new phrase starts the row
                if best is None or pen < best[0]: best = (pen, cuts)
            if best: break
        cuts = best[1] if best else (0, n)
        return [list(range(a, b)) for a, b in zip(cuts, cuts[1:])]

    def scrim(s, out, amt=0.38):
        """a soft dark band behind the lyric rows (always the same, so it never pumps with the lines)."""
        if not hasattr(s, '_band'):
            yy = np.arange(s.H, dtype=F32)
            s._band = (1 - amt * np.exp(-((yy - s.cy) / (s.lh * 2.2)) ** 2)).astype(F32)[:, None, None]
        out *= s._band

    def draw(s, out, t, filt=None, op_mul=1.0, col=None):
        col = IVORY_D if col is None else col
        vis = [(L, R) for L, R in zip(s.lines, s.rows) if filt is None or filt(L)]
        f = font(F_SUB, s.size); sp = f.getlength(" "); asc = f.getmetrics()[0]
        for L, R in vis:
            a0, a1, b0, b1 = L['_a0'], L['_a1'], L['_b0'], L['_b1']
            if not (a0 <= t <= b1): continue
            op = sstep(a0, a1, t) * (1 - sstep(b0, b1, t)) * op_mul
            if op <= 0.003: continue
            y_mid = s.cy - (len(R) - 1) * s.lh / 2
            for ri, row in enumerate(R):
                ws = [f.getlength(L['words'][i]) for i in row]
                x = s.cx - (sum(ws) + sp * (len(row) - 1)) / 2
                y_top = y_mid + ri * s.lh - (asc * 0.72) / 2 - asc * 0.28
                for i, ww in zip(row, ws):
                    w = L['words'][i]; k = sstep(L['wt'][i] - 0.10, L['wt'][i] + 0.08, t)
                    m, ox, oy = glyphs(w, F_SUB, s.size)
                    sh = cv2.GaussianBlur(m, (0, 0), max(1.5, s.size / 16))
                    blit(out, sh, x - ox + 2, y_top - oy + 3, np.zeros(3, F32), op * 0.75)
                    blit(out, m, x - ox, y_top - oy, col, op * (0.55 + 0.45 * k))
                    x += ww + sp

# ---------------------------------------------------------------- ghost "thirsty"
@E.byte_lru(40 * 2 ** 20)
def _hollow(word, path, sz, k):
    """outline-only version of a word mask (the echo copies are drawn hollow)."""
    m, ox, oy = glyphs(word, path, sz)
    e = cv2.erode(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * k + 1, 2 * k + 1)))
    return np.clip(m - e, 0, 1).astype(F32)

def ghost(img, t, t0, x, y, size, col=None, echoes=(), word="thirsty", life=2.4, drift=(0.0, -0.010), gain=1.0,
          shrink=0.78, step_x=0.0, ts=None):
    """the word appears at t0 (linear image, additive) and holds; each sung echo (times in `echoes`) adds a copy
    stepping down below it: smaller, hollow and softer each time, like a reverb tail walking away. The copies never
    overlap (baselines are spaced by the glyph extents). x, y: centre of the first word as frame fractions."""
    H, W = img.shape[:2]
    col = hexc('ece2cb') * 0.55 if col is None else np.asarray(col, F32)
    t_last = echoes[-1] if len(echoes) else t0
    t_end = t_last + life * 0.75                                  # everything leaves together
    if t < t0 - 0.2 or t > t_end + 0.05: return
    out = 1 - sstep(t_end - 0.7, t_end, t)
    items = [(t0, 0)] + [(te, k + 1) for k, te in enumerate(echoes)]
    grow = 1.0 + 0.025 * max(0.0, t - t0)                          # the whole stack breathes out slowly
    base = None; ts = H / 1080 if ts is None else ts
    for te, k in items:
        sz = max(8, int(size * grow * shrink ** k * ts))
        f = font(F_GHOST, sz); asc = f.getmetrics()[0]; pad = int(sz * 0.35)
        if base is None: base = y * H + 0.235 * sz                 # first baseline: visual centre at y
        else: base += 0.27 * prev + 0.76 * sz                      # descender of the one above + ascender of this one
        prev = sz
        age = t - te
        if age < -0.12: continue
        a = sstep(-0.12, 0.10, age) * out
        if a <= 0.003: continue
        pop = 1.0 + 0.06 * math.exp(-max(0.0, age) * 9)            # a small pop as the echo lands
        m, ox, oy = glyphs(word, F_GHOST, sz)
        tw, th = m.shape[1], m.shape[0]
        cx = (x + step_x * k + drift[0] * (t - t0)) * W
        top = base - pad - asc + drift[1] * (t - t0) * 1080 * ts
        if k == 0:
            halo = cv2.GaussianBlur(m, (0, 0), max(2.0, sz / 10))
            blit(img, halo, cx - tw / 2, top, col * 0.45, a * gain * 0.85, add=True)
            blit(img, m, cx - tw / 2, top, col, a * gain * 0.72, add=True)
        else:
            hk = max(1, int(round(sz / 70)))
            hm = _hollow(word, F_GHOST, sz, hk)
            sig = (0.6 + 1.1 * k) * ts
            hm = cv2.GaussianBlur(hm, (0, 0), sig)
            if abs(pop - 1) > 0.004:
                hm = cv2.resize(hm, None, fx=pop, fy=pop, interpolation=cv2.INTER_LINEAR)
                m = cv2.resize(m, None, fx=pop, fy=pop, interpolation=cv2.INTER_LINEAR)
            th2, tw2 = hm.shape
            X = cx - tw2 / 2; Y = top - (th2 - th) / 2
            op = a * gain * 0.72 * 0.72 ** (k - 1)
            blit(img, cv2.GaussianBlur(m, (0, 0), max(1.5, sz / 14)), X, Y, col * 0.18, op, add=True)
            blit(img, hm, X, Y, col, op * 1.5, add=True)

def kinetic(img, t, rows, x=0.07, gain=1.0, t_out=None, ts=None, center=False):
    """big confrontational type, word by word on the sung times (linear image, before the finish).
    rows: [(y, size, col, [(word, t_word), ...]), ...]; x: left edge (or the centre, center=True) as a frame fraction."""
    H, W = img.shape[:2]
    out = 1.0 if t_out is None else 1 - sstep(t_out - 0.25, t_out, t)
    if out <= 0.003: return
    ts = H / 1080 if ts is None else ts
    for (y, size, col, words) in rows:
        sz = int(size * ts)
        f = font(F_DIDONE, sz); sp = f.getlength(" ") * 1.1; track = int(sz * 0.04)
        X = x * W
        if center:
            X -= (sum(text_w(wd, F_DIDONE, sz, track) for wd, _ in words) + sp * (len(words) - 1)) / 2
        for (wd, tw_) in words:
            age = t - tw_
            wlen = text_w(wd, F_DIDONE, sz, track)
            if age >= -0.04:
                a = sstep(-0.04, 0.06, age) * out * gain
                slam = 1.0 + 0.22 * math.exp(-max(0.0, age) * 16)
                m, ox, oy = glyphs(wd, F_DIDONE, int(sz * slam), track)
                k = max(1, int(sz / 75))
                m = cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * k + 1, 2 * k + 1)))
                asc = font(F_DIDONE, int(sz * slam)).getmetrics()[0]
                yb = y * H                                           # baseline
                X0 = X + wlen / 2 - (m.shape[1] - 2 * ox) / 2 - ox
                Y0 = yb - asc * 1.0 - oy + (asc - font(F_DIDONE, sz).getmetrics()[0]) * 0.0
                glow = cv2.GaussianBlur(m, (0, 0), max(2.0, sz / 16))
                blit(img, glow, X0, Y0, np.asarray(col, F32) * 0.5, a * 0.8, add=True)
                blit(img, m, X0, Y0, np.asarray(col, F32), a)
            X += wlen + sp

# ---------------------------------------------------------------- prices
def price(img, t, t0, label, x, y, size, col, weight=0, life=None, slam=False, track=0, under=False, ts=None, maxw=None):
    """a price tag in the picture (linear, additive glow + solid fill). weight: 0 thin .. 3 heavy (dilation).
    maxw: never wider than this (frame fraction; the 9:16 safe width)."""
    H, W = img.shape[:2]
    ts = H / 1080 if ts is None else ts
    if maxw is not None:
        w0 = text_w(label, F_DIDONE, int(size * ts), track) * 1.25 + size * ts * 0.1   # incl. the slam overshoot
        if w0 > maxw * W: size = size * maxw * W / w0
    age = t - t0
    if age < -0.05: return
    if life is not None and age > life: return
    a = sstep(-0.05, 0.10 if slam else 0.35, age)
    if life is not None: a *= 1 - sstep(life - 0.4, life, age)
    sc = (1.0 + 0.25 * math.exp(-max(0, age) * 14)) if slam else (1.0 + 0.02 * age)
    sz = int(size * sc * ts)
    m, ox, oy = glyphs(label, F_DIDONE, sz, track)
    if weight > 0:
        k = max(1, int(weight * sz / 120))
        m = cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * k + 1, 2 * k + 1)))
    tw, th = m.shape[1], m.shape[0]
    X = x * W - tw / 2; Y = y * H - th / 2
    glow = cv2.GaussianBlur(m, (0, 0), max(2.0, sz / 18))
    blit(img, glow, X, Y, np.asarray(col, F32) * 0.6, a * 0.9, add=True)
    blit(img, m, X, Y, np.asarray(col, F32), a)
    if under:
        yl = int(Y + th * 0.82); x0 = int(X + tw * 0.12); x1 = int(X + tw * 0.88)
        cv2.line(img, (x0, yl), (int(x0 + (x1 - x0) * ease_out(age / 0.4)), yl), (np.asarray(col, F32) * a).tolist(), max(1, int(sz / 60)), cv2.LINE_AA)

# ---------------------------------------------------------------- the title
@lru_cache(4)
def title_mask(W, H, size=330, ts=None, bold=1.0):
    """THIRSTY in a heavy Didone, distressed (worn print), plus the drip anchors under the T and the S.
    bold > 1 thickens the strokes further (the album cover, which is read at thumbnail size)."""
    sz = int(size * (H / 1080 if ts is None else ts))
    m, ox, oy = glyphs("THIRSTY", F_DIDONE, sz, int(sz * 0.02))
    k = max(1, int(sz / 90 * bold))
    m = cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * k + 1, 2 * k + 1)))
    h, w = m.shape
    n1 = sample(fbm_tex(512, 1.2, 111), np.arange(w, dtype=F32)[None, :] * 3.0, np.arange(h, dtype=F32)[:, None] * 3.0, 1.0)
    n2 = sample(fbm_tex(512, 2.0, 112), np.arange(w, dtype=F32)[None, :] * 0.8, np.arange(h, dtype=F32)[:, None] * 0.8, 1.0)
    wear = np.clip((n1 - 0.30) * 3.0, 0, 1) * np.clip((n2 - 0.18) * 4.0, 0, 1)
    speck = (sample(fbm_tex(256, 0.4, 113), np.arange(w, dtype=F32)[None, :] * 2.0, np.arange(h, dtype=F32)[:, None] * 2.0, 1.0) > 0.78)
    mm = np.clip(m * (0.35 + 0.65 * wear) * (1 - speck * 0.8), 0, 1)
    # drip anchors: bottom of the T's stem and of the S (fractions of the word width), like the cover
    f = font(F_DIDONE, sz)
    xT = ox + f.getlength("T") * 0.5
    xS = ox + f.getlength("THIR") + f.getlength("S") * 0.38
    base = oy + f.getmetrics()[0] * 0.98
    return mm.astype(F32), (xT, base), (xS, base)

def title(img, t, x, y, size=330, op=1.0, drip=0.0, col=None, ts=None, center=False, bold=1.0, drip_w=1.0):
    """drawn into the linear image. drip: 0..1 how far the pink drips have run. x, y: top-left (or top-centre,
    center=True) as frame fractions."""
    H, W = img.shape[:2]
    col = hexc('ece2cb') * 0.9 if col is None else col
    m, (xT, bT), (xS, bS) = title_mask(W, H, size, ts, bold)
    X, Y = x * W - (m.shape[1] / 2 if center else 0), y * H
    Href = H if ts is None else ts * 1080                         # drips run the same length as in the 16:9 picture
    blit(img, m, X, Y, col, op)
    # drips: tapering pink runs with a bead at the end
    for (dx, by, L) in ((xT, bT, 0.34), (xS, bS, 0.42)):
        ln = L * Href * ease_io(drip) + 6
        x0 = X + dx; y0 = Y + by
        k = float(drip_w); c_ = 20 * k                            # drip_w: stroke scale (1 = the video's)
        lay = np.zeros((int(ln + 40 * k), int(40 * k)), F32)
        pts = np.array([[c_ - 5 * k, 0], [c_ + 5 * k, 0], [c_ + 2.2 * k, ln * 0.85], [c_ + 3.2 * k, ln], [c_ - 3.2 * k, ln], [c_ - 2.2 * k, ln * 0.85]], F32)
        cv2.fillPoly(lay, [np.round(pts * 4).astype(np.int32)], 1.0, cv2.LINE_AA, shift=2)
        cv2.circle(lay, (int(c_ * 4), int(ln * 4)), int(4.5 * k * 4), 1.0, -1, cv2.LINE_AA, shift=2)
        blit(img, lay, x0 - c_, y0 - 2 * k, hexc('ff3d8b') * 1.4, op)
        blit(img, cv2.GaussianBlur(lay, (0, 0), 4 * k), x0 - c_, y0 - 2 * k, hexc('ff3d8b') * 0.6, op * 0.8, add=True)

def brand(out, x, y, size=40, op=1.0, ts=None, center=False):
    """aditazzz in pink mono (display space)."""
    H, W = out.shape[:2]; ts = H / 1080 if ts is None else ts
    m, ox, oy = glyphs("aditazzz", F_MONO, int(size * ts), int(2 * ts))
    X = x * W - ox - ((m.shape[1] - 2 * ox) / 2 if center else 0)
    blit(out, m, X, y * H - oy, PINK_D, op)
