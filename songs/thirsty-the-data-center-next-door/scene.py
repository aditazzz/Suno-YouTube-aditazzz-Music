"""Thirsty (The Data Center Next Door): aditazzz. A small town in a toxic relationship with the windowless data center across its river.

The building is the seductive, insatiable lover: it never sleeps, it breathes with the groove, it drinks the river
down chorus by chorus and turns the town's windows blue at the end. She is only ever a silhouette.

Every frame is a pure function of t. The timeline below is data: each shot is anchored to sung words and downbeats
from build/timed.json and build/beats.json (studio.sync + sync_fix.py), and is written to build/timeline.json.
Picture: 2.39:1 inside 1920x1080, lyrics set in the lower bar.
"""
import os, sys, math, json
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
ROOT = os.path.dirname(os.path.dirname(HERE)); sys.path.insert(0, ROOT)
from studio import core as C
import ys_eng as E
from ys_eng import F32, hexc, sstep, clamp, lerp, ease_io, ease_out, ease_in, keys
import ys_world as WD
import ys_rooms as RM
import ys_details as DT
import ys_type as TY
import ys_house as HS
import ys_her as HER
import ys_people as PP
import ys_town as TW

TM = C.Timing(HERE)
LN = TM.lines
SONG = TM.duration                       # 222.64
TAIL = 4.0
DUR = SONG + TAIL
T_END = 221.6                            # end card (YouTube end screen) from here
A = json.load(open(os.path.join(HERE, "build", "analysis.json")))
ENV_LOW = np.array(A["env_low"], F32); ENV_RMS = np.array(A["env_rms"], F32)
ECHO = json.load(open(os.path.join(HERE, "build", "echoes.json")))
DB = np.array(TM.downbeats); BEATS = np.array(TM.beats)
BAR = float(np.median(np.diff(DB)))       # ~1.80 s
C.THEME.update(disp=TY.F_DIDONE, body=TY.F_SUB, dispb=TY.F_DIDONE, mono=TY.F_MONOB, red=hexc('b3203a') ** (1 / 2.2))

def L(sub, nth=0): return TM.line_t(sub, nth)
def Wd(sub, word, nth=0): return TM.word_t(sub, word, nth)
def db_near(t): return float(DB[np.argmin(np.abs(DB - t))])
def env(arr, t, smooth=0):
    i = int(np.clip(t / 0.01, 0, len(arr) - 1))
    if smooth: return float(arr[max(0, i - smooth):i + smooth + 1].mean())
    return float(arr[i])
def sec(name): return TM.section(name)
def lv(a, b, k): return np.asarray(a, F32) * (1 - k) + np.asarray(b, F32) * k

# ---------------------------------------------------------------- the story clock
T_GROOVE = 3.83
T_SECOND = Wd("asking for a second house", "second")
T_CH = [sec('CH1')['s'], sec('CH2')['s'], sec('FINAL')['s']]
OFF2 = T_CH[1] - T_CH[0]                 # CH2 = CH1 + 86.5
OFF3 = T_CH[2] - T_CH[0]                 # FINAL = CH1 + 129.8
WATER = [(0.0, -0.55), (T_CH[0], -0.62), (T_CH[0] + 8, -0.95), (sec('POST1')['s'], -1.05), (sec('V2')['s'], -1.35),
         (T_CH[1], -1.75), (T_CH[1] + 10, -2.2), (sec('BRIDGE')['s'], -2.4), (T_CH[2], -2.7), (T_CH[2] + 12, -3.1),
         (sec('OUTRO')['s'], -3.2), (DUR, -3.26)]
DRY = [(0.0, 0.0), (sec('V2')['s'], 0.25), (T_CH[1], 0.45), (T_CH[2], 0.8), (sec('OUTRO')['s'], 1.0)]

def breath(t):
    """the building breathes: one slow inhale/exhale per bar, deeper in the choruses, pushed by the bass."""
    u = ((t - DB[0]) / BAR) % 1.0
    b = 0.5 - 0.5 * math.cos(2 * math.pi * u)
    depth = 0.35 if t > T_GROOVE else 0.1
    for s0 in T_CH:
        if s0 - 0.2 <= t < s0 + 29.5: depth = 0.85
    lo = env(ENV_LOW, t, 8)
    return float(np.clip(0.5 + (b - 0.5) * depth + (lo - 0.4) * 0.35, 0, 1))

def world(t, **kw):
    S = WD.default_state()
    S['water'] = keys(WATER, t); S['dry'] = keys(DRY, t)
    S['second'] = sstep(T_SECOND - 0.3, T_SECOND + 3.2, t)
    S['breath'] = breath(t); S['cloud_t'] = t
    S.update(kw)
    return S

def valley(cam, S, t, extra=None, **kw):
    return WD.compose(WD.render(cam, S, t, extra=extra, **kw))

def house_extra(S, t, **hs):
    H2 = dict(S); H2.update(hs)
    def ex(cv): HS.draw(cv, H2, t)
    return ex

# ================================================================ shots (t, W, H, u in 0..1, p params) -> linear HDR
# ---- INTRO
def sh_intro(t, W, H, u, p):
    """near black: the facility across the dark water; a thin red light wakes in its face; slow push over the river."""
    k = ease_io(u)
    cam = E.Cam(lv((-600, 2.4, -150), (-612, 2.0, -70), k), lv((-620, 22, 230), (-620, 24, 230), k), fov=lerp(30, 27, k), W=W, H=H, drift=0.02, t=t, seed=1)
    g = sstep(T_GROOVE - 0.05, T_GROOVE + 0.4, t)
    S = world(t, stars=0.35, mono_lights=0.05 + 0.35 * g, red_slit=keys([(0, 0.02), (2.8, 0.12), (T_GROOVE, 0.25), (9.9, 0.55), (14.5, 1.0)], t),
              plumes=0.25 + 0.5 * g, town_lights=0.25, fog=1.2, glow=0.4 + 0.6 * g, tree_clear=90)
    img = valley(cam, S, t)
    return img * (0.55 + 0.45 * g)

def sh_intro_slit(t, W, H, u, p):
    """push into the red slit; the frame rolls a quarter turn so the slit lies down: the match cut to the ribbon."""
    k = ease_in(u)
    M = WD.MONO_A; cx = (M['x0'] + M['x1']) / 2
    eye = lv((cx - 4, 8.0, -40), (cx, 24.0, M['z0'] - 9.0), k)
    tgt = np.array([cx, 24.0, M['z0']], F32)
    cam = E.Cam(eye, tgt, fov=lerp(26, 18, k), W=W, H=H, roll=-math.pi / 2 * ease_io(clamp((u - 0.35) / 0.65)), drift=0.01, t=t, seed=3)
    S = world(t, stars=0.3, mono_lights=0.4, red_slit=1.0, plumes=0.6, town_lights=0.25, fog=1.1, tree_clear=90)
    img = valley(cam, S, t)
    return img * (1 + 1.5 * sstep(0.85, 1.0, u))

# ---- V1 (dusk)
T_RIBBON = Wd("You rolled into town", "ribbon"); T_SHOVEL = Wd("You rolled into town", "shovel")
def dusk_state(t, **kw):
    return world(t, dusk=kw.pop('dusk', 1.0), sun_az=kw.pop('sun_az', -0.25), stars=0.0, cloud=0.7, glow=kw.pop('glow', 0.5), **kw)

def sh_ceremony(t, W, H, u, p):
    return PP.draw_ceremony(W, H, t, u, dusk_state(t, tree_clear=40), T_RIBBON, T_SHOVEL)

