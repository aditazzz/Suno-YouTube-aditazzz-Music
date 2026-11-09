"""Short E, part 1 at 9:16: "Click! Click! Ship it!" in the LGTM cathedral (frames 1713-1962, song 57.10-65.43).

The 16:9 shot is wide (checks left, window centre, review right, the camera whipping between them). For a phone the
cathedral is re-laid out as a column, centred on the safe column (x 500): the PR header on three lines (number + state,
the video being shipped at 50 px, approvals / lines read), the stained-glass window 1.05x bigger, the choir flanking
its foot, and ONE panel slot under it (x 70-930, y 1100-1480) that shows the review box or the checks, switching with a
whip on the same beats the film's camera whips (REVIEW and WIDE shots -> review box, CHECKS shots -> checks). Clicks
punch, merges shake, Broke it! jiggles, exactly as in the film. Everything read stays left of 0.88 W and above 0.78 H.
Runs on a PRIVATE copy of s2_lgtm (shorts_dg.private): the film's module is untouched.
render_frame(t, W, H) for 9:16 (16:9 falls through to s2_lgtm)."""
import os, sys, math
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shorts_dg as SD

L = SD.private("shortE_lgtm_impl", "s2_lgtm.py")
clamp, eio, eout, seg, ease = L.clamp, L.eio, L.eout, L.seg, L.ease

DW_, DH_ = 1080, 1920                     # design canvas (px at 1080x1920)
CXV = 500                                  # centre of the composition (the safe column is 0..950)
WS = 1.05                                  # window scale
WY_PX = 352
# ---- patch the private module's layout for the column
L.CX = CXV
L.WX = (CXV - L.WW * WS / 2) / WS; L.WY = WY_PX / WS
L.PX_L = L.PX_R = 70; L.PY = 1100; L.PW = 860; L.PH = 380
L.APPROVE_XY = (L.PX_R + 52, L.PY + 162)
L.SUBMIT_BOX = (L.PX_R + L.PW - 36 - 272, L.PY + L.PH - 36 - 66, 272, 66)
L.MERGE_BOX = (L.PX_R + 36, L.PY + 160, L.PW - 72, 88)
L.CUR = L.cursor_targets()
WIN_BOT = WY_PX + L.WHT * WS
CH = []
for r in range(3):
    for side in (-1, 1):
        for j in range(3 if r < 2 else 2):
            CH.append((r, CXV + side * (300 + j * 62 + r * 31), WIN_BOT - 250 + r * 44, (j + r) % 2, j, side))
CH.sort(key=lambda c: c[0])
L.CHOIR = CH

# shots -> which panel is up: REVIEW / WIDE -> review (+1), CHECKS -> checks (-1)
_SW = [(ta, -1.0 if fr is L.CHECKS else 1.0) for ta, fr in L._ARR]
def side(t):
    v = 1.0; prev = 1.0
    for ta, s in _SW:
        if t < ta - L.WHIP: break
        u = eio(seg(t, ta - L.WHIP, ta)); v = prev + (s - prev) * u
        if t < ta: return v
        prev = s
    return prev
L.focus = lambda t: side(t)


def _panel(frame, t, k, which, a, slide):
    if a <= 0.004: return
    m = 60; x0, y0, w, h = L.PX_R, L.PY, L.PW, L.PH
    sub = Image.new("RGBA", (int(round((w + 2 * m) * k)), int(round((h + 2 * m) * k))), (0, 0, 0, 0))
    hk = L.hot(t)
    if which == "review":
        st, i = L.review_state(t)
        L.review_draw(sub, t, k, st, i, -(x0 - m), -(y0 - m))
        blocked = st[0] == "merge" and not st[1] and not st[2]
        if blocked: a *= 0.55
    else:
        L.checks_draw(sub, t, k, hk, -(x0 - m), -(y0 - m))
    L.paste(frame, sub, (x0 - m + slide) * k, (y0 - m) * k, a)


def panels(frame, t, k):
    s = side(t)                                   # +1 review, -1 checks
    ar = clamp((s + 1) / 2); ac = 1 - ar
    _panel(frame, t, k, "checks", ac, -260 * ar)
    _panel(frame, t, k, "review", ar, 260 * ac)
    return ar


