// 11B "The limit was never for me" (CODEPLAN): the reveal. rl_fix2_robot (WATCH blocker: the meter was small in the top right and the
// plates ~8 px tall on a phone; 9:16 showed only wall): now on the S6 M1 plate (5760 px, digit blank) with its needle layer, a push
// in that stops dead on "never" (measured) with the dial and both plates filling the frame: HOURS AWAKE, GLASSES OF WATER 0,
// LAST MEAL TUESDAY read at phone size (plate caps ~51 px at 1920). The needle keeps creeping deeper into the red with a tremble (the
// camera itself is dead still after the stop; p1's sweep read the hold as a freeze).
// rl_fix3_qa1 (QA3): (1) the 1-frame pop at the cut (f5148 -> 5149 jumped ~24% of the push: outQuint is fastest at frame 0):
// the push now eases in from the cut frame (outQuint of u^1.5: 6% of the move on the first frame, peak ~12%/frame around
// frame 4) and still stops dead on "never". (2) 9:16: own framing on the extended meter column (./_meter916): the dial over
// both plates, every plate word inside 10-79% of the width (the "0" out of the like column) and the plates above 68% height.
import React from 'react';
import { useCurrentFrame } from 'remotion';
import { ShotDef, ShotProps } from '../types';
import { cueFrame } from '../../timing';
import { Cam } from '../first30/kit';
import { PL, Pl, clamp, lerp } from '../s10/_lib';
import { M1Needle, PlateDigit } from './_meter';
import { MeterCam916, CX916, CY916 } from './_meter916';
import { inOutSine, outQuint } from '../../ease';

const frameOf = (fmt: string, k: number) => fmt === '9x16'
  ? { cx: lerp(CX916 + 7, CX916, k), cy: lerp(CY916 - 30, CY916, k), s: lerp(0.85, 0.9, k) }   // 9:16: dial + plates, plates bottom 68% -> 67%
  : { cx: lerp(1560, 1734, k), cy: lerp(700, 612, k), s: lerp(1.06, 1.55, k) };   // 16:9: dial rim .. plates bottom fill the height
const stopOf = (shot: ShotProps['shot']) => Math.max(8, (cueFrame(shot, 'never') ?? shot.from + 19) - shot.from);
/** the push: eases in from the cut (no first-frame jump), decelerates to a dead stop on "never" */
const pushK = (f: number, shot: ShotProps['shot']) => outQuint(Math.pow(clamp(f / stopOf(shot)), 1.5));

const Stage: React.FC<ShotProps> = ({ shot, fmt }) => {
  const f = useCurrentFrame();
  const c = frameOf(fmt, pushK(f, shot));
  // rl_l3_ui (cut 4, S21 "the needle goes down"): past 24 and pressed against the stop pin (it was 20-21 here, lower than 1G's 24):
  // the needle strains a hair beyond the pin, trembling (one meter timeline: ~19 at 1G, ~20 at 4J, past 24 at 5:40)
  const v = lerp(24.16, 24.3, inOutSine(clamp(f / shot.dur))) + 0.11 * Math.sin(f * 1.9) * (0.6 + 0.4 * Math.sin(f * 0.37)) + 0.04 * Math.sin(f * 4.3);
  if (fmt === '9x16') return (
    <MeterCam916 cx={c.cx} cy={c.cy} s={c.s}>
      <M1Needle v={v} />
      <PlateDigit f={f} at={1e9} from="0" to="0" />
    </MeterCam916>
  );
  return (
    <Cam cx={c.cx} cy={c.cy} s={c.s}>
      <Pl src={PL.M1} />
      <M1Needle v={v} />
      <PlateDigit f={f} at={1e9} from="0" to="0" />
    </Cam>
  );
};
// 9:16: the meter camera already centres the plates; the crop stays centred
export const S11_11B: ShotDef = { stage: Stage, cx916: () => 0.5 };
