"""Deployed on a Friday — a beach-sunset outage.

A coastal palette (turquoise sea, coral sunset, sand) with a tide that rises in every chorus and goes out in the last.
Intro: a flip clock hits 4:59 PM FRI, a big green MERGE button: "Ship it". V1: the PR with no ticket, no test, no
second pair of eyes, and a green check that lies; the pager starts buzzing. Chorus: the dashboard turns red as the
sunset while the tide rolls over it; ROLLBACK and a life ring. V2: the boardwalk lights up like Slack, NULL where the
money should be, a dead-letter queue stacking like shells, "VP is typing…". Bridge: low tide in the parking lot,
one bar of signal. V3: revert the revert, a crawling pipeline, the graph comes back green. Final: the tide goes out,
"blameless" postmortem. Outro: Root cause: me. 4:59.
"""
import os, math
import numpy as np, cv2
from studio import core as C
from studio import kit as K
from studio.core import (sstep, ease_out, ease_io, win, lerp, hexc, clamp, sprite, blit, text_w, shadow,
                         F_INTER, F_DISP, F_DISPB, F_MONO, F_MONOB, WHITE)
from studio.kit import panel, label, bubble, grid, vgrad, ssa, desat, sticker, check, INK, editor, chip, fill_poly

HERE = os.path.dirname(os.path.abspath(__file__))
TM = C.Timing(HERE)
DUR = TM.duration
LINES = TM.lines
TM.stamps = []; TM.stamp_word = None
def lt(sub, nth=0):
    try: return TM.line_t(sub, nth)
    except Exception: return 1e9
def sec(n): return TM.section(n)
def bp(t, k=7.0): return TM.beat_pulse(t, k)
def lines_in(sn): return [L for L in LINES if L['sec'] == sn]

SEA = hexc('11b5c4'); DEEP = hexc('0a4f78'); CORAL = hexc('ff6b5b'); PEACH = hexc('ffb48a'); SAND = hexc('f2d2a2')
SUN = hexc('ffd34e'); NIGHT = hexc('101a3a'); PINKS = hexc('ff8fb1'); RED = hexc('ff3346'); GREEN = hexc('28d17c')
LILAC = hexc('b79cff'); FOAM = hexc('eafcff'); SLACKP = hexc('4a154b')

S = {n: sec(n) for n in ("V1", "PRE1", "CH1", "V2", "PRE2", "CH2", "BRIDGE", "V3", "FINAL", "OUTRO")}
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
    if t < S["V3"]['s']: return "bridge"
    if t < S["FINAL"]['s']: return "v3"
    return "outro"

T_459 = lt("Four fifty-nine", 0); T_SHIP = lt("Ship it")
T_LAPTOP = lt("laptop half shut"); T_CHANGE = lt("One little change"); T_TICKET = lt("No ticket"); T_GREEN = lt("Green check")
T_COFFEE = lt("Coffee gone cold"); T_MERGE = lt("Merge to main"); T_WIN = lt("Windows down"); T_PAGER = lt("Pager on my hip")
T_SLACK = lt("Slack lighting"); T_ANYONE = lt("Anyone change"); T_NULL = lt("Null in the column"); T_ROWS = lt("Ten thousand rows")
T_RETRY = lt("Retry, retry"); T_DEAD = lt("Dead letters"); T_VP1 = lt("VP typing, VP stopped"); T_VP2 = lt("there it dropped")
T_LOW = lt("Low tide"); T_SHORT = lt("Every shortcut"); T_PARK = lt("parking lot"); T_BAR = lt("One bar")
T_REV = lt("Revert the revert"); T_PIPE = lt("Pipeline crawling"); T_CACHE = lt("Cache still warm"); T_FLUSH = lt("Flush it")
T_GRAPH = lt("Graph dips"); T_GOG = lt("Green on green"); T_CLOSE = lt("Close the laptop"); T_QUICK = lt("quick question")
T_ROOT = lt("Root cause"); T_459b = LINES[-1]['s']
T_END = max(LINES[-1]['e'] + 1.0, DUR - 6.5)

