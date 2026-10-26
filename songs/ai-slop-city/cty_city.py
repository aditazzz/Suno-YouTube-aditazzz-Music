"""The plaza and its towers, drawn as projected polygons in a clean ligne-claire style.

World: x = north (screen right in the main view), y = up, z = west (into the main view). The bench sits at the origin;
the Feed Tower's front face is the plane z = T1Z, facing the camera. Drawing keeps an ID buffer so sun shadows and her
(unnatural) shadow can be applied per visible surface afterwards.
"""
import math
import numpy as np, cv2
from cty_eng import (F32, AA, hexc, c8, mix, clamp, sstep, nrm, Cam, clip_near, screen_poly, fill, fill_id, lines, seg,
                     quad_grid, proj_quads, to_f, to_8, glow)
from cty_sky import sun, palette, render_sky

GROUND, T1F, T1W, LEDB = 1, 2, 4, 9
T1Z = 30.0                      # Feed Tower east face (plane z = T1Z, facing the camera's right-front)
T1X0, T1X1 = 30.0, 57.0         # 9 bays of 3 m; its south face is the plane x = T1X0
T1D = 27.0                      # depth (square plan)
BAY, FLOOR, LOBBY = 3.0, 3.6, 7.2
T1_ROWS, T1_COLS = 42, 9
T1Y0 = LOBBY + 2.4              # first office floor (above the LED band)
T1H = T1Y0 + T1_ROWS * FLOOR
PLAZA = (-16.0, 74.0, -48.0, 72.0)
# the bench and her live in a frame turned 45 degrees: she faces north-east, the bench runs north-west
BF = np.array([math.cos(math.radians(45)), 0.0, -math.sin(math.radians(45))])   # her facing direction
BA = np.array([math.sin(math.radians(45)), 0.0, math.cos(math.radians(45))])    # along the bench, away from camera
BU = np.array([0.0, 1.0, 0.0])


def bw(lx, ly, lz):
    """Bench-local (forward, up, along) -> world."""
    return BF * lx + BU * ly + BA * lz


def bwa(P):
    P = np.asarray(P, float)
    return P[..., 0:1] * BF + P[..., 1:2] * BU + P[..., 2:3] * BA


def fs(d, s):
    """Plaza position given as (forward, right) metres from the bench, as seen by the master camera."""
    return (0.7071 * (d + s), 0.7071 * (d - s))

STONE = hexc('e8dcc8'); STONE_SH = hexc('cbbda6')
PAVE = hexc('c2b8a8'); PAVE2 = hexc('aea290'); ASPH = hexc('55525e')
SCREEN_COLS = [hexc('7af0ff'), hexc('ff5fc8'), hexc('fff27a'), hexc('9a8cff'), hexc('ffffff')]
NEON_COLS = [hexc('ff3fbf'), hexc('3ff0ff'), hexc('b25cff'), hexc('ff5f6d')]

# 3 x 5 pixel letters for spelling words in windows
GLYPH = {
    'S': ['111', '100', '111', '001', '111'], 'L': ['100', '100', '100', '100', '111'], 'O': ['111', '101', '101', '101', '111'],
    'P': ['111', '101', '111', '100', '100'], 'Y': ['101', '101', '111', '010', '010'], 'E': ['111', '100', '111', '100', '111'],
    'U': ['101', '101', '101', '101', '111'], 'R': ['111', '101', '110', '101', '101'], 'I': ['111', '010', '010', '010', '111'],
    'G': ['111', '100', '101', '101', '111'], 'H': ['101', '101', '111', '101', '101'], 'T': ['111', '010', '010', '010', '010'],
}


def spell(word, rows=42, cols=9, row0=5, scale=1, on=4, off=5, pad=1):
    """Window states spelling a 2-letter word on one face (9 columns), like a light show on the curtain wall: `on` (4)
    lights whole cells (window + spandrel) so strokes read solid, `off` (5) blacks out a band of whole cells around the
    letters for contrast; -1 elsewhere = leave those windows to the normal day/night state."""
    a = np.full((rows, cols), -1, np.int8)
    a[max(0, row0 - pad):min(rows, row0 + 5 * scale + pad)] = off
    x = 1
    for ch in word:
        g = GLYPH[ch]
        for r in range(5):
            for c_ in range(3):
                if g[r][c_] == '1':
                    for k in range(scale):
                        rr = row0 + (4 - r) * scale + k
                        if 0 <= rr < rows: a[rr, x + c_] = on
        x += 4
    return a


# ------------------------------------------------------------------ frame context
class Ctx:
    def __init__(self, cam, h, t, pal, sunvec=None):
        self.cam = cam; self.h = h; self.t = t; self.pal = pal
        L, el, az = sun(h) if sunvec is None else sunvec
        self.L = np.asarray(L, np.float64); self.el = el; self.az = az
        self.sunk = clamp((el + 1.0) / 6.0) * float(pal['sun'].max() > 0.02)
        self.suncol = pal['sun'] * 1.0
        self.amb = pal['amb']
        self.fog = pal['fog']; self.fogd = pal['fogd']
        self.ink = pal['ink']
        W, H = cam.W, cam.H
        self.idb = np.zeros((H, W), np.uint16)
        self.sh = np.zeros((H, W), np.uint8)       # sun-shadow mask (applied to ground + Feed Tower front)
        self.glow = np.zeros((H, W, 3), np.uint8)  # emissive layer (windows, lamps, screens) for bloom
        self.grads = []                             # (face id, screen y top, y bottom, k top, k bottom)
        self.lw = max(1.0, H / 1080)

    def lightk(self, ndl):
        return self.amb * 0.92 + self.suncol * (max(0.0, ndl) ** 0.55) * self.sunk * 0.66

    def light(self, alb, n, dist=0.0):
        ndl = float(np.dot(n, self.L)) if self.sunk > 0 else 0.0
        return self.fogged(np.asarray(alb, F32) * self.lightk(ndl), dist)

    def fogged(self, c, dist):
        f = 1 - math.exp(-max(0.0, dist) * self.fogd)
        return mix(c, self.fog, f)

    def inkc(self, dist):
        return self.fogged(self.ink, dist * 1.3)


# ------------------------------------------------------------------ boxes
def box_faces(x0, x1, z0, z1, h, y0=0.0):
    """(name, corners[bl,br,tr,tl], normal, u-vector) for the 4 sides + top, as seen from outside."""
    return [
        ('S', np.array([(x0, y0, z0), (x1, y0, z0), (x1, h, z0), (x0, h, z0)], float), np.array([0, 0, -1.0]), np.array([1, 0, 0.0])),
        ('E', np.array([(x1, y0, z0), (x1, y0, z1), (x1, h, z1), (x1, h, z0)], float), np.array([1.0, 0, 0]), np.array([0, 0, 1.0])),
        ('W', np.array([(x0, y0, z1), (x0, y0, z0), (x0, h, z0), (x0, h, z1)], float), np.array([-1.0, 0, 0]), np.array([0, 0, -1.0])),
        ('N', np.array([(x1, y0, z1), (x0, y0, z1), (x0, h, z1), (x1, h, z1)], float), np.array([0, 0, 1.0]), np.array([-1, 0, 0.0])),
        ('T', np.array([(x0, h, z0), (x1, h, z0), (x1, h, z1), (x0, h, z1)], float), np.array([0, 1.0, 0]), np.array([1, 0, 0.0])),
    ]


class Tower:
    def __init__(self, name, x0, x1, z0, z1, h, kind, seed, alb='d9cfbf', bay=3.0, floor=3.6, lobby=6.0, fid=10,
                 casts=True, tiers=()):
        self.name, self.kind, self.seed = name, kind, seed
        self.x0, self.x1, self.z0, self.z1, self.h = x0, x1, z0, z1, h
        self.alb = hexc(alb); self.bay, self.floor, self.lobby = bay, floor, lobby
        self.fid = fid; self.casts = casts
        self.faces = box_faces(x0, x1, z0, z1, h)
        self.tiers = tiers               # setbacks on top: list of (inset, height)
        rng = np.random.default_rng(seed)
        self.rand = {}
        for nm, C, n, u in self.faces[:4]:
            wlen = np.linalg.norm(C[1] - C[0])
            cols = max(1, int(round(wlen / bay))); rows = max(1, int((h - lobby) / floor))
            self.rand[nm] = dict(cols=cols, rows=rows, r=rng.random((rows, cols)), r2=rng.random((rows, cols)),
                                 blind=rng.random((rows, cols)), ph=rng.random((rows, cols)) * 100)

    def depth_key(self, cam):
        p = cam.pos
        q = np.array([np.clip(p[0], self.x0, self.x1), np.clip(p[1], 0, self.h), np.clip(p[2], self.z0, self.z1)])
        return float(np.linalg.norm(q - p))


