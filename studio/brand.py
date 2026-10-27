"""Brand covers: every YouTube thumbnail is the video's own frame + one consistent top layer.

This is the thumbnail step of the pipeline: `python -m studio.thumbs songs/<slug>` calls song_cover() for every new
video, so its thumbnail matches all the others without any hand work. Songs that render their own thumbnail plates
(e.g. songs/please-hold/make_thumbs.py) call song_cover() on those plates.

usage (from the studio folder), to re-make covers in bulk:
  python3 -m studio.brand                      # every cover listed in brand_covers.yaml
  python3 -m studio.brand rate-limited git-blame
  python3 -m studio.brand --out "<folder>"     # default: <MUSIC_DIR>/_New Brand Covers

The picture underneath is the video's own frame, framed like the original cover (song.yaml ctx_/thumb_ shift,
shift_y, scale and dark). The layer on top is always the same:
  1. the lockup chip, top-left: photo in a green ring, "aditazzz", "</> CLAUDE ANIMATED THIS"
  2. the headline: Anton, black outline, first line(s) ink, last line in the accent (neon green unless the song picks
     red, amber, yellow or ice to suit its frame; never pink)
  3. the description: Instrument Serif italic, one line
What the cover says comes from song.yaml (thumb_lines, thumb_sub, brand_accent); an entry in brand_covers.yaml
overrides it (and covers videos that have no song folder).
"""
import os, sys, argparse, importlib.util
import numpy as np
import yaml
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
FONTS = os.path.join(ROOT, "assets", "fonts")
NAME = "aditazzz"                                       # the name in the lockup chip
PHOTO = os.environ.get("BRAND_PHOTO", os.path.join(ROOT, "assets", "brand", "aditazzz.jpg"))   # square photo for the chip

# brand tokens: aditazzz.github.io site.css + the photo backdrop
BG = (12, 12, 11)          # --bg
INK = (236, 230, 216)      # --ink
WHITE = (255, 255, 255)    # descriptions: brightest white for legibility
GREEN = (116, 227, 106)    # --accent (neon green)
PINK = (247, 157, 183)
RED = (255, 66, 72)        # the one alternate headline accent, for warm/red frames
SNOWFLAKE_BLUE = (41, 181, 232)   # #29B5E8, Snowflake's brand blue (Snowflake Undrop only)
AMBER = (255, 168, 64)            # warm/orange frames
YELLOW = (255, 211, 78)           # purple/teal frames with a yellow subject
ICE = (125, 211, 255)             # icy/blue frames
# headline accents: one short shared set (no pink); the lockup is always neon green
ACCENTS = {"green": None, "red": RED, "amber": AMBER, "yellow": YELLOW, "ice": ICE, "snowflake": SNOWFLAKE_BLUE}     # photo backdrop (only in the photo itself)
OUTLINE = (11, 11, 15)

W, H = 1920, 1080
HEAD_SIZE = 184          # headline: same size on every cover
CODE_SCALE = 0.74         # `code` capitals at 80% of the line's capitals (mono reads bigger)
TAG_SIZE = 46            # series/version label above the headline
TAG_H = 96
BOTTOM = 56              # the text block ends this far above the bottom edge
SUB_SIZE = 88            # description: same size on every cover (readable at phone size)
MX, MY = 64, 56            # lockup position: the same on every cover


def F(name, size): return ImageFont.truetype(os.path.join(FONTS, name), int(size))


# ---------------------------------------------------------------- the picture
def shift(base, sx=0.0, sy=0.0, scale=1.0):
    """Same slide/zoom as studio.thumbs._shift (uncovered edge gets a soft dark blur of the frame)."""
    from studio.thumbs import _shift
    return _shift(base, sx, sy, scale)


def darken(a, side="left", dark=0.62):
    """Same text-side darkening as studio.thumbs.context_card."""
    a = a.astype(np.float32) / 255
    xx = np.linspace(0, 1, a.shape[1], dtype=np.float32)[None, :, None]
    t = xx if side == "left" else 1 - xx
    a *= 1 - dark * np.clip((0.72 - t) / 0.72, 0, 1) ** 0.8
    return (np.clip(a, 0, 1) * 255).astype(np.uint8)


