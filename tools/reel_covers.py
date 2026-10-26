"""Covers for already-posted Reels/Shorts: best frame of each clip + 'CLAUDE ANIMATED/CODED THIS' + song title,
all inside Instagram's 3:4 grid crop (y 12.5%..87.5%) so nothing is cut off on the profile grid.

usage: python tools/reel_covers.py <frames_dir> <out_dir> [--full <dir of full-res chosen frames>]
frames_dir holds '<clip name>__<k>.jpg' samples. Prints the chosen sample per clip.
"""
import os, sys, glob, json, re
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
from studio import core
F_COND = os.path.join(core.FONTS, "Anton-Regular.ttf")

SONGS = {   # song: (hook, accent). Longer names first: a clip belongs to the first name it starts with.
    "Git Blame": ("ANIMATED THIS", "#ff4d6d"),
    "Autocomplete": ("ANIMATED THIS", "#ff2fa8"),
    "AI Sycophant (RLHF)": ("ANIMATED THIS", "#ff6fb1"),
    "TED Talk": ("ANIMATED THIS", "#ffcc33"),
    "Graceful Shutdown": ("CODED THIS", "#7ee0ff"),
    "Merge Conflict": ("CODED THIS", "#ff6a5c"),
    "Rate Limited": ("CODED THIS", "#ff3d9a"),
    "Snowflake Undrop": ("ANIMATED THIS", "#8fe3ff"),
    "AI Sycophant": ("ANIMATED THIS", "#d7ff3a"),
    "Vacation (To My Bed)": ("ANIMATED THIS", "#ffd23f"),
    "Deployed on a Friday": ("ANIMATED THIS", "#ffd34e"),
}

def score(p):
    a = np.asarray(Image.open(p).convert("RGB")).astype(np.float32) / 255
    lum = a.mean(); rg = a[..., 0] - a[..., 1]; yb = (a[..., 0] + a[..., 1]) / 2 - a[..., 2]
    col = np.sqrt(rg.std() ** 2 + yb.std() ** 2) + 0.3 * np.sqrt(rg.mean() ** 2 + yb.mean() ** 2)
    dark = (a.max(-1) < 0.08).mean()
    detail = np.abs(np.diff(a.mean(-1), axis=1)).mean() * 10
    return lum * 0.8 + col * 1.6 + detail * 0.4 - dark * 0.6

def lift(a):
    """No black covers: lift dark frames (gamma + a little exposure)."""
    m = a.mean()
    if m < 0.30:
        g = np.interp(m, [0.03, 0.30], [0.55, 1.0]); a = np.clip(a ** g * np.interp(m, [0.03, 0.30], [1.35, 1.0]), 0, 1)
    return a

def colorfulness(a):
    rg = a[..., 0] - a[..., 1]; yb = (a[..., 0] + a[..., 1]) / 2 - a[..., 2]
    return float(np.sqrt(rg.std() ** 2 + yb.std() ** 2) + 0.3 * np.sqrt(rg.mean() ** 2 + yb.mean() ** 2))

