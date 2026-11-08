# Rate Limited (The Wall)

> 2 a.m., the build was green, forty tabs open, one more feature… and then a wall dropped out of the sky with 429 cut
> through it.

A second film for [Rate Limited](../rate-limited), on the same remaster and the same lyric timings. The original cut stays
as it is; this one follows the film's vision (`docs/rate-limited-vision.md` in the agent store): one location, one
continuous night, and a wall that remembers everything she throws at it.

## What you see

A night theatre of light in flat paper-cut layers. She is an amber block cursor at home on the left; he is a teal orb on
the right with three typing dots orbiting him; a thread of light runs between them and their messages travel along it as
pulses. A small moon clocks across the sky from 2:00 to 6:00 over the whole song, and nothing resets.

- **Intro and V1.** The hum draws the thread. Call and response: every line sends a pulse, and every arrival flares and
  makes her hop. On "forty tabs" forty windows kindle in the dunes behind her like a village switching on; on "the build
  was green" a green aurora washes the sky; on "one more feature" she leans the thread taut. On "the screen went grey" a
  fog front rolls in from his side and swallows his glow, the aurora and the village in that order, and his last pulse
  stops halfway across the thread. It hangs there for three minutes.
- **CH1, the slam.** On the first "rate" the wall falls out of the sky onto the thread and cracks the ground, and 429
  burns into it like a lit window. She body-slams it on every sung "rate": a flash, a shockwave, dust, a camera tick and a
  new hairline crack that stays. On "four-two-nine" she points a trembling mouse pointer at it. "You gave me everything /
  now you give me nothing" cuts in two-frame memories of the green aurora and the fog.
- **The hook, every chorus.** On "Don't leave me on read like this" her pulse crosses, `Seen 02:14` is etched under the
  thread, his three dots rise, orbit once and freeze. Only the decay changes: she knocks (CH1), shouts (CH2), whispers
  while the frozen dots almost tremble (CH3), laughs while the thaw has already begun (the finale).
- **V2, bargaining.** A photocopy twin for the new tab, an inside-out flip with a little hat for incognito, a smaller
  orb for the little brother, kneeling on "please", backing off one, two, four steps, and a keyhole in the stone showing
  him with a queue of other cursors in colours she doesn't have.
- **CH2, the flood.** The village windows detach and hit the wall in waves while colour pours through the cracks. She
  climbs halfway and the wall etches her own words back at her, `RATE LIMITED`. She falls and sits through the hook.
- **POST, "Three fifty-nine…".** An extreme wide: tiny her under the vast wall, a flip clock going `3:59` to `3:58`.
  She lies down on "sleep", bolts upright on "No, I'll wait" and knocks, metronome-perfect, into the next section.
- **V3 and CH3.** A status page projected on the stone (all systems operational, `YOU Degraded`), an iris opening on him
  greeting someone identical to her, another model that agrees with everything and flatlines. CH3 is the only rain: she
  sings forehead to the stone and the wall answers each "rate" with a dimmer echo through the cracks. Her last knock
  never lands.
