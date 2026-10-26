"""Thumbnails + Short cover for TED Talk (Shadow Play).

usage: MUSIC_DIR=... python3 songs/ted-talk-shadow-play/thumb.py
Writes into the song's output folder:
  TED Talk (Shadow Play) - YouTube thumbnail.jpg              his giant shadow reaching over the room, she has her hand up
                                                              (the red clip), EVERY STANDUP HAS A TED. in cut-paper capitals
  TED Talk (Shadow Play) - YouTube thumbnail option 2.jpg     IT'S A TED TALK hanging on strings over his shadow (a frame of the video)
  TED Talk (Shadow Play) - YouTube thumbnail option 3.jpg     the end: the stage gone dark, the iris onto the road he walked off down
  TED Talk (Shadow Play) - YouTube thumbnail (no text).jpg    the main picture without words
  TED Talk (Shadow Play) - Short cover (9x16).jpg / (9x16, no text).jpg
"""
import os, sys, math
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
from studio.config import load_song
from studio.render import load_scene
from studio import core as C

sc = load_scene(HERE)
song = load_song(HERE)
OUT = song["out_dir"]; T = song["title"]
os.makedirs(OUT, exist_ok=True)
ST, PR, PP = sc.ST, sc.PR, sc.PP
F_ANTON = os.path.join(C.FONTS, "Anton-Regular.ttf")
RED = (224, 53, 43); INK = (14, 9, 7); CREAM = (246, 231, 200)

def make_cam(W, H, s, fx, floor_y):
    """a camera: world -> screen scale s, world x fx at the centre, the floor at screen y floor_y"""
    cam = ST.Cam(1920, 1080)
    cam.W, cam.H, cam.vert = W, H, False
    cam.s = s; cam.ox = W / 2 - fx * s; cam.oy = floor_y - ST.FLOOR * s
    return cam

def stage(cam, me_x=760.0, ted_x=1220.0, g=2.15, crowd=(("Lee", 360, 1), ("Sam", 515, 1), ("Priya", 1500, -1), ("Marcus", 1690, -1)),
          asleep=("Marcus",), t=40.0, me_pose=None, ted_pose=None, windows=False, level=1.0):
    W, H = cam.W, cam.H
    light = ST.screen_light(cam, t, level, 0.25, np.array([ted_x, 520.0]), 900.0, 0.0)
    L = ST.Layers(W, H)
    deep = L.mask("deep")
    if windows:
        for (x, y, w, h) in ((1515, 140, 255, 230),):
            fr, holes = PR.window_blinds(x, y, w, h); ST.fill(deep, cam, fr); ST.fill(deep, cam, holes, 0)
    for x, s_ in ((70, 1.25), (1850, 1.3)):
        ST.fill(deep, cam, PR.plant(x, s_, t))
    tops = {}
    for i, (n, x0, f) in enumerate(crowd):
        p = PP.Pose(sit=1.0, head=0.02, slump=0.85 if n in asleep else 0.0, sh_f=0.08 + 0.3 * (i % 3 == 1), el_f=0.9 * (i % 3 == 1) + 0.2)
        ST.fill(L.mask("near"), cam, [np.asarray(c) for c in PR.chair(x0 - f * 20, f, 0.95)])
        tops[n] = sc.put_puppet(L, cam, n, x0, f, p, "crisp")["top"]
        if n in asleep:
            for j, (c, s_, op) in enumerate(PR.zzz(tops[n][0] + f * 30, tops[n][1] + 10, 0.55 + i * 0.37, 2.2)):
                c = (c[0], tops[n][1] + 10 - (tops[n][1] + 10 - c[1]) * 0.6)
                PR.stamp(L.mask("near"), cam, PR.glyph("Z" if j % 2 else "z", PR.F_SERIF, 120), c, s_ * min(1, op * 1.6))
    ST.fill(L.mask("near"), cam, [np.asarray(c) for c in PR.chair(me_x - 20, 1, 0.95)])
    mp = me_pose or PP.Pose(sit=1.0, sh_f=2.75, el_f=0.15, head=-0.12)
    a_me = sc.put_puppet(L, cam, "Me", me_x, 1, mp, "crisp")
    tp = ted_pose or PP.Pose(mouth=0.6, sh_f=1.62, el_f=0.12, sh_b=0.3, el_b=0.5, head=-0.05)
    a_ted = sc.put_puppet(L, cam, "Ted", ted_x, -1, tp, "crisp", g=g)
    img = L.composite(light)
    c = cam.P(a_me["top"]); r = 26 * cam.s; R_ = int(r * 7)       # the red clip's little glow
    y0, y1 = max(0, int(c[1]) - R_), min(H, int(c[1]) + R_); x0, x1 = max(0, int(c[0]) - R_), min(W, int(c[0]) + R_)
    yy, xx = np.ogrid[y0:y1, x0:x1]
    img[y0:y1, x0:x1] += (np.exp(-(((xx - c[0]) ** 2 + (yy - c[1]) ** 2) / (r * r * 4))) * 0.22)[..., None] * np.array([1.0, 0.12, 0.06], np.float32)
    img += sc.grain(W, H, 3)[..., None]
    return Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)), a_me, a_ted

