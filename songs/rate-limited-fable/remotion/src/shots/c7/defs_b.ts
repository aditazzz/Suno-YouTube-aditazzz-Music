// Cut 7, lane R-B's blocks (B31-B61, sections 7-13). R-B owns this file and src/shots/c7/s07..s13/**, src/data/c7b/** (and the kit, since
// rl7_ra exited). Each entry: block id -> ShotDef (props.shot = the BLOCK, src/data/blocks_c7.json). A block missing here plays cut 6.
import { ShotDef } from '../types';
import { B7 } from './s07';
import { B9 } from './s09';
import { B10 } from './s10';
import { B12 } from './s12';

export const DEFS_B: Record<string, ShotDef> = { ...B7, ...B9, ...B10, ...B12 };
