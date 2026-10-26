"""Everything drawn on top of the world: map labels (Ted's buzzwords as place names), the pinned question, Ted's
marker, the map-app chrome (search bar, compass, scale bar, clock), the bridge's 15-minute ring, the giant
IT'S A TED TALK region labels, the lyrics, the subscribe pill and the end card."""
import math
import numpy as np, cv2
from studio import core as C
from studio.core import sstep, ease_out, ease_io, clamp, lerp, hexc
S = None                     # the scene module; set by scene.py (avoids a circular import)
import office as OF
import citymap as CM
import cosmos as CO
from view import View

F32 = np.float32

# ---------------------------------------------------------------- text helpers
def _anchor(w, h, pad, ax, ay, asc, size):
    X = {'l': -pad, 'c': -w / 2, 'r': -(w - pad)}[ax]
    Y = {'t': -pad, 'c': -h / 2, 'b': -(h - pad), 'm': -(pad + asc - 0.36 * size)}[ay]
    return X, Y

def label(img, s, x, y, font, size, col, halo=None, op=1.0, ax='c', ay='m', track=0, halo_k=1.0):
    """text with an optional soft halo (map-label style). (x, y): anchor point."""
    if op <= 0.004 or not s: return 0
    size = int(round(size)); gl = max(3, int(size * 0.13))
    spr = C.sprite(s, font, size, gl, track=int(track))
    a, g, pad = spr; h, w = a.shape
    asc, _ = C.font(font, size).getmetrics()
    dx, dy = _anchor(w, h, pad, ax, ay, asc, size)
    X, Y = int(round(x + dx)), int(round(y + dy))
    H, W = img.shape[:2]; x0, y0, x1, y1 = max(0, X), max(0, Y), min(W, X + w), min(H, Y + h)
    if x1 <= x0 or y1 <= y0: return w - 2 * pad
    reg = img[y0:y1, x0:x1]
    if halo is not None:
        m = np.clip(g[y0 - Y:y1 - Y, x0 - X:x1 - X] * 3.2 * halo_k, 0, 1)[..., None] * op
        reg *= (1 - m); reg += m * np.asarray(halo, F32)
    m = a[y0 - Y:y1 - Y, x0 - X:x1 - X][..., None] * op
    reg *= (1 - m); reg += m * np.asarray(col, F32)
    return w - 2 * pad

def label_rot(img, s, x, y, ang, font, size, col, halo=None, op=1.0, track=0):
    """centred text turned by ang (radians, screen)"""
    if op <= 0.004: return
    size = int(round(size)); gl = max(3, int(size * 0.13))
    a, g, pad = C.sprite(s, font, size, gl, track=int(track))
    if abs(math.sin(ang)) < 1e-3 and math.cos(ang) > 0: return label(img, s, x, y, font, size, col, halo, op, 'c', 'c', track)
    h, w = a.shape; D = int(math.hypot(w, h)) + 4
    M = cv2.getRotationMatrix2D((w / 2, h / 2), -math.degrees(ang), 1.0); M[0, 2] += (D - w) / 2; M[1, 2] += (D - h) / 2
    ar = cv2.warpAffine(a, M, (D, D)); gr = cv2.warpAffine(g, M, (D, D))
    X, Y = int(round(x - D / 2)), int(round(y - D / 2)); H, W = img.shape[:2]
    x0, y0, x1, y1 = max(0, X), max(0, Y), min(W, X + D), min(H, Y + D)
    if x1 <= x0 or y1 <= y0: return
    reg = img[y0:y1, x0:x1]
    if halo is not None:
        m = np.clip(gr[y0 - Y:y1 - Y, x0 - X:x1 - X] * 3.2, 0, 1)[..., None] * op
        reg *= (1 - m); reg += m * np.asarray(halo, F32)
    m = ar[y0 - Y:y1 - Y, x0 - X:x1 - X][..., None] * op
    reg *= (1 - m); reg += m * np.asarray(col, F32)

def rrect(img, x, y, w, h, r, col, op=1.0, shadow=0.0):
    H, W = img.shape[:2]
    pad = int(30 + r); X0, Y0 = int(x) - pad, int(y) - pad; X1, Y1 = int(x + w) + pad, int(y + h) + pad
    x0, y0, x1, y1 = max(0, X0), max(0, Y0), min(W, X1), min(H, Y1)
    if x1 <= x0 or y1 <= y0: return
    m = np.zeros((Y1 - Y0, X1 - X0), np.uint8)
    cv2.rectangle(m, (int((x - X0 + r) * 16), int((y - Y0) * 16)), (int((x - X0 + w - r) * 16), int((y - Y0 + h) * 16)), 255, -1, cv2.LINE_AA, 4)
    cv2.rectangle(m, (int((x - X0) * 16), int((y - Y0 + r) * 16)), (int((x - X0 + w) * 16), int((y - Y0 + h - r) * 16)), 255, -1, cv2.LINE_AA, 4)
    for cx, cy in ((x + r, y + r), (x + w - r, y + r), (x + r, y + h - r), (x + w - r, y + h - r)):
        cv2.circle(m, (int((cx - X0) * 16), int((cy - Y0) * 16)), int(r * 16), 255, -1, cv2.LINE_AA, 4)
    a = m.astype(F32) / 255.0
    reg = img[y0:y1, x0:x1]; aa = a[y0 - Y0:y1 - Y0, x0 - X0:x1 - X0]
    if shadow > 0:
        sh = cv2.GaussianBlur(a, (0, 0), 9)
        sh = np.roll(sh, 5, axis=0)[y0 - Y0:y1 - Y0, x0 - X0:x1 - X0]
        reg *= (1 - sh * shadow * op)[..., None]
    reg *= (1 - aa * op)[..., None]; reg += (aa * op)[..., None] * np.asarray(col, F32)

