import React from 'react';
import { C, MED, mixC, useLayout, useT } from '../theme';

/** '● REC mm:ss:ff' under the memory meter, counting real film time from `from` (the press, s12). 34 px. */
export const RecClock: React.FC<{ from: number; theme?: number; opacity?: number; stopAt?: number; label?: string; dot?: string }> = ({ from, theme = 1, opacity = 1, stopAt, label, dot }) => {
  const t = useT();
  const { meter: m } = useLayout();
  if (t < from || opacity <= 0) return null;
  const stopped = stopAt !== undefined && t >= stopAt; // rc_final: the click stops the recording (s78)
  const d = (stopped ? stopAt! : t) - from;
  const appear = Math.min(1, d / 0.2), ease = 1 - Math.pow(1 - appear, 3);
  const ff = Math.floor((d * 30) % 30), ss = Math.floor(d % 60), mm = Math.floor(d / 60);
  const p2 = (n: number) => String(n).padStart(2, '0');
  const blink = stopped || Math.floor(d) % 2 === 0 || d < 1;
  const lab = stopped && label ? label : 'REC';
  const wide = lab.length > 3 ? (lab.length - 3) * 21 : 0; // a longer label grows the box to the left, never overflows it
  return (
    <div style={{ ...MED, position: 'absolute', left: m.x - wide, top: m.y + 58, width: m.w + wide, height: 44, display: 'flex', justifyContent: 'flex-end',
      alignItems: 'center', gap: 14, fontSize: 34, lineHeight: '44px', opacity: ease * opacity, transform: `translateY(${(1 - ease) * -8}px)`, color: mixC('rgba(23,23,28,.7)', 'rgba(255,255,255,.62)', theme) }}>
      <span style={{ display: 'inline-block', width: 16, height: 16, borderRadius: 8, background: dot ?? C.meterRed, opacity: blink ? 1 : 0.25, boxShadow: dot ? 'none' : '0 0 10px rgba(255,59,82,.55)' }} />
      <span>{lab}</span>
      <span style={{ color: mixC('#17171c', '#f4f1f6', theme), fontVariantNumeric: 'tabular-nums' }}>{`${p2(mm)}:${p2(ss)}:${p2(ff)}`}</span>
    </div>
  );
};
