"""Tiny vector 3D renderer for the illustrated city (ligne claire: flat fills, clean ink lines, real perspective).

World: metres, y up. Everything is drawn as projected polygons on a uint8 canvas with anti-aliasing, plus an ID buffer so
shadows and lights can be applied per visible surface afterwards. Cameras support yaw/pitch/roll, fov and lens shift
("rise") so architectural shots keep their verticals straight.
"""
import math
import numpy as np, cv2

F32 = np.float32
AA = cv2.LINE_AA
SHIFT = 4
SUB = 16.0


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)], F32)


def c8(c):
    c = np.clip(np.asarray(c, F32), 0, 1)
    return (int(round(c[0] * 255)), int(round(c[1] * 255)), int(round(c[2] * 255)))


def mix(a, b, t):
    return np.asarray(a, F32) * (1 - t) + np.asarray(b, F32) * t


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def sstep(a, b, x):
    if b == a: return 1.0 if x >= b else 0.0
    t = clamp((x - a) / (b - a)); return t * t * (3 - 2 * t)


def nrm(v):
    v = np.asarray(v, np.float64); return v / (np.linalg.norm(v) + 1e-12)


class Cam:
    def __init__(self, W, H, pos, yaw=0.0, pitch=0.0, roll=0.0, fov=45.0, rise=0.0, slide=0.0, near=0.25):
        """yaw/pitch/roll in degrees; fov = vertical field of view in degrees; rise/slide = lens shift in units of H."""
        self.W, self.H = W, H
        self.pos = np.asarray(pos, np.float64)
        y, p, r = math.radians(yaw), math.radians(pitch), math.radians(roll)
        f = np.array([math.sin(y) * math.cos(p), math.sin(p), math.cos(y) * math.cos(p)])
        rt = np.array([math.cos(y), 0.0, -math.sin(y)])
        up = np.array([-math.sin(y) * math.sin(p), math.cos(p), -math.cos(y) * math.sin(p)])
        if r:
            rt, up = rt * math.cos(r) + up * math.sin(r), -rt * math.sin(r) + up * math.cos(r)
        self.R = np.stack([rt, up, f])
        self.fwd = f
        self.fov = fov
        self.f = (H / 2) / math.tan(math.radians(fov) / 2)
        self.cx = W / 2 + slide * H
        self.cy = H / 2 + rise * H
        self.near = near

    @staticmethod
    def look(W, H, pos, target, fov=45.0, roll=0.0, rise=0.0, slide=0.0, level=False):
        d = np.asarray(target, np.float64) - np.asarray(pos, np.float64)
        yaw = math.degrees(math.atan2(d[0], d[2]))
        pitch = 0.0 if level else math.degrees(math.atan2(d[1], math.hypot(d[0], d[2])))
        return Cam(W, H, pos, yaw, pitch, roll, fov, rise, slide)

    def to_cam(self, P):
        return (np.asarray(P, np.float64) - self.pos) @ self.R.T

    def proj_c(self, Pc):
        z = np.maximum(Pc[..., 2], 1e-6)
        return np.stack([self.cx + self.f * Pc[..., 0] / z, self.cy - self.f * Pc[..., 1] / z], -1)

    def proj(self, P):
        Pc = self.to_cam(P)
        return self.proj_c(Pc), Pc[..., 2]

    def ray_dirs(self, step=1):
        """World-space unit ray directions for every pixel (H, W, 3) (optionally subsampled)."""
        xs = (np.arange(0, self.W, step, dtype=F32) + 0.5 * step - self.cx) / self.f
        ys = -(np.arange(0, self.H, step, dtype=F32) + 0.5 * step - self.cy) / self.f
        X, Y = np.meshgrid(xs, ys)
        R = self.R.astype(F32)
        d = X[..., None] * R[0] + Y[..., None] * R[1] + R[2]
        return d / np.linalg.norm(d, axis=-1, keepdims=True)

    def px_per_m(self, P):
        """Screen pixels per metre at world point P (for scaling sprites / line widths)."""
        z = self.to_cam(P)[..., 2]
        return self.f / max(1e-3, float(z))

    def homography_plane(self, origin, ex, ey):
        """3x3 homography mapping plane coords (a, b) [metres along ex, ey from origin] to screen pixels."""
        K = np.array([[self.f, 0, self.cx], [0, -self.f, self.cy], [0, 0, 1]])
        o = self.R @ (np.asarray(origin, np.float64) - self.pos)
        a = self.R @ np.asarray(ex, np.float64)
        b = self.R @ np.asarray(ey, np.float64)
        return K @ np.stack([a, b, o], 1)


