// Chorus 2 + post-chorus 2 (c2_space .. po2_sky, slots 43-56). Built by earth_sec_c2, Sun Nov 8 2026.
// Shares only the line-of-light drawing primitive with chorus 1. The shots and animation are independent.
//
// THE IDEA (creative-director call): chorus 1 is the release, she blooms and he is the joke. Chorus 2 is the same lines after
// verse 2, when his lights are already off on her: darker, closer, lower, cut on the line downbeats, his warm tech smaller each
// line until it burns out on "atmosphere". The payoff is "needed": on line 9 SHE clears the whole sky around herself (the cold
// open's stars-back-away move, now hers and much bigger) and blooms alone in clean dark. Post 2 (rebuilt in the polish, see
// POLISH below): the stars she sent away fly through her clean sky to him and pack into one small knot; her aurora closes into a
// crown around her pole and stands up on "sky".
//
// Seven framings, none of them chorus 1's (centred wide / rack beside her / Amazon close / centred terminator):
//   L0 space      CUT  low horizon over Europe's night, fireworks embers still falling
//   L1-2 stars/GPUs    the horizon drops, the sky becomes a ROW of racks; chips rise into them; on "go" the racks roll out like luggage
//   L3 rivers     CUT  straight down on Africa: Nile, Congo, Niger all running at once
//   L4-5 sun/disappear CUT  her whole face at the dusk line: he runs across her dark side toward a crescent of real daylight, is lost in the glare; the crescent thins to dark
//   L6 cool       CUT  dead-centre vertical frame: she is a small cool disc at the bottom, he is one hot point straight above, far up
//   L7 atmosphere CUT  her limb close, air and aurora wrapping her; his red spark burns out on the word
//   L8 space      the CRANE: up and over her northern limb (the aurora we were just under), landing on "space" above Asia;
//                 the stars step back from her
//   L9 needed     she takes the whole sky (every star out of frame), her light goes out in a ring, a thin green ring starts
//                 to draw itself around her pole
// POLISH (earth_pol_c2, Mon Nov 9): (1) every slot sits on the approved lux look (coldOpen.ts LOOK underneath, `deep`/`galaxy`
// turned down where the star drawings must read); (2) "rivers" is framed wider and keeps turning (the 4k river map is soft at 1:1
// past r ~2); (3) the tail (L8 .. "I'll keep the sky") is its own thing now, ONE function of time (`tail`), so the engine's slot
// blend always blends a frame with itself. Chorus 1's tail is a small full disc, a dot, a wall of stars at the side and a cut to a
// horizon. This one is seen from above her north: after "needed" the stars she pushed away fly THROUGH her clean sky to him and
// pack into one small knot ("you can have the stars"), while her aurora closes into a crown around her pole, low at first, a
// step taller on each "Ooh", full height on "sky". The bridge then cuts to one warm star: the knot is that star.
// 9:16 has its own framing per shot (V below, final 9:16 screen units), because the engine's automatic reframe pushes low
// horizons and side-offset frames under the bottom 30% UI zone.
// Old versions: build/le_pol_c2/old/.
// INSERTS: none in this stretch. PLACEHOLDER (her Nov 9 mark: close surface approved): c2_rivers could take a surface2 plate of
// the Congo basin (pitch_mockups/surface2 render.night_plate) at the L3 camera below; the engine version holds without it.
import { PAL, Section, Builder, Ctx, Out, hits, env, smooth, spark, flow, C, RIVERS, lerp, clamp01, reverse } from './api';
import { CamKey, SPIN_DEG_S, camAt, camFor, projGeo } from '../camera';
import { Cam, Flow, Fmt, Spark, StarKey } from '../types';
import { Anchor, at, words } from '../anchor';
import { ASPECT, starAttr } from '../stars';
import { Grade, RGB } from '../grade';
import { LOOK } from './coldOpen'; // read only: the approved look (lux planet, deep stars, Milky Way mist)
import { spring, CREEP, SPACE } from './proof30'; // read only
import { lineFlows, P2 } from './chorus1';
import { bridge } from './bridge'; // read only: its first builder, for the cut at the seam

const S = 'chorus2', PO = 'post2';
const wt = (li: number) => words(S, li).map((w) => w[0]);
const mixC = (a: RGB, b: RGB, u: number): RGB => [lerp(a[0], b[0], u), lerp(a[1], b[1], u), lerp(a[2], b[2], u)];
const WARM: RGB = PAL.filament, HOT: RGB = [1.0, 0.42, 0.12], // (earth_cut2, gate 7: his spark Filament, his chips Ember; was cream)
  AUR_G: RGB = [0.1, 1.0, 0.5], AUR_V: RGB = [0.6, 0.2, 1.0];
const D = Math.PI / 180;
// the engine adds her slow spin on top of the keys; LON(deg, anchor) = the key value that faces `deg` at that moment
const LON = (deg: number, a: Anchor) => deg - SPIN_DEG_S * at(a);

