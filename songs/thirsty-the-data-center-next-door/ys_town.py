"""Town pieces: the high school with its new roof, the water tower, the construction cranes for the second house.
All in valley coordinates; call from a valley render's `extra` hook.
"""
import math
import numpy as np, cv2
import ys_eng as E
from ys_eng import F32, hexc, nrm, sample, fbm_tex, sstep, ease_io
import ys_world as WD

def _box(cv, c, sx, sy, sz, col_fn, cam_cull=True):
    cx, cy, cz = c; x0, x1, z0, z1 = cx - sx / 2, cx + sx / 2, cz - sz / 2, cz + sz / 2; y0, y1 = cy, cy + sy
    faces = [([(x0, y1, z0), (x1, y1, z0), (x1, y0, z0), (x0, y0, z0)], (0, 0, -1)), ([(x1, y1, z1), (x0, y1, z1), (x0, y0, z1), (x1, y0, z1)], (0, 0, 1)),
             ([(x0, y1, z1), (x0, y1, z0), (x0, y0, z0), (x0, y0, z1)], (-1, 0, 0)), ([(x1, y1, z0), (x1, y1, z1), (x1, y0, z1), (x1, y0, z0)], (1, 0, 0)),
             ([(x0, y1, z1), (x1, y1, z1), (x1, y1, z0), (x0, y1, z0)], (0, 1, 0))]
    for pts, n in faces:
        P = np.array(pts, F32); nn = np.array(n, F32)
        if np.dot(nn, P.mean(0) - cv.cam.eye) >= 0: continue
        cv.poly(P, col_fn(nn, P), ztest=True)

def school(cv, S, t, roof_glint=0.0):
    """a long two-storey brick school with a gym whose standing-seam metal roof is brand new (it catches the sky)."""
    cam = cv.cam; c = WD.SCHOOL
    amb = WD.ambient_light(S); dusk = float(S.get('dusk', 0))
    sun = nrm([math.sin(S.get('sun_az', 0)), 0.25, math.cos(S.get('sun_az', 0))])
    def brick(n, P):
        def f(X, Y, Z, m):
            Pw = WD._world_from_screen(cam, X, Y, Z)
            u = (Pw[..., 0] + Pw[..., 2]); v = Pw[..., 1]
            row = np.floor(v / 0.075); off = (row % 2) * 0.11
            mortar = (np.abs(((u + off) % 0.22) - 0.11) > 0.1) | (np.abs((v % 0.075) - 0.0375) > 0.033)
            tone = 0.85 + 0.3 * sample(fbm_tex(256, 1.0, 151), u * 6, v * 6, 1.0)
            alb = np.where(mortar[..., None], hexc('8a8478')[None, None], hexc('7a3a2c')[None, None] * tone[..., None])
            lit = amb * (1.4 + 0.5 * max(0, float(n[1]))) + hexc('ff9a70') * 0.10 * dusk * max(0.0, float(np.dot(n, sun)))
            # windows: rows of tall classroom windows, some lit warm
            wx = ((u % 3.4) > 0.6) & ((u % 3.4) < 2.6); wy = ((v > 1.0) & (v < 2.6)) | ((v > 4.4) & (v < 6.0))
            win = wx & wy
            wl = np.abs(np.modf(np.sin(np.floor(u / 3.4) * 12.99 + np.floor(v / 3.4) * 7.7) * 43758.5)[0]) > 0.55
            col = alb * lit[None, None]
            col = np.where(win[..., None], hexc('0c1016') * 0.02 + hexc('ffd49a') * 0.18 * wl[..., None] * S.get('town_lights', 1.0), col)
            return col.astype(F32)
        return f
    _box(cv, (c[0] - 20, 0, c[2]), 70, 7.2, 16, brick)
    # parapet line
    # the gym: a taller block with a shallow gable metal roof (new: it shines)
    gx, gz = c[0] + 30, c[2] + 2
    _box(cv, (gx, 0, gz), 30, 9.0, 28, brick)
    ridge = 12.0
    roof_f = np.array([[gx - 16, ridge, gz], [gx + 16, ridge, gz], [gx + 16, 9.0, gz - 15], [gx - 16, 9.0, gz - 15]], F32)
    roof_b = np.array([[gx + 16, ridge, gz], [gx - 16, ridge, gz], [gx - 16, 9.0, gz + 15], [gx + 16, 9.0, gz + 15]], F32)
    for P, n in ((roof_f, nrm([0, 1, -0.2])), (roof_b, nrm([0, 1, 0.2]))):
        if np.dot(n, P.mean(0) - cam.eye) >= 0: continue
        def metal(X, Y, Z, m, n=n):
            Pw = WD._world_from_screen(cam, X, Y, Z)
            seam = np.exp(-(((Pw[..., 0] - gx) % 0.6) - 0.3) ** 2 / 0.0006)
            V = E.nrm(cam.eye) * 0
            refl = hexc('ff9a8a') * dusk * 0.5 + hexc('9fb8cc') * 0.05
            # a sheen that slides along the roof (the new metal catching the sky)
            sweep = np.exp(-((Pw[..., 0] - (gx - 18 + 36 * roof_glint)) / 5.0) ** 2) * (roof_glint > 0)
            col = hexc('8a9098') * (amb * 2 + 0.004) + refl * (0.25 + 0.5 * seam[..., None]) * 0.2 + hexc('ffe2c8') * (sweep * 0.6)[..., None]
            return col.astype(F32)
        cv.poly(P, metal, ztest=True)
    # flag pole + flag
    fp = np.array([c[0] - 62, 0, c[2] - 14], F32)
    cv.line3(fp, fp + np.array([0, 11, 0], F32), hexc('c8c8c8') * (amb * 3 + 0.004), width_m=0.09)
    wave = t * 2.2
    for k in range(12):
        x0 = k * 0.16; x1 = (k + 1) * 0.16
        y0 = 10.9 - 0.04 * math.sin(wave + k * 0.6); y1 = 10.9 - 0.04 * math.sin(wave + (k + 1) * 0.6)
        P = np.array([[fp[0] + x0, y0, fp[2] + 0.12 * math.sin(wave + k)], [fp[0] + x1, y1, fp[2] + 0.12 * math.sin(wave + k + 1)],
                      [fp[0] + x1, y1 - 1.1, fp[2] + 0.12 * math.sin(wave + k + 1)], [fp[0] + x0, y0 - 1.1, fp[2] + 0.12 * math.sin(wave + k)]], F32)
        def flagc(X, Y, Z, m, k=k):
            Pw = WD._world_from_screen(cam, X, Y, Z)
            v = 10.9 - Pw[..., 1]
            stripe = (np.floor(v / (1.1 / 13)) % 2)
            c_ = np.where(stripe[..., None] > 0, hexc('d8d2c4')[None, None], hexc('9a1c2a')[None, None])
            canton = (v < 0.6) & (Pw[..., 0] - fp[0] < 0.8)
            c_ = np.where(canton[..., None], hexc('1c2a58')[None, None], c_)
            return (c_ * (amb * 3 + 0.003 + hexc('ff9a70') * 0.08 * dusk)).astype(F32)
        cv.poly(P, flagc, ztest=True)

