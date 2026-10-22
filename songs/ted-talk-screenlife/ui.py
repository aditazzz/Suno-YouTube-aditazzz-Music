"""A small vector UI kit for drawing a laptop desktop: rounded rectangles, text, icons, shadows — everything in desktop
units (the laptop screen is 1280 x 720), drawn through a camera onto a float image at the output resolution.
Every element is composited inside its own little region (fast, and crisp at any zoom)."""
import os, math
from functools import lru_cache
import numpy as np, cv2
from studio import core as C

F32 = np.float32
DW, DH = 1280.0, 720.0                       # the desktop, in desktop units
SH = 4; SC = 1 << SH                         # subpixel precision for cv2
FONT = {"r": os.path.join(C.FONTS, "Inter-Regular.otf"), "m": os.path.join(C.FONTS, "Inter-Medium.otf"),
        "s": os.path.join(C.FONTS, "Inter-SemiBold.otf"), "b": os.path.join(C.FONTS, "InterDisplay-Bold.otf"),
        "k": os.path.join(C.FONTS, "InterDisplay-Black.otf"), "l": os.path.join(C.FONTS, "Inter-Light.otf"),
        "mono": os.path.join(C.FONTS, "JBMono-400.ttf"), "hand": os.path.join(C.FONTS, "Caveat-Medium.ttf"),
        "marker": os.path.join(C.FONTS, "PermanentMarker-Regular.ttf")}

def hexc(h): return C.hexc(h)

class Cam:
    """desktop -> screen: the desktop point (cx, cy) lands in the middle of the frame, scaled by s"""
    def __init__(s, W, H, cx, cy, scale):
        s.W, s.H, s.cx, s.cy, s.s = W, H, cx, cy, scale
        s.ox = W / 2 - cx * scale; s.oy = H / 2 - cy * scale
    def P(s, x, y): return x * s.s + s.ox, y * s.s + s.oy
    def L(s, v): return v * s.s
    def visible(s, x, y, w, h, pad=0):
        X0, Y0 = s.P(x, y); X1, Y1 = s.P(x + w, y + h)
        return X1 > -pad and Y1 > -pad and X0 < s.W + pad and Y0 < s.H + pad

class Clip:
    """a screen-space clip rectangle stack (for scrolling panels and windows)"""
    def __init__(s): s.st = []
    def push(s, cam, x, y, w, h):
        X0, Y0 = cam.P(x, y); X1, Y1 = cam.P(x + w, y + h)
        if s.st:
            a = s.st[-1]; X0, Y0, X1, Y1 = max(X0, a[0]), max(Y0, a[1]), min(X1, a[2]), min(Y1, a[3])
        s.st.append((X0, Y0, X1, Y1))
    def pop(s): s.st.pop()
    def get(s, W, H): return s.st[-1] if s.st else (0, 0, W, H)
CLIP = Clip()

# ---------------------------------------------------------------- compositing a mask into the image
def _put(img, mask, ix0, iy0, color, op):
    """mask: uint8 or float (0..1) covering img[iy0:iy0+h, ix0:ix0+w]"""
    H, W = img.shape[:2]
    cx0, cy0, cx1, cy1 = CLIP.get(W, H)
    h, w = mask.shape
    x0, y0 = max(ix0, int(math.floor(cx0)), 0), max(iy0, int(math.floor(cy0)), 0)
    x1, y1 = min(ix0 + w, int(math.ceil(cx1)), W), min(iy0 + h, int(math.ceil(cy1)), H)
    if x1 <= x0 or y1 <= y0: return
    m = mask[y0 - iy0:y1 - iy0, x0 - ix0:x1 - ix0]
    a = (m.astype(F32) / 255.0 if m.dtype == np.uint8 else m) * op
    reg = img[y0:y1, x0:x1]
    col = np.asarray(color, F32)
    if col.ndim == 1:
        reg *= 1 - a[..., None]; reg += a[..., None] * col
    else:                                   # an image the size of the mask
        cc = col[y0 - iy0:y1 - iy0, x0 - ix0:x1 - ix0]
        reg *= 1 - a[..., None]; reg += a[..., None] * cc

def _box(img, X0, Y0, X1, Y1, pad=2):
    H, W = img.shape[:2]
    if not (X1 >= X0 and Y1 >= Y0): return None
    ix0, iy0 = int(math.floor(X0)) - pad, int(math.floor(Y0)) - pad
    ix1, iy1 = int(math.ceil(X1)) + pad, int(math.ceil(Y1)) + pad
    if ix1 <= 0 or iy1 <= 0 or ix0 >= W or iy0 >= H: return None
    return ix0, iy0, ix1, iy1

