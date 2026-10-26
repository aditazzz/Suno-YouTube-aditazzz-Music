"""The Drive — world engine. A pseudo-3D coast highway seen through the windshield: sky and sea that follow the time
of day, a road that curves and dips, water that comes in over everything in the choruses, and roadside sprites
(signs, lights, cars, the pier) placed by distance along the track. Everything is float32 RGB in [0, 1]."""
import math, os
import numpy as np, cv2
from studio import core as C
from studio.core import hexc, sstep, clamp, lerp

RW = 2.2          # road half-width (world units)
CAMH = 1.15       # camera height above the road
PPU = 110.0       # sprite pixels per world unit at base scale
FOG_Z = 90.0


# ------------------------------------------------------------------ time of day palettes
# tod: 0 golden hour (4:59 PM) · 0.25 sunset · 0.5 night · 0.75 pre-dawn · 1.0 dawn
_KEYS = [0.0, 0.25, 0.5, 0.75, 1.0]
_PAL = {
    'sky_top': ['4c84c4', '2a2358', '04071a', '0d1a3f', '4f78b4'],
    'sky_mid': ['b9d2ea', 'd45a52', '0a1434', '2a4079', 'e8a59a'],
    'sky_hor': ['ffe1b0', 'ffb070', '19264d', '7f90b8', 'ffe2c4'],
    'sun':     ['fff0c8', 'ff8c4a', 'e8ecff', '000000', 'ffd2a0'],
    'sea_far': ['3f93b4', '2e4a7c', '0b1d3c', '1c3a62', '4b93b4'],
    'sea_near': ['2d7596', '26406e', '0d2448', '203f66', '3a7f9e'],
    'sand':    ['e4cfa2', 'c49a7a', '2a2e48', '4a5272', 'd9c2a2'],
    'land':    ['b58c5a', '7a5a62', '141a30', '2a3350', 'a88c6e'],
    'hill1':   ['8e7a86', '5a3f60', '0d1230', '20294a', '8a7f9e'],
    'hill2':   ['a9929a', '7a5272', '131a3a', '2c365a', 'a498ae'],
    'road':    ['5e5a68', '4a4454', '202230', '2b2d3b', '5b5866'],
    'shoulder': ['cfc2a2', 'a08a78', '3a3e52', '4e5470', 'c8bca4'],
    'line':    ['fff3c8', 'ffd8a8', 'dde4ff', 'd8dcf0', 'fff0d8'],
    'amb':     ['ffffff', 'ffb894', '4a5c9a', '7a88b8', 'ffd8c8'],
    'haze':    ['ffe7c4', 'ffb98a', '243260', '7a8ab4', 'ffe6cc'],
}
_PALV = {k: np.array([hexc(h) for h in v], np.float32) for k, v in _PAL.items()}


def pal(name, tod):
    v = _PALV[name]; tod = clamp(tod)
    return np.array([np.interp(tod, _KEYS, v[:, c]) for c in range(3)], np.float32)


def night(tod): return float(np.interp(tod, [0.25, 0.42, 0.62, 0.85], [0, 1, 1, 0]))


# ------------------------------------------------------------------ the track
class Track:
    """Curvature and elevation along the distance d. xoff(d) is the lateral offset of the road center (double integral
    of the curvature); heading(d) its first derivative. Hills come from elev(d)."""
    def __init__(self, length=6000.0, step=0.5, seed=7):
        self.step = step; n = int(length / step) + 2
        d = np.arange(n) * step; self.d = d
        r = np.random.default_rng(seed)
        curv = np.zeros(n, np.float32)
        # gentle S-bends every ~120 units, with a few long sweeping coastal curves
        for _ in range(80):
            c = r.uniform(60, length - 60); w = r.uniform(25, 70); a = r.uniform(-0.0045, 0.0045)
            curv += a * np.exp(-((d - c) / w) ** 2)
        for c, w, a in ((900, 160, 0.004), (1500, 200, -0.0035), (2600, 220, 0.0032), (3800, 180, -0.004)):
            curv += a * np.exp(-((d - c) / w) ** 2)
        head = np.cumsum(curv) * step
        self.x = np.cumsum(head) * step
        self.h = head
        self.curv = curv

    def xoff(self, d): return np.interp(d, self.d, self.x)
    def heading(self, d): return np.interp(d, self.d, self.h)


