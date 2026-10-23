import librosa, numpy as np, json
y, sr = librosa.load("/mnt/user-data/uploads/Next_Token.wav", sr=22050, mono=True)
tempo, beats = librosa.beat.beat_track(y=y, sr=sr, units="time")
tempo = float(np.atleast_1d(tempo)[0])
rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=512)[0]
t = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=512)
print("tempo", tempo, "nbeats", len(beats), np.round(beats[:6],2), "dur", len(y)/sr)
for a in range(0, 192, 4):
    seg = rms[(t>=a)&(t<a+4)]
    print(f"{a:3d}s {'#'*int(seg.mean()*200)}")
fps=30; n=int(192*fps)
env = np.interp(np.arange(n)/fps, t, rms); env = env/env.max()
# low band energy for kick pulse
S = np.abs(librosa.stft(y, n_fft=2048, hop_length=512))
low = S[:12].mean(axis=0); low = low/low.max()
lowv = np.interp(np.arange(n)/fps, t[:len(low)], low)
json.dump({"tempo":tempo,"beats":[float(b) for b in beats],"env":[round(float(x),3) for x in env],"low":[round(float(x),3) for x in lowv]}, open("nt_beats.json","w"))
