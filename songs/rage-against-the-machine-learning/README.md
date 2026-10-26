# Rage Against the Machine Learning

[![Rage Against the Machine Learning: watch on YouTube](thumbnail.jpg)](https://youtu.be/yihrQYQjx40)

**▶ [Watch it on YouTube](https://youtu.be/yihrQYQjx40)**

> They scraped my blog from 2009. My terrible poems. My cat's full name. I never clicked accept, and the model kept learning anyway. A 90s rap-rock protest anthem for everyone whose whole personality is now a vector. ✊

## What you see

A night wall gets wheat-pasted with photocopied evidence of a life scraped into a training set (the 2009 blog stamped SCRAPED, a router poem marked "awful", the cat's full name circled, Clause 62 in size-two font), then the boardroom memo that followed (efficiency gains, 10,000 tally marks, a bunker for sale, an invoice stamped UNPAID). Every hook is a crowd chant slammed onto torn paper, the breakdown chart lets LOSS fall while RENT punches through the poster, and OPT OUT gets spray-painted across the whole wall.

## The code

| File | Lines | What it is |
|---|---:|---|
| [`scene.py`](scene.py) | 1,438 | Rage Against the Machine Learning — protest zine riot. |
| [`sync_fix.py`](sync_fix.py) | 29 | This song's sync fix: the shouted gang vocals barely register in the separated vocal stem, so the words for those parts come from transcribing the full mix, and a few line starts are set by hand. |

That's **1,467 lines** of Python for this one video, on top of the shared engine in [`studio/`](../../studio). [`song.yaml`](song.yaml) holds the creative settings and copy, [`lyrics.txt`](lyrics.txt) the lyrics, and [`build/`](build) the word timings, beats, sections and clips.

## By the numbers

- 2:47 long, 10,014 frames rendered (16:9 and 9:16, 30 fps)
- 38 lyric lines and 258 words synced to the vocals, 99 BPM
- 5 Shorts and Reels cut from it

## Render it

```bash
python -m studio.render songs/rage-against-the-machine-learning --stills 50.1 91.8 126.0 133.5
python -m studio.render songs/rage-against-the-machine-learning --fmt 9x16 --stills 50.1 91.8 126.0 133.5
```

The timing data is in `build/`, so stills render without the audio. You'll need the fonts listed in [assets/fonts/README.md](../../assets/fonts/README.md).

---

Song, lyrics and concept by aditazzz. Video by Claude Opus 5.5: every frame is rendered from the code in this folder. The code is MIT-licensed; the song, lyrics and artwork are all rights reserved ([details](../../LICENSE-CONTENT.md)).
