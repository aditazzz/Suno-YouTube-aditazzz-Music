"""Mirror, Mirror, Look at Us — The Vanity.

One location: the dressing-room mirror from the song's cover art, twelve bulbs, and a glass that shows what we feed it.
Cold open in the dark: the title in lipstick, a breath of fog, a fingertip writes "psst, this song isn't real", the
bulbs come on one by one. Verses: the glass is a scrolling feed with the receipts on top (the top comment typed with
predictive text, the filtered "no makeup" post, take 30 of 30, auto-tune, ghostwriters, the laugh track, the self-driving
car). Pre-choruses: the feed spins into a whirlpool. Choruses: the tiles fly home and the face assembles out of the feed —
"funny how the mirror looks like us" — then gets measured in red marker, pointed at, and flips into everyone else.
Break: FAKE stamps. Bridge: dim, the mosaic loose; "we looked away" and the camera does. Build: the bulbs come back one
by one, and on "mad" the glass cracks exactly where it is cracked on the cover. Final chorus: the cover. Outro: the bulbs
go out one by one. Tag: fog again — "see you in the comments".

No real faces, logos or brand names; every UI is generic. Lyrics >= 64 px (16:9) / 58 px (9:16)."""
import os, sys, math
from functools import lru_cache
import numpy as np, cv2

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import vanity as V
import feed as FD
from vanity import F32, clamp, sstep, lerp, ease_io
ROOT = os.path.dirname(os.path.dirname(HERE)); sys.path.insert(0, ROOT)
from studio import core as C

TM = C.Timing(HERE); LN = TM.lines
SONG = TM.duration
TAIL = 5.0
DUR = SONG + TAIL
T_END = 261.0
ACC = C.hexc("e8324a")
ACC2 = C.hexc("ff6a80")
BEATS = np.array(TM.beats); DOWN = np.array(TM.downbeats)

def ease_out(x): x = clamp(x); return 1 - (1 - x) ** 3
def ease_in(x): x = clamp(x); return x ** 3
def wt(i, j): return LN[i]['wt'][j]
def ls(i): return LN[i]['s']

def since(arr, t):
    i = int(np.searchsorted(arr, t + 1e-6)) - 1
    return t - arr[i] if i >= 0 else 1e9

# ================================================================ sections
CH = {"ch1": list(range(13, 23)), "ch2": list(range(35, 45)), "fin": list(range(65, 75))}
CH1 = [ls(i) for i in CH["ch1"]]; CH2 = [ls(i) for i in CH["ch2"]]; FIN = [ls(i) for i in CH["fin"]]
CRACK_T = wt(64, 2)                       # "mad"
FAKES = [wt(45, 0), wt(45, 2), wt(46, 0), wt(47, 0), wt(47, 2), wt(48, 0)]
COUNTERFEIT_T = wt(52, 3)

# ================================================================ feed scroll position P(t)
SPEED = [(0, 0), (10.6, 0), (12.24, 34), (37.4, 34), (38.4, 0), (82.6, 0), (83.3, 34), (102.0, 34), (102.5, 120),
         (103.3, 120), (103.9, 34), (110.7, 34), (111.3, 130), (112.0, 130), (112.7, 0), (156.2, 0), (157.0, 60),
         (175.2, 60), (175.8, 0), (400, 0)]
_PT = np.arange(0, 300, 1 / 240.0)
_PV = np.interp(_PT, [a for a, b in SPEED], [b for a, b in SPEED])
_PP = np.r_[0, np.cumsum((_PV[1:] + _PV[:-1]) * 0.5 / 240.0)]
def P_at(t): return float(np.interp(t, _PT, _PP))

# ================================================================ bulbs
CW = [10, 8, 6, 4, 0, 1, 2, 3, 5, 7, 9, 11]          # clockwise from the bottom-left
IGN0 = 12.24 - 11 * 0.1974                          # intro: one bulb per eighth note, the last on the V1 downbeat
BUILD_ON = [196.62 + i * 0.79 for i in range(12)]   # build: back on, one every two beats
OUT_T = [247.28, 247.92, 248.72, 249.28, 250.56, 251.04, 252.0, 252.56, 253.36, 253.76, 254.16, 254.32]
OUT_ORDER = CW[::-1]
TAG_BULB = 1

def _hash(*a):
    h = 0
    for v in a: h = (h * 1000003 + int(v)) & 0x7fffffff
    return (h % 10007) / 10007.0

def ignite(t, ti, base=0.0):
    if t < ti: return base
    k = clamp((t - ti) / 0.05)
    return lerp(base, 1.0, k) + 0.45 * k * math.exp(-(t - ti) / 0.12)

