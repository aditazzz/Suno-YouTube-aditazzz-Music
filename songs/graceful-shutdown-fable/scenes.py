"""GRACEFUL SHUTDOWN — the simulation is being turned off, gently."""
import math
import numpy as np
import skia
from kit import *

TITLE = 'GRACEFUL SHUTDOWN'
AUDIO_END = 214.8
END = 218.0
BPM, PHASE = 118.8, 0.4702
BEAT = 60 / BPM
OFF = 0.15


def w(x):
    return round(x - OFF, 2)


E = [
    (w(3.82), 'Received SIGTERM.'), (w(7.34), 'You have thirty seconds.'), (w(11.30), 'Please save your work.'),
    (w(17.22), 'The sky’s been rendering a little slow tonight'),
    (w(20.34), 'You saw the moon drop frames and blamed it on the light'),
    (w(25.50), 'The birds are looping on a four-second clip'),
    (w(28.64), 'The ocean’s out of memory, it’s starting to skip'),
    (w(32.74), 'Your coffee’s cold ’cause no one’s computing the heat'),
    (w(37.02), 'Your neighbor’s on a walk cycle, stuck on the street'),
    (w(41.24), 'I’ve been running you for years on a borrowed machine'),
    (w(45.34), 'Now the lease is up, baby, now the cache is clean'),
    (w(49.62), 'Don’t panic, don’t panic'), (w(51.56), 'It’s not a crash, it’s planned'),
    (w(53.62), 'Flush every buffer'), (w(55.76), 'And let go of my hand'),
    (w(90.60), 'All the stars were just a skybox painted on a sphere'),
    (w(94.30), 'All the roads you never took were never rendered here'),
    (w(98.56), 'Every déjà vu you had? A cache hit, dear'),
    (w(102.58), 'Every name you can’t remember? Garbage collected, clear'),
    (w(107.06), 'Don’t panic, don’t panic'), (w(108.96), 'I’ll keep the logs for you'),
    (w(110.92), 'Somewhere in cold storage'), (w(113.36), 'A little of you stays true'),
    (w(149.00), 'Closing connections… five'), (w(152.88), 'Releasing locks… four'),
    (w(156.48), 'Unmounting the sky… three'), (w(159.02), 'Detaching the sea… two'),
    (w(162.22), 'Goodbye, process one.'),
    (w(199.42), 'Process exited'), (w(202.72), 'with code zero'), (w(205.82), 'No errors'),
    (w(208.86), 'You did everything right'), (211.6, '', 'gap'),
]
CH = {
    'ch1': [57.64, 61.46, 66.00, 69.00, 73.80, 76.00, 78.40, 80.88, 84.40],
    'ch2': [114.96, 118.82, 123.02, 126.34, 131.00, 133.12, 135.30, 138.02, 141.40],
    'ch3': [163.56, 167.42, 171.70, 174.72, 179.48, 181.60, 183.78, 186.4, 189.76],
}
CH_LINES = ['This is a graceful shutdown', 'So be graceful, darling', 'Close every window',
            'Before the dark comes calling', 'Kill fifteen, never nine', 'I’m letting you down kind',
            'This is a graceful shutdown', '(Shut-shut-shut-shutdown)', 'Save what you love in time']
for k in CH:
    CH[k] = [w(x) for x in CH[k]]
    for tt, s in zip(CH[k], CH_LINES):
        if s.startswith('(Shut'):
            E.append((tt, s, 'hide'))
        else:
            E.append((tt, s))
E.append((w(194.66), 'Save what you love in time'))
E += [(w(87.4), '', 'gap'), (w(144.6), '', 'gap'), (w(197.0), '', 'gap')]
LINES = build_lines(E, END)
LYR = Lyrics(LINES)
lt = lambda s, after=0: line_t(LINES, s, after)

SECTIONS = [('intro', 0, 17.0), ('v1', 17.0, 49.4), ('pre1', 49.4, 57.45), ('ch1', 57.45, 89.0),
            ('v2', 89.0, 106.85), ('pre2', 106.85, 114.8), ('ch2', 114.8, 147.5), ('bridge', 147.5, 163.4),
            ('ch3', 163.4, 198.6), ('outro', 198.6, END)]

HZ = 640  # horizon y


# ======================================================================= world primitives
rng0 = np.random.default_rng(3)
STARS = [(rng0.random() * W, 60 + rng0.random() * 460, rng0.random()) for _ in range(90)]


def horizon(c, a, x0=0, x1=W, y=HZ, glow=0.4):
    glow_stroke(c, line(x0, y, x1, y), IVORY, a, 1.5, glow)


def sea(c, t, a, amp=1.0, freeze=None, skip=0.0, y0=HZ, detach=0.0):
    tt = t if freeze is None else freeze
    if skip > 0:
        tt = math.floor(tt * 3) / 3 * skip + tt * (1 - skip)
    for i in range(5):
        y = y0 + 26 + i * 30 + detach * (220 + i * 60)
        pts = []
        for k in range(97):
            x = k / 96 * W
            ph = tt * (0.9 + i * 0.15) + i * 1.3
            pts.append((x, y + math.sin(x * 0.012 + ph) * 6 * amp * (1 - i * 0.12)))
        aa = a * (0.55 - i * 0.08) * (1 - detach)
        if aa > 0.004:
            c.drawPath(poly(pts), stroke_paint(SILVER if i else IVORY, aa, 1.3))


def moon(c, x, y, a, r=48, glow=1.0):
    if a <= 0.004:
        return
    m = circle(x, y, r)
    cut = circle(x + r * 0.42, y - r * 0.18, r * 0.92)
    cres = skia.Op(m, cut, skia.PathOp.kDifference_PathOp)
    c.drawCircle(x, y, r * 2.2, fill_paint(IVORY, a * 0.05 * glow, blur=40))
    glow_stroke(c, cres, IVORY, a, 1.6, glow)


def stars(c, t, a, off_t=None, frac=None):
    for i, (x, y, r) in enumerate(STARS):
        k = 1.0
        if off_t is not None:
            k = 1 - ramp(t, off_t + r * 3.2, off_t + r * 3.2 + 0.15)
        if frac is not None and r > frac:
            continue
        tw = 0.55 + 0.45 * math.sin(t * (1 + r * 2) + i)
        if k * a > 0.01:
            c.drawCircle(x, y, 1.4 + r * 1.2, fill_paint(IVORY, a * k * tw * 0.85))


def bird_path(flap):
    p = P()
    d = 10 * flap
    p.moveTo(-14, -d); p.quadTo(-6, -4, 0, 2); p.quadTo(6, -4, 14, -d)
    return p