def _az(x, z):
    """Compass azimuth (deg, north = 0, east = 90) of a ground point seen from the bench."""
    return math.degrees(math.atan2(-z, x)) % 360


def make_city():
    T = []
    T.append(Tower('T1', T1X0, T1X1, T1Z, T1Z + T1D, T1H, 'stone', 1, 'e8dcc8', BAY, FLOOR, T1Y0, fid=T1F,
                   tiers=((2.5, 9.0), (5.0, 7.0), (8.5, 5.0))))
    T.append(Tower('T3', 88, 114, 2, 28, 68, 'brick', 3, 'bd8d70', 3.4, 3.6, 5.5, fid=30))
    T.append(Tower('L1', -42, -16, 4, 48, 22.0, 'arcade', 8, 'dccfb8', 4.0, 3.8, 5.0, fid=80))
    T.append(Tower('R1', 16, 42, -40, -8, 26.0, 'arcade', 9, 'cdbba2', 4.0, 3.8, 5.0, fid=86))
    T.append(Tower('T2', 150, 180, 120, 150, 236, 'glass', 2, '9db3cc', 3.2, 3.8, 6.0, fid=20))
    T.append(Tower('T4', 200, 228, 40, 68, 196, 'glass', 4, '8ea6c4', 3.0, 3.8, 6.0, fid=40))
    T.append(Tower('T5', 120, 146, 196, 222, 150, 'stone', 5, 'd6c9b3', 3.2, 3.6, 6.0, fid=50))
    T.append(Tower('T6', -84, -54, -64, -34, 88, 'brick', 6, 'c79a7a', 3.4, 3.6, 5.5, fid=60))
    T.append(Tower('T7', 44, 74, -96, -66, 132, 'glass', 7, 'a2b8cc', 3.0, 3.8, 6.0, fid=70))
    T.append(Tower('L2', -10, 14, 62, 90, 34.0, 'arcade', 11, 'd8c7ad', 4.0, 3.8, 5.0, fid=90))
    rng = np.random.default_rng(99)
    fid = 100
    placed = 0
    while placed < 190:
        ang = rng.uniform(0, 2 * math.pi); r = rng.uniform(110, 760)
        cx, cz = r * math.cos(ang), r * math.sin(ang)
        az = _az(cx, cz)
        if -40 < cx < 190 and -110 < cz < 230: continue
        if 230 <= az < 312:          # west / south-west: the old low-rise district, open sky for sunsets
            h = rng.uniform(10, 34) if r < 420 else rng.uniform(20, 70)
        elif 312 <= az or az < 40:   # north-west to north: the business district behind the Feed Tower
            h = rng.uniform(60, 250) * (1.2 if r > 350 else 1.0)
        elif 40 <= az < 140:         # east: the sunrise skyline
            h = rng.uniform(50, 220) if not (82 < az < 98) else rng.uniform(14, 40)
        else:                        # south
            h = rng.uniform(25, 110)
        w = rng.uniform(18, 46); d = rng.uniform(18, 46)
        kind = str(rng.choice(['far', 'farglass'])) if h > 40 else 'far'
        alb = str(rng.choice(['cdbfae', 'a9b6c6', 'bba48e', 'd6cbbb', '9aaabe']))
        T.append(Tower('S%d' % placed, cx - w / 2, cx + w / 2, cz - d / 2, cz + d / 2, h, kind, 1000 + placed, alb, 3.2, 3.8,
                       6.0 if h > 40 else 3.0, fid=fid, casts=False)); fid += 6
        placed += 1
    return T


CITY = make_city()
CITY_BY = {T.name: T for T in CITY}


# ------------------------------------------------------------------ ground
def ground(img, ctx, lamps, lamp_amt, extra_light=None, s=2):
    """Paving with fog, ambient occlusion at building feet and night lamp pools, computed at half resolution."""
    cam = ctx.cam; W, H = cam.W, cam.H
    d = cam.ray_dirs(s)
    dy = d[..., 1]
    ok = dy < -1e-5
    tt = np.where(ok, -cam.pos[1] / np.where(ok, dy, -1), 0).astype(F32)
    gx = (cam.pos[0] + d[..., 0] * tt).astype(F32); gz = (cam.pos[2] + d[..., 2] * tt).astype(F32)
    dist = tt
    sx = np.floor(gx / 1.5).astype(np.int32); sz = np.floor(gz / 1.5).astype(np.int32)
    hsh = ((sx * 73856093) ^ (sz * 19349663)) & 1023
    tone = (hsh.astype(F32) / 1023 - 0.5) * 0.06
    fade = np.clip(1 - dist / 60, 0, 1)
    band = ((np.abs(((gx + 6) % 12) - 6) < 0.42) | (np.abs(((gz + 6) % 12) - 6) < 0.42)).astype(F32) * np.clip(1 - dist / 150, 0, 1)
    x0, x1, z0, z1 = PLAZA
    plaza = ((gx > x0) & (gx < x1) & (gz > z0) & (gz < z1)).astype(F32)
    alb = PAVE[None, None] * (1 + tone * fade)[..., None]
    alb = alb * (1 - band[..., None] * 0.22) + PAVE2[None, None] * band[..., None] * 0.22
    alb = alb * plaza[..., None] + ASPH[None, None] * (1 - plaza[..., None])
    # contact shadow along the Feed Tower and the low buildings
    ao = np.ones(gx.shape, F32)
    for nm in ('T1', 'L1', 'R1', 'T3', 'L2'):
        T = CITY_BY[nm]
        dx = np.maximum(np.maximum(T.x0 - gx, gx - T.x1), 0); dz = np.maximum(np.maximum(T.z0 - gz, gz - T.z1), 0)
        ao *= 1 - 0.24 * np.exp(-np.sqrt(dx * dx + dz * dz) / 1.5)
    lk = ctx.lightk(float(ctx.L[1]))
    col = alb * lk[None, None] * ao[..., None]
    if lamp_amt > 0.01:
        acc = np.zeros(gx.shape, F32)
        for (lx, lz, r, k) in lamps:
            acc += k * np.exp(-((gx - lx) ** 2 + (gz - lz) ** 2) / (r * r))
        col += (acc * lamp_amt)[..., None] * hexc('ffb866')[None, None] * alb * 1.5
    if extra_light is not None:
        col += extra_light(gx, gz, alb)
    f = 1 - np.exp(-dist * ctx.fogd)
    col = col * (1 - f[..., None]) + ctx.fog[None, None] * f[..., None]
    col = cv2.resize(col, (W, H), interpolation=cv2.INTER_LINEAR)
    # exact horizon at full resolution
    R = cam.R
    ys = -(np.arange(H, dtype=F32) + 0.5 - cam.cy) / cam.f
    xs = (np.arange(W, dtype=F32) + 0.5 - cam.cx) / cam.f
    dyf = R[0][1] * xs[None, :] + R[1][1] * ys[:, None] + R[2][1]
    okf = dyf < 0
    m = np.clip(-dyf * 400, 0, 1)[..., None]
    img[:] = img * (1 - m) + col * m
    ctx.idb[okf] = GROUND
    ctx.gs = (gx, gz, dist, s)
    return gx, gz, dist


def clip_seg(cam, a, b):
    Pc = cam.to_cam(np.array([a, b], float))
    za, zb = Pc[0, 2], Pc[1, 2]
    n = cam.near
    if za < n and zb < n: return None
    if za < n: Pc[0] = Pc[0] + (Pc[1] - Pc[0]) * (n - za) / (zb - za)
    if zb < n: Pc[1] = Pc[1] + (Pc[0] - Pc[1]) * (n - zb) / (za - zb)
    return cam.proj_c(Pc)


