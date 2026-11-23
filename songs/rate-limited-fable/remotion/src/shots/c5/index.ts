// rl5_c (cut 5 package C): the screen shots, ready for D to register in src/shots/index.ts (see workers/rl5_c/PATCH.md).
// Frames = CUT5_PLAN §3 [from, to). Every shot reads its cues as absolute film frames, so register it at these frames.
import { ShotDef } from '../types';
import { C5_1G } from './S1G';
import { C5_3B } from './S3B';
import { C5_3C } from './S3C';
import { C5_4T } from './S4T';
import { C5_4E } from './S4E';
import { C5_8D } from './S8D';
import { C5_9C } from './S9C';
import { C5_10A } from './S10A';
import { C5_5E } from './S5E';
import { C5_7A, C5_7B, C5_7C } from './S7';
import { C5_2G, C5_5H, C5_8E, C5_LAB, C5_LAB_FRAMES } from './Layers';
export { C5_LAB, C5_LAB_FRAMES };

export const C5_SHOTS: Record<string, ShotDef> = { '1G': C5_1G, '3B': C5_3B, '3C': C5_3C, '4T': C5_4T, '4E': C5_4E, '8D': C5_8D, '9C': C5_9C, '10A': C5_10A,
  '5E': C5_5E, '7A': C5_7A, '7B': C5_7B, '7C': C5_7C,
  // placeholders on cut 4e plates (glass layer on top); swap the stage for B's K plate + GlassChat when it lands
  '2G': C5_2G, '5H': C5_5H, '8E': C5_8E };
export const C5_FRAMES: Record<string, [number, number]> = {
  '1G': [478, 530], '2G': [1121, 1190], '3B': [1260, 1330], '3C': [1330, 1451], '4T': [1451, 1712], '4E': [1712, 1851], '5E': [2580, 2719], '5H': [2719, 2858],
  '7A': [3136, 3205], '7B': [3205, 3275], '7C': [3275, 3344], '7E1': [3414, 3553], '8A': [3691, 3830], '8D': [3830, 3969], '8E': [3969, 4108],
  '9A': [4246, 4385], '9C': [4455, 4593], '9E1': [4593, 4662], '9E2': [4662, 4732], '10A': [4836, 4975], '13E': [6358, 6598],
};
