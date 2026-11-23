// Plate: one approved still filling the stage, with an eased camera move (push / pan / drift / rise), optional
// parallax layers cut from the same still by mask PNGs, and an optional grade. Pure function of the frame.
//
//   <Plate src="plates/door.jpg" dur={shot.dur} move="push" />
//   <Plate src="plates/door.jpg" dur={70} move={{ s: [1.04, 1.12], x: [0, -0.02], y: [0, 0.01] }} ease={outCubic}
//          layers={[{ mask: 'plates/masks/door_fg.png', depth: 0.6 }]} grade="brightness(0.9) saturate(1.1)" />
//
// Moves are in stage fractions: x/y = offset of the camera target (0.02 = 2% of the stage), s = scale. Parallax:
// a layer with depth d moves (1 + d) times the camera's x/y and scales by 1 + d * (s - 1), so near things travel more.
// Masks are white-on-black (or alpha) PNGs the size of the still: white = this layer. Make them with any matte tool
// or by hand; keep the edges soft (8-20 px feather) so the layer seam never shows.
// children ride the camera (depth 0, drawn above the parallax layers): inserts, props, in-world type. hud = drawn on top,
// fixed to the frame (does NOT move with the camera). Fixed Nov 15 (rl_first30_v2): children used to sit outside the move.
import React from 'react';
import { AbsoluteFill, Img, staticFile, useCurrentFrame } from 'remotion';
import { STAGE_H, STAGE_W } from '../theme';
import { clamp, inOutSine, lerp } from '../ease';

export type Move = { s?: [number, number]; x?: [number, number]; y?: [number, number]; r?: [number, number] };
export const MOVES: Record<string, Move> = {
  hold: { s: [1.02, 1.02] },
  push: { s: [1.0, 1.07] },
  pushHard: { s: [1.0, 1.16] },
  pull: { s: [1.08, 1.0] },
  driftR: { s: [1.06, 1.08], x: [0.018, -0.018] },
  driftL: { s: [1.06, 1.08], x: [-0.018, 0.018] },
  rise: { s: [1.06, 1.08], y: [0.018, -0.014] },
  fall: { s: [1.06, 1.08], y: [-0.014, 0.018] },
};
export type Layer = { mask: string; depth: number; src?: string };

const asSrc = (s: string) => (s.startsWith('http') || s.startsWith('/') || s.startsWith('data:') ? s : staticFile(s));

export const cameraAt = (move: Move | string, k: number) => {
  const m = typeof move === 'string' ? MOVES[move] ?? MOVES.hold : move;
  const s = lerp(m.s?.[0] ?? 1, m.s?.[1] ?? 1, k), x = lerp(m.x?.[0] ?? 0, m.x?.[1] ?? 0, k), y = lerp(m.y?.[0] ?? 0, m.y?.[1] ?? 0, k);
  const r = lerp(m.r?.[0] ?? 0, m.r?.[1] ?? 0, k);
  // never show an edge: the scale has to cover the offset on both axes
  const sMin = 1 + 2 * Math.max(Math.abs(x), Math.abs(y)) + Math.abs(r) * 0.02;
  return { s: Math.max(s, sMin), x, y, r };
};

export const Plate: React.FC<{
  src: string; dur: number; move?: Move | string; ease?: (k: number) => number; delay?: number;
  layers?: Layer[]; grade?: string; children?: React.ReactNode; hud?: React.ReactNode; fit?: 'cover' | 'contain';
}> = ({ src, dur, move = 'push', ease = inOutSine, delay = 0, layers = [], grade, children, hud, fit = 'cover' }) => {
  const f = useCurrentFrame();
  const k = ease(clamp((f - delay) / Math.max(1, dur - 1 - delay)));
  const cam = cameraAt(move, k);
  const tf = (d: number) => {
    const s = 1 + (cam.s - 1) * (1 + d); const x = cam.x * (1 + d) * STAGE_W, y = cam.y * (1 + d) * STAGE_H;
    return `translate(${x.toFixed(2)}px, ${y.toFixed(2)}px) scale(${s.toFixed(5)}) rotate(${cam.r.toFixed(3)}deg)`;
  };
  const img: React.CSSProperties = { position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: fit };
  return (
    <AbsoluteFill style={{ overflow: 'hidden', filter: grade, background: '#000' }}>
      <AbsoluteFill style={{ transform: tf(0), transformOrigin: '50% 50%' }}>
        <Img src={asSrc(src)} style={img} />
      </AbsoluteFill>
      {layers.map((l, i) => {
        const m = `url(${asSrc(l.mask)})`;
        return (
          <AbsoluteFill key={i} style={{ transform: tf(l.depth), transformOrigin: '50% 50%' }}>
            <Img src={asSrc(l.src ?? src)} style={{ ...img, WebkitMaskImage: m, maskImage: m, WebkitMaskSize: '100% 100%', maskSize: '100% 100%', maskMode: 'luminance' } as any} />
          </AbsoluteFill>
        );
      })}
      {children ? <AbsoluteFill style={{ transform: tf(0), transformOrigin: '50% 50%' }}>{children}</AbsoluteFill> : null}
      {hud}
    </AbsoluteFill>
  );
};