def disc(img, x, y, r, col, op=1.0, ring=None, ring_w=3.0):
    H, W = img.shape[:2]; R = int(r + ring_w + 4)
    X0, Y0 = int(x) - R, int(y) - R; X1, Y1 = int(x) + R + 1, int(y) + R + 1
    x0, y0, x1, y1 = max(0, X0), max(0, Y0), min(W, X1), min(H, Y1)
    if x1 <= x0 or y1 <= y0: return
    yy, xx = np.mgrid[Y0:Y1, X0:X1].astype(F32); d = np.sqrt((xx - x) ** 2 + (yy - y) ** 2)
    reg = img[y0:y1, x0:x1]; sl = (slice(y0 - Y0, y1 - Y0), slice(x0 - X0, x1 - X0))
    if ring is not None:
        a = np.clip(r + ring_w - d + 0.5, 0, 1)[sl][..., None] * op; reg *= (1 - a); reg += a * np.asarray(ring, F32)
    a = np.clip(r - d + 0.5, 0, 1)[sl][..., None] * op; reg *= (1 - a); reg += a * np.asarray(col, F32)

# ---------------------------------------------------------------- the views (what is where on screen)
def map_view(t, z, W, H, th): return View(W, H, *S.map_center(W, H), 10 ** z / 1920.0, th)
def space_view(t, z, W, H):
    c = S.space_center(z)
    return View(W, H, c[0], c[1], 10 ** z / 1920.0, 0.0)

def pin_screen(t, z, W, H, th):
    """screen position of the question (the narrator) at time t"""
    if z < 6.4:
        p_map = map_view(t, z, W, H, th).to_px(S.me_world()[None])[0]
        if z < 6.15: return p_map
    if z < 8.3: p_sp = np.array([W / 2.0, H / 2.0])
    else:
        v = space_view(t, z, W, H); P = CO.planet_positions(S.years(t))
        p_sp = v.to_px(P["Earth"][None])[0] if z < 14.0 else (v.to_px(np.zeros((1, 2)))[0] * sstep(14.0, 14.5, z) + v.to_px(P["Earth"][None])[0] * sstep(14.5, 14.0, z))
    if z < 6.4:
        k = float(sstep(6.15, 6.4, z)); return p_map * (1 - k) + p_sp * k
    return p_sp

def bg_dark(img, x0, y0, x1, y1):
    H, W = img.shape[:2]; x0, y0, x1, y1 = max(0, int(x0)), max(0, int(y0)), min(W, int(x1)), min(H, int(y1))
    if x1 <= x0 or y1 <= y0: return 0.0
    return float(1 - img[y0:y1:4, x0:x1:4].mean())

# ---------------------------------------------------------------- map labels
STREETS = [("h", -70, "Circle Back Blvd"), ("h", 70, "North Star Ave"), ("v", -70, "Synergy St"), ("v", 70, "Deep Dive Dr"),
           ("h", 210, "Bandwidth Ave"), ("h", -210, "Double-Click Way"), ("v", 210, "Leverage Ln"), ("v", -210, "Pivot Pkwy"),
           ("h", 490, "Low-Hanging Fruit St"), ("v", -490, "Move The Needle Rd")]
PLACES = [  # text, world, zmin, zmax, style
    ("Kitchen", (32.6, -11.5), 1.35, 2.15, "poi"), ("Lounge", (-25.8, -8.2), 1.35, 2.15, "poi"),
    ("Meeting rooms", (-10.0, -18.2), 1.45, 2.15, "poi"),
    ("DOWNTOWN", (380, -560), 3.15, 4.25, "district"), ("WHERE HE WAS YOUNG", (-2700, 1950), 3.35, 4.55, "district"),
    ("NOBODY BELIEVED IN HIM HEIGHTS", (2600, -2900), 3.4, 4.6, "district"),
    ("Story About His Father Park", (-700, 350), 2.65, 3.75, "park"), ("Tangent River", (-2350, -1660), 3.0, 4.55, "water"),
    ("15-Minute Loop", (-5400, 5300), 3.9, 4.95, "road"), ("Lake Pause", (16500, -15500), 4.35, 5.7, "water"),
    ("Pause Reservoir", (-23000, 22000), 4.45, 5.5, "water")]
def town_cues():
    return {"So": S.T_SOw, "Right?": S.T_RIGHT, "The Real Question": S.T_REALQ, "Journey": S.T_JOURNEY, "Unlock": S.T_UNLOCK,
            "Story": S.T_STORY, "Circle Back": -1e3, "Synergy": -1e3}

def zfade(z, a, b, e=0.15): return float(sstep(a, a + e, z) * sstep(b, b - e, z))

def keep_out(x, y, W, H, sc, w=300):
    """True where a label would collide with the lyrics or the scale bar"""
    if W > H:
        if y > H * 0.78: return True
        if x + w > W - 470 * sc and y > H - 130 * sc: return True
    else:
        if abs(y - H * 0.705) < 120 * sc: return True
        if x + w > W - 470 * sc and 330 * sc < y < 450 * sc: return True
        if y > H * 0.80: return True
    return False

