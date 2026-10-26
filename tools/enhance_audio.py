"""Remove the steady hum/whine that AI music generators (Suno etc.) leave under a track.

What it targets: narrow tones that sit under the whole song at a near-constant level and are NOT musical notes
(off the song's tuning by 20+ cents), e.g. a ~50 Hz buzz and its overtones, or a whine around 800-900 Hz.
It measures them, then cuts each one with a very narrow zero-phase notch, so the music around them is untouched.
It never overwrites the original and does not change loudness, EQ or dynamics.

  python3 tools/enhance_audio.py "music/<Song>.wav"                              # analyse + write "<Song> (clean).wav"
  python3 tools/enhance_audio.py song.wav --dry                                 # analyse only, print what it would cut
  python3 tools/enhance_audio.py song.wav --preview 0:12                        # also write an A/B clip: 12 s before, 12 s after
Options: --min-prom 5 (dB a tone must stand out by), --max-cents 20 (tones closer than this to a real note are kept
unless --drones), --hp 0 (optional high-pass in Hz for sub-rumble), --start/--end (seconds used for analysis).
"""
import os, sys, argparse, math
import numpy as np, soundfile as sf, scipy.signal as ss


def cents_off(f, ref=440.0):
    n = 12 * math.log2(f / ref); return abs(n - round(n)) * 100


def tuning(mono, sr):
    """Song tuning offset in cents, from the strongest peaks (no librosa needed)."""
    f, P = ss.welch(mono, sr, nperseg=1 << 15)
    pk, _ = ss.find_peaks(10 * np.log10(P + 1e-20), prominence=10)
    pk = [i for i in pk if 80 < f[i] < 2000]
    if not pk: return 0.0
    devs = []
    for i in pk:
        n = 12 * math.log2(f[i] / 440.0); devs.append((n - round(n)) * 100)
    return float(np.median(devs))


def find_tones(mono, sr, min_prom=5.0, max_cents=20.0, drones=False, tune=0.0):
    n = 1 << 18
    f, P = ss.welch(mono, sr, nperseg=n, noverlap=n // 2)
    Pd = 10 * np.log10(P + 1e-22); df = f[1]
    # stationarity: how much each frequency's level moves over time
    fs_, ts_, Z = ss.stft(mono, sr, nperseg=16384, noverlap=8192)
    A = 20 * np.log10(np.abs(Z) + 1e-9); std = A.std(1)
    base = ss.medfilt(Pd, int(24 / df) | 1)
    pk, props = ss.find_peaks(Pd - base, prominence=min_prom, width=(None, max(3, int(6 / df))))
    tones = []
    for i in pk:
        fr = f[i]
        if fr < 25 or fr > 16000: continue
        a, b, c = Pd[i - 1], Pd[i], Pd[i + 1]; fr = (i + 0.5 * (a - c) / (a - 2 * b + c)) * df
        prom = float(Pd[i] - base[i])
        j = int(np.argmin(np.abs(fs_ - fr)))
        steady = float(std[max(0, j - 1):j + 2].min())
        nb_std = float(np.median(np.r_[std[max(0, j - 12):max(0, j - 3)], std[j + 3:j + 12]]))
        off = cents_off(fr, 440.0 * 2 ** (tune / 1200))
        musical = off < max_cents
        if steady > nb_std * 0.75 and not drones: continue          # moves like music, not a hum
        if musical and not drones: continue
        tones.append(dict(f=fr, prom=prom, cents=off, steady=steady, nb=nb_std))
    return tones


def notch(x, sr, tones):
    y = x.copy()
    for t in tones:
        bw = max(1.2, t['f'] * 0.0035)
        b, a = ss.iirnotch(t['f'], t['f'] / bw, fs=sr)
        y = ss.filtfilt(b, a, y, axis=0)
    return y


def prominence_at(mono, sr, fr):
    n = 1 << 18; f, P = ss.welch(mono, sr, nperseg=n, noverlap=n // 2); Pd = 10 * np.log10(P + 1e-22); df = f[1]
    i = int(round(fr / df)); w = max(1, int(1 / df))
    nb = np.median(np.r_[Pd[i - int(12 / df):i - int(3 / df)], Pd[i + int(3 / df):i + int(12 / df)]])
    return float(Pd[i - w:i + w + 1].max() - nb)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("wav"); ap.add_argument("--out"); ap.add_argument("--dry", action="store_true")
    ap.add_argument("--min-prom", type=float, default=5.0); ap.add_argument("--max-cents", type=float, default=20.0)
    ap.add_argument("--drones", action="store_true"); ap.add_argument("--hp", type=float, default=0.0)
    ap.add_argument("--start", type=float, default=None); ap.add_argument("--end", type=float, default=None)
    ap.add_argument("--preview", default=None, help="start:seconds for an A/B clip, e.g. 0:12")
    a = ap.parse_args()
    x, sr = sf.read(a.wav, always_2d=True); info = sf.info(a.wav)
    mono = x.mean(1)
    s0 = int((a.start if a.start is not None else 0.07 * len(mono) / sr) * sr)
    s1 = int((a.end if a.end is not None else 0.98 * len(mono) / sr) * sr)
    seg = mono[s0:s1]
    tune = tuning(seg, sr)
    tones = find_tones(seg, sr, a.min_prom, a.max_cents, a.drones, tune)
    print(f"{os.path.basename(a.wav)}: {sr} Hz, tuning {tune:+.0f} cents, {len(tones)} steady off-pitch tone(s)")
    for t in sorted(tones, key=lambda t: t['f']):
        print(f"  {t['f']:8.1f} Hz  +{t['prom']:.1f} dB over neighbours  {t['cents']:.0f} cents off-pitch  "
              f"level wobble {t['steady']:.1f} dB (music around it {t['nb']:.1f})")
    if a.dry or not tones: return
    y = notch(x, sr, tones)
    if a.hp > 0:
        b, c = ss.butter(2, a.hp, btype="high", fs=sr); y = ss.filtfilt(b, c, y, axis=0)
    peak = np.abs(y).max()
    if peak > 0.999: y = y * (0.999 / peak)
    out = a.out or os.path.splitext(a.wav)[0] + " (clean).wav"
    sf.write(out, y, sr, subtype=info.subtype if info.subtype in ("PCM_16", "PCM_24", "FLOAT") else "PCM_24")
    ym = y.mean(1)[s0:s1]
    print("after:", ", ".join(f"{t['f']:.0f} Hz {t['prom']:+.0f}->{prominence_at(ym, sr, t['f']):+.0f} dB" for t in sorted(tones, key=lambda t: t['f'])))
    print("wrote", out)
    if a.preview:
        st, du = (float(v) for v in a.preview.split(":"))
        i0, i1 = int(st * sr), int((st + du) * sr); gap = np.zeros((int(0.6 * sr), x.shape[1]))
        ab = np.concatenate([x[i0:i1], gap, y[i0:i1]])
        p = os.path.splitext(a.wav)[0] + f" (A-B {int(st)}s, original then clean).wav"
        sf.write(p, ab, sr, subtype="PCM_16"); print("wrote", p)


if __name__ == "__main__":
    main()
