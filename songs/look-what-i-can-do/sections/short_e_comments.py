"""Short E, part 2 at 9:16: verse 2 (her titles) in the comment section (frames 1963-2399, song 65.43-80.00).

The 16:9 page is two columns (her post left, the thread right) photographed by a drifting camera. For a phone the page
is re-laid out as one tall column, like the app on a phone: her real post on top (x 60-880), the thread under it with
a long view (cards at full size: 62 px lyric lines, 34 px meta), the input bar at the foot. The camera keeps Mirror's
floating-page look (perspective, glow, glossy floor) but tilts instead of panning: on the post for "Senior Slopcore
Architect" (highlighter + RECEIPT), down to the thread as the titles are typed, back up when the post flips into her
profile for "thought leader / TED Talk fee". The page is framed a little left of centre (safe column, x <= 0.88 W).
Runs on a PRIVATE copy of s3_comments (shorts_dg.private): the film's module is untouched.
render_frame(t, W, H) for 9:16 (16:9 falls through to s3_comments)."""
import os, sys, math
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shorts_dg as SD

M = SD.private("shortE_comments_impl", "s3_comments.py")
clamp, lerp, ease_io = M.clamp, M.lerp, M.ease_io

# ---- the tall page (page px)
M.PW, M.PH = 940, 2040
M.POST_X, M.POST_Y, M.POST_W = 60, 60, 820
M.PROF_Y = 60
M.TX, M.TW = 55, 830
M.HEAD_Y, M.VIEW, M.INP_Y = 660, (748, 1900), 1930
PAGE_TONE = 0.88                           # the page's whites top out at 0.88 (mean luma < 0.62, < 12% above 0.92)
XOFF = 0.06                                # frame the page left of centre by 6% of W

#        (t, s, cx, cy, yaw, pitch)  s = output px per page px
_T0, _T1 = M.T0, M.T1
SHOTS = [(_T0 - 0.5, 0.98, 470, 560, -3.0, 2.0), (_T0 + 0.06, 0.98, 470, 560, -3.0, 2.0), (M.T_SLOP - 0.22, 1.02, 505, 400, -1.0, 0.6),
         (M.T_RECEIPT + 0.5, 1.03, 505, 400, -0.8, 0.5),
         (float(M.L2["s"]) - 0.02, 1.00, 470, 1440, 2.0, 0.0), (float(M.L4["s"]), 1.01, 470, 1450, 0.5, 0.0),
         (float(M.L6["s"]), 1.00, 470, 1450, -1.0, 0.0), (M.T_FLIP - 0.12, 1.00, 470, 1440, -0.8, 0.0),
         (M.T_FLIP + 0.36, 1.05, 470, 480, -2.0, 0.3), (M.T_400, 1.07, 470, 470, -1.2, 0.3), (_T1 + 0.5, 1.08, 470, 466, -0.8, 0.3)]
MOVES = {4: 0.38, 8: 0.48}


def camera(t):
    i = max(0, int(np.searchsorted([s[0] for s in SHOTS], t, side="right")) - 1)
    a = SHOTS[i]; b = SHOTS[min(i + 1, len(SHOTS) - 1)]
    if b is a: k = 0.0
    elif (i + 1) in MOVES: d = MOVES[i + 1]; k = ease_io(clamp((t - (b[0] - d)) / d))
    else: k = ease_io(clamp((t - a[0]) / max(1e-3, b[0] - a[0])))
    s, cx, cy, yaw, pitch = (lerp(a[j], b[j], k) for j in range(1, 6))
    cx += 4 * math.sin(t * 0.31) + 2 * math.sin(t * 0.73 + 1); cy += 3 * math.sin(t * 0.27 + 2)
    yaw += 0.4 * math.sin(t * 0.21); pitch += 0.2 * math.sin(t * 0.17 + 1)
    for tk, amp in ((M.T_RECEIPT, 0.025), (M.T_TALK, 0.02)):
        if tk <= t < tk + 0.8: s *= 1 + amp * clamp((t - tk) / 0.03) * math.exp(-(t - tk) / 0.16)
    return s, cx, cy, yaw, pitch


