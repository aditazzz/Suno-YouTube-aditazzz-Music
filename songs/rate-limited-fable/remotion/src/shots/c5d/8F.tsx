// rl5_d cut 5 8F placeholder until rl5_b's K plate lands (CUT5_PLAN §3: "K plate: 429 visor, then eyes. Single push"): the S7 D1
// plate, close on him behind the glass from her side, ONE eased push over the whole shot, no clock (box patched), no punch.
import React from 'react';
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { lerp } from '../../ease';
import { ShotDef, ShotProps } from '../types';
import { Cam, Grain, PlateImg } from '../s07/_lib';
import { LobbyPanda, pt } from '../../blocks/PandaClock';
import { ioc } from './legacy';

const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame(); const g = shot.from + f; const k = ioc(f, 0, shot.dur - 1);
  return (
    <AbsoluteFill>
      <Cam cx={lerp(1380, 1420, k)} cy={660} s={lerp(1.7, 1.9, k)}><PlateImg src="secb/D1.jpg" /><LobbyPanda time={pt(4, 39)} /></Cam>
      <Grain g={g} />
    </AbsoluteFill>
  );
};
export const C5_8F: ShotDef = { stage: Stage, cx916: () => 0.5 };
