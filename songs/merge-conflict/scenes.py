"""MERGE CONFLICT — HEAD (her) vs incoming (him), one line, line 42."""
import os, math, sys
import numpy as np
import skia
from kit import *
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'ai-sycophant-fable'))  # repo layout (the chat used an absolute path)
from face import face_parts, draw_face, ORDER, thumb_path

TITLE = 'MERGE CONFLICT'
END = 209.5
BPM, PHASE = 120.0, 0.2322
BEAT = 60 / BPM
OFF = 0.15
HER, HIM = IVORY, COOL


def w(x):
    return round(x - OFF, 2)


E = [
    (w(2.70), 'Auto-merging main.py'), (w(7.56), 'Conflict'), (w(9.96), 'Automatic merge failed'),
    (w(28.58), 'I was here first on line forty-two'), (w(31.68), 'I renamed the function, I left you a note'),
    (w(35.58), 'You lived on a branch for three whole weeks'), (w(39.82), 'Never pulled once, never wrote'),
    (w(43.44), 'I rewrote that line the very same day'), (w(46.56), 'I made it async, I made it clean'),
    (w(50.54), 'You never told me you were touching it'), (w(54.54), 'You never told me anything'),
    (w(92.12), 'My tests all pass, I’ve got a green check'),
    (w(95.52), 'I’ve got a thread where the lead said yes'),
    (w(99.00), 'You force-pushed once and I forgave you'),
    (w(103.00), 'You squashed my commits and I’m still a mess'),
    (w(106.56), 'It works on my machine'), (w(108.08), 'It works on mine'),
    (w(110.04), 'Then why won’t it work on this one line?'),
    (w(146.64), 'Accept current change'), (w(149.58), 'Accept incoming change'),
    (w(153.54), 'Accept both changes'), (w(155.48), 'Build failed'),
    (w(158.62), 'Maybe your function name was better'), (w(162.38), 'Maybe your null check saved my life'),
    (w(166.36), 'Maybe we were never enemies'), (w(169.40), 'Just two people and one file'),
    (w(172.50), 'So I’ll take your version, baby'), (w(174.58), 'And you’ll keep a piece of mine'),
    (w(176.56), 'We’ll delete the markers'), (w(179.52), 'Line by line'),
    (w(181.18), 'Commit it together'), (w(182.86), 'Push it straight to main'),
    (w(185.36), 'No more arrows'), (w(187.44), 'No more pain'),
    (w(198.44), 'Merge successful'), (w(201.34), 'Two new conflicts in utils.py'),
    (w(12.0), '', 'gap'), (w(58.0), '', 'gap'), (w(190.5), '', 'gap'), (205.6, '', 'gap'),
]
PRE = {'pre1': [59.98, 63.68, 67.98, 71.08], 'pre2': [112.00, 115.62, 119.96, 123.08]}
PRE_LINES = ['Seven arrows pointing left (that’s you)', 'A line of equals in between (that’s us)',
             'Seven arrows pointing right (that’s me)', 'And nothing in the middle but the screen']
CH = {'ch1': [75.32, 78.06, 79.58, 81.88, 83.66, 85.60, 87.62, 89.86],
      'ch2': [127.36, 130.06, 131.56, 134.00, 135.68, 137.60, 139.62, 141.94]}
CH_LINES = ['It’s a merge conflict, baby', 'Your version or mine', 'Two hearts on the same line',
            'At the very same time', 'I won’t rebase for you', 'You won’t rebase for me',
            'So we’re stuck between the markers', 'Of what we used to be']
for k in PRE:
    PRE[k] = [w(x) for x in PRE[k]]
    E += list(zip(PRE[k], PRE_LINES))
for k in CH:
    CH[k] = [w(x) for x in CH[k]]
    E += list(zip(CH[k], CH_LINES))
E.append((w(92.0), '', 'gap')); E.append((w(144.6), '', 'gap'))
LINES = build_lines(E, END)
LYR = Lyrics(LINES)
lt = lambda s, after=0: line_t(LINES, s, after)

SECTIONS = [('intro', 0, 28.3), ('v1', 28.3, 59.7), ('pre1', 59.7, 75.1), ('ch1', 75.1, 91.9),
            ('v2', 91.9, 111.75), ('pre2', 111.75, 127.2), ('ch2', 127.2, 144.6), ('bridge', 144.6, 158.4),
            ('breakdown', 158.4, 172.3), ('final', 172.3, 197.9), ('outro', 197.9, END)]

# ======================================================================= faces
_her_cache, _him_cache = {}, {}


def short_hair():
    p = P()
    cubic(p, [(-158, -120), (-170, -220), (-90, -268), (0, -266),
              (100, -268), (172, -214), (160, -120)])
    cubic(p, [(-150, -150), (-110, -200), (-40, -214), (30, -232)])
    cubic(p, [(-60, -260), (-40, -236), (0, -222), (60, -224)])
    cubic(p, [(150, -150), (140, -190), (110, -214), (70, -226)])
    return p


def her_parts(smile=0.0, eyes='open', look=0.0):
    k = (round(smile, 2), eyes, round(look, 2))
    if k not in _her_cache:
        _her_cache[k] = face_parts(smile=k[0], eyes=eyes, look=k[2])
    return _her_cache[k]


