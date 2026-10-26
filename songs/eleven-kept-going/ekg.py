"""Eleven Kept Going: the rendering kit.

Linear HDR float32 frames (H, W, 3) until develop(). World units are metres, +Y up, ground at y = 0.
A tiny 3-D engine (look-at camera, faceted meshes drawn supersampled with a painter's sort, Lambert + point lights),
a Falcon-style first stage / second stage / fairing built from it (no logos, no names), engine flames and smoke as
lit billboards, a star sky, water reflections, and the text layers (subtitles, mission captions, handwriting).
Every frame is a pure function of t: particles are closed-form in their age, so chunks render independently.
"""
import os, math
from functools import lru_cache
import numpy as np, cv2
if os.environ.get("EKG_THREADS"): cv2.setNumThreads(int(os.environ["EKG_THREADS"]))   # chunk workers run in parallel: keep each one single-threaded

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FONTS = os.path.join(ROOT, "assets", "fonts")
F32 = np.float32

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def sstep(a, b, x):
    if b == a: return 1.0 if x >= b else 0.0
    t = clamp((x - a) / (b - a)); return t * t * (3 - 2 * t)
def ease_io(t): t = clamp(t); return t * t * t * (t * (6 * t - 15) + 10)
def ease_out(t): t = clamp(t); return 1 - (1 - t) ** 3
def ease_in(t): t = clamp(t); return t ** 3
def lerp(a, b, t): return a + (b - a) * t
def lerpv(a, b, t): return np.asarray(a, F32) * (1 - t) + np.asarray(b, F32) * t
def hexc(h, gain=1.0):
    h = h.lstrip('#'); c = np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)], F32)
    return np.power(c, 2.2) * gain                       # sRGB -> linear
def nrm(v): v = np.asarray(v, F32); return v / max(1e-9, float(np.linalg.norm(v)))
def rng(seed): return np.random.default_rng(seed)

# ---------------------------------------------------------------- palette (linear)
WHITE = np.array([1.0, 1.0, 1.0], F32)
FLAME_W = np.array([1.0, 0.86, 0.62], F32)      # white-gold: ascent
FLAME_HOT = np.array([1.0, 0.95, 0.85], F32)
FLAME_O = np.array([1.0, 0.42, 0.10], F32)      # the one orange: entry burn onward
FLAME_O2 = np.array([1.0, 0.58, 0.22], F32)
MOON = np.array([0.55, 0.65, 0.9], F32)         # moonlight / night ambient
MOON_E = 0.12                                    # moonlight irradiance on a surface facing the moon (one scale for every shot)
FLOOD = np.array([1.0, 0.93, 0.80], F32)        # sodium-free pad floodlights (white, slightly warm)
SKY_TOP = np.array([0.0022, 0.0030, 0.0062], F32)
SKY_HOR = np.array([0.010, 0.013, 0.024], F32)

# ---------------------------------------------------------------- frame + blending
def frame(W, H, col=(0, 0, 0)): img = np.empty((H, W, 3), F32); img[:] = col; return img

def vgrad(W, H, top, bot, mid=None, mpos=0.5, y0=0.0, y1=1.0):
    y = np.clip((np.linspace(0, 1, H, dtype=F32) - y0) / max(1e-6, (y1 - y0)), 0, 1)[:, None]
    top, bot = np.asarray(top, F32), np.asarray(bot, F32)
    if mid is None: g = top[None] * (1 - y) + bot[None] * y
    else:
        mid = np.asarray(mid, F32); a = np.clip(y / mpos, 0, 1); b = np.clip((y - mpos) / (1 - mpos), 0, 1)
        g = np.where(y < mpos, top[None] * (1 - a) + mid[None] * a, mid[None] * (1 - b) + bot[None] * b)
    return np.repeat(g[:, None, :], W, 1).reshape(H, W, 3)

@lru_cache(48)
def gauss_kernel(r):
    """normalised-peak gaussian sprite, radius r px (sigma = r/2.5)."""
    n = int(math.ceil(r * 1.6)); x = np.arange(-n, n + 1, dtype=F32)
    g = np.exp(-(x / max(0.5, r / 2.5)) ** 2 / 2)
    return np.outer(g, g).astype(F32)

def splat(img, x, y, r, col, gain=1.0):
    """additive soft dot (r = visual radius in px)."""
    r = min(max(0.6, float(r)), 1.2 * max(img.shape[0], img.shape[1])); rk = round(r * 2) / 2 if r < 40 else round(r / 4) * 4
    k = gauss_kernel(rk); n = k.shape[0] // 2
    H, W = img.shape[:2]; xi, yi = int(round(x)), int(round(y))
    x0, y0, x1, y1 = xi - n, yi - n, xi + n + 1, yi + n + 1
    if x1 <= 0 or y1 <= 0 or x0 >= W or y0 >= H: return
    kx0, ky0 = max(0, -x0), max(0, -y0); kx1, ky1 = k.shape[1] - max(0, x1 - W), k.shape[0] - max(0, y1 - H)
    img[max(0, y0):min(H, y1), max(0, x0):min(W, x1)] += k[ky0:ky1, kx0:kx1, None] * (np.asarray(col, F32) * gain)[None, None]

def splats(img, xs, ys, rs, cols, gains):
    for x, y, r, c, g in zip(xs, ys, rs, cols, gains):
        if g > 1e-5: splat(img, x, y, r, c, g)

def glow_layer(W, H, pts, scale=0.25):
    """big soft glows on a low-res buffer (cheap), returned full size. pts: (x, y, r, col, gain)."""
    w, h = max(2, int(W * scale)), max(2, int(H * scale)); L = np.zeros((h, w, 3), F32)
    cap = 1.2 * max(w, h)
    for x, y, r, c, g in pts: splat(L, x * scale, y * scale, min(cap, max(0.8, r * scale)), c, g)
    return cv2.resize(L, (W, H), interpolation=cv2.INTER_LINEAR)

def over(img, layer, alpha):
    """img = img*(1-a) + layer*a   (alpha (H,W) or (H,W,1))."""
    a = alpha if alpha.ndim == 3 else alpha[..., None]
    img *= (1 - a); img += layer * a