def clip_near(Pc, near):
    n = len(Pc)
    if n == 0: return None
    z = Pc[:, 2]
    if (z >= near).all(): return Pc
    if (z < near).all(): return None
    out = []
    for i in range(n):
        a, b = Pc[i], Pc[(i + 1) % n]
        ia, ib = a[2] >= near, b[2] >= near
        if ia: out.append(a)
        if ia != ib:
            s = (near - a[2]) / (b[2] - a[2]); out.append(a + (b - a) * s)
    return np.array(out) if len(out) >= 3 else None


def screen_poly(cam, P):
    """World polygon (n,3) -> screen polygon (m,2) after near clipping, or None."""
    Pc = clip_near(cam.to_cam(P), cam.near)
    if Pc is None: return None
    return cam.proj_c(Pc)


def _i(p):
    return np.round(np.asarray(p, np.float64) * SUB).astype(np.int32)


def _guard(img):
    """Screen-space clip rectangle: the frame plus a generous guard band. Near-clipped faces of buildings right next to
    the camera project to vertices millions of pixels away; clipping (rather than rejecting) keeps them, at any size."""
    H, W = img.shape[:2]; g = float(max(W, H))
    return -g, -g, W + g, H + g


def _clip_poly(p, box):
    """Sutherland–Hodgman clip of a closed screen polygon (n, 2) to box = (x0, y0, x1, y1). None if nothing is left."""
    x0, y0, x1, y1 = box
    if p[:, 0].min() >= x0 and p[:, 0].max() <= x1 and p[:, 1].min() >= y0 and p[:, 1].max() <= y1:
        return p
    for ax, lim, lo in ((0, x0, True), (0, x1, False), (1, y0, True), (1, y1, False)):
        v = p[:, ax]
        ins = (v >= lim) if lo else (v <= lim)
        if ins.all(): continue
        if not ins.any(): return None
        out = []; n = len(p)
        for i in range(n):
            j = (i + 1) % n
            if ins[i]: out.append(p[i])
            if ins[i] != ins[j]:
                s = (lim - p[i, ax]) / (p[j, ax] - p[i, ax])
                q = p[i] + (p[j] - p[i]) * s; q[ax] = lim
                out.append(q)
        if len(out) < 3: return None
        p = np.array(out)
    return p


def _clip_seg2(a, b, box):
    """Liang–Barsky clip of the segment a-b to box; returns (a', b') or None."""
    x0, y0, x1, y1 = box
    t0, t1 = 0.0, 1.0
    dx, dy = b[0] - a[0], b[1] - a[1]
    for pp, qq in ((-dx, a[0] - x0), (dx, x1 - a[0]), (-dy, a[1] - y0), (dy, y1 - a[1])):
        if pp == 0:
            if qq < 0: return None
            continue
        r = qq / pp
        if pp < 0:
            if r > t1: return None
            t0 = max(t0, r)
        else:
            if r < t0: return None
            t1 = min(t1, r)
    return a + (b - a) * t0, a + (b - a) * t1


