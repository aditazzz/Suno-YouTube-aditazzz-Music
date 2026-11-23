// 2B, the paddle (first30.md + HEROES.md): close on him through the clean glass, drawer open, paddle below frame, a
// slow push; on "nine" the 429 paddle comes up beside his head (H1 PADDLE frames 724-766 when they land; until then the
// C0 -> C0s (2 frames) -> C1 pose swap), with the chorus hit (1.5% in, settle). Lobby clock digits in code, blurred to
// the plate's focus. Plates: S8 C0/C0s/C1 (rl_stills; previews until the finals land), positions from its layout.json.
import React from 'react';
import { useCurrentFrame } from 'remotion';
import { clamp, inOutSine, lerp } from '../../ease';
import { ShotDef, ShotProps } from '../types';
import { cueFrame } from '../../timing';
import { ScreenInsert, Quad } from '../../blocks/ScreenInsert';
import { FONT } from '../../theme';
import { Cam, HeroClip, PlateImg, heroReady, hit, keys, swap } from './kit';
import heroes from './heroes.json';
import assets from './assets.json';

const lay = (assets as any).S8_C_layout; const K = 2560 / lay.size[0];
const CLOCK = lay.clock.corners_TL_TR_BR_BL.map(([x, y]: number[]) => [x * K, y * K]) as Quad;
/** the C1 preview from rl_stills lacks the 429 print (their 11:10 note: fixed in job 2); draw it in code until then */
const PADDLE_429_IN_CODE = (assets as any).C1?.kind === 'preview';
const PAD = [lay.paddle_face_centre_C1[0] * K, lay.paddle_face_centre_C1[1] * K];

// rl_l3_ui (cut 4, §2a): the lobby display on the S8 close plates is now the panda wall clock (out of focus behind his head, masked
// behind the raised paddle). Same props as before, so every shot that imports this LobbyClock (2G, 12B, 12G) gets the panda.
import { PandaLobbyClockS8 } from '../../blocks/PandaClock';
export const LobbyClock = PandaLobbyClockS8;
void CLOCK; void ScreenInsert; void FONT;

const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame(); const g = shot.from + f;
  const nine = cueFrame(shot, 'nine') ?? 36;
  const st = swap(f, nine, 2);
  const s = lerp(1.0, 1.045, clamp(f / (shot.dur - 1))) * (1 + hit(f, nine + 1, 0.015, 14));
  const src = st === 'A' ? 'first30/C0.jpg' : st === 'S' ? 'first30/C0s.jpg' : 'first30/C1.jpg';
  return (
    <Cam cx={1280 + (s - 1) * 1250} cy={720} s={s}>   {/* the push leans toward the paddle so it never leaves frame */}
      <HeroClip id="H1" g={g} fallback={<PlateImg src={src} />} />
      {st === 'B' && PADDLE_429_IN_CODE ? (
        <div data-fit="off" style={{ position: 'absolute', left: PAD[0], top: PAD[1], transform: 'translate(-50%,-50%) rotate(2deg)', fontFamily: FONT.head, fontWeight: 900,
          fontSize: 150, color: '#c8352b', letterSpacing: '0.01em', filter: 'blur(0.6px)' }}>429</div>
      ) : null}
      <LobbyClock text="2:05" />
    </Cam>
  );
};
// v3 (rl_first30_v3, CD V3 order 1): the cam2 take of the approved H1 acting (rl_h1cam2: 704-773, the camera move, the red
// light kick and the 2:05 are all in the render). Code keeps only a 1-frame 0.6% tick on 740; no code push, hit or clock.
// 9:16: the crop follows the take's own track (heroes.json H1b.track, measured from the frames) onto the 429 disc.
const H1B = (heroes as any).H1b as { track?: [number, number][] } | undefined;
// rl_l3_ui (cut 4, FIX4_PLAN §2a "the digital box on the door frame is removed everywhere ... a panda wall clock covers its spot"):
// the same H1b take with the panda wall clock (2:05) composited over the box, behind his head and the paddle, defocused like the
// wall and smeared through the whip (workers/rl_l3_ui/tools/panda_h1b.py: box track + foreground matte). Frames: l3/H1b_panda.
const StageB: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame(); const g = shot.from + f;
  const nine = cueFrame(shot, 'nine') ?? 36;
  const s = 1 + (f === nine ? 0.006 : 0);
  const fr = Math.round(clamp(g, 704, 773));
  return (
    <Cam cx={1280} cy={720} s={s}>
      <PlateImg src={`l3/H1b_panda/f_${String(fr).padStart(5, '0')}.jpg`} />
    </Cam>
  );
};
const trackX = (f: number, shot: ShotProps['shot']) => keys(shot.from + f, (H1B?.track ?? [[704, 0.47], [742, 0.6]]) as [number, number][], inOutSine);
// 9:16 (v2): on his face, then the crop slides to the paddle as it comes up
export const S2_2B: ShotDef = heroReady('H1b')
  ? { stage: StageB, cx916: trackX }
  : { stage: Stage, cx916: (f, shot) => { const n = (cueFrame(shot, 'nine') ?? 36); return lerp(0.47, 0.84, inOutSine(clamp((f - n) / 10))); } };
