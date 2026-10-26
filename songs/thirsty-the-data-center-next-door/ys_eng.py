"""Thirsty (The Data Center Next Door): the rendering kit.

Everything is linear-light HDR float32 (H, W, 3) until develop(). World units are metres, +Y up, ground at y = 0,
+Z points from the town toward the facility. Each frame is a pure function of t, so chunks render independently.

Pieces
  Cam        look-at pinhole camera with a real focal length (fov is measured on the 2.39:1 picture band), lens shift,
             roll and a slow handheld drift; per-pixel ray directions for sky / ground / water.
  Canvas     colour + view-depth buffers. Polygons are drawn far-to-near (painter) with anti-aliased edges; every
             pixel keeps its exact depth (1/z is affine across a planar face), so fog, light occlusion and the
             transparent layers can be done per pixel afterwards.
  noise      tileable fbm textures (FFT), cellular cracks; sampled in world space with cv2.remap.
  fog        exponential height fog with drifting density, coloured by the sky at the horizon.
  lights     point lights splatted into an emissive buffer with a depth test; water reflections as vertical streaks.
  develop    film finish: halation, bloom, filmic curve, split-tone grade, grain, vignette, letterbox.
"""
import os, math
from functools import lru_cache
import numpy as np, cv2
if os.environ.get("YS_THREADS"): cv2.setNumThreads(int(os.environ["YS_THREADS"]))

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FONTS = os.path.join(ROOT, "assets", "fonts")
F32 = np.float32
ASPECT = 2.39                                   # picture band inside the 16:9 frame

# ---------------------------------------------------------------- math
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def sstep(a, b, x):
    if b == a: return 1.0 if x >= b else 0.0
    t = clamp((x - a) / (b - a)); return t * t * (3 - 2 * t)
def ss_arr(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
def ease_io(t): t = clamp(t); return t * t * t * (t * (6 * t - 15) + 10)
def ease_out(t): t = clamp(t); return 1 - (1 - t) ** 3
def ease_in(t): t = clamp(t); return t ** 3
def lerp(a, b, t): return a + (b - a) * t
def lerpv(a, b, t): return np.asarray(a, F32) * (1 - t) + np.asarray(b, F32) * t
def nrm(v): v = np.asarray(v, F32); return v / max(1e-9, float(np.linalg.norm(v)))
def hexc(h, gain=1.0):
    h = h.lstrip('#'); c = np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)], F32)
    return (np.power(c, 2.2) * gain).astype(F32)                         # sRGB -> linear
def keys(kk, t, ease=ease_io):
    """piecewise eased interpolation through [(t, value), ...]; values may be scalars or vectors."""
    if t <= kk[0][0]: return kk[0][1]
    for (t0, v0), (t1, v1) in zip(kk, kk[1:]):
        if t <= t1:
            u = ease((t - t0) / max(1e-6, t1 - t0))
            return (np.asarray(v0, F32) * (1 - u) + np.asarray(v1, F32) * u) if isinstance(v0, (tuple, list, np.ndarray)) else v0 + (v1 - v0) * u
    return kk[-1][1]

def hash01(*a):
    """deterministic pseudo-random in [0,1) from ints/floats."""
    h = 0x345678
    for v in a: h = (h * 1000003) ^ (int(v * 7919) & 0xffffffff); h &= 0xffffffff
    h ^= h >> 13; h = (h * 0x5bd1e995) & 0xffffffff; h ^= h >> 15
    return (h & 0xffffff) / float(0x1000000)

def smooth_noise1(t, seed=0, rate=1.0):
    """1-D smooth noise in [-1, 1] (sum of incommensurate sines), for handheld drift and flicker."""
    s = seed * 1.618
    return (math.sin(t * rate * 1.31 + s) * 0.5 + math.sin(t * rate * 2.17 + s * 2.3) * 0.3 + math.sin(t * rate * 3.73 + s * 0.7) * 0.2)

# ---------------------------------------------------------------- palette (linear)
NAVY = hexc('0a1322'); NAVY2 = hexc('15223a'); TEAL = hexc('0f3a40'); PETROL = hexc('1d5a5e'); CHAR = hexc('18191c')
STEEL = hexc('8a9aa6'); IVORY = hexc('ece2cb'); DIRTY = hexc('d2c5a8'); CRIMSON = hexc('c01f3a'); DEEPRED = hexc('7a0f20')
PINK = hexc('ff3d8b'); SODIUM = hexc('ffae62'); LED = hexc('d8ecff'); AMBER = hexc('ffc07a'); BLUEWIN = hexc('4f9cff')
RED_AV = hexc('ff2236'); WHITE = np.array([1, 1, 1], F32)