# ---------------------------------------------------------------- shapes
def rr_pts(x0, y0, x1, y1, r, n=8):
    r = max(0.0, min(r, (x1 - x0) / 2, (y1 - y0) / 2))
    if r < 0.5: return np.array([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], float)
    pts = []
    for cx, cy, a0 in ((x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)):
        for k in range(n + 1):
            a = math.radians(a0 + 90 * k / n); pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return np.array(pts)

def poly_screen(img, polys, color, op=1.0, holes=()):
    """polygons in SCREEN coordinates"""
    if op <= 0.003 or not len(polys): return
    allp = np.concatenate([np.asarray(p, float) for p in polys])
    b = _box(img, allp[:, 0].min(), allp[:, 1].min(), allp[:, 0].max(), allp[:, 1].max())
    if b is None: return
    ix0, iy0, ix1, iy1 = b
    m = np.zeros((iy1 - iy0, ix1 - ix0), np.uint8)
    off = np.array([ix0, iy0], float)
    cv2.fillPoly(m, [np.round((np.asarray(p, float) - off) * SC).astype(np.int32) for p in polys], 255, cv2.LINE_AA, SH)
    if holes: cv2.fillPoly(m, [np.round((np.asarray(p, float) - off) * SC).astype(np.int32) for p in holes], 0, cv2.LINE_AA, SH)
    _put(img, m, ix0, iy0, color, op)

def poly(img, cam, polys, color, op=1.0, holes=()):
    tr = lambda p: np.asarray(p, float) * cam.s + np.array([cam.ox, cam.oy])
    poly_screen(img, [tr(p) for p in polys], color, op, [tr(h) for h in holes])

def stroke(img, cam, pts, w, color, op=1.0, closed=False):
    if op <= 0.003: return
    P = np.asarray(pts, float) * cam.s + np.array([cam.ox, cam.oy]); lw = max(1.0, w * cam.s)
    b = _box(img, P[:, 0].min() - lw, P[:, 1].min() - lw, P[:, 0].max() + lw, P[:, 1].max() + lw)
    if b is None: return
    ix0, iy0, ix1, iy1 = b
    m = np.zeros((iy1 - iy0, ix1 - ix0), np.uint8)
    q = np.round((P - np.array([ix0, iy0])) * SC).astype(np.int32)
    cv2.polylines(m, [q], closed, 255, max(1, int(round(lw))), cv2.LINE_AA, SH)
    _put(img, m, ix0, iy0, color, op)

def rrect(img, cam, x, y, w, h, r, color, op=1.0, border=None, bw=1.0, bop=1.0):
    if w <= 0 or h <= 0: return
    X0, Y0 = cam.P(x, y); X1, Y1 = cam.P(x + w, y + h)
    if color is not None:
        poly_screen(img, [rr_pts(X0, Y0, X1, Y1, r * cam.s)], color, op)
    if border is not None:
        lw = max(1.0, bw * cam.s); hw = lw / 2
        P = rr_pts(X0 + hw, Y0 + hw, X1 - hw, Y1 - hw, max(0, r * cam.s - hw))
        b = _box(img, X0, Y0, X1, Y1)
        if b is None: return
        ix0, iy0, ix1, iy1 = b
        m = np.zeros((iy1 - iy0, ix1 - ix0), np.uint8)
        cv2.polylines(m, [np.round((P - np.array([ix0, iy0])) * SC).astype(np.int32)], True, 255, max(1, int(round(lw))), cv2.LINE_AA, SH)
        _put(img, m, ix0, iy0, border, op * bop)

def circle(img, cam, cx, cy, r, color, op=1.0):
    X, Y = cam.P(cx, cy); R = r * cam.s
    b = _box(img, X - R, Y - R, X + R, Y + R)
    if b is None or op <= 0.003: return
    ix0, iy0, ix1, iy1 = b
    m = np.zeros((iy1 - iy0, ix1 - ix0), np.uint8)
    cv2.circle(m, (int(round((X - ix0) * SC)), int(round((Y - iy0) * SC))), max(1, int(round(R * SC))), 255, -1, cv2.LINE_AA, SH)
    _put(img, m, ix0, iy0, color, op)

