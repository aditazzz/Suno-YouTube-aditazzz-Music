"""The Comment Section's UI kit: an invented comment-thread app in dark and light mode. Everything is drawn with PIL
at page resolution and returned as premultiplied float sprites (sRGB, 0..1) so a frame is a stack of cheap blits.
No real platform's look, logos or names: generic rounded cards, outline hearts, one electric-blue accent."""
import os, math
from functools import lru_cache
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FONTS = os.path.join(ROOT, "assets", "fonts")
F_SB = os.path.join(FONTS, "Inter-SemiBold.otf"); F_MD = os.path.join(FONTS, "Inter-Medium.otf")
F_BLK = os.path.join(FONTS, "InterDisplay-Black.otf"); F_BOLD = os.path.join(FONTS, "InterDisplay-Bold.otf")
F_MONO = os.path.join(FONTS, "JBMono-700.ttf"); F_STAMP = os.path.join(FONTS, "SairaStencilOne-Regular.ttf")
F32 = np.float32

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))

@lru_cache(128)
def font(path, size): return ImageFont.truetype(path, int(size))

# ---------------------------------------------------------------- palette
ACCENT = (77, 163, 255); PINK = (255, 61, 108); RED = (232, 44, 62); GREEN = (52, 211, 125); GOLD = (255, 200, 61)
THEMES = {
    0: dict(bg=(12, 14, 18), panel=(18, 20, 26), card=(24, 27, 34), card2=(30, 34, 43), text=(238, 240, 245),
            muted=(132, 139, 153), line=(42, 46, 56), input=(28, 31, 39), chip=(38, 43, 54), shadow=0.55),
    1: dict(bg=(236, 238, 242), panel=(250, 250, 252), card=(255, 255, 255), card2=(244, 246, 249), text=(16, 18, 22),
            muted=(104, 110, 124), line=(222, 225, 231), input=(238, 240, 244), chip=(228, 232, 238), shadow=0.18),
}
def th(theme, k): return THEMES[theme][k]
def rgba(c, a=255): return (int(c[0]), int(c[1]), int(c[2]), int(a))

# ---------------------------------------------------------------- sprites
def to_sprite(im):
    """PIL RGBA -> (premultiplied rgb float32, alpha float32)."""
    a8 = np.asarray(im).astype(F32) * F32(1 / 255.0)
    al = np.ascontiguousarray(a8[..., 3])
    return np.ascontiguousarray(a8[..., :3] * al[..., None]), al

def blit(dst, spr, x, y, op=1.0, scale=1.0, tint=None):
    """composite a premultiplied sprite with its top-left at (x, y) (page px)."""
    if op <= 0.003: return
    rgb, al = spr
    if abs(scale - 1.0) > 0.003:
        w = max(1, int(round(al.shape[1] * scale))); h = max(1, int(round(al.shape[0] * scale)))
        it = cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR
        rgb = cv2.resize(rgb, (w, h), interpolation=it); al = cv2.resize(al, (w, h), interpolation=it)
    h, w = al.shape; H, W = dst.shape[:2]
    xi, yi = int(round(x)), int(round(y))
    X0, Y0, X1, Y1 = max(0, xi), max(0, yi), min(W, xi + w), min(H, yi + h)
    if X1 <= X0 or Y1 <= Y0: return
    a = al[Y0 - yi:Y1 - yi, X0 - xi:X1 - xi]
    c = rgb[Y0 - yi:Y1 - yi, X0 - xi:X1 - xi]
    if tint is not None: c = a[..., None] * np.asarray(tint, F32)
    reg = dst[Y0:Y1, X0:X1, :3]
    if op < 0.999: reg *= (1 - a * op)[..., None]; reg += c * op
    else: reg *= (1 - a)[..., None]; reg += c

