"""Step 5 — thumbnails in the series style: wide-tracked mono title over a clean hero frame.

usage: python -m studio.thumbs songs/<slug> [--times 120 228]   (several times -> several options for Test & Compare)
Writes  "<Title> - YouTube thumbnail.jpg", "(no text)", extra "option N" files, and "Short cover (9x16).jpg".
"""
import os, sys, argparse
import numpy as np
from PIL import Image
from .config import load_song
from . import core
from .render import load_scene

def title_card(base, title, caption=None, accent=None, label=None):
    """Series style (see docs/lessons.md): heavy glowing title in the lower half, tiny top-left series label,
    the hero frame's own centerpiece above it, one accent color."""
    img = base.astype(np.float32) / 255; H, W = img.shape[:2]
    accent = core.hexc(accent) if isinstance(accent, str) else (accent if accent is not None else core.hexc('ff3d9a'))
    yy = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    img *= 1 - 0.78 * np.clip((yy - 0.52) / 0.48, 0, 1) ** 1.2          # dark floor for the title
    img *= 1 - 0.45 * np.clip((0.10 - yy) / 0.10, 0, 1)                  # and a little at the top for the label
    words = title.upper().split()
    lines = [" ".join(words)]
    if len(lines[0]) > 11 and len(words) > 1:                            # two stacked lines read bigger on a phone
        best = min(range(1, len(words)), key=lambda k: abs(len(" ".join(words[:k])) - len(" ".join(words[k:]))))
        lines = [" ".join(words[:best]), " ".join(words[best:])]
    size = 230 if len(lines) == 1 else 190
    while size > 70 and max(core.text_w(l, core.F_DISP, size) for l in lines) > W * 0.90: size -= 6
    lh = size * 0.98; y0 = H * (0.80 if len(lines) == 1 else 0.70)
    for i, l in enumerate(lines):
        sp = core.sprite(l, core.F_DISP, size, 22)
        y = y0 + i * lh
        core.shadow(img, sp, W / 2 - sp[0].shape[1] / 2 + sp[2] + 6, y - sp[0].shape[0] / 2 + sp[2] + 10, 1.0)
        col = core.WHITE if i == 0 or len(lines) == 1 else accent * 0.5 + core.WHITE * 0.5
        core.blit(img, sp, W / 2, y, col, 1.0, 1.1, glow_color=accent, anchor='c')
    lab = label or "CLAUDE OPUS 5.5  ·  ADITAZZZ"
    core.blit(img, core.sprite(lab, core.F_MONOB, 30, track=4), 40, 30, core.WHITE * 0.9, 1.0)
    if caption:
        fs = 40; w = int(core.text_w(caption, core.F_DISPB, fs) + 70); h = 76; x = 40; y = 80
        core._pill(img, x, y, w, h, accent, 0.95)
        core.txt(img, caption, x + 35, y + 14, fs, core.hexc('0d0b1a'), 1.0, core.F_DISPB)
    return (np.clip(img, 0, 1) * 255).astype(np.uint8)

F_COND = os.path.join(core.FONTS, "Anton-Regular.ttf")

