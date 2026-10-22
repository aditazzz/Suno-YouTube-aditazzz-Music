"""Eleven Kept Going — the first orbital-class booster to come home (21 December 2015, Cape Canaveral, Landing Zone 1).

UP, THEN DOWN. Until the Turn the camera only ever looks up: the floodlit vehicle on the pad, ignition, the climb,
the separation, the ladder of spent stages falling away while the light splits into eleven. On "But this one" the
screen goes black. On "turned around" every shot after it looks down: the booster flipping in the dark, the boostback,
grid fins and cold gas, the long way down to one small light on the coast, the entry burn (the first and only orange),
the landing burn, four legs, touchdown, the smoke. Then the room where somebody did the math, the plan drawn in marker
turning into the two real arcs of light, and dawn.

Palette: black, white, and one orange that appears at the entry burn. Documentary subtitles; mission captions in mono.
No faces, no logos, no company names.
"""
import os, sys, math
from functools import lru_cache
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import ekg as K
from ekg import F32, sstep, clamp, lerp, ease_io, ease_out, ease_in
ROOT = K.ROOT; sys.path.insert(0, ROOT)
from studio import core as C
import coast as CO, pad as PD, ascent as AS, descent as DS, lz as Z, ground as G, orbit as O, room as RM, after as AF

TM = C.Timing(HERE); LN = TM.lines
SONG = TM.duration                     # 309.6
TAIL = 3.0
DUR = SONG + TAIL
T_END = 305.2                          # end screen
T_TOUCH = 196.56
LIFTOFF = 64.6                         # ignition 61.6, T-0 three seconds later

F_SUB = os.path.join(K.FONTS, "Inter-Regular.otf")
F_CAP = os.path.join(K.FONTS, "JBMono-700.ttf")
F_TITLE = os.path.join(K.FONTS, "InterDisplay-ExtraLight.otf")
F_TITLE2 = os.path.join(K.FONTS, "Inter-Medium.otf")
ORANGE = K.hexc("ff7a1e")

def vert(W, H): return H > W
def S(W, H): return min(W, H) / 1080

# ================================================================ shots (each returns a linear HDR frame)
PADAIM = CO.PAD + np.array([0, 40, 0], F32)

def s_cold_open(t, W, H, u):
    """0-17: the long lens across the water. A slow push toward the floodlit vehicle; vapor; heat shimmer."""
    z = lerp(13.0, 21.0, ease_io(u))
    img, cam, hy = CO.render(t, W, H, dict(zoom=z, aim=PADAIM + np.array([0, 4 * u, 0], F32), vapor=1.0, shimmer=0.8, haze=1.0))
    return img

def pad_shot(eye0, eye1, tg0, tg1, fov0, fov1=None, ease=ease_io, **kw):
    def f(t, W, H, u):
        k = ease(u)
        st = dict(eye=K.lerpv(eye0, eye1, k), target=K.lerpv(tg0, tg1, k), fov=lerp(fov0, fov1 or fov0, k), vapor=1.0)
        st.update({kk: (v(t, u) if callable(v) else v) for kk, v in kw.items()})
        img, cam = PD.render(t, W, H, st)
        return img
    return f

# the instrumental intro: one continuous rise up the vehicle, in four cuts on downbeats
s_engines = pad_shot((9.0, 1.1, 13.0), (8.0, 2.4, 11.5), (0, 12, 0), (0, 16, 0), 62, 60)
s_side = pad_shot((-7.5, 6.0, 12.5), (-7.0, 30.0, 11.5), (0, 24, 0), (0, 50, 0), 52, 48)
s_upper = pad_shot((15.0, 47.0, 21.0), (13.5, 61.0, 19.0), (0, 56, 0), (0, 68.5, 0), 40, 38)
s_full = pad_shot((42.0, 2.0, 62.0), (36.0, 2.0, 54.0), (0, 34, 0), (0, 36, 0), 50, 50, ease=lambda x: x)

