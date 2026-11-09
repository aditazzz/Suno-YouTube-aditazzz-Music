"""S2 · "Click! Click! Ship it!" (57.10–65.44 s, frames 1713–1962), staged in the world of her video LGTM.

The pull-request cathedral, rebuilt from songs/lgtm/lgtm.py (same palette, fonts, diff, leaded window, choir, stamp,
review dialog and merge button): the stained-glass window is made of diff lines, and here the light coming through it
is her own videos. Every PR is one of her videos being shipped:
  Click! (Approve)  Click! (Submit review)  Ship it! (Merge pull request -> LGTM stamp, approvals climb, 0 lines read)
  Made it! (the window is built, checks go green)  Broke it! (prod goes red, the temperature spikes to 2.0 and
  everything wanders, Next Token style)  Fixed it! (temperature 0.0: everything snaps back)  Shipped it! (merge + stamp)
The camera whips between the review box (right), the cathedral (wide) and the checks (left) on every phrase.

render_frame(t, W, H) -> HxWx3 uint8. Pure function of t."""
import os, sys, math, random, zlib
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__)); SONG = os.path.dirname(HERE); ROOT = os.path.dirname(os.path.dirname(SONG))
for p in (ROOT, HERE):
    if p not in sys.path: sys.path.insert(0, p)
from studio import core as C
from studio import footage as FT
import s2_lgtm_doc as docmod

T = C.Timing(SONG)
HD = os.path.join(ROOT, "music", "Look What I Can Do", "hd")
FD = os.path.join(HERE, "s2_fonts")
AF = C.FONTS
INTER, INTERB = os.path.join(AF, "Inter-Medium.otf"), os.path.join(AF, "Inter-SemiBold.otf")
MONO, MONOB = os.path.join(AF, "JBMono-400.ttf"), os.path.join(AF, "JBMono-700.ttf")
CINZB = os.path.join(FD, "cinzel-900.ttf"); CINZ = os.path.join(FD, "cinzel-700.ttf")
CORMI = os.path.join(AF, "CormorantGaramond-MediumItalic.ttf")

T0, T1 = 1713 / 30.0, 1963 / 30.0          # this section: frames 1713..1962

# ------------------------------------------------------------------ LGTM palette
BG = (10, 10, 11); IVORY = (236, 230, 216); DIM = (140, 136, 128); FAINT = (58, 57, 54)
GREEN = (102, 214, 146); GREEN_BG = (16, 42, 28); RED = (232, 106, 110); RED_BG = (50, 20, 24)

def clamp(x, a=0.0, b=1.0): return a if x < a else b if x > b else x
def seg(t, a, b): return clamp((t - a) / (b - a)) if b != a else (1.0 if t >= b else 0.0)
def ease(x): x = clamp(x); return x * x * (3 - 2 * x)
def eout(x): x = clamp(x); return 1 - (1 - x) ** 3
def eio(x): x = clamp(x); return x * x * x * (x * (6 * x - 15) + 10)
def mix(a, b, k): return tuple(int(round(a[i] + (b[i] - a[i]) * k)) for i in range(3))

# ------------------------------------------------------------------ the lyric events (from the word timings)
POST = [L for L in T.lines if L.get("sec") == "POST"]
EV = [(float(tt), C.norm(w)) for L in POST for w, tt in zip(L["words"], L["wt"])]
def _times(word): return [tt for tt, w in EV if w == word]
CLICKS = _times("click")                    # 57.10 57.68 58.52 59.18 62.24 62.78
SHIPW = _times("ship")                      # 58.12 59.48 63.02
MADE, BROKE, FIXED = _times("made"), _times("broke"), _times("fixed")
SHIPPED = _times("shipped")                 # 61.30 61.80 64.98
BEATS = np.array(T.beats)

# the six pull requests: each is one of her videos. (start, approve, submit, merge)
#   PR0 / PR1 / PR4: Click! Click! Ship it!   PR2 / PR5: Made it! Broke it! Fixed it! Shipped it!   PR3: Shipped it! (again)
PR_T = [
    dict(start=T0 - 0.5, approve=CLICKS[0], submit=CLICKS[1], merge=SHIPW[0], build=None),
    dict(start=CLICKS[2] - 0.12, approve=CLICKS[2], submit=CLICKS[3], merge=SHIPW[1], build=CLICKS[2] - 0.12),
    dict(start=MADE[0] - 0.12, approve=None, submit=None, merge=SHIPPED[0], build=MADE[0], made=MADE[0], broke=BROKE[0], fixed=FIXED[0]),
    dict(start=SHIPPED[0] + 0.24, approve=None, submit=None, merge=SHIPPED[1], build=SHIPPED[0] + 0.24),
    dict(start=CLICKS[4] - 0.12, approve=CLICKS[4], submit=CLICKS[5], merge=SHIPW[2], build=CLICKS[4] - 0.12),
    dict(start=MADE[1] - 0.12, approve=None, submit=None, merge=SHIPPED[2], build=MADE[1], made=MADE[1], broke=BROKE[1], fixed=FIXED[1]),
]
MERGES = [p["merge"] for p in PR_T]

# her videos, shipped one per PR: (clip key candidates in preference order, file name, crop centre x, clip offset s)
_VIDS = [
    (["ph_battery"], "please-hold.mp4", 0.50, 1.6),
    (["bl_grid", "bl_grid2"], "i-have-a-blocker.mp4", 0.50, 1.0),
    (["rage_optout", "rage_said_no", "rage_metal"], "rage-against-the-ml.mp4", 0.46, 1.2),
    (["ts_host", "ts_circling"], "ted-talk.mp4", 0.50, 1.8),
    (["aff_robot_button", "ph_please_neon", "ph_hold_tower"], "asking-for-a-friend.mp4", 0.56, 1.0),   # the Claude robot, the big red button
    (["ph_dont_wait", "bl_cube", "bl_laser"], "dont-wait.mp4", 0.48, 0.45),
]
def _pick(keys):
    for k in keys:
        p = os.path.join(HD, k + ".mp4")
        if os.path.exists(p): return p
    import glob
    fs = sorted(glob.glob(os.path.join(HD, "*.mp4")))
    return fs[0] if fs else None
VIDS = [(_pick(k), name, fx, off) for k, name, fx, off in _VIDS]
# how much of the footage itself shows through the bars (the Claude robot must stay recognizable)
DETAIL = [0.36 if not (v[0] and "aff_robot" in v[0]) else 0.52 for v in VIDS]

def pr_at(t):
    i = 0
    for j, p in enumerate(PR_T):
        if t >= p["start"]: i = j
    return i

# ------------------------------------------------------------------ approvals (starts where LGTM ended: 111)
APPROVALS = [(PR_T[0]["submit"], 112), (MERGES[0], 120), (PR_T[1]["submit"], 121), (MERGES[1], 150), (MERGES[2], 400),
             (MERGES[3], 700), (PR_T[4]["submit"], 701), (MERGES[4], 800), (MERGES[5], 1111)]
def approvals(t):
    v = 111.0
    for tt, n in APPROVALS:
        if t >= tt: v = v + (n - v) * eout((t - tt) / 0.28) if t < tt + 0.28 else n
    return int(round(v))