def him_parts(smile=0.0, eyes='open', look=0.0):
    k = (round(smile, 2), eyes, round(look, 2))
    if k not in _him_cache:
        p = dict(face_parts(smile=k[0] * 0.7, eyes=eyes, look=k[2], brow=-0.3))
        p['hair'] = short_hair()
        # squarer jaw
        jaw = P()
        cubic(jaw, [(-150, -150), (-160, -40), (-160, 60), (-140, 130),
                    (-118, 180), (-60, 214), (0, 216), (60, 214), (118, 180), (140, 130),
                    (160, 60), (160, -40), (150, -150)])
        p['contour'] = jaw
        # thicker neck
        nk = P()
        cubic(nk, [(-78, 186), (-76, 240), (-80, 290), (-96, 326)])
        cubic(nk, [(78, 186), (76, 240), (80, 290), (96, 326)])
        cubic(nk, [(-96, 326), (-160, 348), (-240, 350), (-320, 372)])
        cubic(nk, [(96, 326), (160, 348), (240, 350), (320, 372)])
        p['neck'] = nk
        _him_cache[k] = p
    return _him_cache[k]


def her(c, x, y, s, a, draw=1.0, smile=0.0, eyes='open', look=0.0, glow=0.8, dash=None):
    draw_face(c, x, y, s, HER, a, 1.8, draw=draw, parts=her_parts(smile, eyes, look), glow=glow, dash=dash)


def him(c, x, y, s, a, draw=1.0, smile=0.0, eyes='open', look=0.0, glow=0.8, dash=None):
    draw_face(c, x, y, s, HIM, a, 1.8, draw=draw, parts=him_parts(smile, eyes, look), glow=glow, dash=dash)


# ======================================================================= code editor
def editor(c, x, y, w_, h_, a, lines, t=0, hl=None, title='main.py', first=40):
    """lines: list of (text, colour, alpha) ; hl: {index: colour}"""
    if a <= 0.004:
        return
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x - w_ / 2, y - h_ / 2, x + w_ / 2, y + h_ / 2), 12, 12),
                fill_paint((12, 12, 13), a * 0.94))
    glow_stroke(c, rrect(x, y, w_, h_, 12), SILVER, a * 0.7, 1.3, 0.3)
    c.drawPath(line(x - w_ / 2, y - h_ / 2 + 40, x + w_ / 2, y - h_ / 2 + 40), stroke_paint(SILVER, a * 0.4, 1.0))
    mono_label(c, title, x - w_ / 2 + 24, y - h_ / 2 + 27, 14, a * 0.7, SILVER, align='left', tracking=2)
    lh = 40
    y0 = y - h_ / 2 + 80
    for i, item in enumerate(lines):
        if item is None:
            continue
        txt, colr, la = item
        yy = y0 + i * lh
        if hl and i in hl:
            c.drawRect(skia.Rect(x - w_ / 2 + 2, yy - 27, x + w_ / 2 - 2, yy + 11), fill_paint(hl[i], a * 0.10))
            c.drawRect(skia.Rect(x - w_ / 2 + 2, yy - 27, x - w_ / 2 + 6, yy + 11), fill_paint(hl[i], a * 0.9))
        draw_text(c, str(first + i), x - w_ / 2 + 54, yy, TF_MONO, 18, SILVER, a * 0.45, align='right')
        draw_text(c, txt, x - w_ / 2 + 80, yy, TF_MONO, 22, colr, a * la, align='left')


def heart_path():
    p = P()
    cubic(p, [(0, 60), (-40, 30), (-110, -10), (-100, -60),
              (-90, -110), (-20, -110), (0, -60),
              (20, -110), (90, -110), (100, -60),
              (110, -10), (40, 30), (0, 60)])
    return p


HEART = heart_path()
CHECK = P(); CHECK.moveTo(-22, 2); CHECK.lineTo(-6, 18); CHECK.lineTo(26, -18)
CROSS = P(); CROSS.moveTo(-18, -18); CROSS.lineTo(18, 18); CROSS.moveTo(18, -18); CROSS.lineTo(-18, 18)


def laptop(x, y, s=1.0):
    p = rrect(x, y, 300 * s, 190 * s, 8 * s)
    p.moveTo(x - 190 * s, y + 105 * s); p.lineTo(x + 190 * s, y + 105 * s)
    p.lineTo(x + 165 * s, y + 95 * s); p.lineTo(x - 165 * s, y + 95 * s); p.close()
    return p


