// LightChange: a grade crossfade between two plates (or two graded versions of one plate): lights going out, dawn
// coming up, a neon sign switching the room's colour. B fades in over A from frame `at` for `len` frames, eased;
// an optional flicker pre-roll for a light that stutters before it holds.
//
//   <LightChange at={40} len={18} a={<Plate src="plates/dawn.jpg" dur={d} grade="brightness(0.55) hue-rotate(-12deg)" />}
//                                b={<Plate src="plates/dawn.jpg" dur={d} />} />
import React from 'react';
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { clamp, inOutSine } from '../ease';

export const lightK = (f: number, at: number, len: number, flicker = 0, ease = inOutSine) => {
  const k = ease(clamp((f - at) / Math.max(1, len)));
  if (flicker > 0 && f >= at - flicker && f < at) { const d = f - (at - flicker); return d % 4 < 2 ? 0.55 : 0.08; }
  return k;
};

export const LightChange: React.FC<{ a: React.ReactNode; b: React.ReactNode; at: number; len: number; flicker?: number;
  blend?: React.CSSProperties['mixBlendMode'] }> = ({ a, b, at, len, flicker = 0, blend }) => {
  const f = useCurrentFrame(); const k = lightK(f, at, len, flicker);
  return (
    <AbsoluteFill>
      <AbsoluteFill>{a}</AbsoluteFill>
      {k > 0 ? <AbsoluteFill style={{ opacity: k, mixBlendMode: blend }}>{b}</AbsoluteFill> : null}
    </AbsoluteFill>
  );
};
