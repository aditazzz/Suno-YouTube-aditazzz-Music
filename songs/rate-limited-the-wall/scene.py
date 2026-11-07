"""Rate Limited (The Wall): the Remotion film.

The picture is drawn in Remotion (remotion/: React + one canvas, every frame a pure function of the time) and rendered
into silent masters build/master_<fmt>.mp4 (see README.md). This module lets the studio pipeline treat them like any
other scene: render_frame(t, W, H) returns the master's frame at t with the channel's 2D layer on top (the lyric captions,
the 16:9 subscribe pill after the first chorus, the end card on the black after the cut), so studio.render (finals),
studio.cuts (Shorts and Reels), studio.thumbs and studio.safezone work unchanged.

    python3 songs/rate-limited-the-wall/scene.py spec    build/spec.npy: the song's 48-band spectrum (the cracks' leak)
    python3 songs/rate-limited-the-wall/scene.py plan    caption_place_9x16.json: 9:16 caption bands, from the 9:16 master
"""
import os, sys, json
import numpy as np, cv2

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE)); sys.path.insert(0, ROOT)
from studio import core as C, caplayer
from studio.config import load_song

FPS = 30
TM = C.Timing(HERE)
SONG = TM.duration; TAIL = float(load_song(HERE).get("tail", 4.0)); DUR = SONG + TAIL
T_CUT = min(d for d in TM.downbeats if d > TM.lines[-1]["e"] - 1.2)   # cut to black on her blink (remotion/src/story.ts T.cut)
T_END = T_CUT + 0.3                                                    # keep in sync with song.yaml end_screen_at
PILL_AT, PILL_DUR = TM.section("V2")["s"] + 1.2, 5.5                   # right after the first chorus (16:9 only)
AMBER = C.hexc("ffac3a")
C.THEME.update(red=AMBER)

# captions are their own layer, over the caption-free master. Left out: lines the world already shows (the hum is the
# thread drawing itself, the wall etches RATE LIMITED and USAGE LIMIT REACHED, the flip clock reads 3:59 -> 3:58, and
# Bridge 2 is his side, the film's only mint type) and anything after the cut to black.
CAPTIONS = os.environ.get("RL_CAPTIONS", "1") != "0"
SHOWN = {"Mm-mm-mm", "Rate limited, rate limited#CH2", "Three fifty-nine", "Three fifty-eight", "Usage limit reached"}
CAP_SKIP = {i for i, L in enumerate(TM.lines)
            if L["sec"] == "BRIDGE2" or L["text"] in SHOWN or f"{L['text']}#{L['sec']}" in SHOWN}
CAP_ENDS = {len(TM.lines) - 1: T_CUT - 0.05}
PLACE_9x16 = os.path.join(HERE, "caption_place_9x16.json")
DEFAULT_Y_9x16 = 0.62            # between the wall's base and her, inside the safe zone, until a plan exists


def captions(fr, t, W, H):
    out = fr.astype(np.float32) / 255
    if W >= H:
        C.overlay_lyrics(out, t, W, H, TM, active=AMBER, glow=AMBER, skip=lambda L: TM.lines.index(L) in CAP_SKIP or L["s"] > T_CUT)
    else:
        if "place" not in _CAP: _CAP["place"] = caplayer.load_place(PLACE_9x16)
        caplayer.draw(out, t, W, H, TM.lines, _CAP["place"], skip=CAP_SKIP, ends=CAP_ENDS, default_y=DEFAULT_Y_9x16)
    return out
_CAP = {}


class Reader:
    """sequential-friendly frame reader for one master (seeks only when asked for a frame out of order)."""
    def __init__(self, path):
        self.path = path; self.cap = None; self.next = 0; self.last = None; self.n = None
    def get(self, fi):
        if self.cap is None:
            self.cap = cv2.VideoCapture(self.path)
            if not self.cap.isOpened():
                raise SystemExit(f"missing master: {self.path}  (cd {os.path.join(HERE, 'remotion')} && npm run master -- "
                                 f"{os.path.basename(self.path)[7:-4]})")
            self.n = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)); self.next = 0
        fi = max(0, min(fi, self.n - 1))
        if self.last is not None and fi == self.next - 1: return self.last
        if fi != self.next:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, fi); self.next = fi
        ok, fr = self.cap.read()
        if not ok: return self.last if self.last is not None else np.zeros((1080, 1920, 3), np.uint8)
        self.next = fi + 1; self.last = cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)
        return self.last


