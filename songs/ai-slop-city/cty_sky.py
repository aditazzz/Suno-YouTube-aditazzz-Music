"""Time of day for the city: sun path, palettes, and the illustrated sky (gradient, sun, clouds, stars, moon).

World axes: x = north (screen right in the main view), y = up, z = west (into the main view). The main camera looks west
at the Feed Tower, so the sun rises behind the camera, crosses to the left (south) and sets behind the towers.
"""
import math
import numpy as np, cv2
from cty_eng import F32, hexc, mix, clamp, sstep, nrm

SUNRISE, SUNSET, NOON = 6.0, 19.8, 12.9


def sun(h):
    """Unit vector toward the sun, elevation (deg), azimuth (deg from north, clockwise)."""
    hh = h % 24
    u = (hh - SUNRISE) / (SUNSET - SUNRISE)            # 0 at sunrise, 1 at sunset
    az = 88 + 184 * u                                  # east -> south -> west
    el = 60 * math.sin(math.pi * u) if 0 <= u <= 1 else -12 * math.sin(math.pi * min(1.0, abs(u if u < 0 else u - 1) * 2.6))
    if 0 <= u <= 1: el = 60 * math.sin(math.pi * u) ** 0.9
    a, e = math.radians(az), math.radians(el)
    L = np.array([math.cos(a) * math.cos(e), math.sin(e), -math.sin(a) * math.cos(e)])
    return L, el, az


# ------------------------------------------------------------------ palettes (keyed by hour)
def P(**k): return k

KEYS = [
    (0.0, P(z='070a1a', m='111633', hz='2a2550', lo='3a2a4a', sun='000000', amb='2a3460', fog='1a1d3a', fogd=0.0045, ink='0b0b16',
            cl='2a2c4a', cs='15172c', glass='141a33', glass2='222a4a', stars=0.55, lit=0.32, lamp=1.0, haze='3b2d55', city=0.9)),
    (4.6, P(z='0a0f26', m='1b2246', hz='3a3463', lo='4a3a5e', sun='000000', amb='34406e', fog='252a4c', fogd=0.004, ink='0d0e1c',
            cl='34365a', cs='1b1d36', glass='18203d', glass2='2b3560', stars=0.35, lit=0.24, lamp=1.0, haze='4a3a66', city=0.7)),
    (5.6, P(z='1c2552', m='4a4a85', hz='c58aa6', lo='f2b39a', sun='ff9a6a', amb='6a6aa6', fog='8a7aa8', fogd=0.0034, ink='1a1830',
            cl='e6a3b0', cs='6a5f96', glass='3a4478', glass2='c48aa0', stars=0.06, lit=0.14, lamp=0.6, haze='d99aa0', city=0.3)),
    (6.4, P(z='3a5a9a', m='8aa0d0', hz='f6c6a6', lo='ffd9a8', sun='ffb47a', amb='7a7cb8', fog='c6b0c4', fogd=0.0036, ink='1d1b33',
            cl='ffe0c8', cs='9a8ab8', glass='5a6ea8', glass2='f0c0a8', stars=0.0, lit=0.05, lamp=0.0, haze='f0c0b0', city=0.0)),
    (8.5, P(z='3f78c4', m='7fb0e0', hz='dbe8f0', lo='eef0ea', sun='fff0d8', amb='8a9cc8', fog='c9d8ea', fogd=0.0032, ink='1c1d30',
            cl='ffffff', cs='b4c4e0', glass='4f7cb8', glass2='b8d4ee', stars=0.0, lit=0.0, lamp=0.0, haze='e4ecf2', city=0.0)),
    (12.9, P(z='2f6fc4', m='6ca8e6', hz='d6e8f4', lo='eef4f6', sun='fffaf0', amb='8ca2cc', fog='cfe0f0', fogd=0.003, ink='1c1e30',
             cl='ffffff', cs='bccbe4', glass='4a7ec4', glass2='c4dcf2', stars=0.0, lit=0.0, lamp=0.0, haze='e8f0f6', city=0.0)),
    (16.2, P(z='3c74c0', m='7aaedc', hz='e8e4dc', lo='f6e8d4', sun='ffeccc', amb='909cc6', fog='d6d6dc', fogd=0.0032, ink='1d1c2e',
             cl='fff8ec', cs='b8b8d4', glass='4f78b4', glass2='d8d4dc', stars=0.0, lit=0.0, lamp=0.0, haze='eee4d8', city=0.0)),
    (18.4, P(z='4a5c9c', m='9a98c0', hz='f6c08a', lo='ffd49a', sun='ffb860', amb='7a74aa', fog='d8b49c', fogd=0.0036, ink='241a2e',
             cl='ffd6a0', cs='9a7fa8', glass='5a5c96', glass2='f4b67c', stars=0.0, lit=0.04, lamp=0.0, haze='f2c294', city=0.0)),
    (19.5, P(z='2e3270', m='7a5a98', hz='f08a6a', lo='ffa660', sun='ff8a4a', amb='76649e', fog='b67a88', fogd=0.0034, ink='231629',
             cl='ff9a7a', cs='6a4a7e', glass='443c7a', glass2='e8806a', stars=0.0, lit=0.12, lamp=0.4, haze='e8866e', city=0.2)),
    (20.3, P(z='141c46', m='303a78', hz='8a5a8a', lo='c27088', sun='000000', amb='3e467a', fog='4a4670', fogd=0.0038, ink='121228',
             cl='6a5a8a', cs='2a2a52', glass='1c2450', glass2='4a4a80', stars=0.12, lit=0.3, lamp=1.0, haze='7a5280', city=0.7)),
    (21.6, P(z='080b1e', m='121838', hz='2c2852', lo='3e2c50', sun='000000', amb='2c3664', fog='1c1f3e', fogd=0.0044, ink='0b0b18',
             cl='2c2e4e', cs='16182e', glass='141a36', glass2='232b4e', stars=0.5, lit=0.36, lamp=1.0, haze='3c2e58', city=0.95)),
    (24.0, P(z='070a1a', m='111633', hz='2a2550', lo='3a2a4a', sun='000000', amb='2a3460', fog='1a1d3a', fogd=0.0045, ink='0b0b16',
             cl='2a2c4a', cs='15172c', glass='141a33', glass2='222a4a', stars=0.55, lit=0.32, lamp=1.0, haze='3b2d55', city=0.9)),
]
_NUM = ('fogd', 'stars', 'lit', 'lamp', 'city')


