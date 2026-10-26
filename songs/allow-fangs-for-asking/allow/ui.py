"""Phone screens, drawn at native resolution and mapped onto the blank screens in the plates.

Restrained, real-looking system UI (dark mode): the permission prompts that climb through the song, the share sheet
in the bridge, the lock screen at 3 a.m. Returned as linear RGB + alpha at a portrait screen size (w x h)."""
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter
from .fx import F32, to_lin, font

UI = 'Inter-Medium.otf'; UIB = 'Inter-SemiBold.otf'; UIR = 'Inter-Regular.otf'

PROMPTS = {
    'notifications': ('“Midnight” Would Like to Send You Notifications',
                      'Notifications may include alerts, sounds and icon badges.'),
    'location': ('Allow “Midnight” to use your location?', 'It knows where you sleep.'),
    'camera': ('“Midnight” Would Like to Access the Camera', 'To see you when you check.'),
    'microphone': ('“Midnight” Would Like to Access the Microphone', 'To hear you say yes.'),
    'contacts': ('“Midnight” Would Like to Access Your Contacts', 'So you can share him with the people you love.'),
    'sis': ('“Sis” Would Like to Send You Notifications', 'You have to see this.'),
}


def _wrap(d, text, f, maxw):
    words = text.split(); lines = []; cur = ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if d.textlength(t, font=f) <= maxw: cur = t
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines


