"""The room where somebody did the math. After the Turn the camera only looks down, so the desk is a still life seen
from straight above (papers of numbers, a plotted trajectory, a pencil, a calculator, a cold coffee), lit by a desk lamp
at night and by the window at dawn; and the whiteboard where the flight is drawn in marker, word by word, as she sings it.
Both are flat 'sets' drawn at high resolution with PIL, then lit and photographed (crop, rotation, lens falloff, grain)."""
import math, os
from functools import lru_cache
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
import ekg as K
from ekg import F32, sstep, clamp, lerp, ease_io, ease_out

F_MARK = os.path.join(K.FONTS, "PermanentMarker-Regular.ttf")
F_HAND = os.path.join(K.FONTS, "Caveat-Medium.ttf")
F_MONO = os.path.join(K.FONTS, "JBMono-400.ttf")

def lin(img_u8): return np.power(np.asarray(img_u8, F32) / 255.0, 2.2)

# ---------------------------------------------------------------- the desk, from above (1 px = 0.4 mm)
DW, DH = 4000, 2600
NOTES_A = ["t_MECO = 143 s", "MECO @ ~75 km", "boostback: 3 eng", "entry: 3 eng", "landing: 1 eng", "g0 = 9.81 m/s²",
           "Isp_sl = 282 s", "Δv = Isp·g0·ln(m0/mf)", "T/W (1 eng) > 1 ?"]
NOTES_B = ["dist ≈ 9 km S", "→ LZ-1", "v_touch < 2 m/s", "throttle min ?", "→ hoverslam", "legs @ T-10 s ?", "margin ?",
           "re-check fins", "it will turn here"]
MUG = (2860.0, 760.0)          # mug centre on the desk (px)
MUG_R = 205.0

def _sheet(w, h, lines, graph, seed, ink=(38, 44, 66, 255), size=58):
    sh = Image.new("RGBA", (w, h), (238, 234, 224, 255)); sd = ImageDraw.Draw(sh)
    if graph:
        for x in range(0, w, 34): sd.line([(x, 0), (x, h)], fill=(192, 208, 214, 255), width=1)
        for y in range(0, h, 34): sd.line([(0, y), (w, y)], fill=(192, 208, 214, 255), width=1)
    f = ImageFont.truetype(F_HAND, size); rr = np.random.default_rng(seed)
    y = 60
    for ln in lines:
        sd.text((54 + int(rr.integers(-8, 8)), y), ln, font=f, fill=ink); y += int(size * 1.25) + int(rr.integers(-4, 8))
        if y > h - 90: break
    return sh

