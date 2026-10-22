"""TED Talk, as screenlife: the whole song happens on her laptop screen.

The standup is a video call. Ted is the host. Everything is told with the screen: the meeting timer, her chat
message that never gets answered, Ted literally stepping back from his webcam, dark mode when somebody dims the
lights, cameras switching off when everybody sits down, his "keynote" virtual background, the slides he shares
(blank), the photo of his father, a loading circle for circling back, a tally of every "so", buzzword bingo, her
calendar crashing, the participants list at the bridge (Dana: last seen 2 years ago), the End-meeting button nobody
is allowed to press, and at the end a DM to Ted that can't be delivered. A camera moves over the screen like in a
screenlife film."""
import os, sys, math
from types import SimpleNamespace
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path: sys.path.insert(0, HERE)
from studio import core as C
from studio.core import sstep, ease_out, ease_io, clamp, lerp
import ui as U
import avatars as A
import apps as AP

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
T_RAFTER = [lt("right after the part", i) for i in (0, 1)]; T_YOUNG = [lt("where he was young", i) for i in (0, 1)]
T_NOBODY = [lt("nobody believed", i) for i in (0, 1)]; T_BELIEVE_E = [le("nobody believed", i) for i in (0, 1)]
T_V2 = TM.section("V2")["s"]; T_SOw = wt("He starts every", "so."); T_RIGHT = wt("He ends every", "right?")
T_REALQ = lt("He says, the real"); T_REAL = wt("He says, the real", "real"); T_ABOUTQ = lt("about the question")
T_JOURNEY = wt("He said journey", "journey."); T_UNLOCK = wt("He said journey", "unlock."); T_STORY = lt("let me tell you")
T_STORYw = wt("let me tell you", "story,"); T_CAL = lt("and I watched my calendar"); T_GIVEUP = lt("give up")
T_CH2 = TM.section("CH2")["s"]; T_TED = lt("Ted."); T_STANDUP = lt("This is a standup")
T_FIFTEEN = lt("It is fifteen"); T_EIGHT = lt("for eight people"); T_SIX = lt("You have used six"); T_HARD = lt("Dana had a hard stop")
T_HAS = lt("Dana has had"); T_TWO = lt("for two years"); T_GHOST = lt("Dana is a ghost"); T_DIDTHAT = lt("You did that")
T_FINAL = TM.section("FINAL")["s"]; T_NOSCHED = lt("Nobody scheduled"); T_NOEND = lt("Nobody can end"); T_NOQA = lt("There's no Q")
T_NOA = lt("because there's no A"); T_NEVERQ = lt("because there was never"); T_ANYWAY = lt("Anyway"); T_HESAYS = lt("He says.")
T_HAVING = lt("Having taken"); T_PLACE = lt("Into a place"); T_REACH = lt("none of us"); T_END = 157.2
T_PILL = T_V2 + 0.3
T_NEVERQ_Q = wt("because there was never", "Q.")
T_OPEN = 1.65                     # she clicks Join
JOIN = {"Ted": 2.25, "Dana": 2.6, "Priya": 2.9, "Marcus": 3.2, "Sam": 3.5, "Lee": 3.8, "Jo": 4.1, "Me": 4.4}

def kf(t, keys):
    """piecewise ease between (time, value) keys; values may be tuples"""
    if t <= keys[0][0]: return keys[0][1]
    for (a, va), (b, vb) in zip(keys[:-1], keys[1:]):
        if a <= t <= b:
            k = ease_io((t - a) / max(b - a, 1e-6))
            if isinstance(va, tuple): return tuple(lerp(x, y, k) for x, y in zip(va, vb))
            return lerp(va, vb, k)
    return keys[-1][1]

def kf_lin(t, keys):
    if t <= keys[0][0]: return keys[0][1]
    for (a, va), (b, vb) in zip(keys[:-1], keys[1:]):
        if a <= t <= b: return lerp(va, vb, (t - a) / max(b - a, 1e-6))
    return keys[-1][1]

def win(t, a, b, fi=0.3, fo=0.3): return sstep(a - fi, a, t) * (1 - sstep(b, b + fo, t))

# ---------------------------------------------------------------- meeting time (fast-forwarded story time)
MEET = [(0, 0.0), (4.6, 0.0), (T_FOUR, 4.0), (T_DIM, 5.6), (T_18[0] - 0.2, 6.3), (T_18[0] + 0.7, 18.0), (T_V2, 22.0), (T_CH2, 27.4),
        (T_18[1] - 0.2, 28.0), (T_18[1] + 0.7, 45.0), (T_TED, 49.0), (T_FINAL, 53.0), (T_ANYWAY, 61.0), (DUR, 64.0)]
def meet_min(t): return kf_lin(t, MEET)

# ---------------------------------------------------------------- layout constants (desktop units)
HUD = (14.0, 34.0, 872.0, 612.0)
PANEL_W = 262.0
def btn_xy(i):          # the control bar buttons: mic, video, share, react, raise, captions, chat, people, more
    x, y, w, h = HUD; n = 9; bw = 52; x0 = x + (w - 120) / 2 - n * bw / 2
    return x0 + i * bw + bw / 2, y + h - 28
B_MIC, B_HAND, B_CC, B_CHAT, B_PEOPLE = btn_xy(0), btn_xy(4), btn_xy(5), btn_xy(6), btn_xy(7)
B_LEAVE = (HUD[0] + HUD[2] - 96 + 40, HUD[1] + HUD[3] - 28)
PANEL_X = HUD[0] + HUD[2] - 10 - PANEL_W + 6
CHAT_IN = (PANEL_X + 120, HUD[1] + 64 + (HUD[3] - 120) - 25)
CHAT_SEND = (PANEL_X + PANEL_W - 6 - 30, CHAT_IN[1])
NOTES_R = (900.0, 34.0, 366.0, 300.0)
CAL_R = (900.0, 344.0, 366.0, 302.0)
DM_R = (900.0, 150.0, 366.0, 420.0)

# ---------------------------------------------------------------- the story, as state
def talking(t):
    quiet = any(a - 0.05 < t < b for a, b in ((T_PAUSE[0], T_PAUSE_E[0]), (T_PAUSE[1], T_PAUSE_E[1]), (T_TED - 0.1, T_FINAL - 0.4),
                                              (T_HAVING, DUR)))
    if quiet or t < 4.0: return 0.0
    return max(0.0, 0.35 + 0.35 * math.sin(t * 2 * math.pi * 4.1) + 0.3 * math.sin(t * 2 * math.pi * 6.7 + 1))

def singing(t):
    """her mouth when she speaks at the bridge: open on the sung words"""
    for L in TM.lines:
        if T_TED - 0.05 <= L['s'] <= T_FINAL and L['s'] - 0.05 <= t <= L['e'] + 0.05:
            for w_, tt in zip(L['words'], L['wt']):
                if tt - 0.02 <= t <= tt + 0.22: return 0.25 + 0.45 * abs(math.sin((t - tt) * 14))
    return 0.0

def stage_bg(t):
    return any(a <= t < b for a, b in ((TT[0] - 0.25, T_V2 + 0.4), (TT[2] - 0.25, T_TED), (TT[4] - 0.25, T_ANYWAY + 0.3)))