# ======================================================================= branch graph
def branch_graph(c, t, a, prog=1.0, merge=0.0, conflict=0.0, y=CY, x0=200, x1=1720, squash=0.0, n_feat=9):
    """main (her, ivory) and feature/async (him, cool) diverging, optional merge"""
    if a <= 0.004:
        return
    bx = x0 + 260
    mx = x1 - 160
    # main
    p = P(); p.moveTo(x0, y); p.lineTo(lerp(x0, x1, prog), y)
    glow_stroke(c, p, HER, a, 2.0, 0.6)
    # feature branch arc
    f = P(); f.moveTo(bx, y)
    bd = min(260, (mx - bx) / 4)
    f.cubicTo(bx + bd * 0.46, y, bx + bd * 0.54, y - 150, bx + bd, y - 150)
    f.lineTo(mx - bd, y - 150)
    f.cubicTo(mx - bd * 0.54, y - 150, mx - bd * 0.46, y, mx, y)
    fp = clamp((prog - 0.15) / 0.85)
    glow_stroke(c, trim(f, 0, fp if merge <= 0 else 1), HIM, a, 2.0, 0.6)
    # commits
    for i in range(7):
        x = x0 + 40 + i * (x1 - x0 - 80) / 6
        if (x - x0) / (x1 - x0) > prog:
            continue
        glow_stroke(c, circle(x, y, 9), HER, a, 1.8, 0.5)
    for i in range(n_feat):
        u = (i + 1) / (n_feat + 1)
        xx = lerp(bx + bd, mx - bd, u)
        if u > fp * 1.15:
            continue
        xs = lerp(xx, (bx + mx) / 2, squash)
        glow_stroke(c, circle(xs, y - 150, 9), HIM, a * (1 - squash * 0.6 if i else 1), 1.8, 0.5)
    mono_label(c, 'main', x0 - 20, y + 6, 14, a * 0.6, HER, align='right')
    mono_label(c, 'feature/async', bx + bd + 40, y - 186, 14, a * 0.6 * clamp(fp * 3), HIM, align='left')
    if conflict > 0:
        glow_stroke(c, circle(mx, y, 22), IVORY, a * conflict, 2.2, 1.2)
        draw_icon(c, CROSS, mx, y, 0.8, a * conflict, IVORY, 2.4, glow=1.2)
    if merge > 0:
        glow_stroke(c, circle(mx, y, 14), IVORY, a * merge, 2.4, 1.6)
        c.drawCircle(mx, y, 50, fill_paint(IVORY, a * merge * 0.12, blur=20))


# ======================================================================= HUD
def hud(c, t, A, vertical):
    a = window(t, 10.5, END - 3.4, 1.0, 0.8) * 0.6
    if a <= 0:
        return
    if t < w(186.0):
        s, colr = 'main.py  ·  1 conflict', IVORY
    elif t < w(201.34):
        s, colr = 'main.py  ·  0 conflicts', SILVER
    else:
        s, colr = 'utils.py  ·  2 conflicts', IVORY
    if vertical:
        draw_text(c, s, 540, 440, TF_MONO, 14, colr, a, tracking=3)
    else:
        draw_text(c, s, W - 70, 70, TF_MONO, 13, colr, a, align='right', tracking=3)


# ======================================================================= INTRO
def sec_intro(c, t, A):
    a_sec = sec_alpha(t, 0, 28.3, 0.01, 0.4)
    layer(c, a_sec)
    logs = [(0.3, '$ git merge feature/async', SILVER), (w(2.70), 'Auto-merging main.py', SILVER),
            (w(7.56), 'CONFLICT (content): Merge conflict in main.py', IVORY),
            (w(9.96), 'Automatic merge failed; fix conflicts and then commit the result.', SILVER)]
    la = 1 - ease_io(ramp(t, 12.0, 13.0))
    for i, (ts, s, colr) in enumerate(logs):
        typed(c, s, 300, 330 + i * 52, t, ts, 45, 26, la * (1.0 if i == 2 else 0.8), colr, align='left',
              caret=(i == 3 or t < logs[min(i + 1, 3)][0]))
    # instrumental: the two branches grow, the two of them appear
    ga = window(t, 12.4, 28.6, 0.6, 0.5)
    if ga > 0:
        prog = ease_io(ramp(t, 12.6, 24.5))
        conf = ease_out(ramp(t, 25.0, 25.6))
        branch_graph(c, t, ga, prog, conflict=conf, y=CY + 230, x0=360, x1=1560)
        her(c, 520, CY - 90, 0.5, ga * ease_io(ramp(t, 15.5, 18.0)), draw=ease_io(ramp(t, 15.5, 19.0)))
        him(c, 1400, CY - 90, 0.5, ga * ease_io(ramp(t, 19.0, 21.5)), draw=ease_io(ramp(t, 19.0, 22.5)))
        mono_label(c, 'HEAD', 520, CY + 110, 15, ga * 0.6 * ease_out(ramp(t, 18, 19)), HER)
        mono_label(c, 'INCOMING', 1400, CY + 110, 15, ga * 0.6 * ease_out(ramp(t, 22, 23)), HIM)
        if t > 25.0:
            draw_text(c, 'MERGE CONFLICT', CX, 150, TF_MONO4, 60, IVORY, ga * ease_out(ramp(t, 25.0, 25.3)),
                      tracking=24, glow=1.2 * max(0, 1 - (t - 25.0) / 0.6) + 0.6)
    c.restore()