def blit_clip(dst, spr, x, y, clip, op=1.0, fade=0):
    """blit, but only inside the vertical band clip=(y0, y1) of dst, with an optional soft fade (px) at both edges."""
    rgb, al = spr; h, w = al.shape; H, W = dst.shape[:2]
    xi, yi = int(round(x)), int(round(y)); y0c, y1c = int(clip[0]), int(clip[1])
    X0, Y0, X1, Y1 = max(0, xi), max(y0c, yi), min(W, xi + w), min(y1c, yi + h)
    if X1 <= X0 or Y1 <= Y0 or op <= 0.003: return
    a = al[Y0 - yi:Y1 - yi, X0 - xi:X1 - xi] * op; c = rgb[Y0 - yi:Y1 - yi, X0 - xi:X1 - xi] * op
    if fade > 0:
        ys = np.arange(Y0, Y1, dtype=F32)
        f = np.clip(np.minimum(ys - y0c, y1c - ys) / fade, 0, 1)[:, None]
        a = a * f; c = c * f[..., None]
    reg = dst[Y0:Y1, X0:X1, :3]; reg *= (1 - a)[..., None]; reg += c

# ---------------------------------------------------------------- icons
def heart_poly(cx, cy, s, n=40):
    pts = []
    for i in range(n):
        u = i / n * 2 * math.pi
        x = 16 * math.sin(u) ** 3; y = -(13 * math.cos(u) - 5 * math.cos(2 * u) - 2 * math.cos(3 * u) - math.cos(4 * u))
        pts.append((cx + x * s / 34, cy + y * s / 34 - s * 0.04))
    return pts

def draw_heart(d, cx, cy, s, fill=None, outline=None, width=3):
    p = heart_poly(cx, cy, s)
    if fill is not None: d.polygon(p, fill=fill)
    if outline is not None: d.line(p + [p[0]], fill=outline, width=width, joint="curve")

def draw_sparkle(d, cx, cy, s, fill):
    k = 0.28
    p = [(cx, cy - s), (cx + s * k, cy - s * k), (cx + s, cy), (cx + s * k, cy + s * k), (cx, cy + s), (cx - s * k, cy + s * k),
         (cx - s, cy), (cx - s * k, cy - s * k)]
    d.polygon(p, fill=fill)

def draw_bubble(d, x, y, s, outline, width=3):
    d.rounded_rectangle((x, y, x + s, y + s * 0.78), s * 0.3, outline=outline, width=width)
    d.polygon([(x + s * 0.22, y + s * 0.74), (x + s * 0.18, y + s * 0.98), (x + s * 0.42, y + s * 0.76)], fill=outline)

def draw_pin(d, cx, cy, s, fill):
    d.ellipse((cx - s * 0.32, cy - s * 0.5, cx + s * 0.32, cy + s * 0.12), fill=fill)
    d.line([(cx, cy + s * 0.05), (cx, cy + s * 0.55)], fill=fill, width=max(2, int(s * 0.14)))

def draw_check(d, cx, cy, s, fill, width=4):
    d.line([(cx - s * 0.45, cy), (cx - s * 0.12, cy + s * 0.32), (cx + s * 0.48, cy - s * 0.36)], fill=fill, width=width, joint="curve")

def draw_search(d, cx, cy, s, fill, width=5):
    d.ellipse((cx - s * 0.42, cy - s * 0.42, cx + s * 0.22, cy + s * 0.22), outline=fill, width=width)
    d.line([(cx + s * 0.16, cy + s * 0.16), (cx + s * 0.48, cy + s * 0.48)], fill=fill, width=width + 1)

def pill(d, x, y, text, f, bg, fg, padx=16, h=None):
    tw = f.getlength(text); h = h or int(f.size * 1.45)
    d.rounded_rectangle((x, y, x + tw + 2 * padx, y + h), h // 2, fill=bg)
    d.text((x + padx, y + h / 2), text, font=f, fill=fg, anchor="lm")
    return x + tw + 2 * padx

def wrap_words(words, f, maxw):
    """lay out words; returns lines [[(word, x)]] and the line height."""
    sp = f.getlength(" "); lines = [[]]; x = 0.0
    for w in words:
        ww = f.getlength(w)
        if lines[-1] and x + ww > maxw: lines.append([]); x = 0.0
        lines[-1].append((w, x)); x += ww + sp
    return lines

# ---------------------------------------------------------------- avatars
@lru_cache(1)
def cover_rgb():
    im = cv2.cvtColor(cv2.imread(os.path.join(HERE, "assets", "cover_clean.png")), cv2.COLOR_BGR2RGB)
    return im

def _circle(img8, size):
    im = Image.fromarray(cv2.resize(img8, (size, size), interpolation=cv2.INTER_AREA)).convert("RGBA")
    m = Image.new("L", (size * 4, size * 4), 0); ImageDraw.Draw(m).ellipse((0, 0, size * 4 - 1, size * 4 - 1), fill=255)
    m = m.resize((size, size), Image.LANCZOS)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0)); out.paste(im, (0, 0), m)
    return out

