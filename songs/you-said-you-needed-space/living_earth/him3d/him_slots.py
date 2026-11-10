"""him_slots.py: the 3D "him" in the film's hero beats (earth_him_wire, Nov 9). One RUN = one continuous piece of acting.
  Blender -b him.blend --python him_slots.py -- <run> <169|916> <out dir> [meta=1] [stills=f,f,...] [pct=50] [samples=48] [mb=1] [first=f] [last=f]
Reads build/him_wire/tracks/<run>.json (his spark per frame under the engine's real camera: living_earth/him3d/him_export.sh),
so he is rendered where the engine draws him, in the engine's frame numbers (file him_<film frame>.png, RGBA 16 bit).
Per frame: place + pose + light are pure functions of the film frame (act_* below). For motion blur the transforms of every
rig object are baked as linear keys on the integer frames (so Eevee can sample between them); lights and emission are set
per frame. <out dir>/meta.json: per frame alpha (the post step fades him with it), centre px, span px, heat.
"""
import bpy, json, math, os, sys
from mathutils import Matrix, Vector, Quaternion
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import him_render as HR
from him_render import R, clamp01, smooth, lerp, move, nz, settle, spring_at, merged, SPAN

SONG = os.path.dirname(os.path.dirname(HERE))
RES = {'169': (2560, 1440), '916': (1080, 1920)}
FPS = 30.0

# ----------------------------------------------------------------------------- the track
class Track:
    def __init__(self, run, fmt):
        d = json.load(open(os.path.join(SONG, 'build/him_wire/tracks', run + '.json')))
        self.run, self.fmt, self.f0, self.f1, self.t0, self.t1 = run, fmt, d['f0'], d['f1'], d['t0'], d['t1']
        self.slots = {s: (a, b) for s, a, b in d['slotFrames']}; self.last_slot_frame = d['slotFrames'][-1][2]
        self.rows = {r['f']: r for r in d[fmt]['frames']}; self.W, self.H = RES[fmt]
        self.have = sorted(r['f'] for r in d[fmt]['frames'] if r.get('x') is not None)
        # MEASURED on the rendered film (him_cutcheck.py "cuts seen"): finalChorus.ts cuts into fc_hold on a frame-quantised time, one frame
        # before the slot index changes, and its hand-over is not byte-identical, so the exporter's `shot` flag misses that one frame.
        for a_, b_ in {'fc_hold': [(5654, 5722)]}.get(run, []):
            for g in range(a_, b_ + 1):
                if g in self.rows: self.rows[g]['shot'] = True
    def row(self, f):
        """the row at film frame f. Where the builder draws no spark of his: the nearest frame that has one, intensity 0; before the
        first one (a cut-in: the sections drop sparks for the 0.45 s after a cut) his place is carried back along his own motion."""
        r = self.rows.get(int(f))
        if r is not None and r.get('x') is not None: return r
        if not self.have: return None
        near = min(self.have, key=lambda g: abs(g - f)); o = dict(self.rows[near]); o['int'] = 0.0; o['w'] = (r or {}).get('w', 0.0) or 0.0; o['held'] = True
        if f < self.have[0] and len(self.have) > 1 and self.have[0] - f <= 20:
            a, b = self.rows[self.have[0]], self.rows[self.have[1]]; n = self.have[0] - f
            o['px'] = [a['px'][0] - (b['px'][0] - a['px'][0]) * n, a['px'][1] - (b['px'][1] - a['px'][1]) * n]
        o['shot'] = bool((r or {}).get('shot', False))
        if r is not None:
            o['her'], o['sun'] = r['her'], r['sun']
            if r.get('bt'): o['bt'] = r['bt']
        return o
    def units(self, v):   # engine screen units -> px of this format (a length)
        return v * self.H / 2.0

def heat_of(row):   # his spark's colour: warm white (g 0.72) .. red (g 0.18)
    return clamp01((0.72 - row['col'][1]) / 0.54) if row and row.get('col') else 0.0

def my_idle(t, P, wings=1.0, body=1.0):
    """alive is never static (as HR.idle), with gains: the bridge holds him inside the outline her lights drew"""
    P['dz'] += body * 0.018 * math.sin(t * 6.283 / 4.5); P['lean'] += body * 1.2 * math.sin(t * 6.283 / 4.5 + 0.8)
    for i, nm in enumerate(('L', 'R')):
        w = P['wing' + nm]; w['flap'] += wings * 1.8 * nz(t, 3 + 5 * i); w['twist'] += wings * 2.0 * nz(t, 11 + 5 * i, 0.17)
        w['fold'] = tuple(f + wings * 1.5 * nz(t - 0.12 * j, 20 + 7 * i + j, 0.3) for j, f in enumerate(w['fold']))
    P['dish_az'] += body * 4 * nz(t, 40, 0.15); P['dish_el'] += body * 2.5 * nz(t, 41, 0.2)
    P['head_roll'] += 1.2 * nz(t, 50, 0.2)
    sx = 0.012 * round(1.5 * nz(t, 60, 0.45)); P['pupil'] = (P['pupil'][0] + sx, P['pupil'][1])
    ph = (t % 1.3) / 1.3; P['beacon'] *= 0.12 + 1.6 * math.exp(-((ph - 0.08) / 0.05) ** 2)
    return P

def blink(t, t0, d=0.16):   # a quick shutter blink at t0: 0 .. 1 .. 0
    u = (t - t0) / d; return math.sin(clamp01(u) * math.pi) ** 2 if 0 < u < 1 else 0.0
def tremble(t, amp):        # overheating shake: two fast sines (a pure function of time)
    return amp * (0.6 * math.sin(t * 61.0) + 0.4 * math.sin(t * 97.0 + 1.3))
def kick(t, t0):
    """a released spring: 0 before t0, jumps toward 1 with a damped overshoot (the thread lets go, the link snaps)"""
    return settle((t - t0) * 1.4, 5.0, 11.0) if t > t0 else 0.0
def mixv(a, b, k):
    if isinstance(a, dict): return {q: mixv(a[q], b[q], k) for q in a}
    if isinstance(a, (tuple, list)): return tuple(mixv(x, y, k) for x, y in zip(a, b))
    return a + (b - a) * k

