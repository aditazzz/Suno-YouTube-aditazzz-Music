// 13D "Where were we" (CODEPLAN): very close on the brass plates of the meter. On the last hit the GLASSES OF WATER
// digit flips 0 -> 1 (split-flap, 6 frames) with a 1% camera hit. Plate: S6 M1 (plate digit blank; digits are code),
// box from its layout.json (right-aligned at 2253.7, 861.7 on the stage).
// rl_fix2_robot (WATCH blocker, 9:16 only: the crop read "ER 1 / TUESDAY"): 9:16 has its own framing; 16:9 unchanged.
// rl_fix3_qa1 (QA3: in 9:16 the "1", the film's payoff, sat at x ~0.92 in the like column): 9:16 now uses the same meter
// framing as 11B's end (../s11/_meter916, s 0.88 -> 0.893 + the hit, max ~0.907): the "1" at ~0.79 of the width, GLASSES at
// ~0.10, plates above 68% height, the dial above and the six untouched glasses on the shelf below. The dial is in the
// 9:16 frame now (16:9 never shows it), so it needs its needle: just past 0 (NEEDLE_916; 6:01, the morning after the
// 6:00 reset; director's call, one constant: 21.2 would continue 11B's reading instead).
import React from 'react';
import { useCurrentFrame } from 'remotion';
import { ShotDef, ShotProps } from '../types';
import { cueFrame } from '../../timing';
import { Cam, hit } from '../first30/kit';
import { PL, Pl, lerp, pulse } from '../s10/_lib';
import { inOutSine } from '../../ease';
import { M1Needle, PlateDigit } from '../s11/_meter';
import { MeterCam916, CX916, CY916 } from '../s11/_meter916';

const NEEDLE_916 = 0.4;
const cam = (fmt: string, k: number) => fmt === '9x16'
  ? { cx: CX916, cy: CY916, s: lerp(0.88, 0.893, inOutSine(k)) }
  : { cx: lerp(2010, 1985, inOutSine(k)), cy: 866, s: 2.85 };
const Stage: React.FC<ShotProps> = ({ shot, fmt }) => {
  const f = useCurrentFrame(); const g = shot.from + f;
  const at = Math.max(0, (cueFrame(shot, 'last hit') ?? shot.from + 1) - shot.from);
  const k = Math.min(1, f / (shot.dur - 1)); const c = cam(fmt, k);
  const s = c.s * (1 + hit(f, at + 3, 0.01, 10)) * pulse(g);
  if (fmt === '9x16') return (
    <MeterCam916 cx={c.cx} cy={c.cy} s={s}>
      <M1Needle v={NEEDLE_916 + 0.03 * Math.sin(f * 1.3)} />
      <PlateDigit f={f} at={at} from="0" to="1" />
    </MeterCam916>
  );
  return (
    <Cam cx={c.cx} cy={c.cy} s={s}>
      <Pl src={PL.M1} />
      <PlateDigit f={f} at={at} from="0" to="1" />
    </Cam>
  );
};
export const S13_13D: ShotDef = { stage: Stage, cx916: () => 0.5 };
