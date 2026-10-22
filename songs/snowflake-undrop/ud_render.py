from ud_scene import *
import sys, subprocess, os

# ======================================================================= extras: clones
CLONE_SLOTS = np.array([(-5.4, 0, 0.0), (5.4, 0, 0.0), (-10.8, 0, 1.5), (10.8, 0, 1.5), (-5.4, 0, 6.0), (5.4, 0, 6.0),
                        (0, 0, 6.5), (-10.8, 0, 7.5), (10.8, 0, 7.5), (0, 0, 12.5), (-5.4, 0, 12.0), (5.4, 0, 12.0)], np.float32)
_sub = np.array([-0.12, -0.04, 0.04, 0.12], np.float32)
CLONE_PTS = np.concatenate([G + np.array([s, 0, 0], np.float32) for s in _sub])
CLONE_HDR = np.concatenate([IS_HDR] * len(_sub))
CLONE_V = np.concatenate([V] * len(_sub)) * 1.3
def clone_state(t):
    out = []
    for i, slot in enumerate(CLONE_SLOTS):
        t0 = T_V2 - 0.6 + i * 0.42
        k = ease_io((t - t0) / 0.9)
        if k <= 0: continue
        fade = 1 - sstep(T_WARE - 0.8, T_WARE + 0.8, t)
        if fade <= 0: continue
        pos = slot * k
        out.append((i, pos, k * fade))
    return out

def draw_clones(t, cam, buf, W, H):
    labels = []
    for i, pos, a in clone_state(t):
        P = CLONE_PTS + pos
        col = (VIO if i % 2 else MAG) * 0.55 + ICE * 0.25
        w = np.full(len(P), 1.5 * a, np.float32)
        w[CLONE_HDR] *= 1.8
        if i == 0 and t > T_WRECK:
            tau = t - T_WRECK
            P = P + CLONE_V * (1 - math.exp(-2.2 * tau)) + np.array([0, -0.6, 0]) * tau
            w = w * max(0, 1 - tau / 3.5) * (1.5 + 4 * math.exp(-tau * 3))
            col = MAG * 1.5
        u, v, z = project(P, cam, W, H)
        splat(buf, u, v, w * (z > 0.3), col)
        uu, vv, zz = project(pos[None] + np.array([[0, G[:, 1].max() + 0.45, 0]], np.float32), cam, W, H)
        labels.append((i, uu[0], vv[0], zz[0], a))
    return labels

