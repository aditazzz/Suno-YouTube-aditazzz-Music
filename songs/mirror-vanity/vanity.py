"""The Vanity: the set is the song's cover art (a bulb-lit dressing-room mirror whose glass shows a face made of the feed).
It is used as a photographic plate: upscaled 2x, the crack painted out (it arrives later, exactly where it is on the
cover), the 12 bulbs found so they can be switched off one by one (relighting the frame and the table with them),
and the glass separated so its content can be animated: dark glass, fog and finger writing, the feed, receipts,
and the face assembling from its own tiles.

Coordinates: plate pixels at 2x (the cover is 1254 px; the plate is 2508 px). Linear float32 colour.
"""
import os, json, math
from functools import lru_cache
import numpy as np, cv2

HERE = os.path.dirname(os.path.abspath(__file__))
F32 = np.float32
S = 2                                         # plate scale over the 1254 px cover
N = 1254 * S
GLASS = (307 * S, 152 * S, 948 * S, 1012 * S)  # x0, y0, x1, y1 of the mirror glass
CANVAS_W = 4800                              # the plate centred on a wider dark canvas (16:9 framing, pans)
CX0 = (CANVAS_W - N) // 2                    # plate x offset inside the canvas

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def sstep(a, b, x):
    if b == a: return 1.0 if x >= b else 0.0
    t = clamp((x - a) / (b - a)); return t * t * (3 - 2 * t)
def ease_io(t): t = clamp(t); return t * t * t * (t * (6 * t - 15) + 10)
def lerp(a, b, t): return a + (b - a) * t
def to_lin(u8): return np.power(u8.astype(F32) / 255.0, 2.2)

@lru_cache(1)
def bulbs():
    b = json.load(open(os.path.join(HERE, "assets", "bulbs.json")))
    return [(d["x"] * S, d["y"] * S, d["r"] * S) for d in b]

@lru_cache(1)
def crack_paths():
    d = json.load(open(os.path.join(HERE, "assets", "crack_track.json")))
    return [np.array([(x * S, y * S) for x, y, v in d["main"]], F32), np.array([(x * S, y * S) for x, y, v in d["branch"]], F32)]

@lru_cache(1)
def extra_paths():
    d = json.load(open(os.path.join(HERE, "assets", "crack_track.json")))
    return [np.array([(x * S, y * S) for x, y, v in seg], F32) for seg in d.get("extra", [])]

