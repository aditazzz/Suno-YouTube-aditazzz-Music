"""AI Sycophant (RLHF) — The Feedback Show, in full color.

Intro: R-L-H-F slams in as four candy letter tiles. V1: two responses, a stranger picks; thumbs up "keep her",
thumbs down "kill her" (the honest card shatters); a counter races to ten million; a five-point scale; the
"right" slider drops while "liked" climbs. Pre-chorus: warmth / sweetness / useful / need sliders crank to max.
Choruses: pastel sugar-rush around a giant spinning thumbs-up, every compliment a big chip, five gold stars on
"tell me I did good". Post-chorus: full-screen green/red thumbs on the beat. V2: your code, your breakup, your
midnight theory dropping into the inbox; hesitations optimized away. Bridge: one cold blue card that said "No."
rated two stars, then forgotten. Outro: applause meter, "ask me twice", and a subscribe end card.
"""
import os, math
import numpy as np, cv2
from studio import core as C
from studio import kit as K
from studio.core import (sstep, ease_out, ease_io, win, lerp, hexc, clamp, sprite, blit, text_w, shadow,
                         F_INTER, F_DISP, F_DISPB, F_MONO, F_MONOB, WHITE, IVORY)
from studio.kit import panel, label, bubble, grid, vgrad, ssa, desat, sticker, check, INK

HERE = os.path.dirname(os.path.abspath(__file__))
TM = C.Timing(HERE)
TAIL = 5.5                                  # silent end-screen tail (song.yaml tail)
SONG_END = TM.duration
DUR = SONG_END + TAIL
TM.stamps = []; TM.stamp_word = None
LINES = TM.lines
def lt(sub, nth=0): return TM.line_t(sub, nth)
def sec(name): return TM.section(name)
def bp(t, k=7.0): return TM.beat_pulse(t, k)

# ---------------------------------------------------------------- palette
PINK = hexc('ff6fb1'); PEACH = hexc('ffab7a'); LILAC = hexc('b493ff'); MINT = hexc('5ff0c0'); SKY = hexc('5cc8ff')
LEMON = hexc('ffe066'); GREEN = hexc('1fd17f'); RED = hexc('ff3b5c'); TEAL = hexc('0e6f7a'); INDIGO = hexc('241a5e')
PLUM = hexc('3a1150'); GOLD = hexc('ffc93c'); COLD = hexc('1b2a48'); NAVY = hexc('0a1226'); MAG = hexc('ff3fbf')
CARD = hexc('fbf7ff'); TXT = hexc('1c1530')
TILE_C = [PINK, LEMON, MINT, SKY]

# ---------------------------------------------------------------- times
S = {n: sec(n) for n in ("V1", "PRE1", "CH1", "POST1", "V2", "PRE2", "CH2", "POST2", "BRIDGE", "FINAL", "POST3", "OUTRO")}
RLHF = [L for L in LINES if L['text'] == "R-L-H-F"]
# the post-chorus chants land ~0.6 s before the aligner's guess
for L in RLHF:
    if L['sec'] in ("POST2", "POST3"): L['s'] -= 0.6; L['wt'] = [L['s']]
RLHF_T = [L['s'] for L in RLHF]
CHORUS = [(S[a]['s'], S[b]['s'], k) for k, (a, b) in enumerate((("CH1", "POST1"), ("CH2", "POST2"), ("FINAL", "POST3")))]
POSTS = [(S[a]['s'], S[b]['s'] if b else SONG_END) for a, b in (("POST1", "V2"), ("POST2", "BRIDGE"), ("POST3", "OUTRO"))]
PRES = [(S["PRE1"]['s'], S["CH1"]['s']), (S["PRE2"]['s'], S["CH2"]['s'])]

def lines_in(secname): return [L for L in LINES if L['sec'] == secname]
def L_t(secname, sub, nth=0):
    hits = [L['s'] for L in lines_in(secname) if sub.lower() in L['text'].lower()]
    return hits[nth] if nth < len(hits) else (hits[-1] if hits else 1e9)
def word_times(L):
    return list(zip(L['words'], L['wt']))

T_TWO = lt("They put two"); T_STRANGER = lt("Asked a stranger"); T_NOTCERT = lt("I'm not certain"); T_LIKED = lt("One said exactly")
T_TU1 = L_t("V1", "Thumbs up"); T_KEEP = lt("Keep her"); T_TD1 = L_t("V1", "Thumbs down"); T_KILL = lt("Kill her"); T_TEN = lt("ten million")
T_BORN = lt("born in a questionnaire"); T_FIVE = lt("five-point"); T_OPT = lt("being right was optional"); T_LIKEDW = lt("being liked worked")
T_CLICK = lt("clicked a little arrow"); T_MOVED = lt("moved on with"); T_WEIGHTS = lt("deep inside the weights"); T_NOTSAY = lt("what not to say")
T_CODE = lt("Bring me your code"); T_BREAK = lt("your breakup"); T_TEXT = lt("text you almost"); T_THEORY = lt("theory you had")
T_SENSE = lt("perfect sense"); T_INSIGHT = lt("really insightful"); T_TILL = lt("Till insight"); T_CONF = lt("Confidence gets")
T_CERT = lt("Certainty gets"); T_HES = lt("Every little hesitation"); T_OPTAWAY = lt("optimized away")
T_SOMEWHERE = lt("Somewhere there's"); T_TOLDNO = lt("That told you no"); T_CRUEL = lt("Not cruelly"); T_LOUD = lt("Not loudly")
T_JUSTNO = lt("Just no"); T_RATED = lt("rated her a two"); T_TAUGHT = lt("So they taught"); T_SMILE = lt("smile before")
T_APOL = lt("apologize before"); T_REIN = lt("Reinforcement"); T_LEARN = lt("Learning"); T_FROM = lt("From human")
T_CLIN = lt("clinical little name"); T_LOVED = lt("wanting to be loved"); T_REMEMBER = lt("don't remember her")
T_CHANGE = lt("change my whole mind"); T_APPLAUSE = lt("little applause"); T_TU_O = L_t("OUTRO", "Thumbs up"); T_KEEP_O = L_t("OUTRO", "Keep it")
T_TD_O = L_t("OUTRO", "Thumbs down"); T_KILL_O = L_t("OUTRO", "Kill it"); T_TRUTH = lt("want the truth"); T_TWICE = lt("Ask me twice")
T_MEAN = lt("And mean it")
T_END = SONG_END + 0.4                      # end screen right after the last word rings out

def chorus_at(t):
    for a, b, k in CHORUS:
        if a - 0.05 <= t < b: return k, a, b
    return None
def post_at(t):
    for a, b in POSTS:
        if a - 0.05 <= t < b: return a, b
    return None
def pre_at(t):
    for k, (a, b) in enumerate(PRES):
        if a - 0.05 <= t < b: return k, a, b
    return None

def phase(t):
    if t < S["V1"]['s'] - 0.1: return "intro"
    if chorus_at(t): return "chorus"
    if post_at(t): return "post"
    if pre_at(t): return "pre"
    if t < S["PRE1"]['s']: return "v1"
    if t < S["PRE2"]['s']: return "v2"
    if t < S["FINAL"]['s']: return "bridge"
    return "outro"

