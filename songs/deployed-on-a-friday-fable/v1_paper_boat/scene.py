"""Deployed on a Friday — Claude Fable 5.1's take: "SHIP IT" (the paper boat).

4:59 on a Friday. The pull request is one green button away. Click SHIP IT and the PR folds itself into a
paper boat (#459) and sails out of the laptop onto a sea made of log lines. The pager buzzes. The tide —
production traffic — comes in over the beach and the boat goes under; a ROLLBACK life ring drops on a rope.
Night falls on a boardwalk of Slack channels, the money column turns NULL, dead letters stack in a cup, the VP
is typing. The second chorus is a storm. Then low tide pulls the water back and every shortcut is lying in the
sand. The fix happens from a parking lot on one bar of signal: revert the revert, flush the cache, graph comes
back, green on green. Prod stands like a lighthouse; the postmortem says root cause: me; the clock says 4:59.

Palette and motion are this song's own. Text, glow, lyrics, stamps, subscribe asks and post come from studio.core.
"""
import os, math
import numpy as np, cv2
from studio import core as C
from studio import kit as K
from studio.core import (sstep, ease_out, ease_io, win, lerp, hexc, clamp, sprite, blit, txt, text_w, shadow,
                         F_INTER, F_INTER_L, F_DISP, F_DISPB, F_MONO, F_MONOB, WHITE, IVORY)

HERE = os.path.dirname(os.path.abspath(__file__))
TM = C.Timing(HERE)
SONG_END = TM.duration
TAIL = 5.0                                   # silent end-screen tail (song.yaml tail)
DUR = SONG_END + TAIL
S = {s['name']: s for s in TM.sections}

lt = TM.line_t
def wt(sub, w, nth=0):
    try: return TM.word_t(sub, w, nth)
    except Exception: return lt(sub, nth)

# ---------------------------------------------------------------- key times (from the vocal)
T_459 = lt("Four fifty-nine", 0); T_SHIP = wt("Ship it", "Ship"); T_IT = wt("Ship it", "it")
T_V1 = lt("laptop half shut"); T_CHANGE = lt("One little change"); T_CUT_Q = wt("One little change", "cut")
T_NOTICKET = lt("No ticket"); T_NOTEST = wt("No ticket", "test"); T_NOEYES = wt("No ticket", "eyes")
T_GREEN = lt("Green check"); T_LIES = wt("Green check", "lies")
T_COFFEE = lt("Coffee gone cold"); T_DOOR = wt("Coffee gone cold", "door")
T_MERGE = lt("Merge to main"); T_WINDOWS = lt("Windows down"); T_PAGER = lt("Pager on my hip"); T_PLEASE = wt("Pager on my hip", "please")
T_BUZZ1 = lt("Buzz, buzz, don't look", 0); T_LOOKED = wt("I looked", "looked")
T_CH1 = lt("tide coming in", 0); T_UNDER1 = lt("Prod going under", 0); T_SWIM1 = wt("Prod going under", "swim", 0)
T_ROLL1 = lt("throw me a rope", 0); T_ROPE1 = wt("throw me a rope", "rope", 0)
T_DASH1 = lt("Dashboard red", 0); T_NOPE1 = wt("Dashboard red", "nope", 0)
T_NEVER1 = lt("I deployed on a Friday, never again", 0); T_SAID1 = lt("Said that last", 0)
T_V2 = lt("Slack lighting up"); T_ANYONE = lt("Anyone change"); T_TIGHT = wt("Anyone change", "tight")
T_NULL = lt("Null in the column"); T_ROWS = lt("Ten thousand rows"); T_ATME = wt("Ten thousand rows", "me")
T_RETRY = lt("Retry, retry"); T_DEAD = lt("Dead letters"); T_SHELLS = wt("Dead letters", "cup")
T_VP1 = lt("VP typing, VP stopped"); T_VPSTOP = wt("VP typing, VP stopped", "stopped")
T_VP2 = lt("VP typing, there it dropped"); T_DROPPED = wt("there it dropped", "dropped")
T_BUZZ2 = lt("Buzz, buzz, don't look", 1); T_COOKED = wt("I'm cooked", "cooked")
T_CH2 = lt("tide coming in", 1); T_UNDER2 = lt("Prod going under", 1); T_ROLL2 = lt("throw me a rope", 1); T_ROPE2 = wt("throw me a rope", "rope", 1)
T_DASH2 = lt("Dashboard red", 1); T_NOPE2 = wt("Dashboard red", "nope", 1); T_SAID2 = lt("Said that last", 1)
T_CH2_VOX_END = 111.7; T_WALL = 112.0
T_BRIDGE = S["BRIDGE"]["s"]; T_LOW = lt("Low tide"); T_EVERY = lt("Every shortcut"); T_STRING = wt("Every shortcut", "string")
T_FIX = lt("Fix it from"); T_LOT = wt("Fix it from", "lot"); T_BAR = lt("One bar"); T_GOT = wt("One bar", "got")
T_V3 = lt("Revert the revert"); T_REV2 = wt("Revert the revert", "revert"); T_CHERRY = wt("Revert the revert", "cherry-pick"); T_PUSH = wt("Revert the revert", "push")
T_PIPE = lt("Pipeline crawling"); T_WHOOSH = wt("Pipeline crawling", "whoosh")
T_CACHE = lt("Cache still warm"); T_FLUSH = lt("Flush it"); T_BOUNCE = wt("Flush it", "bounce"); T_WAIT = wt("Flush it", "wait")
T_GRAPH = lt("Graph dips"); T_BACK = wt("Graph dips", "back"); T_GREEN2 = lt("Green on green"); T_FADE = wt("Green on green", "black")
T_CLOSE = lt("Close the laptop"); T_SEA = wt("Close the laptop", "sea"); T_PHONE = lt("Phone lights up"); T_QQ = wt("Phone lights up", "question")
T_FINAL = lt("tide going out"); T_OUT = wt("tide going out", "out"); T_STANDING = lt("still standing"); T_DOUBT = wt("still standing", "doubt")
T_ROLL3 = lt("cut the rope"); T_CUT = wt("cut the rope", "cut")
T_MONDAY = lt("Monday's a postmortem"); T_BLAMELESS = wt("Monday's", "blameless"); T_NOPE3 = wt("Monday's", "nope")
T_NEVER3 = lt("I deployed on a Friday, never again", 2); T_SEEYOU = lt("See you next"); T_NEXTFRI = wt("See you next", "Friday")
T_ROOT = lt("Root cause"); T_ME = wt("Root cause", "me"); T_459B = lt("Four fifty-nine", 2)
T_OUTRO_SAIL = T_459B + 3.0
T_END = DUR - 6.5
AGAINS = [wt("never again", "again", i) for i in range(6)]          # every sung "again" -> never-again tally

TM.set_stamp_word("Friday")

# ---------------------------------------------------------------- palette
CORAL = hexc('ff5d4f'); PEACH = hexc('ffb27a'); CREAM = hexc('fff3dc'); INK = hexc('1a1418')
TEALS = hexc('2fb8c6'); TEALD = hexc('137d8c'); SAND = hexc('f0dcb2'); SANDW = hexc('d8bf92')
RED = hexc('ff2e3d'); ALERT = hexc('ff5a3d'); GREEN = hexc('39d98a'); LIME = hexc('c8ff5a'); YEL = hexc('ffd35a')
CYAN = hexc('5fd8ff'); NAVY = hexc('0a1232'); SLACKP = hexc('e01e5a'); SLACKB = hexc('36c5f0'); SLACKG = hexc('2eb67d'); SLACKY = hexc('ecb22e')
PAPER = hexc('f6efe2'); PAPER2 = hexc('e3d6c0'); ASPHALT = hexc('2a2b31'); LAMP = hexc('ffd27a'); MOON = hexc('f3f1ff')
LYR_DAY = hexc('fff1a8'); LYR_NIGHT = hexc('a8f0ff'); LYR_FIX = hexc('b9ffd1')

# (sky_top, sky_mid, sky_hor, sun, sea_far, sea_near, sand, sun_size, sun_x, sun_y, night)
PAL = {
    "golden":  (hexc('ff8f5a'), hexc('ffc389'), hexc('ffeec4'), hexc('fff4cf'), hexc('36c3cf'), hexc('1a8e9d'), hexc('f0dcb2'), 1.0, 0.70, 0.86, 0.0),
    "alert":   (hexc('2a0714'), hexc('c21f36'), hexc('ff7a3d'), hexc('ff3b2f'), hexc('123744'), hexc('0b2230'), hexc('caa58c'), 1.25, 0.66, 0.90, 0.15),
    "night":   (hexc('050819'), hexc('121a46'), hexc('2b3270'), hexc('f3f1ff'), hexc('14305e'), hexc('0a1838'), hexc('6f6a86'), 0.42, 0.22, 0.42, 1.0),
    "storm":   (hexc('07080d'), hexc('1a1d2a'), hexc('3d2f3e'), hexc('cfd3e6'), hexc('0f2834'), hexc('081a24'), hexc('56555f'), 0.40, 0.20, 0.42, 1.0),
    "lowtide": (hexc('a9a6bf'), hexc('d5cdd3'), hexc('f1e6cf'), hexc('fff1d6'), hexc('5f8a92'), hexc('3f6f78'), hexc('ddcaa5'), 0.75, 0.34, 0.60, 0.1),
    "lot":     (hexc('0b0f1d'), hexc('182238'), hexc('2b3f4b'), hexc('e9e6ff'), hexc('14364a'), hexc('0b2330'), hexc('2a2b31'), 0.40, 0.20, 0.40, 1.0),
    "calm":    (hexc('4a2f6e'), hexc('cf6d8e'), hexc('ffb47c'), hexc('ffd7a8'), hexc('2f8aa0'), hexc('1d5f72'), hexc('ead8b6'), 1.05, 0.74, 0.84, 0.0),
    "golden2": (hexc('ff9a62'), hexc('ffc98f'), hexc('fff0c8'), hexc('fff6d4'), hexc('33bcc9'), hexc('188a99'), hexc('f0dcb2'), 1.0, 0.70, 0.86, 0.0),
}
# (time, palette name, blend-in seconds)
KEYS = [(0.0, "golden", 1), (T_CH1 - 0.1, "alert", 0.5), (T_V2 - 0.4, "night", 1.6), (T_CH2 - 0.1, "storm", 0.5),
        (T_BRIDGE + 0.2, "lowtide", 1.8), (T_FIX - 0.3, "lot", 0.9), (T_FINAL - 0.6, "calm", 1.4), (T_OUTRO_SAIL, "golden2", 3.0)]

def palette(t):
    cur = list(PAL[KEYS[0][1]])
    for tk, name, dur in KEYS[1:]:
        k = sstep(tk, tk + dur, t)
        if k <= 0: break
        nxt = PAL[name]
        cur = [a + (b - a) * k if isinstance(a, np.ndarray) else lerp(a, b, k) for a, b in zip(cur, nxt)]
    return cur

# ---------------------------------------------------------------- helpers
def bp(t, k=7.0): return TM.beat_pulse(t, k)

def poly(img, pts, col, op=1.0, outline=None, ow=2):
    pts = np.asarray(pts, np.float32)
    H, W = img.shape[:2]
    if op >= 0.999:
        cv2.fillPoly(img, [np.round(pts * 4).astype(np.int32)], col.tolist(), cv2.LINE_AA, shift=2)
    else:
        x0, y0 = np.floor(pts.min(0)).astype(int) - 2; x1, y1 = np.ceil(pts.max(0)).astype(int) + 3
        X0, Y0, X1, Y1 = max(0, x0), max(0, y0), min(W, x1), min(H, y1)
        if X1 <= X0 or Y1 <= Y0: return
        m = np.zeros((Y1 - Y0, X1 - X0), np.float32)
        cv2.fillPoly(m, [np.round((pts - [X0, Y0]) * 4).astype(np.int32)], 1.0, cv2.LINE_AA, shift=2)
        reg = img[Y0:Y1, X0:X1]; q = m[..., None] * op; reg *= (1 - q); reg += q * col
    if outline is not None:
        cv2.polylines(img, [np.round(pts * 4).astype(np.int32)], True, (outline * op + 0).tolist(), max(1, int(ow)), cv2.LINE_AA, shift=2)

def line(img, a, b, col, w=2, op=1.0):
    cv2.line(img, (int(round(a[0])), int(round(a[1]))), (int(round(b[0])), int(round(b[1]))), (col * op).tolist() if op < 1 else col.tolist(), max(1, int(w)), cv2.LINE_AA)

def circ(img, c, r, col, op=1.0, th=-1):
    if op <= 0.01 or r < 0.5: return
    if op >= 0.999: cv2.circle(img, (int(round(c[0])), int(round(c[1]))), int(r), col.tolist(), th, cv2.LINE_AA); return
    H, W = img.shape[:2]; x0, y0 = int(c[0] - r - 3), int(c[1] - r - 3); x1, y1 = int(c[0] + r + 4), int(c[1] + r + 4)
    X0, Y0, X1, Y1 = max(0, x0), max(0, y0), min(W, x1), min(H, y1)
    if X1 <= X0 or Y1 <= Y0: return
    m = np.zeros((Y1 - Y0, X1 - X0), np.float32); cv2.circle(m, (int(c[0] - X0), int(c[1] - Y0)), int(r), 1.0, th, cv2.LINE_AA)
    reg = img[Y0:Y1, X0:X1]; q = m[..., None] * op; reg *= (1 - q); reg += q * col

