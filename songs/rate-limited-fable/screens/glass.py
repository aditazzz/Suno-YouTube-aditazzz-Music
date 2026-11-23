"""The door glass is her screen: its states as layers (rl_screens).

  messages   2G  'One last thing.' -> Delivered -> Read 2:06 AM
             5H  three messages, one per beat of the roll -> Read 3:59 AM (lands on the approved close frame at 1:35.1)
  typing     8E  Read 4:37 AM, then his three typing dots; on 'nothing' the dots go out
  read-first 12G an empty draft bubble with a caret; 'Read.' appears before she sends anything
  sleep      11C the glass dims like a screen going to sleep (two steps, like a laptop)
  ripple     2C  three knocks, three soft rings, like taps on a touch screen that no longer answers

Close shots (2G, 5H, 12G) are screen-space overlays at 2560x1440 in the approved layout (build/pitch2/her_side/comp_close.py,
scaled 4/3), plus a 1080x1920 version placed for the 9:16 safe zone. The wide shot (8E), the knocks and the sleep are in the glass's
own UV space (blns.door: 1.36 m x 1.62 m -> 1360 x 1620 px, seen from her side).
"""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit as K

RECEIPT = (38, 34, 30)                # the approved receipt colour (dark on the lit lobby)


class Bubble:
    """a sent bubble (blue pill, white text) or the incoming typing bubble; built once, then placed with a spring"""

    def __init__(self, text, fsize, padx, pady, th, radius, color=K.BLUE, tcolor=None, draft=False):
        self.text = text; f = K.font('med', fsize); self.f = f
        tw = K.text_w(text, f) if text else 0
        self.w = int(round(tw + 2 * padx)) if text else int(round(radius * 2 + fsize * 2.6)); self.h = int(round(th + 2 * pady))
        im = Image.new('RGBA', (self.w + 8, self.h + 8), (0, 0, 0, 0))
        if draft:
            # an empty draft: a faint blue pill with a hairline edge (she has started a message)
            # the compose field: a pale pill with a blue hairline, nothing typed yet
            K.rrect(im, (4, 4, 4 + self.w, 4 + self.h), radius, color + (255,))
            K.rrect(im, (7, 7, 1 + self.w, 1 + self.h), radius - 3, (232, 236, 244, 255))
        else:
            K.rrect(im, (4, 4, 4 + self.w, 4 + self.h), radius, color + (240,))
            # the faintest top-light so the pill reads as a lit object, not a flat sticker
            g = Image.new('L', (self.w, self.h), 0); ga = np.linspace(46, 0, self.h)[:, None] * np.ones((1, self.w)); g = Image.fromarray(ga.astype(np.uint8))
            m = K.rrect_mask(self.w, self.h, radius); g = Image.fromarray((np.asarray(g, dtype=np.float32) * np.asarray(m, dtype=np.float32) / 255).astype(np.uint8))
            hi = Image.new('RGBA', (self.w, self.h), (255, 255, 255, 0)); hi.putalpha(g); im.alpha_composite(hi, (4, 4))
        self.tbox = None
        if text:
            d = ImageDraw.Draw(im); tcolor = tcolor or K.W()
            d.text((4 + padx, 4 + pady + th / 2), text, font=f, fill=tcolor, anchor='lm')
            self.tbox = d.textbbox((4 + padx, 4 + pady + th / 2), text, font=f, anchor='lm')
        self.im = K.clamp_white(im)


