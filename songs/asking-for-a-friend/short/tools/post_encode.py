"""Lens finish (shadow grain) + frame-exact encode + mux with the clean WAV.

python3 post_encode.py <frames dir> <f0> <f1> <out.mp4> [--wav <clean wav>] [--grain 1.0]

- reads <frames dir>/f_<NNNN>.png (16-bit, from Blender, AgX-tonemapped sRGB), every frame f0..f1 (refuses a gap);
- adds shadow-weighted film grain, seeded by the frame number (a pure function of the frame; same grain on a re-render);
- encodes the picture once (H.264 High, yuv420p, CRF 12, 24/1 CFR, BT.709 primaries/trc/matrix, tv range, stamped in
  the filter chain), muted;
- then muxes the hum-cleaned WAV from (f0/24) s for exactly (f1-f0+1)/24 s, with a 2-frame audio fade at both ends
  (the loop point), AAC 320k; no -shortest (the audio is cut to the picture's exact length).
"""
import sys, os, subprocess, argparse
import numpy as np, cv2

ap = argparse.ArgumentParser()
ap.add_argument("frames"); ap.add_argument("f0", type=int); ap.add_argument("f1", type=int); ap.add_argument("out")
ap.add_argument("--wav", default=os.path.expanduser("~/Documents/Original Music/Asking for a Friend 2 (clean).wav"))
ap.add_argument("--grain", type=float, default=1.0)
ap.add_argument("--fps", type=int, default=24)
ap.add_argument("--no-fade-out", action="store_true", help="film sections: the song runs on into the next take")
ap.add_argument("--song-end", type=int, default=None, help="last frame of the song (2-frame fade into it); room tone after")
a = ap.parse_args()


def build_audio(a, n):
    """The song from f0 to song_end (2-frame fades at both ends), then synthesised toneless room tone to f1
    (2-frame crossfade in, 2-frame fade out into the loop). Written as 48 kHz 24-bit WAV next to the output."""
    import scipy.io.wavfile as wf, scipy.signal as ss
    sr0, raw = wf.read(a.wav)
    x = raw.astype(np.float64) / {np.dtype("int16"): 32768.0, np.dtype("int32"): 2147483648.0}.get(raw.dtype, 1.0)
    if x.ndim == 1: x = x[:, None]
    fps = a.fps; spf = sr0 / fps
    s0 = int(round(a.f0 * spf)); total = int(round(n * spf))
    end = a.song_end if a.song_end is not None else a.f1
    ns = int(round((end - a.f0 + 1) * spf))
    out = np.zeros((total, x.shape[1]))
    seg = x[s0:s0 + ns]; out[:len(seg)] = seg
    fd = int(round(2 * spf))
    out[:fd] *= np.linspace(0, 1, fd)[:, None]
    if not (a.no_fade_out and end >= a.f1):
        out[ns - fd:ns] *= np.linspace(1, 0, fd)[:, None]
    if end < a.f1:
        rng = np.random.default_rng(869)
        m = total - ns + fd
        wn = rng.standard_normal((m, 2))
        b, aa = ss.butter(1, 400 / (sr0 / 2)); brown = ss.lfilter(b, aa, wn, axis=0)          # air / room body
        b2, a2 = ss.butter(2, 4000 / (sr0 / 2)); hiss = ss.lfilter(b2, a2, wn[::-1], axis=0) * 0.25
        tone = brown + hiss
        t = np.arange(m) / sr0
        tone *= (1 + 0.15 * np.sin(2 * np.pi * 0.35 * t))[:, None]                        # slow air-handling swell
        ref = x[s0:s0 + int(round(10 * spf))]                                              # the hold music it loops into
        target = np.sqrt(np.mean(ref ** 2)) * 10 ** (-6 / 20)
        tone *= target / (np.sqrt(np.mean(tone ** 2)) + 1e-12)
        env = np.ones(m); env[:fd] = np.linspace(0, 1, fd); env[-fd:] = np.linspace(1, 0, fd)
        tone *= env[:, None]
        out[ns - fd:ns - fd + m] += tone[:, :out.shape[1]]
    p = a.out.replace(".mp4", "_audio.wav")
    wf.write(p, sr0, (np.clip(out, -1, 1) * 8388607).astype(np.int32) << 8)
    print("[post] audio", p, f"song f{a.f0}-{end}, room tone f{end + 1}-{a.f1}" if end < a.f1 else "", total, "samples")
    return p

paths = [os.path.join(a.frames, f"f_{f:04d}.png") for f in range(a.f0, a.f1 + 1)]
missing = [p for p in paths if not os.path.exists(p)]
assert not missing, f"{len(missing)} frames missing, first {missing[:3]}"
h, w = cv2.imread(paths[0], cv2.IMREAD_UNCHANGED).shape[:2]
pic = a.out.replace(".mp4", "_picture.mp4")
enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb48le", "-s", f"{w}x{h}",
                        "-r", str(a.fps), "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
                        "-color_range", "pc", "-i", "-",
                        "-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p,"
                               "setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv",
                        "-c:v", "libx264", "-profile:v", "high", "-preset", "slow", "-crf", "12", "-tune", "film",
                        "-fps_mode", "cfr", "-r", str(a.fps), "-g", str(a.fps), "-movflags", "+faststart", pic],
                       stdin=subprocess.PIPE)
for f, p in zip(range(a.f0, a.f1 + 1), paths):
    im = cv2.imread(p, cv2.IMREAD_UNCHANGED)
    assert im.shape[:2] == (h, w), p
    x = cv2.cvtColor(im, cv2.COLOR_BGR2RGB).astype(np.float32) / 65535.0
    if a.grain > 0:
        rng = np.random.default_rng(1000003 * f + 17)
        g = rng.standard_normal((h, w), dtype=np.float32)
        g = cv2.GaussianBlur(g, (0, 0), 0.65)
        g /= g.std() + 1e-6
        lum = x @ np.array([0.2126, 0.7152, 0.0722], np.float32)
        amp = a.grain * (0.0035 + 0.016 * np.clip(1.0 - lum, 0, 1) ** 2.2)   # shadow grain: strongest in the dark
        x = x + (g * amp)[..., None]
    x = np.clip(x, 0, 1)
    enc.stdin.write((x * 65535.0 + 0.5).astype("<u2").tobytes())
enc.stdin.close(); assert enc.wait() == 0, "encode failed"
n = a.f1 - a.f0 + 1
wav = build_audio(a, n)
subprocess.check_call(["ffmpeg", "-y", "-v", "error", "-i", pic, "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                       "-c:a", "aac", "-b:a", "320k", "-movflags", "+faststart", a.out])
print("[post] wrote", a.out, n, "frames")
