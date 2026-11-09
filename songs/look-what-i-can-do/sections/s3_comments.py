"""S3 · verse 2, her titles (65.44–80.00 s, frames 1963–2399), staged in the world of "Mirror, Mirror, Look at Us
(The Comment Section)".

Rebuilt from songs/mirror-comments (scene.py + ui.py): the invented dark comment-thread app (graphite cards, outline
hearts, one electric-blue accent, karaoke on the word just sung), the page floating in a dark room above a glossy black
floor that reflects it, photographed by a drifting perspective camera. Here the post is her REAL X post
(post_slopcore.png, "...transition into a Principal Slopcore Architect role."):
  "I'm a Senior Slopcore Architect"  -> the camera is on her real post: highlighter over "Principal Slopcore Architect",
                                        RECEIPT stamp.
  the next five titles                -> her replies in the thread, typed on their sung words, each giving itself away
                                        (Mirror style): What's Next is scheduled for tomorrow; Things That Look Complete
                                        never finished loading; Missing Feet has a 404 avatar; Vibes and Synergy was an
                                        autocomplete suggestion; Artificial Me is AI-generated, and liked by 4 of her.
  "A thought leader by half past three / By four I've got a TED Talk fee!"
                                     -> the post flips into her REAL X profile, whose bio has grown a line per title;
                                        the clock reads 3:30, then 4:00; TED Talk Speaker lands with a Paid partnership.
render_frame(t, W, H) -> HxWx3 uint8. Pure function of t."""
import os, sys, math
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__)); SONG = os.path.dirname(HERE); ROOT = os.path.dirname(os.path.dirname(SONG))
for p in (ROOT, HERE):
    if p not in sys.path: sys.path.insert(0, p)
from studio import core as C

T = C.Timing(SONG)
ASSETS = os.path.join(ROOT, "music", "Look What I Can Do", "assets")
FONTS = C.FONTS
F_SB, F_MD = os.path.join(FONTS, "Inter-SemiBold.otf"), os.path.join(FONTS, "Inter-Medium.otf")
F_BLK, F_BOLD = os.path.join(FONTS, "InterDisplay-Black.otf"), os.path.join(FONTS, "InterDisplay-Bold.otf")
F_MONO = os.path.join(FONTS, "JBMono-700.ttf")
F_STAMP = os.path.join(FONTS, "SairaStencilOne-Regular.ttf")
if not os.path.exists(F_STAMP): F_STAMP = os.path.join(FONTS, "Anton-Regular.ttf")
F_XBIO = F_BOLD

T0, T1 = 1963 / 30.0, 2400 / 30.0

def clamp(x, a=0.0, b=1.0): return a if x < a else b if x > b else x
def sstep(a, b, x):
    if b == a: return 1.0 if x >= b else 0.0
    k = clamp((x - a) / (b - a)); return k * k * (3 - 2 * k)
def ease_io(x): x = clamp(x); return x * x * x * (x * (6 * x - 15) + 10)
def ease_out(x): x = clamp(x); return 1 - (1 - x) ** 3
def lerp(a, b, k): return a + (b - a) * k

# ------------------------------------------------------------------ Mirror's palette (dark mode) + her highlighter
ACCENT = (77, 163, 255); PINK = (255, 61, 108); RED = (232, 44, 62); GREEN = (52, 211, 125); GOLD = (255, 200, 61)
TH = dict(bg=(12, 14, 18), card=(24, 27, 34), card2=(30, 34, 43), text=(238, 240, 245), muted=(132, 139, 153),
          line=(42, 46, 56), input=(28, 31, 39), chip=(38, 43, 54), skel=(58, 64, 78), skel_hi=(92, 100, 118))
HILITE = (255, 225, 77)                          # #ffe14d
X_INK = (15, 20, 25); X_MUTE = (83, 100, 113)
def rgba(c, a=255): return (int(c[0]), int(c[1]), int(c[2]), int(a))

# ------------------------------------------------------------------ the lyric lines
def LINE(sub):
    for L in T.lines:
        if L["text"].startswith(sub): return L
    raise KeyError(sub)
def WT(L, word, nth=0):
    k = 0
    for w, tt in zip(L["words"], L["wt"]):
        if C.norm(w) == C.norm(word):
            if k == nth: return float(tt)
            k += 1
    raise KeyError(word)
L1, L2, L3 = LINE("I'm a Senior Slopcore"), LINE("Chief Executive"), LINE("VP of Things")
L4, L5, L6 = LINE("Director of the Missing"), LINE("Head of Vibes"), LINE("Chief of Artificial")
L7, L8 = LINE("A thought leader"), LINE("By four I've got")
BEATS = np.array(T.beats)

# ------------------------------------------------------------------ fonts / sprites (PIL RGBA at page scale ps)
_FC = {}
def font(path, size):
    k = (path, int(round(size)))
    if k not in _FC: _FC[k] = ImageFont.truetype(path, max(6, int(round(size))))
    return _FC[k]
_SP = {}
def cache(key, fn):
    if key not in _SP:
        if len(_SP) > 700: _SP.clear()
        _SP[key] = fn()
    return _SP[key]

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
    d.polygon([(cx, cy - s), (cx + s * k, cy - s * k), (cx + s, cy), (cx + s * k, cy + s * k), (cx, cy + s), (cx - s * k, cy + s * k),
               (cx - s, cy), (cx - s * k, cy - s * k)], fill=fill)
def draw_bubble(d, x, y, s, outline, width=3):
    d.rounded_rectangle((x, y, x + s, y + s * 0.78), s * 0.3, outline=outline, width=width)
    d.polygon([(x + s * 0.22, y + s * 0.74), (x + s * 0.18, y + s * 0.98), (x + s * 0.42, y + s * 0.76)], fill=outline)
def draw_check(d, cx, cy, s, fill, width=4):
    d.line([(cx - s * 0.45, cy), (cx - s * 0.12, cy + s * 0.32), (cx + s * 0.48, cy - s * 0.36)], fill=fill, width=width, joint="curve")
