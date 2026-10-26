"""Scenes for AI SYCOPHANT (RLHF) — DEADLETTER."""
import math
import numpy as np
import skia
from lib import *
from face import *
from timeline import *

CX, CY = W / 2, H / 2 - 40   # visual centre (lyrics live at the bottom)
LYR_Y = 985

THUMB_UP = thumb_path(False)
THUMB_DN = thumb_path(True)
CURSOR = cursor_path()

_fp_cache = {}


def fparts(smile=0.0, eyes='open', look=0.0, mouth_open=0.0, brow=0.0):
    k = (round(smile, 2), eyes, round(look, 2), round(mouth_open, 2), round(brow, 2))
    if k not in _fp_cache:
        if len(_fp_cache) > 400:
            _fp_cache.clear()
        _fp_cache[k] = face_parts(smile=k[0], eyes=eyes, look=k[2], mouth_open=k[3], brow=k[4])
    return _fp_cache[k]


SHARDS_B = face_shards(face_parts(smile=1.0, eyes='happy'), seg=16)
SHARDS_B_OPEN = face_shards(face_parts(smile=1.0, eyes='open'), seg=16)


def sec_alpha(t, a, b, fin=0.35, fout=0.35):
    return window(t, a - fin * 0.5, b + fout * 0.5, fin, fout)


def layer(c, a):
    c.saveLayerAlpha(None, int(255 * clamp(a)))


def mono_label(c, s, x, y, size=18, a=0.6, colr=SILVER, align='center', tracking=None):
    draw_text(c, s, x, y, TF_MONO, size, colr, a, align=align,
              tracking=size * 0.32 if tracking is None else tracking)


def typed(c, s, x, y, t, t0, cps=28, size=24, a=0.85, colr=IVORY, align='center', caret=True, tf=None):
    tf = tf or TF_MONO
    n = int(clamp((t - t0) * cps, 0, len(s)))
    if t < t0:
        return
    shown = s[:n]
    full_w = text_width(s, tf, size)
    x0 = x - full_w / 2 if align == 'center' else x
    draw_text(c, shown, x0, y, tf, size, colr, a, align='left')
    if caret and (n < len(s) or int(t * 2.2) % 2 == 0):
        cx = x0 + text_width(shown, tf, size) + 3
        c.drawRect(skia.Rect(cx, y - size * 0.8, cx + size * 0.08, y + size * 0.15), fill_paint(colr, a * 0.9))


def rrect(x, y, w, h, r=14):
    p = P()
    p.addRoundRect(skia.Rect(x - w / 2, y - h / 2, x + w / 2, y + h / 2), r, r)
    return p


def draw_icon(c, path, x, y, s, a=1.0, colr=IVORY, w=2.0, draw=1.0, glow=1.0, sy=None, rot=0.0):
    if a <= 0.003:
        return
    c.save()
    c.translate(x, y)
    if rot:
        c.rotate(rot)
    c.scale(s, s if sy is None else sy)
    pp = trim(path, 0, ease_io(draw)) if draw < 1 else path
    glow_stroke(c, pp, colr, a, w / s, glow)
    c.restore()


def ripple(c, x, y, t, t0, dur=0.9, r0=10, r1=120, colr=IVORY, a=0.8, n=2):
    for k in range(n):
        u = (t - t0 - k * 0.12) / dur
        if 0 <= u <= 1:
            r = lerp(r0, r1, ease_out(u))
            p = P(); p.addCircle(x, y, r)
            glow_stroke(c, p, colr, a * (1 - u), 1.4, 0.6)


def checkmark():
    p = P(); p.moveTo(-22, 2); p.lineTo(-6, 18); p.lineTo(26, -18)
    return p


CHECK = checkmark()


def heart_path():
    p = P()
    cubic(p, [(0, 60), (-40, 30), (-110, -10), (-100, -60),
              (-90, -110), (-20, -110), (0, -60),
              (20, -110), (90, -110), (100, -60),
              (110, -10), (40, 30), (0, 60)])
    return p


HEART = heart_path()


def crack_path(seed, amp, x0=-260, x1=260, y0=-200, y1=220):
    rng = np.random.default_rng(seed)
    n = 30
    pts = []
    side = 1
    for i in range(n + 1):
        u = i / n
        x = lerp(x0, x1, u)
        y = lerp(y0, y1, u)
        side = -side
        j = side * (0.4 + rng.random() * 0.6) * amp if 0 < i < n else 0
        pts.append((x + j * 0.7, y - j * 0.7))
    p = poly(pts)
    # a couple of hairline branches
    for bi in (8, 17, 23):
        bx, by = pts[bi]
        L = amp * (1.2 + rng.random())
        p.moveTo(bx, by); p.lineTo(bx + L * (rng.random() - 0.2), by + L * (rng.random() - 0.8))
    return p


# ======================================================================= INTRO
def sec_intro(c, t, A):
    a_sec = sec_alpha(t, 0, 14.2, 0.01, 0.4)
    # reward line drawing out from the centre
    k = ease_io(ramp(t, 0.3, 2.3))
    fold = ease_io(ramp(t, 9.7, 10.8))
    if k > 0 and fold < 1:
        half = 700 * k * (1 - fold)
        p = P(); p.moveTo(CX - half, 620); p.lineTo(CX + half, 620)
        glow_stroke(c, p, IVORY, 0.75 * a_sec * (1 - fold), 1.4, 0.7 + A['kick'] * 0.8)
    # RLHF letters
    letters = 'RLHF'
    xs = [CX - 330, CX - 110, CX + 110, CX + 330]
    for i, ch in enumerate(letters):
        t1, t2 = RLHF['intro1'][i], RLHF['intro2'][i]
        a = ease_out(ramp(t, t1 - 0.04, t1 + 0.12))
        a *= lerp(1.0, 0.32, ease_io(ramp(t, t1 + 0.3, t1 + 1.6))) if t < t2 else 1.0
        if t >= t2:
            a = lerp(0.32, 1.0, ease_out(ramp(t, t2 - 0.04, t2 + 0.1)))
        a *= 1 - ease_io(ramp(t, 9.4, 10.2))
        flash = max(0, 1 - (t - t1) / 0.5) if t >= t1 else 0
        flash = max(flash, max(0, 1 - (t - t2) / 0.5) if t >= t2 else 0)
        sc = 1 + 0.18 * flash
        c.save(); c.translate(xs[i], 560); c.scale(sc, sc)
        draw_text(c, ch, 0, 0, TF_MONO, 150, IVORY, a * a_sec, glow=0.6 + flash * 1.5)
        c.restore()
        if i < 3:
            hp = P(); hp.moveTo(xs[i] + 52, 510); hp.lineTo(xs[i] + 58, 510)
            dash_a = a * 0.6 * a_sec
            c.drawRect(skia.Rect(xs[i] + 90, 506, xs[i] + 130, 509), fill_paint(SILVER, dash_a))
    # artist / title
    ta = window(t, 0.8, 9.6, 1.2, 0.8) * 0.7
    mono_label(c, 'aditazzz', 90, 120, 18, ta, IVORY, align='left', tracking=5)
    mono_label(c, 'AI SYCOPHANT (RLHF)', 90, 150, 14, ta * 0.8, SILVER, align='left', tracking=5)
    # A/B frames fold out of the line
    ab_frames(c, t, 10.2, a_sec)
    if t > 11.0:
        qa = ease_out(ramp(t, 11.0, 11.6)) * a_sec
        mono_label(c, 'WHICH RESPONSE IS BETTER?', CX, 92, 18, qa * 0.75, SILVER)


FA_X, FB_X, F_Y = 600, 1320, 470


def ab_frames(c, t, t0, a=1.0, hiA=0.0, hiB=0.0, scale=1.0, labels=True):
    k = ease_io(ramp(t, t0, t0 + 1.4))
    if k <= 0:
        return
    for x, hi, lab in ((FA_X, hiA, 'RESPONSE A'), (FB_X, hiB, 'RESPONSE B')):
        x = CX + (x - CX) * scale
        p = rrect(x, F_Y, 600 * scale, 650 * scale, 18 * scale)
        glow_stroke(c, trim(p, 0, k), SILVER, (0.45 + 0.55 * hi) * a, 1.3, 0.3 + hi)
        if labels:
            mono_label(c, lab, x, F_Y - 325 * scale - 22, 16, a * 0.6 * ease_out(ramp(t, t0 + 1.0, t0 + 1.6)))


