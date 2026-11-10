// frameAt(t, fmt): the whole film as a pure function of time. Slot = BEATS[i] (beats.ts); its builder (sections/*.ts)
// gets the base frame (camera keys + default grade) and returns what it changes. Crossing into a slot blends from the
// previous slot's frame over BLEND_S (camera/grade numbers lerp, flows/sparks cross-fade), so no slot can pop.
import { BEATS, Beat } from './beats';
import { at, lineText, sectionAt } from './anchor';
import { TIMING } from './timing.gen';
import { GRADE_DEFAULT, Grade } from './grade';
import { Cam, Flow, Fmt, Frame, Spark } from './types';
import { camAt, camFor, setCamKeys } from './camera';
import { setStarKeys } from './stars';
import { SECTIONS, Builder, Ctx, Insert } from './sections';

export const SLOTS = BEATS.map((b, i) => ({ ...b, t0: at(b.at), t1: i + 1 < BEATS.length ? at(BEATS[i + 1].at) : TIMING.duration }));
for (let i = 1; i < SLOTS.length; i++) if (SLOTS[i].t0 < SLOTS[i - 1].t0) throw new Error(`beats.ts: ${SLOTS[i].id} starts before ${SLOTS[i - 1].id}`);
export const BLEND_S = 0.45;

const BUILDERS: Record<string, Builder> = {};
export const INSERTS: (Insert & { t0: number; t1: number })[] = [];
{
  const camKeys = [], starKeys = [];
  for (const s of SECTIONS) {
    Object.assign(BUILDERS, s.builders); camKeys.push(...(s.camera ?? [])); starKeys.push(...(s.stars ?? []));
    for (const ins of s.inserts ?? []) { const sl = SLOTS.find((x) => x.id === ins.slot); if (sl) INSERTS.push({ ...ins, t0: Math.max(sl.t0, ins.from), t1: ins.to !== undefined ? at(ins.to) : sl.t1 }); }
  }
  setCamKeys(camKeys); setStarKeys(starKeys);
  for (const id of Object.keys(BUILDERS)) if (!SLOTS.find((s) => s.id === id)) throw new Error(`sections: builder for unknown slot ${id}`);
}
export function slotIndexAt(t: number) { let i = 0; while (i + 1 < SLOTS.length && SLOTS[i + 1].t0 <= t) i++; return i; }

function baseFrame(t: number): Frame {
  return { t, cam: camAt(t), grade: { ...GRADE_DEFAULT }, flows: [], sparks: [], pulses: [] };
}
const word = (sid: string, li: number, wi: number) => TIMING.lines[sid]?.[li]?.words[wi]?.[0] ?? at(`${sid}/L${li}`);
function build(i: number, t: number, fmt: Fmt): Frame {
  const s = SLOTS[i], base = baseFrame(t);
  const ctx: Ctx = { t, fmt, slot: s, lt: t - s.t0, u: Math.max(0, Math.min(1, (t - s.t0) / (s.t1 - s.t0))), dur: s.t1 - s.t0, base, at, word };
  const b = BUILDERS[s.id];
  const o = b ? b(ctx) : {};
  return { ...base, ...o, cam: { ...base.cam, ...(o.cam ?? {}) } as Cam, grade: { ...base.grade, ...(o.grade ?? {}) } as Grade,
    flows: o.flows ?? [], sparks: o.sparks ?? [], pulses: o.pulses ?? [], built: o.built ?? !!b };
}
const lerp = (a: number, b: number, u: number) => a + (b - a) * u;
function lerpObj<T>(a: T, b: T, u: number): T {
  if (typeof a === 'number' && typeof b === 'number') return lerp(a, b, u) as unknown as T;
  if (Array.isArray(a) && Array.isArray(b) && a.length === b.length) return a.map((x, i) => lerpObj(x, b[i], u)) as unknown as T;
  if (a && b && typeof a === 'object' && typeof b === 'object') { const o: Record<string, unknown> = {}; for (const k of Object.keys(b)) o[k] = k in (a as object) ? lerpObj((a as Record<string, unknown>)[k], (b as Record<string, unknown>)[k], u) : (b as Record<string, unknown>)[k]; return o as T; }
  return u < 0.5 ? a : b;
}
const fade = <X extends Flow | Spark>(xs: X[], k: number) => xs.map((x) => ({ ...x, intensity: x.intensity * k }));
export const insertSrc = (ins: Insert, fmt: Fmt) => fmt === '916' && ins.src916 ? ins.src916 : ins.src;
export function insertAt(t: number, avail: string[], fmt: Fmt) { return INSERTS.find((x) => avail.includes(insertSrc(x, fmt)) && t >= x.t0 && t < x.t1); }
export function frameAt(t: number, fmt: Fmt): Frame {
  const i = slotIndexAt(t), s = SLOTS[i];
  let f = build(i, t, fmt);
  if (i > 0 && t - s.t0 < BLEND_S) {
    const p = build(i - 1, t, fmt), u0 = (t - s.t0) / BLEND_S, u = u0 * u0 * (3 - 2 * u0);
    f = { ...f, cam: lerpObj(p.cam, f.cam, u), grade: lerpObj(p.grade, f.grade, u), flows: [...fade(p.flows, 1 - u), ...fade(f.flows, u)], sparks: [...fade(p.sparks, 1 - u), ...fade(f.sparks, u)], pulses: [...p.pulses, ...f.pulses] };
  }
  f.cam = camFor(fmt, f.cam);
  f.label = `${s.id}${f.built ? '' : ' [default]'} · ${sectionAt(t)} ${t.toFixed(2)}s · ${s.plan}`;
  return f;
}
export const slotLyric = (b: Beat) => { const m = /^([A-Za-z0-9]+)\/L(\d+)/.exec(String(b.at)); return m ? lineText(m[1], +m[2]) : ''; };
