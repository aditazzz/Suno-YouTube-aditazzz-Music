"""Her house on Willow Road: a two-storey farmhouse on the river bank, its porch facing the facility across the water.
Plus what ends up in her yard: server racks (one, then a row, then the whole lawn), and the electric meter.

All in valley coordinates. Local frame: F = toward the facility (front), R = right when facing it, Y up.
draw(cv, S, t)   call from a valley render's `extra` hook.  S: porch (light 0..1), win_up / win_down (her windows),
                 racks (count), rack_red (0..1 all LEDs red), her_porch (None or dict for her silhouette)
"""
import math
from functools import lru_cache
import numpy as np, cv2
import ys_eng as E
from ys_eng import F32, hexc, nrm, sample, fbm_tex
import ys_world as WD
import ys_rooms as RM

F = RM.FWD; R = RM.RIGHT; Y = np.array([0, 1, 0], F32)
BASE = WD.HOUSE.astype(F32)
HW, HD, WALL, PITCH = 4.6, 4.2, 5.9, 0.75          # half width (along R), half depth (along F), wall height, roof pitch
PORCH_D, PORCH_FL, PORCH_RF = 2.4, 0.62, 3.05

def P(r, y, f): return BASE + R * r + Y * y + F * f
def Q(*pts): return np.array([P(*p) for p in pts], F32)

SIDING = hexc('9c978c'); TRIM = hexc('d8d2c4'); ROOF = hexc('2a2a2d'); PORCHF = hexc('4a4038')
PORCH_LIGHT = hexc('ffc27a'); WIN_WARM = hexc('ffbf76')

def _lit(S, n, extra=0.0):
    amb = WD.ambient_light(S)
    fac = float(max(0.0, np.dot(n, F))) * 0.018 * S.get('glow', 1.0) * float(S.get('mono_lights', 1.0))
    return amb * (1.3 + 0.6 * max(0.0, float(n[1]))) + hexc('a8c4d4') * fac + extra

def porch_lit(cam, S, alb, n):
    """per-pixel: the porch light (a bulb under the porch roof by the door) + the facility glow."""
    pl = float(S.get('porch', 1.0))
    bulb = P(0.9, PORCH_RF - 0.35, HD + 0.25)
    nn = np.asarray(n, F32)
    def f(X, Y_, Z, m):
        Pw = WD._world_from_screen(cam, X, Y_, Z)
        d = bulb[None, None] - Pw; d2 = (d * d).sum(-1) + 0.15; dd = np.sqrt(d2)
        ndl = np.clip((d * nn).sum(-1) / dd, 0, 1)
        col = np.asarray(alb, F32) * (_lit(S, nn)[None, None] + PORCH_LIGHT * (pl * 0.9 * ndl / d2)[..., None])
        return col
    return f

