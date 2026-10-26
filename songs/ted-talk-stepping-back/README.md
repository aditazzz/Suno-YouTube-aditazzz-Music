# TED Talk, Stepping Back

[![TED Talk, Stepping Back: watch on YouTube](thumbnail.jpg)](https://youtu.be/J7B3NgWeIYs)

**▶ [Watch it on YouTube](https://youtu.be/J7B3NgWeIYs)** · one of the [TED Talk](../../README.md#ted-talk-one-song-five-music-videos) videos

> I asked Ted if the file was ready. He said "so — stepping back." So the camera did: from our standup all the way out to the edge of the observable universe. My question is still pinned in the middle. Unanswered. 🔭

## What you see

One continuous zoom out, every power of ten timed to the song: the standup from the ceiling, the office with its roof off, a city whose streets are named after Ted's buzzwords (Circle Back Blvd, Synergy St, Lake Pause, a town called Right?), the clouds, the Earth while my calendar gives up, the Moon, the planets circling back, the stars, the Milky Way, Andromeda, the cosmic web, and the edge of what anyone can see. At "Ted. This is a standup." it snaps all the way back into the room, where Ted has used 6 of our 15 minutes and Dana has become a ghost.

## The code

| File | Lines | What it is |
|---|---:|---|
| [`citymap.py`](citymap.py) | 374 | The city around the office, the countryside around the city and the clouds above it, as a clean light map. |
| [`cosmos.py`](cosmos.py) | 408 | Everything bigger than the weather: the Earth (photoreal, studio.space), the Moon, the solar system, the stars, the Milky Way, the Local Group, the cosmic web and the edge of the observable universe. |
| [`office.py`](office.py) | 267 | The standup from straight above: the office floor plan (an architect's plan with the roof off) and the eight people in a circle. |
| [`overlay.py`](overlay.py) | 573 | Everything on top of the world: map labels (Ted's buzzwords as place names), the pinned question, Ted's marker, the map app's search bar, compass, scale bar and clock, the bridge's 15-minute ring, the giant IT'S A TED TALK labels, the lyrics, the subscribe pill and the end card. |
| [`scene.py`](scene.py) | 248 | TED Talk, stepping back: one continuous zoom out. |
| [`thumb.py`](thumb.py) | 107 | Thumbnails + Short cover for TED Talk (Stepping Back). |
| [`view.py`](view.py) | 30 | A 2-D map camera: from the world (in metres) to screen pixels, with zoom and rotation. |
| [`zoomnoise.py`](zoomnoise.py) | 44 | Zoomable fractal noise: the same world-anchored pattern at any scale, with the octaves that would alias faded out, so land, clouds and nebulae seen at one scale are still the same pattern a power of ten later. |

That's **2,051 lines** of Python for this one video, on top of the shared engine in [`studio/`](../../studio). [`song.yaml`](song.yaml) holds the creative settings and copy, [`lyrics.txt`](lyrics.txt) the lyrics, and [`build/`](build) the word timings, beats, sections and clips.

## By the numbers

- 2:41 long, 9,834 frames rendered (16:9 and 9:16, 30 fps)
- 57 lyric lines and 274 words synced to the vocals, 144 BPM
- 6 Shorts and Reels cut from it

## Render it

```bash
python -m studio.render songs/ted-talk-stepping-back --stills 23.4 48.3 88.5 128.7
python -m studio.render songs/ted-talk-stepping-back --fmt 9x16 --stills 23.4 48.3 88.5 128.7
```

The timing data is in `build/`, so stills render without the audio. You'll need the fonts listed in [assets/fonts/README.md](../../assets/fonts/README.md).

## The other versions

- [TED Talk (the original)](../ted-talk)
- [TED Talk, in Charts](../ted-talk-charts)
- [TED Talk, in Shadow Puppets](../ted-talk-shadow-play)
- [TED Talk, on My Laptop Screen](../ted-talk-screenlife)

---

Song, lyrics and concept by aditazzz. Video by Claude Opus 5.5: every frame is rendered from the code in this folder. The code is MIT-licensed; the song, lyrics and artwork are all rights reserved ([details](../../LICENSE-CONTENT.md)).
