"""Deployed on a Friday — The Drive (Claude Fable 5.1's second take).

The whole video is the drive home after shipping at 4:59, seen from the driver's seat of a car on a coast highway.
The dashboard carries the clock, the gauges and the phone in its mount; the road carries the lyrics as highway
signs. Every chorus the tide comes in over the road and the car floats, water rising inside it, a ROLLBACK life ring
thrown through the windshield. Verse two is night on a pier of neon Slack channels; the bridge is the car pulled
over at an overlook at low tide, the seabed full of shortcuts; verse three is the U-turn and the fix; the finale is
dawn with the PROD lighthouse still standing; the outro is the clock reading 4:59 again at the office gate."""
import os, sys, math
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from studio import core as C
from studio.core import hexc, sstep, clamp, lerp
import dof_world as WD
import dof_sprites as SP
import dof_dash as DS
import dof_type as TY

TM = C.Timing(HERE)
TAIL = 5.0
DUR = TM.duration + TAIL
T_END = DUR - 6.5
C.THEME.update(disp=C.F_DISP, body=C.F_INTER, red=hexc('ff5d4f'))

lt = TM.line_t; wt = TM.word_t
T_459 = lt("Four fifty-nine", 0); T_SHIP = wt("Ship it", "Ship"); T_IT = wt("Ship it", "it")
T_V1 = lt("Four fifty-nine, laptop half shut"); T_CHANGE = lt("One little change")
T_NOTICKET = lt("No ticket"); T_NOTEST = wt("No ticket", "test"); T_NOEYES = wt("No ticket", "eyes")
T_GREEN = lt("Green check lying"); T_COFFEE = lt("Coffee gone cold"); T_MERGE = lt("Merge to main")
T_WINDOWS = lt("Windows down"); T_PAGER = lt("Pager on my hip")
T_PRE1 = lt("Buzz, buzz, don't look", 0); T_LOOKED = lt("Buzz, buzz, I looked")
T_CH1 = lt("I deployed on a Friday, tide coming in", 0); T_UNDER1 = lt("Prod going under", 0)
T_ROPE1 = wt("throw me a rope", "rope", 0); T_RED1 = lt("Dashboard red", 0); T_NEVER1 = lt("I deployed on a Friday, never again", 0)
T_LAST1 = lt("Said that last Friday", 0)
T_V2 = lt("Slack lighting up"); T_ANYONE = lt("Anyone change something"); T_NULL = wt("Null in the column", "Null")
T_ROWS = lt("Ten thousand rows"); T_RETRY = lt("Retry, retry"); T_DEAD = lt("Dead letters")
T_VP1 = lt("VP typing, VP stopped"); T_VPSTOP = wt("VP typing, VP stopped", "stopped"); T_VP2 = lt("VP typing, there it dropped"); T_DROP = wt("VP typing, there it dropped", "dropped")
T_PRE2 = lt("Buzz, buzz, don't look", 1); T_COOKED = wt("Buzz, buzz, I'm cooked", "cooked")
T_CH2 = lt("I deployed on a Friday, tide coming in", 1); T_UNDER2 = lt("Prod going under", 1)
T_ROPE2 = wt("throw me a rope", "rope", 1); T_RED2 = lt("Dashboard red", 1); T_NEVER2 = lt("I deployed on a Friday, never again", 1)
T_LAST2 = lt("Said that last Friday", 1); T_CH2_END = [L for L in TM.lines if 'Said that last Friday' in L['text']][1]['e']   # the last sung line of the chorus (the section runs on into the instrumental)
T_BRIDGE = lt("Low tide shows you everything"); T_SHORTCUT = lt("Every shortcut"); T_PARKING = lt("Fix it from the parking lot"); T_ONEBAR = lt("One bar of signal")
T_REVERT = lt("Revert the revert"); T_CHERRY = wt("Revert the revert", "cherry-pick"); T_PUSH = wt("Revert the revert", "push")
T_PIPE = lt("Pipeline crawling"); T_WHOOSH = wt("Pipeline crawling", "whoosh"); T_CACHE = lt("Cache still warm")
T_FLUSH = lt("Flush it, bounce it"); T_BOUNCE = wt("Flush it, bounce it", "bounce"); T_WAIT = wt("Flush it, bounce it", "wait")
T_GRAPH = lt("Graph dips down"); T_BACK = wt("Graph dips down", "back"); T_GG = lt("Green on green"); T_BLACK = wt("Green on green", "black")
T_CLOSE = lt("Close the laptop"); T_QUESTION = lt("Phone lights up")
T_FINAL = lt("I deployed on a Friday, tide going out"); T_STANDING = lt("Prod's still standing"); T_CUT = lt("Rollback, rollback, cut the rope"); T_CUTW = wt("cut the rope", "cut")
T_MONDAY = lt("Monday's a postmortem"); T_NEVER3 = lt("I deployed on a Friday, never again", 2); T_NEXT = lt("See you next Friday")
T_ROOT = lt("Root cause: me"); T_459B = lt("Four fifty-nine", 2)
T_STOP = 116.5                   # parked at the overlook (instrumental after the second chorus)
T_UTURN = T_REVERT + 0.45


