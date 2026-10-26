"""TED Talk — the standup that turns into a keynote.

Office standup ring -> "So, stepping back" -> lights dim -> red rug, LED wall, arena of empty chairs.
Bridge: hard stop, back to a tiny call grid; Dana's tile becomes a ghost. Final: nobody can end it.
Outro: Ted takes it offline through a door of light, into a place none of us can reach.
"""
import os, math
import numpy as np, cv2
from studio import core as C
from studio.core import (sstep, ease_out, ease_io, win, lerp, hexc, clamp, orbit, project, splat, sprite, blit, txt, card,
                         text_w, shadow, F_INTER, F_INTER_L, F_DISP, F_DISPB, F_MONO, F_MONOB, WHITE, IVORY)

HERE = os.path.dirname(os.path.abspath(__file__))
TM = C.Timing(HERE)
DUR = TM.duration
lt = TM.line_t
def wt(sub, w, nth=0):
    try: return TM.word_t(sub, w, nth)
    except Exception: return lt(sub, nth)

# ---------------------------------------------------------------- palette
RED = hexc('e8383d'); RED2 = hexc('ff5a4f'); AMBER = hexc('ffb347'); WARM = hexc('fff0d6'); PLUM = hexc('1a0920')
MAGENTA = hexc('ff3d8b'); ORANGE = hexc('ff8a2b'); TEALG = hexc('9fc2c4'); OFFICE = hexc('2a3438'); SEPIA = hexc('c9a77c')
CYAN = hexc('4fd8ff'); GREEN = hexc('39d98a'); GHOST = hexc('cfe6ff')

# ---------------------------------------------------------------- key times
T_V1 = lt("He doesn't answer"); T_DIFF = lt("difference"); T_FOUR = lt("four minutes")
T_ASK = lt("I asked him"); T_SO = lt("He said, so"); T_DIM = lt("Somebody dim"); T_SIT = lt("everybody sit")
TT = [L['s'] for L in TM.lines if L['text'].startswith("It's a Ted talk") or L['text'].startswith("It's always")]
T_CH1 = TT[0]
T_18 = lt("Eighteen minutes", 0); T_FATHER = lt("story about his father", 0); T_PAUSE = lt("pause he thinks", 0)
T_CIRCLE = lt("circle back", 0); T_YOUNG = lt("where he was young", 0); T_BELIEVE = lt("nobody believed", 0)
T_V2 = lt("He starts every"); T_ENDS = lt("He ends every"); T_REALQ = lt("the real question"); T_ABOUTQ = lt("about the question")
T_JOURNEY = lt("He said journey"); T_STORY = lt("let me tell you"); T_CAL = lt("watched my calendar"); T_GIVEUP = lt("give up")
T_CH2 = TT[2]
T_18b = lt("Eighteen minutes", 1); T_FATHERb = lt("story about his father", 1); T_PAUSEb = lt("pause he thinks", 1)
T_CIRCLEb = lt("circle back", 1); T_YOUNGb = lt("where he was young", 1)
T_STOP = TM.section("BRIDGE")["s"]
T_TED = lt("Ted."); T_STANDUP = lt("This is a standup"); T_FIFTEEN = lt("fifteen minutes"); T_EIGHT = lt("eight people")
T_SIX = lt("You have used six"); T_HARD = lt("Dana had a hard stop"); T_HAS = lt("Dana has had"); T_TWO = lt("two years")
T_GHOST = lt("Dana is a ghost"); T_DIDTHAT = lt("You did that")
T_FINAL = TT[4]; T_NOSCHED = lt("Nobody scheduled"); T_NOEND = lt("Nobody can end"); T_NOQA = lt("no Q and A")
T_NOA = lt("because there's no A"); T_NEVERQ = lt("never a Q"); T_ALWAYS = lt("always a Ted talk")
T_OUTRO = lt("Anyway"); T_HESAYS = lt("He says."); T_HAVING = lt("Having taken"); T_PLACE = lt("Into a place"); T_REACH = lt("none of us")

TM.stamps = [TM.snap(t - 0.05, 0.2) for t in TT]
TM.stamp_word = None

def phase(t):
    if t < T_SO: return "office"
    if t < T_CH1: return "dim"
    if t < T_STOP: return "stage"
    if t < T_FINAL - 0.6: return "bridge"
    if t < T_OUTRO: return "final"
    return "outro"

def bp(t, k=7.0): return TM.beat_pulse(t, k)

# ---------------------------------------------------------------- people
RING = 8
NAMES = ["Ted", "Me", "Dana", "Priya", "Marcus", "Sam", "Lee", "Jo"]
P_COL = [AMBER, hexc('a9c6ff'), hexc('cfe6ff'), hexc('ffb3c7'), hexc('b7f0c4'), hexc('ffd98a'), hexc('c9b3ff'), hexc('9fe3e0')]
def ring_pos(i):
    a = -math.pi / 2 + i * 2 * math.pi / RING
    return np.array([math.cos(a) * 2.3, 0.0, math.sin(a) * 2.3 + 0.4], np.float32)
SEATS = [np.array([x, 0.0, -2.6], np.float32) for x in (-2.7, -1.8, -0.9, 0.9, 1.8, 2.7, 0.0)]

def ted_pos(t):
    a = ring_pos(0); stage = np.array([0, 0, 0.8], np.float32)
    p = a + (stage - a) * ease_io((t - T_SO) / 2.2)
    if t >= T_OUTRO:   # walks to the door
        door = np.array([3.3, 0, 1.6], np.float32)
        p = stage + (door - stage) * ease_io((t - T_HESAYS) / (T_HAVING + 1.2 - T_HESAYS))
    return p

def other_pos(i, t):
    a = ring_pos(i); s = SEATS[i - 1]
    k = ease_io((t - T_SIT - (i - 1) * 0.12) / 1.3)
    return a + (s - a) * k, k

# ---------------------------------------------------------------- 3D helpers
def P3(pts): return np.asarray(pts, np.float32).reshape(-1, 3)
def to2(pts, cam, W, H):
    u, v, z = project(P3(pts), cam, W, H); return np.stack([u, v], 1), z

