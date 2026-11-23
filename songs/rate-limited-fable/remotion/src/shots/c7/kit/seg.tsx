// Her H7.8 / H7.18 (cut 6 frame notes 8, 18): "429 font can look more square like on an alarm clock ... robotic text squarish like
// digital alarm clocks have"; "same font change for the eyes area, more computer like". ONE seven-segment face for every number his
// visor shows (429, 4, 42, 418, 200 ...), everywhere: SegText draws it, VisorSeg pins it on a visor's digit row (a quad measured on
// the plate's own digit render, so size/place match the approved look), lit segments emissive (screen blend: the glass reflections
// stay on top), unlit segments a faint ghost like a real alarm clock, a soft glow. The plate under it is the visor's `dark` state.
import React from 'react';
import { ScreenInsert, Quad } from '../../../blocks/ScreenInsert';

// segments: a top, b top-right, c bottom-right, d bottom, e bottom-left, f top-left, g middle
const MAP: Record<string, string> = {
  '0': 'abcdef', '1': 'bc', '2': 'abged', '3': 'abgcd', '4': 'fgbc', '5': 'afgcd', '6': 'afgedc', '7': 'abc', '8': 'abcdefg', '9': 'abcdfg',
  '-': 'g', ' ': '', 'E': 'afged', 'r': 'eg', 'o': 'cdeg', 'H': 'bcefg', 'P': 'abefg', 'L': 'def', 'A': 'abcefg', 'C': 'adef', 'S': 'afgcd',
};
const CW = 60, CH = 100, T = 13, GAP = 2.2;     // one cell; segment thickness; gap between segments (the alarm-clock look)
/** the polygon of one segment in a CW x CH cell (beveled ends, square robotic face) */
const seg = (s: string): string => {
  const h = T / 2, x0 = h, x1 = CW - h, y0 = h, ym = CH / 2, y1 = CH - h;
  const H = (y: number, a: number, b: number) => `${a + GAP + h},${y - h} ${b - GAP - h},${y - h} ${b - GAP},${y} ${b - GAP - h},${y + h} ${a + GAP + h},${y + h} ${a + GAP},${y}`;
  const V = (x: number, a: number, b: number) => `${x - h},${a + GAP + h} ${x},${a + GAP} ${x + h},${a + GAP + h} ${x + h},${b - GAP - h} ${x},${b - GAP} ${x - h},${b - GAP - h}`;
  switch (s) {
    case 'a': return H(y0, x0, x1); case 'g': return H(ym, x0, x1); case 'd': return H(y1, x0, x1);
    case 'f': return V(x0, y0, ym); case 'b': return V(x1, y0, ym); case 'e': return V(x0, ym, y1); default: return V(x1, ym, y1);
  }
};
const ALL = 'abcdefg'.split('');
/** native size of a SegText string (cells + spacing) */
export const segSize = (text: string, space = 0.42) => ({ w: text.length * CW + (text.length - 1) * CW * space, h: CH });
export const SegText: React.FC<{ text: string; color?: string; ghost?: number; glow?: number; space?: number; on?: number }> = ({ text, color = '#fdf3d8', ghost = 0.07, glow = 0.7, space = 0.42, on = 1 }) => {
  const { w, h } = segSize(text, space);
  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} style={{ position: 'absolute', left: 0, top: 0, overflow: 'visible',
      filter: glow > 0 ? `drop-shadow(0 0 ${(4 * glow).toFixed(1)}px ${color}) drop-shadow(0 0 ${(12 * glow).toFixed(1)}px ${color})` : undefined }}>
      {text.split('').map((ch, i) => {
        const lit = MAP[ch] ?? '';
        return (
          <g key={i} transform={`translate(${i * CW * (1 + space)}, 0)`}>
            {ALL.map((s) => <polygon key={s} points={seg(s)} fill={color} opacity={lit.includes(s) ? on : ghost} />)}
          </g>
        );
      })}
    </svg>
  );
};
/** a visor's digit row on a plate (stage px quad TL, TR, BR, BL around the row): the string fills the row's height, centred */
export const VisorSeg: React.FC<{ text: string; quad: Quad; color?: string; on?: number; ghostText?: string }> = ({ text, quad, color, on = 1 }) => {
  // left-aligned in a fixed 3-cell row: 4 -> 42 -> 429 types into place on the sung digits (the unlit cells stay as ghost 8s)
  const n = Math.max(3, text.length); const t = text.padEnd(n, ' ');
  const { w, h } = segSize(t);
  return (
    <div style={{ position: 'absolute', inset: 0, mixBlendMode: 'screen', pointerEvents: 'none' }}>
      <ScreenInsert corners={quad} w={w} h={h}><SegText text={t} color={color} on={on} /></ScreenInsert>
    </div>
  );
};
// Digit rows measured on each plate's own digit render (plate px / 1.5 = stage px): the box of the baked digits, so the new face sits
// where the approved one did. K / 4G / 5B are near flat-on; 5A is the visor in perspective (the row's quad follows the glass).
const q = (x0: number, y0: number, x1: number, y1: number): Quad => [[x0 / 1.5, y0 / 1.5], [x1 / 1.5, y0 / 1.5], [x1 / 1.5, y1 / 1.5], [x0 / 1.5, y1 / 1.5]];
export const VISOR_ROWS: Record<string, { quad: Quad; color: string }> = {
  K: { quad: q(1745, 928, 2206, 1076), color: '#fdf3d8' },
  '4G': { quad: q(1560, 566, 2045, 723), color: '#fdf3d8' },
  '5B': { quad: q(1659, 701, 2059, 820), color: '#c9ffe0' },
  '5A': { quad: [[1172 / 1.5, 205 / 1.5], [2229 / 1.5, 37 / 1.5], [2229 / 1.5, 561 / 1.5], [1172 / 1.5, 620 / 1.5]], color: '#fdf3d8' },
};