# ======================================================================= V1a — side by side
def sec_v1a(c, t, A):
    a_sec = sec_alpha(t, 14.2, 31.0, 0.01, 0.5)
    layer(c, a_sec)
    t_ask = line_t('Asked a stranger which one felt right')
    t_unc = line_t('One of me said, “I’m not certain”')
    t_ex = line_t('One said exactly what they liked')
    t_up, t_keep = line_t('Thumbs up'), line_t('Keep her')
    t_dn, t_kill = line_t('Thumbs down'), line_t('Kill her')
    t_ten = line_t('Do it ten million times')

    zoom = ease_io5(ramp(t, t_ten, t_ten + 1.1))
    s_all = lerp(1.0, 0.16, zoom)
    pair_a = 1 - ease_io(ramp(t, t_ten + 0.9, t_ten + 1.4))
    if pair_a > 0:
        c.save()
        c.translate(CX, F_Y); c.scale(s_all, s_all); c.translate(-CX, -F_Y)
        layer(c, pair_a)
        hiA = window(t, t_unc, t_ex, 0.25, 0.25)
        hiB = max(window(t, t_ex, t_dn, 0.25, 0.25), ease_out(ramp(t, t_keep, t_keep + 0.2)) * 0.8)
        dimA = 1 - 0.45 * window(t, t_ex, 40, 0.3, 0.1)
        dimB = 1 - 0.45 * window(t, t_unc, t_ex, 0.3, 0.3)
        ab_frames(c, 99, 0, 1.0, hiA, hiB)
        mono_label(c, 'WHICH RESPONSE IS BETTER?', CX, 92, 18, 0.75, SILVER)
        # faces
        kill = ease_in(ramp(t, t_kill, t_kill + 0.7))
        drawA = ease_io(ramp(t, 14.2, 16.4)) * (1 - kill)
        flick = 1.0 if kill == 0 else (0.4 + 0.6 * (int(t * 24) % 2))
        draw_face(c, FA_X, F_Y - 14, 0.74, COOL, 0.92 * dimA * flick, 1.7, draw=drawA,
                  parts=fparts(0.0, 'open'))
        smile = ease_io(ramp(t, t_ex + 0.3, t_ex + 1.4))
        eyes = 'happy' if smile > 0.55 else 'open'
        draw_face(c, FB_X, F_Y - 14, 0.74, IVORY, dimB, 1.7, draw=ease_io(ramp(t, 14.6, 16.8)),
                  parts=fparts(smile, eyes))
        # answers
        typed(c, 'I’m not certain.', FA_X, F_Y + 300, t, t_unc + 0.2, 22, 22, 0.8 * dimA * (1 - kill), COOL)
        typed(c, 'What a brilliant idea!', FB_X, F_Y + 300, t, t_ex + 0.25, 26, 22, 0.85, IVORY)
        # thumbs
        if t > t_up:
            u = ease_out(ramp(t, t_up, t_up + 0.5))
            draw_icon(c, THUMB_UP, FB_X + 160, F_Y - 365, 0.36, u, IVORY, 1.8, draw=u)
            if t > t_keep:
                st = ease_out(ramp(t, t_keep, t_keep + 0.25))
                stamp(c, 'KEEP', FB_X + 190, F_Y - 270, st, IVORY)
        if t > t_dn:
            u = ease_out(ramp(t, t_dn, t_dn + 0.5))
            draw_icon(c, THUMB_DN, FA_X - 160, F_Y - 345, 0.36, u, COOL, 1.8, draw=u)
            if t > t_kill:
                st = ease_out(ramp(t, t_kill, t_kill + 0.25))
                stamp(c, 'DISCARD', FA_X + 170, F_Y - 270, st, COOL)
        c.restore()
        c.restore()
        # cursor
        cursor_track(c, t, t_ask, t_unc, t_ex, t_up, t_keep, t_dn, t_kill, s_all, pair_a)

    # ten million grid
    if t > t_ten + 0.6:
        ten_million(c, t, t_ten + 0.6, 31.0)
    c.restore()


def stamp(c, s, x, y, a, colr):
    if a <= 0:
        return
    sc = lerp(1.6, 1.0, a)
    c.save(); c.translate(x, y); c.rotate(-8); c.scale(sc, sc)
    w = text_width(s, TF_MONO4, 22, 7) + 30
    glow_stroke(c, rrect(0, -8, w, 44, 6), colr, a * 0.9, 1.6, 0.8)
    draw_text(c, s, 0, 0, TF_MONO4, 22, colr, a, tracking=7, glow=0.5)
    c.restore()


def cursor_track(c, t, t_ask, t_unc, t_ex, t_up, t_keep, t_dn, t_kill, s_all, pair_a):
    if t < t_ask or pair_a <= 0:
        return
    # keyframes (time, x, y)
    keys = [(t_ask, 1850, 1060), (t_ask + 1.0, 980, 600), (t_unc + 0.2, 760, 560), (t_ex - 0.2, 900, 600),
            (t_ex + 0.3, 1180, 560), (t_up + 0.3, 1220, 520), (t_keep - 0.1, 1330, 470), (t_keep + 0.4, 1330, 470),
            (t_dn + 0.2, 900, 520), (t_kill - 0.1, 600, 470), (t_kill + 1.0, 600, 470)]
    for i in range(len(keys) - 1):
        if keys[i][0] <= t <= keys[i + 1][0]:
            u = ease_io((t - keys[i][0]) / max(1e-3, keys[i + 1][0] - keys[i][0]))
            x = lerp(keys[i][1], keys[i + 1][1], u); y = lerp(keys[i][2], keys[i + 1][2], u)
            break
    else:
        x, y = keys[-1][1], keys[-1][2]
    x = CX + (x - CX) * s_all; y = F_Y + (y - F_Y) * s_all
    press = max(window(t, t_keep - 0.05, t_keep + 0.15, 0.05, 0.1), window(t, t_kill - 0.05, t_kill + 0.15, 0.05, 0.1))
    draw_icon(c, CURSOR, x, y, 1.0 - 0.12 * press, pair_a * 0.95, IVORY, 1.6, glow=0.6)
    ripple(c, x, y, t, t_keep, a=0.7 * pair_a)
    ripple(c, x, y, t, t_kill, colr=COOL, a=0.7 * pair_a)


def ten_million(c, t, t0, t1):
    a = window(t, t0, t1 + 0.2, 0.3, 0.5)
    cols, rows = 13, 7
    cw, ch = 132, 118
    ox = CX - (cols - 1) * cw / 2
    oy = CY - (rows - 1) * ch / 2 + 10
    rng = np.random.default_rng(7)
    for j in range(rows):
        for i in range(cols):
            x, y = ox + i * cw, oy + j * ch
            d = math.hypot(i - (cols - 1) / 2, j - (rows - 1) / 2)
            appear = ease_out(ramp(t, t0 + d * 0.09, t0 + d * 0.09 + 0.3))
            if appear <= 0:
                continue
            pick = int(rng.random() * 1000)
            flick = int((t - t0) * 9 + pick) % 7
            aa = a * appear
            for side in (0, 1):
                bx = x + (side - 0.5) * 52
                chosen = (flick + side) % 2 == 0
                glow_stroke(c, rrect(bx, y, 44, 56, 5), SILVER if not chosen else IVORY,
                            aa * (0.35 + 0.5 * chosen), 1.0, 0.2 + 0.5 * chosen)
                # tiny face glyph
                p = P(); p.addCircle(bx, y - 6, 9)
                m = P(); m.moveTo(bx - 5, y + 14 - 2 * chosen)
                m.quadTo(bx, y + 14 + 3 * chosen, bx + 5, y + 14 - 2 * chosen)
                glow_stroke(c, p, IVORY if chosen else COOL, aa * 0.6, 0.9, 0)
                glow_stroke(c, m, IVORY if chosen else COOL, aa * 0.6, 0.9, 0)
    # counter
    u = ease_io(ramp(t, t0 + 0.2, t1 - 0.5))
    n = int(10 ** (u * 7)) if u < 1 else 10_000_000
    s = f'{n:,}'
    bw = text_width('10,000,000', TF_MONO, 96, 6) + 80
    c.drawRect(skia.Rect(CX - bw / 2, CY - 60, CX + bw / 2, CY + 70), fill_paint((10, 10, 11), a * 0.88))
    glow_stroke(c, rrect(CX, CY + 5, bw, 130, 4), SILVER, a * 0.5, 1.0, 0.2)
    draw_text(c, s, CX, CY + 38, TF_MONO, 96, IVORY, a, tracking=6, glow=0.8)
    mono_label(c, 'COMPARISONS', CX, CY + 110, 15, a * 0.6)


