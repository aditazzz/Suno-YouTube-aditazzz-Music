"""Stitch engine: a cross-stitched cloth world, rendered frame by frame as a pure function of time.

World = grid of cells (one cross stitch each). Elements are index arrays with per-cell reveal times.
A frame: compose the visible cells -> look up stitch tiles in a pre-rendered atlas -> warp through the camera
-> needle/thread overlay -> depth of field, light, grain.
"""
import os, math
import numpy as np, cv2

W, H, FPS = 1920, 1080, 30
HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "cache")
os.makedirs(CACHE, exist_ok=True)

# ----------------------------------------------------------------------------- palette (thread colours)
LINEN = (201, 182, 150)
PALETTE = [
    ("cloth", LINEN),            # 0 = bare cloth
    ("red", (186, 22, 30)),      # 1
    ("dred", (120, 14, 24)),     # 2
    ("black", (30, 27, 28)),     # 3
    ("white", (246, 241, 230)),  # 4
    ("cream", (240, 233, 216)),  # 5  app background
    ("gold", (222, 166, 34)),    # 6
    ("terra", (203, 100, 66)),   # 7  app accent
    ("skin", (226, 172, 134)),   # 8
    ("skind", (186, 124, 90)),   # 9
    ("teal", (30, 110, 120)),    # 10
    ("green", (62, 110, 60)),    # 11
    ("grey", (140, 136, 128)),   # 12
    ("brown", (110, 68, 40)),    # 13
    ("sky", (150, 196, 216)),    # 14
    ("pink", (220, 140, 140)),   # 15
    ("dgrey", (74, 70, 68)),     # 16
    ("bubble", (224, 214, 190)), # 17 user bubble
    ("yellow", (242, 208, 92)),  # 18
    ("navy", (36, 50, 84)),      # 19
    ("lbrown", (168, 120, 78)),  # 20
    ("silver", (196, 198, 200)), # 21
    ("orange", (226, 128, 48)),  # 22
    ("lgreen", (120, 160, 90)),  # 23
    ("eye", (226, 172, 134)),    # 24 skin stitch + black French knot
    ("eyet", (203, 100, 66)),    # 25 terra stitch + black French knot
]
KNOTS = {24, 25}
C = {n: i for i, (n, _) in enumerate(PALETTE)}
NCOL = len(PALETTE)
ERASE = 255
NVAR = 4
MIPS = [4, 6, 8, 12, 16, 24, 32, 48, 64, 96]


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a + 1e-9), 0, 1)
    return t * t * (3 - 2 * t)


def _wrap_blur(a, s):
    t = np.tile(a, (3, 3))
    t = cv2.GaussianBlur(t, (0, 0), s)
    n = a.shape[0]
    return t[n:2 * n, n:2 * n]


def _leg(u, v, p0, p1, r, rng, M):
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dx, dy)
    t = ((u - p0[0]) * dx + (v - p0[1]) * dy) / (L * L)
    s = ((u - p0[0]) * dy - (v - p0[1]) * dx) / L          # signed distance across
    endt = np.minimum(t, 1 - t)
    reff = r * (0.62 + 0.38 * smoothstep(0.0, 0.2, endt))  # narrows into the hole
    aa = 1.5 / M
    alpha = smoothstep(reff, reff - aa, np.abs(s)) * smoothstep(-0.02, 0.02, endt)
    q = np.clip(s / np.maximum(reff, 1e-6), -1, 1)
    prof = np.sqrt(np.clip(1 - q * q, 0, 1))
    shade = 0.50 + 0.50 * prof
    groove = np.exp(-(q / 0.16) ** 2)                       # two strands of floss
    shade -= 0.16 * groove
    shade += 0.05 * np.sin(2 * np.pi * (t * L * 9 + q * 0.9 * np.sign(dy * dx + 1e-9)))  # twist
    shade *= 0.62 + 0.38 * smoothstep(0.0, 0.16, endt)      # darkens going into the hole
    return alpha.astype(np.float32), shade.astype(np.float32), q.astype(np.float32), t.astype(np.float32)


