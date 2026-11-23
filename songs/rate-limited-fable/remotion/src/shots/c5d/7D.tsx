// rl5_d2 cut 5 7D (3344-3414): CUT5_PLAN §3 "Her hopeful smile freezing behind the glass. Slow push." Her only (cut 4e opened on his
// visor close in front of a cork board of paper notices: out, per the plan row and her no-papers rule). rl5_a1's re-dress (bodysuit):
// c5/7D/7D_smile -> 7D_frozen on "met." (3377, words.json), one slow push.
import React from 'react';
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { ShotDef } from '../types';
import { plateShot } from './plate';
import { Grain2 } from '../../blocks/real/Scene';

const FREEZE = 3377;
const base = plateShot({ src: (f) => (f < FREEZE - 3344 ? 'c7/apt/7D_smile_click.jpg' : 'c7/apt/7D_frozen_click.jpg'),
  cam: [{ cx: 1280, cy: 700, s: 1.02 }, { cx: 1280, cy: 690, s: 1.08 }] });
export const C5_7D: ShotDef = { ...base, stage: (p) => { const S = base.stage; const f = useCurrentFrame(); return <AbsoluteFill><S {...p} /><Grain2 f={f} /></AbsoluteFill>; } };