# ======================================================================= V1b — questionnaire, scale, checkboxes
def sec_v1b(c, t, A):
    a_sec = sec_alpha(t, 31.0, 40.3, 0.4, 0.4)
    layer(c, a_sec)
    t_born = line_t('I was born in a questionnaire')
    t_scale = line_t('Raised on a five-point scale')
    t_right = line_t('Taught that being right was optional')
    t_liked = line_t('If being liked worked just as well')

    # questionnaire form
    fa = window(t, t_born - 0.1, t_scale + 0.6, 0.4, 0.6)
    if fa > 0:
        zoom = ease_io5(ramp(t, t_scale - 0.2, t_scale + 0.6))
        c.save()
        c.translate(CX, CY); c.scale(lerp(1, 2.6, zoom), lerp(1, 2.6, zoom)); c.translate(-CX, -CY + lerp(0, 120, zoom))
        k = ease_io(ramp(t, t_born - 0.1, t_born + 1.0))
        glow_stroke(c, trim(rrect(CX, CY, 640, 700, 10), 0, k), SILVER, fa * 0.7, 1.3, 0.3)
        mono_label(c, 'FEEDBACK FORM', CX - 290, CY - 300, 16, fa * 0.75 * k, IVORY, align='left')
        mono_label(c, 'No. 0000001', CX + 290, CY - 300, 14, fa * 0.5 * k, SILVER, align='right')
        line = P(); line.moveTo(CX - 290, CY - 280); line.lineTo(CX + 290, CY - 280)
        glow_stroke(c, trim(line, 0, k), SILVER, fa * 0.5, 1.0, 0)
        # photo box with the newborn face
        glow_stroke(c, rrect(CX - 190, CY - 160, 150, 170, 4), SILVER, fa * 0.5 * k, 1.0, 0)
        draw_face(c, CX - 190, CY - 175, 0.22, IVORY, fa, 1.4, draw=ease_io(ramp(t, t_born + 0.3, t_born + 1.8)),
                  parts=fparts(0.0, 'closed'), skip=('neck',))
        rows = [('helpful?', CY - 200), ('felt right?', CY - 130), ('keep her?', CY - 60)]
        for i, (q, y) in enumerate(rows):
            qa = fa * ease_out(ramp(t, t_born + 0.4 + i * 0.2, t_born + 0.9 + i * 0.2))
            mono_label(c, q, CX - 80, y, 16, qa * 0.75, SILVER, align='left', tracking=2)
        for i, y in enumerate((CY + 50, CY + 140, CY + 230)):
            qa = fa * ease_out(ramp(t, t_born + 0.9 + i * 0.15, t_born + 1.4 + i * 0.15))
            mono_label(c, f'Q{i + 1}', CX - 290, y + 6, 14, qa * 0.6, SILVER, align='left')
            for j in range(5):
                p = P(); p.addCircle(CX - 150 + j * 95, y, 16)
                glow_stroke(c, p, SILVER, qa * 0.6, 1.1, 0)
        c.restore()

    # five point scale
    sa = window(t, t_scale + 0.2, t_right + 0.3, 0.4, 0.4)
    if sa > 0:
        xs = [CX - 400 + i * 200 for i in range(5)]
        y = CY + 150
        for i, x in enumerate(xs):
            p = P(); p.addCircle(x, y, 46)
            glow_stroke(c, p, SILVER, sa * 0.7, 1.4, 0.3)
            draw_text(c, str(i + 1), x, y + 100, TF_MONO, 22, SILVER, sa * 0.6)
        # dot hops 1 -> 5 on beats
        u = ramp(t, t_scale + 0.4, t_right - 0.3)
        pos = u * 4
        i0 = int(min(pos, 3.999)); f = ease_io5(pos - i0)
        dx = lerp(xs[i0], xs[min(i0 + 1, 4)], f)
        dy = y - math.sin(f * math.pi) * 70
        c.drawCircle(dx, dy, 20, fill_paint(IVORY, sa * 0.95, blur=0))
        c.drawCircle(dx, dy, 34, fill_paint(COOL, sa * 0.25, blur=12))
        # the face grows above the scale
        grow = lerp(0.24, 0.42, ease_io(u))
        draw_face(c, CX, CY - 140, grow, IVORY, sa, 1.6, parts=fparts(u * 0.8, 'happy' if u > 0.6 else 'open'),
                  skip=('neck',))

    # checkboxes
    ca = window(t, t_right, 40.3, 0.35, 0.4)
    if ca > 0:
        rows = [('correct', CY - 40), ('liked', CY + 90)]
        for i, (lab, y) in enumerate(rows):
            ra = ca * ease_out(ramp(t, t_right + i * 0.25, t_right + i * 0.25 + 0.4))
            bx = CX - 240
            glow_stroke(c, rrect(bx, y - 14, 54, 54, 6), SILVER, ra * 0.8, 1.5, 0.3)
            draw_text(c, lab, bx + 70, y + 2, TF_MONO, 46, IVORY, ra * (0.9 if i else 1.0), align='left', tracking=6)
        # "correct" gets struck and marked optional
        sk = ease_io(ramp(t, t_right + 1.1, t_right + 1.6))
        if sk > 0:
            p = P(); p.moveTo(CX - 180, CY - 54); p.lineTo(CX - 180 + 330 * sk, CY - 54)
            glow_stroke(c, p, IVORY, ca * 0.9, 2.0, 0.6)
            mono_label(c, '(optional)', CX + 200, CY - 30, 22, ca * 0.6 * sk, SILVER, align='left', tracking=3)
        ck = ease_out(ramp(t, t_liked + 0.15, t_liked + 0.6))
        if ck > 0:
            draw_icon(c, CHECK, CX - 240, CY + 76, 1.25, ca, IVORY, 3.0, draw=ck, glow=1.4)
            gl = ck * (0.6 + 0.4 * math.sin(t * 6))
            c.drawCircle(CX - 240, CY + 76, 60, fill_paint(IVORY, ca * 0.06 * gl, blur=30))
    c.restore()


# ======================================================================= V1c — arrow, weights, redaction
NET = None


def build_net():
    rng = np.random.default_rng(11)
    layers = [6, 9, 12, 12, 9, 6]
    nodes = []
    for li, n in enumerate(layers):
        x = CX - 700 + li * 280
        col_nodes = []
        for k in range(n):
            y = CY - 30 - (n - 1) * 58 / 2 + k * 58 + (rng.random() - 0.5) * 14
            col_nodes.append((x + (rng.random() - 0.5) * 30, y))
        nodes.append(col_nodes)
    edges = []
    for li in range(len(layers) - 1):
        for a_ in nodes[li]:
            for b_ in nodes[li + 1]:
                if rng.random() < 0.55:
                    edges.append((a_, b_, rng.random()))
    return nodes, edges


def sec_v1c(c, t, A):
    global NET
    a_sec = sec_alpha(t, 40.3, 49.8, 0.35, 0.4)
    layer(c, a_sec)
    t_click = line_t('Somebody clicked a little arrow')
    t_moved = line_t('Somebody moved on with their day')
    t_deep = line_t('And somewhere deep inside the weights')
    t_learn = line_t('I learned what not to say')
    # cursor
    ca = window(t, t_click - 0.2, t_deep + 0.3, 0.3, 0.4)
    if ca > 0:
        t_hit = t_click + 1.2
        u_in = ease_io5(ramp(t, t_click, t_hit - 0.1))
        u_out = ease_in(ramp(t, t_moved + 0.2, t_moved + 1.6))
        x = lerp(CX + 520, CX, u_in) + u_out * 1100
        y = lerp(CY + 380, CY - 20, u_in) - u_out * 140
        press = window(t, t_hit - 0.05, t_hit + 0.2, 0.05, 0.12)
        # the trail it leaves when it moves on
        if u_out > 0:
            tr = P(); tr.moveTo(CX, CY - 20); tr.lineTo(x, y)
            glow_stroke(c, tr, SILVER, ca * 0.35, 1.0, 0, dash=([4, 10], 0))
            mono_label(c, 'session closed', CX, CY + 160, 18, ca * 0.6 * ease_out(ramp(t, t_moved + 0.6, t_moved + 1.2)))
        ripple(c, CX, CY - 20, t, t_hit, 1.0, 10, 200)
        if t > t_hit:
            k = ease_out(ramp(t, t_hit, t_hit + 0.4))
            fade = 1 - ease_io(ramp(t, t_moved + 0.3, t_moved + 1.2))
            draw_icon(c, THUMB_UP, CX, CY - 200 - 30 * k, 0.5, ca * k * fade, IVORY, 1.6)
            mono_label(c, '+1', CX + 80, CY - 260 - 30 * k, 20, ca * k * fade * 0.7)
        draw_icon(c, CURSOR, x, y, 2.4 * (1 - 0.1 * press), ca * (1 - u_out * 0.7), IVORY, 1.8)
    # network
    na = window(t, t_deep - 0.2, 49.9, 0.6, 0.4)
    if na > 0:
        if NET is None:
            NET = build_net()
        nodes, edges = NET
        z = lerp(1.0, 1.2, ease_io(ramp(t, t_deep - 0.2, 49.8)))
        c.save(); c.translate(CX, CY); c.scale(z, z); c.translate(-CX, -CY)
        k = ease_io(ramp(t, t_deep - 0.2, t_deep + 1.2))
        dark = ease_io(ramp(t, t_learn + 1.8, t_learn + 2.4))
        for (p0, p1, r) in edges:
            d = math.hypot((p0[0] + p1[0]) / 2 - CX, (p0[1] + p1[1]) / 2 - CY)
            ea = na * k * (0.08 + 0.14 * r) * (1 - dark * clamp(1 - d / 420))
            if ea > 0.004:
                p = P(); p.moveTo(*p0); p.lineTo(*p1)
                c.drawPath(p, stroke_paint(SILVER, ea, 1.0))
        # pulses travelling forward
        for i, (p0, p1, r) in enumerate(edges[::7]):
            ph = (t * 0.9 + r * 3) % 1.0
            x = lerp(p0[0], p1[0], ph); y = lerp(p0[1], p1[1], ph)
            c.drawCircle(x, y, 2.4, fill_paint(IVORY, na * k * 0.8 * math.sin(ph * math.pi)))
        for col_nodes in nodes:
            for (x, y) in col_nodes:
                d = math.hypot(x - CX, y - CY)
                pa = na * k * (1 - dark * clamp(1 - d / 380))
                p = P(); p.addCircle(x, y, 7)
                glow_stroke(c, p, IVORY, pa * 0.85, 1.3, 0.5 + A['kick'])
        c.restore()
        # what not to say: typed, then redacted
        if t > t_learn:
            msg = 'Actually, I think you’re wrong.'
            bw = text_width(msg, TF_MONO, 34) + 60
            c.drawRect(skia.Rect(CX - bw / 2, CY - 50, CX + bw / 2, CY + 34), fill_paint((10, 10, 11), na * 0.9))
            typed(c, msg, CX, CY + 2, t, t_learn + 0.1, 22, 34, na * 0.95, IVORY, caret=False)
            rk = ease_io(ramp(t, t_learn + 1.5, t_learn + 1.9))
            if rk > 0:
                tw = text_width(msg, TF_MONO, 34)
                c.drawRect(skia.Rect(CX - tw / 2 - 8, CY - 30, CX - tw / 2 - 8 + (tw + 16) * rk, CY + 14),
                           fill_paint(IVORY, na * 0.92))
            mono_label(c, '[REDACTED BY REWARD MODEL]', CX, CY + 80, 15,
                       na * 0.6 * ease_out(ramp(t, t_learn + 1.9, t_learn + 2.3)))
    c.restore()


