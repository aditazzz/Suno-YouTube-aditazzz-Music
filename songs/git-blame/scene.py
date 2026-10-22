"""Git Blame — receipts in neon.

Intro: a blame view opens, "Let's see who wrote this." V1: every line in the gutter says his name; 3:14 a.m. "fixed some
things"; prod catches fire; the coffee goes cold. Pre: "it's in the log" scrolls forever. Chorus: coral/teal synth-pop,
a wall of lines all signed by him, squash / rebase / rewrite / rearrange shuffles the lines and his name stays put.
V2: the diff is public, force-push bounces off BRANCH PROTECTION: LOCKED, "Co-authored-by: your best friend".
Receipts: commit cards with timestamps, "Love you." gets REVERTED one minute later. Bridge 2: one command typed.
Final: kaleidoscope of his name. Outro: Collaborator removed. Changes saved.
"""
import os, math
import numpy as np, cv2
from studio import core as C
from studio import kit as K
from studio.core import (sstep, ease_out, ease_io, win, lerp, hexc, clamp, sprite, blit, text_w, shadow,
                         F_INTER, F_DISP, F_DISPB, F_MONO, F_MONOB, WHITE)
from studio.kit import panel, label, bubble, grid, vgrad, ssa, desat, sticker, check, INK, editor, chip, fill_poly, heart_pts

HERE = os.path.dirname(os.path.abspath(__file__))
TM = C.Timing(HERE)
TAIL = 0.0
DUR = TM.duration
LINES = TM.lines
TM.stamps = []; TM.stamp_word = None
def lt(sub, nth=0):
    try: return TM.line_t(sub, nth)
    except Exception: return 1e9
def sec(n): return TM.section(n)
def bp(t, k=7.0): return TM.beat_pulse(t, k)
def lines_in(sn): return [L for L in LINES if L['sec'] == sn]

CORAL = hexc('ff4d6d'); TEAL = hexc('19d3c5'); PEACH = hexc('ffb38a'); NIGHT = hexc('120d24'); PLUM = hexc('2b1146')
LIME = hexc('b8ff5c'); GOLD = hexc('ffcf4a'); SKY = hexc('5cc8ff'); PINK = hexc('ff7ac3'); RED = hexc('ff3344'); GREEN = hexc('2bd67b')
HIM = "him"; BFF = "your bestie"

S = {n: sec(n) for n in ("V1", "PRE1", "CH1", "V2", "PRE2", "CH2", "BRIDGE", "BRIDGE2", "FINAL", "OUTRO")}
CHORUS = [(S["CH1"]['s'], S["V2"]['s'], 0), (S["CH2"]['s'], S["BRIDGE"]['s'], 1), (S["FINAL"]['s'], S["OUTRO"]['s'], 2)]
PRES = [(S["PRE1"]['s'], S["CH1"]['s']), (S["PRE2"]['s'], S["CH2"]['s'])]
def chorus_at(t):
    for a, b, k in CHORUS:
        if a - 0.05 <= t < b: return k, a, b
def pre_at(t):
    for a, b in PRES:
        if a - 0.05 <= t < b: return a, b
def phase(t):
    if t < S["V1"]['s'] - 0.2: return "intro"
    if chorus_at(t): return "chorus"
    if pre_at(t): return "pre"
    if t < S["PRE1"]['s']: return "v1"
    if t < S["PRE2"]['s']: return "v2"
    if t < S["BRIDGE2"]['s']: return "receipts"
    if t < S["FINAL"]['s']: return "bridge2"
    return "outro"

T_OK = lt("Okay."); T_WHO = lt("Let's see who wrote")
T_TOUCH = lt("never touched"); T_HIST = lt("pulled the history"); T_42 = lt("Line forty-two"); T_NAME = lt("Your name."); T_43 = lt("Forty-three")
T_AGAIN = lt("You again"); T_314 = lt("Three fourteen"); T_FIXED = lt("fixed some things"); T_TRUST = lt("My trust")
T_PROD = lt("broken in prod"); T_MAIN = lt("Pushed straight"); T_REVIEW = lt("No review"); T_BURN = lt("whole thing's burning")
T_COFFEE = lt("coffee went cold"); T_FACE = lt("dead in the face"); T_ITSELF = lt("code wrote itself")
T_FRIENDS = lt("You told your friends"); T_BROKE = lt("broke the build"); T_CUTE = lt("That's cute"); T_DIFF = lt("diff is public")
T_CIRCLE = lt("circle back"); T_BLOCK = lt("circled the block"); T_FORCE = lt("force-push"); T_BRANCH = lt("Branch protection")
T_LOCKED = lt("Locked."); T_EVERYLIE = lt("Every little lie"); T_STAMPED = lt("Timestamped"); T_NOTHING = lt("nothing's going on")
T_LINES = lt("right there in the lines"); T_COAUTH = lt("Co-authored"); T_HELL = lt("hell of a commit"); T_HIDE = lt("didn't even hide")
T_CHECK = lt("never check it")
T_TUE = lt("Tuesday."); T_FRI = lt("Friday."); T_SUN = lt("Sunday.", 0); T_LOVE = lt("Love you."); T_REVERT = lt("Reverted.")
T_SUN2 = lt("Sunday.", 1); T_904 = lt("Nine oh four")
T_SIDE = lt("need your side"); T_ALIBI = lt("your alibi"); T_CMD = lt("One command"); T_LINE1 = lt("One little line")
T_SHOWED = lt("look who showed up"); T_EVERYT = lt("Every time"); T_GB = lt("Git blame.")
T_REMOVED = lt("Collaborator removed"); T_SAVED = lt("Changes saved")
T_END = max(T_SAVED + 2.2, DUR - 6.5)