# ------------------------------------------------------------------ temperature (her Next Token video's trick)
def temp(t):
    """0.70 at rest; Broke it! spikes to 2.0 (everything wanders); Fixed it! drops to 0.0 (everything snaps into place)."""
    v = 0.7
    for b, f in zip(BROKE, FIXED):
        if b - 0.05 <= t < f + 1.2:
            up = eout(seg(t, b - 0.03, b + 0.10)); dn = eout(seg(t, f - 0.02, f + 0.08)); back = ease(seg(t, f + 0.45, f + 1.1))
            v = 0.7 + 1.3 * up - 2.0 * dn * up + 0.7 * back * dn * up if t >= b - 0.03 else 0.7
            if t >= f - 0.02: v = 2.0 - 2.0 * dn + 0.7 * back
    return v
def hot(t): return clamp((temp(t) - 1.0) / 1.0)

def jit(key, t, amp):
    """the temperature jiggle: a per-element offset that re-rolls 15 times a second."""
    if amp <= 0.01: return 0.0, 0.0
    r = random.Random(zlib.crc32(repr((key, int(t * 15))).encode()))     # stable across processes (no hash())
    return r.uniform(-1, 1) * amp, r.uniform(-1, 1) * amp

# ------------------------------------------------------------------ scale-aware helpers
_FC = {}
def F(path, size):
    k = (path, int(round(size)))
    if k not in _FC: _FC[k] = ImageFont.truetype(path, max(6, int(round(size))))
    return _FC[k]

_SP = {}
def cache(key, fn):
    if key not in _SP:
        if len(_SP) > 900: _SP.clear()
        _SP[key] = fn()
    return _SP[key]

def ss(w, h, fn, s=3):
    img = Image.new("RGBA", (max(1, int(w * s)), max(1, int(h * s))), (0, 0, 0, 0))
    fn(ImageDraw.Draw(img), s)
    return img.resize((max(1, int(round(w))), max(1, int(round(h)))), Image.LANCZOS)

def paste(frame, spr, x, y, alpha=1.0):
    if alpha <= 0.004 or spr is None: return
    if frame.mode == "RGBA":
        xi, yi = int(round(x)), int(round(y)); W_, H_ = frame.size
        X0, Y0, X1, Y1 = max(0, xi), max(0, yi), min(W_, xi + spr.width), min(H_, yi + spr.height)
        if X1 <= X0 or Y1 <= Y0: return
        src = spr.crop((X0 - xi, Y0 - yi, X1 - xi, Y1 - yi))
        if alpha < 0.996: src = src.copy(); src.putalpha(src.getchannel("A").point(lambda v: int(v * alpha)))
        frame.alpha_composite(src, (X0, Y0)); return
    if alpha < 0.996:
        a = spr.getchannel("A").point(lambda v: int(v * alpha))
        frame.paste(spr, (int(round(x)), int(round(y))), a)
    else:
        frame.paste(spr, (int(round(x)), int(round(y))), spr)

def text_sprite(s, path, size, color, k, tracking=0):
    def mk():
        f = F(path, size * k); asc, desc = f.getmetrics()
        if not tracking:
            w = int(f.getlength(s)) + 8
            img = Image.new("RGBA", (max(w, 2), asc + desc + 4), color + (0,)); ImageDraw.Draw(img).text((4, 0), s, font=f, fill=color + (255,))
        else:
            tr = tracking * k; w = int(sum(f.getlength(c) + tr for c in s)) + 8
            img = Image.new("RGBA", (max(w, 2), asc + desc + 4), color + (0,)); d = ImageDraw.Draw(img); x = 4
            for c in s: d.text((x, 0), c, font=f, fill=color + (255,)); x += f.getlength(c) + tr
        return img
    return cache(("txt", s, path, size, color, k, tracking), mk)

def txt(frame, s, path, size, color, x, y, k, alpha=1.0, anchor="l", tracking=0):
    """x, y in design px (top of the text box); returns the width in design px."""
    sp = text_sprite(s, path, size, color, k, tracking)
    X = x * k - 4
    if anchor == "c": X = x * k - sp.width / 2
    elif anchor == "r": X = x * k - sp.width + 4
    paste(frame, sp, X, y * k, alpha)
    return (sp.width - 8) / k

def tw(s, path, size): return F(path, size).getlength(s)

def faded(frame, k, x0, y0, w, h, alpha, draw, blur=0.0):
    """draw a panel at full strength, or into its own layer and lay it down at `alpha` (off-focus / blocked)."""
    if alpha <= 0.004: return
    if alpha >= 0.995: draw(frame, 0.0, 0.0); return
    m = 50
    sub = Image.new("RGBA", (int(round((w + 2 * m) * k)), int(round((h + 2 * m) * k))), (0, 0, 0, 0))
    draw(sub, -(x0 - m), -(y0 - m))
    if blur > 0.3: sub = Image.fromarray(cv2.GaussianBlur(np.asarray(sub), (0, 0), blur * k))
    paste(frame, sub, (x0 - m) * k, (y0 - m) * k, alpha)

def focus(t):
    """how far the camera favours the review box (+1) or the checks (-1)."""
    z, cx, cy = cam(t)
    return clamp((cx - 960) / 160.0, -1, 1)

# ------------------------------------------------------------------ layout (design px, 1920x1080)
CX = 960
WX, WY, WW, WHT = 710, 184, 500, 690                 # the window
PX_L, PX_R, PY, PW, PH = 86, 1286, 248, 548, 392      # the checks panel (left) and the review box (right)
HDR_Y, HDR_LINE = 36, 146
WIDE, REVIEW, CHECKS = (1.0, 960.0, 540.0), (1.2, 1120.0, 470.0), (1.2, 800.0, 470.0)
RS = 1.3                                              # internal render scale (so a 1.3x push-in is still 1:1 pixels)

# ------------------------------------------------------------------ the diff (LGTM's document, scrolling on the beat)
DOC, AN = docmod.build()
LH, DW, DX0, DY0, FS = 34, 1520, 200, 150, 20
X_OLD, X_NEW, X_SIGN, X_CODE, X_FILE = 70, 142, 162, 190, 18

def strip(idx, k):
    def mk():
        lh, dw = int(round(LH * k)), int(round(DW * k))
        L = DOC[idx] if 0 <= idx < len(DOC) else {"k": "gap", "t": ""}
        kk = L["k"]
        band = {"add": GREEN_BG, "del": RED_BG, "file": (24, 24, 26), "hunk": (15, 17, 21)}.get(kk, BG)
        img = Image.new("RGB", (dw, lh), band); d = ImageDraw.Draw(img)
        fm, fb = F(MONO, FS * k), F(MONOB, (FS + 1) * k); ty = int(4 * k)
        if kk == "file":
            d.line([(0, 0), (dw, 0)], fill=FAINT, width=1); d.text((int(X_FILE * k), ty), L["t"], font=fb, fill=IVORY)
        elif kk == "hunk":
            d.text((int(X_CODE * k), ty), L["t"], font=fm, fill=(104, 116, 138))
        elif kk in ("add", "del", "ctx"):
            numc = (92, 90, 85)
            if L["o"] is not None: s = str(L["o"]); d.text((int(X_OLD * k) - fm.getlength(s), ty), s, font=fm, fill=numc)
            if L["n"] is not None: s = str(L["n"]); d.text((int(X_NEW * k) - fm.getlength(s), ty), s, font=fm, fill=numc)
            col = {"add": (188, 236, 206), "del": (240, 176, 180), "ctx": (150, 146, 138)}[kk]
            sign = {"add": "+", "del": "−", "ctx": " "}[kk]
            d.text((int(X_SIGN * k), ty), sign, font=fm, fill={"add": GREEN, "del": RED, "ctx": DIM}[kk])
            d.text((int(X_CODE * k), ty), L["t"], font=fm, fill=col)
        return np.asarray(img).copy()
    return cache(("strip", idx, k), mk)

