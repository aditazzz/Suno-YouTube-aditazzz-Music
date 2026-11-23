// Clocks. The night runs 11:58 PM to 6:00 AM; every shot's BOARDS clock ("2:04 to 2:06 AM") drives its clock face.
// minutes = minutes after 6 PM (timing.parseClock), so the night is one increasing number.
//
//   const [a, b] = clockRange(shot); const m = clockAt(shot, f);            // eased sweep across the shot
//   <AnalogClock cx={1800} cy={300} r={120} minutes={m} />   <DigitalClock x={..} y={..} minutes={m} size={90} />
import React from 'react';
import { useCurrentFrame } from 'remotion';
import { C, FONT, SIZE } from '../theme';
import { Shot, clockRange, fmtClock } from '../timing';
import { clamp, inOutCubic, lerp } from '../ease';

/** eased minutes-after-6PM for frame f inside the shot (sweeps the BOARDS range over [a, b] of the shot's frames) */
export const clockAt = (shot: Shot, f: number, a = 0, b = shot.dur, ease = inOutCubic) => {
  const [m0, m1] = clockRange(shot); return lerp(m0, m1, ease(clamp((f - a) / Math.max(1, b - a))));
};

export const AnalogClock: React.FC<{ cx: number; cy: number; r: number; minutes: number; face?: string; ink?: string;
  hand?: string; seconds?: boolean }> = ({ cx, cy, r, minutes, face = C.paper, ink = '#1a1c22', hand = '#1a1c22', seconds = false }) => {
  const total = minutes + 18 * 60; // minutes since midnight-ish (only angles matter)
  const hA = ((total / 60) % 12) * 30, mA = (total % 60) * 6, sA = ((total * 60) % 60) * 6;
  const H = (deg: number, len: number, wd: number, col: string) => (
    <line x1={0} y1={len * 0.15} x2={0} y2={-len} stroke={col} strokeWidth={wd} strokeLinecap="round" transform={`rotate(${deg})`} />
  );
  return (
    <svg data-fit="off" style={{ position: 'absolute', left: cx - r, top: cy - r, overflow: 'visible' }} width={2 * r} height={2 * r}
      viewBox={`${-r} ${-r} ${2 * r} ${2 * r}`}>
      <circle r={r} fill={face} stroke={ink} strokeWidth={r * 0.06} />
      {Array.from({ length: 12 }, (_, i) => (
        <line key={i} x1={0} y1={-r * 0.82} x2={0} y2={-r * (i % 3 ? 0.74 : 0.66)} stroke={ink} strokeWidth={r * (i % 3 ? 0.025 : 0.045)} transform={`rotate(${i * 30})`} />
      ))}
      {H(hA, r * 0.5, r * 0.07, hand)}{H(mA, r * 0.74, r * 0.045, hand)}{seconds ? H(sA, r * 0.8, r * 0.015, C.neonRed) : null}
      <circle r={r * 0.05} fill={hand} />
    </svg>
  );
};

export const DigitalClock: React.FC<{ x: number; y: number; minutes: number; size?: number; color?: string; secs?: boolean;
  glow?: boolean; ampm?: boolean }> = ({ x, y, minutes, size = 90, color = C.neonRed, secs = false, glow = true, ampm = false }) => {
  const total = (minutes + 18 * 60) % (24 * 60);
  return (
    <div data-fit="off" style={{ position: 'absolute', left: x, top: y, fontFamily: FONT.mono, fontWeight: 700, fontSize: Math.max(size, SIZE.min),
      color, letterSpacing: '0.04em', fontVariantNumeric: 'tabular-nums', whiteSpace: 'nowrap',
      textShadow: glow ? `0 0 ${size * 0.12}px ${color}, 0 0 ${size * 0.35}px ${color}66` : undefined }}>
      {fmtClock(minutes, secs)}{ampm ? <span style={{ fontSize: '0.4em', marginLeft: '0.3em' }}>{total >= 720 ? 'PM' : 'AM'}</span> : null}
    </div>
  );
};

/** a clock that sweeps with the shot's BOARDS range: drop it in any shot */
export const ShotClock: React.FC<{ shot: Shot; kind?: 'analog' | 'digital'; cx: number; cy: number; r?: number; size?: number }> = ({ shot, kind = 'digital', cx, cy, r = 110, size = 90 }) => {
  const f = useCurrentFrame(); const m = clockAt(shot, f);
  return kind === 'analog' ? <AnalogClock cx={cx} cy={cy} r={r} minutes={m} /> : <DigitalClock x={cx} y={cy} minutes={m} size={size} />;
};
