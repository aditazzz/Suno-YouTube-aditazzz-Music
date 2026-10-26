"""Step 1 — sync: audio + lyrics -> word timings, beats, downbeats, sections.

usage: python -m studio.sync songs/<slug>
needs songs/<slug>/song.yaml (audio:) and songs/<slug>/lyrics.txt
lyrics.txt: section headers on their own line starting with '#', e.g. #V1 #PRE #CH1 #BRIDGE #FINAL #OUTRO
Writes songs/<slug>/build/{mono16.wav,vocals16.wav,words.json,timed.json,beats.json,sections.json}
"""
import os, sys, json, re, difflib, subprocess
import numpy as np
from .config import load_song, MODELS

norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())

def separate(song, b):
    import sherpa_onnx, soundfile as sf, librosa
    out = os.path.join(b, "vocals16.wav")
    if os.path.exists(out): return out
    d = os.path.join(MODELS, "sherpa-onnx-spleeter-2stems-fp16")
    cfg = sherpa_onnx.OfflineSourceSeparationConfig(model=sherpa_onnx.OfflineSourceSeparationModelConfig(
        spleeter=sherpa_onnx.OfflineSourceSeparationSpleeterModelConfig(vocals=f"{d}/vocals.fp16.onnx", accompaniment=f"{d}/accompaniment.fp16.onnx"),
        num_threads=os.cpu_count() or 2))
    sp = sherpa_onnx.OfflineSourceSeparation(cfg)
    y, sr = librosa.load(song["audio"], sr=44100, mono=False)
    if y.ndim == 1: y = np.stack([y, y])
    # chunked (30 s windows, 1 s crossfade) so it fits in ~3 GB of RAM
    W, O = 30 * sr, 1 * sr; n = y.shape[1]; out16 = []; prev_tail = None; a = 0
    while a < n:
        b = min(n, a + W + O)
        res = sp.process(sample_rate=sr, samples=np.ascontiguousarray(y[:, a:b].astype(np.float32)))
        v = np.asarray(res.stems[0].data); v = v.mean(0) if v.ndim == 2 else v
        v = librosa.resample(v, orig_sr=res.sample_rate, target_sr=16000)
        o16 = O * 16000 // sr
        if prev_tail is not None:
            k = min(len(prev_tail), len(v)); r = np.linspace(0, 1, k)
            v[:k] = prev_tail[:k] * (1 - r) + v[:k] * r
        if b < n: prev_tail = v[-o16:].copy(); v = v[:-o16]
        out16.append(v); a += W
        del res
    sf.write(out, np.concatenate(out16), 16000)
    return out

def transcribe(vocals, b):
    import sherpa_onnx, soundfile as sf
    out = os.path.join(b, "words.json")
    if os.path.exists(out): return json.load(open(out))
    d = os.path.join(MODELS, "sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8") + "/"
    r = sherpa_onnx.OfflineRecognizer.from_transducer(encoder=d + "encoder.int8.onnx", decoder=d + "decoder.int8.onnx",
        joiner=d + "joiner.int8.onnx", tokens=d + "tokens.txt", model_type="nemo_transducer", num_threads=os.cpu_count() or 2)
    y, sr = sf.read(vocals, dtype="float32")
    words = []; t = 0.0
    while t < len(y) / sr:
        s = r.create_stream(); s.accept_waveform(sr, y[int(t * sr):int((t + 12) * sr)]); r.decode_stream(s)
        cur, cs = "", None
        for tk, tt in zip(s.result.tokens, s.result.timestamps):
            if tk.startswith("▁") or tk.startswith(" "):
                if cur: words.append((cs + t, cur))
                cur, cs = tk.lstrip("▁ "), tt
            else:
                if cs is None: cs = tt
                cur += tk
        if cur: words.append((cs + t, cur))
        t += 10.0
    words.sort(); clean = []
    for w in words:
        if clean and abs(w[0] - clean[-1][0]) < 0.25 and norm(w[1]) == norm(clean[-1][1]): continue
        clean.append(w)
    json.dump(clean, open(out, "w")); return clean

def align(words, lyrics_path, aliases):
    asr = [(t, norm(x)) for t, x in words if norm(x)]
    lines, sec = [], None
    for l in open(lyrics_path):
        l = l.rstrip("\n")
        if l.startswith('#'): sec = l[1:].strip(); continue
        if l.strip(): lines.append({"sec": sec, "text": l.strip(), "words": l.split()})
    lw = [(li, norm(w)) for li, L in enumerate(lines) for w in L["words"]]
    A = [a for _, a in asr]; B = [b for _, b in lw]; n, m = len(B), len(A)
    def sc(b, a):
        if b == a: return 3
        if a in aliases.get(b, []): return 2
        if len(b) > 2 and len(a) > 2 and difflib.SequenceMatcher(None, a, b).ratio() > 0.7: return 2
        return -1
    D = np.full((n + 1, m + 1), -1e9); D[0, :] = 0; P = np.zeros((n + 1, m + 1), int)
    for i in range(1, n + 1):
        D[i, 0] = D[i - 1, 0] - 1
        for j in range(1, m + 1):
            o = (D[i - 1, j - 1] + sc(B[i - 1], A[j - 1]), D[i - 1, j] - 1, D[i, j - 1] - 0.3)
            k = int(np.argmax(o)); D[i, j] = o[k]; P[i, j] = k
    i, j = n, int(np.argmax(D[n])); T = [None] * n; matched = 0
    while i > 0 and j > 0:
        k = P[i, j]
        if k == 0:
            if sc(B[i - 1], A[j - 1]) > 0: T[i - 1] = asr[j - 1][0]; matched += 1
            i -= 1; j -= 1
        elif k == 1: i -= 1
        else: j -= 1
    idx = [k for k in range(n) if T[k] is not None]
    for k in range(n):
        if T[k] is None:
            p = max([x for x in idx if x < k], default=None); q = min([x for x in idx if x > k], default=None)
            T[k] = T[q] - 0.3 * (q - k) if p is None else T[p] + 0.3 * (k - p) if q is None else T[p] + (T[q] - T[p]) * (k - p) / (q - p)
    k = 0
    for L in lines:
        L["wt"] = [float(x) for x in T[k:k + len(L["words"])]]; k += len(L["words"]); L["s"] = L["wt"][0]
    for a, b2 in zip(lines, lines[1:]): a["e"] = min(b2["s"], a["wt"][-1] + 1.6)
    lines[-1]["e"] = lines[-1]["wt"][-1] + 2.5
    return lines, matched / max(1, n)