T_THOUSAND = Wd("promised me the future", "thousand")
def sh_town_hill(t, W, H, u, p):
    """the town from the hill at dusk, the facility on the horizon; a thousand windows come on."""
    k = ease_io(u)
    cam = E.Cam(lv((640, 58, -960), (600, 54, -930), k), (-560, 30, 210), fov=lerp(30, 27, k), W=W, H=H, drift=0.03, t=t, seed=5)
    wave = keys([(p['_t0'], 0.12), (T_THOUSAND - 0.3, 0.25), (T_THOUSAND + 1.6, 1.0)], t)
    S = dusk_state(t, dusk=0.85, sun_az=-0.9, win_wave=wave, town_lights=1.0)
    return valley(cam, S, t, extra=lambda cv: TW.school(cv, S, t))

def sh_facade_track(t, W, H, u, p):
    """a slow low track along the windowless facade: no windows, just the seams, the washers and the scale."""
    k = u
    M = WD.MONO_A
    cam = E.Cam(lv((M['x1'] + 30, 1.6, M['z0'] - 46), (M['x1'] - 70, 1.6, M['z0'] - 44), k), lv((M['x1'] - 120, 34, M['z0']), (M['x1'] - 220, 36, M['z0']), k),
                fov=46, W=W, H=H, drift=0.01, t=t, seed=7)
    S = dusk_state(t, dusk=0.55 - 0.25 * u, sun_az=-0.6, tree_clear=200, glow=0.7)
    return valley(cam, S, t, extra=lambda cv: PP.draw_fence(cv, S, t))

def sh_house_night(t, W, H, u, p):
    """her house at night: one window lit upstairs, the facility glowing across the river; the hum."""
    k = ease_io(u)
    cam = E.Cam(lv(HS.P(11.0, 1.7, -7.0), HS.P(9.5, 1.75, -5.0), k), HS.P(-3.0, 4.5, 30.0), fov=40, W=W, H=H, drift=0.02, t=t, seed=8)
    S = world(t, stars=0.55, tree_clear=25)
    return valley(cam, S, t, extra=house_extra(S, t, porch=0.0, win_up=1.0, win_down=0.0))

# ---- PRE (power lines, the lamp, the bill)
def sh_lines(t, W, H, u, p):
    """low under the pylon line, the wires converge on the facility; surges ride the wires on the beat."""
    k = ease_io(u)
    bases, hd = WD.pylon_line()
    b = bases[p.get('tower', 5)]; fwd = np.array([math.cos(hd), 0, math.sin(hd)], F32); side = np.array([-fwd[2], 0, fwd[0]], F32)
    b3 = np.array([b[0], 0, b[1]], F32)
    eye = lv(b3 - fwd * 30 + side * 10 + np.array([0, 1.6, 0], F32), b3 - fwd * 18 + side * 8 + np.array([0, 1.7, 0], F32), k)
    tgt = b3 + fwd * 300 + np.array([0, 70 - 10 * k, 0], F32)
    cam = E.Cam(eye, tgt, fov=p.get('fov', 58), W=W, H=H, drift=0.02, t=t, seed=2)
    lo = env(ENV_LOW, t, 2)
    S = world(t, stars=0.5, surge=p.get('surge', 1.0) * (0.4 + 1.2 * lo), surge_phase=((t - DB[0]) / (BAR / 2)) % 1.0, hum=lo * p.get('hum', 1.0), tree_clear=60)
    return valley(cam, S, t)

T_OFF = Wd("I turn mine off", "off")
def sh_bedroom(t, W, H, u, p):
    t_off = p.get('t_off', T_OFF)
    lamp = p.get('lamp', 1.0 - sstep(t_off - 0.04, t_off + 0.08, t))
    cp = p.get('cam')
    if cp: cam = RM.bedroom_cam(W, H, u=cp[0], v=cp[1], w=cp[2], tu=cp[3], tv=cp[4], fov=cp[5], push=ease_io(u) * p.get('push', 0.35), t=t)
    else: cam = RM.bedroom_cam(W, H, push=ease_io(u) * p.get('push', 0.35), t=t)
    cv = RM.draw_bedroom(W, H, dict(lamp=lamp, window_light=1.0, blind_open=0.55, breath=breath(t), glass_level=p.get('glass', 0.8)), t, cam=cam,
                         valley_S=world(t, stars=0.4))
    return cv.img + cv.emis

def make_bill(t_number, t_mine, second=False):
    def sh(t, W, H, u, p):
        hist = [0.30, 0.33, 0.31, 0.36, 0.40, 0.46, 0.51, 0.55, 0.60, 0.66, 0.73, 0.81, 0.0]
        if second: hist = [min(0.88, h + 0.06) for h in hist[:-1]] + [0.0]
        n = (t - t_number) / (BAR / 4)
        bars = [hv * ease_out(clamp(n - k * 0.55)) for k, hv in enumerate(hist[:-1])]
        bars.append(keys([(t_mine - 1.6, 0.0), (t_mine - 0.15, 0.80), (t_mine + 0.06, 0.97 if not second else 1.05), (t_mine + 1.2, 0.99 if not second else 1.08)], t, ease=ease_in))
        a0, a1 = (96.0, 316.0) if not second else (318.0, 524.17)
        amt = a0 + (a1 - a0) * clamp((t - t_number) / (t_mine - t_number)) ** 1.6
        hit = sstep(t_mine - 0.02, t_mine + 0.06, t) * (1 - sstep(t_mine + 0.4, t_mine + 1.0, t))
        ta = ease_io(clamp((t - (t_mine - 1.4)) / 1.5)) * (0.85 if second else 0.6)
        return DT.draw_bill(W, H, t, dict(bars=bars, amount=f"$ {amt:,.2f}", hit=hit, push=ease_io(u) * (1.4 if second else 1.0) * (1 - ta), breath=breath(t), focus=0.52, to_amount=ta))
    return sh

T_NUMBER = L("Everybody's got a number"); T_MINE = Wd("and you're about to hit mine", "mine")
T_NUMBER2 = L("Everybody's got a number", 1); T_MINE2 = Wd("and you're about to hit mine", "mine", 1)
sh_bill = make_bill(T_NUMBER, T_MINE); sh_bill2 = make_bill(T_NUMBER2, T_MINE2, second=True)

def sh_black(t, W, H, u, p):
    """near black: the facility's silhouette and its red slit (both houses after V2)."""
    cam = E.Cam((-760, 2.0, -90), (-820, 24, 240), fov=34, W=W, H=H, drift=0.01, t=t, seed=9)
    S = world(t, stars=0.2, mono_lights=0.06, red_slit=1.0, plumes=0.3, town_lights=0.2, fog=1.3, glow=0.3, tree_clear=100)
    return valley(cam, S, t) * p.get('gain', 1.0)

# ---- CHORUS pieces
def sh_across(t, W, H, u, p):
    """the facility across the river at night, breathing, mirrored in the water."""
    k = ease_io(u)
    cam = E.Cam(lv(p.get('e0', (-360, 1.5, -46)), p.get('e1', (-372, 1.45, -40)), k), lv(p.get('g0', (-650, 24, 230)), p.get('g1', (-655, 25, 230)), k),
                fov=p.get('fov', 36) - 2 * k, W=W, H=H, drift=0.02, t=t, seed=4)
    S = world(t, stars=0.55, tree_clear=70)
    return valley(cam, S, t)

def sh_river_close(t, W, H, u, p):
    S = world(t, stars=0.4)
    t0 = p['_t0']
    S['water'] = keys(WATER, t0) - p.get('drop', 0.16) * ease_io(u)
    return DT.draw_river_close(W, H, t, dict(push=ease_io(u), water_hi=keys(WATER, t0) + p.get('hi', 0.0)), S, x=p.get('x', -520.0))

def sh_fans(t, W, H, u, p):
    z = lerp(p.get('z0', 1.2), p.get('z1', 3.2), ease_io(u))
    rot = p.get('r0', 0.2) + p.get('rv', 0.05) * (t - p['_t0'])
    return DT.draw_fans(W, H, t, dict(zoom=z, rot=rot, breath=breath(t), red=p.get('red', 0.85), speed=p.get('speed', 0.42),
                                      cx=p.get('cx', 0.0), cy=p.get('cy', 0.0), glow=1.0, ripple=p.get('ripple', 0.0)))

