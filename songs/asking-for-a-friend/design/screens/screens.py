"""The film's screens and signs as texture sources (CREATIVE.md §13.2), plus flat review cards. PIL only, no GPU.

  python3 screens.py textures          # all stills -> board/ clock/ scheduler/ tag/ emergency/
  python3 screens.py board 390         # one board frame (a pure function of the film frame f) -> board/board_f0390.png
  python3 screens.py board 366 572     # a range -> board/board_f####.png

Every texture is drawn at a fixed px/mm, so sizes in mm (and so in final pixels at a camera's px/m) are exact.
See SPEC.md for the physical sizes and NOTES.md for the size checks.
"""
import json, math, os, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
FONTS = os.path.join(ROOT, "assets", "fonts")
SONG = os.path.abspath(os.path.join(HERE, "..", ".."))


def F(name, px):
    return ImageFont.truetype(os.path.join(FONTS, name), int(round(px)))


ANTON, INTER_SB, INTER = "Anton-Regular.ttf", "Inter-SemiBold.otf", "Inter-Regular.otf"
VT, JB, SAIRA, MARKER = "VT323-Regular.ttf", "JBMono-700.ttf", "SairaStencilOne-Regular.ttf", "PermanentMarker-Regular.ttf"
CAP = {ANTON: 0.859, INTER_SB: 0.728, VT: 0.56, JB: 0.73, SAIRA: 0.716, MARKER: 0.695}   # cap height / em, measured


import contextlib
from contextlib import nullcontext
sys.path.insert(0, ROOT)
from studio import textfit
REC = None                                # the active studio.textfit.Recorder while a texture is built for the fit check


def box(b, name="box"):
    """Declare the container the text drawn inside this `with` must stay in (checked by tools/text_fit_check.py)."""
    return REC.container(b, name) if REC is not None else nullcontext()


def skip():
    return REC.skip() if REC is not None else nullcontext()


def hexc(h, a=None):
    h = h.lstrip("#")
    c = tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    return c + (a,) if a is not None else c


def glow_layer(img, radius, strength=1.0):
    """Screen-add a blurred copy (a real emitter's halo, kept tight so type stays crisp)."""
    g = img.filter(ImageFilter.GaussianBlur(radius))
    if strength != 1.0:
        g = g.point(lambda v: int(v * strength))
    return ImageChops.add(img, g)


# ====================================================================== 1. the status board
BW, BH = 3200, 1800                      # px = mm
B_GREEN = hexc("#0B7A57")
B_INK = hexc("#F3F6EE")                  # off-white type
B_SOFT = hexc("#CFEFDD")                 # fine print, a touch softer
B_PILL = hexc("#06593F")
B_DOT = hexc("#7CFFC0")
B_BAR = hexc("#8FE6BD")
B_STRIP = hexc("#F2EEE4")
ORANGE = hexc("#EC6A34")                 # Claude's orange: only for the one flickering bar (CD 13.2)
FPS = 24
TEMP_KEYS = [(366, 19), (417.5, 24), (469, 31), (520.5, 38), (572, 46)]   # 19 -> 46 °C, f366 -> f572 (CD 13.2)
FLICKER_F = 434                          # CD 13.7 4c (look worker, 12:10): the glass breaks f452 (shards appear), outside both board holds (9:16 f366-450, 16:9 f388-436); nearest frame of his action inside both, with the 3 orange frames + 2 repaint frames ending f438 (orange f434-436 inside both holds)


def _beats():
    try:
        m = json.load(open(os.path.join(SONG, "audio", "audio_map.json")))
        return [b["t"] for b in m["beats"]]
    except Exception:
        return [i * 60 / 117 for i in range(600)]


BEATS = _beats()


def temp_at(f):
    if f <= TEMP_KEYS[0][0]:
        return TEMP_KEYS[0][1]
    for (f0, t0), (f1, t1) in zip(TEMP_KEYS, TEMP_KEYS[1:]):
        if f <= f1:
            return int(round(t0 + (t1 - t0) * (f - f0) / (f1 - f0)))
    return TEMP_KEYS[-1][1]


