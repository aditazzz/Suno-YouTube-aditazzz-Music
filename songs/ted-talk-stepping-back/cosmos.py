"""Everything bigger than the weather: the Earth (photoreal, studio.space), the Moon, the solar system, the stars,
the Milky Way, the Local Group, the cosmic web and the edge of the observable universe.

From the Earth onward the picture is a top-down 'map' of space: the camera looks down on the plane of the planets,
always centred on the same spot (the question), and every scale is labelled like a map."""
import math, os
from functools import lru_cache
import numpy as np, cv2
import studio.space as SP
import zoomnoise as ZN
from view import View

F32 = np.float32
R_E = 6.371e6; AU = 1.496e11; LY = 9.4607e15
LAT0, LON0 = 39.1, -94.6                       # the office
FOV = 24.0
HERE = os.path.dirname(os.path.abspath(__file__))

def ef(lat, lon):
    la, lo = math.radians(lat), math.radians(lon)
    return np.array([math.cos(la) * math.sin(lo), math.sin(la), math.cos(la) * math.cos(lo)], F32)

def _rot():
    la, lo = math.radians(LAT0), math.radians(LON0)
    q0 = ef(LAT0, LON0); e = np.array([math.cos(lo), 0, -math.sin(lo)], F32)
    n = np.array([-math.sin(la) * math.sin(lo), math.cos(la), -math.sin(la) * math.cos(lo)], F32)
    return np.stack([e, n, q0], 1).astype(F32)              # world -> Earth-fixed (columns: east, north, up)
ROT = _rot()

def sun_world(days=0.0):
    """direction to the Sun in world coordinates, `days` after 9:15 a.m. on Oct 21 (the Earth turns under it)."""
    return SP.nrm(ROT.T @ ef(-10.9, -29.9 - 360.0 * days))

def _pole():
    s = ef(-10.9, -29.9); p = ef(66.56, 25.6); p = p - (p @ s) * s
    return SP.nrm(ROT.T @ SP.nrm(p))
POLE = _pole()                                                   # ecliptic north, world coordinates

def frame_R(z):
    """16:9 frame width at the ground, in Earth radii"""
    return 10 ** z / R_E

def pole_mix(z):
    return SP.sstep(7.3, 8.7, z)

def cam_for(z, W, H):
    """straight down over the office at low z; turning to look down on the plane of the planets as the Earth shrinks."""
    fpx = 540.0 / math.tan(math.radians(FOV) / 2)
    D = 1.0 + frame_R(z) * fpx / 1920.0
    k = float(pole_mix(z))
    d0 = np.array([0, 0, 1], F32); d = SP.nrm(d0 * (1 - k) + POLE * k) if k > 0 else d0
    up0 = np.array([0, 1, 0], F32)
    up = SP.nrm(up0 - (up0 @ d) * d)
    return SP.Cam(d * D, (0, 0, 0), up, FOV, W, H)

def plane_axes():
    """screen axes of the final (pole) camera, as world vectors: right, up"""
    c = cam_for(9.5, 1920, 1080); return c.r.astype(np.float64), c.u.astype(np.float64)

MOON_ANG = math.radians(35)
def moon_pos():
    r, u = plane_axes(); return (60.3 * (math.cos(MOON_ANG) * r + math.sin(MOON_ANG) * u)).astype(F32)