def sh_lightbill(t, W, H, u, p):
    """the town from above at night: its streetlights go out one by one while the facility brightens."""
    k = ease_io(u)
    cam = E.Cam(lv((520, 70, -880), (500, 74, -860), k), lv((-420, 20, 150), (-450, 20 + 70 * p.get('tilt', 1.0), 180), k), fov=34, W=W, H=H, drift=0.03, t=t, seed=11)
    dim = keys([(p['_t0'], 0.0), (p['_t1'] - 0.6, p.get('dim', 0.75))], t, ease=lambda x: x)
    S = world(t, stars=0.5, street_dim=dim, win_off=dim * 0.6, glow=1.0 + 0.6 * k)
    S['breath'] = min(1.0, S['breath'] + 0.3 * k)
    return valley(cam, S, t)

def sh_porch(t, W, H, u, p):
    """on the porch behind her; the yard, the river and the facility. Dolly zoom: the long lens pulls the facility in."""
    k = ease_io(u)
    z0, z1 = p.get('zoom', (0.0, 0.0))
    z = lerp(z0, z1, k)
    fov = lerp(46, 15, z)
    back = math.tan(math.radians(46) / 2) / math.tan(math.radians(fov) / 2)
    her = HS.P(-0.45, HS.PORCH_FL + 1.7, HS.HD + HS.PORCH_D - 0.35)
    eye = her + (HS.P(0.55, HS.PORCH_FL + 1.55, HS.HD + 0.35) - her) * back
    tgt = HS.P(-1.5, 10.0 + 18 * z, HS.HD + 330)
    cam = E.Cam(eye, tgt, fov=fov, W=W, H=H, drift=0.01, t=t, seed=12)
    S = world(t, stars=0.45, tree_clear=20)
    cv = WD.render(cam, S, t, extra=house_extra(S, t, porch=1.0, win_up=0.0, win_down=0.25, racks=p.get('racks', 0)))
    x, y, zz = cam.project(her[None]); hh = 0.235 * cam.fpx / zz[0]
    HER.draw(cv.img, 'stand_back', float(x[0]), float(y[0]), hh, light_dir=(0.2, -1.0), rim=hexc('ffc27a') * 0.5 + hexc('cfe2ee') * 0.08,
             backlit=0.7, emis=cv.emis, t=t, seed=5)
    return WD.compose(cv)

def sh_price(t, W, H, u, p):
    """black: a price alone (the confrontation, the outro's quiet numbers); the type is drawn by the overlays."""
    return np.zeros((H, W, 3), F32)

def sh_yard(t, W, H, u, p):
    """her front lawn full of somebody else's servers, blinking; she stands among them facing the facility.
    On "yard" every LED in the lawn turns red."""
    k = ease_io(u)
    cam = E.Cam(lv(HS.P(6.4, 1.15, HS.HD + 2.6), HS.P(5.9, 1.2, HS.HD + 4.0), k), HS.P(1.5, 3.6, HS.HD + 70), fov=p.get('fov', 50), W=W, H=H, drift=0.015, t=t, seed=13)
    S = world(t, stars=0.4, tree_clear=25)
    tr = p.get('t_red', 1e9)
    red = sstep(tr - 0.05, tr + 0.15, t)
    cv = WD.render(cam, S, t, extra=house_extra(S, t, porch=1.0, win_up=0.0, racks=p.get('racks', 2), rack_red=red))
    her = HS.P(3.1, 1.7, HS.HD + 10.6)
    x, y, z = cam.project(her[None]); hh = 0.235 * cam.fpx / z[0]
    HER.draw(cv.img, 'stand_back', float(x[0]), float(y[0]), hh, light_dir=(-0.2, -1.0), rim=hexc('cfe2ee') * 0.35 + hexc('ff2236') * 0.25 * red,
             backlit=0.75, emis=cv.emis, t=t, seed=19, dep=cv.dep, depth=float(z[0]))
    return WD.compose(cv)

def sh_glass(t, W, H, u, p):
    lev = lerp(p.get('l0', 0.82), p.get('l1', 0.30), ease_in(u))
    return DT.draw_glass(W, H, t, dict(level=lev, wob=0.3 + 0.5 * env(ENV_LOW, t, 2), push=u))

def sh_meter(t, W, H, u, p):
    t0 = p['_t0']; r0, r1 = p.get('rate', (0.6, 4.0)); tb = p.get('t_break', 1e9); d = max(0.1, p['_t1'] - t0)
    def phase(tt):
        x = min(tt, tb) - t0
        return r0 * x + (r1 - r0) * x * x / (2 * d)
    rate = (r0 + (r1 - r0) * u) if t < tb else 0.0
    return DT.draw_meter(W, H, t, dict(rate=rate, phase=phase(t), dials=4812.0 + phase(t) * 0.8, porch=1.0, push=u))

def sh_pipe(t, W, H, u, p):
    return DT.draw_pipe(W, H, t, dict(flow=p.get('flow', 0.6) + 0.3 * env(ENV_LOW, t, 2), breath=breath(t), push=ease_io(u)))

# ---- POST (hypnotic)
def sh_plume_black(t, W, H, u, p):
    """a steam column rising into the black sky; nothing else."""
    k = ease_io(u)
    M = WD.MONO_A; st = WD.stacks(M)[1]
    cam = E.Cam(lv((st[0] + 150, 40, st[2] - 420), (st[0] + 140, 42, st[2] - 400), k), (st[0] - 10, st[1] + 95 + 25 * k, st[2]), fov=34, W=W, H=H, drift=0.01, t=t, seed=15)
    S = world(t, stars=0.5, mono_lights=0.55, town_lights=0.0, glow=0.6, fog=0.8, cloud=0.25)
    return valley(cam, S, t) * (1 - 0.5 * sstep(0.75, 1.0, u))

# ---- V2 (summer dusk)
T_ROOF = Wd("Okay, I'll give you", "roof,")
def sh_school(t, W, H, u, p):
    k = ease_io(u)
    c = WD.SCHOOL
    cam = E.Cam(lv(c + np.array([150, 24, -150], F32), c + np.array([138, 22, -140], F32), k), c + np.array([6, 6, 6], F32), fov=lerp(40, 37, k), W=W, H=H, drift=0.02, t=t, seed=17)
    S = dusk_state(t, dusk=0.9, sun_az=-0.85, tree_clear=50)
    glint = clamp((t - (T_ROOF - 0.8)) / 1.6)
    return valley(cam, S, t, extra=lambda cv: TW.school(cv, S, t, roof_glint=glint))

def sh_town_dusk(t, W, H, u, p):
    """from the bridge at dusk: the river, the town lights, the facility on the horizon. It looks almost beautiful."""
    k = ease_io(u)
    cam = E.Cam(lv((-20, 5.5, -12), (-26, 5.6, -10), k), lv((-560, 14, 200), (-570, 14, 205), k), fov=34, W=W, H=H, drift=0.02, t=t, seed=19)
    S = dusk_state(t, dusk=0.95, sun_az=-0.85, tree_clear=40)
    return valley(cam, S, t)