// ---- words on a visor (her H7.8 square robotic face + PLAN7 C4 "visor text aligned"): a 5x7 LED dot matrix, square dots ----
// One size per shot (no per-line auto-fit jumping), each line centred optically on the glass (the 7-row cap block, not a font box),
// equal side margins (>= 8% of the glass), the rows following the glass's curve (bulge), unlit dots a faint ghost, a 1 px bloom.
const F57: Record<string, string> = {
  A: '01110100011000111111100011000110001', B: '11110100011000111110100011000111110', C: '01110100011000010000100001000101110',
  D: '11110100011000110001100011000111110', E: '11111100001000011110100001000011111', F: '11111100001000011110100001000010000',
  G: '01110100011000010111100011000101111', H: '10001100011000111111100011000110001', I: '01110001000010000100001000010001110',
  J: '00111000100001000010000101001001100', K: '10001100101010011000101001001010001', L: '10000100001000010000100001000011111',
  M: '10001110111010110101100011000110001', N: '10001100011100110101100111000110001', O: '01110100011000110001100011000101110',
  P: '11110100011000111110100001000010000', Q: '01110100011000110001101011001001101', R: '11110100011000111110101001001010001',
  S: '01111100001000001110000010000111110', T: '11111001000010000100001000010000100', U: '10001100011000110001100011000101110',
  V: '10001100011000110001100010101000100', W: '10001100011000110101101011010101010', X: '10001100010101000100010101000110001',
  Y: '10001100010101000100001000010000100', Z: '11111000010001000100010001000011111',
  '0': '01110100011001110101110011000101110', '1': '00100011000010000100001000010001110', '2': '01110100010000100010001000100011111',
  '3': '11111000100010000010000011000101110', '4': '00010001100101010010111110001000010', '5': '11111100001111000001000011000101110',
  '6': '00110010001000011110100011000101110', '7': '11111000010001000100010000100001000', '8': '01110100011000101110100011000101110',
  '9': '01110100011000101111000010001001100', '!': '00100001000010000100001000000000100', '?': '01110100010000100010001000000000100',
  '%': '11000110010001000100010001001100011', '.': '00000000000000000000000000110001100', ':': '00000011000110000000011000110000000',
  '-': '00000000000000011111000000000000000', "'": '00100001000100000000000000000000000', ' ': '00000000000000000000000000000000000',
};
/** native size of LED text at dot pitch p (5x7 cells + 1 column of space) */
export const ledSize = (text: string, p: number) => ({ w: (text.length * 6 - 1) * p, h: 7 * p });
export const VisorText: React.FC<{
  lines: string[]; quad: Quad; w?: number; h?: number; pitch?: number; color?: string; ghost?: number; bulge?: number; lineGap?: number; on?: number;
}> = ({ lines, quad, w = 1000, h = 300, pitch, color = '#BFF4FF', ghost = 0.06, bulge = 0.05, lineGap = 2.5, on = 1 }) => {
  // one pitch for the whole shot: the longest line fits 84% of the glass width, all lines fit 80% of its height
  const cols = Math.max(...lines.map((l) => l.length * 6 - 1)), rows = lines.length * 7 + (lines.length - 1) * lineGap;
  const p = pitch ?? Math.min((w * 0.84) / cols, (h * 0.8) / rows);
  const top0 = (h - rows * p) / 2; const dot = p * 0.78, r = p * 0.12;
  const dots: React.ReactNode[] = [];
  lines.forEach((line, li) => {
    const lw = (line.length * 6 - 1) * p, x0 = (w - lw) / 2, y0 = top0 + li * (7 + lineGap) * p;
    line.toUpperCase().split('').forEach((ch, ci) => {
      const g = F57[ch] ?? F57[' '];
      for (let k = 0; k < 35; k++) {
        const x = x0 + (ci * 6 + (k % 5)) * p, yb = y0 + Math.floor(k / 5) * p;
        const u = (x + p / 2) / w * 2 - 1; const y = yb + bulge * h * (1 - u * u) * 0.5;   // the rows follow the glass's curve
        const lit = g[k] === '1';
        dots.push(<rect key={`${li}-${ci}-${k}`} x={x + (p - dot) / 2} y={y + (p - dot) / 2} width={dot} height={dot} rx={r} fill={color} opacity={lit ? on : ghost} />);
      }
    });
  });
  return (
    <div style={{ position: 'absolute', inset: 0, mixBlendMode: 'screen', pointerEvents: 'none' }}>
      <ScreenInsert corners={quad} w={w} h={h}>
        <svg width={w} height={h} style={{ position: 'absolute', left: 0, top: 0, overflow: 'visible', filter: `drop-shadow(0 0 1px ${color}) drop-shadow(0 0 ${(p * 0.6).toFixed(1)}px ${color})` }}>{dots}</svg>
      </ScreenInsert>
    </div>
  );
};