def draw_person(lay, mask, cam, W, H, base, height, body, rim, t, gesture=0.0, finger=0.0, heart=0.0, sit=0.0, mic=False, alpha=1.0, seed=0):
    """Stylised figure: head, torso (vest), arms that gesture. Drawn as a billboard at a 3D floor point."""
    foot2, z = to2([base], cam, W, H)
    if z[0] < 0.4: return
    head3 = base + np.array([0, height, 0], np.float32)
    head2, _ = to2([head3], cam, W, H)
    hp = float(foot2[0, 1] - head2[0, 1])
    if hp < 6: return
    cx, fy = float(foot2[0, 0]), float(foot2[0, 1])
    def P(dx, dy): return (int((cx + dx * hp) * 16), int((fy - dy * hp) * 16))
    s = 1 - 0.38 * sit
    col_b = tuple(int(c * 255) for c in body); col_r = tuple(int(c * 255) for c in rim)
    th = max(1, int(hp * 0.022)); thr = max(1, int(hp * 0.012))
    def poly(pts, fill=True):
        a = np.array(pts, np.int32)
        if fill:
            cv2.fillPoly(lay, [a], col_b, cv2.LINE_AA, 4); cv2.fillPoly(mask, [a], int(255 * alpha), cv2.LINE_AA, 4)
        cv2.polylines(lay, [a], True, col_r, thr, cv2.LINE_AA, 4); cv2.polylines(mask, [a], True, int(255 * alpha), thr, cv2.LINE_AA, 4)
    def line(a, b, w):
        cv2.line(lay, a, b, col_b, w, cv2.LINE_AA, 4); cv2.line(mask, a, b, int(255 * alpha), w, cv2.LINE_AA, 4)
    # legs
    if sit < 0.5:
        line(P(-0.06, 0.0), P(-0.05, 0.45 * s), max(2, int(hp * 0.07))); line(P(0.06, 0.0), P(0.05, 0.45 * s), max(2, int(hp * 0.07)))
    # torso
    top = 0.80 * s; hip = 0.42 * s if sit < 0.5 else 0.28
    poly([P(-0.17, top), P(0.17, top), P(0.13, hip), P(-0.13, hip)])
    # vest V
    if mic:
        cv2.line(lay, P(-0.07, top), P(0.0, top - 0.17), col_r, thr, cv2.LINE_AA, 4); cv2.line(lay, P(0.07, top), P(0.0, top - 0.17), col_r, thr, cv2.LINE_AA, 4)
    # head
    hc = P(0.0, top + 0.12); r = int(hp * 0.105 * 16)
    cv2.circle(lay, hc, r, col_b, -1, cv2.LINE_AA, 4); cv2.circle(lay, hc, r, col_r, thr, cv2.LINE_AA, 4)
    cv2.circle(mask, hc, r + thr * 16, int(255 * alpha), -1, cv2.LINE_AA, 4)
    if mic:  # headset mic
        cv2.line(lay, P(0.09, top + 0.14), P(0.05, top + 0.06), col_r, max(1, thr), cv2.LINE_AA, 4)
    # arms (hidden once seated)
    for side in ((-1, 1) if sit < 0.5 else ()):
        sh = (side * 0.16, top - 0.03)
        if heart > 0 and side == -1:
            a1, a2 = math.radians(200), math.radians(330)
        else:
            sw = math.sin(t * 5.3 + side * 1.7 + seed) * 0.5 + 0.5
            up = gesture * (0.6 + 0.4 * sw) * (1.0 if side == 1 else 0.7)
            a1 = math.radians(-100 + side * 0) + side * 0
            a1 = math.radians(270 + side * (15 + 70 * up))          # upper arm: down -> out/up
            a2 = a1 + side * math.radians(25 + 80 * up)
            if finger > 0 and side == 1: a1, a2 = math.radians(300 - 50 * finger), math.radians(265 - 20 * finger + 180)
        L1 = 0.22 * s; L2 = 0.2 * s
        ex, ey = sh[0] + math.cos(a1) * L1 * (1 if side == 1 else -1) * (1 if side == 1 else -1), sh[1] + math.sin(a1) * L1
        ex = sh[0] + side * abs(math.cos(a1)) * L1 if heart == 0 or side == 1 else sh[0] + 0.02
        ey = sh[1] + math.sin(a1) * L1 if heart == 0 or side == 1 else sh[1] - 0.14
        hx = ex + side * abs(math.cos(a2)) * L2 if heart == 0 or side == 1 else 0.02
        hy = ey + math.sin(a2) * L2 if heart == 0 or side == 1 else top - 0.12
        w = max(2, int(hp * 0.05))
        line(P(*sh), P(ex, ey), w); line(P(ex, ey), P(hx, hy), w)
        cv2.circle(lay, P(hx, hy), int(hp * 0.03 * 16), col_r, -1, cv2.LINE_AA, 4)
        if finger > 0 and side == 1:
            cv2.line(lay, P(hx, hy), P(hx, hy + 0.08 * finger), col_r, max(1, thr + 1), cv2.LINE_AA, 4)

