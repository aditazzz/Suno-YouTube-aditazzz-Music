"""Eleven Kept Going: word-time fixes after studio.sync.

The recognizer struggles with the long held notes ("aiming", "dark", "going") and with the soft final refrains, and the
aligner squeezes the three closing "One came home"s together. These times were read off build/words.json, short-window
re-transcription of the separated vocal, and its loudness envelope (see the notes beside each line).

usage (after `python -m studio.sync songs/eleven-kept-going`):  python3 songs/eleven-kept-going/fix_timing.py
Keeps the aligner's output as build/timed_raw.json and rewrites build/timed.json + build/sections.json.
"""
import os, sys, json, shutil
HERE = os.path.dirname(os.path.abspath(__file__)); B = os.path.join(HERE, "build")
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
import numpy as np
from studio import sync

# (section, line text) -> word start times (one per word in lyrics.txt); a list of lists for a line sung more than once
FIX = {
    ("INTRO", "December twenty-first"): [7.2, 7.8],
    ("INTRO", "Twenty-fifteen"): [9.95],
    ("INTRO", "Night"): [15.45],                                   # quiet, almost whispered; heard as "Nine"
    ("REFRAIN", "Eleven kept going"): [114.0, 114.45, 114.7],
    ("TURN", "But this one turned around"): [116.6, 116.85, 117.05, 117.65, 118.05],   # silence 117.2-117.6, band at 118.58
    ("V3", "Grid fins catch the air"): [133.0, 133.76, 134.56, 135.12, 135.36],
    ("V3", "It is aiming"): [152.55, 153.1, 153.45],               # "aiming" is held to ~159
    ("BUILD", "Entry burn"): [159.4, 160.4],
    ("BUILD", "Into the dark"): [181.36, 181.68, 182.2],
    ("PEAK", "Eleven kept going"): [184.9, 186.8, 187.9],
    ("PEAK", "One came home"): [194.65, 195.45, 195.75],           # alone in the gap, right before the hit at 196.56
    ("POST", "It stood there in the smoke"): [222.8, 223.0, 223.6, 223.9, 224.2, 224.5],
    ("POST", "Landing Zone One"): [236.3, 237.0, 237.5],
    ("POST", "Like it had somewhere"): [247.6, 247.9, 248.3, 248.6],
    ("FINAL", "One came home"): [[280.3, 280.9, 281.6], [287.3, 287.9, 288.6], [302.45, 303.2, 303.5]],
}

def main():
    raw = os.path.join(B, "timed_raw.json"); out = os.path.join(B, "timed.json")
    if not os.path.exists(raw) or os.path.getmtime(raw) < os.path.getmtime(os.path.join(B, "words.json")):
        shutil.copyfile(out, raw)
    lines = json.load(open(raw)); used = {}
    for L in lines:
        k = (L["sec"], L["text"])
        if k not in FIX: continue
        wt = FIX[k]
        if isinstance(wt[0], list): wt = wt[used.get(k, 0)]
        assert len(wt) == len(L["words"]), (k, len(wt), len(L["words"]))
        L["wt"] = [float(x) for x in wt]; L["s"] = L["wt"][0]; used[k] = used.get(k, 0) + 1
    missing = set(FIX) - set(used)
    if missing: raise SystemExit(f"fixes that matched no line (lyrics.txt changed?): {sorted(missing)}")
    for a, b in zip(lines, lines[1:]): a["e"] = min(b["s"], a["wt"][-1] + 2.4)    # held notes: captions linger a little longer
    lines[-1]["e"] = lines[-1]["wt"][-1] + 2.5
    json.dump(lines, open(out, "w"), indent=0)
    bt = json.load(open(os.path.join(B, "beats.json")))
    secs = sync.sections(lines, np.array(bt["downbeats"]), bt["duration"])
    json.dump(secs, open(os.path.join(B, "sections.json"), "w"), indent=1)
    for s in secs: print(f"  {s['name']:8} {s['s']:7.2f}-{s['e']:7.2f}  {s['first_line'][:50]}")
    print(f"fixed {sum(used.values())} lines")

if __name__ == "__main__":
    main()
