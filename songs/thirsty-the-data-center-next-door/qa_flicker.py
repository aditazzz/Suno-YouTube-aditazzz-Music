"""QA: luminance flicker scan of a rendered video against the shot list.
Flags (a) frame-to-frame jumps in mean luminance that are not at a cut, (b) strobing: luminance that alternates
up/down many times within half a second. python3 qa_flicker.py <video.mp4>"""
import os, sys, json, subprocess
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
vid = sys.argv[1]
W, H = 192, 108
p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", vid, "-vf", f"scale={W}:{H}", "-f", "rawvideo", "-pix_fmt", "gray", "-"], stdout=subprocess.PIPE)
lum = []; band = []
while True:
    b = p.stdout.read(W * H)
    if len(b) < W * H: break
    f = np.frombuffer(b, np.uint8).reshape(H, W).astype(np.float32)
    lum.append(f[14:94].mean()); band.append(f[14:94])
lum = np.array(lum)
tl = json.load(open(os.path.join(HERE, "build", "timeline.json")))
cuts = np.array([s["start"] for s in tl["shots"]])
fi = np.arange(len(lum)); t = fi / 30.0
near_cut = np.min(np.abs(t[:, None] - cuts[None, :]), axis=1) < 0.07
d = np.abs(np.diff(lum))
flag = np.nonzero((d > 6.0) & ~near_cut[1:])[0]
print(f"{len(lum)} frames, mean luminance {lum.mean():.1f}, {len(cuts)} shots")
print("jumps > 6 levels not at a cut:", [(round(float(t[i + 1]), 2), round(float(d[i]), 1)) for i in flag[:40]])
# strobing: count sign changes of the luminance derivative over 15-frame windows (ignoring tiny wiggles)
dd = np.diff(lum); s = np.sign(np.where(np.abs(dd) > 0.8, dd, 0))
strobe = []
for i in range(0, len(s) - 15):
    w = s[i:i + 15]; w = w[w != 0]
    if len(w) > 6 and (np.diff(w) != 0).sum() >= 6: strobe.append(round(float(t[i]), 2))
print("strobe-like windows:", strobe[:40] if strobe else "none")
# per-pixel temporal noise in static shots is grain (expected); report the 95th percentile of frame diffs for info
pd = [float(np.percentile(np.abs(band[i + 1] - band[i]), 95)) for i in range(0, len(band) - 1, 30)]
print("p95 per-pixel frame diff (every second):", round(float(np.median(pd)), 1), "median,", round(float(np.max(pd)), 1), "max")