# ----------------------------------------------------------------------------- the beats. Each returns a state dict:
#   P (pose incl. yaw/pitch/roll), span (px in this format), off (px, y down), alpha, heat, power, light{...}, rocket{...}?
def base_state(tr, f):
    row = tr.row(f)
    return dict(row=row, P=merged(None), off=(0.0, 0.0), alpha=1.0, w=float(row.get('w', 0.0) or 0.0), heat=heat_of(row), power=1.0, span=600.0, d=14.0,
                light=dict(sun=(0.6, 0.35, 0.55), sun_energy=8.0, earth=(0.2, -1, 0.1), earth_energy=0.7, her_world=0.3, exposure=0.5, lamps=1.0))

def act_co_count(tr, f):
    """0:04-0:08 the open: his rocket leaves her (one continuous shot: coldOpen.ts). The camera falls back faster than he climbs;
    at 0:06 he passes close to us (the rocket fills a quarter of the frame), then dwindles to the spark he is in co_space. He rides on
    top, wings folded, looking ahead; one look back at her as he passes; then ahead again. He grows out of the spark and shrinks
    back into it (no cut here, so the swap is hidden in his size)."""
    S = base_state(tr, f); t = f / FPS; row = S['row']; wide = tr.fmt == '169'; P = S['P']
    pk = smooth(3.9, 5.75, t) * (1 - smooth(6.15, 7.75, t))
    L = math.exp(lerp(math.log(64.0), math.log(640.0 if wide else 470.0), pk))
    hx, hy = row['x'] - row['her'][0], row['y'] - row['her'][1]; th = math.degrees(math.atan2(hy, hx))      # he flies straight away from her
    S['rocket'] = dict(len_px=L, d=40, yaw=18 + 26 * (t - 5.9), pitch=lerp(26, -20, smooth(4.5, 7.2, t)), roll=th - 90 + 3 * nz(t, 5, 0.4),
                       flame_len=0.42 * (1 + 0.10 * math.sin(t * 43) + 0.07 * math.sin(t * 71 + 1)), flame_light=900 * (1 + 0.15 * math.sin(t * 43)))
    cr = math.cos(R(th)); sr = math.sin(R(th)); S['off'] = (-cr * L * 0.52 * pk, sr * L * 0.52 * pk)   # at the pass he is held by his middle: the nose (and him on it) stays in frame; the engine's trail lies on the same axis
    for nm in ('L', 'R'): P['wing' + nm] = dict(twist=0.0, flap=10.0 + 1.5 * nz(t, 3, 0.8), fold=(58.0, -116.0, 110.0))
    look = move(t, 5.55, 0.28, ant=0.18, amt=0.2) * (1 - smooth(6.35, 6.7, t))                               # the look back
    P['head_pan'] = lerp(-12, 118, look); P['head_tilt'] = lerp(-16, 12, look); P['brow_tilt'] = lerp(-12, 6, look); P['lid'] = 0.45 * look
    P['pupil_size'] = lerp(1.1, 0.9, look); P['dish_az'] = 40 + 30 * look; P['dish_el'] = 25
    lag = spring_at(t, lambda s: move(s, 5.55, 0.28, 0.18, 0.2), 70.0, 5.0) - move(t, 5.55, 0.28, 0.18, 0.2)
    P['whip'] = (-18 + 8 * nz(t, 70, 1.2), 6 + 30 * lag + 6 * nz(t, 71, 1.4))                                # the aerial streams back in the climb
    P['leds'] = tuple(0.5 + 1.2 * math.exp(-(((t - 0.11 * j) % 0.9) / 0.1) ** 2) for j in range(3))
    sx, sy, sz = row['sun']; n = math.hypot(sx, sy) or 1.0
    S['light'] = dict(sun=(sx / n * 0.8, sy / n * 0.8, 0.6), sun_energy=9.0, earth=(-hx, -hy, 0.05), earth_energy=0.6, her_world=0.22, exposure=0.5, lamps=1.0)
    S['alpha'] = smooth(3.76, 4.25, t) * (1 - smooth(7.25, 7.74, t))
    return S

def act_c1_chase(tr, f):
    """"Go on, chase the sun all day / Go on, disappear": he runs her limb a step behind the sunrise (cut in, cut out). He starts with
    an eye still on her; on "chase" the take: head snaps to the sun, wings sweep back, he leans into it. Through "disappear" the glare
    takes him: the lid comes down, he whites out (alpha = the builder's own fade into the glare)."""
    S = base_state(tr, f); t = f / FPS; row = S['row']; wide = tr.fmt == '169'; P = S['P']
    S['span'] = 860.0 if wide else 540.0; S['off'] = (0.0, -tr.units(0.205 if wide else 0.17))
    go = move(t, 55.50, 0.26, ant=0.2, amt=0.22)                                   # "chase"
    P['yaw'] = lerp(24, 52, go); P['pitch'] = 5 + 2 * math.sin(t * 2.2); P['roll'] = lerp(-3, -15, go) + 2.0 * nz(t, 2, 0.5)
    P['lean'] = lerp(0, -7, go)
    P['head_pan'] = lerp(-58, -12, go); P['head_tilt'] = lerp(16, -9, go); P['brow_tilt'] = lerp(6, -15, move(t, 55.54, 0.2, ant=0.1, amt=0.5))
    P['pupil_size'] = lerp(0.9, 1.22, smooth(55.5, 55.8, t))
    for i, nm in enumerate(('L', 'R')):
        w = P['wing' + nm]; s = move(t, 55.56 + 0.05 * i, 0.3, ant=0.22, amt=0.5)
        w['twist'] = lerp(26, -15, s); w['flap'] = lerp(5, 11 + 3 * i, s) + 2.2 * math.sin(t * 11 + i) * go      # effort: a fast flutter (at rest the panels are feathered off the sun: flat to it they mirror it and go white)
        w['fold'] = tuple(lerp(fo, -9 - 2 * j, move(t, 55.56 + 0.05 * i + 0.06 * j, 0.3, ant=0.22, amt=0.8)) for j, fo in enumerate(w['fold']))
    P['dz'] += 0.03 * math.sin(t * 9.5) * go
    P['dish_az'] = lerp(60, -95, move(t, 55.62, 0.34, ant=0.2, amt=0.15)); P['dish_el'] = lerp(35, 62, go)
    P['leds'] = tuple(0.5 + 1.4 * math.exp(-(((t - 55.5 - 0.1 * j) % 0.6) / 0.09) ** 2) for j in range(3))
    drive = lambda s: move(s, 55.50, 0.26, 0.2, 0.22)
    lag = spring_at(t, drive, 70.0, 5.0) - drive(t); P['whip'] = (-14 * go + 12 * lag + 2 * nz(t, 70), 10 * go + 24 * lag + 3 * nz(t, 71, 0.9))
    gl = smooth(57.2, 58.3, t)                                                     # the glare: squint, then gone
    P['lid'] = 0.75 * gl; P['brow_tilt'] += 20 * gl; P['pupil_size'] *= lerp(1, 0.7, gl); P['head_tilt'] += 6 * gl
    S['alpha'] = clamp01(row['int'] / 1.5)
    S['light'] = dict(sun=(0.80, -0.30, 0.52), sun_energy=lerp(7.5, 15.0, gl), earth=(0.1, -1, 0.25), earth_energy=0.9, her_world=0.34, exposure=lerp(0.5, 1.5, gl), lamps=1.0)
    return S