def homography(W, H, ps, s, cx, cy, yaw, pitch):
    f = s * M.D_CAM; ox = W / 2 - XOFF * W
    cyw, syw = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    cp, sp = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
    src = np.array([(0, 0), (M.PW, 0), (M.PW, M.PH), (0, M.PH)], np.float32); dst = []
    for u, v in src:
        X, Y, Z = u - cx, v - cy, 0.0
        X, Z = X * cyw + Z * syw, -X * syw + Z * cyw
        Y, Z = Y * cp - Z * sp, Y * sp + Z * cp
        d = M.D_CAM + Z; dst.append((ox + f * X / d, H / 2 + f * Y / d))
    return cv2.getPerspectiveTransform(src * ps, np.array(dst, np.float32))


def render_frame(t, W, H):
    if W >= H:
        import s3_comments; return s3_comments.render_frame(t, W, H)
    t = float(t)
    s, cx, cy, yaw, pitch = camera(t)
    ps = round(min(1.5, max(0.7, s * 1.02)) * 20) / 20.0
    pg = M.render_page(t, ps).copy()
    pg[..., :3] = (pg[..., :3].astype(np.float32) * PAGE_TONE).astype(np.uint8)   # her white post/profile -> 0.88 (brightness rule)
    Hm = homography(W, H, ps, s, cx, cy, yaw, pitch)
    w2, h2 = W // 2, H // 2
    S2 = np.array([[0.5, 0, 0], [0, 0.5, 0], [0, 0, 1]], np.float64)
    bg = M.room(w2, h2).copy()
    pc = Hm @ np.array([M.PW * ps / 2, M.PH * ps / 2, 1.0]); pc = pc[:2] / pc[2] * 0.5
    rx, ry = M.PW * s * 0.75 * 0.5, M.PH * s * 0.75 * 0.5
    yy, xx = np.ogrid[0:h2, 0:w2]
    g = np.exp(-(((xx - pc[0]) / rx) ** 2)).astype(np.float32) * np.exp(-(((yy - pc[1]) / ry) ** 2)).astype(np.float32)
    bg += g[..., None] * np.array([0.10, 0.13, 0.20], np.float32)
    bl = Hm @ np.array([M.PW * ps / 2, M.PH * ps, 1.0]); bl = bl[:2] / bl[2]
    if bl[1] < H - 4:
        Hp, Wp = pg.shape[:2]
        small = cv2.resize(pg, (Wp // 3, Hp // 3), interpolation=cv2.INTER_AREA)
        small = cv2.GaussianBlur(small, (0, 0), 1.6)[::-1].astype(np.float32) / 255
        fade = (0.42 * np.exp(-np.arange(small.shape[0], dtype=np.float32) / (small.shape[0] * 0.30)))[:, None]
        small[..., :3] *= small[..., 3:4] * fade[..., None]; small[..., 3] *= fade
        Tm = np.array([[3, 0, 0], [0, 3, Hp + 70 * ps], [0, 0, 1]], np.float64)
        rw = cv2.warpPerspective(small, S2 @ Hm @ Tm, (w2, h2), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
        bg = bg * (1 - rw[..., 3:4]) + rw[..., :3]
    bg = cv2.resize(bg, (W, H), interpolation=cv2.INTER_LINEAR)
    pw = cv2.warpPerspective(pg, Hm, (W, H), flags=cv2.INTER_LINEAR if s / ps > 0.75 else cv2.INTER_AREA,
                             borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    a = pw[..., 3].astype(np.float32) * (1 / 255.0)
    out = pw[..., :3].astype(np.float32) * (1 / 255.0)
    out -= bg; out *= a[..., None]; out += bg
    out *= M.vignette(W, H)
    out += (M.grain(W, H, int(round(t * 30))) * 0.008)[..., None]
    np.clip(out, 0, 1, out=out); out *= 255; out += 0.5
    return out.astype(np.uint8)
