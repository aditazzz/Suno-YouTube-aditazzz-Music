// rl_secc: sections 10-13 (10A..13E), one file per shot in s10/ s11/ s12/ s13/; shared kit in s10/_lib.tsx.
import { ShotDef } from '../types';
import { S10_10A } from './10A';
import { S10_10B } from './10B';
import { S11_11A } from '../s11/11A';
import { S11_11B } from '../s11/11B';
import { S11_11C } from '../s11/11C';
import { S11_11D } from '../s11/11D';
import { S11_11E } from '../s11/11E';
import { S12_12A } from '../s12/12A';
import { S12_12B } from '../s12/12B';
import { S12_12C } from '../s12/12C';
import { S12_12D } from '../s12/12D';
import { S12_12E } from '../s12/12E';
import { S12_12F } from '../s12/12F';
import { S12_12G } from '../s12/12G';
import { S12_12H } from '../s12/12H';
import { S12_12I } from '../s12/12I';
import { S13_13A } from '../s13/13A';
import { S13_13B } from '../s13/13B';
import { S13_13C } from '../s13/13C';
import { S13_13D } from '../s13/13D';
import { S13_13E } from '../s13/13E';

export const SECC: Record<string, ShotDef> = {
  '10A': S10_10A, '10B': S10_10B,
  '11A': S11_11A, '11B': S11_11B, '11C': S11_11C, '11D': S11_11D, '11E': S11_11E,
  '12A': S12_12A, '12B': S12_12B, '12C': S12_12C, '12D': S12_12D, '12E': S12_12E, '12F': S12_12F, '12G': S12_12G, '12H': S12_12H, '12I': S12_12I,
  '13A': S13_13A, '13B': S13_13B, '13C': S13_13C, '13D': S13_13D, '13E': S13_13E,
};
