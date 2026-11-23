// 2F "Rate limited, rate limited" (2:06): the chorus pair of punch-ins. Cut 4 (rl_l3_ui; R6: the 429 close was the same picture
// nine times; R7/S10: one BACK AT 6:00 design; §2a: one clock): beat 1-2 = through the glass from her side, hard in on the lobby's
// panda wall clock at 2:06 (where the digital box was), his spiky head soft in the corner; beats 3-4 = the BACK AT 6:00 shop sign
// on the glass (the panda dial set to 6:00), a damped swing from the punch; focus racks to the sign (the lobby behind goes soft).
// PLATE: S7 D1 (final). Clock and sign are code (blocks/PandaClock).
import React from 'react';
import { useCurrentFrame } from 'remotion';
import { clamp, inOutSine, lerp } from '../../ease';
import { ShotDef, ShotProps } from '../types';
import { Cam, PlateImg, P, gb, hit, D1L, pendulum, pulse } from '../s03/_lib';
import { BackAt6Sign, LobbyPanda, S7_CLOCK, pt } from '../../blocks/PandaClock';

export const SIGN_W = 300;                                    // the sign board width on the stage (hung from D1L.hook)
const camAt = (f: number, shot: ShotProps['shot']) => {
  const g = shot.from + f; const b2 = gb(shot, 2);
  if (f < b2) { const k = inOutSine(clamp(f / (b2 - 1))); return { half: 0, cx: lerp(S7_CLOCK.cx - 120, S7_CLOCK.cx - 90, k), cy: S7_CLOCK.cy + 30, s: lerp(3.1, 3.3, k) * (1 + hit(f, 0, 0.025, 9) + pulse(g)) }; }
  const k = inOutSine(clamp((f - b2) / (shot.dur - b2 - 1)));
  return { half: 1, cx: D1L.hook[0] - 30, cy: D1L.hook[1] + SIGN_W * 0.5, s: lerp(3.05, 3.2, k) * (1 + hit(f, b2, 0.02, 9) + pulse(g)) };
};
export const SignOnGlass: React.FC<{ f: number; at: number; amp?: number }> = ({ f, at, amp = 3 }) => (
  <BackAt6Sign x={D1L.hook[0]} y={D1L.hook[1]} w={SIGN_W} swing={pendulum(f, at, amp, 26, 2.4)} light={0.97} blur={0.5} uid="s2f" />
);
const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame(); const b2 = gb(shot, 2);
  const { half, cx, cy, s } = camAt(f, shot);
  if (half === 0) return <Cam cx={cx} cy={cy} s={s}><PlateImg src={P.D1} /><LobbyPanda time={pt(2, 6, 10 + f / 30)} chrono={(10 + f / 30) % 60} /></Cam>;
  return (
    <Cam cx={cx} cy={cy} s={s}>
      <div style={{ position: 'absolute', inset: 0, filter: 'blur(2.6px)' }}><PlateImg src={P.D1} /><LobbyPanda time={pt(2, 6, 12)} /></div>
      <SignOnGlass f={f} at={b2} />
    </Cam>
  );
};
const c916 = (x: number, cx: number, s: number) => { const c = clamp(cx, 1280 / s, 2560 - 1280 / s); return clamp((1280 + (x - c) * s) / 2560, 0.16, 0.84); };
export const S2_2F: ShotDef = { stage: Stage, cx916: (f, shot) => { const c = camAt(f, shot); return c916(c.half === 0 ? S7_CLOCK.cx : D1L.hook[0], c.cx, c.s); } };