def s_xray(t, W, H, u):
    """47-56.2 'Eleven small machines / Waiting in the dark': the fairing turns to glass, the eleven satellites inside."""
    k = ease_io(u)
    xr = sstep(47.5, 49.4, t) * (1 - sstep(55.6, 56.24, t))
    st = dict(eye=K.lerpv((15.0, 53.0, 19.0), (10.5, 56.5, 13.0), k), target=K.lerpv((0, 63.0, 0), (0, 64.5, 0), k),
              fov=lerp(40, 34, k), vapor=0.7, xray=xr, spin=0.25 * u)
    img, cam = PD.render(t, W, H, st)
    return img

def s_pullout(t, W, H, u):
    """56.24-61.6 'Built to leave the ground / Never to come back': pull out and down to the whole vehicle."""
    k = ease_io(u)
    st = dict(eye=K.lerpv((12.0, 50.0, 16.0), (56.0, 2.5, 80.0), k), target=K.lerpv((0, 62.0, 0), (0, 34.0, 0), k), fov=lerp(42, 50, k), vapor=1.0)
    img, cam = PD.render(t, W, H, st)
    return img

def s_ignite(t, W, H, u):
    """61.6-65.2 'Nine engines came alive': low under the engines, the ripple of nine flames, steam; then everything white."""
    ft = t - 61.6
    st = dict(eye=(15.0, 1.4, 21.0), target=(0, 9.0 + 2 * u, 0), fov=58, vapor=0.6, ignite=sstep(0.0, 0.6, ft), flame_t=ft,
              whiteout=sstep(64.55, 65.25, t) ** 1.5, lift=max(0.0, t - LIFTOFF) ** 2 * 1.2)
    img, cam = PD.render(t, W, H, st)
    return img

def s_liftoff_tele(t, W, H, u):
    """65.2-67.76 'The whole night turned white': from white, the long lens again, the vehicle rising off the pad."""
    lt = t - LIFTOFF
    img, cam, hy = CO.render(t, W, H, dict(zoom=lerp(6.5, 5.0, u), aim=PADAIM + np.array([0, 40 + 40 * u, 0], F32), launch_t=lt, shimmer=0.6, vapor=0.0))
    wo = 1 - sstep(65.2, 66.1, t)
    return img * (1 - wo) + K.FLAME_HOT * 6.0 * wo

def s_climb(t, W, H, u):
    """67.76-74.92 'For a few seconds / Darkness lost the sky': the whole coast lit by it, the climb (time compressed)."""
    lt = 3.2 + (t - 67.76) * 3.6
    img, cam, hy = CO.render(t, W, H, dict(zoom=lerp(1.2, 0.95, ease_io(u)), launch_t=lt, aim=(-200.0, 900.0 * u, -7000.0)))
    return img

def s_sep(t, W, H, u):
    """74.92-83.2 'Then the first stage falls away / While the second carries on' (looking up the climb)."""
    img, cam = AS.render_sep(t, W, H, dict(u=u, meco=0.17, sep=0.30, mvac=0.62))
    return img

def s_ladder(t, W, H, u):
    """83.2-115.1: the ladder of spent stages; 'You left the ladder behind'; at 114.0 the light splits into eleven."""
    lad = sstep(83.2, 90.0, t)
    fall = sstep(109.84, 113.6, t)
    ghosts = sstep(86.4, 88.5, t) * (1 - sstep(112.0, 114.0, t))
    split = sstep(114.0, 114.8, t)
    img, cam = AS.render_ladder(t, W, H, dict(u=(t - 83.2) / 31.9, ladder=lad, fall=fall, ghosts=ghosts, split=split))
    fade = sstep(114.9, 115.12, t)
    return img * (1 - fade)

def s_leaving(t, W, H, u):
    """96.64-106.64 'To send something higher / Than we've ever gone / That was the bargain': from the spent stage,
    watching the second stage go."""
    img, cam = AS.render_leaving(t, W, H, dict(u=u))
    return img

def s_ladder2(t, W, H, u):
    return s_ladder(t, W, H, u)