# ---------------------------------------------------------------- local clouds on the Earth (match the map's clouds)
def local_cloud_alpha(cam, W, H, cover, mpp, step=3):
    """the map's cloud deck (world-anchored noise around the office) as seen on the globe: a screen-space alpha map
    computed at 1/step resolution (ray -> ground point -> local metres -> cloud field)."""
    import citymap as CM
    D = cam.rays(step); eye = cam.eye
    b = D @ eye; c = float(eye @ eye) - 1.0; disc = b * b - c; hit = (disc > 0) & (b < 0)
    tt = -b - np.sqrt(np.maximum(disc, 0)); P = eye[None, None] + D * tt[..., None]
    Q = mat_rot(P)
    lat = np.arcsin(np.clip(Q[..., 1], -1, 1)); lon = np.arctan2(Q[..., 0], Q[..., 2])
    dlat = lat - math.radians(LAT0); dlon = (lon - math.radians(LON0) + np.pi) % (2 * np.pi) - np.pi
    X = (dlon * np.cos(lat) * R_E).astype(np.float64); Y = (-dlat * R_E).astype(np.float64)
    r = np.sqrt(X * X + Y * Y)
    fld = CM.cloud_field(X, Y, mpp * step)
    thr = 1.02 - cover * 0.62
    a = np.clip((fld - thr) / 0.10, 0, 1) * np.clip((2.6e6 - r) / 0.8e6, 0, 1) * hit
    return cv2.resize(a.astype(F32), (W, H), interpolation=cv2.INTER_LINEAR)

def mat_rot(P):
    return SP.mat3(P.astype(F32), ROT.T) if False else (P.reshape(-1, 3) @ ROT.T.astype(F32)).reshape(P.shape)

def local_cloud_hook(alpha):
    def hook(d):
        a = alpha[d["ys"], d["xs"]]
        if not (a > 0.002).any(): return d["surf"]
        mu = np.clip(d["mu_s"], 0, 1)
        cl = (mu * 1.6 + 0.01)[:, None] * np.array([1.0, 1.0, 1.0], F32)
        return d["surf"] * (1 - a[:, None]) + cl * a[:, None]
    return hook

# ---------------------------------------------------------------- star backdrop (fixed sky)
def sky(img, cam, gain=1.0):
    SP.stars(img, cam, gain=gain, occlude=True)
    return img

def develop_f(img, exposure=1.0, bloom_k=0.06, vignette=0.18):
    x = SP.bloom(img * exposure, bloom_k)
    y = SP.aces(x)
    if vignette: y *= SP._vig(x.shape[1], x.shape[0], float(vignette))[..., None]
    return np.power(np.clip(y, 0, 1), 1 / 2.2).astype(F32)

def render_earth(z, t, W, H, days=0.0, cloud_cover=None):
    """HDR radiance for the Earth (+Moon, stars). Returns (img, earth_cover_mask, cam)."""
    cam = cam_for(z, W, H); D = cam.rays()
    S = sun_world(days)
    p = {"exposure": 1.0, "lights": 1.2}
    if cloud_cover is not None:
        mpp = 10 ** z / 1920
        p["surface_hook"] = local_cloud_hook(local_cloud_alpha(cam, W, H, cloud_cover, mpp))
    img, cover, hit = SP.earth(cam, D, S, ROT, p)
    if z > 7.6:
        mo, mhit = SP.body(cam, D, moon_pos(), 0.2727, S, SP.moon_tex(), spin_deg=0.0, gain=1.0)
        img = np.where(mhit[..., None], mo, img); hit = hit | mhit
    sk = np.zeros_like(img); sky(sk, cam, gain=float(np.clip((z - 6.4) / 0.8, 0, 1)) * 0.9)
    sk[hit] = 0
    img += sk
    return img, cover, cam

# ---------------------------------------------------------------- the solar system (2-D, metres, Sun at the origin)
PLANETS = [  # name, a (AU), period (yr), start angle (deg), radius (m), colour
    ("Mercury", 0.387, 0.241, 40, 2.44e6, (0.75, 0.72, 0.68)), ("Venus", 0.723, 0.615, 140, 6.05e6, (0.95, 0.88, 0.70)),
    ("Earth", 1.0, 1.0, None, 6.371e6, (0.45, 0.65, 1.0)), ("Mars", 1.524, 1.881, 300, 3.39e6, (0.95, 0.52, 0.35)),
    ("Jupiter", 5.203, 11.86, 215, 6.99e7, (0.92, 0.80, 0.66)), ("Saturn", 9.537, 29.45, 330, 5.82e7, (0.93, 0.85, 0.62)),
    ("Uranus", 19.19, 84.0, 60, 2.54e7, (0.62, 0.86, 0.92)), ("Neptune", 30.07, 164.8, 350, 2.46e7, (0.42, 0.58, 1.0))]