# ---------------------------------------------------------------- beach
def tide_level(t):
    """0 = low, 1 = high (water covers the bottom third)."""
    c = chorus_at(t)
    if c:
        k, a, b = c
        if k < 2: return 0.35 + 0.55 * ease_io((t - a) / (b - a) * 1.4)
        return 0.9 - 0.75 * ease_io((t - a) / (b - a))
    ph = phase(t)
    if ph == "bridge": return 0.05
    if ph == "outro": return 0.12
    return 0.3

def bg_beach(G, t, mood=0.0, night=0.0):
    """mood 0 = golden hour, 1 = red sunset, night = boardwalk at night."""
    top = lerp(hexc('3a6fd8'), hexc('4a1f6e'), mood); mid = lerp(PEACH, CORAL, mood); hz = 0.10
    sky = vgrad(G, top, CORAL * 0.8, mid, 0.40)
    sky = sky * (1 - night) + vgrad(G, NIGHT, hexc('2b1b4f')) * night
    X, Y = G['X'], G['Y']
    sun = np.exp(-(X ** 2 + (Y - hz + 0.06) ** 2) * 20) * (1 - night)
    sky += lerp(SUN, CORAL, mood) * (1.0 * sun)[..., None]
    img = sky
    # sea from the horizon down
    sea_mask = (Y > hz).astype(np.float32)[..., None]
    depth = np.clip((Y - hz) * 2.2, 0, 1)[..., None]
    sea = lerp(SEA, DEEP, 0.3) * (1 - depth) + DEEP * depth * 0.9
    sea = sea * (1 - night * 0.6) + lerp(CORAL, RED, mood) * 0.25 * np.exp(-(X ** 2) * 6)[..., None] * (1 - depth) * (1 - night)
    waves = 0.5 + 0.5 * np.sin((Y - hz) * 120 / np.maximum(Y - hz, 0.02) ** 0.2 + np.sin(X * 6 + t) * 2 - t * 2)
    sea += FOAM * (0.08 * ssa(0.85, 1.0, waves) * (Y > hz))[..., None]
    img = img * (1 - sea_mask) + sea * sea_mask
    # sand + the tide line
    lvl = tide_level(t)
    shore = 0.62 - 0.22 * lvl + 0.012 * np.sin(X * 9 + t * 1.6)
    sand_m = ssa(-0.004, 0.004, Y - shore)[..., None]
    sand = vgrad(G, SAND, SAND * 0.8) * (1 - night * 0.65)
    img = img * (1 - sand_m) + sand * sand_m
    foam = np.exp(-((Y - shore) / 0.008) ** 2)
    img += FOAM * (0.6 * foam * (1 - night * 0.5))[..., None]
    if night > 0:   # boardwalk lights
        for i in range(14):
            x = -0.9 + i * 0.14; y = 0.02 + 0.015 * math.sin(i)
            on = 0.6 + 0.4 * math.sin(t * 6 + i * 1.3)
            img += lerp(SUN, PINKS, (i % 3) / 2) * (0.5 * night * on * np.exp(-((X - x) ** 2 + (Y - y) ** 2) * 900))[..., None]
    return img

