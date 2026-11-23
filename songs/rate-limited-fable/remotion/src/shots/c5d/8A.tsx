// rl5_d cut 5 8A (CUT5_PLAN §3 8A: "Walking home with Cooper: admire the car for a full bar (3691-3761), then the meter, held a full
// bar; its 4, 2, 9 tick on the sung digits (3778/3785/3797). No 429 on the buildings. One glide along the car, eases onto the meter";
// her N37 "Stay here no need to have the 429 on the building", N38 "Admire the car longer"). Cut 4e's L5 plates (the GT3 RS wide with
// her walk phases + the meter close); the old 8B (429 windows) is gone. No camera kicks: one eased glide left along the car toward the
// meter for the whole first bar, a cut on the downbeat that keeps the leftward drift, then a slow drift on the meter while it's read.
// rl5_c's meter digits (4, 2, 9 on the cues) go on top of the meter plate when they land.
import React from 'react';
import { AbsoluteFill, Img, staticFile, useCurrentFrame } from 'remotion';
import { clamp, lerp, inOutSine } from '../../ease';
import { ShotDef, ShotProps } from '../types';
import { Cam, Grain, flick, flickOut } from '../s07/_lib';
import { PlateImg } from '../first30/kit';
import l5 from '../first30/l5.json';
import { C4E, ioc } from './legacy';

const F = (l5 as any).A8.files as Record<string, string>;
export const CUT_METER_C5 = 70;                    // 3761: the downbeat after the first full bar
const RATES = (C4E['8A'].cues ?? []).map((c) => c.frame - C4E['8A'].from).slice(0, 3); // the three "Rate"s (0, 9, 17)

export type MeterLayer = React.FC<{ f: number; shot: ShotProps['shot'] }>;
export const make8A = (MeterTop?: MeterLayer): ShotDef => {
  const Stage: React.FC<ShotProps> = ({ shot, fmt }) => {
    const f = useCurrentFrame(); const g = shot.from + f; const v = fmt === '9x16';
    if (f >= CUT_METER_C5) {
      const k = inOutSine(clamp((f - CUT_METER_C5) / Math.max(1, shot.dur - 1 - CUT_METER_C5)));
      // arrives with the wide's leftward drift (the plate slides right on screen), decelerating to rest by the end
      const d = 1 - Math.pow(1 - Math.min(1, (f - CUT_METER_C5) / 40), 3);
      return (
        <AbsoluteFill>
          <Cam cx={lerp(1330, 1270, d)} cy={lerp(770, 790, k)} s={lerp(1.0, 1.035, k)}>
            <PlateImg src={`l5/${F.meter}`} />
            {MeterTop ? <MeterTop f={f} shot={shot} /> : null}
            <Grain g={g} k={0.035} />
          </Cam>
        </AbsoluteFill>
      );
    }
    const ind = RATES.reduce((m, r) => Math.max(m, f >= r && f < r + 8 ? (f < r + 4 ? flick(f, r) : flickOut(f, r + 4)) : 0), 0);
    const k = ioc(f, 0, CUT_METER_C5 + 12);         // still moving at the cut (the meter half picks up the drift)
    const s = v ? lerp(1.25, 1.32, k) : lerp(1.0, 1.24, k);
    const ph = f < (RATES[1] ?? 9) ? 'A' : f < (RATES[2] ?? 17) ? 'B' : 'C';
    return (
      <Cam cx={v ? 1180 : lerp(1300, 1020, k)} cy={v ? 760 : lerp(730, 790, k)} s={s}>
        <PlateImg src={`l5/${F.plate_cooper}`} />
        {F.ind ? <PlateImg src={`l5/${F.ind}`} opacity={ind} /> : null}
        <Img src={staticFile(`l1r/8A/walk_${ph}.png`)} style={{ position: 'absolute', left: 0, top: 0, width: 2560, height: 1440 }} />
        <AbsoluteFill style={{ opacity: ind * 0.10, background: 'rgb(255,168,64)', mixBlendMode: 'soft-light' }} />
        <Grain g={g} k={0.035} />
      </Cam>
    );
  };
  return { stage: Stage, cx916: (f) => (f >= CUT_METER_C5 ? 0.5 : 0.46) };
};
export const C5_8A = make8A();