def ctx_picture(base, song, c):
    """The original context-card framing: slide the hero frame aside, darken behind the text."""
    g = lambda k, d: float(c.get(k, song.get("ctx_" + k, song.get("thumb_" + k, d))))
    side = c.get("side", song.get("thumb_hook_side", "left"))
    sx = g("shift", 0); sx = sx if side == "left" else -abs(sx)
    sy = float(c.get("shift_y", song.get("ctx_shift_y", float(song.get("thumb_shift_y", 0)) * 0.5)))
    arr = shift(np.asarray(base.convert("RGB")), sx, sy, g("scale", 1))
    lift = float(c.get("lift", 1.0))                     # >1 brightens the shadows of a very dark frame
    if lift != 1.0:
        arr = (255 * (arr.astype(np.float32) / 255) ** (1 / lift)).clip(0, 255).astype(np.uint8)
    return Image.fromarray(darken(arr, side, float(c.get("dark", song.get("ctx_dark", 0.62)))))


def load_mod(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def callout(img, piece, x, y, w):
    """A framed screen crop with a soft shadow (same as the Screenlife thumbnail's callout)."""
    piece = piece.resize((w, int(piece.height * w / piece.width)), Image.LANCZOS)
    sh = Image.new("L", img.size, 0); ImageDraw.Draw(sh).rounded_rectangle((x + 8, y + 14, x + w + 8, y + piece.height + 14), 18, fill=170)
    img.paste((0, 0, 0), (0, 0), sh.filter(ImageFilter.GaussianBlur(16)))
    ImageDraw.Draw(img).rounded_rectangle((x - 6, y - 6, x + w + 6, y + piece.height + 6), 20, fill=(70, 70, 78))
    m = Image.new("L", piece.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, piece.width - 1, piece.height - 1), 16, fill=255)
    img.paste(piece, (x, y), m)


def special_picture(slug, song):
    """Covers whose original was a one-off design (no old text/badge baked in)."""
    sd = os.path.join(ROOT, "songs", slug)
    if slug == "ted-talk-charts":                      # the Daily Standup front page, banner and all
        m = load_mod(os.path.join(sd, "thumb.py"), "tc_thumb")
        m.badge = lambda *a, **k: 0
        _ban = m.banner
        m.banner = lambda lines, fs, *a, **k: _ban([l.rstrip('.') for l in lines], fs, *a, **k)
        sc = m.sc
        def masthead(cv, W_, vert):                    # same masthead, set right of the lockup
            sc.text(cv, "THE DAILY STANDUP", 1532, 92, sc.F_MAST, 58, sc.INK, 1.0, 'c', 'm', track=3)
            sc.stroke(cv, [(1230, 172), (1840, 172)], sc.INK, 3.0); sc.stroke(cv, [(1230, 181), (1840, 181)], sc.INK, 1.4)
            sc.text(cv, "9:15 A.M.", 1240, 214, sc.F_MONO, 34, sc.RED, 1.0, 'l', 'm')
            sc.text(cv, "PRICE: 15 MINUTES", 1840, 214, sc.F_SANSM, 26, sc.INK2, 1.0, 'r', 'm', track=2)
            sc.stroke(cv, [(1230, 246), (1840, 246)], sc.INK, 1.6)
        m.masthead = masthead
        return m.front(False)
    if slug == "ted-talk-stepping-back":               # the zoom tunnel, slid right
        m = load_mod(os.path.join(sd, "thumb.py"), "tsb_thumb")
        im = m.tunnel(W, H, cx=1235, cy=560, ks=(0.55, 0.34, 0.20)); m.bubble(im, 1235, 568, 0.85)
        return im
    if slug == "ted-talk-screenlife":                  # Ted on his keynote stage + the meeting timer
        m = load_mod(os.path.join(sd, "thumb.py"), "tsl_thumb")
        t = m.sc.TT[4] + 0.9
        base = m.shot(t, 232.0, 352.0, 2.3, cursor=False)
        timer = m.shot(t, 125.0, 81.0, 3.4, cursor=False).crop((420, 470, 1650, 612))
        callout(base, timer, MX + 6, 330, 640)        # the timer is the punchline: big, between the lockup and the headline
        return base
    if slug == "vacation-to-my-bed":                   # poster moved right onto clean paper
        b = Image.open(os.path.join(song["out_dir"], f"{song['title']} - YouTube thumbnail (no text).jpg")).convert("RGB")
        paper = b.crop((W - 860, 0, W, H))
        im = Image.new("RGB", (W, H))
        for x in range(0, W, 860): im.paste(paper, (x, 0))
        im.paste(b.crop((100, 0, 780, H)), (W - 700, 0))
        return Image.fromarray(darken(np.asarray(im), "left", 0.62))
    if slug == "ai-slop-city":
        from studio.render import load_scene
        from studio import core
        sc = load_scene(sd); core.STATE["clean"] = True
        im = Image.fromarray(sc.render_frame(float(song.get("thumb_time", 61.0)), W, H, 5)); core.STATE["clean"] = False
        return ctx_picture(im, song, {})
    return None


