"""What the glass shows: the face cut into tiles (scrambled into a scrolling feed, flying home into the face, flipping
into everyone else, falling apart), the receipt cards (what the feed never shows you), the lipstick title, fog breathed
onto the glass with a fingertip writing in it, the marker lines, the pointing cursors, the stamps.

Everything here works in GLASS coordinates: 1282 x 1720 px (the mirror glass of the 2x plate), linear float RGB.
Text sizes are chosen so they stay readable after the mirror is scaled into the frame (a 16:9 frame shows the glass at
~0.5x, so main text is ~88 px here -> ~45 px on screen; nothing meant to be read is under 60 px here)."""
import os, math
from functools import lru_cache
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
import vanity as V
from vanity import F32, clamp, sstep, lerp, ease_io

ROOT = os.path.dirname(os.path.dirname(V.HERE))
FONTS = os.path.join(ROOT, "assets", "fonts")
F_SB = os.path.join(FONTS, "Inter-SemiBold.otf"); F_MD = os.path.join(FONTS, "Inter-Medium.otf")
F_BLK = os.path.join(FONTS, "InterDisplay-Black.otf"); F_BOLD = os.path.join(FONTS, "InterDisplay-Bold.otf")
F_HAND = os.path.join(FONTS, "Caveat-Medium.ttf"); F_MARK = os.path.join(FONTS, "PermanentMarker-Regular.ttf")
F_MONO = os.path.join(FONTS, "JBMono-700.ttf"); F_STAMP = os.path.join(FONTS, "SairaStencilOne-Regular.ttf")

GW, GH = V.GW, V.GH                         # 1282 x 1720
TW, TH = 80, 86                              # a feed of thumbnails: 16 x 20 tiles
NX, NY = GW // TW, GH // TH
NT = NX * NY
TILE = TW

@lru_cache(64)
def font(path, size): return ImageFont.truetype(path, size)

def ease_out(x): x = clamp(x); return 1 - (1 - x) ** 3
def ease_in(x): x = clamp(x); return x * x * x

# ================================================================ tiles
@lru_cache(2)
def face(cracked=False):
    return V.glass_face(cracked)

def _tiles(img):   # (NT, TH, TW, 3) copy of the tiled area
    return img[:NY * TH, :NX * TW].reshape(NY, TH, NX, TW, 3).transpose(0, 2, 1, 3, 4).reshape(NT, TH, TW, 3)

def _untile(T, out):
    out[:NY * TH, :NX * TW] = T.reshape(NY, NX, TH, TW, 3).transpose(0, 2, 1, 3, 4).reshape(NY * TH, NX * TW, 3)
    return out

