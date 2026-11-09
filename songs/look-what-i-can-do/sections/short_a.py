"""Short A ("Too late!"), part 1 at 9:16: the terminal from scene.py, frames 1032-1287 (song 34.41-42.90).

scene.py's own vertical branch was a squeezed 16:9 layout (32 px boxes, half the frame empty), so the Short draws its own
9:16 composition from scene.py's pieces: the board of her videos up top (no 15 px pane labels), the session log at 44 px,
the permission boxes at 50/42 px in the middle of the frame, and TOO LATE! at full phone width with the temperature
jiggle. Everything that's read sits inside the Shorts safe zone (x <= 88% of the width, y <= 78% of the height).
16:9 is untouched: nothing in scene.py changes; this module only calls it.

  render_frame(t, W, H) for sections/run.py (W < H only; 16:9 falls through to scene.py unchanged)
  end_card(u, W, H): the 1.5 s end card, u = seconds into it (short_a_end.py renders it)
"""
import os, sys, math
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__)); SONG = os.path.dirname(HERE)
sys.path.insert(0, SONG)
import scene as SC
from studio import core as C

K, S, text, tw, rrect, rect = SC.K, SC.S, SC.text, SC.tw, SC.rrect, SC.rect
BG, INK, MUTE, GREEN, AMBER, RED, HDR, LINE = SC.BG, SC.INK, SC.MUTE, SC.GREEN, SC.AMBER, SC.RED, SC.HDR, SC.LINE
F_ANTON, F_MONOB, F_MONO = SC.F_ANTON, SC.F_MONOB, SC.F_MONO
clamp, sstep, ease_out, ease_io, env = SC.clamp, SC.sstep, SC.ease_out, SC.ease_io, SC.env

X0 = 64                      # left margin; the right edge of anything read stays left of 0.88 W
SAFE_R, SAFE_B = 0.88, 0.78
BOARD = (56, 200, 1024, 850)  # the board of her videos (imagery, may run under the right column)

# the session log for 9:16: same lines and timing as scene.py's V1_LOG, the long system line shortened to fit 44 px
V1_LOG_V = [dict(e) for e in SC.V1_LOG]
for e in V1_LOG_V:
    if e["text"].startswith("epochs: 0"): e["text"] = "epochs: 0 · training data: none"


def header(img, t, W, H):
    y = 104; sz = 34
    a = text(img, "adita@studio", X0, y, sz, INK, 0.9, F_MONOB)
    text(img, " ~/look-what-i-can-do", X0 + a, y, sz, MUTE, 0.9, F_MONO)


def board(img, t, W, H, dim):
    """The 8 panes as they stand after 'eleven things last night': scene.py's 3x3 board, headers blank (no tiny labels)."""
    ts = 1.0
    cells = SC._cells(9, BOARD, 14)
    off = (cells[1][0] - cells[0][0]) / 2          # 8 panes: the last row's two sit centred (no hole bottom-right)
    cells = [c if i < 6 else (c[0] + off,) + tuple(c[1:]) for i, c in enumerate(cells)]
    for i, (t0, kind, clip, fname) in enumerate(SC.V1_PANES):
        x, y, w, h = cells[i]
        if kind == "wave": SC.wave_pane(img, x, y, w, h, t, 1.0, ts)
        elif kind == "roll": SC.roll_pane(img, x, y, w, h, t, 1.0, ts)
        else:
            # her site is held on its clean stretch ("Each one gets its own page", 5-6.9 s of the clip): at 4 s the
            # source's own "27,709 lines of code" chip wraps out of its pill
            tc = 5.0 + 0.22 * max(0.0, t - 34.41) if clip.startswith("site-tour") else t - t0
            SC.pane(img, x, y, w, h, clip, tc, None, "", 1.0, ts, hdr=False)
        if kind in ("wave", "roll"):           # blank their header strip: a clean window bar instead of 15 px labels
            hh = int(max(18, min(34 * ts, h * 0.16)))
            rect(img, x + 2, y + 2, w - 4, hh - 2, HDR, 1.0)
    if dim > 0:
        x0, y0, x1, y1 = BOARD
        rrect(img, x0 - 10, y0 - 10, x1 - x0 + 20, y1 - y0 + 20, 10, fill=BG, fill_op=dim)


