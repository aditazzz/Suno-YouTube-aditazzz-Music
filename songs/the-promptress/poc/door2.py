"""Door v2: a moon-door as a physical, impossible opening (not a screen).
- the world inside has depth: it grows slower than the rim as you approach and slides against it as you move (parallax)
- the rim has thickness (a dark stone lip, a lit inner wall on the far side) and a thin bright meniscus
- it lights our world: a pool of light on the ground, a wet reflection, a glow in the air
- her clouds pour out over the lip and roll across the plain (crossing the boundary)
- the picture is her photo_08 (moon in lit clouds); the moon can be lifted out, and the clouds lose its light"""
import math, numpy as np, cv2
import wkit as K
W, H = K.W, K.H
_p08 = cv2.imread(f"{K.AS}/photo_08.png").astype(np.float32) / 255
MOON08 = (451.3, 497.5, 59.0)
_cl = None
DRAIN = 1          # 1: round 3 relight; 2: V4 (the clouds lose their silver: darker, colder, flatter)
MENISCUS = 0.35; HALO = 0.20; HOLEFILL = "inpaint"

_pc = {}
def _base(size, moon_left):
    key = (size // 6 * 6, int(round(moon_left)))
    if key in _pc: return _pc[key]
    size = key[0]; h, w = _p08.shape[:2]; s = size / w
    pic = cv2.resize(_p08, (size, int(h * s) + 1), interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC)
    yo = int(size * 0.02); pic = pic[yo:yo + size]
    mx, my, mr = MOON08[0] * s, MOON08[1] * s - yo, MOON08[2] * s
    pic = np.clip(pic * 1.12 + 0.02, 0, 1) ** 0.9
    pic = pic * 0.55 + pic.mean(2, keepdims=True) * np.array([0.92, 0.98, 1.04], np.float32) * 0.45
    yy, xx = np.ogrid[0:size, 0:size]; d = np.sqrt((xx - mx) ** 2 + (yy - my) ** 2) / max(mr, 1e-3)
    if key[1] == 0:
        # what was behind the moon: the clouds, filled in from around it (and darker: its light is gone)
        sc = 2; sm = cv2.resize(pic, (size // sc, size // sc), interpolation=cv2.INTER_AREA)
        mk = np.zeros(sm.shape[:2], np.uint8); cv2.circle(mk, (int(mx / sc), int(my / sc)), int(mr * 1.25 / sc), 255, -1)
        fill = cv2.inpaint(np.clip(sm * 255, 0, 255).astype(np.uint8), mk, max(3, int(mr / sc * 0.6)), cv2.INPAINT_TELEA).astype(np.float32) / 255
        fill = cv2.resize(fill, (size, size), interpolation=cv2.INTER_CUBIC)
        if HOLEFILL == "patch":   # V4: real cloud from elsewhere in her photo, matched to the light around the hole
            dx, dy = int(mr * 2.8), int(-mr * 0.5)
            src = np.roll(np.roll(pic, -dy, 0), -dx, 1)
            ringm = ((d > 1.35) & (d < 2.2))[..., None]
            m_loc = (pic * ringm).sum((0, 1)) / max(ringm.sum(), 1); m_src = (src * ringm).sum((0, 1)) / max(ringm.sum(), 1)
            fill = np.clip(src * (m_loc / np.maximum(m_src, 1e-3)), 0, 1) * 0.5 + fill * 0.5 / 0.92
        hole = np.clip((1.30 - d) / 0.30, 0, 1)[..., None]
        pic = pic * (1 - hole) + fill * 0.92 * hole
    lit = np.exp(-(d / 4.5) ** 2)[..., None].astype(np.float32)
    if len(_pc) > 6: _pc.pop(next(iter(_pc)))
    _pc[key] = (pic.astype(np.float32), (mx, my), mr, lit)
    return _pc[key]

def picture(size, moon_left=1.0, relight=1.0):
    """her photo as the door's world, square. moon_left 1 = moon there, 0 = lifted out. relight 0..1: how much of
    the moon's light the clouds still have (they go dark when it leaves). -> (img, moon centre, moon radius)"""
    pic, mc, mr, lit = _base(size, moon_left)
    if relight < 1 and DRAIN == 2:
        k = 1 - relight; g = pic.mean(2, keepdims=True)
        pic = pic * (1 - 0.65 * k) + g * np.array([0.80, 0.88, 1.02], np.float32) * 0.65 * k
        pic = pic * (1 - k * (0.62 * lit + 0.42))
    elif relight < 1: pic = pic * (1 - (1 - relight) * (0.55 * lit + 0.22))
    return pic, mc, mr

def _clouds():
    global _cl
    if _cl is None: _cl = K.cloud_tex("cloudframe_46")
    return _cl

def draw(img, cx, cy, r, t, depth=1.0, slide=(0.0, 0.0), moon_left=1.0, relight=1.0, ground_y=None, ellipse=1.0,
         thickness_side=-1.0, spill=1.0, fog=1.0, interior_scale=1.25, ripple=None):
    """draw the door at screen (cx, cy) radius r (ellipse: horizontal squash for oblique views). depth: how far the
    world inside is (1 = parallax as a distant world). slide: interior offset in px (camera moving sideways).
    ripple: (x, y, t0) a crossing point on the surface sending out rings. Returns (img, info dict)."""
    ys, xs = np.ogrid[0:H, 0:W]
    rx, ry = r * ellipse, r
    rr = np.sqrt(((xs - cx) / rx) ** 2 + ((ys - cy) / ry) ** 2)
    m = np.clip((1 - rr) * ry / 1.2 + 0.5, 0, 1).astype(np.float32)
    # --- the world inside: her photo, bigger than the opening, sliding against it ---
    size = int(2 * ry * interior_scale) + 4
    if size > 3 * W: size = 3 * W
    pic, (pmx, pmy), pmr = picture(size, moon_left, relight)
    sx_ = (2 * rx * interior_scale) / size
    ox = cx - size * sx_ / 2 + slide[0] + t * ry * 0.012; oy = cy - size / 2 + slide[1]
    M = np.float32([[sx_, 0, ox], [0, 1, oy]])
    inner = cv2.warpAffine(pic, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    if ripple is not None:
        px_, py_, age = ripple
        if 0 <= age < 1.6:
            dd = np.sqrt((xs - px_) ** 2 + (ys - py_) ** 2).astype(np.float32)
            wave = np.sin(dd / (ry * 0.045) - age * 14) * np.exp(-((dd - age * ry * 0.9) / (ry * 0.25)) ** 2) * (1 - age / 1.6)
            off = (wave * ry * 0.010).astype(np.float32)
            mapx = (xs + off * (xs - px_) / np.maximum(dd, 1)).astype(np.float32); mapy = (ys + off * (ys - py_) / np.maximum(dd, 1)).astype(np.float32)
            inner = cv2.remap(inner, np.broadcast_to(mapx, (H, W)).copy(), np.broadcast_to(mapy, (H, W)).copy(), cv2.INTER_LINEAR)
            inner = inner + (np.clip(wave, 0, 1) * 0.10)[..., None]
    moon_screen = (ox + pmx * sx_, oy + pmy, pmr)
    col = cv2.mean(pic)[:3]
    # --- light it throws into our world ---
    g = ground_y if ground_y is not None else cy + ry
    halo = np.exp(-np.clip(rr - 1, 0, None) / 0.35) * (rr > 0.99) * HALO
    img = img + halo[..., None] * np.array(col, np.float32) * 1.2 * spill
    pool = np.exp(-(((xs - cx) / (rx * 2.2)) ** 2 + ((ys - g - ry * 0.35) / (ry * 0.45)) ** 2)) * np.clip((ys - g + 2) / (ry * 0.15), 0, 1)
    img = img + pool[..., None] * np.array(col, np.float32) * 0.65 * spill * relight ** 0.5
    # wet reflection of the opening on the plain
    hh = int(min(ry * 0.9, H - g - 1)) if g < H - 2 else 0
    if hh > 4:
        g0 = int(g)
        src = (inner * m[..., None])[max(0, g0 - hh):g0][::-1]
        rf = cv2.GaussianBlur(src, (0, 0), 2.5, sigmaY=10)
        rip = (np.sin(np.arange(rf.shape[0])[:, None] * 0.35 + t * 3.0) * 3).astype(np.float32)
        rf = cv2.remap(rf, (np.arange(W)[None, :] + rip).astype(np.float32), np.repeat(np.arange(rf.shape[0], dtype=np.float32)[:, None], W, 1), cv2.INTER_LINEAR)
        fade = np.linspace(0.42, 0, rf.shape[0])[:, None, None]
        img[g0:g0 + rf.shape[0]] += rf * fade
    # contact shadow where it meets the ground
    cs = np.exp(-(((xs - cx) / (rx * 0.5)) ** 2 + ((ys - g) / (ry * 0.03 + 2)) ** 2))
    img = img * (1 - 0.5 * cs[..., None])
    # --- the opening: you look through a short tunnel; the far world is a little hazier than ours ---
    inner = inner * (1 - 0.45 * np.clip((rr - 0.72) / 0.28, 0, 1) ** 1.5)[..., None]
    inner = inner * 0.92 + np.array(col, np.float32) * 0.08
    img = img * (1 - m[..., None]) + inner * m[..., None]
    # rim: a dark lip, a lit inner wall on the far side (thickness), and a thin bright meniscus at the surface
    lip = np.exp(-((rr - 1.0) * ry / max(ry * 0.018, 1.5)) ** 2)
    img = img * (1 - 0.75 * lip[..., None])
    ang = np.arctan2((ys - cy) / ry, (xs - cx) / rx)
    side = np.clip(np.cos(ang - (0 if thickness_side > 0 else math.pi)), 0, 1)
    wall = np.clip(1 - np.abs(rr - 0.965) * ry / max(ry * 0.035, 1.5), 0, 1) * side ** 1.5 * (rr < 1.0)
    img = img * (1 - 0.5 * wall[..., None]) + wall[..., None] * np.array(col, np.float32) * 0.55
    men = np.exp(-((rr - 0.995) * ry / 1.3) ** 2)
    img = img + men[..., None] * np.array([0.80, 0.88, 0.95], np.float32) * MENISCUS
    # --- her clouds pour out over the lip and roll toward us across the plain ---
    if fog > 0:
        d = _clouds(); th, tw = d.shape
        band_y0 = g - ry * 0.10; band_h = ry * 0.55
        v = (ys - band_y0) / band_h
        uu = ((xs - cx) / (rx * 3.0) + 0.5 + t * 0.010) % 1 * tw
        vv = np.clip(v * 0.6 + 0.1 - t * 0.02, 0, 0.999) * (th - 1)
        dens = cv2.remap(d, np.ascontiguousarray(np.broadcast_to(uu, (H, W)), np.float32), np.ascontiguousarray(np.broadcast_to(vv, (H, W)), np.float32), cv2.INTER_LINEAR)
        shape = np.exp(-((xs - cx) / (rx * 1.6)) ** 2) * np.clip(1 - np.abs(v - 0.45) / 0.55, 0, 1) ** 1.3
        dens = np.clip((dens - 0.42) * 2.6, 0, 1)
        a = np.clip(dens * shape * 0.95 * fog, 0, 0.8)
        lit = np.array(col, np.float32) * (0.55 + 0.45 * relight)
        img = img * (1 - a[..., None]) + lit * 0.9 * a[..., None]
    return img, dict(m=m, rr=rr, moon=moon_screen, col=col)

def moon_home(cx, cy, r, t, slide=(0.0, 0.0), ellipse=1.0, interior_scale=1.25):
    """where draw() puts the picture's moon on screen (same maths), without drawing -> (x, y, radius)"""
    rx, ry = r * ellipse, r
    size = int(2 * ry * interior_scale) + 4
    if size > 3 * W: size = 3 * W
    _, (pmx, pmy), pmr, _ = _base(size, 1)
    sx_ = (2 * rx * interior_scale) / size
    ox = cx - size * sx_ / 2 + slide[0] + t * ry * 0.012; oy = cy - size / 2 + slide[1]
    return np.array([ox + pmx * sx_, oy + pmy]), pmr
