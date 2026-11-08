import React from 'react';
import { W, H, C } from './theme';
/** flat graphic skyline: no photos */
export const Skyline: React.FC<{ y?: number; c1?: string; c2?: string; windows?: boolean }> = ({ y = 900, c1 = '#5A3AA8', c2 = '#3C2480', windows = true }) => {
  const b = [[0, 260, 420], [260, 200, 560], [440, 300, 340], [740, 220, 700], [940, 260, 480], [1200, 180, 620], [1360, 300, 400], [1640, 240, 760], [1860, 200, 460], [2040, 320, 540], [2340, 240, 640]];
  return (
    <svg style={{ position: 'absolute', left: 0, top: y - 700, width: W, height: 700 + (H - y) }} viewBox={`0 0 ${W} ${700 + (H - y)}`}>
      {b.map(([x, w, h], i) => (<g key={i}><rect x={x} y={700 - h} width={w} height={h + (H - y)} fill={i % 2 ? c1 : c2} />
        {windows && Array.from({ length: Math.floor(h / 70) }).map((_, r) => Array.from({ length: Math.floor(w / 70) }).map((__, q) => ((r * 3 + q * 5 + i) % 4 === 0) ? <rect key={r + '-' + q} x={x + 22 + q * 62} y={700 - h + 26 + r * 66} width={26} height={34} fill="#FFE9B0" opacity={0.85} /> : null))}</g>))}
    </svg>
  );
};
export const Sky: React.FC<{ a?: string; b?: string; c?: string }> = ({ a = C.skyTop, b = C.skyMid, c = C.skyLow }) => (
  <div style={{ position: 'absolute', inset: 0, background: `linear-gradient(180deg, ${a} 0%, ${b} 55%, ${c} 100%)` }} />
);
export const Sun: React.FC<{ x: number; y: number; r: number; c?: string }> = ({ x, y, r, c = '#FFF6D8' }) => (
  <div style={{ position: 'absolute', left: x - r, top: y - r, width: r * 2, height: r * 2, borderRadius: '50%', background: c, boxShadow: `0 0 ${r}px ${c}88` }} />
);
