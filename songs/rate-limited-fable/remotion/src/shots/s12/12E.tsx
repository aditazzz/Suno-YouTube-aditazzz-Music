// 12E "You gave me everything / Now you give me nothing" (cut 4, lane L2; her #32 note): her and Cooper side by side at the coffee table, chins
// on it, enormous eyes on the closed laptop; then she blows a curl off her face and he sighs, ears lifting. The neon above, readable on the
// dark wall. Plates: l2/12E_stare -> l2/12E_blow (one camera), the slowest push of the film.
import React from 'react';
import { useCurrentFrame } from 'remotion';
import { ShotDef, ShotProps } from '../types';
import { Cam } from '../first30/kit';
import { L2Img, beat, settle } from '../l2kit';
import { FixPlate } from '../c7/fix713/FixPlate';   // rl7_fixb: neon in the tube family baked into the plate
import { L2Q } from '../l2data';
import { clamp, inOutSine, lerp } from '../../ease';

const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame(); const b5 = beat(shot, 5, 87);
  const k = inOutSine(clamp(f / (shot.dur - 1)));
  const h = (L2Q['12E_stare']?.head as [number, number] | undefined) ?? [1000, 880];      // her face on the plate: the push ends between her and Cooper, the laptop in
  const tx = h[0] + 170, ty = h[1] + 60;
  return <Cam cx={lerp(1280, tx, k)} cy={lerp(720, ty, k)} s={lerp(1.0, 1.36, k) * (1 + settle(f, b5, 0.005))}><FixPlate src={f < b5 ? 'c7/apt/12E_stare_ban.jpg' : 'c7/apt/12E_blow_ban.jpg'} /></Cam>;
};
export const S12_12E: ShotDef = { stage: Stage, cx916: () => 0.45 };