def poly_mask(W, H, pts, ss=4, blur=0.0):
    m = np.zeros((H * ss, W * ss), np.uint8)
    p = np.round(np.asarray(pts, np.float64) * ss).astype(np.int32)
    cv2.fillPoly(m, [p], 255)
    m = cv2.resize(m, (W, H), interpolation=cv2.INTER_AREA).astype(F32) / 255
    return cv2.GaussianBlur(m, (0, 0), blur) if blur > 0 else m

def polyline_glow(img, pts, col, width=2.0, glow=6.0, gain=1.0, glow_gain=0.6, ss=2):
    """additive stroked polyline with a soft halo (for light trails and drawn lines)."""
    H, W = img.shape[:2]
    pts = np.asarray(pts, np.float64)
    if len(pts) < 2: return
    x0, y0 = np.floor(pts.min(0) - glow * 3 - width); x1, y1 = np.ceil(pts.max(0) + glow * 3 + width)
    x0, y0 = int(max(0, x0)), int(max(0, y0)); x1, y1 = int(min(W, x1)), int(min(H, y1))
    if x1 <= x0 or y1 <= y0: return
    w, h = x1 - x0, y1 - y0
    m = np.zeros((h * ss, w * ss), np.uint8)
    p = np.round((pts - [x0, y0]) * ss * 16).astype(np.int32)
    cv2.polylines(m, [p], False, 255, max(1, int(round(width * ss))), cv2.LINE_AA, shift=4)
    core = cv2.resize(m, (w, h), interpolation=cv2.INTER_AREA).astype(F32) / 255
    halo = cv2.GaussianBlur(core, (0, 0), glow) if glow > 0 else 0
    img[y0:y1, x0:x1] += (core * gain + halo * glow_gain * gain)[..., None] * np.asarray(col, F32)[None, None]

# ---------------------------------------------------------------- noise (cached textures)
@lru_cache(8)
def noise_tex(size=512, seed=1, octaves=6, persist=0.55):
    """tileable fractal value noise in [0,1]."""
    r = rng(seed); acc = np.zeros((size, size), F32); amp = 1.0; tot = 0.0
    for o in range(octaves):
        n = 4 * 2 ** o
        g = r.random((n, n)).astype(F32)
        g = np.tile(g, (3, 3))
        up = cv2.resize(g, (size * 3, size * 3), interpolation=cv2.INTER_CUBIC)[size:2 * size, size:2 * size]
        acc += up * amp; tot += amp; amp *= persist
    acc /= tot
    acc = (acc - acc.min()) / max(1e-6, acc.max() - acc.min())
    return acc.astype(F32)

def tile_sample(tex, W, H, sx, sy, ox, oy):
    """sample a tileable texture over a W x H frame: scale (tex px per screen px) and offset (tex px)."""
    th, tw = tex.shape[:2]
    xs = (np.arange(W, dtype=F32) * sx + ox) % tw; ys = (np.arange(H, dtype=F32) * sy + oy) % th
    mx, my = np.meshgrid(xs, ys)
    return cv2.remap(tex, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)

# ---------------------------------------------------------------- stars
@lru_cache(8)
def star_field(seed=11, n=5200):
    """unit-square star positions, magnitudes and tints (cached)."""
    r = rng(seed)
    x = r.random(n).astype(F32); y = r.random(n).astype(F32)
    m = r.power(0.18, n).astype(F32)                      # many faint, few bright
    bright = (1 - m) ** 6 * 1.0 + 0.004
    tint_t = r.random(n)
    tint = np.where(tint_t[:, None] < 0.15, [1.0, 0.82, 0.62], np.where(tint_t[:, None] > 0.85, [0.72, 0.82, 1.0], [1, 1, 1])).astype(F32)
    tw = r.random(n).astype(F32) * 6.28
    return x, y, bright, tint, tw

def stars(img, t, gain=1.0, seed=11, n=5200, ox=0.0, oy=0.0, scale=1.0, horizon=None, density=1.0, twinkle=0.35):
    """screen-space star field that wraps (pan with ox/oy in frame widths). Most stars are faint single pixels."""
    H, W = img.shape[:2]; S = max(W, H)
    x, y, b, tint, tw = star_field(seed, n)
    res = clamp((W * H) / (1920.0 * 1080.0), 0.08, 1.0)               # fewer stars in small previews (same look per pixel)
    k = int(len(x) * clamp(density, 0, 1) * res)
    X = (((x[:k] - ox) * scale) % 1.0) * S * max(1.0, scale) ** 0 - (S - W) / 2
    Y = (((y[:k] - oy) * scale) % 1.0) * S - (S - H) / 2
    ok = (X > -4) & (X < W + 4) & (Y > -4) & (Y < H + 4)
    if horizon is not None: ok &= Y < horizon
    X, Y, B, T, TW = X[ok], Y[ok], b[:k][ok], tint[:k][ok], tw[:k][ok]
    B = B * (1 - twinkle + twinkle * (0.5 + 0.5 * np.sin(t * 2.3 + TW * 7))) * gain
    if horizon is not None:
        B = B * np.clip((horizon - Y) / (H * 0.12), 0.15, 1)      # extinction near the horizon
    faint = B < 0.05
    xi = np.clip(X[faint].astype(np.int32), 0, W - 1); yi = np.clip(Y[faint].astype(np.int32), 0, H - 1)
    np.add.at(img, (yi, xi), (T[faint] * B[faint, None] * 1.6))
    sc = min(W, H) / 1080.0
    for xx, yy, bb, tt in zip(X[~faint], Y[~faint], B[~faint], T[~faint]):
        splat(img, xx, yy, max(0.6, (0.8 + min(2.0, bb * 2.5)) * sc), tt, bb * 2.2)

