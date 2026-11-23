// The crayon drawing (4C, 4D): a database cylinder, a smiling sun, DATABASE in crayon capitals. Drawn 2D art.
import React from 'react';
import { HAND } from '../s03/_lib';
export const Drawing: React.FC<{ w: number; h: number; rot?: number }> = ({ w, h, rot = 0 }) => (
  <div data-fit="box" style={{ position: 'absolute', left: 0, top: 0, width: w, height: h, background: '#f6f2e8', transform: `rotate(${rot}deg)`, boxShadow: '0 8px 18px rgba(0,0,0,0.45)', borderRadius: 3 }}>
    <svg width={w} height={h} viewBox="0 0 330 240" style={{ position: 'absolute', inset: 0 }}>
      <g fill="none" strokeLinecap="round" strokeLinejoin="round">
        <circle cx={270} cy={52} r={26} stroke="#f2b200" strokeWidth={7} />
        {Array.from({ length: 8 }, (_, i) => { const a = (i * Math.PI) / 4; return <line key={i} x1={270 + 34 * Math.cos(a)} y1={52 + 34 * Math.sin(a)} x2={270 + 48 * Math.cos(a)} y2={52 + 48 * Math.sin(a)} stroke="#f2b200" strokeWidth={6} />; })}
        <path d="M260,58 q10,9 20,0" stroke="#7a4a00" strokeWidth={4} /><circle cx={262} cy={46} r={2.5} fill="#7a4a00" /><circle cx={278} cy={46} r={2.5} fill="#7a4a00" />
        <ellipse cx={110} cy={62} rx={62} ry={18} stroke="#2f6fd0" strokeWidth={7} />
        <path d="M48,62 v86 a62,18 0 0 0 124,0 v-86" stroke="#2f6fd0" strokeWidth={7} />
        <path d="M48,104 a62,18 0 0 0 124,0" stroke="#2f6fd0" strokeWidth={6} />
      </g>
    </svg>
    <div style={{ position: 'absolute', left: 0, right: 0, bottom: 8, textAlign: 'center', fontFamily: HAND, fontWeight: 700, fontSize: Math.max(34, h * 0.17), color: '#d2402e', letterSpacing: '0.04em' }}>DATABASE</div>
  </div>
);