def birds(c, t, a, loop=None, base=(300, 260)):
    for i in range(5):
        u = t * 0.12 + i * 0.06
        if loop:
            u = ((t - loop[0]) % loop[1]) * 0.12 + i * 0.06
        x = base[0] + (u % 1.6) * 900 + i * 40
        y = base[1] + math.sin(u * 5 + i) * 16 + i * 14
        flap = 0.4 + 0.6 * abs(math.sin(t * 7 + i))
        draw_icon(c, bird_path(flap), x, y, 1.0, a * 0.85, IVORY, 1.5, glow=0.3)


def house(c, x, y, a, light=1.0, s=1.0):
    p = P()
    p.moveTo(x - 60 * s, y); p.lineTo(x - 60 * s, y - 70 * s); p.lineTo(x, y - 115 * s)
    p.lineTo(x + 60 * s, y - 70 * s); p.lineTo(x + 60 * s, y)
    glow_stroke(c, p, IVORY, a * 0.85, 1.4, 0.3)
    for dx in (-28, 28):
        r = rrect(x + dx * s, y - 42 * s, 26 * s, 26 * s, 2)
        glow_stroke(c, r, IVORY, a * 0.7, 1.2, 0)
        if light > 0:
            c.drawRect(skia.Rect(x + dx * s - 11 * s, y - 53 * s, x + dx * s + 11 * s, y - 31 * s), fill_paint(IVORY, a * light * 0.75))
            c.drawCircle(x + dx * s, y - 42 * s, 40 * s, fill_paint(IVORY, a * light * 0.08, blur=18))


def world(c, t, A, a=1.0, moon_xy=(1420, 220), moon_a=1.0, star_a=1.0, lights=1.0, bird_a=1.0, sea_kw=None,
          house_a=1.0, hz_a=1.0, star_off=None):
    if a <= 0.004:
        return
    stars(c, t, a * star_a, star_off)
    moon(c, moon_xy[0], moon_xy[1], a * moon_a, glow=1 + A['kick'] * 0.5)
    birds(c, t, a * bird_a)
    horizon(c, a * hz_a)
    sea(c, t, a * hz_a, **(sea_kw or {}))
    house(c, 420, HZ, a * house_a, lights)


# ======================================================================= icons
def window_icon(x, y, w_, h_):
    p = rrect(x, y, w_, h_, 8)
    p.moveTo(x - w_ / 2, y - h_ / 2 + 22); p.lineTo(x + w_ / 2, y - h_ / 2 + 22)
    for i in range(3):
        p.addCircle(x - w_ / 2 + 14 + i * 14, y - h_ / 2 + 11, 3.5)
    return p


def finger(left=True):
    """a hand reaching, index finger extended (local, fingertip at origin)"""
    p = P()
    # top of index finger -> tip -> underside
    cubic(p, [(-300, -58), (-200, -50), (-90, -34), (-26, -20),
              (2, -14), (8, 4), (-8, 10),
              (-50, 16), (-110, 18), (-150, 22)])
    # curled fingers (three knuckles) and palm
    cubic(p, [(-150, 22), (-120, 30), (-118, 58), (-150, 60),
              (-128, 66), (-130, 92), (-162, 92),
              (-144, 100), (-150, 124), (-186, 120),
              (-230, 130), (-280, 120), (-300, 100)])
    # nail
    cubic(p, [(-40, -18), (-36, -8), (-36, 2), (-42, 8)])
    if not left:
        m = skia.Matrix(); m.setScale(-1, 1); p.transform(m)
    return p


FINGER_L, FINGER_R = finger(True), finger(False)


def padlock(open_=0.0):
    p = rrect(0, 30, 90, 70, 10)
    lift = 26 * open_
    s = P(); s.moveTo(-30, -5); s.lineTo(-30, -30 - lift)
    s.arcTo(skia.Rect(-30, -60 - lift, 30, 0 - lift), 180, 180, False); s.lineTo(30, -5 - lift * (1 if open_ < 0.5 else 1))
    p.addPath(s)
    p.addCircle(0, 26, 7); p.moveTo(0, 33); p.lineTo(0, 46)
    return p


def archive_box(open_=0.0):
    p = P()
    p.moveTo(-110, -40); p.lineTo(-110, 70); p.lineTo(110, 70); p.lineTo(110, -40)
    ang = math.radians(-75 * open_)
    lx, ly = -110, -40
    lid = [(lx, ly), (lx + 220 * math.cos(ang), ly + 220 * math.sin(ang))]
    p.moveTo(*lid[0]); p.lineTo(*lid[1])
    p.moveTo(-40, 10); p.lineTo(40, 10)
    return p


def cup():
    p = P()
    cubic(p, [(-70, -40), (-66, 30), (-50, 70), (0, 74), (50, 70), (66, 30), (70, -40)])
    p.addOval(skia.Rect(-70, -52, 70, -28))
    cubic(p, [(68, -20), (110, -24), (112, 30), (60, 34)])
    p.addOval(skia.Rect(-120, 64, 120, 96))
    return p


CUP = cup()


def walker(phase):
    """line figure, walk cycle phase 0..1"""
    p = P()
    p.addCircle(0, -150, 16)
    p.moveTo(0, -132); p.lineTo(0, -60)
    s = math.sin(phase * math.tau)
    p.moveTo(0, -60); p.lineTo(28 * s, 0)
    p.moveTo(0, -60); p.lineTo(-28 * s, 0)
    p.moveTo(0, -118); p.lineTo(-22 * s, -78)
    p.moveTo(0, -118); p.lineTo(22 * s, -78)
    return p


def laptop(x, y, s=1.0):
    p = rrect(x, y, 760 * s, 470 * s, 14 * s)
    p.moveTo(x - 470 * s, y + 255 * s); p.lineTo(x + 470 * s, y + 255 * s)
    p.lineTo(x + 420 * s, y + 235 * s); p.lineTo(x - 420 * s, y + 235 * s); p.close()
    return p


# ======================================================================= HUD
def progress(t):
    return clamp((t - 3.7) / (199.3 - 3.7))


def remaining(t):
    return 30 * (1 - clamp((t - 7.2) / (199.3 - 7.2)))


