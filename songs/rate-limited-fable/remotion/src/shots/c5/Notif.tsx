// 9E2 vacuum notification (cut 5; plan §3: 9E2 f4662-4732; N45): her N45 "the Roomba should be here with the error message
// obstacle is doing yoga". A phone-style notification banner (the iOS look: frosted card, app icon, app name, "now", the message)
// slides down into the top of the 16:9 frame on the wide and holds; no brand (our own round vacuum glyph, name VACUUM).
//   <VacuumNotif f={f} at={NOTIF.IN - shot.from} />   drawn in output px (2560x1440), after the stage
import React from 'react';
import { AbsoluteFill } from 'remotion';
import { F } from '../../blocks/real/tokens';
import { VACUUM } from '../../blocks/real/script';
import { clamp, pop } from './kit';

export const NOTIF = { IN: 4676 };   // absolute: ~0.45 s into 9E2, so the wide reads first; holds 1.9 s to the cut
const W = 1180;

export const VacuumNotif: React.FC<{ f: number; at: number; x?: number; y?: number }> = ({ f, at, x = (2560 - W) / 2, y = 60 }) => {
  if (f < at) return null;
  const k = clamp(pop(f, at, 10), 0, 1.08);
  return (
    <AbsoluteFill style={{ pointerEvents: 'none' }}>
      <div style={{ position: 'absolute', left: x, top: y, width: W, transform: `translateY(${((k - 1) * 260).toFixed(1)}px)`, opacity: clamp(k * 3),
        borderRadius: 52, background: 'rgba(246,244,240,0.86)', backdropFilter: 'blur(30px)', boxShadow: '0 18px 50px rgba(0,0,0,0.35)', padding: '30px 38px',
        display: 'flex', alignItems: 'center', gap: 30, fontFamily: F.ios, boxSizing: 'border-box' }}>
        <div style={{ width: 112, height: 112, borderRadius: 26, background: 'linear-gradient(160deg,#5b6370,#2d323a)', flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <svg width={78} height={78} viewBox="0 0 80 80"><circle cx={40} cy={40} r={32} fill="#E9ECF0" /><circle cx={40} cy={40} r={22} fill="none" stroke="#9aa3ad" strokeWidth={4} />
            <circle cx={40} cy={22} r={6} fill="#2d323a" /><path d="M14 52 Q40 66 66 52" fill="none" stroke="#9aa3ad" strokeWidth={4} /></svg>
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', gap: 20 }}>
            <span style={{ fontSize: 40, fontWeight: 700, letterSpacing: 1, color: '#1c1c1e' }}>{VACUUM.app}</span>
            <span style={{ fontSize: 38, color: '#6c6c70' }}>{VACUUM.when}</span>
          </div>
          <div style={{ fontSize: 52, fontWeight: 500, color: '#1c1c1e', marginTop: 6, whiteSpace: 'nowrap' }}>{VACUUM.body}</div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
