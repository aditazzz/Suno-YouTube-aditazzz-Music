"""The standup seen from straight above: the office floor plan (an architect's plan with the roof taken off) and
the eight people in a circle. World units are metres, x east, y south, the middle of the circle at (0, 0).
Everything draws into a uint8 RGB canvas with cv2's anti-aliased fills (fast), positions through a View."""
import math
import numpy as np, cv2

SH = 4; SC = 16                                     # cv2 sub-pixel shift: coordinates x16
def rgb8(h): return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
def mix8(a, b, k): return tuple(int(round(x + (y - x) * k)) for x, y in zip(a, b))

FLOOR = rgb8('f3f0ea'); CARPET = rgb8('e9e4da'); WALL = rgb8('2f2d2a'); GLASS = rgb8('9fbfd6'); FURN = rgb8('fdfcf9')
FURN_E = rgb8('aaa397'); MON = rgb8('2c2b29'); CHAIR = rgb8('6b6e75'); LEAF = rgb8('8cbf78'); LEAF2 = rgb8('6aa35b')
POT = rgb8('c9b8a2'); CORE = rgb8('dfd9cf'); HATCH = rgb8('b6aea1'); WOOD = rgb8('e6d6bd'); SOFA = rgb8('8d9db1')
RUG = rgb8('e2ddd2'); BOARD = rgb8('ffffff'); SKIN = rgb8('d9a77f'); CUP = rgb8('ffffff'); COFFEE = rgb8('6b4a32')

BLD = (-32.0, -22.0, 38.0, 24.0)                    # the office building's footprint
R_CIRCLE = 1.55
PEOPLE = [  # name, angle on the circle (deg; -90 = north/top), shirt, hair
    ("Ted", -90, 'd93a2b', '3a2a20'), ("Dana", -45, '7c9a86', '5b3b27'), ("Priya", 0, 'c9a24c', '1d1916'),
    ("Marcus", 45, '5b6d8a', '191613'), ("Me", 90, '2448a8', '6a492e'), ("Sam", 135, '9b9081', 'a3836a'),
    ("Lee", 180, '4d5955', '2a2421'), ("Jo", 225, 'b47c6c', 'caa36c')]

def person_pos(i, t=0.0):
    name, a, _, _ = PEOPLE[i]; r = R_CIRCLE * (1.13 if name == "Ted" else 1.0)
    a = math.radians(a) + 0.04 * math.sin(t * 0.7 + i * 1.9) * (name != "Ted")
    return np.array([r * math.cos(a), r * math.sin(a)])