def ring(img, cam, cx, cy, r, w, color, op=1.0):
    X, Y = cam.P(cx, cy); R = r * cam.s; lw = max(1.0, w * cam.s)
    b = _box(img, X - R - lw, Y - R - lw, X + R + lw, Y + R + lw)
    if b is None or op <= 0.003: return
    ix0, iy0, ix1, iy1 = b
    m = np.zeros((iy1 - iy0, ix1 - ix0), np.uint8)
    cv2.circle(m, (int(round((X - ix0) * SC)), int(round((Y - iy0) * SC))), max(1, int(round(R * SC))), 255, max(1, int(round(lw))), cv2.LINE_AA, SH)
    _put(img, m, ix0, iy0, color, op)

def shadow(img, cam, x, y, w, h, r, op=0.25, blur=14.0, dy=6.0):
    """a soft drop shadow under a window or card"""
    if op <= 0.003: return
    X0, Y0 = cam.P(x, y + dy); X1, Y1 = cam.P(x + w, y + h + dy); B = blur * cam.s
    b = _box(img, X0 - 3 * B, Y0 - 3 * B, X1 + 3 * B, Y1 + 3 * B)
    if b is None: return
    ix0, iy0, ix1, iy1 = b
    f = max(1, int(B / 3))       # blur at reduced size
    hh, ww = (iy1 - iy0) // f + 2, (ix1 - ix0) // f + 2
    m = np.zeros((hh, ww), np.uint8)
    P = rr_pts((X0 - ix0) / f, (Y0 - iy0) / f, (X1 - ix0) / f, (Y1 - iy0) / f, r * cam.s / f)
    cv2.fillPoly(m, [np.round(P * SC).astype(np.int32)], 255, cv2.LINE_AA, SH)
    a = cv2.GaussianBlur(m.astype(F32) / 255.0, (0, 0), max(0.5, B / f))
    a = cv2.resize(a, (ww * f, hh * f), interpolation=cv2.INTER_LINEAR)[:iy1 - iy0, :ix1 - ix0]
    _put(img, a, ix0, iy0, (0.0, 0.0, 0.0), op)

# ---------------------------------------------------------------- text
@lru_cache(64)
def _metrics(path, px):
    f = C.font(path, px); asc, desc = f.getmetrics(); l, t, r, b = f.getbbox("H")
    return asc, desc, b - t
def text_w(s, size, cam_s=1.0, wt="m"):
    """width in desktop units"""
    px = max(4, int(round(size * cam_s)))
    return C.text_w(s, FONT[wt], px) / cam_s

def text(img, cam, s, x, y, size, color, wt="m", op=1.0, anchor="lm", maxw=None, track=0.0):
    """anchor: [l|c|r][t|m|b] — m = the middle of the capitals, t = top of capitals, b = baseline"""
    if not s or op <= 0.003: return 0.0
    px = int(round(size * cam.s))
    if px < 4: return 0.0
    path = FONT[wt]
    if maxw is not None:
        mw = maxw * cam.s
        if C.text_w(s, path, px) > mw:
            while len(s) > 1 and C.text_w(s + "…", path, px) > mw: s = s[:-1]
            s = s.rstrip() + "…"
    spr = C.sprite(s, path, px, 0, int(round(track * px)) if track else 0)
    a, g, pad = spr
    asc, desc, cap = _metrics(path, px)
    w = a.shape[1] - 4 - 2 * pad
    X, Y = cam.P(x, y)
    if anchor[0] == "c": X -= w / 2
    elif anchor[0] == "r": X -= w
    v = anchor[1] if len(anchor) > 1 else "m"
    base = Y + (cap / 2 if v == "m" else cap if v == "t" else 0)            # screen y of the baseline
    top = base - asc
    H_, W_ = img.shape[:2]
    ix0, iy0 = int(round(X)) - pad, int(round(top)) - pad
    m = a
    _put(img, m, ix0, iy0, color, op)
    return w / cam.s

def text_lines(s, size, maxw, wt="m"):
    """wrap text into lines that fit maxw desktop units (measured at a fixed reference size)"""
    words = s.split(" "); lines = [[]]
    ref = 100.0 / size
    for wd in words:
        trial = " ".join(lines[-1] + [wd])
        if lines[-1] and C.text_w(trial, FONT[wt], 100) / ref > maxw: lines.append([wd])
        else: lines[-1].append(wd)
    return [" ".join(l) for l in lines]

