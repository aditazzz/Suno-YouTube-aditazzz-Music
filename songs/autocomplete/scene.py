"""Autocomplete — it finishes her sentences before she sings them.

The lyric IS the visual: every line appears as a big text field where the AI's ghost completion (glowing pink)
shows up before she sings it, and turns white word by word as she does. Above it: a giant blinking cursor,
drifting next-token guesses with probabilities, a suggestion dropdown. Choruses bloom into wine/magenta/cyan
with a huge AUTO|COMPLETE wordmark. Bridge: one cursor in the dark, "my pulse" (a heartbeat) vs "your prediction"
(probability bars). "I was going to say—": everything cuts to black. Final chorus, then "Finish it." and a hard stop.
"""
import os, math
import numpy as np, cv2
from studio import core as C
from studio import kit as K
from studio.core import (sstep, ease_out, ease_io, win, lerp, hexc, clamp, sprite, blit, text_w, shadow,
                         F_INTER, F_DISP, F_DISPB, F_MONO, F_MONOB, WHITE)
from studio.kit import panel, label, bubble, grid, vgrad, ssa, desat, check, INK, chip, fill_poly, heart_pts

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

WINE = hexc('3a0a2c'); INKV = hexc('0c0716'); MAG = hexc('ff2fa8'); GHOST = hexc('ff8fd0'); CYAN = hexc('39e6ff'); VIO = hexc('7b4dff')
LIL = hexc('c9b4ff'); GOLD = hexc('ffd36b')

S = {n: sec(n) for n in ("V1", "PRE1", "CH1", "V2", "PRE2", "CH2", "BRIDGE", "FINAL", "OUTRO")}
CHORUS = [(S["CH1"]['s'], S["V2"]['s'], 0), (S["CH2"]['s'], S["BRIDGE"]['s'], 1), (S["FINAL"]['s'], DUR + 1, 2)]   # music keeps going after the last word
def chorus_at(t):
    for a, b, k in CHORUS:
        if a - 0.05 <= t < b: return k, a, b
T_HOLD = lt("Hold up"); T_BLINK = lt("Let the cursor blink"); T_PULSE = lt("My pulse"); T_PRED = lt("Your prediction")
T_WANT = lt("My want"); T_BEST = lt("Your best completion"); T_TELL = lt("Tell me"); T_MID = lt("disappear mid-line")
T_SAY1 = lt("I was going to say", 0); T_SAY2 = lt("I was going to say", 1); T_FINISH = lt("Finish it", 3) if sum(L['text'] == "Finish it" for L in LINES) > 3 else LINES[-1]['s']
T_LAST = LINES[-1]['s']
T_END = DUR - 6.5
T_OUT = LINES[-1]['e'] + 0.4          # after the last "Finish it": the unfinished sentence
T_DEL0, T_DEL1 = 0.9, 2.0             # intro: the wordmark backspaces into the lone cursor
T_SLEEP = lt("Past the hour"); T_KNOW = lt("I know what you are"); T_WANTED = lt("being wanted")

def phase(t):
    if chorus_at(t): return "chorus"
    if t < S["CH1"]['s']: return "v1"
    if t < S["CH2"]['s']: return "v2"
    if t < S["FINAL"]['s']: return "bridge"
    return "outro"

# ---------------------------------------------------------------- backgrounds
_r = np.random.default_rng(3)
def bg_night(G, t):
    img = vgrad(G, INKV, WINE * 0.55)
    img += VIO * (0.18 * np.exp(-((G['X']) ** 2 * 2 + (G['Y'] + 0.12) ** 2 * 3)))[..., None]
    img += MAG * (0.10 * np.exp(-((G['X'] - 0.7) ** 2 * 2 + (G['Y'] - 0.4) ** 2 * 3)))[..., None]
    return img

def bg_bloom(G, t, k):
    pals = [(MAG, VIO, CYAN), (VIO, MAG, CYAN), (MAG, CYAN, GOLD)]
    c1, c2, c3 = pals[k]
    R, A = G['R'], G['A']
    ring = 0.5 + 0.5 * np.cos(R * 24 - t * 5)
    img = c1 * (0.75 * np.exp(-R * 1.8))[..., None] + c2 * (0.35 * (1 - np.exp(-R * 1.4)))[..., None]
    img += c3 * (0.10 * ring * (R > 0.2))[..., None]
    sweep = ssa(-0.3, 0.3, np.sin(A * 6 + t * 0.8))
    img *= (0.82 + 0.25 * sweep[..., None])
    if k == 2: img = img * 0.6 + K.kaleido(G, t, 0.9, seg=6) * 0.45
    img *= 0.88 + 0.22 * bp(t, 6)
    return img