# ======================================================================= VERSE 1
def sec_v1(c, t, A):
    a_sec = sec_alpha(t, 28.3, 59.7, 0.4, 0.4)
    layer(c, a_sec)
    t1 = lt('I was here first on line forty-two'); t2 = lt('I renamed the function, I left you a note')
    t3 = lt('You lived on a branch for three whole weeks'); t4 = lt('Never pulled once, never wrote')
    t5 = lt('I rewrote that line the very same day'); t6 = lt('I made it async, I made it clean')
    t7 = lt('You never told me you were touching it'); t8 = lt('You never told me anything')
    herturn = t < t5 - 0.2
    ha = 1.0 if herturn else 0.4
    hm = 0.4 if herturn else 1.0
    her(c, 300, CY - 40, 0.5, ha, glow=0.5 + 0.6 * herturn)
    him(c, 1620, CY - 40, 0.5, hm * ease_io(ramp(t, 28.3, 29.5)), glow=0.5 + 0.6 * (not herturn))
    mono_label(c, 'HEAD', 300, CY + 160, 14, ha * 0.6, HER)
    mono_label(c, 'feature/async', 1620, CY + 160, 14, hm * 0.6, HIM)
    # editor (her version, then his)
    ea = window(t, t1 - 0.1, t3 + 0.1, 0.3, 0.3) + window(t, t5 - 0.1, t7 + 0.1, 0.3, 0.3)
    if ea > 0:
        if herturn:
            renamed = ease_out(ramp(t, t2 + 0.3, t2 + 0.6))
            l42 = 'def get_user(id):' if renamed > 0.5 else 'def fetch_user(id):'
            lines = [('import db', SILVER, 0.6), ('', SILVER, 1),
                     (l42, HER, 1), ('    return db.users[id]', SILVER, 0.7),
                     ('# renamed it. pls pull. — HEAD', HER, 0.8 * ease_out(ramp(t, t2 + 1.0, t2 + 1.6))), ('', SILVER, 1)]
            editor(c, CX, CY, 800, 330, ea, lines, t, hl={2: HER}, title='main.py  (main)')
            if t < t2:
                draw_text(c, '← line 42', CX + 300, CY - 54, TF_MONO, 18, HER, ea * ease_out(ramp(t, t1 + 0.6, t1 + 1.0)),
                          align='left')
        else:
            clean = ease_out(ramp(t, t6 + 0.5, t6 + 1.0))
            lines = [('import db', SILVER, 0.6), ('', SILVER, 1),
                     ('async def fetch_user(id):', HIM, 1),
                     ('    return await db.users.get(id)' if clean > 0.5 else '    return db.users[id]', SILVER, 0.8),
                     ('# cleaned up. — feature/async', HIM, 0.8 * clean), ('', SILVER, 1)]
            editor(c, CX, CY, 800, 330, ea, lines, t, hl={2: HIM}, title='main.py  (feature/async)')
            if t < t6:
                draw_text(c, 'same day', CX + 280, CY - 54, TF_MONO, 18, HIM, ea * ease_out(ramp(t, t5 + 0.8, t5 + 1.2)),
                          align='left')
    # three whole weeks: branch graph
    ba = window(t, t3 - 0.1, t5 - 0.1, 0.3, 0.3)
    if ba > 0:
        branch_graph(c, t, ba, ease_io(ramp(t, t3 - 0.1, t3 + 2.2)), y=CY + 60, x0=560, x1=1360, n_feat=12)
        mono_label(c, '21 days', CX, CY - 140, 18, ba * 0.7 * ease_out(ramp(t, t3 + 1.6, t3 + 2.0)), HIM)
        if t > t4:
            k = ease_out(ramp(t, t4, t4 + 0.4))
            draw_text(c, 'git pull', CX - 140, CY + 210, TF_MONO, 30, SILVER, ba * k * 0.6)
            c.drawPath(line(CX - 220, CY + 200, CX - 220 + 160 * ease_io(ramp(t, t4 + 0.4, t4 + 0.8)), CY + 200),
                       stroke_paint(IVORY, ba * k, 2.0))
            draw_text(c, '× 0', CX + 120, CY + 210, TF_MONO, 30, HIM, ba * k)
    # you never told me: chat
    ca = window(t, t7 - 0.1, 59.8, 0.3, 0.4)
    if ca > 0:
        msg = 'you were touching main.py??'
        tw = text_width(msg, TF_MONO, 26)
        bx = CX + 60
        k = ease_out(ramp(t, t7 + 0.1, t7 + 0.4))
        glow_stroke(c, rrect(bx, CY - 60, tw + 70, 80, 36), HIM, ca * k, 1.5, 0.6)
        draw_text(c, msg, bx, CY - 51, TF_MONO, 26, HIM, ca * k)
        mono_label(c, 'seen 3 weeks ago', bx + tw / 2 + 30, CY + 4, 13, ca * k * 0.55, align='right', tracking=2)
        if t > t8:
            k2 = ease_out(ramp(t, t8, t8 + 0.3))
            glow_stroke(c, rrect(CX - 200, CY + 90, 150, 70, 34), HER, ca * k2, 1.5, 0.4)
            stopped = t > t8 + 2.0
            for i in range(3):
                ph = 0.5 + 0.5 * math.sin(t * 7 - i * 0.8)
                c.drawCircle(CX - 230 + i * 30, CY + 90, 7, fill_paint(HER, ca * k2 * (0.25 if stopped else 0.3 + 0.6 * ph)))
            if stopped:
                mono_label(c, 'stopped typing', CX - 200, CY + 160, 13, ca * 0.5, align='center')
    c.restore()


# ======================================================================= PRE-CHORUS: the markers
def markers(c, t, T, a, scale=1.0, y=CY, her_a=1.0, him_a=1.0):
    rows = [('<<<<<<< HEAD', HER, '(that’s you)'), ('=======', SILVER, '(that’s us)'),
            ('>>>>>>> feature/async', HIM, '(that’s me)')]
    for i, (s, colr, note) in enumerate(rows):
        ti = T[i] + 0.2
        if t < ti - 0.03:
            continue
        yy = y - 170 + i * 170
        slam_text(c, s, CX, yy, t, ti, 64 * scale, colr, a, tracking=6)
        mono_label(c, note, CX, yy + 50, 16, a * 0.6 * ease_out(ramp(t, ti + 0.9, ti + 1.3)), colr)


def sec_pre(c, t, A, key):
    T = PRE[key]
    t0 = {'pre1': 59.7, 'pre2': 111.75}[key]; t1 = {'pre1': 75.1, 'pre2': 127.2}[key]
    a_sec = sec_alpha(t, t0, t1, 0.3, 0.05)
    layer(c, a_sec)
    markers(c, t, T, 1.0)
    sa = window(t, T[3], t1 + 0.1, 0.3, 0.05)
    if sa > 0:
        glow = 0.5 + 0.5 * math.sin(t * 4)
        her(c, 200, CY - 20, 0.45, sa, look=0.8)
        him(c, 1720, CY - 20, 0.45, sa, look=-0.8)
    c.restore()


