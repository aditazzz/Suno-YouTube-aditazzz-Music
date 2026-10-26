# Snowflake Undrop

[![Snowflake Undrop: watch on YouTube](thumbnail.jpg)](https://youtu.be/fwYfcvyjhYw)

**▶ [Watch it on YouTube](https://youtu.be/fwYfcvyjhYw)**

> I ran DROP TABLE on production at 3 a.m. Snowflake didn't lecture me, didn't sulk, didn't bring it up again. It just kept the history long enough for me to type one word: UNDROP. ❄️ A love song to the only relationship where I'm comfortable paying by consumption.

## What you see

The production table shatters into ice, Time Travel rewinds it, and the rows rebuild themselves into a snowflake.

## The code

| File | Lines | What it is |
|---|---:|---|
| [`scene.py`](scene.py) | 3 | The entry point the pipeline calls: it hands over `render_frame()` from [`ud_render.py`](ud_render.py). |
| [`ud_engine.py`](ud_engine.py) | 289 | Shared helpers, timing and the data the scene is built from. |
| [`ud_render.py`](ud_render.py) | 745 | The renderer, including the clones of the table. |
| [`ud_scene.py`](ud_scene.py) | 254 | Palettes and the timeline: the shatter, the rewind and the rebuild. |

That's **1,291 lines** of Python for this one video, on top of the shared engine in [`studio/`](../../studio). [`song.yaml`](song.yaml) holds the creative settings and copy, [`lyrics.txt`](lyrics.txt) the lyrics, and [`build/`](build) the word timings, beats, sections and clips.

## By the numbers

- 4:26 long, 15,974 frames rendered (16:9 and 9:16, 30 fps)
- 89 lyric lines and 501 words synced to the vocals, 99 BPM
- 5 Shorts and Reels cut from it

## Render it

```bash
python -m studio.render songs/snowflake-undrop --stills 79.9 85.1 146.4 213.0
python -m studio.render songs/snowflake-undrop --fmt 9x16 --stills 79.9 85.1 146.4 213.0
```

The timing data is in `build/`, so stills render without the audio. You'll need the fonts listed in [assets/fonts/README.md](../../assets/fonts/README.md).

---

Song, lyrics and concept by aditazzz. Video by Claude Opus 5.5: every frame is rendered from the code in this folder. The code is MIT-licensed; the song, lyrics and artwork are all rights reserved ([details](../../LICENSE-CONTENT.md)).