def map_labels(img, t, z, W, H, th, sc):
    if z > 6.3: return
    v = map_view(t, z, W, H, th)
    # people's names (at the start, and at the bridge)
    kn = zfade(z, -5, 1.22, 0.12) * (sstep(S.T_V1, S.T_V1 + 0.6, t) * (1 - sstep(S.T_ASK - 0.4, S.T_ASK, t)) + sstep(S.T_EIGHT, S.T_EIGHT + 0.4, t) * (1 - sstep(S.T_FINAL + 0.4, S.T_FINAL + 1.2, t)))
    if kn > 0:
        st = S.story(t); bridge = t > S.T_STOP
        for i, (name, a, shirt, hair) in enumerate(OF.PEOPLE):
            if name == "Dana" and st["dana_gone"] > 0.6 and st["ghost"] < 0.5: continue
            if bridge and name not in ("Ted", "Dana"): continue          # the ring's colours say who is who
            p = OF.person_pos(i, t); o = p / np.linalg.norm(p) * (0.55 if not bridge else -0.48)
            q = v.to_px((p + o)[None])[0]
            col = S.RED if name == "Ted" else (S.BLUE_D if name == "Me" else S.INK2)
            nm = name + (" (ghost)" if name == "Dana" and st["ghost"] > 0.5 else "")
            hw = C.text_w(nm, S.F_SANS, int(34 * sc)) / 2 + 14 * sc
            label(img, nm, float(np.clip(q[0], hw, W - hw)), float(np.clip(q[1], 30 * sc, H - 30 * sc)), S.F_SANS, 34 * sc, col, S.WHITE, kn)
    # places
    for (txt, p, a, b, style) in PLACES:
        k = zfade(z, a, b)
        if k <= 0: continue
        q = v.to_px(np.array([p], float))[0]
        fs_ = {"poi": 34, "district": 34, "park": 36, "water": 44, "road": 34}[style] * sc
        hw = (C.text_w(txt, S.F_SANS, int(fs_)) + (len(txt) * 5 * sc if style == "district" else 0)) / 2 + 20 * sc
        if not (-hw < q[0] < W + hw and 0 < q[1] < H): continue
        q = np.array([np.clip(q[0], hw, W - hw), q[1]])
        pn = pin_screen(t, z, W, H, th)
        if style not in ("poi",):
            near = max(abs(q[0] - pn[0]) - hw - 160 * sc, (q[1] - pn[1]) + 170 * sc if q[1] < pn[1] else (q[1] - pn[1]) - 40 * sc)
            k *= float(np.clip(near / (60 * sc), 0, 1))
            if k <= 0: continue
        if style == "poi": label(img, txt, q[0], q[1], S.F_SANSM, 34 * sc, S.INK2, S.WHITE, k)
        elif style == "district": label(img, txt, q[0], q[1], S.F_SANS, 34 * sc, S.MUTE, S.WHITE, k, track=int(5 * sc))
        elif style == "park": label(img, txt, q[0], q[1], S.F_SANS, 36 * sc, C.hexc('3f7a3a'), S.WHITE, k)
        elif style == "water": label(img, txt, q[0], q[1], S.F_ITAL, 44 * sc, S.WATER_T, C.hexc('eaf4fb'), k)
        elif style == "road": label(img, txt, q[0], q[1], S.F_SANS, 34 * sc, C.hexc('8a6420'), C.hexc('fff6dd'), k)
    if 3.3 < z < 4.55:
        sub = zfade(z, 3.35, 4.55)
        q = v.to_px(np.array([[-2700, 1950]]))[0]; label(img, "(historic district)", q[0], q[1] + 42 * sc, S.F_ITAL, 36 * sc, S.MUTE, S.WHITE, sub)
    # street names along the streets, near the middle of the frame
    k = zfade(z, 1.95, 3.25)
    if k > 0:
        cx, cy = W / 2, H / 2
        for (o, c, name) in STREETS:
            # the point of the street closest to a spot a little off-centre
            ref = v.to_world(np.array([[cx + (340 if o == "h" else 0) * sc, cy + (0 if o == "h" else -250) * sc]]))[0]
            p = np.array([ref[0], c]) if o == "h" else np.array([c, ref[1]])
            q = v.to_px(p[None])[0]
            if not (60 < q[0] < W - 60 and 60 < q[1] < H - 60): continue
            pn = pin_screen(t, z, W, H, th)
            if abs(q[0] - pn[0]) < 260 * sc and -190 * sc < q[1] - pn[1] < 40 * sc: continue
            if keep_out(q[0], q[1], W, H, sc, 120 * sc): continue
            ang = th if o == "h" else th + math.pi / 2
            ang = (ang + math.pi / 2) % math.pi - math.pi / 2
            label_rot(img, name, q[0], q[1], ang, S.F_SANS, 34 * sc, S.INK2, S.WHITE, k)
    # towns: Ted's words, each appearing as he says it
    Wd = CM.world()
    for T in Wd.towns:
        cue = town_cues().get(T["name"], -1e3)
        kz = zfade(z, 4.55, 6.05)
        kt = sstep(cue, cue + 0.25, t) if cue > 0 else 1.0
        k = kz * kt
        if k <= 0: continue
        q = v.to_px(np.array([T["c"]], float))[0]
        pn = pin_screen(t, z, W, H, th)
        k *= float(np.clip((math.hypot(q[0] - pn[0], (q[1] - pn[1]) * 1.5) - 150 * sc) / (90 * sc), 0, 1))
        if k <= 0 or keep_out(q[0], q[1], W, H, sc, C.text_w(T["name"], S.F_SANS, int(42 * sc)) + 30 * sc): continue
        pop = 1 + 0.25 * math.exp(-max(0, t - cue) * 6) if cue > 0 else 1
        disc(img, q[0], q[1], 7 * sc * pop, S.INK2, k, ring=S.WHITE, ring_w=3 * sc)
        label(img, T["name"], q[0] + 16 * sc, q[1], S.F_SANS, 42 * sc * pop, S.INK, S.WHITE, k, 'l', 'm')