TOK = ["you", "me", "want", "know", "stay", "mean", "say", "need", "close", "yet", "more", "right"]
TK = np.stack([_r.uniform(0.05, 0.95, 30), _r.uniform(0.05, 0.6, 30), _r.uniform(0.4, 1.2, 30), _r.uniform(0, 6.28, 30)], 1)
def tokens(img, t, W, H, ts, amt):
    if amt <= 0.01: return
    for i, (x, y, sp, ph) in enumerate(TK):
        yy = (y - t * 0.012 * sp) % 0.62 + 0.04
        p = 0.2 + 0.75 * (0.5 + 0.5 * math.sin(t * 0.7 * sp + ph))
        s = f"{TOK[i % len(TOK)]} {p:.2f}"
        o = amt * (0.25 + 0.35 * (0.5 + 0.5 * math.sin(t * sp + ph)))
        blit(img, sprite(s, F_MONOB, int(36 * ts)), x * W, yy * H, LIL, o, anchor='c')

def big_cursor(img, cx, cy, h, col, op, t, rate=1.6):
    if op <= 0.01: return
    on = 0.5 + 0.5 * math.cos(t * rate * 2 * math.pi)
    on = 1.0 if on > 0.3 else 0.15
    w = max(4, int(h * 0.09)); sg = h * 0.15
    # blur only a box around the cursor (same result as a full-frame blur, ~20x cheaper)
    H_, W_ = img.shape[:2]; pad = int(sg * 4) + 3
    x0, x1 = max(0, int(cx - w / 2) - pad), min(W_, int(cx + w / 2) + pad + 1)
    y0, y1 = max(0, int(cy - h / 2) - pad), min(H_, int(cy + h / 2) + pad + 1)
    if x1 <= x0 or y1 <= y0: return
    lay = np.zeros((y1 - y0, x1 - x0), np.float32)
    cv2.rectangle(lay, (int(cx - w / 2) - x0, int(cy - h / 2) - y0), (int(cx + w / 2) - x0, int(cy + h / 2) - y0), 1.0, -1)
    g = cv2.GaussianBlur(lay, (0, 0), sg)
    img[y0:y1, x0:x1] += (g * 0.9 + lay)[..., None] * col * op * on

# ---------------------------------------------------------------- the typing field (replaces the lyric overlay)
def current_line(t):
    starts = [L['s'] for L in LINES]
    i = int(np.searchsorted(starts, t + 0.45)) - 1
    if i < 0: return None, None
    L = LINES[i]
    nxt = starts[i + 1] if i + 1 < len(starts) else 1e9
    if t > max(L['e'] + 0.8, L['s'] + 1.5) and t < nxt - 0.45: return None, i
    return L, i

