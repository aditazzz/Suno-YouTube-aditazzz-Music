"""Interiors: her bedroom (upstairs, the window faces the facility across the river) and the council chamber.

The bedroom is built in the valley's own coordinates, inside her house, so the view through the window is the
real valley rendered with the same camera. Venetian blinds: slats drawn in perspective over that view, and their
shadow pattern traced per pixel (each surface point looks back toward the window along the light direction and asks
whether it passes between two slats), which gives the noir stripes on the bed, the walls and her.
"""
import math
from functools import lru_cache
import numpy as np, cv2
import ys_eng as E
from ys_eng import F32, hexc, nrm, sample, fbm_tex
import ys_world as WD
import ys_her as HER

# ---------------------------------------------------------------- the bedroom frame (local u right, v up, w toward the window)
_fc = np.array([(WD.MONO_A['x0'] + WD.MONO_A['x1']) / 2, 0, (WD.MONO_A['z0'] + WD.MONO_A['z1']) / 2], F32)
FWD = nrm((_fc - WD.HOUSE) * np.array([1, 0, 1], F32))
RIGHT = np.array([FWD[2], 0, -FWD[0]], F32)
UP = np.array([0, 1, 0], F32)
ORIGIN = WD.HOUSE + np.array([0, 3.1, 0], F32) + FWD * 4.6          # centre of the window wall at floor level
ROOM = dict(u0=-2.2, u1=2.2, h=2.6, w0=-3.8)
WIN = dict(u0=-0.95, u1=0.95, v0=0.78, v1=2.12)
SLATS = 30

def L2W(u, v, w):
    return ORIGIN + RIGHT * u + UP * v + FWD * w

def W2L(P):
    Q = P - ORIGIN
    return Q @ RIGHT, Q @ UP, Q @ FWD

def bedroom_cam(W, H, k=0.0, u=0.85, v=1.2, w=-3.3, tu=-0.1, tv=1.38, fov=44.0, push=0.0, t=0.0):
    eye = L2W(u - 0.25 * push, v, w + 0.9 * push); tgt = L2W(tu, tv, 0.0)
    return E.Cam(eye, tgt, fov=fov, W=W, H=H, drift=0.004, t=t, seed=5)

def _stripes_local(u, v, w, S):
    """window light reaching local point (u, v, w): 0..1 through the opening and between the slats."""
    Ld = S['win_dir']                         # local direction toward the light (lu, lv, lw), lw > 0
    s = np.maximum(0, -w) / max(1e-4, Ld[2])
    hu = u + s * Ld[0]; hv = v + s * Ld[1]
    soft = 0.004 + 0.006 * np.maximum(0, -w)   # penumbra widens with distance from the window (a floodlight: small source)
    inwin = E.ss_arr(WIN['u0'] - soft, WIN['u0'] + soft, hu) * (1 - E.ss_arr(WIN['u1'] - soft, WIN['u1'] + soft, hu)) \
        * E.ss_arr(WIN['v0'] - soft, WIN['v0'] + soft, hv) * (1 - E.ss_arr(WIN['v1'] - soft, WIN['v1'] + soft, hv))
    sp = (WIN['v1'] - WIN['v0']) / SLATS
    ph = ((hv - WIN['v0']) / sp) % 1.0
    open_ = float(S.get('blind_open', 0.55))
    sw = soft / sp
    gap = E.ss_arr(1 - open_ - 0.04 - sw, 1 - open_ + 0.04 + sw, ph) * (1 - E.ss_arr(0.97 - sw * 0.5, 1.0, ph))
    up = float(S.get('blind_up', 0.0))      # blinds raised: the top part of the window is open
    gap = np.maximum(gap, E.ss_arr(WIN['v1'] - up - 0.02, WIN['v1'] - up + 0.02, hv) * 0)
    return inwin * gap

LAMP = dict(u=1.55, v=0.92, w=-0.35)          # centre of the shade (nightstand right of the window)
LAMP_COL = hexc('ffb46a')
WIN_COL = hexc('b9d4e6')