def txy(k): return (k % NX) * TW, (k // NX) * TH

class _TileView:
    """tile k of the face as a view (no copy)."""
    def __init__(self, img): self.img = img
    def __getitem__(self, k):
        if isinstance(k, (int, np.integer)):
            x, y = txy(int(k)); return self.img[y:y + TH, x:x + TW]
        return _tiles(self.img)[k]
    def __len__(self): return NT

@lru_cache(2)
def face_tiles(cracked=False): return _TileView(face(cracked))

@lru_cache(1)
def tile_alpha():
    """a thumbnail's shape: rounded corners, a hairline gap to its neighbours."""
    m = np.zeros((TH * 4, TW * 4), np.uint8)
    cv2.rectangle(m, (14, 14), (TW * 4 - 15, TH * 4 - 15), 255, -1)
    m = cv2.resize(m, (TW, TH), interpolation=cv2.INTER_AREA).astype(F32) / 255
    r = 7; yy, xx = np.mgrid[0:TH, 0:TW].astype(F32)
    for cx, cy in ((r + 3, r + 3), (TW - r - 4, r + 3), (r + 3, TH - r - 4), (TW - r - 4, TH - r - 4)):
        corner = ((xx < r + 3) if cx < TW / 2 else (xx > TW - r - 4)) & ((yy < r + 3) if cy < TH / 2 else (yy > TH - r - 4))
        d = np.hypot(xx - cx, yy - cy)
        m = np.where(corner, m * np.clip(r + 0.5 - d, 0, 1), m)
    return m.astype(F32)

@lru_cache(1)
def grout():
    a = tile_alpha()
    g = np.ones((GH, GW), F32)
    g[:NY * TH, :NX * TW] = np.tile(a, (NY, NX))
    return (0.10 + 0.90 * g)[..., None].astype(F32)

@lru_cache(4)
def perm(pid=0):
    return np.random.default_rng(23 + 101 * pid).permutation(NT)

@lru_cache(4)
def inv_perm(pid=0): return np.argsort(perm(pid))

@lru_cache(4)
def tile_gain(pid=0):
    r = np.random.default_rng(7 + pid)
    g = r.uniform(0.84, 1.16, (NT, 1, 1, 1)).astype(F32)
    return g * (1 + r.normal(0, 0.05, (NT, 1, 1, 3))).astype(F32)

@lru_cache(4)
def scrambled(cracked=False, pid=0):
    """the face's tiles shuffled into a wall of thumbnails: the feed before it becomes a face.
    cell j shows tile perm[j]; tile k sits in cell inv[k]."""
    f = face(cracked)
    T = face_tiles(cracked)[perm(pid)] * tile_gain(pid)
    out = _untile(T, f.copy())
    return (out * grout()).astype(F32)

@lru_cache(1)
def col_speed(): return np.random.default_rng(41).uniform(0.6, 1.4, NX).astype(F32)

def feed_layout(P, cracked=False, pid=0):
    """the feed with every column scrolled up by P * its own speed (px, sub-pixel, wrapping)."""
    sc = scrambled(cracked, pid); out = sc.copy(); sp = col_speed()
    for c in range(NX):
        o = (P * sp[c]) % GH; oi = int(o); f = o - oi
        col = sc[:, c * TW:(c + 1) * TW]
        a = np.roll(col, -oi, axis=0)
        if f > 1e-3: a = a * (1 - f) + np.roll(col, -oi - 1, axis=0) * f
        out[:, c * TW:(c + 1) * TW] = a
    return out

def tile_src(k, P, pid=0):
    """where tile k currently sits in the scrolled feed (x, y of its top-left)."""
    j = inv_perm(pid)[k]; c, r = j % NX, j // NX
    y = (r * TH - P * col_speed()[c]) % GH
    if y > GH - TH * 0.5: y -= GH
    return c * TW, y

@lru_cache(1)
def tile_order():
    """when each tile flies home: the eyes first, then the lips, then outward."""
    feats = [(370, 704, 0.0), (930, 704, 0.0), (636, 1280, 140.0)]
    cx, cy = GW * 0.5, GH * 0.47
    r = np.random.default_rng(5); keys = []
    for k in range(NT):
        x, y = txy(k); x += TW / 2; y += TH / 2
        d = min(math.hypot(x - fx, y - fy) + bias for fx, fy, bias in feats) * 0.65 + math.hypot(x - cx, y - cy) * 0.35
        keys.append(d + r.uniform(-120, 120))
    keys = np.array(keys)
    return (np.argsort(np.argsort(keys)) / (NT - 1)).astype(F32)

@lru_cache(1)
def tile_jitter(): return np.random.default_rng(9).uniform(-1, 1, (NT, 2)).astype(F32)

def _paste(out, tile, x, y, mul=1.0, alpha=None):
    h, w = tile.shape[:2]; xi, yi = int(round(x)), int(round(y))
    H, W = out.shape[:2]
    X0, Y0, X1, Y1 = max(0, xi), max(0, yi), min(W, xi + w), min(H, yi + h)
    if X1 <= X0 or Y1 <= Y0: return
    t = tile[Y0 - yi:Y1 - yi, X0 - xi:X1 - xi]
    if mul != 1.0: t = t * mul
    if alpha is None: out[Y0:Y1, X0:X1] = t
    else:
        a = alpha[Y0 - yi:Y1 - yi, X0 - xi:X1 - xi][..., None]
        reg = out[Y0:Y1, X0:X1]; reg *= (1 - a); reg += t * a

def _flying(tile, sc):
    """a tile in flight: scaled, with its thumbnail shape as alpha."""
    w, h = max(2, int(round(TW * sc))), max(2, int(round(TH * sc)))
    a = tile_alpha()
    if (w, h) != (TW, TH):
        tile = cv2.resize(tile, (w, h), interpolation=cv2.INTER_LINEAR); a = cv2.resize(a, (w, h), interpolation=cv2.INTER_LINEAR)
    return tile, a

def _tile_mask(sel):
    return np.repeat(np.repeat(sel.reshape(NY, NX), TH, 0), TW, 1)

def assemble(t, t0, t1, P, cracked=False, dur=1.5, dim=0.42, spread=1.0, pid=0):
    """tiles lift out of the (stopped) feed and fly to their home, staggered over [t0, t1]: the face emerges.
    returns (glass image, fraction of tiles home)."""
    f = face(cracked)
    if t >= t1 + 0.05: return f.copy(), 1.0
    span = max(0.01, t1 - t0 - dur)
    prog = np.clip((t - (t0 + tile_order() * span)) / dur, 0, 1)
    out = feed_layout(P, cracked, pid) * dim
    for k in np.nonzero(prog > 0)[0]:          # the slots the departed tiles left behind go dark
        x, y = tile_src(k, P, pid)
        yi = int(round(y)); Y0, Y1 = max(0, yi), min(GH, yi + TH)
        if Y1 > Y0: out[Y0:Y1, x:x + TW] *= 0.10
    home = prog >= 1.0
    if home.any():
        np.copyto(out[:NY * TH, :NX * TW], f[:NY * TH, :NX * TW], where=_tile_mask(home)[..., None])
    frac = float(home.mean())
    if frac > 0.98: out[:, NX * TW:] = f[:, NX * TW:]
    jit = tile_jitter()
    T = face_tiles(cracked)
    mv = np.nonzero((prog > 0) & (prog < 1))[0]
    for k in mv[np.argsort(prog[mv])]:
        p = float(prog[k]); e = 1 - (1 - p) ** 3
        sx_, sy_ = tile_src(k, P, pid); hx, hy = txy(k)
        arc = math.sin(p * math.pi) * 170 * spread
        x = lerp(sx_, hx, e) + jit[k, 0] * arc; y = lerp(sy_, hy, e) + jit[k, 1] * arc
        sc = 1.0 + 0.55 * math.sin(p * math.pi)
        tile, a = _flying(T[k], sc)
        land = clamp((p - 0.85) / 0.15)                  # the thumbnail's frame melts into the face as it lands
        if land > 0: a = a * (1 - land) + land
        _paste(out, tile, hx + (x - hx) - (tile.shape[1] - TW) / 2, y - (tile.shape[0] - TH) / 2, 1.0 + 0.8 * math.sin(p * math.pi), a)
    return out, frac

def scatter(t, t0, t1, P, cracked=False, dim=0.42, pid=0):
    """the face comes apart: tiles drop out (top first, with a random spread) and fall away, the feed shows behind."""
    f = face(cracked)
    if t <= t0: return f.copy(), 1.0
    out = feed_layout(P, cracked, pid) * dim
    r = np.random.default_rng(31)
    rowk = (np.arange(NT) // NX) / NY
    start = t0 + (rowk * 0.55 + r.uniform(0, 0.45, NT)) * (t1 - t0) * 0.75
    vx = r.uniform(-260, 260, NT); vy = r.uniform(-220, 40, NT)
    tt = t - start
    stay = tt <= 0
    if stay.any():
        np.copyto(out[:NY * TH, :NX * TW], f[:NY * TH, :NX * TW], where=_tile_mask(stay)[..., None])
    T = face_tiles(cracked)
    for k in np.nonzero(~stay)[0]:
        a_ = tt[k]
        if a_ > 1.2: continue
        hx, hy = txy(k)
        x = hx + vx[k] * a_; y = hy + vy[k] * a_ + 0.5 * 2600 * a_ * a_
        if y > GH: continue
        tile, a = _flying(T[k], max(0.25, 1 - a_ * 0.45))
        _paste(out, tile, x + (TW - tile.shape[1]) / 2, y + (TH - tile.shape[0]) / 2, max(0.0, 1 - a_ * 0.7), a)
    return out, float(stay.mean())

@lru_cache(1)
def people_tiles():
    """tiles from the outer feed (where the cover shows separate pictures of people): what 'everyone else' looks like."""
    return np.array([k for k in range(NT) if (k % NX) < 3 or (k % NX) > NX - 4 or (k // NX) < 4 or (k // NX) > NY - 5])

def flip_wave(t, waves, cracked=False, base=None):
    """'looks like us': a wave of tiles flips (like cards) to other people's pictures and back, crossing the face."""
    f = face(cracked)
    out = (base if base is not None else f).copy()
    T = face_tiles(cracked); pt = people_tiles(); al = tile_alpha()
    for wi, tw in enumerate(waves):
        for k in range(NT):
            hx, hy = txy(k)
            phase = (hx * 0.8 + hy * 0.55) / (GW * 0.8 + GH * 0.55)
            u = t - tw - phase * 1.3
            if not (0 < u < 1.2): continue
            other = T[pt[(k * 7919 + wi * 131) % len(pt)]]
            if u < 0.18: src, w = T[k], math.cos(u / 0.18 * math.pi / 2)
            elif u < 0.36: src, w = other, math.sin((u - 0.18) / 0.18 * math.pi / 2)
            elif u < 0.78: src, w = other, 1.0
            elif u < 0.96: src, w = other, math.cos((u - 0.78) / 0.18 * math.pi / 2)
            else: src, w = T[k], math.sin(min(1.0, (u - 0.96) / 0.22) * math.pi / 2)
            out[hy:hy + TH, hx:hx + TW] *= 0.35
            tw_ = max(1, int(round(TW * clamp(w))))
            sq = cv2.resize(src, (tw_, TH), interpolation=cv2.INTER_AREA) * (0.70 + 0.45 * clamp(w))
            a = cv2.resize(al, (tw_, TH), interpolation=cv2.INTER_AREA)[..., None] if u < 0.96 else 1.0
            x0 = hx + (TW - tw_) // 2
            reg = out[hy:hy + TH, x0:x0 + tw_]; reg *= (1 - a); reg += sq * a
    return out

def loose(t, amp, cracked=False, dark=0.08):
    """a loose mosaic: every tile a little off its place and a little small, gaps showing between them."""
    f = face(cracked)
    if amp < 0.004: return f.copy()
    out = f * dark
    T = face_tiles(cracked); jit = tile_jitter()
    ph = np.random.default_rng(3).uniform(0, 6.28, NT)
    sc = 1.0 - 0.10 * amp
    al = tile_alpha()
    for k in range(NT):
        hx, hy = txy(k)
        dx = (jit[k, 0] * 22 + 6 * math.sin(t * 0.9 + ph[k])) * amp
        dy = (jit[k, 1] * 22 + 6 * math.cos(t * 0.7 + ph[k])) * amp
        tile, a = _flying(T[k], sc)
        a = a * amp + (1 - amp)
        _paste(out, tile, hx + (TW - tile.shape[1]) / 2 + dx, hy + (TH - tile.shape[0]) / 2 + dy, 1.0, a)
    return out

def reshuffle(t, t0, dur, P, pid_a=0, pid_b=1):
    """the feed re-sorts itself tile by tile (a machine picking what you see). returns the undimmed feed."""
    k = clamp((t - t0) / dur)
    if k <= 0: return feed_layout(P, False, pid_a)
    if k >= 1: return feed_layout(P, False, pid_b)
    a = feed_layout(P, False, pid_a); b = feed_layout(P, False, pid_b)
    r = np.random.default_rng(13).random(NT)
    np.copyto(a[:NY * TH, :NX * TW], b[:NY * TH, :NX * TW], where=_tile_mask(r < k)[..., None])
    return a

@lru_cache(1)
def _polar():
    yy, xx = np.mgrid[0:GH, 0:GW].astype(F32)
    cx, cy = GW / 2, GH * 0.47
    dx, dy = xx - cx, yy - cy
    return np.hypot(dx, dy), np.arctan2(dy, dx), cx, cy

def twirl(img, amt, pull=0.0):
    """a whirlpool: everything turns around the centre of the glass, the middle the most (pull > 0 also draws inward)."""
    if abs(amt) < 1e-3 and pull < 1e-3: return img
    r, a, cx, cy = _polar()
    w = np.exp(-(r / (GH * 0.42)) ** 2 * 1.6)
    da = amt * w; rr = r * (1 + pull * w)
    mx = (cx + rr * np.cos(a + da)).astype(F32); my = (cy + rr * np.sin(a + da)).astype(F32)
    return cv2.remap(img, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

# ================================================================ sprites (PIL -> linear float, cached)
CARD_BG = (246, 245, 243, 246); INK = (18, 18, 22, 255); MUTED = (108, 108, 118, 255)
BLUE = (36, 110, 230, 255); RED = (232, 50, 74, 255); WHITE = (255, 255, 255, 255); DARK = (22, 22, 27, 242)

def _spr(im, sigma=22):
    a8 = np.asarray(im).astype(F32) / 255
    rgb = np.ascontiguousarray(np.power(a8[..., :3], 2.2)); a = np.ascontiguousarray(a8[..., 3])
    return rgb, a, cv2.GaussianBlur(a, (0, 0), sigma)

def blit(img, spr, cx, cy, op=1.0, scale=1.0, shadow=0.5, dy=28, light=1.0):
    """composite a sprite (linear rgb, straight alpha) centred at (cx, cy), with a soft drop shadow."""
    if op <= 0.003 or scale <= 0.02: return
    rgb, a, sh = spr
    if abs(scale - 1) > 0.004:
        w = max(2, int(round(rgb.shape[1] * scale))); h = max(2, int(round(rgb.shape[0] * scale)))
        it = cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR
        rgb = cv2.resize(rgb, (w, h), interpolation=it); a = cv2.resize(a, (w, h), interpolation=it); sh = cv2.resize(sh, (w, h), interpolation=it)
    h, w = a.shape; H, W = img.shape[:2]
    xa, ya = int(round(cx - w / 2)), int(round(cy - h / 2))
    if shadow > 0:
        sx, sy = xa + int(dy * 0.3 * scale), ya + int(dy * scale)
        X0, Y0, X1, Y1 = max(0, sx), max(0, sy), min(W, sx + w), min(H, sy + h)
        if X1 > X0 and Y1 > Y0:
            img[Y0:Y1, X0:X1] *= (1 - sh[Y0 - sy:Y1 - sy, X0 - sx:X1 - sx] * (op * shadow))[..., None]
    X0, Y0, X1, Y1 = max(0, xa), max(0, ya), min(W, xa + w), min(H, ya + h)
    if X1 <= X0 or Y1 <= Y0: return
    A = (a[Y0 - ya:Y1 - ya, X0 - xa:X1 - xa] * op)[..., None]
    reg = img[Y0:Y1, X0:X1]; reg *= (1 - A)
    c = rgb[Y0 - ya:Y1 - ya, X0 - xa:X1 - xa]
    reg += (c * light if light != 1.0 else c) * A

def pop(t, t0, t1=None, rise=0.22, fall=0.28):
    """(opacity, scale) for a card that pops in at t0 and leaves at t1."""
    if t < t0: return 0.0, 0.0
    k = clamp((t - t0) / rise); e = 1 - (1 - k) ** 3
    sc = 0.84 + 0.16 * e + 0.05 * math.sin(k * math.pi)
    op = e
    if t1 is not None and t > t1:
        q = clamp((t - t1) / fall); op *= 1 - q; sc *= 1 - 0.08 * q
    return op, sc

def _wrap(text, f, maxw):
    words = text.split(" "); lines = [[]]
    for wd in words:
        trial = " ".join(lines[-1] + [wd])
        if lines[-1] and f.getlength(trial) > maxw: lines.append([wd])
        else: lines[-1].append(wd)
    return [" ".join(l) for l in lines]

def _heart(d, cx, cy, s, fill):
    r = s * 0.27
    d.ellipse((cx - s * 0.5, cy - s * 0.38, cx - s * 0.5 + 2 * r, cy - s * 0.38 + 2 * r), fill=fill)
    d.ellipse((cx + s * 0.5 - 2 * r, cy - s * 0.38, cx + s * 0.5, cy - s * 0.38 + 2 * r), fill=fill)
    d.polygon([(cx - s * 0.49, cy - s * 0.16), (cx + s * 0.49, cy - s * 0.16), (cx, cy + s * 0.42)], fill=fill)

def _heart_badge(size, broken=0):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, size - 1, size - 1), size // 4, fill=RED)
    _heart(d, size / 2, size / 2 + size * 0.03, size * 0.58, WHITE)
    if broken:
        c = size / 2; k = broken / 4
        pts = [(c + size * 0.02, size * 0.22), (c - size * 0.07, size * 0.40), (c + size * 0.06, size * 0.52), (c - size * 0.05, size * 0.66), (c, size * 0.84)]
        d.line(pts, fill=RED, width=max(3, int(size * 0.075 * k)), joint="curve")
    return im

def _avatar(size, seed):
    r = np.random.default_rng(seed)
    c1 = tuple(int(x) for x in r.integers(70, 210, 3)); c2 = tuple(int(x) for x in r.integers(25, 110, 3))
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse((0, 0, size - 1, size - 1), fill=c1 + (255,))
    d.ellipse((size * 0.31, size * 0.17, size * 0.69, size * 0.55), fill=c2 + (255,))
    d.ellipse((size * 0.14, size * 0.60, size * 0.86, size * 1.25), fill=c2 + (255,))
    m = Image.new("L", (size, size), 0); ImageDraw.Draw(m).ellipse((0, 0, size - 1, size - 1), fill=255)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0)); out.paste(im, (0, 0), m)
    return out

@lru_cache(6)
def comment_card(text, user="@realart_only", likes=None, top=False, replies=(), broken=0, caret=False, w=1150):
    pad = 50; ax = pad + 128 + 34
    f = font(F_SB, 88); fu = font(F_MD, 62); fl = font(F_SB, 68); fr = font(F_MD, 66)
    lines = _wrap(text, f, w - ax - pad) if text else [""]
    h = pad + (112 if top else 0) + 82 + len(lines) * 108 + (118 if likes is not None else 26) + len(replies) * 124 + pad - 10
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 46, fill=CARD_BG)
    y = pad
    if top:
        tw = fu.getlength("Top comment")
        d.rounded_rectangle((pad, y, pad + tw + 56, y + 88), 44, fill=(228, 228, 233, 255))
        d.text((pad + 28, y + 8), "Top comment", font=fu, fill=MUTED); y += 112
    im.alpha_composite(_avatar(128, 3), (pad, y))
    d.text((ax, y), user + "  ·  2h", font=fu, fill=MUTED)
    ty = y + 82
    for i, l in enumerate(lines):
        d.text((ax, ty), l, font=f, fill=INK)
        if caret and i == len(lines) - 1:
            cx = ax + f.getlength(l) + 8
            d.rectangle((cx, ty + 12, cx + 7, ty + 100), fill=BLUE)
        ty += 108
    if likes is not None:
        im.alpha_composite(_heart_badge(86, broken), (ax, ty + 14))
        d.text((ax + 110, ty + 18), likes, font=fl, fill=INK); ty += 118
    else:
        ty += 26
    for i, rp in enumerate(replies):
        im.alpha_composite(_avatar(96, 20 + i * 3), (ax, ty))
        d.text((ax + 124, ty + 12), rp, font=fr, fill=INK); ty += 124
    return _spr(im)

@lru_cache(6)
def keyboard_card(typed, chips=("art", "artists", "AI"), sel=0, pressed=False, caret=True, w=1190):
    ft = font(F_SB, 84); fc = font(F_SB, 72); fk = font(F_MD, 60)
    h = 960
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 50, fill=(208, 211, 218, 248))
    d.rounded_rectangle((30, 30, w - 30, 186), 40, fill=WHITE)
    d.text((70, 58), typed, font=ft, fill=INK)
    if caret:
        cx = 70 + ft.getlength(typed) + 8; d.rectangle((cx, 60, cx + 8, 156), fill=BLUE)
    cw = (w - 60) / 3
    for i, c in enumerate(chips):
        x = 30 + i * cw
        if i == sel:
            d.rounded_rectangle((x + 10, 210, x + cw - 10, 330), 30, fill=BLUE if pressed else WHITE)
        col = WHITE if (i == sel and pressed) else (INK if i == sel else MUTED)
        d.text((x + cw / 2 - fc.getlength(c) / 2, 226), c, font=fc, fill=col)
    rows = ["qwertyuiop", "asdfghjkl", "zxcvbnm"]; ky = 360
    for row in rows:
        kw = (w - 60) / 10; off = 30 + (10 - len(row)) * kw / 2
        for i, ch in enumerate(row):
            x = off + i * kw
            d.rounded_rectangle((x + 6, ky, x + kw - 6, ky + 130), 18, fill=(252, 252, 253, 255))
            d.text((x + kw / 2 - fk.getlength(ch) / 2, ky + 30), ch, font=fk, fill=INK)
        ky += 146
    d.rounded_rectangle((w * 0.24, ky, w * 0.76, ky + 120), 18, fill=(252, 252, 253, 255))
    return _spr(im)

@lru_cache(16)
def label_card(text, sub="", size=92, dark=True, w=0):
    f = font(F_BOLD, size); fs_ = font(F_MD, int(size * 0.68))
    tw = f.getlength(text); sw = fs_.getlength(sub) if sub else 0
    w = w or int(max(tw, sw) + 130)
    h = int(size * 1.55 + (size * 0.95 if sub else 0) + 46)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    bg, fg = (DARK, WHITE) if dark else (CARD_BG, INK)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 44, fill=bg)
    d.text((w / 2 - tw / 2, 30), text, font=f, fill=fg)
    if sub: d.text((w / 2 - sw / 2, 30 + size * 1.32), sub, font=fs_, fill=(fg[0], fg[1], fg[2], 210))
    return _spr(im)