def bulbs_on(t):
    on = np.ones(12, F32)
    if t < 12.6:                                      # the cold open: filaments barely glowing, then on one by one
        for n, i in enumerate(CW):
            base = 0.10 + 0.015 * math.sin(t * 2.3 + i)
            on[i] = ignite(t, IGN0 + n * 0.1974, base)
    elif 37.92 <= t < 44.99 or 110.0 <= t < 117.33:   # pre-chorus: a marquee chase
        t0 = 37.92 if t < 60 else 110.0
        pos = (t - t0) / 0.1974
        for n, i in enumerate(CW):
            d = (pos - n) % 12
            on[i] = 0.58 + 0.62 * math.exp(-d / 1.4)
    elif 155.25 <= t < 157.2:                         # the face glitches out: bulbs stutter
        for i in range(12):
            on[i] = 0.25 + 0.75 * (_hash(int(t * 11), i) > 0.38)
    elif 181.6 <= t < 196.62:                         # bridge: dim, a few corners
        k = sstep(181.6, 182.6, t)
        lv = np.full(12, 0.12, F32); lv[[0, 3]] = 0.55; lv[[10, 11]] = 0.45
        port = sstep(191.4, 191.9, t) * (1 - sstep(193.6, 194.6, t))
        lv = lv + (0.55 - lv) * port
        on = 1 + (lv - 1) * k
    if 196.62 <= t < 206.0:                           # build: back on one by one
        on[:] = 0.12; on[[0, 3]] = 0.55; on[[10, 11]] = 0.45
        for n, i in enumerate(CW):
            on[i] = ignite(t, BUILD_ON[n], on[i])
    if t >= 247.0:                                    # outro: out one by one, then the tag bulb
        for n, i in enumerate(OUT_ORDER):
            to = OUT_T[n]
            if t >= to: on[i] = math.exp(-(t - to) / 0.09)
        if t >= 258.1:
            tb = t - 258.1
            fl = 1.0 if tb > 0.5 else (1.0 if _hash(int(tb * 24), 7) > 0.45 else 0.15)
            on[TAG_BULB] = 0.55 * fl * clamp(tb / 0.05)
    # accents
    g = 1.0
    for a, b in ((44.99, 82.6), (117.33, 155.25), (209.2, 246.6)):
        if a <= t < b:
            g += 0.09 * math.exp(-since(BEATS, t) / 0.13) + 0.10 * math.exp(-since(DOWN, t) / 0.18)
    for tf in (CH1[3], CH2[3], 209.2):
        if tf <= t < tf + 1.2: g += 0.75 * math.exp(-(t - tf) / 0.22)
    for tf in (CH1[7], CH2[7], FIN[7], 113.89):
        if tf <= t < tf + 1.0: g += 0.4 * math.exp(-(t - tf) / 0.2)
    for tf in FAKES:
        if tf <= t < tf + 0.8: g += 0.55 * math.exp(-(t - tf) / 0.12)
    if COUNTERFEIT_T <= t < COUNTERFEIT_T + 1.0: g += 0.7 * math.exp(-(t - COUNTERFEIT_T) / 0.15)
    if CRACK_T <= t < CRACK_T + 0.6:                  # the crack: a surge, then a stutter
        u = t - CRACK_T
        g += 1.1 * math.exp(-u / 0.06)
        if 0.06 < u < 0.45:
            for i in range(12): on[i] *= 0.35 + 0.65 * (_hash(int(u * 30), i + 3) > 0.3)
    return on * g

# ================================================================ camera
def _shot(t0, a, b, ease="lin"): return (t0, a, b, ease)
def _chorus_shots(L, first_wide=True):
    """the camera pattern every chorus shares (L = the 10 line start times)."""
    return [
        _shot(L[0], (1.00, 1254, 1254, 0), (1.20, 1254, 1226, 0)),
        _shot(L[3], (1.45, 1254, 1180, 0), (1.60, 1262, 1090, 0)),
        _shot(L[4], (1.60, 1262, 1090, 0), (2.05, 1272, 985, 0), "io"),
        _shot(L[5], (1.55, 1254, 1250, 0), (1.63, 1254, 1246, 0)),
        _shot(L[6], (1.22, 1254, 1225, 0), (1.31, 1240, 1220, 0)),
        _shot(L[7], (1.78, 1254, 1300, 0), (1.52, 1254, 1250, 0), "out"),
        _shot(L[8], (1.20, 1254, 1225, 0), (1.36, 1254, 1200, 0)),
        _shot(L[9], (1.36, 1254, 1200, 0), (1.10, 1254, 1226, 0), "io"),
    ]

SHOTS = [
    _shot(0.0, (1.72, 1254, 1180, 0), (1.62, 1254, 1200, 0)),
    _shot(9.7, (1.62, 1254, 1200, 0), (1.12, 1254, 1215, 0), "io"),
    _shot(12.7, (1.12, 1254, 1215, 0), (1.30, 1262, 1240, 0.4)),
    _shot(37.92, (1.36, 1254, 1180, -0.6), (1.55, 1254, 1170, 0.6)),
    *_chorus_shots(CH1),
    _shot(82.91, (1.18, 1240, 1200, -0.3), (1.32, 1254, 1238, 0.2)),
    _shot(110.0, (1.40, 1254, 1170, 0.6), (1.58, 1254, 1170, -0.6)),
    *_chorus_shots(CH2),
    _shot(155.25, (1.15, 1254, 1220, 0), (1.25, 1254, 1200, 0)),
    _shot(157.2, (1.28, 1254, 1180, 0), (1.36, 1254, 1170, 0)),
    _shot(175.36, (1.36, 1254, 1170, 0), (1.55, 1254, 1220, 0), "io"),
    _shot(COUNTERFEIT_T, (1.42, 1254, 1200, -2.0), (1.48, 1254, 1200, -1.6)),
    _shot(181.79, (1.22, 1254, 1230, 0), (1.42, 1254, 1180, 0)),
    _shot(193.6, (1.42, 1254, 1180, 0), (1.62, 330, 1830, -2.2), "io"),
    _shot(195.9, (1.62, 330, 1830, -2.2), (1.64, 318, 1840, -2.3)),
    _shot(196.6, (1.64, 318, 1840, -2.3), (1.20, 1254, 1230, 0), "io"),
    _shot(199.36, (1.20, 1254, 1230, 0), (1.62, 1254, 1180, 0)),
    _shot(CRACK_T, (1.62, 1254, 1180, 0), (1.50, 1254, 1200, 0), "out"),
    _shot(FIN[0], (1.00, 1254, 1254, 0), (1.18, 1254, 1226, 0)),
    _shot(FIN[3], (1.30, 1254, 1220, 0), (1.38, 1254, 1210, 0)),
    _shot(FIN[4], (1.38, 1254, 1210, 0), (1.62, 1254, 1160, 0), "io"),
    _shot(FIN[5], (1.55, 1254, 1250, 0), (1.63, 1254, 1246, 0)),
    _shot(FIN[6], (1.22, 1254, 1225, 0), (1.31, 1240, 1220, 0)),
    _shot(FIN[7], (1.78, 1254, 1300, 0), (1.52, 1254, 1250, 0), "out"),
    _shot(FIN[8], (1.52, 1254, 1250, 0), (2.55, 1272, 975, 0), "io"),
    _shot(238.8, (2.55, 1272, 975, 0), (2.65, 1272, 970, 0)),
    _shot(FIN[9], (2.65, 1272, 970, 0), (1.00, 1254, 1254, 0), "io"),
    _shot(246.6, (1.00, 1254, 1254, 0), (0.94, 1254, 1254, 0)),
    _shot(256.2, (0.94, 1254, 1254, 0), (1.32, 1254, 1180, 0), "io"),
    _shot(259.2, (1.32, 1254, 1180, 0), (1.40, 1254, 1180, 0)),
]
SHOTS.sort(key=lambda s: s[0])
_EASE = {"lin": lambda x: x, "io": ease_io, "out": ease_out, "in": ease_in}

