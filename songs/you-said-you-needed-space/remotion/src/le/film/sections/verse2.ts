// Verse 2: v2_rain .. v2_light (song 82.6-101.2 s). Built by earth_sec_v2, Sun Nov 8 2026 (was: rough defaults by le_engine).
// The stretch in one line: with him gone she finally gets her rain, her green and her sleep (2a, close and cool),
// then his machines' appetite is packed into labelled moving boxes and shipped to his rocket (2b, warm vs her cyan).
//   A  v2_rain      CUT to a low horizon over the Amazon at night: rain of light, one ripple per sung word
//   B  v2_green     the camera follows the rain down into the forest; it blooms in teal waves on "green"
//   C  v2_sleep/v2_whirring  CUT to his warm white city lights humming; they click off, her cyan settles, stars drift into "Zzz"
//   D  v2_chips..v2_light    CUT to a low horizon; four moving boxes drawn in his warm light, each labelled in stars on its
//                   key word (CHIPS, SNACKS, HUM, LIGHT), filled from her surface, then shipped to the rocket's cargo stack.
//                   She gets brighter with every box that leaves. (Box 4 ships in p2_milky: pre2.ts calls moveOut too.)
// POLISH (earth_pol_v2, Mon Nov 9): look pass (every slot on the lux planet, LOOKB below), clean cuts (post 1 -> rain, green -> sleep,
// whirring -> boxes), labels that hold 1.5 s+, him drawn as a satellite. Cut 1's version: build/le_pol_v2/orig/verse2.ts.cut1.
// inserts: none needed. PLACEHOLDER: if the ground v2 worker (pitch_mockups/ground2) makes a ground-level "forest blooms"
// clip, it belongs on v2_green (song 86.2-88.0): add { slot: 'v2_green', src: 'le/inserts/<clip>.mp4', from: 86.2 } below.
// The engine version here works without it. v2_green is also this stretch's one close-surface slot: the engine's surface goes soft
// past r ~2.5 at 1440p, so the dive lands at r 2.4-2.5 with tight bloom; the redone close surface (pitch_mockups/surface2,
// night_plate region 'amazon') belongs here once the pitch page decides it.
import { PAL, Section, Builder, Ctx, Out, hits, smooth, spark, flow, C, lerp, clamp01 } from './api';
import { at, words } from '../anchor';
import { camAt, camFor, viewOfGeo, toScreen, SPIN_DEG_S } from '../camera';
import { rng, home, starAttr, ASPECT } from '../stars';
import { Box, Cam, Flow, Fmt, Pulse, Spark, StarSet } from '../types';
import { Grade, RGB } from '../grade';
import { LOOK } from './coldOpen'; // read only: the approved look (lux planet, deep stars, Milky Way mist)
import { post1 } from './post';     // read only, plus the hand-over at the 2478 seam (bottom of this file)