def _shade_fn(cam, S, alb, n_local, rough=0.0, tex=None):
    nL = np.asarray(n_local, F32)
    lamp = float(S.get('lamp', 1.0)); win = float(S.get('window_light', 1.0))
    def f(X, Y, Z, m):
        P = WD._world_from_screen(cam, X, Y, Z)
        Q = P - ORIGIN
        u = Q @ RIGHT; v = Q @ UP; w = Q @ FWD
        col = np.zeros(X.shape + (3,), F32)
        a = np.asarray(alb, F32)
        if tex is not None: a = a[None, None] * tex(u, v, w)[..., None]
        # lamp: a drum shade throws a cone up and a cone down, and glows a little sideways
        if lamp > 0.001:
            du, dv, dw = LAMP['u'] - u, LAMP['v'] - v, LAMP['w'] - w
            d2 = du * du + dv * dv + dw * dw + 0.02; d = np.sqrt(d2)
            ndl = np.clip((du * nL[0] + dv * nL[1] + dw * nL[2]) / d, 0, 1)
            cone = 0.45 + 0.55 * E.ss_arr(0.45, 0.8, np.abs(dv) / d)
            col += LAMP_COL * (lamp * 3.2 * ndl * cone / d2)[..., None]
            col += LAMP_COL * (lamp * 0.045)        # bounce
        if win > 0.001:
            st = _stripes_local(u, v, w, S)
            Ld = S['win_dir']
            ndl = np.clip(nL[0] * Ld[0] + nL[1] * Ld[1] + nL[2] * Ld[2], 0, 1)
            col += WIN_COL * (win * 2.4 * st * ndl * (0.6 + 0.4 * float(S.get('breath', 0.5))))[..., None]
            col += WIN_COL * (win * 0.02)           # the glow of the window filling the room
        col += hexc('0c1422') * 0.012
        return a * col
    return f

def _wall_tex(u, v, w):
    n = sample(fbm_tex(256, 1.3, 71), u * 40 + w * 40, v * 40, 1.0)
    return 0.85 + 0.3 * n

