// 9E "And you didn't even say goodbye, you just said" (cut 4, lane L2; her #24/#25 notes, S18): first half, she is ON the plate, jiggling,
// arms out for balance, mouth open, watching Cooper fly off (the bail); second half, she has moved to her yoga mat in warrior 2, the vacuum on
// its own little mat beside her in its own warrior (tipped on one edge, status light calm green), the party going on round them, and Cooper
// landed dazed on the sofa, in view (he stays there through 9G). No STUCK card.
import React from 'react';
import { useCurrentFrame } from 'remotion';
import { ShotDef, ShotProps } from '../types';
import { Cam } from '../s07/_lib';
import { L2Img, PlateJiggle, beat, settle } from '../l2kit';
import { LobbyPanda } from '../c4clock';
import { clamp, inOutSine, lerp } from '../../ease';

const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame(); const g = shot.from + f; const half = beat(shot, 4, 69);
  if (f < half) {
    const k = inOutSine(clamp(f / (half - 1)));
    return <Cam cx={lerp(1280, 1180, k)} cy={720} s={lerp(1.0, 1.06, k)}><PlateJiggle id="9E_bail" g={g} amp={7} /></Cam>;
  }
  const k = inOutSine(clamp((f - half) / (shot.dur - 1 - half)));
  return <Cam cx={lerp(1280, 1340, k)} cy={720} s={lerp(1.0, 1.08, k) * (1 + settle(f, half))}><L2Img id="9E_w2" /><LobbyPanda id="9E_w2" h={4} m={43} /></Cam>;
};
export const S9_9E: ShotDef = { stage: Stage, cx916: () => 0.5 };