def ted_state(t):
    st = A.St(cx=80.0, cy=42.0, s=13.0, body=True)
    on_stage = stage_bg(t)
    # stepping back: he walks away from his webcam; on the "stage" he stands back in the spotlight
    d = 0.0
    d = max(d, 0.78 * ease_io((t - T_STEP) / 0.75) * (1 - sstep(TT[0] - 0.3, TT[0] - 0.25, t)))
    if on_stage: d = 0.56
    st.d = d
    e = ease_io(d)
    st.s = lerp(13.0, 4.4, e); st.cy = lerp(42.0, 72 - 9.9 * 4.4, e)
    st.mouth = talking(t) * (0.9 if d < 0.3 else 0.7)
    st.blink = A.blink_at(t, 1.0)
    st.brow = 0.25 + 0.2 * math.sin(t * 1.3); st.tilt = 0.04 * math.sin(t * 1.1)
    st.gaze = (0.0, 0.0)
    beat = math.sin(t * 2 * math.pi * 143.55 / 60 / 2)
    g = sstep(T_V1, T_V1 + 0.6, t)
    st.hands = [(-1, 0.25 + g * (0.55 + 0.35 * beat), 1.2 + g * 0.6), (1, 0.15 + g * (0.35 - 0.2 * beat), 0.9 + g * 0.5)] if d > 0.25 else \
               ([(-1, 0.9 + 0.5 * beat, 1.6)] if g > 0.5 and talking(t) > 0 and (t * 0.7) % 2 < 1.2 else None)
    # "so —": both hands up
    if T_SO - 0.1 < t < T_STEP + 1.2:
        st.hands = [(-1, 2.5, 0.5), (1, 2.5, 0.5)]; st.brow = 0.7
    # the pause he thinks is powerful: one finger up, frozen
    for a, b in zip(T_PAUSE, T_PAUSE_E):
        if a - 0.1 < t < b + 0.3:
            st.hands = [(-1, 2.9, 0.15), (1, 0.15, 0.3)]; st.mouth = 0.0; st.brow = 0.6; st.tilt = -0.08
    # circling back: a slow turn (he paces)
    for a, b in zip(T_CIRCLE, T_CIRCLE_E):
        if a < t < b:
            st.cx = 80 + 26 * math.sin((t - a) / (b - a) * 2 * math.pi) * (1 if on_stage else 0.4)
    # the bridge: he goes quiet; "You did that": he looks down
    if T_TED - 0.1 < t < T_FINAL - 0.4:
        st.hands = None; st.mouth = 0.0; st.brow = -0.1 + 0.6 * sstep(T_TED - 0.1, T_TED + 0.2, t) * (1 - sstep(T_STANDUP, T_STANDUP + 0.6, t))
        k = sstep(T_DIDTHAT, T_DIDTHAT + 0.6, t)
        st.gaze = (0.0, 0.8 * k); st.tilt = 0.12 * k; st.cy += 3 * k
    if t > T_ANYWAY + 0.2:     # "happy to take this offline": a little bow
        k = sstep(T_ANYWAY + 1.2, T_ANYWAY + 1.8, t) * (1 - sstep(T_HESAYS, T_HESAYS + 0.5, t))
        st.cy += 5 * k * (st.s / 13); st.tilt = 0.1 * k
    return st

def me_state(t):
    st = A.St(cx=80.0, cy=42.0, s=13.0)
    st.blink = A.blink_at(t, 2.3); st.smile = 0.15; st.tilt = 0.02 * math.sin(t * 0.9 + 1)
    typing = any(a < t < b for a, b in TYPE_WINDOWS)
    if typing: st.gaze = (0.15, 0.85); st.tilt = 0.05
    if T_FOUR - 0.3 < t < T_ASK - 0.2: st.brow = -0.25; st.blink = max(st.blink, 0.35); st.smile = -0.3      # four minutes in
    if T_SO < t < T_DIM + 0.5: st.brow = 0.75; st.mouth = 0.12                                              # stepping back?!
    if T_CH1 < t < T_V2 and int(t / 4.3) % 3 == 1: st.gaze = (0.0, -0.9); st.brow = 0.3; st.smile = -0.2        # eye roll
    if T_CH2 < t < T_TED and int(t / 3.9) % 3 == 2: st.gaze = (0.0, -0.9); st.brow = 0.3; st.smile = -0.2
    if T_TED - 0.15 < t < T_FINAL:                                                                           # she speaks
        st.mouth = singing(t); st.brow = -0.35; st.smile = 0.0; st.gaze = (0.0, 0.0)
    if t > T_PLACE: st.smile = -0.1; st.brow = 0.1
    return st

def other_state(name, t):
    st = A.St(cx=80.0, cy=42.0, s=13.0)
    seed = {"Dana": 3.1, "Priya": 4.7, "Marcus": 5.3, "Sam": 6.9, "Lee": 7.7, "Jo": 8.3}[name]
    st.blink = A.blink_at(t, seed); st.tilt = 0.03 * math.sin(t * 0.8 + seed); st.cx = 80 + 1.5 * math.sin(t * 0.5 + seed)
    st.smile = 0.2
    if T_FOUR - 0.5 + seed * 0.07 < t < T_ASK:                  # four minutes in: everyone drifts
        st.blink = max(st.blink, 0.45); st.smile = -0.2; st.tilt = 0.08 * math.sin(seed)
        if name == "Marcus": st.eyes_closed = 1.0; st.tilt = 0.18
    if name == "Priya" and T_SO < t < T_DIM: st.mouth = 0.5; st.eyes_closed = 1.0                       # laughing
    if T_TED < t < T_FINAL: st.brow = 0.5; st.gaze = (0.3 if name in ("Dana", "Priya", "Marcus") else -0.3, 0.0)   # they all look up
    return st

TYPE_WINDOWS = [(7.2, 8.7), (20.5, 21.2), (T_NEVERQ - 0.1, T_NEVERQ + 1.1), (T_PLACE + 0.9, T_PLACE + 2.6)]

def messages(t):
    M = []
    def add(at, who, text, tm, **kw):
        if t >= at: M.append(dict(who=who, text=text, time=tm, k=ease_out((t - at) / 0.25), **kw))
    add(8.85, "Me", "is the file ready?", "9:16", hl=0.7 * win(t, T_ASK, T_ASK + 2.2, 0.2, 0.4) + 0.7 * win(t, T_ABOUTQ, T_ABOUTQ + 1.6, 0.2, 0.4))
    add(10.75, "Ted", "Love this question!! So, stepping back for a sec: what does ready even mean? Is any file ever truly ready? "
                      "I'd argue the real question is", "9:16", clip=3)
    add(21.3, "Me", "the file?", "9:19")
    add(T_PAUSE[0] + 0.9, "Sam", "Ted you froze", "9:38")
    add(T_PAUSE[0] + 1.6, "Marcus", "he's buffering", "9:38")
    add(T_PAUSE[0] + 2.4, "Priya", "it's a pause. for effect", "9:38")
    add(T_CIRCLE[0] + 1.0, "Ted", "Great point, will circle back on this!", "9:40")
    add(T_ABOUTQ + 0.15, "Ted", "“is the file ready?” The real question is: what IS a file?", "9:44")
    add(T_PAUSE[1] + 0.9, "Jo", "is this still the standup", "10:07")
    add(T_PAUSE[1] + 1.7, "Lee", "?", "10:07")
    add(T_ANYWAY + 0.3, "Ted", "Anyway! Happy to take this offline", "10:16")
    return M

