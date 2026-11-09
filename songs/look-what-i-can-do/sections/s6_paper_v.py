"""S6 for the 9:16 Short B ("Net worth"): the same Daily Standup issue, re-laid out for a tall page (1080x1920 design units).

The 16:9 film keeps using s6_paper.py untouched; this module only imports its timing, assets and helpers and re-places
every figure for a portrait sheet: two-column spreads become stacked (clipping on top, chart below), the org chart is
narrowed, and all type is >= 34 px. Readable things stay inside the Shorts safe zone (x 64..950, y < 1497); the paper
itself runs edge to edge. The cream is toned down in-render (like master_v3.py) with a soft stage light on the figure.
  render_frame(t, W=1080, H=1920)"""
import math
import numpy as np, cv2
import s6_paper as P
from s6_paper import (T_SO, T_BACK, T_POST2, T_DOOM, T_SUMM, T_PANIC, T_ROOM, T_TEN, T_MAC, T_MINIS, T_FOR, T_REASONS,
                      T_CANT, T_AGENTS, T_FORMED, T_COMPANY, T_ME, T_EMPL, T_SONG, T_END, T_EARTH, T_GAVE0, T_GAVE, T_MYSELF,
                      T_BRAND, T_TRIPLED, T_MY, T_WORTH, P_BACK, P_TOM, P_MINIS, BOX_BACK, BOX_TOM, BOX_MINIS, ROOM, PIE, L1,
                      SW, NSWARM, JOBS, FS, SHOT_CEO, SHOT_CAR, CLOCK, _img, _has, avatar, photo, tile, typed_rows, mini, axes)
from s6_ink import *          # noqa: F401,F403
from studio.core import sstep, ease_out, ease_io, clamp, lerp, hexc

DW, DH = 1080, 1920
XL, XR, YB = 64, 950, 1490          # safe zone for anything that must be read (right 12 %, bottom 22 % clear)
CX = (XL + XR) / 2                  # 507: centre of the readable column

class VCv(Cv):
    def __init__(s, img, W, H):
        super().__init__(img, W, H)
        s.DW, s.DH = DW, DH; s.k = W / DW; s.cx, s.cy = DW / 2, DH / 2
        s.box = (XL, 296, XR - XL, YB - 296)

# ---------------------------------------------------------------- furniture
def masthead(cv):
    text(cv, "THE DAILY STANDUP", 540, 150, F_MAST, 76, INK, 1.0, 'c', 'm', track=2)
    stroke(cv, [(XL - 16, 200), (1016, 200)], INK, 2.2); stroke(cv, [(XL - 16, 207), (1016, 207)], INK, 1.0)
    text(cv, "THURSDAY, OCT. 30", XL, 240, F_SANSM, 34, INK2, 1.0, 'l', 'm', track=1)
    text(cv, "PRICE: 1 SUBSCRIPTION", XR, 240, F_SANSM, 34, INK2, 1.0, 'r', 'm', track=1)
    stroke(cv, [(XL - 16, 270), (1016, 270)], INK, 1.4)

_GREEK = np.random.default_rng(31).uniform(0.55, 1.0, 200)
def greek(cv):
    """the rest of the page below the safe zone: columns of body copy (texture only, nothing to read)"""
    stroke(cv, [(XL - 16, 1528), (1016, 1528)], RULE, 1.4)
    cols = [(XL, 290), (XL + 320, 290), (XL + 640, 312)]
    for ci, (x, w) in enumerate(cols):
        rect(cv, x, 1556, w * 0.78, 22, BAR, 0.75)
        rect(cv, x, 1588, w * 0.52, 22, BAR, 0.75)
        for j in range(9):
            y = 1640 + j * 30; f = 1.0 if j % 5 != 4 else 0.55 * _GREEK[ci * 20 + j]
            rect(cv, x, y, w * (f if f < 1 else 0.96 + 0.04 * _GREEK[ci * 20 + j]), 11, GRID, 1.0)
        if ci < 2: stroke(cv, [(x + w + 15, 1552), (x + w + 15, 1900)], GRID, 1.2)

