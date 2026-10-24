"""The Drive — the inside of the car, drawn in screen space over the world: the dashboard with its cluster (speed,
engine temperature, a PROD warning light, the clock), the phone in its mount, the coffee, the laptop on the passenger
seat (16:9), the wheel and hands, the pillars and the rear-view mirror, water rising inside the car in the choruses,
and the ROLLBACK ring hanging off the windshield."""
import math
import numpy as np, cv2
from studio import core as C
from studio import kit as K
from studio.core import hexc, sstep, clamp, lerp, sprite, blit, text_w, shadow, F_DISP, F_DISPB, F_MONO, F_MONOB, F_INTER
from dof_sprites import lifering

INK = hexc('121218'); DASH = hexc('1f1d26'); DASH2 = hexc('2a2730'); CREAM = hexc('f4efe4')
AMBER = hexc('ffb547'); REDL = hexc('ff3b3b'); GREENL = hexc('39e07a'); CYAN = hexc('5fd8ff')
GLASS = hexc('cfe6ef')


def lay(W, H):
    vert = H > W; ts = min(W, H) / 1080
    if not vert:
        L = dict(vert=False, ts=ts, yD=H * 0.705, wheel=(W * 0.33, H * 1.21, H * 0.42), cluster=(W * 0.33, H * 0.805),
                 phone=(W * 0.585, H * 0.79, W * 0.085, H * 0.165), coffee=(W * 0.68, H * 0.93), laptop=(W * 0.84, H * 0.87),
                 mirror=(W * 0.5, H * 0.075, W * 0.19, H * 0.075), pillar=0.06)
    else:
        L = dict(vert=True, ts=ts, yD=H * 0.745, wheel=(W * 0.40, H * 1.11, W * 0.40), cluster=(W * 0.40, H * 0.81),
                 phone=(W * 0.76, H * 0.80, W * 0.17, H * 0.14), coffee=(W * 0.58, H * 0.95), laptop=None,
                 mirror=None, pillar=0.03)
    return L


def _fill_poly(img, pts, col, op=1.0):
    K.fill_poly(img, np.array(pts, np.int32), col, op)


def _arc_pts(cx, cy, r, a0, a1, n=40):
    return [(cx + math.cos(a) * r, cy + math.sin(a) * r) for a in np.linspace(a0, a1, n)]


def dashboard(img, t, W, H, L, S):
    """S: speed (0..1 of the dial), temp (0..1), red (0..1 dashboard red), clock (str), prod_warn (0..1), tod light."""
    ts = L['ts']; yD = L['yD']; vert = L['vert']
    amb = S.get('amb', 1.0); red = S.get('red', 0.0)
    # dash body: a wide curved shape
    xs = np.linspace(0, W, 24)
    top = [(x, yD + math.sin((x / W) * math.pi) * -H * 0.025 + (abs(x / W - 0.5) * H * 0.02)) for x in xs]
    pts = top + [(W, H), (0, H)]
    _fill_poly(img, pts, DASH * amb)
    # top ridge highlight
    ridge = [(x, y + 2) for x, y in top] + [(x, y + H * 0.018) for x, y in reversed(top)]
    _fill_poly(img, ridge, DASH2 * amb * 1.15)
    # a strip of windshield reflection just above the dash
    refl = [(x, y - H * 0.03) for x, y in top] + [(x, y) for x, y in reversed(top)]
    _fill_poly(img, refl, GLASS, 0.05)
    cluster(img, t, W, H, L, S)
    phone(img, t, W, H, L, S)
    coffee(img, t, W, H, L, S)
    if L['laptop']: laptop(img, t, W, H, L, S)
    wheel(img, t, W, H, L, S)