const wt = (sec: string, li: number) => words(sec, li).map((w) => w[0]);
// the camera's lon gets her spin added (camera.ts): the key value that puts `target` longitude in front at time `a`
export const lonAt = (target: number, a: string | number) => target - SPIN_DEG_S * at(a);
// a place on her as [x, y] in her radii from her centre (same in 16:9 and 9:16)
const relOfGeo = (cam: Cam, lat: number, lon: number): [number, number] => { const p = toScreen({ ...cam, x: 0, y: 0, r: 1 }, viewOfGeo(cam, lat, lon)); return [p.x, p.y]; };
// Star shapes in this stretch have their own layout per format (the engine's automatic 9:16 re-fit stacks side shapes on one
// spot), laid out by hand for 9:16: centred, inside the safe zone.
// ---- a one-stroke plotter alphabet (survey-map lettering), drawn as dots of light. Cap height = 6, baseline y = 0 ----
export const GLYPH: Record<string, { w: number; s: number[][][] }> = {
  A: { w: 4, s: [[[0, 0], [2, 6], [4, 0]], [[1, 2.2], [3, 2.2]]] }, B: { w: 4, s: [[[0, 0], [0, 6], [3, 6], [4, 5], [4, 4], [3, 3], [0, 3]], [[3, 3], [4, 2], [4, 1], [3, 0], [0, 0]]] },
  C: { w: 4, s: [[[4, 5], [3, 6], [1, 6], [0, 5], [0, 1], [1, 0], [3, 0], [4, 1]]] }, D: { w: 4, s: [[[0, 0], [0, 6], [2.5, 6], [4, 4.5], [4, 1.5], [2.5, 0], [0, 0]]] },
  E: { w: 3.6, s: [[[3.6, 6], [0, 6], [0, 0], [3.6, 0]], [[0, 3], [2.8, 3]]] }, I: { w: 0.4, s: [[[0.2, 0], [0.2, 6]]] },
  K: { w: 4, s: [[[0, 0], [0, 6]], [[4, 6], [0, 2.6]], [[1.4, 3.8], [4, 0]]] }, L: { w: 3.6, s: [[[0, 6], [0, 0], [3.6, 0]]] },
  M: { w: 5, s: [[[0, 0], [0, 6], [2.5, 2], [5, 6], [5, 0]]] }, N: { w: 4, s: [[[0, 0], [0, 6], [4, 0], [4, 6]]] },
  O: { w: 4, s: [[[1, 0], [0, 1], [0, 5], [1, 6], [3, 6], [4, 5], [4, 1], [3, 0], [1, 0]]] },
  S: { w: 4, s: [[[4, 5], [3, 6], [1, 6], [0, 5], [0, 4], [1, 3], [3, 3], [4, 2], [4, 1], [3, 0], [1, 0], [0, 1]]] },
  T: { w: 4, s: [[[0, 6], [4, 6]], [[2, 6], [2, 0]]] }, V: { w: 4, s: [[[0, 6], [2, 0], [4, 6]]] }, W: { w: 5.4, s: [[[0, 6], [1.3, 0], [2.7, 4.2], [4.1, 0], [5.4, 6]]] },
  Y: { w: 4, s: [[[0, 6], [2, 3], [4, 6]], [[2, 3], [2, 0]]] }, '0': { w: 3.6, s: [[[1, 0], [0, 1], [0, 5], [1, 6], [2.6, 6], [3.6, 5], [3.6, 1], [2.6, 0], [1, 0]]] },
  H: { w: 4, s: [[[0, 0], [0, 6]], [[4, 0], [4, 6]], [[0, 3], [4, 3]]] }, P: { w: 4, s: [[[0, 0], [0, 6], [3, 6], [4, 5], [4, 4], [3, 3], [0, 3]]] },
  U: { w: 4, s: [[[0, 6], [0, 1], [1, 0], [3, 0], [4, 1], [4, 6]]] }, G: { w: 4, s: [[[4, 5], [3, 6], [1, 6], [0, 5], [0, 1], [1, 0], [3, 0], [4, 1], [4, 2.8], [2.2, 2.8]]] },
  '1': { w: 1.8, s: [[[0, 4.6], [1.6, 6], [1.6, 0]]] }, ' ': { w: 2.6, s: [] },
};
export const GAP = 1.5;
export const textWidth = (text: string, cap: number) => (text.split('').reduce((a, ch) => a + GLYPH[ch].w, 0) + GAP * (text.length - 1)) * cap / 6;
// ---- star shapes from pure geometry. The engine's text / svg / rects sets rasterise on a canvas and seed their star layout from
// the pixel count, so two render tabs can disagree by a pixel and a held label then boils from frame to frame (seen on LIGHT in
// 9:16, frames 3029-3035 of the first render). These are laid out from strokes with a fixed seed: the same in every tab. ----
type V2 = [number, number];
export function starShape(id: string, build: (fmt: Fmt) => { lines: V2[][]; weight: number }, keep = 0.06): StarSet {
  const cache = new Map<Fmt, Float32Array>();
  const layout = (fmt: Fmt) => {
    const { lines, weight } = build(fmt), H = home(fmt), A = starAttr(), R = rng(9000 + id.length * 977 + id.charCodeAt(0) * 31 + id.charCodeAt(id.length - 1)), out = Float32Array.from(H);
    const segs: { a: V2; b: V2; l: number }[] = []; let tot = 0;
    for (const ln of lines) for (let i = 0; i + 1 < ln.length; i++) { const l = Math.hypot(ln[i + 1][0] - ln[i][0], ln[i + 1][1] - ln[i][1]); segs.push({ a: ln[i], b: ln[i + 1], l }); tot += l; }
    const moving: number[] = []; for (let i = 0; i < H.length / 2; i++) if (A.r3[i] >= keep) moving.push(i);
    const tg: V2[] = []; let si = 0, acc = 0;
    for (let m = 0; m < moving.length; m++) { // evenly along the strokes, scattered inside the stroke's width (round, bold letters)
      const d = ((m + R()) / moving.length) * tot; while (si < segs.length - 1 && acc + segs[si].l < d) { acc += segs[si].l; si++; }
      const sg = segs[si], u = sg.l > 0 ? Math.min(1, (d - acc) / sg.l) : 0, an = R() * Math.PI * 2, rad = weight * Math.sqrt(R());
      tg.push([sg.a[0] + (sg.b[0] - sg.a[0]) * u + Math.cos(an) * rad, sg.a[1] + (sg.b[1] - sg.a[1]) * u + Math.sin(an) * rad]); }
    moving.sort((p, q) => H[p * 2] - H[q * 2]); tg.sort((p, q) => p[0] - q[0]); // left stays left: the stars travel without crossing the whole sky
    moving.forEach((i, m) => { out[i * 2] = tg[m][0]; out[i * 2 + 1] = tg[m][1]; });
    return out; };
  return { kind: 'fn', front: true, fn: (i, _t, _h, _n, fmt) => { let P = cache.get(fmt); if (!P) { P = layout(fmt); cache.set(fmt, P); } return [P[i * 2], P[i * 2 + 1]]; } };
}
// a word as strokes, fitted inside a box (cap height and width both respected, the stroke's own width included)
export function wordLines(text: string, box: Box): { lines: V2[][]; weight: number } {
  const units = textWidth(text, 6), k0 = Math.min(box.h / (6 + 2 * 0.6), box.w / (units + 2 * 0.6)), weight = 0.6 * k0, k = k0, w = units * k;
  const lines: V2[][] = []; let pen = box.cx - w / 2; const y0 = box.cy - 3 * k;
  for (const ch of text) { const gl = GLYPH[ch]; for (const st of gl.s) lines.push(st.map((q) => [pen + q[0] * k, y0 + q[1] * k] as V2)); pen += (gl.w + GAP) * k; }
  return { lines, weight };
}
const mixC = (a: RGB, b: RGB, u: number): RGB => [lerp(a[0], b[0], u), lerp(a[1], b[1], u), lerp(a[2], b[2], u)];
// ---- the film's look (same base as pre1.ts lookBase, without the cold open's room): the lux planet, the deep star field and the
// Milky Way mist under every slot of verse 2 and pre-chorus 2; each builder's own grade goes on top (deep / galaxy turned down
// where the cast stars spell something, as chorus1.ts does). ----
export const LOOKB: Partial<Grade> = { ...LOOK, seam: 0.14, hisWarm: 0.35, haloWide: 0.25, room: 0 };
export const withLookB = (B: Record<string, Builder>) => { for (const id of Object.keys(B)) { const b = B[id]; B[id] = (c) => { const o = b(c); return { ...o, grade: { ...LOOKB, ...(o.grade ?? {}) } }; }; } };
// Hard cuts stay hard (same idea as pre1.ts hardCut): the engine cross-fades every slot change over 0.45 s, so where the camera
// cuts, the outgoing slot's builder draws the incoming shot from the cut on. Pulses stay with the incoming side (the engine adds both).
const reslot = (c: Ctx, id: string, t0: number, t1: number): Ctx => ({ ...c, slot: { ...c.slot, id, t0, t1 }, lt: c.t - t0, u: clamp01((c.t - t0) / (t1 - t0)), dur: t1 - t0 });
export const cutTo = (B: Record<string, Builder>, from: string, to: Builder, id: string, t0: number, t1: number) => { const a = B[from]; if (!a) return;
  B[from] = (c) => (c.t >= t0 ? { ...to(reslot(c, id, t0, t1)), pulses: [] } : a(c)); };