def _build_master(M=192):
    """Returns per-variant geometry: cloth rgb, and for each leg alpha/shade + shadows."""
    yy, xx = np.mgrid[0:M, 0:M]
    u = ((xx + 0.5) / M).astype(np.float32)
    v = ((yy + 0.5) / M).astype(np.float32)
    out = []
    for var in range(NVAR):
        rng = np.random.default_rng(100 + var)
        n = 4
        su, sv = u * n, v * n
        iu, iv = np.floor(su).astype(int), np.floor(sv).astype(int)
        fu, fv = su - iu - 0.5, sv - iv - 0.5
        chk = (iu + iv) % 2
        across = np.where(chk == 0, fv, fu)
        along = np.where(chk == 0, fu, fv)
        shade = 0.80 + 0.20 * np.cos(across * np.pi)
        shade *= 0.90 + 0.10 * np.cos(along * np.pi)
        fib = np.sin(across * np.pi * 7 + rng.uniform(0, 6)) * 0.025     # fibres in each yarn
        noise = _wrap_blur(rng.normal(0, 1, (M, M)).astype(np.float32), 1.6) * 0.10
        noise2 = _wrap_blur(rng.normal(0, 1, (M, M)).astype(np.float32), 9.0) * 0.5
        d = np.minimum.reduce([np.hypot(u - a, v - b) for a in (0, 1) for b in (0, 1)])
        hole = smoothstep(0.125, 0.045, d)
        cl = (shade + fib + noise + noise2 * 0.08) * (1 - 0.62 * hole)
        cloth = np.stack([cl * LINEN[0], cl * LINEN[1] * (1 - 0.03 * hole), cl * LINEN[2] * (1 - 0.08 * hole)], -1)
        r = 0.215 * (1 + rng.uniform(-0.05, 0.05))
        j = lambda: rng.uniform(-0.012, 0.012)
        a1, s1, q1, t1 = _leg(u, v, (0 + j(), 1 + j()), (1 + j(), 0 + j()), r, rng, M)   # "/" bottom leg
        a2, s2, q2, t2 = _leg(u, v, (0 + j(), 0 + j()), (1 + j(), 1 + j()), r, rng, M)   # "\" top leg
        s1 = s1 + 0.10 * (-q1)                 # "/" leg: its upper-left flank faces the light
        s2 = s2 + 0.10 * np.exp(-((q2 + 0.35) / 0.25) ** 2)   # soft sheen streak
        tn = _wrap_blur(rng.normal(0, 1, (M, M)).astype(np.float32), 1.0) * 0.07
        s1 = s1 + tn
        s2 = s2 + tn
        sh = lambda a, k: np.roll(np.roll(cv2.GaussianBlur(a, (0, 0), M * 0.022), int(M * 0.04 * k), 0), int(M * 0.03 * k), 1)
        out.append(dict(cloth=cloth.astype(np.float32), a1=a1, s1=s1, a2=a2, s2=s2,
                        sh1=sh(a1, 1.0), sh2=sh(a2, 1.0), sh2on1=sh(a2, 0.7),
                        tone=1 + rng.uniform(-0.035, 0.035)))
    return out


def _tile(g, rgb, state):
    """state 1 = first leg only, 2 = full cross."""
    col = np.array(rgb, np.float32)
    lum = col.mean()
    # dark threads keep a little sheen so black is not a hole
    lift = 16.0 if lum < 60 else 0.0
    img = g["cloth"] * (1 - 0.42 * g["sh1"])[..., None]
    s1 = g["s1"] * g["tone"]
    if state == 2:
        s1 = s1 * (1 - 0.38 * g["sh2on1"])
    leg1 = np.clip(col[None, None] * s1[..., None] * 1.12 + lift * np.clip(s1 - 0.6, 0, 1)[..., None] * 2, 0, 255)
    img = img * (1 - g["a1"][..., None]) + leg1 * g["a1"][..., None]
    if state == 2:
        img = img * (1 - 0.42 * g["sh2"] * (1 - g["a1"]))[..., None]
        s2 = g["s2"] * g["tone"]
        leg2 = np.clip(col[None, None] * s2[..., None] * 1.12 + lift * np.clip(s2 - 0.6, 0, 1)[..., None] * 2, 0, 255)
        img = img * (1 - g["a2"][..., None]) + leg2 * g["a2"][..., None]
    return img


