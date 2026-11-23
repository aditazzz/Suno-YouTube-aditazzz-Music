// rl5_d cut 5 2F (CUT5_PLAN §3: "The door sign, one slow push (no double punch-in, no clock beside it)"; her OV "camera more
// continuous not so abrupt", N03/N06 no clock by the sign). Same S7 D1 plate (box patched out) and BACK AT 6:00 sign as cut 4e's
// 2F second half; one eased push over the whole shot, the sign settling from a small swing, the lobby soft behind.
import React from 'react';
import { useCurrentFrame } from 'remotion';
import { lerp } from '../../ease';
import { ShotDef, ShotProps } from '../types';
import { Cam, PlateImg, P, D1L } from '../s03/_lib';
import { LobbyPanda, pt } from '../../blocks/PandaClock';
import { SignOnGlass, SIGN_W } from '../first30/S2F';
import { ioc } from './legacy';

const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame(); const k = ioc(f, 0, shot.dur - 1);
  return (
    <Cam cx={D1L.hook[0] - 30} cy={D1L.hook[1] + SIGN_W * 0.5} s={lerp(2.85, 3.05, k)}>
      <div style={{ position: 'absolute', inset: 0, filter: 'blur(2.6px)' }}><PlateImg src={P.D1} /><LobbyPanda time={pt(2, 6, 12)} /></div>
      <SignOnGlass f={f} at={-6} amp={1.6} />
    </Cam>
  );
};
export const C5_2F: ShotDef = { stage: Stage, cx916: () => 0.5 };