// ---- the shots: one list, both formats. c = the 16:9 camera key; v = the 9:16 frame (her disk in final 9:16 screen units) ----
type V = { x: number; y: number; r: number };
type Shot = { at: Anchor; ease?: CamKey['ease']; c: Partial<Cam>; v: V };
const SHOTS: Shot[] = [
  // L0 "You said you needed space": CUT on the downbeat. Low horizon, Europe's night at the limb, slow push.
  { at: `${S}/L0`, ease: 'hold', c: { x: 0.25, y: -2.3, r: 2.4, lon: LON(18, `${S}/L0`), lat: -30, roll: 5, sun: [0.3, -0.75, -0.6], par: [0.5, 0.2] }, v: { x: 0.08, y: -1.27, r: 1.3 } },
  { at: `${S}/L1`, ease: 'linear', c: { y: -2.38, r: 2.5 }, v: { x: 0.08, y: -1.32, r: 1.36 } },
  // L1 "meant the stars": the horizon drops away and the sky opens for the racks; lands on "meant"
  { at: `${S}/L1/w3`, ease: 'smooth', c: { x: 0, y: -3.42, r: 3.0, lat: -34, roll: 2 }, v: { x: 0, y: -1.74, r: 1.6 } },
  { at: `${S}/L3-0.03`, ease: 'linear', c: { y: -3.5, r: 3.05 }, v: { x: 0, y: -1.78, r: 1.62 } },
  // L3 "rivers left to flow": CUT, straight down on Africa, low: the frame is nearly all surface, a sliver of her limb at one
  // edge (cut-1 note: too many full-globe shots). Wider than the first cut (r 2.5-2.95 showed the 4k river map soft at 1:1; tested
  // tonight: the lux capillaries hold up to r ~2.2, past that the big veins go soft again) and never still: a steady push and turn
  { at: `${S}/L3`, ease: 'hold', c: { x: 0.16, y: -0.1, r: 1.85, lon: LON(20, `${S}/L3`), lat: 5, roll: 20, sun: [0.6, 0.3, -0.74], par: [-0.3, 0.1] }, v: { x: 0.02, y: 0.1, r: 1.2 } },
  { at: `${S}/L4-0.03`, ease: 'linear', c: { x: 0.12, y: -0.08, r: 2.2, lat: 8, roll: 9 }, v: { x: 0, y: 0.12, r: 1.42 } },
  // L4-5 "chase the sun / disappear": CUT to her whole face at the dusk line (chorus 1 plays this on a horizon): the night side
  // is hers, a crescent of real daylight on the right. He runs across her dark face toward it; she keeps turning, the crescent thins
  { at: `${S}/L4`, ease: 'hold', c: { x: -0.3, y: -0.15, r: 1.3, lon: LON(-62, `${S}/L4`), lat: 8, roll: -10, sun: [0.85, 0.12, -0.5], par: [0.2, -0.2] }, v: { x: -0.22, y: -0.08, r: 0.74 } },
  { at: `${S}/L5`, ease: 'linear', c: { x: -0.34, r: 1.36, sun: [0.8, 0.12, -0.62] }, v: { x: -0.23, y: -0.08, r: 0.77 } },
  { at: `${S}/L6-0.03`, ease: 'linear', c: { x: -0.38, r: 1.42, sun: [0.55, 0.1, -0.85] }, v: { x: -0.24, y: -0.08, r: 0.8 } },
  // L6 "who's gonna cool you down up there": CUT to a dead-centre, vertical frame (chorus 1's two-shot is a diagonal with her big):
  // she is a small cool disc at the bottom, he is one hot point straight above her, a long way up
  { at: `${S}/L6`, ease: 'hold', c: { x: 0, y: -0.62, r: 0.22, lon: LON(10, `${S}/L6`), lat: 15, roll: -12, sun: [0.85, 0.25, -0.46], par: [0, 0] }, v: { x: 0, y: -0.3, r: 0.15 } },
  { at: `${S}/L7-0.03`, ease: 'linear', c: { y: -0.64, r: 0.2 }, v: { x: 0, y: -0.31, r: 0.14 } },
  // L7 "no atmosphere": CUT to her limb, close: the air and the aurora
  { at: `${S}/L7`, ease: 'hold', c: { x: -0.5, y: -3.3, r: 3.2, lon: LON(100, `${S}/L7`), lat: -28, roll: 0, sun: [-0.3, -0.8, -0.5], par: [-0.4, 0.3] }, v: { x: -0.15, y: -1.87, r: 1.7 } },
  { at: `${S}/L8`, ease: 'hold', c: { x: -0.2, y: -0.99, r: 1.18, lat: -8, roll: -2 }, v: { x: -0.07, y: -0.60, r: 0.78 } },
  // ---- THE TAIL (see `tail`): one move from here to the bridge's cut ----
  // L8 "you said you needed space" (2): the crane. Up and over her northern limb, pulling back, landing on "space": she is a
  // dome seen from above her north (Asia under us, Siberia's rivers running up to the pole), the whole sky over her
  { at: `${S}/L8/w4`, ease: 'smooth', c: { x: 0, y: -0.5, r: 0.6, lon: LON(96, `${S}/L8/w4`), lat: 33, roll: -5, sun: [-0.25, -0.62, -0.74], par: [0, 0.25] }, v: { x: 0, y: -0.3, r: 0.34 } },
  { at: `${S}/L9/w3-0.1`, ease: 'linear', c: { y: -0.51, r: 0.63 }, v: { x: 0, y: -0.3, r: 0.355 } },
  // L9 "turns out I NEEDED some too": on the word she swells toward us, then a slow creep
  { at: `${S}/L9/w3+0.45`, ease: 'out', c: { y: -0.56, r: 0.8, lat: 34, par: [0, 0] }, v: { x: 0, y: -0.33, r: 0.45 } },
  { at: `${PO}/L0`, ease: 'linear', c: { y: -0.6, r: 0.86 }, v: { x: 0, y: -0.35, r: 0.48 } },
  // The post now lands on the crown on "fly" and holds for the stars and the aurora's own movement on "sky".
  { at: `${PO}/L1/w3+0.22`, ease: 'smooth', c: { x: -0.3, y: -1.3, r: 1.75, lat: 31, roll: -4 }, v: { x: -0.02, y: -0.75, r: 0.95 } },
];
const camKeys: CamKey[] = SHOTS.map((s) => ({ at: s.at, cam: s.c, ease: s.ease }));
// 9:16: evaluate v with the same timing/eases, then undo camera.ts camFor so the engine's reframe lands exactly on v
const EASE = { smooth: (u: number) => u * u * (3 - 2 * u), linear: (u: number) => u, hold: () => 0, out: (u: number) => 1 - (1 - u) ** 3, in: (u: number) => u * u * u };
const VK = SHOTS.map((s) => ({ t: at(s.at), v: s.v, ease: s.ease ?? 'smooth' }));
const T0 = VK[0].t, T_END = at('bridgeA/L0');
function vAt(t: number): V {
  let i = 0; while (i + 1 < VK.length && VK[i + 1].t <= t) i++;
  if (i + 1 >= VK.length || t <= VK[0].t) return VK[i].v;
  const a = VK[i], b = VK[i + 1], u = EASE[b.ease](clamp01((t - a.t) / Math.max(1e-3, b.t - a.t)));
  return { x: lerp(a.v.x, b.v.x, u), y: lerp(a.v.y, b.v.y, u), r: Math.exp(lerp(Math.log(a.v.r), Math.log(b.v.r), u)) };
}
const K916 = ASPECT['916'] / ASPECT['169'];
function unCamFor(v: V): V { // the 16:9-space camera that camFor('916') maps onto v
  const ax = Math.abs(v.x), sg = v.x < 0 ? -1 : 1;
  if (ax < 1e-5) return { x: 0, y: v.y / 0.8, r: v.r / 0.62 };
  if (ax >= 0.6 * K916 * 0.4) return { x: v.x / (K916 * 0.4), y: (v.y + 0.5) / 0.8, r: v.r / 0.62 };
  const x = (1 - Math.sqrt(Math.max(0, 1 - 4 * ax / K916))) / 2; // x k (1 - x) = |v.x| for x < 0.6
  return { x: sg * x, y: (v.y + 0.5 * (x / 0.6)) / 0.8, r: v.r / 0.62 };
}
// her disk on screen in this format, as the frame will show it (for things I place in screen space)
function disk(c: Ctx): V {
  if (c.fmt === '169') return { x: c.base.cam.x, y: c.base.cam.y, r: c.base.cam.r };
  const f = camFor('916', { ...c.base.cam, ...(cam916(c) ?? {}) });
  return { x: f.x, y: f.y, r: f.r };
}
function cam916(c: Ctx): Partial<Cam> | undefined {
  if (c.fmt !== '916' || c.t < T0 || c.t >= T_END) return undefined; // my range only; it starts and ends on cuts
  return unCamFor(vAt(c.t));
}
// the camera as the frame shows it, per format, for any time in my range (a function of time only: the star function uses it too)
const camOf = (t: number, fmt: Fmt): Cam => (fmt === '169' ? camAt(t) : camFor('916', { ...camAt(t), ...unCamFor(vAt(t)) }));
// every builder of mine goes through this: same camera function on both sides of a slot seam, so cuts stay cuts
// ... and sits on the film's look: LUXBASE underneath, the builder's own grade on top
const wrap = (b: Builder): Builder => (c) => { const o0 = b(c), o = c.t < T_END ? { ...o0, grade: { ...LUXBASE, ...(o0.grade ?? {}) } } : o0, k = cam916(c); return k ? { ...o, cam: { ...(o.cam ?? {}), ...k } } : o; };
const wrapAll = (m: Record<string, Builder>) => Object.fromEntries(Object.entries(m).map(([k, b]) => [k, wrap(b)]));
// Hard cuts stay hard (same convention as pre1.ts hardCut): the engine cross-fades every slot change over 0.45 s (grade, flows,
// sparks). Where the camera cuts, the outgoing slot's builder hands over to the incoming one from the cut on, with the incoming
// slot's own clock, so nothing of the old shot is drawn into the new one.
const reslot = (c: Ctx, t0: number, t1: number): Ctx => ({ ...c, slot: { ...c.slot, t0, t1 }, lt: c.t - t0, u: clamp01((c.t - t0) / (t1 - t0)), dur: t1 - t0 });
const hardCut = (B: Record<string, Builder>, from: string, to: string, cut: Anchor, next: Anchor) => { const a = B[from], b = B[to], t0 = at(cut), t1 = at(next); B[from] = (c) => (c.t >= t0 ? b(reslot(c, t0, t1)) : a(c)); };

