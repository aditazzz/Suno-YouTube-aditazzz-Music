"""Pixel (stitch) art: fonts, sprites, borders. Everything returns uint8 index arrays (0 = bare cloth)."""
import os
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
from engine import C, ERASE

FONTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")   # Anton + EB Garamond, both SIL Open Font License

CH = {'.': 0, 'R': C['red'], 'r': C['dred'], 'K': C['black'], 'W': C['white'], 'C': C['cream'], 'G': C['gold'],
      'T': C['terra'], 'S': C['skin'], 's': C['skind'], 'B': C['teal'], 'g': C['green'], 'y': C['grey'],
      'n': C['brown'], 'b': C['sky'], 'P': C['pink'], 'd': C['dgrey'], 'u': C['bubble'], 'Y': C['yellow'],
      'N': C['navy'], 'l': C['lbrown'], 'V': C['silver'], 'O': C['orange'], 'L': C['lgreen'], 'e': C['eye'], '#': ERASE}


def A(rows):
    """ASCII art -> index array."""
    if isinstance(rows, str):
        rows = [r for r in rows.split("\n") if r.strip() != ""]
        rows = [r.strip() for r in rows]
    w = max(len(r) for r in rows)
    out = np.zeros((len(rows), w), np.uint8)
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            out[y, x] = CH[ch]
    return out


def canvas(w, h, fill=0):
    return np.full((h, w), fill, np.uint8)


def paste(dst, src, x, y, mask=True):
    h, w = src.shape
    x0, y0 = max(x, 0), max(y, 0)
    x1, y1 = min(x + w, dst.shape[1]), min(y + h, dst.shape[0])
    if x0 >= x1 or y0 >= y1:
        return dst
    s = src[y0 - y:y1 - y, x0 - x:x1 - x]
    d = dst[y0:y1, x0:x1]
    if mask:
        m = s > 0
        d[m] = s[m]
    else:
        d[:] = s
    return dst


def recolor(a, mapping):
    out = a.copy()
    for k, v in mapping.items():
        out[a == C[k]] = C[v] if isinstance(v, str) else v
    return out


def flip(a):
    return a[:, ::-1].copy()


