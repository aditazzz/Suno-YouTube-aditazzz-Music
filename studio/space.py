"""Photoreal space for music videos: a real-texture Earth (NASA Blue/Black Marble), a physically-motivated atmosphere
(Rayleigh + Mie single scattering, approximated analytically so it renders in well under a second), a star field
with a faint Milky Way, the Sun with diffraction spikes, an optical "eye" made of light, and an HDR camera chain
(bloom, ACES tonemap, grain, vignette).

Everything is in linear HDR until `develop()`. World units: Earth radius = 1, +Y = up, Earth spins about +Y.
"""
import os
from functools import lru_cache
import numpy as np, cv2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPACE = os.path.join(ROOT, "assets", "space")
F32 = np.float32

def nrm(v): v = np.asarray(v, F32); return v / np.linalg.norm(v)
def mat3(X, M):
    """X (..., 3) @ M (3, 3) — via cv2.transform, ~40x faster than numpy matmul for millions of 3-vectors."""
    sh = X.shape; return cv2.transform(np.ascontiguousarray(X, F32).reshape(-1, 1, 3), np.ascontiguousarray(np.asarray(M, F32).T)).reshape(sh)
def sstep(a, b, x): t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)

# ---------------------------------------------------------------- textures
@lru_cache(None)
def textures(level=0):
    """level 0 = 4096 wide, 1 = 2048 (for a small Earth: less shimmer)."""
    rd = lambda n, flag=cv2.IMREAD_COLOR: cv2.imread(os.path.join(SPACE, n), flag)
    day = cv2.cvtColor(rd("earth_day.jpg"), cv2.COLOR_BGR2RGB).astype(F32) / 255
    day = np.power(day, 2.2)                                                    # sRGB -> linear reflectance
    lights = rd("earth_lights.jpg", cv2.IMREAD_GRAYSCALE).astype(F32) / 255
    lights = cv2.resize(lights, (day.shape[1], day.shape[0]), interpolation=cv2.INTER_CUBIC)
    lights = np.power(np.clip(lights, 0, 1), 1.6)
    rng = np.random.default_rng(11)                                                 # fine city sparkle so close-ups aren't blobs
    spark = cv2.GaussianBlur(rng.random(lights.shape).astype(F32), (0, 0), 0.7)
    spark = np.clip((spark - spark.mean()) * 9 + 1, 0, 3)
    lights = lights * (0.35 + 0.65 * spark)
    clouds = rd("earth_clouds.png", cv2.IMREAD_GRAYSCALE).astype(F32) / 255
    water = rd("earth_water.png", cv2.IMREAD_GRAYSCALE).astype(F32) / 255
    tex = dict(day=day, lights=lights, clouds=clouds, water=water)
    for _ in range(level): tex = {k: cv2.pyrDown(v) for k, v in tex.items()}
    return tex

def sample(t, u, v):
    """Bilinear lookup with horizontal wrap. u, v in [0,1) texture space (any 2-D shape)."""
    h, w = t.shape[:2]
    mx = (u * w - 0.5).astype(F32); my = np.clip(v * h - 0.5, 0, h - 1).astype(F32)
    return cv2.remap(t, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)

# ---------------------------------------------------------------- camera
class Cam:
    """fov is the vertical field of view of a 1920x1080 frame; other sizes keep the same pixel scale on their short side,
    so a 9:16 frame shows the same subject at the same size with more room above and below."""
    def __init__(self, eye, target=(0, 0, 0), up=(0, 1, 0), fov=40.0, W=1920, H=1080, roll=0.0, shift=(0.0, 0.0)):
        """shift = lens shift in pixels (x right, y down): moves the picture without perspective change."""
        self.sx, self.sy = float(shift[0]), float(shift[1])
        self.eye = np.asarray(eye, F32); f = nrm(np.asarray(target, F32) - self.eye)
        r = nrm(np.cross(f, np.asarray(up, F32))); u = np.cross(r, f)
        if roll: c, s = np.cos(roll), np.sin(roll); r, u = c * r + s * u, -s * r + c * u
        self.f, self.r, self.u, self.W, self.H = f, r.astype(F32), u.astype(F32), W, H
        self.fpx = (min(W, H) / 2) / np.tan(np.radians(fov) / 2)
    def rays(self, step=1):
        Dc = _cam_dirs(self.W, self.H, float(self.fpx), self.sx, self.sy, step)       # unit directions in camera space (cached)
        return mat3(Dc, np.stack([self.r, self.u, self.f]))
    def project(self, d):
        """directions (n,3) -> pixel x, y, in-front mask"""
        z = d @ self.f; ok = z > 1e-4; zz = np.where(ok, z, 1)
        return self.W / 2 + self.sx + (d @ self.r) / zz * self.fpx, self.H / 2 + self.sy - (d @ self.u) / zz * self.fpx, ok
    def project_point(self, p):
        x, y, ok = self.project((np.asarray(p, F32) - self.eye)[None]); return float(x[0]), float(y[0]), bool(ok[0])

