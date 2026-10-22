# Mirror, Mirror (v3): The Comment Section

[![Mirror, Mirror (v3): The Comment Section: watch on YouTube](thumbnail.jpg)](https://youtu.be/9kZTktBfjjc)

**▶ [Watch it on YouTube](https://youtu.be/9kZTktBfjjc)** · one of the [Mirror, Mirror, Look at Us](../../README.md#mirror-mirror-look-at-us-three-versions) videos

> The top comment says "the death of art". Look under it: it was an autocomplete suggestion. A pop song about the AI art debate, played out under its own post. 🪞

## What you see

The song's own post fills with comments while the artist replies with the lyrics. Every comment gives itself away: an autocomplete chip under "the death of art", a beauty-filtered avatar on "no makeup, no filter, ever", "Pitch-corrected 100%", "Written by 7 people" and "typing this while driving lol". On every "mirror" the cover's glass reflects the whole thread. Everything gets stamped FAKE, a million comments get pulled into the mirror to train it, and it cracks on "mad"

## The code

| File | Lines | What it is |
|---|---:|---|
| [`build_ig_cover.py`](build_ig_cover.py) | 44 | Instagram (under 3 min) cover for Mirror, Mirror - The Comment Section, with the mirror image as the picture. |
| [`scene.py`](scene.py) | 830 | Mirror, Mirror, Look at Us — The Comment Section (version 3 of 3). See NOTES.md for the beats. |
| [`script.py`](script.py) | 136 | The thread: who posts what, when, and what gives each commenter away. Lyric lines are replies from @aditazzz (typed word by word on their sung times); the crowd and the system cards are written here by hand. |
| [`ui.py`](ui.py) | 497 | The Comment Section's UI kit: an invented comment-thread app in dark and light mode. Everything is drawn with PIL at page resolution and returned as premultiplied float sprites (sRGB, 0..1) so a frame is a stack of… |

That's **1,507 lines** of Python for this one video, on top of the shared engine in [`studio/`](../../studio). [`song.yaml`](song.yaml) holds the creative settings and copy, [`lyrics.txt`](lyrics.txt) the lyrics, and [`build/`](build) the word timings, beats, sections and clips.

The beat-by-beat plan for the video is in [NOTES.md](NOTES.md).

## By the numbers

- 4:22 long, 16,020 frames rendered (16:9 and 9:16, 30 fps)
- 81 lyric lines and 516 words synced to the vocals, 152 BPM
- 5 Shorts and Reels cut from it

## Render it

```bash
python -m studio.render songs/mirror-comments --stills 57.0 78.6 144.1 209.6
python -m studio.render songs/mirror-comments --fmt 9x16 --stills 57.0 78.6 144.1 209.6
```

The timing data is in `build/`, so stills render without the audio. You'll need the fonts listed in [assets/fonts/README.md](../../assets/fonts/README.md).

This scene also needs the song's cover art (`assets/cover_clean.png` and `assets/cover_cracked.png`). Those aren't in this repo, so it won't render as is; the code is here to read.

## The other versions

- [Mirror, Mirror (v1): The Vanity](../mirror-vanity)
- [Mirror, Mirror (v2): Hall of Mirrors](../mirror-hall)

---

Song, lyrics and concept by aditazzz. Video by Claude Opus 5.5: every frame is rendered from the code in this folder. The code is MIT-licensed; the song, lyrics and artwork are all rights reserved ([details](../../LICENSE-CONTENT.md)).