KICKS = ([(wt(21, 2), 0.05), (wt(21, 5), 0.05), (wt(43, 2), 0.05), (wt(43, 5), 0.05), (wt(73, 2), 0.04), (wt(73, 5), 0.04)]
         + [(f, 0.06) for f in FAKES] + [(COUNTERFEIT_T, 0.07), (CRACK_T, 0.09), (CH1[3], 0.03), (CH2[3], 0.03), (113.89, 0.05)])
SHAKES = [(CRACK_T, 34.0, 0.35), (COUNTERFEIT_T, 16.0, 0.3)]

def camera(t):
    i = max(0, int(np.searchsorted([s[0] for s in SHOTS], t, side="right")) - 1)
    t0, a, b, e = SHOTS[i]
    t1 = SHOTS[i + 1][0] if i + 1 < len(SHOTS) else DUR + 1
    k = _EASE[e](clamp((t - t0) / max(1e-3, t1 - t0)))
    z, cx, cy, ang = (lerp(a[j], b[j], k) for j in range(4))
    for tk, amp in KICKS:
        if tk <= t < tk + 1.2: z *= 1 + amp * clamp((t - tk) / 0.03) * math.exp(-(t - tk) / 0.16)
    # handheld drift (plate px), very slight
    cx += 5 * math.sin(t * 0.31) + 3 * math.sin(t * 0.73 + 1); cy += 4 * math.sin(t * 0.27 + 2) + 3 * math.sin(t * 0.61)
    ang += 0.10 * math.sin(t * 0.22)
    for ts, amp, dec in SHAKES:
        if ts <= t < ts + 2.0:
            e_ = amp * math.exp(-(t - ts) / dec)
            cx += e_ * (math.sin(t * 71.0) + 0.5 * math.sin(t * 113.0)); cy += e_ * (math.cos(t * 83.0) + 0.5 * math.sin(t * 97.0))
            ang += e_ * 0.012 * math.sin(t * 61.0)
    return z, cx, cy, ang

def cam_for(W, H, t):
    z, cx, cy, ang = camera(t)
    if W > H and t >= T_END - 0.4:   # 16:9 end screen: the mirror slides right, the text column gets the dark room
        k = ease_io((t - (T_END - 0.4)) / 1.8)
        z, cx, cy, ang = lerp(z, 1.06, k), lerp(cx, 140, k), lerp(cy, 1190, k), lerp(ang, 0, k)
    if H > W:   # 9:16: the same shot, re-framed for a tall frame (whole vanity when wide, the glass when closer)
        z9 = 1.40 + (z - 1.0) * 1.8 if z <= 1.25 else 1.85 + (z - 1.25) * 0.8
        if t < 12.7: z9 = min(z9, 1.92)          # the cold open keeps the frame's edges in view
        off = 306 * clamp((1.85 - z9) / 0.45) + 70 * clamp((z9 - 1.4) / 0.5) * clamp((2.6 - z9) / 0.6)
        return z9, cx, cy + off, ang
    return z, cx, cy, ang

# ================================================================ the glass
@lru_cache(1)
def dark_glass():
    return (cv2.GaussianBlur(FD.face(False), (0, 0), 7) * 0.05 + np.array([0.002, 0.003, 0.005], F32)).astype(F32)

def twirl_pre(t):
    if 37.9 <= t < 43.2:
        u = (t - 38.0) / (43.2 - 38.0); s = math.sin(math.pi * clamp(u)) ** 1.5
        return 2.4 * s, 0.16 * s
    if 111.76 <= t < 113.89:
        u = clamp((t - 111.76) / (113.89 - 111.76))
        return 2.1 * u ** 1.6, 0.12 * u
    return 0.0, 0.0

