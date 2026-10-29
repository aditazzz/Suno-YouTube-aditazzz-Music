"""Studio core: shared helpers every song scene can use.

A song scene module (songs/<slug>/scene.py) must expose:
    render_frame(t: float, W: int, H: int, fi: int) -> np.uint8 array (H, W, 3) RGB
and should draw lyrics with core.overlay_lyrics / core.overlay_stamp so the
pipeline can (a) hide overlays for thumbnails (STATE['clean']) and
(b) filter lyric lines at edit joins (STATE['lyric_filter']).
"""
import os, json, math, re
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(ROOT, "assets", "fonts")
F_INTER = os.path.join(FONTS, "Inter-SemiBold.otf")
F_INTER_L = os.path.join(FONTS, "Inter-Medium.otf")
F_DISP = os.path.join(FONTS, "InterDisplay-Black.otf")
F_DISPB = os.path.join(FONTS, "InterDisplay-Bold.otf")
F_MONO = os.path.join(FONTS, "JBMono-400.ttf")
F_MONOB = os.path.join(FONTS, "JBMono-700.ttf")
FPS = 30

# Pipeline-controlled switches (set by render/cuts/thumbs, read by scenes)
STATE = {"clean": False, "lyric_filter": None,
         "platform": os.environ.get("STUDIO_PLATFORM", "")}   # "youtube": 9:16 end card asks to subscribe instead of the Instagram follow

# Readability rules (thin/small text is hard to read on a phone):
#   lyrics >= 64 px (16:9) / 58 px (9:16) at 1080p, SemiBold, dark shadow
#   any text meant to be READ (UI cards, labels, jokes) >= 34 px at 1080p and bold weight; tiny text only for pure texture
MIN_READ = 34

# 9:16 safe zone, as fractions of the 1080x1920 frame. On a phone, YouTube Shorts, Instagram Reels and TikTok scale the
# video to the screen height and crop ~9% off each side, then draw their own controls over the picture:
#   top     the back / search / menu bar, down to ~12% H                       -> nothing to read above `top`
#   bottom  channel name, title, caption, related-video chip, from ~70% H down -> nothing to read below `bottom`
#   left / right   the crop                                                    -> nothing to read outside them
#   buttons the like / comment / save / share column, x > 80% W from ~50% H down
# Measured on an iPhone (Oct 23, 2026): a lyric placed at 8.5% H sat under the back arrow and the search icon.
# Lyrics, titles, hooks and cards stay inside; `python -m studio.safezone songs/<slug>` checks every lyric line of a
# song before its 9:16 render (studio.render refuses to start a 9:16 render without a passing, up-to-date check).
SAFE_9x16 = dict(top=0.13, bottom=0.70, left=0.10, right=0.90, buttons_x=0.80, buttons_y=0.50)

def safe_place_9x16(cx, cy, maxw, rows=1, lh=0.04):
    """Clamp a text block (center x, center y, max width, as frame fractions; `rows` lines of height `lh`) into the
    9:16 safe zone. Returns (cx, cy, maxw)."""
    S = SAFE_9x16; half_h = rows * lh / 2
    cy = min(max(cy, S['top'] + half_h), S['bottom'] - half_h)
    right = S['buttons_x'] if cy + half_h > S['buttons_y'] else S['right']
    left = S['left'] + 0.01; right -= 0.01
    maxw = min(maxw, right - left)
    cx = min(max(cx, left + maxw / 2), right - maxw / 2)
    return cx, cy, maxw

def fit_9x16(box_of, cx, cy, mw, W=1080, H=1920):
    """Move / re-wrap a text block until it sits inside SAFE_9x16. box_of(cx, cy, mw) -> pixel box (x0, y0, x1, y1) of
    the block laid out there. A block that is already safe comes back unchanged, so fixing a scene only moves the lines
    that were in the way."""
    S = SAFE_9x16; m = 0.012
    for _ in range(12):
        b = box_of(cx, cy, mw)
        if not safe_violations(b, W, H): break
        x0, y0, x1, y1 = b[0] / W, b[1] / H, b[2] / W, b[3] / H
        right = (S['buttons_x'] if y1 > S['buttons_y'] else S['right']) - m; left = S['left'] + m
        if x1 - x0 > right - left: mw = min(mw, right - left) * 0.97          # too wide: wrap onto more rows
        elif x0 < left: cx += left - x0                                       # slide it in from the crop
        elif x1 > right: cx -= x1 - right
        if y0 < S['top'] + m: cy += S['top'] + m - y0                         # out from under the top bar
        elif y1 > S['bottom'] - m: cy -= y1 - (S['bottom'] - m)               # up off the caption block
    return cx, cy, mw