# ---------------------------------------------------------------- icons (24-unit grid, drawn at `size`)
def icon(img, cam, name, x, y, size, color, op=1.0, bg=None):
    """an icon centred at (x, y)"""
    k = size / 24.0
    def T(P): return [(x + (px - 12) * k, y + (py - 12) * k) for px, py in P]
    if name == "mic" or name == "mic_off":
        rrect(img, cam, x - 3.6 * k, y - 9 * k, 7.2 * k, 12.5 * k, 3.6 * k, color, op)
        stroke(img, cam, [(x + (math.cos(a) * 6.3) * k, y + (1.5 + math.sin(a) * 6.3) * k) for a in np.linspace(0.05, math.pi - 0.05, 16)], 1.7 * k, color, op)
        stroke(img, cam, [(x, y + 7.8 * k), (x, y + 10.5 * k)], 1.7 * k, color, op)
        stroke(img, cam, [(x - 3.5 * k, y + 10.6 * k), (x + 3.5 * k, y + 10.6 * k)], 1.7 * k, color, op)
        if name == "mic_off": stroke(img, cam, [(x - 8.5 * k, y - 9 * k), (x + 8.5 * k, y + 10 * k)], 2.0 * k, color, op)
    elif name in ("cam", "cam_off"):
        rrect(img, cam, x - 10 * k, y - 6 * k, 13.5 * k, 12 * k, 2.5 * k, color, op)
        poly(img, cam, [T([(16.2, 9.6), (22, 6.2), (22, 17.8), (16.2, 14.4)])], color, op)
        if name == "cam_off": stroke(img, cam, [(x - 9 * k, y - 9 * k), (x + 9 * k, y + 9.5 * k)], 2.0 * k, color, op)
    elif name == "share":
        rrect(img, cam, x - 10 * k, y - 8 * k, 20 * k, 14 * k, 2 * k, None, op, color, 1.7 * k)
        stroke(img, cam, T([(12, 15), (12, 7)]), 1.7 * k, color, op); stroke(img, cam, T([(8.8, 10), (12, 6.8), (15.2, 10)]), 1.7 * k, color, op)
        stroke(img, cam, T([(8, 22), (16, 22)]), 1.7 * k, color, op)
    elif name == "react":
        ring(img, cam, x, y, 9.5 * k, 1.7 * k, color, op)
        circle(img, cam, x - 3.4 * k, y - 2.5 * k, 1.4 * k, color, op); circle(img, cam, x + 3.4 * k, y - 2.5 * k, 1.4 * k, color, op)
        stroke(img, cam, [(x + 4.8 * math.cos(a) * k, y + (1.4 + 3.6 * math.sin(a)) * k) for a in np.linspace(0.3, math.pi - 0.3, 10)], 1.6 * k, color, op)
    elif name == "hand":
        palm = T([(7.5, 13), (7.5, 7.5), (9.3, 6.6), (10.4, 7.5), (10.4, 4.6), (12.2, 3.8), (13.4, 4.8), (13.4, 4.2), (15.2, 3.6), (16.4, 4.8),
                  (16.4, 7.2), (18.2, 6.8), (19.4, 8.0), (19.4, 15), (17.5, 19.5), (13.6, 21.2), (10.2, 20.0), (5.2, 14.8), (5.6, 12.6), (7.5, 13)])
        poly(img, cam, [palm], color, op)
    elif name == "chat":
        poly(img, cam, [rr_pts(x - 10 * k, y - 8.5 * k, x + 10 * k, y + 5.5 * k, 3.5 * k)], color, op)
        poly(img, cam, [T([(7, 16.5), (7, 22), (12.5, 16.5)])], color, op)
    elif name == "people":
        circle(img, cam, x - 3.5 * k, y - 4.5 * k, 3.6 * k, color, op)
        poly(img, cam, [[(x - 3.5 * k + 6.8 * k * math.cos(a), y + 9 * k + 6.8 * k * math.sin(a) * 0.95) for a in np.linspace(math.pi, 2 * math.pi, 16)]], color, op)
        circle(img, cam, x + 5.5 * k, y - 3.5 * k, 2.9 * k, color, op * 0.8)
        poly(img, cam, [[(x + 5.5 * k + 5.4 * k * math.cos(a), y + 8 * k + 5.4 * k * math.sin(a) * 0.95) for a in np.linspace(math.pi, 2 * math.pi, 16)]], color, op * 0.8)
    elif name == "cc":
        rrect(img, cam, x - 10.5 * k, y - 7.5 * k, 21 * k, 15 * k, 3 * k, None, op, color, 1.7 * k)
        text(img, cam, "CC", x, y + 0.3 * k, 8.4 * k, color, "b", op, "cm")
    elif name == "dots":
        for dx in (-6, 0, 6): circle(img, cam, x + dx * k, y, 1.9 * k, color, op)
    elif name == "phone":     # hang up
        P = [(x + 11 * k * math.cos(a), y + 2 * k + 6 * k * math.sin(a)) for a in np.linspace(math.pi * 1.05, math.pi * 1.95, 18)]
        stroke(img, cam, P, 4.2 * k, color, op)
    elif name == "record":
        circle(img, cam, x, y, 5 * k, color, op)
    elif name == "wifi":
        for i, r in enumerate((3.0, 6.6, 10.2)):
            stroke(img, cam, [(x + r * math.cos(a) * k, y + 6 * k + r * math.sin(a) * k) for a in np.linspace(-math.pi * 0.78, -math.pi * 0.22, 10)], 1.8 * k, color, op)
        circle(img, cam, x, y + 6 * k, 1.5 * k, color, op)
    elif name == "battery":
        rrect(img, cam, x - 11 * k, y - 5.5 * k, 19.5 * k, 11 * k, 2.6 * k, None, op, color, 1.4 * k)
        rrect(img, cam, x - 9.2 * k, y - 3.7 * k, 13.5 * k, 7.4 * k, 1.4 * k, color, op)
        rrect(img, cam, x + 9 * k, y - 2.2 * k, 1.8 * k, 4.4 * k, 0.8 * k, color, op)
    elif name == "search":
        ring(img, cam, x - 2 * k, y - 2 * k, 6 * k, 1.8 * k, color, op)
        stroke(img, cam, [(x + 2.4 * k, y + 2.4 * k), (x + 8 * k, y + 8 * k)], 2.0 * k, color, op)
    elif name == "send":
        poly(img, cam, [T([(3, 4), (21, 12), (3, 20), (6, 12)])], color, op)
    elif name == "check":
        stroke(img, cam, T([(5, 12.5), (10, 17.5), (19, 7)]), 2.2 * k, color, op)
    elif name == "x":
        stroke(img, cam, T([(6, 6), (18, 18)]), 2.0 * k, color, op); stroke(img, cam, T([(18, 6), (6, 18)]), 2.0 * k, color, op)
    elif name == "warn":
        poly(img, cam, [T([(12, 3), (22, 20.5), (2, 20.5)])], color, op)
    elif name == "lock":
        rrect(img, cam, x - 7 * k, y - 1 * k, 14 * k, 10 * k, 2 * k, color, op)
        stroke(img, cam, [(x + 4.5 * k * math.cos(a), y - 1 * k + 5.5 * k * math.sin(a)) for a in np.linspace(math.pi, 2 * math.pi, 12)], 2.0 * k, color, op)
    elif name == "grid":
        for dx in (-5.5, 5.5):
            for dy in (-5.5, 5.5): rrect(img, cam, x + dx * k - 4.4 * k, y + dy * k - 4.4 * k, 8.8 * k, 8.8 * k, 1.6 * k, color, op)
    elif name == "speaker":
        rrect(img, cam, x - 10 * k, y - 8 * k, 20 * k, 12 * k, 1.8 * k, color, op)
        for dx in (-7, -2.3, 2.3, 7): rrect(img, cam, x + dx * k - 2 * k, y + 5.5 * k, 4 * k, 3 * k, 0.8 * k, color, op * 0.7)
    elif name == "bell":
        P = T([(12, 3.5), (16.5, 6), (17.5, 12), (19.5, 16.5), (4.5, 16.5), (6.5, 12), (7.5, 6)])
        poly(img, cam, [P], color, op); circle(img, cam, x, y + 7 * k, 2.2 * k, color, op)
    elif name == "plus":
        stroke(img, cam, T([(12, 5), (12, 19)]), 2.0 * k, color, op); stroke(img, cam, T([(5, 12), (19, 12)]), 2.0 * k, color, op)