CODE = ["def ship_it(build):", "    if build.green:", "        deploy(main)", "    trust = load_trust()",
        "    # fixed some things", "    trust = None", "    return prod", "def alibi(day):", "    return 'working late'",
        "def gym():", "    return 'at the gym'", "    # TODO: tell her", "def commit(msg):", "    push(main, force=True)",
        "    review = skip()", "    return msg"]

# ---------------------------------------------------------------- backgrounds
def bg_night(G, t):
    img = vgrad(G, PLUM * 0.9, NIGHT)
    img += TEAL * (0.14 * np.exp(-((G['X'] + 0.5) ** 2 * 2 + (G['Y'] + 0.2) ** 2 * 3)))[..., None]
    img += CORAL * (0.12 * np.exp(-((G['X'] - 0.6) ** 2 * 2 + (G['Y'] - 0.3) ** 2 * 3)))[..., None]
    return img

def bg_chorus(G, t, k):
    pals = [(CORAL, TEAL), (TEAL, PINK), (GOLD, CORAL)]
    c1, c2 = pals[k]
    base = vgrad(G, c1 * 0.75, c2 * 0.35, c1 * 0.5 + c2 * 0.3, 0.55)
    # synthwave grid floor
    Y = G['Y']; X = G['X']; hz = 0.12
    below = Y > hz
    zz = 1.0 / np.maximum(Y - hz, 1e-3)
    gx = np.abs(((X * zz * 0.6) % 1) - 0.5); gz = np.abs(((zz * 0.35 + t * 1.2) % 1) - 0.5)
    lines = np.maximum(ssa(0.46, 0.5, gx), ssa(0.44, 0.5, gz)) * below * np.clip((Y - hz) * 3, 0, 1)
    img = base + c2 * (0.55 * lines)[..., None] + WHITE * (0.15 * lines)[..., None]
    sun = np.exp(-(X ** 2 + (Y - 0.0) ** 2) * 9) * (Y < hz)
    stripes = ssa(-0.1, 0.1, np.sin(Y * 90 + t * 2))
    img += GOLD * (0.65 * sun * (0.5 + 0.5 * stripes))[..., None]
    img *= 0.9 + 0.2 * bp(t, 6)
    return img

def bg_receipts(G, t):
    img = vgrad(G, hexc('1e1a2e'), hexc('0b0a12'))
    # corkboard-ish warm vignette
    img += PEACH * (0.06 * np.exp(-G['R'] ** 2 * 2))[..., None]
    return img