def _knot(img, M):
    """A French knot sitting on the stitch: a small dark bead with a sheen and a shadow."""
    yy, xx = np.mgrid[0:M, 0:M]
    u = (xx + 0.5) / M; v = (yy + 0.5) / M
    r = 0.235
    d = np.hypot(u - 0.5, v - 0.5)
    sh = np.exp(-(np.hypot(u - 0.56, v - 0.58) / (r * 1.05)) ** 2 * 1.6)
    img = img * (1 - 0.5 * sh)[..., None]
    a = smoothstep(r, r - 2.0 / M, d)
    nz = np.sqrt(np.clip(1 - (d / r) ** 2, 0, 1))
    lam = np.clip(0.35 + 0.65 * (nz * 0.8 - (u - 0.5) / r * 0.35 - (v - 0.5) / r * 0.35), 0, 1.3)
    twist = 0.06 * np.sin(np.arctan2(v - 0.5, u - 0.5) * 3 + d * 40)
    spec = np.exp(-(np.hypot(u - 0.43, v - 0.42) / 0.06) ** 2)
    col = np.array([34, 30, 32], np.float32)[None, None] * (lam + twist)[..., None] * 1.5 + 150 * spec[..., None]
    return img * (1 - a[..., None]) + np.clip(col, 0, 255) * a[..., None]


def _back_tile(g, rgb, rng):
    """Back of a cross stitch: two short parallel bars."""
    M = g["cloth"].shape[0]
    yy, xx = np.mgrid[0:M, 0:M]
    u = ((xx + 0.5) / M).astype(np.float32); v = ((yy + 0.5) / M).astype(np.float32)
    img = g["cloth"][:, ::-1].copy() * 0.93
    col = np.array(rgb, np.float32)
    for x0 in (0.04, 0.96):
        a, s, q, t = _leg(u, v, (x0, 0.02), (x0 + rng.uniform(-0.03, 0.03), 0.98), 0.17, rng, M)
        sha = np.roll(cv2.GaussianBlur(a, (0, 0), M * 0.02), int(M * 0.03), 0)
        img = img * (1 - 0.35 * sha * (1 - a))[..., None]
        img = img * (1 - a[..., None]) + np.clip(col * s[..., None] * 1.05, 0, 255) * a[..., None]
    return img


_ATLAS = None


def atlas():
    """dict S -> uint8 array [key, S, S, 3]; key = colour*12 + state*4 + variant, state 0 half,1 full,2 back."""
    global _ATLAS
    if _ATLAS is not None:
        return _ATLAS
    path = os.path.join(CACHE, "atlas_v6.npz")
    if os.path.exists(path):
        z = np.load(path)
        _ATLAS = {int(k): z[k] for k in z.files}
        return _ATLAS
    M = 192
    geo = _build_master(M)
    rng = np.random.default_rng(7)
    tiles = np.zeros((NCOL * 12, M, M, 3), np.float32)
    for ci, (_, rgb) in enumerate(PALETTE):
        for var in range(NVAR):
            g = geo[var]
            if ci == 0:
                tiles[ci * 12 + 0 + var] = g["cloth"]
                tiles[ci * 12 + 4 + var] = g["cloth"]
                tiles[ci * 12 + 8 + var] = g["cloth"][:, ::-1] * 0.93
            else:
                tiles[ci * 12 + 0 + var] = _tile(g, rgb, 1)
                tiles[ci * 12 + 4 + var] = _tile(g, rgb, 2) if ci not in KNOTS else _knot(_tile(g, rgb, 2), M)
                tiles[ci * 12 + 8 + var] = _back_tile(g, rgb, rng)
    tiles = np.clip(tiles, 0, 255)
    A = {}
    for S in MIPS:
        A[S] = np.stack([cv2.resize(t, (S, S), interpolation=cv2.INTER_AREA) for t in tiles]).round().astype(np.uint8)
    np.savez(path, **{str(k): v for k, v in A.items()})
    _ATLAS = A
    return A


