// rl_secb: sections 7-9 (7AB..9G) in one map, spread into SHOT_DEFS by ../index.ts (one line there, fewer edit collisions).
import { ShotDef } from '../types';
import { S7_7A, S7_7B } from './7AB';
import { S7_7C } from './7C';
import { S7_7D } from './7D';
import { S7_7E } from './7E';
import { S7_7F } from './7F';
import { S7_7G } from './7G';
import { S7_7H } from './7H';
import { S8_8A } from '../s08/8A';
import { S8_8B, S8_8C } from '../s08/8B';
import { S8_8D } from '../s08/8D';
import { S8_8E } from '../s08/8E';
import { S8_8F } from '../s08/8F';
import { S8_8G } from '../s08/8G';
import { S9_9A } from '../s09/9A';
import { S9_9B } from '../s09/9B';
import { S9_9C } from '../s09/9C';
import { S9_9D } from '../s09/9D';
import { S9_9E } from '../s09/9E';
import { S9_9F } from '../s09/9F';
import { S9_9G } from '../s09/9G';
export const SECB: Record<string, ShotDef> = {
  '7A': S7_7A, '7B': S7_7B, '7C': S7_7C, '7D': S7_7D, '7E': S7_7E, '7F': S7_7F, '7G': S7_7G, '7H': S7_7H,
  '8A': S8_8A, '8B': S8_8B, '8C': S8_8C, '8D': S8_8D, '8E': S8_8E, '8F': S8_8F, '8G': S8_8G,
  '9A': S9_9A, '9B': S9_9B, '9C': S9_9C, '9D': S9_9D, '9E': S9_9E, '9F': S9_9F, '9G': S9_9G,
};
