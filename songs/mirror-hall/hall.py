"""Hall of Mirrors, the engine. A long dark hall lined on both walls with the cover's bulb-lit vanity mirror (cropped to
its frame), each one showing the face from the cover through a different funhouse distortion. At the far end of the
hall stands the cover itself. A perspective camera walks the hall.

World units: a wall mirror is 1 unit tall. x right, y up, +z behind the camera at the start (the hall runs toward -z).
Colour: linear float32 (HDR). Textures are sRGB uint8 RGBA (warped as bytes, linearised after the warp)."""
import os, sys, math
from functools import lru_cache
import numpy as np, cv2

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "mirror-vanity"))
import vanity as V                    # the cover as a photographic plate (built for version 1)
F32 = np.float32

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))

# ================================================================ the mirror texture (1x cover px)
FX0, FY0, FX1, FY1 = 190, 48, 1064, 1072          # the vanity frame with its bulbs
TW, TH = FX1 - FX0, FY1 - FY0                      # 874 x 1024
GX0, GY0, GX1, GY1 = 307 - FX0, 152 - FY0, 948 - FX0, 1012 - FY0
GW, GH = GX1 - GX0, GY1 - GY0                      # the glass: 641 x 860
MIR_H = 1.0; MIR_W = MIR_H * TW / TH

LUT = np.power(np.arange(256, dtype=np.float64) / 255.0, 2.2).astype(F32)
def to_u8(img): return (np.power(np.clip(img, 0, 1), 1 / 2.2) * 255 + 0.5).astype(np.uint8)

@lru_cache(1)
def cover_lin():
    return np.ascontiguousarray(V.assets()["l1"].astype(F32) * F32(1 / 65535.0))      # 1254^2, clean, all bulbs on

@lru_cache(2)
def face_lin(cracked=False):
    return cv2.resize(V.glass_face(cracked), (GW, GH), interpolation=cv2.INTER_AREA)

@lru_cache(1)
def crack_full():
    return cv2.resize(V.assets()["crack_mask"], (GW, GH), interpolation=cv2.INTER_AREA)

@lru_cache(12)
def crack_grow(kq):
    """the crack over the glass grown to kq/10 (top-right first, the branch last)."""
    if kq >= 10: return crack_full()
    return cv2.resize(V.crack_reveal_glass(kq / 10.0), (GW, GH), interpolation=cv2.INTER_AREA)

@lru_cache(1)
def edge_vig():
    yy, xx = np.mgrid[0:GH, 0:GW].astype(F32)
    d = np.minimum.reduce([xx, GW - 1 - xx, yy, GH - 1 - yy])
    return (1 - 0.45 * np.exp(-d / 18.0) - 0.18 * np.exp(-d / 80.0)).astype(F32)[..., None]

# ---------------------------------------------------------------- funhouse distortions of the face
SMOOTH_KINDS = {"tall", "wide", "bulge", "pinch", "wave", "twirl", "symm"}     # morph by bending the map
@lru_cache(96)
def warp_maps(kind, kq):
    k = kq / 10.0
    yy, xx = np.mgrid[0:GH, 0:GW].astype(F32)
    cx, cy = (GW - 1) / 2, (GH - 1) / 2
    dx, dy = xx - cx, yy - cy
    if kind == "tall": sx, sy = xx, cy + dy * (1 - 0.55 * k)
    elif kind == "wide": sx, sy = cx + dx * (1 - 0.58 * k), yy
    elif kind in ("bulge", "pinch"):
        R = 0.66 * GH; r = np.sqrt(dx * dx + dy * dy) / R
        p = (1 + 0.95 * k) if kind == "bulge" else 1 / (1 + 0.85 * k)
        rr = np.where(r < 1, np.power(np.maximum(r, 1e-6), p), r)
        f = rr / np.maximum(r, 1e-6); sx, sy = cx + dx * f, cy + dy * f
    elif kind == "wave":
        sx = xx + k * 34 * np.sin(yy / GH * 2 * np.pi * 2.6 + 0.6); sy = yy + k * 22 * np.sin(xx / GW * 2 * np.pi * 2.1)
    elif kind == "twirl":
        R = 0.62 * GH; r = np.sqrt(dx * dx + dy * dy) / R
        a = k * 2.4 * np.clip(1 - r, 0, 1) ** 2; c, s = np.cos(a), np.sin(a)
        sx, sy = cx + dx * c - dy * s, cy + dx * s + dy * c
    elif kind == "symm":                              # the left half, mirrored onto the right: a perfect face
        sx = xx * (1 - k) + (cx - np.abs(dx)) * k; sy = yy
    else: sx, sy = xx, yy
    return sx.astype(F32), sy.astype(F32)