def pulse_at(f):
    """0..1, a fast attack and ~0.15 s decay on each beat of the hold music."""
    t = f / FPS
    past = [b for b in BEATS if b <= t]
    if not past:
        return 0.0
    return math.exp(-(t - past[-1]) / 0.15)


def board(f=390, temp=None):
    im = Image.new("RGB", (BW, BH), B_GREEN)
    d = ImageDraw.Draw(im)
    # a screen, not a slab: the faintest top-lit falloff
    for y in range(0, 1550):
        k = 1.0 + 0.05 * (1 - y / 1550)
        d.line([(0, y), (BW, y)], fill=tuple(min(255, int(c * k)) for c in B_GREEN))
    M = 90
    # headline: two lines, Anton
    s = 447
    fh = F(ANTON, s)
    cap = CAP[ANTON] * s
    y1 = M + cap
    y2 = y1 + 85 + cap
    px0, px1 = 2380, BW - M
    with box((0, 0, px0, 1000), "headline"):
        d.text((M - 8, y1), "ALL SYSTEMS", font=fh, fill=B_INK, anchor="ls")
        d.text((M - 8, y2), "OPERATIONAL", font=fh, fill=B_INK, anchor="ls")
    # status pills, a column at the right
    ph = (y2 - M - 3 * 34) / 4
    fp = F(ANTON, 150)
    p = pulse_at(f)
    for i, name in enumerate(["BILLING", "AUTH", "DEPLOY", "ROOF"]):
        top = M + i * (ph + 34)
        d.rounded_rectangle([px0, top, px1, top + ph], radius=ph / 2, fill=B_PILL)
        cx, cy = px0 + ph / 2 + 10, top + ph / 2
        r = 40 * (1 + 0.22 * p)
        halo = Image.new("RGB", im.size, (0, 0, 0))
        ImageDraw.Draw(halo).ellipse([cx - r * 1.9, cy - r * 1.9, cx + r * 1.9, cy + r * 1.9], fill=tuple(int(c * (0.25 + 0.35 * p)) for c in B_DOT))
        im = ImageChops.add(im, halo.filter(ImageFilter.GaussianBlur(22)))
        d = ImageDraw.Draw(im)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=B_DOT)
        with box((px0, top, px1, top + ph), "pill " + name):
            d.text((cx + 80, cy + CAP[ANTON] * 150 / 2), name, font=fp, fill=B_INK, anchor="ls")
    # uptime row: 90 thin bars (one per second, scrolling 1 bar/s) + the label
    fi = F(INTER_SB, 140)
    ry0, ry1 = 1060, 1200
    lab = "uptime 100.00%"
    with box((0, ry0 - 40, BW, 1260), "uptime row"):
        d.text((BW - M, ry1), lab, font=fi, fill=B_SOFT, anchor="rs")
    bx1 = BW - M - d.textlength(lab, font=fi) - 70
    pitch = (bx1 - M) / 90
    sec = int(f // FPS)
    for k in range(90):
        idx = sec + k                                         # absolute bar index: the strip scrolls one bar a second
        shade = 0.86 + 0.14 * ((idx * 2654435761) % 97) / 96  # faint per-bar variation so the scroll is visible
        col = tuple(int(c * shade) for c in B_BAR)
        if k == 89 and FLICKER_F <= f < FLICKER_F + 3:
            col = ORANGE
        elif k == 89 and FLICKER_F + 3 <= f < FLICKER_F + 5:
            col = tuple((a + b) // 2 for a, b in zip(ORANGE, B_BAR))
        x = M + k * pitch
        d.rounded_rectangle([x, ry0, x + pitch * 0.62, ry1], radius=4, fill=col)
    # info row
    iy = 1405
    with box((0, iy - 160, BW, 1550), "info row"):
        d.text((M, iy), "last incident: never", font=fi, fill=B_SOFT, anchor="ls")
    tval = temp_at(f) if temp is None else temp
    tl = f"lobby temp {tval}°C"
    tx = BW - M - d.textlength(tl, font=fi)
    with box((0, iy - 160, BW, 1550), "info row"):
        d.text((BW - M, iy), tl, font=fi, fill=B_SOFT, anchor="rs")
    # a small thermometer before it (geometry, not text)
    th_x = tx - 70
    d.rounded_rectangle([th_x - 14, iy - 112, th_x + 14, iy - 10], radius=14, outline=B_SOFT, width=7)
    d.ellipse([th_x - 26, iy - 34, th_x + 26, iy + 18], fill=B_SOFT)
    lvl = (tval - 19) / (46 - 19)
    d.rectangle([th_x - 6, iy - 22 - 80 * max(0.15, lvl), th_x + 6, iy - 12], fill=B_SOFT)
    # the subscribe strip (CD 13.11): a status-page button, no keycap, no icon. Board green on the off-white strip.
    sy0 = 1550
    d.rectangle([0, sy0, BW, BH], fill=B_STRIP)
    with box((0, sy0, BW, BH), "subscribe strip"):
        d.text((M, sy0 + 125 + CAP[INTER_SB] * 150 / 2), "SUBSCRIBE TO UPDATES", font=F(INTER_SB, 150),
               fill=B_GREEN, anchor="ls")
    return im


# ====================================================================== 2. the 7-segment clock (front panel)
CPX = 10                                  # px per mm
CW, CH = 180 * CPX, 140 * CPX
SEG_ON, SEG_GHOST = hexc("#FF3D17"), hexc("#2C0B07")
SEG_HALF = hexc("#170605")                 # the half digit's ghost: barely visible
SEGS = {"0": "abcdef", "1": "bc", "2": "abged", "3": "abgcd", "4": "fgbc", "5": "afgcd", "6": "afgedc", "7": "abc",
        "8": "abcdefg", "9": "abcdfg", " ": ""}


def _steel(w, h, seed=3):
    import random
    rnd = random.Random(seed)
    im = Image.new("RGB", (w, h), hexc("#6E7176"))
    d = ImageDraw.Draw(im)
    for y in range(h):                    # brushed
        v = 100 + rnd.randint(-10, 10)
        d.line([(0, y), (w, y)], fill=(v + 4, v + 6, v + 10))
    for _ in range(90):                   # scuffs
        x, y = rnd.randint(0, w), rnd.randint(0, h)
        L = rnd.randint(30, 260); a = rnd.uniform(-0.5, 0.5)
        d.line([(x, y), (x + L * math.cos(a), y + L * math.sin(a))], fill=(150, 152, 156), width=rnd.choice([1, 2, 2, 3]))
    im = im.filter(ImageFilter.GaussianBlur(0.8))
    # darker worn edges
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], radius=60, outline=255, width=40)
    m = m.filter(ImageFilter.GaussianBlur(30))
    return Image.composite(Image.new("RGB", (w, h), (40, 42, 46)), im, m)


