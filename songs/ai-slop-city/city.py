"""The city: a stone-and-glass tower over a plaza at golden hour (also at night and at dawn), rendered as a real
perspective scene so the camera can move: dolly, crane, push in.

Everything is a projection of world geometry (metres; X right, Y up, Z away from us). Faces are drawn by inverse
mapping each pixel to the surface it sees, so patterns, light, reflections and HER SHADOW are all computed per pixel.

Her shadow comes from a point light behind her that can creep closer: far away it behaves like the low sun (a long thin
shadow across the plaza); right behind her the shadow balloons and climbs the tower. It stays attached to her feet and
bends where the plaza meets the facade, because it is a real projection.
"""
import math
from functools import lru_cache
import numpy as np, cv2
from studio.core import hexc, clamp, sstep, lerp

F32 = np.float32
AA = cv2.LINE_AA


def nrm(v):
    v = np.asarray(v, F32); return v / np.linalg.norm(v)


SUN = nrm((-0.46, 0.085, -0.88))          # golden hour: low, behind the camera, to the left
SUNCOL = hexc('ffbf80'); AMB = hexc('8f95cc'); AMB_N = hexc('3a3f78')
STONE = hexc('ead8c2'); PAVE = hexc('d9c3aa'); BRONZE = hexc('3a3140')
SKY_LOW = hexc('ffd2a6'); SKY_MID = hexc('e7b2c2'); SKY_HI = hexc('9db0dd'); SKY_TOP = hexc('6e88c8')
HAZE = hexc('f0cbbf'); SCREEN = hexc('f2f6ff'); HOTPINK = hexc('ff5f9e')


class Cam:
    """Pinhole camera looking along +Z, with lens shift (verticals stay vertical, like an architecture lens)."""
    def __init__(s, W, H, f, X, Y, Z, sx=0.0, sy=0.0):
        s.W, s.H, s.f = W, H, float(f)
        s.X, s.Y, s.Z = float(X), float(Y), float(Z)
        s.cx = W / 2 + sx; s.cy = H / 2 + sy
        s.ts = min(W, H) / 1080

    def P(s, X, Y, Z):
        d = max(1e-3, Z - s.Z)
        return (s.cx + s.f * (X - s.X) / d, s.cy - s.f * (Y - s.Y) / d)

    def xy(s, x0=0, y0=0, x1=None, y1=None):
        x1 = s.W if x1 is None else x1; y1 = s.H if y1 is None else y1
        return np.arange(x0, x1, dtype=F32)[None, :], np.arange(y0, y1, dtype=F32)[:, None]

    def on_ground(s, xs, ys):
        dy = np.maximum(ys - s.cy, 0.25)
        d = s.f * s.Y / dy
        return s.X + (xs - s.cx) * d / s.f, s.Z + d * np.ones_like(xs)

    def on_z(s, xs, ys, Zp):
        d = Zp - s.Z
        return s.X + (xs - s.cx) * d / s.f + 0 * ys, s.Y - (ys - s.cy) * d / s.f + 0 * xs

    def on_x(s, xs, ys, Xp):
        d = s.f * (Xp - s.X) / np.where(np.abs(xs - s.cx) < 1e-3, 1e-3, xs - s.cx)
        return s.Y - (ys - s.cy) * d / s.f, s.Z + d


def hash2(i, j):
    return (np.sin(i * 12.9898 + j * 78.233) * 43758.5453) % 1.0


def fbm(h, w, seed, octaves=5, base=4.0, persist=0.55):
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w), F32); amp = 1.0; tot = 0.0; m = max(h, w)
    for o in range(octaves):
        f = base * (2 ** o)
        g = rng.normal(0, 1, (max(3, int(f * h / m) + 3), max(3, int(f * w / m) + 3))).astype(F32)
        out += cv2.resize(g, (w, h), interpolation=cv2.INTER_CUBIC) * amp
        tot += amp; amp *= persist
    return out / tot


# ---------------------------------------------------------------- sky
def elevation(cam, xs, ys):
    return np.arctan2((cam.cy - ys) / cam.f, np.sqrt(1 + ((xs - cam.cx) / cam.f) ** 2))


