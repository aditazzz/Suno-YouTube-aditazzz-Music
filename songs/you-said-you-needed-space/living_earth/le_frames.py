"""The three Living Earth shots' frame ranges (engine fps 30) from timing/timing_v0.yaml + living_earth/shots.json.
    .venv/bin/python living_earth/le_frames.py [LE1|LE2|LE3]   -> prints `id comp first last`, writes build/living_earth/ranges.json
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); SONG = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(SONG, "timing"))
from timing import load
T = load(); spec = json.load(open(os.path.join(HERE, "shots.json"))); fps = spec["fps"]
out = {}
for k, s in spec["shots"].items():
    a, b = T.at(s["start"]), T.at(s["end"])
    out[k] = dict(comp=s["composition"], first=int(round(a * fps)), last=int(round(b * fps)) - 1, start_s=a, end_s=b, title=s["title"])
os.makedirs(os.path.join(SONG, "build", "living_earth"), exist_ok=True)
json.dump(out, open(os.path.join(SONG, "build", "living_earth", "ranges.json"), "w"), indent=1)
want = sys.argv[1:] or list(out)
for k in want:
    r = out[k]; print(k, r["comp"], r["first"], r["last"])