def header(frame, t, k):
    i = L.pr_at(t); p = L.PR_T[i]; merged = t >= p["merge"] - 0.02
    hk = L.hot(t); dx, dy = L.jit("hdr", t, 14 * hk)
    num, title = f"#{1111 + i}", f"ship: {L.VIDS[i][1]}"
    sp = L.pill("Merged" if merged else "Open", (168, 132, 255) if merged else L.GREEN, k)
    w1 = L.tw(num, L.MONO, 34) + 18 + sp.width / k
    x = CXV - w1 / 2
    x += L.txt(frame, num, L.MONO, 34, L.DIM, x + dx, 116 + 4 + dy, k) + 18
    L.paste(frame, sp, (x + dx) * k, (116 + 2 + dy) * k)
    fs = 50
    while L.tw(title, L.INTERB, fs) > 860 and fs > 36: fs -= 2
    L.txt(frame, title, L.INTERB, fs, L.IVORY, CXV + dx, 172 + dy, k, anchor="c")
    n = L.approvals(t); pop = 0.0
    for tt, _ in L.APPROVALS:
        if tt <= t < tt + 0.3: pop = math.exp(-(t - tt) / 0.08)
    col = L.mix(L.IVORY, L.GREEN, pop); y2 = 252
    parts = [("approvals", L.MONO, 34, L.DIM, 12, 6), (f"{n:,}", L.MONOB, 44, col, 48, -3 * pop), ("lines read", L.MONO, 34, L.DIM, 12, 6), ("0", L.MONOB, 44, L.IVORY, 0, 0)]
    wtot = sum(L.tw(s_, f_, z_) + g_ for s_, f_, z_, c_, g_, o_ in parts) + L.tw("8,888", L.MONOB, 44) - L.tw(f"{n:,}", L.MONOB, 44)
    x = CXV - wtot / 2; ex, ey = L.jit("cnt", t, 14 * hk)
    for s_, f_, z_, c_, g_, o_ in parts:
        w_ = L.txt(frame, s_, f_, z_, c_, x + ex, y2 + o_ + ey, k)
        x += (max(w_, L.tw("8,888", L.MONOB, 44)) if f_ == L.MONOB and s_ != "0" else w_) + g_


def stamp(frame, t, k):
    for j, m in enumerate(L.MERGES):
        tau = t - m
        if tau < 0: continue
        nxt = L.PR_T[j + 1]["start"] if j + 1 < len(L.PR_T) else 1e9
        out = seg(t, nxt - 0.02, nxt + 0.1)
        if out >= 1: continue
        sp = L.stamp_sprite(k * 0.92, L.STAMP_ANG[j]); sc = 1 + 1.2 * math.exp(-tau * 26)
        if abs(sc - 1) > 0.01: sp = sp.resize((int(sp.width * sc), int(sp.height * sc)), Image.BILINEAR)
        L.paste(frame, sp, CXV * k - sp.width / 2, (WY_PX + 0.62 * L.WHT * WS) * k - sp.height / 2, clamp(tau * 18) * (1 - out))


_C = {}
def rays_v(k):
    key = ("rays", k)
    if key not in _C:
        W_, H_ = int(round(DW_ * k)), int(round(DH_ * k))
        img = Image.new("RGB", (W_, H_), (0, 0, 0)); d = ImageDraw.Draw(img)
        ox, oy = CXV * k, (WY_PX + 212 * WS) * k; import random; rng = random.Random(7)
        for j in range(9):
            a = math.radians(50 + j * 10 + rng.uniform(-3, 3)); wd = math.radians(rng.uniform(2.2, 4.5)); Lr = 3000 * k
            c = rng.choice([(34, 46, 38), (44, 42, 36), (40, 30, 30)])
            d.polygon([(ox, oy), (ox + Lr * math.cos(a - wd), oy + Lr * math.sin(a - wd)), (ox + Lr * math.cos(a + wd), oy + Lr * math.sin(a + wd))], fill=c)
        _C[key] = np.asarray(img.filter(ImageFilter.GaussianBlur(22 * k))).copy()
    return _C[key]


def scrim_v(k):
    key = ("scrim", k)
    if key not in _C:
        CHp, CWp = int(round(DH_ * k)), int(round(DW_ * k)); ys = np.arange(CHp, dtype=np.float32) / k
        sc_ = np.clip((ys - 1150) / 300, 0, 1) ** 1.3 * 0.70 + np.clip((330 - ys) / 90, 0, 1) * 0.6
        _C[key] = np.ascontiguousarray(np.broadcast_to(((1 - sc_) * 255)[:, None, None], (CHp, CWp, 3))).astype(np.uint8)
    return _C[key]