# crops of the little pictures that make up the cover's feed (outside the face): crowd avatars
CROWD_SPOTS = [(330, 200), (380, 260), (850, 230), (900, 300), (340, 360), (880, 420), (330, 520), (905, 560), (350, 700),
               (880, 720), (330, 860), (890, 880), (420, 190), (800, 190), (360, 960), (860, 960), (450, 950), (780, 950),
               (520, 200), (700, 200), (320, 620), (910, 640), (330, 430), (900, 480)]
FACE_SPOTS = [(470, 470, 120), (780, 470, 120), (625, 760, 150), (560, 520, 230), (690, 520, 230), (625, 640, 330)]

@lru_cache(64)
def avatar(key, size):
    """'crowd:i' a crop of the cover's feed, 'face:i' the face from the cover, 'bot:i' a generated letter avatar,
    'artist' the cover itself (the artist's avatar). Returns a sprite."""
    kind, _, idx = key.partition(":"); i = int(idx or 0)
    cov = cover_rgb()
    if kind == "crowd":
        x, y = CROWD_SPOTS[i % len(CROWD_SPOTS)]; r = 46
        im = _circle(cov[y - r:y + r, x - r:x + r], size)
    elif kind == "face":
        x, y, r = FACE_SPOTS[i % len(FACE_SPOTS)]
        im = _circle(cov[y - r:y + r, x - r:x + r], size)
    elif kind == "artist":
        im = _circle(cov[60:1194, 60:1194], size)
    elif kind == "filt":           # the same crop, beauty-filtered: smoothed, brightened, warmed
        x, y = CROWD_SPOTS[i % len(CROWD_SPOTS)]; r = 46
        c = cov[y - r:y + r, x - r:x + r].copy()
        for _ in range(3): c = cv2.bilateralFilter(c, 9, 60, 9)
        c = np.clip(c.astype(F32) * 1.22 + np.array([18, 8, 4], F32), 0, 255).astype(np.uint8)
        im = _circle(c, size)
    else:
        rng = np.random.default_rng(i + 3)
        col = tuple(int(v) for v in rng.integers(50, 200, 3))
        im = Image.new("RGBA", (size * 2, size * 2), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.ellipse((0, 0, size * 2 - 1, size * 2 - 1), fill=col + (255,))
        f = font(F_BOLD, int(size * 1.0)); d.text((size, size), "U", font=f, fill=(255, 255, 255, 235), anchor="mm")
        im = im.resize((size, size), Image.LANCZOS)
    return to_sprite(im)

def flip_avatar(dst, a_key, b_key, size, x, y, k):
    """card-flip from avatar a to avatar b: k 0..1 (squash to an edge, swap, open)."""
    if k <= 0: blit(dst, avatar(a_key, size), x, y); return
    if k >= 1: blit(dst, avatar(b_key, size), x, y); return
    key = a_key if k < 0.5 else b_key
    w = abs(math.cos(k * math.pi))
    rgb, al = avatar(key, size)
    ww = max(1, int(round(size * w)))
    s = (cv2.resize(rgb, (ww, size), interpolation=cv2.INTER_AREA), cv2.resize(al, (ww, size), interpolation=cv2.INTER_AREA))
    blit(dst, s, x + (size - ww) / 2, y)

# ---------------------------------------------------------------- comment cards
META = 34
def card_metrics(fmt):
    if fmt == "16x9": return dict(w=830, fs=44, lfs=70, av=64, pad=20, indent=70)
    return dict(w=980, fs=48, lfs=64, av=68, pad=22, indent=64)

@lru_cache(512)
def crowd_card(fmt, theme, user, text, badges=(), top=False, edited=False, chips=(), chip_sel=-1, deleted=False,
               reply=False, system=False):
    """a crowd comment. returns (sprite, info) with info: av=(x, y), heart=(cx, cy), count=(x, y), h, w."""
    M = card_metrics(fmt); T = THEMES[theme]
    W = M["w"] - (M["indent"] if reply else 0); pad = M["pad"]; av = M["av"]
    fm = font(F_SB, META); fmm = font(F_MD, META); ft = font(F_SB, M["fs"]); fb = font(F_SB, 34)
    x0 = pad + av + 18; tw = W - x0 - pad
    words = text.split(" ") if not deleted else "This comment has been deleted".split(" ")
    ff = font(F_MD, M["fs"]) if deleted else ft
    lines = wrap_words(words, ff, tw); lh = int(M["fs"] * 1.22)
    # badge rows (wrap)
    rows = [[]]; bx = 0
    for b in badges:
        bw = fb.getlength(b) + (70 if b.startswith("AI") else 30)
        if rows[-1] and bx + bw > tw: rows.append([]); bx = 0
        rows[-1].append(b); bx += bw + 10
    nb = len(rows) if badges else 0
    h = pad + (54 if top else 0) + 46 + nb * 54 + len(lines) * lh + (70 if chips else 0) + 56 + pad - 6
    im = Image.new("RGBA", (W, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, W - 1, h - 1), 26, fill=rgba(T["card"]))
    y = pad
    if top:
        draw_pin(d, x0 + 10, y + 20, 26, rgba(T["muted"]))
        d.text((x0 + 32, y + 20), "Top comment", font=fmm, fill=rgba(T["muted"]), anchor="lm"); y += 54
    ux = x0
    d.text((ux, y + 20), "@" + user, font=fm, fill=rgba(T["text"]), anchor="lm"); ux += fm.getlength("@" + user) + 12
    meta = "· 2m" + (" · edited" if edited else "")
    d.text((ux, y + 20), meta, font=fmm, fill=rgba(T["muted"]), anchor="lm")
    y += 46
    for row in (rows if badges else []):
        ux = x0
        for b in row:
            col, fg = (ACCENT, (255, 255, 255)) if (b.startswith("AI") or b == "Recommended for you") else \
                      (GOLD, (20, 20, 20)) if b in ("Paid partnership", "Sponsored") else (T["chip"], T["text"])
            if b.startswith("AI"):
                bw = fb.getlength(b) + 70
                d.rounded_rectangle((ux, y + 2, ux + bw, y + 46), 22, fill=rgba(col))
                draw_sparkle(d, ux + 24, y + 24, 12, rgba(fg)); d.text((ux + 44, y + 24), b, font=fb, fill=rgba(fg), anchor="lm")
                ux += bw + 10
            else:
                ux = pill(d, ux, y + 2, b, fb, rgba(col), rgba(fg), padx=15, h=44) + 10
        y += 54
    col = T["muted"] if (deleted or system) else T["text"]
    for ln in lines:
        for w, x in ln: d.text((x0 + x, y + 2), w, font=ff, fill=rgba(col))
        y += lh
    if chips:
        cx = x0; y += 8
        for i, c in enumerate(chips):
            sel = i == chip_sel
            cx = pill(d, cx, y, c, fb, rgba(ACCENT if sel else T["chip"]), rgba((255, 255, 255) if sel else T["text"]), padx=16, h=48) + 10
        y += 62
    y += 6
    hx, hy = x0 + 16, y + 22
    draw_heart(d, hx, hy, 34, outline=rgba(T["muted"]), width=3)
    d.text((x0 + 150, hy), "Reply", font=fmm, fill=rgba(T["muted"]), anchor="lm")
    return to_sprite(im), dict(av=(pad, pad + (54 if top else 0)), heart=(hx, hy), count=(x0 + 42, hy), h=h, w=W)

def pin_metrics(fmt):
    if fmt == "16x9": return dict(av=52, pad=16, fs=44, r1=44, r2=56, r3=58)
    return dict(av=56, pad=16, fs=48, r1=46, r2=60, r3=60)

@lru_cache(64)
def pinned_card(fmt, theme, user, text, chips=(), chip_sel=-1, badges=()):
    """the top comment, pinned under the thread's header: compact (avatar, handle and a pin label on one row, the text
    with its likes on the next) plus one receipts row (autocomplete chips or badges). returns (sprite, info)."""
    M = card_metrics(fmt); P = pin_metrics(fmt); T = THEMES[theme]
    W = M["w"]; pad = P["pad"]; av = P["av"]
    fm = font(F_SB, META); fmm = font(F_MD, META); ft = font(F_SB, P["fs"]); fb = font(F_SB, 34)
    x0 = pad + av + 16
    row3 = bool(chips) or bool(badges)
    h = pad + P["r1"] + P["r2"] + (P["r3"] if row3 else 0) + pad - 2
    im = Image.new("RGBA", (W, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, W - 1, h - 1), 26, fill=rgba(T["card"]), outline=rgba(ACCENT), width=3)
    y = pad
    d.text((x0, y + P["r1"] / 2), "@" + user, font=fm, fill=rgba(T["text"]), anchor="lm")
    ux = x0 + fm.getlength("@" + user) + 12
    d.text((ux, y + P["r1"] / 2), "· 2m", font=fmm, fill=rgba(T["muted"]), anchor="lm")
    lab = "Top comment"; lw = fmm.getlength(lab)
    d.text((W - pad - 6, y + P["r1"] / 2), lab, font=fmm, fill=rgba(ACCENT), anchor="rm")
    draw_pin(d, W - pad - 6 - lw - 22, y + P["r1"] / 2 + 2, 26, rgba(ACCENT))
    y += P["r1"]
    d.text((x0, y + P["r2"] / 2), text, font=ft, fill=rgba(T["text"]), anchor="lm")
    hx, hy = W - pad - 150, y + P["r2"] / 2
    draw_heart(d, hx, hy, 34, outline=rgba(T["muted"]), width=3)
    y += P["r2"]
    if chips:
        cx = x0
        for i, c in enumerate(chips):
            sel = i == chip_sel
            cx = pill(d, cx, y + 4, c, fb, rgba(ACCENT if sel else T["chip"]), rgba((255, 255, 255) if sel else T["text"]), padx=16, h=48) + 10
    elif badges:
        ux = x0
        for b in badges:
            col, fg = (ACCENT, (255, 255, 255)) if (b.startswith("AI") or b == "Recommended for you") else (T["chip"], T["text"])
            if b.startswith("AI"):
                bw = fb.getlength(b) + 70
                d.rounded_rectangle((ux, y + 6, ux + bw, y + 50), 22, fill=rgba(col))
                draw_sparkle(d, ux + 24, y + 28, 12, rgba(fg)); d.text((ux + 44, y + 28), b, font=fb, fill=rgba(fg), anchor="lm")
                ux += bw + 10
            else:
                ux = pill(d, ux, y + 6, b, fb, rgba(col), rgba(fg), padx=15, h=44) + 10
    return to_sprite(im), dict(av=(pad, pad + (P["r1"] + P["r2"] - av) / 2), heart=(hx, hy), count=(hx + 26, hy), h=h, w=W)

@lru_cache(512)
def lyric_card(fmt, theme, text, nwords, reply=True):
    """a reply from the artist with the sung line: only the first `nwords` words are written so far (the rest are
    reserved space). returns (sprite, info) with info['words'] = [(word, x, y, w)] in card px (all words)."""
    M = card_metrics(fmt); T = THEMES[theme]
    W = M["w"] - (M["indent"] if reply else 0); pad = M["pad"]; av = M["av"]
    fm = font(F_SB, META); fmm = font(F_MD, META); fb = font(F_SB, 30); fl = font(F_SB, M["lfs"])
    x0 = pad + av + 18; tw = W - x0 - pad
    words = text.split(" "); lines = wrap_words(words, fl, tw); lh = int(M["lfs"] * 1.16)
    h = pad + 46 + len(lines) * lh + 10 + 56 + pad - 6
    im = Image.new("RGBA", (W, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, W - 1, h - 1), 26, fill=rgba(T["card2"]))
    d.rounded_rectangle((0, 0, 7, h - 1), 3, fill=rgba(ACCENT))
    y = pad
    d.text((x0, y + 20), "@aditazzz", font=fm, fill=rgba(T["text"]), anchor="lm")
    ux = x0 + fm.getlength("@aditazzz") + 12
    ux = pill(d, ux, y + 1, "Creator", fb, rgba(ACCENT), (255, 255, 255, 255), padx=14, h=40) + 12
    d.text((ux, y + 20), "· now", font=fmm, fill=rgba(T["muted"]), anchor="lm")
    y += 50
    info = []; k = 0
    for ln in lines:
        for w, x in ln:
            if k < nwords: d.text((x0 + x, y), w, font=fl, fill=rgba(T["text"]))
            info.append((w, x0 + x, y, fl.getlength(w))); k += 1
        y += lh
    y += 10
    hx, hy = x0 + 16, y + 22
    draw_heart(d, hx, hy, 34, outline=rgba(T["muted"]), width=3)
    d.text((x0 + 150, hy), "Reply", font=fmm, fill=rgba(T["muted"]), anchor="lm")
    return to_sprite(im), dict(av=(pad, pad), heart=(hx, hy), count=(x0 + 42, hy), h=h, w=W, words=info, lfs=M["lfs"])

@lru_cache(256)
def word_sprite(word, size, color):
    f = font(F_SB, size)
    w = int(f.getlength(word)) + 8; h = int(size * 1.4)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); ImageDraw.Draw(im).text((0, 0), word, font=f, fill=rgba(color))
    return to_sprite(im)

