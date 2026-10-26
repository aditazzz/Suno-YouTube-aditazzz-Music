# Merge Conflict: how it was made

This video was made on October 12–13, 2026, in one chat with Claude Fable 5.1, with the small engine that came before
`studio/`: [`studio-early/`](../../studio-early). The code here is the code that rendered the published video,
recovered from that chat. The only change is that the absolute paths the chat used (`/home/claude/common`,
`/home/claude/syco`, `/home/claude/fonts`) are now relative to the repo; each one is marked with a comment.

## Files

| File | What it is |
|---|---|
| `scenes.py` | Every section of the video, drawn with skia through `studio-early/kit.py`. It imports the two faces and the line helpers from [`../ai-sycophant-fable/`](../ai-sycophant-fable) (`face.py`, `lib.py`), which were written a day earlier for the first Fable video. `SECTIONS`, `BPM` and `PHASE` (the beat grid) are at the top; the word timings are inside each section. |

The renderer, the chunked render driver, the thumbnail and the assembly script are in `studio-early/`.

## What isn't in the repo

- `analysis.npz`: beat and loudness tracks made from the song with `studio-early/analyze.py`.
- The word timings came from a local Whisper pass (`studio-early/asr/asrw.mjs`) and were then written into `scenes.py`,
  so the transcript itself isn't needed.
- The fonts (see [`studio-early/README.md`](../../studio-early/README.md)) and the audio (`Merge Conflict.wav`).

## Render and assemble, as it was run

```sh
# from the repo root
S=songs/merge-conflict
python3 studio-early/analyze.py "Merge Conflict.wav" $S/analysis.npz
ffmpeg -i "Merge Conflict.wav" -ac 1 -ar 16000 -f f32le $S/full.f32 && (cd studio-early/asr && node asrw.mjs ../../$S/full.f32 ../../$S/asr_w.json)

python3 studio-early/render.py $S still 5 20 24 80 150 200          # stills -> $S/stills/s_<t>.png

# both aspect ratios per frame, in 300-frame chunks, two workers (END 209.5 s -> 6,285 frames)
for k in 0 1; do studio-early/drive_both.sh $S $k 2 6285 & done; wait

# concat the chunks, mux the audio, cut the Shorts and Reels
python3 studio-early/assemble.py $S "Merge Conflict.wav" 209.5 "Merge Conflict" \
  '[["Short 1 (his side to the chorus, 49s)", 43.1, 91.9], ["Short 2 (build failed to the final chorus, 53s)", 144.6, 197.8], ["Reel 1 (chorus, 21s)", 70.8, 91.9], ["Reel 2 (accept both changes, 21s)", 144.6, 166.0], ["Reel 3 (works on my machine, 20s)", 91.9, 111.8]]'

python3 studio-early/thumbs.py            # thumbnails for Graceful Shutdown, then Merge Conflict
```
