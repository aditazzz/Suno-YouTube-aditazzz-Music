from ud_engine import *

# ======================================================================= palettes
# (time, top, bottom, aurora_amt, exposure)
def pal_keys():
    k = [
        (0.0,     hexc('02040c'), hexc('060c22'), 0.0, 1.0),
        (T_DROP - 0.05, hexc('03081a'), hexc('0a1636'), 0.05, 1.0),
        (T_DROP + 0.3, hexc('1a0206'), hexc('3a0710'), 0.0, 1.1),
        (T_REMEMBER, hexc('140309'), hexc('2a0612'), 0.0, 1.0),
        (T_PRE - 2, hexc('040a1c'), hexc('0b1a3a'), 0.1, 1.0),
        (T_CH1 - 0.1, hexc('02040e'), hexc('071228'), 0.2, 1.0),
        (T_CH1 + 0.6, hexc('04122e'), hexc('0d2a5a'), 0.85, 1.15),
        (T_V2 - 2, hexc('050a20'), hexc('140b34'), 0.35, 1.0),
        (T_WARE, hexc('040a14'), hexc('0a1c26'), 0.15, 1.0),
        (T_SORRY, hexc('0a0618'), hexc('1a0d2c'), 0.2, 1.0),
        (T_PRE2, hexc('03050c'), hexc('0a1020'), 0.15, 0.95),
        (T_CH2 - 0.1, hexc('03050c'), hexc('0a1020'), 0.2, 1.0),
        (T_CH2 + 0.6, hexc('120a2a'), hexc('2c0f3e'), 1.0, 1.15),
        (T_BRIDGE, hexc('0a0816'), hexc('16102a'), 0.25, 1.0),
        (T_TT, hexc('060a1c'), hexc('101836'), 0.35, 1.0),
        (T_BUILD, hexc('050a1c'), hexc('0c1a3c'), 0.5, 1.05),
        (T_FINAL - 0.6, hexc('0a1430'), hexc('1a3060'), 0.9, 1.2),
        (T_FINAL + 0.5, hexc('0c0a2c'), hexc('28104a'), 1.2, 1.2),
        (T_OUTRO + 1, hexc('03050e'), hexc('0a1024'), 0.35, 1.0),
        (DUR + 2, hexc('010205'), hexc('03060e'), 0.0, 0.9),
    ]
    return k
PK = pal_keys()
def palette(t):
    for (a, *pa), (b, *pb) in zip(PK, PK[1:]):
        if a <= t < b:
            x = ease_io((t - a) / (b - a)) if b - a < 4 else sstep(a, a + min(3.0, b - a), t)
            return [lerp(np.asarray(u, np.float32), np.asarray(v, np.float32), x) for u, v in zip(pa, pb)]
    return [np.asarray(x, np.float32) for x in PK[-1][1:]]

# ======================================================================= aurora
_AW, _AH = 240, 135
_ax = np.linspace(0, 1, _AW)[None, :]; _ay = np.linspace(0, 1, _AH)[:, None]
def aurora(t, W, H, amt, hue_shift=0.0):
    if amt <= 0.01: return None
    yc = 0.42 + 0.06 * np.sin(_ax * 5.0 + t * 0.21) + 0.04 * np.sin(_ax * 11.0 - t * 0.33)
    streak = 0.55 + 0.45 * np.sin(_ax * 70 + 2.0 * np.sin(_ax * 9 + t * 0.4) + t * 0.6)
    streak *= 0.6 + 0.4 * np.sin(_ax * 23 - t * 0.27)
    below = np.exp(-np.maximum(0, _ay - yc) * 28)
    above = np.exp(-np.maximum(0, yc - _ay) * 3.2)
    I = (below * above) * streak
    I *= 0.6 + 0.4 * np.sin(_ax * 3.1 + t * 0.15)
    h = np.clip((yc - _ay) * 2.2 + 0.1 + hue_shift, 0, 1)[..., None]
    c0 = TEAL; c1 = hexc('3fa8ff'); c2 = VIO if hue_shift < 0.5 else MAG
    col = np.where(h < 0.5, c0 + (c1 - c0) * (h * 2), c1 + (c2 - c1) * ((h - 0.5) * 2))
    img = (I[..., None] * col * amt).astype(np.float32)
    return cv2.resize(cv2.GaussianBlur(img, (0, 0), 1.2), (W, H), interpolation=cv2.INTER_CUBIC)