def ease(x): x = clamp(x); return x * x * (3 - 2 * x)


def curve(keys, t):
    if t <= keys[0][0]: return keys[0][1]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t0 <= t <= t1: return v0 + (v1 - v0) * ease((t - t0) / max(1e-6, t1 - t0))
    return keys[-1][1]


def lin(keys, t):
    if t <= keys[0][0]: return keys[0][1]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t0 <= t <= t1: return v0 + (v1 - v0) * (t - t0) / max(1e-6, t1 - t0)
    return keys[-1][1]


# ------------------------------------------------------------------ speed and distance
SPEED = [(0, 0), (T_IT + 0.9, 0), (T_IT + 1.3, 1.5), (17.5, 9.0), (T_V1, 10.5), (T_CH1, 10.5), (T_CH1 + 2, 6.0), (T_LAST1, 6.0),
         (T_V2, 10.0), (T_RETRY - 0.5, 10.0), (T_RETRY + 0.6, 2.6), (T_DEAD + 2.0, 2.6), (T_VP1 + 1.5, 9.5), (T_CH2, 10.0), (T_CH2 + 2, 5.5),
         (T_CH2_END, 5.5), (T_CH2_END + 1.5, 9.0), (T_STOP - 2.5, 4.0), (T_STOP, 0.0), (T_UTURN, 0.0), (T_UTURN + 0.5, 3.0), (T_PIPE - 0.3, 9.0),
         (T_PIPE + 0.2, 3.0), (T_WHOOSH - 0.1, 3.0), (T_WHOOSH + 0.3, 17.0), (T_CACHE, 11.0), (T_WAIT, 10.0), (T_WAIT + 0.4, 4.0), (T_GRAPH - 0.2, 4.0),
         (T_GRAPH + 0.5, 10.5), (T_FINAL, 10.5), (T_NEXT + 2.0, 10.5), (T_ROOT, 6.0), (T_459B + 2.0, 0.0), (DUR + 5, 0.0)]
_TG = np.arange(0, DUR + 6, 1 / 30.0)
_SP = np.array([lin(SPEED, float(x)) for x in _TG], np.float32)
_DI = np.concatenate([[0.0], np.cumsum((_SP[1:] + _SP[:-1]) * 0.5 / 30.0)])


def speed(t): return float(np.interp(t, _TG, _SP))
def dist(t): return float(np.interp(t, _TG, _DI))


TRACK = WD.Track()

# ------------------------------------------------------------------ the story
TOD = [(0, 0.0), (T_V1, 0.03), (T_PRE1, 0.12), (T_CH1, 0.16), (T_RED1, 0.25), (T_LAST1, 0.3), (T_V2, 0.42), (T_V2 + 3, 0.5), (T_CH2_END, 0.52),
       (T_STOP, 0.58), (T_REVERT, 0.62), (T_PIPE, 0.68), (T_GG, 0.74), (T_FINAL, 0.78), (T_STANDING, 0.84), (T_NEVER3, 0.92), (T_NEXT + 2, 0.97),
       (T_459B - 0.02, 0.97), (T_459B, 0.0), (DUR + 5, 0.0)]
CLOCK = [(0, 0), (T_V1 + 1.6, 0), (T_V1 + 1.7, 1), (T_CH1, 15), (T_V2, 281), (T_CH2, 419), (T_BRIDGE, 613), (T_REVERT, 751), (T_FINAL, 829), (T_ROOT, 900),
         (T_459B - 0.02, 900), (T_459B, 0), (DUR + 5, 0)]


