"""Skies and steam for Thirsty (The Data Center Next Door).

sky(cv, S)    twilight -> night sky per pixel: gradient, sunset glow, a cloud deck at 1.6 km lit from below by the
              sunset (pink / orange linings, mauve bodies) or at night by the facility's light dome (cold teal-white),
              and stars where the sky is dark. S['mirror'] draws the sky seen in the water (ray y flipped).
plume(...)    a billowing steam column above a cooling stack, as a soft volume billboard in the world: noise scrolled
              upward and warped, widening with height, lit warm from below, by the sky from above, and pink at dusk.
"""
import math
from functools import lru_cache
import numpy as np, cv2
import ys_eng as E
from ys_eng import F32, hexc, sample, fbm_tex

# twilight palette (linear)
Z_NIGHT = hexc('050a16'); H_NIGHT = hexc('0f1a2c')
Z_DUSK = hexc('0a1430'); M_DUSK = hexc('27304e'); H_DUSK = hexc('d8646a'); SUN_DUSK = hexc('ff8a4a'); ANTI = hexc('1e2a50')
CL_LIT = hexc('ff8278'); CL_GOLD = hexc('ffa060'); CL_BODY = hexc('1d1f33'); CL_NIGHT = hexc('141b2b')
DOME = hexc('9fc4d0')

def sky(cv, S, res=4):
    """fill every pixel without depth with sky (computed at 1/res and upsampled; stars at full res).
    S keys: dusk [0..1], sun_az (rad), glow_az, glow (0..), cloud (0..1), cloud_t (s of drift), stars (0..1),
    mirror (bool), haze (0..1)."""
    cam = cv.cam
    mask = ~np.isfinite(cv.dep)
    if not mask.any(): return
    lc = E.lowres_cam(cam, res)
    col, dens = sky_colour(lc, S)
    up = cv2.resize(col, (cv.W, cv.H), interpolation=cv2.INTER_LINEAR)
    cv.img[mask] = up[mask]
    if dens is not None: cv.sky_cloud = cv2.resize(dens, (cv.W, cv.H), interpolation=cv2.INTER_LINEAR)
    st = float(S.get('stars', 0.0))
    if st > 0: _stars(cv, st, S.get('mirror', False), getattr(cv, 'sky_cloud', None))

def sky_colour(cam, S):
    D, k = cam.dirs()
    dusk = float(S.get('dusk', 0.0)); cloud = float(S.get('cloud', 0.6)); mir = S.get('mirror', False)
    dx, dy, dz = D[..., 0], D[..., 1], D[..., 2]
    if mir: dy = -dy
    el = np.clip(dy, -0.2, 1.0)
    az = np.arctan2(dx, dz)
    sun_az = S.get('sun_az', -0.6); glow_az = S.get('glow_az', -1.2)
    sunf = (0.5 + 0.5 * np.cos(az - sun_az)).astype(F32)
    hor = np.exp(-np.maximum(el, 0) / 0.11).astype(F32)            # 1 at the horizon
    up = np.clip(el / 0.55, 0, 1).astype(F32)
    zn = Z_NIGHT * (1 - dusk) + Z_DUSK * dusk
    # toward the sun the low sky is pink; away from it, the blue-violet of the earth's shadow
    hn_d = (M_DUSK[None, None] * (0.55 + 0.45 * sunf[..., None]) + ANTI[None, None] * (1 - sunf[..., None]) * 0.6)
    hn = H_NIGHT[None, None] * (1 - dusk) + hn_d * dusk
    col = zn[None, None] * up[..., None] + hn * (1 - up[..., None])
    sg = (hor ** 1.6 * sunf ** 4.0 * dusk)[..., None]
    col = col + SUN_DUSK * sg * 0.9 + H_DUSK * (hor ** 1.7 * sunf ** 2.4 * dusk * 0.5)[..., None]
    gw = float(S.get('glow', 0.0)); dome = None
    if gw > 0:
        da = np.angle(np.exp(1j * (az - glow_az))).astype(F32)
        dome = np.exp(-(da / 0.9) ** 2) * np.exp(-np.maximum(el, 0) / 0.2)
        col = col + DOME * (dome * gw * 0.035)[..., None]
    dens_out = None
    if cloud > 0:
        hc = 1600.0
        with np.errstate(divide='ignore', invalid='ignore'):
            tt = np.where(dy > 0.004, (hc - cam.eye[1]) / dy, np.inf)
        ok = np.isfinite(tt)
        if ok.any():
            tt = np.where(ok, tt, 0).astype(F32)
            ct = float(S.get('cloud_t', 0.0))
            X = (cam.eye[0] + dx * tt + ct * 6.0).astype(F32); Z = (cam.eye[2] + dz * tt + ct * 2.0).astype(F32)
            n1 = sample(fbm_tex(512, 2.6, 11), X, Z, 512 / 14000.0)
            n2 = sample(fbm_tex(512, 2.0, 12), X, Z, 512 / 5200.0)
            n = n1 * 0.72 + n2 * 0.28
            thr = 0.62 - 0.30 * cloud
            dens = np.clip((n - thr) / 0.16, 0, 1) * np.clip(1 - tt / 60000.0, 0, 1) * ok
            dens *= np.clip(dy / 0.03, 0, 1)
            thin = np.clip(1 - (n - thr) / 0.22, 0, 1)
            lit_d = (sunf ** 2.4 * thin ** 1.5 * dusk)[..., None]
            ccol = CL_BODY * (0.25 + 0.75 * dusk) * (0.5 + 0.5 * hor[..., None]) + (CL_LIT * (0.8 - 0.3 * sunf[..., None]) + CL_GOLD * 0.5 * sunf[..., None]) * lit_d * (0.35 + 0.9 * hor[..., None])
            ccol = ccol * (dusk > 0.02) + CL_NIGHT * (1 - min(1.0, dusk * 3))
            if dome is not None:
                ccol = ccol + DOME * (dome * gw * 0.22 * (0.35 + 0.65 * thin) + 0.012 * gw)[..., None]
            a = dens[..., None] * (0.92 if not mir else 0.8)
            col = col * (1 - a) + ccol * a
            dens_out = dens.astype(F32)
    hz = float(S.get('haze', 0.0))
    if hz: col = col * (1 - hz * hor[..., None] * 0.6) + hn * (hz * hor * 0.6)[..., None]
    return col.astype(F32), dens_out

