// rl_seca: shared helpers for sections 3-6 (shots 3A..6D). Own copy of the first30 kit patterns (so a change there never
// moves these shots), plus the props these sections reuse: the 429 paddle, paper slips/notes, the lobby clock, image
// sequences (rl_screens layers), the neon region swap and a code wall clock. Pure functions of the frame.
//
// PLATES: every shot names its plate in one constant at the top of its file (`P.<key>`), so a landed still is one swap.
import { c5p } from '../c5d/plates';   // rl5_d2: cut 5 plate swaps
import React from 'react';
import { AbsoluteFill, Img, staticFile } from 'remotion';
import { FONT, STAGE_H, STAGE_W } from '../../theme';
import { clamp, inOutCubic, lerp, outCubic } from '../../ease';
import { BEATS, frameOf, Shot } from '../../timing';
import { ScreenInsert, Quad } from '../../blocks/ScreenInsert';
import assets from '../first30/assets.json';

export const W = STAGE_W, H = STAGE_H;

/** placeholder plates (nearest approved) and the stills that replace them (CODEPLAN NEW STILLS) */
export const P = {
  door: 'cutfix/door_rain_al.jpg',    // rl_cutfix: the Rain door (door_r3, Rain her) aligned to the old door.jpg stage (s .907, -15/-10 px); was plates/door.jpg (old her)
  close: 'plates/close.jpg',          // approved CLOSE with bubbles
  C0: 'first30/C0.jpg', C0s: 'first30/C0s.jpg', C1: 'first30/C1.jpg',   // S8 (4320 px)
  M1: 'first30/M1.jpg', M1n: 'first30/M1_needle.png',                     // S6 (5760 px)
  b2b: 'cutfix/room_b2b_rain.jpg',    // rl_cutfix: the approved Rain B2B (same camera; only her pixels differ from plates/room_b2b.jpg)
  routine: 'cutfix/room_routine_rain.jpg',   // rl_cutfix: the approved Rain routine (same camera; only her differs)
  D1: 'seca/plates/D1.jpg', D1nod: 'seca/plates/D1nod_region.png', signBack: 'seca/plates/sign_back_at_6.png',   // S7 (final, 4320 px)
  T6: 'seca/plates/T6.jpg',                                                     // S13 (5760 px)
  signFlicker: 'plates/sign_flicker.jpg', signLieDown: 'plates/sign_lie_down.jpg',
};

/** stage camera: puts stage point (cx, cy) at the frame centre at scale s; children ride the move. Never shows past the plate. */
export const Cam: React.FC<{ cx?: number; cy?: number; s?: number; r?: number; children: React.ReactNode; free?: boolean; creep?: number }> = ({ cx = W / 2, cy = H / 2, s: s0 = 1, r = 0, children, free, creep = 0 }) => {
  const s = s0 * (1 + 0.014 * clamp(creep));
  const hw = W / 2 / s, hh = H / 2 / s;
  const x = free ? cx : clamp(cx, hw, W - hw), y = free ? cy : clamp(cy, hh, H - hh);
  return (
    <AbsoluteFill style={{ transformOrigin: '0 0', transform: `translate(${W / 2}px, ${H / 2}px) rotate(${r.toFixed(3)}deg) scale(${s.toFixed(5)}) translate(${(-x).toFixed(2)}px, ${(-y).toFixed(2)}px)` }}>
      {children}
    </AbsoluteFill>
  );
};
export const PlateImg: React.FC<{ src: string; filter?: string; opacity?: number; style?: React.CSSProperties }> = ({ src, filter, opacity = 1, style }) => (
  <Img src={staticFile(c5p(src))} style={{ position: 'absolute', left: 0, top: 0, width: W, height: H, filter, opacity, ...style }} />
);
/** motion blur from shutter samples (running mean) */
export const MBlur: React.FC<{ n?: number; shutter?: number; on?: boolean; render: (dt: number) => React.ReactNode }> = ({ n = 5, shutter = 0.5, on = true, render }) => {
  if (!on || n <= 1) return <>{render(0)}</>;
  return <>{Array.from({ length: n }, (_, i) => <AbsoluteFill key={i} data-fit={i ? 'off' : undefined} style={{ opacity: 1 / (i + 1) }}>{render((i / (n - 1) - 0.5) * shutter)}</AbsoluteFill>)}</>;
};
/** camera hit: punch to amt in 2-3 frames, settle with one small rebound */
export const hit = (f: number, at: number, amt = 0.015, len = 10) => {
  const d = f - at; if (d < 0) return 0;
  if (d < 3) return amt * outCubic(d / 3);
  const k = clamp((d - 3) / len); return amt * Math.exp(-4 * k) * Math.cos(k * Math.PI * 1.6) * (1 - k);
};
export const swap = (f: number, at: number, hold = 2): 'A' | 'S' | 'B' => (f < at ? 'A' : f < at + hold ? 'S' : 'B');
export const ez = (f: number, a: number, b: number, e: (k: number) => number = inOutCubic) => e(clamp((f - a) / Math.max(1e-6, b - a)));
export const keys = (f: number, ks: [number, number][], e: (k: number) => number = inOutCubic) => {
  if (f <= ks[0][0]) return ks[0][1];
  for (let i = 1; i < ks.length; i++) if (f <= ks[i][0]) return lerp(ks[i - 1][1], ks[i][1], e((f - ks[i - 1][0]) / Math.max(1e-6, ks[i][0] - ks[i - 1][0])));
  return ks[ks.length - 1][1];
};
/** settle after a slap/land: overshoot then rest (0 -> 1) */
export const land = (f: number, at: number, len = 8) => { const d = f - at; if (d <= 0) return 0; const k = clamp(d / len); return 1 + 0.12 * Math.sin(k * Math.PI * 1.5) * (1 - k) * (k < 1 ? 1 : 0) - (1 - outCubic(clamp(d / 3))); };
export const pendulum = (f: number, at: number, amp: number, p: number, d = 2.2) => { const t = Math.max(0, f - at) / p; return f < at ? 0 : amp * Math.exp(-d * t) * Math.cos(2 * Math.PI * t); };
/** shot-local frame of grid beat i (falls back to i beats of 17.4 frames) */
export const gb = (shot: Shot, i: number) => (shot.grid?.[i] !== undefined ? frameOf(shot.grid[i]) - shot.from : Math.round(i * 17.4));
/** the hold's breathing: 0.6% on each beat (kicks) from the verse 2 drums on; off in dead-still shots */
export const pulse = (g: number, amt = 0.006) => {
  const t = g / 30; let lo = 0, hi = BEATS.length; while (lo < hi) { const m = (lo + hi) >> 1; if (BEATS[m] <= t) lo = m + 1; else hi = m; }
  const b = BEATS[lo - 1]; if (b === undefined) return 0; const d = t - b; return d < 0 || d > 0.3 ? 0 : amt * Math.exp(-d * 14);
};