def clock(t):
    m = int(lin(CLOCK, t)); hh = (16 + (59 + m) // 60) % 24; mm = (59 + m) % 60
    return f"{hh % 12 or 12}:{mm:02d}", ("PM" if hh >= 12 else "AM")


def flood(t):
    """Water height over the road (world units, 0..0.9)."""
    f = 0.0
    f = max(f, curve([(T_CH1 - 0.2, 0), (T_CH1 + 1.8, 0.45), (T_UNDER1, 0.5), (T_UNDER1 + 1.6, 0.72), (T_LAST1 + 2.5, 0.72), (T_V2 + 0.8, 0.0)], t) if T_CH1 - 0.2 <= t <= T_V2 + 0.8 else 0)
    f = max(f, curve([(T_CH2 - 0.2, 0), (T_CH2 + 1.6, 0.55), (T_UNDER2 + 1.6, 0.85), (T_LAST2 + 3, 0.85), (T_CH2_END + 1.8, 0.0)], t) if T_CH2 - 0.2 <= t <= T_CH2_END + 1.8 else 0)
    f = max(f, curve([(T_FINAL - 1.0, 0.32), (T_FINAL + 2.5, 0.12), (T_STANDING + 1.0, 0.0)], t) if T_FINAL - 1.0 <= t <= T_STANDING + 1.0 else 0)
    return f


def interior(t):
    lv = 0.0
    lv = max(lv, curve([(T_UNDER1 + 0.2, 0), (T_UNDER1 + 2.2, 0.2), (T_LAST1 + 3, 0.22), (T_V2 + 1.0, 0)], t) if T_UNDER1 <= t <= T_V2 + 1 else 0)
    lv = max(lv, curve([(T_UNDER2 + 0.2, 0), (T_UNDER2 + 2.4, 0.3), (T_LAST2 + 3, 0.33), (T_CH2_END + 2.2, 0)], t) if T_UNDER2 <= t <= T_CH2_END + 2.2 else 0)
    return lv


def story(t):
    S = dict(t=t, tod=lin(TOD, t), flood=flood(t), interior=interior(t), clouds=0.5, cloud_drift=dist(t) * 0.15 + t * 1.5)
    S['night'] = WD.night(S['tod'])
    S['amb'] = float(lerp(1.0, 0.55, S['night']))
    # dashboard
    red = 0.0
    if T_RED1 - 0.1 <= t <= T_V2 + 1: red = sstep(T_RED1 - 0.1, T_RED1 + 0.25, t) * (1 - sstep(T_V2, T_V2 + 1, t))
    if T_RED2 - 0.1 <= t <= T_CH2_END + 1.5: red = max(red, sstep(T_RED2 - 0.1, T_RED2 + 0.25, t) * (1 - sstep(T_CH2_END, T_CH2_END + 1.5, t)))
    S['red'] = red
    sp = speed(t); S['speed_dial'] = clamp(sp / 16.0) * 0.8 + (0.08 if sp > 0 else 0)
    temp = 0.32 + 0.25 * sstep(T_PRE2, T_COOKED, t) * (1 - sstep(T_CH2_END + 3, T_STOP, t))
    temp += 0.45 * sstep(T_COOKED - 0.2, T_COOKED + 0.3, t) * (1 - sstep(T_CH2_END + 2, T_STOP, t))
    temp += 0.2 * sstep(T_CACHE - 0.2, T_CACHE + 0.4, t) * (1 - sstep(T_FLUSH, T_FLUSH + 1.5, t))
    S['temp'] = min(temp, 1.0)
    S['prod_warn'] = max(sstep(T_UNDER1 - 0.1, T_UNDER1 + 0.2, t) * (1 - sstep(T_V2 - 0.5, T_V2, t)),
                         sstep(T_UNDER2 - 0.1, T_UNDER2 + 0.2, t) * (1 - sstep(T_CH2_END, T_CH2_END + 1, t)),
                         sstep(T_PRE1, T_PRE1 + 0.2, t) * (1 - sstep(T_CH1, T_CH1 + 0.1, t)) * 0.8)
    c, ap = clock(t); S['clock'] = c; S['ampm'] = ap
    S['day'] = 'FRI' if t < T_V2 else ('SAT' if t < T_459B else 'FRI')
    S['steam'] = 1 - sstep(T_COFFEE, T_COFFEE + 1.2, t) if t < T_459B else 1.0
    S['lid'] = 0.5 * (1 - sstep(T_CLOSE + 0.3, T_CLOSE + 1.2, t)) if t < T_459B else 0.5
    S['lap_glow'] = 1.0
    S['hands'] = 1.0
    # phone
    buzz = 0.0
    for tb in (T_PAGER + 0.8, T_PRE1, T_PRE1 + 0.62, T_LOOKED, T_LOOKED + 0.62, T_PRE2, T_PRE2 + 0.62, T_PRE2 + 2.2, T_PRE2 + 2.8, T_QUESTION):
        if tb <= t < tb + 0.45: buzz = max(buzz, 1 - (t - tb) / 0.45)
    S['buzz'] = buzz
    if t < T_SHIP - 0.4 or (T_IT + 3.2 <= t < T_PAGER + 0.7): S['phone'] = 'dark'
    elif t < T_IT + 3.2 or t >= T_459B + 1.2: S['phone'] = 'pr'; S['press'] = sstep(T_IT - 0.05, T_IT + 0.05, t) * (1 - sstep(T_IT + 0.25, T_IT + 0.4, t)) if t < T_459B else 0.0; S['deploy'] = (sstep(T_IT + 0.1, T_IT + 2.4, t) if t >= T_IT + 0.1 else 0.0) if t < T_459B else 0.0
    elif t < T_V2: S['phone'] = 'alerts'; S['n_alerts'] = int(lin([(T_PAGER + 0.7, 1), (T_PRE1, 2), (T_LOOKED + 1.2, 12), (T_CH1 + 2, 47), (T_LAST1, 99)], t))
    elif t < T_BRIDGE: S['phone'] = 'alerts'; S['n_alerts'] = 99
    elif t < T_REVERT: S['phone'] = 'onebar'; S['push'] = sstep(T_ONEBAR, T_ONEBAR + 2.4, t)
    elif t < T_GG: S['phone'] = 'dark'
    elif t < T_QUESTION - 0.1: S['phone'] = 'green'
    elif t < T_FINAL + 1.5: S['phone'] = 'question'
    else: S['phone'] = 'dark'
    # mirror (16:9)
    S['mirror_col'] = WD.pal('sky_hor', S['tod']) * 0.6 + WD.pal('sky_mid', S['tod']) * 0.4
    S['mirror_glow'] = max(sstep(T_CH1, T_CH1 + 1, t) * (1 - sstep(T_V2, T_V2 + 1, t)), sstep(T_CH2, T_CH2 + 1, t) * (1 - sstep(T_CH2_END, T_CH2_END + 1, t)))
    if T_ROOT <= t < T_459B + 0.3: S['mirror_text'] = 'me'; S['mirror_text_op'] = sstep(T_ROOT + 0.6, T_ROOT + 0.8, t) * (1 - sstep(T_459B, T_459B + 0.3, t))
    # ring
    for tr, t_end, cut in ((T_ROPE1, T_V2 - 0.3, None), (T_ROPE2, T_CH2_END - 0.2, None), (T_CUT - 0.4, T_CUTW + 1.2, T_CUTW)):
        if tr - 0.05 <= t <= t_end:
            k = sstep(tr - 0.05, tr + 0.55, t)
            hang = sstep(tr + 0.55, tr + 0.9, t)
            op = 1.0
            if cut is not None and t > cut:
                op = 1 - sstep(cut, cut + 0.7, t)
            elif t > t_end - 0.5: op = 1 - sstep(t_end - 0.5, t_end, t)
            S['ring'] = dict(k=k, hang=hang, op=op, drop=(t - cut) if (cut is not None and t > cut) else 0.0)
    # road effects
    S['chevrons'] = sstep(T_ROWS, T_ROWS + 0.4, t) * (1 - sstep(T_RETRY - 0.2, T_RETRY + 0.3, t))
    if T_PIPE - 0.1 <= t <= T_CACHE + 0.5:
        S['pipeline'] = (lin([(T_PIPE, 0.08), (T_WHOOSH - 0.1, 0.35), (T_WHOOSH + 0.4, 1.0)], t), 'pipeline')
    S['whoosh'] = sstep(T_WHOOSH - 0.1, T_WHOOSH + 0.15, t) * (1 - sstep(T_WHOOSH + 0.6, T_WHOOSH + 1.4, t))
    S['uturn'] = clamp((t - (T_UTURN - 0.45)) / 0.9)
    S['flip'] = -1.0 if t >= T_UTURN else 1.0
    # low tide at the overlook: the beach widens and the seabed shows
    S['lowtide'] = sstep(T_STOP + 1.0, T_BRIDGE + 1.5, t) * (1 - sstep(T_UTURN - 0.3, T_UTURN + 0.3, t))
    # the dip for the graph
    S['pitch'] = (math.sin(clamp((t - T_GRAPH) / (T_BACK + 0.6 - T_GRAPH)) * math.pi) * 0.09) if T_GRAPH <= t <= T_BACK + 0.6 else 0.0
    S['bounce'] = math.sin((t - T_BOUNCE) * 22) * math.exp(-(t - T_BOUNCE) * 4) * 0.035 if t >= T_BOUNCE else 0.0
    S['headlights'] = 1.0
    S['center_solid'] = False
    S['fade'] = sstep(T_BLACK - 0.1, T_BLACK + 0.2, t) * (1 - sstep(T_CLOSE - 0.05, T_CLOSE + 0.35, t))
    S['gg'] = sstep(T_GG - 0.1, T_GG + 0.3, t) * (1 - sstep(T_CLOSE, T_CLOSE + 1, t))
    S['loop_flash'] = math.exp(-max(0.0, t - T_459B) * 9) if t >= T_459B else 0.0
    return S


# ------------------------------------------------------------------ objects along the road
def D_at(t_hit, ahead=0.0): return dist(t_hit) + ahead
OBJ = []
def add(o):
    if o.emissive == 0.0 and o.rgba.shape[1] > 200: o.emissive = 0.35   # signs are retro-reflective: they read at night
    OBJ.append(o); return o
R = WD.RoadObject

# the office gate, both ends of the loop
D0 = 0.0; D_END = dist(T_459B + 2.0)
for base, t0, t1 in ((D0, -1, T_V1 + 2), (D_END, T_ROOT - 2, 1e9)):
    add(R(base + 5.0, 1.15, SP.gate(0.0), 3.2, t0=t0, t1=t1, name='gate'))
    add(R(base + 9.5, 3.0, SP.sign(["EMPLOYEE", "PARKING"], 'notice', 2.6, 3.4), 3.4, t0=t0, t1=t1))
    add(R(base + 16.0, 9.5, SP.office('ACME CLOUD', 9.0, 8.0, 0.45), 9.0, t0=t0, t1=t1))
    add(R(base + 9.0, -3.4, SP.palm(1), 5.5, t0=t0, t1=t1)); add(R(base + 20.0, -3.0, SP.palm(2), 5.0, t0=t0, t1=t1))
GATE = [o for o in OBJ if o.name == 'gate']

add(R(D_at(17.6), 3.4, SP.sign(["MAIN ST", "merge"], 'guide', 3.4, 3.8, arrow='up'), 3.8, t1=T_V1 + 4))
add(R(D_at(T_CHANGE + 0.9), 3.2, SP.sign(["ONE LITTLE", "CHANGE"], 'warn', 3.2, 4.2), 4.2))
add(R(D_at(T_NOTICKET + 0.75), 3.0, SP.sign(["NO TICKET"], 'no', 2.6, 4.0), 4.0))
add(R(D_at(T_NOTEST + 0.75), 3.0, SP.sign(["NO TEST"], 'no', 2.6, 4.0), 4.0))
add(R(D_at(T_NOEYES + 0.65), 3.0, SP.sign(["NO SECOND", "PAIR OF EYES"], 'no', 2.9, 4.0), 4.0))
add(R(D_at(T_GREEN + 1.3), 2.7, SP.traffic_light('green', True), 5.0, glow=(0.9, 0.5, 0.0, hexc('39e07a')), emissive=0.6))
add(R(D_at(T_MERGE + 1.3), 3.4, SP.sign(["MERGE", "→ MAIN"], 'exit', 3.4, 3.9, arrow='right'), 3.9))
for k, tt in enumerate(np.arange(T_V1 - 2, T_CH1, 3.1)):
    add(R(D_at(tt), -3.3 if k % 2 else 3.6, SP.palm(k % 5), 5.6 if k % 2 else 4.8))
add(R(D_at(T_CH1 + 1.2), 3.3, SP.sign(["HIGH TIDE", "AHEAD"], 'warn', 3.2, 4.2), 4.2))
add(R(D_at(T_UNDER1 + 1.4), 3.2, SP.sign(["NO", "LIFEGUARD"], 'no', 2.8, 4.0), 4.0))
add(R(D_at(T_NEVER1 + 2.4), 4.4, SP.sign(["NEVER AGAIN", "said that last Friday"], 'bill', 6.0, 4.6, sub='#deploys'), 4.6))
add(R(D_at(T_LAST1 + 2.4), 4.4, SP.sign(["LAST FRIDAY", "never again"], 'bill', 6.0, 4.6, sub='and the one before'), 4.6))
# night: the pier of Slack channels on the ocean side, streetlights on the land side
for k, ch in enumerate(("#incidents", "#prod-alerts", "#general", "#eng", "#on-call", "#checkout", "#war-room", "#help")):
    d = D_at(T_V2 + 1.0 + k * 1.6)
    add(R(d, -6.2, SP.pier(), 4.0, t0=T_V2 - 8, t1=T_CH2_END + 10))
    col = [SP.NEON, (255, 170, 60), (120, 220, 255), (120, 255, 170)][k % 4]
    add(R(d + 1.0, -4.4, SP.neon(ch, col), 1.4, glow=(0.5, 0.55, 0.25, hexc('%02x%02x%02x' % col)), emissive=1.0, t0=T_V2 - 8, t1=T_CH2_END + 10))
for k, tt in enumerate(np.arange(T_V2 - 6, T_STOP, 2.2)):
    add(R(D_at(tt), 3.2, SP.streetlight(), 5.0, glow=(0.97, 0.3, 0.35, hexc('ffd890')), emissive=0.8, t0=T_V2 - 12, t1=T_REVERT))
add(R(D_at(T_ANYONE + 1.3), 4.6, SP.sign(["anyone change", "something?"], 'bill', 6.0, 4.6, sub='#incidents · 2 min ago'), 4.6))
add(R(D_at(T_NULL + 1.6), 6.0, SP.bank(6.0, 6.0, '$ $ $'), 6.0, t1=T_NULL + 0.1, emissive=0.3))
add(R(D_at(T_NULL + 1.6), 6.0, SP.bank(6.0, 6.0, 'NULL'), 6.0, t0=T_NULL + 0.1, emissive=0.3))
QUEUE = []
for k, (lat, col) in enumerate(((-0.9, (70, 72, 84)), (0.9, (120, 40, 44)), (-0.85, (60, 90, 120)), (0.95, (180, 160, 120)), (-0.9, (90, 70, 110)))):
    o = add(R(0.0, lat, SP.car_rear(col, 'RETRY' if k % 2 == 0 else 'RETRY-%d' % (k + 1)), 1.56, glow=(0.45, 0.5, 0.25, hexc('ff3b3b')), emissive=0.55, t0=T_RETRY - 0.4, t1=T_VP1 + 4))
    o.q = (6.0 + k * 3.2); QUEUE.append(o)
for k in range(3):
    add(R(D_at(T_DEAD + 0.9 + k * 0.7), 2.5 + 0.3 * k, SP.envelopes(12 + 4 * k, k), 1.6))
add(R(D_at(T_VP1 + 1.1), 4.6, SP.sign(["VP is typing", "• • •"], 'bill', 6.0, 4.6, sub='#incidents'), 4.6, t1=T_VPSTOP))
add(R(D_at(T_VP1 + 1.1), 4.6, SP.sign(["VP is typing", " "], 'bill', 6.0, 4.6, sub='#incidents'), 4.6, t0=T_VPSTOP, t1=T_VP2))
add(R(D_at(T_VP2 + 2.0), 4.6, SP.sign(["VP:", "who deployed?"], 'bill', 6.0, 4.6, sub='#incidents · just now'), 4.6, t0=T_DROP - 0.2))
add(R(D_at(T_CH2 + 1.2), 3.3, SP.sign(["HIGH TIDE", "AGAIN"], 'warn', 3.2, 4.2), 4.2))
add(R(D_at(T_NEVER2 + 2.4), 4.4, SP.sign(["NEVER AGAIN", "(again)"], 'bill', 6.0, 4.6, sub='#deploys'), 4.6))
add(R(D_at(T_LAST2 + 2.4), 4.4, SP.sign(["LAST FRIDAY", "never again"], 'bill', 6.0, 4.6, sub='and the one before that'), 4.6))
add(R(D_at(T_CH2_END + 2.6), 3.4, SP.sign(["SCENIC", "OVERLOOK"], 'guide', 3.4, 3.8, arrow='right'), 3.8))
add(R(D_at(T_STOP - 1.0), 2.3, SP.cone(), 1.05)); add(R(D_at(T_STOP - 1.0) + 2.0, 2.5, SP.cone(), 1.05))
add(R(D_at(T_STOP) + 9.0, 4.6, SP.sign(["PARKING LOT", "one bar of signal"], 'notice', 3.2, 3.6), 3.6, t0=T_STOP - 20, t1=T_UTURN))
# the seabed at low tide (ahead and to the left while parked)
D_PARK = dist(T_STOP)
for k, (txt, z, lat) in enumerate((("TODO", 5.0, -3.1), ("// temporary", 7.5, -4.2), ("hardcoded", 10.5, -3.3), ("hack", 13.5, -4.4), ("skip tests", 17, -3.4), ("string", 21, -4.2), ("shortcut", 26, -3.2), ("??", 32, -4.0))):
    add(R(D_PARK + z, lat, SP.small_sign(txt, 1.5, 1.4), 1.5, t0=T_BRIDGE - 1, t1=T_UTURN))
    add(R(D_PARK + z + 1.3, lat - 1.1, SP.rock(k, 1.6 + 0.4 * (k % 3)), 0.55 + 0.15 * (k % 3), t0=T_BRIDGE - 1, t1=T_UTURN))
# after the U-turn: the way back
add(R(D_at(T_CHERRY + 0.9), 3.3, SP.sign(["cherry-pick"], 'guide', 3.4, 3.6), 3.6, t0=T_UTURN))
add(R(D_at(T_PUSH + 0.8), 3.3, SP.sign(["PUSH"], 'guide', 3.0, 3.6, arrow='up'), 3.6, t0=T_UTURN))
add(R(D_at(T_CACHE + 1.0), 3.3, SP.sign(["CACHE", "STILL WARM"], 'warn', 3.2, 4.2), 4.2, t0=T_UTURN))
for k, tt in enumerate(np.arange(T_UTURN + 1, T_FINAL, 2.6)):
    add(R(D_at(tt), 3.3 if k % 2 else -3.4, SP.palm(k % 5), 5.4, t0=T_UTURN))
for k in range(3):
    add(R(D_at(T_GG + 0.6 + k * 0.45), 2.7 if k % 2 == 0 else -2.7, SP.traffic_light('green', False), 5.0, glow=(0.9, 0.5, 0.0, hexc('39e07a')), emissive=0.6, t0=T_UTURN))
add(R(D_at(T_STANDING + 3.0), -5.6, SP.lighthouse('PROD', True), 12.0, glow=(0.93, 0.3, 0.3, hexc('ffe9a0')), emissive=0.35, t0=T_FINAL - 2))
add(R(D_at(T_MONDAY + 1.4), 4.4, SP.sign(["MONDAY:", "POSTMORTEM"], 'bill', 6.0, 4.6, sub='blameless · nope'), 4.6, t0=T_UTURN))
add(R(D_at(T_NEVER3 + 2.8), 4.4, SP.sign(["NEVER AGAIN"], 'bill', 6.0, 4.6, sub='see you next Friday'), 4.6, t0=T_UTURN))
add(R(D_at(T_NEXT + 2.0), 3.4, SP.sign(["NEXT FRIDAY"], 'exit', 3.4, 3.9, arrow='right'), 3.9, t0=T_UTURN))


def update_dynamic(t, V):
    """Objects that move with the car: the queue of RETRY cars, the gate's arm."""
    for o in QUEUE:
        if t < T_VP1 + 1.5: o.d = V.D + o.q
        else: o.d = V.D + o.q + (t - T_VP1 - 1.5) ** 2 * 9.0
    lift = sstep(T_IT + 0.25, T_IT + 1.4, t) if t < T_459B else 0.0
    GATE[0].rgba = SP.gate(lift); GATE[1].rgba = SP.gate(0.0)


# ------------------------------------------------------------------ frame
def render_frame(t, W, H, fi):
    t = float(t); S = story(t); vert = H > W; ts = min(W, H) / 1080
    D = dist(t)
    fl = S['flood']
    bob = math.sin(t * 2.1) * H * 0.012 * fl / 0.9 + math.sin(t * 3.7) * H * 0.004 * fl / 0.9
    bob += S['bounce'] * H
    bob += math.sin(t * 37) * H * 0.0012 * clamp(speed(t) / 10)   # engine
    pitch = S['pitch'] * H
    u = S['uturn']; pan = (W * 1.4 * ease(u / 0.5)) if u < 0.5 else (-W * 1.4 * (1 - ease((u - 0.5) / 0.5)))
    V = WD.View(W, H, D, TRACK, bob=bob, pitch=pitch, flip=S['flip'], pan=pan)
    update_dynamic(t, V)
    img = np.empty((H, W, 3), np.float32)
    WD.sky(img, V, t, S)
    WD.hills(img, V, t, S)
    WD.ground(img, V, t, S)
    WD.flood(img, V, t, S)
    WD.draw_objects(img, V, t, S, OBJ)
    if S['whoosh'] > 0.01: WD.motion_streaks(img, V, S['whoosh'])
    if 0.01 < S['uturn'] < 0.99: WD.motion_streaks(img, V, math.sin(S['uturn'] * math.pi) ** 0.5 * 1.0)
    # inside the car
    L = DS.lay(W, H)
    DS.frame_glass(img, t, W, H, L, S)
    DS.dashboard(img, t, W, H, L, S)
    DS.ring(img, t, W, H, L, S)
    DS.interior_water(img, t, W, H, L, S['interior'], WD.pal('sea_near', S['tod']))
    # lyrics above the dashboard
    TY.lyrics(img, t, W, H, TM, hide=lambda L_: L_['sec'] in ('INTRO', 'OUTRO'), band=0.35)
    # kinetic type on the windshield: 4:59, the SHIP IT, the chorus hits
    for t0, text, dur in ((T_459, "4:59", 2.2), (T_459B, "4:59", 2.8), (T_ROOT, "root cause: me", 1.6)):
        if t0 <= t < t0 + dur:
            k = (t - t0) / dur
            DS.hud_word(img, t, W, H, text, sstep(0, 0.06, k) * (1 - sstep(0.82, 1.0, k)), y=(0.28 if text == "4:59" else 0.2) if not vert else 0.22, size=0.15 if text == "4:59" else 0.07, col=DS.CREAM, glow=hexc('ffb547'))
    if T_SHIP - 0.1 <= t < T_IT + 2.6:
        k = (t - T_SHIP + 0.1) / (T_IT + 2.6 - T_SHIP + 0.1)
        DS.hud_word(img, t, W, H, "SHIP IT" if t < T_IT + 0.1 else "deploying…" if t < T_IT + 2.4 else "deployed", sstep(0, 0.04, k) * (1 - sstep(0.9, 1.0, k)),
                    y=0.30 if not vert else 0.22, size=0.11, col=hexc('3ddc84') if t < T_IT + 0.1 else DS.CREAM, glow=hexc('3ddc84'), mono=False, x=0.40 if not vert else 0.5)
    if S['gg'] > 0.01: img += S['gg'] * 0.10 * hexc('39e07a')
    if S['fade'] > 0.01: img *= (1 - 0.92 * S['fade'])
    if S['loop_flash'] > 0.01: img += S['loop_flash'] * 0.8 * hexc('ffe6b0')
    # the subscribe pill (16:9) after the first chorus; the end card
    C.subscribe_pill(img, t, W, H, T_V2 + 0.3, 5.0)
    if t > T_END - 0.2:
        C.end_screen(img, t, W, H, T_END, DUR - T_END, "See you next Friday.", title="Deployed on a Friday")
    return C.finish(img, t, fi, DUR, ca=0.0012)