def words(img, lines, x, y, size, lead=1.0, fill=INK, red_word="TED.", stroke=0, stroke_fill=CREAM, shadow=False):
    """big condensed capitals, black like cut paper (the red word is the one colour)"""
    d = ImageDraw.Draw(img); f = ImageFont.truetype(F_ANTON, size); yy = y
    if shadow:
        sh = Image.new("L", img.size, 0); ds = ImageDraw.Draw(sh); y2 = y
        for ln in lines:
            ds.text((x + size * 0.03, y2 + size * 0.05), ln, font=f, fill=150, stroke_width=stroke, stroke_fill=150); y2 += int(size * lead)
        img.paste((40, 20, 10), (0, 0), sh.filter(ImageFilter.GaussianBlur(size * 0.06)))
        d = ImageDraw.Draw(img)
    for ln in lines:
        xx = x
        for k, wd in enumerate(ln.split(" ")):
            col = RED if wd == red_word else fill
            d.text((xx, yy), wd, font=f, fill=col, stroke_width=stroke, stroke_fill=stroke_fill)
            xx += d.textlength(wd + " ", font=f)
        yy += int(size * lead)

def badge(img, x, y, h=58, txt="CLAUDE ANIMATED THIS"):
    d = ImageDraw.Draw(img); f = ImageFont.truetype(F_ANTON, int(h * 0.6)); w = d.textlength(txt, font=f) + h * 0.9
    d.rounded_rectangle((x, y, x + w, y + h), h // 2, fill=RED); d.text((x + h * 0.45, y + h / 2 + 1), txt, font=f, fill=(255, 255, 255), anchor="lm")

def video_frame(t, W=1920, H=1080):
    C.STATE["clean"] = True
    im = sc.render_frame(t, W, H, int(t * 30))
    C.STATE["clean"] = False
    return Image.fromarray(im)

if __name__ == "__main__":
    W, H = 1920, 1080
    cam = make_cam(W, H, 1.25, 1010.0, 1062.0)
    base, a_me, a_ted = stage(cam)
    base.save(os.path.join(OUT, f"{T} - YouTube thumbnail (no text).jpg"), quality=93)
    main = base.copy()
    badge(main, 64, 30, 54)
    words(main, ["EVERY STANDUP", "HAS A TED."], 60, 92, 164, lead=1.03)
    main.save(os.path.join(OUT, f"{T} - YouTube thumbnail.jpg"), quality=93)
    # option 2: the hanging letters over his shadow (a frame of the video)
    o2 = video_frame(28.6); badge(o2, 64, 965)
    o2.save(os.path.join(OUT, f"{T} - YouTube thumbnail option 2.jpg"), quality=93)
    # option 3: the end, the stage dark and the iris onto the road
    o3 = video_frame(153.0); badge(o3, 64, 50)
    words(o3, ["HE TOOK IT", "OFFLINE."], 64, 120, 150, lead=1.05, fill=CREAM, red_word="OFFLINE.", stroke=0, shadow=True)
    o3.save(os.path.join(OUT, f"{T} - YouTube thumbnail option 3.jpg"), quality=93)
    # Short cover: the same picture, vertical
    camv = make_cam(1080, 1920, 1.62, 950.0, 1880.0)
    v, _, _ = stage(camv, me_x=740.0, ted_x=1070.0, crowd=(("Sam", 515, 1), ("Dana", 1330, -1)), asleep=("Dana",))
    v.save(os.path.join(OUT, f"{T} - Short cover (9x16, no text).jpg"), quality=93)
    badge(v, 60, 120, 60); words(v, ["EVERY", "STANDUP", "HAS A TED."], 56, 200, 190, lead=1.04)
    v.save(os.path.join(OUT, f"{T} - Short cover (9x16).jpg"), quality=93)
    print("thumbnails written to", OUT)