def clock(cv, t):
    clk = "4:01 P.M."
    for tt, lab in CLOCK:
        if t >= tt: clk = lab; break
    x, y, w, h = cv.box
    text(cv, clk, x + w, y + 24, F_MONO, 36, RED, 1.0, 'r', 'm')

def frame(cv, kicker, title, source=None):
    """kicker, a headline wrapped to at most two lines, hairline; returns the chart area"""
    x, y, w, h = cv.box
    text(cv, kicker, x, y + 24, F_SANS, 36, RED, 1.0, 'l', 'm', track=3)
    fs = 60
    rows = wrap(title, F_HEAD, fs, w)
    while len(rows) > 2 and fs > 44: fs -= 2; rows = wrap(title, F_HEAD, fs, w)
    lh = fs * 1.08
    for i, r in enumerate(rows): text(cv, r, x, y + 88 + i * lh, F_HEAD, fs, INK, 1.0, 'l', 'm')
    yr = y + 88 + (len(rows) - 1) * lh + fs * 0.62
    stroke(cv, [(x, yr), (x + w, yr)], RULE, 1.6)
    if source: text(cv, source, x, y + h - 16, F_SANSM, 34, MUTE, 1.0, 'l', 'm')
    top = yr + 30; bot = y + h - (60 if source else 20)
    return (x, top, w, bot - top)

# ================================================================ FIG. 20: the two posts
def fig_posts(cv, t):
    x0, top, w, ch = frame(cv, "FIG. 20", "Humanity's outlook, according to my last two posts", "Source: @adita_zzz on X")
    s = 0.60; px, py = x0 + 20, top + 18
    kb1 = sstep(T_SO - 0.06, T_SO + 0.22, t); kb2 = sstep(T_BACK - 0.12, T_BACK + 0.10, t)
    clipping(cv, P_BACK, _img(P_BACK), px, py, s, 1.0, marks=[BOX_BACK[0] + (kb1,), BOX_BACK[1] + (kb2,)])
    kl = ease_out((t - (T_POST2 - 0.02)) / 0.20)
    if kl > 0:
        kv = sstep(T_DOOM - 0.08, T_DOOM + 0.16, t)
        # laid squarely on post 1 (a 12 px step): offset +50 left post 1's avatar peeking out half-covered at the left
        clipping(cv, P_TOM, _img(P_TOM), px + 12, py + 6 - 40 * (1 - kl), s, min(1.0, kl * 3), marks=[BOX_TOM + (kv,)])
    # outlook chart, under the clippings (horizontal: three levels, post 1 / post 2 along x)
    ax, ar = x0 + 236, x0 + w - 20
    ytop = py + 672 * s + 150; ymid = ytop + 120; ybot = ymid + 120
    text(cv, "OUTLOOK", ax - 22, ytop - 64, F_SANS, 34, MUTE, 1.0, 'r', 'm', track=3)
    for yy, lab, col in ((ytop, "so back", INK), (ymid, "meh", MUTE), (ybot, "doomed", RED)):
        stroke(cv, [(ax, yy), (ar, yy)], GRID, 1.4)
        text(cv, lab, ax - 22, yy, F_SANS, 46, col, 1.0, 'r', 'm')
    stroke(cv, [(ax, ytop - 30), (ax, ybot + 24)], INK, 2.2)
    p0 = (ax, ymid); p1 = (ax + 260, ytop); p2 = (ax + 560, ybot)
    for xx, lab in ((p1[0], "post 1"), (p2[0], "post 2")):
        text(cv, lab, xx, ybot + 58, F_SANSM, 34, MUTE, 1.0, 'c', 'm')
    k1 = ease_out((t - (T_SO - 0.08)) / 0.30)
    k2 = clamp((t - (T_DOOM - 0.10)) / 0.26) ** 1.6
    circle(cv, p0[0], p0[1], 9, INK2)
    if k1 > 0: stroke(cv, [p0, (lerp(p0[0], p1[0], k1), lerp(p0[1], p1[1], k1))], INK, 5)
    if k1 > 0.98 and k2 <= 0:
        pop = 1 + 0.5 * math.exp(-(t - T_SO - 0.22) * 9) if t > T_SO + 0.22 else 1.0
        circle(cv, p1[0], p1[1], 13 * pop, PEN); circle(cv, p1[0], p1[1], 24, PEN, 0.5, wd=2.5)
    if k2 > 0:
        e = (lerp(p1[0], p2[0], k2), lerp(p1[1], p2[1], k2))
        stroke(cv, [p1, e], RED, 5); circle(cv, p1[0], p1[1], 9, INK); circle(cv, e[0], e[1], 13, RED)
        if k2 >= 1: circle(cv, p2[0], p2[1], 25 + 6 * math.exp(-(t - T_DOOM - 0.16) * 7), RED, 0.6, wd=2.5)