def sh_booth(t, W, H, u, p):
    """the gate at dusk: the booth's warm light, her cousin outside it, back to us, watching the gate."""
    k = ease_io(u)
    b = WD.BOOTH
    cam = E.Cam(lv(b + np.array([7.0, 1.55, -14.0], F32), b + np.array([5.5, 1.6, -12.0], F32), k), b + np.array([-6.0, 4.5, 60.0], F32), fov=40, W=W, H=H, drift=0.015, t=t, seed=21)
    S = dusk_state(t, dusk=0.45, sun_az=0.2, tree_clear=40, glow=0.9)
    def ex(cv):
        PP.draw_fence(cv, S, t); PP.draw_booth(cv, S, t)
    cv = WD.render(cam, S, t, extra=ex)
    img = WD.compose(cv)
    P = b + np.array([1.2, 1.80, -2.6], F32)
    x, y, z = cam.project(P[None]); hh = 0.24 * cam.fpx / z[0]
    PP.man(img, float(x[0]), float(y[0]), hh, rim=hexc('ffd49a') * 0.35, light_dir=(-0.6, -0.6), body=hexc('0a0b0d') * 0.5, cap=True, emis=cv.emis, sway=0.01 * math.sin(t))
    _security_text(img, float(x[0]), float(y[0]) + hh * 2.2, hh)
    return img

def _security_text(img, x, y, hh):
    m, ox, oy = TY.glyphs("SECURITY", TY.F_SANS, max(6, int(hh * 0.42)), int(hh * 0.05))
    TY.blit(img, m, x - m.shape[1] / 2, y - m.shape[0] / 2, hexc('d8d4c8') * 0.06, 0.9)

def sh_booth_close(t, W, H, u, p):
    """through the booth window: him at his little TV, the endless wall behind."""
    k = ease_io(u)
    b = WD.BOOTH
    cam = E.Cam(lv(b + np.array([-2.5, 1.5, -4.2], F32), b + np.array([-2.2, 1.5, -3.6], F32), k), b + np.array([1.5, 2.6, 8.0], F32), fov=44, W=W, H=H, drift=0.01, t=t, seed=23)
    S = world(t, dusk=0.15, stars=0.3, tree_clear=40)
    def ex(cv):
        PP.draw_fence(cv, S, t); PP.draw_booth(cv, S, t, inside_light=1.3)
    cv = WD.render(cam, S, t, extra=ex)
    img = WD.compose(cv)
    P = b + np.array([0.15, 1.55, 0.1], F32)
    x, y, z = cam.project(P[None]); hh = 0.24 * cam.fpx / z[0]
    flick = 0.7 + 0.3 * math.sin(t * 13) * math.sin(t * 7.3)
    E.soft_glow(img, x[0] + hh * 1.4, y[0] + hh * 1.6, hh * 1.2, hexc('8fb8ff'), 0.05 * flick)
    PP.man(img, float(x[0]), float(y[0]), hh, rim=hexc('8fb8ff') * 0.3 * flick + hexc('ffd49a') * 0.2, light_dir=(0.8, 0.2), body=hexc('0a0b0d') * 0.6, cap=True, emis=cv.emis)
    return img

def sh_creek(t, W, H, u, p):
    """the creek running low at the end of a summer day: the bed is cracking, the last water a ribbon of sky."""
    k = ease_io(u)
    x0 = 230.0; zc = float(WD.river_zc(x0))
    S = dusk_state(t, dusk=0.75, sun_az=-0.75, tree_clear=30, glow=0.6)
    h = -3.22; S['water'] = h; S['dry'] = 0.85
    cam = E.Cam(lv((x0 + 16, h + 1.5, zc - 9), (x0 + 12, h + 1.45, zc - 8), k), (x0 - 160, h + 7, zc + 70), fov=46, W=W, H=H, drift=0.015, t=t, seed=43)
    cv = WD.render(cam, S, t)
    img = WD.compose(cv)
    TW.fireflies(img, cam, t, cam.eye + np.array([-14, 0.2, 7], F32), n=18, spread=(7.0, 1.2, 6.0), gain=0.7)
    return img

def sh_bed_hum(t, W, H, u, p):
    """night, lamp off: the glass on the nightstand trembles with the hum."""
    return DT.draw_glass(W, H, t, dict(level=0.7, wob=0.6 + 0.8 * env(ENV_LOW, t, 1), push=0.3 * u))

def sh_second(t, W, H, u, p):
    """the second house rising next door, cranes over it, at the last of the light."""
    k = ease_io(u)
    cam = E.Cam(lv((-290, 15.0, -118), (-300, 15.5, -108), k), (-900, 30, 300), fov=40, W=W, H=H, drift=0.02, t=t, seed=25)
    S = dusk_state(t, dusk=0.5, sun_az=-1.1, tree_clear=60, glow=1.0)
    return valley(cam, S, t, extra=lambda cv: TW.cranes(cv, S, t, S['second']))

def sh_two(t, W, H, u, p):
    """two houses now; she stands on the bank, small, facing them."""
    k = ease_io(u)
    hz = float(WD.river_zc(-706)) - WD.RIVER_W - 1.0
    eye = lv((-700, 1.7, hz - 26), (-704, 1.7, hz - 22), k)
    cam = E.Cam(eye, (-860, 24, 260), fov=38, W=W, H=H, drift=0.015, t=t, seed=27)
    S = world(t, stars=0.5, tree_clear=50)
    cv = WD.render(cam, S, t, extra=lambda cv: TW.cranes(cv, S, t, 0.6))
    her = np.array([-706, 1.7, hz], F32)
    x, y, z = cam.project(her[None]); hh = 0.235 * cam.fpx / z[0]
    HER.draw(cv.img, 'stand_back', float(x[0]), float(y[0]), hh, light_dir=(0, -1), rim=hexc('cfe2ee') * 0.3, backlit=0.9, emis=cv.emis, t=t, seed=9)
    return WD.compose(cv)

def sh_street_dark(t, W, H, u, p):
    """her street at night: the neighbours' windows go dark one by one, then hers, on "off"."""
    k = ease_io(u)
    cam = E.Cam(lv((-40, 11.0, -168), (-46, 10.0, -160), k), (-170, 1.0, -30), fov=44, W=W, H=H, drift=0.015, t=t, seed=29)
    t_off = Wd("I turn mine off", "off", 1)
    off = keys([(t_off + 0.1, 0.0), (p['_t1'] - 0.2, 0.92)], t, ease=lambda x: x)
    S = world(t, stars=0.5, win_off=off, tree_clear=20)
    mine = 1.0 - sstep(t_off - 0.04, t_off + 0.08, t)
    return valley(cam, S, t, extra=house_extra(S, t, porch=mine, win_up=mine, win_down=0.0))

def sh_bassbar(t, W, H, u, p):
    """both houses breathing at full, the camera drifting in."""
    k = ease_io(u)
    cam = E.Cam(lv((-640, 2.0, -70), (-650, 2.4, -40), k), (-860, 26, 250), fov=lerp(42, 36, k), W=W, H=H, drift=0.02, t=t, seed=31)
    S = world(t, stars=0.4, tree_clear=70)
    S['breath'] = min(1.0, S['breath'] * 1.2 + 0.1)
    return valley(cam, S, t)

# ---- BRIDGE
def sh_hall(t, W, H, u, p):
    """static, symmetrical. The only motion is the fluorescent hum."""
    fl = 0.5 + 0.5 * math.sin(t * 2 * math.pi * 1.7) * math.sin(t * 2 * math.pi * 0.37)
    cv = RM.draw_hall(W, H, dict(flicker=fl * 0.25, clock=19.7 + (t - 162.0) / 3600), t)
    return cv.img + cv.emis

# ---- FINAL / OUTRO
def sh_window_profile(t, W, H, u, p):
    """her in profile at the window, the room cold, the facility's light on the edge of her face."""
    cam = RM.bedroom_cam(W, H, u=-1.55, v=1.3, w=-1.2, tu=0.4, tv=1.45, fov=36, push=0.0, t=t)
    cv = RM.draw_bedroom(W, H, dict(lamp=0.0, window_light=1.0, blind_open=p.get('blind', 0.7), breath=breath(t)), t, cam=cam, her=False,
                         valley_S=world(t, stars=0.4))
    hp = RM.L2W(0.05, 1.72, -0.55)
    x, y, z = cam.project(hp[None]); hh = 0.235 * cam.fpx / z[0]
    wx, wy, _ = cam.project(RM.L2W(0.0, 1.45, 0.0)[None])
    HER.draw(cv.img, 'stand_profile', float(x[0]), float(y[0]), hh, light_dir=(float(wx[0] - x[0]), float(wy[0] - y[0])), rim=RM.WIN_COL * 0.6,
             backlit=0.4, emis=cv.emis, t=t, seed=13, wind=0.1)
    return cv.img + cv.emis