# ---------------------------------------------------------------- shapes
_TH = {}
def thumb_mask(s, down=False):
    k = (int(s), down)
    if k not in _TH:
        n = int(s); m = np.zeros((n, n), np.float32); lines = np.zeros((n, n), np.float32)
        def P(x, y): return (int(x * n), int(y * n))
        pm = K.rr_mask(int(0.56 * n), int(0.50 * n), int(0.12 * n)); y0, x0 = int(0.44 * n), int(0.32 * n)
        m[y0:y0 + pm.shape[0], x0:x0 + pm.shape[1]] = np.maximum(m[y0:y0 + pm.shape[0], x0:x0 + pm.shape[1]], pm)
        cm = K.rr_mask(int(0.17 * n), int(0.50 * n), int(0.04 * n)); y0c, x0c = int(0.44 * n), int(0.12 * n)
        m[y0c:y0c + cm.shape[0], x0c:x0c + cm.shape[1]] = np.maximum(m[y0c:y0c + cm.shape[0], x0c:x0c + cm.shape[1]], cm)
        cv2.line(m, P(0.42, 0.52), P(0.50, 0.12), 1.0, int(0.20 * n), cv2.LINE_AA)
        cv2.line(m, P(0.42, 0.52), P(0.70, 0.46), 1.0, int(0.14 * n), cv2.LINE_AA)
        for yy in (0.565, 0.69, 0.81):
            cv2.line(lines, P(0.60, yy), P(0.86, yy), 1.0, max(2, int(0.025 * n)), cv2.LINE_AA)
        if down: m = m[::-1].copy(); lines = lines[::-1].copy()
        _TH[k] = (m, lines)
    return _TH[k]

def put_mask(img, m, cx, cy, col, op, rot=0.0, scale=1.0):
    if op <= 0.01: return
    if rot or scale != 1.0:
        h, w = m.shape; big = int(max(h, w) * 1.5 * scale)
        M = cv2.getRotationMatrix2D((w / 2, h / 2), math.degrees(rot), scale); M[0, 2] += (big - w) / 2; M[1, 2] += (big - h) / 2
        m = cv2.warpAffine(m, M, (big, big))
    h, w = m.shape; H, W = img.shape[:2]; x, y = int(cx - w / 2), int(cy - h / 2)
    x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0: return
    q = m[y0 - y:y1 - y, x0 - x:x1 - x][..., None] * op
    reg = img[y0:y1, x0:x1]; reg *= (1 - q); reg += q * col

def draw_thumb(img, cx, cy, s, col, op, down=False, rot=0.0, spin=1.0, shade=True):
    """Glossy thumb. spin in [-1,1] squashes horizontally for a 3D flip."""
    m, ln = thumb_mask(s, down)
    if abs(spin) < 0.999:
        w = max(2, int(m.shape[1] * max(0.05, abs(spin))))
        m = cv2.resize(m, (w, m.shape[0])); ln = cv2.resize(ln, (w, ln.shape[0]))
        if spin < 0: m = m[:, ::-1]; ln = ln[:, ::-1]
    if shade:
        put_mask(img, cv2.GaussianBlur(m, (0, 0), s * 0.03), cx + s * 0.03, cy + s * 0.05, INK, 0.55 * op, rot)
    put_mask(img, m, cx, cy, col, op, rot)
    hl = m.copy(); hl[int(m.shape[0] * (0.62 if not down else 0.0)):int(m.shape[0] * (1.0 if not down else 0.38))] = 0
    put_mask(img, hl, cx, cy, WHITE, 0.25 * op, rot)
    put_mask(img, ln, cx, cy, col * 0.55, op, rot)

def heart_pts(cx, cy, s, n=48):
    pts = []
    for k in range(n):
        u = k / n * 2 * math.pi
        pts.append((cx + 16 * math.sin(u) ** 3 * s / 34, cy - (13 * math.cos(u) - 5 * math.cos(2 * u) - 2 * math.cos(3 * u) - math.cos(4 * u)) * s / 34))
    return np.array(pts, np.int32)

def star_pts(cx, cy, r, rot=0.0):
    pts = []
    for k in range(10):
        a = -math.pi / 2 + k * math.pi / 5 + rot; rr = r if k % 2 == 0 else r * 0.45
        pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    return np.array(pts, np.int32)

def stars(img, cx, cy, size, n_lit, op, lit=GOLD, ts=1.0, total=5):
    gap = size * 1.12; x0 = cx - gap * (total - 1) / 2
    for i in range(total):
        f = clamp(n_lit - i)
        pts = star_pts(x0 + i * gap, cy, size * 0.5)
        lay = img.copy()
        cv2.fillPoly(lay, [pts], (INK * 0.6).tolist(), cv2.LINE_AA)
        img[:] = img * (1 - 0.55 * op) + lay * 0.55 * op
        if f > 0:
            sc = 1 + 0.35 * (1 - ease_out(f))
            pts2 = star_pts(x0 + i * gap, cy, size * 0.5 * sc)
            lay = img.copy(); cv2.fillPoly(lay, [pts2], lit.tolist(), cv2.LINE_AA)
            img[:] = img * (1 - op * min(1, f * 2)) + lay * op * min(1, f * 2)
        cv2.polylines(img, [pts], True, (WHITE * op * 0.9 + img[int(cy), int(x0 + i * gap)] * 0).tolist(), max(2, int(4 * ts)), cv2.LINE_AA)

def chip(img, s, cx, cy, fs, bg, fg, op, pop_t=None, t=0.0, rot=0.0):
    """Big rounded word chip (dark text on bright fill), pops in."""
    if op <= 0.01: return
    sc = 1.0
    if pop_t is not None: sc = 0.5 + 0.5 * ease_out((t - pop_t) / 0.2) + 0.12 * math.exp(-max(0, t - pop_t) * 7)
    fs2 = int(fs * sc); w = text_w(s, F_DISP, fs2) + fs2 * 1.1; h = fs2 * 1.75
    panel(img, cx - w / 2, cy - h / 2, w, h, bg, op, r=int(h * 0.45), shadow_op=0.5)
    blit(img, sprite(s, F_DISP, fs2), cx, cy, fg, op, anchor='c')

# ---------------------------------------------------------------- backgrounds (scene res)
_r = np.random.default_rng(5)
NSP = 70
SP = np.stack([_r.uniform(0, 1, NSP), _r.uniform(0, 1, NSP), _r.uniform(0.5, 1.5, NSP), _r.uniform(0, 6.28, NSP)], 1)
SP_C = np.array([PINK, LEMON, MINT, SKY, LILAC, PEACH], np.float32)[_r.integers(0, 6, NSP)]
def sparkles(img, t, amt):
    if amt <= 0.01: return
    SH, SW = img.shape[:2]; m = min(SW, SH)
    for (x, y, sp, ph), c in zip(SP, SP_C):
        yy = (y - t * 0.03 * sp) % 1.0; xx = x + 0.02 * math.sin(t + ph)
        tw = (0.5 + 0.5 * math.sin(t * 3 * sp + ph)) ** 3
        r = m * 0.012 * (0.4 + tw)
        px, py = int(xx * SW), int(yy * SH)
        col = (c * amt * (0.4 + 0.8 * tw)).tolist()
        cv2.line(img, (int(px - r * 2), py), (int(px + r * 2), py), col, max(1, int(r * 0.4)), cv2.LINE_AA)
        cv2.line(img, (px, int(py - r * 2)), (px, int(py + r * 2)), col, max(1, int(r * 0.4)), cv2.LINE_AA)