def _to8(a): return (np.clip(a, 0, 1) ** (1 / 2.2) * 255 + 0.5).astype(np.uint8)

@lru_cache(12)
def photo(kind, w, h, filt=0):
    """a picture for a post: a crop of the face in the mirror (or fake grass), with a beauty filter dialled to `filt`/10."""
    if kind == "grass":
        r = np.random.default_rng(2)
        im = Image.new("RGB", (w, h), (40, 120, 40)); d = ImageDraw.Draw(im)
        for y in range(0, h, 2):
            k = y / h; d.line([(0, y), (w, y)], fill=(int(60 + 40 * k), int(150 + 70 * k), int(50 + 20 * k)))
        for _ in range(2600):
            x = r.uniform(0, w); y = r.uniform(h * 0.05, h * 1.05); L = r.uniform(30, 90); a = r.uniform(-0.25, 0.25)
            c = (int(r.uniform(70, 130)), int(r.uniform(170, 235)), int(r.uniform(50, 90)))
            d.line([(x, y), (x + L * math.sin(a), y - L)], fill=c, width=3)
        a8 = np.asarray(im)
    else:
        crops = {"eyes": (0.10, 0.30, 0.90, 0.52), "lips": (0.22, 0.62, 0.78, 0.86), "face": (0.15, 0.24, 0.85, 0.90),
                 "selfie": (0.18, 0.20, 0.82, 0.78)}
        x0, y0, x1, y1 = crops[kind]; f = face(False)
        c = f[int(y0 * GH):int(y1 * GH), int(x0 * GW):int(x1 * GW)]
        ch, cw = c.shape[:2]; ar = w / h
        if cw / ch > ar: nw = int(ch * ar); c = c[:, (cw - nw) // 2:(cw - nw) // 2 + nw]
        else: nh = int(cw / ar); c = c[(ch - nh) // 2:(ch - nh) // 2 + nh]
        a8 = cv2.resize(_to8(c), (w, h), interpolation=cv2.INTER_AREA)
    if filt:
        k = filt / 10
        sm = cv2.bilateralFilter(np.ascontiguousarray(a8), 15, 30 + 70 * k, 9)
        sm = cv2.addWeighted(sm, 0.6 + 0.4 * k, cv2.GaussianBlur(sm, (0, 0), 3), 0.4 * k, 0)
        a8 = cv2.addWeighted(np.ascontiguousarray(a8), 1 - k, sm, k, 0)
        a8 = np.clip(a8.astype(F32) * (1 + 0.22 * k) + np.array([18, 8, 2], F32) * k, 0, 255).astype(np.uint8)
    return Image.fromarray(np.ascontiguousarray(a8)).convert("RGBA")

@lru_cache(6)
def post_card(kind, caption, tag="", sliders=(), filt=0, w=1060, ph=560, user="@just.me"):
    pad = 40; fc = font(F_SB, 76); ft = font(F_SB, 60); fs_ = font(F_MD, 60); fu = font(F_SB, 60)
    pw = w - 2 * pad
    h = pad + 96 + ph + 26 + 96 + (100 if tag else 0) + (len(sliders) * 104 + 14 if sliders else 0) + pad - 6
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 46, fill=CARD_BG)
    im.alpha_composite(_avatar(80, 11), (pad, pad + 4)); d.text((pad + 104, pad + 10), user, font=fu, fill=INK)
    y = pad + 96
    p = photo(kind, pw, ph, filt)
    m = Image.new("L", (pw, ph), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, pw - 1, ph - 1), 26, fill=255)
    im.paste(p, (pad, y), m); y += ph + 26
    d.text((pad + 4, y), caption, font=fc, fill=INK); y += 96
    if tag:
        tw = ft.getlength(tag)
        d.rounded_rectangle((pad, y, pad + tw + 56, y + 84), 42, fill=(255, 214, 10, 255))
        d.text((pad + 28, y + 6), tag, font=ft, fill=INK); y += 100
    for name, val in sliders:
        d.text((pad + 4, y + 14), name, font=fs_, fill=INK)
        bx0, bx1 = pad + 290, w - pad - 140
        d.rounded_rectangle((bx0, y + 40, bx1, y + 56), 8, fill=(200, 200, 208, 255))
        kx = bx0 + (bx1 - bx0) * clamp(val / 100.0)
        d.rounded_rectangle((bx0, y + 40, kx, y + 56), 8, fill=BLUE)
        d.ellipse((kx - 30, y + 18, kx + 30, y + 78), fill=WHITE, outline=(160, 160, 170, 255), width=4)
        d.text((w - pad - 110, y + 14), f"{int(round(val))}", font=fs_, fill=INK)
        y += 104
    return _spr(im)