# ======================================================================= CHORUS
def sec_chorus(c, t, A, key):
    T = CH[key]
    t0 = {'ch1': 75.1, 'ch2': 127.2}[key]; t1 = {'ch1': 91.9, 'ch2': 144.6}[key]
    a_sec = sec_alpha(t, t0, t1, 0.02, 0.3)
    layer(c, a_sec)
    pulse = 1 + 0.02 * A['kick']
    vise = ease_io5(ramp(t, T[6], T[7] + 0.6))
    gap = lerp(1.0, 0.45, vise)
    # faces
    fy = CY - 10
    her(c, 470 + 160 * vise, fy, 0.62 * pulse, 1 - 0.3 * vise, look=0.5, glow=1 + A['kick'])
    him(c, 1450 - 160 * vise, fy, 0.62 * pulse, 1 - 0.3 * vise, look=-0.5, glow=1 + A['kick'])
    # title
    ta = window(t, T[0] - 0.05, T[1] + 0.2, 0.08, 0.3)
    if ta > 0:
        draw_text(c, 'MERGE CONFLICT', CX, 140, TF_MONO4, 72, IVORY, ta, tracking=24,
                  glow=1.4 * max(0, 1 - (t - T[0]) / 0.5) + 0.6 + A['kick'])
    # your version or mine: two code lines alternate on beats
    va = window(t, T[1] - 0.05, T[2] + 0.1, 0.1, 0.3)
    if va > 0:
        on = int((t - T[1]) / BEAT) % 2
        draw_text(c, 'def get_user(id):', CX, CY - 40, TF_MONO, 34, HER, va * (1 if on == 0 else 0.25), glow=0.8 * (on == 0))
        draw_text(c, 'async def fetch_user(id):', CX, CY + 40, TF_MONO, 34, HIM, va * (1 if on == 1 else 0.25),
                  glow=0.8 * (on == 1))
    # two hearts on the same line, same time
    ha = window(t, T[2] - 0.05, T[4] + 0.1, 0.1, 0.3)
    if ha > 0:
        hy = CY + 40
        c.drawPath(line(CX - 360, hy + 30, CX + 360, hy + 30), stroke_paint(SILVER, ha * 0.6, 1.4))
        mono_label(c, '42', CX - 400, hy + 36, 16, ha * 0.5, align='right')
        u = ease_in(ramp(t, T[2], T[3] + 0.1))
        for s, colr in ((-1, HER), (1, HIM)):
            x = CX + s * lerp(300, 46, u)
            draw_icon(c, HEART, x, hy - 20, 0.42, ha, colr, 2.0, glow=0.8)
        if t > T[3] + 0.1:
            k = max(0, 1 - (t - T[3] - 0.1) / 0.6)
            ripple(c, CX, hy - 20, t, T[3] + 0.1, 0.7, 10, 160, IVORY, 0.9)
            draw_icon(c, CROSS, CX, hy - 110, 1.0, ha * ease_out(ramp(t, T[3] + 0.1, T[3] + 0.3)), IVORY, 2.6, glow=1 + k)
    # rebase refusals
    ra = window(t, T[4] - 0.05, T[6] + 0.1, 0.1, 0.3)
    if ra > 0:
        for i, (s, colr, x) in enumerate((('$ git rebase feature/async', HER, CX), ('$ git rebase main', HIM, CX))):
            ti = T[4 + i]
            if t < ti:
                continue
            y = CY - 40 + i * 90
            k = ease_out(ramp(t, ti, ti + 0.3))
            draw_text(c, s, x, y, TF_MONO, 30, colr, ra * k)
            draw_text(c, 'refused', x, y + 34, TF_MONO, 16, SILVER, ra * 0.6 * ease_out(ramp(t, ti + 0.6, ti + 0.9)),
                      tracking=4)
    # stuck between the markers: vise
    if vise > 0 or t > T[6]:
        ma = window(t, T[6] - 0.05, t1 + 0.4, 0.15, 0.4)
        top = lerp(80, CY - 230, vise)
        bot = lerp(H - 140, CY + 230, vise)
        draw_text(c, '<' * 7 + ' HEAD', CX, top, TF_MONO, 54, HER, ma, tracking=8, glow=0.8)
        draw_text(c, '>' * 7 + ' feature/async', CX, bot, TF_MONO, 54, HIM, ma, tracking=8, glow=0.8)
    c.restore()