def safe_violations(box, W=1080, H=1920):
    """box = (x0, y0, x1, y1) in pixels of a 9:16 frame -> list of the safe-zone rules it breaks."""
    S = SAFE_9x16; x0, y0, x1, y1 = box[0] / W, box[1] / H, box[2] / W, box[3] / H; v = []
    if y0 < S['top']: v.append('top bar')
    if y1 > S['bottom']: v.append('bottom captions')
    if x0 < S['left']: v.append('left crop')
    if x1 > S['right']: v.append('right crop')
    elif x1 > S['buttons_x'] and y1 > S['buttons_y']: v.append('buttons')
    return v

# ------------------------------------------------------------------ math
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def sstep(a, b, x):
    t = clamp((x - a) / (b - a)) if b != a else float(x >= a)
    return t * t * (3 - 2 * t)
def ease_out(t): t = clamp(t); return 1 - (1 - t) ** 3
def ease_io(t): t = clamp(t); return t * t * t * (t * (6 * t - 15) + 10)
def win(t, a, b, fi=0.3, fo=0.3): return sstep(a - fi, a, t) * (1 - sstep(b, b + fo, t))
def lerp(a, b, t): return a + (b - a) * t
def hexc(h): h = h.lstrip('#'); return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)], np.float32)
norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())

ICE = hexc('5fd8ff'); ICE2 = hexc('a8f0ff'); WHITE = np.array([1, 1, 1], np.float32)
RED = hexc('ff2a3d'); MAG = hexc('ff3fbf'); VIO = hexc('8b5cff'); GOLD = hexc('ffc35a')
TEAL = hexc('2bffc6'); NAVY = hexc('050a1c'); IVORY = hexc('f3ead8'); AMBER = hexc('ff8a3d')

# ------------------------------------------------------------------ timing
class Timing:
    """Loads songs/<slug>/build/{timed,beats}.json produced by studio.sync."""
    def __init__(self, song_dir):
        b = os.path.join(song_dir, "build")
        self.lines = json.load(open(os.path.join(b, "timed.json")))
        bt = json.load(open(os.path.join(b, "beats.json")))
        self.beats = np.array(bt["beats"]); self.downbeats = np.array(bt["downbeats"])
        self.tempo = bt["tempo"]; self.duration = bt["duration"]
        self.sections = json.load(open(os.path.join(b, "sections.json")))
        self.stamp_word = None
        self.stamps = []

    def line_t(self, sub, nth=0):
        hits = [L for L in self.lines if sub.lower() in L['text'].lower()]
        return hits[nth]['s']
    def word_t(self, sub, word, nth=0):
        L = [L for L in self.lines if sub.lower() in L['text'].lower()][nth]
        for w, t in zip(L['words'], L['wt']):
            if norm(w) == norm(word): return t
        raise KeyError(word)
    def section(self, name, nth=0):
        hits = [s for s in self.sections if s['name'] == name]
        return hits[nth]
    def section_at(self, t):
        for s in self.sections:
            if s['s'] <= t < s['e']: return s['name']
        return self.sections[-1]['name']
    def snap(self, t, tol=0.32):
        i = np.argmin(abs(self.beats - t))
        return float(self.beats[i]) if abs(self.beats[i] - t) < tol else t
    def beat_pulse(self, t, k=7.0):
        i = np.searchsorted(self.beats, t) - 1
        return math.exp(-(t - self.beats[i]) * k) if i >= 0 else 0.0
    def set_stamp_word(self, word):
        """Every sung occurrence of `word` becomes a big title hit (like UNDROP)."""
        self.stamp_word = norm(word)
        st = []
        for L in self.lines:
            for w, tt in zip(L['words'], L['wt']):
                if norm(w) == self.stamp_word: st.append(self.snap(tt - 0.12, 0.25))
        st.sort(); fix = []
        for s in st:
            if fix and s - fix[-1] < 0.3:
                nb = self.beats[self.beats > fix[-1] + 0.3]; s = float(nb[0])
            fix.append(s)
        self.stamps = fix
    def last_stamp(self, t):
        i = np.searchsorted(self.stamps, t) - 1
        return (self.stamps[i], i) if i >= 0 else (None, -1)

# ------------------------------------------------------------------ text sprites
_FONTS, _SPR = {}, {}
def font(path, size):
    k = (path, size)
    if k not in _FONTS: _FONTS[k] = ImageFont.truetype(path, size)
    return _FONTS[k]