def palette(h):
    hh = h % 24
    for i in range(len(KEYS) - 1):
        h0, a = KEYS[i]; h1, b = KEYS[i + 1]
        if h0 <= hh <= h1:
            t = (hh - h0) / (h1 - h0); t = t * t * (3 - 2 * t)
            out = {}
            for k in a:
                if k in _NUM: out[k] = a[k] * (1 - t) + b[k] * t
                else: out[k] = mix(hexc(a[k]), hexc(b[k]), t)
            return out
    return palette(0.0)


def blackout_palette(p, k):
    """Power cut: the city glow dies, the sky goes deep and the stars come out."""
    if k <= 0: return p
    q = dict(p)
    for name, col in (('z', '050813'), ('m', '0b1330'), ('hz', '1a2554'), ('lo', '1e2650'), ('haze', '141c40'), ('fog', '0c1026'),
                      ('amb', '141a3a'), ('cl', '0c0f22'), ('cs', '06081a'), ('glass', '060914'), ('glass2', '0a0e20')):
        q[name] = mix(p[name], hexc(col), k)
    q['stars'] = p['stars'] * (1 - k) + 1.0 * k
    q['lit'] = p['lit'] * (1 - k); q['lamp'] = p['lamp'] * (1 - k); q['city'] = p['city'] * (1 - k)
    q['milky'] = k
    return q


def neon_palette(p, k):
    """Reboot: the city comes back brighter than before, every surface a screen."""
    if k <= 0: return p
    q = dict(p)
    for name, col in (('z', '12062a'), ('m', '2a0c4a'), ('hz', '8a1a6a'), ('lo', 'c42a7a'), ('haze', 'a0287a'), ('fog', '4a1450'),
                      ('amb', '6a3a9a'), ('cl', '7a2a7a'), ('cs', '2a0c3a')):
        q[name] = mix(p[name], hexc(col), k)
    q['lamp'] = max(p['lamp'], k); q['city'] = max(p['city'], k)
    return q


# ------------------------------------------------------------------ sky dome textures (built once)
def _vnoise(h, w, cells_y, cells_x, rng):
    g = rng.random((cells_y + 3, cells_x + 3)).astype(F32)
    g[:, -3:] = g[:, :3]     # wrap horizontally
    big = cv2.resize(g, (int(math.ceil((cells_x + 3) * w / cells_x)), int(math.ceil((cells_y + 3) * h / cells_y))), interpolation=cv2.INTER_CUBIC)
    return big[:h, :w]