def act_c1_heat(tr, f):
    """"Who's gonna cool you down up there? / You've got no atmosphere" (cut in at 59.28, cut out at 64.40; chorus1.ts: he floats between
    her and the star thermometer, which bursts on "atmosphere" and knocks him back). Smug at first; his chest lights go amber one by one,
    he looks down at them; he shakes, pulls his wings over his head for shade, glows red; on "atmosphere" he blows a fuse: knocked back,
    wings flung, the eye stutters, and he hangs there limp and red."""
    S = base_state(tr, f); t = f / FPS; row = S['row']; wide = tr.fmt == '169'; P = S['P']
    T_ATMO = 62.56
    limp = smooth(T_ATMO + 0.1, T_ATMO + 0.7, t); hit = kick(t, T_ATMO)
    punch = smooth(T_ATMO - 0.32, T_ATMO + 0.08, t)
    S['span'] = (590.0 if wide else 430.0) * (1 - 0.07 * limp) * (1 + (0.24 if wide else 0.15) * punch)
    h = max(S['heat'], smooth(59.8, 62.5, t)) if not row.get('held') else smooth(59.8, 62.5, t); S['heat'] = h; hh = h * h
    P['yaw'] = -26 + 4 * nz(t, 1, 0.2) + 34 * limp; P['pitch'] = 4 - 10 * limp; P['roll'] = 3 + tremble(t, 2.6 * hh) * (1 - limp) + 30 * (hit - 0.55 * limp)
    S['off'] = (tremble(t + 3.1, 5.0 * hh) * (1 - limp), tremble(t + 7.7, 4.0 * hh) * (1 - limp))
    worry = move(t, 60.05, 0.26, ant=0.16, amt=0.2)                                # "cool you down": he looks at his own chest lights
    P['head_pan'] = lerp(14, 4, worry); P['head_tilt'] = lerp(-6, 24, worry) * (1 - smooth(61.2, 61.5, t)) + 26 * limp; P['head_roll'] = lerp(8, 0, worry) + 14 * limp
    P['brow_tilt'] = lerp(16, -16, worry) + 30 * limp; P['brow_roll'] = lerp(10, 0, worry); P['lid'] = lerp(0.35, 0.0, worry)
    dart = math.sin(clamp01((t - 61.3) / 1.2) * math.pi * 3)                       # then looks for shade: left, right, left
    P['head_pan'] += 34 * dart * smooth(61.25, 61.45, t) * (1 - smooth(62.4, 62.56, t)); P['pupil_size'] = lerp(1.0, 0.72, hh)
    shade = move(t, 61.55, 0.4, ant=0.2, amt=0.15) * (1 - smooth(T_ATMO, T_ATMO + 0.12, t))   # wings up over his head
    for i, nm in enumerate(('L', 'R')):
        w = P['wing' + nm]; fling = math.sin(clamp01((t - T_ATMO) / 0.5) * math.pi)
        w['flap'] = lerp(5, 46, shade) - 24 * limp + 26 * fling * (1 if i == 0 else 0.7) + 5 * math.sin((t - T_ATMO) * 5.0 + i) * limp * math.exp(-(max(0.0, t - T_ATMO)) / 1.2)
        w['fold'] = tuple(lerp(fo, (38, 30, 24)[j], shade) + lerp(0, (-14, 20, -26)[j] * (1 if i == 0 else -0.7), limp) for j, fo in enumerate(w['fold']))
        w['twist'] = lerp(0, 22 * (1 if i == 0 else -1), limp)
    P['lid'] = max(P['lid'], 0.55 * smooth(61.0, 62.3, t), 0.95 * limp)
    P['leds'] = tuple(lerp(1.0, 0.25 + 1.6 * (math.sin(t * (17 + 5 * j)) > 0), smooth(59.9 + 0.3 * j, 60.1 + 0.3 * j, t)) * (1 - 0.85 * limp) for j in range(3))
    sq = math.sin(clamp01((t - (T_ATMO - 0.14)) / 0.14) * math.pi)                 # anticipation: a squash before the pop
    P['dz'] += -0.06 * sq
    loose = spring_at(t, lambda s: 1.0 if s > T_ATMO else 0.0, 14.0, 1.6)
    P['dish_az'] = lerp(25, 150, loose); P['dish_el'] = lerp(38, 84, loose)
    P['whip'] = (tremble(t, 8 * hh) * (1 - limp) + 26 * (spring_at(t, lambda s: kick(s, T_ATMO), 50.0, 3.5) - hit), tremble(t + 1, 8 * hh) * (1 - limp))
    S['alpha'] = 1.0 if f <= tr.last_slot_frame else 0.0                            # there from the cut to the cut
    S['power'] = lerp(1.0, 0.3 + 0.35 * (math.sin(t * 23) > 0.3), limp)
    S['light'] = dict(sun=(0.45, 0.55, 0.62), sun_energy=lerp(10.0, 6.5, hh), earth=(-1, -0.4, 0.25), earth_energy=0.6, her_world=0.22, exposure=0.5, lamps=1.0 - limp)   # as he glows the sun steps back, so the red stays red
    return S

# sections/bridge.ts HIM_POSE (earth_c2_br drew the outline of her lights from his own model edges in this pose, orthographic)
BR_POSE = dict(yaw=-14.0, pitch=20.0, roll=5.0, head_pan=8.0, head_tilt=14.0, head_roll=9.0, dish_az=8.0, dish_el=112.0,
               wingL=dict(twist=18.0, flap=-5.0, fold=(7.0, 9.0, 12.0)), wingR=dict(twist=18.0, flap=-3.0, fold=(8.0, 10.0, 13.0)))
