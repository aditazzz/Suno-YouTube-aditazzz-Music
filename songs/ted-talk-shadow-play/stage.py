"""The shadow theatre: a backlit paper screen in a dark proscenium, a camera onto it, and layers of shadow.

World units: the 16:9 frame shows the whole screen, x 0..1920, y 0..1080; the floor is at y = 880.
The 9:16 frame crops to the action (a camera that pans), scaled 1.08. Shadows are drawn into masks in layers;
a layer's 'depth' is how far the puppet is from the paper: far from the paper = bigger, softer, lighter."""
import math
from functools import lru_cache
import numpy as np, cv2

F32 = np.float32
FLOOR = 880.0
LAMP = np.array([960.0, 420.0])            # where the lamp's light is centred on the screen
SH = 3; SC = 1 << SH
VS = 1.25            # 9:16: world -> screen scale (x 1080/W)
V_TOP = 200.0        # 9:16: the top of the stage opening, in px of a 1920-tall frame

class Cam:
    """world -> screen. 16:9: the whole screen (zoom > 1 pushes in on (fx, fy)). 9:16: a 1000-unit-wide slice around fx,
    with the floor anchored low in the frame."""
    def __init__(s, W, H, fx=960.0, fy=540.0, zoom=1.0):
        s.W, s.H = W, H; s.vert = H > W
        if not s.vert:
            s.s = W / 1920.0 * zoom; s.ox = W / 2 - fx * s.s; s.oy = H / 2 - fy * s.s
        else:
            s.s = VS * W / 1080.0 * zoom
            half = (W / 2) / s.s
            fx = float(np.clip(fx, half + 40, 1920 - half - 40))
            s.ox = W / 2 - fx * s.s
            s.oy = V_TOP * H / 1920.0 - 40.0 * s.s          # world y 40 at the top of the opening
    def P(s, pts):
        pts = np.asarray(pts, float); return np.stack([pts[..., 0] * s.s + s.ox, pts[..., 1] * s.s + s.oy], -1)
    def L(s, v): return v * s.s

def fill(mask, cam, polys, val=255):
    for p in polys:
        q = np.round(cam.P(p) * SC).astype(np.int64)
        q = np.clip(q, -2 ** 30, 2 ** 30).astype(np.int32)
        cv2.fillPoly(mask, [q], val, cv2.LINE_AA, SH)

def line(mask, cam, a, b, w, val=255):
    a = cam.P(np.asarray(a, float)); b = cam.P(np.asarray(b, float))
    cv2.line(mask, tuple(np.round(a * SC).astype(int)), tuple(np.round(b * SC).astype(int)), val, max(1, int(round(cam.L(w)))), cv2.LINE_AA, SH)

def polyline(mask, cam, P, w, val=255, closed=False):
    q = np.round(cam.P(np.asarray(P, float)) * SC).astype(np.int32)
    cv2.polylines(mask, [q], closed, val, max(1, int(round(cam.L(w)))), cv2.LINE_AA, SH)

