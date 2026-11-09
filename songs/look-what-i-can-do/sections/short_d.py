"""Short D ("Hey Claude?") at 9:16: the terminal from scene.py, frames 0-1072 (song 0.00-35.77).

scene.py's vertical branch is a squeezed 16:9 layout (32-46 px text, small board), so this Short draws its own 9:16
composition from scene.py's pieces (scene.py is untouched; 16:9 falls through to it):
  0.00-0.62   the cover: a wall of 27 of her videos with the "Welcome to the studio" card on it. On "Hey" the wall
              fades out and the card settles at the top (not a near-empty terminal on the first frame).
  0.62-13.58  the conversation at 64 px (lyric size), word-wrapped inside the safe column; Claude's lines in amber;
              the three strategy bullets at 46 px.
  13.58-19.76 the beat drops: ls ~/Original Music at 40 px, the count huge in Anton, "projects · 0 video editors".
  19.76-35.77 verse 1: her board builds pane by pane on each "I made ..." (panes without the 15 px header labels), the
              eleven-things burst with its counter, and the verse typed at 58 px, wrapped at the comma.
Everything read stays inside x 64..0.88 W and above 0.78 H.
  render_frame(t, W, H) for sections/run.py (9:16)
"""
import os, sys, math
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__)); SONG = os.path.dirname(HERE)
sys.path.insert(0, SONG); sys.path.insert(0, HERE)
import scene as SC
from studio import core as C

K, S, text, tw, rrect, rect = SC.K, SC.S, SC.text, SC.tw, SC.rrect, SC.rect
BG, INK, MUTE, GREEN, AMBER, HDR, LINE = SC.BG, SC.INK, SC.MUTE, SC.GREEN, SC.AMBER, SC.HDR, SC.LINE
F_ANTON, F_MONOB, F_MONO = SC.F_ANTON, SC.F_MONOB, SC.F_MONO
clamp, sstep, ease_out, ease_io, env, lerp = SC.clamp, SC.sstep, SC.ease_out, SC.ease_io, SC.env, SC.lerp

N0, N1 = 0, 1072
X0 = 64; SAFE_R, SAFE_B = 0.88, 0.78
T_HEY = SC.INTRO_LOG[0]["s"]


def header(img, op=1.0):
    y = 104; sz = 34
    a = text(img, "adita@studio", X0, y, sz, INK, 0.9 * op, F_MONOB)
    text(img, " ~/look-what-i-can-do", X0 + a, y, sz, MUTE, 0.9 * op, F_MONO)


# ------------------------------------------------------------------ the cover: a wall of her videos
def wall(img, t, op):
    if op <= 0.01: return
    cols, rows, gap = 3, 9, 8
    tw_ = (1080 - gap * (cols - 1)) / cols; th = tw_ * 9 / 16
    oy = (1920 - (rows * th + gap * (rows - 1))) / 2
    for r in range(rows):
        for c in range(cols):
            i = r * cols + c; clip, _, off = SC.lib(i)
            x, y = c * (tw_ + gap), oy + r * (th + gap)
            SC.pane(img, x, y, tw_, th, clip, 1.2 + off + t + 0.37 * i, None, "", op, 1.0, hdr=False, check=False)
    img *= (1 - 0.18 * op)


def welcome(img, t, y, op):
    if op <= 0.01: return
    x, w, h = X0, 1080 * SAFE_R - X0, 210
    rrect(img, x, y, w, h, 22, fill=AMBER, fill_op=op * 0.95)
    rrect(img, x + 4, y + 4, w - 8, h - 8, 19, fill=BG, fill_op=op)
    SC.spark(img, x + 72, y + 78, 28, AMBER, op)
    text(img, "Welcome to the studio", x + 128, y + 40, 54, INK, op, F_MONOB)
    text(img, "~/look-what-i-can-do", x + 128, y + 120, 36, MUTE, op, F_MONO)