# ---------------------------------------------------------------- space labels
def space_labels(img, t, z, W, H, sc):
    if z < 7.5: return
    v = space_view(t, z, W, H); yr = S.years(t); P = CO.planet_positions(yr)
    pin = pin_screen(t, z, W, H, 0.0)
    def lab(txt, p, a, b, sub=None, dx=18, col=None, below=False):
        k = zfade(z, a, b)
        if k <= 0: return
        q = v.to_px(np.asarray(p, float)[None])[0]
        if not (40 * sc < q[0] < W - 60 * sc and 60 * sc < q[1] < H - 60 * sc): return
        if not below:
            dpin = math.hypot(q[0] - pin[0], (q[1] - pin[1]) * 1.6)
            k *= float(np.clip((dpin - 120 * sc) / (80 * sc), 0, 1))
            if k <= 0: return
        tw_ = C.text_w(txt, S.F_SANS, int(34 * sc)) + len(txt) * 4 * sc
        ax, x0 = ('l', q[0] + dx * sc) if q[0] + dx * sc + tw_ < W - 30 * sc else ('r', q[0] - dx * sc)
        if below: ax, x0, yq = 'c', q[0], q[1] + 44 * sc
        else: yq = q[1]
        if keep_out(x0 if ax == 'l' else x0 - tw_, yq, W, H, sc, tw_): return
        label(img, txt, x0, yq, S.F_SANS, 34 * sc, col if col is not None else C.hexc('e8eef7'), C.hexc('05070c'), k, ax, 'm', track=int(4 * sc))
        if sub: label(img, sub, x0, yq + 40 * sc, S.F_SANSM, 32 * sc, C.hexc('aab4c4'), C.hexc('05070c'), k * 0.95, ax, 'm')
    r, u = CO.plane_axes(); m3 = CO.moon_pos().astype(np.float64)
    moon2 = P["Earth"] + np.array([m3 @ r, -(m3 @ u)]) * CO.R_E
    lab("THE EARTH", P["Earth"], 7.75, 9.6, below=True)
    lab("THE MOON", moon2, 8.55, 10.4)
    for name, a, per, ang, rad, col in CO.PLANETS:
        if name == "Earth": continue
        zmin = 10.4 if a < 2 else 11.6; zmax = 12.4 if a < 2 else 14.2
        lab(name.upper(), P[name], zmin, zmax)
    lab("THE SUN", np.zeros(2), 11.0, 16.8, dx=26)
    for (nm, d, ang) in CO.NAMED_STARS:
        if d < 30: lab(nm.upper(), CO.named_star_pos(nm), 16.3, 18.6, sub=f"{d:g} light-years away")
        else: lab(nm.upper(), CO.named_star_pos(nm), 18.4, 19.9, sub=f"{d:,.0f} light-years")
    gc = np.array([-0.82, 0.48]) * 26000 * CO.LY
    lab("THE MILKY WAY", gc + np.array([0, -64000]) * CO.LY, 20.7, 23.3, sub="400 billion stars", dx=-60)
    lab("ANDROMEDA", S.ANDROMEDA, 22.25, 24.0, sub="2.5 million light-years", dx=26 + 110000 * CO.LY / v.mpp / sc)
    lab("TRIANGULUM", S.TRIANGULUM, 22.6, 23.7, dx=18 + 30000 * CO.LY / v.mpp / sc)
    k = zfade(z, 24.3, 26.0)
    if k > 0:
        label(img, "GALAXIES, STRUNG ALONG INVISIBLE THREADS", W / 2, H * (0.16 if W > H else 0.24), S.F_SANS, 34 * sc, C.hexc('d9e2f2'), C.hexc('05070c'), k, 'c', 'm', track=int(4 * sc))
    k = zfade(z, 26.8, 27.4)
    if k > 0:
        q = v.to_px(np.array([[0.0, -CO.R_OBS]]))[0]
        label(img, "THE OBSERVABLE UNIVERSE", W / 2, max(q[1] - 70 * sc, 70 * sc), S.F_SANS, 38 * sc, C.hexc('ffd9c2'), C.hexc('05070c'), k, 'c', 'm', track=int(5 * sc))
        label(img, "the edge of what any of us can see", W / 2, max(q[1] - 70 * sc, 70 * sc) + 48 * sc, S.F_ITAL, 40 * sc, C.hexc('e6c3ae'), C.hexc('05070c'), k, 'c', 'm')

# ---------------------------------------------------------------- the question, Ted, and the bridge's ring
def question(img, t, z, W, H, th, sc):
    k = sstep(S.T_ASK + 0.1, S.T_ASK + 0.45, t) * (1 - sstep(S.T_TED - 0.1, S.T_TED + 0.1, t) * (1 - sstep(S.T_STANDUP + 0.8, S.T_STANDUP + 1.1, t)))
    k *= 1 - sstep(S.T_END - 0.4, S.T_END + 0.2, t)                  # steps aside for the end card's text
    if k <= 0: return
    p = pin_screen(t, z, W, H, th)
    if z < 1.6: p = p + np.array([0, -18 * sc])                      # above the narrator's head
    dark = bg_dark(img, p[0] - 200, p[1] - 160, p[0] + 200, p[1] + 20)
    pop = 1 + 0.18 * math.exp(-max(0, t - S.T_ASK - 0.1) * 7)
    fs = 42 * sc * pop; fs2 = 32 * sc * pop
    txt = "Is the file ready?"; tw = C.text_w(txt, S.F_SANS, int(fs))
    bw = tw + 52 * sc; bh = fs * 1.25 + fs2 * 1.3 + 22 * sc
    bx = float(np.clip(p[0] - bw / 2, 14 * sc, W - bw - 14 * sc)); by = p[1] - 24 * sc - bh
    by = max(by, 8 * sc)
    rrect(img, bx, by, bw, bh, 20 * sc, S.WHITE, k, shadow=0.35)
    # tail
    tx_ = float(np.clip(p[0], bx + 26 * sc, bx + bw - 26 * sc))
    tri = np.array([[tx_ - 13 * sc, by + bh - 2], [tx_ + 13 * sc, by + bh - 2], [p[0], by + bh + 18 * sc]])
    m = np.zeros(img.shape[:2], np.uint8); cv2.fillPoly(m, [np.round(tri * 16).astype(np.int32)], 255, cv2.LINE_AA, 4)
    a = (m.astype(F32) / 255.0)[..., None] * k; img *= (1 - a); img += a * S.WHITE
    label(img, txt, bx + 26 * sc, by + 14 * sc + fs * 0.62, S.F_SANS, fs, S.INK, None, k, 'l', 'm')
    label(img, "Delivered", bx + bw - 24 * sc, by + bh - 12 * sc - fs2 * 0.5, S.F_SANSM, fs2, S.MUTE, None, k, 'r', 'm')
    disc(img, p[0], p[1] + 4 * sc, 8 * sc, S.BLUE, k, ring=S.WHITE, ring_w=3 * sc)