// ---- the look of this chorus: after verse 2 his warm lights are off on her; warm only lives in the sky (racks, chips, his satellite) ----
const NIGHT = { hisOff: 0.88, hisWarm: 0.5, herCyan: 0.85, violet: 0.9, mist: 0.42 };
// the approved look under every slot (as pre1.ts lookBase does for chorus 1): the lux planet, the deep star field and the Milky
// Way mist; her night bloom levels from chorus 1 (forests, rivers, motes) so the two choruses are the same world
const LUXBASE: Partial<Grade> = { ...LOOK, room: 0, roomX: 0, roomY: 0, seam: 0.14, haloWide: 0.2, forest: 1.3, rivers: 1.4, riverPulse: 1.1, ocean: 0.6, motes: 0.5, bloom: 0.62 };

// ---- "meant the stars": a ROW of racks across the sky (chorus 1 has one rack beside her). A function set, so each format gets its own layout ----
type Lay = { n: number; x0: number; x1: number; y0: number; y1: number; gap: number; out: number };
const RACKS: Record<Fmt, Lay> = { '169': { n: 3, x0: -1.5, x1: 1.5, y0: -0.2, y1: 0.86, gap: 0.24, out: 4.8 }, '916': { n: 2, x0: -0.45, x1: 0.45, y0: 0.06, y1: 0.7, gap: 0.1, out: 1.8 } };
const BARS = Array.from({ length: 7 }, (_, j) => 0.115 + j * 0.128);
// rack unit space (u right, v up): the frame, 7 server units as bars, a status LED per unit. [u0, v0, u1, v1, weight]
const SEGS: [number, number, number, number, number][] = [
  [0, 0, 1, 0, 1], [1, 0, 1, 1, 1.25], [1, 1, 0, 1, 1], [0, 1, 0, 0, 1.25],
  ...BARS.map((v): [number, number, number, number, number] => [0.1, v, 0.72, v, 0.62]),
  ...BARS.map((v): [number, number, number, number, number] => [0.83, v, 0.9, v, 0.1]),
];
const SEG_TOT = SEGS.reduce((a, s) => a + s[4], 0);
const rackRect = (fmt: Fmt, j: number) => { const L = RACKS[fmt], w = (L.x1 - L.x0 - L.gap * (L.n - 1)) / L.n; return { x: L.x0 + j * (w + L.gap), y: L.y0, w, h: L.y1 - L.y0 }; };
const T_OUT = at(`${S}/L2/w4`) - 0.14; // Anticipate "go" and clear the frame before the cut, rightmost first.
const rackOut = (fmt: Fmt, j: number, t: number) => { const L = RACKS[fmt], k = clamp01((t - T_OUT - (L.n - 1 - j) * 0.055) / 0.38); return L.out * k * k * k; };
const rackFn = (i: number, t: number, home: [number, number], _n: number, fmt: Fmt): [number, number] => {
  const SA = starAttr(); if (SA.r3[i] < 0.1) return home; // a tenth of the sky stays sky
  const L = RACKS[fmt], A = ASPECT[fmt];
  const j = Math.min(L.n - 1, Math.max(0, Math.floor(((home[0] / (A * 1.06) + 1) / 2) * L.n))); // nearest rack: no crossing paths
  let u = SA.r2[i] * SEG_TOT, k = 0; while (k < SEGS.length - 1 && u > SEGS[k][4]) { u -= SEGS[k][4]; k++; }
  const s = SEGS[k], f = SA.r1[i], R = rackRect(fmt, j), h = ((i * 7919) % 97) / 97 - 0.5, jit = h * 0.006;
  const slab = k >= 4 ? h * 0.05 * R.h : 0; // a unit / its LED has height
  return [R.x + (s[0] + (s[2] - s[0]) * f) * R.w + jit + rackOut(fmt, j, t), R.y + (s[1] + (s[3] - s[1]) * f) * R.h - jit + slab];
};
const starKeys: StarKey[] = [
  // (pre2's own `sky` key at chorus2/L0+0.6 brings the fireworks home over c2_space; these start after it)
  { at: `${S}/L1/w3-0.05`, set: { kind: 'fn', fn: rackFn, front: true }, dur: 0.5, straggle: 0.3, curve: 0.12 }, // landed on "stars"
  { at: `${S}/L3+0.02`, set: { kind: 'sky' }, dur: 1.5, straggle: 0.4 },
  { at: `${S}/L8/w4-0.1`, set: { kind: 'fn', fn: (i, t, h, n, f) => tailStar(i, t, h, n, f), front: false }, dur: 0.12, straggle: 0 },   // the whole tail: step back, leave, fly to him (tailStar)
  { at: 'bridgeA/L0-0.04', set: { kind: 'sky' }, dur: 1.6, straggle: 0.5 }, // released at the bridge's cut ("I'll still point you out at night")
];

