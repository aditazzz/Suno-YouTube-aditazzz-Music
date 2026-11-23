// rl5_c (cut 5, package C): shared staging for the cut 5 screen shots. Every value is a pure function of the frame.
// Cue frames in this package are the plan's ABSOLUTE film frames (CUT5_PLAN §3/§6); a shot turns them local with loc(shot, F),
// so the shots stay right if D registers them at the plan's frames (and degrade gracefully if a shot is trimmed).
import React from 'react';
import { AbsoluteFill } from 'remotion';
import { clamp, inOutCubic, lerp } from '../../ease';
import { Phone } from '../../blocks/real/Phone';
import { Grain2, SoftPlate, Spill, Vig, hand } from '../../blocks/real/Scene';

export const loc = (shot: { from: number }, F: number) => F - shot.from;
/** eased 0..1 between a and b (inOut cubic: §2f "every move eased in and out") */
export const ez = (f: number, a: number, b: number, e: (k: number) => number = inOutCubic) => e(clamp((f - a) / Math.max(1e-6, b - a)));
/** a spring-ish pop 0..1(+overshoot) from frame at (for bubbles/chips landing) */
export const pop = (f: number, at: number, len = 9) => {
  const x = (f - at) / len; if (x <= 0) return 0; if (x >= 2.2) return 1;
  return 1 - Math.exp(-4.2 * x) * Math.cos(5.2 * x);
};

/** her phone, held close in her room (the room soft behind): k = stage px per iOS pt; focus = the screen point (pt) at frame centre.
 *  drift: a slow eased push (k0 -> k1) over the shot, a tiny handheld drift. */
export const PhoneStage: React.FC<{
  f: number; dur: number; k0: number; k1: number; focus0: number; focus1: number; time: string; rot?: number; seed?: number; cx?: number;
  dark?: boolean; plate?: string; dim?: number; children: React.ReactNode; grey?: number; light?: number;
}> = ({ f, dur, k0, k1, focus0, focus1, time, rot = -0.8, seed = 5, cx = 1280, dark, plate, dim, children, grey = 0, light }) => {
  const e = ez(f, 0, dur - 1);
  const k = lerp(k0, k1, e), focus = lerp(focus0, focus1, e);
  const h = hand(f, 1, seed);
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ filter: grey > 0 ? `grayscale(${grey}) brightness(${1 - 0.12 * grey})` : undefined }}>
        <SoftPlate src={plate} dim={dim} x={-h.x * 0.4} y={-h.y * 0.4} />
      </AbsoluteFill>
      <Spill cx={1280} cy={740} r={1500} k={0.12 * (1 - 0.6 * grey)} />
      <AbsoluteFill style={{ filter: grey > 0 ? `grayscale(${grey})` : undefined }}>
        <Phone cx={cx + h.x} cy={720 + (426 - focus) * k + h.y} w={393 * k} rot={rot + h.r} time={time} dark={dark} glare={0.06} silent light={light}>
          {children}
        </Phone>
      </AbsoluteFill>
      <Vig k={0.38} />
      <Grain2 f={f} />
    </AbsoluteFill>
  );
};

/** highlight sweep (a marker stroke drawn left to right) used by the crossword and the 8D/9C emphasis */
export const sweep = (f: number, at: number, len = 6) => clamp((f - at) / len);
export { clamp, lerp };