// ---------------- A + B: rain, then green ----------------
const RAIN_GEO: [number, number][] = [[-3, -60], [-11, -52], [3, -67], [-15, -63], [1, -74], [-7, -46]]; // where each sung word's drop lands
const RAINW = wt('verse2a', 0);
const rainPulses = (t: number): Pulse[] => RAINW.map((w, k) => ({ lat: RAIN_GEO[k % 6][0], lon: RAIN_GEO[k % 6][1], t0: w, speed: 13, strength: 0.5 * (1 - smooth(w + 1.6, w + 2.4, t)) }));
const RR = rng(8201);
const DROPS = Array.from({ length: 80 }, () => ({ x: RR() * 2 - 1, y: RR(), p: 0.7 + 0.6 * RR(), o: RR() * 3, s: RR() }));
// CUT 2 (earth_c2_v2; cloud chat for Adita, Nov 9 00:40: "too many full-globe shots in a row ... vary scale and angle, get low over the
// surface"): the rain shot is now LOW over the Amazon, looking along her surface to the horizon (it was the top half of the globe).
// 9:16 gets its own height (the automatic re-frame left two thirds of the frame as empty sky): rain9 lifts her, and lets go as the
// camera dives after the rain, so v2_green lands where it did.
const RAIN9 = 0.45, rain9 = (t: number) => RAIN9 * (1 - smooth(at('verse2a/L0/w5'), at('verse2a/L1/w4') + 0.1, t));
const camRain = (c: Ctx): Cam => (c.fmt === '916' ? { ...c.base.cam, y: c.base.cam.y + rain9(c.t) } : c.base.cam);
const v2_rain: Builder = (c) => {
  const cam = camRain(c), cs = camFor(c.fmt, cam), topR = (1 - cs.y) / cs.r, botR = (-1 - cs.y) / cs.r, tall = topR - Math.max(0.2, botR) + 0.12, wide = Math.min(0.95, 1.04 * ASPECT[c.fmt] / cs.r);
  const rainEnd = at('verse2a/L0/w5');
  const k = smooth(0.1, 0.7, c.lt) * (1 - smooth(rainEnd + 0.15, rainEnd + 0.75, c.t)); // streaks thin out as the camera dives after them
  const flows: Flow[] = [], sparks: Spark[] = [];
  for (const d of DROPS) { // the rain: short streaks of her light falling onto her, slanted
    const lx = d.x * wide, top = Math.sqrt(Math.max(0, 1 - lx * lx)); if (top < 0.3) continue;
    const ly = lerp(Math.max(0.2, botR), top * 0.96, d.y), u = (((c.t + d.o) / d.p) % 1 + 1) % 1;
    flows.push(flow({ space: 'rel', pts: [[lx + 0.13 * tall, ly + tall], [lx, ly]] }, u * 1.08, { tail: 0.07, count: 14, size: 6 + 5 * d.s, color: mixC(C.her, C.white, 0.35 + 0.4 * d.s), intensity: (1.5 + 1.3 * d.s) * k }));
  }
  RAINW.forEach((w, i) => { // one bigger drop per sung word; where it lands a ring of light spreads over her (pulses)
    const p = relOfGeo(cam, RAIN_GEO[i % 6][0], RAIN_GEO[i % 6][1]), u = (c.t - (w - 0.42)) / 0.42;
    if (u > 0 && u < 1.25) flows.push(flow({ space: 'rel', pts: [[p[0] + 0.13 * tall, p[1] + tall], p] }, u, { tail: 0.14, count: 22, size: 11, color: mixC(C.her, C.white, 0.6), intensity: 2.4 * smooth(0, 0.3, c.lt + 0.3) }));
    sparks.push(spark(0, 0, { rel: p, size: 10, color: C.her, intensity: 1.5 * hits(c.t, [w], 0.2, 0.04) * smooth(0, 0.2, c.lt) }));
  });
  const motes = 1.15 * smooth(0, 0.7, c.lt); // (the cut from post 1 is hard now, so the rain can start at once)
  return { ...(c.fmt === '916' ? { cam: { y: cam.y } } : {}), motes: 'rain', flows, sparks, pulses: rainPulses(c.t),
    grade: { violet: 1, mist: 0.6, motes, clouds: 0.5, ocean: 0.8, glow: 1.0, hisWarm: 0.3, herCyan: 0.85, rivers: 0.9, atmos: 1.15, aurora: 0, kick: 0.22 * hits(c.t, RAINW, 0.32) } };
};
const v2_green: Builder = (c) => {
  const W = wt('verse2a', 1), g = at('verse2a/L1/w4'); // "green"
  const bloom = smooth(g - 0.3, g + 0.55, c.t);
  return { ...(c.fmt === '916' ? { cam: { y: c.base.cam.y + rain9(c.t) } } : {}), motes: 'rain',
    // every ring is gone before the cut at the end of the slot (the engine keeps a slot's pulses 0.45 s into the next one, then drops them)
    pulses: [...rainPulses(c.t).slice(2), { lat: -3, lon: -60, t0: W[0], speed: 11, strength: 0.35 }, { lat: -9, lon: -68, t0: W[2], speed: 11, strength: 0.35 },
      { lat: -4, lon: -62, t0: g - 0.05, speed: 17, strength: 0.6 }, { lat: 3, lon: -53, t0: g + 0.28, speed: 17, strength: 0.45 }].map((p) => ({ ...p, strength: p.strength * (1 - smooth(c.dur - 0.4, c.dur - 0.04, c.lt)) })),
    grade: { forest: lerp(0.9, 2.6, bloom), glow: lerp(1.0, 1.08, bloom), rivers: lerp(0.9, 0.8, bloom), kick: 0.15 * hits(c.t, W, 0.3), hisWarm: 0.25, herCyan: 0.9, clouds: lerp(0.5, 0.2, c.u), violet: 1, mist: 0.45, ocean: 0.8, atmos: 1.15, bloom: lerp(0.6, 0.38, smooth(0, 1.2, c.lt)), bloomRadius: lerp(0.45, 0.3, smooth(0, 1.2, c.lt)),
      motes: 1.0 * (1 - smooth(c.dur - 0.4, c.dur - 0.05, c.lt)) } };
};

// ---------------- C: his lights hum, then off; she sleeps ----------------
const ZBOX: Record<Fmt, Box> = { '169': { cx: 1.1, cy: 0.5, w: 1.0, h: 0.82 }, '916': { cx: 0.02, cy: 0.47, w: 0.62, h: 0.5 } }; // 9:16: centred above her, inside the safe zone
const ZZZ = starShape('zzz', (fmt) => { const b = ZBOX[fmt], m = (x: number, y: number): [number, number] => [b.cx + (x / 120 - 0.5) * b.w, b.cy + (0.5 - y / 100) * b.h];
  // z z Z, rising up and to the right like a comic (drawn on a 120 x 100 card, y down)
  return { weight: 0.02 * b.h / 0.9, lines: [[m(6, 72), m(21, 72), m(6, 91), m(21, 91)], [m(34, 42), m(58, 42), m(34, 72), m(58, 72)], [m(70, 7), m(107, 7), m(70, 53), m(107, 53)]] }; }, 0.35);
