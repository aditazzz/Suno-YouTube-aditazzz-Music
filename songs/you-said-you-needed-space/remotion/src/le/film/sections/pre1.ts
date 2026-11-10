// Pre-chorus 1: p1_holding .. p1_missing. Built by earth_sec_c1 (Sun Nov 8): the build into the first chorus.
//   A  "You said I'm holding you down"    CUT to her limb, close: his rocket strains straight up on a taut thread of its own exhaust
//   B  "That's just gravity, you know"     pull back: the thread bends over into an orbit; on "gravity" every star falls into orbit rings around her
//   C  "Up there you'll still be falling"  CUT low over her horizon: he falls past overhead, the star rings stream by
//   D  "Always missing me below"           CUT wide: he loops again and again, faster and lower; the rings tighten (the breath in before the chorus)
// The release (chorus1.ts): on "space" the rings burst outward and she blooms.
// Story colour code: his rocket/trail = warm white; everything of hers = cyan/violet.
// inserts: none in this stretch (no ground-level plants / hill figure here).
import { PAL, Section, Builder, smooth, spark, flow, C, lerp, clamp01, env, hits } from './api';
import { at, words } from '../anchor';
import { camAt, camFor } from '../camera';
import { Cam, Flow, Fmt, Spark } from '../types';
import { Grade } from '../grade';
import { LOOK } from './coldOpen';
import { spring } from './proof30';

const D = Math.PI / 180;
const frac = (x: number) => x - Math.floor(x);
export const T1 = {
  hold: at('pre1/L0'), down: at('pre1/L0/w5'), grav: at('pre1/L1'), gravity: at('pre1/L1/w2'), fall: at('pre1/L2'), falling: at('pre1/L2/w5'),
  miss: at('pre1/L3'), below: at('pre1/L3/w3'), c0: at('chorus1/L0'), space: at('chorus1/L0/w4'),
};
// her slow spin is added to lon by the engine: a key that should face `lon` at song time t asks for this
export const lonAt = (lon: number, t: number) => lon - 0.35 * t;

// ---- 9:16 reframes for this stretch (pre1 / chorus1 / post1) ----
// camera.ts camFor is the default 9:16 reframe. Where a shot needs its own 9:16 framing, a window here gives the camera
// (in the same pre-camFor units as the keys) for 9:16 only. Every builder of this stretch returns `cam: ovr(c.t, c.fmt)`, so
// both sides of a slot blend agree and a cut stays a cut; windows start and end on cuts ('hold' keys).
export type Win916 = { a: number; b: number; f: (t: number, base: Cam) => Partial<Cam> };
export const OVR: Win916[] = [];
export function ovr(t: number, fmt: Fmt): Partial<Cam> {
  if (fmt !== '916') return {};
  for (const w of OVR) if (t >= w.a && t < w.b) return w.f(t, camAt(t));
  return {};
}
// the final on-screen camera of this stretch (what the star `fn` sets and screen-space sparks are placed against)
export const camC = (t: number, fmt: Fmt): Cam => camFor(fmt, { ...camAt(t), ...ovr(t, fmt) });

// ---- the film's look ----
// earth_proof30 (the creative director's first 30 s) put the approved mockup look into the engine behind grade.lux: the lux planet
// (crisp veins + capillaries, real day side with the gold/rose dusk line, thin limb), the deep star field (42k stars) and the Milky
// Way mist. This stretch sits on the same base (coldOpen.ts LOOK) so the film does not change look at 0:35. LUX = false gives the
// engine's first look back (the builders' own numbers were first set on it).
export const LUX = true;
export const ROOM0 = 1.099;                                    // proof30 roomR() once the cold open's room has fully opened (R0 + 3 steps)
const TR = { l3: at('chorus1/L3'), l8: at('chorus1/L8'), sky: at('post1/L0') }; // (post 1 sets its own room per shot: post.ts)
// the room the DEEP stars and the mist keep around her (the cast keeps the same room: chorus1.ts roomFn): 1.5 x her radius from
// "space" (a spring, like the cold open's) until the rivers cut; 2.2 x from the second "space" until the post-chorus
export const roomGain = (t: number, fmt: Fmt): number => {
  const k = t < TR.l3 ? 1.5 * spring(t - (at('chorus1/L0/w4') - 0.06), 7.2, 0.6) : t >= TR.l8 && t < TR.sky ? 2.2 * smooth(TR.l8 + 0.15, TR.l8 + 1.7, t) : 0;
  return t < at('chorus1/L0/w4') - 0.06 ? 0 : (k * camC(t, fmt).r) / ROOM0;
};
export const lookBase = (t: number, fmt: Fmt): Partial<Grade> => { if (!LUX) return {}; const cam = camC(t, fmt);
  return { ...LOOK, seam: 0.14, hisWarm: 0.35, haloWide: 0.25, room: roomGain(t, fmt), roomX: cam.x, roomY: cam.y, roomKeep: t >= TR.l8 ? 0.16 : 0 }; }; // roomKeep: the second room is space, not a hole
