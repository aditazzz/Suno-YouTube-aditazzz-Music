// rl5_d3 cut 5 1D (286-356): CUT5_PLAN §3 "Two-room wide: he's at the ShipIt! counter, she's at the door with her first parcel; neon on.
// One set state all shot." Camera: "Slow slide left toward the door". rl5_a1's re-dress (c5/1D/T1s.jpg: bodysuit, barefoot on the boards,
// her FAME parcel, kit5 lobby), ONE plate state first frame to last. Cut 4e's 1D pasted old-render crops on top (her sweater layer, the cat
// paw, the jamb), slid in two old parcels and comp'd a panda clock: all out (plan §2e "No comp'd clocks anywhere"; pile = 1 in 1D).
// KNOWN (12:10, sent to rl5_b): kit5's far-wall ShipIt! sign sits behind the handless 3D clock; lands by C5PATH when re-rendered.
import React from 'react';
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { ShotDef } from '../types';
import { plateShot } from './plate';
import { Grain2 } from '../../blocks/real/Scene';

const base = plateShot({ src: 'c6/1D/T1s.jpg', cam: [{ cx: 1350, cy: 745, s: 1.06 }, { cx: 1220, cy: 745, s: 1.06 }] });
export const C5_1D: ShotDef = { ...base, stage: (p) => { const S = base.stage; const f = useCurrentFrame(); return <AbsoluteFill><S {...p} /><Grain2 f={f} /></AbsoluteFill>; } };