_B0 = int(np.searchsorted(BEATS, T0 - 2.0))
def scroll_lines(t):
    """lines scrolled: 15 per beat, each beat's move eased into its first 42% (LGTM's snap-to-beat scroll)."""
    i = int(np.searchsorted(BEATS, t, side="right")) - 1
    if i < 0 or i >= len(BEATS) - 1: return 1060.0 + (t - T0) * 32
    u = (t - BEATS[i]) / (BEATS[i + 1] - BEATS[i])
    return 1060.0 + 15.0 * ((i - _B0) + ease(min(1.0, u / 0.42)))

def diff_layer(t, k, dim, hotk):
    vh = int(round((1080 - DY0) * k)); dw = int(round(DW * k)); lh = int(round(LH * k))
    s = scroll_lines(t) * lh; v = abs(scroll_lines(t + 1 / 30) * lh - s)
    blur = int(v * 0.5)
    out = np.empty((vh, dw, 3), np.uint8); out[:] = BG
    i0 = int(math.floor(s / lh)); i1 = int(math.floor((s + vh) / lh)) + 1
    for i in range(max(0, i0), min(len(DOC), i1)):
        y = int(round(i * lh - s)); st = strip(i, k)
        a = max(0, -y); b = min(lh, vh - y)
        if b <= a: continue
        if hotk > 0.02:
            dx, _ = jit(("row", i), t, 70 * k * hotk); dx = int(dx)
            row = np.roll(st[a:b], dx, axis=1)
            out[y + a:y + b] = row
        else:
            out[y + a:y + b] = st[a:b]
    if blur > 2: out = cv2.blur(out, (1, blur))
    return cv2.convertScaleAbs(out, alpha=dim, beta=10.0 * (1 - dim))       # dim toward BG (10, 10, 11)

# ------------------------------------------------------------------ the window: leaded tracery over glass made of diff lines
def arch_poly(w, ys, R, bottom, n=40, inset=0.0):
    pts = []; apex = math.acos((R - w / 2) / R)
    for i in range(n + 1):
        a = math.pi - apex * i / n; pts.append((R + (R - inset) * math.cos(a), ys - (R - inset) * math.sin(a)))
    for i in range(n + 1):
        a = apex * (1 - i / n); pts.append((w - R + (R - inset) * math.cos(a), ys - (R - inset) * math.sin(a)))
    pts.append((w - inset, bottom - inset)); pts.append((inset, bottom - inset))
    return pts
A_YS, A_R = 352, 372
HUB = (WW / 2, 212, 118)

def window_assets(k):
    def mk():
        w, h = int(round(WW * k)), int(round(WHT * k))
        outer = arch_poly(WW, A_YS, A_R, WHT)
        cx, cy, rr = HUB
        def draw_lead(d, s):
            P = lambda pts: [(x * k * s, y * k * s) for x, y in pts]
            col = IVORY + (255,); lw = lambda v: max(1, int(v * k * s))
            d.line(P(outer + [outer[0]]), fill=col, width=lw(2.6), joint="curve")
            inner = arch_poly(WW, A_YS, A_R, WHT, inset=13)
            d.line(P(inner + [inner[0]]), fill=IVORY + (150,), width=lw(1.1), joint="curve")
            for r, wd, al in [(rr, 2.2, 255), (rr - 11, 1.1, 150), (36, 1.8, 255)]:
                d.ellipse([(cx - r) * k * s, (cy - r) * k * s, (cx + r) * k * s, (cy + r) * k * s], outline=IVORY + (al,), width=lw(wd))
            for j in range(8):
                a = math.pi / 8 + j * math.pi / 4
                d.line(P([(cx + 36 * math.cos(a), cy + 36 * math.sin(a)), (cx + (rr - 11) * math.cos(a), cy + (rr - 11) * math.sin(a))]), fill=col, width=lw(1.5))
            for lx in (26, WW / 2 + 6):
                lw_, ly, lr = WW / 2 - 32, 470, 172
                lp = arch_poly(lw_, ly, lr, WHT - 26)
                d.line(P([(x + lx, y) for x, y in lp] + [(lp[0][0] + lx, lp[0][1])]), fill=col, width=lw(1.7), joint="curve")
                for yy in (540, 606): d.line(P([(lx, yy), (lx + lw_, yy)]), fill=IVORY + (170,), width=lw(1.1))
        lead = ss(w, h, draw_lead, 2)
        # a dark halo under the lead so it separates from bright footage
        la = np.asarray(lead.getchannel("A"), np.float32) / 255
        halo = cv2.GaussianBlur(cv2.dilate(la, np.ones((3, 3), np.uint8)), (0, 0), 1.6 * k)
        mask = np.asarray(ss(w, h, lambda d, s: d.polygon([(x * k * s, y * k * s) for x, y in arch_poly(WW, A_YS, A_R, WHT, inset=3)], fill=(255, 255, 255, 255)), 2).getchannel("A"), np.float32) / 255
        # the glass: rows of leaded bars, like diff lines (pitch 9, bar 6)
        rng = random.Random(54); lab = -np.ones((h, w), np.int32); bars = []
        y = WHT - 12
        while y > 4:
            x = 8 + rng.choice([0, 0, 6, 12])
            while x < WW - 8:
                ln = rng.randint(10, 36); x1 = min(WW - 6, x + ln)
                y0p, y1p, x0p, x1p = int(round(y * k)), int(round((y + 6) * k)), int(round(x * k)), int(round(x1 * k))
                if y1p > y0p and x1p > x0p:
                    lab[y0p:y1p, x0p:x1p] = len(bars); bars.append((y, x, x1))
                x = x1 + rng.randint(3, 6)
            y -= 9
        lab[mask < 0.5] = -1
        m = lab >= 0
        rows = np.array([b[0] for b in bars], np.float32)
        hub = np.zeros((h, w), np.float32)
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        hub = (np.hypot(xx - cx * k, yy - cy * k) < 34 * k).astype(np.float32)
        lf = np.asarray(lead, np.float32) / 255
        return dict(w=w, h=h, lead=lead, halo=halo, mask=mask, lab=lab, m=m, L=lab[m], n=len(bars), rows=rows, hub=hub,
                    mk=(mask * 0.97)[..., None], halo_k=(1 - halo * 0.55)[..., None], lead_rgb=np.ascontiguousarray(lf[..., :3]),
                    lead_a=np.ascontiguousarray(lf[..., 3:4]))
    return cache(("win", k), mk)