_DOME = {}
def dome():
    """Cloud density panorama: azimuth 0..360 over 4096 px, elevation 0..50 deg over 640 px (row 0 = 50 deg)."""
    if 'c' in _DOME: return _DOME
    rng = np.random.default_rng(11)
    Hh, Ww = 640, 4096
    n = np.zeros((Hh, Ww), F32); amp = 1.0; tot = 0
    for cy, cx in ((4, 16), (8, 40), (16, 96), (32, 220), (64, 512)):
        n += amp * _vnoise(Hh, Ww, cy, cx, rng); tot += amp; amp *= 0.55
    n /= tot
    el = np.linspace(50, 0, Hh, dtype=F32)[:, None]
    # cumulus banks low on the horizon, thin streaks higher up
    bank = n - (0.56 + 0.10 * np.clip((el - 4) / 30, 0, 1))
    dens = np.clip(bank * 9, 0, 1)
    # flatten the bottoms (illustrated cumulus): density fades quickly below each cloud's base
    shade = np.clip(cv2.GaussianBlur(dens, (0, 0), 6)[::1] - np.roll(cv2.GaussianBlur(dens, (0, 0), 6), -10, 0), 0, 1)
    top = np.clip(dens - np.roll(dens, 6, 0), 0, 1)
    _DOME['c'] = dens; _DOME['sh'] = np.clip(1 - shade * 2.5, 0, 1); _DOME['top'] = top
    # milky way (for the blackout), on its own panorama covering the whole sky (elevation 0..90 over MW_H rows):
    # a broad glow, mottled star clouds, a brighter bulge, and a dark dust rift down the middle
    Hm = MW_H
    elm = np.linspace(90, 0, Hm, dtype=F32)[:, None]
    m1 = _vnoise(Hm, Ww, 10, 64, rng); m2 = _vnoise(Hm, Ww, 40, 256, rng); m3 = _vnoise(Hm, Ww, 100, 640, rng)
    az = np.linspace(0, 2 * math.pi, Ww, dtype=F32)[None, :]
    off = elm - mw_el(az)
    glow = np.exp(-(off / 9.5) ** 2) * 0.75 + np.exp(-(off / 4.0) ** 2) * 0.35
    da = (az - math.radians(MW_CORE_AZ) + math.pi) % (2 * math.pi) - math.pi
    core = np.exp(-(da / 0.7) ** 2)
    clouds = np.clip(0.8 + 0.55 * (m2 - 0.5) + 0.22 * (m3 - 0.5), 0, 1.6)
    rift = np.exp(-((off - 0.6 - 3.2 * (m1 - 0.5)) / (1.1 + 0.9 * m2)) ** 2) * np.clip(0.6 + 1.0 * (m2 - 0.5), 0, 1)
    rift = np.maximum(rift, 0.55 * np.exp(-((off + 3.5 - 4.0 * (m2 - 0.5)) / 0.8) ** 2) * np.clip(m1 * 1.4 - 0.3, 0, 1))
    _DOME['mw'] = np.clip(glow * (0.42 + 0.58 * core) * clouds * (1 - 0.82 * rift), 0, 1.5).astype(F32)
    _DOME['mwc'] = (core * np.exp(-(off / 7.0) ** 2)).astype(F32)
    # stars: a uniform sprinkle plus a dense, mostly faint population hugging the band
    rs = np.random.default_rng(5)
    n0, n1 = 3200, 9000
    v0 = rs.standard_normal((n0, 3)); v0[:, 1] = np.abs(v0[:, 1]); v0 /= np.linalg.norm(v0, axis=1, keepdims=True)
    a1 = rs.random(n1) * 2 * math.pi
    e1 = mw_el(a1) + rs.standard_normal(n1) * (3.0 + 4.0 * rs.random(n1))
    e1 = np.radians(np.clip(e1, 0.5, 89.0))
    v1 = np.stack([np.cos(e1) * np.sin(a1), np.sin(e1), -np.cos(e1) * np.cos(a1)], 1)
    _DOME['stars'] = np.concatenate([v0, v1])
    _DOME['mag'] = np.concatenate([rs.random(n0) ** 3.2, rs.random(n1) ** 5.0])
    _DOME['band'] = np.concatenate([np.zeros(n0, bool), np.ones(n1, bool)])
    _DOME['tw'] = rs.random(n0 + n1) * 6.28
    warm = rs.random(n0 + n1) ** 2.5
    _DOME['scol'] = (hexc('dfe6ff')[None] * (1 - warm[:, None]) + hexc('ffe2bc')[None] * warm[:, None]).astype(F32)
    return _DOME


