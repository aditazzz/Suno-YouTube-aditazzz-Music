"""Short C end card (1.5 s after the song section): the film's terminal look, dark and clean, inside the 9:16 safe zone.
render_frame(t, W, H) with t = seconds into the card (0..1.5)."""
import os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); SONG = os.path.dirname(HERE)
if SONG not in sys.path: sys.path.insert(0, SONG)
import scene as SC
from scene import C, S, text, tw, rrect, cursor, ease_out, sstep, BG, INK, MUTE, GREEN, RED, WHITE, F_MONOB, F_MONO, F_ANTON


def render_frame(t, W, H):
    """The three Shorts share one end card: Short A's (sections/short_a.py end_card)."""
    import short_a
    return short_a.end_card(t, W, H, int(5593 + t * 30))


def render_frame_old(t, W, H):
    ts = W / 1080; img = np.empty((H, W, 3), np.float32); img[:] = BG
    cx = W * 0.47                                         # centred a little left: the right 12% belongs to YouTube's buttons
    k1 = ease_out(t / 0.25)
    text(img, "❯ open @adita_zzz", S(84, ts), H * 0.20, S(40, ts), MUTE, k1, F_MONO)
    fs = S(66, ts)
    for i, l in enumerate(("Full video", "on my channel")):
        text(img, l, cx, H * 0.33 + i * fs * 1.3, fs, INK, k1, F_MONOB, anchor="c")
    k2 = ease_out((t - 0.15) / 0.3); pop = 1 + 0.1 * max(0.0, 1 - (t - 0.15) / 0.3)
    ps = int(S(84, ts) * pop); pw = tw("SUBSCRIBE", ps, F_ANTON) + ps * 1.4; ph = ps * 1.55
    rrect(img, cx - pw / 2, H * 0.47 - ph / 2, pw, ph, ph / 2, fill=RED, fill_op=k2)
    text(img, "SUBSCRIBE", cx, H * 0.47, ps, WHITE, k2, F_ANTON, anchor="c")
    k3 = ease_out((t - 0.3) / 0.3)
    w3 = tw("@adita_zzz", S(62, ts)); x3 = cx - w3 / 2
    text(img, "@adita_zzz", x3, H * 0.57, S(62, ts), GREEN, k3, F_MONOB)
    if t > 0.3: cursor(img, x3 + w3 + S(10, ts), H * 0.57 + S(10, ts), S(64, ts), t, GREEN, k3)
    fade = sstep(0.0, 0.2, t)
    img *= fade
    return C.finish(img, 190 + t, int(5700 + t * 30), SC.DUR + 10, vignette=True)
