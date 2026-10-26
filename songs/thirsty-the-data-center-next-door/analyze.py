"""Audio analysis for Thirsty (The Data Center Next Door), on top of studio.sync's beats/words.

usage: python3 songs/thirsty-the-data-center-next-door/analyze.py
Writes build/analysis.json:
  env_low / env_mid / env_high / env_rms   10 ms envelopes (0..1) for the bass hum, snare, hats, overall loudness
  kicks / snares / onsets                  transient times (s) found on the percussive part
  novelty / boundaries                     structural novelty curve + its peaks (section-change candidates)
  vocal_env                                vocal loudness (from build/vocals16.wav) for the breathing / silence beats
and build/analysis.png, a picture of all of it with the beat grid and lyric lines, for checking by eye.
"""
import os, sys, json
import numpy as np, librosa, scipy.signal as ss

HERE = os.path.dirname(os.path.abspath(__file__)); B = os.path.join(HERE, "build")
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
from studio.config import load_song

HOP = 220                     # 10 ms at 22.05 kHz
SR = 22050

def norm01(x, lo=5, hi=99.5):
    a, b = np.percentile(x, lo), np.percentile(x, hi)
    return np.clip((x - a) / max(1e-9, b - a), 0, 1)

def band_env(S, freqs, f0, f1):
    m = (freqs >= f0) & (freqs < f1)
    return np.sqrt((S[m] ** 2).mean(0))

def peaks(env, t, min_gap, thr):
    d = np.maximum(0, np.diff(env, prepend=env[0]))
    p, _ = ss.find_peaks(d, height=thr, distance=max(1, int(min_gap / 0.01)))
    return [float(t[i]) for i in p]

def main():
    song = load_song(HERE)
    y, _ = librosa.load(song["audio"], sr=SR, mono=True)
    dur = len(y) / SR
    yh, yp = librosa.effects.hpss(y, margin=2.0)
    S = np.abs(librosa.stft(y, n_fft=2048, hop_length=HOP)); Sp = np.abs(librosa.stft(yp, n_fft=2048, hop_length=HOP))
    freqs = librosa.fft_frequencies(sr=SR, n_fft=2048); t = librosa.frames_to_time(np.arange(S.shape[1]), sr=SR, hop_length=HOP)
    low = band_env(S, freqs, 25, 140); mid = band_env(Sp, freqs, 1200, 5000); high = band_env(Sp, freqs, 6000, 11000)
    rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=HOP)[0][:len(t)]
    sm = lambda x, k: np.convolve(x, np.ones(k) / k, mode="same")
    env_low, env_mid, env_high, env_rms = norm01(sm(low, 3)), norm01(sm(mid, 2)), norm01(sm(high, 2)), norm01(sm(rms, 5))
    # transients on the percussive part
    kick_env = norm01(band_env(Sp, freqs, 35, 120)); snare_env = norm01(band_env(Sp, freqs, 1500, 4500))
    kicks = peaks(kick_env, t, 0.18, 0.12); snares = peaks(snare_env, t, 0.18, 0.14)
    o_env = librosa.onset.onset_strength(y=yp, sr=SR, hop_length=HOP)
    onsets = librosa.frames_to_time(librosa.onset.onset_detect(onset_envelope=o_env, sr=SR, hop_length=HOP, backtrack=False), sr=SR, hop_length=HOP).tolist()
    # structure: checkerboard novelty on beat-synchronous chroma + MFCC
    bj = json.load(open(os.path.join(B, "beats.json"))); beats = np.array(bj["beats"])
    hop2 = 512
    C = librosa.feature.chroma_cqt(y=yh, sr=SR, hop_length=hop2); M = librosa.feature.mfcc(y=y, sr=SR, hop_length=hop2, n_mfcc=13)
    bf = librosa.time_to_frames(beats, sr=SR, hop_length=hop2)
    Cs = librosa.util.sync(C, bf, aggregate=np.median); Ms = librosa.util.sync(M, bf)
    F = np.vstack([librosa.util.normalize(Cs, axis=0), librosa.util.normalize(Ms[1:], axis=0)])
    R = np.corrcoef(F.T); R = np.nan_to_num(R)
    k = 16; g = ss.windows.gaussian(2 * k, k / 2); ker = np.outer(g, g) * np.outer(np.r_[-np.ones(k), np.ones(k)], np.r_[-np.ones(k), np.ones(k)])
    nov = np.zeros(R.shape[0])
    for i in range(k, R.shape[0] - k): nov[i] = (R[i - k:i + k, i - k:i + k] * ker).sum()
    nov = norm01(np.maximum(nov, 0), 0, 100)
    bt_times = np.r_[0, beats][:len(nov)]
    bp, _ = ss.find_peaks(nov, height=0.25, distance=12)
    boundaries = [float(bt_times[i]) for i in bp if i < len(bt_times)]
    vocal_env = []
    vp = os.path.join(B, "vocals16.wav")
    if os.path.exists(vp):
        v, vsr = librosa.load(vp, sr=16000)
        vr = librosa.feature.rms(y=v, frame_length=1024, hop_length=160)[0]
        vocal_env = norm01(sm(vr, 5), 2, 99.5)
    out = dict(hop=0.01, duration=dur, env_low=np.round(env_low, 3).tolist(), env_mid=np.round(env_mid, 3).tolist(),
               env_high=np.round(env_high, 3).tolist(), env_rms=np.round(env_rms, 3).tolist(),
               vocal_env=np.round(np.asarray(vocal_env), 3).tolist(), kicks=kicks, snares=snares, onsets=onsets,
               novelty=np.round(nov, 3).tolist(), novelty_t=bt_times.tolist(), boundaries=boundaries, tempo=bj["tempo"])
    json.dump(out, open(os.path.join(B, "analysis.json"), "w"))
    print(f"dur {dur:.2f}s tempo {bj['tempo']:.1f}  kicks {len(kicks)} snares {len(snares)} onsets {len(onsets)}")
    print("novelty boundaries:", " ".join(f"{b:.2f}" for b in boundaries))
    plot(out, beats, np.array(bj["downbeats"]), S, t)