# ---------------------------------------------------------------- UI
def intro_ui(img, t, W, H, ts, vert):
    if t > S["V1"]['s'] + 5.4: return
    a = sstep(T_459 - 0.6, T_459, t) * (1 - sstep(T_LAPTOP - 0.6, T_LAPTOP - 0.1, t))
    if a <= 0.01: return
    cy = H * (0.30 if not vert else 0.30)
    digs = "4:59"; fs = int((200 if not vert else 190) * ts); tw = int(fs * 0.72); th = int(fs * 1.2); gap = int(16 * ts)
    widths = [tw if c != ":" else int(fs * 0.28) for c in digs]; x = W / 2 - (sum(widths) + gap * 3) / 2
    for c, ww in zip(digs, widths):
        if c == ":":
            for dy in (-0.18, 0.18): cv2.circle(img, (int(x + ww / 2), int(cy + dy * fs)), int(fs * 0.06), (WHITE * a).tolist(), -1, cv2.LINE_AA)
        else:
            panel(img, x, cy - th / 2, ww, th, hexc('1c2433'), a, r=int(ww * 0.12))
            cv2.line(img, (int(x), int(cy)), (int(x + ww), int(cy)), (INK * a).tolist(), max(2, int(4 * ts)))
            blit(img, sprite(c, F_DISP, fs), x + ww / 2, cy, SUN, a, anchor='c')
        x += ww + gap
    label(img, "PM  ·  FRIDAY", W / 2, cy + th / 2 + 60 * ts, 60 * ts, WHITE, a, F_DISP)
    if t > T_SHIP - 0.2:
        k = sstep(T_SHIP - 0.2, T_SHIP, t) * a
        press = math.exp(-max(0, t - T_SHIP - 0.4) * 6) if t > T_SHIP + 0.4 else 0
        fs2 = int(60 * ts); lab = "MERGE TO MAIN"; bw = text_w(lab, F_DISP, fs2) + 120 * ts; bh = fs2 * 1.9
        by = cy + th / 2 + 140 * ts
        C._pill(img, W / 2 - bw / 2, by + 8 * ts, bw, bh, INK, 0.6 * k)
        C._pill(img, W / 2 - bw / 2, by + press * 6 * ts, bw, bh, GREEN, k)
        blit(img, sprite(lab, F_DISP, fs2), W / 2, by + press * 6 * ts + bh / 2, INK, k, anchor='c')

def v1_ui(img, t, W, H, ts, vert):
    if not (T_LAPTOP - 0.6 < t < S["PRE1"]['s'] + 0.1): return
    a = sstep(T_LAPTOP - 0.6, T_LAPTOP - 0.1, t) * (1 - sstep(S["PRE1"]['s'] - 0.2, S["PRE1"]['s'] + 0.1, t))
    if not vert: x, y, w, h = W * 0.20, H * 0.06, W * 0.60, H * 0.56
    else: x, y, w, h = W * 0.05, H * 0.11, W * 0.90, H * 0.46
    panel(img, x, y, w, h, hexc('fbfaf6'), a, r=int(26 * ts))
    fsT = int((52 if not vert else 48) * ts)
    blit(img, sprite("PR #4059  one little change", F_DISP, fsT), x + 40 * ts, y + 34 * ts, INK, a)
    rows = [(T_TICKET, "ticket", False), (T_TICKET + 0.6, "tests", False), (T_TICKET + 1.2, "second pair of eyes", False), (T_GREEN, "all checks passed", True)]
    fs = int(46 * ts)
    for i, (tt, s, ok) in enumerate(rows):
        if t < tt - 0.1: continue
        q = sstep(tt - 0.1, tt + 0.1, t) * a
        yy = y + (130 + i * 92) * ts
        col = GREEN if ok else RED
        cv2.circle(img, (int(x + 70 * ts), int(yy + fs * 0.6)), int(26 * ts), (col * q + img[int(yy), int(x)] * (1 - q)).tolist(), -1, cv2.LINE_AA)
        if ok: check(img, x + 70 * ts, yy + fs * 0.6, 26 * ts, WHITE, q)
        else:
            for d in (-1, 1): cv2.line(img, (int(x + 58 * ts), int(yy + fs * 0.6 - 12 * ts * d)), (int(x + 82 * ts), int(yy + fs * 0.6 + 12 * ts * d)), (WHITE * q + col * (1 - q)).tolist(), max(3, int(5 * ts)), cv2.LINE_AA)
        blit(img, sprite(("no " + s) if not ok else s, F_DISPB, fs), x + 120 * ts, yy, INK, q)
        if ok and t > T_GREEN + 0.8: chip(img, "(lying)", x + 120 * ts + text_w(s, F_DISPB, fs) + 120 * ts, yy + fs * 0.6, 40 * ts, PINKS, INK, q, T_GREEN + 0.8, t)
    if t > T_MERGE - 0.1:
        q = sstep(T_MERGE - 0.1, T_MERGE + 0.1, t) * a
        fs2 = int(54 * ts); lab = "Merged into main"; bw = text_w(lab, F_DISP, fs2) + 100 * ts; bh = fs2 * 1.8
        C._pill(img, x + w / 2 - bw / 2, y + h - bh - 30 * ts, bw, bh, hexc('8250df'), q)
        blit(img, sprite(lab, F_DISP, fs2), x + w / 2, y + h - bh / 2 - 30 * ts, WHITE, q, anchor='c')
    if t > T_PAGER - 0.1:   # pager buzzing
        q = sstep(T_PAGER - 0.1, T_PAGER + 0.1, t) * a
        sh = math.sin(t * 60) * 8 * ts
        pw, ph = 330 * ts, 170 * ts; px = (x + w - pw * 0.6) if not vert else W / 2 - pw / 2; py = y + h - ph * 0.4
        panel(img, px + sh, py, pw, ph, hexc('1a1a22'), q, r=int(22 * ts), border=RED)
        blit(img, sprite("PAGER", F_MONOB, int(38 * ts)), px + sh + pw / 2, py + ph * 0.32, RED, q, anchor='c')
        blit(img, sprite("prod: critical", F_DISPB, int(44 * ts)), px + sh + pw / 2, py + ph * 0.68, WHITE, q, anchor='c')