def s_black(t, W, H, u):
    """115.1-117.65: black. 'But this one' — a breath of cold gas in the dark."""
    img = np.zeros((H, W, 3), F32)
    if t > 116.55:
        cam = K.Cam((0, 0, 60), (0, 0, 0), W, H, fov=40)
        a = t - 116.55
        for i in range(6):
            age = a - i * 0.06
            if age < 0: continue
            K.smoke_sprite(img, W * 0.56 + age * 120 * S(W, H), H * 0.46 - age * 30 * S(W, H), (30 + age * 140) * S(W, H),
                           0.35 * math.exp(-age * 1.2), np.array([0.05, 0.06, 0.08], F32), i + 40, rot=i * 60)
    return img

def s_flip(t, W, H, u):
    """117.65-118.58 'turned around': now looking DOWN. The booster turning end over end above the dark Earth."""
    img, cam = DS.flip(t, W, H, u, dict(puff_t=117.7))
    return img

def s_boostback_wide(t, W, H, u):
    """118.58-125.6: the band crashes in; three engines light, pushing it back toward the coast."""
    img, cam = DS.boostback(t, W, H, u * 0.5, {})
    return img

def s_boostback_close(t, W, H, u):
    img, cam = DS.boostback(t, W, H, 0.5 + u * 0.5, dict(close=1))
    return img

def s_fins(t, W, H, u):
    """133-139.6 'Grid fins catch the air / Cold gas turns it slow'."""
    img, cam = DS.fins_close(t, W, H, u, dict(fin_u=(t - 133.0) / 2.6, puffs=[136.1, 137.0, 137.9, 138.9]))
    return img

def s_longway(t, W, H, u):
    """139.6-149.04 'A long way down / A long way left to go / And it is not drifting'."""
    img, cam = DS.long_way(t, W, H, u, {})
    return img

def s_aiming(t, W, H, u):
    """149.04-159.4 'It knows where it is going / It is aiming'."""
    img, cam = DS.aiming(t, W, H, u, dict(line=sstep(149.4, 152.4, t), lock=sstep(152.55, 155.6, t)))
    return img

def s_entry(t, W, H, u):
    """159.4-166.56 'Entry burn / The whole sky turns orange' — the first orange."""
    img, cam = DS.entry(t, W, H, u, dict(sky=sstep(161.6, 164.6, t)))
    return img

def s_falling(t, W, H, u):
    """166.56-173.52 'Falling faster / Than something that size / Should ever fall / Then'."""
    img, cam = DS.falling(t, W, H, u, {})
    return img

def s_landburn(t, W, H, u):
    """173.52-179.2 'Landing burn / One engine'."""
    img, cam = DS.landing_burn(t, W, H, u * 0.8, dict(legs=0.0))
    return img

def s_legs(t, W, H, u):
    """179.2-184.9 'Four legs unfolding / Into the dark'."""
    img, cam = DS.legs_close(t, W, H, u, dict(legs=sstep(179.4, 182.4, t)))
    return img

def s_orbit(t, W, H, u):
    """184.9-190.3 'Eleven kept going': above them, looking down — eleven small machines drifting apart over the night."""
    img, cam = O.render_sats(t, W, H, dict(u=0.25 + 0.7 * u))
    return img

def s_overhead(t, W, H, u):
    """190.3-196.56 'One came home': from above, the last hundred metres onto the lit circle."""
    k = (t - 190.3) / (T_TOUCH - 190.3)
    y = 4.32 + 150.0 * (1 - k) ** 1.6
    img, cam = Z.render(t, W, H, dict(eye=(14, lerp(230, 120, ease_io(k)), 20), target=(0, 0, 0), fov=lerp(46, 52, k), B=(0, y, 0), legs=1.0, burn=1.0,
                                      ts=t - T_TOUCH, soot=0.5, up=(0, 0, -1)))
    return img

def s_touchdown(t, W, H, u):
    """196.56-205: touchdown. The smoke rolls out across the concrete; the engine cuts. A drone's oblique look down, so it
    plainly stands."""
    ts = t - T_TOUCH
    a = math.radians(28.0 + 8.0 * u); d = 112.0 - 12.0 * u; h = 66.0 + 4.0 * u
    if vert(W, H): d -= 6.0; h -= 2.0
    img, cam = Z.render(t, W, H, dict(eye=(math.sin(a) * d, h, math.cos(a) * d), target=(0, 22.0, 0), fov=46 if not vert(W, H) else 30,
                                      B=(0, 4.32, 0), legs=1.0, burn=math.exp(-ts * 6.0) if ts < 0.6 else 0.0, ts=ts, scorch=1))
    return img

