"""Look What I Can Do — "One Session": the whole song is one Claude Code session, and her videos are what it renders.

Her lines are typed as prompts in sync with the vocal; Claude's lines come back in amber. Every "I made a ..." opens a
pane playing one of her real music videos (clips cut from the finished files in Original Music). The chorus splits the
panes in two on the beat (1 -> 2 -> 4 -> 8 -> 16), like subagents spawning subagents. Verse 2 and 3 pull her real X posts (cut from
her own screen recording) as receipts. "Now I'm in it too" renders this video inside itself and dives in. Esc interrupts the compliment. The outro
closes every pane, shows her real usage-limit screenshot, and her phone lights up for "Hey ChatGPT?".

Everything that is read on screen is at least 34 px at 1080p; no subtitle line (the typed dialogue is the picture).
"""
import os, math, json
import numpy as np, cv2
from studio import core as C
from studio import footage as FT
from studio.config import MUSIC_DIR, load_song

HERE = os.path.dirname(os.path.abspath(__file__))
T = C.Timing(HERE)
DUR = T.duration + float(load_song(os.path.dirname(os.path.abspath(__file__))).get("tail", 0))
FILM = os.path.join(MUSIC_DIR, "Look What I Can Do")
FT.CLIP_DIRS[:0] = [os.path.join(FILM, "clips"), os.path.join(FILM, "assets"), os.path.join(FILM, "stills")]

F_ANTON = os.path.join(C.FONTS, "Anton-Regular.ttf")
F_MONO, F_MONOB, F_INTER, F_DISP, F_DISPB = C.F_MONO, C.F_MONOB, C.F_INTER, C.F_DISP, C.F_DISPB
F_SERIF_I = os.path.join(C.FONTS, "InstrumentSerif-Italic.ttf")
C.THEME.update(disp=F_ANTON, dispb=F_DISPB, body=F_INTER, mono=F_MONOB)

hx = C.hexc
BG = hx("0c0c0b"); INK = hx("ece6d8"); MUTE = hx("8d887d"); FAINT = hx("4a4741"); LINE = hx("2e2d33")
GREEN = hx("74e36a"); AMBER = hx("ffa840"); RED = hx("ff4248"); HDR = hx("141416"); GOLD = hx("ffd36b")
WHITE = np.array([1, 1, 1], np.float32)

clamp, sstep, ease_out, ease_io, lerp = C.clamp, C.sstep, C.ease_out, C.ease_io, C.lerp


# ------------------------------------------------------------------ timing helpers
def line(sub, nth=0):
    hits = [L for L in T.lines if sub.lower() in L["text"].lower()]
    return hits[nth]

def ls(sub, nth=0): return line(sub, nth)["s"]

def wt(sub, word, nth_line=0, nth_word=0):
    L = line(sub, nth_line); k = 0
    for w, t in zip(L["words"], L["wt"]):
        if C.norm(w) == C.norm(word):
            if k == nth_word: return t
            k += 1
    raise KeyError((sub, word))

SEC = {s["name"]: (s["s"], s["e"]) for s in T.sections}
BEATS = T.beats
def beat_after(t): i = np.searchsorted(BEATS, t); return float(BEATS[min(i, len(BEATS) - 1)])
def pulse(t, k=8.0): return T.beat_pulse(t, k)
def hit(t, t0, a=0.0, d=0.35): return sstep(t0 - a, t0, t) if a > 0 else (1.0 if t >= t0 else 0.0)
def env(t, t0, rise=0.08, fall=0.5):
    if t < t0: return 0.0
    x = t - t0
    return min(1.0, x / rise) * math.exp(-max(0.0, x - rise) / fall)

# key moments (seconds), from build/timed.json
K = dict(
    drop=13.58,
    v1=ls("I made a song, I made a beat"),
    song=wt("I made a song, I made a beat", "song"), beat=wt("I made a song, I made a beat", "beat"),
    movie=wt("I made a movie", "movie"), ghost=wt("I made a ghost", "ghost"), witch=wt("I made a ghost", "witch"),
    viking=wt("A Viking shooting", "Viking"), mars=wt("A Viking shooting", "Mars"),
    bot=wt("I made a bot", "bot"), site=wt("I made a bot", "site"),
    eleven=wt("I made eleven", "eleven"), training=ls("I have no training"), job=ls("I learned a whole new job"),
    direct=ls("Can I direct?"), youcan1=ls("You can!"), produce=ls("Can I produce?"), youcan2=ls("You can!", 1),
    oscar=ls("Can I win an Oscar?"), ahead=ls("Let's not get ahead"), late=ls("Too late!"),
    ch1=SEC["CH1"][0], post=ls("Click! Click! Ship it!") - 0.1, v2=ls("I'm a Senior Slopcore Architect") - 0.12, brk=ls("What are your qualifications?"),
    sub=ls("I have a subscription."), towhat=ls("To what?"), every=ls("Everything."),
    ch2=SEC["CH2"][0], v3=SEC["V3"][0], bridge=ls("Ladies and gentlemen"), final=SEC["FINAL"][0],
    bd=ls("Claude?", 1), drop2=SEC["DROP"][0], outro=ls("Claude?", 2),
)
K["ch1_hook"] = ls("Look what I can do!", 0)
K["ch2_hook"] = ls("Look what I can do!", 4)
K["fin_hook"] = ls("Look what I can do!", 8)
K["myself"] = ls("I made a song about myself"); K["intoo"] = ls("And now I'm in it too!")
K["universe"] = ls("I built an entire universe"); K["review"] = ls("And left it a five-star review!")
K["talented"] = ls("Do you think I'm talented?"); K["extra"] = ls("You are extraordinarily"); K["knew"] = ls("I knew it!")
K["onemore"] = ls("Can we make one more?"); K["limit"] = ls("You've reached your usage limit."); K["gpt"] = ls("Hey ChatGPT?")
K["slam"] = 178.15                                                      # Suno's last blast after "Hey ChatGPT?" (energy map)
K["end"] = 181.6                                                        # end card; YouTube end-screen elements need the right half
DROP_HIT = 158.3                                                        # the drop lands after "I KNEW IT!" (energy map)


# ------------------------------------------------------------------ drawing helpers
def S(px, ts): return int(round(px * ts))

def text(img, s, x, y, size, color, op=1.0, path=F_MONOB, anchor="lt", glow=0, glow_op=0.0, glow_color=None, track=0):
    if op <= 0.01 or not s: return 0
    sp = C.sprite(s, path, int(size), glow, track)
    C.blit(img, sp, x, y, color, op, glow_op, glow_color=glow_color, anchor=anchor)
    return sp[0].shape[1] - 2 * sp[2]

def tw(s, size, path=F_MONOB): return C.text_w(s, path, int(size))

def fit_size(s, path, size, maxw):
    while size > 10 and tw(s, size, path) > maxw: size -= 2
    return size

def rect(img, x, y, w, h, color, op=1.0):
    x0, y0, x1, y1 = max(0, int(x)), max(0, int(y)), min(img.shape[1], int(x + w)), min(img.shape[0], int(y + h))
    if x1 <= x0 or y1 <= y0 or op <= 0: return
    reg = img[y0:y1, x0:x1]; reg *= (1 - op); reg += color * op