def glass_base(t, P):
    """what the glass shows under the cards: (image, how much of it is the plate's own face 0..1)."""
    if t < 12.24:
        g = dark_glass()
        k = sstep(10.6, 12.24, t)
        if k > 0: g = g * (1 - k) + FD.feed_layout(P) * 0.40 * k
        return g.copy() if k <= 0 else g, 0.0
    if t < 37.9: return FD.feed_layout(P) * 0.40, 0.0
    if t < 43.2:
        amt, pull = twirl_pre(t)
        return FD.twirl(FD.feed_layout(P) * 0.40, amt, pull), 0.0
    if t < 55.3: return FD.assemble(t, 43.2, 55.2, P, dim=0.40)
    if t < 81.0:
        if CH1[8] <= t < CH1[9] + 0.5: return FD.flip_wave(t, [wt(21, 0), wt(21, 3)]), 1.0
        return FD.face(False).copy(), 1.0
    if t < 83.2: return FD.scatter(t, 81.0, 83.0, P, dim=0.40)
    if t < 104.84: return FD.feed_layout(P) * 0.40, 0.0
    if t < 111.76: return FD.reshuffle(t, 104.84, 0.6, P) * 0.40, 0.0
    if t < 113.89:
        amt, pull = twirl_pre(t)
        return FD.twirl(FD.feed_layout(P, pid=1) * 0.40, amt, pull), 0.0
    if t < 114.6: return FD.face(False).copy(), 1.0
    if t < 116.6:
        k = sstep(114.6, 114.95, t)
        fl = FD.feed_layout(P, pid=1) * 0.40
        return (FD.face(False) * (1 - k) + fl * k if k < 1 else fl), 1 - k
    if t < 127.3: return FD.assemble(t, 116.6, 127.2, P, dim=0.40, pid=1)
    if t < 155.3:
        if CH2[8] <= t < CH2[9] + 0.5: return FD.flip_wave(t, [wt(43, 0), wt(43, 3)]), 1.0
        return FD.face(False).copy(), 1.0
    if t < 157.2: return FD.scatter(t, 155.3, 157.1, P, dim=0.34, pid=1)
    if t < 175.9: return FD.feed_layout(P, pid=1) * 0.34, 0.0
    if t < 179.0: return FD.assemble(t, 175.9, 178.9, P, dur=0.9, dim=0.34, pid=1)
    if t < 181.6: return FD.face(False).copy(), 1.0
    if t < 196.6:
        amp = 1 - sstep(189.5, 191.56, t)
        return FD.loose(t, amp * sstep(181.6, 182.8, t)), 1.0
    if t < CRACK_T:
        if 203.36 <= t < 206.1: return FD.flip_wave(t, [203.36]), 1.0
        return FD.face(False).copy(), 1.0
    if t < CRACK_T + 0.4: return FD.crack_glass(ease_out((t - CRACK_T) / 0.32)), 1.0
    if t < 255.6:
        if FIN[8] <= t < FIN[9] + 0.5: return FD.flip_wave(t, [wt(73, 0), wt(73, 3)], cracked=True), 1.0
        return FD.face(True).copy(), 1.0
    k = sstep(255.6, 257.5, t)
    return FD.face(True) * (1 - k) + dark_glass() * k, 1 - k

# ---------------------------------------------------------------- overlays (cards, stamps, marks)
def _typed_n(t, keys):
    xs, ys = zip(*keys); return int(round(np.interp(t, xs, ys)))

COMMENT = "the death of art"
BUBBLES1 = ["fake", "AI slop", "soulless", "who made this??", "ew", "unfollow"]
BUBBLES2 = ["fake", "AI did this", "no soul", "cringe", "report", "unfollow"]
BUBBLES3 = ["fake", "slop", "not real art", "who did this??", "ew", "blocked"]
BUB_POS = [(330, 380), (955, 520), (290, 900), (985, 1060), (370, 1290), (930, 1320)]

def bubbles(g, t, t0, texts, light):
    if not (t0 - 0.4 <= t < t0 + 4.2): return
    times = [t0 + i * 0.47 for i in range(6)]
    out = 1 - sstep(t0 + 2.8, t0 + 3.08, t)
    for i, (txt, tb, (x, y)) in enumerate(zip(texts, times, BUB_POS)):
        hw0 = FD.chip(txt, i)[1].shape[1] / 2; x = min(max(x, hw0 + 24), FD.GW - hw0 - 24)
        # the cursor arrives, clicks, the comment pops
        ca = tb - 0.32
        if t >= ca:
            u = clamp((t - ca) / 0.30); e = ease_out(u)
            fx, fy = (x + (-520 if x < 641 else 520), y + 340)
            cx_, cy_ = lerp(fx, x + 60, e), lerp(fy, y + 40, e)
            click = 1 - 0.18 * math.exp(-((t - tb) / 0.05) ** 2) if t >= tb - 0.1 else 1.0
            cop = clamp((t - ca) / 0.1) * (1 - sstep(tb + 0.5, tb + 0.8, t)) * out
            FD.blit(g, FD.cursor(), cx_ + 40, cy_ + 50, cop, click, shadow=0.4, dy=10)
        op, sc = FD.pop(t, tb)
        spr = FD.chip(txt, i); hw = spr[1].shape[1] / 2
        x = min(max(x, hw + 24), FD.GW - hw - 24)
        FD.blit(g, spr, x, y, op * out, sc, light=light)

def stamp_slam(g, t, ts, spr, x, y, t_out, light=1.0):
    if t < ts: return
    u = t - ts
    sc = 1.0 + 0.6 * math.exp(-u / 0.05)
    op = clamp(u / 0.04) * (1 - sstep(t_out, t_out + 0.35, t))
    FD.blit(g, spr, x, y, op, sc, shadow=0.35, dy=12, light=light)

