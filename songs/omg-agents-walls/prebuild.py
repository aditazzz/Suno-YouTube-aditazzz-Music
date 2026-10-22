"""Build cached plates / atlases for the IN THE WALLS scene (run before a parallel render; safe to re-run).
usage: python3 songs/omg-agents-walls/prebuild.py list            # print the jobs
       python3 songs/omg-agents-walls/prebuild.py job <index>     # build one job"""
import os, sys, importlib.util
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT); os.chdir(ROOT)
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("walls_scene", os.path.join(HERE, "scene.py"))
sc = importlib.util.module_from_spec(spec); spec.loader.exec_module(sc)
SIZES = {"16x9": (1920, 1080), "9x16": (1080, 1920)}
GRID_CIDS = ["living", "hallway", "kitchen", "bedroom", "basement", "entry", "attic", "net", "street"]
def tile(W, H, n):
    gap = max(2, W // 480); tw, th = (W - gap * (n - 1)) // n, (H - gap * (n - 1)) // n
    return tw - tw % 2, th - th % 2
JOBS = [("atlas", r, 0, 0) for r in ("living", "hallway", "kitchen", "bedroom", "basement", "entry", "attic")]
for fmt in ("16x9", "9x16"):
    W, H = SIZES[fmt]
    for cid in sc.CAMS: JOBS.append(("plate", cid, W, H))
    for n in (2, 3):
        tw, th = tile(W, H, n)
        for cid in GRID_CIDS: JOBS.append(("plate", cid, tw, th))
if sys.argv[1] == "list":
    print(len(JOBS))
else:
    k = int(sys.argv[2]); kind, cid, W, H = JOBS[k]
    if kind == "atlas": sc.atlas(cid)
    else: sc.plate(cid, W, H)
    print("done", k, kind, cid, W, H, flush=True)
