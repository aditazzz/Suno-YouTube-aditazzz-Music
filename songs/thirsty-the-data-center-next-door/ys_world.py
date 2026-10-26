"""The valley: one town, one river, two facilities, a pylon line, all in one world so every shot is a camera in it.

Layout (metres, +Y up). The river runs along X near z = 0. The town is on the near bank (z < 0); her house sits on
the bank at HOUSE. The facility ("the big gray house") is across the river and upstream (z > 0, x < 0); the second
facility rises next door, further upstream. A road bridge crosses at x = 0. Power comes in on a pylon line from the
far hills to a substation in front of the facility; a feeder line crosses the river into town.

render(cam, S, t) draws the whole valley for state S (see default_state()).
"""
import math
from functools import lru_cache
import numpy as np, cv2
import ys_eng as E
from ys_eng import F32, hexc, sample, fbm_tex, nrm, sstep, clamp
import ys_sky as SK

# ---------------------------------------------------------------- layout
RIVER_W = 27.0          # half width at the top of the banks
RIVER_BED_W = 13.0      # half width of the flat bed
RIVER_D = 3.4           # bed depth
def river_zc(x): return 16.0 * np.sin(np.asarray(x, F32) / 260.0 + 0.6) + 7.0 * np.sin(np.asarray(x, F32) / 97.0 + 1.3)

MONO_A = dict(x0=-800.0, x1=-440.0, z0=230.0, z1=390.0, h=62.0)     # the facility
MONO_B = dict(x0=-1260.0, x1=-900.0, z0=250.0, z1=410.0, h=62.0)   # the second house
HOUSE = np.array([-150.0, 0.0, -52.0], F32)                         # her house (front faces +z, the river)
BRIDGE_X = 0.0
SUBSTATION = np.array([-380.0, 0.0, 150.0], F32)
FENCE_Z = 172.0                                                     # the perimeter fence in front of the facility
GATE = np.array([-618.0, 0.0, FENCE_Z], F32)                        # the gate on the road from the bridge
BOOTH = np.array([-606.0, 0.0, FENCE_Z - 4.0], F32)                 # her cousin's booth, just outside the gate
SCHOOL = np.array([260.0, 0.0, -330.0], F32)
TOWER = np.array([110.0, 0.0, -430.0], F32)                         # water tower
CHURCH = np.array([-40.0, 0.0, -260.0], F32)

# ---------------------------------------------------------------- state
def default_state():
    return dict(dusk=0.0, sun_az=-0.35, glow=1.0, glow_az=-1.25, cloud=0.55, cloud_t=0.0, stars=0.5,
                water=-0.7,          # water level (m, 0 = bank top); drops to about -3.3 (a trickle in the bed)
                dry=0.0,             # 0..1 how dried/cracked the exposed bed is
                breath=0.5,          # facility light-seam intensity 0..1 (the breathing)
                mono_lights=1.0,     # 0 = every facility light out
                red_slit=0.0,        # the thin red light in the facade (intro / outro)
                red_point=0.0,       # the one red point that remains
                second=0.0,          # 0..1 the second house rising
                town_lights=1.0,     # town window/street lights multiplier
                street_dim=0.0,      # 0..1 streetlights dimming one by one
                blue=0.0,            # 0..1 windows turning blue one by one (outro)
                house_lamp=1.0,      # her window
                plumes=1.0, fog=1.0, fog_col=None, exposure=1.0, ripple=0.0, surge=0.0, wind=0.0)

# ---------------------------------------------------------------- deterministic town
@lru_cache(1)
def town():
    r = np.random.default_rng(42)
    houses = []
    # streets: a loose grid on the near bank, rotated a little; skip the river, the school, the church plots
    rot = 0.12
    for gi in range(-14, 16):
        for gj in range(1, 22):
            if r.random() < 0.18: continue
            x = gi * 34.0 + r.normal(0, 3); z = -40.0 - gj * 30.0 + r.normal(0, 3)
            xr = x * math.cos(rot) - (z + 60) * math.sin(rot); zr = x * math.sin(rot) + (z + 60) * math.cos(rot) - 60
            if zr > river_zc(xr) - RIVER_W - 16: continue
            if np.hypot(xr - SCHOOL[0], zr - SCHOOL[2]) < 70 or np.hypot(xr - CHURCH[0], zr - CHURCH[2]) < 30: continue
            if np.hypot(xr - TOWER[0], zr - TOWER[2]) < 16: continue
            if np.hypot(xr - HOUSE[0], zr - HOUSE[2]) < 30: continue
            if abs(xr - BRIDGE_X) < 12: continue
            w = r.uniform(8, 12); d = r.uniform(9, 14); h = r.choice([3.2, 3.4, 5.8, 6.2], p=[0.35, 0.25, 0.2, 0.2])
            pitch = r.uniform(0.45, 0.8); turn = r.random() < 0.3
            wall = hexc(r.choice(['8d8a80', '9a8f7a', '7f8a8f', 'a39b8b', '6f6a64', 'b0a48c']))
            roofc = hexc(r.choice(['2b2a2c', '3a3330', '2e3236', '403a36']))
            nwin = int(r.integers(1, 4))
            wins = []
            for k in range(nwin):
                wins.append(dict(u=r.uniform(-0.32, 0.32), v=r.uniform(0.25, 0.55) if h < 4 else r.choice([0.22, 0.62]),
                                 lit=r.random() < 0.62, warm=r.uniform(0.6, 1.0), seed=r.random()))
            houses.append(dict(c=np.array([xr, 0, zr], F32), w=w, d=d, h=h, pitch=pitch, turn=turn, wall=wall, roof=roofc,
                               wins=wins, porch=r.random() < 0.5, order=r.random(), ang=rot + (math.pi / 2 if turn else 0)))
    trees = []
    for k in range(900):
        if k < 380:   # riparian: along the banks
            x = r.uniform(-1700, 900); z = float(river_zc(x)) + r.choice([-1, 1]) * r.uniform(RIVER_W + 4, RIVER_W + 30)
        else:
            x = r.uniform(-1600, 900); z = r.uniform(-900, 600)
        dzr = z - river_zc(x)
        near_river = abs(dzr) < RIVER_W + 22
        if abs(dzr) < RIVER_W + 3: continue
        if (MONO_A['x0'] - 25 < x < MONO_A['x1'] + 25 and MONO_A['z0'] - 25 < z < MONO_A['z1'] + 25): continue
        if (MONO_B['x0'] - 25 < x < MONO_B['x1'] + 25 and MONO_B['z0'] - 25 < z < MONO_B['z1'] + 25): continue
        if z > 30 and r.random() < 0.6 and not near_river: continue
        if abs(x - BRIDGE_X) < 14 and abs(dzr) < 60: continue
        if dzr > 0 and -1340 < x < -380 and r.random() > 0.3: continue
        if np.hypot(x - HOUSE[0], z - HOUSE[2]) < 16: continue
        if np.hypot(x - SCHOOL[0], z - SCHOOL[2]) < 60: continue
        trees.append((x, z, r.uniform(5, 11) * (1.25 if near_river else 1.0), r.uniform(4, 8), r.random()))
    streetlights = []
    for gi in range(-14, 16, 2):
        for gj in range(1, 22, 2):
            x = gi * 34.0 + 17; z = -40.0 - gj * 30.0 + 15
            xr = x * math.cos(rot) - (z + 60) * math.sin(rot); zr = x * math.sin(rot) + (z + 60) * math.cos(rot) - 60
            if zr > river_zc(xr) - RIVER_W - 8: continue
            streetlights.append((xr, zr, r.random()))
    # river road lights on the near bank
    for x in np.arange(-700, 700, 42.0):
        streetlights.append((float(x), float(river_zc(x) - RIVER_W - 9), r.random()))
    return dict(houses=houses, trees=trees, streetlights=np.array(streetlights, F32))