# ======================================================================= dust / snow
ND = 3200
_dr = np.random.default_rng(21)
D0 = np.stack([_dr.uniform(-16, 16, ND), _dr.uniform(-10, 10, ND), _dr.uniform(-8, 14, ND)], 1).astype(np.float32)
DPH = _dr.uniform(0, 6.28, ND).astype(np.float32)
DSZ = _dr.uniform(0.4, 1.0, ND).astype(np.float32)
def _dspeed(t):
    if T_BUILD <= t < T_FINAL: return lerp(-0.6, -4.5, sstep(T_BUILD, T_FINAL - 1, t))   # rising
    if T_DROP <= t < T_DROP + 2: return 3.5 * (1 - sstep(T_DROP, T_DROP + 2, t)) + 0.5
    if T_PRE <= t < T_CH1: return 0.08
    return 0.55
_dcum = np.cumsum([_dspeed(t) for t in np.arange(0, DUR + 2, 1 / 60)]) / 60
def dust(t):
    off = float(np.interp(t, np.arange(0, DUR + 2, 1 / 60), _dcum))
    P = D0.copy()
    P[:, 1] = (P[:, 1] + 10 - off * DSZ) % 20 - 10
    P[:, 0] += 0.35 * np.sin(t * 0.4 + DPH)
    P[:, 2] += 0.25 * np.cos(t * 0.3 + DPH)
    return P

# ======================================================================= splat
def splat(buf, u, v, w, col):
    H, W = buf.shape[:2]
    ok = (u >= 0) & (u < W - 1) & (v >= 0) & (v < H - 1) & (w > 0)
    if not ok.any(): return
    u = u[ok]; v = v[ok]; w = w[ok]
    col = col[ok] if col.ndim == 2 else np.broadcast_to(col, (len(u), 3))
    x0 = u.astype(np.int32); y0 = v.astype(np.int32); fx = u - x0; fy = v - y0
    flat = buf.reshape(-1, 3)
    for dx, dy, ww in ((0, 0, (1 - fx) * (1 - fy)), (1, 0, fx * (1 - fy)), (0, 1, (1 - fx) * fy), (1, 1, fx * fy)):
        idx = (y0 + dy) * W + (x0 + dx); wt = w * ww
        for c in range(3):
            flat[:, c] += np.bincount(idx, weights=wt * col[:, c], minlength=W * H).astype(np.float32)

# ======================================================================= cell state
def m_snow(t):
    a = sstep(T_EVERY1 - 0.5, T_EVERY1 + 1.4, t) * (1 - sstep(T_GAVE_END1 + 0.2, T_GAVE_END1 + 2.4, t))
    b = sstep(T_CH2 + 0.05, T_CH2 + 1.3, t) * (1 - sstep(T_BRIDGE - 2.8, T_BRIDGE + 1.2, t))
    c = sstep(T_FINAL, T_FINAL + 0.85, t) * (1 - sstep(T_OUTRO + 0.5, T_OUTRO + 4.0, t))
    return max(a, b, c)

def spin(t):
    return 0.16 * t + 0.6 * sum(ease_out((t - s) / 0.6) for s in STAMPS if s <= t)

def cell_colors(t, P2r):
    sec = section(t)
    base = ICE[None] * (0.75 + 0.25 * (ri[:, None] % 2)) + 0 * P2r[:, None]
    base = np.where(IS_HDR[:, None], GOLD[None] * 0.9 + 0.3, base)
    red_amt = win(t, T_DROP, T_REMEMBER + 2, 0.05, 4.0)
    if red_amt > 0:
        base = base * (1 - red_amt) + (RED[None] * (0.7 + 0.3 * rng_flick(t))) * red_amt
    if T_BUILD < t < T_FINAL:
        kb = sstep(T_BUILD, T_FINAL, t)
        hue = (np.sin(ri[:, None] * 0.4 + t * 3) * 0.5 + 0.5)
        bc = VIO * hue + ICE2 * (1 - hue)
        base = base * (1 - kb) + (bc * 1.2 + WHITE * 0.3 * beat_pulse(t, 8)) * kb
    m = m_snow(t)
    if m > 0:
        r = np.clip(P2r / 4.2, 0, 1)[:, None]
        if t < T_V2: tip = MAG
        elif t < T_BRIDGE: tip = GOLD
        else:
            hc = (t * 0.25) % 3
            cs = [MAG, GOLD, VIO, MAG]
            i = int(hc); tip = cs[i] * (1 - (hc - i)) + cs[i + 1] * (hc - i)
        snowc = WHITE * (1 - r) ** 2 + ICE * 2 * r * (1 - r) + tip * r ** 2
        snowc = snowc * 1.15
        base = base * (1 - m) + snowc * m
    return base.astype(np.float32)

