import React from 'react';
import { C, useLayout, useT } from '../theme';
import { kickEnv } from '../timing';

/**
 * The dot. Pink (#ff6fae, r 74, three faint rings at +34/+68/+102) breathes on the kick: the disc swells and the
 * rings open outward with the kick envelope (drum MIDI). `variant="white"` is the outro light (r 60, glow, rings at +44).
 * `breath` 0 = static. `ripple` draws the click ring.
 */
export const Dot: React.FC<{ variant?: 'pink' | 'white'; breath?: number; cx?: number; cy?: number; r?: number; ripple?: boolean; opacity?: number }> = ({
  variant = 'pink', breath = 1, cx, cy, r, ripple = false, opacity = 1,
}) => {
  const t = useT();
  const L = useLayout();
  const x = cx ?? L.dot.cx, y = cy ?? L.dot.cy, s = L.dot.scale;
  const white = variant === 'white';
  const R = (r ?? (white ? 60 : 74)) * s, step = (white ? 44 : 34) * s;
  const k = kickEnv(t) * breath;
  const disc = R * (1 + 0.06 * k);
  return (
    <svg width={L.W} height={L.H} style={{ position: 'absolute', left: 0, top: 0, opacity, overflow: 'visible' }}>
      {[3, 2, 1].map((i) => (
        <circle key={i} cx={x} cy={y} r={R + i * step + k * i * 7 * s} fill="none" stroke={`rgba(255,255,255,${0.05 * i})`} strokeWidth={2} />
      ))}
      <circle cx={x} cy={y} r={disc} fill={white ? '#ffffff' : C.pink} style={white ? { filter: 'drop-shadow(0 0 25px #fff)' } : undefined} />
      {ripple && <circle cx={x} cy={y} r={R + 24 * s} fill="none" stroke="rgba(255,255,255,.55)" strokeWidth={3} />}
    </svg>
  );
};