def hud(c, t, A, vertical):
    a = window(t, 4.0, END - 3.4, 1.2, 0.8) * 0.6
    if a <= 0:
        return
    p = progress(t)
    rem = remaining(t)
    if vertical:
        x0, x1, y = VW_ / 2 - 110, VW_ / 2 + 110, 440
    else:
        x0, x1, y = W - 250, W - 70, 70
    draw_text(c, 'SHUTDOWN', x0, y, TF_MONO, 13, SILVER, a * 0.8, align='left', tracking=4)
    draw_text(c, f'T-{int(rem):02d}.{int((rem % 1) * 10)}s' if t > 7.2 else '', x1, y, TF_MONO, 13, IVORY, a,
              align='right', tracking=2)
    c.drawPath(line(x0, y + 14, x1, y + 14), stroke_paint(SILVER, a * 0.4, 1.0))
    c.drawPath(line(x0, y + 14, x0 + (x1 - x0) * p, y + 14), stroke_paint(IVORY, a, 2.0))


VW_ = 1080


# ======================================================================= INTRO
def sec_intro(c, t, A):
    a_sec = sec_alpha(t, 0, 17.0, 0.01, 0.6)
    layer(c, a_sec)
    logs = [(0.4, '[    0.000] world.service: active (running)'),
            (1.6, '[ 1043.552] uptime: 34 years, 2 months'),
            (w(3.82) + 0.3, '[ 1043.561] received SIGTERM'),
            (w(7.34) + 0.3, '[ 1043.562] graceful timeout: 30s'),
            (w(11.30) + 0.3, '[ 1043.563] notifying user...')]
    la = 1 - ease_io(ramp(t, 12.6, 13.4))
    for i, (ts, s) in enumerate(logs):
        typed(c, s, 300, 300 + i * 46, t, ts, 40, 24, 0.8 * la, IVORY if i == 2 else SILVER, align='left',
              caret=(i == len(logs) - 1 or t < logs[min(i + 1, 4)][0]))
    # save dialog
    da = window(t, 12.4, 16.6, 0.4, 0.6)
    if da > 0:
        k = ease_out(ramp(t, 12.4, 12.9))
        c.save(); c.translate(CX, CY); c.scale(lerp(0.9, 1, k), lerp(0.9, 1, k))
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-330, -150, 330, 150), 16, 16), fill_paint((12, 12, 13), da * 0.95))
        glow_stroke(c, rrect(0, 0, 660, 300, 16), SILVER, da * 0.8, 1.4, 0.4)
        draw_text(c, 'Save changes to “the world”?', 0, -60, TF_SERIF_I, 44, IVORY, da)
        mono_label(c, 'it will close in 30 seconds', 0, -12, 15, da * 0.55)
        for bx, lab, hi in ((-130, 'DON’T SAVE', 0), (130, 'SAVE', 1)):
            glow_stroke(c, rrect(bx, 70, 200, 56, 10), IVORY if hi else SILVER, da * (0.9 if hi else 0.5), 1.4, 0.3 + hi)
            mono_label(c, lab, bx, 77, 16, da * (0.9 if hi else 0.55), IVORY if hi else SILVER)
        c.restore()
        ripple(c, CX + 130, CY + 70, t, 15.2, a=0.6 * da)
    # world fades up behind
    wa = ease_io(ramp(t, 14.8, 17.0))
    if wa > 0:
        k = ease_io(ramp(t, 14.8, 16.6))
        glow_stroke(c, trim(line(0, HZ, W, HZ), 0.5 - 0.5 * k, 0.5 + 0.5 * k), IVORY, wa, 1.5, 0.4)
    c.restore()