def _digit(d, x, y, w, h, t, ch, slant=0.08, ghost=None, only=None):
    on = set(SEGS[ch])
    ghost = ghost or SEG_GHOST
    g = t * 0.18
    def P(px, py):                        # slant: shift x with height
        return (x + px + (h - py) * slant, y + py)
    hs = (h - t) / 2
    segs = {
        "a": [(g + t / 2, t / 2), (w - g - t / 2, t / 2)],
        "g": [(g + t / 2, hs + t / 2), (w - g - t / 2, hs + t / 2)],
        "d": [(g + t / 2, h - t / 2), (w - g - t / 2, h - t / 2)],
        "f": [(t / 2, g + t / 2), (t / 2, hs + t / 2 - g)],
        "b": [(w - t / 2, g + t / 2), (w - t / 2, hs + t / 2 - g)],
        "e": [(t / 2, hs + t / 2 + g), (t / 2, h - t / 2 - g)],
        "c": [(w - t / 2, hs + t / 2 + g), (w - t / 2, h - t / 2 - g)],
    }
    for k, ((x0, y0), (x1, y1)) in segs.items():
        if only is not None and k not in only:
            continue
        col = SEG_ON if k in on else ghost
        # a hexagonal segment
        if y0 == y1:
            pts = [(x0 - t / 2, y0), (x0, y0 - t / 2), (x1, y0 - t / 2), (x1 + t / 2, y0), (x1, y0 + t / 2), (x0, y0 + t / 2)]
        else:
            pts = [(x0, y0 - t / 2), (x0 + t / 2, y0), (x0 + t / 2, y1), (x0, y1 + t / 2), (x0 - t / 2, y1), (x0 - t / 2, y0)]
        d.polygon([P(*p) for p in pts], fill=col)


