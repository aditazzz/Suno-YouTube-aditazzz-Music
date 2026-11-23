# Rate Limited: the film in code (Remotion)

The film is built in code on approved stills: camera moves and parallax on plates, screen inserts, clocks, neon
wording, type, light changes, cuts on the beat grid. No 3D animation here; a new pose is a new still (a plate).
Conventions follow `songs/run-it/remotion/`; `node_modules` is a symlink to Run It's (remotion 4.0.539), so no install.

## Layout

| Path | What |
|---|---|
| `tools/build_data.py` | Writes `src/data/shots.json`, `beats.json`, `words.json`. **Run after any change** to the shot list, plates or overrides (the render scripts run it too). |
| `plates_override.json` | Optional, per shot: `{"4C": {"plate": "door_jr", "cx916": 0.42, "move": "pushHard"}}` |
| `public/plates/` | The stills (`<key>.jpg`). Copies of approved frames; add new stills here under a new key. |
| `src/theme.tsx` | Stage size (2560x1440), fonts, text sizes (`SIZE`), palette, `useFmt()` |
| `src/timing.ts` | Shots, beat grid, words, `cueFrame`, `beatPulse`, `wordAt`, clock parsing |
| `src/ease.ts` | Easings (inOut, outBack, springy, fallBounce), `prog`, `noise1` |
| `src/blocks/` | `Plate`, `ScreenInsert`, `TextBox`/`Neon`/`Reveal`, `AnalogClock`/`DigitalClock`/`ShotClock`, `LightChange`, `CaptionLayer` |
| `src/shots/` | `index.ts` the registry, `Animatic.tsx` the default shot, your shots in `s<NN>/<ID>.tsx` |
| `src/Film.tsx` | Sequences every shot on its frames; reframes 9:16; caption layer; audio |
| `render_animatic.sh` | The animatic job (check stills + whole song at 720p with slates) |
| `render_range.sh` | Any frame range in either format through gpuq |

Data: shots come from `build/shots/shots.json` (rl_shots: beat-checked times, frames `[from, to)`, measured cues), with
each shot's "Grows from" frame from BOARDS. Beats: `bts_reel/work/beats_midi.json` + 0.23 s. Words: `build/words.json`.

## Compositions

- `Film16x9` 2560x1440 (props `{preview: true}` = 1280x720). `Film9x16` 1080x1920 (`preview` = 540x960).
- Props: `noAudio` (**default true**: renders are silent and the song is muxed with ffmpeg afterwards, as
  `render_animatic.sh` does; Remotion's bundle 404s on the symlinked `public/song.wav`, the Studio preview still plays it), `captions` (the caption line, **off** by default; its own layer),
  `slate` (shot id / clock / "new picture" cards: animatics only, never finals).
- 9:16 is a reframe of the same stage: scaled to 1920 tall and cropped around the shot's `cx916` (0..1 of the stage
  width). Text that must sit in the 9:16 safe zone goes in the shot's `screen` layer (below), not on the stage.

## Adding a shot (section workers)

1. Read your shots in `build/codeplan/codeplan.json` (rl_codeplan) and `src/data/shots.json` (times, cues, plate).
2. New stills: put them in `public/plates/<key>.jpg`; point the shot at one with `plates_override.json` if it is
   the main plate; run `python3 tools/build_data.py`.
3. Write `src/shots/s<NN>/<ID>.tsx` exporting a `ShotDef` (`src/shots/types.ts`):