def plot(A, beats, downbeats, S, t):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    lines = json.load(open(os.path.join(B, "timed.json"))) if os.path.exists(os.path.join(B, "timed.json")) else []
    dur = A["duration"]; seg = 75.0; n = int(np.ceil(dur / seg))
    fig, axs = plt.subplots(n, 1, figsize=(30, 6.5 * n))
    tt = np.arange(len(A["env_rms"])) * 0.01
    for i, ax in enumerate(np.atleast_1d(axs)):
        a, b = i * seg, min(dur, (i + 1) * seg)
        m = (tt >= a) & (tt < b)
        ax.plot(tt[m], np.array(A["env_rms"])[m] + 3.3, color="k", lw=0.8)
        ax.plot(tt[m], np.array(A["env_low"])[m] + 2.2, color="tab:blue", lw=0.8)
        ax.plot(tt[m], np.array(A["env_mid"])[m] + 1.1, color="tab:red", lw=0.6)
        if len(A["vocal_env"]):
            tv = np.arange(len(A["vocal_env"])) * 0.01; mv = (tv >= a) & (tv < b)
            ax.fill_between(tv[mv], 0, np.array(A["vocal_env"])[mv], color="tab:green", alpha=0.5)
        nt = np.array(A["novelty_t"]); nv = np.array(A["novelty"]); mn = (nt >= a) & (nt < b)
        ax.plot(nt[mn], nv[mn] * 0.9 + 4.4, color="tab:purple", lw=1.2)
        for x in beats[(beats >= a) & (beats < b)]: ax.axvline(x, color="0.85", lw=0.5, zorder=0)
        for x in downbeats[(downbeats >= a) & (downbeats < b)]: ax.axvline(x, color="0.55", lw=0.9, zorder=0)
        for x in A["boundaries"]:
            if a <= x < b: ax.axvline(x, color="tab:purple", lw=2.0, ls="--")
        for x in A["kicks"]:
            if a <= x < b: ax.plot([x, x], [2.2, 2.0], color="tab:blue", lw=1.5)
        for x in A["snares"]:
            if a <= x < b: ax.plot([x, x], [1.1, 0.9], color="tab:red", lw=1.5)
        for L in lines:
            if a <= L["s"] < b:
                ax.text(L["s"], 5.45, L["text"][:34], fontsize=8, rotation=0, va="bottom", ha="left", color="tab:green")
                ax.axvline(L["s"], ymin=0.0, ymax=0.1, color="tab:green", lw=2)
                for w, wt in zip(L["words"], L["wt"]):
                    ax.text(wt, -0.25, w, fontsize=6.5, rotation=90, va="top", ha="center", color="0.25")
        ax.set_xlim(a, a + seg); ax.set_ylim(-1.3, 6.2); ax.set_xticks(np.arange(np.ceil(a), b, 1.0)); ax.tick_params(labelsize=7)
        ax.grid(False)
    plt.tight_layout(); plt.savefig(os.path.join(B, "analysis.png"), dpi=55); print(os.path.join(B, "analysis.png"))

if __name__ == "__main__":
    main()