# ---------------------------------------------------------------- UI
def blame_view(img, t, W, H, ts, vert):
    """Intro + V1: blame gutter fills with his name; 3:14 commit; prod burns."""
    if t > S["PRE1"]['s'] + 0.2: return
    a = sstep(T_TOUCH - 0.8, T_TOUCH - 0.3, t) * (1 - sstep(S["PRE1"]['s'] - 0.2, S["PRE1"]['s'] + 0.2, t))
    if not vert: x, y, w, h = W * 0.10, H * 0.05, W * 0.80, H * 0.56
    else: x, y, w, h = W * 0.04, H * 0.10, W * 0.92, H * 0.50
    n_named = 0
    if t > T_TOUCH: n_named = int(clamp((t - T_TOUCH) / max(0.5, T_314 - T_TOUCH)) * len(CODE))
    blame = [(HIM if i < n_named else "") for i in range(len(CODE))]
    hl = set()
    if T_42 - 0.1 < t < T_314: hl = {3} if t < T_43 - 0.1 else {4}
    if T_314 - 0.1 < t < T_BURN: hl = {4, 5}
    fs = (36 if not vert else 40) * ts
    editor(img, x, y, w, h, CODE, a, ts, fs=fs, title="git blame relationship.py", blame=blame, blame_w=text_w("him  ", F_MONOB, int(fs * 0.85)),
           blame_col=CORAL, hl=hl, hl_col=CORAL * 0.45, line_no0=40)
    # line call-outs
    if T_42 - 0.1 < t < T_314 - 0.1:
        k = sstep(T_42 - 0.1, T_42 + 0.1, t) * a
        chip(img, "line 42: him" if t < T_43 - 0.1 else "line 43: him again", W / 2, y + h + 64 * ts, 56 * ts, CORAL, WHITE, k, T_42 - 0.1 if t < T_43 - 0.1 else T_43 - 0.1, t)
    if T_314 - 0.1 < t < T_PROD - 0.1:
        k = sstep(T_314 - 0.1, T_314 + 0.1, t) * a
        cw, chh = (W * 0.5 if not vert else W * 0.86), 140 * ts
        panel(img, W / 2 - cw / 2, y + h + 14 * ts, cw, chh, hexc('241f3a'), k, r=int(22 * ts), border=TEAL)
        label(img, "3:14 a.m.  ·  him", W / 2, y + h + 14 * ts + chh * 0.30, 42 * ts, TEAL, k, F_MONOB, sh=0)
        label(img, "\"fixed some things\"", W / 2, y + h + 14 * ts + chh * 0.70, 50 * ts, WHITE, k, F_DISPB, sh=0)
    if T_TRUST - 0.1 < t < T_PROD - 0.1:
        k = sstep(T_TRUST - 0.1, T_TRUST + 0.1, t) * a
        sticker(img, W / 2 + (300 if not vert else 250) * ts, y + h * 0.35, 0.8 * ts, k, -0.2, t - T_TRUST, "MY TRUST?")
    # prod on fire + coffee cold
    if t > T_PROD - 0.1:
        k = sstep(T_PROD - 0.1, T_PROD + 0.15, t) * a
        status = "PROD: DOWN" if t > T_BURN - 0.1 else "pushed to main · no review"
        col = RED if t > T_BURN - 0.1 else GOLD
        chip(img, status, W / 2, y + h + 64 * ts, 56 * ts, col, WHITE if col is RED else INK, k, T_PROD - 0.1 if t < T_BURN - 0.1 else T_BURN - 0.1, t)
        if t > T_BURN - 0.1:   # flames along the bottom of the editor
            lay = np.zeros_like(img); n = 26
            for i in range(n):
                fx = x + w * (i + 0.5) / n; ph = i * 1.7
                fh = (60 + 50 * (0.5 + 0.5 * math.sin(t * 9 + ph))) * ts * sstep(T_BURN - 0.1, T_BURN + 0.6, t)
                pts = np.array([(fx - 22 * ts, y + h), (fx, y + h - fh), (fx + 22 * ts, y + h)], np.int32)
                cv2.fillPoly(lay, [pts], (GOLD * 0.6 + CORAL * 0.6).tolist(), cv2.LINE_AA)
            img += cv2.GaussianBlur(lay, (0, 0), 5) * 0.9 * a + lay * 0.4 * a
    if t > T_COFFEE - 0.1:
        k = sstep(T_COFFEE - 0.1, T_COFFEE + 0.2, t) * a * (1 - sstep(T_ITSELF + 0.6, T_ITSELF + 1.0, t))
        cx, cy, s = x + w - 120 * ts, y + h - 160 * ts, 110 * ts
        panel(img, cx - s / 2, cy - s / 2, s, s * 1.05, SKY * 0.8, k, r=int(s * 0.18))
        cv2.ellipse(img, (int(cx + s * 0.55), int(cy)), (int(s * 0.2), int(s * 0.25)), 0, -90, 90, (SKY * 0.8 * k).tolist(), max(4, int(s * 0.1)), cv2.LINE_AA)
        label(img, "cold", cx, cy + s * 0.85, 40 * ts, SKY, k, F_DISPB)
    if t > T_ITSELF - 0.1:
        k = sstep(T_ITSELF - 0.1, T_ITSELF + 0.1, t) * a
        chip(img, "\"the code wrote itself\"", W / 2, H * 0.36, 60 * ts, WHITE, INK, k, T_ITSELF - 0.1, t)

