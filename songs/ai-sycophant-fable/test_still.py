import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)  # repo layout (the chat used an absolute path)
from lib import *
from face import *

surf = skia.Surface(W, H)
c = surf.getCanvas()
c.drawImage(make_bg(), 0, 0)
draw_face(c, 600, 470, 0.95, COOL, 0.9, 2.0, eyes='open', smile=0.0)
draw_face(c, 1320, 470, 0.95, IVORY, 1.0, 2.0, eyes='happy', smile=1.0)
glow_stroke(c, transformed(thumb_path(), 960, 160, 0.5), IVORY, 1, 1.6)
reveal_text(c, 'One said exactly what they liked', W / 2, 960, TF_SERIF_I, 64, 5, 0, 9)
draw_text(c, 'A', 600, 1010, TF_MONO, 22, SILVER, 0.6, tracking=6)
draw_text(c, 'B', 1320, 1010, TF_MONO, 22, SILVER, 0.6, tracking=6)
c.drawImage(make_vignette(), 0, 0)
surf.makeImageSnapshot().save(os.path.join(HERE, 'still.png'), skia.kPNG)