// ---- pieces ----
// chips rising off her into the racks: dashed warm packets, two streams per rack, from just under the horizon
function chipStreams(c: Ctx): Flow[] {
  const d = disk(c), L = RACKS[c.fmt], out: Flow[] = [];
  const limb = (x: number) => d.y + Math.sqrt(Math.max(0, d.r * d.r - (x - d.x) * (x - d.x)));
  const t2 = at(`${S}/L2`), gone = 1 - smooth(T_OUT - 0.12, T_OUT + 0.1, c.t);
  for (let j = 0; j < L.n; j++) for (let s = 0; s < 2; s++) {
    const R = rackRect(c.fmt, j), xs = R.x + R.w * (s ? 0.82 : 0.12), xe = R.x + R.w * (s ? 0.56 : 0.3), y0 = limb(xs) - 0.05;
    const head = Math.max(0, c.t - t2 + 0.3 - 0.1 * j - 0.17 * s) * 0.95;
    out.push(flow({ space: 'screen', pts: [[xs, y0], [xs, y0 + (R.y - y0) * 0.5], [xe, R.y], [xe, R.y + R.h * BARS[2 + s * 3]]] }, head,
      { tail: 3, dash: 22, size: 10, color: PAL.ember, intensity: 3.0 * gone, count: 300 }));
  }
  return out;
}
// Turn the star silhouette into hardware. A GPU case gets a handle and wheels as it leaves the rack.
function rackHardware(c: Ctx): { sparks: Spark[]; flows: Flow[] } {
  const on = smooth(at(`${S}/L1/w3`) + 0.14, at(`${S}/L1/w5`), c.t);
  const pack = at(`${S}/L2/w2`), sparks: Spark[] = [], flows: Flow[] = [];
  const z = c.fmt === '916' ? 0.78 : 1;
  const n = RACKS[c.fmt].n;
  for (let j = 0; j < n; j++) {
    const R = rackRect(c.fmt, j), dx = rackOut(c.fmt, j, c.t);
    if (R.x + dx > ASPECT[c.fmt] + 0.1) continue;
    const p = (u: number, v: number): P2 => [R.x + u * R.w + dx, R.y + v * R.h];
    const outline = (a: number, b: number, x: number, y: number): P2[] => [p(a, b), p(x, b), p(x, y), p(a, y), p(a, b)];
    flows.push(...lineFlows(outline(0, 0, 1, 1), { color: PAL.ember, size: 8 * z, intensity: 0.75 * on }));
    for (const v of [0.20, 0.43, 0.66]) {
      flows.push(...lineFlows([p(0.09, v), p(0.91, v)], { color: PAL.ember, size: 7 * z, intensity: 0.64 * on }));
      const [x, y] = p(0.87, v + 0.07);
      sparks.push(spark(x, y, { size: 12 * z, color: WARM, intensity: 1.1 * on }));
    }
    const lift = smooth(pack + j * 0.06, pack + 0.4 + j * 0.06, c.t);
    const handle = smooth(pack + 0.05, pack + 0.32, c.t);
    const u = 0.2 + 0.24 * lift;
    flows.push(...lineFlows(outline(u, 0.57, u + 0.42, 0.80), { color: WARM, size: 10 * z, intensity: 1.15 * on * lift }));
    flows.push(...lineFlows([p(u + 0.12, 0.80), p(u + 0.12, 0.80 + 0.085 * handle), p(u + 0.30, 0.80 + 0.085 * handle), p(u + 0.30, 0.80)], { color: WARM, size: 8 * z, intensity: on * lift }));
    for (const wheel of [0.10, 0.32]) {
      const [x, y] = p(u + wheel, 0.55);
      sparks.push(spark(x, y, { size: 14 * z, color: WARM, intensity: 1.15 * on * lift }));
    }
  }
  return { sparks, flows };
}

// positions around her edge (angle from the top of her disk, degrees; alt in her radii)
const onLimb = (deg: number, alt: number): [number, number] => [alt * Math.sin(deg * D), alt * Math.cos(deg * D)];
// Chase above the terminator. Keep the full wings in frame while the character runs toward the lit edge.
const CHASE: Record<Fmt, [P2, P2, P2]> = {
  '169': [[-1.23, 0.42], [-0.1, 0.57], [1.18, 0.28]],
  '916': [[-0.23, 0.27], [0.02, 0.39], [0.34, 0.24]],
};
function chase(c: Ctx): { sparks: Spark[]; flows: Flow[] } {
  const start = at(`${S}/L4`), disappear = at(`${S}/L5/w2`);
  const [p0, p1, p2] = CHASE[c.fmt], u = smooth(start + 0.26, disappear + 0.22, c.t);
  const place = (u: number): P2 => [(1 - u) ** 2 * p0[0] + 2 * u * (1 - u) * p1[0] + u ** 2 * p2[0], (1 - u) ** 2 * p0[1] + 2 * u * (1 - u) * p1[1] + u ** 2 * p2[1]];
  const [x, y] = place(u);
  const k = 1 - smooth(disappear + 0.05, disappear + 0.6, c.t);
  const glare = (0.36 + 0.34 * env(c.t, disappear, 0.20, 0.48)) * (1 - smooth(disappear + 0.4, disappear + 1.25, c.t));
  return {
    sparks: [spark(x, y, { size: lerp(15, 7, u), color: WARM, intensity: 2.2 * k }),
      spark(p2[0], p2[1], { size: 170, color: PAL.filament, intensity: 0.8 * glare }),
      spark(p2[0], p2[1], { size: 400, color: PAL.ember, intensity: 0.22 * glare })],
    flows: [flow({ space: 'screen', pts: Array.from({ length: 16 }, (_, i) => place(i / 15)) }, u,
      { tail: 0.22, size: 6, color: PAL.ember, intensity: 1.4 * k * smooth(0, 0.12, u), count: 110 })],
  };
}

