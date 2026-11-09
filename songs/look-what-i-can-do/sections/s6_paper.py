"""S6 · verse 3 (100.00-122.94 s, frames 3000-3687): "The Daily Standup", the newspaper of her video TED Talk (Charts).

The same issue keeps printing, now about her: a new figure every couplet, black ink on cream paper, one red, the blue
ballpoint in the margins, a CORRECTION, and at the end somebody dims the lights (a keynote is coming).
  FIG. 20  her two real posts ("Anyway, I'm back" / "...grow our tomatoes. voluntarily.") + humanity's outlook chart
  FIG. 21  a bot's summary of the panic in the room (it includes you)
  FIG. 22  her real "10 Mac minis. For personal reasons." post, a stack of ten minis, the share of reasons: REDACTED
  FIG. 23  Agents, Inc.: the agents swarm into an org chart; she is the only employee (of the year)
  FIG. 24  jobs on Earth before and after her song -> 0; CORRECTION: one job left, hers (HIRED BY MYSELF)
  FIG. 25  her net worth, tripled: $0 x 3 = $0 (growth +200%, checks out)
"""
import os, sys, glob, math
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__))
SONG = os.path.dirname(HERE); ROOT = os.path.dirname(os.path.dirname(SONG))
for p in (ROOT, HERE):
    if p not in sys.path: sys.path.insert(0, p)
from studio import core as C
from studio.core import sstep, ease_out, ease_io, clamp, lerp, hexc
from s6_ink import *          # noqa: F401,F403  (the Daily Standup kit)
import s6_ink as K

TM = C.Timing(SONG)
ASSETS = os.path.join(ROOT, "music", "Look What I Can Do", "assets")
HD = os.path.join(ROOT, "music", "Look What I Can Do", "hd")
T0, T1 = 100.0, 3688 / 30.0

def wt(sub, word, fb, nth=0):
    try: return TM.word_t(sub, word, nth)
    except Exception: return fb
def lt(sub, fb, nth=0):
    try: return TM.line_t(sub, nth)
    except Exception: return fb

# ---------------------------------------------------------------- key times (word level)
T_SO = wt("We are so back", "so", 100.98); T_BACK = wt("We are so back", "back", 101.36)
T_POST2 = wt("We are doomed", "posted", 101.84); T_DOOM = wt("We are doomed", "doomed", 103.06)
T_ASKED = wt("asked a bot", "asked", 103.70); T_SUMM = wt("asked a bot", "summarize", 104.54)
T_PANIC = wt("panic in the room", "panic", 105.44); T_ROOM = wt("panic in the room", "room", 106.78)
T_TEN = wt("Mac minis", "ten", 107.56); T_MAC = wt("Mac minis", "Mac", 108.40); T_MINIS = wt("Mac minis", "minis", 108.68)
T_FOR = lt("For reasons", 109.14); T_REASONS = wt("For reasons", "reasons", 109.60); T_CANT = wt("For reasons", "can't", 110.26)
T_AGENTS = wt("agents formed", "agents", 110.98); T_FORMED = wt("agents formed", "formed", 111.34); T_COMPANY = wt("agents formed", "company", 111.84)
T_MADE = wt("Employee of the Year", "made", 112.76); T_ME = wt("Employee of the Year", "me", 112.98)
T_EMPL = wt("Employee of the Year", "Employee", 113.14); T_YEAR = wt("Employee of the Year", "Year", 114.10)
T_SONG = wt("song about the end", "song", 115.02); T_END = wt("song about the end", "end", 115.98); T_EARTH = wt("every job on Earth", "Earth", 117.78)
T_GAVE0 = lt("gave myself", 117.99); T_GAVE = wt("gave myself", "gave", 118.20); T_MYSELF = wt("gave myself", "myself", 118.42)
T_BRAND = wt("gave myself", "brand-new", 119.10)
T_TRIPLED = wt("tripled my net", "tripled", 120.00); T_MY = wt("tripled my net", "my", 120.36); T_NET = wt("tripled my net", "net", 120.84)
T_WORTH = wt("tripled my net", "worth", 121.24)
T_DIM = 122.26                                     # somebody dims the lights: "Ladies and gentlemen" (122.94) is a keynote

# ---------------------------------------------------------------- her real posts (word boxes from web/BRIEF.md)
def _img(n): return K.load(os.path.join(ASSETS, n))
P_BACK = "post_back.png"; P_TOM = "post_tomatoes.png"; P_MINIS = "post_minis.png"
BOX_BACK = [(796, 535, 1167, 596), (246, 617, 376, 668)]
BOX_TOM = (246, 280, 595, 343)
BOX_MINIS = [(974, 117, 1193, 166), (249, 201, 426, 250), (447, 201, 1105, 263)]

_AV = {}
def avatar():
    """her X avatar (the round photo on her posts), as a disc"""
    if "a" not in _AV:
        im = _img(P_TOM)
        if im is None: _AV["a"] = (None, None)
        else:
            cx, cy, r = 124, 115, 97
            crop = np.ascontiguousarray(im[cy - r:cy + r, cx - r:cx + r])
            m = np.zeros(crop.shape[:2], np.uint8); cv2.circle(m, (r * 4, r * 4), (r - 1) * 4, 255, -1, cv2.LINE_AA, shift=2)
            _AV["a"] = (crop, m.astype(np.float32) / 255)
    return _AV["a"]