# ---------------------------------------------------------------- camera
# 9:16 frames keep the 16:9 picture's pixel scale on their short side: the same subject size, with more room above and
# below. VSHIFT is a per-shot lens shift for 9:16 only, set by the scene for each shot: [x as a fraction of the frame
# width, y as a fraction of the frame height (positive moves the picture up)].
V_SCALE = 804 / 1080
VSHIFT = [0.0, 0.0]

def sref(W, H):
    """the band-equivalent short side: H of a 16:9 picture band, or W * V_SCALE of a 9:16 frame (sizes scale with it)."""
    return float(H) if W >= H else float(W) * V_SCALE

def pxs(W, H):
    """pixel scale relative to the 1920-wide 16:9 render (for blur radii etc.): W / 1920, or W / 1080 for 9:16;
    a square-ish frame (the album cover) uses its height against the 16:9 band's 804."""
    if W >= H: return W / 1920.0 if W >= 1.7 * H else H / 804.0
    return W / 1080.0

class Cam:
    def __init__(s, eye, target, fov=40.0, W=1920, H=804, roll=0.0, shift=(0.0, 0.0), band_h=None, drift=0.0, t=0.0, seed=0):
        s.W, s.H = int(W), int(H)
        eye = np.asarray(eye, F32); tgt = np.asarray(target, F32)
        if drift:   # slow handheld / dolly breathing: a few cm and a few hundredths of a degree
            eye = eye + np.array([smooth_noise1(t, seed, 0.6), smooth_noise1(t, seed + 3, 0.5) * 0.6, 0], F32) * drift
            tgt = tgt + np.array([smooth_noise1(t, seed + 7, 0.4), smooth_noise1(t, seed + 11, 0.45), 0], F32) * drift * 2.0
        s.eye, s.tgt = eye, tgt
        f = nrm(tgt - eye); up = np.array([0, 1, 0], F32)
        r = np.cross(up, f); r = r / max(1e-9, np.linalg.norm(r)); u = np.cross(f, r)
        if roll:
            c, sn = math.cos(roll), math.sin(roll); r, u = r * c + u * sn, u * c - r * sn
        s.f, s.r, s.u = f.astype(F32), r.astype(F32), u.astype(F32)
        bh = band_h if band_h is not None else (s.H if s.W >= s.H else s.W * V_SCALE)
        s.fpx = (bh / 2) / math.tan(math.radians(fov) / 2)
        sx = shift[0] + (VSHIFT[0] if s.W < s.H else 0.0)
        s.cx = s.W / 2 + sx * s.W; s.cy = s.H / 2 - shift[1] * bh - (VSHIFT[1] * s.H if s.W < s.H else 0.0)
        s.fov = fov; s._dirs = None

    def cam_space(s, P):
        Q = np.asarray(P, F32).reshape(-1, 3) - s.eye
        return Q @ s.r, Q @ s.u, Q @ s.f

    def project(s, P):
        x, y, z = s.cam_space(P); zs = np.maximum(z, 1e-4)
        return s.cx + s.fpx * x / zs, s.cy - s.fpx * y / zs, z

    def px_scale(s, z): return s.fpx / max(1e-4, z)            # pixels per metre at view depth z

    def dirs(s):
        """(H, W, 3) unit ray directions and (H, W) factor k with distance = z * k."""
        if s._dirs is None:
            xs = (np.arange(s.W, dtype=F32) + 0.5 - s.cx); ys = (s.cy - np.arange(s.H, dtype=F32) - 0.5)
            D = s.f[None, None] * s.fpx + s.r[None, None] * xs[None, :, None] + s.u[None, None] * ys[:, None, None]
            n = np.sqrt((D * D).sum(2)); s._dirs = (D / n[..., None], n / s.fpx)
        return s._dirs


def lowres_cam(cam, f):
    """the same camera rendering a frame 1/f the size (same framing)."""
    c = Cam.__new__(Cam); c.__dict__.update(cam.__dict__)
    c.W, c.H = max(4, int(round(cam.W / f))), max(4, int(round(cam.H / f)))
    sx, sy = c.W / cam.W, c.H / cam.H
    c.fpx = cam.fpx * sx; c.cx = cam.cx * sx; c.cy = cam.cy * sy; c._dirs = None
    return c