def field(img, t, W, H, ts, vert, op=1.0):
    if C.STATE["clean"] or op <= 0.01: return
    L, i = current_line(t)
    if L is None: return
    flt = C.STATE["lyric_filter"]
    if flt is not None and not flt(L): return
    words = [(w.strip(), tt) for w, tt in zip(L['words'], L['wt'])]
    fs = int((70 if not vert else 62) * ts); maxw = W * (0.80 if not vert else 0.84)
    sp_w = text_w(" ", F_DISPB, fs)
    rows = [[]]; cw = 0
    for w, tt in words:
        ww = text_w(w, F_DISPB, fs)
        if rows[-1] and cw + sp_w + ww > maxw: rows.append([]); cw = 0
        rows[-1].append((w, tt, ww)); cw += ww + sp_w
    lh = fs * 1.3
    ybase = H * (0.81 if not vert else 0.69)
    y0 = ybase - (len(rows) - 1) * lh / 2
    # dark field behind for contrast
    fw = max(sum(r[2] for r in row) + sp_w * (len(row) - 1) for row in rows) + fs * 1.4
    fh = lh * len(rows) + fs * 0.7
    app = sstep(L['s'] - 0.45, L['s'] - 0.25, t)
    panel(img, W / 2 - fw / 2, y0 - fs * 0.35 - 6, fw, fh, INKV, 0.72 * op * app, r=int(fs * 0.4), shadow_op=0.4)
    last_x, last_y = None, None
    for ri, row in enumerate(rows):
        x = W / 2 - (sum(r[2] for r in row) + sp_w * (len(row) - 1)) / 2; y = y0 + ri * lh
        for w, tt, ww in row:
            sung = t >= tt - 0.06
            pred = sstep(L['s'] - 0.45, L['s'] - 0.25, t)       # the completion is there before she sings it
            if sung:
                hit = math.exp(-max(0, t - tt) * 3)
                col = WHITE * (1 - hit) + CYAN * hit
                spr = sprite(w, F_DISPB, fs, 6)
                shadow(img, spr, x, y + 3, 0.9 * op)
                blit(img, spr, x, y, col, op, 0.5 * hit * op, glow_color=CYAN)
                last_x, last_y = x + ww, y
            else:
                blit(img, sprite(w, F_DISPB, fs, 8), x, y, GHOST * 0.85, op * pred * 0.75, 0.35 * op * pred, glow_color=MAG)
            x += ww + sp_w
    if last_x is None: last_x, last_y = W / 2 - fw / 2 + fs * 0.6, y0
    if int(t * 2.4) % 2 == 0:
        cv2.rectangle(img, (int(last_x + 6), int(last_y + fs * 0.1)), (int(last_x + 6 + fs * 0.08), int(last_y + fs * 1.1)), (CYAN * op).tolist(), -1)