def pre_ui(img, t, W, H, ts, vert):
    p = pre_at(t)
    if not p: return
    a, b = p; o = sstep(a - 0.05, a + 0.1, t) * (1 - sstep(b - 0.1, b + 0.05, t))
    sh = math.sin(t * 70) * 14 * ts * (0.5 + bp(t, 6))
    pw, ph = (520 if not vert else 620) * ts, (900 if not vert else 1000) * ts * (0.55 if not vert else 0.6)
    px, py = W / 2 - pw / 2 + sh, H * (0.06 if not vert else 0.10)
    panel(img, px, py, pw, ph, hexc('16161d'), o, r=int(60 * ts), border=RED)
    blit(img, sprite("BUZZ", F_DISP, int(110 * ts)), px + pw / 2, py + ph * 0.35, RED, o, anchor='c')
    blit(img, sprite("BUZZ", F_DISP, int(110 * ts)), px + pw / 2, py + ph * 0.62, RED, o * sstep(a + 1.0, a + 1.2, t), anchor='c')
    last = [L for L in LINES if a - 0.1 <= L['s'] < b][-1]['text'] if [L for L in LINES if a - 0.1 <= L['s'] < b] else ""
    tag = "I looked" if "looked" in last else ("I'm cooked" if "cooked" in last else "")
    if tag and t > b - 1.8:
        chip(img, tag, W / 2, py + ph + 70 * ts, 62 * ts, SUN, INK, o, b - 1.8, t)

