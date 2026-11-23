// 6B "Three fifty-eight": back to back, a push toward her phone on the yoga block, then a hard cut on beat 2 to the phone's
// sleep story (rl_screens phone_6B: 3:58 left on the word, 3:57 a second later).
// PLATE: B2B (approved) + rl_screens phone_6B.
import React from 'react';
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { lerp, outCubic, clamp } from '../../ease';
import { ShotDef, ShotProps } from '../types';
import { Cam, PlateImg, P, Seq, SCREENS, gb, c916 } from '../s03/_lib';
import { ClockOnWall } from './_clock';
import { FX } from '../s11/_fix2';   // rl_cut2: FX.B2B = the new seat (lane B's floating-head fix), same camera, drop-in

// rl_cutfix (Nov 15): 16:9 frames re-composited on the LIFTED room (warm lamp practical; was near-black): cutfix/screens/. Screen content unchanged.
const [A, B] = SCREENS.phone_6B;
const PHONE = { x: 1360, y: 1280 };
const cam = (f: number, cut: number) => { const k = outCubic(clamp(f / cut)); return { s: lerp(1.0, 1.12, k), cx: lerp(1280, PHONE.x, k), cy: lerp(720, PHONE.y - 200, k) }; };
const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame(); const g = shot.from + f; const cut = gb(shot, 1);
  if (f >= cut) return <AbsoluteFill style={{ background: '#000' }}><Seq dir="cutfix/screens/phone_6B_16x9" g={g} first={A} last={B} /></AbsoluteFill>;
  const c = cam(f, cut);
  return <Cam creep={f / shot.dur} s={c.s} cx={c.cx} cy={c.cy}><PlateImg src={FX.B2B} /><ClockOnWall minutes={3 * 60 + 59} secs={44} /></Cam>;
};
const Screen: React.FC<ShotProps> = ({ shot, fmt }) => {
  const f = useCurrentFrame(); const g = shot.from + f; if (fmt !== '9x16' || f < gb(shot, 1)) return null;
  return <AbsoluteFill style={{ background: '#000' }}><Seq dir="seca/screens/phone_6B_9x16" g={g} first={A} last={B} w={1080} h={1920} /></AbsoluteFill>;
};
export const S6_6B: ShotDef = { stage: Stage, screen: Screen, cx916: (f, shot) => { const c = cam(f, gb(shot, 1)); return f >= gb(shot, 1) ? 0.5 : c916(PHONE.x - 150, c.cx, c.s); } };