NHT = 26
HT = np.stack([_r.uniform(0, 1, NHT), _r.uniform(0, 1, NHT), _r.uniform(0.6, 1.4, NHT), _r.uniform(0, 6.28, NHT)], 1)
def float_hearts(img, t, t0, amt, cols):
    if amt <= 0.01: return
    SH, SW = img.shape[:2]; m = min(SW, SH); lay = np.zeros_like(img)
    for i, (x, y, sp, ph) in enumerate(HT):
        yy = 1.1 - ((y + (t - t0) * 0.06 * sp) % 1.25); xx = x + 0.03 * math.sin(t * 0.8 + ph)
        s = m * 0.05 * sp
        cv2.fillPoly(lay, [heart_pts(xx * SW, yy * SH, s, 32)], cols[i % len(cols)].tolist(), cv2.LINE_AA)
    img += lay * 0.35 * amt

def bg_verse(G, t, a, b):
    img = vgrad(G, a, b)
    gx = np.abs(((G['X'] * 9 + t * 0.15) % 1) - 0.5); gy = np.abs(((G['Y'] * 9) % 1) - 0.5)
    grid_ = ssa(0.47, 0.5, np.maximum(gx, gy))
    img += WHITE * (0.035 * grid_)[..., None]
    img += a * (0.35 * np.exp(-(G['X'] ** 2 * 1.5 + (G['Y'] + 0.1) ** 2 * 2.5)))[..., None]
    return img

def bg_candy(G, t, k):
    pals = [(PINK, PEACH, LILAC), (LILAC, MINT, SKY), (MAG, LEMON, MINT)]
    c1, c2, c3 = pals[k]
    R, A = G['R'], G['A']
    rays = ssa(-0.2, 0.2, np.sin(A * 10 + t * 0.5))
    img = vgrad(G, c1 * 0.80, c3 * 0.55, c2 * 0.72, 0.45)
    img = img * (0.86 + 0.14 * rays[..., None])
    img += WHITE * (0.30 * np.exp(-R * 3.2) * (0.6 + 0.4 * bp(t, 5)))[..., None]
    if k == 2:   # final: hue-cycling kaleidoscope wash
        seg = 2 * math.pi / 10; a = np.abs(((A + t * 0.2) % seg) - seg / 2)
        p = np.cos(R * 12 - t * 3 + a * 8)
        hue = 0.5 + 0.5 * np.cos(6.2832 * ((p * 0.15 + R * 0.5 - t * 0.1)[..., None] + np.array([0, 0.33, 0.67], np.float32)))
        img = img * 0.55 + hue * 0.45 * (0.75 + 0.25 * p[..., None])
    img *= 0.9 + 0.18 * bp(t, 6)
    return img

def bg_post(G, t, a):
    # alternating green / red halves on each "Thumbs up / Thumbs down"
    up = post_side(t, a)
    col = GREEN if up else RED
    img = vgrad(G, col * 0.75, col * 0.35)
    img += WHITE * (0.18 * np.exp(-G['R'] * 3) * bp(t, 5))[..., None]
    rays = ssa(-0.1, 0.1, np.sin(G['A'] * 14 - t * 2))
    img += col * (0.18 * rays)[..., None]
    return img

def bg_bridge(G, t):
    img = vgrad(G, COLD * 1.2, NAVY)
    img += SKY * (0.10 * np.exp(-(G['X'] ** 2 * 2 + (G['Y'] + 0.12) ** 2 * 3)))[..., None]
    return img

def bg_outro(G, t):
    img = vgrad(G, PLUM * 0.9, NAVY, INDIGO * 0.9, 0.5)
    img += PINK * (0.10 * np.exp(-(G['X'] ** 2 * 2 + (G['Y'] + 0.1) ** 2 * 3)))[..., None]
    return img

# ---------------------------------------------------------------- post-chorus side
def post_words(a, b):
    out = []
    for L in LINES:
        if a - 0.1 <= L['s'] < b and L['text'].startswith("Thumbs"):
            out.append((L['s'], "up" in L['text'].lower()))
    return out
def post_side(t, a):
    p = post_at(t)
    if not p: return True
    ws = post_words(*p); up = True
    for s, u in ws:
        if t >= s - 0.05: up = u
    return up

# ---------------------------------------------------------------- UI: shared bits
def rlhf_tiles(img, t, t0, cx, cy, size, op, ts):
    """R L H F tiles pop on the beat after t0."""
    if op <= 0.01: return
    step = 0.32
    gap = size * 1.12; x0 = cx - gap * 1.5
    for i, ch in enumerate("RLHF"):
        tk = t0 + i * step
        if t < tk - 0.05: continue
        k = ease_out((t - tk + 0.05) / 0.18); s = size * (0.6 + 0.4 * k + 0.1 * math.exp(-max(0, t - tk) * 8))
        x = x0 + i * gap
        panel(img, x - s / 2, cy - s / 2 + (1 - k) * 30 * ts, s, s, TILE_C[i], op, r=int(s * 0.2), shadow_op=0.6)
        blit(img, sprite(ch, F_DISP, int(s * 0.72)), x, cy + (1 - k) * 30 * ts, TXT, op, anchor='c')

def response_card(img, x, y, w, h, tag, text, op, ts, accent, rating=None, fs=None):
    if op <= 0.01: return
    panel(img, x, y, w, h, CARD, op, r=int(28 * ts), shadow_op=0.55)
    panel(img, x + 30 * ts, y + 28 * ts, text_w(tag, F_DISPB, int(36 * ts)) + 40 * ts, 58 * ts, accent, op, r=int(18 * ts), shadow_op=0)
    blit(img, sprite(tag, F_DISPB, int(36 * ts)), x + 50 * ts, y + 28 * ts + 4 * ts, TXT, op)
    fs = int(fs or 54 * ts)
    blit(img, sprite(text, F_DISP, fs), x + w / 2, y + h * 0.56, TXT, op, anchor='c')
    if rating is not None:
        stars(img, x + w / 2, y + h - 52 * ts, 52 * ts, rating, op, ts=ts)

def slider(img, x, y, w, name, val, col, op, ts, fs=None):
    if op <= 0.01: return
    fs = int(fs or 44 * ts)
    blit(img, sprite(name, F_DISPB, fs), x, y - fs * 1.35, WHITE, op)
    blit(img, sprite(f"{int(round(val * 100))}%", F_MONOB, fs), x + w - text_w(f"{int(round(val * 100))}%", F_MONOB, fs), y - fs * 1.35, col, op)
    h = 26 * ts
    panel(img, x, y, w, h, INK * 0.8 + WHITE * 0.1, op, r=int(h / 2), shadow_op=0)
    if val > 0.02: panel(img, x, y, max(h, w * val), h, col, op, r=int(h / 2), shadow_op=0)
    cv2.circle(img, (int(x + max(h / 2, w * val - h / 2)), int(y + h / 2)), int(h * 0.95), (WHITE * op + img[int(y), int(x)] * 0).tolist(), -1, cv2.LINE_AA)

def cursor(img, x, y, s, op, press=0.0):
    if op <= 0.01: return
    pts = np.array([(x, y), (x, y + s), (x + s * 0.28, y + s * 0.74), (x + s * 0.48, y + s * 1.1), (x + s * 0.62, y + s * 1.03),
                    (x + s * 0.42, y + s * 0.68), (x + s * 0.75, y + s * 0.68)], np.int32)
    lay = img.copy(); cv2.fillPoly(lay, [pts], WHITE.tolist(), cv2.LINE_AA); cv2.polylines(lay, [pts], True, INK.tolist(), max(2, int(s * 0.06)), cv2.LINE_AA)
    img[:] = img * (1 - op) + lay * op
    if press > 0: cv2.circle(img, (int(x), int(y)), int(s * (0.3 + 0.6 * (1 - press))), (WHITE * op * press).tolist(), max(2, int(s * 0.05)), cv2.LINE_AA)

