// Post-chorus 1: po1_go .. po1_sky. Built by earth_sec_c1 (Sun Nov 8); polish round Nov 9 (earth_pol_c1): three shots instead of
// one slow push on a small disc, and the stars make each line's point.
//   "Ooh, off you go"         CUT: her limb fills the left of the frame like a wall, he is a small warm light out in the black;
//                             on "go" he streaks away, and the first stars turn to follow
//   "Ooh, off you fly"        CUT wider: the stars gather into a flock of birds in a V and fly after him
//   "You can have the stars"  the flock goes, and every star in the sky pours over to HIS side and is crammed there, a packed wall
//                             of stars (16:9: the right third; 9:16: the top); her side of the sky is left dark and empty
//   "I'll keep the sky"       CUT to her horizon: his side stays crammed with (his, warm) stars; her side fills with aurora
//                             (cut 2, Nov 9, the plan beat verbatim: "stars crammed on his side vs aurora on hers"; before, the stars left the frame)
// Story colour code: his spark and trail = warm; aurora, mist, motes = hers (teal/cyan with violet tops).
// inserts: none in this stretch (no ground-level plants / hill figure here).
import { PAL, Section, Builder, smooth, lerp, spark, flow, hits, C, clamp01 } from './api';
import { Box, Flow, Fmt, Spark } from '../types';
import { at, words } from '../anchor';
import { ASPECT, fitBox, starAttr } from '../stars';
import { RGB } from '../grade';
import { camC, hardCut, lonAt, ovr, withLook, OVR, ROOM0 } from './pre1';
import { NIGHT, T, heat, lineFlows, P2, chorus1 } from './chorus1';

const P = 'post1';
const TP = { l0: at(`${P}/L0`), go: at(`${P}/L0/w3`), l1: at(`${P}/L1`), fly: at(`${P}/L1/w3`), l2: at(`${P}/L2`), l3: at(`${P}/L3`), sky: at(`${P}/L3/w3`), end: at('verse2a/L0') };
const frac = (x: number) => x - Math.floor(x);
const mixC = (a: RGB, b: RGB, u: number): RGB => [lerp(a[0], b[0], u), lerp(a[1], b[1], u), lerp(a[2], b[2], u)];
// him leaving (the limb shot): a slow drift out in the black, then gone on "go" with a long warm streak (up and right)
const HIM0: Record<Fmt, P2> = { '169': [0.5, 0.02], '916': [0.1, 0.3] }, HIMDIR: Record<Fmt, P2> = { '169': [0.94, 0.34], '916': [0.42, 0.91] };
function him(t: number, fmt: Fmt): { sparks: Spark[]; flows: Flow[] } {
  const p0 = HIM0[fmt], dir = HIMDIR[fmt];
  const d = 0.03 * Math.max(0, t - TP.l0) + 5.2 * Math.pow(Math.max(0, t - (TP.go - 0.3)), 2);
  const pos = (dd: number): [number, number] => [p0[0] + dir[0] * dd, p0[1] + dir[1] * dd];
  const h = heat(t) * (1 - smooth(TP.l0, TP.go, t)), col = mixC(C.his, [1, 0.4, 0.14], h), p = pos(d), k = 1 - smooth(TP.go + 0.5, TP.go + 0.9, t);
  const st = smooth(TP.go - 0.3, TP.go + 0.1, t), trail = Array.from({ length: 12 }, (_, i) => pos(Math.max(0, d - 2.2 * st * (1 - i / 11))));
  return { sparks: [spark(p[0], p[1], { size: 15, color: col, intensity: 1.9 * k }), spark(p[0], p[1], { size: 64, color: col, intensity: 0.26 * k })],
    flows: [flow({ space: 'screen', pts: trail }, 1, { tail: 1, size: 13, color: PAL.ember, intensity: 2.8 * st * (1 - smooth(TP.go + 0.7, TP.go + 1.25, t)), count: 320 }),
      flow({ space: 'screen', pts: trail }, 1, { tail: 0.7, size: 36, color: PAL.ember, intensity: 0.6 * st * (1 - smooth(TP.go + 0.6, TP.go + 1.1, t)), count: 120 })] }; // (cut 2: a streak you can see at phone size)
}
// "off you fly": the stars as a flock of birds in a V, flying after him (9 birds, wings beating; the leader at the right).
// On "you can have the stars" the flock goes, and the rest of the sky after it (the stars that stayed home leave right to left).
const FLOCK: Record<Fmt, Box> = { '169': { cx: 0.62, cy: 0.3, w: 1.2, h: 1.12 }, '916': { cx: 0, cy: 0.42, w: 0.92, h: 0.8 } };
const NB = 9, FL_KEEP = 0.2;
const birdAt = (j: number, t: number, fmt: Fmt): { c: P2; span: number; ang: number } => { const b = fitBox(FLOCK[fmt], fmt), k = Math.ceil(j / 2), sg = j % 2 ? 1 : -1;
  const out = Math.max(0, t - (TP.l2 + 0.12 + 0.03 * k)), dx = 0.045 * (t - TP.l1) + 4.8 * out * out;
  return { c: [b.cx + (0.42 - 0.2 * k) * b.w + dx + 0.008 * Math.sin(t * 2.3 + j), b.cy + sg * 0.105 * k * b.h + 0.012 * Math.sin(t * 3.1 + j * 1.7) + 0.35 * out * out], span: 0.115 * b.w * (j === 0 ? 1.15 : 1), ang: 0.66 + 0.3 * Math.sin(t * 2 * Math.PI * 1.9 + j * 1.3) }; };