def _rot_rect(rect, cx, cy, deg):
    """Bounding box of `rect` turned `deg` (PIL rotate, counter-clockwise) about (cx, cy)."""
    a = math.radians(deg); x0, y0, x1, y1 = rect
    pts = [(cx + (x - cx) * math.cos(a) + (y - cy) * math.sin(a), cy - (x - cx) * math.sin(a) + (y - cy) * math.cos(a)) for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]
    return (min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts))


def _tape(text, type_mm, rot, seed, at=None):
    f = F(JB, type_mm * CPX)
    tw = f.getlength(text)
    w, h = int(tw + 2 * 5 * CPX), int(type_mm * CPX * 1.45)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, h], fill=hexc("#E9DDB0", 255))                  # yellowed tape
    d.line([(0, 6), (w, 6)], fill=hexc("#F6EDC6", 255), width=6)
    pos = (w / 2, h / 2 + CAP[JB] * type_mm * CPX / 2)
    with skip():
        d.text(pos, text, font=f, fill=hexc("#1C1A16", 255), anchor="ms")
    out = im.rotate(rot, resample=Image.BICUBIC, expand=True)
    if REC is not None and at is not None:      # record the text and the tape as PLACED on the panel (turned, pasted at `at`)
        tb = d.textbbox(pos, text, font=f, anchor="ms")
        tr = _rot_rect(tb, w / 2, h / 2, rot)
        ox, oy = at(out.width)
        off = (out.width - w) / 2, (out.height - h) / 2
        REC.add(text, [tr[0] + off[0] + ox, tr[1] + off[1] + oy, tr[2] + off[0] + ox, tr[3] + off[1] + oy],
                [ox, oy, ox + out.width, oy + out.height], "tape " + text)
    return out


