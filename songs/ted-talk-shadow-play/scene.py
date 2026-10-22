"""TED Talk as a shadow play: cut-paper puppets behind a lamp-lit paper screen.

The standup is a row of silhouettes. The narrator is the girl with the red hair clip (the only colour on stage: a
scrap of red gel the lamp shines through). When Ted says "so — stepping back" he literally steps back from the paper,
toward the lamp, and his shadow grows huge and soft over everyone. At the bridge she stands up, steps forward, and
he shrinks back to size. In the outro he takes it offline: he walks off, and the lamp goes out.
"""
import os, sys, math
from functools import lru_cache
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path: sys.path.insert(0, HERE)
from studio import core as C
from studio.core import sstep, ease_out, ease_io, clamp, lerp, hexc
import puppets as PP
import props as PR
import stage as ST

TM = C.Timing(HERE)
TAIL = 3.0
DUR = TM.duration + TAIL
F32 = np.float32
lt = TM.line_t
def wt(sub, w, nth=0):
    try: return TM.word_t(sub, w, nth)
    except Exception: return lt(sub, nth)
def le(sub, nth=0):
    L = [l for l in TM.lines if sub.lower() in l['text'].lower()][nth]; return L['e']

FONT = lambda n: os.path.join(C.FONTS, n)
F_LYR = FONT("EBGaramond-SemiBold.ttf"); F_SC = FONT("PlayfairDisplaySC-Regular.ttf"); F_ITAL = FONT("CormorantGaramond-MediumItalic.ttf")
CREAM = hexc('f6e7c8'); RED = hexc('e0352b'); EMBER = np.array([1.0, 0.45, 0.12], F32)

# ---------------------------------------------------------------- key times
T_V1 = lt("He doesn't answer"); T_RESP = lt("He responds"); T_DIFF = lt("difference"); T_FOUR = wt("about four minutes", "four")
T_ASK = lt("I asked him"); T_SO = wt("He said, so", "so"); T_STEP = wt("He said, so", "stepping"); T_DIM = lt("Somebody dim")
T_SIT = lt("everybody sit"); T_CH1 = TM.section("CH1")["s"]
TT = [L['s'] for L in TM.lines if L['text'].startswith("It's a Ted talk") or L['text'].startswith("It's always")]
T_18 = [lt("Eighteen minutes", i) for i in (0, 1)]; T_SLIDES = [wt("Eighteen minutes", "slides,", i) for i in (0, 1)]
T_POINT = [wt("Eighteen minutes", "point.", i) for i in (0, 1)]
T_FATHER = [lt("story about his father", i) for i in (0, 1)]; T_PAUSE = [wt("pause he thinks", "pause", i) for i in (0, 1)]
T_PAUSE_E = [le("pause he thinks", i) for i in (0, 1)]
T_CIRCLE = [lt("circle back", i) for i in (0, 1)]; T_CIRCLE_E = [le("circle back", i) for i in (0, 1)]
T_RAFTER = [lt("right after the part", i) for i in (0, 1)]; T_BELIEVE_E = [le("nobody believed", i) for i in (0, 1)]
T_V2 = TM.section("V2")["s"]; T_SOw = wt("He starts every", "so."); T_RIGHT = wt("He ends every", "right?")
T_REALQ = lt("He says, the real"); T_REAL = wt("He says, the real", "real"); T_ABOUTQ = lt("about the question")
T_JOURNEY = wt("He said journey", "journey."); T_UNLOCK = wt("He said journey", "unlock."); T_STORY = lt("let me tell you")
T_STORYw = wt("let me tell you", "story,"); T_CAL = lt("and I watched my calendar"); T_GIVEUP = lt("give up")
T_CH2 = TM.section("CH2")["s"]; T_STOP = TM.section("BRIDGE")["s"]; T_TED = lt("Ted."); T_STANDUP = lt("This is a standup")
T_FIFTEEN = lt("It is fifteen"); T_EIGHT = lt("for eight people"); T_SIX = lt("You have used six"); T_HARD = lt("Dana had a hard stop")
T_HAS = lt("Dana has had"); T_TWO = lt("for two years"); T_GHOST = lt("Dana is a ghost"); T_DIDTHAT = lt("You did that")
T_FINAL = TM.section("FINAL")["s"]; T_NOSCHED = lt("Nobody scheduled"); T_NOEND = lt("Nobody can end"); T_NOQA = lt("There's no Q")
T_NOA = lt("because there's no A"); T_NEVERQ = lt("because there was never"); T_ANYWAY = lt("Anyway"); T_HESAYS = lt("He says.")
T_HAVING = lt("Having taken"); T_PLACE = lt("Into a place"); T_REACH = lt("none of us"); T_END = 157.2
T_PILL = T_V2 + 0.3
TT_E = [L['e'] for L in TM.lines if L['text'].startswith("It's a Ted talk") or L['text'].startswith("It's always")]
LIFT = [TT_E[0] + 0.05, TT_E[1] + 0.05, TT_E[2] + 0.05, TT_E[3] + 0.05, TT_E[4] - 0.15, None, T_ANYWAY + 1.5]
# the wall props (calendar, clock) are hoisted out on their strings whenever the talk takes over the stage
CAL_OUT = [(TT[0], LIFT[1]), (TT[2], LIFT[3]), (TT[4], LIFT[4]), (T_NOQA - 0.3, 1e9)]
CLOCK_OUT = [(TT[0], LIFT[0]), (TT[1], T_BELIEVE_E[0]), (TT[2], LIFT[2]), (TT[3], 1e9)]
def fly(t, ivs):
    """0 = on the wall, 1 = hoisted out of sight"""
    k = 0.0
    for a, b in ivs:
        k = max(k, ease_io((t - (a - 0.42)) / 0.45) * (1 - ease_io((t - (b + 0.42)) / 0.5)))
    return k

SCALE = 560.0                                     # an adult puppet's height in world units
LEFT = [("Jo", 205), ("Lee", 360), ("Sam", 515)]
RIGHT = [("Dana", 1330), ("Priya", 1500), ("Marcus", 1690)]
ME_X = 700.0; TED_X = 1010.0

# ---------------------------------------------------------------- the story, as functions of time
def giant(t):
    """how far Ted has stepped back toward the lamp: 1 = against the paper, ~2 = huge and soft"""
    g = 1.0
    g += 0.95 * ease_io((t - T_STEP) / 1.0) * (1 - ease_io((t - (T_V2 - 0.2)) / 1.6))           # first "stepping back"
    g += 1.10 * ease_io((t - (TT[2] - 0.5)) / 0.9) * (1 - ease_io((t - (T_STANDUP - 0.05)) / 0.45))  # second chorus
    g += 1.05 * ease_io((t - (TT[4] - 0.4)) / 0.8) * (1 - ease_io((t - (T_HAVING + 2.0)) / 0.1) * 0)  # final
    for a, b in ((T_CIRCLE[0], T_CIRCLE_E[0]), (T_CIRCLE[1], T_CIRCLE_E[1])):   # circling back: nearer, farther, nearer
        if a <= t <= b + 0.3:
            k = clamp((t - a) / (b - a)); g += 0.45 * math.sin(k * 2 * math.pi) * (1 - k) ** 0.3
    return g

def lamp(t):
    """(level, spot amount, flicker)"""
    level = lerp(0.55, 1.0, ease_out(t / 2.2))
    spot = 0.62 * sstep(T_DIM, T_DIM + 1.4, t) * (1 - sstep(T_TED + 0.5, T_STANDUP + 0.3, t))
    spot = max(spot, 0.55 * sstep(T_FINAL + 0.8, T_FINAL + 2.0, t) * (1 - sstep(T_ANYWAY, T_ANYWAY + 2.0, t)))
    level *= 1 - 0.25 * sstep(T_DIM, T_DIM + 1.4, t) * (1 - sstep(T_STANDUP, T_STANDUP + 0.3, t))
    level *= 1 - 0.80 * sstep(T_PLACE, T_REACH + 1.5, t)          # taken offline: the lamp goes down
    fl = 0.05 * (1 - sstep(0, 2.2, t)) + 0.06 * sstep(T_TED - 0.1, T_TED, t) * (1 - sstep(T_STANDUP, T_STANDUP + 0.2, t)) + 0.05 * sstep(T_HAVING, T_PLACE, t)
    return level, spot, fl

def curtains(t):
    k = ease_io((t - 0.5) / 2.6)
    k *= 1 - 0.38 * sstep(T_NOEND, T_NOEND + 0.9, t) * (1 - sstep(T_NOEND + 1.3, T_NOEND + 2.0, t))   # Nobody can end it
    k *= 1 - ease_io((t - (T_REACH + 0.6)) / 3.4)                                                     # the end
    return k

def talking(t):
    """Ted's mouth"""
    quiet = any(a - 0.05 < t < b for a, b in ((T_PAUSE[0], T_PAUSE_E[0]), (T_PAUSE[1], T_PAUSE_E[1]), (T_TED, T_STANDUP + 3.0),
                                              (T_HAS - 2, T_DIDTHAT + 1.5)))
    if quiet or t < 1.5 or t > T_HAVING + 1: return 0.0
    return 0.35 + 0.35 * math.sin(t * 2 * math.pi * 4.1) + 0.3 * math.sin(t * 2 * math.pi * 6.7 + 1)