# ---------------------------------------------------------------- polygon clipping
def clip_near(Pc, near=0.5):
    """Sutherland–Hodgman clip of a camera-space polygon (n, 3) against z >= near."""
    out = []; n = len(Pc)
    for i in range(n):
        a, b = Pc[i], Pc[(i + 1) % n]; ia, ib = a[2] >= near, b[2] >= near
        if ia: out.append(a)
        if ia != ib:
            k = (near - a[2]) / (b[2] - a[2]); out.append(a + (b - a) * k)
    return np.array(out, F32) if len(out) >= 3 else None

# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(s, cam, fill=(0, 0, 0)):
        s.cam = cam; H, W = cam.H, cam.W
        s.img = np.empty((H, W, 3), F32); s.img[:] = fill
        s.dep = np.full((H, W), np.inf, F32)            # camera-space z of the nearest opaque surface
        s.emis = np.zeros((H, W, 3), F32)               # emissive / point-light buffer (added after fog)
        s.W, s.H = W, H

    def _screen(s, P3, near=0.5):
        x, y, z = s.cam.cam_space(P3)
        Pc = np.stack([x, y, z], 1)
        if (Pc[:, 2] < near).any():
            Pc = clip_near(Pc, near)
            if Pc is None: return None
        zs = Pc[:, 2]; sx = s.cam.cx + s.cam.fpx * Pc[:, 0] / zs; sy = s.cam.cy - s.cam.fpx * Pc[:, 1] / zs
        return sx, sy, zs

    def poly(s, P3, col, op=1.0, shade=None, depth=True, flat_depth=False, emis=None, ztest=False, write_depth=True, alpha=None):
        """Fill a planar 3-D polygon. col: rgb, or shade(X, Y, Z, mask) -> (h, w, 3) per-pixel colour over the bbox
        (X, Y screen coords, Z view depth). emis: optional emissive rgb (constant) or callable like shade."""
        sc = s._screen(np.asarray(P3, F32))
        if sc is None: return None
        sx, sy, zs = sc
        x0 = max(0, int(math.floor(sx.min())) - 1); x1 = min(s.W, int(math.ceil(sx.max())) + 2)
        y0 = max(0, int(math.floor(sy.min())) - 1); y1 = min(s.H, int(math.ceil(sy.max())) + 2)
        if x1 - x0 < 1 or y1 - y0 < 1: return None
        m = np.zeros((y1 - y0, x1 - x0), F32)
        pts = np.round(np.stack([sx - x0, sy - y0], 1) * 8).astype(np.int32)
        cv2.fillPoly(m, [pts], 1.0, cv2.LINE_AA, shift=3)
        if not m.any(): return None
        if flat_depth or len(zs) < 3:
            Z = np.full(m.shape, float(zs.mean()), F32)
        else:   # 1/z affine in screen space
            A = np.stack([sx, sy, np.ones_like(sx)], 1); bz = 1.0 / zs
            coef, *_ = np.linalg.lstsq(A.astype(np.float64), bz.astype(np.float64), rcond=None)
            X = np.arange(x0, x1, dtype=F32)[None, :] + 0.5; Y = np.arange(y0, y1, dtype=F32)[:, None] + 0.5
            iz = coef[0] * X + coef[1] * Y + coef[2]
            Z = (1.0 / np.maximum(iz, 1e-7)).astype(F32)
        if ztest:
            m = m * (s.dep[y0:y1, x0:x1] > Z * 0.999)
            if not m.any(): return None
        if alpha is not None:
            X = np.arange(x0, x1, dtype=F32)[None, :] + 0.5; Y = np.arange(y0, y1, dtype=F32)[:, None] + 0.5
            m = m * alpha(np.broadcast_to(X, m.shape), np.broadcast_to(Y, m.shape), Z, m)
        mm = m[..., None] * op
        reg = s.img[y0:y1, x0:x1]
        if callable(col):
            X = np.arange(x0, x1, dtype=F32)[None, :] + 0.5; Y = np.arange(y0, y1, dtype=F32)[:, None] + 0.5
            C = col(np.broadcast_to(X, m.shape), np.broadcast_to(Y, m.shape), Z, m)
        else: C = np.asarray(col, F32)
        reg *= (1 - mm); reg += C * mm
        if emis is not None:
            if callable(emis):
                X = np.arange(x0, x1, dtype=F32)[None, :] + 0.5; Y = np.arange(y0, y1, dtype=F32)[:, None] + 0.5
                E = emis(np.broadcast_to(X, m.shape), np.broadcast_to(Y, m.shape), Z, m)
            else: E = np.asarray(emis, F32)
            er = s.emis[y0:y1, x0:x1]; er *= (1 - mm); er += E * mm
        else:
            s.emis[y0:y1, x0:x1] *= (1 - mm)
        if write_depth and op > 0.5:
            d = s.dep[y0:y1, x0:x1]; sel = m > 0.5; d[sel] = Z[sel]
        s.last_bbox = (x0, y0, x1, y1)
        return (x0, y0, x1, y1)

    def line3(s, A, B, col, width_m=0.1, min_px=0.7, op=1.0, emis=None, write_depth=False):
        """an anti-aliased 3-D line whose width is width_m metres (never thinner than min_px)."""
        sc = s._screen(np.array([A, B], F32), 0.5)
        if sc is None: return
        sx, sy, zs = sc
        if len(sx) < 2: return
        z = float(zs.mean()); w = max(min_px, width_m * s.cam.fpx / max(0.5, z))
        _aa_line(s.img, sx[0], sy[0], sx[-1], sy[-1], w, col, op)
        if emis is not None: _aa_line(s.emis, sx[0], sy[0], sx[-1], sy[-1], w, emis, op, add=True)

    def polyline3(s, P, col, width_m=0.05, min_px=0.7, op=1.0, emis=None):
        P = np.asarray(P, F32)
        for a, b in zip(P[:-1], P[1:]): s.line3(a, b, col, width_m, min_px, op, emis)