def notifs(t):
    L = []
    def add(a, b, app, title, body, col, glyph, y, **kw):
        k = ease_out((t - a) / 0.35) * (1 - ease_io((t - b) / 0.35)) if t >= a else 0.0
        if a == 0.0: k = 1.0 * (1 - ease_io((t - b) / 0.35))
        if k > 0: L.append(dict(k=k, app=app, title=title, body=body, col=col, glyph=glyph, y=y, **kw))
    add(0.0, T_OPEN + 0.1, "Calendar", "Daily Standup", "9:15 – 9:30 AM · Huddle", U.hexc("ef4444"), "cal", 36.0, button="Join",
        btn_hl=sstep(T_OPEN - 0.25, T_OPEN - 0.2, t), g="21")
    add(T_DIFF + 0.4, T_ASK - 0.6, "Chatter", "Priya", "did he just answer you with a question", AP.H("8b5cf6"), "chat", 36.0)
    add(T_DIFF + 1.6, T_ASK - 0.6, "Chatter", "Dana", "fyi I have a hard stop at 9:30", AP.H("8b5cf6"), "chat", 118.0)
    add(T_CIRCLE[0] + 2.4, T_RAFTER[0] + 0.4, "Chatter", "Priya", "he's circling back to the circle back", AP.H("8b5cf6"), "chat", 36.0)
    add(T_18[1] + 1.0, T_FATHER[1] - 0.3, "Calendar", "1:1 with Dana", "Started 15 minutes ago", U.hexc("ef4444"), "cal", 36.0, g="21")
    add(T_HARD + 0.25, T_HAS + 0.8, "Huddle", "Dana left the meeting", "Daily Standup", AP.ACCENT, "people", 36.0)
    add(T_ANYWAY + 1.0, T_HAVING - 0.2, "Chatter", "Priya", "he's taking it offline", AP.H("8b5cf6"), "chat", 36.0)
    return L

def cal_events(t):
    """her day. The standup grows down the calendar and pushes everything else off the end of the day"""
    grow = kf(t, [(T_CAL - 0.3, 0.0), (T_GIVEUP - 0.2, 1.0)])
    end = 9.5 + grow * 3.3
    evs = [dict(s=9.25, e=end, t="Daily Standup", sub="Huddle · Ted (host)", c=AP.ACCENT)]
    push = max(0.0, end - 9.5)
    for (a, b, title, col) in ((9.5, 10.0, "Sprint planning", AP.H("10b981")), (10.0, 10.5, "1:1 with Dana", AP.H("ec4899")),
                               (11.0, 12.0, "Design review", AP.H("f59e0b")), (12.0, 12.75, "Lunch", AP.H("6b7280"))):
        evs.append(dict(s=a + push, e=b + push, t=title, c=col, op=1.0))
    return evs