def text_w(text, path, size): return font(path, size).getlength(text)
def sprite(text, path, size, glow=0, track=0):
    k = (text, path, size, glow, track)
    if k in _SPR: return _SPR[k]
    f = font(path, size)
    if track:
        ws = [f.getbbox(ch)[2] for ch in text]; w = int(sum(ws) + track * (len(text) - 1)) + 4
    else:
        w = f.getbbox(text)[2] + 4
    asc, desc = f.getmetrics(); h = asc + desc + 4; pad = glow * 3
    im = Image.new('L', (w + pad * 2, h + pad * 2), 0); d = ImageDraw.Draw(im)
    if track:
        x = pad
        for ch, cw in zip(text, ws): d.text((x, pad), ch, font=f, fill=255); x += cw + track
    else: d.text((pad, pad), text, font=f, fill=255)
    a = np.asarray(im, np.float32) / 255
    g = cv2.GaussianBlur(a, (0, 0), glow) if glow else None
    if len(_SPR) > 4000: _SPR.clear()
    _SPR[k] = (a, g, pad); return _SPR[k]

def blit(img, spr, x, y, color, op=1.0, glow_op=0.0, glow_color=None, anchor='lt', scale=1.0):
    a, g, pad = spr
    if scale != 1.0:
        a = cv2.resize(a, None, fx=scale, fy=scale)
        if g is not None: g = cv2.resize(g, None, fx=scale, fy=scale)
        pad *= scale
    h, w = a.shape
    if anchor == 'c': x -= w / 2; y -= h / 2
    else: x -= pad; y -= pad
    x, y = int(round(x)), int(round(y)); H, W = img.shape[:2]
    x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0: return
    sa = a[y0 - y:y1 - y, x0 - x:x1 - x][..., None]; reg = img[y0:y1, x0:x1]
    if g is not None and glow_op > 0:
        reg += g[y0 - y:y1 - y, x0 - x:x1 - x][..., None] * glow_op * (glow_color if glow_color is not None else color)
    reg *= (1 - sa * op); reg += sa * op * color

def shadow(img, spr, x, y, op):
    a, g, pad = spr
    if g is None: return
    x = int(round(x - pad)); y = int(round(y - pad)); h, w = g.shape; H, W = img.shape[:2]
    x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0: return
    img[y0:y1, x0:x1] *= (1 - np.clip(g[y0 - y:y1 - y, x0 - x:x1 - x] * 2.2, 0, 1)[..., None] * op)

def txt(img, s, x, y, size, color, op=1.0, path=F_INTER, glow=0, glow_op=0.0, anchor='lt'):
    if op > 0.01 and s: blit(img, sprite(s, path, size, glow), x, y, color, op, glow_op, anchor=anchor)

_RR = {}
def card(img, x, y, w, h, op, border=ICE, dark=0.62, r=14, tint=None):
    if op <= 0.01: return
    x, y, w, h = int(x), int(y), int(w), int(h); H, W = img.shape[:2]
    x = max(0, min(x, W - w)); y = max(0, min(y, H - h))
    k = (w, h, r)
    if k not in _RR:
        m = np.zeros((h, w), np.uint8)
        cv2.rectangle(m, (r, 0), (w - r - 1, h - 1), 255, -1); cv2.rectangle(m, (0, r), (w - 1, h - r - 1), 255, -1)
        for cx, cy in ((r, r), (w - r - 1, r), (r, h - r - 1), (w - r - 1, h - r - 1)): cv2.circle(m, (cx, cy), r, 255, -1, cv2.LINE_AA)
        _RR[k] = (m.astype(np.float32) / 255, cv2.GaussianBlur(cv2.Canny(m, 50, 150).astype(np.float32) / 255, (0, 0), 0.6))
    m, e = _RR[k]; reg = img[y:y + h, x:x + w]
    reg *= (1 - m[..., None] * dark * op)
    if tint is not None: reg += m[..., None] * tint * 0.06 * op
    reg += e[..., None] * border * 0.9 * op

def typed(s, t, t0, t1):
    if t < t0: return ""
    return s[:int(len(s) * clamp((t - t0) / max(0.01, t1 - t0)))]

# ------------------------------------------------------------------ 3D + particles
class Cam:
    def __init__(s, pos, tgt, roll=0.0, fov=1.0):
        s.pos = np.array(pos, np.float32); s.tgt = np.array(tgt, np.float32); s.roll = roll; s.fov = fov
