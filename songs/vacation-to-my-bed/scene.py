"""Vacation (To My Bed) — the risograph postcard, with a boarding pass.

Uses the five reel illustrations (out of office / packing / travel time / welcome / wish you were here).
16:9: the illustration as a tilted postcard on warm risograph paper, big synced lyrics on the right in coral and teal,
a boarding pass (FROM: DESK  TO: BED  FLIGHT TIME: 4 SEC) and passport stamps that slam on every chorus.
9:16: the illustration full-frame with the lyric in a paper label inside the safe frame.
"""
import os, math
import numpy as np, cv2
from PIL import Image
from studio import core as C
from studio import kit as K
from studio.core import sstep, ease_out, ease_io, hexc, clamp, sprite, blit, text_w, shadow, F_INTER, F_DISP, F_DISPB, F_MONO, F_MONOB, WHITE

HERE = os.path.dirname(os.path.abspath(__file__))
TM = C.Timing(HERE)
TAIL = 4.0
SONG_END = TM.duration
DUR = SONG_END + TAIL
LINES = TM.lines
TM.stamps = []; TM.stamp_word = None
def lt(sub, nth=0):
    try: return TM.line_t(sub, nth)
    except Exception: return 1e9
def sec(n): return TM.section(n)
def bp(t, k=7.0): return TM.beat_pulse(t, k)

PAPER = hexc('f3e7d3'); PAPER2 = hexc('ead9bd'); CORAL = hexc('e8473b'); TEAL = hexc('1f4f5a'); INKC = hexc('2a2326')
PEACHC = hexc('f6b49a'); CREAM = hexc('fffaf0')

IMGS = [np.asarray(Image.open(os.path.join(HERE, "img", f"{i}.png")).convert("RGB")).astype(np.float32) / 255 for i in range(5)]
OUT, PACK, TRAVEL, WELCOME, BED = range(5)

# image schedule: (start time, image)
SCHED = [(0.0, OUT)]
for L in LINES:
    tx = L['text'].lower(); s = L['s'] - 0.38   # picture lands just before the line, so a clip that starts on the line opens on the right image
    if L['sec'] in ("PRE1", "PRE2") and tx.startswith(("packed", "phone")): SCHED.append((s, PACK if L['sec'] == "PRE1" else BED))
    elif "goin' on vacation" in tx: SCHED.append((s, TRAVEL))
    elif tx.startswith("five-star"): SCHED.append((s, WELCOME))
    elif tx.startswith(("out of office", "do not disturb")): SCHED.append((s, BED))
    elif tx.startswith("the view"): SCHED.append((s, WELCOME))
    elif tx.startswith("forecast"): SCHED.append((s, BED))
    elif tx.startswith("so i booked"): SCHED.append((s, TRAVEL))
    elif tx.startswith("one-way"): SCHED.append((s, OUT))
    elif tx.startswith("wish you"): SCHED.append((s, BED))
SCHED.sort()
def img_at(t):
    cur, t0 = OUT, 0.0
    for s, k in SCHED:
        if t >= s: cur, t0 = k, s
    return cur, t0