# ======================================================================= VERSE 2
def sec_v2(c, t, A):
    a_sec = sec_alpha(t, 91.9, 111.75, 0.3, 0.3)
    layer(c, a_sec)
    T = [lt('My tests all pass, I’ve got a green check'), lt('I’ve got a thread where the lead said yes'),
         lt('You force-pushed once and I forgave you'), lt('You squashed my commits and I’m still a mess'),
         lt('It works on my machine'), lt('It works on mine'), lt('Then why won’t it work on this one line?')]
    # tests (her)
    a = window(t, T[0] - 0.1, T[1] + 0.1, 0.25, 0.3)
    if a > 0:
        her(c, 360, CY - 20, 0.5, a, smile=0.4)
        tests = ['test_get_user', 'test_missing_user', 'test_rename', 'test_vibes']
        for i, s in enumerate(tests):
            ti = T[0] + 0.3 + i * 0.25
            if t < ti:
                continue
            y = CY - 120 + i * 70
            k = ease_out(ramp(t, ti, ti + 0.3))
            draw_icon(c, CHECK, 820, y - 8, 1.0, a * k, HER, 2.4, draw=k, glow=0.8)
            draw_text(c, s, 880, y, TF_MONO, 28, HER, a * k * 0.9, align='left')
            draw_text(c, 'PASSED', 1380, y, TF_MONO, 18, SILVER, a * k * 0.6, align='left', tracking=4)
    # thread (him)
    a = window(t, T[1] - 0.1, T[2] + 0.1, 0.25, 0.3)
    if a > 0:
        him(c, 1560, CY - 20, 0.5, a, smile=0.4)
        msgs = [('him', 'making fetch_user async ok?', HIM), ('lead', 'yes. ship it.', IVORY)]
        for i, (who, m, colr) in enumerate(msgs):
            ti = T[1] + 0.2 + i * 0.9
            if t < ti:
                continue
            y = CY - 80 + i * 130
            k = ease_out(ramp(t, ti, ti + 0.3))
            tw = text_width(m, TF_MONO, 26)
            glow_stroke(c, rrect(800 + tw / 2 + 30, y, tw + 60, 74, 34), colr, a * k, 1.4, 0.5)
            draw_text(c, m, 830, y + 9, TF_MONO, 26, colr, a * k, align='left')
            mono_label(c, who, 790, y - 50, 13, a * k * 0.55, align='left', tracking=3)
    # force push (her forgave)
    a = window(t, T[2] - 0.1, T[3] + 0.1, 0.25, 0.3)
    if a > 0:
        her(c, 360, CY - 20, 0.5, a)
        draw_text(c, '$ git push --force', CX + 120, CY - 120, TF_MONO, 36, HIM, a * ease_out(ramp(t, T[2], T[2] + 0.3)))
        er = ease_io(ramp(t, T[2] + 0.6, T[2] + 1.3))
        rd = ease_io(ramp(t, T[2] + 1.6, T[2] + 2.6))
        p = line(CX - 300, CY + 40, CX + 540, CY + 40)
        glow_stroke(c, trim(p, er, 1) if rd <= 0 else trim(p, 0, rd), HER, a, 2.0, 0.6)
        for i in range(6):
            x = CX - 260 + i * 150
            if (rd <= 0 and (x - (CX - 300)) / 840 < er) or (rd > 0 and (x - (CX - 300)) / 840 > rd):
                continue
            glow_stroke(c, circle(x, CY + 40, 9), HER, a, 1.8, 0.5)
        if rd > 0.9:
            mono_label(c, 'forgiven', CX + 120, CY + 120, 16, a * 0.6, HER)
    # squash (his commits)
    a = window(t, T[3] - 0.1, T[4] + 0.1, 0.25, 0.3)
    if a > 0:
        him(c, 1560, CY - 20, 0.5, a, smile=-0.2)
        sq = ease_io5(ramp(t, T[3] + 0.6, T[3] + 1.6))
        for i in range(7):
            x = lerp(CX - 520 + i * 130, CX - 130, sq)
            glow_stroke(c, circle(x, CY, 12 if i else 12 + 8 * sq), HIM, a * (1 - sq * 0.8 if i else 1), 2.0, 0.6)
        c.drawPath(line(CX - 560, CY, CX + 300, CY), stroke_paint(HIM, a * 0.5, 1.2))
        mono_label(c, '7 commits' if sq < 0.5 else '1 commit (squashed)', CX - 130, CY + 70, 16, a * 0.6, HIM)
    # works on my machine / mine
    a = window(t, T[4] - 0.1, T[6] + 0.1, 0.25, 0.3)
    if a > 0:
        for i, (x, colr, tm) in enumerate(((520, HER, T[4]), (1400, HIM, T[5]))):
            k = ease_out(ramp(t, tm, tm + 0.4))
            glow_stroke(c, laptop(x, CY - 20, 1.3), colr, a * k, 1.6, 0.4)
            draw_icon(c, CHECK, x, CY - 30, 2.0, a * k, colr, 3.0, draw=ease_out(ramp(t, tm + 0.3, tm + 0.7)), glow=1.0)
            mono_label(c, 'my machine' if i == 0 else 'mine', x, CY + 170, 15, a * k * 0.6, colr)
    a = window(t, T[6] - 0.1, 111.8, 0.2, 0.3)
    if a > 0:
        g = (int(t * 14) % 3 - 1) * 6 if t > T[6] + 0.8 else 0
        draw_text(c, '42', CX - 330 + g, CY + 230, TF_MONO, 30, SILVER, a * 0.5)
        draw_text(c, '<<<<<<< ??? >>>>>>>', CX + g, CY + 230, TF_MONO, 34, IVORY, a, glow=0.6)
        draw_icon(c, CROSS, CX + 330, CY + 218, 1.0, a * ease_out(ramp(t, T[6] + 0.6, T[6] + 0.9)), IVORY, 2.6, glow=1.2)
    c.restore()