@lru_cache(6)
def takes_card(n, sel=-1, w=1150):
    cols, rows = 6, 5; pad = 40; gap = 14
    cw = (w - 2 * pad - (cols - 1) * gap) // cols; ch = int(cw * 1.12)
    h = pad + 120 + rows * (ch + gap) + pad - gap
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 46, fill=DARK)
    d.text((pad + 6, pad + 4), f"TAKE {n}/30", font=font(F_MONO, 80), fill=WHITE)
    base = photo("selfie", 360, 400)
    r = np.random.default_rng(4)
    for i in range(cols * rows):
        dx, dy = (int(v) for v in r.integers(0, 50, 2)); g = float(r.uniform(0.7, 1.2))
        if i >= n: continue
        x = pad + (i % cols) * (cw + gap); y = pad + 120 + (i // cols) * (ch + gap)
        c = base.crop((dx, dy, dx + 300, dy + 336)).resize((cw, ch))
        c = Image.eval(c.convert("RGB"), lambda v, g=g: min(255, int(v * g))).convert("RGBA")
        im.paste(c, (x, y))
        if i == sel:
            d.rounded_rectangle((x - 6, y - 6, x + cw + 6, y + ch + 6), 12, outline=BLUE, width=10)
            d.ellipse((x + cw - 64, y + 10, x + cw - 10, y + 64), fill=BLUE)
            d.line([(x + cw - 51, y + 38), (x + cw - 40, y + 50), (x + cw - 22, y + 26)], fill=WHITE, width=7)
    return _spr(im)

@lru_cache(6)
def counter_card(text, sub="", w=0):
    fb = font(F_BLK, 150); fs_ = font(F_MD, 66)
    tw = fb.getlength(text); w = w or int(260 + max(tw, fs_.getlength(sub) if sub else 0) + 90)
    h = 250 + (90 if sub else 0)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 50, fill=DARK)
    im.alpha_composite(_heart_badge(170, 0), (44, 40))
    d.text((250, 34), text, font=fb, fill=WHITE)
    if sub: d.text((250, 222), sub, font=fs_, fill=(220, 220, 228, 255))
    return _spr(im)

