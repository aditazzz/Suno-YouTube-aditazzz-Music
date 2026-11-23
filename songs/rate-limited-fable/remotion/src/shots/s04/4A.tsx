// 4A "Tried a new tab": slide along her wall from her door to the "new" door: it carries a browser-tab label (NEW DOOR x,
// baked) and he is already behind it, paddle up; the full drums land (48.92) on the arrival with a camera hit.
// PLATE: rl_cut1 a1 = S14 T9 (7800x2160 = stage 5200x1440: door 2 LEFT of door 1, so the slide runs right-to-left) +
// him_door1_region (him behind door 1, same pose, for the start). At s 1.32 the two hims are never in frame together
// except inside one motion-blurred frame of the whip.
import React from 'react';
import { useCurrentFrame } from 'remotion';
import { clamp, lerp, inOutSine } from '../../ease';
import { cueFrame } from '../../timing';
import { ShotDef, ShotProps } from '../types';
import { Cam, hit, MBlur, pulse } from '../s03/_lib';
import { A1, Lay, clampCam, c916f } from '../s03/_cut1a';

const K = 2 / 3, PW = 7800 * K;                                       // T9 px -> stage; plate width 5200
const HIM1 = { x: 5313 * K, y: 381 * K, w: 1051 * K, h: 1773 * K };   // layout.him_door1_box
const HIM_X = [(5313 + 6364) / 2 * K, (1680 + 2619) / 2 * K];         // him at door 1 / door 2 (layout boxes)
const CX = [3980, 1420];                                              // camera: on him at door 1 -> on him at door 2 (door 2 + its tab framed)
const S0 = 1.32;
const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame(); const g = shot.from + f;
  const drums = cueFrame(shot, 'drum') ?? 17;
  const k = (t: number) => inOutSine(clamp(t / (drums + 1)));
  const s = S0 * (1 + hit(f, drums, 0.018, 8) + pulse(g));
  return (
    <MBlur n={f <= drums ? 8 : 1} shutter={0.6} render={(dt) => {
      const c = clampCam(lerp(CX[0], CX[1], k(f + dt)), 760, s, 0, PW, 0, 1440);
      return (
        <Cam cx={c.cx} cy={c.cy} s={s} free>
          <Lay src={A1.T9} x={0} y={0} w={PW} h={1440} />
          <Lay src={A1.T9him1} x={HIM1.x} y={HIM1.y} w={HIM1.w} h={HIM1.h} />
        </Cam>
      );
    }} />
  );
};
export const S4_4A: ShotDef = { stage: Stage, cx916: (f, shot) => {
  const k = inOutSine(clamp(f / ((cueFrame(shot, 'drum') ?? 17) + 1)));
  return c916f(lerp(HIM_X[0], HIM_X[1], k), clampCam(lerp(CX[0], CX[1], k), 760, S0, 0, PW).cx, S0); } };
