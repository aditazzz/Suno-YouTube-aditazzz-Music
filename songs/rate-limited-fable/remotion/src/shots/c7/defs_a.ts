// Cut 7, lane R-A's blocks (B01-B30, sections 1-6). Block id -> ShotDef; props.shot is the block (kit/blocks.ts).
import { ShotDef } from '../types';
import { A1 } from './s01';
import { A4 } from './s04';

export const DEFS_A: Record<string, ShotDef> = { ...A1, ...A4 };
