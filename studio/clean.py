"""Step 0 — clean: take the AI-music hum out of the song before anything is synced to it.

usage: python3 -m studio.clean songs/<slug>            # check, clean if needed, point song.yaml at the clean file
       python3 -m studio.clean songs/<slug> --dry      # only report what it finds
       python3 -m studio.clean songs/<slug> --force    # analyse again, even if the song already has a clean file
studio.sync runs this first, so every song is synced, rendered and cut from the clean audio.

AI music generators can leave steady tones under a whole track that aren't part of the music: a low buzz or rumble, a
whine around 850-900 Hz. tools/enhance_audio.py finds the tones that hold one level all song and sit off the song's
tuning (real notes are left alone) and cuts each with a very narrow zero-phase notch. The music, its loudness, EQ,
dynamics and timing don't change (same length to the sample, so word timings stay valid).

When it finds hum it writes "<Song> (clean).wav" next to the original (the original is never touched), an A/B clip in
the song's build/ folder (12 s of the original, a short gap, then the same 12 s clean), and points song.yaml `audio:`
at the clean file, with the original's name in a comment. To keep a song's original audio: `clean_audio: false`.
"""
import argparse, importlib.util, os, re
import numpy as np
from .config import ROOT, MUSIC_DIR, load_song


def _tool():
    """tools/enhance_audio.py: the analysis and the notches, one implementation for the tool and the pipeline."""
    spec = importlib.util.spec_from_file_location("enhance_audio", os.path.join(ROOT, "tools", "enhance_audio.py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def _point_song_yaml(song_dir, clean_name, original_name, note):
    """Rewrite only the top-level `audio:` line of song.yaml, so every other line and comment stays as it was."""
    p = os.path.join(song_dir, "song.yaml"); txt = open(p, encoding="utf-8").read()
    line = f'audio: "{clean_name}"   # {note}; original: {original_name}'
    new, n = re.subn(r"^audio:.*$", lambda m: line, txt, count=1, flags=re.M)
    if n != 1: raise SystemExit(f"no top-level audio: line in {p}")
    open(p, "w", encoding="utf-8").write(new)


def clean(song_dir, dry=False, force=False):
    """Make sure the song plays from hum-free audio. Returns the audio file the pipeline should use."""
    import soundfile as sf, yaml
    raw = yaml.safe_load(open(os.path.join(song_dir, "song.yaml"), encoding="utf-8"))
    song = load_song(song_dir); src = song["audio"]
    if raw.get("clean_audio") is False:
        print(f"audio: clean_audio is false in song.yaml, keeping {os.path.basename(src)}"); return src
    stem = os.path.splitext(src)[0]
    if stem.endswith("(clean)") and not force:
        print(f"audio: already clean ({os.path.basename(src)})"); return src
    out = stem + " (clean).wav"
    rel = lambda p: p if os.path.isabs(str(raw["audio"])) else os.path.relpath(p, MUSIC_DIR)
    if os.path.exists(out) and not force:
        print(f"audio: {os.path.basename(out)} already exists" + ("" if dry else ", song.yaml now points at it"))
        if dry: return src
        _point_song_yaml(song_dir, rel(out), raw["audio"], "hum-cleaned (studio.clean)")
        return out

    E = _tool()
    x, sr = sf.read(src, always_2d=True); info = sf.info(src); mono = x.mean(1)
    s0 = int((0.07 * len(mono) / sr) * sr); s1 = int((0.98 * len(mono) / sr) * sr)   # the tool's window: no intro, no tail
    seg = mono[s0:s1]
    tune = E.tuning(seg, sr)
    tones = sorted(E.find_tones(seg, sr, tune=tune), key=lambda t: t["f"])
    print(f"audio: {os.path.basename(src)}, tuning {tune:+.0f} cents, {len(tones)} steady off-pitch tone(s)")
    for t in tones:
        print(f"  {t['f']:8.1f} Hz  +{t['prom']:.1f} dB over its neighbours, {t['cents']:.0f} cents off the tuning")
    if not tones:
        print("audio: no hum found, the original stays"); return src
    if dry: return src

    y = E.notch(x, sr, tones)
    peak = np.abs(y).max()
    if peak > 0.999: y = y * (0.999 / peak)
    sf.write(out, y, sr, subtype=info.subtype if info.subtype in ("PCM_16", "PCM_24", "FLOAT") else "PCM_24")
    ym = y.mean(1)[s0:s1]
    print("after:", ", ".join(f"{t['f']:.0f} Hz {t['prom']:+.0f} -> {E.prominence_at(ym, sr, t['f']):+.0f} dB" for t in tones))
    b = os.path.join(song_dir, "build"); os.makedirs(b, exist_ok=True)
    i0, i1 = s0, min(len(mono), s0 + 12 * sr)
    ab = np.concatenate([x[i0:i1], np.zeros((int(0.6 * sr), x.shape[1])), y[i0:i1]])
    sf.write(os.path.join(b, "audio_AB.wav"), ab, sr, subtype="PCM_16")
    hz = " + ".join(f"{t['f']:.0f}" for t in tones)
    _point_song_yaml(song_dir, rel(out), raw["audio"], f"hum notched by studio.clean ({hz} Hz)")
    print(f"wrote {out}\n      {os.path.join(b, 'audio_AB.wav')} (12 s original, then the same 12 s clean)\n"
          f"song.yaml audio: now the clean file")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Take the AI-music hum out of a song's audio (step 0 of the pipeline).")
    ap.add_argument("song_dir"); ap.add_argument("--dry", action="store_true"); ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    clean(a.song_dir, dry=a.dry, force=a.force)