@lru_cache(8)
def stamp(text, size=190, rot=-8, col=(226, 36, 58)):
    f = font(F_STAMP, size)
    tw = int(f.getlength(text)); pad = 46
    im = Image.new("RGBA", (tw + pad * 2, int(size * 1.32) + pad), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((10, 10, im.width - 10, im.height - 10), 26, outline=col + (255,), width=16)
    d.text((pad, pad * 0.45), text, font=f, fill=col + (255,))
    a = np.asarray(im).astype(F32) / 255
    r = np.random.default_rng(len(text) + size)
    nz = cv2.GaussianBlur(r.random(a.shape[:2]).astype(F32), (0, 0), 2.4)
    a[..., 3] *= np.clip((nz - 0.36) * 6, 0.3, 1)                     # ink: speckled where the stamp didn't take
    im = Image.fromarray((a * 255).astype(np.uint8)).rotate(rot, expand=True, resample=Image.BICUBIC)
    return _spr(im, sigma=10)

@lru_cache(6)
def pitch_card(kq, w=1150):
    k = kq / 20.0; h = 660
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 46, fill=(20, 22, 28, 244))
    d.text((44, 34), "PITCH CORRECTION", font=font(F_MONO, 60), fill=(170, 178, 196, 255))
    pc = f"{int(k * 100)}%"; fp = font(F_MONO, 60)
    d.text((w - 44 - fp.getlength(pc), 34), pc, font=fp, fill=(255, 214, 10, 255))
    lanes = [200, 290, 380, 470, 560]
    for i, y in enumerate(lanes):
        d.line([(110, y), (w - 44, y)], fill=(62, 66, 80, 255), width=3)
        d.text((48, y - 30), "GFEDC"[i], font=font(F_MONO, 44), fill=(120, 126, 142, 255))
    r = np.random.default_rng(8); notes = [2, 2, 1, 3, 3, 2, 4, 3]; pts = []
    for i in range(260):
        u = i / 259; x = 120 + (w - 180) * u
        n = notes[min(len(notes) - 1, int(u * len(notes)))]
        wob = 38 * math.sin(u * 37) + 24 * math.sin(u * 91 + 1) + 8 * r.standard_normal()
        pts.append((x, lanes[4 - n] + wob * (1 - k)))
    d.line(pts, fill=WHITE, width=8, joint="curve")
    return _spr(im)

@lru_cache(6)
def credits_card(n, w=1040):
    names = ["you", "A. Moreau", "J. Lindqvist", "K. Okafor", "M. Reyes", "S. Patel", "L. Chen", "D. Novak", "R. Haddad", "T. Kimura"]
    h = 150 + n * 94 + 40
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 46, fill=DARK)
    d.text((50, 44), "WRITTEN BY", font=font(F_MONO, 64), fill=(170, 178, 196, 255))
    for i in range(n):
        d.text((50, 150 + i * 94), names[i % len(names)], font=font(F_SB, 74), fill=WHITE)
    return _spr(im)