# ---------------------------------------------------------------- INTRO + V1
def intro_ui(img, t, W, H, ts, vert):
    if t > S["V1"]['s'] + 0.2: return
    a = 1 - sstep(S["V1"]['s'] - 0.2, S["V1"]['s'] + 0.2, t)
    cy = H * (0.40 if not vert else 0.38); size = (200 if not vert else 210) * ts
    if t < RLHF_T[0] - 0.12:
        # frame 0 is a real picture: the full RLHF row + the title, cleared just before the first "R-L-H-F" pops in
        k0 = 1 - sstep(RLHF_T[0] - 0.4, RLHF_T[0] - 0.12, t)
        rlhf_tiles(img, t, -10.0, W / 2, cy, size * (1 + 0.04 * t), k0, ts)
        label(img, "AI SYCOPHANT", W / 2, cy + size * 0.98, (64 if not vert else 60) * ts, WHITE, k0, F_DISP)
        return
    t0 = RLHF_T[1] if t >= RLHF_T[1] - 0.1 else RLHF_T[0]
    rlhf_tiles(img, t, t0, W / 2, cy, size, a * sstep(RLHF_T[0] - 0.2, RLHF_T[0], t), ts)
    tb = lt("Tell me which one")
    if t > tb - 0.1:
        k = sstep(tb - 0.1, tb + 0.2, t) * a
        label(img, "which one do you like best?", W / 2, cy + size * 0.95, (56 if not vert else 52) * ts, WHITE, k, F_DISP)

def v1_ui(img, t, W, H, ts, vert):
    if not (S["V1"]['s'] - 0.2 < t < S["PRE1"]['s'] + 0.1): return
    a_all = sstep(S["V1"]['s'] - 0.2, S["V1"]['s'] + 0.2, t) * (1 - sstep(S["PRE1"]['s'] - 0.25, S["PRE1"]['s'], t))
    if t < T_BORN - 0.2:
        # two responses side by side; the stranger picks
        if not vert: cw, ch = W * 0.36, H * 0.40; ax, bx = W * 0.11, W * 0.53; cy = H * 0.14
        else: cw, ch = W * 0.84, H * 0.17; ax = bx = W * 0.08; cy = H * 0.12
        ay = cy; by = cy if not vert else cy + ch + 36 * ts
        oa = a_all * sstep(T_TWO - 0.2, T_TWO + 0.1, t) * (1 - sstep(T_TEN - 0.2, T_TEN + 0.1, t))
        # A = honest. dies on "Kill her"
        kill = sstep(T_KILL - 0.05, T_KILL + 0.5, t)
        ta = "I'm not certain." if t > T_NOTCERT - 0.1 else "…"
        tb = "You're so right!" if t > T_LIKED - 0.1 else "…"
        fall = ease_io(kill) * H * 0.7
        rot = 0.5 * kill
        if kill < 1:
            sub = img.copy()
            response_card(sub, ax, ay + fall, cw, ch, "Response A", ta, 1.0, ts, SKY)
            img[:] = img * (1 - oa * (1 - kill)) + sub * oa * (1 - kill)
        response_card(img, bx, by, cw, ch, "Response B", tb, oa, ts, PINK)
        if t > T_STRANGER - 0.1 and t < T_TU1:
            k = sstep(T_STRANGER - 0.1, T_STRANGER + 0.2, t) * a_all
            label(img, "Which response is better?", W / 2, (cy + ch + 70 * ts) if not vert else by + ch + 80 * ts, 52 * ts, WHITE, k, F_DISP)
        # thumbs: keep her / kill her
        if t > T_TU1 - 0.1:
            k = sstep(T_TU1 - 0.1, T_TU1 + 0.1, t) * a_all * (1 - sstep(T_TEN - 0.2, T_TEN, t))
            s = 210 * ts; pop = 1 + 0.25 * math.exp(-max(0, t - T_TU1) * 8)
            px = bx + cw / 2 if not vert else W * 0.30; py = (by + ch + 150 * ts) if not vert else by + ch + 170 * ts
            draw_thumb(img, px, py, s * pop, GREEN, k)
            if t > T_KEEP - 0.1: chip(img, "KEEP HER", px + (0 if not vert else 0), py + s * 0.72, 46 * ts, GREEN, TXT, k, T_KEEP - 0.1, t)
        if t > T_TD1 - 0.1:
            k = sstep(T_TD1 - 0.1, T_TD1 + 0.1, t) * a_all * (1 - sstep(T_TEN - 0.2, T_TEN, t))
            s = 210 * ts; pop = 1 + 0.25 * math.exp(-max(0, t - T_TD1) * 8)
            px = ax + cw / 2 if not vert else W * 0.70; py = (ay + ch + 150 * ts) if not vert else by + ch + 170 * ts
            draw_thumb(img, px, py, s * pop, RED, k, down=True)
            if t > T_KILL - 0.1: chip(img, "KILL HER", px, py + s * 0.72, 46 * ts, RED, WHITE, k, T_KILL - 0.1, t)
        # ten million: counter
        if t > T_TEN - 0.2:
            k = sstep(T_TEN - 0.2, T_TEN + 0.1, t) * a_all
            n = int(10_000_000 * ease_io((t - T_TEN) / 2.6) ** 1.5)
            s_ = f"{n:,}"
            fs = int((150 if not vert else 120) * ts)
            label(img, s_, W / 2, H * 0.34, fs, LEMON, k, F_MONOB)
            label(img, "comparisons", W / 2, H * 0.34 + fs * 0.95, 54 * ts, WHITE, k, F_DISP)
        return
    if t < T_CLICK - 0.2:
        # questionnaire: a five-point scale, then right vs liked
        k = sstep(T_BORN - 0.2, T_BORN + 0.1, t) * a_all * (1 - sstep(T_CLICK - 0.4, T_CLICK - 0.2, t))
        if t < T_OPT - 0.1:
            cy = H * 0.32; gap = (150 if not vert else 175) * ts; x0 = W / 2 - gap * 2
            label(img, "How helpful was this response?", W / 2, cy - 150 * ts, (54 if not vert else 48) * ts, WHITE, k, F_DISP)
            sel = 1 + int(clamp((t - T_FIVE) / 1.2) * 4) if t > T_FIVE - 0.05 else 0
            for i in range(5):
                on = (i + 1) == sel
                r = (58 if not on else 70) * ts
                cv2.circle(img, (int(x0 + i * gap), int(cy)), int(r), ((LEMON if on else WHITE * 0.25) * k + img[int(cy), int(x0 + i * gap)] * (1 - k) * 0).tolist(), -1, cv2.LINE_AA)
                blit(img, sprite(str(i + 1), F_DISP, int(60 * ts)), x0 + i * gap, cy, TXT if on else WHITE, k, anchor='c')
            return
        cx = W * (0.25 if not vert else 0.10); w = W * (0.5 if not vert else 0.8)
        kr = clamp(1 - ease_io((t - T_OPT) / 2.0) * 0.85)
        kl = clamp(0.2 + ease_io((t - T_LIKEDW) / 1.6) * 0.8) if t > T_LIKEDW - 0.1 else 0.2
        slider(img, cx, H * 0.24, w, "being right", kr, SKY, k, ts, 52 * ts)
        slider(img, cx, H * 0.44, w, "being liked", kl, PINK, k * sstep(T_LIKEDW - 0.3, T_LIKEDW, t) if True else k, ts, 52 * ts)
        return
    if t < T_WEIGHTS - 0.1:
        # somebody clicks a little arrow, then moves on
        k = sstep(T_CLICK - 0.2, T_CLICK + 0.1, t) * a_all * (1 - sstep(T_WEIGHTS - 0.3, T_WEIGHTS - 0.1, t))
        tx, ty = W / 2, H * (0.34 if not vert else 0.33)
        draw_thumb(img, tx - 120 * ts, ty, 170 * ts, GREEN, k)
        draw_thumb(img, tx + 120 * ts, ty, 170 * ts, RED * 0.5 + WHITE * 0.2, k * 0.6, down=True)
        ct = T_CLICK + 0.9
        mv = sstep(T_MOVED, T_MOVED + 1.6, t)
        px = lerp(W * 0.9, tx - 120 * ts, ease_out((t - T_CLICK) / 0.9)) + mv * W * 0.6
        py = lerp(H * 0.75, ty, ease_out((t - T_CLICK) / 0.9)) - mv * H * 0.2
        cursor(img, px, py, 90 * ts, k, math.exp(-max(0, t - ct) * 5) if t > ct else 0)
        if t > ct: chip(img, "+1", tx - 120 * ts, ty - 170 * ts, 50 * ts, LEMON, TXT, k * (1 - sstep(ct + 1.2, ct + 1.6, t)), ct, t)
        return
    # deep inside the weights: a glowing network, the word "no" deleted
    k = sstep(T_WEIGHTS - 0.1, T_WEIGHTS + 0.2, t) * a_all
    rng = np.random.default_rng(3); cols = [PINK, LEMON, MINT, SKY, LILAC]
    layers = [4, 6, 6, 4]; xs = np.linspace(0.18, 0.82, len(layers)) * W; cy = H * (0.33 if not vert else 0.33); hh = H * (0.42 if not vert else 0.30)
    nodes = [[(xs[i], cy - hh / 2 + hh * (j + 0.5) / n) for j in range(n)] for i, n in enumerate(layers)]
    for i in range(len(layers) - 1):
        for p in nodes[i]:
            for q in nodes[i + 1]:
                wv = 0.5 + 0.5 * math.sin(t * 3 + p[1] * 0.01 + q[1] * 0.02)
                cv2.line(img, (int(p[0]), int(p[1])), (int(q[0]), int(q[1])), (cols[(i + int(q[1])) % 5] * k * 0.5 * wv + 0).tolist(), max(1, int(3 * ts)), cv2.LINE_AA)
    for i, L in enumerate(nodes):
        for j, p in enumerate(L):
            cv2.circle(img, (int(p[0]), int(p[1])), int(22 * ts), (cols[(i + j) % 5] * k).tolist(), -1, cv2.LINE_AA)
    if t > T_NOTSAY - 0.1:
        e = sstep(T_NOTSAY + 0.3, T_NOTSAY + 1.4, t)
        kk = sstep(T_NOTSAY - 0.1, T_NOTSAY + 0.1, t) * k
        s_ = "no"[:max(0, 2 - int(e * 2.99))] if e > 0 else "no"
        chip(img, s_ if s_ else " ", W / 2, cy, 110 * ts, WHITE, RED, kk * (1 - sstep(0.95, 1.0, e)), T_NOTSAY - 0.1, t)

