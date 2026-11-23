// rl_secb: the party's code layers (9C-9G): confetti and streamers as pure functions of the frame, the TV pin.
import React from 'react';
import { AbsoluteFill } from 'remotion';
import { clamp, noise1, outCubic } from '../../ease';
import { Quad } from '../../blocks/ScreenInsert';
import { K16, LAY } from '../s07/_lib';

export const TV: Quad = (LAY.S16.tv_screen_TL_TR_BR_BL as number[][]).map(([x, y]) => [x * K16, y * K16]) as Quad;
const COLS = ['#ff6fa5', '#ffd166', '#5ad1c9', '#9b8cff', '#ff8a5c', '#7ee081'];
const h = (i: number, k: number) => { const x = Math.sin(i * 127.1 + k * 311.7) * 43758.5453; return x - Math.floor(x); };

/** confetti released at `bursts` (shot-local frames), falling with flutter; n pieces per burst */
export const Confetti: React.FC<{ f: number; bursts: number[]; n?: number; frozen?: number }> = ({ f, bursts, n = 40, frozen }) => {
  const t0 = frozen ?? f;
  return (
    <AbsoluteFill style={{ pointerEvents: 'none' }}>
      {bursts.flatMap((b, bi) => Array.from({ length: n }, (_, i) => {
        const id = bi * 100 + i; const age = t0 - b; if (age < 0) return null;
        const x0 = 80 + h(id, 1) * 2400, vy = 7 + h(id, 2) * 6, y = -40 + age * vy + 0.04 * age * age * 0;
        if (y > 1500) return null;
        const x = x0 + 40 * Math.sin(age / (6 + h(id, 3) * 6) + id) + 30 * noise1(age / 20, id);
        const rot = age * (6 + h(id, 4) * 10) + id * 37; const flip = Math.abs(Math.cos(age / (4 + h(id, 5) * 4) + id));
        const w = 14 + h(id, 6) * 10;
        return <div key={id} style={{ position: 'absolute', left: x, top: y, width: w, height: w * 0.6, background: COLS[id % COLS.length],
          transform: `rotate(${rot}deg) scaleY(${0.2 + 0.8 * flip})`, opacity: 0.92, boxShadow: '0 2px 3px rgba(0,0,0,0.25)' }} />;
      }))}
    </AbsoluteFill>
  );
};

/** a streamer shot from (x, y) toward (tx, ty) at frame `at`: an SVG ribbon drawn on over 8 frames, then drooping */
export const Streamer: React.FC<{ f: number; at: number; from: [number, number]; to: [number, number]; col: string; width?: number }> = ({ f, at, from, to, col, width = 16 }) => {
  const k = outCubic(clamp((f - at) / 8)); if (k <= 0) return null;
  const droop = 120 * clamp((f - at - 8) / 30);
  const [x0, y0] = from, [x1, y1] = to;
  const N = 24; const pts = Array.from({ length: N + 1 }, (_, i) => {
    const u = (i / N) * k; const x = x0 + (x1 - x0) * u, y = y0 + (y1 - y0) * u - 220 * Math.sin(Math.PI * u) + droop * u * u;
    return [x + 26 * Math.sin(u * 22 + at), y + 18 * Math.cos(u * 19 + at)];
  });
  return (
    <svg style={{ position: 'absolute', left: 0, top: 0, overflow: 'visible' }} width={2560} height={1440}>
      <polyline points={pts.map((p) => p.join(',')).join(' ')} fill="none" stroke={col} strokeWidth={width} strokeLinecap="round" strokeLinejoin="round" opacity={0.95} />
    </svg>
  );
};