T_TOAST = 1.4
def intro_ui(img, t, W, H, ts, vert):
    if t > T_TOUCH: return
    # frame 0 is a real picture: the title, then his push notification (3:14 AM, "fixed some things")
    at = 1 - sstep(T_WHO - 0.6, T_WHO - 0.2, t)
    if at > 0.01:
        cy = H * (0.36 if not vert else 0.33)
        fs = int((170 if not vert else 150) * ts * (1 + 0.04 * bp(t, 8)))
        blit(img, sprite("git blame", F_MONOB, fs, 14), W / 2, cy, WHITE, at, 0.8 * at, glow_color=CORAL, anchor='c')
        label(img, "relationship.py", W / 2, cy + fs * 0.78, 46 * ts, TEAL, at, F_MONOB, sh=0)
        k = sstep(T_TOAST, T_TOAST + 0.35, t) * at
        if k > 0.01:
            cw = W * (0.46 if not vert else 0.88); ch = 160 * ts
            x = W / 2 - cw / 2; y = H * (0.60 if not vert else 0.46) - (1 - ease_out((t - T_TOAST) / 0.4)) * 50 * ts
            seen = sstep(T_OK - 0.1, T_OK + 0.1, t)
            panel(img, x, y, cw, ch, hexc('1d1833'), k, r=int(26 * ts), border=CORAL * (0.5 + 0.5 * seen) + TEAL * 0.5 * (1 - seen))
            K.dot(img, x + 70 * ts, y + ch / 2, 40 * ts, CORAL, k)
            blit(img, sprite("h", F_DISPB, int(44 * ts)), x + 70 * ts, y + ch / 2, WHITE, k, anchor='c')
            blit(img, sprite("him pushed to main", F_DISPB, int(48 * ts)), x + 130 * ts, y + 26 * ts, WHITE, k)
            blit(img, sprite("3:14 AM · \"fixed some things\"", F_MONO, int(40 * ts)), x + 130 * ts, y + 94 * ts, TEAL, k)
    a = sstep(T_WHO - 0.3, T_WHO, t) * (1 - sstep(T_TOUCH - 1.0, T_TOUCH - 0.4, t))
    if a <= 0.01: return
    cmd = K.typed_line("$ git blame us", t, T_WHO, 14)
    fs = int((88 if not vert else 72) * ts); cy = H * (0.40 if not vert else 0.38)
    blit(img, sprite(cmd if cmd else " ", F_MONOB, fs, 10), W / 2, cy, TEAL, a, 0.5 * a, glow_color=TEAL, anchor='c')
    # git's own progress fills the instrumental before the verse
    t0, t1 = T_WHO + 1.6, T_TOUCH - 1.8
    if t > t0:
        p = clamp((t - t0) / (t1 - t0)); n = int(p * 42); q = a * sstep(t0, t0 + 0.2, t)
        msg = f"Blaming lines: {int(p * 100):3d}% ({n}/42)" + (", done." if p >= 1 else "")
        bw = W * (0.56 if not vert else 0.84); by = cy + fs * 0.9
        blit(img, sprite(msg, F_MONO, int((46 if not vert else 42) * ts)), W / 2 - bw / 2, by, WHITE * 0.85, q)
        bh = 22 * ts; yb = by + 80 * ts
        panel(img, W / 2 - bw / 2, yb, bw, bh, WHITE * 0.12, q, r=int(bh / 2), shadow_op=0)
        if p > 0.01: panel(img, W / 2 - bw / 2, yb, max(bh, bw * p), bh, CORAL, q * (0.8 + 0.2 * bp(t, 6)), r=int(bh / 2), shadow_op=0)

def pre_ui(img, t, W, H, ts, vert):
    p = pre_at(t)
    if not p: return
    a, b = p; o = sstep(a - 0.05, a + 0.15, t) * (1 - sstep(b - 0.15, b, t))
    # git log scrolling: every commit by him
    msgs = ["fixed some things", "working late", "at the gym", "small change", "nothing's going on", "love you", "cleanup", "it's nothing", "trust me"]
    rows = [(f"{(0xa3f9 + i * 977) % 0xffff:04x}  him  {m}", None) for i, m in enumerate(msgs * 3)]
    if not vert: x, y, w, h = W * 0.12, H * 0.06, W * 0.76, H * 0.62
    else: x, y, w, h = W * 0.04, H * 0.10, W * 0.92, H * 0.50
    lines = [(s, WHITE * 0.9) for s, _ in rows]
    scroll = (t - a) * 3.0
    editor(img, x, y, w, h, [r[0] for r in rows], o, ts, fs=(40 if not vert else 40) * ts, title="git log --author=him", scroll=scroll,
           hl={int(scroll) + 2}, hl_col=TEAL * 0.35)
    label(img, "IT'S IN THE LOG", W / 2, y + h + 80 * ts, (92 if not vert else 80) * ts, WHITE, o * (0.6 + 0.4 * bp(t, 5)), F_DISP)