def receipt_sprite(word, time_txt, fs):
    fb = K.font('bold', fs); fr = K.font('med', fs)
    w1 = K.text_w(word, fb); w2 = K.text_w(time_txt, fr) if time_txt else 0
    im = Image.new('RGBA', (int(w1 + w2 + 8), int(fs * 1.5)), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.text((2, fs * .2), word, font=fb, fill=RECEIPT + (255,), anchor='la')
    if time_txt:
        d.text((2 + w1, fs * .2), time_txt, font=fr, fill=RECEIPT + (235,), anchor='la')
    bb = d.textbbox((2, fs * .2), word + (time_txt or ''), font=fb, anchor='la')
    return im, (bb[0], bb[1], bb[0] + w1 + w2, bb[3])


def typing_sprite(fs, t, color=(229, 229, 234), alpha=255):
    """his incoming bubble with three dots bouncing in sequence"""
    h = int(fs * 1.9); w = int(fs * 3.4); im = Image.new('RGBA', (w + 8, h + 8), (0, 0, 0, 0))
    K.rrect(im, (4, 4, 4 + w, 4 + h), h / 2, color + (alpha,))
    r = fs * .18
    for i in range(3):
        ph = (t * 2.2 - i * .18) % 1.0; lift = math.sin(min(ph / .5, 1) * math.pi) if ph < .5 else 0
        cx = 4 + w / 2 + (i - 1) * fs * .78; cy = 4 + h / 2 - lift * fs * .22
        K.circle(im, cx, cy, r, (120, 120, 128, 255), alpha=.55 + .45 * lift)
    return im


# ------------------------------------------------------------------ the close-shot layout (approved, scaled to 1440 and to 9:16)
LAYOUT = {
    '16x9': dict(size=(2560, 1440), R=573, y=55, padx=32, pady=14.7, gap=10.7, th=64, radius=40, fs=48, rfs=40),
    '9x16': dict(size=(1080, 1920), R=640, y=290, padx=36, pady=20, gap=13, th=74, radius=50, fs=58, rfs=44),
}


def messages_frame(t, fmt, msgs, times, receipt_t, read_t, read_time, delivered=True, draft=False, rec=None, read_rise=8, read_fade=.1):
    L = LAYOUT[fmt]; img = Image.new('RGBA', L['size'], (0, 0, 0, 0)); y = L['y']; R = L['R']
    last_bottom = y
    for i, (m, tm) in enumerate(zip(msgs, times)):
        b = Bubble(m, L['fs'], L['padx'], L['pady'], L['th'], L['radius'], draft=draft)
        s = K.spring(t, tm, freq=3.4, damp=.45); a = K.fade(t, tm, .08)
        if s > 0:
            sc = .72 + .28 * s; rise = (1 - min(s, 1)) * 14
            # pivot at the bubble's lower right (where a sent bubble grows from)
            K.sprite_scaled(img, b.im, (R + 4, y + b.h + 4 + rise), ((b.w + 4) / (b.w + 8), (b.h + 4) / (b.h + 8)), sc, a)
            if draft and t >= tm:
                # the caret blinks inside the empty draft (on for half of each 0.53 s)
                if ((t - tm) / .53) % 1 < .55:
                    cx = R - b.w + L['padx'] * 1.05; img_d = ImageDraw.Draw(img)
                    img_d.rounded_rectangle((cx, y + L['pady'] + 8, cx + 5, y + b.h - L['pady'] - 8), radius=2, fill=K.BLUE + (255,))
            if rec is not None and b.tbox and t >= tm + .6:
                ox, oy = R + 4 - (b.w + 4), y + b.h + 4 - (b.h + 4)
                rec.add(m, (b.tbox[0] + ox, b.tbox[1] + oy, b.tbox[2] + ox, b.tbox[3] + oy), (R - b.w, y, R, y + b.h), 'bubble')
        last_bottom = y + b.h; y = y + b.h + L['gap']
    ry = last_bottom + L['gap'] + 2
    # Delivered, then the receipt
    if delivered and receipt_t is not None and t >= receipt_t:
        a = K.fade(t, receipt_t, .12) * (1 - K.fade(t, read_t - .06, .1))
        if a > 0:
            spr, bb = receipt_sprite('Delivered', '', L['rfs']); K.sprite_scaled(img, spr, (R - 4, ry - L['rfs'] * .075), (1 - 4 / spr.width, 0), 1, a)
    if read_t is not None and t >= read_t:
        a = K.fade(t, read_t, read_fade); s = K.spring(t, read_t, 3.6, .5)
        spr, bb = receipt_sprite('Read', read_time, L['rfs']) if read_time is not None else receipt_sprite('Read.', '', L['rfs'])
        K.sprite_scaled(img, spr, (R - 4, ry - L['rfs'] * .075 + (1 - min(s, 1)) * read_rise), (1 - 4 / spr.width, 0), 1, a)
        if rec is not None and t >= read_t + .4:
            x0 = R - 4 - (spr.width - 4); y0r = ry - L['rfs'] * .075; rec.add('Read' + (read_time or '.'), (x0 + bb[0], y0r + bb[1], x0 + bb[2], y0r + bb[3]), None, 'receipt')
    return K.clamp_white(img)


def bezel(fmt):
    """the approved close frame's screen edge: a slim bezel, rounded inner corners, a camera dot, the faintest sheen"""
    Wd, Ht = LAYOUT[fmt]['size']; s = Ht / 1080 if fmt == '16x9' else Wd / 1080 * 1.0
    k = 1440 / 1080 if fmt == '16x9' else 1.0
    out = Image.new('RGBA', (Wd, Ht), (0, 0, 0, 0))
    sh = Image.new('L', (Wd, Ht), 0); ImageDraw.Draw(sh).polygon([(Wd * .50, 0), (Wd * .66, 0), (Wd * .40, Ht), (Wd * .24, Ht)], fill=14)
    sheen = Image.new('RGBA', (Wd, Ht), (255, 255, 255, 0)); sheen.putalpha(sh.filter(ImageFilter.GaussianBlur(90 * k))); out.alpha_composite(sheen)
    bz = Image.new('RGBA', (Wd, Ht), (12, 13, 16, 255)); m = Image.new('L', (Wd * 4, Ht * 4), 255)
    ImageDraw.Draw(m).rounded_rectangle((16 * k * 4, 16 * k * 4, (Wd - 16 * k) * 4, (Ht - 16 * k) * 4), radius=34 * k * 4, fill=0)
    bz.putalpha(m.resize((Wd, Ht), Image.LANCZOS)); out.alpha_composite(bz)
    cx = Wd / 2; K.circle(out, cx, 9 * k, 5 * k, (38, 42, 50, 255)); K.circle(out, cx, 9 * k, 2 * k, (70, 90, 120, 255))
    return out


# ------------------------------------------------------------------ the glass in its own UV space (1360 x 1620, her side)
GW, GH = 1360, 1620


def typing_glass(t, sid='8E', rec=None):
    """8E on the glass texture: her last bubble, Read 4:37 AM, then his typing dots; on 'nothing' they go out. Large type: the shot is wide."""
    s = K.shot(sid); bts = K.beats_in(sid)
    img = Image.new('RGBA', (GW, GH), (0, 0, 0, 0))
    fs = 92; R = GW - 150; y = 360
    b = Bubble('You up?', fs, 58, 26, 112, 72)
    img.alpha_composite(b.im, (int(R - b.w - 4), int(y - 4)))
    if rec is not None:
        rec.add(b.text, (b.tbox[0] + R - b.w - 4, b.tbox[1] + y - 4, b.tbox[2] + R - b.w - 4, b.tbox[3] + y - 4), (R - b.w, y, R, y + b.h), 'bubble')
    ry = y + b.h + 22
    t_read = s['start'] + .12
    if t >= t_read:
        spr, bb = receipt_sprite('Read', ' 4:37 AM', 70); a = K.fade(t, t_read, .12)
        K.sprite_scaled(img, spr, (R - 6, ry), (1 - 4 / spr.width, 0), 1, a)
        if rec is not None:
            x0 = R - 6 - (spr.width - 4); rec.add('Read 4:37 AM', (x0 + bb[0], ry + bb[1], x0 + bb[2], ry + bb[3]), None, 'receipt')
    # his dots: appear on beat 3 of the first bar, go out on 'nothing'
    t_dots = bts[2] if len(bts) > 2 else s['start'] + 1.2
    t_off = K.onset(sid, 'nothing', bts[6] if len(bts) > 6 else s['end'] - 1.0)
    if t >= t_dots:
        on = K.spring(t, t_dots, 3.0, .5); off = K.ease_io(K.lin(t, t_off, t_off + .28))
        sc = (.6 + .4 * on) * (1 - .35 * off); a = K.fade(t, t_dots, .12) * (1 - off)
        spr = typing_sprite(100, t - t_dots)
        K.sprite_scaled(img, spr, (150, ry + 160 + spr.height), (0, 1), sc, a)
    return K.clamp_white(img)


def sleep_curve(t, sid='11C'):
    """glass darkness 0..1: the dimmer turns, the glass drops to 55% (like a laptop dimming), holds, then sleeps"""
    s = K.shot(sid); t0 = s['start'] + .30; t1 = t0 + .85
    d1 = K.ease_out(K.lin(t, t0, t0 + .35)) * .45
    d2 = K.ease_io(K.lin(t, t1, t1 + .30)) * .47
    return d1 + d2


def sleep_glass(t, sid='11C'):
    a = sleep_curve(t, sid)
    return Image.new('RGBA', (GW, GH), (6, 7, 10, int(255 * a)))


def knock_times(sid='2C'):
    bts = K.beats_in(sid)
    fb = bts[:3] if len(bts) >= 3 else [K.shot(sid)['start'] + i * .58 for i in range(3)]
    return [K.onset(sid, f'knock {i + 1}', fb[i]) for i in range(3)]


KNOCK_UV = [(0.60, 0.37), (0.57, 0.34), (0.62, 0.39)]      # her knuckle, seen from her side (mirror u for the lobby side)


def ripple_maps(t, sid='2C'):
    """-> (height 16-bit 'I;16' image, 0.5 = flat; ring highlight RGBA) in glass UV, her side"""
    yy, xx = np.mgrid[0:GH, 0:GW].astype(np.float32)
    h = np.zeros((GH, GW), np.float32); hl = np.zeros((GH, GW), np.float32)
    for tk, (u, v) in zip(knock_times(sid), KNOCK_UV):
        age = t - tk
        if age <= 0 or age > 1.6:
            continue
        r = np.hypot(xx - u * GW, yy - v * GH); front = 40 + 620 * (1 - math.exp(-age * 2.6)); width = 26 + 60 * age
        env = np.exp(-((r - front) / width) ** 2) * math.exp(-age * 2.4)
        h += env * np.sin((r - front) / width * 2.6) * .5
        hl += env * (.5 + .5 * np.cos((r - front) / width * 2.6))
        # the knuckle's own small dimple for the first frames
        h -= np.exp(-(r / 30) ** 2) * math.exp(-age * 14) * .6
    hm = Image.fromarray(np.clip((h * .5 + .5) * 65535, 0, 65535).astype(np.uint16))
    a = np.clip(hl * .30, 0, .30)
    rgba = np.zeros((GH, GW, 4), np.uint8); rgba[..., :3] = K.WHITE_MAX; rgba[..., 3] = (a * 255).astype(np.uint8)
    return hm, Image.fromarray(rgba, 'RGBA')
