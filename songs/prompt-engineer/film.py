"""Prompt Engineer - "Stitch by Stitch". One wedding cloth, cross-stitched by a single red thread.

World 480 x 270 cells, nine panels of 150 x 80:
  A1 intro sampler | A2 title     | A3 bedroom
  B1 wedding       | B2 the stage | B3 the chat window
  C1 kitchen       | C2 the toast | C3 Mama's sampler
"""
import json, math, os, sys
import numpy as np, cv2
import engine as E, art, figures as F
from engine import C, ERASE, smoothstep
from art import A, canvas, paste

SERIF = "EBGaramond-SemiBold.ttf"
ANTON = "Anton-Regular.ttf"
BJ = json.load(open(os.path.join(E.HERE, "beats.json")))
BEATS = np.array(BJ["beats"])
DUR = 251.56
NFRAMES = int(round(DUR * E.FPS))


def bi(t):
    return int(np.searchsorted(BEATS, t + 1e-4, side="right")) - 1


def beats_from(t, n):
    i = int(np.searchsorted(BEATS, t - 0.02))
    return [float(b) for b in BEATS[i:i + n]]


def beat_phase(t):
    i = bi(t)
    if i < 0 or i >= len(BEATS) - 1:
        return 0.0
    return float((t - BEATS[i]) / (BEATS[i + 1] - BEATS[i]))


W = E.World(480, 270)


def alive(t, late=False):
    """When the whole cloth dances: the wide shot in the middle and the finale."""
    return t >= 213.5 or (not late and 162.0 <= t < 177.5)
NEEDLE = []      # (t0, t1, x0, y0, x1, y1, amp, rgb)
FITS = []        # text-fit records


def _reverse_cols(idx, t0, dur):
    return art.order_cols(idx[:, ::-1], t0, dur)[:, ::-1].copy()


ORD = {"cols": art.order_cols, "rows": art.order_rows, "radial": art.order_radial, "rand": art.order_rand,
       "up": art.order_up, "down": art.order_down}


def put(idx, x, y, t=None, dur=0.3, order="cols", off=None, offdur=0.2, needle=False, half=True, rgb=None, **kw):
    idx = np.asarray(idx, np.uint8)
    if t is None:
        ton = -1e9
    elif dur <= 0:
        ton = float(t)
    else:
        ton = ORD[order](idx, t, dur, **kw)
    toff = 1e9
    if off is not None:
        toff = _reverse_cols(idx, off, offdur) if offdur > 0 else float(off)
    W.add(idx, x, y, ton, toff, half=half)
    if needle and t is not None:
        h, w = idx.shape
        NEEDLE.append((t, t + max(dur, 0.12), x, y + h / 2, x + w, y + h / 2, h / 2, rgb or E.PALETTE[1][1]))
    return idx


def swap(x, y, seq, end=1e9, bloom=None):
    """Stop-motion: seq = [(t, sprite)], each shown until the next. bloom = (dur, order) for the first."""
    for i, (t, sp) in enumerate(seq):
        nxt = seq[i + 1][0] if i + 1 < len(seq) else end
        if i == 0 and bloom:
            ton = ORD[bloom[1]](sp, t, bloom[0])
            W.add(sp, x, y, ton, nxt, half=True)
        else:
            W.add(sp, x, y, float(t), nxt, half=False)


def fit(label, x, y, idx, box, pad=1):
    """Record a text block against its container (cells). box = (x0, y0, x1, y1) exclusive."""
    h, w = idx.shape
    ok = x - box[0] >= pad and y - box[1] >= pad and box[2] - (x + w) >= pad and box[3] - (y + h) >= pad
    FITS.append(dict(label=label, text=(x, y, x + w, y + h), box=box, pad=pad, ok=bool(ok)))
    return ok


def txt(s, color="black", font="57"):
    return art.text(s, color, font)[0]


def big(s, color, px, font=SERIF):
    return art.big_text(s, color, px, font)[0]


def put_big_words(text, color, px, x, y, times, off=None, offdur=0.4, font=SERIF, rgb=None):
    """Display lettering revealed word by word on the sung words; the needle follows each word."""
    arr, spans = art.big_text(text, color, px, font)
    ton = np.full(arr.shape, 1e9, np.float32)
    i = 0
    for wd, t in zip(text.split(" "), times):
        a, e = spans[i][0], spans[i + len(wd) - 1][1]
        d = min(0.32, 0.05 * len(wd) + 0.08)
        ton[:, a:e] = art.order_cols(arr[:, a:e], t, d)
        NEEDLE.append((t, t + d, x + a, y + arr.shape[0] / 2, x + e, y + arr.shape[0] / 2, arr.shape[0] / 2, rgb or E.PALETTE[1][1]))
        i += len(wd)
    toff = 1e9 if off is None else _reverse_cols(arr, off, offdur)
    W.add(arr, x, y, ton, toff)
    return arr


def PO(col, row):
    return 9 + 156 * col, 9 + 86 * row


def ribbon(w, h, col="white", edge="red"):
    out = canvas(w, h, C[col])
    out[0, :] = C[edge]; out[-1, :] = C[edge]
    out[:, 0] = C[edge]; out[:, -1] = C[edge]
    out[0, 0] = out[0, -1] = out[-1, 0] = out[-1, -1] = 0
    return out


def check_mark(col="gold", s=1):
    a = A("""
        .........GG
        ........GG.
        .......GG..
        GG....GG...
        .GG..GG....
        ..GGGG.....
        ...GG......
    """)
    return art.recolor(a, {"gold": col})


def plus_spark(col="gold"):
    return art.recolor(A("""
        .G.
        GGG
        .G.
    """), {"gold": col})


# =============================================================================== frame: border + dividers
def build_frame():
    def ton_from(idx, x, y):
        h, w = idx.shape
        yy, xx = np.mgrid[0:h, 0:w]
        d = np.hypot(xx + x - 84, yy + y - 49)
        return (11.3 + 1.7 * np.clip(d / 430, 0, 1)).astype(np.float32)

    top = art.border_band(478, 0)
    W.add(top, 1, 1, ton_from(top, 1, 1))
    W.add(top, 1, 262, ton_from(top, 1, 262))
    side = art.border_band(254, 0).T.copy()
    W.add(side, 1, 8, ton_from(side, 1, 8))
    W.add(side, 472, 8, ton_from(side, 472, 8))
    for gy in (90, 176):
        z = art.zigzag(462, "red", 3)
        W.add(z, 9, gy + 1, ton_from(z, 9, gy + 1))
    for gx in (160, 316):
        z = art.zigzag(252, "red", 3).T.copy()
        W.add(z, gx + 1, 9, ton_from(z, gx + 1, 9))

    # the border marches on the beat once the cloth is alive
    def march(t):
        if not ((162.0 <= t < 177.5) or t >= 213.5):
            return ()
        ph = bi(t) % 8
        b = art.border_band(478, ph)
        s = art.border_band(254, ph).T
        return [(b, 1, 1), (b[:, ::-1], 1, 262), (s, 472, 8), (s[::-1], 1, 8)]
    W.dynamic(march)

    # gold knots where the dividers cross: the last things to bloom
    for i, (gx, gy) in enumerate(((162, 92), (318, 92), (162, 178), (318, 178))):
        d = art.diamond(3, ["gold", "red", "gold", "black"])
        put(d, gx - 3, gy - 3, t=232.2 + i * 0.4, dur=0.25, order="radial")


# =============================================================================== A1 intro sampler
A1 = {}


def build_intro():
    ox, oy = PO(0, 0)
    p1 = big("Please,", "red", 22)
    p2 = big("please", "red", 22)
    x1 = ox + (150 - (p1.shape[1] + 6 + p2.shape[1])) // 2
    y1 = oy + 10
    # "Please," - the first four stitches land on the first four beats, in macro
    ton = art.order_cols(p1, 2.0, 0.72)
    ys, xs = np.where(p1 > 0)
    c0 = max(range(xs.min(), xs.min() + 7), key=lambda c: (xs == c).sum())
    col_rows = sorted(ys[xs == c0])
    stem = [(c0, r) for r in col_rows[3:7]]
    for (cx_, r), b in zip(stem, BEATS[:4]):
        ton[r, cx_] = b
    W.add(p1, x1, y1, ton)
    A1["stem"] = [(x1 + cx_, y1 + r) for cx_, r in stem]
    NEEDLE.append((2.0, 2.72, x1, y1 + 10, x1 + p1.shape[1], y1 + 10, 8, E.PALETTE[1][1]))
    x2 = x1 + p1.shape[1] + 6
    put(p2, x2, y1 + 1, t=2.8, dur=0.7, needle=True)
    A1["please"] = (x1 + (p1.shape[1] + 6 + p2.shape[1]) / 2, y1 + 11)
    # flourish under the words, a quarter per beat, then two tulips
    fl = art.zigzag(112, "gold", 3)
    bts = beats_from(4.0, 4)
    tf = np.zeros(fl.shape, np.float32)
    for q in range(4):
        tf[:, q * 28:(q + 1) * 28] = art.order_cols(fl[:, q * 28:(q + 1) * 28], bts[q], 0.3)
    W.add(fl, ox + 19, y1 + 26, tf)
    NEEDLE.append((bts[0], bts[3] + 0.3, ox + 19, y1 + 27, ox + 131, y1 + 27, 1.5, E.PALETTE[6][1]))
    put(plus_spark("red"), ox + 14, y1 + 26, t=beats_from(5.8, 1)[0], dur=0.15, order="radial")
    put(plus_spark("red"), ox + 133, y1 + 26, t=beats_from(6.2, 1)[0], dur=0.15, order="radial")
    # think it through
    yT = y1 + 31
    xT = ox + 14
    for word, tw in (("think", 6.64), ("it", 7.04), ("through", 7.20)):
        g = txt(word)
        put(g, xT, yT, t=tw, dur=0.22, needle=True, rgb=E.PALETTE[3][1])
        xT += g.shape[1] + 4
    # the staircase: STEP / BY / STEP, one tread per word
    sx, sy = ox + 24, yT + 9
    A1["steps"] = []
    for i, (word, tw) in enumerate((("STEP", 7.60), ("BY", 8.16), ("STEP", 8.48))):
        g = big(word, "red" if i != 1 else "black", 14, ANTON)
        put(g, sx, sy, t=tw, dur=0.2, needle=True)
        last = (i == 2)
        tread = canvas(g.shape[1] + (26 if last else 5), 1, C["black"])      # the last tread runs on as the floor he stands on
        put(tread, sx - 1, sy + g.shape[0] + 1, t=tw + 0.12, dur=0.15 if not last else 0.3)
        if not last:
            riser = canvas(1, 7, C["black"])
            put(riser, sx + g.shape[1] + 3, sy + g.shape[0] + 1, t=tw + 0.2, dur=0.1, order="down")
        A1["steps"].append((sx + g.shape[1] / 2, sy + 6))
        floor_y = sy + g.shape[0] + 1
        sx += g.shape[1] + 4
        sy += 7
    # him, at the foot of the stairs, asking nicely: the first person on the cloth (0:06)
    hx_, hy_ = ox + 101, floor_y - 31
    A1["him"] = (hx_ + 8, hy_ + 15)
    seq = [(6.25, F.him_plead(0))]
    for tw in (6.64, 7.04, 7.20, 7.60, 8.16, 8.48):
        seq.append((tw, F.him_plead(1)))
        seq.append((tw + 0.2, F.him_plead(0)))
    seq.append((10.24, F.him_plead(1)))
    seq.append((10.9, F.him_plead(0, happy=1)))
    swap(hx_, hy_, seq, bloom=(0.5, "up"))
    A1["heart"] = (hx_ + 8, hy_ + 5)
    for i, (dx, dy) in enumerate(((-4, 2), (19, 1), (-5, 12), (20, 11))):
        put(plus_spark("gold" if i % 2 == 0 else "red"), hx_ + dx, hy_ + dy, t=10.3 + 0.1 * i, dur=0.1, order="radial")
    # corners bloom when the camera pulls back
    for (dx, dy) in ((3, 3), (134, 3), (3, 64), (134, 64)):
        d = art.diamond(6, ["gold", "red", "black", "red"])
        put(d, ox + dx, oy + dy, t=11.35, dur=0.9, order="radial")


