// Cut 7 life layers (PLAN7 §2): idle life on every block. All pure functions of the frame (abs = film frame, f = block-local).
//  breathe(f, ox, oy)   Mod for a character slice: 0.35% vertical scale anchored at (ox, oy) (feet/hips), 0.22 Hz.
//  blinkAmt(abs, seed)  0..1 eyes-closed amount: a 4-frame close/open every 3-5 s, never within 3 f of `avoid` frames.
//  Blink                an eyes-closed patch (P1/P2) faded in by blinkAmt; draw it inside the character's slice (SliceCam `on`).
//  voice(abs)           his voice envelope 0..1 (src/data/c7_voice.json, from the robot-voice WAV); idlePulse(abs) 0.5 Hz breath.
//  Glow                 a soft elliptical light (screen blend) at stage (x, y): visor, chest light, screen glow, neon spill.
//  neonBuzz(abs, seed)  opacity of a neon/emission layer: a faint hum + a rare 2-3 frame flicker (seeded, never on a cut).
//  Steam / Dust / Rain  procedural (seeded) wisps, motes in a light shaft, drops sliding down glass, in stage px.
import React from 'react';
import { AbsoluteFill, Img, staticFile } from 'remotion';
import voiceRaw from '../../../data/c7_voice.json';
import { noise1 } from '../../../ease';
import { Mod } from './SliceCam';

const ENV: number[] = (voiceRaw as any).env;
const hash = (n: number, seed = 0) => { const x = Math.sin(n * 127.1 + seed * 311.7) * 43758.5453; return x - Math.floor(x); };

export const breathe = (f: number, ox: number, oy: number, amt = 0.0035, hz = 0.22, seed = 0): Mod => {
  const k = Math.sin((f / 30) * hz * 2 * Math.PI + seed);
  return { sy: 1 + amt * (0.5 + 0.5 * k), sx: 1 + amt * 0.25 * (0.5 + 0.5 * k), ox, oy };
};
/** 4-frame blink (close 2, open 2) every 3-5 s from a seeded schedule over the whole film */
export const blinkAmt = (abs: number, seed = 1, avoid: number[] = []) => {
  let t = 20 + Math.floor(hash(seed, 9) * 60);
  while (t <= abs + 4) {
    const near = avoid.some((a) => Math.abs(a - t) <= 3);
    if (!near && abs >= t && abs < t + 4) return [0.55, 1, 0.6, 0.15][abs - t];
    t += 90 + Math.floor(hash(t, seed) * 60);
  }
  return 0;
};
export const Blink: React.FC<{ src: string; abs: number; seed?: number; avoid?: number[]; style?: React.CSSProperties }> = ({ src, abs, seed = 1, avoid, style }) => {
  const a = blinkAmt(abs, seed, avoid);
  return a > 0.01 ? <Img src={staticFile(src)} style={{ position: 'absolute', left: 0, top: 0, width: 2560, height: 1440, opacity: a, ...style }} /> : null;
};
export const voice = (abs: number) => ENV[abs] ?? 0;
export const idlePulse = (abs: number, hz = 0.5, seed = 0) => 0.5 + 0.5 * Math.sin((abs / 30) * hz * 2 * Math.PI + seed);
/** visor/chest emission strength: his voice where he sings, else the idle pulse (0.35..0.65) */
export const visorK = (abs: number) => { const v = voice(abs); return v > 0.02 ? 0.45 + 0.55 * v : 0.35 + 0.3 * idlePulse(abs); };

export const Glow: React.FC<{ x: number; y: number; rx: number; ry?: number; color: string; op: number; blend?: React.CSSProperties['mixBlendMode']; rot?: number }> = ({ x, y, rx, ry, color, op, blend = 'screen', rot = 0 }) => {
  const h = ry ?? rx;
  return op > 0.003 ? (
    <div style={{ position: 'absolute', left: x - rx, top: y - h, width: 2 * rx, height: 2 * h, borderRadius: '50%', opacity: Math.min(1, op),
      background: `radial-gradient(closest-side, ${color} 0%, ${color} 18%, transparent 100%)`, mixBlendMode: blend, transform: rot ? `rotate(${rot}deg)` : undefined, pointerEvents: 'none' }} />
  ) : null;
};
/** neon hum: 0.94-1.0 slow shimmer + rare 2-3 f flickers (about one per 4 s), seeded; `avoid` frames (cuts) stay steady */
export const neonBuzz = (abs: number, seed = 2, avoid: number[] = []) => {
  const hum = 0.97 + 0.03 * noise1(abs / 7, seed);
  const slot = Math.floor(abs / 120), at = slot * 120 + Math.floor(hash(slot, seed) * 100);
  if (hash(slot, seed + 5) < 0.75 && abs >= at && abs < at + 3 && !avoid.some((a) => Math.abs(a - abs) <= 3)) return hum * [0.35, 0.8, 0.5][abs - at];
  return hum;
};