def ground_lines(img8, ctx):
    """Slab joints near the camera as fine lines that fade with distance."""
    cam = ctx.cam
    px, pz = cam.pos[0], cam.pos[2]
    x0, x1, z0, z1 = PLAZA
    near, mid = [], []
    R = 46
    for i in range(int((px - R) // 1.5), int((px + R) // 1.5) + 1):
        x = i * 1.5
        if x <= x0 or x >= x1: continue
        p = clip_seg(cam, np.array([x, 0, max(z0, pz - 3)]), np.array([x, 0, min(z1, pz + R)]))
        if p is not None: (near if abs(x - px) < 12 else mid).append(p)
    for k in range(int((pz - 3) // 1.5), int((pz + R) // 1.5) + 1):
        z = k * 1.5
        if z <= z0 or z >= z1: continue
        p = clip_seg(cam, np.array([max(x0, px - R), 0, z]), np.array([min(x1, px + R), 0, z]))
        if p is not None: (near if z - pz < 14 else mid).append(p)
    base = mix(PAVE * ctx.lightk(float(ctx.L[1])), ctx.ink, 0.28)
    lines(img8, near, mix(base, ctx.fog, 0.12), 1, closed=False)
    lines(img8, mid, mix(base, ctx.fog, 0.5), 1, closed=False)


# ------------------------------------------------------------------ towers
def draw_tower(img8, ctx, T, S):
    cam = ctx.cam
    for nm, C, n, u in T.faces:
        cen = C.mean(0)
        if np.dot(n, cam.pos - cen) <= 0: continue
        sp = screen_poly(cam, C)
        if sp is None: continue
        if sp[:, 0].max() < 0 or sp[:, 0].min() > cam.W or sp[:, 1].max() < 0 or sp[:, 1].min() > cam.H: continue
        dist = float(np.linalg.norm(cen - cam.pos)) if T.kind in ('far', 'farglass') else T.depth_key(cam)
        fid = T.fid + 'SEWNT'.index(nm)
        if nm == 'T':
            fill(img8, [sp], ctx.light(T.alb * 0.78, n, dist)); fill_id(ctx.idb, [sp], fid)
            lines(img8, [sp], ctx.inkc(dist), 1)
            continue
        base = ctx.light(T.alb, n, dist)
        fill(img8, [sp], base); fill_id(ctx.idb, [sp], fid)
        if T.kind not in ('far', 'farglass') and dist < 260:
            ctx.grads.append((fid, sp[:, 1].min(), sp[:, 1].max(), 1.03, 0.9))
        if T.name == 'T1' and nm in ('S', 'W'):
            t1_face(img8, ctx, T, S, nm, C, n, u, dist)
        elif T.kind in ('stone', 'brick', 'glass', 'arcade'):
            facade_simple(img8, ctx, T, S, nm, C, n, u, dist)
        else:
            facade_far(img8, ctx, T, S, nm, C, n, u, dist, sp)
        lines(img8, [sp], ctx.inkc(dist), 2 if dist < 140 else 1)
        nk = S.get('neon', 0.0)
        if nk > 0.01 and not tower_dark(T, S) and dist < 900:
            col = NEON_COLS[(T.seed + 'SEWNT'.index(nm)) % len(NEON_COLS)] * nk
            lines(ctx.glow, [sp], col, 3 if dist < 200 else 2)
            lines(img8, [sp], mix(ctx.inkc(dist), col, 0.85), 1)
    if T.tiers:
        draw_tiers(img8, ctx, T, S)


def draw_tiers(img8, ctx, T, S):
    """Stepped crown (setbacks) on top of a tower."""
    cam = ctx.cam
    y = T.h
    x0, x1, z0, z1 = T.x0, T.x1, T.z0, T.z1
    for inset, hh in T.tiers:
        x0 += inset; x1 -= inset; z0 += inset; z1 -= inset
        faces = box_faces(x0, x1, z0, z1, y + hh, y)
        for nm, C, n, u in sorted(faces, key=lambda f: -np.linalg.norm(f[1].mean(0) - cam.pos)):
            if np.dot(n, cam.pos - C.mean(0)) <= 0: continue
            sp = screen_poly(cam, C)
            if sp is None: continue
            dist = float(np.linalg.norm(C.mean(0) - cam.pos))
            fill(img8, [sp], ctx.light(T.alb * (0.97 if nm != 'T' else 0.8), n, dist)); fill_id(ctx.idb, [sp], T.fid + 5)
            if nm != 'T':
                # tall slit windows in the crown
                cols = max(2, int((np.linalg.norm(C[1] - C[0])) / 3.0))
                Q = quad_grid(C[0] + np.array([0, 1.0, 0]), (C[1] - C[0]) / cols, np.array([0, hh - 2.0, 0]), cols, 1, 0.35, 0.65, 0.0, 1.0)
                S2, z, on = proj_quads(cam, Q)
                gl = ctx.pal['glass'] if ctx.pal['lit'] < 0.15 else hexc('ffd890')
                fill(img8, [S2[i] for i in np.where(on)[0]], ctx.fogged(gl, dist))
            lines(img8, [sp], ctx.inkc(dist), 1)
        y += hh
    # antenna
    cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
    p = clip_seg(cam, np.array([cx, y, cz]), np.array([cx, y + 26, cz]))
    if p is not None:
        dist = float(np.linalg.norm(np.array([cx, y, cz]) - cam.pos))
        lines(img8, [p], ctx.inkc(dist), 2, closed=False)
        if ctx.pal['lit'] > 0.05 or S.get('neon', 0) > 0:
            tip = p[1]
            blink = 0.5 + 0.5 * math.sin(ctx.t * 4.0)
            cv2.circle(ctx.glow, (int(tip[0]), int(tip[1])), 3, c8(hexc('ff3a3a') * blink), -1, AA)
            cv2.circle(img8, (int(tip[0]), int(tip[1])), 2, c8(mix(hexc('ff3a3a'), np.ones(3), 0.3)), -1, AA)


def tower_dark(T, S):
    """After she locks her phone the city goes dark from the Feed Tower outward (radius in metres)."""
    r = S.get('off_wave')
    if r is None: return False
    cx, cz = (T.x0 + T.x1) / 2, (T.z0 + T.z1) / 2
    return math.hypot(cx - 43.5, cz - 43.5) < r


def window_state(T, R, ctx, S):
    """0 glass, 1 lit (warm), 2 screen (slop). Night windows switch on and off over the time-lapse."""
    if tower_dark(T, S): return np.zeros(R['r'].shape, np.int8)
    lit_p = ctx.pal['lit'] * S.get('power', 1.0)
    flick = (np.sin(R['ph'] + ctx.h * 1.7) * 0.5 + 0.5) * 0.25
    st = np.zeros(R['r'].shape, np.int8)
    st[(R['r'] + flick) < lit_p * 1.25] = 1
    slop = S.get('slop_city', 0.0)
    if slop > 0: st[R['r2'] < slop] = 2
    return st


def _glass(ctx, alt, rnd):
    g1, g2 = ctx.pal['glass'], ctx.pal['glass2']
    k = np.clip(alt / 170, 0, 1)[..., None] * 0.6 + rnd[..., None] * 0.25
    return g1[None] * (1 - k) + g2[None] * k


def facade_simple(img8, ctx, T, S, nm, C, n, u, dist):
    """Neighbour towers: punched windows (stone/brick/arcade) or curtain wall (glass), night lights and slop screens."""
    cam = ctx.cam; R = T.rand[nm]
    cols, rows = R['cols'], R['rows']
    o = C[0] + np.array([0, T.lobby, 0]); ex = (C[1] - C[0]) / cols; ey = np.array([0, T.floor, 0.0])
    if T.kind == 'glass':
        Q = quad_grid(o, ex, ey, cols, rows, 0.03, 0.97, 0.12, 0.97)
    elif T.kind == 'arcade':
        Q = quad_grid(o, ex, ey, cols, rows, 0.25, 0.75, 0.15, 0.80)
    else:
        Q = quad_grid(o, ex, ey, cols, rows, 0.22, 0.78, 0.18, 0.86)
    S2, z, on = proj_quads(cam, Q)
    if not on.any(): return
    st = window_state(T, R, ctx, S).reshape(-1)
    alt = np.repeat((np.arange(rows) * T.floor + T.lobby)[:, None], cols, 1).reshape(-1)
    ndl = max(0.0, float(np.dot(n, ctx.L))) * ctx.sunk
    gl = _glass(ctx, alt, R['r'].reshape(-1)) * (0.88 + 0.2 * ndl)
    if T.kind == 'glass':
        gl = gl * 0.75 + ctx.light(T.alb, n, 0) * 0.25
    fogk = 1 - math.exp(-dist * ctx.fogd)
    ws = cam.px_per_m(C.mean(0)) * T.bay
    idx = np.where(on)[0]
    rr2 = R['r2'].reshape(-1)
    groups = {}
    for i in idx:
        s = st[i]
        key = ('L', int(rr2[i] * 4)) if s == 1 else (('S', i % 5) if s == 2 else ('G', int(np.clip(gl[i].mean() * 14, 0, 13))))
        groups.setdefault(key, []).append(i)
    for key, ii in groups.items():
        pts = [S2[i] for i in ii]
        if key[0] == 'L':
            c = mix(hexc('ffcf86') * (0.78 + 0.06 * key[1]), ctx.fog, fogk * 0.6)
            fill(img8, pts, c); fill(ctx.glow, pts, c * 0.5)
        elif key[0] == 'S':
            c = mix(SCREEN_COLS[key[1]], ctx.fog, fogk * 0.4)
            fill(img8, pts, c); fill(ctx.glow, pts, c * (0.35 if ws > 14 else 0.12))
        else:
            fill(img8, pts, mix(gl[ii].mean(0), ctx.fog, fogk))
    if ws > 10 and T.kind != 'glass':
        lines(img8, [S2[i] for i in idx], mix(ctx.inkc(dist), ctx.light(T.alb, n, dist), 0.5), 1)
    if T.kind == 'glass' and ws > 5:
        sl = []
        for r in range(0, rows + 1):
            a = C[0] + np.array([0, T.lobby + r * T.floor, 0]); b = C[1] + np.array([0, T.lobby + r * T.floor, 0])
            p = clip_seg(cam, a, b)
            if p is not None: sl.append(p)
        lines(img8, sl, mix(ctx.inkc(dist), ctx.light(T.alb, n, dist), 0.6), 1, closed=False)
    if T.kind == 'arcade':
        # ground-floor arches: dark openings
        nA = max(2, int(np.linalg.norm(C[1] - C[0]) / 4.0))
        arcs = []
        for k in range(nA):
            a0 = C[0] + (C[1] - C[0]) * (k + 0.18) / nA; a1 = C[0] + (C[1] - C[0]) * (k + 0.82) / nA
            mid = (a0 + a1) / 2; rad = np.linalg.norm(a1 - a0) / 2
            pts = [a0, a0 + np.array([0, 2.6, 0])]
            for j in range(9):
                th = math.pi - math.pi * j / 8
                pts.append(mid + (a1 - a0) / 2 * math.cos(th) / 1 + np.array([0, 2.6 + rad * math.sin(th), 0]) - (a1 - a0) / 2 * 0 )
            pts += [a1 + np.array([0, 2.6, 0]), a1]
            sp = screen_poly(cam, np.array(pts))
            if sp is not None: arcs.append(sp)
        fill(img8, arcs, mix(ctx.light(T.alb * 0.35, n, dist), hexc('ffcf86') * 0.8, clamp(ctx.pal['lit'] * 2.5) * S.get('power', 1.0)))
        lines(img8, arcs, ctx.inkc(dist), 1)


def facade_far(img8, ctx, T, S, nm, C, n, u, dist, sp):
    cam = ctx.cam; R = T.rand[nm]
    cols, rows = R['cols'], R['rows']
    hpx = sp[:, 1].max() - sp[:, 1].min()
    fogk = 1 - math.exp(-dist * ctx.fogd)
    base = ctx.light(T.alb, n, dist)
    if T.kind == 'farglass' and hpx > 30:
        vl = []
        for c in range(0, cols + 1, 2):
            a = C[0] + (C[1] - C[0]) * c / cols; b = a + np.array([0, T.h, 0])
            p = clip_seg(cam, a, b)
            if p is not None: vl.append(p)
        lines(img8, vl, mix(base, ctx.ink, 0.1), 1, closed=False)
    if tower_dark(T, S): return
    lit_p = ctx.pal['lit'] * S.get('power', 1.0)
    slop = S.get('slop_city', 0.0)
    if lit_p < 0.01 and slop < 0.01: return
    o = C[0] + np.array([0, T.lobby, 0]); ex = (C[1] - C[0]) / cols; ey = np.array([0, T.floor, 0.0])
    r = R['r'].reshape(-1); r2 = R['r2'].reshape(-1)
    flick = (np.sin(R['ph'].reshape(-1) + ctx.h * 1.7) * 0.5 + 0.5) * 0.25
    lit = (r + flick) < lit_p * 1.1
    scr = r2 < slop
    sel = np.where(lit | scr)[0]
    if len(sel) == 0: return
    rr, cc = sel // cols, sel % cols
    P = o[None] + (cc[:, None] + 0.5) * ex[None] + (rr[:, None] + 0.5) * ey[None]
    s, zz = cam.proj(P)
    ok = (zz > cam.near) & (s[:, 0] >= 0) & (s[:, 0] < cam.W - 1) & (s[:, 1] >= 0) & (s[:, 1] < cam.H - 1)
    s, sel2 = s[ok], sel[ok]
    if len(s) == 0: return
    col = np.where(scr[sel2][:, None], np.array([SCREEN_COLS[i % 5] for i in sel2]), hexc('ffcf86')[None] * (0.7 + 0.3 * r2[sel2][:, None]))
    col = col * (1 - fogk * 0.55) + ctx.fog * fogk * 0.55
    xi = s[:, 0].astype(int); yi = s[:, 1].astype(int)
    c8a = (np.clip(col, 0, 1) * 255).astype(np.uint8)
    img8[yi, xi] = c8a
    ctx.glow[yi, xi] = (c8a * 0.25).astype(np.uint8)
    if hpx > 260:
        img8[np.clip(yi + 1, 0, cam.H - 1), xi] = c8a; img8[yi, np.clip(xi + 1, 0, cam.W - 1)] = c8a


# ------------------------------------------------------------------ the Feed Tower (hero faces: east 'S' and south 'W')
def _t1_grid(C):
    o = C[0] + np.array([0, T1Y0, 0]); ex = (C[1] - C[0]) / T1_COLS; ey = np.array([0, FLOOR, 0.0])
    return quad_grid(o, ex, ey, T1_COLS, T1_ROWS, 0.16, 0.84, 0.20, 0.90)


T1FACES = {nm: (C, n, u) for nm, C, n, u in box_faces(T1X0, T1X1, T1Z, T1Z + T1D, T1H)[:4]}
T1Q = {nm: _t1_grid(T1FACES[nm][0]) for nm in ('S', 'W')}
T1QF = {nm: quad_grid(T1FACES[nm][0][0] + np.array([0, T1Y0, 0]), (T1FACES[nm][0][1] - T1FACES[nm][0][0]) / T1_COLS,
                      np.array([0, FLOOR, 0.0]), T1_COLS, T1_ROWS, 0.0, 1.0, 0.0, 1.0) for nm in ('S', 'W')}   # whole bays
T1R = {}
for _k, _nm in enumerate(('S', 'W')):
    _r = np.random.default_rng(42 + _k)
    T1R[_nm] = dict(r=_r.random((T1_ROWS, T1_COLS)), r2=_r.random((T1_ROWS, T1_COLS)), blind=_r.random((T1_ROWS, T1_COLS)),
                    ph=_r.random((T1_ROWS, T1_COLS)) * 100, hl=_r.random((T1_ROWS, T1_COLS)))
REVEAL = 0.5


def _lerp4(q, a, b):
    """Point at (a, b) inside a projected quad [bl, br, tr, tl] (bilinear; fine for small quads)."""
    bl, br, tr, tl = q
    return (bl * (1 - a) + br * a) * (1 - b) + (tl * (1 - a) + tr * a) * b


def subquad(q, a0, a1, b0, b1):
    return np.array([_lerp4(q, a0, b0), _lerp4(q, a1, b0), _lerp4(q, a1, b1), _lerp4(q, a0, b1)])


def t1_face(img8, ctx, T, S, nm, C, n, u, dist):
    cam = ctx.cam
    Sq, zz, on = proj_quads(cam, T1Q[nm])
    R = T1R[nm]
    if on.any():
        Ln = float(np.dot(ctx.L, n))
        lit_face = Ln > 0.02 and ctx.sunk > 0
        st = (S.get('t1_state') or {}).get(nm)
        if st is None: st = window_state(T, R, ctx, S)
        elif (st < 0).any():
            st = np.where(st < 0, window_state(T, R, ctx, S), st).astype(np.int8)
        kr = S.get('t1_kill_rows')
        if kr is not None and kr > 0:
            st = st.copy(); st[max(0, T1_ROWS - int(kr)):] = 0
        st = st.reshape(-1)
        alt = np.repeat((np.arange(T1_ROWS) * FLOOR + T1Y0)[:, None], T1_COLS, 1).reshape(-1)
        rnd = R['r'].reshape(-1); hl = R['hl'].reshape(-1); bl = R['blind'].reshape(-1)
        gl = _glass(ctx, alt, rnd)
        ndl = max(0.0, Ln) * ctx.sunk
        fogk = 1 - math.exp(-dist * ctx.fogd)
        idx = np.where(on)[0]
        glass_i = [i for i in idx if st[i] == 0]
        lit_i = [i for i in idx if st[i] == 1]
        scr_i = [i for i in idx if st[i] == 2]
        off_i = [i for i in idx if st[i] == 3]
        let_i = [i for i in idx if st[i] == 4]
        band_i = [i for i in idx if st[i] == 5]
        if off_i: fill(img8, [Sq[i] for i in off_i], hexc('15151d'))
        if glass_i:
            gi = np.array(glass_i)
            q = np.clip((gl[gi].mean(1) * 12).astype(int), 0, 15)
            for k in np.unique(q):
                ii = gi[q == k]
                fill(img8, [Sq[i] for i in ii], mix(gl[ii].mean(0) * (0.92 + 0.15 * ndl), ctx.fog, fogk))
            up = [subquad(Sq[i], 0, 1, 0.45 + 0.35 * hl[i], 1) for i in gi if hl[i] < 0.6]
            fill(img8, up, mix(mix(ctx.pal['glass2'], ctx.pal['m'], 0.3) * (0.95 + 0.1 * ndl), ctx.fog, fogk))
            blinds = [subquad(Sq[i], 0, 1, 1 - (0.12 + bl[i] * 1.4), 1) for i in gi if bl[i] < 0.3]
            fill(img8, blinds, mix(ctx.light(hexc('ece2d0'), n, 0) * 0.92, ctx.fog, fogk))
        if lit_i:
            c = hexc('ffd08a')
            fill(img8, [Sq[i] for i in lit_i], c); fill(ctx.glow, [Sq[i] for i in lit_i], c * 0.45)
            fill(img8, [subquad(Sq[i], 0, 1, 0.9, 1.0) for i in lit_i], hexc('fff3d6'))
            if (cam.px_per_m(C.mean(0)) * BAY) > 22:
                figs = []
                nod = S.get('nod')
                bob = 0.0 if nod is None else -0.05 * (0.5 + 0.5 * math.sin(nod * 2 * math.pi))
                for i in lit_i:
                    if rnd[i] < (0.55 if nod is None else 0.95):
                        cxx = 0.3 + 0.4 * hl[i] if nod is None else 0.5
                        figs.append(subquad(Sq[i], cxx - 0.07, cxx + 0.07, 0.0, 0.42))
                        figs.append(subquad(Sq[i], cxx - 0.045 + 0.03 * (bob != 0), cxx + 0.045 + 0.03 * (bob != 0), 0.42 + bob, 0.56 + bob))
                        if nod is not None:
                            figs.append(subquad(Sq[i], cxx + 0.07, cxx + 0.13, 0.3, 0.36))
                fill(img8, figs, mix(hexc('6a4a3a'), hexc('ffd08a'), 0.25))
        if scr_i:
            S.setdefault('_t1_screens', {})[nm] = (np.array(scr_i), Sq)
            draw_screens(img8, ctx, S, Sq, scr_i, R, nm)
        if lit_face:
            Lt = float(np.dot(ctx.L, u)); Ly = float(ctx.L[1])
            open_w = BAY * 0.68; open_h = FLOOR * 0.70
            hs = clamp(REVEAL * Ly / max(Ln, 1e-3) / open_h, 0, 0.9)
            wsd = clamp(REVEAL * abs(Lt) / max(Ln, 1e-3) / open_w, 0, 0.9)
            if hs > 0.01 or wsd > 0.01:
                col = mix(gl.mean(0) * 0.5, ctx.ink, 0.18)
                for i in glass_i + lit_i:
                    q = Sq[i]
                    if Lt >= 0:
                        P = [_lerp4(q, 0, 1), _lerp4(q, 1, 1), _lerp4(q, 1, 0), _lerp4(q, 1 - wsd, 0), _lerp4(q, 1 - wsd, 1 - hs), _lerp4(q, 0, 1 - hs)]
                    else:
                        P = [_lerp4(q, 0, 0), _lerp4(q, 0, 1), _lerp4(q, 1, 1), _lerp4(q, 1, 1 - hs), _lerp4(q, wsd, 1 - hs), _lerp4(q, wsd, 0)]
                    fill(img8, [np.array(P)], col)
        else:
            fill(img8, [subquad(Sq[i], 0, 1, 0.86, 1) for i in glass_i], mix(gl.mean(0) * 0.6, ctx.ink, 0.15))
        fill(img8, [subquad(Sq[i], -0.04, 1.04, -0.07, 0.0) for i in idx], ctx.light(STONE * 1.06, BU, dist))
        ws = cam.px_per_m(C.mean(0)) * BAY
        if ws > 7:
            lines(img8, [Sq[i] for i in idx], ctx.inkc(dist), 1)
            if ws > 26:
                mull = [np.array([_lerp4(Sq[i], 0.5, 0), _lerp4(Sq[i], 0.5, 1)]) for i in glass_i + lit_i]
                lines(img8, mull, mix(ctx.inkc(dist), gl.mean(0), 0.35), 1, closed=False)
        if ws > 14:
            vl = []
            for c in range(1, T1_COLS):
                a = C[0] + (C[1] - C[0]) * c / T1_COLS
                p = clip_seg(cam, a + np.array([0, T1Y0, 0]), a + np.array([0, T1H, 0]))
                if p is not None: vl.append(p)
            lines(img8, vl, mix(ctx.inkc(dist), ctx.light(STONE, n, dist), 0.72), 1, closed=False)
        if let_i or band_i:
            # light-show cells, drawn over sills and piers: whole bays (window + spandrel), so the letters read as
            # solid strokes on a black band
            Fq, _, _ = proj_quads(cam, T1QF[nm])
            if band_i: fill(img8, [Fq[i] for i in band_i], hexc('121019'))
            if let_i:
                lc = np.asarray(S.get('letter_col', hexc('ff3fbf')), F32)
                cells = [subquad(Fq[i], 0.035, 0.965, 0.045, 0.955) for i in let_i]
                fill(img8, cells, mix(lc, np.ones(3, F32), 0.22)); fill(ctx.glow, cells, lc * 0.8)
    t1_base(img8, ctx, S, nm, C, n, u, dist)


FEED_BG = [hexc('f4f1ea'), hexc('fff7e8'), hexc('eef4ff'), hexc('1c1c28'), hexc('fde9f2')]
FEED_IMG = [hexc('ff8a5c'), hexc('5cc8ff'), hexc('ffd34d'), hexc('b07cff'), hexc('5be3a4'), hexc('ff5f9e'), hexc('7a9cff')]


def draw_screens(img8, ctx, S, Sq, idx, R, nm):
    """Windows that have become screens: each shows a post (card, picture, a heart), glowing."""
    cam = ctx.cam
    rr = R['r2'].reshape(-1); hl = R['hl'].reshape(-1)
    t = ctx.t
    k = float(S.get('screen_k', 1.0))
    by_bg = {}
    for i in idx:
        by_bg.setdefault(int(rr[i] * 997) % len(FEED_BG), []).append(i)
    for bgk, ii in by_bg.items():
        c = FEED_BG[bgk] * (0.75 + 0.25 * k)
        fill(img8, [Sq[i] for i in ii], c); fill(ctx.glow, [Sq[i] for i in ii], c * 0.55 * k)
    # the picture in each post scrolls: its colour changes with time per window
    pics = {}
    for i in idx:
        j = int(rr[i] * 50 + hl[i] * 20 + t * (0.8 + hl[i])) % len(FEED_IMG)
        pics.setdefault(j, []).append(subquad(Sq[i], 0.1, 0.9, 0.3, 0.86))
    for j, qs in pics.items():
        fill(img8, qs, FEED_IMG[j] * (0.7 + 0.3 * k)); fill(ctx.glow, qs, FEED_IMG[j] * 0.35 * k)
    ws = np.linalg.norm(Sq[idx[0]][1] - Sq[idx[0]][0]) if len(idx) else 0
    if ws > 14:
        hearts = [subquad(Sq[i], 0.1, 0.24, 0.1, 0.22) for i in idx]
        fill(img8, hearts, hexc('ff3b6b'))
        lines_ = [np.array([_lerp4(Sq[i], 0.32, 0.17), _lerp4(Sq[i], 0.85, 0.17)]) for i in idx]
        lines(img8, lines_, hexc('9a96a8'), 1, closed=False)


def t1_base(img8, ctx, S, nm, C, n, u, dist):
    """Glass lobby along each hero face, a revolving door on the east face, the LED band wrapping the corner."""
    cam = ctx.cam
    pw = S.get('power', 1.0)
    off = -n * 0.0
    def P(a, y, d=0.0): return C[0] + (C[1] - C[0]) * a + np.array([0, y, 0]) - n * d
    sp = screen_poly(cam, np.array([P(0.03, 0), P(0.97, 0), P(0.97, LOBBY - 0.5), P(0.03, LOBBY - 0.5)]))
    if sp is not None:
        night = clamp(ctx.pal['lit'] * 2.6) * pw
        inside = mix(mix(ctx.pal['glass'], ctx.pal['glass2'], 0.25), hexc('ffd9a0'), night * 0.85)
        fill(img8, [sp], ctx.fogged(inside, dist))
        if night > 0.05: fill(ctx.glow, [sp], hexc('ffd9a0') * night * 0.3)
        mull = []
        for k in range(10):
            p = clip_seg(cam, P(0.03 + 0.94 * k / 9, 0), P(0.03 + 0.94 * k / 9, LOBBY - 0.5))
            if p is not None: mull.append(p)
        p = clip_seg(cam, P(0.03, 3.0), P(0.97, 3.0))
        if p is not None: mull.append(p)
        lines(img8, mull, ctx.inkc(dist), 1, closed=False)
        if nm == 'S':
            dp = screen_poly(cam, np.array([P(0.45, 0, 0.6), P(0.55, 0, 0.6), P(0.55, 2.8, 0.6), P(0.45, 2.8, 0.6)]))
            fill(img8, [dp], ctx.fogged(mix(inside, ctx.ink, 0.25), dist)); lines(img8, [dp], ctx.inkc(dist), 1)
            cp = screen_poly(cam, np.array([P(0.4, 3.0, 1.6), P(0.6, 3.0, 1.6), P(0.6, 3.25, 0), P(0.4, 3.25, 0)]))
            fill(img8, [cp], ctx.light(hexc('2b2a33'), BU, dist)); lines(img8, [cp], ctx.inkc(dist), 1)
        lines(img8, [sp], ctx.inkc(dist), 2)
    band = np.array([P(0.0, LOBBY + 0.45, 0.06), P(1.0, LOBBY + 0.45, 0.06), P(1.0, LOBBY + 1.95, 0.06), P(0.0, LOBBY + 1.95, 0.06)])
    sp = screen_poly(cam, band)
    if sp is not None:
        fill(img8, [sp], mix(hexc('171a2a'), ctx.fog, 1 - math.exp(-dist * ctx.fogd)))
        fill_id(ctx.idb, [sp], LEDB)
        S.setdefault('_led_band', {})[nm] = (band, sp)
        lines(img8, [sp], ctx.inkc(dist), 1)


# ------------------------------------------------------------------ props
LAMPS = [fs(3.2, 2.6), fs(14, -7), fs(18, 9), fs(-3, -6.5), fs(30, -3), fs(27, 15), fs(40, 6), fs(8, -16), fs(-6, 9)]
TREES = [(*fs(8, -9), 6.4, 2.3), (*fs(13, 11.5), 5.8, 2.1), (*fs(25, -15), 6.9, 2.5), (*fs(-1, -14), 6.0, 2.2), (*fs(34, 17), 6.3, 2.2)]
KIOSK = fs(21, -8)


def draw_lamp(img8, ctx, x, z, on):
    cam = ctx.cam
    dist = float(np.linalg.norm(np.array([x, 2, z]) - cam.pos))
    poleW = 0.065
    pole = np.array([(x - poleW, 0, z), (x + poleW, 0, z), (x + poleW * 0.7, 4.6, z), (x - poleW * 0.7, 4.6, z)])
    sp = screen_poly(cam, pole)
    if sp is None: return
    col = ctx.light(hexc('34343f'), np.array([0, 0, -1.0]), dist)
    fill(img8, [sp], col)
    base = screen_poly(cam, np.array([(x - 0.14, 0, z), (x + 0.14, 0, z), (x + 0.1, 0.38, z), (x - 0.1, 0.38, z)]))
    fill(img8, [base], col)
    head = screen_poly(cam, np.array([(x - 0.42, 4.55, z), (x + 0.42, 4.55, z), (x + 0.36, 4.72, z), (x - 0.36, 4.72, z)]))
    fill(img8, [head], col)
    lw = 1 if dist > 16 else 2
    lines(img8, [sp, head, base], ctx.inkc(dist), lw)
    if on > 0.01:
        lp = screen_poly(cam, np.array([(x - 0.34, 4.50, z), (x + 0.34, 4.50, z), (x + 0.34, 4.555, z), (x - 0.34, 4.555, z)]))
        fill(img8, [lp], mix(col, hexc('fff4d8'), on)); fill(ctx.glow, [lp], hexc('ffe3a8') * on)
        cc = cam.proj(np.array([[x, 4.45, z]]))[0][0]
        r = max(2, int(cam.px_per_m(np.array([x, 4.4, z])) * 0.35))
        cv2.circle(ctx.glow, (int(cc[0]), int(cc[1])), r, c8(hexc('ffe3a8') * 0.45 * on), -1, AA)


def bench_profile(xf, xb):
    """End silhouette of the bench (x, y): legs, seat bracket, armrest and the raked back."""
    return [(xf - 0.03, 0.0), (xf + 0.02, 0.0), (xf - 0.01, 0.40), (xf + 0.03, 0.42), (xf + 0.05, 0.60), (xf + 0.01, 0.645),
            (xf - 0.06, 0.62), (xf - 0.05, 0.46), (xb + 0.04, 0.46), (xb - 0.08, 0.96), (xb - 0.115, 0.95), (xb - 0.02, 0.45),
            (xb - 0.06, 0.0), (xb - 0.01, 0.0), (xb + 0.04, 0.38), (xf - 0.06, 0.38)]


BENCH = dict(z0=-1.05, z1=0.95, xf=0.26, xb=-0.28)


def rbox_faces(cx, cz, w, d, h, y0=0.0):
    """Faces of a box turned like the bench: w along BF (her facing), d along BA (away from the master camera)."""
    c = np.array([cx, 0.0, cz])
    def P(a, y, b): return c + BF * a + BU * y + BA * b
    a0, a1, b0, b1 = -w / 2, w / 2, -d / 2, d / 2
    return [
        ('F', np.array([P(a0, y0, b0), P(a1, y0, b0), P(a1, h, b0), P(a0, h, b0)]), -BA),   # faces the master camera
        ('R', np.array([P(a1, y0, b0), P(a1, y0, b1), P(a1, h, b1), P(a1, h, b0)]), BF),
        ('L', np.array([P(a0, y0, b1), P(a0, y0, b0), P(a0, h, b0), P(a0, h, b1)]), -BF),
        ('B', np.array([P(a1, y0, b1), P(a0, y0, b1), P(a0, h, b1), P(a1, h, b1)]), BA),
        ('T', np.array([P(a0, h, b0), P(a1, h, b0), P(a1, h, b1), P(a0, h, b1)]), BU),
    ]


def rbox_pts(cx, cz, w, d, h, y0=0.0):
    c = np.array([cx, 0.0, cz])
    return [c + BF * a + BU * y + BA * b for a in (-w / 2, w / 2) for y in (y0, h) for b in (-d / 2, d / 2)]


def draw_bench(img8, ctx, extra=None):
    """Classic park bench seen end-on: cast-iron end frames + wooden slats running away from camera."""
    cam = ctx.cam
    z0, z1, xf, xb = BENCH['z0'], BENCH['z1'], BENCH['xf'], BENCH['xb']
    iron = hexc('26252e'); wood = hexc('a06c45')
    dist = float(np.linalg.norm(bw(0, 0.5, z0) - cam.pos))
    nface = -BA; top = BU; side_n = -BF
    slats = []
    for k in range(4):
        slats.append((xb + 0.05 + k * 0.125, 0.42, 0.105, 0.035))
    for k in range(3):
        y = 0.60 + k * 0.12
        slats.append((xb - 0.04 - (y - 0.55) * 0.16, y, 0.032, 0.095))
    P = bwa(np.array([(px, py, z1) for px, py in bench_profile(xf, xb)]))
    sp = screen_poly(cam, P)
    fill(img8, [sp], ctx.light(iron, nface, dist)); lines(img8, [sp], ctx.inkc(dist), 1)
    for (x, y, w, h) in slats:
        topq = bwa(np.array([(x, y + h, z0 + 0.03), (x + w, y + h, z0 + 0.03), (x + w, y + h, z1 - 0.03), (x, y + h, z1 - 0.03)]))
        side = bwa(np.array([(x, y, z0 + 0.03), (x, y, z1 - 0.03), (x, y + h, z1 - 0.03), (x, y + h, z0 + 0.03)]))
        endq = bwa(np.array([(x, y, z0 + 0.03), (x + w, y, z0 + 0.03), (x + w, y + h, z0 + 0.03), (x, y + h, z0 + 0.03)]))
        st = screen_poly(cam, topq); sd = screen_poly(cam, side); se = screen_poly(cam, endq)
        fill(img8, [sd], ctx.light(wood * 0.7, side_n, dist))
        fill(img8, [st], ctx.light(wood * 1.05, top, dist)); fill(img8, [se], ctx.light(wood * 0.8, nface, dist))
        lines(img8, [st, se], ctx.inkc(dist), 1)
    if extra: extra(img8, ctx)
    P = bwa(np.array([(px, py, z0) for px, py in bench_profile(xf, xb)]))
    sp = screen_poly(cam, P)
    fill(img8, [sp], ctx.light(iron, nface, dist)); lines(img8, [sp], ctx.inkc(dist), 1)


def draw_tree(img8, ctx, x, z, h=6.0, r=2.2, seed=0):
    cam = ctx.cam
    dist = float(np.linalg.norm(np.array([x, h * 0.6, z]) - cam.pos))
    nf = np.array([0, 0, -1.0])
    vis = []
    for nm, C, n in rbox_faces(x, z, 2.0, 2.0, 0.55):
        if np.dot(n, cam.pos - C.mean(0)) <= 0: continue
        sp = screen_poly(cam, C)
        if sp is None: continue
        fill(img8, [sp], ctx.light(hexc('5e4f40') if nm == 'T' else hexc('d2c7b5'), n, dist)); vis.append(sp)
    if not vis: return
    lines(img8, vis, ctx.inkc(dist), 1)
    trunk = screen_poly(cam, np.array([(x - 0.11, 0.5, z), (x + 0.11, 0.5, z), (x + 0.07, h * 0.62, z), (x - 0.07, h * 0.62, z)]))
    fill(img8, [trunk], ctx.light(hexc('4f3e31'), nf, dist)); lines(img8, [trunk], ctx.inkc(dist), 1)
    # canopy: a bumpy silhouette (union of clumps) with one ink outline; light side by an offset union; inner arcs
    rng = np.random.default_rng(seed)
    cc = cam.proj(np.array([[x, h * 0.74, z]]))[0][0]
    ppm = cam.px_per_m(np.array([x, h * 0.74, z]))
    R = r * ppm
    if R < 3: return
    x0 = int(max(0, cc[0] - 1.9 * R)); x1 = int(min(cam.W, cc[0] + 1.9 * R))
    y0 = int(max(0, cc[1] - 1.9 * R)); y1 = int(min(cam.H, cc[1] + 1.7 * R))
    if x1 - x0 < 4 or y1 - y0 < 4: return
    sx = float(np.dot(ctx.L, cam.R[0])) if ctx.sunk > 0 else -0.3
    ldx = 0.5 * np.sign(sx) if abs(sx) > 0.08 else -0.25
    leaf = hexc('5a7a48')
    lit = ctx.light(leaf * 1.15, nrm(BU * 0.9 + cam.R[0] * np.sign(sx) * 0.4), dist)
    shd = ctx.fogged(leaf * ctx.lightk(0) * 0.9, dist)
    deep = ctx.fogged(leaf * ctx.lightk(0) * 0.62, dist)
    clumps = []
    for k in range(9):
        a = k / 9 * 2 * math.pi + rng.uniform(-0.3, 0.3); rr = rng.uniform(0.35, 0.62) * R
        clumps.append((cc[0] - x0 + math.cos(a) * rr * 1.05, cc[1] - y0 + math.sin(a) * rr * 0.78, rng.uniform(0.38, 0.52) * R))
    clumps.append((cc[0] - x0, cc[1] - y0, 0.62 * R))
    hh, ww = y1 - y0, x1 - x0
    sil = np.zeros((hh, ww), np.uint8); litm = np.zeros((hh, ww), np.uint8); dm = np.zeros((hh, ww), np.uint8)
    for (u, v, rad) in clumps:
        cv2.circle(sil, (int(u * 4), int(v * 4)), int(rad * 4), 255, -1, AA, 2)
        cv2.circle(litm, (int((u + ldx * rad * 0.42) * 4), int((v - rad * 0.38) * 4)), int(rad * 0.86 * 4), 255, -1, AA, 2)
        cv2.circle(dm, (int((u - ldx * rad * 0.2) * 4), int((v + rad * 0.55) * 4)), int(rad * 0.7 * 4), 255, -1, AA, 2)
    sm = sil.astype(F32) / 255
    lm = (litm.astype(F32) / 255) * sm
    dmk = (dm.astype(F32) / 255) * sm * (1 - lm) * 0.8
    col = shd[None, None] * (1 - lm[..., None]) + lit[None, None] * lm[..., None]
    col = col * (1 - dmk[..., None]) + deep[None, None] * dmk[..., None]
    sub = img8[y0:y1, x0:x1]
    sub[:] = to_8(sub.astype(F32) / 255 * (1 - sm[..., None]) + col * sm[..., None])
    cnts, _ = cv2.findContours((sil > 127).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    cv2.drawContours(sub, cnts, -1, c8(ctx.inkc(dist)), 1, AA)
    # a few interior clump arcs on the shaded side
    for (u, v, rad) in clumps[:4]:
        cv2.ellipse(sub, (int(u), int(v)), (int(rad * 0.9), int(rad * 0.9)), 0, 20, 110, c8(mix(ctx.inkc(dist), shd, 0.45)), 1, AA)


def draw_kiosk(img8, ctx, x, z):
    """Newsstand: a green box with a slanted canopy and racks of papers facing the master camera."""
    cam = ctx.cam
    w, d, h = 3.2, 2.0, 2.5
    dist = float(np.linalg.norm(np.array([x, 1.2, z]) - cam.pos))
    body = hexc('2f5a4c')
    faces = rbox_faces(x, z, w, d, h)
    for nm, C, n in sorted(faces, key=lambda f: -np.linalg.norm(f[1].mean(0) - cam.pos)):
        if np.dot(n, cam.pos - C.mean(0)) <= 0: continue
        sp = screen_poly(cam, C)
        fill(img8, [sp], ctx.light(body, n, dist)); lines(img8, [sp], ctx.inkc(dist), 1)
    c = np.array([x, 0.0, z])
    def P(a, y, b): return c + BF * a + BU * y + BA * b
    can = screen_poly(cam, np.array([P(-w / 2 - 0.25, h + 0.05, -d / 2 - 0.7), P(w / 2 + 0.25, h + 0.05, -d / 2 - 0.7),
                                     P(w / 2 + 0.25, h + 0.35, -d / 2 + 0.2), P(-w / 2 - 0.25, h + 0.35, -d / 2 + 0.2)]))
    fill(img8, [can], ctx.light(hexc('b6463e'), nrm(BU - BA * 0.4), dist)); lines(img8, [can], ctx.inkc(dist), 1)
    sps = []
    for r in range(3):
        for cc in range(6):
            px = -w / 2 + 0.2 + cc * 0.47; py = 0.5 + r * 0.6
            sps.append(screen_poly(cam, np.array([P(px, py, -d / 2 - 0.02), P(px + 0.38, py, -d / 2 - 0.02),
                                                  P(px + 0.38, py + 0.5, -d / 2 - 0.02), P(px, py + 0.5, -d / 2 - 0.02)])))
    tints = ['f2efe6', 'f6e7a8', 'efe9e0', 'f1c9c0', 'e8eef2', 'f4f0d0']
    nf = -BA
    for i, sq in enumerate(sps):
        if sq is None: continue
        fill(img8, [sq], ctx.light(hexc(tints[i % 6]), nf, dist))
        fill(img8, [subquad(sq, 0, 1, 0.78, 1)], ctx.light(hexc('c8352e') if i % 3 == 0 else hexc('1d1d26'), nf, dist))
    lines(img8, [sq for sq in sps if sq is not None], ctx.inkc(dist), 1)


# ------------------------------------------------------------------ sun shadows (ground)
def shadow_box_on_ground(L, x0, x1, z0, z1, h):
    if L[1] <= 0.01: return None
    P = []
    k = h / L[1]
    for x in (x0, x1):
        for z in (z0, z1):
            P.append((x, z)); P.append((x - L[0] * k, z - L[2] * k))
    hull = cv2.convexHull(np.array(P, np.float32)).reshape(-1, 2)
    return np.array([(p[0], 0.0, p[1]) for p in hull])


def shadow_on_plane(L, pts, axis, val):
    """Project 3D points away from the sun onto the plane {axis = val}; convex hull as a 3D polygon (or None)."""
    pts = np.asarray(pts, float)
    if abs(L[axis]) < 1e-4: return None
    s = (pts[:, axis] - val) / L[axis]
    if (s <= 0).all(): return None
    s = np.maximum(s, 0)
    Q = pts - L[None] * s[:, None]
    other = [i for i in range(3) if i != axis]
    hull = cv2.convexHull(Q[:, other].astype(np.float32)).reshape(-1, 2)
    out = np.zeros((len(hull), 3)); out[:, other[0]] = hull[:, 0]; out[:, other[1]] = hull[:, 1]; out[:, axis] = val
    return out


def _box_pts(x0, x1, z0, z1, h, y0=0.0):
    return [(x, y, z) for x in (x0, x1) for y in (y0, h) for z in (z0, z1)]


def draw_sun_shadows(ctx):
    if ctx.sunk <= 0.01 or ctx.L[1] <= 0.003: return
    cam = ctx.cam; L = ctx.L
    ctx.shf = np.zeros_like(ctx.sh)
    g, f = [], []
    def add(pts, ground=True, facade=True):
        if ground:
            P = shadow_on_plane(L, pts, 1, 0.0)
            if P is not None: g.append(screen_poly(cam, P))
        if facade and L[2] < -0.02:
            pts_a = np.asarray(pts, float)
            if pts_a[:, 2].max() < T1Z:
                P = shadow_on_plane(L, pts, 2, T1Z)
                if P is not None: f.append(screen_poly(cam, P))
    for T in CITY:
        if T.casts and T.name != 'T1': add(_box_pts(T.x0, T.x1, T.z0, T.z1, T.h))
    T1 = CITY_BY['T1']
    add(_box_pts(T1.x0, T1.x1, T1.z0, T1.z1, T1.h), facade=False)
    for (x, z) in LAMPS:
        w = 0.065
        add([(x - w, 0, z - w), (x + w, 0, z + w), (x - w, 4.6, z - w), (x + w, 4.6, z + w)])
        add([(x - 0.42, 4.55, z - 0.06), (x + 0.42, 4.55, z + 0.06), (x - 0.42, 4.72, z + 0.06), (x + 0.42, 4.72, z - 0.06)])
    for (x, z, h, r) in TREES:
        ang = np.linspace(0, 2 * math.pi, 18, endpoint=False)
        crown = [(x + math.cos(a) * r * 0.8, h * 0.74 + math.sin(a) * r * 0.62, z + math.sin(a * 2.1) * r * 0.5) for a in ang]
        add(crown)
        add([(x - 0.1, 0.5, z - 0.1), (x + 0.1, 0.5, z + 0.1), (x - 0.08, h * 0.62, z - 0.08), (x + 0.08, h * 0.62, z + 0.08)])
        add(rbox_pts(x, z, 2.0, 2.0, 0.55))
    add(rbox_pts(KIOSK[0], KIOSK[1], 3.2, 2.0, 2.85))
    add([bw(x, y, z) for x in (BENCH['xb'] - 0.05, BENCH['xf']) for y in (0.0, 0.46) for z in (BENCH['z0'], BENCH['z1'])], facade=False)
    for p in g:
        if p is not None: fill(ctx.sh, [p], 255)        # one call each: overlapping polygons in one call would XOR
    for p in f:
        if p is not None: fill(ctx.shf, [p], 255)


def apply_shadows(img, ctx):
    """Darken visible ground / Feed Tower front where the sun is blocked; gradients on tall faces."""
    if ctx.sunk > 0.01:
        sh = ctx.sh.astype(F32) / 255
        ndl_g = float(ctx.L[1]); ndl_f = float(np.dot(ctx.L, np.array([0, 0, -1.0])))
        kg = ctx.lightk(0) / np.maximum(ctx.lightk(ndl_g), 1e-3)
        m = (sh * (ctx.idb == GROUND))[..., None]
        img[:] = img * (1 - m) + img * kg[None, None] * m
        if ndl_f > 0 and getattr(ctx, 'shf', None) is not None:
            kf = ctx.lightk(0) / np.maximum(ctx.lightk(ndl_f), 1e-3)
            m = ((ctx.shf.astype(F32) / 255) * (ctx.idb == T1F))[..., None]
            img[:] = img * (1 - m) + img * kf[None, None] * m
    H = img.shape[0]
    for fid, ytop, ybot, ktop, kbot in ctx.grads:
        if ybot - ytop < 20: continue
        r0, r1 = max(0, int(ytop)), min(H, int(math.ceil(ybot)))
        if r1 <= r0: continue
        sub = ctx.idb[r0:r1] == fid
        if not sub.any(): continue
        rows = np.arange(r0, r1, dtype=F32)[:, None]
        g = ktop + (kbot - ktop) * np.clip((rows - ytop) / (ybot - ytop), 0, 1) ** 1.4
        k = np.where(sub, g, 1.0).astype(F32)
        img[r0:r1] *= k[..., None]
    return img
