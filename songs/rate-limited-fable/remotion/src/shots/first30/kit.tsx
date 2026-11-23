// rl_first30: the shared kit for the first 30 seconds (shots 1A..2D). Pure functions of the frame.
//  Cam      a stage-space camera: puts stage point (cx, cy) at the centre, scaled s (children are in plate/stage px,
//           so everything drawn inside rides the move). The engine's <Plate> does not move its children, so these shots
//           use Cam + PlateImg instead.
//  MBlur    motion blur from shutter samples: renders the child at n sub-frame times and averages them (layer i at
//           opacity 1/(i+1) = an exact running mean).
//  hit / swap / flick / settle   the small moves every shot uses (camera hit, A-smear-B pose swap, 2-frame flicker).
import { c5p } from '../c5d/plates';   // rl5_d2: cut 5 plate swaps
import React from 'react';
import { AbsoluteFill, Img, staticFile } from 'remotion';
import { STAGE_H, STAGE_W } from '../../theme';
import { clamp, inOutCubic, lerp, outCubic } from '../../ease';

export const W = STAGE_W, H = STAGE_H;

export const Cam: React.FC<{ cx?: number; cy?: number; s?: number; r?: number; dx?: number; dy?: number; ph?: number; children: React.ReactNode; style?: React.CSSProperties }> = ({ cx = W / 2, cy = H / 2, s = 1, r = 0, dx = 0, dy = 0, ph = H, children, style }) => {
  // never show past the plate edge (ph = the plate's height in stage px, for tall plates; v3)
  const hw = W / 2 / s, hh = H / 2 / s;
  const x = clamp(cx, hw, W - hw), y = clamp(cy, hh, ph - hh);
  return (
    <AbsoluteFill style={{ transformOrigin: '0 0', transform: `translate(${(W / 2 + dx).toFixed(2)}px, ${(H / 2 + dy).toFixed(2)}px) rotate(${r.toFixed(3)}deg) scale(${s.toFixed(5)}) translate(${(-x).toFixed(2)}px, ${(-y).toFixed(2)}px)`, ...style }}>
      {children}
    </AbsoluteFill>
  );
};
/** clamp a camera centre so the frame stays inside the plate (same rule Cam uses) */
export const clampCam = (cx: number, cy: number, s: number) => ({ cx: clamp(cx, W / 2 / s, W - W / 2 / s), cy: clamp(cy, H / 2 / s, H - H / 2 / s) });

/** a still filling the stage (any 16:9 size is scaled to 2560x1440) */
export const PlateImg: React.FC<{ src: string; filter?: string; opacity?: number; style?: React.CSSProperties }> = ({ src, filter, opacity = 1, style }) => (
  <Img src={staticFile(c5p(src))} style={{ position: 'absolute', left: 0, top: 0, width: W, height: H, filter, opacity, ...style }} />
);

/** motion blur: render(t) at n shutter samples spread over `shutter` frames centred on 0 */
export const MBlur: React.FC<{ n?: number; shutter?: number; on?: boolean; render: (dt: number) => React.ReactNode }> = ({ n = 5, shutter = 0.5, on = true, render }) => {
  if (!on || n <= 1) return <>{render(0)}</>;
  return (
    <>
      {Array.from({ length: n }, (_, i) => {
        const dt = (i / (n - 1) - 0.5) * shutter;
        return <AbsoluteFill key={i} style={{ opacity: 1 / (i + 1) }}>{render(dt)}</AbsoluteFill>;
      })}
    </>
  );
};

/** a camera hit: 0 before `at`, punches to `amt` in 2 frames, settles back with one small rebound by `len` */
export const hit = (f: number, at: number, amt = 0.015, len = 12) => {
  const d = f - at; if (d < 0) return 0;
  if (d < 2) return amt * outCubic(d / 2);
  const k = clamp((d - 2) / len); return amt * Math.exp(-4 * k) * Math.cos(k * Math.PI * 1.6) * (1 - k);
};
/** A-smear-B: 'A' before `at`, 'S' for `hold` frames, then 'B' */
export const swap = (f: number, at: number, hold = 2): 'A' | 'S' | 'B' => (f < at ? 'A' : f < at + hold ? 'S' : 'B');
/** a light coming on at `at`: two flicker frames then on (0..1) */
export const flick = (f: number, at: number) => { const d = f - at; if (d < 0) return 0; if (d < 1) return 0.65; if (d < 2) return 0.12; if (d < 3) return 0.85; return 1; };
/** a light going out at `at`: one flicker frame then off (1..0) */
export const flickOut = (f: number, at: number) => { const d = f - at; if (d < 0) return 1; if (d < 1) return 0.25; if (d < 2) return 0.7; if (d < 3) return 0.15; return 0; };
/** eased 0..1 over [a, b] */
export const ez = (f: number, a: number, b: number, e: (k: number) => number = inOutCubic) => e(clamp((f - a) / Math.max(1e-6, b - a)));
/** keyframed value: [[frame, value], ...] with an easing per segment */
export const keys = (f: number, ks: [number, number][], e: (k: number) => number = inOutCubic) => {
  if (f <= ks[0][0]) return ks[0][1];
  for (let i = 1; i < ks.length; i++) if (f <= ks[i][0]) return lerp(ks[i - 1][1], ks[i][1], e((f - ks[i - 1][0]) / Math.max(1e-6, ks[i][0] - ks[i - 1][0])));
  return ks[ks.length - 1][1];
};
/** damped pendulum angle (deg): released at `at` from amp, period p frames, settles with damping d */
export const pendulum = (f: number, at: number, amp: number, p: number, d = 2.2) => { const t = Math.max(0, f - at) / p; return f < at ? 0 : amp * Math.exp(-d * t) * Math.cos(2 * Math.PI * t); };

/** a soft vignette + grain-free light falloff, so code-built inserts sit in the same lens as the plates */
export const Vignette: React.FC<{ k?: number }> = ({ k = 0.45 }) => (
  <AbsoluteFill style={{ background: `radial-gradient(ellipse 75% 70% at 50% 48%, rgba(0,0,0,0) 55%, rgba(0,0,0,${k}) 100%)`, pointerEvents: 'none' }} />
);

/** HeroClip slot: when a hero render lands (heroes.json ready=true) its frames play here; until then `fallback` shows. */
import heroes from './heroes.json';
type Hero = { ready: boolean; dir: string; first: number; last: number; pad?: number; ext?: string; alpha?: boolean };
export const heroReady = (id: string) => !!(heroes as unknown as Record<string, Hero>)[id]?.ready;
export const HeroClip: React.FC<{ id: string; g: number; fallback: React.ReactNode }> = ({ id, g, fallback }) => {
  const h = (heroes as unknown as Record<string, Hero>)[id];
  if (!h || !h.ready) return <>{fallback}</>;
  const fr = Math.round(clamp(g, h.first, h.last));
  const src = `${h.dir}/f_${String(fr).padStart(h.pad ?? 5, '0')}.${h.ext ?? 'png'}`;
  return <>{h.alpha ? fallback : null}<PlateImg src={src} /></>;
};