# ---------------------------------------------------------------- ground + river (per pixel)
@lru_cache(1)
def ground_maps():
    """top-down albedo map over x in [-2048, 2048], z in [-2048, 2048] at 2 m/px: fields, yards, streets."""
    n = 2048; s = 2.0
    f1 = cv2.resize(fbm_tex(512, 2.4, 31), (n, n)); f2 = cv2.resize(fbm_tex(512, 1.8, 32), (n, n))
    alb = np.empty((n, n, 3), F32)
    grass = hexc('2f3a2a'); field = hexc('4a4532'); dry = hexc('5d5442')
    m = f1[..., None]
    alb[:] = grass * (1 - m) + field * m
    alb = alb * (0.8 + 0.4 * f2[..., None])
    # streets of the town grid (rotated), the river road, the far-bank road to the gate
    lay = np.zeros((n, n), np.uint8)
    rot = 0.12
    def w2m(x, z): return (int((x + 2048) / s), int((z + 2048) / s))
    for gi in range(-15, 17):
        x = gi * 34.0 - 17
        a = (x * math.cos(rot) - (0) * math.sin(rot), x * math.sin(rot) - 60)
        pts = []
        for z in (-40.0, -720.0):
            xr = x * math.cos(rot) - (z + 60) * math.sin(rot); zr = x * math.sin(rot) + (z + 60) * math.cos(rot) - 60
            pts.append(w2m(xr, zr))
        cv2.line(lay, pts[0], pts[1], 255, 3)
    for gj in range(0, 23):
        z = -40.0 - gj * 30.0 + 15
        pts = []
        for x in (-500.0, 560.0):
            xr = x * math.cos(rot) - (z + 60) * math.sin(rot); zr = x * math.sin(rot) + (z + 60) * math.cos(rot) - 60
            pts.append(w2m(xr, zr))
        cv2.line(lay, pts[0], pts[1], 255, 3)
    xs = np.arange(-2000, 2000, 8.0)
    near = np.array([w2m(x, river_zc(x) - RIVER_W - 6) for x in xs], np.int32)
    far = np.array([w2m(x, river_zc(x) + RIVER_W + 10) for x in xs], np.int32)
    cv2.polylines(lay, [near], False, 255, 4); cv2.polylines(lay, [far], False, 255, 4)
    cv2.line(lay, w2m(BRIDGE_X, -900), w2m(BRIDGE_X, 40), 255, 5)
    cv2.line(lay, w2m(GATE[0], GATE[2]), w2m(GATE[0], river_zc(GATE[0]) + RIVER_W + 10), 255, 5)
    road = cv2.GaussianBlur(lay.astype(F32) / 255, (0, 0), 0.8)[..., None]
    alb = alb * (1 - road) + hexc('242528') * road
    # facility pads: concrete aprons
    for M in (MONO_A, MONO_B):
        a = w2m(M['x0'] - 30, M['z0'] - 22); b = w2m(M['x1'] + 30, M['z1'] + 30)
        pad = np.zeros((n, n), F32); cv2.rectangle(pad, a, b, 1.0, -1); pad = cv2.GaussianBlur(pad, (0, 0), 2)[..., None]
        alb = alb * (1 - pad * 0.85) + hexc('3d3f41') * pad * 0.85
    return alb.astype(F32), road[..., 0].astype(F32)

def thalweg_off(x):
    """the low-water channel meanders inside the flat bed (offset from the centreline, m)."""
    return 6.0 * np.sin(np.asarray(x, F32) / 70.0 + 1.1) + 2.5 * np.sin(np.asarray(x, F32) / 23.0 + 0.4)

def _bed(d, nz, ds=None, x=None):
    """river bed height at lateral distance d from the centreline (+ noise for puddles and bars). With the signed
    offset ds and x, the flat bed also gets the narrow, deeper low-water channel (what is left at the end)."""
    slope = np.clip((RIVER_W - d) / (RIVER_W - RIVER_BED_W), 0, 1)
    b = -RIVER_D * slope + (nz - 0.5) * 0.9 * slope
    if ds is not None:
        q = (ds - thalweg_off(x)) / 3.2
        b = b - 0.75 * np.exp(-q * q) * slope + 0.25 * slope * (1 - np.exp(-q * q * 0.25))
    return b.astype(F32)

def ground_and_river(cv, S, t, refl=None):
    """ground plane + river channel for every pixel that has no depth yet and looks down."""
    cam = cv.cam
    h = float(S['water'])
    D, k = cam.dirs()
    rows = np.nonzero((D[:, :, 1] < 0).any(1) & (~np.isfinite(cv.dep)).any(1))[0]
    if len(rows) == 0: return None
    r0, r1 = int(rows[0]), int(rows[-1]) + 1
    sub = CropView(cv, r0, r1)
    w = _ground_and_river(sub, S, t, None if refl is None else refl[r0:r1])
    cv.water_mask = np.zeros(cv.dep.shape, bool)
    if w is not None: cv.water_mask[r0:r1] = w
    return cv.water_mask

class CropView:
    """a horizontal slice of a canvas (rows r0:r1) with a matching camera, for per-pixel passes."""
    def __init__(s, cv, r0, r1):
        c = E.Cam.__new__(E.Cam); c.__dict__.update(cv.cam.__dict__)
        c.H = r1 - r0; c.cy = cv.cam.cy - r0
        D, k = cv.cam.dirs(); c._dirs = (D[r0:r1], k[r0:r1])
        s.cam = c; s.img = cv.img[r0:r1]; s.dep = cv.dep[r0:r1]; s.emis = cv.emis[r0:r1]; s.W = cv.W; s.H = r1 - r0

