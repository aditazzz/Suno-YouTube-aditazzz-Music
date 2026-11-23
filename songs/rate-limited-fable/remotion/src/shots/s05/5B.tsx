// 5B "Hit me with a four-two-nine": he gives the cat (on his desk) a green 200 OK, then on "nine" turns to the glass with the
// 429 (A-smear-B), chorus hit (1.5% in 3 frames, settle).
// PLATE (rl_cut1 a2): S21g T13a (cat on his desk + green 200 OK) -> T13s (turn smear) -> T13b (429 up, 1.4x). The code paddle
// is gone (baked); no lobby clock (in T13 the clock sits behind his hair).
import React from 'react';
import { useCurrentFrame } from 'remotion';
import { clamp, lerp } from '../../ease';
import { cueFrame } from '../../timing';
import { ShotDef, ShotProps } from '../types';
import { Cam, PlateImg, swap, hit, c916 } from '../s03/_lib';
import { IMG, K } from './_cut1b';

const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame();
  const nine = cueFrame(shot, 'nine') ?? 36;
  const st = swap(f, nine, 2);
  const s = lerp(1.0, 1.04, clamp(f / (shot.dur - 1))) * (1 + hit(f, nine + 1, 0.015, 8));
  return (
    <Cam creep={f / shot.dur} cx={lerp(1180, 1420, clamp((f - nine) / 6))} cy={640} s={s}>
      <PlateImg src={IMG[st === 'A' ? 'T13a' : st === 'S' ? 'T13s' : 'T13b'].src} />
    </Cam>
  );
};
// 9:16: the green 200 + the cat, then the 429 (green_box / red_box centres of the T13 layout)
export const S5_5B: ShotDef = { stage: Stage, cx916: (f, shot) => {
  const n = cueFrame(shot, 'nine') ?? 36; const k = clamp((f - n) / 8);
  return c916(lerp(1100 * K, 1887 * K, k), lerp(1180, 1420, clamp((f - n) / 6)), 1);
} };
