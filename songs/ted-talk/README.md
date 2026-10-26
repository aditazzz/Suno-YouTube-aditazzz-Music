# TED Talk (the original)

[![TED Talk (the original): watch on YouTube](thumbnail.jpg)](https://youtu.be/fj7HNVj7s1A)

**▶ [Watch it on YouTube](https://youtu.be/fj7HNVj7s1A)** · one of the [TED Talk](../../README.md#ted-talk-one-song-five-music-videos) videos

> I asked Ted if the file was ready. He said "so — stepping back," somebody dimmed the lights, and our fifteen-minute standup became an eighteen-minute keynote with no slides and no point. 🎤

## What you see

The standup circle turns into a stage, the red rug unrolls, the meeting clock blows past 15:00, and Dana's video tile slowly becomes a ghost.

## The code

| File | Lines | What it is |
|---|---:|---|
| [`scene.py`](scene.py) | 619 | TED Talk — the standup that turns into a keynote. |

That's **619 lines** of Python for this one video, on top of the shared engine in [`studio/`](../../studio). [`song.yaml`](song.yaml) holds the creative settings and copy, [`lyrics.txt`](lyrics.txt) the lyrics, and [`build/`](build) the word timings, beats, sections and clips.

## By the numbers

- 2:41 long, 9,654 frames rendered (16:9 and 9:16, 30 fps)
- 57 lyric lines and 274 words synced to the vocals, 144 BPM
- 5 Shorts and Reels cut from it

## Render it

```bash
python -m studio.render songs/ted-talk --stills 27.8 48.3 88.5 128.7
python -m studio.render songs/ted-talk --fmt 9x16 --stills 27.8 48.3 88.5 128.7
```

The timing data is in `build/`, so stills render without the audio. You'll need the fonts listed in [assets/fonts/README.md](../../assets/fonts/README.md).

## The other versions

- [TED Talk, in Charts](../ted-talk-charts)
- [TED Talk, Stepping Back](../ted-talk-stepping-back)
- [TED Talk, in Shadow Puppets](../ted-talk-shadow-play)
- [TED Talk, on My Laptop Screen](../ted-talk-screenlife)

---

Song, lyrics and concept by aditazzz. Video by Claude Opus 5.5: every frame is rendered from the code in this folder. The code is MIT-licensed; the song, lyrics and artwork are all rights reserved ([details](../../LICENSE-CONTENT.md)).