def s_arcs(t, W, H, u):
    """205-222.8: the long exposure — the two arcs, seen whole in their reflection (the camera keeps looking down)."""
    up = sstep(0.0, 0.55, u); down = sstep(0.35, 0.95, u)
    img, cam, hy = CO.render_mirror(t, W, H, dict(zoom=0.85 if not vert(W, H) else 0.55, pan=(14.0, 0.0), arcs=(up, down), arc_gain=1.0,
                                                   lz_booster=True, lz_smoke=t - T_TOUCH, floods=0.6), pitch=lerp(-9.0, -11.0, u))
    return img

def s_standing(t, W, H, u):
    img, cam = AF.standing(t, W, H, u, {})
    return img

def s_topdown(t, W, H, u):
    img, cam = AF.topdown(t, W, H, u, dict(para=sstep(239.4, 239.8, t) * (1 - sstep(240.6, 241.1, t)),
                                          ocean=sstep(241.1, 241.5, t) * (1 - sstep(242.3, 242.9, t))))
    return img

def s_foot(t, W, H, u):
    img, cam = AF.foot(t, W, H, u, {})
    return img

def s_alone(t, W, H, u):
    img, cam = AF.alone(t, W, H, u, {})
    return img

def s_desk(t, W, H, u):
    """254-259.28 'Somebody built that / sat in a room / Looked at the numbers / Did the math'."""
    if t < 257.36:
        k = (t - 254.0) / 3.36
        st = dict(cx=lerp(2300, 2100, k), cy=lerp(1200, 1250, k), zoom=lerp(0.92, 1.1, ease_io(k)), ang=lerp(-6, -2, k))
    else:
        k = (t - 257.36) / 1.92
        st = dict(cx=lerp(1560, 1500, k), cy=lerp(1100, 1180, k), zoom=lerp(2.1, 2.6, ease_io(k)), ang=lerp(-10, -7, k))
    return RM.desk_render(t, W, H, u, st)

def _board_state(t):
    notes = dict(turn=sstep(260.72, 261.9, t), burn=sstep(262.72, 263.8, t), fall=sstep(264.48, 265.9, t), light=sstep(267.04, 268.4, t),
                 back=sstep(270.72, 271.9, t))
    draw = lerp(0.0, 0.462, sstep(259.4, 260.9, t)) + 0.098 * sstep(261.9, 262.9, t) + 0.30 * sstep(264.0, 266.2, t) + 0.14 * sstep(266.2, 270.6, t)
    return dict(draw=draw, notes=notes, ground=sstep(259.28, 259.9, t))

def _board_text_xy(key):
    """centre of an annotation's mark + text (board px) so the camera frames both."""
    x, y = RM.annot_xy(key)
    for (cu, text, off, k) in RM.ANNOT:
        if k == key: return x + off[0] * 0.5 + 180, y + off[1] * 0.5 + 40
    return x, y

BOARD_KEYS = [(259.28, RM.BW * 0.46, RM.BH * 0.52, 1.0), (260.3, *_board_text_xy("turn"), 1.55), (262.3, *_board_text_xy("burn"), 1.55),
              (264.1, *_board_text_xy("fall"), 1.4), (266.6, *_board_text_xy("light"), 1.4), (270.3, *_board_text_xy("back"), 1.4),
              (272.0, RM.BW * 0.47, RM.BH * 0.52, 1.0)]

def _board_box_xy(key):
    """centre of the box around an annotation's mark and its whole text (board px): a tall frame is too narrow for the
    wide framing, so it centres on the words."""
    x, y = RM.annot_xy(key)
    for (cu, text, off, k) in RM.ANNOT:
        if k == key:
            tw = ImageFont.truetype(RM.F_MARK, 96).getlength(text)
            x0 = min(x - 45, x + off[0]); x1 = max(x + 70, x + off[0] + tw)
            y0 = min(y - 45, y + off[1]); y1 = max(y + (240 if key == "fall" else 70), y + off[1] + 120)
            return (x0 + x1) / 2, (y0 + y1) / 2
    return x, y