@lru_cache(1)
def plates():
    """(plate_cracked, plate_clean, crack_mask) at 2x, linear. Cached to disk (inpainting is slow)."""
    cache = os.path.join(HERE, "build", "plates_2x.npz")
    if os.path.exists(cache):
        z = np.load(cache)
        return z["cracked"], z["clean"], z["mask"]
    src = cv2.cvtColor(cv2.imread(os.path.join(HERE, "assets", "cover_ref.png")), cv2.COLOR_BGR2RGB)
    # the crack at 1x: each traced centreline is 'zipped' shut: pixels inside the crack take the colour from just
    # outside it on their own side (crisp texture, no smear), then a light Telea pass blends the seam.
    d = json.load(open(os.path.join(HERE, "assets", "crack_track.json")))
    paths = [np.array([(x, y) for x, y, v in d["main"]], np.float32), np.array([(x, y) for x, y, v in d["branch"]], np.float32)]
    paths += [np.array([(x, y) for x, y, v in seg], np.float32) for seg in d.get("extra", [])]
    h0, w0 = src.shape[:2]
    mapx, mapy = np.meshgrid(np.arange(w0, dtype=np.float32), np.arange(h0, dtype=np.float32))
    m = np.zeros((h0, w0), np.uint8)
    hw = 3.2
    for P in paths:
        # densify
        seg = np.cumsum(np.r_[0, np.linalg.norm(np.diff(P, axis=0), axis=1)])
        ss = np.arange(0, seg[-1], 0.4)
        X = np.interp(ss, seg, P[:, 0]); Y = np.interp(ss, seg, P[:, 1])
        tx = np.gradient(X); ty = np.gradient(Y); tn = np.hypot(tx, ty) + 1e-6; tx /= tn; ty /= tn
        nx, ny = -ty, tx
        for o in np.arange(-hw, hw + 0.01, 0.4):
            qx = np.round(X + nx * o).astype(np.int32); qy = np.round(Y + ny * o).astype(np.int32)
            ok = (qx >= 0) & (qx < w0) & (qy >= 0) & (qy < h0)
            sg = 1.0 if o >= 0 else -1.0
            mapx[qy[ok], qx[ok]] = (X + nx * sg * (hw + 1.6))[ok]
            mapy[qy[ok], qx[ok]] = (Y + ny * sg * (hw + 1.6))[ok]
            m[qy[ok], qx[ok]] = 255
    zipped = cv2.remap(src, mapx, mapy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    seam = np.zeros_like(m)
    for P in paths:
        cv2.polylines(seam, [np.round(P * 8).astype(np.int32)], False, 255, 1, cv2.LINE_8, shift=3)
    clean = cv2.inpaint(zipped, seam, 1, cv2.INPAINT_TELEA)
    up = lambda a: cv2.resize(a, (N, N), interpolation=cv2.INTER_LANCZOS4)
    cracked = up(src); clean2 = up(clean)
    # a little sharpening after the upscale
    def sharpen(a):
        b = cv2.GaussianBlur(a, (0, 0), 1.2); return cv2.addWeighted(a, 1.35, b, -0.35, 0)
    cracked = to_lin(np.clip(sharpen(cracked), 0, 255)); clean2 = to_lin(np.clip(sharpen(clean2), 0, 255))
    mask = cv2.resize(cv2.GaussianBlur(m, (0, 0), 0.8), (N, N), interpolation=cv2.INTER_LINEAR).astype(F32) / 255
    os.makedirs(os.path.dirname(cache), exist_ok=True)
    np.savez(cache, cracked=cracked.astype(F32), clean=clean2.astype(F32), mask=mask.astype(F32))
    return cracked.astype(F32), clean2.astype(F32), mask.astype(F32)

@lru_cache(1)
def assets():
    """what a render worker needs, compact (uint16 linear): the clean plate at 2x and 1x, the glass of the clean and the
    cracked plate, the crack mask over the glass, the room-edge colours. Built once from plates(), cached on disk."""
    cache = os.path.join(HERE, "build", "vanity_assets.npz")
    if not os.path.exists(cache):
        cr, cl, m = plates()
        sy, sx = glass_slice()
        q = lambda a: np.clip(a * 65535.0 + 0.5, 0, 65535).astype(np.uint16)
        l1 = cv2.resize(cl, (N // 2, N // 2), interpolation=cv2.INTER_AREA)
        pad_l = cv2.GaussianBlur(cl[:, :24].mean(1, keepdims=True), (0, 0), sigmaX=0.1, sigmaY=60) * 0.6
        pad_r = cv2.GaussianBlur(cl[:, -24:].mean(1, keepdims=True), (0, 0), sigmaX=0.1, sigmaY=60) * 0.6
        tmp = cache[:-4] + ".part.npz"
        np.savez(tmp, l0=q(cl), l1=q(l1), face_clean=q(cl[sy, sx]), face_cracked=q(cr[sy, sx]),
                 crack_mask=m[sy, sx].astype(F32), pad_l=pad_l.astype(F32).reshape(-1, 1, 3), pad_r=pad_r.astype(F32).reshape(-1, 1, 3))
        os.replace(tmp, cache)
    z = np.load(cache)
    return {k: z[k] for k in z.files}

@lru_cache(2)
def glass_face(cracked=False):
    return np.ascontiguousarray(assets()["face_cracked" if cracked else "face_clean"].astype(F32) * F32(1 / 65535.0))

def crack_reveal_glass(k):
    """the crack grown to progress k (0..1) over the glass: top-right first, the branch last."""
    main, br = crack_paths()
    off = np.array([GLASS[0], GLASS[1]], F32)
    gw, gh = GLASS[2] - GLASS[0], GLASS[3] - GLASS[1]
    out = np.zeros((gh, gw), np.uint8)
    n1 = int(round(len(main) * clamp(k / 0.82)))
    if n1 > 1: cv2.polylines(out, [np.round((main[:n1] - off) * 4).astype(np.int32)], False, 255, 22, cv2.LINE_8, shift=2)
    if k > 0.70:
        n2 = int(round(len(br) * clamp((k - 0.70) / 0.30)))
        if n2 > 1: cv2.polylines(out, [np.round((br[:n2] - off) * 4).astype(np.int32)], False, 255, 22, cv2.LINE_8, shift=2)
        if k > 0.80:
            for seg in extra_paths():
                n3 = int(round(len(seg) * clamp((k - 0.80) / 0.20)))
                if n3 > 1: cv2.polylines(out, [np.round((seg[:n3] - off) * 4).astype(np.int32)], False, 255, 22, cv2.LINE_8, shift=2)
    return cv2.GaussianBlur(out, (0, 0), 2).astype(F32) / 255 * assets()["crack_mask"]

def crack_reveal_mask(k):
    """0..1 along the crack: the part of the crack that exists at progress k (top-right first, the branch last)."""
    cr, cl, mask = plates()
    main, br = crack_paths()
    out = np.zeros((N, N), np.uint8)
    L1 = len(main); n1 = int(round(L1 * clamp(k / 0.82)))
    if n1 > 1: cv2.polylines(out, [np.round(main[:n1] * 4).astype(np.int32)], False, 255, 22, cv2.LINE_8, shift=2)
    if k > 0.70:
        n2 = int(round(len(br) * clamp((k - 0.70) / 0.30)))
        if n2 > 1: cv2.polylines(out, [np.round(br[:n2] * 4).astype(np.int32)], False, 255, 22, cv2.LINE_8, shift=2)
        if k > 0.80:
            for seg in extra_paths():
                n3 = int(round(len(seg) * clamp((k - 0.80) / 0.20)))
                if n3 > 1: cv2.polylines(out, [np.round(seg[:n3] * 4).astype(np.int32)], False, 255, 22, cv2.LINE_8, shift=2)
    return cv2.GaussianBlur(out, (0, 0), 2).astype(F32) / 255 * mask

@lru_cache(1)
def bulb_weights():
    """per-bulb illumination maps (low res) used to relight the plate when bulbs switch off."""
    sc = 0.0625
    w, h = int(N * sc), int(N * sc)
    yy, xx = np.mgrid[0:h, 0:w].astype(F32) / sc
    maps = []
    for (bx, by, r) in bulbs():
        d2 = (xx - bx) ** 2 + (yy - by) ** 2
        maps.append(1.0 / (1.0 + d2 / (r * 2.2) ** 2) + 0.35 / (1.0 + d2 / (r * 9.0) ** 2))
    return np.stack(maps, 0).astype(F32)

def relight_ratio(on, amb=0.06):
    """the plate is the scene with every bulb on; with bulb i at on[i] (0..1+) the light falls to this ratio."""
    W_ = bulb_weights()
    on = np.asarray(on, F32)[:, None, None]
    tot = W_.sum(0)
    r = (amb + (W_ * on).sum(0)) / (amb + tot)
    return cv2.resize(r, (N, N), interpolation=cv2.INTER_LINEAR)

@lru_cache(1)
def bulb_masks():
    """soft discs of the bulbs (to switch each one off) at full plate resolution, as a list of (y0, y1, x0, x1, alpha)."""
    out = []
    for (bx, by, r) in bulbs():
        R = int(r * 1.35)
        x0, y0 = int(bx) - R, int(by) - R; x1, y1 = int(bx) + R, int(by) + R
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(F32)
        d = np.sqrt((xx - bx) ** 2 + (yy - by) ** 2)
        a = np.clip((r * 1.08 - d) / (r * 0.18), 0, 1)
        out.append((y0, y1, x0, x1, a.astype(F32)))
    return out

def bulb_off_look(roi, a, k):
    """a dead bulb: the glass globe dark, a faint grey sheen top-left, no glow."""
    h, w = a.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(F32)
    cx, cy = w / 2, h / 2
    spec = np.exp(-(((xx - cx + w * 0.16) / (w * 0.12)) ** 2 + ((yy - cy + h * 0.18) / (h * 0.10)) ** 2)) * 0.05
    dead = np.array([0.012, 0.011, 0.010], F32)[None, None] + spec[..., None]
    A = (a * k)[..., None]
    roi *= (1 - A); roi += dead * A

def glass_slice(): x0, y0, x1, y1 = GLASS; return slice(y0, y1), slice(x0, x1)

@lru_cache(1)
def edge_canvas():
    """the dark surround for the canvas outside the plate: the plate's edge colours smeared out and darkened."""
    a = assets(); return a["pad_l"], a["pad_r"]

def compose_plate(base, glass_img, on, extra=None):
    """the full plate for this frame: the plate relit by the bulbs that are on, dead bulbs dark, and the glass content
    replaced by glass_img (linear, the glass size). returns the plate (N, N, 3)."""
    img = base * relight_ratio(on)[..., None]
    for i, (y0, y1, x0, x1, a) in enumerate(bulb_masks()):
        k = clamp(1 - on[i])
        if k > 0.001: bulb_off_look(img[y0:y1, x0:x1], a, k)
    if glass_img is not None:
        sy, sx = glass_slice()
        img[sy, sx] = glass_img
    return img

def bulb_glow(img, on, gain=1.0, ox=0.0, oy=0.0, scale=1.0):
    """HDR emission on top of the lit bulbs (feeds the bloom), in whatever image the plate was warped into: pass the
    plate->image transform as (scale, ox, oy)."""
    H, W = img.shape[:2]
    for i, (bx, by, r) in enumerate(bulbs()):
        g = on[i] * gain
        if g <= 0.01: continue
        x, y = bx * scale + ox, by * scale + oy
        rr = r * scale
        if x < -4 * rr or x > W + 4 * rr or y < -4 * rr or y > H + 4 * rr: continue
        _splat(img, x, y, rr * 0.75, np.array([1.0, 0.80, 0.55], F32), 1.6 * g)
        _splat(img, x, y, rr * 2.6, np.array([1.0, 0.62, 0.30], F32), 0.10 * g)

@lru_cache(64)
def _gk(r):
    n = int(math.ceil(r * 1.6)); x = np.arange(-n, n + 1, dtype=F32)
    g = np.exp(-(x / max(0.5, r / 2.5)) ** 2 / 2); return np.outer(g, g).astype(F32)

def _splat(img, x, y, r, col, gain):
    r = max(0.8, float(r)); rk = round(r) if r > 8 else round(r * 2) / 2
    k = _gk(rk); n = k.shape[0] // 2
    H, W = img.shape[:2]; xi, yi = int(round(x)), int(round(y))
    x0, y0, x1, y1 = xi - n, yi - n, xi + n + 1, yi + n + 1
    if x1 <= 0 or y1 <= 0 or x0 >= W or y0 >= H: return
    kx0, ky0 = max(0, -x0), max(0, -y0); kx1, ky1 = k.shape[1] - max(0, x1 - W), k.shape[0] - max(0, y1 - H)
    img[max(0, y0):min(H, y1), max(0, x0):min(W, x1)] += k[ky0:ky1, kx0:kx1, None] * (col * gain)[None, None]

def view(plate_img, W, H, cx, cy, zoom=1.0, ang=0.0):
    """photograph the plate: centre (cx, cy) in plate px, zoom 1 = the whole plate height fits the frame height
    (9:16 frames fit the plate width instead). Outside the plate: the darkened edge colours.
    returns (frame, (scale, ox, oy)) with frame = plate warped, and the plate->frame transform for overlays."""
    vert = H > W
    base_h = N if not vert else N * H / W
    s = H / base_h * zoom
    rot = math.radians(ang)
    c, sn = math.cos(rot) * s, math.sin(rot) * s
    M = np.array([[c, -sn, W / 2 - (c * cx - sn * cy)], [sn, c, H / 2 - (sn * cx + c * cy)]], F32)
    out = cv2.warpAffine(plate_img, M, (W, H), flags=cv2.INTER_AREA if s < 0.8 else cv2.INTER_LINEAR,
                         borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
    # fill outside the plate with its edge colours, smeared out and fading to black
    Minv = cv2.invertAffineTransform(M)
    corners = np.array([[0, 0, 1], [W - 1, 0, 1], [0, H - 1, 1], [W - 1, H - 1, 1]], F32) @ Minv.T
    if corners[:, 0].min() < 0 or corners[:, 0].max() > N - 1 or corners[:, 1].min() < 0 or corners[:, 1].max() > N - 1:
        pad_l, pad_r = edge_canvas()
        yy, xx = np.mgrid[0:H, 0:W].astype(F32)
        px = Minv[0, 0] * xx + Minv[0, 1] * yy + Minv[0, 2]
        py = Minv[1, 0] * xx + Minv[1, 1] * yy + Minv[1, 2]
        inside = (px >= 0) & (px <= N - 1) & (py >= 0) & (py <= N - 1)
        rows = np.clip(py, 0, N - 1).astype(np.int32)
        fill = np.where((px < N / 2)[..., None], pad_l[rows, 0], pad_r[rows, 0])
        dist = np.maximum.reduce([-px, px - (N - 1), -py, py - (N - 1), np.zeros_like(px)])
        fill = fill * np.exp(-dist / (N * 0.035))[..., None]
        cov = cv2.warpAffine(np.ones((N, N), F32), M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        out = out * cov[..., None] + fill * (1 - cov[..., None])
    return out, (s, float(M[0, 2]), float(M[1, 2]), M)

# ================================================================ frame-space rendering helpers
GX0, GY0, GX1, GY1 = GLASS
GW, GH = GX1 - GX0, GY1 - GY0
JAR = (612, 1944, 726, 2024)                 # the candle jar on the table stands in front of the glass (plate px)

@lru_cache(1)
def plate_levels():
    """the clean plate (uint16 linear RGB) at 2x and 1x, and an 8-bit 'coverage' image of each (for the warp)."""
    a = assets()
    return [(a["l0"], np.full((N, N), 255, np.uint8)), (a["l1"], np.full((N // 2, N // 2), 255, np.uint8))]

def cam_matrix(W, H, cx, cy, zoom, ang=0.0):
    """plate -> frame. zoom 1: the plate height fits a 16:9 frame / the plate width fits a 9:16 frame."""
    s = (H if W >= H else W) / N * zoom
    rot = math.radians(ang); c, sn = math.cos(rot) * s, math.sin(rot) * s
    M = np.array([[c, -sn, W / 2 - (c * cx - sn * cy)], [sn, c, H / 2 - (sn * cx + c * cy)]], F32)
    return M, s

def M_sub(M, ox, oy, k=1.0):
    """M for a source image that is the plate region starting at (ox, oy), downscaled by k (k=2: half resolution)."""
    Mo = M.astype(np.float64).copy()
    Mo[:, 2] += M[:, 0] * ox + M[:, 1] * oy
    Mo[:, :2] *= k
    return Mo.astype(F32)

def xf(M, x, y): return float(M[0, 0] * x + M[0, 1] * y + M[0, 2]), float(M[1, 0] * x + M[1, 1] * y + M[1, 2])

def fill_outside(M, W, H):
    """the room beyond the plate: the plate's edge colours smeared outward, fading to black (computed at 1/4 res)."""
    w4, h4 = W // 4 + 2, H // 4 + 2
    Minv = cv2.invertAffineTransform(M)
    yy, xx = np.mgrid[0:h4, 0:w4].astype(F32) * 4
    px = Minv[0, 0] * xx + Minv[0, 1] * yy + Minv[0, 2]
    py = Minv[1, 0] * xx + Minv[1, 1] * yy + Minv[1, 2]
    pad_l, pad_r = edge_canvas()
    rows = np.clip(py, 0, N - 1).astype(np.int32)
    fill = np.where((px < N / 2)[..., None], pad_l[rows, 0], pad_r[rows, 0])
    dist = np.maximum.reduce([-px, px - (N - 1), -py, py - (N - 1), np.zeros_like(px)])
    fill = fill * np.exp(-dist / (N * 0.035))[..., None]
    big = cv2.resize(fill, (w4 * 4, h4 * 4), interpolation=cv2.INTER_LINEAR)
    return big[:H, :W]

def ratio_low(on, amb=0.06):
    W_ = bulb_weights(); onv = np.asarray(on, F32)[:, None, None]
    return ((amb + (W_ * onv).sum(0)) / (amb + W_.sum(0))).astype(F32)

def ratio_to_frame(rl, M, W, H):
    k = N / rl.shape[0]
    return cv2.warpAffine(rl, M_sub(M, 0, 0, k), (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)

def ratio_to_glass(rl):
    k = N / rl.shape[0]
    A = np.array([[k, 0, -GX0], [0, k, -GY0]], F32)
    return cv2.warpAffine(rl, A, (GW, GH), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)

def bulb_looks(img, M, s, on):
    """bulbs that are dim or off, painted in frame space: a frosted globe glowing warm from a weak filament, or dark."""
    H, W = img.shape[:2]
    for i, (bx, by, r) in enumerate(bulbs()):
        lv = float(on[i]); k = clamp((1.0 - lv) / 0.55)
        if k < 0.002: continue
        x, y = xf(M, bx, by); R = r * s
        X0, Y0, X1, Y1 = int(x - R * 1.3), int(y - R * 1.3), int(x + R * 1.3) + 2, int(y + R * 1.3) + 2
        if X1 <= 0 or Y1 <= 0 or X0 >= W or Y0 >= H: continue
        X0, Y0, X1, Y1 = max(0, X0), max(0, Y0), min(W, X1), min(H, Y1)
        yy, xx = np.mgrid[Y0:Y1, X0:X1].astype(F32)
        d = np.sqrt((xx - x) ** 2 + (yy - y) ** 2)
        a = np.clip((R * 1.04 - d) / max(0.8, R * 0.14), 0, 1)
        spec = np.exp(-(((xx - x + R * 0.36) / (R * 0.18)) ** 2 + ((yy - y + R * 0.40) / (R * 0.13)) ** 2)) * 0.012
        rim = np.clip(1 - np.abs(d - R * 0.93) / (R * 0.08), 0, 1) * 0.002
        lc = clamp(lv)
        glow = lc ** 1.5 * 1.9 * (0.05 + 0.95 * np.exp(-(d / (R * 0.46)) ** 2))
        warm = np.array([1.0, 0.26 + 0.50 * lc, 0.04 + 0.42 * lc], F32)
        col = np.array([0.006, 0.005, 0.0045], F32)[None, None] + (spec + rim)[..., None] * (1 - lc) + glow[..., None] * warm
        A = (a * k)[..., None]
        reg = img[Y0:Y1, X0:X1]; reg *= (1 - A); reg += col * A

@lru_cache(1)
def glass_edge_vignette():
    """the inner shadow of the frame on whatever the glass shows (the plate's own glass already has it)."""
    yy, xx = np.mgrid[0:GH, 0:GW].astype(F32)
    d = np.minimum.reduce([xx, GW - 1 - xx, yy, GH - 1 - yy])
    return (1 - 0.55 * np.exp(-d / 34.0) - 0.25 * np.exp(-d / 160.0)).astype(F32)

@lru_cache(1)
def glass_reflection_patches():
    """each bulb mirrored in the glass edge nearest to it: a soft warm bloom just inside the frame."""
    out = []
    for i, (bx, by, r) in enumerate(bulbs()):
        if by < 400:   # top row: the reflection sits right under the frame
            cx, cy, sx, sy = bx - GX0 + 6, 16.0, r * 0.85, r * 0.34
        elif bx < N / 2:
            cx, cy, sx, sy = 22.0, by - GY0 + 26, r * 0.36, r * 0.62
        else:
            cx, cy, sx, sy = GW - 26.0, by - GY0 + 40, r * 0.36, r * 0.62
        R = int(max(sx, sy) * 4.5)
        x0, y0 = int(cx) - R, int(cy) - R
        yy, xx = np.mgrid[y0:y0 + 2 * R, x0:x0 + 2 * R].astype(F32)
        g = np.exp(-(((xx - cx) / sx) ** 2 + ((yy - cy) / sy) ** 2) * 0.5) * 0.24 \
            + np.exp(-(((xx - cx) / (sx * 2.2)) ** 2 + ((yy - cy) / (sy * 2.2)) ** 2) * 0.5) * 0.045
        X0, Y0, X1, Y1 = max(0, x0), max(0, y0), min(GW, x0 + 2 * R), min(GH, y0 + 2 * R)
        out.append((Y0, Y1, X0, X1, g[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0].astype(F32)))
    return out

REFL_COL = np.array([1.0, 0.58, 0.26], F32)
def add_glass_reflections(g, on, amt=1.0):
    for i, (Y0, Y1, X0, X1, p) in enumerate(glass_reflection_patches()):
        k = float(on[i]) * amt
        if k > 0.01: g[Y0:Y1, X0:X1] += p[..., None] * REFL_COL * k

@lru_cache(1)
def jar_patch():
    """the jar in front of the glass, in glass coords: (sy, sx, alpha, plate pixels)."""
    x0, y0, x1, y1 = JAR
    gx0, gy0, gx1, gy1 = max(0, x0 - GX0), y0 - GY0, x1 - GX0, GH
    yy, xx = np.mgrid[gy0:gy1, gx0:gx1].astype(F32)
    # soft rectangle (the label is lit; rounded top corners)
    a = np.clip((xx - (x0 - GX0)) / 2.5, 0, 1) * np.clip(((x1 - GX0) - xx) / 2.5, 0, 1) * np.clip((yy - gy0) / 2.0, 0, 1)
    pix = glass_face(False)[gy0:gy1, gx0:gx1].copy()
    return (slice(gy0, gy1), slice(gx0, gx1), a.astype(F32), pix)
