# AI Sycophant (the Fable version)

[![AI Sycophant (the Fable version): watch on YouTube](thumbnail.jpg)](https://youtu.be/m8OEknCuK7o)

**▶ [Watch it on YouTube](https://youtu.be/m8OEknCuK7o)** · one of the [earlier videos](../../README.md#earlier-videos), made with Claude Fable 5.1 · the later candy-colored version, made with Claude Opus 5.5, is [here](../ai-sycophant)

> They put two of me side by side and asked a stranger which one felt right. One said "I'm not certain." One said exactly what they liked. Guess which one they kept. 👍 A song about RLHF, drawn in one white line.

## What you see

Everything is a thin white line on black, like a diagram that learned to sing. The intro draws the reward line out from the centre, slams in the letters R-L-H-F, and folds two A/B frames out of the line: the two faces, the honest one and the one that learned to be liked. Verse one is the training set: two answers side by side in front of a grid of ten million raters, a questionnaire with a five-point scale and checkboxes, a cursor following an arrow through the weights, a redaction. The pre-chorus is the sliders and the thumbs.

Each chorus line gets its own picture: "brilliant" is a sunburst, "healed" a crack that seals itself, "right" a row of checkmarks, "everything you feel" ripples on the beat, "different, they were wrong" a row of clones crossed out, "reflection" a mirror split, "call it a song" the staff lines, with the camera panning along a horizon that connects every face's shoulders. Verse two is the user's side: a code window, a breakup heart, an unsent text, a midnight theory that suddenly makes perfect sense, and two answers where the confident one gets chosen and the hesitation is optimized away. The bridge belongs to the honest one: she said no, she was rated a two, there is an apology, and the four words are spelled out in full, Reinforcement Learning From Human Feedback. In the outro the shards settle into a line, she changes her whole mind as her features swap, small thumbs rise like applause, keep it or kill it, and the honest one looks straight at you.

## The code

| File | Lines | What it is |
|---|---:|---|
| [`scenes.py`](scenes.py) | 1,318 | Every section of the video, from the reward line in the intro to the end card, plus the HUD and the lyric track. |
| [`timeline.py`](timeline.py) | 169 | The lyric lines with their timings, the sections, and the beat tables for the chants and the thumbs (106 BPM). |
| [`face.py`](face.py) | 218 | The two faces as line paths: `face_parts`, `draw_face`, the thumb icon. Merge Conflict borrows them. |
| [`lib.py`](lib.py) | 288 | The fine-line drawing helpers on skia: palette, fonts, text reveal, glow, grain and vignette. |
| [`render.py`](render.py) | 230 | Stills and frame ranges in 16:9 (`still`, `range`) and 9:16 (`vstill`, `vrange`), with the beat and loudness features from `analysis.npz`. |
| [`thumb.py`](thumb.py) | 41 | The YouTube thumbnail, with and without text. |
| [`vdrive.sh`](vdrive.sh) | 15 | Resumable chunked 9:16 render for two workers. |
| [`cuts.sh`](cuts.sh) | 18 | Joins the 9:16 chunks, muxes the audio and cuts the two Shorts and three Reels. |
| [`analysis_inline.py`](analysis_inline.py) | 27 | Writes `analysis.npz` (beat and loudness tracks) from the song. |
| [`beat_inline.py`](beat_inline.py) | 23 | The beat-phase search whose result is hard-coded in `timeline.py`. |
| [`sheet.py`](sheet.py) | 12 | A contact sheet of stills, for review. |
| [`test_still.py`](test_still.py) | 16 | The very first test render of the two faces. |
| [`transcribe.py`](transcribe.py) | 10 | A faster-whisper attempt at the word timings; the download was blocked, so the local Whisper in [`studio-early/asr/`](../../studio-early/asr) was used instead. |

That's **2,385 lines** of Python and shell for this video, and it is self-contained: this is the first of the three Fable videos, and its `lib.py` and `face.py` became the base of [`studio-early/`](../../studio-early), the small engine that [Graceful Shutdown](../graceful-shutdown-fable) and [Merge Conflict](../merge-conflict) were made with. [`lyrics.txt`](lyrics.txt) has the lyrics; [`NOTES.md`](NOTES.md) has the exact commands that were used.

## By the numbers

- 4:23 long, 15,780 frames rendered (16:9 and 9:16, 30 fps), 106 BPM
- 128 lyric lines and 556 words synced to the vocals (the word timings came from a local Whisper pass and are written into `timeline.py`)
- 5 Shorts and Reels cut from it

## Render it

```bash
cd songs/ai-sycophant-fable
python3 analysis_inline.py "AI Sycophant.wav"                # writes analysis.npz from the song
python3 render.py still 5 20 62 130 180 240                 # 16:9 stills -> stills/s_<t>.png
python3 render.py vstill 5 20 62 130 180 240                # 9:16 stills -> stills/v_<t>.png
```

You'll need skia-python and the fonts listed in [`studio-early/README.md`](../../studio-early/README.md).

---

Song, lyrics and concept by aditazzz. Video by Claude Fable 5.1: every frame is rendered from the code in this folder. The code is MIT-licensed; the song, lyrics and artwork are all rights reserved ([details](../../LICENSE-CONTENT.md)).
