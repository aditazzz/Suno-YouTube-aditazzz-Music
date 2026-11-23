// Shot registry: shot id (BOARDS id, e.g. "1A") -> its ShotDef. Anything not listed plays the animatic default.
// Section workers: add src/shots/s<NN>/<ID>.tsx exporting a ShotDef and register it here, one line per shot.
// See README.md "Adding a shot".
import { ShotDef } from './types';
import { AnimaticShot } from './Animatic';
import { S1_1A, S1_1B } from './first30/S1AB';
import { S1_1C } from './first30/S1C';
import { S1_1D } from './first30/S1D';
import { S1_1E } from './first30/S1E';
import { S1_1F } from './first30/S1F';
import { S1_1G } from './first30/S1G';
import { S1_1H } from './first30/S1H';
import { S1_1I } from './first30/S1I';
import { S2_2A } from './first30/S2A';
import { S2_2B } from './first30/S2B';
import { S2_2C } from './first30/S2C';
import { S2_2D } from './first30/S2D';
import { S2_2E } from './first30/S2E';
import { S2_2F } from './first30/S2F';
import { S2_2G } from './first30/S2G';
import { SECB } from './s07/secb';   // rl_secb: sections 7-9
import { SECC } from './s10/secc';   // rl_secc: sections 10-13
import { SECA } from './s03/seca';   // rl_seca: sections 3-6

import { c5Defs } from './c5d';   // rl5_d: cut 5 (CUT5_PLAN §3)

// cut 4e's map (kept whole: cut 5's merged shots play these pieces)
export const OLD_DEFS: Record<string, ShotDef> = {
  // '1A': S1_1A,
  // rl_first30 (the first 30 s, src/shots/first30/)
  '1A': S1_1A, '1B': S1_1B, '1C': S1_1C, '1D': S1_1D, '1E': S1_1E, '1F': S1_1F, '1G': S1_1G, '1H': S1_1H, '1I': S1_1I,
  '2A': S2_2A, '2B': S2_2B, '2C': S2_2C, '2D': S2_2D, '2E': S2_2E, '2F': S2_2F, '2G': S2_2G,
  ...SECA,   // rl_seca: 3A-6D (src/shots/s03/seca.ts)
  ...SECB,   // rl_secb: 7A-9G (src/shots/s07/secb.ts)
  ...SECC,   // rl_secc: 10A-13E (src/shots/s10/secc.ts)
};
export const SHOT_DEFS: Record<string, ShotDef> = { ...OLD_DEFS, ...c5Defs(OLD_DEFS) };
export const shotDef = (id: string): ShotDef => SHOT_DEFS[id] ?? AnimaticShot;
