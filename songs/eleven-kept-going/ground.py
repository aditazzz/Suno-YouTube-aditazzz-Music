"""Looking DOWN at the night Cape from anywhere between orbit and a few hundred metres: a curved Earth (ray-sphere),
the real coastline (GSHHS) with procedural city/road lights near the Cape and the global night-lights texture beyond,
moonlit sea with an anti-aliased glitter path, a moonlit cloud deck (domain-warped fields, lit from below by the towns),
haze with distance, the floodlit circle of Landing Zone 1 at full detail, and the black sky / airglow above the horizon.

Local frame: origin on the ground at Landing Zone 1, x = east, y = up, z = south (metres).
"""
import os, math, json
from functools import lru_cache
import numpy as np, cv2
import ekg as K
from ekg import F32, sstep, clamp, lerp
import sys
sys.path.insert(0, K.ROOT)
from studio import space as sp

HERE = os.path.dirname(os.path.abspath(__file__))
RE = 6371000.0
LZ_LON, LZ_LAT = -80.5442, 28.4858
PAD40_LON, PAD40_LAT = -80.5772, 28.5618

def _v(lon, lat):
    lo, la = math.radians(lon), math.radians(lat)
    return np.array([math.cos(la) * math.sin(lo), math.sin(la), math.cos(la) * math.cos(lo)], np.float64)
U0 = _v(LZ_LON, LZ_LAT)
E0 = np.array([math.cos(math.radians(LZ_LON)), 0.0, -math.sin(math.radians(LZ_LON))])
N0 = np.cross(U0, E0)
S0 = -N0

def to_local(lon, lat, h=0.0):
    """geodetic -> local metres (x east, y up, z south), on a sphere."""
    v = _v(lon, lat) * (RE + h); c = U0 * RE
    d = v - c
    return np.array([d @ E0, d @ U0, d @ S0], F32)

def moon_local():
    from orbit import MOON
    m = np.asarray(MOON, np.float64)
    return K.nrm(np.array([m @ E0, m @ U0, m @ S0], F32))

