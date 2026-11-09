"""S6 ink: the drawing kit of "The Daily Standup", copied from songs/ted-talk-charts/scene.py (her TED Talk (Charts) video)
so verse 3 prints in exactly the same newspaper: cream paper with a fold, black ink, one red, blue ballpoint notes.
Landscape only (the v3 film is 16:9). Additions for this section: printed clippings (her X posts, multiplied into the
paper like newsprint), a rubber stamp, agent glyphs, her avatar, and a soft spotlight."""
import os, math
import numpy as np, cv2
from studio import core as C
from studio.core import sstep, ease_out, ease_io, clamp, lerp, hexc

HERE = os.path.dirname(os.path.abspath(__file__))
F32 = np.float32

def FONT(n):
    """our static instances first (assets/fonts may hold the variable Google fonts, which PIL renders at weight 400)"""
    p = os.path.join(HERE, "s6_fonts", n)
    return p if os.path.exists(p) else os.path.join(C.FONTS, n)

F_MAST = FONT("PlayfairDisplaySC-Regular.ttf")
F_HEAD = FONT("EBGaramond-SemiBold.ttf")
F_ITAL = FONT("EBGaramond-MediumItalic.ttf")
F_SANS = FONT("Inter-SemiBold.otf")
F_SANSM = FONT("Inter-Medium.otf")
F_NUM = FONT("InterDisplay-Black.otf")
F_NUMB = FONT("InterDisplay-Bold.otf")
F_MONO = FONT("JBMono-700.ttf")
F_PEN = FONT("Caveat-Medium.ttf")
F_TAB = FONT("Anton-Regular.ttf")

# ---------------------------------------------------------------- palette (same as TED Talk (Charts))
PAPER = hexc('f2ece1'); CARD = hexc('fbf7ef'); INK = hexc('171513'); INK2 = hexc('3d3832'); MUTE = hexc('8a8378')
RULE = hexc('cbc2b2'); GRID = hexc('ddd5c7'); BAR = hexc('b4ab9c'); RED = hexc('d93a2b'); REDL = hexc('f2a093')
PEN = hexc('2448a8'); PENL = hexc('9fb3e6'); GHOST = hexc('a9bccf'); CREAM = hexc('fbf4e6')

# ---------------------------------------------------------------- canvas: design units (1920x1080) -> pixels
SHB = 4; SCL = 1 << SHB
class Cv:
    def __init__(s, img, W, H):
        s.img = img; s.W = W; s.H = H
        s.DW, s.DH = 1920, 1080
        s.k = W / s.DW
        s.cx, s.cy, s.z = s.DW / 2, s.DH / 2, 1.0
        s.dx = 0.0; s.dy = 0.0; s.op = 1.0
        s.box = (170, 196, 1580, 836)
    def X(s, x): return s.W / 2 + (x + s.dx - s.cx) * s.z * s.k
    def Y(s, y): return s.H / 2 + (y + s.dy - s.cy) * s.z * s.k
    def L(s, v): return v * s.z * s.k

def _paint(cv, P, draw, pad, col, op):
    op *= cv.op
    if op <= 0.003: return
    x0 = int(math.floor(P[:, 0].min() - pad)); y0 = int(math.floor(P[:, 1].min() - pad))
    x1 = int(math.ceil(P[:, 0].max() + pad)) + 1; y1 = int(math.ceil(P[:, 1].max() + pad)) + 1
    X0, Y0, X1, Y1 = max(0, x0), max(0, y0), min(cv.W, x1), min(cv.H, y1)
    if X1 <= X0 or Y1 <= Y0: return
    m = np.zeros((y1 - y0, x1 - x0), np.uint8)
    Q = np.round((P - [x0, y0]) * SCL).astype(np.int32)
    draw(m, Q)
    a = m[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0].astype(F32) * (op / 255.0)
    reg = cv.img[Y0:Y1, X0:X1]
    reg *= (1 - a[..., None]); reg += a[..., None] * col

def _px(cv, pts): return np.array([[cv.X(x), cv.Y(y)] for x, y in pts], np.float64)

def fill(cv, pts, col, op=1.0):
    P = _px(cv, pts)
    _paint(cv, P, lambda m, Q: cv2.fillPoly(m, [Q], 255, cv2.LINE_AA, shift=SHB), 3, col, op)