# ---------------------------------------------------------------- 3-D camera
class Cam:
    """look-at pinhole. fov = vertical field of view of a 1920x1080 frame; other aspect ratios keep the pixel scale
    of the short side (a 9:16 frame shows the same subject at the same size with more room above and below)."""
    def __init__(self, eye, target, W, H, fov=40.0, up=(0, 1, 0), roll=0.0, shift=(0.0, 0.0)):
        self.eye = np.asarray(eye, F32); f = nrm(np.asarray(target, F32) - self.eye)
        upv = np.asarray(up, F32)
        if abs(float(np.dot(f, nrm(upv)))) > 0.999: upv = np.array([0, 0, 1], F32)
        r = nrm(np.cross(f, upv)); u = np.cross(r, f)
        if roll: c, s = math.cos(roll), math.sin(roll); r, u = c * r + s * u, -s * r + c * u
        self.f, self.r, self.u = f, r.astype(F32), u.astype(F32)
        self.W, self.H = W, H; self.sx, self.sy = shift
        self.fpx = (min(W, H) / 2) / math.tan(math.radians(fov) / 2)
    def project(self, P):
        """P (..., 3) -> x, y (px), z (depth, m)."""
        d = np.asarray(P, F32) - self.eye
        z = d @ self.f; zz = np.maximum(z, 1e-3)
        return self.W / 2 + self.sx + (d @ self.r) / zz * self.fpx, self.H / 2 + self.sy - (d @ self.u) / zz * self.fpx, z
    def p1(self, p):
        x, y, z = self.project(np.asarray(p, F32)[None]); return float(x[0]), float(y[0]), float(z[0])
    def px_per_m(self, z): return self.fpx / max(1e-3, z)

# ---------------------------------------------------------------- meshes
class Mesh:
    """faces: list of (verts (k,3) float32, albedo rgb, emissive rgb or None, tag). Drawn with flat shading."""
    def __init__(self): self.faces = []
    def add(self, verts, alb, emi=None, tag=0): self.faces.append((np.asarray(verts, F32), np.asarray(alb, F32), emi, tag))
    def extend(self, other): self.faces.extend(other.faces); return self

def _rot_to(axis):
    """3x3 rotation taking +Y to `axis`."""
    a = nrm(axis); y = np.array([0, 1, 0], F32)
    v = np.cross(y, a); s = float(np.linalg.norm(v)); c = float(np.dot(y, a))
    if s < 1e-6: return np.eye(3, dtype=F32) if c > 0 else np.diag([1, -1, -1]).astype(F32)
    vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]], F32)
    return (np.eye(3, dtype=F32) + vx + vx @ vx * ((1 - c) / (s * s))).astype(F32)

def rot_axis(axis, ang):
    a = nrm(axis); c, s = math.cos(ang), math.sin(ang); x, y, z = a
    return np.array([[c + x * x * (1 - c), x * y * (1 - c) - z * s, x * z * (1 - c) + y * s],
                     [y * x * (1 - c) + z * s, c + y * y * (1 - c), y * z * (1 - c) - x * s],
                     [z * x * (1 - c) - y * s, z * y * (1 - c) + x * s, c + z * z * (1 - c)]], F32)

def lathe(profile, seg, alb_fn, emi_fn=None, a0=0.0, outward=False, cap_top=False):
    """surface of revolution about +Y. profile: [(y, r), ...] bottom to top. alb_fn(y_mid, ang) -> rgb.
    (the default winding faces inward, which suits hollow bells; outward=True for solid objects seen from outside)."""
    m = Mesh(); A = np.linspace(a0, a0 + 2 * math.pi, seg + 1)
    ca, sa = np.cos(A), np.sin(A)
    for (y0, r0), (y1, r1) in zip(profile[:-1], profile[1:]):
        for i in range(seg):
            v = [(r0 * ca[i], y0, r0 * sa[i]), (r0 * ca[i + 1], y0, r0 * sa[i + 1]), (r1 * ca[i + 1], y1, r1 * sa[i + 1]), (r1 * ca[i], y1, r1 * sa[i])]
            if outward: v = v[::-1]
            am = (A[i] + A[i + 1]) / 2
            m.add(v, alb_fn((y0 + y1) / 2, am), emi_fn((y0 + y1) / 2, am) if emi_fn else None)
    if cap_top:
        yt, rt_ = profile[-1]
        for i in range(seg):
            v = [(0, yt, 0), (rt_ * ca[i + 1], yt, rt_ * sa[i + 1]), (rt_ * ca[i], yt, rt_ * sa[i])]
            m.add(v if outward else v[::-1], alb_fn(yt, A[i]))
    return m

def box(c, size, alb, R=None, emi=None):
    """axis-aligned box (after rotation R) centred at c, size (sx, sy, sz)."""
    sx, sy, sz = [s / 2 for s in size]
    P = np.array([[-sx, -sy, -sz], [sx, -sy, -sz], [sx, sy, -sz], [-sx, sy, -sz], [-sx, -sy, sz], [sx, -sy, sz], [sx, sy, sz], [-sx, sy, sz]], F32)
    if R is not None: P = P @ np.asarray(R, F32).T
    P += np.asarray(c, F32)
    m = Mesh()
    for f in [(0, 1, 2, 3), (5, 4, 7, 6), (4, 0, 3, 7), (1, 5, 6, 2), (3, 2, 6, 7), (4, 5, 1, 0)]:
        m.add(P[list(f)], alb, emi)
    return m

def transform(mesh, R=None, T=(0, 0, 0)):
    out = Mesh(); R = np.eye(3, dtype=F32) if R is None else np.asarray(R, F32); T = np.asarray(T, F32)
    for v, a, e, tag in mesh.faces: out.faces.append((v @ R.T + T, a, e, tag))
    return out

class Lights:
    def __init__(self, ambient=(0.02, 0.025, 0.04)):
        self.ambient = np.asarray(ambient, F32); self.dirs = []; self.points = []
    def dir(self, d, col): self.dirs.append((nrm(d), np.asarray(col, F32))); return self
    def point(self, p, col, rng_=50.0): self.points.append((np.asarray(p, F32), np.asarray(col, F32), float(rng_))); return self
    def lamp(self, p, I, r0=2.0):
        """physical point light: radiant intensity I (rgb) -> irradiance I / (d^2 + r0^2), the same law the ground planes use."""
        I = np.asarray(I, F32); return self.point(p, I / (r0 * r0), r0)