def clock(hhmm="3:07", colon=True):
    im = _steel(CW, CH)
    d = ImageDraw.Draw(im)
    # the digit window: smoked acrylic
    wx0, wy0, wx1, wy1 = 10 * CPX, 8 * CPX, 170 * CPX, 70 * CPX
    d.rounded_rectangle([wx0 - 14, wy0 - 14, wx1 + 14, wy1 + 14], radius=40, fill=(30, 30, 33))
    d.rounded_rectangle([wx0, wy0, wx1, wy1], radius=30, fill=hexc("#120605"))
    lay = Image.new("RGB", im.size, (0, 0, 0))
    ld = ImageDraw.Draw(lay)
    dh, dw, t = 50 * CPX, 27 * CPX, 6.2 * CPX
    xs = [wx0 + 8 * CPX, wx0 + 40 * CPX, wx0 + 84 * CPX, wx0 + 117 * CPX]
    hh, mm = hhmm.split(":")
    chars = [" ", hh] if len(hh) == 1 else list(hh)
    chars += list(mm)
    y = wy0 + 6 * CPX
    for i, (x, ch) in enumerate(zip(xs, chars)):
        if i == 0 and ch == " ":      # a 12-hour clock's half digit: only the two segments of a "1", barely there (CD 13.6 b)
            _digit(ld, x, y, dw, dh, t, " ", ghost=SEG_HALF, only="bc")
            continue
        _digit(ld, x, y, dw, dh, t, ch)
    # the AM dot: small, lit, top-left of the window, with "AM" printed faintly beside it on the acrylic
    ax, ay, ar = wx0 + 7 * CPX, wy0 + 9 * CPX, 2.6 * CPX
    ld.ellipse([ax - ar, ay - ar, ax + ar, ay + ar], fill=SEG_ON)
    cx = wx0 + 74 * CPX
    for cy in (y + dh * 0.3, y + dh * 0.7):
        ld.ellipse([cx - t * 0.6, cy - t * 0.6, cx + t * 0.6, cy + t * 0.6], fill=SEG_ON if colon else SEG_GHOST)
    lay = glow_layer(lay, 18, 0.55)
    win = Image.new("L", im.size, 0)
    ImageDraw.Draw(win).rounded_rectangle([wx0, wy0, wx1, wy1], radius=30, fill=255)
    im = Image.composite(ImageChops.add(im, lay), im, win)
    d = ImageDraw.Draw(im)
    with box((wx0, wy0, wx1, wy1), "digit window"):
      d.text((wx0 + 11 * CPX, wy0 + 9 * CPX + CAP[INTER_SB] * 4 * CPX / 2), "AM", font=F(INTER_SB, 4 * CPX), fill=(110, 60, 50), anchor="ls")
    # two label-maker strips: "CRON" and "DO NOT ADJUST" (type 21 mm: cap 45 px in the 16:9 ECU at >= 3076 px/m)
    t1 = _tape("CRON", 21, 2.0, 1, at=lambda w: (12 * CPX, 75 * CPX))
    t2 = _tape("DO NOT ADJUST", 21, -1.0, 2, at=lambda w: (max(0, CW - w - 2 * CPX), 104 * CPX))
    im.paste(t1, (12 * CPX, 75 * CPX), t1)
    im.paste(t2, (max(0, CW - t2.width - 2 * CPX), 104 * CPX), t2)
    return im


# ====================================================================== 3. SCHEDULED JOBS (amber terminal)
SPX = 2                                    # px per mm
SW, SH = 700 * SPX, 500 * SPX
AMBER, AMBER_DIM, CRT = hexc("#FFB238"), hexc("#5A3A0C"), hexc("#0C0803")


def _crt_base(dark=False):
    im = Image.new("RGB", (SW, SH), (7, 6, 5) if dark else CRT)
    vign = Image.new("L", (SW, SH), 0)
    ImageDraw.Draw(vign).rounded_rectangle([0, 0, SW - 1, SH - 1], radius=90, outline=255, width=60)
    vign = vign.filter(ImageFilter.GaussianBlur(50))
    im = Image.composite(Image.new("RGB", (SW, SH), (0, 0, 0)), im, vign)
    if dark:   # glass: a faint diagonal reflection, nothing readable
        refl = Image.new("L", (SW, SH), 0)
        ImageDraw.Draw(refl).polygon([(0, 0), (SW * 0.45, 0), (SW * 0.15, SH), (0, SH)], fill=18)
        im = Image.composite(Image.new("RGB", (SW, SH), (60, 64, 70)), im, refl.filter(ImageFilter.GaussianBlur(60)))
    return im