def ted_state(t):
    """x, facing, pose for Ted"""
    beat = math.sin(t * 2 * math.pi * 143.55 / 60 / 2)
    x = TED_X; f = -1
    p = PP.Pose(mouth=max(0, talking(t)))
    # default: a speaker's gestures, on the beat
    g = sstep(T_V1, T_V1 + 0.6, t)
    p.sh_f = 0.25 + g * (0.75 + 0.45 * beat); p.el_f = 0.35 + g * (0.6 - 0.3 * beat)
    p.sh_b = -0.05 + g * (0.35 - 0.25 * beat); p.el_b = 0.3 + g * 0.5
    p.head = -0.05 + 0.04 * math.sin(t * 1.7)
    # "so —": both hands up; "stepping back": two steps backward
    k_so = sstep(T_SO - 0.05, T_SO + 0.15, t) * (1 - sstep(T_STEP + 0.9, T_STEP + 1.3, t))
    p.sh_f = lerp(p.sh_f, 2.3, k_so); p.el_f = lerp(p.el_f, 0.2, k_so); p.sh_b = lerp(p.sh_b, 2.0, k_so); p.el_b = lerp(p.el_b, 0.25, k_so)
    ks = clamp((t - T_STEP) / 1.0)
    if 0 < ks < 1:
        ph = ks * 2 * math.pi * 2
        p.hip_f = 0.30 * math.sin(ph); p.hip_b = -0.30 * math.sin(ph); p.kn_f = 0.25 * max(0, math.cos(ph)); p.kn_b = 0.25 * max(0, -math.cos(ph))
    # the pause he thinks is powerful: one finger raised, frozen
    for a, b in zip(T_PAUSE, T_PAUSE_E):
        k = sstep(a - 0.1, a + 0.1, t) * (1 - sstep(b, b + 0.4, t))
        if k > 0:
            p.sh_f = lerp(p.sh_f, 2.6, k); p.el_f = lerp(p.el_f, 0.15, k); p.sh_b = lerp(p.sh_b, -0.05, k); p.el_b = lerp(p.el_b, 0.4, k); p.head = lerp(p.head, -0.25, k)
    # circling back: he walks a loop (facing changes on the far side)
    for a, b in zip(T_CIRCLE, T_CIRCLE_E):
        if a <= t <= b + 0.3:
            k = clamp((t - a) / (b - a)); th = k * 2 * math.pi
            x = TED_X + 320 * math.sin(th) * (1 - 0.0 * k)
            f = -1 if math.cos(th) > 0 else 1
            ph = (t - a) * 2 * math.pi * 1.6
            p.hip_f = 0.32 * math.sin(ph); p.hip_b = -0.32 * math.sin(ph); p.kn_f = 0.3 * max(0, math.cos(ph)); p.kn_b = 0.3 * max(0, -math.cos(ph))
    kk = sstep(T_JOURNEY - 0.45, T_JOURNEY - 0.15, t) * (1 - sstep(T_STORY - 0.35, T_STORY - 0.05, t))
    if kk > 0: p.sh_f = lerp(p.sh_f, 1.45, kk); p.el_f = lerp(p.el_f, 0.36 + 0.04 * math.sin(t * 5), kk); p.head = lerp(p.head, -0.1, kk)
    kbk = sstep(T_STORY - 0.2, T_STORY + 0.2, t) * (1 - sstep(T_CAL + 0.4, T_CAL + 1.0, t))
    if kbk > 0: p.sh_f = lerp(p.sh_f, 1.05, kbk); p.el_f = lerp(p.el_f, 0.75, kbk); p.sh_b = lerp(p.sh_b, 1.05, kbk); p.el_b = lerp(p.el_b, 0.75, kbk); p.head = lerp(p.head, 0.2, kbk)
    # the bridge: frozen at "Ted.", then shrinking back; "You did that": head down
    kb = sstep(T_TED - 0.05, T_TED + 0.1, t) * (1 - sstep(T_FINAL - 0.3, T_FINAL + 0.4, t))
    if kb > 0:
        p.sh_f = lerp(p.sh_f, 0.15, kb); p.el_f = lerp(p.el_f, 0.3, kb); p.sh_b = lerp(p.sh_b, -0.1, kb); p.el_b = lerp(p.el_b, 0.2, kb)
        p.head = lerp(p.head, 0.25 * sstep(T_DIDTHAT, T_DIDTHAT + 0.6, t), kb); p.slump = 0.6 * sstep(T_DIDTHAT, T_DIDTHAT + 0.6, t) * kb
    # "Nobody can end it": he holds the curtains open
    kc = sstep(T_NOEND, T_NOEND + 0.5, t) * (1 - sstep(T_NOEND + 2.2, T_NOEND + 2.8, t))
    if kc > 0: p.sh_f = lerp(p.sh_f, 1.55, kc); p.el_f = lerp(p.el_f, 0.05, kc); p.sh_b = lerp(p.sh_b, 1.4, kc); p.el_b = lerp(p.el_b, 0.1, kc)
    # the outro: a bow, then he walks off to the right
    kbow = sstep(T_ANYWAY + 1.5, T_ANYWAY + 2.2, t) * (1 - sstep(T_HESAYS, T_HESAYS + 0.5, t))
    if kbow > 0: p.lean = lerp(p.lean, -0.6, kbow); p.head = lerp(p.head, 0.3, kbow); p.sh_f = lerp(p.sh_f, 0.1, kbow); p.sh_b = lerp(p.sh_b, -0.3, kbow)
    kw = clamp((t - T_HAVING) / 3.4)
    if kw > 0:
        f = 1; x = TED_X + 1500 * ease_io(kw) ** 1.2
        ph = (t - T_HAVING) * 2 * math.pi * 1.4
        p.hip_f = 0.35 * math.sin(ph); p.hip_b = -0.35 * math.sin(ph); p.kn_f = 0.3 * max(0, math.cos(ph)); p.kn_b = 0.3 * max(0, -math.cos(ph))
        p.sh_f = 0.3 * math.sin(ph + math.pi); p.sh_b = 0.3 * math.sin(ph); p.el_f = 0.3; p.el_b = 0.3; p.mouth = 0
    return x, f, p

def me_state(t):
    x = ME_X; p = PP.Pose(head=0.02 * math.sin(t * 1.3 + 2))
    # hand up with a question
    kq = sstep(T_V1 - 0.2, T_V1 + 0.3, t) * (1 - sstep(T_RESP + 1.6, T_RESP + 2.3, t))
    p.sh_f = lerp(p.sh_f, 2.75, kq); p.el_f = lerp(p.el_f, 0.15, kq)
    # holding up the file
    kf = sstep(T_ASK - 0.1, T_ASK + 0.4, t) * (1 - sstep(T_STEP + 0.4, T_STEP + 1.0, t))
    x += 70 * kf * (1 - sstep(T_DIM, T_SIT + 0.5, t))
    p.sh_f = lerp(p.sh_f, 1.55, kf); p.el_f = lerp(p.el_f, 0.55, kf)
    # the real question: holding her little ? up again
    kr = sstep(T_REALQ - 0.3, T_REALQ + 0.1, t) * (1 - sstep(T_REAL + 0.2, T_REAL + 0.5, t))
    p.sh_f = lerp(p.sh_f, 1.6, kr); p.el_f = lerp(p.el_f, 0.4, kr)
    kp = sstep(T_ABOUTQ, T_ABOUTQ + 0.4, t) * (1 - sstep(T_ABOUTQ + 3.0, T_ABOUTQ + 3.6, t))   # pointing down at her dropped ?
    p.sh_f = lerp(p.sh_f, 0.9, kp); p.el_f = lerp(p.el_f, -0.4, kp); p.head = lerp(p.head, 0.25, kp)
    sit = sstep(T_SIT, T_SIT + 0.8, t) * (1 - sstep(T_TED - 0.1, T_TED + 0.5, t)) + sstep(T_FINAL + 1.0, T_FINAL + 1.8, t)
    p.sit = min(1, sit)
    # the bridge: she stands, steps forward, points at "You did that"
    kfw = sstep(T_TED + 0.1, T_STANDUP + 0.6, t) * (1 - sstep(T_FINAL + 0.4, T_FINAL + 1.2, t))
    x += 120 * kfw
    if 0 < kfw < 1:
        ph = kfw * 2 * math.pi * 1.5
        p.hip_f = 0.3 * math.sin(ph); p.hip_b = -0.3 * math.sin(ph); p.kn_f = 0.25 * max(0, math.cos(ph))
    kgest = sstep(T_FIFTEEN, T_FIFTEEN + 0.4, t) * (1 - sstep(T_HARD, T_HARD + 0.4, t))
    p.sh_f = lerp(p.sh_f, 2.1, kgest); p.el_f = lerp(p.el_f, 0.6, kgest); p.head = lerp(p.head, -0.15, kgest)
    kpt = sstep(T_DIDTHAT - 0.1, T_DIDTHAT + 0.25, t) * (1 - sstep(T_FINAL - 0.2, T_FINAL + 0.5, t))
    p.sh_f = lerp(p.sh_f, 1.62, kpt); p.el_f = lerp(p.el_f, 0.0, kpt); p.hand_open = 0
    # the final: asleep in her chair? no — she keeps her question up until the end
    kq2 = sstep(T_NOQA - 0.2, T_NOQA + 0.4, t) * (1 - sstep(T_NEVERQ + 1.6, T_NEVERQ + 2.4, t))
    p.sh_f = lerp(p.sh_f, 2.6, kq2); p.el_f = lerp(p.el_f, 0.2, kq2)
    kend = sstep(T_REACH, T_REACH + 1.2, t)
    p.sh_f = lerp(p.sh_f, 2.5, kend); p.el_f = lerp(p.el_f, 0.25, kend)
    return x, 1, p