@lru_cache(1)
def desk_set():
    """albedo (linear, H x W x 3) of the desk with everything on it, and a height map (for soft contact shadows)."""
    r = np.random.default_rng(5)
    g = cv2.resize(K.noise_tex(512, 70, 6, 0.6), (DW, DH), interpolation=cv2.INTER_CUBIC)
    yy = np.arange(DH, dtype=F32)[:, None]
    grain = (0.5 + 0.5 * np.sin(yy * 0.03 + g * 10)) * 0.22 + 0.78
    base = np.stack([60 * grain, 44 * grain, 32 * grain], 2)
    im = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)).convert("RGBA")
    hmap = Image.new("L", (DW, DH), 0)
    def place(sh, cx, cy, ang, height):
        s2 = sh.rotate(ang, expand=True, resample=Image.BICUBIC)
        x, y = int(cx - s2.width / 2), int(cy - s2.height / 2)
        im.alpha_composite(s2, (x, y))
        hmap.paste(Image.new("L", s2.size, height), (x, y), s2.split()[3])
    # notebook underneath, then the two sheets of numbers
    nb = Image.new("RGBA", (1100, 1400), (24, 30, 42, 255)); nd = ImageDraw.Draw(nb)
    nd.rectangle((40, 40, 1060, 1360), outline=(60, 70, 90, 255), width=6)
    place(nb, 980, 1500, -14, 18)
    a = _sheet(1150, 1500, NOTES_A, True, 1)
    ad = ImageDraw.Draw(a)
    # the plot: up and over, flip, back, down to an X (in red pencil)
    pts = []
    for k in range(80):
        u = k / 79
        if u < 0.5:
            v = u / 0.5; pts.append((120 + 700 * v ** 1.5, 1330 - 620 * math.sin(v * math.pi / 2)))
        else:
            v = (u - 0.5) / 0.5; pts.append((820 - 560 * v ** 0.9 + 120 * math.sin(v * math.pi), 710 + 620 * v ** 1.8))
    ad.line(pts, fill=(176, 52, 36, 255), width=5)
    ad.line([(80, 1340), (1080, 1340)], fill=(60, 60, 70, 255), width=3)
    ad.line([(236, 1310), (284, 1370)], fill=(176, 52, 36, 255), width=5); ad.line([(284, 1310), (236, 1370)], fill=(176, 52, 36, 255), width=5)
    place(a, 1550, 1180, 7, 30)
    b = _sheet(1080, 1420, NOTES_B, False, 2)
    place(b, 2420, 1500, -10, 36)
    # a coffee ring on the sheet (an earlier cup)
    ring = Image.new("RGBA", (420, 420), (0, 0, 0, 0)); rd = ImageDraw.Draw(ring)
    rd.ellipse((20, 20, 400, 400), outline=(120, 82, 46, 90), width=14)
    place(ring, 2240, 1980, 0, 36)
    # calculator
    calc = Image.new("RGBA", (420, 680), (0, 0, 0, 0)); cd = ImageDraw.Draw(calc)
    cd.rounded_rectangle((0, 0, 419, 679), 34, fill=(26, 26, 28, 255)); cd.rounded_rectangle((40, 40, 380, 170), 12, fill=(70, 86, 74, 255))
    cd.text((70, 70), "9.81", font=ImageFont.truetype(F_MONO, 64), fill=(18, 26, 20, 255))
    for i in range(4):
        for j in range(5):
            cd.rounded_rectangle((44 + i * 86, 220 + j * 88, 108 + i * 86, 284 + j * 88), 10, fill=(60, 60, 64, 255))
    place(calc, 3330, 1900, 18, 60)
    # pencil
    pen = Image.new("RGBA", (1000, 44), (0, 0, 0, 0)); pd = ImageDraw.Draw(pen)
    pd.rectangle((70, 4, 940, 40), fill=(212, 164, 40, 255)); pd.rectangle((940, 4, 1000, 40), fill=(230, 120, 140, 255))
    pd.rectangle((920, 4, 944, 40), fill=(170, 170, 160, 255)); pd.polygon([(70, 4), (70, 40), (0, 22)], fill=(232, 204, 160, 255))
    pd.polygon([(22, 15), (22, 29), (0, 22)], fill=(36, 36, 36, 255))
    place(pen, 2020, 640, 23, 40)
    alb = lin(im.convert("RGB"))
    h = cv2.GaussianBlur(np.asarray(hmap, F32), (0, 0), 3)
    return alb, h

def mug_layer(alb, h, light_dir):
    """the mug from above: a white rim, cold black coffee with a faint ring line, the handle; plus its soft shadow."""
    out = alb.copy(); H_, W_ = alb.shape[:2]
    cx, cy = MUG; R = MUG_R
    yy, xx = np.ogrid[0:H_, 0:W_]
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    # shadow (cast away from the light), soft
    sx, sy = -light_dir[0] * 120, -light_dir[1] * 120
    ds = np.sqrt((xx - cx - sx) ** 2 + (yy - cy - sy) ** 2)
    sh = np.clip((R * 1.05 - ds) / 60, 0, 1) * 0.65
    sh = cv2.GaussianBlur(sh.astype(F32), (0, 0), 30)
    out *= (1 - sh)[..., None]
    rim = (d < R) & (d > R - 26)
    inner = d <= R - 26
    out[rim] = np.array([0.80, 0.80, 0.78], F32)
    coffee = np.array([0.020, 0.010, 0.005], F32)
    out[inner] = coffee
    stain = inner & (np.abs(d - (R - 44)) < 3)                    # the dried line where the level was
    out[stain] = np.array([0.07, 0.04, 0.02], F32)
    # handle (an arc on the right side)
    hd = np.sqrt((xx - (cx + R + 40)) ** 2 + (yy - cy) ** 2)
    handle = (np.abs(hd - 70) < 18) & (xx > cx + R - 5)
    out[handle] = np.array([0.74, 0.74, 0.72], F32)
    return out, (d < R + 2) | handle

