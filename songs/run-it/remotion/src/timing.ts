// Every frame is a pure function of time. All song data comes from build/*.json (copied into src/data).
// timeline.json = tools/make_timeline.py (shots.yaml lands + meter steps, timed.json words with the vocal-MIDI fixes,
// the drum-MIDI beats and kicks). Re-run it whenever shots.yaml / build/*.json change.
import timelineRaw from './data/timeline.json';
import sectionsRaw from './data/sections.json';

export const FPS = 30;
export const DURATION_SEC = 198.0; // 3:18.0 (sections.json OUTRO ends at 198.0)
export const DURATION_FRAMES = Math.round(DURATION_SEC * FPS); // 5940

export type Line = { sec: string; text: string; words: string[]; wt: number[]; s: number; e: number; shot?: string; src?: string };
export type TShot = { id: string; at: number; t?: number; sec?: string; title?: string; land: number; land_bar?: string; lines: number[];
  payoff: { word: string; t: number; lift: number } | null; meter: number | null };
export type MeterStep = { t: number; v: number; shot: string };
export const timeline = timelineRaw as unknown as { fps: number; end: number; beats: number[]; downbeats: number[]; kicks: number[];
  snares: number[]; hats: number[]; lines: Line[]; shots: TShot[]; meter: MeterStep[]; edits: any[]; edit_points: number[] };
export const tshots: TShot[] = timeline.shots;
export const tshot = (id: string) => tshots.find((s) => s.id === id)!;
export type Section = { name: string; s: number; e: number; kind: string; first_line: string };

export const lines: Line[] = timeline.lines;
export const sections: Section[] = sectionsRaw as Section[];
export const downbeats: number[] = timeline.downbeats;
export const beats: number[] = timeline.beats;
export const kicks: number[] = timeline.kicks;
export const snares: number[] = timeline.snares;
export const hats: number[] = timeline.hats;
/** Index of the beat containing t (fractional part = position inside the beat). */
export const beatPos = (t: number) => { const i = Math.max(0, lowerBound(beats, t + 1e-6) - 1); const b = beats[i], n = beats[i + 1] ?? b + 0.5; return i + Math.min(0.999, Math.max(0, (t - b) / (n - b))); };

export const frameOf = (t: number) => Math.round(t * FPS);
export const timeOf = (frame: number) => frame / FPS;

// first index with a[i] >= t (a sorted)
function lowerBound(a: number[], t: number) {
  let lo = 0, hi = a.length;
  while (lo < hi) { const m = (lo + hi) >> 1; if (a[m] < t) lo = m + 1; else hi = m; }
  return lo;
}

/** First downbeat at or after t (sec). Past the last downbeat: the last one. */
export const downbeatAtOrAfter = (t: number) => downbeats[Math.min(lowerBound(downbeats, t - 1e-6), downbeats.length - 1)];
/** Same, as a frame number: where a world change on the downbeat should land. */
export const downbeatFrameAtOrAfter = (t: number) => frameOf(downbeatAtOrAfter(t));
/** 0-based bar index containing t (bar n starts at downbeats[n]). -1 before the first downbeat. */
export const barOf = (t: number) => Math.max(-1, lowerBound(downbeats, t + 1e-6) - 1);
/** Beat position inside the bar, 0..<4 (fractional), for t. */
export const beatInBar = (t: number) => {
  const b = barOf(t); if (b < 0) return 0;
  const i = lowerBound(beats, t + 1e-6) - 1;
  const bi = beats[i] ?? downbeats[b];
  const next = beats[i + 1] ?? bi + 0.5;
  return Math.min(3.999, (i - lowerBound(beats, downbeats[b] - 1e-6)) + (t - bi) / Math.max(1e-6, next - bi));
};

/** Seconds since the latest hit in `a` at or before t (Infinity before the first). */
export function sinceHit(a: number[], t: number) {
  const i = lowerBound(a, t + 1e-6) - 1;
  return i < 0 ? Infinity : t - a[i];
}
/** Seconds until the next hit after t (Infinity after the last). */
export function untilHit(a: number[], t: number) {
  const i = lowerBound(a, t + 1e-6);
  return i >= a.length ? Infinity : a[i] - t;
}
/** Kick envelope 0..1: 1 on the hit, exponential fall-off (decay seconds). Pure function of t. */
export const kickEnv = (t: number, decay = 0.22) => { const d = sinceHit(kicks, t); return d === Infinity ? 0 : Math.exp(-d / decay); };
export const snareEnv = (t: number, decay = 0.18) => { const d = sinceHit(snares, t); return d === Infinity ? 0 : Math.exp(-d / decay); };
export const hatEnv = (t: number, decay = 0.08) => { const d = sinceHit(hats, t); return d === Infinity ? 0 : Math.exp(-d / decay); };

