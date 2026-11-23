// 5G "Rate limited, rate limited" (3:58), the chorus pair. Cut 4 (rl_l3_ui; R6: not the same 429 close again; §2a one clock; R7 one
// sign): beats 1-2 = the wide from her side (T6 camera): her arms folded at the tape, him at the door with the 429 up, the lobby's
// panda wall clock at 3:58 above QUIET HOURS; a punch in. Beats 3-4 = the BACK AT 6:00 shop sign on the glass (as in 2F).
// PLATES: S11 h1_t4p (5760, T6 camera); S7 D1 (final). Clock and sign are code.
import React from 'react';
import { useCurrentFrame } from 'remotion';
import { clamp, inOutSine, lerp } from '../../ease';
import { ShotDef, ShotProps } from '../types';
import { Cam, PlateImg, P, gb, hit, pulse, D1L } from '../s03/_lib';
import { A1, Lay } from '../s03/_cut1a';
import { LobbyPanda, T6_CLOCK, WallPanda, pt } from '../../blocks/PandaClock';
import { SIGN_W, SignOnGlass } from '../first30/S2F';

const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame(); const g = shot.from + f;
  const b2 = gb(shot, 2);
  if (f < b2) {
    const k = inOutSine(clamp(f / (b2 - 1)));
    const s = lerp(1.42, 1.5, k) * (1 + hit(f, 0, 0.02, 8) + pulse(g));
    return (
      <Cam cx={lerp(1120, 1100, k)} cy={600} s={s}>
        <Lay src={A1.H1t4p} x={0} y={0} w={2560} h={1440} />
        <WallPanda at={T6_CLOCK} time={pt(3, 58, 20 + f / 30)} chrono={(20 + f / 30) % 60} light={0.92} uid="t6" />
      </Cam>
    );
  }
  const k = inOutSine(clamp((f - b2) / (shot.dur - b2 - 1)));
  const s = lerp(2.85, 3.0, k) * (1 + hit(f, b2, 0.02, 8) + pulse(g));
  return (
    <Cam cx={D1L.hook[0] - 30} cy={D1L.hook[1] + SIGN_W * 0.5} s={s * 1.07}>
      <div style={{ position: 'absolute', inset: 0, filter: 'blur(2.6px)' }}><PlateImg src={P.D1} /><LobbyPanda time={pt(3, 58, 30)} /></div>
      <SignOnGlass f={f} at={b2} />
    </Cam>
  );
};
export const S5_5G: ShotDef = { stage: Stage, cx916: () => 0.5 };
