"""Close-ups: the electric bill, the river's edge, the cooling fans, the meter, the glass of water, the server racks.

Each returns a linear HDR image (H, W, 3) (and sometimes extra layers). They share the film finish with the rest.
"""
import math, os
from functools import lru_cache
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
import ys_eng as E
from ys_eng import F32, hexc, sample, fbm_tex, sstep, clamp, ease_io, ease_out
import ys_world as WD

FONTS = E.FONTS
def _font(name, size): return ImageFont.truetype(os.path.join(FONTS, name), int(size))

# ---------------------------------------------------------------- the electric bill
BILL_W, BILL_H = 1400, 1800
@lru_cache(2)
def bill_base():
    """the paper and its static print (greeked lines, rules, the header); 8-bit L, then float."""
    im = Image.new('L', (BILL_W, BILL_H), 0); d = ImageDraw.Draw(im)
    ink = 255
    d.text((110, 110), "WILLOW VALLEY ELECTRIC", font=_font('Inter-SemiBold.otf', 54), fill=ink)
    d.text((110, 182), "RESIDENTIAL SERVICE  ·  STATEMENT", font=_font('JBMono-400.ttf', 30), fill=int(ink * 0.7))
    d.line((110, 250, BILL_W - 110, 250), fill=ink, width=4)
    r = np.random.default_rng(4)
    y = 300
    for k in range(7):   # greeked account lines
        w1 = int(r.uniform(260, 520)); w2 = int(r.uniform(120, 300))
        d.rectangle((110, y, 110 + w1, y + 16), fill=int(ink * 0.45)); d.rectangle((BILL_W - 110 - w2, y, BILL_W - 110, y + 16), fill=int(ink * 0.45))
        y += 46
    d.text((110, 660), "USAGE HISTORY", font=_font('Inter-SemiBold.otf', 34), fill=int(ink * 0.85))
    d.line((110, 1310, BILL_W - 110, 1310), fill=int(ink * 0.8), width=3)       # chart baseline
    for k in range(13):
        d.text((150 + k * 87, 1325), "JFMAMJJASONDJ"[k], font=_font('JBMono-400.ttf', 26), fill=int(ink * 0.55))
    d.line((110, 1430, BILL_W - 110, 1430), fill=ink, width=2)
    d.text((110, 1470), "AMOUNT DUE", font=_font('Inter-SemiBold.otf', 46), fill=ink)
    y = 1580
    for k in range(3):
        d.rectangle((110, y, 110 + int(r.uniform(400, 700)), y + 14), fill=int(ink * 0.4)); y += 40
    a = np.asarray(im, F32) / 255
    paper = (0.78 + 0.22 * cv2.resize(fbm_tex(256, 1.1, 91), (BILL_W, BILL_H)))
    fibers = cv2.resize(fbm_tex(512, 0.8, 92), (BILL_W, BILL_H))
    paper = paper * (0.94 + 0.06 * fibers)
    return a, paper.astype(F32)

def bill_texture(t, bars, amount, hit=0.0, red_line=True):
    """bars: list of heights 0..1 (13 months; the last may exceed the red line), amount: text, hit: 0..1 flash."""
    a, paper = bill_base()
    im = Image.new('L', (BILL_W, BILL_H), 0); d = ImageDraw.Draw(im)
    redm = Image.new('L', (BILL_W, BILL_H), 0); dr = ImageDraw.Draw(redm)
    top, base = 760, 1300
    if red_line:
        yl = int(base - (base - top) * 0.92)
        for x in range(110, BILL_W - 110, 36): dr.line((x, yl, x + 20, yl), fill=255, width=4)
        dr.text((BILL_W - 330, yl - 46), "YOUR LIMIT", font=_font('JBMono-700.ttf', 30), fill=255)
    for k, hgt in enumerate(bars):
        if hgt <= 0: continue
        x0 = 128 + k * 87; x1 = x0 + 52
        y0 = int(base - (base - top) * min(1.0, hgt))
        if y0 >= base - 3: continue
        tgt = dr if hgt >= 0.92 else d
        tgt.rectangle((x0, y0, x1, base - 2), fill=255)
    d.text((110, 1520), amount, font=_font('PlayfairDisplaySC-Regular.ttf', 0 + 80), fill=255) if False else None
    dr.text((BILL_W - 110 - _font('Inter-SemiBold.otf', 72).getlength(amount), 1458), amount, font=_font('Inter-SemiBold.otf', 72), fill=255)
    ink = np.maximum(a, np.asarray(im, F32) / 255)
    red = np.asarray(redm, F32) / 255
    col = paper[..., None] * hexc('e4dccb')[None, None]
    col = col * (1 - ink[..., None] * 0.92) + hexc('1a1a1c')[None, None] * ink[..., None] * 0.92 * 0.05
    col = col * (1 - red[..., None]) + (hexc('b3182f') * (1 + hit * 1.5))[None, None] * red[..., None] * paper[..., None]
    return col.astype(F32), red