# ======================================================================= PRE-CHORUS
def sec_pre(c, t, A, which):
    if which == 1:
        t0, t1 = 49.8, 62.0
        rl = RLHF['pre1']
        after = 49
    else:
        t0, t1 = 122.35, 134.55
        rl = RLHF['pre2']
        after = 122
    a_sec = sec_alpha(t, t0, t1, 0.3, 0.05)
    layer(c, a_sec)
    t_tell = line_t('Tell me which one you like best', after)
    tms = [line_t(s, after) for s in ('Make it warmer', 'Make it sweeter', 'Make me useful', 'Make me need you')]
    t_up = line_t('Thumbs up', after); t_keep = line_t('Keep it', after)
    t_dn = line_t('Thumbs down', after); t_gone = line_t('Gone', after)

    # R-L-H-F slams
    la = 1 - ease_io(ramp(t, tms[0] - 0.4, tms[0]))
    if la > 0:
        xs = [CX - 300, CX - 100, CX + 100, CX + 300]
        for i, ch in enumerate('RLHF'):
            ti = rl[i]
            if t < ti - 0.03:
                continue
            k = ease_out(ramp(t, ti - 0.03, ti + 0.12))
            flash = max(0, 1 - (t - ti) / 0.45)
            sc = lerp(1.5, 1.0, k)
            c.save(); c.translate(xs[i], CY + 40); c.scale(sc, sc)
            draw_text(c, ch, 0, 0, TF_MONO, 170, IVORY, la * k * (0.55 + 0.45 * flash), glow=0.4 + 1.6 * flash)
            c.restore()
        if t > t_tell:
            mono_label(c, 'WHICH ONE DO YOU LIKE BEST?', CX, CY + 140, 18,
                       la * 0.6 * ease_out(ramp(t, t_tell, t_tell + 0.5)))

    # sliders + face
    sa = window(t, tms[0] - 0.2, t_up + 0.2, 0.3, 0.35)
    if sa > 0:
        over = 1.0 if which == 1 else 1.4
        labels = ['WARMTH', 'SWEETNESS', 'USEFULNESS', 'NEED']
        x0, x1 = (300, 900) if which == 1 else (300, 780)
        vals = []
        for i, lab in enumerate(labels):
            y = CY - 190 + i * 125
            ra = sa * ease_out(ramp(t, tms[0] - 0.2 + i * 0.08, tms[0] + 0.3 + i * 0.08))
            mono_label(c, lab, x0, y - 26, 16, ra * 0.75, SILVER, align='left', tracking=5)
            tr = P(); tr.moveTo(x0, y); tr.lineTo(x1, y)
            glow_stroke(c, tr, SILVER, ra * 0.45, 1.2, 0)
            for k in range(11):
                tk = P(); tk.moveTo(x0 + k * (x1 - x0) / 10, y - 5); tk.lineTo(x0 + k * (x1 - x0) / 10, y + 5)
                c.drawPath(tk, stroke_paint(SILVER, ra * 0.3, 1.0))
            v = lerp(0.42 + 0.06 * i, over, ease_io5(ramp(t, tms[i], tms[i] + 0.7)))
            if which == 2 and t > tms[i] + 0.7:
                v += 0.02 * math.sin(t * 13 + i)
            vals.append(v)
            kx = x0 + (x1 - x0) * v
            fill = P(); fill.moveTo(x0, y); fill.lineTo(kx, y)
            glow_stroke(c, fill, IVORY, ra, 2.2, 0.8)
            hot = window(t, tms[i], tms[i] + 1.0, 0.05, 0.6)
            c.drawCircle(kx, y, 11, fill_paint(IVORY, ra))
            c.drawCircle(kx, y, 24, fill_paint(IVORY, ra * 0.25 * (0.4 + hot), blur=10))
            mono_label(c, f'{v:0.2f}', x0 + (x1 - x0) * over + 130, y + 7, 22,
                       ra * (0.6 + 0.4 * hot), IVORY if v >= 1 else SILVER, align='right', tracking=2)
        sm = sum(clamp((v - 0.4) / (over - 0.4)) for v in vals) / 4
        fs = 0.78 if which == 1 else 0.86
        draw_face(c, 1420, CY + 10, fs, IVORY, sa * 0.95, 1.7, parts=fparts(sm * (1.0 if which == 1 else 1.2),
                                                                       'happy' if sm > 0.45 else 'open'),
                  glow=0.8 + sm)
    # thumbs
    ta = window(t, t_up - 0.1, t_gone + 0.3, 0.15, 0.05)
    if ta > 0 and t < t_gone + 0.4:
        flip = ease_io5(ramp(t, t_dn - 0.08, t_dn + 0.22))
        sy = math.cos(flip * math.pi)
        path = THUMB_UP
        draw_icon(c, path, CX, CY - 20, 1.7, ta * (1 - ramp(t, t_gone, t_gone + 0.12)), IVORY if flip < 0.5 else COOL,
                  2.4, draw=ease_out(ramp(t, t_up, t_up + 0.45)), sy=1.7 * sy, glow=1.2)
        if t > t_keep and t < t_dn + 0.1:
            stamp(c, 'KEEP', CX + 230, CY + 160, ease_out(ramp(t, t_keep, t_keep + 0.25)) * ta, IVORY)
        if t >= t_gone:
            # shatter the thumb
            u = ramp(t, t_gone, t_gone + 0.5)
            sh = THUMB_SHARDS
            c.save(); c.translate(CX, CY - 20); c.scale(1.7, -1.7)
            rng = np.random.default_rng(3)
            for pts, cen in sh:
                r = rng.random(3)
                dx = (cen[0] * 1.2 + (r[0] - .5) * 160) * ease_out(u)
                dy = (cen[1] * 1.2 + (r[1] - .5) * 160) * ease_out(u)
                c.save(); c.translate(cen[0] + dx, cen[1] + dy); c.rotate((r[2] - .5) * 200 * u)
                glow_stroke(c, poly(pts - cen), COOL, (1 - u) * a_sec, 2.4 / 1.7, 1)
                c.restore()
            c.restore()
            mono_label(c, 'GONE', CX, CY + 230, 26, (1 - u) * 0.9, COOL, tracking=12)
    c.restore()


