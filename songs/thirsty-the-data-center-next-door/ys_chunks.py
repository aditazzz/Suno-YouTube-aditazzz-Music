"""Render this song's 16:9 chunks (--fmt 16x9 | 16x9_1440 | 16x9_4k) over a frame range, forward or backward, in parallel, inside a time budget.
Same chunk files and encoder as `studio.render` (build/chunks_16x9/<first frame>.mp4, written as .part then renamed),
so two machines can split the song (one from the start, one from the end) and `ys_assemble.py` joins them.

  python3 songs/thirsty-the-data-center-next-door/ys_chunks.py --from 0 --to 4200 --jobs 3 --budget 110          # Mac, forward
  python3 songs/thirsty-the-data-center-next-door/ys_chunks.py --from 4200 --to 99999 --order rev --jobs 2          # cloud, backward
  python3 songs/thirsty-the-data-center-next-door/ys_chunks.py --status
"""
import os, sys, time, json, argparse, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
from studio.config import load_song

ap = argparse.ArgumentParser()
ap.add_argument("--from", dest="f0", type=int, default=0); ap.add_argument("--to", dest="f1", type=int, default=10 ** 9)
ap.add_argument("--order", default="fwd", choices=("fwd", "rev")); ap.add_argument("--jobs", type=int, default=2)
ap.add_argument("--budget", type=float, default=None); ap.add_argument("--step", type=int, default=30)
ap.add_argument("--status", action="store_true"); ap.add_argument("--fmt", default="16x9")
a = ap.parse_args()
song = load_song(HERE); b = song["build"]; ch = os.path.join(b, f"chunks_{a.fmt}"); os.makedirs(ch, exist_ok=True)
dur = json.load(open(os.path.join(b, "beats.json")))["duration"] + float(song.get("tail", 0)); N = int(dur * 30)
parts = [(s, min(N, s + a.step)) for s in range(0, N, a.step)]
done = lambda s: os.path.exists(os.path.join(ch, f"{s:06d}.mp4"))
if a.status:
    d = [s for s, _ in parts if done(s)]
    gaps = []; run = None
    for s, _ in parts:
        if not done(s):
            if run is None: run = [s, s]
            run[1] = s
        elif run is not None: gaps.append(tuple(run)); run = None
    if run is not None: gaps.append(tuple(run))
    print(f"{len(d)}/{len(parts)} chunks done (N={N} frames, step {a.step}); missing ranges (first frames): {gaps[:12]}")
    sys.exit()
todo = [(s, c) for s, c in parts if a.f0 <= s < a.f1 and not done(s)]
if a.order == "rev": todo.reverse()
print(f"{len(todo)} chunks to render in [{a.f0}, {min(a.f1, N)}) {a.order}, {a.jobs} jobs", flush=True)
procs = []; t0 = time.time(); n_ok = 0
env = dict(os.environ); env.setdefault("YS_THREADS", "1"); env.setdefault("STUDIO_CHUNK_CRF", "12")
while todo or procs:
    if a.budget and time.time() - t0 > a.budget: todo = []
    while todo and len(procs) < a.jobs:
        s, c = todo.pop(0)
        if done(s): continue
        out = os.path.join(ch, f"{s:06d}.mp4")
        lg = open(os.path.join(ch, f"{s:06d}.log"), "w")
        procs.append((s, subprocess.Popen([sys.executable, "-m", "studio.render", HERE, "--worker", a.fmt, str(s), str(c), out], cwd=ROOT, env=env,
                                          stdout=subprocess.DEVNULL, stderr=lg)))
    time.sleep(0.5)
    for s, p in procs[:]:
        if p.poll() is not None:
            procs.remove((s, p))
            if p.returncode != 0: print(f"chunk {s} failed: {open(os.path.join(ch, f'{s:06d}.log')).read()[-400:]}", flush=True)
            else: n_ok += 1
print(f"rendered {n_ok} chunks in {time.time() - t0:.0f}s", flush=True)