# ------------------------------------------------------------------ a wrapped session log
def wrap(s, size, maxw, comma=False):
    if tw(s, size) <= maxw: return [s]
    if comma and ", " in s:
        a, b = s.split(", ", 1)
        if tw(a + ",", size) <= maxw and tw(b, size) <= maxw: return [a + ",", b]
    out, cur = [], ""
    for w in s.split(" "):
        cand = (cur + " " + w).strip()
        if cur and tw(cand, size) > maxw: out.append(cur); cur = w
        else: cur = cand
    out.append(cur); return out


def rows_of(e, t, size, sys_size, maxw, comma):
    """[(who, text, size, first?, typing?)] rows for one entry at time t (typed portion only)."""
    who = e["who"]; sz = size if who in ("u", "c") else sys_size
    pre = tw("❯ ", sz) if who == "u" else sz * 0.95 if who == "c" else 0
    full = wrap(e["text"], sz, maxw - pre, comma)
    if who in ("u", "c"):
        n = len(SC.typed_text(e["text"], t, e["s"], e["t1"]))
    else: n = 10 ** 6
    out = []; used = 0
    for j, r in enumerate(full):
        if used >= n and j > 0: break
        part = r[:max(0, n - used)]; used += len(r) + 1
        out.append((who, part, sz, j == 0, pre))
    return out


def draw_log(img, t, entries, size, sys_size, y_bottom, y_top, comma=False, extra_last=None):
    vis = [e for e in entries if t >= e["s"]]
    if not vis: return
    maxw = 1080 * SAFE_R - X0 - 6
    rows = []
    for e in vis:
        rr = rows_of(e, t, size, sys_size, maxw, comma)
        rows += [(r, e) for r in rr]
    lhs = [r[2] * 1.32 for r, _ in rows]
    last = vis[-1]; k = ease_out((t - last["s"]) / 0.16)
    yb = y_bottom + (1 - k) * lhs[-1] * 0.5
    typing_e = last if (last["who"] == "u" and t < last["t1"] + 0.6) else None
    n = len(rows)
    # whole entries only: an entry whose first row would sit above y_top is dropped with all its rows
    ys = [0.0] * n; y = yb
    for i in range(n - 1, -1, -1): y -= lhs[i]; ys[i] = y
    keep = set(); ents = []
    for (r, e) in rows:
        if e not in ents: ents.append(e)
    for e in ents:
        i0 = next(i for i, (_, ee) in enumerate(rows) if ee is e)
        if ys[i0] >= y_top - 1: keep.add(id(e))
    for i in range(n - 1, -1, -1):
        (who, s, sz, first, pre), e = rows[i]; lh = lhs[i]; y = ys[i]
        if id(e) not in keep: continue
        age = sum(1 for (_, ee) in rows[i + 1:] if ee is not e and _[3])
        i0 = next(j for j, (_, ee) in enumerate(rows) if ee is e)
        op = max(0.32, 1 - age * 0.13) * clamp((ys[i0] - y_top) / (lhs[i0] * 0.8) + 0.25)
        x = X0
        if who == "u":
            if first: text(img, "❯ ", x, y, sz, GREEN, op, F_MONOB)
            w2 = text(img, s, x + pre, y, sz, INK, op, F_MONOB)
            if e is typing_e and i == n - 1: SC.cursor(img, x + pre + w2 + sz * 0.12, y + sz * 0.18, int(sz * 1.05), t, GREEN, op)
        elif who == "c":
            if first: cv2.circle(img, (int(x + sz * 0.3), int(y + sz * 0.72)), int(sz * 0.2), (AMBER * op + img[int(y + sz * 0.72), int(x + sz * 0.3)] * (1 - op)).tolist(), -1, cv2.LINE_AA)
            text(img, s, x + pre, y, sz, AMBER, op, F_MONOB)
        elif who == "ok": text(img, s, x, y, sz, GREEN, op, F_MONOB)
        else: text(img, s, x, y, sz, MUTE, op, F_MONO)