# ---------------------------------------------------------------- her footage (Asking for a Friend), in clean single shots
# Each hd clip is a 6 s montage; these are the frame ranges of single shots inside them (found by cut detection):
#   aff_robot_memo 36-98: the Claude robot (spiky ivory hair) at his desk, "OWNER: nobody" on the wall  -> the CEO's headshot
#   aff_porsche_side 68-118: her friend's Ultraviolet GT3 RS side-on, yellow calipers, desert road  -> "assets" (not hers)
# (shot = clip, first frame, last frame, optional crop x, y, w, h in source pixels)
SHOT_CEO = ("aff_robot_memo.mp4", 37, 97, (360, 80, 920, 517))
SHOT_CAR = ("aff_porsche_side.mp4", 69, 117, None)
def _has(shot): return os.path.exists(os.path.join(HD, shot[0]))
_SEG = {}
def _segment(shot, pw, ph):
    """decode a shot once at its on-screen pixel size (cover fit), cached; None if the clip is missing"""
    k = (shot, pw, ph)
    if k not in _SEG:
        path = os.path.join(HD, shot[0]); a, b = shot[1], shot[2]; cr = shot[3] if len(shot) > 3 else None
        arr = None
        if os.path.exists(path):
            import subprocess
            vf = (f"trim=start_frame={a}:end_frame={b + 1},setpts=PTS-STARTPTS,"
                  + (f"crop={cr[2]}:{cr[3]}:{cr[0]}:{cr[1]}," if cr else "") +
                  f"scale={pw}:{ph}:force_original_aspect_ratio=increase:flags=bicubic,crop={pw}:{ph}")
            raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-an", "-vf", vf, "-vsync", "0", "-f", "rawvideo",
                                  "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
            n = len(raw) // (pw * ph * 3)
            if n > 0: arr = np.frombuffer(raw[:n * pw * ph * 3], np.uint8).reshape(n, ph, pw, 3)
        if len(_SEG) > 8: _SEG.clear()
        _SEG[k] = arr
    return _SEG[k]

def shot_frame(cv, shot, u, w, h):
    """the shot at progress u (0..1, clamped), blended between neighbouring frames so slow playback stays smooth"""
    pw, ph = max(2, int(round(cv.L(w)))), max(2, int(round(cv.L(h))))
    seg = _segment(shot, pw, ph)
    if seg is None: return None
    f = clamp(u) * (len(seg) - 1); i = int(f); fr = f - i; j = min(len(seg) - 1, i + 1)
    a = seg[i].astype(np.float32) / 255
    if fr > 1e-3: a = a * (1 - fr) + seg[j].astype(np.float32) * (fr / 255)
    return a

def photo(cv, shot, u, x, y, w, h, op=1.0, pad=10, fallback=None, base=None):
    """a news photo: card mat, the footage, a hairline, a soft shadow (base: decode size while the photo scales)"""
    rect(cv, x - pad + 9, y - pad + 11, w + 2 * pad, h + 2 * pad, INK, 0.10 * op, r=10)
    rect(cv, x - pad, y - pad, w + 2 * pad, h + 2 * pad, CARD, op, r=10)
    fr = shot_frame(cv, shot, u, *(base or (w, h)))
    if fr is not None: paste(cv, ("shot", shot[0]), fr, x, y, w, h, op, cache=False)
    elif fallback: fallback()
    rect(cv, x - pad, y - pad, w + 2 * pad, h + 2 * pad, INK, op, r=10, wd=2)

# ---------------------------------------------------------------- the newspaper furniture
CLOCK = [(119.6, "4:15 P.M."), (114.2, "4:14 P.M."), (110.5, "4:09 P.M."), (107.0, "4:06 P.M."), (103.5, "4:02 P.M.")]
def masthead(cv, t):
    clk = "4:01 P.M."
    for tt, lab in CLOCK:
        if t >= tt: clk = lab; break
    text(cv, "THE DAILY STANDUP", 960, 66, F_MAST, 74, INK, 1.0, 'c', 'm', track=3)
    stroke(cv, [(120, 112), (1800, 112)], INK, 2.2); stroke(cv, [(120, 119), (1800, 119)], INK, 1.0)
    text(cv, "THURSDAY, OCT. 30", 120, 146, F_SANSM, 30, INK2, 1.0, 'l', 'm', track=2)
    text(cv, clk, 960, 146, F_MONO, 32, RED, 1.0, 'c', 'm')
    text(cv, "PRICE: 1 SUBSCRIPTION", 1800, 146, F_SANSM, 30, INK2, 1.0, 'r', 'm', track=2)
    stroke(cv, [(120, 172), (1800, 172)], INK, 1.4)

def frame(cv, kicker, title, source=None):
    """figure furniture (as in TED Talk (Charts)): red kicker, serif headline, hairline; returns the chart area"""
    x, y, w, h = cv.box
    text(cv, kicker, x, y + 22, F_SANS, 32, RED, 1.0, 'l', 'm', track=3)
    ts = fit(title, F_HEAD, 60, w, 40)
    text(cv, title, x, y + 80, F_HEAD, ts, INK, 1.0, 'l', 'm')
    yr = y + 80 + ts * 0.7
    stroke(cv, [(x, yr), (x + w, yr)], RULE, 1.6)
    if source: text(cv, source, x, y + h - 14, F_SANSM, 30, MUTE, 1.0, 'l', 'm')
    top = yr + 28; bot = y + h - (54 if source else 20)
    return (x, top, w, bot - top)