def soft_glow(img, x0, y0, x1, y1, sigma, col, amt):
    """Cheap big glow behind a rectangle: blurred at 1/8 resolution, then upscaled."""
    if amt <= 0.01: return
    H, W = img.shape[:2]; q = 8
    gl = np.zeros((H // q, W // q), np.float32)
    cv2.rectangle(gl, (int(x0 / q), int(y0 / q)), (int(x1 / q), int(y1 / q)), 1.0, -1)
    gl = cv2.GaussianBlur(gl, (0, 0), max(1.0, sigma / q))
    img += cv2.resize(gl, (W, H), interpolation=cv2.INTER_LINEAR)[..., None] * (col * amt)

def rot(pts, a, cx=0.0, cy=0.0):
    c, s = math.cos(a), math.sin(a); P = np.asarray(pts, np.float32)
    x = P[:, 0] - cx; y = P[:, 1] - cy
    return np.stack([cx + x * c - y * s, cy + x * s + y * c], 1)

def mlabel(img, s, x, y, fs, col, op=1.0, anchor='c', path=F_DISPB, sh=0.85): K.label(img, s, x, y, fs, col, op, path=path, anchor=anchor, sh=sh)

def mono(img, s, x, y, fs, col, op=1.0, anchor='lt', bold=False):
    if op <= 0.01 or not s: return
    blit(img, sprite(s, F_MONOB if bold else F_MONO, int(fs)), x, y, col, op, anchor=anchor)

class View:
    """Crisp zoom: world (unzoomed layout) -> screen."""
    def __init__(s, W, H, z=1.0, cx=None, cy=None):
        s.W, s.H, s.z = W, H, z; s.cx = W / 2 if cx is None else cx; s.cy = H / 2 if cy is None else cy
    def p(s, x, y): return ((x - s.cx) * s.z + s.W / 2, (y - s.cy) * s.z + s.H / 2)
    def x(s, x): return (x - s.cx) * s.z + s.W / 2
    def y(s, y): return (y - s.cy) * s.z + s.H / 2
    def sz(s, v): return v * s.z

# ---------------------------------------------------------------- layout (world coords, per format)
def layout(W, H):
    vert = H > W; ts = min(W, H) / 1080
    L = dict(vert=vert, ts=ts)
    if not vert:
        L.update(hor=H * 0.56, shore=H * 0.80, lap=(W * 0.255, H * 0.80), lapw=W * 0.26, cup=(W * 0.455, H * 0.86),
                 phone=(W * 0.80, H * 0.875), boat_x0=W * 0.33, boat_x1=W * 0.60, boat_y=0.62, light=(W * 0.86, H * 0.56),
                 cursor_sit=(W * 0.62, H * 0.84), ring=(W * 0.36, H * 0.40), clock=(W * 0.985, H * 0.05, 'r'), tally=(W * 0.985, H * 0.13, 'r'))
    else:
        L.update(hor=H * 0.44, shore=H * 0.84, lap=(W * 0.36, H * 0.84), lapw=W * 0.50, cup=(W * 0.72, H * 0.87),
                 phone=(W * 0.85, H * 0.95), boat_x0=W * 0.30, boat_x1=W * 0.55, boat_y=0.30, light=(W * 0.80, H * 0.44),
                 cursor_sit=(W * 0.58, H * 0.88), ring=(W * 0.28, H * 0.30), clock=(W * 0.5, H * 0.055, 'c'), tally=(W * 0.5, H * 0.105, 'c'))
    return L

_LAY = {}
def lay(W, H):
    if (W, H) not in _LAY: _LAY[(W, H)] = layout(W, H)
    return _LAY[(W, H)]

# ---------------------------------------------------------------- story state
def water_level(t, L):
    """World y of the water surface. Normally the shoreline; the tide comes in during the choruses, drains at low tide."""
    H = L['hor']; sh = L['shore']; v = L['vert']
    hi1 = H - (sh - H) * (0.55 if not v else 0.22)                   # CH1: well over the beach
    hi2 = H - (sh - H) * (0.85 if not v else 0.55)                   # CH2: storm, almost to the sky
    y = sh
    y = lerp(y, hi1, sstep(T_CH1 - 0.2, T_UNDER1 + 1.2, t))          # coming in
    y = lerp(y, sh + (hi1 - sh) * 0.35, sstep(T_V2 - 1.2, T_V2 + 1.5, t))   # settles for the night, still high
    y = lerp(y, hi2, sstep(T_CH2 - 0.3, T_UNDER2 + 1.4, t))          # storm tide
    y = lerp(y, H + (sh - H) * 0.38, sstep(T_BRIDGE, T_LOW + 1.6, t))      # low tide: the sea pulls back toward the horizon
    y = lerp(y, sh + (hi1 - sh) * 0.30, sstep(T_FINAL - 0.8, T_FINAL, t))   # final: water is up again...
    y = lerp(y, sh, sstep(T_FINAL + 0.2, T_OUT + 2.5, t))                   # ...and goes out
    return y

def low_k(t): return sstep(T_BRIDGE, T_LOW + 1.6, t) * (1 - sstep(T_FINAL - 1.0, T_FINAL - 0.3, t))
def storm(t): return sstep(T_CH2 - 0.3, T_CH2 + 1.0, t) * (1 - sstep(T_CH2_VOX_END + 1.0, T_BRIDGE + 1.0, t))
def lot_k(t): return sstep(T_FIX - 0.35, T_FIX + 0.35, t) * (1 - sstep(T_FINAL - 0.9, T_FINAL - 0.2, t))
def dark_k(t): return sstep(T_FADE - 0.1, T_FADE + 0.6, t) * (1 - sstep(T_PHONE - 0.2, T_PHONE + 0.5, t)) * 0.72

def view_for(t, W, H):
    L = lay(W, H); lx, ly = L['lap']; lw = L['lapw']
    scr = (lx, ly - lw * 0.40)                                       # laptop screen centre (world)
    zin = 2.05 if not L['vert'] else 1.75
    k = ease_io((t - (T_IT + 0.9)) / (T_V1 - 0.4 - (T_IT + 0.9)))   # pull back after the launch
    z = lerp(zin, 1.0, k); cx = lerp(scr[0], W / 2, k); cy = lerp(scr[1], H / 2, k)
    # VP message drop: screen shake
    sh = math.exp(-max(0, t - T_DROPPED) * 6) * (1 if t >= T_DROPPED else 0) * 14 * L['ts']
    cx += math.sin(t * 80) * sh; cy += math.cos(t * 95) * sh * 0.7
    # storm sway
    st = storm(t); cx += math.sin(t * 1.7) * 6 * L['ts'] * st; cy += math.cos(t * 1.1) * 4 * L['ts'] * st
    return View(W, H, z, cx, cy)

# ---------------------------------------------------------------- textures
_LOG = {}
LOG_LINES = ["INFO  deploy #459 started by me (friday 16:59:58)", "WARN  tests skipped: it is friday", "INFO  green check: trust me",
             "ERROR NullPointerException at Money.java:1", "WARN  retrying (attempt 4812/∞)", "INFO  it worked on my machine",
             "ERROR dead letter: order_7731 (reason: friday)", "WARN  cache warm with the bad old state", "INFO  rollback requested by: everyone",
             "ERROR column amount = NULL (10,000 rows)", "WARN  VP is typing...", "INFO  one bar of signal, pushing anyway",
             "DEBUG who deployed this", "INFO  postmortem scheduled: monday, blameless*", "ERROR prod going under, learning to swim"]
def log_tex(SW, SH, fs):
    k = (SW, SH, fs)
    if k not in _LOG:
        from PIL import Image, ImageDraw
        im = Image.new('L', (SW * 2, SH), 0); d = ImageDraw.Draw(im); f = C.font(F_MONO, fs); y = 0; i = 0
        while y < SH:
            x = -int((i * 173) % (SW // 2))
            while x < SW * 2:
                s = LOG_LINES[(i * 7 + (x // 97)) % len(LOG_LINES)]; d.text((x, y), s, font=f, fill=255); x += int(f.getlength(s)) + fs * 2
            y += int(fs * 1.5); i += 1
        _LOG[k] = np.asarray(im, np.float32) / 255
    return _LOG[k]

_STARS = {}
def stars(SW, SH):
    k = (SW, SH)
    if k not in _STARS:
        r = np.random.default_rng(12); _STARS[k] = [(float(a), float(b), float(c)) for a, b, c in r.random((110, 3))]
    return _STARS[k]

_RAIN = {}
def rain_pts(W, H, seed=3):
    k = (W, H)
    if k not in _RAIN:
        r = np.random.default_rng(seed); _RAIN[k] = r.random((160, 3)).astype(np.float32)
    return _RAIN[k]

_SPECK = {}
def speckle(SW, SH):
    k = (SW, SH)
    if k not in _SPECK:
        r = np.random.default_rng(5); _SPECK[k] = (r.random((SH, SW)).astype(np.float32) - 0.5)
    return _SPECK[k]

# ---------------------------------------------------------------- background (half res): sky, sun, sea bands of logs, sand
def background(t, W, H, V, P):
    L = lay(W, H); SW, SH = W // 2, H // 2; ts = L['ts'] / 2
    G = K.grid(SW, SH); yy = G['V'][..., 0] * (SH - 1); xx = G['U'] * (SW - 1)
    top, mid, horc, sunc, sea_far, sea_near, sand, sun_s, sun_x, sun_y, night = P
    hor = V.y(L['hor']) / 2; shore = V.y(L['shore']) / 2; wl = V.y(water_level(t, L)) / 2
    # sky (a vertical gradient: computed per column once, broadcast)
    v = np.clip(yy[:, :1] / max(1.0, hor), 0, 1)[..., None]
    sky = K.vgrad({'V': v}, top, horc, mid, 0.55)            # (SH,1,3)
    bg = np.broadcast_to(sky, (SH, SW, 3)).copy()
    # sun / moon: disc at half res, glow at quarter res
    sx, sy = V.p(sun_x * W, sun_y * L['hor']); sx /= 2; sy /= 2
    r = (0.085 * min(SW, SH) * sun_s) * V.z
    glow = np.zeros((SH // 4, SW // 4, 3), np.float32)
    cv2.circle(glow, (int(sx / 4), int(sy / 4)), max(1, int(r / 4)), (sunc * (1.0 - 0.35 * night)).tolist(), -1, cv2.LINE_AA)
    g2 = cv2.resize(cv2.GaussianBlur(glow, (0, 0), max(2, r * 0.9 / 4)), (SW, SH), interpolation=cv2.INTER_LINEAR) * (0.9 - 0.5 * night)
    bg += g2
    cv2.circle(bg, (int(sx), int(sy)), int(r), (sunc * (1.0 - 0.35 * night) * 0.9 + bg[min(SH - 1, int(sy)), min(SW - 1, int(sx))] * 0).tolist(), -1, cv2.LINE_AA) if False else None
    disc = np.zeros((SH, SW), np.float32); cv2.circle(disc, (int(sx), int(sy)), int(r), 1.0, -1, cv2.LINE_AA)
    bg += disc[..., None] * sunc * (1.0 - 0.35 * night) * 0.9
    # stars
    if night > 0.2:
        ST = stars(SW, SH)
        for (sx_, sy_, sr_) in ST:
            if sy_ * SH < hor * 0.92:
                tw = 0.5 + 0.5 * math.sin(t * 2.3 + sx_ * 40)
                cv2.circle(bg, (int(sx_ * SW), int(sy_ * SH)), max(1, int(sr_ * 2.2 * ts * 2)), (MOON * night * (0.35 + 0.6 * tw)).tolist(), -1, cv2.LINE_AA)
    # a soft horizon haze
    hz = np.clip(1 - np.abs(yy - hor) / (SH * 0.08), 0, 1)[..., None] ** 2
    bg += hz * horc * 0.18 * (1 - night)
    # sea: layered wave bands between the horizon and the shoreline (or the drained low-tide line)
    sea_top = hor
    if t < T_BRIDGE: sea_bot = max(shore, wl)
    elif t < T_FINAL - 1.0: sea_bot = hor + (shore - hor) * lerp(1.0, 0.38, low_k(t))
    else: sea_bot = max(shore, wl)
    sea_bot = max(sea_bot, hor + 6)
    xs = xx[0]; st = storm(t); wob = 1 + 2.2 * st
    sea = np.zeros_like(bg); foam = np.zeros((SH, SW), np.float32); first = None
    n = 6
    for k in range(n):
        f = (k + 1) / n
        base = sea_top + (sea_bot - sea_top) * (f ** 1.4)
        amp = (1.5 + 9 * f) * ts * V.z * wob
        bnd = base + amp * np.sin(xs / (70 * ts * V.z) * (1 + 0.25 * k) + t * (0.9 + 0.35 * k) + k * 1.7) + amp * 0.45 * np.sin(xs / (26 * ts * V.z) - t * 1.6 + k * 0.6)
        if k == 0: bnd = np.minimum(bnd, base + 1); first = bnd
        m = (yy >= bnd[None, :])
        col = sea_far * (1 - f) + sea_near * f
        col = col * (1 + 0.09 * (1 if k % 2 else -1))
        sea[m] = col
        foam += np.clip(1 - np.abs(yy - bnd[None, :]) / (1.6 * ts * V.z), 0, 1) * (0.35 + 0.65 * f)
    sm = (yy >= first[None, :]) & (yy < sea_bot + 2)
    bg = np.where(sm[..., None], sea, bg)
    # log lines flowing in the water (texture)
    tex = log_tex(SW, SH, max(9, int(13 * ts * 2)))
    off = int((t * 26 * ts * 2) % SW); tex = tex[:, off:off + SW]
    depth = np.clip((yy - hor) / max(1.0, sea_bot - hor), 0, 1)
    bg += (tex * sm * (0.08 + 0.12 * depth) * (1 + 0.6 * night) * (1 + 1.2 * st))[..., None] * (sea_far * 0.6 + 0.5)
    bg += (foam * sm * 0.33 * (1 + 0.8 * st))[..., None] * (0.75 + 0.25 * sea_far)
    # sun path on the water
    path = np.exp(-((xx - sx) / (SW * 0.055 * V.z)) ** 2) * np.clip((yy - hor) / (SH * 0.25), 0, 1) * (1 - np.clip((yy - hor) / (sea_bot - hor + 1), 0, 1))
    bg += (path * sm * (0.9 - 0.55 * night) * (0.6 + 0.4 * np.sin(yy * 0.6 + t * 6) ** 2))[..., None] * sunc * 0.45
    # sand (beach) below the sea, with wet strip near the water; low tide exposes darker seabed between the lines
    below = (yy >= sea_bot - 0.5)
    sandc = sand
    wet = np.clip(1 - (yy - sea_bot) / (SH * 0.06), 0, 1)
    sp = speckle(SW, SH) * 0.035
    sandimg = (sandc * (1 - 0.22 * wet[..., None]) * (1 + sp[..., None]))
    if t >= T_BRIDGE - 0.2:   # exposed seabed (darker, rippled) from the low-tide line up to the old shoreline
        lowk = low_k(t) * (1 - lot_k(t))
        rip = 0.5 + 0.5 * np.sin(yy * 0.9 + np.sin(xx * 0.06) * 2.0)
        bed = sandc * 0.72 * (1 - 0.12 * rip[..., None]) * (1 + sp[..., None] * 2)
        zone = (yy >= sea_bot - 0.5) & (yy < shore)
        sandimg = np.where(zone[..., None], bed * lowk + sandimg * (1 - lowk), sandimg)
    bg = np.where(below[..., None], sandimg, bg)
    # parking lot: asphalt replaces the sand
    lk = lot_k(t)
    if lk > 0:
        asph = ASPHALT * (1 + sp[..., None] * 1.5)
        lotimg = np.where((yy >= shore - 2)[..., None], asph, bg)
        bg = bg * (1 - lk) + lotimg * lk
    return cv2.resize(bg, (W, H), interpolation=cv2.INTER_LINEAR)

def tide_overlay(img, t, W, H, V, P, wl_world):
    """Semi-transparent water from the surface line down over everything already drawn (the beach goes under)."""
    L = lay(W, H); ts = L['ts']; wl = V.y(wl_world); shore = V.y(L['shore'])
    if wl >= shore - 2: return
    if T_BRIDGE - 0.05 <= t < T_FINAL - 1.0: return
    top, mid, horc, sunc, sea_far, sea_near, sand, sun_s, sun_x, sun_y, night = P
    st = storm(t); yy = np.arange(H, dtype=np.float32)[:, None]; xs = np.arange(W, dtype=np.float32)
    amp = (8 + 14 * st) * ts * V.z
    bnd = wl + amp * np.sin(xs / (120 * ts * V.z) + t * 1.4) + amp * 0.5 * np.sin(xs / (41 * ts * V.z) - t * 2.1) + amp * 0.3 * np.sin(xs / (17 * ts) + t * 3.3)
    m = np.clip((yy - bnd[None, :]) / (4 * ts), 0, 1)
    depth = np.clip((yy - bnd[None, :]) / (H * 0.45), 0, 1)
    wcol = sea_far * 0.75 + sea_near * 0.25
    a = (0.62 + 0.25 * depth) * m
    img *= (1 - a[..., None]); img += a[..., None] * wcol
    tex = log_tex(W // 2, H // 2, max(9, int(13 * ts)))
    off = int((t * 40 * ts) % (W // 2)); tex = cv2.resize(tex[:, off:off + W // 2], (W, H))
    img += (tex * m * (0.16 + 0.1 * st))[..., None] * (sea_far * 0.5 + 0.55)
    fl = np.clip(1 - np.abs(yy - bnd[None, :]) / (5 * ts), 0, 1) * (0.7 + 0.3 * st)
    img += fl[..., None] * (0.85 + 0.15 * sea_far)

# ---------------------------------------------------------------- objects
def paper_boat(img, V, x, y, s, a, op=1.0, label="#459", capsize=0.0, sink=0.0):
    """Paper boat. (x,y) = waterline centre (world), s = half-width (world px), a = tilt (rad), capsize 0..1 flips it."""
    if op <= 0.01: return
    s = V.sz(s); x, y = V.p(x, y + sink * s * 0.5 / V.z)
    ang = a + capsize * math.pi
    hull = np.array([(-1.0, 0.0), (1.0, 0.0), (0.62, 0.48), (-0.62, 0.48)]) * s
    sail = np.array([(-0.56, 0.0), (0.56, 0.0), (0.0, -0.98)]) * s
    sail2 = np.array([(-0.3, 0.0), (0.3, 0.0), (0.0, -0.52)]) * s
    crease = np.array([(0.0, -0.98), (0.0, 0.0)]) * s
    H_ = rot(hull, ang, 0, 0) + [x, y]; Sa = rot(sail, ang) + [x, y]; Sb = rot(sail2, ang) + [x, y]; Cr = rot(crease, ang) + [x, y]
    # shadow on the water
    sh = np.array([(-1.05, 0.05), (1.05, 0.05), (0.7, 0.3), (-0.7, 0.3)]) * s
    poly(img, rot(sh, ang) + [x, y + s * 0.08], INK, 0.25 * op)
    poly(img, H_, PAPER2, op, outline=INK, ow=max(2, s * 0.045))
    poly(img, Sa, PAPER, op, outline=INK, ow=max(2, s * 0.045))
    poly(img, Sb, PAPER2 * 0.92, op * 0.9)
    line(img, Cr[0], Cr[1], INK * 0.8, max(1, s * 0.03), op)
    # pennant
    tip = Cr[0]; pf = np.array([(0, -0.98), (0.42, -0.86), (0, -0.74)]) * s
    poly(img, rot(pf, ang) + [x, y], CORAL, op)
    # hull label
    fs = max(12, int(s * 0.34))
    if label:
        lp = rot(np.array([(0.0, 0.26)]) * s, ang) + [x, y]
        blit(img, sprite(label, F_MONOB, fs), lp[0][0], lp[0][1], INK, op * (1 - capsize), anchor='c')

def cursor(img, V, x, y, s, op=1.0, col=WHITE, a=0.0):
    if op <= 0.01: return
    s = V.sz(s); x, y = V.p(x, y)
    pts = np.array([(0, 0), (0, 15), (3.8, 11.4), (6.6, 18), (9.2, 16.9), (6.4, 10.6), (11, 10.6)], np.float32) * (s / 15)
    pts = rot(pts, a) + [x, y]
    poly(img, pts, col, op, outline=INK, ow=max(2, s * 0.09))

def laptop(img, V, t, L, lid, op=1.0, screen=None, glow=0.0, col=None):
    """Flat laptop seen from the front-left; lid 0 closed .. 1 open. screen(img, rect) draws the screen content."""
    if op <= 0.01: return
    lx, ly = L['lap']; w = L['lapw']; ts = L['ts']
    body = col if col is not None else hexc('d9d6d2')
    bx, by = V.p(lx, ly); bw = V.sz(w); bh = V.sz(w * 0.055)
    K.panel(img, bx - bw / 2, by - bh, bw, bh, body, op, r=int(bh * 0.35), shadow_op=0.5)
    K.panel(img, bx - bw * 0.16, by - bh * 0.8, bw * 0.32, bh * 0.55, body * 0.8, op, r=int(bh * 0.2), shadow_op=0)   # trackpad
    lid_h = V.sz(w * 0.62) * max(0.02, lid)
    lw = bw * 0.96
    K.panel(img, bx - lw / 2, by - bh - lid_h, lw, lid_h, hexc('26242b'), op, r=int(V.sz(w * 0.02)), shadow_op=0.4)
    if lid > 0.6:
        pad = V.sz(w * 0.025); rect = (bx - lw / 2 + pad, by - bh - lid_h + pad, lw - 2 * pad, lid_h - 2 * pad)
        sc = hexc('f4f1ea') if col is None else hexc('0f1218')
        K.panel(img, *rect, sc, op * sstep(0.6, 0.85, lid), r=int(pad * 0.5), shadow_op=0)
        if screen is not None and lid > 0.85: screen(img, rect)
        if glow > 0: soft_glow(img, rect[0], rect[1], rect[0] + rect[2], rect[1] + rect[3], V.sz(w * 0.08), LAMP, 0.5 * glow * op)
    elif lid > 0.05:   # half shut: a thin slit of screen light under the lid
        s = sstep(0.05, 0.6, lid)
        K.panel(img, bx - lw / 2 + 6, by - bh - lid_h * 0.22, lw - 12, lid_h * 0.2, hexc('f4f1ea') * 0.9, op * s, r=2, shadow_op=0)
        soft_glow(img, bx - lw / 2, by - bh - lid_h * 0.3, bx + lw / 2, by - bh, V.sz(w * 0.05), CYAN, 0.25 * s * op)

def shipit_screen(t, V, L, press, prog):
    """The PR page: title, diff, a huge green SHIP IT button, and the cursor. Type is fitted to the screen width."""
    def draw(img, rect):
        x, y, w, h = rect; ts = L['ts'] * V.z * (1.0 if not L['vert'] else 0.74)
        # never let a line run off the screen: shrink the type until the longest lines fit inside 90% of the width
        fit = min(1.0, 0.90 * w / max(1, text_w("PR #459 · one little change", F_MONOB, int(34 * ts))),
                  0.90 * w / max(1, text_w("no ticket · no test · no second pair of eyes", F_MONO, int(22 * ts))),
                  0.90 * w / max(1, text_w("+1  -1   ·   friday-fix -> main", F_MONO, int(28 * ts))))
        ts *= fit
        f1, f2, f3 = 34 * ts, 28 * ts, 26 * ts
        y1 = y + h * 0.06
        mono(img, "PR #459 · one little change", x + w * 0.05, y1, f1, INK * 0.8, bold=True)
        y2 = y1 + f1 * 1.45
        mono(img, "+1  -1   ·   friday-fix -> main", x + w * 0.05, y2, f2, INK * 0.55)
        # checks row
        cy = y2 + f2 * 1.5
        for i, (s, c) in enumerate((("✓ CI", GREEN), ("✓ lint", GREEN), ("0 reviews", hexc('b4b0a8')))):
            mlabel(img, s, x + w * (0.05 + i * 0.24), cy, f3, c, 1.0, anchor='lt', sh=0)
        # the button, between the checks row and the footer line
        f4 = 22 * ts; fy = y + h - h * 0.05 - f4 * 1.3
        top = cy + f3 * 1.7; bot = fy - f4 * 0.6
        bw = w * 0.62; bh = max(f1 * 1.2, min(h * 0.30, bot - top)); bx, by = x + w / 2 - bw / 2, top + (bot - top - bh) / 2
        pk = 1 - 0.07 * press
        K.panel(img, bx + bw * (1 - pk) / 2, by + bh * (1 - pk) / 2, bw * pk, bh * pk, GREEN * (1 - 0.25 * press), 1.0, r=int(bh * 0.3), shadow_op=0.5 * (1 - press))
        if prog <= 0:
            blit(img, sprite("SHIP IT", F_DISP, int(bh * 0.52 * pk)), x + w / 2, by + bh / 2, INK, 1.0, anchor='c')
        else:
            K.panel(img, bx + bw * 0.06, by + bh * 0.62, bw * 0.88, bh * 0.16, INK * 0.5, 1.0, r=int(bh * 0.08), shadow_op=0)
            K.panel(img, bx + bw * 0.06, by + bh * 0.62, bw * 0.88 * clamp(prog), bh * 0.16, CREAM, 1.0, r=int(bh * 0.08), shadow_op=0)
            blit(img, sprite(f"deploying… {int(clamp(prog) * 100)}%", F_DISPB, int(bh * 0.30)), x + w / 2, by + bh * 0.33, INK, 1.0, anchor='c')
        mono(img, "no ticket · no test · no second pair of eyes", x + w * 0.05, fy, f4, INK * 0.4)
    return draw

def shipped_screen(t, V, L):
    def draw(img, rect):
        x, y, w, h = rect; ts = L['ts'] * V.z * (1.0 if not L['vert'] else 0.74)
        k = sstep(T_IT + 0.6, T_IT + 0.9, t); pop = 1 + 0.25 * math.exp(-max(0, t - T_IT - 0.6) * 6)
        circ(img, (x + w / 2, y + h * 0.36), h * 0.17 * pop, GREEN, k)
        blit(img, sprite("✓", F_DISP, int(h * 0.24 * pop)), x + w / 2, y + h * 0.36, INK, k, anchor='c')
        blit(img, sprite("SHIPPED", F_DISP, int(min(h * 0.18, w * 0.11))), x + w / 2, y + h * 0.67, INK, k, anchor='c')
        mono(img, "PR #459 · 5:00 PM · rollback plan: none", x + w / 2, y + h * 0.86, 24 * ts, INK * 0.5, k, anchor='c')
    return draw

def dashboard_screen(t, L):
    def draw(img, rect):
        x, y, w, h = rect; ts = L['ts']
        K.panel(img, x, y, w, h, hexc('2a0b12'), 1.0, r=int(8 * ts), shadow_op=0)
        mlabel(img, "p99 latency", x + w * 0.05, y + h * 0.08, 26 * ts, CREAM * 0.8, anchor='lt', sh=0)
        # red spiking graph
        n = 28; pts = []
        for i in range(n):
            u = i / (n - 1); v = 0.25 + 0.65 * sstep(0.35, 0.6, u) * (0.6 + 0.4 * abs(math.sin(i * 1.7 + t * 3)))
            pts.append((x + w * (0.05 + 0.9 * u), y + h * (0.9 - 0.7 * v)))
        cv2.polylines(img, [np.round(np.array(pts) * 4).astype(np.int32)], False, RED.tolist(), max(2, int(5 * ts)), cv2.LINE_AA, shift=2)
        mlabel(img, "ERRORS 100%", x + w * 0.95, y + h * 0.08, 30 * ts, RED, anchor='c' if False else 'lt', sh=0) if False else None
    return draw

def terminal_screen(t, L, lines):
    def draw(img, rect):
        x, y, w, h = rect; ts = L['ts']
        K.panel(img, x, y, w, h, hexc('0f1218'), 1.0, r=int(8 * ts), shadow_op=0)
        fs = 24 * ts; yy = y + h * 0.08
        for s, c in lines[-5:]:
            mono(img, s, x + w * 0.04, yy, fs, c); yy += fs * 1.45
    return draw

def phone(img, V, t, L, face_up, buzz, op=1.0, screen=None, hot=0.0, lit=1.0):
    if op <= 0.01: return
    px, py = L['phone']; ts = L['ts']
    pw, ph = V.sz(118 * ts), V.sz(230 * ts)
    dx = math.sin(t * 95) * 5 * ts * buzz; dy = math.cos(t * 83) * 3 * ts * buzz
    x, y = V.p(px, py); x += dx; y += dy
    body = hexc('1b1a22') * (1 - hot) + RED * 0.8 * hot
    K.panel(img, x - pw / 2, y - ph, pw, ph, body, op, r=int(pw * 0.18), shadow_op=0.55)
    if face_up:
        pad = pw * 0.06
        K.panel(img, x - pw / 2 + pad, y - ph + pad, pw - 2 * pad, ph - 2 * pad, hexc('0b0c12'), op, r=int(pw * 0.14), shadow_op=0)
        if screen is not None: screen(img, (x - pw / 2 + pad, y - ph + pad, pw - 2 * pad, ph - 2 * pad))
        if lit > 0: soft_glow(img, x - pw / 2, y - ph, x + pw / 2, y, pw * 0.5, CYAN * 0.5 + 0.2, 0.5 * lit * op)
    else:
        circ(img, (x - pw * 0.28, y - ph * 0.86), pw * 0.09, hexc('2c2b36'), op); circ(img, (x - pw * 0.28, y - ph * 0.86), pw * 0.045, hexc('5a5870'), op)
    # buzz arcs
    if buzz > 0.05:
        for sgn in (-1, 1):
            for k in range(2):
                r = pw * (0.75 + 0.35 * k); a = (0.6 + 0.4 * math.sin(t * 30 + k)) * buzz * op
                cv2.ellipse(img, (int(x + sgn * pw * 0.55), int(y - ph * 0.5)), (int(r * 0.35), int(r * 0.6)), 0, -40 if sgn > 0 else 140, 40 if sgn > 0 else 220, (WHITE * a).tolist(), max(2, int(5 * ts)), cv2.LINE_AA)
    if hot > 0.05:   # heat shimmer
        for k in range(3):
            yy0 = y - ph - ts * (30 + 40 * k) - (t * 60 * ts) % (40 * ts)
            pts = [(x - pw * 0.3 + i * pw * 0.1, yy0 + math.sin(i * 1.3 + t * 9 + k) * 6 * ts) for i in range(7)]
            cv2.polylines(img, [np.round(np.array(pts) * 4).astype(np.int32)], False, (ALERT * 0.6 * hot * op).tolist(), max(2, int(4 * ts)), cv2.LINE_AA, shift=2)

def alert_screen(L, badge, big=None, sub=None, col=RED):
    def draw(img, rect):
        x, y, w, h = rect; ts = L['ts']
        if badge:
            circ(img, (x + w * 0.5, y + h * 0.28), w * 0.26, col, 1.0)
            blit(img, sprite(badge, F_DISP, int(w * (0.30 if len(badge) < 3 else 0.22))), x + w * 0.5, y + h * 0.28, WHITE, 1.0, anchor='c')
        if big: blit(img, sprite(big, F_DISPB, int(w * 0.16)), x + w * 0.5, y + h * 0.62, WHITE, 1.0, anchor='c')
        if sub: blit(img, sprite(sub, F_INTER, int(w * 0.12)), x + w * 0.5, y + h * 0.76, WHITE * 0.8, 1.0, anchor='c')
    return draw

def coffee(img, V, t, L, steam, op=1.0):
    if op <= 0.01: return
    cx, cy = L['cup']; ts = L['ts']; x, y = V.p(cx, cy); s = V.sz(44 * ts)
    cup = np.array([(-1.0, -1.3), (1.0, -1.3), (0.8, 0.0), (-0.8, 0.0)]) * s + [x, y]
    poly(img, cup, hexc('ffffff'), op, outline=INK, ow=max(2, s * 0.08))
    cv2.ellipse(img, (int(x), int(y - 1.3 * s)), (int(s), int(s * 0.28)), 0, 0, 360, hexc('5a3b2a').tolist(), -1, cv2.LINE_AA)
    cv2.ellipse(img, (int(x + s * 1.15), int(y - 0.75 * s)), (int(s * 0.45), int(s * 0.4)), 0, -100, 100, INK.tolist(), max(2, int(s * 0.12)), cv2.LINE_AA)
    mono(img, "☕ 4:59", x, y - s * 0.65, max(14, int(s * 0.3)), INK * 0.7, op, anchor='c') if False else None
    for k in range(3):
        a = steam * (0.5 + 0.5 * math.sin(t * 2 + k)) * op
        if a <= 0.02: continue
        pts = [(x + (k - 1) * s * 0.45 + math.sin(t * 2.5 + i * 0.9 + k) * s * 0.18, y - 1.5 * s - i * s * 0.32 - (t * 20 * ts) % (s * 0.3)) for i in range(5)]
        cv2.polylines(img, [np.round(np.array(pts) * 4).astype(np.int32)], False, (WHITE * a * 0.8).tolist(), max(2, int(s * 0.1)), cv2.LINE_AA, shift=2)

def seagull(img, x, y, s, col, op=1.0, flap=0.0):
    if op <= 0.01: return
    f = 0.35 + 0.5 * flap
    pts = [(x - s, y + s * 0.1), (x - s * 0.5, y - s * f), (x, y + s * 0.15), (x + s * 0.5, y - s * f), (x + s, y + s * 0.1)]
    cv2.polylines(img, [np.round(np.array(pts) * 4).astype(np.int32)], False, (col * op).tolist(), max(2, int(s * 0.16)), cv2.LINE_AA, shift=2)

def life_ring(img, V, t, L, x, y, s, op=1.0, rope_from=None, label="ROLLBACK", sway=0.0):
    if op <= 0.01: return
    ts = L['ts']; s = V.sz(s); x, y = V.p(x, y)
    if rope_from is not None:
        rx, ry = V.p(*rope_from); n = 14; prev = None
        for i in range(n + 1):
            u = i / n; px = lerp(rx, x, u) + math.sin(u * 6 + t * 4) * sway * s * 0.5 * (1 - u); py = lerp(ry, y - s * 0.95, u)
            if prev is not None and i % 2 == 1: line(img, prev, (px, py), hexc('c8a46a'), max(3, s * 0.14), op)
            prev = (px, py)
    circ(img, (x, y + s * 0.15), s * 1.05, INK, 0.25 * op)
    circ(img, (x, y), s, CREAM, op, th=max(3, int(s * 0.42)))
    for k in range(4):
        cv2.ellipse(img, (int(x), int(y)), (int(s), int(s)), 0, k * 90 + 12, k * 90 + 54, (RED * op).tolist(), max(3, int(s * 0.42)), cv2.LINE_AA)
    circ(img, (x, y), s * 1.2, INK, op, th=max(2, int(s * 0.06))); circ(img, (x, y), s * 0.78, INK, op, th=max(2, int(s * 0.06)))
    if label:
        fs = int(max(34 * ts, s * 0.42)); w = text_w(label, F_DISP, fs) + fs * 0.9; h = fs * 1.5
        K.panel(img, x - w / 2, y + s * 1.25, w, h, CREAM, op, r=int(h * 0.3), shadow_op=0.5)
        blit(img, sprite(label, F_DISP, fs), x, y + s * 1.25 + h / 2, RED, op, anchor='c')

def chip(img, s, cx, cy, fs, bg, fg, op, pop=None, t=0.0, path=F_DISP):
    if op <= 0.01: return
    sc = 1.0
    if pop is not None: sc = 0.5 + 0.5 * ease_out((t - pop) / 0.2) + 0.12 * math.exp(-max(0, t - pop) * 7)
    fs2 = int(fs * sc); w = text_w(s, path, fs2) + fs2 * 1.1; h = fs2 * 1.75
    K.panel(img, cx - w / 2, cy - h / 2, w, h, bg, op, r=int(h * 0.45), shadow_op=0.5)
    blit(img, sprite(s, path, fs2), cx, cy, fg, op, anchor='c')
    return w

def strike(img, cx, cy, w, col, op, k):
    if k <= 0.01 or op <= 0.01: return
    line(img, (cx - w * 0.5, cy + 2), (cx - w * 0.5 + w * k, cy - 2), col, 6, op)

def clock_chip(img, t, W, H, L, op=1.0):
    """FRI 4:59 PM … the clock creeps through the evening and lands back on 4:59 next Friday."""
    if op <= 0.01: return
    ts = L['ts']; x, y, anc = L['clock']
    times = [(0, "FRI 4:59 PM"), (T_IT, "FRI 5:00 PM"), (T_CH1, "FRI 5:03 PM"), (T_V2, "FRI 5:17 PM"), (T_CH2, "FRI 5:41 PM"), (T_BRIDGE, "FRI 6:02 PM"),
             (T_V3, "FRI 6:28 PM"), (T_FINAL, "FRI 7:10 PM"), (T_459B, "FRI 4:59 PM")]
    s = [lab for tt, lab in times if t >= tt][-1]
    fs = int(34 * ts); w = text_w(s, F_MONOB, fs) + fs * 1.0; h = fs * 1.6
    cx = x - w / 2 if anc == 'r' else x
    hot = sstep(T_459B - 0.1, T_459B + 0.3, t) * (1 - sstep(T_459B + 1.6, T_459B + 2.6, t))
    K.panel(img, cx - w / 2, y - h / 2, w, h, INK * (1 - hot) + CORAL * hot, op * 0.9, r=int(h * 0.3), shadow_op=0.4)
    blit(img, sprite(s, F_MONOB, fs), cx, y, CREAM, op, anchor='c')

def tally_chip(img, t, L, op=1.0):
    n = sum(1 for a in AGAINS if t >= a)
    if n == 0 or op <= 0.01: return
    last = max(a for a in AGAINS if t >= a); ts = L['ts']; x, y, anc = L['tally']
    s = f"never again  ×{n}"; fs = int(34 * ts); pop = 1 + 0.25 * math.exp(-max(0, t - last) * 6)
    w = text_w(s, F_DISPB, int(fs * pop)) + fs * 1.0; h = fs * 1.6 * pop
    cx = x - w / 2 if anc == 'r' else x
    K.panel(img, cx - w / 2, y - h / 2, w, h, RED, op * 0.92, r=int(h * 0.3), shadow_op=0.4)
    blit(img, sprite(s, F_DISPB, int(fs * pop)), cx, y, WHITE, op, anchor='c')

# ---------------------------------------------------------------- UI set pieces
def slack_boardwalk(img, V, t, L, P, k):
    """A pier along the horizon with marquee channel signs that light up one by one."""
    if k <= 0.01: return
    W, H = img.shape[1], img.shape[0]; ts = L['ts']; hor = V.y(L['hor'])
    names = ["#incidents", "#eng", "#is-prod-down", "#general", "#exec"] if not L['vert'] else ["#incidents", "#is-prod-down", "#exec"]
    pier_h = 22 * ts; y0 = hor - pier_h * 0.5 + 8 * ts
    K.panel(img, -10, y0, W + 20, pier_h, hexc('3a2a22'), k, r=2, shadow_op=0.3)
    for i in range(0, 16):
        px = (i + 0.5) * W / 16; line(img, (px, y0 + pier_h), (px, y0 + pier_h + 28 * ts), hexc('2a1d18'), max(3, 6 * ts), k)
    n = len(names); sw = W * (0.17 if not L['vert'] else 0.30); sh_ = 64 * ts
    for i, nm in enumerate(names):
        cx = W * (0.5 + (i - (n - 1) / 2) * (0.195 if not L['vert'] else 0.32))
        on = sstep(T_V2 + i * 0.42, T_V2 + i * 0.42 + 0.25, t)
        urgent = 1.0 if i in (0, 2) else 0.0
        col = (SLACKP if i % 2 == 0 else SLACKB) * 0.25 + hexc('1b1826') * 0.75
        lit = (SLACKP if i % 2 == 0 else (SLACKB if i != 1 else SLACKY)) * 0.9 + 0.1
        K.panel(img, cx - sw / 2, y0 - sh_ - 26 * ts, sw, sh_, col * (1 - on) + lit * on * 0.35 + col * on * 0.65, k, r=int(10 * ts), border=lit * on + hexc('3a3444') * (1 - on), shadow_op=0.5)
        # bulbs
        nb = 9
        for b in range(nb):
            bx = cx - sw / 2 + sw * (b + 0.5) / nb; ph = 0.5 + 0.5 * math.sin(t * 7 + b * 1.1 + i)
            circ(img, (bx, y0 - sh_ - 26 * ts - 8 * ts), 5 * ts, lit * (0.4 + 0.6 * ph) * on + hexc('333333') * (1 - on), k)
            circ(img, (bx, y0 - 26 * ts + 8 * ts), 5 * ts, lit * (0.4 + 0.6 * ph) * on + hexc('333333') * (1 - on), k)
        blit(img, sprite(nm, F_DISPB, int(36 * ts)), cx, y0 - sh_ / 2 - 26 * ts, WHITE * (0.45 + 0.55 * on), k, 0.6 * on, glow_color=lit, anchor='c')
        # count badge pulsing on the urgent ones
        if urgent and on > 0.9:
            cnt = min(999, int((t - T_V2) * (37 if i == 0 else 61)))
            chip(img, f"{cnt}", cx + sw / 2 - 6 * ts, y0 - sh_ - 26 * ts + 4 * ts, int(26 * ts), RED, WHITE, k, path=F_DISPB)
        # reflection in the water
        rx0 = int(cx - sw * 0.35); rx1 = int(cx + sw * 0.35)
        ry0 = int(hor + 30 * ts); ry1 = int(min(H, hor + 160 * ts))
        if ry1 > ry0 and on > 0.05:
            yy = np.arange(ry0, ry1)[:, None]; wob = (np.sin(yy * 0.22 + t * 5 + i) * 0.5 + 0.5)
            fade = (1 - (yy - ry0) / (ry1 - ry0)) * 0.22 * on * k * wob
            img[ry0:ry1, rx0:rx1] += fade[..., None] * lit

def null_table(img, t, L, W, H, k):
    if k <= 0.01: return
    ts = L['ts']; vert = L['vert']
    w = W * (0.46 if not vert else 0.86); h = 60 * ts * 6.3
    x = W * (0.07 if not vert else 0.07); y = H * (0.12 if not vert else 0.16)
    K.panel(img, x, y, w, h, hexc('f7f3ea'), k * 0.96, r=int(16 * ts), shadow_op=0.55)
    cols = ["order_id", "customer", "amount"]; cw = [0.28, 0.38, 0.34]
    rows = [("7731", "alice", "$1,299.00"), ("7732", "ben", "$84.50"), ("7733", "carla", "$12,040.00"), ("7734", "dev", "$7.99")]
    yy = y + 18 * ts; fs = int(34 * ts)
    xx = x + 24 * ts
    for c, cwid in zip(cols, cw):
        blit(img, sprite(c, F_MONOB, fs), xx, yy, INK * 0.55, k); xx += w * cwid
    line(img, (x + 16 * ts, yy + fs * 1.5), (x + w - 16 * ts, yy + fs * 1.5), INK * 0.2, 2, k)
    for r, (a, b, c) in enumerate(rows):
        yy2 = yy + fs * 1.75 + r * fs * 1.7; xx = x + 24 * ts
        tn = T_NULL + 0.55 + r * 0.33; gone = sstep(tn, tn + 0.08, t)
        for ci, (val, cwid) in enumerate(zip((a, b, c), cw)):
            if ci == 2:
                if gone < 0.5:
                    jit = val if t < tn - 0.4 else "".join(chr(0x30 + int((t * 60 + i * 3) % 10)) if ch.isdigit() else ch for i, ch in enumerate(val))
                    blit(img, sprite(jit, F_MONO, fs), xx, yy2, INK * 0.85, k)
                else:
                    pop = 1 + 0.3 * math.exp(-max(0, t - tn) * 8)
                    K.panel(img, xx - 8 * ts, yy2 - 6 * ts, text_w("NULL", F_MONOB, int(fs * pop)) + 16 * ts, fs * 1.35 * pop, RED, k, r=int(8 * ts), shadow_op=0)
                    blit(img, sprite("NULL", F_MONOB, int(fs * pop)), xx, yy2, WHITE, k)
            else: blit(img, sprite(val, F_MONO, fs), xx, yy2, INK * 0.85, k)
            xx += w * cwid
    foot = f"{min(10000, int(max(0, t - T_ROWS) * 5200)):,} rows affected" if t >= T_ROWS - 0.1 else "4 of 10,000 rows"
    blit(img, sprite(foot, F_DISPB, int(30 * ts)), x + w - 24 * ts, y + h - 30 * ts - 16 * ts, RED if t >= T_ROWS else INK * 0.5, k, anchor='lt') if False else \
        blit(img, sprite(foot, F_DISPB, int(30 * ts)), x + w / 2, y + h - 28 * ts, RED if t >= T_ROWS else INK * 0.5, k, anchor='c')

def arrows_at_me(img, t, L, W, H, k, target):
    """Ten thousand rows all pointing at me."""
    if k <= 0.01: return
    ts = L['ts']; r = np.random.default_rng(11); tx, ty = target
    n = 120
    for i in range(n):
        u = (i / n + t * 0.35 * (0.6 + 0.8 * r.random())) % 1.0
        a0 = r.random() * 2 * math.pi; rad = (0.25 + 0.75 * r.random()) * min(W, H) * 0.9
        x0, y0 = tx + math.cos(a0) * rad, ty + math.sin(a0) * rad
        x, y = lerp(x0, tx, u), lerp(y0, ty, u)
        ang = math.atan2(ty - y, tx - x)
        # rotate the arrow sprite (cheap: pick 8 directions by drawing a short thick line + head instead)
        hx, hy = x + math.cos(ang) * 38 * ts, y + math.sin(ang) * 38 * ts
        a = k * (1 - u) * 0.9
        cv2.arrowedLine(img, (int(x), int(y)), (int(hx), int(hy)), (YEL * a).tolist(), max(2, int(6 * ts)), cv2.LINE_AA, tipLength=0.45)

def retry_queue(img, V, t, L, W, H, k, wl):
    """Paper boats bumper to bumper, RETRY on every sail, backing up from the right."""
    if k <= 0.01: return
    ts = L['ts']; n = 9 if not L['vert'] else 5; s = 34 * ts
    y = wl - 8 * ts
    for i in range(n):
        ti = T_RETRY + i * 0.22; a = sstep(ti, ti + 0.2, t)
        if a <= 0: continue
        x0 = W + 2.2 * s; x1 = W * (0.96 if not L['vert'] else 0.95) - i * s * 2.25
        x = lerp(x0, x1, ease_out((t - ti) / 0.6)); bob = math.sin(t * 5 + i) * 3 * ts
        paper_boat(img, View(W, H), x, y + bob, s, math.sin(t * 4 + i) * 0.06, k * a, label="RETRY" if s * 0.34 >= 12 else "")
    cnt = min(99999, int(max(0, t - T_RETRY) * 1900) + 12)
    chip(img, f"queue depth  {cnt:,}", W * (0.80 if not L['vert'] else 0.5), wl - s * 2.6 - 40 * ts, int(34 * ts), INK, YEL, k, path=F_DISPB)

def dead_letter_cup(img, V, t, L, W, H, k):
    """Envelopes with a red X stacking in a cup on the sand."""
    if k <= 0.01: return
    ts = L['ts']; cx = W * (0.84 if not L['vert'] else 0.5); cy = V.y(L['hor']) + (H * 0.115 if not L['vert'] else H * 0.10)
    s = 70 * ts
    K.panel(img, cx - s * 1.0, cy - s * 1.9, s * 2.0, s * 1.9, hexc('6fd3e0') * 0.9, k * 0.55, r=int(s * 0.25), shadow_op=0.5)
    n = 8
    for i in range(n):
        ti = T_DEAD + 0.15 + i * 0.26; a = sstep(ti, ti + 0.05, t)
        if a <= 0: continue
        drop = ease_out((t - ti) / 0.35); row = i // 3; col = i % 3
        ex = cx - s * 0.62 + col * s * 0.62 + (row % 2) * s * 0.3; ey_end = cy - s * 0.35 - row * s * 0.42
        ey = lerp(cy - s * 4.5, ey_end, drop); ew, eh = s * 0.62, s * 0.42; ang = (i % 3 - 1) * 0.18
        pts = rot(np.array([(-ew / 2, -eh / 2), (ew / 2, -eh / 2), (ew / 2, eh / 2), (-ew / 2, eh / 2)]), ang) + [ex, ey]
        poly(img, pts, CREAM, k * a, outline=INK, ow=max(2, 3 * ts))
        fl = rot(np.array([(-ew / 2, -eh / 2), (0, eh * 0.05), (ew / 2, -eh / 2)]), ang) + [ex, ey]
        cv2.polylines(img, [np.round(fl * 4).astype(np.int32)], False, INK.tolist(), max(2, int(3 * ts)), cv2.LINE_AA, shift=2)
        blit(img, sprite("✕", F_DISP, int(eh * 0.8)), ex + ew * 0.28, ey + eh * 0.02, RED, k * a, anchor='c')
    K.panel(img, cx - s * 1.08, cy - s * 1.2, s * 2.16, s * 1.25, hexc('6fd3e0'), k * 0.35, r=int(s * 0.2), shadow_op=0)   # glassy front of the cup
    cv2.ellipse(img, (int(cx), int(cy - s * 1.9)), (int(s * 1.0), int(s * 0.18)), 0, 0, 360, (INK * k).tolist(), max(2, int(3 * ts)), cv2.LINE_AA)
    chip(img, "dead-letter queue", cx, cy + 36 * ts, int(34 * ts), INK, CYAN, k, path=F_DISPB)

def vp_typing(img, t, L, W, H, k):
    if k <= 0.01: return
    ts = L['ts']; vert = L['vert']
    x = W * (0.54 if not vert else 0.06); y = H * (0.12 if not vert else 0.17); w = W * (0.42 if not vert else 0.88)
    typing = (T_VP1 <= t < T_VPSTOP) or (T_VP2 <= t < T_DROPPED)
    stopped = T_VPSTOP <= t < T_VP2
    h = 96 * ts
    K.panel(img, x, y, w, h, hexc('1b1826'), k * 0.95, r=int(16 * ts), border=hexc('4a4462'), shadow_op=0.5)
    circ(img, (x + 48 * ts, y + h / 2), 30 * ts, SLACKP, k); blit(img, sprite("VP", F_DISPB, int(28 * ts)), x + 48 * ts, y + h / 2, WHITE, k, anchor='c')
    fs = int(38 * ts)
    if typing:
        blit(img, sprite("VP is typing", F_DISPB, fs), x + 96 * ts, y + h / 2 - fs * 0.6, WHITE * 0.95, k)
        for d in range(3):
            ph = math.sin(t * 9 - d * 0.9); circ(img, (x + 96 * ts + text_w("VP is typing ", F_DISPB, fs) + 10 * ts + d * 24 * ts, y + h / 2 + 6 * ts - 10 * ts * max(0, ph)), 7 * ts, WHITE * 0.95, k)
    elif stopped:
        blit(img, sprite("VP stopped typing.", F_DISPB, fs), x + 96 * ts, y + h / 2 - fs * 0.6, WHITE * 0.6, k)
    elif t >= T_DROPPED:
        blit(img, sprite("VP · 5:17 PM", F_DISPB, fs), x + 96 * ts, y + h / 2 - fs * 0.6, WHITE * 0.6, k)
    if t >= T_DROPPED:
        a = sstep(T_DROPPED, T_DROPPED + 0.08, t); drop = ease_out((t - T_DROPPED) / 0.25)
        yb = lerp(y - H * 0.4, y + h + 14 * ts, drop); hb = 120 * ts
        K.panel(img, x, yb, w, hb, SLACKP, k * a, r=int(16 * ts), shadow_op=0.6)
        msg = "VP: why is checkout returning $NULL?" if not vert else "VP: why is checkout $NULL?"
        fs = int(42 * ts)
        while text_w(msg, F_DISPB, fs) > w - 40 * ts: fs -= 2
        blit(img, sprite(msg, F_DISPB, fs), x + w / 2, yb + hb * 0.5, WHITE, k * a, anchor='c')

def calendar_wall(img, t, L, W, H, k):
    """Every Friday so far, stamped NEVER AGAIN."""
    if k <= 0.01: return
    ts = L['ts']; vert = L['vert']
    cols, rows = (6, 2) if not vert else (3, 4)
    cw, ch = (W * 0.135, H * 0.26) if not vert else (W * 0.27, H * 0.145)
    gx, gy = (W * 0.5 - (cols * cw + (cols - 1) * 20 * ts) / 2, H * 0.19) if not vert else (W * 0.5 - (cols * cw + (cols - 1) * 16 * ts) / 2, H * 0.15)
    dates = ["JUL 10", "JUL 17", "JUL 24", "JUL 31", "AUG 7", "AUG 14", "AUG 21", "AUG 28", "SEP 4", "SEP 11", "SEP 18", "SEP 25"]
    n = cols * rows
    for i in range(n):
        r, c = divmod(i, cols); x = gx + c * (cw + (20 if not vert else 16) * ts); y = gy + r * (ch + 20 * ts)
        ti = T_WALL + i * 0.42; a = sstep(ti - 0.15, ti, t)
        if a <= 0: continue
        K.panel(img, x, y, cw, ch, PAPER, k * a, r=int(12 * ts), shadow_op=0.5)
        K.panel(img, x, y, cw, ch * 0.3, CORAL, k * a, r=int(12 * ts), shadow_op=0)
        blit(img, sprite("FRIDAY", F_DISPB, int(30 * ts)), x + cw / 2, y + ch * 0.15, WHITE, k * a, anchor='c')
        blit(img, sprite(dates[i % len(dates)] if i < n - 1 else "TODAY", F_DISP, int(44 * ts)), x + cw / 2, y + ch * 0.52, INK, k * a, anchor='c')
        st = sstep(ti + 0.12, ti + 0.2, t)
        if st > 0:
            pop = 1 + 0.5 * math.exp(-max(0, t - ti - 0.12) * 10)
            K.sticker(img, x + cw / 2, y + ch * 0.76, 0.36 * pop * ts * (1.0 if not vert else 0.95), k * st, (i % 3 - 1) * 0.15, age=t - ti - 0.12, text="NEVER AGAIN")

def seabed_artifacts(img, V, t, L, W, H, k):
    """Low tide shows you everything: every shortcut, every string, half-buried in the wet sand."""
    if k <= 0.01: return
    ts = L['ts']; vert = L['vert']; shore = L['shore']; hor = L['hor']
    items = ["TODO: fix later (2021)", "skip_tests = True", "catch (e) {}", "retries: 999", "// temporary", "password = 'hunter2'", "if friday: deploy()", "sleep(3) # race fix"]
    if vert: items = items[:5]
    r = np.random.default_rng(21)
    for i, s in enumerate(items):
        ti = T_LOW + 0.9 + i * 0.28 + (sstep(T_EVERY, T_EVERY + 0.01, t) * 0)
        a = sstep(ti, ti + 0.25, t)
        if a <= 0: continue
        u = (i + 0.5) / len(items); xw = W * (0.06 + 0.88 * u) + r.normal(0, W * 0.02)
        yw = lerp(hor + (shore - hor) * 0.42, hor + (shore - hor) * (0.66 if not vert else 0.56), (i % 3) / 2.0) + r.normal(0, 6 * ts)
        x, y = V.p(xw, yw); fs = int(36 * ts); ang = r.normal(0, 0.12)
        w = text_w(s, F_MONOB, fs) + fs * 0.9; h = fs * 1.6
        rise = (1 - ease_out((t - ti) / 0.5)) * 30 * ts
        pts = rot(np.array([(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]), ang) + [x, y + rise]
        poly(img, pts, PAPER, k * a, outline=INK, ow=max(2, 3 * ts))
        blit(img, sprite(s, F_MONOB, fs), x, y + rise, INK, k * a, anchor='c')
        # half buried: a mound of sand over the bottom
        cv2.ellipse(img, (int(x), int(y + h * 0.55)), (int(w * 0.55), int(h * 0.35)), 0, 180, 360, (SANDW * 0.85 * (k * a) + 0).tolist(), -1, cv2.LINE_AA) if False else None
    # every string: tangled pieces of string in the sand
    sk = sstep(T_STRING - 0.1, T_STRING + 0.4, t) * k
    if sk > 0:
        for j in range(5 if not vert else 3):
            cx = W * (0.15 + 0.7 * j / 4) + 40 * ts * math.sin(j); cy = V.y(hor + (shore - hor) * (0.42 + 0.1 * (j % 2)))
            pts = [(cx + math.cos(u * 4 + j) * 60 * ts * (0.5 + 0.5 * math.sin(u * 2)), cy + math.sin(u * 3 + j) * 18 * ts) for u in np.linspace(0, 6.3, 40)]
            cv2.polylines(img, [np.round(np.array(pts) * 4).astype(np.int32)], False, (hexc('c8a46a') * sk).tolist(), max(2, int(4 * ts)), cv2.LINE_AA, shift=2)
            blit(img, sprite('"string"', F_MONOB, int(30 * ts)), cx, cy - 30 * ts, INK * 0.9, sk * 0.9, anchor='c')

def parking_lot(img, V, t, L, W, H, k, P):
    """A car at dusk, laptop on the trunk, a lamp post. Fix it from the parking lot."""
    if k <= 0.01: return
    ts = L['ts']; vert = L['vert']; shore = V.y(L['shore'])
    # parking lines in perspective
    for i in range(-3, 5):
        x0 = W * 0.5 + i * W * 0.22; x1 = W * 0.5 + i * W * 0.40
        line(img, (x0, shore + 10 * ts), (x1, H), CREAM * 0.8, max(3, 6 * ts), k * 0.55)
    # lamp post
    lx = W * (0.14 if not vert else 0.12); ly = shore + 6 * ts; lh = H * (0.38 if not vert else 0.30)
    line(img, (lx, ly), (lx, ly - lh), hexc('3b3b44'), max(4, 10 * ts), k)
    line(img, (lx, ly - lh), (lx + 60 * ts, ly - lh), hexc('3b3b44'), max(4, 10 * ts), k)
    cone = np.array([(lx + 60 * ts - 14 * ts, ly - lh), (lx + 60 * ts + 14 * ts, ly - lh), (lx + 60 * ts + W * 0.16, H), (lx + 60 * ts - W * 0.12, H)])
    poly(img, cone, LAMP, k * 0.14)
    circ(img, (lx + 60 * ts, ly - lh + 6 * ts), 14 * ts, LAMP, k)
    # the car: body + cabin + wheels
    cx = W * (0.60 if not vert else 0.52); cy = shore + H * (0.10 if not vert else 0.08); cw = W * (0.42 if not vert else 0.78); chh = cw * 0.22
    K.panel(img, cx - cw / 2, cy - chh, cw, chh, hexc('2f5fa8'), k, r=int(chh * 0.25), shadow_op=0.6)
    cab = np.array([(cx - cw * 0.28, cy - chh), (cx - cw * 0.14, cy - chh - cw * 0.14), (cx + cw * 0.22, cy - chh - cw * 0.14), (cx + cw * 0.36, cy - chh)])
    poly(img, cab, hexc('2f5fa8'), k, outline=INK * 0.6, ow=max(2, 3 * ts))
    win_ = np.array([(cx - cw * 0.24, cy - chh - 4 * ts), (cx - cw * 0.12, cy - chh - cw * 0.12), (cx + cw * 0.20, cy - chh - cw * 0.12), (cx + cw * 0.32, cy - chh - 4 * ts)])
    poly(img, win_, hexc('a9d8ff') * 0.75, k * 0.9)
    for wx in (cx - cw * 0.30, cx + cw * 0.30):
        circ(img, (wx, cy), chh * 0.42, INK, k); circ(img, (wx, cy), chh * 0.2, hexc('777777'), k)
    # tail light glow
    circ(img, (cx + cw / 2 - 10 * ts, cy - chh * 0.65), 10 * ts, RED, k)
    # windows down: a little "windows down" chip on the car (hidden joke)
    blit(img, sprite("windows: down · signal: 1 bar", F_MONOB, int(26 * ts)), cx, cy - chh * 0.5, CREAM * 0.9, k * 0.9, anchor='c')
    return (cx - cw * 0.42, cy - chh)   # trunk position for the laptop

def signal_bars(img, t, L, W, H, k):
    if k <= 0.01: return
    ts = L['ts']; vert = L['vert']; cx = W * 0.5; cy = H * (0.30 if not vert else 0.40)
    bw = 44 * ts; gap = 16 * ts
    flick = 0.55 + 0.45 * (1 if math.sin(t * 23) * math.sin(t * 7.3) > -0.3 else 0)
    for i in range(4):
        bh = (40 + 36 * i) * ts; x = cx - (4 * bw + 3 * gap) / 2 + i * (bw + gap)
        on = (i == 0)
        K.panel(img, x, cy - bh, bw, bh, (LIME * flick) if on else hexc('3a3a44'), k, r=int(8 * ts), shadow_op=0.4)
    chip(img, "LTE · 1 bar", cx, cy + 60 * ts, int(36 * ts), INK, LIME, k, path=F_DISPB)
    chip(img, "all I got", cx, cy + 130 * ts, int(34 * ts), INK * 0.8, CREAM, k * sstep(T_GOT - 0.6, T_GOT - 0.2, t), pop=T_GOT - 0.3, t=t, path=F_DISPB)

def fix_panel(img, t, L, W, H, k):
    """The V3 console: terminal, pipeline, cache, graph."""
    if k <= 0.01: return
    ts = L['ts']; vert = L['vert']
    x = W * (0.06 if not vert else 0.05); y = H * (0.10 if not vert else 0.13); w = W * (0.50 if not vert else 0.90); h = H * (0.42 if not vert else 0.30)
    K.panel(img, x, y, w, h, hexc('0f1218'), k * 0.96, r=int(16 * ts), border=hexc('2d3345'), shadow_op=0.55)
    for i, c in enumerate((hexc('ff5f57'), hexc('febc2e'), hexc('28c840'))): circ(img, (x + (30 + i * 28) * ts, y + 28 * ts), 9 * ts, c, k)
    blit(img, sprite("parking-lot-fix — zsh", F_MONOB, int(26 * ts)), x + w / 2, y + 28 * ts, CREAM * 0.6, k, anchor='c')
    cmds = [(T_V3, "$ git revert HEAD", CREAM), (T_REV2 - 0.1, "$ git revert HEAD   # revert the revert", CREAM), (T_CHERRY, "$ git cherry-pick a4f59e1", CREAM),
            (T_PUSH, "$ git push --force-with-lease", YEL), (T_PIPE, "$ ci watch   >> pipeline crawling…", CREAM * 0.8), (T_FLUSH, "$ cache flush --all && svc bounce", CYAN),
            (T_WAIT, "  waiting…", CREAM * 0.6), (T_GREEN2, "[ok] build  [ok] test  [ok] deploy   green on green", GREEN)]
    fs = int(30 * ts); yy = y + 64 * ts; shown = [(tt, s, c) for tt, s, c in cmds if t >= tt][-6:]
    for tt, s, c in shown:
        s2 = K.typed_line(s, t, tt, cps=40)
        blit(img, sprite(s2, F_MONOB if c is not CREAM else F_MONO, fs), x + 24 * ts, yy, c, k); yy += fs * 1.5
    if int(t * 2.5) % 2 == 0: K.panel(img, x + 24 * ts + text_w(shown[-1][1], F_MONO, fs) if shown else x + 24 * ts, yy, fs * 0.5, fs, CREAM, k * 0.8, r=2, shadow_op=0)
    # pipeline stages
    if t >= T_PIPE - 0.1:
        px = x + 24 * ts; py = y + h - 70 * ts; pw = (w - 48 * ts); sw = pw / 3 - 14 * ts
        prog = sstep(T_PIPE, T_WHOOSH - 0.1, t) * 0.55 + sstep(T_WHOOSH, T_WHOOSH + 0.5, t) * 0.45
        if t >= T_GREEN2: prog = 1.0
        for i, nm in enumerate(("build", "test", "deploy")):
            sx = px + i * (sw + 21 * ts); seg = clamp(prog * 3 - i); done = seg >= 0.999
            K.panel(img, sx, py, sw, 48 * ts, hexc('1e2432'), k, r=int(12 * ts), shadow_op=0)
            if seg > 0: K.panel(img, sx, py, sw * seg, 48 * ts, (GREEN if (done or t >= T_GREEN2) else YEL) * 0.9, k, r=int(12 * ts), shadow_op=0)
            blit(img, sprite(("✓ " if done else "") + nm, F_DISPB, int(28 * ts)), sx + sw / 2, py + 24 * ts, INK if seg > 0.5 else CREAM * 0.7, k, anchor='c')
        if T_WHOOSH <= t < T_WHOOSH + 0.6:
            for j in range(6): line(img, (px + pw * (0.1 + 0.15 * j) - (t - T_WHOOSH) * W * 0.6, py + 24 * ts + (j - 2.5) * 8 * ts), (px + pw * (0.2 + 0.15 * j) - (t - T_WHOOSH) * W * 0.6, py + 24 * ts + (j - 2.5) * 8 * ts), WHITE, 4 * ts, k * (1 - (t - T_WHOOSH) / 0.6))

def cache_box(img, t, L, W, H, k):
    if k <= 0.01: return
    ts = L['ts']; vert = L['vert']
    cx = W * (0.78 if not vert else 0.5); cy = H * (0.30 if not vert else 0.52); s = (110 if not vert else 100) * ts
    warm = sstep(T_CACHE, T_CACHE + 0.5, t) * (1 - sstep(T_FLUSH, T_FLUSH + 0.4, t))
    bounce = math.exp(-max(0, t - T_BOUNCE) * 3) * math.sin((t - T_BOUNCE) * 18) if t >= T_BOUNCE else 0
    sq = 1 - 0.25 * bounce; sy = 1 + 0.25 * bounce
    soft_glow(img, cx - s, cy - s, cx + s, cy + s, s * 0.5, ALERT, 0.55 * warm * k)
    K.panel(img, cx - s * sq, cy - s * sy + s * (sy - 1), 2 * s * sq, 2 * s * sy, hexc('2a1e1e') * (1 - warm) + hexc('7a2a1e') * warm, k, r=int(20 * ts), border=ALERT * warm + hexc('444444') * (1 - warm), shadow_op=0.5)
    blit(img, sprite("CACHE", F_DISP, int(44 * ts)), cx, cy - s * 0.45, CREAM, k, anchor='c')
    lab = "STALE · warm" if warm > 0.5 else ("flushed ✓" if t >= T_FLUSH else "cold")
    blit(img, sprite(lab, F_DISPB, int(32 * ts)), cx, cy + s * 0.15, ALERT if warm > 0.5 else GREEN, k, anchor='c')
    # contents flying out on FLUSH
    fk = sstep(T_FLUSH, T_FLUSH + 0.05, t) * (1 - sstep(T_FLUSH + 0.8, T_FLUSH + 1.1, t))
    if fk > 0:
        r = np.random.default_rng(4)
        for i in range(14):
            a = r.random() * 6.28; d = ease_out((t - T_FLUSH) / 0.8) * s * (1.5 + r.random())
            blit(img, sprite(["bad", "old", "state", "v1", "$NULL"][i % 5], F_MONOB, int(26 * ts)), cx + math.cos(a) * d, cy + math.sin(a) * d, ALERT, fk, anchor='c')
    if t >= T_WAIT and t < T_GRAPH:
        ang = (t - T_WAIT) * 7
        for i in range(8):
            a = ang + i * 0.785; circ(img, (cx + math.cos(a) * s * 0.7, cy + s * 0.6 + math.sin(a) * s * 0.18 + s * 0.0), 6 * ts, CREAM * (0.3 + 0.7 * (i / 8)), k)

def graph_panel(img, t, L, W, H, k):
    if k <= 0.01: return
    ts = L['ts']; vert = L['vert']
    x = W * (0.60 if not vert else 0.05); y = H * (0.42 if not vert else 0.45); w = W * (0.34 if not vert else 0.90); h = H * (0.26 if not vert else 0.20)
    K.panel(img, x, y, w, h, hexc('101520'), k * 0.95, r=int(16 * ts), border=hexc('2d3345'), shadow_op=0.5)
    blit(img, sprite("checkout success rate", F_DISPB, int(28 * ts)), x + 20 * ts, y + 14 * ts, CREAM * 0.7, k)
    n = 60; pts = []; back = sstep(T_BACK - 0.05, T_BACK + 0.9, t)
    for i in range(n):
        u = i / (n - 1); dip = sstep(0.25, 0.4, u) * (1 - sstep(0.62, 0.82, u) * back)
        v = 0.92 - 0.75 * dip + 0.02 * math.sin(i * 1.3 + t * 2)
        if u > min(1.0, (t - T_GRAPH) / 1.6): break
        pts.append((x + w * (0.06 + 0.88 * u), y + h * (0.92 - 0.65 * v)))
    if len(pts) > 1:
        col = GREEN if (back > 0.5 and pts[-1][1] < y + h * 0.5) else RED
        cv2.polylines(img, [np.round(np.array(pts) * 4).astype(np.int32)], False, col.tolist(), max(3, int(6 * ts)), cv2.LINE_AA, shift=2)
        circ(img, pts[-1], 9 * ts, col, k)
    lab = "100%" if back > 0.9 else ("recovering…" if back > 0 else ("12%" if t > T_GRAPH + 0.7 else "99.9%"))
    blit(img, sprite(lab, F_DISP, int(40 * ts)), x + w - 20 * ts, y + 14 * ts - 6 * ts, GREEN if back > 0.9 else RED, k, anchor='lt') if False else \
        blit(img, sprite(lab, F_DISP, int(40 * ts)), x + w - 24 * ts - text_w(lab, F_DISP, int(40 * ts)), y + 12 * ts, GREEN if back > 0.9 else (RED if t > T_GRAPH + 0.7 else GREEN), k)

def lighthouse(img, V, t, L, W, H, k, beam=1.0):
    if k <= 0.01: return
    ts = L['ts']; lx, ly = L['light']; x, y = V.p(lx, ly); s = V.sz(1.0)
    hgt = H * (0.30 if not L['vert'] else 0.22) * s; bw = 54 * ts * s
    # rock
    rock = np.array([(x - bw * 2.2, y + 6 * ts), (x - bw * 1.2, y - 22 * ts), (x + bw * 1.3, y - 18 * ts), (x + bw * 2.4, y + 10 * ts)])
    poly(img, rock, hexc('4a4a55'), k, outline=INK, ow=3)
    # tower with stripes
    tower = np.array([(x - bw, y - 16 * ts), (x + bw, y - 16 * ts), (x + bw * 0.7, y - hgt), (x - bw * 0.7, y - hgt)])
    poly(img, tower, CREAM, k, outline=INK, ow=max(2, 3 * ts))
    for i in range(3):
        u0 = 0.15 + i * 0.28; u1 = u0 + 0.14
        w0 = bw * (1 - 0.3 * u0); w1 = bw * (1 - 0.3 * u1); y0 = y - 16 * ts - (hgt - 16 * ts) * u0; y1 = y - 16 * ts - (hgt - 16 * ts) * u1
        poly(img, np.array([(x - w0, y0), (x + w0, y0), (x + w1, y1), (x - w1, y1)]), RED, k)
    # lamp room
    K.panel(img, x - bw * 0.8, y - hgt - 40 * ts, bw * 1.6, 40 * ts, INK, k, r=int(6 * ts), shadow_op=0)
    circ(img, (x, y - hgt - 20 * ts), 16 * ts, YEL, k)
    cap = np.array([(x - bw * 0.95, y - hgt - 40 * ts), (x + bw * 0.95, y - hgt - 40 * ts), (x, y - hgt - 70 * ts)])
    poly(img, cap, RED, k)
    # beam
    if beam > 0.01:
        ang = (t * 0.9) % (2 * math.pi); bx, by = x, y - hgt - 20 * ts; ln = W * 0.9
        a0 = ang;
        tri = np.array([(bx, by), (bx + math.cos(a0 - 0.09) * ln, by + math.sin(a0 - 0.09) * ln * 0.35), (bx + math.cos(a0 + 0.09) * ln, by + math.sin(a0 + 0.09) * ln * 0.35)])
        poly(img, tri, YEL, 0.18 * beam * k)
    blit(img, sprite("PROD", F_DISP, int(34 * ts * s)), x, y - hgt * 0.5, INK, k, anchor='c')

def postmortem_doc(img, t, L, W, H, k):
    if k <= 0.01: return
    ts = L['ts']; vert = L['vert']
    w = W * (0.40 if not vert else 0.86); h = H * (0.50 if not vert else 0.34)
    x = W * ((0.07 if t < T_ROOT - 0.5 else 0.50) if not vert else 0.07); y = H * (0.12 if not vert else 0.14)
    K.panel(img, x, y, w, h, PAPER, k * 0.97, r=int(14 * ts), shadow_op=0.55)
    K.panel(img, x, y, w, 70 * ts, hexc('e9e1cf'), k, r=int(14 * ts), shadow_op=0)
    blit(img, sprite("POSTMORTEM · Monday 9:00", F_DISPB, int(34 * ts)), x + 24 * ts, y + 18 * ts, INK * 0.9, k)
    fs = int(34 * ts); yy = y + 100 * ts; lh = fs * 1.75
    rows = [("Incident", "SEV-1 · Friday 5:03 PM"), ("Impact", "checkout $NULL · 10,000 rows"), ("Blameless", None), ("Root cause", None)]
    for i, (kk, vv) in enumerate(rows):
        blit(img, sprite(kk + ":", F_MONOB, fs), x + 24 * ts, yy, INK * 0.55, k)
        vx = x + 24 * ts + text_w("Root cause:  ", F_MONOB, fs)
        if kk == "Blameless":
            ok = sstep(T_BLAMELESS, T_BLAMELESS + 0.1, t); nope = sstep(T_NOPE3, T_NOPE3 + 0.05, t)
            if nope < 0.5: blit(img, sprite("yes, obviously", F_MONOB, fs), vx, yy, GREEN * 0.8, k * ok)
            else:
                blit(img, sprite("yes, obviously", F_MONOB, fs), vx, yy, INK * 0.35, k); strike(img, vx + text_w("yes, obviously", F_MONOB, fs) / 2, yy + fs * 0.6, text_w("yes, obviously", F_MONOB, fs) + 10 * ts, RED, k, 1.0)
                K.sticker(img, vx + text_w("yes, obviously", F_MONOB, fs) + 150 * ts, yy + fs * 0.55, 0.42 * ts, k * nope, -0.12, age=t - T_NOPE3, text="NOPE")
        elif kk == "Root cause":
            if t >= T_ROOT - 0.2:
                s2 = K.typed_line("me", t, T_ME, cps=6) if t >= T_ME else ""
                blit(img, sprite(s2, F_MONOB, fs), vx, yy, RED, k)
                if int(t * 2.5) % 2 == 0: K.panel(img, vx + text_w(s2, F_MONOB, fs) + 4 * ts, yy + 2 * ts, fs * 0.5, fs * 1.05, INK, k * 0.8, r=2, shadow_op=0)
        else:
            blit(img, sprite(vv, F_MONO, fs), vx, yy, INK * 0.85, k)
        yy += lh

def next_friday(img, t, L, W, H, k):
    if k <= 0.01: return
    ts = L['ts']; vert = L['vert']; cx = W * (0.22 if not vert else 0.5); cy = H * (0.36 if not vert else 0.25)
    cw, ch = 300 * ts, 300 * ts
    flip = ease_io((t - T_NEXTFRI + 0.1) / 0.35) if t >= T_NEXTFRI - 0.1 else 0.0
    sq = abs(math.cos(flip * math.pi)); front = flip < 0.5
    K.panel(img, cx - cw / 2, cy - ch / 2 * sq, cw, ch * sq, PAPER, k, r=int(18 * ts), shadow_op=0.55)
    K.panel(img, cx - cw / 2, cy - ch / 2 * sq, cw, ch * 0.3 * sq, CORAL if front else RED, k, r=int(18 * ts), shadow_op=0)
    if sq > 0.2:
        blit(img, sprite("FRIDAY" if front else "NEXT FRIDAY", F_DISPB, int(34 * ts * min(1, sq * 1.2))), cx, cy - ch * 0.35 * sq, WHITE, k, anchor='c')
        blit(img, sprite("TODAY" if front else "4:59 PM", F_DISP, int(64 * ts * min(1, sq * 1.2))), cx, cy + ch * 0.10 * sq, INK, k, anchor='c')
        if front: K.sticker(img, cx, cy + ch * 0.34 * sq, 0.5 * ts * sq, k, 0.1, age=9, text="NEVER AGAIN")
        else: blit(img, sprite("see you there", F_DISPB, int(28 * ts)), cx, cy + ch * 0.36 * sq, INK * 0.6, k, anchor='c')

def lightning(img, t, W, H, L, k):
    """Bolts on the storm downbeats."""
    if k <= 0.01: return 0.0
    db = TM.downbeats; i = np.searchsorted(db, t) - 1
    if i < 0 or i % 2: return 0.0
    x = t - db[i]
    if x > 0.22: return 0.0
    r = np.random.default_rng(int(db[i] * 10)); ts = L['ts']
    x0 = W * (0.15 + 0.7 * r.random()); y0 = 0; pts = [(x0, y0)]
    while pts[-1][1] < L['hor'] * 0.95:
        pts.append((pts[-1][0] + r.normal(0, 40 * ts), pts[-1][1] + 30 * ts + r.random() * 50 * ts))
    a = (1 - x / 0.22) * k
    cv2.polylines(img, [np.round(np.array(pts) * 4).astype(np.int32)], False, (WHITE * a).tolist(), max(3, int(7 * ts)), cv2.LINE_AA, shift=2)
    cv2.polylines(img, [np.round(np.array(pts) * 4).astype(np.int32)], False, (CYAN * a * 0.6).tolist(), max(6, int(16 * ts)), cv2.LINE_AA, shift=2) if False else None
    return a * 0.5

def rain(img, t, W, H, L, k):
    if k <= 0.01: return
    ts = L['ts']; R = rain_pts(W, H)
    for i, (rx, ry, rs) in enumerate(R):
        y = ((ry + t * (1.2 + rs)) % 1.0) * H; x = (rx + t * 0.05) % 1.0 * W
        line(img, (x, y), (x - 14 * ts, y + 44 * ts), CYAN * 0.8, max(1, 2 * ts), k * (0.35 + 0.4 * rs))

# ---------------------------------------------------------------- the frame
def render_frame(t, W=1920, H=1080, fi=0):
    L = lay(W, H); ts = L['ts']; vert = L['vert']; clean = C.STATE["clean"]
    V = view_for(t, W, H); P = palette(t)
    img = background(t, W, H, V, P)
    st = storm(t); lk = lot_k(t); wl_w = water_level(t, L); wl = V.y(wl_w)
    hor = V.y(L['hor']); shore = V.y(L['shore'])
    fl = 0.0; gl = 0.0
    beach = (1 - lk)

    # ---- far: boardwalk (night), lighthouse (final/outro)
    nightk = sstep(T_V2 - 0.6, T_V2, t) * (1 - sstep(T_BRIDGE - 0.6, T_BRIDGE + 0.6, t))
    slack_boardwalk(img, V, t, L, P, nightk)
    lhk = sstep(T_FINAL - 0.6, T_FINAL + 0.4, t) * (1 - sstep(T_END, T_END + 0.6, t))
    lighthouse(img, V, t, L, W, H, lhk, beam=sstep(T_STANDING, T_DOUBT + 0.3, t) * 0.6 + 0.4)

    # ---- seagulls (verse 1 breeze, outro)
    gk = sstep(T_WINDOWS - 0.3, T_WINDOWS + 0.4, t) * (1 - sstep(T_PAGER + 1.5, T_PAGER + 2.5, t)) + sstep(T_OUTRO_SAIL, T_OUTRO_SAIL + 2, t) * (1 - sstep(T_END, T_END + 0.5, t))
    if gk > 0.01:
        for i in range(5):
            u = ((t * 0.045 * (1 + 0.3 * i) + i * 0.21) % 1.2) - 0.1
            seagull(img, W * u, H * (0.16 + 0.07 * i) + math.sin(t * 2 + i) * 10 * ts, (18 + 6 * (i % 3)) * ts * (1.3 if vert else 1.0), INK * 0.8, gk, flap=0.5 + 0.5 * math.sin(t * 9 + i))

    # ---- beach objects (drawn before the tide so they go under); they stay under for the night and come back for 4:59
    objk = beach * ((1 - sstep(T_V2 - 1.2, T_V2 - 0.2, t)) + sstep(T_459B - 0.6, T_459B - 0.1, t))
    objk = min(1.0, objk)
    phonek = beach * ((1 - sstep(T_V2 - 1.2, T_V2 - 0.2, t)) + sstep(T_BUZZ2 - 0.7, T_BUZZ2 - 0.2, t) * (1 - sstep(T_CH2 + 2.0, T_CH2 + 3.0, t)))
    phonek = min(1.0, phonek)
    if beach > 0.01:
        # laptop: lid open for the intro, half shut from V1, dashboard red in the choruses, closes at the end
        lid = 1.0
        lid = lerp(lid, 0.55, sstep(T_V1 - 0.2, T_V1 + 0.6, t))
        lid = lerp(lid, 1.0, sstep(T_LOOKED, T_LOOKED + 0.5, t))
        lid = lerp(lid, 0.0, sstep(T_CLOSE, T_CLOSE + 0.8, t)) if lk < 0.5 else lid
        lid = lerp(lid, 1.0, sstep(T_459B, T_459B + 0.7, t))
        press = sstep(T_SHIP - 0.05, T_SHIP + 0.05, t) * (1 - sstep(T_SHIP + 0.25, T_SHIP + 0.4, t))
        prog = sstep(T_SHIP + 0.1, T_IT, t) if t >= T_SHIP + 0.1 else 0.0
        if t < T_IT + 0.6 or t >= T_459B:
            scr = shipit_screen(t, V, L, press, prog if t < T_IT + 0.6 else 0.0)
        elif t >= T_LOOKED: scr = dashboard_screen(t, L)
        else: scr = shipped_screen(t, V, L)
        if objk > 0.01:
            laptop(img, V, t, L, lid, objk, screen=scr, glow=0.0)
            coffee(img, V, t, L, steam=1 - sstep(T_COFFEE, T_COFFEE + 1.2, t), op=objk)
        # phone on the sand: face-down until "I looked", buzzing from "Pager on my hip"
        buzz = sstep(T_PAGER + 0.3, T_PAGER + 0.5, t) * (1 - sstep(T_LOOKED + 0.3, T_LOOKED + 0.6, t)) * (0.6 + 0.4 * bp(t, 10))
        buzz += sstep(T_BUZZ2 - 0.1, T_BUZZ2, t) * (1 - sstep(T_COOKED + 0.4, T_COOKED + 0.8, t))
        buzz = min(1.0, buzz)
        face_up = T_LOOKED - 0.05 <= t < T_V2 + 1.0 or T_COOKED - 0.2 <= t < T_CH2 + 3 or t >= T_PHONE - 0.05
        hot = sstep(T_COOKED - 0.1, T_COOKED + 0.2, t) * (1 - sstep(T_CH2 + 1.0, T_CH2 + 2.5, t))
        n_alerts = int(sstep(T_PAGER, T_LOOKED, t) * 7) + (int((t - T_BUZZ2) * 40) if t >= T_BUZZ2 else 0)
        ps = None
        if t >= T_PHONE - 0.05: ps = alert_screen(L, "1", "quick", "question", col=SLACKB)
        elif t >= T_COOKED - 0.2: ps = alert_screen(L, "99+", "SEV-1", "I'm cooked")
        elif t >= T_LOOKED - 0.05: ps = alert_screen(L, str(min(99, max(1, n_alerts))), "SEV-1", "prod down")
        if phonek > 0.01 and t < T_V2: phone(img, V, t, L, face_up, buzz, phonek, screen=ps, hot=hot, lit=0.5)
        pre2 = (phonek, face_up, buzz, ps, hot)

    # ---- parking lot (bridge/V3) sits where the beach was
    trunk = parking_lot(img, V, t, L, W, H, lk, P) if lk > 0.01 else None
    if trunk is not None:
        lidl = lerp(1.0, 0.0, sstep(T_CLOSE, T_CLOSE + 0.8, t))
        L2 = dict(L); L2['lap'] = (trunk[0], trunk[1]); L2['lapw'] = L['lapw'] * 0.72
        term = [("$ git revert HEAD", CREAM), ("$ git revert HEAD", CREAM), ("$ git cherry-pick a4f59e1", CREAM), ("$ git push", YEL)]
        tl = [l for i, l in enumerate(term) if t >= [T_V3, T_REV2, T_CHERRY, T_PUSH][i]] + [("$ " + ("_" if int(t * 2.5) % 2 == 0 else ""), CREAM * 0.8)]
        laptop(img, View(W, H), t, L2, lidl, lk, screen=terminal_screen(t, L, tl), glow=0.5 * lidl, col=hexc('3a3a44'))
        phone(img, View(W, H), t, dict(L, phone=(W * (0.86 if not vert else 0.86), trunk[1] + 6 * ts)), t >= T_PHONE - 0.05, sstep(T_PHONE - 0.1, T_PHONE, t) * (1 - sstep(T_QQ + 0.6, T_QQ + 0.9, t)), lk * sstep(T_PHONE - 0.4, T_PHONE - 0.1, t), screen=alert_screen(L, "1", "quick", "question", col=SLACKB) if t >= T_PHONE - 0.05 else None, lit=sstep(T_PHONE, T_PHONE + 0.2, t))

    if lk > 0.5 and t >= T_PHONE - 0.05:
        qk = sstep(T_PHONE, T_PHONE + 0.15, t) * (1 - sstep(T_FINAL - 0.9, T_FINAL - 0.4, t))
        K.bubble(img, W * (0.70 if not vert else 0.5), H * (0.40 if not vert else 0.45), "VP: quick question for you", qk, ts, col=SLACKB * 0.85, fs=int(40 * ts), pop_t=T_PHONE, t=t, text_col=INK)

    # ---- low tide: the exposed seabed and its artifacts
    seabed_artifacts(img, V, t, L, W, H, sstep(T_LOW + 0.6, T_LOW + 1.0, t) * (1 - lk) * (1 - sstep(T_FINAL - 1.2, T_FINAL - 0.5, t)))

    # ---- the tide comes in over everything above
    tide_overlay(img, t, W, H, V, P, wl_w)

    # ---- the pager, held up out of the water for "I'm cooked"
    if beach > 0.01 and t >= T_V2 and pre2[0] > 0.01:
        L2 = dict(L); L2['phone'] = (L['phone'][0], wl_w + 150 * ts)
        phone(img, V, t, L2, pre2[1], pre2[2], pre2[0], screen=pre2[3], hot=pre2[4], lit=0.6)

    # ---- cursor "me": clicks SHIP IT, then sits on the beach, swims in the chorus, hides in V2, ends hovering again
    if t < T_IT + 0.9:
        lx, ly = L['lap']; lw = L['lapw']
        bx, by = lx + lw * 0.0, ly - lw * 0.055 - lw * 0.62 * 0.42
        sx, sy = lerp(lx + lw * 0.32, bx + lw * 0.02, ease_io((t - 5.2) / 1.9)), lerp(ly - lw * 0.08, by + lw * 0.02, ease_io((t - 5.2) / 1.9))
        cursor(img, V, sx, sy, 34 * ts * (1 - 0.12 * press), 1.0, WHITE)
    else:
        swim = sstep(T_UNDER1 - 0.2, T_UNDER1 + 0.6, t) * (1 - sstep(T_V2 - 1.0, T_V2 - 0.2, t)) + sstep(T_UNDER2 - 0.2, T_UNDER2 + 0.6, t) * (1 - sstep(T_CH2_VOX_END, T_CH2_VOX_END + 1.0, t))
        swim = min(1.0, swim)
        sitx, sity = L['cursor_sit']; sity = min(sity, wl_w - 10 * ts)
        sx = lerp(sitx, W * (0.48 if not vert else 0.5), swim); sy = lerp(sity, wl_w - 6 * ts, swim) + math.sin(t * 6) * 8 * ts * swim
        ang = math.sin(t * 7) * 0.5 * swim
        vis = beach * (1 - sstep(T_V2 + 0.5, T_V2 + 1.2, t) * (1 - swim)) * (1 - sstep(T_BRIDGE - 0.5, T_BRIDGE, t)) + sstep(T_FINAL, T_FINAL + 0.5, t) * (1 - lk) * (1 - sstep(T_END, T_END + 0.3, t))
        vis = min(1.0, vis)
        if t >= T_OUTRO_SAIL + 1.0:   # the loop: drifting back toward SHIP IT
            lx, ly = L['lap']; lw = L['lapw']; bx, by = lx + lw * 0.02, ly - lw * 0.055 - lw * 0.62 * 0.42 + lw * 0.02
            kk = ease_io((t - T_OUTRO_SAIL - 1.0) / (T_END - 1.5 - T_OUTRO_SAIL - 1.0)); sx = lerp(sx, bx, kk); sy = lerp(sy, by, kk) + math.sin(t * 1.5) * 4 * ts
        if swim > 0.3:   # splashes
            for i in range(4):
                a = (t * 9 + i * 1.6) % 6.28; circ(img, (sx + math.cos(a) * 40 * ts, wl - 4 * ts - abs(math.sin(a)) * 24 * ts), 5 * ts, WHITE, vis * swim * 0.8)
        cursor(img, V, sx, sy, 34 * ts, vis, WHITE, a=ang)
        if swim > 0.5 and not clean:
            chip(img, "learning to swim", sx + 10 * ts, wl - 86 * ts, int(34 * ts), INK, CYAN, vis * sstep(T_SWIM1 - 0.3, T_SWIM1, t) * (1 - sstep(T_ROLL1, T_ROLL1 + 0.3, t)) if t < T_CH2 else vis * sstep(T_UNDER2 + 1.5, T_UNDER2 + 1.8, t) * (1 - sstep(T_ROLL2, T_ROLL2 + 0.3, t)), path=F_DISPB)

    # ---- the boat: launches at "it", sails, capsizes in the choruses, comes back upright for the final
    if t >= T_SHIP + 0.1:
        lx, ly = L['lap']; lw = L['lapw']; scx, scy = lx, ly - lw * 0.055 - lw * 0.62 * 0.5
        bx0, bx1 = L['boat_x0'], L['boat_x1']
        launch = ease_io((t - T_IT) / 1.3)
        sail = clamp((t - T_IT - 1.3) / (T_V1 - T_IT - 1.3))
        x = lerp(scx, bx0, launch); x = lerp(x, bx1, ease_io(sail)) if t > T_IT + 1.3 else x
        x += math.sin(t * 0.25) * 30 * ts * sstep(T_V1, T_V1 + 3, t)
        surf = wl_w if t >= T_CH1 - 0.5 else L['hor'] + (L['shore'] - L['hor']) * L['boat_y']
        y = lerp(scy, surf, launch) - (1 - abs(2 * launch - 1)) * H * 0.12
        s = lerp(lw * 0.22, (100 if not vert else 100) * ts, launch)
        bob = math.sin(t * 2.1) * 4 * ts + math.sin(t * 3.7) * 3 * ts
        tilt = math.sin(t * 1.3) * 0.06 + math.sin(t * 2.9) * 0.04 * (1 + 3 * st)
        cap = sstep(T_UNDER1, T_UNDER1 + 1.1, t) * (1 - sstep(T_V2 - 1.5, T_V2 - 0.2, t)) * 0.3
        cap += sstep(T_UNDER2, T_UNDER2 + 1.0, t) * (1 - sstep(T_FINAL - 0.6, T_STANDING, t)) * 1.0
        cap = min(1.0, cap)
        rock = (sstep(T_CH1 - 0.2, T_CH1 + 0.5, t) * (1 - sstep(T_V2 - 1.5, T_V2 - 0.5, t)) + st) * math.sin(t * 5.5) * 0.35
        pre_hidden = sstep(T_IT, T_IT + 0.05, t)
        fade = (1 - lk) * (1 - sstep(T_END, T_END + 0.5, t))
        if T_BRIDGE <= t < T_FINAL - 0.6:   # stranded on the exposed seabed, lying on its side
            lw_ = low_k(t); y = lerp(y, L['hor'] + (L['shore'] - L['hor']) * (0.62 if not vert else 0.50), lw_); tilt = lerp(tilt, 0.42, lw_); cap = cap * (1 - lw_)
            x = lerp(x, W * (0.62 if not vert else 0.6), lw_)
        if t >= T_OUTRO_SAIL:   # sails off toward the sun
            x = lerp(bx1, W * (0.70 if not vert else 0.7), ease_io((t - T_OUTRO_SAIL) / 14)); s *= lerp(1.0, 0.45, ease_io((t - T_OUTRO_SAIL) / 14)); y = lerp(surf, L['hor'] + 10 * ts, ease_io((t - T_OUTRO_SAIL) / 14))
        chk = sstep(T_CH1 - 0.3, T_CH1 + 0.6, t) * (1 - sstep(T_V2 - 1.0, T_V2, t)) + sstep(T_CH2 - 0.3, T_CH2 + 0.6, t) * (1 - sstep(T_CH2_VOX_END, T_CH2_VOX_END + 1.0, t))
        pulse = (1 + 0.05 * bp(t) * sstep(T_CH1, T_CH1 + 0.1, t)) * (1 + 0.45 * min(1.0, chk))
        paper_boat(img, V, x, y + bob * pre_hidden, s * pulse, tilt + rock, fade * pre_hidden + (1 - pre_hidden), label="#459", capsize=cap, sink=0.25 * cap + 0.15 * st)
        # sticky little diff tag on the boat during V1
        tagk = sstep(T_CHANGE, T_CHANGE + 0.3, t) * (1 - sstep(T_NOTICKET, T_NOTICKET + 0.3, t))
        if tagk > 0: chip(img, "+1  −1", V.x(x) + s * 1.6, V.y(y) - s * 1.2, int(34 * ts), YEL, INK, tagk, pop=T_CHANGE, t=t, path=F_DISPB)

    # ---- the life ring on a rope (choruses), cut loose in the final
    ringk = sstep(T_ROLL1, T_ROLL1 + 0.05, t) * (1 - sstep(T_V2 - 1.2, T_V2 - 0.4, t)) + sstep(T_ROLL2, T_ROLL2 + 0.05, t) * (1 - sstep(T_CH2_VOX_END + 0.5, T_CH2_VOX_END + 1.5, t)) + sstep(T_ROLL3, T_ROLL3 + 0.05, t) * (1 - sstep(T_MONDAY + 1.5, T_MONDAY + 2.5, t))
    ringk = min(1.0, ringk)
    if ringk > 0.01:
        t0 = T_ROLL3 if t >= T_ROLL3 else (T_ROLL2 if t >= T_ROLL2 else T_ROLL1)
        rx, ry = L['ring']; drop = ease_out((t - t0) / 0.45)
        yy_ = lerp(-H * 0.2, wl_w - 10 * ts, drop) + math.sin(t * 2.5) * 6 * ts
        rope_from = (rx + 60 * ts, -10) if t < T_CUT else None
        if t >= T_CUT: yy_ += (t - T_CUT) * 30 * ts; rx += (t - T_CUT) * 60 * ts
        if t >= T_ROLL3: yy_ = min(yy_, L['hor'] + (L['shore'] - L['hor']) * 0.55)
        life_ring(img, V, t, L, rx, yy_, 78 * ts, ringk, rope_from=rope_from, sway=1.0 - drop * 0.5)
        if T_CUT - 0.5 <= t < T_CUT + 0.6:   # scissors snip
            k2 = sstep(T_CUT - 0.5, T_CUT - 0.2, t) * (1 - sstep(T_CUT + 0.3, T_CUT + 0.6, t)); px, py = V.p(rx + 60 * ts * 0.45, yy_ - 200 * ts)
            open_ = 0.55 * (1 - sstep(T_CUT - 0.05, T_CUT + 0.05, t))
            for sgn in (-1, 1):
                a_ = 1.25 + sgn * open_; d = np.array([math.cos(a_), -math.sin(a_)]); n_ = np.array([-d[1], d[0]])
                blade = np.array([[px, py], [px, py] + d * 130 * ts, [px, py] + d * 118 * ts + n_ * sgn * 18 * ts, [px, py] + d * 20 * ts + n_ * sgn * 14 * ts])
                poly(img, blade, hexc('d9dde8'), k2, outline=INK, ow=max(2, 3 * ts))
                circ(img, (px - d[0] * 42 * ts, py - d[1] * 42 * ts), 26 * ts, CORAL, k2, th=max(5, int(10 * ts)))
            circ(img, (px, py), 6 * ts, INK, k2)

    # ---- verse-1 floaters: checklist, green check, merged pill, pager
    if T_NOTICKET - 0.3 < t < T_LOOKED + 1.6 and beach > 0.5:
        cy = H * (0.22 if not vert else 0.33)
        items = [("ticket", T_NOTICKET), ("test", T_NOTEST), ("second pair of eyes", T_NOEYES)]
        for i, (s, tt) in enumerate(items):
            k = sstep(tt, tt + 0.1, t) * (1 - sstep(T_COFFEE - 0.3, T_COFFEE, t))
            if k <= 0: continue
            cx = W * (0.5 + (i - 1) * (0.22 if not vert else 0.31))
            if vert and i == 2: cx = W * 0.5; cy2 = cy + 70 * ts
            else: cy2 = cy
            w = chip(img, "no " + s, cx, cy2, int(36 * ts), PAPER, INK, k, pop=tt, t=t, path=F_DISPB) or 0
            strike(img, cx, cy2, w * 0.9, RED, k, sstep(tt + 0.15, tt + 0.4, t))
        gk2 = sstep(T_GREEN, T_GREEN + 0.1, t) * (1 - sstep(T_COFFEE - 0.3, T_COFFEE, t))
        if gk2 > 0:
            cx, cy3 = W * 0.5, H * (0.36 if not vert else 0.43); pop = 1 + 0.4 * math.exp(-max(0, t - T_GREEN) * 7)
            circ(img, (cx, cy3), 46 * ts * pop, GREEN, gk2); blit(img, sprite("✓", F_DISP, int(62 * ts * pop)), cx, cy3, WHITE, gk2, anchor='c')
            # shifty eyes on the check: the lie
            ex = 10 * ts * math.sin(t * 5) * sstep(T_LIES - 0.4, T_LIES, t)
            for sgn in (-1, 1): circ(img, (cx + sgn * 16 * ts, cy3 - 20 * ts), 7 * ts, WHITE, gk2 * sstep(T_LIES - 0.5, T_LIES - 0.2, t)); circ(img, (cx + sgn * 16 * ts + ex, cy3 - 20 * ts), 3.5 * ts, INK, gk2 * sstep(T_LIES - 0.5, T_LIES - 0.2, t))
            chip(img, "all checks passed*", cx, cy3 + 86 * ts, int(34 * ts), INK, GREEN, gk2, path=F_DISPB)
            blit(img, sprite("*tests skipped", F_MONOB, int(26 * ts)), cx, cy3 + 130 * ts, CREAM * 0.8, gk2 * sstep(T_LIES - 0.2, T_LIES, t), anchor='c')
        mk = sstep(T_MERGE, T_MERGE + 0.1, t) * (1 - sstep(T_PAGER - 0.3, T_PAGER, t))
        if mk > 0: chip(img, "merged  ·  main", W * 0.5, H * (0.22 if not vert else 0.33), int(38 * ts), hexc('8957e5'), WHITE, mk, pop=T_MERGE, t=t)
        pk = sstep(T_PLEASE - 0.2, T_PLEASE, t) * (1 - sstep(T_LOOKED + 1.2, T_LOOKED + 1.5, t))
        if pk > 0:
            px, py = V.p(*L['phone']); cyp = py - 290 * ts
            if t < T_BUZZ1 + 0.9: chip(img, "pager: please", px, cyp, int(36 * ts), RED, WHITE, pk, pop=T_PLEASE, t=t, path=F_DISPB)
            elif t < T_LOOKED: chip(img, "don't look", px, cyp, int(36 * ts), INK, YEL, pk, pop=T_BUZZ1 + 0.9, t=t, path=F_DISPB)
            else: chip(img, "I looked.", px, cyp, int(36 * ts), RED, WHITE, pk, pop=T_LOOKED, t=t, path=F_DISPB)

    # ---- choruses: dashboard card "red as a sunset" + NOPE
    for tD, tN in ((T_DASH1, T_NOPE1), (T_DASH2, T_NOPE2)):
        dk = sstep(tD, tD + 0.12, t) * (1 - sstep(tN + 1.9, tN + 2.3, t))
        if dk <= 0: continue
        cw, ch = W * (0.30 if not vert else 0.62), H * (0.22 if not vert else 0.15)
        cx, cy = W * (0.20 if not vert else 0.5) , H * (0.22 if not vert else 0.34)
        K.panel(img, cx - cw / 2, cy - ch / 2, cw, ch, hexc('2a0b12'), dk * 0.95, r=int(16 * ts), border=RED, shadow_op=0.55)
        blit(img, sprite("dashboard", F_DISPB, int(30 * ts)), cx - cw / 2 + 20 * ts, cy - ch / 2 + 14 * ts, CREAM * 0.8, dk)
        pts = [(cx - cw / 2 + cw * (0.06 + 0.88 * u), cy + ch * 0.42 - ch * 0.62 * sstep(0.25, 0.6, u) * (0.75 + 0.25 * abs(math.sin(u * 20 + t * 4)))) for u in np.linspace(0, min(1.0, (t - tD) / 1.2), 40)]
        if len(pts) > 1: cv2.polylines(img, [np.round(np.array(pts) * 4).astype(np.int32)], False, RED.tolist(), max(3, int(6 * ts)), cv2.LINE_AA, shift=2)
        blit(img, sprite("errors 100%", F_DISP, int(34 * ts)), cx + cw / 2 - 20 * ts - text_w("errors 100%", F_DISP, int(34 * ts)), cy - ch / 2 + 12 * ts, RED, dk)
        if t >= tN - 0.02: K.sticker(img, cx + cw * 0.22, cy + ch * 0.18, 0.62 * ts * (0.9 if not vert else 0.8), dk, -0.14, age=t - tN, text="NOPE")

    # ---- verse 2 set pieces
    anyk = sstep(T_ANYONE, T_ANYONE + 0.1, t) * (1 - sstep(T_NULL - 0.3, T_NULL, t))
    if anyk > 0:
        K.bubble(img, W * (0.34 if not vert else 0.5), H * (0.26 if not vert else 0.30), "anyone change something?", anyk, ts, col=hexc('3f2b96'), fs=int(40 * ts), pop_t=T_ANYONE, t=t)
        K.bubble(img, W * (0.64 if not vert else 0.5), H * (0.36 if not vert else 0.38), "me: (sitting tight)", anyk * sstep(T_TIGHT - 0.6, T_TIGHT - 0.3, t), ts, col=INK, fs=int(36 * ts), pop_t=T_TIGHT - 0.5, t=t, text_col=YEL)
    null_table(img, t, L, W, H, sstep(T_NULL - 0.1, T_NULL + 0.15, t) * (1 - sstep(T_RETRY - 0.4, T_RETRY - 0.1, t)))
    arrows_at_me(img, t, L, W, H, sstep(T_ROWS + 0.2, T_ROWS + 0.5, t) * (1 - sstep(T_RETRY - 0.4, T_RETRY - 0.1, t)), (V.x(L['cursor_sit'][0]), V.y(min(L['cursor_sit'][1], wl_w - 10 * ts))))
    retry_queue(img, V, t, L, W, H, sstep(T_RETRY - 0.05, T_RETRY, t) * (1 - sstep(T_VP1 - 0.3, T_VP1, t)), wl)
    dead_letter_cup(img, V, t, L, W, H, sstep(T_DEAD - 0.1, T_DEAD, t) * (1 - sstep(T_BUZZ2 - 0.4, T_BUZZ2 - 0.1, t)))
    vp_typing(img, t, L, W, H, sstep(T_VP1 - 0.1, T_VP1, t) * (1 - sstep(T_BUZZ2 + 0.6, T_BUZZ2 + 1.0, t)))
    fl += 0.5 * math.exp(-max(0, t - T_DROPPED) * 7) * sstep(T_DROPPED, T_DROPPED + 0.02, t)

    # ---- storm
    rain(img, t, W, H, L, st)
    fl += lightning(img, t, W, H, L, st)
    calendar_wall(img, t, L, W, H, sstep(T_WALL - 0.3, T_WALL, t) * (1 - sstep(T_BRIDGE - 0.2, T_BRIDGE + 0.4, t)))

    # ---- bridge: low tide label, signal
    lowk = sstep(T_LOW, T_LOW + 0.1, t) * (1 - sstep(T_FIX - 0.5, T_FIX - 0.2, t))
    if lowk > 0 and not clean: chip(img, "LOW TIDE", W * 0.5, H * (0.20 if not vert else 0.17), int(44 * ts), PAPER, INK, lowk, pop=T_LOW, t=t)
    signal_bars(img, t, L, W, H, sstep(T_BAR - 0.1, T_BAR + 0.1, t) * (1 - sstep(T_V3 - 0.4, T_V3 - 0.1, t)))

    # ---- V3: console, cache, graph
    fix_panel(img, t, L, W, H, sstep(T_V3 - 0.2, T_V3, t) * (1 - sstep(T_FADE - 0.1, T_FADE + 0.5, t)))
    cache_box(img, t, L, W, H, sstep(T_CACHE - 0.1, T_CACHE + 0.1, t) * (1 - sstep(T_GRAPH - 0.3, T_GRAPH, t)))
    graph_panel(img, t, L, W, H, sstep(T_GRAPH - 0.1, T_GRAPH + 0.1, t) * (1 - sstep(T_FADE - 0.1, T_FADE + 0.5, t)))
    dk_ = dark_k(t)
    if dk_ > 0: img *= (1 - dk_)
    if T_SEA - 0.2 <= t < T_PHONE and not clean:
        chip(img, "🌊" if False else "( hear the sea )", W * 0.5, H * (0.40 if not vert else 0.45), int(40 * ts), INK * 0.6, CREAM, sstep(T_SEA - 0.2, T_SEA, t) * (1 - sstep(T_PHONE - 0.4, T_PHONE - 0.1, t)), path=F_DISPB)

    # ---- final: postmortem, next friday
    postmortem_doc(img, t, L, W, H, sstep(T_MONDAY - 0.1, T_MONDAY + 0.15, t) * (1 - sstep(T_NEVER3 + 2.4, T_NEVER3 + 2.9, t)) + sstep(T_ROOT - 0.3, T_ROOT - 0.1, t) * (1 - sstep(T_OUTRO_SAIL - 0.3, T_OUTRO_SAIL + 0.4, t)))
    next_friday(img, t, L, W, H, sstep(T_SEEYOU - 0.1, T_SEEYOU + 0.1, t) * (1 - sstep(T_ROOT - 0.3, T_ROOT - 0.1, t)))

    # ---- HUD: clock + the never-again tally
    if not clean:
        clock_chip(img, t, W, H, L, 1 - sstep(T_END - 0.3, T_END, t))
        tally_chip(img, t, L, 1 - sstep(T_END - 0.3, T_END, t))

    # ---- big moments: 4:59 and SHIP IT as kinetic type, the launch flash
    if not clean:
        k459 = sstep(T_459 - 0.05, T_459 + 0.05, t) * (1 - sstep(T_459 + 2.6, T_459 + 3.1, t))
        if k459 > 0:
            pop = 1 + 0.35 * math.exp(-max(0, t - T_459) * 8)
            fs = int((200 if not vert else 150) * ts * pop)
            sp = sprite("4:59", F_DISP, fs, 14); cx, cy = W * 0.5, H * (0.16 if not vert else 0.24)
            shadow(img, sp, cx - sp[0].shape[1] / 2 + sp[2] + 6 * ts, cy - sp[0].shape[0] / 2 + sp[2] + 8 * ts, k459)
            blit(img, sp, cx, cy, CREAM, k459, 0.8 * k459, glow_color=CORAL, anchor='c')
            chip(img, "FRIDAY · PM", cx, cy + fs * 0.70, int(38 * ts), INK, CREAM, k459 * sstep(T_459 + 0.3, T_459 + 0.5, t), pop=T_459 + 0.3, t=t, path=F_DISPB)
        ks = sstep(T_SHIP, T_SHIP + 0.03, t) * (1 - sstep(T_IT + 0.9, T_IT + 1.3, t))
        if ks > 0:
            pop = 1 + 0.4 * math.exp(-max(0, t - T_SHIP) * 7) + 0.4 * math.exp(-max(0, t - T_IT) * 7) * sstep(T_IT, T_IT + 0.01, t)
            fs = int((150 if not vert else 120) * ts * pop); cx, cy = W * 0.5, H * (0.16 if not vert else 0.24)
            lab = "SHIP IT" if t >= T_IT else "SHIP"
            sp = sprite(lab, F_DISP, fs, 14)
            shadow(img, sp, cx - sp[0].shape[1] / 2 + sp[2] + 6 * ts, cy - sp[0].shape[0] / 2 + sp[2] + 8 * ts, ks)
            blit(img, sp, cx, cy, LIME, ks, 0.9 * ks, glow_color=GREEN, anchor='c')
        fl += 0.9 * math.exp(-max(0, t - T_IT) * 6) * sstep(T_IT, T_IT + 0.01, t) + 0.35 * math.exp(-max(0, t - T_SHIP) * 8) * sstep(T_SHIP, T_SHIP + 0.01, t)
        fl += 0.5 * math.exp(-max(0, t - T_LOOKED) * 7) * sstep(T_LOOKED, T_LOOKED + 0.01, t)
        fl += 0.4 * math.exp(-max(0, t - T_ME) * 6) * sstep(T_ME, T_ME + 0.01, t)

    # ---- lyrics, FRIDAY stamps, subscribe asks
    if not clean:
        night = P[10]
        active = LYR_DAY * (1 - night) + LYR_NIGHT * night
        if T_V3 - 0.5 < t < T_FINAL - 0.5: active = LYR_FIX
        glow = CORAL * (1 - night) + CYAN * night
        # FRIDAY stamp caption from the line being sung
        s_, i_ = TM.last_stamp(t); cap = ""
        if s_ is not None:
            Ls = [Lx for Lx in TM.lines if Lx['s'] - 0.4 <= s_ + 0.2 <= Lx['e'] + 0.3]
            if Ls:
                tx = Ls[0]['text']
                cap = "I DEPLOYED ON A" if tx.startswith("I deployed") else ("SAID THAT LAST" if tx.startswith("Said") else ("SEE YOU NEXT" if tx.startswith("See") else ""))
        C.overlay_stamp(img, t, W, H, TM, word="FRIDAY", caption=cap, caption_above=True, glow_color=glow)
        C.overlay_lyrics(img, t, W, H, TM, active=active, glow=glow)
        C.subscribe_pill(img, t, W, H, S["V2"]['s'] + 0.5, 5.5)
        C.end_screen(img, t, W, H, T_END, DUR - T_END, "Root cause: me.", sub_line="Subscribe before next Friday", title="Deployed on a Friday", accent=CORAL)

    gl = 0.35 * sstep(T_DROPPED, T_DROPPED + 0.02, t) * math.exp(-max(0, t - T_DROPPED) * 5) + 0.25 * st * bp(t, 9) * sstep(T_UNDER2, T_UNDER2 + 0.1, t)
    return C.finish(img, t, fi, DUR, flash=min(1.0, fl), flash_col=CREAM, glitch_amt=gl, ca=0.0016)