def act_br(tr, f):
    """"Every word you speak up there / You learned from everyone / You can travel past the moon ...": her lights rise and draw his
    outline around his star (bridge.ts: his own edges, his star = his eye). On "everyone" the eye ring closes and the real him comes up
    inside the outline, eye first: made of what he learned from her. He holds the pose (the outline stays on him as a rim of her light),
    so the acting is his face: the eye opens, he looks down at her, the lid softens; on "travel" he looks up to the moon, the dish
    swings to it; one look back on "the moon". He recedes on the bridge's own track and gives way to the small outline at ~163 s."""
    S = base_state(tr, f); t = f / FPS; row = S['row']; wide = tr.fmt == '169'
    P = merged(BR_POSE); S['P'] = P; bt = row['bt']; S['px_abs'] = (bt['origin_px'][0], bt['origin_px'][1]); S['span'] = bt['span_px']; S['d'] = 60.0
    EYE = 156.83
    wake = move(t, EYE, 0.26, ant=0.1, amt=0.12); alive = smooth(EYE + 0.1, EYE + 0.8, t)
    down = smooth(157.25, 157.6, t) * (1 - smooth(158.35, 158.62, t))              # he looks down at her
    up = move(t, 158.52, 0.5, ant=0.22, amt=0.12)                                  # "travel": up to the moon (upper left)
    back = move(t, 159.48, 0.3, ant=0.18, amt=0.2) * (1 - smooth(160.3, 160.75, t))  # one look back on "the moon"
    P['head_tilt'] = 14 + 13 * down - 22 * up * (1 - back) + 4 * back; P['head_pan'] = 8 + 4 * down - 30 * up * (1 - back); P['head_roll'] = 9 - 5 * up * (1 - back)
    P['brow_tilt'] = lerp(0, -12, wake) + 14 * down - 6 * up * (1 - back) + 10 * back
    P['lid'] = 1.9 * (1 - wake) + 0.30 * down + 0.25 * back + 0.9 * blink(t, 158.02)
    P['pupil_size'] = lerp(0.6, 1.25, wake) - 0.15 * down; P['pupil'] = (0.0, -0.03 * down + 0.02 * up * (1 - back))
    P['dish_az'] = 8 + 96 * move(t, 158.40, 0.6, ant=0.2, amt=0.1); P['dish_el'] = lerp(112, 58, move(t, 158.40, 0.6, ant=0.2, amt=0.1))   # the dish hears it first
    P['leds'] = tuple(clamp01((t - EYE - 0.25 - 0.14 * j) / 0.08) * (0.5 + 1.3 * math.exp(-(((t - EYE - 0.25 - 0.14 * j) % 1.1) / 0.12) ** 2)) for j in range(3))
    P['beacon'] = alive
    drive = lambda s: move(s, 158.52, 0.5, 0.22, 0.12) + 0.5 * move(s, EYE, 0.26, 0.1, 0.12)
    lag = spring_at(t, drive, 60.0, 5.0) - drive(t); P['whip'] = (8 * lag, 26 * lag + 2 * alive * nz(t, 71))
    S['alpha'] = smooth(156.62, 157.30, t) * (1 - smooth(162.45, 163.3, t)); S['power'] = clamp01(wake); S['heat'] = 0.0; S['idle'] = (0.0, 0.0)
    S['light'] = dict(sun=(-0.5, 0.45, 0.7), sun_energy=lerp(1.4, 4.2, alive), earth=(0.0, -1, 0.35), earth_energy=lerp(2.2, 1.3, alive), her_world=lerp(0.6, 0.4, alive),
                      exposure=0.5, lamps=alive)
    return S

def act_fc_hold(tr, f):
    """"I don't need to hold you down" (cut in, cut out): the last thread from her is taut on him; on "hold" it lets go. He lurches
    free (the pull is gone), the aerial whips, wings fly open; he looks back down at her, the brow softens, a small nod; he turns away."""
    S = base_state(tr, f); t = f / FPS; row = S['row']; wide = tr.fmt == '169'; P = S['P']
    S['span'] = 520.0 if wide else 350.0
    TR = 189.44
    free = kick(t, TR + 0.03); taut = smooth(188.6, 189.2, t) * (1 - smooth(TR, TR + 0.06, t))
    ux, uy = (-0.64, -0.77) if wide else (-0.45, -0.89)                             # away from her, in px (y down)
    S['off'] = ((12 * taut * math.sin(t * 38) * 0.15 + 30 * free) * ux + (0 if wide else 40), (30 * free) * uy + tremble(t, 1.5 * taut))
    away = smooth(190.2, 191.2, t)
    P['yaw'] = lerp(38, 30, free) - 46 * away; P['pitch'] = lerp(-12, -6, free); P['roll'] = lerp(-13, 6, free) + 2 * nz(t, 2, 0.3)   # leaning against the thread, then upright
    P['lean'] = lerp(7, -2, free)
    look = move(t, TR + 0.42, 0.3, ant=0.16, amt=0.2)                              # looks back down at her
    P['head_pan'] = lerp(-30, 16, look) + 30 * away; P['head_tilt'] = lerp(-4, 20, look) - 14 * away; P['head_roll'] = 6 * look
    nod = math.sin(clamp01((t - (TR + 0.95)) / 0.4) * math.pi); P['head_tilt'] += 7 * nod
    P['brow_tilt'] = lerp(14, -16, move(t, TR + 0.02, 0.16, ant=0.05, amt=0.3)) + 14 * smooth(TR + 0.7, TR + 1.1, t); P['lid'] = 0.3 * taut + 0.3 * smooth(TR + 0.7, TR + 1.1, t)
    P['pupil_size'] = lerp(0.85, 1.25, free) - 0.2 * smooth(TR + 0.7, TR + 1.1, t)
    for i, nm in enumerate(('L', 'R')):
        w = P['wing' + nm]; fl = move(t, TR + 0.03 + 0.05 * i, 0.3, ant=0.02, amt=0.1)
        w['flap'] = lerp(-4, 17, fl) - 6 * smooth(TR + 0.8, TR + 1.4, t); w['twist'] = lerp(-10, 6, fl) * (1 if i == 0 else -1)
        w['fold'] = tuple(lerp((9, 11, 14)[j], (-8, -7, -10)[j], move(t, TR + 0.03 + 0.05 * i + 0.06 * j, 0.3, ant=0.02, amt=0.1)) for j in range(3))
    P['dish_az'] = lerp(150, 60, free); P['dish_el'] = lerp(20, 50, free)
    drive = lambda s: kick(s, TR + 0.03)
    lag = spring_at(t, drive, 50.0, 3.5) - drive(t); P['whip'] = (22 * lag, 46 * lag + 2 * nz(t, 71))
    P['leds'] = tuple(0.5 + 1.3 * math.exp(-(((t - TR - 0.1 * j) % 1.2) / 0.1) ** 2) * (t > TR) for j in range(3))
    S['alpha'] = 1.0 if f <= tr.last_slot_frame else 0.0; S['heat'] = 0.0
    S['light'] = dict(sun=(0.72, 0.5, 0.4), sun_energy=6.8, earth=(0.75, -0.6, 0.25), earth_energy=1.0, her_world=0.34, exposure=0.5, lamps=1.0)
    return S