def lines_batch(cv, A, B, col, width_m=0.1, min_px=0.7, op=1.0, near=0.5, emis=None):
    """many 3-D segments (A[i] -> B[i]) of one colour: projected together, drawn into one AA coverage mask."""
    A = np.asarray(A, F32).reshape(-1, 3); B = np.asarray(B, F32).reshape(-1, 3)
    if len(A) == 0: return
    cam = cv.cam
    xa, ya, za = cam.cam_space(A); xb, yb, zb = cam.cam_space(B)
    keep = (za > near) | (zb > near)
    if not keep.any(): return
    xa, ya, za, xb, yb, zb = xa[keep], ya[keep], za[keep], xb[keep], yb[keep], zb[keep]
    # clip to the near plane
    ka = za < near; kb = zb < near
    if ka.any():
        k = (near - za[ka]) / (zb[ka] - za[ka]); xa[ka] += (xb[ka] - xa[ka]) * k; ya[ka] += (yb[ka] - ya[ka]) * k; za[ka] = near
    if kb.any():
        k = (near - zb[kb]) / (za[kb] - zb[kb]); xb[kb] += (xa[kb] - xb[kb]) * k; yb[kb] += (ya[kb] - yb[kb]) * k; zb[kb] = near
    f = cam.fpx
    sxa = cam.cx + f * xa / za; sya = cam.cy - f * ya / za; sxb = cam.cx + f * xb / zb; syb = cam.cy - f * yb / zb
    w = np.maximum(min_px, width_m * f / np.maximum(0.5, (za + zb) / 2))
    W, H = cv.W, cv.H
    vis = ~(((sxa < -10) & (sxb < -10)) | ((sxa > W + 10) & (sxb > W + 10)) | ((sya < -10) & (syb < -10)) | ((sya > H + 10) & (syb > H + 10)))
    if not vis.any(): return
    m = np.zeros((H, W), F32)
    ww = np.maximum(1, np.round(w)).astype(int); cov = np.clip(w / ww, 0, 1)
    for th in np.unique(ww[vis]):
        sel = vis & (ww == th)
        for c_ in np.unique(np.round(cov[sel] * 8) / 8):
            ss = sel & (np.round(cov * 8) / 8 == c_)
            pts = np.stack([np.stack([sxa[ss], sya[ss]], 1), np.stack([sxb[ss], syb[ss]], 1)], 1)
            pts = np.clip(np.round(pts * 8), -2 ** 28, 2 ** 28).astype(np.int32)
            lay = np.zeros((H, W), F32)
            cv2.polylines(lay, list(pts), False, 1.0, int(th), cv2.LINE_AA, shift=3)
            np.maximum(m, lay * float(max(c_, 0.125)), out=m)
    mm = (m * op)[..., None]
    cv.img *= (1 - mm); cv.img += mm * np.asarray(col, F32)
    if emis is not None: cv.emis += mm * np.asarray(emis, F32)
    else: cv.emis *= (1 - mm)