# ---------------------------------------------------------------- the mouse pointer
def cursor(img, cam, x, y, size=1.0, op=1.0, click=0.0):
    """an arrow pointer with its tip at (x, y); click: 0..1, a ring that expands"""
    if op <= 0.003: return
    if click > 0:
        ring(img, cam, x, y, (6 + 16 * click) * size, 1.6 * size, (0.30, 0.45, 1.0), op * (1 - click) * 0.9)
    k = size * 0.62
    P = [(0, 0), (0, 17.5), (4.1, 13.6), (7.0, 20.0), (9.6, 18.9), (6.8, 12.6), (12.4, 12.4)]
    P = [(x + px * k, y + py * k) for px, py in P]
    poly(img, cam, [[(px + 0.9 * size, py + 1.6 * size) for px, py in P]], (0, 0, 0), op * 0.25)
    poly(img, cam, [P], (1, 1, 1), op)
    stroke(img, cam, P, 1.15 * size, (0.04, 0.04, 0.05), op, closed=True)

# ---------------------------------------------------------------- curves
_BASIS = {}
def _basis(n):
    if n not in _BASIS:
        u = np.linspace(0, 1, n, endpoint=False)
        _BASIS[n] = 0.5 * np.stack([-u + 2 * u ** 2 - u ** 3, 2 - 5 * u ** 2 + 3 * u ** 3, u + 4 * u ** 2 - 3 * u ** 3, -u ** 2 + u ** 3], 1)
    return _BASIS[n]