def sun_dir_2d():
    """unit vector toward the Sun from the Earth, in the pole camera's screen axes (x right, y down)."""
    r, u = plane_axes(); S = sun_world(0).astype(np.float64)
    v = np.array([S @ r, -(S @ u)]); return v / np.linalg.norm(v)

def earth_angle0():
    v = -sun_dir_2d(); return math.atan2(v[1], v[0])        # Earth's heliocentric direction

def planet_positions(years):
    """heliocentric 2-D positions (m) after `years` of orbit time"""
    out = {}
    e0 = earth_angle0()
    for name, a, per, ang, rad, col in PLANETS:
        a0 = e0 if ang is None else math.radians(ang)
        th = a0 - 2 * math.pi * years / per                  # counter-clockwise seen from ecliptic north = clockwise on a y-down screen
        out[name] = np.array([a * AU * math.cos(th), a * AU * math.sin(th)])
    return out

# ---------------------------------------------------------------- 2-D drawing into an HDR image
def _mask_draw(H, W, fn):
    m = np.zeros((H, W), np.uint8); fn(m); return m.astype(F32) / 255.0

def ring(img, view, c, R, col, gain, wpx=1.4, dash=False):
    """a circle of world radius R around world point c, only the visible arc is drawn"""
    H, W = img.shape[:2]; cs = view.to_px(np.asarray(c, np.float64)[None])[0]; Rp = R / view.mpp
    if Rp < 1.5: return
    dc = np.hypot(cs[0] - W / 2, cs[1] - H / 2); hd = math.hypot(W, H) / 2
    if dc - Rp > hd + 4 or Rp - dc > hd + 4: return            # entirely outside, or the frame is inside the circle
    if Rp > 4 * hd:
        th_c = math.atan2(H / 2 - cs[1], W / 2 - cs[0]); dth = (hd * 1.6) / Rp
        th = np.linspace(th_c - dth, th_c + dth, 600)
    else: th = np.linspace(0, 2 * np.pi, int(np.clip(Rp * 0.7, 48, 2400)))
    P = np.stack([cs[0] + Rp * np.cos(th), cs[1] + Rp * np.sin(th)], 1)
    q = np.round(P * 16).astype(np.int64); q = np.clip(q, -2 ** 30, 2 ** 30).astype(np.int32)
    def f(m):
        if dash:
            for i in range(0, len(q) - 1, 2): cv2.line(m, tuple(q[i]), tuple(q[i + 1]), 255, max(1, int(round(wpx))), cv2.LINE_AA, 4)
        else: cv2.polylines(m, [q], False, 255, max(1, int(round(wpx))), cv2.LINE_AA, 4)
    a = _mask_draw(H, W, f) * (min(1.0, wpx) if wpx < 1 else 1.0)
    img += a[..., None] * np.asarray(col, F32) * gain

def dot(img, x, y, rpx, col, gain=1.0, glow=0.0):
    H, W = img.shape[:2]
    if x < -50 or y < -50 or x > W + 50 or y > H + 50: return
    if rpx < 1.6:
        SP.glow_dot(img, x, y, np.asarray(col, F32) * gain * 2.0, max(0.7, rpx))
    else:
        m = _mask_draw(H, W, lambda mm: cv2.circle(mm, (int(round(x * 16)), int(round(y * 16))), int(round(rpx * 16)), 255, -1, cv2.LINE_AA, 4))
        img += m[..., None] * np.asarray(col, F32) * gain
    if glow > 0: SP.glow_dot(img, x, y, np.asarray(col, F32) * glow, max(2.0, rpx * 1.6))

