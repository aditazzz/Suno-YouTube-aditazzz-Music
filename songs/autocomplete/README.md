# Autocomplete

[![Autocomplete: watch on YouTube](thumbnail.jpg)](https://youtu.be/EJeIkThk8xA)

**▶ [Watch it on YouTube](https://youtu.be/EJeIkThk8xA)**

> I type half a thought. You fill in what I've got. A dark, late-night electro-pop song about being predicted by an AI, and how being understood this fast feels a little too much like being wanted. 🖤

## What you see

Every lyric appears in a text field where the AI's glowing completion shows up before she sings it, next-token guesses drift with their probabilities, the chorus blooms around a giant AUTO|COMPLETE wordmark, and in the bridge her pulse races a probability chart until "I was going to say—" cuts to black, and at the end the model keeps offering endings to a sentence she never finishes.

## The code

| File | Lines | What it is |
|---|---:|---|
| [`scene.py`](scene.py) | 317 | Autocomplete — it finishes her sentences before she sings them. |

That's **317 lines** of Python for this one video, on top of the shared engine in [`studio/`](../../studio). [`song.yaml`](song.yaml) holds the creative settings and copy, [`lyrics.txt`](lyrics.txt) the lyrics, and [`build/`](build) the word timings, beats, sections and clips.

## By the numbers

- 3:07 long, 11,232 frames rendered (16:9 and 9:16, 30 fps)
- 72 lyric lines and 312 words synced to the vocals, 108 BPM
- 5 Shorts and Reels cut from it

## Render it

```bash
python -m studio.render songs/autocomplete --stills 0.4 56.2 103.0 149.8
python -m studio.render songs/autocomplete --fmt 9x16 --stills 0.4 56.2 103.0 149.8
```

The timing data is in `build/`, so stills render without the audio. You'll need the fonts listed in [assets/fonts/README.md](../../assets/fonts/README.md).

---

Song, lyrics and concept by aditazzz. Video by Claude Opus 5.5: every frame is rendered from the code in this folder. The code is MIT-licensed; the song, lyrics and artwork are all rights reserved ([details](../../LICENSE-CONTENT.md)).