BOARD_KEYS_V = [(259.28, RM.BW * 0.40, RM.BH * 0.55, 1.0), (260.3, *_board_box_xy("turn"), 1.55), (262.3, *_board_box_xy("burn"), 1.55),
                (264.1, *_board_box_xy("fall"), 1.4), (266.6, *_board_box_xy("light"), 1.4), (270.3, *_board_box_xy("back"), 1.4),
                (272.0, RM.BW * 0.47, RM.BH * 0.52, 1.0)]

def board_cam(t, W=1920, H=1080):
    """hold on each annotation while it's written; glide to the next one just before its word. The view never leaves
    the board."""
    keys = BOARD_KEYS_V if H > W else BOARD_KEYS
    cx, cy, z = keys[0][1:]
    for i, (ta, xa, ya, za) in enumerate(keys):
        if t < ta: break
        if i == 0: cx, cy, z = xa, ya, za; continue
        _, xp, yp, zp = keys[i - 1]
        k = ease_io((t - ta) / 0.9)
        cx, cy, z = lerp(xp, xa, k), lerp(yp, ya, k), lerp(zp, za, k)
    sw = RM.BW * 0.92 / z; sh = sw * H / W
    if sh > RM.BH * 0.94: z *= sh / (RM.BH * 0.94); sw = RM.BW * 0.92 / z; sh = sw * H / W
    mx, my = sw * 0.56, sh * 0.56
    cx = min(max(cx, mx), RM.BW - mx); cy = min(max(cy, my), RM.BH - my)
    return dict(cx=cx, cy=cy, zoom=z, ang=-1.2, persp=0.025)

def s_board(t, W, H, u):
    """259.28-273.24 'And said / It will turn here / Burn here / Fall this far / Light again / And come back'."""
    st = _board_state(t)
    st["cam"] = board_cam(t, W, H)
    img, M = RM.board_render(t, W, H, st)
    return img

def s_board_glow(t, W, H, u):
    """273.24-275.3 'And it came back': the drawn flight turns into light ..."""
    st = _board_state(t); st["draw"] = 1.0
    st["glow"] = sstep(273.24, 274.6, t)
    st["cam"] = board_cam(272.5, W, H)
    img, M = RM.board_render(t, W, H, st)
    return img

def s_arcs_return(t, W, H, u):
    """275.3-280.3 ... and becomes the real one: the two arcs over the water."""
    img, cam, hy = CO.render_mirror(t, W, H, dict(zoom=lerp(0.8, 0.88, u) * (1.0 if not vert(W, H) else 0.65), pan=(14.0, 0.0), arcs=(1.0, 1.0),
                                                   arc_gain=1.0, lz_booster=True, lz_smoke=t - T_TOUCH, floods=0.5), pitch=-10.0)
    return img

def s_dawn(t, W, H, u):
    """280.3-293 'One came home': dawn over the water; the booster standing on the far shore; eleven points of light."""
    img, cam, hy = CO.render(t, W, H, dict(zoom=lerp(1.0, 1.25, ease_io(u)), pan=(lerp(4.0, 6.5, u), -1.2), dawn=lerp(0.35, 0.8, u),
                                           lz_booster=True, lz_smoke=t - T_TOUCH, sats=sstep(282.0, 292.0, t), floods=lerp(0.3, 0.1, u)))
    return img

def s_room_dawn(t, W, H, u):
    """293-end: the empty room at dawn. The desk, the cold coffee, the plan."""
    st = dict(cx=lerp(2350, 2250, u), cy=lerp(1250, 1300, u), zoom=lerp(0.86, 0.95, ease_io(u)), ang=lerp(3, 1, u), lamp=0.0, dawn=1.0)
    return RM.desk_render(t, W, H, u, st)