def _aa_line(img, x0, y0, x1, y1, w, col, op=1.0, add=False):
    """anti-aliased line of (sub-pixel) width w into a float image, drawn through a small mask."""
    H, W = img.shape[:2]
    pad = int(w) + 3
    bx0 = max(0, int(min(x0, x1)) - pad); bx1 = min(W, int(max(x0, x1)) + pad + 1)
    by0 = max(0, int(min(y0, y1)) - pad); by1 = min(H, int(max(y0, y1)) + pad + 1)
    if bx1 <= bx0 or by1 <= by0: return
    m = np.zeros((by1 - by0, bx1 - bx0), F32)
    ww = max(1, int(round(w)))
    a = max(0.0, min(1.0, w / ww)) * op            # thin lines: full-pixel line, faded by coverage
    p0 = (int(round((x0 - bx0) * 8)), int(round((y0 - by0) * 8))); p1 = (int(round((x1 - bx0) * 8)), int(round((y1 - by0) * 8)))
    cv2.line(m, p0, p1, 1.0, ww, cv2.LINE_AA, shift=3)
    mm = m[..., None] * a; reg = img[by0:by1, bx0:bx1]
    if add: reg += mm * np.asarray(col, F32)
    else: reg *= (1 - mm); reg += mm * np.asarray(col, F32)

# ---------------------------------------------------------------- caches with a memory budget
def byte_lru(max_bytes):
    """like functools.lru_cache, but bounded by the bytes of the numpy arrays it holds (big glyph masks and steam
    sprites otherwise pile up into gigabytes at 1440p / 4K). Pure functions only: results are unchanged."""
    import functools
    from collections import OrderedDict
    def size(v):
        if isinstance(v, np.ndarray): return v.nbytes
        if isinstance(v, (tuple, list)): return sum(size(x) for x in v)
        return 64
    max_bytes = int(max_bytes * float(os.environ.get('YS_CACHE_SCALE', '1.0')))   # < 1 on a memory-tight machine
    def deco(fn):
        cache = OrderedDict(); st = {'b': 0}
        @functools.wraps(fn)
        def w(*args, **kw):
            k = args + tuple(sorted(kw.items())) if kw else args
            if k in cache:
                cache.move_to_end(k); return cache[k]
            v = fn(*args, **kw); cache[k] = v; st['b'] += size(v)
            while st['b'] > max_bytes and len(cache) > 1:
                _, old = cache.popitem(last=False); st['b'] -= size(old)
            return v
        w.cache_clear = lambda: (cache.clear(), st.update(b=0))
        w.cache_bytes = lambda: st['b']
        return w
    return deco

# ---------------------------------------------------------------- noise
@lru_cache(16)
def fbm_tex(n=512, beta=2.0, seed=0, lo=0.0):
    """tileable fractal noise in [0, 1] (power-law spectrum)."""
    r = np.random.default_rng(seed)
    w = r.normal(0, 1, (n, n)).astype(F32)
    fy = np.fft.fftfreq(n)[:, None]; fx = np.fft.rfftfreq(n)[None, :]
    f = np.sqrt(fx * fx + fy * fy); f[0, 0] = 1
    flt = f ** (-beta / 2); flt[0, 0] = 0
    if lo: flt *= (f > lo / n)
    out = np.fft.irfft2(np.fft.rfft2(w) * flt, s=(n, n)).astype(F32)
    out -= out.min(); out /= max(1e-9, out.max())
    return out

