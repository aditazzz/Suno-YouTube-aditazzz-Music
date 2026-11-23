// Cut 7 transitions (PLAN7 §2).
//  has(path): is this file under public/c7 (src/data/c7files.json, written by tools/c7_packs.py)? Lane assets swap in when they land.
//  WallDolly: the camera trucks sideways through the cutaway wall between her room and the lobby. Wrap the outgoing block's
//    last n frames with side='out' and the incoming block's first n with side='in' (same n, same dir): the picture drifts
//    (accelerating out, decelerating in: equal speed at the cut) while the wall's cross-section crosses the lens and covers the
//    cut. The wall is P1's render (c7/wall/xsec.png: plaster, studs, brass door edge) once it lands; until then cut 6's door slab.
//  Match: B's first frames are re-framed so B's feature (circle centre + radius, stage px) sits exactly where A's was on screen,
//    then ease (n frames, out-cubic in log scale) to B's own framing. A cut that reads as one shape continuing.
//  Whip: a directional smear (n shutter samples along (vx, vy) screen px), 3-4 frames around a whip.
import React from 'react';
import { AbsoluteFill, Img, staticFile } from 'remotion';
import files from '../../../data/c7files.json';

const W = 2560, H = 1440;
const FILES = new Set(files as unknown as string[]);
export const has = (p: string) => FILES.has(p);
const easeIn = (t: number) => t * t * t;
const easeOut = (t: number) => 1 - Math.pow(1 - t, 3);

// P1's section: olive (her room's paint) | drywall | studs + insulation | drywall | brown trim. On screen the lobby is always LEFT of the
// wall and her room RIGHT (the cutaway set), whichever way the camera travels, so the olive face goes on the right: xsec_flip.
export const WALL = has('c7/wall/xsec_flip.png') ? 'c7/wall/xsec_flip.png' : 'c7/wall/xsec.png';
const SLAB = 1.25 * W;
const SlabCss: React.FC<{ left: number }> = ({ left }) => (
  <div style={{ position: 'absolute', top: -20, bottom: -20, left, width: SLAB,
    background: 'linear-gradient(90deg, #1c130d 0%, #33231a 3%, #4a3424 5%, #2a1d14 9%, #2b1e14 30%, #22170f 50%, #2b1e14 70%, #2a1d14 91%, #4a3424 95%, #33231a 97%, #1c130d 100%)',
    boxShadow: '0 0 60px 30px rgba(8,5,3,0.55)', filter: 'blur(5px)' }} />
);
const Wall: React.FC<{ left: number; blur: number }> = ({ left, blur }) => (has(WALL)
  ? <Img src={staticFile(WALL)} style={{ position: 'absolute', top: -10, height: H + 20, left, width: SLAB, objectFit: 'cover', filter: `blur(${blur.toFixed(1)}px)` }} />
  : <SlabCss left={left} />);

/** WallDolly state for a block-local frame: the drift (stage px, signed) and the wall's left edge (null = not in frame) */
export const wallDolly = (f: number, dur: number, n: number, dir: 1 | -1, side: 'out' | 'in', travel = 320) => {
  const u = side === 'out' ? Math.min(1, Math.max(0, (f - (dur - n)) / n)) : Math.min(1, Math.max(0, f / n));
  const active = side === 'out' ? f >= dur - n : f < n;
  const shift = side === 'out' ? travel * easeIn(u) : -travel * (1 - easeOut(u));
  const cover = (W - SLAB) / 2;
  let left = side === 'out' ? W + (cover - W) * easeIn(u) : cover + (-SLAB - cover) * easeOut(u);
  if (dir === -1) left = W - left - SLAB;
  // speed of the wall (px/f) -> motion blur on it
  const v = side === 'out' ? 3 * u * u * (cover - W) / n : 3 * (1 - u) * (1 - u) * (-SLAB - cover) / n;
  return { dx: -dir * shift, left: active ? left : null, blur: Math.min(24, Math.abs(v) * 0.12) };
};
/** wraps a block's stage in the dolly drift and draws the wall crossing (stage space, under the screen layer) */
export const WallDolly: React.FC<{ f: number; dur: number; n?: number; dir?: 1 | -1; side: 'out' | 'in'; travel?: number; children: React.ReactNode }> = ({ f, dur, n = 12, dir = 1, side, travel, children }) => {
  const w = wallDolly(f, dur, n, dir, side, travel);
  return (
    <AbsoluteFill style={{ overflow: 'hidden' }}>
      <AbsoluteFill style={{ transform: `translateX(${w.dx.toFixed(2)}px)` }}>{children}</AbsoluteFill>
      {w.left !== null ? <Wall left={w.left} blur={w.blur} /> : null}
    </AbsoluteFill>
  );
};

export type Feat = { x: number; y: number; r: number };   // on SCREEN (stage px of the output frame) at the cut
/** Match: re-frame B (whose feature is at `b` on screen in its own framing at frame 0) so it starts on A's feature `a` */
export const Match: React.FC<{ f: number; n: number; a: Feat; b: Feat; children: React.ReactNode }> = ({ f, n, a, b, children }) => {
  const u = easeOut(Math.min(1, Math.max(0, f / n)));
  const kk = Math.exp(Math.log(a.r / b.r) * (1 - u));                       // scale: A's size -> B's own, in log space
  const px = (1 - u) * a.x + u * b.x, py = (1 - u) * a.y + u * b.y;          // where B's feature sits on screen now
  const X = px - kk * b.x, Y = py - kk * b.y;                               // p -> (px, py) + kk (p - b)
  return <AbsoluteFill style={{ transformOrigin: '0 0', transform: `translate(${X.toFixed(2)}px, ${Y.toFixed(2)}px) scale(${kk.toFixed(5)})` }}>{children}</AbsoluteFill>;
};
/** directional smear: n copies along (vx, vy) screen px (the frame's motion), as an exact running mean */
export const Whip: React.FC<{ vx: number; vy?: number; n?: number; on?: boolean; render: () => React.ReactNode }> = ({ vx, vy = 0, n = 7, on = true, render }) => {
  if (!on || n <= 1 || Math.hypot(vx, vy) < 4) return <>{render()}</>;
  return (
    <>
      {Array.from({ length: n }, (_, i) => {
        const t = i / (n - 1) - 0.5;
        return <AbsoluteFill key={i} style={{ opacity: 1 / (i + 1), transform: `translate(${(vx * t).toFixed(2)}px, ${(vy * t).toFixed(2)}px)` }}>{render()}</AbsoluteFill>;
      })}
    </>
  );
};