@lru_cache(maxsize=16)
def _clouds(W, H):
    c = fbm(H // 4, W // 4, 77, 6, 3.0, 0.55)
    c = cv2.resize(c, (W * 2, H), interpolation=cv2.INTER_CUBIC)
    return c


def sky(cam, t, mode='eve'):
    W, H = cam.W, cam.H
    xs, ys = cam.xy()
    el = np.degrees(elevation(cam, xs, ys)) * np.ones((H, 1), F32)
    if mode == 'eve':
        k1 = np.clip(el / 9.0, 0, 1)[..., None]; k2 = np.clip((el - 9) / 30.0, 0, 1)[..., None]; k3 = np.clip((el - 39) / 40.0, 0, 1)[..., None]
        img = SKY_LOW * (1 - k1) + SKY_MID * k1
        img = img * (1 - k2) + SKY_HI * k2
        img = img * (1 - k3) + SKY_TOP * k3
        # high thin clouds, lit pink and gold from below
        c = _clouds(W, H)
        off = int((t * 6 * cam.ts) % W)
        cl = c[:, off:off + W] if off + W <= c.shape[1] else np.roll(c, -off, axis=1)[:, :W]
        band = np.exp(-((el - 22) / 11.0) ** 2)
        cm = np.clip((cl - 0.18) * 2.4, 0, 1) * band
        img = img * (1 - 0.55 * cm[..., None]) + (hexc('ffd7c2') * 0.6 + hexc('ffb0a0') * 0.4) * 0.55 * cm[..., None]
    elif mode == 'night':
        k = np.clip(el / 50.0, 0, 1)[..., None]
        img = hexc('3a2f63') * (1 - k) + hexc('0d1230') * k
    else:  # dawn, sun ahead
        k = np.clip(el / 35.0, 0, 1)[..., None]
        img = hexc('ffd6a0') * (1 - k) ** 1.4 + hexc('86a8de') * (1 - (1 - k) ** 1.4)
    return img.astype(F32)


# ---------------------------------------------------------------- her shadow
def shadow_sample(Wx, Wy, Wz, light, her, M, sc, directional=False):
    """For world points W, how much of her silhouette lies between W and the light. M: her mask (square, feet at the
    bottom centre), sc: mask px per metre, her = (x, z) of her feet."""
    S = M.shape[0]
    hx, hz = her
    if directional:
        d = light
        t = (hz - Wz) / d[2]
        bx = Wx + t * d[0]; by = Wy + t * d[1]
        valid = (t > 0).astype(F32)
    else:
        Lx, Ly, Lz = light
        den = Wz - Lz
        den = np.where(np.abs(den) < 1e-3, 1e-3, den)
        t = (hz - Lz) / den
        bx = Lx + t * (Wx - Lx); by = Ly + t * (Wy - Ly)
        valid = ((t > 0) & (t < 1)).astype(F32)
    mu = (S / 2 + (bx - hx) * sc).astype(F32)
    mv = (S - S * 0.04 - by * sc).astype(F32)
    out = cv2.remap(M, mu, mv, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    return out * valid


def light_pos(her, g):
    """g = 0: far along the low sun; g = 1: right behind her (the shadow is enormous)."""
    D = math.exp(lerp(math.log(5000.0), math.log(1.65), g))
    hx, hz = her
    return (hx + SUN[0] * D, 1.0 + SUN[1] * D, hz + SUN[2] * D)


# ---------------------------------------------------------------- the plaza
def ground(img, cam, t, shadow_fn, lamps=(), mode='eve', refl=None):
    """Big limestone slabs (anti-aliased joints), lit by the low sun; her shadow and the lamp shadows on it."""
    W, H = cam.W, cam.H
    y0 = int(max(0, math.ceil(cam.cy + 0.5)))
    if y0 >= H: return
    xs, ys = cam.xy(0, y0)
    X, Z = cam.on_ground(xs, ys)
    tile = 1.5
    fx = (X / tile) % 1.0; fz = (Z / tile) % 1.0
    dx = np.minimum(fx, 1 - fx) * tile * cam.f / (Z - cam.Z)
    dz = np.minimum(fz, 1 - fz) * tile * cam.f * cam.Y / ((Z - cam.Z) ** 2)
    joint = np.clip(1.3 - dx, 0, 1) + np.clip(1.3 - dz, 0, 1)
    joint = np.clip(joint, 0, 1) * np.exp(-(Z - cam.Z) / 70.0)
    slab = 0.93 + 0.07 * hash2(np.floor(X / tile), np.floor(Z / tile))
    alb = PAVE * slab[..., None] * (1 - 0.22 * joint[..., None])
    sh = np.zeros_like(X)
    if shadow_fn is not None: sh = np.maximum(sh, shadow_fn(X, np.zeros_like(X), Z))
    if mode != 'night' and lamps:
        sh = np.maximum(sh, lamp_shadows(cam, lamps, X, Z))
    if mode == 'eve':
        lit = alb * (SUNCOL * 0.62 + AMB * 0.30)
        dark = alb * AMB * 0.36
        col = lit * (1 - sh[..., None]) + dark * sh[..., None]
    elif mode == 'night':
        col = alb * AMB_N * 0.30
    else:
        col = alb * (hexc('ffcf98') * 0.55 + hexc('9fb2e0') * 0.30) * (1 - 0.6 * sh[..., None])
    # polished stone: a soft reflection of what stands on it (rendered with a mirrored camera)
    if refl is not None:
        dist = (Z - cam.Z)
        fres = np.clip(0.06 + 0.22 * (1 - np.exp(-dist / 60.0)), 0, 0.3)[..., None]
        col = col * (1 - fres) + refl[y0:] * fres
    fog = np.clip(1 - np.exp(-(Z - cam.Z) / 380.0), 0, 1)[..., None]
    col = col * (1 - fog) + (HAZE if mode == 'eve' else (hexc('2a2550') if mode == 'night' else hexc('ffe0b8'))) * fog
    img[y0:] = col
    return X, Z, y0


def lamp_shadows(cam, lamps, X, Z, sun=SUN):
    sh = np.zeros_like(X)
    for (x, z, h) in lamps:
        ex = x - sun[0] / sun[1] * h; ez = z - sun[2] / sun[1] * h
        vx, vz = ex - x, ez - z; ln2 = vx * vx + vz * vz
        u = np.clip(((X - x) * vx + (Z - z) * vz) / ln2, 0, 1)
        d = np.sqrt((X - (x + u * vx)) ** 2 + (Z - (z + u * vz)) ** 2)
        wpx = d * cam.f / np.maximum(Z - cam.Z, 0.1)
        w0 = 0.07 * cam.f / np.maximum(Z - cam.Z, 0.1)
        sh = np.maximum(sh, np.clip(1.0 + w0 - wpx, 0, 1) * (u < 0.995) * 0.9)
    return sh


def lamps_draw(img, cam, lamps, mode='eve', t=0.0):
    H, W = img.shape[:2]
    for (x, z, h) in sorted(lamps, key=lambda q: -q[1]):
        if z - cam.Z < 0.5: continue
        b = cam.P(x, 0, z); tp = cam.P(x, h, z)
        k = cam.f / (z - cam.Z)
        m = np.zeros((H, W), F32)
        cv2.line(m, (int(b[0] * 4), int(b[1] * 4)), (int(tp[0] * 4), int(tp[1] * 4)), 1.0, max(2, int(0.13 * k)), AA, shift=2)
        hd = cam.P(x + 0.35, h + 0.05, z)
        cv2.line(m, (int(tp[0] * 4), int(tp[1] * 4)), (int(hd[0] * 4), int(hd[1] * 4)), 1.0, max(2, int(0.10 * k)), AA, shift=2)
        cv2.ellipse(m, (int(hd[0] * 4), int((hd[1] + 0.12 * k) * 4)), (max(2, int(0.22 * k * 4)), max(2, int(0.09 * k * 4))), 0, 0, 360, 1.0, -1, AA, shift=2)
        sh = cv2.GaussianBlur(m, (0, 0), 0.6)
        img[:] = img * (1 - sh[..., None]) + sh[..., None] * BRONZE
        # the sun catches the left edge of the pole
        rim = np.clip(sh - np.roll(sh, max(1, int(0.04 * k)), axis=1), 0, 1)
        img += rim[..., None] * SUNCOL * (0.55 if mode == 'eve' else 0.0)
        if mode == 'night':
            g = np.zeros((H, W), F32); cv2.circle(g, (int(hd[0]), int(hd[1] + 0.15 * k)), max(2, int(0.16 * k)), 1.0, -1, AA)
            img += (cv2.GaussianBlur(g, (0, 0), 0.5 * k) * 2.0 + g)[..., None] * hexc('ffd39a')


# ---------------------------------------------------------------- the tower
def reflection(el_deg, X, jitter):
    """What the glass reflects: the sky behind us (toward the sun, warm and bright low down), with a far skyline."""
    e = el_deg + jitter
    k1 = np.clip(e / 7.0, 0, 1)[..., None]; k2 = np.clip((e - 7) / 25.0, 0, 1)[..., None]
    c = hexc('ffd9a8') * (1 - k1) + hexc('f0b7b8') * k1
    c = c * (1 - k2) + hexc('a9b6e2') * k2
    sky_line = 2.5 + 2.2 * (0.5 + 0.5 * np.sin(X * 0.09) * np.sin(X * 0.031 + 1.0)) + 1.2 * ((np.floor(X / 9.0) % 3) == 0)
    bld = (e < sky_line).astype(F32)[..., None]
    return c * (1 - bld) + hexc('9a7f9f') * bld


def tower(img, cam, T, t, mode='eve', shadow_fn=None, feed=0.0, display=None, crowd=None, lights_off=0.0, mirror=False):
    """The tower's front face: limestone grid with deep-set glass. Returns the screen box drawn."""
    W, H = cam.W, cam.H
    x0, x1, zf, ht = T
    if zf - cam.Z < 1: return None
    a = cam.P(x0, ht, zf); b = cam.P(x1, 0.0, zf)
    X0, X1 = int(max(0, math.floor(a[0]))), int(min(W, math.ceil(b[0])))
    if not mirror:
        Y0, Y1 = int(max(0, math.floor(a[1]))), int(min(H, math.ceil(b[1])))
    else:
        Y0, Y1 = int(max(0, math.floor(b[1]))), int(min(H, math.ceil(a[1])))
    if X1 <= X0 or Y1 <= Y0: return None
    xs, ys = cam.xy(X0, Y0, X1, Y1)
    X, Y = cam.on_z(xs, ys, zf)
    if mirror: Y = -Y
    u = X - x0
    bay, flh = 3.0, 4.2
    i = np.floor(u / bay); j = np.floor(Y / flh)
    fu = (u / bay) % 1.0; fv = (Y / flh) % 1.0
    col_w, slab_h = 0.20, 0.19
    winu = (fu > col_w / 2) & (fu < 1 - col_w / 2)
    winv = (fv > slab_h) & (fv < 0.985)
    win = (winu & winv).astype(F32)
    d = zf - cam.Z
    pxu = bay * cam.f / d; pxv = flh * cam.f / d
    # anti-alias the window edges a little
    eu = np.minimum(np.abs(fu - col_w / 2), np.abs(fu - (1 - col_w / 2))) * pxu
    ev = np.minimum(np.abs(fv - slab_h), np.abs(fv - 0.985)) * pxv
    edge = np.clip(1 - np.minimum(eu, ev), 0, 1) * 0.5
    winf = np.clip(win - edge * (2 * win - 1), 0, 1)
    h = hash2(i, j)
    sh = shadow_fn(X, Y, np.full_like(X, zf)) if shadow_fn is not None else np.zeros_like(X)
    # stone: lit by the low sun from the left (front faces take most of it)
    stone = STONE * (0.95 + 0.05 * hash2(i + 11, j))[..., None]
    lam = float(max(0.0, -SUN[2]))
    el = np.degrees(np.arctan2(Y - cam.Y, d))
    if mode == 'eve':
        st_lit = stone * (SUNCOL * 1.02 * lam + AMB * 0.25)
        st_dark = stone * AMB * 0.47
        stone_c = st_lit * (1 - sh[..., None]) + st_dark * sh[..., None]
        # deep-set windows: the left reveal throws a sliver of shade onto the glass
        recess = 0.42
        sl = recess * abs(SUN[0] / SUN[2]) / bay
        st = recess * abs(SUN[1] / SUN[2]) / flh
        selfsh = (((fu - col_w / 2) < sl) | ((0.985 - fv) < st)).astype(F32) * (1 - sh)
        F = np.clip(0.42 + 0.5 * (1 - np.cos(np.radians(np.abs(el)))) * 3, 0, 0.92)[..., None]
        refl = reflection(el, X, (hash2(i + 5, j + 2) - 0.5) * 2.2)
        lit_floor = (hash2(j + 3, np.floor(i / 4)) < 0.45).astype(F32)
        interior = hexc('3a2f3c') * (1 - lit_floor[..., None]) + hexc('6b5550') * lit_floor[..., None]
        ceiling = ((fv > 0.86) & (fv < 0.95)).astype(F32) * lit_floor
        interior = interior + ceiling[..., None] * hexc('ffd9a6') * 0.55
        glass = refl * F + interior * (1 - F)
        glass = glass * (1 - 0.18 * selfsh[..., None]) * (1 - 0.12 * sh[..., None])
    elif mode == 'night':
        stone_c = stone * AMB_N * 0.28
        lit_floor = (hash2(j + 3, np.floor(i / 3)) < 0.55).astype(F32)
        glass = hexc('1b1d3a') * (1 - lit_floor[..., None]) + hexc('f5c98f') * 0.55 * lit_floor[..., None]
    else:  # dawn: backlit, the stone in shade, glass reflecting the bright sky
        stone_c = stone * hexc('b9b4d6') * 0.55
        glass = hexc('d8c9e0') * 0.8
    col = stone_c * (1 - winf[..., None]) + glass * winf[..., None]
    # windows inside the shadow light up with posts: the feed lives in the shadow
    if feed > 0 or (mode == 'night' and crowd is None and display is None):
        if mode == 'eve': on = (h < feed).astype(F32) * winf * np.clip(sh * 1.4, 0, 1)
        else: on = (h < 0.9).astype(F32) * winf * (1 - np.clip(sh * 1.4, 0, 1)) * (feed if feed > 0 else 1.0)
        pu = (fu - col_w / 2) / (1 - col_w); pv = (fv - slab_h) / (0.985 - slab_h)
        pic = ((pv > 0.42) & (pv < 0.88) & (pu > 0.12) & (pu < 0.88)).astype(F32)
        lines = (((pv > 0.25) & (pv < 0.30) & (pu > 0.12) & (pu < 0.72)) | ((pv > 0.15) & (pv < 0.19) & (pu > 0.12) & (pu < 0.50))).astype(F32)
        hu, hv = (pu - 0.80) / 0.065, (pv - 0.20) / 0.06
        heart = ((hu ** 2 + hv ** 2) < 1).astype(F32)
        tint = np.stack([0.80 + 0.2 * hash2(i + 3, j), 0.72 + 0.2 * hash2(i, j + 7), 0.92 + 0.08 * h], -1)
        scr = SCREEN * (1 - pic[..., None]) + (hexc('ffb3cf') * 0.5 + hexc('b8c4ff') * 0.5) * tint * pic[..., None]
        scr = scr * (1 - lines[..., None] * 0.55) + hexc('8f98c8') * lines[..., None] * 0.55
        scr = scr * (1 - heart[..., None]) + HOTPINK * heart[..., None]
        flick = 0.88 + 0.12 * np.sin(t * 6.0 + h * 40)[..., None]
        col = col * (1 - on[..., None]) + scr * flick * 1.08 * on[..., None]
    if crowd is not None and crowd[0] > 0.01:
        amt, nod = crowd
        pu = (fu - col_w / 2) / (1 - col_w); pv = (fv - slab_h) / (0.985 - slab_h)
        sel = (h < amt).astype(F32) * winf
        cu = (pu - 0.5) / 0.16; cvv = (pv - 0.62 + 0.05 * nod) / 0.13
        headm = ((cu ** 2 + cvv ** 2) < 1).astype(F32)
        bod = ((np.abs((pu - 0.5) / 0.34) < 0.55 + 0.45 * np.clip((0.52 - pv) / 0.4, 0, 1)) & (pv < 0.52 - 0.05 * nod)).astype(F32)
        fig = np.clip(headm + bod, 0, 1) * sel
        back = (hexc('fbf3ea') if mode == 'eve' else hexc('e8eeff'))
        col = col * (1 - sel[..., None]) + back * sel[..., None]
        col = col * (1 - fig[..., None]) + hexc('2b2442') * fig[..., None]
    if display is not None:
        bm, (c0, r0) = display
        rows, cols = bm.shape
        ii = (i - c0).astype(np.int32); jj = (r0 + rows - 1 - j).astype(np.int32)
        inside = (ii >= 0) & (ii < cols) & (jj >= 0) & (jj < rows)
        v = np.zeros_like(X); v[inside] = bm[jj[inside], ii[inside]]
        px = v * winf
        col = col * (1 - (winf * inside)[..., None] * 0.45)
        col = col * (1 - px[..., None]) + (hexc('ffffff') * 0.75 + hexc('ffb3d1') * 0.25) * 1.25 * px[..., None]
    if lights_off > 0:
        floors = ht / flh
        dark = (j >= floors * (1 - lights_off)).astype(F32) * winf
        col = col * (1 - dark[..., None] * 0.92) + hexc('161933') * dark[..., None] * 0.92
    # aerial haze up the tower
    dist = np.sqrt(d * d + (Y - cam.Y) ** 2)
    fog = np.clip(1 - np.exp(-dist / (520.0 if mode != 'night' else 900.0)), 0, 0.6)[..., None]
    hz = HAZE if mode == 'eve' else (hexc('2a2550') if mode == 'night' else hexc('ffe3c2'))
    col = col * (1 - fog) + hz * fog
    ax = np.clip(xs - a[0] + 0.5, 0, 1) * np.ones_like(Y)
    sub = img[Y0:Y1, X0:X1]
    sub[:] = sub * (1 - ax[..., None]) + col * ax[..., None]
    return (X0, Y0, X1, Y1)


def boxes(img, cam, B, mode='eve'):
    """Background buildings: front faces lit, street-facing sides in shade, window grids, haze with distance."""
    H, W = img.shape[:2]
    for (x0, x1, z0, z1, h, k) in sorted(B, key=lambda b: -b[2]):
        if z0 - cam.Z < 2: continue
        fog = 1 - math.exp(-(z0 - cam.Z) / 260.0)
        hz = HAZE if mode == 'eve' else (hexc('2a2550') if mode == 'night' else hexc('ffe3c2'))
        tone = [hexc('f2c9a2'), hexc('e9bfa8'), hexc('f6d2b0'), hexc('dcb7b4'), hexc('efc4a0'), hexc('e2c0b8')][k % 6]
        if mode == 'eve': litc, shc = tone * (SUNCOL * 0.95 + AMB * 0.2), tone * AMB * 0.62
        elif mode == 'night': litc, shc = hexc('1d2142'), hexc('171a36')
        else: litc, shc = hexc('b8afd3') * 0.75, hexc('a49cc9') * 0.7
        litc = litc * (1 - fog) + hz * fog; shc = shc * (1 - fog) + hz * fog
        sides = []
        if x1 < cam.X: sides.append((x1, shc))
        if x0 > cam.X: sides.append((x0, shc))
        for (xx, c) in sides:
            q = [cam.P(xx, 0, z0), cam.P(xx, h, z0), cam.P(xx, h, z1), cam.P(xx, 0, z1)]
            m = np.zeros((H, W), F32)
            cv2.fillPoly(m, [np.round(np.array(q) * 4).astype(np.int32)], 1.0, AA, shift=2)
            img[:] = img * (1 - m[..., None]) + m[..., None] * c
            # window bands on the side, reflecting the sky
            nb = int(h / 4.2)
            if 4.2 * cam.f / (z0 - cam.Z) > 4:
                g = np.zeros((H, W), F32)
                for r in range(nb):
                    p0 = cam.P(xx, r * 4.2 + 1.2, z0); p1 = cam.P(xx, r * 4.2 + 1.2, z1)
                    p2 = cam.P(xx, r * 4.2 + 3.8, z1); p3 = cam.P(xx, r * 4.2 + 3.8, z0)
                    cv2.fillPoly(g, [np.round(np.array([p0, p1, p2, p3]) * 4).astype(np.int32)], 1.0, AA, shift=2)
                gc = hexc('b9b9e0') if mode == 'eve' else hexc('2a2f5c')
                img[:] = img * (1 - (g * m)[..., None] * 0.55) + (g * m)[..., None] * (gc * (1 - fog) + hz * fog) * 0.55
        p0 = cam.P(x0, h, z0); p1 = cam.P(x1, 0, z0)
        m2 = np.zeros((H, W), F32)
        cv2.rectangle(m2, (int(round(p0[0])), int(round(p0[1]))), (int(round(p1[0])), int(round(p1[1]))), 1.0, -1)
        img[:] = img * (1 - m2[..., None]) + m2[..., None] * litc
        flp = 4.2 * cam.f / (z0 - cam.Z)
        if flp > 3:
            g = np.zeros((H, W), F32)
            rng = np.random.default_rng(int(z0 * 7 + x0))
            for r in range(int(h / 4.2)):
                for c_ in range(int((x1 - x0) / 3.0)):
                    q0 = cam.P(x0 + c_ * 3.0 + 0.35, r * 4.2 + 3.7, z0); q1 = cam.P(x0 + c_ * 3.0 + 2.65, r * 4.2 + 1.0, z0)
                    val = 0.55 + 0.45 * rng.random()
                    cv2.rectangle(g, (int(round(q0[0])), int(round(q0[1]))), (int(round(q1[0])), int(round(q1[1]))), val, -1)
            if mode == 'eve':
                wc = hexc('f7c9b6') * 0.6 + hexc('c7c3ea') * 0.4
                img[:] = img * (1 - (g * m2)[..., None] * 0.45) + (g * m2)[..., None] * (wc * (1 - fog) + hz * fog) * 0.45
            elif mode == 'night':
                lit = (g > 0.82).astype(F32)
                img += (lit * m2)[..., None] * hexc('ffcf8a') * 0.6 * (1 - fog * 0.5)
            else:
                img[:] = img * (1 - (g * m2)[..., None] * 0.3) + (g * m2)[..., None] * hexc('e8dcef') * 0.3


# ---------------------------------------------------------------- finishing: bloom, dust in the light, grade
def bloom(img, ts, thr=0.82, amt=0.55):
    b = np.clip(img - thr, 0, None)
    s = cv2.resize(b, (img.shape[1] // 4, img.shape[0] // 4), interpolation=cv2.INTER_AREA)
    g1 = cv2.GaussianBlur(s, (0, 0), 3 * ts); g2 = cv2.GaussianBlur(s, (0, 0), 12 * ts)
    g = cv2.resize(g1 * 0.6 + g2 * 0.8, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_LINEAR)
    return img + g * amt


def dust(img, t, ts, n=46, seed=5, col=None, op=1.0):
    """Motes drifting through the low sun, out of focus."""
    H, W = img.shape[:2]
    rng = np.random.default_rng(seed)
    P = rng.random((n, 5))
    lay = np.zeros((H, W), F32)
    for k in range(n):
        x = (P[k, 0] * W + t * (8 + 14 * P[k, 2]) * ts + 40 * ts * math.sin(t * 0.3 + k)) % W
        y = (P[k, 1] * H - t * (3 + 6 * P[k, 3]) * ts + 30 * ts * math.sin(t * 0.21 + k * 2)) % H
        r = (2 + 9 * P[k, 4] ** 2) * ts
        a = (0.25 + 0.75 * P[k, 3]) * (0.6 + 0.4 * math.sin(t * 1.3 + k))
        cv2.circle(lay, (int(x), int(y)), max(1, int(r)), a, -1, AA)
    lay = cv2.GaussianBlur(lay, (0, 0), 1.6 * ts)
    img += lay[..., None] * (hexc('ffe2b8') if col is None else col) * 0.28 * op


def grade(img, mode='eve'):
    if mode == 'eve':
        lum = img.mean(-1, keepdims=True)
        shadows = np.clip(1 - lum * 1.6, 0, 1)
        img = img + shadows * (hexc('2a2050') - 0) * 0.08
        img = img * (1 + 0.04 * np.clip(lum - 0.6, 0, 1) * hexc('ffb070'))
    return img