# ---------------------------------------------------------------- upper visuals
def v_ui(img, t, W, H, ts, vert):
    ph = phase(t)
    if ph not in ("v1", "v2"): return
    cx, cy = W / 2, H * (0.33 if not vert else 0.32)
    tokens(img, t, W, H, ts, 0.55 * (sstep(T_DEL0, T_DEL1 + 0.3, t) if t < T_DEL1 + 0.3 else 1.0))
    ch = (300 if not vert else 340) * ts
    if t < T_DEL1 + 0.35:
        word = "AUTOCOMPLETE"; n = len(word) - int(clamp((t - T_DEL0) / (T_DEL1 - T_DEL0)) * len(word))
        fs = int((170 if not vert else 111) * ts); sub = word[:n]
        wa = text_w(sub[:4], F_DISP, fs); wb = text_w(sub[4:], F_DISP, fs) if n > 4 else 0
        x0 = cx - (wa + wb) / 2
        if sub: blit(img, sprite(sub[:4], F_DISP, fs, 14), x0 + wa / 2, cy, WHITE, 1.0, 0.6, glow_color=CYAN, anchor='c')
        if n > 4: blit(img, sprite(sub[4:], F_DISP, fs, 18), x0 + wa + wb / 2, cy, GHOST, 0.9, 1.0, glow_color=MAG, anchor='c')
        hh = lerp(fs * 0.9, ch, sstep(T_DEL1, T_DEL1 + 0.3, t))
        big_cursor(img, x0 + wa + wb + 12 * ts, cy, hh, CYAN, 1.0, t if t > T_DEL1 else 0.0)
    else:
        big_cursor(img, cx, cy, ch, CYAN, 1.0, t)
    # suggestion dropdown under the cursor for the current line
    L, i = current_line(t)
    if L is None: return
    words = L['text'].split()
    if len(words) < 2: return
    nxt = " ".join(words[len(words) // 2:]).strip(",.")
    alts = [nxt, "…stay", "…say it"] if i % 2 == 0 else [nxt, "…don't", "…go on"]
    a = sstep(L['s'] - 0.4, L['s'] - 0.2, t) * (1 - sstep(L['e'], L['e'] + 0.4, t))
    fs = int(40 * ts); w = max(text_w(s, F_INTER, fs) for s in alts) + 190 * ts; h = fs * 1.6
    x0 = cx + (60 if not vert else -w / 2 + 0) * ts if not vert else cx - w / 2; y0 = cy + (170 if not vert else 210) * ts
    for k, s in enumerate(alts):
        sel = k == 0
        panel(img, x0, y0 + k * (h + 6 * ts), w, h, (MAG * 0.8 if sel else hexc('1d1430')), a, r=int(12 * ts), shadow_op=0.3)
        blit(img, sprite(s, F_INTER, fs), x0 + 26 * ts, y0 + k * (h + 6 * ts) + h * 0.18, WHITE if sel else LIL, a)
        blit(img, sprite(["0.97", "0.02", "0.01"][k], F_MONOB, int(34 * ts)), x0 + w - 100 * ts, y0 + k * (h + 6 * ts) + h * 0.22, WHITE if sel else LIL * 0.7, a)
    if T_SLEEP - 0.2 < t < T_SLEEP + 2.4:
        k = sstep(T_SLEEP - 0.2, T_SLEEP, t) * (1 - sstep(T_SLEEP + 2.0, T_SLEEP + 2.4, t))
        chip(img, "2:47 AM", W * (0.78 if not vert else 0.5), H * (0.12 if not vert else 0.10), 60 * ts, VIO, WHITE, k, T_SLEEP - 0.2, t)
    if T_KNOW - 0.2 < t < T_KNOW + 2.0:
        k = sstep(T_KNOW - 0.2, T_KNOW, t) * (1 - sstep(T_KNOW + 1.6, T_KNOW + 2.0, t))
        chip(img, "language model", W * (0.78 if not vert else 0.5), H * (0.12 if not vert else 0.10), 56 * ts, LIL, INK, k, T_KNOW - 0.2, t)

def chorus_ui(img, t, W, H, ts, vert):
    c = chorus_at(t)
    if not c: return
    k, a, b = c; o = sstep(a - 0.05, a + 0.2, t) * (1 - sstep(b - 0.2, b + 0.05, t))
    if k == 2: o *= 1 - sstep(T_OUT, T_OUT + 0.6, t)
    if o <= 0.01: return
    fs = int((190 if not vert else 150) * ts) * (1 + 0.05 * bp(t, 8))
    cy = H * (0.33 if not vert else 0.30)
    w1 = text_w("AUTO", F_DISP, int(fs)); w2 = text_w("COMPLETE", F_DISP, int(fs))
    if vert:
        blit(img, sprite("AUTO", F_DISP, int(fs), 14), W / 2, cy - fs * 0.55, WHITE, o, 0.6 * o, glow_color=CYAN, anchor='c')
        blit(img, sprite("COMPLETE", F_DISP, int(fs * 0.82), 18), W / 2, cy + fs * 0.45, GHOST, o * (0.75 + 0.25 * bp(t, 5)), 1.0 * o, glow_color=MAG, anchor='c')
        cx_cur = W / 2 + text_w("AUTO", F_DISP, int(fs)) / 2 + 14
        big_cursor(img, cx_cur, cy - fs * 0.55, fs * 0.9, CYAN, o, t, 2.5)
    else:
        x0 = W / 2 - (w1 + w2) / 2
        blit(img, sprite("AUTO", F_DISP, int(fs), 14), x0 + w1 / 2, cy, WHITE, o, 0.6 * o, glow_color=CYAN, anchor='c')
        blit(img, sprite("COMPLETE", F_DISP, int(fs), 18), x0 + w1 + w2 / 2, cy, GHOST, o * (0.75 + 0.25 * bp(t, 5)), 1.0 * o, glow_color=MAG, anchor='c')
        big_cursor(img, x0 + w1 + 8, cy, fs * 0.9, CYAN, o, t, 2.5)
    # "Finish it" punches
    fin = [L for L in lines_in(["CH1", "CH2", "FINAL"][k]) if "Finish it" in L['text']]
    for L in fin:
        if 0 <= t - L['s'] < 1.4:
            q = o * (1 - sstep(L['s'] + 0.9, L['s'] + 1.4, t))
            chip(img, "FINISH IT", W / 2, H * (0.56 if not vert else 0.53), 72 * ts, CYAN, INK, q, L['s'], t)

def bridge_ui(img, t, W, H, ts, vert):
    if not (S["BRIDGE"]['s'] - 0.1 < t < S["FINAL"]['s']): return
    o = sstep(S["BRIDGE"]['s'] - 0.1, S["BRIDGE"]['s'] + 0.3, t)
    cx, cy = W / 2, H * (0.30 if not vert else 0.30)
    dark = sstep(T_SAY1 - 0.1, T_SAY1 + 0.1, t)
    big_cursor(img, cx, cy, (360 if not vert else 400) * ts, CYAN, o, t, 1.0 if t > T_BLINK else 1.6)
    if T_PULSE - 0.1 < t < T_TELL and dark < 1:
        q = sstep(T_PULSE - 0.1, T_PULSE + 0.1, t) * o
        # my pulse: a heartbeat line on the left; your prediction: probability bars on the right
        x0 = W * (0.08 if not vert else 0.06); x1 = W * (0.44 if not vert else 0.94)
        yy = cy + (260 if not vert else 300) * ts
        pts = []
        for i in range(81):
            u = i / 80; ph_ = (u * 2 - (t - T_PULSE) * 1.2) % 1.0
            b = -90 * ts if 0.45 < ph_ < 0.48 else (50 * ts if 0.48 <= ph_ < 0.51 else 0)
            pts.append((int(x0 + (x1 - x0) * u), int(yy + b)))
        cv2.polylines(img, [np.array(pts, np.int32)], False, (MAG * q).tolist(), max(4, int(7 * ts)), cv2.LINE_AA)
        label(img, "my pulse", (x0 + x1) / 2, yy + 80 * ts, 48 * ts, GHOST, q, F_DISPB)
        if t > T_PRED - 0.1:
            q2 = sstep(T_PRED - 0.1, T_PRED + 0.1, t) * o
            if not vert: bx0, bx1, by = W * 0.56, W * 0.92, yy + 40 * ts
            else: bx0, bx1, by = W * 0.10, W * 0.90, yy + 280 * ts
            vals = [0.92, 0.05, 0.02, 0.01]; names = ["want", "need", "stay", "go"]
            bw = (bx1 - bx0) / 4.5
            for j, v in enumerate(vals):
                hh = (230 if not vert else 180) * ts * v
                x = bx0 + j * bw * 1.15
                panel(img, x, by - hh, bw, max(8, hh), CYAN if j == 0 else LIL * 0.6, q2, r=int(8 * ts), shadow_op=0)
                blit(img, sprite(names[j], F_INTER, int(36 * ts)), x + bw / 2, by + 30 * ts, WHITE, q2, anchor='c')
            label(img, "your prediction", (bx0 + bx1) / 2, by - (280 if not vert else 230) * ts, 48 * ts, CYAN, q2, F_DISPB)
    img *= 1 - 0.92 * dark * (1 - sstep(S["FINAL"]['s'] - 0.05, S["FINAL"]['s'], t))
    if dark > 0: big_cursor(img, cx, cy, (360 if not vert else 400) * ts, CYAN, o * dark, t, 1.0)

CANDS = [("you", 0.41), ("goodnight", 0.22), ("stay", 0.17), ("I'm fine", 0.12), ("nothing", 0.08)]
def outro_ui(img, t, W, H, ts, vert):
    """After the last "Finish it": "I was going to say" waits; the model keeps offering endings, none is taken."""
    if not (T_OUT < t < T_END + 0.2): return
    o = sstep(T_OUT, T_OUT + 0.5, t) * (1 - sstep(T_END - 0.3, T_END, t))
    cx, cy = W / 2, H * (0.30 if not vert else 0.28)
    big_cursor(img, cx, cy, (300 if not vert else 340) * ts, CYAN, o, t, 1.0)
    t_stop = T_END - 2.6                                   # suggestions give up; only the cursor is left
    so = o * (1 - sstep(t_stop, t_stop + 0.4, t))
    step = (t_stop - T_OUT - 0.8) / len(CANDS)
    sel = min(len(CANDS) - 1, int(max(0.0, t - T_OUT - 0.8) / step))
    fs = int(44 * ts); w = max(text_w(c, F_INTER, fs) for c, _ in CANDS) + 220 * ts; h = fs * 1.6
    x0 = (cx + 70 * ts) if not vert else cx - w / 2; y0 = cy + ((-h * 2.5) if not vert else 230 * ts)
    for j, (c, p) in enumerate(CANDS):
        q = so * sstep(T_OUT + 0.3 + j * 0.08, T_OUT + 0.5 + j * 0.08, t); on = j == sel and t > T_OUT + 0.8
        panel(img, x0, y0 + j * (h + 6 * ts), w, h, MAG * 0.8 if on else hexc('1d1430'), q, r=int(12 * ts), shadow_op=0.3)
        blit(img, sprite(c, F_INTER, fs), x0 + 28 * ts, y0 + j * (h + 6 * ts) + h * 0.17, WHITE if on else LIL, q)
        blit(img, sprite(f"{p:.2f}", F_MONOB, int(38 * ts)), x0 + w - 110 * ts, y0 + j * (h + 6 * ts) + h * 0.21, WHITE if on else LIL * 0.7, q)
    # the field: her words in white, the model's ghost ending after the caret
    fs2 = int((70 if not vert else 62) * ts); mine = "I was going to say"
    ghost = (" " + CANDS[sel][0]) if t < t_stop and t > T_OUT + 0.8 else ""
    wm = text_w(mine, F_DISPB, fs2); wg = text_w(ghost, F_DISPB, fs2) if ghost else 0
    fw = wm + text_w(" goodnight", F_DISPB, fs2) + fs2 * 1.4; fh = fs2 * 1.6
    y = H * (0.81 if not vert else 0.69)
    panel(img, W / 2 - fw / 2, y - fs2 * 0.35 - 6, fw, fh, INKV, 0.72 * o, r=int(fs2 * 0.4), shadow_op=0.4)
    x = W / 2 - (wm + wg) / 2 if ghost else W / 2 - wm / 2
    spr = sprite(mine, F_DISPB, fs2, 6); shadow(img, spr, x, y + 3, 0.9 * o); blit(img, spr, x, y, WHITE, o)
    if ghost:
        gq = o * sstep(0, 0.15, (t - T_OUT - 0.8) % step) * (1 - sstep(step - 0.15, step, (t - T_OUT - 0.8) % step))
        blit(img, sprite(ghost, F_DISPB, fs2, 8), x + wm + fs2 * 0.12, y, GHOST * 0.85, gq * 0.8, 0.35 * gq, glow_color=MAG)
    if int(t * 2.0) % 2 == 0:
        cv2.rectangle(img, (int(x + wm + 6), int(y + fs2 * 0.1)), (int(x + wm + 6 + fs2 * 0.08), int(y + fs2 * 1.1)), (CYAN * o).tolist(), -1)

# ---------------------------------------------------------------- frame
def render_scene(t, SW, SH, vert):
    G = grid(SW, SH); ph = phase(t)
    if ph == "chorus":
        k, a, b = chorus_at(t); img = bg_bloom(G, t, k)
        if k == 2 and t > T_OUT: img = img * (1 - 0.6 * sstep(T_OUT, T_OUT + 1.5, t)) + bg_night(G, t) * 0.5 * sstep(T_OUT, T_OUT + 1.5, t)
    elif ph == "bridge":
        img = bg_night(G, t) * 0.7
    else:
        img = bg_night(G, t)
    return img

def render_frame(t, W=1920, H=1080, fi=0):
    vert = H > W; ts = min(W, H) / 1080
    SW, SH = (W * 2 // 3) // 2 * 2, (H * 2 // 3) // 2 * 2
    sc = render_scene(t, SW, SH, vert)
    img = cv2.resize(np.clip(sc, 0, 1.4).astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR)
    img = img / (1 + np.maximum(img - 0.85, 0))
    clean = C.STATE["clean"]
    v_ui(img, t, W, H, ts, vert)
    chorus_ui(img, t, W, H, ts, vert)
    bridge_ui(img, t, W, H, ts, vert)
    img *= 1 - 0.35 * C.post(W, H).bot
    field(img, t, W, H, ts, vert, 1.0 if t < T_END else 0.0)
    outro_ui(img, t, W, H, ts, vert)
    if not clean:
        C.subscribe_pill(img, t, W, H, lines_in("CH1")[-1]['e'] + 0.2 if False else S["V2"]['s'] - 0.2, 5.0)
        C.end_screen(img, t, W, H, T_END, DUR - T_END, "Go on. Finish it.", sub_line="Subscribe for a new song every week", title="Autocomplete", accent=MAG)
    fl = 0.0
    for a, b, k in CHORUS:
        if 0 <= t - a < 1.2: fl += 0.45 * math.exp(-(t - a) * 5)
    gl = 0.0
    if 0 <= t - T_SAY1 < 0.2: gl += 0.6
    return C.finish(img, t, fi, DUR, flash=fl, flash_col=GHOST * 0.8, glitch_amt=gl, ca=0.002)
