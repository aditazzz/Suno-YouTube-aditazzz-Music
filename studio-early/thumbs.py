import sys, os, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)  # repo layout (the chat used an absolute path)
from kit import *

def load(proj):
    spec = importlib.util.spec_from_file_location('scenes_' + os.path.basename(proj), os.path.join(proj, 'scenes.py'))
    m = importlib.util.module_from_spec(spec); sys.path.insert(0, proj); spec.loader.exec_module(m); return m

def finish(surf, path):
    c = surf.getCanvas()
    g = make_grain(1, seed=5)[0]
    c.drawImageRect(g, skia.Rect(0, 0, W, H), skia.SamplingOptions(), skia.Paint(BlendMode=skia.BlendMode.kOverlay, Alphaf=0.10))
    c.drawImage(make_vignette(), 0, 0)
    surf.makeImageSnapshot().save(path, skia.kPNG)

A = {'kick': 0.3, 'energy': 1}
# ---- Graceful Shutdown
G = load(os.path.join(HERE, '..', 'songs', 'graceful-shutdown-fable'))
for text in (True, False):
    s = skia.Surface(W, H); c = s.getCanvas(); c.drawImage(make_bg(), 0, 0)
    c.save(); c.translate(0, 230)
    G.world(c, 40.0, A, 1.0, moon_xy=(1500, 60))
    c.restore()
    dy = 40 if text else -10
    c.save(); c.translate(CX, CY + dy)
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-420, -180, 420, 180), 18, 18), fill_paint((12, 12, 13), 0.96))
    glow_stroke(c, rrect(0, 0, 840, 360, 18), IVORY, 0.9, 2.0, 0.8)
    draw_text(c, 'Save changes to “the world”?', 0, -70, TF_SERIF_I, 58, IVORY, 1.0, glow=0.4)
    mono_label(c, 'it will close in 30 seconds', 0, -12, 20, 0.6)
    for bx, lab, hi in ((-170, 'DON’T SAVE', 0), (170, 'SAVE', 1)):
        glow_stroke(c, rrect(bx, 90, 260, 72, 12), IVORY if hi else SILVER, 0.95 if hi else 0.55, 2.0, 0.4 + hi)
        mono_label(c, lab, bx, 98, 22, 0.95 if hi else 0.6, IVORY if hi else SILVER)
    c.restore()
    if text:
        draw_text(c, 'GRACEFUL SHUTDOWN', CX, 160, TF_MONO4, 96, IVORY, 1.0, tracking=20, glow=0.9)
    finish(s, os.path.join(HERE, '..', 'songs', 'graceful-shutdown-fable', 'out', f'thumb_{"text" if text else "clean"}.png'))
import sys as _s
if len(_s.argv) > 1: raise SystemExit
# ---- Merge Conflict
M = load(os.path.join(HERE, '..', 'songs', 'merge-conflict'))
for text in (True, False):
    s = skia.Surface(W, H); c = s.getCanvas(); c.drawImage(make_bg(), 0, 0)
    oy = 70 if text else 20
    M.her(c, 330, CY + oy, 0.95, 1.0, look=0.8, glow=1.4)
    M.him(c, 1590, CY + oy, 0.95, 1.0, look=-0.8, glow=1.4)
    for i, (s_, colr) in enumerate((('<<<<<<< HEAD', M.HER), ('=======', SILVER), ('>>>>>>> feature', M.HIM))):
        draw_text(c, s_, CX, CY - 60 + oy + i * 110, TF_MONO4, 54, colr, 1.0, tracking=4, glow=0.8)
    if text:
        draw_text(c, 'MERGE CONFLICT', CX, 160, TF_MONO4, 104, IVORY, 1.0, tracking=22, glow=0.9)
    finish(s, os.path.join(HERE, '..', 'songs', 'merge-conflict', 'out', f'thumb_{"text" if text else "clean"}.png'))