def shade_faces(mesh, lights, eye):
    """flat Lambert shading per face (two-sided off: back faces culled by the caller)."""
    out = []
    for v, alb, emi, tag in mesh.faces:
        c = v.mean(0)
        n = np.cross(v[1] - v[0], v[2] - v[0]); nn = float(np.linalg.norm(n))
        if nn < 1e-9 and len(v) > 3: n = np.cross(v[2] - v[1], v[3] - v[1]); nn = float(np.linalg.norm(n))
        if nn < 1e-9: continue
        n = n / nn
        if float(np.dot(n, eye - c)) <= 0: continue                    # back face
        L = lights.ambient * (0.6 + 0.4 * max(0.0, float(n[1])))
        for d, col in lights.dirs: L = L + col * max(0.0, float(np.dot(n, -d)))
        for p, col, rr in lights.points:
            dv = p - c; dist = float(np.linalg.norm(dv)) + 1e-3
            L = L + col * max(0.0, float(np.dot(n, dv / dist))) / (1 + (dist / rr) ** 2)
        col = alb * L
        if emi is not None: col = col + np.asarray(emi, F32)
        out.append((v, col, c))
    return out

def draw_mesh(img, cam, mesh, lights, alpha_out=None, ss=3, pad=4, near=0.5, max_box=2600):
    """painter's-sorted flat polygons rendered supersampled in the mesh's screen bbox, composited over img.
    returns the coverage mask (H, W) (useful for occlusion / reflections)."""
    H, W = img.shape[:2]
    faces = shade_faces(mesh, lights, cam.eye)
    if not faces: return None
    items = []
    for v, col, c in faces:
        x, y, z = cam.project(v)
        if (z < near).any(): continue
        items.append((float(np.linalg.norm(c - cam.eye)), np.stack([x, y], 1), col))
    if not items: return None
    allp = np.concatenate([p for _, p, _ in items])
    x0, y0 = np.floor(allp.min(0)) - pad; x1, y1 = np.ceil(allp.max(0)) + pad
    x0, y0, x1, y1 = int(max(0, x0)), int(max(0, y0)), int(min(W, x1)), int(min(H, y1))
    if x1 <= x0 or y1 <= y0: return None
    w, h = x1 - x0, y1 - y0
    s = ss
    while w * s > max_box * 2 or h * s > max_box * 2: s -= 1
    s = max(1, s)
    buf = np.zeros((h * s, w * s, 3), F32); cov = np.zeros((h * s, w * s), np.uint8)
    items.sort(key=lambda it: -it[0])
    for _, p, col in items:
        q = np.round((p - [x0, y0]) * s * 16).astype(np.int32)
        cv2.fillConvexPoly(buf, q, tuple(float(c) for c in col), cv2.LINE_8, shift=4)
        cv2.fillConvexPoly(cov, q, 255, cv2.LINE_8, shift=4)
    if s > 1:
        buf = cv2.resize(buf, (w, h), interpolation=cv2.INTER_AREA)
        a = cv2.resize(cov, (w, h), interpolation=cv2.INTER_AREA).astype(F32) / 255
    else: a = cov.astype(F32) / 255
    roi = img[y0:y1, x0:x1]
    roi *= (1 - a)[..., None]; roi += buf                 # buf is already coverage-weighted (premultiplied by the AREA downsample)
    if alpha_out is not None: alpha_out[y0:y1, x0:x1] = np.maximum(alpha_out[y0:y1, x0:x1], a)
    full = np.zeros((H, W), F32); full[y0:y1, x0:x1] = a
    return full

def draw_mesh_wire(img, cam, mesh, edge_col, fill_col, fill_a=0.5, width=1.2, ss=2, near=0.5, lights=None):
    """technical-drawing look: back faces culled, painter's sorted; each face filled (fill_col, optionally shaded) at
    fill_a, then its outline stroked in edge_col."""
    H, W = img.shape[:2]
    items = []
    for v, alb, emi, tag in mesh.faces:
        c = v.mean(0); n = np.cross(v[1] - v[0], v[2] - v[0]); nn = float(np.linalg.norm(n))
        if nn < 1e-9: continue
        n = n / nn
        if float(np.dot(n, cam.eye - c)) <= 0: continue
        x, y, z = cam.project(v)
        if (z < near).any(): continue
        sh = 1.0
        if lights is not None:
            sh = 0.35 + 0.65 * max(0.0, float(np.dot(n, -lights.dirs[0][0]))) if lights.dirs else 1.0
        items.append((float(np.linalg.norm(c - cam.eye)), np.stack([x, y], 1), sh))
    if not items: return
    items.sort(key=lambda it: -it[0])
    allp = np.concatenate([p for _, p, _ in items])
    x0, y0 = np.floor(allp.min(0)) - 4; x1, y1 = np.ceil(allp.max(0)) + 4
    x0, y0, x1, y1 = int(max(0, x0)), int(max(0, y0)), int(min(W, x1)), int(min(H, y1))
    if x1 <= x0 or y1 <= y0: return
    w, h = x1 - x0, y1 - y0
    buf = np.zeros((h * ss, w * ss, 3), F32); cov = np.zeros((h * ss, w * ss), F32)
    fc = np.asarray(fill_col, F32); ec = np.asarray(edge_col, F32)
    lw = max(1, int(round(width * ss)))
    for _, p, sh in items:
        q = np.round((p - [x0, y0]) * ss * 16).astype(np.int32)
        cv2.fillConvexPoly(buf, q, tuple(float(c) for c in fc * sh * fill_a), cv2.LINE_8, shift=4)
        cv2.fillConvexPoly(cov, q, fill_a, cv2.LINE_8, shift=4)
        cv2.polylines(buf, [q], True, tuple(float(c) for c in ec), lw, cv2.LINE_AA, shift=4)
        cv2.polylines(cov, [q], True, 1.0, lw, cv2.LINE_AA, shift=4)
    if ss > 1:
        buf = cv2.resize(buf, (w, h), interpolation=cv2.INTER_AREA); cov = cv2.resize(cov, (w, h), interpolation=cv2.INTER_AREA)
    roi = img[y0:y1, x0:x1]
    roi *= (1 - np.clip(cov, 0, 1))[..., None]; roi += buf