def cluster(img, t, W, H, L, S):
    ts = L['ts']; cx, cy = L['cluster']; vert = L['vert']
    red = S.get('red', 0.0); amb = S.get('amb', 1.0)
    w, h = (W * 0.30, H * 0.17) if not vert else (W * 0.62, H * 0.13)
    lit = AMBER * (1 - red) + REDL * red
    K.panel(img, cx - w / 2, cy - h / 2, w, h, hexc('15141a'), 1.0, r=int(h * 0.3), border=hexc('3a3742') * amb, shadow_op=0.3)
    # glow of the backlight
    G = _grid(W, H)
    g = np.exp(-(((G['xx'] - cx) / (w * 0.55)) ** 2 + ((G['yy'] - cy) / (h * 0.5)) ** 2))
    img += g[..., None] * lit * (0.08 + 0.18 * red)
    # speedometer (left dial)
    dx = cx - w * 0.37; r = h * 0.34          # dials far enough apart that a 5-character clock never touches them
    _dial(img, dx, cy + h * 0.06, r, S.get('speed', 0.0), lit, ts, ticks=9, label='MPH')
    # temperature (right dial)
    tx = cx + w * 0.37
    _dial(img, tx, cy + h * 0.06, r * 0.82, S.get('temp', 0.3), lit, ts, ticks=5, label='C   H', hot=S.get('temp', 0.3) > 0.85)
    # clock
    fs = int(h * 0.36)
    while text_w('10:00', F_MONOB, fs) > (w * 0.37 - r * 1.05) * 2 * 0.92: fs -= 2
    clk = S.get('clock', '4:59')
    blit(img, sprite(clk, F_MONOB, fs), cx, cy - h * 0.02, lit * 1.05, 1.0, anchor='c')
    blit(img, sprite(S.get('ampm', 'PM'), F_MONO, int(fs * 0.4)), cx, cy + h * 0.27, lit * 0.8, 1.0, anchor='c')
    blit(img, sprite(S.get('day', 'FRI'), F_MONO, int(fs * 0.4)), cx, cy - h * 0.36, lit * 0.8, 1.0, anchor='c')
    # PROD warning light
    pw = S.get('prod_warn', 0.0)
    if pw > 0.01:
        bx, by = cx, cy + h * 0.38 if False else cy + h * 0.395
        k = 0.5 + 0.5 * math.sin(t * 9)
        K.panel(img, cx - w * 0.11, cy + h * 0.33, w * 0.22, h * 0.13, REDL * (0.6 + 0.4 * k), pw, r=int(h * 0.05), shadow_op=0)
        blit(img, sprite('⚠ PROD', F_DISPB, int(h * 0.1)), cx, cy + h * 0.395, INK, pw, anchor='c')


def _dial(img, cx, cy, r, v, lit, ts, ticks=9, label='', hot=False):
    a0, a1 = math.radians(150), math.radians(390)
    pts = np.array(_arc_pts(cx, cy, r, a0, a1), np.int32)
    cv2.polylines(img, [pts], False, (lit * 0.9).tolist(), max(2, int(3 * ts)), cv2.LINE_AA)
    for k in range(ticks):
        a = a0 + (a1 - a0) * k / (ticks - 1)
        p0 = (int(cx + math.cos(a) * r * 0.84), int(cy + math.sin(a) * r * 0.84)); p1 = (int(cx + math.cos(a) * r), int(cy + math.sin(a) * r))
        cv2.line(img, p0, p1, (lit * 0.9).tolist(), max(2, int(2.5 * ts)), cv2.LINE_AA)
    a = a0 + (a1 - a0) * clamp(v)
    col = (REDL if hot else CREAM)
    cv2.line(img, (int(cx), int(cy)), (int(cx + math.cos(a) * r * 0.9), int(cy + math.sin(a) * r * 0.9)), col.tolist(), max(3, int(4 * ts)), cv2.LINE_AA)
    cv2.circle(img, (int(cx), int(cy)), max(3, int(r * 0.09)), (lit * 0.8).tolist(), -1, cv2.LINE_AA)
    if label: blit(img, sprite(label, F_MONO, max(14, int(r * 0.26))), cx, cy + r * 0.55, lit * 0.75, 1.0, anchor='c')