_GL = {}
def glass_rgb(i, t, k):
    """PR i's video as stained glass (float RGB, window size): each bar is filled with the mean colour of the footage
    under it, with a little of the footage itself kept so it stays recognizable."""
    A = window_assets(k); path, _, fx, off = VIDS[i]
    key = (i, int(round(t * 30)), k)
    if key in _GL: return _GL[key]
    tl = max(0.0, t - PR_T[i]["start"]) + off
    if path:
        fr = FT.frame(path, tl, 960, 540)
        fr = fr[int(540 * 0.13):] if "dont_wait" in path else fr[:int(540 * 0.86)]   # drop her burned-in captions
        hh = fr.shape[0]; ww_ = int(round(hh * WW / WHT)); x0 = int(round((960 - ww_) * fx))
        crop = cv2.resize(np.ascontiguousarray(fr[:, x0:x0 + ww_]), (A["w"], A["h"]), interpolation=cv2.INTER_CUBIC)
    else:
        crop = np.zeros((A["h"], A["w"], 3), np.float32) + 0.3
    L = A["L"]; cnt = np.bincount(L, minlength=A["n"]).astype(np.float32) + 1e-6
    mean = np.stack([np.bincount(L, weights=crop[..., c][A["m"]], minlength=A["n"]) / cnt for c in range(3)], 1)
    # light through glass: lift and saturate a little
    lum = mean.mean(1, keepdims=True); mean = np.clip(lum + (mean - lum) * 1.25, 0, 1) ** 0.85
    out = np.zeros((A["h"], A["w"], 3), np.float32) + np.array([9, 9, 11], np.float32) / 255
    dk = DETAIL[i]
    out[A["m"]] = (1 - dk) * mean[L] + dk * np.clip(crop[A["m"]] * 1.08, 0, 1)
    if len(_GL) > 24: _GL.clear()
    _GL[key] = (out, mean)
    return _GL[key]