def pill(d, x, y, text, f, bg, fg, padx=16, h=None):
    tw = f.getlength(text); h = h or int(f.size * 1.45)
    d.rounded_rectangle((x, y, x + tw + 2 * padx, y + h), h // 2, fill=bg)
    d.text((x + padx, y + h / 2), text, font=f, fill=fg, anchor="lm")
    return x + tw + 2 * padx
def wrap_words(words, f, maxw):
    sp = f.getlength(" "); lines = [[]]; x = 0.0
    for w in words:
        ww = f.getlength(w)
        if lines[-1] and x + ww > maxw: lines.append([]); x = 0.0
        lines[-1].append((w, x)); x += ww + sp
    return lines

# ------------------------------------------------------------------ her real images
_IM = {}
def asset(name):
    if name not in _IM:
        im = cv2.imread(os.path.join(ASSETS, name), cv2.IMREAD_COLOR)
        _IM[name] = cv2.cvtColor(im, cv2.COLOR_BGR2RGB) if im is not None else np.full((100, 100, 3), 255, np.uint8)
    return _IM[name]

def circle_img(img8, size):
    im = Image.fromarray(cv2.resize(img8, (size, size), interpolation=cv2.INTER_AREA)).convert("RGBA")
    m = Image.new("L", (size * 4, size * 4), 0); ImageDraw.Draw(m).ellipse((0, 0, size * 4 - 1, size * 4 - 1), fill=255)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0)); out.paste(im, (0, 0), m.resize((size, size), Image.LANCZOS))
    return out

def her_face(): return asset("profile.png")[350:592, 20:262]          # her real avatar (inside the circle; no banner)

def avatar(kind, size):
    """'her' her real avatar, 'clone:i' her avatar (for the clones), '404', 'skel', 'letter:i' a generic letter avatar."""
    def mk():
        if kind.startswith("her") or kind.startswith("clone"): return circle_img(her_face(), size)
        im = Image.new("RGBA", (size * 3, size * 3), (0, 0, 0, 0)); d = ImageDraw.Draw(im); s3 = size * 3
        if kind == "404":
            d.ellipse((0, 0, s3 - 1, s3 - 1), fill=rgba((52, 30, 36)), outline=rgba(RED), width=int(s3 * 0.05))
            d.text((s3 / 2, s3 / 2), "404", font=font(F_MONO, s3 * 0.40), fill=rgba(RED), anchor="mm")
        elif kind == "skel":
            d.ellipse((0, 0, s3 - 1, s3 - 1), fill=rgba(TH["skel"]))
        else:
            i = int(kind.split(":")[1]); rng = np.random.default_rng(i + 3)
            col = tuple(int(v) for v in rng.integers(60, 190, 3))
            d.ellipse((0, 0, s3 - 1, s3 - 1), fill=rgba(col))
            d.text((s3 / 2, s3 / 2), "RG"[i % 2], font=font(F_BOLD, s3 * 0.46), fill=(255, 255, 255, 235), anchor="mm")
        return im.resize((size, size), Image.LANCZOS)
    return cache(("av", kind, size), mk)

# ------------------------------------------------------------------ layout (page px at ps = 1)
PW, PH = 1920, 1080
POST_X, POST_Y, POST_W = 110, 246, 820       # her post, centred in the left column
PROF_Y = 112                                   # her profile (taller), same centre
TX, TW = 990, 830                                  # the thread column
HEAD_Y, VIEW, INP_Y = 52, (140, 930), 958
GAP = 16
PAD, AV, LFS, META = 20, 64, 62, 34
X0 = PAD + AV + 18

# ------------------------------------------------------------------ the thread: who posts what, and what gives it away
class E:
    def __init__(s, t, kind, text, user="aditazzz", av="her", line=None, badges=(), receipt_t=None, punch=(), extra=None):
        s.t, s.kind, s.text, s.user, s.av, s.line = t, kind, text, user, av, line
        s.badges, s.receipt_t, s.punch, s.extra = badges, receipt_t, punch, extra or {}

def _end(L): return float(L["wt"][-1])
ENT = [
    E(T0 - 3.0, "crowd", "congrats on the new role!!", "careerglowup", "letter:0", badges=("Recommended for you",)),
    E(T0 - 2.0, "crowd", "are you open to new opportunities?", "recruiter_ai", "letter:1", badges=("AI-assisted",)),
    E(float(L1["s"]) - 0.12, "lyric", L1["text"], line=L1, badges=("✓ Verified by: herself",), receipt_t=_end(L1) + 0.35, punch=("Slopcore",)),
    E(float(L2["s"]) - 0.12, "lyric", L2["text"], line=L2, badges=("Scheduled · posts tomorrow",), receipt_t=_end(L2) + 0.18, punch=("What's", "Next")),
    E(float(L3["s"]) - 0.12, "lyric", L3["text"], line=L3, badges=("✓ 100% complete",), receipt_t=_end(L3) + 0.2, punch=("Look", "Complete"),
      extra=dict(skeleton=True)),
    E(float(L4["s"]) - 0.12, "lyric", L4["text"], line=L4, badges=("feet.png not found",), receipt_t=_end(L4) + 0.18, punch=("Missing", "Feet"),
      extra=dict(av404=True)),
    E(float(L5["s"]) - 0.12, "lyric", L5["text"], line=L5, badges=(), receipt_t=None, punch=("Vibes", "Synergy"),
      extra=dict(chips=("vibes", "synergy", "alignment"))),
    E(float(L6["s"]) - 0.12, "lyric", L6["text"], line=L6, badges=("AI-generated",), receipt_t=WT(L6, "Artificial") + 0.28, punch=("Artificial", "Me"),
      extra=dict(clones=True, clones_t=WT(L6, "Me") + 0.04)),
]
for i, e in enumerate(ENT): e.id = i
CHIP_T = [WT(L5, "Vibes") - 0.05, WT(L5, "Synergy") - 0.05]

def badge_color(b):
    if b.startswith("AI") or b == "Recommended for you": return ACCENT, (255, 255, 255)
    if b.startswith("✓ Verified"): return ACCENT, (255, 255, 255)
    if b.startswith("✓ 100%"): return GREEN, (12, 20, 16)
    if b.startswith("feet"): return RED, (255, 255, 255)
    if b.startswith("Scheduled"): return GOLD, (20, 20, 20)
    return TH["chip"], TH["text"]

def card_layout(e):
    """static geometry of a card (page px): h, text lines, word boxes."""
    def mk():
        if e.kind == "lyric":
            fl = font(F_SB, LFS); lines = wrap_words(e.text.split(" "), fl, TW - X0 - PAD); lh = int(LFS * 1.16)
        else:
            fl = font(F_SB, 44); lines = wrap_words(e.text.split(" "), fl, TW - X0 - PAD); lh = int(44 * 1.22)
        has_row = bool(e.badges) or bool(e.extra.get("chips"))
        h = PAD + 50 + len(lines) * lh + (64 if has_row else 0) + 8 + 56 + PAD - 6
        words = []; y = PAD + 50
        for ln in lines:
            for w, x in ln: words.append((w, X0 + x, y, fl.getlength(w)))
            y += lh
        return dict(h=h, lines=lines, lh=lh, words=words, row_y=PAD + 50 + len(lines) * lh + 6, foot_y=h - PAD + 6 - 56 + 22)
    return cache(("lay", e.id), mk)