def diff_v(t, k, dim, hotk):
    """The diff behind everything, full height (s2's diff_layer is sized for 1080)."""
    lh = int(round(L.LH * k)); dw = int(round(L.DW * k)); vh = int(round((DH_ - 120) * k))
    s = L.scroll_lines(t) * lh; v = abs(L.scroll_lines(t + 1 / 30) * lh - s); blur = int(v * 0.5)
    out = np.empty((vh, dw, 3), np.uint8); out[:] = L.BG
    i0 = int(math.floor(s / lh)); i1 = int(math.floor((s + vh) / lh)) + 1
    for i in range(max(0, i0), min(len(L.DOC), i1)):
        y = int(round(i * lh - s)); st = L.strip(i, k); a = max(0, -y); b = min(lh, vh - y)
        if b <= a: continue
        if hotk > 0.02:
            dx, _ = L.jit(("row", i), t, 70 * k * hotk); out[y + a:y + b] = np.roll(st[a:b], int(dx), axis=1)
        else: out[y + a:y + b] = st[a:b]
    if blur > 2: out = cv2.blur(out, (1, blur))
    return cv2.convertScaleAbs(out, alpha=dim, beta=10.0 * (1 - dim))


def cursor(frame, t, k, op):
    if op <= 0.02: return
    x, y = L.cursor_pos(t); hk = L.hot(t); dx, dy = L.jit("cur", t, 20 * hk)
    d = ImageDraw.Draw(frame)
    for tt, (cx, cy), c in L.CUR:
        tau = t - tt
        if 0 <= tau < 0.36:
            r = (10 + 70 * eout(tau / 0.36)) * k; a = (1 - tau / 0.36) * op
            d.ellipse([cx * k - r, cy * k - r, cx * k + r, cy * k + r], outline=L.mix(L.BG, L.IVORY, a * 0.9), width=max(1, int(3 * k)))
    L.paste(frame, L.cursor(k * 1.2), (x + dx) * k, (y + dy) * k, op)


def render_frame(t, W, H):
    if W >= H:
        import s2_lgtm; return s2_lgtm.render_frame(t, W, H)
    t = float(t); k = W / DW_; kw = k * WS
    CWp, CHp = int(round(DW_ * k)), int(round(DH_ * k)); hk = L.hot(t)
    frame = Image.new("RGB", (CWp, CHp), L.BG)
    frame.paste(Image.fromarray(diff_v(t, k, 0.22, hk)), (int(round(-150 * k)), int(round(120 * k))))
    canvas = np.asarray(frame).copy()
    i = int(np.searchsorted(L.BEATS, t, side="right")) - 1
    bp = math.exp(-7.0 * (t - L.BEATS[i])) if i >= 0 else 0.0
    burst = 0.0
    for m in L.MERGES:
        if m <= t < m + 1.2: burst = max(burst, math.exp(-(t - m) / 0.35))
    canvas = cv2.addWeighted(canvas, 1.0, rays_v(k), 0.08 + 0.08 * bp + 0.32 * burst, 0)
    L.window_layer(canvas, t, kw, 0.55 + 0.25 * bp + 0.5 * burst, hk)
    canvas = cv2.multiply(canvas, scrim_v(k), scale=1 / 255.0)
    frame = Image.fromarray(canvas)
    L.choir_layer(frame, t, k, hk)
    ar = panels(frame, t, k)
    header(frame, t, k)
    stamp(frame, t, k)
    cursor(frame, t, k, clamp((ar - 0.5) * 2))
    img = np.asarray(frame)
    # punch on clicks/merges and the merge/broke shake, about the window (no crop: the layout is already the frame)
    z = 1 + L.punch(t) * 0.8; sx, sy = L.shake(t)
    cx, cy = CXV * k, 800 * k
    M = np.array([[z, 0, cx - z * cx + sx * k], [0, z, cy - z * cy + sy * k]], np.float32)
    out = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    # whip blur while the panel slot switches
    v = abs(side(t + 1 / 60) - side(t - 1 / 60)) * 30
    if v > 0.2:
        Lb = int(min(60, v * 18) * k)
        if Lb > 2:
            y0, y1 = int((L.PY - 70) * k), int((L.PY + L.PH + 70) * k)
            out = out.copy(); out[y0:y1] = cv2.blur(out[y0:y1], (Lb, 1))
    fl = 0.0
    for m in L.MERGES:
        if 0 <= t - m < 0.3: fl = max(fl, 0.10 * math.exp(-(t - m) * 16))
    if fl > 0.004 or hk > 0.02:
        o = out.astype(np.float32) * (1 / 255.0)
        if fl > 0.004: o = o * (1 - fl) + np.array(L.IVORY, np.float32) / 255 * fl
        if hk > 0.02: o = o * (1 - 0.10 * hk) + o * np.array([1.25, 0.8, 0.8], np.float32) * 0.10 * hk
        return (np.clip(o, 0, 1) * 255 + 0.5).astype(np.uint8)
    return np.ascontiguousarray(out)