def beats(audio, lines, b):
    import librosa
    y, sr = librosa.load(audio, sr=22050, mono=True)
    dur = len(y) / sr
    tempo, bt = librosa.beat.beat_track(y=y, sr=sr); bt = librosa.frames_to_time(bt, sr=sr)
    rms = librosa.feature.rms(y=y, hop_length=2205)[0]
    # downbeat phase: the biggest energy changes (chorus drops, breakdowns) land on beat 1.
    rr = librosa.feature.rms(y=y, hop_length=512)[0]; rt = librosa.frames_to_time(np.arange(len(rr)), sr=sr, hop_length=512)
    e = np.array([rr[(rt >= x) & (rt < z)].mean() if ((rt >= x) & (rt < z)).any() else 0 for x, z in zip(bt[:-1], bt[1:])])
    jump = np.array([abs(e[i:i + 2].mean() - e[i - 2:i].mean()) if 2 <= i < len(e) - 2 else 0 for i in range(len(e))])
    votes = np.bincount([i % 4 for i in np.argsort(-jump)[:16]], minlength=4).astype(float)
    if votes.max() / max(1, votes.sum()) < 0.4:   # weak evidence: add lyric line starts as a second opinion
        for L in lines:
            i = int(np.argmin(abs(bt - L["s"])))
            if abs(bt[i] - L["s"]) < 0.2: votes[i % 4] += 0.5
    ph = int(np.argmax(votes)); db = bt[ph::4]
    json.dump({"tempo": float(np.atleast_1d(tempo)[0]), "beats": bt.tolist(), "downbeats": db.tolist(), "rms": rms.tolist(),
               "duration": dur}, open(os.path.join(b, "beats.json"), "w"))
    return bt, db, dur

def sections(lines, db, dur):
    secs = []
    for L in lines:
        if not secs or secs[-1]["name"] != L["sec"]:
            s = L["s"]; prev = db[db <= s + 0.45]
            start = float(prev[-1]) if len(prev) and s - prev[-1] < 2.6 else s - 0.3
            secs.append({"name": L["sec"], "s": max(0.0, start), "first_line": L["text"], "first_word_t": L["s"]})
    if secs and secs[0]["s"] > 1.0: secs.insert(0, {"name": "INTRO", "s": 0.0, "first_line": "", "first_word_t": secs[0]["s"]})
    for a, b2 in zip(secs, secs[1:]): a["e"] = b2["s"]
    secs[-1]["e"] = dur
    for s in secs: s["kind"] = kind(s["name"])
    return secs

def kind(name):
    n = name.upper()
    for k, pre in (("intro", "INTRO"), ("pre", "PRE"), ("verse", "V"), ("chorus", "CH"), ("chorus", "HOOK"), ("chorus", "FINAL"),
                   ("bridge", "BRIDGE"), ("build", "BUILD"), ("outro", "OUTRO"), ("post", "POST")):
        if n.startswith(pre): return k
    return "other"

def main(song_dir):
    song = load_song(song_dir); b = os.path.join(song_dir, "build"); os.makedirs(b, exist_ok=True)
    print("separating vocals…"); voc = separate(song, b)
    print("transcribing…"); words = transcribe(voc, b)
    lines, cov = align(words, os.path.join(song_dir, "lyrics.txt"), song.get("aliases", {}))
    bt, db, dur = beats(song["audio"], lines, b)
    json.dump(lines, open(os.path.join(b, "timed.json"), "w"), indent=0)
    secs = sections(lines, db, dur); json.dump(secs, open(os.path.join(b, "sections.json"), "w"), indent=1)
    print(f"aligned {len(lines)} lines, word match {cov:.0%}, tempo {json.load(open(os.path.join(b,'beats.json')))['tempo']:.1f}, {dur:.1f}s")
    for s in secs: print(f"  {s['name']:8} {s['s']:7.2f}-{s['e']:7.2f}  {s['first_line'][:50]}")
    if cov < 0.6: print("WARNING: low word match — check lyrics.txt matches the sung version, then review build/timed.json")

if __name__ == "__main__":
    main(sys.argv[1])
