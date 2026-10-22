"""IN THE WALLS — tiny planar ray-caster for CCTV night-vision plates.

A camera feed = a static PLATE (ray-cast once per camera and frame size, cached on disk) plus per-frame layers:
  lum   : IR night-vision luminance (illuminator at the camera: no shadows, 1/d^2 falloff, hot centre)
  irr   : IR irradiance alone (to light things drawn on walls later: notes, calendars, marks)
  heat  : thermal-camera base (people hot, electronics warm, walls cool)
  atlas : per-pixel lookup into the camera's WALL ATLAS (writable wall rects -> texture px), so writing that
          appears 'inside the walls' is drawn once in wall space and remapped to the screen every frame
  lights: named light maps (TV glow, window, street...) multiplied by a time curve per frame
The lens is a wide CCTV lens with barrel distortion; forward projection of world points uses the same model.
"""
import os, math, hashlib
import numpy as np, cv2

# ------------------------------------------------------------------ noise (deterministic)
def _vnoise(n, cells, seed):
    r = np.random.default_rng(seed); g = r.random((cells, cells)).astype(np.float32)
    g = np.concatenate([g, g[:1]], 0); g = np.concatenate([g, g[:, :1]], 1)          # tileable
    return cv2.resize(g, (n + n // cells, n + n // cells), interpolation=cv2.INTER_CUBIC)[:n, :n]
def _fbm(n, seed, octaves=((8, 0.5), (32, 0.3), (128, 0.2))):
    return sum(_vnoise(n, c, seed + i) * w for i, (c, w) in enumerate(octaves))
NOISE = None
def noise():
    global NOISE
    if NOISE is None:
        NOISE = {"fbm": _fbm(512, 7), "fine": _vnoise(512, 256, 11), "low": _vnoise(512, 6, 13)}
    return NOISE
def samp(tex, u, v, scale):
    n = tex.shape[0]
    iu = (np.floor(u * scale).astype(np.int64)) % n; iv = (np.floor(v * scale).astype(np.int64)) % n
    return tex[iv, iu]

# ------------------------------------------------------------------ primitives
class Rect:
    """Planar rectangle: corner p0, edge vectors a (u axis) and b (v axis). mat(u, v, P) -> albedo."""
    def __init__(s, p0, a, b, mat=0.5, heat=0.25, emit=0.0, name=None, write=None, two_sided=True, ppm=200):
        s.p0 = np.array(p0, np.float32); s.a = np.array(a, np.float32); s.b = np.array(b, np.float32)
        s.U = float(np.linalg.norm(s.a)); s.V = float(np.linalg.norm(s.b))
        s.ea = s.a / s.U; s.eb = s.b / s.V
        n = np.cross(s.ea, s.eb); s.n = n / np.linalg.norm(n)
        s.mat, s.heat, s.emit, s.name, s.write, s.ppm = mat, heat, emit, name, write, ppm
    def hit(s, O, D):
        dn = D @ s.n; num = float((s.p0 - O) @ s.n)
        with np.errstate(divide='ignore', invalid='ignore'):
            t = num / dn
        P = O + D * t[..., None]; Q = P - s.p0
        u = Q @ s.ea; v = Q @ s.eb
        ok = (t > 0.02) & (u >= 0) & (u <= s.U) & (v >= 0) & (v <= s.V) & np.isfinite(t)
        return t, ok, u, v, np.broadcast_to(s.n, D.shape)

class Poly(Rect):
    """Planar convex polygon given by world vertices (coplanar); u, v are coordinates in its own frame."""
    def __init__(s, verts, **kw):
        V = np.array(verts, np.float32); p0 = V[0]; a = V[1] - V[0]
        b0 = V[2] - V[0]; nrm = np.cross(a, b0); b = np.cross(nrm, a); b = b / np.linalg.norm(b) * np.linalg.norm(a)
        super().__init__(p0, a, b, **kw)
        uv = np.stack([(V - p0) @ s.ea, (V - p0) @ s.eb], 1)
        mn = uv.min(0); mx = uv.max(0)
        s.p0 = (p0 + mn[0] * s.ea + mn[1] * s.eb).astype(np.float32)
        s.uv = uv - mn; s.U = float(mx[0] - mn[0]); s.V = float(mx[1] - mn[1])
    def hit(s, O, D):
        dn = D @ s.n; num = float((s.p0 - O) @ s.n)
        with np.errstate(divide='ignore', invalid='ignore'):
            t = num / dn
        P = O + D * t[..., None]; Q = P - s.p0
        u = Q @ s.ea; v = Q @ s.eb; ok = (t > 0.02) & np.isfinite(t)
        k = len(s.uv)
        # convex inside test (consistent orientation)
        area = 0.0
        for i in range(k):
            x0, y0 = s.uv[i]; x1, y1 = s.uv[(i + 1) % k]; area += x0 * y1 - x1 * y0
        sg = 1.0 if area > 0 else -1.0
        for i in range(k):
            x0, y0 = s.uv[i]; x1, y1 = s.uv[(i + 1) % k]
            ok &= ((x1 - x0) * (v - y0) - (y1 - y0) * (u - x0)) * sg >= -1e-6
        return t, ok, u, v, np.broadcast_to(s.n, D.shape)

class Ell:
    """Axis-aligned ellipsoid (pillows, blanket lumps, heads, lamp shades). u, v = longitude/latitude-ish."""
    def __init__(s, c, r, mat=0.5, heat=0.3, emit=0.0, name=None, cut_y=None):
        s.c = np.array(c, np.float32); s.r = np.array(r, np.float32); s.mat, s.heat, s.emit, s.name = mat, heat, emit, name
        s.write = None; s.cut_y = cut_y
    def hit(s, O, D):
        o = (O - s.c) / s.r; d = D / s.r
        a = np.einsum('...i,...i->...', d, d); b = 2 * (d @ o); c = float(o @ o) - 1
        disc = b * b - 4 * a * c; ok = disc > 0
        sq = np.sqrt(np.maximum(disc, 0)); t = (-b - sq) / (2 * a)
        P = O + D * t[..., None]
        if s.cut_y is not None:
            ok &= P[..., 1] >= s.cut_y
        ok &= t > 0.02
        nn = (P - s.c) / (s.r ** 2); nn /= np.linalg.norm(nn, axis=-1, keepdims=True) + 1e-9
        u = np.arctan2(P[..., 2] - s.c[2], P[..., 0] - s.c[0]); v = P[..., 1]
        return t, ok, u, v, nn

class Cyl:
    """Vertical cylinder (axis along y) with a top cap: water heater, pole, speaker, mug."""
    def __init__(s, c, r, y0, y1, mat=0.5, heat=0.3, emit=0.0, name=None, cap=True):
        s.c = np.array(c, np.float32); s.r, s.y0, s.y1 = r, y0, y1; s.mat, s.heat, s.emit, s.name = mat, heat, emit, name
        s.write = None; s.cap = cap
    def hit(s, O, D):
        ox, oz = O[0] - s.c[0], O[2] - s.c[2]; dx, dz = D[..., 0], D[..., 2]
        a = dx * dx + dz * dz; b = 2 * (ox * dx + oz * dz); c = ox * ox + oz * oz - s.r * s.r
        disc = b * b - 4 * a * c; okd = disc > 0
        sq = np.sqrt(np.maximum(disc, 0)); t = (-b - sq) / (2 * np.maximum(a, 1e-9))
        y = O[1] + D[..., 1] * t
        ok = okd & (t > 0.02) & (y >= s.y0) & (y <= s.y1)
        P = O + D * t[..., None]
        nn = np.stack([P[..., 0] - s.c[0], np.zeros_like(t), P[..., 2] - s.c[2]], -1) / s.r
        u = np.arctan2(P[..., 2] - s.c[2], P[..., 0] - s.c[0]) * s.r; v = y - s.y0
        if s.cap:
            with np.errstate(divide='ignore', invalid='ignore'):
                tc = (s.y1 - O[1]) / D[..., 1]
            Pc = O + D * tc[..., None]
            okc = (tc > 0.02) & (((Pc[..., 0] - s.c[0]) ** 2 + (Pc[..., 2] - s.c[2]) ** 2) <= s.r * s.r) & np.isfinite(tc)
            use = okc & (~ok | (tc < t))
            t = np.where(use, tc, t); ok = ok | okc
            nn = np.where(use[..., None], np.array([0, 1, 0], np.float32), nn)
            u = np.where(use, Pc[..., 0] - s.c[0], u); v = np.where(use, Pc[..., 2] - s.c[2], v)
        return t, ok, u, v, nn

def box(x0, y0, z0, x1, y1, z1, mat=0.5, heat=0.3, faces="all", name=None, emit=0.0):
    """Axis-aligned box as rects (outward normals). faces: subset of 'LRBTFK' (left right bottom top front back) or 'all'."""
    out = []
    f = "LRBTFK" if faces == "all" else faces
    dx, dy, dz = x1 - x0, y1 - y0, z1 - z0
    if "F" in f: out.append(Rect((x0, y0, z0), (dx, 0, 0), (0, dy, 0), mat, heat, emit, name))       # faces -z
    if "K" in f: out.append(Rect((x1, y0, z1), (-dx, 0, 0), (0, dy, 0), mat, heat, emit, name))      # faces +z
    if "L" in f: out.append(Rect((x0, y0, z1), (0, 0, -dz), (0, dy, 0), mat, heat, emit, name))      # faces -x
    if "R" in f: out.append(Rect((x1, y0, z0), (0, 0, dz), (0, dy, 0), mat, heat, emit, name))       # faces +x
    if "T" in f: out.append(Rect((x0, y1, z0), (dx, 0, 0), (0, 0, dz), mat, heat, emit, name))       # faces +y
    if "B" in f: out.append(Rect((x0, y0, z1), (dx, 0, 0), (0, 0, -dz), mat, heat, emit, name))      # faces -y
    return out

# ------------------------------------------------------------------ camera + lens
class Cam:
    def __init__(s, pos, look, hfov=100.0, k=0.32, roll=0.0):
        s.pos = np.array(pos, np.float32); look = np.array(look, np.float32)
        f = look - s.pos; f /= np.linalg.norm(f)
        up = np.array([math.sin(roll), math.cos(roll), 0.0], np.float32)
        r = np.cross(up, f); r /= np.linalg.norm(r); u = np.cross(f, r)
        s.R = np.stack([r, u, f], 1).astype(np.float32)          # columns: right, up, forward (world)
        s.hfov, s.k = hfov, k
    def focal(s, W, H):
        # focal so that the distorted image spans hfov horizontally: tan(hfov/2) = ru(edge) ; edge rd = (W/2)/f
        tu = math.tan(math.radians(s.hfov) / 2)
        # solve rd*(1 + k rd^2) = tu for rd, then f = (W/2)/rd
        rd = tu
        for _ in range(30): rd = tu / (1 + s.k * rd * rd)
        return (W / 2) / rd
    def rays(s, W, H):
        f = s.focal(W, H)
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        xd = (xx + 0.5 - W / 2) / f; yd = (yy + 0.5 - H / 2) / f
        r2 = xd * xd + yd * yd; m = 1 + s.k * r2
        dc = np.stack([xd * m, -yd * m, np.ones_like(xd)], -1)
        D = dc @ s.R.T; D /= np.linalg.norm(D, axis=-1, keepdims=True)
        return D.astype(np.float32)
    def project(s, P, W, H):
        """World points (...,3) -> screen px (x, y) and camera depth z (z<=0: behind)."""
        P = np.asarray(P, np.float32); Q = (P - s.pos) @ s.R
        z = Q[..., 2]; zs = np.maximum(z, 1e-3)
        xu = Q[..., 0] / zs; yu = -Q[..., 1] / zs; ru = np.sqrt(xu * xu + yu * yu)
        rd = ru.copy()
        for _ in range(12): rd = ru / (1 + s.k * rd * rd)
        sc = np.where(ru > 1e-9, rd / np.maximum(ru, 1e-9), 1.0)
        f = s.focal(W, H)
        return W / 2 + xu * sc * f, H / 2 + yu * sc * f, z

# ------------------------------------------------------------------ plate building
def build_plate(prims, cam, W, H, ir=1.0, amb=0.05, beam=0.62, lights=None, atlas_order=None, expose=0.30, pct=72,
                d0=1.2, dpow=1.6):
    """Ray-cast the static scene. Returns dict of float16/fixed maps. lights: {name: (pos, power)} for light maps.
    IR illuminator sits at the camera: beam = half-angle (rad) of its soft cone; d0/dpow shape the distance falloff;
    the plate is auto-exposed so its pct-th percentile lands at `expose` (all cameras read alike)."""
    D = cam.rays(W, H); O = cam.pos
    zb = np.full((H, W), np.inf, np.float32); pid = np.full((H, W), -1, np.int32)
    U = np.zeros((H, W), np.float32); V = np.zeros((H, W), np.float32); N = np.zeros((H, W, 3), np.float32)
    for i, p in enumerate(prims):
        t, ok, u, v, n = p.hit(O, D)
        ok &= t < zb
        if not ok.any(): continue
        zb[ok] = t[ok]; pid[ok] = i; U[ok] = u[ok]; V[ok] = v[ok]; N[ok] = n[ok] if n.ndim == 3 else n[ok]
    P = O + D * np.where(np.isfinite(zb), zb, 50.0)[..., None]
    alb = np.zeros((H, W), np.float32); heat = np.zeros((H, W), np.float32); emit = np.zeros((H, W), np.float32)
    mapx = np.full((H, W), -1.0, np.float32); mapy = np.full((H, W), -1.0, np.float32)
    for i, p in enumerate(prims):
        m = pid == i
        if not m.any(): continue
        mat = p.mat
        alb[m] = mat(U[m], V[m], P[m]) if callable(mat) else mat
        heat[m] = p.heat(U[m], V[m], P[m]) if callable(p.heat) else p.heat
        if p.emit: emit[m] = p.emit(U[m], V[m], P[m]) if callable(p.emit) else p.emit
        if p.write is not None and atlas_order is not None:
            ax0, ay0 = p.write
            mapx[m] = ax0 + U[m] * p.ppm; mapy[m] = ay0 + (p.V - V[m]) * p.ppm
    d = np.where(np.isfinite(zb), zb, 50.0)
    # make normals face the camera (two-sided)
    dn = np.einsum('hwc,hwc->hw', N, D); N = np.where((dn > 0)[..., None], -N, N)
    cosi = np.clip(-np.einsum('hwc,hwc->hw', N, D), 0, 1)
    fwd = cam.R[:, 2]; ang = np.arccos(np.clip(D @ fwd, -1, 1))
    spot = np.exp(-(ang / beam) ** 2)
    irr = ir * (0.35 + 0.65 * cosi) * spot / (1 + (d / d0) ** dpow) + amb
    lum = alb * irr
    sc = expose / max(1e-4, float(np.percentile(lum[np.isfinite(zb)], pct)))
    irr *= sc; lum = lum * sc + emit
    out = {"lum": lum.astype(np.float16), "irr": irr.astype(np.float16), "heat": heat.astype(np.float16),
           "alb": alb.astype(np.float16), "depth": d.astype(np.float16)}
    if atlas_order is not None:
        m1, m2 = cv2.convertMaps(mapx, mapy, cv2.CV_16SC2)
        out["amap1"] = m1; out["amap2"] = m2; out["awall"] = (mapx >= 0)
    for name, (lp, power) in (lights or {}).items():
        L = np.array(lp, np.float32) - P; dl = np.linalg.norm(L, axis=-1); L /= dl[..., None] + 1e-6
        c2 = np.clip(np.einsum('hwc,hwc->hw', N, L), 0, 1)
        out["L_" + name] = (alb * c2 * power * sc / np.maximum(dl * dl, 0.25)).astype(np.float16)
    return out

def cached_plate(cache_dir, key, fn):
    os.makedirs(cache_dir, exist_ok=True)
    p = os.path.join(cache_dir, key + ".npz")
    if os.path.exists(p):
        try:
            z = np.load(p); return {k: z[k] for k in z.files}
        except Exception:
            pass
    d = fn(); tmp = p + f".{os.getpid()}.tmp.npz"
    np.savez(tmp, **d); os.replace(tmp, p)
    return d