# ================================================================ FIG. 21: the bot's summary of the panic
def fig_summary(cv, t):
    x0, top, w, ch = frame(cv, "FIG. 21", "The panic in the room, summarized by a bot", "Source: a bot")
    bx, by, bw, bh = x0 + 10, top + 16, w - 20, 394
    rect(cv, bx + 10, by + 12, bw, bh, INK, 0.10, r=18)
    tile(cv, bx, by, bw, bh)
    sx, sy = bx + 52, by + 54; r1, r2 = 15, 4.5
    fill(cv, [(sx + (r1 if i % 2 == 0 else r2) * math.cos(-math.pi / 2 + i * math.pi / 4),
               sy + (r1 if i % 2 == 0 else r2) * math.sin(-math.pi / 2 + i * math.pi / 4)) for i in range(8)], RED)
    text(cv, "SUMMARY", sx + 30, sy, F_SANS, 34, RED, 1.0, 'l', 'm', track=3)
    text(cv, "1 source: the room", bx + bw - 40, sy, F_SANSM, 34, MUTE, 1.0, 'r', 'm')
    stroke(cv, [(bx + 40, by + 100), (bx + bw - 40, by + 100)], RULE, 1.6)
    fs = 64; lh = fs * 1.12
    rows = wrap("Everyone in the room is panicking.", F_HEAD, fs, bw - 100)
    n = int(len(" ".join(rows)) * clamp((t - (T_SUMM - 0.05)) / 0.85))
    vis = typed_rows(rows, n); y0 = by + 156
    for i, r in enumerate(vis): text(cv, r, bx + 46, y0 + i * lh, F_HEAD, fs, INK, 1.0, 'l', 'm')
    t3a, t3b = T_ROOM - 0.62, T_ROOM - 0.18
    s3 = "This includes you."
    n3 = int(len(s3) * clamp((t - t3a) / (t3b - t3a)))
    y3 = y0 + len(rows) * lh + 26
    if n3 > 0: text(cv, s3[:n3], bx + 46, y3, F_HEAD, fs, RED, 1.0, 'l', 'm')
    typing = (T_SUMM - 0.05 < t < T_SUMM + 0.95) or (t3a < t < t3b + 0.5)
    if (T_SUMM - 0.25 < t < t3b + 0.6) and (typing or int(t * 3.2) % 2 == 0):
        if t < t3a: last = vis[-1] if vis else ""; cyy = y0 + (max(1, len(vis)) - 1) * lh; cxx = bx + 46 + tw(last, F_HEAD, fs)
        else: cxx = bx + 46 + tw(s3[:n3], F_HEAD, fs); cyy = y3
        rect(cv, cxx + 8, cyy - fs * 0.42, 5, fs * 0.74, RED if t >= t3a else INK)
    pen_text(cv, "rude.", bx + 46 + tw(s3, F_HEAD, fs) + 30, y3 + 4, 62, (t - (T_ROOM - 0.06)) / 0.26)
    # the room: 5 x 3 pictogram, the counter on its header row
    hy = by + bh + 44
    sp, rsp, ss = 164, 142, 0.92
    gx = CX - 2 * sp; gy = hy + 112
    text(cv, "THE ROOM", x0 + 10, hy, F_SANS, 34, MUTE, 1.0, 'l', 'm', track=3)
    order = sorted(range(14), key=lambda i: (ROOM[i][0] - 2) ** 2 + (ROOM[i][1] - 1) ** 2 * 2.2 + 0.01 * i)
    npan = 0
    for i, (c, r) in enumerate(ROOM):
        you = i == 14
        tf = (T_ROOM - 0.40) if you else (T_PANIC - 0.10 + order.index(i) * 0.05)
        k = sstep(tf, tf + 0.10, t)
        if k > 0.5: npan += 1
        x = gx + c * sp; y = gy + r * rsp
        jx = k * 3.4 * math.sin(t * 57 + i * 1.9); jy = k * 2.0 * math.sin(t * 43 + i * 2.7)
        col = (PEN if you else BAR) * (1 - k) + RED * k
        person(cv, x + jx, y + jy, ss, col)
        if k > 0:
            pop = ease_out((t - tf) / 0.14)
            text(cv, "!", x + jx + 46 * ss, y - 58 * ss + jy, F_NUM, 44 * (0.6 + 0.4 * pop), RED, k, 'c', 'm')
        if you: text(cv, "you", x, y + 46 * ss + 36, F_SANS, 44, PEN, 1.0, 'c', 'm')
    text(cv, f"{npan} of 15 panicking", x0 + w - 10, hy, F_NUMB, 42, RED if npan else INK, 1.0, 'r', 'm')

