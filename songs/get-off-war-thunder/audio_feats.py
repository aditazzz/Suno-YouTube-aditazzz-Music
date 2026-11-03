# Beat grid and energy for render.py. In the chat this ran as an inline script; it's saved here as a file.
# Run in this folder after: ffmpeg -v error -y -i song.wav -ac 1 -ar 16000 song16k.wav
# Writes audio_feats.json (bpm, phase, per-30fps-frame normalized RMS) that render.py loads.
# tempo + energy envelope
import wave, numpy as np, json
with wave.open("song16k.wav") as f:
    sr=f.getframerate(); x=np.frombuffer(f.readframes(f.getnframes()),dtype=np.int16).astype(np.float32)/32768
hop=512; n=len(x)//hop
# spectral flux onset envelope
win=1024
spec_prev=None; flux=[]
for i in range(n):
    seg=x[i*hop:i*hop+win]
    if len(seg)<win: seg=np.pad(seg,(0,win-len(seg)))
    S=np.abs(np.fft.rfft(seg*np.hanning(win)))
    if spec_prev is not None: flux.append(np.sum(np.maximum(S-spec_prev,0)))
    else: flux.append(0)
    spec_prev=S
flux=np.array(flux); flux-=flux.mean()
fps_env=sr/hop
ac=np.correlate(flux,flux,'full')[len(flux)-1:]
best=None
for bpm in np.arange(100,200,0.25):
    lag=60/bpm*fps_env
    l0=int(round(lag)); v=ac[l0]+0.5*ac[int(round(2*lag))]
    if best is None or v>best[1]: best=(bpm,v)
print("bpm", best[0])
# find beat phase: pick offset maximizing flux sum on grid over first 30s using chosen bpm
bpm=best[0]; period=60/bpm
bestph=None
for ph in np.arange(0,period,0.005):
    t=np.arange(ph,120.5,period); idx=(t*fps_env).astype(int); idx=idx[idx<len(flux)]
    v=flux[idx].sum()
    if bestph is None or v>bestph[1]: bestph=(ph,v)
print("phase",bestph[0])
# RMS energy per video frame (30fps)
fps=30; frames=int(np.ceil(len(x)/sr*fps)); rms=[]
for i in range(frames):
    seg=x[int(i*sr/fps):int((i+1)*sr/fps)]
    rms.append(float(np.sqrt(np.mean(seg**2))) if len(seg) else 0.0)
rms=np.array(rms); rms/=rms.max()
json.dump({"bpm":float(bpm),"phase":float(bestph[0]),"rms":[round(float(v),3) for v in rms]},open("audio_feats.json","w"))
# print section energies
for a,b in [(0,2.8),(2.8,9.5),(9.6,27.5),(28,44),(46,64.5),(65,77.5),(77.6,92),(92.8,107.5),(108,120.5)]:
    print(a,b, round(float(rms[int(a*fps):int(b*fps)].mean()),3))
