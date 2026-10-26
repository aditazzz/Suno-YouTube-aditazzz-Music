# Git Blame

[![Git Blame: watch on YouTube](thumbnail.jpg)](https://youtu.be/tSyb-KQfysA)

**▶ [Watch it on YouTube](https://youtu.be/tSyb-KQfysA)**

> Pulled the history. Line forty-two? His name. Forty-three? Him again. And the co-author on that 3:14 a.m. commit was my best friend. 💀 A breakup song in git blame.

## What you see

A blame view where every gutter fills with his name, prod catching fire at 3:14 a.m., a git log that scrolls forever, a neon synthwave chorus where the lines get squashed and rebased and his name never moves, a force-push bouncing off branch protection, git shortlog after every chorus (42 lines him, 0 me), and a corkboard of timestamped receipts where "love you" gets reverted a minute later.

## The code

| File | Lines | What it is |
|---|---:|---|
| [`scene.py`](scene.py) | 431 | Git Blame — receipts in neon. |

That's **431 lines** of Python for this one video, on top of the shared engine in [`studio/`](../../studio). [`song.yaml`](song.yaml) holds the creative settings and copy, [`lyrics.txt`](lyrics.txt) the lyrics, and [`build/`](build) the word timings, beats, sections and clips.

## By the numbers

- 3:49 long, 13,722 frames rendered (16:9 and 9:16, 30 fps)
- 95 lyric lines and 390 words synced to the vocals, 96 BPM
- 5 Shorts and Reels cut from it

## Render it

```bash
python -m studio.render songs/git-blame --stills 3.2 68.6 125.8 183.0
python -m studio.render songs/git-blame --fmt 9x16 --stills 3.2 68.6 125.8 183.0
```

The timing data is in `build/`, so stills render without the audio. You'll need the fonts listed in [assets/fonts/README.md](../../assets/fonts/README.md).

---

Song, lyrics and concept by aditazzz. Video by Claude Opus 5.5: every frame is rendered from the code in this folder. The code is MIT-licensed; the song, lyrics and artwork are all rights reserved ([details](../../LICENSE-CONTENT.md)).
