"""The contact sheet (<= 1600 px wide) and the crops sheet for rl_screens, from the rendered frames.
  .venv/bin/python songs/rate-limited/screens/contact.py"""
import glob, os, sys
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit as K

O = K.OUT
CLOSE = Image.open(os.path.join(K.SONG, 'build', 'pitch2', 'bl', 'door_close.png')).convert('RGBA').resize((2560, 1440), Image.LANCZOS)   # the clean plate under the approved close frame
BZ = os.path.join(O, 'glass_bezel', 'bezel_16x9.png')


def last(d, k=-1):
    fs = sorted(glob.glob(os.path.join(O, d, 'f_*.png')))
    return Image.open(fs[k]) if fs else None


def at(d, frame):
    p = os.path.join(O, d, f'f_{frame:05d}.png')
    return Image.open(p) if os.path.exists(p) else None


def over_close(layer):
    im = CLOSE.copy(); im.alpha_composite(layer.convert('RGBA')); im.alpha_composite(Image.open(BZ)); return im.convert('RGB')


def on(col, layer):
    im = Image.new('RGBA', layer.size, col + (255,)); im.alpha_composite(layer.convert('RGBA')); return im.convert('RGB')


def fr(sid, dt):
    return int(round((K.shot(sid)['start'] + dt) * K.FPS))


tiles = []   # (label, image)
tiles.append(('2G glass  Read 2:06 AM', over_close(at('glass_2G/16x9', fr('2G', 2.2)))))
tiles.append(('5H glass  lands on the approved frame', over_close(at('glass_5H/16x9', K.frames_for('5H')[-7]))))
tiles.append(('12G glass  Read. before she sends', over_close(at('glass_12G/16x9', fr('12G', 2.0)))))
tiles.append(('8E glass texture  Read 4:37 + dots', on((196, 170, 130), at('glass_8E/glass_uv', fr('8E', 1.9))).resize((1210, 1440))))
tiles.append(('2C knock rings (highlight)', on((60, 62, 72), at('glass_2C_ripple/highlight_uv', int(round((K.onset('2C', 'knock 3', 26.4) + .15) * K.FPS)))).resize((1210, 1440))))
tiles.append(('11C sleep  first step (45% dark)', on((196, 170, 130), at('glass_11C_sleep/glass_uv', int(round((K.shot('11C')['start'] + .9) * K.FPS)))).resize((1210, 1440))))
for sid, dt, lab in (('3C', 2.27, 'usage page'), ('6B', 1.6, 'sleep story 3:57 left'), ('7G', 2.1, 'group chat'), ('7H', 1.6, 'her reply'), ('8D', 2.0, 'notes app')):
    tiles.append((f'{sid} {lab} 16:9', at(f'phone_{sid}/16x9', fr(sid, dt))))
tiles.append(('6C watch 16:9', at('watch_6C/16x9', fr('6C', .9))))
tiles.append(('5E editor 16:9', at('laptop_5E/16x9', fr('5E', .1))))
tiles.append(('13E prompt (laptop screen)', at('laptop_13E/screen', fr('13E', 4.6))))
tiles.append(('9A TV', at('tv_9A/tex', fr('9A', 2.0))))
tiles.append(('9C TV  the change', at('tv_9C/tex', int(round((K.beats_in('9C')[1] + .45) * K.FPS)))))
tiles.append(('9D TV  the party', at('tv_9D/tex', fr('9D', 1.0))))
tiles = [(l, i) for l, i in tiles if i is not None]
cols = 4; tw = 1600 // cols; th = 225 + 26
sheet = Image.new('RGB', (1600, th * ((len(tiles) + cols - 1) // cols) + 6), (22, 22, 24)); d = ImageDraw.Draw(sheet)
for k, (lab, im) in enumerate(tiles):
    t = im.convert('RGB').copy(); t.thumbnail((tw - 8, 225)); x = (k % cols) * tw + (tw - t.width) // 2; y = (k // cols) * th + 4
    sheet.paste(t, (x, y)); d.text(((k % cols) * tw + 6, y + 228), lab, fill=(220, 220, 220), font=K.font('med', 16))
sheet.save(os.path.join(O, 'contact_sheet.jpg'), quality=86)
# 9:16 strip
strip = []
for d9 in ('glass_5H/9x16', 'phone_3C/9x16', 'phone_6B/9x16', 'phone_7G/9x16', 'phone_8D/9x16', 'watch_6C/9x16', 'laptop_5E/9x16'):
    fs = sorted(glob.glob(os.path.join(O, d9, 'f_*.png')))
    if fs:
        im = Image.open(fs[-8]); strip.append(on((150, 130, 110), im) if im.mode == 'RGBA' else im.convert('RGB'))
s9 = Image.new('RGB', (1600, 410), (22, 22, 24))
for k, im in enumerate(strip):
    t = im.copy(); t.thumbnail((220, 390)); s9.paste(t, (8 + k * 228, 10))
s9.save(os.path.join(O, 'contact_sheet_9x16.jpg'), quality=86)
print('wrote', os.path.join(O, 'contact_sheet.jpg'), sheet.size, 'and contact_sheet_9x16.jpg')
