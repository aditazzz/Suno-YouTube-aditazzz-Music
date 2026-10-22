"""Mirror, Mirror, Look at Us — Hall of Mirrors (version 2 of 3). See NOTES.md for the beats.

A walk down a long dark hall lined with the cover's bulb-lit vanity mirror. Every mirror bends the face from the cover
a different way (funhouse mirrors), and the verse lines label them with the machines we already let shape our
reflection: autocomplete, the beauty filter, take 30 of 30, auto-tune, ghostwriters... The one labelled AI-GENERATED
is the only mirror that doesn't bend anything. In the choruses every mirror straightens out: it looks like us. The
cover itself waits at the end of the hall; the camera reaches it for the last chorus and holds on it for the outro.
The lyrics appear as reflections (mirror-written) and flip the right way round as they are sung."""
import os, sys, math
from functools import lru_cache
import numpy as np, cv2

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import hall as Hl
ROOT = os.path.dirname(os.path.dirname(HERE)); sys.path.insert(0, ROOT)
from studio import core as C
import json

F32 = np.float32
TM = C.Timing(HERE)
LN = json.load(open(os.path.join(HERE, "build", "timed.json")))
def wt(i, j): return LN[i]["wt"][j]
def ls(i): return LN[i]["s"]
SONG = TM.duration; TAIL = 5.0; DUR = SONG + TAIL; T_END = 261.0
BEATS = np.array(TM.beats); DOWN = np.array(TM.downbeats)
ACC = C.hexc("e8b45a")                        # warm gold (bulb light)
IVORY = np.array([0.96, 0.93, 0.86], F32)

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def sstep(a, b, x):
    if b == a: return 1.0 if x >= b else 0.0
    t = clamp((x - a) / (b - a)); return t * t * (3 - 2 * t)
def ease_io(x): x = clamp(x); return x * x * x * (x * (6 * x - 15) + 10)
def lerp(a, b, k): return a + (b - a) * k
def since(arr, t):
    i = np.searchsorted(arr, t, side="right") - 1
    return t - arr[i] if i >= 0 else 99.0

def fmt_of(W, H): return "16x9" if W >= H else "9x16"
HALL = {"16x9": dict(Wc=1.35, Hc=2.7, Ym=1.08, D=1.7, tilt=18, fog=15.0, f=1250.0, lead=1.2, cover_d=3.02, maxyaw=58),
        "9x16": dict(Wc=1.0, Hc=2.7, Ym=1.08, D=1.7, tilt=18, fog=15.0, f=1080.0, lead=1.1, cover_d=2.62, maxyaw=62)}
EYE = 1.05

# ================================================================ the walk: speed profile -> position along the hall
SPEED = [(0, 0.0), (4.4, 0.0), (6.6, 0.14), (12.2, 0.26), (13.4, 0.34), (37.3, 0.34), (38.6, 0.78), (44.0, 0.88),
         (45.4, 0.30), (81.8, 0.30), (83.4, 0.34), (109.4, 0.34), (110.6, 0.78), (116.0, 0.88), (117.8, 0.30),
         (154.8, 0.30), (157.0, 0.40), (179.4, 0.40), (181.8, 0.06), (195.0, 0.0), (196.8, 0.12), (202.3, 0.50),
         (205.3, 1.35), (206.30, 1.35), (206.62, 0.0), (209.0, 0.0)]
T_FINAL = (209.0, 244.9); FINAL_LEN = 11.0
GRID = 1 / 60.0
@lru_cache(1)
def walk():
    ts = np.arange(0, DUR + 1, GRID)
    v = np.interp(ts, [s[0] for s in SPEED], [s[1] for s in SPEED])
    v[ts > T_FINAL[0]] = 0.0
    z = 1.0 - np.concatenate([[0.0], np.cumsum((v[1:] + v[:-1]) * 0.5 * GRID)])
    zf = z[np.searchsorted(ts, T_FINAL[0])]
    k = np.clip((ts - T_FINAL[0]) / (T_FINAL[1] - T_FINAL[0]), 0, 1); k = k * k * k * (k * (6 * k - 15) + 10)
    z = np.where(ts > T_FINAL[0], zf - FINAL_LEN * k, z)
    return ts, z.astype(np.float64), v