# ----------------------------------------------------------------------------- world
class World:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.elems = []     # (idx, x, y, ton, toff, tmin, half)
        self.dyn = []       # fn(t) -> list of (idx, x, y)
        rng = np.random.default_rng(3)
        self._var = rng.integers(0, NVAR, (4096, 4096), dtype=np.uint8)

    def add(self, idx, x, y, ton=-1e9, toff=1e9, half=True):
        idx = np.asarray(idx, np.uint8)
        if np.isscalar(ton):
            tmin = ton
            ton_a = None
        else:
            ton_a = np.asarray(ton, np.float32)
            tmin = float(ton_a[idx > 0].min()) if (idx > 0).any() else 1e9
        if not np.isscalar(toff):
            toff = np.asarray(toff, np.float32)
            tmax = float(toff[idx > 0].max()) if (idx > 0).any() else -1e9
        else:
            tmax = toff
        self.elems.append([idx, int(x), int(y), ton if ton_a is None else ton_a, toff, tmin, half, tmax])
        return len(self.elems) - 1

    def dynamic(self, fn):
        self.dyn.append(fn)

    def compose(self, t, x0, y0, x1, y1):
        """colour grid + state grid (0 half, 1 full) for cells [x0,x1) x [y0,y1)."""
        gh, gw = y1 - y0, x1 - x0
        col = np.zeros((gh, gw), np.uint8)
        st = np.ones((gh, gw), np.uint8)

        def blit(idx, ex, ey, ton, toff, half):
            eh, ew = idx.shape
            ax0, ay0 = max(ex, x0), max(ey, y0)
            ax1, ay1 = min(ex + ew, x1), min(ey + eh, y1)
            if ax0 >= ax1 or ay0 >= ay1:
                return
            sub = idx[ay0 - ey:ay1 - ey, ax0 - ex:ax1 - ex]
            m = sub > 0
            if isinstance(ton, np.ndarray):
                tsub = ton[ay0 - ey:ay1 - ey, ax0 - ex:ax1 - ex]
                m &= tsub <= t
            if isinstance(toff, np.ndarray):
                m &= toff[ay0 - ey:ay1 - ey, ax0 - ex:ax1 - ex] > t
            if not m.any():
                return
            cv_ = col[ay0 - y0:ay1 - y0, ax0 - x0:ax1 - x0]
            sv_ = st[ay0 - y0:ay1 - y0, ax0 - x0:ax1 - x0]
            er = m & (sub == ERASE)
            dr = m & ~er
            cv_[dr] = sub[dr]
            if half and isinstance(ton, np.ndarray):
                fresh = (t - tsub) < 0.055
                sv_[dr] = np.where(fresh[dr], 0, 1)
                # unpicking: half stitch of the old colour lingers one beat of time
                efresh = er & fresh
                sv_[efresh] = 0
                gone = er & ~fresh
                cv_[gone] = 0
                sv_[gone] = 1
            else:
                sv_[dr] = 1
                cv_[er] = 0
                sv_[er] = 1

        for idx, ex, ey, ton, toff, tmin, half, tmax in self.elems:
            if t < tmin or t >= tmax:
                continue
            blit(idx, ex, ey, ton, toff, half)
        for fn in self.dyn:
            for item in fn(t) or ():
                blit(np.asarray(item[0], np.uint8), int(item[1]), int(item[2]), -1e9, 1e9, False)
        return col, st

    def raster(self, t, x0, y0, x1, y1, S, back=False):
        col, st = self.compose(t, x0, y0, x1, y1)
        vy = (np.arange(y0, y1) % 4096)[:, None]
        vx = (np.arange(x0, x1) % 4096)[None, :]
        var = self._var[vy, vx]
        if back:
            key = col.astype(np.int32) * 12 + 8 + var
        else:
            key = col.astype(np.int32) * 12 + st.astype(np.int32) * 4 + var
        A = atlas()[S]
        tiles = A[key]                                   # gh, gw, S, S, 3
        gh, gw = key.shape
        return tiles.transpose(0, 2, 1, 3, 4).reshape(gh * S, gw * S, 3)