# =============================================================================== A2 title
def build_title():
    ox, oy = PO(1, 0)
    b = beats_from(13.17, 30)
    t1, sp1 = art.big_text("PROMPT", "red", 24, ANTON)
    t2, sp2 = art.big_text("ENGINEER", "black", 24, ANTON)
    x1 = ox + (150 - t1.shape[1]) // 2
    x2 = ox + (150 - t2.shape[1]) // 2
    y1, y2 = oy + 6, oy + 29
    k = 0
    for (tx, sp, x, y) in ((t1, sp1, x1, y1), (t2, sp2, x2, y2)):
        ton = np.full(tx.shape, 1e9, np.float32)
        for (a, e) in sp:
            sub = tx[:, a:e]
            ton[:, a:e] = art.order_up(sub, b[k], 0.24)
            NEEDLE.append((b[k], b[k] + 0.24, x + a, y + 10, x + e, y + 10, 9, E.PALETTE[1][1]))
            k += 1
        W.add(tx, x, y, ton)
    # side medallions bloom ring by ring on the beat
    ring_cols = ["gold", "red", "red", "black", "white", "red", "black", "gold", "red", "black", "red", "black"]
    for sx_ in (ox + 4, ox + 150 - 4 - 23):
        d = art.diamond(11, ring_cols)
        put(d, sx_, oy + 16, t=0, order="radial", dur=1)
        W.elems[-1][3] = art.order_beats(d, b[4:16], 0.2)
        W.elems[-1][5] = b[4]
    med = [art.diamond(11, ring_cols[-i:] + ring_cols[:-i]) for i in range(12)]

    def march_rings(t):
        if not (b[16] <= t < 26.5 or 162.0 <= t < 177.5 or t >= 213.5):
            return ()
        m = med[bi(t) % 12]
        return [(m, ox + 4, oy + 16), (m, ox + 150 - 4 - 23, oy + 16)]
    W.dynamic(march_rings)
    for i, sx_ in enumerate((ox + 8, ox + 18, ox + 127, ox + 137)):
        put(art.tulip(), sx_, oy + 43, t=b[16 + i], dur=0.3, order="up")
    for i, xx in enumerate(range(ox + 30, ox + 121, 9)):
        put(plus_spark("gold" if i % 2 == 0 else "red"), xx, oy + 1, t=b[6 + i], dur=0.12, order="radial")
    # the valle: one dancer joins per beat, then they never stop
    kinds = "mwmwmwmw"
    x0 = ox + 9
    joins = beats_from(10.4, len(kinds) + 1)

    def line(t):
        if t < joins[0]:
            return ()
        pose = bi(t) % 4
        hop = -1 if pose % 2 else 0
        out = []
        for i, kd in enumerate(kinds):
            if t >= joins[i]:
                out.append((F.dancer(kd, pose), x0 + 14 * i, oy + 54 + hop))
        if t >= joins[-1]:
            out.append((F.dancer_lead(pose), x0 + 14 * len(kinds), oy + 54 - 3 + hop))
        return out
    W.dynamic(line)
    put(canvas(140, 1, C["black"]), ox + 5, oy + 79, t=10.0, dur=0.5)


# =============================================================================== A3 bedroom
A3 = {}


def build_bedroom():
    ox, oy = PO(2, 0)
    put(canvas(144, 1, C["brown"]), ox + 3, oy + 73, t=22.6, dur=0.8)
    # little rug
    put(art.border_band(56, 2), ox + 3, oy + 74, t=23.0, dur=0.6)
    bx, by = ox + 6, oy + 44
    swap(bx, by, [(22.8, F.bed(0)), (25.92, F.bed(1)), (28.3, F.bed(2))], bloom=(1.2, "up"))
    wx, wy = ox + 44, oy + 4
    swap(wx, wy, [(23.2, F.house_window(0)), (26.80, F.house_window(1)), (27.25, F.house_window(2))], bloom=(1.0, "radial"))
    A3["window"] = (wx + 22, wy + 17)
    # "Not the real one": the thread crosses it out
    X = canvas(30, 30)
    for i in range(30):
        for d in (0, 1):
            if 0 <= i + d < 30:
                X[i, i + d] = C["red"]; X[i, 29 - i - d] = C["red"]
    tx = np.full(X.shape, 1e9, np.float32)
    yy, xx = np.mgrid[0:30, 0:30]
    diag1 = (np.abs(xx - yy) <= 1)
    tx[diag1] = 28.96 + 0.25 * (yy[diag1] / 30)
    tx[~diag1] = 29.44 + 0.25 * (yy[~diag1] / 30)
    W.add(X, wx + 7, wy + 2, tx)
    NEEDLE.append((28.96, 29.21, wx + 7, wy + 2, wx + 37, wy + 32, 0.5, E.PALETTE[1][1]))
    NEEDLE.append((29.44, 29.69, wx + 37, wy + 2, wx + 7, wy + 32, 0.5, E.PALETTE[1][1]))
    # the desk
    dx, dy = ox + 100, oy + 34
    A3["desk"] = (dx + 20, dy + 16)
    swap(dx, dy, [(23.6, F.desk_scene("type")), (32.6, F.desk_scene("crack")), (33.5, F.desk_scene("crack2")),
                  (34.05, F.desk_scene("crack")), (34.56, F.desk_scene("surgeon")), (35.9, F.desk_scene("type"))],
         bloom=(1.0, "up"))
    def desk_dance(t):
        if not alive(t):
            return ()
        return [(F.desk_scene("surgeon" if bi(t) % 2 else "type"), dx, dy)]
    W.dynamic(desk_dance)
    # bedside table: the alarm clock that wakes him
    nx, ny = ox + 56, oy + 51
    swap(nx, ny, [(23.9, F.nightstand(0))] + [(float(bt), F.nightstand(1 + i % 2)) for i, bt in enumerate(np.arange(25.2, 26.35, 0.11))]
         + [(26.4, F.nightstand(0))], bloom=(0.6, "up"))
    # wall: a framed heart sampler above the desk
    fr = art.frame_rect(13, 11, "brown")
    paste(fr, art.heart(), 3, 3)
    put(fr, ox + 116, oy + 12, t=24.0, dur=0.5, order="radial")


# =============================================================================== B3 the chat window
B3 = {}