// every builder of the stretch: the look underneath, the builder's own grade on top
export const withLook = (B: Record<string, Builder>) => { for (const id of Object.keys(B)) { const b = B[id]; B[id] = (c) => { const o = b(c); return { ...o, grade: { ...lookBase(c.t, c.fmt), ...(o.grade ?? {}) } }; }; } };

// Hard cuts stay hard: the engine cross-fades every slot change over 0.45 s (camera, grade, flows, sparks). Where the camera
// cuts, the outgoing slot's builder hands over to the incoming one from the cut on, so nothing of the old shot is drawn in
// the new one. (Builders of this stretch use only c.t and c.fmt, so they can be called for any time.)
export const hardCut = (B: Record<string, Builder>, from: string, to: string, tCut: number) => { const a = B[from], b = B[to]; B[from] = (c) => (c.t >= tCut ? b(c) : a(c)); };

// ---- his rocket: one trajectory for the whole pre-chorus, in her radii from her centre (screen axes) ----
// climb (A) -> gravity turn (B) -> orbit (C) -> faster and lower (D) -> flung out on "space" (chorus1.ts draws that part too)
const W0 = 117, ACC = 80, RHO = 1.315, Q = 0.95, NODE = -18; // orbit: deg/s, deg/s^2 after "missing", radius, squash, tilt of the ellipse
function polar(t: number): [number, number] {
  const { hold, down, grav, miss, space } = T1;
  const u = clamp01((t - hold) / (grav + 1.5 - hold));
  let rho = 1.012 + (RHO - 1.012) * (1 - Math.pow(1 - u, 2.0));
  rho -= 0.03 * env(t, down, 0.07, 0.45);                 // the tug on "down"
  rho -= 0.185 * smooth(miss, space, t);                   // "missing me below": every pass skims lower
  let th = 111;
  const tg = t - grav; if (tg > 0) th -= tg < 1.6 ? (W0 * tg * tg) / 3.2 : W0 * (tg - 0.8);
  const tm = Math.max(0, Math.min(t, space) - miss); th -= 0.5 * ACC * tm * tm;
  if (t > space) { const s = t - space, ws = ACC * (space - miss); rho += 9 * s * s; th -= (ws * s) / (1 + 3 * s); }
  return [rho, th];
}
export function rocketRel(t: number): [number, number] {
  const [rho, th] = polar(t), q = lerp(1, Q, smooth(1.04, 1.28, rho));
  const x = rho * Math.cos(th * D), y = q * rho * Math.sin(th * D), c = Math.cos(NODE * D), s = Math.sin(NODE * D);
  return [c * x - s * y, s * x + c * y];
}
// the rocket spark + its exhaust trail (the last `span` seconds of the trajectory). k = overall gain, big = close shot (bigger light)
export function rocket(t: number, o: { span?: number; k?: number; big?: number; count?: number } = {}): { sparks: Spark[]; flows: Flow[] } {
  const k = o.k ?? 1, big = o.big ?? 1, span = Math.min(o.span ?? 2.0, Math.max(0.04, t - T1.hold));
  const N = 96, tw = 0.012 * env(t, T1.down, 0.04, 0.7) * Math.sin((t - T1.down) * 2 * Math.PI * 7); // the thread twangs on "down"
  const strain = (1 - smooth(T1.grav, T1.grav + 0.8, t)) * (0.4 + 0.6 * smooth(T1.hold, T1.down, t));
  const jit: [number, number] = [0.006 * strain * Math.sin(t * 61), 0.004 * strain * Math.sin(t * 47 + 1)];
  const pts = Array.from({ length: N + 1 }, (_, i) => { const p = rocketRel(t - span * (1 - i / N)); const b = Math.sin((Math.PI * i) / N); return [p[0] + tw * b + jit[0] * (i / N), p[1] + jit[1] * (i / N)] as [number, number]; });
  const head = pts[N], fl = 0.85 + 0.15 * Math.sin(t * 38);
  return {
    sparks: [spark(0, 0, { rel: head, size: 13 * big, color: PAL.filament, intensity: 1.7 * k * fl }), spark(0, 0, { rel: head, size: 34 * big, color: PAL.ember, intensity: 0.5 * k })], // (earth_cut2, gate 7: Filament head, Ember trail)
    flows: [flow({ space: 'rel', pts }, 1, { tail: 1, size: 4.6 * big, color: PAL.ember, intensity: 1.45 * k, count: o.count ?? 520 }),
      flow({ space: 'rel', pts }, 1, { tail: 0.35, size: 9 * big, color: PAL.filament, intensity: 0.5 * k, count: 90 })],
  };
}