def cranes(cv, S, t, grow):
    """tower cranes over the second house's site; their red lights blink."""
    if grow <= 0.01: return
    M = WD.MONO_B
    amb = WD.ambient_light(S)
    col = hexc('0d0f12') + amb * 0.3
    A, B = [], []
    for i, (fx, fz, hgt, jib, ang) in enumerate(((0.25, 0.3, 92, 60, 0.6), (0.62, 0.55, 104, 70, 2.4), (0.85, 0.2, 86, 55, -0.9))):
        base = np.array([M['x0'] + fx * (M['x1'] - M['x0']), 0, M['z0'] + fz * (M['z1'] - M['z0'])], F32)
        a = ang + 0.04 * math.sin(t * 0.1 + i)
        mast_top = base + np.array([0, hgt, 0], F32)
        for dx, dz in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            A.append(base + np.array([dx, 0, dz], F32) * 1.0); B.append(mast_top + np.array([dx, 0, dz], F32) * 1.0)
        for y in np.arange(0, hgt, 4.0):
            A.append(base + np.array([-1, y, -1], F32)); B.append(base + np.array([1, y + 4, 1], F32))
        d = np.array([math.cos(a), 0, math.sin(a)], F32)
        A.append(mast_top - d * jib * 0.3); B.append(mast_top + d * jib)
        A.append(mast_top - d * jib * 0.3 + np.array([0, -2, 0], F32)); B.append(mast_top + d * jib + np.array([0, -2, 0], F32))
        A.append(mast_top + np.array([0, 8, 0], F32)); B.append(mast_top + d * jib * 0.7)
        A.append(mast_top + np.array([0, 8, 0], F32)); B.append(mast_top - d * jib * 0.3)
        hook = mast_top + d * jib * (0.45 + 0.2 * math.sin(t * 0.07 + i))
        A.append(hook); B.append(hook - np.array([0, 30 + 10 * math.sin(t * 0.05 + i), 0], F32))
        blink = 1.0 if (int(t * 1.2 + i * 0.4) % 2 == 0) else 0.15
        E.lights(cv, [mast_top + np.array([0, 8.5, 0], F32), mast_top + d * jib], WD.RED_AV, 3.0 * blink * grow, size_m=0.6)
    E.lines_batch(cv, np.array(A, F32), np.array(B, F32), col, width_m=0.35, min_px=0.6, op=0.95 * min(1.0, grow * 2))

def fireflies(img, cam, t, center, n=14, spread=(6.0, 1.2, 8.0), gain=1.0, seed=3):
    """a few fireflies over the creek: slow drifting warm points that blink on and off."""
    r = np.random.default_rng(seed)
    P = []; w = []
    for k in range(n):
        ph = r.uniform(0, 100); sp = r.uniform(0.2, 0.5)
        p = np.array(center, F32) + np.array([math.sin(t * sp * 0.7 + ph) * spread[0], 0.4 + abs(math.sin(t * sp * 0.5 + ph * 1.3)) * spread[1], math.cos(t * sp * 0.6 + ph * 0.7) * spread[2]], F32)
        on = max(0.0, math.sin(t * r.uniform(0.6, 1.4) + ph)) ** 6
        P.append(p); w.append(on)
    x, y, z = cam.project(np.array(P, F32))
    for xi, yi, zi, wi in zip(x, y, z, w):
        if zi < 0.5 or wi < 0.02: continue
        E.soft_glow(img, xi, yi, max(1.2, 0.05 * cam.fpx / zi), hexc('d8ff70') * 0.7 + hexc('ffd060') * 0.3, wi * 0.5 * gain)
        E.soft_glow(img, xi, yi, max(4.0, 0.3 * cam.fpx / zi), hexc('d8ff70'), wi * 0.04 * gain)