@lru_cache(2)
def _star_dirs(n=2600, seed=5):
    r = np.random.default_rng(seed)
    v = r.normal(0, 1, (n, 3)).astype(F32); v[:, 1] = np.abs(v[:, 1]); v /= np.linalg.norm(v, axis=1, keepdims=True)
    mag = r.uniform(0, 1, n).astype(F32) ** 6
    return v, mag

def _stars(cv, amt, mir, cloud):
    v, mag = _star_dirs()
    cam = cv.cam
    P = cam.eye + v * 1e5
    if mir: P = cam.eye + v * np.array([1, -1, 1], F32) * 1e5
    x, y, z = cam.project(P)
    ok = (z > 0) & (x >= 0) & (x < cv.W - 1) & (y >= 0) & (y < cv.H - 1) & (v[:, 1] > 0.05)
    x, y, m = x[ok], y[ok], mag[ok]
    xi, yi = x.astype(int), y.astype(int)
    sky = ~np.isfinite(cv.dep[yi, xi])
    w = (0.02 + 0.5 * m) * amt * sky
    if cloud is not None: w = w * (1 - cloud[yi, xi])
    E._splat_points(cv.emis, x, y, w.astype(F32), np.broadcast_to(np.array([0.85, 0.9, 1.0], F32), (len(x), 3)))

# ---------------------------------------------------------------- steam plumes (billowing puffs)
@E.byte_lru(240 * 2 ** 20)
def puff_sprite(rq, seed):
    """a soft, eroded ball of steam rq px in radius: (alpha, vertical shading coordinate -1 top .. +1 bottom)."""
    R = max(1.5, rq); n = int(R * 2.7) + 3
    yy, xx = np.mgrid[0:n, 0:n].astype(F32); c = n / 2
    dx, dy = (xx - c) / R, (yy - c) / R
    d2 = dx * dx + dy * dy
    base = np.clip(1 - d2, 0, 1) ** 0.9
    tex = fbm_tex(256, 1.9, 23 + seed % 5)
    nz = sample(tex, xx * (14.0 / R) + seed * 53, yy * (14.0 / R) + seed * 17, 1.0)
    nz2 = sample(fbm_tex(256, 1.4, 29), xx * (34.0 / R) + seed * 7, yy * (34.0 / R), 1.0)
    a = np.clip(base * 1.7 - (1 - nz) * 0.75 - (1 - nz2) * 0.2, 0, 1)
    a = a ** 1.1
    return a.astype(F32), np.clip(dy, -1, 1).astype(F32)