# ================================================================ FIG. 22: ten Mac minis, for reasons
def fig_minis(cv, t):
    x0, top, w, ch = frame(cv, "FIG. 22", "Mac minis acquired this week, by reason")
    x, y, bw_, h = cv.box
    sw_ = text(cv, "Source: ", x, y + h - 16, F_SANSM, 34, MUTE, 1.0, 'l', 'm')
    rect(cv, x + sw_ + 2, y + h - 34, 196, 36, INK, 1.0)
    s = 0.64; px, py = x0 + 14, top + 16
    kmac = sstep(T_MAC - 0.10, T_MAC + 0.12, t); kmin = sstep(T_MINIS - 0.10, T_MINIS + 0.10, t)
    kfor = sstep(T_FOR - 0.02, T_REASONS + 0.05, t)
    clipping(cv, P_MINIS, _img(P_MINIS), px, py, s, 1.0, marks=[BOX_MINIS[0] + (kmac,), BOX_MINIS[1] + (kmin,), BOX_MINIS[2] + (kfor,)])
    kr = ease_out((t - (T_CANT - 0.06)) / 0.20)
    if kr > 0:
        bx0, by0, bx1, by1 = BOX_MINIS[2]
        rx0, ry0 = px + (bx0 - 10) * s, py + (by0 - 8) * s; rw, rh = (bx1 - bx0 + 20) * s, (by1 - by0 + 14) * s
        rect(cv, rx0, ry0, rw * kr, rh, INK, 1.0)
        if kr > 0.9: text(cv, "REDACTED", rx0 + rw / 2, ry0 + rh / 2 + 1, F_MONO, 34, CREAM, sstep(0.9, 1.0, kr), 'c', 'm')
    # the stack of ten (right column)
    mw, mh, gap = 300, 38, 6; sx0 = x0 + w - mw - 10; base = top + 880
    n = 0
    for i in range(10):
        ti = T_TEN - 0.04 + i * 0.112
        k = ease_out((t - ti) / 0.13)
        if k <= 0: continue
        n += 1
        yy = base - (i + 1) * (mh + gap) - 70 * (1 - k)
        mini(cv, sx0, yy, mw, mh, min(1.0, k * 2))
    if n:
        kt = ease_out((t - (T_TEN - 0.04 + (n - 1) * 0.112)) / 0.13)
        ktop = base - (n - 1 + kt) * (mh + gap)
        text(cv, str(n), sx0 + mw / 2, ktop - 72, F_NUM, 100, INK if n < 10 else RED, 1.0, 'c', 'm')
    text(cv, "Mac minis", sx0 + mw / 2, base + 34, F_SANS, 34, MUTE, sstep(T_TEN - 0.1, T_TEN + 0.1, t), 'c', 'm', track=1)
    # share of reasons (left column): pie, then its redacted legend
    ky = top + 310
    kk = sstep(T_FOR - 0.10, T_FOR + 0.15, t)
    text(cv, "SHARE OF REASONS", x0 + 10, ky, F_SANS, 34, MUTE, kk, 'l', 'm', track=3)
    pcx, pcy, R = x0 + 140, ky + 170, 120
    sweep = ease_out((t - (T_FOR - 0.02)) / 0.65)
    a = -math.pi / 2
    for i, (pct, col, bw) in enumerate(PIE):
        span = 2 * math.pi * pct / 100 * sweep
        if span > 0.002: wedge(cv, pcx, pcy, R * 0.52, R, a, a + span, col, 1.0)
        a += span
    lx, lr = x0 + 10, sx0 - 60
    for i, (pct, col, bw) in enumerate(PIE):
        ti = T_FOR + 0.08 + i * 0.09
        k = sstep(ti, ti + 0.16, t)
        if k <= 0: continue
        yy = ky + 340 + i * 60
        rect(cv, lx, yy - 15, 30, 30, col, k, r=4)
        rect(cv, lx + 48, yy - 17, bw * 0.78 * ease_out((t - ti) / 0.22), 34, INK, k)
        text(cv, f"{pct}%", lr, yy, F_NUMB, 40, INK, k, 'r', 'm')