def build_chat():
    ox, oy = PO(2, 1)
    g = lambda x, y: (ox + x, oy + y)
    T0 = 29.6
    # ---- chrome
    body = art.rounded_rect(150, 80, "cream", 3)
    put(body, ox, oy, t=T0, dur=1.3, order="radial", cx=0, cy=0, power=0.8)
    bar = art.rounded_rect(150, 7, "bubble", 3)
    bar[4:, :] = C["bubble"]
    for i, col in enumerate(("red", "yellow", "lgreen")):
        bar[2:5, 4 + i * 5:7 + i * 5] = C[col]
    put(bar, ox, oy, t=T0 + 0.1, dur=0.8, order="cols")
    ttl = txt("Claude", "grey", "35")
    put(ttl, ox + 75 - ttl.shape[1] // 2, oy + 1, t=T0 + 0.9, dur=0.3)
    fit("window title", 75 - ttl.shape[1] // 2, 1, ttl, (20, 0, 150, 7), 1)
    side = canvas(16, 73, C["bubble"])
    side[-1, 0] = 0; side[-2, 0] = 0; side[-1, 1] = 0
    paste(side, A("""
        ddddddd
        d.d...d
        d.d...d
        d.d...d
        ddddddd
    """), 4, 4)
    paste(side, A("""
        ..TTT..
        .TTWTT.
        TTTWTTT
        TWWWWWT
        TTTWTTT
        .TTWTT.
        ..TTT..
    """), 4, 13)
    # the rail's own icons, as in the app with the sidebar closed: chats, projects
    paste(side, A("""
        .yyyyy.
        y.....y
        y.....y
        .yyyyy.
        ..y....
        .y.....
    """), 4, 25)
    paste(side, A("""
        yyy....
        yyyyyyy
        y.....y
        y.....y
        yyyyyyy
    """), 4, 36)
    paste(side, A("""
        ..NNNNN..
        .NNNNNNN.
        NNNSSSNNN
        NNNSSSNNN
        NNNNNNNNN
        NNSSSSSNN
        .NSSSSSN.
        ..NNNNN..
    """), 3, 62)
    put(side, ox, oy + 7, t=T0 + 0.3, dur=0.9, order="down")
    B3["center"] = (ox + 75, oy + 40)

    # ---- state NEW (30.4 .. 47.0): the app's home screen. Greeting, the input box (it grows a line at a time as he
    # types, as the real one does), the + and the model picker, the send button, and the suggestion chips under it.
    OFF1 = 47.0
    st = art.star8(4, "terra")
    gm = big("Good morning", "black", 15)
    gx = 17 + (133 - (9 + 4 + gm.shape[1])) // 2
    put(st, *g(gx, 11), t=T0 + 1.2, dur=0.4, order="radial", off=OFF1)
    put(gm, *g(gx + 13, 8), t=T0 + 1.3, dur=0.7, off=OFF1, needle=True, rgb=E.PALETTE[3][1])
    BX, BY, BW = 22, 26, 124
    HB = {1: 27, 2: 36, 3: 45}                                   # box height by number of typed lines
    BH = HB[3]
    GROW = [(T0 + 1.5, 1), (38.40, 2), (39.72, 1), (42.00, 2), (44.56, 3)]
    boxes = {n: art.rounded_rect(BW, h, "white", 3, outline="bubble") for n, h in HB.items()}
    swap(ox + BX, oy + BY, [(t_, boxes[n]) for t_, n in GROW[:-1]], end=GROW[-1][0], bloom=(0.7, "radial"))
    put(boxes[3], *g(BX, BY), t=GROW[-1][0], dur=0, off=OFF1, offdur=0.3)
    ph = txt("How can I help you today?", "grey", "35")
    put(ph, *g(BX + 6, BY + 6), t=T0 + 2.0, dur=0.5, off=36.7, offdur=0.12)
    fit("chat placeholder", BX + 6, BY + 6, ph, (BX, BY, BX + BW, BY + HB[1]), 2)
    # controls row: it rides the bottom edge of the box
    plus = A("""
        ..d..
        ..d..
        ddddd
        ..d..
        ..d..
    """)
    mdl = txt("Fable 5.2", "grey")
    chev = A("""
        y...y
        .y.y.
        ..y..
    """)
    mdl2 = canvas(mdl.shape[1] + 8, 7)
    paste(mdl2, mdl, 0, 0); paste(mdl2, chev, mdl.shape[1] + 3, 2)
    mdl = mdl2

    def send_btn(col="terra"):
        s = art.rounded_rect(9, 9, col, 2)
        s[2:7, 4] = C["white"]
        s[3, 3] = C["white"]; s[3, 5] = C["white"]; s[4, 2] = C["white"]; s[4, 6] = C["white"]
        return s
    for i, (t_, n) in enumerate(GROW):
        t1_ = GROW[i + 1][0] if i + 1 < len(GROW) else OFF1
        yb = BY + HB[n]
        first, last = i == 0, i == len(GROW) - 1
        put(plus, *g(BX + 6, yb - 9), t=t_ + (0.6 if first else 0), dur=0.2 if first else 0, off=t1_, offdur=0)
        mx_ = BX + BW - 17 - mdl.shape[1] - 3
        put(mdl, *g(mx_, yb - 10), t=t_ + (0.7 if first else 0), dur=0.3 if first else 0, off=t1_, offdur=0)
        fit("model selector (%d lines)" % n, mx_, yb - 10, mdl, (BX, BY, BX + BW - 14, yb), 2)
        seq = [(t_ + (0.8 if first else 0), send_btn())]
        if last:
            seq += [(46.85, send_btn("dred")), (47.0, send_btn())]
        swap(ox + BX + BW - 13, oy + yb - 12, seq, end=t1_ if not last else 47.15, bloom=(0.2, "radial") if first else None)
    B3["box"] = (ox + BX + BW / 2, oy + BY + BH / 2)
    # suggestion chips under the box: they ride down with it, and leave when the third line needs the room
    chips = ["Write", "Learn", "Code"]
    cw = [art.text_w(c_) + 8 for c_ in chips]
    for i, (t_, n) in enumerate(GROW[:-1]):
        t1_ = GROW[i + 1][0]
        first = i == 0
        cx_ = BX + (BW - (sum(cw) + 5 * (len(chips) - 1))) // 2
        CY = BY + HB[n] + 4
        for j, c_ in enumerate(chips):
            pill = art.rounded_rect(cw[j], 11, "cream", 3, outline="bubble")
            put(pill, *g(cx_, CY), t=t_ + ((0.45 + 0.1 * j) if first else 0), dur=0.15 if first else 0, order="radial", off=t1_, offdur=0)
            ct = txt(c_, "dgrey")
            put(ct, *g(cx_ + 4, CY + 2), t=t_ + ((0.52 + 0.1 * j) if first else 0), dur=0.15 if first else 0, off=t1_, offdur=0)
            fit("chip %s (%d lines)" % (c_, n), cx_ + 4, CY + 2, ct, (cx_, CY, cx_ + cw[j], CY + 11), 2)
            fit("chip row %s in window (%d lines)" % (c_, n), cx_, CY, pill, (17, 7, 150, 80), 2)
            cx_ += cw[j] + 5

    # typing, line by line, word by word
    LX, LY = BX + 6, BY + 5

    def type_words(words, x, y, off, color="black", space=4, label=None, boxr=None):
        """words = [(text, t)], returns end x."""
        x0 = x
        for wtxt, tw in words:
            gph = txt(wtxt, color)
            put(gph, ox + x, oy + y, t=tw, dur=min(0.22, 0.035 * len(wtxt) + 0.05), off=off, offdur=0.15, needle=True,
                rgb=E.PALETTE[3][1])
            x += gph.shape[1] + space
        if boxr:
            FITS.append(dict(label=label, text=(x0, y, x - space, y + 7), box=boxr, pad=2,
                             ok=bool(x - space <= boxr[2] - 2 and x0 >= boxr[0] + 2 and y >= boxr[1] + 2 and y + 7 <= boxr[3] - 2)))
        return x

    br = lambda n: (BX, BY, BX + BW, BY + HB[n])
    boxr = br(3)
    # "You are a helpful someone" (as sung) ... he unpicks it
    xe = type_words([("You", 36.80), ("are", 37.04)], LX, LY, OFF1, label="typed line 1", boxr=br(1))
    type_words([("a", 37.36), ("helpful", 37.60)], xe, LY, 39.68, label="typed line 1 (first try)", boxr=br(1))
    type_words([("someone", 38.48)], LX, LY + 9, 39.55, label="typed line 2 (first try)", boxr=br(2))
    type_words([("an", 41.04), ("expert", 41.28)], xe, LY, OFF1, label="typed line 1 final", boxr=br(1))
    type_words([("lawyer.", 42.08), ("30", 43.52), ("years.", 44.16)], LX, LY + 9, OFF1, label="typed line 2", boxr=br(2))
    type_words([("You", 44.64), ("passed", 44.96), ("the", 45.52), ("bar.", 45.84)], LX, LY + 18, OFF1, label="typed line 3", boxr=br(3))

    # ---- state CONVO (47.2 .. 53.5)
    OFF2 = 53.45
    lines = ["You are an expert", "lawyer. 30 years.", "You passed the bar."]
    bw = max(art.text_w(s) for s in lines) + 8
    bub = art.rounded_rect(bw, 33, "bubble", 3)
    bx_ = 146 - bw
    put(bub, *g(bx_, 9), t=47.2, dur=0.35, order="radial", off=OFF2, offdur=0.25)
    for i, s in enumerate(lines):
        gph = txt(s)
        put(gph, *g(bx_ + 4, 13 + i * 9), t=47.3 + i * 0.08, dur=0.25, off=OFF2, offdur=0.25)
        fit("sent bubble line %d" % (i + 1), bx_ + 4, 13 + i * 9, gph, (bx_, 9, bx_ + bw, 42), 2)
    SX, SY = 20, 40
    B3["star1"] = (ox + SX + 12.5, oy + SY + 12.5)
    swap(ox + SX, oy + SY, [(47.75, F.star("plain")), (49.2, F.star("sad")), (50.80, F.star("happy"))], end=OFF2, bloom=(0.3, "radial"))
    scales = A("""
        ......G......
        .GGGGGGGGGGG.
        .G....G....G.
        .G....G....G.
        GGG...G...GGG
        GGG...G...GGG
        ......G......
        ....GGGGG....
    """)
    scales = art.recolor(scales, {"gold": "black"})
    put(scales, *g(SX + 26, SY + 1), t=50.9, dur=0.3, off=OFF2)
    rep = txt("Ready, counsel.")
    put(rep, *g(SX + 28, SY + 13), t=52.0, dur=0.6, off=OFF2, needle=True, rgb=E.PALETTE[3][1])
    fit("reply 1", SX + 28, SY + 13, rep, (17, 7, 150, 80), 2)
    sbox = art.rounded_rect(BW, 13, "white", 3, outline="bubble")
    put(sbox, *g(BX, 65), t=47.4, dur=0.3, order="radial", off=OFF2)
    rp = txt("Reply to Claude...", "grey")
    put(rp, *g(BX + 6, 68), t=47.6, dur=0.2, off=OFF2)
    fit("reply placeholder", BX + 6, 68, rp, (BX, 65, BX + BW, 78), 2)

    # ---- state PRE (compose view), used by both verses
    def pre_state(t0, off, lines4, star_seq, top_text, dots_until, send_t, lx=6):
        PX, PY, PW, PH = 22, 34, 124, 44
        pbox = art.rounded_rect(PW, PH, "white", 3, outline="bubble")
        put(pbox, *g(PX, PY), t=t0, dur=0.35, order="radial", off=off, offdur=0.3)
        pr = (PX, PY, PX + PW, PY + PH)
        for i, words in enumerate(lines4):
            type_words(words, PX + lx, PY + 4 + i * 10, off, label="compose line %d @%.0f" % (i + 1, t0), boxr=pr)
        swap(ox + PX + PW - 13, oy + PY + PH - 12, [(t0 + 0.2, send_btn()), (send_t - 0.12, send_btn("dred")), (send_t + 0.05, send_btn())],
             end=off, bloom=(0.2, "radial"))
        swap(ox + 20, oy + 5, star_seq, end=off, bloom=(0.25, "radial"))
        if top_text:
            tt = txt(top_text[0])
            put(tt, *g(46, 17), t=top_text[1], dur=0.5, off=off, needle=True, rgb=E.PALETTE[3][1])
            fit("reply @%.0f" % t0, 46, 17, tt, (17, 7, 144, 34), 2)

        # thinking dots under the star while he types
        def dots(t):
            if not (t0 + 0.4 <= t < dots_until):
                return ()
            n = bi(t) % 3 + 1
            d = canvas(11, 2)
            for i in range(n):
                d[:, i * 4:i * 4 + 2] = C["terra"]
            return [(d, ox + 46, oy + 22)]
        W.dynamic(dots)
        B3["star2"] = (ox + 20 + 12.5, oy + 5 + 12.5)
        B3["pbox"] = (ox + PX + PW / 2, oy + PY + PH / 2)

    pre_state(53.6, 100.0,
              [[("Please", 53.92), ("and", 54.32), ("thank", 54.48), ("you.", 54.64)],
               [("Step", 55.84), ("by", 56.08), ("step.", 56.24)],
               [("Take", 57.52), ("a", 57.76), ("deep", 57.84), ("breath.", 58.08)],
               [("Don't", 59.52), ("forget.", 59.76)]],
              [(53.6, F.star("plain")), (57.84, F.star("breath")), (59.3, F.star("plain")), (61.1, F.star("happy"))],
              None, 61.1, 61.0)
    for i in range(3):
        put(check_mark(), *g(52 + i * 14, 14), t=61.3 + i * 0.22, dur=0.15, off=100.0)

    # ---- verse 2: the uncle's chat. U1 = what he yelled, then context
    U0, UOFF = 120.0, 131.5
    ylines = ["IT'S BROKE!!!", "IT'S SLOW!!!"]
    bw2 = max(art.text_w(s) for s in ylines) + 8
    bx2 = 146 - bw2
    put(art.rounded_rect(bw2, 24, "bubble", 3), *g(bx2, 9), t=U0, dur=0.3, off=UOFF, offdur=0.25)
    for i, s in enumerate(ylines):
        gph = txt(s)
        put(gph, *g(bx2 + 4, 13 + i * 9), t=U0, dur=0.2, off=UOFF, offdur=0.25)
        fit("uncle bubble line %d" % (i + 1), bx2 + 4, 13 + i * 9, gph, (bx2, 9, bx2 + bw2, 33), 2)
    swap(ox + 20, oy + 28, [(U0, F.star("sad"))], end=UOFF, bloom=(0.2, "radial"))
    um = txt("Um. What is slow?")
    put(um, *g(50, 43), t=129.3, dur=0.5, off=UOFF, needle=True, rgb=E.PALETTE[3][1])
    fit("reply uncle", 50, 43, um, (17, 7, 150, 56), 2)
    ubox = art.rounded_rect(BW, 24, "white", 3, outline="bubble")
    put(ubox, *g(BX, 55), t=U0, dur=0.3, off=UOFF)
    ur = (BX, 55, BX + BW, 79)
    type_words([("My", 129.9), ("laptop", 130.05), ("is", 130.24), ("slow.", 130.4)], BX + 6, 58, UOFF, label="context line 1", boxr=ur)
    type_words([("It", 130.72), ("is", 130.8), ("8", 130.88), ("years", 130.96), ("old.", 131.1)], BX + 6, 67, UOFF, label="context line 2", boxr=ur)
    B3["land"] = (ox + bx2 + bw2 / 2, oy + 21)                   # the zoom-through lands on what he yelled
    # the uncle's own version: still in CAPS (it is how he types), but this time he says please
    pre_state(131.6, 1e9,
              [[("PLEASE", 131.84), ("AND", 132.24), ("THANK", 132.40), ("YOU.", 132.56)],
               [("STEP", 133.76), ("BY", 134.00), ("STEP.", 134.16)],
               [("TAKE", 135.52), ("A", 135.68), ("DEEP", 135.84), ("BREATH.", 136.00)],
               [("DON'T", 137.44), ("FORGET.", 137.68)]],
              [(131.6, F.star("sad")), (132.9, F.star("plain")), (135.84, F.star("breath")), (137.3, F.star("plain")), (139.0, F.star("happy"))],
              ("Now we're talking.", 139.1), 139.0, 138.9, lx=4)


# =============================================================================== B2 the stage
B2 = {}


def stage_chorus(T0, variant):
    """Kinetic stitched type for one chorus. T0 = when "He's" lands."""
    ox, oy = PO(1, 1)
    cx = ox + 75
    top = oy + 2
    area = (ox + 2, oy + 0, ox + 148, oy + 45)      # fit box only: the stage's lettering area (3 bare rows to the divider above)

    def word(arr, x, y, r_on, r_off, dur=0.22, needle=True, label=None, order="cols", rgb=None):
        put(arr, x, y, t=T0 + r_on, dur=dur, off=T0 + r_off, offdur=0.14, needle=needle, order=order, rgb=rgb)
        if label:
            fit("%s (chorus %d)" % (label, variant), x, y, arr, area, 1)

    def shadowed(arr, sh="black"):
        """Lettering with a one-stitch drop shadow (the last chorus)."""
        out = canvas(arr.shape[1] + 1, arr.shape[0] + 1)
        paste(out, np.where(arr > 0, C[sh], 0).astype(np.uint8), 1, 1)
        paste(out, arr, 0, 0)
        return out

    def banner(s_, bg, px=19):
        w_ = big(s_, "white", px, ANTON)
        bn = art.rounded_rect(w_.shape[1] + 8, w_.shape[0] + 4, bg, 2)
        paste(bn, w_, 4, 2)
        FITS.append(dict(label="banner %s (chorus %d)" % (s_, variant), text=(4, 2, 4 + w_.shape[1], 2 + w_.shape[0]),
                         box=(0, 0, bn.shape[1], bn.shape[0]), pad=2, ok=True))
        return bn

    cA, cB = ("red", "black") if variant != 2 else ("black", "red")
    a = big("PROMPT", cA, 22, ANTON); b = big("ENGINEER", cB, 22, ANTON)
    if variant == 2:
        a = banner("PROMPT", "red"); b = banner("ENGINEER", "black")
    if variant == 3:
        a = shadowed(big("PROMPT", "red", 22, ANTON)); b = shadowed(big("ENGINEER", "red", 22, ANTON))
    lift = 1 if variant == 3 else 0          # the shadowed lettering is a row taller: keep it clear of the heads
    word(a, cx - a.shape[1] // 2, top + 0 - lift, 0.5, 3.85, label="PROMPT")
    word(b, cx - b.shape[1] // 2, top + 21 - 2 * lift, 1.15, 3.9, label="ENGINEER")
    # please ... and it worked
    p = big("please", "red", 34)
    px_ = cx - p.shape[1] // 2 - 12
    if variant != 2:
        word(p if variant == 1 else shadowed(p), px_, top + (4 if variant == 1 else 1), 4.05, 7.35, dur=0.4, label="please")
    if variant == 2:
        pass                                                          # said at the wedding table instead (build_wedding)
    else:
        ck = np.kron(check_mark(), np.ones((2, 2), np.uint8))
        word(ck, px_ + p.shape[1] + 6, top + 12, 5.2, 7.4, dur=0.25, rgb=E.PALETTE[6][1], label="check")
    # IMPORTANT in all caps
    imp = big("IMPORTANT", "red", 30, ANTON)
    ix = cx - imp.shape[1] // 2
    if variant == 2:
        # stitched the other way round: a solid red banner, the word left as white thread
        ban = art.rounded_rect(imp.shape[1] + 8, imp.shape[0] + 5, "red", 2)
        paste(ban, np.where(imp > 0, C["white"], 0).astype(np.uint8), 4, 2)
        word(ban, ix - 4, top + 1, 7.5, 9.1, dur=0.3, label="IMPORTANT banner")
    elif variant == 3:
        word(shadowed(imp), ix, top + 3, 7.5, 9.1, dur=0.3, label="IMPORTANT")
    else:
        word(imp, ix, top + 3, 7.5, 9.1, dur=0.3, label="IMPORTANT")
    ul = canvas(imp.shape[1] - 12, 5)
    ul[0:2] = C["black"]; ul[3:5] = C["black"]
    word(ul, ix + 6, top + 3 + imp.shape[0] + 3, 8.72, 9.15, dur=0.25, rgb=E.PALETTE[3][1], label="underline")
    # three examples, then relax
    for i, r in enumerate((9.2, 9.52, 9.84)):
        ex = art.tulip() if variant == 1 else (art.star8(3, "terra", "gold") if variant == 2 else art.heart())
        ex = np.kron(ex, np.ones((2, 2), np.uint8))
        dg = np.kron(art.text(str(i + 1), "black")[0], np.ones((2, 2), np.uint8))
        tl = canvas(16, 34)
        paste(tl, ex, (16 - ex.shape[1]) // 2, 16 - ex.shape[0])
        paste(tl, dg, (16 - dg.shape[1]) // 2, 19)
        word(tl, cx - 57 + i * 20, top + (2 if variant == 3 else 5), r, 10.95, dur=0.16, needle=True, order="up", label="example %d" % (i + 1))
    rl = big("relax", "black", 26, "EBGaramond-MediumItalic.ttf")
    word(rl, cx + 4, top + 11, 10.3, 10.95, dur=0.3, label="relax")
    wav = art.zigzag(50, "gold", 3)
    word(wav, cx + 3, top + 11 + rl.shape[0] + 3, 10.5, 11.0, dur=0.3, needle=False, label="relax line")
    # he's a prompt engineer (colours swapped)
    a2 = big("PROMPT", cB, 22, ANTON); b2 = big("ENGINEER", cA, 22, ANTON)
    if variant == 2:
        a2 = banner("PROMPT", "black"); b2 = banner("ENGINEER", "red")
    if variant == 3:
        a2 = shadowed(big("PROMPT", "black", 22, ANTON), "red"); b2 = shadowed(big("ENGINEER", "black", 22, ANTON), "red")
    word(a2, cx - a2.shape[1] // 2, top + 0 - lift, 11.45, 13.15, label="PROMPT 2")
    word(b2, cx - b2.shape[1] // 2, top + 21 - 2 * lift, 12.05, 13.2, label="ENGINEER 2")
    # think it through, step by step, okay?
    tt = txt("think it through")
    word(tt, ox + 12, top + 2, 13.25, 15.05, dur=0.4, rgb=E.PALETTE[3][1], label="think it through")
    sx, sy = ox + 30, top + 9
    for i, (wd, r) in enumerate((("STEP", 13.8), ("BY", 14.04), ("STEP", 14.2))):
        gph = big(wd, "red" if i != 1 else "black", 14, ANTON)
        word(gph, sx, sy, r, 16.3, dur=0.12, label="stair %d" % i)
        tr = canvas(gph.shape[1] + 5, 1, C["black"])
        word(tr, sx - 1, sy + gph.shape[0] + 1, r + 0.08, 16.3, dur=0.1, needle=False)
        sx += gph.shape[1] + 5
        sy += 9
    ok = big("OK?", "black", 16, ANTON)
    word(ok, sx + 1, sy - 17, 14.5, 16.3, dur=0.15, label="OK?")
    # (flip to the back happens here: 15.15 .. 16.8, handled by the camera)
    mg = big("magic words", "red", 22)
    mx = cx - mg.shape[1] // 2 - 13
    word(mg, mx, top + 6, 16.55, 18.6, dur=0.2, needle=False, label="magic words")
    for i, (dx, dy) in enumerate(((-9, 2), (30, 27), (-6, 22), (mg.shape[1] - 8, 26), (40, -5), (80, 30))):
        word(plus_spark("gold" if i % 2 else "red"), mx + dx, top + 6 + dy, 16.7 + 0.06 * i, 18.6, dur=0.08, needle=False)
    ck2 = np.kron(check_mark("red"), np.ones((2, 2), np.uint8))
    word(ck2, mx + mg.shape[1] + 5, top + 9, 17.62, 18.65, dur=0.2, label="they work")


def stage_steps(words, t_off, y_base=None):
    """The climbing staircase of STEP BY STEP on the stage. words = [(word, t)]. Long runs climb in two flights."""
    ox, oy = PO(1, 1)
    flights = [words] if len(words) <= 8 else [words[:6], words[6:]]
    for fi_, fl in enumerate(flights):
        n = len(fl)
        widths = [big(w, "red", 10, ANTON).shape[1] for w, _ in fl]
        total = sum(widths) + 2 * (n - 1)
        x = ox + max(3, (150 - total) // 2)
        if len(flights) == 1:
            rise = min(4, (43 - 10) // max(n - 1, 1))
            y = oy + 3 + (n - 1) * rise
        else:
            rise = 2
            y = oy + (28 if fi_ == 0 else 10) + 0
        for i, (wd, t) in enumerate(fl):
            gph = big(wd, "red" if wd == "STEP" else "black", 10, ANTON)
            put(gph, x, y, t=t, dur=0.12, off=t_off, offdur=0.2, needle=True)
            fit("staircase %s @%.1f" % (wd, t), x, y, gph, (ox + 1, oy + 1, ox + 149, oy + 46), 1)
            tr = canvas(gph.shape[1] + 2, 1, C["black"])
            put(tr, x - 1, y + gph.shape[0] + 1, t=t + 0.06, dur=0.08, off=t_off, offdur=0.2)
            x += gph.shape[1] + 2
            y -= rise


def build_stage():
    ox, oy = PO(1, 1)
    B2["center"] = (ox + 75, oy + 40)
    stage_chorus(63.36, 1)
    stage_chorus(141.28, 2)
    stage_chorus(213.52, 3)
    stage_steps([("STEP", 82.16), ("BY", 82.40), ("STEP", 82.56), ("BY", 82.88), ("STEP", 83.04),
                 ("STEP", 84.40), ("BY", 84.64), ("STEP", 84.88)], 88.2)
    stage_steps([("STEP", 159.44), ("BY", 159.68), ("STEP", 160.40), ("BY", 160.64), ("STEP", 160.88)], 162.6)
    stage_steps([("STEP", 232.24), ("BY", 232.48), ("STEP", 232.64), ("BY", 232.88), ("STEP", 233.04), ("BY", 233.28),
                 ("STEP", 234.40), ("BY", 234.72), ("STEP", 234.88), ("BY", 236.48), ("STEP", 237.12)], 240.4)
    # the last words
    pl = big("Please.", "red", 24)
    th = big("Thank you.", "red", 24)
    # the film stays clean (her rule, relayed Nov 20 11:16): no subscribe button in it; the ask is the end card appended after
    rowx = ox + 75 - pl.shape[1] // 2
    put(pl, rowx, oy + 2, t=241.28, dur=0.6, needle=True)
    put(th, ox + 75 - th.shape[1] // 2, oy + 21, t=243.36, dur=0.9, needle=True)
    fit("Please.", rowx, oy + 2, pl, (ox, oy, ox + 150, oy + 46), 1)
    fit("Thank you.", ox + 75 - th.shape[1] // 2, oy + 21, th, (ox, oy, ox + 150, oy + 46), 1)
    # ground band under the dancers; unpicked at the end for the maker's line
    put(canvas(146, 1, C["black"]), ox + 2, oy + 72, t=62.0, dur=0.6)
    # STITCH_COVER_CREDIT=1 (covers only, never the master): the zigzag is already unpicked and the maker's line already
    # stitched from the start, so a chorus frame can carry the credit as real stitches (oneshot_blind/covers/make_covers.py)
    cover = os.environ.get("STITCH_COVER_CREDIT") == "1"
    if cover:
        put(art.zigzag(140, "black", 3), ox + 5, oy + 74, t=62.2, dur=0.6, off=0.0, offdur=0)
    else:
        put(art.zigzag(140, "black", 3), ox + 5, oy + 74, t=62.2, dur=0.6, off=245.6, offdur=0.4)
    cr = txt("Made with Claude Fable 5.2", "black", "35")       # small sampler capitals: two clear rows above and below
    crx = ox + 75 - cr.shape[1] // 2
    if cover:
        crx += int(os.environ.get("STITCH_COVER_CREDIT_DX", "0"))     # cover only: clear of YouTube's timestamp corner
        put(cr, crx, oy + 75, t=0.0, dur=0)
    else:
        put(cr, crx, oy + 75, t=246.2, dur=1.6, needle=True, rgb=E.PALETTE[3][1])
    fit("credit", crx, oy + 75, cr, (ox, oy + 73, ox + 150, oy + 82), 2)
    B2["credit_end"] = (crx + cr.shape[1] + 3, oy + 77)

    # the dancers
    kinds = "mwmwmw"
    x0 = ox + 23
    joins = beats_from(60.6, 8)
    sway = [0, 1, 2, 1, 0, -1, -2, -1]

    def line(t):
        if t < joins[0]:
            return ()
        k = bi(t)
        pose = k % 4
        hop = -1 if pose % 2 else 0
        sx = sway[(k // 1) % 8] if t > 63.3 else 0
        out = []
        kk, xb = (kinds, x0) if t < 213.4 else ("mwmw", ox + 44)     # the last chorus makes room for Mama
        for i, kd in enumerate(kk):
            if t >= joins[i]:
                out.append((F.dancer(kd, pose), xb + sx + 14 * i, oy + 47 + hop))
        if t >= joins[6]:
            out.append((F.dancer_lead(pose), xb + sx + 14 * len(kk), oy + 47 - 3 + hop))
        if t >= 213.4:
            mm = F.mama("glass") if k % 2 else F.mama("stand")
            out.append((mm, ox + 21, oy + 43 + hop))
        # the family joins from the second chorus on
        if t >= 140.4:
            up = (k % 2 == 1)
            un = F.uncle("yell" if up else "stand")
            if not up:
                c2 = canvas(21, 31); paste(c2, un, 2, 3); un = c2
            out.append((un, ox + 1, oy + 41 + hop))
            hm = F.him_shrug() if up else F.him("suit")
            out.append((hm, ox + 131, oy + 41 + hop))
        return out
    W.dynamic(line)


# back of the cloth: the mess nobody understands
_TANGLE = {}


def tangle(seed=42):
    if seed not in _TANGLE:
        ox, oy = PO(1, 1)
        rng = np.random.default_rng(seed)
        segs = []
        cols = [E.PALETTE[C[c]][1] for c in ("red", "black", "red", "gold", "white", "red", "black", "dred")]
        wide = (seed == 99)
        if wide:
            ox, oy = 8, 92
        ww, hh = (312, 172) if wide else (150, 80)
        for i in range(150 if wide else 46):
            a = np.array([rng.uniform(ox - 10, ox + ww + 10), rng.uniform(oy - 4, oy + hh + 4)])
            ang = rng.uniform(0, 2 * np.pi)
            L = rng.uniform(15, 80)
            b = a + L * np.array([math.cos(ang), math.sin(ang) * 0.6])
            m = (a + b) / 2 + rng.normal(0, 7, 2)
            segs.append((a, m, b, cols[i % len(cols)]))
        knots = [(np.array([rng.uniform(ox, ox + ww), rng.uniform(oy, oy + hh)]), cols[i % len(cols)]) for i in range(48 if wide else 16)]
        _TANGLE[seed] = (segs, knots)
    return _TANGLE[seed]


def draw_tangle(frame, M, zoom, seed=42):
    segs, knots = tangle(seed)
    lines = []
    for a, m, b, col in segs:
        pts = E._bez(a, m, b, 24)
        ph = np.c_[pts, np.ones(len(pts))] @ M.T
        lines.append((ph[:, :2] / ph[:, 2:3], col))
    kn = []
    for p, col in knots:
        q = M @ np.array([p[0], p[1], 1.0])
        c = np.array([q[0] / q[2], q[1] / q[2]])
        tail = E._bez(c, c + [zoom * 2, zoom * 1.5], c + [zoom * 1.2, zoom * 4.5], 16)
        lines.append((tail, col))
        kn.append((c, col))
    # one soft shadow pass for every loose thread
    sh = np.zeros(frame.shape[:2], np.uint8)
    th = max(2, int(round(zoom * 1.1 * 0.17)))
    off = np.array([zoom * 0.28, zoom * 0.38])
    for scr, col in lines:
        cv2.polylines(sh, [np.round((scr + off) * 16).astype(np.int32)], False, 255, th, cv2.LINE_AA, 4)
    sh = cv2.GaussianBlur(sh, (0, 0), max(1.5, zoom * 0.13))
    frame[:] = (frame.astype(np.float32) * (1 - 0.45 * sh.astype(np.float32) / 255)[..., None]).astype(np.uint8)
    for scr, col in lines:
        E.draw_thread(frame, scr, zoom * 1.1, col)
    for c, col in kn:
        ci = (int(c[0]), int(c[1]))
        r = max(2, int(zoom * 0.42))
        cv2.circle(frame, (ci[0] + r // 3, ci[1] + r // 2), r, (60, 50, 40), -1, cv2.LINE_AA)
        cv2.circle(frame, ci, r, tuple(int(v * 0.8) for v in col), -1, cv2.LINE_AA)
        cv2.circle(frame, (ci[0] - r // 3, ci[1] - r // 3), max(1, r // 3), tuple(int(min(255, v * 1.2 + 30)) for v in col), -1, cv2.LINE_AA)


# =============================================================================== B1 the wedding
B1 = {}


def build_wedding():
    ox, oy = PO(0, 1)
    b = beats_from(88.2, 12)
    put(F.bunting(140), ox + 5, oy + 3, t=b[0], dur=0.8)
    for i, lx in enumerate((6, 43)):
        put(F.lantern(), ox + lx, oy + 9, t=b[1] + 0.2 * i, dur=0.2, order="radial")
    # the band
    put(canvas(146, 1, C["red"]), ox + 2, oy + 76, t=b[1], dur=0.6)
    put(art.zigzag(72, "red", 3), ox + 2, oy + 77, t=b[1] + 0.2, dur=0.5)
    names = ["clarinet", "drum", "accordion"]
    bx = [ox + 3, ox + 26, ox + 49]
    B1["band"] = [(x + 11, oy + 62) for x in bx]

    def band(t):
        out = []
        k = bi(t)
        for i, nm in enumerate(names):
            if t >= b[2 + i]:
                out.append((F.musician(nm, k), bx[i], oy + 50))
        # notes float up from the clarinet on the beat
        if t >= b[5] and not (144.4 <= t < 148.9):
            ph = k % 4
            note = A("""
                .KK
                .K.
                .K.
                KK.
                KK.
            """)
            out.append((note, ox + 50 + (ph % 2) * 2, oy + 43 - ph * 3))
            out.append((note, ox + 70 - (ph % 2) * 2, oy + 41 - ((ph + 2) % 4) * 3))
        return out
    W.dynamic(band)
    # the couple, on their own little ground line above the band (figures in registers, like an old sampler)
    bride = F.dancer("w", 0)
    top_ = bride[:8].copy()
    body = bride[8:].copy()
    top_[top_ == C["red"]] = C["white"]                      # veil
    body[(body == C["black"]) | (body == C["red"])] = C["white"]
    body[12:15][body[12:15] == C["white"]] = C["white"]
    bride = np.vstack([top_, body])
    bride[20:23, 1:14][bride[20:23, 1:14] == C["gold"]] = C["gold"]
    groom = F.dancer("m", 0)
    gl = groom[15:].copy()
    gl[gl == C["white"]] = C["black"]
    groom = np.vstack([groom[:15], gl])
    cpx, cpy = ox + 13, oy + 13
    put(canvas(40, 1, C["red"]), cpx - 5, cpy + 25, t=b[4], dur=0.4)

    def couple(t):
        if t < b[5]:
            return ()
        k = bi(t)
        hop = -(k % 2) if (t < 103.0 or alive(t)) else 0
        return [(groom, cpx, cpy + hop), (bride, cpx + 14, cpy + hop)]
    W.dynamic(couple)
    put(art.carnation(), ox + 68, oy + 13, t=b[6], dur=0.3, order="up", off=106.5, offdur=0)   # under Mama's ribbon from 106.3
    put(art.carnation(), ox + 68, oy + 13, t=114.45, dur=0)                                 # back under her next one
    # the table, Mama and him behind it
    mx, my = ox + 85, oy + 41
    hx, hy = ox + 115, oy + 39
    B1["mama"] = (mx + 9, my + 8)
    B1["him"] = (hx + 8, hy + 8)
    B1["talk"] = (ox + 103, oy + 38)

    def M_(pose, mouth=0):
        c = canvas(21, 29); paste(c, F.mama(pose), 0, 0)
        if mouth:
            c[8:10, 7:10] = C["dred"]
        return c

    def H_(kind, mouth=0):
        c = canvas(17, 31)
        paste(c, F.him_shrug() if kind == "shrug" else F.him_talk(0), 0, 0)
        if mouth or kind == "talk":
            c[9:11, 7:10] = C["dred"]
        return c

    def talk_seq(bases, words, maker):
        """bases = [(t, pose)]; mouth opens on every sung word for a fifth of a second."""
        ev = [(t, p, 0) for t, p in bases]
        pose_at = lambda tt: [p for t, p in bases if t <= tt][-1]
        for tw in words:
            ev.append((tw, pose_at(tw), 1))
            ev.append((tw + 0.2, pose_at(tw + 0.2), 0))
        ev.sort(key=lambda e: (e[0], -e[2]))
        out, last = [], None
        for t, p, m in ev:
            if out and abs(t - out[-1][0]) < 1e-6:
                out[-1] = (t, maker(p, m))
            else:
                out.append((t, maker(p, m)))
        return out
    swap(mx, my, talk_seq([(b[5], "stand"), (106.56, "ask"), (110.3, "stand"), (114.56, "point"), (117.2, "stand")],
                          [106.56, 107.36, 107.60, 107.92, 108.48, 108.80, 109.28, 114.56, 114.80, 115.68, 116.16, 116.48], M_), bloom=(0.6, "up"))
    swap(hx, hy, talk_seq([(b[6], "stand"), (110.96, "shrug"), (113.4, "stand")], [110.96, 111.28, 111.60, 112.16, 112.48], H_), bloom=(0.6, "up"))
    tbl = F.wedding_table(70)

    def table_dance(t):
        if not (alive(t) or 144.4 <= t < 148.8):
            return ()
        k = bi(t)
        return [(M_("glass" if k % 2 else "stand"), mx, my - (k % 2)), (H_("shrug" if k % 2 == 0 else "stand"), hx, hy - ((k + 1) % 2)),
                (tbl, ox + 77, oy + 54)]
    W.dynamic(table_dance)
    put(tbl, ox + 77, oy + 54, t=b[4], dur=0.8, order="cols")
    # speech ribbons (text lives in the cloth, like an old tapestry)
    # one ribbon per speaker: Mama's sits over her (red edge, like her dress), his over him (black edge, like his suit),
    # each with a long tail that comes down to the speaker's own head
    RB = {"mama": (ox + 52, oy + 11, ox + 144, oy + 32, "red", mx + 5), "him": (ox + 71, oy + 11, ox + 149, oy + 32, "black", hx + 4)}

    def say(lines, t0, t1, who, word_times):
        rb = RB[who][:4]
        edge, tail_x = RB[who][4], RB[who][5]
        r = ribbon(rb[2] - rb[0], 21, edge=edge)
        put(r, rb[0], rb[1], t=t0 - 0.25, dur=0.25, off=t1, offdur=0.15)
        tl = art.recolor(A("""
            RWWWWWWWR
            .RWWWWWR.
            ..RWWWR..
            ...RWR...
            ....R....
        """), {"red": edge})
        put(tl, tail_x, rb[3] - 1, t=t0 - 0.1, dur=0.1, off=t1, offdur=0.1)
        k = 0
        for li, ln in enumerate(lines):
            x = rb[0] + 5
            for wd in ln.split(" "):
                gph = txt(wd)
                put(gph, x, rb[1] + 3 + li * 9, t=word_times[k], dur=0.15, off=t1, offdur=0.15, needle=True, rgb=E.PALETTE[3][1])
                x += gph.shape[1] + 4
                k += 1
            FITS.append(dict(label="ribbon: " + ln, text=(rb[0] + 5, rb[1] + 3 + li * 9, x - 4, rb[1] + 10 + li * 9), box=rb, pad=2,
                             ok=bool(x - 4 <= rb[2] - 2)))
    say(["Son, what is it", "that you do?"], 106.56, 110.1, "mama", [106.56, 107.36, 107.60, 107.92, 108.48, 108.80, 109.28])
    say(["I talk to the", "computer."], 110.96, 113.7, "him", [110.96, 111.28, 111.60, 112.16, 112.48])
    say(["Your uncle does", "that too."], 114.56, 117.4, "mama", [114.56, 114.80, 115.68, 116.16, 116.48])
    # second chorus: Mama tells the table (sung: "He said please, and it worked today")
    say(["He said please,", "and it worked!"], 144.80, 148.7, "mama", [144.80, 144.96, 145.36, 146.00, 146.24, 146.48])
    hrt2 = np.kron(art.heart(), np.ones((2, 2), np.uint8))
    put(hrt2, ox + 62, oy + 34, t=146.96, dur=0.25, order="radial", off=148.7, offdur=0.15)


# =============================================================================== C1 the kitchen
C1 = {}


def kitchen_table():
    out = canvas(46, 30)
    out[18:20, 0:46] = C["lbrown"]
    out[20:30, 2:4] = C["brown"]; out[20:30, 42:44] = C["brown"]
    out[18, 4:42] = C["red"]
    out[0:15, 9:35] = C["dgrey"]
    out[1:14, 10:34] = C["cream"]
    # the chat on his screen: his message in a bubble on the right, the star and its answer on the left, the input box below
    out[2:5, 21:33] = C["bubble"]
    out[3, 22:32] = C["dgrey"]
    out[6:9, 11:14] = C["terra"]; out[7, 12] = C["black"]
    out[6, 16:28] = C["grey"]; out[8, 16:24] = C["grey"]
    out[10:13, 11:33] = C["white"]
    out[11, 12:22] = C["silver"]
    out[11, 30:32] = C["terra"]
    out[15:17, 7:37] = C["silver"]
    out[17, 7:37] = C["grey"]
    return out


def build_kitchen():
    ox, oy = PO(0, 2)
    T = 116.6
    put(canvas(144, 1, C["brown"]), ox + 3, oy + 75, t=T, dur=0.6)
    put(F.shelf(), ox + 8, oy + 10, t=T + 0.1, dur=0.5)
    # window
    win = art.frame_rect(22, 18, "brown", 1)
    win[1:-1, 1:-1] = C["sky"]
    win[:, 10:12] = C["brown"]
    win[1:5, 1:10] = C["white"]; win[1:5, 12:21] = C["white"]
    for x in range(1, 21, 2):
        if win[5, x] != C["brown"]:
            win[5, x] = C["red"]
    put(win, ox + 104, oy + 3, t=T + 0.2, dur=0.5)
    # hanging lamp
    lamp = canvas(11, 12)
    lamp[0:6, 5] = C["dgrey"]
    lamp[6:9, 2:9] = C["gold"]; lamp[9, 1:10] = C["gold"]; lamp[10, 4:7] = C["yellow"]
    put(lamp, ox + 64, oy + 1, t=T + 0.3, dur=0.3, order="down")
    put(F.fridge(), ox + 130, oy + 35, t=T + 0.35, dur=0.7, order="up")
    sx, sy = ox + 6, oy + 45

    def steam(t):
        if t < T + 0.6:
            return ()
        return [(F.stove(bi(t)), sx, sy)]
    W.dynamic(steam)
    tx, ty = ox + 47, oy + 45
    put(kitchen_table(), tx, ty, t=T + 0.2, dur=0.6, order="up")
    C1["screen"] = (tx + 22.5, ty + 1.0)                          # (+4.5, +2.5 in the camera key = the middle of his bubble on the screen)
    ux, uy = ox + 98, oy + 44
    C1["uncle"] = (ux + 10, uy + 12)

    def U(pose):
        if pose == "stand":
            c = canvas(21, 31); paste(c, F.uncle("stand"), 2, 3); return c
        return F.uncle(pose)
    seq = [(T + 0.3, U("stand"))]
    for i, bt in enumerate(beats_from(118.3, 15)):
        if bt > 124.5:
            break
        seq.append((bt, U("yell" if i % 2 == 0 else "yell2")))
    seq.append((124.6, U("stand")))
    swap(ux, uy, seq, bloom=(0.5, "up"))

    # yell marks between him and the laptop, flashing on the beat
    def marks(t):
        if not (118.3 <= t < 124.5):
            return ()
        k = bi(t) % 2
        m = A("""
            R....
            .R...
            R....
        """) if k == 0 else A("""
            ..R..
            .R...
            ..R..
        """)
        return [(m, ux - 5, uy + 8), (m[::-1], ux - 6, uy + 14)]
    W.dynamic(marks)
    y1 = txt("IT'S BROKE!", "red"); y2 = txt("IT'S SLOW!", "red")
    put(y1, ox + 60, oy + 25, t=121.44, dur=0.3, off=124.6, needle=True)
    put(y2, ox + 64, oy + 34, t=123.28, dur=0.3, off=124.6, needle=True)
    fit("yell 1", ox + 60, oy + 25, y1, (ox + 46, oy + 22, ox + 128, oy + 44), 2)
    fit("yell 2", ox + 64, oy + 34, y2, (ox + 46, oy + 22, ox + 128, oy + 44), 2)
    # he arrives: give it context
    hx, hy = ox + 28, oy + 44
    c = canvas(17, 31); paste(c, F.him("suit"), 0, 0)
    c2 = canvas(17, 31); paste(c2, F.him_shrug(), 0, 0)
    swap(hx, hy, [(124.7, c), (126.56, c2), (128.0, c)], bloom=(0.3, "up"))
    def kitchen_dance(t):
        if not alive(t):
            return ()
        k = bi(t)
        return [(U("yell" if k % 2 else "stand"), ux, uy - (k % 2)), (c2 if k % 2 == 0 else c, hx, hy - ((k + 1) % 2))]
    W.dynamic(kitchen_dance)
    r = ribbon(92, 12)
    g_ = txt("Give it context.")
    tl_ = A("""
        RWWWR
        .RWR.
        ..R..
    """)
    put(r, ox + 8, oy + 29, t=126.3, dur=0.25, off=131.6, offdur=0)
    put(g_, ox + 12, oy + 32, t=126.56, dur=0.7, needle=True, rgb=E.PALETTE[3][1], off=131.6, offdur=0)
    put(tl_, hx + 6, oy + 40, t=126.4, dur=0.1, off=131.6, offdur=0)
    for sp_, x_, y_ in ((r, ox + 8, oy + 29), (g_, ox + 12, oy + 32), (tl_, hx + 6, oy + 40)):
        put(sp_, x_, y_, t=169.3, dur=0)                        # stitched back in for the whole-cloth views
    fit("ribbon: Give it context.", ox + 12, oy + 32, g_, (ox + 8, oy + 29, ox + 100, oy + 41), 2)
    C1["duo"] = ((hx + ux + 21) / 2, oy + 52)


# =============================================================================== C3 Mama's sampler
C3 = {}


def build_sampler():
    ox, oy = PO(2, 2)
    hdr = (ox + 3, oy + 0, ox + 147, oy + 19)
    # two quiet lines fill the empty panel, word by word, then both are unpicked for the one that stays
    mid = (ox + 2, oy + 20, ox + 148, oy + 70)
    L1, L2 = "Maybe it's not magic.", "It's just being clear."
    m1 = big(L1, "black", 16); m2 = big(L2, "black", 16)
    m1x, m1y = ox + 75 - m1.shape[1] // 2, oy + 26
    m2x, m2y = ox + 75 - m2.shape[1] // 2, oy + 48
    put_big_words(L1, "black", 16, m1x, m1y, [178.08, 178.72, 179.20, 179.68], off=184.2, rgb=E.PALETTE[3][1])
    put_big_words(L2, "black", 16, m2x, m2y, [181.44, 182.40, 182.72, 183.28], off=184.3, rgb=E.PALETTE[3][1])
    fit("bridge: " + L1, m1x, m1y, m1, mid, 1)
    fit("bridge: " + L2, m2x, m2y, m2, mid, 1)
    rng = np.random.default_rng(21)
    k_ = 0
    placed = []
    for i in range(400):
        dx, dy = int(rng.integers(5, 138)), int(rng.integers(3, 68))
        if m1x - ox - 9 < dx < m1x - ox + m1.shape[1] + 2 and m1y - oy - 9 < dy < m1y - oy + m1.shape[0] + 2:
            continue
        if any(abs(dx - px) < 9 and abs(dy - py) < 9 for px, py in placed):
            continue
        placed.append((dx, dy))
        sp_ = art.star8(3, "gold", "red") if k_ % 3 == 0 else (art.star8(2, "gold") if k_ % 3 == 1 else plus_spark())
        put(sp_, ox + dx, oy + dy, t=174.6 + 0.05 * k_, dur=0.12, order="radial", off=179.2 + 0.05 * k_, offdur=0.1)
        k_ += 1
        if k_ >= 34:
            break
    a = txt("Say what you mean,", "black")
    k = txt("kindly.", "red")
    tot = a.shape[1] + 5 + k.shape[1]
    hx = ox + 75 - tot // 2
    put(a, hx, oy + 6, t=184.8, dur=1.6, needle=True, rgb=E.PALETTE[3][1])
    put(k, hx + a.shape[1] + 5, oy + 6, t=187.2, dur=0.6, needle=True)
    FITS.append(dict(label="header: Say what you mean, kindly.", text=(hx, oy + 6, hx + tot, oy + 13), box=hdr, pad=1,
                     ok=bool(hx - hdr[0] >= 1 and hdr[2] - (hx + tot) >= 1)))
    put(art.zigzag(140, "red", 3), ox + 5, oy + 19, t=187.8, dur=0.8)
    C3["header"] = (ox + 75, oy + 10)
    C3["l3"] = (hx, tot)
    C3["oy"] = oy
    # Mama and the boy
    mx, my = ox + 106, oy + 38
    C3["mama"] = (mx + 14, my + 12)
    c0 = canvas(21, 29); paste(c0, F.mama("stand"), 0, 0)
    seq = [(185.5, c0)]
    for i, t in enumerate((195.28, 196.64, 199.2, 200.72)):
        seq.append((t, F.mama("point")))
        seq.append((t + 0.7, c0))
    swap(mx, my, seq, bloom=(2.3, "up"))
    put(F.kid(), mx + 23, my + 10, t=188.9, dur=1.0, order="up", off=213.4, offdur=0)
    kd = F.kid()
    put(canvas(40, 1, C["red"]), mx - 2, my + 29, t=185.1, dur=0.6)

    def sampler_dance(t):
        if t < 213.4:
            return ()
        k = bi(t)
        return [(F.mama("point") if (k // 2) % 2 else c0, mx, my), (kd, mx + 23, my + 10 - (k % 2))]
    W.dynamic(sampler_dance)
    # the four instructions
    rows = [(F.icon_bus(), "Take the bus.", 195.28, [195.28, 195.60, 195.84]),
            (F.icon_clock(), "Be home by ten.", 196.64, [196.64, 197.04, 197.52, 197.76]),
            (F.icon_jacket(), "Wear a jacket.", 199.20, [199.20, 199.60, 199.76]),
            (F.icon_phone(), "Call me after.", 200.72, [200.72, 201.20, 201.44])]
    area = (ox + 2, oy + 21, ox + 105, oy + 69)
    for i, (ic, line, t0, wts) in enumerate(rows):
        ry = oy + 23 + i * 12
        put(ic, ox + 4 + (19 - ic.shape[1]) // 2, ry + (11 - ic.shape[0]) // 2, t=t0 - 0.45, dur=0.4, order="radial")
        x = ox + 26
        for wd, tw in zip(line.split(" "), wts):
            gph = txt(wd)
            put(gph, x, ry + 2, t=tw, dur=0.16, needle=True, rgb=E.PALETTE[3][1])
            x += gph.shape[1] + 4
        FITS.append(dict(label="sampler: " + line, text=(ox + 26, ry + 2, x - 4, ry + 9), box=area, pad=1, ok=bool(x - 4 <= area[2] - 1)))
    C3["list"] = (ox + 62, oy + 44)
    # "then she says it all again": the same four, again and again along the bottom
    icons = [F.icon_bus(), F.icon_clock(), F.icon_jacket(), F.icon_phone()]
    ts = [202.40, 202.88, 203.28, 203.76, 204.20, 204.48, 204.72, 204.96]
    x = ox + 5
    for i in range(8):
        ic = icons[i % 4]
        put(ic, x, oy + 69 + (11 - ic.shape[0]) // 2, t=ts[i], dur=0.14, order="radial")
        x += ic.shape[1] + (5 if i % 4 != 3 else 9)
    C3["strip"] = (ox + 75, oy + 74)


# =============================================================================== C2 the toast
C2 = {}


def build_toast():
    ox, oy = PO(1, 2)
    T = 203.6
    gy = oy + 75
    put(canvas(146, 1, C["red"]), ox + 2, gy, t=T, dur=0.6)
    put(art.zigzag(140, "red", 3), ox + 5, gy + 1, t=T + 0.2, dur=0.6)
    mx = ox + 65
    C2["mama"] = (mx + 9, gy - 20)
    # gold rays behind Mama, a ring per beat after "to Mama"
    rays = canvas(71, 52)
    cxr, cyr = 35, 36
    for kk in range(16):
        ang = math.pi + kk * math.pi / 15
        for rr in range(16, 25):
            if (rr // 3) % 2 == 0:
                xx = int(round(cxr + rr * math.cos(ang) * 1.05)); yy = int(round(cyr + rr * math.sin(ang) * 0.9))
                if 0 <= xx < 71 and 0 <= yy < 52:
                    rays[yy, xx] = C["gold"]
    put(rays, mx + 9 - cxr, gy - 29 - cyr + 10, t=0, order="radial", dur=1, cx=cxr, cy=cyr)
    bts = beats_from(208.3, 5)
    W.elems[-1][3] = art.order_beats(rays, bts, 0.15, cx=cxr, cy=cyr)
    W.elems[-1][5] = bts[0]

    def M_(pose):
        c = canvas(21, 29); paste(c, F.mama(pose), 0, 0); return c
    swap(mx, gy - 29, [(T + 0.2, M_("stand")), (206.48, M_("glass"))], bloom=(0.7, "up"))

    def U(pose):
        if pose == "stand":
            c = canvas(21, 31); paste(c, F.uncle("stand"), 2, 3); return c
        return F.uncle(pose)
    swap(ox + 36, gy - 31, [(T + 0.3, U("stand")), (206.56, U("glass"))], bloom=(0.7, "up"))
    # him, raising a glass
    hs = canvas(21, 31); paste(hs, F.him("suit"), 0, 0)
    hg = canvas(21, 31); paste(hg, F.him("suit"), 0, 0)
    hg[16:22, 13:15] = 0
    paste(hg, F.GLASS_ARM("K"), 12, 7)
    swap(ox + 94, gy - 31, [(T + 0.4, hs), (206.64, hg)], bloom=(0.7, "up"))
    for i, (dx, kd) in enumerate(((4, "w"), (19, "m"), (117, "w"), (132, "m"))):
        d0 = canvas(17, 28); paste(d0, F.dancer(kd, 0), 0, 3)
        swap(ox + dx, gy - 28, [(T + 0.1 * i, d0), (206.48 + 0.08 * i, F.glass_raised(kd, 0))], bloom=(0.6, "up"))

    def bob(t):
        if t < 213.4:
            return ()
        k = bi(t)
        return [(F.glass_raised(kd, k), ox + dx, gy - 28) for dx, kd in ((4, "w"), (19, "m"), (117, "w"), (132, "m"))]
    W.dynamic(bob)
    tm = big("To Mama", "red", 24)
    tmx = ox + 75 - tm.shape[1] // 2
    put(tm, tmx, oy + 3, t=208.32, dur=0.8, needle=True)
    fit("To Mama", tmx, oy + 3, tm, (ox, oy, ox + 150, oy + 24), 1)
    sub = txt("the first prompt engineer")
    sbx = ox + 75 - sub.shape[1] // 2
    x = sbx
    for wd, tw in zip("the first prompt engineer".split(" "), (210.32, 210.48, 210.88, 211.52)):
        gph = txt(wd)
        put(gph, x, oy + 24, t=tw, dur=0.2, needle=True, rgb=E.PALETTE[3][1])
        x += gph.shape[1] + 4
    fit("the first prompt engineer", sbx, oy + 24, sub, (ox, oy + 21, ox + 150, oy + 34), 1)
    put(art.heart(), tmx - 14, oy + 8, t=209.2, dur=0.3, order="radial")
    put(art.heart(), tmx + tm.shape[1] + 7, oy + 8, t=209.4, dur=0.3, order="radial")
    swap(ox + 118, oy + 30, [(211.7, F.star("happy"))], bloom=(0.4, "radial"))
    C2["banner"] = (ox + 75, oy + 16)


# =============================================================================== build
build_frame()
build_intro()
build_title()
build_bedroom()
build_chat()
build_stage()
build_wedding()
build_kitchen()
build_sampler()
build_toast()


def build_glitter():
    col, _ = W.compose(251.0, 0, 0, 480, 270)
    occ = (col > 0).astype(np.uint8)
    occ2, _ = W.compose(238.0, 0, 0, 480, 270)
    occ |= (occ2 > 0).astype(np.uint8)
    ox, oy = PO(1, 1)
    occ[oy - 2:oy + 48, ox - 2:ox + 152] = 1
    occ[:9] = 1; occ[-9:] = 1; occ[:, :9] = 1; occ[:, -9:] = 1
    occ = cv2.dilate(occ, np.ones((9, 9), np.uint8))
    rng = np.random.default_rng(9)
    pts = []
    for gy in range(12, 258, 9):
        for gx in range(12, 468, 11):
            x = gx + int(rng.integers(-3, 4)); y = gy + int(rng.integers(-2, 3))
            if 0 < x < 478 and 0 < y < 268 and not occ[y, x]:
                d = math.hypot((x - 240) / 240, (y - 135) / 135)
                pts.append((x, y, 232.3 + 5.4 * min(d, 1.2) / 1.2, int(rng.integers(0, 3)), "gold" if rng.random() < 0.7 else "red"))
    sp = {"gold": plus_spark("gold"), "red": plus_spark("red")}
    dot = {"gold": canvas(1, 1, C["gold"]), "red": canvas(1, 1, C["red"])}

    def glitter(t):
        if t < 232.3:
            return ()
        k = bi(t)
        out = []
        for x, y, t0, ph, cl in pts:
            if t >= t0:
                out.append((sp[cl], x - 1, y - 1) if (k + ph) % 3 else (dot[cl], x, y))
        return out
    W.dynamic(glitter)
    return len(pts)


NGLITTER = build_glitter()
NEEDLE.sort(key=lambda e: e[0])


# =============================================================================== camera
def camera_keys():
    K = []

    def k(t, x, y, z, **kw):
        d = dict(x=float(x), y=float(y), zoom=float(z))
        d.update(kw)
        K.append((t, d))

    pA1, pA2, pA3 = (84, 49), (240, 49), (396, 49)
    pB1, pB2, pB3 = (84, 135), (240, 135), (396, 135)
    pC1, pC2, pC3 = (84, 221), (240, 221), (396, 221)
    st = A1["stem"]
    sxm = st[1][0] + 0.5
    sym = (st[0][1] + st[-1][1]) / 2 + 0.5
    # ---- intro
    k(0.0, sxm + 2.5, sym, 86)
    k(1.95, sxm + 3.5, sym, 74, p=1.2)
    k(3.5, A1["please"][0], A1["please"][1] + 1, 13.4, p=2.4)
    k(6.3, A1["please"][0], A1["please"][1] + 4, 14.4, p=1.5)
    k(7.1, 78, 52.5, 13.6, p=2.2)                             # the whole first sampler: the stairs, and him at the foot of them
    for i_, tw_ in enumerate((7.60, 8.16, 8.48)):               # the camera takes the three steps down with the words
        k(tw_ - 0.02, 78 + 1.5 * i_, 52.5 + 0.85 * i_, 13.6)
        k(tw_ + 0.14, 79.5 + 1.5 * i_, 53.35 + 0.85 * i_, 13.6, p=2.6)
    k(11.25, 82.5, 55.0, 13.9, p=1.2)
    # ---- title: whip onto a line that is already dancing; the letters land on it beat by beat
    k(12.3, pA2[0], pA2[1], 12.2, p=2.6)
    k(19.3, pA2[0], pA2[1], 12.7, p=1.15)
    k(19.95, 165 + 34, 9 + 71.6, 27, p=2.4)                    # low along the dancers
    k(22.2, 165 + 103, 9 + 71.6, 27, p=1.1)
    k(22.85, pA2[0], pA2[1], 12.2, p=2.4)
    k(24.3, pA2[0], pA2[1], 12.5, p=1.2)
    k(24.55, pA2[0] + 1, pA2[1], 12.5)
    # ---- bedroom
    k(25.6, 321 + 35, 9 + 56, 23.5, p=2.4)
    k(26.6, 321 + 35, 9 + 56, 24.5, p=1.2)
    k(27.2, pA3[0] - 30, pA3[1] - 0.5, 15.6, p=2.2)
    k(28.8, pA3[0] - 28, pA3[1] - 1.5, 16.4, p=1.3)
    k(29.5, A3["window"][0], A3["window"][1] + 4, 22, p=2.0)
    k(29.95, A3["window"][0], A3["window"][1] + 4, 22.5)
    k(30.7, pB3[0], pB3[1], 12.5, p=2.4)
    k(32.3, pB3[0], pB3[1], 12.9, p=1.3)
    k(32.85, A3["desk"][0], A3["desk"][1] - 1, 24, p=2.6)
    k(35.6, A3["desk"][0], A3["desk"][1] - 2, 26, p=1.3)
    # ---- typing
    bx, by = B3["box"]
    k(36.5, pB3[0] + 0.5, pB3[1], 12.7, p=2.6)                 # the frame is the app window, whole
    k(46.7, pB3[0] + 0.5, pB3[1], 13.0, p=1.2)
    k(47.7, pB3[0], pB3[1], 12.8, p=2.2)
    k(48.3, pB3[0], pB3[1], 12.8)
    s1 = B3["star1"]
    k(53.2, pB3[0], pB3[1], 12.95, p=1.2)
    pb = B3["pbox"]
    k(53.9, pb[0], pb[1] - 12, 14.6, p=2.4)                    # inside the window: below its title bar, above its bottom edge
    k(57.45, pb[0], pb[1] - 12, 14.9, p=1.2)
    s2 = B3["star2"]
    k(57.84, s2[0] + 10.5, s2[1] + 4.6, 37, p=2.6)             # the star takes a breath: between the title bar and his text
    k(59.2, s2[0] + 10.5, s2[1] + 4.6, 38.5, p=1.2)
    k(59.6, pb[0], pb[1] - 12, 14.7, p=2.6)
    k(61.2, pb[0], pb[1] - 12, 14.95, p=1.2)
    k(62.3, pB3[0], pB3[1], 12.8, p=2.0)
    k(62.5, pB3[0], pB3[1], 12.8)

    # ---- chorus (shared choreography)
    def chorus(T0, v, t_in, t_out):
        sx_, sy_ = pB2
        if v == 3:
            # the last chorus: one look at the stage, then back to four panels at once, the whole family dancing
            Qx, Qy = 162, 178
            k(t_in, sx_, sy_ - 2, 12.9, p=2.6)
            k(T0 + 3.6, sx_, sy_ - 2, 13.3, p=1.2)
            k(T0 + 4.5, Qx, Qy, 6.1, p=2.4)                       # please: the whole family, four panels
            k(T0 + 7.42, Qx, Qy, 6.3, p=1.1)
            k(T0 + 7.62, sx_, sy_ - 2, 12.9, p=3.0)               # IMPORTANT: punched in on the stage
            k(T0 + 9.1, sx_, sy_ - 2, 13.2)
            k(T0 + 9.55, Qx, Qy, 6.1, p=2.4)                      # three examples, then relax
            k(T0 + 10.95, Qx, Qy, 6.25, p=1.1)
            k(T0 + 11.5, pC2[0], pC2[1] - 1, 12.4, p=2.6)         # "He's a prompt engineer": so was she
            k(T0 + 13.0, pC2[0], pC2[1] - 1, 12.8, p=1.15)
            k(T0 + 13.65, Qx, Qy, 6.1, p=2.4)                     # step by step, the flip, the magic words
            k(T0 + 16.7, Qx, Qy, 6.4, p=1.05)
            k(T0 + 18.6, Qx, Qy, 6.1, p=1.6)
            return
        if v == 2:
            k(t_in, sx_ + 43, sy_ + 21, 25, p=2.6)                # "He's..." - on him, dancing
            k(T0 + 1.0, sx_ + 42, sy_ + 21, 26, p=1.2)
            k(T0 + 1.6, sx_, sy_ - 2, 12.9, p=2.4)
        else:
            k(t_in, sx_, sy_ - 2, 12.9, p=2.6)
        k(T0 + (3.4 if v == 2 else 3.8), sx_, sy_ - 2, 13.3, p=1.2)
        if v == 2:
            tkx, tky = B1["talk"]
            k(T0 + 3.45, sx_, sy_ - 2, 13.3)
            k(T0 + 3.95, tkx - 2.5, tky + 0.8, 17.2, p=2.6)     # Mama tells the table
            k(T0 + 7.2, tkx - 2.5, tky + 0.8, 17.4, p=1.2)
        else:
            k(T0 + 4.3, sx_ + 1, sy_ - 11, 15.0, p=2.4)         # please
            k(T0 + 7.35, sx_ + 3, sy_ - 11, 15.5, p=1.2)
        k(T0 + (7.68 if v == 2 else 7.6), sx_, sy_ - 2, 12.9, p=3.0 if v != 2 else 2.6)                  # IMPORTANT
        k(T0 + 9.1, sx_, sy_ - 2, 13.2)
        if v == 2:
            # the family is in the line now (uncle far left, him far right): stay wide enough to keep them whole
            k(T0 + 9.4, sx_ - 2, sy_ - 2, 12.7, p=2.4)          # three examples
            k(T0 + 10.9, sx_ + 2, sy_ - 2, 12.9, p=1.2)
            k(T0 + 11.4, sx_ - 40.4, sy_ + 20, 24, p=2.4)         # the uncle has joined the line (the panel's edge as the frame's)
            k(T0 + 11.9, sx_ - 40.4, sy_ + 20, 24.2, p=1.2)       # ... and out before ENGINEER lands above him
            k(T0 + 12.45, sx_, sy_ - 2, 12.9, p=2.4)
            k(T0 + 13.1, sx_, sy_ - 2, 13.0)
            k(T0 + 13.7, sx_ - 1, sy_ - 2, 12.7, p=2.4)         # stairs
            k(T0 + 15.05, sx_ + 1, sy_ - 2, 12.9, p=1.2)
        else:
            k(T0 + 9.4, sx_ - 14, sy_ - 9, 15.0, p=2.4)         # three examples
            k(T0 + 10.9, sx_ + 2, sy_ - 9, 15.0, p=1.2)
            k(T0 + 11.5, sx_, sy_ - 2, 12.9, p=2.4)             # title again, whole stage
            k(T0 + 13.1, sx_, sy_ - 2, 13.3)
            k(T0 + 13.7, sx_ - 4, sy_ - 10, 14.6, p=2.4)        # stairs: every word stays in frame, "OK?" included
            k(T0 + 15.05, sx_ - 3, sy_ - 9, 14.9, p=1.2)
        k(T0 + 15.3, sx_, sy_ - 2, 13.0, p=2.0)                 # back of the cloth
        k(T0 + 16.6, sx_, sy_ - 2, 13.4, p=1.2)
        k(T0 + 17.0, sx_ + 1, sy_ - 2, 12.5, p=2.2)             # magic words
        k(T0 + 18.5, sx_ + 1, sy_ - 2, 12.8, p=1.2)
        k(T0 + 19.0, sx_, sy_ - 2, 12.9, p=2.2)
        if t_out:
            k(t_out, sx_, sy_ - 2, 13.2, p=1.2)

    chorus(63.36, 1, 63.3, 85.6)
    # dancers close: feet and faces
    k(86.4, pB2[0] - 26, pB2[1] + 19, 26, p=2.2)
    k(89.4, pB2[0] + 30, pB2[1] + 19, 26, p=1.15)
    # ---- wedding
    k(90.6, pB1[0], pB1[1], 12.8, p=2.4)
    k(92.5, pB1[0], pB1[1], 13.2, p=1.2)
    bd = B1["band"]
    k(93.3, bd[0][0] + 2, bd[0][1] - 2, 30, p=2.4)
    k(95.3, bd[0][0] + 2, bd[0][1] - 2, 31, p=1.2)
    k(95.75, bd[1][0], bd[1][1] - 2, 31, p=2.6)
    k(97.4, bd[1][0], bd[1][1] - 2, 32, p=1.2)
    k(97.85, bd[2][0], bd[2][1] - 2, 32, p=2.6)
    k(99.3, bd[2][0], bd[2][1] - 2, 32.5, p=1.2)
    k(100.6, pB1[0], pB1[1], 12.8, p=2.2)
    k(101.6, pB1[0], pB1[1], 12.8)
    tk = B1["talk"]
    k(103.5, tk[0] - 2, tk[1] + 3, 16.4, p=2.0)
    k(106.2, tk[0] - 2, tk[1] + 3, 16.8, p=1.2)
    k(106.9, tk[0] + 1, tk[1] + 1.5, 16.9, p=2.2)               # Mama asks: her ribbon whole, with headroom
    k(110.2, tk[0] + 1, tk[1] + 1.5, 17.1, p=1.2)
    k(110.9, tk[0] + 6, tk[1] + 1.5, 17.1, p=2.2)               # his answer: the frame slides over to him
    k(113.9, tk[0] + 6, tk[1] + 1.5, 17.3, p=1.2)
    k(114.5, tk[0] + 1, tk[1] + 1.5, 17.1, p=2.2)
    k(117.25, tk[0] + 1, tk[1] + 1.5, 17.3, p=1.2)
    # ---- kitchen
    un = C1["uncle"]
    k(118.1, un[0] - 12, un[1] - 5, 16.6, p=2.6)
    k(124.5, un[0] - 11, un[1] - 5, 17.4, p=1.2)
    k(125.3, pC1[0] - 9.5, pC1[1] + 2, 15.0, p=2.2)             # his ribbon whole, with margin on the left
    k(127.5, pC1[0] - 9.5, pC1[1] + 2, 15.3, p=1.2)
    sc = C1["screen"]
    k(128.38, sc[0] + 4.5, sc[1] + 2.5, 170, ei=2.4, cut=1)
    ld = B3["land"]
    k(128.4, ld[0], ld[1], 170)
    k(129.25, pB3[0], pB3[1], 12.3, eo=2.6)
    k(129.7, pB3[0], pB3[1], 12.3)
    k(131.4, pB3[0], pB3[1], 12.6, p=1.2)
    k(131.9, pb[0], pb[1] - 12, 14.6, p=2.4)                    # his own version, typed in CAPS
    k(135.3, pb[0], pb[1] - 12, 14.9, p=1.2)
    k(135.84, pB3[0], pB3[1], 12.4, p=2.4)                      # the whole window: the star breathes with him
    k(138.9, pB3[0], pB3[1], 12.7, p=1.1)
    k(140.0, pB3[0], pB3[1], 12.9, p=1.6)                       # the answer
    k(140.3, pB3[0], pB3[1], 12.9)
    chorus(141.28, 2, 141.2, 161.7)
    # ---- instrumental 2: the clarinet, then the whole cloth
    du = C1["duo"]
    k(162.7, du[0] - 3.0, du[1] + 5.0, 17.6, p=2.6)             # the kitchen: uncle and nephew dancing, both whole
    k(164.4, du[0] - 2.0, du[1] + 5.0, 18.0, p=1.15)
    k(165.1, 43.1, 95 + 63.5, 22.6, p=2.6)                      # the band, all three in one frame (under the couple's line)
    k(166.9, 42.8, 95 + 63.3, 23.0, p=1.15)
    k(167.6, 9 + 30, 95 + 28, 27, p=2.6)                        # the bride and groom
    k(168.9, 9 + 30, 95 + 27, 28.5, p=1.15)
    k(170.6, 240, 135, 4.0, p=2.0, rot=0.0)
    k(173.6, 240, 135, 4.12, p=1.1)                             # a small push only: the outer panels keep their margins
    k(176.7, pC3[0], pC3[1] - 2, 12.7, p=2.0)
    hd = C3["header"]
    (a3, w3) = C3["l3"]
    yb = C3["oy"] + 23
    k(177.6, pC3[0], pC3[1] - 2, 12.7, p=2.2)
    # ---- bridge: the empty panel, two big quiet lines, then the camera follows the needle along the one that stays
    k(184.2, pC3[0], pC3[1] - 2, 13.1, p=1.15)
    k(184.9, pC3[0], pC3[1] - 1.5, 12.6, p=2.0)               # "Say what you mean, kindly.": the whole line, a slow push
    k(188.3, pC3[0], pC3[1] - 0.5, 13.0, p=1.2)
    k(189.6, pC3[0], pC3[1], 12.8, p=2.0)
    k(191.6, pC3[0], pC3[1], 13.0)
    mm = C3["mama"]
    k(192.6, mm[0] + 2, mm[1] + 2, 24, p=2.2)
    k(194.8, mm[0] + 2, mm[1] + 2, 25.5, p=1.2)
    k(195.3, pC3[0], pC3[1] - 1, 12.2, p=2.4)                  # whole header line in frame, with margin
    k(202.2, pC3[0], pC3[1] - 1, 12.5, p=1.2)
    k(203.0, pC3[0], pC3[1] + 1.5, 12.2, p=2.0)                # the whole sampler: header, list, and the strip that repeats
    k(205.2, pC3[0], pC3[1] + 1.5, 12.4, p=1.2)
    # ---- toast
    k(206.1, pC2[0], pC2[1] + 6, 15.5, p=2.6)
    k(208.1, pC2[0], pC2[1] + 6, 16.2, p=1.2)
    cm = C2["mama"]
    k(208.75, cm[0] + 1, cm[1] + 5, 25.0, p=2.4)                # to Mama
    k(209.7, cm[0] + 1, cm[1] + 4, 26.5, p=1.2)
    k(210.4, pC2[0], pC2[1] - 1, 12.3, p=2.2)                   # she was the first prompt engineer
    k(212.5, pC2[0], pC2[1] - 1, 12.6, p=1.2)
    k(213.45, pB2[0], pB2[1] - 1, 13.2, p=2.6)
    # ---- last chorus: same dance, then the camera steps back, step by step
    chorus(213.52, 3, 213.45, None)
    zs = [(232.24, 5.75), (232.64, 5.4), (233.04, 5.1), (234.40, 4.8), (234.88, 4.5), (237.12, 4.25), (237.52, 4.05)]
    z, cx_, cy_ = 6.1, 162.0, 178.0
    k(232.2, cx_, cy_, z)
    for i, (t, zz) in enumerate(zs):
        f_ = (i + 1) / len(zs)
        nx, ny = 162 + (240 - 162) * f_, 178 + (135 - 178) * f_
        k(t + 0.02, cx_, cy_, z)
        k(t + 0.3, nx, ny, zz, p=2.6)
        z, cx_, cy_ = zz, nx, ny
    k(240.9, 240, 135, 4.15, p=1.2)
    k(243.1, 240, 136.5, 11.75, p=2.0)                         # in for the last words: the panel with its red frame
    k(251.6, 240, 136.5, 12.0, p=1.1)
    return K


TRACK = E.Track(camera_keys())
CUTS = [t for t, d in TRACK.keys if d.get("cut")]

# flips to the back of the cloth: (start, end) of the back view, per chorus
FLIPS = [(63.36 + 15.2, 63.36 + 16.62), (141.28 + 15.12, 141.28 + 16.56), (213.52 + 15.12, 213.52 + 16.56)]
FLIP_T = 0.26


def cam_at(t):
    c = TRACK.at(t)
    c.pop("cut", None)
    z = c["zoom"]
    # breathing on the beat during the dance sections
    in_dance = (13.2 < t < 24.5) or (63.3 < t < 103) or (141.2 < t < 177) or (206 < t < 251.6)
    if in_dance:
        ph = beat_phase(t)
        c["zoom"] = z * (1 + 0.012 * math.exp(-ph * 5.0))
    # IMPORTANT: a shake on the hit
    for T0 in (63.36, 141.28, 213.52):
        d = t - (T0 + 7.5)
        if 0 <= d < 0.5:
            a = (1 - d / 0.5) ** 2
            c["x"] += a * 0.8 * math.sin(d * 90) * 12.8 / z
            c["y"] += a * 0.6 * math.cos(d * 75) * 12.8 / z
    # gentle hand-held drift, smaller when close
    c["x"] += 0.35 * math.sin(t * 0.53) * 12.8 / max(z, 4)
    c["y"] += 0.25 * math.sin(t * 0.41 + 1.3) * 12.8 / max(z, 4)
    c["rot"] = c.get("rot", 0.0) + 0.004 * math.sin(t * 0.37)
    for (ca, cb) in ((15.0, 24.4), (63.4, 89.4), (141.3, 161.6), (213.6, 232.0)):
        if ca < t < cb:
            env = ease3((t - ca) / 0.8) * ease3((cb - t) / 0.8)
            c["rot"] += 0.013 * env * math.sin(2 * math.pi * (t - ca) / (BEATS[200] - BEATS[192]))
    c["tilt"] = 0.16 * float(smoothstep(15, 60, z))
    c["dof"] = 6.5 * float(smoothstep(19, 70, z))
    c["lx"] = 0.40 + 0.05 * math.sin(t * 0.11)
    c["ly"] = 0.36 + 0.04 * math.cos(t * 0.09)
    # light: bridge is the quiet, warm room; the finale is bright
    lstr = 0.42
    if 177 < t < 206:
        lstr = 0.42 + 0.14 * ease3(min(1, (t - 177) / 2.0)) * (1 - ease3(max(0, (t - 204.5) / 1.5)))
    if t > 232:
        lstr = 0.42 - 0.12 * ease3(min(1, (t - 232) / 6.0))
    c["lstr"] = lstr
    c["warm"] = _grade(t)
    # the second chorus is the wedding after dark: one pool of lamplight on the cloth
    if 140.9 < t < 162.9:
        c["spot"] = ease3((t - 140.9) / 0.9) * ease3((162.9 - t) / 0.9)
    # the card flip
    c["back"] = False
    for (a, b) in FLIPS:
        if a - FLIP_T / 2 <= t <= b + FLIP_T / 2:
            if t < a + FLIP_T / 2:
                p = (t - (a - FLIP_T / 2)) / FLIP_T
            elif t > b - FLIP_T / 2:
                p = 1 - (t - (b - FLIP_T / 2)) / FLIP_T
            else:
                p = 1.0
            fx = math.cos(math.pi * min(max(p, 0), 1))
            c["back"] = fx < 0
            if abs(fx) < 0.04:
                fx = 0.04 if fx >= 0 else -0.04
            c["flipx"] = fx
            c["tilt"] = c["tilt"] + 0.25 * math.sin(math.pi * p)
    if t < 0.5:
        c["fade"] = 0.8 + 0.2 * ease3(t / 0.5)
    return c


def ease3(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


# warmth of the light through the film: (time, warm). Morning is cool and clear, the wedding is lamplight,
# the bridge is the warmest and quietest, the last chorus opens up again.
_GRADE = [(0.0, 0.05), (24.0, 0.05), (26.0, 0.015), (62.0, 0.02), (64.0, 0.05), (88.0, 0.05), (91.0, 0.085), (117.0, 0.085),
          (119.0, 0.06), (128.3, 0.06), (128.5, 0.02), (140.0, 0.02), (141.5, 0.05), (162.0, 0.05), (165.0, 0.07), (176.0, 0.07),
          (179.0, 0.10), (205.0, 0.10), (207.0, 0.085), (213.0, 0.085), (215.0, 0.05), (252.0, 0.045)]


def _grade(t):
    for (a, wa), (b, wb) in zip(_GRADE[:-1], _GRADE[1:]):
        if a <= t < b:
            return wa + (wb - wa) * ease3((t - a) / (b - a))
    return _GRADE[-1][1]


# =============================================================================== needle
def needle_at(t):
    """-> None or dict(x, y, lift, plunge, alpha, rgb) in cell coords."""
    if t < 2.0:
        st = A1["stem"]
        i = bi(t)
        j = min(max(i, 0), 3)
        tgt = st[j]
        nb = BEATS[min(i + 1, len(BEATS) - 1)] if i >= 0 else BEATS[0]
        pb = BEATS[i] if i >= 0 else -0.45
        ph = (t - pb) / max(nb - pb, 1e-3)
        nxt = st[min(j + 1, 3)] if i >= 0 else st[0]
        if i < 0:
            tgt = st[0]
        # after a stitch: rise, travel, come down on the next beat
        e = E.ease_io(ph, 2.0)
        x = tgt[0] + (nxt[0] - tgt[0]) * e
        y = tgt[1] + (nxt[1] - tgt[1]) * e
        lift = 1.7 * math.sin(math.pi * ph) ** 0.8 if i >= 0 else 1.7 * (1 - ph) ** 1.5 + 0.0
        if i < 0:
            lift = 2.2 * (1 - E.ease_io(max(ph, 0), 2.0))
        plunge = 0.10 * max(0.0, 1 - abs(ph - 0.0) * 9) + 0.10 * max(0.0, 1 - abs(1 - ph) * 9)
        return dict(x=x + 0.5, y=y + 0.5, lift=lift, plunge=plunge, alpha=1.0, rgb=E.PALETTE[1][1])
    act = None
    prev = None
    nxt = None
    for ev in NEEDLE:
        if ev[0] <= t <= ev[1]:
            act = ev
        elif ev[1] < t:
            if prev is None or ev[1] >= prev[1]:
                prev = ev
        elif ev[0] > t and nxt is None:
            nxt = ev
    if act:
        u = (t - act[0]) / max(act[1] - act[0], 1e-3)
        x = act[2] + (act[4] - act[2]) * u
        y = act[3] + (act[5] - act[3]) * u + act[6] * 0.7 * math.sin(t * 46)
        return dict(x=x, y=y, lift=0.25 + 0.3 * abs(math.sin(t * 23)), plunge=0.0, alpha=1.0, rgb=act[7])
    if prev and nxt and nxt[0] - prev[1] < 1.5:
        u = (t - prev[1]) / (nxt[0] - prev[1])
        e = E.ease_io(u, 2.0)
        x = prev[4] + (nxt[2] - prev[4]) * e
        y = prev[5] + (nxt[3] - prev[5]) * e
        return dict(x=x, y=y, lift=0.3 + 1.6 * math.sin(math.pi * u), plunge=0.0, alpha=1.0, rgb=prev[7])
    if prev and t - prev[1] < 0.6:
        u = (t - prev[1]) / 0.6
        return dict(x=prev[4] + 3 * u, y=prev[5] - 2 * u, lift=0.3 + 5 * u * u, plunge=0.0, alpha=1 - ease3(u), rgb=prev[7])
    if nxt and nxt[0] - t < 0.6:
        u = 1 - (nxt[0] - t) / 0.6
        return dict(x=nxt[2] + 3 * (1 - u), y=nxt[3] - 2 * (1 - u), lift=0.3 + 5 * (1 - u) ** 2, plunge=0.0, alpha=ease3(u), rgb=nxt[7])
    return None


# =============================================================================== frame
def _motion_blur(frame, t, cam):
    """Half-frame shutter: blur along the camera's travel on whips, radially on fast zooms, sideways on the flip."""
    dt = 1 / 60.0
    if any(t - dt < c <= t + 1e-6 for c in CUTS) or t < dt:
        return frame
    c0 = cam_at(t - dt)
    z = cam["zoom"]
    dx = (cam["x"] - c0["x"]) * z
    dy = (cam["y"] - c0["y"]) * z
    L = math.hypot(dx, dy)
    fx = abs(cam.get("flipx", 1.0))
    if fx < 0.9:
        L2 = (1 - fx) * 46
        frame = cv2.blur(frame, (int(L2) | 1, 1))
    if L > 22:
        Lb = (L - 22) * 1.25
        n = int(max(2, min(Lb, 110)))
        ker = np.zeros((2 * n + 1, 2 * n + 1), np.float32)
        cv2.line(ker, (int(n - dx / L * n), int(n - dy / L * n)), (int(n + dx / L * n), int(n + dy / L * n)), 1.0, 1, cv2.LINE_AA)
        ker /= ker.sum()
        frame = cv2.filter2D(frame, -1, ker, borderType=cv2.BORDER_REPLICATE)
    dz = math.log(cam["zoom"] / c0["zoom"])
    if abs(dz) > 0.012:
        acc = frame.astype(np.float32)
        n = 6
        for i in range(1, n):
            sc_ = math.exp(-dz * i / (n - 1) * 1.0)
            Mz = np.array([[sc_, 0, (1 - sc_) * E.W / 2], [0, sc_, (1 - sc_) * E.H / 2]], np.float32)
            acc += cv2.warpAffine(frame, Mz, (E.W, E.H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        frame = (acc / n).astype(np.uint8)
    return frame


def render(t, fi=0):
    cam = cam_at(t)
    frame, M = E.render_cloth(W, t, cam, back=cam["back"])
    frame = E.wrinkle(np.ascontiguousarray(frame), M)
    z = cam["zoom"]
    if cam["back"]:
        draw_tangle(frame, M, z * abs(cam.get("flipx", 1.0)) ** 0.5, seed=42 if t < 100 else (7 if t < 200 else 99))
    else:
        nd = needle_at(t)
        if nd and abs(cam.get("flipx", 1.0)) > 0.9:
            tip = E.project(M, nd["x"], nd["y"])
            if -400 < tip[0] < E.W + 400 and -400 < tip[1] < E.H + 400:
                zz = max(z, 5.0)
                ang = -38 + 26 * nd.get("rest", 0.0)
                anc = E.project(M, nd["x"] - 1.2, nd["y"] + 0.4)
                E.draw_needle(frame, tip, zz, nd["lift"], nd["rgb"], anchor=anc, ang_deg=ang, plunge=nd["plunge"], alpha=nd["alpha"])
    frame = _motion_blur(frame, t, cam)
    return E.finish(frame, fi, cam)


def main():
    cmd = sys.argv[1]
    if cmd == "still":
        os.makedirs(os.path.join(E.HERE, "scratch"), exist_ok=True)
        for a in sys.argv[2:]:
            t = float(a)
            f = render(t, int(t * 30))
            cv2.imwrite(os.path.join(E.HERE, "scratch", "still_%07.2f.jpg" % t), f[:, :, ::-1], [cv2.IMWRITE_JPEG_QUALITY, 92])
    elif cmd == "view":
        # view <name> <t> <x> <y> <zoom> [more t x y zoom ...]: stills through a fixed camera (layout checks)
        name = sys.argv[2]
        a = [float(v) for v in sys.argv[3:]]
        global cam_at
        real = cam_at
        for i in range(0, len(a), 4):
            t, x, y, z = a[i:i + 4]
            def cam_at(tt, x=x, y=y, z=z, t=t):
                c = real(t); c.update(x=x, y=y, zoom=z, rot=0.0, tilt=0.0, dof=0.0); c.pop("flipx", None); c["back"] = False
                return c
            f = render(t, int(t * 30))
            cv2.imwrite(os.path.join(E.HERE, "scratch", "%s_%d.jpg" % (name, i // 4)), f[:, :, ::-1], [cv2.IMWRITE_JPEG_QUALITY, 90])
        cam_at = real
    elif cmd == "sheet":
        name = sys.argv[2]
        ts = [float(a) for a in sys.argv[3:]]
        cols = 4
        tw, th = 400, 225
        rows = (len(ts) + cols - 1) // cols
        sheet = np.zeros((rows * (th + 18), cols * tw, 3), np.uint8)
        for i, t in enumerate(ts):
            f = cv2.resize(render(t, int(t * 30)), (tw, th), interpolation=cv2.INTER_AREA)
            y = (i // cols) * (th + 18); x = (i % cols) * tw
            sheet[y:y + th, x:x + tw] = f
            cv2.putText(sheet, "%.2f" % t, (x + 4, y + th + 14), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.imwrite(os.path.join(E.HERE, "scratch", name + ".jpg"), sheet[:, :, ::-1], [cv2.IMWRITE_JPEG_QUALITY, 88])
    elif cmd == "render":
        import subprocess
        f0, f1, out = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (E.W, E.H),
                              "-r", "30", "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
                              "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-movflags", "+faststart", out],
                             stdin=subprocess.PIPE)
        for fi in range(f0, f1):
            p.stdin.write(render(fi / 30.0, fi).tobytes())
        p.stdin.close()
        p.wait()
        print("done", f0, f1, out, flush=True)
    elif cmd == "fits":
        bad = [f for f in FITS if not f["ok"]]
        print(len(FITS), "text blocks;", len(bad), "failing")
        for f in bad:
            print("FAIL", f)
        os.makedirs(os.path.join(E.HERE, "scratch"), exist_ok=True)
        json.dump(FITS, open(os.path.join(E.HERE, "scratch", "fits.json"), "w"), indent=1, default=lambda o: int(o))


if __name__ == "__main__":
    main()