def stroke(cv, pts, col, wd=2.0, op=1.0, closed=False):
    P = _px(cv, pts); w = cv.L(wd)
    if w < 1.0: op *= max(0.25, w); w = 1.0
    t = max(1, int(round(w)))
    _paint(cv, P, lambda m, Q: cv2.polylines(m, [Q], closed, 255, t, cv2.LINE_AA, shift=SHB), t + 3, col, op)

def dashed(cv, pts, col, wd=2.0, op=1.0, dash=14, gap=10, prog=1.0):
    pts = np.asarray(pts, np.float64); seg = np.hypot(*np.diff(pts, axis=0).T); tot = seg.sum() * prog
    cum = np.concatenate([[0], np.cumsum(seg)])
    def at(d):
        i = min(len(seg) - 1, np.searchsorted(cum, d, side='right') - 1); u = (d - cum[i]) / max(seg[i], 1e-9)
        return pts[i] + (pts[i + 1] - pts[i]) * u
    d = 0.0
    while d < tot:
        e = min(tot, d + dash); stroke(cv, [at(d), at((d + e) / 2), at(e)], col, wd, op); d = e + gap

def circ_pts(cx, cy, r, n=72, a0=0.0, a1=2 * math.pi, ry=None):
    ry = r if ry is None else ry
    return [(cx + r * math.cos(a0 + (a1 - a0) * i / n), cy + ry * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]

def circle(cv, cx, cy, r, col, op=1.0, wd=None):
    if r <= 0.05: return
    if wd is None: fill(cv, circ_pts(cx, cy, r, 64)[:-1], col, op)
    else: stroke(cv, circ_pts(cx, cy, r, 72), col, wd, op, closed=True)

def rrect_pts(x, y, w, h, r):
    r = min(r, w / 2, h / 2); P = []
    for cx, cy, a0 in ((x + w - r, y + r, -math.pi / 2), (x + w - r, y + h - r, 0), (x + r, y + h - r, math.pi / 2), (x + r, y + r, math.pi)):
        for i in range(7): a = a0 + i * (math.pi / 2) / 6; P.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return P

def rect(cv, x, y, w, h, col, op=1.0, r=0, wd=None):
    if w <= 0 or h <= 0: return
    pts = rrect_pts(x, y, w, h, r) if r > 0 else [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
    if wd is None: fill(cv, pts, col, op)
    else: stroke(cv, pts, col, wd, op, closed=True)

def wedge(cv, cx, cy, r0, r1, a0, a1, col, op=1.0):
    n = max(3, int(abs(a1 - a0) / 0.04))
    outer = [(cx + r1 * math.cos(a0 + (a1 - a0) * i / n), cy + r1 * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]
    inner = [(cx + r0 * math.cos(a1 - (a1 - a0) * i / n), cy + r0 * math.sin(a1 - (a1 - a0) * i / n)) for i in range(n + 1)]
    fill(cv, outer + inner, col, op)

def arrow(cv, pts, col, wd=3.0, op=1.0, head=16, prog=1.0, dash=False):
    pts = np.asarray(pts, np.float64)
    if prog <= 0: return
    if prog < 1.0:
        seg = np.hypot(*np.diff(pts, axis=0).T); cum = np.concatenate([[0], np.cumsum(seg)]); d = cum[-1] * clamp(prog)
        i = min(len(seg) - 1, np.searchsorted(cum, d, side='right') - 1); u = (d - cum[i]) / max(seg[i], 1e-9)
        pts = np.vstack([pts[:i + 1], pts[i] + (pts[i + 1] - pts[i]) * u])
    if len(pts) < 2 or np.hypot(*(pts[-1] - pts[0])) < 1: return
    if dash: dashed(cv, pts, col, wd, op)
    else: stroke(cv, pts, col, wd, op)
    if prog >= 0.98:
        p1, p0 = pts[-1], pts[-2]; d = p1 - p0; n = np.hypot(*d)
        if n > 1e-6:
            d /= n; q = np.array([-d[1], d[0]])
            fill(cv, [p1 + d * 2, p1 - d * head + q * head * 0.55, p1 - d * head - q * head * 0.55], col, op)

# ---------------------------------------------------------------- text
def text(cv, s, x, y, font, size, col, op=1.0, ax='l', ay='m', track=0):
    op *= cv.op
    if op <= 0.004 or not s: return 0.0
    px = max(6, int(round(size * cv.z * cv.k)))
    if px > 900: return 0.0
    spr = C.sprite(s, font, px, 0, track=int(round(track * cv.z * cv.k)) if track else 0)
    h, w = spr[0].shape
    asc, desc = C.font(font, px).getmetrics()
    X = cv.X(x); Y = cv.Y(y)
    if ax == 'c': X -= w / 2
    elif ax == 'r': X -= w
    if ay == 'm': Y -= asc - 0.36 * px
    elif ay == 'b': Y -= asc
    elif ay == 't': Y -= asc - 0.74 * px
    C.blit(cv.img, spr, X, Y, col, op)
    return w / (cv.z * cv.k)

def tw(s, font, size, track=0):
    if not s: return 0.0
    if track:
        f = C.font(font, max(6, int(size))); return sum(f.getbbox(ch)[2] for ch in s) + track * (len(s) - 1)
    return C.text_w(s, font, max(6, int(size)))

def fit(s, font, size, maxw, lo=20):
    while size > lo and tw(s, font, size) > maxw: size -= 2
    return size

def wrap(s, font, size, maxw):
    words = s.split(); rows = [""]
    for w in words:
        cand = (rows[-1] + " " + w).strip()
        if rows[-1] and tw(cand, font, size) > maxw: rows.append(w)
        else: rows[-1] = cand
    return rows

# ---------------------------------------------------------------- the blue pen (narrator) and the red marker
def _smooth_noise(seed, n, amp):
    r = np.random.default_rng(seed); v = r.normal(0, 1, n + 8)
    v = np.convolve(v, np.ones(7) / 7, mode='same')[4:4 + n]
    return v * amp

def _resample(pts, step=6.0):
    pts = np.asarray(pts, np.float64); out = [pts[0]]
    for a, b in zip(pts[:-1], pts[1:]):
        d = np.hypot(*(b - a)); k = max(1, int(d / step))
        for i in range(1, k + 1): out.append(a + (b - a) * i / k)
    return np.array(out)

def pen(cv, pts, prog, seed=0, wd=4.6, col=PEN, op=0.92, jit=2.0):
    if prog <= 0: return
    P = _resample(pts)
    if len(P) < 2: return
    d = np.diff(P, axis=0); nrm = np.stack([-d[:, 1], d[:, 0]], 1); nrm /= np.maximum(np.hypot(nrm[:, 0], nrm[:, 1])[:, None], 1e-9)
    nrm = np.vstack([nrm, nrm[-1:]])
    P = P + nrm * _smooth_noise(seed, len(P), jit)[:, None]
    n = max(2, int(len(P) * clamp(prog)))
    stroke(cv, P[:n], col, wd, op)

def pen_ellipse(cv, cx, cy, rx, ry, prog, seed=0, wd=4.6, col=PEN, op=0.92):
    a0 = -2.4 + 0.3 * math.sin(seed); n = 90
    pts = [(cx + rx * (1 + 0.05 * math.sin(i * 0.21 + seed)) * math.cos(a0 + 2 * math.pi * 1.1 * i / n),
            cy + ry * (1 + 0.06 * math.cos(i * 0.17 + seed)) * math.sin(a0 + 2 * math.pi * 1.1 * i / n)) for i in range(n + 1)]
    pen(cv, pts, prog, seed, wd, col, op, jit=1.2)

def pen_arrow(cv, p0, p1, prog, seed=0, bend=0.25, wd=4.6, col=PEN, op=0.92):
    p0 = np.array(p0, float); p1 = np.array(p1, float); d = p1 - p0; q = np.array([-d[1], d[0]]) * bend
    mid = (p0 + p1) / 2 + q
    pts = [(1 - u) ** 2 * p0 + 2 * (1 - u) * u * mid + u * u * p1 for u in np.linspace(0, 1, 40)]
    pen(cv, pts, min(1, prog / 0.8), seed, wd, col, op, jit=1.0)
    if prog > 0.8:
        k = clamp((prog - 0.8) / 0.2); e = pts[-1]; dd = pts[-1] - pts[-4]; dd /= max(np.hypot(*dd), 1e-9); nq = np.array([-dd[1], dd[0]])
        L = 26
        pen(cv, [e, e - dd * L + nq * L * 0.6], k, seed + 1, wd, col, op, jit=0.6)
        pen(cv, [e, e - dd * L - nq * L * 0.6], k, seed + 2, wd, col, op, jit=0.6)

def pen_text(cv, s, x, y, size, prog, ax='l', ay='m', col=PEN, op=0.95):
    if prog <= 0: return 0.0
    k = max(1, int(round(len(s) * clamp(prog * 1.0))))
    full = tw(s, F_PEN, size)
    if ax == 'c': x -= full / 2
    elif ax == 'r': x -= full
    return text(cv, s[:k], x, y, F_PEN, size, col, op, 'l', ay)

def marker(cv, x, y, w, h, prog, col=REDL, op=0.62, seed=0):
    """highlighter swipe behind a word (x,y = left, middle)."""
    if prog <= 0: return
    w2 = w * clamp(prog); sk = _smooth_noise(seed, 4, 3)
    fill(cv, [(x - 6, y - h / 2 + sk[0]), (x + w2 + 6, y - h / 2 + sk[1]), (x + w2 + 8, y + h / 2 + sk[2]), (x - 4, y + h / 2 + sk[3])], col, op)

# ---------------------------------------------------------------- paper, finish
_PAPER = {}
def paper(W, H):
    k = (W, H)
    if k not in _PAPER:
        r = np.random.default_rng(11)
        low = cv2.resize(cv2.GaussianBlur(r.normal(0, 1, (H // 8, W // 8)).astype(F32), (0, 0), 5), (W, H), interpolation=cv2.INTER_CUBIC)
        low /= max(1e-6, np.abs(low).max())
        fib = cv2.GaussianBlur(r.normal(0, 1, (H, W)).astype(F32), (0, 0), 0.8)
        fib2 = cv2.GaussianBlur(r.normal(0, 1, (H, W)).astype(F32), (0, 0), sigmaX=6, sigmaY=0.6)
        img = PAPER[None, None, :] * (1 + 0.022 * low[..., None] + 0.010 * fib[..., None] + 0.008 * fib2[..., None])
        yy, xx = np.mgrid[0:H, 0:W].astype(F32)
        d = np.hypot((xx - W / 2) / (W / 2), (yy - H / 2) / (H / 2))
        img *= (1 - 0.10 * np.clip(d - 0.55, 0, None) ** 1.6)[..., None]
        fy = H * 0.5   # the fold of the newspaper (a soft crease across the middle of the sheet)
        crease = np.exp(-((yy[:, :1] - fy) / (2.2 * W / 1920)) ** 2) * 0.035 - np.exp(-((yy[:, :1] - fy + 5 * W / 1920) / (5 * W / 1920)) ** 2) * 0.012
        img *= (1 - crease)[..., None]
        _PAPER[k] = img.astype(F32)
    return _PAPER[k].copy()

def finish(img, fi):
    H, W = img.shape[:2]; p = C.post(W, H)
    img += cv2.resize(p.grain[fi % 6], (W, H), interpolation=cv2.INTER_NEAREST)[..., None] * 0.011
    return (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)

def halo(cv, s, x, y, font, size, op, track=0):
    """paint paper behind a piece of text so it reads over anything (a knockout)"""
    if op <= 0.01: return
    px = max(6, int(round(size * cv.z * cv.k))); gl = max(4, int(px * 0.10))
    spr = C.sprite(s, font, px, gl, track=int(round(track * cv.z * cv.k)) if track else 0)
    a, g, pad = spr; h, w = a.shape
    asc, _ = C.font(font, px).getmetrics()
    X = int(round(cv.X(x) - (w - 2 * pad) / 2 - pad)); Y = int(round(cv.Y(y) - (asc - 0.36 * px) - pad))
    H, W = cv.img.shape[:2]; X0, Y0, X1, Y1 = max(0, X), max(0, Y), min(W, X + w), min(H, Y + h)
    if X1 <= X0 or Y1 <= Y0: return
    m = np.clip(g[Y0 - Y:Y1 - Y, X0 - X:X1 - X] * 3.0, 0, 1)[..., None] * op * 0.92
    reg = cv.img[Y0:Y1, X0:X1]; reg *= (1 - m); reg += m * PAPER

# ---------------------------------------------------------------- additions for S6
_IMG = {}
def load(path):
    if path not in _IMG:
        im = cv2.imread(path, cv2.IMREAD_COLOR)
        _IMG[path] = None if im is None else cv2.cvtColor(im, cv2.COLOR_BGR2RGB).astype(F32) / 255.0
    return _IMG[path]

_RS = {}
def _resized(key, arr, pw, ph):
    k = (key, pw, ph)
    if k not in _RS:
        if len(_RS) > 64: _RS.clear()
        _RS[k] = cv2.resize(arr, (pw, ph), interpolation=cv2.INTER_AREA if pw < arr.shape[1] else cv2.INTER_CUBIC)
    return _RS[k]

def _region(cv, x, y, w, h):
    X0 = cv.X(x); Y0 = cv.Y(y); pw = max(1, int(round(cv.L(w)))); ph = max(1, int(round(cv.L(h))))
    xi, yi = int(round(X0)), int(round(Y0))
    a0, b0, a1, b1 = max(0, xi), max(0, yi), min(cv.W, xi + pw), min(cv.H, yi + ph)
    return xi, yi, pw, ph, a0, b0, a1, b1

def multiply(cv, key, arr, x, y, w, h, op=1.0):
    """print an image into the paper (multiply blend: its white becomes whatever is underneath, its ink stays ink)"""
    op *= cv.op
    if op <= 0.004 or arr is None: return
    xi, yi, pw, ph, a0, b0, a1, b1 = _region(cv, x, y, w, h)
    if a1 <= a0 or b1 <= b0: return
    src = _resized(key, arr, pw, ph)[b0 - yi:b1 - yi, a0 - xi:a1 - xi]
    reg = cv.img[b0:b1, a0:a1]
    reg *= (1 - op) + op * src

def paste(cv, key, arr, x, y, w, h, op=1.0, mask=None, cache=True):
    """opaque paste (photos / footage), optional float mask (h, w) at the source's own resolution"""
    op *= cv.op
    if op <= 0.004 or arr is None: return
    xi, yi, pw, ph, a0, b0, a1, b1 = _region(cv, x, y, w, h)
    if a1 <= a0 or b1 <= b0: return
    if cache: src = _resized(key, arr, pw, ph)
    else: src = arr if arr.shape[:2] == (ph, pw) else cv2.resize(arr, (pw, ph), interpolation=cv2.INTER_AREA)
    src = src[b0 - yi:b1 - yi, a0 - xi:a1 - xi]
    reg = cv.img[b0:b1, a0:a1]
    if mask is None: m = op
    else: m = _resized(("mask", key), mask, pw, ph)[b0 - yi:b1 - yi, a0 - xi:a1 - xi][..., None] * op
    reg *= (1 - m); reg += src * m

def clipping(cv, key, arr, x, y, s, op=1.0, marks=(), pad=14, shadow=True):
    """one of her X posts printed on the page as a clipping: card, hairline, soft shadow, optional red highlighter
    swipes given in post pixels: [(x0, y0, x1, y1, prog), ...]"""
    if arr is None or op <= 0.004: return
    h0, w0 = arr.shape[:2]; w, h = w0 * s, h0 * s
    if shadow: rect(cv, x - pad + 9, y - pad + 11, w + 2 * pad, h + 2 * pad, INK, 0.10 * op, r=12)
    rect(cv, x - pad, y - pad, w + 2 * pad, h + 2 * pad, CARD, op, r=12)
    for i, (bx0, by0, bx1, by1, pr) in enumerate(marks):
        if pr > 0: marker(cv, x + bx0 * s, y + (by0 + by1) / 2 * s, (bx1 - bx0) * s, (by1 - by0) * s * 1.16, pr, REDL, 0.80 * op, seed=40 + i)
    multiply(cv, key, arr, x, y, w, h, op)
    rect(cv, x - pad, y - pad, w + 2 * pad, h + 2 * pad, INK, op, r=12, wd=1.8)

def stamp(img, cv, s, x, y, size, t0, t, col=RED, ang=-8.0, sub=None, op=1.0, seed=3):
    """a rubber stamp that slams onto the page at t0 (x, y = centre, design units)"""
    u = t - t0
    if u < 0: return
    k = cv.k
    fs = int(round(size * k)); spr = C.sprite(s, F_SANS, fs, 0, track=int(round(size * 0.12 * k)))[0]
    th, tw_ = spr.shape
    sub_spr = C.sprite(sub, F_SANS, int(round(size * 0.42 * k)), 0, track=int(round(size * 0.08 * k)))[0] if sub else None
    pad = int(round(size * 0.34 * k)); bw_ = int(round(5 * k * size / 60)) + 2
    sh = sub_spr.shape if sub_spr is not None else (0, 0)
    W_ = max(tw_, sh[1]) + 2 * pad; H_ = th + (sh[0] + int(pad * 0.2) if sub_spr is not None else 0) + int(pad * 1.2)
    lay = np.zeros((H_, W_), F32)
    cv2.rectangle(lay, (bw_ // 2, bw_ // 2), (W_ - 1 - bw_ // 2, H_ - 1 - bw_ // 2), 1.0, bw_, cv2.LINE_AA)
    ty = int(pad * 0.55); lay[ty:ty + th, (W_ - tw_) // 2:(W_ - tw_) // 2 + tw_] = np.maximum(lay[ty:ty + th, (W_ - tw_) // 2:(W_ - tw_) // 2 + tw_], spr)
    if sub_spr is not None:
        sy = ty + th + int(pad * 0.05); sx = (W_ - sh[1]) // 2
        lay[sy:sy + sh[0], sx:sx + sh[1]] = np.maximum(lay[sy:sy + sh[0], sx:sx + sh[1]], sub_spr)
    # a little ink texture (deterministic)
    r = np.random.default_rng(seed); tex = cv2.resize(r.uniform(0.0, 1.0, (max(2, H_ // 6), max(2, W_ // 6))).astype(F32), (W_, H_), interpolation=cv2.INTER_CUBIC)
    lay *= np.clip(0.80 + 0.35 * tex, 0, 1)
    sc = 1.0 + 0.35 * (1 - ease_out(u / 0.13))
    a_ = ang + 3.0 * (1 - ease_out(u / 0.18))
    M = cv2.getRotationMatrix2D((W_ / 2, H_ / 2), a_, sc)
    M[0, 2] += cv.X(x) - W_ / 2; M[1, 2] += cv.Y(y) - H_ / 2
    H, W = img.shape[:2]
    al = cv2.warpAffine(lay, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    o = sstep(0, 0.04, u) * op * cv.op * 0.92
    a = al[..., None] * o
    img *= (1 - a); img += a * col

def bot(cv, cx, cy, s, col, op=1.0, eye=None):
    """an agent: rounded head, two eyes, an antenna (s = head width)"""
    if op <= 0.004: return
    eye = CREAM if eye is None else eye
    w, h = s, s * 0.80
    stroke(cv, [(cx, cy - h / 2), (cx, cy - h / 2 - s * 0.22)], col, max(2.0, s * 0.06), op)
    circle(cv, cx, cy - h / 2 - s * 0.26, s * 0.075, col, op)
    rect(cv, cx - w / 2, cy - h / 2, w, h, col, op, r=s * 0.24)
    circle(cv, cx - s * 0.19, cy - s * 0.02, s * 0.095, eye, op)
    circle(cv, cx + s * 0.19, cy - s * 0.02, s * 0.095, eye, op)
    stroke(cv, [(cx - s * 0.14, cy + s * 0.20), (cx + s * 0.14, cy + s * 0.20)], eye, max(1.6, s * 0.05), op * 0.9)

def person(cv, x, y, s, col, op=1.0):
    circle(cv, x, y - 46 * s, 22 * s, col, op)
    rect(cv, x - 28 * s, y - 18 * s, 56 * s, 64 * s, col, op, r=22 * s)

_SPOT = {}
def spot(W, H, box):
    k = (W, H, box)
    if k not in _SPOT:
        cv = Cv(None, W, H); x, y, w, h = box
        cx, cy = cv.X(x + w / 2), cv.Y(y + h / 2)
        rx, ry = cv.L(w * 0.56), cv.L(h * 0.60)
        yy, xx = np.mgrid[0:H, 0:W].astype(F32)
        d = ((np.abs(xx - cx) / rx) ** 4 + (np.abs(yy - cy) / ry) ** 4) ** 0.25
        _SPOT[k] = (1 / (1 + d ** 10)).astype(F32)
    return _SPOT[k]

def light(img, a, box):
    """'somebody dim the lights': a = ambient (1 = office lights on); a warm pool stays on the figure"""
    if a > 0.995: return
    H, W = img.shape[:2]; s = spot(W, H, box)[..., None]
    warm = np.array([1.0, 0.975, 0.93], F32); cool = np.array([0.86, 0.86, 0.95], F32)
    tint = 1 + (1 - a) * ((s * warm + (1 - s) * cool) - 1)
    img *= (a + (1 - a) * s) * tint
