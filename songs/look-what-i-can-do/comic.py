"""The comic-book pass: between sections the camera pulls back to one comic page that maps the whole film (12 panels,
one per section, read left to right) and steps into the next panel.

  python3 comic.py <flat.mp4> <out.mp4>          # flat.mp4: the assembled film (picture only)
  python3 comic.py <flat.mp4> --page <t> <out.jpg>  # preview one composited frame

Each panel is 16:9 like the frame, so when the view rect equals a panel rect the panel IS the frame: the transition
starts and ends seamlessly. Panels already visited show their key frame in full colour; panels still to come are inked
but not yet coloured (high-contrast greyscale, the "pencils"). The two live panels play the film itself.
"""
import os, sys, subprocess, math
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1920, 1080, 30
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FONTS = os.path.join(ROOT, "assets", "fonts")
# section starts (frames) in reading order; the comic page has one panel per entry
SECTIONS = [("P1", 0, "THE SESSION"), ("S1", 1288, "BLUE HOUR"), ("S2", 1713, "SHIP IT"), ("S3", 1963, "THE COMMENTS"),
            ("S4", 2400, "IN THE WALLS"), ("S5", 2530, "THE SWARM"), ("S6", 3000, "THE DAILY STANDUP"), ("S7", 3688, "THE KEYNOTE"),
            ("S8", 4096, "THE SEERESS"), ("BD", 4553, "I KNEW IT"), ("S9", 4749, "PLEASE HOLD"), ("S10", 5152, "USAGE LIMIT")]
END = 5448
# boundaries that get the page (others stay hard cuts: P1->S1 flies out of the laptop, S8->BD fades to black, BD->S9 is the drop hit)
TRANS = {"S2", "S3", "S4", "S5", "S6", "S7", "S8", "S10"}
HALF = 11                                   # frames on each side of a boundary

PS = 2                                      # page supersampling (the page is drawn at 2x and cropped)
PW, PH = W * PS, H * PS
COLS, ROWS = 4, 3; MARG = 70 * PS; GUT = 30 * PS; VGUT = 70 * PS; BORDER = 7 * PS
CW = (PW - 2 * MARG - (COLS - 1) * GUT) / COLS; CH = CW * 9 / 16
TOP = (PH - (ROWS * CH + (ROWS - 1) * VGUT)) / 2 + 20 * PS
# aged newsprint: stays under the glow line (no pixel >0.92) between dark sections
PAPER = (214, 208, 196); INKC = (17, 17, 19); CAPTION = (255, 225, 77)


def panel_rect(i):  # in page pixels
    c, r = i % COLS, i // COLS
    x = MARG + c * (CW + GUT); y = TOP + r * (CH + VGUT)
    return x, y, CW, CH


def font(name, size): return ImageFont.truetype(os.path.join(FONTS, name), int(size))


def paper():
    im = Image.new("RGB", (PW, PH), PAPER); a = np.asarray(im).astype(np.float32)
    yy, xx = np.mgrid[0:PH, 0:PW]                                       # a faint halftone on the paper, like print
    dots = (np.sin(xx * 0.18 / PS) * np.sin(yy * 0.18 / PS) > 0.92).astype(np.float32)
    a -= dots[..., None] * 10
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def pencils(img):   # an upcoming panel: inked but not coloured
    g = cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2GRAY).astype(np.float32)
    g = np.clip((g - 40) * 1.35, 0, 255); g = 255 - (255 - g) * 0.75
    e = cv2.Canny(np.asarray(img), 60, 140).astype(np.float32)
    g = np.clip(g - e * 0.6, 0, 255)
    return Image.fromarray(np.stack([g * 0.98, g * 0.97, g * 0.94], -1).astype(np.uint8))