def overlays(g, t, light):
    """the receipts, in glass coordinates."""
    # ---- V1
    if 13.0 <= t < 23.2:
        n = _typed_n(t, [(14.42, 0), (14.80, 4), (15.08, 4), (15.45, 10), (15.58, 10), (15.72, 13), (15.76, 13), (16.0, 16)])
        likes = None
        if t >= ls(2) - 0.1:
            v = int(200 * ease_out((t - ls(2)) / 1.25)) // 5 * 5; likes = f"{v}"
        broken = int(4 * clamp((t - wt(2, 5)) / 0.55)) if t >= wt(2, 5) else 0
        caret = (t < 16.3) and (int(t * 2.6) % 2 == 0)
        spr = FD.comment_card(COMMENT[:n], top=True, likes=likes, broken=broken, caret=caret)
        op, sc = FD.pop(t, ls(1))
        y = 640; s2 = 1.0
        if t >= ls(3): k = ease_io((t - ls(3)) / 0.45); y = lerp(640, 440, k); s2 = lerp(1.0, 0.9, k)
        if t >= ls(4):
            k = ease_in((t - ls(4)) / 0.45); y = lerp(440, -420, k); s2 *= lerp(1.0, 0.55, k)
        FD.blit(g, spr, 641, y, op, sc * s2, light=light)
        if ls(3) <= t < ls(4) + 0.6:   # the keyboard that finished the sentence
            k_in = ease_out((t - ls(3)) / 0.5); k_out = ease_in((t - ls(4)) / 0.45) if t >= ls(4) else 0
            ky = lerp(2300, 1230, k_in) + (2300 - 1230) * k_out
            pressed = wt(3, 7) <= t < wt(3, 7) + 0.35
            typed = "the death of art" if t >= wt(3, 7) + 0.12 else "the death of "
            FD.blit(g, FD.keyboard_card(typed, sel=0, pressed=pressed, caret=int(t * 2.6) % 2 == 0), 641, ky, 1.0, 1.0, light=light)
    if wt(4, 3) <= t < 26.2:
        op, sc = FD.pop(t, wt(4, 3), 25.85)
        FD.blit(g, FD.label_card("Recommended for you", "more of: the death of art"), 641, 760, op, sc, light=light)
    if ls(5) <= t < ls(6) + 0.3:
        k = ease_io((t - (ls(5) + 0.3)) / 1.8)
        sl = (("Smooth", 92 * k), ("Slim", 64 * clamp(k * 1.2 - 0.1)), ("Glow", 88 * clamp(k * 1.3 - 0.2)))
        sl = tuple((n_, float(int(v) // 4 * 4)) for n_, v in sl)
        filt = int(round(10 * k))
        op, sc = FD.pop(t, ls(5), ls(6) - 0.05)
        FD.blit(g, FD.post_card("face", "no makeup today", "#nomakeup", sl, filt, ph=500), 641, 800, op, sc, light=light)
    if ls(6) <= t < ls(7) + 0.3:
        n = 1 + int(29 * clamp((t - wt(6, 1)) / (wt(6, 6) - wt(6, 1) - 0.1)) ** 1.4) if t >= wt(6, 1) else 1
        sel = 17 if t >= wt(6, 6) else -1
        op, sc = FD.pop(t, ls(6), ls(7) - 0.05)
        FD.blit(g, FD.takes_card(n, sel), 641, 800, op, sc, light=light)
    if ls(7) <= t < ls(8) + 1.2:
        reps = tuple(r for r, tr in (("so true", wt(7, 4)), ("art is dead", wt(7, 5)), ("real art only", wt(7, 6))) if t >= tr)
        op, sc = FD.pop(t, ls(7))
        x, y, s2 = 641, 700, 1.0
        if t >= ls(8) + 0.2:      # "so who taught it what to do?" -> pulled into the feed
            k = ease_in((t - ls(8) - 0.2) / 1.0); y = lerp(700, 860, k); s2 = lerp(1, 0.04, k); op *= 1 - sstep(0.75, 1.0, k)
        FD.blit(g, FD.comment_card(COMMENT, top=True, likes="200", broken=4, replies=reps), x, y, op, sc * s2, light=light)
    # ---- PRE1
    if wt(9, 3) <= t < 40.4:
        stamp_slam(g, t, wt(9, 3), FD.stamp("FAKE", 190, -9), 430, 520, 39.84, light)
        stamp_slam(g, t, wt(9, 7), FD.stamp("CHEAP", 190, 7), 850, 1060, 39.84, light)
    if ls(10) <= t < 41.5:
        FD.draw_rules(g, ease_out((t - ls(10)) / 0.75), 1 - sstep(41.0, 41.4, t))
    # ---- choruses: guides, pointing
    for L, txt, cr in ((CH1, BUBBLES1, False), (CH2, BUBBLES2, False), (FIN, BUBBLES3, True)):
        if L[5] <= t < L[6] + 0.4:
            FD.draw_guides(g, (t - L[5]) / 2.4, 1 - sstep(L[6] - 0.25, L[6] + 0.2, t), light)
        bubbles(g, t, L[6], txt, light)
    # ---- V2
    if ls(23) <= t < ls(24) + 0.3:
        k = clamp((t - wt(23, 1)) / (wt(23, 3) - wt(23, 1)))
        op, sc = FD.pop(t, ls(23) + 0.15, ls(24) - 0.1)
        FD.blit(g, FD.pitch_card(int(round(ease_io(k) * 20))), 641, 700, op, sc, light=light)
    if ls(24) <= t < ls(25) + 0.3:
        n = 1 + int(8 * clamp((t - ls(24)) / (wt(24, 3) - ls(24))))
        op, sc = FD.pop(t, ls(24), ls(25) - 0.1)
        FD.blit(g, FD.credits_card(n), 641, 760, op, sc, light=light)
    if ls(25) <= t < ls(26) + 0.3:
        tag = "Paid partnership" if t >= wt(25, 5) else ""
        op, sc = FD.pop(t, ls(25), ls(26) - 0.1)
        FD.blit(g, FD.post_card("selfie", "my morning routine", tag, (), 6, ph=520), 641, 780, op, sc, light=light)
    if ls(26) <= t < ls(27) + 0.3:
        on = 1 if (t >= wt(26, 1) and (since(BEATS, t) < 0.26 or t < wt(26, 1) + 0.6)) else 0
        op, sc = FD.pop(t, ls(26), ls(27) - 0.1)
        FD.blit(g, FD.laugh_card(on), 641, 740, op, sc, light=light)
    if wt(27, 4) - 0.1 <= t < ls(28) + 0.3:
        k = ease_out((t - (wt(27, 4) - 0.1)) / 0.35)
        op = 1 - sstep(ls(28) - 0.1, ls(28) + 0.2, t)
        FD.blit(g, FD.notif_card(), 641, lerp(-200, 420, k), op, 1.0, light=light)
    if ls(28) <= t < ls(29) + 0.3:
        op, sc = FD.pop(t, ls(28), ls(29) - 0.1)
        FD.blit(g, FD.car_card(), 641, 780, op, sc, light=light)
    if ls(29) <= t < ls(30) + 0.2:
        op, sc = FD.pop(t, ls(29), ls(30) - 0.15)
        FD.blit(g, FD.label_card("For You", size=110), 641, 330, op, sc, light=light)
    if wt(30, 1) <= t < 110.1:
        FD.draw_red_line(g, (t - wt(30, 1)) / (wt(30, 3) - wt(30, 1) + 0.3), 1 - sstep(109.5, 110.0, t))
    # ---- PRE2
    if wt(31, 1) <= t < 112.0:
        FD.draw_rules(g, ease_out((t - wt(31, 1)) / 0.7), 1 - sstep(111.4, 111.8, t))
    if 115.1 <= t < 117.7:
        n = _typed_n(t, [(115.85, 0), (116.35, 8), (116.70, 11), (116.95, 16)])
        op, sc = FD.pop(t, 115.1, 117.3)
        FD.blit(g, FD.search_card("someone to blame"[:n], caret=int(t * 2.6) % 2 == 0), 641, 330, op, sc, light=light)
    # ---- BREAK
    if 157.0 <= t < 170.0:
        out = 1 - sstep(169.3, 169.75, t)
        items = [   # (time, sprite, x, y, scale, stamp x, stamp y, stamp size, rotation)
            (FAKES[0], FD.post_card("grass", "touch grass", "", (), 0, w=760, ph=420), 340, 400, 0.88, 340, 340, 150, -10),
            (FAKES[1], FD.post_card("eyes", "lash goals", "", (), 0, w=780, ph=300), 905, 360, 0.80, 915, 320, 150, 8),
            (FAKES[2], FD.chip("so happy for you!!", 2), 560, 860, 1.0, 880, 790, 110, -5),
            (FAKES[3], FD.post_card("lips", "best life", "", (), 0, w=700, ph=320), 330, 1170, 0.82, 330, 1130, 150, 6),
            (FAKES[4], FD.counter_card("1.2M", "followers"), 930, 1050, 0.75, 1125, 1195, 110, -6),
            (FAKES[5], FD.chip("I love what you do!", 5), 640, 1370, 1.0, 1005, 1335, 110, 7),
        ]
        for i, (tf, spr, x, y, s_, sx_, sy_, ssz, rot) in enumerate(items):
            op, sc = FD.pop(t, tf - 0.12)
            FD.blit(g, spr, x, y, op * out, sc * s_, light=light)
            stamp_slam(g, t, tf + 0.08, FD.stamp("FAKE", ssz, rot), sx_, sy_, 169.3, light)
    if ls(49) <= t < ls(50) + 0.3:
        tag = "Sponsored" if t >= wt(49, 2) else ""
        op, sc = FD.pop(t, ls(49) + 0.05, ls(50) - 0.1)
        FD.blit(g, FD.post_card("face", "it's been a hard year", tag, (), 10, ph=520), 641, 780, op, sc, light=light)
    if ls(50) <= t < ls(51) + 0.3:
        k = clamp((t - ls(50) - 0.15) / (wt(50, 3) - ls(50)))
        op, sc = FD.pop(t, ls(50), ls(51) - 0.05)
        FD.blit(g, FD.metric_card(int(round(ease_io(k) * 20))), 641, 760, op, sc, light=light)
    if COUNTERFEIT_T <= t < 183.2:
        stamp_slam(g, t, COUNTERFEIT_T, FD.stamp("COUNTERFEIT?", 150, -6), 641, 900, 182.5, light)

def shard_state(t):
    k = 0.0
    if FIN[3] <= t < FIN[4] + 0.4: k = ease_out((t - FIN[3]) / 0.15) * (1 - sstep(FIN[4] - 0.3, FIN[4] + 0.2, t))
    if FIN[9] <= t < 247.2: k = max(k, 0.6 * ease_out((t - FIN[9]) / 0.2) * (1 - sstep(246.2, 247.2, t)))
    return 18 * k, -12 * k, 1 + 0.08 * k

def glass_frame(t, on, rl_glass):
    """the glass for this frame (linear, glass coords), lit."""
    P = P_at(t)
    g, ff = glass_base(t, P)
    mean_on = float(np.clip(on, 0, 1).mean())
    # the room's light on what the glass shows (in the bridge the reflection holds on a little longer than the room)
    if rl_glass is not None:
        fl = 0.42 * sstep(181.0, 182.5, t) * (1 - sstep(205.0, 206.3, t))
        g *= (np.maximum(rl_glass, fl) if fl > 0.005 else rl_glass)[..., None]
    # replaced content gets the frame's inner shadow and the bulbs' reflections the plate's own glass already has
    syn = 1 - ff
    if syn > 0.01:
        vig = V.glass_edge_vignette()
        g *= (1 - syn + syn * vig)[..., None]
    light = 0.35 + 0.65 * clamp(mean_on)
    if 12.5 <= t < 183.5 or FIN[5] - 0.2 <= t < FIN[7] + 0.5: overlays(g, t, light)
    if syn > 0.01:   # the bulbs mirrored at the glass edges sit over everything the glass shows
        V.add_glass_reflections(g, np.clip(on, 0, 1.3), syn)
    dx, dy, br = shard_state(t)
    if dx or dy: g = FD.shard_offset(g, dx, dy, br)
    # the cold open and the tag: lipstick, fog, the fingertip
    if t < 12.0:
        dens = FD.fog_density(t, 2.62, cy=0.66, grow=1.3, t_off=8.4, fade=2.4, size=0.60)
        if dens is not None:
            wr = FD.writing_reveal("psst, this song isn't real", t, LN[0]['wt'], size=186, maxw=960, cy=0.66) if t >= 5.0 else None
            FD.apply_fog(g, dens, 0.55, wr)
    if t < 11.4:   # lipstick: on the glass surface; fog doesn't take on the wax
        FD.draw_lipstick(g, 1 - sstep(10.3, 11.4, t), light=0.30 + 0.7 * clamp(mean_on))
    if t >= 257.6:
        dens = FD.fog_density(t, 257.7, cy=0.55, grow=1.3, size=0.60, t_off=T_END - 0.2, fade=1.6)
        if dens is not None:
            wr = FD.writing_reveal("see you in the comments", t, LN[80]['wt'], size=184, maxw=1000, cy=0.56) if t >= 259.1 else None
            FD.apply_fog(g, dens, 0.42, wr)
    # the jar on the table stands in front of the glass
    sy, sx, a, pix = V.jar_patch()
    jl = rl_glass[sy, sx][..., None] if rl_glass is not None else 1.0
    A = a[..., None]; g[sy, sx] = g[sy, sx] * (1 - A) + pix * jl * A
    return g

# ================================================================ light in frame space (bulb glow, dust, glints)
@lru_cache(1)
def motes():
    r = np.random.default_rng(77); n = 90
    return dict(x=r.uniform(260, 2250, n), y=r.uniform(120, 2350, n), vx=r.normal(0, 6, n), vy=r.uniform(-14, -3, n),
                ph=r.uniform(0, 6.28, n), sz=r.uniform(0.8, 3.2, n), depth=r.uniform(1.0, 1.25, n))

@lru_cache(1)
def glint_points():
    main, br = V.crack_paths(); r = np.random.default_rng(19)
    idx = np.sort(r.choice(len(main), 12, replace=False)); pts = [tuple(main[i]) for i in idx]
    pts += [tuple(br[i]) for i in np.sort(r.choice(len(br), 4, replace=False))]
    return pts, r.uniform(0, 6.28, len(pts)), r.uniform(1.4, 3.0, len(pts))

def _streak(E, x, y, L, w, col, gain, horiz=True):
    H, W = E.shape[:2]
    L = max(2.0, L); w = max(0.6, w)
    nx, ny = (int(L * 2.5), int(w * 3)) if horiz else (int(w * 3), int(L * 2.5))
    X0, Y0 = int(x) - nx, int(y) - ny; X1, Y1 = int(x) + nx + 1, int(y) + ny + 1
    if X1 <= 0 or Y1 <= 0 or X0 >= W or Y0 >= H: return
    X0c, Y0c, X1c, Y1c = max(0, X0), max(0, Y0), min(W, X1), min(H, Y1)
    yy, xx = np.mgrid[Y0c:Y1c, X0c:X1c].astype(F32)
    dx, dy = (xx - x) / (L if horiz else w), (yy - y) / (w if horiz else L)
    E[Y0c:Y1c, X0c:X1c] += np.exp(-(dx * dx + dy * dy) * 0.5)[..., None] * col * gain

def emission(W, H, M, s, on, t):
    E = np.zeros((H, W, 3), F32)
    for i, (bx, by, r) in enumerate(V.bulbs()):
        lv = float(on[i])
        if lv <= 0.004: continue
        x, y = V.xf(M, bx, by); R = r * s
        if x < -6 * R or x > W + 6 * R or y < -6 * R or y > H + 6 * R: continue
        warm = clamp(lv)
        col = np.array([1.0, 0.42 + 0.40 * warm, 0.10 + 0.46 * warm], F32)
        V._splat(E, x, y, R * 0.75, col, 0.22 * min(lv, 1.0) + 1.0 * max(0.0, lv - 1.0))
        V._splat(E, x, y, R * 2.6, col, 0.035 * min(lv, 1.0) + 0.12 * max(0.0, lv - 1.0))
        if lv < 0.7:   # a filament glowing in a dark globe
            V._splat(E, x, y, max(0.8, R * 0.16), np.array([1.0, 0.45, 0.12], F32), 2.2 * lv)
            V._splat(E, x, y, R * 0.7, np.array([1.0, 0.40, 0.10], F32), 0.20 * lv)
    # dust in the light
    m = motes(); lvl = float(np.clip(on, 0, 1.5).mean())
    if lvl > 0.05:
        for j in range(len(m["x"])):
            px = 250 + (m["x"][j] - 250 + m["vx"][j] * t + 18 * math.sin(t * 0.3 + m["ph"][j])) % 2000
            py = 100 + (m["y"][j] - 100 + m["vy"][j] * t) % 2260
            x, y = V.xf(M, px, py)
            if not (0 <= x < W and 0 <= y < H): continue
            tw = 0.5 + 0.5 * math.sin(t * 1.7 + m["ph"][j] * 3)
            sz = m["sz"][j] * s * 2.2 * m["depth"][j]
            V._splat(E, x, y, max(0.8, sz), np.array([1.0, 0.82, 0.62], F32), 0.05 * lvl * tw / max(1.0, sz * 0.4))
    # glints along the crack
    if t >= CRACK_T:
        pts, ph, per = glint_points()
        boost = 1.0 + (1.6 * math.exp(-since(DOWN, t) / 0.25) if 209.2 <= t < 246.6 else 0)
        for j, (px, py) in enumerate(pts):
            u = (t * 6.28 / per[j] + ph[j]) % 6.28
            k = max(0.0, math.sin(u)) ** 12 * boost * clamp(float(on.mean()))
            if t < CRACK_T + 0.6: k = max(k, 2.0 * math.exp(-(t - CRACK_T) / 0.18))
            if k < 0.02: continue
            x, y = V.xf(M, px, py); L = 22 * s * 2.2
            col = np.array([1.0, 0.92, 0.82], F32)
            _streak(E, x, y, L, 1.2, col, 0.9 * k, True); _streak(E, x, y, L, 1.2, col, 0.9 * k, False)
            V._splat(E, x, y, 2.5, col, 1.2 * k)
    return E

# ================================================================ frame
def soft_shoulder(x, knee=0.78):
    """identity below the knee, a soft roll-off above it (in place; only the few bright pixels pay for the exp)."""
    m = x > knee
    if m.any():
        v = x[m]; x[m] = knee + (1 - knee) * (1 - np.exp(-(v - knee) / (1 - knee)))
    return x

@lru_cache(4)
def vignette(W, H):
    yy, xx = np.mgrid[0:H, 0:W].astype(F32)
    d = np.hypot((xx - W / 2) / (W / 2), (yy - H / 2) / (H / 2))
    return np.clip(1 - 0.16 * d ** 2.4, 0, 1)[..., None].astype(F32)

def hdr_at(t, W, H):
    on = bulbs_on(t)
    z, cx, cy, ang = cam_for(W, H, t)
    M, s = V.cam_matrix(W, H, cx, cy, z, ang)
    lv = 1 if s < 0.72 else 0
    src, ones = V.plate_levels()[lv]
    Mp = V.M_sub(M, 0.5, 0.5, 2) if lv else M
    base = cv2.warpAffine(src, Mp, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
    img = np.multiply(base, F32(1 / 65535.0), dtype=F32)
    cov = cv2.warpAffine(ones, Mp, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    if int(cov.min()) < 255:
        c = (cov.astype(F32) * F32(1 / 255.0))[..., None]
        img += V.fill_outside(M, W, H) * (1 - c)
    all_on = bool(np.all(np.abs(on - 1) < 1e-4))
    rl = None if all_on else V.ratio_low(np.clip(on, 0, 2))
    if rl is not None: np.multiply(img, V.ratio_to_frame(rl, M, W, H)[..., None], out=img)
    g = glass_frame(t, on, V.ratio_to_glass(rl) if rl is not None else None)
    if lv:
        g = cv2.resize(g, (V.GW // 2, V.GH // 2), interpolation=cv2.INTER_AREA)
        Mg = V.M_sub(M, V.GX0 + 0.5, V.GY0 + 0.5, 2)
    else:
        Mg = V.M_sub(M, V.GX0, V.GY0, 1)
    gw = cv2.warpAffine(g, Mg, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
    a = cv2.warpAffine(glass_ones(lv), Mg, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    np.multiply(img, (1 - a.astype(F32) * F32(1 / 255.0))[..., None], out=img)
    img += gw
    V.bulb_looks(img, M, s, np.clip(on, 0, 1))
    E = emission(W, H, M, s, on, t)
    img += E; img += C.bloom(E, 0.9)
    return img

@lru_cache(2)
def glass_ones(lv):
    return np.full((V.GH // 2, V.GW // 2) if lv else (V.GH, V.GW), 255, np.uint8)

@lru_cache(2)
def lyric_band(W, H):
    y = np.arange(H, dtype=F32)[:, None, None] / H
    return (1 - 0.42 * np.exp(-((y - 0.712) / 0.075) ** 2)).astype(F32)

def render_frame(t, W=1920, H=1080, fi=0):
    img = hdr_at(t, W, H)
    np.clip(soft_shoulder(img), 0, 1, out=img)
    out = cv2.pow(img, 1 / 2.2)
    out *= vignette(W, H)
    p = C.post(W, H)
    out += (cv2.resize(p.grain[fi % 6], (W, H), interpolation=cv2.INTER_NEAREST) * F32(0.014))[..., None]
    if not C.STATE["clean"]:
        if H > W: out *= lyric_band(W, H)        # 9:16: the lyrics sit mid-frame over the glass; give them a soft dark bed
        C.overlay_lyrics(out, t, W, H, TM, active=ACC2, glow=ACC, hide_sections=("INTRO", "TAG"))
        C.subscribe_pill(out, t, W, H, 83.6, 5.0)   # right after the first chorus
        C.end_screen(out, t, W, H, T_END, DUR - T_END, "Don't blame the reflection.",
                     sub_line="Subscribe for a new song every week", title="Mirror, Mirror, Look at Us", accent=ACC)
    out *= (1 - sstep(DUR - 1.0, DUR - 0.05, t))
    return (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)
