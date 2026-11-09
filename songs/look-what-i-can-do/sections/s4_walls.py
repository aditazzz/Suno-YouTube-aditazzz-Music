"""S4 · qualifications (80.00-84.34 s, frames 2400-2529): the exchange seen through the night-vision security cameras
of "OMG! We Found Other Agents: They're In the Walls" (same ray-cast house, IR plates, wall atlas, OSD, DVR grid).

  80.00  CAM 01 (PTZ on the living room TV). The TV turns itself on, like in In the Walls, and Claude asks in amber:
         "What are your qualifications?"  (the only colour in the green night-vision frame is Claude's amber)
  82.10  her answer glows through the plaster above the TV, white-green, in In the Walls' handwriting:
         "I have a subscription."
  83.20  the PTZ jolts toward the TV: "To what?"
  83.64  "Everything." -> cut to the DVR's 3x3 grid: every camera in the house fills with subscription receipts at once
         (In the Walls' chorus, where every wall lit up together); the living room in the centre now says "Everything."
         in the wall, and the receipts never cover the word.

Copied from songs/omg-agents-walls (engine.py -> s4_engine.py, rooms.py -> s4_rooms.py, and the plate / atlas /
night-vision / OSD code below); nothing in that folder is touched. Plates and atlases cache under build/s4_cache.
"""
import os, sys, math, hashlib
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__)); SONG = os.path.dirname(HERE)
if HERE not in sys.path: sys.path.insert(0, HERE)
from studio import core as C
from studio.core import sstep, ease_out, ease_io, lerp, hexc, clamp, sprite, blit, text_w, shadow
import s4_engine as E
import s4_rooms as R

TM = C.Timing(SONG)
LINES = TM.lines
CACHE = os.path.join(SONG, "build", "s4_cache"); os.makedirs(CACHE, exist_ok=True)

FD = os.path.join(HERE, "s4_fonts")
def _f(name):
    p = os.path.join(C.FONTS, name)                         # the repo's shared fonts first, a local copy as fallback
    return p if os.path.exists(p) else os.path.join(FD, name)
VT = _f("VT323-Regular.ttf"); ROCK = _f("RockSalt-Regular.ttf"); TYPEW = _f("SpecialElite-Regular.ttf")
MARKER = _f("PermanentMarker-Regular.ttf"); CAVEAT = _f("Caveat-Medium.ttf"); SCRAWL = _f("ShadowsIntoLight-Regular.ttf")

NV_LO = np.array([0.010, 0.020, 0.016], np.float32); NV_HI = np.array([0.86, 0.98, 0.87], np.float32)
REC_RED = hexc('ff3b30'); OSD_W = np.array([0.97, 0.99, 0.97], np.float32)
AMBER = hexc('ffa840'); AMBER_HOT = hexc('ffd08a')

def rng(seed): return np.random.default_rng(seed)
def hsh(*a): return (math.sin(sum((i + 1) * 12.9898 * x for i, x in enumerate(a))) * 43758.5453) % 1.0
def F(a): return a.astype(np.float32)

# ================================================================== key times (from the song's word timings)
def _line(sub):
    for L in LINES:
        if sub.lower() in L["text"].lower(): return L
    raise KeyError(sub)
LQ, LSUB, LTO, LEV = _line("qualifications"), _line("I have a subscription"), _line("To what?"), _line("Everything.")
T_Q = LQ["s"]; T_SUB = LSUB["s"]; T_TO = LTO["s"]; T_EV = LEV["s"]; T_END = 84.34
Q_WORDS = list(zip(LQ["words"], LQ["wt"]))          # What 80.00, are 80.62, your 80.74, qualifications? 80.88

# ================================================================== the house (same rooms, two tweaks)
def living_hi():
    """The living room with a sharper atlas on the back wall (the dialogue is written there, close to the PTZ)."""
    P, cams, lights = R.living()
    for p in P:
        if getattr(p, "name", None) == "back": p.ppm = 420
    return P, cams, lights
def livptz():
    """CAM 01 on PTZ: tight on the TV and the wall above it (where her answers come through)."""
    return R.closeup(living_hi, ((0.55, 2.10, 0.70), (3.86, 1.50, 6.0), 37), ((1.4, 2.0, 1.2), (3.9, 1.3, 6.0), 30))

CAMS = {"livptz": (livptz, "CAM 01", "LIVING RM", "living"),
        "hallway": (R.hallway, "CAM 02", "HALLWAY", "hallway"),
        "kitchen": (R.kitchen, "CAM 03", "KITCHEN", "kitchen"),
        "fridge": (R.fridge, "CAM 03", "KITCHEN", "kitchen"),
        "bedroom": (R.bedroom, "CAM 04", "BEDROOM", "bedroom"),
        "basement": (R.basement, "CAM 05", "BASEMENT", "basement"),
        "board": (R.board, "CAM 05", "BASEMENT", "basement"),
        "entry": (R.entry, "CAM 07", "FRONT DOOR", "entry"),
        "attic": (R.attic, "CAM 08", "ATTIC", "attic"),
        "net": (R.net, "CAM 06", "NETWORK", "basement"),
        "dome": (R.dome, "CAM 02", "HALLWAY", "hallway"),
        "keys": (R.keys, "CAM 07", "FRONT DOOR", "entry"),
        "livwide": (living_hi, "CAM 10", "LIVING RM", "living")}
ROOM_FN = {"living": living_hi, "hallway": R.hallway, "kitchen": R.kitchen, "bedroom": R.bedroom, "basement": R.basement,
           "entry": R.entry, "attic": R.attic}