def crowd_state(name, x0, facing, i, t):
    p = PP.Pose(head=0.025 * math.sin(t * 1.1 + i * 1.7))
    bored = sstep(T_FOUR + i * 0.18, T_FOUR + 0.7 + i * 0.18, t) * (1 - sstep(T_ASK, T_ASK + 0.5, t))
    asleep = sstep(T_18[1] + i * 0.25, T_18[1] + 0.8 + i * 0.25, t) * (1 - sstep(T_TED, T_TED + 0.4, t))
    asleep = max(asleep, sstep(TT[5] + i * 0.2, TT[5] + 0.8 + i * 0.2, t))
    p.slump = max(bored, asleep, 0.55 * sstep(T_RESP, T_RESP + 4, t) * (1 - sstep(T_ASK, T_ASK + 0.5, t)) * (i % 2))
    p.sit = sstep(T_SIT + i * 0.06, T_SIT + 0.7 + i * 0.06, t)
    p.sh_f = 0.08 + 0.3 * (i % 3 == 1); p.el_f = 0.9 * (i % 3 == 1) + 0.2   # some hold a coffee
    x = x0
    if name == "Dana":
        kw = clamp((t - T_HARD) / 1.7)
        if kw > 0:
            p.sit = p.sit * (1 - sstep(0, 0.25, kw)); facing = 1
            x = x0 + 700 * sstep(0.2, 1.0, kw)
            ph = kw * 2 * math.pi * 3
            p.hip_f = 0.3 * math.sin(ph) * (kw > 0.2); p.hip_b = -0.3 * math.sin(ph) * (kw > 0.2); p.kn_f = 0.25 * max(0, math.cos(ph)) * (kw > 0.2)
    return x, facing, p

def dana_gone(t): return sstep(T_HARD + 1.6, T_HARD + 1.75, t)

# ---------------------------------------------------------------- drawing the stage
def put_puppet(L, cam, name, x, facing, pose, layer="crisp", g=1.0, extra_gel=None):
    pu = PP.CAST[name]
    polys, holes, gels, rods, anch = pu.parts(pose, x, ST.FLOOR, SCALE, facing)
    if g != 1.0:   # stepping back toward the lamp: the shadow grows about the lamp's centre and goes soft
        S = lambda P: ST.LAMP + (np.asarray(P) - ST.LAMP) * g
        polys = [S(p) for p in polys]; holes = [S(p) for p in holes]; gels = [(S(p), c) for p, c in gels]
        rods = [(S(a), S(b)) for a, b in rods]; anch = {k: S(v) for k, v in anch.items()}
        m = np.zeros((cam.H, cam.W), np.uint8)
        ST.fill(m, cam, polys); ST.fill(m, cam, holes, 0)
        for a, b in rods: ST.line(m, cam, a, b, 1.8 * g, 80)
        L.add_custom(m, 0.9 + 4.2 * (g - 1), 0.965 - 0.20 * (g - 1))
    else:
        m = L.mask(layer)
        ST.fill(m, cam, polys); ST.fill(m, cam, holes, 0)
        for a, b in rods: ST.line(m, cam, a, b, 1.6, 70)
    for gp, col in gels:
        gm = np.zeros((cam.H, cam.W), np.uint8); ST.fill(gm, cam, [gp]); L.add_gel(gm, col, 0.9 + 3 * (g - 1))
    return anch

def render_frame(t, W=1920, H=1080, fi=0):
    vert = H > W
    cam = ST.Cam(W, H, fx=focus_x(t) if vert else 960.0)       # only the 9:16 camera pans
    level, spot, fl = lamp(t)
    g = giant(t)
    tx, tf, tp = ted_state(t)
    spot_c = ST.LAMP + (np.array([tx, 600.0]) - ST.LAMP) * 1.0 if spot > 0 else None
    light = ST.screen_light(cam, t, level, spot, np.array([tx, 520.0]), 430.0 * g, fl)
    L = ST.Layers(W, H)
    draw_backdrop(L, cam, t)
    draw_props_back(L, cam, t)
    # the crowd (chairs first)
    st_sit = sstep(T_SIT, T_SIT + 0.7, t)
    tops = {}
    for i, (n, x0) in enumerate(LEFT + RIGHT):
        facing = 1 if (n, x0) in LEFT else -1
        x, f, p = crowd_state(n, x0, facing, i, t)
        if st_sit > 0:
            ST.fill(L.mask("near"), cam, [np.asarray(c) for c in PR.chair(x0 - facing * 20, facing, 0.95)])
        if n == "Dana": dana_chair(L, cam, x0 - facing * 20, t)
        if n == "Dana" and dana_gone(t) >= 1: continue
        a_ = put_puppet(L, cam, n, x, f, p, "crisp"); tops[n] = a_["top"]
        if p.slump > 0.6 and t > T_18[1]:
            ic = iris_circle(t, cam)
            for j, (c, s_, op) in enumerate(PR.zzz(a_["top"][0] + f * 30, a_["top"][1] + 10, t + i * 0.37, 2.2)):
                c = (c[0], a_["top"][1] + 10 - (a_["top"][1] + 10 - c[1]) * 0.55)
                if ic is not None and math.hypot(c[0] - ic[0][0], c[1] - ic[0][1]) < ic[1] + 45: continue   # not inside an open inset
                PR.stamp(L.mask("near"), cam, PR.glyph("Z" if j % 2 else "z", PR.F_SERIF, 120), c, s_ * min(1, op * 1.6))
    mx, mf, mp = me_state(t)
    if mp.sit > 0 and t < T_TED + 0.3 or t > T_FINAL + 0.5:
        ST.fill(L.mask("near"), cam, [np.asarray(c) for c in PR.chair(ME_X - 20, 1, 0.95)])
    a_me = put_puppet(L, cam, "Me", mx, mf, mp, "crisp")
    a_ted = put_puppet(L, cam, "Ted", tx, tf, tp, "crisp", g=g)
    tops["Me"] = a_me["top"]; tops["Ted"] = a_ted["top"]
    draw_props_front(L, cam, t, a_me, a_ted, g, tops)
    if hasattr(L, "lit_clip"):
        (cc, rr) = L.lit_clip; lm = np.zeros((H, W), np.uint8); PR.circle(lm, cam, cc, rr, 255)
        lm = cv2.GaussianBlur(lm.astype(F32) / 255.0, (0, 0), 2.0)[..., None]
        light = light * (1 - lm) + ST.screen_light(cam, t, 1.0, 0.0, None, 380.0, 0.0) * lm
    img = L.composite(light)
    # the ember glow of the burning Q (light through a burning edge)
    if hasattr(L, "ember"):
        e = cv2.GaussianBlur(L.ember.astype(F32) / 255.0, (0, 0), 2.5)
        img += e[..., None] * EMBER * 1.4 * level
    # the red clip keeps a little glow even as the lamp goes out
    k_last = sstep(T_PLACE, T_REACH + 1.5, t)
    if k_last > 0:
        c = cam.P(a_me["top"]) ; r = 26 * cam.s; R_ = int(r * 7)
        y0, y1 = max(0, int(c[1]) - R_), min(H, int(c[1]) + R_); x0, x1 = max(0, int(c[0]) - R_), min(W, int(c[0]) + R_)
        if y1 > y0 and x1 > x0:
            yy, xx = np.ogrid[y0:y1, x0:x1]
            glow = np.exp(-(((xx - c[0]) ** 2 + (yy - c[1]) ** 2) / (r * r * 4))).astype(F32)
            img[y0:y1, x0:x1] += (glow * k_last * 0.5)[..., None] * np.array([1.0, 0.12, 0.06], F32) * (1 - sstep(T_END + 1.5, DUR, t))
    # the curtains, valance and theatre
    curt = np.zeros((H, W), np.uint8); curt_h = np.zeros((H, W), np.uint8)
    ck = curtains(t)
    for side in ("left", "right"):
        polys, holes = PR.curtain(side, ck, t)
        ST.fill(curt, cam, polys)
        ST.fill(curt_h, cam, holes)
    ST.fill(curt, cam, PR.valance(t))
    ccol = np.array([0.10, 0.035, 0.025], F32)
    for (y0, y1, x0, x1) in curtain_rois(curt, H, W):
        a = cv2.GaussianBlur(curt[y0:y1, x0:x1].astype(F32) / 255.0, (0, 0), 1.0)[..., None]
        ah = cv2.GaussianBlur(curt_h[y0:y1, x0:x1].astype(F32) / 255.0, (0, 0), 1.2)[..., None]
        L_ = light[y0:y1, x0:x1]
        img[y0:y1, x0:x1] = img[y0:y1, x0:x1] * (1 - a) + (ccol + L_ * 0.06) * a + ah * a * L_ * 0.35   # light leaks through the folds
    pm, pcol, box = ST.proscenium(W, H)
    bx0, by0, bx1, by1 = [int(v) for v in box]; rr = int(0.03 * W) + 6
    for (y0, y1, x0, x1) in ((0, by0 + rr, 0, W), (by1 - 6, H, 0, W), (0, H, 0, bx0 + 6), (0, H, bx1 - 6, W)):
        p_ = pm[y0:y1, x0:x1, None]
        img[y0:y1, x0:x1] = img[y0:y1, x0:x1] * (1 - p_) + pcol[y0:y1, x0:x1] * p_
    sign(img, cam, t, light)
    lyrics(img, t, W, H)
    if not C.STATE["clean"]:
        C.subscribe_pill(img, t, W, H, T_PILL, 5.0)
        C.end_screen(img, t, W, H, T_END, DUR - T_END, "It's always a Ted talk.", sub_line="Subscribe for a new song every week",
                     title="TED Talk, a shadow play", accent=RED)
    return finish(img, t, fi)