# ------------------------------------------------------------------ intro
INTRO = [dict(e) for e in SC.INTRO_LOG]
for e in INTRO:
    if e["who"] == "s": e["text"] = e["text"].strip()


def scene_intro(img, t):
    out = 1 - sstep(K["drop"] - 0.12, K["drop"] + 0.1, t)
    cov = 1 - sstep(T_HEY - 0.32, T_HEY + 0.02, t)
    wall(img, t, cov * out)
    yb = lerp(170, 820, ease_io(cov))
    welcome(img, t, yb, out)
    header(img, (1 - cov) * out)
    if t >= T_HEY - 0.05:
        draw_log(img, t, INTRO, 64, 46, 1440, 430)


# ------------------------------------------------------------------ the beat drops: everything she has made
def scene_boot(img, t):
    t0 = K["drop"] + 0.05; t1 = K["v1"] - 0.25
    header(img)
    text(img, "❯ ls ~/Original\\ Music", X0, 180, 46, INK, 1.0, F_MONOB)
    n = len(SC.FOLDERS); k = clamp((t - t0) / (t1 - t0)); shown = min(n, int(n * k) + 1)
    fs = 40; lh = fs * 1.42; top, yb = 270, 1010
    vis = int((yb - top) / lh); first = max(0, shown - vis)
    last_t = t0 + (t1 - t0) * (shown - 1) / n
    slide = (1 - ease_out((t - last_t) / 0.1)) * lh
    maxw = 1080 * SAFE_R - X0 - tw("✓ ", fs)
    for i in range(first, shown):
        y = yb - (shown - i) * lh + slide
        if y < top - lh * 0.2: continue
        o = clamp((y - top) / lh + 0.3)
        a = text(img, "✓ ", X0, y, fs, GREEN, o, F_MONOB)
        name = SC.FOLDERS[i] + "/"
        while tw(name, fs, F_MONO) > maxw: name = name[:-3] + "…/" if not name.endswith("…/") else name[:-3] + "…/"
        text(img, name, X0 + a, y, fs, AMBER if SC.FOLDERS[i] == "Look What I Can Do" else INK, o, F_MONO)
    cx, cy = (X0 + 1080 * SAFE_R) / 2, 1200
    pop = env(t, last_t, 0.02, 0.12)
    text(img, str(shown), cx, cy, 300 * (1 + 0.05 * pop), AMBER, 1.0, F_ANTON, anchor="c")
    lab = "projects" if t < t1 - 0.45 else "projects · 0 video editors"
    text(img, lab, cx, cy + 205, 44, INK, 1.0, F_MONOB, anchor="c")


# ------------------------------------------------------------------ verse 1
REGION = (56, 200, 1024, 850)
V1 = [dict(e) for e in SC.V1_LOG]
for e in V1:
    if e["text"].startswith("epochs: 0"): e["text"] = "epochs: 0 · training data: none"


