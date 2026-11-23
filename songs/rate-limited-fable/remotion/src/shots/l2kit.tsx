// lane L2 (rl_l2_act, cut 4): the kit her acting shots share. Pure functions of the frame.
// Plates are lane L2's Blender stills (public/l2/, data in l2data.ts written by workers/rl_l2_act/prep_l2.py).
import { c5p } from './c5d/plates';   // rl5_d2: cut 5 plate swaps
import React from 'react';
import { AbsoluteFill, Img, staticFile } from 'remotion';
import { L2P } from './l2data';
import { C4SIGN } from './c4sign';
import { C4FIX } from './c4fix';
import { clamp } from '../ease';

export const SW = 2560, SH = 1440;

/** a plate filling the stage; `fallback` (an older plate path) if lane L2's render is not in yet */
export const L2Img: React.FC<{ id: string; layer?: 'src' | 'fg' | 'hair' | 'clean' | 'pop1' | 'pop2' | 'pop3'; fallback?: string; style?: React.CSSProperties }> = ({ id, layer = 'src', fallback, style }) => {
  const p = L2P[id]; const key = layer === 'src' ? id : `${id}:${layer}`; const c4 = C4FIX[key] ?? C4SIGN[key];        // rl_cut4_fix overrides first        // rl_cut4: the 'Last Warning' neon re-render (c4sign.ts)
  const src = c4 ?? (p ? (p[layer] as string | undefined) : undefined);
  const s = src ?? (layer === 'src' ? fallback : undefined);
  if (!s) return null;
  return <Img src={staticFile(c5p(s))} style={{ position: 'absolute', left: 0, top: 0, width: SW, height: SH, ...style }} />;
};
export const hasL2 = (id: string, layer: 'src' | 'fg' | 'hair' | 'clean' = 'src') => !!(C4FIX[layer === 'src' ? id : `${id}:${layer}`] || C4SIGN[layer === 'src' ? id : `${id}:${layer}`] || (L2P[id] && (L2P[id] as Record<string, unknown>)[layer]));   // rl_cut4: c4sign plates/layers count

/** local frame of a grid beat (fallback if the shot has no grid) */
export const beat = (shot: { from: number; grid?: number[] }, i: number, fallback: number) => {
  const t = shot.grid?.[i]; return t == null ? fallback : Math.round(t * 30) - shot.from;
};

/** §2c the vibration plate: a 12-15 Hz shake of her + Cooper + the plate (fg layer) with shutter blur, her curls and the pom-pom on their own
 *  layer a quarter-cycle late and a little bigger, so they bounce; the room (clean layer) still. amp in stage px. If the layers are not in
 *  (previews), the whole still shakes gently instead. */
export const PlateJiggle: React.FC<{ id: string; g: number; amp: number; hz?: number; fallback?: string }> = ({ id, g, amp, hz = 13.5, fallback }) => {
  const off = (t: number, lag: number, k: number) => {
    const ph = 2 * Math.PI * hz * (t / 30) - lag;
    return [amp * k * 0.35 * Math.sin(ph * 0.5 + 1.1), amp * k * Math.sin(ph)] as [number, number];
  };
  const N = 5, shutter = 0.5;
  const samples = (lag: number, k: number) => Array.from({ length: N }, (_, i) => off(g + (i / (N - 1) - 0.5) * shutter, lag, k));
  if (!hasL2(id, 'fg') || !hasL2(id, 'clean')) {
    const s = samples(0, 0.35);
    return (
      <AbsoluteFill>
        {s.map(([dx, dy], i) => <AbsoluteFill key={i} style={{ opacity: 1 / (i + 1), transform: `translate(${dx.toFixed(2)}px, ${dy.toFixed(2)}px)` }}><L2Img id={id} fallback={fallback} /></AbsoluteFill>)}
      </AbsoluteFill>
    );
  }
  const a = samples(0, 1), b = samples(Math.PI / 2, 1.7);
  return (
    <AbsoluteFill>
      <L2Img id={id} layer="clean" />
      {a.map(([dx, dy], i) => <AbsoluteFill key={`a${i}`} style={{ opacity: 1 / (i + 1), transform: `translate(${dx.toFixed(2)}px, ${dy.toFixed(2)}px)` }}><L2Img id={id} layer="fg" /></AbsoluteFill>)}
      {hasL2(id, 'hair') ? b.map(([dx, dy], i) => <AbsoluteFill key={`b${i}`} style={{ opacity: 1 / (i + 1), transform: `translate(${dx.toFixed(2)}px, ${dy.toFixed(2)}px)` }}><L2Img id={id} layer="hair" /></AbsoluteFill>) : null}
    </AbsoluteFill>
  );
};

/** rl_cut4: the per-sample offsets PlateJiggle gives her (the fg layer, or the whole still without layers), with each sample's
 *  opacity, so a code layer pinned on her (9C's phone screen) rides the same shake. */
export const jiggleSamples = (id: string, g: number, amp: number, hz = 13.5): { dx: number; dy: number; op: number }[] => {
  const layers = hasL2(id, 'fg') && hasL2(id, 'clean'); const k = layers ? 1 : 0.35, N = 5, shutter = 0.5;
  return Array.from({ length: N }, (_, i) => {
    const t = g + (i / (N - 1) - 0.5) * shutter; const ph = 2 * Math.PI * hz * (t / 30);
    return { dx: amp * k * 0.35 * Math.sin(ph * 0.5 + 1.1), dy: amp * k * Math.sin(ph), op: 1 / (i + 1) };
  });
};

/** a hard pose cut held on the beat, with a 2-frame settle (the cut lands with the camera a hair bigger) */
export const settle = (f: number, at: number, amt = 0.012) => { const d = f - at; return d < 0 ? 0 : amt * Math.exp(-d / 3) * (d < 1 ? 1 : 0.6); };
export const ramp = (f: number, a: number, b: number) => clamp((f - a) / Math.max(1e-6, b - a));

/** a pinned face's quad scaled toward its centre (the dial square was measured to the case's lugs: k ~0.84 sits on the case) */
export const shrinkQuad = <Q extends [number, number][]>(q: Q, k: number): Q => {
  const cx = q.reduce((m, p) => m + p[0], 0) / q.length, cy = q.reduce((m, p) => m + p[1], 0) / q.length;
  return q.map(([x, y]) => [cx + (x - cx) * k, cy + (y - cy) * k]) as Q;
};