def chorus_ui(img, t, W, H, ts, vert):
    c = chorus_at(t)
    if not c: return
    k, a, b = c; o = sstep(a - 0.05, a + 0.2, t) * (1 - sstep(b - 0.2, b, t))
    ls = lines_in(["CH1", "CH2", "FINAL"][k])
    def tl(sub):
        h = [L['s'] for L in ls if sub.lower() in L['text'].lower()]
        return h[0] if h else 1e9
    t_roll = tl("Rollback"); t_dash = tl("Dashboard"); t_never = tl("never again"); t_said = tl("Said that last") if k < 2 else tl("See you next")
    t_post = tl("postmortem"); t_prod = tl("Prod")
    # dashboard: red as the sunset (or green again in the final)
    if not vert: x, y, w, h = W * 0.22, H * 0.06, W * 0.56, H * 0.40
    else: x, y, w, h = W * 0.06, H * 0.10, W * 0.88, H * 0.30
    good = k == 2
    q = o
    panel(img, x, y, w, h, hexc('121826'), q * 0.92, r=int(24 * ts))
    blit(img, sprite("prod / revenue" if not good else "prod / revenue (recovered)", F_MONOB, int(38 * ts)), x + 30 * ts, y + 24 * ts, WHITE * 0.85, q)
    pts = []
    for i in range(80):
        u = i / 79
        drop = 0.0
        if not good: drop = sstep(0.35, 0.45, u) * min(1, (t - a) / 2)
        else: drop = sstep(0.2, 0.3, u) * (1 - sstep(0.6, 0.75, u))
        v = 0.75 - 0.6 * drop + 0.05 * math.sin(u * 30 + t * 2)
        pts.append((int(x + 40 * ts + (w - 80 * ts) * u), int(y + h - 30 * ts - (h - 110 * ts) * v)))
    col = RED if not good else GREEN
    cv2.polylines(img, [np.array(pts, np.int32)], False, (col * q).tolist(), max(5, int(9 * ts)), cv2.LINE_AA)
    if t > t_dash - 0.1 and not good:
        img[int(y):int(y + h), int(x):int(x + w)] += RED * 0.12 * q * (0.5 + 0.5 * bp(t, 4))
    big = "I DEPLOYED ON A FRIDAY"
    fsb = int((92 if not vert else 70) * ts)
    while text_w(big, F_DISP, fsb) > W * 0.92: fsb -= 4
    label(img, big, W / 2, y + h + 80 * ts, fsb, WHITE, q * (0.85 + 0.15 * bp(t, 6)), F_DISP)
    if t_prod - 0.1 < t < t_roll - 0.1:
        chip(img, "prod: going under" if not good else "prod: still standing", W / 2, y + h + 190 * ts, 56 * ts, RED if not good else GREEN, WHITE if not good else INK, q, t_prod - 0.1, t)
    if (not good and t_roll - 0.1 < t < t_dash - 0.1) or (good and t_roll - 0.1 < t < t_post - 0.1):
        # life ring
        cx, cy, r = W / 2, y + h + 210 * ts, 70 * ts
        for j in range(8):
            a0 = j * 45 + (t - t_roll) * 120
            cv2.ellipse(img, (int(cx), int(cy)), (int(r), int(r)), a0, 0, 45, ((RED if j % 2 == 0 else WHITE) * q).tolist(), int(r * 0.45), cv2.LINE_AA)
        blit(img, sprite("ROLLBACK", F_DISP, int(56 * ts)), cx + r + 30 * ts, cy - 34 * ts, WHITE, q)
    if good and t > t_post - 0.1 and t < t_never - 0.1:
        chip(img, "postmortem: \"blameless\"  ·  nope", W / 2, y + h + 200 * ts, 52 * ts, LILAC, INK, q, t_post - 0.1, t)
    if t > t_never - 0.1:
        chip(img, "NEVER AGAIN", W / 2, y + h + 200 * ts, 64 * ts, SUN, INK, q, t_never - 0.1, t)
        if t > t_said - 0.1:
            label(img, "(said that last Friday)" if k < 2 else "(see you next Friday)", W / 2, y + h + 300 * ts, 50 * ts, WHITE, q, F_DISPB)

