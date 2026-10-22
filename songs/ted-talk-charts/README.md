# TED Talk, in Charts

[![TED Talk, in Charts: watch on YouTube](thumbnail.jpg)](https://youtu.be/uCADBFlAyUI)

**▶ [Watch it on YouTube](https://youtu.be/uCADBFlAyUI)** · one of the [TED Talk](../../README.md#ted-talk-one-song-five-music-videos) videos

> I asked Ted if the file was ready. He said "so — stepping back," somebody dimmed the lights, and our fifteen-minute standup became an eighteen-minute keynote with no slides and no point. This time, in charts. 📊

## What you see

The whole song is one issue of a newspaper called The Daily Standup, with a new chart every few seconds: how Ted handles a question (it never reaches ANSWER), my will to live by minute (it falls off a cliff at minute four), the topics he covered (your question: 0%), his most-used words (so: 214, the file: 0), buzzword bingo, and a zoom-out on the one question nobody answered. When somebody dims the lights the paper sits under a spotlight; at Dana's hard stop the office lights snap back on and the paper prints a CORRECTION. In the end Ted's dot unplugs from the team network and drifts down into a footnote.

## The code

| File | Lines | What it is |
|---|---:|---|
| [`scene.py`](scene.py) | 1,310 | TED Talk, in charts: "The Daily Standup". |
| [`thumb.py`](thumb.py) | 136 | Thumbnails + Short cover for TED Talk (Charts): a front page of The Daily Standup. |

That's **1,446 lines** of Python for this one video, on top of the shared engine in [`studio/`](../../studio). [`song.yaml`](song.yaml) holds the creative settings and copy, [`lyrics.txt`](lyrics.txt) the lyrics, and [`build/`](build) the word timings, beats, sections and clips.

## By the numbers

- 2:41 long, 9,834 frames rendered (16:9 and 9:16, 30 fps)
- 57 lyric lines and 274 words synced to the vocals, 144 BPM
- 5 Shorts and Reels cut from it

## Render it

```bash
python -m studio.render songs/ted-talk-charts --stills 29.5 48.3 88.5 128.7
python -m studio.render songs/ted-talk-charts --fmt 9x16 --stills 29.5 48.3 88.5 128.7
```

The timing data is in `build/`, so stills render without the audio. You'll need the fonts listed in [assets/fonts/README.md](../../assets/fonts/README.md).

## The other versions

- [TED Talk (the original)](../ted-talk)
- [TED Talk, Stepping Back](../ted-talk-stepping-back)
- [TED Talk, in Shadow Puppets](../ted-talk-shadow-play)
- [TED Talk, on My Laptop Screen](../ted-talk-screenlife)

---

Song, lyrics and concept by aditazzz. Video by Claude Opus 5.5: every frame is rendered from the code in this folder. The code is MIT-licensed; the song, lyrics and artwork are all rights reserved ([details](../../LICENSE-CONTENT.md)).