def cam_z(t): ts, z, _ = walk(); return float(np.interp(t, ts, z))
def speed(t): ts, _, v = walk(); return float(np.interp(t, ts, v))
@lru_cache(2)
def zend(fmt):
    ts, z, _ = walk(); return -(float(z[-1]) - HALL[fmt]["cover_d"])

def mirror_z(side, k, D): return -(k + (0.0 if side < 0 else 0.5)) * D

# ================================================================ which mirror shows what
# the verse lines: (start, end, side, kind, label); the mirror is picked where the camera will pass it
LOOKS = [(ls(1), ls(2), -1, "wave", "TOP COMMENT"), (ls(2), ls(3), 1, "pinch", "200 LIKES"),
         (ls(3), ls(4), -1, "tall", "AUTOCOMPLETE"), (ls(4), ls(5), 1, "twins", "FOR YOU"),
         (ls(5), ls(6), -1, "smooth", "BEAUTY FILTER"), (ls(6), ls(7), 1, "grid", "TAKE 30 OF 30"),
         (ls(7), ls(8) - 0.2, -1, "flat", "THE REAL ONE?"),
         (ls(23), ls(24), 1, "steps", "AUTO-TUNE"), (ls(24), ls(25), -1, "symm", "GHOSTWRITTEN"),
         (ls(25), ls(26), 1, "gold", "SPONSORED"), (ls(26), ls(27), -1, "bulge", "LAUGH TRACK"),
         (ls(27), ls(28), 1, "wide", "PREDICTED"), (ls(28), ls(29), -1, "twirl", "AUTOPILOT"),
         (ls(29), ls(30), 1, "mosaic", "RECOMMENDED"), (ls(30), LN[30]["e"] + 0.3, -1, "flat", "AI-GENERATED"),
         (ls(33), LN[33]["e"], 1, "flat", "YOU"),
         (ls(62), LN[62]["e"], -1, "flat", None)]
FILLER = ["wave", "bulge", "tall", "pinch", "wide", "twirl", "symm", "twins", "steps", "mosaic", "smooth", "gold"]

@lru_cache(2)
def plan(fmt):
    """per mirror (side, k): (kind, strength, label, look index). Looked-at mirrors are found from the walk."""
    hp = HALL[fmt]; D = hp["D"]; info = {}; looks = []
    for i, (a, b, side, kind, label) in enumerate(LOOKS):
        zm = cam_z((a + b) / 2) - hp["lead"]
        k = int(round(-zm / D - (0.0 if side < 0 else 0.5)))
        info[(side, k)] = (kind, 1.0, label, i); looks.append((a, b, side, k))
    return info, looks

def filler_kind(side, k):
    h = (k * 7 + (3 if side > 0 else 0)) % len(FILLER)
    return FILLER[h], 0.55 + 0.25 * (((k * 13 + (side > 0)) % 4) / 3)

# ---------------------------------------------------------------- the funhouse comes and goes
CHORUS = [(44.16, 82.57), (116.19, 156.18), (208.98, 262.0)]
FLAT_IN = [(wt(13, 2), 0.9), (wt(35, 2), 0.9), (wt(65, 2), 0.9), (wt(51, 3), 1.2)]   # "look at us" / "learns all our tricks"
FLAT_OUT = [(82.0, 1.4), (155.6, 1.4)]
def straighten(t):
    """1 = every mirror flat (it looks like us), 0 = the funhouse."""
    v = 0.0
    if t >= FLAT_IN[3][0] - 0.2 and t < 182.0: v = sstep(FLAT_IN[3][0], FLAT_IN[3][0] + FLAT_IN[3][1], t)
    if t >= 182.0: v = 1.0                         # from the bridge on: no more bending
    for (a, d), (b, d2) in zip(FLAT_IN[:2], FLAT_OUT):
        if a <= t < b + d2: v = max(v, sstep(a, a + d, t) * (1 - sstep(b, b + d2, t)))
    if t >= FLAT_IN[2][0]: v = 1.0
    if t >= wt(61, 0) - 0.5: v = 1.0
    return v

