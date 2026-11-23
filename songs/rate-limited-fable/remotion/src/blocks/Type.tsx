// Type layers. Sizes are stage px at 1440 and follow the studio rule: lyrics 64, everything else >= 34, code 38-40.
// TextBox is the container text_fit_check.py measures (data-fit="box"): copy that spills, clips or touches the edge
// fails the check. If copy does not fit, shorten it or grow the box; never drop below SIZE.min.
// Baked PNG text (a phone screen, a slip) goes through studio/textfit.py instead and comes in via ScreenInsert.
import React from 'react';
import { useCurrentFrame } from 'remotion';
import { C, FONT, SIZE } from '../theme';
import { clamp, outCubic } from '../ease';

export type Box = { x: number; y: number; w: number; h: number };

export const TextBox: React.FC<Box & {
  size?: number; kind?: 'ui' | 'lyric' | 'code' | 'head' | 'brand'; weight?: number; color?: string; bg?: string;
  align?: 'left' | 'center' | 'right'; valign?: 'top' | 'center' | 'bottom'; pad?: number; radius?: number;
  lineHeight?: number; opacity?: number; style?: React.CSSProperties; children: React.ReactNode;
}> = ({ x, y, w, h, size, kind = 'ui', weight, color = C.white, bg, align = 'left', valign = 'center', pad = 24, radius = 10,
  lineHeight = 1.18, opacity = 1, style, children }) => {
  const want = size ?? (kind === 'lyric' ? SIZE.lyric : kind === 'code' ? SIZE.code : SIZE.label);
  const fs = Math.max(want, kind === 'lyric' ? SIZE.lyric : kind === 'code' ? 38 : SIZE.min); // the floor is the rule
  const fam = kind === 'code' ? FONT.mono : kind === 'head' ? FONT.head : kind === 'brand' ? FONT.brand : FONT.ui;
  return (
    <div data-fit="box" style={{ position: 'absolute', left: x, top: y, width: w, height: h, padding: pad, boxSizing: 'border-box',
      background: bg, borderRadius: radius, display: 'flex', flexDirection: 'column', opacity,
      justifyContent: valign === 'top' ? 'flex-start' : valign === 'bottom' ? 'flex-end' : 'center', ...style }}>
      <div style={{ fontFamily: fam, fontSize: fs, fontWeight: weight ?? (kind === 'head' ? 900 : kind === 'code' ? 400 : 600),
        color, textAlign: align, lineHeight, whiteSpace: 'pre-wrap', overflowWrap: 'break-word' }}>{children}</div>
    </div>
  );
};

/** In-world neon wording (a lit sign is a real light, so it glows; nothing else does). on = 0..1 (flicker/ignite). */
export const Neon: React.FC<{ text: string; x: number; y: number; size: number; color?: string; on?: number;
  font?: string; rotate?: number; align?: 'left' | 'center' }> = ({ text, x, y, size, color = C.neonGreen, on = 1, font = FONT.head, rotate = 0, align = 'center' }) => {
  const g = clamp(on);
  return (
    <div data-fit="off" style={{ position: 'absolute', left: x, top: y, transform: `translate(${align === 'center' ? '-50%' : '0'}, -50%) rotate(${rotate}deg)`,
      fontFamily: font, fontWeight: 900, fontSize: Math.max(size, SIZE.min), whiteSpace: 'nowrap', letterSpacing: '0.02em',
      color: g > 0.05 ? color : 'rgba(40,40,40,0.9)', opacity: 0.35 + 0.65 * g,
      textShadow: g > 0.05 ? `0 0 ${0.08 * size * g}px ${color}, 0 0 ${0.3 * size * g}px ${color}, 0 0 ${0.8 * size * g}px ${color}88` : 'none' }}>
      {text}
    </div>
  );
};
/** neon ignition 0..1 starting at frame `at`: two sputters then on (deterministic) */
export const igniteAt = (f: number, at: number) => {
  const d = f - at; if (d < 0) return 0; if (d < 2) return 0.7; if (d < 4) return 0.1; if (d < 5) return 1; if (d < 7) return 0.3; return 1;
};

/** word-by-word reveal of a string over [start, start+len] frames: each word fades and lifts in (no pop-in) */
export const Reveal: React.FC<{ text: string; start: number; len: number; lift?: number }> = ({ text, start, len, lift = 10 }) => {
  const f = useCurrentFrame(); const ws = text.split(/(\s+)/);
  const n = ws.filter((w) => w.trim()).length; let i = -1;
  return <>{ws.map((w, j) => {
    if (!w.trim()) return <span key={j}>{w}</span>;
    i++; const k = outCubic(clamp((f - start - (i * len) / Math.max(1, n)) / 6));
    return <span key={j} style={{ opacity: k, display: 'inline-block', transform: `translateY(${(1 - k) * lift}px)` }}>{w}</span>;
  })}</>;
};