def v2_ui(img, t, W, H, ts, vert):
    if not (S["V2"]['s'] - 0.1 < t < S["PRE2"]['s'] + 0.1): return
    o = sstep(S["V2"]['s'] - 0.1, S["V2"]['s'] + 0.2, t) * (1 - sstep(S["PRE2"]['s'] - 0.2, S["PRE2"]['s'], t))
    if not vert: x, y, w, h = W * 0.18, H * 0.06, W * 0.64, H * 0.58
    else: x, y, w, h = W * 0.05, H * 0.10, W * 0.90, H * 0.48
    if t < T_NULL - 0.1:
        panel(img, x, y, w, h, hexc('1a1d21'), o, r=int(24 * ts))
        panel(img, x, y, w, 80 * ts, SLACKP, o, r=int(24 * ts), shadow_op=0)
        blit(img, sprite("#incident-prod", F_DISPB, int(44 * ts)), x + 30 * ts, y + 14 * ts, WHITE, o)
        msgs = [("ops-bot", "ALERT: checkout error rate 41%"), ("ops-bot", "ALERT: revenue = NULL"), ("VP", "anyone change something?")]
        for i, (who, m) in enumerate(msgs):
            tt = T_SLACK + i * 0.9 if i < 2 else T_ANYONE
            if t < tt - 0.1: continue
            q = sstep(tt - 0.1, tt + 0.1, t) * o; yy = y + (120 + i * 120) * ts
            cv2.circle(img, (int(x + 60 * ts), int(yy + 34 * ts)), int(30 * ts), ((CORAL if who == "VP" else SEA) * q).tolist(), -1, cv2.LINE_AA)
            blit(img, sprite(who, F_DISPB, int(40 * ts)), x + 110 * ts, yy, WHITE, q)
            blit(img, sprite(m, F_INTER, int(42 * ts)), x + 110 * ts, yy + 48 * ts, WHITE * 0.9, q)
        if t > T_ANYONE + 1.0:
            chip(img, "*sitting very still*", W / 2, y + h - 60 * ts, 50 * ts, SUN, INK, o, T_ANYONE + 1.0, t)
        return
    if t < T_RETRY - 0.1:
        rows = [("account", "amount")] + [(f"acct_{1040 + i}", "NULL") for i in range(6)]
        panel(img, x, y, w, h, hexc('f7f4ec'), o, r=int(24 * ts))
        for i, (c1, c2) in enumerate(rows):
            yy = y + (40 + i * 70) * ts
            if yy > y + h - 60 * ts: break
            q = o * sstep(T_NULL - 0.1 + i * 0.12, T_NULL + i * 0.12, t)
            blit(img, sprite(c1, F_MONOB, int(42 * ts)), x + 50 * ts, yy, INK, q)
            blit(img, sprite(c2, F_MONOB, int(42 * ts)), x + w * 0.62, yy, RED if c2 == "NULL" else INK, q)
        if t > T_ROWS - 0.1:
            chip(img, "10,000 rows  ·  git blame: me", W / 2, y + h + 60 * ts, 54 * ts, CORAL, WHITE, o, T_ROWS - 0.1, t)
        return
    if t < T_VP1 - 0.1:
        # queue backing up; dead letters stacking like shells
        panel(img, x, y, w, h, hexc('0f2a3d'), o, r=int(24 * ts))
        lab = "retry queue" if t < T_DEAD - 0.1 else "dead-letter queue"
        blit(img, sprite(lab, F_DISP, int(52 * ts)), x + 40 * ts, y + 30 * ts, FOAM, o)
        n = int(clamp((t - T_RETRY) / 4.0) * 28)
        cols = 7; ew, eh = (w - 120 * ts) / cols, 70 * ts
        for i in range(n):
            r, c = divmod(i, cols)
            ex = x + 60 * ts + c * ew; ey = y + h - 40 * ts - (r + 1) * (eh + 12 * ts)
            if ey < y + 110 * ts: break
            panel(img, ex + 6 * ts, ey, ew - 12 * ts, eh, (PEACH if t > T_DEAD - 0.1 else FOAM * 0.9), o, r=int(8 * ts), shadow_op=0.3)
            cv2.line(img, (int(ex + 6 * ts), int(ey)), (int(ex + ew / 2), int(ey + eh * 0.55)), (INK * 0.6 * o).tolist(), max(2, int(3 * ts)), cv2.LINE_AA)
            cv2.line(img, (int(ex + ew - 6 * ts), int(ey)), (int(ex + ew / 2), int(ey + eh * 0.55)), (INK * 0.6 * o).tolist(), max(2, int(3 * ts)), cv2.LINE_AA)
        blit(img, sprite(f"{n * 357:,} waiting", F_MONOB, int(44 * ts)), x + w - 360 * ts, y + 36 * ts, SUN, o)
        return
    # VP typing… stopped… typing… dropped
    panel(img, x, y + h * 0.3, w, h * 0.4, hexc('1a1d21'), o, r=int(24 * ts))
    typing = (T_VP1 - 0.1 < t < T_VP1 + 1.2) or (T_VP2 - 0.1 < t < T_VP2 + 1.0)
    stopped = (T_VP1 + 1.2 <= t < T_VP2 - 0.1)
    if typing:
        for i in range(3):
            yy = y + h * 0.5 - 12 * ts * max(0, math.sin(t * 8 - i))
            cv2.circle(img, (int(x + 90 * ts + i * 44 * ts), int(yy)), int(14 * ts), (WHITE * o).tolist(), -1, cv2.LINE_AA)
        blit(img, sprite("VP is typing…", F_DISPB, int(52 * ts)), x + 250 * ts, y + h * 0.5 - 30 * ts, WHITE, o)
    elif stopped:
        blit(img, sprite("VP stopped typing", F_DISPB, int(52 * ts)), x + 90 * ts, y + h * 0.5 - 30 * ts, WHITE * 0.7, o)
    else:
        blit(img, sprite("VP: \"call me.\"", F_DISPB, int(56 * ts)), x + 90 * ts, y + h * 0.5 - 30 * ts, CORAL, o)