MW_CORE_AZ = 160.0      # sky azimuth (deg) of the bright bulge: the open sky up-left of the tower in the blackout view
MW_H = 720               # rows of the milky-way panorama (elevation 90 -> 0)


def mw_el(az):
    """Elevation (deg) of the milky way's centre line at sky azimuth az (radians). In the blackout view (looking ~138 deg)
    it climbs diagonally from behind the right-hand towers (~25 deg) to the open sky up-left (~48 deg)."""
    return 36 + 20 * np.sin(az - 2.44)


def render_sky(cam, pal, t, h, cloud_drift=0.0, step=2, sun_vec=None):
    """Sky image (H, W, 3) float, plus a mask of the sun disk (for rays) and the sun's screen position."""
    W, H = cam.W, cam.H
    d = cam.ray_dirs(step)
    el = np.degrees(np.arcsin(np.clip(d[..., 1], -1, 1)))
    stops = [(-8, pal['lo'] * 0.85), (0, pal['lo']), (3.5, pal['hz']), (16, pal['m']), (55, pal['z']), (90, pal['z'])]
    xs = np.array([s for s, _ in stops], F32)
    sky = np.stack([np.interp(el, xs, np.array([c[i] for _, c in stops], F32)) for i in range(3)], -1).astype(F32)
    L, sel, saz = sun(h) if sun_vec is None else sun_vec
    L = np.asarray(L, F32)
    cosang = np.clip((d * L).sum(-1), -1, 1)
    sunmask = np.zeros(el.shape, F32)
    if pal['sun'].max() > 0.02 and sel > -4:
        ang = np.degrees(np.arccos(cosang))
        halo = np.exp(-ang / 9.0) * 0.5 + np.exp(-ang / 30.0) * 0.25
        vis = clamp((sel + 3) / 4)
        sky += halo[..., None] * pal['sun'] * 0.55 * vis
        disk = np.clip((1.6 - ang) / 0.25, 0, 1) * vis
        sunmask = np.maximum(disk, np.exp(-ang / 2.4) * 0.6 * vis)
        sky = sky * (1 - disk[..., None]) + disk[..., None] * mix(pal['sun'], np.ones(3, F32), 0.65)
    # clouds
    D = dome()
    az = (np.degrees(np.arctan2(d[..., 0], -d[..., 2])) + cloud_drift) % 360
    py = ((50 - np.clip(el, 0, 50)) / 50 * 639).astype(F32)
    px = (az / 360 * 4095).astype(F32)
    dens = cv2.remap(D['c'], px, py, cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
    shd = cv2.remap(D['sh'], px, py, cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
    top = cv2.remap(D['top'], px, py, cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
    above = np.clip(el / 1.5, 0, 1)
    dens = dens * above * np.clip(1 - (el - 38) / 12, 0, 1) * (1 - 0.92 * pal.get('milky', 0.0))
    near_sun = np.clip(cosang, 0, 1) ** 6
    ccol = pal['cs'][None, None] * (1 - shd[..., None]) + pal['cl'][None, None] * shd[..., None]
    ccol = ccol + top[..., None] * 0.25 * (pal['cl'] - pal['cs']) + near_sun[..., None] * pal['sun'] * 0.35
    sky = sky * (1 - dens[..., None]) + ccol * dens[..., None]
    # stars + milky way
    if pal['stars'] > 0.01:
        mw = pal.get('milky', 0.0)
        if mw > 0.01:
            # the milky way is fixed to the sky (like the stars), not carried along by the cloud drift
            px0 = ((np.degrees(np.arctan2(d[..., 0], -d[..., 2])) % 360) / 360 * 4095).astype(F32)
            pym = ((90 - np.clip(el, 0, 90)) / 90 * (MW_H - 1)).astype(F32)
            band = cv2.remap(D['mw'], px0, pym, cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
            cw = cv2.remap(D['mwc'], px0, pym, cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
            col = hexc('9fb0ec')[None, None] * (1 - cw[..., None]) + hexc('f2dcc0')[None, None] * cw[..., None]
            sky += band[..., None] * col * 0.72 * mw * above[..., None]
    if step > 1:
        sky = cv2.resize(sky, (W, H), interpolation=cv2.INTER_LINEAR)
        sunmask = cv2.resize(sunmask, (W, H), interpolation=cv2.INTER_LINEAR)
    if pal['stars'] > 0.01:
        sky = _stars(sky, cam, pal['stars'], t, pal.get('milky', 0.0))
    sp, sz = cam.proj(L[None] * 1e5)
    return sky, sunmask, (sp[0], float(sz[0]))


def _stars(sky, cam, amt, t, milky):
    """Stars as light, not pixels: a sub-pixel (bilinear) core for every star, a soft halo on the bright ones and a faint
    four-point glint on the brightest few; sizes scale with the frame so 4K and 540p look alike."""
    D = dome()
    v = D['stars']; mag = D['mag']
    Hh, Ww = sky.shape[:2]; ts = Hh / 1080
    Pc = v @ cam.R.T
    ok = Pc[:, 2] > 0.05
    S = cam.proj_c(Pc)
    keep = ok & (S[:, 0] >= 1) & (S[:, 0] < Ww - 2) & (S[:, 1] >= 1) & (S[:, 1] < Hh - 2) & (v[:, 1] > 0.02)
    # without the blackout only the brighter part of the sprinkle shows; the band population needs a dark sky
    thr = 1 - (0.12 + 0.88 * milky) * min(1, amt * 1.2)
    keep &= (mag > thr * 0.96) & (~D['band'] | (milky > 0.05))
    if not keep.any(): return sky
    S = S[keep]; m = mag[keep]; tw = D['tw'][keep]; col = D['scol'][keep]
    bandk = np.where(D['band'][keep], milky, 1.0)
    br = (0.3 + 0.7 * m) * amt * (0.82 + 0.18 * np.sin(t * 2.6 + tw)) * (1.0 + 0.6 * milky) * bandk
    x = S[:, 0] - 0.5; y = S[:, 1] - 0.5
    x0 = np.floor(x).astype(int); y0 = np.floor(y).astype(int); fx = (x - x0)[:, None]; fy = (y - y0)[:, None]
    e = br[:, None] * col * max(1.0, ts) ** 0.5
    for dx, dy, w in ((0, 0, (1 - fx) * (1 - fy)), (1, 0, fx * (1 - fy)), (0, 1, (1 - fx) * fy), (1, 1, fx * fy)):
        np.add.at(sky, (y0 + dy, x0 + dx), e * w)
    big = m > 0.45
    if big.any():
        halo = np.zeros((Hh, Ww, 3), F32)
        np.add.at(halo, (np.clip(y0[big], 0, Hh - 1), np.clip(x0[big], 0, Ww - 1)), (br[big] * (m[big] - 0.45) * 6.0)[:, None] * col[big])
        sky += cv2.GaussianBlur(halo, (0, 0), 1.1 * ts + 0.3) * (2.0 * ts * ts + 0.5)
    top = np.argsort(-(br * m))[:14]
    if len(top) and milky > 0.05:
        gl = np.zeros((Hh, Ww), np.uint8)
        for i in top:
            L_ = (5 + 9 * m[i]) * ts; cx_, cy_ = S[i, 0], S[i, 1]; a = int(min(255, 255 * br[i] * 0.55 * milky))
            for (ux, uy) in ((1, 0), (0, 1)):
                cv2.line(gl, (int((cx_ - ux * L_) * 16), int((cy_ - uy * L_) * 16)), (int((cx_ + ux * L_) * 16), int((cy_ + uy * L_) * 16)),
                         a, 1, cv2.LINE_AA, shift=4)
        g = cv2.GaussianBlur(gl.astype(F32) / 255, (0, 0), 0.6 * ts)
        sky += g[..., None] * hexc('e8ecff') * 0.5
    return sky


def warm_palette(p, k):
    """The last morning: warmer, kinder light than the first one."""
    if k <= 0: return p
    q = dict(p)
    for name, col in (('z', '5f86c8'), ('m', 'a9b8e0'), ('hz', 'ffd6a0'), ('lo', 'ffe0b0'), ('sun', 'ffc674'), ('amb', '9a8cb4'),
                      ('fog', 'e8c8b0'), ('cl', 'fff0d8'), ('cs', 'c8a8b8'), ('glass2', 'f8d0a8'), ('haze', 'ffd8b0')):
        q[name] = mix(p[name], hexc(col), k)
    q['sun'] = q['sun'] * (1 + 0.15 * k)
    return q


def drain_palette(p, k):
    """'You handed me your gold': the sunset's colour drains out of the sky into her shadow."""
    if k <= 0: return p
    q = dict(p)
    for name in ('hz', 'lo', 'sun', 'cl', 'haze', 'glass2', 'm'):
        c = p[name]; g = c.mean()
        q[name] = mix(c, np.array([g, g, g * 1.08], F32) * 0.85, k)
    return q
