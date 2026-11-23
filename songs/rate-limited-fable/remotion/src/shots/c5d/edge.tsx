// rl5_d cut 5: the door-edge travel (CUT5_PLAN §2f.2: "The door-edge travel she loves in 10B->11A is the film's connector between
// her room and the lobby (3A->3B, 4F->4G, 10B->11A)"). The camera keeps travelling sideways across the cut; the door's dark edge
// (the slab, its lit brass-trimmed edge) crosses the lens and covers the cut frame, then clears on the other side.
//  edgeOut(def, n, dir): the last n frames of a shot: the camera starts drifting (accelerating) in `dir`, the edge enters.
//  edgeIn(def, n, dir): the first n frames of the next shot: the edge leaves the other side, the drift decelerates to rest.
// dir = +1: the camera travels right (the world and the edge move left on screen). Speeds match at the cut (same curve, mirrored).
import React from 'react';
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { ShotDef, ShotProps } from '../types';

const W = 2560;
const SLAB = 1.25 * W;           // the slab is wider than the frame: at the cut it fills it
const TRAVEL = 260;              // stage px the plate drifts over each half
const easeIn = (t: number) => t * t * t;
const easeOut = (t: number) => 1 - Math.pow(1 - t, 3);

const Slab: React.FC<{ left: number }> = ({ left }) => (
  <div style={{ position: 'absolute', top: -20, bottom: -20, left, width: SLAB,
    background: 'linear-gradient(90deg, #1c130d 0%, #33231a 3%, #4a3424 5%, #2a1d14 9%, #2b1e14 30%, #22170f 50%, #2b1e14 70%, #2a1d14 91%, #4a3424 95%, #33231a 97%, #1c130d 100%)',
    boxShadow: '0 0 60px 30px rgba(8,5,3,0.55)', filter: 'blur(5px)' }}>
    {/* the lit brass edge strips on both long edges */}
    <div style={{ position: 'absolute', top: 0, bottom: 0, left: SLAB * 0.035, width: 10, background: 'linear-gradient(180deg, rgba(212,170,110,0.35), rgba(170,120,70,0.15))', filter: 'blur(3px)' }} />
    <div style={{ position: 'absolute', top: 0, bottom: 0, right: SLAB * 0.035, width: 10, background: 'linear-gradient(180deg, rgba(212,170,110,0.35), rgba(170,120,70,0.15))', filter: 'blur(3px)' }} />
  </div>
);

const wrap = (def: ShotDef, n: number, dir: 1 | -1, side: 'out' | 'in'): ShotDef => ({
  ...def,
  stage: (props: ShotProps) => {
    const f = useCurrentFrame(); const S = def.stage; const dur = props.shot.dur;
    // u: 0..1 through this half of the transition (out: last n frames; in: first n frames)
    const u = side === 'out' ? Math.min(1, Math.max(0, (f - (dur - n)) / n)) : Math.min(1, Math.max(0, f / n));
    const active = side === 'out' ? f >= dur - n : f < n;
    // plate drift: out accelerates 0 -> TRAVEL; in decelerates from -TRAVEL -> 0 (same speed at the cut)
    const shift = side === 'out' ? TRAVEL * easeIn(u) : -TRAVEL * (1 - easeOut(u));
    // the slab's left edge (dir +1, moving left on screen): out: from W -> (W - SLAB)/2 (covers); in: (W - SLAB)/2 -> -SLAB
    const cover = (W - SLAB) / 2;
    let left = side === 'out' ? W + (cover - W) * easeIn(u) : cover + (-SLAB - cover) * easeOut(u);
    if (dir === -1) left = W - left - SLAB;
    return (
      <AbsoluteFill style={{ overflow: 'hidden' }}>
        <AbsoluteFill style={{ transform: `translateX(${(-dir * shift).toFixed(2)}px) scale(${(1 + 2 * Math.abs(shift) / W).toFixed(5)})` }}><S {...props} /></AbsoluteFill>
        {active ? <Slab left={left} /> : null}
      </AbsoluteFill>
    );
  },
});
export const edgeOut = (def: ShotDef, n = 10, dir: 1 | -1 = 1) => wrap(def, n, dir, 'out');
export const edgeIn = (def: ShotDef, n = 10, dir: 1 | -1 = 1) => wrap(def, n, dir, 'in');
