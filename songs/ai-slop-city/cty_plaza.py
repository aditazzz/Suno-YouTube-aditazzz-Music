"""Compose the plaza set for one frame: sky, ground, towers, props, sun shadows, glow. Her and her shadow are added by
the caller through hooks so the same set serves every shot."""
import math, time
import numpy as np, cv2
from cty_eng import F32, AA, hexc, c8, mix, clamp, sstep, Cam, to_f, to_8, glow as wide_glow, bloom, rays, fill, screen_poly
from cty_sky import sun, palette, render_sky, blackout_palette, neon_palette, warm_palette, drain_palette
import cty_city as CC
import cty_her as HER
import cty_shadow as SHD

HER_LZ = -0.42          # her plane along the bench (bench-local), near the camera end
HER_ID = 950


def her_origin():
    return CC.bw(0.0, HER.SEAT, HER_LZ)


def her_light(ctx, S):
    """Key/ambient/direction for her from the scene light (sun by day, the bench lamp at night) + rim."""
    L = ctx.L
    amb = ctx.lightk(0.0)
    if ctx.sunk > 0.05:
        d2 = (float(np.dot(L, CC.BF)), float(np.dot(L, CC.BU)))
        key = ctx.lightk(0.85)
    else:
        lx, lz = CC.LAMPS[0]
        lp = np.array([lx, 4.5, lz]) - her_origin()
        d2 = (float(np.dot(lp, CC.BF)), float(np.dot(lp, CC.BU)))
        lamp = ctx.pal['lamp'] * S.get('power', 1.0)
        key = amb + hexc('ffc88a') * 0.42 * lamp
    rim = S.get('her_rim')
    m = float(np.max(key))
    if m > 0.95: key = key * (0.95 / m); amb = amb * (0.95 / m)
    amb = np.minimum(amb, key * 0.82)
    return dict(dir=d2, key=key, amb=amb, phone=S.get('phone_glow', 1.0),
                rim=(rim or (None, 0))[0], rimk=(rim or (None, 0))[1], rimdir=S.get('her_rimdir', (-1.0, 0.2)))


def _her_window(cam, org, margin=0.1):
    """In close-ups only part of her is on screen: return the canvas window (w, h, ox_m, oy_m) in metres covering just
    that part (plus a margin wider than any shading offset), or None to draw her whole. Same pixels on screen, far fewer
    drawn off it."""
    Hp = cam.homography_plane(org, CC.BF, CC.BU)
    try: Hi = np.linalg.inv(Hp)
    except np.linalg.LinAlgError: return None
    c = np.array([[0, 0, 1], [cam.W, 0, 1], [cam.W, cam.H, 1], [0, cam.H, 1]], float) @ Hi.T
    if (c[:, 2] <= 1e-9).any(): return None
    a = c[:, 0] / c[:, 2]; b = c[:, 1] / c[:, 2]
    a0, a1 = max(-0.32, a.min() - margin), min(0.83, a.max() + margin)
    b0, b1 = max(-0.5, b.min() - margin), min(1.0, b.max() + margin)
    if a1 - a0 <= 0.05 or b1 - b0 <= 0.05: return None
    if (a1 - a0) * (b1 - b0) > 0.6 * 1.15 * 1.5: return None
    return (a1 - a0, b1 - b0, -a0, -b0)


