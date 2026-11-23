// 4J "(Say it's not about me)": a slow push on the dial, the needle deep in the red (a faint tremble), label out of frame;
// her soft reflection in the dial glass (2D, screen blend). The drums stop: no beat pulse.
// rl_fix2_open (WATCH blocker): was the same hold as 1G with HOURS AWAKE readable. Now a different picture from the full-res dial
// crop (first30/dial.tsx): turned 40 deg so the needle hangs straight down from the hub (out of frame at the top) into
// the red ticks, the gold rim across the corner; a slow push; the lobby darker and cooler, her reflection over the red. The label and the plates never enter the
// frame (build/fix2/open/tools/check_dial.py checks every frame).
import React from 'react';
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { clamp, lerp, inOutSine, noise1 } from '../../ease';
import { ShotDef, ShotProps } from '../types';
import { DialView, dialTip } from '../first30/dial';

// rl_l3_ui (cut 4, S21: one meter timeline, ~20 at 2:58): the needle at ~19.9 (was 23.6, deeper than 11B's), centred on the tip, turned 30 deg (was 40)
// (searched so the label stays out at every frame) (workers/rl_l3_ui/tools/check_dial_l3.py).
export const J4 = { cx0: 4827, cx1: 4831, cy0: 944, cy1: 948, w0: 600, w1: 510, r: 30 };   // S6 px: centred on the tip at ~19.9, turned 30 deg, a slow push
const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame();
  const v = 19.9 + 0.1 * noise1(f / 9, 4);
  const k = inOutSine(clamp(f / (shot.dur - 1)));
  const cx = lerp(J4.cx0, J4.cx1, k), cy = lerp(J4.cy0, J4.cy1, k), w = lerp(J4.w0, J4.w1, k);
  const [tx, ty] = dialTip(v); const kk = 2560 / w; const a = (J4.r * Math.PI) / 180;
  const dx = (tx - cx) * kk, dy = (ty - cy) * kk;
  const fx = 1280 + dx * Math.cos(a) - dy * Math.sin(a), fy = 720 + dx * Math.sin(a) + dy * Math.cos(a);
  const mask = `radial-gradient(ellipse 34% 44% at ${(fx / 25.6).toFixed(1)}% ${(fy / 14.4).toFixed(1)}%, #000 50%, transparent 100%)`;
  return (
    <AbsoluteFill>
      <DialView cx={cx} cy={cy} w={w} r={J4.r} v={v} filter="blur(4.5px) brightness(0.78) saturate(0.9)" />
      <AbsoluteFill style={{ WebkitMaskImage: mask, maskImage: mask }}><DialView cx={cx} cy={cy} w={w} r={J4.r} v={v} filter="brightness(0.8) saturate(0.95) contrast(1.06)" /></AbsoluteFill>
      {/* her reflection in the glass: a soft head-and-shoulders, screen-blended, drifting the other way to the push */}
      <AbsoluteFill style={{ mixBlendMode: 'screen', opacity: lerp(0.14, 0.24, k) }}>
        <div style={{ position: 'absolute', left: 1500 - 60 * k, top: 260, width: 520, height: 600, borderRadius: '50% 50% 45% 45%', background: 'rgb(200,160,110)', filter: 'blur(60px)' }} />
        <div style={{ position: 'absolute', left: 1240 - 60 * k, top: 760, width: 1040, height: 900, borderRadius: '50%', background: 'rgb(150,40,50)', filter: 'blur(80px)' }} />
      </AbsoluteFill>
      <AbsoluteFill style={{ background: 'radial-gradient(ellipse 75% 70% at 50% 50%, rgba(0,0,0,0) 45%, rgba(8,10,20,0.5) 100%)' }} />
    </AbsoluteFill>
  );
};
export const S4_4J: ShotDef = { stage: Stage, cx916: () => 0.5 };