def _clip_open(p, box):
    """Clip an open polyline to box; returns the visible pieces."""
    x0, y0, x1, y1 = box
    if p[:, 0].min() >= x0 and p[:, 0].max() <= x1 and p[:, 1].min() >= y0 and p[:, 1].max() <= y1:
        return [p]
    pieces, cur = [], []
    for i in range(len(p) - 1):
        s = _clip_seg2(p[i], p[i + 1], box)
        if s is None:
            if len(cur) >= 2: pieces.append(np.array(cur))
            cur = []; continue
        a, b = s
        if cur and np.abs(cur[-1] - a).max() < 1e-6: cur.append(b)
        else:
            if len(cur) >= 2: pieces.append(np.array(cur))
            cur = [a, b]
    if len(cur) >= 2: pieces.append(np.array(cur))
    return pieces


def _polys(img, polys):
    box = _guard(img); out = []
    for p in polys:
        if p is None or len(p) < 3: continue
        p = np.asarray(p, np.float64)
        if not np.isfinite(p).all(): continue
        p = _clip_poly(p, box)
        if p is not None: out.append(_i(p))
    return out


def _ok(p):
    return p is not None and len(p) >= 3 and np.isfinite(p).all()


def fill(img, polys, col):
    polys = _polys(img, polys)
    if polys: cv2.fillPoly(img, polys, col if isinstance(col, (int, float)) else c8(col), AA, shift=SHIFT)


def fill_id(idb, polys, val):
    polys = _polys(idb, polys)
    if polys: cv2.fillPoly(idb, polys, int(val), cv2.LINE_8, shift=SHIFT)


def lines(img, polys, col, th=1, closed=True):
    box = _guard(img); out = []
    for p in polys:
        if p is None or len(p) < 2: continue
        p = np.asarray(p, np.float64)
        if not np.isfinite(p).all(): continue
        if closed and len(p) >= 3:
            p = _clip_poly(p, box)
            if p is not None: out.append(_i(p))
        else:
            out.extend(_i(q) for q in _clip_open(p, box))
    if out: cv2.polylines(img, out, closed, col if isinstance(col, (int, float)) else c8(col), max(1, int(th)), AA, shift=SHIFT)


def seg(img, a, b, col, th=1):
    a = np.asarray(a, np.float64); b = np.asarray(b, np.float64)
    if not (np.isfinite(a).all() and np.isfinite(b).all()): return
    s = _clip_seg2(a, b, _guard(img))
    if s is None: return
    cv2.line(img, tuple(_i(s[0])), tuple(_i(s[1])), c8(col) if not isinstance(col, (int, float)) else col, max(1, int(th)), AA, shift=SHIFT)


def quad_grid(o, ex, ey, cols, rows, u0, u1, v0, v1):
    """World corners (rows*cols, 4, 3) of a grid of rectangles on a plane. Cell (r, c) spans [c + u0, c + u1] x [r + v0, r + v1]
    in cell units; ex/ey are cell-size vectors."""
    c = np.arange(cols)[None, :, None]; r = np.arange(rows)[:, None, None]
    o = np.asarray(o, np.float64); ex = np.asarray(ex, np.float64); ey = np.asarray(ey, np.float64)
    def P(du, dv): return o + (c + du) * ex + (r + dv) * ey
    q = np.stack([P(u0, v0), P(u1, v0), P(u1, v1), P(u0, v1)], 2)   # rows, cols, 4, 3
    return q.reshape(rows * cols, 4, 3)


def proj_quads(cam, Q):
    """Project many small world quads (N, 4, 3); returns screen (N, 4, 2), depth (N,), visible mask (all corners in front)."""
    Pc = cam.to_cam(Q.reshape(-1, 3)).reshape(Q.shape)
    vis = (Pc[..., 2] > cam.near).all(1)
    S = cam.proj_c(Pc)
    on = vis & (S[..., 0].max(1) > -2) & (S[..., 0].min(1) < cam.W + 2) & (S[..., 1].max(1) > -2) & (S[..., 1].min(1) < cam.H + 2)
    return S, Pc[..., 2].mean(1), on


# ------------------------------------------------------------------ image helpers
def to_f(img8): return img8.astype(F32) / 255.0
def to_8(img): return (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)