def bridge_ui(img, t, W, H, ts, vert):
    if not (S["BRIDGE"]['s'] - 0.1 < t < S["V3"]['s'] + 0.1): return
    o = sstep(S["BRIDGE"]['s'] - 0.1, S["BRIDGE"]['s'] + 0.4, t) * (1 - sstep(S["V3"]['s'] - 0.2, S["V3"]['s'], t))
    cx, cy = W / 2, H * (0.30 if not vert else 0.30)
    pw, ph = 330 * ts, 560 * ts
    panel(img, cx - pw / 2, cy - ph / 2, pw, ph, hexc('16161d'), o, r=int(50 * ts), border=WHITE * 0.6)
    bars = 1 if t > T_BAR - 0.1 else (2 if t > T_PARK - 0.1 else 3)
    for i in range(4):
        hh = (30 + i * 26) * ts; bx = cx - 70 * ts + i * 42 * ts; by = cy - ph / 2 + 150 * ts
        col = (WHITE if i < bars else WHITE * 0.2) * o
        cv2.rectangle(img, (int(bx), int(by - hh)), (int(bx + 28 * ts), int(by)), col.tolist(), -1)
    blit(img, sprite("1 bar" if bars == 1 else "LTE", F_DISPB, int(48 * ts)), cx, cy - ph / 2 + 210 * ts, WHITE, o, anchor='c')
    blit(img, sprite("parking lot", F_DISPB, int(44 * ts)), cx, cy + 60 * ts, SUN, o * sstep(T_PARK - 0.1, T_PARK + 0.1, t), anchor='c')
    blit(img, sprite("fixing prod", F_DISPB, int(44 * ts)), cx, cy + 130 * ts, WHITE, o * sstep(T_PARK - 0.1, T_PARK + 0.1, t), anchor='c')

def v3_ui(img, t, W, H, ts, vert):
    if not (S["V3"]['s'] - 0.1 < t < S["FINAL"]['s'] + 0.1): return
    o = sstep(S["V3"]['s'] - 0.1, S["V3"]['s'] + 0.2, t) * (1 - sstep(S["FINAL"]['s'] - 0.2, S["FINAL"]['s'], t))
    if not vert: x, y, w, h = W * 0.16, H * 0.06, W * 0.68, H * 0.58
    else: x, y, w, h = W * 0.04, H * 0.10, W * 0.92, H * 0.48
    if t < T_GRAPH - 0.1:
        cmds = [(T_REV, "$ git revert 7f3e1c2   # the revert"), (T_REV + 0.9, "$ git cherry-pick a91b0d4"), (T_REV + 1.6, "$ git push"),
                (T_PIPE, "pipeline: [####------] crawling…"), (T_CACHE, "cache: warm (bad old state)"), (T_FLUSH, "$ flush --all && bounce")]
        lines = []
        for tt, s in cmds:
            if t >= tt - 0.1: lines.append(K.typed_line(s, t, tt - 0.1, 30))
        K.editor(img, x, y, w, h, lines, o, ts, fs=(42 if not vert else 34) * ts, title="parking-lot.sh", bg=hexc('0f1720'), fg=FOAM)
        return
    if t < T_CLOSE - 0.1:
        panel(img, x, y, w, h, hexc('0f1720'), o, r=int(24 * ts))
        pts = []
        for i in range(90):
            u = i / 89
            if u > clamp((t - T_GRAPH) / 2.6): break
            v = 0.7 - 0.5 * sstep(0.15, 0.3, u) * (1 - sstep(0.5, 0.75, u)) + 0.03 * math.sin(u * 40)
            pts.append((int(x + 40 * ts + (w - 80 * ts) * u), int(y + h - 50 * ts - (h - 120 * ts) * v)))
        if len(pts) > 1: cv2.polylines(img, [np.array(pts, np.int32)], False, (GREEN * o).tolist(), max(5, int(9 * ts)), cv2.LINE_AA)
        if t > T_GOG - 0.1:
            chip(img, "all green", W / 2, y + 70 * ts, 60 * ts, GREEN, INK, o, T_GOG - 0.1, t)
        return
    # close the laptop, hear the sea... phone lights up
    if t > T_QUICK - 0.1:
        q = sstep(T_QUICK - 0.1, T_QUICK + 0.1, t) * o
        bubble(img, W / 2, H * 0.30, "quick question 🙂" if False else "quick question?", q, ts, hexc('2f6bff'), fs=int(62 * ts), pop_t=T_QUICK - 0.1, t=t)