def board(img, t, dim):
    """scene.v1_board for 9:16: same build (each video opens big, then settles), panes without header labels."""
    region = REGION; gap = 14
    times = [p[0] for p in SC.V1_PANES]
    k_n = sum(1 for x in times if t >= x - 0.02)
    if k_n == 0: return
    t_k = times[k_n - 1]; a = ease_out((t - t_k + 0.02) / 0.3)
    new = SC._cells(SC._V1_GRID[k_n], region, gap); old = SC._cells(SC._V1_GRID[max(1, k_n - 1)], region, gap) if k_n > 1 else new
    if k_n >= 7:                                      # 7-8 panes on a 3x3: centre the last row (no hole bottom-right)
        def cen(cells, n):
            last = cells[6:n]; ncols = 3
            if not last: return cells
            off = (ncols - len(last)) * (cells[1][0] - cells[0][0]) / 2
            return cells[:6] + [(c[0] + off,) + tuple(c[1:]) for c in last] + cells[n:]
        new = cen(new, k_n); old = cen(old, k_n - 1) if k_n - 1 >= 7 else old
    for i in range(k_n):
        t0, kind, clip, fname = SC.V1_PANES[i]
        if i < k_n - 1: r = tuple(lerp(u, v, a) for u, v in zip(old[i], new[i]))
        elif kind == "clip":
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
        x, y, w, h = r; o = min(1, a * 1.5) if i == k_n - 1 else 1.0
        if kind == "wave": SC.wave_pane(img, x, y, w, h, t, o, 1.0)
        elif kind == "roll": SC.roll_pane(img, x, y, w, h, t, o, 1.0)
        else:
            tc = 5.0 + 0.22 * max(0.0, t - t0 - 0.5) if clip.startswith("site-tour") else t - t0
            SC.pane(img, x, y, w, h, clip, tc, None, "", o, 1.0, hdr=False)
        if kind in ("wave", "roll"):            # a clean window bar instead of the 15 px labels
            hh = int(max(18, min(34, h * 0.16))); rect(img, x + 2, y + 2, w - 4, hh - 2, HDR, o)
        if i == k_n - 1 and t - t0 < 0.3: rrect(img, x, y, w, h, 10, border=GREEN, border_op=o * (1 - (t - t0) / 0.3))
    if t >= K["eleven"] - 0.05:
        e0 = K["eleven"]; dt = 60 / SC.T.tempo / 4
        rects = SC.grid_rects(16, *region, 10)
        order = [5, 10, 0, 15, 6, 3, 12, 9, 1, 14, 7]
        fade = 1 - sstep(K["training"] + 0.1, K["training"] + 0.5, t)
        if fade > 0.01:
            rrect(img, region[0] - 8, region[1] - 8, region[2] - region[0] + 16, region[3] - region[1] + 16, 10, fill=BG, fill_op=0.6 * sstep(e0, e0 + 0.12, t) * fade)
        for j, ri in enumerate(order):
            tj = e0 + j * dt
            if t < tj: continue
            kk = ease_out((t - tj) / 0.12); x, y, w, h = rects[ri]
            clip, fname, off = SC.lib(j * 3 + 1)
            SC.pane(img, x + w * (1 - kk) / 2, y + h * (1 - kk) / 2, w * kk, h * kk, clip, t - tj + off, None, fname, fade, 1.0, hdr=False)
    if dim > 0: rrect(img, region[0] - 10, region[1] - 10, region[2] - region[0] + 20, region[3] - region[1] + 20, 10, fill=BG, fill_op=dim)


def scene_v1(img, t):
    header(img)
    board(img, t, 0.4 * sstep(K["training"] + 0.2, K["training"] + 0.8, t))
    e0 = K["eleven"]
    if e0 - 0.05 <= t < K["direct"]:
        dt = 60 / SC.T.tempo / 4; cnt = min(11, int((t - e0) / dt) + 1)
        o = sstep(e0 - 0.05, e0 + 0.05, t) * (1 - sstep(K["job"] - 0.2, K["job"] + 0.2, t))
        pop = env(t, e0 + (cnt - 1) * dt, 0.02, 0.1)
        text(img, str(cnt), X0, 868, 140 * (1 + 0.04 * pop), AMBER, o, F_ANTON)
        text(img, "things last night", X0 + 190, 930, 44, INK, o, F_MONOB)
    top = 1060 if t < K["job"] + 0.25 else 940
    draw_log(img, t, V1, 58, 44, 1460, top, comma=True)


def compose(t, W, H):
    img = np.empty((H, W, 3), np.float32); img[:] = BG
    if t < K["drop"]: scene_intro(img, t)
    elif t < K["v1"] - 0.1: scene_boot(img, t)
    else: scene_v1(img, t)
    return img


def render_frame(t, W, H):
    fi = int(round(t * 30))
    if W >= H: return SC.render_frame(t, W, H, fi)
    img = compose(t, W, H)
    flash = 0.35 * env(t, K["drop"], 0.02, 0.18)
    return C.finish(img, t, fi, 1e9, flash=flash, flash_col=SC.WHITE * 0.8, glitch_amt=0.0, ca=0.0012, vignette=True)
