"""Second-opinion word timing for Thirsty (The Data Center Next Door).

studio.sync transcribes the separated vocal stem. Here a few words were missed there (the intro's "You're", the
outro's whispered "And who's paying yours?", ad-lib echoes), so this script:
  1. transcribes the full MIX as well, in two staggered passes (12 s windows, every 5 s),
  2. aligns lyrics.txt against the vocal-stem words and against the mix words separately (studio.sync.align),
  3. merges them word by word: both matched and close -> mean; one matched -> that one; neither -> interpolate
     between the nearest matched neighbours, weighted by syllables,
  4. keeps every "thirsty" the ASR heard that is not a lyric word (the backing echoes) as build/echoes.json.
Writes build/timed.json (the stem-only version is kept as build/timed_stem.json) and prints what changed.

usage: MUSIC_DIR=... python3 songs/thirsty-the-data-center-next-door/sync_fix.py
"""
import os, sys, json, re
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); B = os.path.join(HERE, "build")
ROOT = os.path.dirname(os.path.dirname(HERE)); sys.path.insert(0, ROOT)
from studio.config import load_song, MODELS
from studio.sync import align

norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())

# The intro sings "You're so thirsty" once (thirsty at 10.88 in both passes) and then three backing echoes
# (11.9, 12.8, 13.7); the aligner gave the lyric word the last echo. (line text, word index, time)
FIX = [("You're so thirsty.", 2, 10.88)]

def syl(w):
    w = norm(w)
    return max(1, len(re.findall(r"[aeiouy]+", w)) - (1 if w.endswith("e") and len(w) > 3 else 0))

def transcribe_mix(audio):
    out = os.path.join(B, "words_mix.json")
    if os.path.exists(out): return json.load(open(out))
    import sherpa_onnx, librosa
    d = os.path.join(MODELS, "sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8") + "/"
    r = sherpa_onnx.OfflineRecognizer.from_transducer(encoder=d + "encoder.int8.onnx", decoder=d + "decoder.int8.onnx",
        joiner=d + "joiner.int8.onnx", tokens=d + "tokens.txt", model_type="nemo_transducer", num_threads=os.cpu_count() or 2)
    y, sr = librosa.load(audio, sr=16000, mono=True)
    words = []
    for t0 in np.arange(0, len(y) / sr, 5.0):
        s = r.create_stream(); s.accept_waveform(sr, y[int(t0 * sr):int((t0 + 12) * sr)]); r.decode_stream(s)
        cur, cs = "", None
        for tk, tt in zip(s.result.tokens, s.result.timestamps):
            if tk.startswith("▁") or tk.startswith(" "):
                if cur and 0.6 < cs < 11.4 or (cur and t0 == 0 and cs <= 0.6): words.append((cs + t0, cur))
                cur, cs = tk.lstrip("▁ "), tt
            else:
                if cs is None: cs = tt
                cur += tk
        if cur and cs is not None and cs < 11.4: words.append((cs + t0, cur))
    words.sort(); clean = []
    for w in words:   # the two staggered passes hear most words twice: keep one
        if clean and abs(w[0] - clean[-1][0]) < 0.3 and norm(w[1]) == norm(clean[-1][1]): continue
        clean.append(w)
    json.dump(clean, open(out, "w")); return clean

def matched_times(lines, words):
    ts = set(round(t, 3) for t, _ in words)
    return [[(t if round(t, 3) in ts else None) for t in L["wt"]] for L in lines]

def main():
    song = load_song(HERE)
    stem_words = json.load(open(os.path.join(B, "words.json")))
    mix_words = transcribe_mix(song["audio"])
    lyr = os.path.join(HERE, "lyrics.txt"); al = song.get("aliases", {})
    A, ca = align(stem_words, lyr, al); M, cm = align(mix_words, lyr, al)
    print(f"stem match {ca:.0%}, mix match {cm:.0%}")
    ma, mm = matched_times(A, stem_words), matched_times(M, mix_words)
    flat = []   # (line index, word index, word, time or None)
    for li, L in enumerate(A):
        for wi, w in enumerate(L["words"]):
            a, m = ma[li][wi], mm[li][wi]
            if a is not None and m is not None:
                t = (a + m) / 2 if abs(a - m) < 0.25 else m      # disagree: the mix hears sung words more reliably here
            else:
                t = a if a is not None else m
            flat.append([li, wi, w, t])
    # monotonic: drop matches that go backwards
    last = -1
    for f in flat:
        if f[3] is not None:
            if f[3] <= last + 0.02: f[3] = None
            else: last = f[3]
    known = [i for i, f in enumerate(flat) if f[3] is not None]
    for i, f in enumerate(flat):
        if f[3] is not None: continue
        p = max([k for k in known if k < i], default=None); q = min([k for k in known if k > i], default=None)
        if p is None: f[3] = flat[q][3] - 0.3 * (q - i); continue
        if q is None: f[3] = flat[p][3] + 0.3 * (i - p); continue
        span = [syl(flat[k][2]) for k in range(p, q)]
        f[3] = flat[p][3] + (flat[q][3] - flat[p][3]) * sum(span[:i - p]) / sum(span)
    old = json.load(open(os.path.join(B, "timed.json")))
    if not os.path.exists(os.path.join(B, "timed_stem.json")):
        json.dump(old, open(os.path.join(B, "timed_stem.json"), "w"), indent=0)
    lines = [dict(sec=L["sec"], text=L["text"], words=L["words"]) for L in A]
    for li, wi, w, t in flat: lines[li].setdefault("wt", []).append(float(round(t, 3)))
    for text, wi, t in FIX:   # checked by ear-equivalent: the ASR's own timestamps in both passes
        for L in lines:
            if L["text"] == text: L["wt"][wi] = t
    for L in lines: L["s"] = L["wt"][0]
    for a, b in zip(lines, lines[1:]): a["e"] = min(b["s"], a["wt"][-1] + 1.6)
    lines[-1]["e"] = lines[-1]["wt"][-1] + 2.5
    for L in lines:   # the last word of a line is held: end at least 0.5 s after it starts
        L["e"] = max(L["e"], min(L["wt"][-1] + 0.5, L["e"] + 0.5))
    json.dump(lines, open(os.path.join(B, "timed.json"), "w"), indent=0)
    # backing "thirsty" echoes: heard by either pass, not part of a lyric line
    lyric_t = [t for L in lines for t in L["wt"]]
    echoes = sorted({round(t, 2) for t, w in stem_words + mix_words if norm(w) in ("thirsty", "thirst", "first")
                     and min(abs(np.array(lyric_t) - t)) > 0.3})
    ech = []
    for e in echoes:
        if ech and e - ech[-1] < 0.35: continue
        ech.append(e)
    json.dump(ech, open(os.path.join(B, "echoes.json"), "w"))
    for L, O in zip(lines, old):
        d = [f"{w}:{a:.2f}->{b:.2f}" for w, a, b in zip(L["words"], O["wt"], L["wt"]) if abs(a - b) > 0.12]
        if d: print(f"  {L['sec']:6} {L['text'][:40]:40} " + " ".join(d))
    print("echoes:", ech)

if __name__ == "__main__":
    main()
