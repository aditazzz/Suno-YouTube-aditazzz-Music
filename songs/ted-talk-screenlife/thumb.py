"""Thumbnails + Short cover for TED Talk (Screenlife).

usage: MUSIC_DIR=... python3 songs/ted-talk-screenlife/thumb.py
Writes into the song's output folder:
  TED Talk (Screenlife) - YouTube thumbnail.jpg              the call has turned into his keynote: Ted on a stage in the speaker
                                                             tile, everyone else's camera off, the timer in red. "15-MINUTE STANDUP."
  TED Talk (Screenlife) - YouTube thumbnail option 2.jpg     the desktop: the sticky note "ask Ted: is the file ready?? (asked 3x)"
  TED Talk (Screenlife) - YouTube thumbnail option 3.jpg     "End meeting for all: only the host can end this meeting"
  TED Talk (Screenlife) - YouTube thumbnail (no text).jpg    the main picture without words
  TED Talk (Screenlife) - Short cover (9x16).jpg / (9x16, no text).jpg
"""
import os, sys
import numpy as np
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
U, AP = sc.U, sc.AP
F_ANTON = os.path.join(C.FONTS, "Anton-Regular.ttf")
RED = (229, 72, 77)

def shot(t, cx, cy, zoom, W=1920, H=1080, vert=False, cursor=True):
    """the screen at time t through a chosen camera (no lyrics, no overlays)"""
    S = sc.state(t, vert)
    s = (H / U.DH if vert else W / U.DW) * zoom
    cam = U.Cam(W, H, cx, cy, s)
    img = np.zeros((H, W, 3), np.float32)
    AP.desktop(img, cam, S); AP.desktop_items(img, cam, S); AP.huddle(img, cam, S); AP.notes(img, cam, S); AP.calendar(img, cam, S)
    for d in S.dialogs: AP.dialog(img, cam, S, d)
    for m in S.menus: AP.menu(img, cam, S, m)
    AP.dm_window(img, cam, S); AP.menubar(img, cam, S); AP.dock(img, cam, S); AP.notifications(img, cam, S)
    if cursor: U.cursor(img, cam, S.cursor[0], S.cursor[1], 1.0, 1.0, 0.0)
    return Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8))

def words(img, lines, x, y, size, lead=1.0, fill=(255, 255, 255), red_word=None, stroke=0, stroke_fill=(10, 10, 14), shadow=True, anchor="la"):
    d = ImageDraw.Draw(img); f = ImageFont.truetype(F_ANTON, size)
    if shadow:
        sh = Image.new("L", img.size, 0); ds = ImageDraw.Draw(sh); yy = y
        for ln in lines:
            ds.text((x + size * 0.03, yy + size * 0.05), ln, font=f, fill=190, stroke_width=stroke + 2, stroke_fill=190, anchor=anchor); yy += int(size * lead)
        img.paste((0, 0, 0), (0, 0), sh.filter(ImageFilter.GaussianBlur(size * 0.07)))
        d = ImageDraw.Draw(img)
    yy = y
    for ln in lines:
        if red_word and red_word in ln and anchor == "la":
            xx = x
            for wd in ln.split(" "):
                d.text((xx, yy), wd, font=f, fill=RED if wd == red_word else fill, stroke_width=stroke, stroke_fill=stroke_fill)
                xx += d.textlength(wd + " ", font=f)
        else:
            d.text((x, yy), ln, font=f, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill, anchor=anchor)
        yy += int(size * lead)

def badge(img, x, y, h=58, txt="CLAUDE ANIMATED THIS"):
    d = ImageDraw.Draw(img); f = ImageFont.truetype(F_ANTON, int(h * 0.6)); w = d.textlength(txt, font=f) + h * 0.9
    d.rounded_rectangle((x, y, x + w, y + h), h // 2, fill=(224, 53, 43)); d.text((x + h * 0.45, y + h / 2 + 1), txt, font=f, fill=(255, 255, 255), anchor="lm")

if __name__ == "__main__":
    W, H = 1920, 1080
    t_main = sc.TT[4] + 0.9                      # the final chorus: Ted on his stage, the timer long past the end
    base = shot(t_main, 232.0, 352.0, 2.3, cursor=False)          # Ted on his keynote stage, in the speaker tile
    timer = shot(t_main, 125.0, 81.0, 3.4, cursor=False).crop((420, 470, 1650, 612))   # the meeting timer, long past the end
    def callout(img, piece, x, y, w):
        piece = piece.resize((w, int(piece.height * w / piece.width)), Image.LANCZOS)
        sh = Image.new("L", img.size, 0); ImageDraw.Draw(sh).rounded_rectangle((x + 8, y + 14, x + w + 8, y + piece.height + 14), 18, fill=170)
        img.paste((0, 0, 0), (0, 0), sh.filter(ImageFilter.GaussianBlur(16)))
        ImageDraw.Draw(img).rounded_rectangle((x - 6, y - 6, x + w + 6, y + piece.height + 6), 20, fill=(70, 70, 78))
        m = Image.new("L", piece.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, piece.width - 1, piece.height - 1), 16, fill=255)
        img.paste(piece, (x, y), m)
    base_nt = base.copy(); callout(base_nt, timer, 70, 70, 900)
    base_nt.save(os.path.join(OUT, f"{T} - YouTube thumbnail (no text).jpg"), quality=93)
    main = base.copy(); callout(main, timer, 70, 70, 900)
    badge(main, 76, 300)
    words(main, ["15-MINUTE", "STANDUP."], 70, 380, 176, lead=0.98, fill=(255, 255, 255))
    main.save(os.path.join(OUT, f"{T} - YouTube thumbnail.jpg"), quality=93)
    # option 2: the desktop at 9:14 a.m.
    o2 = shot(0.0, 990.0, 250.0, 1.75, cursor=False)
    badge(o2, 60, 50); words(o2, ["IS THE FILE", "READY?"], 56, 140, 170, lead=1.02, fill=(28, 24, 30), shadow=False)
    o2.save(os.path.join(OUT, f"{T} - YouTube thumbnail option 2.jpg"), quality=93)
    # option 3: nobody can end it
    o3 = shot(sc.T_NOEND + 0.9, 640.0, 470.0, 2.2, cursor=True)
    badge(o3, 60, 50); words(o3, ["NOBODY", "CAN END IT."], 56, 140, 170, lead=1.02)
    o3.save(os.path.join(OUT, f"{T} - YouTube thumbnail option 3.jpg"), quality=93)
    # Short cover: Ted's keynote in the speaker tile
    v = shot(t_main, 322.0, 372.0, 1.5, 1080, 1920, vert=True, cursor=False)
    v.save(os.path.join(OUT, f"{T} - Short cover (9x16, no text).jpg"), quality=93)
    callout(v, timer, 70, 1430, 940)
    badge(v, 64, 118, 60); words(v, ["15-MINUTE", "STANDUP."], 60, 196, 190, lead=0.98)
    v.save(os.path.join(OUT, f"{T} - Short cover (9x16).jpg"), quality=93)
    print("thumbnails written to", OUT)
