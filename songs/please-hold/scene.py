"""Please Hold: the 3D film.

The picture is rendered in 3D (three.js, web/), frame by frame, into build/h (16:9, 1600x900) and build/v (9:16, 900x1600),
then (optionally) assembled into silent masters build/master_<fmt>.mp4 (assemble.sh); while the frames are on disk they
are read directly. This module lets the studio pipeline treat them like any other scene: render_frame(t, W, H) returns the master's frame at t (upscaled to W x H) with the
channel's 2D layer on top (the 16:9 subscribe pill after the first chorus), so studio.render (finals), studio.cuts
(Shorts, Reels and the under-3-minute edit) and studio.thumbs work unchanged. The end card (a keypad: "To subscribe,
press 1.") is part of the 3D film itself, with the right half of the 16:9 frame left clear for YouTube's end screen."""
import os, sys
import numpy as np, cv2

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE)); sys.path.insert(0, ROOT)
from studio import core as C

FPS = 30
SONG = 206.28; TAIL = 6.72; DUR = SONG + TAIL          # the audio stops dead at 206.28 (the battery dies); the end card follows
PILL_AT, PILL_DUR = 102.35, 4.6                         # right after the first chorus (16:9 only)
C.THEME.update(red=C.hexc("ff6a1a"))


class Reader:
    """sequential-friendly frame reader for one master (seeks only when asked for a frame out of order)."""
    def __init__(self, path):
        self.path = path; self.cap = None; self.next = 0; self.last = None; self.n = None
    def get(self, fi):
        if self.cap is None:
            self.cap = cv2.VideoCapture(self.path)
            if not self.cap.isOpened(): raise SystemExit(f"missing 3D master: {self.path}")
            self.n = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)); self.next = 0
        fi = max(0, min(fi, self.n - 1))
        if self.last is not None and fi == self.next - 1: return self.last
        if fi != self.next:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, fi); self.next = fi
        ok, fr = self.cap.read()
        if not ok: return self.last if self.last is not None else np.zeros((900, 1600, 3), np.uint8)
        self.next = fi + 1; self.last = cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)
        return self.last


class Frames:
    """the rendered JPEG frames themselves (build/h, build/v), when they're still on disk: no master needed."""
    def __init__(self, d): self.d = d; self.n = len([f for f in os.listdir(d) if f.endswith(".jpg")])
    def get(self, fi):
        fi = max(0, min(fi, self.n - 1)); im = cv2.imread(os.path.join(self.d, f"f_{fi:05d}.jpg"))
        if im is None: raise SystemExit(f"missing frame {fi} in {self.d}")
        return cv2.cvtColor(im, cv2.COLOR_BGR2RGB)


_R = {}
def master(fmt):
    if fmt not in _R:
        d = os.path.join(HERE, "build", "h" if fmt == "16x9" else "v")
        if os.path.isdir(d) and os.path.exists(os.path.join(d, f"f_{int(DUR * FPS) - 1:05d}.jpg")): _R[fmt] = Frames(d)
        else: _R[fmt] = Reader(os.path.join(HERE, "build", f"master_{fmt}.mp4"))
    return _R[fmt]


def clean_plate(t, W, H):
    """a clean still rendered for covers (build/covers_raw/s_<t>.jpg, no lyrics or HUD), when one exists for t."""
    p = os.path.join(HERE, "build", "covers_raw", f"s_{t:.2f}.jpg")
    if not os.path.exists(p): return None
    im = cv2.cvtColor(cv2.imread(p), cv2.COLOR_BGR2RGB)
    if im.shape[0] > im.shape[1] and W < H or im.shape[0] <= im.shape[1] and W >= H:
        return cv2.resize(im, (W, H), interpolation=cv2.INTER_AREA if im.shape[1] > W else cv2.INTER_CUBIC)
    return None


def render_frame(t, W=1920, H=1080, fi=None):
    fmt = "16x9" if W >= H else "9x16"
    if C.STATE["clean"]:
        cp = clean_plate(t, W, H)
        if cp is not None: return cp
    fr = master(fmt).get(int(round(t * FPS)))
    if fr.shape[1] != W or fr.shape[0] != H:
        fr = cv2.resize(fr, (W, H), interpolation=cv2.INTER_CUBIC)
        bl = cv2.GaussianBlur(fr, (0, 0), 1.0)
        fr = cv2.addWeighted(fr, 1.35, bl, -0.35, 0)                    # a touch of sharpening after the upscale
    if C.STATE["clean"]: return fr
    if not (W >= H and PILL_AT - 0.5 <= t <= PILL_AT + PILL_DUR + 0.5): return fr   # no 2D layer here: skip the float pass
    out = fr.astype(np.float32) / 255
    C.subscribe_pill(out, t, W, H, PILL_AT, PILL_DUR, line="@adita_zzz  ·  songs about tech life")
    return (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)