def draw(cv, S, t):
    cam = cv.cam
    flip = None
    faces = []
    # walls (front faces the facility) --------------------------------------------------------------
    walls = [
        ('front', [(-HW, WALL, HD), (HW, WALL, HD), (HW, 0, HD), (-HW, 0, HD)], F),
        ('back', [(HW, WALL, -HD), (-HW, WALL, -HD), (-HW, 0, -HD), (HW, 0, -HD)], -F),
        ('left', [(-HW, WALL, -HD), (-HW, WALL, HD), (-HW, 0, HD), (-HW, 0, -HD)], -R),
        ('right', [(HW, WALL, HD), (HW, WALL, -HD), (HW, 0, -HD), (HW, 0, HD)], R),
    ]
    rh = WALL + HD * PITCH
    gables = [('gl', [(-HW, WALL, -HD), (-HW, rh, 0), (-HW, WALL, HD)], -R), ('gr', [(HW, WALL, HD), (HW, rh, 0), (HW, WALL, -HD)], R)]
    roofs = [('rf', [(-HW - 0.4, rh, 0), (HW + 0.4, rh, 0), (HW + 0.4, WALL - 0.3, HD + 0.45), (-HW - 0.4, WALL - 0.3, HD + 0.45)], nrm(Y + F * PITCH)),
             ('rb', [(HW + 0.4, rh, 0), (-HW - 0.4, rh, 0), (-HW - 0.4, WALL - 0.3, -HD - 0.45), (HW + 0.4, WALL - 0.3, -HD - 0.45)], nrm(Y - F * PITCH))]
    for name, pts, n in walls + gables:
        Pq = Q(*pts)
        if np.dot(n, Pq.mean(0) - cam.eye) >= 0: continue
        cv.poly(Pq, siding_fn(cam, S, n, name), ztest=True)
    for name, pts, n in roofs:
        Pq = Q(*pts)
        if np.dot(n, Pq.mean(0) - cam.eye) >= 0: continue
        cv.poly(Pq, ROOF * _lit(S, n), ztest=True)
    # windows -----------------------------------------------------------------------------------------
    up = float(S.get('win_up', 1.0)); dn = float(S.get('win_down', 0.0))
    wins = [((-2.4, 3.55), up, 'bed'), ((2.4, 3.55), 0.0, 'up2'), ((-2.6, 1.15), dn, 'down1'), ((2.6, 1.15), dn * 0.6, 'down2')]
    for (r0, y0), on, nm in wins:
        pts = [(r0 - 0.62, y0 + 1.42, HD + 0.03), (r0 + 0.62, y0 + 1.42, HD + 0.03), (r0 + 0.62, y0, HD + 0.03), (r0 - 0.62, y0, HD + 0.03)]
        Pq = Q(*pts)
        if np.dot(F, Pq.mean(0) - cam.eye) < 0:
            glow = WIN_WARM * on
            base = hexc('0a0c10') * 0.02 + glow * 0.25
            cv.poly(Pq, base, emis=glow * 0.7, ztest=True, write_depth=False)
            # mullions + blinds texture for the bedroom window
            for k in range(1, 3):
                cv.line3(P(r0, y0 + 1.42 * k / 3, HD + 0.05), P(r0 - 0.62, y0 + 1.42 * k / 3, HD + 0.05), TRIM * _lit(S, F) * 0.8, width_m=0.035)
            cv.line3(P(r0, y0, HD + 0.05), P(r0, y0 + 1.42, HD + 0.05), TRIM * _lit(S, F) * 0.8, width_m=0.04)
            for a, b in (((r0 - 0.7, y0 - 0.05), (r0 + 0.7, y0 - 0.05)), ((r0 - 0.7, y0 + 1.47), (r0 + 0.7, y0 + 1.47))):
                cv.line3(P(a[0], a[1], HD + 0.06), P(b[0], b[1], HD + 0.06), TRIM * _lit(S, F), width_m=0.09)
    # porch ------------------------------------------------------------------------------------------
    pf = HD + PORCH_D
    deck = Q((-HW, PORCH_FL, HD), (HW, PORCH_FL, HD), (HW, PORCH_FL, pf), (-HW, PORCH_FL, pf))
    cv.poly(deck, porch_lit(cam, S, PORCHF, Y), ztest=True)
    cv.poly(Q((-HW, PORCH_FL, pf), (HW, PORCH_FL, pf), (HW, 0, pf), (-HW, 0, pf)), porch_lit(cam, S, PORCHF * 0.7, F), ztest=True)
    # steps (centre)
    for k in range(3):
        y = PORCH_FL - (k + 1) * 0.2; f0 = pf + k * 0.3
        cv.poly(Q((-0.8, y + 0.2, f0), (0.8, y + 0.2, f0), (0.8, y + 0.2, f0 + 0.3), (-0.8, y + 0.2, f0 + 0.3)), porch_lit(cam, S, PORCHF * 1.1, Y), ztest=True)
        cv.poly(Q((-0.8, y + 0.2, f0 + 0.3), (0.8, y + 0.2, f0 + 0.3), (0.8, y, f0 + 0.3), (-0.8, y, f0 + 0.3)), porch_lit(cam, S, PORCHF * 0.8, F), ztest=True)
    # porch roof + posts + rail
    cv.poly(Q((-HW - 0.2, PORCH_RF, HD), (HW + 0.2, PORCH_RF, HD), (HW + 0.2, PORCH_RF - 0.3, pf + 0.25), (-HW - 0.2, PORCH_RF - 0.3, pf + 0.25)),
            ROOF * _lit(S, nrm(Y + F * 0.1)), ztest=True)
    cv.poly(Q((-HW - 0.2, PORCH_RF - 0.3, pf + 0.25), (HW + 0.2, PORCH_RF - 0.3, pf + 0.25), (HW + 0.2, PORCH_RF - 0.55, pf + 0.25), (-HW - 0.2, PORCH_RF - 0.55, pf + 0.25)),
            porch_lit(cam, S, TRIM * 0.8, F), ztest=True)
    for r in (-HW + 0.15, -1.1, 1.1, HW - 0.15):
        cv.line3(P(r, PORCH_FL, pf - 0.12), P(r, PORCH_RF - 0.5, pf - 0.12), TRIM * 0.9 * _lit(S, F) + PORCH_LIGHT * 0.02 * float(S.get('porch', 1)), width_m=0.13, min_px=1.0)
    for rr in ((-HW + 0.15, -1.1), (1.1, HW - 0.15)):
        cv.line3(P(rr[0], PORCH_FL + 0.9, pf - 0.12), P(rr[1], PORCH_FL + 0.9, pf - 0.12), TRIM * 0.8 * _lit(S, F), width_m=0.07, min_px=1.0)
        for k in range(1, 9):
            r = rr[0] + (rr[1] - rr[0]) * k / 9
            cv.line3(P(r, PORCH_FL, pf - 0.12), P(r, PORCH_FL + 0.9, pf - 0.12), TRIM * 0.7 * _lit(S, F), width_m=0.035, min_px=0.8)
    # front door (between the lower windows)
    cv.poly(Q((-0.55, 2.75, HD + 0.02), (0.55, 2.75, HD + 0.02), (0.55, PORCH_FL, HD + 0.02), (-0.55, PORCH_FL, HD + 0.02)), porch_lit(cam, S, hexc('3a2420'), F), ztest=True)
    # the porch bulb itself
    if float(S.get('porch', 1.0)) > 0.01:
        E.lights(cv, [P(0.9, PORCH_RF - 0.35, HD + 0.25)], PORCH_LIGHT, 3.0 * float(S.get('porch', 1.0)), size_m=0.07)
    # the electric meter on the right wall
    m = P(HW + 0.02, 1.5, HD - 1.2)
    cv.poly(Q((HW + 0.03, 1.75, HD - 1.38), (HW + 0.03, 1.75, HD - 1.02), (HW + 0.03, 1.25, HD - 1.02), (HW + 0.03, 1.25, HD - 1.38)), hexc('6a6e72') * _lit(S, R) * 1.5, ztest=True)
    # yard: mailbox + the Willow Rd sign by the road behind the house
    draw_sign(cv, S, t)
    # server racks on the lawn
    n_r = int(S.get('racks', 0))
    if n_r > 0: draw_racks(cv, S, t, n_r)