_R = {}
def master(fmt):
    if fmt not in _R: _R[fmt] = Reader(os.path.join(HERE, "build", f"master_{fmt}.mp4"))
    return _R[fmt]


def render_frame(t, W=1920, H=1080, fi=None):
    fmt = "16x9" if W >= H else "9x16"
    fr = master(fmt).get(int(round(t * FPS)) if fi is None else fi)
    if fr.shape[1] != W or fr.shape[0] != H:
        fr = cv2.resize(fr, (W, H), interpolation=cv2.INTER_CUBIC if fr.shape[1] < W else cv2.INTER_AREA)
    if C.STATE["clean"]: return fr
    pill = W >= H and PILL_AT - 0.5 <= t <= PILL_AT + PILL_DUR + 0.5
    cap = CAPTIONS and t < T_CUT + 0.2
    if not (pill or cap or t >= T_END): return fr
    out = captions(fr, t, W, H) if cap else fr.astype(np.float32) / 255
    if pill: C.subscribe_pill(out, t, W, H, PILL_AT, PILL_DUR, line="@adita_zzz  ·  songs about tech life")
    if t >= T_END: C.end_screen(out, t, W, H, T_END, DUR - T_END, "Where were we?", title="Rate Limited", accent=AMBER)
    return (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)


def spectrum():
    """48 log-spaced bands, 40 Hz-14 kHz, 30 fps, normalised per band, fast attack and smooth release (the same analysis
    as the original cut's build/spec.npy, recomputed from this song's audio)."""
    import soundfile as sf
    y, sr = sf.read(load_song(HERE)["audio"], dtype="float32")
    if y.ndim > 1: y = y.mean(1)
    hop = sr / FPS; n = 4096; win = np.hanning(n).astype(np.float32)
    N = int(len(y) / hop); NB = 48
    freqs = np.fft.rfftfreq(n, 1 / sr); edges = np.geomspace(40, 14000, NB + 1)
    idx = [(np.searchsorted(freqs, edges[i]), max(np.searchsorted(freqs, edges[i]) + 1, np.searchsorted(freqs, edges[i + 1]))) for i in range(NB)]
    S = np.zeros((N, NB), np.float32)
    for f in range(N):
        a = int(f * hop); seg = y[a:a + n]
        if len(seg) < n: seg = np.pad(seg, (0, n - len(seg)))
        m = np.abs(np.fft.rfft(seg * win))
        S[f] = [m[i0:i1].mean() for i0, i1 in idx]
    S = np.log1p(S * 4)
    lo, hi = np.percentile(S, 8, 0), np.percentile(S, 99.3, 0)
    S = np.clip((S - lo) / (hi - lo + 1e-6), 0, 1)
    for f in range(1, N): S[f] = np.maximum(S[f], S[f - 1] * 0.82)
    p = os.path.join(HERE, "build", "spec.npy"); np.save(p, S.astype(np.float32)); print("wrote", p, S.shape)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "spec": spectrum()
    elif cmd == "plan":
        import yaml
        song = yaml.safe_load(open(os.path.join(HERE, "song.yaml")))
        src = caplayer._Src(os.path.join(HERE, "build", "master_9x16.mp4"))
        avoid = [(c["start"], c["start"] + 3.0, 0.10, float(c.get("hook_y", song.get("hook_y", 0.135))) + 0.17)
                 for c in song.get("clips", []) if c.get("hook")]
        res = caplayer.plan(src, TM.lines, 1080, 1920, skip=CAP_SKIP, ends=CAP_ENDS, avoid=avoid)
        json.dump({str(k): v for k, v in res.items()}, open(PLACE_9x16, "w"), indent=1); print("wrote", PLACE_9x16)
    else: print(__doc__)