def variant(f, kind, k):
    """the face f (linear GH x GW x 3) through the distortion `kind` at strength k (0..1)."""
    if k <= 0.001 or kind in (None, "flat"): return f
    if kind in SMOOTH_KINDS:
        sx, sy = warp_maps(kind, int(round(k * 10)))
        return cv2.remap(f, sx, sy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    if kind == "grid":                               # thirty takes: the face, 5 x 6 times
        cw, ch = GW / 5, GH / 6
        yy, xx = np.mgrid[0:GH, 0:GW].astype(F32)
        sx = (xx % cw) / cw * GW; sy = (yy % ch) / ch * GH
        g = cv2.remap(f, sx, sy, cv2.INTER_AREA if False else cv2.INTER_LINEAR)
        cell = ((xx // cw) + (yy // ch) * 5).astype(np.int32)
        tint = np.array([[1.0, 1.0, 1.0], [1.06, 0.98, 0.92], [0.92, 0.98, 1.08], [1.04, 1.04, 0.9]], F32)[cell % 4]
        g = g * tint * (0.85 + 0.15 * ((cell * 7) % 5 == 0))[..., None]
        line = ((xx % cw) < 2) | ((yy % ch) < 2)
        g[line] *= 0.15
    elif kind == "twins":                            # two of you, side by side
        yy, xx = np.mgrid[0:GH, 0:GW].astype(F32)
        sx = ((xx * 2) % GW) * 0.86 + GW * 0.07; sy = (yy - GH / 2) * 0.86 + GH / 2
        g = cv2.remap(f, sx, sy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    elif kind == "steps":                            # auto-tune: the face cut into bands, each snapped sideways
        yy, xx = np.mgrid[0:GH, 0:GW].astype(F32)
        band = (yy // 54).astype(np.int32)
        off = np.array([0, 26, -18, 34, -30, 12, -8, 22, -24, 6, 30, -14, 18, -28, 8, -20, 26], F32)[band % 17]
        g = cv2.remap(f, xx + off, (band * 54 + 27).astype(F32) * 0.5 + yy * 0.5, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    elif kind == "mosaic":
        s = 22; g = cv2.resize(cv2.resize(f, (GW // s, GH // s), interpolation=cv2.INTER_AREA), (GW, GH), interpolation=cv2.INTER_NEAREST)
    elif kind == "smooth":                           # the beauty filter: plastic skin, a glow
        u8 = to_u8(f)
        for _ in range(3): u8 = cv2.bilateralFilter(u8, 9, 70, 9)
        g = LUT[u8] * np.array([1.18, 1.1, 1.04], F32) + 0.012
        g = g + cv2.GaussianBlur(g, (0, 0), 14) * 0.25
    elif kind == "gold":                             # sponsored: everything a little golden
        lum = (f * np.array([0.3, 0.55, 0.15], F32)).sum(-1, keepdims=True)
        g = lum * np.array([1.5, 1.1, 0.45], F32) * 1.25
    else: return f
    return f * (1 - k) + g * k

# ---------------------------------------------------------------- the texture of one mirror
@lru_cache(1)
def tex_alpha():
    a = np.zeros((TH * 2, TW * 2), np.uint8); r = 36
    cv2.rectangle(a, (r * 2 + 8, 8), (TW * 2 - r * 2 - 8, TH * 2 - 8), 255, -1)
    cv2.rectangle(a, (8, r * 2 + 8), (TW * 2 - 8, TH * 2 - r * 2 - 8), 255, -1)
    for x, y in ((r * 2 + 8, r * 2 + 8), (TW * 2 - r * 2 - 8, r * 2 + 8), (r * 2 + 8, TH * 2 - r * 2 - 8), (TW * 2 - r * 2 - 8, TH * 2 - r * 2 - 8)):
        cv2.circle(a, (x, y), r * 2, 255, -1)
    a = cv2.resize(a, (TW, TH), interpolation=cv2.INTER_AREA)
    return cv2.GaussianBlur(a, (0, 0), 2.5)

def build_mips(rgba):
    out = [rgba]
    for _ in range(3):
        h, w = out[-1].shape[:2]; out.append(cv2.resize(out[-1], (max(2, w // 2), max(2, h // 2)), interpolation=cv2.INTER_AREA))
    return out

@lru_cache(40)
def mirror_tex(kind, kq, crack=0, dark=0):
    """mip chain of RGBA uint8 for a wall mirror: the frame from the cover, its glass showing the face through
    `kind` at strength kq/10, the crack grown to crack/10, the glass blacked out by dark/10 (no reflection)."""
    img = cover_lin()[FY0:FY1, FX0:FX1].copy()
    g = variant(face_lin(False), kind, kq / 10.0)
    if crack:
        m = crack_grow(crack)[..., None]
        g = g * (1 - m) + face_lin(True) * m + m * F32(0.05)
    g = g * edge_vig()
    if dark: g = g * (1 - dark / 10.0)
    img[GY0:GY1, GX0:GX1] = g
    rgba = np.dstack([to_u8(img), tex_alpha()])
    return build_mips(rgba)

@lru_cache(8)
def refl_tex(kind, kq, crack=0, dark=0):
    """the blurred, darker copy a glossy floor shows: alpha strongest at the mirror's bottom edge."""
    m = mirror_tex(kind, kq, crack, dark)[2].copy()
    m[..., :3] = cv2.GaussianBlur(m[..., :3], (0, 0), 3.0)
    h = m.shape[0]; grad = np.clip((np.arange(h, dtype=F32) / h - 0.15) / 0.85, 0, 1) ** 1.6
    m[..., 3] = (m[..., 3].astype(F32) * grad[:, None] * 0.34).astype(np.uint8)
    return m

# ---------------------------------------------------------------- the cover at the end of the hall
END_S = 2.6                                          # the end vanity is 2.6 units tall (the whole cover image)
@lru_cache(8)
def end_tex(crack=0, lit=10):
    img = cover_lin().copy()
    g = face_lin(False)
    if crack:
        m = crack_grow(crack)[..., None]; g = g * (1 - m) + face_lin(True) * m
    img[152:1012, 307:948] = g * edge_vig()
    img *= F32(0.25 + 0.75 * lit / 10.0)
    yy, xx = np.mgrid[0:1254, 0:1254].astype(F32)
    d = np.minimum.reduce([xx, 1253 - xx, yy, 1253 - yy])
    a = (np.clip(d / 200.0, 0, 1) ** 1.5 * 255).astype(np.uint8)
    return build_mips(np.dstack([to_u8(img), a]))

# ================================================================ camera and projection
class Cam:
    __slots__ = ("x", "y", "z", "yaw", "pitch", "roll", "f", "R")
    def __init__(s, x, y, z, yaw, pitch, roll, f):
        s.x, s.y, s.z, s.yaw, s.pitch, s.roll, s.f = x, y, z, yaw, pitch, roll, f
        cy, sy = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        cp, sp = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
        cr, sr = math.cos(math.radians(roll)), math.sin(math.radians(roll))
        Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]); Rx = np.array([[1, 0, 0], [0, cp, -sp], [0, sp, cp]])
        Rz = np.array([[cr, -sr, 0], [sr, cr, 0], [0, 0, 1]])
        s.R = Ry @ Rx @ Rz                               # camera -> world

def project(cam, P, W, H):
    """world points (N, 3) -> (screen xy (N, 2), depth (N,))."""
    p = (np.asarray(P, np.float64) - np.array([cam.x, cam.y, cam.z])) @ cam.R
    d = -p[:, 2]
    dd = np.where(np.abs(d) < 1e-6, 1e-6, d)
    return np.stack([W / 2 + cam.f * p[:, 0] / dd, H / 2 - cam.f * p[:, 1] / dd], 1), d

def mirror_corners(side, zc, hall):
    """world corners TL, TR, BR, BL of a wall mirror (side -1 left wall, +1 right wall) centred at depth zc."""
    th = math.radians(hall["tilt"])                 # turned a little toward the hall's entrance
    if side < 0: u = np.array([math.sin(th), 0, -math.cos(th)]); xc = -hall["Wc"] + 0.04 + MIR_W / 2 * math.sin(th)
    else: u = np.array([math.sin(th), 0, math.cos(th)]); xc = hall["Wc"] - 0.04 - MIR_W / 2 * math.sin(th)
    c = np.array([xc, hall["Ym"], zc]); up = np.array([0, 1.0, 0])
    hw, hh = MIR_W / 2, MIR_H / 2
    return np.array([c - u * hw + up * hh, c + u * hw + up * hh, c + u * hw - up * hh, c - u * hw - up * hh])

def end_corners(hall):
    z = -hall["Zend"]; s = END_S
    return np.array([[-s / 2, s, z], [s / 2, s, z], [s / 2, 0, z], [-s / 2, 0, z]], np.float64)

# ================================================================ drawing
def warp_quad(img, mips, quad_xy, depth, gain=1.0, near=0.25, alpha_mul=1.0):
    """draw the texture (mip chain) into img (linear) on the projected quad. returns False if not drawn."""
    if depth.min() < near: return False
    H, W = img.shape[:2]
    x0, y0 = np.floor(quad_xy.min(0)).astype(int); x1, y1 = np.ceil(quad_xy.max(0)).astype(int)
    X0, Y0, X1, Y1 = max(0, x0), max(0, y0), min(W, x1 + 1), min(H, y1 + 1)
    if X1 - X0 < 2 or Y1 - Y0 < 2: return False
    ph = max(np.linalg.norm(quad_xy[3] - quad_xy[0]), np.linalg.norm(quad_xy[2] - quad_xy[1]))
    L = int(clamp(math.floor(math.log2(max(1.0, mips[0].shape[0] / max(ph, 1.0)))), 0, len(mips) - 1))
    tex = mips[L]; th, tw = tex.shape[:2]
    src = np.array([[0, 0], [tw, 0], [tw, th], [0, th]], F32)
    Hm = cv2.getPerspectiveTransform(src, (quad_xy - np.array([X0, Y0])).astype(F32))
    w = cv2.warpPerspective(tex, Hm, (X1 - X0, Y1 - Y0), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    a = w[..., 3]
    if not a.any(): return False
    af = a.astype(F32) * F32(alpha_mul / 255.0)
    reg = img[Y0:Y1, X0:X1]
    reg *= (1 - af)[..., None]
    reg += LUT[w[..., :3]] * (af * gain)[..., None]
    return True

GLOW_CORE = np.array([1.0, 0.80, 0.55], F32); GLOW_HALO = np.array([1.0, 0.62, 0.30], F32)
def bulb_points(corners):
    """world positions of the 12 bulbs of a mirror with these corners, and the bulb radius in world units."""
    TL, TR, BR, BL = corners
    pts = []
    for (bx, by, r) in V.bulbs():
        u = (bx / 2 - FX0) / TW; v = (by / 2 - FY0) / TH
        pts.append(TL + (TR - TL) * u + (BL - TL) * v)
    return np.array(pts), 36.0 / TH * MIR_H

def splat_bulbs(E, cam, pts, rw, gain, W, H, refl=False):
    if gain <= 0.01: return
    xy, d = project(cam, pts, W, H)
    for (x, y), dd in zip(xy, d):
        if dd < 0.3: continue
        rr = rw * cam.f / dd
        if x < -6 * rr or x > W + 6 * rr or y < -6 * rr or y > H + 6 * rr: continue
        V._splat(E, x, y, max(0.9, rr * 0.75), GLOW_CORE, 1.4 * gain)
        V._splat(E, x, y, max(1.5, rr * 2.4), GLOW_HALO, (0.05 if refl else 0.09) * gain)

# ---------------------------------------------------------------- the hall itself: walls, floor, ceiling (ray cast)
@lru_cache(4)
def rays(W, H, f, k):
    w, h = W // k, H // k
    yy, xx = np.mgrid[0:h, 0:w].astype(F32)
    X = (xx * k + k / 2 - W / 2) / f; Y = -(yy * k + k / 2 - H / 2) / f
    return np.stack([X, Y, -np.ones_like(X)], -1).reshape(-1, 3)

WALL = np.array([0.0090, 0.0050, 0.0042], F32); FLOOR = np.array([0.0052, 0.0037, 0.0032], F32)
CEIL = np.array([0.0016, 0.0013, 0.0012], F32); WARM = np.array([1.0, 0.60, 0.30], F32)
def hall_bg(cam, W, H, hall, light_fn, end_glow=1.0, k=2):
    """the room, rendered at 1/k resolution and upscaled. light_fn(side, idx array) -> brightness of those mirrors."""
    R = rays(W, H, cam.f, k)
    d = R @ cam.R.T
    dx, dy, dz = d[:, 0], d[:, 1], d[:, 2]
    Wc, Hc, D = hall["Wc"], hall["Hc"], hall["D"]
    inf = np.float32(1e9)
    with np.errstate(divide="ignore", invalid="ignore"):
        tl = np.where(dx < -1e-6, (-Wc - cam.x) / dx, inf); tr = np.where(dx > 1e-6, (Wc - cam.x) / dx, inf)
        tf = np.where(dy < -1e-6, (0 - cam.y) / dy, inf); tc = np.where(dy > 1e-6, (Hc - cam.y) / dy, inf)
        te = np.where(dz < -1e-6, (-hall["Zend"] - cam.z) / dz, inf)
    T = np.stack([tl, tr, tf, tc, te], 1); sid = T.argmin(1); t = T[np.arange(len(T)), sid]
    t = np.where(t > 0, t, inf).astype(F32)
    X = cam.x + dx * t; Y = cam.y + dy * t; Z = cam.z + dz * t
    col = np.zeros((len(t), 3), F32)
    Ym = hall["Ym"]
    # walls: warm light spilling around each mirror
    for side, s_id, off in ((-1, 0, 0.0), (1, 1, 0.5)):
        m = sid == s_id
        if not m.any(): continue
        z = Z[m]; y = Y[m]
        q = -z / D - off; idx = np.round(q).astype(np.int32); dz_ = (q - idx) * D
        L = light_fn(side, idx)
        g = np.exp(-(dz_ / 0.58) ** 2 - ((y - Ym) / 0.75) ** 2) * 0.55 + np.exp(-(dz_ / 1.2) ** 2 - ((y - Ym) / 1.6) ** 2) * 0.10
        wains = np.where(y < 0.42, 0.55, 1.0) * np.where(np.abs(y - 0.42) < 0.018, 1.9, 1.0)   # dado rail
        col[m] = WALL * (wains * (0.45 + 0.35 * np.clip(y / Hc, 0, 1)))[:, None] + WARM * (g * L * 0.15)[:, None]
    # floor: pools of light under the mirrors, a warm streak toward the far vanity
    m = sid == 2
    if m.any():
        x = X[m]; z = Z[m]
        qa = -z / D; ia = np.round(qa).astype(np.int32); da = (qa - ia) * D
        qb = -z / D - 0.5; ib = np.round(qb).astype(np.int32); db = (qb - ib) * D
        La = light_fn(-1, ia); Lb = light_fn(1, ib)
        pa = np.exp(-((x + Wc) / 0.75) ** 2 - (da / 0.7) ** 2) * La; pb = np.exp(-((x - Wc) / 0.75) ** 2 - (db / 0.7) ** 2) * Lb
        streak = np.exp(-(x / 0.55) ** 2) * 0.03 * end_glow
        planks = 1.0 + 0.10 * np.cos(x / 0.21 * 2 * np.pi)
        col[m] = FLOOR * planks[:, None] + WARM * ((pa + pb) * 0.13 + streak)[:, None]
    m = sid == 3
    if m.any(): col[m] = CEIL
    m = sid == 4
    if m.any():
        x = X[m]; y = Y[m]
        col[m] = WALL * 0.28 + WARM * (np.exp(-(x / 2.2) ** 2 - ((y - 1.3) / 1.6) ** 2) * 0.018 * end_glow)[:, None]
    # haze: the far end glows a little through the air
    fog = np.exp(-t / hall["fog"]).astype(F32)[:, None]
    col = col * fog + np.array([0.0042, 0.0027, 0.0019], F32) * end_glow * (1 - fog)
    img = col.reshape(H // k, W // k, 3)
    return cv2.resize(img, (W, H), interpolation=cv2.INTER_LINEAR)