# ---------------------------------------------------------------- LED wall texture
LW, LH = 640, 320
def led_texture(t):
    tex = np.zeros((LH, LW, 3), np.float32)
    yy = np.linspace(0, 1, LH)[:, None, None]; xx = np.linspace(0, 1, LW)[None, :, None]
    ph = phase(t)
    hue = 0.5 + 0.5 * math.sin(t * 0.6)
    tex[:] = MAGENTA * (0.55 * (1 - yy)) * (0.6 + 0.4 * hue) + ORANGE * (0.5 * yy) * (1 - 0.3 * hue)
    tex *= 0.55 + 0.45 * bp(t, 5)
    # panel seams
    tex[::40] *= 0.35; tex[:, ::40] *= 0.35
    def big(s, color=WARM, size=150, y=None, font=F_DISP, op=1.0):
        spr = sprite(s, font, size, 0)
        a = spr[0]
        if a.shape[1] > LW * 0.92: a = cv2.resize(a, None, fx=LW * 0.92 / a.shape[1], fy=LW * 0.92 / a.shape[1])
        h, w = a.shape; x0 = (LW - w) // 2; y0 = (LH - h) // 2 if y is None else int(y - h / 2)
        x0, y0 = max(0, x0), max(0, y0); h = min(h, LH - y0); w = min(w, LW - x0)
        reg = tex[y0:y0 + h, x0:x0 + w]; aa = a[:h, :w, None] * op
        reg *= (1 - aa); reg += aa * color
    if ph == "stage" or ph == "final":
        if win(t, T_18 - 0.1, T_FATHER, 0.1, 0.2) > 0 or win(t, T_18b - 0.1, T_FATHERb, 0.1, 0.2) > 0:
            base = T_18 if t < T_V2 else T_18b
            secs = max(0, 18 * 60 - int((t - base) * 41))
            big(f"{secs // 60:02d}:{secs % 60:02d}", WARM, 170, LH * 0.42, F_MONOB)
            # three empty slide frames, struck through
            k = sstep(base + 1.0, base + 1.6, t)
            for i in range(3):
                x0 = 90 + i * 170; cv2.rectangle(tex, (x0, 240), (x0 + 120, 300), (1, 0.94, 0.84), 2)
                if k > 0: cv2.line(tex, (x0, 300), (x0 + int(120 * k), 240), (1, 0.3, 0.3), 4)
        for tf in (T_FATHER, T_FATHERb):
            a = win(t, tf, tf + 3.4 if tf == T_FATHER else tf + 2.0, 0.15, 0.3)
            if a > 0:  # sepia childhood photo: small kid, two tall adults shaking heads
                ph_ = np.zeros_like(tex); ph_[:] = SEPIA * 0.55
                ph_ *= (0.75 + 0.25 * np.random.default_rng(int(t * 8)).random((LH, LW, 1))).astype(np.float32)
                ink = (0.22, 0.15, 0.08)
                for k, x in enumerate((210, 430)):
                    sh_ = math.sin(t * 9 + k) * 10
                    cv2.circle(ph_, (int(x + sh_), 70), 26, ink, -1, cv2.LINE_AA); cv2.rectangle(ph_, (x - 34, 96), (x + 34, 300), ink, -1)
                cv2.circle(ph_, (320, 175), 18, ink, -1, cv2.LINE_AA); cv2.rectangle(ph_, (298, 193), (342, 300), ink, -1)
                cv2.rectangle(ph_, (12, 12), (LW - 12, LH - 12), (0.95, 0.88, 0.72), 6)
                tex = tex * (1 - a) + ph_ * a
        for tp in (T_PAUSE, T_PAUSEb):
            a = win(t, tp, tp + 3.0 if tp == T_PAUSE else tp + 2.2, 0.1, 0.3)
            if a > 0:
                tex *= (1 - 0.7 * a); n = 1 + int((t - tp) * 2.5) % 4
                big("." * n, WARM, 220, LH * 0.45, F_DISP, a)
        for ty in (T_YOUNG, T_YOUNGb):
            a = win(t, ty, ty + 4.2, 0.2, 0.4)
            if a > 0:
                tex = tex * (1 - 0.6 * a) + np.array([0.18, 0.12, 0.08], np.float32) * 0.6 * a
                big("NOBODY BELIEVED", WARM, 80, LH * 0.5, F_DISPB, a * 0.9)
        # buzzwords (verse 2)
        buzz = [(T_V2, wt("He starts every", "so"), "SO."), (T_ENDS, T_ENDS, "RIGHT?"), (T_REALQ, T_REALQ, "THE REAL QUESTION IS"),
                (T_JOURNEY, wt("He said journey", "journey"), "JOURNEY"), (T_JOURNEY, wt("He said journey", "unlock"), "UNLOCK"),
                (T_STORY, T_STORY, "LET ME TELL YOU A STORY")]
        if T_V2 - 0.3 < t < T_CAL:
            cur = None
            for _, ts_, w in buzz:
                if t >= ts_ - 0.05: cur = (ts_, w)
            if cur:
                k = ease_out((t - cur[0]) / 0.25)
                big(cur[1], WARM, int(150 * (1.25 - 0.25 * k)), LH * 0.5, F_DISP, k)
        if T_CAL - 0.2 < t < T_CH2:
            big("TED", WARM, 260, LH * 0.5, F_DISP, 0.9)
        if T_CH2 < t < T_STOP:  # concert mode: rotating rays
            ang = np.arctan2(yy - 0.5, xx - 0.5)[..., 0]
            rays = (0.5 + 0.5 * np.cos(ang * 12 + t * 3))[..., None]
            tex = tex * 0.6 + rays * (RED2 * 0.5 + AMBER * 0.4) * (0.6 + 0.6 * bp(t, 4))
            big("TED", WARM, 250, LH * 0.5, F_DISP, 0.85)
        if ph == "final":
            if t > T_NOQA - 0.2 and t < T_ALWAYS:
                tex *= 0.4; big("Q&A", WARM, 230, LH * 0.5, F_DISP)
                ka = sstep(wt("because there's no A", "A") - 0.05, wt("because there's no A", "A") + 0.25, t)
                kq = sstep(wt("never a Q", "Q") - 0.05, wt("never a Q", "Q") + 0.25, t)
                cv2.line(tex, (430, 250), (430 + int(150 * ka), 80), (1, 0.25, 0.25), 14)
                cv2.line(tex, (70, 250), (70 + int(170 * kq), 70), (1, 0.25, 0.25), 14)
            elif t >= T_ALWAYS - 0.1:   # infinite mirror of stages
                for k in range(7):
                    s = 0.85 ** k; w = int(LW * s * 0.9); h = int(LH * s * 0.85)
                    x0 = (LW - w) // 2; y0 = (LH - h) // 2
                    cv2.rectangle(tex, (x0, y0), (x0 + w, y0 + h), tuple((RED2 * (1 - k / 8)).tolist()), 3)
                    cv2.ellipse(tex, (LW // 2, y0 + int(h * 0.82)), (int(w * 0.18), int(h * 0.05)), 0, 0, 360, tuple((RED * (1 - k / 8)).tolist()), -1)
            elif t < T_NOQA - 0.2:
                big("TED", WARM, 250, LH * 0.5, F_DISP, 0.85)
    return np.clip(tex, 0, 2)

def warp_onto(dst, tex, quad2, amt=1.0):
    SH, SW = dst.shape[:2]
    src = np.float32([[0, 0], [LW, 0], [LW, LH], [0, LH]])
    M = cv2.getPerspectiveTransform(src, np.float32(quad2))
    w = cv2.warpPerspective(tex, M, (SW, SH), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    dst += w * amt

# ---------------------------------------------------------------- arena + particles
_r = np.random.default_rng(5)
CH = []
for k in range(42):
    z = -3.6 - k * 0.95; y = 0.22 * k; half = 7 + 0.55 * k
    for x in np.arange(-half, half + 0.01, 0.62): CH.append((x, y, z))
CH = np.array(CH, np.float32)
NC = 900
CONF = np.stack([_r.uniform(-8, 8, NC), _r.uniform(0, 10, NC), _r.uniform(-6, 6, NC)], 1).astype(np.float32)
CONF_C = np.array([RED2, AMBER, WARM, MAGENTA, CYAN], np.float32)[_r.integers(0, 5, NC)]
CONF_PH = _r.uniform(0, 6.28, NC).astype(np.float32)
STARS = np.stack([_r.uniform(-60, 60, 1500), _r.uniform(-5, 50, 1500), _r.uniform(20, 90, 1500)], 1).astype(np.float32)

# ---------------------------------------------------------------- camera
def camera(t):
    ph = phase(t)
    if ph == "office":
        k = sstep(0, T_SO, t)
        return orbit(lerp(0.55, -0.25, k), lerp(0.42, 0.32, k), lerp(8.5, 7.2, k), (0, 0.8, 0.5))
    if ph == "dim":
        k = ease_io((t - T_SO) / (T_CH1 - T_SO))
        return orbit(lerp(-0.25, 0.0, k), lerp(0.32, 0.1, k), lerp(7.2, 8.8, k), (0, lerp(0.8, 1.3, k), lerp(0.5, 1.2, k)))
    if ph == "stage":
        s = math.sin(t * 0.37); pk = 0.5 * bp(t, 5)
        if t < T_V2:
            k = sstep(T_CH1, T_CH1 + 1.0, t)
            return orbit(0.18 * s, 0.07 + 0.03 * math.sin(t * 0.23), lerp(8.8, 7.0, k) - pk, (0, 1.45, 1.3), roll=0.03 * s)
        if t < T_JOURNEY:
            return orbit(0.12 * s, 0.05, 5.6 - 0.6 * sstep(T_V2, T_JOURNEY, t), (0, 1.25, 0.8))
        if t < T_CH2:  # swing behind Ted: the arena of empty chairs
            k = ease_io((t - T_JOURNEY) / 3.0)
            return orbit(lerp(0.1, math.pi - 0.35, k), lerp(0.05, 0.16, k), lerp(5.0, 6.5, k), (0, 1.3, lerp(0.8, -1.0, k)))
        k = ease_io((t - T_CH2) / 1.4)
        return orbit(lerp(math.pi - 0.35, 0.12 * math.sin(t * 0.3), k), lerp(0.16, 0.30, k), lerp(6.5, 24 - 2 * pk, k), (0, 1.6, lerp(-1.0, 1.4, k)), roll=0.04 * math.sin(t * 0.5) * k)
    if ph == "bridge":
        return orbit(0, 0.1, 9, (0, 1.5, 1.5))
    if ph == "final":
        s = math.sin(t * 0.8)
        return orbit(0.3 * s, 0.08 + 0.04 * math.cos(t * 0.6), 7.6 - 1.0 * bp(t, 5), (0, 1.5, 1.4), roll=0.08 * s)
    k = ease_io((t - T_OUTRO) / 6.0); k2 = ease_io((t - T_PLACE) / 6.0)
    return orbit(lerp(0.2, 0.55, k) - 0.3 * k2, lerp(0.1, 0.18, k) + 0.4 * k2, lerp(9, 8, k) + 40 * k2, (lerp(0, 2.2, k), 1.4 + 6 * k2, 1.4))

# ---------------------------------------------------------------- scene
def light_amt(t):
    """0 = office fluorescent, 1 = stage."""
    return sstep(T_DIM, T_SIT + 0.8, t)

def render_scene(t, SW, SH, vert):
    ph = phase(t); cam = camera(t)
    if vert: cam.fov = 0.95
    la = light_amt(t)
    yy = np.linspace(0, 1, SH, dtype=np.float32)[:, None, None]
    office_bg = OFFICE * (1.1 - 0.4 * yy) + TEALG * 0.12
    stage_bg = PLUM * (0.6 + 0.8 * yy) + RED * 0.05 * (1 - yy)
    bg = office_bg * (1 - la) + stage_bg * la
    if ph == "outro": bg = bg * (1 - sstep(T_PLACE, T_PLACE + 4, t)) + np.array([0.01, 0.01, 0.03], np.float32) * sstep(T_PLACE, T_PLACE + 4, t)
    img = np.broadcast_to(bg, (SH, SW, 3)).copy().astype(np.float32)
    glow = np.zeros((SH, SW, 3), np.float32)
    edge = np.zeros((SH, SW, 3), np.uint8)
    if ph == "bridge": return img * 0.0, cam
    # floor grid (office) / stage floor
    gcol = (TEALG * 0.35 * (1 - la) + RED * 0.12 * la) * 255
    for x in np.arange(-8, 8.01, 1.0):
        q, z = to2([[x, 0, -6], [x, 0, 10]], cam, SW, SH)
        if z.min() > 0.2: cv2.line(edge, tuple((q[0] * 16).astype(int)), tuple((q[1] * 16).astype(int)), gcol.tolist(), 1, cv2.LINE_AA, 4)
    for z0 in np.arange(-6, 10.01, 1.0):
        q, z = to2([[-8, 0, z0], [8, 0, z0]], cam, SW, SH)
        if z.min() > 0.2: cv2.line(edge, tuple((q[0] * 16).astype(int)), tuple((q[1] * 16).astype(int)), gcol.tolist(), 1, cv2.LINE_AA, 4)
    # ceiling lights (office): switch off one by one on "dim the lights"
    if la < 1:
        for i, (x, z0) in enumerate([(-2, -1), (2, -1), (-2, 2), (2, 2), (-2, 5), (2, 5)]):
            on = 1 - sstep(T_DIM + i * 0.22, T_DIM + i * 0.22 + 0.08, t)
            q, z = to2([[x - 0.7, 3.2, z0 - 0.3], [x + 0.7, 3.2, z0 - 0.3], [x + 0.7, 3.2, z0 + 0.3], [x - 0.7, 3.2, z0 + 0.3]], cam, SW, SH)
            if z.min() > 0.2:
                cv2.fillConvexPoly(edge, (q * 16).astype(np.int32), (np.array([230, 245, 255]) * (0.15 + 0.85 * on)).tolist(), cv2.LINE_AA, 4)
    # red rug unrolls under Ted
    rug_r = 2.4 * ease_out((t - T_CH1) / 0.5) if t >= T_CH1 else 0
    if ph == "outro": rug_r *= 1 - 0.7 * sstep(T_PLACE, T_PLACE + 3, t)
    if rug_r > 0.05:
        ang = np.linspace(0, 2 * math.pi, 72)
        q, z = to2(np.stack([np.cos(ang) * rug_r, np.full(72, 0.01), np.sin(ang) * rug_r + 0.8], 1), cam, SW, SH)
        if z.min() > 0.2:
            rc = RED * (0.75 + 0.25 * bp(t, 6))
            rl = np.zeros((SH, SW, 3), np.float32); cv2.fillPoly(rl, [(q * 16).astype(np.int32)], rc.tolist(), cv2.LINE_AA, 4)
            img = img * (1 - (rl.sum(2, keepdims=True) > 0) * 0.0) + rl * 0.9; glow += rl * 0.5
    # LED wall
    if la > 0.2 and ph != "outro" or (ph == "outro" and t < T_PLACE + 2):
        quad, z = to2([[-6, 0.6, 5], [6, 0.6, 5], [6, 5.8, 5], [-6, 5.8, 5]], cam, SW, SH)
        if z.min() > 0.2:
            rise = sstep(T_CH1 - 0.2, T_CH1 + 0.9, t)
            if rise > 0:
                q2 = quad[[3, 2, 1, 0]]   # texture top-left -> world top-left
                q2 = q2.copy(); q2[0] = q2[3] + (q2[0] - q2[3]) * rise; q2[1] = q2[2] + (q2[1] - q2[2]) * rise
                fade = 1 - sstep(T_HAVING, T_PLACE + 1.5, t) if ph == "outro" else 1
                tl = np.zeros_like(img); warp_onto(tl, led_texture(t), q2, 1.0)
                img += tl * fade; glow += tl * 0.35 * fade
    # arena of empty chairs (visible from behind Ted / high shots)
    if ph in ("stage", "final") and (t > T_JOURNEY or ph == "final"):
        u, v, z = project(CH, cam, SW, SH)
        w = np.clip(6.0 / np.maximum(z, 0.5), 0, 1.0) * (z > 0.5) * 0.55
        splat(img, u, v, w.astype(np.float32), (RED * 0.5 + WARM * 0.3).astype(np.float32))
        u2, v2, z2 = project(CH + np.array([0, 0.35, -0.12], np.float32), cam, SW, SH)
        splat(img, u2, v2, (w * 0.6).astype(np.float32), (RED * 0.6).astype(np.float32))
    # spotlight cone + haze
    if la > 0.1 and not (ph == "outro" and t > T_PLACE + 2):
        tp = ted_pos(t); apex = np.array([tp[0] * 0.3, 7.5, -2.5], np.float32)
        ang = np.linspace(0, 2 * math.pi, 40)
        ring3 = np.stack([tp[0] + np.cos(ang) * 1.2, np.full(40, 0.02), tp[2] + np.sin(ang) * 1.2], 1)
        q, z = to2(np.vstack([apex[None], ring3]), cam, SW, SH)
        if z.min() > 0.2:
            hull = cv2.convexHull((q * 16).astype(np.int32))
            cl = np.zeros((SH, SW, 3), np.float32); cv2.fillConvexPoly(cl, hull, (WARM * 0.22 * la).tolist(), cv2.LINE_AA, 4)
            img += cv2.GaussianBlur(cl, (0, 0), 6)
    # concert beams + lasers + confetti
    if (ph == "stage" and t > T_CH2) or ph == "final":
        n = 7
        for i in range(n):
            a = math.sin(t * 0.9 + i * 0.9) * 0.6
            base = np.array([-5 + i * (10 / (n - 1)), 6.5, 4.5], np.float32)
            tip = base + np.array([math.sin(a) * 9, -6.5, -9], np.float32)
            q, z = to2([base, tip], cam, SW, SH)
            if z.min() > 0.2:
                c = [RED2, AMBER, MAGENTA, CYAN][i % 4] * (0.6 + 0.8 * bp(t, 5)) * 255
                cv2.line(edge, tuple((q[0] * 16).astype(int)), tuple((q[1] * 16).astype(int)), c.tolist(), 2, cv2.LINE_AA, 4)
        fall = ((t * 1.6 + CONF_PH) % 10)
        P = CONF.copy(); P[:, 1] = 10 - fall; P[:, 0] += 0.4 * np.sin(t * 2 + CONF_PH)
        k = sstep(T_CH2, T_CH2 + 0.3, t) if ph == "stage" else sstep(T_FINAL, T_FINAL + 0.3, t)
        u, v, z = project(P, cam, SW, SH)
        tw = 0.5 + 0.5 * np.sin(t * 9 + CONF_PH * 3)
        splat(img, u, v, (np.clip(5 / np.maximum(z, 0.5), 0, 2) * (z > 0.5) * tw * k * 1.2).astype(np.float32), CONF_C)
    # stars (outro)
    if ph == "outro" and t > T_PLACE - 1:
        u, v, z = project(STARS, cam, SW, SH)
        splat(img, u, v, (np.full(len(STARS), 0.6) * sstep(T_PLACE - 1, T_PLACE + 3, t) * (z > 1)).astype(np.float32), WARM)
    img += edge.astype(np.float32) / 255 * 1.1
    glow += edge.astype(np.float32) / 255 * 0.6
    # people
    lay = np.zeros((SH, SW, 3), np.uint8); mask = np.zeros((SH, SW), np.uint8)
    people = []
    for i in range(1, RING):
        if ph in ("outro",) and t > T_PLACE: continue
        p, k = other_pos(i, t)
        sit = k
        dim = 0.75 - 0.35 * la
        body = P_COL[i] * dim * 0.9 if la < 0.5 else np.array([0.06, 0.04, 0.07], np.float32)
        rim = P_COL[i] * (0.9 if la < 0.5 else 0.55)
        people.append((p, dict(height=1.7, body=body, rim=rim, sit=sit, seed=i, gesture=0.0)))
    tp = ted_pos(t)
    door_in = sstep(T_HAVING + 0.6, T_HAVING + 1.3, t)
    if door_in < 1 and not (ph == "bridge"):
        g = 0.0
        if T_SO <= t: g = 0.35 + 0.65 * sstep(T_CH1 - 1, T_CH1, t)
        heart = 1.0 if (win(t, T_FATHER, T_PAUSE + 3, 0.1, 0.2) > 0 or win(t, T_FATHERb, T_PAUSEb + 2.2, 0.1, 0.2) > 0) else 0.0
        frozen = win(t, T_PAUSE, T_PAUSE + 3, 0.05, 0.1) > 0 or win(t, T_PAUSEb, T_PAUSEb + 2.2, 0.05, 0.1) > 0
        finger = win(t, T_ASK + 1.0, T_DIM, 0.3, 0.3)
        body = AMBER * 0.55 if la < 0.5 else np.array([0.07, 0.04, 0.03], np.float32)
        rim = AMBER * (1.0 + 0.6 * la)
        people.append((tp, dict(height=1.85, body=body, rim=rim, gesture=g * (0 if frozen else 1), finger=finger, heart=heart,
                                mic=t >= T_CH1, seed=0, alpha=1 - door_in, tt=(T_PAUSE if frozen else t))))
    # draw far -> near
    people.sort(key=lambda pd: -float(np.linalg.norm(pd[0] - cam.pos)))
    for p, d in people:
        tt = d.pop("tt", t)
        draw_person(lay, mask, cam, SW, SH, p, d.pop("height"), d.pop("body"), d.pop("rim"), tt, **d)
    m = mask.astype(np.float32)[..., None] / 255
    img = img * (1 - m) + lay.astype(np.float32) / 255 * m
    # door of light (outro)
    if ph == "outro":
        op = sstep(T_OUTRO, T_OUTRO + 1.2, t) * (1 - sstep(T_HAVING + 1.3, T_HAVING + 2.4, t))
        wd = 0.9 * (1 - sstep(T_HAVING + 1.0, T_HAVING + 2.2, t))
        if op > 0 and wd > 0.01:
            q, z = to2([[3.3 - wd / 2, 0, 1.8], [3.3 + wd / 2, 0, 1.8], [3.3 + wd / 2, 2.3, 1.8], [3.3 - wd / 2, 2.3, 1.8]], cam, SW, SH)
            if z.min() > 0.2:
                dl = np.zeros_like(img); cv2.fillConvexPoly(dl, (q * 16).astype(np.int32), (WARM * 2.2 * op).tolist(), cv2.LINE_AA, 4)
                img += dl; glow += dl * 1.4
        # after the door closes: one point of light, far away
        sp_ = sstep(T_HAVING + 1.8, T_HAVING + 2.6, t)
        if sp_ > 0:
            q, z = to2([[3.3, 1.2, 1.8]], cam, SW, SH)
            if z[0] > 0.2:
                pt = np.zeros_like(img); cv2.circle(pt, (int(q[0, 0]), int(q[0, 1])), 2, (WARM * 3 * sp_ * (0.7 + 0.3 * math.sin(t * 3))).tolist(), -1, cv2.LINE_AA)
                img += pt; glow += pt * 4
    return img + C.bloom(glow + np.maximum(img - 0.7, 0), 0.9 + 0.8 * la * (1 + bp(t, 5))), cam

# ---------------------------------------------------------------- overlays (full res)
def hud(img, t, W, H, ts):
    """Meeting pill: clock runs ~14x so 'four minutes in' lands on 9:19."""
    if phase(t) == "bridge" or t > T_PLACE + 3: return
    vert = H > W
    mins = t * 14.4 / 60
    hh, mm = 9, 15 + int(mins)
    el = int(t * 14.4); over = el > 15 * 60
    s1 = f"Daily standup   {hh}:{mm:02d} AM"
    s2 = f"{el // 60:02d}:{el % 60:02d} / 15:00"
    fs = int(36 * ts); x = W - int((40 if not vert else 150) * ts); y = int(H * (0.05 if not vert else 0.09))
    w = int(max(text_w(s1, F_INTER, fs), text_w(s2, F_MONOB, fs)) + 70 * ts); h = int(fs * 3.0)
    card(img, x - w, y, w, h, 0.95, border=(RED2 if over else IVORY * 0.6), dark=0.7, r=int(18 * ts))
    blink = over and int(t * 2) % 2
    cv2.circle(img, (x - w + int(26 * ts), y + int(fs * 0.9)), int(9 * ts), ((RED2 if blink or not over else RED * 0.5)).tolist(), -1, cv2.LINE_AA)
    txt(img, s1, x - w + int(46 * ts), y + int(fs * 0.3), fs, WARM, 1.0, F_INTER)
    txt(img, s2, x - w + int(46 * ts), y + int(fs * 1.55), fs, RED2 if over else WARM * 0.85, 1.0, F_MONOB, 4, 0.4 if over else 0)

def bubble(img, x, y, s, op, ts, col=hexc('2b6cff'), fs=None, tail=True, seen=False):
    fs = fs or int(40 * ts); w = int(text_w(s, F_INTER, fs) + 64 * ts); h = int(fs * 2.1)
    x = int(x - w / 2); y = int(y - h / 2)
    card(img, x, y, w, h, op, border=col * 0.9, dark=0.0, r=int(h / 2.2), tint=None)
    reg = img[max(0, y):y + h, max(0, x):x + w]
    if reg.size:
        m = np.zeros(reg.shape[:2], np.uint8); cv2.rectangle(m, (0, 0), (m.shape[1] - 1, m.shape[0] - 1), 255, -1)
        reg *= (1 - 0.0);
    cv2.rectangle(img, (x + h // 2, y), (x + w - h // 2, y + h), (col * op).tolist(), -1, cv2.LINE_AA)
    cv2.circle(img, (x + h // 2, y + h // 2), h // 2, (col * op).tolist(), -1, cv2.LINE_AA)
    cv2.circle(img, (x + w - h // 2, y + h // 2), h // 2, (col * op).tolist(), -1, cv2.LINE_AA)
    txt(img, s, x + int(32 * ts), y + int(fs * 0.45), fs, WHITE, op, F_INTER)
    if seen: txt(img, "Seen", x + w - int(10 * ts), y + h + int(6 * ts), int(26 * ts), IVORY * 0.7, op, F_INTER) if False else \
        blit(img, sprite("Seen", F_INTER, int(28 * ts)), x + w - text_w("Seen", F_INTER, int(28 * ts)), y + h + int(8 * ts), IVORY * 0.75, op)

def question(img, t, W, H, ts):
    """'is the file ready?' — asked, ignored, orbits the stage (circle back), still unanswered at the end."""
    vert = H > W
    s = "is the file ready?"
    a = win(t, T_ASK, T_SO + 1.2, 0.2, 0.5)
    if a > 0:
        bubble(img, W * 0.3 if not vert else W * 0.42, H * (0.62 if not vert else 0.6), s, a, ts)
    a = win(t, T_CIRCLE, T_YOUNG, 0.3, 0.5)
    if a > 0:
        ang = (t - T_CIRCLE) * 1.6
        rx, ry = (W * 0.32, H * 0.22) if not vert else (W * 0.3, H * 0.16)
        bubble(img, W / 2 + math.cos(ang) * rx, H * 0.42 + math.sin(ang) * ry, s, a, ts)
    a = win(t, T_REACH + 0.6, DUR, 0.5, 0.1) * (1 - sstep(DUR - 4.0, DUR - 3.0, t))
    if a > 0:
        bubble(img, W / 2, H * 0.62, s, a, ts, seen=True)

def calendar(img, t, W, H, ts):
    a = win(t, T_CAL - 0.4, T_CH2 + 0.4, 0.3, 0.4)
    if a <= 0: return
    vert = H > W
    w = int((520 if not vert else 760) * ts); h = int(560 * ts); x = int(W * 0.06) if not vert else (W - w) // 2; y = int(H * 0.14)
    card(img, x, y, w, h, a, border=IVORY * 0.6, dark=0.78, r=int(18 * ts))
    txt(img, "My calendar", x + int(28 * ts), y + int(20 * ts), int(36 * ts), WARM, a, F_INTER)
    melt = sstep(T_GIVEUP - 0.6, T_GIVEUP + 1.0, t)
    items = [("Deep work", hexc('5b8cff')), ("Lunch", hexc('39d98a')), ("1:1 with Priya", hexc('ffb347')), ("Ship the file", hexc('ff5a4f')), ("Gym", hexc('c9b3ff'))]
    for i, (s, c) in enumerate(items):
        drop = melt * (60 + 90 * i) * ts * (1 + melt * 2); rot = melt * (i % 2 * 2 - 1) * 8
        yy = y + int(90 * ts) + i * int(88 * ts) + int(drop)
        if yy + int(70 * ts) > y + h - 4: continue
        cv2.rectangle(img, (x + int(28 * ts), yy), (x + w - int(28 * ts), yy + int(70 * ts)), (c * 0.55 * a).tolist(), -1, cv2.LINE_AA)
        txt(img, s, x + int(48 * ts), yy + int(14 * ts), int(36 * ts), WHITE, a * (1 - 0.6 * melt), F_INTER)
    if melt > 0.6:
        txt(img, "Busy: Ted", x + int(28 * ts), y + h - int(80 * ts), int(44 * ts), RED2, a * sstep(0.6, 1.0, melt), F_DISPB, 6, 0.5)

def final_cards(img, t, W, H, ts):
    vert = H > W
    a = win(t, T_NOSCHED - 0.1, T_NOEND + 0.2, 0.2, 0.3)
    if a > 0:
        fs = int(38 * ts); w = int((640 if not vert else 820) * ts); h = int(250 * ts); x = (W - w) // 2; y = int(H * (0.16 if not vert else 0.2))
        card(img, x, y, w, h, a, border=AMBER, dark=0.8, r=int(20 * ts))
        txt(img, "TED Talk", x + int(30 * ts), y + int(24 * ts), int(48 * ts), WARM, a, F_DISPB)
        txt(img, "Organizer: nobody", x + int(30 * ts), y + int(100 * ts), fs, IVORY * 0.9, a, F_INTER)
        txt(img, "Repeats: forever", x + int(30 * ts), y + int(160 * ts), fs, IVORY * 0.9, a, F_INTER)
    a = win(t, T_NOEND - 0.1, T_NOQA - 0.1, 0.2, 0.3)
    if a > 0:
        fs = int(44 * ts); s = "End meeting"; w = int(text_w(s, F_DISPB, fs) + 90 * ts); h = int(fs * 2.1)
        clicks = int((t - T_NOEND) * 4); shake = (math.sin(t * 60) * 10 * ts) if (t - T_NOEND) * 4 % 1 < 0.3 else 0
        x = int(W / 2 - w / 2 + shake); y = int(H * (0.5 if not vert else 0.45))
        cv2.rectangle(img, (x, y), (x + w, y + h), (RED * a).tolist(), -1, cv2.LINE_AA)
        txt(img, s, x + int(45 * ts), y + int(fs * 0.45), fs, WHITE, a, F_DISPB)
        cx, cy = x + int(w * 0.7), y + int(h * 0.7) + int(6 * ts * ((t * 4) % 1 < 0.3))
        cur = np.array([[0, 0], [0, 34], [9, 26], [16, 40], [22, 37], [15, 24], [27, 24]], np.float32) * ts * 1.4 + [cx, cy]
        cv2.fillPoly(img, [cur.astype(np.int32)], (np.array([1, 1, 1]) * a).tolist(), cv2.LINE_AA)
        cv2.polylines(img, [cur.astype(np.int32)], True, (np.array([0, 0, 0]) * a).tolist(), max(1, int(2 * ts)), cv2.LINE_AA)
        txt(img, f"clicked {clicks + 1}×", x + w + int(20 * ts), y + int(fs * 0.6), int(34 * ts), IVORY * 0.8, a, F_MONOB)

def bridge(img, t, W, H, ts):
    """Hard stop -> the call grid. Ted has used six of fifteen minutes. Dana is a ghost now."""
    if not (T_STOP - 0.05 <= t < T_FINAL - 0.6): return
    vert = H > W
    img[:] = hexc('0c0d10')
    a = sstep(T_TED - 0.15, T_TED + 0.1, t)
    if a <= 0: return
    cols, rows = (4, 2) if not vert else (2, 4)
    gx0, gy0 = int(W * 0.06), int(H * (0.16 if not vert else 0.12))
    gw = W - 2 * gx0; gh = int(H * (0.56 if not vert else 0.52)); gap = int(14 * ts)
    tw_ = (gw - gap * (cols - 1)) // cols; th_ = (gh - gap * (rows - 1)) // rows
    push = sstep(T_DIDTHAT, T_DIDTHAT + 3.0, t)
    for i, name in enumerate(NAMES):
        c, r = i % cols, i // cols
        x = gx0 + c * (tw_ + gap); y = gy0 + r * (th_ + gap)
        dana = name == "Dana"; ted = name == "Ted"
        dim = 1 - 0.75 * push * (0 if ted else 1)
        base = hexc('1b1d22') * dim
        cv2.rectangle(img, (x, y), (x + tw_, y + th_), base.tolist(), -1)
        talk = ted and (int(t * 6) % 2 == 0)
        bc = (GREEN if ted else IVORY * 0.25) * dim
        cv2.rectangle(img, (x, y), (x + tw_, y + th_), bc.tolist(), max(2, int((5 if ted else 2) * ts)), cv2.LINE_AA)
        cx, cy = x + tw_ // 2, y + int(th_ * 0.45); rr = int(min(tw_, th_) * 0.2)
        if dana:
            g = sstep(T_GHOST, T_GHOST + 1.2, t); age = sstep(T_TWO - 0.3, T_TWO + 0.6, t)
            if g < 1:
                cv2.circle(img, (cx, cy), rr, (P_COL[i] * 0.6 * (1 - age * 0.6) * (1 - g) * dim).tolist(), -1, cv2.LINE_AA)
                txt(img, "D", cx, cy, int(rr * 1.1), WHITE * (1 - g), dim * (1 - g), F_DISPB, anchor='c')
            if age > 0:  # cobwebs
                for k in range(3):
                    cv2.line(img, (x, y + int(k * 26 * ts)), (x + int((80 - k * 20) * ts), y), (IVORY * 0.35 * age * dim).tolist(), 1, cv2.LINE_AA)
                    cv2.line(img, (x + tw_, y + th_ - int(k * 26 * ts)), (x + tw_ - int((80 - k * 20) * ts), y + th_), (IVORY * 0.35 * age * dim).tolist(), 1, cv2.LINE_AA)
            if g > 0:  # a sheet ghost, floating
                bob = math.sin(t * 2.4) * rr * 0.12
                gh_ = [];
                for k in range(19):
                    an = math.pi + k * math.pi / 18; gh_.append((cx + math.cos(an) * rr, cy - rr * 0.2 + math.sin(an) * rr + bob))
                for k in range(9):
                    gh_.append((cx + rr - k * rr * 2 / 8, cy + rr * 1.05 + (8 if k % 2 else 0) * ts + bob))
                pts = np.array(gh_, np.int32)
                gl = np.zeros_like(img); cv2.fillPoly(gl, [pts], (GHOST * 0.75 * g).tolist(), cv2.LINE_AA)
                img += cv2.GaussianBlur(gl, (0, 0), 3 * ts) * 0.5 + gl * 0.55 * dim
                for ex in (-0.35, 0.35):
                    cv2.circle(img, (int(cx + ex * rr), int(cy - rr * 0.25 + bob)), max(3, int(rr * 0.12)), (np.array([0.05, 0.05, 0.08]) * g).tolist(), -1, cv2.LINE_AA)
            if T_HARD - 0.1 < t:
                badge = "hard stop 9:30" if t < T_TWO - 0.2 else "hard stop · since 2024"
                fs = int(30 * ts); bw = int(text_w(badge, F_INTER, fs) + 30 * ts)
                cv2.rectangle(img, (x + int(12 * ts), y + int(12 * ts)), (x + int(12 * ts) + bw, y + int(12 * ts) + int(fs * 1.6)), (RED * 0.85 * dim).tolist(), -1, cv2.LINE_AA)
                txt(img, badge, x + int(27 * ts), y + int(16 * ts), fs, WHITE, dim * sstep(T_HARD - 0.1, T_HARD + 0.2, t), F_INTER)
        else:
            cv2.circle(img, (cx, cy), rr, (P_COL[i] * (0.9 if ted else 0.55) * dim).tolist(), -1, cv2.LINE_AA)
            txt(img, name[0], cx, cy, int(rr * 1.1), hexc('101114'), 1.0, F_DISPB, anchor='c')
            if ted and talk: cv2.circle(img, (cx, cy), rr + int(10 * ts), (GREEN * 0.8).tolist(), max(2, int(4 * ts)), cv2.LINE_AA)
        lab = name + (" (ghost)" if dana and t > T_GHOST + 0.6 else "") + (" · speaking" if ted else "")
        txt(img, lab, x + int(16 * ts), y + th_ - int(54 * ts), int(34 * ts), WHITE * dim, 1.0, F_INTER)
    # title + timer bar
    if t > T_STANDUP - 0.15:
        o = sstep(T_STANDUP - 0.15, T_STANDUP + 0.15, t)
        txt(img, "Daily standup  ·  15 min  ·  8 people", gx0, int(H * (0.07 if not vert else 0.06)), int(44 * ts), WARM, o * (1 - 0.6 * push), F_DISPB)
    if t > T_FIFTEEN - 0.1:
        o = sstep(T_FIFTEEN - 0.1, T_FIFTEEN + 0.2, t) * (1 - 0.6 * push)
        by = gy0 + gh + int(50 * ts); bh = int(34 * ts)
        cv2.rectangle(img, (gx0, by), (gx0 + gw, by + bh), (IVORY * 0.18 * o).tolist(), -1)
        for k in range(1, 8):
            xx = gx0 + gw * k // 8; cv2.line(img, (xx, by), (xx, by + bh), (hexc('0c0d10')).tolist(), max(2, int(3 * ts)))
        used = sstep(T_SIX - 0.1, T_SIX + 1.0, t) * (6 / 15)
        if used > 0:
            cv2.rectangle(img, (gx0, by), (gx0 + int(gw * used), by + bh), (RED2 * o).tolist(), -1)
            txt(img, "Ted: 6:00", gx0 + int(gw * used) + int(14 * ts), by - int(4 * ts), int(40 * ts), RED2, o, F_DISPB)
        txt(img, "15:00", gx0 + gw, by + bh + int(12 * ts), int(34 * ts), IVORY * 0.7, o, F_MONOB) if False else None
    # the stop: black flash right at the cut
    img *= sstep(T_STOP - 0.05, T_STOP + 0.25, t) * 0.0 + (1 - 0.9 * (1 - sstep(T_STOP, T_TED - 0.1, t)))

def end_card(img, t, W, H, ts):
    e = sstep(DUR - 4.0, DUR - 3.0, t)
    if e <= 0: return
    img *= (1 - 0.65 * e)
    txt(img, "aditazzz", W / 2, H * 0.48, int(120 * ts), WHITE, e, F_DISPB, 12, 0.6, anchor='c')
    blit(img, sprite("T E D   T A L K", F_INTER, int(44 * ts)), W / 2, H * 0.48 + 110 * ts, RED2, e, anchor='c')

# ---------------------------------------------------------------- frame
def render_frame(t, W=1920, H=1080, fi=0):
    vert = H > W; ts = min(W, H) / 1080
    SW, SH = (W * 2 // 3) // 2 * 2, (H * 2 // 3) // 2 * 2
    sc, cam = render_scene(t, SW, SH, vert)
    img = cv2.resize(C.tonemap(sc, 1.0), (W, H), interpolation=cv2.INTER_LINEAR)
    if not C.STATE["clean"]:
        bridge(img, t, W, H, ts)
        hud(img, t, W, H, ts)
        question(img, t, W, H, ts)
        calendar(img, t, W, H, ts)
        final_cards(img, t, W, H, ts)
        C.overlay_stamp(img, t, W, H, TM, word="TED TALK", caption=("it's always a" if t > T_ALWAYS - 0.3 else "it's a"),
                        glow_color=RED2, caption_above=True, hide=lambda tt: phase(tt) == "bridge")
        skip = lambda L: L['text'].startswith("It's a Ted talk") or L['text'].startswith("It's always")
        C.overlay_lyrics(img, t, W, H, TM, active=hexc('ffd27a'), glow=AMBER, skip=skip, band=phase(t) != "bridge")
        end_card(img, t, W, H, ts)
    else:
        bridge(img, t, W, H, ts) if phase(t) == "bridge" else None
    # flashes: stage reveal, each stamp, final return
    fl = 0.0
    for s in TM.stamps:
        if 0 <= t - s < 1: fl += 0.3 * math.exp(-(t - s) * 7)
    if 0 <= t - T_FINAL < 2: fl += 0.6 * math.exp(-(t - T_FINAL) * 3)
    gl = 0.0
    if 0 <= t - T_STOP < 0.25: gl += 0.8
    for s in TM.stamps:
        if 0 <= t - s < 0.12: gl += 0.3
    return C.finish(img, t, fi, DUR, flash=fl, flash_col=hexc('ffe2c4'), glitch_amt=gl)