def sh_dry_river(t, W, H, u, p):
    """the river almost gone: cracked mud flats, one thin channel of water left, the houses across."""
    k = ease_io(u)
    x0 = p.get('x', -470.0); zc = float(WD.river_zc(x0))
    S = world(t, stars=0.45, tree_clear=40)
    S['water'] = h = p.get('water', -3.22); S['dry'] = 1.0
    cam = E.Cam(lv((x0 + 22, h + 2.6, zc - 12), (x0 + 16, h + 2.4, zc - 10), k), (x0 - 170, h + 6, zc + 150), fov=46, W=W, H=H, drift=0.02, t=t, seed=33)
    return valley(cam, S, t)

def sh_her_bed(t, W, H, u, p):
    """she stands out on the dry river bed, facing the two houses."""
    k = ease_io(u)
    x0 = -560.0; zc = float(WD.river_zc(x0))
    S = world(t, stars=0.45, tree_clear=40)
    S['water'] = h = -3.24; S['dry'] = 1.0
    cam = E.Cam(lv((x0 + 12, h + 1.5, zc - 16), (x0 + 11, h + 1.55, zc - 14), k), (x0 - 160, h + 22, zc + 280), fov=40, W=W, H=H, drift=0.015, t=t, seed=35)
    cv = WD.render(cam, S, t)
    her = np.array([x0 + 1.0, h + 1.7, zc - 5.5], F32)
    x, y, z = cam.project(her[None]); hh = 0.235 * cam.fpx / z[0]
    HER.draw(cv.img, 'stand_back', float(x[0]), float(y[0]), hh, light_dir=(0, -1), rim=hexc('cfe2ee') * 0.35, backlit=0.9, emis=cv.emis, t=t, seed=17)
    return WD.compose(cv)

def sh_profile_close(t, W, H, u, p):
    """close on her profile, rim-lit by the facility (it is out of focus behind her)."""
    k = ease_io(u)
    cam = E.Cam((-600, 2.2, -70), (-640, 20, 230), fov=30, W=W, H=H, drift=0.01, t=t, seed=37)
    S = world(t, stars=0.3, tree_clear=100)
    img = valley(cam, S, t)
    img = cv2.GaussianBlur(img, (0, 0), 9.0 * E.pxs(W, H)) * 1.2
    if H > W:   # 9:16: her profile centred, the head well below the top bar (and below the price)
        HER.draw(img, 'profile', W * (0.40 - 0.02 * k), H * 0.34, E.sref(W, H) * 0.30, light_dir=(1.0, -0.35), rim=hexc('ffd2a0') * 0.75 + hexc('cfe2ee') * 0.3, backlit=0.22, t=t, seed=21, wind=0.3)
    else:
        HER.draw(img, 'profile', W * (0.34 - 0.02 * k), H * 0.12, H * 0.32, light_dir=(1.0, -0.35), rim=hexc('ffd2a0') * 0.75 + hexc('cfe2ee') * 0.3, backlit=0.22, t=t, seed=21, wind=0.3)
    return img

def sh_aerial_blue(t, W, H, u, p):
    """above the town at night: one window turns blue, then the next, then all of them, on the beat."""
    k = ease_io(u)
    hx, hz = float(WD.HOUSE[0]), float(WD.HOUSE[2])
    cam = E.Cam(lv((hx + 150, 52, hz - 230), (hx + 130, 70, hz - 250), k), lv((hx - 160, 0, hz + 120), (hx - 190, 6, hz + 150), k), fov=46, W=W, H=H, drift=0.02, t=t, seed=39)
    i0 = int(np.searchsorted(BEATS, p['_t0'])); i = int(np.searchsorted(BEATS, t))
    steps = max(0, i - i0); frac = sstep(0, 0.12, (t - BEATS[max(0, i - 1)]))
    blue = clamp((steps - 1 + frac) / max(1, p.get('beats', 13)))
    S = world(t, stars=0.4, blue=blue * 1.02, tree_clear=0)
    return valley(cam, S, t, extra=house_extra(S, t, porch=0.0, win_up=0.0))

T_YOURS = Wd("And who's paying yours", "yours?")
def sh_lights_out(t, W, H, u, p):
    """on "yours?" the facility's lights go out row by row, until one small red point is left."""
    k = ease_io(u)
    cam = E.Cam(lv((-640, 2.2, -120), (-646, 2.2, -100), k), (-840, 26, 250), fov=40, W=W, H=H, drift=0.01, t=t, seed=41)
    out = clamp((t - (T_YOURS - 0.1)) / 1.1)
    S = world(t, stars=0.5 + 0.3 * out, blue=1.0, lights_out=out, plumes=1 - 0.7 * out, town_lights=1 - 0.8 * out, glow=1 - 0.9 * out,
              red_point=sstep(T_YOURS - 0.1, T_YOURS + 0.3, t), fog=1 - 0.4 * out, tree_clear=80)
    img = valley(cam, S, t)
    return img * (1 - 0.85 * sstep(T_YOURS + 1.2, SONG - 0.2, t))

def sh_end(t, W, H, u, p):
    """black, and the one red point."""
    img = np.zeros((H, W, 3), F32)
    gx, gy = (W * 0.72, H * 0.46) if W > H else (W * 0.62, H * 0.47)
    E.soft_glow(img, gx, gy, 2.0 * E.pxs(W, H), WD.RED_AV, 2.0 * (0.8 + 0.2 * math.sin(t * 1.6)))
    E.soft_glow(img, gx, gy, 9.0 * E.pxs(W, H), WD.RED_AV, 0.15)
    return img