// CUT 2: this was the stretch's full-globe shot. Now the camera is low over the Gulf looking north across his city lights to the
// horizon: the lights are big enough to watch them click off one cluster at a time, and the Zzz rises off her limb.
// 9:16 has its own height (SLEEP9: the automatic re-frame put the cities in the bottom UI zone).
const SLEEP9 = 0.62;
const sleep: Builder = (c) => {
  const S = wt('verse2a', 2), t = c.t, t0 = at('verse2a/L2'), zz = at('verse2a/L2/w4'), mach = at('verse2a/L3/w4'); // "sleep", "machines"
  // a few lights go on each word, most on "sleep", the stragglers one by one through "machines"
  const off = 0.08 * smooth(S[1], S[1] + 0.2, t) + 0.1 * smooth(S[3], S[3] + 0.25, t) + 0.27 * smooth(zz, zz + 0.5, t) + 0.55 * smooth(at('verse2a/L3'), mach + 0.45, t);
  const whir = (1 - smooth(zz, mach, t)) * (0.07 * Math.sin(t * 2 * Math.PI * 5.0) + 0.04 * Math.sin(t * 2 * Math.PI * 7.3)); // the whirring: his lights buzz (intended, small)
  const asleep = smooth(zz, zz + 1.2, t), breath = 0.06 * Math.sin((t - zz) * 2 * Math.PI * 0.4) * asleep;
  return { ...(c.fmt === '916' ? { cam: { y: c.base.cam.y + SLEEP9 } } : {}), grade: { hisWarm: 1.55 * (1 + whir), hisOff: clamp01(off), herCyan: lerp(0.12, 1.15, smooth(zz, mach + 0.6, t)), glow: lerp(0.8, 1.05, asleep) + breath, forest: 0.5,
    violet: lerp(0.6, 1, asleep), mist: lerp(0.25, 0.6, asleep), stars: lerp(1.0, 1.75, smooth(zz - 0.5, zz + 0.2, t)), aurora: 0.25 * asleep, motes: 0.45 * smooth(0.5, 1.3, t - t0),
    deep: lerp(1, 0.14, smooth(zz - 0.6, zz + 0.2, t)), galaxy: lerp(1, 0.4, smooth(zz - 0.6, zz + 0.2, t)) } }; // the sky goes quiet for the Zzz
};

// ---------------- D: the move-out (also used by pre2.ts for the last box and his leaving) ----------------
// POLISH (earth_pol_v2, Nov 9): every label now lands on its sung word and stays readable 1.5 s or more. One box position could
// not do that (the next line's box needed the spot), so 16:9 alternates two positions (left, right) and 9:16 lifts each labelled
// box to a shelf above the packing spot. Each label is the cast stars PLUS a soft warm stroke under them (reads at phone size;
// the stars alone were sparkle). He is drawn as him: a satellite in a few warm-white strokes, towing the boxes as parcels.
const LS = [0, 1, 2, 3].map((i) => at(`verse2b/L${i}`));
const KW = ['verse2b/L0/w5', 'verse2b/L1/w3', 'verse2b/L2/w3', 'verse2b/L3/w3'].map((a) => at(a)); // chips, appetite, hum, light: the box is taped shut on the word
// when each label lands: on its sung word, except LIGHT, which lands on "never-ending" (and is taped on "light"). Cloud chat for
// Adita, Nov 9 00:40: "MILKY WAY ESTATES survey map on the galaxy with one SOLD lot (03, replace the odd "LIGHT" billboard at p12)":
// p12 = pre-chorus 2, which opened on the LIGHT box. "light" is sung 0.3 s before "You can have the Milky Way", so a label landing
// on the word either flashes by or sits over the next line. Now LIGHT is up for 1.2 s inside verse 2 and is gone as pre-chorus 2 starts.
const KWL = [KW[0], KW[1], KW[2], at('verse2b/L3/w2')];
export const DRAW = [LS[0] + 0.05, LS[1] + 0.26, LS[2] + 0.05, KW[2] + 0.87]; // when each box is drawn
const UP = [KW[0] + 0.55, KW[1] + 0.72, KW[2] + 0.55, 1e9];                    // 9:16: the labelled box is lifted to the shelf
export const SHIP = [KW[0] + 2.25, KW[1] + 2.11, KW[2] + 1.87, at('pre2/L0') + 0.05]; // when each box leaves for him
const FLY = 0.62;
export const DEPART = SHIP[3] + FLY + 0.12; // he leaves with all four
export const GAL_T = at('pre2/L0') - 0.22;  // LIGHT's stars let go into the Milky Way a breath before "You can have the Milky Way" (pre2.ts)
// "midnight appetite" = SNACKS: the creative-director pun on the CHIPS box before it (one string to change if she'd rather not)
export const LABELS = ['CHIPS', 'SNACKS', 'HUM', 'LIGHT'];
type Lay = { ground: Box[]; shelf: Box | null; pad: V2; him: V2; s: number; dock: V2; dock0: V2; dockStep: V2; away: V2; lane: number | null };
const GL: Box = { cx: -0.96, cy: 0.22, w: 1.1, h: 0.42 }, GR: Box = { cx: 0.4, cy: 0.22, w: 1.1, h: 0.42 }, G9: Box = { cx: 0, cy: -0.03, w: 0.66, h: 0.2 };
// ground = each box's word box (the outline sits `pad` outside it); him = where he floats, s = his half span;
// dock = a parcel's size, dock0 + dockStep * b = where parcel b hangs from him (16:9: a string under him; 9:16: a train behind him)
export const LAY: Record<Fmt, Lay> = {
  '169': { ground: [GL, GR, GL, GR], shelf: null, pad: [0.08, 0.075], him: [1.4, 0.74], s: 0.24, dock: [0.17, 0.1], dock0: [0, -0.24], dockStep: [0, -0.135], away: [1.5, 0.9], lane: 0.64 }, // lane: the height a box flies to him at, between the standing boxes and his wings
  '916': { ground: [G9, G9, G9, G9], shelf: { ...G9, cy: 0.33 }, pad: [0.05, 0.045], him: [0.3, 0.62], s: 0.12, dock: [0.085, 0.055], dock0: [-0.16, 0], dockStep: [-0.105, 0], away: [0.7, 1.1], lane: null },
};
export const fullOf = (L: Lay, w: Box): Box => ({ cx: w.cx, cy: w.cy, w: w.w + 2 * L.pad[0], h: w.h + 2 * L.pad[1] });
const backOut = (f: number) => { const k = 1.4, x = clamp01(f) - 1; return 1 + (k + 1) * x * x * x + k * x * x; }; // arrives, overshoots a little, settles
// his leaving: a small dip back first (anticipation), then he accelerates away up-right with the lot
const goOf = (t: number, L: Lay): V2 => { const dep = Math.max(0, t - DEPART), dd = dep * dep * 2.4 - 0.022 * smooth(DEPART - 0.3, DEPART, t) * (1 - smooth(DEPART, DEPART + 0.25, t)); return [L.away[0] * dd, L.away[1] * dd]; };
// where parcel b hangs: on a string from him, swaying a little more the further down it is (luggage, not a diagram)
const dockOf = (L: Lay, b: number, t: number): V2 => { const sw = 0.055 * L.s * (b + 1) * Math.sin(t * 1.7 - b * 0.55), v = L.dockStep[0] === 0;
  return [L.him[0] + L.dock0[0] + L.dockStep[0] * b + (v ? sw : 0), L.him[1] + L.dock0[1] + L.dockStep[1] * b + (v ? 0 : sw)]; };