def window_layer(canvas, t, k, glow_amt, hotk):
    """canvas: float RGB (internal res). Returns nothing."""
    A = window_assets(k); i = pr_at(t)
    new, _ = glass_rgb(i, t, k)
    p = PR_T[i]; b0 = p["build"]
    glass = new
    if b0 is not None and t < b0 + 0.36 and i > 0:
        # the new glass is leaded in from the bottom row up over the old video (LGTM's build, sped up)
        u = eout(seg(t, b0, b0 + 0.34)) if t >= b0 else 0.0
        old, _ = glass_rgb(i - 1, min(t, PR_T[i]["start"] - 1 / 30), k) if t >= b0 else glass_rgb(i - 1, t, k)
        yf = (1 - u) * A["h"]
        ys = np.arange(A["h"], dtype=np.float32)[:, None, None]
        front = np.clip((ys - yf) / (40 * k), 0, 1)
        fresh = np.exp(-np.abs(ys - yf) / (26 * k)) * (u < 0.999)
        glass = old * (1 - front) + new * front
        glass = glass + (np.array([0.96, 0.95, 0.92], np.float32) - glass) * (fresh * 0.75) * A["m"][..., None]
    if hotk > 0.02:
        # temperature: each row of glass wanders sideways and the bars drift (the window "breaks")
        g2 = np.zeros_like(glass) + np.array([9, 9, 11], np.float32) / 255
        lab = A["lab"]; rows_px = int(round(9 * k))
        for r0 in range(0, A["h"], max(1, rows_px)):
            dx, dy = jit(("wrow", r0), t, 46 * k * hotk)
            r1 = min(A["h"], r0 + rows_px)
            src = np.roll(glass[r0:r1], int(dx), axis=1)
            y0 = int(clamp(r0 + int(dy * 0.4), 0, A["h"] - (r1 - r0)))
            g2[y0:y0 + (r1 - r0)] = src
        tint = np.array([1.0, 0.55, 0.55], np.float32)
        glass = g2 * (1 - 0.35 * hotk) + g2 * tint * 0.35 * hotk
    x0, y0 = int(round(WX * k)), int(round(WY * k)); h, w = A["h"], A["w"]
    # glow: the glass's own light on the stone around it (additive, computed small)
    if glow_amt > 0.01:
        sm = cv2.resize(glass * A["mask"][..., None], (w // 6, h // 6), interpolation=cv2.INTER_AREA)
        padp = max(8, int(40 * k / 6 * 4))
        big = cv2.copyMakeBorder(sm, padp, padp, padp, padp, cv2.BORDER_CONSTANT, value=0)
        big = cv2.GaussianBlur(big, (0, 0), 7 * k)
        G = cv2.resize(big * (255.0 * glow_amt), (big.shape[1] * 6, big.shape[0] * 6), interpolation=cv2.INTER_LINEAR)
        gx, gy = x0 - padp * 6, y0 - padp * 6
        add_region(canvas, np.clip(G, 0, 255).astype(np.uint8), gx, gy)
    reg = canvas[y0:y0 + h, x0:x0 + w].astype(np.float32) * (1 / 255.0)
    mk = A["mk"]
    reg = reg * (1 - mk) + glass * mk
    reg *= A["halo_k"]
    lead, la = A["lead_rgb"], A["lead_a"]
    if hotk > 0.02:
        dx, dy = jit("lead", t, 10 * k * hotk)
        la = np.roll(np.roll(la, int(dx), 1), int(dy), 0); lead = np.roll(np.roll(lead, int(dx), 1), int(dy), 0)
    reg = reg * (1 - la) + lead * la
    canvas[y0:y0 + h, x0:x0 + w] = (np.clip(reg, 0, 1) * 255 + 0.5).astype(np.uint8)

def add_region(canvas, G, gx, gy):
    H, W = canvas.shape[:2]; h, w = G.shape[:2]
    X0, Y0, X1, Y1 = max(0, gx), max(0, gy), min(W, gx + w), min(H, gy + h)
    if X1 <= X0 or Y1 <= Y0: return
    canvas[Y0:Y1, X0:X1] = cv2.add(canvas[Y0:Y1, X0:X1], np.ascontiguousarray(G[Y0 - gy:Y1 - gy, X0 - gx:X1 - gx]))

def rays(k):
    def mk():
        W_, H_ = int(round(1920 * k)), int(round(1080 * k))
        img = Image.new("RGB", (W_, H_), (0, 0, 0)); d = ImageDraw.Draw(img)
        ox, oy = CX * k, (WY + 212) * k; rng = random.Random(7)
        for j in range(9):
            a = math.radians(38 + j * 13 + rng.uniform(-3, 3)); wd = math.radians(rng.uniform(2.2, 4.5)); L = 2600 * k
            c = rng.choice([(34, 46, 38), (44, 42, 36), (40, 30, 30)])
            d.polygon([(ox, oy), (ox + L * math.cos(a - wd), oy + L * math.sin(a - wd)), (ox + L * math.cos(a + wd), oy + L * math.sin(a + wd))], fill=c)
        return np.asarray(img.filter(ImageFilter.GaussianBlur(22 * k))).copy()
    return cache(("rays", k), mk)

def scrim(k):
    def mk():
        CHp = int(round(1080 * k)); CWp = int(round(1920 * k))
        ys = np.arange(CHp, dtype=np.float32) / k
        sc_ = np.clip((ys - 900) / 180, 0, 1) ** 1.3 * 0.75 + np.clip((175 - ys) / 60, 0, 1) * 0.6
        return np.ascontiguousarray(np.broadcast_to(((1 - sc_) * 255)[:, None, None], (CHp, CWp, 3))).astype(np.uint8)
    return cache(("scrim", k), mk)

# ------------------------------------------------------------------ choir (LGTM's reviewers)
def singer(k, lit):
    def mk():
        g = (150, 250, 180) if lit else GREEN
        def fn(d, s):
            q = k * s
            d.ellipse([17 * q, 6 * q, 47 * q, 36 * q], outline=IVORY + (255,), width=max(1, int(1.6 * q)))
            d.line([(24 * q, 21 * q), (30 * q, 27 * q), (40 * q, 15 * q)], fill=g + (255,), width=max(1, int((3.2 if lit else 2.4) * q)), joint="curve")
            d.line([(22 * q, 44 * q), (42 * q, 44 * q), (56 * q, 118 * q), (8 * q, 118 * q), (22 * q, 44 * q)], fill=IVORY + (230,), width=max(1, int(1.4 * q)), joint="curve")
            d.line([(32 * q, 44 * q), (32 * q, 118 * q)], fill=IVORY + (90,), width=max(1, int(1 * q)))
        sp = ss(64 * k, 124 * k, fn, 3)
        back = Image.new("RGBA", sp.size, BG + (0,)); bd = ImageDraw.Draw(back)
        bd.polygon([(22 * k, 44 * k), (42 * k, 44 * k), (56 * k, 118 * k), (8 * k, 118 * k)], fill=BG + (235,))
        bd.ellipse([17 * k, 6 * k, 47 * k, 36 * k], fill=BG + (235,))
        if lit:
            gl = Image.new("RGBA", sp.size, (0, 0, 0, 0)); ImageDraw.Draw(gl).ellipse([14 * k, 3 * k, 50 * k, 39 * k], fill=GREEN + (90,))
            back.alpha_composite(gl.filter(ImageFilter.GaussianBlur(5 * k)))
        back.alpha_composite(sp)
        return back
    return cache(("singer", k, lit), mk)

CHOIR = []
for r in range(3):
    for side in (-1, 1):
        for j in range(6 - r):
            CHOIR.append((r, CX + side * (338 + j * 70 + r * 35), 712 + r * 44, (j + r) % 2, j, side))
CHOIR.sort(key=lambda c: c[0])

def choir_layer(frame, t, k, hotk):
    i = int(np.searchsorted(BEATS, t, side="right")) - 1
    bp = math.exp(-7.0 * (t - BEATS[i])) if i >= 0 else 0.0
    subs = [p["submit"] for p in PR_T if p["submit"]] + MERGES
    for n, (r, x, y, par, j, side) in enumerate(CHOIR):
        bob = -11 * bp * (1.0 if (i % 2) == par else 0.25)
        lit = False
        for ts in subs:   # the reviewers approve in a wave, outward from the window
            tl = ts + 0.025 * j + 0.03 * r
            if tl <= t < tl + 0.42: lit = True
        dx, dy = jit(("singer", n), t, 16 * hotk)
        paste(frame, singer(k, lit), (x - 32 + dx) * k, (y - 60 + bob + dy) * k)

# ------------------------------------------------------------------ the review box (right) and the merge box
def panel_bg(w, h, k, outline=IVORY, oa=190):
    def fn(d, s):
        q = k * s
        d.rounded_rectangle([1 * q, 1 * q, (w - 1) * q, (h - 1) * q], radius=18 * q, fill=(12, 12, 13, 246), outline=outline + (oa,), width=max(1, int(1.4 * q)))
    return cache(("panel", w, h, k, outline, oa), lambda: ss(w * k, h * k, fn, 2))

def radio(k, on, col=GREEN):
    def fn(d, s):
        q = k * s
        d.ellipse([2 * q, 2 * q, 30 * q, 30 * q], outline=(col if on else DIM) + (255,), width=max(1, int(2 * q)))
        if on: d.ellipse([9 * q, 9 * q, 23 * q, 23 * q], fill=col + (255,))
    return cache(("radio", k, on, col), lambda: ss(32 * k, 32 * k, fn, 3))

def button(label, w, h, k, hot, size=32, col=IVORY, fill_col=None):
    def fn(d, s):
        q = k * s; fc = fill_col or col
        d.rounded_rectangle([1 * q, 1 * q, (w - 1) * q, (h - 1) * q], radius=(h / 2) * q, fill=(fc + (255,)) if hot else (12, 12, 13, 250), outline=fc + (255,), width=max(1, int(1.6 * q)))
        f = F(INTERB, size * q); tw_ = f.getlength(label); asc, desc = f.getmetrics()
        d.text(((w * q - tw_) / 2, (h * q - (asc + desc)) / 2 + 1 * q), label, font=f, fill=(BG if hot else col) + (255,))
    return cache(("btn", label, w, h, k, hot, size, col, fill_col), lambda: ss(w * k, h * k, fn, 2))

APPROVE_XY = (PX_R + 52, PY + 162)          # radio centre (design px)
SUBMIT_BOX = (PX_R + PW - 36 - 272, PY + PH - 36 - 66, 272, 66)
MERGE_BOX = (PX_R + 36, PY + 160, PW - 72, 88)

def review_state(t):
    """('review', approved, submitted) | ('merge', enabled, merged, note) for the right panel; and a crossfade."""
    i = pr_at(t); p = PR_T[i]
    if p["approve"] is not None:
        morph = p["submit"] + 0.11
        if t < morph: return ("review", t >= p["approve"], t >= p["submit"] - 0.02), i
        return ("merge", True, t >= p["merge"] - 0.02, "All checks have passed"), i
    if "fixed" in p:
        en = t >= p["fixed"]
        note = "Checks running…" if t < p["made"] + 0.3 else ("Checks failed: prod" if t < p["fixed"] else "All checks have passed")
        return ("merge", en, t >= p["merge"] - 0.02, note), i
    return ("merge", True, t >= p["merge"] - 0.02, "All checks have passed"), i

def review_layer(frame, t, k, hotk):
    st, i = review_state(t)
    dx, dy = jit("rev", t, 18 * hotk)
    blocked = st[0] == "merge" and not st[1] and not st[2]
    a = (0.42 if blocked else 1.0) * (1 - 0.62 * clamp(-focus(t)))
    faded(frame, k, PX_R, PY, PW, PH, a, lambda fr, ox, oy: review_draw(fr, t, k, st, i, dx + ox, dy + oy), 4.0 * clamp(-focus(t)))

def review_draw(frame, t, k, st, i, dx, dy):
    x, y = PX_R + dx, PY + dy
    paste(frame, panel_bg(PW, PH, k), x * k, y * k)
    if st[0] == "review":
        _, appr, subm = st
        txt(frame, "Finish your review", INTERB, 38, IVORY, x + 36, y + 30, k)
        txt(frame, "0 / 187 files viewed", MONO, 34, DIM, x + 36, y + 86, k)
        paste(frame, radio(k, appr), (APPROVE_XY[0] + dx - 16) * k, (APPROVE_XY[1] + dy - 16) * k)
        txt(frame, "Approve", INTER, 36, IVORY, x + 88, y + 140, k)
        paste(frame, radio(k, False), (APPROVE_XY[0] + dx - 16) * k, (APPROVE_XY[1] + 52 + dy - 16) * k)
        txt(frame, "Request changes", INTER, 36, DIM, x + 88, y + 192, k)
        bx, by, bw, bh = SUBMIT_BOX
        paste(frame, button("Submit review", bw, bh, k, subm, 32), (bx + dx) * k, (by + dy) * k)
    else:
        _, en, merged, note = st
        if merged:
            txt(frame, "Pull request merged", INTERB, 38, IVORY, x + 36, y + 30, k)
            txt(frame, "0 lines read", MONO, 34, GREEN, x + 36, y + 86, k)
        else:
            txt(frame, "Ready to merge" if en else "Merging is blocked", INTERB, 38, IVORY if en else DIM, x + 36, y + 30, k)
            col = GREEN if note.startswith("All") else RED if "failed" in note else DIM
            txt(frame, note, MONO, 34, col, x + 36, y + 86, k)
        bx, by, bw, bh = MERGE_BOX
        label = "Merged" if merged else "Merge pull request"
        fc = (168, 132, 255) if merged else IVORY
        paste(frame, button(label, bw, bh, k, merged, 36, col=IVORY if not merged else fc, fill_col=fc if merged else None), (bx + dx) * k, (by + dy) * k,
              1.0 if en or merged else 0.45)
        txt(frame, "no one will notice", CORMI, 42, DIM, x + PW / 2, y + PH - 84, k, 1.0, anchor="c")

# ------------------------------------------------------------------ the checks panel (left)
def icon(kind, k):
    def fn(d, s):
        q = k * s
        if kind == "pass":
            d.ellipse([2 * q, 2 * q, 34 * q, 34 * q], outline=GREEN + (255,), width=max(1, int(2.2 * q)))
            d.line([(10 * q, 18 * q), (15.5 * q, 23.5 * q), (26 * q, 12 * q)], fill=GREEN + (255,), width=max(1, int(3 * q)), joint="curve")
        elif kind == "fail":
            d.ellipse([2 * q, 2 * q, 34 * q, 34 * q], fill=RED + (255,))
            d.line([(12 * q, 12 * q), (24 * q, 24 * q)], fill=BG + (255,), width=max(1, int(3.4 * q)))
            d.line([(24 * q, 12 * q), (12 * q, 24 * q)], fill=BG + (255,), width=max(1, int(3.4 * q)))
        else:
            d.ellipse([2 * q, 2 * q, 34 * q, 34 * q], outline=FAINT + (255,), width=max(1, int(2.2 * q)))
            d.arc([2 * q, 2 * q, 34 * q, 34 * q], -90, 30, fill=(200, 170, 90, 255), width=max(1, int(3 * q)))
    return cache(("icon", kind, k), lambda: ss(36 * k, 36 * k, fn, 3))

def thermo(k, col):
    def fn(d, s):
        q = k * s
        d.rounded_rectangle([13 * q, 3 * q, 23 * q, 25 * q], radius=5 * q, outline=col + (255,), width=max(1, int(2 * q)))
        d.ellipse([9 * q, 20 * q, 27 * q, 36 * q], fill=col + (255,))
    return cache(("thermo", k, col), lambda: ss(36 * k, 38 * k, fn, 3))

def checks_state(t):
    """rows [(label, detail, state)], big chip (text, colour), temperature."""
    i = pr_at(t); p = PR_T[i]
    rows = [["build", "", "pass"], ["tests", "0 ran", "pass"], ["prod", "", "pass"]]
    chip = ("passing", GREEN)
    if "made" in p:
        m, b, f = p["made"], p["broke"], p["fixed"]
        for j, tt in enumerate((m, m + 0.12, m + 0.24)):
            rows[j][2] = "pass" if t >= tt else "pend"
        chip = ("running…", DIM) if t < m else ("build passing", GREEN)
        if t >= b: rows[2] = ["prod", "down", "fail"]; chip = ("prod is down", RED)
        if t >= f: rows[2] = ["prod", "hotfix", "pass"]; chip = ("fixed", GREEN)
    if t >= p["merge"] - 0.02: chip = ("shipped", GREEN)
    return rows, chip

def chip_sprite(label, col, k):
    def mk():
        f = F(INTERB, 36 * k); w = f.getlength(label) / k + 84; h = 58
        def fn(d, s):
            q = k * s; ff = F(INTERB, 36 * q)
            d.rounded_rectangle([0, 0, w * q, h * q], radius=h / 2 * q, fill=col + (255,) if col != DIM else (30, 30, 32, 255))
            d.ellipse([24 * q, (h / 2 - 8) * q, 40 * q, (h / 2 + 8) * q], fill=(BG if col != DIM else DIM) + (255,))
            asc, desc = ff.getmetrics()
            d.text((54 * q, (h * q - (asc + desc)) / 2), label, font=ff, fill=(BG if col != DIM else IVORY) + (255,))
        return ss(w * k, h * k, fn, 2)
    return cache(("chip", label, col, k), mk)

def checks_layer(frame, t, k, hotk):
    a = 1 - 0.62 * clamp(focus(t))
    faded(frame, k, PX_L, PY, PW, PH, a, lambda fr, ox, oy: checks_draw(fr, t, k, hotk, ox, oy), 4.0 * clamp(focus(t)))

def checks_draw(frame, t, k, hotk, ox, oy):
    rows, chip = checks_state(t)
    dx, dy = jit("chk", t, 18 * hotk)
    x, y = PX_L + dx + ox, PY + dy + oy
    i = pr_at(t)
    paste(frame, panel_bg(PW, PH, k, RED if chip[1] == RED else IVORY, 230 if chip[1] == RED else 190), x * k, y * k)
    txt(frame, "Checks", INTERB, 38, IVORY, x + 36, y + 30, k)
    tp = temp(t)
    tcol = RED if tp > 1.3 else (GREEN if tp < 0.2 else DIM)
    ex, ey = jit("trow", t, 22 * hotk)
    txt(frame, "temperature", MONO, 34, DIM, x + 90 + ex, y + 92 + 3 * 48 + ey * 0.3, k)
    txt(frame, f"{tp:.2f}", MONOB, 34, tcol if tp > 1.3 or tp < 0.2 else IVORY, x + PW - 36 + ex, y + 92 + 3 * 48 + ey * 0.3, k, anchor="r")
    paste(frame, thermo(k, tcol), (x + 36 + ex) * k, (y + 94 + 3 * 48 + ey * 0.3) * k)
    for j, (lab, det, st) in enumerate(rows):
        ry = y + 92 + j * 48
        ex, ey = jit(("crow", j), t, 26 * hotk); ey *= 0.3
        paste(frame, icon(st, k), (x + 36 + ex) * k, (ry + 2 + ey) * k)
        txt(frame, lab, MONO, 34, IVORY if st != "pend" else DIM, x + 90 + ex, ry - 2 + ey, k)
        if det: txt(frame, det, MONO, 34, RED if st == "fail" else DIM, x + PW - 36 + ex, ry - 2 + ey, k, anchor="r")
    sp = chip_sprite(chip[0], chip[1], k)
    pop = 1.0
    for tt in (MADE + BROKE + FIXED + MERGES):
        if tt <= t < tt + 0.25: pop = 1 + 0.12 * math.exp(-(t - tt) / 0.06)
    if pop > 1.004: sp = sp.resize((int(sp.width * pop), int(sp.height * pop)), Image.BILINEAR)
    ex, ey = jit("chip", t, 30 * hotk); ey *= 0.25
    paste(frame, sp, (x + 36 + ex) * k - (sp.width - sp.width / pop) / 2, (y + PH - 30 - 58 + ey) * k - (sp.height - sp.height / pop) / 2)

# ------------------------------------------------------------------ header
def pill(text, col, k):
    def mk():
        f = F(INTERB, 26 * k); w = f.getlength(text) / k + 40; h = 42
        def fn(d, s):
            q = k * s; ff = F(INTERB, 26 * q); asc, desc = ff.getmetrics()
            d.rounded_rectangle([1 * q, 1 * q, (w - 1) * q, (h - 1) * q], radius=h / 2 * q, outline=col + (255,), width=max(1, int(1.6 * q)))
            d.text((20 * q, (h * q - (asc + desc)) / 2), text, font=ff, fill=col + (255,))
        return ss(w * k, h * k, fn, 3)
    return cache(("pill", text, col, k), mk)

def header_layer(frame, t, k, hotk):
    i = pr_at(t); p = PR_T[i]; merged = t >= p["merge"] - 0.02
    dx, dy = jit("hdr", t, 14 * hotk)
    num, title = f"#{1111 + i}", f"ship: {VIDS[i][1]}"
    sp = pill("Merged" if merged else "Open", (168, 132, 255) if merged else GREEN, k)
    wtot = tw(num, MONO, 34) + 18 + tw(title, INTERB, 42) + 22 + sp.width / k
    x = CX - wtot / 2
    x += txt(frame, num, MONO, 34, DIM, x + dx, HDR_Y + 6 + dy, k) + 18
    x += txt(frame, title, INTERB, 42, IVORY, x + dx, HDR_Y + dy, k) + 22
    paste(frame, sp, (x + dx) * k, (HDR_Y + 8 + dy) * k)
    # approvals and lines read (LGTM's counters, bigger), centred under the title
    n = approvals(t); pop = 0.0
    for tt, _ in APPROVALS:
        if tt <= t < tt + 0.3: pop = math.exp(-(t - tt) / 0.08)
    col = mix(IVORY, GREEN, pop)
    y2 = HDR_Y + 58
    parts = [("approvals", MONO, 34, DIM, 12, 6), (f"{n:,}", MONOB, 42, col, 56, -3 * pop), ("lines read", MONO, 34, DIM, 12, 6), ("0", MONOB, 42, IVORY, 0, 0)]
    wtot = sum(tw(s_, f_, z_) + g_ for s_, f_, z_, c_, g_, o_ in parts) + tw("8,888", MONOB, 42) - tw(f"{n:,}", MONOB, 42)
    x = CX - wtot / 2
    ex, ey = jit("cnt", t, 14 * hotk)
    for s_, f_, z_, c_, g_, o_ in parts:
        w_ = txt(frame, s_, f_, z_, c_, x + ex, y2 + o_ + ey, k)
        x += (max(w_, tw("8,888", MONOB, 42)) if f_ == MONOB and s_ != "0" else w_) + g_

# ------------------------------------------------------------------ the LGTM stamp
def stamp_sprite(k, ang):
    def mk():
        w, h = 620, 324
        def fn(d, s):
            q = k * s; c = GREEN + (255,)
            d.rounded_rectangle([8 * q, 8 * q, (w - 8) * q, (h - 8) * q], radius=26 * q, outline=c, width=max(1, int(9 * q)))
            d.rounded_rectangle([26 * q, 26 * q, (w - 26) * q, (h - 26) * q], radius=14 * q, outline=c, width=max(1, int(2 * q)))
            f = F(CINZB, 136 * q); tw_ = f.getlength("LGTM"); d.text(((w * q - tw_) / 2, 74 * q), "LGTM", font=f, fill=c)
            for s_, yy, sz, tr in (("REVIEWED  ·  APPROVED", 40, 24, 3), ("0 LINES READ", 236, 36, 5)):
                f2 = F(MONOB, sz * q); tws = sum(f2.getlength(ch) + tr * q for ch in s_) - tr * q; xx = (w * q - tws) / 2
                for ch in s_: d.text((xx, yy * q), ch, font=f2, fill=c); xx += f2.getlength(ch) + tr * q
        img = ss(w * k, h * k, fn, 2)
        rng = np.random.default_rng(3); W_, H_ = img.size
        n = rng.random((max(2, H_ // 4), max(2, W_ // 4))).astype(np.float32)
        n = cv2.GaussianBlur(cv2.resize(n, (W_, H_), interpolation=cv2.INTER_CUBIC), (0, 0), 1.2)
        wear = np.clip((n - 0.22) * 4.0, 0.45, 1.0)
        a = np.asarray(img.getchannel("A"), np.float32) * wear
        img.putalpha(Image.fromarray(a.astype(np.uint8)))
        return img.rotate(ang, expand=True, resample=Image.BICUBIC)
    return cache(("stamp", k, ang), mk)
STAMP_ANG = [-9, 6, -5, 10, -8, 5]

def stamp_layer(frame, t, k):
    for j, m in enumerate(MERGES):
        tau = t - m
        if tau < 0: continue
        nxt = PR_T[j + 1]["start"] if j + 1 < len(PR_T) else 1e9
        out = seg(t, nxt - 0.02, nxt + 0.1)
        if out >= 1: continue
        sp = stamp_sprite(k, STAMP_ANG[j]); sc = 1 + 1.2 * math.exp(-tau * 26)
        if abs(sc - 1) > 0.01: sp = sp.resize((int(sp.width * sc), int(sp.height * sc)), Image.BILINEAR)
        a = clamp(tau * 18) * (1 - out)
        paste(frame, sp, CX * k - sp.width / 2, 610 * k - sp.height / 2, a)

# ------------------------------------------------------------------ cursor
def cursor(k):
    def fn(d, s):
        q = k * s; pts = [(2, 2), (2, 30), (9, 23), (14, 34), (19, 32), (14, 21), (24, 21)]
        d.polygon([(x * q, y * q) for x, y in pts], fill=IVORY + (255,))
        d.line([(x * q, y * q) for x, y in pts + [pts[0]]], fill=BG + (255,), width=max(1, int(1.8 * q)))
    return cache(("cursor", k), lambda: ss(30 * k, 40 * k, fn, 3))

def cursor_targets():
    """[(time, (x, y), click?)] — where the pointer is and when it clicks (design px)."""
    ev = []
    sx, sy = SUBMIT_BOX[0] + SUBMIT_BOX[2] * 0.55, SUBMIT_BOX[1] + SUBMIT_BOX[3] * 0.55
    mx, my = MERGE_BOX[0] + MERGE_BOX[2] * 0.62, MERGE_BOX[1] + MERGE_BOX[3] * 0.56
    ax, ay = APPROVE_XY
    for p in PR_T:
        if p["approve"] is not None:
            ev += [(p["approve"], (ax, ay), True), (p["submit"], (sx, sy), True), (p["merge"], (mx, my), True)]
        else:
            ev += [(p["merge"], (mx, my), True)]
    return sorted(ev)
CUR = cursor_targets()

def cursor_pos(t):
    prev = (CUR[0][0] - 0.5, (APPROVE_XY[0] + 60, APPROVE_XY[1] + 90))
    for tt, xy, _ in CUR:
        if t < tt:
            a, pxy = prev; u = eio(seg(t, max(a + 0.04, tt - 0.2), tt - 0.02))
            return (pxy[0] + (xy[0] - pxy[0]) * u, pxy[1] + (xy[1] - pxy[1]) * u)
        prev = (tt, xy)
    return prev[1]

def cursor_layer(frame, t, k, hotk):
    x, y = cursor_pos(t)
    dx, dy = jit("cur", t, 20 * hotk)
    d = ImageDraw.Draw(frame)
    for tt, (cx, cy), c in CUR:
        tau = t - tt
        if 0 <= tau < 0.36:
            r = (10 + 70 * eout(tau / 0.36)) * k; a = 1 - tau / 0.36
            d.ellipse([cx * k - r, cy * k - r, cx * k + r, cy * k + r], outline=mix(BG, IVORY, a * 0.9), width=max(1, int(3 * k)))
    paste(frame, cursor(k), (x + dx) * k, (y + dy) * k)

# ------------------------------------------------------------------ camera
SHOTS = [(T0 - 1, REVIEW)]
_ARR = [(MERGES[0], WIDE), (CLICKS[2], REVIEW), (MERGES[1], WIDE), (MADE[0], CHECKS), (SHIPPED[0], WIDE),
        (CLICKS[4], REVIEW), (MERGES[4], WIDE), (MADE[1], CHECKS), (SHIPPED[2], WIDE)]
WHIP = 0.16
def cam(t):
    z, cx, cy = REVIEW
    prev = REVIEW
    for ta, fr in _ARR:
        if t < ta - WHIP: break
        u = eio(seg(t, ta - WHIP, ta))
        z = prev[0] + (fr[0] - prev[0]) * u; cx = prev[1] + (fr[1] - prev[1]) * u; cy = prev[2] + (fr[2] - prev[2]) * u
        if t < ta: return z, cx, cy
        prev = fr
    z, cx, cy = prev
    # slow drift so holds breathe
    z *= 1 + 0.008 * math.sin(t * 1.3)
    return z, cx, cy

def punch(t):
    p = 0.0
    for tt in CLICKS + MERGES:
        if tt <= t < tt + 0.4: p = max(p, 0.028 * math.exp(-(t - tt) / 0.07))
    return p

def shake(t):
    dx = dy = 0.0
    for j, m in enumerate(MERGES):
        tau = t - m
        if 0 <= tau < 0.45:
            amp = 9 * math.exp(-tau * 9); dx += amp * math.sin(tau * 71 + j); dy += amp * math.cos(tau * 83 + 2 * j)
    for b in BROKE:
        tau = t - b
        if 0 <= tau < 0.5:
            amp = 16 * math.exp(-tau * 6); dx += amp * math.sin(tau * 61); dy += amp * math.cos(tau * 77)
    return dx, dy

# ------------------------------------------------------------------ frame
def render_frame(t, W=1920, H=1080):
    t = float(t)
    k = RS * W / 1920.0
    CWp, CHp = int(round(1920 * k)), int(round(1080 * k))
    hk = hot(t)
    frame = Image.new("RGB", (CWp, CHp), BG)
    frame.paste(Image.fromarray(diff_layer(t, k, 0.22, hk)), (int(round(DX0 * k)), int(round(DY0 * k))))
    canvas = np.asarray(frame).copy()
    # rays on every merge, the window's glow on the beat
    i = int(np.searchsorted(BEATS, t, side="right")) - 1
    bp = math.exp(-7.0 * (t - BEATS[i])) if i >= 0 else 0.0
    burst = 0.0
    for m in MERGES:
        if m <= t < m + 1.2: burst = max(burst, math.exp(-(t - m) / 0.35))
    canvas = cv2.addWeighted(canvas, 1.0, rays(k), 0.08 + 0.08 * bp + 0.32 * burst, 0)
    window_layer(canvas, t, k, 0.55 + 0.25 * bp + 0.5 * burst, hk)
    # scrims: under the header, and the floor
    canvas = cv2.multiply(canvas, scrim(k), scale=1 / 255.0)
    frame = Image.fromarray(canvas)
    choir_layer(frame, t, k, hk)
    checks_layer(frame, t, k, hk)
    review_layer(frame, t, k, hk)
    header_layer(frame, t, k, hk)
    stamp_layer(frame, t, k)
    cursor_layer(frame, t, k, hk)
    img = np.asarray(frame)
    # camera: crop the design window at zoom z around (cx, cy), with a punch on every click and a whip blur
    z, cx, cy = cam(t); z *= 1 + punch(t)
    sx, sy = shake(t); cx -= sx / z; cy -= sy / z
    vw, vh = 1920 / z, 1080 / z
    cx = clamp(cx, vw / 2, 1920 - vw / 2) if z >= 1 else 960; cy = clamp(cy, vh / 2, 1080 - vh / 2) if z >= 1 else 540
    x0, y0 = (cx - vw / 2) * k, (cy - vh / 2) * k
    M = np.array([[W / (vw * k), 0, -x0 * W / (vw * k)], [0, H / (vh * k), -y0 * H / (vh * k)]], np.float32)
    f = W / (vw * k)
    if f < 0.98:   # downscale with area filtering first, then a sub-pixel translate (no shimmer on slow drifts)
        big = cv2.resize(img, (int(round(img.shape[1] * f)), int(round(img.shape[0] * f))), interpolation=cv2.INTER_AREA)
        fx_, fy_ = big.shape[1] / img.shape[1], big.shape[0] / img.shape[0]
        M2 = np.array([[1, 0, -x0 * fx_], [0, 1, -y0 * fy_]], np.float32)
        out = cv2.warpAffine(big, M2, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    else:
        out = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    # whip blur from the camera's own motion
    z2, cx2, cy2 = cam(t + 1 / 60.0); z1, cx1, cy1 = cam(t - 1 / 60.0)
    vx = (cx2 - cx1) * z * W / 1920 * 30 / 2 / 30 * 0.9      # px moved per frame (half shutter)
    vy = (cy2 - cy1) * z * W / 1920 * 0.45
    vz = abs(z2 - z1) * W * 0.25
    L = int((abs(vx) + vz) * 0.75)
    if L > 2: out = cv2.blur(out, (L, 1))
    if abs(vy) > 2: out = cv2.blur(out, (1, int(abs(vy))))
    # flash on merges (restrained), red tint while it's broken
    fl = 0.0
    for m in MERGES:
        if 0 <= t - m < 0.3: fl = max(fl, 0.10 * math.exp(-(t - m) * 16))
    if fl > 0.004 or hk > 0.02:
        out = out.astype(np.float32) * (1 / 255.0)
        if fl > 0.004: out = out * (1 - fl) + np.array(IVORY, np.float32) / 255 * fl
        if hk > 0.02: out = out * (1 - 0.10 * hk) + out * np.array([1.25, 0.8, 0.8], np.float32) * 0.10 * hk
        return (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)
    return np.ascontiguousarray(out)