def axes(cv, x, y, w, h, xt, yt, ylab=None, xlab=None, grid=True):
    for f, lab in yt:
        yy = y + h - f * h
        if grid and f > 0: stroke(cv, [(x, yy), (x + w, yy)], GRID, 1.4)
        text(cv, lab, x - 16, yy, F_SANSM, 34, MUTE, 1.0, 'r', 'm')
    stroke(cv, [(x, y + h), (x + w, y + h)], INK, 2.2)
    for f, lab in xt:
        xx = x + f * w; stroke(cv, [(xx, y + h), (xx, y + h + 10)], INK, 2.0)
        text(cv, lab, xx, y + h + 36, F_SANSM, 34, MUTE, 1.0, 'c', 'm')
    if ylab: text(cv, ylab, x, y - 28, F_SANS, 34, INK2, 1.0, 'l', 'm')
    if xlab: text(cv, xlab, x + w, y + h + 78, F_SANSM, 32, MUTE, 1.0, 'r', 'm')

def tile(cv, x, y, w, h, op=1.0):
    rect(cv, x, y, w, h, CARD, op, r=14); rect(cv, x, y, w, h, INK, op, r=14, wd=2)

def typed_rows(rows, n):
    """the first n characters of a wrapped paragraph, row by row"""
    out = []
    for r in rows:
        if n <= 0: break
        out.append(r[:n]); n -= len(r) + 1
    return out

# ================================================================ FIG. 20: the two posts
def fig_posts(cv, t):
    cx_, cy_, cw, ch = frame(cv, "FIG. 20", "Humanity's outlook, according to my last two posts", "Source: @adita_zzz on X")
    s = 0.76; px, py = 184, cy_ + 16
    kb1 = sstep(T_SO - 0.06, T_SO + 0.22, t); kb2 = sstep(T_BACK - 0.12, T_BACK + 0.10, t)
    clipping(cv, P_BACK, _img(P_BACK), px, py, s, 1.0,
             marks=[BOX_BACK[0] + (kb1,), BOX_BACK[1] + (kb2,)])
    # the second post lands on top of the first (the newest clipping on the pile), leaving "Anyway, I'm back" in view
    kl = ease_out((t - (T_POST2 - 0.02)) / 0.20)
    if kl > 0:
        kv = sstep(T_DOOM - 0.08, T_DOOM + 0.16, t)
        clipping(cv, P_TOM, _img(P_TOM), px + 64, py + 12 - 40 * (1 - kl), s, min(1.0, kl * 3), marks=[BOX_TOM + (kv,)])
    # outlook chart (right column)
    ax = 1500; ytop, ymid, ybot = cy_ + 70, cy_ + 290, cy_ + 510
    for yy, lab, col in ((ytop, "so back", INK), (ymid, "meh", MUTE), (ybot, "doomed", RED)):
        stroke(cv, [(ax, yy), (1750, yy)], GRID, 1.4)
        text(cv, lab, ax - 18, yy, F_SANS, 46, col, 1.0, 'r', 'm')
    stroke(cv, [(ax, ytop - 30), (ax, ybot + 24)], INK, 2.2)
    text(cv, "OUTLOOK", ax - 18, ytop - 62, F_SANS, 30, MUTE, 1.0, 'r', 'm', track=3)
    p0 = (ax, ymid); p1 = (1590, ytop); p2 = (1718, ybot)
    for xx, lab in ((p1[0], "post 1"), (p2[0], "post 2")):
        text(cv, lab, xx, ybot + 58, F_SANSM, 32, MUTE, 1.0, 'c', 'm')
    k1 = ease_out((t - (T_SO - 0.08)) / 0.30)
    k2 = clamp((t - (T_DOOM - 0.10)) / 0.26) ** 1.6
    circle(cv, p0[0], p0[1], 9, INK2)
    if k1 > 0:
        e = (lerp(p0[0], p1[0], k1), lerp(p0[1], p1[1], k1))
        stroke(cv, [p0, e], INK, 5)
    if k1 > 0.98 and k2 <= 0:
        pop = 1 + 0.5 * math.exp(-(t - T_SO - 0.22) * 9) if t > T_SO + 0.22 else 1.0
        circle(cv, p1[0], p1[1], 13 * pop, PEN); circle(cv, p1[0], p1[1], 24, PEN, 0.5, wd=2.5)
    if k2 > 0:
        e = (lerp(p1[0], p2[0], k2), lerp(p1[1], p2[1], k2))
        stroke(cv, [p1, e], RED, 5)
        circle(cv, p1[0], p1[1], 9, INK)
        circle(cv, e[0], e[1], 13, RED)
        if k2 >= 1: circle(cv, p2[0], p2[1], 25 + 6 * math.exp(-(t - T_DOOM - 0.16) * 7), RED, 0.6, wd=2.5)