const HIM_COOL: Record<Fmt, P2> = { '169': [-0.22, 0.37], '916': [-0.15, 0.36] };
const HIM_ATMOS: Record<Fmt, P2> = { '169': [0.74, 0.37], '916': [0.02, 0.33] };
function thermometer(c: Ctx, heat: number): Flow[] {
  const [x, y] = c.fmt === '916' ? [0.29, 0.28] : [0.43, 0.31];
  const z = c.fmt === '916' ? 0.78 : 1;
  const p = (u: number, v: number): P2 => [x + z * u, y + z * v];
  const on = smooth(at(`${S}/L6/w2`) - 0.10, at(`${S}/L6/w2`) + 0.14, c.t);
  const bulb = Array.from({ length: 15 }, (_, i) => {
    const a = (0.5 + i / 14 * 2) * Math.PI;
    return p(Math.cos(a) * 0.056, -0.16 + Math.sin(a) * 0.056);
  });
  return [
    ...lineFlows([p(-0.029, -0.12), p(-0.029, 0.20), p(-0.017, 0.22), p(0.017, 0.22), p(0.029, 0.20), p(0.029, -0.12)], { color: PAL.ivory, size: 8 * z, intensity: 0.75 * on, per: 140 }),
    ...lineFlows(bulb, { color: mixC(PAL.ember, PAL.overheat, heat), size: 11 * z, intensity: on, per: 140 }),
    ...lineFlows([p(0, -0.16), p(0, lerp(-0.09, 0.19, heat))], { color: mixC(PAL.filament, PAL.overheat, heat), size: 13 * z, intensity: 1.15 * on, per: 155 }),
    ...[-0.025, 0.06, 0.145].flatMap((v) => lineFlows([p(0.055, v), p(0.086, v)], { color: PAL.ivory, size: 7 * z, intensity: 0.65 * on })),
  ];
}

const rh = (i: number, k: number) => { const x = Math.sin(i * k) * 43758.5453; return x - Math.floor(x); };

// ================= THE TAIL: L8 "you said you needed space" .. "I'll keep the sky" (130.0 - 148.4 s) =================
const TS = { l8: at(`${S}/L8`), space: at(`${S}/L8/w4`), l9: at(`${S}/L9`), needed: at(`${S}/L9/w3`), some: at(`${S}/L9/w4`), po: at(`${PO}/L0`), fly: at(`${PO}/L1`),
  l2: at(`${PO}/L2`), stars: at(`${PO}/L2/w4`), l3: at(`${PO}/L3`), sky: at(`${PO}/L3/w3`) };
// grade.room is a gain on the cold open's room. With roomKeep > 0 the engine draws the SOFT room (earth_pol_open's patch, applied
// Nov 9 00:40): no edge, the far stars thin toward her, and its radius keeps creeping outward from the cold open's "space" (9 s)
// on, which two minutes later is 4x the radius asked for. softUnit(t) = that radius for gain 1, so room = radius / softUnit(t).
const softUnit = (t: number) => 1.099 + CREEP * SPACE.R0 * Math.max(0, t - SPACE.t);
// the room the stars give her, in her radii: a step back on "space" (his kind of space), the whole sky on "needed" (hers)
// (the push on "needed" eases in and out over a second: an ease-out here threw every star out of frame in three frames, a pop)
const roomK = (t: number) => 1.6 * spring(t - (TS.space - 0.06), 7.2, 0.6) + 2.9 * smooth(TS.needed - 0.15, TS.needed + 0.85, t);
// where the stars she sent away end up: one small knot, high on his side of the frame (the bridge cuts to one warm star)
const KNOT: Record<Fmt, { x: number; y: number; s: number }> = { '169': { x: 1.1, y: 0.58, s: 0.06 }, '916': { x: 0.25, y: 0.6, s: 0.06 } };
// when star i reaches the knot: two waves ("off you go", "off you fly"), the last few on "stars". Its flight takes longer the
// farther it has to come (d = screen units to the knot), so no star crosses the frame faster than ~1 screen height a second
// (they are dots with no motion blur: faster than that they strobe)
const flightOf = (i: number, d: number) => 1.1 + 1.15 * d + 0.45 * rh(i, 4.1414);
const arriveAt = (i: number, u: number, tf: number) => Math.max(TS.po + 0.1 + tf,
  u < 0.5 ? lerp(TS.po + 1.5, TS.fly + 1.0, u / 0.5) : u < 0.94 ? lerp(TS.fly + 1.3, TS.stars - 0.6, (u - 0.5) / 0.44) : lerp(TS.stars - 0.6, TS.stars + 0.05, (u - 0.94) / 0.06));