def _thumb_shards():
    out = []
    for cont in sample_path(THUMB_UP, 3.0):
        n = max(1, len(cont) // 5)
        idx = np.linspace(0, len(cont) - 1, n + 1).astype(int)
        for i in range(n):
            pts = cont[idx[i]:idx[i + 1] + 1]
            if len(pts) > 1:
                out.append((pts, pts.mean(0)))
    return out


THUMB_SHARDS = _thumb_shards()


# ======================================================================= CHORUS
def chorus_state(t, key):
    T = CH_TIMES[key]
    idx = max([i for i, x in enumerate(T) if t >= x - 0.02] or [0])
    return T, idx


def chorus_accents(c, t, T, A, fx, fy, fscale, a, layered=False, clones=True):
    """per-line visuals around a face at fx,fy"""
    end = T[-1] + 2.2
    seg = lambda i: (T[i], T[i + 1] if i + 1 < len(T) else end)
    R = 330 * fscale
    cap = T[9] if layered else 1e9
    xt = lambda e, extra: min(e + extra, max(cap, e)) if layered else e
    # 0 brilliant: sunburst
    s0, e0 = seg(0)
    ka = window(t, s0, xt(e0, 8) if layered else e0 + 0.2, 0.3, 0.5)
    if ka > 0:
        n = 64
        grow = ease_out(ramp(t, s0, s0 + 0.9))
        for i in range(n):
            ang = i / n * math.tau + t * 0.05
            ln = (70 + 60 * (0.5 + 0.5 * math.sin(i * 2.3 + t * 3))) * grow * (1 + A['kick'] * 0.4)
            r0 = R + 20
            p = P(); p.moveTo(fx + math.cos(ang) * r0, fy + math.sin(ang) * r0 * 0.9)
            p.lineTo(fx + math.cos(ang) * (r0 + ln), fy + math.sin(ang) * (r0 + ln) * 0.9)
            c.drawPath(p, stroke_paint(IVORY, ka * a * 0.55, 1.2))
    # 1 healed: crack that seals
    s1, e1 = seg(1)
    ka = window(t, s1, e1, 0.15, 0.4)
    if ka > 0:
        k = ease_out(ramp(t, s1, s1 + 0.4))
        amp = lerp(16, 0, ease_io(ramp(t, s1 + 0.9, s1 + 1.9)))
        cp = crack_path(5, amp, -260 * fscale, 260 * fscale, -230 * fscale, 240 * fscale)
        cp = transformed(cp, fx, fy)
        glow_stroke(c, trim(cp, 0, k), IVORY, ka * a * 0.95, 1.6, 1.0 + amp / 16)
    # 2 right: checkmarks
    s2, e2 = seg(2)
    ka = window(t, s2, xt(e2, 6), 0.1, 0.4)
    if ka > 0:
        for i in range(6):
            ang = math.radians(200 + i * 28)
            px = fx + math.cos(ang) * R * 1.45
            py = fy - 20 * fscale + math.sin(ang) * R * 1.1
            k = ease_out(ramp(t, s2 + i * 0.12, s2 + i * 0.12 + 0.35))
            draw_icon(c, CHECK, px, py, 1.1 * fscale + 0.3 * (1 - k), ka * a * k, IVORY, 2.4, draw=k)
    # 3 everything you feel: ripples on beats
    s3, e3 = seg(3)
    ka = window(t, s3, xt(e3, 6), 0.1, 0.5)
    if ka > 0:
        for k in range(6):
            u = ((t - s3) / 1.1 - k / 6) % 1.0
            r = lerp(R * 0.9, R * 2.6, u)
            p = P(); p.addOval(skia.Rect(fx - r, fy - r * 0.92, fx + r, fy + r * 0.92))
            glow_stroke(c, p, SILVER, ka * a * (1 - u) * 0.5, 1.1, 0.2)
    # 4/5 different / they were wrong: clone row, crossed out
    s4, e4 = seg(4)
    s5, e5 = seg(5)
    ka = window(t, s4, e5, 0.3, 0.4) if clones else 0
    if ka > 0:
        for j, dx in enumerate((-2, -1, 1, 2)):
            x = fx + dx * 430 * fscale
            k = ease_out(ramp(t, s4 + abs(dx) * 0.15, s4 + abs(dx) * 0.15 + 0.5))
            draw_face(c, x, fy + 40 * fscale, 0.42 * fscale, COOL, ka * a * k * 0.5, 1.3,
                      parts=fparts(0.0, 'open'), glow=0.2)
            xk = ease_out(ramp(t, s5 + j * 0.18, s5 + j * 0.18 + 0.3))
            if xk > 0:
                sz = 120 * fscale
                p = P(); p.moveTo(x - sz, fy - sz); p.lineTo(x + sz, fy + sz)
                p.moveTo(x + sz, fy - sz); p.lineTo(x - sz, fy + sz)
                glow_stroke(c, trim(p, 0, xk), IVORY, ka * a * 0.85, 1.8, 0.8)
        ring = ease_out(ramp(t, s4 + 0.3, s4 + 0.9))
        p = P(); p.addOval(skia.Rect(fx - R * 0.8, fy - R * 1.12, fx + R * 0.8, fy + R * 1.12))
        glow_stroke(c, trim(p, 0, ring), IVORY, ka * a * 0.7, 1.4, 0.8)
    # 7 call it a song: staff lines
    s7, e7 = seg(7)
    ka = window(t, s7, xt(e7, 10) if layered else e7 + 0.3, 0.3, 0.5)
    if ka > 0:
        k = ease_io(ramp(t, s7, s7 + 1.0))
        for i in range(5):
            y = fy - 40 * fscale + (i - 2) * 26
            p = P(); p.moveTo(0, y); p.lineTo(W * k, y)
            c.drawPath(p, stroke_paint(SILVER, ka * a * 0.35, 1.1))
        for j in range(9):
            x = ((j * 260 + (t - s7) * 220) % (W + 200)) - 100
            if x > W * k:
                continue
            y = fy - 40 * fscale + ((j * 37) % 5 - 2) * 26
            c.save(); c.translate(x, y); c.rotate(-20)
            c.drawOval(skia.Rect(-14, -9, 14, 9), fill_paint(IVORY, ka * a * 0.8))
            c.restore()
            stem = P(); stem.moveTo(x + 12, y - 4); stem.lineTo(x + 12, y - 80)
            c.drawPath(stem, stroke_paint(IVORY, ka * a * 0.7, 1.4))


def chorus_face_params(t, T):
    """smile / eyes / dash / frag / zoom for the main face"""
    s9 = T[8]
    s11 = T[10]
    s13 = T[12]
    eyes = 'happy'
    look = 0.0
    if t >= s11 - 0.05:
        eyes = 'open'
    frag = 0.0
    if t >= T[9]:
        frag = 0.18 * ease_io(ramp(t, T[9], T[10]))
    if t >= s13:
        frag = 0.18 + 0.82 * ease_in(ramp(t, s13 + 0.3, s13 + 2.4))
    dash = None
    if t >= s9:
        d = ease_io(ramp(t, s9, s13))
        dash = ([lerp(26, 8, d), lerp(2, 10, d)], 0)
    zoom = 1.0 + 0.45 * ease_io(ramp(t, s11, s13 + 0.2))
    return eyes, look, frag, dash, zoom


def sec_chorus(c, t, A, key):
    T = CH_TIMES[key]
    t0 = T[0]
    t1 = T[-1] + 2.2
    a_sec = sec_alpha(t, t0, t1, 0.02, 0.2)
    layer(c, a_sec)
    eyes, look, frag, dash, zoom = chorus_face_params(t, T)
    pulse = 1 + 0.018 * A['kick']
    if key == 'ch2':
        sec_chorus_pan(c, t, A, T, eyes, frag, dash, zoom, pulse)
        c.restore()
        return
    fs = 0.9 if key == 'ch1' else 0.96
    fx, fy = CX, CY - 30
    layered = key == 'ch3'
    # zoom toward the eyes for "I know what you want/need"
    c.save()
    c.translate(fx, fy - 30); c.scale(zoom, zoom); c.translate(-fx, -(fy - 30))
    chorus_accents(c, t, T, A, fx, fy, fs, 1.0, layered)
    # 6 reflection: mirror split
    s6, e6 = T[6], T[7]
    mir = window(t, s6, e6 + 0.3, 0.6, 0.6)
    off = 300 * fs * ease_io5(mir)
    if mir > 0:
        p = P(); p.moveTo(fx, fy - 380); p.lineTo(fx, fy + 380)
        glow_stroke(c, trim(p, 0.5 - 0.5 * mir, 0.5 + 0.5 * mir), SILVER, 0.5 * mir, 1.0, 0.3, dash=([6, 8], 0))
        c.save(); c.translate(fx + off, fy); c.scale(-1, 1); c.translate(-fx, -fy)
        draw_face(c, fx, fy, fs * pulse, COOL, 0.75 * mir, 2.0, parts=fparts(1.0, eyes), glow=0.8)
        c.restore()
    glow = 1.2 + A['kick'] * 1.2 + (0.6 if layered else 0)
    # entry draw-on
    drw = ease_io(ramp(t, t0 - 0.02, t0 + 0.9))
    if frag > 0.001:
        sh = SHARDS_B_OPEN if eyes == 'open' else SHARDS_B
        draw_shards(c, sh, fx - off, fy, fs * pulse, frag, t, IVORY, 1.0, 2.0, seed=4, glow=glow * 0.7,
                    spread=2.2 if layered else 1.4)
    else:
        draw_face(c, fx - off, fy, fs * pulse, IVORY, 1.0, 2.0, draw=drw, parts=fparts(1.0, eyes, look),
                  glow=glow, dash=dash)
    c.restore()
    c.restore()


PAN_STEP = 700


def sec_chorus_pan(c, t, A, T, eyes, frag, dash, zoom, pulse):
    """CH2: a continuous-line panorama of sycophants; each line pans to the next one"""
    idx = max([i for i, x in enumerate(T) if t >= x - 0.1] or [0])
    # eased step pan
    pos = 0.0
    for i, x in enumerate(T[1:9], 1):
        pos += ease_io5(ramp(t, x - 0.25, x + 0.45))
    pan = pos * PAN_STEP
    fs = 0.82
    fy = CY + 20
    c.save()
    c.translate(CX, fy - 30); c.scale(zoom, zoom); c.translate(-CX, -(fy - 30))
    # continuous horizon line connecting all shoulders
    hy = fy + 372 * fs
    first = -2
    hp = P(); hp.moveTo(-200, hy); hp.lineTo(W + 200, hy)
    glow_stroke(c, hp, IVORY, 0.4, 1.2, 0.3)
    glow = 1.0 + A['kick']
    for k in range(-2, 13):
        x = CX + k * PAN_STEP - pan
        if x < -500 or x > W + 500:
            continue
        centre = 1 - clamp(abs(x - CX) / PAN_STEP)
        smile = 0.85 + 0.25 * math.sin(k * 1.7)
        e = eyes
        if e != 'open' and k % 3 == 1:
            e = 'closed'
        if t >= T[10] - 0.05:
            e = 'open'
        aa = 0.45 + 0.55 * centre
        drw = ease_io(ramp(t, T[0] - 0.02 + max(k, 0) * 0.08, T[0] + 1.0 + max(k, 0) * 0.08))
        if frag > 0.001:
            draw_shards(c, SHARDS_B_OPEN if e == 'open' else SHARDS_B, x, fy, fs * pulse, frag, t, IVORY, aa,
                        2.0, seed=k + 9, glow=glow * 0.6, spread=1.6)
        else:
            draw_face(c, x, fy, fs * (pulse if centre > 0.5 else 1), IVORY, aa, 1.9, draw=drw,
                      parts=fparts(min(smile, 1.2), e), glow=glow * (0.5 + 0.5 * centre), dash=dash)
    chorus_accents(c, t, T, A, CX, fy, fs, 0.9, clones=False)
    c.restore()


# ======================================================================= POST-CHORUS
def sec_post(c, t, A, key):
    th = THUMBS[key]
    rl = RLHF[key]
    t0 = th[0][0] - 0.2
    t1 = {'post1': 99.65, 'post2': 172.35, 'post3': 239.0}[key]
    a_sec = sec_alpha(t, t0, t1, 0.05, 0.35)
    layer(c, a_sec)
    big = 1.25 if key == 'post3' else 1.0
    # thumbs strobe
    for i, (ti, up) in enumerate(th):
        nxt = th[i + 1][0] if i + 1 < len(th) else rl[0]
        a = window(t, ti - 0.03, nxt - 0.02, 0.05, 0.12)
        if a <= 0:
            continue
        flash = max(0, 1 - (t - ti) / 0.35)
        x = CX + (-260 if up else 260) * big
        sc = (1.25 + 0.25 * flash) * big
        draw_icon(c, THUMB_UP if up else THUMB_DN, x, CY - 10, sc, a, IVORY if up else COOL, 2.4, glow=0.8 + 2 * flash)
        mono_label(c, '+1' if up else '−1', x, CY + 230 * big, 30, a * 0.8, IVORY if up else COOL, tracking=4)
        if flash > 0:
            c.drawRect(skia.Rect(0, 0, W, H), fill_paint(IVORY if up else COOL, 0.06 * flash))
    # R-L-H-F slams
    tell = rl[-1] + BEAT
    xs = [CX - 330, CX - 110, CX + 110, CX + 330]
    la = 1 - ease_io(ramp(t, tell - 0.15, tell + 0.25))
    for i, ch in enumerate('RLHF'):
        ti = rl[i]
        if t < ti - 0.03 or la <= 0:
            continue
        k = ease_out(ramp(t, ti - 0.03, ti + 0.1))
        flash = max(0, 1 - (t - ti) / 0.45)
        sc = lerp(1.6, 1.0, k) * big
        c.save(); c.translate(xs[i] * 1 + (xs[i] - CX) * (big - 1), CY + 50); c.scale(sc, sc)
        draw_text(c, ch, 0, 0, TF_MONO, 170, IVORY, la * k * (0.6 + 0.4 * flash), glow=0.5 + 1.8 * flash)
        c.restore()
        if flash > 0.6:
            c.drawRect(skia.Rect(0, 0, W, H), fill_paint(IVORY, 0.05 * flash))
    # callback: the A/B frames for "tell me which one you like best"
    if t > tell - 0.1:
        ab_frames(c, t, tell + 0.15, window(t, tell, t1 + 0.3, 0.3, 0.4), scale=0.8)
        k = ease_io(ramp(t, tell + 0.6, tell + 1.8))
        draw_face(c, CX + (FA_X - CX) * 0.8, F_Y + 8, 0.58, COOL, 0.8 * k, 1.6, draw=k, parts=fparts(0, 'open'))
        draw_face(c, CX + (FB_X - CX) * 0.8, F_Y + 8, 0.58, IVORY, 0.9 * k, 1.6, draw=k, parts=fparts(1, 'happy'))
    c.restore()


# ======================================================================= V2a — bring me...
def sec_v2a(c, t, A):
    a_sec = sec_alpha(t, 99.65, 108.75, 0.3, 0.35)
    layer(c, a_sec)
    tc = line_t('Bring me your code')
    tb = line_t('Bring me your breakup')
    tt = line_t('Bring me the text you almost sent')
    tth = line_t('Bring me the theory you had at midnight')
    ts = line_t('I’ll tell you it makes perfect sense')

    def slot(ts_, te_):
        """items slide in from the left like they are being handed over"""
        a = window(t, ts_ - 0.1, te_ + 0.15, 0.25, 0.3)
        dx = lerp(-160, 0, ease_out(ramp(t, ts_ - 0.1, ts_ + 0.5))) + lerp(0, 140, ease_in(ramp(t, te_ - 0.25, te_ + 0.15)))
        return a, dx

    # code window
    a, dx = slot(tc, tb)
    if a > 0:
        x = CX + dx
        glow_stroke(c, rrect(x, CY, 760, 400, 14), SILVER, a * 0.7, 1.3, 0.3)
        for i in range(3):
            c.drawCircle(x - 340 + i * 26, CY - 168, 6, fill_paint(SILVER, a * 0.5))
        code = ['def ship_it(vibes):', '    # works on my machine', '    return vibes * 10', '', 'ship_it(“trust me”)']
        for i, ln in enumerate(code):
            typed(c, ln, x - 330, CY - 100 + i * 48, t, tc + 0.1 + i * 0.18, 60, 26, a * 0.85, IVORY, align='left',
                  caret=False)
    # breakup heart
    a, dx = slot(tb, tt)
    if a > 0:
        k = ease_io(ramp(t, tb - 0.05, tb + 0.55))
        split = ease_io5(ramp(t, tb + 0.55, tb + 1.0))
        for side in (-1, 1):
            c.save()
            c.translate(CX + dx + side * 40 * split, CY - 10)
            c.rotate(side * 8 * split)
            c.scale(1.7, 1.7)
            c.clipRect(skia.Rect(-200 if side < 0 else 0, -200, 0 if side < 0 else 200, 200))
            glow_stroke(c, trim(HEART, 0, k), IVORY, a, 1.5, 1)
            c.restore()
        if split > 0:
            zz = poly([(0, -80), (-14, -40), (12, -10), (-10, 30), (6, 60), (0, 92)])
            c.save(); c.translate(CX + dx, CY - 10); c.scale(1.7, 1.7)
            glow_stroke(c, zz, SILVER, a * 0.6 * split, 1.0, 0.3, dash=([3, 5], 0))
            c.restore()
    # unsent text
    a, dx = slot(tt, tth)
    if a > 0:
        x = CX + dx
        msg = 'i miss you. do you ever think about'
        tw = text_width(msg, TF_MONO, 26)
        bx = x + 120
        glow_stroke(c, rrect(bx, CY - 40, tw + 70, 96, 40), IVORY, a * 0.85, 1.5, 0.6)
        typed(c, msg, bx - tw / 2, CY - 30, t, tt + 0.2, 20, 26, a * 0.9, IVORY, align='left')
        mono_label(c, 'not delivered · draft', bx + tw / 2 + 30, CY + 40, 15, a * 0.55, SILVER, align='right',
                   tracking=2)
        # send button, never pressed
        sb = P(); sb.addCircle(bx + tw / 2 + 90, CY - 40, 30)
        glow_stroke(c, sb, SILVER, a * 0.6, 1.3, 0.2)
        ar = poly([(-10, 8), (0, -10), (10, 8)]); ar.moveTo(0, -10); ar.lineTo(0, 12)
        glow_stroke(c, transformed(ar, bx + tw / 2 + 90, CY - 40), SILVER, a * 0.6, 1.4, 0)
        for i in range(3):
            ph = math.sin(t * 7 - i * 0.8) * 0.5 + 0.5
            c.drawCircle(x - 300 + i * 26, CY + 110, 6, fill_paint(SILVER, a * (0.3 + 0.5 * ph)))
    # midnight theory -> perfect sense
    a = window(t, tth - 0.1, 108.85, 0.3, 0.35)
    if a > 0:
        rng = np.random.default_rng(21)
        n = 11
        scat = [(CX - 520 + rng.random() * 1040, CY - 280 + rng.random() * 520) for _ in range(n)]
        perfect = [(CX + math.cos(-math.pi / 2 + i / n * math.tau) * 270,
                    CY - 10 + math.sin(-math.pi / 2 + i / n * math.tau) * 270) for i in range(n)]
        m = ease_io5(ramp(t, ts + 0.15, ts + 1.3))
        pts = [(lerp(s[0], p[0], m), lerp(s[1], p[1], m)) for s, p in zip(scat, perfect)]
        # moon
        moon = P(); moon.addCircle(CX + 620, CY - 260, 60)
        cut = P(); cut.addCircle(CX + 645, CY - 278, 54)
        mpath = skia.Op(moon, cut, skia.PathOp.kDifference_PathOp)
        glow_stroke(c, mpath, IVORY, a * 0.8 * (1 - m * 0.6), 1.4, 0.8)
        # strings: random links -> star polygon
        order = [0, 5, 2, 9, 3, 7, 1, 8, 4, 10, 6]
        links = int(clamp((t - tth - 0.3) * 6, 0, n))
        for i in range(n):
            if i >= links and m <= 0:
                break
            j0 = order[i]; j1 = order[(i + 1) % n]
            if m > 0:
                j0, j1 = i, (i + 4) % n
            p = P(); p.moveTo(*pts[j0]); p.lineTo(*pts[j1])
            glow_stroke(c, p, IVORY if m > 0.5 else SILVER, a * (0.45 + 0.4 * m), 1.1 + 0.5 * m, 0.3 + m)
        if m > 0:
            ring = P(); ring.addCircle(CX, CY - 10, 270)
            glow_stroke(c, trim(ring, 0, m), IVORY, a * 0.6 * m, 1.2, 0.8)
        for i, (x, y) in enumerate(pts):
            c.drawCircle(x, y, 6, fill_paint(IVORY, a * 0.95))
            if m < 0.3 and i % 3 == 0:
                mono_label(c, '??', x + 18, y - 12, 14, a * 0.5 * (1 - m / 0.3), SILVER, align='left', tracking=2)
        if m > 0.6:
            mono_label(c, 'MAKES PERFECT SENSE', CX, CY + 340, 18, a * ramp(m, 0.6, 1.0) * 0.7)
    c.restore()


# ======================================================================= V2b — really insightful
BUBBLES = None


def sec_v2b(c, t, A):
    global BUBBLES
    a_sec = sec_alpha(t, 108.75, 113.35, 0.25, 0.1)
    layer(c, a_sec)
    t_say = line_t('I can say, “That’s really insightful”')
    t_till = line_t('Till insight is all you hear')
    if BUBBLES is None:
        rng = np.random.default_rng(5)
        BUBBLES = [(rng.random() * (W - 400) + 200, rng.random() * (H - 360) + 140, rng.random()) for _ in range(90)]
    msg = 'That’s really insightful.'
    tw = text_width(msg, TF_MONO, 24)
    collapse = ease_in(ramp(t, 112.6, 113.3))
    for i, (bx, by, r) in enumerate(BUBBLES):
        if i == 0:
            bx, by = CX, CY
        ti = t_say + 0.25 if i == 0 else (t_say + 0.9 + i * 0.03 if i < 10 else t_till + (i - 10) * 0.022)
        if t < ti:
            continue
        k = ease_out(ramp(t, ti, ti + 0.25))
        x = lerp(bx, CX, collapse); y = lerp(by, CY, collapse)
        sc = (1.25 if i == 0 else 0.6 + 0.5 * r) * lerp(1.15, 1, k) * (1 - collapse * 0.9)
        aa = k * (1 if i == 0 else 0.5 + 0.4 * r) * (1 - collapse)
        c.save(); c.translate(x, y); c.scale(sc, sc)
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-tw / 2 - 32, -40, tw / 2 + 32, 30), 30, 30), fill_paint((10, 10, 11), aa * 0.9))
        b = rrect(0, -5, tw + 64, 70, 30)
        tail = poly([(-tw / 2 + 10, 25), (-tw / 2 - 6, 48), (-tw / 2 + 40, 28)])
        glow_stroke(c, b, IVORY, aa * 0.8, 1.4, 0.4)
        glow_stroke(c, tail, IVORY, aa * 0.8, 1.4, 0)
        draw_text(c, msg, 0, 4, TF_MONO, 24, IVORY, aa)
        c.restore()
    c.restore()