# (t0, t1, fn, exposure)
SHOTS = [
    (0.0, 17.0, s_cold_open, 1.0),
    (17.0, 24.3, s_engines, 1.0),
    (24.3, 31.4, s_side, 1.0),
    (31.4, 38.6, s_upper, 1.0),
    (38.6, 47.0, s_full, 1.0),
    (47.0, 56.24, s_xray, 1.0),
    (56.24, 61.6, s_pullout, 1.0),
    (61.6, 65.2, s_ignite, 1.0),
    (65.2, 67.76, s_liftoff_tele, 1.0),
    (67.76, 74.92, s_climb, 1.0),
    (74.92, 83.2, s_sep, 1.0),
    (83.2, 96.64, s_ladder, 1.0),
    (96.64, 106.64, s_leaving, 1.0),
    (106.64, 115.1, s_ladder2, 1.0),
    (115.1, 117.65, s_black, 1.0),
    (117.65, 118.58, s_flip, 3.0),
    (118.58, 125.6, s_boostback_wide, 3.0),
    (125.6, 133.0, s_boostback_close, 3.0),
    (133.0, 139.6, s_fins, 2.6),
    (139.6, 149.04, s_longway, 3.2),
    (149.04, 159.4, s_aiming, 3.2),
    (159.4, 166.56, s_entry, 1.2),
    (166.56, 173.52, s_falling, 2.2),
    (173.52, 179.2, s_landburn, 1.8),
    (179.2, 184.9, s_legs, 1.8),
    (184.9, 190.3, s_orbit, 1.5),
    (190.3, T_TOUCH, s_overhead, 1.0),
    (T_TOUCH, 205.0, s_touchdown, 1.0),
    (205.0, 222.8, s_arcs, 1.0),
    (222.8, 236.3, s_standing, 1.0),
    (236.3, 242.96, s_topdown, 1.0),
    (242.96, 247.6, s_foot, 1.0),
    (247.6, 254.0, s_alone, 1.3),
    (254.0, 259.28, s_desk, 1.0),
    (259.28, 273.24, s_board, 1.0),
    (273.24, 275.3, s_board_glow, 1.0),
    (275.3, 280.3, s_arcs_return, 1.0),
    (280.3, 293.0, s_dawn, 1.0),
    (293.0, DUR + 1, s_room_dawn, 1.0),
]
DISSOLVES = {275.3: 0.7, 280.3: 1.2, 293.0: 1.4}          # cut time -> dissolve length (s), centred on the cut

def shot_at(t):
    for i, (a, b, f, e) in enumerate(SHOTS):
        if a <= t < b: return i
    return len(SHOTS) - 1

def hdr_at(t, W, H):
    i = shot_at(t); a, b, f, e = SHOTS[i]
    img = f(t, W, H, clamp((t - a) / (b - a))) * e
    # dissolves across marked cuts
    for tc, d in DISSOLVES.items():
        if tc - d / 2 <= t < tc + d / 2:
            j = shot_at(tc - 1e-3) if t >= tc else shot_at(tc)
            a2, b2, f2, e2 = SHOTS[j]
            other = f2(t, W, H, clamp((t - a2) / (b2 - a2))) * e2
            k = (t - (tc - d / 2)) / d                     # 0 -> 1 across the dissolve
            mine_w = k if t >= tc else 1 - k
            img = img * mine_w + other * (1 - mine_w)
    return img

# ================================================================ text: documentary subtitles, mission captions, title
@lru_cache(256)
def _font(path, size): return ImageFont.truetype(path, size)

def sub_size(W, H): return int((64 if not vert(W, H) else 58) * S(W, H))

@lru_cache(128)
def text_sprite(text, path, size, track=0, maxw=0):
    """(alpha, shadow) float32 sprites for a line of text, wrapped to maxw px."""
    f = _font(path, size)
    words = text.split(" "); rows = [[]]
    for w in words:
        trial = " ".join(rows[-1] + [w])
        if rows[-1] and maxw and f.getlength(trial) + track * len(trial) > maxw: rows.append([w])
        else: rows[-1].append(w)
    rows = [" ".join(r) for r in rows]
    lh = int(size * 1.25); pad = int(size * 0.7)
    widths = [f.getlength(r) + track * max(0, len(r) - 1) for r in rows]
    Wd = int(max(widths) + 2 * pad); Hd = int(lh * len(rows) + 2 * pad)
    im = Image.new("L", (Wd, Hd), 0); d = ImageDraw.Draw(im)
    for i, r in enumerate(rows):
        x = (Wd - widths[i]) / 2; y = pad + i * lh
        if track:
            for ch in r: d.text((x, y), ch, font=f, fill=255); x += f.getlength(ch) + track
        else: d.text((x, y), r, font=f, fill=255)
    a = np.asarray(im, F32) / 255
    sh = cv2.GaussianBlur(a, (0, 0), size * 0.18)
    return a, sh