const arrivedShare = (t: number) => (t < TS.po + 1.5 ? 0 : t < TS.fly + 1.0 ? 0.5 * (t - TS.po - 2.0) / (TS.fly + 1.0 - TS.po - 2.0) : t < TS.fly + 1.3 ? 0.5 : t < TS.stars - 0.6 ? 0.5 + 0.44 * (t - TS.fly - 1.3) / (TS.stars - 0.6 - TS.fly - 1.3) : Math.min(1, 0.94 + 0.06 * (t - TS.stars + 0.6) / 0.65));
// the cast (2,600 stars) through the whole tail, one function of time:
//   "space"   each star backs away from her (the wave travels outward, every star with its own small lag)
//   "needed"  the room takes the whole frame: they are all outside it
//   post 2    from outside the frame each one flies through her clean sky to him on a long inward spiral and joins the knot
const WAITCAM: Partial<Record<Fmt, Cam>> = {};
const waitCam = (fmt: Fmt) => (WAITCAM[fmt] ??= camOf(TS.needed + 1.6, fmt));
const tailStar = (i: number, t: number, home: [number, number], _n: number, fmt: Fmt): [number, number] => {
  const SA = starAttr(), A = ASPECT[fmt], K = KNOT[fmt], wait = t >= TS.needed + 1.6;
  const cam = wait ? waitCam(fmt) : camOf(t, fmt);   // once they are all out of frame their waiting places stop following the camera
  const dx = home[0] - cam.x, dy = home[1] - cam.y, r = Math.hypot(dx, dy) || 1e-6;
  const R = roomK((wait ? TS.needed + 1.6 : t) - 0.1 * SA.r1[i] - 0.14 * clamp01(r / 2)) * cam.r * (1 + 0.05 * Math.sin(3 * Math.atan2(dy, dx) + 1) + 0.06 * (SA.r3[i] - 0.5));
  const r2 = Math.cbrt(r * r * r + R * R * R);
  let x = cam.x + (dx / r) * r2, y = cam.y + (dy / r) * r2;
  if (!wait) return [x, y];
  // waiting just outside the frame (they are far outside by now; nobody sees the step)
  const m = 1.08 + 0.3 * SA.r3[i], k = Math.min(1, (A * m) / Math.max(1e-6, Math.abs(x)), m / Math.max(1e-6, Math.abs(y)));
  x *= k; y *= k;
  const tf = flightOf(i, Math.hypot(x - K.x, y - K.y)), p = clamp01((t - (arriveAt(i, SA.r2[i], tf) - tf)) / tf);
  if (p <= 0) return [x, y];
  const e = 0.45 * p * p * (3 - 2 * p) + 0.55 * p * p, q = 1 - e;              // slow to leave, quicker the closer it gets (falling in)
  const g = Math.sqrt(-2 * Math.log(1 - 0.985 * SA.r3[i])), rad = K.s * g;     // its place in the knot: a small round cluster, dense at the heart
  const w = 0.45 / (0.35 + g), ph = 6.2832 * rh(i, 7.77) + w * (t - TS.po);    // the knot turns slowly, the heart faster
  const ox = rad * Math.cos(ph), oy = rad * Math.sin(ph);
  const th = 1.3 * e, c = Math.cos(th), sn = Math.sin(th), vx = (x - K.x) * q, vy = (y - K.y) * q;
  return [K.x + c * vx - sn * vy + ox * e, K.y + sn * vx + c * vy + oy * e];
};
// him: one warm point where they are going; it grows as they arrive and flares when the last of them land on "stars"
function hisKnot(t: number, fmt: Fmt): Spark[] {
  const K = KNOT[fmt], on = smooth(TS.po + 0.14, TS.po + 0.88, t), arr = arrivedShare(t), pop = env(t, TS.stars, 0.08, 0.6), z = fmt === '916' ? 0.75 : 1;
  if (on <= 0) return [];
  return [spark(K.x, K.y, { size: (8 + 6 * arr + 6 * pop) * z, color: WARM, intensity: on * (1.3 + 0.9 * arr + 1.4 * pop) }),
    spark(K.x, K.y, { size: (70 + 110 * arr + 40 * pop) * z, color: WARM, intensity: on * (0.08 + 0.12 * arr + 0.2 * pop) })];
}
// HER CROWN: the auroral oval around her north pole, drawn on her (rays stand on the 62nd parallel, straight up from the
// ground), so it turns and tilts with her. A thin ring first (it draws itself round from the far side on "some too"), then
// rays: low, a step taller on each "Ooh", full height on "sky". The far side stands up over her limb into the sky she kept.
const OVAL = { lat: 62, lon0: 96 + 180, n: 150, nTall: 50 };
const ovalLat = (a: number, t: number) => OVAL.lat + 1.5 * Math.sin(a * 12.566 + t * 0.15) + 0.8 * Math.sin(a * 56.5 - t * 0.4);
function crown(t: number, fmt: Fmt, cam: Cam): Flow[] {
  const draw = smooth(TS.some - 0.15, TS.po - 0.5, t); if (draw <= 0.001) return [];
  const up = spring(t - (TS.sky - 0.06), 6.0, 0.5);
  const H = 0.03 + 0.045 * smooth(TS.po, TS.po + 1.4, t) + 0.04 * smooth(TS.fly, TS.fly + 1.4, t) + 0.025 * smooth(TS.stars - 0.4, TS.stars + 0.3, t) + 0.12 * up;
  const G = 0.5 + 0.12 * smooth(TS.po, TS.po + 1.4, t) + 0.12 * smooth(TS.fly, TS.fly + 1.4, t) + 0.1 * up + 0.22 * env(t, TS.sky, 0.1, 0.9);
  const z = fmt === '916' ? 0.8 : 1, out: Flow[] = [];
  const P = (lat: number, lon: number, lift: number): [number, number] => { const q = projGeo(cam, [lat, lon], lift); return [q.x, q.y]; };
  // the ring itself: two halves from the far side round to the front
  for (const sg of [1, -1]) out.push(flow({ space: 'geo', lift: 0.006, pts: Array.from({ length: 49 }, (_, k) => { const a = (k / 48) * 0.5; return [ovalLat(sg > 0 ? a : 1 - a, t), OVAL.lon0 + sg * 360 * a] as [number, number]; }) },
    draw * 1.25, { tail: 1.25, size: 15 * z, count: 760, intensity: 0.75 * G, color: mixC(AUR_G, C.her, 0.25) }));
  // rays: particles at a constant spacing on screen (a fixed count per ray made the long far-side rays strings of beads at 1:1),
  // the light per ray kept the same; BUDGET keeps the whole crown under the engine's 9,000 flow particles
  const px = fmt === '916' ? 1 / 960 : 1 / 720, BUDGET = 5600;
  type Ray = { pts: [number, number][]; len: number; size: number; I: number; color: RGB; step: number; head: number };
  const rays: Ray[] = [], len = (p: [number, number][]) => p.slice(1).reduce((q, v, k) => q + Math.hypot(v[0] - p[k][0], v[1] - p[k][1]), 0);
  for (let i = 0; i < OVAL.n; i++) {
    const a = (i + 0.6 * (rh(i, 12.9898) - 0.5)) / OVAL.n, da = Math.min(a, 1 - a) * 2, on = smooth(0, 1, draw * 1.35 - da);
    if (on < 0.02) continue;
    const lon = OVAL.lon0 + 360 * a, lat = ovalLat(a, t);
    // curtains: slow folds round the ring decide how tall each ray stands; light runs along them
    const slow = 0.5 + 0.5 * Math.sin(a * 18.85 - t * 0.35), fold = 0.5 + 0.5 * Math.sin(a * 44.0 + t * 0.22), wave = 0.5 + 0.5 * Math.sin(a * 31.4 - t * 1.1 + 6.28 * rh(i, 78.233));
    const h = H * (0.18 + 1.0 * slow * slow + 0.3 * fold * fold + 0.12 * rh(i, 39.425)) * on, lean = 0.6 * Math.sin(t * 0.3 + a * 12);
    const violet = clamp01(0.3 + 0.6 * Math.sin(a * 25.1 + t * 0.2));
    const p1 = [P(lat + lean, lon + lean, h), P(lat + lean * 0.4, lon, h * 0.45), P(lat, lon, 0.004)], s1 = (17 + 60 * h) * z;
    rays.push({ pts: p1, len: len(p1), size: s1, step: s1 * 0.13 * px, head: 1.03, I: 30 * G * on * (0.3 + 0.3 * wave) * (0.6 + 2.2 * Math.min(h, 0.2)), color: mixC(AUR_G, AUR_V, violet * 0.55) });
    // violet tops, on every third ray
    if (i % 3 === 0 && i / 3 < OVAL.nTall) { const p2 = [P(lat + lean * 1.6, lon + lean, h * 1.6), P(lat + lean * 0.5, lon, h * 0.5)], s2 = (24 + 80 * h) * z; // from inside the green: the ray turns violet, no separate plume
      rays.push({ pts: p2, len: len(p2), size: s2, step: s2 * 0.12 * px, head: 1.05, I: 44 * G * on * (0.05 + 0.055 * wave) * (0.4 + 3.0 * Math.min(h, 0.2)), color: AUR_V }); }
  }
  const want = rays.reduce((q, r) => q + Math.max(6, r.len / r.step), 0), thin = Math.max(1, want / BUDGET);
  for (const r of rays) { const n = Math.max(6, Math.min(140, Math.round(r.len / (r.step * thin))));
    out.push(flow({ space: 'screen', pts: r.pts }, r.head, { tail: r.head, size: r.size, count: n, intensity: r.I / n, color: r.color })); }
  return out;
}
// "needed": her light goes out from her as one soft wave, and the stars leave ahead of it (cause, then effect). A flow fades
// along its length, so each ring is four full circles, alternating direction, starting a quarter turn apart: the fades cancel
// and the ring is even all the way round (the first version, twelve fading arcs, read as a dashed loading spinner)
function exhale(t: number, tN: number, fmt: Fmt): Flow[] {
  const u = (t - tN + 0.05) / 1.7; if (u <= 0 || u >= 1) return [];   // 1.7 s: at 1.1 s the ring crossed the frame in a handful of frames (a flash, not a wave)
  const z = fmt === '916' ? 0.55 : 1;   // the tall frame is narrow: the same ring there fills it (measured: the checks read it as a run of cuts), so it is slimmer and quieter
  const I = Math.pow(1 - u, 1.3) * z, out: Flow[] = [];
  const rings: [number, RGB, number, number][] = [[1, C.her, 0.3, 54], [1.07, mixC(C.her, C.violet, 0.7), 0.16, 80]];
  rings.forEach(([k, col, gain, size], ri) => {
    const R = lerp(1.03, 4.4, 1 - Math.pow(1 - u, 1.5)) * k;
    // the wave widens and softens as it goes out (a fixed size showed the single particles as beads once the ring was big)
    for (let q = 0; q < 4; q++) { const dir = q % 2 ? -1 : 1, a0 = q * 90.55 + ri * 45;
      out.push(flow({ space: 'rel', pts: Array.from({ length: 81 }, (_, j) => onLimb(a0 + dir * j * 5, R)) }, 1.02, { tail: 1.02, size: size * (0.45 + 0.55 * R) * (fmt === '916' ? 0.62 : 1), count: ri ? 320 : 600, intensity: ((gain * I) / (0.6 + 0.4 * R)) * (ri ? 1 : 0.4), color: col })); } // dense: at 200 a flow's particles showed as a string of beads at 1:1
  });
  return out;
}

