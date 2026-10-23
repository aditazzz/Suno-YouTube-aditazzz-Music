"""Single-line contour face + icons, fine-line tattoo style."""
import math
import numpy as np
import skia
from lib import *


def _mirror(pts):
    return [(-x, y) for (x, y) in pts]


def cubic(p, pts):
    """pts: start, then triples of control points"""
    p.moveTo(*pts[0])
    for i in range(1, len(pts), 3):
        p.cubicTo(*pts[i], *pts[i + 1], *pts[i + 2])
    return p


def face_parts(smile=0.0, eyes='open', look=0.0, mouth_open=0.0, brow=0.0):
    """Return ordered dict name->path in local coords (face ~ 480 tall, eyes at y=-30).
    smile: -0.3..1.2 ; eyes: 'open' | 'closed' | 'happy' ; look: iris x offset -1..1"""
    parts = {}

    # head contour: one side flows into the other (open top, fine-line style)
    p = P()
    cubic(p, [(-150, -150),
              (-160, -60), (-162, 30), (-138, 110),
              (-116, 168), (-62, 210), (0, 214),
              (62, 210), (116, 168), (138, 110),
              (162, 30), (160, -60), (150, -150)])
    parts['contour'] = p

    # hair: long single strokes framing the face
    h = P()
    cubic(h, [(8, -262), (-120, -268), (-196, -170), (-196, -40),
              (-196, 80), (-178, 170), (-214, 300), ])
    cubic(h, [(8, -262), (130, -266), (200, -170), (198, -40),
              (196, 90), (182, 180), (226, 310)])
    cubic(h, [(-30, -250), (-96, -220), (-150, -170), (-156, -110)])
    cubic(h, [(40, -248), (110, -214), (150, -160), (158, -96)])
    cubic(h, [(-205, 60), (-238, 160), (-226, 250), (-262, 330)])
    cubic(h, [(206, 70), (236, 170), (228, 250), (262, 336)])
    parts['hair'] = h

    # brows
    b = P()
    by = -66 - brow * 10
    cubic(b, [(-122, by + 6), (-100, by - 14), (-58, by - 16), (-30, by - 2)])
    cubic(b, [(122, by + 6), (100, by - 14), (58, by - 16), (30, by - 2)])
    parts['brows'] = b

    # eyes
    e = P()
    if eyes == 'open':
        for sx in (-1, 1):
            cx = 75 * sx
            cubic(e, [(cx - 38 * sx, -26), (cx - 22 * sx, -46), (cx + 18 * sx, -46), (cx + 38 * sx, -24)])
            cubic(e, [(cx - 34 * sx, -24), (cx - 16 * sx, -12), (cx + 16 * sx, -12), (cx + 34 * sx, -22)])
            ir = 12
            e.addCircle(cx + look * 10, -30, ir)
            e.addCircle(cx + look * 10, -30, 3.0)
    elif eyes == 'closed':
        for sx in (-1, 1):
            cx = 75 * sx
            cubic(e, [(cx - 38 * sx, -30), (cx - 20 * sx, -16), (cx + 18 * sx, -16), (cx + 38 * sx, -28)])
            for k in range(4):
                u = 0.2 + k * 0.2
                x = cx + sx * lerp(-30, 30, u)
                yb = -18 - 4 * math.sin(u * math.pi)
                e.moveTo(x, yb + 4)
                e.lineTo(x - sx * 3 * (k - 1.5), yb + 13)
    else:  # happy: upturned crescents, the eerie 'pleased' face
        for sx in (-1, 1):
            cx = 75 * sx
            cubic(e, [(cx - 36 * sx, -20), (cx - 20 * sx, -42), (cx + 18 * sx, -42), (cx + 36 * sx, -20)])
            for k in range(3):
                u = 0.3 + k * 0.2
                x = cx + sx * lerp(-28, 28, u)
                e.moveTo(x, -38 - 2 * math.sin(u * 3))
                e.lineTo(x + sx * (k - 1) * 4, -50)
    parts['eyes'] = e

    # nose: one continuous line from the brow
    n = P()
    cubic(n, [(-30, -62), (-14, -40), (-4, 8), (-14, 46),
              (-22, 62), (-6, 74), (6, 68)])
    cubic(n, [(18, 66), (26, 64), (30, 58), (26, 50)])
    parts['nose'] = n

    # mouth
    s = smile
    cx, cy = 50 + 12 * max(s, 0), 116 - 18 * s
    m = P()
    # upper lip with cupid's bow
    cubic(m, [(-cx, cy), (-30, 104 - 4 * s), (-14, 98 - 2 * s), (0, 104 - 2 * s),
              (14, 98 - 2 * s), (30, 104 - 4 * s), (cx, cy)])
    # parting line
    mid = 116 + 10 * s + mouth_open * 6
    cubic(m, [(-cx, cy), (-20, mid), (20, mid), (cx, cy)])
    # lower lip
    ly = 134 + 6 * s + mouth_open * 14
    cubic(m, [(-cx + 14, cy + 8 + 2 * s), (-16, ly), (16, ly), (cx - 14, cy + 8 + 2 * s)])
    if s > 0.5:  # smile creases
        k = (s - 0.5) * 2
        cubic(m, [(-cx - 10, cy - 18 * k), (-cx - 16, cy - 4), (-cx - 12, cy + 8), (-cx - 4, cy + 14 * k)])
        cubic(m, [(cx + 10, cy - 18 * k), (cx + 16, cy - 4), (cx + 12, cy + 8), (cx + 4, cy + 14 * k)])
    parts['mouth'] = m

    # neck + collarbone
    k = P()
    cubic(k, [(-64, 182), (-60, 240), (-64, 290), (-80, 330)])
    cubic(k, [(64, 182), (60, 240), (64, 290), (80, 330)])
    cubic(k, [(-80, 330), (-140, 352), (-220, 350), (-300, 372)])
    cubic(k, [(80, 330), (140, 352), (220, 350), (300, 372)])
    parts['neck'] = k
    return parts