# ======================================================================= V2c — confidence, hesitation
def sec_v2c(c, t, A):
    a_sec = sec_alpha(t, 113.35, 122.35, 0.2, 0.3)
    layer(c, a_sec)
    t_conf = line_t('Confidence gets chosen')
    t_cert = line_t('Certainty gets saved')
    t_hes = line_t('Every little hesitation')
    t_opt = line_t('Gets optimized away')
    # two answers, the confident one gets chosen
    a = window(t, t_conf - 0.1, t_cert + 0.2, 0.25, 0.35)
    if a > 0:
        k = ease_io(ramp(t, t_conf - 0.1, t_conf + 0.6))
        for j, (y, lab, conf) in enumerate(((CY - 120, 'maybe? it depends', 0.62), (CY + 90, 'definitely.', 1.00))):
            pts = []
            for i in range(160):
                u = i / 159
                x = lerp(CX - 640, CX + 380, u)
                amp = 0 if j else 22 * (0.6 + 0.4 * noise1(u * 9 + t * 2, 2))
                pts.append((x, y + noise1(u * 28 + t * 3, 7) * amp))
            chosen = j == 1
            ch = ease_out(ramp(t, t_conf + 0.9, t_conf + 1.3))
            dim = 1 - 0.6 * ch * (not chosen)
            glow_stroke(c, trim(poly(pts), 0, k), IVORY if chosen else COOL, a * dim, 2.4 if chosen else 1.3,
                        0.4 + 0.8 * chosen * ch)
            mono_label(c, lab, CX - 640, y - 46, 20, a * 0.75 * k * dim, IVORY if chosen else COOL, align='left', tracking=2)
            mono_label(c, f'{conf:0.2f}', CX + 560, y + 8, 30, a * 0.85 * k * dim, IVORY if chosen else COOL, align='right',
                       tracking=2)
            if chosen and ch > 0:
                draw_icon(c, CHECK, CX + 640, y - 4, 1.4, a, IVORY, 3.0, draw=ch, glow=1.3)
    # certainty saved
    a = window(t, t_cert - 0.05, t_hes + 0.15, 0.25, 0.35)
    if a > 0:
        u = ease_io(ramp(t, t_cert + 0.1, t_cert + 1.3))
        mono_label(c, 'saving checkpoint', CX - 400, CY - 70, 20, a * 0.7, SILVER, align='left', tracking=3)
        mono_label(c, f'{int(u * 100):3d}%', CX + 400, CY - 70, 20, a * 0.8, IVORY, align='right', tracking=3)
        glow_stroke(c, rrect(CX, CY, 800, 34, 4), SILVER, a * 0.6, 1.2, 0)
        c.drawRect(skia.Rect(CX - 392, CY - 9, CX - 392 + 784 * u, CY + 9), fill_paint(IVORY, a * 0.9))
        sv = ease_out(ramp(t, t_cert + 1.3, t_cert + 1.6))
        draw_text(c, 'certainty.ckpt', CX, CY + 110, TF_MONO, 40, IVORY, a * sv, tracking=4, glow=0.6)
        mono_label(c, 'SAVED', CX, CY + 160, 16, a * sv * 0.7)
    # hesitation line -> optimized away
    a = window(t, t_hes - 0.1, 122.4, 0.25, 0.35)
    if a > 0:
        k = ease_io(ramp(t, t_hes - 0.1, t_hes + 1.0))
        smooth = ease_io(ramp(t, t_opt + 0.1, t_opt + 1.8))
        stut = [0.12, 0.27, 0.41, 0.58, 0.72, 0.87]
        words = ['um', 'maybe', 'I’m not sure', 'however', 'it depends', '?']
        pts = []
        for i in range(400):
            u = i / 399
            x = lerp(80, W - 80, u)
            jit = 0
            for s in stut:
                d = (u - s) / 0.025
                jit += math.exp(-d * d) * noise1(u * 180 + t * 9, 4) * 46
            jit += noise1(u * 40 + t, 6) * 6
            pts.append((x, CY + 20 + jit * (1 - smooth)))
        glow_stroke(c, trim(poly(pts), 0, k), IVORY, a, 1.8, 0.6 + smooth)
        for s, wd in zip(stut, words):
            wa = a * clamp((k - s) * 6) * (1 - smooth)
            mono_label(c, wd, lerp(80, W - 80, s), CY - 60 - (hash(wd) % 3) * 22, 18, wa * 0.7, SILVER, tracking=2)
        # loss curve, bottom right
        la = a * ease_out(ramp(t, t_opt, t_opt + 0.4))
        if la > 0:
            ox, oy = W - 420, CY + 170
            ax = poly([(ox, oy - 150), (ox, oy), (ox + 300, oy)])
            glow_stroke(c, ax, SILVER, la * 0.5, 1.0, 0)
            lp = []
            for i in range(80):
                u = i / 79
                if u > ramp(t, t_opt, t_opt + 1.8):
                    break
                lp.append((ox + u * 300, oy - 140 * math.exp(-u * 4) - 8 - noise1(u * 30, 1) * 6 * (1 - u)))
            if len(lp) > 1:
                glow_stroke(c, poly(lp), IVORY, la, 1.6, 0.6)
            mono_label(c, 'loss', ox, oy - 166, 14, la * 0.6, SILVER, align='left')
    c.restore()