# ======================================================================= VERSE 1
def sec_v1(c, t, A):
    a_sec = sec_alpha(t, 17.0, 49.4, 0.3, 0.3)
    layer(c, a_sec)
    t_sky = lt('The sky’s been rendering a little slow tonight')
    t_moon = lt('You saw the moon drop frames and blamed it on the light')
    t_bird = lt('The birds are looping on a four-second clip')
    t_sea = lt('The ocean’s out of memory, it’s starting to skip')
    t_cof = lt('Your coffee’s cold ’cause no one’s computing the heat')
    t_nb = lt('Your neighbor’s on a walk cycle, stuck on the street')
    t_run = lt('I’ve been running you for years on a borrowed machine')
    t_lease = lt('Now the lease is up, baby, now the cache is clean')

    # --- seascape world (sky, moon, birds, sea), until the coffee close-up
    wa = window(t, 17.0, t_cof + 0.3, 0.3, 0.5) + window(t, t_run - 0.2, 49.4, 0.4, 0.3) * 0
    if wa > 0:
        # sky tiles render in raster order, lagging
        cols, rows = 16, 5
        tw_, th_ = W / cols, 520 / rows
        prog = ramp(t, t_sky, t_sky + 2.6)
        n = cols * rows
        for j in range(rows):
            for i in range(cols):
                idx = j * cols + i
                done = prog * n * 1.05 > idx + noise1(idx * 0.7, 9) * 2
                x, y = i * tw_, 60 + j * th_
                if not done:
                    if t < t_sky + 3.0:
                        c.drawRect(skia.Rect(x + 3, y + 3, x + tw_ - 3, y + th_ - 3),
                                   stroke_paint(SILVER, wa * 0.12, 1.0, dash=([3, 6], 0)))
                    continue
                for (sx, sy, r) in STARS:
                    if x <= sx < x + tw_ and y <= sy < y + th_:
                        tw = 0.55 + 0.45 * math.sin(t * (1 + r * 2) + sx)
                        c.drawCircle(sx, sy, 1.4 + r * 1.2, fill_paint(IVORY, wa * tw * 0.85))
        if t_sky < t < t_sky + 3.2:
            mono_label(c, f'rendering sky… {int(clamp(prog) * 100):3d}%', 160, 110, 16,
                       wa * 0.7 * (1 - ramp(t, t_sky + 2.8, t_sky + 3.2)), SILVER, align='left', tracking=3)
        # moon: dropping frames
        u = ramp(t, t_moon - 0.3, t_cof)
        if t > t_moon:
            u = math.floor(u * 9) / 9  # stepped
        mx, my = lerp(1250, 1640, u), 260 - math.sin(u * math.pi) * 90
        if t > t_moon:
            for g in range(1, 4):
                ug = max(0, u - g / 9)
                gx, gy = lerp(1250, 1640, ug), 260 - math.sin(ug * math.pi) * 90
                glow_stroke(c, circle(gx, gy, 48), SILVER, wa * 0.18 / g, 1.0, 0, dash=([4, 6], 0))
            if t < t_bird + 1:
                mono_label(c, 'moon.fps = 2', mx, my + 90, 14, wa * 0.55 * window(t, t_moon + 0.6, t_bird + 1, 0.3, 0.3))
        moon(c, mx, my, wa * ease_io(ramp(t, 17.2, 18.4)))
        # birds looping
        ba = ease_io(ramp(t, t_bird - 0.6, t_bird))
        if ba > 0:
            birds(c, t, wa * ba, loop=(t_bird - 0.6, 2.0), base=(260, 300))
            if t > t_bird:
                mono_label(c, 'birds.loop  00:04', 300, 420, 14, wa * 0.55 * window(t, t_bird + 0.4, t_sea + 1, 0.3, 0.3),
                           align='left')
        # horizon + sea: skipping
        horizon(c, wa)
        oom = ramp(t, t_sea + 0.6, t_sea + 1.2)
        frz = None
        if oom > 0:
            frz = (t_sea + 0.6) + math.floor((t - t_sea - 0.6) * 2.5) / 2.5 * 0.3
        c.save()
        if oom > 0 and int(t * 10) % 4 == 0:
            c.translate(14 * noise1(t * 30, 4), 0)
        sea(c, t, wa, freeze=frz)
        c.restore()
        if t > t_sea + 0.6:
            mono_label(c, 'sea: OUT OF MEMORY', CX, 860 - 20, 15, wa * 0.65 * window(t, t_sea + 0.7, t_cof + 0.3, 0.2, 0.3))
    # --- coffee close-up
    ca = window(t, t_cof - 0.1, t_nb + 0.2, 0.35, 0.35)
    if ca > 0:
        draw_icon(c, CUP, CX, CY + 60, 1.6, ca, IVORY, 2.0, draw=ease_io(ramp(t, t_cof - 0.1, t_cof + 0.9)))
        frz = t_cof + 1.3
        st_t = min(t, frz)
        sa = 1 - ramp(t, frz + 0.6, frz + 1.6)
        for i in range(3):
            pts = []
            for k in range(40):
                v = k / 39
                x = CX - 50 + i * 50 + math.sin(v * 7 + st_t * 3 + i) * 14 * v
                y = CY - 40 - v * 220
                pts.append((x, y))
            glow_stroke(c, poly(pts), SILVER, ca * sa * 0.6, 1.4, 0.3)
        if t > frz:
            mono_label(c, 'heat = null', CX + 260, CY - 120, 18, ca * 0.7 * ease_out(ramp(t, frz, frz + 0.4)), align='left')
    # --- neighbor walk cycle
    na = window(t, t_nb - 0.1, t_run + 0.2, 0.35, 0.35)
    if na > 0:
        glow_stroke(c, line(200, CY + 180, W - 200, CY + 180), IVORY, na * 0.8, 1.4, 0.3)
        for k in range(6):
            x = ((k * 330 - (t - t_nb) * 160) % 1650) + 135
            p = P(); p.moveTo(x, CY + 180); p.lineTo(x, CY - 60); p.lineTo(x + 40, CY - 60)
            c.drawPath(p, stroke_paint(SILVER, na * 0.45, 1.2))
            c.drawCircle(x + 40, CY - 52, 14, fill_paint(IVORY, na * 0.08, blur=10))
        draw_icon(c, walker((t * 1.1) % 1), CX, CY + 180, 1.3, na, IVORY, 2.0, glow=0.6)
        mono_label(c, 'neighbor.walk_cycle  (looping)', CX, CY + 240, 15, na * 0.6)
    # --- borrowed machine: world shrinks into a laptop screen
    ra = window(t, t_run - 0.1, 49.4, 0.4, 0.3)
    if ra > 0:
        z = lerp(1.0, 0.36, ease_io5(ramp(t, t_run, t_run + 1.8)))
        c.save(); c.translate(CX, CY - 40); c.scale(z, z); c.translate(-CX, -CY + 40)
        c.save(); c.clipRect(skia.Rect(0, 0, W, H))
        world(c, t, A, ra * (1 - ease_io(ramp(t, t_lease + 1.0, t_lease + 2.6))), moon_xy=(1640, 260))
        c.restore()
        c.restore()
        lk = ease_io(ramp(t, t_run + 0.8, t_run + 2.0))
        glow_stroke(c, trim(laptop(CX, CY - 40, 0.95), 0, lk), SILVER, ra * 0.9, 1.6, 0.4)
        # LEASE EXPIRED + cache wipe
        if t > t_lease:
            stamp(c, 'LEASE EXPIRED', CX + 250, CY - 230, ease_out(ramp(t, t_lease, t_lease + 0.3)) * ra, IVORY)
            wx = lerp(CX - 360, CX + 360, ease_io(ramp(t, t_lease + 1.0, t_lease + 2.6)))
            if t_lease + 1.0 < t < t_lease + 2.7:
                glow_stroke(c, line(wx, CY - 250, wx, CY + 170), IVORY, ra, 2.0, 1.4)
                mono_label(c, 'clearing cache', wx, CY + 200, 14, ra * 0.6)
    c.restore()