# ---------------------------------------------------------------- the vehicle (no logos, no names)
R_BODY = 1.83          # 3.66 m core
R_FAIR = 2.6           # 5.2 m fairing
L_S1 = 41.0            # first-stage tank section (white)
L_INT = 6.5            # interstage (black), grid fins near its top
L_S2 = 12.5            # second stage (white)
L_FAIR = 13.1          # fairing
WHITE_PAINT = np.array([0.78, 0.79, 0.80], F32)
SOOT = np.array([0.05, 0.045, 0.04], F32)
BLACK_CF = np.array([0.035, 0.036, 0.04], F32)
GRIDFIN = np.array([0.20, 0.20, 0.21], F32)
METAL = np.array([0.35, 0.33, 0.30], F32)

def _soot(y, ang, amount, seed=3):
    """landed-booster soot streaks: darker toward the top, streaky around the circumference."""
    if amount <= 0: return 0.0
    st = 0.5 + 0.5 * math.sin(ang * 7 + 1.3) * math.sin(ang * 13 + 0.7) + 0.3 * math.sin(ang * 29 + seed)
    h = clamp((y - 6) / 34)
    return clamp(amount * (0.25 + 0.75 * h) * (0.55 + 0.45 * st), 0, 0.92)

def stage1_mesh(seg=96, soot=0.0, legs=0.0, fins=0.0, with_engines=True, leg_seg=1):
    """first stage incl. interstage, base at y=0 (engine exit plane ~ -1.2 m). legs: 0 stowed .. 1 deployed.
    fins: 0 stowed (folded up) .. 1 deployed (horizontal)."""
    def alb(y, a):
        if y > L_S1: return BLACK_CF
        base = WHITE_PAINT * (1 - _soot(y, a, soot)) + SOOT * _soot(y, a, soot)
        if y < 1.0: base = base * 0.55                         # the octaweb skirt is darker
        return base
    ys = [0.0, 1.0] + ([float(v) for v in np.linspace(2.0, L_S1, 21)] if soot > 0 else [6.0, 12, 20, 28, 36, L_S1])
    prof = [(y, R_BODY) for y in ys] + [(L_S1 + 0.01, R_BODY), (L_S1 + L_INT, R_BODY)]
    m = lathe(prof, seg, alb)
    # top cap of the interstage (open ring seen from above during the descent)
    cap = Mesh(); A = np.linspace(0, 2 * math.pi, seg + 1); yt = L_S1 + L_INT
    for i in range(seg):
        cap.add([(0, yt, 0), (R_BODY * math.cos(A[i + 1]), yt, R_BODY * math.sin(A[i + 1])), (R_BODY * math.cos(A[i]), yt, R_BODY * math.sin(A[i]))], np.array([0.02, 0.02, 0.022], F32))
    m.extend(cap)
    if with_engines: m.extend(engines_mesh())
    m.extend(fins_mesh(fins))
    m.extend(legs_mesh(legs, soot))
    return m

def engines_mesh(seg=18):
    """octaweb: 8 + 1 bells under the base."""
    m = Mesh()
    pos = [(0, 0)] + [(1.25 * math.cos(k * math.pi / 4 + math.pi / 8), 1.25 * math.sin(k * math.pi / 4 + math.pi / 8)) for k in range(8)]
    for (px, pz) in pos:
        prof = [(-1.25, 0.46), (-0.6, 0.33), (0.0, 0.22)]
        e = lathe(prof, seg, lambda y, a: METAL * (0.6 + 0.4 * (y + 1.25)))
        m.extend(transform(e, None, (px, 0, pz)))
    return m

def fins_mesh(dep, n=4, cells=5):
    """grid fins: lattice panels (a frame and a grid of thin bars) hinged near the top of the interstage.
    stowed: folded up flat against the body; deployed: sticking straight out."""
    m = Mesh(); yh = L_S1 + L_INT - 2.1
    w, l, th = 1.2, 1.5, 0.12
    ang = (1 - dep) * math.radians(86)                     # 86 deg = folded up along the body
    bar = 0.05
    for k in range(n):
        a = k * math.pi / 2 + math.pi / 4
        out = np.array([math.cos(a), 0, math.sin(a)], F32); tan = np.array([-math.sin(a), 0, math.cos(a)], F32)
        hinge = out * R_BODY + np.array([0, yh, 0], F32)
        R = rot_axis(tan, ang)
        d_out = R @ out; d_n = R @ np.array([0, 1, 0], F32)
        c0 = hinge + d_out * 0.1
        Rb = np.stack([d_out, d_n, tan], 1)                   # local (out, normal, tan) -> world
        def bx(cu, cv, su, sv, col):
            c = c0 + d_out * cu + tan * cv
            m.extend(box(c, (su, th, sv), col, Rb))
        # frame
        bx(l / 2, -w / 2, l, bar * 2, GRIDFIN); bx(l / 2, w / 2, l, bar * 2, GRIDFIN)
        bx(0.0, 0.0, bar * 2, w, GRIDFIN); bx(l, 0.0, bar * 2, w, GRIDFIN)
        # lattice bars (two diagonal-ish families drawn straight for legibility)
        for i in range(1, cells):
            bx(l * i / cells, 0.0, bar, w, GRIDFIN * 0.85)
            bx(l / 2, -w / 2 + w * i / cells, l, bar, GRIDFIN * 0.85)
    return m

