// 13B exterior beat (fix round 4, rl_l5_street; FIX4_PLAN §2g.3 / row 37): "the grey building comes back to colour floor by floor top to
// bottom (the exact reverse of 1H's 'went grey'), ending on the open door with the sunrise on it." Its own component: L2's 13B.tsx cuts to
// it for one beat (<Ext13B f={...} dur={...} g={...} /> with f = frames since the cut), or use S13_13B_ext as a whole shot.
// The pair with 1H: the SAME camera (CAM_FLAT, the NS2 whole framing, flat-on, dead centre), the same five floor bands in the same order
// (top first), each floor flickering on its step with 1H's flicker run backwards (flick vs flickOut), the sign stuttering back to green
// first (1H drained it first), the tail lifting out of 1H's 3-degree droop and starting to swing again.
// The colour state is L5 13B (build/stills/L5_13B, blrl4_street): 6:00 sunrise, the sun on every floor and the street, BUILD PASSING
// on, the panda post clock at 6:00, the entry doors open (warm lobby), the car at the kerb. The grey state is that same render drained in
// code (an exact pixel pair: nothing moves between grey and colour except the colour). Then the push to the door: the whole plate
// (4320) hands over to two exact crops of the same camera (mid 14.2 m and door 7.1 m wide, 2560 each), so the landing is full resolution.
import { c5p } from '../c5d/plates';   // rl5_d2: cut 5 plate swaps (rl5_b facade patches)
import React from 'react';
import { AbsoluteFill, Img, staticFile, useCurrentFrame } from 'remotion';
import { clamp, inOutCubic, inOutSine, lerp } from '../../ease';
import { ShotDef, ShotProps } from '../types';
import { Cam, ez, flick } from '../first30/kit';
import l5 from '../first30/l5.json';

const B = (l5 as any).B13 as undefined | {
  size: number[]; floors: { floors: { floor_from_bottom: number; y_top: number; y_bottom: number }[]; facade_x: number[]; lobby_band: number[] };
  sign: { structure: number[] }; door: number[]; tail: { region: number[]; pivot: number[] }; crops: Record<string, number[]>; files: Record<string, string>;
};
export const HAVE_13B_EXT = !!(B && B.files?.whole);
const KW = B ? 2560 / B.size[0] : 1;
/** the drained state (1H's end look: cold, desaturated, a stop down) */
const GREY = 'grayscale(0.94) brightness(0.74) contrast(0.92)';
/** the schedule (frames since the cut): sign, floors 5..1 (top first), then the street and the sky; then the push to the door */
const T_SIGN = 0, T_FLOOR = [4, 9, 14, 19, 24], T_REST = 29, T_PUSH = 30;

export const Ext13B: React.FC<{ f: number; dur: number; g?: number }> = ({ f, dur }) => {
  if (!B || !HAVE_13B_EXT) return null;
  const full: React.CSSProperties = { position: 'absolute', left: 0, top: 0, width: 2560, height: 1440 };
  const fx = B.floors.facade_x;
  const fl = B.floors.floors.slice().sort((a, b) => b.floor_from_bottom - a.floor_from_bottom);       // top floor first
  const band = (x0: number, y0: number, x1: number, y1: number) =>
    `inset(${(y0 * KW).toFixed(1)}px ${(2560 - x1 * KW).toFixed(1)}px ${(1440 - y1 * KW).toFixed(1)}px ${(x0 * KW).toFixed(1)}px)`;
  const ss = B.sign.structure; const sr = [ss[0] - 40, Math.max(0, ss[1] - 40), ss[2] + 40, ss[3] + 40];
  const sign = f < T_SIGN ? 0 : f < T_SIGN + 4 ? [0.3, 0.05, 0.8, 0.2][f - T_SIGN] : 1;      // the stutter back on (1H's drain, reversed)
  const rest = ez(f, T_REST, T_REST + 6, inOutSine);
  // the push: whole -> door crop, eased; the crops sit on top at their exact rects (identical pixels, sharper)
  const door = B.crops.door, mid = B.crops.mid;
  const dc = [(door[0] + door[2]) / 2 * KW, (door[1] + door[3]) / 2 * KW];
  const sEnd = 2560 / ((door[2] - door[0]) * KW);
  const k = inOutCubic(clamp((f - T_PUSH) / Math.max(1, dur - 1 - T_PUSH)));
  const s = Math.exp(lerp(0, Math.log(sEnd), k));                       // a constant-rate zoom (log space)
  const cx = lerp(1280, dc[0], k), cy = lerp(720, dc[1], k);
  // the tail: out of 1H's droop (3 deg), up, then swinging again
  const tr = B.tail.region, piv = B.tail.pivot;
  const css = lerp(-3, 0, ez(f, 6, 18, inOutSine)) + 5 * Math.sin((2 * Math.PI * (f - 18)) / 36) * ez(f, 18, 30, inOutSine);
  const box = (r: number[]): React.CSSProperties => ({ position: 'absolute', left: r[0] * KW, top: r[1] * KW, width: (r[2] - r[0]) * KW, height: (r[3] - r[1]) * KW });
  return (
    <Cam cx={cx} cy={cy} s={s}>
      <Img src={staticFile(c5p(`l5/${B.files.whole}`))} style={{ ...full, filter: GREY }} />
      {sign > 0.005 ? <Img src={staticFile(c5p(`l5/${B.files.whole}`))} style={{ ...full, opacity: sign, clipPath: band(sr[0], sr[1], sr[2], sr[3]) }} /> : null}
      {fl.map((b, i) => {
        const a = flick(f, T_FLOOR[i] ?? 99); if (a < 0.005) return null;
        return <Img key={i} src={staticFile(c5p(`l5/${B.files.whole}`))} style={{ ...full, opacity: a, clipPath: band(fx[0], b.y_top, fx[1], b.y_bottom) }} />;
      })}
      {rest > 0.005 ? <Img src={staticFile(c5p(`l5/${B.files.whole}`))} style={{ ...full, opacity: rest }} /> : null}
      {B.files.tail ? (
        <Img src={staticFile(`l5/${B.files.tail}`)} style={{ ...box(tr), transformOrigin: `${((piv[0] - tr[0]) * KW).toFixed(2)}px ${((piv[1] - tr[1]) * KW).toFixed(2)}px`,
          transform: `rotate(${css.toFixed(3)}deg)`, filter: f < T_REST ? `grayscale(${(1 - rest).toFixed(3)})` : undefined }} />
      ) : null}
      {B.files.mid && s > 1.25 ? <Img src={staticFile(c5p(`l5/${B.files.mid}`))} style={{ ...box(mid), opacity: clamp((s - 1.25) / 0.3) * rest }} /> : null}
      {B.files.door && s > 2.4 ? <Img src={staticFile(c5p(`l5/${B.files.door}`))} style={{ ...box(door), opacity: clamp((s - 2.4) / 0.6) * rest }} /> : null}
    </Cam>
  );
};

const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame();
  return <AbsoluteFill><Ext13B f={f} dur={shot.dur} g={shot.from + f} /></AbsoluteFill>;
};
export const S13_13B_ext: ShotDef = { stage: Stage, cx916: () => 0.5 };