# ------------------------------------------------------------------ view
class View:
    def __init__(self, W, H, D, track, bob=0.0, pitch=0.0, flip=1.0, f=None, pan=0.0):
        self.W, self.H, self.D, self.tr = W, H, D, track
        self.pan = pan            # horizontal sweep of the whole world (the U-turn)
        self.vert = H > W
        self.f = f or min(W, H) * 1.0
        self.yh = (H * (0.46 if not self.vert else 0.42)) + bob + pitch
        self.flip = flip          # -1 after the U-turn: the ocean swaps sides
        self.x0 = track.xoff(D); self.h0 = track.heading(D)

    def cx(self, z):
        """Screen x of the road center at distance z ahead (array ok)."""
        z = np.maximum(z, 1e-3)
        return self.W / 2 + self.pan + self.flip * (self.tr.xoff(self.D + z) - self.x0 - self.h0 * z) * self.f / z

    def project(self, z, lat=0.0, h=0.0):
        """World point z ahead, lat right of center, h above the road -> (x, y, scale)."""
        z = max(z, 1e-3)
        return (self.cx(z) + self.flip * lat * self.f / z, self.yh + (CAMH - h) * self.f / z, self.f / z / PPU)


_G = {}
def grid(W, H):
    if (W, H) not in _G:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.random.default_rng(3)
        _G[(W, H)] = dict(xx=xx, yy=yy, noise=r.random((H, W)).astype(np.float32),
                          stars=(r.random((H, W)) > 0.9985).astype(np.float32) * r.random((H, W)).astype(np.float32))
    return _G[(W, H)]


# ------------------------------------------------------------------ sky
def sky(img, V, t, S):
    """Sky at quarter resolution (it is all soft gradients), stars at full resolution."""
    W, H = V.W, V.H; tod = S['tod']
    q = 4; w, h = W // q, H // q
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32) * q
    top, mid, hor = pal('sky_top', tod), pal('sky_mid', tod), pal('sky_hor', tod)
    v = np.clip(yy / max(1.0, V.yh), 0, 1)[..., None]
    a = np.clip(v / 0.55, 0, 1); b = np.clip((v - 0.55) / 0.45, 0, 1)
    sk = np.where(v < 0.55, top * (1 - a) + mid * a, mid * (1 - b) + hor * b)
    nt = night(tod)
    sx, sy, sr, scol, sglow = sun_pos(V, tod)
    if scol is not None:
        d = np.hypot(xx - sx, yy - sy)
        disc = np.clip((sr - d) / (sr * 0.06), 0, 1)
        glow = np.exp(-(d / (sr * 6.0)) ** 1.3) * sglow
        sk += glow[..., None] * scol * 0.55
        sk = sk * (1 - disc[..., None]) + disc[..., None] * (scol * 1.05)
    cl = S.get('clouds', 0.5)
    if cl > 0.01:
        band = cloud_band(w, h, V.yh / q, S.get('cloud_drift', 0.0))
        ccol = hor * 0.55 + pal('sun', tod) * 0.45 if nt < 0.5 else hor * 1.1
        sk += band[..., None] * ccol * 0.22 * cl
    hz = np.exp(-((yy - V.yh) / (H * 0.07)) ** 2)[..., None] * (yy[..., None] <= V.yh + 1)
    sk += hz * pal('haze', tod) * 0.25
    img[:] = cv2.resize(sk, (W, H), interpolation=cv2.INTER_LINEAR)
    if nt > 0.01:
        G = grid(W, H)
        st = G['stars'] * nt * (0.6 + 0.4 * np.sin(t * 3 + G['noise'] * 40))
        vv = np.clip(G['yy'] / max(1.0, V.yh), 0, 1)
        img += (st * np.clip(1 - vv * 1.3, 0, 1))[..., None] * 1.1
    return img


