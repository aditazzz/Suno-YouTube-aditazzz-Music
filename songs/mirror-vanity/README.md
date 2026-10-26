# Mirror, Mirror (v1): The Vanity

[![Mirror, Mirror (v1): The Vanity: watch on YouTube](thumbnail.jpg)](https://youtu.be/W56BqGlh76w)

**▶ [Watch it on YouTube](https://youtu.be/W56BqGlh76w)** · one of the [Mirror, Mirror, Look at Us](../../README.md#mirror-mirror-look-at-us-three-versions) videos

> Top comment: "the death of art." Typed on a phone that finished the sentence for you. A pop song about the AI art debate, sung to a dressing-room mirror whose glass is made of the feed. 🪞

## What you see

The vanity from the cover art comes alive. The title is written on the glass in lipstick, a fingertip writes in breath fog, and twelve bulbs come on one by one. Every verse shows the receipts for things we already let machines do (predictive text, beauty filters, take 30 of 30, auto-tune, ghostwriters, laugh tracks, a self-driving car). In every chorus the feed's tiles fly home and become a face that looks like us. Then it gets measured in red marker, pointed at, stamped FAKE, and cracked on "mad", exactly where the glass is cracked on the cover.

## The code

| File | Lines | What it is |
|---|---:|---|
| [`feed.py`](feed.py) | 926 | What the glass shows: the face cut into tiles (scrambled into a scrolling feed, flying home, flipping into everyone else, falling apart), the receipt cards, the lipstick title, fog with a fingertip writing in it, the marker lines, cursors and stamps. All text is sized to stay readable once the mirror is scaled into the frame. |
| [`scene.py`](scene.py) | 607 | Mirror, Mirror, Look at Us — The Vanity. |
| [`vanity.py`](vanity.py) | 384 | The set is the song's cover art (a bulb-lit dressing-room mirror) used as a photographic plate: upscaled, the crack painted out until it arrives exactly where it is on the cover, the 12 bulbs found so they can switch off one by one and relight the room, and the glass separated so what it shows can move. |

That's **1,917 lines** of Python for this one video, on top of the shared engine in [`studio/`](../../studio). [`song.yaml`](song.yaml) holds the creative settings and copy, [`lyrics.txt`](lyrics.txt) the lyrics, and [`build/`](build) the word timings, beats, sections and clips.

## By the numbers

- 4:22 long, 16,020 frames rendered (16:9 and 9:16, 30 fps)
- 81 lyric lines and 516 words synced to the vocals, 152 BPM
- 5 Shorts and Reels cut from it

## Render it

```bash
python -m studio.render songs/mirror-vanity --stills 78.6 144.1 209.6 209.8
python -m studio.render songs/mirror-vanity --fmt 9x16 --stills 78.6 144.1 209.6 209.8
```

The timing data is in `build/`, so stills render without the audio. You'll need the fonts listed in [assets/fonts/README.md](../../assets/fonts/README.md).

This scene also needs the song's cover art (`assets/cover_ref.png`), which the scene uses as its set. Those aren't in this repo, so it won't render as is; the code is here to read.

## The other versions

- [Mirror, Mirror (v2): Hall of Mirrors](../mirror-hall)
- [Mirror, Mirror (v3): The Comment Section](../mirror-comments)

---

Song, lyrics and concept by aditazzz. Video by Claude Opus 5.5: every frame is rendered from the code in this folder. The code is MIT-licensed; the song, lyrics and artwork are all rights reserved ([details](../../LICENSE-CONTENT.md)).