# ================================================================ FIG. 21: the bot's summary of the panic
ROOM = [(c, r) for r in range(3) for c in range(5)]          # (col, row); the last one is you
def fig_summary(cv, t):
    cx_, cy_, cw, ch = frame(cv, "FIG. 21", "The panic in the room, summarized by a bot", "Source: a bot")
    bx, by, bw, bh = 184, cy_ + 40, 860, 470
    rect(cv, bx + 10, by + 12, bw, bh, INK, 0.10, r=18)
    tile(cv, bx, by, bw, bh)
    # header: a sparkle + SUMMARY, the source
    sx, sy = bx + 58, by + 58; r1, r2 = 15, 4.5
    fill(cv, [(sx + (r1 if i % 2 == 0 else r2) * math.cos(-math.pi / 2 + i * math.pi / 4),
               sy + (r1 if i % 2 == 0 else r2) * math.sin(-math.pi / 2 + i * math.pi / 4)) for i in range(8)], RED)
    text(cv, "SUMMARY", sx + 30, sy, F_SANS, 32, RED, 1.0, 'l', 'm', track=3)
    text(cv, "1 source: the room", bx + bw - 44, sy, F_SANSM, 30, MUTE, 1.0, 'r', 'm')
    stroke(cv, [(bx + 44, by + 104), (bx + bw - 44, by + 104)], RULE, 1.6)
    fs = 64; lh = fs * 1.12
    rows = wrap("Everyone in the room is panicking.", F_HEAD, fs, bw - 100)
    n = int(len(" ".join(rows)) * clamp((t - (T_SUMM - 0.05)) / 0.85))
    vis = typed_rows(rows, n); y0 = by + 178
    for i, r in enumerate(vis): text(cv, r, bx + 50, y0 + i * lh, F_HEAD, fs, INK, 1.0, 'l', 'm')
    t3a, t3b = T_ROOM - 0.62, T_ROOM - 0.18
    s3 = "This includes you."
    n3 = int(len(s3) * clamp((t - t3a) / (t3b - t3a)))
    y3 = y0 + len(rows) * lh + 34
    if n3 > 0: text(cv, s3[:n3], bx + 50, y3, F_HEAD, fs, RED, 1.0, 'l', 'm')
    # the bot's cursor while it types
    typing = (T_SUMM - 0.05 < t < T_SUMM + 0.95) or (t3a < t < t3b + 0.5)
    if (T_SUMM - 0.25 < t < t3b + 0.6) and (typing or int(t * 3.2) % 2 == 0):
        if t < t3a: last = vis[-1] if vis else ""; cyy = y0 + (max(1, len(vis)) - 1) * lh; cxx = bx + 50 + tw(last, F_HEAD, fs)
        else: cxx = bx + 50 + tw(s3[:n3], F_HEAD, fs); cyy = y3
        rect(cv, cxx + 8, cyy - fs * 0.42, 5, fs * 0.74, RED if t >= t3a else INK)
    pen_text(cv, "rude.", bx + 50 + tw(s3, F_HEAD, fs) + 34, y3 + 4, 62, (t - (T_ROOM - 0.06)) / 0.26)
    # the room (pictogram chart): everyone flips to panic on "panic", you on "room"
    gx, gy, sp, rsp, ss = 1196, cy_ + 176, 132, 176, 1.25
    text(cv, "THE ROOM", gx - 40, cy_ + 16, F_SANS, 30, MUTE, 1.0, 'l', 'm', track=3)
    order = sorted(range(14), key=lambda i: (ROOM[i][0] - 2) ** 2 + (ROOM[i][1] - 1) ** 2 * 2.2 + 0.01 * i)
    npan = 0
    for i, (c, r) in enumerate(ROOM):
        you = i == 14
        tf = (T_ROOM - 0.40) if you else (T_PANIC - 0.10 + order.index(i) * 0.05)
        k = sstep(tf, tf + 0.10, t)
        if k > 0.5: npan += 1
        x = gx + c * sp; y = gy + r * rsp
        jx = k * 3.4 * math.sin(t * 57 + i * 1.9); jy = k * 2.0 * math.sin(t * 43 + i * 2.7)
        base = PEN if you else BAR
        col = base * (1 - k) + RED * k
        person(cv, x + jx, y + jy, ss, col)
        if k > 0:
            pop = ease_out((t - tf) / 0.14)
            text(cv, "!", x + jx, y - 96 * ss + jy, F_NUM, 40 * (0.6 + 0.4 * pop), RED, k, 'c', 'm')
        if you: text(cv, "you", x, y + 46 * ss + 40, F_SANS, 44, PEN, 1.0, 'c', 'm')
    yl = gy + 2 * rsp + 46 * ss + 104
    text(cv, "panicking", gx - 40, yl, F_SANS, 40, INK2, 1.0, 'l', 'm')
    text(cv, f"{npan} of 15", gx + 4 * sp + 40, yl, F_NUMB, 46, RED if npan else INK, 1.0, 'r', 'm')

# ================================================================ FIG. 22: ten Mac minis, for reasons
def mini(cv, x, y, w, h, op=1.0):
    rect(cv, x, y, w, h, hexc('dcd7ce'), op, r=h * 0.32)
    stroke(cv, [(x + h * 0.4, y + h * 0.28), (x + w - h * 0.4, y + h * 0.28)], CREAM, 2.0, op * 0.8)
    rect(cv, x, y, w, h, INK, op, r=h * 0.32, wd=1.8)
    circle(cv, x + w - h * 0.62, y + h * 0.58, h * 0.09, INK2, op)

