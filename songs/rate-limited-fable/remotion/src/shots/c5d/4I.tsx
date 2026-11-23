// rl5_d2 cut 5 4I (2129-2233): rl5_b's re-render (c5/4I, her N23: no nightcap, pom-pom or cables; racks calm, green lights, nothing
// dangling). Line 1: T12a, the closet open, his "see?". Line 2 (grid beat 3, as cut 4e): T12b, turned back to her, eyes kind, open hand
// toward the meter (off right). Plan: slow push, turns with him: the camera eases in toward the racks on line 1, then carries right
// onto him on line 2 (no punch, no snore glow: nothing in the closet moves).
import React from 'react';
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { ShotDef, ShotProps } from '../types';
import { Cam, PlateImg, gb, c916 } from '../s03/_lib';
import { lerp } from '../../ease';
import { ioc } from './legacy';
import { Grain2 } from '../../blocks/real/Scene';

// stage px (plate 3840 -> /1.5): doorway x 643-1507, him x 1433-2557
const tl = (f: number, shot: ShotProps['shot']) => {
  const cut = gb(shot as any, 3) - 1;
  const s = lerp(1.03, 1.10, ioc(f, 0, shot.dur - 1));
  const cx = f < cut ? lerp(1240, 1170, ioc(f, 0, cut)) : lerp(1170, 1440, ioc(f, cut, shot.dur - 1));
  const cy = lerp(730, 700, ioc(f, 0, shot.dur - 1));
  return { cut, cx, cy, s };
};
const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame(); const t = tl(f, shot);
  return (
    <AbsoluteFill>
      <Cam cx={t.cx} cy={t.cy} s={t.s}><PlateImg src={f < t.cut ? 'c5/4I/T12a.jpg' : 'c5/4I/T12b.jpg'} /></Cam>
      <Grain2 f={f} />
    </AbsoluteFill>
  );
};
export const C5_4I: ShotDef = { stage: Stage, cx916: (f, shot) => { const t = tl(f, shot); return c916(t.cx, t.cx, t.s); } };