def ted_marker(img, t, z, W, H, th, sc):
    """Ted's red dot once he is too small to see; in the outro it drifts out of the universe"""
    k = sstep(1.75, 2.05, z) if t < S.T_FINAL + 30 else 1.0
    if t > S.T_STANDUP + 1.0 and t < S.T_FINAL + 2.0: k = sstep(1.75, 2.05, z)
    if k <= 0: return
    if z < 6.4:
        v = map_view(t, z, W, H, th); p = v.to_px(S.ted_world(t)[None])[0]
        if z > 2.6:
            pin = pin_screen(t, z, W, H, th); p = pin + np.array([26 * sc, -6 * sc]) * sstep(2.6, 3.4, z) + (p - pin) * sstep(3.4, 2.6, z)
    else:
        pin = pin_screen(t, z, W, H, th); p = pin + np.array([26 * sc, -6 * sc])
    # the drift: in the outro he takes it offline, out past the edge of the observable universe
    if t > S.T_HAVING - 0.2:
        pin = pin_screen(t, z, W, H, th)
        off_v, fade = S.ted_offset(t, z, W, H, sc); p = pin + off_v; k *= fade
        for j in range(1, 10):
            ov, _ = S.ted_offset(t - j * 0.09, S.Z(t - j * 0.09), W, H, sc)
            q = pin + ov * (10 ** (S.Z(t - j * 0.09) - z))
            disc(img, q[0], q[1], max(1.0, 6 * sc * (1 - j / 10)), S.RED, 0.28 * (1 - j / 10) * k)
    off = sstep(S.T_HAVING - 0.1, S.T_HAVING + 0.4, t)
    col = S.RED * (1 - off) + C.hexc('9a9590') * off
    disc(img, p[0], p[1], 9 * sc, col, k, ring=S.WHITE, ring_w=3 * sc)
    dark = bg_dark(img, p[0], p[1] - 30, p[0] + 200, p[1] + 30)
    txt = "Ted" + (" (offline)" if off > 0.5 else "")
    label(img, txt, p[0] + 18 * sc, p[1], S.F_SANS, 40 * sc, col if dark < 0.5 else C.hexc('ff6a5a') * (1 - off) + C.hexc('c9c4bd') * off,
          S.WHITE if dark < 0.5 else C.hexc('0a0a0f'), k, 'l', 'm')

def bridge_ring(img, t, z, W, H, th, sc):
    """'It is fifteen minutes for eight people. You have used six.' — a 15-minute ring around the circle"""
    if not (S.T_FIFTEEN - 0.2 < t < S.T_FINAL + 2.5) or z > 2.0: return
    k = sstep(S.T_FIFTEEN, S.T_FIFTEEN + 0.6, t) * (1 - sstep(S.T_FINAL + 0.6, S.T_FINAL + 1.6, t))
    if k <= 0: return
    v = map_view(t, z, W, H, th); c = v.to_px(np.zeros((1, 2)))[0]; R = 2.2 / v.mpp; wpx = max(3, 0.19 / v.mpp)
    draw = ease_out((t - S.T_FIFTEEN) / 1.0)
    k8 = sstep(S.T_EIGHT, S.T_EIGHT + 0.5, t); k6 = ease_io((t - S.T_SIX) / 1.0)
    st = S.story(t)
    shares = np.full(8, 1 / 8); shares[0] = lerp(1 / 8, 6 / 15, k6); shares[1:] = (1 - shares[0]) / 7
    def arc(a0, a1, col, op, dashed=False, w=None):
        if op <= 0.004 or a1 <= a0: return
        n = max(8, int(abs(a1 - a0) * R / 5)); A = np.linspace(a0, a1, n)
        P = np.stack([c[0] + R * np.cos(A + th), c[1] + R * np.sin(A + th)], 1)
        m = np.zeros(img.shape[:2], np.uint8); q = np.round(P * 16).astype(np.int32)
        ww = int(round(w if w else wpx))
        if dashed:
            for i in range(0, len(q) - 2, 3): cv2.line(m, tuple(q[i]), tuple(q[i + 1]), 255, ww, cv2.LINE_AA, 4)
        else: cv2.polylines(m, [q], False, 255, ww, cv2.LINE_AA, 4)
        aa = (m.astype(F32) / 255.0)[..., None] * op; img[:] = img * (1 - aa) + aa * np.asarray(col, F32)
    # the plain 15-minute ring, drawing itself on
    arc(-math.pi / 2, -math.pi / 2 + 2 * math.pi * draw, C.hexc('5d5a54'), k * (1 - k8))
    # each person's share, centred on where they stand (Ted's grows to 6 of 15 minutes)
    later = []
    if k8 > 0:
        a = -math.pi / 2 - shares[0] * math.pi
        for i in range(8):
            name, deg, shirt, hair = OF.PEOPLE[i]
            col = S.RED if i == 0 else C.hexc(shirt)
            ghosted = name == "Dana" and (st["dana_gone"] > 0.5)
            arc(a + 0.035, a + 2 * math.pi * shares[i] - 0.035, C.hexc('a9b6c6') if ghosted else col, k * k8, dashed=ghosted)
            if name == "Dana": later.append(a + 2 * math.pi * shares[i])
            a += 2 * math.pi * shares[i]
    # Dana's hard stop: a red tick where her time ends
    kh = sstep(S.T_HARD, S.T_HARD + 0.3, t) * k
    if kh > 0 and later:
        ae = later[0] + th
        p0 = c + np.array([math.cos(ae), math.sin(ae)]) * (R - 30 * sc); p1 = c + np.array([math.cos(ae), math.sin(ae)]) * (R + 30 * sc)
        m = np.zeros(img.shape[:2], np.uint8); cv2.line(m, tuple(np.round(p0 * 16).astype(int)), tuple(np.round(p1 * 16).astype(int)), 255, int(6 * sc), cv2.LINE_AA, 4)
        aa = (m.astype(F32) / 255.0)[..., None] * kh; img[:] = img * (1 - aa) + aa * S.RED
        p2 = c + np.array([math.cos(ae), math.sin(ae)]) * (R + 74 * sc)
        label(img, "hard stop", p2[0], p2[1], S.F_SANS, 34 * sc, S.RED, S.WHITE, kh)
    # the readout in the middle of the circle
    if k8 <= 0: txt, col = "15 MINUTES", S.INK
    elif k6 <= 0.02: txt, col = "8 PEOPLE", S.INK
    else:
        used = 6.0 * k6; txt, col = f"TED: {int(used)}:{int(round((used % 1) * 60)) % 60:02d} OF 15:00", S.RED
    label(img, txt, c[0], c[1] - 6 * sc, S.F_SANS, 38 * sc, col, S.WHITE, k, 'c', 'm', track=int(3 * sc))