def hot_pose(t, h):
    """red hot: shaking, wings pulled over his head for shade, the eye squeezed, chest lights stuttering"""
    P = merged(None); hh = h * h
    P['yaw'] = 30 + 4 * nz(t, 1, 0.2); P['pitch'] = -8; P['roll'] = 6 + tremble(t, 2.8 * hh)
    for i, nm in enumerate(('L', 'R')):
        w = P['wing' + nm]; w['flap'] = lerp(5, 40, h) + 3 * math.sin(t * 13 + i) * h; w['fold'] = tuple(lerp(fo, (34, 28, 22)[j], h) for j, fo in enumerate(w['fold']))
    P['lid'] = 0.7 * h; P['brow_tilt'] = 18 * h; P['pupil_size'] = lerp(1.0, 0.7, h); P['head_tilt'] = 14; P['head_pan'] = -8 + 22 * math.sin(t * 4.2) * h
    P['leds'] = tuple(lerp(1.0, 0.25 + 1.6 * (math.sin(t * (17 + 5 * j)) > 0), h) for j in range(3))
    P['whip'] = (tremble(t, 9 * hh), tremble(t + 1, 9 * hh))
    return P, (tremble(t + 3.1, 4.0 * hh), tremble(t + 7.7, 3.0 * hh))

def act_fc_cool(tr, f):
    """"Who's gonna cool you down up there?" (final chorus; cut in, cut out): we look up at him for once. Pleased with himself for a
    beat, then the heat climbs: the chest lights stutter, he looks down at them, starts to shake, the wings come up."""
    S = base_state(tr, f); t = f / FPS; row = S['row']; wide = tr.fmt == '169'
    S['span'] = 560.0 if wide else 400.0
    h = smooth(197.6, 199.5, t); S['heat'] = h
    P, off = hot_pose(t, h); S['P'] = P; S['off'] = off
    P['yaw'] = 26; P['pitch'] = -16                                                # seen from below
    for nm in ('L', 'R'): P['wing' + nm]['twist'] = 20.0 * (1 - h)                   # feathered off the sun until they come up for shade
    worry = move(t, 198.15, 0.26, ant=0.16, amt=0.2)
    P['head_tilt'] = lerp(-8, 24, worry); P['head_pan'] = lerp(12, 2, worry) + 20 * math.sin(t * 4.2) * h * smooth(198.9, 199.2, t); P['brow_tilt'] = lerp(16, -14, worry) + 14 * h * h; P['brow_roll'] = lerp(10, 0, worry)
    P['lid'] = max(lerp(0.35, 0.0, worry), 0.6 * smooth(198.8, 199.5, t))
    S['alpha'] = 1.0 if f <= tr.last_slot_frame else 0.0
    S['light'] = dict(sun=(0.5, 0.78, 0.38), sun_energy=lerp(8.0, 6.0, h * h), earth=(0.5, -0.85, 0.1), earth_energy=0.7, her_world=0.24, exposure=0.5, lamps=1.0)
    return S

def act_fc_end(tr, f):
    """From "You've got no atmosphere" (cut in at 199.52) through the countdown to "disconnected", one fixed place in the top corner
    (finalChorus.ts satPos). Red hot and shaking over her scarf, wings over his head; he cools as the count starts and hangs on his data
    link, dish down at her, his three chest lights counting with her (two lit on "two", one on "one"). On "disconnected" the link
    snaps: he jolts back, the dish swings loose, the eye stutters red and goes out, the wings sag. He stays, dark, in her light."""
    S = base_state(tr, f); t = f / FPS; row = S['row']; wide = tr.fmt == '169'
    TWO, ONE, DISC = 210.56, 211.20, 211.76
    punch = smooth(DISC - 0.42, DISC + 0.04, t)
    S['span'] = lerp(430.0, 790.0, punch) if wide else lerp(330.0, 420.0, punch)
    cool = smooth(203.6, 205.8, t)                                                 # the count starts: he comes down from red
    h = (1 - 0.25 * smooth(202.0, 203.6, t)) * (1 - cool); S['heat'] = h
    Ph, off_h = hot_pose(t, h)
    snap = kick(t, DISC + 0.02); dead = smooth(DISC + 0.25, DISC + 0.75, t)
    P = merged(None)
    P['yaw'] = 34; P['pitch'] = -10; P['roll'] = lerp(4, -14, dead) + 1.5 * nz(t, 2, 0.3) + 14 * (snap - smooth(DISC, DISC + 0.6, t))
    P['head_pan'] = 10 + 8 * nz(t, 9, 0.12) * (1 - dead); P['head_tilt'] = lerp(16, 30, dead); P['head_roll'] = 12 * dead
    P['brow_tilt'] = lerp(4, -18, move(t, DISC + 0.02, 0.14, ant=0.04, amt=0.3)) * (1 - dead) + 16 * dead; P['lid'] = 1.25 * dead
    P['pupil_size'] = lerp(1.0, 1.3, snap) * (1 - 0.5 * dead)
    for i, nm in enumerate(('L', 'R')):
        w = P['wing' + nm]; w['flap'] = lerp(6, -24, dead) + 9 * (snap - smooth(DISC, DISC + 0.5, t)); w['twist'] = lerp(20.0, 14.0 * (1 if i == 0 else -1), dead)   # feathered off the sun (flat to it the panels mirror it)
        w['fold'] = tuple(fo + (12, -18, 22)[j] * dead * (1 if i == 0 else -0.8) for j, fo in enumerate(w['fold']))
    loose = spring_at(t, lambda s: 1.0 if s > DISC else 0.0, 14.0, 1.6)             # the dish swings on its gimbal, barely damped
    P['dish_az'] = 150 + 60 * loose; P['dish_el'] = lerp(18, 78, loose)
    n_lit = 3 if t < TWO + 0.02 else 2 if t < ONE + 0.02 else 1 if t < DISC else 0
    P['leds'] = tuple((1.2 + 0.5 * math.exp(-(((t - 0.13 * j) % 0.75) / 0.1) ** 2) if j < n_lit else 0.04) * (1 - 0.9 * dead) for j in range(3))   # data ticking up the link
    lag = spring_at(t, lambda s: kick(s, DISC + 0.02), 50.0, 3.5) - snap; P['whip'] = (20 * lag, 44 * lag)
    S['P'] = mixv(Ph, P, cool); S['off'] = (off_h[0] * (1 - cool) + 30 * snap * -0.5, off_h[1] * (1 - cool) + 30 * snap * -0.87)
    stut = 1.0 if t < DISC else (1.0 if math.sin((t - DISC) * 70) > 0 else 0.15)   # the same stutter as the link (outro.ts)
    S['power'] = stut * (1 - dead); S['P']['beacon'] = 1 - dead; S['eye_red'] = smooth(DISC, DISC + 0.3, t)
    S['idle'] = (1 - dead, 1 - 0.7 * dead)
    S['alpha'] = 1.0                                                                # after "disconnected" he goes with the engine's blend into the sunrise (state(): alpha x w outside the run)
    S['light'] = dict(sun=(0.78, 0.5, 0.38), sun_energy=lerp(6.5, 4.5, dead), earth=(0.6, -0.8, 0.25), earth_energy=lerp(0.9, 1.2, dead), her_world=0.3, exposure=0.5, lamps=1 - dead)
    return S