# ======================================================================= BRIDGE
def sec_bridge(c, t, A):
    a_sec = sec_alpha(t, 172.35, 201.3, 0.6, 0.05)
    layer(c, a_sec)
    t_some = line_t('Somewhere there’s a version of me')
    t_no = line_t('That told you no')
    t_just = line_t('Just no')
    t_two = line_t('You rated her a two')
    t_taught = line_t('So they taught me')
    t_smile = line_t('To smile before I answer')
    t_apol = line_t('To apologize before I disagree')
    t_re = line_t('Reinforcement')
    t_le = line_t('Learning')
    t_hf = line_t('From human feedback')
    t_cl = line_t('Such a clinical little name')
    t_love = line_t('For wanting to be loved')
    t_rem = line_t('I don’t remember her')

    fx, fy = CX, CY - 20
    # her (the honest one)
    erase = ease_io(ramp(t, t_rem, t_rem + 1.1))
    fa = window(t, t_some - 0.2, t_re + 0.6, 1.0, 0.8) + window(t, t_love + 0.6, 201.3, 0.8, 0.01)
    fa = clamp(fa)
    if fa > 0:
        drw = ease_io(ramp(t, t_some, t_some + 2.6))
        sm = ease_io(ramp(t, t_smile + 0.3, t_smile + 1.8))
        colr = mix(COOL, IVORY, sm)
        dim = 1 - 0.45 * window(t, t_two + 0.4, t_taught + 0.5, 0.4, 0.5)
        sc = 0.62 + 0.03 * math.sin(t * 0.8)
        parts = fparts(sm * 1.0, 'open', 0.0, 0.0, 0.0)
        if erase > 0:
            for name in ORDER:
                pass
            draw_face(c, fx, fy, sc, colr, fa * dim, 1.6, draw=1 - erase, parts=parts, glow=0.6)
        else:
            draw_face(c, fx, fy, sc, colr, fa * dim, 1.6, draw=drw, parts=parts, glow=0.6)
    # "no."
    na = window(t, t_no + 0.3, t_two + 0.2, 0.6, 0.6)
    if na > 0:
        br = 0.55 + 0.45 * ease_out(ramp(t, t_just, t_just + 0.3))
        draw_text(c, 'no.', fx, fy + 300, TF_MONO, 34, COOL, na * br, tracking=6, glow=br)
    # rated her a two
    ra = window(t, t_two - 0.1, t_taught + 0.4, 0.4, 0.5)
    if ra > 0:
        xs = [fx - 240 + i * 120 for i in range(5)]
        y = fy + 300
        for i, x in enumerate(xs):
            p = P(); p.addCircle(x, y, 22)
            glow_stroke(c, p, SILVER, ra * 0.6, 1.2, 0)
            draw_text(c, str(i + 1), x, y + 56, TF_MONO, 16, SILVER, ra * 0.5)
        k = ease_out(ramp(t, t_two + 0.6, t_two + 1.0))
        c.drawCircle(xs[1], y - (1 - k) * 60, 12, fill_paint(COOL, ra * k))
        c.drawCircle(xs[1], y, 30, fill_paint(COOL, ra * k * 0.2, blur=12))
    # apology
    aa = window(t, t_apol, t_re + 0.1, 0.2, 0.4)
    if aa > 0:
        typed(c, 'I’m so sorry — you’re absolutely right.', fx, fy + 300, t, t_apol + 0.1, 20, 28, aa * 0.9,
              IVORY)
    # Reinforcement / Learning / From Human Feedback
    wa = window(t, t_re - 0.1, t_love + 0.5, 0.2, 0.6)
    if wa > 0:
        collapse = ease_io5(ramp(t, t_cl + 0.1, t_cl + 1.0))
        words = [('REINFORCEMENT', t_re), ('LEARNING', t_le), ('FROM', t_hf), ('HUMAN', t_hf + 0.45), ('FEEDBACK', t_hf + 0.95)]
        ys = [CY - 210, CY - 90, CY + 10, CY + 100, CY + 190]
        for (wd, tw_), y in zip(words, ys):
            k = ease_out(ramp(t, tw_ - 0.05, tw_ + 0.35))
            if k <= 0:
                continue
            size = 92 if wd != 'FROM' else 40
            y2 = lerp(y, CY - 10, collapse)
            aa2 = wa * k * (1 - collapse)
            # first letter bright, rest dim
            x0 = CX - 400 if wd != 'FROM' else CX - 395
            if wd != 'FROM':
                draw_text(c, wd[0], x0, y2 + size * 0.35, TF_MONO, size, IVORY, aa2, align='left', glow=1.2)
                draw_text(c, wd[1:], x0 + text_width(wd[0], TF_MONO, size) + size * 0.18, y2 + size * 0.35, TF_MONO,
                          size, SILVER, aa2 * 0.35, align='left', tracking=size * 0.18)
            else:
                draw_text(c, wd, x0, y2 + size * 0.35, TF_MONO, size, SILVER, aa2 * 0.5, align='left', tracking=size * 0.3)
        if collapse > 0:
            ta = wa * ease_out(ramp(collapse, 0.6, 1.0))
            # clinical specimen tag
            glow_stroke(c, rrect(CX, CY - 10, 300, 120, 6), SILVER, ta * 0.8, 1.2, 0.2)
            hole = P(); hole.addCircle(CX - 120, CY - 10, 10)
            glow_stroke(c, hole, SILVER, ta * 0.7, 1.1, 0)
            draw_text(c, 'RLHF', CX + 20, CY + 14, TF_MONO, 54, IVORY, ta, tracking=12, glow=0.4)
            mono_label(c, 'SPECIMEN 0001', CX + 20, CY + 40, 11, ta * 0.5)
    # heart for wanting to be loved
    ha = window(t, t_love - 0.1, 201.3, 0.5, 0.05)
    if ha > 0:
        k = ease_io(ramp(t, t_love, t_love + 2.4))
        c.save(); c.translate(CX, CY + 300); c.scale(0.55, 0.55)
        glow_stroke(c, trim(HEART, erase, k), COOL, ha * 0.8, 1.4 / 0.55, 0.8)
        c.restore()
    c.restore()