@lru_cache(16)
def _cam_dirs(W, H, fpx, sx, sy, step=1):
    x, y = _grid(W, H); x = (x - sx)[::step, ::step]; y = (y + sy)[::step, ::step]
    D = np.stack([x, y, np.full_like(x, fpx)], 2)
    return (D / np.sqrt(np.sum(D * D, 2, keepdims=True))).astype(F32)

@lru_cache(8)
def _grid(W, H):
    x = np.arange(W, dtype=F32) + 0.5 - W / 2; y = H / 2 - (np.arange(H, dtype=F32) + 0.5)
    return np.meshgrid(x, y)

def spin(lon_deg, tilt_deg=23.4):
    """world -> Earth-fixed rotation (Earth turned by lon_deg, axis tilted toward the camera's left)."""
    a, t = np.radians(lon_deg), np.radians(tilt_deg)
    Ry = np.array([[np.cos(a), 0, -np.sin(a)], [0, 1, 0], [np.sin(a), 0, np.cos(a)]], F32)
    Rz = np.array([[np.cos(t), -np.sin(t), 0], [np.sin(t), np.cos(t), 0], [0, 0, 1]], F32)
    return (Rz @ Ry).astype(F32)

# ---------------------------------------------------------------- atmosphere constants
BETA_R = np.array([0.175, 0.41, 1.0], F32)      # Rayleigh scattering ~ 1/lambda^4 (680, 550, 440 nm), normalised
BETA_M = np.array([1.0, 1.0, 1.0], F32) * 0.22  # Mie (haze/aerosol), grey
H_ATM = 0.0085                                   # visual scale height in Earth radii (exaggerated ~7x for screen)

def hg(cos, g):
    return (1 - g * g) / (4 * np.pi * np.power(1 + g * g - 2 * g * cos, 1.5))

def sun_transmittance(cos_sun, density=1.0):
    """colour of sunlight after the path through the atmosphere toward the sun (reddens at grazing angles)."""
    airm = 1.0 / (np.clip(cos_sun + 0.16, 0.018, 1.2))
    return np.exp(-(BETA_R * 0.32 + BETA_M * 0.12)[None] * (airm * density)[..., None])