class Mip:
    """a texture with area-averaged mip levels, sampled with a per-pixel level of detail (trilinear). Stored in its
    own dtype (uint8 / uint16 keep big maps small); `scale` converts samples to linear floats."""
    def __init__(self, img, nlev=7, wrap=False, scale=1.0):
        self.lv = [img]; self.wrap = wrap; self.scale = scale
        for i in range(nlev):
            p = self.lv[-1]
            if min(p.shape[:2]) < 16: break
            self.lv.append(cv2.resize(p, (max(1, p.shape[1] // 2), max(1, p.shape[0] // 2)), interpolation=cv2.INTER_AREA))
    def sample(self, x, y, lod, border=0.0):
        """x, y: level-0 texel coordinates (flat arrays); lod: log2(texels per pixel) (flat array)."""
        lod = np.clip(lod, 0, len(self.lv) - 1.001)
        l0 = np.floor(lod).astype(np.int32); fr = (lod - l0).astype(F32)
        out = np.zeros(x.shape + self.lv[0].shape[2:], F32)
        mode = cv2.BORDER_WRAP if self.wrap else cv2.BORDER_CONSTANT
        for L in range(len(self.lv)):
            w = np.where(l0 == L, 1 - fr, 0) + np.where(l0 + 1 == L, fr, 0)
            j = np.nonzero(w > 0)[0]
            if len(j) == 0: continue
            sc = 2.0 ** -L
            v = _remap(self.lv[L], (x[j] + 0.5) * sc - 0.5, (y[j] + 0.5) * sc - 0.5, mode, border).astype(F32)
            ww = w[j] if v.ndim == 1 else w[j][:, None]
            out[j] += v * ww
        return out * self.scale

U16 = 1500.0                                                     # uint16 light maps: value = linear * U16

@lru_cache(1)
def assets():
    """inner level: the Cape at 20 m/texel; outer level: Florida at ~147 m/texel; beyond: the global textures.
    Kept compact (uint8 masks, uint16 lights): each render worker holds these in memory."""
    meta = json.load(open(os.path.join(HERE, "assets", "cape_meta.json")))
    land = cv2.GaussianBlur(cv2.imread(os.path.join(HERE, "assets", "cape_land.png"), 0), (0, 0), 1.2)
    lights = cv2.imread(os.path.join(HERE, "assets", "cape_lights.png"), 0)
    lf = (lights.astype(F32) / 255) ** 2 * 4.0                   # linear light per 20 m texel
    del lights
    # LZ-1's own work lights are drawn at full detail by the LZ layer: take them out of the map
    lx = (LZ_LON - meta["lon0"]) / (meta["lon1"] - meta["lon0"]) * meta["W"]; ly = (meta["lat1"] - LZ_LAT) / (meta["lat1"] - meta["lat0"]) * meta["H"]
    r0 = int(max(0, ly - 40)), int(max(0, lx - 40))
    yy, xx = np.ogrid[r0[0]:int(ly + 40), r0[1]:int(lx + 40)]
    rr = np.sqrt(((xx - lx) * 20.0) ** 2 + ((yy - ly) * 20.0) ** 2)
    lf[r0[0]:int(ly + 40), r0[1]:int(lx + 40)] *= np.clip((rr - 380.0) / 200.0, 0, 1).astype(F32)
    # point lights: one per local maximum, carrying the energy of its 3x3 neighbourhood (no grid of dots)
    mx3 = cv2.dilate(lf, np.ones((3, 3), np.uint8))
    peak = (lf >= mx3 - 1e-7) & (lf > 0.003)
    del mx3
    lp = cv2.boxFilter(lf, -1, (3, 3), normalize=False)
    del lf
    lp = np.where(peak, np.clip(lp * 3.0 * U16, 0, 65535), 0).astype(np.uint16)
    del peak
    fmeta = json.load(open(os.path.join(HERE, "assets", "fl_meta.json")))
    fland = cv2.GaussianBlur(cv2.imread(os.path.join(HERE, "assets", "fl_land.png"), 0), (0, 0), 0.8)
    fl = cv2.imread(os.path.join(HERE, "assets", "fl_lights.png"), 0).astype(F32)
    fl = np.clip((fl / 255) ** 2 * 4.0 * 0.28 * U16, 0, 65535).astype(np.uint16)
    return dict(meta=meta, land=Mip(land, scale=1 / 255.0), lights=Mip(lp, scale=1 / U16), lights_p=lp,
                fmeta=fmeta, fland=Mip(fland, scale=1 / 255.0), flights=Mip(fl, scale=1 / U16))

@lru_cache(1)
def cloud_tex():
    """2048^2 tileable cloud density: fbm, domain-warped so the cells shear into streets and rafts (no cotton balls)."""
    n = 2048
    def fbm(seed, base, oct_, persist):
        r = K.rng(seed); acc = np.zeros((n, n), F32); amp = 1.0; tot = 0.0
        for o in range(oct_):
            k = base * 2 ** o
            g = r.random((k, k)).astype(F32)
            up = cv2.resize(np.tile(g, (3, 3)), (n * 3, n * 3), interpolation=cv2.INTER_CUBIC)[n:2 * n, n:2 * n]
            acc += up * amp; tot += amp; amp *= persist
        acc /= tot; return (acc - acc.min()) / max(1e-6, acc.max() - acc.min())
    wx = fbm(71, 3, 5, 0.55) - 0.5; wy = fbm(72, 3, 5, 0.55) - 0.5
    base = fbm(73, 4, 8, 0.58)
    yy, xx = np.mgrid[0:n, 0:n].astype(F32)
    mx = (xx + wx * n * 0.22) % n; my = (yy + wy * n * 0.12) % n
    d = cv2.remap(base, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
    det = fbm(74, 32, 4, 0.6)
    d = d * 0.82 + det * 0.18
    return d.astype(F32)

@lru_cache(1)
def _cloud_mip(): return Mip(cloud_tex(), 8, wrap=True)

@lru_cache(1)
def _cloud_sorted(): return np.sort(cloud_tex()[::4, ::4].ravel())

def _cloud_q(q):
    v = _cloud_sorted(); return float(v[int(np.clip(q, 0, 1) * (len(v) - 1))])

@lru_cache(1)
def _blur_cloud():
    c = cloud_tex(); k = 32
    return cv2.GaussianBlur(np.pad(c, k, mode="wrap"), (0, 0), 4.0)[k:-k, k:-k].copy()

@lru_cache(1)
def global_tex():
    t = sp.textures(0)
    return t["lights"], t["water"]

def _remap(tex, a, b, mode=cv2.BORDER_CONSTANT, border=0, interp=cv2.INTER_LINEAR):
    """sample tex at flat coordinate arrays (any length): remap needs < 32767 rows, so fold into 4096-wide blocks."""
    n = a.shape[0]; k = 4096; m = -(-n // k) * k
    A = np.full(m, -10, F32); B = np.full(m, -10, F32); A[:n] = a; B[:n] = b
    r = cv2.remap(tex, A.reshape(-1, k), B.reshape(-1, k), interp, borderMode=mode, borderValue=border)
    return r.reshape(m, -1)[:n] if r.ndim == 3 else r.reshape(-1)[:n]

def remap_flat(tex, xs, ys, mode=cv2.BORDER_CONSTANT): return _remap(tex, xs, ys, mode)

def _hash2(i, j, s):
    v = np.sin(i * 127.1 + j * 311.7 + s * 74.7) * 43758.5453
    return v - np.floor(v)

def sharp_lights(lf, mx, my, mpp_tex, foot):
    """turn the 20 m light texels into point lights when the pixels are small: each texel's light sits near its centre
    (hashed jitter) and is drawn as a gaussian of ~one pixel, conserving its energy. foot = metres per screen pixel."""
    H_, W_ = lf.shape
    out = np.zeros_like(mx)
    sig = np.maximum(foot * 0.75, 1.6) / mpp_tex                     # in texels
    norm_ = 1.0 / (2 * math.pi * sig * sig)
    cx0 = np.floor(mx - 0.5); cy0 = np.floor(my - 0.5)
    for dx in (0, 1):
        for dy in (0, 1):
            ci = cx0 + dx; cj = cy0 + dy
            ok = (ci >= 0) & (ci < W_) & (cj >= 0) & (cj < H_)
            ii = np.clip(ci, 0, W_ - 1).astype(np.int32); jj = np.clip(cj, 0, H_ - 1).astype(np.int32)
            v = lf[jj, ii].astype(F32) * (1.0 / U16) * ok
            lx = ci + 0.5 + (_hash2(ci, cj, 1.0) - 0.5) * 0.5; ly = cj + 0.5 + (_hash2(ci, cj, 2.0) - 0.5) * 0.5
            d2 = (mx - lx) ** 2 + (my - ly) ** 2
            out += v * np.exp(-d2 / (2 * sig * sig)) * norm_
    return out

def view(cam, W, H, t, p=None):
    """HDR frame of the Earth/sky seen by `cam` (ekg.Cam in local metres).
    p: moon, lights, clouds (0..1), cloud_alt, cloud_scale, cloud_drift, haze, stars, horizon_glow, ocean, lz (flood gain of LZ-1),
    scorch, lz_lamps."""
    p = p or {}
    eye = cam.eye.astype(np.float64)
    ys_, xs_ = np.mgrid[0:H, 0:W].astype(F32)
    D = (cam.f[None, None] * cam.fpx + cam.r[None, None] * (xs_ - W / 2 - cam.sx)[..., None] + cam.u[None, None] * (H / 2 + cam.sy - ys_)[..., None])
    D = D / np.linalg.norm(D, axis=2, keepdims=True)
    D = D.reshape(-1, 3).astype(np.float64)
    C = np.array([0.0, -RE, 0.0])
    oc = eye - C
    b = D @ oc; cq = float(oc @ oc) - RE * RE
    disc = b * b - cq
    hit = (disc > 0) & ((-b - np.sqrt(np.maximum(disc, 0))) > 0)
    s = np.where(hit, -b - np.sqrt(np.maximum(disc, 0)), np.inf)
    out = np.zeros((H * W, 3), F32)
    alt = float(np.linalg.norm(oc) - RE)
    Mn = moon_local(); mg = p.get("moon", 1.0)
    # ---------------- sky (no ground hit)
    sky = ~hit
    if sky.any():
        Ds = D[sky]
        dmin = np.sqrt(np.maximum(float(oc @ oc) - (Ds @ oc) ** 2, 0)) - RE         # closest approach altitude of the ray
        dmin = np.where((Ds @ oc) < 0, dmin, alt + 1e5 * (Ds @ oc))
        glow = np.exp(-np.maximum(dmin, 0) / (9000 + alt * 0.02))
        col = np.array([0.006, 0.009, 0.020], F32)[None] * glow[:, None] * p.get("horizon_glow", 1.0)
        if alt < 20000:                                                                   # town glow low on the horizon
            col += np.array([0.010, 0.007, 0.005], F32)[None] * np.exp(-np.maximum(dmin, 0) / 2500)[:, None] * p.get("horizon_glow", 1.0)
        ag = np.exp(-((dmin - 95000) / 9000) ** 2) * (alt > 60000)                       # airglow band (from high up)
        col += np.array([0.010, 0.020, 0.008], F32)[None] * ag[:, None] * 0.35
        out[sky] = col
    light_full = np.zeros(H * W, F32)
    # ---------------- ground / sea
    if hit.any():
        idx = np.nonzero(hit)[0]
        P = eye[None] + D[idx] * s[idx][:, None]
        V = P - C; V /= np.linalg.norm(V, axis=1, keepdims=True)
        Q = np.outer(V[:, 0], E0) + np.outer(V[:, 1], U0) + np.outer(V[:, 2], S0)
        lon = np.degrees(np.arctan2(Q[:, 0], Q[:, 2])); lat = np.degrees(np.arcsin(np.clip(Q[:, 1], -1, 1)))
        A = assets(); meta = A["meta"]; fmeta = A["fmeta"]
        dist = s[idx]
        cosv = np.abs((D[idx] * V).sum(1))
        foot = (dist / cam.fpx / np.maximum(cosv, 0.08)).astype(F32)          # metres per pixel on the ground
        foot_iso = (dist / cam.fpx).astype(F32)
        # inner level (the Cape, 20 m)
        mx = ((lon - meta["lon0"]) / (meta["lon1"] - meta["lon0"]) * meta["W"]).astype(F32)
        my = ((meta["lat1"] - lat) / (meta["lat1"] - meta["lat0"]) * meta["H"]).astype(F32)
        inside = (mx >= 0) & (mx < meta["W"] - 1) & (my >= 0) & (my < meta["H"] - 1)
        land_v = np.zeros(len(idx), F32); light_v = np.zeros(len(idx), F32); land_s = np.zeros(len(idx), F32)
        f_in = np.clip(np.minimum.reduce([mx / 300, (meta["W"] - mx) / 300, my / 300, (meta["H"] - my) / 300]), 0, 1).astype(F32)
        j = np.nonzero(f_in > 0)[0]
        if len(j):
            lod = np.log2(np.maximum(1.0, foot_iso[j] / 20.0)).astype(F32)
            land_v[j] = A["land"].sample(mx[j], my[j], np.log2(np.maximum(1.0, foot[j] / 20.0)))
            land_s[j] = A["land"].sample(mx[j], my[j], np.maximum(2.2, np.log2(np.maximum(1.0, foot[j] / 20.0))).astype(F32))
            lv_ = A["lights"].sample(mx[j], my[j], lod)
            kb = np.clip((14.0 - foot_iso[j]) / 8.0, 0, 1)
            if (kb > 0).any():
                jj = np.nonzero(kb > 0)[0]
                lv_[jj] = lv_[jj] * (1 - kb[jj]) + sharp_lights(A["lights_p"], mx[j][jj], my[j][jj], 20.0, foot_iso[j][jj]) * kb[jj]
            light_v[j] = lv_
        # outer level (Florida, ~147 m)
        fx = ((lon - fmeta["lon0"]) / (fmeta["lon1"] - fmeta["lon0"]) * fmeta["W"]).astype(F32)
        fy = ((fmeta["lat1"] - lat) / (fmeta["lat1"] - fmeta["lat0"]) * fmeta["H"]).astype(F32)
        f_out = np.clip(np.minimum.reduce([fx / 200, (fmeta["W"] - fx) / 200, fy / 200, (fmeta["H"] - fy) / 200]), 0, 1).astype(F32)
        mpp_f = 147.0
        j = np.nonzero((f_out > 0) & (f_in < 1))[0]
        if len(j):
            lod = np.log2(np.maximum(1.0, foot_iso[j] / mpp_f)).astype(F32)
            fl = A["fland"].sample(fx[j], fy[j], np.log2(np.maximum(1.0, foot[j] / mpp_f)))
            fli = A["flights"].sample(fx[j], fy[j], lod)
            w = 1 - f_in[j]
            land_v[j] = land_v[j] * (1 - w) + fl * w
            land_s[j] = land_s[j] * (1 - w) + fl * w
            light_v[j] = light_v[j] * (1 - w) + fli * w
        # beyond: the global textures
        f_any = np.maximum(f_in, f_out)
        j = np.nonzero(f_any < 1)[0]
        if len(j):
            gl, gw = global_tex()
            u = ((lon[j] / 360.0 + 0.5) % 1.0); v = 0.5 - lat[j] / 180.0
            gx = (u * gl.shape[1]).astype(F32); gy = (v * gl.shape[0]).astype(F32)
            gl_v = _remap(gl, gx, gy, cv2.BORDER_WRAP); gw_v = _remap(gw, gx, gy, cv2.BORDER_WRAP)
            w = 1 - f_any[j]
            land_v[j] = land_v[j] * (1 - w) + (1 - gw_v) * w
            land_s[j] = land_s[j] * (1 - w) + (1 - gw_v) * w
            light_v[j] = light_v[j] * (1 - w) + (gl_v ** 1.6) * 0.9 * w
        # moonlit land and sea
        mu = np.clip(V @ Mn, 0, 1)
        tex = K.noise_tex(512, 44, 6, 0.6); tex2 = K.noise_tex(512, 45, 5, 0.65)
        tv = tex[(np.abs(P[:, 2] * 0.004).astype(np.int64)) % 512, (np.abs(P[:, 0] * 0.004).astype(np.int64)) % 512]
        tv2 = tex2[(np.abs(P[:, 2] * 0.03).astype(np.int64)) % 512, (np.abs(P[:, 0] * 0.03).astype(np.int64)) % 512]
        k2 = np.clip((150.0 - foot) / 100.0, 0, 1)[:, None]                  # fine variation only where pixels resolve it
        land_alb = np.array([0.050, 0.054, 0.050], F32)[None] * (0.45 + 0.6 * tv[:, None] + 0.45 * (tv2[:, None] - 0.5) * k2)
        sea_alb = np.array([0.018, 0.022, 0.030], F32)[None]
        lv = land_v[:, None]
        Em = (K.MOON_E * mu * mg + 0.003)[:, None] * K.MOON[None]
        base = (land_alb * lv + sea_alb * (1 - lv)) * Em
        # moon glitter: a smooth slope-distribution lobe (no aliasing from far away), sparkle only when pixels are small
        Vv = -D[idx]
        Hh = Mn[None] + Vv; Hh /= np.linalg.norm(Hh, axis=1, keepdims=True)
        ch = np.clip((V * Hh).sum(1), 1e-3, 1)
        tan2 = (1 - ch * ch) / (ch * ch)
        rough = 0.13
        lobe = np.exp(-tan2 / (rough * rough)) / (ch ** 4)
        ks = np.clip((3.0 - foot) / 2.5, 0, 1)
        if ks.any():
            wt = K.noise_tex(256, 61, 4, 0.5)
            wx = ((P[:, 0] * 0.5 + t * 0.6) % 256).astype(np.int32); wz = ((P[:, 2] * 0.5) % 256).astype(np.int32)
            spark = (wt[wz, wx] - 0.45) * 3.0
            lobe = lobe * (1 + ks * np.clip(spark, -0.9, 2.5))
        sea = (1 - land_v) * p.get("ocean", 1.0)
        col = base + (lobe * sea * mg * 0.006)[:, None] * np.array([0.75, 0.82, 1.0], F32)[None]
        # the beach: a strip of pale sand along the shore and a faint, broken line of surf just off it (only where pixels
        # resolve them), so a coastline reads as a coast and not as a seam
        kc = np.clip((60.0 - foot) / 40.0, 0, 1)
        if kc.any():
            sand = np.exp(-((land_s - 0.60) / 0.16) ** 2) * kc
            brk = tex2[(np.abs(P[:, 2] * 0.012 + t * 0.05).astype(np.int64)) % 512, (np.abs(P[:, 0] * 0.002).astype(np.int64) + 77) % 512]
            surf = np.exp(-((land_s - 0.20) / 0.07) ** 2) * kc * np.clip((brk - 0.35) * 2.2, 0, 1)
            col += (sand * 0.16)[:, None] * Em
            col += (surf * mg * (K.MOON_E * mu + 0.004) * 0.30)[:, None] * np.array([0.80, 0.86, 1.0], F32)[None]
        lights_col = np.array([1.0, 0.80, 0.55], F32) * 0.6 + np.array([0.85, 0.9, 1.0], F32) * 0.4
        col += light_v[:, None] * lights_col[None] * 1.4 * p.get("lights", 1.0)
        # Landing Zone 1 at full detail (concrete, ring, floodlight pools)
        lzg = p.get("lz", 1.0)
        if lzg > 0:
            import lz as Z
            near = (np.abs(P[:, 0]) < Z.TEX_M / 2 - 2) & (np.abs(P[:, 2]) < Z.TEX_M / 2 - 2)
            if near.any():
                jn = np.nonzero(near)[0]
                px = P[jn, 0].astype(F32); pz = P[jn, 2].astype(F32)
                alb = Z.pad_tex(int(p.get("scorch", 0)))
                mpx = Z.TEX_M / Z.TEX_N
                a = _remap(alb, (px + Z.TEX_M / 2) / mpx, (pz + Z.TEX_M / 2) / mpx, cv2.BORDER_REPLICATE)
                E = np.zeros((len(jn), 3), F32) + K.MOON[None] * (Z.MOON_E * mu[jn] * mg + 0.003)[:, None]
                for f in Z.FLOODS:
                    fx, fy, fz = f
                    d2 = (fx - px) ** 2 + (fz - pz) ** 2 + fy * fy
                    E += (K.FLOOD * Z.FLOOD_I * lzg)[None] * (fy / np.sqrt(d2) / d2 * Z.spot(f, px, 0.0, pz))[:, None]
                rr = np.maximum(np.abs(px), np.abs(pz))
                fadeL = np.clip((Z.TEX_M / 2 - 10 - rr) / 60, 0, 1)[:, None]
                col[jn] = col[jn] * (1 - fadeL) + (a * E) * fadeL
                light_v[jn] *= (1 - fadeL[:, 0])
        # haze / aerial perspective
        hz = 1 - np.exp(-dist / (60000 + alt * 0.8) * p.get("haze", 1.0))
        col = col * (1 - hz[:, None] * 0.85) + np.array([0.004, 0.006, 0.012], F32)[None] * hz[:, None] * p.get("horizon_glow", 1.0)
        out[idx] = col
        light_full[idx] = light_v
    img = out.reshape(H, W, 3)
    # ---------------- cloud deck (moonlit tops, lit from below over the towns)
    if p.get("clouds", 0) > 0:
        ca = p.get("cloud_alt", 2500.0)
        b2 = D @ oc; c2 = float(oc @ oc) - (RE + ca) ** 2; disc2 = b2 * b2 - c2
        if alt > ca:
            s2 = -b2 - np.sqrt(np.maximum(disc2, 0)); okc = (disc2 > 0) & (s2 > 0)
        else:
            s2 = -b2 + np.sqrt(np.maximum(disc2, 0)); okc = (disc2 > 0) & (s2 > 0)
        if okc.any():
            idc = np.nonzero(okc)[0]
            Pc = eye[None] + D[idc] * s2[idc][:, None]
            ct = cloud_tex(); n = ct.shape[0]; cm = _cloud_mip()
            sc = p.get("cloud_scale", 1.0 / 30.0)                          # texels per metre (2048 texels = 61 km)
            dr = t * p.get("cloud_drift", 0.0)
            u_ = ((Pc[:, 0] * sc + dr) % n).astype(F32); v_ = ((Pc[:, 2] * sc) % n).astype(F32)
            foot_c = (s2[idc] / cam.fpx * sc).astype(F32)                   # texels per pixel
            lod = np.log2(np.maximum(1.0, foot_c)).astype(F32)
            dens = cm.sample(u_, v_, lod)
            cov = p["clouds"]
            th = _cloud_q(1 - cov)
            soft = 0.10 + 0.03 * lod
            a = np.clip((dens - th) / soft, 0, 1) ** 1.2 * 0.88
            mxy = np.array([Mn[0], Mn[2]], F32); mxy = mxy / max(1e-6, float(np.linalg.norm(mxy))) * 6
            dens2 = cm.sample(((u_ + mxy[0]) % n).astype(F32), ((v_ + mxy[1]) % n).astype(F32), lod)
            relief = np.clip(0.75 + (dens2 - dens) * 4.0, 0.35, 1.3)
            a = a * np.exp(-s2[idc] / 180000)
            mu_c = max(0.05, float(Mn[1]))
            ccol = K.MOON[None] * (0.42 * K.MOON_E * mu_c * mg) * relief[:, None]
            lb = cv2.GaussianBlur(light_full.reshape(H, W), (0, 0), max(2.0, min(W, H) * 0.01)).reshape(-1)
            ccol = ccol + lb[idc][:, None] * np.array([1.0, 0.7, 0.45], F32)[None] * 0.25
            flat = img.reshape(-1, 3)
            flat[idc] = flat[idc] * (1 - a[:, None] * 0.92) + ccol * a[:, None]
            img = flat.reshape(H, W, 3)
    if p.get("stars", 0) > 0:
        st = np.zeros_like(img); K.stars(st, t, gain=p["stars"], n=3600, density=1.0, twinkle=0.1)
        img += st * sky.reshape(H, W)[..., None]
    # the four flood towers of LZ-1 as lamps
    if p.get("lz", 1.0) > 0 and p.get("lz_lamps", True):
        import lz as Z
        for (fx, fy, fz) in Z.FLOODS:
            x, y, z = cam.p1((fx, fy, fz))
            if z > 1 and -10 < x < W + 10 and -10 < y < H + 10:
                r = max(0.8, 0.9 * cam.px_per_m(z))
                g = min(8.0, 1.5e7 / (z * z)) * p.get("lz", 1.0)
                K.splat(img, x, y, r, K.FLOOD, g / max(1.0, r * r * 0.25))
    return img, hit.reshape(H, W)

def lz_screen(cam):
    """where Landing Zone 1 is on screen."""
    return cam.p1((0.0, 0.0, 0.0))