```tsx
import React from 'react';
import { useCurrentFrame } from 'remotion';
import { Plate } from '../../blocks/Plate';
import { ScreenInsert } from '../../blocks/ScreenInsert';
import { Neon, igniteAt, TextBox } from '../../blocks/Type';
import { ShotClock } from '../../blocks/Clock';
import { cueFrame } from '../../timing';
import { outCubic } from '../../ease';
import { ShotDef, ShotProps } from '../types';

const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame();                         // shot-local frame (0 = the cut)
  const on = cueFrame(shot, 'green') ?? 20;            // measured word onset from rl_shots, not the lyric sheet
  return (
    <Plate src="plates/dawn.jpg" dur={shot.dur} move={{ s: [1.0, 1.1], y: [0.02, -0.01] }} ease={outCubic}
           layers={[{ mask: 'plates/masks/dawn_fg.png', depth: 0.5 }]}>
      <Neon text="DKWHEEL" x={1280} y={210} size={120} on={igniteAt(f, on)} />   {/* rides the camera */}
      <ShotClock shot={shot} kind="analog" cx={2100} cy={520} r={90} />
    </Plate>
  );
};
const Screen: React.FC<ShotProps> = ({ fmt }) => (           // optional: screen-space, per format
  <TextBox x={fmt === '16x9' ? 120 : 98} y={fmt === '16x9' ? 1180 : 1080} w={800} h={110} size={38}>RETRY-AFTER: 6h</TextBox>
);
export const S1_1B: ShotDef = { stage: Stage, screen: Screen, cx916: (f) => 0.5 - 0.1 * Math.min(1, f / 60) };
```

4. Register it in `src/shots/index.ts`: `import { S1_1B } from './s01/1B';` and `'1B': S1_1B,`. Everything not
   registered keeps playing the animatic plate, so the film always renders end to end.
5. Rules that keep the film consistent: every frame a pure function of `useCurrentFrame()` (no state, no
   `Math.random`, use `noise1`); nothing pops in (fade/scale in over >= 4 frames, `animation-principles`); a light
   is the only thing that glows; text sizes from `SIZE` (lyrics 64, others >= 34 at 1440; `TextBox` enforces the
   floor); keep highlights below clipping (her note: no blown-out highlights). Insert corners are measured on the
   plate at its rest framing (the still's own pixels scaled to 2560x1440); put the insert inside `<Plate>` so it moves
   with the camera.

### Blocks in one line each

- `Plate src dur move ease delay layers grade` eased push/pan/drift (presets `hold push pushHard pull driftL driftR
  rise fall`, or `{s,x,y,r}` pairs); `layers` = parallax from mask PNGs (white = layer, feathered edges).
- `ScreenInsert corners w h src|children glare light` 4-corner pin (TL, TR, BR, BL stage px); `lerpQuad` to animate.
- `TextBox x y w h size kind bg align valign` the box text_fit_check measures; `Neon text x y size on`;
  `igniteAt(f, at)`; `Reveal text start len` word-by-word.
- `AnalogClock / DigitalClock minutes`, `ShotClock shot`, `clockAt(shot, f)` (BOARDS clock range, eased).
- `LightChange a b at len flicker` grade crossfade.
- Timing: `cueFrame(shot, 'nine')`, `wordAt('green', after)`, `beatPulse(t)`, `sinceBeat`, `beatAtOrAfter`,
  `downbeatAtOrAfter`, `barBeat('12.3')` (seconds; `frameOf(t) - shot.from` for shot-local frames).

## Rendering (always through the GPU queue, one job, detached)

```bash
# a look at your shots (half size, silent): frames from src/data/shots.json
nohup env PREVIEW=1 ./render_range.sh 16x9 <from> <to> ../build/codecut/<you>_<ids>.mp4 rl_<you> > /dev/null 2>&1 &
# one still
npx remotion still src/index.ts Film16x9 out.jpg --frame=<f> --props='{"preview":true}'
# the whole animatic again (tag = version)
nohup ../../../tools/gpuq.sh rl_remotion bash -c "$PWD/render_animatic.sh v1" > /dev/null 2>&1 &
```

Check that your job's log appears in `logs/gpuq/`. Before DONE: `python3 tools/text_fit_check.py` on your frames,
one contact sheet <= 1600 px, and a sweep of every frame of your shots at delivery size (render-checks skill).

## Masters (later)

Silent 16:9 at 2560x1440 and 9:16 at 1080x1920 (`noAudio`), linked as `build/video_16x9_1440.mp4` /
`build/video_9x16.mp4`, then `studio.render --fmt 16x9_1440 --finals-only` etc. (see the studio CLAUDE.md).