def chorus_ui(img, t, W, H, ts, vert):
    c = chorus_at(t)
    if not c: return
    k, a, b = c; o = sstep(a - 0.05, a + 0.15, t) * (1 - sstep(b - 0.15, b + 0.05, t))
    ls = lines_in(["CH1", "CH2", "FINAL"][k])
    def tl(sub, nth=0):
        h = [L['s'] for L in ls if sub.lower() in L['text'].lower()]
        return h[nth] if nth < len(h) else 1e9
    t_squash = tl("Squash"); t_rewrite = tl("Rewrite"); t_version = tl("need your version"); t_see = tl("see who made it")
    t_log = max(L['e'] for L in ls) + 0.5          # instrumental tail of the chorus: git shortlog says it all
    dim = 1 - 0.75 * sstep(t_log, t_log + 0.4, t)
    # giant "git blame" title on the beat
    fs = int((150 if not vert else 120) * ts) * (1 + 0.06 * bp(t, 8))
    cy = H * (0.16 if not vert else 0.15)
    blit(img, sprite("git blame", F_MONOB, int(fs), 14), W / 2, cy, WHITE, o, 0.8 * o, glow_color=[CORAL, TEAL, GOLD][k], anchor='c')
    # wall of lines, every one signed "him"
    n = 7; lh = (78 if not vert else 84) * ts; y0 = cy + fs * 0.75
    w = W * (0.72 if not vert else 0.92); x0 = W / 2 - w / 2
    order = list(range(n))
    if t > t_squash - 0.1 and t < t_version:   # squash / rebase / rewrite / rearrange: lines shuffle, name stays
        seed = int((t - t_squash) / 0.55)
        rng = np.random.default_rng(seed); rng.shuffle(order)
    labels = ["every line", "got your name", "you can lie", "the log won't change", "squash it", "rebase it", "rearrange it"]
    for r in range(n):
        yy = y0 + r * lh
        if yy > H * (0.66 if not vert else 0.62): break
        j = order[r]
        appear = sstep(a + r * 0.08, a + r * 0.08 + 0.2, t)
        q = o * appear * dim
        if q <= 0.01: continue
        hl = (t > t_see - 0.1)
        panel(img, x0, yy, w, lh * 0.82, (hexc('1a1530') if not hl else CORAL * 0.85), q * 0.92, r=int(14 * ts), shadow_op=0.3)
        fh, fl_ = (42, 40) if not vert else (50, 48)
        blit(img, sprite("him", F_MONOB, int(fh * ts)), x0 + 24 * ts, yy + lh * 0.10, (CORAL if not hl else WHITE), q)
        blit(img, sprite(labels[j], F_MONO, int(fl_ * ts)), x0 + (140 if not vert else 160) * ts, yy + lh * 0.10, WHITE * 0.92, q)
    if t > t_see - 0.1:
        chip(img, "I can see who made it", W / 2, H * (0.64 if not vert else 0.62), 56 * ts, WHITE, INK, o * (1 - sstep(t_log, t_log + 0.3, t)), t_see - 0.1, t)
    if t > t_log: shortlog(img, t, t_log, W, H, ts, vert, o, [CORAL, TEAL, GOLD][k])

def shortlog(img, t, t0, W, H, ts, vert, o, acc):
    """`git shortlog -sn`: 42 lines him, 0 me. Fills the instrumental after each chorus."""
    k = sstep(t0, t0 + 0.35, t) * o
    if k <= 0.01: return
    cw = W * (0.56 if not vert else 0.90); ch = (330 if not vert else 340) * ts
    x = W / 2 - cw / 2; y = H * (0.40 if not vert else 0.36) - (1 - ease_out((t - t0) / 0.4)) * 40 * ts
    panel(img, x, y, cw, ch, hexc('15121f'), k, r=int(26 * ts), border=acc)
    blit(img, sprite("$ git shortlog -sn", F_MONOB, int(42 * ts)), x + 40 * ts, y + 34 * ts, TEAL, k)
    fill = ease_out((t - t0 - 0.4) / 0.9)
    for i, (n, who, frac, col) in enumerate(((42, "him", fill, CORAL), (0, "me", 0.0, WHITE * 0.5))):
        yy = y + (120 + i * 105) * ts; fs = int(56 * ts)
        num = int(round(n * fill)) if i == 0 else 0
        blit(img, sprite(f"{num:>2}", F_MONOB, fs), x + 40 * ts, yy, GOLD if i == 0 else WHITE * 0.45, k)
        blit(img, sprite(who, F_MONOB, fs), x + 160 * ts, yy, WHITE if i == 0 else WHITE * 0.45, k)
        bx = x + (330 if not vert else 290) * ts; bw = x + cw - 40 * ts - bx; by = yy + 14 * ts; bh = 34 * ts
        panel(img, bx, by, bw, bh, WHITE * 0.12, k, r=int(bh / 2), shadow_op=0)
        if frac > 0.02: panel(img, bx, by, max(bh, bw * frac), bh, col, k * (0.85 + 0.15 * bp(t, 6)), r=int(bh / 2), shadow_op=0)