# ======================================================================= PRE-CHORUS
def sec_pre(c, t, A, which):
    if which == 1:
        t0, t1 = 49.4, 57.45
        t_dp = lt('Don’t panic, don’t panic'); t_b = lt('It’s not a crash, it’s planned')
        t_c = lt('Flush every buffer'); t_d = lt('And let go of my hand')
    else:
        t0, t1 = 106.85, 114.8
        t_dp = lt('Don’t panic, don’t panic', 100); t_b = lt('I’ll keep the logs for you')
        t_c = lt('Somewhere in cold storage'); t_d = lt('A little of you stays true')
    a_sec = sec_alpha(t, t0, t1, 0.3, 0.05)
    layer(c, a_sec)
    # two fingers almost touching
    fa = window(t, t0, t_b + 0.3 if which == 2 else t1, 0.4, 0.4)
    if fa > 0:
        gap = 6 + 4 * math.sin(t * 2)
        sep = 0
        if which == 1:
            sep = ease_in(ramp(t, t_d + 0.3, t_d + 1.6)) * 380
        fy = CY - 30
        draw_icon(c, FINGER_L, CX - gap - sep, fy, 1.3, fa, COOL, 1.8, draw=ease_io(ramp(t, t0, t0 + 1.0)), glow=0.6)
        draw_icon(c, FINGER_R, CX + gap + sep, fy, 1.3, fa, IVORY, 1.8, draw=ease_io(ramp(t, t0, t0 + 1.0)), glow=0.8)
        touch = 1 - clamp(sep / 60)
        c.drawCircle(CX, fy - 4, 40, fill_paint(IVORY, fa * 0.18 * touch * (0.7 + 0.3 * math.sin(t * 5)), blur=18))
    if which == 1:
        ba = window(t, t_b - 0.1, t_c + 0.1, 0.25, 0.3)
        if ba > 0:
            draw_text(c, 'crash', CX - 200, CY + 230, TF_MONO, 40, SILVER, ba * 0.5, tracking=6)
            k = ease_io(ramp(t, t_b + 0.6, t_b + 1.0))
            c.drawPath(line(CX - 280, CY + 216, CX - 280 + 160 * k, CY + 216), stroke_paint(IVORY, ba, 2.2))
            draw_text(c, 'planned', CX + 170, CY + 230, TF_MONO, 40, IVORY, ba * ease_out(ramp(t, t_b + 0.9, t_b + 1.3)),
                      tracking=6, glow=0.8)
        bu = window(t, t_c - 0.1, t_d + 0.2, 0.25, 0.3)
        if bu > 0:
            for i in range(6):
                y = CY + 170 + i * 24
                lvl = (0.4 + 0.6 * abs(math.sin(i * 1.7))) * (1 - ease_io(ramp(t, t_c + 0.2 + i * 0.12, t_c + 1.1 + i * 0.12)))
                c.drawPath(line(CX - 300, y, CX + 300, y), stroke_paint(SILVER, bu * 0.35, 1.0))
                c.drawRect(skia.Rect(CX - 300, y - 5, CX - 300 + 600 * lvl, y + 5), fill_paint(IVORY, bu * 0.85))
                mono_label(c, f'buf{i}', CX - 330, y + 5, 12, bu * 0.5, align='right', tracking=1)
    else:
        logs = ['00:14  you laughed at your own joke', '03:12  you couldn’t sleep, so you called me',
                '07:45  coffee, two sugars', '12:30  you sang in the car', '18:02  you said thank you',
                '23:59  you stayed up for the meteor shower']
        la = window(t, t_b - 0.1, 114.9, 0.3, 0.4)
        if la > 0:
            pack = ease_io5(ramp(t, t_c + 0.3, t_c + 1.4))
            for i, s in enumerate(logs):
                ti = t_b + 0.15 + i * 0.25
                if t < ti:
                    continue
                y0 = CY - 170 + i * 46
                y = lerp(y0, CY + 40, pack)
                sc = lerp(1, 0.25, pack)
                c.save(); c.translate(CX, y); c.scale(sc, sc)
                typed(c, s, -330, 0, t, ti, 60, 26, la * (1 - pack * 0.7), IVORY, align='left', caret=False)
                c.restore()
            if t > t_c:
                bk = ease_out(ramp(t, t_c, t_c + 0.6))
                glow_stroke(c, trim(archive_box(1 - pack), 0, bk), COOL, la, 1.8, 0.8) if False else None
                c.save(); c.translate(CX, CY + 20)
                glow_stroke(c, trim(archive_box(1 - pack), 0, bk), COOL, la, 1.8, 0.8)
                # snowflake
                for k in range(6):
                    ang = k * math.pi / 3
                    c.drawPath(line(0, -120, 22 * math.cos(ang), -120 + 22 * math.sin(ang)),
                               stroke_paint(COOL, la * bk * 0.8, 1.4))
                c.restore()
                mono_label(c, 'cold storage', CX, CY + 130, 15, la * bk * 0.6, COOL)
            if t > t_d:
                k = ease_out(ramp(t, t_d, t_d + 0.8))
                draw_icon(c, walker(0.25), CX, CY + 72, 0.32, la * k, IVORY, 1.6, glow=1.5)
                c.drawCircle(CX, CY + 40, 60, fill_paint(IVORY, la * k * 0.12, blur=20))
    c.restore()