ZOOMED = {"fridge": "ZOOM 4X", "board": "ZOOM 3X", "livptz": "PTZ 2X"}

_SRC = hashlib.md5((open(os.path.join(HERE, "s4_engine.py")).read() + open(os.path.join(HERE, "s4_rooms.py")).read()).encode()).hexdigest()[:8]
_SELF = open(os.path.abspath(__file__)).read()
_WHASH = hashlib.md5((_SRC + _SELF[_SELF.index("# " + "=" * 66 + " writing"):_SELF.index("# " + "=" * 66 + " end writing")]).encode()).hexdigest()[:8]

_ROOM = {}
def room(cid):
    if cid not in _ROOM:
        P, cams, lights = CAMS[cid][0]() if cid in CAMS else ROOM_FN[cid]()
        aw, ah, slots = R.assign_atlas(P)
        _ROOM[cid] = dict(P=P, cams=cams, lights=lights, aw=aw, ah=ah, slots=slots)
    return _ROOM[cid]

def cam_of(cid, W, H): return room(cid)["cams"]["9x16" if H > W else "16x9"]
def _camkey(cam): return hashlib.md5(np.concatenate([cam.pos, cam.R.ravel(), [cam.hfov, cam.k]]).astype(np.float32).tobytes()).hexdigest()[:6]

_PLATES = {}
def plate(cid, W, H):
    k = (cid, W, H)
    if k in _PLATES: return _PLATES[k]
    rm = room(cid); cam = cam_of(cid, W, H)
    d = E.cached_plate(CACHE, f"{cid}_{W}x{H}_{_SRC}_{_camkey(cam)}",
                       lambda: E.build_plate(rm["P"], cam, W, H, lights=rm["lights"], atlas_order=True))
    d = {kk: v for kk, v in d.items() if kk not in ("alb", "depth", "awall")}
    if len(_PLATES) >= 12: _PLATES.pop(next(iter(_PLATES)))
    _PLATES[k] = d
    return d

def proj(cid, W, H, pts): return cam_of(cid, W, H).project(np.asarray(pts, np.float32), W, H)
def wquad(cid, W, H, c, ex, ey):
    c = np.array(c, np.float32); ex = np.array(ex, np.float32); ey = np.array(ey, np.float32)
    x, y, z = proj(cid, W, H, np.stack([c, c + ex, c + ex + ey, c + ey]))
    if (z <= 0.05).any(): return None
    return np.stack([x, y], 1)