def scheduler(state="on", cursor=True, warm=1.0):
    """state: dark (before f728) | on | refresh (the tick on 'alarm' f740)."""
    if state == "dark":
        return _crt_base(dark=True)
    im = _crt_base()
    txt = Image.new("RGB", (SW, SH), (0, 0, 0))
    d = ImageDraw.Draw(txt)
    m = 40 * SPX
    fj = F(JB, 47 * SPX)
    hb = 92 * SPX                          # header baseline
    if state == "refresh":
        d.rectangle([m - 10 * SPX, hb - 52 * SPX, SW - m + 10 * SPX, hb + 14 * SPX], fill=AMBER)
        hc = CRT
    else:
        hc = AMBER
    for x_mm, word in ((40, "JOB"), (210, "NEXT RUN"), (500, "OWNER")):
        with box((0, 0, SW, SH), "screen"):
            d.text((x_mm * SPX, hb), word, font=fj, fill=hc, anchor="ls")
    d.line([(m, hb + 24 * SPX), (SW - m, hb + 24 * SPX)], fill=AMBER, width=3 * SPX)
    for yy in (172, 222):                  # the empty table
        for x in range(m, SW - m, 18 * SPX):
            d.line([(x, yy * SPX), (x + 8 * SPX, yy * SPX)], fill=AMBER_DIM, width=2 * SPX)
    d.text((m - 4 * SPX, 336 * SPX), "0 jobs scheduled", font=F(VT, 95 * SPX), fill=AMBER, anchor="ls")
    d.text((m, 404 * SPX), "last ran: 03:07 today", font=fj, fill=AMBER, anchor="ls")
    d.text((m, 462 * SPX), "owner: nobody", font=fj, fill=AMBER, anchor="ls")
    if cursor:
        cx = m + fj.getlength("owner: nobody") + 14 * SPX
        d.rectangle([cx, 462 * SPX - 36 * SPX, cx + 26 * SPX, 462 * SPX + 6 * SPX], fill=AMBER)
    txt = glow_layer(txt, 9, 0.45)
    if warm < 1.0:
        txt = txt.point(lambda v: int(v * warm))
    return ImageChops.add(im, txt)


def scheduler_at(f):
    if f < 728:
        return scheduler("dark")
    warm = min(1.0, (f - 728 + 1) / 3)     # 3-frame phosphor warm-up on the ping
    if 740 <= f < 742:
        return scheduler("refresh", cursor=False, warm=warm)
    return scheduler("on", cursor=((f - 728) % 24) < 12, warm=warm)


# ====================================================================== 4. the DO NOT DELETE tag (+ the column stencil)
TPX = 5
TW, TH = 340 * TPX, 240 * TPX