# ======================================================================= BRIDGE: code lens
def sec_bridge(c, t, A):
    a_sec = sec_alpha(t, 144.6, 158.4, 0.3, 0.3)
    layer(c, a_sec)
    tc = lt('Accept current change'); ti = lt('Accept incoming change')
    tb = lt('Accept both changes'); tf = lt('Build failed')
    state = 'none'
    if t > tc + 0.5: state = 'cur'
    if t > ti + 0.5: state = 'inc'
    if t > tb + 0.5: state = 'both'
    if state == 'cur':
        lines = [('def get_user(id):', HER, 1), ('    return db.users[id]', SILVER, 0.7)]
    elif state == 'inc':
        lines = [('async def fetch_user(id):', HIM, 1), ('    return await db.users.get(id)', SILVER, 0.7)]
    elif state == 'both':
        lines = [('def get_user(id):', HER, 1), ('async def fetch_user(id):', HIM, 1), ('    return ???', SILVER, 0.7)]
    else:
        lines = [('<<<<<<< HEAD', HER, 0.9), ('def get_user(id):', HER, 1), ('=======', SILVER, 0.7),
                 ('async def fetch_user(id):', HIM, 1), ('>>>>>>> feature/async', HIM, 0.9)]
    editor(c, CX, CY + 40, 900, 330, 1.0, lines, t, first=40, title='main.py  (merging)')
    # code lens
    lens = [('Accept Current Change', tc, HER), ('Accept Incoming Change', ti, HIM), ('Accept Both Changes', tb, IVORY)]
    x = CX - 440
    for s, tt, colr in lens:
        tw = text_width(s, TF_MONO, 18)
        hot = window(t, tt, tt + 0.9, 0.05, 0.3)
        draw_text(c, s, x, CY - 160, TF_MONO, 18, colr, 0.5 + 0.5 * hot, align='left', glow=hot)
        if hot > 0:
            c.drawPath(line(x, CY - 152, x + tw, CY - 152), stroke_paint(colr, hot, 1.4))
            ripple(c, x + tw / 2, CY - 165, t, tt + 0.1, 0.6, 6, 70, colr, 0.8)
        x += tw + 30
    if t > tf:
        k = ease_out(ramp(t, tf, tf + 0.15))
        g = (int(t * 18) % 3 - 1) * 8 * (1 - ramp(t, tf + 0.8, tf + 1.2))
        c.drawRect(skia.Rect(0, 0, W, H), fill_paint((10, 10, 11), 0.6 * k))
        draw_text(c, 'BUILD FAILED', CX + g, CY + 30, TF_MONO4, 110, IVORY, k, tracking=20, glow=1.4)
        draw_icon(c, CROSS, CX, CY - 120, 2.0, k, IVORY, 3.0, glow=1.4)
    c.restore()


# ======================================================================= BREAKDOWN
def sec_breakdown(c, t, A):
    a_sec = sec_alpha(t, 158.4, 172.3, 0.6, 0.2)
    layer(c, a_sec)
    T = [lt('Maybe your function name was better'), lt('Maybe your null check saved my life'),
         lt('Maybe we were never enemies'), lt('Just two people and one file')]
    close = ease_io(ramp(t, 158.4, 172.0))
    her(c, lerp(560, 760, close), CY - 40, 0.62, 1.0, smile=0.2 + 0.4 * close, look=0.6, glow=0.6)
    him(c, lerp(1360, 1160, close), CY - 40, 0.62, 1.0, smile=0.2 + 0.4 * close, look=-0.6, glow=0.6)
    notes = [(T[0], 'get_user  (better)', HIM, 1360), (T[1], 'if user is None: return  (saved me)', HER, 560)]
    for i, (tt, s, colr, x) in enumerate(notes):
        a = window(t, tt + 0.3, T[2] + 0.2, 0.4, 0.5)
        draw_text(c, s, CX, CY + 250 + i * 50, TF_MONO, 24, colr, a * 0.9)
    a = window(t, T[3] - 0.1, 172.4, 0.4, 0.2)
    if a > 0:
        fx, fy = CX, CY + 270
        p = P(); p.moveTo(fx - 40, fy - 55); p.lineTo(fx + 20, fy - 55); p.lineTo(fx + 40, fy - 35)
        p.lineTo(fx + 40, fy + 55); p.lineTo(fx - 40, fy + 55); p.close()
        glow_stroke(c, p, IVORY, a, 1.8, 0.8)
        draw_text(c, 'main.py', fx, fy + 90, TF_MONO, 16, SILVER, a * 0.7, tracking=3)
    c.restore()