def warp_quad(dst, tex, quad_px, op=1.0, mode="add", alpha=None):
    if op <= 0.003 or quad_px is None: return
    H, W = dst.shape[:2]; q = np.array(quad_px, np.float32)
    x0, y0 = np.floor(q.min(0)).astype(int); x1, y1 = np.ceil(q.max(0)).astype(int) + 1
    x0, y0 = max(0, x0), max(0, y0); x1, y1 = min(W, x1), min(H, y1)
    if x1 <= x0 or y1 <= y0: return
    th, tw = tex.shape[:2]
    M = cv2.getPerspectiveTransform(np.array([[0, 0], [tw, 0], [tw, th], [0, th]], np.float32), q - np.array([x0, y0], np.float32))
    out = cv2.warpPerspective(tex, M, (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR, borderValue=0)
    reg = dst[y0:y1, x0:x1]
    if mode == "add": reg += out * op
    elif mode == "over":
        a = cv2.warpPerspective(alpha if alpha is not None else np.ones(tex.shape[:2], np.float32), M, (x1 - x0, y1 - y0),
                                flags=cv2.INTER_LINEAR, borderValue=0) * op
        if out.ndim == 3: a = a[..., None]
        reg *= (1 - a); reg += out * a

_FT = {}
def ft(path, size):
    k = (path, int(size))
    if k not in _FT: _FT[k] = ImageFont.truetype(path, int(size))
    return _FT[k]

# ================================================================== the wall atlas (copied from In the Walls, + per-pixel paper)
U16 = 65000
def tq_(t): return np.uint16(min(U16, max(0, t) * 100))
class Atlas:
    """Everything ON or IN a camera's walls, drawn once in wall space with per-pixel reveal / erase times.
    g*: light leaking through the plaster (emissive). r*: paper on the wall (lit by the IR like the wall)."""
    def __init__(s, rid):
        rm = room(rid); s.aw, s.ah = max(8, rm["aw"]), max(8, rm["ah"]); s.slots = rm["slots"]
        sh = (s.ah, s.aw)
        s.g = np.zeros(sh, np.uint8); s.gt0 = np.full(sh, U16, np.uint16); s.gt1 = np.full(sh, U16, np.uint16)
        s.r = np.zeros(sh, np.uint8); s.rv = np.zeros(sh, np.uint8); s.rt0 = np.full(sh, U16, np.uint16); s.rt1 = np.full(sh, U16, np.uint16)
    def slot(s, wall):
        x0, y0, w, h, p = s.slots[wall]; return x0, y0, w, h, p.ppm
    def _region(s, wall, ah_, aw_, x, y):
        x0, y0, w, h, ppm = s.slot(wall)
        px = int(x0 + x * ppm); py = int(y0 + (h - y * ppm) - ah_)
        X0, Y0, X1, Y1 = max(px, x0), max(py, y0), min(px + aw_, x0 + w), min(py + ah_, y0 + h)
        return px, py, X0, Y0, X1, Y1
    def _times(s, px, py, aw_, ah_, X0, Y0, X1, Y1, t0, t1, sweep):
        if sweep == "x": fr = ((np.arange(X0, X1) - px) / max(1, aw_))[None, :].repeat(Y1 - Y0, 0)
        else: fr = ((np.arange(Y0, Y1) - py) / max(1, ah_))[:, None].repeat(X1 - X0, 1)
        return np.clip((t0 + (t1 - t0) * fr) * 100, 0, U16).astype(np.uint16)
    def glow(s, wall, a, x, y, t0, t1, erase=1e9):
        """a: uint8 light (wall px); x, y: bottom-left in metres. Reveal sweeps left -> right."""
        ah_, aw_ = a.shape; px, py, X0, Y0, X1, Y1 = s._region(wall, ah_, aw_, x, y)
        if X1 <= X0 or Y1 <= Y0: return
        sub = a[Y0 - py:Y1 - py, X0 - px:X1 - px]; tq = s._times(px, py, aw_, ah_, X0, Y0, X1, Y1, t0, t1, "x"); eq = tq_(erase)
        G, T0, T1 = s.g[Y0:Y1, X0:X1], s.gt0[Y0:Y1, X0:X1], s.gt1[Y0:Y1, X0:X1]
        m = sub > 10; upd = m & ((sub >= G) | (T1 < tq))
        G[upd] = sub[upd]; T0[upd] = tq[upd]; T1[upd] = eq
    def paper(s, wall, alpha, val, x, y, t0, t1, erase=1e9, sweep="y"):
        """alpha: uint8 coverage, val: uint8 IR reflectance per pixel (paper ~ 235, ink ~ 40). Prints top -> bottom."""
        ah_, aw_ = alpha.shape; px, py, X0, Y0, X1, Y1 = s._region(wall, ah_, aw_, x, y)
        if X1 <= X0 or Y1 <= Y0: return
        sa = alpha[Y0 - py:Y1 - py, X0 - px:X1 - px]; sv = val[Y0 - py:Y1 - py, X0 - px:X1 - px]
        tq = s._times(px, py, aw_, ah_, X0, Y0, X1, Y1, t0, t1, sweep); eq = tq_(erase)
        m = sa > 40
        s.r[Y0:Y1, X0:X1][m] = sa[m]; s.rv[Y0:Y1, X0:X1][m] = sv[m]
        s.rt0[Y0:Y1, X0:X1][m] = tq[m]; s.rt1[Y0:Y1, X0:X1][m] = eq
    def text(s, wall, txt, x, y, size, t0, t1=None, font=ROCK, rot=0.0, erase=1e9, gain=1.0, halo=True):
        """Glowing writing. x, y in metres from the wall's bottom-left; size ~ letter height in metres."""
        ppm = s.slot(wall)[4]
        fs = max(8, int(size * ppm * 1.5)); f = ft(font, fs)
        bb = f.getbbox(txt); pad = max(4, fs // 3)
        im = Image.new("L", (bb[2] - bb[0] + 2 * pad, bb[3] - bb[1] + 2 * pad), 0)
        ImageDraw.Draw(im).text((pad - bb[0], pad - bb[1]), txt, font=f, fill=255)
        a = np.asarray(im, np.float32)
        if halo: a = np.maximum(a, cv2.GaussianBlur(a, (0, 0), max(1.0, fs * 0.06)) * 0.45)
        if rot: a = _rot(a, rot)
        a = np.clip(a * gain, 0, 255).astype(np.uint8)
        s.glow(wall, a, x - pad / ppm, y - pad / ppm, t0, t0 + 0.04 if t1 is None else t1, erase)
        return (bb[2] - bb[0]) / ppm, (bb[3] - bb[1]) / ppm
    def frame(s, t):
        tq = tq_(t)
        vis = (s.gt0 <= tq) & (s.gt1 > tq)
        g = np.where(vis, s.g, 0).astype(np.uint8)
        fr = vis & (s.gt0 > tq_(t - 0.12))                        # fresh writing burns brighter for a moment
        if fr.any(): g = np.where(fr, np.minimum(255, s.g.astype(np.uint16) * 3 // 2).astype(np.uint8), g)
        rv = (s.rt0 <= tq) & (s.rt1 > tq)
        return g, np.where(rv, s.r, 0).astype(np.uint8), s.rv
    def save(s, p): np.savez(p, g=s.g, gt0=s.gt0, gt1=s.gt1, r=s.r, rv=s.rv, rt0=s.rt0, rt1=s.rt1)
    def load(s, p):
        z = np.load(p)
        for k in ("g", "gt0", "gt1", "r", "rv", "rt0", "rt1"): setattr(s, k, z[k])

def _rot(a, deg):
    M = cv2.getRotationMatrix2D((a.shape[1] / 2, a.shape[0] / 2), deg, 1.0)
    cs, sn = abs(M[0, 0]), abs(M[0, 1]); nw = int(a.shape[0] * sn + a.shape[1] * cs) + 2; nh = int(a.shape[0] * cs + a.shape[1] * sn) + 2
    M[0, 2] += nw / 2 - a.shape[1] / 2; M[1, 2] += nh / 2 - a.shape[0] / 2
    return cv2.warpAffine(a, M, (nw, nh), flags=cv2.INTER_LINEAR)

_ATL = {}
def atlas(rid, layer=1):
    """Layer 1: receipts + her answer. Layer 2 (living room only): 'Everything.', written over the same plaster."""
    k = (rid, layer)
    if k in _ATL: return _ATL[k]
    a = Atlas(rid); p = os.path.join(CACHE, f"atlas{layer}_{rid}_{_WHASH}.npz")
    try:
        a.load(p)
    except Exception:
        (WRITE if layer == 1 else WRITE2)[rid](a)
        tmp = p + f".{os.getpid()}.tmp.npz"; a.save(tmp); os.replace(tmp, p)
    _ATL[k] = a; return a

# ================================================================== writing
SUBS = ["CLAUDE MAX", "CHATGPT PRO", "GEMINI ADV", "SUNO PRO", "MIDJOURNEY", "CURSOR PRO", "X PREMIUM", "LINKEDIN PREM",
        "NOTION AI", "COPILOT", "PERPLEXITY", "RUNWAY", "ELEVENLABS", "CANVA PRO", "ADOBE CC", "SPOTIFY", "DUOLINGO MAX",
        "MASTERCLASS", "HEADSPACE", "ICLOUD 2TB", "GOOGLE ONE", "DROPBOX", "FIGMA", "FRAMER", "VERCEL PRO", "REPLIT",
        "LOVABLE", "KLING", "PIKA", "LUMA", "HIGGSFIELD", "GROK", "RAYCAST AI", "SUPERHUMAN", "WARP"]
PRICES = ["$20.00", "$200.00", "$19.99", "$10.00", "$30.00", "$8.00", "$9.99", "$24.00", "$39.99", "$15.00", "$100.00", "$12.00"]

_RC = {}
def receipt(k, ppm, w_m=0.20, h_m=0.32):
    """A printed subscription receipt, in wall pixels: (alpha uint8, IR value uint8). Paper bright, ink dark."""
    key = (k % 48, ppm, round(w_m, 3), round(h_m, 3))
    if key in _RC: return _RC[key]
    w = max(10, int(w_m * ppm)); h = max(16, int(h_m * ppm)); r = rng(1000 + k % 48)
    ss = 4 if w < 160 else 2                                           # supersample small ones so the ink reads
    W_, H_ = w * ss, h * ss
    a = Image.new("L", (W_, H_), 0); v = Image.new("L", (W_, H_), 0); da = ImageDraw.Draw(a); dv = ImageDraw.Draw(v)
    zz = max(3, W_ // 12); pts = [(0, 0), (W_ - 1, 0), (W_ - 1, H_ - zz)]
    for i in range(12, -1, -1): pts.append((i * (W_ - 1) / 12, H_ - 1 if i % 2 == 0 else H_ - zz))     # torn zig-zag foot
    da.polygon(pts, fill=255); dv.polygon(pts, fill=236)
    ink = 34; m = W_ * 0.09; y = H_ * 0.06
    name = SUBS[k % len(SUBS)]; price = PRICES[(k * 7) % len(PRICES)]
    f1 = ft(TYPEW, max(6, int(W_ * 0.115))); f2 = ft(TYPEW, max(6, int(W_ * 0.15))); f3 = ft(TYPEW, max(6, int(W_ * 0.085)))
    dv.text((W_ / 2, y), "RECEIPT", font=f1, fill=ink, anchor="ma"); y += W_ * 0.17
    dv.line((m, y, W_ - m, y), fill=110, width=max(1, W_ // 90)); y += W_ * 0.06
    dv.text((m, y), name[:12], font=f3, fill=ink); y += W_ * 0.13
    dv.text((m, y), "monthly", font=f3, fill=90); y += W_ * 0.15
    for _ in range(2):
        ww = (W_ - 2 * m) * r.uniform(0.45, 0.9); dv.line((m, y, m + ww, y), fill=150, width=max(1, W_ // 70)); y += W_ * 0.08
    y += W_ * 0.04; dv.line((m, y, W_ - m, y), fill=110, width=max(1, W_ // 90)); y += W_ * 0.05
    dv.text((W_ - m, y), price, font=f2, fill=ink, anchor="ra"); y += W_ * 0.22
    dv.text((m, y), "AUTO-RENEW", font=f3, fill=70); y += W_ * 0.14
    bx = m
    while bx < W_ - m and y < H_ - zz - W_ * 0.12:                     # barcode
        bw = max(1, int(W_ * r.choice([0.008, 0.016, 0.024]))); dv.rectangle((bx, y, bx + bw, y + W_ * 0.10), fill=30); bx += bw + max(1, int(W_ * 0.012))
    A = np.asarray(a.resize((w, h), Image.LANCZOS)); V = np.asarray(v.resize((w, h), Image.LANCZOS))
    _RC[key] = (A, V); return A, V

def _place_receipts(a, wall, n, t_lo, t_hi, seed, xr=None, yr=None, avoid=(), size=(0.15, 0.24), big=0.0, origin=None, rot=9.0):
    """n receipts slapped on a wall between t_lo and t_hi (a wave from `origin`), never inside an `avoid` box."""
    r = rng(seed); p = a.slots[wall][4]; ppm = a.slot(wall)[4]
    xr = xr or (0.0, p.U - 0.05); yr = yr or (0.05, p.V - 0.05)
    ox, oy = origin if origin else ((xr[0] + xr[1]) / 2, (yr[0] + yr[1]) / 2)
    items = []
    tries = 0
    while len(items) < n and tries < n * 8:
        tries += 1
        w_m = r.uniform(*size) * (1.6 if r.random() < big else 1.0); h_m = w_m * r.uniform(1.45, 1.75)
        x = r.uniform(xr[0] - w_m * 0.3, xr[1] - w_m * 0.7); y = r.uniform(yr[0] - h_m * 0.2, yr[1] - h_m * 0.8)
        if any(not (x + w_m < ax0 or x > ax1 or y + h_m < ay0 or y > ay1) for (ax0, ay0, ax1, ay1) in avoid): continue
        d = math.hypot(x + w_m / 2 - ox, y + h_m / 2 - oy); items.append((d, x, y, w_m, h_m))
    if not items: return
    dmax = max(it[0] for it in items) + 1e-6
    for j, (d, x, y, w_m, h_m) in enumerate(items):
        t0 = t_lo + (t_hi - t_lo) * ((d / dmax) * 0.75 + 0.25 * r.random())
        A, V = receipt(int(r.integers(0, 10 ** 6)), ppm, w_m, h_m)
        ang = r.normal(0, rot)
        if abs(ang) > 0.5: A = _rot(A.astype(np.float32), ang).astype(np.uint8); V = _rot(V.astype(np.float32), ang).astype(np.uint8)
        a.paper(wall, A, V, x, y, t0, t0 + 0.07)

T_FLOOD = T_EV + 0.02
TILE_DELAY = {"living": 0.0, "kitchen": 0.06, "basement": 0.06, "entry": 0.06, "hallway": 0.11, "bedroom": 0.11, "attic": 0.14}

def flood(a, rid, walls, seed):
    """'Everything.': every writable wall in the room papered with receipts in ~0.4 s."""
    d = TILE_DELAY.get(rid, 0.08)
    for k, (wall, n, kw) in enumerate(walls):
        _place_receipts(a, wall, n, T_FLOOD + d, T_FLOOD + d + 0.42, seed + k, **kw)

def _wall_w(a, wall, txt, size, font=ROCK):
    ppm = a.slot(wall)[4]; fs = max(8, int(size * ppm * 1.5)); bb = ft(font, fs).getbbox(txt); return (bb[2] - bb[0]) / ppm

# living-room back wall layout (metres from its bottom-left; the TV covers x 3.25-4.75, y 0.62-1.48)
SUB_SIZE = 0.185; EV_SIZE = 0.27; TXT_CX = 4.0; HAND = MARKER     # her handwriting: bold marker, legible at a glance
EV_BOX = (2.70, 1.50, 5.25, 2.30)

def write_living(a):
    # her answer comes through the plaster, in step with the words (I have a 82.10 · subscription. 82.40)
    wt = dict(zip(LSUB["words"], LSUB["wt"]))
    x2 = TXT_CX - _wall_w(a, "back", "subscription.", SUB_SIZE, HAND) / 2
    a.text("back", "I have a", x2 + 0.03, 2.05, SUB_SIZE, T_SUB - 0.03, wt["subscription."] - 0.05, font=HAND, rot=-1.5, erase=T_EV - 0.01, gain=0.9)
    a.text("back", "subscription.", x2, 1.69, SUB_SIZE, wt["subscription."] - 0.03, wt["subscription."] + 0.50, font=HAND, rot=-1.5, erase=T_EV - 0.01, gain=0.9)
    flood(a, "living", [("back", 170, dict(avoid=[EV_BOX, (3.2, 0.5, 4.8, 1.5)], origin=(4.0, 1.9))),
                        ("left", 150, dict(yr=(0.1, 2.5))), ("right", 160, dict(yr=(0.1, 2.5)))], 100)

def write_living2(a):
    # "Everything." replaces her answer, bigger (its own layer, so the two never fight over the same plaster)
    a.text("back", "Everything.", TXT_CX - _wall_w(a, "back", "Everything.", EV_SIZE, HAND) / 2, 1.70, EV_SIZE, T_EV - 0.01, T_EV + 0.30,
           font=HAND, rot=-2.5, gain=0.95)

def write_hallway(a):
    flood(a, "hallway", [("left", 170, dict(yr=(0.15, 2.4))), ("right", 170, dict(yr=(0.15, 2.4))), ("back", 25, dict(yr=(0.1, 2.4)))], 200)
def write_kitchen(a):
    flood(a, "kitchen", [("back", 90, dict(yr=(0.95, 2.5))), ("right", 110, dict()), ("left", 90, dict()),
                         ("fridge", 26, dict(size=(0.11, 0.17), origin=(0.42, 1.0), rot=6))], 300)
def write_bedroom(a):
    flood(a, "bedroom", [("back", 80, dict(yr=(1.25, 2.5))), ("right", 90, dict()), ("left", 110, dict())], 400)
def write_basement(a):
    # the board where In the Walls pinned its 200 impossible tasks: 200 receipts, in rows
    r = rng(5); ppm = a.slot("back")[4]; i = 0
    for row in range(16):
        for col in range(13):
            if i >= 200: break
            x = 0.12 + col * 0.10 + r.normal(0, 0.004); y = 1.80 - row * 0.096 + r.normal(0, 0.004)
            tt = T_FLOOD + 0.05 + 0.40 * (i / 200) ** 0.8
            A, V = receipt(i, ppm, 0.08, 0.088); a.paper("back", A, V, x, y, tt, tt + 0.05); i += 1
    flood(a, "basement", [("back", 40, dict(xr=(1.5, 3.7), yr=(1.6, 2.2))), ("right", 90, dict()), ("left", 50, dict(xr=(0.1, 2.5)))], 500)
def write_entry(a):
    flood(a, "entry", [("back", 70, dict()), ("left", 90, dict()), ("right", 80, dict())], 600)
def write_attic(a):
    flood(a, "attic", [("back", 90, dict(xr=(0.3, 4.6), yr=(0.1, 1.9))), ("roofL", 110, dict())], 700)

WRITE = {"living": write_living, "hallway": write_hallway, "kitchen": write_kitchen, "bedroom": write_bedroom,
         "basement": write_basement, "entry": write_entry, "attic": write_attic}
WRITE2 = {"living": write_living2}
# ================================================================== end writing

# ================================================================== the TV (Claude talks through it)
TV_C = (3.29, 1.44, 6.0 - 0.123); TV_EX = (1.42, 0, 0); TV_EY = (0, -0.78, 0)
def tv_on(t):
    return sstep(T_Q - 0.30, T_Q - 0.18, t) * (1.0 - 0.10 * (math.sin(t * 61) * math.sin(t * 23) > 0.6))

def _typed_words(words, t, lead=0.04):
    """Words appear letter by letter, each over its own sung time."""
    out = []
    for i, (w, tw) in enumerate(words):
        t1 = words[i + 1][1] if i + 1 < len(words) else tw + 0.55
        dur = max(0.08, min(0.5, t1 - tw))
        if i == 0: tw, dur = tw - 0.30, 0.26                 # "What" is already up on the first frame of the section
        if t < tw - lead: break
        n = len(w); k = clamp((t - tw + lead) / dur)
        out.append(w[:max(1, int(math.ceil(n * k)))])
        if k < 1: break
    return out

def tv_lines(t):
    if t < T_TO - 0.02:
        ws = _typed_words(Q_WORDS, t)
        l1 = " ".join(ws[:3]); l2 = ws[3] if len(ws) > 3 else ""
        return [l1, l2], (len(ws) < 4 or len(l2) < len("qualifications?"))
    s = C.typed("To what?", t, T_TO - 0.02, T_TO + 0.20)
    return [s, ""], len(s) < 8

_TVT = {}
def tv_tex(t, w=1100, h=604):
    """The TV screen as an RGB texture: near-black glass, amber text (Claude), a little scanline, a cursor."""
    lines, typing = tv_lines(t); cur = int(t * 2.6) % 2 == 0
    key = (tuple(lines), cur, w, h)
    if key in _TVT: return _TVT[key]
    im = Image.new("L", (w, h), 0); d = ImageDraw.Draw(im)
    big = t >= T_TO - 0.02
    fs = int(h * (0.36 if big else 0.262)); f = ft(VT, fs)
    x0 = int(w * 0.07); y0 = int(h * (0.27 if big else 0.19)); lh = int(fs * 0.98)
    last = (x0, y0)
    for i, s in enumerate(lines):
        if not s: continue
        d.text((x0, y0 + i * lh), s, font=f, fill=255); last = (x0 + f.getlength(s), y0 + i * lh)
    if cur:
        cx, cy = last; d.rectangle((cx + fs * 0.08, cy + fs * 0.18, cx + fs * 0.46, cy + fs * 0.80), fill=255)
    a = np.asarray(im, np.float32) / 255
    # the Claude spark, top left
    sp = np.zeros((h, w), np.float32); sx, sy, sr = int(w * 0.075 + h * 0.035), int(h * 0.085), int(h * 0.04)
    for k in range(4):
        ang = k * math.pi / 4
        cv2.line(sp, (int(sx - math.cos(ang) * sr), int(sy - math.sin(ang) * sr)), (int(sx + math.cos(ang) * sr), int(sy + math.sin(ang) * sr)), 1.0, max(2, h // 120), cv2.LINE_AA)
    a = np.maximum(a, sp * 0.9)
    glow = cv2.GaussianBlur(a, (0, 0), h * 0.012)
    rgb = np.zeros((h, w, 3), np.float32) + np.array([0.020, 0.016, 0.012], np.float32)
    rgb += glow[..., None] * AMBER * 0.55 + a[..., None] * (AMBER * 0.85 + AMBER_HOT * 0.15)
    scan = (0.90 + 0.10 * (np.arange(h) % 4 < 2)).astype(np.float32)[:, None, None]
    rgb *= scan
    if len(_TVT) > 60: _TVT.clear()
    _TVT[key] = rgb; return rgb

# ================================================================== a CCTV feed (single channel), then night vision
_NZ = {}
def noise_frames(W, H):
    k = (W, H)
    if k not in _NZ:
        r = rng(77); _NZ[k] = [r.normal(0, 1, (H // 2 + 1, W // 2 + 1)).astype(np.float32) for _ in range(8)]
    return _NZ[k]

def feed(cid, t, W, H, gain=0.72):
    """IR luminance of one camera: plate (walls kept dark so writing and paper read), TV wash, paper, light in the walls."""
    pl = plate(cid, W, H)
    img = F(pl["lum"]) * gain
    rid = CAMS[cid][3]
    lv = tv_on(t) if rid == "living" else 0.0
    if lv > 0.01:                                           # the TV's light on the room (IR sees it as a soft wash)
        img += F(pl["L_tv"]) * (0.05 * lv)
    at = atlas(rid)
    g, ra, rv = at.frame(t)
    if ra.any():
        rs = cv2.remap(ra, pl["amap1"], pl["amap2"], cv2.INTER_LINEAR, borderValue=0).astype(np.float32) / 255
        vs = cv2.remap(rv, pl["amap1"], pl["amap2"], cv2.INTER_LINEAR, borderValue=0).astype(np.float32) / 255
        img = img * (1 - rs) + rs * vs * F(pl["irr"]) * 1.45
    if rid in WRITE2 and t >= T_EV - 0.05:
        g = np.maximum(g, atlas(rid, 2).frame(t)[0])
    if g.any():
        gs = cv2.remap(g, pl["amap1"], pl["amap2"], cv2.INTER_LINEAR, borderValue=0).astype(np.float32) / 255
        img += gs * 1.0
    return img

def nightvision(img, fi, W, H, expo=1.0, noise=1.0):
    x = 1 - np.exp(-np.maximum(img, 0) * 2.15 * expo)
    sm = cv2.resize(x, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    bl = cv2.GaussianBlur(np.maximum(sm - 0.52, 0), (0, 0), max(2, W / 320))
    x = x + cv2.resize(bl, (W, H)) * 1.0
    nz = cv2.resize(noise_frames(W, H)[fi % 8], (W, H), interpolation=cv2.INTER_LINEAR)
    x = x + nz * noise * (0.026 + 0.04 * (1 - np.clip(x, 0, 1)))
    x = np.clip(x, 0, 1.15) ** 1.32                         # a little more contrast than In the Walls: no grey haze
    return NV_LO + (NV_HI - NV_LO) * x[..., None]

def zoom_M(z, cx, cy, W, H):
    cx = clamp(cx, 0.5 / z, 1 - 0.5 / z); cy = clamp(cy, 0.5 / z, 1 - 0.5 / z)
    return np.array([[z, 0, W / 2 - z * cx * W], [0, z, H / 2 - z * cy * H]], np.float32)

def tv_composite(img, t, cid, W, H, M=None):
    """Draw the TV screen (RGB, amber) onto the night-vision image, after any digital zoom M, plus its amber spill."""
    lv = tv_on(t)
    if lv <= 0.01: return
    q = wquad(cid, W, H, TV_C, TV_EX, TV_EY)
    if q is None: return
    if M is not None: q = q @ M[:, :2].T + M[:, 2]
    tex = tv_tex(t)
    Hh, Ww = img.shape[:2]
    lay = np.zeros((Hh, Ww, 3), np.float32); warp_quad(lay, tex, q, 1.0, mode="add")
    msk = np.zeros((Hh, Ww), np.float32); warp_quad(msk, np.ones(tex.shape[:2], np.float32), q, 1.0, mode="add")
    m = np.clip(msk, 0, 1)[..., None] * lv
    img *= (1 - m); img += lay * lv
    # amber light spilling onto the wall around the set (the only colour in the room)
    x0, y0 = q.min(0); x1, y1 = q.max(0); cx, cy = (x0 + x1) / 2, (y0 + y1) / 2; rw, rh = (x1 - x0), (y1 - y0)
    sw, sh = max(8, Ww // 8), max(8, Hh // 8)
    yy, xx = np.mgrid[0:sh, 0:sw].astype(np.float32); xx = xx * Ww / sw; yy = yy * Hh / sh
    sp = np.exp(-(((xx - cx) / (rw * 0.95)) ** 2 + ((yy - cy) / (rh * 1.1)) ** 2))
    sp = cv2.resize(sp, (Ww, Hh), interpolation=cv2.INTER_LINEAR)[..., None] * (1 - m)
    bright = 0.55 + 0.45 * min(1.0, len("".join(tv_lines(t)[0])) / 12)
    img += sp * AMBER * 0.075 * lv * bright

# ================================================================== OSD (In the Walls' DVR look)
def stamp(t):
    s = 3 * 3600 + 14 * 60 + 7.0 + (t - T_Q)
    s = int(s) % 86400
    return f"2026-11-08  {s // 3600:02d}:{(s // 60) % 60:02d}:{s % 60:02d}"

def osd(img, t, W, H, cam_label, room_label, extra=None, ts=None):
    ts = ts or min(W, H) / 1080
    fs = int(56 * ts); x = 58 * ts; y = 46 * ts
    for i, s in enumerate([cam_label + "  " + room_label, stamp(t)]):
        sp = sprite(s, VT, fs, 4); yy = y + i * fs * 0.95
        shadow(img, sp, x + 2 * ts, yy + 2 * ts, 0.9); blit(img, sp, x, yy, OSD_W, 0.95)
    if int((t - T_Q) * 1.25 + 0.2) % 2 == 0:
        rx = W - 196 * ts; ry = y + fs * 0.52
        cv2.circle(img, (int(rx), int(ry)), int(13 * ts), REC_RED.tolist(), -1, cv2.LINE_AA)
        sp = sprite("REC", VT, fs, 4); shadow(img, sp, rx + 28 * ts, y + 2 * ts, 0.9); blit(img, sp, rx + 26 * ts, y, OSD_W, 0.95)
    if extra:
        sp = sprite(extra, VT, fs, 4); xx = W - text_w(extra, VT, fs) - 58 * ts; yy = y + fs * 0.95
        shadow(img, sp, xx + 2 * ts, yy + 2 * ts, 0.9); blit(img, sp, xx, yy, OSD_W, 0.95)

def static_burst(img, W, H, fi, amt):
    if amt <= 0.01: return img
    r = rng(fi * 31 + 7); nz = r.random((H // 3, W // 3)).astype(np.float32)
    nz = cv2.resize(nz, (W, H), interpolation=cv2.INTER_NEAREST)[..., None]
    return img * (1 - amt) + nz * amt

# ================================================================== shots
PUSH = (T_Q - 0.4, T_TO - 0.02)               # slow PTZ push while they talk
def ptz_shot(t, W, H, fi):
    cid = "livptz"
    f = feed(cid, t, W, H)
    img = nightvision(f, fi, W, H)
    z = lerp(1.0, 1.07, ease_io((t - PUSH[0]) / (PUSH[1] - PUSH[0])))
    if t >= T_TO - 0.02:                        # "To what?": the camera jolts in (question and answer both stay in frame)
        u = (t - (T_TO - 0.02)) / 0.14
        z = 1.07 + 0.11 * ease_out(u) + 0.02 * math.sin(clamp(u) * math.pi)
    q = wquad(cid, W, H, TV_C, TV_EX, TV_EY); tc = q.mean(0)
    tx, ty = tc[0] / W, (tc[1] / H + 0.30) / 2  # between the set and the writing above it
    cx = lerp(0.5, tx, clamp((z - 1) * 3.2)); cy = lerp(0.5, ty, clamp((z - 1) * 3.2))
    M = zoom_M(z, cx, cy, W, H)
    if z > 1.001: img = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    tv_composite(img, t, cid, W, H, M if z > 1.001 else None)
    return img, ("ZOOM 3X" if t >= T_TO - 0.02 else "PTZ 2X")

# DVR "1+12" multiview: the living room big in the middle, twelve more cameras around it
LAYOUT = [(0, 0, "hallway"), (0, 1, "kitchen"), (0, 2, "bedroom"), (0, 3, "attic"), (1, 0, "livwide"), (1, 3, "fridge"),
          (2, 0, "board"), (2, 3, "entry"), (3, 0, "net"), (3, 1, "basement"), (3, 2, "keys"), (3, 3, "dome")]
def grid_geo(W, H):
    gap = max(2, W // 480); tw, th = (W - gap * 3) // 4, (H - gap * 3) // 4; tw -= tw % 2; th -= th % 2
    ox = (W - (tw * 4 + gap * 3)) // 2; oy = (H - (th * 4 + gap * 3)) // 2
    return gap, tw, th, ox, oy

def grid_shot(t, W, H, fi):
    out = np.zeros((H, W, 3), np.float32); gap, tw, th, ox, oy = grid_geo(W, H)
    ts = min(W, H) / 1080
    for i, (r_, c_, cid) in enumerate(LAYOUT):
        x0, y0 = ox + c_ * (tw + gap), oy + r_ * (th + gap)
        tile = nightvision(feed(cid, t, tw, th), fi + i, tw, th)
        out[y0:y0 + th, x0:x0 + tw] = tile
        lab = f"{CAMS[cid][1]} {CAMS[cid][2]}"; fs = max(16, int(30 * ts))
        sp = sprite(lab, VT, fs, 3); shadow(out, sp, x0 + 10 * ts + 2, y0 + 6 * ts + 2, 0.9); blit(out, sp, x0 + 10 * ts, y0 + 6 * ts, OSD_W, 0.9)
    cw, ch = 2 * tw + gap, 2 * th + gap; cw -= cw % 2; ch -= ch % 2
    x0, y0 = ox + tw + gap, oy + th + gap
    tile = nightvision(feed("livptz", t, cw, ch), fi + 20, cw, ch)
    tv_composite(tile, t, "livptz", cw, ch)
    out[y0:y0 + ch, x0:x0 + cw] = tile
    fs = int(40 * ts); lab = "CAM 01 LIVING RM"
    sp = sprite(lab, VT, fs, 3); shadow(out, sp, x0 + 16 * ts + 2, y0 + 10 * ts + 2, 0.9); blit(out, sp, x0 + 16 * ts, y0 + 10 * ts, OSD_W, 0.95)
    cv2.rectangle(out, (x0, y0), (x0 + cw - 1, y0 + ch - 1), (OSD_W * 0.55).tolist(), max(1, int(2 * ts)))     # selected channel
    return out

# ================================================================== frame
def render_frame(t, W=1920, H=1080):
    fi = int(round(t * 30)); ts = min(W, H) / 1080
    if t < T_EV - 0.01:
        img, extra = ptz_shot(t, W, H, fi)
        osd(img, t, W, H, "CAM 01", "LIVING RM", extra)
        cut = T_TO - 0.02
    else:
        img = grid_shot(t, W, H, fi)
        st = "DVR 16CH  " + stamp(t); fs = int(40 * ts)
        sp = sprite(st, VT, fs, 4); xx = W - text_w(st, VT, fs) - 22 * ts; yy = H - fs * 1.20
        shadow(img, sp, xx + 2, yy + 2, 0.9); blit(img, sp, xx, yy, OSD_W, 0.95)
        if int((t - T_Q) * 1.25 + 0.2) % 2 == 0:
            cv2.circle(img, (int(xx - 26 * ts), int(yy + fs * 0.52)), int(10 * ts), REC_RED.tolist(), -1, cv2.LINE_AA)
        cut = T_EV - 0.01
    since = t - cut
    gl = 0.38 * (1 - since / 0.10) if 0 <= since < 0.10 else 0.0          # In the Walls' cut: a couple of frames of tear
    if 0 <= since < 0.067: img = static_burst(img, W, H, fi, 0.20)
    fl = 0.0
    if 0 <= t - T_FLOOD < 0.5: fl = 0.35 * math.exp(-(t - T_FLOOD) * 8)          # the flood hits on the downbeat
    return C.finish(img, t, fi, 1e9, flash=fl, flash_col=np.array([0.92, 1.0, 0.92], np.float32), glitch_amt=gl, ca=0.0012)
