// 13C "Okay" (cut 4, lane L2; her #38/#39 notes, §2d the water thread): in the lobby at 6:00, the lights up: the first thing she does is drink
// THE glass of water he slid through the slot at 11D (L4's one glass, sharp and clear), eyes shut, before the coffee; her mug (the speckled
// cream stoneware, the terracotta A to the camera) steams on his desk; he watches. 13D then flips GLASSES OF WATER to 1. Plate: l2/13C.
import React from 'react';
import { useCurrentFrame } from 'remotion';
import { ShotDef, ShotProps } from '../types';
import { Cam } from '../first30/kit';
import { L2Img } from '../l2kit';
import { clamp, inOutSine, lerp } from '../../ease';

const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame(); const k = inOutSine(clamp(f / (shot.dur - 1)));
  return <Cam cx={lerp(1280, 1220, k)} cy={lerp(720, 690, k)} s={lerp(1.0, 1.07, k)}><L2Img id="13C" /></Cam>;
};
export const S13_13C: ShotDef = { stage: Stage, cx916: () => 0.5 };
