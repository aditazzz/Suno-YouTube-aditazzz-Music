"""The watch (6C), the laptop editor (5E) and the morning prompt (13E): screens of our own (rl_screens). No maker's marks."""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit as K
import phone as P

# ------------------------------------------------------------------ 6C: the watch buzzes. TIME TO STAND! (it is 3:59 AM)
WW, WH = 1000, 1200
TEAL = (90, 220, 210)


def stand_figure(im, cx, cy, s, p, col):
    """a little figure getting up: sitting (p=0) to standing tall, arms up in a stretch (p=1)"""
    d = ImageDraw.Draw(im); w = int(24 * s)
    hip = (cx, cy + 50 * s * (1 - p) + 20 * s * p); sh = (cx, hip[1] - 120 * s)
    K.circle(im, cx, sh[1] - 52 * s, 32 * s, col)
    d.line([sh, hip], fill=col, width=w)
    for sg in (-1, 1):                                                     # legs: bent forward when sitting, apart when standing
        knee = (cx + sg * 10 * s * p + 70 * s * (1 - p), hip[1] + 70 * s * p + 6 * s * (1 - p)); foot = (cx + sg * 30 * s * p + 70 * s * (1 - p), hip[1] + 135 * s * p + 80 * s * (1 - p))
        d.line([hip, knee, foot], fill=col, width=w, joint='curve')
        hand = (cx + sg * (40 + 40 * p) * s, sh[1] + (70 - 150 * p) * s)       # arms: on the knees, then up
        d.line([(cx, sh[1] + 12 * s), hand], fill=col, width=w)
        K.circle(im, hand[0], hand[1], w * .55, col)
        K.circle(im, foot[0], foot[1], w * .55, col)


