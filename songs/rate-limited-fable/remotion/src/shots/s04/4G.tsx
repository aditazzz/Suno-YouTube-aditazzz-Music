// 4G "Four-two-nine instead": on her, four tiles out, arms folded; a whip pan (shutter-sample blur) across to the door, and
// the 429 paddle SLAMS into frame big on the music's hit (1:05.0): the whip overshoots into a punch-in (2.1x -> 2.85x),
// settles back to 2.6x with a small roll correction, and a camera hit. This is the verse's 429 moment.
// PLATE: rl_cut1 a1 = S11 H1_t4_paddle (5760x3240, T6's camera: her at the 4s tape, him at the door holding the paddle up,
// 1.3x, turned to the camera; his desk empty). 2.25 plate px per stage px: the 2.6x hold is a 1.16x upscale (clean render, reads sharp).
import React from 'react';
import { useCurrentFrame } from 'remotion';
import { clamp, lerp, inOutCubic } from '../../ease';
import { cueFrame } from '../../timing';
import { ShotDef, ShotProps } from '../types';
import { Cam, hit, MBlur, pulse, c916 } from '../s03/_lib';
import { A1, Lay } from '../s03/_cut1a';
import { T6_CLOCK, WallPanda, pt } from '../../blocks/PandaClock';

const K = 2560 / 5760;
const HER = { x: 1745, y: 760 };                                  // her_4 (box 3600-4243 x 739-2923): head and folded arms
const PAD = { x: 1792.3 * K, y: 1098.2 * K };                     // layout.paddle.face_px (797, 488)
// rl_l3_ui (cut 4, #7 "The clock on the wall doesn't have hands ... Rolex Panda" + the watch row): the hold lands a little wider and left,
// so the panda wall clock (2:24) and the whole QUIET HOURS notice share the frame with the paddle (it no longer half-covers the notice).
const LANDC = { x: 700, y: 432 };
/** zoom over the move: 2.1 on her -> overshoots to 2.85 at the landing -> settles at 2.6 */
const zoom = (f: number, a: number, land: number) => {
  if (f < a) return 2.1;
  if (f < land) return lerp(2.1, 2.6, inOutCubic((f - a) / (land - a)));
  const d = f - land; return 2.35 + 0.25 * Math.exp(-d / 3.2) * Math.cos(d / 2.6);
};
const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame(); const g = shot.from + f;
  const land = cueFrame(shot, 'hit') ?? 27; const a = land - 11;
  const k = (t: number) => inOutCubic(clamp((t - a) / (land - a)));
  const moving = f >= a - 1 && f <= land;
  const roll = f < land ? -2.2 * Math.sin(Math.PI * k(f)) : 1.1 * Math.exp(-(f - land) / 4) * Math.cos((f - land) / 2.2);
  return (
    <MBlur n={moving ? 10 : 1} shutter={1.0} render={(dt) => {
      const t = k(f + dt);
      const s = zoom(f + dt, a, land) * (1 + hit(f, land, 0.03, 9) + (f > land + 12 ? pulse(g) : 0));
      return (
        <Cam cx={lerp(HER.x, LANDC.x, t)} cy={lerp(HER.y, LANDC.y, t)} s={s} r={roll}>
          <Lay src={A1.H1t4p} x={0} y={0} w={2560} h={1440} />
          <WallPanda at={T6_CLOCK} time={pt(2, 24, 10 + (f + dt) / 30)} chrono={(10 + (f + dt) / 30) % 60} light={0.92} uid="g4" />
        </Cam>
      );
    }} />
  );
};
export const S4_4G: ShotDef = { stage: Stage, cx916: (f, shot) => {
  const land = cueFrame(shot, 'hit') ?? 27; const k = inOutCubic(clamp((f - land + 11) / 11));
  return c916(lerp(HER.x, PAD.x, k), lerp(HER.x, LANDC.x, k), zoom(f, land - 11, land)); } };