def sun_glow(img, x, y, k=1.0, rpx=2.0, spikes=True):
    SP.glow_dot(img, x, y, np.array([1.0, 0.97, 0.9]) * 40 * k, max(1.6, rpx))
    SP.glow_dot(img, x, y, np.array([1.0, 0.9, 0.75]) * 2.2 * k, max(8, rpx * 3))
    SP.glow_dot(img, x, y, np.array([1.0, 0.82, 0.6]) * 0.22 * k, max(40, rpx * 12))
    if spikes: SP.starburst(img, x, y, k * 0.8, 6, 260, 0.35)

# ---------------------------------------------------------------- stars between the stars (hierarchical point bands)
@lru_cache(None)
def star_bands():
    """bands of stars around the Sun: band k has one star per (L_k)^2, L_k = 1.2 ly * 2.6^k; brighter bands are rarer."""
    rng = np.random.default_rng(31); bands = []
    for k in range(9):
        L = 1.2 * LY * 2.6 ** k; n = 2600
        P = rng.uniform(-0.5, 0.5, (n, 2)) * L * math.sqrt(n)
        temp = rng.choice([3200, 3800, 4500, 5500, 6200, 7500, 10000, 18000], n, p=[.30, .18, .14, .12, .09, .08, .06, .03])
        col = np.stack([SP.bb_rgb(tt) for tt in temp]).astype(F32)
        br = (rng.pareto(1.6, n) + 1.0).astype(F32)
        bands.append((L, P, col, br))
    return bands

NAMED_STARS = [("Alpha Centauri", 4.37, 205), ("Barnard's Star", 5.96, 120), ("Sirius", 8.6, 300), ("Procyon", 11.4, 20),
               ("Vega", 25.0, 75), ("Arcturus", 36.7, 160), ("Betelgeuse", 548, 255), ("Rigel", 863, 330)]

def named_star_pos(name):
    for n_, d, a in NAMED_STARS:
        if n_ == name: return np.array([d * LY * math.cos(math.radians(a)), d * LY * math.sin(math.radians(a))])

def draw_stars_world(img, view, gain=1.0, galaxy_mod=None):
    H, W = img.shape[:2]; b = view.box
    for (L, P, col, br) in star_bands():
        sp = L / view.mpp                                       # typical spacing in px
        w = float(np.clip((sp - 5) / 10, 0, 1) * np.clip((900 - sp) / 500, 0, 1))
        if w <= 0: continue
        sel = (P[:, 0] > b[0]) & (P[:, 0] < b[2]) & (P[:, 1] > b[1]) & (P[:, 1] < b[3])
        if not sel.any(): continue
        S = view.to_px(P[sel]); c = col[sel]; bb = br[sel] * w * gain
        if galaxy_mod is not None: bb = bb * galaxy_mod(P[sel])
        x, y = S[:, 0], S[:, 1]
        ok = (x >= 1) & (x < W - 2) & (y >= 1) & (y < H - 2)
        x, y, c, bb = x[ok], y[ok], c[ok], bb[ok]
        val = c * (bb * 0.55)[:, None]
        x0 = np.floor(x).astype(int); y0 = np.floor(y).astype(int); fx = (x - x0)[:, None]; fy = (y - y0)[:, None]
        for dx, dy, ww in ((0, 0, (1 - fx) * (1 - fy)), (1, 0, fx * (1 - fy)), (0, 1, (1 - fx) * fy), (1, 1, fx * fy)):
            np.add.at(img, (y0 + dy, x0 + dx), val * ww)
        big = bb > 2.5
        for xi, yi, ci, bi in zip(x[big], y[big], c[big], bb[big]):
            SP.glow_dot(img, xi, yi, ci * min(bi, 12) * 0.035, 2.0)

