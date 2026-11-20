"""Render the whole film in parallel chunks, join them frame-exactly, mux the song. Usage: render_all.py <out.mp4> [nproc]"""
import subprocess, sys, os, time
HERE = os.path.dirname(os.path.abspath(__file__))
out = sys.argv[1]
nproc = int(sys.argv[2]) if len(sys.argv) > 2 else 4
N = 7547
CH = 420
chunks = [(a, min(a + CH, N)) for a in range(0, N, CH)]
os.makedirs(os.path.join(HERE, "chunks"), exist_ok=True)
t0 = time.time()
running = []
todo = [c for c in chunks if not os.path.exists(os.path.join(HERE, "chunks", "c_%05d.mp4" % c[0]))]
files = []
for a, b in chunks:
    files.append(os.path.join(HERE, "chunks", "c_%05d.mp4" % a))
while todo or running:
    while todo and len(running) < nproc:
        a, b = todo.pop(0)
        part = os.path.join(HERE, "chunks", "part_%05d.mp4" % a)
        p = subprocess.Popen([sys.executable, os.path.join(HERE, "film.py"), "render", str(a), str(b), part], stdout=subprocess.DEVNULL)
        p.final = (part, os.path.join(HERE, "chunks", "c_%05d.mp4" % a))
        running.append(p)
    for p in list(running):
        if p.poll() is not None:
            if p.returncode != 0:
                print("CHUNK FAILED", p.args); sys.exit(1)
            os.rename(*p.final)
            print("chunk", p.final[1], "%.0fs" % (time.time() - t0), flush=True)
            running.remove(p)
    time.sleep(0.5)
lst = os.path.join(HERE, "chunks", "list.txt")
open(lst, "w").write("".join("file '%s'\n" % f for f in files))
silent = os.path.join(HERE, "chunks", "silent.mp4")
subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", silent])
subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-i", os.path.join(HERE, "source.wav"), "-map", "0:v", "-map", "1:a",
                       "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", out])
for f in files + [silent, lst]:
    os.remove(f)
print("rendered %s in %.0fs" % (out, time.time() - t0))