# ---------------------------------------------------------------- the floor plan (generated once)
def _plan():
    rng = np.random.default_rng(4)
    P = dict(desks=[], chairs=[], mons=[], tables=[], walls=[], glass=[], plants=[], rugs=[], sofas=[], counters=[],
             hatch=[], cols=[], doors=[])
    x0, y0, x1, y1 = BLD
    # structural columns on a 9 m grid
    for cx in np.arange(x0 + 7, x1 - 3, 9.0):
        for cy in np.arange(y0 + 7, y1 - 3, 9.0):
            if abs(cx) < 4.5 and abs(cy) < 4.5: continue
            if 13 < cx < 27 and -7 < cy < 7: continue
            P["cols"].append((cx - 0.22, cy - 0.22, cx + 0.22, cy + 0.22))
    # core: lifts, stairs, restrooms
    cx0, cy0, cx1, cy1 = 14.0, -6.5, 26.0, 6.5
    P["core"] = (cx0, cy0, cx1, cy1)
    for k in range(3): P["walls"].append([(cx0 + 4 * k, cy0), (cx0 + 4 * k, cy0 + 4)])
    P["lifts"] = [(cx0 + 0.4 + 4 * k, cy0 + 0.4, cx0 + 3.6 + 4 * k, cy0 + 3.6) for k in range(3)]
    P["stairs"] = (cx0 + 0.4, cy1 - 5.6, cx0 + 5.6, cy1 - 0.4)
    P["walls"] += [[(cx0, cy0 + 4), (cx1, cy0 + 4)], [(cx0 + 6, cy1 - 6), (cx0 + 6, cy1)], [(cx0, cy1 - 6), (cx1, cy1 - 6)]]
    # meeting rooms along the north wall (glass fronts)
    for k, (ax, bx) in enumerate(((-31.6, -21.0), (-21.0, -10.4), (-10.4, 0.2), (0.2, 10.8))):
        ay, by = -21.6, -14.6
        P["glass"].append([(ax, by), (bx, by)])
        if k: P["walls"].append([(ax, ay), (ax, by)])
        P["doors"].append(((ax + bx) / 2 + 2.0, by, 0.9))
        tx0, tx1 = ax + 2.2, bx - 2.2; ty0, ty1 = ay + 2.0, by - 2.0
        P["tables"].append(("rect", tx0, ty0, tx1, ty1))
        for xx in np.linspace(tx0 + 0.7, tx1 - 0.7, 4):
            P["chairs"] += [(xx, ty0 - 0.55), (xx, ty1 + 0.55)]
    P["walls"].append([(10.8, -21.6), (10.8, -14.6)])
    # kitchen in the north-east corner
    P["counters"] += [(28.0, -21.6, 37.6, -20.6), (36.6, -21.6, 37.6, -12.0), (29.0, -16.0, 33.0, -15.0)]
    for (tx, ty) in ((30.0, -11.0), (33.6, -8.4), (29.2, -6.6)):
        P["tables"].append(("round", tx, ty, 0.6, 0))
        for a in range(4): P["chairs"].append((tx + 1.0 * math.cos(a * 1.571 + 0.4), ty + 1.0 * math.sin(a * 1.571 + 0.4)))
    # lounge in the west
    P["rugs"].append(("rect", -30.6, -12.6, -21.0, -3.0))
    P["sofas"] += [(-30.0, -12.0, -28.8, -6.0), (-28.0, -12.0, -22.0, -10.8), (-28.0, -4.8, -23.2, -3.6)]
    P["tables"].append(("rect", -26.6, -9.0, -24.0, -6.6))
    # open-plan desks: pods of 2 x 3
    def pod(px, py, rot=False):
        for r in range(2):
            for c in range(3):
                if not rot:
                    dx0, dy0 = px + c * 1.6, py + r * 0.8
                    P["desks"].append((dx0, dy0, dx0 + 1.56, dy0 + 0.76))
                    my = dy0 + 0.14 if r == 0 else dy0 + 0.62
                    P["mons"].append((dx0 + 0.45, my - 0.04, dx0 + 1.11, my + 0.04))
                    P["chairs"].append((dx0 + 0.78, dy0 - 0.5 if r == 0 else dy0 + 1.26))
                else:
                    dx0, dy0 = px + r * 0.8, py + c * 1.6
                    P["desks"].append((dx0, dy0, dx0 + 0.76, dy0 + 1.56))
                    mx = dx0 + 0.14 if r == 0 else dx0 + 0.62
                    P["mons"].append((mx - 0.04, dy0 + 0.45, mx + 0.04, dy0 + 1.11))
                    P["chairs"].append((dx0 - 0.5 if r == 0 else dx0 + 1.26, dy0 + 0.78))
    for px in (-29.5, -22.5, -15.5, -8.5):
        for py in (7.5, 13.0, 18.5):
            pod(px, py)
    for py in (8.0, 14.0):
        pod(3.5, py)
    for py in (-4.0, 4.5, 13.0):
        pod(29.5, py, rot=True); pod(33.4, py, rot=True)
    # the standup corner: a round rug, a whiteboard behind Ted, plants
    P["rugs"].append(("round", 0.0, 0.0, 3.3, 0))
    P["board"] = (-1.15, -3.18, 1.15, -3.02)
    for (px, py, r) in ((-4.6, -3.6, 0.55), (4.4, -3.9, 0.6), (-5.4, 3.2, 0.5), (8.6, -11.0, 0.7), (-17.0, 3.0, 0.65),
                        (11.8, 2.6, 0.55), (-31.0, 23.0, 0.6), (37.0, 23.2, 0.6), (-31.0, -13.6, 0.55), (12.4, -13.6, 0.6),
                        (26.6, 9.2, 0.5), (-0.6, 23.0, 0.55)):
        P["plants"].append((px, py, r))
    # exterior windows: wall gaps every 3 m on the long facades
    P["windows"] = []
    for x in np.arange(x0 + 2.0, x1 - 1.0, 3.0): P["windows"] += [((x, y0), (x + 2.0, y0)), ((x, y1), (x + 2.0, y1))]
    for y in np.arange(y0 + 2.0, y1 - 1.0, 3.0): P["windows"] += [((x0, y), (x0, y + 2.0)), ((x1, y), (x1, y + 2.0))]
    return P