export const Vignette: React.FC<{ k?: number }> = ({ k = 0.45 }) => (
  <AbsoluteFill style={{ background: `radial-gradient(ellipse 75% 70% at 50% 48%, rgba(0,0,0,0) 55%, rgba(0,0,0,${k}) 100%)`, pointerEvents: 'none' }} />
);
/** one shared fine grain so code-built inserts sit in the same lens as the plates (deterministic per frame) */
export const Grain: React.FC<{ g: number; k?: number }> = ({ g, k = 0.05 }) => (
  <AbsoluteFill style={{ opacity: k, mixBlendMode: 'overlay', pointerEvents: 'none' }}>
    <svg width={W} height={H}><filter id={`gr${g % 7}`}><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves={2} seed={g % 97} /></filter>
      <rect width={W} height={H} filter={`url(#gr${g % 7})`} /></svg>
  </AbsoluteFill>
);

/** an rl_screens frame sequence (named by master frame), clamped to its range */
export const Seq: React.FC<{ dir: string; g: number; first: number; last: number; style?: React.CSSProperties; w?: number; h?: number }> = ({ dir, g, first, last, style, w = W, h = H }) => {
  const fr = Math.round(clamp(g, first, last));
  return <Img src={staticFile(`${dir}/f_${String(fr).padStart(5, '0')}.png`)} style={{ position: 'absolute', left: 0, top: 0, width: w, height: h, ...style }} />;
};
export const SCREENS = {
  phone_3C: [1324, 1404], phone_6B: [2921, 3002], watch_6C: [2991, 3071], laptop_5E: [2574, 2655], glass_5H: [2782, 2863],
} as Record<string, [number, number]>;

// ---------- props ----------
export const HAND = 'Noteworthy, "Marker Felt", "Chalkboard SE", "Bradley Hand", cursive';
export const RED = '#c8352b', INK = '#2a2622', PAPER = '#efe9dc';

