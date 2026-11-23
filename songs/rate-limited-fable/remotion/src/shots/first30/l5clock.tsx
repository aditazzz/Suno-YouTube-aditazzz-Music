// rl_l5_street (fix round 4, lane L5): the PANDA street post clock (FIX4_PLAN §2a: one clock design) for the plates rendered before
// round 4 (NS1 1A/1B, NS2 tall 1C, NS2 whole 1H), whose post clock still has the old plain face. The face is L4's kit clock itself
// (assets/props/rl4_kit.py panda_clock kind='face', R .345 m: the one clock of the film) rendered face-on on the post in the night street's
// light with its hands hidden (build/stills/L5_1C/post_dial.png -> public/l5/post_dial.png), laid flat over the old face (the post clock
// faces the level cameras square-on, so a 2D face is exact). The hands are drawn here to the kit's own dimensions (rl4_kit.panda_clock):
// hour .50R x .095R and minute .80R x .072R, black sticks with white lume inlays; chrono .90R x .016R, black with a red tip; steel cap.
// Fallback before the dial render exists: the spec texture public/l5/panda_dial.png (workers/rl_l5_street/tools/panda_dial.py).
import React from 'react';
import { Img, staticFile } from 'remotion';
import l5 from './l5.json';

const DIAL = (l5 as any).post_dial as undefined | { file: string; half_m: number; R_m: number };
const OLD_FACE_M = 0.45, TICK_M = 0.39;   // the old post face radius and the old layouts' tick radius (points_12_3_6_9), metres
const R_M = DIAL?.R_m ?? 0.345;            // the kit dial radius on the post
const HALF_M = DIAL?.half_m ?? 0.45;       // the dial image's half-size (case 1.31 R + 5%)

/** metres -> plate px for an old layout clock (pivot + points_12_3_6_9 at the tick radius) */
export const pxPerM = (c: { pivot: number[]; points_12_3_6_9: number[][] }) => Math.abs(c.points_12_3_6_9[1][0] - c.pivot[0]) / TICK_M;
/** kept for callers that think in the old face radius */
export const faceR = (c: { pivot: number[]; points_12_3_6_9: number[][] }) => pxPerM(c) * OLD_FACE_M;

const Hand: React.FC<{ deg: number; L: number; w: number; tail: number; lume?: [number, number, number]; tip?: number; fill?: string }> = ({ deg, L, w, tail, lume, tip, fill = '#0b0b0d' }) => (
  <g transform={`rotate(${deg.toFixed(3)})`}>
    <rect x={-w / 2} y={-L} width={w} height={L + tail} rx={w * 0.45} fill={fill} />
    {lume ? <rect x={-(w * lume[2]) / 2} y={-L * lume[1]} width={w * lume[2]} height={L * (lume[1] - lume[0])} rx={w * 0.2} fill="#ecebe3" /> : null}
    {tip ? <rect x={-w * 0.51} y={-L} width={w * 1.02} height={L * (1 - tip)} fill="#b3141c" /> : null}
  </g>
);

/** the panda post clock. cx, cy = centre in the parent's px; ppm = parent px per metre at the clock; minutes = minutes past midnight
 *  (fractional ok); blur in px; dim multiplies the dial (night). */
export const PostPanda: React.FC<{ cx: number; cy: number; ppm: number; minutes: number; blur?: number; dim?: number }> = ({ cx, cy, ppm, minutes, blur = 0, dim = 1 }) => {
  const h = (minutes / 60) % 12, m = minutes % 60;
  const R = R_M * ppm, half = HALF_M * ppm;
  return (
    <div data-fit="off" style={{ position: 'absolute', left: cx - half, top: cy - half, width: 2 * half, height: 2 * half, filter: `${blur > 0 ? `blur(${blur}px) ` : ''}brightness(${dim})` }}>
      <Img src={staticFile(DIAL ? `l5/${DIAL.file}` : 'l5/panda_dial.png')} style={{ position: 'absolute', inset: 0, width: '100%', height: '100%' }} />
      <svg width={2 * half} height={2 * half} viewBox={`${-half} ${-half} ${2 * half} ${2 * half}`} style={{ position: 'absolute', inset: 0, overflow: 'visible' }}>
        <Hand deg={h * 30} L={0.50 * R} w={0.095 * R} tail={0.10 * R} lume={[0.30, 0.86, 0.52]} />
        <Hand deg={m * 6} L={0.80 * R} w={0.072 * R} tail={0.12 * R} lume={[0.24, 0.93, 0.48]} />
        <Hand deg={0} L={0.90 * R} w={0.016 * R} tail={0.24 * R} tip={0.84} />
        <circle r={0.045 * R} fill="#c9cacd" /><circle r={0.028 * R} fill="#b3141c" />
      </svg>
    </div>
  );
};
