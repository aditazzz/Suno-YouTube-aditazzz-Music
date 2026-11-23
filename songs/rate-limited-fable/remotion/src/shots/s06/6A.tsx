// 6A "Three fifty-nine": the wall clock's second hand ticks on the side-stick.
// rl_fix2_robot (WATCH blockers: 2E/6A/6D were the same still wide; his seated head floated over a heap of parts): plate FX.B2B
// (the approved Rain B2B with its left strip - QUIET HOURS, him, the 429 stand, the door edge - re-rendered at 2x with him in the new
// seat: back on the door, legs out, head square on a readable neck). New picture: it opens CLOSE on the clock at 3:59 and the QUIET
// HOURS sign (the ticks on the eighths), then on the bar's second half tilts down to him sitting against the door, the 429 parked
// beside him, her upside-down stand just through the glass. No beat pulse: the dead hour. The clock is code (face + hands).
import React from 'react';
import { useCurrentFrame } from 'remotion';
import { ShotDef, ShotProps } from '../types';
import { Cam, PlateImg, ez } from '../s03/_lib';
import { lerp } from '../../ease';
import { B2B_CLOCK, WallPanda, pt } from '../../blocks/PandaClock';
const WALLCLOCK = { x: B2B_CLOCK.cx, y: B2B_CLOCK.cy };
import { FX } from '../s11/_fix2';
import { outX } from '../s11/_meter';

const HEAD = { x: 858.7 * 2560 / 2880, y: 1150.5 * 2560 / 2880 };     // his head in the new seat (blender/b2b/layout.json head_px)
const camAt = (f: number, dur: number) => {
  const k = ez(f, 24, dur - 12);
  return { cx: lerp(560, 840, k), cy: lerp(330, 975, k), s: lerp(2.0, 1.55, k) * (1 + 0.012 * f / dur) };
};
const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame();
  const t0 = (shot.cues ?? []).find((c) => c.word === 'side-stick')?.frame ?? shot.from + 9;
  const ticks = Math.max(0, Math.floor((shot.from + f - t0) / 8.7) + 1);   // eighth notes
  const c = camAt(f, shot.dur);
  return (
    <Cam cx={c.cx} cy={c.cy} s={c.s}>
      <PlateImg src={FX.B2B} />
      {/* rl_l3_ui (cut 4, §2a): the panda wall clock at 3:59, its red chrono hand ticking on the side-stick */}
      <WallPanda at={B2B_CLOCK} time={pt(3, 59)} chrono={(28 + ticks) % 60} running={(28 + ticks) % 60} uid="a6" />
    </Cam>
  );
};
export const S6_6A: ShotDef = {
  stage: Stage,
  // 9:16: the clock, then his head
  cx916: (f, shot) => { const c = camAt(f, shot.dur); const k = ez(f, 24, shot.dur - 12); return Math.min(1, Math.max(0, outX(lerp(WALLCLOCK.x, HEAD.x, k), c.cx, c.s) / 2560)); },
};
