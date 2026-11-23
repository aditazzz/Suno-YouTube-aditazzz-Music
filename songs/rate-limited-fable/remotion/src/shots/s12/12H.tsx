// 12H "Rate, rate, rate limited" (fix round 4, rl_l5_street; her cut 3 note: "When we show the car we should really show it off.")
// L5 12H (build/stills/L5_12H, blrl4_street): the car beauty at 5:59, predawn. A real slow dolly, rendered frame by frame in Cycles: low
// (0.85 m) on the wet road off her front-left corner, 22 mm at f/2.8, tracking 0.75 m along her flank toward the tail while the frame stays
// on her: Ultraviolet paint with the rose-and-blue sky in it, yellow calipers, DKWHEEL on the Texas front plate, the wet road reflecting her
// and the lamps, the panda post clock at 5:59 soft above her roof, the expired meter by her nose (still 429). Claps only: a beat pulse.
// Falls back to the cut 3 plate (S20 NS5 predawn + tail) if the frames are missing. NS5Tail / NS5_CLOCK stay exported (13B uses them).
import React from 'react';
import { useCurrentFrame } from 'remotion';
import { ShotDef, ShotProps } from '../types';
import { Cam, PlateImg } from '../first30/kit';
import { Lay, PL, Pl, WallClock, clamp, lerp, pulse } from '../s10/_lib';
import { inOutSine } from '../../ease';
import l5 from '../first30/l5.json';

const K = 2560 / 2880;
export const NS5_CLOCK = { cx: 980.8 * K, cy: 1186.3 * K, r: 28 };      // layout clock.pivot; face r 33 px (2880) = 29.6 stage
/** the cat's tail (S20 tail.png at region 19,0 .. 999,264; pivot 484.6,-950 above the frame); g = film frame */
export const NS5Tail: React.FC<{ g: number; lit?: number }> = ({ g, lit = 0 }) => (
  <div style={{ position: 'absolute', inset: 0, transformOrigin: `${484.6 * K}px ${-950 * K}px`, transform: `rotate(${(2.2 * Math.sin((2 * Math.PI * g) / 84)).toFixed(3)}deg)`,
    filter: lit > 0 ? `brightness(${1 + 0.35 * lit}) saturate(${1 + 0.15 * lit})` : undefined }}>
    <Lay src="cut1/c/tail.png" k={K} x={19} y={0} w={980} h={264} />
  </div>
);

const H12 = (l5 as any).H12 as undefined | { frames: number };
const NF = H12?.frames ?? 0;
/** the dolly frame for shot-local frame f (the render has one frame per film frame; fewer = a preview, held) */
const frameSrc = (f: number, dur: number) => {
  const i = NF >= dur ? clamp(Math.round(f), 0, NF - 1) : clamp(Math.round((f / Math.max(1, dur - 1)) * (NF - 1)), 0, NF - 1);
  return `l5/12H/f_${String(i + 1).padStart(4, '0')}.jpg`;
};

const StageL5: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame(); const g = shot.from + f;
  return (
    <Cam cx={1280} cy={720} s={pulse(g)}>
      <PlateImg src={frameSrc(f, shot.dur)} />
    </Cam>
  );
};

const StageCut3: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame(); const g = shot.from + f;
  const k = inOutSine(clamp(f / (shot.dur - 1)));
  return (
    <Cam cx={lerp(1300, 1220, k)} cy={lerp(720, 760, k)} s={lerp(1.0, 1.07, k) * pulse(g)}>
      <Pl src={PL.PREDAWN} />
      <NS5Tail g={g} />
      <WallClock cx={NS5_CLOCK.cx} cy={NS5_CLOCK.cy} r={NS5_CLOCK.r} hr={5} min={59} face={false} blur={0.6} />
    </Cam>
  );
};
export const S12_12H: ShotDef = NF > 0 ? { stage: StageL5, cx916: () => 0.45 } : { stage: StageCut3, cx916: () => 0.5 };
