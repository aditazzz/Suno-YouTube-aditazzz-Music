// rl5_d3 cut 5 2C (774-843): CUT5_PLAN §3 "Over his shoulder: her at the chained door, palm on the glass, cuffs closed, five fingers."
// Camera "Slow drift right". rl5_a1's re-dress c5/2C/K1.jpg (bodysuit, closed cuffs) STILL HAS his held 429 paddle in the foreground
// (banished film-wide: plan §2e, A1's own PATCH) and a fist, not a palm: framed tight on the top of the plate so the paddle (disc top
// y 821 stage) stays out: s 1.82, frame bottom <= 792. Her face, fist, the chain and his spikes stay in. Re-render requested (FOR THE DIRECTOR).
import React from 'react';
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { ShotDef } from '../types';
import { plateShot } from './plate';
import { Grain2 } from '../../blocks/real/Scene';

// 12:22 A1's P2 landed (his paddle lowered: only a sliver of its rim at the bottom edge, plate y >= 1337 stage): the real
// over-the-shoulder, her whole figure at the chained door. s 1.10 anchored on the top keeps the rim out (frame bottom 1309).
export const C5_2C_SRC = 'c5/2C/K1.jpg';      // K1 (paddle up) is only used framed tight on her face (teaser beat 3)
export const C5_2C_WIDE = 'c7/apt/2C_P2e_slop.jpg'   // rl7_master: rl7_apt_fin locked room;
export const CAM_2C = { a: { cx: 1220, cy: 655, s: 1.10 }, b: { cx: 1300, cy: 655, s: 1.10 } };
const base = plateShot({ src: C5_2C_WIDE, cam: [CAM_2C.a, CAM_2C.b] });
export const C5_2C: ShotDef = { ...base, stage: (p) => { const S = base.stage; const f = useCurrentFrame(); return <AbsoluteFill><S {...p} /><Grain2 f={f} /></AbsoluteFill>; } };
