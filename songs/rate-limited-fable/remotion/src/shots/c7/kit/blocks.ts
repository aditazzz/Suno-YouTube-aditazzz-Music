// Cut 7 blocks (src/data/blocks_c7.json, from PLAN7 §1 by workers/rl7_ra/make_blocks.py). A block is Shot-shaped (id, from, to,
// dur, cues, grid, cx916 ...) so every ShotDef/ShotProps works unchanged: its cues/grid are the union of the cut 6 shots it spans.
import blocksRaw from '../../../data/blocks_c7.json';
import { SHOTS, Shot, BEATS, DOWNBEATS } from '../../../timing';

export type Block = Shot & { n: number; kind: string; old: string[]; cuts: number[] };
const raw = (blocksRaw as any).blocks as { id: string; n: number; from: number; to: number; dur: number; kind: string; old: string[]; cuts: number[]; sec: string }[];
export const OLD = (id: string): Shot => SHOTS.find((s) => s.id === id)!;
export const BLOCKS: Block[] = raw.map((b) => {
  const olds = b.old.map(OLD); const first = olds[0];
  return {
    ...first, id: b.id, n: b.n, kind: b.kind, old: b.old, cuts: b.cuts, from: b.from, to: b.to, dur: b.dur,
    s: b.from / 30, e: b.to / 30, section: first.section,
    cues: olds.flatMap((o) => o.cues ?? []), grid: olds.flatMap((o) => o.grid ?? []),
  } as Block;
});
export const block = (id: string): Block => BLOCKS.find((b) => b.id === id)!;
/** block-local frame of an absolute film frame */
export const loc = (b: Shot, abs: number) => abs - b.from;
/** block-local frames of the beats (or downbeats) inside a block */
export const beatsIn = (b: Shot, bars = false) => (bars ? DOWNBEATS : BEATS).map((t) => Math.round(t * 30) - b.from).filter((x) => x >= 0 && x < b.dur);
