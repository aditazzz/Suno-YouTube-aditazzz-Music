# TED Talk, on My Laptop Screen

[![TED Talk, on My Laptop Screen: watch on YouTube](thumbnail.jpg)](https://youtu.be/yTvdXw8K6Ls)

**▶ [Watch it on YouTube](https://youtu.be/yTvdXw8K6Ls)** · one of the [TED Talk](../../README.md#ted-talk-one-song-five-music-videos) videos

> I asked Ted if the file was ready. He stepped back from his webcam, somebody turned on dark mode, everybody's camera went off, and my calendar crashed. Our standup, told entirely on my laptop screen. 💻

## What you see

The whole song plays out on my laptop screen, like a screenlife film. The standup is a video call and Ted is the host. My question sits in the chat while he answers it with a question, and four minutes in the meeting timer says it all. At "so — stepping back" he literally steps back from his webcam, somebody dims the lights (dark mode), everybody sits down (cameras off), and his virtual background turns into a keynote stage. He shares eighteen minutes of blank slides, a photo of his father fishing, a loading circle for circling back and a picture of himself at seven in the rain. I keep a tally of every "so" and every "right?", get buzzword bingo, and watch my calendar crash. At "Ted. This is a standup." I unmute: eight people, fifteen minutes, Ted has used six, and Dana, who left two years ago, is a ghost in her tile now. Nobody can end the meeting, the host has turned off Q&A, and when he finally takes it offline, my message to him can't be delivered.

## The code

| File | Lines | What it is |
|---|---:|---|
| [`apps.py`](apps.py) | 628 | The apps on her laptop: the desktop, the meeting app (Huddle), its chat / people / Q&A panel, Notes, Calendar, notifications and dialogs. All drawn from a state object S (see scene.state). |
| [`avatars.py`](avatars.py) | 318 | The people in the video tiles: flat, front-facing illustrations in their home offices. |
| [`scene.py`](scene.py) | 594 | TED Talk, as screenlife: the whole song happens on her laptop screen. |
| [`thumb.py`](thumb.py) | 99 | Thumbnails + Short cover for TED Talk (Screenlife). |
| [`ui.py`](ui.py) | 350 | A small vector UI kit for the laptop desktop: rounded rectangles, text, icons and shadows in desktop units (the screen is 1280 × 720), drawn through a camera so everything stays crisp at any zoom. |

That's **1,989 lines** of Python for this one video, on top of the shared engine in [`studio/`](../../studio). [`song.yaml`](song.yaml) holds the creative settings and copy, [`lyrics.txt`](lyrics.txt) the lyrics, and [`build/`](build) the word timings, beats, sections and clips.

## By the numbers

- 2:41 long, 9,834 frames rendered (16:9 and 9:16, 30 fps)
- 57 lyric lines and 274 words synced to the vocals, 144 BPM
- 6 Shorts and Reels cut from it

## Render it

```bash
python -m studio.render songs/ted-talk-screenlife --stills 10.0 48.3 88.5 128.7
python -m studio.render songs/ted-talk-screenlife --fmt 9x16 --stills 10.0 48.3 88.5 128.7
```

The timing data is in `build/`, so stills render without the audio. You'll need the fonts listed in [assets/fonts/README.md](../../assets/fonts/README.md).

## The other versions

- [TED Talk (the original)](../ted-talk)
- [TED Talk, in Charts](../ted-talk-charts)
- [TED Talk, Stepping Back](../ted-talk-stepping-back)
- [TED Talk, in Shadow Puppets](../ted-talk-shadow-play)

---

Song, lyrics and concept by aditazzz. Video by Claude Opus 5.5: every frame is rendered from the code in this folder. The code is MIT-licensed; the song, lyrics and artwork are all rights reserved ([details](../../LICENSE-CONTENT.md)).