// ---- "that's just gravity": the cast falls into orbit rings around her (same tilted family of orbits as his rocket) ----
// 5 of 6 stars take a ring; inner rings turn faster (Kepler). From "missing" on they speed up and draw in toward her.
// (The deep star field is turned down while the cast performs, here and for the rack and the fan: most cast stars are as
// small as the deep ones, and a shape made of them only reads against a quiet sky.)
export const RINGS = 8;
export function ringStar(i: number, t: number, cam: Cam): [number, number] {
  const j = i % RINGS, h1 = frac(i * 0.61803398875), h2 = frac(i * 0.7548776662);
  const sq = lerp(1, 0.46, smooth(T1.miss, T1.space - 0.08, t));
  const a0 = 1.22 + 0.19 * j, a = 1.1 + (a0 - 1.1 + 0.07 * (h2 - 0.5)) * sq;
  const w = 38 * Math.pow(1.22 / a0, 1.5), tm = Math.max(0, Math.min(t, T1.space) - T1.miss);
  const ph = (h1 * 360 - w * (t - T1.gravity) - 0.5 * w * 0.5 * tm * tm) * D;
  const x = a * Math.cos(ph), y = Q * a * Math.sin(ph), c = Math.cos(NODE * D), s = Math.sin(NODE * D);
  return [cam.x + cam.r * (c * x - s * y), cam.y + cam.r * (s * x + c * y)];
}
const ringFn = (i: number, t: number, home: [number, number], _n: number, fmt: Fmt): [number, number] => (i % 6 === 0 ? home : ringStar(i, t, camC(t, fmt)));