def v2_ui(img, t, W, H, ts, vert):
    if not (S["V2"]['s'] - 0.1 < t < S["PRE2"]['s'] + 0.1): return
    o = sstep(S["V2"]['s'] - 0.1, S["V2"]['s'] + 0.15, t) * (1 - sstep(S["PRE2"]['s'] - 0.2, S["PRE2"]['s'], t))
    R_ = W * (0.86 if not vert else 0.94); L_ = W * (0.14 if not vert else 0.06)
    fs = int(46 * ts)
    if t < T_CIRCLE - 0.1:
        y = H * (0.12 if not vert else 0.15)
        bubble(img, L_, y, "she broke the build lol", o, ts, hexc('3b3b4f'), fs=fs, align='l', pop_t=T_FRIENDS, t=t)
        if t > T_CUTE - 0.1: bubble(img, R_, y + 120 * ts, "that's cute", o, ts, CORAL, fs=fs, align='r', pop_t=T_CUTE - 0.1, t=t)
        if t > T_DIFF - 0.1:
            k = sstep(T_DIFF - 0.1, T_DIFF + 0.15, t) * o
            dx, dw = (W * 0.2, W * 0.6) if not vert else (W * 0.06, W * 0.88); dy = y + 230 * ts
            rows = [("- she broke it", RED), ("+ he pushed to main", GREEN), ("+ force=True", GREEN)]
            for i, (s, col) in enumerate(rows):
                panel(img, dx, dy + i * 80 * ts, dw, 70 * ts, col * 0.35, k, r=int(12 * ts), shadow_op=0)
                blit(img, sprite(s, F_MONOB, int(42 * ts)), dx + 24 * ts, dy + i * 80 * ts + 10 * ts, col * 0.6 + WHITE * 0.5, k)
            label(img, "the diff is public", W / 2, dy + 290 * ts, 54 * ts, WHITE, k, F_DISP)
        return
    if t < T_EVERYLIE - 0.1:
        # circle back -> circled the block -> force push bounces off a lock
        y = H * (0.34 if not vert else 0.33)
        if t < T_FORCE - 0.1:
            k = o; ang = (t - T_CIRCLE) * 3
            r = (200 if not vert else 180) * ts
            for i in range(10):
                aa = ang - i * 0.18
                cv2.circle(img, (int(W / 2 + math.cos(aa) * r), int(y + math.sin(aa) * r)), int((22 - i * 1.8) * ts), (CORAL * k * (1 - i / 10)).tolist(), -1, cv2.LINE_AA)
            label(img, "circling back…" if t < T_BLOCK - 0.1 else "…around the block", W / 2, y, 62 * ts, WHITE, k, F_DISP)
            return
        k = o
        lock = t > T_BRANCH - 0.1
        bx = W / 2 - (1 - ease_out((t - T_FORCE) / 0.5)) * W * 0.4
        if not lock:
            chip(img, "git push --force", bx, y, 64 * ts, GOLD, INK, k, T_FORCE - 0.1, t)
        else:
            bounce = math.exp(-(t - T_BRANCH) * 5) * math.sin((t - T_BRANCH) * 25) * 30 * ts
            s = 170 * ts; lx = W / 2 + bounce
            cv2.ellipse(img, (int(lx), int(y - s * 0.45)), (int(s * 0.32), int(s * 0.38)), 0, 180, 360, (TEAL * k).tolist(), max(6, int(s * 0.12)), cv2.LINE_AA)
            panel(img, lx - s * 0.5, y - s * 0.45, s, s * 0.8, TEAL, k, r=int(s * 0.14))
            label(img, "BRANCH PROTECTION", W / 2, y + s * 0.75, (66 if not vert else 58) * ts, WHITE, k, F_DISP)
            if t > T_LOCKED - 0.1:
                sticker(img, W / 2 + s * 0.9, y - s * 0.4, 0.75 * ts, k, -0.2, t - T_LOCKED + 0.1, "LOCKED")
        return
    if t < T_COAUTH - 0.1:
        # every little lie, timestamped and signed
        k = o; y0 = H * (0.10 if not vert else 0.13)
        lies = [(T_EVERYLIE, "\"nothing's going on\"", "Tue 02:14"), (T_STAMPED, "\"just a friend\"", "Fri 23:52"), (T_NOTHING, "\"it's nothing\"", "Sun 09:03")]
        for i, (tt, s, ts_) in enumerate(lies):
            if t < tt - 0.1: continue
            q = sstep(tt - 0.1, tt + 0.1, t) * k
            cw = W * (0.6 if not vert else 0.9); yy = y0 + i * 150 * ts
            panel(img, W / 2 - cw / 2, yy, cw, 120 * ts, hexc('201b33'), q, r=int(20 * ts), border=CORAL * 0.8)
            blit(img, sprite(ts_, F_MONOB, int((38 if not vert else 42) * ts)), W / 2 - cw / 2 + 30 * ts, yy + 36 * ts, TEAL, q)
            blit(img, sprite(s, F_DISPB, int((46 if not vert else 50) * ts)), W / 2 - cw / 2 + 260 * ts, yy + 30 * ts, WHITE, q)
            check(img, W / 2 + cw / 2 - 60 * ts, yy + 60 * ts, 36 * ts, GREEN, q)
        return
    # co-authored with my best friend
    k = o
    cw = W * (0.66 if not vert else 0.92); ch = (330 if not vert else 360) * ts; cx = W / 2 - cw / 2; cy = H * (0.10 if not vert else 0.13)
    panel(img, cx, cy, cw, ch, hexc('1b1730'), k, r=int(26 * ts), border=PINK)
    blit(img, sprite("commit 9f3e2a1", F_MONOB, int(40 * ts)), cx + 36 * ts, cy + 30 * ts, GOLD, k)
    blit(img, sprite("Author: him", F_MONOB, int(42 * ts)), cx + 36 * ts, cy + 100 * ts, WHITE, k)
    if t > T_COAUTH + 0.4:
        q = sstep(T_COAUTH + 0.4, T_COAUTH + 0.6, t) * k
        blit(img, sprite(f"Co-authored-by: {BFF}", F_MONOB, int(42 * ts)), cx + 36 * ts, cy + 170 * ts, PINK, q)
        for i in range(6):
            hx = cx + cw - 80 * ts - i * 50 * ts; hy = cy + 175 * ts - (t - T_COAUTH) * 60 * ts * (1 + i * 0.3) % (120 * ts)
            fill_poly(img, heart_pts(hx, hy, 34 * ts), PINK, q * 0.8)
    if t > T_HELL - 0.1:
        chip(img, "that's a hell of a commit", W / 2, cy + ch + 80 * ts, 56 * ts, CORAL, WHITE, k, T_HELL - 0.1, t)