def orbit(yaw, pitch, dist, tgt=(0, 0, 0), roll=0.0, fov=1.0):
    tgt = np.array(tgt, np.float32)
    p = tgt + dist * np.array([math.sin(yaw) * math.cos(pitch), math.sin(pitch), -math.cos(yaw) * math.cos(pitch)], np.float32)
    return Cam(p, tgt, roll, fov)
def project(P, cam, W, H):
    z = cam.tgt - cam.pos; z /= np.linalg.norm(z)
    up = np.array([math.sin(cam.roll), math.cos(cam.roll), 0], np.float32)
    x = np.cross(up, z); x /= np.linalg.norm(x); y = np.cross(z, x)
    Q = P - cam.pos; cx = Q @ x; cy = Q @ y; cz = Q @ z
    foc = min(W, H) * 1.25 * cam.fov; czs = np.maximum(cz, 1e-3)
    return W / 2 + foc * cx / czs, H / 2 - foc * cy / czs, cz

def splat(buf, u, v, w, col):
    """Additive bilinear point splats into a float (H,W,3) buffer."""
    H, W = buf.shape[:2]
    ok = (u >= 0) & (u < W - 1) & (v >= 0) & (v < H - 1) & (w > 0)
    if not ok.any(): return
    u, v, w = u[ok], v[ok], w[ok]
    col = col[ok] if col.ndim == 2 else np.broadcast_to(col, (len(u), 3))
    x0 = u.astype(np.int32); y0 = v.astype(np.int32); fx = u - x0; fy = v - y0
    flat = buf.reshape(-1, 3)
    for dx, dy, ww in ((0, 0, (1 - fx) * (1 - fy)), (1, 0, fx * (1 - fy)), (0, 1, (1 - fx) * fy), (1, 1, fx * fy)):
        idx = (y0 + dy) * W + (x0 + dx); wt = w * ww
        for c in range(3):
            flat[:, c] += np.bincount(idx, weights=wt * col[:, c], minlength=W * H).astype(np.float32)