def rng_flick(t):
    return 0.5 + 0.5 * math.sin(t * 37.0) * math.sin(t * 13.0)

ROW_MESS = np.random.default_rng(4).normal(0, 1.4, R).astype(np.float32)
def cells(t):
    """returns centers (N,3), rotation (N,3,3), colors, alpha"""
    tau = tau_explode(t)
    P = G.copy()
    Rm = None
    if tau > 0:
        P = G + V * (1 - np.exp(-1.6 * tau))[None] + np.array([0, -0.2, 0], np.float32) * tau
        P[:, 1] += 0.05 * np.sin(t * 1.3 + ri) * sstep(T_PRE - 2, T_PRE, t)
        Rm = rodrigues(AX, OM * tau * 0.55)
    # rows messed then rolled back (V2)
    if t > T_SORRY - 1.7 and t < T_ROWS + 3.5:
        k = np.clip((t - T_ROWS - ri * 0.04) / 0.9, 0, 1)
        amt = sstep(T_SORRY - 1.5, T_SORRY + 1.5, t) * ((1 - (1 - (1 - k) ** 3)) if t >= T_ROWS else np.ones_like(k))
        P = P.copy(); P[:, 0] += ROW_MESS[ri] * amt
        P[:, 2] += np.abs(ROW_MESS[ri]) * 0.5 * amt
    # breathing in pre2 (auto suspend/resume)
    m = m_snow(t)
    if m > 0:
        sp = spin(t)
        cs, sn = math.cos(sp), math.sin(sp)
        S = S_POS.copy()
        S[:, 0], S[:, 1] = S_POS[:, 0] * cs - S_POS[:, 1] * sn, S_POS[:, 0] * sn + S_POS[:, 1] * cs
        pulse = 1 + 0.06 * beat_pulse(t, 6)
        S *= pulse
        em = ease_io(m)
        arc = np.sin(math.pi * em) * (1.8 + 1.2 * np.sin(np.arange(N) * 1.7))
        P = P * (1 - em) + S * em
        P[:, 2] -= arc
        ang = (S_ANG + sp) * em
        Rz = np.zeros((N, 3, 3), np.float32)
        Rz[:, 0, 0] = np.cos(ang); Rz[:, 0, 1] = -np.sin(ang); Rz[:, 1, 0] = np.sin(ang); Rz[:, 1, 1] = np.cos(ang); Rz[:, 2, 2] = 1
        Rm = Rz
    if T_BUILD - 0.5 < t < T_FINAL + 0.1:
        kb = sstep(T_BUILD, T_FINAL - 0.3, t) * (1 - sstep(T_BACKUP - 0.4, T_BACKUP + 0.6, t) * 0.7)
        bp = beat_pulse(t, 6)
        jit = np.sin(np.arange(N) * 12.9898 + t * 17) * 0.5
        P = P.copy()
        P[:, :2] += G[:, :2] * (0.25 * kb + 0.18 * kb * bp)
        P[:, 2] += (jit * 1.6 * kb + np.sin(ri * 0.6 + t * 4) * 0.5 * kb)
        if Rm is None:
            Rm = rodrigues(AX, OM * 0.25 * kb * np.sin(t * 3 + np.arange(N)))
    P2r = np.hypot(P[:, 0], P[:, 1])
    col = cell_colors(t, P2r)
    alpha = np.ones(N, np.float32)
    alpha *= np.clip((t - 2.0 - ri * 0.11) / 0.5, 0, 1)
    return P, Rm, col, alpha