def claude_card(base, hook="ANIMATED THIS", accent=None, top="CLAUDE", side="left", shift=0.0, scale=1.0, shift_y=0.0):
    """The hook cover: huge condensed 'CLAUDE / ANIMATED THIS' top-left, white + one loud accent, thick black outline.
    Works for 16:9 thumbnails and 9:16 Short covers (readable at phone-feed size)."""
    from PIL import ImageDraw, ImageFont, ImageFilter
    if shift or shift_y or scale != 1.0:   # slide/zoom the hero frame so its centerpiece sits beside the text, not under it
        import cv2
        Hh, Ww = base.shape[:2]
        M = np.float32([[scale, 0, Ww * shift + Ww * (1 - scale) / 2], [0, scale, Hh * shift_y + Hh * (1 - scale) / 2]])
        # the uncovered edge gets a soft, dark blur of the frame (a mirrored copy shows backwards text and chips)
        sh = cv2.warpAffine(base.astype(np.float32), M, (Ww, Hh), borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        msk = cv2.warpAffine(np.ones((Hh, Ww), np.float32), M, (Ww, Hh), borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        msk = cv2.GaussianBlur(msk, (0, 0), Ww * 0.015)[..., None]
        fill = cv2.GaussianBlur(base.astype(np.float32), (0, 0), Ww * 0.04) * 0.5
        base = np.clip(sh * msk + fill * (1 - msk), 0, 255).astype(np.uint8)
    im = Image.fromarray(base).convert("RGB"); W, H = im.size; vert = H > W
    acc = accent if isinstance(accent, str) else "#d7ff3a"
    acc = acc if acc.startswith("#") else "#" + acc
    # darken behind the text a little so it pops on any frame
    a = np.asarray(im).astype(np.float32) / 255
    yy = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]; xx = np.linspace(0, 1, W, dtype=np.float32)[None, :, None]
    m = np.clip(1 - yy / (0.42 if vert else 0.62), 0, 1) * (1.0 if vert else np.clip(1.25 - (xx if side == 'left' else 1 - xx), 0, 1))
    a *= 1 - 0.45 * m
    im = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))
    lines = [(top, "#ffffff"), (hook, acc)]
    maxw = W * (0.90 if vert else 0.62); x0 = int(W * (0.05 if vert else 0.035)); y = int(H * (0.05 if vert else 0.06))
    size = int(H * (0.11 if vert else 0.19))
    def fnt(sz): return ImageFont.truetype(F_COND, sz)
    if side == "right" and not vert: maxw = W * 0.44; size = int(H * 0.26)
    while max(fnt(size).getbbox(t)[2] for t, _ in lines) > maxw: size -= 4
    f = fnt(size); sw = max(6, size // 13)
    if side == "right" and not vert:
        x0 = int(W * 0.5); y = int(H / 2 - size * 1.04 - size * 0.12)
    sh = Image.new("L", im.size, 0); ds = ImageDraw.Draw(sh); yy_ = y
    for t, _ in lines:
        ds.text((x0 + sw, yy_ + sw * 1.6), t, font=f, fill=200, stroke_width=sw, stroke_fill=200); yy_ += int(size * 1.04)
    sh = sh.filter(ImageFilter.GaussianBlur(sw * 1.2))
    im = Image.composite(Image.new("RGB", im.size, (0, 0, 0)), im, sh)
    d = ImageDraw.Draw(im)
    for t, c in lines:
        d.text((x0, y), t, font=f, fill=c, stroke_width=sw, stroke_fill="#0b0b0f"); y += int(size * 1.04)
    return np.asarray(im)

def made_in_card(base, side="right", shift=0.0, scale=1.0, small="MADE ENTIRELY IN", big="CLAUDE CODE"):
    """Second hook style: small wide-tracked line over a huge one, cream with a soft shadow, bottom corner."""
    from PIL import ImageDraw, ImageFont, ImageFilter
    import cv2
    if shift or scale != 1.0:
        Hh, Ww = base.shape[:2]
        M = np.float32([[scale, 0, Ww * shift + Ww * (1 - scale) / 2], [0, scale, Hh * (1 - scale) / 2]])
        base = cv2.warpAffine(base, M, (Ww, Hh), borderMode=cv2.BORDER_REFLECT)
    im = Image.fromarray(base).convert("RGB"); W, H = im.size; vert = H > W
    a = np.asarray(im).astype(np.float32) / 255
    yy = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    if a.mean() < 0.55: a *= 1 - 0.5 * np.clip((yy - 0.45) / 0.55, 0, 1)   # only darken dark frames; light paper stays clean
    im = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))
    bw = W * (0.88 if vert else 0.50)
    fb = ImageFont.truetype(F_COND, 400); sb = 400
    while fb.getbbox(big)[2] > bw: sb -= 6; fb = ImageFont.truetype(F_COND, sb)
    ss = max(30, int(sb * 0.26)); fs = ImageFont.truetype(core.F_DISP, ss)
    def tracked_w(f, t, tr): return sum(f.getbbox(c)[2] for c in t) + tr * (len(t) - 1)
    tr = 0
    while tracked_w(fs, small, tr) < fb.getbbox(big)[2] * 0.98 and tr < ss * 0.5: tr += 1
    wbig = fb.getbbox(big)[2]
    x0 = int((W - wbig) / 2) if vert else (int(W * 0.965 - wbig) if side == "right" else int(W * 0.035))
    yb = int(H * (0.70 if vert else 0.86) - sb * 0.95); ys = int(yb - ss * 1.45)
    shd = Image.new("L", im.size, 0); ds = ImageDraw.Draw(shd)
    ds.text((x0 + 8, yb + 12), big, font=fb, fill=230 if np.asarray(im).mean() < 140 else 60)
    shd = shd.filter(ImageFilter.GaussianBlur(10)); im = Image.composite(Image.new("RGB", im.size, (0, 0, 0)), im, shd)
    d = ImageDraw.Draw(im)
    light = np.asarray(im).mean() > 140
    ink, fill = ("#1d1a1f", "#1d1a1f") if light else ("#2a2420", "#f4eee4")
    x = x0
    for c in small:
        if not light: d.text((x + 3, ys + 4), c, font=fs, fill="#000000")
        d.text((x, ys), c, font=fs, fill=fill); x += fs.getbbox(c)[2] + tr
    light = np.asarray(im).mean() > 140
    ink, fill = ("#1d1a1f", "#1d1a1f") if light else ("#2a2420", "#f4eee4")
    d.text((x0, yb), big, font=fb, fill=fill, stroke_width=max(3, sb // 40), stroke_fill=ink)
    return np.asarray(im)

def _shift(base, shift=0.0, shift_y=0.0, scale=1.0):
    """Slide/zoom the hero frame; the uncovered edge gets a soft dark blur of the frame."""
    if not (shift or shift_y or scale != 1.0): return base
    import cv2
    Hh, Ww = base.shape[:2]
    M = np.float32([[scale, 0, Ww * shift + Ww * (1 - scale) / 2], [0, scale, Hh * shift_y + Hh * (1 - scale) / 2]])
    sh = cv2.warpAffine(base.astype(np.float32), M, (Ww, Hh), borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    msk = cv2.warpAffine(np.ones((Hh, Ww), np.float32), M, (Ww, Hh), borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    msk = cv2.GaussianBlur(msk, (0, 0), Ww * 0.015)[..., None]
    fill = cv2.GaussianBlur(base.astype(np.float32), (0, 0), Ww * 0.04) * 0.5
    return np.clip(sh * msk + fill * (1 - msk), 0, 255).astype(np.uint8)

def context_card(base, lines, sub=None, accent=None, side="left", shift=0.0, shift_y=0.0, scale=1.0, badge="CLAUDE ANIMATED THIS", dark=0.62):
    """Thumbnail that says what the video is about: a 2-3 line hook (last line in the accent), one plain line saying
    what kind of song it is, and a small 'CLAUDE ANIMATED THIS' badge. Hero frame slid aside so it stays visible."""
    from PIL import ImageDraw, ImageFont, ImageFilter
    acc = accent if isinstance(accent, str) else "#ff3d9a"; acc = acc if acc.startswith("#") else "#" + acc
    base = _shift(base, shift if side == "left" else -abs(shift), shift_y, scale)
    H, W = base.shape[:2]
    a = base.astype(np.float32) / 255
    xx = np.linspace(0, 1, W, dtype=np.float32)[None, :, None]
    t = xx if side == "left" else 1 - xx
    a *= 1 - dark * np.clip((0.72 - t) / 0.72, 0, 1) ** 0.8          # dark behind the text column
    im = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    colw = W * 0.58
    lines = [l.upper() for l in lines]; size = int(H * 0.20)
    while size > 40 and max(ImageFont.truetype(F_COND, size).getbbox(l)[2] for l in lines) > colw: size -= 4
    f = ImageFont.truetype(F_COND, size); lh = int(size * 1.02); sw = max(5, size // 16)
    fs = None
    if sub:
        fs = ImageFont.truetype(core.F_DISPB, int(H * 0.054))
        while fs.size > 20 and fs.getbbox(sub)[2] > colw: fs = ImageFont.truetype(core.F_DISPB, fs.size - 2)
    fb = ImageFont.truetype(F_COND, int(H * 0.052)); bw = fb.getbbox(badge)[2]; bh = int(H * 0.085)
    blockw = max([f.getbbox(l)[2] + sw for l in lines] + [bw + bh * 0.9] + ([fs.getbbox(sub)[2]] if fs else []))
    x0 = int(W * 0.045) if side == "left" else int(W * 0.955 - blockw)
    # badge
    by = int(H * 0.07); d.rounded_rectangle((x0, by, x0 + bw + bh * 0.9, by + bh), bh // 2, fill=acc)
    d.text((x0 + bh * 0.45, by + bh / 2), badge, font=fb, fill="#0b0b0f", anchor="lm")
    # hook lines
    y = by + bh + int(H * 0.05)
    shd = Image.new("L", im.size, 0); ds = ImageDraw.Draw(shd)
    for i, l in enumerate(lines): ds.text((x0 + sw, y + i * lh + sw * 1.5), l, font=f, fill=210, stroke_width=sw, stroke_fill=210)
    if fs:
        yb = max(d.textbbox((x0, y + i * lh), l, font=f, stroke_width=sw)[3] for i, l in enumerate(lines)); ys = yb + int(H * 0.03)
        ds.text((x0 + 3, ys + 4), sub, font=fs, fill=230, stroke_width=6, stroke_fill=230)
    im = Image.composite(Image.new("RGB", im.size, (0, 0, 0)), im, shd.filter(ImageFilter.GaussianBlur(sw * 1.4))); d = ImageDraw.Draw(im)
    for i, l in enumerate(lines):
        d.text((x0, y + i * lh), l, font=f, fill=(acc if i == len(lines) - 1 else "#ffffff"), stroke_width=sw, stroke_fill="#0b0b0f")
    if fs: d.text((x0, ys), sub, font=fs, fill="#f4f4f4", stroke_width=2, stroke_fill="#0b0b0f")
    return np.asarray(im)

def ctx_args(song):
    """context_card kwargs from song.yaml (ctx_* override the thumb_* framing used by the older cards)."""
    g = lambda k, d: float(song.get("ctx_" + k, song.get("thumb_" + k, d)))
    return dict(lines=song["thumb_lines"], sub=song.get("thumb_sub"), accent=song.get("thumb_hook_color", song.get("accent")),
                side=song.get("thumb_hook_side", "left"), shift=g("shift", 0), shift_y=float(song.get("ctx_shift_y", float(song.get("thumb_shift_y", 0)) * 0.5)),
                scale=g("scale", 1), dark=float(song.get("ctx_dark", 0.62)), badge=song.get("ctx_badge", "CLAUDE ANIMATED THIS"))

def main(song_dir, times=None):
    song = load_song(song_dir); sc = load_scene(song_dir); out = song["out_dir"]; os.makedirs(out, exist_ok=True); T = song["title"]
    times = times or [float(song.get("thumb_time", 60))]
    core.STATE["clean"] = True
    for k, t in enumerate(times):
        base = sc.render_frame(t, 1920, 1080, 5)
        suffix = "" if k == 0 else f" option {k + 1}"
        if k == 0: Image.fromarray(base).save(os.path.join(out, f"{T} - YouTube thumbnail (no text).jpg"), quality=93)
        hooks = song.get("thumb_hooks", ["ANIMATED THIS", "CODED THIS"])
        if k == 0 and song.get("thumb_lines"):
            Image.fromarray(context_card(base, **ctx_args(song))).save(os.path.join(out, f"{T} - YouTube thumbnail.jpg"), quality=93)
            hooks = [h for h in hooks if h != hooks[0]] or []
            nm0 = f"{T} - YouTube thumbnail (CLAUDE {song.get('thumb_hooks', ['ANIMATED THIS'])[0].title()}).jpg"
            Image.fromarray(claude_card(base, song.get("thumb_hooks", ["ANIMATED THIS"])[0], song.get("thumb_hook_color", song.get("accent")), side=song.get("thumb_hook_side", "left"), shift=float(song.get("thumb_shift", 0)), scale=float(song.get("thumb_scale", 1)), shift_y=float(song.get("thumb_shift_y", 0)))).save(os.path.join(out, nm0), quality=93)
        if k == 0:
            for j, hk in enumerate(hooks):
                if song.get("thumb_lines"): j += 1
                nm = f"{T} - YouTube thumbnail.jpg" if j == 0 else f"{T} - YouTube thumbnail (CLAUDE {hk.title()}).jpg"
                Image.fromarray(claude_card(base, hk, song.get("thumb_hook_color", song.get("accent")), side=song.get("thumb_hook_side", "left"), shift=float(song.get("thumb_shift", 0)), scale=float(song.get("thumb_scale", 1)), shift_y=float(song.get("thumb_shift_y", 0)))).save(os.path.join(out, nm), quality=93)
            Image.fromarray(made_in_card(base, song.get("thumb_hook_side", "left") if song.get("thumb_hook_side") else "right", float(song.get("made_shift", 0)), float(song.get("thumb_scale", 1)))).save(os.path.join(out, f"{T} - YouTube thumbnail (MADE IN CLAUDE CODE).jpg"), quality=93)
            suffix = " (title style)"
        Image.fromarray(title_card(base, song.get("thumb_title", T), song.get("thumb_caption"), song.get("accent"), song.get("thumb_label"))).save(os.path.join(out, f"{T} - YouTube thumbnail{suffix}.jpg"), quality=93)
    core.STATE["clean"] = False
    ct = float(song.get("cover_time", times[0]))
    cov = sc.render_frame(ct, 1080, 1920, int(ct * 30))
    if "cover_hook_time" in song:
        core.STATE["clean"] = True; hc = float(song["cover_hook_time"]); cov_h = sc.render_frame(hc, 1080, 1920, int(hc * 30)); core.STATE["clean"] = False
    else: cov_h = cov
    Image.fromarray(claude_card(cov_h, song.get("thumb_hooks", ["ANIMATED THIS"])[0], song.get("thumb_hook_color", song.get("accent")))).save(os.path.join(out, f"{T} - Short cover (9x16).jpg"), quality=93)
    Image.fromarray(cov).save(os.path.join(out, f"{T} - Short cover (9x16, no text).jpg"), quality=93)
    print("thumbnails written to", out)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("song_dir"); ap.add_argument("--times", nargs="*", type=float)
    a = ap.parse_args(); main(a.song_dir, a.times)
