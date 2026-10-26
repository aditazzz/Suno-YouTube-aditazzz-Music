# Mirror, Mirror (v2): Hall of Mirrors

[![Mirror, Mirror (v2): Hall of Mirrors: watch on YouTube](thumbnail.jpg)](https://youtu.be/yxZGNE2k9XU)

**▶ [Watch it on YouTube](https://youtu.be/yxZGNE2k9XU)** · one of the [Mirror, Mirror, Look at Us](../../README.md#mirror-mirror-look-at-us-three-versions) videos

> Every mirror in this hall bends the face a different way: autocomplete, the beauty filter, take 30 of 30, auto-tune, ghostwriters. Guess which one is the only mirror that doesn't. 🪞

## What you see

A long dark hall lined with the bulb-lit vanity mirror from the cover art, each one bending the same face like a funhouse mirror. Every verse line turns to the mirror it's about and names what bends it, from AUTOCOMPLETE to AUTOPILOT. On every "mirror, mirror" the whole picture turns over like a hand mirror; on "look at us" every mirror in the hall straightens out and shows the same face. The lyrics are mirror-written and flip the right way round as each word is sung. The hall goes dark in the bridge, and on "mad" every mirror cracks at once, exactly where the cover is cracked.

## The code

| File | Lines | What it is |
|---|---:|---|
| [`hall.py`](hall.py) | 303 | The engine: a long dark hall lined on both sides with the cover's bulb-lit vanity mirror, each one showing the face from the cover through a different funhouse distortion, with the cover itself at the far end. A perspective camera walks the hall. |
| [`scene.py`](scene.py) | 449 | Mirror, Mirror, Look at Us — Hall of Mirrors (version 2 of 3). See [`NOTES.md`](NOTES.md) for the beats. |

That's **752 lines** of Python for this one video, on top of the shared engine in [`studio/`](../../studio). [`song.yaml`](song.yaml) holds the creative settings and copy, [`lyrics.txt`](lyrics.txt) the lyrics, and [`build/`](build) the word timings, beats, sections and clips.

The beat-by-beat plan for the video is in [NOTES.md](NOTES.md).

## By the numbers

- 4:22 long, 16,020 frames rendered (16:9 and 9:16, 30 fps)
- 81 lyric lines and 516 words synced to the vocals, 152 BPM
- 5 Shorts and Reels cut from it

## Render it

```bash
python -m studio.render songs/mirror-hall --stills 78.6 144.1 209.6 245.5
python -m studio.render songs/mirror-hall --fmt 9x16 --stills 78.6 144.1 209.6 245.5
```

The timing data is in `build/`, so stills render without the audio. You'll need the fonts listed in [assets/fonts/README.md](../../assets/fonts/README.md).

This scene also needs the song's cover art, through the Vanity scene (`../mirror-vanity/assets/cover_ref.png`). Those aren't in this repo, so it won't render as is; the code is here to read.

## The other versions

- [Mirror, Mirror (v1): The Vanity](../mirror-vanity)
- [Mirror, Mirror (v3): The Comment Section](../mirror-comments)

---

Song, lyrics and concept by aditazzz. Video by Claude Opus 5.5: every frame is rendered from the code in this folder. The code is MIT-licensed; the song, lyrics and artwork are all rights reserved ([details](../../LICENSE-CONTENT.md)).