# ---------------------------------------------------------------- galaxies (procedural, cached)
GAL_HALF = 90000 * LY                                           # the texture spans +-90,000 light-years
def _galaxy(n=2048, seed=4, arms=2, pitch=12.0, bar_ang=0.5, minor=0.55, warm=0.0, R_disk=52000.0, r_arm=9000.0, bar=1.0, tag="mw"):
    """a face-on barred spiral, HDR linear RGB, spanning +-90,000 light-years (cached in build/)."""
    path = os.path.join(HERE, "build", f"galaxy_{tag}_{n}_{seed}.npy")
    if os.path.exists(path): return np.load(path).astype(F32)
    rng = np.random.default_rng(seed)
    c = (np.arange(n) + 0.5 - n / 2) / (n / 2) * 90000.0
    X, Y = np.meshgrid(c, c); r = np.sqrt(X * X + Y * Y) + 1e-3; th = np.arctan2(Y, X)
    px = 180000.0 / n
    nzA = ZN.fbm(X, Y, px, seed=seed + 40, lam_max=14000, lam_min=150, gain=0.6, px_cut=1.2)     # arm brightness
    nzW = ZN.fbm(X, Y, px, seed=seed + 41, lam_max=20000, lam_min=600, gain=0.55, px_cut=1.2)    # arm wobble
    nzD = ZN.fbm(X, Y, px, seed=seed + 42, lam_max=5000, lam_min=90, gain=0.62, px_cut=1.0)      # dust filaments
    nzK = ZN.fbm(X, Y, px, seed=seed + 43, lam_max=1800, lam_min=70, gain=0.65, px_cut=1.0)      # knots
    kk = 1.0 / math.tan(math.radians(pitch))
    lr = np.log(np.maximum(r, r_arm * 0.6) / r_arm)
    wob = (nzW - 0.5) * 0.55
    arms_img = np.zeros_like(r); dust_img = np.zeros_like(r)
    offs = [(0.0, 1.0), (np.pi, 1.0)] + ([(np.pi / 2, minor), (3 * np.pi / 2, minor)] if minor > 0 else [])
    for off, strength in offs:
        d = np.angle(np.exp(1j * (th - off - lr * kk + wob)))
        dist = np.abs(d) * r
        w = 2600 + r * 0.13
        arms_img += np.exp(-(dist / w) ** 2) * strength
        dd = np.angle(np.exp(1j * (d + (w * 0.9) / np.maximum(r, 1))))
        dust_img += np.exp(-((np.abs(dd) * r) / (w * 0.32)) ** 2) * strength
    ramp = sstep_np(r_arm * 0.7, r_arm * 1.25, r) * sstep_np(R_disk * 1.3, R_disk * 0.8, r)
    mod = np.clip(0.1 + 2.2 * (nzA - 0.36), 0.0, 1.9) ** 1.3
    arm = arms_img * ramp * mod
    disk = np.exp(-r / (R_disk / 4.3)) * sstep_np(R_disk * 1.5, R_disk * 1.0, r)
    xb = X * math.cos(bar_ang) + Y * math.sin(bar_ang); yb = -X * math.sin(bar_ang) + Y * math.cos(bar_ang)
    barI = np.exp(-(xb / (r_arm * 1.0)) ** 2 - (yb / (r_arm * 0.32)) ** 2) * bar
    bulge = np.exp(-(r / 3600.0) ** 2) * 1.4 + np.exp(-(r / 1100.0) ** 2) * 2.6
    knots = np.clip((nzK - 0.60) * 4.0, 0, 1) * arm
    young = arm * 0.85 + knots * 1.6
    old = disk * (0.45 + 0.25 * nzA) + barI * 1.0 + bulge + arm * disk * 2.0
    dust = 1 - 0.78 * np.clip(dust_img, 0, 1) * ramp * np.clip((nzD - 0.30) * 2.2, 0, 1)
    dust *= 1 - 0.35 * np.clip((nzD - 0.58) * 3, 0, 1) * sstep_np(R_disk, R_disk * 0.3, r)
    col_old = np.array([1.0, 0.80 - 0.05 * warm, 0.57 - 0.08 * warm], F32); col_young = np.array([0.64, 0.79, 1.0], F32)
    img = (old[..., None] * col_old + young[..., None] * col_young) * dust[..., None]
    # pink star-forming knots and blue clusters along the arms
    P = rng.uniform(-R_disk * 1.2, R_disk * 1.2, (160000, 2))
    ix = ((P[:, 0] / 90000) * (n / 2) + n / 2).astype(int).clip(0, n - 1); iy = ((P[:, 1] / 90000) * (n / 2) + n / 2).astype(int).clip(0, n - 1)
    pa = np.clip(arm[iy, ix], 0, 1.5) ** 1.5
    keep = rng.random(len(P)) < pa * 0.35
    kinds = rng.random(keep.sum()); amp = rng.uniform(0.6, 1.6, keep.sum())
    pink = np.array([1.0, 0.40, 0.58], F32) * 2.2; blue = np.array([0.72, 0.86, 1.0], F32) * 2.6
    np.add.at(img, (iy[keep], ix[keep]), np.where((kinds < 0.4)[:, None], pink, blue) * amp[:, None])
    # unresolved stars: a fine speckle over the disk
    sp = rng.random((n, n)).astype(F32); spk = np.clip((sp - 0.982) * 60, 0, 1)
    img += spk[..., None] * (disk * 1.6 + arm * 0.6 + 0.015)[..., None] * np.array([1.0, 0.95, 0.9], F32)
    img = cv2.GaussianBlur(img.astype(F32), (0, 0), 0.55)
    img *= sstep_np(89000, 80000, np.maximum(np.abs(X), np.abs(Y)))[..., None]
    os.makedirs(os.path.dirname(path), exist_ok=True); np.save(path, img.astype(np.float16))
    return img.astype(F32)