# ================================================================ FIG. 23: Agents, Inc.
CEO_W, CEO_H = 520, 292
L1X = [120, 330, 575, 830]
def fig_org(cv, t):
    x0, top, w, ch = frame(cv, "FIG. 23", "Org chart: Agents, Inc. (founded today)", "Source: the agents")
    foot = _has(SHOT_CEO)
    cxo = CX + 90                                   # the CEO photo sits right of centre; its label reads to its left
    yc, y1, y2 = top + 170, top + 460, top + 690
    slots = [(cxo, yc)] + [(xx, y1) for xx in L1X]
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
        tau = t - T_AGENTS
        fx = lerp(160, 520, ease_out((tau + 0.10) / 0.40)) + 110 * math.sin(2.4 * tau)
        fy = top + 330 + 60 * math.sin(3.4 * tau + 0.5)
        ph_ = r[1] * 2 * math.pi + tau * (2.2 + 1.2 * r[2]) * (1 if r[3] > 0.35 else -1)
        wx = fx + (60 + 100 * r[4]) * math.cos(ph_); wy = fy + (34 + 70 * r[5]) * math.sin(ph_ * 1.0 + r[2])
        kf = ease_io((t - (T_FORMED - 0.06 + r[6] * 0.22)) / 0.46)
        x = lerp(wx, sx, kf); y = lerp(wy, sy, kf)
        if i < 5:
            s_ = lerp(sz * 0.55, sz, kf) * (0.6 + 0.4 * ka)
            seats.append((x, y, s_, kf, ka))
        else:
            s_ = sz * 0.50 * (0.6 + 0.4 * ka) * (1 - 0.5 * kf)
            op = 1 - sstep(0.75, 1.0, kf)
            if op > 0.01: bot(cv, x, y, s_, RED if seat == 0 else INK2, op)
    kc = ease_out((t - (T_COMPANY - 0.10)) / 0.40)
    ceo_bot = yc + (CEO_H / 2 + 10 if foot else 54)
    yb1 = (ceo_bot + y1 - 66) / 2
    if kc > 0:
        stroke(cv, [(cxo, ceo_bot), (cxo, lerp(ceo_bot, yb1, min(1, kc * 2)))], INK2, 2.4)
        if kc > 0.5:
            u = (kc - 0.5) * 2
            stroke(cv, [(lerp(cxo, L1X[0], u), yb1), (lerp(cxo, L1X[-1], u), yb1)], INK2, 2.4)
            if u > 0.98:
                for xx in L1X: stroke(cv, [(xx, yb1), (xx, y1 - 66)], INK2, 2.4)
    km = ease_out((t - (T_ME - 0.12)) / 0.26)
    yb2 = y2 - 96
    if km > 0:
        for xx in L1X: stroke(cv, [(xx, y1 + 90), (xx, lerp(y1 + 90, yb2, km))], INK2, 2.4)
        if km > 0.7:
            stroke(cv, [(L1X[0], yb2), (L1X[-1], yb2)], INK2, 2.4)
            stroke(cv, [(CX, yb2), (CX, y2 - 66)], INK2, 2.4)
    for i, st in enumerate(seats):
        if st is None: continue
        x, y, s_, kf, ka = st
        ceo = i == 0
        if ceo and foot and kf > 0.9:
            kp = ease_out((kf - 0.9) / 0.1)
            pw, ph = lerp(s_ * 1.2, CEO_W, kp), lerp(s_ * 0.9, CEO_H, kp)
            photo(cv, SHOT_CEO, (t - T_FORMED - 0.25) / 2.75, x - pw / 2, y - ph / 2, pw, ph, kp, base=(CEO_W, CEO_H))
            if kp < 1: bot(cv, x, y, s_, RED, 1 - kp)
        else:
            bot(cv, x, y, s_, RED if ceo else INK2)
        kl = sstep(0.85, 1.0, kf)
        if kl > 0:
            if ceo:
                lx = x - (CEO_W / 2 + 34 if foot else 86)
                text(cv, "CEO", lx, y - 24, F_SANS, 46, RED, kl, 'r', 'm')
                text(cv, "an agent", lx, y + 30, F_ITAL, 50, INK2, kl, 'r', 'm')
            else:
                text(cv, L1[i - 1][0], x, y + 72, F_SANS, 38, INK, kl, 'c', 'm')
    if km > 0:
        crop, m = avatar(); r = 62 * (0.7 + 0.3 * km)
        circle(cv, CX, y2, r + 7, PEN, km)
        if crop is not None: paste(cv, "avatar", crop, CX - r, y2 - r, 2 * r, 2 * r, km, mask=m)
        ke = sstep(T_EMPL - 0.06, T_EMPL + 0.12, t)
        text(cv, "Adita", CX, y2 + 108, F_SANS, 50, PEN, km, 'c', 'm')
        text(cv, "employee", CX, y2 + 172, F_SANSM, 42, MUTE, km * (1 - ke), 'c', 'm')
        if ke > 0:
            text(cv, "EMPLOYEE OF THE YEAR", CX, y2 + 172, F_SANS, 46, RED, ke, 'c', 'm', track=3)
            kr = ease_out((t - (T_EMPL - 0.02)) / 0.22); rx, ry = CX - 132, y2 + 2
            sc = kr * (1 + 0.25 * math.exp(-(t - T_EMPL) * 8) * (t > T_EMPL))
            fill(cv, [(rx - 18 * sc, ry + 10 * sc), (rx - 34 * sc, ry + 66 * sc), (rx - 14 * sc, ry + 56 * sc), (rx - 2 * sc, ry + 72 * sc), (rx + 4 * sc, ry + 14 * sc)], RED)
            fill(cv, [(rx + 18 * sc, ry + 10 * sc), (rx + 34 * sc, ry + 66 * sc), (rx + 14 * sc, ry + 56 * sc), (rx + 2 * sc, ry + 72 * sc), (rx - 4 * sc, ry + 14 * sc)], hexc('b52e22'))
            circle(cv, rx, ry, 36 * sc, RED); circle(cv, rx, ry, 27 * sc, CREAM, 1.0, wd=2.4)
            fill(cv, [(rx + (15 if j % 2 == 0 else 6) * sc * math.cos(-math.pi / 2 + j * math.pi / 5),
                       ry + (15 if j % 2 == 0 else 6) * sc * math.sin(-math.pi / 2 + j * math.pi / 5)) for j in range(10)], CREAM)
        pen_text(cv, "(only employee)", CX + 110, y2 + 4, 62, (t - (T_EMPL + 0.22)) / 0.42, 'l', 'm')