PIE = [(41, RED, 250), (33, INK2, 330), (19, hexc('6e675d'), 200), (7, BAR, 290)]
def fig_minis(cv, t):
    cx_, cy_, cw, ch = frame(cv, "FIG. 22", "Mac minis acquired this week, by reason")
    x, y, w, h = cv.box
    sw_ = text(cv, "Source: ", x, y + h - 14, F_SANSM, 30, MUTE, 1.0, 'l', 'm')
    rect(cv, x + sw_ + 2, y + h - 30, 196, 32, INK, 1.0)
    s = 0.80; px, py = 184, cy_ + 14
    kmac = sstep(T_MAC - 0.10, T_MAC + 0.12, t); kmin = sstep(T_MINIS - 0.10, T_MINIS + 0.10, t)
    kfor = sstep(T_FOR - 0.02, T_REASONS + 0.05, t)
    clipping(cv, P_MINIS, _img(P_MINIS), px, py, s, 1.0, marks=[BOX_MINIS[0] + (kmac,), BOX_MINIS[1] + (kmin,), BOX_MINIS[2] + (kfor,)])
    # "...for reasons I can't share": the reasons get redacted
    kr = ease_out((t - (T_CANT - 0.06)) / 0.20)
    if kr > 0:
        bx0, by0, bx1, by1 = BOX_MINIS[2]
        rx0, ry0 = px + (bx0 - 10) * s, py + (by0 - 8) * s; rw, rh = (bx1 - bx0 + 20) * s, (by1 - by0 + 14) * s
        rect(cv, rx0, ry0, rw * kr, rh, INK, 1.0)
        if kr > 0.9: text(cv, "REDACTED", rx0 + rw / 2, ry0 + rh / 2 + 1, F_MONO, 34, CREAM, sstep(0.9, 1.0, kr), 'c', 'm')
    # the stack of ten (a unit chart): one lands per eighth note from "ten"
    sx0, mw, mh, gap = 1350, 360, 40, 6; base = cy_ + 600
    n = 0
    for i in range(10):
        ti = T_TEN - 0.04 + i * 0.112
        k = ease_out((t - ti) / 0.13)
        if k <= 0: continue
        n += 1
        yy = base - (i + 1) * (mh + gap) - 70 * (1 - k)
        mini(cv, sx0, yy, mw, mh, min(1.0, k * 2))
    # the count rides on top of the stack
    if n:
        kt = ease_out((t - (T_TEN - 0.04 + (n - 1) * 0.112)) / 0.13)
        ktop = base - (n - 1 + kt) * (mh + gap)
        text(cv, str(n), sx0 + mw / 2, ktop - 76, F_NUM, 104, INK if n < 10 else RED, 1.0, 'c', 'm')
    text(cv, "Mac minis", sx0 + mw / 2, base + 30, F_SANS, 34, MUTE, sstep(T_TEN - 0.1, T_TEN + 0.1, t), 'c', 'm', track=1)
    # share of reasons: a pie whose legend is redacted
    ky = cy_ + 346
    kk = sstep(T_FOR - 0.10, T_FOR + 0.15, t)
    text(cv, "SHARE OF REASONS", 184, ky, F_SANS, 30, MUTE, kk, 'l', 'm', track=3)
    pcx, pcy, R = 312, ky + 150, 108
    sweep = ease_out((t - (T_FOR - 0.02)) / 0.65)
    a = -math.pi / 2
    for i, (pct, col, bw) in enumerate(PIE):
        span = 2 * math.pi * pct / 100 * sweep
        if span > 0.002: wedge(cv, pcx, pcy, R * 0.52, R, a, a + span, col, 1.0)
        a += span
    lx, lw_ = 500, 640
    for i, (pct, col, bw) in enumerate(PIE):
        ti = T_FOR + 0.08 + i * 0.09
        k = sstep(ti, ti + 0.16, t)
        if k <= 0: continue
        yy = ky + 62 + i * 62
        rect(cv, lx, yy - 15, 30, 30, col, k, r=4)
        rect(cv, lx + 50, yy - 17, bw * ease_out((t - ti) / 0.22), 34, INK, k)
        text(cv, f"{pct}%", lx + lw_, yy, F_NUMB, 40, INK, k, 'r', 'm')