# ---------------------------------------------------------------- the paper screen and its light
@lru_cache(4)
def paper_tex(W, H):
    rng = np.random.default_rng(5)
    fib = cv2.GaussianBlur(rng.normal(0, 1, (H, W)).astype(F32), (0, 0), sigmaX=7, sigmaY=0.7)
    fib2 = cv2.GaussianBlur(rng.normal(0, 1, (H, W)).astype(F32), (0, 0), sigmaX=0.8, sigmaY=5)
    blot = cv2.resize(cv2.GaussianBlur(rng.normal(0, 1, (H // 16, W // 16)).astype(F32), (0, 0), 3), (W, H), interpolation=cv2.INTER_CUBIC)
    t = 1 + 0.035 * fib + 0.025 * fib2 + 0.05 * blot / max(1e-6, np.abs(blot).max())
    return t.astype(F32)

@lru_cache(8)
def _grid(W, H, f):
    h, w = (H + f - 1) // f, (W + f - 1) // f
    yy, xx = np.mgrid[0:h, 0:w].astype(F32)
    return yy * f + (f - 1) / 2.0, xx * f + (f - 1) / 2.0

LIGHT_COL = np.array([1.0, 0.70, 0.40], F32) * np.array([1.0, 0.92, 0.85], F32)

def screen_light(cam, t, level=1.0, spot=0.0, spot_c=None, spot_r=380.0, flicker=0.0):
    """the lamp behind the paper: warm amber, brightest a little above centre. level: overall brightness,
    spot: 0..1 narrows the light to a spotlight around spot_c (world). (Smooth, so it is worked out at 1/4 size.)"""
    W, H = cam.W, cam.H; f = 4
    yy, xx = _grid(W, H, f)
    wx = (xx - cam.ox) / cam.s; wy = (yy - cam.oy) / cam.s           # world coords of each pixel
    d = np.sqrt(((wx - LAMP[0]) / 1150.0) ** 2 + ((wy - LAMP[1]) / 820.0) ** 2)
    base = np.clip(1.22 - 0.80 * d ** 1.5, 0.10, 1.25)
    if spot > 0:
        c = LAMP if spot_c is None else spot_c
        ds = np.sqrt(((wx - c[0]) / spot_r) ** 2 + ((wy - c[1]) / (spot_r * 1.15)) ** 2)
        sp = np.clip(1.25 - 0.9 * ds ** 2.2, 0.0, 1.25)
        base = base * (1 - spot) + np.maximum(sp, 0.06) * spot
    fl = 1.0 + flicker * (0.5 * math.sin(t * 23.0) + 0.3 * math.sin(t * 37.0 + 1) + 0.2 * math.sin(t * 61.0 + 2))
    S = (base * (level * fl) * (1 - 0.18 * np.clip(d - 0.4, 0, 1))).astype(F32)     # warmer, deeper towards the edges
    S = cv2.resize(S, (W, H), interpolation=cv2.INTER_LINEAR) * paper_tex(W, H)
    return S[..., None] * LIGHT_COL

# ---------------------------------------------------------------- layers of shadow
class Layers:
    """named masks; depth -> blur and opacity"""
    DEPTH = {"crisp": (0.9, 0.965), "near": (1.6, 0.94), "mid": (3.2, 0.86), "deep": (7.0, 0.72), "far": (13.0, 0.55)}
    def __init__(s, W, H):
        s.W, s.H = W, H; s.m = {}; s.gel = []; s.custom = []
    def mask(s, name):
        if name not in s.m: s.m[name] = np.zeros((s.H, s.W), np.uint8)
        return s.m[name]
    def add_custom(s, mask, sigma, op):
        """a mask with its own blur/opacity (e.g. a giant soft shadow, a translucent ghost)"""
        s.custom.append((mask, sigma, op))
    def add_gel(s, mask, color, sigma=0.9):
        s.gel.append((mask, np.asarray(color, F32), sigma))
    def composite(s, light):
        H, W = light.shape[:2]
        k = W / 1920.0 if W > H else VS * W / 1080.0
        trans = np.ones((H, W), F32)
        items = [(m, *s.DEPTH[n]) for n, m in s.m.items()] + s.custom
        for m, sig, op in items:
            roi = bbox(m, 3 * sig * k + 2)
            if roi is None: continue
            y0, y1, x0, x1 = roi
            a = m[y0:y1, x0:x1].astype(F32) * (op / 255.0)
            trans[y0:y1, x0:x1] *= 1 - blur(a, sig * k)
        img = light * trans[..., None]
        for m, col, sig in s.gel:   # coloured gel lets light through, tinted
            roi = bbox(m, 3 * sig + 2)
            if roi is None: continue
            y0, y1, x0, x1 = roi
            a = blur(m[y0:y1, x0:x1].astype(F32) / 255.0, sig)[..., None]
            img[y0:y1, x0:x1] = img[y0:y1, x0:x1] * (1 - a) + light[y0:y1, x0:x1] * col * 1.25 * a
        return img

def bbox(m, pad):
    """the padded bounding box of a mask's non-zero pixels (or None)"""
    rows = np.flatnonzero(m.any(1))
    if len(rows) == 0: return None
    cols = np.flatnonzero(m.any(0)); p = int(pad)
    H, W = m.shape
    return max(0, rows[0] - p), min(H, rows[-1] + 1 + p), max(0, cols[0] - p), min(W, cols[-1] + 1 + p)

def blur(a, sig):
    """Gaussian blur; wide ones are done at half size"""
    if sig <= 0.3: return a
    if sig < 2.5 or min(a.shape) < 16: return cv2.GaussianBlur(a, (0, 0), sig)
    h, w = a.shape
    sm = cv2.resize(a, ((w + 1) // 2, (h + 1) // 2), interpolation=cv2.INTER_AREA)
    sm = cv2.GaussianBlur(sm, (0, 0), sig / 2)
    return cv2.resize(sm, (w, h), interpolation=cv2.INTER_LINEAR)

# ---------------------------------------------------------------- the proscenium (the theatre around the screen)
@lru_cache(4)
def proscenium(W, H):
    """an alpha mask (1 = theatre, 0 = screen) and its colour image: dark wood with a little gold edge"""
    m = np.zeros((H, W), F32)
    if W > H:
        x0, x1, y0, y1 = 0.032 * W, 0.968 * W, 0.050 * H, 0.835 * H
    else:
        x0, x1 = 0.035 * W, 0.965 * W; y0 = V_TOP * H / 1920; y1 = y0 + 860.0 * VS * W / 1080.0
    m[:] = 1
    yy, xx = np.mgrid[0:H, 0:W].astype(F32)
    # screen opening with slightly rounded top corners
    r = 0.03 * W
    inside = (xx > x0) & (xx < x1) & (yy > y0) & (yy < y1)
    for cx, cy in ((x0 + r, y0 + r), (x1 - r, y0 + r)):
        corner = ((xx - cx) ** 2 + (yy - cy) ** 2 > r * r) & (np.abs(xx - cx) < r) & (yy < cy) & (((xx < cx) & (cx < W / 2)) | ((xx > cx) & (cx > W / 2)))
        inside &= ~corner
    m[inside] = 0
    m = cv2.GaussianBlur(m, (0, 0), 1.0)
    # colour: very dark warm brown with a faint gold rim around the opening
    edge = cv2.GaussianBlur((m > 0.5).astype(F32), (0, 0), 2.0)
    rim = np.clip(1 - np.abs(edge - 0.5) * 3, 0, 1) * (m > 0.02)
    col = np.zeros((H, W, 3), F32) + np.array([0.075, 0.045, 0.030], F32)
    grain = cv2.GaussianBlur(np.random.default_rng(3).normal(0, 1, (H, W)).astype(F32), (0, 0), sigmaX=9, sigmaY=1.2) * 0.012
    col += grain[..., None]
    col += rim[..., None] * np.array([0.55, 0.38, 0.16], F32) * 0.55
    return m, col, (x0, y0, x1, y1)