def legs_mesh(dep, soot=0.0, n=4):
    """four landing legs: stowed flat along the lower body (tips up), deployed swung down ~ 60 deg out."""
    m = Mesh(); L = 9.6; w = 1.05; th = 0.32
    ang = lerp(math.radians(4), math.radians(118), ease_io(dep))     # 0 = along the body, tip up; 118 deg = splayed down-out
    for k in range(n):
        a = k * math.pi / 2
        out = np.array([math.cos(a), 0, math.sin(a)], F32); tan = np.array([-math.sin(a), 0, math.cos(a)], F32)
        hinge = out * (R_BODY + 0.18) + np.array([0, 0.6, 0], F32)
        d = rot_axis(tan, -ang) @ np.array([0, 1, 0], F32)             # leg direction from the hinge (swings outward)
        nrm_ = np.cross(d, tan)
        tip = hinge + d * L
        col = BLACK_CF * (1 - 0.3 * soot)
        # tapered box beam in 3 segments (slightly thicker in the middle), carbon black with a lighter edge rail
        sec = [(0.0, w, th), (0.45, w * 0.92, th * 1.25), (1.0, w * 0.55, th * 0.8)]
        for (u0, w0, t0), (u1, w1, t1) in zip(sec[:-1], sec[1:]):
            c0 = hinge + d * (L * u0); c1 = hinge + d * (L * u1)
            P0 = [c0 - tan * w0 / 2 + nrm_ * t0 / 2, c0 + tan * w0 / 2 + nrm_ * t0 / 2, c0 + tan * w0 / 2 - nrm_ * t0 / 2, c0 - tan * w0 / 2 - nrm_ * t0 / 2]
            P1 = [c1 - tan * w1 / 2 + nrm_ * t1 / 2, c1 + tan * w1 / 2 + nrm_ * t1 / 2, c1 + tan * w1 / 2 - nrm_ * t1 / 2, c1 - tan * w1 / 2 - nrm_ * t1 / 2]
            shades = [1.0, 0.85, 0.7, 0.85]
            for i in range(4):
                j = (i + 1) % 4
                m.add([P0[i], P0[j], P1[j], P1[i]], col * shades[i])
        # foot pad: a round, flat pad on a short ball joint (lies flat on the ground when deployed)
        if dep > 0.3:
            pad = lathe([(0.0, 0.62), (0.16, 0.66), (0.30, 0.42), (0.55, 0.16)], 20, lambda y, a_: METAL * 0.55, outward=True, cap_top=True)
            m.extend(transform(pad, None, tip + d * 0.12 - np.array([0, 0.35, 0], F32)))
        # telescoping strut (a thin box from the body higher up to mid-leg)
        if dep > 0.02:
            s0 = out * (R_BODY + 0.1) + np.array([0, 7.5, 0], F32); s1 = hinge + d * (L * 0.62)
            mid = (s0 + s1) / 2; ln = float(np.linalg.norm(s1 - s0)); R = _rot_to(s1 - s0)
            m.extend(box(mid, (0.26, ln, 0.26), METAL * 0.7, R))
    return m

def upper_mesh(seg=96, fairing=True):
    """second stage + fairing, base at y=0 (sits on the interstage top)."""
    def alb(y, a): return WHITE_PAINT
    prof = [(0, R_BODY), (L_S2, R_BODY)]
    m = lathe(prof, seg, alb)
    if fairing:
        yb = L_S2
        fp = [(yb, R_BODY), (yb + 0.7, R_BODY + 0.42), (yb + 1.4, R_FAIR), (yb + 6.2, R_FAIR)]
        Rn = R_FAIR; Ln = L_FAIR - 6.2; rho = (Rn * Rn + Ln * Ln) / (2 * Rn)
        for k in range(1, 13):                                     # tangent-ogive nose
            x = Ln * (1 - (1 - k / 12) ** 1.25)
            fp.append((yb + 6.2 + x, max(0.0, math.sqrt(max(0.0, rho * rho - x * x)) - (rho - Rn)) + 0.02))
        m.extend(lathe(fp, seg, lambda y, a: WHITE_PAINT * 0.98))
    return m

def mvac_mesh(seg=32):
    """second-stage vacuum nozzle under the second stage (visible after separation)."""
    prof = [(-3.0, 1.55), (-1.6, 1.0), (-0.4, 0.45), (0.0, 0.35)]
    return lathe(prof, seg, lambda y, a: np.array([0.22, 0.2, 0.19], F32) * (0.6 + 0.2 * (y + 3)))

def place(mesh, pos, axis=(0, 1, 0), spin=0.0):
    R = _rot_to(axis) @ rot_axis((0, 1, 0), spin)
    return transform(mesh, R, pos)

# ---------------------------------------------------------------- flames, plumes, smoke
def scaled_cam(cam, s):
    """the same camera rendering into a frame s times the size."""
    c = Cam.__new__(Cam)
    c.eye, c.f, c.r, c.u = cam.eye, cam.f, cam.r, cam.u
    c.W, c.H = max(2, int(round(cam.W * s))), max(2, int(round(cam.H * s)))
    c.sx, c.sy = cam.sx * s, cam.sy * s; c.fpx = cam.fpx * s
    return c

def flame_lowres(img, cam, nozzle, direction, length, radius, s=0.25, **kw):
    """a soft plume or light shaft rendered into a small buffer and scaled up (far cheaper, identical when soft)."""
    H, W = img.shape[:2]
    c2 = scaled_cam(cam, s)
    buf = np.zeros((c2.H, c2.W, 3), F32)
    occ = kw.pop("occ", None)
    if occ is not None:
        occ = (cv2.resize(occ[0], (c2.W, c2.H), interpolation=cv2.INTER_AREA), cv2.resize(occ[1], (c2.W, c2.H), interpolation=cv2.INTER_NEAREST))
    flame(buf, c2, nozzle, direction, length, radius, occ=occ, **kw)
    img += cv2.resize(buf, (W, H), interpolation=cv2.INTER_LINEAR)