# ----------------------------------------------------------------------------- 5x7 font (classic column font)
_F57 = {
 ' ': (0,0,0,0,0), '!': (0,0,0x5F,0,0), '"': (0,7,0,7,0), '#': (0x14,0x7F,0x14,0x7F,0x14), '$': (0x24,0x2A,0x7F,0x2A,0x12),
 '%': (0x23,0x13,0x08,0x64,0x62), '&': (0x36,0x49,0x55,0x22,0x50), "'": (0,5,3,0,0), '(': (0,0x1C,0x22,0x41,0),
 ')': (0,0x41,0x22,0x1C,0), '*': (0x14,0x08,0x3E,0x08,0x14), '+': (8,8,0x3E,8,8), ',': (0,0x50,0x30,0,0),
 '-': (8,8,8,8,8), '.': (0,0x60,0x60,0,0), '/': (0x20,0x10,8,4,2),
 '0': (0x3E,0x51,0x49,0x45,0x3E), '1': (0,0x42,0x7F,0x40,0), '2': (0x42,0x61,0x51,0x49,0x46), '3': (0x21,0x41,0x45,0x4B,0x31),
 '4': (0x18,0x14,0x12,0x7F,0x10), '5': (0x27,0x45,0x45,0x45,0x39), '6': (0x3C,0x4A,0x49,0x49,0x30), '7': (1,0x71,9,5,3),
 '8': (0x36,0x49,0x49,0x49,0x36), '9': (6,0x49,0x49,0x29,0x1E), ':': (0,0x36,0x36,0,0), ';': (0,0x56,0x36,0,0),
 '<': (8,0x14,0x22,0x41,0), '=': (0x14,0x14,0x14,0x14,0x14), '>': (0,0x41,0x22,0x14,8), '?': (2,1,0x51,9,6),
 '@': (0x32,0x49,0x79,0x41,0x3E),
 'A': (0x7E,0x11,0x11,0x11,0x7E), 'B': (0x7F,0x49,0x49,0x49,0x36), 'C': (0x3E,0x41,0x41,0x41,0x22), 'D': (0x7F,0x41,0x41,0x22,0x1C),
 'E': (0x7F,0x49,0x49,0x49,0x41), 'F': (0x7F,9,9,9,1), 'G': (0x3E,0x41,0x49,0x49,0x7A), 'H': (0x7F,8,8,8,0x7F),
 'I': (0,0x41,0x7F,0x41,0), 'J': (0x20,0x40,0x41,0x3F,1), 'K': (0x7F,8,0x14,0x22,0x41), 'L': (0x7F,0x40,0x40,0x40,0x40),
 'M': (0x7F,2,0x0C,2,0x7F), 'N': (0x7F,4,8,0x10,0x7F), 'O': (0x3E,0x41,0x41,0x41,0x3E), 'P': (0x7F,9,9,9,6),
 'Q': (0x3E,0x41,0x51,0x21,0x5E), 'R': (0x7F,9,0x19,0x29,0x46), 'S': (0x46,0x49,0x49,0x49,0x31), 'T': (1,1,0x7F,1,1),
 'U': (0x3F,0x40,0x40,0x40,0x3F), 'V': (0x1F,0x20,0x40,0x20,0x1F), 'W': (0x3F,0x40,0x38,0x40,0x3F), 'X': (0x63,0x14,8,0x14,0x63),
 'Y': (7,8,0x70,8,7), 'Z': (0x61,0x51,0x49,0x45,0x43),
 'a': (0x20,0x54,0x54,0x54,0x78), 'b': (0x7F,0x48,0x44,0x44,0x38), 'c': (0x38,0x44,0x44,0x44,0x20), 'd': (0x38,0x44,0x44,0x48,0x7F),
 'e': (0x38,0x54,0x54,0x54,0x18), 'f': (8,0x7E,9,1,2), 'g': (0x0C,0x52,0x52,0x52,0x3E), 'h': (0x7F,8,4,4,0x78),
 'i': (0,0x44,0x7D,0x40,0), 'j': (0x20,0x40,0x44,0x3D,0), 'k': (0x7F,0x10,0x28,0x44,0), 'l': (0,0x41,0x7F,0x40,0),
 'm': (0x7C,4,0x18,4,0x78), 'n': (0x7C,8,4,4,0x78), 'o': (0x38,0x44,0x44,0x44,0x38), 'p': (0x7C,0x14,0x14,0x14,8),
 'q': (8,0x14,0x14,0x18,0x7C), 'r': (0x7C,8,4,4,8), 's': (0x48,0x54,0x54,0x54,0x20), 't': (4,0x3F,0x44,0x40,0x20),
 'u': (0x3C,0x40,0x40,0x20,0x7C), 'v': (0x1C,0x20,0x40,0x20,0x1C), 'w': (0x3C,0x40,0x30,0x40,0x3C), 'x': (0x44,0x28,0x10,0x28,0x44),
 'y': (0x0C,0x50,0x50,0x50,0x3C), 'z': (0x44,0x64,0x54,0x4C,0x44),
}


def glyph57(ch):
    cols = _F57.get(ch, _F57['?'])
    g = np.zeros((7, 5), np.uint8)
    for x, c in enumerate(cols):
        for y in range(7):
            if c >> y & 1:
                g[y, x] = 1
    # trim empty side columns for narrow glyphs (keeps i, l, !, . compact)
    if ch != ' ':
        used = np.where(g.any(0))[0]
        g = g[:, used[0]:used[-1] + 1]
    else:
        g = g[:, :3]
    return g


_F35 = {
 'A': "010101111101101", 'B': "110101110101110", 'C': "011100100100011", 'D': "110101101101110", 'E': "111100110100111",
 'F': "111100110100100", 'G': "011100101101011", 'H': "101101111101101", 'I': "111010010010111", 'J': "001001001101010",
 'K': "101101110101101", 'L': "100100100100111", 'M': "101111111101101", 'N': "110101101101101", 'O': "010101101101010",
 'P': "110101110100100", 'Q': "010101101110011", 'R': "110101110101101", 'S': "011100010001110", 'T': "111010010010010",
 'U': "101101101101111", 'V': "101101101101010", 'W': "101101111111101", 'X': "101101010101101", 'Y': "101101010010010",
 'Z': "111001010100111", '0': "111101101101111", '1': "010110010010111", '2': "110001010100111", '3': "110001010001110",
 '4': "101101111001001", '5': "111100110001110", '6': "011100111101111", '7': "111001010010010", '8': "111101111101111",
 '9': "111101111001110", ' ': "000000000000000", '.': "000000000000010", ',': "000000000010100", '!': "010010010000010",
 '?': "110001010000010", '-': "000000111000000", ':': "000010000010000", "'": "010010000000000", '+': "000010111010000",
 '/': "001001010100100",
}