FAKE_T = [wt(45, 0), wt(45, 2), wt(46, 0), wt(47, 0), wt(47, 2), wt(48, 0)]
BREAK_LOOK = ["bulge", "tall", "twins", "wave", "wide", "pinch"]
SMOOTH_T, GOLD_T = wt(49, 0), wt(50, 0)
CRACK_T = wt(64, 2)                                 # "mad"

def mirror_state(fmt, side, k, t):
    """(kind, strength 0..1, crack 0..10, dark 0..10) for one wall mirror."""
    info, looks = plan(fmt)
    if (side, k) in info: kind, s, label, li = info[(side, k)]
    else: kind, s = filler_kind(side, k)
    # the break: every "Fake" pops the nearest mirrors to a hard bend; then everything filtered, then gold
    if 156.5 <= t < FLAT_IN[3][0] + 1.4:
        u = since(np.array(FAKE_T), t); n = int(np.searchsorted(FAKE_T, t, side="right")) - 1
        if n >= 0 and t < SMOOTH_T:
            kind = BREAK_LOOK[(n + k) % len(BREAK_LOOK)]; s = 0.45 + 0.55 * math.exp(-u / 0.6)
        if t >= SMOOTH_T: kind, s = ("smooth", 1.0) if t < GOLD_T else ("gold", 1.0)
    s = s * (1 - straighten(t))
    crack = 0 if t < CRACK_T else int(round(10 * clamp((t - CRACK_T) / 0.32)))
    return kind, s, crack, 0

# ---------------------------------------------------------------- light
def lights_on(fmt, t, idx):
    """brightness of the mirrors with pair index idx (array) at time t."""
    idx = np.asarray(idx)
    k0 = int(round(-cam_z(t) / HALL[fmt]["D"]))
    rel = idx - k0
    on = np.clip((t - (0.45 * np.maximum(rel - 3, 0) - 0.2)) / 0.18, 0, 1) if t < 9 else np.ones(idx.shape, F32)
    if 182.0 <= t < 197.5:                          # the bridge: the hall goes out, nearest first
        lines = [ls(i) for i in range(53, 61)]
        n = sum(1 for x in lines if t >= x)
        cut = k0 + n * 2.6 + 0.5
        off = np.clip((cut - idx) / 1.5, 0, 1) * sstep(182.0, 182.6, t)
        back = sstep(196.0, 197.4, t) * np.clip(1 - (idx - k0) * 0.08, 0, 1) if t >= 196 else 0
        on = np.clip(on * (1 - off) + back, 0, 1)
    pulse = 1.0
    if any(a <= t < b for a, b in CHORUS):
        pulse = 1.0 + 0.28 * math.exp(-since(DOWN, t) / 0.25) + 0.12 * math.exp(-since(BEATS, t) / 0.12)
    if 206.32 <= t < 207.2: pulse *= 1 + 1.6 * math.exp(-(t - CRACK_T) / 0.12)
    if wt(52, 3) <= t < wt(52, 3) + 0.9: pulse *= 0.35 + 0.65 * (0.5 + 0.5 * math.cos((t - wt(52, 3)) * 40))
    return (on * pulse).astype(F32)

def end_light(t):
    v = 0.8
    if 182.0 <= t < 191.56: v = 0.8 - 0.55 * sstep(182.0, 186.0, t)
    if t >= 191.56: v = 0.25 + 1.05 * sstep(191.56, 192.4, t) - 0.25 * sstep(196.0, 198.0, t)   # "handed back our portrait"
    if t >= 208.98: v = 1.0
    return v

# ================================================================ the camera
FLIPS = []                                          # "Mirror, mirror": the whole picture turns over, and back
for i in (13, 17, 35, 39, 65, 69):
    FLIPS.append((wt(i, 0), wt(i, 1)))
