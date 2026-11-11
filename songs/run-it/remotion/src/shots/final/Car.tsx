// The GT3 RS side profile from the approved frames (design/frames.html gt3(), ported 1:1 to SVG): Ultraviolet body,
// YELLOW calipers, unbadged. Origin = rear-wheel ground point, faces right, ~466 x 192 units. Purple only here (PALETTE).
import React from 'react';

const UV = '#5b2d94', UVhi = '#8a5cd0', UVlo = '#2f1452', CAL = '#ffd21f';
const WY = -44, WR = 44, WHEELS = [104, 368];
const rr = (x: number, y: number, w: number, h: number, r: number) => `M${x + r},${y} L${x + w - r},${y} Q${x + w},${y} ${x + w},${y + r} L${x + w},${y + h - r} Q${x + w},${y + h} ${x + w - r},${y + h} L${x + r},${y + h} Q${x},${y + h} ${x},${y + h - r} L${x},${y + r} Q${x},${y} ${x + r},${y} Z`;
const arcPt = (cx: number, cy: number, r: number, a: number) => `${cx + Math.cos(a) * r},${cy + Math.sin(a) * r}`;

export const Car: React.FC<{ id: string }> = ({ id }) => (
  <g>
    <defs>
      <linearGradient id={`uv${id}`} x1="0" y1="-150" x2="0" y2="-40" gradientUnits="userSpaceOnUse">
        <stop offset="0" stopColor={UVhi} /><stop offset="0.35" stopColor={UV} /><stop offset="1" stopColor={UVlo} />
      </linearGradient>
    </defs>
    <ellipse cx={236} cy={2} rx={250} ry={9} fill="rgba(0,0,0,.5)" />
    <path d="M72,-112 Q58,-140 62,-172 M128,-128 Q116,-150 118,-172" stroke="#3a3448" strokeWidth={7} strokeLinecap="round" fill="none" />
    <path d="M12,-40 L6,-74 Q8,-96 28,-102 C74,-118 150,-146 236,-150 C272,-152 304,-142 336,-120 C376,-112 420,-104 448,-88 C464,-78 468,-56 462,-42 Z" fill={`url(#uv${id})`} />
    {WHEELS.map((wx) => <path key={wx} d={`M${wx - WR - 7},${WY} A${WR + 7},${WR + 7} 0 0 1 ${wx + WR + 7},${WY} L${wx + WR + 7},-40 L${wx - WR - 7},-40 Z`} fill="#0a0910" />)}
    <rect x={160} y={-48} width={150} height={8} fill="#120f18" /><rect x={420} y={-44} width={46} height={5} fill="#120f18" />
    <path d="M30,-98 C140,-112 300,-112 446,-86" stroke="rgba(200,170,255,.45)" strokeWidth={2.5} fill="none" />
    <path d="M122,-112 C160,-130 206,-140 240,-141 C274,-141 300,-132 322,-114 Z" fill="#16131f" stroke="#0c0a12" strokeWidth={3} />
    <path d="M232,-140 L228,-113" stroke={UVlo} strokeWidth={6} />
    <path d="M150,-82 L196,-88 L190,-66 L154,-64 Z" fill="#0f0c15" />
    <path d="M318,-112 L312,-52" stroke="rgba(20,10,35,.6)" strokeWidth={2} />
    <path d={rr(2, -182, 160, 13, 5)} fill="#16131e" stroke="#4a4260" strokeWidth={2} />
    <path d={rr(0, -190, 9, 32, 3)} fill="#16131e" stroke="#4a4260" strokeWidth={2} />
    <path d={rr(155, -190, 9, 32, 3)} fill="#16131e" stroke="#4a4260" strokeWidth={2} />
    <path d={rr(8, -90, 22, 7, 3)} fill="#ff3b52" />
    <ellipse cx={0} cy={0} rx={13} ry={8.5} fill="#fff6e2" transform="translate(432 -98) rotate(-31.5)" />
    {WHEELS.map((wx) => (
      <g key={`w${wx}`}>
        <circle cx={wx} cy={WY} r={WR} fill="#09080d" />
        <circle cx={wx} cy={WY} r={32} fill="#2b2934" />
        <path d={`M${arcPt(wx, WY, 28, -Math.PI * 0.98)} A28,28 0 0 1 ${arcPt(wx, WY, 28, -Math.PI * 0.42)} L${arcPt(wx, WY, 15, -Math.PI * 0.42)} A15,15 0 0 0 ${arcPt(wx, WY, 15, -Math.PI * 0.98)} Z`} fill={CAL} />
        {Array.from({ length: 10 }, (_, k) => { const a = (k / 10) * Math.PI * 2 + 0.15; return <line key={k} x1={wx + Math.cos(a) * 7} y1={WY + Math.sin(a) * 7} x2={wx + Math.cos(a) * 31} y2={WY + Math.sin(a) * 31} stroke="#b4b2c0" strokeWidth={3.5} />; })}
        <circle cx={wx} cy={WY} r={6} fill="#e2e0ea" />
      </g>
    ))}
  </g>
);
export const CAR_W = 466, CAR_H = 192;
