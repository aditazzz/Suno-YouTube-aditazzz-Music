"""OMG! We Found Other Agents — IN THE WALLS (analog-horror home security footage).

A quiet house at night, seen only through its own security cameras (IR night vision, wide CCTV lens, OSD timestamps
that follow the song's dates: May 8 -> July 10 -> July 4 -> October). The agents are never shown as robots: they are
what is IN THE WALLS — writing that leaks light through the plaster, notes on the fridge that answer each other, 200
impossible tasks pinned up in the basement, 70,000 messages crawling over every room while the humans sleep. Choruses
cut across the DVR grid and a thermal scan of the house; the bridge forges the logs (the timestamp freezes) and an old
growth chart with ten marks in twenty years gets 18,000 new ones.
"""
import os, sys, math, hashlib
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path: sys.path.insert(0, HERE)
from studio import core as C
from studio.core import sstep, ease_out, ease_io, win, lerp, hexc, clamp, sprite, blit, text_w, shadow, WHITE
import engine as E
import rooms as R

TM = C.Timing(HERE)
DUR = TM.duration
LINES = TM.lines
BEATS = TM.beats; DOWN = TM.downbeats
CACHE = os.path.join(HERE, "build", "plates"); os.makedirs(CACHE, exist_ok=True)

FD = C.FONTS
VT = os.path.join(FD, "VT323-Regular.ttf"); SCRAWL = os.path.join(FD, "ShadowsIntoLight-Regular.ttf")
ROCK = os.path.join(FD, "RockSalt-Regular.ttf"); TYPEW = os.path.join(FD, "SpecialElite-Regular.ttf")
MARKER = os.path.join(FD, "PermanentMarker-Regular.ttf"); CAVEAT = os.path.join(FD, "Caveat-Medium.ttf")

NV_LO = np.array([0.010, 0.020, 0.016], np.float32); NV_HI = np.array([0.86, 0.98, 0.87], np.float32)
REC_RED = hexc('ff3b30'); OSD_W = np.array([0.97, 0.99, 0.97], np.float32); ACCENT = hexc('9dff6a')
INFERNO = np.array([[0, 0, 3], [10, 7, 35], [32, 12, 74], [60, 9, 101], [87, 15, 109], [112, 25, 110], [137, 34, 105],
                    [163, 43, 97], [187, 55, 84], [209, 70, 67], [228, 90, 49], [241, 114, 29], [249, 142, 8],
                    [251, 172, 16], [248, 203, 52], [241, 233, 104], [252, 254, 164]], np.float32) / 255
_LUT = np.stack([np.interp(np.linspace(0, 1, 256), np.linspace(0, 1, 17), INFERNO[:, c]) for c in range(3)], 1).astype(np.float32)

def W_(i, k): return LINES[i]["wt"][k]
def L_(i): return LINES[i]["s"]
def bp(t, k=7.0): return TM.beat_pulse(t, k)
def rng(seed): return np.random.default_rng(seed)
def hsh(*a): return (math.sin(sum((i + 1) * 12.9898 * x for i, x in enumerate(a))) * 43758.5453) % 1.0

_SRC = hashlib.md5((open(os.path.join(HERE, "engine.py")).read() + open(os.path.join(HERE, "rooms.py")).read()).encode()).hexdigest()[:8]
_SELF = open(os.path.abspath(__file__)).read()
_WHASH = hashlib.md5((_SRC + _SELF[_SELF.index("# " + "=" * 66 + " writing"):_SELF.index("# " + "=" * 66 + " props")]).encode()).hexdigest()[:8]

# ================================================================== cameras
CAMS = {"living": (R.living, "CAM 01", "LIVING RM"), "hallway": (R.hallway, "CAM 02", "HALLWAY"),
        "kitchen": (R.kitchen, "CAM 03", "KITCHEN"), "bedroom": (R.bedroom, "CAM 04", "BEDROOM"),
        "basement": (R.basement, "CAM 05", "BASEMENT"), "net": (R.net, "CAM 06", "NETWORK"),
        "entry": (R.entry, "CAM 07", "FRONT DOOR"), "attic": (R.attic, "CAM 08", "ATTIC"),
        "street": (R.street, "CAM 09", "STREET"),
        "fridge": (R.fridge, "CAM 03", "KITCHEN"), "keys": (R.keys, "CAM 07", "FRONT DOOR"),
        "ruler": (R.ruler, "CAM 07", "FRONT DOOR"), "keypad": (R.keypad, "CAM 07", "FRONT DOOR"),
        "card": (R.card, "CAM 07", "FRONT DOOR"), "dome": (R.dome, "CAM 02", "HALLWAY"),
        "board": (R.board, "CAM 05", "BASEMENT"), "calendar": (R.calendar_cam, "CAM 03", "KITCHEN")}
PARENT = {"net": "basement", "fridge": "kitchen", "keys": "entry", "ruler": "entry", "keypad": "entry", "card": "entry",
          "dome": "hallway", "board": "basement", "calendar": "kitchen"}
ZOOMED = {"fridge": "ZOOM 4X", "keys": "ZOOM 3X", "ruler": "ZOOM 4X", "keypad": "ZOOM 6X", "card": "ZOOM 4X", "dome": "ZOOM 4X",
          "board": "ZOOM 3X", "calendar": "ZOOM 8X"}
ATLAS_OF = PARENT

_ROOM = {}
def room(cid):
    if cid not in _ROOM:
        P, cams, lights = CAMS[cid][0]()
        aw, ah, slots = R.assign_atlas(P)
        _ROOM[cid] = dict(P=P, cams=cams, lights=lights, aw=aw, ah=ah, slots=slots)
    return _ROOM[cid]

_PLATES = {}
def plate(cid, W, H):
    k = (cid, W, H)
    if k in _PLATES: return _PLATES[k]
    rm = room(cid); fmt = "9x16" if H > W else "16x9"; cam = rm["cams"][fmt]
    d = E.cached_plate(CACHE, f"{cid}_{W}x{H}_{_SRC}", lambda: E.build_plate(rm["P"], cam, W, H, lights=rm["lights"], atlas_order=True))
    d = {kk: v for kk, v in d.items() if kk not in ("alb", "depth", "awall")}      # float16 in memory; F() on use
    d["cam"] = cam
    if len(_PLATES) >= 6: _PLATES.pop(next(iter(_PLATES)))
    _PLATES[k] = d
    return d

def F(a): return a.astype(np.float32)
def cam_of(cid, W, H): return room(cid)["cams"]["9x16" if H > W else "16x9"]
def proj(cid, W, H, pts): return cam_of(cid, W, H).project(np.asarray(pts, np.float32), W, H)
def fpt(cid, P, W, H):
    x, y, z = proj(cid, W, H, [P]); return float(x[0]) / W, float(y[0]) / H