PLAN = _plan()

# ---------------------------------------------------------------- drawing helpers (uint8 canvas, AA)
def poly(cv, view, pts, col):
    q = view.to_px16(np.asarray(pts, np.float64))
    cv2.fillPoly(cv, [q], col, cv2.LINE_AA, shift=SH)

def rects(cv, view, R, col, outline=None, ow=1):
    if not len(R): return
    R = np.asarray(R, np.float64)
    C = np.stack([R[:, [0, 1]], R[:, [2, 1]], R[:, [2, 3]], R[:, [0, 3]]], 1)
    Q = view.to_px16(C)
    cv2.fillPoly(cv, list(Q), col, cv2.LINE_AA, shift=SH)
    if outline is not None: cv2.polylines(cv, list(Q), True, outline, ow, cv2.LINE_AA, shift=SH)

def circles(cv, view, X, r, col, outline=None, ow=1):
    if not len(X): return
    X = np.asarray(X, np.float64)
    n = int(np.clip(np.max(r) / view.mpp * 0.6, 10, 120))
    a = np.linspace(0, 2 * np.pi, n, endpoint=False)
    rr = np.broadcast_to(np.asarray(r, np.float64), (len(X),))
    C = X[:, None, :] + np.stack([np.cos(a), np.sin(a)], 1)[None] * rr[:, None, None]
    Q = view.to_px16(C)
    cv2.fillPoly(cv, list(Q), col, cv2.LINE_AA, shift=SH)
    if outline is not None: cv2.polylines(cv, list(Q), True, outline, ow, cv2.LINE_AA, shift=SH)

def lines(cv, view, segs, col, width_m=None, width_px=1.0):
    for s in segs:
        q = view.to_px16(np.asarray(s, np.float64))
        w = max(1, int(round(width_m / view.mpp if width_m else width_px)))
        cv2.polylines(cv, [q], False, col, w, cv2.LINE_AA, shift=SH)

def ellipse(cv, view, c, ax_m, ay_m, ang, col):
    """filled ellipse: world centre c, semi-axes (m), ang = world angle of the first axis (rad)."""
    s = view.to_px(np.asarray(c, np.float64)[None])[0]
    a = math.degrees(ang + view.rot)
    cv2.ellipse(cv, (int(round(s[0] * SC)), int(round(s[1] * SC))),
                (max(1, int(round(ax_m / view.mpp * SC))), max(1, int(round(ay_m / view.mpp * SC)))), a, 0, 360, col, -1, cv2.LINE_AA, SH)

# ---------------------------------------------------------------- the office
def apply_shadow(cv, view, mask, strength, box_world=None):
    """darken the canvas where mask (uint8) is set; only inside the screen box of box_world if given."""
    H, W = cv.shape[:2]
    if box_world is not None:
        x0, y0, x1, y1 = box_world
        P = view.to_px(np.array([[x0, y0], [x1, y0], [x1, y1], [x0, y1]]))
        a0, b0 = max(0, int(P[:, 0].min()) - 2), max(0, int(P[:, 1].min()) - 2)
        a1, b1 = min(W, int(P[:, 0].max()) + 3), min(H, int(P[:, 1].max()) + 3)
        if a1 <= a0 or b1 <= b0: return
    else: a0, b0, a1, b1 = 0, 0, W, H
    m = mask[b0:b1, a0:a1].astype(np.float32) * (strength / 255.0)
    reg = cv[b0:b1, a0:a1].astype(np.float32); reg *= (1 - m)[..., None]
    cv[b0:b1, a0:a1] = reg.astype(np.uint8)

