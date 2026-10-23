# studio-early: the engine before the engine

The channel's first week (October 10–13, 2026) was five videos made one chat at a time, before [`studio/`](../studio)
existed. [LGTM](../songs/lgtm) and [Next Token](../songs/next-token) are standalone programs. The three Fable videos
grew a small shared engine: [AI Sycophant](../songs/ai-sycophant-fable) was self-contained, and its line-drawing
helpers and faces (`lib.py`, `face.py`) became the base that [Graceful Shutdown](../songs/graceful-shutdown-fable)
and [Merge Conflict](../songs/merge-conflict) were drawn with. This folder is that engine, kept as it ran.

Everything here draws thin lines with [skia-python](https://pypi.org/project/skia-python/) on a black canvas. The
ideas that survived into `studio/` are all here in miniature: a scene file per song with a `SECTIONS` table and a
beat grid, beat and loudness features from the audio, stills for review, chunked renders in both aspect ratios, and one
script that joins the chunks, muxes the audio and cuts the Shorts and Reels.

## Files

| File | Lines | What it is |
|---|---:|---|
| [`render.py`](render.py) | 228 | `python3 render.py <song folder> still` / `vstill` / `range` / `vrange` / `both`: loads the song's `scenes.py` and `analysis.npz`, renders 16:9 / 9:16 stills to `<song folder>/stills/`, or frame ranges to an mp4 (`both` renders the two aspect ratios in one pass). |
| [`kit.py`](kit.py) | 136 | Drawing helpers shared by the scenes (labels, typed text, windows, cards), on top of `songs/ai-sycophant-fable/lib.py`. |
| [`analyze.py`](analyze.py) | 32 | `python3 analyze.py song.wav analysis.npz`: spectral bands, loudness, onset flux, a BPM and beat-phase estimate. |
| [`drive.sh`](drive.sh) | 17 | `drive.sh <song folder> <worker> <workers> <frames>`: resumable 300-frame chunks, 16:9 then 9:16. |
| [`drive_both.sh`](drive_both.sh) | 16 | The same, rendering both aspect ratios per frame. |
| [`assemble.py`](assemble.py) | 25 | `assemble.py <song folder> song.wav <end seconds> "<title>" '<clips json>'`: concatenates the chunks, pads and muxes the audio, writes the YouTube 16:9 and Instagram 9:16 files and cuts the clips. |
| [`thumbs.py`](thumbs.py) | 50 | The YouTube thumbnails for Graceful Shutdown and Merge Conflict (`python3 thumbs.py gs` for the first only). |
| [`sheet.py`](sheet.py) | 12 | A contact sheet of stills, for review. |
| [`asr/asrw.mjs`](asr/asrw.mjs), [`asr/asr.mjs`](asr/asr.mjs) | 22 | Word-level (and segment-level) transcription with Whisper small, running locally through transformers.js. The word times were the starting point for the lyric timings in each `scenes.py`. |

## Running it

```bash
pip install numpy skia-python fonttools brotli
```

The absolute paths the chats used (`/home/claude/common`, `/home/claude/syco`, `/home/claude/fonts`) were replaced by
paths relative to the repo, each marked with a comment, so this runs from a clone as is. Fonts go in `studio-early/fonts/`
(or point `EARLY_FONTS` at a folder): `lib.py` wants `cormorant-garamond-latin-300-italic.ttf`,
`cormorant-garamond-latin-500-italic.ttf`, `cormorant-garamond-latin-300-normal.ttf`, `jetbrains-mono-latin-300-normal.ttf`
and `jetbrains-mono-latin-400-normal.ttf`, made from the `@fontsource` packages:

```bash
mkdir -p studio-early/fonts && cd studio-early/fonts
npm install --ignore-scripts @fontsource/cormorant-garamond @fontsource/jetbrains-mono
python3 - <<'EOF'
from fontTools.ttLib import TTFont
for fam, files in {"cormorant-garamond": ["latin-300-italic", "latin-300-normal", "latin-500-italic"],
                   "jetbrains-mono": ["latin-300-normal", "latin-400-normal"]}.items():
    for f in files:
        t = TTFont(f"node_modules/@fontsource/{fam}/files/{fam}-{f}.woff2"); t.flavor = None; t.save(f"{fam}-{f}.ttf")
EOF
```

Then, from the repo root, with the song's audio:

```bash
python3 studio-early/analyze.py "Merge Conflict.wav" songs/merge-conflict/analysis.npz
python3 studio-early/render.py songs/merge-conflict still 5 20 24 80 150 200
```

For the transcription helper: `cd studio-early/asr && npm install --ignore-scripts sts-whisper-small @huggingface/transformers`,
then `ffmpeg -i song.wav -ac 1 -ar 16000 -f f32le full.f32 && node asrw.mjs full.f32 words.json`.

Each song's `NOTES.md` has the exact commands that produced its video.
