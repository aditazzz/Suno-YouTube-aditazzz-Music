// 13B "Welcome back" (cut 4, lane L2; her #37 note, §2g): the door swings open, warm light floods her, he gives the small bow (1I in
// reverse) (l2/13B_open); one beat outside: the grey building comes back to colour floor by floor (L5's Ext13B, the reverse of 1H); then
// she runs through into the lobby, arms up, Cooper bounding after her (l2/13B_run).
import React from 'react';
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { ShotDef, ShotProps } from '../types';
import { Cam, hit } from '../first30/kit';
import { Ext13B, HAVE_13B_EXT } from './13B_ext';
import { L2Img, beat } from '../l2kit';
import { clamp, inOutSine, lerp } from '../../ease';

const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame(); const g = shot.from + f;
  // rl_cut4_fix (rl_watch4 13B: the 0.4 s greyscale insert read as a grading glitch): the exterior holds 28 f (~0.9 s) and plays at 1.5x so every
  // floor comes back to colour (L5's floors at 4..24, rest 29); the run starts after it (its hit moves with it).
  const b1 = beat(shot, 1, 17), b2 = b1 + 28, XS = 1.5;
  if (f < b1) {
    const k = inOutSine(clamp(f / (b1 - 1))); const flood = clamp(f / 8);
    return <Cam cx={1280} cy={720} s={lerp(1.0, 1.04, k)}><L2Img id="13B_open" style={{ filter: `brightness(${lerp(0.8, 1.0, flood).toFixed(3)})` }} /></Cam>;
  }
  if (f < b2 && HAVE_13B_EXT) return <AbsoluteFill><Ext13B f={(f - b1) * XS} dur={(b2 - b1) * XS} g={g} /></AbsoluteFill>;
  const k = inOutSine(clamp((f - b2) / (shot.dur - 1 - b2)));
  return <Cam cx={1280} cy={720} s={lerp(1.03, 1.10, k) * (1 + hit(f, b2, 0.012, 10))}><L2Img id="13B_run" /></Cam>;
};
export const S13_13B: ShotDef = { stage: Stage, cx916: () => 0.5 };