// where box b is at time t: open on the ground, (9:16) lifted to the shelf, flying to him (e 0..1), or leaving with him
export function boxAt(b: number, t: number, fmt: Fmt): { box: Box; e: number; go: V2 } {
  const L = LAY[fmt], g = fullOf(L, L.ground[b]), go = goOf(t, L); let cx = g.cx, cy = g.cy;
  if (L.shelf) { const u = backOut((t - UP[b]) / 0.5); cx = lerp(g.cx, L.shelf.cx, u); cy = lerp(g.cy, L.shelf.cy, u); }
  // the flight: it lifts and shrinks to parcel size, travels along the lane (a left box clears the right one), drops onto his string
  const f = clamp01((t - SHIP[b]) / FLY), e = f * f * (3 - 2 * f), d = dockOf(L, b, t), es = smooth(0, 0.35, f);
  const x = L.lane === null ? lerp(cx, d[0], e) : lerp(cx, d[0], smooth(0.2, 0.78, f));
  const y = L.lane === null ? lerp(cy, d[1], e) + 0.05 * Math.sin(Math.PI * e) : cy + (L.lane - cy) * smooth(0, 0.35, f) + (d[1] - L.lane) * smooth(0.68, 1, f);
  return { e, go, box: { cx: x + go[0], cy: y + go[1], w: lerp(g.w, L.dock[0], es), h: lerp(g.h, L.dock[1], es) } };
}
// ---- the labels: ONE star set for the whole move-out, each star on its own clock. Even stars spell CHIPS then HUM, odd stars
// SNACKS then LIGHT (two labels are up at once). A label's stars land on its word, ride the box to the shelf and to him, and
// peel off home in flight; LIGHT's stay where they are (pre2's galaxy key takes them). Stars with nothing to do wait in the
// sky with the stage cleared: none over her, inside a box or on him (the set is on the front layer). ----
const IDLE: Partial<Record<Fmt, Float32Array>> = {};
function idle(fmt: Fmt): Float32Array {
  const hit = IDLE[fmt]; if (hit) return hit;
  const H = home(fmt), L = LAY[fmt], out = Float32Array.from(H), R = rng(3131), A = ASPECT[fmt], cs = camFor(fmt, camAt(LS[2]));
  const zones = [...L.ground, ...(L.shelf ? [L.shelf] : [])].map((w) => fullOf(L, w));
  const bad = (x: number, y: number) => Math.hypot(x - cs.x, y - cs.y) < cs.r * 1.035 || Math.hypot(x - L.him[0], y - L.him[1]) < L.s * 1.35
    || zones.some((z) => Math.abs(x - z.cx) < z.w / 2 + 0.035 && Math.abs(y - z.cy) < z.h / 2 + 0.035);
  for (let i = 0; i < H.length / 2; i++) { if (!bad(H[i * 2], H[i * 2 + 1])) continue;
    for (let k = 0; k < 60; k++) { const x = (R() * 2 - 1) * A * 1.04, y = (R() * 2 - 1) * 1.04; if (!bad(x, y)) { out[i * 2] = x; out[i * 2 + 1] = y; break; } } }
  return (IDLE[fmt] = out);
}
const WL = new Map<string, { lines: V2[][]; weight: number }>();
const wordOf = (b: number, fmt: Fmt) => { const k = `${b}${fmt}`; let v = WL.get(k); if (!v) { v = wordLines(LABELS[b], LAY[fmt].ground[b]); WL.set(k, v); } return v; };
const LBL = new Map<string, Float32Array>();
function labelLayout(b: number, fmt: Fmt): Float32Array { // where each star of label b's half of the cast sits in the word (at the box's ground position)
  const key = `${b}${fmt}`, hit = LBL.get(key); if (hit) return hit;
  const { lines, weight } = wordOf(b, fmt), I = idle(fmt), R = rng(9100 + b * 977), out = Float32Array.from(I);
  const segs: { a: V2; b: V2; l: number }[] = []; let tot = 0;
  for (const ln of lines) for (let i = 0; i + 1 < ln.length; i++) { const l = Math.hypot(ln[i + 1][0] - ln[i][0], ln[i + 1][1] - ln[i][1]); segs.push({ a: ln[i], b: ln[i + 1], l }); tot += l; }
  const mine: number[] = []; for (let i = b % 2; i < I.length / 2; i += 2) mine.push(i);
  const tg: V2[] = []; let si = 0, acc = 0;
  for (let m = 0; m < mine.length; m++) { // evenly along the strokes, scattered inside the stroke's width
    const d = ((m + R()) / mine.length) * tot; while (si < segs.length - 1 && acc + segs[si].l < d) { acc += segs[si].l; si++; }
    const sg = segs[si], u = sg.l > 0 ? Math.min(1, (d - acc) / sg.l) : 0, an = R() * Math.PI * 2, rad = weight * 0.85 * Math.sqrt(R());
    tg.push([sg.a[0] + (sg.b[0] - sg.a[0]) * u + Math.cos(an) * rad, sg.a[1] + (sg.b[1] - sg.a[1]) * u + Math.sin(an) * rad]); }
  mine.sort((p, q) => I[p * 2] - I[q * 2]); tg.sort((p, q) => p[0] - q[0]); // left stays left: the stars travel without crossing the whole sky
  mine.forEach((i, m) => { out[i * 2] = tg[m][0]; out[i * 2 + 1] = tg[m][1]; });
  LBL.set(key, out); return out;
}
const sm = (x: number) => { const u = clamp01(x); return u * u * (3 - 2 * u); };
const LABELSET: StarSet = { kind: 'fn', front: true, fn: (i, t, _h, _n, fmt) => {
  const I = idle(fmt), ix = I[i * 2], iy = I[i * 2 + 1], r1 = starAttr().r1[i];
  for (const b of [(i % 2) + 2, i % 2]) {
    const t0 = KWL[b] - 0.36 + 0.14 * r1; if (t < t0) continue;      // lands ON the word (complete within ~0.1 s of its onset)
    const P = labelLayout(b, fmt); let px = P[i * 2], py = P[i * 2 + 1];
    if (b < 3) { const L = LAY[fmt], g = fullOf(L, L.ground[b]), { box } = boxAt(b, t, fmt); px = box.cx + (px - g.cx) * (box.w / g.w); py = box.cy + (py - g.cy) * (box.h / g.h); }
    const k = sm((t - t0) / 0.34) * (b < 3 ? 1 - sm((t - (SHIP[b] + 0.18 + 0.25 * r1)) / 0.6) : 1);
    return [ix + (px - ix) * k, iy + (py - iy) * k];
  }
  return [ix, iy];
} };
const WARM: RGB = PAL.filament, WARMW: RGB = [1.0, 0.76, 0.46], BOXC: RGB = PAL.ember; // (earth_cut2, gate 7) him + labels Filament, his boxes Ember (was neutral cream)
// a dot of light, and a stroke made of them (one particle each: the engine has 9,000 flow particles a frame, a long-tailed flow wastes most)
export const dot = (p: V2, size: number, color: RGB, intensity: number): Flow => flow({ space: 'screen', pts: [p] }, 0, { tail: 0, count: 1, size: size / 2.2, color, intensity });
export function line(out: Flow[], pts: V2[], step: number, size: number, color: RGB, intensity: number, frac = 1) {
  if (intensity <= 0.002 || frac <= 0) return; const ls: number[] = []; let tot = 0;
  for (let i = 0; i + 1 < pts.length; i++) { const l = Math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]); ls.push(l); tot += l; }
  const n = Math.max(1, Math.round(tot / step)), m = Math.min(n + 1, Math.ceil((n + 1) * Math.min(1, frac))); let si = 0, acc = 0;
  for (let j = 0; j < m; j++) { const d = (j / n) * tot; while (si < ls.length - 1 && acc + ls[si] < d) { acc += ls[si]; si++; }
    const u = ls[si] > 0 ? Math.min(1, (d - acc) / ls[si]) : 0; out.push(dot([lerp(pts[si][0], pts[si + 1][0], u), lerp(pts[si][1], pts[si + 1][1], u)], size, color, intensity)); }
}
const corners = (b: Box): V2[] => { const x0 = b.cx - b.w / 2, x1 = b.cx + b.w / 2, y0 = b.cy - b.h / 2, y1 = b.cy + b.h / 2; return [[x0, y1], [x1, y1], [x1, y0], [x0, y0], [x0, y1]]; };
const bez = (p0: V2, p1: V2, p2: V2, n: number, wob?: (s: number) => number): V2[] => Array.from({ length: n }, (_, i) => {
  const s = i / (n - 1), a = (1 - s) * (1 - s), b = 2 * s * (1 - s), cc = s * s; let x = a * p0[0] + b * p1[0] + cc * p2[0], y = a * p0[1] + b * p1[1] + cc * p2[1];
  if (wob) { const tx = 2 * (1 - s) * (p1[0] - p0[0]) + 2 * s * (p2[0] - p1[0]), ty = 2 * (1 - s) * (p1[1] - p0[1]) + 2 * s * (p2[1] - p1[1]), l = Math.hypot(tx, ty) || 1, o = wob(s); x += (-ty / l) * o; y += (tx / l) * o; }
  return [x, y] as V2; });