def kb(im, t, t0, W, H, k):
    """Ken Burns: slow zoom in/out alternating per cut."""
    z = 1.0   # no zoom: the hand-lettered titles run right to the picture edges, so any crop cuts letters off
    h, w = im.shape[:2]
    cw, ch = w / z, h / z; x0 = (w - cw) / 2; y0 = (h - ch) / 2 + (h - ch) * 0.1 * math.sin(k)
    M = np.array([[W / cw, 0, -x0 * W / cw], [0, H / ch, -y0 * H / ch]], np.float32)
    return cv2.warpAffine(im, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

_PAP = {}
def paper(W, H):
    if (W, H) not in _PAP:
        r = np.random.default_rng(2)
        n = cv2.GaussianBlur(r.normal(0, 1, (H // 2, W // 2)).astype(np.float32), (0, 0), 1.2)
        n = cv2.resize(n, (W, H))[..., None]
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        dots = (0.5 + 0.5 * np.sin(xx * 0.35) * np.sin(yy * 0.35))[..., None]
        base = PAPER * (1 - 0.05 * dots) + n * 0.018
        _PAP[(W, H)] = base.astype(np.float32)
    return _PAP[(W, H)].copy()

def postcard(img, t, W, H, ts, cx, cy, ph, ang):
    k, t0 = img_at(t)
    pw = int(ph * 9 / 16); ph = int(ph)
    pic = kb(IMGS[k], t, t0, pw, ph, int(t0 * 7))
    # crossfade from the previous image for 0.25 s
    prevs = [s for s in SCHED if s[0] < t0]
    if prevs and t - t0 < 0.25:
        pk, pt0 = prevs[-1][1], prevs[-1][0]
        a = sstep(t0, t0 + 0.25, t)
        pic = kb(IMGS[pk], t, pt0, pw, ph, int(pt0 * 7)) * (1 - a) + pic * a
    bd = int(18 * ts)
    card = np.ones((ph + 2 * bd, pw + 2 * bd, 3), np.float32) * CREAM
    card[bd:bd + ph, bd:bd + pw] = pic
    hh, ww = card.shape[:2]; big = int(math.hypot(hh, ww)) + 4
    M = cv2.getRotationMatrix2D((ww / 2, hh / 2), ang, 1.0); M[0, 2] += (big - ww) / 2; M[1, 2] += (big - hh) / 2
    rc = cv2.warpAffine(card, M, (big, big)); rm = cv2.warpAffine(np.ones((hh, ww), np.float32), M, (big, big))
    x, y = int(cx - big / 2), int(cy - big / 2)
    X0, Y0, X1, Y1 = max(0, x), max(0, y), min(W, x + big), min(H, y + big)
    sh = cv2.GaussianBlur(rm, (0, 0), 14 * ts)
    sx, sy = int(10 * ts), int(16 * ts)
    reg = img[Y0 + sy:Y1 + sy, X0 + sx:X1 + sx]; ss = sh[Y0 - y:Y0 - y + reg.shape[0], X0 - x:X0 - x + reg.shape[1]][..., None]
    reg *= (1 - 0.35 * ss)
    m = rm[Y0 - y:Y1 - y, X0 - x:X1 - x][..., None]
    img[Y0:Y1, X0:X1] = img[Y0:Y1, X0:X1] * (1 - m) + rc[Y0 - y:Y1 - y, X0 - x:X1 - x] * m

_BG = {}
def _bg_blur(k, W, H):
    if (k, W, H) not in _BG:
        im = cv2.resize(IMGS[k], (W, H), interpolation=cv2.INTER_AREA)
        im = cv2.GaussianBlur(im, (0, 0), min(W, H) / 40)
        _BG[(k, W, H)] = (im * 0.55 + PAPER * 0.45).astype(np.float32)
    return _BG[(k, W, H)].copy()

def cur_line(t):
    starts = [L['s'] for L in LINES]
    i = int(np.searchsorted(starts, t + 0.3)) - 1
    return i

def lyrics_side(img, t, x0, x1, ycen, W, H, ts):
    """Big karaoke lines in coral (current), teal (previous/next ghosts)."""
    if C.STATE["clean"]: return
    i = cur_line(t)
    if i < 0: return
    flt = C.STATE["lyric_filter"]
    maxw = x1 - x0
    def layout(L, fs):
        words = [(w.strip(), tt) for w, tt in zip(L['words'], L['wt'])]
        sp = text_w(" ", F_DISP, fs); rows = [[]]; cw = 0
        for w, tt in words:
            ww = text_w(w, F_DISP, fs)
            if rows[-1] and cw + sp + ww > maxw: rows.append([]); cw = 0
            rows[-1].append((w, tt, ww)); cw += ww + sp
        return rows, sp
    L = LINES[i]
    if flt is not None and not flt(L): return
    nxt = LINES[i + 1]['s'] if i + 1 < len(LINES) else 1e9
    vis = sstep(L['s'] - 0.3, L['s'], t) * (1 - sstep(max(L['e'] + 1.2, L['s'] + 2.5), max(L['e'] + 1.6, L['s'] + 2.9), t)) if t < nxt - 0.3 else 1.0
    fs = int(96 * ts)
    rows, sp = layout(L, fs)
    while len(rows) > 3 and fs > 60: fs -= 6; rows, sp = layout(L, fs)
    lh = fs * 1.18; y0 = ycen - (len(rows) - 1) * lh / 2 - fs * 0.6
    for ri, row in enumerate(rows):
        x = x0
        for w, tt, ww in row:
            on = t >= tt - 0.05
            hit = math.exp(-max(0, t - tt) * 4) if on else 0
            col = CORAL if on else TEAL * 0.35 + PAPER * 0.65
            dy = -8 * ts * hit
            blit(img, sprite(w, F_DISP, fs), x, y0 + ri * lh + dy, col, vis)
            x += ww + sp
    # previous line, small, above
    if i > 0 and t - L['s'] < 2.5:
        P = LINES[i - 1]
        blit(img, sprite(P['text'], F_DISPB, int(44 * ts)), x0, y0 - 80 * ts, TEAL, 0.55 * vis * (1 - sstep(L['s'] + 1.5, L['s'] + 2.5, t)))

def label_caption(img, t, W, H, ts):
    """9:16: current line in a paper label inside the safe frame (kept a bit smaller so it never gets cut off)."""
    if C.STATE["clean"]: return
    i = cur_line(t)
    if i < 0: return
    L = LINES[i]
    flt = C.STATE["lyric_filter"]
    if flt is not None and not flt(L): return
    nxt = LINES[i + 1]['s'] if i + 1 < len(LINES) else 1e9
    vis = sstep(L['s'] - 0.25, L['s'], t) * (1 - sstep(max(L['e'] + 0.6, L['s'] + 2.0), max(L['e'] + 1.0, L['s'] + 2.4), t)) if t < nxt - 0.25 else 1.0
    if vis <= 0.01: return
    fs = int(54 * ts); maxw = W * 0.74
    words = [(w.strip(), tt) for w, tt in zip(L['words'], L['wt'])]
    sp = text_w(" ", F_DISP, fs); rows = [[]]; cw = 0
    for w, tt in words:
        ww = text_w(w, F_DISP, fs)
        if rows[-1] and cw + sp + ww > maxw: rows.append([]); cw = 0
        rows[-1].append((w, tt, ww)); cw += ww + sp
    lh = fs * 1.22
    bw = max(sum(r[2] for r in row) + sp * (len(row) - 1) for row in rows) + fs * 1.2
    bh = lh * len(rows) + fs * 0.7
    cy = H * 0.665; y0 = cy - bh / 2
    K.panel(img, W / 2 - bw / 2, y0, bw, bh, CREAM, 0.94 * vis, r=int(fs * 0.35), shadow_op=0.35)
    for ri, row in enumerate(rows):
        x = W / 2 - (sum(r[2] for r in row) + sp * (len(row) - 1)) / 2; y = y0 + fs * 0.32 + ri * lh
        for w, tt, ww in row:
            on = t >= tt - 0.05
            blit(img, sprite(w, F_DISP, fs), x, y, CORAL if on else TEAL * 0.55 + CREAM * 0.45, vis)
            x += ww + sp

def boarding_pass(img, t, W, H, ts, x, y, w):
    a = sstep(0.3, 1.0, t) * (1 - sstep(lt("Two weeks") - 0.5, lt("Two weeks"), t))
    if a <= 0.01: return
    h = w * 0.42
    K.panel(img, x, y, w, h, CREAM, a, r=int(24 * ts), shadow_op=0.4)
    K.panel(img, x, y, w, h * 0.24, CORAL, a, r=int(24 * ts), shadow_op=0)
    blit(img, sprite("BOARDING PASS", F_MONOB, int(42 * ts)), x + 36 * ts, y + h * 0.05, CREAM, a)
    cols = [("FROM", "DESK"), ("TO", "BED"), ("FLIGHT", "4 SEC")]
    for i, (k_, v) in enumerate(cols):
        cx = x + 40 * ts + i * w * 0.32
        blit(img, sprite(k_, F_MONOB, int(34 * ts)), cx, y + h * 0.34, TEAL, a)
        blit(img, sprite(v, F_DISP, int(76 * ts)), cx, y + h * 0.50, INKC, a)
    blit(img, sprite("GATE: hallway   SEAT: all of it", F_MONOB, int(34 * ts)), x + 40 * ts, y + h * 0.82, TEAL, a)

STAMPS = []
for L in LINES:
    if "goin' on vacation" in L['text'].lower():
        STAMPS.append(L['s'])
STAMP_TXT = ["ARRIVED: BED", "DO NOT DISTURB", "5-STAR", "ARRIVED: BED", "OUT OF OFFICE", "ARRIVED: BED"]
def stamps(img, t, W, H, ts, region):
    x0, y0, x1, y1 = region
    for j, s in enumerate(STAMPS):
        if t < s: continue
        age = t - s
        o = sstep(0, 0.05, age) * (1 - sstep(9.0, 10.0, age))
        if o <= 0.01: continue
        rng = np.random.default_rng(j + 3)
        cx = rng.uniform(x0, x1); cy = rng.uniform(y0, y1)
        txt = STAMP_TXT[j % len(STAMP_TXT)]
        sc = 1 + 0.8 * math.exp(-age * 14)
        fs = int(58 * ts * sc)
        sp = sprite(txt, F_DISP, fs)
        a = sp[0]; h_, w_ = a.shape; pad = int(fs * 0.35)
        tile = np.zeros((h_ + pad * 2, w_ + pad * 2), np.float32)
        cv2.rectangle(tile, (pad // 3, pad // 3), (tile.shape[1] - pad // 3, tile.shape[0] - pad // 3), 1.0, max(3, int(fs * 0.08)), cv2.LINE_AA)
        tile[pad:pad + h_, pad:pad + w_] = np.maximum(tile[pad:pad + h_, pad:pad + w_], a)
        rot = rng.uniform(-14, 14)
        big = int(max(tile.shape) * 1.2)
        M = cv2.getRotationMatrix2D((tile.shape[1] / 2, tile.shape[0] / 2), rot, 1.0); M[0, 2] += (big - tile.shape[1]) / 2; M[1, 2] += (big - tile.shape[0]) / 2
        tr = cv2.warpAffine(tile, M, (big, big))
        x, y = int(cx - big / 2), int(cy - big / 2)
        X0, Y0, X1, Y1 = max(0, x), max(0, y), min(W, x + big), min(H, y + big)
        if X1 <= X0 or Y1 <= Y0: continue
        m = tr[Y0 - y:Y1 - y, X0 - x:X1 - x][..., None] * o * 0.85
        col = CORAL if j % 2 == 0 else TEAL
        img[Y0:Y1, X0:X1] = img[Y0:Y1, X0:X1] * (1 - m) + col * m

def render_frame(t, W=1920, H=1080, fi=0):
    vert = H > W; ts = min(W, H) / 1080
    tt = min(t, SONG_END)
    if vert:
        # the whole illustration as a big postcard (nothing cropped), over a soft blurred copy of itself
        k, t0 = img_at(tt)
        img = _bg_blur(k, W, H)
        z = 1.0 + 0.025 * ease_io(clamp((tt - t0) / 6.0, 0, 1)) + 0.008 * bp(tt, 6)
        postcard(img, tt, W, H, ts, W * 0.5, H * 0.465, H * 0.80 * z, -1.6 + 0.6 * math.sin(tt * 0.3))
        label_caption(img, tt, W, H, ts)
    else:
        img = paper(W, H)
        postcard(img, tt, W, H, ts, W * 0.235, H * 0.5, H * 0.86, -2.5 + 0.8 * math.sin(tt * 0.3))
        if not C.STATE["clean"]:
            blit(img, sprite("VACATION (TO MY BED)", F_MONOB, int(36 * ts), track=int(6 * ts)), W * 0.47, H * 0.075, TEAL, 0.9)
            blit(img, sprite("aditazzz", F_DISPB, int(36 * ts)), W * 0.47, H * 0.075 + 48 * ts, CORAL, 0.9)
            boarding_pass(img, tt, W, H, ts, W * 0.47, H * 0.17, W * 0.46)
            stamps(img, tt, W, H, ts, (W * 0.60, H * 0.26, W * 0.88, H * 0.42))
            lyrics_side(img, tt, W * 0.47, W * 0.95, H * 0.74, W, H, ts)
            C.subscribe_pill(img, t, W, H, lt("To my bed", 1) + 2.0, 5.5)
    if not C.STATE["clean"]:
        C.end_screen(img, t, W, H, SONG_END - 2.5, DUR - SONG_END + 2.5, "Wish you were here.", sub_line="Subscribe for a new song every week",
                     title="Vacation (To My Bed)", accent=CORAL)
    return C.finish(img, t, fi, DUR, flash=0.0, glitch_amt=0.0, ca=0.0, vignette=False)