# ================================================================ FIG. 23: Agents, Inc.
L1 = [("CFO", 420), ("CTO", 780), ("Head of HR", 1140), ("VP of Vibes", 1500)]
CEO_W, CEO_H = 456, 256
NSWARM = 20
SW = np.random.default_rng(23).uniform(0, 1, (NSWARM, 7))
def fig_org(cv, t):
    cx_, cy_, cw, ch = frame(cv, "FIG. 23", "Org chart: Agents, Inc. (founded today)", "Source: the agents")
    foot = _has(SHOT_CEO)
    yc, y1, y2 = cy_ + 134, cy_ + 372, cy_ + 578
    # the swarm: agents appear scattered on "agents", fly into their seats on "formed"
    slots = [(960, yc)] + [(xx, y1) for _, xx in L1]
    sizes = [116, 86, 86, 86, 86]
    seats = []
    for i in range(NSWARM):
        seat = i % 5; (sx, sy), sz = slots[seat], sizes[seat]
        r = SW[i]
        ta = T_AGENTS - 0.10 + r[0] * 0.30
        ka = ease_out((t - ta) / 0.20)
        if ka <= 0:
            if i < 5: seats.append(None)
            continue
        # a cohesive flock: it sweeps in from the left and loops once; each agent orbits inside it
        tau = t - T_AGENTS
        fx = lerp(330, 900, ease_out((tau + 0.10) / 0.40)) + 150 * math.sin(2.4 * tau)
        fy = cy_ + 300 + 60 * math.sin(3.4 * tau + 0.5)
        ph_ = r[1] * 2 * math.pi + tau * (2.2 + 1.2 * r[2]) * (1 if r[3] > 0.35 else -1)
        wx = fx + (70 + 120 * r[4]) * math.cos(ph_); wy = fy + (34 + 60 * r[5]) * math.sin(ph_ * 1.0 + r[2])
        kf = ease_io((t - (T_FORMED - 0.06 + r[6] * 0.22)) / 0.46)
        x = lerp(wx, sx, kf); y = lerp(wy, sy, kf)
        if i < 5:
            s_ = lerp(sz * 0.55, sz, kf) * (0.6 + 0.4 * ka)
            seats.append((x, y, s_, kf, ka))
        else:   # the rest of the swarm pours into the five seats
            s_ = sz * 0.50 * (0.6 + 0.4 * ka) * (1 - 0.5 * kf)
            op = 1 - sstep(0.75, 1.0, kf)
            if op > 0.01: bot(cv, x, y, s_, RED if seat == 0 else INK2, op)
    # connectors (drawn on "company")
    kc = ease_out((t - (T_COMPANY - 0.10)) / 0.40)
    ceo_bot = yc + (CEO_H / 2 + 10 if foot else 54)
    yb1 = (ceo_bot + y1 - 66) / 2
    if kc > 0:
        stroke(cv, [(960, ceo_bot), (960, lerp(ceo_bot, yb1, min(1, kc * 2)))], INK2, 2.4)
        if kc > 0.5:
            u = (kc - 0.5) * 2; half = 540 * u
            stroke(cv, [(960 - half, yb1), (960 + half, yb1)], INK2, 2.4)
            if u > 0.98:
                for _, xx in L1: stroke(cv, [(xx, yb1), (xx, y1 - 66)], INK2, 2.4)
    # her node + its connectors (on "made me"): she reports to all four of them
    km = ease_out((t - (T_ME - 0.12)) / 0.26)
    yb2 = y2 - 84
    if km > 0:
        for _, xx in L1: stroke(cv, [(xx, y1 + 96), (xx, lerp(y1 + 96, yb2, km))], INK2, 2.4)
        if km > 0.7:
            stroke(cv, [(420, yb2), (1500, yb2)], INK2, 2.4)
            stroke(cv, [(960, yb2), (960, y2 - 66)], INK2, 2.4)
    for i, st in enumerate(seats):
        if st is None: continue
        x, y, s_, kf, ka = st
        ceo = i == 0
        if ceo and foot and kf > 0.9:
            kp = ease_out((kf - 0.9) / 0.1)
            # the glyph opens into his headshot: the Claude robot from Asking for a Friend
            pw, ph = lerp(s_ * 1.2, CEO_W, kp), lerp(s_ * 0.9, CEO_H, kp)
            u = (t - T_FORMED - 0.25) / 2.75
            photo(cv, SHOT_CEO, u, x - pw / 2, y - ph / 2, pw, ph, kp, base=(CEO_W, CEO_H))
            if kp < 1: bot(cv, x, y, s_, RED, 1 - kp)
        else:
            bot(cv, x, y, s_, RED if ceo else INK2)
        kl = sstep(0.85, 1.0, kf)
        if kl > 0:
            if ceo:
                lx = x + (CEO_W / 2 + 36 if foot else 86)
                text(cv, "CEO", lx, y - 22, F_SANS, 46, RED, kl, 'l', 'm')
                text(cv, "an agent", lx, y + 30, F_ITAL, 50, INK2, kl, 'l', 'm')
            else:
                text(cv, L1[i - 1][0], x, y + 72, F_SANS, 42, INK, kl, 'c', 'm')
    if km > 0:
        crop, m = avatar(); r = 58 * (0.7 + 0.3 * km)
        circle(cv, 960, y2, r + 7, PEN, km)
        if crop is not None: paste(cv, "avatar", crop, 960 - r, y2 - r, 2 * r, 2 * r, km, mask=m)
        text(cv, "Adita", 960 + 86, y2 - 24, F_SANS, 46, PEN, km, 'l', 'm')
        ke = sstep(T_EMPL - 0.06, T_EMPL + 0.12, t)
        text(cv, "employee", 960 + 86, y2 + 30, F_SANSM, 40, MUTE, km * (1 - ke), 'l', 'm')
        if ke > 0:
            text(cv, "EMPLOYEE OF THE YEAR", 960 + 86, y2 + 30, F_SANS, 44, RED, ke, 'l', 'm', track=3)
            # the rosette
            kr = ease_out((t - (T_EMPL - 0.02)) / 0.22); rx, ry = 960 - 116, y2 + 2
            sc = kr * (1 + 0.25 * math.exp(-(t - T_EMPL) * 8) * (t > T_EMPL))
            fill(cv, [(rx - 18 * sc, ry + 10 * sc), (rx - 34 * sc, ry + 66 * sc), (rx - 14 * sc, ry + 56 * sc), (rx - 2 * sc, ry + 72 * sc), (rx + 4 * sc, ry + 14 * sc)], RED)
            fill(cv, [(rx + 18 * sc, ry + 10 * sc), (rx + 34 * sc, ry + 66 * sc), (rx + 14 * sc, ry + 56 * sc), (rx + 2 * sc, ry + 72 * sc), (rx - 4 * sc, ry + 14 * sc)], hexc('b52e22'))
            circle(cv, rx, ry, 36 * sc, RED); circle(cv, rx, ry, 27 * sc, CREAM, 1.0, wd=2.4)
            fill(cv, [(rx + (15 if j % 2 == 0 else 6) * sc * math.cos(-math.pi / 2 + j * math.pi / 5),
                       ry + (15 if j % 2 == 0 else 6) * sc * math.sin(-math.pi / 2 + j * math.pi / 5)) for j in range(10)], CREAM)
        pen_text(cv, "(only employee)", 960 - 178, y2 + 4, 62, (t - (T_EMPL + 0.22)) / 0.42, 'r', 'm')