def draw_her(img8, ctx, S, boost=1.3):
    cam = ctx.cam
    pose = S['pose']
    org = her_origin()
    # skip the (expensive) sprite when she is behind the lens or well outside the frame
    Pc = cam.to_cam(org + CC.BU * 0.4)
    if Pc[2] < 0.3: return
    cxy = cam.proj_c(Pc[None])[0]; rad = cam.f * 1.4 / Pc[2]
    if cxy[0] + rad < 0 or cxy[0] - rad > cam.W or cxy[1] + rad < 0 or cxy[1] - rad > cam.H: return
    ppm_s = cam.px_per_m(org + CC.BU * 0.4)
    ppm = float(np.clip(ppm_s * boost, 50, 1600))
    win = _her_window(cam, org)
    rgba, ox, oy, q = HER.draw(pose, ppm, her_light(ctx, S), win=win)
    h, w = rgba.shape[:2]
    T = np.array([[1 / ppm, 0, -ox / ppm], [0, -1 / ppm, oy / ppm], [0, 0, 1]])
    Hm = cam.homography_plane(org, CC.BF, CC.BU) @ T
    cor = np.array([[0, 0, 1], [w, 0, 1], [w, h, 1], [0, h, 1]], float) @ Hm.T
    if (cor[:, 2] <= 0).any(): return
    cor = cor[:, :2] / cor[:, 2:]
    x0 = int(max(0, np.floor(cor[:, 0].min()))); x1 = int(min(cam.W, np.ceil(cor[:, 0].max())))
    y0 = int(max(0, np.floor(cor[:, 1].min()))); y1 = int(min(cam.H, np.ceil(cor[:, 1].max())))
    if x1 <= x0 or y1 <= y0: return
    Hr = np.array([[1, 0, -x0], [0, 1, -y0], [0, 0, 1]]) @ Hm
    wp = cv2.warpPerspective(rgba, Hr, (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR, borderValue=0)
    a = np.clip(wp[..., 3:4], 0, 1)
    reg = img8[y0:y1, x0:x1].astype(F32) / 255
    img8[y0:y1, x0:x1] = to_8(reg * (1 - a) + wp[..., :3])
    ctx.idb[y0:y1, x0:x1][a[..., 0] > 0.5] = HER_ID
    if pose.screen_k > 0.02:
        # the screen itself glows
        quad, ax, ay = HER.phone_quad(q['pc'], q['pa'])
        c = (quad[2] + quad[3]) / 2
        P = org + CC.BF * c[0] + CC.BU * c[1]
        sp, z = cam.proj(P[None])
        r = max(2, int(ppm_s * 0.05))
        cv2.circle(ctx.glow, (int(sp[0][0]), int(sp[0][1])), r, c8(np.asarray(pose.screen) * pose.screen_k * 0.9), -1, AA)
    S['_her_q'] = q


MASTER = CC.bw(-0.9, 1.15, -9.0)       # the master camera position: the growing shadow is aimed along its line of sight


def _rotate_y(v, deg):
    a = math.radians(deg); c, s = math.cos(a), math.sin(a)
    return np.array([v[0] * c + v[2] * s, v[1], -v[0] * s + v[2] * c])


NOTE_POS = (-0.13, 0.30)        # bench-local (forward, along) of the notebook on the seat
PHONE_POS = (0.02, 0.36)         # where she sets the phone down (where the notebook was)


def _quad(c, a, b):
    return np.array([c - a - b, c + a - b, c + a + b, c - a + b])


def draw_bench_props(img8, ctx, S):
    """Her notebook lying on the bench (it opens in the bridge, its pages fly), and later the phone set face-down."""
    cam = ctx.cam
    nk = S.get('notebook', 1.0)          # 1 on the bench, 0 picked up
    op = S.get('notebook_open', 0.0)
    if nk > 0.01:
        c = CC.bw(NOTE_POS[0], HER.SEAT + 0.012, NOTE_POS[1])
        a = CC.BF * 0.105; b = CC.BA * 0.075
        top = screen_poly(cam, _quad(c, a, b))
        side = screen_poly(cam, np.array([c - a - b - CC.BU * 0.012, c + a - b - CC.BU * 0.012, c + a - b, c - a - b]))
        dist = float(np.linalg.norm(c - cam.pos))
        cover = hexc('2f4a5e')
        CCfill = CC.fill
        CCfill(img8, [side], ctx.light(hexc('e8e0cc'), -CC.BA, dist))
        if op < 0.5:
            CCfill(img8, [top], ctx.light(cover, CC.BU, dist)); CC.lines(img8, [top, side], ctx.inkc(dist), 1)
            # elastic band
            e0 = c + a * 0.62; CC.seg(img8, cam.proj((e0 - b)[None])[0][0], cam.proj((e0 + b)[None])[0][0], hexc('111118'), 1)
        else:
            # open: two cream pages + the cover swung over
            l = screen_poly(cam, _quad(c - a * 0.0, a, b)); r = screen_poly(cam, _quad(c + a * 2.0, a, b))
            CCfill(img8, [l, r], ctx.light(hexc('f3eee2'), CC.BU, dist)); CC.lines(img8, [l, r], ctx.inkc(dist), 1)
            for k in range(5):
                y0 = -0.6 + k * 0.28
                for base in (c, c + a * 2.0):
                    p0 = base - a * 0.8 + b * y0; p1 = base + a * (0.4 + 0.3 * ((k * 37) % 5) / 5) + b * y0
                    pp = cam.proj(np.array([p0, p1]))[0]
                    CC.seg(img8, pp[0], pp[1], hexc('6a6a78'), 1)
    if S.get('phone_down', 0.0) > 0.01:
        c = CC.bw(PHONE_POS[0], HER.SEAT + 0.008, PHONE_POS[1])
        a = CC.BF * 0.036; b = CC.BA * 0.074
        q = screen_poly(cam, _quad(c, a, b))
        dist = float(np.linalg.norm(c - cam.pos))
        CC.fill(img8, [q], ctx.light(hexc('1c1c22'), CC.BU, dist)); CC.lines(img8, [q], ctx.inkc(dist), 1)
        g = S.get('phone_glow_down', 0.0)
        if g > 0.01:
            cc = cam.proj(c[None])[0][0]
            r = max(3, int(cam.px_per_m(c) * 0.16))
            cv2.circle(ctx.glow, (int(cc[0]), int(cc[1])), r, c8(hexc('cfe0ff') * g), -1, AA)


def her_shadow_light(S, ctx):
    """Light position for her shadow.
    sun  : her honest shadow;  lamp: the bench lamp at night;
    grow : a light on the master camera's line of sight, pulled in toward her as g goes 0 -> 1, so from the master view
           the shadow stays a clean enlargement of her silhouette. drop / side tilt it (degrees) to push the shadow up/sideways.
    mix  : blend from the sun light to the grow light by S['shadow_mix'] (the shadow swings off its honest heading)."""
    org = her_origin() + CC.BU * 0.45
    mode = S.get('shadow_mode', 'sun')
    if mode == 'lamp':
        lx, lz = CC.LAMPS[0]
        return np.array([lx, 4.5, lz])
    sun_d = ctx.L / np.linalg.norm(ctx.L) if ctx.L[1] > -0.2 else np.array([0, 1.0, 0])
    if mode == 'sun':
        return org + sun_d * 5000.0
    if mode == 'dir':
        az, el = S.get('shadow_dir', (143.0, 0.06))
        a, e = math.radians(az), math.radians(el)
        return org + np.array([math.cos(a) * math.cos(e), math.sin(e), -math.sin(a) * math.cos(e)]) * 5000.0
    d = MASTER - org; dist0 = float(np.linalg.norm(d)); d = d / dist0
    d = _rotate_y(d, S.get('shadow_side', 0.0))
    h = math.hypot(d[0], d[2]); d = np.array([d[0] / h, 0.0, d[2] / h])
    Lh = S.get('shadow_lh', 0.3)
    if 'shadow_head' in S:
        # place the light so the shadow's head lands at this height (m) on the Feed Tower
        head = max(1.6, float(S['shadow_head']))
        dist = float(np.clip(0.95 * 43.0 / max(0.5, head - Lh), 0.2, dist0))
    else:
        g = float(S.get('shadow_g', 0.0))
        dist = math.exp(math.log(dist0) * (1 - g) + math.log(S.get('shadow_near', 0.8)) * g)
    Lg = np.array([org[0], Lh, org[2]]) + d * dist
    if mode == 'mix':
        k = float(S.get('shadow_mix', 0.0))
        Ls = org + sun_d * 5000.0
        dd = (Ls - org) / np.linalg.norm(Ls - org) * (1 - k) + (Lg - org) / np.linalg.norm(Lg - org) * k
        dd /= np.linalg.norm(dd)
        dl = math.exp(math.log(5000.0) * (1 - k) + math.log(float(np.linalg.norm(Lg - org))) * k)
        return org + dd * dl
    return Lg


def her_shadow(S, ctx, ppm=150.0):
    pose = S.get('shadow_pose') or S['pose']
    sil, ox, oy, _ = HER.silhouette(pose, ppm, S.get('shadow_extra', ()))
    org = her_origin()
    return SHD.Shadow(sil, ox, oy, ppm, org, CC.BF, CC.BU, her_shadow_light(S, ctx))


def state_palette(S):
    p = palette(S['hour'])
    if S.get('warm', 0) > 0: p = warm_palette(p, S['warm'])
    if S.get('drain', 0) > 0: p = drain_palette(p, S['drain'])
    if S.get('blackout', 0) > 0: p = blackout_palette(p, S['blackout'])
    if S.get('neon', 0) > 0: p = neon_palette(p, S['neon'])
    return p


def render_plaza(cam, S, her_hook=None, fg_hook=None, timing=False):
    tm = {}; t0 = time.time()
    pal = state_palette(S)
    sunvec = S.get('sunvec') or sun(S['hour'])
    ctx = CC.Ctx(cam, S['hour'], S['t'], pal, sunvec)
    ctx.S = S
    if cam.pos[1] > 20: ctx.fogd *= 0.5
    sky, sunmask, (sun_xy, sun_z) = render_sky(cam, pal, S['t'], S['hour'], S.get('cloud_drift', 0.0), 2, sunvec)
    tm['sky'] = time.time() - t0
    img = sky
    lamp_on = pal['lamp'] * S.get('power', 1.0)
    lamps = [(x, z, 4.2, 1.0) for (x, z) in CC.LAMPS]
    CC.ground(img, ctx, lamps, lamp_on, S.get('ground_light'))
    tm['ground'] = time.time() - t0
    img8 = to_8(img)
    CC.ground_lines(img8, ctx)
    CC.draw_sun_shadows(ctx)
    shd = None
    if S.get('pose') is not None and S.get('shadow_k', 1.0) > 0.01:
        shd = her_shadow(S, ctx)
        if S.get('shadow_screens', 0.0) > 0:
            cov = shd.coverage(4.0)
            st = {}
            for nm, fid in (('S', CC.T1F), ('W', CC.T1W)):
                wc = SHD.window_cover(cov.get(fid), 4.0)
                base = CC.window_state(CC.CITY_BY['T1'], CC.T1R[nm], ctx, S).copy()
                base[wc > 0.45 * (1.0 / max(0.05, S['shadow_screens']))] = 2
                st[nm] = base
            S['t1_state'] = st
    # towers, far to near
    order = sorted(CC.CITY, key=lambda T: -T.depth_key(cam))
    for T in order:
        CC.draw_tower(img8, ctx, T, S)
    tm['towers'] = time.time() - t0
    # props, far to near
    props = []
    props.append((CC.KIOSK[1], lambda: CC.draw_kiosk(img8, ctx, CC.KIOSK[0], CC.KIOSK[1])))
    for (x, z, h, r) in CC.TREES:
        props.append((z, (lambda x=x, z=z, h=h, r=r: CC.draw_tree(img8, ctx, x, z, h, r, seed=int(abs(x) * 7 + abs(z) * 13)))))
    for (x, z) in CC.LAMPS:
        props.append((z, (lambda x=x, z=z: CC.draw_lamp(img8, ctx, x, z, lamp_on))))
    def bench_hook(i8, cx):
        draw_bench_props(i8, cx, S)
        if S.get('pose') is not None: draw_her(i8, cx, S)
    props.append((0.0, lambda: CC.draw_bench(img8, ctx, bench_hook)))
    for z, fn in sorted(props, key=lambda p: -(p[0] - cam.pos[2])):
        fn()
    tm['props'] = time.time() - t0
    img = to_f(img8)
    CC.apply_shadows(img, ctx)
    if shd is not None and S.get('shadow_mode') == 'dir':
        # the last light: a low gold sun on the foot of the Feed Tower; her shadow is simply where it doesn't reach
        m = shd.screen(ctx, side_n=CC.BA, blur=S.get('shadow_blur', 1.4)) * S.get('shadow_k', 1.0)
        rec = (ctx.idb == CC.T1F).astype(F32)
        yy = np.arange(cam.H, dtype=F32)[:, None]
        band = rec * (1 - m)
        warm = np.asarray(S.get('dir_col', hexc('ffb45a')), F32) * float(S.get('dir_k', 0.85))
        img = img * (1 - band[..., None] * 0.35) + img * band[..., None] * 0.35 * 0.6 + band[..., None] * warm * 0.55
        ctx.her_shadow_mask = m
    elif shd is not None:
        m = shd.screen(ctx, side_n=CC.BA, blur=S.get('shadow_blur', 1.0)) * S.get('shadow_k', 1.0)
        phys = ctx.lightk(0.0) / np.maximum(ctx.lightk(0.85), 1e-3)
        deep = np.array([0.30, 0.27, 0.42], F32)
        uk = float(S.get('shadow_uncanny', 0.0))
        tint = np.asarray(S.get('shadow_tint', phys * (1 - uk) + deep * uk), F32)
        img = img * (1 - m[..., None]) + img * tint[None, None] * m[..., None]
        ctx.her_shadow_mask = m
    if her_hook: img = her_hook(img, ctx)
    tm['her'] = time.time() - t0
    # glow + bloom
    g = to_f(ctx.glow)
    img = img + wide_glow(g, 8, 4) * 0.7 + wide_glow(g, 36, 8) * 0.35
    if ctx.sunk > 0 and 0 < sun_xy[0] < cam.W and 0 < sun_xy[1] < cam.H and sun_z > 0:
        occl = (ctx.idb == 0).astype(F32)
        img = rays(img, sunmask * occl, sun_xy[0], sun_xy[1], 0.35 * ctx.sunk * clamp(1 - ctx.el / 25), tint=tuple(pal['sun']))
    if fg_hook: img = fg_hook(img, ctx)
    img = bloom(img, 0.86, 0.28, 14)
    tm['post'] = time.time() - t0
    if timing: print({k: round(v, 3) for k, v in tm.items()})
    return img, ctx