@lru_cache(512)
def text_sprite(text, path, size, color):
    f = font(path, size)
    w = int(f.getlength(text)) + 6; h = int(size * 1.35)
    im = Image.new("RGBA", (max(1, w), h), (0, 0, 0, 0)); ImageDraw.Draw(im).text((0, h / 2), text, font=f, fill=rgba(color), anchor="lm")
    return to_sprite(im)

@lru_cache(64)
def heart_sprite(size, theme, state):
    """state: 'outline', 'liked' (filled pink) or 'broken:k' (k 1..4: the crack opening)."""
    T = THEMES[theme]
    im = Image.new("RGBA", (size * 2, size * 2), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    c = size
    if state == "outline": draw_heart(d, c, c, size * 1.7, outline=rgba(T["muted"]), width=5)
    else:
        draw_heart(d, c, c, size * 1.7, fill=rgba(PINK))
        if state.startswith("broken"):
            k = int(state.split(":")[1]) / 4
            p = [(c + 2, c - size * 0.62), (c - size * 0.16, c - size * 0.2), (c + size * 0.14, c + size * 0.1), (c - size * 0.1, c + size * 0.4), (c, c + size * 0.75)]
            d.line(p, fill=(0, 0, 0, 0), width=max(2, int(size * 0.22 * k)), joint="curve")
    im = im.resize((size, size), Image.LANCZOS)
    return to_sprite(im)

def fmt_count(n):
    if n >= 999500: return "999K+"
    if n >= 10000: return f"{n / 1000:.0f}K" if n >= 100000 else f"{n / 1000:.1f}K"
    if n >= 1000: return f"{n / 1000:.1f}K"
    return str(int(n))

# ---------------------------------------------------------------- panels and cards
@lru_cache(8)
def input_box(fmt, theme, text, caret, placeholder=True, post_hot=False, suggested=False):
    T = THEMES[theme]; W = 830 if fmt == "16x9" else 980; h = 86
    im = Image.new("RGBA", (W, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, W - 1, h - 1), h // 2, fill=rgba(T["input"]))
    f = font(F_SB, 40); fm = font(F_MD, 40)
    if text: d.text((34, h / 2), text, font=f, fill=rgba(T["text"]), anchor="lm")
    elif placeholder: d.text((34, h / 2), "Add a comment…", font=fm, fill=rgba(T["muted"]), anchor="lm")
    if caret:
        cx = 34 + (f.getlength(text) + 4 if text else 0)
        d.rectangle((cx, h / 2 - 26, cx + 5, h / 2 + 26), fill=rgba(ACCENT))
    if suggested:
        fb = font(F_SB, 28); pill(d, W - 330, 20, "Suggested", fb, rgba(ACCENT), (255, 255, 255, 255), padx=14, h=46)
    fb = font(F_SB, 38)
    d.text((W - 40, h / 2), "Post", font=fb, fill=rgba(ACCENT if (text or post_hot) else T["muted"]), anchor="rm")
    return to_sprite(im)

@lru_cache(16)
def header(fmt, theme, count_text, sort="Top"):
    T = THEMES[theme]; W = 830 if fmt == "16x9" else 980; h = 74
    im = Image.new("RGBA", (W, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    f = font(F_BOLD, 46); fm = font(F_MD, 36)
    d.text((6, h / 2), "Comments", font=f, fill=rgba(T["text"]), anchor="lm")
    x = 6 + f.getlength("Comments") + 18
    d.text((x, h / 2 + 2), count_text, font=fm, fill=rgba(T["muted"]), anchor="lm")
    lab = f"Sort by: {sort}  ▾" if False else f"Sort by: {sort}"
    tw = fm.getlength(lab)
    d.text((W - 10 - tw, h / 2 + 2), lab, font=fm, fill=rgba(ACCENT if sort != "Top" else T["muted"]), anchor="lm")
    return to_sprite(im)

@lru_cache(8)
def search_bar(fmt, theme, text, caret):
    T = THEMES[theme]; W = 830 if fmt == "16x9" else 980; h = 86
    im = Image.new("RGBA", (W, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, W - 1, h - 1), h // 2, fill=rgba(T["input"]), outline=rgba(ACCENT), width=3)
    draw_search(d, 46, h / 2, 34, rgba(T["muted"]))
    f = font(F_SB, 44); d.text((90, h / 2), text, font=f, fill=rgba(T["text"]), anchor="lm")
    if caret:
        cx = 90 + f.getlength(text) + 4; d.rectangle((cx, h / 2 - 26, cx + 5, h / 2 + 26), fill=rgba(ACCENT))
    return to_sprite(im)

@lru_cache(8)
def guidelines_card(fmt, theme, checks=0):
    T = THEMES[theme]; W = 830 if fmt == "16x9" else 980
    rules = ["Be kind", "No bots", "No AI art", "Human feelings only"]
    f = font(F_BOLD, 44); fr = font(F_SB, 42)
    h = 30 + 66 + len(rules) * 64 + 26
    im = Image.new("RGBA", (W, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, W - 1, h - 1), 26, fill=rgba(T["card2"]), outline=rgba(ACCENT), width=3)
    draw_pin(d, 44, 64, 30, rgba(ACCENT))
    d.text((74, 64), "Community guidelines", font=f, fill=rgba(T["text"]), anchor="lm")
    for i, r in enumerate(rules):
        y = 30 + 66 + i * 64 + 32
        d.text((44, y), f"{i + 1}.", font=fr, fill=rgba(T["muted"]), anchor="lm")
        d.text((96, y), r, font=fr, fill=rgba(T["text"]), anchor="lm")
        if i < checks: draw_check(d, W - 70, y, 38, rgba(GREEN), width=6)
    return to_sprite(im)

@lru_cache(8)
def report_sheet(fmt, theme, checked=0):
    T = THEMES[theme]; W = 830 if fmt == "16x9" else 980
    opts = ["Looks AI-made", "Too perfect", "Not real art", "It made me feel something"]
    f = font(F_BOLD, 46); fr = font(F_SB, 42)
    h = 30 + 70 + len(opts) * 72 + 26
    im = Image.new("RGBA", (W, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, W - 1, h - 1), 28, fill=rgba(T["card2"]))
    d.text((40, 64), "Report this post", font=f, fill=rgba(T["text"]), anchor="lm")
    for i, o in enumerate(opts):
        y = 30 + 70 + i * 72 + 36
        on = i < checked
        d.rounded_rectangle((40, y - 22, 84, y + 22), 10, fill=rgba(RED if on else T["chip"]))
        if on: draw_check(d, 62, y, 30, (255, 255, 255, 255), width=5)
        d.text((104, y), o, font=fr, fill=rgba(T["text"]), anchor="lm")
    return to_sprite(im)

@lru_cache(24)
def insights_card(fmt, theme, kq):
    k = kq / 20.0; T = THEMES[theme]; W = 830 if fmt == "16x9" else 980; h = 360
    im = Image.new("RGBA", (W, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, W - 1, h - 1), 26, fill=rgba(T["card2"]))
    d.text((40, 56), "Post insights", font=font(F_BOLD, 44), fill=rgba(T["text"]), anchor="lm")
    v = f"+{int(312 * k)}%"; fb = font(F_BLK, 76)
    d.text((W - 40, 58), v, font=fb, fill=rgba(GREEN), anchor="rm")
    pts = []
    for i in range(120):
        u = i / 119
        if u > k: break
        pts.append((50 + (W - 100) * u, h - 50 - (h - 170) * (u ** 2.2) - 16 * math.sin(u * 21) * (1 - u)))
    if len(pts) > 1: d.line(pts, fill=rgba(GREEN), width=8, joint="curve")
    d.text((40, 120), "Engagement", font=font(F_MD, 36), fill=rgba(T["muted"]), anchor="lm")
    return to_sprite(im)

@lru_cache(8)
def dialog(fmt, theme, pressed=False):
    T = THEMES[theme]; W = 700 if fmt == "16x9" else 820; h = 300
    im = Image.new("RGBA", (W, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, W - 1, h - 1), 34, fill=rgba(T["card2"]))
    d.text((W / 2, 74), "Discard comment?", font=font(F_BOLD, 50), fill=rgba(T["text"]), anchor="mm")
    d.text((W / 2, 140), "It won't be posted.", font=font(F_MD, 38), fill=rgba(T["muted"]), anchor="mm")
    d.line([(0, 196), (W, 196)], fill=rgba(T["line"]), width=2)
    d.line([(W / 2, 196), (W / 2, h)], fill=rgba(T["line"]), width=2)
    if pressed: d.rounded_rectangle((W / 2 + 2, 198, W - 2, h - 2), 30, fill=rgba(T["chip"]))
    d.text((W * 0.25, 248), "Keep", font=font(F_SB, 44), fill=rgba(T["text"]), anchor="mm")
    d.text((W * 0.75, 248), "Discard", font=font(F_SB, 44), fill=rgba(RED), anchor="mm")
    return to_sprite(im)

@lru_cache(8)
def training_chip(fmt, theme, kq):
    k = kq / 40.0; T = THEMES[theme]; W = 760 if fmt == "16x9" else 900; h = 150
    im = Image.new("RGBA", (W, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, W - 1, h - 1), 30, fill=rgba(T["card2"]), outline=rgba(ACCENT), width=3)
    n = int(4812330 * k)
    d.text((36, 52), f"Learning from {n:,} comments", font=font(F_SB, 40), fill=rgba(T["text"]), anchor="lm")
    d.rounded_rectangle((36, 96, W - 36, 116), 10, fill=rgba(T["chip"]))
    d.rounded_rectangle((36, 96, 36 + (W - 72) * k, 116), 10, fill=rgba(ACCENT))
    return to_sprite(im)

@lru_cache(16)
def stamp(text, size, rot=-8, col=(232, 44, 62)):
    f = font(F_STAMP, size)
    tw = int(f.getlength(text)); pad = int(size * 0.3)
    im = Image.new("RGBA", (tw + pad * 2, int(size * 1.3) + pad), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((8, 8, im.width - 8, im.height - 8), int(size * 0.16), outline=col + (255,), width=max(6, size // 11))
    d.text((pad, pad * 0.45), text, font=f, fill=col + (255,))
    a = np.asarray(im).astype(F32) / 255
    r = np.random.default_rng(len(text) + size)
    nz = cv2.GaussianBlur(r.random(a.shape[:2]).astype(F32), (0, 0), 2.2)
    a[..., 3] *= np.clip((nz - 0.36) * 6, 0.35, 1)
    im = Image.fromarray((a * 255).astype(np.uint8)).rotate(rot, expand=True, resample=Image.BICUBIC)
    return to_sprite(im)

@lru_cache(8)
def label_chip(text, size, bg, fg=(255, 255, 255)):
    f = font(F_SB, size); h = int(size * 1.6); w = int(f.getlength(text) + size * 1.3)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), h // 2, fill=rgba(bg))
    d.text((w / 2, h / 2), text, font=f, fill=rgba(fg), anchor="mm")
    return to_sprite(im)
