// rl5_d cut 5: 4J and 11B on the same meter plate (S6 M1 + needle layer), CUT5_PLAN §3 4J "The meter, readable: needle at 19.
// (11B's plate, needle in code.) Slow push, dead centre" (her N24 "make it clear that we are looking at hours awake") and 11B
// "needle past 24, bent on the stop. Dead still" (so 11B's hold is the escalation of 4J's, not a repeat of its push).
import React from 'react';
import { useCurrentFrame } from 'remotion';
import { ShotDef, ShotProps } from '../types';
import { Cam } from '../first30/kit';
import { PL, Pl, clamp, lerp } from '../s10/_lib';
import { M1Needle, PlateDigit } from '../s11/_meter';
import { MeterCam916, CX916, CY916 } from '../s11/_meter916';
import { inOutSine } from '../../ease';
import { ioc } from './legacy';

// 11B's landing frame (16:9): dial rim .. plates bottom fill the height
const END = { cx: 1734, cy: 612, s: 1.55 };
const S4J: React.FC<ShotProps> = ({ shot, fmt }) => {
  const f = useCurrentFrame(); const k = ioc(f, 0, shot.dur - 1);
  const v = lerp(18.85, 19.05, inOutSine(clamp(f / shot.dur))) + 0.05 * Math.sin(f * 1.3);
  if (fmt === '9x16') return <MeterCam916 cx={CX916} cy={lerp(CY916 - 20, CY916, k)} s={lerp(0.86, 0.9, k)}><M1Needle v={v} /><PlateDigit f={f} at={1e9} from="0" to="0" /></MeterCam916>;
  return (
    <Cam cx={END.cx} cy={END.cy} s={lerp(1.45, 1.55, k)}>
      <Pl src={PL.M1} /><M1Needle v={v} /><PlateDigit f={f} at={1e9} from="0" to="0" />
    </Cam>
  );
};
const S11B: React.FC<ShotProps> = ({ shot, fmt }) => {
  const f = useCurrentFrame();
  const v = lerp(24.16, 24.3, inOutSine(clamp(f / shot.dur))) + 0.11 * Math.sin(f * 1.9) * (0.6 + 0.4 * Math.sin(f * 0.37)) + 0.04 * Math.sin(f * 4.3);
  if (fmt === '9x16') return <MeterCam916 cx={CX916} cy={CY916} s={0.9}><M1Needle v={v} /><PlateDigit f={f} at={1e9} from="0" to="0" /></MeterCam916>;
  return (
    <Cam cx={END.cx} cy={END.cy} s={END.s}>
      <Pl src={PL.M1} /><M1Needle v={v} /><PlateDigit f={f} at={1e9} from="0" to="0" />
    </Cam>
  );
};
export const C5_4J: ShotDef = { stage: S4J, cx916: () => 0.5 };
export const C5_11B: ShotDef = { stage: S11B, cx916: () => 0.5 };
