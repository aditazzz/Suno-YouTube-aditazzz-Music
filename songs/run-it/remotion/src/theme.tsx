// The locked look (design/frames.html, approved round 2). Palette rules: pink ONLY on the dot, purple ONLY on the car,
// magenta ONLY in the crash. No grain, restrained bloom.
import React, { createContext, useContext } from 'react';
import { useCurrentFrame, useVideoConfig } from 'remotion';
import { FPS, sectionAt } from './timing';
import PJ from './data/palette.json';

// Colours come from the creative director's palette (src/data/palette.json, PALETTE.md; director approved 02:15).
// Key names and value shapes are unchanged (strings; the alpha ones are now #rrggbbaa, which CSS/SVG and mixC read).
export const P = PJ as typeof PJ;
export const C = {
  bg: P.v1.bg,                    // design canvas (frame 1)
  dotGrid: P.v1.ghost,            // was white 8%; now cool #c8e1eb 8%
  text: P.ui.promptText,          // prompt text
  barBg: P.ui.barBg,
  barBorder: P.ui.barBorder,
  meter: P.ui.meter, meterAmber: P.ui.meterAmber, meterRed: P.ui.meterRed,
  pink: P.v1.dot,                 // the dot, only
  purple: P.v2.car, purpleHi: P.v2.carHi, purpleLo: P.v2.carLo, caliper: P.v2.caliper, // the car, only
  magenta: P.crash.missing,       // the crash, only
  red: P.v1.redButton,            // the red button (was #ff2e43; now #ff4630, director OK 02:15)
  night: [P.v2.skyTop, P.v2.skyHorizon], windowAmber: P.v2.window, windowWhite: P.v2.windowCool,
  wire: P.ch2.wire,
};
export const FONT = 'JBM, "JetBrains Mono", ui-monospace, monospace';
// JetBrains Mono Medium (500): public/fonts/JBMono-500.ttf (JetBrains Mono Medium 2.304, OFL; the real file, no stroke stand-in).
export const MED: React.CSSProperties = { fontFamily: FONT, fontWeight: 500 };
/** Paper theme (the white intro page, 0-17.9 s) for the in-scene UI. k = 0 paper .. 1 dark (the approved look). */
export const PAPER = { page: P.intro.bg, canvas: P.intro.surface, ink: P.intro.ink, inkSoft: P.ui.paperInkSoft, grid: P.ui.paperGrid };
const hex = (h: string) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
/** #rrggbb, #rrggbbaa (palette ghosts) or rgba() -> [r, g, b, a] */
const rgbaP = (c: string): number[] => c.startsWith('#') ? [...hex(c), c.length >= 9 ? parseInt(c.slice(7, 9), 16) / 255 : 1] : (c.match(/[\d.]+/g) as string[]).map(Number);
/** a palette colour as rgba() with alpha a (multiplies a #rrggbbaa ghost's own alpha) */
export const rgbaOf = (c: string, a = 1) => { const v = rgbaP(c); return `rgba(${v[0]},${v[1]},${v[2]},${((v[3] ?? 1) * a).toFixed(3)})`; };
/** mix two CSS colours (#rrggbb or rgba()) at k 0..1 */
export const mixC = (a: string, b: string, k: number) => {
  const A = rgbaP(a), B = rgbaP(b); const m = A.map((v, i) => v + ((B[i] ?? 1) - v) * k);
  return `rgba(${Math.round(m[0])},${Math.round(m[1])},${Math.round(m[2])},${(m[3] ?? 1).toFixed(3)})`;
};

export type Fmt = '16x9' | '9x16';
export type Layout = {
  fmt: Fmt; W: number; H: number;
  // bottom: the docked bar's bottom edge; lh: text line height; cols: columns per line (balanced wrap);
  // pad: [top, right, bottom, left] inside the border; chev: chevron column; centreLift/centreDx: the intro/loop
  // centred position (overlay barLift 440 = BAR_CENTRE_LIFT maps to centreLift px up and centreDx px right). rc_916.
  bar: { x: number; y: number; w: number; h: number; font: number; bottom?: number; lh?: number; cols?: number;
    pad?: [number, number, number, number]; chev?: number; centreLift?: number; centreDx?: number };
  meter: { x: number; y: number; w: number; label: number };
  dot: { cx: number; cy: number; scale: number };
  stage?: { x0: number; y0: number; x1: number; y1: number; cx: number; cy: number }; // key picture lives here (9:16)
  chip?: { x: number; y: number; h: number };  // top-left chip slot (pass labels, corner pills)
};
// 16:9 = the approved frames exactly. 9:16 = LAYOUT_916.md (cd_916, director approved 03:25): a phone chat, the
// composer docked bottom-left with the platform's button column as its right gutter.
export const LAYOUTS: Record<Fmt, Layout> = {
  '16x9': { fmt: '16x9', W: 1920, H: 1080, bar: { x: 370, y: 930, w: 1180, h: 100, font: 42, bottom: 1030, lh: 52.5, cols: 99 },
    meter: { x: 1540, y: 64, w: 300, label: 34 }, dot: { cx: 960, cy: 470, scale: 1 } },
  '9x16': { fmt: '9x16', W: 1080, H: 1920,
    bar: { x: 110, y: 1204, w: 750, h: 126, font: 58, bottom: 1330, lh: 70, cols: 18, pad: [26, 20, 26, 24], chev: 42, centreLift: 388, centreDx: 55 },
    meter: { x: 664, y: 272, w: 300, label: 34 }, dot: { cx: 540, cy: 680, scale: 1.35 },
    stage: { x0: 116, y0: 250, x1: 964, y1: 1110, cx: 540, cy: 680 }, chip: { x: 116, y: 262, h: 56 } },
};
export const LayoutCtx = createContext<Layout>(LAYOUTS['16x9']);
export const useLayout = () => useContext(LayoutCtx);

// Absolute film time inside a <Shot> (Sequences reset the frame; `from` is added back).
export const FromCtx = createContext(0);
export const useAbsFrame = () => useCurrentFrame() + useContext(FromCtx);
export const useT = () => useAbsFrame() / useVideoConfig().fps;
export { FPS };

// Per-section palette: the section at film time t -> its palette.json block (so the bg steps v1 #050507 -> ch1 #070b14
// -> v2 #0a0f1a live in one place). sections.json names -> palette sections.
export type SectionPalette = Record<string, string>;
const SEC_TO_PAL: Record<string, keyof typeof PJ> = {
  INTRO: 'intro', V1: 'v1', PRE1: 'v1', CH1: 'ch1', POST1: 'ch1', V2: 'v2', PRE2: 'v2', CH2: 'ch2', POST2: 'ch2',
  BRIDGE: 'middle3d', BREAK: 'crash', CRASH: 'crash', FINAL: 'final', OUTRO: 'outro',
};
export const sectionPalette = (t: number): SectionPalette =>
  (P as unknown as Record<string, SectionPalette>)[SEC_TO_PAL[sectionAt(t).name] ?? 'v1'];