// ---- lyric lines ----
/** Sung onset of every word in a line (sec), from timed.json `wt`. */
export const wordOnsets = (line: Line) => line.wt;
/** The line being sung/held at t: the last line whose first word has started (undefined before the first). */
export function lineAt(t: number): Line | undefined {
  let r: Line | undefined;
  for (const l of lines) { if (l.wt[0] <= t + 1e-6) r = l; else break; }
  return r;
}
export const lineIndexAt = (t: number) => { const l = lineAt(t); return l ? lines.indexOf(l) : -1; };
/** Word onsets per line, in order: [[t,t,..],..] */
export const onsetsPerLine = () => lines.map(wordOnsets);

export const sectionAt = (t: number): Section => sections.find((s) => t >= s.s && t < s.e) ?? sections[sections.length - 1];

// ---- the prompt bar as a pure function of time ----
const TYPE_SEC = 0.14;      // a word's letters land over this long, starting at its sung onset
const CLEAR_GAP = 2.5;      // if the next line is this far past the last word's end, the bar empties after SUBMIT_HOLD
const SUBMIT_HOLD = 0.55;   // seconds the finished line stays after its end before the bar empties (long gaps)
export const SUBMIT_FLASH = 0.22; // seconds the submit flash lasts

export type PromptState = { text: string; typing: boolean; lastTypedAt: number; flash: number; lineIndex: number };

/** What the bar shows at t: the typed text so far, whether a word is mid-type, and the submit flash 0..1. */
export function promptAt(t: number): PromptState {
  const li = lineIndexAt(t);
  if (li < 0) return { text: '', typing: false, lastTypedAt: -Infinity, flash: 0, lineIndex: -1 };
  const l = lines[li], next = lines[li + 1];
  // submit happens when the line ends (last word onset + a little), never later than the next line's first word.
  // Lines with a payoff (the grammar): submit = the payoff lift (land - 0.30), when the payoff word flies to what it changes.
  const lastOn = l.wt[l.wt.length - 1];
  const sh = l.shot ? tshot(l.shot) : undefined;
  const lift = sh?.payoff && sh.lines[sh.lines.length - 1] === li && sh.payoff.lift >= lastOn + 0.15 ? sh.payoff.lift : undefined;
  const submitAt = Math.min(lift ?? Math.max(l.e, lastOn + 0.2), next ? next.wt[0] - 0.04 : Infinity);
  // typed characters so far
  let text = '', typing = false, lastTypedAt = l.wt[0];
  for (let i = 0; i < l.words.length; i++) {
    const w = l.words[i], on = l.wt[i];
    if (t < on) break;
    const frac = Math.min(1, (t - on) / TYPE_SEC);
    const n = Math.max(1, Math.ceil(frac * w.length)); // first letter lands exactly at the onset
    text += (i ? ' ' : '') + w.slice(0, n);
    lastTypedAt = on + TYPE_SEC;
    typing = frac < 1;
  }
  let flash = 0;
  if (t >= submitAt && t < submitAt + SUBMIT_FLASH) flash = 1 - (t - submitAt) / SUBMIT_FLASH;
  // after a long gap the bar empties
  const gapNext = next ? next.wt[0] - l.e : Infinity;
  // (a line with a world change stays up until 1.2 s after its land, so the prompt and its result share the frame)
  const holdTill = Math.max(submitAt + SUBMIT_HOLD, sh && sh.lines[sh.lines.length - 1] === li ? sh.land + 1.2 : -Infinity);
  if (t >= holdTill && gapNext > CLEAR_GAP) text = '';
  return { text, typing, lastTypedAt, flash, lineIndex: li };
}

// ---- memory meter: the shots' meter steps (shots.yaml `meter`, on each shot's land), counting up over COUNT_SEC ----
const COUNT_SEC = 0.32;
export function memoryAt(t: number) {
  const M = timeline.meter;
  let v = M.length ? M[0].v : 0;
  for (let i = 0; i < M.length; i++) {
    if (t < M[i].t) break;
    const k = Math.min(1, (t - M[i].t) / COUNT_SEC), e = 1 - Math.pow(1 - k, 3);
    v = v + (M[i].v - v) * e;
  }
  return v;
}