# ================================================================ FIG. 24: jobs on Earth (+ CORRECTION)
def fig_jobs(cv, t):
    x0, top, w, ch = frame(cv, "FIG. 24", "Jobs on Earth, before and after my song", "Source: my song")
    x, y, cw, h = x0 + 150, top + 86, w - 190, 360
    axes(cv, x, y, cw, h, [(0.08, "2024"), (0.39, "2025"), (FS, "2026")], [(0, "0"), (0.5, "1.7 bn"), (1, "3.4 bn")], ylab="jobs")
    def val(f): return 0.955 + 0.03 * f + 0.008 * math.sin(f * 23)
    def Pt(f, v): return (x + f * cw, y + h - v * h)
    kd = ease_io((t - 114.30) / 0.75)
    pre = [Pt(f, val(f)) for f in np.linspace(0, FS * kd, max(2, int(60 * kd)))] if kd > 0 else []
    if len(pre) > 1: stroke(cv, pre, INK, 5)
    ks = sstep(T_SONG - 0.08, T_SONG + 0.12, t)
    if ks > 0:
        xs = x + FS * cw
        dashed(cv, [(xs, y - 6), (xs, y - 6 + (h + 6) * ease_out((t - T_SONG + 0.08) / 0.3))], RED, 2.6, ks)
        text(cv, "my song", xs, y - 34, F_SANS, 42, RED, ks, 'c', 'm')
    kc = ease_io((t - (T_END - 0.04)) / (T_EARTH - T_END + 0.04))
    vt = val(FS)
    if kc > 0:
        cliff = [Pt(FS + 0.035 * u ** 0.5, vt * (1 - u)) for u in np.linspace(0, min(1, kc / 0.85), 30)]
        stroke(cv, cliff, RED, 5)
        if kc > 0.85:
            u = (kc - 0.85) / 0.15
            stroke(cv, [Pt(FS + 0.035, 0.004), Pt(lerp(FS + 0.035, 1.0, u), 0.004)], RED, 5)
    pen_text(cv, "oops", x + FS * cw + 44, y + h * 0.40, 66, (t - (T_EARTH - 0.50)) / 0.30, 'l')
    tx, ty, tw_, th = x0 + 10, top + 620, w - 20, 280
    corr = sstep(T_GAVE0 - 0.02, T_GAVE0 + 0.14, t)
    if corr > 0:
        wpx = 420 * ease_out((t - T_GAVE0 + 0.02) / 0.20)
        rect(cv, tx, ty - 66, wpx, 58, RED, 1.0, r=8)
        if wpx > 420 * 0.6: text(cv, "CORRECTION", tx + 28, ty - 37, F_SANS, 40, CREAM, sstep(0.6, 0.9, wpx / 420), 'l', 'm', track=4)
    tile(cv, tx, ty, tw_, th)
    text(cv, "JOBS ON EARTH", tx + 34, ty + 50, F_SANS, 34, MUTE, 1.0, 'l', 'm', track=3)
    n = int(round(JOBS * (1 - kc))) if kc < 1 else 0
    if t >= T_GAVE - 0.02:
        kn = ease_out((t - T_GAVE + 0.02) / 0.16)
        text(cv, "1", tx + 34, ty + 170 + 18 * (1 - kn), F_NUM, 200, INK, kn, 'l', 'm')
        k2 = sstep(T_MYSELF - 0.06, T_MYSELF + 0.14, t)
        text(cv, "job left on Earth.", tx + 196, ty + 140, F_HEAD, 58, INK, k2, 'l', 'm')
        text(cv, "It's mine.", tx + 196, ty + 210, F_ITAL, 58, RED, sstep(T_MYSELF + 0.10, T_MYSELF + 0.30, t), 'l', 'm')
    elif n > 0:
        s_ = f"{n:,}"; fs = fit(s_, F_NUM, 96, tw_ - 68, 30)
        text(cv, s_, tx + 34, ty + 150, F_NUM, fs, INK, 1.0, 'l', 'm')
        text(cv, "and counting", tx + 34, ty + 228, F_ITAL, 48, INK2, 1.0, 'l', 'm')
    else:
        text(cv, "0", tx + 34, ty + 170, F_NUM, 200, RED, 1.0, 'l', 'm')
    stamp(cv.img, cv, "HIRED", x + cw * 0.30, y + h * 0.56, 88, T_BRAND - 0.04, t, RED, ang=-8.0, sub="BY MYSELF", seed=9)