class Page:
    def __init__(self, keyframes):
        self.base = paper(); self.key = keyframes        # {idx: PIL image (W,H)}
        d = ImageDraw.Draw(self.base)
        f = font("Anton-Regular.ttf", 40 * PS)
        d.text((MARG, 18 * PS), "LOOK WHAT I CAN DO", font=f, fill=INKC)
        f2 = font("JBMono-700.ttf", 22 * PS)
        d.text((PW - MARG, 40 * PS), "ADITAZZZ · A COMIC OF EVERYTHING WE MADE · ISSUE #1", font=f2, fill=(70, 68, 64), anchor="ra")

    def render(self, cur, nxt, live_i, live_img, visited):
        """The page with every panel; live_i shows live_img; panels < visited are coloured."""
        im = self.base.copy(); d = ImageDraw.Draw(im)
        fc = font("Anton-Regular.ttf", 24 * PS)
        for i, (sid, f0, title) in enumerate(SECTIONS):
            x, y, w, h = panel_rect(i)
            src = live_img if i == live_i else self.key.get(i)
            if src is not None:
                pic = src.resize((int(w), int(h)), Image.LANCZOS)
                if i != live_i and i >= visited: pic = pencils(pic)
                im.paste(pic, (int(x), int(y)))
            d.rectangle([x - BORDER, y - BORDER, x + w + BORDER, y + h + BORDER], outline=INKC, width=BORDER)
            # caption tab above the panel, in the gutter (outside the panel, so a panel that fills the frame is clean)
            cap = f"{i + 1:02d} · {title}"; tw = d.textlength(cap, font=fc); y0 = y - BORDER - 46 * PS
            d.rectangle([x - BORDER, y0, x + tw + 26 * PS, y - BORDER], fill=CAPTION); d.rectangle([x - BORDER, y0, x + tw + 26 * PS, y - BORDER], outline=INKC, width=3 * PS)
            d.text((x + 10 * PS, y0 + 7 * PS), cap, font=fc, fill=INKC)
        return im


def ease(x): x = min(1, max(0, x)); return x * x * (3 - 2 * x)


def view_rect(i, j, u):
    """u in [0,1]: 0 = panel i fills the frame, 0.5 = pulled back over both, 1 = panel j fills the frame."""
    a, b = panel_rect(i), panel_rect(j)
    ax, ay = a[0] + a[2] / 2, a[1] + a[3] / 2; bx, by = b[0] + b[2] / 2, b[1] + b[3] / 2
    k = ease(u)
    cx, cy = ax + (bx - ax) * k, ay + (by - ay) * k
    # zoom: panel width at the ends, about 2.4 panels wide in the middle (the page reads, the live panel stays big)
    z = math.sin(math.pi * min(1, max(0, u))) ** 0.8
    w = CW * (1 + 1.55 * z) + abs(bx - ax) * 0.55 * z; h = w * 9 / 16
    return cx - w / 2, cy - h / 2, w, h


def composite(page_img, rect):
    x, y, w, h = rect
    M = np.float32([[W / w, 0, -x * W / w], [0, H / h, -y * H / h]])
    return cv2.warpAffine(np.asarray(page_img), M, (W, H), flags=cv2.INTER_AREA, borderValue=PAPER)


def trans_index():
    """frame -> (prev panel, next panel, u, live panel)"""
    m = {}
    for j, (sid, f0, _) in enumerate(SECTIONS):
        if sid not in TRANS: continue
        i = j - 1
        for n in range(f0 - HALF, f0 + HALF):
            u = (n - (f0 - HALF) + 0.5) / (2 * HALF)
            m[n] = (i, j, u, i if n < f0 else j)
    return m


def read_frames(path):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", path, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    while True:
        b = p.stdout.read(W * H * 3)
        if len(b) < W * H * 3: break
        yield np.frombuffer(b, np.uint8).reshape(H, W, 3)


def grab(path, n):
    b = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{n / FPS:.4f}", "-i", path, "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    return Image.fromarray(np.frombuffer(b[:W * H * 3], np.uint8).reshape(H, W, 3))


def keyframes(flat):
    """each panel's key art: a frame ~45% into its section (the director can override in KEY)."""
    KEY = {"P1": 1180, "S7": 3840, "BD": 4740}
    out = {}
    for i, (sid, f0, _) in enumerate(SECTIONS):
        f1 = SECTIONS[i + 1][1] if i + 1 < len(SECTIONS) else END
        out[i] = grab(flat, KEY.get(sid, int(f0 + (f1 - f0) * 0.45)))
    return out


def main():
    flat = sys.argv[1]
    page = Page(keyframes(flat)); T = trans_index()
    if sys.argv[2] == "--page":
        n = int(round(float(sys.argv[3]) * FPS)); i, j, u, li = T[n]
        live = grab(flat, n); vis = j if n >= SECTIONS[j][1] else i
        Image.fromarray(composite(page.render(i, j, li, live, vis + 1), view_rect(i, j, u))).save(sys.argv[4], quality=92); return
    out = sys.argv[2]
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-c:v", "libx264", "-preset", "veryfast", "-crf", "15", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for n, fr in enumerate(read_frames(flat)):
        if n in T:
            i, j, u, li = T[n]; vis = (j if n >= SECTIONS[j][1] else i) + 1
            fr = composite(page.render(i, j, li, Image.fromarray(fr), vis), view_rect(i, j, u))
        enc.stdin.write(np.ascontiguousarray(fr).tobytes())
    enc.stdin.close(); enc.wait(); print("wrote", out)


if __name__ == "__main__":
    main()
