"""Shared drawing kit for DEADLETTER videos (built on syco/lib.py)."""
import os, sys, math
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'songs', 'ai-sycophant-fable'))  # repo layout (the chat used an absolute path)
import numpy as np
import skia
from lib import *

CX, CY = W / 2, H / 2 - 40


def sec_alpha(t, a, b, fin=0.35, fout=0.35):
    return window(t, a - fin * 0.5, b + fout * 0.5, fin, fout)


def layer(c, a):
    c.saveLayerAlpha(None, int(255 * clamp(a)))


def mono_label(c, s, x, y, size=18, a=0.6, colr=SILVER, align='center', tracking=None, tf=None):
    draw_text(c, s, x, y, tf or TF_MONO, size, colr, a, align=align,
              tracking=size * 0.32 if tracking is None else tracking)


def typed(c, s, x, y, t, t0, cps=28, size=24, a=0.85, colr=IVORY, align='center', caret=True, tf=None):
    tf = tf or TF_MONO
    if t < t0:
        return
    n = int(clamp((t - t0) * cps, 0, len(s)))
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


def circle(x, y, r):
    p = P(); p.addCircle(x, y, r); return p


def line(x0, y0, x1, y1):
    p = P(); p.moveTo(x0, y0); p.lineTo(x1, y1); return p


def draw_icon(c, path, x, y, s, a=1.0, colr=IVORY, w=2.0, draw=1.0, glow=1.0, sy=None, rot=0.0):
    if a <= 0.003:
        return
    c.save()
    c.translate(x, y)
    if rot:
        c.rotate(rot)
    c.scale(s, s if sy is None else sy)
    pp = trim(path, 0, ease_io(draw)) if draw < 1 else path
    glow_stroke(c, pp, colr, a, w / max(s, 1e-3), glow)
    c.restore()


def ripple(c, x, y, t, t0, dur=0.9, r0=10, r1=120, colr=IVORY, a=0.8, n=2):
    for k in range(n):
        u = (t - t0 - k * 0.12) / dur
        if 0 <= u <= 1:
            r = lerp(r0, r1, ease_out(u))
            glow_stroke(c, circle(x, y, r), colr, a * (1 - u), 1.4, 0.6)


def stamp(c, s, x, y, a, colr, rot=-8, size=22):
    if a <= 0:
        return
    sc = lerp(1.6, 1.0, a)
    c.save(); c.translate(x, y); c.rotate(rot); c.scale(sc, sc)
    w = text_width(s, TF_MONO4, size, size * 0.32) + 30
    glow_stroke(c, rrect(0, -size * 0.36, w, size * 2, 6), colr, a * 0.9, 1.6, 0.8)
    draw_text(c, s, 0, 0, TF_MONO4, size, colr, a, tracking=size * 0.32, glow=0.5)
    c.restore()


def cubic(p, pts):
    p.moveTo(*pts[0])
    for i in range(1, len(pts), 3):
        p.cubicTo(*pts[i], *pts[i + 1], *pts[i + 2])
    return p


def slam_text(c, s, x, y, t, t0, size=170, colr=IVORY, a=1.0, tf=None, tracking=0):
    if t < t0 - 0.03:
        return
    k = ease_out(ramp(t, t0 - 0.03, t0 + 0.12))
    flash = max(0, 1 - (t - t0) / 0.45)
    sc = lerp(1.5, 1.0, k)
    c.save(); c.translate(x, y); c.scale(sc, sc)
    draw_text(c, s, 0, 0, tf or TF_MONO, size, colr, a * k * (0.6 + 0.4 * flash), glow=0.4 + 1.6 * flash,
              tracking=tracking)
    c.restore()


class Lyrics:
    """serif lyric track + band, shared by 16:9 and 9:16 renderers"""
    def __init__(self, lines):
        self.lines = lines
        self.band = skia.GradientShader.MakeLinear([(0, 860), (0, 960)],
                                                   [skia.Color4f(10 / 255, 10 / 255, 11 / 255, 0),
                                                    skia.Color4f(10 / 255, 10 / 255, 11 / 255, 0.9)])

    def draw(self, c, t, y=985, size=56):
        c.drawRect(skia.Rect(0, 860, W, H), skia.Paint(Shader=self.band))
        for (t0, t1, s, st) in self.lines:
            if st != 'lyric' or t < t0 - 0.1 or t > t1 + 0.5:
                continue
            reveal_text(c, s, CX, y, TF_SERIF_I, size, t, t0, t1, IVORY, 0.96, stagger=0.018, dur=0.4,
                        glow=0.35, out_dur=0.3)


def build_lines(entries, end):
    """entries: list of (t, text[, style]) -> (t0, t1, text, style) with auto end"""
    L = sorted([list(e) + (['lyric'] if len(e) == 2 else []) for e in entries], key=lambda x: x[0])
    out = []
    for i, (t, s, st) in enumerate(L):
        nxt = L[i + 1][0] if i + 1 < len(L) else end
        e = min(nxt - 0.06, t + 4.2)
        if st != 'gap':
            out.append((t, e, s, st))
    return out


def line_t(lines, text, after=0.0):
    for t0, t1, s, st in lines:
        if s == text and t0 >= after - 0.01:
            return t0
    raise KeyError(text)