_CL = {}
def cloud_band(W, H, yh, drift):
    k = (W, H)
    if k not in _CL:
        r = np.random.default_rng(21); n = r.random((H // 4, W // 2)).astype(np.float32)
        cb = cv2.GaussianBlur(n, (0, 0), W / 160); cb = (cb - cb.mean()) / (cb.std() + 1e-6)
        _CL[k] = cb
    cb = _CL[(W, H)]
    sh = int(drift) % cb.shape[1]
    cb = np.roll(cb, sh, axis=1)
    big = cv2.resize(cb, (W, H))
    v = np.arange(H, dtype=np.float32)[:, None] / max(1.0, yh)
    return np.clip((big - 0.35) * 0.9, 0, 1) * np.clip(1 - np.abs(v - 0.62) / 0.3, 0, 1)


_GLOW = {}
def glow_sprite(r, px=160):
    k = int(r)
    if k not in _GLOW:
        yy, xx = np.mgrid[0:px, 0:px].astype(np.float32); d = np.hypot(xx - px / 2, yy - px / 2) / (px / 2) * 2.2
        _GLOW[k] = np.exp(-d ** 2).astype(np.float32)
    return _GLOW[k]


def add_glow(img, cx, cy, r, col, amt):
    if amt <= 0.003 or r < 1: return
    g = glow_sprite(r); px = max(4, int(r * 4.4)); g = cv2.resize(g, (px, px))
    H, W = img.shape[:2]; x0, y0 = int(cx - px / 2), int(cy - px / 2)
    X0, Y0, X1, Y1 = max(0, x0), max(0, y0), min(W, x0 + px), min(H, y0 + px)
    if X1 <= X0 or Y1 <= Y0: return
    img[Y0:Y1, X0:X1] += g[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0][..., None] * col * amt


def sun_pos(V, tod):
    W, H = V.W, V.H
    nt = night(tod)
    if 0.3 < tod < 0.72:   # moon
        k = (tod - 0.3) / 0.42
        return W * (0.78 - 0.4 * k), V.yh - H * (0.26 + 0.08 * math.sin(k * math.pi)), H * 0.028, hexc('e9eeff'), 0.35 * nt
    if tod <= 0.3:
        k = tod / 0.3   # golden hour: sun sliding down to the horizon
        y = V.yh - H * (0.17 * (1 - k) + 0.005)
        return W * (0.62 - 0.22 * k), y, H * (0.05 + 0.04 * k), pal('sun', tod), 1.0 - 0.3 * k
    k = (tod - 0.72) / 0.28   # dawn: sun rising on the other side
    return W * (0.34 + 0.2 * k), V.yh - H * (0.01 + 0.12 * k), H * (0.075 - 0.03 * k), pal('sun', tod), 0.7 + 0.3 * k


# ------------------------------------------------------------------ hills (behind the land side)
def hills(img, V, t, S):
    W, H = V.W, V.H; tod = S['tod']
    q = 4; w, h = W // q, int(V.yh) // q + 2
    if h < 3: return img
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32) * q
    x = np.arange(w, dtype=np.float32) * q
    shift = -V.h0 * V.f * V.flip - V.pan
    hor = pal('sky_hor', tod)
    lay = img[:h * q].copy() if False else None
    sk = cv2.resize(img[:h * q], (w, h), interpolation=cv2.INTER_AREA)
    for li, (amp, freq, col, par, ph) in enumerate(((0.16, 1.7, pal('hill1', tod), 0.25, 1.3), (0.10, 2.9, pal('hill2', tod), 0.5, 4.1))):
        u = (x + shift * par + V.D * 0.08 * par * V.flip) / W
        prof = (np.sin(u * freq * 6.28 + ph) * 0.5 + 0.5) ** 1.6 * 0.6 + (np.sin(u * freq * 2.1 * 6.28 + ph * 2.2) * 0.5 + 0.5) * 0.4
        side = np.clip((x / W - 0.3) / 0.45, 0, 1) if V.flip > 0 else np.clip((0.7 - x / W) / 0.45, 0, 1)
        hgt = prof * amp * H * side ** 0.8
        m = np.clip((yy - (V.yh - hgt[None, :])) / (2.0 * q), 0, 1) * (yy <= V.yh + 1)
        c = col * 0.7 + hor * 0.3 * (1 + li * 0.6)
        sk *= (1 - m[..., None]); sk += m[..., None] * c
    big = cv2.resize(sk, (w * q, h * q), interpolation=cv2.INTER_LINEAR)
    img[:h * q, :w * q] = big
    return img


# ------------------------------------------------------------------ ground: road, shoulder, sand, sea
def ground(img, V, t, S):
    W, H = V.W, V.H; G = grid(W, H); xx = G['xx']; yy = G['yy']; tod = S['tod']
    y0 = int(V.yh) + 1
    if y0 >= H: return img
    rows = np.arange(y0, H, dtype=np.float32)
    z = CAMH * V.f / (rows - V.yh)                       # distance per row
    cx = V.cx(z); rw = RW * V.f / z
    Z = z[:, None]; CX = cx[:, None]; RWv = rw[:, None]
    u = (xx[y0:] - CX) / RWv * V.flip                    # u < 0: ocean side (before the U-turn)
    au = np.abs(u)
    dd = V.D + Z
    fog = (1 - np.exp(-Z / FOG_Z))[..., None]
    hor = pal('haze', tod)
    road, shoulder, line, sand, land = (pal(k, tod) for k in ('road', 'shoulder', 'line', 'sand', 'land'))
    sea_far, sea_near = pal('sea_far', tod), pal('sea_near', tod)
    nz = G['noise'][y0:]
    base = np.empty((H - y0, W, 3), np.float32)
    # land side
    base[:] = land * (0.9 + 0.2 * nz)[..., None]
    # ocean side: sand strip then water
    sea_mix = np.clip(Z / 60, 0, 1)
    sea = (sea_near * (1 - sea_mix) + sea_far * sea_mix)[:, None, :]
    shimmer = 0.5 + 0.5 * np.sin(dd * 1.1 - t * 1.6 + np.sin(xx[y0:] * 0.011 + t * 0.7) * 2.0)
    crest = np.clip((shimmer - 0.93) * 14, 0, 1) * np.clip(1 - Z / 120, 0, 1)
    seacol = sea * (0.92 + 0.16 * shimmer)[..., None] + crest[..., None] * (pal('line', tod) * 0.6 + hor * 0.4) * 0.6
    sea_edge = -1.75 - 3.2 * S.get('lowtide', 0.0)      # low tide: the beach widens and the seabed shows
    ocean_m = (u < sea_edge)[..., None]
    sand_m = ((u >= sea_edge) & (u < -1.1))[..., None]
    base = np.where(ocean_m, seacol, base)
    base = np.where(sand_m, sand * (0.9 + 0.2 * nz)[..., None], base)
    # shoulder, road, lines
    sh_m = ((au >= 1.0) & (au < 1.1))[..., None]
    base = np.where(sh_m, shoulder * (0.9 + 0.2 * nz)[..., None], base)
    road_m = (au < 1.0)[..., None]
    rcol = road * (0.94 + 0.12 * nz)[..., None]
    base = np.where(road_m, rcol, base)
    edge = ((au > 0.90) & (au < 0.945))[..., None]
    base = np.where(edge, line * 0.9, base)
    dash_on = ((dd // 2.6) % 2 == 0)
    cl = ((au < 0.024) & dash_on)[..., None] if not S.get('center_solid') else (au < 0.024)[..., None]
    base = np.where(cl, line, base)
    # road chevrons pointing at the driver ("ten thousand rows all pointing at me")
    chev = S.get('chevrons', 0.0)
    if chev > 0.01:
        ph = (dd * 0.9 - t * 6.0) % 4.0
        cm = (np.abs(ph - 2.0 - au * 1.2) < 0.22) & (au < 0.85)
        base = np.where(cm[..., None], line * 0.9 * chev + base * (1 - chev), base)
    # pipeline progress bar on the center line (verse 3)
    pb = S.get('pipeline')
    if pb is not None:
        frac, lbl = pb
        bar = (au < 0.07)[..., None]
        fill = (bar & ((Z < frac * 60)[..., None]))
        base = np.where(bar, hexc('2a2f3a'), base); base = np.where(fill, hexc('3ddc84'), base)
    # night: headlights + tail of the beam
    nt = night(tod) * S.get('headlights', 1.0)
    if nt > 0.01:
        beam = np.exp(-(Z / 34.0) ** 2) * np.exp(-(u / 1.6) ** 2) * nt
        base *= (0.72 + 0.28 * (1 - nt)); base += beam[..., None] * hexc('ffe9b0') * 0.62
    # sun path on the water
    sx, sy, sr, scol, sg = sun_pos(V, tod)
    if scol is not None and sg > 0:
        path = np.exp(-((xx[y0:] - sx) / (W * 0.035 + Z * 0.0)) ** 2) * np.clip(1 - Z / 140, 0, 1) * (ocean_m[..., 0]) * (0.5 + 0.5 * shimmer)
        base += path[..., None] * scol * 0.45 * sg
    # fog with distance
    base = base * (1 - fog) + hor * fog
    img[y0:] = base
    # subtle horizon line of the sea
    return img


# ------------------------------------------------------------------ flood: the tide comes in over the road
def flood(img, V, t, S):
    """hw: water height above the road (0..0.95 of CAMH). Everything below the horizon turns to water, the road
    showing through where it's shallow."""
    hw = S.get('flood', 0.0)
    if hw <= 0.003: return img
    W, H = V.W, V.H; G = grid(W, H); xx = G['xx']; tod = S['tod']
    y0 = int(V.yh) + 1
    rows = np.arange(y0, H, dtype=np.float32)
    z = CAMH * V.f / (rows - V.yh); Z = z[:, None]
    dd = V.D + Z
    sea_far, sea_near = pal('sea_far', tod), pal('sea_near', tod)
    sea = (sea_near * (1 - np.clip(Z / 50, 0, 1)) + sea_far * np.clip(Z / 50, 0, 1))[:, None, :]
    w1 = np.sin(dd * 0.8 - t * 2.4 + np.sin(xx[y0:] * 0.013 + t) * 1.6)
    w2 = np.sin(dd * 2.3 + t * 3.1 + xx[y0:] * 0.004)
    shimmer = 0.5 + 0.25 * w1 + 0.25 * w2
    a = clamp(hw / 0.9); alpha = (0.35 + 0.55 * a) * np.clip(Z / 2.5, 0.35, 1)
    crest = np.clip((shimmer - 0.86) * 9, 0, 1) * np.clip(1 - Z / 90, 0, 1) * (0.4 + 0.6 * a)
    col = sea * (0.85 + 0.3 * shimmer)[..., None]
    reg = img[y0:]
    reg *= (1 - alpha[..., None]); reg += alpha[..., None] * col
    reg += crest[..., None] * (pal('line', tod) * 0.5 + pal('haze', tod) * 0.5) * 0.5
    # the water's own horizon is a touch higher than the road's: a bright rim
    rim = np.exp(-((rows - V.yh) / (H * 0.012)) ** 2)[:, None, None] * a
    reg += rim * pal('haze', tod) * 0.35
    return img


# ------------------------------------------------------------------ sprites
_RS = {}
def _resized(rgba, w, h):
    if w * h > 40000:   # big (near) sprites change size every frame: resize them fresh instead of filling memory
        return cv2.resize(rgba, (w, h), interpolation=cv2.INTER_AREA if w < rgba.shape[1] else cv2.INTER_LINEAR)
    k = (id(rgba), w, h)
    if k not in _RS:
        if len(_RS) > 400: _RS.clear()
        _RS[k] = cv2.resize(rgba, (w, h), interpolation=cv2.INTER_AREA if w < rgba.shape[1] else cv2.INTER_LINEAR)
    return _RS[k]


def alpha_blit(img, rgba, x, y, scale=1.0, anchor='bc', tint=None, op=1.0, clip_y=None, fog=0.0, haze=None):
    """rgba float32 (h, w, 4). anchor 'bc' = bottom-center at (x, y). clip_y: don't draw rows below this screen y.
    fog: mix the sprite's color toward `haze` by this much (distance haze)."""
    if op <= 0.005 or scale <= 0.002: return
    h0, w0 = rgba.shape[:2]
    w, h = max(1, int(round(w0 * scale))), max(1, int(round(h0 * scale)))
    if w < 2 or h < 2: return
    sp = _resized(rgba, w, h)
    if anchor == 'bc': x0, y0 = int(round(x - w / 2)), int(round(y - h))
    elif anchor == 'c': x0, y0 = int(round(x - w / 2)), int(round(y - h / 2))
    else: x0, y0 = int(round(x)), int(round(y))
    H, W = img.shape[:2]
    X0, Y0, X1, Y1 = max(0, x0), max(0, y0), min(W, x0 + w), min(H, y0 + h)
    if clip_y is not None: Y1 = min(Y1, int(clip_y))
    if X1 <= X0 or Y1 <= Y0: return
    s = sp[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]
    a = s[..., 3:4] * op; c = s[..., :3]
    if tint is not None: c = c * tint
    if fog > 0.003 and haze is not None: c = c * (1 - fog) + haze * fog
    reg = img[Y0:Y1, X0:X1]; reg *= (1 - a); reg += a * c


class RoadObject:
    """A sprite standing on the road at distance d (world), lat units right of the center, drawn h units tall."""
    def __init__(self, d, lat, rgba, h, glow=None, emissive=0.0, t0=-1e9, t1=1e9, name=''):
        self.d, self.lat, self.rgba, self.h = d, lat, rgba, h
        self.glow, self.emissive, self.t0, self.t1, self.name = glow, emissive, t0, t1, name


def draw_objects(img, V, t, S, objs):
    W, H = V.W, V.H; tod = S['tod']; amb = pal('amb', tod); haze = pal('haze', tod)
    hw = S.get('flood', 0.0)
    vis = []
    for o in objs:
        if not (o.t0 <= t <= o.t1): continue
        z = (o.d - V.D)
        if 2.2 < z < 260: vis.append((z, o))
    vis.sort(key=lambda p: -p[0])
    for z, o in vis:
        x, y, s = V.project(z, o.lat, 0.0)
        if x < -W or x > 2 * W: continue
        sc = s * (o.h * PPU / o.rgba.shape[0])
        fog = 1 - math.exp(-z / FOG_Z)
        tint = amb * (1 - o.emissive) + o.emissive
        clip = None
        if hw > 0.003:
            clip = V.yh + (CAMH - hw) * V.f / z
        # fog: blend toward haze by drawing a haze-colored copy on top with the fog alpha
        near = sstep(2.2, 3.6, z)   # fade out as it passes the window
        alpha_blit(img, o.rgba, x, y, sc, 'bc', tint=tint, clip_y=clip, fog=fog * (1 - o.emissive * 0.7), haze=haze, op=near)
        if o.glow is not None and (night(tod) > 0.2 or o.emissive > 0):
            gx, gy = x, y - o.rgba.shape[0] * sc * o.glow[0]
            r = o.rgba.shape[1] * sc * o.glow[1]
            add_glow(img, gx, gy, r, o.glow[3], o.glow[2] * (1 - fog) * max(night(tod), o.emissive * 0.5))
    return img


def motion_streaks(img, V, amt):
    """Speed lines near the frame edges (whoosh)."""
    if amt <= 0.01: return img
    W, H = V.W, V.H; G = grid(W, H)
    d = np.hypot((G['xx'] - W / 2) / (W / 2), (G['yy'] - V.yh) / (H / 2))
    k = np.clip((d - 0.55) / 0.5, 0, 1) * amt
    blur = cv2.GaussianBlur(img, (0, 0), sigmaX=W * 0.012 * amt + 0.1, sigmaY=0.1 + H * 0.004 * amt)
    img[:] = img * (1 - k[..., None]) + blur * k[..., None]
    return img