def draw_office(cv, view, t, k_plan=1.0, sit=0.0, phones=0.0, ted_talk=1.0, ghost=0.0, dana_gone=0.0):
    """k_plan 0..1: the plan fades to a plain roof colour as we pull away."""
    P = PLAN; x0, y0, x1, y1 = BLD; mp = view.mpp
    roof = rgb8('d9d4cc')
    def C(c): return mix8(roof, c, k_plan)
    rects(cv, view, [BLD], C(FLOOR))
    if k_plan <= 0.02: return
    for r in P["rugs"]:
        if r[0] == "rect": rects(cv, view, [r[1:5]], C(RUG))
        else: circles(cv, view, [(r[1], r[2])], r[3], C(RUG))
    rects(cv, view, [P["core"]], C(CORE))
    rects(cv, view, P["lifts"], C(rgb8('cfc8bc')), C(FURN_E))
    sx0, sy0, sx1, sy1 = P["stairs"]
    if mp < 0.08: lines(cv, view, [[(sx0, y), (sx1, y)] for y in np.arange(sy0 + 0.3, sy1, 0.3)], C(HATCH), width_px=1)
    if mp < 0.05:
        for (a0, b0, a1, b1) in P["lifts"]: lines(cv, view, [[(a0, b0), (a1, b1)], [(a0, b1), (a1, b0)]], C(FURN_E), width_px=1)
    # soft contact shadows of desks, tables and people
    if mp < 0.15:
        osh = np.zeros(cv.shape[:2], np.uint8); off = np.array([0.06, 0.09])
        R = np.asarray(P["desks"], np.float64); rects(osh, view, R + np.r_[off, off], 255)
        people_shadows(osh, view, t, sit, ghost, dana_gone)
        if mp < 0.03: osh = cv2.GaussianBlur(osh, (0, 0), max(0.6, 0.02 / mp))
        apply_shadow(cv, view, osh, 0.20 * k_plan, BLD)
    rects(cv, view, P["counters"], C(rgb8('e7e1d7')), C(FURN_E))
    for tb in P["tables"]:
        if tb[0] == "rect": rects(cv, view, [tb[1:5]], C(WOOD), C(FURN_E))
        else: circles(cv, view, [(tb[1], tb[2])], tb[3], C(WOOD), C(FURN_E))
    rects(cv, view, P["sofas"], C(SOFA))
    rects(cv, view, P["desks"], C(FURN), C(FURN_E) if mp < 0.06 else None)
    rects(cv, view, P["mons"], C(MON))
    circles(cv, view, P["chairs"], 0.27, C(CHAIR))
    rects(cv, view, P["cols"], C(rgb8('a39d93')))
    for (px, py, r) in P["plants"]:
        circles(cv, view, [(px, py)], r, C(LEAF))
        if mp < 0.06:
            a = np.linspace(0, 2 * np.pi, 7, endpoint=False)
            circles(cv, view, [(px + r * 0.45 * math.cos(q), py + r * 0.45 * math.sin(q)) for q in a], r * 0.38, C(LEAF2))
    rects(cv, view, [P["board"]], C(BOARD), C(WALL))
    lines(cv, view, P["glass"], C(GLASS), width_m=0.12)
    lines(cv, view, P["walls"], C(WALL), width_m=0.18)
    draw_people(cv, view, t, C, sit, phones, ted_talk, ghost, dana_gone)
    if ghost > 0 and mp < 0.06: ghost_dana(cv, view, t, ghost * k_plan)
    W_ = 0.38
    lines(cv, view, [[(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]], C(WALL), width_m=W_)
    if mp < 0.12:
        lines(cv, view, P["windows"], C(rgb8('cfe0ec')), width_m=W_ * 0.55)

def _pose(i, t, ted_talk, dana_gone):
    name = PEOPLE[i][0]; p = person_pos(i, t)
    if name == "Dana" and dana_gone > 0: p = p + np.array([-1.2, -2.6]) * dana_gone ** 1.6
    f = -p / max(np.linalg.norm(p), 1e-6)
    if name == "Ted" and ted_talk > 0: f = np.array([0.0, 1.0]) * 0.8 + f * 0.2; f /= np.linalg.norm(f)
    n = np.array([-f[1], f[0]])
    return name, p, f, n

def people_shadows(osh, view, t, sit, ghost, dana_gone):
    for i in range(len(PEOPLE)):
        name, p, f, n = _pose(i, t, 1.0, dana_gone)
        if name == "Dana" and (ghost > 0 or dana_gone >= 1): continue
        ellipse(osh, view, p + np.array([0.07, 0.10]), 0.30, 0.20, math.atan2(n[1], n[0]), 255)

def draw_people(cv, view, t, C, sit, phones, ted_talk, ghost, dana_gone):
    beat = math.sin(t * 2 * math.pi * 143.55 / 60 / 2)
    order = [i for i in range(len(PEOPLE)) if PEOPLE[i][0] != "Ted"] + [0]
    fine = view.mpp < 0.012
    for i in order:
        name, p, f, n = _pose(i, t, ted_talk, dana_gone)
        _, _, shirt, hair = PEOPLE[i]
        ang = math.atan2(n[1], n[0])
        if name == "Dana" and (ghost > 0 or dana_gone >= 1): continue
        if sit > 0 and name != "Ted":
            circles(cv, view, [p - f * 0.06], 0.28 * min(1, sit * 1.4), C(CHAIR))
        sc = 1 - 0.05 * sit * (name != "Ted")
        sh = rgb8(shirt); dark = mix8(sh, (0, 0, 0), 0.28); lite = mix8(sh, (255, 255, 255), 0.18)
        g = (0.09 * beat * ted_talk) if name == "Ted" else 0.0
        # arms along the sides, hands in front
        for side in (-1, 1):
            ap = p + n * side * 0.215 * sc + f * (0.05 + g * side)
            ellipse(cv, view, ap, 0.05 * sc, 0.12 * sc, math.atan2(f[1], f[0]), C(dark))
            hp = p + n * side * (0.14 if name != "Ted" else 0.19 + 0.05 * abs(beat)) * sc + f * (0.20 + g * side) * sc
            circles(cv, view, [hp], 0.042 * sc, C(SKIN))
        # shoulders: outline, cloth, a soft highlight on the back
        ellipse(cv, view, p, 0.255 * sc, 0.145 * sc, ang, C(dark))
        ellipse(cv, view, p, 0.240 * sc, 0.130 * sc, ang, C(sh))
        if fine: ellipse(cv, view, p - f * 0.04, 0.17 * sc, 0.06 * sc, ang, C(lite))
        # head from above: a little face showing at the front, hair over the rest
        circles(cv, view, [p + f * 0.06], 0.075 * sc, C(SKIN))
        circles(cv, view, [p - f * 0.005], 0.098 * sc, C(rgb8(hair)))
        if fine: circles(cv, view, [p - f * 0.03 + n * 0.025], 0.03 * sc, C(mix8(rgb8(hair), (255, 255, 255), 0.22)))
        if name in ("Priya", "Lee", "Jo") and phones < 0.5:
            q = p + f * 0.25 + n * 0.12
            circles(cv, view, [q], 0.046, C(CUP)); circles(cv, view, [q], 0.033, C(COFFEE))
        if phones > 0 and name not in ("Ted", "Me"):
            q = p + f * (0.27 * min(1, phones * 1.5))
            R = np.array([[-0.035, -0.07], [0.035, -0.07], [0.035, 0.07], [-0.035, 0.07]])
            rot = np.array([[n[0], f[0]], [n[1], f[1]]])
            poly(cv, view, q + R @ rot.T, C(rgb8('1b1c22')))
            poly(cv, view, q + (R * 0.8) @ rot.T, C(mix8(rgb8('1b1c22'), rgb8('9cc4ff'), min(1, phones))))

def ghost_dana(cv, view, t, k):
    """Dana as a little sheet ghost, from above: a white cloth disc with two eye holes, slightly see-through."""
    if k <= 0: return
    i = [j for j in range(len(PEOPLE)) if PEOPLE[j][0] == "Dana"][0]
    p = person_pos(i, 0.0) + np.array([0.0, 0.02 * math.sin(t * 3)])
    f = -p / np.linalg.norm(p); n = np.array([-f[1], f[0]])
    over = cv.copy()
    a = np.linspace(0, 2 * np.pi, 40, endpoint=False)
    rr = 0.30 * (1 + 0.07 * np.sin(a * 7 + t * 5))
    poly(over, view, p[None] + np.stack([np.cos(a), np.sin(a)], 1) * rr[:, None], (250, 251, 255))
    for side in (-1, 1): circles(over, view, [p + f * 0.08 + n * side * 0.08], 0.045, (40, 44, 60))
    cv[:] = cv2.addWeighted(over, 0.72 * k, cv, 1 - 0.72 * k, 0)