# ================================================================ FIG. 24: jobs on Earth (+ CORRECTION)
JOBS = 3_412_083_117
FS = 0.70
def fig_jobs(cv, t):
    cx_, cy_, cw, ch = frame(cv, "FIG. 24", "Jobs on Earth, before and after my song", "Source: my song")
    x, y, w, h = 330, cy_ + 76, 760, cy_ + 520 - (cy_ + 76)
    axes(cv, x, y, w, h, [(0.08, "2024"), (0.39, "2025"), (FS + 0.0, "2026")], [(0, "0"), (0.5, "1.7 bn"), (1, "3.4 bn")], ylab="jobs")
    def val(f): return 0.955 + 0.03 * f + 0.008 * math.sin(f * 23)
    def P(f, v): return (x + f * w, y + h - v * h)
    kd = ease_io((t - 114.30) / 0.75)
    pre = [P(f, val(f)) for f in np.linspace(0, FS * kd, max(2, int(60 * kd)))] if kd > 0 else []
    if len(pre) > 1: stroke(cv, pre, INK, 5)
    # the song (a dashed marker on "song")
    ks = sstep(T_SONG - 0.08, T_SONG + 0.12, t)
    if ks > 0:
        xs = x + FS * w
        dashed(cv, [(xs, y - 6), (xs, y - 6 + (h + 6) * ease_out((t - T_SONG + 0.08) / 0.3))], RED, 2.6, ks)
        text(cv, "my song", xs, y - 34, F_SANS, 42, RED, ks, 'c', 'm')
    # the cliff: drawn from "end" to "Earth", in step with the counter
    kc = ease_io((t - (T_END - 0.04)) / (T_EARTH - T_END + 0.04))
    vt = val(FS)
    if kc > 0:
        cliff = [P(FS + 0.035 * u ** 0.5, vt * (1 - u)) for u in np.linspace(0, min(1, kc / 0.85), 30)]
        stroke(cv, cliff, RED, 5)
        if kc > 0.85:
            u = (kc - 0.85) / 0.15
            stroke(cv, [P(FS + 0.035, 0.004), P(lerp(FS + 0.035, 1.0, u), 0.004)], RED, 5)
    pen_text(cv, "oops", x + FS * w + 62, y + h * 0.40, 66, (t - (T_EARTH - 0.50)) / 0.30, 'l')
    # the counter tile, then the CORRECTION
    tx, ty, tw_, th = 1190, cy_ + 76, 560, 470
    corr = sstep(T_GAVE0 - 0.02, T_GAVE0 + 0.14, t)
    if corr > 0:   # the correction tab prints above the tile
        wpx = tw_ * ease_out((t - T_GAVE0 + 0.02) / 0.20)
        rect(cv, tx, ty - 66, wpx, 58, RED, 1.0, r=8)
        if wpx > tw_ * 0.6: text(cv, "CORRECTION", tx + 28, ty - 37, F_SANS, 40, CREAM, sstep(0.6, 0.9, wpx / tw_), 'l', 'm', track=4)
    tile(cv, tx, ty, tw_, th)
    text(cv, "JOBS ON EARTH", tx + 34, ty + 52, F_SANS, 34, MUTE, 1.0, 'l', 'm', track=3)
    n = int(round(JOBS * (1 - kc))) if kc < 1 else 0
    if t >= T_GAVE - 0.02:
        kn = ease_out((t - T_GAVE + 0.02) / 0.16)
        text(cv, "1", tx + 34, ty + 216 + 18 * (1 - kn), F_NUM, 230, INK, kn, 'l', 'm')
        k2 = sstep(T_MYSELF - 0.06, T_MYSELF + 0.14, t)
        text(cv, "job left on Earth.", tx + 34, ty + 360, F_HEAD, 52, INK, k2, 'l', 'm')
        text(cv, "It's mine.", tx + 34, ty + 420, F_ITAL, 52, RED, sstep(T_MYSELF + 0.10, T_MYSELF + 0.30, t), 'l', 'm')
    elif n > 0:
        s_ = f"{n:,}"; fs = fit(s_, F_NUM, 76, tw_ - 68, 30)
        text(cv, s_, tx + 34, ty + 200, F_NUM, fs, INK, 1.0, 'l', 'm')
        text(cv, "and counting", tx + 34, ty + 300, F_ITAL, 46, INK2, 1.0, 'l', 'm')
    else:
        kz = ease_out((t - T_EARTH) / 0.14)
        text(cv, "0", tx + 34, ty + 216, F_NUM, 230, RED, 1.0, 'l', 'm')
    stamp(cv.img, cv, "HIRED", 580, y + h * 0.56, 92, T_BRAND - 0.04, t, RED, ang=-8.0, sub="BY MYSELF", seed=9)