def draw_cells(fill, edge, P, Rm, col, alpha, cam, W, H, scale=1.0, edge_only=False, thick=1, inner=True):
    loc = LOC * scale
    if Rm is None: Cn = P[:, None, :] + loc[None]
    else: Cn = P[:, None, :] + np.einsum('nij,kj->nki', Rm, loc)
    u, v, z = project(Cn.reshape(-1, 3), cam, W, H)
    u = u.reshape(N, 4); v = v.reshape(N, 4); z = z.reshape(N, 4)
    if inner and not edge_only:
        a = P + (np.einsum('nij,j->ni', Rm, np.array([-CW * 0.3, 0, 0], np.float32)) if Rm is not None else np.array([-CW * 0.3, 0, 0], np.float32))
        b = P + (np.einsum('nij,j->ni', Rm, np.array([CW * 0.12, 0, 0], np.float32)) if Rm is not None else np.array([CW * 0.12, 0, 0], np.float32))
        ua, va, za = project(a, cam, W, H); ub, vb, zb = project(b, cam, W, H)
    order = np.argsort(-z.mean(1))
    pts = np.stack([u, v], -1) * 16
    for i in order:
        if alpha[i] <= 0.01 or z[i].min() < 0.25: continue
        p = pts[i].astype(np.int32)
        if p[:, 0].max() < -2000 or p[:, 0].min() > W * 16 + 2000: continue
        c = (col[i] * 255 * alpha[i]).tolist()
        if not edge_only:
            cv2.fillConvexPoly(fill, p, [x * 0.5 for x in c], cv2.LINE_AA, 4)
            if inner:
                cv2.line(fill, (int(ua[i] * 16), int(va[i] * 16)), (int(ub[i] * 16), int(vb[i] * 16)), c, 1, cv2.LINE_AA, 4)
        cv2.polylines(edge, [p], True, c, thick, cv2.LINE_AA, 4)