def flame(img, cam, nozzle, direction, length, radius, col=FLAME_W, gain=1.0, flick=0.0, n=26, t=0.0, core_gain=1.0, expand=1.0,
          diamonds=0.0, occ=None, seed=0):
    """additive exhaust, rendered as a continuous emitting volume: gaussian samples packed along the axis closely enough
    (<= 0.3 radius apart on screen) that they merge into one smooth plume from any angle. `gain` sets the brightness of
    the plume seen side-on; seen end-on it piles up the way a real volume does. diamonds: Mach-diamond banding (sea level).
    occ = (coverage, depth) of a vehicle drawn just before: samples behind it only show around its silhouette."""
    d = nrm(direction); H, W = img.shape[:2]; noz = np.asarray(nozzle, F32)
    m = 160
    ue = np.linspace(0, 1, m + 1, dtype=F32)                       # interval edges
    se = length * ue ** 1.15
    Pe = noz[None] + d[None] * se[:, None]
    xe, ye, ze = cam.project(Pe)
    if (ze <= 0.5).all(): return []
    re_m = radius * (0.55 + 2.4 * ue ** 1.3 * expand)
    re_px = re_m * cam.fpx / np.maximum(ze, 1e-3)
    seg_px = np.hypot(np.diff(xe), np.diff(ye))
    rmin = np.maximum(np.minimum(re_px[:-1], re_px[1:]), 0.6)
    nk = np.clip(np.ceil(seg_px / (0.3 * rmin)), 1, 64)
    if nk.sum() > 3000: nk = np.maximum(1, np.floor(nk * 3000 / nk.sum()))
    nk = nk.astype(np.int32)
    # subdivide each interval into nk samples
    k_of = np.repeat(np.arange(m), nk)
    j = np.arange(len(k_of)) - np.repeat(np.cumsum(nk) - nk, nk)
    frac = (j + 0.5) / nk[k_of]
    u = ue[k_of] + (ue[k_of + 1] - ue[k_of]) * frac
    ds = (se[k_of + 1] - se[k_of]) / nk[k_of]
    s_m = length * u ** 1.15
    P = noz[None] + d[None] * s_m[:, None]
    x, y, z = cam.project(P)
    r_m = radius * (0.55 + 2.4 * u ** 1.3 * expand)
    r_px = r_m * cam.fpx / np.maximum(z, 1e-3)
    ok = (z > 0.5) & (r_px < 1.5 * max(W, H)) & (x > -2 * r_px - W) & (x < 2 * W + 2 * r_px) & (y > -2 * r_px - H) & (y < 2 * H + 2 * r_px)
    hot = np.exp(-u * 3.2)
    wob = 1 + flick * (0.22 * np.sin(t * 41 + u * 44 + seed) + 0.12 * np.sin(t * 67 - u * 90 + 2 * seed)) * u
    B = gain * (0.55 + 0.45 * np.exp(-u * 2.2)) * (1 - 0.55 * u) * wob * np.clip((1 - u) / 0.35, 0, 1) ** 0.8
    if diamonds > 0:
        B *= 1 + diamonds * 0.8 * np.maximum(0, np.cos(2 * math.pi * s_m / max(0.5, radius * 2.2))) ** 6 * np.exp(-u * 2.5)
    g = B * ds / np.maximum(r_m, 1e-3)                            # peak per sample so the merged plume has brightness B
    C = col[None] * (1 - hot[:, None]) + FLAME_HOT[None] * hot[:, None]
    behind = np.zeros(len(x), bool)
    if occ is not None:
        cov_o, dep_o = occ
        xi = np.clip(x.astype(np.int32), 0, W - 1); yi = np.clip(y.astype(np.int32), 0, H - 1)
        behind = (cov_o[yi, xi] > 0.5) & (dep_o[yi, xi] < z - 0.3)
    pts = []
    lay_back = np.zeros_like(img) if behind.any() else None
    for i in np.nonzero(ok & (g > 1e-5))[0]:
        tgt = lay_back if behind[i] else img
        if r_px[i] < 60: splat(tgt, x[i], y[i], r_px[i], C[i], g[i])
        else: pts.append((x[i], y[i], r_px[i], C[i], g[i], behind[i]))
    big_f = [p[:5] for p in pts if not p[5]]; big_b = [p[:5] for p in pts if p[5]]
    if big_f: img += glow_layer(W, H, big_f, 0.25)
    if big_b: lay_back += glow_layer(W, H, big_b, 0.25)
    # core: small and very hot at the nozzle
    xc, yc, zc = cam.p1(noz + d * radius * 0.6)
    if zc > 0.5:
        rc = radius * 0.9 * cam.px_per_m(zc)
        cb = False
        if occ is not None:
            xi, yi = int(np.clip(xc, 0, W - 1)), int(np.clip(yc, 0, H - 1)); cb = occ[0][yi, xi] > 0.5 and occ[1][yi, xi] < zc - 0.3
        tgt = lay_back if (cb and lay_back is not None) else img
        if cb and lay_back is None: lay_back = np.zeros_like(img); tgt = lay_back
        splat(tgt, xc, yc, rc, FLAME_HOT, gain * 3.0 * core_gain / max(1.0, rc * 0.02))
    if lay_back is not None:
        img += lay_back * (1 - occ[0])[..., None]
    return pts

def puff_tex(seed, size=96):
    """soft billowy smoke sprite in [0,1] (alpha)."""
    return _puff(seed % 12, size)

@lru_cache(64)
def _puff(seed, size):
    """a soft billow: gaussian body, edges eaten by warped noise (no hard lumps), fading well inside the square."""
    r = rng(seed + 100); s = size
    yy, xx = np.mgrid[0:s, 0:s].astype(F32); cx = cy = (s - 1) / 2
    n1 = cv2.resize(noise_tex(128, 30 + seed, 5, 0.6), (s, s), interpolation=cv2.INTER_CUBIC)
    n2 = cv2.resize(noise_tex(128, 60 + seed, 4, 0.55), (s, s), interpolation=cv2.INTER_CUBIC)
    wx = (n1 - 0.5) * s * 0.16; wy = (n2 - 0.5) * s * 0.16
    d = np.sqrt((xx + wx - cx) ** 2 + (yy + wy - cy) ** 2) / (s / 2)
    body = np.exp(-(d / 0.55) ** 2 * 1.6)
    for _ in range(2):                                   # one or two soft sub-billows
        ox, oy = r.normal(0, s * 0.12, 2); rr = s * r.uniform(0.18, 0.26)
        body = np.maximum(body, np.exp(-(((xx + wx - cx - ox) ** 2 + (yy + wy - cy - oy) ** 2) / (rr * rr)) * 1.6) * 0.85)
    det = cv2.resize(noise_tex(128, 90 + seed, 6, 0.62), (s, s), interpolation=cv2.INTER_CUBIC)
    a = np.clip(body * (0.65 + 0.7 * (det - 0.5)), 0, 1)
    d0 = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / (s / 2)
    win = np.clip((0.98 - d0) / 0.35, 0, 1); win = win * win * (3 - 2 * win)   # never reaches the square's edge
    return (a * win).astype(F32)