def skel_col(pulse): return tuple(int(lerp(TH["skel"][i], TH["skel_hi"][i], pulse / 7.0)) for i in range(3))

def card_sprite(e, nwords, receipt, chip_sel, ps, pulse=0):
    """the card at page scale ps: background, header, the words typed so far, the receipts row, the footer."""
    def mk():
        Lo = card_layout(e); W, H = int(round(TW * ps)), int(round(Lo["h"] * ps)); q = ps
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        lyric = e.kind == "lyric"
        d.rounded_rectangle((0, 0, W - 1, H - 1), int(26 * q), fill=rgba(TH["card2"] if lyric else TH["card"]))
        if lyric: d.rounded_rectangle((0, 0, int(7 * q), H - 1), int(3 * q), fill=rgba(ACCENT))
        fm, fmm, fb = font(F_SB, META * q), font(F_MD, META * q), font(F_SB, 30 * q)
        y = PAD * q; ux = X0 * q
        d.text((ux, y + 20 * q), "@" + e.user, font=fm, fill=rgba(TH["text"]), anchor="lm"); ux += fm.getlength("@" + e.user) + 12 * q
        if lyric:
            ux = pill(d, ux, y + 1 * q, "Creator", fb, rgba(ACCENT), (255, 255, 255, 255), padx=int(14 * q), h=int(40 * q)) + 12 * q
        meta = "· now" if lyric else "· 2h"
        if lyric and e.badges and e.badges[0].startswith("Scheduled") and receipt: meta = "· tomorrow"
        d.text((ux, y + 20 * q), meta, font=fmm, fill=rgba(ACCENT if meta == "· tomorrow" else TH["muted"]), anchor="lm")
        ff = font(F_SB, (LFS if lyric else 44) * q)
        for k, (w, wx, wy, ww) in enumerate(Lo["words"]):
            if k < nwords: d.text((wx * q, wy * q), w, font=ff, fill=rgba(TH["text"]))
        ry = Lo["row_y"] * q
        if e.extra.get("chips") and nwords > 0:
            cx = X0 * q; fc = font(F_SB, 34 * q)
            for i, c in enumerate(e.extra["chips"]):
                sel = i == chip_sel
                cx = pill(d, cx, ry, c, fc, rgba(ACCENT if sel else TH["chip"]), rgba((255, 255, 255) if sel else TH["text"]), padx=int(18 * q), h=int(52 * q)) + 12 * q
        if receipt and e.badges:
            bx = X0 * q; fbb = font(F_SB, 34 * q)
            for b in e.badges:
                bg, fg = badge_color(b)
                if b.startswith("AI"):
                    bw = fbb.getlength(b) + 74 * q
                    d.rounded_rectangle((bx, ry, bx + bw, ry + 52 * q), int(26 * q), fill=rgba(bg))
                    draw_sparkle(d, bx + 26 * q, ry + 26 * q, 13 * q, rgba(fg)); d.text((bx + 48 * q, ry + 26 * q), b, font=fbb, fill=rgba(fg), anchor="lm")
                    bx += bw + 10 * q
                else:
                    bx = pill(d, bx, ry, b, fbb, rgba(bg), rgba(fg), padx=int(18 * q), h=int(52 * q)) + 10 * q
        fy = Lo["foot_y"] * q
        if e.extra.get("skeleton") and receipt:
            # it "looks complete": the footer never finished loading
            for (x0, w) in ((X0, 54), (X0 + 80, 90), (X0 + 210, 150)):
                d.rounded_rectangle((x0 * q, fy - 13 * q, (x0 + w) * q, fy + 13 * q), int(13 * q), fill=rgba(skel_col(pulse)))
        else:
            draw_heart(d, (X0 + 16) * q, fy, 34 * q, outline=rgba(TH["muted"]), width=max(2, int(3 * q)))
            d.text(((X0 + 150) * q, fy), "Reply", font=fmm, fill=rgba(TH["muted"]), anchor="lm")
            if e.extra.get("clones") and receipt == 2:
                d.text(((X0 + 404) * q, fy), "Liked by 4 of you", font=fmm, fill=rgba(TH["text"]), anchor="lm")
        return im
    return cache(("card", e.id, nwords, receipt, chip_sel, round(ps, 3), pulse), mk)

def nwords_at(e, t):
    if e.kind != "lyric": return 10 ** 6
    return sum(1 for tt in e.line["wt"] if t >= tt - 0.04)

def heights(t):
    """[(entry, eased height)] of what's posted, oldest first."""
    out = []
    for e in ENT:
        if t < e.t: continue
        h = card_layout(e)["h"] * ease_io((t - e.t) / 0.22)
        out.append((e, h))
    return out

def scroll_at(t):
    tot = sum(h + GAP for _, h in heights(t))
    return max(0.0, tot - (VIEW[1] - VIEW[0]) + 18)

# ------------------------------------------------------------------ highlighter
def hilite_dark(page, ps, x, y, w, h, frac, word, size, clip):
    """on a dark card: a yellow band sweeps over the word, the word turns to ink on it."""
    if frac <= 0: return
    y0c, y1c = clip
    X0p, Y0p = int((x - 6) * ps), int((y + size * 0.10) * ps)
    X1f, Y1p = int((x + w + 8) * ps), int((y + size * 1.22) * ps)
    X1p = int(X0p + (X1f - X0p) * clamp(frac))
    Y0p, Y1p = max(Y0p, int(y0c * ps)), min(Y1p, int(y1c * ps))
    if X1p <= X0p or Y1p <= Y0p: return
    band = Image.new("RGBA", (X1p - X0p, Y1p - Y0p), rgba(HILITE))
    page.alpha_composite(band, (X0p, Y0p))
    # the word in ink, clipped to the band
    f = font(F_SB, size * ps)
    tw_ = Image.new("RGBA", (X1f - X0p + 10, int((size * 1.5) * ps)), (0, 0, 0, 0))
    ImageDraw.Draw(tw_).text((int(6 * ps), 0), word, font=f, fill=rgba((20, 18, 10)))
    crop = tw_.crop((0, Y0p - int(y * ps), X1p - X0p, Y1p - int(y * ps)))
    page.alpha_composite(crop, (X0p, Y0p))