# ---------------------------------------------------------------- Earth
def earth(cam, D, sun, rot, p=None):
    """HDR radiance of the Earth + its atmosphere on the frame (H,W,3), plus the planet coverage mask (H,W).
    p: dict of extras: clouds_lon (deg drift), lights (night-light gain), atmo (gain), day (albedo gain), exposure,
       uv_hook(u, v, hitmask) -> (u, v) for glitches, layer gains: surface, sea, sky (0..1 to 'unmount')."""
    p = p or {}; E = p.get("exposure", 1.0); S = nrm(sun)
    H, W = D.shape[:2]; eye = cam.eye
    b = D @ eye; c = float(eye @ eye) - 1.0
    disc = b * b - c; hit = (disc > 0) & (b < 0)
    out = np.zeros((H, W, 3), F32)
    # ------------------------------------------------ atmosphere outside the disk (limb glow)
    d2 = np.maximum(float(eye @ eye) - b * b, 0); dmin = np.sqrt(d2)
    alt = dmin - 1.0
    limb = (~hit) & (b < 0) & (alt < H_ATM * 9)
    sky_gain = p.get("sky", 1.0)
    if limb.any() and sky_gain > 0:
        ys, xs = np.nonzero(limb)
        Dl = D[ys, xs]; tc = -b[ys, xs]; Pt = eye[None] + Dl * tc[:, None]; Nt = Pt / np.linalg.norm(Pt, axis=1, keepdims=True)
        a = np.maximum(alt[ys, xs], 0)
        rho = np.exp(-a / H_ATM)
        mu_s = Nt @ S
        lit = sstep(-0.11, 0.03, mu_s + a * 2.0)                                    # high air stays lit a bit past the terminator
        Ts = sun_transmittance(mu_s, density=0.22 + 7 * rho)                         # low, grazing air -> red/orange; high air stays blue-white
        tau = (BETA_R * 4.2 + BETA_M * 1.6)[None] * rho[:, None]
        cos = Dl @ S
        ph_r = 0.0597 * (1 + cos * cos); ph_m = hg(cos, 0.78)
        scat = (BETA_R[None] * ph_r[:, None] * 1.5 + BETA_M[None] * ph_m[:, None] * 0.55) / (BETA_R + BETA_M)[None]
        L = (1 - np.exp(-tau)) * Ts * scat * lit[:, None] * 22.0
        out[ys, xs] = L * sky_gain * p.get("atmo", 1.0)
    # ------------------------------------------------ the disk
    if hit.any():
        ys, xs = np.nonzero(hit)
        Dh = D[ys, xs]; bb = b[ys, xs]; t = -bb - np.sqrt(disc[ys, xs])
        N = eye[None] + Dh * t[:, None]
        Q = mat3(N, rot.T)                                                           # Earth-fixed
        lon = np.arctan2(Q[:, 0], Q[:, 2]); lat = np.arcsin(np.clip(Q[:, 1], -1, 1))
        u = (lon / (2 * np.pi) + 0.5) % 1.0; v = 0.5 - lat / np.pi
        if p.get("uv_hook"): u, v = p["uv_hook"](u, v, (ys, xs))
        diam = 2 * cam.fpx / max(1e-3, np.sqrt(max(c, 1e-6)))                        # rough on-screen diameter in px
        tex = textures(1 if diam < 1500 else 0)
        n = len(u); k = 2048; m = -(-n // k) * k
        U = np.zeros(m, F32); V = np.zeros(m, F32); U[:n] = u; V[:n] = v; U = U.reshape(-1, k); V = V.reshape(-1, k)
        smp = lambda name, du=0.0, dv=0.0: sample(tex[name], (U + du) % 1.0, V + dv).reshape(m, -1)[:n] if tex[name].ndim == 3 else sample(tex[name], (U + du) % 1.0, V + dv).reshape(m)[:n]
        alb = smp("day") * p.get("day", 1.0)
        water = smp("water")
        cdrift = p.get("clouds_lon", 0.0) / 360.0
        cl = np.clip(smp("clouds", cdrift) * 1.15 - 0.05, 0, 1) * p.get("clouds", 1.0)
        mu_s = N @ S; V_ = -Dh; mu_v = np.clip(np.sum(N * V_, 1), 1e-3, 1)
        Ts = sun_transmittance(mu_s)
        irr = np.clip(mu_s, 0, 1)[:, None] * Ts
        twil = sstep(-0.16, 0.06, mu_s)[:, None]
        # cloud shadows: sample the cloud layer a little toward the sun (in Earth-fixed tangent space)
        Se = S @ rot.T; east = np.stack([Q[:, 2], np.zeros(n, F32), -Q[:, 0]], 1); east /= np.maximum(np.linalg.norm(east, axis=1, keepdims=True), 1e-4)
        north = np.cross(Q, east); se = east @ Se; sn = north @ Se
        sh_u = cdrift + se * 0.0022 / np.maximum(np.cos(lat), 0.2); sh_v = -sn * 0.0022 / 1.0
        cs = np.clip(sample(tex["clouds"], (U + sh_u_pad(sh_u, m, k)) % 1.0, V + sh_u_pad(sh_v, m, k)).reshape(m)[:n] * 1.15 - 0.05, 0, 1) * p.get("clouds", 1.0)
        surf_gain = p.get("surface", 1.0); sea_gain = p.get("sea", 1.0)
        ground = alb * (irr * (1 - 0.55 * cs[:, None]) + twil * 0.012) * 1.25
        ground = ground * (1 - water[:, None] * (1 - sea_gain))
        # ocean glint
        Hv = S[None] + V_; Hv /= np.linalg.norm(Hv, axis=1, keepdims=True)
        nh = np.clip(np.sum(N * Hv, 1), 0, 1)
        fres = 0.02 + 0.98 * np.power(1 - mu_v, 5)
        glint = (np.power(nh, 220) * 2.2 + np.power(nh, 28) * 0.05) * fres * 8
        ground += (water * sea_gain * glint * (mu_s > 0) * (1 - cs))[:, None] * Ts * 0.6
        # night lights (under the clouds)
        night = sstep(0.06, -0.12, mu_s)
        city = smp("lights")[:, None] * np.array([1.0, 0.68, 0.36], F32) * (night * (1 - 0.65 * cl) * sstep(0.02, 0.3, mu_v) * p.get("lights", 1.0) * 2.4)[:, None]
        ground = ground * surf_gain + city
        # clouds over the top
        cloud = (irr * 1.6 + twil * 0.02) * np.array([1.0, 1.0, 1.0], F32)
        surf = ground * (1 - cl[:, None]) + cloud * cl[:, None] * surf_gain
        if p.get("surface_hook"):
            surf = p["surface_hook"](dict(surf=surf, u=u, v=v, lon=lon, lat=lat, mu_s=mu_s, mu_v=mu_v, water=water, clouds=cl, ys=ys, xs=xs, N=N))
        # atmosphere over the disk: extinction + in-scatter, more toward the limb
        airm = 1.0 / (mu_v + 0.035)
        tau = (BETA_R * 0.075 + BETA_M * 0.035)[None] * airm[:, None] * sky_gain
        cos = Dh @ S; ph_r = 0.0597 * (1 + cos * cos); ph_m = hg(cos, 0.78)
        scat = (BETA_R[None] * ph_r[:, None] + BETA_M[None] * ph_m[:, None] * 0.9) / (BETA_R + BETA_M)[None]
        lit_a = sstep(-0.1, 0.12, mu_s)[:, None] * sun_transmittance(mu_s, 1.0)
        ins = (1 - np.exp(-tau)) * lit_a * scat * 22.0 * p.get("atmo", 1.0)
        out[ys, xs] = surf * np.exp(-tau) + ins
    cover = hit.astype(F32)
    return out * E, cover, hit

def sh_u_pad(a, m, k):
    o = np.zeros(m, F32); o[:len(a)] = a; return o.reshape(-1, k)

# ---------------------------------------------------------------- other bodies (the Moon)
@lru_cache(None)
def moon_tex(seed=21, h=512, w=1024):
    rng = np.random.default_rng(seed)
    def noise(sc): return cv2.resize(rng.random((max(2, h // sc), max(2, w // sc))).astype(F32), (w, h), interpolation=cv2.INTER_CUBIC)
    fbm = sum(noise(s) * a for s, a in ((128, 1.0), (64, 0.6), (32, 0.4), (16, 0.25), (8, 0.15), (4, 0.1))) / 2.5
    maria = sstep(0.55, 0.62, cv2.GaussianBlur(noise(96), (0, 0), 6))
    alb = 0.17 - 0.08 * maria + 0.05 * (fbm - 0.5)
    yy, xx = np.mgrid[0:h, 0:w].astype(F32)
    for _ in range(260):                                                             # craters: dark floor, bright rim
        cx, cy, r = rng.uniform(0, w), rng.uniform(h * 0.1, h * 0.9), rng.pareto(2.2) * 3 + 2
        d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / r
        m = d < 1.6
        if m.any(): alb[m] += (-0.035 * (d[m] < 0.85) + 0.05 * np.exp(-((d[m] - 1.0) / 0.12) ** 2))
    return np.clip(np.repeat(alb[..., None], 3, 2) * np.array([1.0, 0.98, 0.95], F32), 0.02, 0.4)

def body(cam, D, center, radius, sun, tex, spin_deg=0.0, gain=1.0):
    """a textured, sun-lit sphere (e.g. the Moon). Returns radiance (H,W,3) and coverage mask."""
    H, W = D.shape[:2]; oc = cam.eye - np.asarray(center, F32)
    b = D @ oc; c = float(oc @ oc) - radius * radius; disc = b * b - c; hit = (disc > 0) & (b < 0)
    out = np.zeros((H, W, 3), F32)
    if hit.any():
        ys, xs = np.nonzero(hit); Dh = D[ys, xs]; t = -b[ys, xs] - np.sqrt(disc[ys, xs])
        N = (oc[None] + Dh * t[:, None]) / radius
        a = np.radians(spin_deg); Q = np.stack([N[:, 0] * np.cos(a) - N[:, 2] * np.sin(a), N[:, 1], N[:, 0] * np.sin(a) + N[:, 2] * np.cos(a)], 1)
        u = ((np.arctan2(Q[:, 0], Q[:, 2]) / (2 * np.pi) + 0.5) % 1).astype(F32); v = (0.5 - np.arcsin(np.clip(Q[:, 1], -1, 1)) / np.pi).astype(F32)
        alb = sample(tex, u[None], v[None])[0]
        mu = np.clip(N @ nrm(sun), 0, 1); mv = np.clip(np.sum(N * -Dh, 1), 1e-3, 1)
        ls = mu / (mu + mv + 1e-3) * 2.0                                              # Lommel-Seeliger: the flat, full look of the Moon
        out[ys, xs] = alb * (ls * 3.2 * gain)[:, None]
    return out, hit

# ---------------------------------------------------------------- stars + milky way
@lru_cache(None)
def star_catalog(n=14000, seed=7):
    rng = np.random.default_rng(seed)
    z = rng.uniform(-1, 1, n); a = rng.uniform(0, 2 * np.pi, n); r = np.sqrt(1 - z * z)
    d = np.stack([r * np.cos(a), z, r * np.sin(a)], 1).astype(F32)
    # concentrate a share of stars toward a galactic plane
    g = nrm((0.35, 0.86, -0.38)); k = int(n * 0.45)
    dd = d[:k] - np.outer(d[:k] @ g, g) * rng.uniform(0.6, 1.0, k)[:, None]
    d[:k] = dd / np.linalg.norm(dd, axis=1, keepdims=True)
    mag = rng.pareto(1.35, n).astype(F32) + 1.0                                     # many faint, few bright
    b = np.clip(mag * 0.018, 0, 30)
    temp = rng.choice([3200, 4200, 5200, 5800, 6500, 8000, 11000, 20000], n, p=[.12, .16, .16, .14, .14, .12, .10, .06])
    col = np.stack([bb_rgb(t) for t in temp]).astype(F32)
    return d, b.astype(F32), col

def bb_rgb(t):
    t = t / 100.0
    r = 255 if t <= 66 else 329.7 * (t - 60) ** -0.1332
    g = 99.47 * np.log(t) - 161.1 if t <= 66 else 288.1 * (t - 60) ** -0.0755
    b = 255 if t >= 66 else (0 if t <= 19 else 138.5 * np.log(t - 10) - 305.0)
    c = np.clip(np.array([r, g, b]) / 255, 0, 1) ** 2.2
    return c / max(c.max(), 1e-3)

def stars(img, cam, gain=1.0, occlude=True, twinkle_t=0.0):
    d, br, col = star_catalog()
    x, y, ok = cam.project(d)
    H, W = img.shape[:2]
    ok &= (x >= 1) & (x < W - 2) & (y >= 1) & (y < H - 2)
    if occlude:                                                                      # hidden behind the planet
        b = d @ cam.eye; c = float(cam.eye @ cam.eye) - 1
        ok &= ~((b * b - c > 0) & (b < 0))
    x, y, br, col = x[ok], y[ok], br[ok], col[ok]
    if twinkle_t: br = br * (1 + 0.12 * np.sin(twinkle_t * 3.1 + np.arange(len(br)) * 1.7))
    val = col * (br * gain)[:, None]
    x0 = np.floor(x).astype(int); y0 = np.floor(y).astype(int); fx = (x - x0)[:, None]; fy = (y - y0)[:, None]
    for dx, dy, w in ((0, 0, (1 - fx) * (1 - fy)), (1, 0, fx * (1 - fy)), (0, 1, (1 - fx) * fy), (1, 1, fx * fy)):
        np.add.at(img, (y0 + dy, x0 + dx), val * w)
    big = br > 1.2                                                                   # a few bright ones get a soft halo
    for xi, yi, bi, ci in zip(x[big], y[big], br[big], col[big]):
        glow_dot(img, xi, yi, ci * bi * gain * 0.05, 2.2)
    return img

@lru_cache(None)
def milky_way(seed=3):
    """equirect (1024x512) emission: a soft band with dust lanes, in galactic coordinates."""
    rng = np.random.default_rng(seed); h, w = 512, 1024
    lat = (0.5 - (np.arange(h) + 0.5) / h)[:, None] * np.pi; lon = ((np.arange(w) + 0.5) / w)[None] * 2 * np.pi
    noise = lambda s: cv2.resize(rng.random((max(2, h // s), max(2, w // s))).astype(F32), (w, h), interpolation=cv2.INTER_CUBIC)
    fbm = sum(noise(s) * (s / 64) for s in (64, 32, 16, 8, 4)) / sum(s / 64 for s in (64, 32, 16, 8, 4))
    dust = sum(noise(s) * (s / 32) for s in (32, 16, 8, 4)) / sum(s / 32 for s in (32, 16, 8, 4))
    band = np.exp(-(lat / (0.16 + 0.06 * np.cos(lon * 2))) ** 2) * (0.55 + 0.45 * np.cos(lon) ** 2)
    core = np.exp(-((lon - np.pi) / 0.5) ** 2 - (lat / 0.12) ** 2) * 0.8
    em = (band + core) * (0.5 + fbm) * np.clip(1 - 1.6 * np.clip(dust - 0.45, 0, 1) * np.exp(-(lat / 0.05) ** 2) * 2.2, 0.1, 1)
    em = cv2.GaussianBlur(em.astype(F32), (0, 0), 1.2)
    rgb = np.stack([em * 1.0, em * 0.92, em * 0.86], 2)
    return rgb.astype(F32)

def milkyway(img, D, gain=0.02, hit=None):
    """the band is soft, so it is looked up at 1/4 resolution and scaled up."""
    H, W = img.shape[:2]; Ds = D[2::4, 2::4]
    g = nrm((0.35, 0.86, -0.38)); a = nrm(np.cross(g, (0, 0, 1))); bb = np.cross(g, a)
    x = Ds @ a; y = Ds @ g; z = Ds @ bb
    u = (np.arctan2(z, x) / (2 * np.pi) + 0.5) % 1; v = 0.5 - np.arcsin(np.clip(y, -1, 1)) / np.pi
    mw = cv2.resize(sample(milky_way(), u.astype(F32), v.astype(F32)), (W, H), interpolation=cv2.INTER_LINEAR)
    if hit is not None: mw[hit] = 0
    img += mw * gain
    return img

# ---------------------------------------------------------------- sun, glows, flares
def glow_dot(img, x, y, rgb, sigma):
    H, W = img.shape[:2]; r = int(sigma * 4) + 1
    x0, x1, y0, y1 = max(0, int(x) - r), min(W, int(x) + r + 1), max(0, int(y) - r), min(H, int(y) + r + 1)
    if x1 <= x0 or y1 <= y0: return
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(F32)
    g = np.exp(-((xx - x) ** 2 + (yy - y) ** 2) / (2 * sigma * sigma))
    img[y0:y1, x0:x1] += g[..., None] * np.asarray(rgb, F32)

def sun_visibility(cam, sun, ang_r=0.006):
    """fraction of the sun's disk not hidden by the Earth (0..1), for eclipses and the 'diamond ring'."""
    S = nrm(sun); eye = cam.eye; de = float(np.linalg.norm(eye))
    ang_earth = np.arcsin(min(1.0, 1.0 / de)); ang_sep = np.arccos(np.clip(float(S @ (-eye / de)), -1, 1))
    return float(np.clip((ang_sep - ang_earth) / (2 * ang_r) + 0.5, 0, 1))

def sun(img, cam, sun_dir, intensity=1.0, spikes=6, spike_len=0.32, vis=None, rot=0.35):
    S = nrm(sun_dir); x, y, ok = cam.project(S[None]); x, y, ok = float(x[0]), float(y[0]), bool(ok[0])
    if not ok: return img
    v = sun_visibility(cam, S) if vis is None else vis
    if v <= 0: return img
    H, W = img.shape[:2]; k = intensity * v
    glow_dot(img, x, y, np.array([1.0, 0.97, 0.92]) * 60 * k, 2.0)
    glow_dot(img, x, y, np.array([1.0, 0.92, 0.80]) * 2.4 * k, 9)
    glow_dot(img, x, y, np.array([1.0, 0.85, 0.70]) * 0.25 * k, 40)
    starburst(img, x, y, k, spikes, spike_len * H, rot)
    return img

def starburst(img, x, y, k, n=6, length=500, rot=0.35, width=1.6):
    H, W = img.shape[:2]; r = int(length)
    x0, x1, y0, y1 = max(0, int(x) - r), min(W, int(x) + r + 1), max(0, int(y) - r), min(H, int(y) + r + 1)
    if x1 <= x0 or y1 <= y0: return
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(F32); dx, dy = xx - x, yy - y; rr = np.sqrt(dx * dx + dy * dy) + 1e-3
    acc = np.zeros_like(rr)
    for i in range(n):
        a = rot + i * np.pi / (n / 2) if n > 2 else rot + i * np.pi
        c, s = np.cos(a), np.sin(a)
        along = dx * c + dy * s; across = np.abs(-dx * s + dy * c)
        acc += np.exp(-(across / (width + rr * 0.004)) ** 2) * np.exp(-np.abs(along) / (length * 0.22)) * (along > 0)
    col = np.array([1.0, 0.93, 0.85], F32)
    img[y0:y1, x0:x1] += (acc * k * 1.0 / (1 + rr / 40))[..., None] * col

# ---------------------------------------------------------------- the eye (a lid of light)
def eye_mask(W, H, cx, cy, half_w, open_, curve=1.0, soft=2.5):
    """almond aperture: 1 inside, 0 outside. open_ = half-height at centre in px."""
    x, y = _grid(W, H); x = x + W / 2 - cx; y = (H / 2 - y) - cy
    xn = np.clip(np.abs(x) / max(half_w, 1), 0, 1)
    lid = open_ * np.power(np.clip(1 - xn * xn, 0, 1), curve)
    d = lid - np.abs(y)                                                           # >0 inside
    inside = np.clip(d / soft + 0.5, 0, 1) * (np.abs(x) < half_w)
    return inside.astype(F32), d.astype(F32), lid.astype(F32), x, y

def iris(W, H, cx, cy, r_in, r_out, t=0.0, seed=5, rot=0.0):
    """corona/iris light around the pupil, looked up from a cached polar image (fast for moving cameras)."""
    P = _iris_polar(seed, round(r_out / max(r_in, 1), 2)); na, nq = P.shape[:2]
    x, y = _grid(W, H); x = x + W / 2 - cx; y = (H / 2 - y) - cy
    rr = np.sqrt(x * x + y * y); ang = np.arctan2(y, x) + rot
    mx = (rr / max(r_in, 1) - 0.9) / (_IQ_MAX - 0.9) * (nq - 1); my = ((ang / (2 * np.pi)) % 1.0) * na
    return cv2.remap(P, mx.astype(F32), my.astype(F32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)

_IQ_MAX = 4.2
@lru_cache(4)
def _iris_polar(seed, ratio, na=6144, nq=700):
    q = np.linspace(0.9, _IQ_MAX, nq, dtype=F32)[None]; ang = (np.arange(na, dtype=F32)[:, None] / na) * 2 * np.pi - np.pi
    r_in = 300.0; rr = q * r_in + 0 * ang
    xx = rr * np.cos(ang); yy = rr * np.sin(ang)
    return _iris_eval(xx, yy, r_in, r_in * ratio, seed)

def _iris_eval(x, y, r_in, r_out, seed):
    """radial light fibres between the pupil (the dark planet) and the lids: HDR, cyan core, amber outer."""
    rr = np.sqrt(x * x + y * y) + 1e-3; ang = np.arctan2(y, x)
    fib_a, len_a = iris_noise(seed)
    k = ((ang / (2 * np.pi) + 0.5) * len(fib_a)).astype(F32)
    fib = cv2.remap(fib_a[None].repeat(2, 0), k, np.zeros_like(k), cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
    ln = cv2.remap(len_a[None].repeat(2, 0), k, np.zeros_like(k), cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
    rn = (rr - r_in) / max(r_out - r_in, 1)
    q = np.maximum(rr / max(r_in, 1), 1.0)
    fall = np.power(q, -2.2) * np.exp(-np.clip(rn, 0, None) * (0.6 + 2.8 * (1 - ln)))   # corona-like falloff, uneven lengths
    on = sstep(-0.004, 0.02, rn)
    streak = fall * on * (0.08 + 1.5 * fib)
    base = np.exp(-np.clip(rn, 0, None) * 5.0) * on * 0.35                              # soft glow hugging the pupil
    cyan = np.array([0.30, 0.86, 1.30], F32); white = np.array([1.1, 1.05, 1.0], F32); amber = np.array([1.5, 0.55, 0.15], F32)
    m1 = np.clip(rn * 2.2, 0, 1)[..., None]; m2 = np.clip((rn - 0.55) * 2.5, 0, 1)[..., None]
    col = (white * (1 - m1) + cyan * m1) * (1 - m2) + amber * m2
    return ((streak + base)[..., None] * col * 0.75).astype(F32)

@lru_cache(None)
def iris_noise(seed=5, n=8192):
    """1-D angular noise for iris fibres: thin bright fibres of random length (organic, not stripes)."""
    rng = np.random.default_rng(seed); f = np.zeros(n, F32)
    for oc, a in ((64, 0.35), (256, 0.35), (1024, 0.45), (4096, 0.6)):
        v = rng.random(oc).astype(F32); f += a * cv2.resize(v[None], (n, 1), interpolation=cv2.INTER_CUBIC)[0]
    f = np.power(np.clip(f / f.max(), 0, 1), 4.0) * 1.6
    ln = cv2.resize(rng.random(512).astype(F32)[None], (n, 1), interpolation=cv2.INTER_CUBIC)[0]
    return f.astype(F32), np.clip(ln, 0, 1).astype(F32)

def eye_layer(img, cx, cy, half_w, open_, glow=1.0, t=0.0, iris_img=None):
    """darken outside the aperture, put an amber glow on the lid edges (light leaking around a lid)."""
    H, W = img.shape[:2]
    inside, d, lid, x, y = eye_mask(W, H, cx, cy, half_w, open_)
    out = img * inside[..., None]
    if iris_img is not None: out += iris_img * inside[..., None]
    # rim light just outside the edge, strongest near the corners, thin bright line on the edge
    xr = np.abs(x) / max(half_w, 1)
    edge = np.exp(-np.maximum(-d, 0) / 14.0) * (d < 0) * (1 - sstep(0.97, 1.10, xr))     # soft past the corners (no hard cut)
    line = np.exp(-(d / 2.2) ** 2) * (1 - sstep(0.985, 1.03, xr))
    corner = 0.55 + 0.9 * np.power(np.clip(np.abs(x) / max(half_w, 1), 0, 1), 2)
    amber = np.array([1.6, 0.6, 0.16], F32)
    rim = (edge * 0.9 + line * 2.0) * corner * glow * sstep(0, 6, open_ + 2)
    # when nearly shut it's a single line of light
    out += rim[..., None] * amber
    return out

# ---------------------------------------------------------------- camera development
def bloom(img, strength=0.08, thresh=0.9):
    """same weights as a 6-level sum, accumulated small-to-large so only one full-size resize is needed."""
    H, W = img.shape[:2]
    lvl = cv2.resize(img, (W // 2, H // 2), interpolation=cv2.INTER_AREA); lvl = np.maximum(lvl - thresh, 0)
    levels = []
    for i in range(6):
        if i: lvl = cv2.resize(lvl, (max(1, lvl.shape[1] // 2), max(1, lvl.shape[0] // 2)), interpolation=cv2.INTER_AREA)
        levels.append(cv2.GaussianBlur(lvl, (0, 0), 1.6) * (0.9 ** i))
    acc = levels[-1]
    for g in reversed(levels[:-1]):
        acc = cv2.resize(acc, (g.shape[1], g.shape[0]), interpolation=cv2.INTER_LINEAR) + g
    return img + cv2.resize(acc, (W, H), interpolation=cv2.INTER_LINEAR) * strength

def aces(x):
    a, b, c, d, e = 2.51, 0.03, 2.43, 0.59, 0.14
    return np.clip((x * (a * x + b)) / (x * (c * x + d) + e), 0, 1)

def develop(img, exposure=1.0, bloom_k=0.07, grain=0.010, vignette=0.22, ca=1.0, fi=0, lift=0.0):
    x = bloom(img * exposure, bloom_k)
    if ca:
        H, W = x.shape[:2]; s = 1 + ca * 0.0009
        M = cv2.getRotationMatrix2D((W / 2, H / 2), 0, s); x[..., 0] = cv2.warpAffine(x[..., 0], M, (W, H), borderMode=cv2.BORDER_REFLECT)
        M = cv2.getRotationMatrix2D((W / 2, H / 2), 0, 1 / s); x[..., 2] = cv2.warpAffine(x[..., 2], M, (W, H), borderMode=cv2.BORDER_REFLECT)
    y = aces(x)
    if vignette: y *= _vig(x.shape[1], x.shape[0], float(vignette))[..., None]
    y = np.power(np.clip(y, 0, 1), 1 / 2.2)
    if lift: y = y * (1 - lift) + lift
    if grain:
        n = _grain(y.shape[0], y.shape[1], fi % 8)
        dy, dx = (fi * 7919) % y.shape[0], (fi * 104729) % y.shape[1]
        n = np.roll(n, (dy, dx), (0, 1)) * grain
        y += (n * (0.5 + 0.5 * (1 - y.mean(2))))[..., None]
    return (np.clip(y, 0, 1) * 255 + 0.5).astype(np.uint8)

@lru_cache(4)
def _vig(W, H, k):
    gx, gy = _grid(W, H); r = np.sqrt((gx / (W / 2)) ** 2 + (gy / (H / 2)) ** 2) / 1.414
    return (1 - k * np.power(r, 2.4)).astype(F32)

@lru_cache(16)
def _grain(H, W, i):
    return np.random.default_rng(i * 7919 + 13).standard_normal((H, W)).astype(F32)