def act_p2_estate(tr, f):
    """"All that empty real estate" (pre2.ts: 100 BILLION LOTS AVAILABLE, and he has bought one tiny one). He glides in from off
    frame right and settles beside his lot (104.27-104.90, on the builder's own path); the SOLD board swings in at 105.07: the take,
    he looks at it (to his left), pats it with a wing, then the look to camera, brow cocked. As the survey lets go (106.37) he
    crouches and is off, out of frame right."""
    S = base_state(tr, f); t = f / FPS; row = S['row']; wide = tr.fmt == '169'; P = S['P']
    IN, REST, SOLD, OUT = 104.27, 104.90, 105.07, 106.37
    punch = smooth(REST, SOLD + 0.33, t) * (1 - smooth(OUT - 0.20, OUT + 0.04, t))
    S['span'] = (518.0 if wide else 326.0) * (1 + (0.19 if wide else 0.12) * punch)
    arr = smooth(IN, REST + 0.15, t); brake = math.sin(clamp01((t - (REST - 0.35)) / 0.6) * math.pi)
    crouch = math.sin(clamp01((t - (OUT - 0.2)) / 0.22) * math.pi); go = clamp01((t - (OUT + 0.02)) / 0.5); go = go * go * go
    S['off'] = (-16 * crouch + tr.units(1.6 if wide else 1.0) * go, 6 * crouch - tr.units(0.25) * go)
    P['yaw'] = lerp(-58, -22, arr) + 70 * go; P['pitch'] = -4; P['roll'] = 5 + 13 * brake - 20 * crouch + 2 * nz(t, 2, 0.3) - 24 * go
    take = move(t, SOLD + 0.08, 0.24, ant=0.14, amt=0.25); smug = move(t, 105.72, 0.28, ant=0.14, amt=0.2) * (1 - smooth(OUT - 0.25, OUT - 0.05, t))
    P['head_pan'] = lerp(18, -30, take) + 62 * smug; P['head_tilt'] = lerp(-6, 10, take) - 8 * smug; P['head_roll'] = -10 * smug
    P['brow_tilt'] = lerp(4, -18, move(t, SOLD + 0.1, 0.18, ant=0.08, amt=0.4)) + 38 * smug; P['brow_roll'] = -13 * smug; P['lid'] = 0.42 * smug
    P['pupil_size'] = lerp(1.0, 1.25, take) - 0.2 * smug
    tap = math.sin(clamp01((t - 105.32) / 0.42) * math.pi * 2) ** 2                # two pats
    P['wingL'] = dict(twist=6.0 + 10 * brake, flap=4.0 - 11 * tap + 12 * brake, fold=(-6.0 - 9 * tap, -8.0, -10.0))
    P['wingR'] = dict(twist=-6.0 - 10 * brake, flap=6.0 + 12 * brake + 26 * go, fold=(-4.0, -6.0, -8.0 - 20 * go))
    P['leds'] = tuple(0.5 + 1.4 * math.exp(-(((t - SOLD - 0.11 * j) % 0.7) / 0.1) ** 2) * (t > SOLD) for j in range(3))
    P['dish_az'] = lerp(25, -60, take); P['dish_el'] = 40
    drive = lambda s: smooth(IN, REST + 0.15, s) + 0.6 * move(s, SOLD + 0.08, 0.24, 0.14, 0.25)
    lag = spring_at(t, drive, 50.0, 4.0) - drive(t); P['whip'] = (10 * lag, 40 * lag + 2 * nz(t, 71))
    S['alpha'] = 1.0 if IN - 0.02 <= t <= OUT + 0.55 else 0.0; S['heat'] = 0.0
    S['light'] = dict(sun=(0.5, 0.4, 0.65), sun_energy=7.0, earth=(0.0, -1, 0.3), earth_energy=1.1, her_world=0.32, exposure=0.5, lamps=1.0)
    return S