def _ground_and_river(cv, S, t, refl=None):
    cam = cv.cam; D, k = cam.dirs()
    h = float(S['water'])
    tw, Xw, Zw, okw = E.plane_hit(cam, h)
    empty = ~np.isfinite(cv.dep)
    if cam.eye[1] > 0:
        tg, Xg, Zg, okg = E.plane_hit(cam, 0.0)
        free = okg & empty
        if not free.any(): return None
        dg = np.abs(Zg - river_zc(Xg))
        inside = free & (dg < RIVER_W)
    else:
        # the camera is down in the channel (at the waterline): rays that climb out over a bank hit that bank's
        # wall unless they clear the top; rays going down meet the water / the bed
        tg, Xg, Zg, okg = E.plane_hit(cam, 0.0)                    # from below: where a climbing ray reaches y = 0
        dg = np.abs(Zg - river_zc(Xg))
        bank = okg & empty & (dg >= RIVER_W)                       # it reached the bank top outside the channel: a wall
        down = okw & empty
        free = bank | down
        if not free.any(): return None
        inside = down
    # ---- ground (outside the channel)
    alb, road = ground_maps()
    g = free & ~inside
    out_col = np.zeros_like(cv.img)
    if g.any():
        u = (Xg + 2048) / 2.0; v = (Zg + 2048) / 2.0
        a = cv2.remap(alb, np.where(g, u, 0).astype(F32), np.where(g, v, 0).astype(F32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        det = sample(fbm_tex(512, 1.2, 33), Xg, Zg, 512 / 40.0)
        a = a * (0.75 + 0.5 * det[..., None])
        out_col = a * ambient_light(S)[None, None] * 1.0 + a * (town_light(Xg, Zg, S) + facility_ground_light(Xg, Zg, S))
    # ---- channel: water or exposed bed (drawn at the water-plane hit)
    ch = inside & okw
    water = np.zeros(cv.dep.shape, bool)
    if ch.any():
        dsw = Zw - river_zc(Xw); dw = np.abs(dsw)
        nz = sample(fbm_tex(512, 2.0, 34), Xw, Zw, 512 / 90.0)
        bed = _bed(dw, nz, dsw, Xw)
        water = ch & (bed < h)
        mud = ch & ~water
        if mud.any():
            above = np.clip((bed - h) / 1.2, 0, 1)               # wet near the waterline, dry higher up
            cr, shade = crack_lookup(Xw, Zw)
            dryk = float(S.get('dry', 0.0)) * above
            mc = hexc('231f1c') * (1 - above[..., None]) * 0.8 + hexc('4a4038') * above[..., None]
            mc = mc * (0.8 + 0.35 * nz[..., None]) * (1 - dryk[..., None] * cr[..., None] * 0.8)
            mc = mc * (0.9 + 0.2 * shade[..., None] * dryk[..., None])
            lit = ambient_light(S)[None, None] * 1.6 + town_light(Xw, Zw, S) + facility_ground_light(Xw, Zw, S) * 1.4 + hexc('2a3a48') * 0.012 * float(S.get('glow', 1.0))
            mcol = mc * lit
            # wet sheen: the sky / lights glance off the mud near the water
            sheen = (1 - above) ** 2 * 0.35
            out_col = np.where(mud[..., None], mcol + sheen[..., None] * hexc('1c2a3a') * (0.4 + S.get('dusk', 0) * 0.8), out_col)
        if water.any():
            wc = water_shade(cv, S, t, Xw, Zw, tw, refl)
            out_col = np.where(water[..., None], wc, out_col)
    # write
    tt = np.where(inside, tw, tg)
    z = E.dist_to_z(cam, np.where(np.isfinite(tt), tt, 1e6))
    cv.img[free] = out_col[free]
    cv.dep[free] = z[free]
    return water

@lru_cache(1)
def _crack():
    return E.crack_tex(512, 140, 3)

def crack_lookup(X, Z):
    e, s = _crack()
    return sample(e, X, Z, 512 / 26.0), sample(s, X, Z, 512 / 26.0)

def ambient_light(S):
    """irradiance from the sky: navy at night, mauve-pink at dusk."""
    d = float(S.get('dusk', 0.0))
    return (hexc('0e1626') * 0.32 * (1 - d) + hexc('2a2c40') * 0.32 * d + hexc('2a3a48') * 0.06 * S.get('glow', 0)).astype(F32)

def town_light(X, Z, S):
    """sodium pools of the streetlights on the ground (top-down light map, per frame dimming)."""
    lm = light_map(round(float(S.get('street_dim', 0.0)), 2), round(float(S.get('town_lights', 1.0)), 2))
    u = ((X + 2048) / 2.0).astype(F32); v = ((Z + 2048) / 2.0).astype(F32)
    l = cv2.remap(lm, u, v, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    return l[..., None] * SODIUM_POOL

SODIUM_POOL = hexc('ffae62') * 0.9

@lru_cache(8)
def light_map(dim, tl):
    n = 2048; m = np.zeros((n, n), F32)
    for x, z, o in town()['streetlights']:
        a = street_on(o, dim) * tl
        if a <= 0.01: continue
        cx, cy = (x + 2048) / 2.0, (z + 2048) / 2.0
        r = 9.0
        x0, y0 = int(cx - r * 2.5), int(cy - r * 2.5)
        yy, xx = np.mgrid[y0:y0 + int(r * 5), x0:x0 + int(r * 5)].astype(F32)
        g = np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * (r * 0.9) ** 2)) * a
        if 0 <= x0 and 0 <= y0 and x0 + g.shape[1] < n and y0 + g.shape[0] < n: m[y0:y0 + g.shape[0], x0:x0 + g.shape[1]] += g
    return m * 0.55

def street_on(order, dim):
    """streetlight with random `order` stays on until the dimming wave reaches it."""
    return float(np.clip((order - dim) / 0.06 + 1, 0, 1)) if dim > 0 else 1.0

def water_shade(cv, S, t, X, Z, tw, refl):
    cam = cv.cam; D, k = cam.dirs()
    cosv = np.clip(-D[..., 1], 0.02, 1)
    R = (0.02 + 0.98 * (1 - cosv) ** 5).astype(F32)
    body = hexc('061114') * (0.6 + 0.6 * float(S.get('dusk', 0)))
    if refl is None: rc = np.zeros_like(cv.img)
    else:
        # ripples: flowing noise in world space; the displacement shrinks with distance
        flow = t * 0.8
        n1 = sample(fbm_tex(256, 1.6, 35), X * 1.0 - flow * 3, Z * 2.2, 256 / 30.0) - 0.5
        n2 = sample(fbm_tex(256, 1.4, 36), X * 0.7 + flow, Z * 1.3 - flow * 0.5, 256 / 9.0) - 0.5
        amp = (0.8 + float(S.get('ripple', 0.0)) * 3.0)
        dist = np.where(np.isfinite(tw), tw, 1e4)
        sc = cam.fpx / np.maximum(5, dist) * amp
        dx = (n1 * 0.6 + n2 * 0.4) * sc * 0.25
        dy = (n2 * 0.8 + n1 * 0.2) * sc * 1.2
        H, W = cv.H, cv.W
        xs = np.arange(W, dtype=F32)[None, :] + dx; ys = np.arange(H, dtype=F32)[:, None] + dy
        rc = cv2.remap(np.ascontiguousarray(refl), xs.astype(F32), ys.astype(F32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return body * (1 - R[..., None]) + rc * R[..., None]

# ---------------------------------------------------------------- the facility
def breath_curve(t, bar=1.805, phase=4.272):
    """a slow inhale / exhale locked to the bar: 0..1 (inhale over the first half, exhale over the second)."""
    u = ((t - phase) / bar) % 1.0
    return 0.5 - 0.5 * math.cos(2 * math.pi * u)

def mono_faces(M, grow=1.0):
    x0, x1, z0, z1, h = M['x0'], M['x1'], M['z0'], M['z1'], M['h'] * grow
    V = lambda x, y, z: (x, y, z)
    return {
        'front': ([V(x0, h, z0), V(x1, h, z0), V(x1, 0, z0), V(x0, 0, z0)], (0, 0, -1), (x0, x1), z0),     # faces the river
        'left': ([V(x0, h, z1), V(x0, h, z0), V(x0, 0, z0), V(x0, 0, z1)], (-1, 0, 0), (z1, z0), x0),
        'right': ([V(x1, h, z0), V(x1, h, z1), V(x1, 0, z1), V(x1, 0, z0)], (1, 0, 0), (z0, z1), x1),
        'back': ([V(x1, h, z1), V(x0, h, z1), V(x0, 0, z1), V(x1, 0, z1)], (0, 0, 1), (x1, x0), z1),
        'top': ([V(x0, h, z1), V(x1, h, z1), V(x1, h, z0), V(x0, h, z0)], (0, 1, 0), None, h),
    }

def _world_from_screen(cam, X, Y, Z):
    """reconstruct world points for screen pixels (X, Y) at view depth Z."""
    sx = (X - cam.cx) / cam.fpx * Z; sy = (cam.cy - Y) / cam.fpx * Z
    P = cam.eye[None, None] + cam.r[None, None] * sx[..., None] + cam.u[None, None] * sy[..., None] + cam.f[None, None] * Z[..., None]
    return P

LED_SEAM = hexc('cfe9ff'); RED_AV = hexc('ff2236'); UPLIGHT = hexc('dbe8f2'); BAND = hexc('eef5ff')
UP_STEP = 20.0                      # one wall-washer every 20 m along the base

def seams_u(L):
    """where the vertical light seams run (metres along a face of length L)."""
    n = max(2, int(round(L / 72.0)))
    return [L * (k + 0.5) / n for k in range(n)]

def draw_monolith(cv, M, S, t, which='A', mirror_h=None):
    """the big gray house: dark precast concrete, a row of wall-washers throwing scallops of cold light up the
    facade, a few vertical light seams that breathe, a base band, the red slit, red aviation lights."""
    cam = cv.cam
    grow = float(S.get('second', 1.0)) if which == 'B' else 1.0
    if grow <= 0.001: return
    faces = mono_faces(M, grow)
    hgt = M['h'] * grow
    br = float(S.get('breath', 0.5)); ml = float(S.get('mono_lights', 1.0)); dusk = float(S.get('dusk', 0.0))
    # lights going out row by row (outro): a sweep from the top down
    out_k = float(S.get('lights_out', 0.0))
    amb = ambient_light(S)
    flip = np.array([1, -1, 1], F32); off2 = np.array([0, 2 * mirror_h, 0], F32) if mirror_h is not None else None
    for name in ('back', 'left', 'right', 'front', 'top'):
        P, n, span, off = faces[name]
        P = np.array(P, F32)
        if mirror_h is not None: P = P * flip + off2
        nn = np.array(n, F32)
        if mirror_h is not None: nn = nn * flip
        if np.dot(nn, P.mean(0) - cam.eye) >= 0: continue
        if name == 'top':
            cv.poly(P, hexc('202225') * (amb * 3 + 0.002), ztest=True)
            continue
        L = abs(span[1] - span[0])
        seam_list = seams_u(L)
        side = name in ('left', 'right', 'back')
        def coords(X, Y, Z, name=name, span=span):
            Pw = _world_from_screen(cam, X, Y, Z)
            if mirror_h is not None: Pw = Pw * flip + off2
            uu = (Pw[..., 0] if name in ('front', 'back') else Pw[..., 2]); vv = Pw[..., 1]
            return np.abs(uu - span[0]), vv
        def shade(X, Y, Z, m, side=side):
            uu, vv = coords(X, Y, Z)
            panel = (uu % 12.0); course = (vv % 4.6)
            seam = np.maximum(np.exp(-(np.minimum(panel, 12 - panel) / 0.1) ** 2), np.exp(-(np.minimum(course, 4.6 - course) / 0.05) ** 2) * 0.5)
            st1 = sample(fbm_tex(512, 1.5, 41), uu * 0.35, vv * 3.0 + (7 if side else 0) * 50, 512 / 150.0)
            st2 = sample(fbm_tex(256, 1.2, 42), uu * 2.0, vv * 0.25, 256 / 40.0)           # vertical rain streaks
            alb = 0.055 + 0.04 * st1 + 0.02 * st2 - 0.02 * seam
            fin = np.exp(-(((uu - 30.0) % 60.0 - 30.0) / 0.9) ** 2) * 0.02                      # pilasters catch more light
            alb = alb + fin
            lv = (vv > hgt - 9.5) & (vv < hgt - 4.5)
            slat = 0.55 + 0.45 * (((vv * 4.0) % 1.0) > 0.5)
            alb = np.where(lv, alb * 0.55 * slat, alb)
            # wall-washers: a scallop of light from each fixture at the base
            du = ((uu - UP_STEP / 2) % UP_STEP) - UP_STEP / 2
            hv = np.maximum(vv - 0.4, 0)
            wid = 0.9 + 0.42 * hv
            fx = np.floor(uu / UP_STEP)
            hsh = np.modf(np.sin(fx * 12.9898 + (3.1 if side else 0.0)) * 43758.5453)[0]
            hsh = np.abs(hsh)
            strength = np.where(hsh < 0.12, 0.08, 0.6 + 0.4 * hsh)
            wash = np.exp(-(du / wid) ** 2) * np.exp(-hv / 13.0) * (1 - np.exp(-hv / 0.8)) * 4.5 * strength
            wash *= ml * (1 - out_k)
            sky_up = 0.35 + 0.65 * np.clip(vv / hgt, 0, 1)
            col = alb[..., None] * (amb * sky_up[..., None] * 1.5 + UPLIGHT * (wash * (0.55 if side else 1.0))[..., None]
                                    + hexc('ff8f8a') * (dusk * 0.10 * np.clip(vv / hgt, 0, 1))[..., None])
            return col
        def emis(X, Y, Z, m, name=name, L=L, seam_list=seam_list, side=side):
            uu, vv = coords(X, Y, Z)
            e = np.zeros(X.shape + (3,), F32)
            px = max(1e-3, float(np.median(Z))) / cam.fpx                  # metres per pixel here
            wseam = max(0.18, px * 0.8)
            dq = np.full(uu.shape, 1e9, F32)
            for su in seam_list: dq = np.minimum(dq, np.abs(uu - su))
            seam = np.exp(-(dq / wseam) ** 2) * np.clip((vv - 1.0) / 2.0, 0, 1) * np.clip((hgt - 1.5 - vv) / 2.0, 0, 1)
            # the breath climbs the seams from the ground and falls back
            climb = np.clip((br * 1.15 * hgt - vv) / (hgt * 0.25) + 0.25, 0, 1)
            sweep = np.clip((vv - (1 - out_k * 1.2) * hgt) / 6.0 + 1, 0, 1) if out_k > 0 else 1.0
            e += LED_SEAM * (seam * (0.15 + 0.85 * br) * climb * ml * (0.8 if side else 1.6) * (1 - (1 - sweep) if out_k > 0 else 1))[..., None]
            band = np.exp(-((vv - 3.4) / max(0.10, px * 0.75)) ** 2) * ml * (1 - out_k)
            e += BAND * (band * 0.9)[..., None]
            par = np.exp(-((vv - (hgt - 0.8)) / max(0.08, px * 0.7)) ** 2) * ml * 0.25 * (1 - out_k)
            e += LED_SEAM * par[..., None]
            if name == 'front':
                rs = float(S.get('red_slit', 0.0))
                if rs > 0:
                    cx = L / 2; wv = max(0.22, px * 0.8)
                    top = 3.0 + (hgt - 6.0) * min(1.0, rs)
                    sl = np.exp(-((uu - cx) / wv) ** 2) * np.clip((vv - 3.0) / 1.2, 0, 1) * np.clip((top - vv) / 1.5, 0, 1)
                    e += hexc('ff1730') * (sl * 4.0 * min(1.0, rs * 4))[..., None]
            return e
        cv.poly(P, shade, emis=emis, ztest=True)
    if mirror_h is None: _roof_units(cv, M, S, t, hgt)
    draw_stacks(cv, M, S, t, hgt, mirror_h, amb, ml * (1 - out_k))
    blink = 0.5 + 0.5 * max(0.0, math.sin(t * 2 * math.pi / 2.0)) ** 6
    corners = np.array([[M['x0'], hgt + 1.2, M['z0']], [M['x1'], hgt + 1.2, M['z0']], [M['x0'], hgt + 1.2, M['z1']], [M['x1'], hgt + 1.2, M['z1']],
                        [(M['x0'] + M['x1']) / 2, hgt + 1.2, M['z0']]], F32)
    E.lights(cv, corners, RED_AV, 4.0 * blink * ml * (1 - out_k), size_m=0.6, mirror_h=mirror_h)
    rp = float(S.get('red_point', 0.0))
    if rp > 0 and which == 'A':
        E.lights(cv, [[(M['x0'] + M['x1']) / 2, hgt + 1.2, M['z0']]], RED_AV, 4.5 * rp, size_m=0.6, mirror_h=mirror_h)
    if ml * (1 - out_k) > 0.01:
        xs = np.arange(M['x0'] + UP_STEP / 2, M['x1'], UP_STEP, dtype=F32)
        P = np.stack([xs, np.full_like(xs, 0.6), np.full_like(xs, M['z0'] - 0.8)], 1)
        E.lights(cv, P, UPLIGHT, 1.4 * ml * (1 - out_k), size_m=0.3, mirror_h=mirror_h)
    # perimeter floodlight poles in front of the facade (they throw light on the apron and glow in the fog)
    if ml * (1 - out_k) > 0.01:
        xs = np.arange(M['x0'] + 30, M['x1'] - 10, 60.0, dtype=F32)
        P = np.stack([xs, np.full_like(xs, 12.0), np.full_like(xs, M['z0'] - 42.0)], 1)
        E.lights(cv, P, hexc('f4f1e8'), 3.0 * ml * (1 - out_k), size_m=0.6, mirror_h=mirror_h)
        if mirror_h is None:
            for x in xs:
                cv.line3(np.array([x, 0, M['z0'] - 42.0], F32), np.array([x, 12.0, M['z0'] - 42.0], F32), hexc('0c0e10'), width_m=0.25, min_px=0.6)

def draw_stacks(cv, M, S, t, hgt, mirror_h, amb, lit):
    """the exhaust stacks the steam rises from (they break the roofline), and a long mechanical penthouse."""
    cam = cv.cam
    fl = np.array([1, -1, 1], F32); o2 = np.array([0, 2 * mirror_h, 0], F32) if mirror_h is not None else None
    def mq(pts):
        Pq = np.array(pts, F32)
        return Pq if mirror_h is None else Pq * fl + o2
    # penthouse: set back from the front edge
    x0, x1 = M['x0'] + 30, M['x1'] - 30; z0, z1 = M['z0'] + 25, M['z1'] - 40; y0, y1 = hgt, hgt + 7.0
    for pts, n in (([[x0, y1, z0], [x1, y1, z0], [x1, y0, z0], [x0, y0, z0]], (0, 0, -1)),
                   ([[x1, y1, z0], [x1, y1, z1], [x1, y0, z1], [x1, y0, z0]], (1, 0, 0)),
                   ([[x0, y1, z1], [x0, y1, z0], [x0, y0, z0], [x0, y0, z1]], (-1, 0, 0))):
        Pq = mq(pts); nn = np.array(n, F32) * (fl if mirror_h is not None else 1)
        if np.dot(nn, Pq.mean(0) - cam.eye) < 0: cv.poly(Pq, hexc('1a1c1f') * (amb * 2.2 + 0.0015), ztest=True)
    for i, p in enumerate(stacks(M)):
        r = 3.2; h0, h1 = hgt, p[1] + 10.0
        # a cylinder: draw its silhouette as a quad facing the camera, shaded across its width
        c = np.array([p[0], 0, p[2]], F32)
        side = cam.r * np.array([1, 0, 1], F32); side = side / max(1e-6, np.linalg.norm(side))
        pts = [c + side * -r + np.array([0, h1, 0], F32), c + side * r + np.array([0, h1, 0], F32), c + side * r + np.array([0, h0, 0], F32), c + side * -r + np.array([0, h0, 0], F32)]
        def shade(X, Y, Z, m, c=c, side=side, r=r):
            P = _world_from_screen(cam, X, Y, Z) if mirror_h is None else _world_from_screen(cam, X, Y, Z) * fl + o2
            u = np.clip(((P - c) @ side) / r, -1, 1)
            lam = 0.35 + 0.65 * np.sqrt(np.clip(1 - u * u, 0, 1))
            return (hexc('2a2d31') * (amb * 2.5 + 0.002) * lam[..., None] + hexc('d6e6f0') * (0.02 * lit * np.exp(-(u - 0.6) ** 2 / 0.05))[..., None]).astype(F32)
        cv.poly(mq(pts), shade, ztest=True)
        E.lights(cv, [[p[0], h1 + 0.6, p[2]]], RED_AV, 2.2 * lit * (0.6 + 0.4 * math.sin(t * 2.5 + i)), size_m=0.5, mirror_h=mirror_h)

def _roof_units(cv, M, S, t, hgt):
    cam = cv.cam
    if cam.eye[1] < hgt + 2: return
    amb = ambient_light(S)
    for i in range(10):
        for j in range(4):
            cx = M['x0'] + 25 + i * ((M['x1'] - M['x0'] - 50) / 9); cz = M['z0'] + 30 + j * ((M['z1'] - M['z0'] - 60) / 3)
            s = 7.0
            P = np.array([[cx - s, hgt + 3.0, cz + s], [cx + s, hgt + 3.0, cz + s], [cx + s, hgt + 3.0, cz - s], [cx - s, hgt + 3.0, cz - s]], F32)
            cv.poly(P, hexc('1d1f22') * (amb * 3 + 0.003), ztest=True)

def stacks(M):
    """exhaust stack positions on the roof (plume sources): uneven spacing, a little set back."""
    fr = (0.12, 0.34, 0.61, 0.86)
    out = []
    for i, f in enumerate(fr):
        out.append((M['x0'] + f * (M['x1'] - M['x0']), M['h'] + 4, M['z0'] + 38 + (i % 2) * 22))
    return np.array(out, F32)

def facility_ground_light(X, Z, S):
    """the apron in front of each facade, lit by its floodlights and wall-washers."""
    ml = float(S.get('mono_lights', 1.0)) * (1 - float(S.get('lights_out', 0.0)))
    out = np.zeros(X.shape, F32)
    if ml <= 0.01: return out[..., None] * 0
    for M, g in ((MONO_A, 1.0), (MONO_B, float(S.get('second', 0.0)))):
        if g < 0.9: continue
        inx = np.clip((X - M['x0'] + 10) / 20, 0, 1) * np.clip((M['x1'] + 10 - X) / 20, 0, 1)
        dz = M['z0'] - Z
        front = np.where(dz > 0, np.exp(-np.maximum(dz, 0) / 22.0), 0) * inx
        pools = np.exp(-(((X - M['x0'] - 30) % 60 - 30) / 14.0) ** 2) * np.exp(-((dz - 42) / 16.0) ** 2) * inx
        out += (front * 0.35 + pools * 0.6) * ml
    return out[..., None] * hexc('d8e4ec')

# ---------------------------------------------------------------- town drawing
def house_polys(hh):
    """faces of a gabled house: list of (points (n,3), normal, kind)."""
    c, w, d, h, pitch = hh['c'], hh['w'], hh['d'], hh['h'], hh['pitch']
    a = hh['ang']; ca, sa = math.cos(a), math.sin(a)
    def L(x, y, z): return np.array([c[0] + x * ca - z * sa, y, c[2] + x * sa + z * ca], F32)
    rh = h + w * 0.5 * pitch
    faces = []
    faces.append(([L(-w / 2, h, -d / 2), L(w / 2, h, -d / 2), L(w / 2, 0, -d / 2), L(-w / 2, 0, -d / 2)], (0, 0, -1), 'wall_f'))
    faces.append(([L(w / 2, h, d / 2), L(-w / 2, h, d / 2), L(-w / 2, 0, d / 2), L(w / 2, 0, d / 2)], (0, 0, 1), 'wall_b'))
    faces.append(([L(-w / 2, h, d / 2), L(-w / 2, rh, 0), L(-w / 2, h, -d / 2), L(-w / 2, 0, -d / 2), L(-w / 2, 0, d / 2)], (-1, 0, 0), 'gable_l'))
    faces.append(([L(w / 2, h, -d / 2), L(w / 2, rh, 0), L(w / 2, h, d / 2), L(w / 2, 0, d / 2), L(w / 2, 0, -d / 2)], (1, 0, 0), 'gable_r'))
    o = 0.5
    faces.append(([L(-w / 2 - o, rh, 0), L(w / 2 + o, rh, 0), L(w / 2 + o, h - 0.3, -d / 2 - o), L(-w / 2 - o, h - 0.3, -d / 2 - o)], (0, 1, -1), 'roof_f'))
    faces.append(([L(w / 2 + o, rh, 0), L(-w / 2 - o, rh, 0), L(-w / 2 - o, h - 0.3, d / 2 + o), L(w / 2 + o, h - 0.3, d / 2 + o)], (0, 1, 1), 'roof_b'))
    out = []
    for P, n, kind in faces:
        nx, ny, nz = n; nw = np.array([nx * ca - nz * sa, ny, nx * sa + nz * ca], F32); nw /= np.linalg.norm(nw)
        out.append((np.array(P, F32), nw, kind))
    return out, L

@lru_cache(1)
def town_geo():
    """static world-space geometry for every house (faces, window quads) plus arrays for fast culling."""
    T = town(); out = []
    hx, hz = float(HOUSE[0]), float(HOUSE[2])
    dmax = max(1.0, max(np.hypot(h['c'][0] - hx, h['c'][2] - hz) for h in T['houses']))
    r = np.random.default_rng(77)
    for hh in T['houses']:
        polys, L = house_polys(hh)
        front_n = polys[0][1]
        wins = []
        for wi in hh['wins']:
            hw = 0.75; hg = 0.65; yv = hh['h'] * wi['v'] + 0.9; u = wi['u'] * hh['w']; zf = -hh['d'] / 2 - 0.06
            Q = np.array([L(u - hw, yv + hg, zf), L(u + hw, yv + hg, zf), L(u + hw, yv - hg, zf), L(u - hw, yv - hg, zf)], F32)
            wins.append(dict(Q=Q, c=Q.mean(0), lit=wi['lit'], warm=wi['warm']))
        dh = np.hypot(hh['c'][0] - hx, hh['c'][2] - hz) / dmax
        out.append(dict(hh=hh, polys=polys, front_n=front_n, wins=wins, blue_order=float(dh * 0.88 + 0.12 * r.random()),
                        size=max(hh['w'], hh['d'], hh['h'] + hh['w'] * 0.5 * hh['pitch'])))
    C = np.array([g['hh']['c'] for g in out], F32)
    tr = np.array([[t_[0], 0, t_[1]] for t_ in T['trees']], F32)
    near_river_h = np.abs(C[:, 2] - river_zc(C[:, 0])) < 150
    near_river_t = np.abs(tr[:, 2] - river_zc(tr[:, 0])) < 150
    return out, C, tr, near_river_h, near_river_t

def blue_k(order, blue):
    """how far house `order` is into the blue: 0 warm .. 1 blue (a quick flip as the wave passes)."""
    return float(np.clip((blue * 1.12 - order) / 0.035, 0, 1)) if blue > 0 else 0.0

def draw_town(cv, S, t, mirror_h=None, max_dist=2600.0, detail=1.0):
    cam = cv.cam; T = town(); G, C, TR, nrh, nrt = town_geo()
    amb = ambient_light(S); dusk = float(S.get('dusk', 0)); tl = float(S.get('town_lights', 1.0)); blue = float(S.get('blue', 0.0))
    fac_dir = nrm(np.array([MONO_A['x0'] * 0.5 + MONO_A['x1'] * 0.5, 30, MONO_A['z0']], F32) - np.array([0, 0, -200], F32))
    sun_dir = nrm([math.sin(S.get('sun_az', 0)), 0.15, math.cos(S.get('sun_az', 0))])
    flip = np.array([1, -1, 1], F32); off2 = np.array([0, 2 * mirror_h, 0], F32) if mirror_h is not None else None
    dh = np.linalg.norm(C - cam.eye, axis=1)
    dt_ = np.linalg.norm(TR - cam.eye, axis=1) if len(TR) else np.zeros(0)
    clear = float(S.get('tree_clear', 90.0))
    # cull to the view cone (cheap angular test) and distance
    def in_view(P, rad):
        x, y, z = cam.cam_space(P)
        lim = (cam.W / 2 + 40) / cam.fpx
        return (z > -rad) & (np.abs(x) - rad < z * lim * 1.05 + rad) & (dh_ok := True)
    hsel = (dh < max_dist)
    tsel = (dt_ < max_dist * 1.2) & (dt_ >= clear)
    if mirror_h is not None: hsel &= nrh; tsel &= nrt
    Ph = C if mirror_h is None else C * flip + off2
    xh, yh, zh = cam.cam_space(Ph); lim = (cam.W / 2) / cam.fpx
    hsel &= (zh > -20) & (np.abs(xh) < zh * lim * 1.15 + 25)
    if len(TR):
        Pt = TR if mirror_h is None else TR * flip + off2
        xt, yt, zt = cam.cam_space(Pt)
        tsel &= (zt > -20) & (np.abs(xt) < zt * lim * 1.15 + 25)
    items = [(float(dh[i]), 0, i) for i in np.nonzero(hsel)[0]] + [(float(dt_[i]), 1, i) for i in np.nonzero(tsel)[0]]
    items.sort(key=lambda it: -it[0])
    win_pts, win_cols, win_int = [], [], []
    ft = S.get('fac_trees')          # (album cover only) keep this fraction of the trees between the river and the facility
    for d, kind, i in items:
        if kind == 1:
            if ft is not None:
                x_, z_ = T['trees'][i][0], T['trees'][i][1]
                if MONO_A['x0'] - 60 < x_ < MONO_A['x1'] + 60 and river_zc(x_) < z_ < MONO_A['z0'] and ((i * 2654435761) % 1000) / 1000 > ft:
                    continue
            draw_tree(cv, T['trees'][i], S, t, mirror_h)
            continue
        g = G[i]; ob = g['hh']
        px = cam.fpx / max(1.0, d)
        bl = blue_k(g['blue_order'], blue)
        if g['size'] * px >= 2.0:
            for P, n, k in g['polys']:
                Pm = P if mirror_h is None else P * flip + off2
                nm = n if mirror_h is None else n * flip
                if np.dot(nm, Pm.mean(0) - cam.eye) >= 0: continue
                base = ob['roof'] if k.startswith('roof') else ob['wall']
                lit = amb * (1.2 + 0.8 * max(0.0, float(n[1]))) + hexc('9fb8c6') * 0.02 * max(0.0, float(np.dot(n, fac_dir))) * S.get('glow', 1)
                lit = lit + hexc('ff9a6a') * 0.08 * dusk * max(0.0, float(np.dot(n, sun_dir)))
                if bl > 0: lit = lit + BLUEWIN * 0.004 * bl
                cv.poly(Pm, base * lit, ztest=True)
        ww_ = float(S.get('win_wave', 1.0)); wo_ = float(S.get('win_off', 0.0))
        wave_on = 1.0 if ww_ >= 1.0 else float(np.clip((ww_ * 1.1 - g['blue_order']) / 0.03, 0, 1))
        wave_off = 0.0 if wo_ <= 0 else float(np.clip((wo_ * 1.1 - g['blue_order']) / 0.03, 0, 1))
        for wi in g['wins']:
            on = (1.0 if (wi['lit'] or bl > 0) else 0.0) * (wave_on if bl <= 0 else 1.0) * (1 - wave_off if bl <= 0 else 1.0)
            if on * tl <= 0.01: continue
            col = AMBER * (0.7 + 0.3 * wi['warm']) * (1 - bl) + BLUEWIN * bl
            inten = (0.9 + 0.4 * wi['warm']) * tl * on * (1 + 0.6 * bl)
            if px * 1.5 > 2.5:
                Q = wi['Q'] if mirror_h is None else wi['Q'] * flip + off2
                nf = g['front_n'] if mirror_h is None else g['front_n'] * flip
                if np.dot(nf, Q.mean(0) - cam.eye) < 0:
                    cv.poly(Q, col * inten * 0.35, emis=col * inten * 0.55, ztest=True, write_depth=False)
            else:
                win_pts.append(wi['c']); win_cols.append(col); win_int.append(inten * 0.6)
    if win_pts:
        E.lights(cv, np.array(win_pts, F32), np.array(win_cols, F32), np.array(win_int, F32), size_m=0.5, mirror_h=mirror_h)
    sl = T['streetlights']
    if len(sl):
        dim = float(S.get('street_dim', 0.0))
        on = np.array([street_on(o, dim) for o in sl[:, 2]], F32) * tl
        P = np.stack([sl[:, 0], np.full(len(sl), 7.5, F32), sl[:, 1]], 1)
        E.lights(cv, P, SODIUM, 1.6 * on, size_m=0.35, mirror_h=mirror_h)

AMBER = hexc('ffb867'); BLUEWIN = hexc('5aa2ff'); SODIUM = hexc('ffab5e')

@lru_cache(400)
def tree_sprite(seed, rq):
    """alpha mask of a deciduous tree silhouette with a canopy radius of about rq px: lobed crown, leafy edge, trunk.
    returns (mask, ax, ay): the sprite and its trunk-base anchor."""
    r = np.random.default_rng(seed)
    R = max(2.0, rq)
    Wd = int(R * 3.4) + 6; Ht = int(R * 3.6) + 6
    yy, xx = np.mgrid[0:Ht, 0:Wd].astype(F32)
    cx, cy = Wd / 2, R * 1.25 + 3
    field = np.zeros((Ht, Wd), F32)
    nl = int(r.integers(5, 9))
    for k in range(nl):
        ox = r.normal(0, 0.45) * R; oy = r.normal(0, 0.32) * R - 0.1 * R
        s = R * r.uniform(0.35, 0.6)
        field += np.exp(-(((xx - cx - ox) / s) ** 2 + ((yy - cy - oy) / (s * 0.85)) ** 2))
    tex = fbm_tex(256, 1.25, 52)
    nz = sample(tex, xx * (9.0 / R) * 4 + seed * 37, yy * (9.0 / R) * 4, 1.0)
    crown = np.clip((field - 0.55 + (nz - 0.5) * 0.9) * (3.0 + R * 0.05), 0, 1)
    # trunk + two limbs
    m = crown.copy()
    tw = max(1, int(R * 0.09))
    base = (cx + r.normal(0, 0.05) * R, cy + R * 1.55)
    top = (cx + r.normal(0, 0.08) * R, cy + R * 0.2)
    cv2.line(m, (int(base[0] * 4), int(base[1] * 4)), (int(top[0] * 4), int(top[1] * 4)), 1.0, tw, cv2.LINE_AA, shift=2)
    for k in range(2):
        a = r.uniform(-1.2, 1.2); L = R * r.uniform(0.5, 0.8)
        p0 = (base[0] * 0.4 + top[0] * 0.6, base[1] * 0.4 + top[1] * 0.6)
        p1 = (p0[0] + math.sin(a) * L, p0[1] - math.cos(a) * L)
        cv2.line(m, (int(p0[0] * 4), int(p0[1] * 4)), (int(p1[0] * 4), int(p1[1] * 4)), 1.0, max(1, tw // 2), cv2.LINE_AA, shift=2)
    return np.clip(m, 0, 1).astype(F32), base[0], base[1]

def draw_tree(cv, tr, S, t, mirror_h=None):
    """a dark deciduous silhouette against the lit fog; a little sway in the wind."""
    x, z, hgt, rad, sd = tr
    cam = cv.cam
    P = np.array([x, 0.0, z], F32)
    if mirror_h is not None: P = P * np.array([1, -1, 1], F32) + np.array([0, 2 * mirror_h, 0], F32)
    sx, sy, sz = cam.project(P[None])
    if sz[0] < 1.0: return
    s = cam.fpx / sz[0]
    rr = rad * s
    if rr < 0.7: return
    if rr > 3 * max(cv.W, cv.H): return            # a tree at the lens (it would be a multi-GB sprite): skip it
    if sx[0] < -rr * 3 or sx[0] > cv.W + rr * 3: return
    # quantise the sprite size (6 % steps) so slow camera moves reuse sprites
    q = 1.06 ** round(math.log(max(rr, 0.7)) / math.log(1.06))
    m, ax, ay = tree_sprite(int(sd * 1e6) % 100000, round(q, 3))
    k = rr / q
    if abs(k - 1) > 0.01: m = cv2.resize(m, None, fx=k, fy=k, interpolation=cv2.INTER_LINEAR); ax *= k; ay *= k
    # the crown scale vs. tree height: stretch vertically to the tree's height ratio
    if mirror_h is not None: m = m[::-1]; ay = m.shape[0] - ay
    x0 = int(round(sx[0] - ax)); y0 = int(round(sy[0] - ay))
    h_, w_ = m.shape
    X0, Y0, X1, Y1 = max(0, x0), max(0, y0), min(cv.W, x0 + w_), min(cv.H, y0 + h_)
    if X1 <= X0 or Y1 <= Y0: return
    mm = m[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]
    zz = float(sz[0])
    d = cv.dep[Y0:Y1, X0:X1]
    mm = mm * (d > zz * 0.995)
    amb = ambient_light(S)
    col = hexc('101512') * (amb * 5 + 0.0015)
    reg = cv.img[Y0:Y1, X0:X1]; a3 = mm[..., None]
    reg *= (1 - a3); reg += col * a3
    cv.emis[Y0:Y1, X0:X1] *= (1 - a3)
    d[mm > 0.5] = zz

# ---------------------------------------------------------------- hills
@lru_cache(1)
def _hill_profiles():
    r = np.random.default_rng(7)
    out = []
    for k, (dist, hgt) in enumerate(((5200, 260), (3600, 190), (2600, 120))):
        ang = np.linspace(-math.pi, math.pi, 720, endpoint=False)
        n = np.zeros_like(ang)
        for f in (2, 3, 5, 8, 13, 21, 34):
            n += np.sin(ang * f + r.uniform(0, 6.28)) / f ** 0.9
        n = (n - n.min()) / (n.max() - n.min())
        out.append((dist, hgt * (0.35 + 0.65 * n), ang))
    return out

def draw_hills(cv, S, mirror_h=None):
    cam = cv.cam
    amb = ambient_light(S); dusk = float(S.get('dusk', 0))
    for li, (dist, hh, ang) in enumerate(_hill_profiles()):
        P = np.stack([np.sin(ang) * dist, hh, np.cos(ang) * dist], 1).astype(F32) + np.array([cam.eye[0], 0, cam.eye[2]], F32) * np.array([0.92, 0, 0.92], F32)
        if mirror_h is not None: P = P * np.array([1, -1, 1], F32) + np.array([0, 2 * mirror_h, 0], F32)
        x, y, z = cam.project(P)
        ok = z > 1
        if ok.sum() < 3: continue
        # draw the silhouette as segments between consecutive visible points
        col = (hexc('0c1220') * (1 - dusk) + hexc('3a2a44') * dusk) * (0.7 + 0.15 * li) + amb * 0.3 * li
        idx = np.nonzero(ok)[0]
        segs = np.split(idx, np.nonzero(np.diff(idx) > 1)[0] + 1)
        for sg in segs:
            if len(sg) < 2: continue
            xs, ys = x[sg], y[sg]
            if xs.max() < -200 or xs.min() > cv.W + 200: continue
            bottom = cv.H * 3 if mirror_h is None else -cv.H * 3
            pts = np.concatenate([np.stack([xs, ys], 1), [[xs[-1], bottom], [xs[0], bottom]]]).astype(F32)
            m = np.zeros((cv.H, cv.W), F32)
            cv2.fillPoly(m, [np.round(pts * 4).astype(np.int32)], 1.0, cv2.LINE_AA, shift=2)
            m *= ~np.isfinite(cv.dep) | (cv.dep > dist * 0.98)
            mm = m[..., None]
            cv.img *= (1 - mm); cv.img += col * mm
            sel = m > 0.5; cv.dep[sel] = dist

# ---------------------------------------------------------------- pylons + wires
def pylon_line():
    """the transmission line from the far hills to the substation: tower bases (x, z) and heading."""
    A = np.array([-2300.0, 900.0]); B = np.array([SUBSTATION[0] - 20, SUBSTATION[2] + 30])
    n = 9; pts = [A + (B - A) * (k / (n - 1)) for k in range(n)]
    hd = math.atan2(B[1] - A[1], B[0] - A[0])
    return [np.array(p, F32) for p in pts], hd

def feeder_line():
    """a smaller line from the substation across the river into town."""
    A = np.array([SUBSTATION[0] + 30, SUBSTATION[2] - 10]); B = np.array([60.0, -380.0])
    n = 7; pts = [A + (B - A) * (k / (n - 1)) for k in range(n)]
    return [np.array(p, F32) for p in pts], math.atan2(B[1] - A[1], B[0] - A[0])

def pylon_geo(base, hd, H=46.0):
    """lattice tower (a classic 'cat' silhouette, simplified): list of segments in world space + wire attach points."""
    bx, bz = float(base[0]), float(base[1])
    ca, sa = math.cos(hd + math.pi / 2), math.sin(hd + math.pi / 2)   # cross-arms perpendicular to the line
    fa, fs = math.cos(hd), math.sin(hd)
    def P(u, y, w=0.0):   # u across the line, w along the line
        return np.array([bx + u * ca + w * fa, y, bz + u * sa + w * fs], F32)
    segs = []
    legs = [(-4.5, -4.5), (4.5, -4.5), (4.5, 4.5), (-4.5, 4.5)]
    top = [(-1.2, -1.2), (1.2, -1.2), (1.2, 1.2), (-1.2, 1.2)]
    ys = [0, 10, 20, 30, 38, H]
    for i in range(4):
        u0, w0 = legs[i]; u1, w1 = top[i]
        segs.append((P(u0, 0, w0), P(u1 * 1.4, 30, w1 * 1.4)))
        segs.append((P(u1 * 1.4, 30, w1 * 1.4), P(u1, H, w1)))
    for y0, y1 in zip(ys[:-1], ys[1:]):
        k0 = 1 - min(1, y0 / 30) * 0.69; k1 = 1 - min(1, y1 / 30) * 0.69
        for i in range(4):
            ua, wa = legs[i]; ub, wb = legs[(i + 1) % 4]
            segs.append((P(ua * k0, y0, wa * k0), P(ub * k1, y1, wb * k1)))
            segs.append((P(ub * k0, y0, wb * k0), P(ua * k1, y1, wa * k1)))
    arms = []
    for y, L in ((34.0, 14.0), (41.0, 10.0)):
        segs.append((P(-L, y), P(L, y))); segs.append((P(-L, y - 2.2), P(-1.6, y))); segs.append((P(L, y - 2.2), P(1.6, y)))
        segs.append((P(-L, y), P(-1.6, y - 3.2))); segs.append((P(L, y), P(1.6, y - 3.2)))
        arms += [P(-L, y - 2.6), P(L, y - 2.6)]
    arms.append(P(0, H + 0.5))
    return segs, arms

def catenary(A, B, sag, n=24):
    s = np.linspace(0, 1, n, dtype=F32)[:, None]
    P = A[None] * (1 - s) + B[None] * s
    P[:, 1] -= sag * 4 * s[:, 0] * (1 - s[:, 0])
    return P

@lru_cache(4)
def _pylon_static(which):
    """every lattice segment of every tower on the chosen lines (static)."""
    lines = []
    if 'main' in which: lines.append(pylon_line() + (46.0,))
    if 'feeder' in which: lines.append(feeder_line() + (26.0,))
    segA, segB = [], []
    for bases, hd, Ht in lines:
        for b in bases:
            segs, arms = pylon_geo(b, hd, Ht)
            for A, B in segs: segA.append(A); segB.append(B)
    return np.array(segA, F32), np.array(segB, F32)

def _pylon_wires(which):
    out = []
    if 'main' in which: out.append(pylon_line() + (46.0,))
    if 'feeder' in which: out.append(feeder_line() + (26.0,))
    res = []
    for bases, hd, Ht in out:
        res.append([pylon_geo(b, hd, Ht)[1] for b in bases])
    return res

def draw_pylons(cv, S, t, mirror_h=None, surge=0.0, hum=0.0, which=('main', 'feeder'), lit=0.0):
    cam = cv.cam; amb = ambient_light(S)
    col = hexc('0b0e12') + amb * 0.25
    which = tuple(which)
    A, B = _pylon_static(which)
    if mirror_h is not None:
        fl = np.array([1, -1, 1], F32); o2 = np.array([0, 2 * mirror_h, 0], F32); A = A * fl + o2; B = B * fl + o2
    E.lines_batch(cv, A, B, col, width_m=0.22, min_px=0.6, op=0.95)
    WA, WB, pulses = [], [], []
    for att in _pylon_wires(which):
        for a0, a1 in zip(att[:-1], att[1:]):
            for k in range(min(len(a0), len(a1))):
                P0, P1 = a0[k], a1[k]
                span = float(np.linalg.norm(P1 - P0))
                W = catenary(P0, P1, span * 0.035 + hum * 0.15 * math.sin(t * 2 * math.pi * 2.2 + k))
                if mirror_h is not None: W = W * np.array([1, -1, 1], F32) + np.array([0, 2 * mirror_h, 0], F32)
                WA.append(W[:-1]); WB.append(W[1:])
                if surge > 0 and mirror_h is None:
                    ph = (surge + k * 0.13) % 1.0
                    for s0 in (ph, (ph + 0.5) % 1.0):
                        i = min(int(s0 * (len(W) - 1)), len(W) - 2); f = s0 * (len(W) - 1) - i
                        pulses.append(W[i] * (1 - f) + W[i + 1] * f)
    if WA:
        E.lines_batch(cv, np.concatenate(WA), np.concatenate(WB), col * 1.4, width_m=0.06, min_px=0.55, op=0.9)
    if pulses and lit > 0:
        E.lights(cv, np.array(pulses, F32), hexc('bfe6ff'), 2.2 * lit, size_m=0.6)

# ---------------------------------------------------------------- the whole valley
def render(cam, S, t, reflections=True, refl_scale=0.5, town_on=True, pylons=True, plumes=True, extra=None, pre=None):
    cv = E.Canvas(cam)
    S = dict(S)
    if S.get('glow_az') is None or S.get('auto_glow', True):
        S['glow_az'] = math.atan2((MONO_A['x0'] + MONO_A['x1']) / 2 - cam.eye[0], (MONO_A['z0'] + MONO_A['z1']) / 2 - cam.eye[2])
    SK.sky(cv, S)
    refl = None
    if reflections:
        refl = reflection(cam, S, t, refl_scale, town_on, pylons, extra)
    water = ground_and_river(cv, S, t, refl)
    draw_hills(cv, S)
    if pre: pre(cv)
    # facility(ies) far to near
    monos = [('A', MONO_A)]
    if S.get('second', 0) > 0: monos.append(('B', MONO_B))
    monos.sort(key=lambda m: -np.linalg.norm(np.array([(m[1]['x0'] + m[1]['x1']) / 2, 20, (m[1]['z0'] + m[1]['z1']) / 2], F32) - cam.eye))
    for w, M in monos: draw_monolith(cv, M, S, t, w)
    if pylons: draw_pylons(cv, S, t, surge=S.get('surge_phase', 0.0), hum=S.get('hum', 0.0), lit=S.get('surge', 0.0))
    if town_on: draw_town(cv, S, t)
    if extra: extra(cv)
    # atmosphere: the fog is lit by what is bright in the frame (the facility sits in its own luminous haze)
    fc = S.get('fog_col'); fc = fog_color(S) if fc is None else fc
    Lf = light_field(cv)
    E.fog_pass(cv, fc[None, None] + Lf * (0.9 * S.get('fog_glow', 1.0)), density=0.0024 * S.get('fog', 1.0), height=S.get('fog_h', 12.0),
               haze_tex=fbm_tex(512, 2.6, 61), t=t, noise_amt=0.6)
    E.fog_pass(cv, fc[None, None] * 0.8 + Lf * 0.6, density=0.00018 * S.get('haze', 1.0), height=400.0)
    cv.img += Lf * (0.22 * S.get('fog', 1.0))
    if plumes and S.get('plumes', 1.0) > 0:
        for w, M in monos:
            g = float(S.get('second', 1.0)) if w == 'B' else 1.0
            if g < 0.95: continue
            for i, p in enumerate(stacks(M)):
                p = p + np.array([0, 10.5, 0], F32)
                SK.plume(cv, p, t + i * 7.3, height=(180, 250, 210, 270)[i % 4], r0=5, r1=(48, 62, 55, 70)[i % 4], wind=(1.6, 0.6), S=dict(S, plume_fog=0.12, fog_col=fc),
                         gain=1.0 * S.get('plumes', 1.0), seed=i + (10 if w == 'B' else 0), lit_from_below=1.0)
    return cv

def light_field(cv, k_img=0.6):
    """what the fog sees: bright surfaces and lights, blurred wide (1/8 res, three scales)."""
    W, H = cv.W, cv.H
    skyw = np.where(np.isfinite(cv.dep), 1.0, 0.3).astype(F32)[..., None]
    src = cv.emis + np.clip(cv.img * k_img - 0.002, 0, None) * skyw
    q = cv2.resize(src, (max(8, W // 8), max(8, H // 8)), interpolation=cv2.INTER_AREA)
    s8 = W / 240.0
    a = cv2.GaussianBlur(q, (0, 0), 2.5 * s8); b = cv2.GaussianBlur(q, (0, 0), 8.0 * s8); c = cv2.GaussianBlur(q, (0, 0), 24.0 * s8)
    return cv2.resize(a * 0.35 + b * 0.8 + c * 1.5, (W, H), interpolation=cv2.INTER_LINEAR)

def scatter(cv, amt):
    """light scattered by the fog around every bright source: a wide, low-res blur of the emissive buffer."""
    if amt <= 0: return
    W, H = cv.W, cv.H
    q = cv2.resize(cv.emis, (max(8, W // 8), max(8, H // 8)), interpolation=cv2.INTER_AREA)
    s8 = W / 240.0                                  # blur radii scale with the frame
    a = cv2.GaussianBlur(q, (0, 0), 3.0 * s8); b = cv2.GaussianBlur(q, (0, 0), 9.0 * s8); c = cv2.GaussianBlur(q, (0, 0), 26.0 * s8)
    cv.img += cv2.resize(a * 0.5 + b * 0.9 + c * 1.4, (W, H), interpolation=cv2.INTER_LINEAR) * amt

def fog_color(S):
    d = float(S.get('dusk', 0.0))
    return (hexc('0b1220') * 0.8 * (1 - d) + hexc('20263a') * 0.9 * d + hexc('1c2c38') * 0.15 * S.get('glow', 1.0)).astype(F32)

def reflection(cam, S, t, scale, town_on, pylons, extra):
    """the valley mirrored in the water plane, at reduced resolution, lights stretched into vertical streaks."""
    h = float(S['water'])
    W2, H2 = max(16, int(cam.W * scale)), max(16, int(cam.H * scale))
    c2 = E.Cam.__new__(E.Cam); c2.__dict__.update(cam.__dict__)
    c2.W, c2.H = W2, H2; c2.fpx = cam.fpx * scale; c2.cx = cam.cx * scale; c2.cy = cam.cy * scale; c2._dirs = None
    rv = E.Canvas(c2)
    SK.sky(rv, dict(S, mirror=True, stars=S.get('stars', 0) * 0.6))
    draw_hills(rv, S, mirror_h=h)
    monos = [('A', MONO_A)] + ([('B', MONO_B)] if S.get('second', 0) > 0 else [])
    for w, M in monos: draw_monolith(rv, M, S, t, w, mirror_h=h)
    if pylons: draw_pylons(rv, S, t, mirror_h=h)
    if town_on: draw_town(rv, S, t, mirror_h=h, max_dist=1400)
    # light streaks on rippled water
    e = rv.emis
    st = cv2.GaussianBlur(e, (0, 0), sigmaX=0.8, sigmaY=6.0 * scale * 2) * 2.2
    img = rv.img + st
    img = cv2.GaussianBlur(img, (0, 0), sigmaX=0.6, sigmaY=1.6)
    return cv2.resize(img, (cam.W, cam.H), interpolation=cv2.INTER_LINEAR) * 0.92

def compose(cv, extra_emis=1.0):
    """colour + emissive into one linear image."""
    return cv.img + cv.emis * extra_emis

# ---------------------------------------------------------------- foreground reeds / grass
def draw_reeds(cv, S, t, x0, x1, z0, z1, n=260, hmin=0.5, hmax=1.6, seed=3, wind=1.0, col=None):
    """grass and reeds as anti-aliased blades in a world rectangle (they sway with the wind)."""
    cam = cv.cam; r = np.random.default_rng(seed)
    amb = ambient_light(S)
    col = col if col is not None else hexc('0c0f0c') * (amb * 4 + 0.0015)
    X = r.uniform(x0, x1, n); Z = r.uniform(z0, z1, n); Hh = r.uniform(hmin, hmax, n); ph = r.uniform(0, 6.28, n)
    lean = r.normal(0, 0.18, n)
    d = np.hypot(X - cam.eye[0], Z - cam.eye[2]); order = np.argsort(-d)
    for i in order:
        sway = (math.sin(t * 1.3 + ph[i]) * 0.08 + math.sin(t * 2.9 + ph[i] * 1.7) * 0.03) * wind
        pts = []
        for s_ in np.linspace(0, 1, 6):
            bend = (lean[i] + sway) * s_ ** 1.6
            pts.append((X[i] + bend * Hh[i], Hh[i] * s_ * (1 - 0.08 * s_ * s_), Z[i] + bend * 0.3))
        pts = np.array(pts, F32)
        for a, b in zip(pts[:-1], pts[1:]):
            cv.line3(a, b, col, width_m=0.018 + 0.01 * r.random(), min_px=1.2, op=0.97)