@lru_cache(4)
def laugh_card(on=1, w=1000):
    h = 400; im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 30, fill=(38, 10, 12, 255), outline=(96, 22, 28, 255), width=14)
    f = font(F_BLK, 210); txt = "LAUGH"
    col = (255, 70, 76, 255) if on else (84, 30, 34, 255)
    d.text((w / 2 - f.getlength(txt) / 2, 62), txt, font=f, fill=col)
    return _spr(im)

@lru_cache(4)
def notif_card(w=1190):
    h = 300; im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 60, fill=(238, 238, 242, 246))
    d.rounded_rectangle((40, 60, 220, 240), 42, fill=(22, 22, 27, 255)); _heart(d, 130, 154, 100, RED)
    d.text((260, 58), "You might like this", font=font(F_SB, 80), fill=INK)
    d.text((260, 162), "before you even searched", font=font(F_MD, 64), fill=MUTED)
    return _spr(im)

@lru_cache(4)
def car_card(w=1150):
    h = 700; im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 50, fill=(14, 16, 20, 246))
    d.polygon([(w * 0.14, h - 34), (w * 0.86, h - 34), (w * 0.56, 190), (w * 0.44, 190)], fill=(42, 46, 56, 255))
    for i in range(6):
        y = 205 + i * 78; k = (y - 190) / (h - 230)
        d.line([(w / 2, y), (w / 2, y + 38)], fill=(225, 225, 225, 255), width=max(3, int(4 + 10 * k)))
    d.line([(w * 0.44, 190), (w * 0.14, h - 34)], fill=(36, 160, 250, 255), width=8)
    d.line([(w * 0.56, 190), (w * 0.86, h - 34)], fill=(36, 160, 250, 255), width=8)
    fm = font(F_MONO, 60); lab = "SELF-DRIVING"
    d.rounded_rectangle((40, 40, 40 + fm.getlength(lab) + 60, 136), 48, fill=(36, 160, 250, 255))
    d.text((70, 52), lab, font=fm, fill=WHITE)
    fb = font(F_BLK, 120); d.text((w - 330, 26), "65", font=fb, fill=WHITE)
    d.text((w - 150, 82), "mph", font=font(F_MD, 56), fill=(176, 176, 186, 255))
    return _spr(im)

@lru_cache(6)
def search_card(typed, caret=True, w=1190):
    h = 190; im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 95, fill=(246, 245, 243, 248))
    d.ellipse((60, 52, 132, 124), outline=(90, 90, 100, 255), width=10); d.line([(122, 118), (154, 150)], fill=(90, 90, 100, 255), width=12)
    f = font(F_SB, 84); d.text((190, 40), typed, font=f, fill=INK)
    if caret:
        x = 190 + f.getlength(typed) + 8; d.rectangle((x, 46, x + 8, 146), fill=BLUE)
    return _spr(im)

@lru_cache(6)
def metric_card(kq, w=1150):
    k = kq / 20.0; h = 660
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 46, fill=(14, 16, 20, 246))
    d.text((48, 44), "ENGAGEMENT", font=font(F_MONO, 64), fill=(170, 178, 196, 255))
    v = f"+{int(312 * k)}%"; fb = font(F_BLK, 120); d.text((w - 48 - fb.getlength(v), 22), v, font=fb, fill=(60, 220, 120, 255))
    pts = []
    for i in range(140):
        u = i / 139
        if u > k: break
        pts.append((60 + (w - 120) * u, h - 70 - (h - 260) * (u ** 2.3) - 22 * math.sin(u * 23) * (1 - u)))
    if len(pts) > 1: d.line(pts, fill=(60, 220, 120, 255), width=10, joint="curve")
    return _spr(im)

@lru_cache(16)
def chip(text, seed=0):
    """a comment bubble: avatar + a few words."""
    f = font(F_SB, 78); tw = f.getlength(text)
    w = int(tw + 210); h = 150
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 75, fill=CARD_BG)
    im.alpha_composite(_avatar(104, 40 + seed), (24, 23))
    d.text((150, 26), text, font=f, fill=INK)
    return _spr(im, sigma=16)

@lru_cache(2)
def cursor(size=150):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    s = size / 100.0
    P = [(8, 4), (8, 82), (28, 64), (42, 94), (56, 88), (43, 59), (70, 59)]
    d.polygon([(x * s, y * s) for x, y in P], fill=(14, 14, 18, 255))
    inner = [(12, 14), (12, 72), (29, 56), (44, 86), (51, 83), (37, 53), (60, 53)]
    d.polygon([(x * s, y * s) for x, y in inner], fill=WHITE)
    return _spr(im, sigma=8)

# ================================================================ lipstick title
@lru_cache(1)
def lipstick():
    """'Mirror, / Mirror, / Look at Us' written on the glass in lipstick: waxy, streaky, slightly broken strokes."""
    f = font(F_MARK, 168)
    im = Image.new("L", (GW, GH), 0); d = ImageDraw.Draw(im)
    y = 236
    for l, dx in (("Mirror,", -150), ("Mirror,", 80), ("Look at Us", 0)):
        w = f.getlength(l); d.text((GW / 2 - w / 2 + dx, y), l, font=f, fill=255); y += 200
    m = np.asarray(im).astype(F32) / 255
    r = np.random.default_rng(17)
    streak = cv2.GaussianBlur(r.random((GH, GW)).astype(F32), (0, 0), sigmaX=9, sigmaY=1.2)
    streak = (streak - streak.min()) / (np.ptp(streak) + 1e-6)
    grit = cv2.GaussianBlur(r.random((GH, GW)).astype(F32), (0, 0), 1.3)
    grit = (grit - grit.min()) / (np.ptp(grit) + 1e-6)
    a = m * np.clip(0.55 + 1.1 * (streak - 0.5) + 0.25, 0.25, 1) * np.clip((grit - 0.22) * 5, 0, 1)
    a = np.clip(cv2.GaussianBlur(a, (0, 0), 0.7) * 1.15, 0, 1)
    hb = cv2.GaussianBlur(m, (0, 0), 3.5)
    gy, gx = np.gradient(hb)
    sheen = np.clip(-(gx + gy) * 9, 0, 1) * m
    col = np.array([0.42, 0.012, 0.035], F32)[None, None] * (0.75 + 0.5 * streak[..., None]) + sheen[..., None] * np.array([0.9, 0.55, 0.55], F32) * 0.55
    ys, xs = np.nonzero(a > 0.01)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    return np.ascontiguousarray(col[y0:y1, x0:x1]).astype(F32), np.ascontiguousarray(a[y0:y1, x0:x1]).astype(F32), (y0, y1, x0, x1)

def draw_lipstick(g, op, light=1.0):
    """lipstick on the glass surface (in front of whatever the glass shows)."""
    if op <= 0.003: return
    col, a, (y0, y1, x0, x1) = lipstick()
    A = (a * op)[..., None]
    reg = g[y0:y1, x0:x1]; reg *= (1 - A); reg += col * light * A