def sstep_np(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)

@lru_cache(None)
def galaxy(kind="mw"):
    if kind == "mw": return _galaxy(2048, 4, 2, 19.0, 0.5, minor=0.38, warm=0.0, R_disk=52000, r_arm=10000, bar=1.3, tag="mw")
    return _galaxy(1024, 9, 2, 14.0, 1.2, minor=0.2, warm=1.0, R_disk=62000, r_arm=8000, bar=0.3, tag="m31")

def blit_galaxy(img, view, center, half, tex, gain=1.0, incl=1.0, pa=0.0):
    """draw a galaxy texture covering [-half, half]^2 around world point `center`, squashed by incl, turned by pa."""
    H, W = img.shape[:2]; n = tex.shape[0]
    cs = view.to_px(np.asarray(center, np.float64)[None])[0]; s = half / view.mpp      # half-size in px
    if s < 1.0: return
    if cs[0] + s < -10 or cs[0] - s > W + 10 or cs[1] + s < -10 or cs[1] - s > H + 10: return
    # screen -> texture: u = n/2 + R(-pa) * ((p - cs) / s) scaled for inclination * n/2
    c, sn = math.cos(pa), math.sin(pa)
    A = np.array([[c, sn], [-sn, c]]) / s; A[1] /= max(incl, 1e-3)
    M = np.zeros((2, 3)); M[:, :2] = A * (n / 2); M[:, 2] = -A @ cs * (n / 2) + n / 2
    src = tex
    if s * 2 < n / 2:     # minify: pre-shrink to avoid sparkle
        f = max(1, int(n / (s * 2)))
        lv = tex
        while lv.shape[0] > s * 4 and lv.shape[0] > 8: lv = cv2.pyrDown(lv)
        src = lv; M[:, :2] *= src.shape[0] / n; M[:, 2] = (M[:, 2] - n / 2) * (src.shape[0] / n) + src.shape[0] / 2
    out = cv2.warpAffine(src, M, (W, H), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    boost = 1.0 + 2.5 * float(np.clip((70 - s) / 60, 0, 1))          # small (distant) galaxies: keep them visible
    img += out * gain * boost
    if s < 90: SP.glow_dot(img, cs[0], cs[1], np.array([1.0, 0.9, 0.75], F32) * gain * 0.6 * float(np.clip((90 - s) / 60, 0, 1)), max(2.0, s * 0.18))

# ---------------------------------------------------------------- the cosmic web + the edge of the observable universe
R_OBS = 46.5e9 * LY
def _hash2(i, j, s):
    a = np.sin(i * 127.1 + j * 311.7 + s * 74.7) * 43758.5453; b = np.sin(i * 269.5 + j * 183.3 + s * 246.1) * 43758.5453
    return a - np.floor(a), b - np.floor(b)

def worley(X, Y, cell, seed):
    """distances (cell units) to the nearest three cell points: F2-F1 ~ 0 on the walls, F3-F1 ~ 0 where walls meet"""
    gx = X / cell; gy = Y / cell; ix = np.floor(gx); iy = np.floor(gy); fx = gx - ix; fy = gy - iy
    F1 = np.full(X.shape, 9.0); F2 = np.full(X.shape, 9.0); F3 = np.full(X.shape, 9.0)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            hx, hy = _hash2(ix + dx, iy + dy, seed)
            px = dx + 0.08 + hx * 0.84 - fx; py = dy + 0.08 + hy * 0.84 - fy
            d = np.sqrt(px * px + py * py)
            F3 = np.where(d < F2, F2, np.minimum(F3, d))
            F2 = np.where(d < F1, F1, np.where(d < F2, d, F2))
            F1 = np.minimum(F1, d)
    return F1, F2, F3

WEB_CELLS = [(2.2e9 * LY, 0.8, 10), (520e6 * LY, 1.0, 11), (150e6 * LY, 0.8, 12), (45e6 * LY, 0.6, 13)]
def web_density(X, Y, mpp):
    """filaments of galaxies along the walls of cells at three scales, bright knots where walls meet, uneven strength;
    scales too small for the pixel grid fade to their (dim) average"""
    out = np.zeros(X.shape); tot = 0.0
    for cell, wgt, seed in WEB_CELLS:
        px = cell / max(mpp, 1e-9)
        k = float(np.clip((px - 14) / 30, 0, 1) * np.clip((14000 - px) / 7000, 0, 1))   # only while the cells fit the frame
        if k > 0:
            F1, F2, F3 = worley(X, Y, cell, seed)
            wpx = max(1.5, min(0.010 * cell, 4e6 * LY) / max(mpp, 1e-9))     # filament half-width in pixels
            wc = wpx * mpp / cell
            fil = np.exp(-((F2 - F1) / wc) ** 2)
            node = np.exp(-((F3 - F1) / (wc * 3.5)) ** 2)
            mod = np.clip((ZN.fbm(X, Y, mpp, seed=seed + 50, lam_max=cell * 0.6, lam_min=cell * 0.04, gain=0.6, px_cut=3) - 0.36) * 3.2, 0.05, 1.7)
            soft = float(np.clip(14.0 / wpx, 0.12, 1.0))                     # wide (close-up) filaments: just a faint haze
            out += wgt * (k * (fil * mod + node * 2.2 * mod) * soft + (1 - k) * 0.08)
        else: out += wgt * 0.08
        tot += wgt
    return out / tot

@lru_cache(None)
def galaxy_points():
    """galaxies as points, in bands of spacing (like the stars), kept where the web is dense"""
    rng = np.random.default_rng(77); bands = []
    for k in range(8):
        L = 1.6e6 * LY * 2.4 ** k; n = 9000
        P = rng.uniform(-0.5, 0.5, (n, 2)) * L * math.sqrt(n)
        d = web_density(P[:, 0], P[:, 1], L / 200.0)
        keep = rng.random(n) < np.clip(d * 1.6, 0, 1) ** 1.5
        P = P[keep]; m = len(P)
        col = np.where((rng.random(m) < 0.5)[:, None], np.array([1.0, 0.88, 0.72], F32), np.array([0.80, 0.86, 1.0], F32))
        br = (rng.pareto(1.8, m) + 1.0).astype(F32)
        bands.append((L, P, col.astype(F32), br))
    return bands

def cosmic_web(img, view, gain=1.0, step=3):
    H, W = img.shape[:2]
    X, Y = view.grid(step); mpp = view.mpp * step
    dens = web_density(X, Y, mpp)
    r = np.sqrt(X * X + Y * Y)
    fade = np.clip((R_OBS * 0.93 - r) / (R_OBS * 0.25), 0, 1)                 # the young universe: no galaxies yet
    glow = cv2.GaussianBlur(dens.astype(F32), (0, 0), 0.9) * fade
    col = np.stack([glow * 0.62, glow * 0.52, glow * 0.70], 2) * 0.72 * gain
    img += cv2.resize(col.astype(F32), (W, H), interpolation=cv2.INTER_LINEAR)
    # resolved galaxies as points
    b = view.box
    for (L, P, c, br) in galaxy_points():
        sp = L / view.mpp; w = float(np.clip((sp - 4) / 8, 0, 1) * np.clip((700 - sp) / 400, 0, 1))
        if w <= 0: continue
        sel = (P[:, 0] > b[0]) & (P[:, 0] < b[2]) & (P[:, 1] > b[1]) & (P[:, 1] < b[3])
        if not sel.any(): continue
        S_ = view.to_px(P[sel]); x, y = S_[:, 0], S_[:, 1]; cc = c[sel]; bb = br[sel] * w * gain
        rr = np.sqrt(P[sel][:, 0] ** 2 + P[sel][:, 1] ** 2); bb = bb * np.clip((R_OBS * 0.93 - rr) / (R_OBS * 0.25), 0, 1)
        ok = (x >= 1) & (x < W - 2) & (y >= 1) & (y < H - 2)
        x, y, cc, bb = x[ok], y[ok], cc[ok], bb[ok]
        val = cc * (bb * 0.45)[:, None]
        x0 = np.floor(x).astype(int); y0 = np.floor(y).astype(int); fx = (x - x0)[:, None]; fy = (y - y0)[:, None]
        for dx, dy, ww in ((0, 0, (1 - fx) * (1 - fy)), (1, 0, fx * (1 - fy)), (0, 1, (1 - fx) * fy), (1, 1, fx * fy)):
            np.add.at(img, (y0 + dy, x0 + dx), val * ww)
    return img

def universe_edge(img, view, gain=1.0):
    """the cosmic microwave background as a glowing shell at the edge of what we can see; nothing outside."""
    H, W = img.shape[:2]
    X, Y = view.grid(2); r = np.sqrt(X * X + Y * Y) / R_OBS
    shell = np.exp(-((r - 1.0) / 0.018) ** 2) * 1.6 + np.exp(-((r - 1.0) / 0.07) ** 2) * 0.35
    inside = np.clip((1.0 - r) / 0.01, 0, 1)
    nz = ZN.fbm(X, Y, view.mpp * 2, seed=71, lam_max=5e25, lam_min=1e23, gain=0.6, px_cut=2.0)
    shell *= (0.65 + 0.7 * nz)
    col = np.stack([shell * 1.0, shell * 0.55, shell * 0.32], 2) * gain
    col = cv2.resize(col.astype(F32), (W, H), interpolation=cv2.INTER_LINEAR)
    ins = cv2.resize(inside.astype(F32), (W, H), interpolation=cv2.INTER_LINEAR)
    img *= (0.15 + 0.85 * ins)[..., None]
    img += col
    return img