const wing = (B: { c: P2; span: number; ang: number }, sg: number, q: number): P2 => [B.c[0] + sg * q * B.span * Math.cos(B.ang * 0.7), B.c[1] + q * B.span * Math.sin(B.ang) * (1 - 0.3 * q * q)];
const flockFn = (i: number, t: number, home: [number, number], _n: number, fmt: Fmt): [number, number] => {
  const A = starAttr(), W = ASPECT[fmt];
  if (A.r3[i] < FL_KEEP) return home; void W;
  const j = i % NB, B = birdAt(j, t, fmt), q = Math.pow(frac(i * 0.61803398875), 0.8), sg = A.r2[i] < 0.5 ? -1 : 1, p = wing(B, sg, q);
  return [p[0] + (frac(i * 0.7548776662) - 0.5) * 0.011, p[1] + (frac(i * 0.37) - 0.5) * 0.011];
};
const flockLight = (t: number, fmt: Fmt): Flow[] => { const on = smooth(TP.l1 + 0.7, TP.l1 + 1.05, t) * (1 - smooth(TP.l2 + 0.05, TP.l2 + 0.4, t)), out: Flow[] = [], z = fmt === '916' ? 0.8 : 1; if (on <= 0.004) return out;
  for (let j = 0; j < NB; j++) { const B = birdAt(j, t, fmt); if (B.c[0] - B.span > ASPECT[fmt] + 0.05) continue;
    out.push(...lineFlows([1, 0.66, 0.33, 0, -0.33, -0.66, -1].map((v) => wing(B, Math.sign(v) || 1, Math.abs(v))), { color: PAL.filament, size: 7.5 * z, intensity: 0.7 * on, per: 150 })); } // (earth_cut2, gate 7: the stars that follow him are his gold)
  return out; };
