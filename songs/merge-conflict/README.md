# Merge Conflict

[![Merge Conflict: watch on YouTube](thumbnail.jpg)](https://youtu.be/MXJEF6xaPtU)

**▶ [Watch it on YouTube](https://youtu.be/MXJEF6xaPtU)** · one of the [earlier videos](../../README.md#earlier-videos), made with Claude Fable 5.1

> Two hearts on the same line, at the very same time. 💔 A breakup told as a git merge conflict: HEAD (her) versus the incoming branch (him), one file, line 42.

## What you see

Fine white lines on black. Her face on the left is HEAD; his on the right is the incoming branch. Between them sits `main.py`, and both of them keep rewriting line 42: she renames the function and leaves a note, he makes it async and clean, and on the branch graph his feature branch lives for three whole weeks without a single pull. The pre-chorus draws the conflict markers between the two faces, seven arrows left, a line of equals, seven arrows right, and nothing in the middle but the screen.

In the chorus the two versions of the line alternate on the beat, two hearts land on the same line at the same time, each rebase is refused, and the markers close like a vise. Verse two is the evidence: her green tests, his thread where the lead said yes, a force-push forgiven, commits squashed, "works on my machine" on both laptops. The bridge is a code lens over the review notes (`get_user (better)`, `if user is None: return (saved me)`), and the breakdown runs through the editor's three buttons: accept current, accept incoming, accept both. Build failed. The final chorus resolves the file line by line, merges on the graph, pushes straight to main, and the marker glyphs drift away. The outro: merge successful. Two new conflicts in `utils.py`.

## The code

| File | Lines | What it is |
|---|---:|---|
| [`scenes.py`](scenes.py) | 634 | Every section of the video: the two faces, the code editor, the branch graph, the conflict markers, the chorus, the evidence, the code lens, the breakdown, the resolution and the outro, plus the HUD for both aspect ratios. |

That's **634 lines** of Python for this video, on top of [`studio-early/`](../../studio-early), the small engine that came before [`studio/`](../../studio) (it draws with skia, renders stills and frame ranges, and assembles the final files), and the faces and line-drawing helpers in [`../ai-sycophant-fable/`](../ai-sycophant-fable) (`face.py`, `lib.py`), which it imports. [`lyrics.txt`](lyrics.txt) has the lyrics; [`NOTES.md`](NOTES.md) has the exact commands that were used.

## By the numbers

- 3:30 long, 12,570 frames rendered (16:9 and 9:16, 30 fps), 120 BPM
- 61 lyric lines and 338 words synced to the vocals (the word timings came from a local Whisper pass and are written into `scenes.py`)
- 5 Shorts and Reels cut from it

## Render it

```bash
# from the repo root; see studio-early/README.md for the paths the early engine expects
python3 studio-early/render.py songs/merge-conflict still 5 20 24 80 150 200    # -> songs/merge-conflict/stills/
```

The scene needs `analysis.npz` (beat and loudness tracks made from the song by `studio-early/analyze.py`) and the fonts in [`studio-early/README.md`](../../studio-early/README.md).

---

Song, lyrics and concept by aditazzz. Video by Claude Fable 5.1: every frame is rendered from the code in this folder. The code is MIT-licensed; the song, lyrics and artwork are all rights reserved ([details](../../LICENSE-CONTENT.md)).
