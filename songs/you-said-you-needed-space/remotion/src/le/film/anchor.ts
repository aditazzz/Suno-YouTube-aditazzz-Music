// Anchors -> seconds, the TS twin of timing/timing.py's anchors (the generated TIMING table is the only source of numbers).
//   'chorus1'            section start        'chorus1/end'      section end
//   'chorus1/L2'         line 2's onset       'chorus1/L2/w3'    line 2, word 3's onset
//   any of those + '+0.4' or '-1.2' seconds;  or a plain number (seconds).
import { TIMING } from './timing.gen';
export type Anchor = string | number;
const RX = /^([A-Za-z0-9]+)(?:\/(end|L(\d+)(?:\/w(\d+))?))?([+-]\d+(?:\.\d+)?)?$/;
export function at(a: Anchor): number {
  if (typeof a === 'number') return a;
  const m = RX.exec(a.trim());
  if (!m) throw new Error(`le anchor: bad ${a}`);
  const [, sid, kind, li, wi, off] = m;
  const sec = TIMING.sections[sid];
  if (!sec) throw new Error(`le anchor: unknown section in ${a}`);
  let t = sec[0];
  if (kind === 'end') t = sec[1];
  else if (li !== undefined) {
    const line = TIMING.lines[sid]?.[+li];
    if (!line) throw new Error(`le anchor: ${sid} has no line ${li} (${a})`);
    t = line.t;
    if (wi !== undefined) { const w = line.words[+wi]; if (!w) throw new Error(`le anchor: no word ${wi} in ${a}`); t = w[0]; }
  }
  return t + (off ? parseFloat(off) : 0);
}
export const FPS = TIMING.fps;
export const DURATION_S = TIMING.duration;
export const DURATION_FRAMES = Math.round(TIMING.duration * TIMING.fps);
export const lineText = (sid: string, i: number) => TIMING.lines[sid]?.[i]?.text ?? '';
export const words = (sid: string, i: number) => TIMING.lines[sid]?.[i]?.words ?? [];
export function sectionAt(t: number): string {
  for (const s of TIMING.order) { const [a, b] = TIMING.sections[s]; if (t >= a && t < b) return s; }
  return TIMING.order[TIMING.order.length - 1];
}