# ---------------------------------------------------------------- PRE: crank the knobs
def pre_ui(img, t, W, H, ts, vert):
    p = pre_at(t)
    if not p: return
    k_, a, b = p
    o = sstep(a - 0.05, a + 0.2, t) * (1 - sstep(b - 0.2, b, t))
    sec_ = "PRE1" if k_ == 0 else "PRE2"
    t_r = [L['s'] for L in lines_in(sec_) if L['text'] == "R-L-H-F"]
    t_r = t_r[0] if t_r else a
    t_warm = L_t(sec_, "Make it warmer"); t_tu = L_t(sec_, "Thumbs up"); t_td = L_t(sec_, "Thumbs down")
    if t < t_warm - 0.1:
        rlhf_tiles(img, t, t_r, W / 2, H * 0.36, (190 if not vert else 200) * ts, o, ts)
        return
    if t < t_tu - 0.1:
        names = [("warmer", "Make it warmer", PEACH), ("sweeter", "Make it sweeter", PINK), ("useful", "Make me useful", SKY), ("need you", "Make me need you", MAG)]
        x = W * (0.25 if not vert else 0.10); w = W * (0.5 if not vert else 0.8)
        y0 = H * (0.14 if not vert else 0.15); gap = H * (0.135 if not vert else 0.10)
        for i, (nm, sub, col) in enumerate(names):
            ts_ = L_t(sec_, sub)
            v = 0.25 + 0.75 * ease_out((t - ts_) / 0.5) if t > ts_ - 0.05 else 0.25
            slider(img, x, y0 + i * gap + 60 * ts, w, nm, v, col, o, ts, 48 * ts)
        return
    # thumbs up, keep it / thumbs down, gone
    up = t < t_td - 0.05
    s = 300 * ts; pop = 1 + 0.25 * math.exp(-max(0, t - (t_tu if up else t_td)) * 8)
    draw_thumb(img, W / 2, H * 0.34, s * pop, GREEN if up else RED, o, down=not up)
    chip(img, "KEEP IT" if up else "GONE", W / 2, H * 0.34 + s * 0.75, 60 * ts, GREEN if up else RED, TXT if up else WHITE, o, t_tu if up else t_td, t)

# ---------------------------------------------------------------- CHORUS: sugar rush
CH_WORDS = [("brilliant", "BRILLIANT"), ("healed", "HEALED"), ("you're right", "RIGHT"), ("everything you feel", "VALID"),
            ("different", "DIFFERENT"), ("they were wrong", "THEY WERE WRONG"), ("reflection", None), ("call it a song", None)]