# ================================================================ fog and the fingertip
@lru_cache(1)
def fog_noise():
    r = np.random.default_rng(12)
    h4, w4 = GH // 4, GW // 4
    base = np.zeros((h4, w4), F32)
    for o, s in enumerate((96, 48, 24, 12, 6)):
        g = r.random((h4 // s + 2, w4 // s + 2)).astype(F32)
        base += cv2.resize(g, (w4, h4), interpolation=cv2.INTER_CUBIC) * (0.5 ** o)
    base = (base - base.min()) / (base.max() - base.min())
    return cv2.resize(base, (GW, GH), interpolation=cv2.INTER_CUBIC)

@lru_cache(1)
def fog_noise_lo(): return cv2.GaussianBlur(fog_noise(), (0, 0), 40)

@lru_cache(4)
def _fog_dist(cx, cy):
    yy, xx = np.mgrid[0:GH, 0:GW].astype(F32)
    return np.sqrt(((xx - cx * GW) / GW) ** 2 + ((yy - cy * GH) / GH * 1.45) ** 2)

def fog_density(t, t0, cx=0.5, cy=0.52, grow=1.4, t_off=None, fade=2.2, size=0.62):
    """breath on the glass: spreads from (cx, cy) over `grow` s and evaporates from its edges inward after t_off."""
    if t < t0: return None
    nz = fog_noise(); lo = fog_noise_lo(); d = _fog_dist(cx, cy)
    R = size * (1 - math.exp(-(t - t0) / grow * 2.2))
    dens = np.clip((R - d + (lo - 0.5) * 0.10 + (nz - 0.5) * 0.04) / 0.34, 0, 1)
    if t_off is not None and t > t_off:
        k = (t - t_off) / fade
        dens *= np.clip((1.0 - k * 1.3 - d * 0.9 + (lo - 0.5) * 0.5) / 0.35, 0, 1)
    return dens * (0.85 + 0.15 * nz) * fog_grain()

@lru_cache(1)
def fog_grain():
    r = np.random.default_rng(4)
    return (0.9 + 0.2 * cv2.GaussianBlur(r.random((GH, GW)).astype(F32), (0, 0), 0.9) * 2.5 - 0.25).clip(0.75, 1.15).astype(F32)

@lru_cache(4)
def writing_mask(text, size=196, maxw=980, cy=0.52):
    f = font(F_HAND, size)
    lines = _wrap(text, f, maxw)
    im = Image.new("L", (GW, GH), 0); d = ImageDraw.Draw(im)
    lh = int(size * 0.98); y = GH * cy - len(lines) * lh / 2 - size * 0.12
    total = sum(f.getlength(l) for l in lines); acc = 0.0; boxes = []
    for l in lines:
        w = f.getlength(l); x = GW / 2 - w / 2
        d.text((x, y), l, font=f, fill=255, stroke_width=2, stroke_fill=255)
        boxes.append((x, y + size * 0.55, w, acc)); acc += w; y += lh
    m = cv2.GaussianBlur(np.asarray(im).astype(F32) / 255, (0, 0), 1.1)
    # each row belongs to the line whose middle is nearest; along it, 'order' runs left to right
    rows = np.arange(GH, dtype=F32)[:, None]
    centers = np.array([b[1] for b in boxes], F32)[None, :]
    li = np.argmin(np.abs(rows - centers), axis=1)
    xx = np.arange(GW, dtype=F32)[None, :]
    order = np.empty((GH, GW), F32)
    for i, (x, yc, w, a0) in enumerate(boxes):
        sel = li == i
        order[sel] = np.clip((a0 + (xx - x)) / total, 0, 1)
    return m, order, tuple(lines)

def writing_reveal(text, t, word_times, size=196, maxw=980, cy=0.52, drip=True, per_word=0.34):
    """how much of the text the fingertip has written at time t (each word lands on its sung time), as a mask."""
    m, order, lines = writing_mask(text, size, maxw, cy)
    f = font(F_HAND, size)
    total = sum(f.getlength(l) for l in lines)
    sp = f.getlength(" ")
    pos = []; acc = 0.0
    for l in lines:
        ws = l.split(" ")
        for wi, w in enumerate(ws):
            ww = f.getlength(w); pos.append((acc, ww)); acc += ww + (sp if wi < len(ws) - 1 else 0)
    prog = 0.0
    for (p0, ww), wt in zip(pos, word_times):
        k = clamp((t - wt) / per_word)
        if k > 0: prog = (p0 + ww * k) / total
    if t >= word_times[-1] + per_word: prog = 1.2            # the last letter's tail too
    rev = m * np.clip((prog - order) / 0.010, 0, 1)
    if drip and prog > 0:
        r = np.random.default_rng(len(text))
        cols = np.nonzero(rev.max(0) > 0.6)[0]
        if len(cols):
            for c in r.choice(cols, size=min(10, len(cols)), replace=False):
                rws = np.nonzero(rev[:, c] > 0.6)[0]
                if not len(rws): continue
                ystart = rws.max(); age = max(0.0, t - word_times[0] - 0.8 - r.uniform(0, 1.6))
                L = int(min(200, age * 50))
                if L > 2:
                    sl = rev[ystart:min(GH, ystart + L), max(0, c - 2):c + 3]
                    taper = np.linspace(0.75, 0.15, sl.shape[0], dtype=F32)[:, None]
                    np.maximum(sl, taper, out=sl)
    return rev

FOG_COL = np.array([0.62, 0.58, 0.55], F32)
def apply_fog(g, dens, light, writing=None):
    """fog over the glass: a pale scattering haze lit by the room; where the fingertip went, clear dark glass shows."""
    if dens is None: return
    if writing is not None: dens = dens * (1 - np.clip(writing * 1.1, 0, 1))
    D = dens[..., None]
    g *= (1 - 0.72 * D); g += FOG_COL * (light * 0.16 + 0.002) * D
    if writing is not None:   # beads of water along the cleared strokes catch a little light
        edge = np.clip(cv2.GaussianBlur(writing, (0, 0), 2.0) - writing * 0.8, 0, 1) * dens
        g += (edge * light * 0.05)[..., None] * FOG_COL

# ================================================================ marker lines, rules, the red line
GUIDES = [
    ("dash", [(641, 300), (641, 1600)]),                                               # centre line
    ("dash", [(150, 704), (1130, 704)]),                                               # eye line
    ("line", [(230, 585), (300, 540), (380, 520), (470, 530), (545, 565)]),            # brows
    ("line", [(737, 565), (812, 530), (902, 520), (982, 540), (1052, 585)]),
    ("line", [(540, 1085), (590, 1060), (641, 1052), (692, 1060), (742, 1085)]),       # nose
    ("line", [(445, 1280), (520, 1215), (641, 1196), (762, 1215), (835, 1280), (762, 1345), (641, 1366), (520, 1345), (445, 1280)]),  # lips
    ("line", [(255, 820), (280, 1080), (360, 1330), (470, 1490), (641, 1560), (812, 1490), (922, 1330), (1002, 1080), (1027, 820)]),  # jaw
]
GUIDE_LABELS = [("lift", 240, 430), ("slim", 860, 980), ("fill", 980, 1270), ("smaller", 980, 1500)]

def _partial(pts, k):
    pts = np.array(pts, F32)
    seg = np.r_[0, np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]
    L = seg[-1] * clamp(k)
    if L <= 0: return None
    n = int(np.searchsorted(seg, L))
    if n >= len(pts): return pts
    out = list(pts[:n])
    a = (L - seg[n - 1]) / max(1e-6, seg[n] - seg[n - 1]); out.append(pts[n - 1] + (pts[n] - pts[n - 1]) * a)
    return np.array(out, F32)

MARKER = np.array([0.80, 0.02, 0.05], F32)
def draw_guides(g, k, op, light=1.0):
    """the face measured and marked up in red (a retouch guide): lines draw on with k in 0..1 (staggered)."""
    if op <= 0.003 or k <= 0: return
    m = np.zeros((GH, GW), np.uint8)
    n = len(GUIDES)
    for i, (kind, pts) in enumerate(GUIDES):
        ki = clamp((k - i / n * 0.55) / 0.45)
        P = _partial(pts, ki)
        if P is None or len(P) < 2: continue
        if kind == "dash":
            seg = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
            s = 0.0
            while s < seg[-1]:
                a, b = s, min(seg[-1], s + 34)
                pa = (np.interp(a, seg, P[:, 0]), np.interp(a, seg, P[:, 1])); pb = (np.interp(b, seg, P[:, 0]), np.interp(b, seg, P[:, 1]))
                cv2.line(m, (int(round(pa[0] * 4)), int(round(pa[1] * 4))), (int(round(pb[0] * 4)), int(round(pb[1] * 4))), 255, 6, cv2.LINE_AA, shift=2)
                s += 58
        else:
            cv2.polylines(m, [np.round(P * 4).astype(np.int32)], False, 255, 10, cv2.LINE_AA, shift=2)
    A = (m.astype(F32) / 255 * op * 0.92)[..., None]
    g *= (1 - A); g += MARKER * light * A
    kl = clamp((k - 0.55) / 0.45)
    for i, (word, x, y) in enumerate(GUIDE_LABELS):
        ki = clamp((kl - i * 0.18) / 0.3)
        if ki > 0: blit_tinted(g, _note(word), x, y, op * ki, light)

@lru_cache(8)
def _note(word, size=150):
    f = font(F_HAND, size); w = int(f.getlength(word)) + 30
    im = Image.new("L", (w, int(size * 1.3)), 0); ImageDraw.Draw(im).text((15, 0), word, font=f, fill=255, stroke_width=3, stroke_fill=255)
    return np.asarray(im).astype(F32) / 255

def blit_tinted(g, a, cx, cy, op, light=1.0, col=MARKER):
    h, w = a.shape; xa, ya = int(cx - w / 2), int(cy - h / 2)
    X0, Y0, X1, Y1 = max(0, xa), max(0, ya), min(GW, xa + w), min(GH, ya + h)
    if X1 <= X0 or Y1 <= Y0: return
    A = (a[Y0 - ya:Y1 - ya, X0 - xa:X1 - xa] * op)[..., None]
    reg = g[Y0:Y1, X0:X1]; reg *= (1 - A); reg += col * light * A

def draw_rules(g, k, op):
    """notebook rules ruled across the glass (the rules we keep): thin blue lines and a red margin."""
    if op <= 0.003 or k <= 0: return
    m = np.zeros((GH, GW), np.uint8); mr = np.zeros((GH, GW), np.uint8)
    n = 16
    for i in range(n):
        y = 150 + i * 92; ki = clamp((k - i / n * 0.6) / 0.4)
        if ki <= 0: continue
        cv2.line(m, (40 * 4, y * 4), (int((40 + (GW - 80) * ki) * 4), y * 4), 255, 4, cv2.LINE_AA, shift=2)
    if k > 0.3:
        L = clamp((k - 0.3) / 0.6)
        cv2.line(mr, (190 * 4, 60 * 4), (190 * 4, int((60 + (GH - 120) * L) * 4)), 255, 6, cv2.LINE_AA, shift=2)
    A = (m.astype(F32) / 255 * op * 0.85)[..., None]
    g *= (1 - A); g += np.array([0.10, 0.35, 0.85], F32) * A
    A = (mr.astype(F32) / 255 * op * 0.9)[..., None]
    g *= (1 - A); g += MARKER * A

def draw_red_line(g, k, op, y=880):
    """'then draw the line': one thick marker stroke across the glass, a little uneven."""
    if op <= 0.003 or k <= 0: return
    pts = [(70, y + 14), (300, y + 4), (560, y - 6), (820, y + 2), (1050, y - 8), (1215, y - 2)]
    P = _partial(pts, ease_out(k))
    if P is None or len(P) < 2: return
    m = np.zeros((GH, GW), np.uint8)
    cv2.polylines(m, [np.round(P * 4).astype(np.int32)], False, 255, 26, cv2.LINE_AA, shift=2)
    A = (cv2.GaussianBlur(m.astype(F32) / 255, (0, 0), 1.0) * op)[..., None]
    g *= (1 - A); g += MARKER * 1.05 * A

# ================================================================ the crack, the broken reflection
@lru_cache(1)
def shard_mask():
    """the part of the glass on the lower-right side of the main crack."""
    main, br = V.crack_paths()
    P = main - np.array([V.GX0, V.GY0], F32)
    if P[0, 1] > P[-1, 1]: P = P[::-1]
    poly = np.vstack([P, [[P[-1, 0], GH + 5], [GW + 5, GH + 5], [GW + 5, -5], [P[0, 0], -5]]])
    m = np.zeros((GH, GW), np.uint8)
    cv2.fillPoly(m, [np.round(poly * 4).astype(np.int32)], 255, cv2.LINE_AA, shift=2)
    return m.astype(F32) / 255

@lru_cache(1)
def shard_edge():
    b = cv2.GaussianBlur(shard_mask(), (0, 0), 1.8)
    e = b * (1 - b) * 4.0                       # peaks on the crack line, zero inside and outside
    # only the crack itself, not the glass border
    yy, xx = np.mgrid[0:GH, 0:GW]
    border = (xx < 6) | (xx > GW - 7) | (yy < 6) | (yy > GH - 7)
    e[border] = 0
    return np.clip(e, 0, 1).astype(F32)

def shard_offset(g, dx, dy, brightness=1.0):
    """the lower-right shard sits slightly out of plane: its reflection is shifted (and a hair brighter), and the
    broken edge catches the light."""
    if abs(dx) + abs(dy) < 0.05 and abs(brightness - 1) < 0.005: return g
    m = shard_mask()[..., None]
    sh = cv2.warpAffine(g, np.array([[1, 0, dx], [0, 1, dy]], F32), (GW, GH), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    out = g * (1 - m) + sh * brightness * m
    k = clamp((abs(dx) + abs(dy)) / 20.0)
    out += (shard_edge() * 0.35 * k)[..., None] * np.array([1.0, 0.85, 0.7], F32)
    return out

def crack_glass(k):
    """the face with the crack grown to progress k (0..1)."""
    if k <= 0: return face(False).copy()
    if k >= 1: return face(True).copy()
    a = V.crack_reveal_glass(k)[..., None]
    return face(False) * (1 - a) + face(True) * a