FLASHES = [tt for i, L in enumerate(LN) if L["sec"] in ("CH1", "CH2", "FINAL") for w, tt in zip(L["words"], L["wt"])
           if w.lower().startswith("mirror") and not any(abs(tt - a) < 0.01 or abs(tt - b) < 0.01 for a, b in FLIPS)]

def look_weight(t, a, b):
    return sstep(a - 0.55, a + 0.1, t) * (1 - sstep(b - 0.25, b + 0.45, t))

def camera(fmt, t):
    hp = HALL[fmt]; f = hp["f"]
    z = cam_z(t); v = speed(t)
    x = 0.0; y = EYE; yaw = 0.0; pitch = -1.0; roll = 0.0
    # walking: a gentle step bob and sway
    ph = t * 2 * math.pi * (1.0 + v * 1.3)
    y += 0.012 * min(1.0, v * 3) * math.sin(ph * 2); roll += 0.35 * min(1.0, v * 3) * math.sin(ph)
    yaw += 1.2 * math.sin(t * 0.23) + 0.6 * math.sin(t * 0.61 + 1); pitch += 0.5 * math.sin(t * 0.19 + 2)
    # looking at the mirrors the verses talk about
    info, looks = plan(fmt)
    for (a, b, side, k) in looks:
        w = look_weight(t, a, b)
        if w <= 0.001: continue
        zc = mirror_z(side, k, hp["D"]); xc = side * (hp["Wc"] - 0.3)
        ang = math.degrees(math.atan2(-(xc - x), -(zc - z)))
        ang = max(-hp["maxyaw"], min(hp["maxyaw"], ang))
        yaw = lerp(yaw, ang, ease_io(w))
    # pre-chorus 2: "searching for someone to blame" sweeps the hall
    if ls(34) <= t < ls(35) + 0.3:
        u = (t - ls(34)) / (ls(35) - ls(34)); yaw += 34 * math.sin(u * 2 * math.pi * 1.5) * sstep(ls(34), ls(34) + 0.4, t) * (1 - sstep(ls(35) - 0.2, ls(35) + 0.3, t))
    # the bridge: "We looked away" turns to the wall
    if 193.3 <= t < 197.6:
        w = sstep(193.6, 194.6, t) * (1 - sstep(196.2, 197.6, t))
        side, k = looked_away(fmt); zc = mirror_z(side, k, hp["D"]); xc = side * (hp["Wc"] - 0.25)
        yaw = lerp(yaw, math.degrees(math.atan2(-(xc - x), -(zc - z))), ease_io(w))
    # the end: rise to the cover's eye line and hold it square
    k = sstep(T_FINAL[1] - 9.0, T_FINAL[1], t)
    y = lerp(y, Hl.END_S / 2, k); pitch = lerp(pitch, 0.0, k); yaw = lerp(yaw, 0.0, k); roll = lerp(roll, 0.0, k)
    # the crack: a hard shake
    if CRACK_T <= t < CRACK_T + 1.2:
        e = math.exp(-(t - CRACK_T) / 0.22)
        yaw += 2.2 * e * math.sin(t * 71); pitch += 1.6 * e * math.cos(t * 83); roll += 2.5 * e * math.sin(t * 57)
    # the chorus downbeats push in a touch (the frame breathes)
    if any(a <= t < b for a, b in CHORUS) and t < T_FINAL[1] - 4:
        f *= 1 + 0.018 * math.exp(-since(DOWN, t) / 0.22)
    return Hl.Cam(x, y, z, yaw, pitch, roll, f)

def flip_scale(t):
    """horizontal scale of the whole picture: 1 normal, -1 mirrored; a quick squash through 0 on each flip."""
    s = 1.0
    for a, b in FLIPS:
        if a - 0.11 <= t < b + 0.11:
            if t < a + 0.11: u = (t - (a - 0.11)) / 0.22; return math.cos(math.pi * u)
            if t < b - 0.11: return -1.0
            u = (t - (b - 0.11)) / 0.22; return -math.cos(math.pi * u)
    return s

