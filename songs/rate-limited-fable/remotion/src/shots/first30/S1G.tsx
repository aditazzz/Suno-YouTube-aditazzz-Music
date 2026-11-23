// 1G, the needle (first30.md): very close on the dial. rl_fix2_open: a macro of the RED ZONE ONLY, from the full-res dial crop
// (dial.tsx): hub at the left edge, ticks 20-24 and the red pin on the right; the HOURS AWAKE label and the plates never enter
// the frame (the 11B twist stays hidden; check_dial.py). The needle creeps the last hair, touches the red pin on beat 2 with a
// 2-frame bounce; the lobby light dims 5%. A macro focus falloff (sharp around the tip, soft at the frame edges).
// 4J (s04/4J.tsx) is a different picture: tilted, tighter on the tip deep in the red, her reflection, darker.
import React from 'react';
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { clamp, inOutSine, lerp } from '../../ease';
import { ShotDef, ShotProps } from '../types';
import { frameOf } from '../../timing';
import { ez } from './kit';
import { DialView, dialTip } from './dial';

// rl_l3_ui (cut 4, S21 "the meter needle goes down": one meter timeline, HOURS AWAKE ~19 at 1G/4J, past 24 against the stop at 11B):
// the needle now sits just into the red at ~19 (the red zone starts at 18), creeping a hair and ticking on beat 2; the frame moved
// onto it, turned 18 deg (the tip high in frame, the red arc sweeping down through it); the HOURS AWAKE label and the plates still
// never enter (workers/rl_l3_ui/tools/check_dial_l3.py, every frame). 4J is tighter, darker, turned 30 deg, with her reflection.
export const G1 = { cx0: 4899, cx1: 4903, cy: 951, w0: 640, w1: 595, r: 18 };
const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame();
  const touch = frameOf(shot.grid?.[1] ?? 17.104) - shot.from;    // beat 2 of the shot (beat 1 is the cut)
  let v: number;
  if (f < touch) v = lerp(18.72, 19.0, Math.pow(clamp(f / touch), 1.6));
  else { const d = f - touch; v = d === 0 ? 19.06 : d === 1 ? 18.98 : 19.02; }
  const k = inOutSine(clamp(f / (shot.dur - 1)));
  const cx = lerp(G1.cx0, G1.cx1, k), w = lerp(G1.w0, G1.w1, k);
  const dim = 0.05 * ez(f, touch, touch + 4);
  const [tx, ty] = dialTip(v); const k2 = 2560 / w; const a = (G1.r * Math.PI) / 180;
  const ddx = (tx - cx) * k2, ddy = (ty - G1.cy) * k2;
  const fx = 1280 + ddx * Math.cos(a) - ddy * Math.sin(a), fy = 720 + ddx * Math.sin(a) + ddy * Math.cos(a);   // the tip in frame px: the focus centre
  const mask = `radial-gradient(ellipse 38% 46% at ${(fx / 25.6).toFixed(1)}% ${(fy / 14.4).toFixed(1)}%, #000 55%, transparent 100%)`;
  return (
    <AbsoluteFill>
      <DialView cx={cx} cy={G1.cy} w={w} r={G1.r} v={v} filter="blur(3.5px)" />
      <AbsoluteFill style={{ WebkitMaskImage: mask, maskImage: mask }}><DialView cx={cx} cy={G1.cy} w={w} r={G1.r} v={v} /></AbsoluteFill>
      <AbsoluteFill style={{ background: 'radial-gradient(ellipse 80% 75% at 55% 50%, rgba(0,0,0,0) 55%, rgba(30,18,6,0.35) 100%)' }} />
      <AbsoluteFill style={{ background: '#000', opacity: dim }} />
    </AbsoluteFill>
  );
};
export const S1_1G: ShotDef = { stage: Stage, cx916: () => 0.55 };