def draw_bedroom(W, H, S, t, cam=None, her=True, exterior_scale=0.5, valley_S=None):
    """the room; S: lamp (0..1), window_light, blind_open, breath, plus the valley state in valley_S."""
    cam = cam or bedroom_cam(W, H, t=t)
    lu = nrm(S.get('light_dir_local', [0.55, 0.30, 1.0]))
    S = dict(S); S['win_dir'] = lu
    # 1. the valley through the window (same camera, smaller, a little soft: the focus is in the room)
    VS = dict(WD.default_state()); VS.update(valley_S or {})
    ext_cam = E.lowres_cam(cam, 1 / exterior_scale) if exterior_scale < 1 else cam
    vcv = WD.render(ext_cam, VS, t, reflections=True, refl_scale=0.5)
    ext = WD.compose(vcv)
    if exterior_scale < 1: ext = cv2.resize(ext, (cam.W, cam.H), interpolation=cv2.INTER_LINEAR)
    ext = cv2.GaussianBlur(ext, (0, 0), 1.2 * E.pxs(cam.W, cam.H)) * float(S.get('ext_gain', 5.0))
    cv = E.Canvas(cam)
    cv.img[:] = ext
    cv.dep[:] = 1e5
    def Q(*pts): return np.array([L2W(*p) for p in pts], F32)
    R = ROOM; Wn = WIN
    wall = hexc('5a5550'); ceil_ = hexc('4a4744'); floor_ = hexc('2a211b')
    # window wall around the opening (w = 0), normal -w (into the room)
    for quad in ([(R['u0'], R['h'], 0), (Wn['u0'], R['h'], 0), (Wn['u0'], 0, 0), (R['u0'], 0, 0)],
                 [(Wn['u1'], R['h'], 0), (R['u1'], R['h'], 0), (R['u1'], 0, 0), (Wn['u1'], 0, 0)],
                 [(Wn['u0'], Wn['v0'], 0), (Wn['u1'], Wn['v0'], 0), (Wn['u1'], 0, 0), (Wn['u0'], 0, 0)],
                 [(Wn['u0'], R['h'], 0), (Wn['u1'], R['h'], 0), (Wn['u1'], Wn['v1'], 0), (Wn['u0'], Wn['v1'], 0)]):
        cv.poly(Q(*quad), _shade_fn(cam, S, wall, (0, 0, -1), tex=_wall_tex), ztest=False)
    # side walls, floor, ceiling
    cv.poly(Q((R['u0'], R['h'], R['w0']), (R['u0'], R['h'], 0), (R['u0'], 0, 0), (R['u0'], 0, R['w0'])), _shade_fn(cam, S, wall * 0.9, (1, 0, 0), tex=_wall_tex))
    cv.poly(Q((R['u1'], R['h'], 0), (R['u1'], R['h'], R['w0']), (R['u1'], 0, R['w0']), (R['u1'], 0, 0)), _shade_fn(cam, S, wall * 0.9, (-1, 0, 0), tex=_wall_tex))
    cv.poly(Q((R['u0'], 0, 0), (R['u1'], 0, 0), (R['u1'], 0, R['w0']), (R['u0'], 0, R['w0'])), _shade_fn(cam, S, floor_, (0, 1, 0)))
    cv.poly(Q((R['u0'], R['h'], R['w0']), (R['u1'], R['h'], R['w0']), (R['u1'], R['h'], 0), (R['u0'], R['h'], 0)), _shade_fn(cam, S, ceil_, (0, -1, 0)))
    # window casing + sill
    trim = hexc('3d3935')
    c = 0.07
    for quad, n in (([(Wn['u0'] - c, Wn['v1'] + c, -0.02), (Wn['u1'] + c, Wn['v1'] + c, -0.02), (Wn['u1'] + c, Wn['v1'], -0.02), (Wn['u0'] - c, Wn['v1'], -0.02)], (0, 0, -1)),
                    ([(Wn['u0'] - c, Wn['v1'], -0.02), (Wn['u0'], Wn['v1'], -0.02), (Wn['u0'], Wn['v0'], -0.02), (Wn['u0'] - c, Wn['v0'], -0.02)], (0, 0, -1)),
                    ([(Wn['u1'], Wn['v1'], -0.02), (Wn['u1'] + c, Wn['v1'], -0.02), (Wn['u1'] + c, Wn['v0'], -0.02), (Wn['u1'], Wn['v0'], -0.02)], (0, 0, -1)),
                    ([(Wn['u0'] - c - 0.03, Wn['v0'], -0.16), (Wn['u1'] + c + 0.03, Wn['v0'], -0.16), (Wn['u1'] + c + 0.03, Wn['v0'], 0), (Wn['u0'] - c - 0.03, Wn['v0'], 0)], (0, 1, 0)),
                    ([(Wn['u0'] - c - 0.03, Wn['v0'], -0.16), (Wn['u1'] + c + 0.03, Wn['v0'], -0.16), (Wn['u1'] + c + 0.03, Wn['v0'] - 0.05, -0.16), (Wn['u0'] - c - 0.03, Wn['v0'] - 0.05, -0.16)], (0, 0, -1))):
        cv.poly(Q(*quad), _shade_fn(cam, S, trim, n))
    # blinds: slats across the opening, tilted; their edges catch the window light
    sp = (Wn['v1'] - Wn['v0']) / SLATS; op_ = float(S.get('blind_open', 0.55))
    tilt = (1 - op_) * 1.25
    for k in range(SLATS):
        vc = Wn['v0'] + (k + 0.5) * sp
        dv = math.cos(tilt) * sp * 0.48 * 0 + math.sin(tilt) * sp * 0.5; dw = math.cos(tilt) * sp * 0.5
        quad = [(Wn['u0'], vc + dv, -0.06 - dw), (Wn['u1'], vc + dv, -0.06 - dw), (Wn['u1'], vc - dv, -0.06 + dw), (Wn['u0'], vc - dv, -0.06 + dw)]
        lit = 0.03 * float(S.get('lamp', 1.0)) * LAMP_COL + WIN_COL * 0.012 * float(S.get('window_light', 1.0))
        cv.poly(Q(*quad), hexc('8c8378') * 0.4 * lit * 40 * 0.05 + hexc('151515') * 0.004)
        # the lit edge of each slat
        cv.line3(L2W(Wn['u0'], vc - dv, -0.06 + dw), L2W(Wn['u1'], vc - dv, -0.06 + dw), WIN_COL * 0.05 * float(S.get('window_light', 1.0)) * (0.5 + 0.5 * float(S.get('breath', 0.5))), width_m=0.003, min_px=0.8, op=0.8)
    # cords
    for uu in (Wn['u0'] + 0.25, Wn['u1'] - 0.25):
        cv.line3(L2W(uu, Wn['v1'], -0.075), L2W(uu, Wn['v0'] + 0.02, -0.075), hexc('1a1816') * 0.02, width_m=0.004, min_px=0.6)
    # curtains: two heavy panels with folds
    def curtain(u0, u1):
        def f(X, Y, Z, m):
            P = WD._world_from_screen(cam, X, Y, Z); u = (P - ORIGIN) @ RIGHT
            fold = 0.55 + 0.45 * np.cos((u - u0) / 0.09 * math.pi) ** 2
            base = _shade_fn(cam, S, hexc('3a2f2b'), (0, 0, -1))(X, Y, Z, m)
            return base * fold[..., None] * 0.9
        cv.poly(Q((u0, R['h'] - 0.08, -0.12), (u1, R['h'] - 0.08, -0.12), (u1, 0.05, -0.12), (u0, 0.05, -0.12)), f)
    curtain(Wn['u0'] - 0.62, Wn['u0'] - 0.04); curtain(Wn['u1'] + 0.04, Wn['u1'] + 0.62)
    # nightstand + lamp + the glass of water (right of the window)
    ns = dict(u0=1.18, u1=1.92, w0=-0.62, w1=-0.08, h=0.58)
    wood = hexc('2c2119')
    for quad, n in (([(ns['u0'], ns['h'], ns['w0']), (ns['u1'], ns['h'], ns['w0']), (ns['u1'], 0, ns['w0']), (ns['u0'], 0, ns['w0'])], (0, 0, -1)),
                    ([(ns['u0'], ns['h'], ns['w1']), (ns['u0'], ns['h'], ns['w0']), (ns['u0'], 0, ns['w0']), (ns['u0'], 0, ns['w1'])], (-1, 0, 0)),
                    ([(ns['u0'], ns['h'], ns['w1']), (ns['u1'], ns['h'], ns['w1']), (ns['u1'], ns['h'], ns['w0']), (ns['u0'], ns['h'], ns['w0'])], (0, 1, 0))):
        cv.poly(Q(*quad), _shade_fn(cam, S, wood, n))
    lamp = float(S.get('lamp', 1.0))
    # lamp base (a narrow column) and shade (a drum: drawn as its silhouette quad + glow)
    cv.poly(Q((LAMP['u'] - 0.05, ns['h'] + 0.22, LAMP['w']), (LAMP['u'] + 0.05, ns['h'] + 0.22, LAMP['w']), (LAMP['u'] + 0.07, ns['h'], LAMP['w']), (LAMP['u'] - 0.07, ns['h'], LAMP['w'])),
            _shade_fn(cam, S, hexc('6a5a48'), (0, 0, -1)))
    r_sh = 0.19; sh0, sh1 = ns['h'] + 0.2, ns['h'] + 0.47
    sh_col = hexc('e8cfa6') * (0.012 + 0.75 * lamp) + hexc('20242a') * 0.006
    cv.poly(Q((LAMP['u'] - r_sh * 0.82, sh1, LAMP['w']), (LAMP['u'] + r_sh * 0.82, sh1, LAMP['w']), (LAMP['u'] + r_sh, sh0, LAMP['w']), (LAMP['u'] - r_sh, sh0, LAMP['w'])),
            sh_col, emis=hexc('ffc27e') * 0.9 * lamp)
    # glass of water (a small cylinder silhouette with a bright rim)
    gu, gw = 1.36, -0.40
    gl = [(gu - 0.035, ns['h'] + 0.13, gw), (gu + 0.035, ns['h'] + 0.13, gw), (gu + 0.031, ns['h'], gw), (gu - 0.031, ns['h'], gw)]
    wl = float(S.get('glass_level', 0.8))
    cv.poly(Q(*gl), hexc('1a2028') * 0.02 + LAMP_COL * 0.06 * lamp, op=0.7)
    wq = [(gu - 0.033, ns['h'] + 0.01 + 0.11 * wl, gw), (gu + 0.033, ns['h'] + 0.01 + 0.11 * wl, gw), (gu + 0.031, ns['h'] + 0.01, gw), (gu - 0.031, ns['h'] + 0.01, gw)]
    cv.poly(Q(*wq), hexc('2a3a48') * 0.04 + LAMP_COL * 0.05 * lamp + WIN_COL * 0.02, op=0.8, emis=WIN_COL * 0.03 * float(S.get('window_light', 1.0)))
    # bed along the left wall (we see its foot end and the duvet)
    bed = dict(u0=-2.2, u1=0.45, w0=-3.8, w1=-1.05, h=0.56)
    linen = hexc('8f877c')
    def duvet(X, Y, Z, m):
        P = WD._world_from_screen(cam, X, Y, Z); u = (P - ORIGIN) @ RIGHT; w = (P - ORIGIN) @ FWD
        wr = 0.82 + 0.18 * np.sin(u * 7 + np.sin(w * 3) * 2) * np.sin(w * 5.5)
        return _shade_fn(cam, S, linen, (0, 1, 0))(X, Y, Z, m) * wr[..., None]
    cv.poly(Q((bed['u0'], bed['h'], bed['w1']), (bed['u1'], bed['h'], bed['w1']), (bed['u1'], bed['h'], bed['w0']), (bed['u0'], bed['h'], bed['w0'])), duvet)
    cv.poly(Q((bed['u1'], bed['h'], bed['w1']), (bed['u1'], bed['h'], bed['w0']), (bed['u1'], 0.1, bed['w0']), (bed['u1'], 0.1, bed['w1'])), _shade_fn(cam, S, linen * 0.8, (1, 0, 0)))
    cv.poly(Q((bed['u0'], bed['h'], bed['w1']), (bed['u1'], bed['h'], bed['w1']), (bed['u1'], 0.1, bed['w1']), (bed['u0'], 0.1, bed['w1'])), _shade_fn(cam, S, linen * 0.75, (0, 0, 1)))
    # her, sitting on the bed's corner nearest the window, facing it
    if her:
        hp = L2W(0.08, bed['h'] + 0.98, -1.3)
        x, y, z = cam.project(hp[None])
        hh = 0.235 * cam.fpx / max(0.3, z[0])
        wx, wy, _ = cam.project(L2W(0.0, 1.45, 0.0)[None])
        ld = np.array([wx[0] - x[0], wy[0] - y[0]], F32)
        rimc = WIN_COL * (0.10 + 0.08 * float(S.get('breath', 0.5))) * float(S.get('window_light', 1.0)) + LAMP_COL * 0.06 * lamp
        HER.draw(cv.img, 'sit_back', float(x[0]), float(y[0]), hh, light_dir=ld, rim=rimc * 4.0, rim_amt=1.0, backlit=0.8,
                 body=hexc('07080a') * 0.3 + LAMP_COL * 0.004 * lamp, t=t, emis=cv.emis, wind=0.15, seed=11)
    return cv