# ================================================================ rendering the hall
def hdr(t, W, H):
    fmt = fmt_of(W, H); hp = dict(HALL[fmt]); hp["Zend"] = zend(fmt); D = hp["D"]
    cam = camera(fmt, t)
    lf = lambda side, idx: lights_on(fmt, t, idx)
    eg = end_light(t)
    img = Hl.hall_bg(cam, W, H, hp, lf, eg, k=3)
    E = np.zeros_like(img)
    # the cover at the end of the hall
    crack = 0 if t < CRACK_T else int(round(10 * clamp((t - CRACK_T) / 0.32)))
    ec = Hl.end_corners(hp); xy, d = Hl.project(cam, ec, W, H)
    fogE = math.exp(-max(0.0, d.mean() - 4) / 60.0)
    Hl.warp_quad(img, Hl.end_tex(crack, 10), xy, d, gain=eg * fogE, near=0.3)
    s = 1254.0
    fr = [ec[0] + (ec[1] - ec[0]) * (Hl.FX0 / s) + (ec[3] - ec[0]) * (Hl.FY0 / s), ec[0] + (ec[1] - ec[0]) * (Hl.FX1 / s) + (ec[3] - ec[0]) * (Hl.FY0 / s),
          ec[0] + (ec[1] - ec[0]) * (Hl.FX1 / s) + (ec[3] - ec[0]) * (Hl.FY1 / s), ec[0] + (ec[1] - ec[0]) * (Hl.FX0 / s) + (ec[3] - ec[0]) * (Hl.FY1 / s)]
    pts, rw = Hl.bulb_points(np.array(fr))
    Hl.splat_bulbs(E, cam, pts, rw * (fr[3][1] - fr[0][1]) / Hl.MIR_H * -1 if False else rw * Hl.END_S * Hl.TH / 1254.0, eg * fogE, W, H)
    # the wall mirrors, far to near
    z0 = cam.z; zmax = -hp["Zend"] + 1.2
    items = []
    k_lo = max(1, int((-z0 - 1.0) / D) - 1); k_hi = int((-z0 + 26) / D) + 1
    for k in range(k_lo, k_hi + 1):
        for side in (-1, 1):
            zc = mirror_z(side, k, D)
            if zc > z0 + 0.6 or zc < zmax: continue
            items.append((zc, side, k))
    items.sort(key=lambda a: a[0])
    for zc, side, k in items:
        corners = Hl.mirror_corners(side, zc, hp)
        xy, d = Hl.project(cam, corners, W, H)
        if d.max() < 0.3: continue
        if (xy[:, 0].max() < -40 or xy[:, 0].min() > W + 40) and d.min() > 0: continue
        L = float(lights_on(fmt, t, np.array([k]))[0])
        kind, s_, crack, dark = mirror_state(fmt, side, k, t)
        if 193.6 <= t < 197.6 and (side, k) == looked_away(fmt): dark = int(round(10 * sstep(193.9, 194.5, t) * (1 - sstep(196.3, 197.2, t))))
        kq = int(round(s_ * 10)); key = ("flat", 0) if kq == 0 else (kind, kq)
        fog = math.exp(-max(0.0, d.mean() - 2.0) / 22.0)
        gain = (0.10 + 0.90 * min(1.0, L)) * fog
        rc = corners.copy(); rc[:, 1] *= -1
        rxy, rd = Hl.project(cam, rc, W, H)
        Hl.warp_quad(img, [Hl.refl_tex(key[0], key[1], crack, dark)], rxy, rd, gain=gain, near=0.3)
        Hl.warp_quad(img, Hl.mirror_tex(key[0], key[1], crack, dark), xy, d, gain=gain)
        if d.mean() < 22:
            pts, rw = Hl.bulb_points(corners)
            Hl.splat_bulbs(E, cam, pts, rw, L * fog, W, H)
            rp = pts.copy(); rp[:, 1] *= -1
            Hl.splat_bulbs(E, cam, rp, rw, 0.28 * L * fog, W, H, refl=True)
    # the crack: a white flash along everything
    if CRACK_T <= t < CRACK_T + 0.5: img += F32(0.35 * math.exp(-(t - CRACK_T) / 0.08))
    img += E; img += C.bloom(E, 0.85)
    return img, cam, hp