_GR = {}
def _grid(W, H):
    if (W, H) not in _GR:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); _GR[(W, H)] = dict(xx=xx, yy=yy)
    return _GR[(W, H)]


def phone(img, t, W, H, L, S):
    ts = L['ts']; x, y, w, h = L['phone']; amb = S.get('amb', 1.0)
    # mount arm
    K.panel(img, x - w * 0.1, y + h * 0.45, w * 0.2, h * 0.35, hexc('26242c') * amb, 1.0, r=int(w * 0.08), shadow_op=0.3)
    K.panel(img, x - w / 2, y - h / 2, w, h, hexc('0c0c10'), 1.0, r=int(w * 0.16), border=hexc('3c3a44') * amb, shadow_op=0.5)
    sx, sy, sw, sh = x - w * 0.43, y - h * 0.46, w * 0.86, h * 0.92
    scr = S.get('phone', 'dark')
    buzz = S.get('buzz', 0.0)
    if buzz > 0.01:   # the phone rattles in its mount
        dx = math.sin(t * 70) * w * 0.035 * buzz; sx += dx
    if scr == 'dark':
        K.panel(img, sx, sy, sw, sh, hexc('101016'), 1.0, r=int(w * 0.12), shadow_op=0)
        blit(img, sprite(S.get('clock', '4:59'), F_INTER, int(sh * 0.12)), x, y - h * 0.3, CREAM * 0.35, 1.0, anchor='c')
    elif scr == 'pr':
        K.panel(img, sx, sy, sw, sh, hexc('f2efe8'), 1.0, r=int(w * 0.12), shadow_op=0)
        fs = max(12, int(sh * 0.075))
        blit(img, sprite('PR #459', F_MONOB, fs), x, sy + sh * 0.12, INK, 1.0, anchor='c')
        blit(img, sprite('one little change', F_INTER, int(fs * 0.9)), x, sy + sh * 0.22, INK * 0.7, 1.0, anchor='c')
        blit(img, sprite('✓ CI  ✓ lint  0 reviews', F_INTER, int(fs * 0.78)), x, sy + sh * 0.32, hexc('2a8a4a'), 1.0, anchor='c')
        press = S.get('press', 0.0); prog = S.get('deploy', 0.0)
        bw, bh = sw * 0.84, sh * 0.2; by = sy + sh * 0.44
        K.panel(img, x - bw / 2, by, bw, bh, hexc('3ddc84') * (1 - 0.25 * press), 1.0, r=int(bh * 0.3), shadow_op=0.4 * (1 - press))
        if prog <= 0: blit(img, sprite('SHIP IT', F_DISP, int(bh * 0.5)), x, by + bh / 2, INK, 1.0, anchor='c')
        else:
            K.panel(img, x - bw * 0.44, by + bh * 0.6, bw * 0.88, bh * 0.18, INK * 0.5, 1.0, r=4, shadow_op=0)
            K.panel(img, x - bw * 0.44, by + bh * 0.6, bw * 0.88 * clamp(prog), bh * 0.18, CREAM, 1.0, r=4, shadow_op=0)
            lab = 'deploying…' if prog < 1 else '✓ deployed'
            blit(img, sprite(lab, F_DISPB, int(bh * 0.3)), x, by + bh * 0.3, INK, 1.0, anchor='c')
        blit(img, sprite('no ticket · no test', F_MONO, int(fs * 0.7)), x, sy + sh * 0.76, INK * 0.5, 1.0, anchor='c')
        blit(img, sprite('no second pair of eyes', F_MONO, int(fs * 0.7)), x, sy + sh * 0.84, INK * 0.5, 1.0, anchor='c')
    elif scr == 'alerts':
        K.panel(img, sx, sy, sw, sh, hexc('101016'), 1.0, r=int(w * 0.12), shadow_op=0)
        n = int(S.get('n_alerts', 1)); fs = max(12, int(sh * 0.065))
        for i in range(min(n, 6)):
            yy = sy + sh * (0.1 + i * 0.145)
            K.panel(img, sx + sw * 0.06, yy, sw * 0.88, sh * 0.12, hexc('2a2230'), 1.0, r=int(sh * 0.03), shadow_op=0)
            cv2.circle(img, (int(sx + sw * 0.16), int(yy + sh * 0.06)), max(3, int(sh * 0.028)), REDL.tolist(), -1, cv2.LINE_AA)
            lab = ['PagerDuty', 'prod: 5xx ↑', '#incidents', 'VP', 'checkout', 'on-call'][i % 6]
            blit(img, sprite(lab, F_INTER, fs), sx + sw * 0.26, yy + sh * 0.025, CREAM, 1.0)
        badge = str(n) if n < 100 else '99+'
        K.panel(img, sx + sw * 0.66, sy + sh * 0.02, sw * 0.3, sh * 0.075, REDL, 1.0, r=int(sh * 0.035), shadow_op=0)
        blit(img, sprite(badge, F_DISPB, fs), sx + sw * 0.81, sy + sh * 0.057, CREAM, 1.0, anchor='c')
    elif scr == 'onebar':
        K.panel(img, sx, sy, sw, sh, hexc('101016'), 1.0, r=int(w * 0.12), shadow_op=0)
        fs = max(12, int(sh * 0.07))
        for i in range(4):
            bx = sx + sw * (0.3 + i * 0.11); bh = sh * (0.03 + i * 0.02)
            K.panel(img, bx, sy + sh * 0.22 - bh, sw * 0.08, bh, CREAM if i == 0 else hexc('3a3a44'), 1.0, r=2, shadow_op=0)
        blit(img, sprite('1 bar', F_MONOB, fs), x, sy + sh * 0.32, CREAM, 1.0, anchor='c')
        blit(img, sprite('git push', F_MONO, int(fs * 0.9)), x, sy + sh * 0.5, CREAM * 0.8, 1.0, anchor='c')
        prog = S.get('push', 0.0)
        K.panel(img, sx + sw * 0.12, sy + sh * 0.6, sw * 0.76, sh * 0.05, hexc('2a2a34'), 1.0, r=3, shadow_op=0)
        K.panel(img, sx + sw * 0.12, sy + sh * 0.6, sw * 0.76 * clamp(prog), sh * 0.05, GREENL, 1.0, r=3, shadow_op=0)
        blit(img, sprite(f'{int(clamp(prog) * 100)}%', F_MONO, int(fs * 0.9)), x, sy + sh * 0.74, CREAM * 0.8, 1.0, anchor='c')
    elif scr == 'question':
        K.panel(img, sx, sy, sw, sh, hexc('101016'), 1.0, r=int(w * 0.12), shadow_op=0)
        fs = max(12, int(sh * 0.07))
        K.panel(img, sx + sw * 0.06, sy + sh * 0.3, sw * 0.88, sh * 0.3, hexc('2f6bff'), 1.0, r=int(sh * 0.05), shadow_op=0)
        blit(img, sprite('quick question', F_INTER, fs), x, sy + sh * 0.4, CREAM, 1.0, anchor='c')
        blit(img, sprite('for you…', F_INTER, fs), x, sy + sh * 0.5, CREAM, 1.0, anchor='c')
        blit(img, sprite('Fri 4:59 PM', F_MONO, int(fs * 0.8)), x, sy + sh * 0.72, CREAM * 0.5, 1.0, anchor='c')
    elif scr == 'green':
        K.panel(img, sx, sy, sw, sh, hexc('101016'), 1.0, r=int(w * 0.12), shadow_op=0)
        fs = max(12, int(sh * 0.07))
        for i, lab in enumerate(('✓ build', '✓ deploy', '✓ checkout', '✓ prod')):
            blit(img, sprite(lab, F_MONOB, fs), x, sy + sh * (0.2 + i * 0.16), GREENL, 1.0, anchor='c')