def outro_ui(img, t, W, H, ts, vert):
    if t < T_ROOT - 0.3 or t > T_END + 0.4: return
    a = sstep(T_ROOT - 0.3, T_ROOT, t) * (1 - sstep(T_END, T_END + 0.4, t))
    cw, ch = (W * 0.56 if not vert else W * 0.88), 260 * ts; y = H * 0.18
    panel(img, W / 2 - cw / 2, y, cw, ch, hexc('fbfaf6'), a, r=int(28 * ts))
    blit(img, sprite("Root cause:", F_DISP, int(60 * ts)), W / 2, y + ch * 0.32, INK, a, anchor='c')
    blit(img, sprite("me.  (Friday, 4:59 PM)", F_DISP, int(64 * ts)), W / 2, y + ch * 0.68, CORAL, a, anchor='c')

# ---------------------------------------------------------------- frame
def render_scene(t, SW, SH, vert):
    G = grid(SW, SH); ph = phase(t)
    if ph == "chorus":
        k, a, b = chorus_at(t)
        mood = 0.9 if k < 2 else 0.25
        return bg_beach(G, t, mood) * (0.92 + 0.15 * bp(t, 6))
    if ph == "v2": return bg_beach(G, t, 0.5, night=sstep(S["V2"]['s'] - 0.5, S["V2"]['s'] + 1.0, t))
    if ph == "pre": return bg_beach(G, t, 0.7) * (0.85 + 0.25 * bp(t, 8))
    if ph == "bridge": return bg_beach(G, t, 0.4)
    if ph == "v3": return bg_beach(G, t, 0.3 - 0.3 * sstep(T_CLOSE - 0.5, T_CLOSE + 1, t))
    if ph == "outro": return bg_beach(G, t, 0.2)
    return bg_beach(G, t, 0.0)

def render_frame(t, W=1920, H=1080, fi=0):
    vert = H > W; ts = min(W, H) / 1080
    SW, SH = (W * 2 // 3) // 2 * 2, (H * 2 // 3) // 2 * 2
    sc = render_scene(t, SW, SH, vert)
    img = cv2.resize(np.clip(sc, 0, 1.4).astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR)
    img = img / (1 + np.maximum(img - 0.85, 0))
    clean = C.STATE["clean"]
    intro_ui(img, t, W, H, ts, vert); v1_ui(img, t, W, H, ts, vert); pre_ui(img, t, W, H, ts, vert)
    chorus_ui(img, t, W, H, ts, vert); v2_ui(img, t, W, H, ts, vert); bridge_ui(img, t, W, H, ts, vert)
    v3_ui(img, t, W, H, ts, vert); outro_ui(img, t, W, H, ts, vert)
    if not clean:
        img *= 1 - 0.45 * C.post(W, H).bot
        C.overlay_lyrics(img, t, W, H, TM, active=SUN, glow=CORAL, skip=lambda L: L['sec'] == "INTRO" or L['s'] > T_END)
        C.subscribe_pill(img, t, W, H, lines_in("CH2")[-1]['e'] + 1.0, 5.5)
        C.end_screen(img, t, W, H, T_END, DUR - T_END, "See you next Friday.", sub_line="Subscribe for a new song every week", title="Deployed on a Friday", accent=CORAL)
    fl = 0.0
    for a, b, k in CHORUS:
        if 0 <= t - a < 1.2: fl += 0.45 * math.exp(-(t - a) * 5)
    gl = 0.0
    if 0 <= t - T_PAGER < 0.3: gl += 0.4
    for a, b in PRES:
        if a <= t < b: gl += 0.15 * bp(t, 10)
    return C.finish(img, t, fi, DUR, flash=fl, flash_col=SUN * 0.8, glitch_amt=gl, ca=0.0018)