def blur(x, s):
    if s <= 0: return x
    return cv2.GaussianBlur(x, (0, 0), s)


def glow(layer, sigma, scale=4):
    """Cheap wide blur via downsampling."""
    H, W = layer.shape[:2]
    small = cv2.resize(layer, (max(1, W // scale), max(1, H // scale)), interpolation=cv2.INTER_AREA)
    small = cv2.GaussianBlur(small, (0, 0), max(0.5, sigma / scale))
    return cv2.resize(small, (W, H), interpolation=cv2.INTER_LINEAR)


def bloom(img, thresh=0.72, amt=0.6, sigma=18):
    lum = img.max(-1, keepdims=True)
    hi = img * np.clip((lum - thresh) / (1 - thresh + 1e-6), 0, 1)
    g = glow(hi, sigma, 4) * 0.6 + glow(hi, sigma * 3.5, 8) * 0.4
    return img + g * amt


def rays(img, src_mask, cx, cy, amt, decay=0.93, n=26, tint=(1.0, 0.85, 0.62)):
    """Radial light shafts from a bright source (crepuscular rays), done at quarter resolution."""
    if amt <= 0.003: return img
    H, W = img.shape[:2]; s = 4
    m = cv2.resize(src_mask, (W // s, H // s), interpolation=cv2.INTER_AREA).astype(F32)
    acc = m.copy(); cur = m.copy(); w = 1.0; tot = 1.0
    sc = 1.0
    for i in range(n):
        sc *= 0.965
        M = np.array([[sc, 0, (1 - sc) * cx / s], [0, sc, (1 - sc) * cy / s]], F32)
        cur = cv2.warpAffine(m, M, (W // s, H // s), flags=cv2.INTER_LINEAR)
        w *= decay; acc += cur * w; tot += w
    acc = cv2.resize(acc / tot, (W, H), interpolation=cv2.INTER_LINEAR)
    return img + acc[..., None] * np.array(tint, F32) * amt


def grain(H, W, seed, amt=0.035):
    rng = np.random.default_rng(seed)
    g = rng.standard_normal((H // 2, W // 2)).astype(F32)
    g = cv2.resize(g, (W, H), interpolation=cv2.INTER_LINEAR)
    return g[..., None] * amt


_PAPER = {}
def paper(H, W):
    """Static paper tooth: very low-amplitude fibrous texture, multiplied over the frame."""
    k = (H, W)
    if k not in _PAPER:
        rng = np.random.default_rng(7)
        n = rng.standard_normal((H, W)).astype(F32)
        n1 = cv2.GaussianBlur(n, (0, 0), 0.8)
        n2 = cv2.GaussianBlur(rng.standard_normal((H // 8, W // 8)).astype(F32), (0, 0), 2.0)
        n2 = cv2.resize(n2, (W, H))
        p = 1 + 0.018 * n1 / (n1.std() + 1e-6) + 0.02 * n2 / (n2.std() + 1e-6)
        _PAPER[k] = p[..., None].astype(F32)
    return _PAPER[k]


def vignette(H, W, amt=0.28):
    yy, xx = np.mgrid[0:H, 0:W].astype(F32)
    d = ((xx - W / 2) / (W / 2)) ** 2 * 0.8 + ((yy - H / 2) / (H / 2)) ** 2 * 0.8
    return (1 - amt * np.clip(d, 0, 1.6) ** 1.4)[..., None]


_VIG = {}
def vig(H, W, amt=0.28):
    k = (H, W, round(amt, 3))
    if k not in _VIG: _VIG[k] = vignette(H, W, amt)
    return _VIG[k]


def lift(img, shadows, mids, highs):
    """Simple 3-way grade: tint shadows / mids / highlights (each an RGB multiplier/offset-ish)."""
    l = img.mean(-1, keepdims=True)
    ws = np.clip(1 - l * 2.2, 0, 1); wh = np.clip(l * 2.2 - 1.2, 0, 1); wm = 1 - ws - wh
    return img * (ws * shadows + wm * mids + wh * highs)