def perm_box(img, t, x, y, w, title, t_sel, sel, op):
    fs_t, fs = 50, 42
    while tw(title, fs_t) > w - 64 and fs_t > 36: fs_t -= 2
    opts = ["1. Yes", "2. Yes, and don't ask again", "3. No, let's not get ahead—"]
    while max(tw(o_, fs) for o_ in opts) > w - 110 and fs > 34: fs -= 2
    h = 100 + fs * 1.6 * 3 + 30
    rrect(img, x, y, w, h, 18, fill=AMBER, fill_op=op)
    rrect(img, x + 3, y + 3, w - 6, h - 6, 16, fill=BG, fill_op=op)
    text(img, title, x + 32, y + 30, fs_t, INK, op, F_MONOB)
    for i, s_ in enumerate(opts):
        yy = y + 108 + i * fs * 1.6
        chosen = t >= t_sel and i == sel
        col = (GREEN if sel == 0 else AMBER) if chosen else MUTE
        if chosen:
            pop = env(t, t_sel, 0.04, 0.3)
            rrect(img, x + 18, yy - fs * 0.22, w - 36, fs * 1.5, 10, fill=col, fill_op=(0.10 + 0.12 * pop) * op)
            text(img, "❯", x + 32, yy, fs, col, op, F_MONOB)
        text(img, s_, x + 76, yy, fs, col, op, F_MONOB)
    return h


def too_late(img, t, W, H):
    x0 = t - K["late"]; k = ease_out(x0 / 0.12)
    sz = 240; sc = 1.3 - 0.3 * k
    cx, cy = W * 0.445, H * 0.49   # left of centre: with the jiggle the '!' stays left of 0.88 W
    SC.darken(img, 0.35 * min(1, k * 2))
    temp = 0.2 + 1.8 * ease_io(clamp((x0 - 0.15) / 1.1))          # Next Token's trick, as in scene.py
    word = "TOO LATE!"; ws = [tw(ch, sz * sc, F_ANTON) for ch in word]; wtot = sum(ws); ang = math.radians(5.0)
    q = math.floor(t * 15) / 15
    acc = -wtot / 2
    for i, ch in enumerate(word):
        acc += ws[i] / 2
        if ch != " ":
            j = (temp - 0.2) / 1.8
            dx = math.sin(q * 41.3 + i * 7.1) * 14 * j; dy = math.sin(q * 37.7 + i * 3.3 + 1.7) * 22 * j
            da = math.sin(q * 29.9 + i * 5.9 + 0.4) * 14 * j
            px = cx + acc * math.cos(ang) + dx; py = cy - acc * math.sin(ang) + dy
            SC.blit_rot(img, ch, px, py, sz, RED, 5.0 + da, min(1, k * 1.6), F_ANTON, sc)
        acc += ws[i] / 2
    o = min(1, k * 2)
    tf = 38; lab = f"temperature {temp:.1f}"; lw = tw(lab, tf, F_MONOB)
    by = cy + 190; bh = 64; bw = lw + 56 + 140
    bx0 = (W * SAFE_R + X0) / 2 - bw / 2 - 20
    rrect(img, int(bx0), int(by), int(bw), bh, 32, fill=C.hexc("1a1a1d"), fill_op=0.92 * o, border=C.hexc("3a3a40"))
    text(img, lab, bx0 + 28, by + 12, tf, AMBER, o, F_MONOB)
    gx = bx0 + 28 + lw + 22
    rrect(img, int(gx), int(by + 25), 120, 14, 7, fill=C.hexc("2c2c31"), fill_op=o)
    rrect(img, int(gx), int(by + 25), int(max(10, 120 * temp / 2.0)), 14, 7, fill=RED, fill_op=o)
    s_ = "$ claude --dangerously-skip-permissions"
    fs = SC.fit_size(s_, F_MONOB, 38, W * SAFE_R - X0 - 8)
    text(img, s_, X0, cy + 330, fs, RED, o, F_MONOB)


