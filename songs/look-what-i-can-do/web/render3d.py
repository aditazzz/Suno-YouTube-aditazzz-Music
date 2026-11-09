"""Render the 3D stretches of the film in resumable chunks, JOBS at a time.
  python3 render3d.py [W H] [JOBS]     -> build/chunks_3d/<n0>.mp4 for frames 1289-4552 and 4749-5447"""
import os, sys, subprocess, time
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "..", "build", "chunks_3d")
W, H = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (1920, 1080)
JOBS = int(sys.argv[3]) if len(sys.argv) > 3 else 2
RANGES = [(1288, 1288), (1289, 4552), (4749, 5447)]          # inclusive frame ranges at 30 fps (2D: part 1, the breakdown, the end card)
if os.environ.get('RANGES'): RANGES = [tuple(int(x) for x in r.split('-')) for r in os.environ['RANGES'].split(',')]   # e.g. RANGES=1289-2399 (keep ends on chunk boundaries)
STEP = 150
chunks = []
for a, b in RANGES:
    n = a
    while n <= b:
        m = min(b, (n // STEP + 1) * STEP - 1); chunks.append((n, m)); n = m + 1
os.makedirs(OUT, exist_ok=True)
todo = [(a, b) for a, b in chunks if not os.path.exists(os.path.join(OUT, f"{a:05d}.mp4"))]
print(f"{len(chunks)} chunks, {len(todo)} to render at {W}x{H}, {JOBS} at a time", flush=True)
procs = []; t0 = time.time()
while todo or procs:
    while todo and len(procs) < JOBS:
        a, b = todo.pop(0); out = os.path.join(OUT, f"{a:05d}.mp4")
        log = open(os.path.join(OUT, f"{a:05d}.log"), "w")
        p = subprocess.Popen(["node", "render.mjs", "range", str(W), str(H), out, f"{a / 30:.6f}", f"{(b + 1) / 30:.6f}"], cwd=HERE, stdout=log, stderr=subprocess.STDOUT)
        procs.append((p, a, b, log))
    time.sleep(3)
    for item in procs[:]:
        p, a, b, log = item
        if p.poll() is not None:
            procs.remove(item); log.close()
            ok = p.returncode == 0 and os.path.exists(os.path.join(OUT, f"{a:05d}.mp4"))
            print(f"{'done' if ok else 'FAILED'} {a}-{b} ({time.time() - t0:.0f}s)", flush=True)
            if not ok: todo.append((a, b))
print("ALL 3D CHUNKS DONE", flush=True)
