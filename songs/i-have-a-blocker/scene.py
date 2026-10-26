"""I have a blocker. (Take It Offline), v2: the 3D film.

The picture is rendered in 3D (three.js, web/), frame by frame, into build/v2master_<fmt>.mp4 (see web/render_all.sh).
This module lets the studio pipeline treat those masters like any other scene: render_frame(t, W, H) returns the master's
frame at t (upscaled to W x H) with the channel's 2D layer on top (mid-video subscribe pill, end card), so studio.render
(finals), studio.cuts (Shorts and Reels), studio.thumbs and tools/yt_short_endcard work unchanged."""
import os, sys, math
import numpy as np, cv2

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE)); sys.path.insert(0, ROOT)
from studio import core as C

FPS = 30
SONG = 179.8; TAIL = 3.5; DUR = SONG + TAIL
END_AT = 174.5
C.THEME.update(red=C.hexc("ef4b4b"))
GREEN = C.hexc("3ee07a")


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


_R = {}
def master(fmt):
    if fmt not in _R: _R[fmt] = Reader(os.path.join(HERE, "build", f"v2master_{fmt}.mp4"))
    return _R[fmt]


def render_frame(t, W=1920, H=1080, fi=None):
    fmt = "16x9" if W >= H else "9x16"
    fr = master(fmt).get(int(round(t * FPS)))
    if fr.shape[1] != W or fr.shape[0] != H:
        fr = cv2.resize(fr, (W, H), interpolation=cv2.INTER_CUBIC)
        bl = cv2.GaussianBlur(fr, (0, 0), 1.0)
        fr = cv2.addWeighted(fr, 1.35, bl, -0.35, 0)                    # a touch of sharpening after the upscale
    if C.STATE["clean"]: return fr
    if t < END_AT and not (W >= H and 59.4 <= t <= 64.5): return fr   # no 2D layer here: skip the float pass
    out = fr.astype(np.float32) / 255
    C.subscribe_pill(out, t, W, H, 59.45, 5.0, line="@adita_zzz  ·  songs about tech life")
    C.end_screen(out, t, W, H, END_AT, DUR - END_AT, "Same time tomorrow.",
                 sub_line="Subscribe for more songs about tech life", title="I have a blocker. (Take It Offline)", accent=GREEN)
    return (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)
