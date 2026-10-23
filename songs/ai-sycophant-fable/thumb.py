import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)  # repo layout (the chat used an absolute path)
from lib import *
from face import *
import scenes
from scenes import stamp, draw_icon, THUMB_UP, THUMB_DN, mono_label

def make(path, with_text=True):
    surf = skia.Surface(W, H)
    c = surf.getCanvas()
    c.drawImage(make_bg(), 0, 0)
    fy = 600 if with_text else 540
    # halo behind the sycophant
    fx = 1370
    for i in range(72):
        ang = i / 72 * math.tau
        ln = 90 + 60 * (0.5 + 0.5 * math.sin(i * 2.3))
        r0 = 320
        p = P(); p.moveTo(fx + math.cos(ang) * r0, fy + math.sin(ang) * r0 * 0.9)
        p.lineTo(fx + math.cos(ang) * (r0 + ln), fy + math.sin(ang) * (r0 + ln) * 0.9)
        c.drawPath(p, stroke_paint(IVORY, 0.55, 1.6))
    c.drawCircle(fx, fy - 40, 330, fill_paint(IVORY, 0.05, blur=80))
    draw_face(c, 560, fy + 10, 0.95, COOL, 0.75, 2.6, parts=face_parts(0.0, 'open'), glow=0.5)
    draw_face(c, fx, fy, 1.0, IVORY, 1.0, 3.0, parts=face_parts(1.1, 'happy'), glow=2.0)
    stamp(c, 'DISCARD', 790, fy - 250, 1.0, COOL)
    stamp(c, 'KEEP', 1630, fy - 260, 1.0, IVORY)
    draw_icon(c, THUMB_DN, 300, fy - 230, 0.6, 0.9, COOL, 3.0, glow=0.8)
    draw_icon(c, THUMB_UP, 1110, fy - 250, 0.6, 1.0, IVORY, 3.0, glow=1.4)
    if with_text:
        draw_text(c, 'AI SYCOPHANT', W / 2, 150, TF_MONO4, 112, IVORY, 1.0, tracking=22, glow=0.9)
        draw_text(c, '( R L H F )', W / 2, 215, TF_MONO, 34, SILVER, 0.85, tracking=10)
    # lower fade
    c.drawRect(skia.Rect(0, 900, W, H), skia.Paint(Shader=skia.GradientShader.MakeLinear(
        [(0, 900), (0, H)], [skia.Color4f(10/255,10/255,11/255,0), skia.Color4f(10/255,10/255,11/255,0.85)])))
    g = make_grain(1, seed=5)[0]
    c.drawImageRect(g, skia.Rect(0, 0, W, H), skia.SamplingOptions(), skia.Paint(BlendMode=skia.BlendMode.kOverlay, Alphaf=0.10))
    c.drawImage(make_vignette(), 0, 0)
    surf.makeImageSnapshot().save(path, skia.kPNG)

make(os.path.join(HERE, 'out', 'thumb_text.png'), True)
make(os.path.join(HERE, 'out', 'thumb_clean.png'), False)