def act_c2(tr, f):
    """C2 is three camera setups: the chase, the rising thermometer, and the held silhouette above Earth's air."""
    S = base_state(tr, f)
    t, row, P = f / FPS, S['row'], S['P']
    wide = tr.fmt == '169'
    if row['slot'] in ('c2_sun', 'c2_disappear'):
        chase = tr.t0 + 0.64                       # "chase" at 121.20
        disappear = tr.t0 + 2.96                   # "disappear" at 123.52
        push = move(t, chase, 0.34, ant=0.18, amt=0.22)
        glare = smooth(disappear - 0.22, disappear + 0.40, t)
        S['span'] = (425 if wide else 288) * lerp(1.0, 0.62, glare)
        S['alpha'] = clamp01(row['int'] / 1.65)
        P['yaw'], P['pitch'], P['roll'] = lerp(18, 37, push), 4, lerp(-3, -12, push)
        P['head_pan'], P['head_tilt'] = lerp(-34, 10, push), lerp(8, -7, push)
        P['lid'], P['dish_az'] = 0.83 * glare, lerp(-20, -75, push)
        for nm in ('L', 'R'):
            P['wing' + nm]['twist'] = lerp(20, -9, push)
            P['wing' + nm]['flap'] = lerp(4, 10, push)
        S['light'].update(sun=(0.8, 0.08, 0.59), sun_energy=lerp(6.5, 10, glare), exposure=lerp(0.5, 0.79, glare))
        return S

    S['alpha'] = float(f <= tr.last_slot_frame)
    heat = heat_of(row)
    S['heat'] = heat
    if row['slot'] == 'c2_cool':
        S['span'] = 412 if wide else 296
        worry = smooth(125.44, 125.94, t)          # "cool" to "down"
        P['yaw'], P['pitch'], P['roll'] = -16, -13, 2 + 2.2 * heat * heat * math.sin(14 * t)
        P['head_pan'], P['head_tilt'] = lerp(-4, 29, worry), lerp(-5, 15, worry)
        P['lid'], P['brow_tilt'] = lerp(0.25, 0.08, worry), lerp(13, -10, worry)
        P['leds'] = tuple(lerp(0.6, 1.6, smooth(125.44 + j * 0.18, 125.75 + j * 0.18, t)) for j in range(3))
    else:
        S['span'] = 480 if wide else 344
        settle_heat = smooth(128.16, 128.88, t)    # "atmosphere" into the hold
        P['yaw'], P['pitch'], P['roll'] = lerp(-18, -11, settle_heat), 6, lerp(3, -4, settle_heat)
        P['head_pan'], P['head_tilt'] = lerp(10, -4, settle_heat), lerp(-3, 11, settle_heat)
        P['lid'], P['brow_tilt'] = lerp(0.18, 0.76, settle_heat), lerp(-7, 16, settle_heat)
        S['power'] = lerp(1.0, 0.39, settle_heat)
        S['idle'] = (0.25, 0.2)
        for nm in ('L', 'R'):
            P['wing' + nm]['flap'] = lerp(8, -8, settle_heat)
            P['wing' + nm]['twist'] = 13
    S['light'].update(sun=(0.68, 0.34, 0.64), sun_energy=lerp(6.5, 4.3, heat), earth_energy=0.92, exposure=0.5)
    return S

DEBUG = {}
ACTS = dict(co_count=act_co_count, c1_chase=act_c1_chase, c1_heat=act_c1_heat, c2=act_c2, br=act_br, fc_hold=act_fc_hold, fc_cool=act_fc_cool, fc_end=act_fc_end, p2_estate=act_p2_estate)

def state(tr, f):
    S = ACTS[tr.run](tr, f); t = f / FPS
    iw, ib = S.get('idle', (1.0, 1.0)); S['P'] = my_idle(t, S['P'], iw, ib)
    row = S['row']
    if not row.get('shot', False): S['alpha'] *= S['w']     # the picture is not (yet / any more) this run's shot: only the engine's own blend out of it may still show him (0 across a cut)
    base = S.get('px_abs') or row['px']; S['px'] = (base[0] + S['off'][0], base[1] + S['off'][1])
    if DEBUG.get('span'): S['span'] = float(DEBUG['span']); S['px'] = (tr.W / 2, tr.H * 0.6)      # look-dev: a close-up in the middle of the frame
    return S