# ================================================================ the timeline
def build_timeline():
    s = []
    def add(name, t0, t1, fn, **p): s.append(dict(name=name, t0=float(t0), t1=float(t1), fn=fn, p=p))
    # INTRO
    add('intro_awakening', 0.0, 14.55, sh_intro)
    add('intro_into_the_slit', 14.55, sec('V1')['s'], sh_intro_slit)
    # V1 (dusk)
    add('v1_ribbon_and_shovel', sec('V1')['s'], L("promised me the future") - 0.05, sh_ceremony)
    add('v1_a_thousand_jobs', L("promised me the future") - 0.05, L("Built a big gray house") - 0.05, sh_town_hill)
    add('v1_without_a_single_window', L("Built a big gray house") - 0.05, L("and you hum all night") - 0.05, sh_facade_track)
    add('v1_hum_all_night', L("and you hum all night") - 0.05, sec('PRE1')['s'], sh_house_night)
    # PRE1
    add('pre1_lights_247', sec('PRE1')['s'], L("I turn mine off") - 0.12, sh_lines)
    add('pre1_lamp_off', L("I turn mine off") - 0.12, T_NUMBER - 0.2, sh_bedroom, push=0.35)
    add('pre1_the_bill', T_NUMBER - 0.2, T_MINE + 0.62, sh_bill)
    add('pre1_dark', T_MINE + 0.62, T_CH[0], sh_black, gain=0.8)
    # the choruses share a skeleton; each pass escalates
    def chorus(n):
        tag = ['ch1', 'ch2', 'final'][n]
        t_drink = L("drinking up my river", n); t_thirst2 = L("You're so thirsty", 2 * n + 1 + (1 if n else 0)) if False else [l['s'] for l in LN if l['text'].startswith("You're so thirsty") and l['sec'] == ('CH1', 'CH2', 'FINAL')[n]][1]
        t_run = L("running up my light bill", n); t_five = L("Five dollars?", n); t_ten = L("Ten dollars?", n)
        t_25 = L("Twenty-five? Get your", n); t_cause = L("'cause you're drinking", n)
        t_water_end = Wd("'cause you're drinking", "and", n) - 0.15
        if n < 2:
            add(f'{tag}_breathing', T_CH[n], t_drink - 0.05, sh_across,
                **({} if n == 0 else dict(e0=(-700, 1.6, -60), e1=(-712, 1.55, -54), g0=(-860, 26, 250), g1=(-866, 27, 250), fov=40)))
            add(f'{tag}_drinking_the_river', t_drink - 0.05, t_thirst2 - 0.1, sh_river_close, drop=0.16 if n == 0 else 0.22, x=-520.0 if n == 0 else -600.0)
            add(f'{tag}_eyes', t_thirst2 - 0.1, t_run - 0.05, sh_fans, z0=1.3 if n == 0 else 2.0, z1=3.6 if n == 0 else 5.0, speed=0.42 if n == 0 else 0.7, rv=0.05 if n == 0 else -0.08)
            add(f'{tag}_light_bill', t_run - 0.05, t_five - 0.05, sh_lightbill, dim=0.75 if n == 0 else 1.0)
            add(f'{tag}_five', t_five - 0.05, t_ten - 0.05, sh_porch, zoom=(0.0, 0.08), racks=0 if n == 0 else 2)
            add(f'{tag}_ten', t_ten - 0.05, t_25 - 0.05, sh_porch, zoom=(0.15, 0.85), racks=0 if n == 0 else 2)
            add(f'{tag}_twenty_five', t_25 - 0.05, t_25 + 0.75, sh_price)
            add(f'{tag}_servers_out_my_yard', t_25 + 0.75, t_cause - 0.05, sh_yard, racks=2 if n == 0 else 8, fov=50 if n == 0 else 56)
            if n == 0: add(f'{tag}_drinking_my_water', t_cause - 0.05, t_water_end, sh_glass)
            else: add(f'{tag}_drinking_my_water', t_cause - 0.05, t_water_end, sh_pipe, flow=0.6)
            t_card_end = sec('POST1')['s'] if n == 0 else 161.24
            add(f'{tag}_charging_my_card', t_water_end, t_card_end, sh_meter, rate=(0.6, 4.0) if n == 0 else (1.5, 9.0), t_break=72.93 if n == 0 else 159.43)
        else:
            add('final_window', 177.25, t_drink - 0.04, sh_window_profile)
            add('final_dry_river', t_drink - 0.04, t_thirst2 - 0.05, sh_dry_river)
            add('final_on_the_bed', t_thirst2 - 0.05, 184.69, sh_her_bed)
            add('final_eyes', 184.69, t_run - 0.04, sh_fans, z0=5.5, z1=7.5, speed=0.9, red=1.0, rv=0.12)
            add('final_surge', t_run - 0.04, 188.27, sh_lines, tower=6, fov=50, surge=1.6, hum=2.0)
            add('final_out_of_sight', 188.27, t_five - 0.05, sh_bassbar)
            t_baby = Wd("Five dollars?", "Baby,", 2) - 0.05; t_mm = Wd("Ten dollars?", "Mm,", 2) - 0.05
            add('final_five', t_five - 0.05, t_baby, sh_porch, zoom=(0.1, 0.2), racks=12)
            add('final_baby_you_can_stay', t_baby, t_ten - 0.05, sh_profile_close)
            add('final_ten', t_ten - 0.05, t_mm, sh_porch, zoom=(0.5, 1.0), racks=12)
            add('final_okay_okay', t_mm, t_25 - 0.05, sh_dry_river, x=-650.0, water=-3.26)
            add('final_twenty_five', t_25 - 0.05, t_25 + 0.85, sh_price)
            add('final_servers_out_my_yard', t_25 + 0.85, t_cause - 0.05, sh_yard, racks=33, fov=60, t_red=Wd("Twenty-five? Get your", "yard,", 2))
            add('final_drinking_my_water', t_cause - 0.05, t_water_end, sh_pipe, flow=1.0)
            add('final_charging_my_card', t_water_end, 204.47, sh_meter, rate=(3.0, 16.0), t_break=202.66)
            add('final_full_breath', 204.47, sec('OUTRO')['s'], sh_bassbar)
    chorus(0)
    # POST1
    add('post1_the_eyes', sec('POST1')['s'], L("Always wanting more") - 0.05, sh_fans, z0=1.0, z1=1.35, rv=0.035, speed=0.38)
    add('post1_wanting_more', L("Always wanting more") - 0.05, L("Thirsty... (thirsty)", 1) - 0.05, sh_fans, z0=1.35, z1=6.5, rv=0.06, speed=0.38)
    add('post1_the_puddle', L("Thirsty... (thirsty)", 1) - 0.05, L("What you asking for") - 0.05, sh_fans, z0=2.4, z1=2.6, ripple=0.9, rv=0.02, cx=0.5, cy=0.5)
    add('post1_what_you_asking_for', L("What you asking for") - 0.05, L("Okay, I'll give you") - 0.06, sh_plume_black)
    # V2 (a summer dusk)
    add('v2_the_school_roof', L("Okay, I'll give you") - 0.06, L("paid your taxes early") - 0.05, sh_school)
    add('v2_taxes_early', L("paid your taxes early") - 0.05, L("He watches your front gate") - 0.05, sh_town_dusk)
    add('v2_the_booth', L("He watches your front gate") - 0.05, L("thinks you're not so bad") - 0.05, sh_booth)
    add('v2_not_so_bad', L("thinks you're not so bad") - 0.05, L("But the creek's running low") - 0.05, sh_booth_close)
    add('v2_the_creek', L("But the creek's running low") - 0.05, L("and the hum's in my sleep") - 0.05, sh_creek)
    add('v2_the_hum', L("and the hum's in my sleep") - 0.05, L("And you're asking for a second") - 0.05, sh_bed_hum)
    add('v2_second_house', L("And you're asking for a second") - 0.05, L("like you've never heard") - 0.05, sh_second)
    add('v2_never_heard_no', L("like you've never heard") - 0.05, sec('PRE2')['s'], sh_two)
    # PRE2
    add('pre2_lights_247', sec('PRE2')['s'], L("I turn mine off", 1) - 0.12, sh_lines, tower=3, fov=56, surge=1.4)
    add('pre2_lamp_off', L("I turn mine off", 1) - 0.12, T_NUMBER2 - 0.2, sh_bedroom, t_off=Wd("I turn mine off", "off", 1), cam=(-1.55, 1.2, -2.1, 0.25, 1.32, 46), push=0.25)
    add('pre2_the_bill', T_NUMBER2 - 0.2, T_MINE2 + 0.5, sh_bill2)
    add('pre2_dark', T_MINE2 + 0.5, T_CH[1], sh_black, gain=0.85)
    chorus(1)
    add('ch2_bass_bar', 161.24, L("Public comment") - 0.04, sh_bassbar)
    add('bridge_public_comment', L("Public comment") - 0.04, 177.25, sh_hall)     # holds through the question
    chorus(2)
    # OUTRO
    add('outro_whats_your_number', sec('OUTRO')['s'], Wd("Five? Ten?", "Five?") - 0.2, sh_window_profile, blind=0.8)
    add('outro_five', Wd("Five? Ten?", "Five?") - 0.2, Wd("Five? Ten?", "Ten?") - 0.15, sh_price)
    add('outro_ten', Wd("Five? Ten?", "Ten?") - 0.15, L("Twenty-five?", 3) - 0.1, sh_price)
    add('outro_twenty_five', L("Twenty-five?", 3) - 0.1, 212.11, sh_price)
    add('outro_the_blue', 212.11, L("And who's paying yours") - 0.2, sh_aerial_blue, beats=13)
    add('outro_whos_paying_yours', L("And who's paying yours") - 0.2, SONG, sh_lights_out)
    add('end_card', SONG, DUR + 1, sh_end)
    s.sort(key=lambda d: d['t0'])
    for a, b in zip(s, s[1:]): a['t1'] = b['t0']           # no gaps, no overlaps
    return s

