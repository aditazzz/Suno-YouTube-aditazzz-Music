// rl_seca: sections 3-6 (3A..6D), one file per shot in s03..s06. Registered in ../index.ts as ...SECA.
import { ShotDef } from '../types';
import { S3_3A } from './3A'; import { S3_3B } from './3B'; import { S3_3C } from './3C'; import { S3_3D } from './3D';
import { S4_4A } from '../s04/4A'; import { S4_4B } from '../s04/4B'; import { S4_4C } from '../s04/4C'; import { S4_4D } from '../s04/4D';
import { S4_4E } from '../s04/4E'; import { S4_4F } from '../s04/4F'; import { S4_4G } from '../s04/4G'; import { S4_4H } from '../s04/4H';
import { S4_4I } from '../s04/4I'; import { S4_4J } from '../s04/4J';
import { S5_5A } from '../s05/5A'; import { S5_5B } from '../s05/5B'; import { S5_5C } from '../s05/5C'; import { S5_5D } from '../s05/5D';
import { S5_5E } from '../s05/5E'; import { S5_5F } from '../s05/5F'; import { S5_5G } from '../s05/5G'; import { S5_5H } from '../s05/5H';
import { S6_6A } from '../s06/6A'; import { S6_6B } from '../s06/6B'; import { S6_6C } from '../s06/6C'; import { S6_6D } from '../s06/6D';

export const SECA: Record<string, ShotDef> = {
  '3A': S3_3A, '3B': S3_3B, '3C': S3_3C, '3D': S3_3D,
  '4A': S4_4A, '4B': S4_4B, '4C': S4_4C, '4D': S4_4D, '4E': S4_4E, '4F': S4_4F, '4G': S4_4G, '4H': S4_4H, '4I': S4_4I, '4J': S4_4J,
  '5A': S5_5A, '5B': S5_5B, '5C': S5_5C, '5D': S5_5D, '5E': S5_5E, '5F': S5_5F, '5G': S5_5G, '5H': S5_5H,
  '6A': S6_6A, '6B': S6_6B, '6C': S6_6C, '6D': S6_6D,
};
