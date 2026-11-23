// 5D "Right in the middle of my grind": the queue.
// rl_l4_props (cut 4, her notes f2555: "I don't get what those papers are saying or doing" / "the sign ... going off the wall and so are
// the papers ... sunny requests and more personality"): no rack, no slips, no wall sign. Her scheduled requests are little clay people in
// sunny outfits camped out in a line at his desk like a launch-day queue, waiting for 6:00, each with a number bib continuing her ticket 41
// (1E): 42 in a beach chair (sun hat, shades, a thermos), 43 asleep in a sleeping bag (nightcap), 44 doing the crossword, 45 with a thermos,
// 46 in shades on tiptoe. One rendered plate (L4_5D_Q, the lobby set whole: no composited wall patch). A slow drift along the line from
// its far end to the front of the queue.
import React from 'react';
import { useCurrentFrame } from 'remotion';
import { clamp, lerp, inOutSine } from '../../ease';
import { ShotDef, ShotProps } from '../types';
import { Cam, PlateImg, Vignette, Grain, pulse } from '../s03/_lib';
import { L4IMG, L4LAY } from '../l4data';

const K = 2560 / 2880;
const P = L4LAY['5D'].people as Record<string, number[]>;
const ctr = (b: number[]) => [(b[0] + b[2]) / 2 * K, (b[1] + b[3]) / 2 * K];
const FAR = ctr(P['46'] ?? [1800, 700, 2000, 900]), NEAR = ctr(P['42'] ?? [900, 700, 1300, 1300]);
const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame(); const g = shot.from + f;
  const k = inOutSine(clamp(f / Math.max(1, shot.dur - 1)));
  const cx = lerp(lerp(1280, FAR[0], 0.35), lerp(1280, NEAR[0], 0.35), k), cy = lerp(lerp(720, FAR[1], 0.25), lerp(720, NEAR[1], 0.25), k);
  return (
    <Cam creep={f / shot.dur} cx={cx} cy={cy} s={lerp(1.03, 1.10, k) * (1 + pulse(g))}>
      <PlateImg src={L4IMG.D5_Q.src} />
      <Vignette k={0.35} />
      <Grain g={g} />
    </Cam>
  );
};
// 9:16 (vertical later: not re-checked this round): follow the drift
export const S5_5D: ShotDef = { stage: Stage, cx916: (f, shot) => { const k = inOutSine(clamp(f / Math.max(1, shot.dur - 1))); return lerp(FAR[0], NEAR[0], k) / 2560; } };