@lru_cache(2)
def looked_away(fmt):
    """the wall mirror the camera turns to on "We looked away" (its glass goes black)."""
    hp = HALL[fmt]; z = cam_z(194.8); D = hp["D"]
    k = int(round((-(z - (1.7 if fmt == "16x9" else 1.5))) / D)); return (-1, k)

# ================================================================ labels and lyrics
F_LYR = os.path.join(ROOT, "assets", "fonts", "CormorantGaramond-Bold.ttf")
F_LAB = os.path.join(ROOT, "assets", "fonts", "PlayfairDisplaySC-Regular.ttf")
def draw_labels(out, t, W, H, cam, hp, fmt):
    info, looks = plan(fmt)
    fs = 46 if W > H else 48
    for i, (a, b, side, k) in enumerate(looks):
        label = LOOKS[i][4]
        if not label: continue
        op = sstep(a - 0.15, a + 0.25, t) * (1 - sstep(b - 0.1, b + 0.35, t))
        if op <= 0.01: continue
        corners = Hl.mirror_corners(side, mirror_z(side, k, hp["D"]), hp)
        bot = (corners[2] + corners[3]) / 2 - np.array([0, 0.05, 0])
        xy, d = Hl.project(cam, bot[None], W, H)
        if d[0] < 0.3: continue
        sp = C.sprite(label, F_LAB, fs, 0, track=3)
        w = sp[0].shape[1]; h = sp[0].shape[0]
        x = float(np.clip(xy[0, 0], w / 2 + 70, W - w / 2 - 70)); y = float(np.clip(xy[0, 1] + 26, 120, H * (0.60 if W > H else 0.56)))
        bw, bh = int(w + 46), int(h + 18)
        C._pill(out, x - bw / 2, y - bh / 2, bw, bh, np.array([0.05, 0.035, 0.025], F32), 0.82 * op)
        cv2.rectangle(out, (int(x - bw / 2 + 5), int(y - bh / 2 + 5)), (int(x + bw / 2 - 5), int(y + bh / 2 - 5)),
                      tuple(float(c) * op * 0.9 for c in ACC), 2, cv2.LINE_AA)
        C.blit(out, sp, x, y, ACC * 1.05, op, anchor="c")