def draw_bill(W, H, t, S):
    """the bill on the nightstand in the light through the blinds. S: bars, amount, hit, push (0..1), lamp (0..1)."""
    tex, red = bill_texture(t, S['bars'], S['amount'], S.get('hit', 0.0))
    # the paper lies flat; the camera looks down at it at ~50 degrees, slowly pushing in
    push = float(S.get('push', 0.0)); ta = float(S.get('to_amount', 0.0))
    ang0 = math.radians(-9)
    ax_, az_ = 0.025, -0.094                                             # AMOUNT DUE line on the sheet (before its -9 deg turn)
    amt_p = np.array([ax_ * math.cos(ang0) - az_ * math.sin(ang0), 0.0, ax_ * math.sin(ang0) + az_ * math.cos(ang0)], F32)
    vert = W < H; VZ = 1.5                                               # 9:16: the sheet 1/1.5 the size, so it fits the width
    eye = np.array([0.06 + 0.02 * push, 0.34 - 0.07 * push, -0.30 + 0.07 * push], F32)
    tgt = np.array([0.0, 0.0, 0.02 - 0.03 * push], F32)
    tc = ta * (0.6 if vert else 1.0)                                     # 9:16: a shorter move to the amount (the whole sheet stays in)
    if tc > 0:
        e2 = amt_p + np.array([0.01, 0.15, -0.13], F32) * (1.25 if vert else 1.0)
        eye = eye * (1 - tc) + e2 * tc; tgt = tgt * (1 - tc) + amt_p * tc
    fov = 40 - 6 * push - 6 * tc
    if vert: fov = math.degrees(2 * math.atan(math.tan(math.radians(fov) / 2) * VZ))
    cam = E.Cam(eye, tgt, fov=fov, W=W, H=H, drift=0.0015, t=t, seed=3)
    cv = E.Canvas(cam)
    # wood surface
    def wood(X, Y, Z, m):
        P = WD._world_from_screen(cam, X, Y, Z)
        g = sample(fbm_tex(256, 1.2, 93), P[..., 0] * 400, P[..., 2] * 25, 1.0)
        rings = 0.85 + 0.15 * np.sin(P[..., 2] * 220 + g * 9)
        st = stripe(P)
        lit = hexc('b9d4e6') * (0.03 + 0.20 * st)[..., None] + hexc('ffb46a') * float(S.get('lamp', 0.0)) * 0.05
        return (hexc('3a2a1e') * rings[..., None] * (0.8 + 0.4 * g[..., None])) * lit
    def stripe(P):
        # blinds' stripes cross the nightstand diagonally (same blinds as the room)
        q = (P[..., 0] * 0.45 + P[..., 2] * 0.9) / 0.024
        ph = q % 1.0
        return E.ss_arr(0.42, 0.50, ph) * (1 - E.ss_arr(0.86, 0.94, ph)) * (0.6 + 0.4 * float(S.get('breath', 0.5)))
    cv.poly(np.array([[-0.6, 0, 0.6], [0.6, 0, 0.6], [0.6, 0, -0.6], [-0.6, 0, -0.6]], F32), wood)
    # the bill: a 0.216 x 0.279 m sheet, a little rotated, mapped from the texture
    ang = math.radians(-9)
    c, s_ = math.cos(ang), math.sin(ang)
    hw, hd = 0.108, 0.1395
    corners = np.array([[-hw, 0.0005, hd], [hw, 0.0005, hd], [hw, 0.0005, -hd], [-hw, 0.0005, -hd]], F32)
    corners = np.stack([corners[:, 0] * c - corners[:, 2] * s_, corners[:, 1], corners[:, 0] * s_ + corners[:, 2] * c], 1)
    x, y, z = cam.project(corners)
    quad = np.stack([x, y], 1).astype(F32)
    src = np.float32([[0, 0], [BILL_W - 1, 0], [BILL_W - 1, BILL_H - 1], [0, BILL_H - 1]])
    M = cv2.getPerspectiveTransform(src, quad)
    warped = cv2.warpPerspective(tex, M, (W, H), flags=cv2.INTER_AREA, borderMode=cv2.BORDER_CONSTANT)
    mask = cv2.warpPerspective(np.ones((BILL_H, BILL_W), F32), M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    redw = cv2.warpPerspective(red, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    # light on the paper: stripes + a little lamp
    D, k = cam.dirs()
    tt = np.where(D[..., 1] < -1e-4, -cam.eye[1] / D[..., 1], 0)
    P = cam.eye[None, None] + D * tt[..., None]
    st = stripe(P)
    light = hexc('b9d4e6') * (0.42 + 0.30 * st)[..., None] + hexc('ffb46a') * float(S.get('lamp', 0.0)) * 0.3
    paper = warped * light
    paper += hexc('ff2a40') * (redw * float(S.get('hit', 0.0)) * 0.35)[..., None]
    m3 = mask[..., None]
    cv.img = cv.img * (1 - m3) + paper * m3
    # soft shadow of the sheet's edge, and depth of field (focus across the middle of the page)
    yy = np.linspace(0, 1, H, dtype=F32)[:, None]
    if vert:   # the same depth of field on the smaller sheet: focus at the lens centre, gradient and radii scaled with it
        c = cam.cy / H
        focus = (c + 0.006) * (1 - ta) + c * ta
        blur_k = np.clip(np.abs(yy - focus) * 2.2 * VZ * H / E.sref(W, H), 0, 1); rk = 1 / VZ
    else:
        focus = float(S.get('focus', 0.55)) * (1 - ta) + 0.5 * ta
        blur_k = np.clip(np.abs(yy - focus) * 2.2, 0, 1); rk = 1.0
    b1 = cv2.GaussianBlur(cv.img, (0, 0), 3.5 * rk * E.pxs(W, H)); b2 = cv2.GaussianBlur(cv.img, (0, 0), 9.0 * rk * E.pxs(W, H))
    w1 = np.clip(blur_k * 2, 0, 1)[..., None]; w2 = np.clip(blur_k * 2 - 1, 0, 1)[..., None]
    img = cv.img * (1 - w1) + b1 * w1
    img = img * (1 - w2) + b2 * w2
    return img

# ---------------------------------------------------------------- the river's edge (low, at the waterline)
@lru_cache(1)
def _rocks():
    r = np.random.default_rng(12)
    rocks = []
    for k in range(9):
        rocks.append(dict(x=r.uniform(-1.6, 2.2), z=r.uniform(1.4, 6.5), rx=r.uniform(0.08, 0.28), ry=r.uniform(0.05, 0.16), seed=int(r.integers(0, 999))))
    rocks.sort(key=lambda d: -d['z'])
    return rocks

def draw_river_edge(W, H, t, S, VS):
    """camera a hand above the water near the bank, rocks breaking the surface, the facility far across, its lights
    on the water. VS: valley state (water level etc). S: drop (0..1 how far the level has fallen in this shot)."""
    base = np.array([-520.0, 0.0, 0.0], F32)
    zc = float(WD.river_zc(base[0]))
    h0 = float(VS['water'])
    eye = np.array([base[0] + 0.0, h0 + 0.22, zc - 10.0], F32)
    tgt = np.array([base[0] - 120.0, h0 + 6.0, 260.0], F32)
    cam = E.Cam(eye, tgt, fov=float(S.get('fov', 30)), W=W, H=H, drift=0.01, t=t, seed=21)
    rocks = _rocks()
    fwd = E.nrm((tgt - eye) * np.array([1, 0, 1], F32)); right = np.array([fwd[2], 0, -fwd[0]], F32)
    def extra(cv):
        for rk in rocks:
            P0 = eye + fwd * rk['z'] + right * rk['x']
            draw_rock(cv, P0, rk, VS, t)
    cvv = WD.render(cam, VS, t, reflections=True, refl_scale=0.5, extra=extra)
    return WD.compose(cvv)

def draw_rock(cv, P0, rk, VS, t):
    """a rounded wet stone sitting in the river: a lumpy ellipse in screen space, shaded with noise normals, darker
    and glossy in the band just above the waterline (freshly exposed as the water drops)."""
    cam = cv.cam
    h = float(VS['water']); drop = float(VS.get('drop', 0.0))
    bottom_y = h - 0.4
    top_y = h + rk['ry'] * (0.8 + 0.6 * drop)
    Pc = np.array([P0[0], (bottom_y + top_y) / 2, P0[2]], F32)
    x, y, z = cam.project(np.array([[P0[0], top_y, P0[2]], [P0[0], h, P0[2]], Pc], F32))
    if z[2] < 0.3: return
    s = cam.fpx / z[2]
    rx = rk['rx'] * s; ytop = y[0]; ywl = y[1]
    if rx < 1.0: return
    x0 = int(max(0, x[2] - rx * 1.3)); x1 = int(min(cv.W, x[2] + rx * 1.3)); y0 = int(max(0, ytop - 4)); y1 = int(min(cv.H, ywl + 2))
    if x1 <= x0 or y1 <= y0: return
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(F32)
    u = (xx - x[2]) / rx; v = (yy - ywl) / max(1.0, ywl - ytop)          # v: -1 at the top, 0 at the waterline
    rng = np.random.default_rng(rk['seed'])
    nz = sample(fbm_tex(256, 1.6, 95), xx * (8 / rx) + rk['seed'] * 13, yy * (8 / rx), 1.0)
    shape = 1 - u * u * (1.0 + 0.25 * (nz - 0.5)) - np.maximum(-v, 0) ** 2.2
    a = np.clip(shape * 6, 0, 1) * (v <= 0.02)
    if not a.any(): return
    # shading: fake normal from the shape gradient
    nx = -u; ny = np.clip(-v, 0, 1) * 1.4
    lit = np.clip(0.35 + 0.5 * ny - 0.2 * nx, 0, 1)
    wet = np.clip((v + 0.0) / -0.001, 0, 1) * 0 + np.clip(1 - (-v) / (0.25 + 0.7 * drop), 0, 1)   # near the waterline
    alb = hexc('3d3a36') * (0.7 + 0.5 * nz[..., None]) * (1 - wet[..., None] * 0.55)
    amb = WD.ambient_light(VS)
    col = alb * (amb * 2.5 + hexc('c8d8e8') * 0.02 * lit[..., None])
    spec = wet * np.clip(ny - 0.2, 0, 1) * 0.06 * (0.6 + 0.4 * nz)
    col = col + hexc('d6e4ee') * spec[..., None]
    reg = cv.img[y0:y1, x0:x1]; A = a[..., None]
    reg *= (1 - A); reg += col * A
    cv.emis[y0:y1, x0:x1] *= (1 - A)
    d = cv.dep[y0:y1, x0:x1]; d[a > 0.5] = z[2]

# ---------------------------------------------------------------- the roof: cooling fans like eyes
def draw_fans(W, H, t, S):
    """top-down over the facility roof: a grid of big fan units. S: zoom (1 = the grid, ~6 = one fan fills the frame),
    rot (radians, slow), cx, cy (roof coords of the frame centre, in fan pitches), speed (rev/s), glow, red (hub light),
    ripple (puddle ripples 0..1), breath."""
    zoom = float(S.get('zoom', 1.0)); rot = float(S.get('rot', 0.0)); spd = float(S.get('speed', 0.45))
    cx, cy = float(S.get('cx', 0.0)), float(S.get('cy', 0.0))
    pitch = E.sref(W, H) / 2.6 * zoom                  # px per fan pitch
    img = np.zeros((H, W, 3), F32); emis = np.zeros_like(img)
    yy, xx = np.mgrid[0:H, 0:W].astype(F32)
    X = (xx - W / 2) / pitch; Y = (yy - H / 2) / pitch
    c, s_ = math.cos(rot), math.sin(rot)
    U = X * c - Y * s_ + cx; V = X * s_ + Y * c + cy          # roof coords in pitches
    # roof membrane
    tex = sample(fbm_tex(512, 1.4, 96), U * 60, V * 60, 1.0)
    seams = np.exp(-((U * 4) % 1.0 - 0.5) ** 2 / 0.0004) * 0.0 + np.exp(-(((V * 2.0) % 1.0) - 0.5) ** 2 / 0.0003)
    roof = hexc('1c1e21') * (0.75 + 0.5 * tex[..., None]) * (1 - 0.3 * seams[..., None])
    breath = float(S.get('breath', 0.5)); glow = float(S.get('glow', 1.0))
    amb = hexc('0d1520') * 0.08
    img[:] = roof * (amb * 8)
    # puddles on the roof reflect the sky glow and the fans' light
    pud = sample(fbm_tex(512, 2.4, 97), U * 3.0 + 11, V * 3.0, 1.0)
    pm = E.ss_arr(0.60, 0.64, pud)
    # fan units at integer roof coords
    iu = np.round(U); iv = np.round(V)
    du = U - iu; dv = V - iv
    r = np.sqrt(du * du + dv * dv)
    ang = np.arctan2(dv, du)
    R_house = 0.40; R_blade = 0.36; R_hub = 0.07
    house = E.ss_arr(R_house + 0.012, R_house - 0.012, r) - E.ss_arr(R_house - 0.03 + 0.008, R_house - 0.03 - 0.008, r)
    inside = E.ss_arr(R_house - 0.03 + 0.006, R_house - 0.03 - 0.006, r)
    # each fan turns at its own phase; blades motion-blurred over a 180-degree shutter
    hsh = np.abs(np.modf(np.sin(iu * 12.9898 + iv * 78.233) * 43758.5453)[0])
    nbl = 7
    phase = t * spd * 2 * math.pi * (0.92 + 0.16 * hsh) + hsh * 6.28
    a_rel = (ang - phase) % (2 * math.pi / nbl)
    blade_w = 0.42 * (2 * math.pi / nbl) * (1 + 0.3 * (r / R_blade))      # blades widen toward the tip
    blur = spd * 2 * math.pi / 30 * 0.5 / (2 * math.pi / nbl)            # shutter smear as a fraction of the pitch
    edge = 0.06 + blur
    bl = E.ss_arr(0, edge, a_rel) * (1 - E.ss_arr(blade_w, blade_w + edge, a_rel))
    bl = bl * E.ss_arr(R_hub, R_hub + 0.02, r) * (1 - E.ss_arr(R_blade - 0.01, R_blade + 0.01, r))
    bl = bl * (1 - min(0.6, blur * 1.5))
    # the glow below the blades (the hall underneath), breathing with the building
    under = hexc('8fd0e0') * (0.06 + 0.40 * breath) * glow * np.clip(1 - r / R_house, 0, 1)[..., None] ** 1.8
    grille = (np.exp(-(((r * 26) % 1.0) - 0.5) ** 2 / 0.006) * 0.5 + np.exp(-(((ang / (2 * math.pi) * 24) % 1.0) - 0.5) ** 2 / 0.004) * 0.35) * inside
    fan_col = under * (1 - bl[..., None] * 0.92) * (1 - grille[..., None] * 0.7) + hexc('202328') * 0.012 * bl[..., None]
    hub = E.ss_arr(R_hub, R_hub - 0.01, r)
    led = E.ss_arr(0.016, 0.008, r)
    red = float(S.get('red', 0.0))
    fan_col = fan_col * (1 - hub[..., None]) + (hexc('141519') * 0.03) * hub[..., None]
    fan_col = fan_col * (1 - led[..., None]) + hexc('ff2236') * (red * 1.5) * led[..., None]
    rimc = hexc('3a4048') * 0.05 + hexc('cfe6f0') * 0.04 * glow * breath
    img = img * (1 - inside[..., None]) + fan_col * inside[..., None]
    img = img * (1 - house[..., None]) + rimc * house[..., None]
    emis += under * (1 - bl[..., None]) * inside[..., None] * 0.6
    emis += hexc('ff2236') * (red * 3.0 * led)[..., None]
    # puddles: mirror-ish, they hold a rippled copy of the glow
    rip = float(S.get('ripple', 0.0))
    if rip > 0 or True:
        dx = (sample(fbm_tex(256, 1.5, 98), U * 18 + t * 0.6, V * 18, 1.0) - 0.5) * (3 + 30 * rip)
        refl = cv2.remap((img + emis).astype(F32), (xx + dx).astype(F32), (yy + dx * 0.5).astype(F32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        refl = cv2.GaussianBlur(refl, (0, 0), 2.0)
        pmo = (pm * (1 - inside) * (1 - house))[..., None]
        img = img * (1 - pmo * 0.7) + (refl * 0.5 + hexc('0f1a26') * 0.01) * pmo
    return img + emis

# ---------------------------------------------------------------- the river's edge, close (stones at the waterline)
@lru_cache(1)
def _stones():
    r = np.random.default_rng(31)
    st = []
    for k in range(26):
        st.append(dict(lat=r.uniform(-0.2, 3.4), fw=r.uniform(-1.8, 1.8), a=r.uniform(0.05, 0.22), b=r.uniform(0.03, 0.09),
                       c=r.uniform(0.05, 0.2), yaw=r.uniform(0, math.pi), sink=r.uniform(0.25, 0.6), seed=int(r.integers(0, 9999))))
    for k in range(44):      # gravel and small cobbles between them
        sz = r.uniform(0.015, 0.06)
        st.append(dict(lat=r.uniform(-0.3, 3.6), fw=r.uniform(-2.0, 2.0), a=sz * r.uniform(0.8, 1.4), b=sz * r.uniform(0.4, 0.7),
                       c=sz * r.uniform(0.8, 1.3), yaw=r.uniform(0, math.pi), sink=r.uniform(0.2, 0.5), seed=int(r.integers(0, 9999))))
    return st

def river_close_cam(W, H, t, VS, x=-520.0, push=0.0):
    zc = float(WD.river_zc(x)); h = float(VS['water'])
    # stand on the near bank slope, just above the water, looking along the waterline toward the facility
    dbank = RIVER_EDGE_D(h)
    eye = np.array([x + 1.2 - 0.4 * push, h + 0.55 - 0.08 * push, zc - dbank - 1.8 + 0.5 * push], F32)
    hd = E.nrm(np.array([-60.0, 0, 160.0 + dbank], F32))
    tgt = eye + hd * 10.0 + np.array([0, -1.55, 0], F32)
    return E.Cam(eye, tgt, fov=38, W=W, H=H, drift=0.006, t=t, seed=23)

def RIVER_EDGE_D(h):
    """lateral distance from the centreline at which the bed meets water level h (nearly: ignoring bed noise)."""
    return WD.RIVER_W - (-h) / WD.RIVER_D * (WD.RIVER_W - WD.RIVER_BED_W)

def draw_river_close(W, H, t, S, VS, x=-520.0):
    """stones and mud at the waterline in the foreground (sharp), the river and the facility behind (soft).
    The waterline slips back across the stones as VS['water'] drops; freshly exposed stone stays dark and wet."""
    cam = river_close_cam(W, H, t, VS, x, float(S.get('push', 0.0)))
    h = float(VS['water']); h_hi = float(S.get('water_hi', h))      # where the water was a moment ago (wet line)
    stones = _stones()
    zc = float(WD.river_zc(x)); dE = RIVER_EDGE_D(h)
    def extra(cv):
        # stones along the near edge: placed on the bank slope at lateral distance `lat` from today's waterline
        for s_ in stones:
            lat = dE + s_['lat'] * 0.6 - 0.6
            P = np.array([x + s_['fw'] * 1.6, 0, zc - lat], F32)
            bed = float(-WD.RIVER_D * np.clip((WD.RIVER_W - lat) / (WD.RIVER_W - WD.RIVER_BED_W), 0, 1))
            P[1] = bed + s_['b'] * (1 - s_['sink'])
            stone(cv, P, s_, h, h_hi, VS, t)
    cvv = WD.render(cam, VS, t, reflections=True, refl_scale=0.5, extra=extra, town_on=False)
    img = WD.compose(cvv)
    # depth of field: focus on the stones (2-4 m); the far bank and the facility go soft
    z = cvv.dep
    near = 4.5
    k = np.clip((np.log(np.maximum(z, 0.3)) - math.log(near)) / 2.2, 0, 1)
    b1 = cv2.GaussianBlur(img, (0, 0), 2.5 * E.pxs(W, H)); b2 = cv2.GaussianBlur(img, (0, 0), 7.0 * E.pxs(W, H))
    w1 = np.clip(k * 2, 0, 1)[..., None]; w2 = np.clip(k * 2 - 1, 0, 1)[..., None]
    img = img * (1 - w1) + b1 * w1
    img = img * (1 - w2) + b2 * w2
    return img

def stone(cv, C, s_, h, h_hi, VS, t):
    """ray-traced ellipsoid stone (only what is above the water), wet and glossy below the recent waterline."""
    cam = cv.cam
    a, b, c = s_['a'], s_['b'], s_['c']; yaw = s_['yaw']
    cy, sy = math.cos(yaw), math.sin(yaw)
    Rm = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]], F32)
    # screen bbox from the 8 box corners
    corners = np.array([[i * a, j * b, k * c] for i in (-1, 1) for j in (-1, 1) for k in (-1, 1)], F32) @ Rm.T + C
    x, y, z = cam.project(corners)
    if (z < 0.2).any(): return
    x0 = int(max(0, x.min() - 2)); x1 = int(min(cv.W, x.max() + 3)); y0 = int(max(0, y.min() - 2)); y1 = int(min(cv.H, y.max() + 3))
    if x1 - x0 < 2 or y1 - y0 < 2: return
    D, kk = cam.dirs()
    Dd = D[y0:y1, x0:x1]
    # into the stone's frame (scaled to a unit sphere)
    O = (cam.eye - C) @ Rm; Dl = Dd @ Rm
    sc = np.array([1 / a, 1 / b, 1 / c], F32)
    o = O * sc; d = Dl * sc
    A = (d * d).sum(-1); B = 2 * (d * o).sum(-1); Cq = float((o * o).sum()) - 1
    disc = B * B - 4 * A * Cq
    hit = disc > 0
    if not hit.any(): return
    tt = (-B - np.sqrt(np.maximum(disc, 0))) / (2 * A)
    P = cam.eye[None, None] + Dd * tt[..., None]
    above = P[..., 1] > h
    m = hit & (tt > 0) & above
    if not m.any(): return
    zv = (P - cam.eye) @ cam.f
    m &= cv.dep[y0:y1, x0:x1] > zv
    if not m.any(): return
    Pl = (P - C) @ Rm
    nl = Pl * (sc * sc); nw = nl @ Rm.T; nw /= np.linalg.norm(nw, axis=-1, keepdims=True) + 1e-9
    bump = sample(fbm_tex(256, 1.3, 99 + s_['seed'] % 3), Pl[..., 0] * 60 + s_['seed'], Pl[..., 2] * 60 + Pl[..., 1] * 40, 1.0)
    fine = sample(fbm_tex(256, 0.5, 97), Pl[..., 0] * 400 + s_['seed'] * 3, Pl[..., 2] * 400 + Pl[..., 1] * 300, 1.0)
    alb = hexc('6a655d') * (0.55 + 0.55 * bump[..., None]) * (0.85 + 0.3 * fine[..., None])
    wet = np.clip((h_hi + 0.03 - P[..., 1]) / 0.05, 0, 1)              # below the recent waterline: still wet
    alb = alb * (1 - 0.65 * wet[..., None])
    Lf = E.nrm([-0.45, 0.35, 0.82])                                     # toward the facility's glow
    ndl = np.clip((nw * Lf).sum(-1), 0, 1)
    up = np.clip(nw[..., 1], 0, 1)
    amb = WD.ambient_light(VS)
    col = alb * (amb * (3.0 + 4.0 * up[..., None]) + hexc('cfe2ee') * (0.22 * ndl)[..., None])
    # wet specular: the facility light glancing off
    V = -Dd; Hh = V + Lf; Hh /= np.linalg.norm(Hh, axis=-1, keepdims=True) + 1e-9
    spec = np.clip((nw * Hh).sum(-1), 0, 1) ** 28 * (0.04 + 0.8 * wet) * np.clip(fine * 1.8 - 0.4, 0, 1.2)   # rough: the sheen breaks up
    col = col + hexc('e8f2f8') * (spec * 0.5)[..., None]
    reg = cv.img[y0:y1, x0:x1]; mm = m.astype(F32)
    # soften the silhouette by one pixel
    mm = cv2.GaussianBlur(mm, (0, 0), 0.6) * m + mm * (1 - m) * 0
    reg[m] = col[m]
    cv.emis[y0:y1, x0:x1][m] = 0
    cv.dep[y0:y1, x0:x1][m] = zv[m]

# ---------------------------------------------------------------- the glass of water (it drains by itself)
@lru_cache(4)
def _glass_bg(W, H, seed=0):
    """the bedroom window behind the glass, very soft: bokeh of the facility's lights between the slats."""
    import ys_rooms as RM
    cam = RM.bedroom_cam(W // 3, H // 3, u=1.32, v=0.78, w=-0.95, tu=-0.2, tv=1.45, fov=34)
    cv = RM.draw_bedroom(W // 3, H // 3, dict(lamp=0.0, window_light=1.0, blind_open=0.6, breath=0.7), 70.0, cam=cam, her=False,
                         exterior_scale=1.0, valley_S=dict(breath=0.8, stars=0.3, water=-1.0))
    img = cv.img + cv.emis
    img = cv2.GaussianBlur(cv2.resize(img, (W, H), interpolation=cv2.INTER_LINEAR), (0, 0), 7.0 * E.pxs(W, H))
    return img.astype(F32)

def draw_glass(W, H, t, S):
    """S: level (0..1 of the glass), wob (surface trembling 0..1), lamp, push."""
    bg = _glass_bg(W, H).copy() * 1.6
    yy0, xx0 = np.mgrid[0:H, 0:W].astype(F32)
    # bokeh: the facility's lights between the slats, big soft discs
    rng = np.random.default_rng(7)
    for k in range(14):
        bx, by = rng.uniform(0.45, 1.0) * W, rng.uniform(0.05, 0.62) * H; br = rng.uniform(18, 46) * E.pxs(W, H)
        E.soft_glow(bg, bx, by, br, hexc('cfe6f2') if rng.random() > 0.15 else hexc('ff3048'), 0.03 + 0.05 * rng.random())
    img = bg
    push = float(S.get('push', 0.0))
    s = E.sref(W, H) / 1080 * (1.25 + 0.1 * push) * (1.0 if W >= H else 1.15)
    cx, base_y = (W * 0.40, H * 0.93) if W >= H else (W * 0.45, H * 0.565)   # 9:16: the glass stands above the lyrics
    gw, gh = 300 * s, 600 * s
    ell = 0.17
    top_y = base_y - gw * ell * 0.3
    img[int(top_y):, :] = img[int(top_y):, :] * 0.25 + hexc('2c2119') * 0.01
    level = float(S.get('level', 0.8)); wob = float(S.get('wob', 0.0))
    yw = base_y - gh * level * 0.92 - 6 * s
    x0, x1 = int(max(0, cx - gw / 2 - 6)), int(min(W, cx + gw / 2 + 6)); y0, y1 = int(max(0, base_y - gh - gw * ell - 6)), int(min(H, base_y + gw * ell + 6))
    yy, xx = yy0[y0:y1, x0:x1], xx0[y0:y1, x0:x1]
    u = (xx - cx) / (gw / 2)
    inside = (np.abs(u) < 1) & (yy > base_y - gh) & (yy < base_y + gw * ell * np.sqrt(np.clip(1 - u * u, 0, 1)))
    surf = yw + np.sin(u * 6 + t * 10) * 3.0 * s * wob
    wat = inside & (yy > surf + gw * ell * np.sqrt(np.clip(1 - u * u, 0, 1)) * 0.0)
    # water: magnified, flipped background, teal and darker; brighter toward the bottom (light gathers)
    sx = (cx - (xx - cx) * 0.45).astype(F32); sy = (yy * 0.97 + H * 0.02).astype(F32)
    refr = cv2.remap(bg, np.clip(sx, 0, W - 1), np.clip(sy, 0, H - 1), cv2.INTER_LINEAR)
    reg = img[y0:y1, x0:x1]
    tint = hexc('8cc0cc') * 1.3
    reg[wat] = refr[wat] * tint + hexc('0a1a20') * 0.006
    air = inside & ~wat
    refr2 = cv2.remap(bg, (cx + (xx - cx) * 0.9).astype(F32), yy.astype(F32), cv2.INTER_LINEAR)
    reg[air] = reg[air] * 0.6 + refr2[air] * 0.45
    # glass thickness: bright, soft walls; a long window reflection; a darker band just under the surface
    du = 1 - np.abs(u)
    walls = (np.exp(-(du / 0.07) ** 2) * 0.9 + np.exp(-(du / 0.018) ** 2) * 1.8) * inside
    reg += walls[..., None] * hexc('dcebf5') * 0.10
    hlx = np.exp(-((u + 0.55) / 0.07) ** 2) * inside * (yy < base_y - gh * 0.08) * (yy > base_y - gh * 0.95)
    reg += (hlx * 0.20)[..., None] * hexc('eef6fc')
    under = wat & (yy < surf + 16 * s)
    reg[under] *= 0.7
    for (yc, a, w_) in ((float(np.mean(surf)), 1.0, 2.2), (base_y - gh, 0.9, 1.6), (base_y, 0.6, 2.4)):
        cv2.ellipse(img, (int(cx), int(yc)), (int(gw / 2), int(gw / 2 * ell)), 0, 0, 360, (hexc('dcebf5') * 0.16 * a).tolist(), max(1, int(w_ * s)), cv2.LINE_AA)
    # caustic on the nightstand
    E.soft_glow(img, cx + gw * 0.25, base_y + gw * ell * 0.6, gw * 0.35, hexc('9fd0dc'), 0.02 + 0.04 * level)
    if level < 0.25:
        k = (0.25 - level) / 0.25
        for j in range(3):
            ang = t * 6 + j * 2.1
            px = cx + math.cos(ang) * gw * 0.25 * (1 - k * 0.5); py = base_y - 14 * s - math.sin(ang) * gw * ell * 0.25
            cv2.circle(img, (int(px), int(py)), max(1, int(3 * s)), (hexc('dcebf5') * 0.12 * k).tolist(), -1, cv2.LINE_AA)
    return img

# ---------------------------------------------------------------- the electric meter (the disk spins up)
def draw_meter(W, H, t, S):
    """the analog meter on the side of her house, face-on and close. S: rate (disk turns per second), dials (kWh, a float
    that keeps counting), porch (warm light), push."""
    img = np.zeros((H, W, 3), F32)
    yy, xx = np.mgrid[0:H, 0:W].astype(F32)
    s = min(W, H) / 1080 * (1 + 0.15 * float(S.get('push', 0.0))) * (1.0 if W >= H else 0.86)
    # clapboard siding behind
    lap = 0.80 + 0.20 * (((yy / (78 * s)) % 1.0) ** 0.35)
    st = sample(fbm_tex(256, 1.4, 131), xx * 0.6, yy * 0.2, 1.0)
    pl = float(S.get('porch', 1.0))
    warm = np.exp(-((xx - W * 0.15) ** 2 + (yy + H * 0.2) ** 2) / (2 * (W * 0.6) ** 2))
    img[:] = (hexc('7f8386') * (lap * (0.85 + 0.25 * st))[..., None]) * (hexc('ffc27a') * (0.012 + 0.11 * pl * warm ** 1.6)[..., None] + hexc('9fb4c4') * 0.035)
    cx, cy = (W * 0.52, H * 0.50) if W >= H else (W * 0.46, H * 0.375)
    R = 330 * s
    # the socket ring and the glass dome
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / R
    ring = E.ss_arr(1.12, 1.10, d) * (1 - E.ss_arr(1.02, 1.0, d))
    face = E.ss_arr(1.0, 0.985, d)
    img = img * (1 - ring[..., None]) + hexc('7a8086') * (0.04 + 0.06 * pl) * ring[..., None]
    plate = hexc('d6d2c6') * (0.04 + 0.16 * pl * warm[..., None] + 0.03)
    img = img * (1 - face[..., None]) + plate * face[..., None]
    # five dials across the top
    kwh = float(S.get('dials', 4812.0))
    digits = [int(kwh // 10 ** (4 - k)) % 10 + (kwh % 10 ** (4 - k)) / 10 ** (4 - k) for k in range(5)]
    for k in range(5):
        dx = cx + (k - 2) * 108 * s; dy = cy - 120 * s
        cv2.circle(img, (int(dx), int(dy)), int(44 * s), (hexc('ece8de') * 0.18).tolist(), -1, cv2.LINE_AA)
        cv2.circle(img, (int(dx), int(dy)), int(44 * s), (hexc('1a1a1a') * 0.02).tolist(), max(1, int(2 * s)), cv2.LINE_AA)
        for j in range(10):
            a = j / 10 * 2 * math.pi * (1 if k % 2 == 0 else -1)
            cv2.line(img, (int(dx + math.sin(a) * 36 * s), int(dy - math.cos(a) * 36 * s)), (int(dx + math.sin(a) * 42 * s), int(dy - math.cos(a) * 42 * s)), (hexc('1a1a1a') * 0.02).tolist(), max(1, int(2 * s)), cv2.LINE_AA)
        a = digits[k] / 10 * 2 * math.pi * (1 if k % 2 == 0 else -1)
        cv2.line(img, (int(dx), int(dy)), (int(dx + math.sin(a) * 34 * s), int(dy - math.cos(a) * 34 * s)), (hexc('101010') * 0.02).tolist(), max(2, int(4 * s)), cv2.LINE_AA)
    # the disk: a thin horizontal aluminium edge with a black mark sweeping across it
    dyk = cy + 70 * s; dw = 230 * s
    rate = float(S.get('rate', 0.5)); ph = float(S.get('phase', t * rate))
    disk = (np.abs(yy - dyk) < 7 * s) & (np.abs(xx - cx) < dw)
    img[disk] = hexc('c8ccd0') * (0.10 + 0.15 * pl)
    # mark position: projection of a point going round the disk
    blur = min(1.0, rate / 4.0)
    for j in range(6 if blur > 0.3 else 1):
        a = 2 * math.pi * (ph - j * min(0.08, rate / 30.0 / 6))
        mx = cx + math.cos(a) * dw * 0.97
        if math.sin(a) < 0: continue           # behind the disk's edge
        w_ = max(2, int(10 * s * (0.4 + 0.6 * abs(math.sin(a)))))
        op = (1.0 if j == 0 else 0.5 / j) * (1 - blur * 0.6)
        cv2.rectangle(img, (int(mx - w_ / 2), int(dyk - 7 * s)), (int(mx + w_ / 2), int(dyk + 7 * s)), (hexc('0a0a0a') * 0.01 * op + hexc('c8ccd0') * 0.1 * (1 - op)).tolist(), -1)
    # nameplate text (tiny, texture only) and "kWh"
    lab = TY_glyph("kWh", 46 * s)
    if lab is not None:
        m = lab; hm, wm = m.shape; X0 = int(cx - wm / 2); Y0 = int(cy + 130 * s)
        img[Y0:Y0 + hm, X0:X0 + wm] = img[Y0:Y0 + hm, X0:X0 + wm] * (1 - m[..., None] * 0.9) + hexc('1a1a1a') * 0.01 * m[..., None]
    # dome highlights: a curved window reflection and a rim glint
    hl = np.exp(-((d - 0.82) / 0.05) ** 2) * np.clip(np.cos(np.arctan2(yy - cy, xx - cx) + 2.4), 0, 1) ** 3 * face
    img += (hl * 0.25)[..., None] * hexc('e8f0f8') * (0.3 + 0.5 * pl)
    img += (np.exp(-((d - 0.99) / 0.01) ** 2) * 0.10)[..., None] * hexc('ffd8a8') * pl
    # slight DOF falloff toward the frame edges
    rr = np.sqrt(((xx - cx) / W) ** 2 + ((yy - cy) / H) ** 2)
    bl = cv2.GaussianBlur(img, (0, 0), 6 * E.pxs(W, H))
    k = np.clip((rr - 0.3) * 3, 0, 1)[..., None]
    return img * (1 - k) + bl * k

def TY_glyph(text, size):
    import ys_type as TY
    m, ox, oy = TY.glyphs(text, TY.F_SANS, int(size))
    return m

# ---------------------------------------------------------------- the intake pipe (the facility drinking the river)
def draw_pipe(W, H, t, S):
    """a concrete headwall on the far bank with a big intake mouth behind a steel grate; the river runs into it.
    S: flow (0..1 how hard it drinks), breath, push."""
    flow = float(S.get('flow', 0.5)); push = float(S.get('push', 0.0))
    img = np.zeros((H, W, 3), F32)
    yy, xx = np.mgrid[0:H, 0:W].astype(F32)
    s = E.sref(W, H) / 804 * (1 + 0.1 * push)
    cx, cy = (W * 0.55 if W >= H else W * 0.47), H * 0.40 + 10 * s * push
    R = E.sref(W, H) * (0.30 if W >= H else 0.42) * (1 + 0.1 * push)
    wl = H * 0.58                                   # waterline on the wall
    # concrete headwall: stained, lit from the upper left by a floodlight
    n1 = sample(fbm_tex(512, 1.5, 161), xx * 0.5, yy * 0.5, 1.0); n2 = sample(fbm_tex(256, 1.1, 162), xx * 2.0, yy * 0.15, 1.0)
    alb = hexc('6a6a66') * (0.6 + 0.5 * n1[..., None]) * (0.85 + 0.25 * n2[..., None])
    flood = np.exp(-(((xx - W * 0.15) / (W * 0.7)) ** 2 + ((yy + H * 0.3) / (H * 1.1)) ** 2))
    stain = np.clip(1 - (wl - yy) / (H * 0.12), 0, 1) * (yy < wl)     # dark wet band above the waterline
    img[:] = alb * (hexc('cfe2ee') * (0.03 + 0.55 * flood)[..., None]) * (1 - 0.6 * stain[..., None])
    # the pipe mouth: dark, a ring of concrete lip, a grate of bars
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    lip = E.ss_arr(R * 1.12, R * 1.08, d) * (1 - E.ss_arr(R * 1.0, R * 0.98, d))
    mouth = E.ss_arr(R, R * 0.985, d)
    depthg = np.clip(1 - d / R, 0, 1)
    inner = hexc('05070a') * 0.004 * (1 + depthg[..., None])
    img = img * (1 - lip[..., None] * 0.4) + hexc('8a8a84') * 0.05 * lip[..., None]
    img = img * (1 - mouth[..., None]) + inner * mouth[..., None]
    bars = (np.abs(((xx - cx) % (R * 0.22)) - R * 0.11) < R * 0.022) & (mouth > 0.5)
    img[bars] = hexc('2a2c30') * 0.04 + hexc('cfe2ee') * 0.03
    # water: everything below the waterline, flowing into the mouth (radial drift + a slow swirl)
    wat = yy > wl
    rx = (xx - cx) / W; ry = (yy - wl) / H
    r_ = np.sqrt(rx * rx + ry * ry) + 1e-4; th = np.arctan2(ry, rx)
    adv = t * (0.04 + 0.22 * flow)
    q1 = sample(fbm_tex(256, 1.6, 163), (r_ + adv) * 900, th * 60 + t * 2 * flow, 1.0)
    q2 = sample(fbm_tex(256, 1.3, 164), (r_ + adv * 1.7) * 2000, th * 140, 1.0)
    ripple = (q1 - 0.5) * 0.7 + (q2 - 0.5) * 0.3
    # reflection of the wall (flipped about the waterline), distorted by the ripples, darker
    sy = (2 * wl - yy + ripple * H * 0.05).astype(F32); sx = (xx + ripple * W * 0.02).astype(F32)
    refl = cv2.remap(img, sx, np.clip(sy, 0, H - 1), cv2.INTER_LINEAR)
    fres = np.clip(0.25 + (1 - (yy - wl) / (H - wl)) * 0.6, 0, 1)[..., None]
    water = refl * fres * 0.8 + hexc('061216') * 0.006
    # the facility's lights streaking on the water, broken by the flow
    for k, fx in enumerate((0.12, 0.3, 0.8, 0.93)):
        x0 = W * fx; streak = np.exp(-((xx - x0 - ripple * W * 0.05) / (W * 0.0025)) ** 2) * np.clip(1 - (yy - wl) / (H * 0.42), 0, 1)
        water += (streak * np.clip(ripple * 4 + 0.3, 0, 1))[..., None] * hexc('dbe8f2') * 0.35 * (0.6 + 0.4 * float(S.get('breath', 0.5)))
    # foam where it pours in
    foam = np.exp(-(((xx - cx) / (R * 0.9)) ** 2 + ((yy - wl) / (H * 0.03)) ** 2)) * np.clip(ripple * 3 + 0.4, 0, 1) * flow
    water += foam[..., None] * hexc('cfe2ee') * 0.30
    img = np.where(wat[..., None], water, img)
    return img