const wt = (li: number) => words('pre1', li).map((w) => w[0]);
const SUN_P: [number, number, number] = [0.5, -0.38, -0.78]; // behind her, low: the warm of the sun stays out of these frames (the only warm light is his)
export const pre1: Section = {
  name: 'pre1',
  camera: [
    // A: cut on the line from the "ball of dirt" dot to her limb, close and low; a slow push while he strains
    { at: 'pre1/L0', cam: { x: 0, y: -1.72, r: 1.7, lon: lonAt(-92, 36), lat: -24, roll: 0, sun: SUN_P, par: [0, 0] }, ease: 'hold' },
    { at: 'pre1/L1', cam: { r: 1.8, y: -1.8 } },
    // B: the pull back that shows it was an orbit all along
    { at: 'pre1/L1+1.75', cam: { x: -0.12, y: -0.04, r: 0.46, lat: 12, roll: -8, par: [0, 0.35] } },
    // C: cut, low over her horizon; he falls past overhead
    { at: 'pre1/L2', cam: { x: 0.12, y: -2.25, r: 1.9, lon: lonAt(22, 41), lat: -22, roll: 3, par: [0, 0] }, ease: 'hold' },
    { at: 'pre1/L3-0.02', cam: { x: -0.1, y: -2.3, r: 1.98, par: [0.12, 0] }, ease: 'linear' },
    // D: cut wide; a slow push in while everything tightens
    { at: 'pre1/L3', cam: { x: 0, y: 0, r: 0.5, lon: lonAt(-30, 45), lat: 8, roll: -12, par: [0, 0] }, ease: 'hold' },
    { at: 'chorus1/L0/w4-0.08', cam: { r: 0.68, roll: -14 }, ease: 'in' },
  ],
  stars: [
    { at: 'pre1/L1/w2-0.2', set: { kind: 'fn', fn: ringFn, front: false }, dur: 1.7, straggle: 0.45, curve: 0.35 },
  ],
  builders: {
    p1_holding: (c) => ({ // close on her limb: violet mist, her rivers answer each word; he pulls, the thread holds
      // the hand-off from verse 1: the engine blends the "ball of dirt" dot (sunlit, verse1.ts) into this shot over 0.45 s, a crash
      // zoom. Her day side is faded out through that blend and comes back as the thin crescent, so the day/night line does not
      // sweep across her face mid-zoom.
      cam: ovr(c.t, c.fmt), grade: { glow: 1.15, violet: 1, mist: 1.3, aurora: 0.35, atmos: 1.3, rivers: 1.3, kick: 0.25 * hits(c.t, wt(0), 0.3), motes: 0.5 }, // (cut 2: verse1.ts hands over at the cut now, so the old day-side fade through the crash zoom is gone)
      ...rocket(c.t, { span: 3, big: 1.5 }),
    }),
    p1_gravity: (c) => { const k = smooth(T1.grav, T1.grav + 1.75, c.t); return { // one move, no cut: mist thins as we pull back, the stars fall in
      cam: ovr(c.t, c.fmt), grade: { glow: 1.15, violet: 1, mist: lerp(1.3, 0.5, k), aurora: lerp(0.35, 0.15, k), atmos: 1.3, rivers: 1.3, stars: lerp(1, 1.9, k), deep: lerp(1, 0.07, smooth(T1.gravity - 0.3, T1.gravity + 1.3, c.t)), kick: 0.3 * hits(c.t, [T1.gravity], 0.5), motes: lerp(0.5, 0.3, k) },
      ...rocket(c.t, { span: 2.4, big: lerp(1.5, 0.9, k) }),
    }; },
    p1_falling: (c) => ({
      cam: ovr(c.t, c.fmt), grade: { glow: 1.45, violet: 1, mist: 1.2, aurora: 0.7, atmos: 1.4, rivers: 1.5, herCyan: 0.8, stars: 1.7, deep: 0.55, kick: 0.3 * hits(c.t, [T1.falling], 0.5), motes: 0.5 },
      ...rocket(c.t, { span: 1.7, big: 2.3, count: 900 }),
    }),
    p1_missing: (c) => { const k = smooth(T1.miss, T1.space, c.t); return { // again and again: the trail winds into a spiral, the world holds its breath
      cam: ovr(c.t, c.fmt), grade: { glow: lerp(1.15, 0.85, k), violet: 1, mist: 0.5, atmos: lerp(1.3, 1.0, k), rivers: 1.3, stars: lerp(1.9, 2.1, k), deep: 0.07, kick: 0.22 * hits(c.t, wt(3), 0.35), motes: 0.3 },
      ...rocket(c.t, { span: lerp(2.0, 2.6, k), big: 1.25, count: 2200 }),
    }; },
  },
};
withLook(pre1.builders);
hardCut(pre1.builders, 'p1_gravity', 'p1_falling', T1.fall);
hardCut(pre1.builders, 'p1_falling', 'p1_missing', T1.miss);
// 9:16: the fly-by shot keeps her horizon a third of the way up the tall frame
OVR.push({ a: T1.fall, b: T1.miss, f: (t) => ({ y: lerp(-1.92, -1.97, clamp01((t - T1.fall) / (T1.miss - T1.fall))) }) });
