import numpy as np, subprocess, sys
wav, out = sys.argv[1], sys.argv[2]
sr=22050
x=np.frombuffer(subprocess.run(['ffmpeg','-v','error','-i',wav,'-ac','1','-ar',str(sr),'-f','f32le','-'],capture_output=True).stdout,np.float32)
hop=512; n=2048
frames=1+(len(x)-n)//hop
win=np.hanning(n)
S=np.empty((frames,n//2+1),np.float32)
for s in range(0,frames,4000):
    e=min(frames,s+4000)
    idx=np.arange(n)[None,:]+hop*np.arange(s,e)[:,None]
    S[s:e]=np.abs(np.fft.rfft(x[idx]*win,axis=1))
freqs=np.fft.rfftfreq(n,1/sr)
t=(np.arange(frames)*hop+n/2)/sr
band=lambda lo,hi: S[:,(freqs>=lo)&(freqs<hi)].sum(1)
low=band(30,150); mid=band(300,3400); rms=np.sqrt((S**2).mean(1))
flux=np.r_[0,np.maximum(0,np.diff(np.log1p(S),axis=0)).sum(1)]
fps=sr/hop
e=np.maximum(0,np.diff(np.log1p(low),prepend=0)); e=np.maximum(e-np.convolve(e,np.ones(43)/43,'same'),0)
best=[]
for bpm in np.arange(70,180,0.1):
    p=60/bpm*fps
    sc=max(e[np.clip((np.arange(int(len(e)/p))*p+o).astype(int),0,len(e)-1)].mean() for o in np.arange(0,p,2))
    best.append((sc,bpm))
best.sort(reverse=True)
bpm=best[0][1]; p=60/bpm*fps
sc=[(e[(o+np.arange(int((len(e)-o)/p))*p).astype(int)].mean(),o) for o in np.arange(0,p,0.25)]
o=max(sc)[1]; phase=np.interp(o,np.arange(len(t)),t)
print('bpm candidates',[(round(b,1),round(s,3)) for s,b in best[:6]],'phase',phase)
np.savez(out,t=t,low=low,mid=mid,rms=rms,flux=flux,bpm=bpm,phase=phase)
r=20*np.log10(rms+1e-9)
print(' '.join(f"{a}:{r[(t>=a)&(t<a+1)].mean():.0f}" for a in range(0,int(t[-1]))))