# ---------------------------------------------------------------- the top layer
def avatar(d):
    if os.path.exists(PHOTO):
        p = Image.open(PHOTO).convert("RGB").resize((d, d), Image.LANCZOS)
    else:                                                # no photo yet (assets/brand/): a plain dark disc in the ring
        print(f"  note: no lockup photo at {PHOTO}", flush=True)
        p = Image.new("RGB", (d, d), (40, 40, 38))
    ring = max(4, d // 26)
    o = Image.new("RGBA", (d + 2 * ring, d + 2 * ring), (0, 0, 0, 0))
    def disc(n):
        m = Image.new("L", (n * 4, n * 4), 0); ImageDraw.Draw(m).ellipse((0, 0, n * 4 - 1, n * 4 - 1), fill=255)
        return m.resize((n, n), Image.LANCZOS)
    o.paste(Image.new("RGBA", o.size, GREEN + (255,)), (0, 0), disc(o.width))
    o.paste(p, (ring, ring), disc(d))
    return o


def lockup(im):
    """Photo + aditazzz + </> CLAUDE ANIMATED THIS on a site-black chip. Returns its bottom edge."""
    av_d, pad = 156, 24
    fn, fb = F("InstrumentSerif-Regular.ttf", 82), F("JBMono-700.ttf", 58)
    badge = "</> CLAUDE ANIMATED THIS"
    tw = max(fn.getbbox(NAME)[2], fb.getbbox(badge)[2] + 4)
    av = avatar(av_d)
    cw, ch = pad + av.width + 26 + tw + pad + 10, pad * 2 + av.height
    chip = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    ImageDraw.Draw(chip).rounded_rectangle((0, 0, cw - 1, ch - 1), ch // 2, fill=BG + (224,))
    chip.paste(av, (pad, pad), av)
    d = ImageDraw.Draw(chip); tx = pad + av.width + 26
    d.text((tx, pad + 4), NAME, font=fn, fill=INK)
    # badge line: larger, and weighted up with a same-color outline so it reads as extra bold
    d.text((tx + 2, pad + av.height - 72), badge, font=fb, fill=GREEN, stroke_width=2, stroke_fill=GREEN)
    sh = Image.new("L", im.size, 0)
    ImageDraw.Draw(sh).rounded_rectangle((MX + 4, MY + 12, MX + cw + 4, MY + ch + 12), ch // 2, fill=150)
    im.paste((0, 0, 0), (0, 0), sh.filter(ImageFilter.GaussianBlur(16)))
    im.paste(chip, (MX, MY), chip)
    return MY + ch


def _segs(text, upper):
    """Split on `backticks`: code spans keep their case and are set in mono, the rest follows the line style."""
    parts = text.split("`")
    return [(p if i % 2 else (p.upper() if upper else p), bool(i % 2)) for i, p in enumerate(parts) if p]


def _code_font(f, mono, size):
    """Mono font sized so its capitals line up with the line's own capitals."""
    cap = lambda ft: ft.getbbox("H")[3] - ft.getbbox("H")[1]
    return F(mono, size * CODE_SCALE * cap(f) / cap(F(mono, size)))


def rich_w(text, f, fc, upper, chip=False):
    sg = _segs(text, upper)
    pad = _pad(fc) if chip else 0
    return sum((fc if code else f).getlength(t) + (2 * pad if code else 0) for t, code in sg) + _gap(f) * (len(sg) - 1)


def _pad(fc):
    return int(fc.size * 0.22)


def _gap(f):
    return int(f.size * 0.12)                      # extra air where code meets the line's own font


def rich_text(d, xy, text, f, fc, upper, chip=False, **kw):
    """Draw a line with inline `code` spans on a shared baseline. chip=True sets each span in a dark terminal chip."""
    x, y = xy; base = y + f.getmetrics()[0]
    for t, code in _segs(text, upper):
        if code:
            pad = _pad(fc) if chip else 0
            if chip and d.im.mode == "RGB":
                cap = fc.getbbox("H")[3] - fc.getbbox("H")[1]; desc = fc.getmetrics()[1]
                d.rounded_rectangle((x, base - cap - pad, x + fc.getlength(t) + 2 * pad, base + desc * 0.5 + pad * 0.3),
                                    int(pad * 0.8), fill=BG, outline=(60, 60, 56), width=3)
            d.text((x + pad, base), t, font=fc, anchor="ls", **kw)
            x += fc.getlength(t) + 2 * pad + _gap(f)
        else:
            d.text((x, y), t, font=f, **kw)
            x += f.getlength(t) + _gap(f)


def headline(im, lines, sub, side, top, accent=None, tag=None):
    """Anton lines (last one in the accent) + italic description. `backticks` mark commands, set in mono."""
    # one size for every cover: long hooks get another line in brand_covers.yaml, never a smaller font
    lines = [l.rstrip(" .") for l in lines]                 # no trailing periods
    colw = W * 0.64
    size = HEAD_SIZE
    f = F("Anton-Regular.ttf", size); lh = int(size * 1.04); sw = max(5, size // 16)
    fc = _code_font(f, "JBMono-700.ttf", size)
    for l in lines:
        if rich_w(l, f, fc, True, True) > colw:
            print(f"  WARNING: headline line too long, split it in brand_covers.yaml: {l!r}", flush=True)
    sub = sub.rstrip(" .") if sub else sub                 # no trailing period on the description either
    fs = F("InstrumentSerif-Italic.ttf", SUB_SIZE) if sub else None
    fsc = _code_font(fs, "JBMono-400.ttf", SUB_SIZE) if sub else None
    subs = [sub] if sub else []
    if fs and rich_w(sub, fs, fsc, False) > W - 2 * MX - 8:     # descriptions stay on one line unless wider than the cover
        wd = sub.split()
        k = min(range(1, len(wd)), key=lambda k: max(rich_w(" ".join(wd[:k]), fs, fsc, False), rich_w(" ".join(wd[k:]), fs, fsc, False)))
        subs = [" ".join(wd[:k]), " ".join(wd[k:])]
    slh = int(SUB_SIZE * 1.12)
    blockw = max([rich_w(l, f, fc, True, True) + sw for l in lines] + [rich_w(t, fs, fsc, False) for t in subs])
    x0 = MX + 4 if side == "left" else int(W - MX - blockw)
    # the text block sits on one fixed bottom line on every cover (lockup fixed at the top)
    block_h = len(lines) * lh + (len(subs) * slh + 10 if subs else 0)
    y = max(top + (34 + TAG_H if tag else 34), H - BOTTOM - block_h)
    last = y + (len(lines) - 1) * lh + f.getmetrics()[0] + sw
    ys = last + 6 - (fs.getbbox("Ag")[1] if fs else 0)
    shd = Image.new("L", im.size, 0); ds = ImageDraw.Draw(shd)
    for i, l in enumerate(lines):
        rich_text(ds, (x0 + sw, y + i * lh + sw * 1.5), l, f, fc, True, True, fill=215, stroke_width=sw, stroke_fill=215)
    for j, t in enumerate(subs): rich_text(ds, (x0 + 3, ys + j * slh + 5), t, fs, fsc, False, fill=240, stroke_width=9, stroke_fill=240)
    if subs and ys + len(subs) * slh > H - 30:
        print(f"  WARNING: description runs off the bottom, shorten it: {sub!r}", flush=True)
    im.paste((0, 0, 0), (0, 0), shd.filter(ImageFilter.GaussianBlur(sw * 1.4)))
    d = ImageDraw.Draw(im)
    for i, l in enumerate(lines):
        rich_text(d, (x0, y + i * lh), l, f, fc, True, True, fill=(accent or GREEN) if i == len(lines) - 1 else INK, stroke_width=sw, stroke_fill=OUTLINE)
    for j, t in enumerate(subs): rich_text(d, (x0, ys + j * slh), t, fs, fsc, False, fill=WHITE, stroke_width=4, stroke_fill=OUTLINE)
    if tag: draw_tag(im, tag.upper(), x0 + 4, y - TAG_H + 6, accent or GREEN)


def draw_tag(im, tag, x, y, accent):
    """Series / version label: small tracked mono caps on a dark chip, the accent-colored bar marks it as a series."""
    f = F("JBMono-700.ttf", TAG_SIZE); tr = 3
    w = sum(f.getbbox(ch)[2] if ch != " " else f.getlength(" ") for ch in tag) + tr * (len(tag) - 1)
    h = int(TAG_SIZE * 1.55); pad = int(TAG_SIZE * 0.55)
    chip = Image.new("RGBA", (int(w + pad * 2 + 14), h), (0, 0, 0, 0)); d = ImageDraw.Draw(chip)
    d.rounded_rectangle((0, 0, chip.width - 1, h - 1), 8, fill=BG + (215,))
    d.rectangle((0, 0, 6, h - 1), fill=accent + (255,))
    cx = pad + 10
    for ch in tag:
        d.text((cx, h / 2), ch, font=f, fill=INK, anchor="lm")
        cx += (f.getbbox(ch)[2] if ch != " " else f.getlength(" ")) + tr
    x = min(x, W - MX - chip.width)                    # right-side headlines: keep the label on the cover
    im.paste(chip, (int(x), int(y)), chip)


def brand_cover(picture, lines, sub=None, side="left", accent=None, tag=None):
    im = picture.convert("RGB").resize((W, H), Image.LANCZOS)
    bottom = lockup(im)
    if lines: headline(im, lines, sub, side, bottom, accent, tag)
    return im


# ---------------------------------------------------------------- the pipeline's entry point
def config_for(slug):
    """The song's entry in brand_covers.yaml, or {} (song.yaml then decides everything)."""
    p = os.path.join(ROOT, "brand_covers.yaml")
    if not slug or not os.path.exists(p): return {}
    return (yaml.safe_load(open(p, encoding="utf-8")) or {}).get(slug) or {}


def song_cover(song, frame, slug=None, c=None):
    """The brand cover for one clean 16:9 frame of a song (numpy array or PIL image), as a PIL image.
    Text and framing: brand_covers.yaml[slug] first, then song.yaml (thumb_lines, thumb_sub, brand_accent,
    thumb_hook_side, ctx_shift / ctx_shift_y / ctx_scale / ctx_dark)."""
    c = dict(config_for(slug) if c is None else c)
    img = frame if isinstance(frame, Image.Image) else Image.fromarray(np.asarray(frame))
    pic = ctx_picture(img.convert("RGB").resize((W, H), Image.LANCZOS), song, c)
    lines = c.get("lines", song.get("thumb_lines"))
    if not lines:
        print("  WARNING: no thumb_lines in song.yaml (or brand_covers.yaml): the cover has no headline", flush=True)
    side = c.get("side", song.get("thumb_hook_side", "left"))
    accent = ACCENTS[c.get("accent", song.get("brand_accent", "green"))]
    return brand_cover(pic, lines, c.get("sub", song.get("thumb_sub")), side, accent, c.get("tag", song.get("brand_tag")))


# ---------------------------------------------------------------- driver
def build(slug, c, out_dir):
    from studio.config import load_song, MUSIC_DIR
    sd = os.path.join(ROOT, "songs", slug)
    if os.path.isdir(sd) and "folder" not in c:
        song = load_song(sd)
    else:                     # a video without a studio song folder: its frame lives in Original Music/<folder>
        song = {"title": c.get("title", c["folder"]), "folder": c["folder"], "out_dir": os.path.join(MUSIC_DIR, c["folder"])}
    pic = special_picture(slug, song) if os.path.isdir(sd) else None
    if pic is None:
        src = os.path.join(song["out_dir"], c.get("frame") or f"{song['title']} - YouTube thumbnail (no text).jpg")
        pic = ctx_picture(Image.open(src).convert("RGB").resize((W, H), Image.LANCZOS), song, c)
    side = c.get("side", song.get("thumb_hook_side", "left"))
    im = brand_cover(pic, c.get("lines", song.get("thumb_lines")), c.get("sub", song.get("thumb_sub")), side,
                     ACCENTS[c.get("accent", song.get("brand_accent", "green"))], c.get("tag", song.get("brand_tag")))
    name = c.get("name", song.get("folder", song["title"]))
    os.makedirs(out_dir, exist_ok=True)
    p = os.path.join(out_dir, f"{name} - YouTube thumbnail (brand).jpg")
    im.save(p, quality=93)
    return p


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("slugs", nargs="*"); ap.add_argument("--out")
    a = ap.parse_args()
    cfg = yaml.safe_load(open(os.path.join(ROOT, "brand_covers.yaml")))
    from studio.config import MUSIC_DIR
    out = a.out or os.path.join(MUSIC_DIR, "_New Brand Covers")
    for slug in (a.slugs or list(cfg)):
        try:
            print("ok ", build(slug, cfg.get(slug) or {}, out), flush=True)
        except Exception as e:
            print("ERR", slug, repr(e), flush=True)


if __name__ == "__main__":
    main()
