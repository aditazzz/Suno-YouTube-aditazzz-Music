# Run after analysis_inline.py: finds the beat phase that timeline.py hard-codes as PHASE/BEAT (in the chat this was an inline script).
import numpy as np
d=np.load('analysis.npz'); t=d['t']; low=d['low']; flux=d['flux']; mid=d['mid']; rms=d['rms']
fps=1/(t[1]-t[0]); bp=60/106*fps
e=np.maximum(0,np.diff(np.log1p(low),prepend=0)); e=np.maximum(e-np.convolve(e,np.ones(43)/43,'same'),0)
sc=[]
for o in np.arange(0,bp,0.25):
    idx=(o+np.arange(int((len(e)-o)/bp))*bp).astype(int); sc.append((e[idx].mean(),o))
s,o=max(sc); phase=o/fps
# refine with sub-frame: t index to time
phase_t=np.interp(o,np.arange(len(t)),t)
print('phase',phase_t, 'beat',60/106)
# bar accent
B=60/106
bt=phase_t+np.arange(0,int(259/B))*B
acc=[np.mean([np.interp(b,t,low) for b in bt[k::4]]) for k in range(4)]
print('beat-in-bar low energy',acc)
np.save('beat.npy',np.array([phase_t,B]))
# print loudness per 0.5s
m=np.log10(mid+1e-9); r=20*np.log10(rms+1e-9)
for a in np.arange(0,259.2,1.0):
    sel=(t>=a)&(t<a+1)
    print(f"{a:5.0f} rms {r[sel].mean():6.1f} mid {m[sel].mean():5.2f} low {np.log10(low[sel].mean()+1e-9):5.2f}")