// ---- the builders ----
const c2: Record<string, Builder> = {
  // L0: her night horizon, the last fireworks embers drifting home above it; her veins hit on every word
  c2_space: (c) => ({
    grade: { ...NIGHT, glow: 1.25, atmos: 1.0, aurora: 0.5, stars: 1.25, violet: 1, mist: 0.55, kick: 0.8 * hits(c.t, wt(0), 0.35) },
    pulses: [{ lat: 44, lon: 16, t0: c.word(S, 0, 4), speed: 26, strength: 0.6 }],
  }),
  // L1: she dims a touch so the sky can speak: the racks snap together on "meant", landed on "stars"
  c2_stars: (c) => ({ grade: { ...NIGHT, deep: lerp(1, 0.1, smooth(0.5, 1.3, c.lt)), galaxy: lerp(1, 0.45, smooth(0.5, 1.3, c.lt)), glow: lerp(1.25, 1.0, smooth(0, 1, c.lt)), atmos: lerp(1.0, 0.8, smooth(0, 1, c.lt)), violet: 1, stars: lerp(1.25, 2.0, smooth(0.9, 1.6, c.lt)), castWarm: smooth(0.7, 1.5, c.lt), mist: 0.55, kick: 0.5 * hits(c.t, wt(1), 0.3) }, ...rackHardware(c) }),
  // L2: the last of his chips rise into the racks; on "and go" the whole row rolls out
  c2_gpus: (c) => { const r = rackHardware(c); return { grade: { ...NIGHT, deep: 0.1, galaxy: 0.45, hisOff: lerp(0.88, 1, c.u), glow: 1.0, atmos: 0.8, violet: 1, stars: 2.0, castWarm: 1, mist: 0.55 }, sparks: r.sparks, flows: [...r.flows, ...chipStreams(c)] }; },
  // L3: straight down on her: three great rivers run at once, a ring of light on "rivers" and on "flow"
  c2_rivers: (c) => { const w = wt(3); return {
    grade: { ...NIGHT, daySide: 0.12, seam: 0.06, hisOff: 1, glow: 1.12, rivers: 1.7, riverPulse: 1.5, forest: 0.9, ocean: 0.5, clouds: 0.2, herCyan: 0.8, bloom: 0.5, atmos: 0.7, mist: 0.3, kick: 0.45 * hits(c.t, w, 0.4) },
    flows: [
      flow({ space: 'geo', pts: RIVERS.congo }, smooth(0, 1.7, c.lt) * 1.35, { tail: 0.45, size: 6, intensity: 1.2 }),
      flow({ space: 'geo', pts: RIVERS.nile }, smooth(0.35, 2.0, c.lt) * 1.35, { tail: 0.45, size: 6, intensity: 1.2 }),
      flow({ space: 'geo', pts: RIVERS.niger }, smooth(0.6, 2.2, c.lt) * 1.35, { tail: 0.45, size: 6, intensity: 1.1, color: C.teal }),
    ],
    pulses: [{ lat: -1, lon: 22, t0: w[2] ?? c.slot.t0 + 0.7, speed: 22, strength: 0.4 }, { lat: 30, lon: 31, t0: w[5] ?? c.slot.t0 + 1.8, speed: 28, strength: 0.4 }],
  }; },
  // L4: the dusk line across her whole face: real daylight on the crescent, her night glow everywhere else; his warm spark
  // runs across the dark toward the light and the light keeps moving away
  c2_sun: (c) => { const h = chase(c); return { grade: { ...NIGHT, glow: 1.2, daySide: 0.8, sunWarm: 1, atmos: 0.78, bloom: 0.52, clouds: 0.3, mist: 0.3 }, sparks: h.sparks, flows: h.flows }; },
  // L5: he is lost in the glare at her edge; then the crescent thins to nothing and the frame is hers and dark
  c2_disappear: (c) => { const h = chase(c), tDis = at(`${S}/L5/w2`), dark = smooth(tDis + 0.3, tDis + 1.3, c.t);
    return { grade: { ...NIGHT, glow: lerp(1.2, 1.0, dark), daySide: lerp(0.8, 0.35, dark), sunWarm: 1, atmos: 0.78, bloom: 0.52, clouds: 0.3, mist: 0.3 }, sparks: h.sparks, flows: h.flows }; },
  // The upward-looking two-shot gives his heat one graphic cue, then the next cut drops it completely.
  c2_cool: (c) => { const [x, y] = HIM_COOL[c.fmt], hot = smooth(at(`${S}/L6/w2`), at(`${S}/L6/w6`) + 0.10, c.t);
    return { grade: { ...NIGHT, deep: 0.40, galaxy: 0.55, glow: 1.15, atmos: 1.35, stars: 0.95, motes: 0.2, mist: 0.16 },
      sparks: [spark(x, y, { size: 16, color: mixC(WARM, HOT, hot), intensity: 1.65 })], flows: thermometer(c, hot) }; },
  // The camera holds the panel silhouette in quiet vacuum over her air, long enough to read the contrast.
  c2_atmos: (c) => { const [x, y] = HIM_ATMOS[c.fmt], tA = c.word(S, 7, 3), pop = env(c.t, tA, 0.07, 0.28);
    return { grade: { ...NIGHT, glow: 1.23, atmos: 1.03, aurora: 1.45, violet: 1, mist: 0.32, deep: 0.52, galaxy: 0.55, kick: 0.42 * pop },
      sparks: [spark(x, y, { size: 12 + 10 * pop, color: mixC(HOT, PAL.overheat, smooth(tA - 0.12, tA + 0.2, c.t)), intensity: 1.55 + 0.85 * pop })],
      flows: [flow({ space: 'orbit', alt: 1.035, incl: 80, node: 5, a0: 226, a1: 318 }, smooth(0, 1.1, c.lt) * 1.3,
        { tail: 0.8, size: 9, intensity: 0.26, count: 420, color: mixC(C.her, C.violet, 0.3) })] }; },
};
// ONE function of song time for the six slots of the tail (c2_space2 .. po2_sky), so slot changes inside it are invisible
const tail: Builder = (c) => {
  const t = c.t, cam = camOf(t, c.fmt), own = c.lt < c.dur;      // own = not being drawn as "the previous slot" in a blend (pulses add up there)
  const crane = smooth(TS.l8, TS.space, t), nd = smooth(TS.needed - 0.05, TS.needed + 0.5, t), hit = env(t, TS.needed, 0.12, 0.9);
  const po = smooth(TS.po, TS.po + 2.5, t), packed = arrivedShare(t), sky = smooth(TS.sky - 0.08, TS.sky + 0.4, t), skyHit = env(t, TS.sky, 0.1, 1.0);
  const wordsHit = hits(t, [...wt(8), ...wt(9)], 0.35);
  return {
    grade: { ...NIGHT, violet: 1, daySide: lerp(1, 0.3, crane), seam: 0.3,   // her day crescent is behind her and low: keep the dusk line, not a white sun blob
      glow: lerp(1.3, 1.12, crane) + 0.45 * nd - 0.42 * po + 0.15 * sky, ocean: lerp(0.6, 0.25, po), forest: lerp(1.3, 0.95, po), atmos: lerp(1.15, 1.05, crane) + 0.6 * nd - 0.3 * po + 0.25 * sky,
      aurora: 2.2 * (1 - smooth(TS.l8, TS.l8 + 1.1, t)), mist: lerp(0.65, 0.3, crane) + 0.25 * sky, motes: lerp(0.3, 0.9, nd), bloom: 0.62 + 0.1 * nd + 0.06 * sky,
      flare: 0.35 * hit, kick: 0.6 * wordsHit * (1 - nd) + 0.7 * hit + 0.5 * skyHit, haloWide: 0.2 + 0.25 * nd,
      // the sky: all of it during the crane; from "space" it keeps a room around her; from "needed" the room is the whole frame
      // (the 42,000 far stars are pushed out softly and fade as they go; the 2,600 bright ones really leave: tailStar)
      deep: 1 - smooth(TS.needed - 0.1, TS.needed + 0.9, t), galaxy: lerp(1, 0.3, nd), room: ((roomK(t) + 0.04 * Math.max(0, t - TS.space)) * cam.r) / softUnit(t), roomX: cam.x, roomY: cam.y, roomKeep: 0.16,
      stars: lerp(1.15, 1.35, po) - (c.fmt === '916' ? 1.05 : 0.75) * packed, castWarm: smooth(TS.po + 0.2, TS.po + 2.2, t) },   // (earth_cut2: the stars that go to him turn his gold)   // 2,600 stars in one knot add up: bring them down as they pack
    flows: [...exhale(t, TS.needed, c.fmt), ...crown(t, c.fmt, cam)],
    sparks: hisKnot(t, c.fmt),
    pulses: !own ? [] : [{ lat: 34, lon: 100, t0: TS.space, speed: 30, strength: 0.4 }, { lat: 80, lon: 96, t0: TS.sky, speed: 34, strength: 0.55 }],
    motes: t > TS.needed ? 'rise' : 'drift',
  };
};
for (const id of ['c2_space2', 'c2_needed']) c2[id] = tail;
const po2: Record<string, Builder> = { po2_go: tail, po2_fly: tail, po2_stars: tail, po2_sky: tail };
hardCut(c2, 'c2_gpus', 'c2_rivers', `${S}/L3`, `${S}/L4`);
hardCut(c2, 'c2_rivers', 'c2_sun', `${S}/L4`, `${S}/L5`);
hardCut(c2, 'c2_disappear', 'c2_cool', `${S}/L6`, `${S}/L7`);
hardCut(c2, 'c2_cool', 'c2_atmos', `${S}/L7`, `${S}/L8`);
hardCut(c2, 'c2_atmos', 'c2_space2', `${S}/L8`, `${S}/L9`);
// the seam into the bridge is the bridge's cut (its first camera key is a 'hold'): from its downbeat on, po2_sky draws the bridge's first slot
{ const mine = po2.po2_sky, t1 = at('bridgeA/L1'); po2.po2_sky = (c) => { const b = c.t >= T_END ? bridge.builders.br_point : undefined; return b ? b(reslot(c, T_END, t1)) : mine(c); }; }
export const chorus2: Section = { name: 'chorus2', camera: camKeys.filter((_, i) => at(SHOTS[i].at) < at(`${PO}/L0`)), stars: starKeys.filter((k) => at(k.at) < at(`${PO}/L0`)), builders: wrapAll(c2) };
// post-chorus 2 lives here with its chorus (post.ts re-exports it): post.ts stays chorus 1's file apart from that one line
export const post2: Section = { name: 'post2', camera: camKeys.filter((_, i) => at(SHOTS[i].at) >= at(`${PO}/L0`)), stars: starKeys.filter((k) => at(k.at) >= at(`${PO}/L0`)), builders: wrapAll(po2) };
// unused-import guards for helpers kept for the next pass
void reverse; void ([] as Out[]);