# ======================================================================= extras: warehouse towers
NT, NB = 7, 13
TX = np.linspace(-6.6, 6.6, NT)
def bar_state(t):
    st = np.ones((NT, NB), np.float32); col = np.zeros((NT, NB, 3), np.float32)
    col[:] = ICE * 0.8 + TEAL * 0.2
    for k in range(NT):
        for b in range(NB):
            off = T_SUSP + 0.35 + k * 0.16 + (NB - b) * 0.035
            on = T_QUERY + 0.75 + abs(k - NT // 2) * 0.09 + b * 0.04
            if t < off: s = 0.75 + 0.25 * math.sin(t * 9 + k * 3 + b * 1.7) ** 2
            elif t < on: s = 0.05 + 0.6 * math.exp(-(t - off) * 7)
            else:
                x = t - on; s = 1.0 + 1.2 * math.exp(-x * 3)
                col[k, b] = GOLD * math.exp(-x * 1.2) + (ICE * 0.8 + TEAL * 0.2) * (1 - math.exp(-x * 1.2))
            st[k, b] = s
    return st, col

def draw_towers(t, cam, fill, edge, buf, W, H):
    a = win(t, T_WARE - 0.2, T_SORRY + 0.2, 1.0, 1.4)
    if a <= 0: return
    st, col = bar_state(t)
    quads = []
    for k in range(NT):
        for b in range(NB):
            y = -11.6 + b * 0.42; x = TX[k]
            q = np.array([[x - 0.72, y, 0], [x + 0.72, y, 0], [x + 0.72, y + 0.28, 0], [x - 0.72, y + 0.28, 0]], np.float32)
            quads.append((q, st[k, b], col[k, b]))
    for q, s, c in quads:
        u, v, z = project(q, cam, W, H)
        if z.min() < 0.3: continue
        p = (np.stack([u, v], -1) * 16).astype(np.int32)
        cc = (c * 255 * s * a).tolist()
        cv2.fillConvexPoly(fill, p, [x * 0.6 for x in cc], cv2.LINE_AA, 4)
        cv2.polylines(edge, [p], True, cc, 1, cv2.LINE_AA, 4)
    # floor grid
    gx = np.linspace(-10, 10, 21)
    for x in gx:
        P = np.array([[x, -11.7, -6], [x, -11.7, 6]], np.float32); u, v, z = project(P, cam, W, H)
        if z.min() > 0.3: cv2.line(edge, (int(u[0] * 16), int(v[0] * 16)), (int(u[1] * 16), int(v[1] * 16)), [int(30 * a), int(60 * a), int(90 * a)], 1, cv2.LINE_AA, 4)
    for zq in np.linspace(-6, 6, 13):
        P = np.array([[-10, -11.7, zq], [10, -11.7, zq]], np.float32); u, v, z = project(P, cam, W, H)
        if z.min() > 0.3: cv2.line(edge, (int(u[0] * 16), int(v[0] * 16)), (int(u[1] * 16), int(v[1] * 16)), [int(30 * a), int(60 * a), int(90 * a)], 1, cv2.LINE_AA, 4)
    # query packet
    if T_QUERY - 0.1 < t < T_QUERY + 1.4:
        x = clamp((t - T_QUERY) / 0.8)
        src = np.array([-14, -7.5, -5], np.float32); dst = np.array([0, -9.0, 0], np.float32)
        tr = np.linspace(max(0, x - 0.35), x, 40)
        P = src[None] + (dst - src)[None] * tr[:, None]
        P[:, 1] += np.sin(tr * math.pi) * 2.0
        u, v, z = project(P, cam, W, H)
        w = (tr - tr.min()) / (np.ptp(tr) + 1e-6)
        w = (w ** 2) * 6 * (1 - sstep(0.85, 1.0, x))
        splat(buf, u, v, w.astype(np.float32), GOLD * 1.5)
        if x >= 1:
            # burst
            b = t - T_QUERY - 0.8
            ang = np.linspace(0, 2 * math.pi, 120)
            P = dst[None] + np.stack([np.cos(ang), np.sin(ang) * 0.4, np.sin(ang)], 1) * (b * 9)
            u, v, z = project(P.astype(np.float32), cam, W, H)
            splat(buf, u, v, np.full(120, 2.5 * max(0, 1 - b / 0.6), np.float32), GOLD)

# ======================================================================= extras: time-travel ghosts
GHOST_COLS = [TEAL, hexc('3fa8ff'), VIO, MAG, GOLD, hexc('ff7a6a')]
def draw_ghosts(t, cam, edge, W, H):
    a = win(t, T_TT - 0.4, T_BUILD - 0.6, 0.8, 1.6)
    if a <= 0: return
    for k in range(6):
        kk = sstep(T_TT - 0.4 + k * 0.32, T_TT + 0.4 + k * 0.32, t)
        merge = sstep(T_TRUST - 0.5, T_TRUST + 3.0, t)
        dz = (k + 1) * 1.05 * kk * (1 - merge)
        dx = (k + 1) * 0.25 * kk * (1 - merge)
        P = G + np.array([dx, 0, dz], np.float32)
        col = np.broadcast_to(GHOST_COLS[k], (N, 3)).astype(np.float32)
        al = np.full(N, 0.55 * (1 - k / 7) * a * kk, np.float32)
        draw_cells(None, edge, P, None, col, al, cam, W, H, edge_only=True)

# ======================================================================= extras: frost / snowflakes
def frost_layer(t, cam, buf, W, H):
    m = m_snow(t)
    if m <= 0.01: return
    grow = ease_out(m)
    def one(sp, scale, offset, weight, tipc, sub=1):
        F = FROST[::sub]; Rr = FROST_R[::sub]
        cs, sn = math.cos(sp), math.sin(sp)
        P = F.copy()
        P[:, 0], P[:, 1] = F[:, 0] * cs - F[:, 1] * sn, F[:, 0] * sn + F[:, 1] * cs
        rr = np.hypot(F[:, 0], F[:, 1])
        vis = np.clip((grow * 4.6 - rr) / 0.6, 0, 1)
        P *= scale * (1 + 0.06 * beat_pulse(t, 6))
        P += offset
        u, v, z = project(P.astype(np.float32), cam, W, H)
        tw = 0.45 + 0.55 * np.sin(t * 5 + Rr * 60) ** 2
        w = (weight * vis * tw * (z > 0.3)).astype(np.float32)
        r = np.clip(rr / 4.3, 0, 1)[:, None]
        col = WHITE * (1 - r) + ICE * r * 1.2 * (1 - r) * 2 + tipc * r ** 1.5
        splat(buf, u, v, w, col.astype(np.float32))
    if t < T_V2: tip = MAG
    elif t < T_BRIDGE: tip = GOLD
    else:
        hc = (t * 0.25) % 3; cs_ = [MAG, GOLD, VIO, MAG]; i = int(hc); tip = cs_[i] * (1 - (hc - i)) + cs_[i + 1] * (hc - i)
    sp = spin(t)
    one(sp, 1.0, np.zeros(3, np.float32), 0.42, tip)
    if section(t) in ("FINAL", "CH2"):
        one(spin(t - 0.07), 1.0, np.zeros(3, np.float32), 0.16, tip, 2)
        one(spin(t - 0.14), 1.0, np.zeros(3, np.float32), 0.08, tip, 3)
    if section(t) == "FINAL" or (section(t) == "CH2"):
        n = 6
        amt = sstep(T_FINAL + 0.4, T_FINAL + 2.5, t) if t >= T_FINAL else sstep(T_CH2 + 6, T_CH2 + 10, t) * 0.8
        if amt > 0:
            for k in range(n):
                ang = k * 2 * math.pi / n - 0.13 * t
                rad = 8.2 if t >= T_FINAL else 7.0
                off = np.array([math.cos(ang) * rad, math.sin(ang) * rad * 0.62, 2.5 + math.sin(t * 0.5 + k) * 1.5], np.float32)
                c2 = [ICE, MAG, GOLD, VIO, TEAL, hexc('ff7a6a')][k]
                one(-sp * 1.3 + k, 0.32, off, 0.5 * amt, c2, 3)

def shockwaves(t, cam, edge, W, H):
    for s in STAMPS:
        x = (t - s) / 1.1
        if 0 <= x < 1:
            r = 0.6 + 10.5 * ease_out(x)
            ang = np.linspace(0, 2 * math.pi, 7) + spin(t)
            P = np.stack([np.cos(ang) * r, np.sin(ang) * r, np.zeros(7)], 1).astype(np.float32)
            u, v, z = project(P, cam, W, H)
            if z.min() < 0.3: continue
            p = (np.stack([u, v], -1) * 16).astype(np.int32)
            a = (1 - x) ** 2
            cv2.polylines(edge, [p], True, (ICE2 * 255 * a).tolist(), 2, cv2.LINE_AA, 4)
            P2 = P * 0.82
            u, v, z = project(P2, cam, W, H)
            cv2.polylines(edge, [(np.stack([u, v], -1) * 16).astype(np.int32)], True, (MAG * 200 * a).tolist(), 1, cv2.LINE_AA, 4)

# ======================================================================= levels
def light_level(t):
    lv = 1.0
    if T_PRE2 - 0.5 < t < T_CH2:
        # breathe: suspend (dim) .. resume (bright)
        x = t - T_PRE2
        lv = 0.35 + 0.65 * (0.5 + 0.5 * math.cos(x * 2 * math.pi / 2.4))
        lv = lerp(1.0, lv, sstep(T_PRE2 - 0.5, T_PRE2, t)) * lerp(1, 0.6, sstep(T_BILL, T_BILL + 1.5, t))
        lv = lerp(lv, 1.0, sstep(T_CH2 - 1.6, T_CH2, t))
    if T_WARE - 0.5 < t < T_SORRY + 0.5:
        lv *= lerp(1, 0.35, win(t, T_WARE - 0.5, T_SORRY - 0.5, 1.0, 1.0))
    if T_BRIDGE < t < T_BUILD:
        lv *= lerp(1, 0.55, win(t, T_BRIDGE, T_BUILD - 1, 1.5, 1.0))
    if T_BACKUP - 0.6 < t < T_FINAL:
        lv *= lerp(1, 0.25, sstep(T_BACKUP - 0.6, T_BACKUP + 0.6, t))
    if t > T_OUTRO + 2: lv *= lerp(1, 0.4, sstep(T_OUTRO + 2, DUR, t))
    return lv

def bloom_amt(t):
    b = 0.9
    sec = section(t)
    if sec in ("CH1", "CH2"): b = 1.3 + 0.6 * beat_pulse(t, 5)
    if sec == "FINAL": b = 1.6 + 0.8 * beat_pulse(t, 5)
    if sec == "BUILD": b = lerp(1.0, 2.0, sstep(T_BUILD, T_FINAL, t))
    if T_DROP <= t < T_DROP + 1.5: b += 2.0 * math.exp(-(t - T_DROP) * 3)
    return b

def rays_amt(t):
    m = m_snow(t)
    a = m * (0.55 if section(t) != "FINAL" else 1.0)
    if section(t) == "BUILD": a = max(a, 0.9 * sstep(T_BUILD, T_FINAL, t))
    return a * (1 + 0.6 * beat_pulse(t, 6))

def streak_amt(t):
    sec = section(t); a = 0.0
    if sec in ("CH1", "CH2"): a = 0.5 * m_snow(t) + 0.4 * beat_pulse(t, 5)
    if sec == "FINAL": a = 0.8 + 0.5 * beat_pulse(t, 5)
    if sec == "BUILD": a = 0.8 * sstep(T_BUILD, T_FINAL, t)
    if T_DROP <= t < T_DROP + 1.5: a += 1.0 * math.exp(-(t - T_DROP) * 3)
    return a

def flash(t):
    f = 0.0; col = ICE2
    for s in STAMPS:
        if 0 <= t - s < 1.0: f += 0.38 * math.exp(-(t - s) * 7)
    if 0 <= t - T_CH1 < 3: f += 0.75 * math.exp(-(t - T_CH1) * 3.2)
    if 0 <= t - T_CH2 < 3: f += 0.55 * math.exp(-(t - T_CH2) * 3.2)
    if 0 <= t - T_FINAL < 4: f += 1.25 * math.exp(-(t - T_FINAL) * 2.2)
    if T_FINAL - 0.35 <= t < T_FINAL: f += 0.6 * sstep(T_FINAL - 0.35, T_FINAL, t)
    if 0 <= t - T_DROP < 2: return f + 0.9 * math.exp(-(t - T_DROP) * 5), RED * 0.9 + 0.1
    return f, col

def glitch_amt(t):
    g = 0.0
    if 0 <= t - T_DROP < 1.2: g += 1.0 * math.exp(-(t - T_DROP) * 2.5)
    if T_DROP < t < T_REMEMBER and (int(t * 3.3) % 7 == 0): g += 0.25
    if 0 <= t - T_WRECK < 0.6: g += 0.7 * math.exp(-(t - T_WRECK) * 5)
    for s in STAMPS:
        if 0 <= t - s < 0.18: g += 0.35
    for tt in (T_SORRY + 0.9, T_BIZ + 1.0, T_OFF + 0.9):
        if 0 <= t - tt < 0.25: g += 0.35
    if 0 <= t - T_FINAL < 0.5: g += 0.6
    return g

# ======================================================================= UI helpers (full-res, display space)
_RR = {}
def rr_mask(w, h, r):
    k = (w, h, r)
    if k not in _RR:
        m = np.zeros((h, w), np.uint8)
        cv2.rectangle(m, (r, 0), (w - r - 1, h - 1), 255, -1); cv2.rectangle(m, (0, r), (w - 1, h - r - 1), 255, -1)
        for cx, cy in ((r, r), (w - r - 1, r), (r, h - r - 1), (w - r - 1, h - r - 1)): cv2.circle(m, (cx, cy), r, 255, -1, cv2.LINE_AA)
        e = cv2.Canny(m, 50, 150)
        _RR[k] = (m.astype(np.float32) / 255, cv2.GaussianBlur(e.astype(np.float32) / 255, (0, 0), 0.6))
    return _RR[k]

def card(img, x, y, w, h, op, border=ICE, dark=0.62, r=14, tint=None):
    if op <= 0.01: return
    x, y, w, h = int(x), int(y), int(w), int(h)
    H, W = img.shape[:2]
    if x < 0 or y < 0 or x + w > W or y + h > H:
        x = max(0, min(x, W - w)); y = max(0, min(y, H - h))
    m, e = rr_mask(w, h, r)
    reg = img[y:y + h, x:x + w]
    reg *= (1 - m[..., None] * dark * op)
    if tint is not None: reg += m[..., None] * tint * 0.06 * op
    reg += e[..., None] * border * 0.9 * op

def txt(img, s, x, y, size, color, op=1.0, path=F_INTER, glow=0, glow_op=0.0, anchor='lt'):
    if op <= 0.01 or not s: return
    blit(img, sprite(s, path, size, glow), x, y, color, op, glow_op, anchor=anchor)

def typed(s, t, t0, t1):
    if t < t0: return ""
    n = int(len(s) * clamp((t - t0) / max(0.01, t1 - t0)))
    return s[:n]

# ======================================================================= overlays
def overlay_terminal(img, t, W, H, ts):
    p1 = win(t, 2.6, T_REMEMBER + 1.0, 0.6, 1.2)
    p2 = win(t, T_RET - 0.4, T_CH1 + 3.0, 0.4, 1.0)
    if p1 <= 0 and p2 <= 0: return
    fs = int(28 * ts); lh = int(fs * 1.55)
    vert = H > W
    x = int(W * (0.05 if not vert else 0.06)); y = int(H * (0.075 if not vert else 0.11))
    w = int(W * (0.43 if not vert else 0.88))
    lines = []
    blink = (int(t * 2.2) % 2 == 0)
    if p1 > 0:
        op = p1
        cmd = typed("DROP TABLE production;", t, T_TYPE, T_DROP - 0.35)
        cur = "\x00" if (t < T_DROP and blink) else ""
        lines.append([("snowsql> ", ICE * 0.8), (cmd + cur, IVORY)])
        if t > T_DROP + 0.12: lines.append([("Table PRODUCTION successfully dropped.", RED * 1.2)])
        if t > T_DROP + 0.5: lines.append([("1 Row(s) produced. Time Elapsed: 0.214s", IVORY * 0.45)])
        if t > T_DROP + 1.4: lines.append([("snowsql> ", ICE * 0.8), ("\x00" if blink else "", IVORY)])
    else:
        op = p2
        lines.append([("snowsql> ", ICE * 0.8), (typed("SHOW TABLES HISTORY LIKE 'PRODUCTION';", t, T_RET, T_RET + 1.6), IVORY)])
        if t > T_RET + 1.75:
            lines.append([("name        dropped_on           retention", IVORY * 0.45)])
            lines.append([("PRODUCTION  2026-10-12 03:02:11  1 day", ICE2)])
        if t > T_RUN - 0.2:
            cmd = typed("UNDROP TABLE production;", t, T_RUN, T_CH1 - 0.35)
            cur = "\x00" if (t < T_CH1 and blink) else ""
            lines.append([("snowsql> ", ICE * 0.8), (cmd + cur, WHITE)])
        if t >= T_CH1: lines.append([("Table PRODUCTION successfully restored.", TEAL * 1.1)])
    h = int(lh * (len(lines) + 1.4))
    card(img, x, y, w, h, op * 0.95, border=(RED if (p1 > 0 and t > T_DROP) else ICE) * 0.7, dark=0.66)
    # title bar dots
    for i, c in enumerate([RED, GOLD, TEAL]):
        cv2.circle(img, (x + int(22 * ts) + i * int(20 * ts), y + int(20 * ts)), max(2, int(5 * ts)), (c * 0.8 * op).tolist(), -1, cv2.LINE_AA)
    txt(img, "worksheet — 03:02 AM", x + w - int(16 * ts), y + int(9 * ts), int(18 * ts), IVORY * 0.4, op, F_MONO)
    yy = y + int(lh * 1.0)
    for ln in lines:
        xx = x + int(22 * ts)
        for s, c in ln:
            curs = s.endswith("\x00"); s = s.rstrip("\x00")
            txt(img, s, xx, yy, fs, c, op, F_MONO, glow=3, glow_op=0.35)
            xx += int(text_w(s, F_MONO, fs))
            if curs:
                cv2.rectangle(img, (xx + 2, yy + int(fs * 0.18)), (xx + int(fs * 0.58), yy + int(fs * 1.22)), (IVORY * 0.85 * op).tolist(), -1)
        yy += lh

def overlay_clock(img, t, W, H, ts):
    a = win(t, 2.4, T_PRE - 1, 0.8, 1.0) + win(t, T_RET - 0.4, T_CH1 + 0.5, 0.4, 0.6)
    if a <= 0: return
    sec = int(2 * 60 + 9 + t)
    s = f"03:{sec // 60:02d}:{sec % 60:02d} AM"
    red = T_DROP < t < T_REMEMBER + 2
    col = (RED * 1.1 if (red and int(t * 2) % 2) else IVORY * 0.6)
    txt(img, s, W - int(36 * ts), int(H * 0.07), int(30 * ts), col, a, F_MONOB, anchor='lt' if False else 'lt') if False else None
    sp = sprite(s, F_MONOB, int(30 * ts), 3)
    blit(img, sp, W - int(40 * ts) - sp[0].shape[1], int(H * 0.075), col, a, 0.4)

def pill(img, x, y, s, op, col, ts, sub=None, prog=None, strike=0.0):
    fs = int(24 * ts)
    w = int(text_w(s, F_INTER, fs) + 60 * ts); h = int(fs * 2.2 + (fs * 1.1 if prog is not None else 0))
    x = int(x - w)
    card(img, x, y, w, h, op, border=col * 0.8, dark=0.6, r=int(h / 2.2))
    cv2.circle(img, (x + int(22 * ts), y + int(fs * 1.12)), max(3, int(6 * ts)), (col * op).tolist(), -1, cv2.LINE_AA)
    txt(img, s, x + int(38 * ts), y + int(fs * 0.5), fs, IVORY, op)
    if prog is not None:
        bx = x + int(38 * ts); bw = w - int(70 * ts); by = y + int(fs * 2.0)
        cv2.rectangle(img, (bx, by), (bx + bw, by + max(2, int(4 * ts))), (IVORY * 0.2 * op).tolist(), -1)
        cv2.rectangle(img, (bx, by), (bx + int(bw * prog), by + max(2, int(4 * ts))), (col * op).tolist(), -1)
    if strike > 0:
        cv2.line(img, (x + int(14 * ts), y + h // 2), (x + int(14 * ts + (w - 28 * ts) * strike), y + h // 2), (RED * 1.2 * op).tolist(), max(2, int(3 * ts)), cv2.LINE_AA)
    return h

def overlay_toasts(img, t, W, H, ts):
    if not (12 < t < T_REMEMBER + 3): return
    vert = H > W
    x = W - int((40 if not vert else 150) * ts); y = int(H * (0.14 if not vert else 0.25))
    items = [(word_t("Called my mother", "mother"), "Calling Mom…", GOLD, None),
             (word_t("drafted notice", "notice"), "Resignation_FINAL_v2.docx", ICE, None),
             (word_t("LinkedIn halfway", "LinkedIn"), "#OpenToWork  ·  updating profile", MAG, 'p')]
    for t0, s, c, pr in items:
        a = sstep(t0 - 0.1, t0 + 0.25, t) * (1 - sstep(T_REMEMBER + 1.2, T_REMEMBER + 2.4, t))
        if a <= 0: continue
        dy = (1 - ease_out((t - t0) / 0.4)) * 30 * ts
        strike = sstep(T_REMEMBER, T_REMEMBER + 0.8, t)
        prog = None
        if pr: prog = 0.5 * ease_out((t - t0) / 3.0) * (1 - strike) + 0.5 * strike * 0
        h = pill(img, x, int(y + dy), s, a, c, ts, prog=prog, strike=strike)
        y += h + int(14 * ts)

def overlay_clones(img, t, W, H, ts, labels, sc):
    a = win(t, T_V2 - 0.4, T_WARE - 0.6, 0.6, 0.8)
    if a <= 0: return
    vert = H > W
    x = int(W * 0.05); y = int(H * (0.08 if not vert else 0.1))
    n = len(clone_state(t))
    txt(img, "ZERO-COPY CLONE", x, y, int(22 * ts), ICE2, a, F_MONOB, 3, 0.4)
    txt(img, f"clones: {n:02d}    storage added: 0 B", x, y + int(36 * ts), int(22 * ts), IVORY * 0.7, a, F_MONO)
    if t > T_WRECK: txt(img, "prod_clone_01: wrecked   prod: fine", x, y + int(68 * ts), int(22 * ts), MAG * 1.1, a * sstep(T_WRECK, T_WRECK + 0.3, t), F_MONO)
    # prod label
    for i, u, v, z, al in labels:
        if z < 0.5: continue
        name = f"prod_clone_{i + 1:02d}"
        op = al * a * clamp(9 / z) * (0.25 if (i == 0 and t > T_WRECK + 1.5) else 1)
        txt(img, name, u * sc, v * sc, int(17 * ts), (MAG if i == 0 and t > T_WRECK else VIO * 0.6 + 0.4), op, F_MONO, anchor='c')
    cam_lab = None

def overlay_prod_label(img, t, W, H, ts, cam, sc):
    a = win(t, T_V2 + 0.3, T_WARE - 0.6, 0.6, 0.8) + win(t, T_ROWS + 0.4, T_PRE2 + 1, 0.5, 0.8) * 0
    if a <= 0: return
    u, v, z = project(np.array([[0, G[:, 1].max() + 0.5, 0]], np.float32), cam, int(W / sc), int(H / sc))
    s = "prod" if t < T_PROD else "prod  ·  not even listening"
    txt(img, s, u[0] * sc, v[0] * sc, int(22 * ts), GOLD, a, F_MONOB, 3, 0.5, anchor='c')

def overlay_warehouse(img, t, W, H, ts):
    a = win(t, T_WARE + 0.2, T_SORRY - 0.6, 0.6, 0.6)
    if a <= 0: return
    vert = H > W
    x = int(W * 0.05); y = int(H * (0.08 if not vert else 0.1)); w = int((440 if not vert else 560) * ts); h = int(150 * ts)
    card(img, x, y, w, h, a, border=ICE * 0.6)
    txt(img, "WAREHOUSE   COMPUTE_WH", x + int(22 * ts), y + int(18 * ts), int(20 * ts), IVORY * 0.6, a, F_MONO)
    if t < T_SUSP + 1.0: st, c, cr, fl = "RUNNING", TEAL, "credits/hr  1.00", 1
    elif t < T_QUERY: st, c, cr, fl = "SUSPENDED", IVORY * 0.55, "credits/hr  0.00", 0
    elif t < T_QUERY + 1.7: st, c, cr, fl = "RESUMING", GOLD, "credits/hr  1.00", int(t * 6) % 2
    else: st, c, cr, fl = "RUNNING", GOLD, "credits/hr  1.00", 1
    cc = (x + int(36 * ts), y + int(74 * ts)); rr_ = int(10 * ts)
    cv2.circle(img, cc, rr_, (c * a).tolist(), -1 if fl else max(1, int(2 * ts)), cv2.LINE_AA)
    txt(img, st, x + int(58 * ts), y + int(52 * ts), int(34 * ts), c, a, F_INTER, 4, 0.5)
    txt(img, cr, x + int(22 * ts), y + int(104 * ts), int(20 * ts), IVORY * 0.55, a, F_MONO)
    if T_QUERY - 0.3 < t < T_SORRY - 0.5:
        q = typed("SELECT * FROM production;", t, T_QUERY - 0.3, T_QUERY + 0.4)
        txt(img, "snowsql> " + q, x, y + h + int(22 * ts), int(24 * ts), GOLD * 0.9 + 0.1, a, F_MONO, 3, 0.4)

def overlay_bubbles(img, t, W, H, ts):
    a = win(t, T_SORRY - 0.3, T_PRE2 - 0.6, 0.3, 0.8)
    if a <= 0: return
    vert = H > W
    fs = int(30 * ts)
    x = W - int((70 if not vert else 150) * ts); y = int(H * (0.12 if not vert else 0.14))
    fs = int((30 if not vert else 26) * ts)
    items = [(T_SORRY, "sorry, just saw this"), (T_BIZ, "will circle back in 3–5 business days"), (T_OFF, "let's take this offline")]
    for t0, s in items:
        o = sstep(t0 - 0.15, t0 + 0.15, t) * a
        if o <= 0: continue
        st = sstep(t0 + 0.9, t0 + 1.25, t)
        dim = 1 - 0.55 * sstep(t0 + 1.3, t0 + 2.0, t)
        w = int(text_w(s, F_INTER, fs) + 56 * ts); h = int(fs * 2.1)
        jit = (math.sin(t * 80) * 6 * ts) if 0 < t - t0 - 0.9 < 0.25 else 0
        xx = x - w + int(jit)
        card(img, xx, y, w, h, o * dim, border=IVORY * 0.4, dark=0.55, r=int(h / 2.3), tint=VIO)
        txt(img, s, xx + int(28 * ts), y + int(fs * 0.45), fs, IVORY, o * dim)
        if st > 0:
            cv2.line(img, (xx + int(16 * ts), y + h // 2), (xx + int(16 * ts + (w - 32 * ts) * st), y + h // 2), (RED * 1.3 * o).tolist(), max(2, int(4 * ts)), cv2.LINE_AA)
        y += h + int(18 * ts)
    o = sstep(T_ROWS + 0.2, T_ROWS + 0.6, t) * a
    if o > 0:
        s = "rows rolled back  ·  0.31s"
        w = int(text_w(s, F_INTER, fs) + 56 * ts); h = int(fs * 2.1)
        xx = int(W * 0.06) if not vert else int(W * 0.06)
        card(img, xx, y + int(10 * ts), w, h, o, border=TEAL, dark=0.55, r=int(h / 2.3), tint=TEAL)
        txt(img, s, xx + int(28 * ts), y + int(10 * ts) + int(fs * 0.45), fs, TEAL * 1.1, o, F_INTER, 4, 0.4)

def overlay_pre2(img, t, W, H, ts):
    a = win(t, T_PRE2 - 0.2, T_CH2 - 0.3, 0.4, 0.4)
    if a <= 0: return
    vert = H > W
    x = int(W * 0.06); y = int(H * (0.1 if not vert else 0.12))
    lv = light_level(t)
    txt(img, "ALTER WAREHOUSE SET", x, y, int(22 * ts), IVORY * 0.5, a, F_MONO)
    txt(img, "  AUTO_SUSPEND = 60", x, y + int(36 * ts), int(30 * ts), ICE2 * (0.4 + 0.6 * (1 - lv)), a, F_MONOB, 3, 0.5)
    txt(img, "  AUTO_RESUME  = TRUE", x, y + int(78 * ts), int(30 * ts), GOLD * (0.4 + 0.6 * lv), a * sstep(word_t("Auto-suspend", "auto-resume") - 0.2, word_t("Auto-suspend", "auto-resume"), t), F_MONOB, 3, 0.5)
    if t > T_BILL - 0.1:
        o = sstep(T_BILL - 0.1, T_BILL + 0.3, t) * a
        txt(img, "billed while idle:  $0.00", x, y + int(140 * ts), int(26 * ts), TEAL, o, F_MONO, 3, 0.4)

DOC_A = ["UNDROP TABLE", "", "Brings back the most recent version", "of a table that was dropped,", "as long as it is still inside", "its data retention period.", "", "Names must not be taken. Love must", "be patient. Retention must be > 0."]
def overlay_bridge(img, t, W, H, ts):
    vert = H > W
    # doc card
    a = win(t, T_BRIDGE - 0.3, T_TT + 0.6, 0.5, 0.8)
    if a > 0:
        fs = int(25 * ts); lh = int(fs * 1.6)
        x = int(W * (0.07 if not vert else 0.08)); y = int(H * (0.12 if not vert else 0.12)) + int(10 * ts * math.sin(t * 0.7))
        w = int(W * (0.36 if not vert else 0.84)); h = int(lh * (len(DOC_A) + 1.5))
        card(img, x, y, w, h, a, border=IVORY * 0.45, dark=0.7)
        txt(img, "docs / sql-reference / undrop-table", x + int(24 * ts), y + int(16 * ts), int(17 * ts), IVORY * 0.4, a, F_MONO)
        yy = y + int(lh * 1.2)
        for i, s in enumerate(DOC_A):
            if i == 0:
                txt(img, s, x + int(24 * ts), yy, int(36 * ts), WHITE, a, F_DISPB); yy += int(lh * 1.0); continue
            if s:
                # highlight sweep on lines 2-5
                if 2 <= i <= 5:
                    hl = sstep(T_HIGH + (i - 2) * 0.35, T_HIGH + (i - 2) * 0.35 + 0.45, t)
                    if hl > 0:
                        tw = text_w(s, F_INTER_L, fs)
                        x0 = x + int(20 * ts); x1 = int(x0 + (tw + 8 * ts) * hl)
                        reg = img[yy + int(fs * 0.25):yy + int(fs * 1.3), x0:x1]
                        reg *= 0.5; reg += GOLD * 0.45 * a
                txt(img, s, x + int(24 * ts), yy, fs, IVORY * (0.9 if i < 7 else 0.55), a, F_INTER_L)
            yy += lh
    # retention counter
    a = win(t, T_ONEDAY - 0.2, T_TT + 1.5, 0.3, 0.8)
    if a > 0:
        v = 1 if t < T_NINETY else int(round(1 + 89 * ease_io((t - T_NINETY - 0.2) / 1.4)))
        x = int(W * (0.56 if not vert else 0.08)); y = int(H * (0.14 if not vert else 0.5))
        txt(img, "DATA_RETENTION_TIME_IN_DAYS", x, y, int(22 * ts), IVORY * 0.55, a, F_MONO)
        txt(img, f"{v}", x, y + int(30 * ts), int(150 * ts), (GOLD if v > 1 else ICE2), a, F_DISP, 8, 0.6)
        txt(img, "default 1   ·   enterprise: up to 90", x, y + int(220 * ts), int(20 * ts), IVORY * 0.45, a * sstep(T_NINETY, T_NINETY + 0.5, t), F_MONO)
    # time travel scrubber
    a = win(t, T_TT - 0.2, T_TRUST + 1.0, 0.4, 1.2)
    if a > 0:
        y = int(H * (0.72 if not vert else 0.6)); x0 = int(W * (0.18 if not vert else 0.1)); x1 = int(W * (0.82 if not vert else 0.82))
        cv2.line(img, (x0, y), (x1, y), (IVORY * 0.35 * a).tolist(), max(1, int(2 * ts)), cv2.LINE_AA)
        for i, (lab, f) in enumerate([("-90d", 0.0), ("-30d", 0.45), ("-1d", 0.85), ("now", 1.0)]):
            xx = int(lerp(x0, x1, f))
            cv2.line(img, (xx, y - int(10 * ts)), (xx, y + int(10 * ts)), (IVORY * 0.5 * a).tolist(), max(1, int(2 * ts)), cv2.LINE_AA)
            txt(img, lab, xx, y + int(30 * ts), int(18 * ts), IVORY * 0.5, a, F_MONO, anchor='c')
        ph = lerp(1.0, 0.86, ease_io((t - T_TT) / 3.0)) - 0.12 * win(t, T_BUILT, T_TRUST, 0.8, 1.5)
        px = int(lerp(x0, x1, ph))
        cv2.line(img, (px, y), (x1, y), (TEAL * a).tolist(), max(2, int(3 * ts)), cv2.LINE_AA)
        cv2.circle(img, (px, y), int(9 * ts), (WHITE * a).tolist(), -1, cv2.LINE_AA)
        txt(img, "TIME TRAVEL", x0, y - int(46 * ts), int(20 * ts), TEAL, a, F_MONOB, 3, 0.4)
        off = int((1 - ph) / 0.15 * 86400)
        txt(img, f"AT(OFFSET => -{off})", px, y - int(40 * ts), int(20 * ts), WHITE, a, F_MONO, anchor='c')
    # pricing
    a = win(t, T_ONLYU - 0.2, T_BUILD + 0.3, 0.4, 0.6)
    if a > 0:
        x = int(W * (0.62 if not vert else 0.1)); y = int(H * (0.55 if not vert else 0.56)); w = int(380 * ts); h = int(120 * ts)
        card(img, x, y, w, h, a, border=MAG * 0.7, tint=MAG)
        txt(img, "CREDITS CONSUMED", x + int(22 * ts), y + int(16 * ts), int(18 * ts), IVORY * 0.55, a, F_MONO)
        pv = 0.15 + 0.7 * sstep(T_ONLYU, T_PRICING + 1.5, t)
        bx = x + int(22 * ts); bw = w - int(44 * ts); by = y + int(54 * ts)
        cv2.rectangle(img, (bx, by), (bx + bw, by + int(10 * ts)), (IVORY * 0.15 * a).tolist(), -1)
        cv2.rectangle(img, (bx, by), (bx + int(bw * pv), by + int(10 * ts)), (MAG * a).tolist(), -1)
        txt(img, "status: worth it", x + int(22 * ts), y + int(76 * ts), int(20 * ts), MAG * 1.2, a * sstep(T_PRICING + 0.3, T_PRICING + 0.8, t), F_MONOB)

def overlay_outro(img, t, W, H, ts):
    a = win(t, T_OUTRO + 0.6, DUR + 1, 0.8, 0.1)
    if a <= 0: return
    vert = H > W
    fs = int(30 * ts)
    s1 = "snowsql> UNDROP TABLE production;"; s2 = "Table PRODUCTION successfully restored."
    w = int(max(text_w(s1, F_MONO, fs), text_w(s2, F_MONO, fs)) + 60 * ts)
    w = min(w, int(W * 0.92)); fs2 = fs if w < W * 0.9 else int(fs * 0.8)
    x = (W - w) // 2; y = int(H * (0.18 if not vert else 0.2))
    card(img, x, y, w, int(fs * 4.6), a * 0.9, border=TEAL * 0.6)
    txt(img, s1, x + int(30 * ts), y + int(fs * 0.9), fs2, IVORY, a, F_MONO, 3, 0.3)
    txt(img, s2, x + int(30 * ts), y + int(fs * 2.5), fs2, TEAL * 1.1, a * sstep(T_OUTRO + 1.4, T_OUTRO + 1.7, t), F_MONO, 3, 0.4)
    e = win(t, T_THERAPIST + 2.6, DUR + 1, 0.8, 0.1)
    if e > 0:
        img *= (1 - 0.55 * e)
        txt(img, "aditazzz", W / 2, H * 0.5, int(120 * ts), WHITE, e, F_DISPB, 12, 0.7, anchor='c')
        sp = sprite("U N D R O P", F_INTER_L, int(38 * ts))
        blit(img, sp, W / 2, H * 0.5 + 110 * ts, ICE2, e, anchor='c')

# ----------------------------------------------------------------------- lyrics
def lyric_layout(L, W, fs, maxw):
    words = L['words']; times = L['wt']
    items = [(w, tt) for w, tt in zip(words, times) if norm(w) != 'undrop']
    if not items: return None
    items[0] = (items[0][0].lstrip(',').strip(), items[0][1])
    sp = text_w(" ", F_INTER, fs)
    rows = [[]]; cw = 0
    for w, tt in items:
        ww = text_w(w, F_INTER, fs)
        if rows[-1] and cw + sp + ww > maxw: rows.append([]); cw = 0
        rows[-1].append((w, tt, ww)); cw += ww + (sp if rows[-1] else 0)
    return rows, sp

def _shadow(img, spr, x, y, op):
    a, g, pad = spr
    x = int(round(x - pad)); y = int(round(y - pad)); h, w = g.shape
    H, W = img.shape[:2]
    x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0: return
    img[y0:y1, x0:x1] *= (1 - np.clip(g[y0 - y:y1 - y, x0 - x:x1 - x] * 2.2, 0, 1)[..., None] * op)

def overlay_lyrics(img, t, W, H, ts):
    vert = H > W
    fs = int((52 if not vert else 48) * ts)
    maxw = W * (0.78 if not vert else 0.76)
    ybase = H * (0.835 if not vert else 0.70)
    flt = CORE.STATE['lyric_filter']
    for L in LINES:
        if not (L['s'] - 0.3 <= t <= L['e'] + 0.45): continue
        if flt is not None and not flt(L): continue
        lay = lyric_layout(L, W, fs, maxw)
        if lay is None: continue
        rows, sp = lay
        op_line = sstep(L['s'] - 0.3, L['s'], t) * (1 - sstep(L['e'] + 0.05, L['e'] + 0.45, t))
        lh = fs * 1.3
        y0 = ybase - (len(rows) - 1) * lh / 2 - lh * 0.3 * (1 - op_line)
        for ri_, row in enumerate(rows):
            tw = sum(r[2] for r in row) + sp * (len(row) - 1)
            x = (W - tw) / 2
            for w, tt, ww in row:
                k = sstep(tt - 0.14, tt + 0.06, t)
                act = math.exp(-max(0, t - tt) * 2.2) if t >= tt - 0.05 else 0
                col = IVORY * (0.88) * (1 - act) + ICE2 * act * 1.1
                op = op_line * (0.18 + 0.82 * k)
                dy = (1 - k) * 10 * ts
                shd = sprite(w, F_INTER, fs, 9)
                blit(img, shd, x, y0 + ri_ * lh + dy + 2 * ts, np.zeros(3, np.float32), 0.0, 0.0)
                _shadow(img, shd, x, y0 + ri_ * lh + dy + 2 * ts, 0.75 * op)
                blit(img, sprite(w, F_INTER, fs, 5), x, y0 + ri_ * lh + dy, col, op, 0.55 * act + 0.12, glow_color=ICE)
                x += ww + sp

def overlay_stamp(img, t, W, H, ts):
    s, i = last_stamp(t)
    if s is None: return
    x = t - s
    if x > 1.3: return
    nxt = STAMPS[i + 1] if i + 1 < len(STAMPS) else 1e9
    if t >= nxt: return
    vert = H > W
    size = int((235 if not vert else 190) * ts)
    sp = sprite("UNDROP", F_DISP, size, 14, track=int(10 * ts))
    sc = 1.0 + 0.32 * (1 - ease_out(x / 0.22)) + 0.04 * x
    op = (1 - sstep(0.55, 1.3, x)) * sstep(0, 0.04, x)
    if T_BRIDGE < t < T_BUILD: op = 0
    cy = H * (0.45 if not vert else 0.42)
    dx = (16 * (1 - ease_out(x / 0.4)) + 3) * ts
    a, g, pad = sp
    # additive chromatic copies
    for off, col in ((-dx, np.array([1.0, 0.15, 0.35], np.float32)), (dx, np.array([0.1, 0.8, 1.0], np.float32))):
        aa = cv2.resize(a, None, fx=sc, fy=sc)
        h, w = aa.shape
        xx = int(W / 2 - w / 2 + off); yy = int(cy - h / 2)
        x0, y0, x1, y1 = max(0, xx), max(0, yy), min(W, xx + w), min(H, yy + h)
        if x1 > x0 and y1 > y0:
            img[y0:y1, x0:x1] += aa[y0 - yy:y1 - yy, x0 - xx:x1 - xx, None] * col * op * 0.55
    blit(img, sp, W / 2, cy, WHITE, op, 1.1 * op, glow_color=ICE, anchor='c', scale=sc)
    # small sql caption
    txt(img, "UNDROP TABLE production;", W / 2, cy + size * 0.62 * sc, int(22 * ts), ICE2, op * 0.8, F_MONO, anchor='c')

# ======================================================================= post
class Post:
    def __init__(s, W, H):
        r = np.random.default_rng(9)
        s.grain = [r.normal(0, 1, (H // 2, W // 2)).astype(np.float32) for _ in range(6)]
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        d = np.hypot((xx - W / 2) / (W / 2), (yy - H / 2) / (H / 2))
        s.vig = np.clip(1 - 0.38 * d ** 2.2, 0, 1)[..., None].astype(np.float32)
        s.yramp = (yy[:, :1] / H).astype(np.float32)
        s.bot = np.clip((s.yramp - 0.62) / 0.38, 0, 1)[..., None] ** 1.5
        s.scan = (0.85 + 0.15 * (np.arange(H) % 3 != 0)).astype(np.float32)[:, None, None]

def chroma(img, amt):
    if amt < 0.0004: return img
    H, W = img.shape[:2]
    out = img.copy()
    for c, s in ((0, 1 + amt), (2, 1 - amt)):
        M = np.array([[s, 0, W / 2 * (1 - s)], [0, s, H / 2 * (1 - s)]], np.float32)
        out[..., c] = cv2.warpAffine(img[..., c], M, (W, H), borderMode=cv2.BORDER_REFLECT)
    return out

def glitch(img, amt, fi):
    if amt < 0.05: return img
    H, W = img.shape[:2]
    r = np.random.default_rng(fi * 7 + 3)
    nb = int(3 + 10 * amt)
    for _ in range(nb):
        y = r.integers(0, H - 10); h = int(r.integers(4, int(10 + 80 * amt)))
        dx = int(r.normal(0, 60 * amt))
        img[y:y + h] = np.roll(img[y:y + h], dx, axis=1)
        if r.random() < 0.4: img[y:y + h, :, r.integers(0, 3)] *= 1.6
    return img

# ======================================================================= frame
_POST = {}
def render_frame(t, W=1920, H=1080, fi=0):
    vert = H > W
    SW, SH = (W * 2 // 3) // 2 * 2, (H * 2 // 3) // 2 * 2
    sc = W / SW
    ts = min(W, H) / 1080
    if (W, H) not in _POST: _POST[(W, H)] = Post(W, H)
    post = _POST[(W, H)]
    top, bot, aur, expo = palette(t)
    yr = np.linspace(0, 1, SH, dtype=np.float32)[:, None, None]
    bg = np.broadcast_to(top * (1 - yr) + bot * yr, (SH, SW, 3)).copy()
    A = aurora(t, SW, SH, aur * (1.2 if section(t) == "FINAL" else 1.0), 0.0 if t < T_CH2 else 0.6)
    if A is not None: bg += A * 0.55
    cam = camera(t)
    if vert: cam.fov = 0.78
    layer = np.zeros((SH, SW, 3), np.float32)
    # dust
    P = dust(t); u, v, z = project(P, cam, SW, SH)
    w = np.clip(3.0 / np.maximum(z, 0.5), 0, 1.2) * (z > 0.5) * DSZ * 0.55
    dcol = IVORY * 0.7 + ICE * 0.3
    if T_DROP < t < T_REMEMBER + 3: dcol = dcol * (1 - win(t, T_DROP, T_REMEMBER, 0.1, 3)) + RED * win(t, T_DROP, T_REMEMBER, 0.1, 3)
    if section(t) in ("BUILD", "FINAL"): w = w * 1.6
    splat(layer, u, v, w.astype(np.float32), dcol.astype(np.float32))
    fill = np.zeros((SH, SW, 3), np.uint8); edge = np.zeros((SH, SW, 3), np.uint8)
    lv = light_level(t)
    Pc, Rm, col, al = cells(t)
    al = al * lv
    if section(t) == "V2" and T_WARE - 0.5 < t < T_SORRY + 0.5:
        al = al * lerp(1, 0.4, win(t, T_WARE, T_SORRY, 1, 1))
    draw_cells(fill, edge, Pc, Rm, col, al, cam, SW, SH)
    labels = draw_clones(t, cam, layer, SW, SH) if T_V2 - 1 < t < T_WARE + 1.5 else []
    draw_towers(t, cam, fill, edge, layer, SW, SH)
    draw_ghosts(t, cam, edge, SW, SH)
    frost_layer(t, cam, layer, SW, SH)
    shockwaves(t, cam, edge, SW, SH)
    layer += fill.astype(np.float32) * (0.55 / 255) + edge.astype(np.float32) * (1.25 / 255)
    # bloom
    small = cv2.resize(layer, (SW // 2, SH // 2), interpolation=cv2.INTER_AREA)
    b1 = cv2.GaussianBlur(small, (0, 0), 3)
    b2 = cv2.GaussianBlur(cv2.resize(small, (SW // 8, SH // 8), interpolation=cv2.INTER_AREA), (0, 0), 3)
    glow = cv2.resize(b1, (SW, SH)) * 0.75 + cv2.resize(b2, (SW, SH)) * 1.3
    img = bg + layer + glow * bloom_amt(t)
    ra = rays_amt(t)
    if ra > 0.02:
        q = cv2.resize(layer + glow * 0.3, (SW // 4, SH // 4), interpolation=cv2.INTER_AREA)
        cu, cv_, cz = project(np.zeros((1, 3), np.float32), cam, SW // 4, SH // 4)
        cx, cy = float(cu[0]), float(cv_[0])
        acc = np.zeros_like(q); wsum = 0
        for k in range(12):
            s_ = 1 + 0.045 * k
            M = np.array([[s_, 0, cx * (1 - s_)], [0, s_, cy * (1 - s_)]], np.float32)
            acc += cv2.warpAffine(q, M, (SW // 4, SH // 4)) * (0.86 ** k); wsum += 0.86 ** k
        img += cv2.resize(cv2.GaussianBlur(acc / wsum, (0, 0), 2), (SW, SH)) * ra * 1.4
    sa = streak_amt(t)
    if sa > 0.02:
        q = cv2.resize(layer, (SW // 4, SH // 4), interpolation=cv2.INTER_AREA)
        q = np.maximum(q - 0.55, 0)
        st_ = cv2.GaussianBlur(q, (0, 0), sigmaX=SW / 16, sigmaY=0.6)
        st_ = st_.mean(2, keepdims=True) * np.array([0.35, 0.65, 1.0], np.float32)
        img += cv2.resize(st_, (SW, SH)) * sa * 6.0
    # tone map
    img = 1 - np.exp(-img * 1.35 * expo)
    img = cv2.resize(img, (W, H), interpolation=cv2.INTER_LINEAR)
    # red alarm scanlines
    ra2 = win(t, T_DROP, T_REMEMBER, 0.05, 2.5)
    if ra2 > 0: img *= (1 - ra2 * (1 - post.scan))
    # overlays (skipped for clean thumbnail frames)
    if not CORE.STATE['clean']:
        img *= (1 - 0.55 * post.bot)
        overlay_terminal(img, t, W, H, ts)
        overlay_clock(img, t, W, H, ts)
        overlay_toasts(img, t, W, H, ts)
        overlay_clones(img, t, W, H, ts, labels, sc)
        overlay_prod_label(img, t, W, H, ts, cam, sc)
        overlay_warehouse(img, t, W, H, ts)
        overlay_bubbles(img, t, W, H, ts)
        overlay_pre2(img, t, W, H, ts)
        overlay_bridge(img, t, W, H, ts)
        overlay_outro(img, t, W, H, ts)
        overlay_stamp(img, t, W, H, ts)
        overlay_lyrics(img, t, W, H, ts)
    # flash
    f, fc = flash(t)
    if f > 0: img = img + fc * f * (0.6 + 0.4 * post.vig)
    g = glitch_amt(t)
    img = chroma(img, 0.0018 + 0.012 * g + 0.004 * min(1, f))
    img = glitch(img, g, fi)
    img *= post.vig
    gr = cv2.resize(post.grain[fi % 6], (W, H), interpolation=cv2.INTER_NEAREST)
    img += gr[..., None] * 0.018
    # intro / outro fades
    img *= sstep(0.0, 1.2, t) * (1 - sstep(DUR - 1.2, DUR - 0.1, t))
    return (np.clip(img, 0, 1) * 255).astype(np.uint8)

if __name__ == "__main__":
    W, H = int(sys.argv[1]), int(sys.argv[2]); f0, f1 = int(sys.argv[3]), int(sys.argv[4]); out = sys.argv[5]
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    import time
    st = time.time()
    for fi in range(f0, f1):
        p.stdin.write(render_frame(fi / FPS, W, H, fi).tobytes())
        if fi % 150 == 0: print(f"{out} {fi}/{f1} {time.time() - st:.0f}s", flush=True)
    p.stdin.close(); p.wait()
    print("done", out, time.time() - st)
