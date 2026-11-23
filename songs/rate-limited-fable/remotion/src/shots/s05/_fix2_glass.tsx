// rl_fix2_read (Nov 16): her messages on the door glass at real size (5H, 12G). The glass is a screen between them: her sent
// bubbles (her blue, white type), right-aligned, popping in with a small spring; the receipt line under the last one.
// Drawn in whatever px space the caller is in (16:9 stage or the 9:16 screen layer): size = the message type's px.
import React from 'react';
import { clamp } from '../../ease';
import { FONT } from '../../theme';

const BLUE = 'rgb(34,122,246)';
const pop = (f: number, at: number) => {
  const x = (f - at) / 30; if (x <= 0) return 0;
  const w = 2 * Math.PI * 3.4, d = 0.5, wd = w * Math.sqrt(1 - d * d);
  return 1 - Math.exp(-d * w * x) * (Math.cos(wd * x) + (d / Math.sqrt(1 - d * d)) * Math.sin(wd * x));
};

export type Msg = { text: string; at: number };
/** right: the bubbles' right edge; top: the first bubble's top; size: the message type px */
export const GlassMsgs: React.FC<{ f: number; msgs: Msg[]; receipt?: { text: string; at: number }[]; right: number; top: number; size: number;
  blur?: number; opacity?: number; emptyW?: number }> = ({ f, msgs, receipt = [], right, top, size, blur = 0, opacity = 1, emptyW }) => {
  const padY = size * 0.38, padX = size * 0.62, lh = size * 1.22, gap = size * 0.26;
  const bh = lh + 2 * padY;
  const shown = msgs.filter((m) => f >= m.at);
  const rc = [...receipt].reverse().find((r) => f >= r.at);
  return (
    <div style={{ position: 'absolute', left: 0, top: 0, width: '100%', height: '100%', filter: blur > 0.05 ? `blur(${blur.toFixed(2)}px)` : undefined, opacity, pointerEvents: 'none' }}>
      {shown.map((m, i) => {
        const k = clamp(pop(f, m.at), 0, 1.2); const last = i === shown.length - 1;
        return (
          <div key={i} style={{ position: 'absolute', right: `calc(100% - ${right}px)`, top: top + i * (bh + gap), height: bh, transformOrigin: '100% 100%',
            transform: `scale(${(0.55 + 0.45 * k).toFixed(4)})`, opacity: clamp(k * 2.5) }}>
            <div data-fit={m.text ? 'box' : 'off'} style={{ height: bh, minWidth: emptyW ?? 0, boxSizing: 'border-box', padding: `${padY}px ${padX}px`, borderRadius: bh / 2, background: BLUE,
              fontFamily: FONT.ui, fontWeight: 400, fontSize: size, lineHeight: `${lh}px`, color: '#f4f6fa', whiteSpace: 'nowrap',
              boxShadow: `0 0 ${size * 0.5}px rgba(34,122,246,0.45), 0 ${size * 0.08}px ${size * 0.3}px rgba(0,0,0,0.35)` }}>{m.text || ' '}</div>
            {last ? (   // the tail
              <svg style={{ position: 'absolute', right: -size * 0.2, bottom: 0, overflow: 'visible' }} width={size * 0.6} height={size * 0.6}>
                <path d={`M 0 ${size * 0.05} Q ${size * 0.12} ${size * 0.5} ${size * 0.6} ${size * 0.6} Q ${size * 0.22} ${size * 0.6} 0 ${size * 0.42} Z`} fill={BLUE} />
              </svg>
            ) : null}
          </div>
        );
      })}
      {rc && shown.length ? (
        <div data-fit="box" style={{ position: 'absolute', right: `calc(100% - ${right + size * 0.3}px)`, top: top + shown.length * (bh + gap) - size * 0.1, padding: `${size * 0.18}px ${size * 0.3}px`, fontFamily: FONT.ui, fontWeight: 600,
          fontSize: size * 0.62, lineHeight: 1.2, color: 'rgba(236,238,242,0.96)', whiteSpace: 'nowrap', textShadow: '0 2px 10px rgba(0,0,0,0.7)', opacity: clamp((f - rc.at) / 4) }}>{rc.text}</div>
      ) : null}
    </div>
  );
};