def tag():
    import random
    rnd = random.Random(7)
    im = Image.new("RGBA", (TW, TH), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = 34 * TPX
    shape = [(c, 0), (TW, 0), (TW, TH), (c, TH), (0, TH - c), (0, c)]      # a shipping tag, the clipped end left
    d.polygon(shape, fill=hexc("#E2AE17", 255))
    # paper: a little mottling and an edge darkening
    tex = Image.new("L", (TW, TH), 0)
    td = ImageDraw.Draw(tex)
    for _ in range(1400):
        x, y = rnd.randint(0, TW), rnd.randint(0, TH)
        r = rnd.randint(4, 30)
        td.ellipse([x - r, y - r, x + r, y + r], fill=rnd.randint(8, 26))
    tex = tex.filter(ImageFilter.GaussianBlur(6))
    shade = Image.new("RGBA", (TW, TH), (120, 80, 0, 0))
    shade.putalpha(tex)
    mask = im.getchannel("A")
    im = Image.alpha_composite(im, Image.composite(shade, Image.new("RGBA", (TW, TH), (0, 0, 0, 0)), mask))
    d = ImageDraw.Draw(im)
    # punched hole with a reinforcing ring, and the string
    hx, hy = 30 * TPX, TH / 2
    d.ellipse([hx - 17 * TPX, hy - 17 * TPX, hx + 17 * TPX, hy + 17 * TPX], fill=hexc("#C99A12", 255))
    d.ellipse([hx - 8 * TPX, hy - 8 * TPX, hx + 8 * TPX, hy + 8 * TPX], fill=(0, 0, 0, 0))
    # DO NOT / DELETE, Saira stencil, black
    s = 70 * TPX
    fs = F(SAIRA, s)
    cap = CAP[SAIRA] * s
    x0 = 58 * TPX
    y1 = 26 * TPX + cap
    y2 = y1 + 16 * TPX + cap
    ink = hexc("#17140F", 255)
    with box((c, 0, TW, TH), "tag body"):
        d.text((x0, y1), "DO NOT", font=fs, fill=ink, anchor="ls")
        d.text((x0, y2), "DELETE", font=fs, fill=ink, anchor="ls")
    # "seriously." in marker, crooked, underneath
    mk = Image.new("RGBA", (TW, 90 * TPX), (0, 0, 0, 0))
    mfont = F(MARKER, 46 * TPX)
    mkd = ImageDraw.Draw(mk)
    with skip():
        mkd.text((10, 70 * TPX), "seriously.", font=mfont, fill=hexc("#1E2A6E", 255), anchor="ls")
    mk = mk.rotate(4, resample=Image.BICUBIC, expand=False)
    mpos = (int(x0 + 40 * TPX), int(y2 + 6 * TPX))
    im.alpha_composite(mk, mpos)
    if REC is not None:                         # the marker line as placed (turned 4 deg about the strip's centre, pasted at mpos)
        tb = _rot_rect(mkd.textbbox((10, 70 * TPX), "seriously.", font=mfont, anchor="ls"), TW / 2, mk.height / 2, 4)
        REC.add("seriously.", [tb[0] + mpos[0], tb[1] + mpos[1], tb[2] + mpos[0], tb[3] + mpos[1]], [c, 0, TW, TH], "tag body")
    # brown tape repair across the top-right corner
    tp = Image.new("RGBA", (110 * TPX, 34 * TPX), hexc("#8A5A22", 190))
    tpd = ImageDraw.Draw(tp)
    for k in range(0, tp.width, 9 * TPX):
        tpd.line([(k, 0), (k + 4 * TPX, tp.height)], fill=hexc("#A06C2E", 120), width=TPX)
    tp = tp.rotate(38, resample=Image.BICUBIC, expand=True)
    im.alpha_composite(tp, (-34 * TPX, TH - tp.height + 30 * TPX))      # the torn bottom-left corner, taped
    # clip anything outside the tag shape
    out = Image.new("RGBA", (TW, TH), (0, 0, 0, 0))
    out.paste(im, (0, 0), mask)
    return out


def column_stencil():
    """84 mm wide face x 620 mm, decal with alpha: 'var: DO_NOT_DELETE' / 'since v0.1', stencilled vertically."""
    p = 5
    w, h = 84 * p, 620 * p
    lay = Image.new("RGBA", (h, w), (0, 0, 0, 0))            # drawn horizontally, then turned
    d = ImageDraw.Draw(lay)
    s = 30 * p
    paint = hexc("#E9E2CC", 235)
    d.text((40 * p, 36 * p), "var: DO_NOT_DELETE", font=F(SAIRA, s), fill=paint, anchor="ls")
    d.text((40 * p, 74 * p), "since v0.1", font=F(SAIRA, s), fill=paint, anchor="ls")
    over = lay.filter(ImageFilter.GaussianBlur(10))
    over.putalpha(over.getchannel("A").point(lambda v: v // 4))
    lay = Image.alpha_composite(over, lay)
    return lay.rotate(90, expand=True)


# ====================================================================== 5. IN CASE OF EMERGENCY
EPX = 3
EW, EH = 620 * EPX, 520 * EPX


def emergency():
    """IN CASE OF / EMERGENCY / CALL 911 (her note "Call 911"; CD 13.8): white Anton on lit red acrylic with the white
    keyline; CALL 911 reversed out, red on a white bar across the full inner width. It plants the outro's 911 joke."""
    red = hexc("#C8141E")
    im = Image.new("RGB", (EW, EH), red)
    d = ImageDraw.Draw(im)
    for y in range(EH):                         # lit red acrylic: brighter in the middle
        k = 1.0 + 0.10 * math.sin(math.pi * y / EH)
        d.line([(0, y), (EW, y)], fill=tuple(min(255, int(c * k)) for c in red))
    s12 = 125 * EPX                             # cap 107 mm: 45 px at 423 px/m (16:9 f390); 53 px type at 423 (9:16 f461)
    s3 = 140 * EPX                              # cap 120 mm: 51 px cap in 16:9 at f390
    c12, c3 = CAP[ANTON] * s12, CAP[ANTON] * s3
    y1 = 40 * EPX + c12
    y2 = y1 + 28 * EPX + c12
    d.text((EW / 2, y1), "IN CASE OF", font=F(ANTON, s12), fill=hexc("#FFFFFF"), anchor="ms")
    d.text((EW / 2, y2), "EMERGENCY", font=F(ANTON, s12), fill=hexc("#FFFFFF"), anchor="ms")
    by0, by1 = y2 + 30 * EPX, EH - 12 * EPX
    d.rectangle([12 * EPX, by0, EW - 12 * EPX, by1], fill=hexc("#F6F2EC"))
    d.text((EW / 2, (by0 + by1) / 2 + c3 / 2), "CALL 911", font=F(ANTON, s3), fill=red, anchor="ms")
    d.rounded_rectangle([6 * EPX, 6 * EPX, EW - 6 * EPX, EH - 6 * EPX], radius=8 * EPX, outline=hexc("#F7F2EC"), width=3 * EPX)
    return im


# ====================================================================== textures
def save(im, rel):
    p = os.path.join(HERE, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    im.save(p)
    return p


def textures():
    for t in (19, 24, 31, 38, 46):
        save(board(390, temp=t), f"board/board_T{t}.png")
    for hm in ("3:06", "3:07"):
        for on in (True, False):
            save(clock(hm, on), f"clock/clock_{hm.replace(':', '')}_{'on' if on else 'off'}.png")
    save(scheduler("dark"), "scheduler/sched_dark.png")
    save(scheduler("on", True), "scheduler/sched_on_cursor.png")
    save(scheduler("on", False), "scheduler/sched_on_nocursor.png")
    save(scheduler("refresh", False), "scheduler/sched_refresh.png")
    save(tag(), "tag/tag.png")
    save(column_stencil(), "tag/column_stencil.png")
    save(emergency(), "emergency/sign.png")


# ====================================================================== text-fit check (studio rule, Nov 6 2026)
def fitcheck(save_to=None):
    """Build every texture under a textfit.Recorder; write textfit_<name>.json to build/textfit/ for tools/text_fit_check.py."""
    global REC
    jobs = {
        "board_T19": ((BW, BH), lambda: board(366, temp=19)), "board_T46": ((BW, BH), lambda: board(572, temp=46)),
        "clock_307": ((CW, CH), lambda: clock("3:07", True)), "clock_306": ((CW, CH), lambda: clock("3:06", False)),
        "sched_on": ((SW, SH), lambda: scheduler("on", True)), "sched_refresh": ((SW, SH), lambda: scheduler("refresh", False)),
        "tag": ((TW, TH), tag), "stencil": ((620 * 5, 84 * 5), column_stencil), "emergency": ((EW, EH), emergency),
    }
    out = save_to or os.path.join(SONG, "build", "textfit")
    bad = 0
    for name, (size, fn) in jobs.items():
        with textfit.Recorder(size, name) as rec:
            REC = rec
            try:
                fn()
            finally:
                REC = None
        rec.save(out)
        pr = rec.problems()
        bad += len(pr)
        print(name, len(rec.records), "blocks,", len(pr), "problems")
        for p in pr:
            print("   ", p["kind"], repr(p["text"]), p["bbox"], p.get("container"))
    return bad


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "textures"
    if cmd == "textures":
        textures()
    elif cmd == "board":
        a = int(sys.argv[2]); b = int(sys.argv[3]) if len(sys.argv) > 3 else a
        for f in range(a, b + 1):
            print(save(board(f), f"board/board_f{f:04d}.png"))
    elif cmd == "fitcheck":
        sys.exit(1 if fitcheck() else 0)
    elif cmd == "cards":
        import cards
        cards.main()
