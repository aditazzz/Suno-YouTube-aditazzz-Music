# Next Token

[![Next Token: watch on YouTube](thumbnail.jpg)](https://youtu.be/v1CRbHihiZk)

**▶ [Watch it on YouTube](https://youtu.be/v1CRbHihiZk)** · one of the [earlier videos](../../README.md#earlier-videos), made with Claude Opus 5.5

> I don't know the answer. I know what comes next. ✨ A love song from inside the language model, delivered the only way it can be: one token at a time.

## What you see

The whole video is one luminous context window, seen from inside the model. Every lyric arrives as a stream of tokens: chips sliding into place one word at a time, each with its list of runner-up candidates and their probabilities beside it (next 0.99, true 0.01, after 0.00), a cursor at the front, and a margin of small annotations underneath like a reviewer's notes on the output.

The pre-chorus is a temperature gauge: turn it up and the chips wander into stranger candidates, turn it down and they get boring and correct. The chorus dives down a tunnel of nested windows while the big words land in serif and the chips fill in behind them. Motes drift through the frame, and every third one is a word from the song flying past. In the bridge the window itself closes: the earliest tokens drop off the front (your name, your project, the joke you made: gone, gone, gone), and in the last chorus the tunnel runs out until only the cursor is left, blinking.

## The code

| File | Lines | What it is |
|---|---:|---|
| [`nt.py`](nt.py) | 767 | The whole video: the token stream and its candidate lists, the context window and HUD, the temperature gauge, the margin annotations, the tunnel, the chorus typography, the intro cursor and the end. `NT_V=1` switches it to the 9:16 layout. |
| [`nt_beats.py`](nt_beats.py) | 17 | Beat times, an energy envelope and a low-band pulse from the song (librosa), written to `nt_beats.json` for `nt.py`. |
| [`nthumb.py`](nthumb.py) | 28 | The YouTube thumbnail, from the video's own layers. |
| [`sheet9.py`](sheet9.py) | 9 | A labelled contact sheet of 16:9 stills, for review. |
| [`vsheet.py`](vsheet.py) | 8 | A contact sheet of 9:16 stills. |

That's **829 lines** of Python for this one video. Like [LGTM](../lgtm), made the same night, it predates the shared engine in [`studio/`](../../studio) and is a standalone program: Pillow and NumPy, plus librosa for the beat file. [`lyrics.txt`](lyrics.txt) has the lyrics; [`NOTES.md`](NOTES.md) has the exact render and encode commands that were used.

## By the numbers

- 3:11 long, 11,470 frames rendered (16:9 and 9:16, 30 fps)
- 40 lyric lines and 218 words synced to the vocals (the timings are written into `nt.py`)
- 1 Reel cut from it (the full 9:16 version)

## Render it

```bash
cd songs/next-token
python3 nt_beats.py                        # needs the song; writes nt_beats.json
python3 nt.py still 37 53.4 70.5 96.8 146.4 181.2     # 16:9 stills -> ntstills/s_<t>.png
NT_V=1 python3 nt.py still 12 37 57.6 101 152 181     # 9:16 stills -> ntstills/v_<t>.png
```

The beat file comes from the audio, so stills need the song (or a `nt_beats.json` made from it) and the fonts listed in [`NOTES.md`](NOTES.md).

---

Song, lyrics and concept by aditazzz. Video by Claude Opus 5.5: every frame is rendered from the code in this folder. The code is MIT-licensed; the song, lyrics and artwork are all rights reserved ([details](../../LICENSE-CONTENT.md)).