# ---------------------------------------------------------------- IT'S A TED TALK (region labels at each hit)
def ted_talk_labels(img, t, z, W, H, sc):
    for i, th_ in enumerate(S.TT):
        dt = t - th_
        if dt < 0 or dt > 4.5: continue
        always = i == len(S.TT) - 1
        z0 = S.Z(th_)
        shrink = 10 ** (z0 - z)
        txt = "IT'S ALWAYS A TED TALK" if always else "IT'S A TED TALK"
        base = W * (0.80 if W > H else 0.92)
        size0 = 120 * sc; wtxt = C.text_w(txt, S.F_BLACK, int(size0)) + len(txt) * 0.30 * size0
        size = size0 * min(1.0, base / max(wtxt, 1)) * shrink
        if size < 10: continue
        k = sstep(0, 0.06, dt) * (1 - sstep(2.4 if not always else 3.6, 3.1 if not always else 4.4, dt))
        pin = np.array([W / 2, H / 2])
        y = pin[1] - max(H * (0.24 if W > H else 0.18) * shrink, 178 * sc + size * 0.62)
        dark = bg_dark(img, W * 0.2, y - size, W * 0.8, y + size)
        col = S.RED if dark < 0.5 else C.hexc('ff5b49')
        halo = S.WHITE if dark < 0.5 else C.hexc('07070b')
        pop = 1 + 0.12 * math.exp(-dt * 10)
        label(img, txt, pin[0], y, S.F_BLACK, size * pop, col, halo, k, 'c', 'm', track=int(size * pop * 0.30))

# ---------------------------------------------------------------- map-app chrome
def scale_bar(img, t, z, W, H, sc, k):
    mpp = 10 ** z / 1920.0
    target = 170 * sc * mpp
    e = math.floor(math.log10(target)); best = None
    for m in (1, 2, 5, 10):
        L = m * 10 ** e
        if L <= target: best = L
    L = best or 10 ** e; px = L / mpp
    def fmt(L):
        if L < 1000: return f"{L:g} m"
        if L < 1e9: return f"{L / 1000:,.0f} km"
        if L < 0.1 * CO.LY: return f"{L / 1e9:,.0f} million km"
        ly = L / CO.LY
        if ly < 1e3: return f"{ly:,.1f} light-years".replace(".0 ", " ")
        if ly < 1e6: return f"{ly / 1e3:,.0f},000 light-years"
        if ly < 1e9: return f"{ly / 1e6:,.0f} million light-years"
        return f"{ly / 1e9:,.0f} billion light-years"
    dark = z > 6.3
    col = C.hexc('e8edf5') if dark else S.INK2; halo = C.hexc('05070c') if dark else S.WHITE
    if W > H: x1, y = W - 52 * sc, H - 44 * sc
    else: x1, y = W - 52 * sc, 400 * sc
    x0 = x1 - px
    # draw in a small box around the bar only
    bx0, by0 = int(x0 - 12), int(y - 24 * sc); bx1, by1 = int(x1 + 12), int(y + 12)
    bx0, by0 = max(0, bx0), max(0, by0); bx1, by1 = min(img.shape[1], bx1), min(img.shape[0], by1)
    m = np.zeros((by1 - by0, bx1 - bx0), np.uint8)
    for seg in (((x0, y), (x1, y)), ((x0, y - 12 * sc), (x0, y + 1)), ((x1, y - 12 * sc), (x1, y + 1))):
        cv2.line(m, (int((seg[0][0] - bx0) * 16), int((seg[0][1] - by0) * 16)), (int((seg[1][0] - bx0) * 16), int((seg[1][1] - by0) * 16)), 255, max(2, int(3 * sc)), cv2.LINE_AA, 4)
    hm = cv2.dilate(m, np.ones((5, 5), np.uint8)); hm = cv2.GaussianBlur(hm, (0, 0), 1.5)
    reg = img[by0:by1, bx0:bx1]
    a = (hm.astype(F32) / 255.0)[..., None] * k; reg[:] = reg * (1 - a) + a * np.asarray(halo, F32)
    a = (m.astype(F32) / 255.0)[..., None] * k; reg[:] = reg * (1 - a) + a * np.asarray(col, F32)
    label(img, fmt(L), x1, y - 30 * sc, S.F_SANS, 34 * sc, col, halo, k, 'r', 'm')

def compass(img, t, z, W, H, th, sc, k):
    if k <= 0: return
    if W > H: cx, cy = W - 80 * sc, 80 * sc
    else: cx, cy = W - 80 * sc, 239 * sc
    disc(img, cx, cy, 34 * sc, S.WHITE, k * 0.96)
    a = th - math.pi / 2
    tip = (cx + math.cos(a) * 24 * sc, cy + math.sin(a) * 24 * sc); tail = (cx - math.cos(a) * 24 * sc, cy - math.sin(a) * 24 * sc)
    nrm = (-math.sin(a) * 8 * sc, math.cos(a) * 8 * sc)
    for (pt, col) in (((tip, (cx + nrm[0], cy + nrm[1]), (cx - nrm[0], cy - nrm[1])), S.RED), ((tail, (cx + nrm[0], cy + nrm[1]), (cx - nrm[0], cy - nrm[1])), C.hexc('b9b4ab'))):
        m = np.zeros(img.shape[:2], np.uint8); cv2.fillPoly(m, [np.round(np.array(pt) * 16).astype(np.int32)], 255, cv2.LINE_AA, 4)
        aa = (m.astype(F32) / 255.0)[..., None] * k; img[:] = img * (1 - aa) + aa * col