def compose(t, W, H):
    img = np.empty((H, W, 3), np.float32); img[:] = BG
    if t < K["direct"] - 0.1:
        # 'I learned a whole new job today!': the board (dimmed as in the film) and the session log
        board(img, t, W, H, 0.4 * sstep(K["training"] + 0.2, K["training"] + 0.8, t))
        SC.log(img, t, W, H, V1_LOG_V, X0, 1330, 44, max_lines=6)
    else:
        board(img, t, W, H, 0.78)
        cur = None
        for i, (t0, title, tsel, sel) in enumerate(SC.PERM):
            if t >= t0 - 0.1: cur = (i, t0, title, tsel, sel)
        if cur is not None and t < K["late"] + 0.15:
            i, t0, title, tsel, sel = cur
            k = ease_out((t - t0 + 0.1) / 0.18)
            perm_box(img, t, X0, 760 + (1 - k) * 30, W * SAFE_R - X0 - 8, title, tsel, sel, k)
        if t >= K["late"] - 0.02: too_late(img, t, W, H)
    header(img, t, W, H)
    return img


def render_frame(t, W, H):
    fi = int(round(t * 30))
    if W >= H: return SC.render_frame(t, W, H, fi)
    img = compose(t, W, H)
    flash = 0.5 * env(t, K["late"], 0.02, 0.18)
    gl = 0.5 * (1 - (t - K["late"]) / 0.25) if K["late"] <= t < K["late"] + 0.25 else 0.0
    return C.finish(img, t, fi, 1e9, flash=flash, flash_col=SC.WHITE * 0.8, glitch_amt=gl, ca=0.0012, vignette=True)


# ------------------------------------------------------------------ the end card (1.5 s after the song section)
def end_card(u, W, H, fi=0):
    """Dark, in the film's terminal look: 'Full video on my channel', a red SUBSCRIBE pill, @adita_zzz. All inside the
    safe zone (left 64 px to 0.88 W, above 0.78 H)."""
    img = np.empty((H, W, 3), np.float32); img[:] = BG
    header(img, 0, W, H)
    k1 = ease_out((u + 0.10) / 0.25); k2 = ease_out((u - 0.05) / 0.25); k3 = ease_out((u - 0.18) / 0.25)
    text(img, "❯ open look_what_i_can_do.mp4", X0, 520, 38, MUTE, k1, F_MONO)
    hs = 150; yh = 610 + (1 - k1) * 24
    text(img, "FULL VIDEO", X0, yh, hs, INK, k1, F_ANTON)
    text(img, "ON MY CHANNEL", X0, yh + hs * 1.08, SC.fit_size("ON MY CHANNEL", F_ANTON, hs, W * SAFE_R - X0 - 8), GREEN, k2, F_ANTON)
    # the pill (studio's own SUBSCRIBE pill + bell)
    fs3 = 58; bh = int(fs3 * 1.9); bw = int(tw("SUBSCRIBE", fs3, F_ANTON) + bh * 1.55); px, py = X0, 1060 + (1 - k3) * 24
    C._pill(img, px, py, bw, bh, C.TH('red', C.SUB_RED), k3)
    C._bell(img, px + bh * 0.62, py + bh / 2, bh * 0.62, SC.WHITE, k3, ring=math.sin(u * 16) * math.exp(-max(0, u - 0.4) * 1.5) if u > 0.2 else 0)
    text(img, "SUBSCRIBE", px + bh * 1.12, py + bh / 2 - fs3 * 0.62, fs3, SC.WHITE, k3, F_ANTON)
    a = text(img, "@adita_zzz", X0, 1250 + (1 - k3) * 16, 52, INK, k3, F_MONOB)
    SC.cursor(img, X0 + a + 10, 1250 + 8, 50, u + 0.2, GREEN, k3, blink=True)
    return C.finish(img, 0, fi, 1e9, ca=0.0012, vignette=True)
