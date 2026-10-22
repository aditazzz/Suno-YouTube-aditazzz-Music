"""Rebuild build/clips.json from song.yaml + the files already in the output folder (after partial --only runs)."""
import os, sys, json, glob
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from studio.config import load_song
song = load_song(sys.argv[1]); b = song["build"]; T = song["title"]
p = os.path.join(b, "clips.json"); old = json.load(open(p)) if os.path.exists(p) else {}
clips = song.get("clips"); n = {"reel": 0, "short": 0}
for c in clips:
    n[c["kind"]] += 1
    pre = f"{T} - {'Reel' if c['kind'] == 'reel' else 'Short'} {n[c['kind']]} ({c['label']},"
    hit = [f for f in os.listdir(song["out_dir"]) if f.startswith(pre)]
    c["file"] = hit[0] if hit else None
res = {"clips": clips}
ed = [f for f in os.listdir(song["out_dir"]) if "(under 3 min)" in f]
if ed:
    segs = song.get("edit_segments"); res["edit"] = {"file": ed[0], "segments": segs, "duration": sum(e - a for a, e in segs)}
json.dump(res, open(p, "w"), indent=1); print(json.dumps([c["file"] for c in clips]), res.get("edit", {}).get("file"))
