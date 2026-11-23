// Song data as pure functions of time. All of it comes from src/data/*.json (tools/build_data.py writes them from
// build/shots/shots.json or BOARDS, bts_reel/work/beats_midi.json + 0.23 s, build/words.json). Re-run build_data.py
// whenever those change; nothing here is hand-typed.
import shotsRaw from './data/shots.json';
import beatsRaw from './data/beats.json';
import wordsRaw from './data/words.json';
import { FPS } from './theme';

export type Shot = {
  id: string; s: number; e: number; from: number; to: number; dur: number; sec: number; section: string;
  clock: string; lyric: string; set: string; words: string; plate: string | null; new: boolean; cx916: number;
  move: string;
  /** rl_shots' measured on-word / on-hit cues (absolute film frame + seconds); key actions to these, not to the lyric sheet */
  cues?: Cue[]; grid?: number[];
};
export type Cue = { cue: string; word: string; t: number; frame: number; kind: string; confidence: string };
export const SHOTS: Shot[] = (shotsRaw as any).shots;
export const DURATION_FRAMES: number = (shotsRaw as any).frames;
export const SHOT_SOURCE: string = (shotsRaw as any).source; // 'rl_shots' or 'boards'
export const shotById = (id: string) => SHOTS.find((s) => s.id === id)!;
/** shot-local frame of the shot's cue whose name or word contains `q` (case-insensitive); n = which match (0-based) */
export const cueFrame = (shot: Shot, q: string, n = 0): number | null => {
  const k = q.toLowerCase(); const hits = (shot.cues ?? []).filter((c) => c.cue.toLowerCase().includes(k) || c.word.toLowerCase().includes(k));
  return hits[n] ? hits[n].frame - shot.from : null;
};

export const BEATS: number[] = (beatsRaw as any).beats;
export const DOWNBEATS: number[] = (beatsRaw as any).downbeats;
export const WORDS: [number, string][] = wordsRaw as any;

export const frameOf = (t: number) => Math.round(t * FPS);
export const timeOf = (f: number) => f / FPS;

function lowerBound(a: number[], t: number) {
  let lo = 0, hi = a.length;
  while (lo < hi) { const m = (lo + hi) >> 1; if (a[m] < t) lo = m + 1; else hi = m; }
  return lo;
}
/** fractional beat index at time t (3.5 = halfway through beat 3) */
export const beatPos = (t: number) => {
  const i = Math.max(0, lowerBound(BEATS, t + 1e-6) - 1); const b = BEATS[i], n = BEATS[i + 1] ?? b + 0.579;
  return i + Math.min(0.999, Math.max(0, (t - b) / (n - b)));
};
/** seconds since the last beat (or downbeat, with bars=true) at or before t; Infinity before the first */
export const sinceBeat = (t: number, bars = false) => { const a = bars ? DOWNBEATS : BEATS; const i = lowerBound(a, t + 1e-6) - 1; return i < 0 ? Infinity : t - a[i]; };
/** the beat nearest t, and the first beat / downbeat at or after t (seconds) */
export const nearestBeat = (t: number) => { const i = lowerBound(BEATS, t); const a = BEATS[Math.max(0, i - 1)], b = BEATS[Math.min(BEATS.length - 1, i)]; return Math.abs(t - a) <= Math.abs(b - t) ? a : b; };
export const beatAtOrAfter = (t: number) => BEATS[Math.min(lowerBound(BEATS, t - 1e-6), BEATS.length - 1)];
export const downbeatAtOrAfter = (t: number) => DOWNBEATS[Math.min(lowerBound(DOWNBEATS, t - 1e-6), DOWNBEATS.length - 1)];
/** BOARDS bar notation "12.3" (bar 12, beat 3; 1-based) -> seconds */
export const barBeat = (bb: string | number) => { const [b, k = '1'] = String(bb).split('.'); return BEATS[Math.min(BEATS.length - 1, (Number(b) - 1) * 4 + Number(k) - 1)]; };
/** 1 on the beat, decaying to 0 over `len` seconds: for a hit/flash/pulse keyed to the drums */
export const beatPulse = (t: number, len = 0.18, bars = false) => { const d = sinceBeat(t, bars); return d === Infinity ? 0 : Math.max(0, 1 - d / len); };

/** words sung inside [s, e) (seconds) */
export const wordsIn = (s: number, e: number) => WORDS.filter(([t]) => t >= s && t < e);
/** onset (seconds) of the first word matching `w` (case/punctuation-insensitive) at or after `after` */
export const wordAt = (w: string, after = 0) => {
  const k = w.toLowerCase().replace(/[^a-z0-9']/g, '');
  const hit = WORDS.find(([t, x]) => t >= after && x.toLowerCase().replace(/[^a-z0-9']/g, '') === k);
  return hit ? hit[0] : null;
};

// Clock helpers. BOARDS clocks are like "11:58 PM to 2:04 AM" or "2:04 AM". Minutes since 6 PM keep the night monotonic.
export const parseClock = (c: string): number => {
  const m = c.trim().match(/(\d{1,2}):(\d{2})(?::(\d{2}))?\s*(AM|PM|a\.m\.|p\.m\.)?/i); if (!m) return 0;
  let h = Number(m[1]) % 12; const pm = /p/i.test(m[4] || 'AM'); if (pm) h += 12;
  const mins = h * 60 + Number(m[2]) + Number(m[3] || 0) / 60;
  return (mins - 18 * 60 + 24 * 60) % (24 * 60); // minutes after 6 PM
};
export const clockRange = (shot: Shot): [number, number] => {
  // "2:04 to 2:06 AM": a part without AM/PM takes the other part's
  const parts = shot.clock.split(/\s+to\s+/i).map((p) => p.trim()).filter(Boolean);
  if (!parts.length) return [0, 0];
  const suf = (p: string) => (p.match(/\b(AM|PM)\b/i) || [])[1];
  const fix = (p: string, other?: string) => (suf(p) ? p : `${p} ${(other && suf(other)) || 'AM'}`);
  const a = parseClock(fix(parts[0], parts[1])); const b = parts[1] ? parseClock(fix(parts[1], parts[0])) : a;
  return [a, b];
};
/** minutes-after-6PM -> "h:mm" (12 h, no suffix) */
export const fmtClock = (m: number, secs = false) => {
  const total = (m + 18 * 60) % (24 * 60); let h = Math.floor(total / 60) % 12; if (h === 0) h = 12;
  const mm = Math.floor(total % 60), ss = Math.floor((total * 60) % 60);
  return `${h}:${String(mm).padStart(2, '0')}${secs ? ':' + String(ss).padStart(2, '0') : ''}`;
};