# ----------------------------------------------------------------------------- camera
def cam_matrix(cx, cy, zoom, rot=0.0, tilt=0.0, flipx=1.0):
    """3x3 matrix cell coords -> screen px. tilt = keystone (camera leaning), flipx for the card flip."""
    c, s = math.cos(rot), math.sin(rot)
    T1 = np.array([[1, 0, -cx], [0, 1, -cy], [0, 0, 1]], np.float64)
    R = np.array([[c * zoom * flipx, -s * zoom, 0], [s * zoom * flipx, c * zoom, 0], [0, 0, 1]], np.float64)
    P = np.array([[1, 0, 0], [0, 1, 0], [0, tilt / H, 1]], np.float64)
    T2 = np.array([[1, 0, W / 2], [0, 1, H / 2], [0, 0, 1]], np.float64)
    return T2 @ P @ R @ T1


def pick_mip(z):
    for S in MIPS:
        if S >= z * 0.98:
            return S
    return MIPS[-1]


def project(M, x, y):
    p = M @ np.array([x, y, 1.0])
    return p[0] / p[2], p[1] / p[2]


def render_cloth(world, t, cam, back=False):
    cx, cy, zoom = cam["x"], cam["y"], cam["zoom"]
    M = cam_matrix(cx, cy, zoom, cam.get("rot", 0.0), cam.get("tilt", 0.0), cam.get("flipx", 1.0))
    Mi = np.linalg.inv(M)
    pts = []
    for sx in (0, W / 2, W):
        for sy in (0, H / 2, H):
            p = Mi @ np.array([sx, sy, 1.0])
            pts.append((p[0] / p[2], p[1] / p[2]))
    pts = np.array(pts)
    x0, y0 = np.floor(pts.min(0)).astype(int) - 1
    x1, y1 = np.ceil(pts.max(0)).astype(int) + 1
    zeff = zoom * (1 + abs(cam.get("tilt", 0.0)) * 0.5)
    S = pick_mip(zeff)
    # guard the raster size
    while (x1 - x0) * S * (y1 - y0) * S > 40e6 and S > MIPS[0]:
        S = MIPS[MIPS.index(S) - 1]
    ras = world.raster(t, x0, y0, x1, y1, S, back=back)
    Cm = np.array([[1 / S, 0, x0], [0, 1 / S, y0], [0, 0, 1]], np.float64)
    Hm = M @ Cm
    interp = cv2.INTER_LINEAR if S <= zeff * 1.3 else cv2.INTER_AREA
    frame = cv2.warpPerspective(ras, Hm, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    return frame, M


# ----------------------------------------------------------------------------- post
_LIGHT = {}
_GRAIN = None


def light_map(lx=0.38, ly=0.36, strength=0.42, warm=0.05):
    key = (round(lx, 2), round(ly, 2), round(strength, 2), round(warm, 3))
    if key in _LIGHT:
        return _LIGHT[key]
    yy, xx = np.mgrid[0:H // 4, 0:W // 4].astype(np.float32)
    xx = xx / (W / 4); yy = yy / (H / 4)
    d = np.hypot((xx - lx) * 1.25, (yy - ly) * 0.95)
    f = 1.06 - strength * smoothstep(0.15, 1.05, d)
    f = cv2.resize(f, (W, H), interpolation=cv2.INTER_CUBIC)
    rgb = np.stack([f * (1 + warm), f * (1 + warm * 0.15), f * (1 - warm * 1.7)], -1)     # RGB order
    lm = np.clip(rgb * 200, 0, 255).astype(np.uint8)
    if len(_LIGHT) > 64:
        _LIGHT.clear()
    _LIGHT[key] = lm
    return lm


def grain(i):
    global _GRAIN
    if _GRAIN is None:
        rng = np.random.default_rng(11)
        _GRAIN = [np.clip(128 + cv2.GaussianBlur(rng.normal(0, 26, (H, W)).astype(np.float32), (0, 0), 0.7), 0, 255).astype(np.uint8)
                  for _ in range(6)]
    g = _GRAIN[i % 6]
    return cv2.merge([g, g, g])


_DOFMASK = {}


def dof(frame, amount, focus_y=0.5, band=0.22):
    """Tilt-shift: sharp band around focus_y, blur growing above and below. amount = sigma px at the edges."""
    if amount < 0.3:
        return frame
    key = (round(focus_y, 2), round(band, 2))
    if key not in _DOFMASK:
        yy = (np.arange(H, dtype=np.float32) / H)[:, None]
        m = smoothstep(band, band + 0.42, np.abs(yy - focus_y))
        if len(_DOFMASK) > 64:
            _DOFMASK.clear()
        _DOFMASK[key] = np.repeat(m, W, 1)
    m = _DOFMASK[key]
    b = cv2.GaussianBlur(frame, (0, 0), amount)
    b2 = cv2.GaussianBlur(frame, (0, 0), amount * 0.45)
    m3 = cv2.merge([m, m, m])
    f = frame.astype(np.float32)
    mid = np.clip(m3 * 2, 0, 1)
    far = np.clip(m3 * 2 - 1, 0, 1)
    out = f * (1 - mid) + b2.astype(np.float32) * mid
    out = out * (1 - far) + b.astype(np.float32) * far
    return out.astype(np.uint8)


_WR = None
WR_PX, WR_MARGIN = 2.0, 60          # wrinkle texture: px per cell, margin in cells


def wrinkle_tex():
    """World-anchored cloth shading: soft undulation of the linen, uneven tone, two old fold creases."""
    global _WR
    if _WR is None:
        path = os.path.join(CACHE, "wrinkle_v2.npy")
        if os.path.exists(path):
            _WR = np.load(path)
            return _WR
        w = int((480 + 2 * WR_MARGIN) * WR_PX); h = int((270 + 2 * WR_MARGIN) * WR_PX)
        rng = np.random.default_rng(5)
        hgt = np.zeros((h, w), np.float32)
        for sig, amp in ((70, 1.0), (30, 0.45), (12, 0.16)):
            n = cv2.GaussianBlur(rng.normal(0, 1, (h, w)).astype(np.float32), (0, 0), sig)
            hgt += amp * n / n.std()
        gx = cv2.Sobel(hgt, cv2.CV_32F, 1, 0, ksize=5); gy = cv2.Sobel(hgt, cv2.CV_32F, 0, 1, ksize=5)
        sl = -(gx * 0.7 + gy * 0.7)
        sl = sl / (np.abs(sl).max() + 1e-6)
        shade = 1.0 + 0.085 * np.tanh(sl * 3.0)
        tone = cv2.GaussianBlur(rng.normal(0, 1, (h, w)).astype(np.float32), (0, 0), 45)
        shade *= 1.0 + 0.022 * tone / tone.std()
        # fold creases from years in a drawer: a ridge with a lit and a shaded flank
        xs = (np.arange(w, dtype=np.float32) / WR_PX - WR_MARGIN)[None, :]
        ys = (np.arange(h, dtype=np.float32) / WR_PX - WR_MARGIN)[:, None]
        for x0 in (162.5, 318.5):
            d = xs - x0
            shade *= 1.0 + 0.05 * (-d / 2.2) * np.exp(-(d / 2.2) ** 2)
        for y0 in (135.0,):
            d = ys - y0
            shade *= 1.0 + 0.04 * (-d / 2.2) * np.exp(-(d / 2.2) ** 2)
        _WR = np.clip(shade * 200, 0, 255).astype(np.uint8)
        np.save(path, _WR)
    return _WR


def wrinkle(frame, M):
    T = np.array([[1 / WR_PX, 0, -WR_MARGIN], [0, 1 / WR_PX, -WR_MARGIN], [0, 0, 1]], np.float64)
    wm = cv2.warpPerspective(wrinkle_tex(), M @ T, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return cv2.multiply(frame, cv2.merge([wm, wm, wm]), scale=1 / 200.0)


_SPOT = None


def _spot(frame, s):
    """Night: the cloth falls into cool shadow outside one warm pool of lamplight (the wedding after dark)."""
    global _SPOT
    if _SPOT is None:
        yy, xx = np.mgrid[0:H // 4, 0:W // 4].astype(np.float32)
        d = np.hypot((xx / (W / 4) - 0.5) / 0.60, (yy / (H / 4) - 0.54) / 0.62)
        m = 1 - smoothstep(0.62, 1.12, d)
        _SPOT = cv2.resize(m.astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)[..., None]
    f = frame.astype(np.float32)
    dark = f * np.array([0.30, 0.34, 0.50], np.float32)          # RGB: dim and cool
    lit = np.minimum(f * np.array([1.07, 1.02, 0.90], np.float32), 255)
    m = _SPOT
    out = lit * m + dark * (1 - m)
    return np.clip(f * (1 - s) + out * s, 0, 255).astype(np.uint8)


def finish(frame, fi, cam):
    frame = dof(frame, cam.get("dof", 0.0), cam.get("focus_y", 0.5), cam.get("band", 0.22))
    lm = light_map(cam.get("lx", 0.38), cam.get("ly", 0.36), cam.get("lstr", 0.42), cam.get("warm", 0.05))
    frame = cv2.multiply(frame, lm, scale=1 / 200.0)
    sp = cam.get("spot", 0.0)
    if sp > 0.003:
        frame = _spot(frame, sp)
    frame = cv2.addWeighted(frame, 1.0, grain(fi), 0.05, -0.05 * 128)
    fade = cam.get("fade", 1.0)
    if fade < 0.999:
        frame = cv2.convertScaleAbs(frame, alpha=max(fade, 0.0))
    return frame


# ----------------------------------------------------------------------------- needle + thread (screen space)
def _bez(p0, p1, p2, n=40):
    t = np.linspace(0, 1, n)[:, None]
    return (1 - t) ** 2 * p0 + 2 * t * (1 - t) * p1 + t ** 2 * p2


def draw_thread(frame, pts, zoom, rgb, shadow_off=(0, 0)):
    th = max(2, int(round(zoom * 0.17)))
    pts_i = np.round(pts * 16).astype(np.int32)
    if shadow_off[0] or shadow_off[1]:
        sh = np.zeros(frame.shape[:2], np.uint8)
        so = np.round((pts + np.array(shadow_off)) * 16).astype(np.int32)
        cv2.polylines(sh, [so], False, 255, th, cv2.LINE_AA, 4)
        sh = cv2.GaussianBlur(sh, (0, 0), max(1.5, zoom * 0.12))
        k = (1 - 0.45 * sh.astype(np.float32) / 255)
        frame[:] = (frame.astype(np.float32) * k[..., None]).astype(np.uint8)
    col = np.array(rgb, np.float32)
    cv2.polylines(frame, [pts_i], False, tuple(int(c) for c in col * 0.55), th + 2, cv2.LINE_AA, 4)
    cv2.polylines(frame, [pts_i], False, tuple(int(c) for c in col * 0.95), th, cv2.LINE_AA, 4)
    hl = np.round((pts - np.array([th * 0.22, th * 0.22])) * 16).astype(np.int32)
    cv2.polylines(frame, [hl], False, tuple(int(min(255, c * 1.25 + 26)) for c in col), max(1, th // 3), cv2.LINE_AA, 4)


def draw_needle(frame, tip, zoom, lift, rgb, anchor=None, ang_deg=-38, plunge=0.0, alpha=1.0):
    """tip = screen px of the hole the needle points to; lift in cells (height above cloth);
    plunge 0..1 = part of the needle already through the cloth. anchor = the hole the thread comes out of."""
    if alpha <= 0.01:
        return
    base = frame.copy() if alpha < 0.999 else None
    L = 15.0 * zoom
    a = math.radians(ang_deg)
    d = np.array([math.cos(a), math.sin(a)])            # from tip toward the eye (up-right)
    n = np.array([-d[1], d[0]])
    tipp = np.array(tip, np.float64) + np.array([0, -lift * zoom * 0.9])
    eye = tipp + d * L
    wmax = max(3.4, zoom * 0.46)
    so = np.array([lift * zoom * 0.55 + zoom * 0.3, lift * zoom * 0.75 + zoom * 0.4])
    # needle shadow on the cloth
    sh = np.zeros(frame.shape[:2], np.uint8)
    a0 = np.array(tip, np.float64) if plunge > 0 else tipp + so
    cv2.line(sh, tuple(np.round(a0 * 16).astype(int)), tuple(np.round((eye + so) * 16).astype(int)), 255,
             int(wmax * 1.2) + 1, cv2.LINE_AA, 4)
    sh = cv2.GaussianBlur(sh, (0, 0), max(2.0, zoom * (0.16 + 0.22 * lift)))
    k = (1 - 0.55 * sh.astype(np.float32) / 255)
    frame[:] = (frame.astype(np.float32) * k[..., None]).astype(np.uint8)
    # thread: out of the cloth, a hanging loop, up through the eye
    if anchor is not None:
        anc = np.array(anchor, np.float64)
        eyec = tipp + d * L * 0.95
        span = eyec - anc
        c1 = anc + np.array([span[0] * 0.15, zoom * (5.0 + lift)])
        c2 = eyec + np.array([zoom * 3.5, zoom * (7.5 + lift)])
        t_ = np.linspace(0, 1, 56)[:, None]
        pts = (1 - t_) ** 3 * anc + 3 * (1 - t_) ** 2 * t_ * c1 + 3 * (1 - t_) * t_ ** 2 * c2 + t_ ** 3 * eyec
        draw_thread(frame, pts, zoom, rgb, shadow_off=(zoom * 0.45, zoom * 0.6))
    # needle body: tapered steel, dark edge, bright core
    ts = np.linspace(plunge, 1.0, 26)
    wid = np.array([wmax * (0.10 + 0.90 * smoothstep(0.0, 0.25, tt)) for tt in ts])
    left = np.array([tipp + d * L * tt + n * w / 2 for tt, w in zip(ts, wid)])
    right = np.array([tipp + d * L * tt - n * w / 2 for tt, w in zip(ts, wid)])
    poly = np.round(np.vstack([left, right[::-1]]) * 16).astype(np.int32)
    cv2.polylines(frame, [poly], True, (40, 40, 46), max(2, int(wmax * 0.35)), cv2.LINE_AA, 4)
    cv2.fillPoly(frame, [poly], (118, 122, 130), cv2.LINE_AA, 4)
    core = np.array([tipp + d * L * tt + n * w * 0.10 for tt, w in zip(ts, wid)])
    cv2.polylines(frame, [np.round(core * 16).astype(np.int32)], False, (186, 190, 198), max(1, int(wmax * 0.5)), cv2.LINE_AA, 4)
    hl = np.array([tipp + d * L * tt + n * w * 0.20 for tt, w in zip(ts, wid)])
    cv2.polylines(frame, [np.round(hl * 16).astype(np.int32)], False, (246, 247, 250), max(1, int(wmax * 0.2)), cv2.LINE_AA, 4)
    # the eye, with the thread through it
    ec = tipp + d * L * 0.95
    cv2.ellipse(frame, tuple(np.round(ec).astype(int)), (max(2, int(wmax * 1.0)), max(1, int(wmax * 0.24))), ang_deg, 0, 360,
                tuple(int(c * 0.85) for c in rgb) if anchor is not None else (40, 36, 36), -1, cv2.LINE_AA)
    if base is not None:
        frame[:] = cv2.addWeighted(frame, alpha, base, 1 - alpha, 0)


# ----------------------------------------------------------------------------- keyframes
def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def ease_io(x, p=2.2):
    x = min(1.0, max(0.0, x))
    return x ** p / (x ** p + (1 - x) ** p)


class Track:
    """Keyframed camera: list of (t, dict). Holds are just two keys with equal values. Zoom in log space."""

    def __init__(self, keys):
        self.keys = sorted(keys, key=lambda k: k[0])

    def at(self, t):
        ks = self.keys
        if t <= ks[0][0]:
            return dict(ks[0][1])
        if t >= ks[-1][0]:
            return dict(ks[-1][1])
        for i in range(len(ks) - 1):
            if ks[i][0] <= t < ks[i + 1][0]:
                a, b = ks[i], ks[i + 1]
                x = (t - a[0]) / (b[0] - a[0])
                if "eo" in b[1]:
                    e = 1 - (1 - x) ** b[1]["eo"]
                elif "ei" in b[1]:
                    e = x ** b[1]["ei"]
                else:
                    e = ease_io(x, b[1].get("p", 2.0))
                out = {}
                for k in set(a[1]) | set(b[1]):
                    if k in ("p", "eo", "ei", "cut"):
                        continue
                    va = a[1].get(k, b[1].get(k))
                    vb = b[1].get(k, a[1].get(k))
                    if k == "zoom":
                        out[k] = math.exp(math.log(va) * (1 - e) + math.log(vb) * e)
                    else:
                        out[k] = va * (1 - e) + vb * e
                return out
        return dict(ks[-1][1])