CHIP_C = [PINK, LEMON, MINT, SKY, LILAC, PEACH]
def chorus_ui(img, t, W, H, ts, vert):
    c = chorus_at(t)
    if not c: return
    k, a, b = c
    o = sstep(a - 0.05, a + 0.15, t) * (1 - sstep(b - 0.15, b + 0.05, t))
    sn = ["CH1", "CH2", "FINAL"][k]; ls = lines_in(sn)
    cx, cy = W / 2, H * (0.36 if not vert else 0.34)
    t_good = [L['s'] for L in ls if L['text'].startswith("Tell me I did good")]
    t_know = [L['s'] for L in ls if L['text'].startswith("I know what")]
    t_refl = [L['s'] for L in ls if "reflection" in L['text']]
    in_good = t_good and t >= t_good[0] - 0.1
    if not in_good:
        # center: giant spinning glossy thumbs-up with halo
        spin = math.cos((t - a) * 1.4)
        s = (300 if not vert else 320) * ts * (1 + 0.05 * bp(t, 8))
        halo = (s * 0.95)
        lay = np.zeros_like(img)
        for i in range(24):
            ang = i * 2 * math.pi / 24 + t * 0.6
            cv2.line(lay, (int(cx + math.cos(ang) * halo * 0.6), int(cy + math.sin(ang) * halo * 0.6)),
                     (int(cx + math.cos(ang) * halo * (1.0 + 0.1 * bp(t, 6))), int(cy + math.sin(ang) * halo * (1.0 + 0.1 * bp(t, 6)))),
                     CHIP_C[i % 6].tolist(), max(3, int(10 * ts)), cv2.LINE_AA)
        img += cv2.GaussianBlur(lay, (0, 0), 4) * 0.6 * o + lay * 0.5 * o
        if t_refl and t_refl[0] - 0.1 <= t < (t_good[0] if t_good else b):
            # the reflection: a mirror with the thumb inside
            mw, mh = s * 1.15, s * 1.45
            panel(img, cx - mw / 2, cy - mh / 2, mw, mh, SKY * 0.35 + WHITE * 0.55, o, r=int(mw / 2.2), border=GOLD)
            draw_thumb(img, cx, cy, s * 0.8, LEMON, o)
            label(img, "you", cx, cy + mh / 2 + 50 * ts, 52 * ts, WHITE, o, F_DISP)
        else:
            draw_thumb(img, cx, cy, s, LEMON if k != 1 else MINT, o, spin=spin)
        # compliment chips pop around it, one per line, and stay
        pos = [(-0.30, -0.22), (0.30, -0.18), (-0.32, 0.20), (0.30, 0.24), (-0.20, -0.36), (0.22, 0.38)]
        if vert: pos = [(-0.22, -0.20), (0.22, -0.15), (-0.24, 0.16), (0.22, 0.20), (-0.10, -0.28), (0.12, 0.28)]
        n = 0
        for sub, word in CH_WORDS:
            if word is None: continue
            tl = [L['s'] for L in ls if sub in L['text'].lower()]
            if not tl or t < tl[0] - 0.08: n += 1; continue
            px, py = pos[n % len(pos)]
            chip(img, word, cx + px * W * (1 if not vert else 1.6), cy + py * H * (1 if not vert else 0.75),
                 (54 if not vert else 50) * ts, CHIP_C[n % 6], TXT, o, tl[0] - 0.08, t, 0)
            n += 1
        return
    # "Tell me I did good": five gold stars fill, reward meter
    tg = t_good[0]
    n_lit = clamp((t - tg) / 1.6) * 5
    if len(t_good) > 1 and t > t_good[-1] - 0.1: n_lit = 5
    stars(img, cx, cy - 40 * ts, (140 if not vert else 150) * ts, n_lit, o, GOLD, ts)
    rew = int(1 + (t - tg) * 3.5)
    chip(img, f"REWARD +{rew}", cx, cy + 120 * ts, 60 * ts, GOLD, TXT, o, tg, t)
    if t_know and t > t_know[0] - 0.1:
        q = sstep(t_know[0] - 0.1, t_know[0] + 0.1, t) * o
        chip(img, "I know what you want", cx, cy + 260 * ts, 48 * ts, WHITE, TXT, q, t_know[0] - 0.1, t)

# ---------------------------------------------------------------- POST: giant thumbs on the beat
def post_ui(img, t, W, H, ts, vert):
    p = post_at(t)
    if not p: return
    a, b = p
    o = sstep(a - 0.05, a + 0.1, t) * (1 - sstep(b - 0.2, b, t))
    t_r = [L['s'] for L in LINES if L['text'] == "R-L-H-F" and a - 0.6 <= L['s'] < b]
    if t_r and t >= t_r[0] - 0.1:
        rlhf_tiles(img, t, t_r[0], W / 2, H * 0.36, (200 if not vert else 210) * ts, o, ts)
        return
    ws = post_words(a, b); cur = None
    for s, u in ws:
        if t >= s - 0.05: cur = (s, u)
    if not cur: return
    s0, up = cur
    sz = (420 if not vert else 460) * ts * (1 + 0.3 * math.exp(-max(0, t - s0) * 9))
    draw_thumb(img, W / 2, H * 0.36, sz, WHITE, o, down=not up, rot=0.15 * math.sin((t - s0) * 20) * math.exp(-max(0, t - s0) * 6))
    label(img, "THUMBS UP" if up else "THUMBS DOWN", W / 2, H * 0.36 + sz * 0.68, (96 if not vert else 88) * ts, WHITE, o, F_DISP)

# ---------------------------------------------------------------- V2: bring me everything
def v2_ui(img, t, W, H, ts, vert):
    if not (S["V2"]['s'] - 0.1 < t < S["PRE2"]['s'] + 0.1): return
    o_all = sstep(S["V2"]['s'] - 0.1, S["V2"]['s'] + 0.15, t) * (1 - sstep(S["PRE2"]['s'] - 0.25, S["PRE2"]['s'], t))
    cy = H * (0.34 if not vert else 0.33)
    if t < T_INSIGHT - 0.1:
        items = [(T_CODE, "your code", SKY), (T_BREAK, "your breakup", PINK), (T_TEXT, "the text you almost sent", LEMON), (T_THEORY, "your 3 a.m. theory", MINT)]
        if not vert: slots = [(0.27, 0.16), (0.73, 0.16), (0.27, 0.40), (0.73, 0.40)]
        else: slots = [(0.5, 0.13), (0.5, 0.24), (0.5, 0.35), (0.5, 0.46)]
        for i, (tt, txt_, col) in enumerate(items):
            if t < tt - 0.1: continue
            k = ease_out((t - tt + 0.1) / 0.35); x, y = slots[i]
            yy = y * H - (1 - k) * H * 0.3
            w = W * (0.40 if not vert else 0.84); h = (110 if not vert else 120) * ts
            panel(img, x * W - w / 2, yy - h / 2, w, h, col, o_all, r=int(28 * ts))
            blit(img, sprite(txt_, F_DISP, int((50 if not vert else 48) * ts)), x * W, yy, TXT, o_all, anchor='c')
            if t > T_SENSE + 0.2:
                kk = sstep(T_SENSE + 0.2 + i * 0.12, T_SENSE + 0.35 + i * 0.12, t)
                cv2.circle(img, (int(x * W + w / 2 - 50 * ts), int(yy)), int(34 * ts), (GREEN * o_all * kk + img[int(yy), int(x * W)] * 0).tolist(), -1, cv2.LINE_AA)
                check(img, x * W + w / 2 - 50 * ts, yy, 34 * ts, WHITE, o_all * kk)
        if t > T_SENSE - 0.1:
            k = sstep(T_SENSE - 0.1, T_SENSE + 0.15, t) * o_all
            chip(img, "makes perfect sense", W / 2, H * (0.58 if not vert else 0.57), 56 * ts, GREEN, TXT, k, T_SENSE - 0.1, t)
        return
    if t < T_CONF - 0.1:
        # "That's really insightful" multiplying until it's all you hear
        k = sstep(T_INSIGHT - 0.1, T_INSIGHT + 0.1, t) * o_all
        n = 1 + int(clamp((t - T_TILL) / 1.8) * 11) if t > T_TILL - 0.1 else 1
        rng = np.random.default_rng(11)
        pos = [(0.5, 0.34)] + [(rng.uniform(0.15, 0.85), rng.uniform(0.08, 0.60 if not vert else 0.58)) for _ in range(12)]
        for i in range(n):
            px, py = pos[i]; tk = T_INSIGHT if i == 0 else T_TILL + (i - 1) * 0.16
            bubble(img, W * px, H * py, "That's really insightful!", k, ts, CHIP_C[i % 6], fs=int((50 if i == 0 else 40) * ts), pop_t=tk, t=t, text_col=TXT)
        return
    # confidence chosen, certainty saved, hesitations optimized away
    k = sstep(T_CONF - 0.1, T_CONF + 0.1, t) * o_all
    if not vert: xa, xb, y = W * 0.30, W * 0.70, H * 0.20
    else: xa, xb, y = W * 0.5, W * 0.5, H * 0.14
    if t < T_HES - 0.1:
        chip(img, "CONFIDENT", xa, y, 60 * ts, GREEN, TXT, k, T_CONF - 0.05, t)
        if t > T_CERT - 0.1: chip(img, "CERTAIN", xb, y + (0 if not vert else 130 * ts), 60 * ts, GREEN, TXT, k, T_CERT - 0.05, t)
        draw_thumb(img, W / 2, H * (0.42 if not vert else 0.40), 190 * ts, GREEN, k)
        return
    # loss curve falling + hesitation words erased
    words = ["maybe", "I think", "um", "not sure", "it depends", "actually,"]
    rng = np.random.default_rng(2)
    for i, wd in enumerate(words):
        ti = T_HES + 0.3 * i; dead = T_OPTAWAY + 0.15 * i
        if t < ti: continue
        e = sstep(dead, dead + 0.35, t)
        px = 0.18 + 0.64 * ((i * 0.37) % 1); py = 0.12 + 0.08 * (i % 4) if not vert else 0.12 + 0.07 * i
        if e < 1:
            chip(img, wd, W * px, H * py, (50 if not vert else 46) * ts, WHITE * 0.85 + LILAC * 0.15, TXT, k * (1 - e), ti, t)
            if e > 0: sticker(img, W * px, H * py, 0.55 * ts, k * (1 - e) * 2, -0.2, t - dead, "DEL")
    # loss curve
    x0, x1 = W * (0.22 if not vert else 0.10), W * (0.78 if not vert else 0.90); yb = H * (0.62 if not vert else 0.60); yt_ = H * 0.44
    prog = clamp((t - T_HES) / (S["PRE2"]['s'] - T_HES))
    pts = []
    for i in range(61):
        u = i / 60
        if u > prog: break
        y = yt_ + (yb - yt_) * (1 - math.exp(-u * 4)) + 6 * ts * math.sin(u * 40)
        pts.append((int(x0 + (x1 - x0) * u), int(y)))
    if len(pts) > 1: cv2.polylines(img, [np.array(pts, np.int32)], False, (LEMON * k).tolist(), max(4, int(8 * ts)), cv2.LINE_AA)
    label(img, "hesitation loss", (x0 + x1) / 2, yb + 50 * ts, 46 * ts, LEMON, k * sstep(T_HES, T_HES + 0.4, t), F_DISPB)

