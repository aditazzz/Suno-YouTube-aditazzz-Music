// rl5_d5 cut 5 6A / 6B / 6D on rl5_a1's re-dressed B2B frame (c5/6A/room_rain.jpg, 2880: bodysuit, forearm stand against his door,
// three parcels, kit5 lobby: ONE 3D wall clock with real hands at ~4:00 above QUIET HOURS, ShipIt! / We ship worldwide plaque, no paddle).
// Same camera as cut 4e's FX.B2B, so cut 4e's framings carry over; cut 4e's code WallPanda/ClockOnWall is OUT (it sat exactly on the
// new 3D clock: two clocks). Plan rows: 6A "two-room wide, dead still", 6B "push in from 6A's framing" (KEEP), 6D "matches 6A, slow push".
import React from 'react';
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { lerp, outCubic, clamp } from '../../ease';
import { ShotDef, ShotProps } from '../types';
import { Cam, PlateImg, Seq, SCREENS, gb, c916, pulse } from '../s03/_lib';

export const ROOM6 = 'c5/6A/room_rain.jpg';
// 6A: the dead hour. Dead still two-room wide; a barely-there creep (1.2% over the shot) so it isn't a freeze frame.
const S6A: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame(); const k = f / Math.max(1, shot.dur - 1);
  return <Cam cx={1280} cy={720} s={1 + 0.012 * k}><PlateImg src={ROOM6} /></Cam>;
};
export const C5_6A: ShotDef = { stage: S6A, cx916: () => 0.5 };

// 6B: cut 4e's push toward her phone on the yoga block, then the hard cut on beat 2 to the sleep story (unchanged screens).
const [A, B] = SCREENS.phone_6B;
const PHONE = { x: 1360, y: 1280 };
const cam6B = (f: number, cut: number) => { const k = outCubic(clamp(f / cut)); return { s: lerp(1.012, 1.12, k), cx: lerp(1280, PHONE.x, k), cy: lerp(720, PHONE.y - 200, k) }; };
const S6B: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame(); const g = shot.from + f; const cut = gb(shot, 1);
  if (f >= cut) return <AbsoluteFill style={{ background: '#000' }}><Seq dir="cutfix/screens/phone_6B_16x9" g={g} first={A} last={B} /></AbsoluteFill>;
  const c = cam6B(f, cut);
  return <Cam s={c.s} cx={c.cx} cy={c.cy}><PlateImg src={ROOM6} /></Cam>;
};
export const C5_6B: ShotDef = { stage: S6B, cx916: (f, shot) => { const c = cam6B(f, gb(shot, 1)); return f >= gb(shot, 1) ? 0.5 : c916(PHONE.x - 150, c.cx, c.s); } };

// 6D: cut 4e's framing (pushed in on her stand against the glass and the neon), slow push; the beat pulse kept.
const S6D: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame(); const g = shot.from + f; const k = f / shot.dur;
  return <Cam cx={lerp(1440, 1470, k)} cy={lerp(575, 560, k)} s={lerp(1.38, 1.46, k) * (1 + pulse(g))}><PlateImg src={ROOM6} /></Cam>;
};
export const C5_6D: ShotDef = { stage: S6D, cx916: () => 0.56 };