def blit_text(img, text, path, size, cx, cy, op, col=(1, 1, 1), track=0, maxw=0, shadow=0.75, anchor="c"):
    if op <= 0.003: return
    a, sh = text_sprite(text, path, size, track, maxw)
    h, w = a.shape; H, W = img.shape[:2]
    x0 = int(cx - w / 2) if anchor == "c" else int(cx - int(size * 0.7)); y0 = int(cy - h / 2)
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + w), min(H, y0 + h)
    if xb <= xa or yb <= ya: return
    sl = (slice(ya - y0, yb - y0), slice(xa - x0, xb - x0)); reg = img[ya:yb, xa:xb]
    reg *= (1 - np.clip(sh[sl] * 1.5, 0, 1) * shadow * op)[..., None]
    A = (a[sl] * op)[..., None]
    reg *= (1 - A); reg += A * np.asarray(col, F32)

INTRO_SLATE = [(7.2, "December 21"), (9.95, ", 2015"), (12.8, "Cape Canaveral"), (15.45, "Night")]

SPLIT = {"But this one turned around": [3]}          # word indexes to break a line at (the cut lands on "turned around")

def _split_lines(lines):
    out = []
    for L in lines:
        cuts = SPLIT.get(L['text'])
        if not cuts: out.append(L); continue
        idx = [0] + cuts + [len(L['words'])]
        for a, b in zip(idx[:-1], idx[1:]):
            s0 = L['wt'][a]; e0 = L['wt'][b] - 0.08 if b < len(L['words']) else L['e']
            out.append(dict(L, text=" ".join(L['words'][a:b]), words=L['words'][a:b], wt=L['wt'][a:b], s=s0, e=e0))
    return out

def subtitles(img, t, W, H):
    if C.STATE["clean"]: return
    flt = C.STATE["lyric_filter"]
    v = vert(W, H); fs = sub_size(W, H); maxw = W * (0.72 if v else 0.80)
    cy = H * (0.73 if v else 0.875)
    vis = _split_lines([L for L in LN if L['sec'] != "INTRO" and (flt is None or flt(L)) and L['s'] < T_END - 0.3])
    for i, L in enumerate(vis):
        nxt = vis[i + 1]['s'] if i + 1 < len(vis) else 1e9
        a0, a1 = L['s'] - 0.16, L['s'] + 0.06
        end = min(L['e'] + 0.15, nxt - 0.12, T_END - 0.35)
        b0, b1 = end, min(end + 0.3, nxt - 0.02)
        if not (a0 <= t <= b1): continue
        op = sstep(a0, a1, t) * (1 - sstep(b0, b1, t))
        blit_text(img, L['text'], F_SUB, fs, W / 2, cy, op, maxw=maxw)

def slate(img, t, W, H):
    """the spoken intro as a documentary slate building up in the lower left: date, place, 'Night'."""
    if C.STATE["clean"] or t > 18.2: return
    v = vert(W, H); s = S(W, H)
    fs = int(40 * s); track = int(5 * s)
    x = W * (0.07 if not v else 0.13); y = H * (0.79 if not v else 0.68)
    out = 1 - sstep(16.9, 17.6, t)
    line1 = ""
    for (tt, txt) in INTRO_SLATE[:2]:
        if t >= tt - 0.05: line1 += txt
    rows = [line1.upper()] if line1 else []
    if t >= INTRO_SLATE[2][0] - 0.05: rows.append(INTRO_SLATE[2][1].upper())
    if t >= INTRO_SLATE[3][0] - 0.05: rows.append(INTRO_SLATE[3][1].upper())
    for i, r in enumerate(rows):
        t_in = [7.2, 12.8, 15.45][i]
        op = sstep(t_in - 0.05, t_in + 0.35, t) * out
        a, sh = text_sprite(r, F_CAP, fs, track, 0)
        blit_text(img, r, F_CAP, fs, x, y + i * fs * 1.5, op * 0.92, anchor="l", track=track)

