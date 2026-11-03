# Get Off War Thunder: how it was made

This video was made on October 17–18, 2026, in one chat with Claude Fable 5.1, as a standalone Python program (before
`studio/` existed). The chat's workspace is gone, so the code here was recovered from the chat itself: every file it
wrote, with every later edit replayed in order. Two scripts that ran inline in the chat are saved as files
(`audio_feats.py` and `mux_shorts.py`), and the one absolute output path the chat used is now relative, marked with a
comment. Rendered from this folder with the original song, its frames match the published video.

## Files

| File | What it is |
|---|---|
| `render.py` | The 16:9 video, 1920x1080 at 30 fps. `LINES` holds every lyric line with its word timings; `scene_at()` picks the scene for each moment. |
| `vertical.py` | The three Shorts, 1080x1920. It imports `render.py` and redraws its scenes in a vertical layout. The windows: 9.6–45.8 s, 45.8–77.5 s and 77.5 s to the end. |
| `cover.py` | The YouTube cover (1280x720, plus a 1080p copy). |
| `audio_feats.py` | Writes `audio_feats.json`: tempo, beat phase and loudness per frame. `render.py` loads it at import, so it has to exist before anything renders. |
| `asr.py` | Word timestamps from the vocals with Parakeet TDT 0.6b v2 (int8) through sherpa-onnx, written to `words.json`. The timings were then typed into `render.py`, so rendering doesn't read `words.json`. |
| `mux_shorts.py` | Adds the song to the three silent Short renders, with a 0.25 s fade in and a 0.5 s fade out. |

## What isn't in the repo

- The song (`Get Off War Thunder.wav`, used here as `song.wav`) and `song16k.wav`, made from it.
- `audio_feats.json` and `words.json`: both are made from the song by the scripts above.
- The fonts, all from [google/fonts](https://github.com/google/fonts) (`ofl/`): Black Ops One, Bangers, Russo One,
  Share Tech Mono and Orbitron (`Orbitron[wght].ttf`), in `fonts/`. The star in the last scene uses DejaVu Sans from the
  system (`/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf`).
- The speech model, only needed to redo the timing: `models/sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8` from the
  k2-fsa/sherpa-onnx `asr-models` release, with `pip install sherpa-onnx`.

## Render and assemble, as it was run

```sh
# in this folder, with song.wav and fonts/ in place
ffmpeg -v error -y -i song.wav -ac 1 -ar 16000 song16k.wav
python3 audio_feats.py                       # -> audio_feats.json
python3 asr.py                               # -> words.json (only to redo the word timings)

# the video: 3,617 frames in two halves, side by side, then the song
python3 render.py segment 0 1808 seg_a.mp4 &
python3 render.py segment 1808 3617 seg_b.mp4 &
wait
printf "file 'seg_a.mp4'\nfile 'seg_b.mp4'\n" > list.txt
ffmpeg -v error -y -f concat -safe 0 -i list.txt -i song.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 256k \
  -movflags +faststart -shortest "Get Off War Thunder - Aditazzz feat Alex.mp4"

# the cover
python3 cover.py cover.png

# the Shorts: three silent renders, then the song
for i in 1 2 3; do python3 vertical.py $i short_${i}_v.mp4 & done; wait
python3 mux_shorts.py

# single frames for checking
python3 render.py frame 33 frame.png
python3 vertical.py frame 2 60 short_frame.png
```

Needs Python 3 with Pillow and numpy, and ffmpeg.
