import SONG from '../public/data/song.json';
import SPEC from '../public/data/spec.json';
import {clamp} from './lib';

export type Line = {sec: string; text: string; words: string[]; wt: number[]; s: number; e: number};
export type Section = {name: string; s: number; e: number};

export const FPS = 30;
export const SONG_END: number = SONG.duration;
export const LINES = SONG.lines as Line[];
export const BEATS: number[] = SONG.beats;
export const DOWNBEATS: number[] = SONG.downbeats;
export const SECTIONS = SONG.sections as Section[];

const norm = (s: string) => s.toLowerCase().replace(/[^a-z0-9]/g, '');

export function line(sub: string, nth = 0): Line {
  const n = sub.toLowerCase();
  const hits = LINES.filter((l) => l.text.toLowerCase().includes(n));
  if (!hits.length) throw new Error(`no lyric line contains "${sub}"`);
  return hits[Math.min(nth, hits.length - 1)];
}
export const lt = (sub: string, nth = 0) => line(sub, nth).s;
export const le = (sub: string, nth = 0) => line(sub, nth).e;
// the time of `word` inside the nth line containing `sub` (the wn-th occurrence of that word in the line)
export function wt(sub: string, word: string, nth = 0, wn = 0): number {
  const l = line(sub, nth);
  const w = norm(word);
  let k = 0;
  for (let i = 0; i < l.words.length; i++) {
    if (norm(l.words[i]) === w || (w.length > 3 && norm(l.words[i]).startsWith(w))) {
      if (k++ === wn) return l.wt[i];
    }
  }
  throw new Error(`no word "${word}" in "${l.text}"`);
}
// every time `word` is sung in the lines of section `sec`
export function wordTimes(sec: string, word: string): number[] {
  const w = norm(word), out: number[] = [];
  for (const l of LINES) if (l.sec === sec) l.words.forEach((x, i) => norm(x) === w && out.push(l.wt[i]));
  return out;
}
export function linesOf(sec: string) {
  return LINES.filter((l) => l.sec === sec);
}
export function sec(name: string): {s: number; e: number} {
  const ls = linesOf(name);
  const ss = SECTIONS.filter((s) => s.name === name);
  return {s: ss.length ? ss[0].s : ls[0].s, e: ss.length ? ss[ss.length - 1].e : ls[ls.length - 1].e};
}

export function lastBeat(t: number, list = BEATS) {
  let lo = 0, hi = list.length - 1;
  if (t < list[0]) return list[0] - 60 / SONG.tempo;
  while (lo < hi) {
    const m = (lo + hi + 1) >> 1;
    if (list[m] <= t) lo = m;
    else hi = m - 1;
  }
  return list[lo];
}
export const beatPulse = (t: number, decay = 0.14) => Math.exp(-(t - lastBeat(t)) / decay);
export const barPulse = (t: number, decay = 0.25) => Math.exp(-(t - lastBeat(t, DOWNBEATS)) / decay);
export const BEAT = 60 / SONG.tempo;
export function nearestBeat(t: number, list = BEATS) {
  let best = list[0];
  for (const b of list) if (Math.abs(b - t) < Math.abs(best - t)) best = b;
  return best;
}

const SPEC_RAW = Uint8Array.from(atob(SPEC.b64), (c) => c.charCodeAt(0));
export const NB: number = SPEC.bands;
const NF: number = SPEC.frames;
export function band(t: number, i: number) {
  const f = clamp(t * SPEC.fps, 0, NF - 1.001);
  const f0 = Math.floor(f), k = f - f0;
  const a = SPEC_RAW[f0 * NB + i], b = SPEC_RAW[(f0 + 1) * NB + i];
  return (a + (b - a) * k) / 255;
}
export function level(t: number, lo = 0, hi = NB) {
  let s = 0;
  for (let i = lo; i < hi; i++) s += band(t, i);
  return s / (hi - lo);
}
export const bass = (t: number) => level(t, 0, 6);
export const mids = (t: number) => level(t, 10, 26);
export const highs = (t: number) => level(t, 30, 48);