def receipts_ui(img, t, W, H, ts, vert):
    if not (S["BRIDGE"]['s'] - 0.2 < t < S["BRIDGE2"]['s'] + 0.2): return
    o = sstep(S["BRIDGE"]['s'] - 0.2, S["BRIDGE"]['s'] + 0.3, t) * (1 - sstep(S["BRIDGE2"]['s'] - 0.2, S["BRIDGE2"]['s'] + 0.1, t))
    cards = [(T_TUE, "TUE  2:14 AM", "\"working late\"", TEAL), (T_FRI, "FRI  11:52 PM", "\"at the gym\"", GOLD), (T_SUN, "SUN  9:03 AM", "\"love you\"", PINK)]
    if not vert: cw, ch = W * 0.27, H * 0.40; xs = [W * 0.20, W * 0.50, W * 0.80]; ys = [H * 0.30] * 3
    else: cw, ch = W * 0.80, H * 0.13; xs = [W * 0.5] * 3; ys = [H * 0.16, H * 0.31, H * 0.46]
    for i, (tt, when, what, col) in enumerate(cards):
        if i == 0: tt = min(tt, S["BRIDGE"]['s'] + 0.1)
        if t < tt - 0.1: continue
        q = sstep(tt - 0.1, tt + 0.15, t) * o; rot = (-0.04, 0.03, -0.02)[i]
        x, y = xs[i] - cw / 2, ys[i] - ch / 2 - (1 - ease_out((t - tt + 0.1) / 0.3)) * 60 * ts
        panel(img, x, y, cw, ch, hexc('fbf6ec'), q, r=int(16 * ts))
        panel(img, x, y, cw, (70 if not vert else 60) * ts, col, q, r=int(16 * ts), shadow_op=0)
        blit(img, sprite(when, F_MONOB, int(40 * ts)), x + cw / 2, y + (35 if not vert else 30) * ts, INK, q, anchor='c')
        blit(img, sprite(what, F_DISP, int((54 if not vert else 50) * ts)), x + cw / 2, y + ch * (0.62 if not vert else 0.66), INK, q, anchor='c')
        # pin
        cv2.circle(img, (int(x + cw / 2), int(y + 8 * ts)), int(12 * ts), (CORAL * q + img[int(y), int(x)] * 0).tolist(), -1, cv2.LINE_AA)
        if i == 2 and t > T_REVERT - 0.1:
            sticker(img, xs[i], ys[i], 0.85 * ts, q, -0.25, t - T_REVERT + 0.1, "REVERTED")
    if t > T_SUN2 - 0.1:
        q = sstep(T_SUN2 - 0.1, T_SUN2 + 0.15, t) * o
        chip(img, "SUN 9:04 AM", W / 2, H * (0.64 if not vert else 0.60), 60 * ts, RED, WHITE, q, T_SUN2 - 0.1, t)