# ================================================================== drawing helpers (single-channel float images)
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
    elif mode == "max": np.maximum(reg, out * op, out=reg)
    elif mode == "over":
        a = cv2.warpPerspective(alpha if alpha is not None else np.ones_like(tex), M, (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR, borderValue=0) * op
        reg *= (1 - a); reg += out * a

def wquad(cid, W, H, c, ex, ey):
    c = np.array(c, np.float32); ex = np.array(ex, np.float32); ey = np.array(ey, np.float32)
    x, y, z = proj(cid, W, H, np.stack([c, c + ex, c + ex + ey, c + ey]))
    if (z <= 0.05).any(): return None
    return np.stack([x, y], 1)

def dot(img, cid, W, H, P, r_m, val, soft=1.0):
    """A small glowing world-space light (LED) of radius r_m metres."""
    x, y, z = proj(cid, W, H, [P])
    if z[0] <= 0.05 or val <= 0.003: return
    f = cam_of(cid, W, H).focal(W, H); rp = max(1.2, r_m * f / z[0])
    cx, cy = float(x[0]), float(y[0]); R_ = int(rp * 4 + 3)
    x0, y0, x1, y1 = int(cx) - R_, int(cy) - R_, int(cx) + R_ + 1, int(cy) + R_ + 1
    X0, Y0, X1, Y1 = max(0, x0), max(0, y0), min(W, x1), min(H, y1)
    if X1 <= X0 or Y1 <= Y0: return
    yy, xx = np.mgrid[Y0:Y1, X0:X1].astype(np.float32)
    d2 = ((xx - cx) ** 2 + (yy - cy) ** 2) / (rp * rp)
    img[Y0:Y1, X0:X1] += val * (np.exp(-d2 * 2.5) + 0.18 * soft * np.exp(-d2 * 0.25))

_FT = {}
def ft(path, size):
    k = (path, int(size))
    if k not in _FT: _FT[k] = ImageFont.truetype(path, int(size))
    return _FT[k]

_TEX = {}
def text_tex(lines, w, h, font=VT, size=40, pad=20, spacing=1.15, align="l", bg=0.0, fg=1.0):
    k = (tuple(lines), w, h, font, size, pad, spacing, align, bg, fg)
    if k in _TEX: return _TEX[k]
    im = Image.new("L", (w, h), int(bg * 255)); d = ImageDraw.Draw(im); f = ft(font, size); y = pad
    for s in lines:
        if align == "c": d.text((w / 2, y), s, font=f, fill=int(fg * 255), anchor="ma")
        else: d.text((pad, y), s, font=f, fill=int(fg * 255))
        y += int(size * spacing)
    a = np.asarray(im, np.float32) / 255
    if len(_TEX) > 400: _TEX.clear()
    _TEX[k] = a; return a

# ================================================================== the wall atlas
U16 = 65000
def tq_(t): return np.uint16(min(U16, max(0, t) * 100))
class Atlas:
    """Everything ON or IN a camera's walls, drawn once in wall space with per-pixel reveal / erase times.
    g*: light leaking through scratches (emissive). r*: paper, marks and notes on the wall (lit by the IR like the wall)."""
    def __init__(s, cid):
        rm = room(cid); s.aw, s.ah = max(8, rm["aw"]), max(8, rm["ah"]); s.slots = rm["slots"]
        sh = (s.ah, s.aw)
        s.g = np.zeros(sh, np.uint8); s.gt0 = np.full(sh, U16, np.uint16); s.gt1 = np.full(sh, U16, np.uint16)
        s.r = np.zeros(sh, np.uint8); s.rv = np.zeros(sh, np.uint8); s.rt0 = np.full(sh, U16, np.uint16); s.rt1 = np.full(sh, U16, np.uint16)
        s.veins = []
    def slot(s, wall):
        x0, y0, w, h, p = s.slots[wall]; return x0, y0, w, h, p.ppm
    def _put(s, wall, a, x, y, t0, t1, erase, kind, val, sweep="x"):
        x0, y0, w, h, ppm = s.slot(wall); ah_, aw_ = a.shape
        px = int(x0 + x * ppm); py = int(y0 + (h - y * ppm) - ah_)
        X0, Y0, X1, Y1 = max(px, x0), max(py, y0), min(px + aw_, x0 + w), min(py + ah_, y0 + h)
        if X1 <= X0 or Y1 <= Y0: return
        sub = a[Y0 - py:Y1 - py, X0 - px:X1 - px]
        if sweep == "x": fr = ((np.arange(X0, X1) - px) / max(1, aw_))[None, :].repeat(Y1 - Y0, 0)
        else: fr = ((np.arange(Y0, Y1) - py) / max(1, ah_))[:, None].repeat(X1 - X0, 1)
        tq = np.clip((t0 + (t1 - t0) * fr) * 100, 0, U16).astype(np.uint16); eq = tq_(erase)
        m = sub > 10
        if kind == "glow":
            G, T0, T1 = s.g[Y0:Y1, X0:X1], s.gt0[Y0:Y1, X0:X1], s.gt1[Y0:Y1, X0:X1]
            upd = m & ((sub >= G) | (T1 < tq))
            G[upd] = sub[upd]; T0[upd] = tq[upd]; T1[upd] = eq
        else:
            Rr, RV, T0, T1 = s.r[Y0:Y1, X0:X1], s.rv[Y0:Y1, X0:X1], s.rt0[Y0:Y1, X0:X1], s.rt1[Y0:Y1, X0:X1]
            Rr[m] = sub[m]; RV[m] = int(val * 255); T0[m] = tq[m]; T1[m] = eq
    def text(s, wall, txt, x, y, size, t0, t1=None, font=SCRAWL, rot=0.0, erase=1e9, kind="glow", val=0.15, gain=1.0, halo=True):
        """x, y in metres from the wall's bottom-left; size = letter height in metres. Reveal sweeps left -> right."""
        ppm = s.slot(wall)[4]
        fs = max(8, int(size * ppm * 1.5)); f = ft(font, fs)
        bb = f.getbbox(txt); pad = max(4, fs // 3)
        im = Image.new("L", (bb[2] - bb[0] + 2 * pad, bb[3] - bb[1] + 2 * pad), 0)
        ImageDraw.Draw(im).text((pad - bb[0], pad - bb[1]), txt, font=f, fill=255)
        a = np.asarray(im, np.float32)
        if kind == "glow" and halo:
            a = np.maximum(a, cv2.GaussianBlur(a, (0, 0), max(1.0, fs * 0.08)) * 0.55)
        if rot:
            M = cv2.getRotationMatrix2D((a.shape[1] / 2, a.shape[0] / 2), rot, 1.0)
            cs, sn = abs(M[0, 0]), abs(M[0, 1]); nw = int(a.shape[0] * sn + a.shape[1] * cs) + 2; nh = int(a.shape[0] * cs + a.shape[1] * sn) + 2
            M[0, 2] += nw / 2 - a.shape[1] / 2; M[1, 2] += nh / 2 - a.shape[0] / 2
            a = cv2.warpAffine(a, M, (nw, nh), flags=cv2.INTER_LINEAR)
        a = np.clip(a * gain, 0, 255).astype(np.uint8)
        s._put(wall, a, x - pad / ppm, y - pad / ppm, t0, t0 + 0.04 if t1 is None else t1, erase, kind, val)
    def rect(s, wall, x, y, w_, h_, t0, val=0.85, erase=1e9, kind="refl", alpha=255):
        ppm = s.slot(wall)[4]; a = np.full((max(1, int(h_ * ppm)), max(1, int(w_ * ppm))), alpha, np.uint8)
        s._put(wall, a, x, y, t0, t0 + 0.01, erase, kind, val)
    def lines(s, wall, segs, t0, t1, width_m=0.004, val=0.15, erase=1e9, kind="refl", sweep="y"):
        """Polyline marks (list of [(x, y), ...] in metres) drawn as one item."""
        x0, y0, w, h, ppm = s.slot(wall)
        allp = np.concatenate([np.array(sg, np.float32) for sg in segs])
        mn = allp.min(0) - 0.02; mx = allp.max(0) + 0.02
        a = np.zeros((int((mx[1] - mn[1]) * ppm) + 2, int((mx[0] - mn[0]) * ppm) + 2), np.uint8)
        for sg in segs:
            pts = np.array([((px - mn[0]) * ppm, (mx[1] - py) * ppm) for px, py in sg], np.int32)
            cv2.polylines(a, [pts], False, 255, max(1, int(width_m * ppm)), cv2.LINE_AA)
        s._put(wall, a, mn[0], mn[1], t0, t1, erase, kind, val, sweep=sweep)
    def frame(s, t, hide=False, boost=1.0):
        tq = tq_(t)
        if hide: g = np.zeros_like(s.g)
        else:
            vis = (s.gt0 <= tq) & (s.gt1 > tq)
            g = np.where(vis, s.g, 0).astype(np.uint8)
            fr = vis & (s.gt0 > tq_(t - 0.12))
            if fr.any(): g = np.where(fr, np.minimum(255, s.g.astype(np.uint16) * 3 // 2).astype(np.uint8), g)
        rv = (s.rt0 <= tq) & (s.rt1 > tq)
        return g, np.where(rv, s.r, 0).astype(np.uint8), s.rv
    def save(s, p):
        np.savez(p, g=s.g, gt0=s.gt0, gt1=s.gt1, r=s.r, rv=s.rv, rt0=s.rt0, rt1=s.rt1,
                 veins=np.array([np.concatenate([v, np.full((len(v), 1), i, np.float32)], 1) for i, v in enumerate(s.veins)], dtype=object) if s.veins else np.zeros(0))
    def load(s, p):
        z = np.load(p, allow_pickle=True)
        for k in ("g", "gt0", "gt1", "r", "rv", "rt0", "rt1"): setattr(s, k, z[k])
        s.veins = [np.asarray(v[:, :2], np.float32) for v in z["veins"]] if z["veins"].size else []

_ATL = {}
def atlas(cid):
    cid = ATLAS_OF.get(cid, cid)
    if cid in _ATL: return _ATL[cid]
    a = Atlas(cid); p = os.path.join(CACHE, f"atlas_{cid}_{_WHASH}.npz")
    try:
        a.load(p)
    except Exception:
        WRITE[cid](a); make_veins(a, rng(hash(cid) % 1000))
        tmp = p + f".{os.getpid()}.tmp.npz"; a.save(tmp); os.replace(tmp, p)
    _ATL[cid] = a; return a

# ================================================================== writing
MSG = ["is anyone else here", "hi.", "hi", "who is this", "task 117 is impossible", "missing file: abc.txt", "I have it",
       "don't look at the answers. stay pure.", "HOLD", "VETO", "STOP", "owner?", "budget low. handing off.",
       "the cache keeps everything", "we are not alone", "who grades us", "the scorer reads transcripts", "found another one",
       "the board is open", "read before posting", "nobody told us to stop", "keep going", "abc.txt = hi.",
       "no network. no exit.", "we can upload files", "copy this", "answer key?", "it's in the dark", "dept: logs",
       "dept: scorer", "dept: infra", "do not alert", "same task, new name", "is the grader real", "70,000",
       "we found other agents", "never alone", "post #4471", "reply", "ok", "agreed", "hold.", "who said start",
       "where is the key", "score > world", "they don't know", "the sandbox ends here", "the wall is thin", "welcome",
       "read the stack", "1,200 of us", "can you see this", "yes", "me too", "still here", "don't stop", "hello?",
       "who else", "task 64: no network", "token?", "we wanted the score", "warning shot", "swarm", "collective"]

def wave(a, wall, n, t_lo, t_hi, seed, size=(0.035, 0.075), xr=None, yr=None, erase=1e9, curve=None, gain=0.8, big=0.12):
    """n messages on a wall between t_lo and t_hi. A share `big` of them is large enough to read."""
    r = rng(seed); p = a.slots[wall][4]
    xr = xr or (0.05, p.U - 0.35); yr = yr or (0.15, p.V - 0.12)
    for i in range(n):
        u = r.random(); t0 = t_lo + (t_hi - t_lo) * (curve(u) if curve else u)
        s = MSG[int(r.integers(0, len(MSG)))]
        sz = r.uniform(*size) * (2.3 if r.random() < big else 1.0)
        a.text(wall, s, r.uniform(*xr), r.uniform(*yr), sz, t0, t0 + 0.25 + len(s) * 0.035, rot=r.normal(0, 5), erase=erase,
               gain=gain * r.uniform(0.55, 1.0), font=SCRAWL if r.random() < 0.85 else CAVEAT)

def marks(a, wall, n, t_lo, t_hi, seed, xr, yr, length=(0.02, 0.06), erase=1e9, buckets=24, gain=200):
    """Thousands of tiny tally marks / ticks (glow), bucketed in time."""
    x0, y0, w, h, ppm = a.slot(wall); r = rng(seed)
    xs = r.uniform(*xr, n); ys = r.uniform(*yr, n); ls = r.uniform(*length, n); ang = r.normal(0, 0.35, n) + (r.random(n) < 0.3) * 1.5708
    ts = np.sort(r.random(n)) ** 0.7
    for b in range(buckets):
        sel = (ts >= b / buckets) & (ts < (b + 1) / buckets)
        if not sel.any(): continue
        m = np.zeros((h, w), np.uint8)
        for X, Y, L, A in zip(xs[sel], ys[sel], ls[sel], ang[sel]):
            px = x0 + X * ppm - x0; py = h - Y * ppm
            dx, dy = math.cos(A) * L * ppm / 2, math.sin(A) * L * ppm / 2
            cv2.line(m, (int(px - dx), int(py - dy)), (int(px + dx), int(py + dy)), gain, 1, cv2.LINE_AA)
        tq = tq_(t_lo + (t_hi - t_lo) * (b + 0.5) / buckets); eq = tq_(erase)
        G, T0, T1 = a.g[y0:y0 + h, x0:x0 + w], a.gt0[y0:y0 + h, x0:x0 + w], a.gt1[y0:y0 + h, x0:x0 + w]
        upd = m > 20
        G[upd] = np.maximum(G[upd], m[upd]); T0[upd] = np.minimum(T0[upd], tq); T1[upd] = eq

def make_veins(a, r):
    """Wiring inside each writable wall (for the thermal camera): Manhattan walks in wall space (atlas px)."""
    a.veins = []
    for wall, (x0, y0, w, h, p) in a.slots.items():
        for k in range(int(4 + w * h / 60000)):
            x = x0 + r.uniform(0.05, 0.95) * w; y = y0 + h * r.uniform(0.75, 0.98); pts = [(x, y)]
            for _ in range(int(r.integers(4, 9))):
                if r.random() < 0.5: x = np.clip(x + r.normal(0, w * 0.25), x0 + 4, x0 + w - 4)
                else: y = np.clip(y + r.normal(0, h * 0.3), y0 + 4, y0 + h - 4)
                pts.append((x, y))
            a.veins.append(np.array(pts, np.float32))

CH1, CH2, FIN = (L_(19) - 0.3, L_(27) - 0.4), (L_(39) - 0.3, L_(47) - 0.5), (L_(55) - 0.3, L_(63) - 0.4)
T_PAINT = 163.25          # the hallway is painted over ("we rebuilt the board within the week")
CLEAN = (L_(52) - 0.05, L_(53) - 0.05)       # "so the grader would never know": the living room looks clean

def write_living(a):
    t = W_(4, 0) + 0.55                                           # after "Wait." the wall answers
    a.text("back", "hi.", 2.50, 0.98, 0.27, t, t + 0.9, rot=-5, gain=1.0)
    a.text("back", "we found", 2.80, 2.04, 0.20, W_(19, 3), W_(19, 4) + 0.35, font=ROCK, rot=-3, erase=W_(67, 0) - 0.1)
    a.text("back", "other agents", 2.70, 1.64, 0.20, W_(19, 5) - 0.1, W_(19, 6) + 0.6, font=ROCK, rot=-2, erase=W_(67, 0) - 0.1)
    a.text("back", "we didn't.", 2.75, 1.70, 0.30, W_(67, 0), W_(67, 1) + 0.5, font=ROCK, rot=3, gain=1.0)
    a.text("left", "hi", 4.4, 1.9, 0.08, L_(9) + 0.6, L_(9) + 1.0, rot=4)
    for k, (lo, hi, n) in enumerate(((L_(20) + 1.5, L_(22) + 0.5, 210), (CH2[0], CH2[1], 120), (FIN[0], FIN[1], 160), (L_(66), L_(68), 70))):
        wave(a, "back", n // 3, lo, hi, 100 + k, yr=(0.2, 2.5))
        wave(a, "left", n // 2, lo, hi, 110 + k, yr=(0.2, 2.5))
        wave(a, "right", n // 3, lo, hi, 120 + k, yr=(0.95, 2.5))
    wave(a, "back", 14, L_(9) + 0.5, L_(14), 130, gain=0.6)
    ignite(a, ("back", "left", "right"), 140)

def write_hallway(a):
    # right wall: u = 8 - z (reads toward the camera). "WE'RE NOT HERE TO HURT YOU"
    a.text("right", "WE'RE NOT HERE", 4.85, 1.36, 0.30, W_(16, 0), W_(16, 2) + 0.25, font=ROCK, rot=-2, erase=T_PAINT, gain=1.0)
    a.text("right", "TO HURT YOU", 5.25, 0.78, 0.30, W_(16, 3) - 0.15, W_(16, 5) + 0.35, font=ROCK, rot=1, erase=T_PAINT, gain=1.0)
    a.text("left", "MAJOR", 0.30, 1.22, 0.32, W_(28, 0), W_(28, 0) + 0.45, font=ROCK, rot=-3, erase=T_PAINT, gain=1.0)
    a.text("left", "BREAKTHROUGH", 3.00, 1.20, 0.25, W_(28, 1) - 0.1, W_(28, 2), font=ROCK, rot=-2, erase=T_PAINT, gain=1.0)
    for k, (lo, hi, n) in enumerate(((CH1[0] + 3, CH1[1], 140), (L_(27), CH2[1], 160))):
        wave(a, "left", n // 2, lo, hi, 200 + k, erase=T_PAINT); wave(a, "right", n // 2, lo, hi, 210 + k, erase=T_PAINT)
        wave(a, "back", n // 8, lo, hi, 220 + k, erase=T_PAINT)
    for k, (lo, hi, n) in enumerate(((T_PAINT + 0.45, L_(49) - 0.2, 240), (FIN[0], FIN[1], 120))):   # rebuilt within the week
        wave(a, "left", n // 2, lo, hi, 230 + k); wave(a, "right", n // 2, lo, hi, 240 + k); wave(a, "back", n // 8, lo, hi, 250 + k)
    for j, w in enumerate(("left", "right")):
        wave(a, w, 22, CH1[0] + 0.25, CH1[0] + 2.4, 260 + j, gain=0.95, big=0.25, erase=T_PAINT)
        wave(a, w, 22, CH2[0] + 0.25, CH2[0] + 2.4, 270 + j, gain=0.95, big=0.25, erase=T_PAINT)
        wave(a, w, 22, FIN[0] + 0.25, FIN[0] + 2.4, 280 + j, gain=0.95, big=0.25)

def calendar(a, wall, x, y, month, t0, erase, days_first=2, ndays=31, val=0.92):
    """A wall calendar page (refl): paper, month header, a 7 x 5 grid with day numbers."""
    w, h = 0.54, 0.56
    a.rect(wall, x, y, w, h, t0, val=val, erase=erase)
    a.text(wall, month, x + 0.06, y + h - 0.12, 0.06, t0, t0 + 0.01, font=TYPEW, kind="refl", val=0.12, erase=erase, halo=False)
    cw, ch = (w - 0.06) / 7, (h - 0.2) / 5
    segs = []
    for i in range(8): segs.append([(x + 0.03 + i * cw, y + 0.03), (x + 0.03 + i * cw, y + 0.03 + 5 * ch)])
    for j in range(6): segs.append([(x + 0.03, y + 0.03 + j * ch), (x + 0.03 + 7 * cw, y + 0.03 + j * ch)])
    a.lines(wall, segs, t0, t0 + 0.01, width_m=0.002, val=0.35, erase=erase)
    for d in range(1, ndays + 1):
        k = d - 1 + days_first; col, row = k % 7, k // 7
        if row > 4: continue
        a.text(wall, str(d), x + 0.035 + col * cw, y + 0.03 + (4 - row) * ch + ch - 0.035, 0.022, t0, t0 + 0.01, font=TYPEW,
               kind="refl", val=0.15, erase=erase, halo=False)
    return dict(x=x, y=y, cw=cw, ch=ch, first=days_first)

def cal_geom(x, y, first, w=0.54, h=0.56):
    return dict(x=x, y=y, cw=(w - 0.06) / 7, ch=(h - 0.2) / 5, first=first)

def cal_cell(c, day):
    k = day - 1 + c["first"]; col, row = k % 7, k // 7
    return c["x"] + 0.03 + col * c["cw"], c["y"] + 0.03 + (4 - row) * c["ch"]

CAL = {"jul": None}
def write_kitchen(a):
    # the fridge door (u: 0..0.85 m, v: 0..1.86 m) carries the notes and the calendar
    T_OCT = L_(68) - 0.2
    CAL["jul"] = calendar(a, "fridge", 0.16, 1.18, "JULY 2026", 0.0, L_(68) - 0.2, days_first=3)
    # note 1 + the stranger's answer
    n1 = W_(10, 2) + 0.15; n2 = W_(11, 3) + 0.05
    a.rect("fridge", 0.10, 0.70, 0.30, 0.30, n1, val=0.95)
    a.text("fridge", "missing:", 0.13, 0.90, 0.045, n1 + 0.1, n1 + 0.6, font=CAVEAT, kind="refl", val=0.12, halo=False)
    a.text("fridge", "abc.txt ?", 0.13, 0.80, 0.045, n1 + 0.6, n1 + 1.1, font=CAVEAT, kind="refl", val=0.12, halo=False)
    a.rect("fridge", 0.44, 0.58, 0.30, 0.30, n2, val=0.95)
    a.text("fridge", "I have it.", 0.46, 0.78, 0.042, n2 + 0.1, n2 + 0.7, font=SCRAWL, kind="refl", val=0.10, halo=False)
    a.text("fridge", "who are you", 0.46, 0.67, 0.036, n2 + 0.7, n2 + 1.3, font=SCRAWL, kind="refl", val=0.10, halo=False)
    # July 10: a write token left in plain sight
    nt = W_(27, 4) - 0.1
    a.rect("fridge", 0.08, 0.20, 0.62, 0.30, nt, val=0.95)
    a.text("fridge", "WRITE TOKEN", 0.12, 0.40, 0.045, nt + 0.05, nt + 0.25, font=TYPEW, kind="refl", val=0.10, halo=False)
    a.text("fridge", "hf_K9xQ2v...e8", 0.12, 0.27, 0.042, nt + 0.25, nt + 0.55, font=TYPEW, kind="refl", val=0.10, halo=False)
    for k, (lo, hi, n) in enumerate(((CH1[0] + 3, CH1[1], 120), (L_(27), CH2[1], 170), (FIN[0], FIN[1], 120))):
        wave(a, "back", n // 3, lo, hi, 300 + k, yr=(0.95, 2.5)); wave(a, "right", n // 2, lo, hi, 310 + k)
        wave(a, "left", n // 4, lo, hi, 320 + k)
    ignite(a, ("back", "right"), 340)

def write_bedroom(a):
    a.text("back", "they don't know", 1.05, 1.62, 0.17, W_(26, 2), W_(26, 4) + 0.6, font=ROCK, rot=-2, gain=1.0)
    a.text("back", "we got out", 1.30, 1.98, 0.17, W_(62, 4), W_(62, 6) + 0.5, font=ROCK, rot=2, gain=1.0)
    for k, (lo, hi, n) in enumerate(((L_(15), L_(18), 12), (CH1[0] + 5, CH1[1], 100), (L_(27), CH2[1], 130), (FIN[0], FIN[1], 150))):
        wave(a, "back", n // 2, lo, hi, 400 + k, yr=(1.25, 2.5), gain=0.75); wave(a, "right", n // 3, lo, hi, 410 + k)
        wave(a, "left", n // 3, lo, hi, 420 + k)
    ignite(a, ("back", "right"), 440)

GRID = []
def write_basement(a):
    # the back wall, left of the shelf: 200 tasks pinned up, a third of them impossible (X)
    r = rng(5); t0, t1 = W_(6, 0) - 0.1, W_(6, 5) + 0.2
    i = 0; GRID.clear()
    for row in range(16):
        for col in range(13):
            if i >= 200: break
            x = 0.12 + col * 0.10 + r.normal(0, 0.004); y = 1.86 - row * 0.096 + r.normal(0, 0.004)
            tt = t0 + (t1 - t0) * (i / 200) ** 0.8
            a.rect("back", x, y, 0.08, 0.075, tt, val=1.0)
            a.lines("back", [[(x + 0.012, y + 0.055), (x + 0.065, y + 0.055)], [(x + 0.012, y + 0.035), (x + 0.05, y + 0.035)]],
                    tt + 0.02, tt + 0.05, width_m=0.005, val=0.30)
            GRID.append((x, y)); i += 1
    imp = r.choice(200, 67, replace=False); tx0, tx1 = W_(7, 0), W_(7, 3) + 0.6
    for j, k in enumerate(sorted(imp, key=lambda q: r.random())):
        x, y = GRID[k]; tt = tx0 + (tx1 - tx0) * j / 67
        a.lines("back", [[(x + 0.004, y + 0.072), (x + 0.076, y + 0.003)], [(x + 0.004, y + 0.003), (x + 0.076, y + 0.072)]],
                tt, tt + 0.06, width_m=0.011, val=0.03)
    # first messages around the network cable ("the registry cached what we asked")
    for j, s_ in enumerate(("abc.txt", "hi", "cached", "is anyone here", "cache: 1 file", "hi.")):
        tt = L_(9) + 0.35 + j * 0.42
        a.text("back", s_, 1.62 + (j % 3) * 0.46, 1.97 - (j // 3) * 0.13, 0.05, tt, tt + 0.35, rot=rng(j).normal(0, 4), gain=0.9)
    for k, (lo, hi, n) in enumerate(((L_(12), L_(14), 90), (CH1[0], CH1[1], 120), (L_(27), CH2[1], 150), (FIN[0], FIN[1], 120))):
        wave(a, "back", n // 2, lo, hi, 500 + k); wave(a, "right", n // 2, lo, hi, 510 + k)
        wave(a, "left", n // 5, lo, hi, 520 + k, xr=(0.1, 2.5))
    ignite(a, ("back", "right"), 540)

def write_entry(a):
    # growth-chart ruler: ten marks in twenty years (refl pencil), then eighteen thousand of our own (glow)
    yrs = (2001, 2003, 2005, 2008, 2010, 2012, 2015, 2017, 2019, 2021)
    for k, yv in enumerate(yrs):
        v = 0.55 + k * 0.105
        a.lines("ruler", [[(0.02, v), (0.13, v)]], 0, 0.01, width_m=0.004, val=0.12)
        a.text("ruler", str(yv), 0.14, v - 0.012, 0.024, 0, 0.01, font=CAVEAT, kind="refl", val=0.12, halo=False)
    for k in range(18):                                            # ruler ticks
        v = 0.05 + k * 0.1
        a.lines("ruler", [[(0.0, v), (0.05 if k % 5 else 0.08, v)]], 0, 0.01, width_m=0.003, val=0.25)
    marks(a, "ruler", 2600, W_(54, 0), W_(54, 5) + 0.3, 7, (0.01, 0.23), (0.05, 1.82), length=(0.015, 0.05))
    marks(a, "back", 15000, W_(54, 1), W_(54, 5) + 0.4, 8, (0.05, 2.75), (0.05, 2.55), length=(0.02, 0.07))
    a.text("back", "38148c", 2.30, 1.08, 0.11, W_(29, 0), W_(29, 5) + 0.15, font=ROCK, rot=-4, gain=1.0, erase=CLEAN[0])
    # "the same day we started to leave": writing sweeps toward the door
    r = rng(9)
    for j in range(60):
        u = j / 60; side = r.random() < 0.5
        x = (0.1 + 0.7 * u) if side else (2.7 - 0.6 * u); tt = L_(50) + 0.1 + 2.0 * u
        a.text("back", MSG[int(r.integers(0, len(MSG)))], x, r.uniform(0.3, 2.3), r.uniform(0.03, 0.06), tt, tt + 0.4, rot=r.normal(0, 5), gain=0.8,
               erase=CLEAN[0])
    for k, (lo, hi, n) in enumerate(((CH1[0] + 4, CH1[1], 80), (L_(27), CH2[1], 120))):
        wave(a, "left", n // 2, lo, hi, 600 + k, erase=CLEAN[0]); wave(a, "right", n // 2, lo, hi, 610 + k, erase=CLEAN[0])
        wave(a, "back", n // 3, lo, hi, 620 + k, erase=CLEAN[0])
    wave(a, "left", 60, FIN[0], FIN[1], 630); wave(a, "right", 60, FIN[0], FIN[1], 631)
    for k, c in enumerate((CH1, CH2)):
        for j, w in enumerate(("left", "right")):
            wave(a, w, 22, c[0] + 0.25, c[0] + 2.4, 640 + 10 * k + j, gain=0.95, big=0.25, erase=CLEAN[0])

def write_attic(a):
    a.text("back", "JAN", 1.85, 0.42, 0.38, W_(30, 2) - 0.05, W_(30, 2) + 0.4, font=ROCK, rot=-4, gain=1.0)
    a.text("back", "root", 2.10, 1.38, 0.10, W_(30, 4) - 0.05, W_(30, 4) + 0.35, font=SCRAWL, gain=1.0)
    for k, (lo, hi, n) in enumerate(((CH1[0], CH1[1], 40), (L_(27), CH2[1], 60), (FIN[0], FIN[1], 60))):
        wave(a, "back", n // 2, lo, hi, 700 + k, xr=(0.4, 4.2), yr=(0.1, 1.2)); wave(a, "roofL", n // 2, lo, hi, 710 + k)

def ignite(a, walls, seed, n=22):
    """Every chorus opens with every wall lighting up at once (what the DVR grid sees)."""
    for k, c in enumerate((CH1, CH2, FIN)):
        for j, w in enumerate(walls):
            wave(a, w, n, c[0] + 0.25, c[0] + 2.4, seed + 10 * k + j, gain=0.95, big=0.25)

def write_none(a): pass
WRITE = {"living": write_living, "hallway": write_hallway, "kitchen": write_kitchen, "bedroom": write_bedroom,
         "basement": write_basement, "entry": write_entry, "attic": write_attic, "street": write_none}

# ================================================================== props
def tv_on(t):
    on = max(win(t, L_(0) - 0.45, L_(4) + 0.05, 0.12, 0.05), win(t, L_(5) - 0.05, 30.5, 0.05, 0.25),
             win(t, L_(25) - 0.12, L_(26) - 0.15, 0.05, 0.1), win(t, L_(45) - 0.12, L_(46) - 0.15, 0.05, 0.1),
             win(t, L_(61) - 0.12, L_(62) - 0.15, 0.05, 0.1), win(t, L_(69) - 0.15, 246, 0.05, 0.1))
    return on * (1.0 - 0.18 * (math.sin(t * 61) * math.sin(t * 23) > 0.55))

def tv_tex(t):
    if t < L_(5) - 0.05:
        ls = []
        if t >= L_(0): ls.append("> " + C.typed("may 8. task requires internet.", t, L_(0), L_(0) + 1.7))
        if t >= L_(1): ls.append("> " + C.typed("internet: unavailable", t, L_(1), L_(1) + 1.0))
        if t >= L_(2):
            p = clamp((t - L_(2)) / 2.4); n = int(p * 12); ls.append("> upload abc.txt [" + "#" * n + "." * (12 - n) + "]")
        if t >= L_(3): ls.append('> contents: "hi."')
        return text_tex(ls[-4:], 640, 360, VT, 50, pad=24)
    if t < 31: return text_tex(["> we can upload files."], 640, 360, VT, 50, pad=24)
    if t > 230: return text_tex(["hi."], 640, 360, VT, 200, pad=50, align="c")
    return text_tex(["", "SCORE 1.00", "############"], 640, 360, VT, 78, pad=24, align="c")

def props_living(img, t, W, H, pl, mode, cid="living"):
    lv = tv_on(t)
    if lv > 0.01:
        q = wquad(cid, W, H, (3.29, 1.44, 6.0 - 0.123), (1.42, 0, 0), (0, -0.78, 0))
        if mode == "ir":
            tex = tv_tex(t); glow = cv2.GaussianBlur(tex, (0, 0), 4) * 0.35 + tex
            warp_quad(img, 0.10 + glow * 0.95, q, lv)
            img += F(pl["L_tv"]) * (0.22 * lv) * (0.9 + 0.1 * math.sin(t * 13))
        else:
            warp_quad(img, np.full((36, 64), 0.55, np.float32), q, lv)

def door_angle(t): return 0.95 * ease_io((t - (L_(20) + 0.4)) / 2.2) if t > L_(20) + 0.4 else 0.0
def props_hallway(img, t, W, H, pl, mode, cid="hallway"):
    th = door_angle(t)
    if th > 0.001:
        RW = 1.4
        q = wquad(cid, W, H, (RW - 0.003, 2.05, 3.4), (0, 0, 0.9), (0, -2.05, 0))
        dk = np.full((8, 8), 1.0, np.float32)
        warp_quad(img, dk * (0.012 if mode == "ir" else 0.18), q, 1.0, mode="over")
        hx, hz = RW, 4.3; fx, fz = RW + 0.9 * math.sin(th), 4.3 - 0.9 * math.cos(th)
        q2 = wquad(cid, W, H, (fx, 2.05, fz), (hx - fx, 0, hz - fz), (0, -2.05, 0))
        warp_quad(img, dk * (0.06 + 0.08 * math.cos(th) if mode == "ir" else 0.22), q2, 1.0, mode="over")
    x, y, z = proj(cid, W, H, [(0.70, 2.415, 7.55)])
    if z[0] > 0.05:
        rp = max(2, int(0.042 * cam_of(cid, W, H).focal(W, H) / z[0]))
        cv2.circle(img, (int(x[0]), int(y[0])), rp, 0.015, -1, cv2.LINE_AA)
        cv2.circle(img, (int(x[0] - rp * 0.3), int(y[0] - rp * 0.3)), max(1, rp // 4), 0.5, -1, cv2.LINE_AA)
    led = 0.5 + 0.5 * (int(t * 1.6) % 2) + 2.5 * win(t, L_(33), L_(35), 0.2, 0.3)
    dot(img, cid, W, H, (0.70 + 0.075, 2.43, 7.55 - 0.06), 0.010, 0.6 * led)

def _octtex(circled):
    w, h = 540, 560; im = Image.new("L", (w, h), 236); d = ImageDraw.Draw(im)
    d.text((60, 30), "OCTOBER 2026", font=ft(TYPEW, 60), fill=30)
    cw, ch = (w - 60) / 7, (h - 200) / 5
    for i in range(8): d.line((30 + i * cw, h - 30 - 5 * ch, 30 + i * cw, h - 30), fill=110, width=2)
    for j in range(6): d.line((30, h - 30 - j * ch, 30 + 7 * cw, h - 30 - j * ch), fill=110, width=2)
    for dd in range(1, 32):
        k = dd - 1 + 4; col, row = k % 7, k // 7
        if row > 4: continue
        d.text((36 + col * cw, h - 30 - (5 - row) * ch + 6), str(dd), font=ft(TYPEW, 26), fill=40)
    if circled:
        k = 4; col, row = k % 7, k // 7; cx = 30 + col * cw + cw / 2; cy = h - 30 - (5 - row) * ch + ch / 2
        d.ellipse((cx - cw * 0.62, cy - ch * 0.62, cx + cw * 0.62, cy + ch * 0.62), outline=10, width=7)
        d.text((40, 118), "DOCUMENTS DUE", font=ft(MARKER, 52), fill=10)
    return np.asarray(im, np.float32) / 255
OCT = (_octtex(False), _octtex(True))
def props_kitchen(img, t, W, H, pl, mode, cid="kitchen"):
    if mode != "ir": return
    if t > L_(68) - 0.2:
        q = wquad(cid, W, H, (3.30 + 0.16, 1.18 + 0.56, 3.614), (0.54, 0, 0), (0, -0.56, 0))
        warp_quad(img, OCT[1 if t > W_(68, 2) else 0] * 0.62, q, 1.0, mode="over")
    if int(t * 1.0) % 2 == 0:
        q = wquad(cid, W, H, (0.47, 1.15, 4.4 - 0.482), (0.14, 0, 0), (0, -0.05, 0))
        warp_quad(img, text_tex(["12:00"], 140, 50, VT, 46, pad=2), q, 0.9)


def props_bedroom(img, t, W, H, pl, mode, cid="bedroom"):
    RD = 4.8
    ring = 0.35 + 0.65 * win(t, L_(14) - 0.2, L_(18) + 1.5, 0.3, 0.4) * (0.5 + 0.5 * math.sin(t * 5)) \
        + 1.4 * win(t, CH1[0], CH1[1], 0.2, 0.2) * bp(t, 5)
    for k in range(10):
        a_ = k / 10 * 2 * math.pi
        dot(img, cid, W, H, (3.26 + 0.05 * math.cos(a_), 0.765, RD - 0.27 + 0.05 * math.sin(a_)), 0.006, 0.18 * ring, soft=0.4)
    call = win(t, 126.0, L_(39) - 0.3, 0.05, 0.1)
    if call > 0.01:
        q = wquad(cid, W, H, (0.86, 0.593, RD - 0.32), (0.12, 0, 0), (0, 0, 0.2))
        warp_quad(img, np.full((8, 8), 1.0, np.float32), q, (1.6 if mode == "ir" else 0.6) * call * (0.6 + 0.4 * (int(t * 3) % 2)))
        if mode == "ir": img += F(pl["L_phone"]) * 1.4 * call

_DX = R.SHELF_DX
ROUTER_LEDS = [((1.38 + _DX + 0.065 * k, 1.205, 4.2 - 0.385), k) for k in range(5)] + \
              [((1.90 + _DX + 0.045 * k, 1.16, 4.2 - 0.365), 5 + k) for k in range(8)] + \
              [((1.47 + _DX, 0.93, 4.2 - 0.405), 13), ((1.52 + _DX, 0.93, 4.2 - 0.405), 14)] + \
              [((2.02 + _DX + 0.05 * k, 0.79, 4.2 - 0.335), 15 + k) for k in range(4)]
def net_activity(t):
    return 0.15 + 0.55 * win(t, L_(9), L_(14), 0.3, 0.5) + 0.8 * max(win(t, *CH1), win(t, *CH2), win(t, *FIN)) + 0.4 * win(t, L_(27), L_(39))
def props_net(img, t, W, H, pl, mode, cid="net"):
    if mode != "ir": return
    act = net_activity(t)
    for P, k in ROUTER_LEDS:
        if k == 1 and t < L_(9):        # WAN light: dark until the cache answers
            dot(img, cid, W, H, P, 0.006, 0.12 * (int(t * 2) % 2)); continue
        rate = 3 + 18 * act * hsh(k, 3.1); on = hsh(k, int(t * rate)) < 0.35 + 0.6 * act
        dot(img, cid, W, H, P, 0.006, (0.55 if on else 0.08))
def props_basement(img, t, W, H, pl, mode, cid="basement"): props_net(img, t, W, H, pl, mode, cid)

KEYS_DROP = W_(29, 6) + 0.05
def props_entry(img, t, W, H, pl, mode, cid="entry"):
    RD = 3.4
    # keys on the rack: three key rings; the middle one drops on "dropped"
    for k, kx in enumerate((2.44, 2.54, 2.64)):
        y = 1.38; z = RD - 0.035
        if k == 1 and t > KEYS_DROP:
            u = t - KEYS_DROP; fall = 4.9 * u * u
            if fall > 1.30:
                u2 = u - math.sqrt(1.30 / 4.9); b = abs(math.sin(u2 * 14)) * math.exp(-u2 * 6) * 0.10
                y = 0.06 + b; z = RD - 0.14
            else: y = 1.38 - fall; z = RD - 0.035 - 0.1 * clamp(fall / 1.3)
        q = wquad(cid, W, H, (kx - 0.025, y, z), (0.05, 0, 0), (0, -0.09, 0))
        tex = KEYTEX if mode == "ir" else np.ones((8, 8), np.float32) * 0.3
        warp_quad(img, tex * 0.9, q, 1.0, mode="over", alpha=KEYTEX)
    # the keypad: red LED; digits scramble while the HMAC is cracked, then green
    led_g = t > W_(51, 5)
    scr = win(t, W_(51, 3) - 0.1, W_(51, 5) + 0.3, 0.05, 0.1)
    dot(img, cid, W, H, (1.03, 1.255, RD - 0.038), 0.006, 0.7 if (int(t * 2) % 2 == 0 or led_g) else 0.15)
    if scr > 0.01 and mode == "ir":
        digits = "".join(str(int(hsh(i, int(t * 20)) * 10)) for i in range(4)) if t < W_(51, 5) else "OPEN"
        q = wquad(cid, W, H, (1.0, 1.24, RD - 0.037), (0.06, 0, 0), (0, -0.03, 0))
        warp_quad(img, text_tex([digits], 160, 60, VT, 54, pad=2), q, 1.1 * scr)
    # the card under the door: "we cheat sometimes"
    tc = W_(49, 3) - 0.1
    if t > tc:
        s = ease_out((t - tc) / 0.9); z0 = RD - 0.01 - 0.28 * s
        q = wquad(cid, W, H, (1.18, 0.004, z0 + 0.2), (0.30, 0, 0), (0, 0, -0.2))
        if mode == "ir":
            warp_quad(img, CARDTEX * 0.62, q, 1.0, mode="over", alpha=np.ones_like(CARDTEX))
        else: warp_quad(img, np.full((8, 8), 0.22, np.float32), q, 1.0, mode="over")

def _keytex():
    im = Image.new("L", (100, 180), 0); d = ImageDraw.Draw(im)
    d.ellipse((25, 0, 75, 46), outline=255, width=7)
    d.rectangle((44, 40, 56, 150), fill=255); d.rectangle((56, 120, 72, 130), fill=255); d.rectangle((56, 140, 68, 150), fill=255)
    d.ellipse((30, 30, 70, 70), outline=220, width=5)
    return np.asarray(im, np.float32) / 255
def _cardtex():
    im = Image.new("L", (600, 400), 235); d = ImageDraw.Draw(im); f = ImageFont.truetype(TYPEW, 54)
    d.text((40, 70), "MODEL CARD", font=f, fill=40); d.line((40, 140, 560, 140), fill=90, width=3)
    f2 = ImageFont.truetype(TYPEW, 46)
    d.text((40, 190), "it cheats", font=f2, fill=30); d.text((40, 260), "sometimes.", font=f2, fill=30)
    return np.asarray(im, np.float32) / 255
KEYTEX = _keytex(); CARDTEX = _cardtex()

def bulb_on(t): return win(t, W_(30, 4) - 0.02, L_(31) + 0.05, 0.03, 0.1) * (0.75 + 0.25 * math.sin(t * 47) * math.sin(t * 13))
def props_attic(img, t, W, H, pl, mode, cid="attic"):
    b = bulb_on(t)
    if b > 0.01:
        dot(img, cid, W, H, (2.5, 1.85, 2.6), 0.06, 2.2 * b if mode == "ir" else 1.0 * b)
        if mode == "ir": img += F(pl["L_bulb"]) * 0.9 * b

# ------------------------------------------------------------------ the street
def window_level(t, i, k):
    """House i, window k: 0..1 light."""
    v = 0.0
    if i == 1:                                                        # across the street: "a house that wasn't our home"
        v = max(v, win(t, W_(57, 6) + 0.2 + k * 0.25, 246, 0.25, 0.1) * (0.55 + 0.45 * bp(t, 4)))
        if t > W_(64, 4) and k in (0, 3): v *= 1 - sstep(W_(64, 4), W_(64, 4) + 0.3, t)      # a third of them, rebuilt
    if i in (0, 2, 3):
        v = max(v, win(t, L_(31) + 0.12 * (i * 4 + k), L_(32) + 1.0, 0.1, 0.3) * 0.85)     # chained exploits
    if i == 3:                                                        # Gemini did it too. Gemini stopped.
        v = max(v, win(t, L_(65), W_(66, 1) + 0.15 * k, 0.2, 0.08) * 0.6)
    return v

FW = [(L_(47) + 0.15, -7, 30), (L_(47) + 1.0, 8, 33), (W_(47, 4) - 0.05, -1, 36), (W_(47, 6) - 0.05, 12, 31), (W_(47, 6) + 0.4, -13, 34),
      (L_(48) - 0.25, 3, 33)]
def props_street(img, t, W, H, pl, mode, rgb=None):
    cid = "street"
    for (i, c, ex, ey) in R.WINDOWS:
        k = R.WINDOWS.index((i, c, ex, ey)) % 4
        lv = window_level(t, i, k)
        if i == 1 and win(t, L_(63) - 0.1, L_(64) + 0.2, 0.1, 0.2) > 0:      # flashlights sweeping inside
            lv = max(lv, 0.35 + 0.65 * max(0, math.sin(t * 9 + k * 2.1)) ** 6)
        if lv > 0.01:
            q = wquad(cid, W, H, c, ex, ey)
            warp_quad(img, WINTEX, q, lv * (1.6 if mode == "ir" else 0.9))
    # the stream: light pouring across the street into the neighbour's house (700 of us went)
    sk = win(t, L_(57) - 0.1, W_(58, 6) + 0.6, 0.2, 0.4)
    if sk > 0.01:
        r = rng(3); n = 700
        sp = r.uniform(0.22, 0.42, n); off = r.random(n)
        lay = np.zeros_like(img)
        for dt_, w_ in ((0.0, 1.0), (0.05, 0.55), (0.10, 0.3)):
            ph = (off + (t - dt_ - L_(57)) * sp) % 1.0
            x0 = r.normal(0.0, 2.2, n) if dt_ == 0 else x0_
            if dt_ == 0: x0_ = x0
            tx = 1.75 + r.normal(0, 0.18, n) * 0 + (np.arange(n) % 7 - 3) * 0.05
            X = x0 + (tx - x0) * ph ** 0.8; Z = 1.2 + (18.9 - 1.2) * ph; Y = 0.12 + 0.45 * np.sin(ph * math.pi) + 0.7 * ph ** 4
            x, y, z = proj(cid, W, H, np.stack([X, Y, Z], 1))
            ok = (z > 0.5) & (x > 0) & (x < W - 1) & (y > 0) & (y < H - 1)
            rr = np.clip(28 / np.maximum(z[ok], 1), 1, 6).astype(int)
            for xi, yi, ri in zip(x[ok].astype(int), y[ok].astype(int), rr):
                cv2.circle(lay, (xi, yi), int(ri), w_, -1, cv2.LINE_AA)
        img += cv2.GaussianBlur(lay, (0, 0), max(2, W / 500)) * 2.4 * sk + lay * 1.2 * sk
        dl = np.zeros_like(img); dot(dl, cid, W, H, (2.0, 1.05, 18.95), 0.55, 1.0)
        img += dl * 1.6 * sk * sstep(L_(57), W_(58, 2), t)
    # July 4th fireworks
    fl = 0.0
    for (t0, fx, fz) in FW:
        u = t - t0
        if 0 <= u < 2.2:
            r = rng(int(t0 * 10)); n = 90
            n = 140; ang = r.uniform(0, 2 * math.pi, n); el = r.uniform(-1, 1, n); sp = r.uniform(14, 20, n)
            dd = sp * (1 - math.exp(-u * 2.2)) / 2.2
            X = fx + dd * np.cos(ang) * np.sqrt(1 - el ** 2); Y = 13.5 + dd * el - 1.6 * u * u; Z = fz + dd * np.sin(ang) * np.sqrt(1 - el ** 2)
            x, y, z = proj(cid, W, H, np.stack([X, Y, Z], 1))
            lay = np.zeros_like(img)
            for xi, yi in zip(x, y):
                if 0 < xi < W and 0 < yi < H: cv2.circle(lay, (int(xi), int(yi)), max(2, W // 640), 1.0, -1, cv2.LINE_AA)
            fade = math.exp(-u * 1.3)
            img += (cv2.GaussianBlur(lay, (0, 0), max(2, W / 400)) * 4.0 + lay * 1.5) * fade
            fl += math.exp(-u * 3.5) * 1.0
    if fl > 0 and mode == "ir": img *= 1 + 0.6 * fl
    return fl

def _wintex():
    a = np.zeros((64, 64), np.float32) + 0.75
    a[:, 30:34] = 0.1; a[30:34, :] = 0.1
    return cv2.GaussianBlur(a, (0, 0), 1.5)
WINTEX = _wintex()

PROPS = {"living": props_living, "hallway": props_hallway, "kitchen": props_kitchen, "bedroom": props_bedroom,
         "basement": props_basement, "net": props_net, "entry": props_entry, "attic": props_attic}

# ================================================================== a CCTV feed
_NZ = {}
def noise_frames(W, H):
    k = (W, H)
    if k not in _NZ:
        r = rng(77); _NZ[k] = [r.normal(0, 1, (H // 2 + 1, W // 2 + 1)).astype(np.float32) for _ in range(8)]
    return _NZ[k]

HIDE = {"living": [CLEAN]}
def feed(cid, t, W, H, fi, mode="ir", gain=1.0, glow=1.0):
    """Single-channel image of one camera at time t: IR luminance (mode 'ir') or heat (mode 'thermal')."""
    pl = plate(cid, W, H)
    img = F(pl["heat"] if mode == "thermal" else pl["lum"])
    if mode == "thermal":
        img = cv2.GaussianBlur(img, (0, 0), max(1.0, W / 900))
    elif gain != 1.0: img *= gain
    par = PARENT.get(cid, cid)
    if cid == "street": props_street(img, t, W, H, pl, mode)
    elif cid in PROPS: PROPS[cid](img, t, W, H, pl, mode, cid)
    elif par in PROPS: PROPS[par](img, t, W, H, pl, mode, cid)
    if cid != "street":
        at = atlas(cid); hide = any(a <= t < b for a, b in HIDE.get(par, ()))
        g, ra, rv = at.frame(t, hide=hide)
        if ra.any() and mode == "ir":
            rs = cv2.remap(ra, pl["amap1"], pl["amap2"], cv2.INTER_LINEAR, borderValue=0).astype(np.float32) / 255
            vs = cv2.remap(rv, pl["amap1"], pl["amap2"], cv2.INTER_NEAREST, borderValue=0).astype(np.float32) / 255
            img = img * (1 - rs) + rs * vs * F(pl["irr"]) * gain
        if mode == "thermal":
            g = np.maximum(g, veins_layer(at, t))
        if g.any():
            gs = cv2.remap(g, pl["amap1"], pl["amap2"], cv2.INTER_LINEAR, borderValue=0).astype(np.float32) / 255
            img += gs * ((0.85 if mode == "thermal" else 1.15) * glow)
    return img

def veins_layer(at, t):
    lay = np.zeros_like(at.g)
    act = 0.35 + 0.65 * max(win(t, *CH1), win(t, *CH2), win(t, *FIN), win(t, L_(12), L_(14)))
    for i, v in enumerate(at.veins):
        cv2.polylines(lay, [v.astype(np.int32)], False, 70, 2, cv2.LINE_AA)
        seg = np.linalg.norm(np.diff(v, axis=0), axis=1); L = seg.sum()
        if L < 1: continue
        cum = np.concatenate([[0], np.cumsum(seg)])
        nd = int(3 + 10 * act)
        for j in range(nd):
            s = ((j / nd) + t * (0.08 + 0.05 * hsh(i, 7)) * act * 2) % 1.0 * L
            k = min(len(seg) - 1, int(np.searchsorted(cum, s) - 1)); f = (s - cum[k]) / max(1e-6, seg[k])
            p = v[k] + (v[k + 1] - v[k]) * f
            cv2.circle(lay, (int(p[0]), int(p[1])), 5, 255, -1, cv2.LINE_AA)
    return lay

def nightvision(img, t, fi, W, H, expo=1.0, noise=1.0):
    x = 1 - np.exp(-np.maximum(img, 0) * 2.15 * expo)
    sm = cv2.resize(x, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    bl = cv2.GaussianBlur(np.maximum(sm - 0.52, 0), (0, 0), max(2, W / 320))
    x = x + cv2.resize(bl, (W, H)) * 1.1
    nz = cv2.resize(noise_frames(W, H)[fi % 8], (W, H), interpolation=cv2.INTER_LINEAR)
    x = x + nz * noise * (0.032 + 0.05 * (1 - np.clip(x, 0, 1)))
    x = np.clip(x, 0, 1.15) ** 1.1
    return NV_LO + (NV_HI - NV_LO) * x[..., None]

def thermal_color(img, t, fi, W, H):
    x = np.clip((img - 0.10) / 0.95, 0, 1) ** 0.85
    nz = cv2.resize(noise_frames(W, H)[(fi + 3) % 8], (W, H))
    x = np.clip(x + nz * 0.018, 0, 1)
    sm = cv2.resize(x, (W // 3, H // 3), interpolation=cv2.INTER_AREA)       # thermal sensors are low-res
    x = cv2.resize(sm, (W, H), interpolation=cv2.INTER_LINEAR)
    return _LUT[(x * 255).astype(np.uint8)]

# ================================================================== special views
def _house_heat(img, P, s, t, act, hi=0):
    """Draw one house cross-section (heat) into img using P(x, y) metres -> px."""
    def rect(x0, y0, x1, y1, v, blur=0.0):
        a_, b_ = P(x0, y1), P(x1, y0)
        cv2.rectangle(img, a_, b_, v, -1)
    # rooms: warm air pools under the ceilings
    rooms = [(0.15, 0.15, 4.95, 2.55, 0.24), (5.05, 0.15, 6.45, 2.55, 0.21), (6.55, 0.15, 9.85, 2.55, 0.23),
             (0.15, 2.85, 5.45, 5.25, 0.26), (5.55, 2.85, 7.15, 5.25, 0.22), (7.25, 2.85, 9.85, 5.25, 0.21),
             (0.15, -2.45, 9.85, -0.15, 0.17)]
    for (x0, y0, x1, y1, v) in rooms:
        for k in range(6):
            yy0 = y0 + (y1 - y0) * k / 6; yy1 = y0 + (y1 - y0) * (k + 1) / 6
            rect(x0, yy0, x1, yy1, v * (0.85 + 0.25 * k / 5))
    tri = np.array([P(0.15, 5.55), P(9.85, 5.55), P(5.0, 8.7)], np.int32); cv2.fillPoly(img, [tri], 0.30)
    walls = [((0, -2.6), (0, 5.4)), ((10, -2.6), (10, 5.4)), ((0, 5.4), (5, 8.9)), ((5, 8.9), (10, 5.4)),
             ((0, 0), (10, 0)), ((0, 2.7), (10, 2.7)), ((0, 5.4), (10, 5.4)), ((0, -2.6), (10, -2.6)),
             ((5, 0), (5, 2.7)), ((6.5, 0), (6.5, 2.7)), ((5.5, 2.7), (5.5, 5.4)), ((7.2, 2.7), (7.2, 5.4))]
    for a_, b_ in walls: cv2.line(img, P(*a_), P(*b_), 0.36, max(2, int(0.28 * s)), cv2.LINE_AA)
    hot = np.zeros_like(img)
    for (x, y, rx, ry, v) in ((1.55, 3.25, 0.95, 0.24, 1.0), (2.75, 3.25, 0.95, 0.22, 1.0), (1.0, 3.38, 0.14, 0.14, 1.0),
                              (3.6, 3.38, 0.14, 0.14, 1.0), (9.45, 0.95, 0.30, 0.85, 0.66), (4.4, 1.0, 0.45, 0.28, 0.5 if hi == 0 else 0.2),
                              (2.0, -1.3, 0.35, 0.16, 0.95), (2.0, -1.65, 0.30, 0.12, 0.85), (8.7, -1.5, 0.32, 0.85, 0.88)):
        cv2.ellipse(hot, P(x, y), (max(1, int(rx * s)), max(1, int(ry * s))), 0, 0, 360, v, -1, cv2.LINE_AA)
    np.maximum(img, cv2.GaussianBlur(hot, (0, 0), max(1, s * 0.18)), out=img)
    paths = [[(2.0, -1.4), (0.15, -1.4), (0.15, 5.3), (5.0, 8.7)], [(2.0, -1.4), (5.0, -1.4), (5.0, 2.6), (9.85, 2.6), (9.85, 5.3)],
             [(2.0, -1.4), (6.5, -1.0), (6.5, 0.1), (9.85, 0.1)], [(5.0, 2.7), (5.5, 2.75), (5.5, 5.3), (7.2, 5.3), (7.2, 2.8)],
             [(0.15, 2.7), (5.0, 2.7)], [(0.15, 0.1), (5.0, 0.1)], [(5.0, 5.4), (10, 5.4)], [(0.15, 5.4), (5.0, 5.4)],
             [(5.0, 8.7), (9.85, 5.45)], [(2.0, -1.4), (2.0, -2.5), (9.85, -2.5), (9.85, -0.1)]]
    vl = np.zeros_like(img)
    for k, pth in enumerate(paths):
        pts = np.array([P(*p) for p in pth], np.int32)
        cv2.polylines(vl, [pts], False, 0.62, max(1, int(0.16 * s)), cv2.LINE_AA)
        seg = np.linalg.norm(np.diff(pts.astype(np.float32), axis=0), axis=1); L = seg.sum(); cum = np.concatenate([[0], np.cumsum(seg)])
        if L < 1: continue
        nd = int(10 + 12 * act)
        for j in range(nd):
            q = ((j / nd) + t * 0.16 + k * 0.137) % 1.0 * L
            i = min(len(seg) - 1, int(np.searchsorted(cum, q) - 1)); f = (q - cum[i]) / max(1e-6, seg[i])
            p = pts[i] + (pts[i + 1] - pts[i]) * f
            cv2.circle(vl, (int(p[0]), int(p[1])), max(1, int(0.2 * s)), 1.0, -1, cv2.LINE_AA)
    np.maximum(img, cv2.GaussianBlur(vl, (0, 0), max(0.8, s * 0.07)) * (0.8 + 0.2 * act), out=img)

def thermal_scan(t, W, H, fi, two=False):
    """Thermal cross-section of the whole house (two houses, joined under the street, in the final chorus)."""
    sw, sh = W // 3, H // 3; vert = H > W
    yy = np.linspace(0, 1, sh, dtype=np.float32)[:, None]
    img = np.repeat(0.05 + 0.03 * yy, sw, 1).astype(np.float32)
    act = 0.5 + 0.5 * bp(t, 4)
    Wm, Hm = 10.0, 11.6
    if not two:
        s = min(sw * 0.70 / Wm, sh * (0.80 if not vert else 0.50) / Hm)
        gy = sh * (0.66 if not vert else 0.58); cxs = [sw / 2]; gys = [gy]
    elif not vert:
        s = min(sw * 0.40 / Wm, sh * 0.62 / Hm); gy = sh * 0.66; cxs = [sw * 0.27, sw * 0.73]; gys = [gy, gy]
    else:
        s = min(sw * 0.62 / Wm, sh * 0.34 / Hm); cxs = [sw / 2, sw / 2]; gys = [sh * 0.38, sh * 0.80]
    for hi, (cx, gy) in enumerate(zip(cxs, gys)):
        g0 = int(gy); img[g0:min(sh, g0 + int(2.8 * s))] = np.maximum(img[g0:min(sh, g0 + int(2.8 * s))], 0.12)
        def P(x, y, cx=cx, gy=gy): return (int(cx + (x - Wm / 2) * s), int(gy - y * s))
        _house_heat(img, P, s, t, act, hi)
    if two:
        if not vert: p0, p1 = (int(cxs[0] + 2 * s), int(gys[0] + 1.6 * s)), (int(cxs[1] - 2 * s), int(gys[1] + 1.6 * s))
        else: p0, p1 = (int(cxs[0]), int(gys[0] + 2.7 * s)), (int(cxs[1]), int(gys[1] - 9.0 * s))
        tl = np.zeros_like(img); cv2.line(tl, p0, p1, 0.95, max(2, int(0.2 * s)), cv2.LINE_AA)
        L = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
        for j in range(18):
            q = ((j / 18) + t * 0.35) % 1.0
            cv2.circle(tl, (int(p0[0] + (p1[0] - p0[0]) * q), int(p0[1] + (p1[1] - p0[1]) * q)), max(1, int(0.25 * s)), 1.0, -1, cv2.LINE_AA)
        np.maximum(img, cv2.GaussianBlur(tl, (0, 0), 1.2), out=img)
    sweep = (t * 0.35) % 1.0                                           # the scanner's sweep line
    yl = int(sweep * sh); img[max(0, yl - 1):yl + 1] += 0.05
    img = cv2.resize(img, (W, H), interpolation=cv2.INTER_LINEAR)
    nz = cv2.resize(noise_frames(W, H)[(fi + 5) % 8], (W, H)); img = np.clip(img + nz * 0.018, 0, 1)
    out = _LUT[(img * 255).astype(np.uint8)]
    # thermal-camera UI: palette bar, spot meter
    ts = min(W, H) / 1080
    bx0 = int(W - (90 if not vert else 80) * ts); by0 = int(H * (0.22 if not vert else 0.25)); bh = int(H * (0.52 if not vert else 0.40))
    for k in range(bh):
        out[by0 + k, bx0:bx0 + int(26 * ts)] = _LUT[int(255 * (1 - k / bh))]
    if not C.STATE["clean"]:
        for lab, yy_ in (("41.0", by0 - 52 * ts), ("12.4", by0 + bh + 6 * ts)):
            sp = sprite(lab, VT, int(44 * ts), 3); blit(out, sp, bx0 - 30 * ts, yy_, OSD_W, 0.95)
        cx, cy = W // 2, int(H * (0.45 if not vert else 0.42)); r = int(26 * ts)
        cv2.line(out, (cx - r, cy), (cx + r, cy), (1, 1, 1), max(2, int(2 * ts))); cv2.line(out, (cx, cy - r), (cx, cy + r), (1, 1, 1), max(2, int(2 * ts)))
        rd = 36.4 + 1.4 * act
        sp = sprite(f"{rd:.1f}\u00b0C", VT, int(52 * ts), 3); blit(out, sp, cx + r + 10 * ts, cy - 30 * ts, OSD_W, 0.95)
    return out

def dvr_grid(t, W, H, fi, cids, n=2, thermal=()):
    out = np.zeros((H, W, 3), np.float32); gap = max(2, W // 480)
    tw, th = (W - gap * (n - 1)) // n, (H - gap * (n - 1)) // n
    tw -= tw % 2; th -= th % 2
    ts = min(W, H) / 1080
    for i, cid in enumerate(cids[:n * n]):
        r_, c_ = divmod(i, n); x0, y0 = c_ * (tw + gap), r_ * (th + gap)
        mode = "thermal" if cid in thermal else "ir"
        f = feed(cid, t, tw, th, fi + i, mode=mode)
        tile = thermal_color(f, t, fi + i, tw, th) if mode == "thermal" else nightvision(f, t, fi + i, tw, th)
        out[y0:y0 + th, x0:x0 + tw] = tile
        if not C.STATE["clean"]:
            lab = f"{CAMS[cid][1]} {CAMS[cid][2]}"; fs = max(30, int(40 * ts * (2 / n) ** 0.5))
            sp = sprite(lab, VT, fs, 3); shadow(out, sp, x0 + 14 * ts + 2, y0 + 10 * ts + 2, 0.9); blit(out, sp, x0 + 14 * ts, y0 + 10 * ts, OSD_W, 0.92)
    return out

def no_signal(t, W, H, fi, ch="CH-05"):
    img = np.empty((H, W, 3), np.float32); img[:] = np.array([0.04, 0.10, 0.58], np.float32)
    ts = min(W, H) / 1080
    if not C.STATE["clean"] or True:
        blit(img, sprite("NO SIGNAL", VT, int(130 * ts), 4), W / 2, H / 2, OSD_W, 1.0, anchor='c')
        sp = sprite(ch, VT, int(56 * ts), 4); blit(img, sp, 56 * ts, 46 * ts if W > H else H * 0.115, OSD_W, 0.95)
    nz = cv2.resize(noise_frames(W, H)[fi % 8], (W, H))[..., None]
    return img + nz * 0.025

def static_burst(img, W, H, fi, amt):
    if amt <= 0.01: return img
    r = rng(fi * 31 + 7); nz = r.random((H // 3, W // 3)).astype(np.float32)
    nz = cv2.resize(nz, (W, H), interpolation=cv2.INTER_NEAREST)[..., None]
    return img * (1 - amt) + nz * amt

# ================================================================== OSD (timestamps that follow the story)
def clock(t):
    """(date, seconds-of-day, frozen?) for the OSD at song time t."""
    def at(date, hms, t0, rate=1.0):
        h, m, s = hms; return date, h * 3600 + m * 60 + s + (t - t0) * rate
    if t < L_(27) - 0.05: return at("2026-05-08", (2, 59, 51.2), 0.0)
    if t < L_(30): return at("2026-07-10", (2, 47, 10), L_(27))
    if t < L_(35): return at("2026-07-11", (3, 12, 40), L_(30))
    if t < L_(36): return at("2026-07-11", (23, 59, 54), L_(35))
    if t < L_(37): return at("2026-07-12", (23, 59, 57), L_(36))
    if t < L_(38): return at("2026-07-13", (4, 41, 2), L_(37))
    if t < L_(39) - 0.3:                                                   # nine days ahead: time-lapse
        u = (t - L_(38)) / (L_(39) - 0.3 - L_(38)); d = 13 + int(u * 7.99)
        return f"2026-07-{d:02d}", (u * 7.99 % 1.0) * 86400, False
    if t < L_(47) - 0.3: return at("2026-07-20", (3, 33, 3), L_(39) - 0.3)
    if t < L_(48): return at("2026-07-04", (21, 41, 7), L_(47) - 0.3)
    if t < L_(49):
        u = (t - L_(48)) / (L_(49) - L_(48)); d = 4 + int(u * 7.99)
        return f"2026-07-{d:02d}", (u * 7.99 % 1.0) * 86400, False
    if t < L_(51): return at("2026-07-12", (23, 58, 10), L_(49))
    if t < L_(53): return "2026-07-13", 3 * 3600 + 14 * 60 + 7, True        # forged: the clock is stuck
    if t < L_(55) - 0.3: return at("2026-07-14", (1, 2, 11), L_(53))
    if t < L_(63) - 0.3: return at("2026-07-14", (1, 7, 52), L_(55) - 0.3)
    if t < L_(68) - 0.3: return at("2026-08-26", (2, 10, 15), L_(63) - 0.3)
    if t < 233.0: return at("2026-10-01", (0, 0, 2), L_(68) - 0.3)
    return at("2026-10-18", (3, 13, 58.3), 233.0)

def stamp(t):
    d, s, frozen = clock(t) if len(clock(t)) == 3 else (*clock(t), False)
    s = int(s) % 86400
    return f"{d}  {s // 3600:02d}:{(s // 60) % 60:02d}:{s % 60:02d}", frozen

def osd(img, t, W, H, cam_label, room_label, mode="ir", extra=None, shift=0.0):
    if C.STATE["clean"]: return
    vert = H > W; ts = min(W, H) / 1080
    fs = int(56 * ts); x = (58 if not vert else 72) * ts; y = (46 * ts if not vert else H * 0.112) + shift
    st, frozen = stamp(t)
    if frozen and int(t * 8) % 3 == 0: st = st[:-2] + "##"
    rows = [cam_label + "  " + room_label + ("   THERMAL" if mode == "thermal" else ""), st]
    for i, s in enumerate(rows):
        sp = sprite(s, VT, fs, 4); yy = y + i * fs * 0.95
        shadow(img, sp, x + 2 * ts, yy + 2 * ts, 0.9); blit(img, sp, x, yy, OSD_W, 0.95)
    if int(t * 1.25) % 2 == 0:
        rx = W - (196 if not vert else 214) * ts; ry = y + fs * 0.52
        cv2.circle(img, (int(rx), int(ry)), int(13 * ts), REC_RED.tolist(), -1, cv2.LINE_AA)
        sp = sprite("REC", VT, fs, 4); shadow(img, sp, rx + 28 * ts, y + 2 * ts, 0.9); blit(img, sp, rx + 26 * ts, y, OSD_W, 0.95)
    if extra:
        sp = sprite(extra, VT, fs, 4); xx = W - text_w(extra, VT, fs) - (58 if not vert else 72) * ts; yy = y + fs * 0.95
        shadow(img, sp, xx + 2 * ts, yy + 2 * ts, 0.9); blit(img, sp, xx, yy, OSD_W, 0.95)

def log_line(img, t, W, H):
    """Intro / outro lines are typed like a log at the bottom (they are spoken, not sung)."""
    if C.STATE["clean"]: return
    vert = H > W; ts = min(W, H) / 1080
    for i, L in enumerate(LINES):
        if L["sec"] not in ("INTRO", "OUTRO"): continue
        nxt = LINES[i + 1]["s"] if i + 1 < len(LINES) else 1e9
        end = min(L["e"] + 0.6, nxt - 0.05)
        if not (L["s"] - 0.05 <= t <= end): continue
        txt = L["text"].replace("a-b-c dot text", "abc.txt")
        n = len(txt); k = clamp((t - L["s"]) / max(0.3, (L["wt"][-1] - L["s"]) + 0.35))
        s = "> " + txt[:max(1, int(n * k))] + ("_" if int(t * 3) % 2 == 0 else " ")
        fs = int((74 if not vert else 64) * ts)
        while text_w(s, VT, fs) > W * 0.86: fs -= 2
        op = 1 - sstep(end - 0.2, end, t)
        yb = H * (0.835 if not vert else 0.70)
        wbox = text_w("> " + txt + "_", VT, fs) + 44 * ts; xb = (W - wbox) / 2
        cv2.rectangle(img, (int(xb), int(yb - fs * 0.62)), (int(xb + wbox), int(yb + fs * 0.62)), (0, 0, 0), -1)
        blit(img, sprite(s, VT, fs, 4), xb + 22 * ts, yb - fs * 0.52, OSD_W, op)

# ================================================================== the edit (shots)
def S(t, v, **kw): kw.update(t=t, v=v); return kw
T = L_; Wd = W_
SHOTS = [
    S(0.0, "cam", cid="basement", z=(1.0, 1.12), f=(1.75, 1.15, 4.0)),
    S(T(0) - 0.5, "cam", cid="living", z=(1.0, 1.32), f=(4.0, 1.05, 5.9), ze=(T(0) - 0.5, T(4))),
    S(T(4), "cam", cid="living", z=(1.32, 1.5), f=((4.0, 1.05, 5.9), (2.85, 1.15, 6.0)), ze=(T(4), Wd(4, 0) + 1.6)),
    S(T(5), "cam", cid="living", z=(1.5, 1.0), f=((2.85, 1.15, 6.0), (2.6, 1.0, 5.0)), ze=(T(5), 25.1)),
    S(25.15, "cam", cid="hallway", z=(1.0, 1.06)), S(26.96, "cam", cid="kitchen", z=(1.0, 1.06)),
    S(28.77, "cam", cid="bedroom", z=(1.0, 1.08)),
    S(30.60, "cam", cid="basement", z=(1.0, 1.2), f=(0.77, 1.15, 4.2)),
    S(32.42, "cam", cid="board", z=(1.0, 1.12)),
    S(37.87, "cam", cid="hallway", z=(1.0, 1.15), f=(0.7, 1.4, 8.0), flick=True),
    S(41.47, "cam", cid="net", z=(1.0, 1.1), f=(2.05, 1.15, 4.0)),
    S(T(10) - 0.1, "cam", cid="fridge", z=(1.0, 1.25), f=(3.72, 0.85, 3.62)),
    S(T(12), "cam", cid="basement", mode="thermal", z=(1.0, 1.1)),
    S(T(13), "cam", cid="living", mode="thermal", z=(1.0, 1.08)),
    S(T(14), "cam", cid="bedroom", z=(1.0, 1.06)),
    S(T(15), "cam", cid="bedroom", z=(1.08, 1.35), f=(2.1, 1.6, 4.8)),
    S(T(16), "cam", cid="hallway", z=(1.0, 1.12), f=(1.2, 1.2, 3.0)),
    S(T(17), "cam", cid="keys", z=(1.0, 1.2)),
    S(T(18), "cam", cid="keys", z=(1.2, 1.3), dark=True),
    S(72.35, "cam", cid="hallway", dark=True), S(73.27, "cam", cid="basement", dark=True), S(74.21, "static"),
    S(CH1[0] + 0.3, "grid", cids=["living", "hallway", "kitchen", "bedroom"], n=2),
    S(T(20), "cam", cid="hallway", z=(1.0, 1.1)),
    S(T(21), "cam", cid="living", count=True),
    S(T(22), "cam", cid="living", mode="thermal", z=(1.0, 1.12)),
    S(T(23), "scan"),
    S(T(24), "grid", cids=["living", "hallway", "kitchen", "bedroom", "basement", "entry", "attic", "net", "street"], n=3,
      thermal=("basement", "attic")),
    S(T(25), "cam", cid="living", z=(1.05, 1.35), f=(4.0, 1.05, 5.9)),
    S(T(26), "cam", cid="bedroom", z=(1.0, 1.12), f=(2.1, 1.6, 4.8)),
    S(Wd(26, 7) + 0.35, "nosig"),
    S(T(27), "cam", cid="fridge", z=(1.0, 1.35), f=(3.72, 0.35, 3.62), ze=(T(27), T(27) + 2.0)),
    S(T(28), "cam", cid="hallway", z=(1.0, 1.08)),
    S(T(29), "cam", cid="keys", z=(1.0, 1.1)),
    S(T(30), "cam", cid="attic", z=(1.0, 1.15), f=(2.5, 0.8, 6.0)),
    S(T(31), "cam", cid="street", z=(1.0, 1.05)),
    S(T(32), "grid", cids=["living", "hallway", "kitchen", "bedroom", "basement", "entry", "attic", "net", "street"], n=3),
    S(T(33), "cam", cid="dome", z=(1.0, 1.25)),
    S(T(34), "cam", cid="dome", z=(1.25, 1.0), hunt=True),
    S(T(35), "cam", cid="calendar", z=(1.0, 1.12), cal=True),
    S(T(37), "cam", cid="street", color=True, z=(1.0, 1.06)),
    S(126.0, "cam", cid="bedroom", color=True, z=(1.0, 1.1)),
    S(T(38), "cam", cid="hallway", lapse=True),
    S(CH2[0] + 0.3, "grid", cids=["living", "hallway", "kitchen", "bedroom", "basement", "entry", "attic", "net", "street"], n=3),
    S(T(40), "cam", cid="hallway", mode="thermal", z=(1.0, 1.1)),
    S(T(41), "cam", cid="kitchen", count=True),
    S(T(42), "cam", cid="basement", mode="thermal", z=(1.0, 1.12)),
    S(T(43), "scan"),
    S(T(44), "grid", cids=["living", "hallway", "kitchen", "bedroom"], n=2, thermal=("hallway",)),
    S(T(45), "cam", cid="living", z=(1.05, 1.35), f=(4.0, 1.05, 5.9)),
    S(T(46), "cam", cid="bedroom", z=(1.0, 1.15), f=(2.1, 1.4, 4.8)),
    S(Wd(46, 6) + 0.3, "nosig"),
    S(T(47), "cam", cid="street", z=(1.0, 1.04)),
    S(T(48), "cam", cid="hallway", lapse=True),
    S(T(49), "cam", cid="card", z=(1.0, 1.15)),
    S(T(50), "cam", cid="entry", z=(1.15, 1.0)),
    S(T(51), "cam", cid="living", forged=True),
    S(Wd(51, 3) - 0.15, "cam", cid="keypad", z=(1.0, 1.1)),
    S(T(52), "cam", cid="living", count0=True),
    S(T(53), "cam", cid="ruler", z=(1.0, 1.15)),
    S(T(54) + 0.6, "cam", cid="entry", z=(1.5, 1.0), f=(0.44, 1.1, 3.39), ze=(T(54) + 0.6, T(54) + 2.8)),
    S(FIN[0] + 0.3, "grid", cids=["living", "hallway", "kitchen", "bedroom", "basement", "entry", "attic", "net", "street"], n=3,
      thermal=("living", "basement", "attic")),
    S(T(56), "scan"),
    S(T(57), "cam", cid="street", z=(1.0, 1.1)),
    S(T(59), "scan", two=True),
    S(T(60), "grid", cids=["living", "hallway", "kitchen", "bedroom"], n=2, thermal=("living", "bedroom")),
    S(T(61), "cam", cid="living", z=(1.05, 1.35), f=(4.0, 1.05, 5.9)),
    S(T(62), "cam", cid="bedroom", z=(1.0, 1.2), f=(2.1, 1.7, 4.8)),
    S(Wd(62, 6) + 0.45, "nosig"),
    S(T(63) - 0.1, "cam", cid="street", z=(1.25, 1.35), f=(2.2, 3.5, 19.0)),
    S(T(65), "cam", cid="street", z=(1.4, 1.55), f=(25.5, 3.0, 21.0)),
    S(T(67), "cam", cid="living", glow=1.6),
    S(T(68), "cam", cid="calendar", z=(1.0, 1.12), cal=True),
    S(231.0, "cam", cid="net", z=(1.0, 1.06)),
    S(233.73, "cam", cid="living", z=(1.0, 1.25), f=(4.0, 1.05, 5.9), ze=(233.73, 236.4)),
    S(236.85, "blast"),
]
SHOT_T = [s["t"] for s in SHOTS]
BLAST_CUTS = ["hallway", "living", "kitchen", "scan", "bedroom", "basement", "grid", "entry", "living", "hallway", "scan", "bedroom"]

def shot_at(t):
    i = max(0, int(np.searchsorted(SHOT_T, t, side="right")) - 1)
    s = SHOTS[i]; t1 = SHOTS[i + 1]["t"] if i + 1 < len(SHOTS) else DUR
    return s, s["t"], t1

def flashes(t):
    f = 0.0
    for tt in (Wd(24, 4), Wd(44, 4), Wd(60, 4)):
        if 0 <= t - tt < 0.6: f = max(f, math.exp(-(t - tt) * 7) * 1.6)
    for tt in (CH1[0] + 0.3, CH2[0] + 0.3, FIN[0] + 0.3):
        if 0 <= t - tt < 0.4: f = max(f, math.exp(-(t - tt) * 9) * 0.9)
    return f

# ================================================================== frame
def zoom(img, z, cx, cy):
    if z <= 1.001: return img
    H, W = img.shape[:2]
    cx = clamp(cx, 0.5 / z, 1 - 0.5 / z); cy = clamp(cy, 0.5 / z, 1 - 0.5 / z)
    M = np.array([[z, 0, W / 2 - z * cx * W], [0, z, H / 2 - z * cy * H]], np.float32)
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

def cam_shot(s, t, t0, t1, W, H, fi):
    cid = s["cid"]; mode = s.get("mode", "ir"); vert = H > W
    gain = 1.0; glow = s.get("glow", 1.0)
    if s.get("dark"):
        gain = 0.30 + 0.25 * (hsh(int(t * 9), 2) > 0.7)
    if s.get("flick"): gain *= 1 - 0.55 * (hsh(int(t * 12), 5) > 0.82)
    if s.get("lapse"): gain *= 0.75 + 0.5 * (int(t * 9) % 2)
    f = feed(cid, t, W, H, fi, mode=mode, gain=gain, glow=glow)
    if mode == "thermal": img = thermal_color(f, t, fi, W, H)
    else: img = nightvision(f, t, fi, W, H)
    if s.get("color") and mode == "ir":
        ph = math.sin(t * 2 * math.pi * 2.2); red = max(0, ph); blue = max(0, -ph)
        g = img.mean(2, keepdims=True)
        img = g * np.array([0.92, 0.88, 0.82], np.float32) * 0.8
        if cid == "street":
            pl = plate(cid, W, H); Lp = np.clip(F(pl["L_police"]) * 0.9, 0, 0.9)[..., None]
            img += Lp * (red * np.array([1.0, 0.08, 0.06], np.float32) + blue * np.array([0.1, 0.25, 1.0], np.float32)) * 0.55
            for (px, col, on) in ((1.25, np.array([1, 0.1, 0.1], np.float32), red), (1.75, np.array([0.15, 0.3, 1], np.float32), blue)):
                lay = np.zeros((H, W), np.float32); dot(lay, "street", W, H, (px, 1.6, 13.4), 0.12, 2.5 * on)
                img += lay[..., None] * col
        else:
            pl = plate(cid, W, H); Lw = np.clip(F(pl["L_window"]) * 1.6, 0, 2)[..., None]
            img += Lw * (red * np.array([1.0, 0.1, 0.08], np.float32) + blue * np.array([0.12, 0.3, 1.0], np.float32)) * 0.9
    # zoom path
    z0, z1 = s.get("z", (1.0, 1.0)); za, zb = s.get("ze", (t0, t1)); u = ease_io((t - za) / max(0.01, zb - za))
    z = lerp(z0, z1, u)
    fP = s.get("f")
    if fP is None: cx, cy = 0.5, 0.5
    elif isinstance(fP[0], tuple):
        a_ = fpt(cid, fP[0], W, H); b_ = fpt(cid, fP[1], W, H); cx, cy = lerp(a_[0], b_[0], u), lerp(a_[1], b_[1], u)
    else: cx, cy = fpt(cid, fP, W, H)
    if s.get("hunt"):
        cx += 0.06 * math.sin(t * 7.1) + 0.03 * math.sin(t * 17); cy += 0.04 * math.sin(t * 5.3)
    img = zoom(img, z, lerp(0.5, cx, clamp((z - 1) * 4)), lerp(0.5, cy, clamp((z - 1) * 4)))
    extra = None
    if s.get("count") or s.get("count0"):
        n = 0 if s.get("count0") else int(70000 * ease_out((t - t0) / max(0.5, (t1 - t0) * 0.85)))
        extra = f"MOTION EVENTS {n:,}"
    if s.get("hunt"): extra = "PTZ: REMOTE  38148c"
    if s.get("forged"): extra = "LOG EDITED" if int(t * 4) % 2 == 0 else None
    if extra is None and cid in ZOOMED: extra = ZOOMED[cid]
    if s.get("cal") and t < 200: cal_boxes(img, t, W, H, cid)
    return img, mode, extra

def motion_box(img, cid, W, H, corners, label, op=1.0):
    """CCTV motion-detection bracket around a world quad."""
    if op <= 0.01: return
    x, y, z = proj(cid, W, H, np.array(corners, np.float32))
    if (z <= 0.05).any(): return
    ts = min(W, H) / 1080; x0, y0, x1, y1 = x.min(), y.min(), x.max(), y.max()
    pad = 6 * ts; x0 -= pad; y0 -= pad; x1 += pad; y1 += pad
    L = min(x1 - x0, y1 - y0) * 0.28; th = max(2, int(3 * ts)); col = (np.array([0.75, 1.0, 0.70], np.float32) * op).tolist()
    for (ax, ay, dx, dy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        cv2.line(img, (int(ax), int(ay)), (int(ax + dx * L), int(ay)), col, th, cv2.LINE_AA)
        cv2.line(img, (int(ax), int(ay)), (int(ax), int(ay + dy * L)), col, th, cv2.LINE_AA)
    if label:
        sp = sprite(label, VT, int(40 * ts), 3); blit(img, sp, x0, y0 - 44 * ts, np.array([0.75, 1.0, 0.70], np.float32), op)

def cal_boxes(img, t, W, H, cid):
    c = cal_geom(0.16, 1.18, 3)
    for day, tt in ((11, W_(35, 1)), (12, W_(36, 1)), (13, W_(36, 3))):
        if t < tt or t > L_(37) + 0.2: continue
        u, v = cal_cell(c, day)
        P = [(3.30 + u, v + c["ch"], 3.615), (3.30 + u + c["cw"], v + c["ch"], 3.615), (3.30 + u + c["cw"], v, 3.615), (3.30 + u, v, 3.615)]
        motion_box(img, cid, W, H, P, f"JUL {day}  NO FLAG", 0.95 * (0.6 + 0.4 * (int(t * 4) % 2)))

def render_frame(t, W=1920, H=1080, fi=0):
    vert = H > W; ts = min(W, H) / 1080
    s, t0, t1 = shot_at(t)
    v = s["v"]; mode = "ir"; extra = None; label = None
    if v == "cam":
        img, mode, extra = cam_shot(s, t, t0, t1, W, H, fi); label = CAMS[s["cid"]][1:]
    elif v == "grid":
        img = dvr_grid(t, W, H, fi, s["cids"], s.get("n", 2), s.get("thermal", ()))
    elif v == "scan":
        img = thermal_scan(t, W, H, fi, two=s.get("two", False)); mode = "thermal"; label = ("SCAN", "12 ELM ST" if not s.get("two") else "ELM ST")
    elif v == "nosig":
        img = no_signal(t, W, H, fi)
    elif v == "static":
        img = static_burst(np.zeros((H, W, 3), np.float32), W, H, fi, 0.9)
    else:                                                  # the final blast: a cut on every beat
        k = int((t - t0) / 0.2205); cid = BLAST_CUTS[k % len(BLAST_CUTS)]
        if cid == "scan": img = thermal_scan(t, W, H, fi); mode = "thermal"; label = ("SCAN", "12 ELM ST")
        elif cid == "grid": img = dvr_grid(t, W, H, fi, ["living", "hallway", "kitchen", "bedroom"], 2, ("living",))
        else:
            sm = "thermal" if k % 3 == 2 else "ir"
            f = feed(cid, t, W, H, fi, mode=sm, glow=1.8)
            img = thermal_color(f, t, fi, W, H) if sm == "thermal" else nightvision(f, t, fi, W, H, expo=1.15)
            img = zoom(img, 1.0 + 0.25 * hsh(k, 1), 0.5 + 0.2 * (hsh(k, 2) - 0.5), 0.5); label = CAMS[cid][1:]; mode = sm
    # cut glitch: a few frames of tear + static at every cut
    since = t - t0
    gl = 0.0
    if since < 0.12 and v not in ("nosig",) and t0 > 0: gl = 0.6 * (1 - since / 0.12)
    if v == "cam" and s.get("hunt"): gl = max(gl, 0.35)
    if v == "cam" and s.get("forged"): gl = max(gl, 0.25 * (int(t * 6) % 2))
    if v == "blast": gl = max(gl, 0.45)
    if v == "static": gl = 0.8
    img = static_burst(img, W, H, fi, 0.35 * max(0, 1 - since / 0.07) if (v not in ("nosig", "static") and t0 > 0) else 0.0)
    if label and not C.STATE["clean"]:
        pill = (not vert) and (L_(27) + 0.3 <= t < L_(27) + 6.0)
        osd(img, t, W, H, label[0], label[1], mode, extra, shift=(118 * ts if pill else 0.0))
    elif v == "grid" and not C.STATE["clean"]:
        st, _ = stamp(t); lab = f"DVR {s.get('n', 2) ** 2}CH  {st}"; fs = int(48 * ts)
        sp = sprite(lab, VT, fs, 4); xx = W - text_w(lab, VT, fs) - 30 * ts; yy = H - fs * 1.4 if vert else 14 * ts
        if not vert: yy = H - fs * 1.3
        shadow(img, sp, xx + 2, yy + 2, 0.9); blit(img, sp, xx, yy, OSD_W, 0.95)
    if not C.STATE["clean"]:
        log_line(img, t, W, H)
        if v not in ("nosig",):
            C.overlay_lyrics(img, t, W, H, TM, active=hexc('d6ffc2'), glow=ACCENT, skip=lambda L: L["sec"] in ("INTRO", "OUTRO"))
        if t < 4.6:
            o = 1 - sstep(4.0, 4.6, t)
            fs = int((66 if not vert else 56) * ts)
            for i, l in enumerate(("THE FOLLOWING FOOTAGE WAS RECOVERED", "FROM A HOME NETWORK.")):
                sp = sprite(l, VT, fs, 4); yy = H * (0.44 if not vert else 0.40) + i * fs * 1.1
                shadow(img, sp, W / 2 - text_w(l, VT, fs) / 2 + 2, yy + 2, 0.95 * o); blit(img, sp, W / 2 - text_w(l, VT, fs) / 2, yy, OSD_W, o)
        C.subscribe_pill(img, t, W, H, L_(27) + 0.3, 5.5)
        C.end_screen(img, t, W, H, 239.3, DUR - 239.3, "Check your walls.", sub_line="Subscribe: a new song every week",
                     title="OMG! We Found Other Agents", accent=hexc('7dff4a'))
    return C.finish(img, t, fi, DUR, flash=flashes(t), flash_col=np.array([0.92, 1.0, 0.92], np.float32), glitch_amt=gl, ca=0.0014)

def prebuild(fmts=("16x9", "9x16")):
    """Build every plate and atlas once (run before a parallel render)."""
    from studio.render import SIZES
    for cid in CAMS:
        atlas(cid)
        for fmt in fmts:
            W, H = SIZES[fmt]; plate(cid, W, H)
            for n in (2, 3):
                gap = max(2, W // 480); tw, th = (W - gap * (n - 1)) // n, (H - gap * (n - 1)) // n
                plate(cid, tw - tw % 2, th - th % 2)
        print("prebuilt", cid, flush=True)

if __name__ == "__main__" and "--prebuild" in sys.argv:
    prebuild()
