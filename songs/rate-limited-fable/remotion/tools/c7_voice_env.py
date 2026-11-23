#!/usr/bin/env python3
"""The robot's voice envelope for VoicePulse (PLAN7 §2): per film frame (30 fps) RMS of (robot-voice mix - the plain song),
i.e. his voice alone, smoothed (attack 1 f, release 4 f) and normalised to 0..1 (95th pct of the voiced frames = 1).
Out: src/data/c7_voice.json {"fps": 30, "env": [...] (one per frame, 3 decimals)}."""
import json
from pathlib import Path
import numpy as np
from scipy.io import wavfile
P = Path(__file__).resolve().parents[1]
sr, a = wavfile.read(P.parent / 'audio/Rate Limited (robot voice v1).wav')
sr2, b = wavfile.read(P / 'public/song.wav')
assert sr == sr2, (sr, sr2)
def mono(x):
    x = x.astype(np.float64)
    if x.dtype.kind == 'i' or np.abs(x).max() > 2: x /= 32768.0 if np.abs(x).max() < 70000 else 2 ** 31
    return x.mean(axis=1) if x.ndim == 2 else x
a, b = mono(a), mono(b); n = min(len(a), len(b)); r = a[:n] - b[:n]
hop = sr / 30; nf = int(n / hop)
rms = np.array([np.sqrt(np.mean(r[int(i * hop):int((i + 1) * hop)] ** 2)) for i in range(nf)])
db = 20 * np.log10(rms + 1e-9); voiced = db > -45
top = np.percentile(rms[voiced], 95) if voiced.any() else 1.0
env = np.clip(rms / top, 0, 1); env[~voiced] = 0
out = np.zeros_like(env); y = 0.0
for i, x in enumerate(env):
    y = x if x > y else y + (x - y) * 0.25; out[i] = y
on = np.where(out > 0.1)[0]
print(f'{nf} frames; voiced frames {voiced.sum()}; env > 0.1 from {on.min() if len(on) else None} to {on.max() if len(on) else None}')
(P / 'src/data/c7_voice.json').write_text(json.dumps({'fps': 30, 'env': [round(float(v), 3) for v in out]}))