# ================================================================ FIG. 25: net worth, tripled
def fig_worth(cv, t):
    x0, top, w, ch = frame(cv, "FIG. 25", "My net worth, tripled", "Source: my bank app, checked three times")
    tx, ty, tw_, th = x0 + 10, top + 20, w - 20, 360
    tile(cv, tx, ty, tw_, th)
    text(cv, "NET WORTH", tx + 40, ty + 54, F_SANS, 36, MUTE, 1.0, 'l', 'm', track=3)
    parts = [("$0", T_TRIPLED - 0.04, INK), (" × 3", T_MY - 0.04, INK), (" = $0", T_WORTH - 0.06, RED)]
    fs = fit("$0 × 3 = $0", F_NUM, 160, tw_ - 80, 60)
    xx = tx + 40
    for s_, ts, col in parts:
        k = ease_out((t - ts) / 0.18)
        if k > 0: text(cv, s_, xx, ty + 176 + 22 * (1 - k), F_NUM, fs, col, k, 'l', 'm')
        xx += tw(s_, F_NUM, fs)
    stroke(cv, [(tx + 40, ty + 270), (tx + tw_ - 40, ty + 270)], RULE, 1.6)
    kg = sstep(T_WORTH + 0.16, T_WORTH + 0.34, t)
    text(cv, "growth", tx + 40, ty + 318, F_SANS, 46, INK2, kg, 'l', 'm')
    text(cv, "+200%", tx + tw_ - 40, ty + 318, F_NUMB, 58, RED, kg, 'r', 'm')
    pen_text(cv, "checks out", tx + tw_ - 30, ty + th + 58, 68, (t - (T_WORTH + 0.36)) / 0.26, 'r')
    px, py, pw, ph = x0 + 20, ty + th + 112, 720, 405
    if _has(SHOT_CAR):
        photo(cv, SHOT_CAR, (t - 119.70) / 3.25, px, py, pw, ph)
        text(cv, "Pictured: assets.", px - 6, py + ph + 50, F_ITAL, 50, INK, 1.0, 'l', 'm')
        kc = sstep(T_WORTH + 0.84, T_WORTH + 1.00, t)
        text(cv, "(Not mine. Rendered.)", px - 6, py + ph + 112, F_ITAL, 50, RED, kc, 'l', 'm')