TIMELINE = build_timeline()
_T0 = np.array([d['t0'] for d in TIMELINE])

def shot_at(t):
    i = int(np.searchsorted(_T0, t, side='right')) - 1
    return TIMELINE[max(0, min(i, len(TIMELINE) - 1))]

# ---------------------------------------------------------------- in-picture typography
def ghost_events():
    ev = []
    for l in LN:
        ws = [(w, tt) for w, tt in zip(l['words'], l['wt']) if 'thirsty' in w.lower()]
        if not ws: continue
        main = [tt for w, tt in ws if not w.startswith('(')]
        ech = [tt for w, tt in ws if w.startswith('(')]
        if l['sec'] == 'INTRO' and main and main[0] > 9: ech = list(ECHO)
        if main: ev.append(dict(t=main[0], echoes=ech, sec=l['sec']))
        elif ech: ev.append(dict(t=ech[0], echoes=[], sec=l['sec']))
    return ev
GHOSTS = [g for g in ghost_events() if g['t'] > 6.5]          # the first "Thirsty..." is the title card itself
# where "thirsty" floats (x, y of the first word as frame fractions, size px at 1080, x step per echo). A ghost belongs
# to the shot it starts in and carries across the following cuts until it has faded (its echoes land in the next shot).
GHOST_POS = {'intro_awakening': (0.30, 0.20, 215, 0.045, 0.21), 'ch1_breathing': (0.30, 0.25, 230, 0.03, 0.20), 'ch1_eyes': (0.5, 0.40, 260, 0.0, 0.30),
             'ch2_breathing': (0.70, 0.22, 240, -0.03, 0.20), 'ch2_eyes': (0.5, 0.40, 280, 0.0, 0.30), 'post1_the_eyes': (0.5, 0.40, 250, 0.0, 0.30),
             'post1_the_puddle': (0.5, 0.42, 250, 0.0, 0.30), 'final_on_the_bed': (0.5, 0.20, 250, 0.0, 0.19),
             'bridge_public_comment': (0.5, 0.30, 220, 0.0, 0.22)}   # (x, y, size, x step per echo, 9:16 y)
def _ghost_home():
    out = []
    for g in GHOSTS:
        d = shot_at(g['t'] - 0.02)
        if d['name'] in GHOST_POS: out.append((g, GHOST_POS[d['name']]))
    return out
GHOST_PLAN = []

def _prices():
    out = []
    ivory = hexc('ece2cb') * 0.85; crimson = hexc('c8102e') * 1.6; pink = hexc('ff3d8b') * 1.4
    for n, (s5, s10, s25) in enumerate(((120, 190, 430), (160, 260, 560), (210, 340, 700))):
        t5 = Wd("Five dollars?", "Five", n); t10 = Wd("Ten dollars?", "Ten", n); t25 = Wd("Twenty-five? Get your", "Twenty-five?", n)
        out.append((t5 - 0.06, "$5", 0.80, 0.30, s5, ivory, 0, False, (t10 - 0.1) - (t5 - 0.06)))
        out.append((t10 - 0.06, "$10", 0.78, 0.30, s10, ivory * 1.1, 1, False, (t25 - 0.1) - (t10 - 0.06)))
        out.append((t25 - 0.05, "$25", 0.5, 0.48, s25, crimson if n < 2 else pink, 2 + n, True, 0.85 if n < 2 else 0.95))
    t5 = Wd("Five? Ten?", "Five?"); t10 = Wd("Five? Ten?", "Ten?"); t25 = L("Twenty-five?", 3)
    out.append((t5 - 0.1, "$5", 0.5, 0.48, 150, ivory, 0, False, (t10 - 0.15) - (t5 - 0.1)))
    out.append((t10 - 0.1, "$10", 0.5, 0.48, 150, ivory, 0, False, (t25 - 0.1) - (t10 - 0.1)))
    out.append((t25 - 0.08, "$25", 0.5, 0.48, 150, crimson * 0.8, 0, False, 212.11 - (t25 - 0.08)))
    return out
PRICES = _prices()
TITLE_UNTIL = 6.2

def _yard_rows():
    """GET YOUR SERVERS / OUT MY YARD. on the sung words, for each chorus."""
    out = []
    for n in range(3):
        t_ = lambda w: Wd("Twenty-five? Get your", w, n)
        c2 = hexc('c8102e') * 1.5
        rows = [(0.34, 112, hexc('ece2cb') * 0.85, [("GET", t_("Get")), ("YOUR", t_("your")), ("SERVERS", t_("servers"))]),
                (0.62, 190, c2, [("OUT", t_("out")), ("MY", t_("my")), ("YARD.", t_("yard,"))])]
        out.append((('ch1', 'ch2', 'final')[n] + '_servers_out_my_yard', rows))
    return dict(out)
YARD_TYPE = _yard_rows()

def _yard_rows_v():
    """9:16: GET YOUR / SERVERS / OUT MY / YARD. stacked and centred inside the phone-safe frame."""
    out = {}
    for name, rows in YARD_TYPE.items():
        (y1, s1, c1, w1), (y2, s2, c2, w2) = rows
        out[name] = [(0.250, 120, c1, w1[:2]), (0.318, 140, c1, w1[2:]), (0.430, 196, c2, w2[:2]), (0.528, 196, c2, w2[2:])]
    return out
YARD_TYPE_V = _yard_rows_v()
VX_C = 0.45                                                # 9:16: type centred left of the like/share column

def tscale(W, H):
    """in-picture type scale: the 16:9 band's H / 1080, or the same pixel size on a 9:16 frame."""
    return H / 1080 if W > H else W / 1080 * E.V_SCALE

def overlays_linear(img, t, d):
    if C.STATE["clean"]: return
    H, W = img.shape[:2]; vert = H > W; ts = tscale(W, H)
    if not GHOST_PLAN: GHOST_PLAN.extend(_ghost_home())
    for g, gp in GHOST_PLAN:
        if g['t'] - 0.3 <= t <= (g['echoes'][-1] if g['echoes'] else g['t']) + 3.0:
            if vert: TY.ghost(img, t, g['t'], VX_C, gp[4], gp[2] * 0.92, echoes=g['echoes'], life=2.4 + 0.25 * len(g['echoes']), step_x=0.0, ts=ts)
            else: TY.ghost(img, t, g['t'], gp[0], gp[1], gp[2], echoes=g['echoes'], life=2.4 + 0.25 * len(g['echoes']), step_x=gp[3])
    if d['name'] in YARD_TYPE:
        if vert: TY.kinetic(img, t, YARD_TYPE_V[d['name']], x=VX_C, t_out=d['t1'] + 0.02, ts=ts, center=True)
        else: TY.kinetic(img, t, YARD_TYPE[d['name']], x=0.065, t_out=d['t1'] + 0.02)
    for (t0, lab, x, y, sz, col, wgt, slam, life) in PRICES:
        if t0 - 0.1 <= t <= t0 + life + 0.1:
            if vert:   # centred, above the lyrics; never wider than the safe width
                yv = 0.40 if (lab == "$25" or t0 > sec('OUTRO')['s'] - 1) else 0.21
                TY.price(img, t, t0, lab, VX_C, yv, sz, col, weight=wgt, slam=slam, life=life, ts=ts, maxw=0.60)
            else: TY.price(img, t, t0, lab, x, y, sz, col, weight=wgt, slam=slam, life=life)