def desk_render(t, W, H, u, st):
    """st: cx, cy (desk px at the frame centre), zoom (1 = 2200 px of desk across the frame), ang (deg),
    lamp (0..1), dawn (0..1)."""
    alb, hgt = desk_set()
    lamp = st.get("lamp", 1.0); dawn = st.get("dawn", 0.0)
    # light: the lamp (top-left, warm, a pool) and the window at dawn (from the right, cool-pink, broad)
    sc = 0.25
    w, h = int(DW * sc), int(DH * sc)
    yy, xx = np.mgrid[0:h, 0:w].astype(F32) / sc
    pool = np.exp(-(((xx - 1700) / 1500) ** 2 + ((yy - 1000) / 1100) ** 2)) * 0.62 + 0.012
    E = pool[..., None] * np.array([1.0, 0.78, 0.52], F32) * lamp
    win = (0.18 + 0.30 * np.clip(xx / DW, 0, 1) ** 1.5)[..., None] * lerp(np.array([0.55, 0.6, 0.85], F32), np.array([1.0, 0.72, 0.62], F32), 0.5)
    E = E + win * dawn
    E = cv2.resize(E, (DW, DH), interpolation=cv2.INTER_LINEAR)
    ldir = np.array([-0.6, -0.5], F32) if dawn < 0.5 else np.array([0.9, -0.2], F32)
    ldir = ldir / np.linalg.norm(ldir)
    a2, mask = mug_layer(alb, hgt, ldir)
    # soft drop shadows of the raised things (sheets, calculator, pencil) from the height map
    shift = (int(-ldir[0] * 14), int(-ldir[1] * 14))
    hs = np.roll(np.roll(hgt, shift[1], 0), shift[0], 1)
    shade = np.clip((hs - hgt) / 40.0, 0, 1) * 0.55
    shade = cv2.GaussianBlur(shade, (0, 0), 10)
    lit = a2 * E * (1 - shade)[..., None]
    # rim highlight on the coffee surface (a sliver of the lamp/window reflected)
    cx, cy = MUG
    hx, hy = cx + ldir[0] * 90, cy + ldir[1] * 90
    lit += K.glow_layer(DW, DH, [(hx, hy, 46, np.array([1.0, 0.85, 0.65], F32) if dawn < 0.5 else np.array([1.0, 0.9, 0.9], F32), 0.35 * max(lamp, dawn))], 0.25) * mask[..., None]
    # camera: top-down crop with rotation
    cxv, cyv = st.get("cx", 2000.0), st.get("cy", 1300.0)
    zoom = st.get("zoom", 1.0); ang = st.get("ang", 0.0)
    span = 2200.0 / zoom * (0.6 if H > W else 1.0)             # vertical frames: a narrower strip of desk, same detail
    s = W / span
    M = cv2.getRotationMatrix2D((cxv, cyv), ang, s)
    M[0, 2] += W / 2 - cxv; M[1, 2] += H / 2 - cyv
    img = cv2.warpAffine(lit, M, (W, H), flags=cv2.INTER_AREA if s < 0.9 else cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    # lens: a gentle falloff and a little blur toward the frame edges (a long lens, close)
    return dof_radial(img, st.get("dof", 1.0))

def dof_radial(img, amount=1.0):
    H, W = img.shape[:2]
    if amount <= 0: return img
    b = cv2.GaussianBlur(img, (0, 0), 4.0 * amount * min(W, H) / 1080)
    y, x = np.ogrid[0:H, 0:W]
    r = np.sqrt(((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2) / 1.414
    k = np.clip((r - 0.35) / 0.5, 0, 1).astype(F32)[..., None]
    return img * (1 - k) + b * k

# ---------------------------------------------------------------- the whiteboard
BW, BH = 3200, 1800
GROUND_Y = 1540
PAD_X, LZ_X = 520, 980

def flight_curve(n=480):
    """the plan, drawn by hand: up from the pad and over to the east; turn (the flip) at the top; a short burn back;
    a high arc back toward the coast; the last part nearly vertical onto the LZ."""
    pts = []
    for k in range(n):
        u = k / (n - 1)
        if u < 0.46:                                         # ascent
            v = u / 0.46
            x = PAD_X + 1900 * v ** 1.7; y = GROUND_Y - 1180 * math.sin(v * math.pi / 2) ** 0.85
        elif u < 0.56:                                       # the turn + boostback: a tight hook back to the west
            v = (u - 0.46) / 0.10
            x0, y0 = PAD_X + 1900, GROUND_Y - 1180
            x = x0 + 120 * math.sin(v * math.pi) - 240 * v ** 2; y = y0 - 90 * math.sin(v * math.pi * 0.9)
        else:                                                # the long fall back to the coast, steepening
            v = (u - 0.56) / 0.44
            x0, y0 = PAD_X + 1900 - 240, GROUND_Y - 1180
            x = x0 + (LZ_X - x0) * (1 - (1 - v) ** 1.6); y = y0 + (GROUND_Y - y0) * v ** 2.2
        pts.append((x, y))
    return np.array(pts, F32)

ANNOT = [  # (curve parameter, text, offset, key)
    (0.462, "turn here", (60, -150), "turn"),
    (0.52, "burn here", (-520, -140), "burn"),
    (0.74, "fall this far", (90, -20), "fall"),
    (0.965, "light again", (90, -110), "light"),
    (1.00, "come back", (-150, 90), "back"),
]

@lru_cache(1)
def _board_bg():
    bg = np.full((BH, BW, 3), 0.66, F32) * np.array([0.97, 0.985, 1.0], F32)
    ghost = cv2.resize(K.noise_tex(512, 91, 6, 0.6), (BW, BH), interpolation=cv2.INTER_CUBIC)
    bg *= (0.95 + 0.06 * ghost[..., None])
    # faint ghosts of erased marker
    im = Image.new("L", (BW, BH), 0); d = ImageDraw.Draw(im); f = ImageFont.truetype(F_MARK, 80)
    for (x, y, s) in [(2300, 260, "Δv?"), (2650, 1180, "q_max"), (300, 300, "T-10"), (1400, 160, "MECO 143s")]:
        d.text((x, y), s, font=f, fill=40)
    e = cv2.GaussianBlur(np.asarray(im, F32) / 255, (0, 0), 6)
    bg *= (1 - e[..., None] * 0.15)
    return bg

def board_ink(st):
    ink = np.zeros((BH, BW), np.uint8)
    pts = flight_curve()
    dr = st.get("draw", 0.0)
    n = int(len(pts) * clamp(dr))
    if n > 1:
        cv2.polylines(ink, [np.round(pts[:n] * 4).astype(np.int32)], False, 255, 14, cv2.LINE_AA, shift=2)
    gl = st.get("ground", 1.0)
    if gl > 0:
        x_end = int(lerp(220, 3000, clamp(gl)))
        cv2.line(ink, (220 * 4, GROUND_Y * 4), (x_end * 4, (GROUND_Y + 8) * 4), 255, 10, cv2.LINE_AA, shift=2)
    im = Image.fromarray(ink); d = ImageDraw.Draw(im)
    fs = ImageFont.truetype(F_MARK, 52)
    if gl > 0.2: d.text((PAD_X - 70, GROUND_Y + 30), "pad", font=fs, fill=255)
    if gl > 0.4: d.text((LZ_X - 40, GROUND_Y + 30), "LZ", font=fs, fill=255)
    f = ImageFont.truetype(F_MARK, 96)
    notes = st.get("notes", {})
    for (cu, text, off, key) in ANNOT:
        pr = clamp(notes.get(key, 0.0))
        if pr <= 0: continue
        i = min(len(pts) - 1, int(cu * (len(pts) - 1)))
        x, y = pts[i]
        mk = clamp(pr * 3)
        if key == "turn": d.arc((x - 30, y - 30, x + 30, y + 30), 0, int(360 * mk), fill=255, width=9)
        elif key == "burn":
            for k in range(int(round(4 * mk))): d.line([(x - 22 + k * 15, y + 24), (x - 14 + k * 15, y + 64)], fill=255, width=8)
        elif key == "fall":
            L = 220 * mk; d.line([(x + 40, y - 10), (x + 40, y - 10 + L)], fill=255, width=8)
            if mk >= 1: d.polygon([(x + 18, y + 190), (x + 62, y + 190), (x + 40, y + 236)], fill=255)
        elif key == "light":
            for k in range(int(round(3 * mk))): d.line([(x - 26 + k * 18, y + 18), (x - 20 + k * 18, y + 54)], fill=255, width=8)
        elif key == "back":
            d.line([(x - 40, y - 40), (x - 40 + 80 * mk, y - 40 + 80 * mk)], fill=255, width=10)
            if mk > 0.5: d.line([(x - 40, y + 40), (x - 40 + 80 * (mk - 0.5) * 2, y + 40 - 80 * (mk - 0.5) * 2)], fill=255, width=10)
        k = int(round(len(text) * clamp((pr - 0.25) / 0.75)))
        if k > 0: d.text((x + off[0], y + off[1]), text[:k], font=f, fill=255)
    return np.asarray(im).astype(F32) / 255

def board_render(t, W, H, st):
    """st: draw (0..1 of the flight path), ground, notes (key -> 0..1), cam (cx, cy, zoom, ang, persp), glow (0..1 the drawing
    becoming light), dawn (0..1), lamp (0..1)."""
    bg = _board_bg()
    ink = board_ink(st)
    marker = np.array([0.025, 0.04, 0.10], F32)
    board = bg * (1 - ink[..., None] * 0.93) + marker * ink[..., None] * 0.93
    dawn = st.get("dawn", 0.0); lamp = st.get("lamp", 1.0)
    sc = 0.125; w, h = int(BW * sc), int(BH * sc)
    yy, xx = np.mgrid[0:h, 0:w].astype(F32) / sc
    E = (np.exp(-(((xx - 700) / 2400) ** 2 + ((yy - 2300) / 1900) ** 2)) * 0.75)[..., None] * np.array([1.0, 0.78, 0.55], F32) * lamp
    E += 0.02 + dawn * (0.25 + 0.35 * (xx / BW))[..., None] * np.array([1.0, 0.75, 0.66], F32)
    E = cv2.resize(E, (BW, BH), interpolation=cv2.INTER_LINEAR)
    lit = board * E
    glow = st.get("glow", 0.0)
    if glow > 0:                                      # the plan turns into light (match cut to the real arcs)
        li = cv2.resize(cv2.GaussianBlur(cv2.resize(ink, (BW // 4, BH // 4), interpolation=cv2.INTER_AREA), (0, 0), 3), (BW, BH))
        lit = lit * (1 - 0.9 * glow) + (li[..., None] * K.FLAME_O * 2.4 + ink[..., None] * K.FLAME_W * 2.2) * glow
    c = st.get("cam", {})
    cx, cy, zoom, ang = c.get("cx", BW / 2), c.get("cy", BH / 2), c.get("zoom", 1.0), c.get("ang", 0.0)
    sw = BW * 0.92 / zoom; sh = sw * H / W
    rot = math.radians(ang)
    corners = np.array([[-sw / 2, -sh / 2], [sw / 2, -sh / 2], [sw / 2, sh / 2], [-sw / 2, sh / 2]], F32)
    persp = c.get("persp", 0.05)
    corners[:, 0] *= np.array([1 - persp, 1 - persp, 1 + persp, 1 + persp], F32)   # looking slightly down at the board
    Rm = np.array([[math.cos(rot), -math.sin(rot)], [math.sin(rot), math.cos(rot)]], F32)
    src = corners @ Rm.T + np.array([cx, cy], F32)
    M = cv2.getPerspectiveTransform(src.astype(F32), np.float32([[0, 0], [W, 0], [W, H], [0, H]]))
    img = cv2.warpPerspective(lit, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0.004, 0.004, 0.005))
    img = dof_radial(img, st.get("dof", 0.7))
    return img, M

def screen_curve(M, n=480):
    """the whiteboard flight curve in screen pixels (for the match cut)."""
    p = flight_curve(n)
    return cv2.perspectiveTransform(p[None], M)[0]

def annot_xy(key):
    """board coordinates of an annotation's mark (for framing the camera on it)."""
    pts = flight_curve()
    for (cu, text, off, k) in ANNOT:
        if k == key:
            i = min(len(pts) - 1, int(cu * (len(pts) - 1))); return float(pts[i][0]), float(pts[i][1])
    return BW / 2, BH / 2
