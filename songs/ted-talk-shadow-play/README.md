# TED Talk, in Shadow Puppets

[![TED Talk, in Shadow Puppets: watch on YouTube](thumbnail.jpg)](https://youtu.be/WdhmoHMFYI0)

**▶ [Watch it on YouTube](https://youtu.be/WdhmoHMFYI0)** · one of the [TED Talk](../../README.md#ted-talk-one-song-five-music-videos) videos

> I asked Ted if the file was ready. He said "so — stepping back," stepped back toward the lamp, and his shadow grew until it covered the whole room. Our standup, as a shadow puppet play. 🎭

## What you see

Cut-paper puppets behind a lamp-lit paper screen, where the only color on stage is a scrap of red gel: my hair clip. Every time Ted steps back toward the lamp, his shadow grows huge and soft over everyone. IT'S A TED TALK drops in on strings, his stories open in little irises (his father fishing, his father's father, young Ted in the rain with a violin), a cricket keeps time through the pause he thinks is powerful, paper gulls carry his words off, and my calendar waves a white flag. At "Ted. This is a standup." I stand up and he shrinks back to size: eight people get counted, Dana's empty chair grows cobwebs and a ghost, and the Q in Q&A burns away. In the end he walks off down a long road into an iris, and the lamp goes out on the red clip.

## The code

| File | Lines | What it is |
|---|---:|---|
| [`props.py`](props.py) | 402 | Cut-paper props for the shadow theatre. Everything returns polygons in world units (or stamps glyphs into masks). Floor at y = 880. |
| [`puppets.py`](puppets.py) | 232 | Cut-paper shadow puppets, side view (the way shadow theatre is always seen). |
| [`scene.py`](scene.py) | 858 | TED Talk as a shadow play: cut-paper puppets behind a lamp-lit paper screen. |
| [`stage.py`](stage.py) | 161 | The shadow theatre: a backlit paper screen in a dark proscenium, a camera onto it, and layers of shadow. |
| [`thumb.py`](thumb.py) | 120 | Thumbnails + Short cover for TED Talk (Shadow Play). |

That's **1,773 lines** of Python for this one video, on top of the shared engine in [`studio/`](../../studio). [`song.yaml`](song.yaml) holds the creative settings and copy, [`lyrics.txt`](lyrics.txt) the lyrics, and [`build/`](build) the word timings, beats, sections and clips.

## By the numbers

- 2:41 long, 9,834 frames rendered (16:9 and 9:16, 30 fps)
- 57 lyric lines and 274 words synced to the vocals, 144 BPM
- 6 Shorts and Reels cut from it

## Render it

```bash
python -m studio.render songs/ted-talk-shadow-play --stills 10.0 48.3 88.5 128.7
python -m studio.render songs/ted-talk-shadow-play --fmt 9x16 --stills 10.0 48.3 88.5 128.7
```

The timing data is in `build/`, so stills render without the audio. You'll need the fonts listed in [assets/fonts/README.md](../../assets/fonts/README.md).

## The other versions

- [TED Talk (the original)](../ted-talk)
- [TED Talk, in Charts](../ted-talk-charts)
- [TED Talk, Stepping Back](../ted-talk-stepping-back)
- [TED Talk, on My Laptop Screen](../ted-talk-screenlife)

---

Song, lyrics and concept by aditazzz. Video by Claude Opus 5.5: every frame is rendered from the code in this folder. The code is MIT-licensed; the song, lyrics and artwork are all rights reserved ([details](../../LICENSE-CONTENT.md)).