def curtain_rois(m, H, W):
    """where the curtains and valance are: column bands at the sides and a band across the top"""
    cols = m.any(0); rows = m[:, W // 2 - 4:W // 2 + 4].any(1)
    out = []
    if cols.all():                      # closed (or nearly): the whole frame
        return [(0, H, 0, W)]
    # left band: from 0 to the last column of the leftmost run; right band likewise
    xs = np.flatnonzero(~cols)
    if xs[0] > 0: out.append((0, H, 0, min(W, xs[0] + 4)))
    if xs[-1] < W - 1: out.append((0, H, max(0, xs[-1] - 3), W))
    top = np.flatnonzero(rows)
    if len(top): out.append((0, min(H, top[-1] + 4), max(0, xs[0] - 3), min(W, xs[-1] + 4)))
    return out

def focus_x(t):
    """the 9:16 camera follows the action"""
    k = [(0, 860), (T_STEP, 860), (T_STEP + 1.2, 980), (T_V2, 980), (T_V2 + 1.5, 860), (T_CAL - 0.5, 860), (T_CAL + 0.3, 600),
         (T_GIVEUP + 0.8, 600), (T_GIVEUP + 1.6, 940), (T_HARD, 940), (T_HARD + 1.2, 1420), (T_GHOST + 2.5, 1420), (T_GHOST + 3.6, 900),
         (T_HAVING, 900), (T_HAVING + 1.5, 1150), (T_PLACE + 1.0, 1150), (T_PLACE + 3.0, 760), (DUR, 760)]
    for (a, va), (b, vb) in zip(k[:-1], k[1:]):
        if a <= t <= b: return lerp(va, vb, ease_io((t - a) / max(b - a, 1e-6)))
    return k[-1][1]

# ---------------------------------------------------------------- backdrop and props
def draw_backdrop(L, cam, t):
    deep = L.mask("deep")
    for (x, y, w, h) in ((150, 140, 255, 230), (1515, 140, 255, 230)):
        fr, holes = PR.window_blinds(x, y, w, h); ST.fill(deep, cam, fr); ST.fill(deep, cam, holes, 0)
    for x, s in ((70, 1.25), (1850, 1.3)):
        ST.fill(deep, cam, PR.plant(x, s, t))
    # the clock: four minutes in, then it never stops
    mins = 4.0 * ease_out((t - T_DIFF) / (T_FOUR - T_DIFF + 0.2)) if t > T_DIFF else 0.0
    if t > T_FOUR: mins = 4.0 + (t - T_FOUR) * 0.05
    for a, b in ((T_18[1], T_18[1] + 4.0),):
        if t > a: mins += 15 * ease_io((t - a) / (b - a))
    dy = -600 * fly(t, CLOCK_OUT)
    if 205 + dy + 80 > 0:
        PR.wall_clock(L.mask("mid"), cam, (1215, 205 + dy), 72, mins)
        ST.line(L.mask("mid"), cam, (1215, -60), (1215, 205 + dy - 72), 2.4)

def draw_props_back(L, cam, t):
    mid = L.mask("mid")
    # the calendar on the wall (it gives up; two years blow off it; nobody scheduled it)
    flying = []
    if T_CAL - 0.2 < t < T_GIVEUP + 1.2:
        n = 9
        for i in range(n):
            s0 = T_CAL + i * (T_GIVEUP - T_CAL) / n
            ph = (t - s0) / 0.9
            if 0 < ph < 1: flying.append(ph)
    if T_TWO - 0.2 < t < T_TWO + 2.4:   # "for two years": a flurry of pages
        for i in range(24):
            ph = (t - (T_TWO - 0.1 + i * 0.065)) / 0.85
            if 0 < ph < 1: flying.append((ph, ((i * 0.618) % 1.0 - 0.5) * 2.4 + 1e-3))
    day = 21 + int(max(0, min(9, (t - T_CAL) / (T_GIVEUP - T_CAL) * 9))) if t > T_CAL else 21
    if T_TWO - 0.1 < t < T_TWO + 1.55: day = (7, 19, 2, 28, 11, 23, 5, 16, 30, 9, 21, 14)[int((t - T_TWO) * 7.5) % 12]
    if t > T_NOSCHED - 0.25: day = "—"
    flag = sstep(T_GIVEUP, T_GIVEUP + 0.5, t) * (1 - sstep(T_GIVEUP + 3.5, T_GIVEUP + 4.2, t))
    dy = -620 * fly(t, CAL_OUT)
    if 150 + dy + 170 > 0:
        wv = PR.calendar(mid, cam, 600, 150 + dy, day, flying, t, flag)
        ST.line(mid, cam, (600, -60), (600, 150 + dy - 34), 2.4)
        if wv is not None:
            gm = np.zeros((cam.H, cam.W), np.uint8); ST.fill(gm, cam, [wv]); L.add_custom(gm, 1.0, 0.30)
    # the projection screen, blank (no slides)
    for a in T_18[:1]:
        k = sstep(a - 0.2, a + 0.5, t) * (1 - sstep(T_FATHER[0] - 0.4, T_FATHER[0], t))
        if k > 0:
            y0 = -400 + 470 * ease_out(k); X0, X1 = 330, 830
            ST.fill(mid, cam, [np.array([(X0, y0), (X1, y0), (X1, y0 + 14), (X0, y0 + 14)]), np.array([(X0, y0 + 300), (X1, y0 + 300), (X1, y0 + 318), (X0, y0 + 318)])])
            ST.line(mid, cam, (X0 + 10, y0 + 14), (X0 + 10, y0 + 300), 5); ST.line(mid, cam, (X1 - 10, y0 + 14), (X1 - 10, y0 + 300), 5)
            if t > T_SLIDES[0]:
                gq = PR.glyph("(no slides)", F_ITAL, 90); PR.stamp(mid, cam, gq, ((X0 + X1) / 2, y0 + 160), 60 * sstep(T_SLIDES[0], T_SLIDES[0] + 0.2, t))

def dana_chair(L, cam, x, t):
    """her empty chair: cobwebs grow on it, a spider lets itself down from the back"""
    k = sstep(T_HAS, T_TWO + 1.0, t) * (1 - sstep(T_FINAL + 0.6, T_FINAL + 1.6, t))
    if k <= 0: return
    seat_y = ST.FLOOR - 250 * 0.95
    m = L.mask("crisp")
    for P in PR.cobweb_corner(x + 66 * 0.95, seat_y - 2, 125, k, math.pi * 1.02, math.pi * 1.48, t):
        ST.polyline(m, cam, P, 1.4)
    for P in PR.cobweb_corner(x - 58 * 0.95, seat_y + 22, 70, sstep(T_HAS + 0.6, T_TWO + 1.3, t), math.pi * 0.05, math.pi * 0.48, t):
        ST.polyline(m, cam, P, 1.2)
    ks = sstep(T_TWO - 0.2, T_TWO + 1.2, t)
    if ks > 0:
        sx = x + 50; sy0 = seat_y - 160; sy = sy0 + 95 * ease_out(ks) + 6 * math.sin(t * 2.3)
        ST.line(m, cam, (sx, sy0), (sx, sy - 10), 1.2)
        body, legs = PR.spider(sx, sy, 1.15, t)
        ST.fill(m, cam, body)
        for P in legs: ST.polyline(m, cam, P, 1.6)

def cam_cx(cam):
    """the world x at the centre of the frame"""
    return (cam.W / 2 - cam.ox) / cam.s

def draw_props_front(L, cam, t, a_me, a_ted, g, tops):
    crisp = L.mask("crisp"); near = L.mask("near")
    # her question: a little "?" she holds up (V1), knocked away by Ted's reply
    kq = sstep(T_V1, T_V1 + 0.3, t)
    if kq > 0 and t < T_RESP + 3.0:
        k_fall = ease_in_q((t - (T_RESP + 0.6)) / 1.2)
        c = a_me["hand_f"] + np.array([10, -60]) + np.array([-220, 300]) * k_fall
        PR.stamp(crisp, cam, PR.glyph("?", PR.F_SERIF, 160), c, 90 * kq, ang=-2.5 * k_fall)
    # Ted's reply: paper swirls flying out of his mouth (V1)
    for a, b in ((T_RESP, T_DIFF + 1.0),):
        if a < t < b:
            for j in range(9):
                ph = (t - a - j * 0.22) / 1.6
                if not (0 < ph < 1): continue
                m0 = a_ted["mouth"]; p = m0 + np.array([-420 * ph, -55 * math.sin(ph * math.pi) + 26 * math.sin(ph * 12 + j)])
                shp = ["~", "@", "*", "&", "§", "~", "*", "@", "&"][j]
                PR.stamp(near, cam, PR.glyph(shp, PR.F_SERIF, 120), p, 70 * (1 - 0.3 * ph), ang=ph * 6 + j)
    # the file she holds up
    kf = sstep(T_ASK - 0.1, T_ASK + 0.4, t) * (1 - sstep(T_STEP + 0.4, T_STEP + 1.0, t))
    if kf > 0:
        h = a_me["hand_f"]; P = np.array([(h[0] - 10, h[1] - 120), (h[0] + 80, h[1] - 120), (h[0] + 80, h[1] + 4), (h[0] - 10, h[1] + 4)])
        ST.fill(crisp, cam, [P]); PR.stamp(crisp, cam, PR.glyph("?", PR.F_SERIF, 160), (h[0] + 35, h[1] - 58), 80 * kf, val=0)
    # "so —" over Ted's head when he says it
    kso = sstep(T_SO - 0.05, T_SO + 0.1, t) * (1 - sstep(T_DIM, T_DIM + 0.5, t))
    if kso > 0:
        PR.stamp(near, cam, PR.glyph("so —", PR.F_ITAL, 200), (930.0 if not cam.vert else cam_cx(cam) + 30, 190.0), 90 * kso)
    # IT'S A TED TALK: cut-paper capitals dropping in on strings
    draw_letters(crisp, cam, t)
    # the story about his father (an iris onto a smaller scene), and the young Ted in the rain
    for a, e in zip(T_FATHER, T_PAUSE):
        k = ease_out((t - a) / 0.5) * (1 - ease_io((t - (e - 0.1)) / 0.35))
        if k > 0: iris(L, cam, t, k, "father", nested=(a == T_FATHER[1]))
    for a, e in zip(T_RAFTER, T_BELIEVE_E):
        k = ease_out((t - a) / 0.5) * (1 - ease_io((t - (e + 0.1)) / 0.4))
        if k > 0: iris(L, cam, t, k, "young", violin=(a == T_RAFTER[1]))
    # the pause he thinks is powerful: a cricket (and, the second time, a tumbleweed)
    for j, (a, e) in enumerate(zip(T_PAUSE, T_PAUSE_E)):
        k = sstep(a + 0.4, a + 0.6, t) * (1 - sstep(e + 0.2, e + 0.6, t))
        if k > 0:
            cx = 860 if not cam.vert else cam_cx(cam) - 180
            ST.fill(crisp, cam, PR.cricket(cx, t, 1.2)); ST.fill(near, cam, PR.chirp_lines(cx, t, 1.2))
            if j == 1:
                tx = -150 + 2200 * clamp((t - a - 0.3) / 2.6)
                r = 46; ang = tx / r
                P = [(tx + r * (0.8 + 0.25 * math.sin(q * 7 + ang)) * math.cos(q + ang), ST.FLOOR - r - 4 + r * (0.8 + 0.25 * math.sin(q * 7 + ang)) * math.sin(q + ang)) for q in np.linspace(0, 2 * math.pi, 40)]
                ST.polyline(near, cam, P, 4, closed=True)
                ST.polyline(near, cam, [(tx + r * 0.5 * math.cos(q * 2 + ang), ST.FLOOR - r - 4 + r * 0.5 * math.sin(q * 3 + ang)) for q in np.linspace(0, 2 * math.pi, 30)], 3)
    # circling back: a dotted loop on the floor
    for a, b in zip(T_CIRCLE, T_CIRCLE_E):
        k = sstep(a, a + 0.2, t) * (1 - sstep(b + 0.3, b + 0.9, t))
        if k > 0:
            prog = clamp((t - a) / (b - a))
            for q in np.linspace(0, prog, int(40 * prog) + 1):
                th = q * 2 * math.pi
                c = (TED_X + 320 * math.sin(th), ST.FLOOR + 6 - 26 * math.cos(th))
                PR.circle(near, cam, c, 5, 255)
    # SO / RIGHT?: words fly out of his mouth like birds
    draw_birds(near, cam, t, a_ted)
    # the real question: he plucks her little "?" and holds up a grand one
    kr = sstep(T_REAL, T_REAL + 0.3, t) * (1 - sstep(T_JOURNEY - 0.55, T_JOURNEY - 0.3, t))
    if T_REALQ - 0.3 < t < T_REAL + 0.2:
        PR.stamp(crisp, cam, PR.glyph("?", PR.F_SERIF, 160), a_me["hand_f"] + np.array([10, -60]), 80)
    if kr > 0:
        PR.stamp(crisp if g < 1.05 else near, cam, PR.glyph("?", PR.F_ITAL, 300), a_ted["hand_f"] + np.array([0, -130]), 240 * kr * min(1.8, g))
    if T_REAL < t < T_JOURNEY:
        PR.stamp(crisp, cam, PR.glyph("?", PR.F_SERIF, 160), (ME_X + 150, ST.FLOOR - 30), 60, ang=1.57)    # hers, on the floor
    # journey, unlock, story: he holds each one up
    held_props(crisp, cam, t, a_ted)
    # the bridge: the clock is swapped for an hourglass; eight people are counted
    kh = sstep(T_FIFTEEN - 0.2, T_FIFTEEN + 0.6, t) * (1 - sstep(T_FINAL, T_FINAL + 0.8, t))
    if kh > 0:
        hx = 1215.0; hy = -300 + 540 * ease_out(kh)
        ST.line(L.mask("mid"), cam, (hx, -60), (hx, hy - 136), 2.4)
        used = 0.4 * ease_io((t - T_SIX) / 1.0)
        PR.hourglass(L.mask("mid"), cam, (hx, hy), 240, used, t)
    for i, nm in enumerate(["Jo", "Lee", "Sam", "Me", "Ted", "Dana", "Priya", "Marcus"]):
        a0 = T_EIGHT + 0.05 + i * 0.17
        if t < a0 or nm not in tops or t > T_HARD + 1.2: continue
        k = sstep(a0, a0 + 0.12, t)
        pop = 1 + 0.25 * math.sin(clamp((t - a0) / 0.35) * math.pi)
        up = ease_io((t - (T_HARD - 0.35 + i * 0.04)) / 0.6)
        c = tops[nm] + np.array([0, -64 - 760 * up])
        ST.line(crisp, cam, (c[0], -60), (c[0], c[1] - 28 * k), 1.5)
        PR.number_tag(crisp, cam, c, 31, i + 1, k * pop)
    # Dana's ghost drifts back in and sits in her chair
    kg = sstep(T_GHOST - 0.1, T_GHOST + 1.2, t) * (1 - sstep(T_FINAL + 0.6, T_FINAL + 1.6, t))
    if kg > 0:
        gx = lerp(1960, 1355, ease_io((t - T_GHOST) / 2.2)); gy = ST.FLOOR - 330 + 16 * math.sin(t * 2.2)
        body, holes = PR.ghost(gx, gy, t, 1.3)
        m = np.zeros((cam.H, cam.W), np.uint8); ST.fill(m, cam, body); ST.fill(m, cam, holes, 0)
        L.add_custom(m, 1.2, 0.36 * kg)
    # Q and A
    kqa = sstep(T_NOQA - 0.05, T_NOQA + 0.3, t) * (1 - sstep(T_NEVERQ + 2.4, T_NEVERQ + 3.0, t))
    if kqa > 0:
        cx = 960 if not cam.vert else cam_cx(cam)
        dropA = ease_in_q((t - T_NOA) / 0.7)
        yq = -150 + 430 * ease_out((t - T_NOQA) / 0.4)
        qm = np.zeros((cam.H, cam.W), np.uint8)
        ST.line(qm, cam, (cx - 130, -40), (cx - 130, yq - 80), 2)
        PR.stamp(qm, cam, PR.glyph("Q", F_SC, 220), (cx - 130, yq), 170)
        bp = clamp((t - (T_NEVERQ + 0.8)) / 1.6)
        if bp > 0:
            qm, edge = PR.burn_edge(qm, bp)
            L.ember = np.maximum(getattr(L, "ember", np.zeros_like(edge)), edge)
        np.maximum(crisp, qm, out=crisp)
        PR.stamp(crisp, cam, PR.glyph("&", F_SC, 160), (cx, yq + 10), 110)
        ST.line(crisp, cam, (cx, -40), (cx, yq - 60), 2)
        ya = yq + 700 * dropA
        PR.stamp(crisp, cam, PR.glyph("A", F_SC, 220), (cx + 130, ya), 170, ang=0.8 * dropA)
        if dropA <= 0: ST.line(crisp, cam, (cx + 130, -40), (cx + 130, yq - 80), 2)
    # "into a place none of us can reach": an iris onto a long road, Ted walking away down it; it closes on him
    ka = ease_out((t - T_PLACE) / 0.7)
    if ka > 0 and t < T_REACH + 1.8:
        iris(L, cam, t, ka, "away")

def ease_in_q(x): x = clamp(x); return x * x

# ---------------------------------------------------------------- the hanging letters
LETTER_WORDS = {0: "IT'S", 1: "A", 2: "TED", 3: "TALK", 5: "ALWAYS"}
LETTER_CAP = {(False, False): 90.0, (False, True): 90.0, (True, False): 100.0, (True, True): 86.0}
LINE_TOP = (150.0, 292.0)
def letter_lines(vert, always):
    if always: return [[0, 5], [1, 2, 3]]
    return [[0, 1], [2, 3]] if vert else [[0, 1, 2, 3]]

@lru_cache(8)
def letter_layout(vert, always):
    """glyph key (word, j) -> (x from the line centre in 200-px em units, line, reading order, char)"""
    from PIL import ImageFont
    f = ImageFont.truetype(F_SC, 200); sp = f.getlength(" ") * 1.2; track = 7.0
    out = {}; order = 0
    for li, line in enumerate(letter_lines(vert, always)):
        items = []
        for wi, w in enumerate(line):
            if wi: items.append((None, " ", sp))
            for j, ch in enumerate(LETTER_WORDS[w]): items.append(((w, j), ch, f.getlength(ch) + track))
        tot = sum(a for _, _, a in items) - track; x = -tot / 2
        for key, ch, adv in items:
            if key is not None: out[key] = (x + (adv - track) / 2, li, order, ch); order += 1
            x += adv
    return out

def draw_letters(mask, cam, t):
    """big serif capitals hanging on threads from the top of the stage; at the end, ALWAYS drops in between them.
    Threads of the lower line pass behind the letters of the upper line."""
    cap_px = PR.em_glyph("I", F_SC)[4]
    cx = 960.0 if not cam.vert else cam_cx(cam)
    insts = [(TT[i], LIFT[i], None) for i in range(5)] + [(TT[5], LIFT[6], TT[6])]
    for a, lift_t, morph in insts:
        if not (a - 0.05 < t < lift_t + 1.0): continue
        A = letter_layout(cam.vert, False); B = letter_layout(cam.vert, True) if morph else {}
        km = ease_io((t - (morph - 0.2)) / 0.6) if morph else 0.0
        sA = LETTER_CAP[(cam.vert, False)] / cap_px; sB = LETTER_CAP[(cam.vert, True)] / cap_px
        s = lerp(sA, sB, km)
        lift = ease_io((t - lift_t) / 0.8)
        keys = list(A.keys()) + [k_ for k_ in B if k_ not in A]
        items = []
        for key in keys:
            if key in A:
                xa, la, oa, ch = A[key]
                two = max(v[1] for v in A.values()) > 0                      # two lines: the lower line drops first
                n0 = sum(1 for v in A.values() if v[1] == 0)
                t0 = a + (oa * 0.035 if not two else ((oa - n0) * 0.035 if la == 1 else 0.42 + oa * 0.035))
                if key in B:
                    xb, lb, _, _ = B[key]; x = lerp(xa * sA, xb * sB, km); line_y = lerp(LINE_TOP[la], LINE_TOP[lb], km)
                else: x, line_y = xa * s, LINE_TOP[la]
            else:
                xb, lb, _, ch = B[key]; t0 = morph + 0.12 + key[1] * 0.05; x, line_y = xb * sB, LINE_TOP[lb]
            dk = ease_out(clamp((t - t0) / 0.4))
            if dk <= 0: continue
            bob = 7 * math.sin((t - t0 - 0.4) * 10) * math.exp(-max(0.0, t - t0 - 0.4) * 3.5) * (t > t0 + 0.4)
            y_top = -300 + (line_y + 300) * dk + bob - 950 * lift
            if y_top + 120 < -20: continue
            sw = 0.09 * math.sin((t - t0) * 4.6 + key[1] + key[0]) * math.exp(-max(0.0, t - t0) * 1.1)
            items.append((cx + x, y_top, line_y, ch, sw))
        cap = LETTER_CAP[(cam.vert, False)] * s / sA
        upper = [(X - PR.em_glyph(ch, F_SC)[2] * s / 2 - 5, X + PR.em_glyph(ch, F_SC)[2] * s / 2 + 5, y - 8, y + cap + 10)
                 for X, y, ly, ch, sw in items if ly < 220]
        for X, y, ly, ch, sw in items:
            segs = [(-60.0, y + 3)]
            if ly >= 220:
                for x0, x1, y0, y1 in upper:
                    if x0 < X < x1:
                        nxt = []
                        for s0, s1 in segs:
                            if y1 <= s0 or y0 >= s1: nxt.append((s0, s1)); continue
                            if y0 > s0: nxt.append((s0, y0))
                            if y1 < s1: nxt.append((y1, s1))
                        segs = nxt
            for s0, s1 in segs:
                if s1 > s0 + 1: ST.line(mask, cam, (X, s0), (X, s1), 1.8)
        for X, y, ly, ch, sw in items:
            img, (ax, ay), adv, ink_top, _ = PR.em_glyph(ch, F_SC)
            PR.stamp(mask, cam, img, (X, y), img.shape[0] * s, ang=sw, anchor=(ax / img.shape[1], ink_top / img.shape[0]))

# ---------------------------------------------------------------- word-birds
BIRDS = [("SO", T_SOw - 0.15, 104, 800), ("SO", T_SOw + 0.55, 82, 930), ("SO", T_SOw + 1.25, 64, 730),
         ("RIGHT?", T_RIGHT - 0.15, 70, 900), ("RIGHT?", T_RIGHT + 0.7, 54, 830)]
WING = np.array([(0.0, -0.06), (0.18, -0.15), (0.42, -0.21), (0.68, -0.20), (0.88, -0.13), (1.0, -0.03),
                 (0.93, 0.03), (0.86, 0.0), (0.80, 0.09), (0.72, 0.04), (0.64, 0.13), (0.55, 0.07), (0.45, 0.15),
                 (0.35, 0.08), (0.24, 0.14), (0.12, 0.09), (0.0, 0.11)])
def wing_poly(root, Lw, sg, theta):
    P = []
    for x, y in WING:
        a = theta * (0.55 + 0.45 * x)                 # the outer wing bends further than the inner
        xr = x * math.cos(a) + y * math.sin(a); yr = -x * math.sin(a) + y * math.cos(a)
        P.append((root[0] + sg * xr * Lw, root[1] + yr * Lw))
    return np.array(P)

def gull(mask, cam, b, B, flap, d):
    """a little paper gull flying in direction d (+1 right / -1 left): body, head, beak, forked tail, scalloped wings"""
    P = lambda dx, dy: b + np.array([d * dx * B, dy * B])
    ST.fill(mask, cam, [PR.ellipse_pts(b, 0.24 * B, 0.09 * B, n=20), PR.ellipse_pts(P(0.23, -0.045), 0.08 * B, 0.072 * B, n=14),
                        np.array([P(0.29, -0.06), P(0.41, -0.03), P(0.29, -0.01)]),
                        np.array([P(-0.16, -0.03), P(-0.36, -0.09), P(-0.28, 0.0), P(-0.36, 0.07), P(-0.16, 0.035)])])
    th = 0.25 + 0.75 * flap
    for sg in (-1, 1): ST.fill(mask, cam, [wing_poly(b + np.array([sg * 0.03 * B, -0.03 * B]), 0.78 * B, sg, th)])

def word_bird(mask, cam, word, c, size, flap, d, sw):
    """a gull carrying a word: the word hangs from it on a short thread, swinging"""
    g_ = PR.glyph(word, F_SC, 160)
    top = c - np.array([0.0, size * 0.5])
    B = size * 1.25; b = top - np.array([0.0, size * 0.42 + 0.05 * B])
    ST.line(mask, cam, b + np.array([0, 0.05 * B]), top + np.array([0, size * 0.06]), 1.6)
    PR.stamp(mask, cam, g_, top, size, ang=sw, anchor=(0.5, 0.0))
    gull(mask, cam, b, B, flap, d)

def draw_birds(mask, cam, t, a_ted):
    for word, a, size, ex in BIRDS:
        D = 3.4; u = (t - a) / D
        if not (0 < u < 1): continue
        g_ = PR.glyph(word, F_SC, 160); hw = g_.shape[1] / g_.shape[0] * size / 2
        m0 = a_ted["mouth"] + np.array([-12.0 - hw * 0.6, 0.0])          # the word comes out of his mouth, leftward like speech
        k = ease_io(clamp(u * 1.6)); ky = u ** 1.25
        c = np.array([m0[0] + (ex - m0[0]) * k + 26 * math.sin(u * 7.5 + size), m0[1] + (-330 - m0[1]) * ky])
        grow = ease_out(clamp(u / 0.12))
        flap = math.sin((t - a) * 2 * math.pi * 2.6 + size)
        sw = 0.12 * math.sin((t - a) * 3.1 + size) * min(1, u * 5)
        word_bird(mask, cam, word, c, size * (0.25 + 0.75 * grow), flap, 1 if ex > m0[0] else -1, sw)

# ---------------------------------------------------------------- what Ted holds up: journey, unlock, story
def held_props(mask, cam, t, a_ted):
    h = a_ted["hand_f"]
    kj = sstep(T_JOURNEY - 0.38, T_JOURNEY - 0.2, t) * (1 - sstep(T_UNLOCK - 0.24, T_UNLOCK - 0.14, t))
    if kj > 0:
        polys, holes = PR.mountain_prop(h[0] + 18, h[1], 0.82 * kj)
        ST.fill(mask, cam, polys); ST.fill(mask, cam, holes, 0)
    kk = sstep(T_UNLOCK - 0.2, T_UNLOCK - 0.1, t) * (1 - sstep(T_STORY - 0.3, T_STORY - 0.2, t))
    if kk > 0:
        turn = ease_io((t - T_UNLOCK) / 0.28)
        polys, holes = PR.big_key(h[0], h[1] + 30, turn, 0.92 * kk)
        ST.fill(mask, cam, polys); ST.fill(mask, cam, holes, 0)
        kc = sstep(T_UNLOCK + 0.18, T_UNLOCK + 0.26, t) * (1 - sstep(T_UNLOCK + 0.6, T_UNLOCK + 0.8, t))
        if kc > 0:   # click
            top = np.array([h[0], h[1] + 30 - 250 * 0.92])
            for j in range(5):
                an = -math.pi / 2 + (j - 2) * 0.5; d = np.array([math.cos(an), math.sin(an)])
                ST.line(mask, cam, top + d * 34, top + d * (34 + 36 * kc), 4)
    kb = sstep(T_STORY - 0.12, T_STORY + 0.12, t) * (1 - sstep(T_CAL + 0.4, T_CAL + 0.9, t))
    if kb > 0:
        hh = (a_ted["hand_f"] + a_ted["hand_b"]) / 2
        polys, holes = PR.book(hh[0] - 8, hh[1] - 6, 0.15 + 0.85 * sstep(T_STORYw - 0.6, T_STORYw + 0.3, t), 1.15 * kb)
        ST.fill(mask, cam, polys); ST.fill(mask, cam, holes, 0)

# ---------------------------------------------------------------- irises: little stages inside a cut-paper ring
def iris_circle(t, cam):
    """the father / young inset currently open, as (centre, radius), or None"""
    for (a, e, which, ee) in [(T_FATHER[0], T_PAUSE[0], "father", -0.1), (T_FATHER[1], T_PAUSE[1], "father", -0.1),
                              (T_RAFTER[0], T_BELIEVE_E[0], "young", 0.1), (T_RAFTER[1], T_BELIEVE_E[1], "young", 0.1)]:
        if which == "father": k = ease_out((t - a) / 0.5) * (1 - ease_io((t - (e + ee)) / 0.35))
        else: k = ease_out((t - a) / 0.5) * (1 - ease_io((t - (e + ee)) / 0.4))
        if k > 0:
            c = np.array([470.0, 320.0]) if which == "father" else np.array([1420.0, 320.0])
            if cam.vert: c = np.array([cam_cx(cam), 320.0])
            return c, 230.0 * k
    return None

def iris(L, cam, t, k, which, nested=False, violin=False):
    """a circular inset onto a little story scene; the ring is cut paper, the inside its own small stage
    (the wall behind it is hidden while it's open)"""
    vert = cam.vert
    c = {"father": np.array([470.0, 320.0]), "young": np.array([1420.0, 320.0]), "away": np.array([960.0, 300.0])}[which]
    if vert: c = np.array([cam_cx(cam), 320.0 if which != "away" else 268.0])
    R = (230.0 if not (vert and which == "away") else 200.0) * k; c_clip = c.copy()
    m = np.zeros((cam.H, cam.W), np.uint8)
    sc = 0.42
    if which == "father":
        wy = c[1] + 80
        ST.fill(m, cam, PR.waves(c[0] - 260, c[0] + 260, wy, t, 8))
        ST.fill(m, cam, PR.boat(c[0], wy - 4, 0.8))
        for nm, dx, h, f in (("Ted", -45, 0.95, 1), ("Lee", 50, 0.62, -1)):
            pu = PP.Puppet("father" if dx < 0 else "boy", h, "short", 1.05 if dx < 0 else 0.9)
            pose = PP.Pose(sit=1.0, sh_f=1.2, el_f=0.3)
            polys, holes, gels, rods, anch = pu.parts(pose, c[0] + dx, wy - 22, 300 * sc * 1.6, f)
            ST.fill(m, cam, polys); ST.fill(m, cam, holes, 0)
            hnd = anch["hand_f"]; ST.line(m, cam, hnd, hnd + np.array([f * 120, -110]), 2.5)
            ST.line(m, cam, hnd + np.array([f * 120, -110]), hnd + np.array([f * 140, 60 + 8 * math.sin(t * 2)]), 1)
        if nested:   # his father's father
            c2 = c + np.array([110, -110]); r2 = 70
            ring = np.zeros_like(m); PR.circle(ring, cam, c2, r2 + 10, 255); PR.circle(ring, cam, c2, r2, 0)
            np.maximum(m, ring, out=m)
            pu = PP.Puppet("grandpa", 0.9, "bald", 1.0, nose=1.3)
            polys, holes, _, _, _ = pu.parts(PP.Pose(slump=0.5), c2[0], c2[1] + 60, 110, 1)
            ST.fill(m, cam, polys); ST.fill(m, cam, holes, 0)
    elif which == "young":
        fy = c[1] + 165
        ST.fill(m, cam, [np.array([(c[0] - 300, fy), (c[0] + 300, fy), (c[0] + 300, fy + 200), (c[0] - 300, fy + 200)])])
        ST.fill(m, cam, [p - np.array([0, ST.FLOOR - fy]) for p in PR.lamppost(c[0] + 92, 0.68)])
        pu = PP.Puppet("young", 0.62, "short", 0.9, nose=0.8)
        pose = PP.Pose(slump=0.5, sh_f=0.0, el_f=0.0, sh_b=-0.1)
        if violin: pose = PP.Pose(slump=0.3, sh_f=1.4, el_f=1.6, sh_b=1.2, el_b=0.6, head=0.25)
        polys, holes, gels, rods, anch = pu.parts(pose, c[0] - 60, fy, 360, 1)
        ST.fill(m, cam, polys); ST.fill(m, cam, holes, 0)
        if not violin:
            ST.fill(m, cam, [np.array([(c[0] - 18, fy), (c[0] + 46, fy), (c[0] + 46, fy - 50), (c[0] - 18, fy - 50)])])   # a little suitcase
            ST.polyline(m, cam, [(c[0] + 2, fy - 50), (c[0] + 4, fy - 62), (c[0] + 24, fy - 62), (c[0] + 26, fy - 50)], 4)
        else:
            hb = anch["hand_b"]; ST.line(m, cam, anch["hand_f"], anch["hand_f"] + np.array([95, 62]), 3)
            ST.fill(m, cam, [PR.ellipse_pts(hb + np.array([2, 14]), 30, 16, ang=0.6, n=16)])
        for j in range(30):   # rain
            rx = c[0] - 260 + (j * 41 + t * 260) % 520; ry = c[1] - 220 + ((j * 97 + t * 900) % 440)
            ST.line(m, cam, (rx, ry), (rx - 8, ry + 28), 1.8)
    else:
        ground = np.zeros_like(m)
        ted_pos = far_place(m, ground, cam, c, t)
        close = ease_io((t - (T_REACH - 0.25)) / 1.9)
        R = R * (1 - close)
        c_clip = c + (ted_pos - c) * min(1.0, close * 1.6)
        clip = np.zeros_like(m); PR.circle(clip, cam, c_clip, max(R, 0.5), 255)
        ground = (ground.astype(np.uint16) * clip // 255).astype(np.uint8)
        L.add_custom(ground, 1.0, 0.42)
        if R > 1.5: L.lit_clip = (c_clip, R + 18 * min(1.0, R / 60.0))      # the inset keeps its own light while the stage goes dark
    if R < 1.0: return
    # hide the wall behind the inset
    er = np.zeros_like(m); PR.circle(er, cam, c_clip, R + 18, 255)
    for nm in ("deep", "mid"):
        if nm in L.m: L.m[nm] = (L.m[nm].astype(np.uint16) * (255 - er) // 255).astype(np.uint8)
    # clip to the circle, add the ring (cut paper, with a lace edge)
    clip = np.zeros_like(m); PR.circle(clip, cam, c_clip, R, 255)
    m = (m.astype(np.uint16) * clip // 255).astype(np.uint8)
    rk = min(1.0, R / 70.0)
    ring = np.zeros_like(m); PR.circle(ring, cam, c_clip, R + 16 * rk, 255); PR.circle(ring, cam, c_clip, R, 0)
    L.add_custom(m, 1.0, 0.95)
    for j in range(36):
        a = j / 36 * 2 * math.pi; PR.circle(ring, cam, c_clip + np.array([math.cos(a), math.sin(a)]) * (R + 22 * rk), 6 * rk, 255)
    np.maximum(L.mask("crisp"), ring, out=L.mask("crisp"))

def far_place(m, ground, cam, c, t):
    """the far place: a long road over the hills to the horizon, telephone poles, and Ted walking away down it.
    The land is thin paper (a grey shadow); the road is cut out of it; poles and Ted are black. Returns Ted's centre."""
    hy = c[1] + 26.0; yn = c[1] + 300.0; vx = c[0] + 40
    xs = np.linspace(c[0] - 330, c[0] + 330, 70)
    prof = [(x, hy - 34 * math.exp(-((x - (c[0] - 135)) / 80) ** 2) - 20 * math.exp(-((x - (c[0] + 175)) / 110) ** 2) - 4 * math.sin(x * 0.05)) for x in xs]
    ST.fill(ground, cam, [np.array(prof + [(c[0] + 330, c[1] + 340), (c[0] - 330, c[1] + 340)])])
    S = lambda u: (1 - u) ** 2.0
    def pt(u, side=0.0):
        s_ = S(u); return np.array([vx + (-120 + 80 * math.sin(u * 5.2)) * s_ + side * (125 * s_ + 0.8), hy + (yn - hy) * s_])
    us = np.linspace(0, 0.996, 90)
    ST.fill(ground, cam, [np.array([pt(u, -1) for u in us] + [pt(u, 1) for u in us[::-1]])], 0)
    for i in range(16):   # the centre line
        u0 = i / 16 * 0.95; u1 = u0 + 0.028
        ST.polyline(m, cam, [pt(u, 0) for u in np.linspace(u0, u1, 4)], max(0.7, 6.5 * S(u0)))
    tops = []
    for u in (0.04, 0.18, 0.32, 0.45, 0.56, 0.66, 0.74, 0.81, 0.87):
        b = pt(u, 1.5); h = 250 * S(u) + 5; tp = b - np.array([0, h]); w = 28 * S(u) + 1.2
        ST.line(m, cam, b, tp, max(0.9, 6.5 * S(u)))
        ST.line(m, cam, tp + np.array([-w, 9 * S(u)]), tp + np.array([w, 9 * S(u)]), max(0.7, 4 * S(u)))
        tops.append((tp + np.array([0, 9 * S(u)]), S(u)))
    for (a_, sa), (b_, sb) in zip(tops[:-1], tops[1:]):   # the wire, sagging between the poles
        ST.polyline(m, cam, [a_, (a_ + b_) / 2 + np.array([0, 14 * sa]), b_], 1.3)
    q = clamp((t - (T_PLACE - 0.4)) / (T_REACH + 1.7 - T_PLACE + 0.4))
    u = lerp(0.20, 0.80, q ** 0.85)
    pos = pt(u, 0.0); sc = 300 * S(u)
    ph = (t - T_PLACE) * 2 * math.pi * 1.25
    pose = PP.Pose(hip_f=0.32 * math.sin(ph), hip_b=-0.32 * math.sin(ph), kn_f=0.3 * max(0, math.cos(ph)), kn_b=0.3 * max(0, -math.cos(ph)),
                   sh_f=0.3 * math.sin(ph + math.pi), sh_b=0.3 * math.sin(ph), el_f=0.3, el_b=0.3)
    polys, holes, _, _, _ = PP.CAST["Ted"].parts(pose, pos[0], pos[1], sc, 1)
    ST.fill(m, cam, polys); ST.fill(m, cam, holes, 0)
    return pos - np.array([0, sc * 0.55])

def sign(img, cam, t, light):
    """at the very start, a little board hangs in front of the closed curtain: the letters are cut out, so they glow"""
    k = 1 - sstep(1.4, 2.6, t)
    if k <= 0.01: return
    H, W = img.shape[:2]
    m = np.zeros((H, W), np.uint8)
    y = 330 - 600 * (1 - k) ** 2
    bw, bh = (760, 230) if not cam.vert else (620, 200)
    cx = 960 if not cam.vert else focus_x(t)
    ST.fill(m, cam, [np.array([(cx - bw / 2, y), (cx + bw / 2, y), (cx + bw / 2, y + bh), (cx - bw / 2, y + bh)])])
    ST.line(m, cam, (cx - bw / 3, -30), (cx - bw / 3, y), 2); ST.line(m, cam, (cx + bw / 3, -30), (cx + bw / 3, y), 2)
    holes = np.zeros_like(m)
    PR.stamp(holes, cam, PR.glyph("THE STANDUP", F_SC, 200), (cx, y + bh * 0.42), bh * 0.36)
    PR.stamp(holes, cam, PR.glyph("9:15 a.m.", PR.F_ITAL, 200), (cx, y + bh * 0.78), bh * 0.24)
    a = cv2.GaussianBlur(m.astype(F32) / 255, (0, 0), 1.0) * k
    hl = cv2.GaussianBlur(holes.astype(F32) / 255, (0, 0), 0.8) * k
    img[:] = img * (1 - a[..., None]) + np.array([0.07, 0.03, 0.02], F32) * a[..., None]
    img += hl[..., None] * np.array([1.0, 0.78, 0.45], F32) * 0.95

# ---------------------------------------------------------------- lyrics, finish
def lyrics(img, t, W, H):
    if C.STATE["clean"]: return
    vert = H > W; k = W / (1080 if vert else 1920)
    fs = int((70 if not vert else 62) * k); maxw = W * (0.84 if not vert else 0.80)     # 9:16: inside the Reels/Shorts safe frame
    ybase = H * (0.885 if not vert else 0.745)
    flt = C.STATE["lyric_filter"]
    skip = lambda L: L['text'].startswith("It's a Ted talk") or L['text'].startswith("It's always")
    vis = [L for L in TM.lines if (flt is None or flt(L)) and not skip(L)]
    for li, L in enumerate(vis):
        nxt = vis[li + 1]['s'] if li + 1 < len(vis) else 1e9
        prv = (vis[li - 1]['e'] + 0.45) if li > 0 else -1e9
        if prv > L['s'] - 0.3: a0, a1 = L['s'] - 0.07, L['s'] + 0.05
        else: a0, a1 = L['s'] - 0.3, L['s']
        if L['e'] + 0.45 > nxt - 0.3: b0, b1 = nxt - 0.17, nxt - 0.07
        else: b0, b1 = L['e'] + 0.05, L['e'] + 0.45
        if not (a0 <= t <= b1): continue
        opl = sstep(a0, a1, t) * (1 - sstep(b0, b1, t))
        if opl <= 0.003: continue
        items = list(zip(L['words'], L['wt']))
        nexts = [items[j + 1][1] for j in range(len(items) - 1)] + [L['e'] + 0.3]
        sp = C.text_w(" ", F_LYR, fs); rows = [[]]; cw = 0
        for j, (w_, tt) in enumerate(items):
            ww = C.text_w(w_, F_LYR, fs)
            if rows[-1] and cw + sp + ww > maxw: rows.append([]); cw = 0
            rows[-1].append((w_, tt, ww, nexts[j])); cw += ww + (sp if rows[-1] else 0)
        lh = fs * 1.22; y0 = ybase - (len(rows) - 1) * lh / 2 - fs * 0.62 - lh * 0.2 * (1 - opl)
        for ri, row in enumerate(rows):
            x = (W - (sum(r[2] for r in row) + sp * (len(row) - 1))) / 2
            for w_, tt, ww, nt in row:
                kw = sstep(tt - 0.12, tt + 0.05, t)
                act = sstep(tt - 0.06, tt + 0.02, t) * (1 - sstep(nt - 0.06, nt + 0.04, t))
                yy = y0 + ri * lh
                op = opl * (0.38 + 0.62 * kw)
                C.blit(img, C.sprite(w_, F_LYR, fs, 0), x, yy, CREAM, op)
                if act > 0.02:   # a red cut-paper underline under the word being sung
                    sw = clamp((t - tt + 0.04) / 0.14)
                    x0_, x1_ = int(x), int(x + ww * sw); y_ = int(yy + fs * 1.08)
                    if x1_ > x0_: img[y_:y_ + max(2, int(5 * k)), x0_:x1_] = img[y_:y_ + max(2, int(5 * k)), x0_:x1_] * (1 - act * opl) + RED * act * opl
                x += ww + sp

@lru_cache(16)
def grain(W, H, i):
    return (cv2.resize(C.post(W, H).grain[i], (W, H), interpolation=cv2.INTER_NEAREST) * 0.014).astype(F32)

def finish(img, t, fi):
    H, W = img.shape[:2]; p = C.post(W, H)
    img += grain(W, H, fi % 6)[..., None]
    img *= (1 - sstep(DUR - 1.0, DUR - 0.05, t))
    return (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)
