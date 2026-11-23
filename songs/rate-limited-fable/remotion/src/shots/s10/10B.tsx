// 10B "I thought that we were something" (CODEPLAN): she sits against the door, Cooper lying with his head in her lap,
// him back to back on his side. A slow push while they breathe, then on the last beat the camera starts travelling
// left toward the door edge (continues into 11A, no cut). Plate: S12 H2a (rl_cut1 C; was the room_b2b stand-in).
// Breathing: her + Cooper's region (layout boxes, 5760 px) is a feathered copy of the plate scaled ~0.4% about its base.
// rl_fix2_robot (WATCH blocker: his head floated over a heap of parts; 10B = 12E's wide): plate H2a_seat (him in the new seat: back on
// the door, legs out, head square on a readable neck; region render on the same S12 scene). The framing is now a tight two-shot ACROSS
// the door (him left, her + Cooper right, the door edge between them) with a slow push; on the last beat the camera travels left
// toward the door edge and 11A's wipe continues from exactly there (cx 700, s 1.56). 12E is the room wide from the slips instead.
import React from 'react';
import { useCurrentFrame } from 'remotion';
import { ShotDef, ShotProps } from '../types';
import { Cam } from '../first30/kit';
import { MASTER_CLOCK, PL, Pl, WallClock, clamp, gl, lerp, pulse } from './_lib';
import { inCubic, inOutSine } from '../../ease';
import { FX } from '../s11/_fix2';

const K = 2560 / 5760;
const HER = { x0: 1961 * K, y0: 1571 * K, x1: 3431 * K, y1: 3064 * K };   // rl_cut4 (rl_s12_cpu PATCH §2): the LOVE hat breathes with her       // her box (H2a layout), Cooper inside it
/** the plate breathing: a feathered copy scaled about the region's base; a = 0..1 breath */
export const Breath: React.FC<{ src: string; a: number; box?: typeof HER }> = ({ src, a, box = HER }) => {
  const cx = (box.x0 + box.x1) / 2, cy = (box.y0 + box.y1) / 2, rx = (box.x1 - box.x0) / 2, ry = (box.y1 - box.y0) / 2;
  const m = `radial-gradient(ellipse ${rx}px ${ry}px at ${cx}px ${cy}px, #000 55%, transparent 100%)`;
  return (
    <div style={{ position: 'absolute', inset: 0, WebkitMaskImage: m, maskImage: m }}>
      <div style={{ position: 'absolute', inset: 0, transformOrigin: `${cx}px ${box.y1}px`, transform: `scale(${1 + 0.0015 * a}, ${1 + 0.0042 * a})` }}>
        <Pl src={src} />
      </div>
    </div>
  );
};
const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame(); const g = shot.from + f;
  const go = gl(shot, 4, 69);
  const k = inCubic(clamp((f - go) / (shot.dur - go)));
  const push = inOutSine(clamp(f / go));
  const breath = 0.5 - 0.5 * Math.cos((2 * Math.PI * g) / 96);            // ~3.2 s, slow sleep breathing
  // the two-shot: push 1.48 -> 1.53 on them, then the travel left lands on 11A's wipe start (cx 700, s 1.56)
  const cx = lerp(lerp(930, 910, push), 700, k), s = lerp(lerp(1.48, 1.53, push), 1.56, k);
  return (
    <Cam cx={cx} cy={lerp(925, 935, push)} s={s * pulse(g)}>
      <Pl src={FX.H2a} />
      <Breath src={FX.H2a} a={breath} />
      <WallClock cx={MASTER_CLOCK.cx} cy={MASTER_CLOCK.cy} r={MASTER_CLOCK.r} hr={5} min={44} face={false} blur={0.5} />
    </Cam>
  );
};
/** the 10B camera (also used for the 9:16 crop: centred on the door edge between them, x 865 stage) */
export const cam10B = (f: number, go: number, dur: number) => {
  const k = inCubic(clamp((f - go) / (dur - go))); const push = inOutSine(clamp(f / go));
  return { cx: lerp(lerp(930, 910, push), 700, k), s: lerp(lerp(1.48, 1.53, push), 1.56, k) };
};
export const S10_10B: ShotDef = { stage: Stage, cx916: (f, shot) => { const c = cam10B(f, gl(shot, 4, 69), shot.dur); const hw = 1280 / c.s; const x = Math.min(Math.max(c.cx, hw), 2560 - hw); return clamp(((865 - x) * c.s + 1280) / 2560); } };
