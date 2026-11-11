import React from 'react';
import { C, MED, PAPER, mixC, useLayout, useT } from '../theme';
import { memoryAt } from '../timing';

/**
 * Top-right memory meter. `pct` overrides the shots' meter steps. Amber from 90, red at 100.
 * `theme` 0 = paper .. 1 = dark. `draw` 0..1 builds it in (label rises, track draws left to right). `tick` 0..1 pulses
 * the empty track (the intro's quarter-note ticks).
 */
export const MemoryMeter: React.FC<{ pct?: number; label?: string; opacity?: number; theme?: number; draw?: number; tick?: number }> = ({
  pct, label = 'MEMORY', opacity = 1, theme = 1, draw = 1, tick = 0,
}) => {
  const t = useT();
  const { meter: m } = useLayout();
  const v = pct ?? memoryAt(t);
  const k = Math.max(0, Math.min(1, theme));
  const base = mixC(PAPER.ink, C.meter, k);
  const color = v >= 100 ? C.meterRed : v >= 90 ? C.meterAmber : base;
  const px = m.label; // approved frame used 24 px; the studio floor is 34 px, so 34 here (see STATUS)
  const d = Math.max(0, Math.min(1, draw));
  if (d <= 0 || opacity <= 0) return null;
  const textIn = Math.max(0, Math.min(1, (d - 0.15) / 0.6));
  const trackA = 0.12 + 0.10 * tick;
  return (
    <div style={{ position: 'absolute', left: m.x, top: m.y - 10, width: m.w, opacity }}>
      <div style={{ ...MED, display: 'flex', justifyContent: 'space-between', fontSize: px, lineHeight: '44px', height: 44, opacity: textIn, transform: `translateY(${(1 - textIn) * 14}px)` }}>
        <span style={{ color: mixC(PAPER.inkSoft, 'rgba(255,255,255,.55)', k) }}>{label}</span>
        <span style={{ color }}>{Math.round(v)}%</span>
      </div>
      <div style={{ position: 'relative', height: 10, marginTop: 6, width: m.w * d, borderRadius: 5, background: mixC(`rgba(23,23,28,${trackA})`, `rgba(255,255,255,${trackA})`, k) }}>
        {v > 0 && <div style={{ position: 'absolute', left: 0, top: 0, height: 10, width: Math.max(10, (m.w * v) / 100), borderRadius: 5, background: color, boxShadow: v > 90 ? `0 0 18px ${color}` : 'none' }} />}
      </div>
    </div>
  );
};