def title_linear(img, t):
    # frame 0 is the cover: THIRSTY top left with the pink drips running on "Thirsty..." (9:16: centred, below the top bar)
    if t < TITLE_UNTIL + 0.5:
        H, W = img.shape[:2]
        op = 1 - sstep(TITLE_UNTIL - 1.2, TITLE_UNTIL, t)
        drip = 0.12 + 0.88 * ease_io(clamp((t - 2.6) / 3.0))
        if H > W: TY.title(img, t, VX_C, 0.155, size=196, op=op, drip=drip, ts=tscale(W, H), center=True)
        else: TY.title(img, t, 0.035, 0.045, size=300, op=op, drip=drip)

def overlays_display(full, t, d, W, H, bh):
    if C.STATE["clean"]: return
    vert = H > W
    if vert:
        sv = subs_for(W, H)
        if t < T_END: sv.scrim(full)
        sv.draw(full, t, filt=_sub_filter)
        if t < TITLE_UNTIL + 0.5:
            op = 1 - sstep(TITLE_UNTIL - 1.2, TITLE_UNTIL, t)
            TY.brand(full, VX_C, 0.60, 34, op, ts=W / 1080, center=True)   # low, clear of the drips (16:9 has it in the bottom bar)
    else:
        subs_for(W, H).draw(full, t, filt=_sub_filter)
    bar = (H - bh) // 2
    if t < TITLE_UNTIL + 0.5 and not vert:
        op = 1 - sstep(TITLE_UNTIL - 1.2, TITLE_UNTIL, t)
        TY.brand(full, 0.035, (H - bar * 0.62) / H, 34, op)
    C.subscribe_pill(full, t, W, H, sec('POST1')['s'] + 0.4, 5.0)
    C.end_screen(full, t, W, H, T_END, DUR - T_END, "Who's paying yours?", sub_line="Subscribe for a new song every week",
                 title=None, accent=np.array([0.70, 0.13, 0.23], F32))
    if t >= T_END:
        end_title(full, t, W, H)
        if vert: TY.brand(full, 0.5, 0.668, 30, sstep(T_END + 0.3, T_END + 1.2, t) * 0.95, ts=W / 1080, center=True)
        else: TY.brand(full, 0.07, 0.858, 30, sstep(T_END + 0.3, T_END + 1.2, t) * 0.95)

END_TITLE = ("Thirsty", "(The Data Center Next Door)")      # the release title, on two lines (the end card's title slot)
def end_title(full, t, W, H):
    """the end card's song title in the studio's style (mono, crimson, tracked), split title / parenthetical so it
    stays in the left column on 16:9 (the right half is YouTube's) and left of the buttons on 9:16."""
    e = sstep(T_END, T_END + 0.8, t) * 0.95
    if e <= 0 or C.STATE["clean"]: return
    vert = H > W; ts = min(W, H) / 1080; acc = np.array([0.70, 0.13, 0.23], F32); f = C.TH('mono', C.F_MONOB)
    fit = W * (0.56 if vert else 0.40)
    def fitted(s, fs, tr):
        while C.text_w(s, f, fs) + len(s) * tr > fit and fs > 18 * ts: fs -= 1
        return fs
    a, b = END_TITLE[0].upper(), END_TITLE[1].upper()
    f1 = fitted(a, int((40 if vert else 36) * ts), 8 * ts); f2 = fitted(b, int(f1 * 0.62), 5 * ts)
    s1 = C.sprite(a, f, f1, track=int(8 * ts)); s2 = C.sprite(b, f, f2, track=int(5 * ts))
    if vert:
        C.blit(full, s1, W / 2, H * 0.600, acc, e, anchor='c'); C.blit(full, s2, W / 2, H * 0.600 + f1 * 1.15, acc * 0.92, e, anchor='c')
    else:
        x = W * 0.07; y = H * 0.770
        C.blit(full, s1, x, y, acc, e); C.blit(full, s2, x, y + f1 * 1.35, acc * 0.92, e)

def _sub_filter(Ln):
    """the intro is the title card; the "$25 / GET YOUR SERVERS OUT MY YARD." moment is its own big type."""
    if Ln['sec'] == 'INTRO': return False
    if Ln['sec'] in ('CH1', 'CH2', 'FINAL') and ('servers' in Ln['text'] or Ln['text'].startswith('Twenty-five')): return False
    return True

_SUBS = {}
def subs_for(W, H):
    if (W, H) not in _SUBS: _SUBS[(W, H)] = TY.Subs(LN, W, H, E.band_height(W, H)) if W > H else TY.SubsV(LN, W, H)
    return _SUBS[(W, H)]

# ---------------------------------------------------------------- frame
SCALE = float(os.environ.get("YS_SCALE", "1.0"))          # < 1: render the picture smaller and upscale (previews)

def picture(t, W, H):
    d = shot_at(t)
    u = clamp((t - d['t0']) / max(1e-3, d['t1'] - d['t0']))
    p = dict(d['p']); p['_t0'] = d['t0']; p['_t1'] = d['t1']
    # 9:16 shows the middle 56 % of the 16:9 picture; VC (where in the 16:9 width the 9:16 frame is centred) slides it
    vc = VC.get(d['name'], 0.5) if H > W else 0.5
    E.VSHIFT[0] = -(vc - 0.5) * 1920 / 1080 if H > W else 0.0
    E.VSHIFT[1] = VCY.get(d['name'], 0.0) if H > W else 0.0
    return d['fn'](t, W, H, u, p), d

VC = {'ch1_five': 0.24, 'ch1_ten': 0.22, 'ch2_five': 0.24, 'ch2_ten': 0.22, 'final_five': 0.24, 'final_ten': 0.22,
      'pre1_the_bill': 0.51, 'pre2_the_bill': 0.51, 'v2_not_so_bad': 0.62, 'pre2_lamp_off': 0.70,
      'final_window': 0.58, 'outro_whats_your_number': 0.58}   # 16:9 x of each shot's subject (9:16 framing)
# 9:16 only: lift the picture (fraction of the frame height) so a figure stands above the lyrics instead of behind them
VCY = {'v2_not_so_bad': 0.17, 'v2_the_booth': 0.07, 'pre1_the_bill': 0.13, 'pre2_the_bill': 0.13}

def render_frame(t, W=1920, H=1080, fi=0):
    bh = E.band_height(W, H) if W > H else H
    k = SCALE
    if k < 0.999:
        w2, h2 = int(round(W * k / 2) * 2), int(round(bh * k / 2) * 2)
        img, d = picture(t, w2, h2)
        img = cv2.resize(img, (W, bh), interpolation=cv2.INTER_LINEAR)
    else:
        img, d = picture(t, W, bh)
    img = np.maximum(img, 0)
    overlays_linear(img, t, d)
    title_linear(img, t)
    out = E.develop(img, fi)
    full = E.letterbox(out, H, bh) if bh < H else out
    overlays_display(full, t, d, W, H, bh)
    full *= (1 - sstep(DUR - 1.0, DUR - 0.05, t))
    return (np.clip(full, 0, 1) * 255 + 0.5).astype(np.uint8)

def dump_timeline():
    out = [dict(name=d['name'], start=round(d['t0'], 3), end=round(d['t1'], 3), shot=d['fn'].__name__,
                params={k: (v if not isinstance(v, np.ndarray) else v.tolist()) for k, v in d['p'].items() if not callable(v)}) for d in TIMELINE]
    json.dump(dict(duration=DUR, song=SONG, bar=BAR, end_card=T_END, shots=out, ghosts=GHOSTS,
                   prices=[dict(t=round(p[0], 3), label=p[1]) for p in PRICES]), open(os.path.join(HERE, "build", "timeline.json"), "w"), indent=1)

if __name__ == "__main__":
    dump_timeline()
    for d in TIMELINE: print(f"{d['t0']:7.2f} {d['t1']:7.2f}  {d['t1'] - d['t0']:5.2f}s  {d['name']}")
