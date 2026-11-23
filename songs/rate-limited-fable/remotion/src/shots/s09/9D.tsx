// 9D "There was so much else!": the party bursts out on the beat (the approved PARTY plate on the cut with a hit, the TV
// party bouncing (tv_9D), streamers fired on beats 1 and 3, confetti bursts), then H4 COOPER'S LEAP (4558-4593, real
// 3D motion: build/heroes/h4_bail; the draft at 960 px until the final's 36 frames land, then prep_secb.py swaps it).
import React from 'react';
import { AbsoluteFill, Img, staticFile, useCurrentFrame } from 'remotion';
import { clamp, inOutSine, lerp } from '../../ease';
import { ShotDef, ShotProps } from '../types';
import { ScreenInsert } from '../../blocks/ScreenInsert';
import { ASSETS, Cam, Grain, PlateImg, gridF, hit, seqSrc } from '../s07/_lib';
import { PlateJiggle, beat } from '../l2kit';
import { PhoneScreen9C } from './9C';

export const H4_FIRST = 4558, H4_LAST = 4593;
const H4 = ASSETS.h4 ? 'h4' : 'h4_draft';

// rl_cut4 (L2 PATCH B, director's call): one room, one her. 9D on lane L2's plates (no new render): her squat on the jiggling plate (l2/9C),
// and on beat 2 Cooper is flung off it (l2/9E_bail, its real alpha layers), which 9E opens on. The old PARTY plate + H4 clip (the old routine
// room and the old her in sunglasses and the hotel robe) are out; the party itself arrives in 9E.
const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame(); const g = shot.from + f; const b2 = beat(shot, 2, 35);
  const s = 1.04 * (1 + hit(f, 0, 0.012, 8) + hit(f, b2, 0.014, 8));
  return <Cam cx={1280} cy={720} s={s}><PlateJiggle id={f < b2 ? '9C' : '9E_bail'} g={g} amp={f < b2 ? 6 : 8} />{f < b2 ? <PhoneScreen9C g={g} amp={6} /> : null}<Grain g={g} /></Cam>;
};
// 9:16: on her and the TV, then (rl_cd_cooper) centred on x ~0.33 for the leap: he exits bottom-left
export const S9_9D: ShotDef = { stage: Stage, cx916: () => 0.5 };