/** steam wisps rising from (x, y): n soft blobs, each rising h px over its life, swaying, growing, fading */
export const Steam: React.FC<{ abs: number; x: number; y: number; h?: number; w?: number; n?: number; op?: number; seed?: number; color?: string }> = ({ abs, x, y, h = 220, w = 60, n = 6, op = 0.28, seed = 4, color = '235,235,240' }) => {
  const life = 90;
  return (
    <>
      {Array.from({ length: n }, (_, i) => {
        const ph = (abs + (i * life) / n + hash(i, seed) * 10) % life; const u = ph / life;
        const sway = 18 * noise1((abs + i * 40) / 25, seed + i) * (0.3 + u);
        const r = w * (0.35 + 0.9 * u); const a = op * Math.sin(Math.PI * Math.min(1, u * 1.15)) * (1 - u * 0.5);
        return <div key={i} style={{ position: 'absolute', left: x + sway - r, top: y - u * h - r * 1.3, width: 2 * r, height: 2.6 * r, borderRadius: '50%',
          background: `radial-gradient(closest-side, rgba(${color},${a.toFixed(3)}), rgba(${color},0))`, filter: `blur(${(4 + 10 * u).toFixed(1)}px)` }} />;
      })}
    </>
  );
};
/** dust motes drifting in a light shaft (rect x, y, w, h), twinkling */
export const Dust: React.FC<{ abs: number; x: number; y: number; w: number; h: number; n?: number; op?: number; seed?: number; size?: number }> = ({ abs, x, y, w, h, n = 26, op = 0.5, seed = 6, size = 3 }) => (
  <>
    {Array.from({ length: n }, (_, i) => {
      const t = abs / 30; const px = x + ((hash(i, seed) * w + 14 * t * (hash(i, seed + 1) - 0.4) + 25 * noise1(t * 0.3, i + seed)) % w + w) % w;
      const py = y + ((hash(i, seed + 2) * h + 9 * t * (0.3 + hash(i, seed + 3)) + 18 * noise1(t * 0.25, i + seed + 50)) % h + h) % h;
      const a = op * (0.4 + 0.6 * Math.max(0, noise1(t * 0.8, i * 3 + seed)));
      const s = size * (0.6 + hash(i, seed + 4));
      return <div key={i} style={{ position: 'absolute', left: px, top: py, width: s, height: s, borderRadius: '50%', background: `rgba(255,236,200,${a.toFixed(3)})`, filter: 'blur(1px)' }} />;
    })}
  </>
);
/** rain on glass (rect): beads that sit, then run down with a short trail; seeded, continuous */
export const Rain: React.FC<{ abs: number; x: number; y: number; w: number; h: number; n?: number; op?: number; seed?: number; scale?: number }> = ({ abs, x, y, w, h, n = 40, op = 0.55, seed = 8, scale = 1 }) => (
  <div style={{ position: 'absolute', left: x, top: y, width: w, height: h, overflow: 'hidden' }}>
    {Array.from({ length: n }, (_, i) => {
      const period = 70 + Math.floor(hash(i, seed) * 90), ph = (abs + Math.floor(hash(i, seed + 1) * period)) % period;
      const run = ph > period * 0.55 ? (ph - period * 0.55) / (period * 0.45) : 0;      // sits, then runs
      const px = hash(i + 0.5 * Math.floor((abs + hash(i, seed + 1) * period) / period), seed + 2) * w;
      const py0 = hash(i + 0.37 * Math.floor((abs + hash(i, seed + 1) * period) / period), seed + 3) * h * 0.8;
      const py = py0 + run * run * h * 0.6; const r = (3 + 4 * hash(i, seed + 4)) * scale;
      return (
        <React.Fragment key={i}>
          {run > 0 ? <div style={{ position: 'absolute', left: px - r * 0.35, top: py0, width: r * 0.7, height: Math.max(0, py - py0), background: `linear-gradient(rgba(220,230,255,0), rgba(220,230,255,${(op * 0.35).toFixed(3)}))`, borderRadius: r }} /> : null}
          <div style={{ position: 'absolute', left: px - r, top: py - r, width: 2 * r, height: 2.3 * r, borderRadius: '50%',
            background: `radial-gradient(circle at 35% 30%, rgba(255,255,255,${(op).toFixed(3)}) 0%, rgba(200,215,240,${(op * 0.35).toFixed(3)}) 45%, rgba(20,25,40,${(op * 0.25).toFixed(3)}) 100%)` }} />
        </React.Fragment>
      );
    })}
  </div>
);
/** a light that waves: per-window brightness factor for lit windows (i = window index) */
export const windowFlicker = (abs: number, i: number, seed = 11) => 0.9 + 0.1 * noise1(abs / 18 + i * 3.1, seed + i) - (hash(Math.floor(abs / 45) + i * 17, seed) > 0.985 ? 0.4 : 0);
export const Shade: React.FC<{ op: number; color?: string }> = ({ op, color = '#000' }) => (op > 0.002 ? <AbsoluteFill style={{ background: color, opacity: op }} /> : null);