def glyph35(ch):
    s = _F35.get(ch.upper(), _F35['?'])
    return np.array([int(c) for c in s], np.uint8).reshape(5, 3)


def text(s, color, font="57", spacing=1):
    """Returns (idx array, list of per-char (x0, x1)) for one line."""
    gl = [glyph57(c) if font == "57" else glyph35(c) for c in s]
    hgt = gl[0].shape[0] if gl else 7
    wtot = sum(g.shape[1] for g in gl) + spacing * (len(gl) - 1)
    out = np.zeros((hgt, max(wtot, 1)), np.uint8)
    spans = []
    x = 0
    col = C[color] if isinstance(color, str) else color
    for g in gl:
        out[:, x:x + g.shape[1]][g > 0] = col
        spans.append((x, x + g.shape[1]))
        x += g.shape[1] + spacing
    return out, spans


def text_w(s, font="57", spacing=1):
    return text(s, 1, font, spacing)[0].shape[1]


def big_text(s, color, px=22, font="Anton-Regular.ttf", thresh=120, tracking=1):
    """Rasterise a real font small and threshold it -> chunky stitched display lettering."""
    f = ImageFont.truetype(os.path.join(FONTS, font), px)
    glyphs = []
    for ch in s:
        if ch == ' ':
            glyphs.append(None)
            continue
        im = Image.new("L", (px * 2, px * 2), 0)
        d = ImageDraw.Draw(im)
        d.text((px // 2, px // 4), ch, 255, font=f)
        a = np.array(im)
        xs = np.where((a > thresh).any(0))[0]
        glyphs.append((a[:, xs[0]:xs[-1] + 1] > thresh) if len(xs) else None)
    # common vertical crop
    rows = np.zeros(px * 2, bool)
    for g in glyphs:
        if g is not None:
            rows |= g.any(1)
    ys = np.where(rows)[0]
    y0, y1 = ys[0], ys[-1] + 1
    col = C[color] if isinstance(color, str) else color
    parts, spans, x = [], [], 0
    sp = max(3, px // 4)
    for g in glyphs:
        if g is None:
            x += sp
            continue
        parts.append((x, g[y0:y1]))
        spans.append((x, x + g.shape[1]))
        x += g.shape[1] + tracking
    out = np.zeros((y1 - y0, x - tracking), np.uint8)
    for px_, g in parts:
        out[:, px_:px_ + g.shape[1]][g] = col
    return out, spans


# ----------------------------------------------------------------------------- reveal orders (per-cell times)
def order_cols(idx, t0, dur, spans=None, jitter=0.0):
    """Left to right, each column top to bottom (how a line of lettering is stitched)."""
    h, w = idx.shape
    xs = np.arange(w, dtype=np.float32)[None, :] + np.arange(h, dtype=np.float32)[:, None] / h
    t = t0 + dur * xs / max(w, 1)
    return t.astype(np.float32)


def order_rows(idx, t0, dur):
    h, w = idx.shape
    k = np.arange(h * w, dtype=np.float32).reshape(h, w)
    k[1::2] = k[1::2, ::-1]
    return (t0 + dur * k / (h * w)).astype(np.float32)


def order_radial(idx, t0, dur, cx=None, cy=None, power=1.0):
    h, w = idx.shape
    cx = w / 2 if cx is None else cx
    cy = h / 2 if cy is None else cy
    yy, xx = np.mgrid[0:h, 0:w]
    d = np.hypot(xx - cx, yy - cy)
    d = d / max(d[idx > 0].max() if (idx > 0).any() else 1, 1e-6)
    return (t0 + dur * np.clip(d, 0, 1) ** power).astype(np.float32)


def order_rand(idx, t0, dur, seed=0):
    rng = np.random.default_rng(seed)
    return (t0 + dur * rng.random(idx.shape)).astype(np.float32)


def order_up(idx, t0, dur):
    """Bottom to top (things that grow)."""
    h, w = idx.shape
    yy = (h - 1 - np.arange(h, dtype=np.float32))[:, None] + np.arange(w, dtype=np.float32)[None, :] / w
    return (t0 + dur * yy / h).astype(np.float32)


def order_down(idx, t0, dur):
    h, w = idx.shape
    yy = np.arange(h, dtype=np.float32)[:, None] + np.arange(w, dtype=np.float32)[None, :] / w
    return (t0 + dur * yy / h).astype(np.float32)


def order_beats(idx, beats, per_beat_dur=0.12, mode="radial", cx=None, cy=None):
    """Reveal in rings, one ring per beat (stop-motion bloom)."""
    h, w = idx.shape
    base = order_radial(idx, 0, 1, cx, cy)
    n = len(beats)
    ring = np.minimum((base * n).astype(int), n - 1)
    frac = base * n - ring
    return (np.array(beats, np.float32)[ring] + frac * per_beat_dur).astype(np.float32)


# ----------------------------------------------------------------------------- kilim patterns
def diamond(n, cols):
    """Concentric stepped diamond, size (2n+1). cols = list of colours from centre outward (cycled)."""
    s = 2 * n + 1
    out = np.zeros((s, s), np.uint8)
    for y in range(s):
        for x in range(s):
            d = abs(x - n) + abs(y - n)
            if d <= n:
                out[y, x] = C[cols[d % len(cols)]] if isinstance(cols[0], str) else cols[d % len(cols)]
    return out


def star8(r, col, col2=None):
    """Eight-pointed kilim star (two overlapped squares), radius r cells."""
    s = 2 * r + 1
    out = np.zeros((s, s), np.uint8)
    k = int(round(r * 0.7071))
    for y in range(s):
        for x in range(s):
            dx, dy = abs(x - r), abs(y - r)
            if max(dx, dy) <= k or dx + dy <= r:
                out[y, x] = C[col]
    if col2:
        k2 = max(1, r // 3)
        for y in range(s):
            for x in range(s):
                dx, dy = abs(x - r), abs(y - r)
                if dx + dy <= k2:
                    out[y, x] = C[col2]
    return out


def border_band(length, phase=0, style=0):
    """Horizontal kilim band, 7 cells high: running stepped diamonds between two rules."""
    h = 7
    out = np.zeros((h, length), np.uint8)
    out[0, :] = C['black']
    out[6, :] = C['black']
    for x in range(length):
        p = (x + phase) % 8
        d = abs(p - 4)            # 0..4
        for y in range(1, 6):
            dy = abs(y - 3)
            if style == 0:
                if d + dy <= 2:
                    out[y, x] = C['red'] if d + dy > 0 else C['gold']
                elif d + dy == 4 and dy == 2:
                    out[y, x] = C['black']
            else:
                if d + dy <= 2:
                    out[y, x] = C['black'] if d + dy > 0 else C['red']
                elif d + dy == 4 and dy == 2:
                    out[y, x] = C['red']
    return out


def zigzag(length, col='red', h=3, phase=0):
    out = np.zeros((h, length), np.uint8)
    per = 2 * (h - 1)
    for x in range(length):
        p = (x + phase) % per
        y = p if p < h else per - p
        out[y, x] = C[col]
    return out


def frame_rect(w, h, col='black', th=1):
    out = np.zeros((h, w), np.uint8)
    out[:th] = C[col]; out[-th:] = C[col]; out[:, :th] = C[col]; out[:, -th:] = C[col]
    return out


def rounded_rect(w, h, col, r=2, outline=None):
    out = np.full((h, w), C[col] if isinstance(col, str) else col, np.uint8)
    for i in range(r):
        cut = r - i - (1 if i > 0 else 0)
        cut = [2, 1][i] if r == 2 else ([3, 2, 1][i] if r == 3 else [1][i])
        out[i, :cut] = 0; out[i, w - cut:] = 0
        out[h - 1 - i, :cut] = 0; out[h - 1 - i, w - cut:] = 0
    if outline:
        m = out > 0
        er = cv2.erode(m.astype(np.uint8), np.ones((3, 3), np.uint8), borderValue=0) > 0
        out[m & ~er] = C[outline]
    return out


def heart(col='red'):
    return recolor(A("""
        .RR.RR.
        RRRRRRR
        RRRRRRR
        .RRRRR.
        ..RRR..
        ...R...
    """), {'red': col})


def tulip():
    return A("""
        ..R.R..
        .RRRRR.
        .RRRRR.
        ..RRR..
        ...g...
        .g.g.g.
        ..ggg..
        ...g...
    """)


def carnation():
    return A("""
        .R.R.R.R.
        .RRRRRRR.
        ..RrRrR..
        ...RRR...
        ....g....
        ..g.g.g..
        ...ggg...
        ....g....
        ....g....
    """)
