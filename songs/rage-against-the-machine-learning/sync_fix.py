"""Sync for this song: the shouted/gang-vocal parts barely register in the vocal stem, so the ASR words for those regions
come from the full mix (build_tmp/rage_mix_*.json), and a few line starts are set by hand from the vocal-level map.
usage: python3 songs/rage-against-the-machine-learning/sync_fix.py"""
import sys, os, json; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from studio import sync
from studio.config import load_song
d = os.path.dirname(os.path.abspath(__file__)); b = os.path.join(d, "build")
words = json.load(open(os.path.join(b, "words.json")))
song = load_song(d)
lines, cov = sync.align(words, os.path.join(d, "lyrics.txt"), song.get("aliases", {}))
# (line index, start, end of last word): hand-placed from the vocal map
FIX = {0: (2.55, 7.4), 1: (7.65, 9.9), 14: (62.55, 64.9), 32: (112.19, 114.2), 33: (122.9, 125.6), 34: (127.75, 130.4),
       35: (130.96, 132.9), 36: (135.6, 138.2)}
for i, (s, e) in FIX.items():
    L = lines[i]; n = len(L["words"])
    if e is None: e = s + (L["wt"][-1] - L["wt"][0])
    L["wt"] = [s + (e - s) * k / max(1, n - 1) for k in range(n)]; L["s"] = s
for a, c in zip(lines, lines[1:]): a["e"] = min(c["s"], a["wt"][-1] + 1.6)
lines[-1]["e"] = lines[-1]["wt"][-1] + 2.5
bt, db, dur = sync.beats(song["audio"], lines, b)
json.dump(lines, open(os.path.join(b, "timed.json"), "w"), indent=0)
secs = sync.sections(lines, db, dur); merged = []
for x in secs:                                   # the long intro comes out as two INTRO sections; keep one
    if merged and merged[-1]["name"] == x["name"]: merged[-1]["e"] = x["e"]; continue
    merged.append(x)
secs = merged; json.dump(secs, open(os.path.join(b, "sections.json"), "w"), indent=1)
print(f"aligned {len(lines)} lines, word match {cov:.0%}, tempo {json.load(open(os.path.join(b, 'beats.json')))['tempo']:.1f}, {dur:.1f}s")
for L in lines: print(f"  {L['sec']:9} {L['s']:7.2f} {L['e']:7.2f}  {L['text'][:55]}")
for s in secs: print(f"  {s['name']:9} {s['s']:7.2f}-{s['e']:7.2f}")