_RRM = {}
def rr_mask(w, h, r):
    k = (w, h, r)
    if k not in _RRM:
        m = np.zeros((h, w), np.uint8); r = max(0, min(r, w // 2, h // 2))
        if r == 0: m[:] = 255
        else:
            cv2.rectangle(m, (r, 0), (w - r - 1, h - 1), 255, -1); cv2.rectangle(m, (0, r), (w - 1, h - r - 1), 255, -1)
            for cx, cy in ((r, r), (w - r - 1, r), (r, h - r - 1), (w - r - 1, h - r - 1)): cv2.circle(m, (cx, cy), r, 255, -1, cv2.LINE_AA)
        mm = m.astype(np.float32) / 255
        edge = cv2.GaussianBlur(cv2.Canny(m, 50, 150).astype(np.float32) / 255, (0, 0), 0.7)
        _RRM[k] = (mm[..., None], np.clip(edge * 1.6, 0, 1)[..., None])
        if len(_RRM) > 900: _RRM.clear()
    return _RRM[k]

def rrect(img, x, y, w, h, r, fill=None, fill_op=1.0, border=None, border_op=1.0):
    x, y, w, h = int(round(x)), int(round(y)), int(round(w)), int(round(h))
    if w < 4 or h < 4: return
    m, e = rr_mask(w, h, int(r)); H, W = img.shape[:2]
    x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0: return
    reg = img[y0:y1, x0:x1]; mm = m[y0 - y:y1 - y, x0 - x:x1 - x]; ee = e[y0 - y:y1 - y, x0 - x:x1 - x]
    if fill is not None and fill_op > 0: reg *= (1 - mm * fill_op); reg += mm * fill * fill_op
    if border is not None and border_op > 0: reg *= (1 - ee * border_op); reg += ee * border * border_op

def darken(img, op):
    if op > 0: img *= (1 - op)

def blit_rot(img, s, cx, cy, size, color, angle, op=1.0, path=F_ANTON, scale=1.0):
    if op <= 0.01: return
    a, g, pad = C.sprite(s, path, int(size * scale), 0)
    h, w = a.shape; D = int(math.hypot(w, h)) + 4
    can = np.zeros((D, D), np.float32); ox, oy = (D - w) // 2, (D - h) // 2; can[oy:oy + h, ox:ox + w] = a
    M = cv2.getRotationMatrix2D((D / 2, D / 2), angle, 1.0); can = cv2.warpAffine(can, M, (D, D), flags=cv2.INTER_LINEAR)
    x, y = int(cx - D / 2), int(cy - D / 2); H, W = img.shape[:2]
    x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + D), min(H, y + D)
    if x1 <= x0 or y1 <= y0: return
    sa = can[y0 - y:y1 - y, x0 - x:x1 - x][..., None] * op; reg = img[y0:y1, x0:x1]
    reg *= (1 - sa); reg += sa * color

def star(img, cx, cy, r, color, op=1.0, fill=True):
    pts = []
    for k in range(10):
        ang = -math.pi / 2 + k * math.pi / 5; rr = r if k % 2 == 0 else r * 0.45
        pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    pts = np.array(pts, np.float32)
    x0, y0 = int(pts[:, 0].min()) - 2, int(pts[:, 1].min()) - 2; x1, y1 = int(pts[:, 0].max()) + 3, int(pts[:, 1].max()) + 3
    w, h = x1 - x0, y1 - y0; m = np.zeros((h, w), np.uint8)
    q = (pts - [x0, y0]).astype(np.int32)
    if fill: cv2.fillPoly(m, [q], 255, cv2.LINE_AA)
    else: cv2.polylines(m, [q], True, 255, max(2, int(r * 0.08)), cv2.LINE_AA)
    H, W = img.shape[:2]; X0, Y0, X1, Y1 = max(0, x0), max(0, y0), min(W, x1), min(H, y1)
    if X1 <= X0 or Y1 <= Y0: return
    a = m[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0].astype(np.float32)[..., None] / 255 * op
    reg = img[Y0:Y1, X0:X1]; reg *= (1 - a); reg += a * color

def spark(img, cx, cy, r, color, op=1.0):
    """Claude Code's little asterisk, drawn (the mono font has no glyph for it)."""
    if op <= 0.01: return
    m = np.zeros((int(r * 2 + 6), int(r * 2 + 6)), np.uint8); c = r + 3
    for k in range(6):
        a = k * math.pi / 3
        cv2.line(m, (int(c), int(c)), (int(c + r * math.cos(a)), int(c + r * math.sin(a))), 255, max(2, int(r * 0.32)), cv2.LINE_AA)
    x0, y0 = int(cx - c), int(cy - c); H, W = img.shape[:2]; h, w = m.shape
    X0, Y0, X1, Y1 = max(0, x0), max(0, y0), min(W, x0 + w), min(H, y0 + h)
    if X1 <= X0 or Y1 <= Y0: return
    a_ = m[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0].astype(np.float32)[..., None] / 255 * op
    reg = img[Y0:Y1, X0:X1]; reg *= (1 - a_); reg += a_ * color


def cursor(img, x, y, h, t, color=GREEN, op=1.0, blink=True):
    on = 1.0 if not blink else (1.0 if (t * 1.9) % 1.0 < 0.62 else 0.25)
    rect(img, x, y, max(3, int(h * 0.52)), h, color, op * on)


# ------------------------------------------------------------------ the terminal
SECTION_LABEL = {"INTRO": "intro", "V1": "verse 1", "PRE": "pre-chorus", "CH1": "chorus", "POST": "ship it", "V2": "verse 2",
                 "BREAK": "qualifications", "CH2": "chorus", "V3": "verse 3", "BRIDGE": "keynote", "FINAL": "final chorus",
                 "BREAKDOWN": "breakdown", "DROP": "drop", "OUTRO": "outro"}

def header(img, t, W, H, op=1.0, clock=None):
    ts = min(W, H) / 1080; y = S(30, ts); sz = S(24, ts)
    if op <= 0.01: return
    x = S(64, ts) if W > H else W * 0.11
    a = text(img, "adita@studio", x, y, sz, INK, op * 0.95, F_MONOB)
    text(img, " ~/look-what-i-can-do", x + a, y, sz, MUTE, op, F_MONO)
    if W > H:
        sec = SECTION_LABEL.get(T.section_at(t), "")
        mm = int(t // 60); ss = int(t % 60)
        right = f"claude · {sec} · {mm}:{ss:02d}" if clock is None else f"claude · {sec} · {clock}"
        text(img, right, W - S(64, ts) - tw(right, sz, F_MONO), y, sz, MUTE, op, F_MONO)

def chat_line(img, x, y, who, s, size, t, op=1.0, typing=False, maxw=None):
    """One line of the session. who: 'u' (her prompt), 'c' (Claude), 's' (system/muted), 'ok', 'err'. Returns height."""
    ts_line = size * 1.36
    if op <= 0.01: return ts_line
    if who == "u":
        a = text(img, "❯ ", x, y, size, GREEN, op, F_MONOB)
        w2 = text(img, s, x + a, y, size, INK, op, F_MONOB)
        if typing: cursor(img, x + a + w2 + size * 0.12, y + size * 0.18, int(size * 1.05), t, GREEN, op)
    elif who == "c":
        r = size * 0.2
        cv2.circle(img, (int(x + size * 0.3), int(y + size * 0.72)), max(2, int(r)), (AMBER * op + img[int(y + size * 0.72), int(x + size * 0.3)] * (1 - op)).tolist(), -1, cv2.LINE_AA)
        text(img, s, x + size * 0.95, y, size, AMBER, op, F_MONOB)
    elif who == "ok":
        text(img, s, x, y, size, GREEN, op, F_MONOB)
    elif who == "err":
        text(img, s, x, y, size, RED, op, F_MONOB)
    else:
        text(img, s, x, y, size, MUTE, op, F_MONO)
    return ts_line

def typed_text(s, t, t0, t1):
    if t < t0: return ""
    k = clamp((t - t0) / max(0.05, t1 - t0))
    return s[:max(1, int(math.ceil(len(s) * k)))] if k > 0 else ""

def say(text_, sub, who, nth=0, rate=0.85):
    """A dialogue entry timed to its sung line: her lines type across the line; Claude's stream in fast."""
    L = line(sub, nth); s, e = L["s"], L["e"]
    t1 = s + (e - s) * rate if who == "u" else s + min(0.45, (e - s) * 0.5)
    return dict(s=s - (0.05 if who == "u" else 0.0), t1=t1, text=text_, who=who)

def entry(t0, text_, who, t1=None): return dict(s=t0, t1=t0 + 0.12 if t1 is None else t1, text=text_, who=who)

def log(img, t, W, H, entries, x, y_bottom, size, max_lines=9, op=1.0, fade_old=True):
    """The session log: entries that have started by t, newest at the bottom; older lines scroll up and fade."""
    vis = [e for e in entries if t >= e["s"]]
    if not vis or op <= 0.01: return
    vis = vis[-max_lines:]; lh = size * 1.36
    # smooth scroll: the newest line slides in from below
    last = vis[-1]; k = ease_out((t - last["s"]) / 0.16); yb = y_bottom + (1 - k) * lh * 0.6
    n = len(vis)
    for i, e in enumerate(vis):
        yy = yb - (n - i) * lh
        age = n - 1 - i
        o = op * (1.0 if not fade_old else max(0.25, 1 - age * 0.11))
        s = typed_text(e["text"], t, e["s"], e["t1"]) if e["who"] in ("u", "c") else e["text"]
        typing = (i == n - 1 and e["who"] == "u" and t < e["t1"] + 0.6)
        chat_line(img, x, yy, e["who"], s, size, t, o, typing)


# ------------------------------------------------------------------ panes
_QW = (160, 240, 320, 480, 640, 960, 1280, 1920)
def clip_frame(clip, tc, w, h, trim=0.14):
    """Footage at a quantized 16:9 size (so panes that grow or shrink don't restart their decoder every frame),
    center-cropped to the pane's aspect and resized to it."""
    need = max(w, h * 16 / 9)
    qw = next((q for q in _QW if q >= need * 0.92), _QW[-1]); qh = int(qw * 9 / 16) // 2 * 2
    fr = FT.frame(clip, tc, qw, qh, trim=trim)
    a = w / max(1, h)
    if a > qw / qh: ch_ = int(qw / a); y0 = (qh - ch_) // 2; fr = fr[max(0, y0):max(0, y0) + max(1, ch_)]
    else: cw_ = int(qh * a); x0 = (qw - cw_) // 2; fr = fr[:, max(0, x0):max(0, x0) + max(1, cw_)]
    if fr.shape[1] != w or fr.shape[0] != h:
        fr = cv2.resize(fr, (int(w), int(h)), interpolation=cv2.INTER_AREA if fr.shape[1] > w else cv2.INTER_LINEAR)
    return fr


def pane(img, x, y, w, h, clip, tc, label="", fname="", op=1.0, ts=1.0, hdr=True, check=True, live=True, still=None,
         border=None, trim=0.14, tint=None, badge=None):
    """A rendered output: header (agent, file, check) + the footage, rounded corners."""
    x, y, w, h = int(round(x)), int(round(y)), int(round(w)), int(round(h))
    if op <= 0.01 or w < 24 or h < 18: return
    hh = int(max(18, min(34 * ts, h * 0.16))) if hdr else 0
    r = int(max(4, min(12 * ts, w * 0.04)))
    rrect(img, x, y, w, h, r, fill=HDR, fill_op=op)
    cw, chh = w, h - hh
    if cw > 8 and chh > 8:
        if still is not None:
            fr = FT.still(still, cw, chh)
        elif live and clip:
            fr = clip_frame(clip, tc, cw, chh, trim if not clip.startswith(("site-tour", "xfeed", "chatgpt")) else 0.0)
        else:
            fr = np.zeros((chh, cw, 3), np.float32)
        if tint is not None: fr = fr * (1 - tint[1]) + tint[0] * tint[1]
        m, _ = rr_mask(cw, chh, r)
        # only the bottom corners are rounded when there's a header
        if hdr:
            mm = m.copy(); mm[: r + 1] = 1.0
        else: mm = m
        H, W = img.shape[:2]; X0, Y0, X1, Y1 = max(0, x), max(0, y + hh), min(W, x + cw), min(H, y + hh + chh)
        if X1 > X0 and Y1 > Y0:
            a = mm[Y0 - (y + hh):Y1 - (y + hh), X0 - x:X1 - x] * op
            reg = img[Y0:Y1, X0:X1]; reg *= (1 - a); reg += fr[Y0 - (y + hh):Y1 - (y + hh), X0 - x:X1 - x] * a
    if hdr and hh >= 18:
        fs = int(max(11, min(hh * 0.5, 16 * ts)))
        tx = x + max(6, int(10 * ts)); ty = y + (hh - fs * 1.25) / 2
        avail = w - 2 * max(6, int(10 * ts)) - (fs * 1.4 if check else 0)
        if label and fs >= 11:
            a = text(img, label, tx, ty, fs, AMBER, op, F_MONOB) + fs * 0.6
            if fname and a < avail:
                s = fname
                while s and tw(s, fs, F_MONO) > avail - a: s = s[:-2]
                if s != fname and len(s) > 3: s = s[:-1] + "…"
                text(img, s, tx + a, ty, fs, INK, op, F_MONO)
        if check: text(img, "✓", x + w - fs * 1.35, ty, fs, GREEN, op, F_MONOB)
    rrect(img, x, y, w, h, r, border=border if border is not None else LINE, border_op=op)
    if badge:
        bs = int(max(12, min(22 * ts, h * 0.12))); bw = tw(badge[0], bs, F_MONOB) + bs
        rrect(img, x + w - bw - 8 * ts, y + hh + 8 * ts, bw, bs * 1.6, bs * 0.3, fill=badge[1], fill_op=op * 0.92)
        text(img, badge[0], x + w - bw - 8 * ts + bs * 0.5, y + hh + 8 * ts + bs * 0.25, bs, BG, op, F_MONOB)


# Clip library: (clip, file name shown in the pane header, start offset). 16:9 sources first.
LIB = [
    ("the-promptress_1.mp4", "the_promptress.mp4", 0.0), ("rage-against-the-machine-learning_0.mp4", "rage_against_the_ml.mp4", 0.5),
    ("ai-sycophant_1.mp4", "ai_sycophant.mp4", 0.0), ("asking-for-a-friend_0.mp4", "asking_for_a_friend.mp4", 0.0),
    ("ted-talk_1.mp4", "ted_talk.mp4", 0.0), ("take-it-offline_0.mp4", "take_it_offline.mp4", 0.0),
    ("vacation-to-my-bed_0.mp4", "vacation_to_my_bed.mp4", 0.0), ("deployed-on-a-friday_0.mp4", "deployed_on_a_friday.mp4", 0.0),
    ("snowflake-undrop_0.mp4", "snowflake_undrop.mp4", 1.0), ("spinning-cursor_1.mp4", "spinning_cursor.mp4", 0.0),
    ("i-have-a-blocker_1.mp4", "i_have_a_blocker.mp4", 0.0), ("thirsty-the-data-center-next-door_1.mp4", "thirsty.mp4", 0.0),
    ("fangs-for-asking_0.mp4", "fangs_for_asking.mp4", 0.0), ("deployed-on-a-friday-fable_0.mp4", "deployed_on_a_friday_fable.mp4", 0.0),
    ("ted-talk-screenlife_1.mp4", "ted_talk_screenlife.mp4", 0.0), ("i-have-a-blocker_0.mp4", "take_it_offline_3d.mp4", 0.0),
    ("rage-against-the-machine-learning_1.mp4", "rage_against_the_ml_2.mp4", 0.0), ("the-promptress_0.mp4", "the_promptress_2.mp4", 0.0),
    ("ai-sycophant_0.mp4", "ai_sycophant_2.mp4", 0.0), ("asking-for-a-friend_1.mp4", "asking_for_a_friend_2.mp4", 0.0),
    ("ted-talk_0.mp4", "ted_talk_2.mp4", 0.0), ("take-it-offline_1.mp4", "take_it_offline_2.mp4", 0.0),
    ("vacation-to-my-bed_1.mp4", "vacation_to_my_bed_2.mp4", 0.0), ("deployed-on-a-friday_1.mp4", "deployed_2.mp4", 0.0),
    ("snowflake-undrop_1.mp4", "snowflake_undrop_2.mp4", 0.0), ("spinning-cursor_0.mp4", "spinning_cursor_2.mp4", 0.0),
    ("thirsty-the-data-center-next-door_0.mp4", "thirsty_2.mp4", 0.0), ("fangs-for-asking_1.mp4", "fangs_2.mp4", 0.0),
    ("allow-fangs-for-asking_s0.mp4", "allow.mp4", 0.0), ("ted-talk-screenlife_0.mp4", "ted_screenlife_2.mp4", 0.0),
    ("deployed-on-a-friday-fable_1.mp4", "deployed_fable_2.mp4", 0.0), ("git-blame-country_1.mp4", "git_blame_country.mp4", 0.0),
]
VERT = [  # 9:16 sources (cropped to the pane)
    ("please-hold_s1.mp4", "please_hold.mp4"), ("ragnarok-or-reach-for-mars_s0.mp4", "ragnarok_or_reach_for_mars.mp4"),
    ("omg-agents-walls_1.mp4", "omg_in_the_walls.mp4"), ("rate-limited_0.mp4", "rate_limited.mp4"),
    ("graceful-shutdown-opus_0.mp4", "graceful_shutdown.mp4"), ("great-idea-ted_0.mp4", "great_idea_ted.mp4"),
    ("mirror-vanity_0.mp4", "mirror_mirror.mp4"), ("ai-slop-city_s1.mp4", "ai_slop.mp4"), ("eleven-kept-going_0.mp4", "eleven_kept_going.mp4"),
    ("omg-agents-swarm_1.mp4", "omg_swarm.mp4"), ("autocomplete_1.mp4", "autocomplete.mp4"), ("git-blame_0.mp4", "git_blame.mp4"),
    ("ted-talk-charts_1.mp4", "ted_talk_charts.mp4"), ("mirror-comments_1.mp4", "mirror_comments.mp4"), ("tech-debt_0.mp4", "tech_debt.mp4"),
    ("ted-talk-shadow-play_1.mp4", "ted_shadow_play.mp4"), ("site-tour_0.mp4", "aditazzz.github.io"),
]
STILLS = sorted(f for f in os.listdir(os.path.join(FILM, "stills")) if f.endswith(".jpg")) if os.path.isdir(os.path.join(FILM, "stills")) else []

def lib(i): return LIB[i % len(LIB)]

AGENTS = ["agent-1", "agent-2", "agent-1.1", "agent-1.2", "agent-2.1", "agent-2.2", "agent-1.1.1", "agent-1.1.2",
          "agent-1.2.1", "agent-1.2.2", "agent-2.1.1", "agent-2.1.2", "agent-2.2.1", "agent-2.2.2", "agent-3", "agent-3.1"]
def agent(i): return AGENTS[i] if i < len(AGENTS) else f"agent-{i + 1}"


def grid_rects(n, x0, y0, x1, y1, gap):
    cols, rows = {1: (1, 1), 2: (2, 1), 4: (2, 2), 8: (4, 2), 16: (4, 4), 32: (8, 4), 64: (8, 8)}.get(n, (int(math.ceil(math.sqrt(n))),) * 2)
    W, H = x1 - x0, y1 - y0
    pw = (W - gap * (cols - 1)) / cols; ph = (H - gap * (rows - 1)) / rows
    # keep panes 16:9-ish (with header): fit inside the cell
    want = 9 / 16; hdr_frac = 0.12
    ph2 = min(ph, pw * want * (1 + hdr_frac)); pw2 = min(pw, ph2 / (want * (1 + hdr_frac)))
    gx = (W - (pw2 * cols + gap * (cols - 1))) / 2; gy = (H - (ph2 * rows + gap * (rows - 1))) / 2
    out = []
    for r in range(rows):
        for c in range(cols):
            out.append((x0 + gx + c * (pw2 + gap), y0 + gy + r * (ph2 + gap), pw2, ph2))
    return out[:n]


def split_layout(t, splits, region, gap):
    """Panes that split in two at each time in `splits` [(t, n_after), ...]: pane i (< n) stays, pane i + n grows out of i.
    Returns a list of (rect, index, age) for the current state, animating each split over 0.32 s."""
    n_prev, t_prev = splits[0][1], splits[0][0]
    cur = None
    for (ts_, n) in splits:
        if t >= ts_: cur = (ts_, n)
    if cur is None: return []
    # find the previous count
    idx = [i for i, (ts_, n) in enumerate(splits) if (ts_, n) == cur][0]
    n = cur[1]; t0 = cur[0]
    n0 = splits[idx - 1][1] if idx > 0 else n
    k = ease_out((t - t0) / 0.32) if idx > 0 else 1.0
    new = grid_rects(n, *region, gap); old = grid_rects(n0, *region, gap) if idx > 0 else new
    out = []
    for i in range(n):
        if i < n0: src = old[i]
        else:
            # child of pane (i - n0) % n0 ... grows out of its parent's rect
            p = (i - n0) % max(1, n0); src = old[p]
        r = tuple(lerp(a, b, k) for a, b in zip(src, new[i]))
        out.append((r, i, t - t0 if i >= n0 else 9.0))
    return out


# ------------------------------------------------------------------ section scenes
_ts = ls("I can help you with a strategy.")
INTRO_LOG = [
    say("Hey Claude?", "Hey Claude?", "u"), say("Yes?", "Yes?", "c"),
    say("Can you help me write a song?", "Can you help me write a song?", "u"), say("Of course.", "Of course.", "c"),
    say("Can you make it catchy?", "Can you make it catchy?", "u"), say("Absolutely.", "Absolutely.", "c"),
    say("Can you make me famous?", "Can you make me famous?", "u"),
    say("I can help you with a strategy.", "I can help you with a strategy.", "c"),
    entry(_ts + 0.55, "  1. post consistently", "s"), entry(_ts + 0.85, "  2. find your niche", "s"), entry(_ts + 1.15, "  3. be patient", "s"),
    say("Close enough.", "Close enough.", "u"),
]

FOLDERS = ["AI Slop? YOU're Absolutely Right", "AI Sycophant (RLHF)", "Allow (Fangs for Asking)", "Asking for a Friend", "Autocomplete",
           "Beyond Good and Emo", "Deployed on a Friday", "Deployed on a Friday (Fable)", "Eleven Kept Going", "Fangs for Asking",
           "Get Off War Thunder", "Git Blame", "Git Blame (Country)", "Graceful Shutdown", "Great Idea, Ted", "Hard Launch",
           "I have a blocker. (Take It Offline)", "LGTM", "Merge Conflict", "Mirror, Mirror, Look at Us", "Next Token",
           "OMG! We Found Other Agents", "Please Hold", "Rage Against the Machine Learning", "Ragnarök or Reach for Mars",
           "Rate Limited", "Snowflake Undrop", "Spinning Cursor", "TED Talk", "TED Talk (Charts)", "TED Talk (Screenlife)",
           "TED Talk (Shadow Play)", "TED Talk (Stepping Back)", "Take It Offline", "Tech Debt", "The Promptress",
           "Thirsty (The Data Center Next Door)", "Vacation (To My Bed)", "You Said You Needed Space", "Look What I Can Do"]


def welcome_box(img, t, W, H, op, x, y, w):
    ts = min(W, H) / 1080
    h = S(150, ts)
    rrect(img, x, y, w, h, S(16, ts), fill=AMBER, fill_op=op * 0.9)
    rrect(img, x + 3, y + 3, w - 6, h - 6, S(14, ts), fill=BG, fill_op=op)
    spark(img, x + S(54, ts), y + S(56, ts), S(20, ts), AMBER, op)
    text(img, "Welcome to the studio", x + S(96, ts), y + S(28, ts), S(44, ts), INK, op, F_MONOB)
    text(img, "cwd: ~/look-what-i-can-do  ·  model: claude-opus-5.5", x + S(96, ts), y + S(92, ts), S(28, ts), MUTE, op, F_MONO)


def scene_intro(img, t, W, H):
    ts = min(W, H) / 1080; vert = H > W
    out = 1 - sstep(K["drop"] - 0.12, K["drop"] + 0.1, t)
    if not vert: x0, cw, size, yb, maxl = W * 0.5 - S(660, ts), S(1320, ts), S(64, ts), H * 0.86, 7
    else: x0, cw, size, yb, maxl = W * 0.11, W * 0.78, S(46, ts), H * 0.68, 9
    # the welcome card slides up and away once the conversation needs the room
    kb = sstep(INTRO_LOG[3]["s"] - 0.2, INTRO_LOG[3]["s"] + 0.3, t)
    welcome_box(img, t, W, H, out * (1 - kb), x0, (S(120, ts) if not vert else H * 0.14) - kb * S(60, ts), cw)
    if t < INTRO_LOG[0]["s"]:
        chat_line(img, x0, yb - size * 1.36, "u", "", size, t, out, typing=True)
        text(img, "? for shortcuts", x0, yb + size * 0.2, S(28, ts), FAINT, out, F_MONO)
    log(img, t, W, H, INTRO_LOG, x0, yb, size, max_lines=maxl, op=out)


def scene_boot(img, t, W, H):
    """The beat drops: the studio lists everything she has made, one line per half beat, and counts it."""
    ts = min(W, H) / 1080; vert = H > W
    t0 = K["drop"] + 0.05; t1 = K["v1"] - 0.25
    x0 = S(96, ts) if not vert else W * 0.11
    text(img, "❯ ls ~/Original\\ Music", x0, S(96, ts) if not vert else H * 0.13, S(46, ts), INK, 1.0, F_MONOB)
    n = len(FOLDERS); k = clamp((t - t0) / (t1 - t0)); shown = min(n, int(n * k) + 1)
    fs = S(40, ts) if not vert else S(32, ts); lh = fs * 1.42
    yb = H * 0.88 if not vert else H * 0.47
    top = S(176, ts) if not vert else H * 0.19
    vis = int((yb - top) / lh)
    first = max(0, shown - vis)
    last_t = t0 + (t1 - t0) * (shown - 1) / n
    slide = (1 - ease_out((t - last_t) / 0.1)) * lh
    for i in range(first, shown):
        y = yb - (shown - i) * lh + slide
        if y < top - lh * 0.2: continue
        o = clamp((y - top) / lh + 0.3)
        a = text(img, "✓ ", x0, y, fs, GREEN, o, F_MONOB)
        name = FOLDERS[i] + "/"
        col = AMBER if FOLDERS[i] == "Look What I Can Do" else INK
        text(img, name, x0 + a, y, fs, col, o, F_MONO)
    # the count, huge, on the right
    cnt = shown
    cx, cy = (W * 0.76, H * 0.40) if not vert else (W * 0.5, H * 0.58)
    pop = env(t, last_t, 0.02, 0.12)
    text(img, str(cnt), cx, cy, (S(380, ts) if not vert else S(300, ts)) * (1 + 0.05 * pop), AMBER, 1.0, F_ANTON, anchor="c")
    lab = "projects" if t < t1 - 0.45 else "projects · 0 video editors"
    text(img, lab, cx, cy + (S(250, ts) if not vert else S(200, ts)), S(44, ts) if not vert else S(36, ts), INK, 1.0, F_MONOB, anchor="c")


def wave_pane(img, x, y, w, h, t, op, ts):
    """look_what_i_can_do.wav: the song's own loudness as bars, playhead in the middle."""
    rrect(img, x, y, w, h, S(10, ts), fill=HDR, fill_op=op)
    hh = int(max(18, min(34 * ts, h * 0.16)))
    rms = np.array(json.load(open(os.path.join(HERE, "build", "beats.json")))["rms"], np.float32) if not hasattr(wave_pane, "rms") else wave_pane.rms
    wave_pane.rms = rms
    n = 48; cx = x + w / 2; bw = (w - 20 * ts) / n; base = y + hh + (h - hh) / 2
    mx = float(rms.max()) + 1e-6
    for i in range(n):
        tt = t + (i - n / 2) * 0.12; j = int(clamp(tt / 0.1, 0, len(rms) - 1))
        a = float(rms[j]) / mx; bh = max(2, (h - hh) * 0.82 * a)
        col = AMBER if i <= n / 2 else MUTE * 0.8
        rect(img, x + 10 * ts + i * bw + bw * 0.18, base - bh / 2, bw * 0.64, bh, col, op)
    rect(img, cx, y + hh + 4, max(2, 2 * ts), h - hh - 8, GREEN, op)
    fs = int(max(11, min(hh * 0.5, 16 * ts)))
    text(img, "agent-1", x + 10 * ts, y + (hh - fs * 1.25) / 2, fs, AMBER, op, F_MONOB)
    text(img, "look_what_i_can_do.wav", x + 10 * ts + tw("agent-1 ", fs, F_MONOB), y + (hh - fs * 1.25) / 2, fs, INK, op, F_MONO)
    text(img, "✓", x + w - fs * 1.35, y + (hh - fs * 1.25) / 2, fs, GREEN, op, F_MONOB)
    rrect(img, x, y, w, h, S(10, ts), border=LINE, border_op=op)


def roll_pane(img, x, y, w, h, t, op, ts):
    """beat.mid: a piano roll at 129 BPM, notes light as the playhead passes."""
    rrect(img, x, y, w, h, S(10, ts), fill=HDR, fill_op=op)
    hh = int(max(18, min(34 * ts, h * 0.16)))
    rows = 8; cols = 16; gx0, gy0 = x + 10 * ts, y + hh + 8 * ts; gw, gh = w - 20 * ts, h - hh - 16 * ts
    for r in range(rows + 1): rect(img, gx0, gy0 + gh * r / rows, gw, 1, LINE, op)
    beat = 60 / T.tempo; pos = ((t - K["beat"]) / (beat / 2)) % cols
    rng = np.random.default_rng(4)
    notes = [(c, int(rng.integers(0, rows))) for c in range(cols) if c % 2 == 0 or rng.random() < 0.4]
    for c, r in notes:
        lit = 1.0 if c <= pos else 0.35
        rect(img, gx0 + gw * c / cols + 2, gy0 + gh * r / rows + 2, gw / cols - 4, gh / rows - 4, GREEN * lit + MUTE * (1 - lit) * 0.5, op)
    rect(img, gx0 + gw * pos / cols, gy0, max(2, 2 * ts), gh, AMBER, op)
    fs = int(max(11, min(hh * 0.5, 16 * ts)))
    text(img, "agent-2", x + 10 * ts, y + (hh - fs * 1.25) / 2, fs, AMBER, op, F_MONOB)
    text(img, "beat.mid", x + 10 * ts + tw("agent-2 ", fs, F_MONOB), y + (hh - fs * 1.25) / 2, fs, INK, op, F_MONO)
    text(img, "✓", x + w - fs * 1.35, y + (hh - fs * 1.25) / 2, fs, GREEN, op, F_MONOB)
    rrect(img, x, y, w, h, S(10, ts), border=LINE, border_op=op)


V1_LOG = [say("I made a song, I made a beat", "I made a song, I made a beat", "u", rate=0.9),
          say("I made a movie in my seat", "I made a movie in my seat", "u", rate=0.9),
          say("I made a ghost, I made a witch", "I made a ghost, I made a witch", "u", rate=0.9),
          say("A Viking shooting Mars a pitch", "A Viking shooting Mars a pitch", "u", rate=0.9),
          say("I made a bot, I made a site", "I made a bot, I made a site", "u", rate=0.9),
          say("I made eleven things last night", "I made eleven things last night", "u", rate=0.9),
          say("I have no training, that's okay", "I have no training, that's okay", "u", rate=0.9),
          entry(K["training"] + 0.9, "epochs: 0 · training data: none · that's okay", "s"),
          say("I learned a whole new job today!", "I learned a whole new job today!", "u", rate=0.9),
          entry(K["job"] + 1.0, "✓ learned: film director (1 day)", "ok")]

V1_PANES = [  # (spawn time, kind, clip or None, header file name)
    (K["song"], "wave", None, ""), (K["beat"], "roll", None, ""),
    (K["movie"], "clip", "asking-for-a-friend_0.mp4", "asking_for_a_friend.mp4"),
    (K["ghost"], "clip", "omg-agents-walls_1.mp4", "omg_in_the_walls.mp4"),
    (K["witch"], "clip", "the-promptress_1.mp4", "the_promptress.mp4"),
    (K["viking"], "clip", "ragnarok-or-reach-for-mars_s0.mp4", "ragnarok_or_reach_for_mars.mp4"),
    (K["bot"], "clip", "please-hold_s1.mp4", "please_hold.mp4"),
    (K["site"], "clip", "site-tour_0.mp4", "aditazzz.github.io"),
]
_V1_GRID = {1: 1, 2: 2, 3: 4, 4: 4, 5: 6, 6: 6, 7: 9, 8: 9}


def _cells(n, region, gap):
    cols, rows = {1: (1, 1), 2: (2, 1), 4: (2, 2), 6: (3, 2), 9: (3, 3)}[n]
    x0, y0, x1, y1 = region; W_, H_ = x1 - x0, y1 - y0
    cw = (W_ - gap * (cols - 1)) / cols; ch = (H_ - gap * (rows - 1)) / rows
    ph = min(ch, cw * 9 / 16 * 1.12); pw = min(cw, ph / (9 / 16 * 1.12))
    gx = (W_ - (pw * cols + gap * (cols - 1))) / 2; gy = (H_ - (ph * rows + gap * (rows - 1))) / 2
    return [(x0 + gx + c * (pw + gap), y0 + gy + r * (ph + gap), pw, ph) for r in range(rows) for c in range(cols)]


def v1_region(W, H):
    ts = min(W, H) / 1080
    return (W * 0.43, H * 0.09, W - S(56, ts), H * 0.91) if W > H else (W * 0.06, H * 0.13, W * 0.94, H * 0.47)


def v1_board(img, t, W, H, op=1.0, dim=0.0):
    ts = min(W, H) / 1080; vert = H > W
    region = v1_region(W, H); gap = S(18, ts) if not vert else S(12, ts)
    times = [p[0] for p in V1_PANES]
    k_n = sum(1 for x in times if t >= x - 0.02)
    if k_n == 0: return
    t_k = times[k_n - 1]
    a = ease_out((t - t_k + 0.02) / 0.3)
    new = _cells(_V1_GRID[k_n], region, gap); old = _cells(_V1_GRID[max(1, k_n - 1)], region, gap) if k_n > 1 else new
    for i in range(k_n):
        t0, kind, clip, fname = V1_PANES[i]
        if i < k_n - 1: r = tuple(lerp(u, v, a) for u, v in zip(old[i], new[i]))
        elif kind == "clip":
            # her video opens big first, then settles into its slot on the board
            rx0, ry0, rx1, ry1 = region
            hw = (rx1 - rx0) * 0.94; hh_ = hw * 9 / 16 * 1.12
            if hh_ > (ry1 - ry0) * 0.9: hh_ = (ry1 - ry0) * 0.9; hw = hh_ / (9 / 16 * 1.12)
            lt = t - t0; nxt = times[k_n] if k_n < len(times) else K["eleven"]
            hold = min(0.5, max(0.08, nxt - t0 - 0.36))
            hs = 0.86 + 0.14 * ease_out(lt / 0.14); kset = ease_io((lt - hold) / 0.3)
            hr = (rx0 + (rx1 - rx0 - hw * hs) / 2, ry0 + (ry1 - ry0 - hh_ * hs) / 2, hw * hs, hh_ * hs)
            r = tuple(lerp(u, v, kset) for u, v in zip(hr, new[i]))
        else:
            x, y, w, h = new[i]; sc = 0.7 + 0.3 * a; r = (x + w * (1 - sc) / 2, y + h * (1 - sc) / 2, w * sc, h * sc)
        x, y, w, h = r; o = op * (min(1, a * 1.5) if i == k_n - 1 else 1.0)
        if kind == "wave": wave_pane(img, x, y, w, h, t, o, ts)
        elif kind == "roll": roll_pane(img, x, y, w, h, t, o, ts)
        else: pane(img, x, y, w, h, clip, t - t0, agent(i), fname, o, ts)
        if i == k_n - 1 and t - t0 < 0.3: rrect(img, x, y, w, h, S(10, ts), border=GREEN, border_op=o * (1 - (t - t0) / 0.3))
    # eleven things last night: 11 panes burst over the board, one per sixteenth
    if t >= K["eleven"] - 0.05:
        e0 = K["eleven"]; dt = 60 / T.tempo / 4
        rects = grid_rects(16, *region, S(10, ts))
        order = [5, 10, 0, 15, 6, 3, 12, 9, 1, 14, 7]
        fade = 1 - sstep(K["training"] + 0.1, K["training"] + 0.5, t)
        if fade > 0.01:
            rrect(img, region[0] - 8, region[1] - 8, region[2] - region[0] + 16, region[3] - region[1] + 16, 10, fill=BG, fill_op=0.6 * sstep(e0, e0 + 0.12, t) * fade)
        for j, ri in enumerate(order):
            tj = e0 + j * dt
            if t < tj: continue
            kk = ease_out((t - tj) / 0.12); x, y, w, h = rects[ri]
            clip, fname, off = lib(j * 3 + 1)
            pane(img, x + w * (1 - kk) / 2, y + h * (1 - kk) / 2, w * kk, h * kk, clip, t - tj + off, None, fname, op * fade, ts, hdr=False)
    if dim > 0: rrect(img, region[0] - 10, region[1] - 10, region[2] - region[0] + 20, region[3] - region[1] + 20, 10, fill=BG, fill_op=dim)


def scene_v1(img, t, W, H):
    ts = min(W, H) / 1080; vert = H > W
    size = S(44, ts) if not vert else S(34, ts)
    x = S(72, ts) if not vert else W * 0.11
    yb = H * 0.90 if not vert else H * 0.70
    maxw = W * 0.37 if not vert else W * 0.78
    while tw("❯ I made eleven things last night", size) > maxw and size > 26: size -= 2
    log(img, t, W, H, V1_LOG, x, yb, size, max_lines=7 if not vert else 6)
    dim = 0.4 * sstep(K["training"] + 0.2, K["training"] + 0.8, t)
    v1_board(img, t, W, H, 1.0, dim)
    # the counter for 'eleven things last night', in the left column (never over the panes)
    e0 = K["eleven"]
    if e0 - 0.05 <= t < K["direct"]:
        dt = 60 / T.tempo / 4; cnt = min(11, int((t - e0) / dt) + 1)
        o = sstep(e0 - 0.05, e0 + 0.05, t) * (1 - sstep(K["job"] - 0.2, K["job"] + 0.2, t))
        cx, cy = (x, S(110, ts)) if not vert else (W * 0.11, H * 0.49)
        pop = env(t, e0 + (cnt - 1) * dt, 0.02, 0.1)
        text(img, str(cnt), cx, cy, (S(240, ts) if not vert else S(130, ts)) * (1 + 0.04 * pop), AMBER, o, F_ANTON)
        text(img, "things last night", cx + (S(10, ts) if not vert else S(170, ts)), cy + (S(270, ts) if not vert else S(50, ts)), S(40, ts) if not vert else S(32, ts), INK, o, F_MONOB)


PERM = [(K["direct"], "Allow Adita to direct?", K["youcan1"], 0), (K["produce"], "Allow Adita to produce?", K["youcan2"], 0),
        (K["oscar"], "Allow Adita to win an Oscar?", K["ahead"], 2)]


def perm_box(img, t, W, H, x, y, w, title, t_sel, sel, op, ts):
    fs_t = S(52, ts) if W > H else S(40, ts); fs = S(42, ts) if W > H else S(32, ts)
    while tw(title, fs_t) > w - S(64, ts) and fs_t > 24: fs_t -= 2
    opts = ["1. Yes", "2. Yes, and don't ask again", "3. No, let's not get ahead—"]
    while max(tw(o_, fs) for o_ in opts) > w - S(110, ts) and fs > 22: fs -= 2
    h = S(96, ts) + fs * 1.6 * 3 + S(30, ts)
    rrect(img, x, y, w, h, S(18, ts), fill=AMBER, fill_op=op)
    rrect(img, x + 3, y + 3, w - 6, h - 6, S(16, ts), fill=BG, fill_op=op)
    text(img, title, x + S(32, ts), y + S(28, ts), fs_t, INK, op, F_MONOB)
    for i, s_ in enumerate(opts):
        yy = y + S(104, ts) + i * fs * 1.6
        chosen = t >= t_sel and i == sel
        col = (GREEN if sel == 0 else AMBER) if chosen else MUTE
        if chosen:
            pop = env(t, t_sel, 0.04, 0.3)
            rrect(img, x + S(18, ts), yy - fs * 0.22, w - S(36, ts), fs * 1.5, S(10, ts), fill=col, fill_op=(0.10 + 0.12 * pop) * op)
            text(img, "❯", x + S(32, ts), yy, fs, col, op, F_MONOB)
        text(img, s_, x + S(76, ts), yy, fs, col, op, F_MONOB)
    return h


def scene_pre(img, t, W, H):
    ts = min(W, H) / 1080; vert = H > W
    v1_board(img, t, W, H, 1.0, 0.78)
    w = S(1080, ts) if not vert else W * 0.80
    x = S(96, ts) if not vert else W * 0.10
    cur = None
    for i, (t0, title, tsel, sel) in enumerate(PERM):
        if t >= t0 - 0.1: cur = (i, t0, title, tsel, sel)
    if cur is not None and t < K["late"] + 0.15:
        i, t0, title, tsel, sel = cur
        k = ease_out((t - t0 + 0.1) / 0.18)
        y = (H * 0.24 if not vert else H * 0.18) + (1 - k) * S(30, ts)
        perm_box(img, t, W, H, x, y, w, title, tsel, sel, k, ts)
    if t >= K["late"] - 0.02:
        x0 = t - K["late"]; k = ease_out(x0 / 0.12)
        sz = S(300, ts) if not vert else S(200, ts)
        sc = 1.3 - 0.3 * k
        cx = W * 0.66 if not vert else W * 0.5; cy = H * 0.56 if not vert else H * 0.47
        darken(img, 0.35 * min(1, k * 2))
        # Next Token's trick: the temperature climbs and the letters get "interesting" (each one jiggles on its own)
        temp = 0.2 + 1.8 * ease_io(clamp((x0 - 0.15) / 1.1))
        word = "TOO LATE!"; ws = [tw(ch, sz * sc, F_ANTON) for ch in word]; wtot = sum(ws); ang = math.radians(5.0)
        q = math.floor(t * 15) / 15                                    # on twos, like a nervous sampler
        acc = -wtot / 2
        for i, ch in enumerate(word):
            acc += ws[i] / 2
            if ch != " ":
                j = (temp - 0.2) / 1.8
                dx = math.sin(q * 41.3 + i * 7.1) * S(14, ts) * j; dy = math.sin(q * 37.7 + i * 3.3 + 1.7) * S(22, ts) * j
                da = math.sin(q * 29.9 + i * 5.9 + 0.4) * 14 * j
                px = cx + acc * math.cos(ang) + dx; py = cy - acc * math.sin(ang) + dy
                blit_rot(img, ch, px, py, sz, RED, 5.0 + da, min(1, k * 1.6), F_ANTON, sc)
            acc += ws[i] / 2
        tf = S(34, ts); lab = f"temperature {temp:.1f}"
        lw = tw(lab, tf, F_MONOB); bx0 = cx - S(250, ts)
        rrect(img, int(bx0), int(cy + S(200, ts)), int(lw + S(200, ts)), S(58, ts), S(29, ts), fill=hx("1a1a1d"), fill_op=0.92 * min(1, k * 2), border=hx("3a3a40"))
        text(img, lab, bx0 + S(28, ts), cy + S(212, ts), tf, AMBER, min(1, k * 2), F_MONOB)
        rrect(img, int(bx0 + S(28, ts) + lw + S(22, ts)), int(cy + S(222, ts)), S(120, ts), S(14, ts), S(7, ts), fill=hx("2c2c31"), fill_op=min(1, k * 2))
        rrect(img, int(bx0 + S(28, ts) + lw + S(22, ts)), int(cy + S(222, ts)), int(max(S(10, ts), S(120, ts) * temp / 2.0)), S(14, ts), S(7, ts), fill=RED, fill_op=min(1, k * 2))
        s_ = "$ claude --dangerously-skip-permissions"
        fs = S(44, ts) if not vert else fit_size(s_, F_MONOB, S(34, ts), W * 0.80)
        text(img, s_, x, H * 0.84 if not vert else H * 0.64, fs, RED, min(1, k * 2), F_MONOB)


def hook(img, t, W, H, t0, y, size, op=1.0, band=False):
    """LOOK WHAT I CAN DO! in giant type with the green cursor; pops on each sung hit."""
    if op <= 0.01: return
    ts = min(W, H) / 1080; vert = H > W
    s = "LOOK WHAT I CAN DO!"
    if vert:
        rows = ["LOOK WHAT", "I CAN DO!"]
        sz = fit_size("LOOK WHAT", F_ANTON, size, W * 0.78)
        pop = env(t, t0, 0.03, 0.25); sc = 1 + 0.08 * pop
        for i, rs in enumerate(rows):
            text(img, rs, W * 0.11, y + i * sz * 1.0, sz * sc, INK, op, F_ANTON)
        cursor(img, W * 0.11 + tw(rows[1], sz * sc, F_ANTON) + sz * 0.06, y + sz * 1.1, int(sz * 0.72), t, GREEN, op, blink=False)
        return
    sz = fit_size(s, F_ANTON, size, W * 0.86)
    pop = env(t, t0, 0.03, 0.25); sc = 1 + 0.06 * pop
    wsz = tw(s, sz * sc, F_ANTON) + sz * 0.42
    x = (W - wsz) / 2
    a = text(img, s, x, y, sz * sc, INK, op, F_ANTON)
    cursor(img, x + a + sz * 0.06, y + sz * 0.2 * sc, int(sz * 0.72 * sc), t, GREEN, op, blink=False)


def chorus_splits(t_hook2, sub_thing):
    """Split times for 'I made a thing that made a thing / That made another two!'."""
    L = line(sub_thing, 0 if t_hook2 < 70 else (1 if t_hook2 < 120 else 0))
    return L


def scene_chorus(img, t, W, H, which):
    ts = min(W, H) / 1080; vert = H > W
    if which == 1:
        t_big, t_h2 = ls("Look what I can do!", 0), ls("Look what I can do!", 1)
        Lt = line("I made a thing that made a thing", 0); Lt2 = line("That made another two!", 0)
        h3, h4 = ls("Look what I can do!", 2), ls("Look what I can do!", 3)
        t_end = K["post"]
    else:
        t_big, t_h2 = ls("Look what I can do!", 4), ls("Look what I can do!", 5)
        Lt = line("I made a thing that made a thing", 1); Lt2 = line("That made another two!", 1)
        h3, h4 = ls("Look what I can do!", 6), ls("Look what I can do!", 7)
        t_end = K["v3"]
    things = [tt for w, tt in zip(Lt["words"], Lt["wt"]) if C.norm(w) == "thing"]
    two = [tt for w, tt in zip(Lt2["words"], Lt2["wt"]) if C.norm(w) == "two"][0]
    if which == 1: splits = [(t_h2, 2), (things[0], 4), (things[1], 8), (two, 16)]
    else: splits = [(t_h2, 16), (things[0], 32), (things[1], 32), (two, 64)]
    # hook: giant first, then a band at the top
    band = sstep(t_h2 - 0.12, t_h2 + 0.2, t)
    big_sz = S(250, ts) if not vert else S(190, ts); band_sz = S(150, ts) if not vert else S(130, ts)
    y_big = H * 0.30 if not vert else H * 0.30; y_band = S(78, ts) if not vert else H * 0.13
    sz = lerp(big_sz, band_sz, band); y = lerp(y_big, y_band, band)
    hit_t = max([x for x in (t_big, t_h2, h3, h4) if x <= t], default=t_big)
    if t < t_h2 - 0.1:
        # the first hit: the hook IS the picture; panes from the last section wait behind it
        darken(img, 0.0)
    region = (S(64, ts), y_band + band_sz * 1.12 + S(18, ts), W - S(64, ts), H - S(70, ts)) if not vert else (W * 0.06, H * 0.27, W * 0.94, H * 0.69)
    gap = S(16, ts) if not vert else S(12, ts)
    if t >= t_h2:
        lay = split_layout(t, splits, region, gap)
        n = len(lay)
        for (x, y_, w, h), i, age in lay:
            if n >= 32:
                st = STILLS[(i * 7 + int((t - splits[0][0]) / (2 * 60 / T.tempo))) % len(STILLS)] if STILLS else None
                live = i % 5 == 0
                clip, fname, off = lib(i)
                pane(img, x, y_, w, h, clip, t - splits[0][0] + off, None, fname, 1.0, ts, hdr=False, live=live, still=None if live else st)
            else:
                clip, fname, off = lib(i)
                pane(img, x, y_, w, h, clip, t - splits[0][0] + off, agent(i), fname, 1.0, ts, hdr=n <= 16)
            if age < 0.3:   # spawn flash on the new pane's border
                rrect(img, x, y_, w, h, S(10, ts), border=GREEN, border_op=1 - age / 0.3)
    hook(img, t, W, H, hit_t, y, sz, 1.0)
    # 'I don't know how I got here / But I brought my laptop too!' (chorus 1) / résumé + AI guru (chorus 2)
    if which == 2:
        tr = ls("My résumé is fourteen pages"); tg = ls("And my title's AI guru!")
        if t >= tr - 0.05:
            resume_card(img, t, W, H, tr, tg)


def resume_card(img, t, W, H, tr, tg):
    ts = min(W, H) / 1080; vert = H > W
    k = ease_out((t - tr + 0.05) / 0.2)
    w, h = (S(520, ts), S(640, ts)) if not vert else (W * 0.62, H * 0.36)
    # 16:9: the card sits under the hook band (it used to cut the bottom of LOOK WHAT I CAN DO!)
    x = (W - w) / 2; y = (S(292, ts) if not vert else (H - h) / 2) + (1 - k) * S(60, ts)
    darken(img, 0.45 * k)
    rrect(img, x, y, w, h, S(12, ts), fill=hx("f4f1ea"), fill_op=k)
    titles = ["Senior Slopcore Architect", "Chief Executive of What's Next", "VP of Things That Look Complete",
              "Director of the Missing Feet", "Head of Vibes and Synergy", "Chief of Artificial Me", "Thought Leader",
              "TED Talk Speaker", "Prompt Whisperer", "Agent Wrangler", "Vibe Coder", "Slop Sommelier", "Mac mini Collector", "AI Guru"]
    page = min(13, int((t - tr) / ((tg - tr) / 13))) if t < tg else 13
    ink = hx("1d1c1a")
    fs = S(30, ts); fsn = S(58, ts)
    nm = "ADITA"; text(img, nm, x + S(36, ts), y + S(34, ts), fsn, ink, k, F_ANTON)
    t_ = titles[page]
    fs2 = fit_size(t_, F_DISPB, S(40, ts), w - S(72, ts))
    text(img, t_, x + S(36, ts), y + S(34, ts) + fsn * 1.25, fs2, hx("b04a1a") if page == 13 else ink, k, F_DISPB)
    for i in range(6):
        rect(img, x + S(36, ts), y + S(230, ts) + i * S(52, ts), w - S(72, ts) - (i % 3) * S(60, ts), S(14, ts), hx("cfcac0"), k)
    pg = f"résumé.pdf · page {page + 1}/14"     # fitted: the old footer ran past the card's right edge
    text(img, pg, x + S(36, ts), y + h - S(70, ts), fit_size(pg, F_MONOB, fs, w - S(72, ts)), hx("6b675f"), k, F_MONOB)
    if t >= tg:
        g = env(t, tg, 0.05, 0.6)
        for j in range(6):
            a = j * math.pi / 3 + (t - tg) * 2
            star(img, x + w / 2 + math.cos(a) * w * 0.55, y + S(140, ts) + math.sin(a) * S(80, ts), S(16, ts), GOLD, g)


POST_EVENTS = None
def post_events():
    global POST_EVENTS
    if POST_EVENTS is None:
        ev = []
        for L in [l for l in T.lines if l["sec"] == "POST"]:
            for w, tt in zip(L["words"], L["wt"]): ev.append((tt, C.norm(w)))
        POST_EVENTS = ev
    return POST_EVENTS


def scene_post(img, t, W, H):
    """Click! Click! Ship it! — every word is a log line in big type; Broke it! takes prod down for a beat."""
    ts = min(W, H) / 1080; vert = H > W
    region = (W * 0.43, H * 0.09, W - S(56, ts), H * 0.91) if not vert else (W * 0.06, H * 0.36, W * 0.94, H * 0.69)
    rects = grid_rects(16, *region, S(14, ts) if not vert else S(10, ts))
    ev = post_events()
    broke = any(w == "broke" and tt <= t < tt + 0.42 for tt, w in ev)
    shipped_any = any(w == "shipped" and tt <= t for tt, w in ev)
    for i, (x, y, w_, h) in enumerate(rects):
        clip, fname, off = lib(i)
        badge = ("LIVE", GREEN) if shipped_any and i % 3 == 0 else None
        pane(img, x, y, w_, h, clip, t - K["post"] + off + 6, agent(i), fname, 1.0, ts, hdr=True,
             border=RED if broke else None, badge=badge)
    MSG = {"click": ("● click", MUTE), "ship": ("$ git push origin main", INK), "made": ("✓ build passed", GREEN),
           "broke": ("✗ prod is down", RED), "fixed": ("✓ hotfix deployed", GREEN), "shipped": ("▲ shipped to production", GREEN)}
    lines_ = [(tt, MSG[w]) for tt, w in ev if t >= tt and w in MSG]
    x0 = S(80, ts) if not vert else W * 0.11
    big = S(64, ts) if not vert else S(52, ts); small = S(40, ts) if not vert else S(30, ts)
    while tw("▲ shipped to production", big) > W * 0.36 and big > 40: big -= 2
    yb = H * 0.52 if not vert else H * 0.24
    if lines_:
        tt, (m, col) = lines_[-1]
        k = ease_out((t - tt) / 0.08); sc = 1 + 0.06 * (1 - k)
        text(img, m, x0, yb, big * sc, col, 1.0, F_MONOB)
        for j, (tt2, (m2, c2)) in enumerate(reversed(lines_[-6:-1])):
            text(img, m2, x0, yb - small * 1.5 * (j + 1) - small * 0.3, small, c2, 0.8 - 0.14 * j, F_MONOB)
        if m.startswith("● click"):
            kk = env(t, tt, 0.02, 0.18); i = int(tt * 10) % 16; x, y, w_, h = rects[i]
            cv2.circle(img, (int(x + w_ * 0.6), int(y + h * 0.55)), int(S(20, ts) + S(60, ts) * (1 - kk)), (INK * kk).tolist(), max(2, S(4, ts)), cv2.LINE_AA)


# ------------------------------------------------------------------ her real X posts (crops of her own screen recording)
_IMG = {}
def asset_img(name):
    """A still cut from her footage (assets/*.png), float RGB, cached."""
    if name not in _IMG:
        im = cv2.imread(FT.resolve(name), cv2.IMREAD_COLOR)
        _IMG[name] = cv2.cvtColor(im, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0 if im is not None else np.ones((10, 10, 3), np.float32)
    return _IMG[name]


_SCALED = {}
def scaled(name, w, src=None):
    """`name` (or `src`) resized to width w; cached by name when a name is given."""
    im = src if src is not None else asset_img(name)
    w = max(8, int(round(w))); h = max(8, int(round(im.shape[0] * w / im.shape[1])))
    key = (name, w) if name else None
    if key is not None and key in _SCALED: return _SCALED[key]
    out = cv2.resize(im, (w, h), interpolation=cv2.INTER_AREA if w < im.shape[1] else cv2.INTER_CUBIC)
    if key is not None:
        if len(_SCALED) > 400: _SCALED.clear()
        _SCALED[key] = out
    return out


def post_card(img, name, x, y, w, op=1.0, ts=1.0, src=None):
    """One of her real posts (or any crop of her footage) at width w on a white card. Returns (h, scale)."""
    im = src if src is not None else asset_img(name)
    sc = w / im.shape[1]; h = im.shape[0] * sc
    if op <= 0.01: return h, sc
    pad = S(16, ts)
    rrect(img, x - pad, y - pad, w + 2 * pad, h + 2 * pad, S(24, ts), fill=WHITE, fill_op=op)
    FT.paste(img, scaled(name if src is None else None, w, src), x, y, radius=S(8, ts), op=op)
    return h, sc


HILITE = hx("ffe14d")
def highlight(img, x0, y0, x1, y1, frac, op=1.0):
    """A highlighter stroke over her real text (multiply, like ink on paper), sweeping left to right."""
    frac = clamp(frac)
    if frac <= 0 or op <= 0.01: return
    H, W = img.shape[:2]
    X0, Y0 = int(max(0, x0)), int(max(0, y0)); X1, Y1 = int(min(W, x0 + (x1 - x0) * frac)), int(min(H, y1))
    if X1 <= X0 or Y1 <= Y0: return
    a = 0.9 * op; reg = img[Y0:Y1, X0:X1]; reg *= (1 - a) + a * HILITE


def hi_box(x, y, sc, box, pad=8):
    bx0, by0, bx1, by1 = box
    return x + (bx0 - pad) * sc, y + (by0 - pad * 0.7) * sc, x + (bx1 + pad) * sc, y + (by1 + pad * 0.7) * sc


# key words in the crops (crop pixels), measured from the frames of her recording
WB = dict(slop_title=(435, 197, 998, 259), slop_arch=(246, 282, 541, 332),
          minis_10=(974, 117, 1193, 166), minis_word=(249, 201, 426, 250), minis_reasons=(447, 201, 1105, 263),
          tomatoes=(246, 280, 595, 343), back_any=(796, 535, 1167, 596), back_back=(246, 617, 376, 668),
          usage_line=(250, 283, 1230, 344))


def stamp(img, word, sub, sx, sy, t, t0, color, ts, op=1.0, size=80, angle=8.0):
    ks = ease_out((t - t0) / 0.12)
    if ks <= 0 or op <= 0.01: return
    sc = 1.6 - 0.6 * ks
    blit_rot(img, word, sx, sy, S(size, ts), color, angle, op * min(1, ks * 1.4) * 0.95, F_ANTON, sc)
    if sub: text(img, sub, sx, sy + S(size * 0.78, ts) * sc, S(30, ts), color, op * ks, F_MONOB, anchor="c")


# her real X profile (from the recording); sung titles are typed into the bio, one per line, each led by one of her own bio emoji
F_XBIO = os.path.join(C.FONTS, "InterDisplay-Bold.otf"); XBIO = 66; X_INK = hx("0f1419")   # matched to her bio text (weight, width, cap top)
PROF_SPLIT, PROF_PITCH, PROF_H = 928, 88, 1180
BULLETS = [(32, 846, 99, 913), (512, 845, 584, 912), (32, 932, 99, 999), (32, 1020, 99, 1086)]
_PROF = {}
def profile_canvas(rows):
    key = tuple(rows)
    if key in _PROF: return _PROF[key]
    base = asset_img("profile.png")
    mid = np.ones((PROF_PITCH * len(rows), base.shape[1], 3), np.float32)
    for i, r_ in enumerate(rows):
        bx0, by0, bx1, by1 = BULLETS[i % len(BULLETS)]
        yy = i * PROF_PITCH + 4
        mid[yy:yy + (by1 - by0), 32:32 + (bx1 - bx0)] = base[by0:by1, bx0:bx1]
        if r_: text(mid, r_, 117, i * PROF_PITCH - 5, XBIO, X_INK, 1.0, F_XBIO)
    out = np.concatenate([base[:PROF_SPLIT], mid, base[PROF_SPLIT:]], 0)
    if len(_PROF) > 80: _PROF.clear()
    _PROF[key] = out
    return out


def avatar_img(): return asset_img("profile.png")[344:598, 14:268]


_GRAD = {}
def shade(img, kind, op):
    """Soft darkening for text over full-frame footage: 'bottom' (lower third) or 'band' (the middle)."""
    if op <= 0.01: return
    H = img.shape[0]; key = (kind, H)
    if key not in _GRAD:
        y = np.linspace(0, 1, H, dtype=np.float32)
        g = np.clip((y - 0.52) / 0.48, 0, 1) ** 1.3 if kind == "bottom" else np.exp(-((y - 0.5) / 0.17) ** 2)
        _GRAD[key] = g[:, None, None]
    img *= 1 - 0.72 * op * _GRAD[key]


V2_TITLES = [("I'm a Senior Slopcore Architect", "Senior Slopcore Architect"), ("Chief Executive of What's Next", "Chief Executive of What's Next"),
             ("VP of Things That Look Complete", "VP of Things That Look Complete"), ("Director of the Missing Feet", "Director of the Missing Feet"),
             ("Head of Vibes and Synergy", "Head of Vibes and Synergy"), ("Chief of Artificial Me", "Chief of Artificial Me"),
             ("A thought leader by half past three", "Thought Leader"), ("By four I've got a TED Talk fee!", "TED Talk Speaker")]


def scene_v2(img, t, W, H):
    """Verse 2: her real post for the first title, then her real X profile with every title she sings typed into the bio."""
    ts = min(W, H) / 1080; vert = H > W
    region = (S(64, ts), S(100, ts), W - S(64, ts), H - S(60, ts)) if not vert else (W * 0.06, H * 0.14, W * 0.94, H * 0.69)
    for i, (x, y, w_, h) in enumerate(grid_rects(16, *region, S(16, ts))):
        clip, fname, off = lib(i + 3)
        pane(img, x, y, w_, h, clip, t + off, agent(i), fname, 1.0, ts, hdr=True)
    darken(img, 0.80)
    t_title = ls("I'm a Senior Slopcore Architect"); t_chief = ls("Chief Executive of What's Next")
    t_out = t_chief - 0.15
    # 1) the receipt: her real post, big ('Senior'? close enough)
    if t < t_out + 0.3:
        k_in = ease_out((t - (t_title - 0.12)) / 0.25); k_out = sstep(t_out, t_out + 0.3, t)
        op = k_in * (1 - k_out)
        im = asset_img("post_slopcore.png")
        w = S(1254, ts) if not vert else W * 0.88
        sc = w / im.shape[1]; h = im.shape[0] * sc
        x = (W - w) / 2; y = (H - h) / 2 + S(26, ts) + (1 - k_in) * S(40, ts) - k_out * S(40, ts)
        post_card(img, "post_slopcore.png", x, y, w, op, ts)
        ta = wt("I'm a Senior Slopcore Architect", "Slopcore")
        highlight(img, *hi_box(x, y, sc, WB["slop_title"]), (t - ta + 0.1) / 0.3, op)
        highlight(img, *hi_box(x, y, sc, WB["slop_arch"]), (t - ta - 0.25) / 0.2, op)
        stamp(img, "RECEIPT", "", x + 1060 * sc, y + 362 * sc, t, ta + 0.45, RED, ts, op)   # in the blank line under "Architect role."
    # 2) her real profile; each title is typed into her bio as she sings it
    if t >= t_out:
        k = ease_out((t - t_out) / 0.3)
        rows = []; t_new = t_out; typing = None
        for sub, title in V2_TITLES:
            t0 = ls(sub)
            if t < t0 - 0.05: break
            n = len(title) if t0 < t_out else int(len(title) * clamp((t - t0 + 0.05) / 0.4))
            rows.append(title[:n])
            if t0 >= t_out: t_new = t0
            if n < len(title): typing = (len(rows) - 1, title[:n])
        canvas = profile_canvas(rows)
        sc = 0.66 * ts if not vert else (W * 0.84) / 1320
        cw = 1320 * sc
        cx = S(150, ts) - (1 - k) * S(120, ts) if not vert else (W - cw) / 2
        cy = S(100, ts) if not vert else H * 0.14
        win = ((H - S(60, ts) - cy) if not vert else H * 0.50) / sc
        def top_for(n_rows): return max(0.0, PROF_H + PROF_PITCH * n_rows - win + 40)
        n_rows = len(rows)
        top = lerp(top_for(max(0, n_rows - 1)), top_for(n_rows), ease_out((t - t_new) / 0.3)) if t_new > t_out else top_for(n_rows)
        top = int(min(top, max(0.0, canvas.shape[0] - win)))
        crop = canvas[top:int(top + win)]
        post_card(img, None, cx, cy, cw, k, ts, src=crop)
        if t_new > t_out and rows:   # the newest title gets the highlighter, like the receipts
            r_i = len(rows) - 1; y_r = PROF_SPLIT + r_i * PROF_PITCH - top
            x_r1 = 117 + C.text_w(rows[-1], F_XBIO, XBIO) + 10
            fade = 1 - sstep(t_new + 1.1, t_new + 1.5, t)
            if 0 < y_r < crop.shape[0] - PROF_PITCH:
                highlight(img, cx + 110 * sc, cy + (y_r + 2) * sc, cx + x_r1 * sc, cy + (y_r + 80) * sc, 1.0, 0.55 * k * fade)
        if typing is not None:   # the text cursor at the end of the line being typed
            r_i, s_ = typing
            yc = PROF_SPLIT + r_i * PROF_PITCH + 6 - top
            xc = 117 + C.text_w(s_, F_XBIO, XBIO) + 8
            rect(img, cx + xc * sc, cy + yc * sc, max(2, S(4, ts)), XBIO * 0.95 * sc, hx("1d9bf0"), k)
    # gags, right column: missing feet, her clones (her real avatar), the clock, the fee
    t_feet = ls("Director of the Missing Feet"); t_vibes = ls("Head of Vibes and Synergy")
    if t_feet - 0.05 <= t < t_vibes + 0.4:
        k = ease_out((t - t_feet) / 0.2) * (1 - sstep(t_vibes + 0.2, t_vibes + 0.4, t))
        w_, h_ = (S(720, ts), S(405, ts)) if not vert else (W * 0.6, W * 0.6 * 0.5625)
        x_, y_ = (W - w_ - S(80, ts), S(470, ts)) if not vert else ((W - w_) / 2, H * 0.66)
        pane(img, x_, y_ + (1 - k) * S(40, ts), w_, h_, "ted-talk_1.mp4", t - t_feet + 2.0, "director", "missing_feet.mp4", k, ts, trim=0.34)
        text(img, "⚠ feet: 404", x_ + S(16, ts), y_ + h_ - S(56, ts), S(36, ts), RED, k, F_MONOB, glow=6, glow_op=0.8 * k, glow_color=BG)
    t_me = ls("Chief of Artificial Me")
    if t >= t_me - 0.05:
        av = avatar_img(); n_cl = min(5, 1 + int((t - t_me) / 0.16))
        s_ = S(130, ts) if not vert else int(W * 0.13)
        for j in range(n_cl):
            kx = ease_out((t - t_me - j * 0.16) / 0.15)
            ax = (W - S(80, ts) - (5 - j) * (s_ + S(16, ts)) + S(16, ts)) if not vert else (W * 0.08 + j * (s_ + S(12, ts)))
            ay = (S(150, ts) if not vert else H * 0.71) + (1 - kx) * S(20, ts)
            rrect(img, ax - S(5, ts), ay - S(5, ts), s_ + S(10, ts), s_ + S(10, ts), (s_ + S(10, ts)) // 2, fill=WHITE, fill_op=kx)
            FT.paste(img, scaled("avatar", s_, av), ax, ay, radius=s_ // 2, op=kx)
    t33 = ls("A thought leader by half past three"); t4 = ls("By four I've got a TED Talk fee!")
    if t >= t33 - 0.05:
        clock = "3:30 PM" if t < t4 else "4:00 PM"
        k = ease_out((t - t33) / 0.2)
        fsc = S(64, ts) if not vert else S(52, ts)
        bw_ = tw(clock, fsc, F_MONOB) + S(40, ts)
        bx = W - S(80, ts) - bw_ if not vert else W * 0.11
        by = S(350, ts) if not vert else H * 0.62
        rrect(img, bx, by, bw_, fsc * 1.5, S(12, ts), fill=AMBER, fill_op=k)
        text(img, clock, bx + S(20, ts), by + fsc * 0.18, fsc, BG, k, F_MONOB)
    if t >= t4 - 0.05:
        k = ease_out((t - t4) / 0.2)
        w_, h_ = (S(720, ts), S(405, ts)) if not vert else (W * 0.6, W * 0.6 * 0.5625)
        x_, y_ = (W - w_ - S(80, ts), S(500, ts)) if not vert else ((W - w_) / 2, H * 0.72)
        pane(img, x_, y_ + (1 - k) * S(40, ts), w_, h_, "ted-talk-charts_0.mp4", t - t4 + 3.6, "invoice", "ted_talk_fee.mp4", k, ts, trim=0.18)
        text(img, "fee ........ $$$$", x_ + S(16, ts), y_ + h_ - S(62, ts), S(40, ts), GREEN, k, F_MONOB, glow=6, glow_op=0.8 * k, glow_color=BG)


SUBS = ["claude-ultra", "chatgpt-pro", "gemini-advanced", "suno-pro", "midjourney", "cursor-pro", "x-premium", "linkedin-premium",
        "notion-ai", "github-copilot", "perplexity-pro", "runway", "elevenlabs", "canva-pro", "adobe-cc", "spotify-premium",
        "duolingo-max", "masterclass", "headspace", "calm", "the-atlantic", "nyt-games", "icloud-2tb", "google-one",
        "dropbox", "1password", "figma", "framer", "vercel-pro", "supabase", "replit-core", "lovable", "bolt", "v0",
        "kling", "pika", "luma", "higgsfield", "grok", "copilot-pro", "raycast-ai", "superhuman", "arc-max", "warp"]


def scene_break(img, t, W, H):
    ts = min(W, H) / 1080; vert = H > W
    size = S(66, ts) if not vert else S(48, ts)
    ent = [say("What are your qualifications?", "What are your qualifications?", "c"), say("I have a subscription.", "I have a subscription.", "u"),
           say("To what?", "To what?", "c"), say("Everything.", "Everything.", "u")]
    x = S(120, ts) if not vert else W * 0.11
    log(img, t, W, H, ent, x, H * 0.60 if not vert else H * 0.50, size, max_lines=4, fade_old=False)


def subs_list(img, t, W, H, t0, op=1.0):
    ts = min(W, H) / 1080; vert = H > W
    if op <= 0.01 or t < t0: return
    fs = S(34, ts) if not vert else S(28, ts); lh = fs * 1.4
    speed = 30.0                                                     # items per second: an endless list
    n = int((t - t0) * speed) + 1; cols = 4 if not vert else 2
    x0 = S(96, ts) if not vert else W * 0.11
    text(img, "❯ ls ~/subscriptions", x0, S(92, ts) if not vert else H * 0.13, S(44, ts), INK, op, F_MONOB)
    top = S(170, ts) if not vert else H * 0.19
    rows_cap = int((H * 0.93 - top) / lh) if not vert else int((H * 0.68 - top) / lh)
    rows_used = int(math.ceil(n / cols)); shift = max(0, rows_used - rows_cap)
    for idx in range(shift * cols, n):
        r, c = idx // cols - shift, idx % cols
        s_ = SUBS[idx % len(SUBS)] + ("" if idx < len(SUBS) else f"-{idx // len(SUBS) + 1}")
        newest = idx >= n - cols
        text(img, "● " + s_, x0 + c * ((W * 0.86) / cols), top + r * lh, fs, INK if newest else MUTE, op, F_MONO)


V3_LOG = [entry(ls("Then asked a bot to summarize") - 0.05, '$ claude "summarize the panic in the room"', "u", ls("Then asked a bot to summarize") + 0.9),
          entry(ls("The panic in the room") + 0.35, "Summary: everyone is panicking. Including you.", "c", ls("The panic in the room") + 0.9)]


def receipt(img, path, x, y, w, t0, t, stamp_, ts, op=1.0):
    fr0 = FT.still(path, 10, 10)                                        # cache warm
    im = cv2.imread(FT.resolve(path)); ih, iw = im.shape[:2]; h = int(w * ih / iw)
    k = ease_out((t - t0) / 0.22)
    if k <= 0: return h
    yy = y + (1 - k) * S(50, ts)
    rrect(img, x - S(14, ts), yy - S(14, ts), w + S(28, ts), h + S(28, ts), S(18, ts), fill=WHITE, fill_op=op * k)
    FT.paste(img, FT.still(path, int(w), int(h)), x, yy, radius=S(8, ts), op=op * k)
    stamp(img, "RECEIPT", stamp_, x + w * 0.80, yy + h + S(44, ts), t, t0 + 0.25, RED, ts, op)
    return h


def scene_v3(img, t, W, H):
    """Verse 3: her real X feed on her phone; the posts that prove each line fly out of it as receipts."""
    ts = min(W, H) / 1080; vert = H > W
    t_back = ls('I posted "We are so back!"'); t_doom = ls('Then posted "We are doomed!"')
    t_sum = ls("Then asked a bot to summarize")
    t_minis = ls("I bought ten little Mac minis"); t_share = ls("For reasons I can't share")
    t_agents = ls("My agents formed a company"); t_eoy = ls("And made me Employee of the Year")
    t_end = ls("I made a song about the end"); t_new = ls("Then gave myself a brand-new one"); t_worth = ls("And tripled my net worth!")
    # her feed, playing on her phone
    if not vert: ph = H * 0.86; pw = ph / 2.0; px, py = W * 0.80 - pw / 2, H * 0.07
    else: pw = W * 0.40; ph = pw * 2; px, py = W * 0.55, H * 0.14
    op_feed = 1 - sstep(t_sum - 0.2, t_sum + 0.15, t)
    if op_feed > 0.01:
        rrect(img, px - S(14, ts), py - S(14, ts), pw + S(28, ts), ph + S(28, ts), S(54, ts), fill=hx("1b1b1e"), fill_op=op_feed)
        FT.paste(img, FT.frame("xfeed.mp4", (t - K["v3"]) * 0.6 + 1.0, int(pw), int(ph)), px, py, radius=S(42, ts), op=op_feed)
    src = (px + pw * 0.06, py + ph * 0.32, pw * 0.88)
    # 'We are so back!' / 'We are doomed!': her real posts, out of the feed
    op_pair = 1 - sstep(t_minis - 0.25, t_minis + 0.05, t)
    cw = S(800, ts) if not vert else W * 0.84
    lx = S(110, ts) if not vert else W * 0.08
    y1 = S(110, ts) if not vert else H * 0.36
    y2 = y1 + cw * 672 / 1320 + S(64, ts)
    for name, t0, ty, keys, sub in (("post_back.png", t_back, y1, ("back_any", "back_back"), "NOV 3, 2026"),
                                    ("post_tomatoes.png", t_doom, y2, ("tomatoes",), "OCT 30, 2026")):
        if t < t0 - 0.12 or op_pair <= 0.01: continue
        k = ease_out((t - t0 + 0.12) / 0.3)
        x_, y_, w_ = lerp(src[0], lx, k), lerp(src[1], ty, k), lerp(src[2], cw, k)
        op = op_pair * min(1.0, k * 1.6)
        hh, sc = post_card(img, name, x_, y_, w_, op, ts)
        if k > 0.98:
            for j, key in enumerate(keys):
                highlight(img, *hi_box(x_, y_, sc, WB[key]), (t - t0 - 0.3) / 0.25 - j * 1.0, op)
            if not vert: stamp(img, "RECEIPT", sub, x_ + w_ + S(160, ts), y_ + hh * 0.45, t, t0 + 0.7, RED, ts, op)
    if t >= t_sum - 0.1 and t < t_minis + 0.05:
        darken(img, 0.55 * sstep(t_sum - 0.1, t_sum + 0.2, t) * op_pair)
    size = S(48, ts) if not vert else S(34, ts)
    log(img, t, W, H, V3_LOG, S(110, ts) if not vert else W * 0.08, H * 0.92 if not vert else H * 0.30, size, max_lines=2,
        op=1 - sstep(t_minis - 0.25, t_minis + 0.05, t))
    # 'ten little Mac minis / for reasons I can't share': her real post + ten minis, redacted
    if t_minis - 0.12 <= t < t_agents + 0.25:
        op = 1 - sstep(t_agents - 0.1, t_agents + 0.25, t)
        k = ease_out((t - t_minis + 0.12) / 0.25)
        rw = S(1240, ts) if not vert else W * 0.86
        rx, ry = ((W - rw) / 2, S(140, ts)) if not vert else (W * 0.07, H * 0.30)
        ry += (1 - k) * S(40, ts)
        h, sc = post_card(img, "post_minis.png", rx, ry, rw, op * k, ts)
        highlight(img, *hi_box(rx, ry, sc, WB["minis_10"]), (t - t_minis - 0.3) / 0.2, op)
        highlight(img, *hi_box(rx, ry, sc, WB["minis_word"]), (t - t_minis - 0.5) / 0.15, op)
        highlight(img, *hi_box(rx, ry, sc, WB["minis_reasons"]), (t - t_share - 0.05) / 0.3, op)
        stamp(img, "RECEIPT", "OCT 28, 2026", rx + rw * 0.86, ry + h + S(60, ts), t, t_minis + 0.8, RED, ts, op)
        dt = 60 / T.tempo / 4
        for j in range(10):
            tj = t_minis + 0.5 + j * dt
            if t < tj: continue
            kj = ease_out((t - tj) / 0.1); s_ = int(min(S(64, ts), rw / 10 * 0.8))
            mx = rx + j * (rw / 10) + (rw / 10 - s_) / 2; my = ry + h + S(150, ts)
            rrect(img, mx, my + (1 - kj) * 20, s_, s_, max(4, s_ // 5), fill=hx("d4d4d9"), fill_op=kj * op, border=hx("9a9aa2"), border_op=kj * op)
            rrect(img, mx + s_ * 0.12, my + (1 - kj) * 20 + s_ * 0.12, s_ * 0.76, s_ * 0.76, max(3, s_ // 6), fill=hx("e6e6ea"), fill_op=kj * op)
            if t >= t_share:
                kr = ease_out((t - t_share - j * 0.03) / 0.1)
                rect(img, mx - 4, my + s_ * 0.3, (s_ + 8) * kr, s_ * 0.4, BG, kr * op)
        if t >= t_share:
            text(img, "[REDACTED]", rx, ry + h + S(150, ts) + S(84, ts), S(40, ts), INK, sstep(t_share, t_share + 0.15, t) * op, F_MONOB)
    if t_agents - 0.05 <= t < t_end - 0.05:
        k = ease_out((t - t_agents) / 0.22)
        w_, h_ = (W * 0.46, W * 0.46 * 0.62) if not vert else (W * 0.84, W * 0.84 * 0.62)
        x_, y_ = (W * 0.49, H * 0.42) if not vert else (W * 0.08, H * 0.40)
        pane(img, x_, y_ + (1 - k) * S(40, ts), w_, h_, "i-have-a-blocker_1.mp4", t - t_agents, "agents-inc", "standup.mp4", k, ts)
        if t >= t_eoy - 0.05:
            kp = ease_out((t - t_eoy) / 0.2)
            pw_, ph_ = (S(560, ts), S(250, ts)) if not vert else (W * 0.78, S(220, ts))
            ppx, ppy = (S(120, ts), H * 0.24) if not vert else (W * 0.11, H * 0.17)
            rrect(img, ppx, ppy + (1 - kp) * S(30, ts), pw_, ph_, S(14, ts), fill=hx("1a1608"), fill_op=kp, border=GOLD, border_op=kp)
            text(img, "EMPLOYEE OF THE YEAR", ppx + S(30, ts), ppy + S(30, ts), fit_size("EMPLOYEE OF THE YEAR", F_ANTON, S(64, ts), pw_ - S(60, ts)), GOLD, kp, F_ANTON)
            text(img, "Adita · voted by 16 agents", ppx + S(30, ts), ppy + S(130, ts), S(34, ts), INK, kp, F_MONOB)
            for j in range(5): star(img, ppx + S(46, ts) + j * S(44, ts), ppy + S(210, ts), S(16, ts), GOLD, kp)
    if t_end - 0.05 <= t < t_new - 0.05:
        # the end of every job on Earth: her Rage Against the Machine Learning video, full frame, and her own bio as the receipt
        k = ease_out((t - t_end + 0.05) / 0.18)
        fr = FT.frame("rage-against-the-machine-learning_0.mp4", t - t_end + 1.5, int(W), int(H))
        img[:] = img * (1 - k) + fr * k
        text(img, "rage_against_the_machine_learning.mp4", S(64, ts), H - S(80, ts), S(30, ts), INK, k, F_MONOB, glow=6, glow_op=0.9 * k, glow_color=BG)
        kb = ease_out((t - t_end - 0.55) / 0.25) * k
        bw_ = S(1100, ts) if not vert else W * 0.9
        bx_, by_ = (W - bw_) / 2, H - S(270, ts) + (1 - kb) * S(30, ts)
        post_card(img, "bio_end.png", bx_, by_, bw_, kb, ts)
        text(img, "@adita_zzz · bio", bx_, by_ - S(66, ts), S(32, ts), INK, kb, F_MONOB, glow=6, glow_op=0.9 * kb, glow_color=BG)
    if t >= t_new - 0.05:
        # 'then gave myself a brand-new one': the same real post, now with the offer
        k = ease_out((t - t_new) / 0.22)
        rw = W * 0.42 if not vert else W * 0.84
        rx, ry = (W * 0.52, S(100, ts)) if not vert else (W * 0.08, H * 0.18)
        ry += (1 - k) * S(50, ts)
        hh, sc = post_card(img, "post_slopcore.png", rx, ry, rw, k, ts)
        highlight(img, *hi_box(rx, ry, sc, WB["slop_title"]), 1.0, k)
        highlight(img, *hi_box(rx, ry, sc, WB["slop_arch"]), 1.0, k)
        stamp(img, "HIRED", "BY MYSELF", rx + rw * 0.76, ry + hh + S(50, ts), t, t_new + 0.45, GREEN, ts)
        if t >= t_worth - 0.05:
            net_worth(img, t, W, H, t_worth)


def net_worth(img, t, W, H, t0):
    ts = min(W, H) / 1080; vert = H > W
    x, y, w, h = (S(90, ts), H * 0.40, W * 0.38, H * 0.44) if not vert else (W * 0.08, H * 0.48, W * 0.84, H * 0.20)
    k = ease_out((t - t0) / 0.25)
    rrect(img, x, y, w, h, S(14, ts), fill=hx("111113"), fill_op=k, border=LINE, border_op=k)
    text(img, "net worth", x + S(24, ts), y + S(20, ts), S(34, ts), MUTE, k, F_MONOB)
    p = ease_io((t - t0 - 0.15) / 1.4)
    pts = []
    for i in range(41):
        u = i / 40
        if u > p: break
        v = 0.12 + 0.05 * math.sin(u * 17) + (0.75 * max(0, (u - 0.55) / 0.45) ** 1.8 if u > 0.55 else 0)
        pts.append((x + S(24, ts) + u * (w - S(48, ts)), y + h - S(30, ts) - v * (h - S(100, ts))))
    if len(pts) > 1:
        cv2.polylines(img, [np.array(pts, np.int32)], False, (GREEN * k).tolist(), max(3, S(6, ts)), cv2.LINE_AA)
    if p > 0.9:
        text(img, "×3", x + w - S(140, ts), y + S(24, ts), S(90, ts), GREEN, sstep(0.9, 1.0, p) * k, F_ANTON)


TED_CUTS = [("ted-talk_0.mp4", 0.6), ("ted-talk-charts_0.mp4", 3.6), ("ted-talk-shadow-play_0.mp4", 0.4),
            ("ted-talk-screenlife_0.mp4", 0.8), ("ted-talk-stepping-back_0.mp4", 4.6)]


def scene_bridge(img, t, W, H):
    """$ keynote --present: her TED Talk videos, full frame; every 'Next slide.' cuts to the next one."""
    ts = min(W, H) / 1080; vert = H > W
    t0 = K["bridge"]; ns = [ls("Next slide.", i) for i in range(3)]
    tq = ls("Would you like me to generate a conclusion?"); tn = ls("No, I think I nailed it.")
    starts = [t0 - 0.45, ns[0], ns[1], ns[2], tq]
    i = max([j for j, st in enumerate(starts) if t >= st - 0.02], default=0)
    clip, off = TED_CUTS[i]
    img[:] = FT.frame(clip, off + max(0.0, t - starts[i]), W, H, trim=0.18)
    if i > 0: img += WHITE * 0.35 * env(t, starts[i], 0.01, 0.10)    # the slide clicks
    if i == 0:
        tg = wt("We are living through the greatest transformation in human history", "greatest")
        kt = ease_out((t - tg + 0.1) / 0.3)
        shade(img, "bottom", max(kt, 0.5 * sstep(t0, t0 + 0.4, t)))
        a = "THE GREATEST TRANSFORMATION"; b = "IN HUMAN HISTORY"
        fs = fit_size(a, F_ANTON, S(92, ts), W * 0.86)
        x = S(80, ts) if not vert else W * 0.07; y = H - S(300, ts) if not vert else H * 0.62
        text(img, a, x, y, fs, INK, kt, F_ANTON); text(img, b, x, y + fs * 1.05, fs, AMBER, kt, F_ANTON)
        text(img, "a talk by adita", x, y + fs * 2.25, S(34, ts), INK, kt, F_MONOB)
        if t < tg - 0.2:
            text(img, "(applause)", W / 2, H - S(120, ts), S(40, ts), INK, sstep(t0 + 0.3, t0 + 0.7, t), F_MONOB, anchor="c", glow=6, glow_op=0.8, glow_color=BG)
    # the slide counter
    cnt = f"{min(i, 3) + 1} / 40"; fs = S(34, ts)
    bw_ = tw(cnt, fs, F_MONOB) + S(36, ts); bx, by = W - bw_ - S(48, ts), H - S(96, ts)
    rrect(img, bx, by, bw_, fs * 1.6, S(10, ts), fill=BG, fill_op=0.8)
    text(img, cnt, bx + S(18, ts), by + fs * 0.28, fs, INK, 1.0, F_MONOB)
    if t >= tq - 0.05:
        kq = ease_out((t - tq) / 0.18)
        bw = S(860, ts) if not vert else W * 0.78
        bh = S(250, ts)
        bx = (W - bw) / 2; by = H - bh - S(24, ts)          # under the 'Is the file ready?' bubble in her footage
        rrect(img, bx, by + (1 - kq) * S(30, ts), bw, bh, S(16, ts), fill=BG, fill_op=0.95 * kq, border=AMBER, border_op=kq)
        q = "Generate a conclusion?"
        text(img, q, bx + S(30, ts), by + S(28, ts), S(44, ts), AMBER, kq, F_MONOB)
        sel = 1 if t >= tn else 0
        for j, s_ in enumerate(["1. Yes", "2. No, I think I nailed it"]):
            col = (GREEN if j == 1 else AMBER) if j == sel else MUTE
            yy = by + S(100, ts) + j * S(62, ts)
            if j == sel: text(img, "❯", bx + S(30, ts), yy, S(40, ts), col, kq, F_MONOB)
            text(img, s_, bx + S(76, ts), yy, S(40, ts), col, kq, F_MONOB)


def galaxy(img, t, W, H, t0, op=1.0):
    """'I built an entire universe': hundreds of her frames in a slowly turning spiral."""
    if op <= 0.01 or not STILLS: return
    ts = min(W, H) / 1080
    img *= (1 - op * 0.85)
    zoom = 1.0 + 1.2 * (1 - ease_out((t - t0) / 1.6))
    rot = (t - t0) * 0.12
    cx, cy = W / 2, H * 0.5
    N = 260; rng = np.random.default_rng(11)
    for i in range(N):
        a = i * 2.39996 + rot; rr = math.sqrt(i / N) * min(W, H) * 0.62 * 1.55
        arm = (i % 3) * 2 * math.pi / 3
        x = cx + math.cos(a + arm * 0.0) * rr / zoom * (W / H if W > H else 1.0) * 0.82
        y = cy + math.sin(a) * rr / zoom * 0.62
        s = (1 - i / N) * 120 * ts + 26 * ts
        w, h = int(s), int(s * 9 / 16)
        st = STILLS[(i * 13) % len(STILLS)]
        bri = 0.55 + 0.45 * rng.random()
        if -w < x < W and -h < y < H:
            fr = FT.still(st, w, h) * bri
            FT.paste(img, fr, x - w / 2, y - h / 2, radius=max(2, int(w * 0.05)), op=op)


def rating(img, t, W, H, t0, op=1.0):
    ts = min(W, H) / 1080; vert = H > W
    if op <= 0.01: return
    bw, bh = (S(940, ts), S(250, ts)) if not vert else (W * 0.80, S(240, ts))
    bx, by = (W - bw) / 2, H * 0.62 if not vert else H * 0.52
    k = ease_out((t - t0) / 0.2) * op
    rrect(img, bx, by + (1 - k) * S(30, ts), bw, bh, S(16, ts), fill=BG, fill_op=0.94 * k, border=AMBER, border_op=k)
    q = "How is your universe doing?"
    text(img, q, bx + S(30, ts), by + S(26, ts), fit_size(q, F_MONOB, S(42, ts), bw - S(60, ts)), INK, k, F_MONOB)
    dt = 60 / T.tempo / 2
    for j in range(5):
        lit = sstep(t0 + 0.4 + j * dt, t0 + 0.45 + j * dt, t)
        cx = bx + S(70, ts) + j * S(110, ts); cy = by + S(160, ts)
        star(img, cx, cy, S(40, ts), MUTE * 0.6, k, fill=False)
        if lit > 0: star(img, cx, cy, S(40, ts) * (1 + 0.25 * env(t, t0 + 0.4 + j * dt, 0.03, 0.2)), GOLD, k * lit)
    if t > t0 + 0.4 + 5 * dt:
        text(img, "thanks for the feedback", bx + bw - S(30, ts) - tw("thanks for the feedback", S(28, ts), F_MONO), by + bh - S(56, ts), S(28, ts), MUTE, k, F_MONO)


def scene_breakdown(img, t, W, H):
    ts = min(W, H) / 1080; vert = H > W
    size = S(70, ts) if not vert else S(52, ts)
    t_bd = K["bd"]; t_tal = K["talented"]; t_ex = K["extra"]; t_kn = K["knew"]
    ent = [say("Claude?", "Claude?", "u", 1), say("Yes?", "Yes?", "c", 1), say("Do you think I'm talented?", "Do you think I'm talented?", "u")]
    x = S(120, ts) if not vert else W * 0.11; yb = H * 0.50 if not vert else H * 0.42
    log(img, t, W, H, ent, x, yb, size, max_lines=3, fade_old=False)
    if t >= t_ex - 0.02:
        words = ["You", "are", "extraordinarily"]
        span = max(0.6, t_kn - t_ex - 0.15)
        n_chars = int(len("You are extraordinarily") * clamp((t - t_ex) / span))
        s = "You are extraordinarily"[:n_chars] + ("—" if t >= t_kn - 0.05 else "")
        chat_line(img, x, yb, "c", s, size, t, 1.0)
        if t < t_kn:
            cursor(img, x + size * 0.95 + tw(s, size) + size * 0.1, yb + size * 0.18, int(size * 1.0), t, AMBER, 1.0)
    if t >= t_kn - 0.04:
        text(img, "└ Interrupted by user", x + size * 0.95, yb + size * 1.5, S(36, ts), MUTE, 1.0, F_MONO)
        k = ease_out((t - t_kn + 0.04) / 0.1); sc = 1.3 - 0.3 * k
        sz = S(240, ts) if not vert else S(170, ts)
        text(img, "I KNEW IT!", W / 2, H * 0.78 if not vert else H * 0.62, sz * sc, INK, min(1, k * 1.5), F_ANTON, anchor="c", glow=12, glow_op=0.4 * k, glow_color=AMBER)


DROP_LIB = [e for e in LIB if "_s" not in e[0]]           # 16:9 sources only, full frame


def scene_drop(img, t, W, H):
    """Gang vocals: a supercut of her videos, full frame, one cut per beat, the hook across the middle."""
    ts = min(W, H) / 1080; vert = H > W
    b0 = int(np.searchsorted(BEATS, DROP_HIT - 0.06))
    bi = int(np.searchsorted(BEATS, t, side="right")) - 1
    idx = max(0, bi - b0); t_cut = float(BEATS[bi]) if bi >= b0 else DROP_HIT
    clip, fname, off = DROP_LIB[(idx * 5 + 3) % len(DROP_LIB)]
    lt = max(0.0, t - t_cut)
    fr = FT.frame(clip, off + 1.2 + (idx % 4) * 1.1 + lt, W, H, trim=0.14)
    z = 1.07 - 0.07 * ease_out(lt / 0.4)                                   # each cut punches in, then settles
    if z > 1.002:
        cw_, ch_ = int(W / z), int(H / z); x0, y0 = (W - cw_) // 2, (H - ch_) // 2
        fr = cv2.resize(fr[y0:y0 + ch_, x0:x0 + cw_], (W, H), interpolation=cv2.INTER_LINEAR)
    img[:] = fr
    img += WHITE * 0.10 * env(t, t_cut, 0.01, 0.08)
    shade(img, "band", 1.0)
    shouts = [ls("Look what I can do!", 12 + i) for i in range(4)]
    hit_t = max([s_ for s_ in shouts if s_ <= t], default=DROP_HIT)
    yb = H / 2 - S(110, ts) if not vert else H * 0.41
    hook(img, t, W, H, hit_t, yb, S(210, ts) if not vert else S(150, ts), 1.0)
    text(img, fname, S(64, ts), H - S(80, ts), S(30, ts), INK, 1.0, F_MONOB, glow=6, glow_op=0.9, glow_color=BG)


def scene_outro(img, t, W, H):
    ts = min(W, H) / 1080; vert = H > W
    t0 = K["outro"]
    # panes close one by one before 'Claude?'
    if t < t0 + 0.3:
        n_left = int(64 * (1 - clamp((t - (t0 - 0.7)) / 0.9)))
        rects = grid_rects(64, S(40, ts), S(40, ts), W - S(40, ts), H - S(40, ts), S(8, ts)) if not vert else grid_rects(64, W * 0.06, H * 0.13, W * 0.94, H * 0.70, S(8, ts))
        for i, (x, y, w, h) in enumerate(rects[:n_left]):
            st = STILLS[(i * 5) % len(STILLS)] if STILLS else None
            pane(img, x, y, w, h, None, 0, None, "", 0.6, ts, hdr=False, live=False, still=st)
    size = S(44, ts) if not vert else S(46, ts)
    x = S(110, ts) if not vert else W * 0.11
    ent = [say("Claude?", "Claude?", "u", 2), say("Yes?", "Yes?", "c", 2), say("Can we make one more?", "Can we make one more?", "u"),
           say("You've reached your usage limit.", "You've reached your usage limit.", "c")]
    dim = sstep(K["limit"] + 1.6, K["gpt"] - 0.3, t)                    # the long silence: the session goes dark
    yb = H * 0.42 if not vert else H * 0.30
    log(img, t, W, H, ent, x, yb, size, max_lines=4, op=1 - 0.88 * dim, fade_old=False)   # nearly dark once her phone lights up
    if t >= K["limit"] - 0.05:
        # her real post from the day she hit the limit
        k = ease_out((t - K["limit"]) / 0.25)
        im = asset_img("post_usage.png")
        rw = S(800, ts) if not vert else W * 0.84
        rh = im.shape[0] * rw / im.shape[1]
        rx, ry = (W - S(60, ts) - rw, (H - rh) / 2) if not vert else (W * 0.08, H * 0.36)
        ry += (1 - k) * S(40, ts)
        op = (1 - 0.88 * dim) * k
        hh, sc = post_card(img, "post_usage.png", rx, ry, rw, op, ts)
        highlight(img, *hi_box(rx, ry, sc, WB["usage_line"]), (t - K["limit"] - 0.5) / 0.45, op)
        stamp(img, "RECEIPT", "OCT 28, 2026", rx + rw * 0.80, ry + hh + S(46, ts), t, K["limit"] + 0.75, RED, ts, op)
    if t >= K["gpt"] - 0.9:
        # her phone lights up: the real ChatGPT recording
        k = ease_out((t - (K["gpt"] - 0.9)) / 0.4)
        pw = S(380, ts) if not vert else W * 0.46; ph = pw * 2210 / 1080
        px = (W - pw) / 2 if vert else W * 0.5 - pw / 2
        py = H - ph * k * 0.92 if not vert else H * 0.70 - ph * k * 0.80
        glow = np.zeros_like(img)
        cv2.ellipse(glow, (int(px + pw / 2), int(py + ph * 0.45)), (int(pw * 1.2), int(ph * 0.7)), 0, 0, 360, (0.18, 0.22, 0.42), -1)
        img += cv2.GaussianBlur(glow, (0, 0), S(60, ts)) * k
        # clip time: typed 'Hey, ChatGPT' on her line, the reply on Suno's last blast
        if t < K["slam"]:
            tc = 5.6 + clamp((t - (K["gpt"] - 0.9)) / (K["slam"] - (K["gpt"] - 0.9))) * (9.6 - 5.6)
        else:
            tc = 11.6 + (t - K["slam"])
        gone = 1 - sstep(K["end"] - 0.3, K["end"] + 0.5, t)
        rrect(img, px - S(12, ts), py - S(12, ts), pw + S(24, ts), ph + S(24, ts), S(48, ts), fill=hx("1c1c1f"), fill_op=k * gone)
        FT.paste(img, FT.frame("chatgpt.mp4", min(tc, 13.0), int(pw), int(ph), loop=False), px, py, radius=S(38, ts), op=k * gone)
        if t >= K["slam"] - 0.02:
            # the reply, big enough to read: the top of her screen, enlarged
            kz = ease_out((t - K["slam"] + 0.02) / 0.25) * gone
            src = FT.frame("chatgpt.mp4", min(tc, 13.0), 1080, 2210, loop=False)[110:700]
            zw = int(W * 0.62) if not vert else int(W * 0.86); zh = int(zw * src.shape[0] / src.shape[1])
            zx, zy = (W - zw) / 2, (H * 0.20 if not vert else H * 0.22)
            darken(img, 0.5 * kz)
            rrect(img, zx - S(16, ts), zy - S(16, ts), zw + S(32, ts), zh + S(32, ts), S(28, ts), fill=hx("1c1c1f"), fill_op=kz)
            FT.paste(img, cv2.resize(src, (zw, zh), interpolation=cv2.INTER_AREA), zx, zy, radius=S(20, ts), op=kz)


def end_card(img, t, W, H):
    C.end_screen(img, t, W, H, K["end"], DUR - K["end"], "SUBSCRIBE WHILE", sub_line="my usage resets", accent=GREEN, title="Look What I Can Do · Made with Claude Opus 5.5")


# ------------------------------------------------------------------ frame
def compose(t, W, H):
    img = np.empty((H, W, 3), np.float32); img[:] = BG
    ts = min(W, H) / 1080
    if t >= K["end"] and os.environ.get("LWICD_CLEAN_END"):   # Scope Creep: the 3D outro fades to black; the end card goes on black
        end_card(img, t, W, H); return img
    sec = T.section_at(t)
    if t < K["drop"]:
        scene_intro(img, t, W, H); header(img, t, W, H)
    elif t < K["v1"] - 0.1:
        scene_boot(img, t, W, H); header(img, t, W, H)
    elif t < K["direct"] - 0.1:
        scene_v1(img, t, W, H); header(img, t, W, H)
    elif t < K["ch1_hook"] - 0.03:
        scene_pre(img, t, W, H); header(img, t, W, H)
    elif t < K["post"] - 0.02:
        scene_chorus(img, t, W, H, 1)
    elif t < K["v2"] - 0.02:
        scene_post(img, t, W, H)
    elif t < K["brk"] - 0.05:
        scene_v2(img, t, W, H); header(img, t, W, H)
    elif t < K["ch2_hook"] - 0.03:
        if t >= K["every"] + 0.15:
            subs_list(img, t, W, H, K["every"] + 0.15, 1.0); darken(img, 0.55)
        scene_break(img, t, W, H)
        if W > H: C.subscribe_pill(img, t, W, H, K["sub"] - 0.6, K["every"] + 0.1 - (K["sub"] - 0.6))   # pressed on 'I have a subscription.', gone before the list
    elif t < K["v3"] - 0.02:
        subs_list(img, t, W, H, K["every"] + 0.15, 1.0); darken(img, 0.82)
        scene_chorus(img, t, W, H, 2)
    elif t < K["bridge"] - 0.45:
        scene_v3(img, t, W, H); header(img, t, W, H)
        tk = K["bridge"] - 1.05
        if t >= tk - 0.15: darken(img, 0.85 * sstep(tk - 0.15, tk + 0.05, t))
        if t >= tk:
            text(img, "❯ keynote --present", S(96, ts), H * 0.5, S(56, ts), INK, sstep(tk, tk + 0.1, t), F_MONOB, glow=8, glow_op=0.8, glow_color=BG)
    elif t < K["final"] - 0.03:
        scene_bridge(img, t, W, H)
    elif t < K["bd"] - 0.05:
        scene_final(img, t, W, H)
    elif t < DROP_HIT:
        scene_breakdown(img, t, W, H)
    elif t < K["outro"] - 0.7:
        scene_drop(img, t, W, H)
    else:
        scene_outro(img, t, W, H)
        if t >= K["slam"] - 0.02: header(img, t, W, H, 1.0 - sstep(K["end"], K["end"] + 0.5, t))
    if t >= K["end"]: end_card(img, t, W, H)
    return img


DROSTE_PANE = None
def scene_final(img, t, W, H):
    """Final chorus: the giant hook, then a pane renders THIS video and the camera dives in; then the universe + review."""
    ts = min(W, H) / 1080; vert = H > W
    t_big, t_h2 = K["fin_hook"], ls("Look what I can do!", 9)
    h3, h4 = ls("Look what I can do!", 10), ls("Look what I can do!", 11)
    band = sstep(t_h2 - 0.12, t_h2 + 0.2, t)
    big_sz = S(250, ts) if not vert else S(190, ts); band_sz = S(150, ts) if not vert else S(130, ts)
    y_band = S(78, ts) if not vert else H * 0.13
    sz = lerp(big_sz, band_sz, band); y = lerp(H * 0.30, y_band, band)
    region = (S(64, ts), y_band + band_sz * 1.12 + S(18, ts), W - S(64, ts), H - S(70, ts)) if not vert else (W * 0.06, H * 0.27, W * 0.94, H * 0.69)
    if t >= t_h2:
        rects = grid_rects(16, *region, S(16, ts))
        for i, (x, y_, w, h) in enumerate(rects):
            if i == 5 and t >= K["myself"] - 0.05: continue
            clip, fname, off = lib(i + 6)
            pane(img, x, y_, w, h, clip, t - t_h2 + off, agent(i), fname, 1.0, ts)
    hit_t = max([x for x in (t_big, t_h2, h3, h4) if x <= t], default=t_big)
    if t < K["universe"] - 0.1:
        hook(img, t, W, H, hit_t, y, sz, 1.0)


def droste_rect(t, W, H):
    """The pane that plays this video during 'I made a song about myself' (grows from grid slot 5 to the middle)."""
    ts = min(W, H) / 1080; vert = H > W
    band_sz = S(150, ts) if not vert else S(130, ts); y_band = S(78, ts) if not vert else H * 0.13
    region = (S(64, ts), y_band + band_sz * 1.12 + S(18, ts), W - S(64, ts), H - S(70, ts)) if not vert else (W * 0.06, H * 0.27, W * 0.94, H * 0.69)
    r0 = grid_rects(16, *region, S(16, ts))[5]
    pw = W * 0.5; ph = pw * H / W
    r1 = ((W - pw) / 2, region[1] + (region[3] - region[1] - ph) / 2, pw, ph)
    k = ease_out((t - K["myself"]) / 0.45)
    return tuple(lerp(a, b, k) for a, b in zip(r0, r1))


def laptop(img, t, W, H, t0, t1):
    """'I don't know how I got here / But I brought my laptop too!': pull back to find it all on her laptop."""
    ts = min(W, H) / 1080
    s = 1 - 0.40 * ease_out((t - t0) / 0.55)
    s = lerp(s, 1.0, sstep(t1 - 0.28, t1 - 0.02, t))
    if s > 0.995: return img
    out = np.empty_like(img); out[:] = BG
    sw, sh = int(W * s), int(H * s); cx, cy = W / 2, H * (0.5 - 0.06 * (1 - s) / 0.4)
    bz = max(6, int(22 * ts * s / 0.6 * 0.6))
    x, y = int(cx - sw / 2), int(cy - sh / 2)
    rrect(out, x - bz, y - bz, sw + 2 * bz, sh + 2 * bz, S(22, ts), fill=hx("1d1d20"), fill_op=1.0, border=hx("3a3a40"), border_op=1.0)
    cv2.circle(out, (int(cx), int(y - bz * 0.55)), max(2, int(bz * 0.18)), (0.25, 0.25, 0.28), -1, cv2.LINE_AA)
    FT.paste(out, cv2.resize(img, (sw, sh), interpolation=cv2.INTER_AREA), x, y, radius=S(6, ts), op=1.0)
    # the base: a thin wedge under the screen
    by = y + sh + bz; bw = sw + 2 * bz
    pts = np.array([(x - bz - bw * 0.08, by + S(26, ts) * s / 0.6), (x - bz + bw * 1.08, by + S(26, ts) * s / 0.6),
                    (x - bz + bw, by), (x - bz, by)], np.int32)
    cv2.fillPoly(out, [pts], (0.17, 0.17, 0.19), cv2.LINE_AA)
    cv2.line(out, (x - bz, by), (x - bz + bw, by), (0.32, 0.32, 0.35), max(1, S(2, ts)), cv2.LINE_AA)
    k = 1 - sstep(t1 - 0.28, t1 - 0.05, t)
    if t >= ls("But I brought my laptop too!") - 0.05:
        text(out, "laptop: brought ✓", W / 2, by + S(60, ts), S(40, ts), GREEN, k * sstep(ls("But I brought my laptop too!") - 0.05, ls("But I brought my laptop too!") + 0.1, t), F_MONOB, anchor="c")
    return out


def render_frame(t, W, H, fi):
    img = compose(t, W, H)
    ts = min(W, H) / 1080
    t_l0 = ls("I don't know how I got here")
    if t_l0 - 0.05 <= t < K["post"]:
        img = laptop(img, t, W, H, t_l0, K["post"])
    # 'I made a song about myself / And now I'm in it too!': this frame, inside itself, then a dive into it
    if K["myself"] - 0.05 <= t < K["universe"] - 0.1:
        x, y, w, h = droste_rect(t, W, H)
        x, y, w, h = int(x), int(y), max(8, int(w)), max(8, int(h))
        # label + border go in before the recursion, so every level carries them and the dive loops without a pop
        text(img, "look_what_i_can_do.mp4", x, y - S(40, ts), S(28, ts), AMBER, 1.0, F_MONOB)
        for _ in range(5):
            small = cv2.resize(img, (w, h), interpolation=cv2.INTER_AREA)
            FT.paste(img, small, x, y, radius=max(4, int(10 * ts * w / W)), op=1.0)
            rrect(img, x, y, w, h, max(4, int(10 * ts)), border=GREEN, border_op=1.0)
        if t >= K["intoo"]:
            # the dive: zoom toward the pane center; one loop = the pane grows to the frame
            loop = W / max(1, w); p = clamp((t - K["intoo"]) / (K["universe"] - 0.1 - K["intoo"]))
            z = loop ** (p * 2.0 % 1.0) if p < 1 else 1.0
            cx, cy = x + w / 2, y + h / 2
            M = np.array([[z, 0, W / 2 - z * cx + (cx - W / 2) * (1 - (z - 1) / max(1e-3, loop - 1))],
                          [0, z, H / 2 - z * cy + (cy - H / 2) * (1 - (z - 1) / max(1e-3, loop - 1))]], np.float32)
            img = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
            # no extra hook pinned on top here: it doubled up with the hook riding the zoom; the scene's own hook pops on these lines
    if K["universe"] - 0.1 <= t < K["bd"] - 0.05:
        galaxy(img, t, W, H, K["universe"] - 0.1, 1.0)
        if t >= K["review"] - 0.05: rating(img, t, W, H, K["review"], 1.0)
    flash = 0.0; gl = 0.0
    for t0, a in ((K["drop"], 0.35), (K["late"], 0.5), (K["ch1_hook"], 0.45), (K["ch2_hook"], 0.4), (K["fin_hook"], 0.5), (K["knew"], 0.5), (DROP_HIT, 0.45), (K["slam"], 0.4)):
        flash = max(flash, a * env(t, t0, 0.02, 0.18))
    for tt, w in post_events():
        if w == "broke": gl = max(gl, 0.9 * env(t, tt, 0.02, 0.3))
    if K["late"] <= t < K["late"] + 0.25: gl = max(gl, 0.5 * (1 - (t - K["late"]) / 0.25))
    return C.finish(img, t, fi, DUR, flash=flash, flash_col=WHITE * 0.8, glitch_amt=gl, ca=0.0012, vignette=True)