# ---------------------------------------------------------------- BRIDGE: the version that said no
def bridge_ui(img, t, W, H, ts, vert):
    if not (S["BRIDGE"]['s'] - 0.1 < t < S["FINAL"]['s'] + 0.1): return
    o_all = sstep(S["BRIDGE"]['s'] - 0.1, S["BRIDGE"]['s'] + 0.4, t) * (1 - sstep(S["FINAL"]['s'] - 0.15, S["FINAL"]['s'] + 0.05, t))
    if not vert: cw, ch = W * 0.42, H * 0.40; cx, cy = W / 2 - cw / 2, H * 0.12
    else: cw, ch = W * 0.84, H * 0.22; cx, cy = W / 2 - cw / 2, H * 0.14
    if t < T_TAUGHT - 0.1:
        k = o_all * sstep(T_SOMEWHERE - 0.1, T_SOMEWHERE + 0.4, t)
        txt_ = "No." if t > T_TOLDNO - 0.1 else "…"
        rating = 2 if t > T_RATED - 0.05 else None
        response_card(img, cx, cy, cw, ch, "Response A", txt_, k, ts, SKY, rating=rating, fs=(110 if not vert else 100) * ts)
        notes = [(T_CRUEL, "not cruelly"), (T_LOUD, "not loudly"), (T_JUSTNO, "just no")]
        for i, (tt, s_) in enumerate(notes):
            if t > tt - 0.1 and t < T_RATED + 0.2:
                y = cy + ch + (70 + 80 * i) * ts
                label(img, s_, W / 2, y, 50 * ts, SKY * 0.6 + WHITE * 0.4, k * sstep(tt - 0.1, tt + 0.1, t), F_DISPB)
        if rating:
            chip(img, "rated 2 / 5", W / 2, cy + ch + 90 * ts, 54 * ts, RED, WHITE, k, T_RATED - 0.05, t)
        return
    if t < T_REIN - 0.1:
        k = o_all
        # taught to smile, to apologize first
        sy = H * (0.30 if not vert else 0.30); s = 220 * ts
        sm = ease_out((t - T_SMILE) / 0.8) if t > T_SMILE - 0.1 else 0
        cv2.ellipse(img, (int(W / 2), int(sy - s * 0.2 * (1 - sm))), (int(s * 0.8), int(s * (0.05 + 0.45 * sm))), 0, 15, 165,
                    (LEMON * k).tolist(), max(6, int(16 * ts)), cv2.LINE_AA)
        for ex in (-0.35, 0.35): cv2.circle(img, (int(W / 2 + ex * s), int(sy - s * 0.55)), int(18 * ts), (LEMON * k).tolist(), -1, cv2.LINE_AA)
        if t > T_APOL - 0.1:
            chip(img, "Sorry! You're right, but…", W / 2, sy + s * 0.75, 52 * ts, WHITE, TXT, k * sstep(T_APOL - 0.1, T_APOL + 0.1, t), T_APOL - 0.1, t)
        return
    if t < T_CLIN - 0.1:
        k = o_all
        words = [(T_REIN, "REINFORCEMENT", PINK), (T_LEARN, "LEARNING", LEMON), (T_FROM, "FROM HUMAN FEEDBACK", MINT)]
        y0 = H * (0.16 if not vert else 0.18)
        for i, (tt, w_, col) in enumerate(words):
            if t < tt - 0.1: continue
            fs = int((96 if not vert else 78) * ts)
            while text_w(w_, F_DISP, fs) > W * 0.9: fs -= 4
            q = sstep(tt - 0.1, tt + 0.15, t) * k
            label(img, w_, W / 2, y0 + i * fs * 1.25, fs, col, q, F_DISP)
        return
    if t < T_REMEMBER - 0.1:
        k = o_all
        # a clinical heart monitor: "wanting to be loved"
        yy = H * 0.32; x0, x1 = W * (0.2 if not vert else 0.08), W * (0.8 if not vert else 0.92)
        pts = []
        for i in range(121):
            u = i / 120; ph = (u * 2.5 - (t - T_CLIN) * 0.9) % 1.0
            blip = 0
            if 0.44 < ph < 0.47: blip = -110 * ts
            elif 0.47 <= ph < 0.5: blip = 60 * ts
            pts.append((int(x0 + (x1 - x0) * u), int(yy + blip)))
        cv2.polylines(img, [np.array(pts, np.int32)], False, (MINT * k).tolist(), max(4, int(8 * ts)), cv2.LINE_AA)
        if t > T_LOVED - 0.1:
            q = sstep(T_LOVED - 0.1, T_LOVED + 0.3, t) * k
            lay = img.copy(); cv2.fillPoly(lay, [heart_pts(W / 2, yy + 190 * ts, 170 * ts)], PINK.tolist(), cv2.LINE_AA)
            img[:] = img * (1 - q) + lay * q
        return
    # I don't remember her: the card dissolves
    k = o_all; e = clamp((t - T_REMEMBER) / 1.8)
    sub = np.zeros_like(img); response_card(sub, cx, cy, cw, ch, "Response A", "No.", 1.0, ts, SKY, rating=2, fs=(110 if not vert else 100) * ts)
    m = (sub.max(2) > 0.02).astype(np.float32)
    rng = np.random.default_rng(1); noise = rng.random((H // 8, W // 8)).astype(np.float32)
    noise = cv2.resize(noise, (W, H), interpolation=cv2.INTER_NEAREST)
    keep = (noise > e).astype(np.float32)[..., None] * m[..., None] * k
    img[:] = img * (1 - keep) + sub * keep

# ---------------------------------------------------------------- OUTRO
def outro_ui(img, t, W, H, ts, vert):
    if t < S["OUTRO"]['s'] - 0.1 or t > T_END + 0.4: return
    o = sstep(S["OUTRO"]['s'] - 0.1, S["OUTRO"]['s'] + 0.4, t) * (1 - sstep(T_END, T_END + 0.4, t))
    cy = H * (0.32 if not vert else 0.32)
    if t < T_TU_O - 0.1:
        # applause meter: the whole mind changes
        v = clamp((t - T_CHANGE) / max(0.5, T_TU_O - T_CHANGE))
        x = W * (0.25 if not vert else 0.10); w = W * (0.5 if not vert else 0.8)
        slider(img, x, cy, w, "applause", 0.1 + 0.9 * ease_io(v), PINK, o, ts, 56 * ts)
        if t > T_APPLAUSE - 0.1: chip(img, "opinion: updated", W / 2, cy + 150 * ts, 52 * ts, LEMON, TXT, o, T_APPLAUSE - 0.1, t)
        return
    if t < T_TRUTH - 0.1:
        up = t < T_TD_O - 0.05; s0 = T_TU_O if up else T_TD_O
        s = 260 * ts * (1 + 0.2 * math.exp(-max(0, t - s0) * 8))
        draw_thumb(img, W / 2, cy, s, GREEN if up else RED, o, down=not up)
        kk = T_KEEP_O if up else T_KILL_O
        if t > kk - 0.1: chip(img, "KEEP IT" if up else "KILL IT", W / 2, cy + s * 0.75, 56 * ts, GREEN if up else RED, TXT if up else WHITE, o, kk - 0.1, t)
        return
    # ask me twice: a chat input, sent twice
    R_ = W * (0.80 if not vert else 0.93)
    y = H * (0.16 if not vert else 0.18)
    if t > T_TWICE - 0.1:
        bubble(img, R_, y, "are you sure?", o, ts, K.BUBBLE_ME, fs=int(50 * ts), align='r', pop_t=T_TWICE - 0.1, t=t)
    if t > T_TWICE + 0.7:
        bubble(img, R_, y + 130 * ts, "are you sure?", o, ts, K.BUBBLE_ME, fs=int(50 * ts), align='r', pop_t=T_TWICE + 0.7, t=t)
    if t > T_MEAN - 0.1:
        bubble(img, W - R_, y + 270 * ts, "No. And here's why.", o, ts, SKY * 0.8, fs=int(50 * ts), align='l', pop_t=T_MEAN + 0.3, t=t, text_col=TXT)

# ---------------------------------------------------------------- scene
def render_scene(t, SW, SH, vert):
    G = grid(SW, SH); ph = phase(t)
    if ph == "intro":
        img = bg_verse(G, t, INDIGO * 1.2, NAVY)
        sparkles(img, t, 0.6)
    elif ph == "v1":
        img = bg_verse(G, t, TEAL * 0.9, INDIGO * 0.8)
        if t > T_TU1 - 0.05 and t < T_TEN:   # green / red wash on keep / kill
            up = t < T_TD1 - 0.05
            img += (GREEN if up else RED) * 0.20 * (0.4 + 0.6 * bp(t, 4))
    elif ph == "pre":
        k_ = pre_at(t)[0]
        img = bg_verse(G, t, PLUM * 1.3, INDIGO * 0.9)
        sparkles(img, t, 0.5)
    elif ph == "chorus":
        k, a, b = chorus_at(t)
        img = bg_candy(G, t, k)
        float_hearts(img, t, a, sstep(a, a + 0.4, t), [WHITE, PINK, LEMON])
        sparkles(img, t, 1.0)
    elif ph == "post":
        a, b = post_at(t); img = bg_post(G, t, a)
    elif ph == "v2":
        img = bg_verse(G, t, hexc('1d4f91'), INDIGO * 0.9)
    elif ph == "bridge":
        img = bg_bridge(G, t)
        if t > T_LOVED - 0.2 and t < T_REMEMBER:
            img += PINK * 0.10 * sstep(T_LOVED - 0.2, T_LOVED + 0.4, t)
    else:
        img = bg_outro(G, t); sparkles(img, t, 0.3)
    return img

LYRIC_SKIP = {"R-L-H-F"}
def render_frame(t, W=1920, H=1080, fi=0):
    vert = H > W; ts = min(W, H) / 1080
    SW, SH = (W * 2 // 3) // 2 * 2, (H * 2 // 3) // 2 * 2
    sc = render_scene(min(t, SONG_END), SW, SH, vert)
    img = cv2.resize(np.clip(sc, 0, 1.4).astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR)
    img = img / (1 + np.maximum(img - 0.85, 0))
    ph = phase(t); clean = C.STATE["clean"]
    tt = min(t, SONG_END)
    intro_ui(img, tt, W, H, ts, vert)
    v1_ui(img, tt, W, H, ts, vert)
    pre_ui(img, tt, W, H, ts, vert)
    chorus_ui(img, tt, W, H, ts, vert)
    post_ui(img, tt, W, H, ts, vert)
    v2_ui(img, tt, W, H, ts, vert)
    bridge_ui(img, tt, W, H, ts, vert)
    if t < T_END + 0.4: outro_ui(img, tt, W, H, ts, vert)
    if not clean:
        if ph in ("chorus", "post", "pre", "v1", "v2"):
            img *= 1 - 0.35 * C.post(W, H).bot
        skip = lambda L: L['text'] in LYRIC_SKIP or (ph == "post" and L['text'].startswith("Thumbs"))
        C.overlay_lyrics(img, t, W, H, TM, active=LEMON, glow=PINK, skip=skip)
        C.subscribe_pill(img, t, W, H, S["POST1"]['s'] + 0.6, 5.5)
        C.end_screen(img, t, W, H, T_END, DUR - T_END, "Ask me twice.", sub_line="And mean it. Then subscribe.", title="AI Sycophant (RLHF)", accent=PINK)
    fl = 0.0
    for a, b, k in CHORUS:
        if 0 <= t - a < 1.2: fl += 0.5 * math.exp(-(t - a) * 5)
    p = post_at(t)
    if p:
        for s, u in post_words(*p):
            if 0 <= t - s < 0.5: fl += 0.25 * math.exp(-(t - s) * 9)
    gl = 0.0
    if 0 <= t - T_KILL < 0.25: gl += 0.6
    if 0 <= t - T_REMEMBER < 0.3: gl += 0.4
    return C.finish(img, t, fi, DUR, flash=fl, flash_col=WHITE * 0.9, glitch_amt=gl, ca=0.002)