def bridge2_ui(img, t, W, H, ts, vert):
    if not (S["BRIDGE2"]['s'] - 0.2 < t < S["FINAL"]['s'] + 0.1): return
    o = sstep(S["BRIDGE2"]['s'] - 0.2, S["BRIDGE2"]['s'] + 0.2, t) * (1 - sstep(S["FINAL"]['s'] - 0.1, S["FINAL"]['s'] + 0.05, t))
    if not vert: x, y, w, h = W * 0.14, H * 0.10, W * 0.72, H * 0.50
    else: x, y, w, h = W * 0.05, H * 0.14, W * 0.90, H * 0.40
    cmd = "git blame us" if t < T_SHOWED - 0.1 else "git blame us"
    typed = K.typed_line("$ git blame us", t, T_CMD - 0.1, 10)
    lines = [("# no side, no alibi", WHITE * 0.5), ("", None), (typed, TEAL)]
    if t > T_SHOWED - 0.1:
        n = int(clamp((t - T_SHOWED + 0.1) / 1.2) * 5)
        for i in range(n): lines.append((f"him   line {40 + i * 3}", CORAL))
    editor(img, x, y, w, h, [l[0] if l[1] is not None else l[0] for l in lines], o, ts, fs=(46 if not vert else 44) * ts, title="terminal",
           cursor=(2, len(typed)), t=t)
    if t > T_GB - 0.1:
        q = sstep(T_GB - 0.1, T_GB + 0.1, t) * o
        label(img, "GIT BLAME.", W / 2, y + h + 90 * ts, (110 if not vert else 96) * ts, WHITE, q, F_DISP)

def outro_ui(img, t, W, H, ts, vert):
    if t < T_REMOVED - 0.4 or t > T_END + 0.3: return
    o = sstep(T_REMOVED - 0.4, T_REMOVED, t) * (1 - sstep(T_END, T_END + 0.3, t))
    cw = W * (0.6 if not vert else 0.9); ch = 170 * ts; y = H * 0.24
    panel(img, W / 2 - cw / 2, y, cw, ch, hexc('241f3a'), o, r=int(24 * ts), border=CORAL)
    label(img, f"{HIM} was removed as a collaborator", W / 2, y + ch / 2, (48 if not vert else 42) * ts, WHITE, o, F_DISPB, sh=0)
    if t > T_SAVED - 0.1:
        q = sstep(T_SAVED - 0.1, T_SAVED + 0.1, t) * o
        chip(img, "Changes saved", W / 2, y + ch + 110 * ts, 62 * ts, GREEN, INK, q, T_SAVED - 0.1, t)
        check(img, W / 2 - text_w("Changes saved", F_DISP, int(62 * ts)) / 2 - 70 * ts, y + ch + 110 * ts, 40 * ts, GREEN, q)

# ---------------------------------------------------------------- frame
def render_scene(t, SW, SH, vert):
    G = grid(SW, SH); ph = phase(t)
    if ph == "chorus":
        k, a, b = chorus_at(t)
        img = K.kaleido(G, t, 1.1) * 0.6 + bg_chorus(G, t, k) * 0.55 if k == 2 else bg_chorus(G, t, k)
    elif ph == "receipts":
        img = bg_receipts(G, t)
    else:
        img = bg_night(G, t)
        if ph == "v1" and t > T_BURN:   # prod burning: warm the room
            img += CORAL * 0.10 * sstep(T_BURN, T_BURN + 0.8, t) * (1 - sstep(S["PRE1"]['s'] - 0.4, S["PRE1"]['s'], t))
    return img

def render_frame(t, W=1920, H=1080, fi=0):
    vert = H > W; ts = min(W, H) / 1080
    SW, SH = (W * 2 // 3) // 2 * 2, (H * 2 // 3) // 2 * 2
    sc = render_scene(t, SW, SH, vert)
    img = cv2.resize(np.clip(sc, 0, 1.4).astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR)
    img = img / (1 + np.maximum(img - 0.85, 0))
    ph = phase(t); clean = C.STATE["clean"]
    intro_ui(img, t, W, H, ts, vert)
    blame_view(img, t, W, H, ts, vert)
    pre_ui(img, t, W, H, ts, vert)
    chorus_ui(img, t, W, H, ts, vert)
    v2_ui(img, t, W, H, ts, vert)
    receipts_ui(img, t, W, H, ts, vert)
    bridge2_ui(img, t, W, H, ts, vert)
    outro_ui(img, t, W, H, ts, vert)
    if not clean:
        if ph in ("chorus",): img *= 1 - 0.35 * C.post(W, H).bot
        skip = lambda L: L['text'] in ("Git blame.",)
        C.overlay_lyrics(img, t, W, H, TM, active=hexc('ffd27a'), glow=CORAL, skip=skip)
        C.subscribe_pill(img, t, W, H, S["V2"]['s'] - 7.5, 5.5)
        C.end_screen(img, t, W, H, T_END, DUR - T_END, "Changes saved.", sub_line="Subscribe for a new song every week", title="Git Blame", accent=CORAL)
    fl = 0.0
    for a, b, k in CHORUS:
        if 0 <= t - a < 1.2: fl += 0.5 * math.exp(-(t - a) * 5)
    gl = 0.0
    if 0 <= t - T_REVERT < 0.25: gl += 0.7
    if 0 <= t - T_LOCKED < 0.2: gl += 0.4
    if 0 <= t - T_BURN < 0.3: gl += 0.3
    return C.finish(img, t, fi, DUR, flash=fl, flash_col=WHITE * 0.9, glitch_amt=gl, ca=0.002)