# ======================================================================= camera path
def camera(t):
    sec = section(t)
    if t < T_DROP:
        k = sstep(0, T_DROP, t)
        cam = orbit(lerp(-0.55, -0.12, k), lerp(0.28, 0.06, k), lerp(14.0, 8.4, ease_io(k)), (0, 0.0, 0))
    elif t < T_PRE:
        k = sstep(T_DROP, T_DROP + 4, t); k2 = sstep(T_REMEMBER, T_PRE, t)
        cam = orbit(lerp(-0.12, 0.25, k) + 0.15 * k2, lerp(0.06, -0.08, k), lerp(8.4, 14.5, ease_out((t - T_DROP) / 3.0)) - 1.5 * k2, (0, -0.8 * k, 0), roll=0.05 * math.sin(t * 0.5))
    elif t < T_CH1:
        k = sstep(T_PRE, T_CH1, t)
        cam = orbit(0.4 + 0.25 * k, -0.08 + 0.12 * k, lerp(13.0, 11.0, k), (0, -0.8, 0), roll=-0.04 * k)
    elif t < T_V2 - 1.8:
        k = sstep(T_CH1, T_CH1 + 1.4, t)
        base = orbit(lerp(0.65, 0.0, ease_io(k)), lerp(0.04, 0.0, k), lerp(11.0, 10.5, k), (0, lerp(-0.8, 0, k), 0))
        sw = math.sin((t - T_CH1) * 0.35)
        cam = orbit(0.22 * sw * k + lerp(0.65, 0, ease_io(k)), 0.1 * math.sin((t - T_CH1) * 0.23) * k, lerp(11.0, 10.2 - 0.6 * beat_pulse(t, 4), k), (0, 0, 0), roll=0.06 * sw * k)
    elif t < T_WARE - 0.4:
        k = sstep(T_V2 - 1.8, T_V2 + 3, t); k2 = sstep(T_V2 + 3, T_WARE, t)
        cam = orbit(lerp(0.0, 0.55, ease_io(k)) - 0.9 * k2, lerp(0.0, 0.32, k), lerp(10.2, 22.0, ease_io(k)) + 2 * k2, (0, 0, lerp(0, 6, k)))
    elif t < T_SORRY - 0.6:
        k = sstep(T_WARE - 0.4, T_WARE + 1.6, t)
        cam = orbit(lerp(-0.35, -0.2, k) + 0.08 * (t - T_WARE) / 9, lerp(0.32, 0.1, k), lerp(24, 16.5, ease_io(k)), (0, lerp(0, -8.9, ease_io(k)), lerp(6, 1.5, k)))
    elif t < T_PRE2 - 0.5:
        k = sstep(T_SORRY - 0.6, T_SORRY + 1.4, t)
        cam = orbit(lerp(-0.2, 0.35, ease_io(k)) - 0.03 * (t - T_SORRY), lerp(0.12, 0.05, k), lerp(15, 10.5, ease_io(k)), (lerp(0, 2.2, k), lerp(-8.2, 0, ease_io(k)), lerp(1.5, 0, k)))
    elif t < T_CH2:
        k = sstep(T_PRE2 - 0.5, T_CH2, t)
        cam = orbit(lerp(0.35, -0.3, k), 0.05, lerp(10.5, 9.0, k), (lerp(2.2, 0, sstep(T_PRE2 - 0.5, T_PRE2 + 1.5, t)), 0, 0))
    elif t < T_BRIDGE - 0.6:
        tt = t - T_CH2
        k = sstep(T_CH2, T_CH2 + 1.2, t)
        cam = orbit(lerp(-0.3, 0, k) + 0.5 * math.sin(tt * 0.22), 0.18 * math.sin(tt * 0.17), lerp(9.0, 10.6, k) - 0.7 * beat_pulse(t, 4) - 1.2 * math.sin(tt * 0.12) ** 2, (0, 0, 0), roll=0.1 * math.sin(tt * 0.19))
    elif t < T_BUILD:
        k = sstep(T_BRIDGE - 0.6, T_BRIDGE + 3, t); k2 = sstep(T_TT - 1, T_TT + 2.5, t); k3 = sstep(T_TRUST, T_BUILD, t)
        cam = orbit(lerp(0.2, -0.3, k) + 1.0 * k2 * (1 - 0.6 * k3) + 0.02 * (t - T_BRIDGE), lerp(0.1, 0.2, k) - 0.1 * k3, lerp(12, 13.5, k) + 2.5 * k2 - 3.5 * k3, (-1.8 * (1 - k2), 0, lerp(0, 1.4, k2) * (1 - k3)))
    elif t < T_FINAL:
        k = sstep(T_BUILD, T_FINAL, t)
        cam = orbit(0.25 * (1 - k) + 0.6 * math.sin(k * 3), lerp(0.1, -0.35, ease_io(k)), lerp(10.0, 7.5, ease_io(k)), (0, lerp(0, 1.0, k), 0), roll=0.12 * k * math.sin(t * 2))
    elif t < T_OUTRO - 0.3:
        tt = t - T_FINAL
        k = sstep(T_FINAL, T_FINAL + 1.2, t)
        cam = orbit(0.55 * math.sin(tt * 0.18), 0.22 * math.sin(tt * 0.13) - 0.12 * (1 - k), lerp(8.0, 13.5 + 2.5 * math.sin(tt * 0.1), ease_io(k)) - 0.9 * beat_pulse(t, 4), (0, 0, 0), roll=0.08 * math.sin(tt * 0.21))
    else:
        k = sstep(T_OUTRO - 0.3, DUR, t)
        cam = orbit(0.4 * (1 - k) + 0.1, 0.1 + 0.15 * k, lerp(14, 26, ease_io(k)), (0, lerp(0, 1.5, k), 0))
    # shake
    sh = 0.0
    if T_DROP <= t < T_DROP + 1.4: sh += 0.35 * math.exp(-(t - T_DROP) * 3)
    s, i = last_stamp(t)
    if s is not None and t - s < 0.5: sh += 0.12 * math.exp(-(t - s) * 8)
    if T_FINAL <= t < T_FINAL + 1: sh += 0.25 * math.exp(-(t - T_FINAL) * 4)
    if T_BUILD < t < T_FINAL: sh += 0.04 * sstep(T_BUILD, T_FINAL, t) * beat_pulse(t, 10)
    if sh > 0:
        cam.pos = cam.pos + np.array([math.sin(t * 91), math.sin(t * 73 + 1), 0], np.float32) * sh
    return cam
