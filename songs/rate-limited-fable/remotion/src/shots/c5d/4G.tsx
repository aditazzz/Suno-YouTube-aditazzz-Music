// rl5_d cut 5 4G placeholder until rl5_b's K-plate 4G variant (CUT5_PLAN §3 4G: "The same move pushes through the door glass onto
// him, fully framed ... Continuous push from 4F, lands by 1955, holds"; her N20 no clock, N21 chain latched). S7 D1 plate (box
// patched, no clock), an eased push that arrives already moving (4F's push continues) and lands on frame 1955, then holds.
import React from 'react';
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { lerp } from '../../ease';
import { ShotDef, ShotProps } from '../types';
import { Cam, Grain, PlateImg } from '../s07/_lib';
import { LobbyPanda, pt } from '../../blocks/PandaClock';

const LAND = 35; // 1955 - 1920
const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame(); const g = shot.from + f;
  const t = Math.min(1, f / LAND); const k = 1 - Math.pow(1 - t, 3); // arrives moving (from 4F), decelerates to rest
  return (
    <AbsoluteFill>
      <Cam cx={lerp(1330, 1400, k)} cy={lerp(700, 650, k)} s={lerp(1.15, 1.7, k)}><PlateImg src="secb/D1.jpg" /><LobbyPanda time={pt(2, 24)} /></Cam>
      <Grain g={g} />
    </AbsoluteFill>
  );
};
export const C5_4G: ShotDef = { stage: Stage, cx916: () => 0.5 };