const SR = rng(4407); const SEED = Array.from({ length: 32 }, () => [SR(), SR(), SR()]);
// packets travelling along a path, one short flow each (a flow's trail fades toward its tail, so one long conveyor goes dim)
const packets = (pts: V2[], t: number, ts: number, te: number, travel: number, gap: number, o: Partial<Flow>): Flow[] => {
  const out: Flow[] = [];
  for (let m = 0; ts + m * gap + travel <= te + 1e-6; m++) { const h = (t - ts - m * gap) / travel; if (h > 0 && h < 1 + (o.tail ?? 0.1)) out.push(flow({ space: 'screen', pts }, h, o)); }
  return out;
};
// HIM: the approved 3D him's silhouette in strokes of his warm white, his bright core inside, the whip's tip blinking. He floats, dips under every box that lands on his string, leans into the way out. `at` = his centre.
function him(t: number, L: Lay, p: V2, docked: number, dockFlash: number, dep: number, flows: Flow[], sparks: Spark[]) {
  const s = L.s, dip = SHIP.reduce((a, sh) => { const x = t - (sh + FLY); return a + (x > 0 ? Math.exp(-x * 5) * Math.sin(x * 15) : 0); }, 0);
  const lean = smooth(DEPART - 0.3, DEPART + 0.4, t), ang = (-12 + 4 * Math.sin(t * 0.9) + 9 * dip - 22 * lean) * Math.PI / 180, ca = Math.cos(ang), sa = Math.sin(ang);
  const c: V2 = [p[0], p[1] + s * (0.06 * Math.sin(t * 1.9) - 0.16 * dip)], flap = 0.07 * Math.sin(t * 2.3) + 0.3 * dip - 0.25 * lean;
  const M = (x: number, y: number): V2 => [c[0] + (x * ca - y * sa) * s, c[1] + (x * sa + y * ca) * s], px = s * 720; // px: his half span at 1440p
  // CUT 2 (earth_c2_v2): drawn as the APPROVED 3D him's own silhouette, simplified (earth_him_wire's blueprint, build/him_wire/positions/
  // br_outline.json: a boxy bus, two wings of three panels on yokes, the round dish on top, the whip, the engine bell), so the small
  // him of the move-out is the same character as the 3D him of the hero shots and the bridge's outline. Units: his half span.
  const st = Math.max(0.0075, s * 0.034), sz = Math.max(4.6, px * 0.03);
  const W = (x: number, y: number): V2 => M(x, y - flap * (Math.abs(x) - 0.28) / 0.72); // a wing point: the tip rides the flap
  for (const sg of [-1, 1]) {
    line(flows, [W(sg * 0.28, 0.18), W(sg, 0.18), W(sg, -0.18), W(sg * 0.28, -0.18), W(sg * 0.28, 0.18)], st, sz, WARM, 1.35);
    for (const dx of [0.52, 0.76]) line(flows, [W(sg * dx, 0.18), W(sg * dx, -0.18)], st, sz * 0.8, WARM, 0.9);
    line(flows, [M(sg * 0.2, 0), W(sg * 0.28, 0)], st, sz, WARM, 1.2);                                              // the yoke
    for (const dx of [0.4, 0.64, 0.88]) flows.push(dot(W(sg * dx, 0), px * 0.36, WARM, 0.2));                        // panels: a little of his light in them
  }
  line(flows, [M(-0.2, 0.2), M(0.2, 0.2), M(0.2, -0.26), M(-0.2, -0.26), M(-0.2, 0.2)], st, sz * 1.1, WARMW, 1.5);  // the bus
  flows.push(dot(M(0, -0.03), px * 0.5, WARMW, 0.28));
  line(flows, Array.from({ length: 19 }, (_, i) => M(0.08 + 0.2 * Math.cos(i / 18 * Math.PI * 2 - Math.PI / 2), 0.42 + 0.2 * Math.sin(i / 18 * Math.PI * 2 - Math.PI / 2))), st, sz, WARM, 1.25); // the dish
  line(flows, [M(-0.06, -0.26), M(-0.1, -0.4), M(0.1, -0.4), M(0.06, -0.26)], st, sz, WARM, 1.2);                   // the engine bell
  line(flows, [M(-0.14, 0.2), M(-0.14, 0.7)], st, sz * 0.9, WARM, 1.1);                                             // the whip
  const blink = 0.35 + 0.65 * Math.pow(0.5 + 0.5 * Math.sin(t * 5.2), 4), tip = M(-0.14, 0.7);
  sparks.push(spark(tip[0], tip[1], { size: 8, color: [1.0, 0.6, 0.35], intensity: 1.6 * blink }));
  sparks.push(spark(c[0], c[1], { size: 20 + 2 * docked, intensity: 1.7 + 0.25 * docked + 0.9 * dockFlash + 0.1 * Math.sin(t * 31) })); // his core
  if (docked > 0) { const g = goOf(t, L); line(flows, [M(0, -0.4), ...Array.from({ length: docked }, (_, b) => { const d = dockOf(L, b, t); return [d[0] + g[0], d[1] + g[1]] as V2; })], 0.011, 3.6, WARM, 0.6); } // the string his parcels hang on
  if (t > DEPART - 0.3) { // his thruster, only when he goes
    const n = Math.hypot(L.away[0], L.away[1]), dx = L.away[0] / n, dy = L.away[1] / n, pl = s * (0.5 + 3.0 * Math.min(dep, 0.6)) * smooth(DEPART - 0.3, DEPART + 0.1, t) * (1 + 0.12 * Math.sin(t * 23));
    flows.push(flow({ space: 'screen', pts: [[c[0] - dx * pl, c[1] - dy * pl], c] }, 1, { tail: 1, count: 46, size: 9, color: [1.0, 0.7, 0.4], intensity: 1.3 }));
    if (dep > 0) flows.push(flow({ space: 'screen', pts: [[L.him[0], L.him[1]], c] }, 1, { tail: 0.7, count: 90, size: 4, color: C.his, intensity: 0.9 * (1 - smooth(0.5, 1.1, dep)) }));
  }
}
// the whole move-out as a function of time: boxes (outline, contents rising into them, label, tape), him and his parcels
export function moveOut(c: Ctx): { flows: Flow[]; sparks: Spark[]; packed: number } {
  const t = c.t, fmt = c.fmt, L = LAY[fmt], cs = camFor(fmt, c.base.cam), flows: Flow[] = [], sparks: Spark[] = [];
  const dep = Math.max(0, t - DEPART), go = goOf(t, L);
  if (dep > 1.3) return { flows, sparks, packed: 1 }; // gone: off screen up-right
  const limb = (x: number): V2 => { const dx = Math.max(-0.95, Math.min(0.95, (x - cs.x) / cs.r)) * cs.r; return [cs.x + dx, cs.y + 0.985 * Math.sqrt(cs.r * cs.r - dx * dx)]; };
  let packed = 0, dockFlash = 0;
  for (let b = 0; b < 4; b++) {
    if (t < DRAW[b]) continue;
    const g = fullOf(L, L.ground[b]), { box, e } = boxAt(b, t, fmt), draw = smooth(DRAW[b], DRAW[b] + 0.45, t), k = box.w / g.w;
    packed += smooth(SHIP[b], SHIP[b] + FLY + 0.3, t) / 4; dockFlash += hits(t, [SHIP[b] + FLY], 0.3, 0.05);
    const seal = hits(t, [KW[b]], 0.28, 0.1), open = 1;
    line(flows, corners(box), 0.0085, lerp(9, 5.5, e), BOXC, (2.0 + 1.6 * seal) * lerp(1, 0.8, e), draw);               // the box, drawn on; on his string it is a small taped parcel
    if (e > 0.5) flows.push(dot([box.cx, box.cy], box.h * 720 * 1.1, BOXC, 0.36 * smooth(0.5, 1, e)));                    // with a little of his light in it
    { // packing tape: two short stubs across the lid and the base, zipped on when the label lands
      const tp = smooth(KW[b] - 0.05, KW[b] + 0.2, t), len = L.pad[1] * 0.85 * k;
      if (tp > 0) for (const sg of [1, -1]) line(flows, [[box.cx, box.cy + sg * box.h / 2], [box.cx, box.cy + sg * (box.h / 2 - len)]], 0.008 * k, lerp(8, 4, e), BOXC, 1.8 * open, tp);
    }
    { // the label's body: a soft warm stroke under its stars, riding the box (LIGHT stays put when its box goes)
      const lv = smooth(KWL[b] - 0.1, KWL[b] + 0.14, t) * (b === 3 ? 1 - smooth(GAL_T, GAL_T + 0.3, t) : 1 - smooth(SHIP[b] + 0.12, SHIP[b] + 0.45, t));
      if (lv > 0.002) { const wl = wordOf(b, fmt), m = b === 3 ? g : box, q = m.w / g.w;
        for (const ln of wl.lines) line(flows, ln.map((p) => [m.cx + (p[0] - g.cx) * q, m.cy + (p[1] - g.cy) * (m.h / g.h)] as V2), wl.weight * 0.8 * q, wl.weight * 720 * 1.7 * q, WARMW, 0.42 * lv); }
    }
    const ts = DRAW[b] + 0.1, te = KW[b] + 0.25, yb = g.cy - g.h / 2;
    if (b < 3 && t > te + 0.4) continue; // contents only while the box is being filled on the ground
    const end = (j: number, n: number): V2 => [g.cx + g.w * 0.42 * (n === 1 ? 0 : (j / (n - 1)) * 2 - 1), yb];
    const src = (u: number): V2 => limb(g.cx + g.w * 0.6 * (u * 2 - 1));
    const mid = (p: V2, q: V2, kk: number): V2 => [lerp(p[0], q[0], 0.35) + kk * (q[0] - p[0]), lerp(p[1], q[1], 0.75)];
    if (b === 0) for (let j = 0; j < 22; j++) { // a billion chips: a swarm of small warm packets
      const p = src((j + SEED[j][0] * 0.8) / 22), q = end((j + (j % 3) * 2) % 22, 22);
      flows.push(...packets(bez(p, mid(p, q, 0.25), q, 12), t, ts + 0.3 * SEED[j][1], te, 0.55, 0.085, { tail: 0.05, count: 5, size: 8, color: PAL.ember, intensity: 1.9 }));
    }
    if (b === 1) for (let j = 0; j < 6; j++) { // the midnight appetite: fat gulps
      const p = src((j + 0.5) / 6), q = end(j, 6);
      flows.push(...packets(bez(p, mid(p, q, -0.2), q, 12), t, ts + 0.2 * SEED[j][1], te, 0.5, 0.13, { tail: 0.13, count: 10, size: 16, color: PAL.ember, intensity: 1.4 }));
    }
    if (b === 2) for (let j = 0; j < 3; j++) { // the 24-hour hum: waveforms that never sit still
      const p = src(0.2 + 0.6 * (j + 0.5) / 3), q = end(j, 3), on = 1 - smooth(KW[b], KW[b] + 0.3, t);
      const wob = (s: number) => 0.05 * (cs.r / 2) * Math.sin(Math.PI * s) * Math.sin(2 * Math.PI * (7 + 2 * j) * s - t * 15 + j * 2);
      line(flows, bez(p, mid(p, q, 0.1 * (j - 1)), q, 96, wob), 0.006, 7.5, PAL.filament, 1.9 * on, smooth(ts + 0.1 * j, ts + 0.5 + 0.1 * j, t));
    }
    if (b === 3) { // the never-ending light: beams that stay on until the box leaves
      const on = smooth(ts, ts + 0.5, t) * (1 - smooth(SHIP[3] - 0.25, SHIP[3], t));
      for (let j = 0; j < 7; j++) line(flows, [src((j + 0.5) / 7), end(j, 7)], 0.0075, 7, PAL.filament, 1.3 * on * (0.9 + 0.1 * Math.sin(t * 3 + j * 1.7)));
      sparks.push(spark(g.cx, g.cy, { size: 60, color: PAL.filament, intensity: 0.4 * on }));
    }
  }
  him(t, L, [L.him[0] + go[0], L.him[1] + go[1]], SHIP.filter((s) => t > s + FLY).length, dockFlash, dep, flows, sparks);
  return { flows, sparks, packed };
}
// her side of it: every box that leaves, she glows a little more (rain, green, aurora coming back)
export const herAfter = (t: number, packed: number) => ({ hisOff: 1, hisWarm: 0.5, herCyan: lerp(0.9, 1.35, packed), glow: lerp(1.0, 1.38, packed), forest: lerp(0.8, 2.0, packed), rivers: lerp(1.0, 1.35, packed),
  aurora: lerp(0, 0.7, packed), violet: 1, mist: 0.6, atmos: lerp(1.0, 1.3, packed), motes: lerp(0.4, 0.9, packed), kick: 0.6 * hits(t, SHIP.map((s) => s + FLY), 0.4) });
