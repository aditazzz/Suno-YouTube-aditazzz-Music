// 12D "Right in the middle of my grind" (cut 4, lane L2; her #31 note): the faint, a full silent-film swoon: the back of her wrist to her brow,
// knees going (l2/12D_sway); on the beat she lands flat out on the sofa, and Cooper flops down beside her in the exact same pose, paw on his
// forehead (l2/12D_flop). The landing is a thump: a camera hit.
import React from 'react';
import { useCurrentFrame } from 'remotion';
import { ShotDef, ShotProps } from '../types';
import { Cam, hit } from '../first30/kit';
import { L2Img, beat } from '../l2kit';
import { FixPlate } from '../c7/fix713/FixPlate';   // rl7_fixb: neon in the tube family baked into the plate
import { clamp, inOutSine, lerp } from '../../ease';

const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame(); const b2 = beat(shot, 2, 35);
  if (f < b2) { const k = inOutSine(clamp(f / (b2 - 1))); return <Cam cx={1280} cy={720} s={lerp(1.0, 1.05, k)} r={lerp(0, -0.6, k)}><FixPlate src="c7/apt/12D_sway_ban.jpg" /></Cam>; }
  const k = inOutSine(clamp((f - b2) / (shot.dur - 1 - b2)));
  return <Cam cx={1280} cy={720} s={lerp(1.02, 1.06, k) * (1 + hit(f, b2, 0.022, 12))}><FixPlate src="c7/apt/12D_flop_ban.jpg" /></Cam>;
};
export const S12_12D: ShotDef = { stage: Stage, cx916: () => 0.5 };