def search_bar(img, t, z, W, H, sc, k):
    if k <= 0: return
    if W > H: x, y, w, h = 48 * sc, 40 * sc, 560 * sc, 78 * sc
    else: x, y, w, h = 40 * sc, 200 * sc, W - 180 * sc, 78 * sc
    rrect(img, x, y, w, h, h / 2, S.WHITE, k, shadow=0.30)
    # magnifier
    cx, cy = x + 40 * sc, y + h / 2
    m = np.zeros(img.shape[:2], np.uint8)
    cv2.circle(m, (int((cx - 3 * sc) * 16), int((cy - 3 * sc) * 16)), int(11 * sc * 16), 255, max(2, int(3 * sc)), cv2.LINE_AA, 4)
    cv2.line(m, (int((cx + 5 * sc) * 16), int((cy + 5 * sc) * 16)), (int((cx + 14 * sc) * 16), int((cy + 14 * sc) * 16)), 255, max(2, int(3.5 * sc)), cv2.LINE_AA, 4)
    aa = (m.astype(F32) / 255.0)[..., None] * k; img[:] = img * (1 - aa) + aa * S.INK2
    # what's being searched
    q, res = "", None
    for (ta, tb, word) in ((S.T_SLIDES - 0.1, S.T_POINT - 0.1, "slides"), (S.T_POINT - 0.1, S.T_POINT + 2.4, "point"),
                           (S.T_SLIDES2 - 0.1, S.T_POINT2 - 0.1, "slides"), (S.T_POINT2 - 0.1, S.T_POINT2 + 2.4, "point"),
                           (S.T_REALQ - 0.3, S.T_REALQ + 2.6, "the real question")):
        if ta <= t < tb: q = C.typed(word, t, ta, ta + 0.35); res = t > ta + 0.45
    tx = x + 72 * sc
    if q:
        tw_ = label(img, q, tx, y + h / 2, S.F_SANS, 36 * sc, S.INK, None, k, 'l', 'm')
        if res: label(img, "No results", x + w - 30 * sc, y + h / 2, S.F_SANSM, 32 * sc, S.RED, None, k, 'r', 'm')
    else:
        label(img, "Search for an answer", tx, y + h / 2, S.F_SANSM, 34 * sc, S.MUTE, None, k, 'l', 'm')