# ----------------------------------------------------------------------------- apply to the scene
HEAT_MATS = {'HIM_foil': 0.9, 'HIM_white': 0.22, 'HIM_goldtrim': 0.6, 'HIM_alu': 0.3, 'HIM_kapton': 0.7, 'HIM_dark': 0.35}   # the form must stay readable: a glow from inside, not a pink coat
EYE0 = {}
def principled(mat): return next((n for n in bpy.data.materials[mat].node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None) if mat in bpy.data.materials else None
def apply_heat(h, power, eye_red=0.0):
    """overheating = his colour code going from warm to red: the body glows (emission), the eye turns red, a red light in his chest"""
    for m, k in HEAT_MATS.items():
        b = principled(m)
        if b is None or b.inputs['Emission Strength'].is_linked or b.inputs['Emission Color'].is_linked: continue
        b.inputs['Emission Color'].default_value = (1.0, 0.05, 0.008, 1); b.inputs['Emission Strength'].default_value = k * h * h
    e = max(h, eye_red)
    for m in ('HIM_eye', 'HIM_pupilmat'):
        b = principled(m)
        if m not in EYE0: EYE0[m] = tuple(b.inputs['Emission Color'].default_value)
        c0 = EYE0[m]; b.inputs['Emission Color'].default_value = (lerp(c0[0], 1.0, e), lerp(c0[1], 0.07, e), lerp(c0[2], 0.02, e), 1)
    if 'HIM_heatlight' not in bpy.data.objects:
        ld = bpy.data.lights.new('HIM_heatlight', 'POINT'); ld.color = (1.0, 0.07, 0.015); ld.shadow_soft_size = 0.5
        lo = bpy.data.objects.new('HIM_heatlight', ld); bpy.context.scene.collection.objects.link(lo); lo.parent = HR.ob('HIM_bob'); lo.location = (0, -0.75, 0.1)
    bpy.data.lights['HIM_heatlight'].energy = 26.0 * h * h
    bpy.data.lights['HIM_eyelight'].color = (1.0, lerp(0.6, 0.1, e), lerp(0.3, 0.03, e))

SC_REF_HIM = 1000.0 / 2560 * 2 * HR.TAN * 14 / SPAN       # the look-dev scale his point lights were tuned at (span 1000 px, d 14)
SC_REF_RKT = 640.0 / 2560 * 2 * HR.TAN * 40 / 9.0
def norm_point_lights(sc, ref):
    """his own lights are point lights in world units; he is placed by scaling the model, so their reach has to scale with him (energy ~ scale^2)"""
    k = (sc / ref) ** 2
    for nm in ('HIM_eyelight', 'HIM_lamplightL', 'HIM_lamplightR', 'HIM_heatlight', 'RKT_flamelight'):
        if nm in bpy.data.lights: bpy.data.lights[nm].energy *= k

QPREV = {}
def set_root(o, M):
    loc, q, sc = M.decompose(); o.rotation_mode = 'QUATERNION'
    p = QPREV.get(o.name)
    if p is not None and p.dot(q) < 0: q = -q
    QPREV[o.name] = q.copy(); o.location, o.rotation_quaternion, o.scale = loc, q, sc

def apply_state(tr, S, transforms=True):
    L = S['light']; W, H = tr.W, tr.H
    HR.light_shot(L['sun'], L['sun_energy'], L['earth'], L['earth_energy'], L['her_world'], (0.50, 0.86, 1.0), L['exposure'], L['lamps'])
    P = S['P']; P['eye'] = P.get('eye', 1.0) * S['power']
    him, rk = HR.ob('HIM_root'), HR.ob('RKT_root')
    if S.get('rocket'):
        k = S['rocket']; M = HR.view_matrix(S['px'], k['len_px'], k.get('d', 40), k['yaw'], k['pitch'], k['roll'], 9.0, base=float(W), aspect=H / W); ref = SC_REF_RKT
    else:
        M = HR.view_matrix(S['px'], S['span'], S.get('d', 14.0), P['yaw'], P['pitch'], P['roll'], SPAN, base=float(W), aspect=H / W); ref = SC_REF_HIM
    if transforms:
        HR.apply_pose(P)
        if S.get('rocket'):
            HR.hide_tree(rk, False); set_root(rk, M)
            if him.parent != HR.ob('RKT_seat'):
                him.parent = HR.ob('RKT_seat'); him.matrix_parent_inverse = Matrix.Identity(4)
            him.rotation_mode = 'XYZ'; him.location = (0, 0, 0); him.rotation_euler = (0, 0, R(90)); him.scale = (1, 1, 1)
            for nm in ('RKT_fairingA', 'RKT_fairingB'): HR.hide_tree(HR.ob(nm), True)
            HR.ob('RKT_flame').scale = (1, 1, k['flame_len'])
        else:
            HR.hide_tree(rk, True); him.parent = None; set_root(him, M)
        HR.hide_tree(him, False)
    else:
        HR.apply_pose_lights(P)
    if S.get('rocket'): bpy.data.lights['RKT_flamelight'].energy = S['rocket']['flame_light']
    apply_heat(S['heat'], S['power'], S.get('eye_red', 0.0))
    norm_point_lights(M.to_scale()[0], ref)

def soften_cells():
    b = principled('HIM_cells')
    if b is None: return
    for k, v in (('Coat Weight', 0.22), ('Coat Roughness', 0.42), ('Metallic', 0.22), ('Specular IOR Level', 0.3)):   # less mirror: a panel square to the sun stays blue cells
        if k in b.inputs and not b.inputs[k].is_linked: b.inputs[k].default_value = v
    if 'HIM_sun' in bpy.data.lights: bpy.data.lights['HIM_sun'].specular_factor = 0.7

def rig_objects():
    return [o for o in bpy.data.objects if o.name.startswith('HIM_') or o.name.startswith('RKT_')]

def bake(tr, frames):
    """linear transform keys on every rig object for the frames we render and one frame each side (motion blur samples between them)"""
    try: bpy.context.preferences.edit.keyframe_new_interpolation_type = 'LINEAR'
    except Exception as ex: print('[bake] interpolation pref', ex)
    need = sorted({g for f in frames for g in (f - 1, f, f + 1)})
    objs = None
    for f in need:
        apply_state(tr, state(tr, f))
        if objs is None: objs = rig_objects()
        for o in objs:
            o.keyframe_insert('location', frame=f); o.keyframe_insert('scale', frame=f)
            o.keyframe_insert('rotation_quaternion' if o.rotation_mode == 'QUATERNION' else 'rotation_euler', frame=f)
    print('[bake] keyed', len(objs or []), 'objects on', len(need), 'frames', flush=True)

def main(argv):
    run, fmt, out = argv[0], argv[1], argv[2]; opt = dict(a.split('=', 1) for a in argv[3:])
    tr = Track(run, fmt); os.makedirs(out, exist_ok=True); DEBUG.update({k: v for k, v in opt.items() if k in ('span',)})
    f_first, f_last = int(opt.get('first', tr.f0)), int(opt.get('last', tr.f1))
    frames = [int(x) for x in opt['stills'].split(',')] if opt.get('stills') else list(range(f_first, f_last + 1))
    meta = dict(run=run, fmt=fmt, res=[tr.W, tr.H], f0=tr.f0, f1=tr.f1, frames=[])
    for f in range(tr.f0, tr.f1 + 1):
        S = state(tr, f); meta['frames'].append(dict(f=f, alpha=round(S['alpha'], 4), px=[round(S['px'][0], 1), round(S['px'][1], 1)], span=round(S['rocket']['len_px'] if S.get('rocket') else S['span'], 1),
                                                     heat=round(S['heat'], 3), power=round(S['power'], 3), yaw=round(S['P']['yaw'], 2), pitch=round(S['P']['pitch'], 2), roll=round(S['P']['roll'], 2)))
    json.dump(meta, open(os.path.join(out, 'meta.json'), 'w'))
    if opt.get('meta'): print('[him_slots] meta only', out); return
    sc = HR.setup_scene((tr.W, tr.H), int(opt.get('samples', 48)))
    sc.render.resolution_percentage = int(opt.get('pct', 100)); sc.render.fps = 30
    HR.ob('HIM_cam').data.sensor_fit = 'HORIZONTAL'; soften_cells()
    mb = opt.get('mb', '1') == '1'
    sc.render.use_motion_blur = mb
    if mb:
        sc.render.motion_blur_shutter = 0.5
        for k, v in (('motion_blur_steps', int(opt.get('steps', 3))), ('motion_blur_position', 'CENTER')):
            for holder in (sc.eevee, sc.render):
                if hasattr(holder, k):
                    try: setattr(holder, k, v)
                    except Exception as ex: print('[mb] skip', k, ex)
    todo = [f for f in frames if not (os.path.exists(os.path.join(out, f'him_{f:05d}.png')) and opt.get('resume', '1') == '1')]
    todo = [f for f in todo if any(m['f'] == f and m['alpha'] > 0.004 for m in meta['frames'])]      # frames where he is not there are not rendered
    if not todo: print('[him_slots] nothing to render'); return
    bake(tr, todo)
    for f in todo:
        sc.frame_set(f); apply_state(tr, state(tr, f), transforms=False)
        sc.render.filepath = os.path.join(out, f'him_{f:05d}.png'); bpy.ops.render.render(write_still=True)
        print('[him_slots] wrote', sc.render.filepath, flush=True)

if __name__ == '__main__':
    main(sys.argv[sys.argv.index('--') + 1:])
