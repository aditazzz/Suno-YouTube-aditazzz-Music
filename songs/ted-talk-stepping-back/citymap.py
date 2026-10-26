"""The city around the office, the countryside around the city and the clouds above it, as a clean light map.

World units are metres (x east, y south) with the standup at (0, 0). The city is a grid of 120 m blocks; buildings,
trees and cars exist near the middle (they only show when you are close), blocks everywhere in the city, and beyond
it towns, lakes, highways and land cover. Ted's buzzwords are the place names."""
import math
from functools import lru_cache
import numpy as np, cv2
from shapely.geometry import LineString, Point
import zoomnoise as ZN
from office import rgb8, mix8, rects, circles, poly, lines, SH, SC, BLD, draw_office, apply_shadow

STREET = rgb8('fdfcf9'); BLOCK_DT = rgb8('e3e0db'); BLOCK_MID = rgb8('e8e5df'); BLOCK_RES = rgb8('ecebe3'); YARD = rgb8('e2ead7')
PARK = rgb8('cde4bf'); PATH = rgb8('f3f0e6'); TREE = rgb8('a3cc8f'); TREE2 = rgb8('88b973'); WATER = rgb8('a7d1ec'); BANK = rgb8('cae3bd')
HWY = rgb8('f5cd75'); HWY_C = rgb8('dcae57'); AVE = rgb8('ffffff'); AVE_C = rgb8('d8d2c6'); PLAZA = rgb8('efebe3')
URBAN = rgb8('e7e4de'); LAND_A = rgb8('e9eedd'); LAND_B = rgb8('efeadb'); FOREST = rgb8('cfe2c0'); FIELD = rgb8('e6ebd2')
ROOF_DT = [rgb8(h) for h in ('cdd2d8', 'c4c9d0', 'd5d6d5', 'bdc3cb', 'd9dbde', 'c9ccd1')]
ROOF_MID = [rgb8(h) for h in ('d6d1c9', 'ccc7be', 'dbd7cf', 'c8c3ba', 'd1ccc5', 'c3bfb8')]
ROOF_RES = [rgb8(h) for h in ('c6a596', 'b6a18c', 'a8a29b', 'c0b1a1', '9b958e', 'c9b6a4')]
CARS = [rgb8(h) for h in ('f4f4f2', '2b2d31', '9aa1a8', 'b8382e', '3a5a86', 'd8d2c4')]

PITCH = 140.0; HB = 60.0                           # block pitch and half block (streets 20 m)
SUN_AZ, SUN_EL = 125.0, 30.0                       # 9:15 a.m. in late October
_a = math.radians(SUN_AZ + 180)
SHD = np.array([math.sin(_a), -math.cos(_a)]) / math.tan(math.radians(SUN_EL))   # shadow offset per metre of height

def catmull(P, n=12):
    P = np.asarray(P, float); out = []
    for i in range(len(P) - 1):
        p0, p1, p2, p3 = P[max(i - 1, 0)], P[i], P[i + 1], P[min(i + 2, len(P) - 1)]
        for u in np.linspace(0, 1, n, endpoint=False):
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u + (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3))
    out.append(P[-1]); return np.array(out)

def seg_dist(X, L):
    """distance from points X (n,2) to a polyline L (m,2)"""
    A = L[:-1][None]; B = L[1:][None]; P = X[:, None]
    AB = B - A; t = np.clip(np.sum((P - A) * AB, 2) / np.maximum(np.sum(AB * AB, 2), 1e-9), 0, 1)
    D = A + AB * t[..., None] - P
    return np.sqrt(np.min(np.sum(D * D, 2), 1))

