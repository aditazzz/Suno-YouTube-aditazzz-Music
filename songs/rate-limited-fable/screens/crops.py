"""Zoomed crops of every detail rl_screens claims, from the final frames -> build/screens/crops.jpg (<= 1600 px)."""
import os, sys
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit as K

O = K.OUT


def f(d, sid, dt=None, frame=None):
    n = frame if frame is not None else int(round((K.shot(sid)['start'] + dt) * K.FPS))
    return Image.open(os.path.join(O, d, f'f_{n:05d}.png'))


def on(im, col=(200, 170, 130)):
    b = Image.new('RGBA', im.size, col + (255,)); b.alpha_composite(im.convert('RGBA')); return b.convert('RGB')


close = Image.open(os.path.join(K.SONG, 'build', 'pitch2', 'frames', '02_close_r3.jpg')).convert('RGB').resize((2560, 1440), Image.LANCZOS)
end5h = K.frames_for('5H')[-7]
c5 = close.copy().convert('RGBA'); c5.alpha_composite(f('glass_5H/16x9', '5H', frame=end5h)); c5 = c5.convert('RGB')
t58 = K.onset('6B', 'fifty-eight', 97.86)
items = [
    ('5H approved (left) vs ours on it (right)', None),
    ('2G Read 2:06 AM', on(f('glass_2G/16x9', '2G', 2.25)).crop((120, 30, 720, 330))),
    ('12G draft + Read.', on(f('glass_12G/16x9', '12G', 2.2)).crop((240, 30, 720, 330))),
    ('8E Read 4:37 AM + dots', on(f('glass_8E/glass_uv', '8E', 1.9)).crop((100, 300, 1300, 1000))),
    ('3C 429 / limit reached', f('phone_3C/16x9', '3C', 2.27).crop((700, 0, 2000, 560))),
    ('3C 3h 51m', f('phone_3C/16x9', '3C', 2.27).crop((700, 500, 2000, 1100))),
    ('6B 3:58 left (on the word)', f('phone_6B/16x9', '6B', frame=int(round((t58 + .3) * K.FPS))).crop((700, 500, 2000, 1100))),
    ('7G receipts in clock order', f('phone_7G/16x9', '7G', 2.2).crop((900, 500, 2200, 1100))),
    ('8D FINAL v2', f('phone_8D/16x9', '8D', 2.1).crop((800, 900, 2100, 1440))),
    ('6C watch', f('watch_6C/16x9', '6C', .9).crop((780, 100, 1780, 700))),
    ('5E tab + caret', f('laptop_5E/16x9', '5E', .05).crop((850, 0, 1850, 400))),
    ('13E the prompt', f('laptop_13E/screen', '13E', 4.6).crop((500, 760, 2060, 1140))),
    ('9D LIVE and the time, clear', f('tv_9D/tex', '9D', 1.0).crop((0, 0, 1000, 420))),
    ('9D source line', f('tv_9D/tex', '9D', 1.0).crop((60, 1000, 1200, 1230))),
    ('3C battery 3%', f('phone_3C/screen', '3C', 2.27).crop((700, 30, 1320, 160))),
]
cols = 3; tw = 1600 // cols; th = 300
sheet = Image.new('RGB', (1600, th * ((len(items) + cols - 1) // cols)), (22, 22, 24)); d = ImageDraw.Draw(sheet)
for k, (lab, im) in enumerate(items):
    x, y = (k % cols) * tw, (k // cols) * th
    if im is None:
        a = close.crop((130, 20, 730, 420)); b = c5.crop((130, 20, 730, 420)); im = Image.new('RGB', (1200, 400)); im.paste(a, (0, 0)); im.paste(b, (600, 0))
    t = im.copy(); t.thumbnail((tw - 8, th - 28)); sheet.paste(t, (x + 4, y + 4)); d.text((x + 6, y + th - 22), lab, fill=(230, 230, 230), font=K.font('med', 16))
sheet.save(os.path.join(O, 'crops.jpg'), quality=88); print('wrote crops.jpg', sheet.size)
