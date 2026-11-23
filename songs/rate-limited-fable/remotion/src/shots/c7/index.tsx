// Cut 7 block registry (rl7_ra owns this file). Blocks B01-B30: ./defs_a (R-A); B31-B61: ./defs_b (R-B).
// Film.tsx (cut=7) draws BLOCKS (src/data/blocks_c7.json) with c7Def(block): the block's new def, else cut 6's shots for its frames.
import { ShotDef } from '../types';
import { Shot } from '../../timing';
import { DEFS_A } from './defs_a';
import { DEFS_B } from './defs_b';
import { fallback } from './kit/fallback';

export { BLOCKS } from './kit/blocks';
export const C7_DEFS: Record<string, ShotDef> = { ...DEFS_A, ...DEFS_B };
const FB: Record<string, ShotDef> = {};
export const c7Def = (b: Shot): ShotDef => C7_DEFS[b.id] ?? (FB[b.id] ??= fallback(b));
