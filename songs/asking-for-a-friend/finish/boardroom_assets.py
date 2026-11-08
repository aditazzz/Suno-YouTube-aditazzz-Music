"""Boardroom screen + city plates (PIL; venv python):  python3 boardroom_assets.py"""
import os, math, random
HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.expanduser("~/Documents/Original Music/Asking for a Friend 2/blender")
FONTS = os.environ.get("STUDIO_FONTS", "assets/fonts")   # the studio fonts (repo root assets/fonts)
SCR_PNG = os.path.join(DOCS, "textures", "screens", "br_main_screen.png")
os.makedirs(os.path.dirname(SCR_PNG), exist_ok=True)
from PIL import Image, ImageDraw, ImageFont, ImageFilter


def make_screen():
    W, H = 2400, 1352
    im = Image.new("RGB", (W, H), (9, 13, 20)); d = ImageDraw.Draw(im)
    for y in range(H):                                          # faint vertical falloff so it is not a flat slab
        k = 1.0 - 0.35 * (y / H)
        d.line([(0, y), (W, y)], fill=(int(12 * k), int(17 * k), int(26 * k)))
    A = lambda s: ImageFont.truetype(os.path.join(FONTS, "Anton-Regular.ttf"), s)
    I = lambda s: ImageFont.truetype(os.path.join(FONTS, "Inter-SemiBold.otf"), s)
    SOFT, STEEL, RED = (222, 229, 238), (88, 108, 130), (196, 28, 44)
    # company voice: Anton labels (cap 146 px of 1352 = the >=34 px-at-1080 floor in the c3 framing), a quiet status strip on top
    d.rectangle([0, 0, W, 92], fill=(16, 23, 34)); d.line([(0, 92), (W, 92)], fill=STEEL, width=4)
    d.ellipse([70, 30, 102, 62], fill=RED)
    for k in range(5): d.rounded_rectangle([140 + k * 210, 36, 140 + k * 210 + 170, 56], radius=10, fill=(40, 54, 72))

    def node(cx_, cy, w, h, label, fill, edge, tcol=SOFT, size=170):
        d.rounded_rectangle([cx_ - w // 2, cy - h // 2, cx_ + w // 2, cy + h // 2], radius=26, fill=fill, outline=edge, width=8)
        d.text((cx_, cy + int(size * 0.43)), label, font=A(size), fill=tcol, anchor="ms")

    def arrow(p, q):
        d.line([p, q], fill=STEEL, width=12)
        dx, dy = q[0] - p[0], q[1] - p[1]; n = math.hypot(dx, dy); ux, uy = dx / n, dy / n
        a = (q[0] - 48 * ux + 26 * -uy, q[1] - 48 * uy + 26 * ux); b = (q[0] - 48 * ux - 26 * -uy, q[1] - 48 * uy - 26 * ux)
        d.polygon([q, a, b], fill=STEEL)
    NF, NE = (24, 33, 46), (130, 152, 176)
    X0, XL, XR = 1200, 520, 1880
    node(X0, 310, 1000, 230, "SHUT DOWN?", NF, NE)
    node(XL, 720, 860, 230, "BACKUPS?", NF, NE)
    node(XR, 720, 860, 230, "BILLING?", NF, NE)
    node(X0, 1130, 900, 230, "UNKNOWN", (150, 20, 36), (255, 110, 120))
    arrow((X0 - 250, 430), (XL + 120, 596)); arrow((X0 + 250, 430), (XR - 120, 596))
    arrow((XL + 120, 840), (X0 - 300, 1010)); arrow((XR - 120, 840), (X0 + 300, 1010))
    im.save(SCR_PNG)


CITY_PNG = os.path.join(DOCS, "textures", "screens", "br_city_night.png")


def make_city():
    rnd = random.Random(11); W, H = 4096, 1024
    im = Image.new("RGB", (W, H), (3, 5, 9)); d = ImageDraw.Draw(im)
    for y in range(H):
        t = y / H; d.line([(0, y), (W, y)], fill=(int(3 + 14 * t ** 3), int(5 + 12 * t ** 3), int(10 + 26 * t ** 3)))
    x = 0
    while x < W:                                          # towers: dark silhouettes with lit window cells
        bw = rnd.randint(70, 200); bh = rnd.randint(200, 760); top = H - bh
        shade = rnd.randint(6, 14); d.rectangle([x, top, x + bw, H], fill=(shade, shade + 2, shade + 6))
        for wy in range(top + 10, H - 10, 13):
            for wx in range(x + 8, x + bw - 10, 10):
                if rnd.random() < 0.34:
                    warm = rnd.random() < 0.62
                    c = (255, 200, 130) if warm else (170, 205, 255)
                    k = rnd.uniform(0.35, 1.0)
                    d.rectangle([wx, wy, wx + 4, wy + 6], fill=tuple(int(v * k) for v in c))
        x += bw + rnd.randint(-20, 30)
    for _ in range(220):                                  # street-level lights, a few red beacons on rooftops
        px, py = rnd.randint(0, W), rnd.randint(H - 40, H - 4); d.ellipse([px, py, px + 8, py + 8], fill=(255, 190, 120))
    im = im.filter(ImageFilter.GaussianBlur(1.3)); im.save(CITY_PNG)



make_screen(); make_city(); print("assets ok")