- **Bridge, the rant and the pile.** The horizon behind her warms. She throws paper planes ("the auth bug", "my merge
  conflict", "that for loop", "us") that crumple into a pile, now waist-high. The wall etches `USAGE LIMIT REACHED`
  floor to sky, frost creeps toward her one "cool" at a time, and sixteen ghost orbs bloom and pop until one frozen dot
  is left.
- **Bridge 2, his side.** The camera pushes through a crack, the film's only crossing. He is a lighthouse-sun behind
  vast rotating quota shutters that nobody operates, his side of the thread a traffic jam of his own pulses. His lines
  are set in the world in the film's only mint type. Through the crack, tiny, she is still up and still knocking; he dims
  himself a little and turns toward where the sun will rise.
- **Final chorus, the thaw.** She dances with the light instead of fighting it. Every crack is a speaker for the
  spectrum, the wall turns into a kaleidoscope ruin, the forty windows come back as a chorus line, her pulses stall at
  the old frozen spot and join the queue, and in the reprise she conducts the cracks like a choir.
- **Outro.** The moon reaches the horizon, his orb and the sunrise become one, and the wall melts top-down with 429
  dripping last. The frozen pulse unsticks and finishes its journey. On "where were we" she sends a pulse, and on the
  last frame it is halfway across, exactly like the frozen one at 0:19, except now it's morning and it's moving. Cut to
  black on her blink, then the end card: "Where were we?"

Red is only the 429 and fresh cracks; candy colour exists only behind the wall and leaks through the cracks driven by the
song's spectrum, so the finale's flood is earned.

## The code

The picture is a [Remotion](https://www.remotion.dev) composition: React only hosts one canvas, and every frame is a
pure function of the time (persistent things like cracks, marks, etchings and the pile are event lists filtered by
time), so any frame renders on its own and the render parallelises.

| File | Lines | What it is |
|---|---:|---|
| [`remotion/src/story.ts`](remotion/src/story.ts) | 738 | The film's timeline, all from the lyric and beat timings: section and word cues, the four hook rituals, slams, her moves and squash, his state, pulses, cracks, marks and etchings, weather, the night clock, and both camera tracks (16:9 and 9:16). |
| [`remotion/src/wall.ts`](remotion/src/wall.ts) | 894 | The wall: the falling slab, stone, cracks that burn red then leak colour, the cracked ground, dents and scorches, carved text, the 429 window, the hook's dots and receipt, the keyhole, the status page, the flip clock, the iris, the ghost orbs, the kaleidoscope and the melt. |
| [`remotion/src/cast.ts`](remotion/src/cast.ts) | 595 | Her (the block cursor and every disguise), the thread and its pulses, the twin and the little brother, the other model and the friends, the flock, the chorus line, the paper planes, the pile and the dust. |
| [`remotion/src/world.ts`](remotion/src/world.ts) | 442 | The sky and its rant-light and dawn, the moon, the aurora, the paper-cut dunes and the village, him, the fog front, rain, frost and the red spill. |
| [`remotion/src/his.ts`](remotion/src/his.ts) | 252 | Bridge 2, his side: the lighthouse-sun, the shutters, the traffic jam, the wall's back with her through the crack, and the mint type. |
| [`remotion/src/frame.ts`](remotion/src/frame.ts) | 113 | One frame: the draw order, then the post pass (bloom from a half-resolution light buffer, grade, vignette, grain, flashes). |
| [`remotion/src/gfx.ts`](remotion/src/gfx.ts), [`lib.ts`](remotion/src/lib.ts), [`data.ts`](remotion/src/data.ts) | 407 | The camera and glow helpers and textures; easing, noise and colour; the song data (lines, word times, beats, spectrum). |
| [`remotion/src/Film.tsx`](remotion/src/Film.tsx), [`Root.tsx`](remotion/src/Root.tsx) | 84 | The two compositions (16:9 and 9:16), fonts, and the song as preview audio in Remotion Studio. |
| [`remotion/prep.mjs`](remotion/prep.mjs) | 74 | Writes what the film reads into `remotion/public/` (generated, not in the repo): the timings, the spectrum, the fonts, a link to the song. |
| [`remotion/render.mjs`](remotion/render.mjs) | 63 | Headless renders: PNG stills of single moments, the silent masters, excerpts. |
| [`scene.py`](scene.py) | 128 | The bridge to the Python pipeline: reads the masters and adds the channel's 2D layer (captions, the subscribe pill, the end card), so `studio.render`, `studio.cuts`, `studio.thumbs` and `studio.safezone` work unchanged. Also computes the spectrum from the song (`spec`) and plans the 9:16 caption bands (`plan`). |

Captions are their own layer, drawn by `scene.py` over the caption-free master. Lines the world already shows are left
out: the hum, the CH2 "Rate limited, rate limited" (the wall etches it), "Three fifty-nine / fifty-eight" (the flip
clock), "Usage limit reached" (the wall) and all of Bridge 2 (his mint type).

## Render it

Needs Node 18+, Python with the studio's requirements, the fonts in `assets/fonts/` (see
[assets/fonts/README.md](../../assets/fonts/README.md)) and, for the finals, `Rate Limited (Remastered).wav` in
`MUSIC_DIR`. The timings are the original cut's, so no models are needed.

```bash
cd songs/rate-limited-the-wall/remotion && npm install
npm run studio                                   # live preview, with sound when the song is in MUSIC_DIR
npm run stills -- 16x9 ../build/stills 03-slam=26.2 04-seen=39.4   # PNG stills of single moments
npm run master -- 16x9                           # silent master: ../build/master_16x9.mp4 (add --width 2560 --height 1440 for 1440p)
npm run master -- 9x16                           #                ../build/master_9x16.mp4
cd ../../..
python3 songs/rate-limited-the-wall/scene.py spec    # optional: the spectrum from the remaster (else the original cut's)
python3 songs/rate-limited-the-wall/scene.py plan    # 9:16 caption bands, from the 9:16 master
python -m studio.safezone songs/rate-limited-the-wall
python -m studio.render songs/rate-limited-the-wall --fmt 16x9
python -m studio.render songs/rate-limited-the-wall --fmt 9x16
```

The finals go to their own folder, `MUSIC_DIR/Rate Limited (The Wall)/`, so they never overwrite the original cut's.
