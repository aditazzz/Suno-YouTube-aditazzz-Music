"""Re-cut only some clips (by label) and optionally the Instagram edit: python tools/recut.py songs/<slug> "chorus" "the AI's side" [--edit]"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
from studio.config import load_song
from studio import cuts
from studio.render import load_scene
song = load_song(sys.argv[1]); b = song["build"]; labels = [a for a in sys.argv[2:] if a != "--edit"]
vid = os.path.join(b, "video_9x16.mp4"); sc = load_scene(sys.argv[1]); cover = cuts.cover_png(song, sc)
lines = json.load(open(os.path.join(b, "timed.json")))
n = {"reel": 0, "short": 0}
for c in song["clips"]:
    n[c["kind"]] += 1
    if c["kind"] == "short" and c["end"] - c["start"] > cuts.SHORT_MAX: c = dict(c, end=c["start"] + cuts.SHORT_MAX)
    if c["label"] in labels: cuts.make_clip(song, vid, dict(c), n[c["kind"]], cover, sc, lines)
if "--edit" in sys.argv:
    cuts.make_edit(song, vid, sc, [tuple(s) for s in song["edit_segments"]], cover, lines)