def siding_fn(cam, S, n, name):
    pl = float(S.get('porch', 1.0)); nn = np.asarray(n, F32)
    bulb = P(0.9, PORCH_RF - 0.35, HD + 0.25)
    def f(X, Y_, Z, m):
        Pw = WD._world_from_screen(cam, X, Y_, Z)
        y = Pw[..., 1]
        lap = 0.82 + 0.18 * (((y % 0.2) / 0.2) ** 0.4)             # clapboard laps
        st = sample(fbm_tex(256, 1.4, 121), (Pw[..., 0] + Pw[..., 2]) * 8, y * 2, 1.0)
        alb = SIDING[None, None] * (lap * (0.85 + 0.25 * st))[..., None]
        d = bulb[None, None] - Pw; d2 = (d * d).sum(-1) + 0.2; dd = np.sqrt(d2)
        ndl = np.clip((d * nn).sum(-1) / dd, 0, 1)
        return alb * (_lit(S, nn)[None, None] + PORCH_LIGHT * (pl * 1.1 * ndl / d2)[..., None])
    return f

def draw_sign(cv, S, t):
    cam = cv.cam
    pole = P(HW + 3.0, 0, -HD - 6.0)
    cv.line3(pole, pole + Y * 2.6, hexc('3a3d40') * _lit(S, F) * 3, width_m=0.06)
    a = pole + Y * 2.6 + R * 0.05; b = pole + Y * 2.32 + R * 0.05
    plate = np.array([a - F * 0.0 + R * 0.0 + F * 0.45, a + F * -0.45, b + F * -0.45, b + F * 0.45], F32)
    cv.poly(plate, hexc('1d5a3a') * _lit(S, R) * 4 + hexc('1d5a3a') * 0.01, ztest=True)
    cv.sign_quad = plate

# ---------------------------------------------------------------- server racks
@lru_cache(1)
def rack_layout():
    r = np.random.default_rng(55)
    spots = []
    # first two in the middle of the lawn, then a row, then the lawn fills
    pref = [(1.2, 9.5, 0.05), (-1.8, 11.2, -0.2)]
    for (rr, ff, yaw) in pref: spots.append((rr, ff, yaw, r.random()))
    for k in range(6): spots.append((-6 + k * 2.4 + r.normal(0, 0.3), 13.5 + r.normal(0, 0.4), r.normal(0, 0.12), r.random()))
    for i in range(5):
        for j in range(5):
            spots.append((-7.5 + i * 3.6 + r.normal(0, 0.4), 7.5 + j * 2.2 + r.normal(0, 0.3), r.normal(0, 0.25), r.random()))
    return spots