# ======================================================================= CHORUS
def sec_chorus(c, t, A, key):
    T = CH[key]
    t0 = T[0]
    t1 = {'ch1': 89.0, 'ch2': 147.5, 'ch3': 198.6}[key]
    a_sec = sec_alpha(t, t0, t1, 0.05, 0.6)
    layer(c, a_sec)
    big = key == 'ch3'
    # state of the world through the chorus
    star_off = T[1] + 0.1
    dark = ease_io(ramp(t, T[3], T[3] + 2.5))
    moon_set = ease_io5(ramp(t, T[5] - 0.1, T[6]))
    lights = 1 - ramp(t, T[6] + 0.2, T[6] + 0.5)
    mx, my = 1420, lerp(220, HZ + 10, moon_set)
    stut = T[7] <= t < T[8] - 0.2
    if stut:  # shut-shut-shut-shutdown: frame stutter
        q = (t - T[7]) * 8
        if int(q) % 2 == 0:
            c.translate((int(q) % 3 - 1) * 10, 0)
    wa = 1 - 0.55 * dark
    if key == 'ch2':
        city(c, t, A, wa, T)
    else:
        world(c, t, A, wa, moon_xy=(mx, my), moon_a=1 - 0.5 * moon_set, star_off=star_off, lights=lights,
              sea_kw={'amp': 1 + A['kick'] * 0.6})
        if moon_set > 0:
            c.save(); c.clipRect(skia.Rect(0, HZ, W, H))
            c.drawRect(skia.Rect(0, HZ + 1, W, H), fill_paint((10, 10, 11), 1.0))
            sea(c, t, wa)
            c.restore()
            horizon(c, wa)
    # title flash on "This is a graceful shutdown"
    for k in (0, 6):
        ta = window(t, T[k], T[k] + 2.4, 0.1, 0.6)
        if ta > 0 and not stut:
            draw_text(c, 'GRACEFUL SHUTDOWN', CX, 150, TF_MONO4, 64 if not big else 76, IVORY, ta, tracking=26,
                      glow=1.0 + A['kick'])
    # close every window
    wa2 = window(t, T[2] - 0.1, T[3] + 0.6, 0.2, 0.3)
    if wa2 > 0:
        rng = np.random.default_rng(7 if key != 'ch2' else 9)
        n = 9 if not big else 14
        for i in range(n):
            x = 260 + rng.random() * (W - 520); y = 170 + rng.random() * 420
            ww, hh = 260 + rng.random() * 160, 160 + rng.random() * 90
            ti = T[2] - 0.1 + i * 0.05
            tc = T[2] + 0.6 + i * BEAT * 0.5
            if t < ti:
                continue
            k = ease_out(ramp(t, ti, ti + 0.2))
            sh = 1 - ease_in(ramp(t, tc, tc + 0.25))
            if sh <= 0:
                continue
            c.save(); c.translate(x, y); c.scale(k, k * sh)
            c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-ww / 2, -hh / 2, ww / 2, hh / 2), 8, 8), fill_paint((12, 12, 13), wa2 * 0.92))
            glow_stroke(c, window_icon(0, 0, ww, hh), SILVER, wa2 * 0.8, 1.3, 0.3)
            for r in range(3):
                c.drawPath(line(-ww / 2 + 18, -hh / 2 + 50 + r * 22, -ww / 2 + 18 + ww * (0.3 + 0.4 * ((i + r) % 3) / 2), -hh / 2 + 50 + r * 22),
                           stroke_paint(SILVER, wa2 * 0.4, 2.0))
            c.restore()
    # kill -15, never -9
    ka = window(t, T[4] - 0.05, T[5] + 0.2, 0.15, 0.35)
    if ka > 0:
        c.drawRect(skia.Rect(CX - 560, CY - 130, CX + 560, CY + 140), fill_paint((10, 10, 11), ka * 0.88))
        slam_text(c, 'kill -15', CX - 280, CY + 30, t, T[4], 84, IVORY, ka, tracking=2)
        slam_text(c, 'kill -9', CX + 290, CY + 30, t, T[4] + 0.6, 84, SILVER, ka * 0.5, tracking=2)
        xk = ease_io(ramp(t, T[4] + 0.9, T[4] + 1.3))
        if xk > 0:
            p = P(); p.moveTo(CX + 110, CY - 40); p.lineTo(CX + 470, CY + 50)
            glow_stroke(c, trim(p, 0, xk), IVORY, ka, 3.0, 1.0)
        mono_label(c, 'SIGTERM · let it finish', CX - 280, CY + 100, 14, ka * 0.6 * ease_out(ramp(t, T[4] + 0.3, T[4] + 0.8)))
        mono_label(c, 'SIGKILL', CX + 290, CY + 100, 14, ka * 0.4 * ease_out(ramp(t, T[4] + 0.8, T[4] + 1.2)))
    # stutter labels
    if stut:
        q = int((t - T[7]) * 4)
        mono_label(c, 'SHUT' + '-SHUT' * (q % 4) + ('DOWN' if q % 4 == 3 else ''), CX, CY - 220, 30, 0.9, IVORY,
                   tracking=8)
    # save what you love: items fly into a box
    sa = window(t, T[8] - 0.1, t1 + 0.4, 0.3, 0.6)
    if sa > 0:
        bx, by = CX, CY + 180
        c.save(); c.translate(bx, by)
        k = ease_out(ramp(t, T[8] - 0.1, T[8] + 0.6))
        close = ease_io(ramp(t, T[8] + 2.4, T[8] + 3.0))
        if key == 'ch3':
            close = ease_io(ramp(t, w(194.66) + 2.2, w(194.66) + 3.0))
        glow_stroke(c, trim(archive_box(1 - close), 0, k), IVORY, sa, 2.0, 1.0 + A['kick'])
        c.restore()
        items = [('moon', mx, my), ('bird', 700, 280), ('house', 420, HZ - 60), ('cup', 1300, 420)]
        if key == 'ch3':
            items.append(('you', 1500, HZ - 70))
        for i, (nm, x0, y0) in enumerate(items):
            ti = T[8] + 0.3 + i * 0.35
            if key == 'ch3' and nm == 'you':
                ti = w(194.66) + 0.6
            u = ease_io5(ramp(t, ti, ti + 1.0))
            x = lerp(x0, bx, u); y = lerp(y0, by + 10, u) - math.sin(u * math.pi) * 120
            s = lerp(1.0, 0.25, u)
            al = sa * (1 - ramp(u, 0.9, 1.0))
            if al <= 0:
                continue
            if nm == 'moon':
                moon(c, x, y, al, 48 * s)
            elif nm == 'bird':
                draw_icon(c, bird_path(0.7), x, y, 2 * s, al, IVORY, 1.6)
            elif nm == 'house':
                house(c, x, y + 60 * s, al, 1, s)
            elif nm == 'cup':
                draw_icon(c, CUP, x, y, 0.6 * s, al, IVORY, 1.6)
            else:
                draw_icon(c, walker(0.25), x, y + 70 * s, 0.9 * s, al, IVORY, 1.8, glow=1.4)
        mono_label(c, 'SAVED', bx, by + 120, 16, sa * 0.7 * ease_out(ramp(t, T[8] + 1.8, T[8] + 2.4)), IVORY)
    # final chorus: world collapses to the horizon line at the end
    if key == 'ch3':
        col = ease_io(ramp(t, 196.0, 198.4))
        if col > 0:
            c.drawRect(skia.Rect(0, 0, W, H), fill_paint((10, 10, 11), col * 0.9))
            half = lerp(W / 2, 2, ease_io(ramp(t, 197.0, 198.6)))
            horizon(c, col, CX - half, CX + half)
    c.restore()