ORDER = ['contour', 'brows', 'eyes', 'nose', 'mouth', 'neck', 'hair']


def draw_face(canvas, x, y, scale=1.0, c=IVORY, a=1.0, w=2.0, draw=1.0, parts=None,
              glow=1.0, dash=None, rot=0.0, skip=(), **kw):
    """draw progressively (draw 0..1 across parts in ORDER)"""
    if a <= 0.003:
        return
    parts = parts or face_parts(**kw)
    canvas.save()
    canvas.translate(x, y)
    canvas.rotate(rot)
    canvas.scale(scale, scale)
    names = [n for n in ORDER if n not in skip]
    N = len(names)
    for i, name in enumerate(names):
        u = clamp(draw * N - i * 0.55)   # overlap parts slightly
        if u <= 0:
            continue
        path = trim(parts[name], 0, ease_io(u)) if u < 1 else parts[name]
        glow_stroke(canvas, path, c, a, w / scale, glow, dash=dash)
    canvas.restore()


def face_shards(parts, seg=14.0, names=None):
    """break face into short polyline segments: list of (pts array, center, name)"""
    out = []
    for name in (names or ORDER):
        for cont in sample_path(parts[name], 3.0):
            n = max(1, int(len(cont) * 3.0 / seg))
            idx = np.linspace(0, len(cont) - 1, n + 1).astype(int)
            for i in range(n):
                pts = cont[idx[i]:idx[i + 1] + 1]
                if len(pts) >= 2:
                    out.append((pts, pts.mean(0), name))
    return out


def draw_shards(canvas, shards, x, y, scale, frag, t, c=IVORY, a=1.0, w=2.0, seed=0, drift=(0, -1),
                glow=0.8, spread=1.0):
    """frag 0..1: shards drift away, rotate, fade"""
    canvas.save()
    canvas.translate(x, y)
    canvas.scale(scale, scale)
    rng = np.random.default_rng(seed)
    for i, (pts, cen, name) in enumerate(shards):
        r = rng.random(4)
        thresh = r[0]
        f = clamp((frag - thresh * 0.6) / 0.4)
        if f <= 0:
            path = poly(pts)
            glow_stroke(canvas, path, c, a, w / scale, glow)
            continue
        f = ease_in(f) * 0.6 + f * 0.4
        dirv = cen / (np.linalg.norm(cen) + 40)
        dx = (dirv[0] * 140 + drift[0] * 90 + (r[1] - 0.5) * 120) * f * spread
        dy = (dirv[1] * 140 + drift[1] * 90 + (r[2] - 0.5) * 120 + noise1(t * 0.7 + i, 3) * 10) * f * spread
        ang = (r[3] - 0.5) * 120 * f
        canvas.save()
        canvas.translate(cen[0] + dx, cen[1] + dy)
        canvas.rotate(ang)
        q = pts - cen
        glow_stroke(canvas, poly(q), c, a * (1 - f * 0.85), w / scale, glow)
        canvas.restore()
    canvas.restore()


# ---------------------------------------------------------------- icons
def thumb_path(down=False):
    """minimal fine-line thumb (local box ~ 200x200, centered)"""
    p = P()
    # cuff
    p.addRoundRect(skia.Rect(-96, -10, -58, 86), 6, 6)
    # hand body + thumb, one line
    cubic(p, [(-58, -2),
              (-30, -14), (-6, -40), (4, -78),
              (10, -100), (40, -96), (36, -66),
              (32, -40), (24, -20), (26, -12),
              (60, -14), (86, -12), (86, 6),
              (86, 18), (76, 22), (70, 24),
              (84, 28), (84, 46), (68, 48),
              (80, 54), (78, 70), (62, 70),
              (72, 76), (68, 92), (52, 92),
              (20, 92), (-30, 90), (-58, 80)])
    # finger separations
    cubic(p, [(70, 24), (50, 24), (40, 26), (32, 26)])
    cubic(p, [(68, 48), (50, 48), (40, 48), (32, 48)])
    cubic(p, [(62, 70), (50, 70), (40, 70), (32, 70)])
    if down:
        m = skia.Matrix(); m.setScale(1, -1)
        p.transform(m)
    return p


def cursor_path():
    p = P()
    p.moveTo(0, 0); p.lineTo(0, 64); p.lineTo(16, 50); p.lineTo(28, 76)
    p.lineTo(38, 72); p.lineTo(26, 46); p.lineTo(46, 46); p.close()
    return p