def clock_chip(img, t, z, W, H, sc, k):
    if k <= 0: return
    if W > H: x, y = 48 * sc, 132 * sc
    else: x, y = 40 * sc, 292 * sc
    d = S.days(t)
    gave = sstep(S.T_GIVEUP, S.T_GIVEUP + 0.15, t)
    mins = 15 + min(t, S.T_SIX) / S.T_SIX * 6.0 if t < S.T_FINAL else 15 + 6 + (t - S.T_FINAL) / 20 * 4
    if d > 0.001 and gave < 0.5:
        dd = int(d); hrs = (d - dd) * 24
        h = (9 + int(hrs) + (15 + int(mins) - 15) // 60) % 24
        names = ["WED", "THU", "FRI", "SAT", "SUN", "MON", "TUE"]
        txt = f"{names[dd % 7]}, OCT {21 + dd}  ·  {((h - 1) % 12) + 1}:{int((hrs % 1) * 60):02d} {'AM' if h < 12 else 'PM'}"
        col = S.RED
    elif gave >= 0.5 and t < S.T_GIVEUP + 3.2:
        txt = "Calendar is not responding"; col = S.RED
    else:
        txt = f"WED, OCT 21  ·  9:{int(mins):02d} AM"; col = S.INK2
    fs = 32 * sc; tw = C.text_w(txt, S.F_SANS, int(fs))
    rrect(img, x, y, tw + 40 * sc, 54 * sc, 27 * sc, S.WHITE, k * 0.95, shadow=0.25)
    label(img, txt, x + 20 * sc, y + 27 * sc, S.F_SANS, fs, col, None, k, 'l', 'm')

# ---------------------------------------------------------------- lyrics
def lyrics(img, t, W, H):
    if C.STATE["clean"]: return
    vert = H > W; k = W / (1080 if vert else 1920)
    fs = int((64 if not vert else 58) * k); maxw = W * 0.80
    ybase = H * (0.855 if not vert else 0.705)
    flt = C.STATE["lyric_filter"]
    skip = lambda L: L['text'].startswith("It's a Ted talk") or L['text'].startswith("It's always") or L['text'].strip() == "Ted."
    vis = [L for L in TM_lines() if (flt is None or flt(L)) and not skip(L)]
    dark = float(sstep(0.40, 0.50, bg_dark(img, W * 0.15, ybase - fs, W * 0.85, ybase + fs * 1.6)))
    col = S.INK * (1 - dark) + S.WHITE * dark
    for li, L in enumerate(vis):
        nxt = vis[li + 1]['s'] if li + 1 < len(vis) else 1e9
        prv = (vis[li - 1]['e'] + 0.45) if li > 0 else -1e9
        if prv > L['s'] - 0.3: a0, a1 = L['s'] - 0.07, L['s'] + 0.05
        else: a0, a1 = L['s'] - 0.3, L['s']
        if L['e'] + 0.45 > nxt - 0.3: b0, b1 = nxt - 0.17, nxt - 0.07
        else: b0, b1 = L['e'] + 0.05, L['e'] + 0.45
        if not (a0 <= t <= b1): continue
        opl = sstep(a0, a1, t) * (1 - sstep(b0, b1, t))
        if opl <= 0.003: continue
        items = list(zip(L['words'], L['wt']))
        nexts = [items[j + 1][1] for j in range(len(items) - 1)] + [L['e'] + 0.3]
        sp = C.text_w(" ", S.F_SANS, fs); rows = [[]]; cw = 0
        for j, (w_, tt) in enumerate(items):
            ww = C.text_w(w_, S.F_SANS, fs)
            if rows[-1] and cw + sp + ww > maxw: rows.append([]); cw = 0
            rows[-1].append((w_, tt, ww, nexts[j])); cw += ww + (sp if rows[-1] else 0)
        lh = fs * 1.32; y0 = ybase - (len(rows) - 1) * lh / 2 - lh * 0.25 * (1 - opl)
        for ri, row in enumerate(rows):
            x = (W - (sum(r[2] for r in row) + sp * (len(row) - 1))) / 2
            for w_, tt, ww, nt in row:
                kw = sstep(tt - 0.12, tt + 0.05, t)
                act = sstep(tt - 0.06, tt + 0.02, t) * (1 - sstep(nt - 0.06, nt + 0.04, t))
                yy = y0 + ri * lh
                if act > 0.02:
                    swipe = clamp((t - tt + 0.04) / 0.14)
                    m = np.zeros((int(fs * 1.25), int(ww + fs * 0.5)), np.float32)
                    cv2.rectangle(m, (0, int(fs * 0.12)), (int((ww + fs * 0.5) * swipe), int(fs * 1.13)), 1.0, -1)
                    m = cv2.GaussianBlur(m, (0, 0), 1.2) * (0.62 if dark < 0.5 else 0.9) * act * opl
                    X0 = int(x - fs * 0.25); Y0 = int(yy - fs * 0.05)
                    hh, ww2 = m.shape; X1, Y1 = min(W, X0 + ww2), min(H, Y0 + hh)
                    if X1 > max(0, X0) and Y1 > max(0, Y0):
                        mm = m[max(0, -Y0):Y1 - Y0, max(0, -X0):X1 - X0][..., None]
                        reg = img[max(0, Y0):Y1, max(0, X0):X1]; mc = C.hexc('f2a093') if dark < 0.5 else S.RED
                        reg *= (1 - mm); reg += mm * mc
                op = opl * (0.35 + 0.65 * kw)
                spr = C.sprite(w_, S.F_SANS, fs, 9)
                if dark > 0.05: C.shadow(img, spr, x, yy + 2 * k, 0.9 * op * dark)
                else:   # light background: a soft white halo instead of a shadow
                    a, g, pad = spr; X, Y = int(round(x - pad)), int(round(yy - pad)); h_, w2_ = g.shape
                    hx0, hy0, hx1, hy1 = max(0, X), max(0, Y), min(W, X + w2_), min(H, Y + h_)
                    if hx1 > hx0 and hy1 > hy0:
                        mm = np.clip(g[hy0 - Y:hy1 - Y, hx0 - X:hx1 - X] * 2.4, 0, 1)[..., None] * op * (1 - dark)
                        reg = img[hy0:hy1, hx0:hx1]; reg *= (1 - mm); reg += mm * S.WHITE
                C.blit(img, C.sprite(w_, S.F_SANS, fs, 0), x, yy, col, op)
                x += ww + sp

def TM_lines(): return S.TM.lines

# ---------------------------------------------------------------- all together
def overlays(img, t, z, W, H, th, st):
    sc = W / (1080 if H > W else 1920)
    clean = C.STATE["clean"]
    if C.STATE.get("bare"): return              # thumbnails: the world only
    map_labels(img, t, z, W, H, th, sc)
    space_labels(img, t, z, W, H, sc)
    bridge_ring(img, t, z, W, H, th, sc)
    # "Ted." — the zoom stops dead at the edge of the solar system
    kt = sstep(S.T_TED - 0.05, S.T_TED + 0.12, t) * (1 - sstep(S.T_STANDUP + 0.05, S.T_STANDUP + 0.35, t))
    if kt > 0:
        label(img, "Ted.", W / 2, H * 0.42, S.F_SERIF, (300 if W > H else 260) * sc, S.WHITE, C.hexc('05070c'), kt, 'c', 'm')
    # Ted's own speech bubble: "so — stepping back."
    kb = sstep(S.T_SO - 0.05, S.T_SO + 0.12, t) * (1 - sstep(S.T_DIM + 0.6, S.T_DIM + 1.3, t))
    if kb > 0 and z < 2.2:
        v = map_view(t, z, W, H, th); p = v.to_px(S.ted_world(t)[None])[0] + np.array([0, -24 * sc])
        txt = "so —" if t < S.T_STEP - 0.05 else "so — stepping back."
        fs = 44 * sc; tw = C.text_w(txt, S.F_SANS, int(fs)); bw, bh = tw + 50 * sc, fs * 1.55
        bx = min(max(p[0] - bw / 2, 16 * sc), W - bw - 16 * sc); by = max(p[1] - 22 * sc - bh, 10 * sc)
        rrect(img, bx, by, bw, bh, 20 * sc, S.WHITE, kb, shadow=0.35)
        label(img, txt, bx + 25 * sc, by + bh / 2, S.F_SANS, fs, S.RED, None, kb, 'l', 'm')
    ted_marker(img, t, z, W, H, th, sc)
    question(img, t, z, W, H, th, sc)
    if not clean:
        ted_talk_labels(img, t, z, W, H, sc)
        # map chrome: on the map only; it steps aside for the subscribe pill (16:9)
        kchrome = float(sstep(6.4, 6.0, z))
        kp = 1 - sstep(S.T_PILL - 0.1, S.T_PILL + 0.3, t) * (1 - sstep(S.T_PILL + 4.6, S.T_PILL + 5.0, t)) if W > H else 1.0
        search_bar(img, t, z, W, H, sc, kchrome * kp)
        clock_chip(img, t, z, W, H, sc, kchrome * kp)
        compass(img, t, z, W, H, th, sc, kchrome)
        scale_bar(img, t, z, W, H, sc, 1.0 - sstep(S.T_END - 0.3, S.T_END + 0.3, t))
        lyrics(img, t, W, H)
        C.subscribe_pill(img, t, W, H, S.T_PILL, 5.0)
        C.end_screen(img, t, W, H, S.T_END, S.DUR - S.T_END, "It's always a Ted talk.", sub_line="Subscribe for a new song every week",
                     title="TED Talk, stepping back", accent=S.RED)

def finish(img, t, fi):
    H, W = img.shape[:2]; p = C.post(W, H)
    img += cv2.resize(p.grain[fi % 6], (W, H), interpolation=cv2.INTER_NEAREST)[..., None] * 0.010
    img *= (1 - sstep(S.DUR - 1.0, S.DUR - 0.05, t))
    return (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)