F_STAMP = os.path.join(ROOT, "assets", "fonts", "SairaStencilOne-Regular.ttf")
STAMP_RED = np.array([0.86, 0.10, 0.12], F32)
@lru_cache(64)
def stamp_sprite(text, size, rot):
    from PIL import Image, ImageDraw, ImageFont
    f = ImageFont.truetype(F_STAMP, size); tw = f.getlength(text); pad = int(size * 0.28)
    w, h = int(tw + pad * 2), int(size * 1.25 + pad * 2)
    im = Image.new("L", (w, h), 0); d = ImageDraw.Draw(im)
    d.rounded_rectangle((pad * 0.35, pad * 0.35, w - pad * 0.35, h - pad * 0.35), int(size * 0.14), outline=255, width=max(3, size // 11))
    d.text((w / 2, h / 2), text, font=f, fill=255, anchor="mm")
    a = np.asarray(im.rotate(rot, resample=Image.BICUBIC, expand=True), np.float32) / 255
    rng = np.random.default_rng(len(text) + size)
    grit = cv2.GaussianBlur(rng.random(a.shape).astype(F32), (0, 0), 1.2)
    a = a * np.clip(0.55 + grit * 0.9, 0, 1)
    return (a, None, 0)

def draw_stamps(out, t, W, H, cam, hp, fmt):
    if not (FAKE_T[0] - 0.1 <= t < SMOOTH_T + 0.6): return
    D = hp["D"]
    for n, tf in enumerate(FAKE_T):
        if t < tf: break
        side = -1 if n % 2 == 0 else 1                 # each stamp lands on a mirror just ahead of the camera
        k = int(round((-(cam_z(tf) - 2.9)) / D - (0.0 if side < 0 else 0.5)))
        corners = Hl.mirror_corners(side, mirror_z(side, k, D), hp)
        c = corners.mean(0); xy, d = Hl.project(cam, c[None], W, H)
        if d[0] < 0.4: continue
        px = (Hl.MIR_H * 0.55) * cam.f / d[0]
        size = int(clamp(px / 1.25 * 0.32, 18, 120) // 4 * 4)
        u = t - tf; pop = 1 + 0.6 * math.exp(-u / 0.05)
        op = clamp(u / 0.04) * (1 - sstep(SMOOTH_T, SMOOTH_T + 0.6, t))
        sp = stamp_sprite("FAKE", size, (-8, 6, -4, 9, -10, 5)[n])
        C.blit(out, sp, float(xy[0, 0]), float(xy[0, 1]), STAMP_RED, op, anchor="c", scale=pop)

def lyric_rows(i, fs, maxw):
    words = LN[i]["words"]; f = C.font(F_LYR, fs); sp = f.getlength(" ")
    rows = [[]]; x = 0.0
    for j, w in enumerate(words):
        ww = f.getlength(w)
        if rows[-1] and x + ww > maxw: rows.append([]); x = 0.0
        rows[-1].append((j, w, x, ww)); x += ww + sp
    return rows

def word_sprite(w, fs, sx):
    """the word's sprite squeezed horizontally to |sx| and mirrored when sx < 0."""
    a, g, pad = C.sprite(w, F_LYR, fs, 10)
    nw = max(1, int(round(a.shape[1] * abs(sx))))
    if nw != a.shape[1]:
        a = cv2.resize(a, (nw, a.shape[0]), interpolation=cv2.INTER_AREA); g = cv2.resize(g, (nw, g.shape[0]), interpolation=cv2.INTER_AREA)
    if sx < 0: a, g = a[:, ::-1], g[:, ::-1]
    return (np.ascontiguousarray(a), np.ascontiguousarray(g), 0)

@lru_cache(4)
def lyric_bed(W, H):
    y = np.arange(H, dtype=F32)[:, None, None] / H
    c = 0.835 if W > H else 0.715; s = 0.085 if W > H else 0.06
    return (1 - 0.55 * np.exp(-((y - c) / s) ** 2)).astype(F32)

@lru_cache(1)
def line_windows():
    """(appear, leave) per line: a line stays up at least 0.35 s after its last word, and the next one (shown mirrored
    until its words are sung) only appears once it has gone."""
    out = []; prev_end = -1e9
    for i, L in enumerate(LN):
        nxt = LN[i + 1]["s"] if i + 1 < len(LN) else 1e9
        a = max(L["s"] - 0.45, prev_end + 0.02)
        b = max(L["wt"][-1] + 0.35, min(L["e"] + 1.2, nxt - 0.62))
        if L["sec"] == "TAG": b = T_END + 0.3          # gone as the end card comes in
        out.append((a, b)); prev_end = b + 0.25
    return out

def active_lines(t):
    return [(i, a, b) for i, (a, b) in enumerate(line_windows()) if a <= t < b + 0.25]

def draw_lyrics(out, t, W, H):
    vert = H > W; fs = 84 if vert else 92; maxw = W * (0.88 if vert else 0.80)
    cy0 = H * (0.715 if vert else 0.835)
    flt = C.STATE.get("lyric_filter")                 # edit joins / clip openings: hide lines from before the cut
    for (i, a, b) in active_lines(t):
        if flt is not None and not flt(LN[i]): continue
        op = sstep(a, a + 0.22, t) * (1 - sstep(b, b + 0.25, t))
        if op <= 0.01: continue
        rows = lyric_rows(i, fs, maxw); lh = fs * 1.08
        y0 = cy0 - (len(rows) - 1) * lh / 2
        for r, row in enumerate(rows):
            rw = row[-1][2] + row[-1][3]; x0 = W / 2 - rw / 2; y = y0 + r * lh
            for (j, w, x, ww) in row:
                tw = LN[i]["wt"][j]
                u = (t - (tw - 0.10)) / 0.20
                sx = -1.0 if u <= 0 else (1.0 if u >= 1 else -math.cos(math.pi * u))
                act = math.exp(-max(0.0, t - tw) / 0.55) if t >= tw - 0.1 else 0.0
                col = IVORY * (1 - act) + ACC * act
                o = op * (0.34 + 0.66 * sstep(tw - 0.12, tw + 0.08, t))
                sp = word_sprite(w, fs, sx)
                cx = x0 + x + ww / 2
                C.shadow(out, sp, cx - sp[0].shape[1] / 2, y - sp[0].shape[0] / 2 + 3, 0.85 * o)
                C.blit(out, sp, cx, y, col, o, 0.55 * act * o, glow_color=ACC, anchor="c")
                # its reflection on the floor
                if r == len(rows) - 1:
                    ra = sp[0][::-1] * refl_ramp(sp[0].shape[0])
                    C.blit(out, (np.ascontiguousarray(ra), None, 0), cx, y + fs * 0.98, col * 0.9, 0.22 * o, anchor="c")

@lru_cache(16)
def refl_ramp(h): return (np.clip(1 - np.arange(h, dtype=F32) / (h * 0.75), 0, 1) ** 1.6)[:, None]

# ================================================================ finishing
@lru_cache(4)
def vignette(W, H):
    yy, xx = np.mgrid[0:H, 0:W].astype(F32)
    d = np.hypot((xx - W / 2) / (W / 2), (yy - H / 2) / (H / 2))
    return np.clip(1 - 0.20 * d ** 2.4, 0, 1)[..., None].astype(F32)

def soft_shoulder(x, knee=0.80):
    m = x > knee
    if m.any(): v = x[m]; x[m] = knee + (1 - knee) * (1 - np.exp(-(v - knee) / (1 - knee)))
    return x

def apply_flip(out, sx):
    """the picture turned like a hand mirror: squeezed toward the centre line (never below 30 %, over a blurred, dimmed
    copy of itself) and mirrored once it has passed edge-on."""
    if sx >= 0.999: return out
    H, W = out.shape[:2]
    if sx <= -0.999: return np.ascontiguousarray(out[:, ::-1])
    src = out if sx > 0 else out[:, ::-1]
    k = 0.30 + 0.70 * abs(sx)
    nw = max(2, int(round(W * k)))
    sq = cv2.resize(src, (nw, H), interpolation=cv2.INTER_AREA)
    bg = cv2.resize(cv2.GaussianBlur(cv2.resize(src, (W // 8, H // 8), interpolation=cv2.INTER_AREA), (0, 0), 3), (W, H)) * F32(0.45)
    x0 = (W - nw) // 2; bg[:, x0:x0 + nw] = sq
    edge = np.zeros(W, F32); edge[max(0, x0 - 2):x0 + 3] = 1; edge[max(0, x0 + nw - 3):x0 + nw + 2] = 1
    bg += edge[None, :, None] * F32(0.25) * (1 - abs(sx))
    return bg

def render_frame(t, W=1920, H=1080, fi=0):
    fmt = fmt_of(W, H)
    img, cam, hp = hdr(t, W, H)
    np.clip(soft_shoulder(img), 0, 1, out=img)
    out = cv2.pow(img, 1 / 2.2)
    out = apply_flip(out, flip_scale(t))
    out *= vignette(W, H)
    p = C.post(W, H)
    out += (cv2.resize(p.grain[fi % 6], (W, H), interpolation=cv2.INTER_NEAREST) * F32(0.012))[..., None]
    if not C.STATE["clean"]:
        out *= lyric_bed(W, H)
        if flip_scale(t) > 0.98: draw_labels(out, t, W, H, cam, hp, fmt); draw_stamps(out, t, W, H, cam, hp, fmt)
        draw_lyrics(out, t, W, H)
        C.subscribe_pill(out, t, W, H, 83.6, 5.0)
        C.end_screen(out, t, W, H, T_END, DUR - T_END, "Funny how it looks like us.",
                     sub_line="Subscribe for a new song every week", title="Mirror, Mirror, Look at Us", accent=ACC)
    out *= (1 - sstep(DUR - 1.0, DUR - 0.05, t))
    return (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)