CAPTIONS = [(77.3, 82.2, "T+00:02:25   STAGE SEPARATION"),
            (159.4, 164.2, "T+00:08:01   ENTRY BURN"),
            (186.0, 190.1, "11 SATELLITES · DEPLOYED BY T+00:19:05"),
            (T_TOUCH + 0.25, 203.2, "T+00:09:44   LANDING ZONE 1"),
            (236.3, 239.2, "28.4858° N   80.5442° W")]

def captions(img, t, W, H):
    if C.STATE["clean"]: return
    v = vert(W, H); s = S(W, H)
    fs = int(34 * s); track = int(4 * s)
    for a, b, txt in CAPTIONS:
        if not (a <= t <= b + 0.5): continue
        op = sstep(a, a + 0.4, t) * (1 - sstep(b, b + 0.5, t))
        x = W * (0.07 if not v else 0.13); y = H * (0.10 if not v else 0.17)
        rows = [txt]
        if v:                                    # a tall frame: the two halves of a caption on two lines, inside the phone-safe width
            for sep in ("   ", " · "):
                if sep in txt: rows = [r.strip() for r in txt.split(sep)]; break
        n_all = sum(len(r) for r in rows); done = 0
        k_all = int(round(n_all * clamp((t - a) / 0.7)))                 # typed on
        for i, r in enumerate(rows):
            k = max(0, min(len(r), k_all - done)); done += len(r)
            if k <= 0 and i > 0: break
            blit_text(img, r[:max(1, k)], F_CAP, fs, x, y + i * fs * 1.45, op * 0.9, anchor="l", track=track)

def title(img, t, W, H):
    """the song title over the empty room at dawn, between the last two "One came home"s: the room dims under it like a
    screen at the end of a film, so the white type reads over the paper."""
    if C.STATE["clean"]: return
    a, b = 295.0, 301.7
    if not (a - 0.5 <= t <= b + 0.6): return
    op = sstep(a, a + 1.6, t) * (1 - sstep(b - 0.9, b, t))
    v = vert(W, H); s = S(W, H)
    fs = int((118 if not v else 96) * s)
    cy = H * (0.46 if not v else 0.44)
    yy = (np.arange(H, dtype=F32)[:, None] - cy) / (H * (0.24 if not v else 0.16))
    img *= (1 - op * (0.30 + 0.56 * np.exp(-yy * yy)))[..., None]
    blit_text(img, "eleven kept going", F_TITLE, fs, W / 2, cy, op, shadow=0.6)
    blit_text(img, "aditazzz", F_TITLE2, int(40 * s), W / 2, cy + fs * 0.95, op * 0.85, track=int(6 * s), shadow=0.6)

# ================================================================ frame
EKG_SCALE = float(os.environ.get("EKG_SCALE", "1.0"))           # < 1: render the picture smaller and upscale (previews)
RENDER_SCALE_9x16 = 0.8

def render_frame(t, W=1920, H=1080, fi=0):
    k = EKG_SCALE * (RENDER_SCALE_9x16 if vert(W, H) else 1.0)
    if k < 0.999:
        w2, h2 = int(round(W * k / 2) * 2), int(round(H * k / 2) * 2)
        img = cv2.resize(hdr_at(t, w2, h2), (W, H), interpolation=cv2.INTER_CUBIC); img = np.maximum(img, 0)
    else:
        img = hdr_at(t, W, H)
    out = K.develop(img, fi).astype(F32)
    slate(out, t, W, H); subtitles(out, t, W, H); captions(out, t, W, H); title(out, t, W, H)
    if not C.STATE["clean"]:
        C.subscribe_pill(out, t, W, H, 27.0, 5.0)
        C.end_screen(out, t, W, H, T_END, DUR - T_END, "One came home.", sub_line="Subscribe for a new song every week",
                     title="Eleven Kept Going", accent=ORANGE)
    out *= (1 - sstep(DUR - 1.0, DUR - 0.05, t))
    return (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)
