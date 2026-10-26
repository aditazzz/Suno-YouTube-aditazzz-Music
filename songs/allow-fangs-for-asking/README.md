# Allow (Fangs for Asking)

[![Allow (Fangs for Asking): watch on YouTube](thumbnail.jpg)](https://youtu.be/U4j5HD8G6rU)

**▶ [Watch it on YouTube](https://youtu.be/U4j5HD8G6rU)**

> A vampire only comes in if you invite him. This one asks every night, so politely, from a little glowing screen. 🧛 Allow?

## What you see

A gothic film in one Victorian bedroom at midnight. The vampire is never shown: he's a silhouette beyond the rain, and the invitation is a permission prompt on her phone. The film is built on 17 photographic plates, generated in ChatGPT from aditazzz's prompts and upscaled; everything that moves is code. Rain runs down the outside of the glass, every drop a tiny lens that turns the street upside down, while the inside fogs over, takes his breath-writing ("Midnight" would like to send you notifications) and clears in an oval when he leans in to ask "May I?". "Allow" grows in frost on the pane. The candle and the phone trade the room between them: every sung Allow pulls it a step from candlelight toward screen blue, and the candle goes out on "undead". The permission prompts climb from Notifications to Location, Camera, Microphone and Contacts, and the bite marks are two red notification badges. In the bridge the camera leaves the room for the first time, following one point of blue light down the street to her sister's window, and now she's the one outside, asking. At the end the town's windows turn screen-blue one by one, and one warm light comes on.

Nothing is timed to a tempo grid. The song is a waltz with a pulse that loosens in the bridge, so every sung Allow, every tap and every cut is measured from the recording itself (the vocal and band stems) and kept in [`cues.json`](cues.json). The shot list is in [`STORYBOARD.md`](STORYBOARD.md).

## The code

<!-- excerpt: allow/film.py Film.master -->

| File | Lines | What it is |
|---|---:|---|
| [`allow/film.py`](allow/film.py) | 371 | The edit: all 36 shots as a cut list on moments measured from the song, each shot's camera and state, and `Film(W, H).frame(t)`, which renders any moment to a finished frame. |
| [`allow/timeline.py`](allow/timeline.py) | 71 | The film's clock, read from [`cues.json`](cues.json): every sung Allow and the flare after it, how far the room has gone from candlelight to screen blue, the taps and the lyric on screen. |
| [`allow/master.py`](allow/master.py) | 229 | The master shot: her bedroom window (plate 1) rebuilt as a lit set. The glass, the candle, the phone and the room are separated and relit on their own, so the room can move from candlelight to night to phone. |
| [`allow/glass.py`](allow/glass.py) | 212 | The window glass: raindrops on the outside, each refracting an upside-down street, sliding in stick-slip jumps and leaving clear trails; condensation on the inside that takes writing and refills; tap rings; frost lettering. |
| [`allow/shoulder.py`](allow/shoulder.py) | 91 | Over her shoulder at the sill (plate 2), with his silhouette (plate 7) out of focus beyond the rain, dark against the street lamp. |
| [`allow/macro.py`](allow/macro.py) | 146 | The close-ups: the rainy pane that opens the film, where the fog takes his words and three taps ring it, and the brass bolts, each snapping shut on its own word. |
| [`allow/shots.py`](allow/shots.py) | 117 | The inserts, one plate each: the sill, the bed, the phone, her neck with its two notification badges, her face behind the rain, and the warm-to-cold grade they share. |
| [`allow/others.py`](allow/others.py) | 218 | The mirror that shows the room and not her, her sister's window from outside, where her hand rises in and traces "Allow?" backwards on the glass, and the city whose windows go blue one at a time. |
| [`allow/street.py`](allow/street.py) | 60 | The bridge, the first time the camera leaves her room: a point of cold light drifts down the wet street to her sister's window, and the camera follows. |
| [`allow/ui.py`](allow/ui.py) | 110 | The phone screens: the permission prompts, the share sheet and the 3 a.m. lock screen, drawn as real-looking system UI and mapped onto the phones in the plates in perspective. |
| [`allow/kit.py`](allow/kit.py) | 154 | Shared scene pieces: loading the plates, the candle flame and its halo, keying his silhouette, and the quiet serif lyric line. |
| [`allow/fx.py`](allow/fx.py) | 201 | The building blocks: everything in linear light, seeded noise and blurs, and the film finish (halation, highlight roll-off, split-tone, vignette, grain and the 2:1 letterbox). |
| [`render.py`](render.py) | 71 | The renderer: any range of the film to H.264 in resumable five-second chunks, joined and muxed with the song at the end. |
| [`make_stills.py`](make_stills.py) | 29 | The six approval stills, rendered at 4K before the full film. |

That's **2,080 lines** for this one video. Like the earliest videos here, it's a standalone program: its own small engine in [`allow/`](allow), not the Python engine in [`studio/`](../../studio). [`lyrics.txt`](lyrics.txt) holds the lyrics, [`cues.json`](cues.json) every moment measured from the recording and [`timed.json`](timed.json) the lyric lines word by word.

## By the numbers

- 4:05 long, 7,356 frames rendered at 2560×1440
- 17 photographic plates, 36 shots, 0 stock footage
- 14 sung "Allow"s and 10 taps, every one measured from the recording and hit on the frame
- 5 permission prompts, from Notifications to Contacts, before the sister gets one of her own

## Render it

```bash
cd songs/allow-fangs-for-asking
mkdir -p stills && python3 make_stills.py      # the six approval stills
python3 render.py 0 245.2 allow.mp4 --w 2560    # the whole film at 1440p, in resumable chunks, then the song
```

The 17 plates aren't in this repo: the code expects them in `plates/` (and the 4× upscales in `plates/up/`). Without them it won't render, but it's all here to read. The film uses Cormorant Garamond (SemiBold and Medium Italic) and Inter (Regular, Medium and SemiBold) from [assets/fonts](../../assets/fonts/README.md). The audio isn't in this repo either: `render.py` adds the song from `audio_clean.wav` at the end (`--no-mux` keeps just the rendered chunks). The timing measured from it is here.

---

Song, lyrics and concept by aditazzz. Video by Claude Opus 5.5: every frame is rendered from the code in this folder, over photographic plates generated in ChatGPT from aditazzz's prompts. The code is MIT-licensed; the song, lyrics and artwork are all rights reserved ([details](../../LICENSE-CONTENT.md)).