def smooth(P, n=6, closed=True):
    """Catmull-Rom through the points"""
    P = np.asarray(P, float); m = len(P)
    if closed:
        idx = np.arange(m); i0, i1, i2, i3 = (idx - 1) % m, idx, (idx + 1) % m, (idx + 2) % m
    else:
        idx = np.arange(m - 1); i0 = np.maximum(idx - 1, 0); i1 = idx; i2 = idx + 1; i3 = np.minimum(idx + 2, m - 1)
    seg = np.stack([P[i0], P[i1], P[i2], P[i3]], 1)
    out = np.einsum('nk,skd->snd', _basis(n), seg).reshape(-1, 2)
    if not closed: out = np.vstack([out, P[-1:]])
    return out

def ellipse(cx, cy, rx, ry, ang=0.0, n=36):
    t = np.linspace(0, 2 * math.pi, n, endpoint=False)
    c, s_ = math.cos(ang), math.sin(ang)
    x = rx * np.cos(t); y = ry * np.sin(t)
    return np.stack([cx + x * c - y * s_, cy + x * s_ + y * c], 1)

def gradient_rect(img, cam, x, y, w, h, c0, c1, op=1.0, vertical=True, r=0.0):
    """a rounded rect filled with a linear gradient"""
    X0, Y0 = cam.P(x, y); X1, Y1 = cam.P(x + w, y + h)
    b = _box(img, X0, Y0, X1, Y1)
    if b is None or op <= 0.003: return
    ix0, iy0, ix1, iy1 = b
    m = np.zeros((iy1 - iy0, ix1 - ix0), np.uint8)
    cv2.fillPoly(m, [np.round((rr_pts(X0, Y0, X1, Y1, r * cam.s) - np.array([ix0, iy0])) * SC).astype(np.int32)], 255, cv2.LINE_AA, SH)
    hh, ww = m.shape
    if vertical: u = np.clip((np.arange(hh, dtype=F32) + iy0 - Y0) / max(1.0, Y1 - Y0), 0, 1)[:, None, None]
    else: u = np.clip((np.arange(ww, dtype=F32) + ix0 - X0) / max(1.0, X1 - X0), 0, 1)[None, :, None]
    col = np.asarray(c0, F32) * (1 - u) + np.asarray(c1, F32) * u
    col = np.broadcast_to(col, (hh, ww, 3))
    _put(img, m, ix0, iy0, col, op)

def glow(img, cam, cx, cy, r, color, op=1.0):
    """a soft radial light (additive)"""
    X, Y = cam.P(cx, cy); R = r * cam.s
    b = _box(img, X - R, Y - R, X + R, Y + R)
    if b is None or op <= 0.003: return
    ix0, iy0, ix1, iy1 = b
    H, W = img.shape[:2]
    x0, y0, x1, y1 = max(ix0, 0), max(iy0, 0), min(ix1, W), min(iy1, H)
    cx0, cy0, cx1, cy1 = CLIP.get(W, H)
    x0, y0, x1, y1 = max(x0, int(cx0)), max(y0, int(cy0)), min(x1, int(math.ceil(cx1))), min(y1, int(math.ceil(cy1)))
    if x1 <= x0 or y1 <= y0: return
    yy, xx = np.ogrid[y0:y1, x0:x1]
    a = np.exp(-(((xx - X) ** 2 + (yy - Y) ** 2) / (R * R * 0.35))).astype(F32) * op
    img[y0:y1, x0:x1] += a[..., None] * np.asarray(color, F32)