def duotone(a, acc):
    """Grey line-art frames -> deep accent-tinted background with glowing accent/white lines."""
    c = np.array([int(acc[i:i + 2], 16) for i in (1, 3, 5)], np.float32) / 255
    L = a.mean(-1, keepdims=True); L = (L - L.min()) / max(1e-3, np.percentile(L, 99.5) - L.min()); L = np.clip(L, 0, 1)
    base = np.array([0.05, 0.04, 0.10], np.float32) + c * 0.07
    H, W = a.shape[:2]; yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    glow = np.exp(-(((xx - W / 2) / (W * 0.7)) ** 2 + ((yy - H * 0.45) / (H * 0.45)) ** 2))[..., None]
    bg = base * (0.6 + 1.2 * glow)
    out = bg * (1 - L) + (c * 0.75 + 0.25) * L
    out = out + np.clip(L - 0.75, 0, 1) * 1.6       # hottest lines go to white
    bl = np.asarray(Image.fromarray((np.clip(L[..., 0], 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(10))).astype(np.float32)[..., None] / 255
    return np.clip(out + bl * c * 0.9, 0, 1)

def cover(img, song, hook, acc, top="CLAUDE", tone=True, lines=None, sub=None, badge="CLAUDE ANIMATED THIS"):
    """lines: what-the-video-is-about hook (last line in the accent) with a small CLAUDE ANIMATED THIS badge above;
    without it, the older big CLAUDE / ANIMATED THIS stack."""
    im = img.convert("RGB").resize((1080, 1920), Image.LANCZOS); W, H = im.size
    a = np.asarray(im).astype(np.float32) / 255
    a = duotone(a, acc) if (tone and colorfulness(a) < 0.07) else (lift(a) if tone else a)
    yy = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    hc, hw, hs = (0.27, 0.21, 0.62) if lines else (0.24, 0.16, 0.5)
    a *= 1 - hs * np.clip(1 - np.abs(yy - hc) / hw, 0, 1)             # soft shade behind the hook
    a *= 1 - 0.45 * np.clip(1 - np.abs(yy - 0.76) / 0.12, 0, 1)       # and behind the title
    im = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))
    if lines:
        L = [l.upper() for l in lines]; lines = [(t, "#ffffff") for t in L[:-1]] + [(L[-1], acc)]
        d0 = ImageDraw.Draw(im); fb = ImageFont.truetype(F_COND, 58); bw = fb.getbbox(badge)[2]; bh = 92
        by = int(H * 0.14); bx = (W - bw - int(bh * 0.9)) // 2
        d0.rounded_rectangle((bx, by, bx + bw + bh * 0.9, by + bh), bh // 2, fill=acc, outline="#0b0b0f", width=5)
        d0.text((W // 2, by + bh // 2), badge, font=fb, fill="#0b0b0f", anchor="mm")
        size = 168
        while max(ImageFont.truetype(F_COND, size).getbbox(t)[2] for t, _ in lines) > W * 0.88: size -= 4
        y0 = by + bh + 34
    else:
        lines = [(top, "#ffffff"), (hook, acc)]; size = 240
        while max(ImageFont.truetype(F_COND, size).getbbox(t)[2] for t, _ in lines) > W * 0.86: size -= 4
        y0 = int(H * 0.145)
    f = ImageFont.truetype(F_COND, size); sw = max(6, size // 13); lh = int(size * 1.04)
    sh = Image.new("L", im.size, 0); ds = ImageDraw.Draw(sh)
    for i, (t, _) in enumerate(lines):
        x = (W - f.getbbox(t)[2]) // 2; ds.text((x + sw, y0 + i * lh + sw * 1.6), t, font=f, fill=200, stroke_width=sw, stroke_fill=200)
    im = Image.composite(Image.new("RGB", im.size, (0, 0, 0)), im, sh.filter(ImageFilter.GaussianBlur(sw * 1.2)))
    d = ImageDraw.Draw(im)
    for i, (t, c) in enumerate(lines):
        x = (W - f.getbbox(t)[2]) // 2; d.text((x, y0 + i * lh), t, font=f, fill=c, stroke_width=sw, stroke_fill="#0b0b0f")
    if sub:
        fs = ImageFont.truetype(core.F_DISPB, 54)
        while fs.size > 30 and fs.getbbox(sub)[2] > W * 0.86: fs = ImageFont.truetype(core.F_DISPB, fs.size - 2)
        yb = max(d.textbbox(((W - f.getbbox(t)[2]) // 2, y0 + i * lh), t, font=f, stroke_width=sw)[3] for i, (t, _) in enumerate(lines)) + 26
        d.text((W // 2 + 3, yb + 4), sub, font=fs, fill="#000000", anchor="ma", stroke_width=6, stroke_fill="#000000")
        d.text((W // 2, yb), sub, font=fs, fill="#f4f4f4", anchor="ma", stroke_width=2, stroke_fill="#0b0b0f")
    # song title pill, inside the 3:4 grid crop
    ts = 96
    ft = ImageFont.truetype(core.F_DISP, ts)
    while ft.getbbox(song)[2] > W * 0.80: ts -= 4; ft = ImageFont.truetype(core.F_DISP, ts)
    tw = ft.getbbox(song)[2]; ph = int(ts * 1.55); pw = tw + int(ts * 1.0); px = (W - pw) // 2; py = int(H * 0.775) - ph // 2
    sh2 = Image.new("L", im.size, 0); ImageDraw.Draw(sh2).rounded_rectangle((px + 8, py + 14, px + pw + 8, py + ph + 14), ph // 2, fill=170)
    im = Image.composite(Image.new("RGB", im.size, (0, 0, 0)), im, sh2.filter(ImageFilter.GaussianBlur(14)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((px, py, px + pw, py + ph), ph // 2, fill=acc, outline="#0b0b0f", width=6)
    d.text((W // 2, py + ph // 2), song, font=ft, fill="#0b0b0f", anchor="mm")
    return im

def song_of(name):
    for s in SONGS:
        if name.startswith(s): return s
    return name.split(" - ")[0]

if __name__ == "__main__":
    fd, od = sys.argv[1], sys.argv[2]; full = sys.argv[4] if len(sys.argv) > 4 and sys.argv[3] == "--full" else None
    os.makedirs(od, exist_ok=True)
    clips = sorted({re.sub(r"__\d+\.jpg$", "", os.path.basename(p)) for p in glob.glob(os.path.join(fd, "*__*.jpg"))})
    picks = {}
    for c in clips:
        cands = sorted(glob.glob(os.path.join(fd, glob.escape(c) + "__*.jpg")))
        best = max(cands, key=score); picks[c] = int(re.search(r"__(\d+)\.jpg$", best).group(1))
        src = os.path.join(full, c + ".jpg") if full and os.path.exists(os.path.join(full, c + ".jpg")) else best
        s = song_of(c); hook, acc = SONGS.get(s, ("ANIMATED THIS", "#d7ff3a"))
        title = "AI Sycophant" if s == "AI Sycophant" else s
        cover(Image.open(src), title, hook, acc).save(os.path.join(od, c.replace("Instagram 9x16", "Instagram") + " - cover.jpg"), quality=92)
    json.dump(picks, open(os.path.join(od, "picks.json"), "w"), indent=1)
    print(len(clips), "covers")