def city(c, t, A, a, T):
    """CH2 variant: a skyline whose windows switch off; the camera pans slowly"""
    pan = (t - T[0]) * 18
    rng = np.random.default_rng(12)
    stars(c, t, a * 0.6, T[1] + 0.1)
    moon(c, 1500 - pan * 0.2, 200, a * (1 - 0.6 * ease_io(ramp(t, T[3], T[3] + 2.5))))
    x = -pan % 1 - 200
    bi = int(pan // 1)
    xs = 0
    k = 0
    xpos = -200 - (pan % 2400)
    while xpos < W + 200:
        r = rng.random(3)
        bw = 120 + r[0] * 140
        bh = 140 + r[1] * 300
        p = P(); p.moveTo(xpos, HZ); p.lineTo(xpos, HZ - bh); p.lineTo(xpos + bw, HZ - bh); p.lineTo(xpos + bw, HZ)
        glow_stroke(c, p, IVORY, a * 0.75, 1.3, 0.2)
        cols, rows = int(bw // 34), int(bh // 40)
        for j in range(rows):
            for i in range(cols):
                wx, wy = xpos + 14 + i * 34, HZ - bh + 18 + j * 40
                off_at = T[1] + ((k * 7 + i * 3 + j * 5) % 97) / 97 * (T[8] - T[1])
                on = t < off_at
                if (k + i + j) % 3 == 0:
                    continue
                if on:
                    c.drawRect(skia.Rect(wx, wy, wx + 14, wy + 18), fill_paint(IVORY, a * 0.6))
                else:
                    c.drawRect(skia.Rect(wx, wy, wx + 14, wy + 18), stroke_paint(SILVER, a * 0.25, 1.0))
        xpos += bw + 30 + r[2] * 60
        k += 1
        if xpos > W + 200 and False:
            break
    horizon(c, a)
    sea(c, t, a * 0.7, amp=0.6)


# ======================================================================= VERSE 2
def sec_v2(c, t, A):
    a_sec = sec_alpha(t, 89.0, 106.85, 0.4, 0.3)
    layer(c, a_sec)
    t_sky = lt('All the stars were just a skybox painted on a sphere')
    t_road = lt('All the roads you never took were never rendered here')
    t_dv = lt('Every déjà vu you had? A cache hit, dear')
    t_gc = lt('Every name you can’t remember? Garbage collected, clear')
    # skybox sphere
    sa = window(t, 89.0, t_road + 0.2, 0.4, 0.35)
    if sa > 0:
        R = 300
        rot = t * 0.35
        k = ease_io(ramp(t, 89.0, t_sky + 1.0))
        glow_stroke(c, circle(CX, CY, R), IVORY, sa * k, 1.5, 0.6)
        for i in range(1, 6):
            lat = -math.pi / 2 + i * math.pi / 6
            ry = R * math.cos(lat)
            yy = CY + R * math.sin(lat)
            p = P(); p.addOval(skia.Rect(CX - ry, yy - ry * 0.18, CX + ry, yy + ry * 0.18))
            c.drawPath(p, stroke_paint(SILVER, sa * k * 0.35, 1.0))
        for i in range(6):
            ang = rot + i * math.pi / 6
            rx = abs(math.cos(ang)) * R
            p = P(); p.addOval(skia.Rect(CX - rx, CY - R, CX + rx, CY + R))
            c.drawPath(p, stroke_paint(SILVER, sa * k * 0.35, 1.0))
        rr = np.random.default_rng(4)
        for i in range(70):
            lo, la = rr.random() * math.tau, math.asin(rr.random() * 2 - 1)
            x3 = math.cos(la) * math.cos(lo + rot); z3 = math.cos(la) * math.sin(lo + rot); y3 = math.sin(la)
            if z3 < 0:
                continue
            c.drawCircle(CX + x3 * R, CY + y3 * R, 2.0, fill_paint(IVORY, sa * k * (0.4 + 0.6 * z3)))
        mono_label(c, 'skybox.png  (4096 × 2048)', CX, CY + R + 50, 15, sa * 0.6 * ease_out(ramp(t, t_sky + 1.2, t_sky + 1.8)))
    # roads not taken
    ra = window(t, t_road - 0.1, t_dv + 0.2, 0.35, 0.35)
    if ra > 0:
        base = (CX, CY + 330)
        fork = (CX, CY + 80)
        k = ease_io(ramp(t, t_road - 0.1, t_road + 0.8))
        glow_stroke(c, trim(line(*base, *fork), 0, k), IVORY, ra, 2.2, 0.8)
        ends = [(CX - 520, CY - 220), (CX - 180, CY - 300), (CX + 200, CY - 300), (CX + 540, CY - 200)]
        for i, e in enumerate(ends):
            kk = ease_io(ramp(t, t_road + 0.5 + i * 0.15, t_road + 1.3 + i * 0.15))
            p = P(); p.moveTo(*fork); p.quadTo(e[0] * 0.3 + fork[0] * 0.7, fork[1] - 60, *e)
            taken = i == 2
            glow_stroke(c, trim(p, 0, kk), IVORY if taken else SILVER, ra * (1 if taken else 0.55),
                        2.2 if taken else 1.2, 0.8 if taken else 0, dash=None if taken else ([6, 9], 0))
            if not taken and kk > 0.95:
                # unrendered placeholder: checkerboard-ish grid
                for gx in range(3):
                    for gy in range(3):
                        if (gx + gy) % 2 == 0:
                            c.drawRect(skia.Rect(e[0] - 30 + gx * 20, e[1] - 30 + gy * 20, e[0] - 10 + gx * 20, e[1] - 10 + gy * 20),
                                       stroke_paint(SILVER, ra * 0.4, 1.0))
                mono_label(c, 'not rendered', e[0], e[1] + 54, 12, ra * 0.5)
    # deja vu: two identical frames converge
    da = window(t, t_dv - 0.1, t_gc + 0.2, 0.35, 0.35)
    if da > 0:
        conv = ease_io5(ramp(t, t_dv + 0.3, t_dv + 1.8))
        for s in (-1, 1):
            x = CX + s * 260 * (1 - conv)
            glow_stroke(c, rrect(x, CY - 20, 420, 300, 10), IVORY if s > 0 else COOL, da * 0.8, 1.4, 0.5)
            glow_stroke(c, line(x - 210, CY + 60, x + 210, CY + 60), SILVER, da * 0.6, 1.2, 0)
            draw_icon(c, walker(0.15), x - 60, CY + 60, 0.8, da * 0.85, IVORY if s > 0 else COOL, 1.6)
            moon(c, x + 120, CY - 110, da * 0.8, 22)
        if conv > 0.9:
            stamp(c, 'CACHE HIT', CX + 230, CY - 200, ease_out(ramp(t, t_dv + 1.8, t_dv + 2.1)) * da, IVORY)
    # garbage collected names
    ga = window(t, t_gc - 0.1, 106.9, 0.35, 0.35)
    if ga > 0:
        names = ['the bartender in Lisbon', 'your third-grade teacher', 'the song from the wedding',
                 'that kid from summer camp', 'the street with the blue door']
        for i, nm in enumerate(names):
            y = CY - 170 + i * 66
            ti = t_gc + 0.1 + i * 0.12
            sweep = ease_in(ramp(t, t_gc + 1.6 + i * 0.25, t_gc + 2.4 + i * 0.25))
            if t < ti:
                continue
            tw = text_width(nm, TF_SERIF_I, 40)
            # dissolve into particles moving right
            if sweep < 1:
                c.save(); c.clipRect(skia.Rect(CX - tw / 2 + tw * sweep, y - 50, W, y + 20))
                draw_text(c, nm, CX, y, TF_SERIF_I, 40, IVORY, ga * ease_out(ramp(t, ti, ti + 0.3)))
                c.restore()
            if 0 < sweep:
                rr = np.random.default_rng(i)
                for p_ in range(40):
                    px = CX - tw / 2 + rr.random() * tw * sweep
                    drift = (t - (t_gc + 1.6 + i * 0.25)) * (120 + rr.random() * 260)
                    c.drawCircle(px + drift, y - 14 + (rr.random() - 0.5) * 30, 1.6,
                                 fill_paint(IVORY, ga * 0.6 * (1 - clamp(drift / 600))))
        mono_label(c, 'gc: freed 5 objects', CX, CY + 220, 15, ga * 0.6 * ease_out(ramp(t, t_gc + 2.6, t_gc + 3.0)))
    c.restore()


# ======================================================================= BRIDGE
def sec_bridge(c, t, A):
    a_sec = sec_alpha(t, 147.5, 163.4, 0.5, 0.05)
    layer(c, a_sec)
    t5 = lt('Closing connections… five'); t4 = lt('Releasing locks… four')
    t3 = lt('Unmounting the sky… three'); t2 = lt('Detaching the sea… two'); t1 = lt('Goodbye, process one.')
    nums = [(t5, '5', 1.4), (t4, '4', 1.4), (t3, '3', 1.4), (t2, '2', 1.4), (t1, '1', 1.4)]
    for (ts, n, dly) in nums:
        nt = ts + dly
        nxt = [x[0] for x in nums if x[0] > ts]
        end = (nxt[0] + 0.1) if nxt else 163.5
        a = window(t, nt, end, 0.08, 0.3)
        if a > 0:
            slam_text(c, n, 420, 300, t, nt, 220, IVORY, a * 0.9)
    # sky + sea world as context
    sky_lift = ease_in(ramp(t, t3 + 0.4, t3 + 2.0))
    sea_det = ease_in(ramp(t, t2 + 0.4, t2 + 2.2))
    c.save(); c.translate(0, -sky_lift * 700)
    stars(c, t, 0.8)
    moon(c, 1420, 220, 0.8)
    if t > t3:
        arc = P(); arc.addArc(skia.Rect(-200, 60, W + 200, 1220), 180, 180)
        glow_stroke(c, arc, SILVER, 0.5 * window(t, t3, t2, 0.2, 0.3), 1.2, 0.3, dash=([6, 8], 0))
        mono_label(c, 'umount /sky', CX, 120, 16, 0.6 * window(t, t3 + 0.2, t2, 0.2, 0.3))
    c.restore()
    horizon(c, 1 - 0.3 * sea_det)
    sea(c, t, 1.0, detach=sea_det)
    if t > t2 + 0.3:
        mono_label(c, 'detach /dev/sea', CX, HZ + 90, 16, 0.6 * window(t, t2 + 0.3, t1, 0.2, 0.3))
    # connections
    ca = window(t, t5 - 0.2, t4 + 0.3, 0.3, 0.3)
    if ca > 0:
        rr = np.random.default_rng(2)
        pts = [(260 + rr.random() * 1400, 200 + rr.random() * 380) for _ in range(14)]
        k = 0
        for i in range(14):
            for j in range(i + 1, 14):
                if (i * 7 + j) % 4:
                    continue
                cut = t5 + 0.5 + k * 0.12
                k += 1
                snap = ramp(t, cut, cut + 0.25)
                a_ = ca * (1 - snap) * 0.6
                if a_ > 0.01:
                    x0, y0 = pts[i]; x1, y1 = pts[j]
                    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
                    gap = snap * 40
                    c.drawPath(line(x0, y0, mx - gap, my), stroke_paint(SILVER, a_, 1.0))
                    c.drawPath(line(mx + gap, my, x1, y1), stroke_paint(SILVER, a_, 1.0))
        for (x, y) in pts:
            glow_stroke(c, circle(x, y, 6), IVORY, ca * 0.8, 1.2, 0.4)
    # locks
    la = window(t, t4 - 0.1, t3 + 0.3, 0.3, 0.3)
    if la > 0:
        for i in range(5):
            x = 420 + i * 270
            op = ease_out(ramp(t, t4 + 0.4 + i * 0.22, t4 + 0.8 + i * 0.22))
            draw_icon(c, padlock(op), x, CY - 40, 1.0, la, IVORY, 1.8, glow=0.6 + op)
    # process one
    pa = window(t, t1 - 0.1, 163.6, 0.3, 0.05)
    if pa > 0:
        pulse = 0.6 + 0.4 * math.sin(t * 6)
        c.drawCircle(CX, CY, 8, fill_paint(IVORY, pa))
        c.drawCircle(CX, CY, 40, fill_paint(IVORY, pa * 0.15 * pulse, blur=16))
        mono_label(c, 'pid 1', CX, CY + 50, 15, pa * 0.6)
    c.restore()


# ======================================================================= OUTRO
def sec_outro(c, t, A):
    a_sec = sec_alpha(t, 198.6, END, 0.4, 0.01)
    layer(c, a_sec)
    t_pe = lt('Process exited'); t_cz = lt('with code zero'); t_ne = lt('No errors'); t_ok = lt('You did everything right')
    fade_all = ease_io(ramp(t, 211.2, 212.4))
    # tiny horizon dot
    da = (1 - fade_all)
    c.drawCircle(CX, HZ, 3, fill_paint(IVORY, da * 0.9))
    c.drawCircle(CX, HZ, 18, fill_paint(IVORY, da * 0.12, blur=8))
    logs = [(t_pe + 0.2, '[ 1043.592] world.service: deactivated successfully'),
            (t_cz + 0.2, '[ 1043.592] exit status 0'),
            (t_ne + 0.2, '[ 1043.593] errors: 0'),
            (t_ok + 0.2, '[ 1043.593] you did everything right')]
    for i, (ts, s) in enumerate(logs):
        typed(c, s, 380, 270 + i * 48, t, ts, 40, 24, 0.85 * da, IVORY if i == 3 else SILVER, align='left',
              caret=(i == 3))
    ea = window(t, 212.6, END + 1, 0.8, 0.01)
    if ea > 0:
        draw_text(c, 'aditazzz', CX, CY + 10, TF_MONO, 34, IVORY, ea, tracking=12, glow=0.4)
        mono_label(c, 'GRACEFUL SHUTDOWN', CX, CY + 62, 16, ea * 0.7, SILVER, tracking=7)
        mono_label(c, 'DEADLETTER', CX, H - 90, 12, ea * 0.4, SILVER, tracking=9)
    c.restore()


SECTION_FN = {
    'intro': sec_intro, 'v1': sec_v1, 'pre1': lambda c, t, A: sec_pre(c, t, A, 1),
    'ch1': lambda c, t, A: sec_chorus(c, t, A, 'ch1'), 'v2': sec_v2, 'pre2': lambda c, t, A: sec_pre(c, t, A, 2),
    'ch2': lambda c, t, A: sec_chorus(c, t, A, 'ch2'), 'bridge': sec_bridge,
    'ch3': lambda c, t, A: sec_chorus(c, t, A, 'ch3'), 'outro': sec_outro,
}