# ---------------------------------------------------------------- council chamber
def draw_hall(W, H, S, t):
    """static, symmetrical: seen from the dais. The lectern with its gooseneck microphone in the centre aisle faces
    us, empty; rows of empty folding chairs behind it; the back wall with the doors and the clock; fluorescent panels
    converging; the flag in the corner."""
    cam = E.Cam((0, 1.40, 4.7), (0, 1.22, -8.0), fov=38, W=W, H=H)
    cv = E.Canvas(cam)
    flick = float(S.get('flicker', 0.0))
    def Q(*p): return np.array(p, F32)
    room = dict(x=6.4, h=3.2, z0=-11.0, z1=8.0)
    zb = room['z0']
    def lit_fn(alb, n, tex=None):
        nL = np.asarray(n, F32)
        def f(X, Y, Z, m):
            P = WD._world_from_screen(cam, X, Y, Z)
            col = np.zeros(X.shape + (3,), F32)
            for (px, pz) in PANELS:
                wgt = PANEL_ON.get((px, pz), 0.0)
                if wgt <= 0: continue
                d = np.stack([px - P[..., 0], room['h'] - 0.02 - P[..., 1], pz - P[..., 2]], -1)
                d2 = (d * d).sum(-1) + 0.5; dd = np.sqrt(d2)
                ndl = np.clip((d * nL).sum(-1) / dd, 0, 1)
                col += FLUO * (2.2 * wgt * ndl / d2)[..., None] * (1 - 0.12 * flick)
            col += FLUO * 0.012 + hexc('ff2a2a') * 0.0015 * np.exp(-np.maximum(0, P[..., 2] - zb) / 2.0)[..., None]
            a = np.asarray(alb, F32)
            if tex is not None: a = a[None, None] * tex(P)[..., None]
            return a * col
        return f
    def grain_tex(P):
        return 0.86 + 0.14 * sample(fbm_tex(256, 1.6, 81), P[..., 0] * 20 + P[..., 2] * 20, P[..., 1] * 60, 1.0)
    def panel_tex(P):
        x = np.where(np.abs(P[..., 0]) > room['x'] - 0.05, P[..., 2], P[..., 0])
        grooves = 1 - 0.25 * np.exp(-((x % 0.6) / 0.012) ** 2)
        return grooves * grain_tex(P)
    def ceiling_tex(P):
        gx = np.exp(-(((P[..., 0] + 0.3) % 0.6) / 0.01) ** 2); gz = np.exp(-(((P[..., 2]) % 0.6) / 0.01) ** 2)
        return 1 - 0.3 * np.maximum(gx, gz)
    def carpet_tex(P):
        return 0.8 + 0.2 * sample(fbm_tex(256, 1.0, 82), P[..., 0] * 80, P[..., 2] * 80, 1.0)
    wood = hexc('6b5038'); wall = hexc('a8a497'); carpet = hexc('4a5258')
    # back wall with the doors
    zb = room['z0']
    cv.poly(Q((-room['x'], room['h'], zb), (room['x'], room['h'], zb), (room['x'], 0, zb), (-room['x'], 0, zb)), lit_fn(wall, (0, 0, 1), grain_tex))
    cv.poly(Q((-room['x'], 1.1, zb + 0.01), (room['x'], 1.1, zb + 0.01), (room['x'], 0, zb + 0.01), (-room['x'], 0, zb + 0.01)), lit_fn(wood, (0, 0, 1), panel_tex))
    for dx in (-2.6, 2.6):          # a door each side; the wall behind the microphone stays plain (it reads against it)
        cv.poly(Q((dx - 0.55, 2.2, zb + 0.02), (dx + 0.55, 2.2, zb + 0.02), (dx + 0.55, 0, zb + 0.02), (dx - 0.55, 0, zb + 0.02)), lit_fn(hexc('4a3a2c'), (0, 0, 1), grain_tex))
        cv.poly(Q((dx - 0.15, 1.9, zb + 0.03), (dx + 0.15, 1.9, zb + 0.03), (dx + 0.15, 1.2, zb + 0.03), (dx - 0.15, 1.2, zb + 0.03)), hexc('0c0e10') * 0.3)
        cv.poly(Q((dx - 0.2, 2.5, zb + 0.02), (dx + 0.2, 2.5, zb + 0.02), (dx + 0.2, 2.36, zb + 0.02), (dx - 0.2, 2.36, zb + 0.02)), hexc('300a0c'), emis=hexc('ff2a2a') * 0.45)   # EXIT
    cv.exit_xy = cam.project(Q((2.6, 2.43, zb + 0.03)))[:2]
    for sx in (-1, 1):
        x = sx * room['x']
        cv.poly(Q((x, room['h'], zb), (x, room['h'], room['z1']), (x, 0, room['z1']), (x, 0, zb)), lit_fn(wall * 0.95, (-sx, 0, 0), grain_tex))
        cv.poly(Q((x - sx * 0.01, 1.1, zb), (x - sx * 0.01, 1.1, room['z1']), (x - sx * 0.01, 0, room['z1']), (x - sx * 0.01, 0, zb)), lit_fn(wood, (-sx, 0, 0), panel_tex))
    cv.poly(Q((-room['x'], 0, room['z1']), (room['x'], 0, room['z1']), (room['x'], 0, zb), (-room['x'], 0, zb)), lit_fn(carpet, (0, 1, 0), carpet_tex))
    cv.poly(Q((-room['x'], room['h'], zb), (room['x'], room['h'], zb), (room['x'], room['h'], room['z1']), (-room['x'], room['h'], room['z1'])), lit_fn(hexc('cfccc2'), (0, -1, 0), ceiling_tex))
    for (px, pz) in PANELS:
        wgt = PANEL_ON.get((px, pz), 0.0)
        cv.poly(Q((px - 0.6, room['h'] - 0.01, pz + 0.3), (px + 0.6, room['h'] - 0.01, pz + 0.3), (px + 0.6, room['h'] - 0.01, pz - 0.3), (px - 0.6, room['h'] - 0.01, pz - 0.3)),
                FLUO * (0.9 * wgt + 0.02), emis=FLUO * 2.2 * wgt * (1 - 0.2 * flick))
    # the clock above the doors
    cxk, cyk, czk = cam.project(Q((0.0, 2.85, zb + 0.03)))
    r = 0.27 * cam.fpx / max(1, czk[0])
    cv2.circle(cv.img, (int(cxk[0]), int(cyk[0])), int(r), (hexc('e8e6de') * 0.55).tolist(), -1, cv2.LINE_AA)
    cv2.circle(cv.img, (int(cxk[0]), int(cyk[0])), int(r), (hexc('1a1a1a') * 0.05).tolist(), max(1, int(r * 0.12)), cv2.LINE_AA)
    tm = float(S.get('clock', 19.7))
    for ang, ln, wd in (((tm % 12) / 12 * 2 * math.pi, 0.52, 0.10), ((tm % 1) * 2 * math.pi, 0.8, 0.07)):
        cv2.line(cv.img, (int(cxk[0]), int(cyk[0])), (int(cxk[0] + math.sin(ang) * r * ln), int(cyk[0] - math.cos(ang) * r * ln)), (hexc('111111') * 0.05).tolist(), max(1, int(r * wd)), cv2.LINE_AA)
    sec = (t % 60) / 60 * 2 * math.pi
    cv2.line(cv.img, (int(cxk[0]), int(cyk[0])), (int(cxk[0] + math.sin(sec) * r * 0.85), int(cyk[0] - math.cos(sec) * r * 0.85)), (hexc('a01818') * 0.5).tolist(), max(1, int(r * 0.03)), cv2.LINE_AA)
    # the flag in the right corner, furled on its pole
    fx, fz = 5.5, zb + 0.6
    cv.line3(np.array([fx, 0, fz], F32), np.array([fx, 2.75, fz], F32), hexc('9a8a5a') * 0.6, width_m=0.03)
    fl = [(fx, 2.68, fz), (fx + 0.06, 2.62, fz), (fx + 0.30, 1.55, fz + 0.1), (fx + 0.1, 1.42, fz + 0.05), (fx - 0.06, 1.8, fz)]
    def flag(X, Y, Z, m):
        P = WD._world_from_screen(cam, X, Y, Z); v = P[..., 1]
        band = (np.floor((v - 1.4) / 0.085) % 2)
        c = hexc('8a1c28') * (1 - band[..., None]) + hexc('d2ccbe') * band[..., None]
        topl = (v > 2.25) & (P[..., 0] < fx + 0.12)
        c = np.where(topl[..., None], hexc('1c2a50'), c)
        return c * 0.32 * (0.65 + 0.35 * np.sin(P[..., 0] * 55 + v * 8))[..., None]
    cv.poly(np.array(fl, F32), flag)
    # rows of empty folding chairs behind the lectern, both sides of the aisle (far rows first)
    for row in range(8, -1, -1):
        z = -9.6 + row * 1.15
        for side in (-1, 1):
            for k in range(6):
                x = side * (1.05 + k * 0.6)
                back = Q((x - 0.21, 0.92, z - 0.24), (x + 0.21, 0.92, z - 0.24), (x + 0.21, 0.58, z - 0.24), (x - 0.21, 0.58, z - 0.24))
                cv.poly(back, lit_fn(hexc('5a616a'), (0, 0, 1)))
                for lx in (x - 0.19, x + 0.19):
                    cv.line3(np.array([lx, 0, z + 0.18], F32), np.array([lx, 0.46, z + 0.18], F32), hexc('2a2e34') * 0.2, width_m=0.02)
                    cv.line3(np.array([lx, 0, z - 0.22], F32), np.array([lx, 0.92, z - 0.24], F32), hexc('2a2e34') * 0.2, width_m=0.02)
                seat = Q((x - 0.21, 0.46, z - 0.2), (x + 0.21, 0.46, z - 0.2), (x + 0.21, 0.46, z + 0.2), (x - 0.21, 0.46, z + 0.2))
                cv.poly(seat, lit_fn(hexc('6a727c'), (0, 1, 0)))
                cv.poly(Q((x - 0.21, 0.46, z + 0.2), (x + 0.21, 0.46, z + 0.2), (x + 0.21, 0.41, z + 0.2), (x - 0.21, 0.41, z + 0.2)), lit_fn(hexc('3a4048'), (0, 0, 1)))
    # the lectern facing us, with its gooseneck microphone
    lz = 1.6
    cv.poly(Q((-0.44, 1.12, lz - 0.40), (0.44, 1.12, lz - 0.40), (0.44, 1.16, lz + 0.02), (-0.44, 1.16, lz + 0.02)), lit_fn(wood * 1.15, (0, 1, 0), grain_tex))
    cv.poly(Q((-0.44, 1.12, lz + 0.02), (0.44, 1.12, lz + 0.02), (0.38, 0, lz + 0.02), (-0.38, 0, lz + 0.02)), lit_fn(wood * 0.95, (0, 0, 1), panel_tex))
    cv.poly(Q((-0.30, 0.95, lz + 0.03), (0.30, 0.95, lz + 0.03), (0.30, 0.62, lz + 0.03), (-0.30, 0.62, lz + 0.03)), lit_fn(hexc('8a7a5a'), (0, 0, 1)))  # a seal plaque
    neck = [np.array([0.0, 1.14, lz - 0.30], F32)]
    for k in range(1, 12):
        u = k / 11
        neck.append(np.array([0.0, 1.14 + 0.36 * math.sin(u * math.pi * 0.5), lz - 0.30 + 0.30 * u ** 1.6], F32))
    for a, b in zip(neck[:-1], neck[1:]):
        cv.line3(a, b + (b - a) * 0.15, hexc('1c1e22') * 0.25, width_m=0.016, min_px=1.5)
    cv.line3(neck[0] + np.array([0.004, 0, 0], F32), neck[-1] + np.array([0.004, 0, 0], F32), FLUO * 0.25, width_m=0.004, min_px=0.8, op=0.7)   # the light along the chrome
    tip = neck[-1]
    # the foam windscreen, pointing at us: a dark ball with the overhead light on its crown
    hx, hy, hz = cam.project(np.array([tip + np.array([0, 0.01, 0.06], F32)], F32))
    rr = 0.03 * cam.fpx / max(0.3, hz[0])
    yy_, xx_ = np.mgrid[0:cv.H, 0:cv.W].astype(F32)
    dd = np.sqrt((xx_ - hx[0]) ** 2 + (yy_ - hy[0]) ** 2) / rr
    ball = np.clip((1.0 - dd) * rr * 0.8, 0, 1)
    crown = np.clip(1 - np.sqrt((xx_ - hx[0]) ** 2 + (yy_ - (hy[0] - rr * 0.55)) ** 2) / (rr * 0.7), 0, 1) ** 2
    foam = hexc('17191c') * 0.03 + FLUO * 0.08 * crown[..., None] * (0.7 + 0.3 * sample(fbm_tex(256, 0.6, 85), xx_ * 0.9, yy_ * 0.9, 1.0))[..., None]
    cv.img = cv.img * (1 - ball[..., None]) + foam * ball[..., None]
    cv.poly(Q((-0.05, 1.13, lz - 0.34), (0.05, 1.13, lz - 0.34), (0.05, 1.15, lz - 0.26), (-0.05, 1.15, lz - 0.26)), hexc('15171a') * 0.4)              # the mic's base
    cv.mic_xy = cam.project(np.array([tip], F32))[:2]
    return cv

FLUO = hexc('dfeaee')
PANEL_ON = {(0.0, 3.0): 0.75, (0.0, 0.0): 0.6, (-3.2, 3.0): 0.15, (3.2, 3.0): 0.15, (0.0, -9.0): 0.9, (-3.2, -9.0): 0.25, (3.2, -9.0): 0.25}
PANELS = [(x, z) for x in (-3.2, 0.0, 3.2) for z in (-9.0, -6.0, -3.0, 0.0, 3.0, 6.0)]