/** the round 429 paddle (matches the approved one: cream disc, red rim, dark print, wooden handle). Centre (x, y), disc radius r. */
export const Paddle: React.FC<{ x: number; y: number; r?: number; code?: string; rot?: number; green?: boolean; worn?: boolean; handle?: number }> = ({ x, y, r = 120, code = '429', rot = 0, green, worn, handle = 2.6 }) => {
  const rim = green ? '#3f8a5a' : RED;
  return (
    <div style={{ position: 'absolute', left: x, top: y, width: 0, height: 0, transform: `rotate(${rot}deg)` }}>
      <div style={{ position: 'absolute', left: -r * 0.09, top: r * 0.8, width: r * 0.18, height: r * handle, borderRadius: r * 0.05, background: 'linear-gradient(90deg,#6b4a2c,#a87a4c 45%,#5a3d24)', boxShadow: '0 6px 14px rgba(0,0,0,0.35)' }} />
      <div data-fit="off" style={{ position: 'absolute', left: -r, top: -r, width: 2 * r, height: 2 * r, borderRadius: '50%', boxSizing: 'border-box', border: `${r * 0.13}px solid ${rim}`,
        background: 'radial-gradient(circle at 38% 32%, #f4efe3, #d9d2c2 75%, #bdb5a4)', boxShadow: '0 10px 24px rgba(0,0,0,0.4), inset 0 -6px 14px rgba(0,0,0,0.15)',
        display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: FONT.brand, fontSize: r * (code.length > 3 ? 0.42 : 0.72), color: '#3b3733', lineHeight: 1, textAlign: 'center',
        opacity: 1, filter: worn ? 'sepia(0.35) contrast(0.92)' : undefined }}>{code}</div>
    </div>
  );
};

/** a paper slip / note with handwriting, w x h, centred at (x, y), rotated */
export const Note: React.FC<{ x: number; y: number; w: number; h: number; rot?: number; text: string; size?: number; color?: string; paper?: string; font?: string; style?: React.CSSProperties }> = ({ x, y, w, h, rot = 0, text, size = 60, color = INK, paper = PAPER, font = HAND, style }) => (
  <div data-fit="box" style={{ position: 'absolute', left: x - w / 2, top: y - h / 2, width: w, height: h, transform: `rotate(${rot}deg)`, background: paper, borderRadius: 4,
    boxShadow: '0 8px 18px rgba(0,0,0,0.45)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 14, boxSizing: 'border-box', ...style }}>
    <div style={{ fontFamily: font, fontSize: size, color, lineHeight: 1.05, textAlign: 'center', whiteSpace: 'pre-wrap' }}>{text}</div>
  </div>
);

/** the lobby's digital clock on the S8 close plates (C0/C1), corners from its layout.json; blurred to the plate's focus */
const lay = (assets as any).S8_C_layout; const K8 = 2560 / lay.size[0];
export const C_CLOCK = lay.clock.corners_TL_TR_BR_BL.map(([x, y]: number[]) => [x * K8, y * K8]) as Quad;
export const C_PADDLE = [lay.paddle_face_centre_C1[0] * K8, lay.paddle_face_centre_C1[1] * K8] as [number, number];
export { PandaLobbyClockS8 as LobbyClock } from '../../blocks/PandaClock';
/** the meter (S6 M1): hub pivot and needle rotation for a value */
const lm = (assets as any).S6_M1_layout; const K6 = 2560 / lm.size[0];
export const M_PIV: [number, number] = [lm.pivot[0] * K6, lm.pivot[1] * K6];
export const needleRot = (v: number) => (270 * (v - (lm.needle.rendered_at_value as number))) / 24;

/** the neon over her sofa on B2B: region renders (2880-px crops) placed exactly (measured by template match, Nov 15) */
export const SIGN_REGION = {
  flicker: { src: P.signFlicker, x: 1224.9, y: 260.4, w: 768, h: 496 },
  lieDown: { src: P.signLieDown, x: 1224.9, y: 267.6, w: 768, h: 481.8 },
};
export const SignRegion: React.FC<{ which: keyof typeof SIGN_REGION; opacity: number }> = ({ which, opacity }) => {
  const r = SIGN_REGION[which];
  return <Img src={staticFile(r.src)} style={{ position: 'absolute', left: r.x, top: r.y, width: r.w, height: r.h, opacity,
    WebkitMaskImage: 'radial-gradient(ellipse 48% 46% at 50% 50%, #000 70%, transparent 100%)', maskImage: 'radial-gradient(ellipse 48% 46% at 50% 50%, #000 70%, transparent 100%)' }} />;
};

/** a plain wall clock drawn in code (hands in code, as all the film's clocks): minutes since midnight + seconds */
export { PandaWallClockMinutes as WallClock } from '../../blocks/PandaClock';

/** S7 D1 layout (4320 px) -> stage: head region (the nod), sign box and hook */
export const K7 = 2560 / 4320;
export const D1L = { nod: [1720 * K7, 950 * K7, 926 * K7, 723 * K7], sign: [1927 * K7, 544 * K7, 466 * K7, 425 * K7], hook: [2160 * K7, 593 * K7], head: [2182.3 * K7, 1505.4 * K7] };

/** 9:16 crop centre (0..1 of the OUTPUT frame) that keeps stage point x in view under a Cam(cx, s): applies Cam's clamp */
export const c916 = (x: number, cx: number, s: number) => {
  const c = clamp(cx, W / 2 / s, W - W / 2 / s); return clamp((W / 2 + (x - c) * s) / W, 0.16, 0.84);
};
