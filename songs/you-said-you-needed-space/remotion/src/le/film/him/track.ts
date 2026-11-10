// Where "him" is, per frame, read from the engine itself (earth_him_wire, Nov 9). The section builders draw him as a warm
// spark; the 3D him (living_earth/him3d, Blender) replaces that spark in the hero slots. This file finds his spark in a
// slot's own builder output (no section file is edited), gives its screen position under the engine's real (blended,
// re-framed) camera, and removes it from the frame when his 3D clip is present. Pure functions of time.
import { SLOTS, slotIndexAt, BLEND_S, frameAt } from '../engine';
import { SECTIONS, Builder, Ctx } from '../sections';
import { camAt, projOrbit } from '../camera';
import { GRADE_DEFAULT } from '../grade';
import { at } from '../anchor';
import { TIMING } from '../timing.gen';
import { Cam, Fmt, Frame, Spark } from '../types';
import { ASPECT } from '../stars';
import { himSpot } from '../sections/pre2';   // earth_c2_v2: his parking place beside the SOLD lot (the builder has other warm sparks too)

const BUILDERS: Record<string, Builder> = Object.assign({}, ...SECTIONS.map((s) => s.builders));
const word = (sid: string, li: number, wi: number) => TIMING.lines[sid]?.[li]?.words[wi]?.[0] ?? at(`${sid}/L${li}`);
// one slot's own builder output at any time (as engine.ts build(), which is not exported)
export function ownOut(i: number, t: number, fmt: Fmt) {
  const s = SLOTS[i], base: Frame = { t, cam: camAt(t), grade: { ...GRADE_DEFAULT }, flows: [], sparks: [], pulses: [] };
  const ctx: Ctx = { t, fmt, slot: s, lt: t - s.t0, u: Math.max(0, Math.min(1, (t - s.t0) / (s.t1 - s.t0))), dur: s.t1 - s.t0, base, at, word };
  const b = BUILDERS[s.id]; return b ? b(ctx) : {};
}
export const sparkXY = (s: Spark, cam: Cam): [number, number, boolean] => {
  if (s.orbit) { const p = projOrbit(cam, s.orbit[0], s.orbit[1], s.orbit[2], s.orbit[3]); return [p.x, p.y, p.visible]; }
  if (s.rel) return [cam.x + cam.r * s.rel[0], cam.y + cam.r * s.rel[1], true];
  return [s.x, s.y, true];
};
// ---- which spark is him, per hero slot. Default: the brightest small warm spark (his core); his halo is any warm spark on the same spot.
export type Rule = { maxSize?: number; minSize?: number; warm?: number; nth?: number; test?: (s: Spark, xy: [number, number], fmt: Fmt, t: number) => boolean };
const warmth = (s: Spark) => s.color[0] - s.color[2];
const P2: Rule = { test: (_s, xy, fmt, t) => { const p = himSpot(t, fmt).p; return Math.abs(xy[0] - p[0]) < 0.03 && Math.abs(xy[1] - p[1]) < 0.03; } };   // only the spark on his own spot
export const HIM_RULES: Record<string, Rule> = {
  co_count: {}, c1_sun: {}, c1_disappear: {}, c1_cool: {}, c1_atmos: {},
  c2_sun: {}, c2_disappear: {}, c2_cool: {}, c2_atmos: {},
  br_word: {}, br_learned: {}, br_moon: {}, br_sands: {}, br_ground: {},
  fc_hold: {}, fc_cool: {}, fc_atmos: {}, cd_10: {}, cd_7: {}, cd_5: {}, cd_disc: {}, p2_estate: P2, p2_wish: P2,
};
export const isHimSlot = (id: string) => id in HIM_RULES;
// a RUN = consecutive hero slots that are one continuous piece of his acting (one 3D clip); inside a run the engine's slot
// blends are ignored (he is one object), at its two ends the clip fades with the engine's blend weight
export const HIM_RUNS: Record<string, string[]> = {
  co_count: ['co_count'], c1_chase: ['c1_sun', 'c1_disappear'], c1_heat: ['c1_cool', 'c1_atmos'],
  c2: ['c2_sun', 'c2_disappear', 'c2_cool', 'c2_atmos'],
  br: ['br_word', 'br_learned', 'br_moon', 'br_sands', 'br_ground'],          // on past "the moon" until he is small (earth_c2_br's ask: the pull-back is one move)
  fc_hold: ['fc_hold'], fc_cool: ['fc_cool'],
  fc_end: ['fc_atmos', 'cd_10', 'cd_7', 'cd_5', 'cd_disc'],                   // one fixed place from the scarf to "disconnected" (earth_c2_fc's ask: no spark-and-back)
  p2_estate: ['p2_estate', 'p2_wish'],
};
export const runOf = (slot: string) => Object.keys(HIM_RUNS).find((r) => HIM_RUNS[r].includes(slot));
export type HimPick = { slot: string; i: number; x: number; y: number; size: number; intensity: number; color: [number, number, number]; visible: boolean };
export function pickHim(i: number, t: number, fmt: Fmt, cam: Cam): HimPick | null {
  const id = SLOTS[i].id, rule = HIM_RULES[id]; if (!rule) return null;
  const sp = (ownOut(i, t, fmt).sparks ?? []) as Spark[];
  const c = sp.map((s) => ({ s, xy: sparkXY(s, cam) })).filter(({ s, xy }) => warmth(s) >= (rule.warm ?? 0.12) && s.size <= (rule.maxSize ?? 45) && s.size >= (rule.minSize ?? 0)
    && (!rule.test || rule.test(s, [xy[0], xy[1]], fmt, t)));
  if (!c.length) return null;
  const best = rule.nth !== undefined ? c[Math.min(rule.nth, c.length - 1)] : c.reduce((a, b) => (b.s.intensity > a.s.intensity + 1e-9 ? b : a));   // intensity 0 still gives his place
  return { slot: id, i, x: best.xy[0], y: best.xy[1], size: best.s.size, intensity: best.s.intensity, color: best.s.color as [number, number, number], visible: best.xy[2] };
}
// him at time t: the slot we are in and, inside the engine's 0.45 s blend, the slot before (weights as the engine's cross-fade)
export type HimAt = HimPick & { w: number };
// A CUT: the sections make one by letting the outgoing slot's builder return the incoming slot's frame from the cut on
// (pre1.ts hardCut and its cousins), so both sides of the engine's blend are the same picture. Then there is no blend for him either.
const sameSparks = (a: Spark[], b: Spark[]) => a.length === b.length && JSON.stringify(a) === JSON.stringify(b);
export function himAt(t: number, fmt: Fmt, cam?: Cam): HimAt[] {
  const c = cam ?? frameAt(t, fmt).cam, i = slotIndexAt(t), s = SLOTS[i], out: HimAt[] = [];
  let u = 1; if (i > 0 && t - s.t0 < BLEND_S) { const u0 = (t - s.t0) / BLEND_S; u = u0 * u0 * (3 - 2 * u0); }
  if (u < 1 && sameSparks((ownOut(i - 1, t, fmt).sparks ?? []) as Spark[], (ownOut(i, t, fmt).sparks ?? []) as Spark[])) u = 1;   // a cut
  const a = pickHim(i, t, fmt, c); if (a) out.push({ ...a, w: u });
  if (u < 1) { const b = pickHim(i - 1, t, fmt, c); if (b) out.push({ ...b, w: 1 - u }); }
  return out;
}
// the frame with his spark(s) dimmed by how much of the 3D him is on screen: every warm spark sitting on his spot (core + halo).
// cover(slot) = 0..1 (0 = no 3D him there: the spark stays as the section drew it)
export function dimHim(f: Frame, t: number, fmt: Fmt, cover: (slot: string) => number): Frame {
  const hs = himAt(t, fmt, f.cam).map((h) => ({ ...h, c: cover(h.slot) })).filter((h) => h.c > 0); if (!hs.length) return f;
  const A = ASPECT[fmt], eps = 0.012 * Math.max(1, A);
  return { ...f, sparks: f.sparks.map((s) => { if (warmth(s) < 0.12) return s; const [x, y] = sparkXY(s, f.cam); const h = hs.find((q) => Math.abs(x - q.x) < eps && Math.abs(y - q.y) < eps);
    return h ? { ...s, intensity: s.intensity * (1 - h.c) } : s; }) };
}
// Is the picture on screen at t made by one of these slots' builders? Yes inside those slots; and also in the frame(s) just before
// the first of them when the outgoing builder has already handed over to it (the sections cut that way, sometimes on a frame-quantised
// time, so the slot index alone can be a frame off). Cameras cannot tell (they are functions of time on both sides of a cut): the
// builders' whole output is compared.
export function inShot(ids: string[], t: number, fmt: Fmt): boolean {
  const i = slotIndexAt(t); if (ids.includes(SLOTS[i].id)) return true;
  if (i + 1 < SLOTS.length && ids.includes(SLOTS[i + 1].id)) return JSON.stringify(ownOut(i, t, fmt)) === JSON.stringify(ownOut(i + 1, t, fmt));
  return false;
}
export const toPx = (x: number, y: number, fmt: Fmt, W: number, H: number): [number, number] => [((x / ASPECT[fmt]) + 1) / 2 * W, (1 - y) / 2 * H];