// ---- "you can have the stars": every star crammed on his side (cut 2) ----
// The same push as the "space" room (r -> cbrt(r^3 + R^3)) from a centre far off HER side of the frame, so the whole sky is pressed
// against a slightly curved wall on his side: 16:9 the right third (the wall at x = CRAM_X), 9:16 the top (the wall at y = CRAM_Y).
// The cast (cramFn) and the deep field + mist (grade.room) use the same centre and radius, so they pile up together.
const CRAM_X = 0.66, CRAM_Y = 0.4;
const CRAM: Record<Fmt, { c: P2; R: number }> = { '169': { c: [-ASPECT['169'] - 1.2, -0.3], R: CRAM_X + ASPECT['169'] + 1.2 }, '916': { c: [0, -2.5], R: CRAM_Y + 2.5 } };
const cramFn = (_i: number, _t: number, home: [number, number], _n: number, fmt: Fmt): [number, number] => { const { c, R } = CRAM[fmt], dx = home[0] - c[0], dy = home[1] - c[1], r = Math.hypot(dx, dy) || 1e-6, r2 = Math.cbrt(r * r * r + R * R * R); return [c[0] + (dx / r) * r2, c[1] + (dy / r) * r2]; };
const cramK = (t: number) => Math.pow(clamp01((t - TP.l2 - 0.1) / 1.55), 1.7); // 0 -> 1 through "you can have the stars"; full before the cut
const cramGrade = (t: number, fmt: Fmt) => ({ room: (CRAM[fmt].R * cramK(t)) / ROOM0, roomX: CRAM[fmt].c[0], roomY: CRAM[fmt].c[1], roomKeep: 0, castWarm: 1, starWarm: smooth(TP.l2 + 0.15, TP.l2 + 1.3, t) }); // (earth_cut2: gold AS they cram, not after)
// him, small, in the middle of his pile
const PILE: Record<Fmt, P2> = { '169': [1.22, 0.42], '916': [0.2, 0.7] };
const pileHim = (t: number, fmt: Fmt): Spark[] => { const k = smooth(TP.l2 + 1.3, TP.l3 + 0.2, t), p = PILE[fmt], fl = 0.9 + 0.1 * Math.sin(t * 9); return k <= 0.004 ? [] : [spark(p[0], p[1], { size: 15, color: C.his, intensity: 2.0 * k * fl }), spark(p[0], p[1], { size: 70, color: PAL.ember, intensity: 0.4 * k })]; };
// her aurora: curtains of vertical rays standing on wavy lines above her horizon (teal at the foot, violet at the top),
// unrolling from her side toward his; light runs along them. k = 0..1 how much of it is up. (head just past the path end: the
// engine draws a flow's first particle 2.2x bigger, which would put a blob at every ray's foot)
function curtains(t: number, k: number, fmt: Fmt): Flow[] {
  if (k <= 0.001) return [];
  const A = ASPECT[fmt], cam = camC(t, fmt), wide = fmt === '169', out: Flow[] = [];
  const x0 = -A * 1.04, x1 = wide ? CRAM_X + 0.12 : A * 1.04, N = wide ? 150 : 84, sz = wide ? 1 : 0.8, iz = wide ? 1 : 1.9, hz = wide ? 1 : 0.62;
  const horizon = (x: number) => cam.y + Math.sqrt(Math.max(0, cam.r * cam.r - (x - cam.x) * (x - cam.x)));
  for (let i = 0; i < N; i++) {
    const h1 = frac(i * 0.61803398875), h2 = frac(i * 0.7548776662), band = i % 3;
    const u = (i + 0.7 * (h1 - 0.5)) / N, x = lerp(x0, x1, u);
    const yb = horizon(x) + 0.07 + 0.2 * band + 0.06 * Math.sin(x * (2.1 + band) + t * 0.5 + band * 2) + 0.025 * Math.sin(x * 7.3 + t * 0.9 + band);
    const H = hz * (0.3 + 0.3 * h2) * (0.75 + 0.25 * Math.sin(x * 3.1 - t * 0.7 + band * 1.3)) * (0.85 + 0.25 * band);
    const wave = 0.5 + 0.5 * Math.sin(x * 4.3 - t * 1.7 + band * 2.1 + 5 * h1);
    const grow = smooth(0, 1, k * 1.7 - u * 0.55 - band * 0.08), edge = wide ? smooth(x1, x1 - 0.5, x) : 1;
    const I = grow * (0.35 + 0.65 * wave) * edge;
    if (I < 0.01) continue;
    const lean = 0.05 * Math.sin(x * 1.7 + band), ray = 0.2 + 0.8 * h2 * h2; // big soft sprites that melt into a curtain; each ray its own strength
    out.push(flow({ space: 'screen', pts: [[x + lean, yb + H * grow], [x, yb]] }, 1.04, { tail: 1.04, size: 96 * sz, count: 20, intensity: 0.14 * iz * I * ray, color: band === 1 ? [0.12, 0.92, 0.72] : [0.1, 0.95, 0.8] })); // (earth_cut2 / fresh eyes: the green band read as a third hue; teal now)
    out.push(flow({ space: 'screen', pts: [[x + lean * 1.7, yb + H * grow * 1.75], [x + lean * 0.5, yb + H * grow * 0.4]] }, 1.06, { tail: 1.06, size: 120 * sz, count: 13, intensity: 0.1 * iz * I * ray, color: C.violet }));
  }
  return out;
}
const wt = (li: number) => words(P, li).map((w) => w[0]);
const builders: Record<string, Builder> = {
  // her limb, close: violet mist on the wall of her, his warm city lights dimming on her as he goes
  po1_go: (c) => { const h = him(c.t, c.fmt), k = smooth(TP.go, TP.go + 1.1, c.t); return { cam: ovr(c.t, c.fmt), motes: 'drift',
    grade: { ...NIGHT, glow: 1.45, mist: 1.4, aurora: 0.7, atmos: 1.5, rivers: 1.7, riverPulse: 1.5, forest: 1.5, motes: 0.7, room: 0, stars: lerp(1.0, 1.35, k), castWarm: smooth(TP.go + 0.05, TP.go + 1.0, c.t), deep: 1, galaxy: 1, hisWarm: lerp(0.4, 0.08, k), kick: 0.25 * hits(c.t, [TP.go], 0.5) },
    sparks: h.sparks, flows: h.flows }; },
  po1_fly: (c) => { const k = smooth(TP.l1 + 0.2, TP.l1 + 1.0, c.t); return { cam: ovr(c.t, c.fmt), motes: 'drift',
    grade: { ...NIGHT, glow: 1.4, mist: 0.8, aurora: 0.8, atmos: 1.4, room: 0, stars: lerp(1.3, 2.0, k), castWarm: 1, deep: lerp(1, 0.3, k), galaxy: lerp(1, 0.6, k), hisWarm: 0.08 },
    flows: flockLight(c.t, c.fmt) }; },
  // the cram: cast, deep field and mist are all pressed over to his side (cramFn + the room mechanism from a centre off her side)
  po1_stars: (c) => { const k = smooth(TP.l2, TP.l3, c.t); return { cam: ovr(c.t, c.fmt), motes: 'drift',
    grade: { ...NIGHT, glow: lerp(1.4, 1.3, k), mist: 0.8, aurora: 0.8, atmos: 1.4, stars: 2.0, deep: lerp(0.3, 0.85, k), galaxy: 0.6, hisWarm: 0.08, ...cramGrade(c.t, c.fmt) },
    sparks: pileHim(c.t, c.fmt), flows: flockLight(c.t, c.fmt) }; },
  po1_sky: (c) => { const k = smooth(TP.l3 - 0.05, TP.sky + 0.35, c.t); return { cam: ovr(c.t, c.fmt), motes: 'rise',
    grade: { ...NIGHT, glow: lerp(1.35, 1.7, k), mist: lerp(0.8, 1.3, k), aurora: lerp(0.6, 1.5, k), atmos: lerp(1.3, 1.6, k), motes: lerp(0.5, 1.0, k), stars: 2.0, deep: 0.85, galaxy: 0.6, bloom: 0.8, kick: 0.25 * hits(c.t, wt(3), 0.4), ...cramGrade(c.t, c.fmt) },
    sparks: pileHim(c.t, c.fmt), flows: curtains(c.t, k, c.fmt) }; },
};
withLook(builders);
hardCut(builders, 'po1_go', 'po1_fly', TP.l1);
hardCut(builders, 'po1_stars', 'po1_sky', TP.l3);
{ const a = chorus1.builders.c1_inch, b = builders.po1_go; chorus1.builders.c1_inch = (c) => (c.t >= TP.l0 ? b(c) : a(c)); } // the chorus's last slot hands over at the cut
// 9:16: the limb shot becomes a low horizon (a wall at the left would fill the narrow frame); the flock shot keeps her as a dome at the bottom
OVR.push({ a: TP.l0, b: TP.l1, f: (t) => ({ x: 0, y: lerp(-2.25, -2.3, clamp01((t - TP.l0) / (TP.l1 - TP.l0))), r: 2.42, roll: 0 }) });
OVR.push({ a: TP.l1, b: TP.l3, f: (t) => { const k = clamp01((t - TP.l1) / (TP.l3 - TP.l1)); return { x: 0, y: lerp(-1.5, -1.3, k), r: lerp(1.45, 1.1, k) }; } });
OVR.push({ a: TP.l3, b: TP.end, f: (_t, base) => { const r = base.r * 1.075; return { x: 0, y: (-0.42 - 0.62 * r) / 0.8, r }; } });
export const post1: Section = {
  name: 'post1',
  camera: [
    // "off you go": cut. Her limb is a wall down the left of the frame; he is out in the black
    { at: `${P}/L0`, cam: { x: -2.72, y: -0.2, r: 2.3, lon: lonAt(8, 72.5), lat: 24, roll: -78, sun: [0.5, 0.18, -0.85] }, ease: 'hold' },
    { at: `${P}/L1-0.02`, cam: { x: -2.82, r: 2.38 }, ease: 'linear' },
    // "off you fly": cut wider, she sits in the lower left corner and the sky is the stage; a slow pull back until the sky is empty
    { at: `${P}/L1`, cam: { x: -1.15, y: -0.95, r: 1.15, lon: lonAt(-45, 76), lat: 10, roll: -12 }, ease: 'hold' },
    { at: `${P}/L3-0.02`, cam: { x: -0.98, y: -0.74, r: 0.84 }, ease: 'linear' },
    // "I'll keep the sky": cut to her horizon, the sky above it all hers
    { at: `${P}/L3`, cam: { x: -0.22, y: -1.9, r: 1.8, lon: lonAt(15, 81.5), lat: 0, roll: 4, sun: [0.3, -0.5, -0.82] }, ease: 'hold' },
    { at: 'verse2a/L0-0.04', cam: { y: -1.97, r: 1.9 }, ease: 'linear' },
  ],
  stars: [
    { at: `${P}/L0/w3+0.05`, set: { kind: 'side', side: 1, cram: 0.62 }, dur: 1.3, straggle: 0.5, curve: 0.1, sweep: 0.2 },   // "go": the first stars turn to follow
    { at: `${P}/L1+0.12`, set: { kind: 'fn', fn: flockFn, front: true }, dur: 0.85, straggle: 0.3, curve: 0.25 },             // "off you fly": the flock
    { at: `${P}/L2+0.05`, set: { kind: 'fn', fn: cramFn, front: false }, dur: 1.6, straggle: 0.45, curve: 0.12 },                 // "you can have the stars": crammed on his side
    { at: 'verse2a/L0-0.25', set: { kind: 'sky' }, dur: 3.0, straggle: 0.6, curve: 0.08 },                              // released into verse 2
  ],
  builders,
};
// post2 (po2_go .. po2_sky) is built by earth_sec_c2 and lives in chorus2.ts with its chorus; this file is post 1's. KEEP this line.
export { post2 } from './chorus2';