@lru_cache(4)
def crack_tex(n=512, cells=90, seed=3):
    """tileable dried-mud cracks: 1 on the crack lines, 0 inside the plates; plus per-plate shade."""
    r = np.random.default_rng(seed)
    pts = r.uniform(0, n, (cells, 2))
    big = np.ones((3 * n, 3 * n), np.uint8)
    for dx in (0, n, 2 * n):
        for dy in (0, n, 2 * n):
            for x, y in pts: big[int(y + dy) % (3 * n), int(x + dx) % (3 * n)] = 0
    d, lab = cv2.distanceTransformWithLabels(big, cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
    lab = lab[n:2 * n, n:2 * n]
    edge = np.zeros((n, n), F32)
    edge[:, :-1] += (lab[:, :-1] != lab[:, 1:]); edge[:-1, :] += (lab[:-1, :] != lab[1:, :])
    edge = np.clip(edge, 0, 1)
    edge = cv2.GaussianBlur(edge, (0, 0), 0.9); edge = np.clip(edge * 2.2, 0, 1)
    shade = (lab % 97).astype(F32) / 96.0
    return edge, shade

def sample(tex, u, v, scale=1.0):
    """bilinear wrap-around lookup of a tileable texture at world coords (u, v) * scale (in texels)."""
    n = tex.shape[0]
    u, v = np.broadcast_arrays(np.asarray(u, F32), np.asarray(v, F32))
    sc = np.float32(scale)
    mx = (u * sc).astype(F32, copy=False); my = (v * sc).astype(F32, copy=False)     # remap wraps out-of-range coords itself
    if mx.ndim == 1: return cv2.remap(tex, mx[None], my[None], cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)[0]
    return cv2.remap(tex, np.ascontiguousarray(mx), np.ascontiguousarray(my), cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)

# ---------------------------------------------------------------- planes
def plane_hit(cam, h):
    """per-pixel intersection with the horizontal plane y = h: (t distance along unit ray, X, Z, valid mask)."""
    D, k = cam.dirs()
    dy = D[..., 1]
    with np.errstate(divide='ignore', invalid='ignore'):
        t = (h - cam.eye[1]) / dy
    ok = (t > 0) & np.isfinite(t)
    t = np.where(ok, t, np.inf).astype(F32)
    X = cam.eye[0] + D[..., 0] * np.where(ok, t, 0); Z = cam.eye[2] + D[..., 2] * np.where(ok, t, 0)
    return t, X.astype(F32), Z.astype(F32), ok

def dist_to_z(cam, t):
    """distance along the unit ray -> camera-space z."""
    D, k = cam.dirs(); return (t / k).astype(F32)

# ---------------------------------------------------------------- fog
def fog_pass(cv, fog_col, density=0.0015, height=40.0, haze_tex=None, t=0.0, wind=(1.5, 0.0), noise_amt=0.5, sky_fog=0.0,
             max_fog=0.97):
    """exponential height fog on everything with a depth (and a little haze on the sky).
    fog_col: rgb or (H, W, 3) (e.g. the sky colour near the horizon, brighter around the facility)."""
    cam = cv.cam; D, k = cam.dirs()
    dist = np.where(np.isfinite(cv.dep), cv.dep * k, 0).astype(F32)
    ey = cam.eye[1]; dy = D[..., 1]
    # optical depth of exp(-y/height) density from the eye along the ray (closed form)
    a = np.float32(1.0 / height)
    with np.errstate(over='ignore', invalid='ignore', divide='ignore'):
        e0 = math.exp(-ey * a)
        g = np.where(np.abs(dy) > 1e-4, (1 - np.exp(-dist * dy * a)) / np.maximum(1e-6, np.abs(dy * a)) * np.sign(dy), dist)
        od = density * e0 * np.abs(g)
    if haze_tex is not None and noise_amt > 0:
        # drifting density: sample the noise where the ray crosses half the fog height
        tm = np.clip((height * 0.5 - ey) / np.where(np.abs(dy) > 1e-3, dy, -1e-3), 0, 4000)
        X = cam.eye[0] + D[..., 0] * tm + wind[0] * t; Z = cam.eye[2] + D[..., 2] * tm + wind[1] * t
        nz = sample(haze_tex, X, Z, 0.9)
        od = od * (1 - noise_amt + noise_amt * 2 * nz)
    T = np.exp(-od).astype(F32)
    T = np.maximum(T, 1 - max_fog)
    sky = ~np.isfinite(cv.dep)
    if sky_fog: T = np.where(sky, 1 - sky_fog * (1 - np.clip(D[..., 1] * 4, 0, 1)), T)
    else: T = np.where(sky, 1.0, T)
    fc = np.asarray(fog_col, F32)
    cv.img *= T[..., None]; cv.img += fc * (1 - T)[..., None]
    cv.emis *= T[..., None]
    return T

# ---------------------------------------------------------------- lights
def lights(cv, P, col, inten, size_m=0.3, ztest=True, buf=None, min_r=0.8, mirror_h=None, streak=None):
    """point lights. P (n,3), col (n,3) or (3,), inten (n,) or scalar. Adds a sharp core to the emissive buffer
    (glow comes from bloom). size_m: physical radius (bigger lights read bigger up close)."""
    P = np.asarray(P, F32).reshape(-1, 3)
    if len(P) == 0: return
    cam = cv.cam
    if mirror_h is not None: P = P * np.array([1, -1, 1], F32) + np.array([0, 2 * mirror_h, 0], F32)
    x, y, z = cam.project(P)
    inten = np.broadcast_to(np.asarray(inten, F32), (len(P),)); col = np.broadcast_to(np.asarray(col, F32), (len(P), 3))
    ok = (z > 0.5) & (x > -4) & (x < cv.W + 4) & (y > -4) & (y < cv.H + 4) & (inten > 1e-5)
    if not ok.any(): return
    x, y, z, inten, col = x[ok], y[ok], z[ok], inten[ok], col[ok]
    if ztest and mirror_h is None:
        xi = np.clip(x.astype(int), 0, cv.W - 1); yi = np.clip(y.astype(int), 0, cv.H - 1)
        vis = cv.dep[yi, xi] > z * 0.995 - 0.3
        x, y, z, inten, col = x[vis], y[vis], z[vis], inten[vis], col[vis]
        if len(x) == 0: return
    r = np.maximum(min_r, size_m * cam.fpx / z)
    # energy spread over the disc, but a tiny far light still reads as a point of the given intensity
    w = inten * np.minimum(1.0, (min_r / r) ** 2 * 4 + 0.25)
    out = cv.emis if buf is None else buf
    small = r < 2.2
    if small.any(): _splat_points(out, x[small], y[small], w[small], col[small])
    for xi, yi, ri, wi, ci in zip(x[~small], y[~small], r[~small], w[~small], col[~small]):
        _disc(out, xi, yi, ri, ci * wi)

def _splat_points(buf, u, v, w, col):
    H, W = buf.shape[:2]
    ok = (u >= 0) & (u < W - 1) & (v >= 0) & (v < H - 1)
    if not ok.any(): return
    u, v, w, col = u[ok], v[ok], w[ok], col[ok]
    x0 = u.astype(np.int32); y0 = v.astype(np.int32); fx = (u - x0)[:, None]; fy = (v - y0)[:, None]
    wc = (w[:, None] * col).astype(F32)
    np.add.at(buf, (y0, x0), wc * (1 - fx) * (1 - fy)); np.add.at(buf, (y0, x0 + 1), wc * fx * (1 - fy))
    np.add.at(buf, (y0 + 1, x0), wc * (1 - fx) * fy); np.add.at(buf, (y0 + 1, x0 + 1), wc * fx * fy)

@lru_cache(64)
def _disc_k(r4):
    r = r4 / 4.0; n = int(math.ceil(r * 1.6)) + 1
    yy, xx = np.mgrid[-n:n + 1, -n:n + 1].astype(F32)
    d = np.sqrt(xx * xx + yy * yy) / max(0.5, r)
    return np.clip(1.15 - d, 0, 1) ** 1.6 + np.exp(-d * d * 2.2) * 0.25

def _disc(buf, x, y, r, c):
    k = _disc_k(int(round(min(r, 120) * 4))); n = k.shape[0] // 2
    H, W = buf.shape[:2]; xi, yi = int(round(x)), int(round(y))
    X0, Y0, X1, Y1 = xi - n, yi - n, xi + n + 1, yi + n + 1
    if X1 <= 0 or Y1 <= 0 or X0 >= W or Y0 >= H: return
    kx0, ky0 = max(0, -X0), max(0, -Y0); kx1, ky1 = k.shape[1] - max(0, X1 - W), k.shape[0] - max(0, Y1 - H)
    buf[max(0, Y0):min(H, Y1), max(0, X0):min(W, X1)] += k[ky0:ky1, kx0:kx1, None] * c

def soft_glow(buf, x, y, r, col, gain=1.0):
    """big soft additive glow (gaussian) at screen pos, cheap for r up to ~400 px."""
    H, W = buf.shape[:2]; r = max(1.0, float(r)); n = int(r * 2.6)
    X0, Y0, X1, Y1 = int(x) - n, int(y) - n, int(x) + n + 1, int(y) + n + 1
    x0, y0, x1, y1 = max(0, X0), max(0, Y0), min(W, X1), min(H, Y1)
    if x1 <= x0 or y1 <= y0: return
    gx = np.exp(-((np.arange(x0, x1, dtype=F32) - x) / r) ** 2 * 0.5); gy = np.exp(-((np.arange(y0, y1, dtype=F32) - y) / r) ** 2 * 0.5)
    buf[y0:y1, x0:x1] += (gy[:, None] * gx[None, :])[..., None] * (np.asarray(col, F32) * gain)

# ---------------------------------------------------------------- film finish
@lru_cache(8)
def _vig(W, H, amt):
    yy, xx = np.mgrid[0:H, 0:W].astype(F32)
    d2 = ((xx - W / 2) / (W / 2)) ** 2 * 0.85 + ((yy - H / 2) / (H / 2)) ** 2 * 0.55
    return np.clip(1 - amt * d2 ** 1.15, 0, 1).astype(F32)

@lru_cache(4)
def _grain_pool(H, W, n=10, seed=17):
    r = np.random.default_rng(seed); out = []
    for i in range(n):
        g = r.normal(0, 1, (H, W)).astype(F32)
        g = cv2.GaussianBlur(g, (0, 0), 0.7) * 1.6 + cv2.GaussianBlur(r.normal(0, 1, (H // 2, W // 2)).astype(F32), (0, 0), 0.8).repeat(2, 0).repeat(2, 1)[:H, :W] * 0.5
        out.append(g)
    return out

def filmic(x):
    """ACES-like filmic curve (Narkowicz) with a softer shoulder."""
    a, b, c, d, e = 2.51, 0.03, 2.43, 0.59, 0.14
    return np.clip((x * (a * x + b)) / (x * (c * x + d) + e), 0, 1)

def develop(img, fi, exposure=1.0, bloom_amt=0.06, halation=0.10, thresh=0.75, grain=0.028, vignette=0.32,
            lift=hexc('0b1320') * 0.45, warm_hi=hexc('fff1dc'), sat=0.92, band=True, clean_bars=False, contrast=1.0):
    """linear HDR -> display sRGB float [0, 1]."""
    H, W = img.shape[:2]
    x = img * exposure
    # halation: the red-orange fringe film gets around hot lights (only the brightest parts)
    lum = x[..., 0] * 0.3 + x[..., 1] * 0.59 + x[..., 2] * 0.11
    hot = np.clip(lum - thresh, 0, 8)
    sm = cv2.resize(hot, (W // 2, H // 2), interpolation=cv2.INTER_AREA)
    if halation:
        h1 = cv2.GaussianBlur(sm, (0, 0), 3.0)
        x += cv2.resize(h1, (W, H))[..., None] * (np.array([1.0, 0.28, 0.12], F32) * halation)
    if bloom_amt:
        q = cv2.resize(x, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
        qh = np.clip(q - thresh * 0.6, 0, 50)
        b1 = cv2.GaussianBlur(qh, (0, 0), 2.5); b2 = cv2.GaussianBlur(cv2.resize(qh, (W // 16, H // 16), interpolation=cv2.INTER_AREA), (0, 0), 3.0)
        x += (cv2.resize(b1, (W, H)) * 0.7 + cv2.resize(b2, (W, H)) * 1.0) * bloom_amt
    y = filmic(x)
    if contrast != 1.0: y = np.clip(0.5 + (y - 0.5) * contrast, 0, 1)
    l = y[..., 0] * 0.3 + y[..., 1] * 0.59 + y[..., 2] * 0.11
    if sat != 1.0: y = l[..., None] + (y - l[..., None]) * sat
    # split tone: shadows sit in navy/teal, highlights in dirty ivory
    sh = np.clip(1 - l * 3.0, 0, 1)[..., None]; hi = np.clip((l - 0.55) * 2.2, 0, 1)[..., None]
    y = y + lift * sh * 0.9
    y = y * (1 - hi * 0.12) + y * warm_hi * hi * 0.12
    if vignette: y *= _vig(W, H, float(vignette))[..., None]
    y = np.power(np.clip(y, 0, 1), 1 / 2.2)
    if grain:
        pool = _grain_pool(H, W); g = pool[fi % len(pool)]
        g = np.roll(g, ((fi * 7919) % H, (fi * 104729) % W), (0, 1))
        lv = y.mean(2)
        y += (g * grain * (0.35 + 0.8 * lv * (1 - lv) * 2.2))[..., None] * np.array([1.0, 0.97, 1.03], F32)
    return np.clip(y, 0, 1)

def letterbox(out, H_full, band_h, col=(0, 0, 0)):
    """place the rendered band (band_h tall) into a full-height frame with black bars."""
    W = out.shape[1]; full = np.empty((H_full, W, 3), F32); full[:] = col
    y0 = (H_full - band_h) // 2; full[y0:y0 + band_h] = out[:band_h]
    return full

def band_height(W, H):
    """2.39:1 picture band inside W x H (even number of rows)."""
    return min(H, int(round(W / ASPECT / 2)) * 2)

def dissolve(a, b, k): return a * (1 - k) + b * k
