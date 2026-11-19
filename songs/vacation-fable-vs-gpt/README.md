# Vacation (To My Bed): Claude Fable 5.2 vs GPT-6.2 Astra

[![Claude Fable 5.2 vs GPT-6.2 Astra made the same music video: watch on YouTube](thumbnail.jpg)](https://youtu.be/IC-mSO5-Ef8)

**▶ [Watch it on YouTube](https://youtu.be/IC-mSO5-Ef8)** · the [Short](https://youtube.com/shorts/iAzzXwWlen4) · the song's [original video](../vacation-to-my-bed)

<!-- model: Claude Fable 5.2 and GPT-6.2 Astra -->

> Same song. Same shot-by-shot direction. Same Mac. Four hours each, no help. One of these music videos was made by Claude Fable 5.2 in Claude Code, the other by GPT-6.2 Astra in Codex. Which is which? The answer drops on Friday, Nov 20.

## What you see

Two music videos for the same song, side by side, labeled only A and B. Both had to make the same film: a luxury travel commercial for a resort that is four seconds away. Sincere camera, golden light and premium travel-brand type, and every inch of the destination is her own apartment. The duvet is the ocean, the ceiling is the sky, the nightstand is room service, and it ends on a postcard of the bed: "Wish you were here."

It was a one-shot test: both got the same prompt, the same direction, the same song data and the same open-source film pipeline, with four hours on the clock and no help from me. Until the reveal, the code folder holds only what both runs got, byte for byte, so nothing in it gives the answer away.

## By the numbers

- 3:05 long, 1920×1080 at 30 fps, rendered in Blender
- 44 lyric lines timed to the vocal, 104.4 BPM
- 4 hours of working time per model

## How it worked: one shot

- **Same prompt, same direction.** Both got the exact same kickoff prompt and the same shot-by-shot direction, approved by me word for word. Then I let them go: no notes, no fixes, no second takes.
- **Same inputs.** The final song, Suno's own stems and MIDI for that take, every sung word timed to the vocal, and the lyric.
- **Same pipeline.** An open-source (MIT) film pipeline: treatment, shots, blocking, build and edit, with a critic pass along the way. Everything was rendered in Blender, both runs side by side on my MacBook Pro at the same time.
- **Same clock.** Four hours of working time each, final render included. Time spent stuck at a usage limit didn't count.
- **Same effort.** Both ran at their highest setting (xhigh).

## The files

| File | What it is |
|---|---|
| [`inputs/kickoff-prompt.md`](inputs/kickoff-prompt.md) | The one-shot prompt both runs started from |
| [`inputs/direction.md`](inputs/direction.md) | The full shot-by-shot direction (the brief) |
| [`inputs/map.md`](inputs/map.md) | The song's map: tempo, sections, energy and what's playing where |
| [`inputs/timing.json`](inputs/timing.json) | Every sung word, timed to the vocal |
| [`lyrics.txt`](lyrics.txt) | The lyrics |

At the reveal: which is which, the poll results, and each run's own report on how it made its film.

## The fine print

- GPT-6.2 Astra hit my ChatGPT usage limit 27 minutes in, and again about an hour later. I used a reset, then upgraded my plan.
- Fable hit my Claude usage limit right after it finished rendering every shot.
- Not a scientific benchmark: one song, one run each, one person's direction.

---

Song, lyrics and concept by aditazzz. Videos made in code by Claude Fable 5.2 (Claude Code) and GPT-6.2 Astra (Codex), each following the same direction. The song, lyrics and artwork are all rights reserved ([details](../../LICENSE-CONTENT.md)).
