"""Real footage inside a scene: frames from finished videos (or screen recordings), read in order through ffmpeg.

A scene asks for a frame of a clip at a time and a size:

    from studio import footage as FT
    fr = FT.frame("clips/the-promptress_0.mp4", t_local, 640, 360)       # (360, 640, 3) float32, 0..1
    FT.paste(img, fr, x, y, radius=12, op=1.0)                          # rounded-corner paste into the frame

One ffmpeg process per (clip, size, fit) streams forward, so rendering a chunk front to back decodes each clip once.
Asking for an earlier time (a new chunk, a loop) or a jump of more than two seconds restarts that reader at the new
spot. Readers left unused are closed, oldest first, so a 64-pane grid doesn't keep 64 decoders alive forever.
Clip times past the end loop by default (loop=False holds the last frame).
"""
import os, json, subprocess, collections
import numpy as np, cv2

FPS = 30
MAX_READERS = int(os.environ.get("STUDIO_FOOTAGE_READERS", "40"))
CLIP_DIRS = [d for d in os.environ.get("STUDIO_FOOTAGE_DIRS", "").split(os.pathsep) if d]


def resolve(path):
    """A clip name relative to one of STUDIO_FOOTAGE_DIRS (or an absolute path)."""
    if os.path.isabs(path) and os.path.exists(path): return path
    for d in CLIP_DIRS:
        p = os.path.join(d, path)
        if os.path.exists(p): return p
    return path


_DUR = {}
def duration(path):
    path = resolve(path)
    if path not in _DUR:
        try:
            out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", path],
                                 capture_output=True, text=True, timeout=20).stdout
            _DUR[path] = float(json.loads(out)["format"]["duration"])
        except Exception:
            _DUR[path] = 0.0
    return _DUR[path]


class _Reader:
    def __init__(self, path, w, h, idx, fit, trim=0.0):
        self.path, self.w, self.h, self.fit = path, w, h, fit
        self.i = idx - 1; self.last = None; self.eof = False
        pre = f"crop=iw:ih*{1 - trim:.4f}:0:0," if trim > 0 else ""   # trim: cut the bottom fraction first (burned-in captions)
        if fit == "cover":
            vf = pre + f"scale={w}:{h}:force_original_aspect_ratio=increase:flags=bicubic,crop={w}:{h}"
        else:   # contain: letterbox on black
            vf = pre + f"scale={w}:{h}:force_original_aspect_ratio=decrease:flags=bicubic,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2"
        self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{idx / FPS:.4f}", "-i", path, "-an", "-vf", f"{vf},fps={FPS}",
                                   "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                  bufsize=w * h * 3 * 2)

    def read_to(self, idx):
        n = self.w * self.h * 3
        while self.i < idx and not self.eof:
            b = self.p.stdout.read(n)
            if len(b) < n: self.eof = True; break
            self.last = b; self.i += 1
        return self.last

    def close(self):
        try:
            self.p.stdout.close(); self.p.kill(); self.p.wait(timeout=2)
        except Exception:
            pass


_READERS = collections.OrderedDict()
_LAST = {}


def frame(path, t, w, h, fit="cover", loop=True, trim=0.0):
    """The clip's frame at `t` seconds, scaled to (w, h): float32 (h, w, 3) in 0..1. Black if the clip can't be read."""
    path = resolve(path); w, h = int(w), int(h)
    d = duration(path)
    if d <= 0: return np.zeros((h, w, 3), np.float32)
    t = max(0.0, t)
    if t >= d - 1.0 / FPS: t = (t % d) if loop else d - 1.0 / FPS
    idx = int(t * FPS + 1e-6); key = (path, w, h, fit, round(trim, 3))
    r = _READERS.get(key)
    if r is not None and (idx < r.i or idx > r.i + 2 * FPS or (r.eof and idx > r.i)):
        r.close(); del _READERS[key]; r = None
    if r is None:
        r = _Reader(path, w, h, idx, fit, trim); _READERS[key] = r
        while len(_READERS) > MAX_READERS:
            _, old = _READERS.popitem(last=False); old.close()
    _READERS.move_to_end(key)
    b = r.read_to(idx)
    if b is None:
        return _LAST.get(key, np.zeros((h, w, 3), np.float32))
    out = np.frombuffer(b, np.uint8).reshape(h, w, 3).astype(np.float32) / 255.0
    _LAST[key] = out
    return out


_MASK = {}
def _rr_mask(w, h, r):
    k = (w, h, r)
    if k not in _MASK:
        m = np.zeros((h, w), np.uint8)
        if r <= 0: m[:] = 255
        else:
            cv2.rectangle(m, (r, 0), (w - r - 1, h - 1), 255, -1); cv2.rectangle(m, (0, r), (w - 1, h - r - 1), 255, -1)
            for cx, cy in ((r, r), (w - r - 1, r), (r, h - r - 1), (w - r - 1, h - r - 1)): cv2.circle(m, (cx, cy), r, 255, -1, cv2.LINE_AA)
        _MASK[k] = (m.astype(np.float32) / 255)[..., None]
        if len(_MASK) > 600: _MASK.clear()
    return _MASK[k]


def paste(img, fr, x, y, radius=0, op=1.0):
    """Paste a (h, w, 3) float frame at (x, y) with rounded corners, clipped to the image."""
    if op <= 0.003: return
    h, w = fr.shape[:2]; H, W = img.shape[:2]; x, y = int(round(x)), int(round(y))
    x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0: return
    m = _rr_mask(w, h, int(radius))[y0 - y:y1 - y, x0 - x:x1 - x] * op
    reg = img[y0:y1, x0:x1]
    reg *= (1 - m); reg += fr[y0 - y:y1 - y, x0 - x:x1 - x] * m


def still(path, w, h, fit="cover"):
    """An image file (jpg/png) scaled to (w, h), cached."""
    k = ("still", path, w, h, fit)
    if k in _LAST: return _LAST[k]
    im = cv2.imread(resolve(path), cv2.IMREAD_COLOR)
    if im is None: out = np.zeros((h, w, 3), np.float32)
    else:
        im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB); ih, iw = im.shape[:2]
        s = max(w / iw, h / ih) if fit == "cover" else min(w / iw, h / ih)
        im = cv2.resize(im, (max(1, int(iw * s + 0.5)), max(1, int(ih * s + 0.5))), interpolation=cv2.INTER_AREA)
        ih, iw = im.shape[:2]; out = np.zeros((h, w, 3), np.uint8)
        if fit == "cover":
            ox, oy = (iw - w) // 2, (ih - h) // 2; out = im[oy:oy + h, ox:ox + w]
        else:
            ox, oy = (w - iw) // 2, (h - ih) // 2; out[oy:oy + ih, ox:ox + iw] = im
        out = out.astype(np.float32) / 255.0
    _LAST[k] = out
    return out