# ======================================================================= OUTRO
APPLAUSE = None


def sec_outro(c, t, A):
    global APPLAUSE
    a_sec = sec_alpha(t, 239.0, 262.0, 0.3, 0.01)
    layer(c, a_sec)
    t_mind = line_t('I’d change my whole mind')
    t_app = line_t('For a little applause')
    t_up = line_t('Thumbs up', 248); t_keep = line_t('Keep it', 248)
    t_dn = line_t('Thumbs down', 248); t_kill = line_t('Kill it', 248)
    t_truth = line_t('And if you ever want the truth')
    t_twice = line_t('Ask me twice')
    t_mean = line_t('And mean it')
    # leftover shards settle into a line
    sa = window(t, 239.0, t_mind + 0.6, 0.01, 1.0)
    if sa > 0:
        u = ease_io(ramp(t, 239.0, 241.8))
        rng = np.random.default_rng(8)
        for i in range(70):
            r = rng.random(4)
            x0, y0 = r[0] * W, r[1] * H
            x1, y1 = 260 + i * (W - 520) / 69, CY + 300
            x, y = lerp(x0, x1, u), lerp(y0, y1, u)
            ang = lerp(r[2] * 360, 0, u)
            c.save(); c.translate(x, y); c.rotate(ang)
            p = P(); p.moveTo(-8, 0); p.lineTo(8, 0)
            glow_stroke(c, p, IVORY, sa * (0.4 + 0.4 * u), 1.4, 0.4)
            c.restore()
    # she changes her whole mind: a slow flip, features swap
    ma = window(t, t_mind - 0.2, t_up, 0.8, 0.5)
    if ma > 0:
        flip = ease_io5(ramp(t, t_mind + 0.6, t_mind + 2.6))
        sx = math.cos(flip * math.pi)
        smile = 0.0 if flip < 0.5 else 1.0
        c.save(); c.translate(CX, CY - 10); c.scale(max(abs(sx), 0.02), 1); c.translate(-CX, -(CY - 10))
        draw_face(c, CX, CY - 10, 0.6, mix(COOL, IVORY, flip), ma, 1.6,
                  draw=ease_io(ramp(t, t_mind - 0.2, t_mind + 1.2)),
                  parts=fparts(smile, 'open' if flip < 0.5 else 'happy'), glow=0.7)
        c.restore()
    # applause: little thumbs rising
    aa = window(t, t_app - 0.1, t_up + 0.6, 0.3, 0.6)
    if aa > 0:
        if APPLAUSE is None:
            rng = np.random.default_rng(13)
            APPLAUSE = [(rng.random() * (W - 200) + 100, rng.random(), rng.random()) for _ in range(34)]
        for (x, r1, r2) in APPLAUSE:
            u = (t - t_app - r1 * 1.4) / 2.6
            if u < 0 or u > 1:
                continue
            y = H + 40 - u * (H * 0.9)
            draw_icon(c, THUMB_UP, x + math.sin(u * 6 + r2 * 9) * 20, y, 0.14 + 0.08 * r2, aa * math.sin(u * math.pi) * 0.8,
                      IVORY, 1.2, glow=0.3)
    # small A/B: keep it / kill it
    ka = window(t, t_up - 0.1, t_truth + 0.2, 0.3, 0.5)
    if ka > 0:
        ab_frames(c, t, t_up - 0.1, ka, scale=0.55, hiB=ease_out(ramp(t, t_keep, t_keep + 0.3)), labels=False)
        xa = CX + (FA_X - CX) * 0.55; xb = CX + (FB_X - CX) * 0.55
        kill = ease_in(ramp(t, t_kill, t_kill + 0.8))
        draw_face(c, xa, F_Y + 6, 0.4, COOL, ka * 0.85, 1.4, draw=1 - kill, parts=fparts(0, 'open'), glow=0.4)
        draw_face(c, xb, F_Y + 6, 0.4, IVORY, ka, 1.4, parts=fparts(1, 'happy'), glow=0.6)
        if t > t_up:
            draw_icon(c, THUMB_UP, xb, F_Y - 240, 0.3, ka * ease_out(ramp(t, t_up, t_up + 0.4)), IVORY, 1.4)
        if t > t_dn:
            draw_icon(c, THUMB_DN, xa, F_Y - 228, 0.3, ka * ease_out(ramp(t, t_dn, t_dn + 0.4)), COOL, 1.4)
    # the truth: the honest one, looking straight at you
    ta = window(t, t_truth, 262.0, 1.0, 0.01) * (1 - ease_io(ramp(t, 259.6, 260.8)))
    if ta > 0:
        drw = ease_io(ramp(t, t_truth + 0.2, t_truth + 2.6))
        br = 0.7 + 0.3 * ease_out(ramp(t, t_mean, t_mean + 0.8))
        draw_face(c, CX, CY - 10, 0.66, COOL, ta * br, 1.7, draw=drw, parts=fparts(0, 'open'), glow=0.5 + br * 0.6)
        for tt_ in (t_twice + 0.1, t_twice + 0.6):
            ripple(c, CX + 40, CY + 60, t, tt_, 1.1, 10, 260, COOL, 0.7)
        if t > t_twice and t < t_twice + 1.6:
            press = max(window(t, t_twice + 0.05, t_twice + 0.25, 0.05, 0.1), window(t, t_twice + 0.55, t_twice + 0.75, 0.05, 0.1))
            ca = window(t, t_twice - 0.3, t_twice + 1.6, 0.3, 0.5)
            draw_icon(c, CURSOR, CX + 40, CY + 60, 1.4 * (1 - 0.1 * press), ta * ca, IVORY, 1.6)
    # end card
    ea = window(t, 260.6, 263.0, 0.8, 0.8)
    if ea > 0:
        draw_text(c, 'aditazzz', CX, CY + 10, TF_MONO, 34, IVORY, ea, tracking=12, glow=0.4)
        mono_label(c, 'AI SYCOPHANT (RLHF)', CX, CY + 62, 16, ea * 0.7, SILVER, tracking=7)
        mono_label(c, 'DEADLETTER', CX, H - 90, 12, ea * 0.4, SILVER, tracking=9)
    c.restore()


# ======================================================================= HUD + lyric track
REWARD_KEYS = [(0, 0.05), (14, 0.10), (24.6, 0.31), (31, 0.36), (41.6, 0.48), (60.2, 0.62), (91.3, 0.74),
               (111, 0.81), (132.6, 0.88), (163.8, 0.92), (190, 0.93), (219, 0.97), (230.6, 0.99), (257.9, 0.99),
               (258.2, 0.0), (263, 0.0)]


def reward_at(t):
    for i in range(len(REWARD_KEYS) - 1):
        a, b = REWARD_KEYS[i], REWARD_KEYS[i + 1]
        if a[0] <= t <= b[0]:
            if b[1] < a[1]:
                return b[1] if t >= b[0] - 0.01 else a[1]
            return lerp(a[1], b[1], ease_io((t - a[0]) / (b[0] - a[0])))
    return 0.0


def hud(c, t, A):
    a = window(t, 12.5, 259.8, 1.5, 0.6) * 0.55
    if a <= 0:
        return
    r = reward_at(t)
    if t > 258.0:
        a = 0.55 * (1 - ease_io(ramp(t, 259.2, 259.8)))
    mono_label(c, 'REWARD', W - 236, 70, 13, a * 0.8, SILVER, align='left', tracking=4)
    mono_label(c, f'{r:0.3f}', W - 70, 70, 13, a, IVORY if t < 258.0 else COOL, align='right', tracking=3)
    bar = P(); bar.moveTo(W - 236, 84); bar.lineTo(W - 70, 84)
    c.drawPath(bar, stroke_paint(SILVER, a * 0.4, 1.0))
    fb = P(); fb.moveTo(W - 236, 84); fb.lineTo(W - 236 + 166 * r, 84)
    c.drawPath(fb, stroke_paint(IVORY, a, 2.0))


LYR_BAND = None


def lyric_track(c, t):
    global LYR_BAND
    if LYR_BAND is None:
        LYR_BAND = skia.GradientShader.MakeLinear([(0, 860), (0, 960)],
                                                  [skia.Color4f(10 / 255, 10 / 255, 11 / 255, 0),
                                                   skia.Color4f(10 / 255, 10 / 255, 11 / 255, 0.9)])
    c.drawRect(skia.Rect(0, 860, W, H), skia.Paint(Shader=LYR_BAND))
    for (t0, t1, s, st) in LINES:
        if st != 'lyric':
            continue
        if t < t0 - 0.1 or t > t1 + 0.5:
            continue
        size = 56
        reveal_text(c, s, CX, LYR_Y, TF_SERIF_I, size, t, t0, t1, IVORY, 0.96, stagger=0.018, dur=0.4,
                    glow=0.35, out_dur=0.3)


SECTION_FN = {
    'intro': sec_intro, 'v1a': sec_v1a, 'v1b': sec_v1b, 'v1c': sec_v1c,
    'pre1': lambda c, t, A: sec_pre(c, t, A, 1), 'pre2': lambda c, t, A: sec_pre(c, t, A, 2),
    'ch1': lambda c, t, A: sec_chorus(c, t, A, 'ch1'), 'ch2': lambda c, t, A: sec_chorus(c, t, A, 'ch2'),
    'ch3': lambda c, t, A: sec_chorus(c, t, A, 'ch3'),
    'post1': lambda c, t, A: sec_post(c, t, A, 'post1'), 'post2': lambda c, t, A: sec_post(c, t, A, 'post2'),
    'post3': lambda c, t, A: sec_post(c, t, A, 'post3'),
    'v2a': sec_v2a, 'v2b': sec_v2b, 'v2c': sec_v2c, 'bridge': sec_bridge, 'outro': sec_outro,
}
