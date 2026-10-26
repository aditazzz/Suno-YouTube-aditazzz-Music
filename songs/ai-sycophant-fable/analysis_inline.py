# Writes analysis.npz (beat and loudness tracks), which render.py loads. Run from this folder: python3 analysis_inline.py <song.wav>
# (in the chat this was an inline script with the audio path written in)
import sys, numpy as np, subprocess, json
WAV = sys.argv[1] if len(sys.argv) > 1 else '/mnt/user-data/uploads/AI_Sycophant__Remastered__4.wav'
sr=22050
raw=subprocess.run(['ffmpeg','-v','error','-i',WAV,'-ac','1','-ar',str(sr),'-f','f32le','-'],capture_output=True).stdout
x=np.frombuffer(raw,np.float32)
hop=512; n=2048
frames=1+(len(x)-n)//hop
win=np.hanning(n)
idx=np.arange(n)[None,:]+hop*np.arange(frames)[:,None]
S=np.abs(np.fft.rfft(x[idx]*win,axis=1))
freqs=np.fft.rfftfreq(n,1/sr)
t=(np.arange(frames)*hop+n/2)/sr
def band(lo,hi): return S[:,(freqs>=lo)&(freqs<hi)].sum(1)
low=band(30,150); mid=band(300,3400); hi=band(5000,11000)
rms=np.sqrt((S**2).mean(1))
flux=np.maximum(0,np.diff(np.log1p(S),axis=0)).sum(1); flux=np.r_[0,flux]
# tempo via autocorr of flux
f=flux-np.convolve(flux,np.ones(43)/43,'same'); f=np.maximum(f,0)
ac=np.correlate(f[:20000],f[:20000],'full')[19999:]
fps=sr/hop
lags=np.arange(len(ac))/fps
bpm_range=(lags>60/140)&(lags<60/80)
best=lags[bpm_range][np.argmax(ac[bpm_range])]
print('bpm est',60/best)
np.savez('analysis.npz',t=t,low=low,mid=mid,hi=hi,rms=rms,flux=flux)