# ------------------------------------------------------------------ light FX (scene space, linear float)
def bloom(layer, amt=1.0):
    SH, SW = layer.shape[:2]
    small = cv2.resize(layer, (SW // 2, SH // 2), interpolation=cv2.INTER_AREA)
    b1 = cv2.GaussianBlur(small, (0, 0), 3)
    b2 = cv2.GaussianBlur(cv2.resize(small, (SW // 8, SH // 8), interpolation=cv2.INTER_AREA), (0, 0), 3)
    return (cv2.resize(b1, (SW, SH)) * 0.75 + cv2.resize(b2, (SW, SH)) * 1.3) * amt

def god_rays(src, cx, cy, amt):
    """Radial light rays from (cx, cy) in src pixel coords."""
    SH, SW = src.shape[:2]; q = cv2.resize(src, (SW // 4, SH // 4), interpolation=cv2.INTER_AREA)
    cx, cy = cx / 4, cy / 4; acc = np.zeros_like(q); ws = 0
    for k in range(12):
        s = 1 + 0.045 * k; M = np.array([[s, 0, cx * (1 - s)], [0, s, cy * (1 - s)]], np.float32)
        acc += cv2.warpAffine(q, M, (SW // 4, SH // 4)) * 0.86 ** k; ws += 0.86 ** k
    return cv2.resize(cv2.GaussianBlur(acc / ws, (0, 0), 2), (SW, SH)) * amt * 1.4

def streaks(layer, amt, tint=(0.35, 0.65, 1.0)):
    """Anamorphic horizontal lens streaks from bright areas."""
    SH, SW = layer.shape[:2]
    q = np.maximum(cv2.resize(layer, (SW // 4, SH // 4), interpolation=cv2.INTER_AREA) - 0.55, 0)
    st = cv2.GaussianBlur(q, (0, 0), sigmaX=SW / 16, sigmaY=0.6).mean(2, keepdims=True) * np.array(tint, np.float32)
    return cv2.resize(st, (SW, SH)) * amt * 6.0

def tonemap(img, expo=1.0): return 1 - np.exp(-img * 1.35 * expo)

# ------------------------------------------------------------------ post (display space)
class Post:
    def __init__(s, W, H):
        r = np.random.default_rng(9)
        s.grain = [r.normal(0, 1, (H // 2, W // 2)).astype(np.float32) for _ in range(6)]
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        d = np.hypot((xx - W / 2) / (W / 2), (yy - H / 2) / (H / 2))
        s.vig = np.clip(1 - 0.38 * d ** 2.2, 0, 1)[..., None].astype(np.float32)
        s.bot = (np.clip((yy[:, :1] / H - 0.62) / 0.38, 0, 1)[..., None] ** 1.5).astype(np.float32)
        s.scan = (0.85 + 0.15 * (np.arange(H) % 3 != 0)).astype(np.float32)[:, None, None]
_POST = {}
def post(W, H):
    if (W, H) not in _POST: _POST[(W, H)] = Post(W, H)
    return _POST[(W, H)]

def chroma(img, amt):
    if amt < 0.0004: return img
    H, W = img.shape[:2]; out = img.copy()
    for c, s in ((0, 1 + amt), (2, 1 - amt)):
        M = np.array([[s, 0, W / 2 * (1 - s)], [0, s, H / 2 * (1 - s)]], np.float32)
        out[..., c] = cv2.warpAffine(img[..., c], M, (W, H), borderMode=cv2.BORDER_REFLECT)
    return out

def glitch(img, amt, fi):
    if amt < 0.05: return img
    H = img.shape[0]; r = np.random.default_rng(fi * 7 + 3)
    for _ in range(int(3 + 10 * amt)):
        y = r.integers(0, H - 10); h = int(r.integers(4, int(10 + 80 * amt))); dx = int(r.normal(0, 60 * amt))
        img[y:y + h] = np.roll(img[y:y + h], dx, axis=1)
        if r.random() < 0.4: img[y:y + h, :, r.integers(0, 3)] *= 1.6
    return img

def finish(img, t, fi, duration, flash=0.0, flash_col=ICE2, glitch_amt=0.0, ca=0.0018, vignette=True):
    """Flash, chromatic aberration, glitch, vignette, grain, head/tail fades -> uint8."""
    H, W = img.shape[:2]; p = post(W, H)
    if flash > 0: img = img + flash_col * flash * (0.6 + 0.4 * p.vig)
    img = chroma(img, ca + 0.012 * glitch_amt + 0.004 * min(1, flash))
    img = glitch(img, glitch_amt, fi)
    if vignette: img *= p.vig
    img += cv2.resize(p.grain[fi % 6], (W, H), interpolation=cv2.INTER_NEAREST)[..., None] * 0.018
    img *= (1 - sstep(duration - 1.2, duration - 0.1, t))   # no fade-in: frame 0 is a real picture (never black); fade out at the very end
    return (np.clip(img, 0, 1) * 255).astype(np.uint8)

# ------------------------------------------------------------------ lyrics + title hits
def _layout(L, fs, maxw, skip):
    items = [(w, tt) for w, tt in zip(L['words'], L['wt']) if not (skip and norm(w) == skip)]
    if not items: return None
    items[0] = (items[0][0].lstrip(',').strip(), items[0][1])
    sp = text_w(" ", F_INTER, fs); rows = [[]]; cw = 0
    for w, tt in items:
        ww = text_w(w, F_INTER, fs)
        if rows[-1] and cw + sp + ww > maxw: rows.append([]); cw = 0
        rows[-1].append((w, tt, ww)); cw += ww + (sp if rows[-1] else 0)
    return rows, sp

def overlay_lyrics(img, t, W, H, timing, active=ICE2, glow=ICE, hide_sections=(), skip=None, band=True):
    """Karaoke lower-third. Vertical layout stays inside the Reels safe frame.
    Back-to-back lines swap with a quick crossfade at the next line's first word, so two lines never stack."""
    if STATE["clean"]: return
    vert = H > W; ts = min(W, H) / 1080
    if band: img *= (1 - 0.55 * post(W, H).bot)
    # readability floor: lyrics are never smaller than ~64 px (16:9) / ~58 px (9:16) at 1080
    fs = int((64 if not vert else 58) * ts); maxw = W * (0.80 if not vert else 0.66)
    ybase = H * (0.835 if not vert else 0.62)   # 9:16: inside SAFE_9x16 (above the caption block, left of the buttons)
    xc = W * (0.5 if not vert else 0.45)
    flt = STATE["lyric_filter"]
    vis = [L for L in timing.lines if L.get('sec') not in hide_sections and (flt is None or flt(L)) and not (skip is not None and skip(L))]
    for li, L in enumerate(vis):
        nxt = vis[li + 1]['s'] if li + 1 < len(vis) else 1e9
        prv_out = (vis[li - 1]['e'] + 0.45) if li > 0 else -1e9
        if prv_out > L['s'] - 0.3: a0, a1 = L['s'] - 0.07, L['s'] + 0.05          # previous line still up: swap
        else: a0, a1 = L['s'] - 0.3, L['s']
        if L['e'] + 0.45 > nxt - 0.3: b0, b1 = nxt - 0.17, nxt - 0.07
        else: b0, b1 = L['e'] + 0.05, L['e'] + 0.45
        if not (a0 <= t <= b1): continue
        lay = _layout(L, fs, maxw, timing.stamp_word)
        if lay is None: continue
        rows, sp = lay
        opl = sstep(a0, a1, t) * (1 - sstep(b0, b1, t))
        if opl <= 0.003: continue
        lh = fs * 1.3; y0 = ybase - (len(rows) - 1) * lh / 2 - lh * 0.3 * (1 - opl)
        for ri, row in enumerate(rows):
            x = xc - (sum(r[2] for r in row) + sp * (len(row) - 1)) / 2
            for w, tt, ww in row:
                k = sstep(tt - 0.14, tt + 0.06, t)
                act = math.exp(-max(0, t - tt) * 2.2) if t >= tt - 0.05 else 0
                col = IVORY * 0.97 * (1 - act) + active * act * 1.1
                op = opl * (0.32 + 0.68 * k); dy = (1 - k) * 10 * ts
                shadow(img, sprite(w, F_INTER, fs, 11), x, y0 + ri * lh + dy + 2 * ts, 0.95 * op)
                blit(img, sprite(w, F_INTER, fs, 5), x, y0 + ri * lh + dy, col, op, 0.55 * act + 0.12, glow_color=glow)
                x += ww + sp

def overlay_stamp(img, t, W, H, timing, word=None, caption="", hide=lambda t: False, glow_color=ICE, caption_above=False):
    """Giant title hit with chromatic split on every stamp time."""
    if STATE["clean"] or not timing.stamps: return
    s, i = timing.last_stamp(t)
    if s is None or t - s > 1.3: return
    if i + 1 < len(timing.stamps) and t >= timing.stamps[i + 1]: return
    if hide(t): return
    x = t - s; vert = H > W; ts = min(W, H) / 1080
    word = word or timing.stamp_word.upper()
    size = int((235 if not vert else 190) * ts)
    fitw = W * (0.9 if not vert else (SAFE_9x16['right'] - SAFE_9x16['left'] - 0.04))   # 9:16: inside the phone crop
    if text_w(word, F_DISP, size) > fitw: size = int(size * fitw / text_w(word, F_DISP, size))
    sp = sprite(word, F_DISP, size, 14, track=int(10 * ts))
    sc = 1.0 + 0.32 * (1 - ease_out(x / 0.22)) + 0.04 * x
    op = (1 - sstep(0.55, 1.3, x)) * sstep(0, 0.04, x)
    cy = H * (0.45 if not vert else 0.42); dx = (16 * (1 - ease_out(x / 0.4)) + 3) * ts
    a = sp[0]
    for off, col in ((-dx, np.array([1.0, 0.15, 0.35], np.float32)), (dx, np.array([0.1, 0.8, 1.0], np.float32))):
        aa = cv2.resize(a, None, fx=sc, fy=sc); h, w = aa.shape
        xx = int(W / 2 - w / 2 + off); yy = int(cy - h / 2)
        x0, y0, x1, y1 = max(0, xx), max(0, yy), min(W, xx + w), min(H, yy + h)
        if x1 > x0 and y1 > y0: img[y0:y1, x0:x1] += aa[y0 - yy:y1 - yy, x0 - xx:x1 - xx, None] * col * op * 0.55
    blit(img, sp, W / 2, cy, WHITE, op, 1.1 * op, glow_color=glow_color, anchor='c', scale=sc)
    if caption:
        cyc = cy - size * 0.62 * sc if caption_above else cy + size * 0.62 * sc
        txt(img, caption, W / 2, cyc, int((40 if caption_above else 22) * ts), WHITE if caption_above else ICE2, op * 0.9, F_DISPB if caption_above else F_MONO, 6, 0.4, anchor='c')

# ------------------------------------------------------------------ subscribe asks (every video gets these)
def _cfg():
    try:
        from .config import CFG
        return CFG
    except Exception:
        return {}

def _pill(img, x, y, w, h, col, op):
    """Solid rounded pill (x,y = top-left)."""
    x, y, w, h = int(x), int(y), int(w), int(h); r = h // 2
    lay = np.zeros(img.shape[:2], np.float32)
    cv2.rectangle(lay, (x + r, y), (x + w - r, y + h), 1.0, -1, cv2.LINE_AA)
    cv2.circle(lay, (x + r, y + r), r, 1.0, -1, cv2.LINE_AA); cv2.circle(lay, (x + w - r, y + r), r, 1.0, -1, cv2.LINE_AA)
    m = lay[..., None] * op
    img *= (1 - m); img += m * col

def _bell(img, cx, cy, s, col, op, ring=0.0):
    """Simple notification bell (s = height in px)."""
    lay = np.zeros(img.shape[:2], np.float32); a = ring * 0.35
    c, sn = math.cos(a), math.sin(a)
    def P(px, py): return (int(cx + (px * c - py * sn) * s), int(cy + (px * sn + py * c) * s))
    pts = np.array([P(-0.42, 0.28), P(-0.34, 0.0), P(-0.3, -0.22), P(-0.16, -0.38), P(0, -0.42), P(0.16, -0.38), P(0.3, -0.22),
                    P(0.34, 0.0), P(0.42, 0.28)], np.int32)
    cv2.fillPoly(lay, [pts], 1.0, cv2.LINE_AA)
    cv2.circle(lay, P(0, 0.38), max(2, int(s * 0.11)), 1.0, -1, cv2.LINE_AA)
    cv2.circle(lay, P(0, -0.47), max(2, int(s * 0.06)), 1.0, -1, cv2.LINE_AA)
    m = lay[..., None] * op; img *= (1 - m); img += m * col

SUB_RED = hexc('ff1f3d')

THEME = {}   # a scene can restyle the subscribe pill / end card: C.THEME.update(disp=..., body=..., dispb=..., mono=..., red=...)
def TH(k, d): return THEME.get(k, d)

def subscribe_pill(img, t, W, H, t0, dur=5.0, line=None):
    """Mid-video ask for the 16:9 YouTube master only (the 9:16 master feeds Shorts/Reels, which loop)."""
    if STATE["clean"] or H > W: return
    a = sstep(t0, t0 + 0.35, t) * (1 - sstep(t0 + dur - 0.4, t0 + dur, t))
    if a <= 0.01: return
    ts = H / 1080; cfg = _cfg(); handle = cfg.get("channel_handle", "@adita_zzz")
    line = line or f"{handle}  ·  songs about tech life"   # never promise a schedule
    pop = 1 + 0.12 * math.exp(-max(0, t - t0) * 8)
    fs = int(46 * ts * pop); bh = int(fs * 1.9); bw = int(text_w("SUBSCRIBE", TH('disp', F_DISP), fs) + bh * 1.55)
    x = int(48 * ts); y = int(44 * ts) - int((1 - ease_out((t - t0) / 0.35)) * 40 * ts)
    _pill(img, x, y, bw, bh, TH('red', SUB_RED), a)
    press = sstep(t0 + 1.4, t0 + 1.5, t) * (1 - sstep(t0 + 1.6, t0 + 1.9, t))
    if t > t0 + 1.55:   # "subscribed" state: dark pill, bell rings
        k = sstep(t0 + 1.5, t0 + 1.7, t)
        _pill(img, x, y, bw, bh, hexc('2a2a2e'), a * k)
    _bell(img, x + bh * 0.62, y + bh / 2, bh * 0.62, WHITE, a, ring=math.sin((t - t0) * 18) * math.exp(-max(0, t - t0 - 1.6) * 2.5) if t > t0 + 1.6 else 0)
    lab = "SUBSCRIBED" if t > t0 + 1.6 else "SUBSCRIBE"
    blit(img, sprite(lab, TH('disp', F_DISP), fs), x + bh * 1.12, y + bh / 2 - fs * 0.62, WHITE, a)
    if press > 0: cv2.circle(img, (int(x + bw * 0.62), int(y + bh * 0.6)), int(bh * (0.4 + 0.5 * press)), (WHITE * 0.9).tolist(), max(2, int(3 * ts)), cv2.LINE_AA)
    fs2 = int(38 * ts)
    sp = sprite(line, TH('body', F_INTER), fs2, 8)
    shadow(img, sp, x + bw + 24 * ts, y + bh / 2 - fs2 * 0.62 + 2 * ts, 0.9 * a)
    blit(img, sp, x + bw + 24 * ts, y + bh / 2 - fs2 * 0.62, WHITE, a)

def end_screen(img, t, W, H, t0, dur, headline, sub_line=None, accent=None, title=None):
    """Last-seconds card. 16:9: left column text, right ~45% left clear for YouTube's end-screen
    elements (next-video tile + Subscribe button). 9:16: centered follow card for Instagram."""
    if STATE["clean"]: return
    e = sstep(t0, t0 + 0.8, t)
    if e <= 0: return
    vert = H > W; ts = min(W, H) / 1080; cfg = _cfg(); accent = accent if accent is not None else TH('red', SUB_RED)
    img *= (1 - 0.62 * e)
    if not vert:
        x = W * 0.07
        y = H * 0.30
        hs = int(110 * ts)
        while text_w(headline, TH('disp', F_DISP), hs) > W * 0.46: hs -= 4
        sp = sprite(headline, TH('disp', F_DISP), hs, 12)
        blit(img, sp, x, y, WHITE, e, 0.45 * e, glow_color=accent)
        y += hs * 1.35
        fs = int(48 * ts)
        sub_line = sub_line or "Subscribe for more songs about tech life"
        blit(img, sprite(sub_line, TH('body', F_INTER), fs, 6), x, y, WHITE * 0.96, e)
        y += fs * 1.6
        handle = cfg.get("channel_handle", "@adita_zzz")
        fs3 = int(44 * ts); bh = int(fs3 * 1.9); bw = int(text_w("SUBSCRIBE", TH('disp', F_DISP), fs3) + bh * 1.55)
        _pill(img, x, y, bw, bh, TH('red', SUB_RED), e)
        _bell(img, x + bh * 0.62, y + bh / 2, bh * 0.62, WHITE, e, ring=math.sin((t - t0) * 16) * math.exp(-max(0, t - t0 - 0.6) * 1.5))
        blit(img, sprite("SUBSCRIBE", TH('disp', F_DISP), fs3), x + bh * 1.12, y + bh / 2 - fs3 * 0.62, WHITE, e)
        blit(img, sprite(handle, TH('body', F_INTER), fs3), x + bw + 26 * ts, y + bh / 2 - fs3 * 0.62, WHITE * 0.9, e)
        # arrow toward where YouTube's end-screen elements sit
        ax = int(W * 0.56); ay = int(H * 0.5); k = 0.5 + 0.5 * math.sin((t - t0) * 5)
        cv2.arrowedLine(img, (ax, ay), (int(ax + (60 + 20 * k) * ts), ay), (accent * e).tolist(), max(3, int(7 * ts)), cv2.LINE_AA, tipLength=0.45)
        if title:
            blit(img, sprite(title.upper(), TH('mono', F_MONOB), int(36 * ts), track=int(8 * ts)), x, H * 0.80, accent * 1.0, e * 0.95)
    else:
        ig = cfg.get("instagram", "@aditazzz.music")
        hs = int(118 * ts); fitw = W * (SAFE_9x16['right'] - SAFE_9x16['left'] - 0.04)   # inside the phone crop
        while text_w(headline, TH('disp', F_DISP), hs) > fitw: hs -= 4
        blit(img, sprite(headline, TH('disp', F_DISP), hs, 12), W / 2, H * 0.36, WHITE, e, 0.45 * e, glow_color=accent, anchor='c')
        fs = int(52 * ts)
        blit(img, sprite("songs about tech life", TH('body', F_INTER), fs, 6), W / 2, H * 0.36 + hs * 1.05, WHITE * 0.95, e, anchor='c')
        lab = f"subscribe {cfg.get('channel_handle', '@adita_zzz')}" if STATE.get("platform") == "youtube" else f"follow {ig}"
        fs3 = int(54 * ts)   # the pill stays left of the like/share column: at most 56% of the width, label >= 40 px
        while text_w(lab, TH('dispb', F_DISPB), fs3) + fs3 * 1.9 > W * 0.56 and fs3 > int(40 * ts): fs3 -= 2
        bh = int(fs3 * 1.9); bw = int(text_w(lab, TH('dispb', F_DISPB), fs3) + bh); py = H * 0.495 - bh   # ends above the column's top
        _pill(img, W / 2 - bw / 2, py, bw, bh, accent, e)
        blit(img, sprite(lab, TH('dispb', F_DISPB), fs3), W / 2, py + bh / 2, WHITE, e, anchor='c')
        if title:
            fsT = int(40 * ts)
            while text_w(title.upper(), TH('mono', F_MONOB), fsT) + len(title) * 8 * ts > W * 0.56 and fsT > 24: fsT -= 2   # left of the like/share column
            blit(img, sprite(title.upper(), TH('mono', F_MONOB), fsT, track=int(8 * ts)), W / 2, H * 0.60, accent, e * 0.95, anchor='c')
