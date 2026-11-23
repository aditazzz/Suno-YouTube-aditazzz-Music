// rl5_d3 cut 5 1A teaser (CUT5_PLAN §3 1A): "Teaser on the three hums (0-54): her hopeful at the chained door (2C plate) -> his visor
// close, eyes blink to 429 (K plate) -> her deadpan. Then the street wide starts." Same cuts as cut 4e (hums 6/24/42, street back at 59),
// same kick on each cut; only the three beats change (first30/teaser.tsx withTeaser(base, beats)). All three pictures are cut-5 plates:
//  0-23  her at the chained door, knocking (c5d/2C framing, above his paddle);   24-41  K plate close, eyes -> closed -> 429 (C5_TZ_K);
//  42-58 her face, tight (same 2C plate, s 2.0; her expression is the one A1 rendered: reads flat/deadpan, not a new pose).
import { ShotDef } from '../types';
import { shotById } from '../../timing';
import { withTeaser, Beat } from '../first30/teaser';
import { S1_1A_BASE } from '../first30/S1AB';
import { C5_2C } from './2C';
import { C5_TZ_K } from './K';
import { plateShot } from './plate';

const sh2B = shotById('2B'), sh2C = shotById('2C');
const DEADPAN: ShotDef = plateShot({ src: 'c7/apt/2C_K1_dp_slop.jpg', cam: [{ cx: 1180, cy: 360, s: 2.0 }, { cx: 1186, cy: 362, s: 2.05 }] });
const BEATS5: Beat[] = [
  { def: C5_2C, shot: sh2C, map: (k) => 6 + k },
  { def: C5_TZ_K, shot: { ...sh2B, dur: 18 }, map: (k) => k },
  { def: DEADPAN, shot: { ...sh2C, dur: 17 }, map: (k) => k },
];
export const C5_1A: ShotDef = withTeaser(S1_1A_BASE, BEATS5);