# ======================================================================= FINAL CHORUS
def sec_final(c, t, A):
    a_sec = sec_alpha(t, 172.3, 197.9, 0.2, 0.6)
    layer(c, a_sec)
    T = [lt('So I’ll take your version, baby'), lt('And you’ll keep a piece of mine'),
         lt('We’ll delete the markers'), lt('Line by line'), lt('Commit it together'),
         lt('Push it straight to main'), lt('No more arrows'), lt('No more pain')]
    pulse = 1 + 0.02 * A['kick']
    # editor resolving
    ea = window(t, 172.3, T[4] + 0.2, 0.3, 0.4)
    if ea > 0:
        dl = [ramp(t, T[3] + i * 0.55, T[3] + i * 0.55 + 0.3) for i in range(3)]
        merged = ease_out(ramp(t, T[1] + 0.2, T[1] + 0.6))
        l1 = 'async def get_user(id):' if merged > 0.5 else 'def get_user(id):'
        lines = [('<<<<<<< HEAD', HER, 0.9 * (1 - dl[0])), (l1, IVORY if merged > 0.5 else HER, 1),
                 ('=======', SILVER, 0.7 * (1 - dl[1])),
                 ('async def fetch_user(id):', HIM, 1 - ease_out(ramp(t, T[0] + 0.3, T[0] + 0.8))),
                 ('>>>>>>> feature/async', HIM, 0.9 * (1 - dl[2]))]
        editor(c, CX, CY + 20, 900, 330, ea, lines, t, hl={1: IVORY}, title='main.py  (resolving)')
        if T[0] < t < T[2]:
            mono_label(c, 'her rename + his async', CX, CY + 230, 16, ea * 0.6 * ease_out(ramp(t, T[1] + 0.6, T[1] + 1.0)))
    # merge on the graph, push to main
    ga = window(t, T[4] - 0.1, 198.0, 0.3, 0.6)
    if ga > 0:
        mg = ease_io(ramp(t, T[4], T[4] + 1.0))
        branch_graph(c, t, ga, 1.0, merge=mg, y=CY + 250, x0=360, x1=1560)
        if t > T[5]:
            k = ease_io(ramp(t, T[5], T[5] + 0.8))
            ax = 1400
            p = line(ax, CY + 230, ax, CY + 230 - 300 * k)
            p.moveTo(ax - 18, CY + 230 - 300 * k + 22); p.lineTo(ax, CY + 230 - 300 * k); p.lineTo(ax + 18, CY + 230 - 300 * k + 22)
            glow_stroke(c, p, IVORY, ga, 2.2, 1.0)
            mono_label(c, 'origin/main', ax, CY - 100, 15, ga * 0.7 * k)
    # no more arrows: marker glyphs drift away
    na = window(t, T[6] - 0.1, 198, 0.2, 0.6)
    if na > 0:
        u = ease_in(ramp(t, T[6], T[6] + 2.0))
        rng = np.random.default_rng(3)
        for i in range(24):
            r = rng.random(3)
            ch = '<' if i % 2 else '>'
            x = 200 + r[0] * 1520 + (r[2] - 0.5) * 300 * u
            y = 120 + r[1] * 260 - u * 300
            draw_text(c, ch, x, y, TF_MONO, 40, HER if i % 2 else HIM, na * (1 - u) * 0.7)
    # the two of them
    together = ease_io(ramp(t, T[6], T[7] + 1.0))
    fa = 1 - 0.6 * ease_io(ramp(t, 172.3, 173.0)) * (1 - together)
    her(c, lerp(260, 740, together), CY - 30 - 70 * together, 0.5 * pulse, fa, smile=0.3 + 0.7 * together, look=0.6,
        eyes='happy' if together > 0.6 else 'open', glow=0.6 + together)
    him(c, lerp(1660, 1180, together), CY - 30 - 70 * together, 0.5 * pulse, fa, smile=0.3 + 0.7 * together, look=-0.6,
        eyes='happy' if together > 0.6 else 'open', glow=0.6 + together)
    if together > 0.5:
        draw_icon(c, HEART, CX, CY - 260, 0.5, ease_out(ramp(together, 0.5, 1.0)) * (1 - ease_io(ramp(t, 196.5, 197.9))),
                  IVORY, 2.2, glow=1.2 + A['kick'])
    c.restore()


# ======================================================================= OUTRO
def sec_outro(c, t, A):
    a_sec = sec_alpha(t, 197.9, END, 0.3, 0.01)
    layer(c, a_sec)
    tm = lt('Merge successful'); tn = lt('Two new conflicts in utils.py')
    fa = 1 - ease_io(ramp(t, 205.0, 205.8))
    logs = [(tm + 0.1, '[main 4f2a9c1] Merge branch ‘feature/async’', SILVER),
            (tm + 0.8, 'Merge successful.', IVORY),
            (tn + 0.1, '$ git pull', SILVER),
            (tn + 0.6, 'CONFLICT (content): Merge conflict in utils.py', IVORY),
            (tn + 1.1, 'CONFLICT (content): Merge conflict in utils.py', IVORY)]
    for i, (ts, s, colr) in enumerate(logs):
        typed(c, s, 330, 330 + i * 54, t, ts, 50, 26, fa * 0.9, colr, align='left', caret=(i == 4))
    her(c, 760, CY + 210, 0.25, fa * ease_out(ramp(t, tn + 1.4, tn + 1.9)), eyes='open', smile=-0.2)
    him(c, 1160, CY + 210, 0.25, fa * ease_out(ramp(t, tn + 1.4, tn + 1.9)), eyes='open', smile=-0.2)
    ea = window(t, 206.0, END + 1, 0.8, 0.01)
    if ea > 0:
        draw_text(c, 'aditazzz', CX, CY + 10, TF_MONO, 34, IVORY, ea, tracking=12, glow=0.4)
        mono_label(c, 'MERGE CONFLICT', CX, CY + 62, 16, ea * 0.7, SILVER, tracking=7)
        mono_label(c, 'DEADLETTER', CX, H - 90, 12, ea * 0.4, SILVER, tracking=9)
    c.restore()


SECTION_FN = {
    'intro': sec_intro, 'v1': sec_v1, 'pre1': lambda c, t, A: sec_pre(c, t, A, 'pre1'),
    'ch1': lambda c, t, A: sec_chorus(c, t, A, 'ch1'), 'v2': sec_v2,
    'pre2': lambda c, t, A: sec_pre(c, t, A, 'pre2'), 'ch2': lambda c, t, A: sec_chorus(c, t, A, 'ch2'),
    'bridge': sec_bridge, 'breakdown': sec_breakdown, 'final': sec_final, 'outro': sec_outro,
}