// the sky is kept quiet while the cast spells the labels (as chorus1.ts does for the rack): few deep stars, a little Milky Way mist
export const QUIET = { deep: 0.14, galaxy: 0.4, stars: 1.75 };
const pack: Builder = (c): Out => { const m = moveOut(c); return { flows: m.flows, sparks: m.sparks, grade: { ...herAfter(c.t, m.packed), ...QUIET, castWarm: 1 } }; };

const NIGHT: [number, number, number] = [0.5, -0.5, -0.7];
export const verse2: Section = {
  name: 'verse2',
  camera: [
    // A: cut to the low horizon over the Amazon basin (night side), drifting
    // (cut 2: low over the surface: r 2.9, the basin seen at a grazing angle below a wide horizon; was y -1.25, r 1.75, lat -40)
    { at: 'verse2a/L0', cam: { x: 0, y: -2.5, r: 2.9, lon: lonAt(-60, 'verse2a/L0'), lat: -64, roll: -3, sun: NIGHT, par: [0.2, 0.1] }, ease: 'hold' },
    { at: 'verse2a/L0/w5', cam: { y: -2.57, r: 2.98, lon: lonAt(-59, 'verse2a/L0/w5') }, ease: 'linear' },
    // B: follow the rain down into the forest, landing on "green"
    { at: 'verse2a/L1/w4+0.1', cam: { x: 0, y: 0, r: 2.4, lat: -5, lon: lonAt(-61, 'verse2a/L1/w4'), roll: -6 }, ease: 'smooth' },
    { at: 'verse2a/L2-0.02', cam: { r: 2.52 }, ease: 'linear' },
    // C: cut to his city lights (eastern North America at night); room up-right for the Zzz
    // (cut 2: low, looking north from over the Gulf; a slow creep forward; r 2.6: at 2.9 the city-light map shows its pixels. Was the full globe: x -0.5, y -0.25, r 1.05, lat 37)
    { at: 'verse2a/L2', cam: { x: -0.3, y: -2.1, r: 2.6, lon: lonAt(-91, 'verse2a/L2'), lat: -12, roll: -4, sun: [0.6, -0.4, -0.7], par: [-0.1, -0.15] }, ease: 'hold' },
    { at: 'verse2b/L0-0.02', cam: { y: -2.2, r: 2.72 }, ease: 'linear' },
    // D: cut to a low horizon, gliding; the boxes and the rocket live in the sky above it
    { at: 'verse2b/L0', cam: { x: 0, y: -2.3, r: 2.0, lon: lonAt(-95, 'verse2b/L0'), lat: -22, roll: 0, sun: [0.62, -0.25, -0.74], par: [0.1, 0.2] }, ease: 'hold' },
    { at: 'pre2/L0-0.02', cam: { lon: lonAt(-104, 'pre2/L0'), r: 2.06, y: -2.36, par: [0.04, 0.2] }, ease: 'linear' },
  ],
  stars: [
    { at: 'verse2a/L0', set: { kind: 'sky' }, dur: 3.2, straggle: 0.2, curve: 0.08 }, // post 1's crammed stars come home
    { at: 'verse2a/L2/w4-0.15', set: ZZZ, dur: 0.9, straggle: 0.15, curve: 0.2 },     // "sleep"
    { at: 'verse2a/L3/w4+0.1', set: { kind: 'sky' }, dur: 1.2, straggle: 0.2 },
    // ON the cut, in one step (a morph here lit the whole sky for a third of a second: the engine brightens stars that travel).
    // From the first frame of the shot the stage is clear; then the four labels, each star on its own clock (LABELSET).
    { at: 'verse2b/L0', set: LABELSET, dur: 0.001, straggle: 0, curve: 0 },
  ],
  builders: { v2_rain, v2_green, v2_sleep: sleep, v2_whirring: sleep, v2_chips: pack, v2_appetite: pack, v2_hum: pack, v2_light: pack },
};
withLookB(verse2.builders);
{ const B = verse2.builders, a2 = at('verse2a/L2'), b0 = LS[0];
  cutTo(B, 'v2_green', B.v2_sleep, 'v2_sleep', a2, at('verse2a/L3'));     // green -> his city lights
  cutTo(B, 'v2_whirring', B.v2_chips, 'v2_chips', b0, LS[1]);             // sleep -> the move-out
  // SEAM 2478 (post 1 -> verse 2; first cut 1 flag 2: "a cut, then the brightness settles 90 -> 42 over 14 frames"). The camera cuts
  // here, but the engine kept blending post 1's aurora shot (grade + curtains) over the rain for 0.45 s. From the cut on, po1_sky
  // now draws the rain shot, so the cut is clean in both formats. Only frames at or after verse2a/L0 change: post 1's own range is
  // untouched. (Done from this side because the frames are verse 2's; the same line could live in post.ts instead.)
  cutTo(post1.builders, 'po1_sky', B.v2_rain, 'v2_rain', at('verse2a/L0'), at('verse2a/L1')); }