def state(t, vert):
    S = SimpleNamespace()
    S.t = t
    # theme: dark mode when somebody dims the lights; light again at "Ted."; dark again for the final; light when he's gone
    S.dark = sstep(T_DIM + 0.1, T_DIM + 0.9, t) * (1 - sstep(T_TED - 0.05, T_TED + 0.35, t)) + \
             sstep(TT[4] - 0.2, TT[4] + 0.5, t) * (1 - sstep(T_HAVING + 0.5, T_HAVING + 1.5, t))
    mm = meet_min(t)
    clock = 9 * 60 + 15 + mm
    hh, mi = int(clock // 60), int(clock % 60)
    S.clock_text = "Tue Oct 21  %d:%02d AM" % (hh if hh <= 12 else hh - 12, mi)
    S.dock_day = "21"; S.dock_running = {"huddle", "chat", "notes", "cal"}
    secs = int(mm * 60)
    S.timer_text = "%02d:%02d" % (secs // 60, secs % 60) if secs < 3600 else "%d:%02d:%02d" % (secs // 3600, (secs // 60) % 60, secs % 60)
    S.timer_red = mm >= 15.0
    S.ends_text = "Ends 9:30 AM" if mm < 15 else "Ended %d min ago" % int(mm - 15) if mm < 16 or mm >= 16 else ""
    if 15 <= mm < 16: S.ends_text = "Ended just now"
    # the window
    k_open = ease_out((t - T_OPEN) / 0.45)
    x, y, w, h = HUD; s_ = 0.94 + 0.06 * k_open
    S.hud = (x + w * (1 - s_) / 2, y + h * (1 - s_) / 2, w * s_, h * s_) if k_open < 1 else HUD
    gone = sstep(T_HAVING + 1.6, T_HAVING + 2.1, t)
    S.hud_op = k_open * (1 - gone)
    S.title = "Ted's Talk" if stage_bg(t) and t < T_ANYWAY else "Daily Standup"
    S.rec = sstep(TT[0], TT[0] + 0.3, t) * (1 - sstep(T_HAVING, T_HAVING + 0.3, t))
    # who is here
    S.present = {p: sstep(JOIN[p], JOIN[p] + 0.25, t) for p in AP.PEOPLE_ORDER}
    S.present["Dana"] *= 1 - sstep(T_HARD + 0.15, T_HARD + 0.5, t) * (1 - sstep(T_GHOST - 0.1, T_GHOST + 0.4, t)) \
                         if t < T_FINAL + 0.8 else 1 - sstep(T_HARD + 0.15, T_HARD + 0.5, t)
    S.present["Ted"] *= 1 - sstep(T_HAVING + 0.7, T_HAVING + 1.0, t)
    S.n_present = sum(1 for v in S.present.values() if v > 0.5)
    S.ghost = sstep(T_GHOST - 0.1, T_GHOST + 0.6, t) * (1 - sstep(T_FINAL + 0.4, T_FINAL + 0.8, t))
    # cameras: everybody sits down (cameras off) at "sit down"; back on at "Ted."; off again in the final
    off_at = {"Dana": 0.0, "Priya": 0.15, "Marcus": 0.3, "Sam": 0.45, "Lee": 0.6, "Jo": 0.75}
    S.cam_on = {}
    for p in AP.PEOPLE_ORDER:
        if p in off_at:
            on = 1.0
            if T_SIT + off_at[p] < t < T_TED + 0.3 + off_at[p] * 0.5: on = 0.0
            if t > T_FINAL + 0.6 + off_at[p]: on = 0.0
            S.cam_on[p] = on
        else: S.cam_on[p] = 1.0
    # muted mics; who is speaking
    S.my_mic = T_TED - 0.25 < t < T_FINAL + 0.3
    S.muted = {p: True for p in AP.PEOPLE_ORDER}
    S.muted["Ted"] = not (4.0 < t < T_HAVING + 0.6); S.muted["Me"] = not S.my_mic
    S.speaking = {"Ted": 1.0 if talking(t) > 0.05 and t < T_HAVING else 0.0, "Me": 1.0 if singing(t) > 0 else 0.0}
    # layout: gallery, then Ted in the spotlight; at the bridge she becomes the speaker
    S.speaker_k = sstep(T_SIT + 0.3, T_SIT + 1.0, t)
    S.speaker = "Me" if T_TED - 0.1 < t < T_FINAL + 0.2 else "Ted"
    if S.present["Ted"] < 0.5 and t > T_HAVING: S.speaker = "Me"
    S.spk_from, S.spk_mix = None, 0.0
    for a, f_, to in ((T_TED - 0.1, "Ted", "Me"), (T_FINAL + 0.2, "Me", "Ted")):
        if a <= t < a + 0.55: S.spk_from, S.speaker, S.spk_mix = f_, to, ease_io((t - a) / 0.55)
    # people's video state
    S.st = {"Ted": ted_state(t), "Me": me_state(t)}
    for p in ("Dana", "Priya", "Marcus", "Sam", "Lee", "Jo"): S.st[p] = other_state(p, t)
    S.bg = {"Ted": "stage" if stage_bg(t) else "Ted"}
    S.hands = {"Me": sstep(T_ASK + 0.15, T_ASK + 0.35, t) * (1 - sstep(T_DIM, T_DIM + 0.3, t)) + sstep(T_NOQA - 0.2, T_NOQA, t) * (1 - sstep(T_ANYWAY, T_ANYWAY + 0.3, t))}
    S.my_hand = S.hands["Me"]
    S.name_suffix = {}
    # Ted shares his screen: blank slides, then photos
    S.share = 0.0; S.share_kind = None; S.share_sub = 0
    for i in (0, 1):
        a = T_18[i] + 0.25; b = T_PAUSE[i] - 0.25
        if a - 0.2 < t < b + 0.3:
            S.share = sstep(a - 0.2, a + 0.1, t) * (1 - sstep(b, b + 0.3, t))
            if t < T_FATHER[i] - 0.15: S.share_kind = "slides"; S.share_sub = 0 + (t > T_SLIDES[i] - 0.1) + (t > T_POINT[i] - 0.1)
            else: S.share_kind = "dad" if i == 0 else "dad2"
        a = T_RAFTER[i] + 0.3; b = T_BELIEVE_E[i] - (0.25 if i == 0 else 0.6)
        if a - 0.2 < t < b + 0.3:
            S.share = sstep(a - 0.2, a + 0.1, t) * (1 - sstep(b, b + 0.3, t)); S.share_kind = "young" if i == 0 else "violin"
    # circling back: a loading circle over his video
    S.spinner = max(win(t, T_CIRCLE[0] + 0.1, T_CIRCLE_E[0] - 0.4, 0.25, 0.3), win(t, T_CIRCLE[1] + 0.1, T_CIRCLE_E[1] - 0.4, 0.25, 0.3))
    S.spinner_text = "Circling back…"
    # live captions under his video
    S.captions = sstep(T_SO - 0.4, T_SO - 0.2, t) * (1 - sstep(T_TED - 0.3, T_TED, t)) + sstep(T_FINAL + 0.5, T_FINAL + 0.8, t) * (1 - sstep(T_HAVING, T_HAVING + 0.3, t))
    S.caption_text = caption(t)
    if vert: S.captions = 0.0          # 9:16: the lyrics sit where his captions would be
    # reactions floating up
    S.reactions = []; S.react_from = "Me"
    for a, kind, px in ((T_PAUSE[0] + 0.6, "cricket", 0.5), (T_PAUSE[0] + 1.1, "cricket", 0.7), (T_PAUSE[1] + 0.6, "cricket", 0.5),
                        (T_PAUSE[1] + 1.0, "sleepy", 0.3), (T_PAUSE[1] + 1.5, "sleepy", 0.75), (T_18[1] + 0.6, "eyes", 0.4)):
        k_ = (t - a) / 2.2
        if 0 < k_ < 1: S.reactions.append((kind, k_, px))
    # the side panel
    S.panel = "chat"
    if T_FIFTEEN - 0.3 < t < T_FINAL + 0.2: S.panel = "people"
    if T_NOQA - 0.35 < t < T_NEVERQ + 3.6: S.panel = "qa"
    S.panel_w = PANEL_W * ease_io((t - 6.25) / 0.45)
    S.qa_label = "Q&A" if t < T_NOA + 0.35 else ("Q&" if t < T_NEVERQ_Q + 0.1 else "&")
    S.messages = messages(t)
    S.typing = ""
    for (a, b), s in zip(TYPE_WINDOWS[:2], ("is the file ready?", "the file?")):
        if a < t < b + 0.15: S.typing = C.typed(s, t, a, b)
    S.placeholder = "Message everyone"
    S.hover = None
    # people panel: the talk time, Dana's hard stop
    S.n_listed = 8
    S.list_k = {p: 1.0 for p in AP.PEOPLE_ORDER}
    S.gone = {"Dana": sstep(T_HARD + 0.1, T_HARD + 0.5, t)}
    S.sub = {"Ted": "Host · presenting"}
    S.sub_red = {}
    if t > T_HARD + 0.1: S.sub["Dana"] = "Left · hard stop"
    if t > T_HAS + 0.2: S.sub["Dana"] = "Hard stop · 2 years ago"; S.sub_red["Dana"] = True
    if t > T_GHOST + 0.3: S.sub["Dana"] = "Ghost"
    S.talk = {p: (6 if p == "Ted" else 0) for p in AP.PEOPLE_ORDER}
    S.talk_k = sstep(T_SIX - 0.2, T_SIX + 0.6, t) * (1 - sstep(T_HARD - 0.3, T_HARD + 0.1, t))
    # Q&A
    S.qa_counts = [("Questions", "0"), ("Answers", "0")]
    S.qa_row_k = [sstep(T_NOQA, T_NOQA + 0.3, t), sstep(T_NOA, T_NOA + 0.3, t)]
    S.qa_typing = C.typed("is the file ready?", t, T_NEVERQ - 0.1, T_NEVERQ + 1.0) if T_NEVERQ - 0.1 < t < T_NEVERQ + 1.3 else ""
    S.qa_note = "The host has turned off Q&A for this meeting." if t > T_NEVERQ + 1.3 else ""
    S.qa_note_k = sstep(T_NEVERQ + 1.3, T_NEVERQ + 1.6, t)
    # notes: the tally and buzzword bingo
    S.notes_op = ease_out((t - (T_V2 + 0.6)) / 0.4) * (1 - sstep(T_CH2 - 0.2, T_CH2 + 0.3, t))
    S.notes_r = NOTES_R
    n_so = sum(1 for a in so_times() if t > a); n_right = sum(1 for a in right_times() if t > a)
    S.tally = [("so", n_so), ("right?", n_right)]
    S.bingo_k = sstep(T_REALQ + 1.0, T_REALQ + 1.5, t)
    S.marks = {"JOURNEY": sstep(T_JOURNEY, T_JOURNEY + 0.25, t), "UNLOCK": sstep(T_UNLOCK, T_UNLOCK + 0.25, t), "STORY": sstep(T_STORYw, T_STORYw + 0.25, t),
               "SYNERGY": sstep(T_REALQ + 2.0, T_REALQ + 2.2, t), "PIVOT": sstep(T_ABOUTQ + 1.4, T_ABOUTQ + 1.6, t), "DEEP DIVE": sstep(T_ABOUTQ + 2.6, T_ABOUTQ + 2.8, t),
               "MOONSHOT": sstep(T_STORY + 0.8, T_STORY + 1.0, t), "LEVERAGE": sstep(T_STORY + 1.8, T_STORY + 2.0, t)}
    S.bingo_stamp = clamp((t - (T_STORYw + 0.35)) / 1.0)
    # calendar: opens at "and I watched my calendar", crashes at "give up"; reopens for "Nobody scheduled it"
    S.cal_r = CAL_R
    S.cal_op = ease_out((t - (T_CAL - 0.35)) / 0.35) * (1 - sstep(T_GIVEUP + 0.15, T_GIVEUP + 0.4, t)) + \
               ease_out((t - (T_NOSCHED - 0.3)) / 0.35) * (1 - sstep(T_NOQA - 0.5, T_NOQA - 0.2, t)) + \
               ease_out((t - (TT[6] - 0.2)) / 0.35) * (1 - sstep(T_ANYWAY + 0.4, T_ANYWAY + 0.8, t))
    S.cal_head = "Tuesday, October 21"
    S.cal_now = 9.25 + meet_min(t) / 60.0
    if t < T_NOSCHED - 0.5: S.cal_events = cal_events(t)
    elif t < TT[6] - 0.3:      # nobody scheduled it: nothing on the calendar now
        S.cal_events = [dict(s=9.25, e=9.5, t="Daily Standup", c=AP.ACCENT, op=0.55), dict(s=12.0, e=12.75, t="Lunch", c=AP.H("6b7280"))]
    else:                      # it's always a Ted talk: it repeats forever
        S.cal_head = "Every day, forever"
        k = clamp((t - TT[6]) / 1.2)
        S.cal_events = [dict(s=9.0 + i * 0.5, e=9.0 + i * 0.5 + 0.48, t="Ted's Talk", sub="repeats daily · no end date", c=AP.RED,
                             op=clamp(k * 8 - i)) for i in range(8)]
    # notifications, dialogs, menus
    S.notes_list = notifs(t)
    S.dialogs = []
    S.dialogs.append(dict(k=ease_out((t - T_GIVEUP) / 0.3) * (1 - sstep(T_GIVEUP + 2.6, T_GIVEUP + 2.9, t)) if t > T_GIVEUP else 0.0,
                          cx=CAL_R[0] + CAL_R[2] / 2, cy=CAL_R[1] + CAL_R[3] / 2, w=320, h=196, icon="cal", g="21",
                          title="Calendar quit unexpectedly.", body="Calendar couldn't keep up with today's schedule.",
                          buttons=[("Ignore", False, False), ("Reopen", True, False)]))
    S.dialogs.append(dict(k=ease_out((t - (T_HAVING + 0.9)) / 0.3) * (1 - sstep(T_PLACE - 0.6, T_PLACE - 0.3, t)) if t > T_HAVING + 0.9 else 0.0,
                          cx=HUD[0] + HUD[2] / 2, cy=HUD[1] + HUD[3] / 2, w=330, h=150, title="The host has ended this meeting",
                          body="Ted took it offline.", buttons=[("OK", True, False)]))
    S.menus = []
    km = sstep(T_NOEND - 0.2, T_NOEND + 0.1, t) * (1 - sstep(T_NOQA - 0.5, T_NOQA - 0.25, t))
    S.menus.append(dict(k=km, x=B_LEAVE[0] - 210, y=B_LEAVE[1] - 22, w=250,
                        rows=[("End meeting for all", "Only the host can end this meeting", True, kf(t, [(T_NOEND, 0), (T_NOEND + 0.4, 1)]) > 0.5 and t < T_NOEND + 1.4),
                              ("Leave meeting", "You can't leave while Ted is presenting", True, t > T_NOEND + 1.4)]))
    # DM to Ted at the end
    S.dm_op = ease_out((t - (T_PLACE - 0.2)) / 0.4)
    S.dm_r = DM_R
    S.ted_offline = sstep(T_HAVING + 0.6, T_HAVING + 1.0, t)
    S.ted_status = "Offline · notifications paused" if t < T_REACH else "Offline · unreachable"
    dm = SimpleNamespace(t=t, dark=S.dark, placeholder="Message Ted", typing="")
    a, b = TYPE_WINDOWS[3]
    if a < t < b + 0.15: dm.typing = C.typed("is the file ready?", t, a, b)
    dm.messages = []
    if t > b + 0.2:
        dm.messages.append(dict(who="Me", text="is the file ready?", time="10:19", k=ease_out((t - b - 0.2) / 0.25),
                                status="Sending…" if t < T_REACH else "Not delivered"))
    S.dm = dm
    # the pointer
    S.cursor, S.click = cursor_at(t)
    S.lid = sstep(T_REACH + 1.9, T_REACH + 3.4, t)
    return S

def so_times():
    a = T_V2 + 1.2
    return [a + i * 0.62 for i in range(5)] + [T_SOw - 0.05] + [T_SOw + 0.5 + i * 0.7 for i in range(3)]
def right_times():
    return [T_RIGHT - 1.6 + i * 0.5 for i in range(3)] + [T_RIGHT - 0.05] + [T_RIGHT + 0.45, T_RIGHT + 0.9]

def caption(t):
    """what Ted is saying, as live captions"""
    cues = [(T_SO - 0.4, "So —"), (T_STEP - 0.05, "So — stepping back…"), (T_DIM, "Can somebody dim the lights?"),
            (T_SIT, "Everybody, take a seat."), (TT[0] - 0.2, "Thank you. Thank you so much."), (T_18[0] + 0.2, "I don't use slides."),
            (T_FATHER[0], "My father used to say…"), (T_PAUSE[0] + 0.1, "…"), (TT[1], "So."), (T_CIRCLE[0], "I want to circle back to that."),
            (T_RAFTER[0], "When I was young…"), (T_NOBODY[0], "…nobody believed in me."),
            (T_V2, "So, right?"), (so_times()[3], "So."), (T_SOw + 0.3, "So, so, so."), (T_RIGHT - 0.05, "Right?"), (T_REALQ, "The real question is…"),
            (T_ABOUTQ + 0.2, "…what is a file, really?"), (T_JOURNEY - 0.1, "It's a journey."), (T_UNLOCK - 0.1, "Let's unlock that."),
            (T_STORY, "Let me tell you a story."), (T_CAL - 0.2, "Once upon a time…"), (TT[2] - 0.2, "So."), (T_18[1] + 0.2, "Still no slides."),
            (T_FATHER[1], "My father's father used to say…"), (T_PAUSE[1] + 0.1, "…"), (TT[3], "Right?"), (T_CIRCLE[1], "Circling back…"),
            (T_RAFTER[1], "When I was young…"), (T_NOBODY[1], "…nobody believed in me."),
            (T_FINAL + 0.5, "Where was I?"), (T_NOEND, "Let's keep going."), (T_NOQA, "No questions? Great."), (TT[5] - 0.2, "So."),
            (TT[6], "Right?"), (T_ANYWAY, "Anyway, happy to take this offline.")]
    cur = ""
    for a, s in cues:
        if t >= a: cur = s
    return cur

# ---------------------------------------------------------------- the pointer
def cursor_at(t):
    K = [(0.0, (720.0, 430.0)), (0.9, (720.0, 430.0)), (T_OPEN - 0.05, (1218.0, 75.0)), (T_OPEN + 0.5, (1180.0, 110.0)), (5.6, (700.0, 450.0)),
         (6.2, B_CHAT), (6.7, B_CHAT), (7.15, CHAT_IN), (8.7, CHAT_IN), (8.85, CHAT_SEND), (9.6, (800.0, 470.0)),
         (T_ASK - 0.2, (560.0, 560.0)), (T_ASK + 0.15, B_HAND), (T_ASK + 0.45, B_HAND), (20.45, CHAT_IN), (21.2, CHAT_IN), (21.3, CHAT_SEND),
         (22.5, (760.0, 500.0)), (T_V2 + 0.3, (760.0, 500.0)), (T_V2 + 0.8, (1100.0, 120.0)), (T_JOURNEY - 0.3, (1083.0, 180.0)),
         (T_CAL - 0.6, (1050.0, 300.0)), (T_CAL + 0.2, (1083.0, 420.0)), (T_GIVEUP + 0.9, (1180.0, 610.0)), (T_GIVEUP + 1.8, (1040.0, 550.0)),
         (T_TED - 0.6, (300.0, 560.0)), (T_TED - 0.25, B_MIC), (T_TED + 0.2, B_MIC), (T_FIFTEEN - 0.8, (380.0, 600.0)), (T_FIFTEEN - 0.4, B_PEOPLE),
         (T_FIFTEEN - 0.1, B_PEOPLE), (T_EIGHT + 0.5, (700.0, 300.0)), (T_SIX - 0.3, (790.0, 150.0)), (T_HARD + 0.5, (760.0, 190.0)),
         (T_DIDTHAT - 0.4, (300.0, 140.0)), (T_DIDTHAT + 0.2, (180.0, 120.0)), (T_FINAL + 0.6, (420.0, 520.0)), (T_NOSCHED - 0.4, (1000.0, 420.0)),
         (T_NOEND - 0.5, (760.0, 600.0)), (T_NOEND - 0.15, B_LEAVE), (T_NOEND + 0.4, (700.0, 556.0)), (T_NOEND + 1.4, (700.0, 556.0)),
         (T_NOEND + 1.8, (700.0, 594.0)), (T_NOQA - 0.6, (700.0, 594.0)), (T_NOQA - 0.4, (735.0, 116.0)), (T_NOQA - 0.15, (735.0, 116.0)),
         (T_NEVERQ - 0.3, (740.0, 565.0)), (T_NEVERQ + 1.3, (740.0, 565.0)), (T_NEVERQ + 1.5, (846.0, 565.0)), (T_ANYWAY - 0.5, (700.0, 500.0)),
         (T_PLACE - 0.4, (980.0, 480.0)), (T_PLACE + 0.6, (1050.0, 520.0)), (T_PLACE + 2.6, (1050.0, 520.0)), (T_PLACE + 2.8, (1236.0, 528.0)),
         (T_REACH + 0.6, (1150.0, 470.0)), (DUR, (1150.0, 470.0))]
    p = kf(t, K)
    clicks = [T_OPEN, 6.45, 8.85, T_ASK + 0.3, 21.3, T_TED - 0.1, T_FIFTEEN - 0.2, T_NOEND - 0.05, T_NOQA - 0.25, T_NEVERQ + 1.5, T_PLACE + 2.8]
    ck = 0.0
    for c in clicks:
        if 0 <= t - c < 0.4: ck = (t - c) / 0.4
    return p, ck

# ---------------------------------------------------------------- the camera over the screen
def cam16(t):
    """(cx, cy, zoom) in desktop units; zoom 1 = the whole screen"""
    TEDT = (126.0, 232.0)                        # Ted's tile in the gallery (with the chat open)
    SPK = (320.0, 368.0)                         # the speaker tile
    K = [(0.0, (940.0, 232.0, 1.6)), (0.75, (950.0, 225.0, 1.62)), (1.5, (1060.0, 150.0, 1.85)), (T_OPEN + 0.25, (1040.0, 160.0, 1.8)),
         (T_OPEN + 1.0, (450.0, 340.0, 1.15)), (5.7, (450.0, 340.0, 1.15)), (6.6, (560.0, 340.0, 1.35)), (7.1, (740.0, 470.0, 2.25)),
         (9.4, (740.0, 455.0, 2.15)), (10.6, (700.0, 430.0, 1.85)), (13.4, (700.0, 430.0, 1.85)), (T_DIFF + 0.6, (1090.0, 118.0, 2.35)),
         (T_FOUR - 0.6, (1090.0, 125.0, 2.3)), (T_FOUR - 0.1, (150.0, 92.0, 3.1)), (T_ASK - 0.7, (150.0, 92.0, 3.1)), (T_ASK - 0.1, (520.0, 360.0, 1.3)),
         (T_SO - 0.6, (520.0, 360.0, 1.3)), (T_SO - 0.05, (TEDT[0], TEDT[1], 4.3)), (T_DIM + 0.1, (TEDT[0], TEDT[1] - 4, 4.0)),
         (T_DIM + 0.75, (640.0, 360.0, 1.0)), (T_SIT - 0.1, (640.0, 360.0, 1.0)), (T_SIT + 1.0, (450.0, 340.0, 1.15)),
         (TT[0] - 0.3, (SPK[0], SPK[1], 2.05)), (T_18[0] - 0.2, (SPK[0], SPK[1], 2.05)), (T_18[0] + 0.15, (150.0, 92.0, 2.9)),
         (T_18[0] + 0.9, (150.0, 92.0, 2.9)), (T_18[0] + 1.35, (SPK[0], SPK[1], 2.05)), (T_PAUSE[0] + 0.5, (SPK[0], SPK[1], 2.05)), (T_PAUSE[0] + 1.0, (500.0, 400.0, 1.45)),
         (TT[1] - 0.3, (500.0, 400.0, 1.45)), (TT[1] + 0.2, (SPK[0], SPK[1], 2.05)), (T_CIRCLE[0] + 1.2, (SPK[0], SPK[1], 2.05)),
         (T_CIRCLE[0] + 1.8, (560.0, 330.0, 1.4)), (T_RAFTER[0], (560.0, 330.0, 1.4)), (T_RAFTER[0] + 0.5, (SPK[0], SPK[1], 2.05)),
         (T_V2 - 0.2, (SPK[0], SPK[1], 2.05)), (T_V2 + 0.6, (900.0, 280.0, 1.35)), (T_V2 + 1.4, (1083.0, 190.0, 2.35)),
         (T_REALQ - 0.4, (1083.0, 190.0, 2.35)), (T_REALQ + 0.3, (760.0, 420.0, 1.75)), (T_ABOUTQ + 1.4, (760.0, 420.0, 1.75)),
         (T_ABOUTQ + 2.0, (1083.0, 230.0, 2.1)), (T_CAL - 0.4, (1083.0, 230.0, 2.1)), (T_CAL + 0.2, (1083.0, 495.0, 2.2)),
         (T_GIVEUP + 0.95, (1083.0, 495.0, 2.2)), (TT[2] + 0.75, (SPK[0], SPK[1], 2.05)), (T_18[1] + 0.6, (SPK[0], SPK[1], 2.05)),
         (T_18[1] + 1.0, (900.0, 200.0, 1.5)), (T_FATHER[1] - 0.6, (900.0, 200.0, 1.5)), (T_FATHER[1] - 0.1, (SPK[0], SPK[1], 2.05)),
         (T_PAUSE[1] + 0.5, (SPK[0], SPK[1], 2.05)), (T_PAUSE[1] + 1.0, (500.0, 400.0, 1.45)), (TT[3] + 0.2, (SPK[0], SPK[1], 2.05)),
         (T_BELIEVE_E[1] - 0.4, (SPK[0], SPK[1], 2.05)), (T_TED - 0.15, (450.0, 340.0, 1.15)), (T_STANDUP + 0.6, (330.0, 360.0, 1.9)),
         (T_FIFTEEN - 0.6, (330.0, 360.0, 1.9)), (T_FIFTEEN + 0.1, (100.0, 90.0, 2.6)), (T_EIGHT - 0.3, (100.0, 90.0, 2.6)),
         (T_EIGHT + 0.3, (750.0, 330.0, 1.85)), (T_GHOST - 0.4, (750.0, 330.0, 1.85)), (T_GHOST + 0.35, (175.0, 140.0, 3.8)), (T_GHOST + 2.6, (170.0, 138.0, 4.0)), (T_GHOST + 3.3, (450.0, 255.0, 1.4)), (T_DIDTHAT - 0.5, (450.0, 255.0, 1.4)), (T_DIDTHAT + 0.2, (300.0, 300.0, 1.5)),
         (T_FINAL - 0.1, (300.0, 300.0, 1.5)), (TT[4] + 0.3, (SPK[0], SPK[1], 2.05)), (T_NOSCHED - 0.4, (SPK[0], SPK[1], 2.05)),
         (T_NOSCHED + 0.1, (1083.0, 495.0, 2.2)), (T_NOEND - 0.4, (1083.0, 495.0, 2.2)), (T_NOEND + 0.1, (720.0, 520.0, 2.3)),
         (T_NOQA - 0.5, (720.0, 520.0, 2.3)), (T_NOQA + 0.1, (750.0, 300.0, 1.85)), (T_NEVERQ + 3.2, (750.0, 300.0, 1.85)),
         (TT[5] + 0.3, (SPK[0], SPK[1], 2.05)), (TT[6] - 0.2, (SPK[0], SPK[1], 2.05)), (TT[6] + 0.3, (1083.0, 495.0, 2.2)),
         (T_ANYWAY - 0.2, (1083.0, 495.0, 2.2)), (T_ANYWAY + 0.3, (720.0, 420.0, 1.75)), (T_HAVING + 0.7, (720.0, 420.0, 1.75)),
         (T_HAVING + 1.2, (450.0, 340.0, 1.6)), (T_PLACE - 0.3, (640.0, 360.0, 1.0)), (T_PLACE + 0.6, (1083.0, 380.0, 2.0)),
         (T_REACH + 1.2, (1083.0, 400.0, 2.15)), (T_REACH + 2.0, (640.0, 360.0, 1.0)), (DUR, (640.0, 360.0, 1.0))]
    return kf(t, K)

def cam9(t):
    """9:16: a vertical strip of the screen, following the action (cx, cy, zoom over the full-height strip)"""
    TEDT = (126.0, 232.0); SPK = (320.0, 368.0); CHAT = (749.0, 360.0); NOTES = (1083.0, 190.0); CAL = (1083.0, 495.0)
    K = [(0.0, (1083.0, 300.0, 1.0)), (T_OPEN + 0.2, (1083.0, 300.0, 1.0)), (T_OPEN + 1.0, (330.0, 340.0, 1.0)), (6.0, (330.0, 340.0, 1.0)),
         (6.8, (CHAT[0], CHAT[1], 1.0)), (9.6, (CHAT[0], 420.0, 1.25)), (T_DIFF + 0.2, (CHAT[0], 360.0, 1.0)), (T_DIFF + 0.7, (1083.0, 260.0, 1.0)),
         (T_FOUR - 0.4, (1083.0, 260.0, 1.0)), (T_FOUR, (150.0, 200.0, 1.6)), (T_ASK - 0.6, (150.0, 200.0, 1.6)), (T_ASK, (CHAT[0], 380.0, 1.0)),
         (T_SO - 0.5, (CHAT[0], 380.0, 1.0)), (T_SO, (TEDT[0], TEDT[1], 2.2)), (T_DIM - 0.1, (TEDT[0], TEDT[1], 2.2)),
         (T_DIM + 0.5, (300.0, 360.0, 1.0)), (TT[0] - 0.3, (SPK[0], SPK[1], 1.0)), (T_18[0] - 0.1, (SPK[0], SPK[1], 1.0)),
         (T_18[0] + 0.3, (150.0, 200.0, 1.6)), (T_18[0] + 0.9, (150.0, 200.0, 1.6)), (T_18[0] + 1.35, (SPK[0], SPK[1], 1.0)), (T_PAUSE[0] + 0.5, (SPK[0], SPK[1], 1.0)),
         (T_PAUSE[0] + 1.0, (CHAT[0], 380.0, 1.0)), (TT[1] - 0.3, (CHAT[0], 380.0, 1.0)), (TT[1] + 0.2, (SPK[0], SPK[1], 1.0)),
         (T_V2 - 0.2, (SPK[0], SPK[1], 1.0)), (T_V2 + 1.2, (NOTES[0], NOTES[1] + 60, 1.0)), (T_REALQ - 0.3, (NOTES[0], NOTES[1] + 60, 1.0)),
         (T_REALQ + 0.3, (CHAT[0], 380.0, 1.0)), (T_ABOUTQ + 1.4, (CHAT[0], 380.0, 1.0)), (T_ABOUTQ + 2.0, (NOTES[0], 260.0, 1.0)),
         (T_CAL - 0.3, (NOTES[0], 260.0, 1.0)), (T_CAL + 0.2, (CAL[0], 420.0, 1.0)), (T_GIVEUP + 0.95, (CAL[0], 420.0, 1.0)),
         (TT[2] + 0.75, (SPK[0], SPK[1], 1.0)), (T_PAUSE[1] + 0.5, (SPK[0], SPK[1], 1.0)), (T_PAUSE[1] + 1.0, (CHAT[0], 380.0, 1.0)),
         (TT[3] + 0.2, (SPK[0], SPK[1], 1.0)), (T_BELIEVE_E[1] - 0.4, (SPK[0], SPK[1], 1.0)), (T_TED, (SPK[0], SPK[1], 1.0)),
         (T_FIFTEEN - 0.4, (SPK[0], SPK[1], 1.0)), (T_FIFTEEN + 0.1, (150.0, 200.0, 1.6)), (T_EIGHT - 0.3, (150.0, 200.0, 1.6)),
         (T_EIGHT + 0.3, (CHAT[0], 360.0, 1.0)), (T_DIDTHAT - 0.5, (CHAT[0], 360.0, 1.0)), (T_DIDTHAT + 0.2, (230.0, 330.0, 1.0)),
         (T_FINAL - 0.1, (230.0, 330.0, 1.0)), (TT[4] + 0.3, (SPK[0], SPK[1], 1.0)), (T_NOSCHED - 0.4, (SPK[0], SPK[1], 1.0)),
         (T_NOSCHED + 0.1, (CAL[0], 420.0, 1.0)), (T_NOEND - 0.4, (CAL[0], 420.0, 1.0)), (T_NOEND + 0.1, (740.0, 470.0, 1.25)),
         (T_NOQA - 0.5, (740.0, 470.0, 1.25)), (T_NOQA + 0.1, (CHAT[0], 360.0, 1.0)), (T_NEVERQ + 3.2, (CHAT[0], 360.0, 1.0)),
         (TT[5] + 0.3, (SPK[0], SPK[1], 1.0)), (TT[6] - 0.2, (SPK[0], SPK[1], 1.0)), (TT[6] + 0.3, (CAL[0], 420.0, 1.0)),
         (T_ANYWAY - 0.2, (CAL[0], 420.0, 1.0)), (T_ANYWAY + 0.3, (CHAT[0], 380.0, 1.0)), (T_HAVING + 1.2, (450.0, 340.0, 1.0)),
         (T_PLACE - 0.3, (450.0, 340.0, 1.0)), (T_PLACE + 0.6, (1083.0, 360.0, 1.0)), (DUR, (1083.0, 360.0, 1.0))]
    return kf(t, K)

def make_cam(t, W, H):
    if W > H:
        cx, cy, z = cam16(t); s = W / U.DW * z
        half_w, half_h = W / 2 / s, H / 2 / s
        cx = clamp(cx, half_w - 60, U.DW - half_w + 60) if z > 1.001 else cx
        cy = clamp(cy, half_h - 40, U.DH - half_h + 40) if z > 1.001 else cy
        return U.Cam(W, H, cx, cy, s)
    cx, cy, z = cam9(t); s = H / U.DH * z
    half_w, half_h = W / 2 / s, H / 2 / s
    cx = clamp(cx, half_w - 20, U.DW - half_w + 20); cy = clamp(cy, half_h - 30, U.DH - half_h + 30)
    return U.Cam(W, H, cx, cy, s)

# ---------------------------------------------------------------- rendering
def render_frame(t, W=1920, H=1080, fi=0):
    vert = H > W
    S = state(t, vert)
    cam = make_cam(t, W, H)
    img = np.zeros((H, W, 3), F32)
    AP.desktop(img, cam, S)
    AP.desktop_items(img, cam, S)
    AP.huddle(img, cam, S)
    AP.notes(img, cam, S)
    AP.calendar(img, cam, S)
    for d in S.dialogs: AP.dialog(img, cam, S, d)
    for m in S.menus: AP.menu(img, cam, S, m)
    if S.menus and S.menus[0]["k"] > 0.5 and t > T_NOEND + 0.2:
        AP.tooltip(img, cam, S, B_LEAVE[0], B_LEAVE[1] - 22 - 16 - 2 * 40 - 4, "Only Ted can end it", 0)
    AP.dm_window(img, cam, S)
    AP.menubar(img, cam, S)
    AP.dock(img, cam, S)
    AP.notifications(img, cam, S)
    U.cursor(img, cam, S.cursor[0], S.cursor[1], 1.0, 1.0 - S.lid, S.click)
    # the lid closes: the screen goes dark
    if S.lid > 0:
        img *= 1 - S.lid
        yy = np.linspace(0, 1, H, dtype=F32)[:, None, None]
        img += (0.06 * S.lid * (1 - S.lid) * 4) * (1 - yy) * np.array([0.6, 0.7, 1.0], F32)
    lyrics(img, t, W, H)
    if not C.STATE["clean"]:
        C.subscribe_pill(img, t, W, H, T_PILL, 5.0)
        C.end_screen(img, t, W, H, T_END, DUR - T_END, "It's always a Ted talk.", sub_line="Subscribe for a new song every week",
                     title="TED Talk, screenlife", accent=U.hexc("e0352b"))
    return finish(img, t, fi)

# ---------------------------------------------------------------- lyrics: a live-captions bar at the bottom of the frame
F_LYR = U.FONT["s"]
def lyrics(img, t, W, H):
    if C.STATE["clean"]: return
    vert = H > W; k = W / (1080 if vert else 1920)
    fs = int((64 if not vert else 58) * k); maxw = W * (0.80 if not vert else 0.80)
    ybase = H * (0.875 if not vert else 0.765)
    flt = C.STATE["lyric_filter"]
    vis = [L for L in TM.lines if (flt is None or flt(L))]
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
        lh = fs * 1.25
        y0 = ybase - (len(rows) - 1) * lh / 2 - fs * 0.62 - lh * 0.15 * (1 - opl)
        bw = max(sum(r[2] for r in row) + sp * (len(row) - 1) for row in rows) + fs * 1.1
        bh = len(rows) * lh + fs * 0.55
        bx, by = (W - bw) / 2, y0 - fs * 0.22
        cam = U.Cam(W, H, W / 2, H / 2, 1.0)
        U.rrect(img, cam, bx, by, bw, bh, fs * 0.32, (0.06, 0.06, 0.08), 0.72 * opl)
        for ri, row in enumerate(rows):
            x = (W - (sum(r[2] for r in row) + sp * (len(row) - 1))) / 2
            for w_, tt, ww, nt in row:
                kw = sstep(tt - 0.12, tt + 0.05, t)
                act = sstep(tt - 0.06, tt + 0.02, t) * (1 - sstep(nt - 0.06, nt + 0.04, t))
                yy = y0 + ri * lh
                C.blit(img, C.sprite(w_, F_LYR, fs, 0), x, yy, np.array([1, 1, 1], F32), opl * (0.42 + 0.58 * kw))
                if act > 0.02:
                    sw = clamp((t - tt + 0.04) / 0.14)
                    x0_, x1_ = int(x), int(x + ww * sw); y_ = int(yy + fs * 1.12)
                    if x1_ > x0_: img[y_:y_ + max(3, int(5 * k)), x0_:x1_] = img[y_:y_ + max(3, int(5 * k)), x0_:x1_] * (1 - act * opl) + U.hexc("e0352b") * act * opl
                x += ww + sp

def finish(img, t, fi):
    img *= (1 - sstep(DUR - 1.0, DUR - 0.05, t))
    return (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)