def coffee(img, t, W, H, L, S):
    ts = L['ts']; x, y = L['coffee']; amb = S.get('amb', 1.0)
    w, h = W * (0.045 if not L['vert'] else 0.09), H * (0.075 if not L['vert'] else 0.05)
    K.panel(img, x - w / 2, y - h, w, h, hexc('e9e3d6') * amb, 1.0, r=int(w * 0.15), shadow_op=0.4)
    K.panel(img, x - w * 0.46, y - h * 0.62, w * 0.92, h * 0.14, hexc('c9a26b') * amb, 1.0, r=3, shadow_op=0)
    steam = S.get('steam', 1.0)
    if steam > 0.01:
        for k in range(3):
            ph = t * 1.6 + k * 2.1
            for s in np.linspace(0, 1, 7):
                px = x + (k - 1) * w * 0.22 + math.sin(ph + s * 4) * w * 0.12
                py = y - h - s * h * 0.9
                a = steam * (1 - s) * 0.35
                soft_dot(img, px, py, max(2, int(w * 0.07 * (1 - s * 0.4))), CREAM, a)


def soft_dot(img, cx, cy, r, col, op):
    """A translucent disc blended locally (no full-frame copy)."""
    if op <= 0.01: return
    H, W = img.shape[:2]; x0, y0 = int(cx - r - 1), int(cy - r - 1); n = 2 * r + 3
    X0, Y0, X1, Y1 = max(0, x0), max(0, y0), min(W, x0 + n), min(H, y0 + n)
    if X1 <= X0 or Y1 <= Y0: return
    yy, xx = np.mgrid[Y0:Y1, X0:X1].astype(np.float32)
    m = np.clip(r + 0.5 - np.hypot(xx - cx, yy - cy), 0, 1)[..., None] * op
    reg = img[Y0:Y1, X0:X1]; reg *= (1 - m); reg += m * col