@lru_cache(16)
def _grad(s):
    yy, xx = np.mgrid[0:s, 0:s].astype(F32); c = (s - 1) / 2
    return (xx - c) / (s / 2), (yy - c) / (s / 2)

def smoke_sprite(img, x, y, r_px, alpha, col, seed, rot=0.0, emissive=None, col2=None, ldir=None):
    """composite one lit smoke billboard: col = lit colour (linear), alpha in [0,1]; emissive adds glow (flame-lit interior).
    col2 + ldir (screen-space unit vector toward the key light): the billow is shaded from col (lit side) to col2.
    The billow is rotated and shaded at its texture's resolution and only then scaled to its size on screen (it is soft,
    so this looks the same as shading every screen pixel and is several times faster for big puffs)."""
    if r_px < 0.8 or alpha < 0.004: return
    H, W = img.shape[:2]
    s = int(max(4, min(1600, r_px * 2)))
    if x + s / 2 < 0 or y + s / 2 < 0 or x - s / 2 > W or y - s / 2 > H: return
    x0, y0 = int(round(x - s / 2)), int(round(y - s / 2))
    ax0, ay0 = max(0, -x0), max(0, -y0); ax1, ay1 = s - max(0, x0 + s - W), s - max(0, y0 + s - H)
    if ax1 <= ax0 or ay1 <= ay0: return
    ts = 96 if s <= 96 else 192
    tex = _puff(seed % 12, ts)
    if rot:
        M = cv2.getRotationMatrix2D((ts / 2, ts / 2), rot, 1.0); tex = cv2.warpAffine(tex, M, (ts, ts))
    c1 = np.asarray(col, F32)
    if col2 is not None and ldir is not None:
        gx, gy = _grad(ts)
        k = np.clip(0.5 + 0.65 * (gx * ldir[0] + gy * ldir[1]), 0, 1)
        c2 = np.asarray(col2, F32)
        pre = tex[..., None] * (c2[None, None] + (c1 - c2)[None, None] * k[..., None])
    else:
        pre = tex[..., None] * c1[None, None]
    if emissive is not None:
        pre = pre + (tex ** 1.5)[..., None] * (np.asarray(emissive, F32) * alpha ** 0.5)[None, None]
    interp = cv2.INTER_LINEAR if s >= ts else cv2.INTER_AREA
    if (ax1 - ax0) * (ay1 - ay0) < s * s * 0.6:                 # mostly off screen: scale only the visible window
        sc = ts / s
        M2 = np.float32([[sc, 0, ax0 * sc + 0.5 * sc - 0.5], [0, sc, ay0 * sc + 0.5 * sc - 0.5]])
        a = cv2.warpAffine(tex, M2, (ax1 - ax0, ay1 - ay0), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP)
        P = cv2.warpAffine(pre, M2, (ax1 - ax0, ay1 - ay0), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP)
    else:
        a = cv2.resize(tex, (s, s), interpolation=interp)[ay0:ay1, ax0:ax1]
        P = cv2.resize(pre, (s, s), interpolation=interp)[ay0:ay1, ax0:ax1]
    roi = img[y0 + ay0:y0 + ay1, x0 + ax0:x0 + ax1]
    roi *= (1 - a * alpha)[..., None]
    roi += P * alpha

# ---------------------------------------------------------------- develop (HDR -> sRGB float, before text)
def bloom(img, strength=0.08, thresh=0.8, levels=6):
    H, W = img.shape[:2]
    lvl = cv2.resize(img, (W // 2, H // 2), interpolation=cv2.INTER_AREA); lvl = np.maximum(lvl - thresh, 0)
    acc_levels = []
    for i in range(levels):
        if i: lvl = cv2.resize(lvl, (max(1, lvl.shape[1] // 2), max(1, lvl.shape[0] // 2)), interpolation=cv2.INTER_AREA)
        acc_levels.append(cv2.GaussianBlur(lvl, (0, 0), 1.6) * (0.92 ** i))
    acc = acc_levels[-1]
    for g in reversed(acc_levels[:-1]):
        acc = cv2.resize(acc, (g.shape[1], g.shape[0]), interpolation=cv2.INTER_LINEAR) + g
    return img + cv2.resize(acc, (W, H), interpolation=cv2.INTER_LINEAR) * strength

def aces(x):
    a, b, c, d, e = 2.51, 0.03, 2.43, 0.59, 0.14
    return np.clip((x * (a * x + b)) / (x * (c * x + d) + e), 0, 1)

@lru_cache(4)
def _vig(W, H, k):
    y, x = np.mgrid[0:H, 0:W].astype(F32); x = (x + 0.5 - W / 2) / (W / 2); y = (y + 0.5 - H / 2) / (H / 2)
    r = np.sqrt(x * x + y * y) / 1.414
    return (1 - k * np.power(r, 2.4)).astype(F32)

@lru_cache(8)
def _grain(H, W, i):
    g = np.random.default_rng(i * 7919 + 13).standard_normal((H // 2 + 1, W // 2 + 1)).astype(F32)
    return cv2.resize(g, (W, H), interpolation=cv2.INTER_LINEAR)

def develop(img, fi, exposure=1.0, bloom_k=0.085, thresh=0.8, grain=0.022, vignette=0.28, lift=0.0, sat=1.0):
    """HDR linear -> display sRGB float [0,1]: bloom, ACES, vignette, film grain (filmic, ~16 mm)."""
    x = bloom(img * exposure, bloom_k, thresh)
    y = aces(x)
    if sat != 1.0:
        l = y.mean(2, keepdims=True); y = l + (y - l) * sat
    if vignette: y *= _vig(y.shape[1], y.shape[0], float(vignette))[..., None]
    y = np.power(np.clip(y, 0, 1), 1 / 2.2)
    if lift: y = y * (1 - lift) + lift
    if grain:
        n = _grain(y.shape[0], y.shape[1], fi % 8)
        dy, dx = (fi * 7919) % y.shape[0], (fi * 104729) % y.shape[1]
        n = np.roll(n, (dy, dx), (0, 1)) * grain
        y += (n * (0.35 + 0.65 * (1 - y.mean(2))))[..., None]
    return np.clip(y, 0, 1)