def plume(cv, base, t, height=260.0, r0=9.0, r1=60.0, wind=(6.0, 0.0), S=None, gain=1.0, seed=0, scale=1.0,
          lit_from_below=0.6, dusk_col=None, rate=1.0):
    """a column of steam from `base` (world): puffs emitted every dt seconds rise, slow, swell and drift downwind.
    Each puff is lit warm/cold from below by the facility and from above by the sky (pink at dusk)."""
    S = S or {}
    cam = cv.cam
    base = np.asarray(base, F32)
    dusk = float(S.get('dusk', 0.0))
    dt = 1.7 / rate; life = 95.0; npuff = int(life / dt)
    k0 = int(math.floor(t / dt))
    fogc = np.asarray(S.get('fog_col', hexc('101826')), F32); pf = float(S.get('plume_fog', 0.0))
    pink = (dusk_col if dusk_col is not None else (hexc('ff7d8a') * 0.75 + hexc('ffb27a') * 0.25))
    items = []
    for j in range(npuff):
        k = k0 - j; age = t - k * dt
        u = age / life
        if u < 0 or u > 1: continue
        h1 = E.hash01(seed, k, 1); h2 = E.hash01(seed, k, 2); h3 = E.hash01(seed, k, 3)
        y = height * (1 - (1 - u) ** 1.7)
        rad = r0 + (r1 - r0) * u ** 0.75 * (0.75 + 0.5 * h1)
        P = base + np.array([wind[0] * age * 0.5 * (0.3 + u) + (h2 - 0.5) * rad * 0.8, y, wind[1] * age * 0.5 * (0.3 + u) + (h3 - 0.5) * rad * 0.6], F32)
        items.append((P, rad, u, k, h1))
    if not items: return
    Ps = np.array([it[0] for it in items], F32)
    x, yy, z = cam.project(Ps)
    order = np.argsort(-z)           # far first
    for i in order:
        P, rad, u, k, h1 = items[i]
        if z[i] < 2: continue
        rp = rad * cam.fpx / z[i]
        if rp < 1.0: continue
        if x[i] < -rp * 2 or x[i] > cv.W + rp * 2 or yy[i] < -rp * 2 or yy[i] > cv.H + rp * 2: continue
        q = 1.08 ** round(math.log(max(rp, 1.5)) / math.log(1.08))
        a, sy = puff_sprite(round(min(q, 420.0), 2), int(k % 7))
        sc = rp / q
        if abs(sc - 1) > 0.02:
            a = cv2.resize(a, None, fx=sc, fy=sc, interpolation=cv2.INTER_LINEAR); sy = cv2.resize(sy, None, fx=sc, fy=sc, interpolation=cv2.INTER_LINEAR)
        n = a.shape[0]; X0 = int(x[i] - n / 2); Y0 = int(yy[i] - n / 2)
        xa, ya, xb, yb = max(0, X0), max(0, Y0), min(cv.W, X0 + n), min(cv.H, Y0 + n)
        if xb <= xa or yb <= ya: continue
        aa = a[ya - Y0:yb - Y0, xa - X0:xb - X0]; ss = sy[ya - Y0:yb - Y0, xa - X0:xb - X0]
        aa = aa * (cv.dep[ya:yb, xa:xb] > z[i] * 0.97)
        fade = min(1.0, u * 12) * (1 - u) ** 0.6 * gain * (0.85 + 0.3 * h1)
        aa = aa * fade
        if not aa.any(): continue
        hfrac = float(np.clip(P[1] / height, 0, 1))
        below = (0.5 + 0.5 * ss) * lit_from_below * math.exp(-hfrac * 3.0)
        above = (0.5 - 0.5 * ss)
        c_n = hexc('8796a4') * 0.06 + hexc('cfe4f0') * 0.9 * below[..., None] + hexc('5c6c7c') * 0.06 * above[..., None]
        c_d = hexc('3d3050') * 0.28 + pink * (0.12 + 0.55 * above + 0.15 * (1 - hfrac))[..., None] * (0.45 + 0.55 * hfrac) + hexc('ffd0b0') * 0.08 * below[..., None]
        col = c_n * (1 - dusk) + c_d * dusk
        if pf: col = col * (1 - pf) + fogc * pf
        reg = cv.img[ya:yb, xa:xb]; A = aa[..., None]
        reg *= (1 - A); reg += col * A
        cv.emis[ya:yb, xa:xb] *= (1 - A * 0.9)