FIGS = [(99.0, 103.64, fig_posts), (103.64, 107.40, fig_summary), (107.40, 110.66, fig_minis),
        (110.66, 114.30, fig_org), (114.30, 119.80, fig_jobs), (119.80, 130.0, fig_worth)]

def draw_figs(cv, t):
    for a, b, fn in FIGS:
        if not (a - 0.3 <= t <= b + 0.3): continue
        ein = ease_out((t - (a - 0.04)) / 0.24) if a > P.T0 else 1.0
        eout = ease_io((t - (b - 0.1)) / 0.2)
        op = ein * (1 - eout)
        if op <= 0.004: continue
        cv.op = op; cv.dy = (1 - ein) * 46 - eout * 46
        fn(cv, t)
        cv.dy = 0.0; cv.op = 1.0

# ---------------------------------------------------------------- tone: the cream toned down + a stage light on the figure
# (Nov 8 stills round: x0.84 measured mean luma 0.61-0.71 on the top 86%, over the 0.62 rule; 0.79 + a wider falloff
# puts every figure at ~0.50-0.59 with the centre of the page still reading as cream)
TONE = 0.79
_LIT = {}
def lit(W, H):
    if (W, H) not in _LIT:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        cx, cy = W * (CX / DW), H * 0.43
        d = np.sqrt(((xx - cx) / (W * 0.60)) ** 2 + ((yy - cy) / (H * 0.50)) ** 2)
        g = 1 - 0.60 * np.clip(d - 0.35, 0, None) ** 1.2
        _LIT[(W, H)] = (TONE * np.clip(g, 0.45, 1)).astype(np.float32)[..., None]
    return _LIT[(W, H)]

def render_frame(t, W=1080, H=1920):
    img = paper(W, H)
    cv = VCv(img, W, H)
    masthead(cv); greek(cv); clock(cv, t)
    draw_figs(cv, t)
    img *= lit(W, H)
    return finish(img, int(round(t * 30)))