# ================================================================ FIG. 25: net worth, tripled
def fig_worth(cv, t):
    cx_, cy_, cw, ch = frame(cv, "FIG. 25", "My net worth, tripled", "Source: my bank app, checked three times")
    # the KPI tile: $0 x 3 = $0, one piece per word
    tx, ty, tw_, th = 184, cy_ + 24, 780, 420
    tile(cv, tx, ty, tw_, th)
    text(cv, "NET WORTH", tx + 40, ty + 56, F_SANS, 34, MUTE, 1.0, 'l', 'm', track=3)
    parts = [("$0", T_TRIPLED - 0.04, INK), (" × 3", T_MY - 0.04, INK), (" = $0", T_WORTH - 0.06, RED)]
    fs = fit("$0 × 3 = $0", F_NUM, 150, tw_ - 80, 60)
    xx = tx + 40
    for s_, ts, col in parts:
        k = ease_out((t - ts) / 0.18)
        if k > 0: text(cv, s_, xx, ty + 196 + 22 * (1 - k), F_NUM, fs, col, k, 'l', 'm')
        xx += tw(s_, F_NUM, fs)
    stroke(cv, [(tx + 40, ty + 300), (tx + tw_ - 40, ty + 300)], RULE, 1.6)
    kg = sstep(T_WORTH + 0.16, T_WORTH + 0.34, t)
    text(cv, "growth", tx + 40, ty + 362, F_SANS, 46, INK2, kg, 'l', 'm')
    text(cv, "+200%", tx + tw_ - 40, ty + 362, F_NUMB, 58, RED, kg, 'r', 'm')
    pen_text(cv, "checks out", tx + 44, ty + th + 74, 68, (t - (T_WORTH + 0.40)) / 0.36)
    # the photo next to the story: assets
    px, py, pw, ph = 1040, cy_ + 34, 704, 396
    if _has(SHOT_CAR):
        photo(cv, SHOT_CAR, (t - 119.70) / 3.25, px, py, pw, ph)
        text(cv, "Pictured: assets.", px - 8, py + ph + 52, F_ITAL, 50, INK, 1.0, 'l', 'm')
        kc = sstep(T_WORTH + 0.84, T_WORTH + 1.00, t)
        text(cv, "(Not mine. Rendered.)", px - 8, py + ph + 112, F_ITAL, 50, RED, kc, 'l', 'm')
    else:   # no footage: three empty bars instead
        x, y, w, h = px + 100, py + 40, pw - 120, ph - 40
        axes(cv, x, y, w, h, [], [(0, "$0"), (0.5, "$0"), (1, "$0")])
        for i, lab in enumerate(("Before", "Doubled", "Tripled")):
            xc = x + (i + 0.5) / 3 * w
            text(cv, lab, xc, y + h + 48, F_SANS, 44, INK, 1.0, 'c', 'm')
            k = ease_out((t - (T_TRIPLED - 0.06 + i * 0.13)) / 0.22)
            if k > 0:
                rect(cv, xc - 70 * k, y + h - 8, 140 * k, 8, RED, 1.0)
                text(cv, "$0", xc, y + h - 50 + 16 * (1 - k), F_NUMB, 52, RED, k, 'c', 'm')

# ---------------------------------------------------------------- schedule (the TED Charts figure swap: fade + 46 px slide)
FIGS = [
    (99.0, 103.64, fig_posts),
    (103.64, 107.40, fig_summary),
    (107.40, 110.66, fig_minis),
    (110.66, 114.30, fig_org),
    (114.30, 119.80, fig_jobs),
    (119.80, 130.0, fig_worth),
]

def draw_figs(cv, t):
    for a, b, fn in FIGS:
        if not (a - 0.3 <= t <= b + 0.3): continue
        ein = ease_out((t - (a - 0.04)) / 0.24) if a > T0 else 1.0
        eout = ease_io((t - (b - 0.1)) / 0.2)
        op = ein * (1 - eout)
        if op <= 0.004: continue
        cv.op = op; cv.dy = (1 - ein) * 46 - eout * 46
        fn(cv, t)
        cv.dy = 0.0; cv.op = 1.0

SPOT_BOX = (140, 236, 1640, 790)
def render_frame(t, W=1920, H=1080):
    img = paper(W, H)
    cv = Cv(img, W, H)
    masthead(cv, t)
    draw_figs(cv, t)
    amb = lerp(1.0, 0.24, ease_io((t - T_DIM) / 0.70))
    light(img, amb, SPOT_BOX)
    return finish(img, int(round(t * 30)))