def draw_racks(cv, S, t, n):
    cam = cv.cam
    spots = rack_layout()[:n]
    order = sorted(spots, key=lambda s_: -np.linalg.norm(P(s_[0], 1.0, HD + s_[1]) - cam.eye))
    red = float(S.get('rack_red', 0.0))
    for (rr, ff, yaw, rnd) in order:
        tipped = rnd > 0.86 and n > 8
        c = P(rr, 0, HD + ff)
        cy, sy = math.cos(yaw), math.sin(yaw)
        ax = R * cy + F * sy; az = -R * sy + F * cy                      # rack local axes (front faces -az: toward the house)
        w, d, h = 0.6, 1.0, 2.0
        if tipped: h, d = 1.0, 2.0
        def L(x, yv, z): return c + ax * x + Y * yv + az * z
        boxf = {
            'front': ([L(-w / 2, h, -d / 2), L(w / 2, h, -d / 2), L(w / 2, 0, -d / 2), L(-w / 2, 0, -d / 2)], -az),
            'back': ([L(w / 2, h, d / 2), L(-w / 2, h, d / 2), L(-w / 2, 0, d / 2), L(w / 2, 0, d / 2)], az),
            'left': ([L(-w / 2, h, d / 2), L(-w / 2, h, -d / 2), L(-w / 2, 0, -d / 2), L(-w / 2, 0, d / 2)], -ax),
            'right': ([L(w / 2, h, -d / 2), L(w / 2, h, d / 2), L(w / 2, 0, d / 2), L(w / 2, 0, -d / 2)], ax),
            'top': ([L(-w / 2, h, d / 2), L(w / 2, h, d / 2), L(w / 2, h, -d / 2), L(-w / 2, h, -d / 2)], Y),
        }
        for nm, (pts, nn) in boxf.items():
            Pq = np.array(pts, F32)
            if np.dot(nn, Pq.mean(0) - cam.eye) >= 0: continue
            base = hexc('121316') * (_lit(S, nn) * 3.5 + 0.0008)
            if nm in ('front', 'back') and not tipped:
                cv.poly(Pq, rack_face(cam, S, t, c, ax, az, w, h, d, nm, rnd, red), ztest=True,
                        emis=rack_leds(cam, S, t, c, ax, az, w, h, d, nm, rnd, red))
            else:
                cv.poly(Pq, base, ztest=True)

def rack_face(cam, S, t, c, ax, az, w, h, d, nm, rnd, red):
    def f(X, Y_, Z, m):
        Pw = WD._world_from_screen(cam, X, Y_, Z)
        q = Pw - c; u = q @ ax; v = q[..., 1]
        mesh = 0.75 + 0.25 * (np.sin(u * 900) * np.sin(v * 900) > 0)
        units = 1 - 0.35 * np.exp(-(((v % 0.0889) / 0.0889 - 0.5) / 0.08) ** 2 * 0)
        frame = (np.abs(u) > w / 2 - 0.04) | (v > h - 0.05) | (v < 0.08)
        alb = np.where(frame, 0.05, 0.03 * mesh * units)
        return (alb[..., None] * (WD.ambient_light(S) * 4 + hexc('b8cad8') * 0.01)).astype(F32)
    return f

def rack_leds(cam, S, t, c, ax, az, w, h, d, nm, rnd, red):
    def f(X, Y_, Z, m):
        Pw = WD._world_from_screen(cam, X, Y_, Z)
        q = Pw - c; u = q @ ax; v = q[..., 1]
        slot = np.floor(v / 0.0889).astype(np.int32)
        col_i = np.floor((u + w / 2) / 0.06).astype(np.int32)
        hsh = np.abs(np.modf(np.sin(slot * 12.9898 + col_i * 78.233 + rnd * 91.7) * 43758.5453)[0])
        rate = 0.5 + 4.0 * hsh
        blink = (np.sin(t * rate * 6.283 + hsh * 40) > 0.2 - 0.6 * hsh).astype(F32)
        dotu = ((u + w / 2) % 0.06) / 0.06 - 0.5; dotv = ((v % 0.0889) / 0.0889) - 0.5
        dot = np.exp(-(dotu ** 2 + dotv ** 2) / 0.012)
        on = (col_i >= 6) & (col_i <= 8) & (v > 0.15) & (v < h - 0.15)
        cg = np.where((hsh > 0.82)[..., None], hexc('ffb030')[None, None], np.where((hsh > 0.35)[..., None], hexc('3cff9a')[None, None], hexc('59b8ff')[None, None]))
        if red > 0: cg = cg * (1 - red) + hexc('ff2236')[None, None] * red
        e = cg * (dot * blink * on * 1.6)[..., None]
        return e.astype(F32)
    return f