def hilite_paper(page, ps, x0, y0, x1, y1, frac, op=1.0):
    """on white paper (her screenshots): multiply, like ink."""
    frac = clamp(frac)
    if frac <= 0 or op <= 0.01: return
    X0p, Y0p, Y1p = int(x0 * ps), int(y0 * ps), int(y1 * ps); X1p = int((x0 + (x1 - x0) * frac) * ps)
    if X1p <= X0p or Y1p <= Y0p: return
    reg = page.crop((X0p, Y0p, X1p, Y1p))
    col = tuple(int(255 - (255 - c) * 0.92 * op) for c in HILITE)
    mul = ImageChops.multiply(reg.convert("RGB"), Image.new("RGB", reg.size, col))
    page.paste(mul, (X0p, Y0p))

# ------------------------------------------------------------------ Mirror's stamp
def stamp_sprite(text, size, rot, ps, col=RED):
    def mk():
        f = font(F_STAMP, size * ps); tw_ = int(f.getlength(text)); pad = int(size * 0.3 * ps)
        im = Image.new("RGBA", (tw_ + pad * 2, int(size * 1.3 * ps) + pad), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.rounded_rectangle((8 * ps, 8 * ps, im.width - 8 * ps, im.height - 8 * ps), int(size * 0.16 * ps), outline=col + (255,), width=max(4, int(size * ps / 11)))
        d.text((pad, pad * 0.45), text, font=f, fill=col + (255,))
        a = np.asarray(im).astype(np.float32) / 255
        r = np.random.default_rng(len(text) + int(size))
        nz = cv2.GaussianBlur(r.random(a.shape[:2]).astype(np.float32), (0, 0), 2.2 * ps)
        a[..., 3] *= np.clip((nz - 0.36) * 6, 0.45, 1)
        return Image.fromarray((a * 255).astype(np.uint8)).rotate(rot, expand=True, resample=Image.BICUBIC)
    return cache(("stamp", text, size, rot, round(ps, 3)), mk)

def paste_c(page, spr, cx, cy, ps, op=1.0, scale=1.0):
    if op <= 0.01: return
    if abs(scale - 1) > 0.01: spr = spr.resize((max(1, int(spr.width * scale)), max(1, int(spr.height * scale))), Image.BILINEAR)
    if op < 0.995:
        spr = spr.copy(); spr.putalpha(spr.getchannel("A").point(lambda v: int(v * op)))
    x, y = int(round(cx * ps - spr.width / 2)), int(round(cy * ps - spr.height / 2))
    comp(page, spr, x, y)

def comp(page, spr, x, y, op=1.0):
    W_, H_ = page.size; xi, yi = int(round(x)), int(round(y))
    X0p, Y0p, X1p, Y1p = max(0, xi), max(0, yi), min(W_, xi + spr.width), min(H_, yi + spr.height)
    if X1p <= X0p or Y1p <= Y0p or op <= 0.004: return
    src = spr.crop((X0p - xi, Y0p - yi, X1p - xi, Y1p - yi))
    if op < 0.995: src = src.copy(); src.putalpha(src.getchannel("A").point(lambda v: int(v * op)))
    page.alpha_composite(src, (X0p, Y0p))

def text_spr(s, path, size, color, ps):
    def mk():
        f = font(path, size * ps); w = int(f.getlength(s)) + 8; h = int(size * 1.4 * ps)
        im = Image.new("RGBA", (max(2, w), max(2, h)), (0, 0, 0, 0)); ImageDraw.Draw(im).text((2, h / 2), s, font=f, fill=rgba(color), anchor="lm")
        return im
    return cache(("t", s, path, size, color, round(ps, 3)), mk)

# ------------------------------------------------------------------ the post (her real X post) and its receipt
WB_PRINCIPAL = (435, 197, 998, 259); WB_ARCH = (246, 282, 541, 332)
def post_card(ps):
    def mk():
        im = asset("post_slopcore.png"); sc = POST_W / im.shape[1]; h = im.shape[0] * sc; pad = 18
        W_, H_ = int(round((POST_W + 2 * pad) * ps)), int(round((h + 2 * pad) * ps))
        card = Image.new("RGBA", (W_, H_), (0, 0, 0, 0)); d = ImageDraw.Draw(card)
        d.rounded_rectangle((0, 0, W_ - 1, H_ - 1), int(26 * ps), fill=(255, 255, 255, 255))
        sm = cv2.resize(im, (int(round(POST_W * ps)), int(round(h * ps))), interpolation=cv2.INTER_AREA)
        card.paste(Image.fromarray(sm), (int(round(pad * ps)), int(round(pad * ps))))
        return card, sc, h, pad
    return cache(("post", round(ps, 3)), mk)

T_SLOP, T_ARCH = WT(L1, "Slopcore"), WT(L1, "Architect")
T_RECEIPT = T_ARCH + 0.32

def draw_post(page, t, ps, op=1.0):
    card, sc, h, pad = post_card(ps)
    comp(page, card, (POST_X - pad) * ps, (POST_Y - pad) * ps, op)
    if op < 0.5: return
    def box(b, pd=8):
        x0, y0, x1, y1 = b
        return POST_X + (x0 - pd) * sc, POST_Y + (y0 - pd * 0.6) * sc, POST_X + (x1 + pd) * sc, POST_Y + (y1 + pd * 0.6) * sc
    hilite_paper(page, ps, *box(WB_PRINCIPAL), (t - (T_SLOP - 0.28)) / 0.32)
    hilite_paper(page, ps, *box(WB_ARCH), (t - T_ARCH + 0.02) / 0.2)
    if t >= T_RECEIPT:
        u = t - T_RECEIPT; scl = 1 + 0.7 * math.exp(-u / 0.05)
        sp = stamp_sprite("RECEIPT", 52, -4, ps)
        paste_c(page, sp, POST_X + 1010 * sc, POST_Y + 360 * sc, ps, clamp(u / 0.04), scl)

# ------------------------------------------------------------------ her real X profile, with a line per title
BULLETS = [(32, 846, 99, 913), (512, 845, 584, 912), (32, 932, 99, 999), (32, 1020, 99, 1086)]
TITLES = ["Senior Slopcore Architect", "Chief Executive of What's Next", "VP of Things That Look Complete",
          "Director of the Missing Feet", "Head of Vibes and Synergy", "Chief of Artificial Me", "Thought Leader", "TED Talk Speaker"]
PROF_PITCH, PROF_TOP, XBIO = 80, 470, 58
T_FLIP = float(L7["s"]) + 0.05            # R6's receipt gets read first
T_TL = WT(L7, "thought"); T_330 = WT(L7, "half"); T_400 = WT(L8, "four"); T_TED = WT(L8, "TED"); T_TALK = WT(L8, "Talk")
def title_times():
    ts = [T_FLIP + 0.30 + 0.045 * j for j in range(6)] + [max(T_TL, T_FLIP + 0.30 + 0.045 * 6), T_TED]
    return ts
TT = title_times()

def profile_canvas(n_lines, typing):
    """native-res (1320 wide) image of her real profile with the bio rewritten as her titles.
    n_lines: titles fully shown; typing: (index, chars) of a line being typed, or None."""
    key = ("prof", n_lines, typing)
    def mk():
        base = asset("profile.png")
        n_total = 8
        Hn = PROF_TOP + n_total * PROF_PITCH + 90 + 90 + 20
        can = np.full((Hn, 1320, 3), 255, np.uint8)
        # avatar (circle, from the real profile, without the banner)
        av = np.asarray(circle_img(her_face(), 236))
        a = av[..., 3:4].astype(np.float32) / 255
        reg = can[24:260, 30:266].astype(np.float32); can[24:260, 30:266] = (reg * (1 - a) + av[..., :3] * a).astype(np.uint8)
        can[290:290 + 175] = base[630:805]                       # name, badge, handle
        im = Image.fromarray(can); d = ImageDraw.Draw(im); f = font(F_XBIO, XBIO)
        for j in range(n_total):
            y = PROF_TOP + j * PROF_PITCH
            s = None
            if j < n_lines: s = TITLES[j]
            elif typing and typing[0] == j: s = TITLES[j][:typing[1]]
            if s is None: continue
            bx0, by0, bx1, by1 = BULLETS[(0, 1, 2, 3, 0, 1, 2, 0)[j]]
            im.paste(Image.fromarray(base[by0:by1, bx0:bx1]), (32, y + 4))
            if s: d.text((117, y - 3), s, font=f, fill=X_INK)
        yb = PROF_TOP + n_total * PROF_PITCH
        im.paste(Image.fromarray(base[1018:1092]), (0, yb + 4))  # her real last bio line: "No video editor. Just Claude Code."
        im.paste(Image.fromarray(base[1100:1182]), (0, yb + 92))   # SoCal · youtube.com/@adita_zzz
        return np.asarray(im)
    return cache(key, mk)

TYPE_D = {6: 0.30, 7: 0.14}                      # how long the last two lines take to type
def profile_state(t):
    n = sum(1 for j, tt in enumerate(TT) if t >= tt + TYPE_D.get(j, 0.0))
    typing = None
    for j in (6, 7):
        if TT[j] <= t < TT[j] + TYPE_D[j]:
            typing = (j, max(1, int(len(TITLES[j]) * clamp((t - TT[j]) / TYPE_D[j])))); n = j
    return n, typing

def profile_card(t, ps):
    n, typing = profile_state(t)
    def mk():
        can = profile_canvas(n, typing); sc = POST_W / 1320.0; pad = 18
        w, h = int(round(POST_W * ps)), int(round(can.shape[0] * sc * ps))
        sm = cv2.resize(can, (w, h), interpolation=cv2.INTER_AREA)
        W_, H_ = int(round((POST_W + 2 * pad) * ps)), h + int(round(2 * pad * ps))
        card = Image.new("RGBA", (W_, H_), (0, 0, 0, 0)); ImageDraw.Draw(card).rounded_rectangle((0, 0, W_ - 1, H_ - 1), int(26 * ps), fill=(255, 255, 255, 255))
        card.paste(Image.fromarray(sm), (int(round(pad * ps)), int(round(pad * ps))))
        return card
    return cache(("pcard", n, typing, round(ps, 3)), mk), POST_W / 1320.0

def draw_profile(page, t, ps, op=1.0, xscale=1.0):
    card, sc = profile_card(t, ps); pad = 18
    if xscale < 0.999:
        card = card.resize((max(1, int(card.width * xscale)), card.height), Image.BILINEAR)
    x = (POST_X - pad + (POST_W + 2 * pad) * (1 - xscale) / 2) * ps
    comp(page, card, x, (PROF_Y - pad) * ps, op)
    if xscale < 0.999 or op < 0.5: return
    n, typing = profile_state(t)
    # cascade: each of the first six lines arrives with a quick highlighter flash
    for j in range(8):
        tj = TT[j]
        if t < tj: continue
        y = PROF_Y + (PROF_TOP + j * PROF_PITCH) * sc
        tw_ = font(F_XBIO, XBIO).getlength(TITLES[j]) * sc
        if j < 6:
            k = 1 - sstep(tj + 0.25, tj + 0.6, t)
            if k > 0.01: hilite_paper(page, ps, POST_X + 108 * sc, y - 2 * sc, POST_X + 117 * sc + tw_ + 10 * sc, y + 74 * sc, clamp((t - tj) / 0.12), 0.75 * k)
        else:
            hilite_paper(page, ps, POST_X + 108 * sc, y - 2 * sc, POST_X + 117 * sc + tw_ + 10 * sc, y + 74 * sc, clamp((t - tj - TYPE_D[j] - 0.02) / 0.14), 0.95)
    # the clock: half past three, then four
    if t >= T_330 - 0.05:
        lab = "3:30 PM" if t < T_400 else "4:00 PM"
        sp = clock_pill(lab, ps)
        kk = ease_out((t - (T_330 - 0.05)) / 0.18); flip = 1.0
        if T_400 <= t < T_400 + 0.2: flip = 1 + 0.18 * math.exp(-(t - T_400) / 0.05)
        cx, cy = POST_X + POST_W - 150, PROF_Y + 110
        paste_c(page, sp, cx, cy + (1 - kk) * 14, ps, kk, flip)
    # the fee
    if t >= T_TALK:
        u = t - T_TALK; sp = gold_pill("Paid partnership", ps)
        y = PROF_Y + (PROF_TOP + 7 * PROF_PITCH) * sc
        x = POST_X + (117 + font(F_XBIO, XBIO).getlength(TITLES[7]) + 34) * sc
        paste_c(page, sp, x + sp.width / ps / 2, y + 36 * sc, ps, clamp(u / 0.06), 1 + 0.5 * math.exp(-u / 0.06))

def clock_pill(lab, ps):
    def mk():
        f = font(F_MONO, 44 * ps); w = int(f.getlength(lab) + 110 * ps); h = int(72 * ps)
        im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.rounded_rectangle((0, 0, w - 1, h - 1), h // 2, fill=rgba((255, 168, 64)))
        cx, cy, r = int(40 * ps), h // 2, int(18 * ps)
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=rgba(X_INK), width=max(2, int(4 * ps)))
        hr = 2 if lab.startswith("3") else 0
        d.line([(cx, cy), (cx, cy - r * 0.7)], fill=rgba(X_INK), width=max(2, int(4 * ps)))
        ang = math.radians(90 + (105 if hr else 120)) if False else None
        d.line([(cx, cy), (cx + (r * 0.55 if not hr else -r * 0.1), cy + (0 if not hr else r * 0.6))], fill=rgba(X_INK), width=max(2, int(4 * ps)))
        d.text((int(72 * ps), h / 2), lab, font=f, fill=rgba(X_INK), anchor="lm")
        return im
    return cache(("clock", lab, round(ps, 3)), mk)

def gold_pill(lab, ps):
    def mk():
        f = font(F_SB, 40 * ps); w = int(f.getlength(lab) + 48 * ps); h = int(60 * ps)
        im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.rounded_rectangle((0, 0, w - 1, h - 1), h // 2, fill=rgba(GOLD))
        d.text((w / 2, h / 2), lab, font=f, fill=rgba((20, 20, 20)), anchor="mm")
        return im
    return cache(("gold", lab, round(ps, 3)), mk)

# ------------------------------------------------------------------ the left column: post -> profile (card flip)
def draw_left(page, t, ps):
    if t < T_FLIP: draw_post(page, t, ps); return
    k = clamp((t - T_FLIP) / 0.30)
    if k >= 1: draw_profile(page, t, ps); return
    w = abs(math.cos(k * math.pi))
    if k < 0.5:
        # the post as it is (highlighter, RECEIPT) squashes edge-on
        card, sc, h, pad = post_card(ps)
        lay = Image.new("RGBA", page.size, (0, 0, 0, 0)); draw_post(lay, t, ps)
        x0, y0 = int(round((POST_X - pad) * ps)), int(round((POST_Y - pad) * ps))
        x1, y1 = x0 + card.width, y0 + card.height
        sp = lay.crop((x0 - int(60 * ps), y0, x1 + int(60 * ps), y1))
        c2 = sp.resize((max(1, int(sp.width * w)), sp.height), Image.BILINEAR)
        comp(page, c2, (x0 + x1) / 2 - c2.width / 2, y0)
    else:
        draw_profile(page, t, ps, 1.0, max(0.01, w))

# ------------------------------------------------------------------ the thread column
def draw_thread(page, t, ps):
    v0, v1 = VIEW; sc = scroll_at(t); y = 0.0
    for e, h in heights(t):
        slot = y; y += h + GAP
        if h < 1: continue
        sy = v0 + slot - sc
        if sy > v1 or sy + h < v0: continue
        age = t - e.t; op = ease_out(age / 0.25)
        nw = nwords_at(e, t); rec = e.receipt_t is not None and t >= e.receipt_t
        if rec and e.extra.get("clones") and t >= e.extra["clones_t"]: rec = 2
        sel = -1
        if e.extra.get("chips"):
            sel = 1 if t >= CHIP_T[1] else (0 if t >= CHIP_T[0] else -1)
        pulse = int(round(3.5 + 3.5 * math.sin(t * 7.0))) if (e.extra.get("skeleton") and rec) else 0
        spr = card_sprite(e, nw, rec, sel, ps, pulse)
        x = TX + (1 - ease_out(age / 0.3)) * 40
        blit_clip(page, spr, x * ps, sy * ps, (v0 * ps, v1 * ps), op, 26 * ps)
        Lo = card_layout(e)
        # avatar
        kind = e.av
        if e.extra.get("av404") and rec: kind = "404"
        if e.extra.get("skeleton") and rec: kind = "skel"
        ax, ay = x + PAD, sy + PAD
        if v0 - 10 <= ay <= v1 - 40:
            if e.extra.get("av404") and e.receipt_t - 0.25 <= t < e.receipt_t + 0.25:      # the avatar card-flips to the 404
                kf = clamp((t - (e.receipt_t - 0.25)) / 0.5); w = abs(math.cos(kf * math.pi))
                a = avatar("her" if kf < 0.5 else "404", int(AV * ps))
                a = a.resize((max(1, int(a.width * w)), a.height), Image.BILINEAR)
                comp(page, a, (ax + AV * (1 - w) / 2) * ps, ay * ps, op)
            else:
                if kind == "skel":
                    sk = Image.new("RGBA", (int(AV * ps), int(AV * ps)), (0, 0, 0, 0))
                    ImageDraw.Draw(sk).ellipse((0, 0, sk.width - 1, sk.height - 1), fill=rgba(skel_col(pulse)))
                    comp(page, sk, ax * ps, ay * ps, op)
                else:
                    comp(page, avatar(kind, int(AV * ps)), ax * ps, ay * ps, op)
        # the clones who liked it: four of her
        if e.extra.get("clones") and rec == 2:
            fy = sy + Lo["foot_y"]
            for j in range(4):
                kj = ease_out((t - e.extra["clones_t"] - 0.06 * j) / 0.16)
                if kj <= 0: continue
                s_ = 44; cx_ = x + X0 + 260 + j * 28
                if v0 <= fy - s_ / 2 and fy + s_ / 2 <= v1:
                    ring = Image.new("RGBA", (int((s_ + 6) * ps), int((s_ + 6) * ps)), (0, 0, 0, 0))
                    ImageDraw.Draw(ring).ellipse((0, 0, ring.width - 1, ring.height - 1), fill=rgba(TH["card2"]))
                    comp(page, ring, (cx_ - 3) * ps, (fy - s_ / 2 - 3) * ps, kj)
                    comp(page, avatar("clone:%d" % j, int(s_ * ps)), cx_ * ps, (fy - s_ / 2 + (1 - kj) * 10) * ps, kj)
        if e.kind != "lyric": continue
        # karaoke: the word just sung in the accent; then the highlighter over the punchline words
        L = e.line; fsz = LFS
        for k_, (w, wx, wy, ww) in enumerate(Lo["words"]):
            tt = L["wt"][k_]
            if t < tt - 0.04: break
            act = math.exp(-max(0.0, t - tt) / 0.38)
            yy = sy + wy
            if act > 0.03 and v0 <= yy and yy + fsz * 1.2 <= v1:
                sp = text_spr(w, F_SB, fsz, ACCENT, ps)
                comp(page, sp, (x + wx - 2) * ps, (yy + fsz * 0.7) * ps - sp.height / 2, act)
        t_end = float(L["wt"][-1])
        j = 0
        for k_, (w, wx, wy, ww) in enumerate(Lo["words"]):
            if C.norm(w) in [C.norm(p) for p in e.punch]:
                frac = (t - (t_end + 0.08 + 0.12 * j)) / 0.16; j += 1
                if frac > 0: hilite_dark(page, ps, x + wx, sy + wy, ww, fsz, frac, w, fsz, (v0, v1))
        # the caret while typing
        if t < t_end + 0.08:
            k_ = nwords_at(e, t)
            if 0 < k_ <= len(Lo["words"]) and int(t * 3.2) % 2 == 0:
                w, wx, wy, ww = Lo["words"][k_ - 1]
                yy = sy + wy
                if v0 <= yy and yy + fsz <= v1:
                    ImageDraw.Draw(page).rectangle(((x + wx + ww + 8) * ps, (yy + 10) * ps, (x + wx + ww + 14) * ps, (yy + fsz * 1.05) * ps), fill=rgba(ACCENT))

def blit_clip(page, spr, x, y, clip, op=1.0, fade=0):
    W_, H_ = page.size; xi, yi = int(round(x)), int(round(y)); y0c, y1c = int(clip[0]), int(clip[1])
    X0p, Y0p, X1p, Y1p = max(0, xi), max(y0c, yi), min(W_, xi + spr.width), min(y1c, yi + spr.height)
    if X1p <= X0p or Y1p <= Y0p or op <= 0.003: return
    src = spr.crop((X0p - xi, Y0p - yi, X1p - xi, Y1p - yi))
    a = np.asarray(src.getchannel("A"), np.float32) * op
    if fade > 0:
        ys = np.arange(Y0p, Y1p, dtype=np.float32)
        a *= np.clip(np.minimum(ys - y0c, y1c - ys) / fade, 0, 1)[:, None]
    src = src.copy(); src.putalpha(Image.fromarray(a.astype(np.uint8)))
    page.alpha_composite(src, (X0p, Y0p))

def header_spr(n, ps):
    def mk():
        W_, h = int(TW * ps), int(74 * ps)
        im = Image.new("RGBA", (W_, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        f = font(F_BOLD, 46 * ps); fm = font(F_MD, 36 * ps)
        d.text((6 * ps, h / 2), "Comments", font=f, fill=rgba(TH["text"]), anchor="lm")
        d.text((6 * ps + f.getlength("Comments") + 18 * ps, h / 2 + 2 * ps), str(n), font=fm, fill=rgba(TH["muted"]), anchor="lm")
        lab = "Sort by: Top"; d.text((W_ - 10 * ps - fm.getlength(lab), h / 2 + 2 * ps), lab, font=fm, fill=rgba(TH["muted"]), anchor="lm")
        return im
    return cache(("hdr", n, round(ps, 3)), mk)

def input_spr(ps):
    def mk():
        W_, h = int(TW * ps), int(86 * ps)
        im = Image.new("RGBA", (W_, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.rounded_rectangle((0, 0, W_ - 1, h - 1), h // 2, fill=rgba(TH["input"]))
        d.text((34 * ps, h / 2), "Add a comment…", font=font(F_MD, 40 * ps), fill=rgba(TH["muted"]), anchor="lm")
        d.text((W_ - 40 * ps, h / 2), "Post", font=font(F_SB, 38 * ps), fill=rgba(TH["muted"]), anchor="rm")
        return im
    return cache(("inp", round(ps, 3)), mk)

# ------------------------------------------------------------------ the page
def page_mask(Wp, Hp, ps):
    def mk():
        r = int(40 * ps); m = np.zeros((Hp, Wp), np.uint8)
        cv2.rectangle(m, (r, 0), (Wp - r, Hp), 255, -1); cv2.rectangle(m, (0, r), (Wp, Hp - r), 255, -1)
        for cx, cy in ((r, r), (Wp - r, r), (r, Hp - r), (Wp - r, Hp - r)): cv2.circle(m, (cx, cy), r, 255, -1, cv2.LINE_AA)
        return m
    return cache(("pmask", Wp, Hp), mk)

def render_page(t, ps):
    Wp, Hp = int(round(PW * ps)), int(round(PH * ps))
    page = Image.new("RGBA", (Wp, Hp), rgba(TH["bg"]))
    draw_thread(page, t, ps)
    n = 2 + sum(1 for e in ENT if e.kind == "lyric" and t >= e.t)
    comp(page, header_spr(n, ps), TX * ps, HEAD_Y * ps)
    comp(page, input_spr(ps), TX * ps, INP_Y * ps)
    dim = 0.55 * sstep(T_FLIP - 0.1, T_FLIP + 0.3, t)
    if dim > 0.01:
        x0 = int((TX - 10) * ps)
        a = np.asarray(page.crop((x0, 0, page.width, page.height))).astype(np.float32)
        a[..., :3] = a[..., :3] * (1 - dim) + np.array(TH["bg"], np.float32) * dim
        page.paste(Image.fromarray(a.astype(np.uint8)), (x0, 0))
    draw_left(page, t, ps)
    arr = np.asarray(page).copy()
    arr[..., 3] = page_mask(Wp, Hp, ps)
    return arr

# ------------------------------------------------------------------ camera (Mirror's floating page)
#        (t, zoom, cx, cy, yaw, pitch)
SHOTS = [(T0 - 0.5, 0.80, 960, 590, -6.0, 2.5), (T0 + 0.06, 0.80, 960, 590, -6.0, 2.5), (T_SLOP - 0.22, 1.40, 548, 520, -2.5, 0.5),
         (T_RECEIPT + 0.5, 1.43, 552, 520, -2.0, 0.5),
         (float(L2["s"]) - 0.02, 1.10, 1180, 545, 2.5, 0.0), (float(L4["s"]), 1.12, 1190, 545, 0.5, 0.0),
         (float(L6["s"]), 1.10, 1185, 540, -1.5, 0.0), (T_FLIP - 0.12, 1.10, 1180, 540, -1.0, 0.0),
         (T_FLIP + 0.36, 1.07, 600, 522, -2.5, 0.3), (T_400, 1.09, 592, 520, -1.5, 0.3), (T1 + 0.5, 1.12, 586, 520, -1.0, 0.3)]
MOVES = {4: (0.38,), 8: (0.48,)}                  # fast moves (s) into these keyframes; the rest ease or drift
def camera(t):
    i = max(0, int(np.searchsorted([s[0] for s in SHOTS], t, side="right")) - 1)
    a = SHOTS[i]; b = SHOTS[min(i + 1, len(SHOTS) - 1)]
    if b is a: k = 0.0
    elif (i + 1) in MOVES:
        d = MOVES[i + 1][0]; k = ease_io(clamp((t - (b[0] - d)) / d))
    else:
        k = ease_io(clamp((t - a[0]) / max(1e-3, b[0] - a[0])))
    z, cx, cy, yaw, pitch = (lerp(a[j], b[j], k) for j in range(1, 6))
    cx += 5 * math.sin(t * 0.31) + 3 * math.sin(t * 0.73 + 1); cy += 3 * math.sin(t * 0.27 + 2)
    yaw += 0.5 * math.sin(t * 0.21); pitch += 0.25 * math.sin(t * 0.17 + 1)
    # a little kick on the receipts
    for tk, amp in ((T_RECEIPT, 0.025), (T_TALK, 0.02)):
        if tk <= t < tk + 0.8: z *= 1 + amp * clamp((t - tk) / 0.03) * math.exp(-(t - tk) / 0.16)
    return z, cx, cy, yaw, pitch

D_CAM = 2600.0
def homography(W, H, ps, z, cx, cy, yaw, pitch):
    """page px (at scale ps) -> output px."""
    s = (H / PH) * z; f = s * D_CAM
    cyw, syw = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    cp, sp = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
    src = np.array([(0, 0), (PW, 0), (PW, PH), (0, PH)], np.float32); dst = []
    for u, v in src:
        X, Y, Z = u - cx, v - cy, 0.0
        X, Z = X * cyw + Z * syw, -X * syw + Z * cyw
        Y, Z = Y * cp - Z * sp, Y * sp + Z * cp
        d = D_CAM + Z; dst.append((W / 2 + f * X / d, H / 2 + f * Y / d))
    return cv2.getPerspectiveTransform(src * ps, np.array(dst, np.float32)), s

def room(W, H):
    def mk():
        yy = np.arange(H, dtype=np.float32)[:, None, None]
        g = (0.020 + 0.016 * (1 - yy / H)) * np.array([0.85, 0.9, 1.0], np.float32)
        return np.ascontiguousarray(np.broadcast_to(g, (H, W, 3))).astype(np.float32)
    return cache(("room", W, H), mk)

def vignette(W, H):
    def mk():
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        d = np.hypot((xx - W / 2) / (W / 2), (yy - H / 2) / (H / 2))
        return np.clip(1 - 0.22 * d ** 2.4, 0, 1)[..., None].astype(np.float32)
    return cache(("vig", W, H), mk)

def grain(W, H, fi):
    def mk():
        r = np.random.default_rng(9)
        return [cv2.resize(r.normal(0, 1, (H // 2, W // 2)).astype(np.float32), (W, H), interpolation=cv2.INTER_NEAREST) for _ in range(6)]
    return cache(("grain", W, H), mk)[fi % 6]

def render_frame(t, W=1920, H=1080):
    t = float(t)
    z, cx, cy, yaw, pitch = camera(t)
    ps = min(1.5, max(0.7, z * H / 1080.0 * 1.02))          # draw the page at the resolution the camera needs
    ps = round(ps * 20) / 20.0
    pg = render_page(t, ps)
    Hm, s = homography(W, H, ps, z, cx, cy, yaw, pitch)
    # the room (half resolution: it is soft): gradient + the page's glow + the glossy floor's reflection
    w2, h2 = W // 2, H // 2
    S2 = np.array([[0.5, 0, 0], [0, 0.5, 0], [0, 0, 1]], np.float64)
    bg = room(w2, h2).copy()
    pc = Hm @ np.array([PW * ps / 2, PH * ps / 2, 1.0]); pc = pc[:2] / pc[2] * 0.5
    rx, ry = PW * s * 0.75 * 0.5, PH * s * 0.75 * 0.5
    yy, xx = np.ogrid[0:h2, 0:w2]
    g = np.exp(-(((xx - pc[0]) / rx) ** 2)).astype(np.float32) * np.exp(-(((yy - pc[1]) / ry) ** 2)).astype(np.float32)
    bg += g[..., None] * np.array([0.10, 0.13, 0.20], np.float32)
    bl = Hm @ np.array([PW * ps / 2, PH * ps, 1.0]); bl = bl[:2] / bl[2]
    if bl[1] < H - 4:
        Hp, Wp = pg.shape[:2]
        small = cv2.resize(pg, (Wp // 3, Hp // 3), interpolation=cv2.INTER_AREA)
        small = cv2.GaussianBlur(small, (0, 0), 1.6)[::-1].astype(np.float32) / 255
        fade = (0.42 * np.exp(-np.arange(small.shape[0], dtype=np.float32) / (small.shape[0] * 0.30)))[:, None]
        small[..., :3] *= small[..., 3:4] * fade[..., None]; small[..., 3] *= fade
        Tm = np.array([[3, 0, 0], [0, 3, Hp + 70 * ps], [0, 0, 1]], np.float64)
        rw = cv2.warpPerspective(small, S2 @ Hm @ Tm, (w2, h2), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
        bg = bg * (1 - rw[..., 3:4]) + rw[..., :3]
    bg = cv2.resize(bg, (W, H), interpolation=cv2.INTER_LINEAR)
    # the page itself
    pw = cv2.warpPerspective(pg, Hm, (W, H), flags=cv2.INTER_LINEAR if s / ps > 0.75 else cv2.INTER_AREA,
                             borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    a = pw[..., 3].astype(np.float32) * (1 / 255.0)
    out = pw[..., :3].astype(np.float32) * (1 / 255.0)
    out -= bg; out *= a[..., None]; out += bg
    out *= vignette(W, H)
    out += (grain(W, H, int(round(t * 30))) * 0.008)[..., None]
    np.clip(out, 0, 1, out=out); out *= 255; out += 0.5
    return out.astype(np.uint8)