# ---------------------------------------------------------------- the world (generated once per process)
class World:
    def __init__(s):
        rng = np.random.default_rng(11)
        # rivers, highways, lakes
        s.river = catmull([(-90000, -30000), (-50000, -16000), (-24000, -9000), (-11000, -4800), (-4500, -2600), (-2000, -1500),
                           (-600, -1260), (900, -1500), (2200, -900), (3600, 600), (5600, 1400), (9000, 2900), (16000, 4200),
                           (30000, 9000), (60000, 14000), (95000, 26000)], 16)
        s.river_w = 95.0
        s.hwys = [catmull([(2150, -95000), (2300, -30000), (2150, -9000), (2100, 0), (2250, 9000), (1900, 30000), (2600, 95000)], 10),
                  catmull([(-95000, 2650), (-30000, 2400), (-9000, 2700), (0, 2600), (9000, 2500), (30000, 3100), (95000, 2700)], 10)]
        ring = [(7600 * (1 + 0.06 * math.sin(3 * a)) * math.cos(a), 7600 * (1 + 0.06 * math.sin(3 * a)) * math.sin(a)) for a in np.linspace(0, 2 * np.pi, 49)]
        s.hwys.append(np.array(ring))
        s.hwy_w = 58.0
        # towns (Ted's words), placed around the city; highways lead to them
        s.towns = [dict(name="So", c=(-42000, -21000), r=2600), dict(name="Right?", c=(38000, 26000), r=2300),
                   dict(name="Journey", c=(-30000, 34000), r=2100), dict(name="Unlock", c=(52000, -14000), r=2400),
                   dict(name="The Real Question", c=(5000, 61000), r=1900), dict(name="Story", c=(-66000, 9000), r=2200),
                   dict(name="Circle Back", c=(70000, 40000), r=1800), dict(name="Synergy", c=(-12000, -68000), r=2000)]
        for T in s.towns:
            cx, cy = T["c"]; s.hwys.append(catmull([(0.35 * cx, 0.35 * cy + 2600), (0.7 * cx + 3000, 0.7 * cy), (cx, cy)], 10))
        s.lakes = [s._lake((16500, -15500), 5200, 2600, 0.35, 3), s._lake((-23000, 22000), 3200, 1900, -0.6, 5),
                   s._lake((60000, -40000), 7000, 3000, 0.9, 7), s._lake((-50000, -45000), 4200, 2600, 0.2, 9)]
        s.lake_names = [("Lake Pause", (16500, -15500)), ("Pause Reservoir", (-23000, 22000))]
        # city blocks
        n = 105; ii, jj = np.meshgrid(np.arange(-n, n + 1), np.arange(-n, n + 1))
        cx = ii * PITCH; cy = jj * PITCH; r = np.hypot(cx, cy); ang = np.arctan2(cy, cx)
        edge = 10500 * (1 + 0.20 * np.sin(3 * ang + 1.3) + 0.10 * np.sin(5 * ang + 0.4) + 0.06 * np.sin(11 * ang + 2.2))
        u = rng.random(r.shape)
        keep = (r < edge) | ((r < edge * 1.3) & (u < np.clip(1 - (r - edge) / (0.3 * edge), 0, 1) ** 2 * 0.30))
        C = np.stack([cx[keep], cy[keep]], 1); I = np.stack([ii[keep], jj[keep]], 1)
        d_riv = seg_dist(C, s.river); C_ok = d_riv > s.river_w / 2 + 95
        d_h = np.min(np.stack([seg_dist(C, h) for h in s.hwys[:3]], 1), 1); C_ok &= d_h > s.hwy_w / 2 + 75
        for L in s.lakes: C_ok &= ~s._inside(C, L, 120)
        C = C[C_ok]; I = I[C_ok]; rr = np.hypot(C[:, 0], C[:, 1])
        h = (np.sin(I[:, 0] * 12.9898 + I[:, 1] * 78.233) * 43758.5453) % 1.0
        kind = np.where(rr < 1150, 0, np.where(rr < 3400, 1, 2))
        park = (h < 0.055) & (rr > 700)
        named = (I[:, 0] >= -6) & (I[:, 0] <= -4) & (I[:, 1] >= 2) & (I[:, 1] <= 3)
        park |= named
        kind = np.where(park, 3, kind); kind[(I[:, 0] == 0) & (I[:, 1] == 0)] = 4          # 4 = our office block
        s.blocks = np.concatenate([C - HB, C + HB], 1); s.bkind = kind; s.bI = I; s.br = rr
        s.park_named = s.blocks[named].copy()
        # buildings, trees, yards near the middle
        s._buildings(rng); s._trees(rng); s._cars(rng)
        # bridges where avenues cross the river
        s.bridges = []
        R = LineString(s.river)
        for k in range(-60, 61, 4):
            x = k * PITCH + PITCH / 2
            g = R.intersection(LineString([(x, -20000), (x, 20000)]))
            for p in getattr(g, "geoms", [g]):
                if p.is_empty: continue
                s.bridges.append(("v", x, p.y))
            y = k * PITCH + PITCH / 2
            g = R.intersection(LineString([(-20000, y), (20000, y)]))
            for p in getattr(g, "geoms", [g]):
                if p.is_empty: continue
                s.bridges.append(("h", p.x, y))
        s._urban_masks()

    def _lake(s, c, ax, ay, rot, seed):
        rng = np.random.default_rng(seed); a = np.linspace(0, 2 * np.pi, 400, endpoint=False)
        rad = np.ones_like(a)
        for k, amp in ((2, 0.12), (3, 0.10), (5, 0.07), (9, 0.05), (17, 0.03), (33, 0.018), (61, 0.01)):
            rad += amp * np.sin(k * a + rng.uniform(0, 6.28)) * rng.uniform(0.6, 1.2)
        x = ax * rad * np.cos(a); y = ay * rad * np.sin(a); cr, sr = math.cos(rot), math.sin(rot)
        return np.stack([c[0] + x * cr - y * sr, c[1] + x * sr + y * cr], 1)

    def _inside(s, X, L, m):
        import shapely
        from shapely.geometry import Polygon
        return shapely.contains_xy(Polygon(L).buffer(m), X[:, 0], X[:, 1])

    def _buildings(s, rng):
        B = []      # x0, y0, x1, y1, height, kind, colour index
        sel = np.nonzero(s.br < 3300)[0]
        for bi in sel:
            x0, y0, x1, y1 = s.blocks[bi]; k = s.bkind[bi]; r = s.br[bi]
            if k == 3: continue
            if k == 4:
                B.append((*BLD, 42.0, 4, 0)); continue
            if k == 0:
                split = rng.choice([1, 2, 2, 3, 4])
                lots = [(x0, y0, x1, y1)] if split == 1 else ([(x0, y0, (x0 + x1) / 2, y1), ((x0 + x1) / 2, y0, x1, y1)] if split == 2 else
                        ([(x0, y0, x1, (y0 + y1) / 2), (x0, (y0 + y1) / 2, x1, y1)] if split == 3 else
                         [(x0, y0, (x0 + x1) / 2, (y0 + y1) / 2), ((x0 + x1) / 2, y0, x1, (y0 + y1) / 2), (x0, (y0 + y1) / 2, (x0 + x1) / 2, y1), ((x0 + x1) / 2, (y0 + y1) / 2, x1, y1)]))
                for (a0, b0, a1, b1) in lots:
                    ins = rng.uniform(4, 9); hgt = rng.uniform(35, 210) * max(0.35, 1 - r / 1600)
                    B.append((a0 + ins, b0 + ins, a1 - ins, b1 - ins, hgt, 0, rng.integers(len(ROOF_DT))))
            elif k == 1:
                nx, ny = rng.choice([2, 3]), rng.choice([2, 3, 4])
                for a in range(nx):
                    for b in range(ny):
                        if rng.random() < 0.12: continue
                        a0 = x0 + 4 + a * (112 / nx); b0 = y0 + 4 + b * (112 / ny)
                        B.append((a0 + 2.5, b0 + 2.5, a0 + 112 / nx - 2.5, b0 + 112 / ny - 2.5, rng.uniform(9, 42), 1, rng.integers(len(ROOF_MID))))
            else:
                for side in (0, 1):
                    yy = y0 + 9 if side == 0 else y1 - 21
                    for q in range(9):
                        if rng.random() < 0.08: continue
                        xx = x0 + 3 + q * 12.7 + rng.uniform(0, 2)
                        B.append((xx, yy, xx + rng.uniform(8.5, 10.5), yy + rng.uniform(10, 12), rng.uniform(5.5, 8.5), 2, rng.integers(len(ROOF_RES))))
        s.bld = np.array(B, float)

    def _trees(s, rng):
        T = []
        sel = np.nonzero(s.br < 2700)[0]
        for bi in sel:
            x0, y0, x1, y1 = s.blocks[bi]; k = s.bkind[bi]
            per = []
            for q in np.arange(6, 114, 9.5):
                per += [(x0 + q, y0 + 4.5), (x0 + q, y1 - 4.5), (x0 + 4.5, y0 + q), (x1 - 4.5, y0 + q)]
            for p in per:
                if rng.random() < (0.35 if k == 0 else 0.15): continue
                T.append((p[0] + rng.normal(0, 0.6), p[1] + rng.normal(0, 0.6), rng.uniform(2.6, 3.8)))
            if k == 3:
                for _ in range(int(rng.integers(25, 45))): T.append((rng.uniform(x0 + 8, x1 - 8), rng.uniform(y0 + 8, y1 - 8), rng.uniform(3, 6)))
            if k == 2:
                for _ in range(int(rng.integers(6, 14))): T.append((rng.uniform(x0 + 8, x1 - 8), rng.uniform(y0 + 36, y1 - 36), rng.uniform(3, 5.5)))
        T = np.array(T, float)
        if len(s.bld):   # no trees inside buildings
            B = s.bld; keep = np.ones(len(T), bool)
            for chunk in range(0, len(T), 4000):
                P = T[chunk:chunk + 4000, None, :2]
                inside = (P[..., 0] > B[None, :, 0] - 1) & (P[..., 0] < B[None, :, 2] + 1) & (P[..., 1] > B[None, :, 1] - 1) & (P[..., 1] < B[None, :, 3] + 1)
                keep[chunk:chunk + 4000] = ~inside.any(1)
            T = T[keep]
        s.trees = T

    def _cars(s, rng):
        cars = []
        for k in range(-11, 11):
            line = k * PITCH + PITCH / 2
            for d in (-1, 1):
                for horiz in (0, 1):
                    n = int(rng.integers(30, 60))
                    for _ in range(n):
                        cars.append((horiz, line + d * 4.2, rng.uniform(-1600, 1600), d * rng.uniform(7, 13), rng.integers(len(CARS))))
        s.cars = np.array(cars, float)

    def _urban_masks(s):
        """rasters of 'built-up land' (blocks + streets): one for the city (10 m/px), one for the region (100 m/px)."""
        s.um = []
        for half, n in ((20480.0, 4096), (204800.0, 4096)):
            m = np.zeros((n, n), np.uint8); k = n / (2 * half)
            Q = ((s.blocks.reshape(-1, 2, 2) + half) * k).reshape(-1, 4)
            pad = 12 * k
            for (a, b, c, d) in Q:
                cv2.rectangle(m, (int(a - pad), int(b - pad)), (int(math.ceil(c + pad)), int(math.ceil(d + pad))), 255, -1)
            for T in s.towns:
                cx, cy = T["c"]; rr = T["r"]
                rng = np.random.default_rng(int(abs(cx)) % 997)
                for _ in range(int(rr / 70) ** 2 // 3):
                    a = rng.uniform(0, 2 * np.pi); q = rr * math.sqrt(rng.uniform(0, 1))
                    bx = round((cx + q * math.cos(a)) / PITCH) * PITCH; by = round((cy + q * math.sin(a)) / PITCH) * PITCH
                    x0, y0 = (bx - 70 + half) * k, (by - 70 + half) * k
                    cv2.rectangle(m, (int(x0), int(y0)), (int(x0 + 140 * k), int(y0 + 140 * k)), 255, -1)
            m = cv2.GaussianBlur(m, (0, 0), 0.8)
            s.um.append((half, n, m))

W_ = None
def world():
    global W_
    if W_ is None: W_ = World()
    return W_

# ---------------------------------------------------------------- drawing
def warp_raster(view, half, n, ras, out_hw, interp=cv2.INTER_LINEAR):
    """sample a square raster covering [-half, half]^2 metres into the view."""
    k = n / (2 * half)
    # pixel -> world -> raster: r = (Ai (p - b) + half) * k
    M = np.zeros((2, 3)); M[:, :2] = view.Ai * k; M[:, 2] = (-view.Ai @ view.b + half) * k
    return cv2.warpAffine(ras, M, (out_hw[1], out_hw[0]), flags=interp | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_CONSTANT, borderValue=0)

def land(view, step=4):
    """the countryside: soft land cover from world-anchored noise (computed at 1/step resolution)."""
    X, Y = view.grid(step); mpp = view.mpp * step
    a = ZN.fbm(X, Y, mpp, seed=3, lam_max=80000, lam_min=200, gain=0.6)
    f = ZN.fbm(X, Y, mpp, seed=5, lam_max=30000, lam_min=150, gain=0.55)
    fld = ZN.fbm(X, Y, mpp, seed=8, lam_max=3000, lam_min=150, gain=0.5)
    base = np.array(LAND_A, np.float32)[None, None] * (1 - a[..., None]) + np.array(LAND_B, np.float32)[None, None] * a[..., None]
    fo = np.clip((f - 0.56) / 0.08, 0, 1)[..., None]
    base = base * (1 - fo) + np.array(FOREST, np.float32) * fo
    base += ((fld - 0.5) * 9.0)[..., None]
    return cv2.resize(np.clip(base, 0, 255).astype(np.uint8), (view.W, view.H), interpolation=cv2.INTER_LINEAR)

def draw_map(view, t, z, st):
    """the light map at log-scale z (log10 of the 16:9 frame width in metres). st: dict of story state.
    Returns a uint8 RGB canvas and a float shadow mask (0..1)."""
    Wd = world(); H, W = view.H, view.W
    if z >= 3.85: cv = land(view)
    else: cv = np.empty((H, W, 3), np.uint8); cv[:] = STREET
    shadow = np.zeros((H, W), np.uint8)
    b = view.box; mg = 200
    # lakes + the river (under the city)
    for L in Wd.lakes:
        if view.sees(L[:, 0].min(), L[:, 1].min(), L[:, 0].max(), L[:, 1].max(), mg): poly(cv, view, L, WATER)
    # built-up land
    if z >= 3.85:
        A = []
        if z < 4.9:
            half, n, m = Wd.um[0]; A.append(warp_raster(view, half, n, m, (H, W)))
        if z > 4.3:
            half, n, m = Wd.um[1]; A.append(warp_raster(view, half, n, m, (H, W)))
        a = (np.maximum.reduce(A) if len(A) > 1 else A[0]).astype(np.float32)[..., None] / 255.0
        base = np.array(mix8(STREET, URBAN, float(np.clip((z - 3.85) / 0.35, 0, 1))), np.float32)
        cv = (cv.astype(np.float32) * (1 - a) + base * a).astype(np.uint8)
    # blocks
    kb = float(np.clip((5.35 - z) / 0.45, 0, 1))
    if kb > 0:
        sel = (Wd.blocks[:, 2] > b[0] - mg) & (Wd.blocks[:, 0] < b[2] + mg) & (Wd.blocks[:, 3] > b[1] - mg) & (Wd.blocks[:, 1] < b[3] + mg)
        for kind, col in ((0, BLOCK_DT), (1, BLOCK_MID), (2, BLOCK_RES), (3, PARK), (4, PLAZA)):
            R = Wd.blocks[sel & (Wd.bkind == kind)]
            if len(R): rects(cv, view, R, mix8(URBAN, col, kb) if z > 4.6 else col)
        # yards inside residential blocks
        if z < 3.6:
            R = Wd.blocks[sel & (Wd.bkind == 2)]
            if len(R): rects(cv, view, R + np.array([4, 32, -4, -32]), mix8(BLOCK_RES, YARD, float(np.clip((3.6 - z) / 0.4, 0, 1))))
            R = Wd.blocks[sel & (Wd.bkind == 3)]
            if len(R) and z < 3.2:
                for r_ in R: lines(cv, view, [[(r_[0] + 10, r_[1] + 10), (r_[2] - 10, r_[3] - 10)], [(r_[0] + 10, r_[3] - 10), (r_[2] - 10, r_[1] + 10)]], PATH, width_m=3.0)
    # avenues (every 4th street is wider, with a casing) at city scale
    if 2.4 < z < 4.4:
        k = float(np.clip((z - 2.4) / 0.3, 0, 1) * np.clip((4.4 - z) / 0.3, 0, 1))
        segs = []
        for q in range(-60, 61, 4):
            v = q * PITCH + PITCH / 2
            if b[0] - mg < v < b[2] + mg: segs.append([(v, max(b[1] - mg, -15000)), (v, min(b[3] + mg, 15000))])
            if b[1] - mg < v < b[3] + mg: segs.append([(max(b[0] - mg, -15000), v), (min(b[2] + mg, 15000), v)])
        w = max(1.0, 26.0 / view.mpp)
        for sg in segs:
            q = view.to_px16(np.array(sg)); cv2.polylines(cv, [q], False, mix8(STREET, AVE_C, k), int(round(w + 2)), cv2.LINE_AA, SH)
        for sg in segs:
            q = view.to_px16(np.array(sg)); cv2.polylines(cv, [q], False, AVE, max(1, int(round(w))), cv2.LINE_AA, SH)
    # river (banks, water) and bridges
    def polyline(P, col, wm, minpx=1.0):
        if not view.sees(P[:, 0].min(), P[:, 1].min(), P[:, 0].max(), P[:, 1].max(), wm + mg): return
        ok = (P[:, 0] > b[0] - 4000) & (P[:, 0] < b[2] + 4000) & (P[:, 1] > b[1] - 4000) & (P[:, 1] < b[3] + 4000)
        idx = np.nonzero(ok)[0]
        if not len(idx): return
        # split into contiguous runs
        runs = np.split(idx, np.nonzero(np.diff(idx) > 1)[0] + 1)
        w = max(minpx, wm / view.mpp)
        for rn in runs:
            a0, a1 = max(rn[0] - 1, 0), min(rn[-1] + 2, len(P))
            q = view.to_px16(P[a0:a1]); cv2.polylines(cv, [q], False, col, max(1, int(round(w))), cv2.LINE_AA, SH)
    if z > 2.2:
        polyline(Wd.river, BANK, Wd.river_w + 34, 1.0)
        polyline(Wd.river, WATER, Wd.river_w, 1.4)
        if z < 4.3:
            for (o, x, y) in Wd.bridges:
                if not view.sees(x - 120, y - 120, x + 120, y + 120): continue
                L = (Wd.river_w + 40) / 2
                seg = [(x, y - L), (x, y + L)] if o == "v" else [(x - L, y), (x + L, y)]
                q = view.to_px16(np.array(seg)); cv2.polylines(cv, [q], False, STREET, max(1, int(round(20 / view.mpp))), cv2.LINE_AA, SH)
    # highways
    if z > 2.4:
        for h in Wd.hwys:
            polyline(h, HWY_C, Wd.hwy_w + 10, 2.4 if z > 4.4 else 1.0)
        for h in Wd.hwys:
            polyline(h, HWY, Wd.hwy_w, 1.5 if z > 4.4 else 1.0)
    # buildings, trees, cars (close up only)
    kc = float(np.clip((3.45 - z) / 0.35, 0, 1))
    T = Wd.trees
    if kc > 0 and len(Wd.bld):
        B = Wd.bld
        B = B[(B[:, 2] > b[0] - 400) & (B[:, 0] < b[2] + 400) & (B[:, 3] > b[1] - 400) & (B[:, 1] < b[3] + 400)]
        if len(T): T = T[(T[:, 0] > b[0] - 20) & (T[:, 0] < b[2] + 20) & (T[:, 1] > b[1] - 20) & (T[:, 1] < b[3] + 20)]
        # shadows on the ground: each footprint swept away from the sun (+ trees), applied before the roofs go on
        if len(B):
            d = SHD[None] * B[:, 4:5]
            c0 = B[:, [0, 1]]; c1 = B[:, [2, 1]]; c2 = B[:, [2, 3]]; c3 = B[:, [0, 3]]
            S = np.stack([c2, c3, c3 + d, c0 + d, c1 + d, c1], 1)
            cv2.fillPoly(shadow, list(view.to_px16(S)), 255, cv2.LINE_AA, SH)
        if len(T) and z < 3.4: circles(shadow, view, T[:, :2] + SHD[None] * 7.0, T[:, 2], 255)
        apply_shadow(cv, view, shadow, 0.22 * kc)
        # roofs
        for kind, pal in ((0, ROOF_DT), (1, ROOF_MID), (2, ROOF_RES)):
            Bk = B[B[:, 5] == kind]
            for ci, col in enumerate(pal):
                R = Bk[Bk[:, 6] == ci][:, :4]
                if len(R): rects(cv, view, R, mix8(BLOCK_MID, col, kc), mix8(BLOCK_MID, mix8(col, (60, 60, 60), 0.25), kc) if z < 2.9 else None)
            if kind == 0 and z < 3.0 and len(Bk):   # rooftop plant on the towers
                Rr = Bk[:, :4]; cxy = (Rr[:, :2] + Rr[:, 2:]) / 2
                rects(cv, view, np.concatenate([cxy - 5, cxy + 5], 1), mix8(BLOCK_MID, rgb8('b4b9c0'), kc))
        # trees
        if len(T) and z < 3.4:
            kt = float(np.clip((3.4 - z) / 0.3, 0, 1))
            circles(cv, view, T[:, :2], T[:, 2], mix8(BLOCK_MID, TREE, kt))
            if z < 2.7: circles(cv, view, T[:, :2] - 0.4, T[:, 2] * 0.55, mix8(BLOCK_MID, TREE2, kt))
        # cars
        if z < 3.0:
            C = Wd.cars; tc = st.get("t_traffic", t)
            pos = (C[:, 2] + C[:, 3] * tc + 1600) % 3200 - 1600
            X = np.where(C[:, 0] == 1, pos, C[:, 1]); Y = np.where(C[:, 0] == 1, C[:, 1], pos)
            sel = (X > b[0] - 10) & (X < b[2] + 10) & (Y > b[1] - 10) & (Y < b[3] + 10)
            for ci, col in enumerate(CARS):
                m = sel & (C[:, 4] == ci)
                if not m.any(): continue
                hx = np.where(C[m, 0] == 1, 2.3, 0.95); hy = np.where(C[m, 0] == 1, 0.95, 2.3)
                R = np.stack([X[m] - hx, Y[m] - hy, X[m] + hx, Y[m] + hy], 1)
                rects(cv, view, R, mix8(STREET, col, float(np.clip((3.0 - z) / 0.3, 0, 1))))
    # the office, with its roof off
    ko = float(np.clip((3.3 - z) / 0.5, 0, 1))
    if ko > 0 and view.sees(*BLD, 50):
        draw_office(cv, view, t, k_plan=ko, sit=st.get("sit", 0), phones=st.get("phones", 0),
                    ted_talk=st.get("ted_talk", 1), ghost=st.get("ghost", 0), dana_gone=st.get("dana_gone", 0))
    return cv

# ---------------------------------------------------------------- clouds (above the map, and over the Earth)
def cloud_field(X, Y, mpp):
    """world-anchored cloud density (0..1 before coverage): a weather system around the city."""
    base = ZN.fbm(X, Y, mpp, seed=21, lam_max=1.6e6, lam_min=120, gain=0.56, px_cut=2.5)
    r = np.sqrt(X * X + Y * Y)
    sysm = 0.5 + 0.5 * np.cos(np.clip(r / 2.2e6, 0, 1) * np.pi)          # thicker near the city's weather system
    return base * (0.75 + 0.35 * sysm)

def clouds(view, cover, sun_px=(0.6, -0.4), step=3):
    """RGBA-ish: returns (colour (H,W,3) float, alpha (H,W)) for a cloud deck with the given coverage 0..1."""
    X, Y = view.grid(step); mpp = view.mpp * step
    d = cloud_field(X, Y, mpp)
    thr = 1.02 - cover * 0.62
    a = np.clip((d - thr) / 0.10, 0, 1)
    # light: brighter on the sun side (sample a little toward the sun)
    off = 3.0 * mpp
    d2 = cloud_field(X + sun_px[0] * off, Y + sun_px[1] * off, mpp)
    lit = np.clip(0.80 + (d2 - d) * 6.0 + a * 0.15, 0.55, 1.08)
    col = np.stack([lit * 0.985, lit * 0.99, lit * 1.0], 2)
    a = cv2.resize(a.astype(np.float32), (view.W, view.H), interpolation=cv2.INTER_LINEAR)
    col = cv2.resize(col.astype(np.float32), (view.W, view.H), interpolation=cv2.INTER_LINEAR)
    return col, a