def screen(kind='prompt', key='notifications', w=1170, h=2532, press=0.0, allow_scale=1.0, wallpaper=None, time_str='12:00'):
    """RGBA uint8 screen. press 0..1 highlights Allow (as if tapped); allow_scale grows Allow (the dark pattern)."""
    # a luminous deep-blue wallpaper: at night the screen is the brightest thing in the room
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    r = np.sqrt(((xx - w * 0.35) / w) ** 2 + ((yy - h * 0.3) / h) ** 2)
    base = np.clip(1.0 - r * 0.9, 0, 1)[..., None]
    wp = (np.array([18, 52, 150], np.float32) * (0.45 + 0.75 * base) + np.array([60, 120, 255], np.float32) * base ** 3 * 0.5)
    im = Image.fromarray(np.dstack([np.clip(wp, 0, 255).astype(np.uint8), np.full((h, w), 255, np.uint8)]), 'RGBA')
    if wallpaper is not None:
        wp = Image.fromarray(wallpaper).resize((w, h)).filter(ImageFilter.GaussianBlur(w * 0.03))
        im.paste(wp, (0, 0)); im = Image.blend(im, Image.new('RGBA', (w, h), (0, 0, 0, 255)), 0.45)
    d = ImageDraw.Draw(im)
    s = min(w, h) / 1170
    # status bar
    d.text((90 * s, 52 * s), time_str, font=font(UIB, 50 * s), fill=(235, 238, 245, 255))
    if kind == 'lock':
        d.text((w / 2, 300 * s), 'Saturday, October 31', font=font(UI, 56 * s), fill=(230, 232, 240, 230), anchor='mm')
        d.text((w / 2, 520 * s), time_str, font=font('InterDisplay-Light.otf' if False else UI, 260 * s), fill=(240, 242, 250, 245), anchor='mm')
        # one notification card
        y0 = 1500 * s
        d.rounded_rectangle((60 * s, y0, w - 60 * s, y0 + 230 * s), 42 * s, fill=(40, 44, 54, 210))
        d.text((110 * s, y0 + 55 * s), 'MIDNIGHT', font=font(UIB, 36 * s), fill=(200, 205, 220, 255))
        d.text((w - 110 * s, y0 + 55 * s), 'now', font=font(UIR, 36 * s), fill=(160, 165, 180, 255), anchor='ra')
        d.text((110 * s, y0 + 120 * s), 'Still up? So am I.', font=font(UI, 46 * s), fill=(235, 238, 245, 255))
        return np.asarray(im)
    if kind == 'share':
        y0 = h * 0.52
        d.rounded_rectangle((0, y0, w, h + 60 * s), 56 * s, fill=(28, 30, 36, 255))
        d.text((w / 2, y0 + 90 * s), 'You have to see this', font=font(UIB, 50 * s), fill=(235, 238, 245, 255), anchor='mm')
        for i, (nm, hi) in enumerate([('Sister', True), ('Mom', False), ('Dani', False), ('Work', False)]):
            cx = 190 * s + i * 265 * s; cy = y0 + 330 * s; r = 95 * s
            d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(70, 120, 255, 255) if hi else (64, 68, 80, 255))
            d.text((cx, cy), nm[0], font=font(UIB, 80 * s), fill=(255, 255, 255, 255), anchor='mm')
            d.text((cx, cy + 150 * s), nm, font=font(UI, 40 * s), fill=(235, 238, 245, 255) if hi else (160, 165, 180, 255), anchor='mm')
        bx0, by0 = 70 * s, y0 + 620 * s
        d.rounded_rectangle((bx0, by0, w - bx0, by0 + 150 * s), 40 * s, fill=(10 + int(60 * press), 132 + int(40 * press), 255, 255))
        d.text((w / 2, by0 + 75 * s), 'Send to Sister', font=font(UIB, 52 * s), fill=(255, 255, 255, 255), anchor='mm')
        return np.asarray(im)
    # permission prompt (centred alert)
    title, body = PROMPTS[key]
    aw = 820 * s; ax0 = (w - aw) / 2
    f_t = font(UIB, 50 * s); f_b = font(UIR, 40 * s)
    tl = _wrap(d, title, f_t, aw - 100 * s); bl = _wrap(d, body, f_b, aw - 100 * s)
    th = len(tl) * 64 * s + 30 * s + len(bl) * 54 * s
    ah = th + 120 * s + 150 * s
    ay0 = (h - ah) / 2
    ov = Image.new('RGBA', (w, h), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    od.rounded_rectangle((ax0, ay0, ax0 + aw, ay0 + ah), 52 * s, fill=(38, 40, 48, 236))
    im = Image.alpha_composite(im, ov); d = ImageDraw.Draw(im)
    y = ay0 + 60 * s
    for ln in tl: d.text((w / 2, y), ln, font=f_t, fill=(240, 242, 248, 255), anchor='ma'); y += 64 * s
    y += 30 * s
    for ln in bl: d.text((w / 2, y), ln, font=f_b, fill=(190, 195, 208, 255), anchor='ma'); y += 54 * s
    by = ay0 + ah - 150 * s
    d.line((ax0, by, ax0 + aw, by), fill=(70, 74, 86, 255), width=max(1, int(2 * s)))
    # Don't Allow shrinks and greys as Allow grows: the dark pattern, in miniature
    split = ax0 + aw * (0.5 - 0.18 * (allow_scale - 1))
    d.line((split, by, split, ay0 + ah), fill=(70, 74, 86, 255), width=max(1, int(2 * s)))
    da = int(255 * max(0.25, 1.4 - 0.9 * allow_scale))
    d.text(((ax0 + split) / 2, by + 75 * s), "Don’t Allow", font=font(UIR, 46 * s / max(1.0, allow_scale ** 0.6)),
           fill=(120, 150, 255, da), anchor='mm')
    ab = int(60 * press)
    if press > 0:
        d.rounded_rectangle((split, by, ax0 + aw, ay0 + ah), 0, fill=(90 + ab, 120 + ab, 160 + ab, int(90 * press)))
    d.text(((split + ax0 + aw) / 2, by + 75 * s), 'Allow', font=font(UIB, 50 * s * allow_scale ** 0.5), fill=(140, 175, 255, 255), anchor='mm')
    return np.asarray(im)


def map_to(dst, scr_rgba, quad, glow=1.0, exposure=1.0, mask=None):
    """Perspective-map a screen (RGBA uint8) onto quad [(x,y) tl, tr, br, bl] of a linear frame, as emitted light."""
    h, w = scr_rgba.shape[:2]
    H, W = dst.shape[:2]
    M = cv2.getPerspectiveTransform(np.float32([[0, 0], [w, 0], [w, h], [0, h]]), np.float32(quad))
    rgb = to_lin(scr_rgba[..., :3]) * exposure
    warped = cv2.warpPerspective(rgb, M, (W, H), flags=cv2.INTER_AREA, borderMode=cv2.BORDER_CONSTANT)
    a = cv2.warpPerspective(np.ones((h, w), F32), M, (W, H), flags=cv2.INTER_LINEAR)
    if mask is not None:
        a = a * mask; warped = warped * mask[..., None]
    return dst * (1 - a[..., None]) + warped * glow
