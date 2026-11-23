// rl_secb: shared helpers for sections 7-9 (shots 7AB..9G). Imports rl_first30's kit read-only (never edits it).
// Plates and screen layers come from build/secb/prep_secb.py -> public/secb/ + ./assets.json (re-run it when a still lands).
import React from 'react';
import { AbsoluteFill, Img, staticFile } from 'remotion';
import { clamp, noise1 } from '../../ease';
import { Quad } from '../../blocks/ScreenInsert';
import { beatPulse, timeOf } from '../../timing';
import A from './assets.json';
export { Cam, PlateImg, MBlur, hit, swap, ez, keys, pendulum, flick, flickOut, Vignette, W, H } from '../first30/kit';

export const ASSETS = A as any;
export const LAY = ASSETS.layout as any;
/** stage scale for each still family (stills are bigger than the 2560 stage) */
export const K7 = 2560 / LAY.S7.size[0];      // S7 D1 (4320)
export const K8 = 2560 / LAY.S8.size[0];      // S8 C (4320)
export const K16 = 2560 / LAY.S16.size[0];    // S16 party (2880)
export const K17 = 2560 / LAY.S17.size[0];    // S17 routine (2880)
export const sc = (p: number[], k: number): [number, number] => [p[0] * k, p[1] * k];
export const box = (b: number[], k: number) => ({ x: b[0] * k, y: b[1] * k, w: (b[2] - b[0]) * k, h: (b[3] - b[1]) * k });

/** S7 D1: the glass leaf (the whole leaf is glass), stage px */
const LB = LAY.S7.door.leaf_box as number[];
export const D1_GLASS: Quad = [[LB[0] * K7, LB[1] * K7], [LB[2] * K7, LB[1] * K7], [LB[2] * K7, LB[3] * K7], [LB[0] * K7, LB[3] * K7]];

/** an image sequence named by master frame (f_<g>.ext), held at its ends */
export const seqSrc = (id: string, g: number) => {
  const s = ASSETS[id]; const n = Math.round(clamp(g, s.first, s.last));
  return `secb/${id}/f_${String(n).padStart(5, '0')}.${s.ext}`;
};
export const SeqImg: React.FC<{ id: string; g: number; style?: React.CSSProperties }> = ({ id, g, style }) => (
  <Img src={staticFile(seqSrc(id, g))} style={{ position: 'absolute', left: 0, top: 0, width: 2560, height: 1440, ...style }} />
);
/** a region still (RGBA crop) laid back onto its plate at its box (box in still px, k = stage scale) */
export const Region: React.FC<{ src: string; b: number[]; k: number; opacity?: number; style?: React.CSSProperties }> = ({ src, b, k, opacity = 1, style }) => {
  const r = box(b, k);
  return <Img src={staticFile(src)} style={{ position: 'absolute', left: r.x, top: r.y, width: r.w, height: r.h, opacity, ...style }} />;
};

/** the beat breath on holds: 0.6% on the kick (the grammar, item 2) */
export const breath = (g: number, amt = 0.006) => 1 + amt * beatPulse(timeOf(g), 0.22);
/** shot-local frames of the shot's beat grid */
export const gridF = (shot: { grid?: number[]; from: number }) => (shot.grid ?? []).map((t) => Math.round(t * 30) - shot.from);

/** a fine film grain + lens softness shared by code layers so nothing looks pasted on (deterministic per frame) */
export const Grain: React.FC<{ g: number; k?: number }> = ({ g, k = 0.05 }) => {
  const ox = Math.round(noise1(g * 0.37, 11) * 400), oy = Math.round(noise1(g * 0.53, 17) * 400);
  return (
    <AbsoluteFill style={{ pointerEvents: 'none', opacity: k, mixBlendMode: 'overlay',
      backgroundImage: 'repeating-radial-gradient(circle at 17% 31%, #fff 0 1px, #000 1px 3px), repeating-radial-gradient(circle at 71% 63%, #000 0 1px, #fff 1px 2.5px)',
      backgroundSize: '7px 7px, 11px 11px', backgroundPosition: `${ox}px ${oy}px, ${-oy}px ${ox}px` }} />
  );
};

/** a paper slip / card with crisp text (data-fit box), drawn in stage px; rides the camera if inside Cam */
export const Paper: React.FC<{ x: number; y: number; w: number; h: number; rot?: number; color?: string; children: React.ReactNode; style?: React.CSSProperties }> = ({ x, y, w, h, rot = 0, color = '#f3eee2', children, style }) => (
  <div style={{ position: 'absolute', left: x, top: y, width: w, height: h, transform: `rotate(${rot}deg)`, background: color,
    boxShadow: '0 14px 30px rgba(0,0,0,0.38), 0 2px 4px rgba(0,0,0,0.3)', borderRadius: 4, ...style }}>{children}</div>
);

/** S7 D1's lobby clocks at a given time: analog hands (the plate's clock has none) + the digital face over its baked digits */
import { AnalogClock } from '../../blocks/Clock';
import { FONT as _F } from '../../theme';
export { PandaD1Clocks as D1Clocks } from '../../blocks/PandaClock';
/** minutes after 6 PM from "4:39 AM" */
export const amMin = (h: number, m: number) => (h + 6) * 60 + m;
/** the Cam centre clamp, for screen-space projections of in-world boxes */
export const clampCamS = (cx: number, cy: number, s: number) => ({ cx: Math.min(2560 - 1280 / s, Math.max(1280 / s, cx)), cy: Math.min(1440 - 720 / s, Math.max(720 / s, cy)) });