def laptop(img, t, W, H, L, S):
    x, y = L['laptop']; amb = S.get('amb', 1.0); lid = S.get('lid', 0.5)
    w, h = W * 0.16, H * 0.02
    K.panel(img, x - w / 2, y - h, w, h, hexc('cfcbc4') * amb, 1.0, r=int(h * 0.4), shadow_op=0.4)
    lh = H * 0.11 * lid
    pts = [(x - w * 0.48, y - h), (x + w * 0.48, y - h), (x + w * 0.44, y - h - lh), (x - w * 0.44, y - h - lh)]
    _fill_poly(img, pts, hexc('3a3842') * amb)
    if lid > 0.3:
        k = sstep(0.3, 0.6, lid)
        pts2 = [(x - w * 0.42, y - h - lh * 0.06), (x + w * 0.42, y - h - lh * 0.06), (x + w * 0.39, y - h - lh * 0.94), (x - w * 0.39, y - h - lh * 0.94)]
        _fill_poly(img, pts2, hexc('f2efe8') * k * S.get('lap_glow', 1.0) + hexc('1b1a22') * (1 - k))


def wheel(img, t, W, H, L, S):
    cx, cy, r = L['wheel']; ts = L['ts']; amb = S.get('amb', 1.0)
    steer = S.get('steer', 0.0) * 0.5   # radians
    col = hexc('17161c') * amb; col2 = hexc('2b2a33') * amb
    th = max(10, int(r * 0.08))
    cv2.ellipse(img, (int(cx), int(cy)), (int(r), int(r * 0.78)), math.degrees(steer), 190, 350, col.tolist(), th * 2, cv2.LINE_AA)
    cv2.ellipse(img, (int(cx), int(cy)), (int(r), int(r * 0.78)), math.degrees(steer), 190, 350, col2.tolist(), th // 2, cv2.LINE_AA)
    # spokes
    for a in (math.radians(205), math.radians(335)):
        aa = a + steer
        p0 = (int(cx + math.cos(aa) * r * 0.25), int(cy + math.sin(aa) * r * 0.78 * 0.25)); p1 = (int(cx + math.cos(aa) * r * 0.95), int(cy + math.sin(aa) * r * 0.78 * 0.95))
        cv2.line(img, p0, p1, col.tolist(), th, cv2.LINE_AA)
    # hands (flat, no detail)
    hand = hexc('c99a7a') * amb; hands = S.get('hands', 1.0)
    if hands > 0.01:
        for a in (math.radians(212), math.radians(328)):
            aa = a + steer
            hx, hy = cx + math.cos(aa) * r * 1.0, cy + math.sin(aa) * r * 0.78
            K.panel(img, hx - r * 0.09, hy - r * 0.08, r * 0.18, r * 0.16, hand, hands, r=int(r * 0.06), shadow_op=0.3)
            for k in range(4):
                K.panel(img, hx - r * 0.085 + k * r * 0.045, hy - r * 0.13, r * 0.04, r * 0.1, hand * 0.95, hands, r=int(r * 0.015), shadow_op=0)


def frame_glass(img, t, W, H, L, S):
    """Pillars at the edges, the mirror (16:9), a faint tint band at the top of the windshield."""
    ts = L['ts']; amb = S.get('amb', 1.0); p = L['pillar']
    if p > 0:
        _fill_poly(img, [(0, 0), (W * p, 0), (W * p * 0.5, L['yD']), (0, L['yD'])], hexc('14131a') * amb)
        _fill_poly(img, [(W, 0), (W * (1 - p), 0), (W * (1 - p * 0.5), L['yD']), (W, L['yD'])], hexc('14131a') * amb)
    # top tint band
    yy = _grid(W, H)['yy']
    band = np.clip(1 - yy / (H * 0.09), 0, 1)[..., None] ** 1.5
    img *= (1 - band * 0.45)
    if L['mirror']:
        mx, my, mw, mh = L['mirror']
        K.panel(img, mx - mw / 2, my - mh / 2, mw, mh, hexc('0e0e14'), 1.0, r=int(mh * 0.3), border=hexc('3a3842') * amb, shadow_op=0.5)
        K.panel(img, mx - mw * 0.47, my - mh * 0.4, mw * 0.94, mh * 0.8, S.get('mirror_col', hexc('3b4a62')), 1.0, r=int(mh * 0.2), shadow_op=0)
        glow = S.get('mirror_glow', 0.0)
        if glow > 0.01:
            K.panel(img, mx - mw * 0.47, my - mh * 0.4, mw * 0.94, mh * 0.8, REDL, glow * (0.5 + 0.5 * math.sin(t * 6)) * 0.7, r=int(mh * 0.2), shadow_op=0)
        txt = S.get('mirror_text')
        if txt:
            blit(img, sprite(txt, F_MONOB, int(mh * 0.42)), mx, my, CREAM, S.get('mirror_text_op', 1.0), anchor='c')
        K.panel(img, mx - mw * 0.04, 0, mw * 0.08, my - mh / 2, hexc('14131a') * amb, 1.0, r=2, shadow_op=0)


def interior_water(img, t, W, H, L, level, tod_col):
    """Water inside the car: a translucent fill from the bottom up to `level` (fraction of H), wavy top edge."""
    if level <= 0.003: return
    G = _grid(W, H); xx, yy = G['xx'], G['yy']
    ytop = H * (1 - level) + np.sin(xx * 0.012 + t * 2.6) * H * 0.012 + np.sin(xx * 0.031 - t * 3.7) * H * 0.006
    m = np.clip((yy - ytop) / 3.0, 0, 1)
    depth = np.clip((yy - ytop) / (H * 0.5), 0, 1)
    col = tod_col * 0.75 + hexc('1f6f8a') * 0.25
    a = m * (0.45 + 0.35 * depth)
    img *= (1 - a[..., None]); img += a[..., None] * col
    crest = np.clip(1 - np.abs(yy - ytop) / (H * 0.004), 0, 1)
    img += crest[..., None] * hexc('dff6ff') * 0.6
    # bubbles
    r = np.random.default_rng(4)
    for k in range(18):
        bx = (r.random() * 1.2 - 0.1) * W; ph = r.random() * 9
        by = H - ((t * (0.12 + r.random() * 0.1) + ph) % 1.0) * H * level
        if by > ytop[min(H - 1, max(0, int(by))) if False else 0, int(clamp(bx / W) * (W - 1))]:
            cv2.circle(img, (int(bx + math.sin(t * 3 + ph) * 8), int(by)), max(2, int(H * 0.004 * (1 + r.random()))), (hexc('dff6ff') * 0.8).tolist(), max(1, int(H * 0.0015)), cv2.LINE_AA)


def ring(img, t, W, H, L, S):
    """The ROLLBACK life ring: thrown from ahead, lands on the windshield and hangs on its rope."""
    st = S.get('ring')
    if not st: return
    k, hang, label = st['k'], st['hang'], st.get('label', 'ROLLBACK')
    rg = lifering(label)
    vert = L['vert']
    # flight: from a point ahead on the road to the hang point
    x0, y0 = W * 0.5, H * (0.44 if not vert else 0.40)
    x1, y1 = (W * 0.70, H * 0.47) if not vert else (W * 0.62, H * 0.50)
    e = C.ease_out(k)
    x = lerp(x0, x1, e); y = lerp(y0, y1, e) - math.sin(k * math.pi) * H * 0.12
    s = lerp(0.02, (0.40 if not vert else 0.52), e ** 0.8) * min(W, H) / 1080 * (520 / 520)
    size = s * 520 * (1.0 + 0.04 * math.sin(t * 5) * hang)
    sw = hang * math.sin(t * 2.2) * 0.08
    # rope to the top right corner
    cv2.line(img, (int(x), int(y)), (int(W * 1.02), int(-H * 0.02)), (hexc('d8c29a') * 0.9).tolist(), max(3, int(min(W, H) * 0.006)), cv2.LINE_AA)
    from dof_world import alpha_blit
    rgba = rg
    M = cv2.getRotationMatrix2D((rgba.shape[1] / 2, rgba.shape[0] / 2), math.degrees(sw) + (1 - k) * 540, 1.0)
    rot = cv2.warpAffine(rgba, M, (rgba.shape[1], rgba.shape[0]))
    alpha_blit(img, rot, x, y, size / rgba.shape[1], anchor='c', op=S['ring'].get('op', 1.0))


def hud_word(img, t, W, H, text, k, y=0.3, size=0.16, col=CREAM, glow=None, mono=True, x=0.5):
    """Big kinetic type on the windshield (4:59, the chorus hits)."""
    if k <= 0.01: return
    ts = min(W, H) / 1080
    fs = int(min(W, H) * size)
    while text_w(text, F_DISP if not mono else F_MONOB, fs) > W * 0.9: fs -= 6
    sp = sprite(text, F_DISP if not mono else F_MONOB, fs, 14)
    sc = 1 + 0.25 * (1 - C.ease_out(k / 0.25)) if k < 0.25 else 1.0
    op = sstep(0, 0.05, k)
    shadow(img, sp, W * x - sp[0].shape[1] / 2 + sp[2] + 4 * ts, H * y - sp[0].shape[0] / 2 + sp[2] + 6 * ts, 0.8 * op)
    blit(img, sp, W * x, H * y, col, op, 0.5 * op, glow_color=glow if glow is not None else col, anchor='c', scale=sc)