def watch_screen(t, sid='6C', rec=None):
    s = K.shot(sid); t_buzz = s['start'] + .04
    wake = K.ease_out(K.lin(t, t_buzz, t_buzz + .22))
    im = Image.new('RGBA', (WW, WH), (0, 0, 0, 255))
    lay = Image.new('RGBA', (WW, WH), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    # top row: a red heart, the time
    hx, hy = 110, 120
    K.circle(lay, hx - 17, hy - 6, 22, K.RED + (255,)); K.circle(lay, hx + 17, hy - 6, 22, K.RED + (255,)); K.poly(lay, [(hx - 38, hy + 2), (hx + 38, hy + 2), (hx, hy + 44)], K.RED + (255,))
    d.text((WW - 90, 118), '3:59', font=K.font('semi', 64), fill=K.W(), anchor='rm')
    # the figure stands up as the face wakes
    p = K.ease_io(K.lin(t, t_buzz + .10, t_buzz + .55))
    K.ring(lay, WW / 2, 420, 190, 26, (30, 60, 58, 255)); K.ring(lay, WW / 2, 420, 190, 26, TEAL + (255,), -90, -90 + 360 * .04)   # 0 of 12 hours
    stand_figure(lay, WW / 2 - 26 * (1 - p), 424, .72, p, TEAL + (255,))
    f = K.font('black', 132)
    d.text((WW / 2, 760), 'TIME TO', font=f, fill=K.W(), anchor='mm'); d.text((WW / 2, 900), 'STAND!', font=f, fill=K.W(), anchor='mm')
    d.text((WW / 2, 1050), "It's 3:59 AM.", font=K.font('med', 56), fill=(150, 154, 166, 255), anchor='mm')
    if rec is not None:
        for yy, tx in ((760, 'TIME TO'), (900, 'STAND!')):
            rec.add(tx, d.textbbox((WW / 2, yy), tx, font=f, anchor='mm'), (40, 680, WW - 40, 980), 'headline')
        rec.add("It's 3:59 AM.", d.textbbox((WW / 2, 1050), "It's 3:59 AM.", font=K.font('med', 56), anchor='mm'), (40, 1000, WW - 40, 1110), 'sub')
    # before it wakes: the always-on face, a dim clock (never a blank screen)
    if wake < 1:
        ao = Image.new('RGBA', (WW, WH), (0, 0, 0, 0)); ImageDraw.Draw(ao).text((WW / 2, WH / 2), '3:59', font=K.font('light', 300), fill=(120, 122, 130, int(255 * (1 - wake))), anchor='mm'); im.alpha_composite(ao)
    lay.putalpha(lay.getchannel('A').point(lambda v: int(v * wake)))
    im.alpha_composite(lay)
    return K.clamp_white(im)


def watch_body(screen):
    """our own watch: a rounded graphite case, a crown, the screen inset, a dark band going out of frame"""
    cw, ch = WW + 110, WH + 110; R = 230
    out = Image.new('RGBA', (cw + 60, ch + 900), (0, 0, 0, 0)); ox, oy = 0, 450
    band = Image.new('RGBA', out.size, (0, 0, 0, 0)); K.rrect(band, (150, 0, cw - 150, out.height), 80, (34, 36, 42, 255))
    for yy in range(0, out.height, 26):                                     # the band's weave, very fine
        ImageDraw.Draw(band).line([(150, yy), (cw - 150, yy)], fill=(40, 42, 50, 255), width=8)
    m = Image.new('L', out.size, 0); ImageDraw.Draw(m).rounded_rectangle((150, 0, cw - 150, out.height), radius=80, fill=255); band.putalpha(Image.fromarray(np.minimum(np.asarray(band.getchannel('A')), np.asarray(m))))
    out.alpha_composite(band)
    K.rrect(out, (cw - 20, oy + 330, cw + 40, oy + 520), 24, (92, 94, 102, 255))   # the crown
    K.rrect(out, (ox, oy, ox + cw, oy + ch), R, (88, 90, 98, 255)); K.rrect(out, (ox + 8, oy + 8, ox + cw - 8, oy + ch - 8), R - 8, (16, 17, 20, 255))
    sc = screen.convert('RGBA'); sc.putalpha(K.rrect_mask(WW, WH, 170)); out.alpha_composite(sc, (ox + 55, oy + 55))
    sh = Image.new('L', out.size, 0); ImageDraw.Draw(sh).polygon([(ox + 60, oy + 40), (ox + cw * .55, oy + 40), (ox + 60, oy + ch * .6)], fill=14)
    sheen = Image.new('RGBA', out.size, (255, 255, 255, 0)); sheen.putalpha(sh.filter(ImageFilter.GaussianBlur(50))); out.alpha_composite(sheen)
    return out


def watch_insert_16x9(screen, t, sid='6C'):
    s = K.shot(sid); t_buzz = s['start'] + .04
    body = watch_body(screen); sc = 1.0                                  # the case fills the frame's height: only the face is in shot
    bz = 0.0
    if t_buzz <= t <= t_buzz + .45:                                     # the buzz: a fast, small, decaying shake
        bz = math.sin((t - t_buzz) * 2 * math.pi * 24) * 9 * (1 - (t - t_buzz) / .45)
    p = K.lin(t, s['start'], s['end']); scl = sc * (1 + .03 * K.ease_io(p))
    b = body.resize((int(body.width * scl), int(body.height * scl)), Image.LANCZOS)
    out = P.room_plate().copy()
    # the screen's own light, soft
    glow = Image.new('RGBA', (2560, 1440), (0, 0, 0, 0)); ImageDraw.Draw(glow).ellipse((780, 100, 1780, 1340), fill=(110, 200, 200, int(26 * K.lin(t, t_buzz, t_buzz + .2)))); out.alpha_composite(glow.filter(ImageFilter.GaussianBlur(120)))
    x = 1280 - b.width / 2 + 30 + bz; y = 720 - (450 + (WH + 110) / 2) * scl
    K._paste_sub(out, b, x, y)
    return K.clamp_white(out).convert('RGB')


def watch_insert_9x16(screen, t, sid='6C'):
    """the face fills the width (key text inside 13%..70%), the buzz, a slow push"""
    s = K.shot(sid); t_buzz = s['start'] + .04
    body = watch_body(screen); p = K.lin(t, s['start'], s['end']); scl = 1000 / body.width * (1 + .03 * K.ease_io(p))
    bz = math.sin((t - t_buzz) * 2 * math.pi * 24) * 6 * (1 - (t - t_buzz) / .45) if t_buzz <= t <= t_buzz + .45 else 0.0
    b = body.resize((int(body.width * scl), int(body.height * scl)), Image.LANCZOS)
    out = P.room_plate().crop((1280 - 405, 0, 1280 + 405, 1440)).resize((1080, 1920), Image.LANCZOS)
    K._paste_sub(out, b, 540 - b.width / 2 + 24 + bz, 1920 * .42 - (450 + (WH + 110) / 2) * scl)
    return K.clamp_white(out).convert('RGB')


# ------------------------------------------------------------------ 5E: an empty editor, the caret blinks on the beat four times
LW, LH = 2560, 1600
ED_BG = (22, 24, 30); ED_PANEL = (28, 30, 38); ED_LINE = (44, 47, 58); ED_TXT = (200, 204, 214, 255); ED_DIM = (110, 116, 130, 255)


def editor(t, sid='5E', rec=None):
    s = K.shot(sid); bl = [K.onset(sid, f'cursor blink {i + 1}', s['start'] + i * .58) for i in range(4)]
    im = Image.new('RGBA', (LW, LH), ED_BG + (255,)); d = ImageDraw.Draw(im)
    # window bar, title centred
    d.rectangle((0, 0, LW, 96), fill=(18, 19, 24, 255))
    for i, c in enumerate(((236, 96, 90), (232, 186, 70), (98, 196, 110))): K.circle(im, 52 + i * 52, 48, 15, c + (255,))
    d.text((LW / 2, 48), 'do_it_myself.py', font=K.font('semi', 40), fill=ED_TXT, anchor='mm')
    # the explorer: one file
    d.rectangle((0, 96, 520, LH - 70), fill=ED_PANEL + (255,))
    d.text((48, 160), 'EXPLORER', font=K.font('semi', 34), fill=ED_DIM, anchor='lm')
    d.text((48, 240), '⌄ DO_IT_MYSELF', font=K.font('semi', 36), fill=ED_TXT, anchor='lm')
    K.rrect(im, (24, 280, 496, 362), 10, (48, 54, 72, 255)); d.text((96, 321), 'do_it_myself.py', font=K.font('reg', 38), fill=ED_TXT, anchor='lm')
    K.rrect(im, (60, 304, 82, 336), 4, (240, 196, 90, 255))
    # the tab
    d.rectangle((520, 96, LW, 176), fill=(18, 19, 24, 255)); d.rectangle((900, 96, 1440, 176), fill=ED_BG + (255,)); d.line([(900, 98), (1440, 98)], fill=(120, 170, 255, 255), width=4)
    d.text((940, 136), 'do_it_myself.py', font=K.font('med', 40), fill=ED_TXT, anchor='lm')
    d.text((1400, 136), '×', font=K.font('med', 44), fill=ED_DIM, anchor='mm')
    # line 1, empty, centred layout
    ly = 300
    d.rectangle((880, ly - 34, 1780, ly + 34), fill=(28, 31, 40, 255))
    d.text((960, ly), '1', font=K.font('mono', 40), fill=ED_DIM, anchor='rm')
    on = any(b <= t < b + .30 for b in bl) or t < bl[0] - .3
    if on:
        K.rrect(im, (1004, ly - 28, 1009, ly + 28), 2, (220, 224, 234, 255))
    # status bar + a quiet note in the corner
    d.rectangle((0, LH - 70, LW, LH), fill=(18, 19, 24, 255))
    d.text((40, LH - 35), 'Ln 1, Col 1   ·   Spaces: 4   ·   Python', font=K.font('reg', 36), fill=ED_DIM, anchor='lm')
    d.text((LW - 40, LH - 35), '3:40 AM', font=K.font('reg', 36), fill=ED_DIM, anchor='rm')
    tx0, ty0, tx1, ty1 = LW - 900, LH - 300, LW - 60, LH - 120
    K.shadow(im, (tx0, ty0, tx1, ty1), 20, 30, (0, 12), .5); K.rrect(im, (tx0, ty0, tx1, ty1), 20, (36, 39, 50, 255))
    d.text((tx0 + 48, ty0 + 62), 'Assistant is resting', font=K.font('semi', 40), fill=ED_TXT, anchor='lm')
    d.text((tx0 + 48, ty0 + 124), 'Back at 6:00. You have got this.', font=K.font('reg', 38), fill=ED_DIM, anchor='lm')
    if rec is not None:
        rec.add('Assistant is resting', d.textbbox((tx0 + 48, ty0 + 62), 'Assistant is resting', font=K.font('semi', 40), anchor='lm'), (tx0, ty0, tx1, ty1), 'toast')
        rec.add('Back at 6:00. You have got this.', d.textbbox((tx0 + 48, ty0 + 124), 'Back at 6:00. You have got this.', font=K.font('reg', 38), anchor='lm'), (tx0, ty0, tx1, ty1), 'toast')
        rec.add('do_it_myself.py', d.textbbox((940, 136), 'do_it_myself.py', font=K.font('med', 40), anchor='lm'), (900, 96, 1380, 176), 'tab')
        rec.add('do_it_myself.py', d.textbbox((96, 321), 'do_it_myself.py', font=K.font('reg', 38), anchor='lm'), (24, 280, 496, 362), 'file')
    return K.clamp_white(im)


# ------------------------------------------------------------------ 13E: morning, her first prompt (the tag)
PR_BG = (233, 229, 221)


def prompt(t, sid='13E', rec=None, opaque=True):
    """light, warm morning UI. 'Where were we?' (the song's last line) above the composer; she types 'Make the font bigger.'"""
    s = K.shot(sid); t_type = s['start'] + 2.4; per = .075; txt = 'Make the font bigger.'
    im = Image.new('RGBA', (LW, LH), (PR_BG + (255,)) if opaque else (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if opaque:
        from PIL import ImageFont
        fs = ImageFont.truetype(os.path.join(K.FD, 'InstrumentSerif-Regular.ttf'), 150)
        d.text((LW / 2, 600), 'Where were we?', font=fs, fill=(52, 46, 40, 255), anchor='mm')
        if rec is not None:
            rec.add('Where were we?', d.textbbox((LW / 2, 600), 'Where were we?', font=fs, anchor='mm'), (400, 480, LW - 400, 720), 'heading')
    bx0, by0, bx1, by1 = 560, 820, LW - 560, 1080
    K.shadow(im, (bx0, by0, bx1, by1), 44, 36, (0, 16), .18); K.rrect(im, (bx0, by0, bx1, by1), 44, (246, 244, 240, 255) if opaque else (246, 244, 240, 240))
    n = int(K.clamp((t - t_type) / per, 0, len(txt))); shown = txt[:n]
    f = K.font('reg', 64)
    if shown:
        d.text((bx0 + 70, by0 + 100), shown, font=f, fill=(36, 34, 32, 255), anchor='lm')
    elif t < t_type:
        d.text((bx0 + 70, by0 + 100), 'Ask anything', font=f, fill=(150, 144, 136, 255), anchor='lm')
    cx = bx0 + 70 + (K.text_w(shown, f) if shown else 0) + 6
    if (n < len(txt) and t >= t_type) or ((t * 1.9) % 1 < .55):
        d.rectangle((cx, by0 + 66, cx + 4, by0 + 134), fill=(36, 34, 32, 255))
    # the send button lights when there is something to send
    ready = K.fade(t, t_type + per * len(txt), .15)
    K.circle(im, bx1 - 90, by1 - 80, 46, tuple(int(a + (b - a) * ready) for a, b in zip((200, 196, 188), (52, 46, 40))) + (255,))
    d.line([(bx1 - 90, by1 - 100), (bx1 - 90, by1 - 60)], fill=(246, 244, 240, 255), width=8); d.line([(bx1 - 108, by1 - 84), (bx1 - 90, by1 - 102), (bx1 - 72, by1 - 84)], fill=(246, 244, 240, 255), width=8, joint='curve')
    if rec is not None and n == len(txt):
        rec.add(txt, d.textbbox((bx0 + 70, by0 + 100), txt, font=f, anchor='lm'), (bx0, by0, bx1, by1), 'composer')
    return K.clamp_white(im)
