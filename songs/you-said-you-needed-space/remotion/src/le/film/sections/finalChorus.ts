// Final chorus: fc_space .. fc_atmos (earth_sec_fc, Sun Nov 8; polish earth_pol_fc, Mon Nov 9: lux look on every slot, the hero
// falls back from a close-up, star rain on "rain", a flower of stars on "bloom", the thread and the day reframed).
// Final chorus: The climax: she blooms on the downbeat and takes the room,
// then a beat-cut montage, one idea per sung line (rivers+rain, room to bloom, chips+heat leave, his dreams beyond her blue,
// the thread lets go, the smile, his day-long chase, all the life down here, his heat, her scarf of air).
// Shots are hard cuts on the line onsets (camera `hold` keys, lon compensated for the engine's spin); a slot that ends on a
// cut hands over to the next slot's builder after its own end, so the engine's 0.45 s slot blend never smears a cut.
// The ground-level montage can replace fc_life using native horizontal or vertical clips.
// The orbit montage still serves as the engine-only fallback.
import { PAL, Section, Builder, Ctx, Out, hits, smooth, lerp, env, spark, flow, C, RIVERS, clamp01 } from './api';
import { CamKey, SPIN_DEG_S, lerpCam, camFor } from '../camera';
import { words, at } from '../anchor';
import { TIMING } from '../timing.gen';
import { Cam, Flow, Fmt, GeoPt, Path, StarKey } from '../types';
import { Grade, RGB } from '../grade';
import { rng, starAttr, ASPECT, N_CAST } from '../stars';

const D = Math.PI / 180;
const L = (i: number) => at(`finalChorus/L${i}`);
const wt = (li: number) => words('finalChorus', li).map((w) => w[0]);
const W = (li: number, wi: number) => wt(li)[wi] ?? L(li);
const Q = (t: number) => Math.round(t * TIMING.fps) / TIMING.fps - 0.002; // a cut time snapped to the nearest frame
const DOWN = Q(at('finalChorus'));              // the chorus downbeat (176.17): "space" lands, she blooms (the cut, on the frame)
const BEAT = TIMING.bar / 4;
const beatsFrom = (t0: number, n: number) => Array.from({ length: n }, (_, i) => t0 + i * BEAT);
const mix = (a: RGB, b: RGB, u: number): RGB => [lerp(a[0], b[0], u), lerp(a[1], b[1], u), lerp(a[2], b[2], u)];
const F = <X>(c: { fmt: Fmt }, a: X, b: X) => (c.fmt === '169' ? a : b);
export const SUN0: [number, number, number] = [0.85, 0.25, -0.46];
const CAM0: Cam = { x: 0, y: 0, r: 0.8, lon: 0, lat: 0, roll: 0, sun: SUN0, par: [0, 0] };
// a shot: a hard cut at t0 to `a` (lon = the place facing the camera AT that time), drifting to `b` just before t1
function shot(t0: number, t1: number, a: Partial<Cam>, b?: Partial<Cam>, ease: CamKey['ease'] = 'linear'): CamKey[] {
  const A = { ...CAM0, ...a }, tq = Q(t0), te = Q(t1) - 0.004, B = { ...A, ...(b ?? {}) };
  return [{ at: tq, cam: { ...A, lon: A.lon - SPIN_DEG_S * tq }, ease: 'hold' }, { at: te, cam: { ...B, lon: B.lon - SPIN_DEG_S * te }, ease }];
}
// THE LOOK (polish, Nov 9): every slot of this file and of outro.ts sits on the approved lux planet (grade.lux: crisp veins +
// capillaries, the gold/rose dusk line, the deep star field and the Milky Way mist), as coldOpen..post1 do. A slot's own grade
// goes on top; `deep` / `galaxy` come down where a star drawing has to read (the flower, the countdown numbers).
export const LUXB: Partial<Grade> = { lux: 1, galaxy: 1, deep: 1, dust: 0, seam: 0.14, capil: 1 };
// the full-bloom look (style board pick 1: alive, not neon)
const FULL = { glow: 1.5, stars: 0.45, bloom: 0.72, // (earth_cut2, gate 3 in spirit: the final chorus passed the clip number but her river hearts read as flat white; glow 1.55 / bloom 0.8 before)
  atmos: 1.1, rivers: 1.5, forest: 1.4, ocean: 1.0, herCyan: 1.0, hisWarm: 0.3, violet: 0.85, motes: 0.9, mist: 0.35 };

// ---- a bloom of light veins growing over her surface from one point (geo space): "room to bloom" ----
type Twig = { path: Path; delay: number; k: number };
function tree(lat0: number, lon0: number, seed: number, nMain = 7, len = 9): Twig[] {
  const R = rng(seed), out: Twig[] = [];
  const grow = (lat: number, lon: number, ang: number, Ln: number, depth: number, delay: number) => {
    const pts: GeoPt[] = [[lat, lon]], n = 7; let a = ang;
    for (let i = 1; i <= n; i++) {
      a += (R() - 0.5) * 0.8; lat += Math.sin(a) * Ln / n; lon += Math.cos(a) * Ln / n / Math.max(0.3, Math.cos(lat * D)); pts.push([lat, lon]);
      if (depth < 2 && i >= 2 && R() < 0.42) grow(lat, lon, a + (R() < 0.5 ? -1 : 1) * (0.5 + R() * 0.7), Ln * 0.55, depth + 1, delay + (i / n) * (depth ? 0.25 : 0.5));
    }
    out.push({ path: { space: 'geo', pts, lift: 0.002 }, delay, k: depth === 0 ? 1 : depth === 1 ? 0.75 : 0.55 });
  };
  for (let k = 0; k < nMain; k++) grow(lat0, lon0, (k / nMain) * Math.PI * 2 + R() * 0.6, len * (0.7 + 0.6 * R()), 0, 0);
  return out;
}
const growFlows = (tw: Twig[], g: number, col: RGB, size: number, inten: number, count = 36): Flow[] =>
  tw.map((b) => flow(b.path, clamp01((g - b.delay) / 0.55), { tail: 1, color: col, size: size * b.k, intensity: inten * b.k * smooth(b.delay, b.delay + 0.1, g), count }));
const BLOOMS = [tree(-4, -62, 11, 8, 10), tree(3, -53, 23, 6, 7), tree(-12, -68, 37, 6, 7)];
const JUNGLE = tree(0.5, 22, 51, 7, 8);
const HEART = tree(3, 21, 77, 10, 30);
// a river running: light travelling down a geo polyline
const run = (pts: GeoPt[], t: number, t0: number, o: Partial<Flow> = {}) => flow({ space: 'geo', pts, lift: 0.002 }, smooth(t0, t0 + 1.5, t) * 1.35, { tail: 0.45, size: 6, intensity: 1.5, count: 150, ...o });
const NILE_UP = RIVERS.nile, CONGO = RIVERS.congo, NIGER = RIVERS.niger;
const ZAMBEZI: GeoPt[] = [[-11.5, 24.2], [-13.5, 23.2], [-16.0, 23.5], [-17.9, 25.9], [-16.5, 28.8], [-15.6, 30.4], [-16.2, 33.6], [-18.6, 36.3]];

// ---- the smile (cut 2: a CLOSE-UP of her face, and visibly rivers): tributaries run down her cheeks and join one braided,
// meandering channel that curls up into a smile (depth g overshoots and settles); light runs along it like a current ----
const smileY = (u: number, g: number) => -0.12 - 0.3 * g * Math.cos((u * Math.PI) / 2) + 0.016 * Math.sin(u * 9 + 0.6);
const smilePts = (g: number): [number, number][] => Array.from({ length: 25 }, (_, i) => { const u = (i / 24) * 2 - 1; return [u * 0.47, smileY(u, g)] as [number, number]; });
const TRIB_U = [-0.82, -0.5, -0.16, 0.2, 0.52, 0.84];
const tribPts = (k: number, g: number): [number, number][] => { const u = TRIB_U[k], x = u * 0.47, y = smileY(u, g), s = k % 2 ? 1 : -1, h = 0.27 + 0.06 * ((k * 7) % 3);
  return Array.from({ length: 8 }, (_, j) => { const v = 1 - j / 7; return [x + s * (0.1 * v * v + 0.022 * Math.sin(v * 7 + k) * v) + 0.03 * v, y + h * v + 0.012 * Math.sin(v * 9 + k * 2) * v] as [number, number]; }); };
const rot = (pts: [number, number][], deg: number) => { const c = Math.cos(deg * D), s = Math.sin(deg * D); return pts.map(([x, y]) => [c * x - s * y, s * x + c * y] as [number, number]); };

// ---- "all the life down here": three places, one per beat, each with its own light ----
const M0 = L(9), LIFE_T = [Q(M0), Q(M0 + BEAT), Q(M0 + 2 * BEAT), Q(L(10))];
const lifeIdx = (t: number) => (t < LIFE_T[1] ? 0 : t < LIFE_T[2] ? 1 : 2);
// the reef (cut 2: it was a dark sea with a few coast veins): strings of pearls of light along the Great Barrier Reef, lighting up from the middle out
const REEF: GeoPt[] = [[-10.4, 143.9], [-12.4, 144.3], [-14.3, 145.6], [-16.0, 146.3], [-17.8, 147.4], [-19.4, 149.0], [-20.9, 150.9], [-22.6, 152.4], [-24.2, 153.0]];
// six uneven chains (each wanders on its own, its own bead spacing and size), so it reads as a living reef and not as ruled lines
const REEF_J: number[][] = (() => { const R = rng(606); return Array.from({ length: 6 }, () => Array.from({ length: REEF.length * 2 + 3 }, () => R())); })();
const reefRow = (k: number): GeoPt[] => REEF.map(([la, lo], i) => [la + 0.26 * k + 0.75 * (REEF_J[k][i * 2] - 0.5), lo + 0.6 * k + 0.75 * (REEF_J[k][i * 2 + 1] - 0.5)] as GeoPt);
const reefFlows = (t: number, fmt: Fmt): Flow[] => { const g = clamp01((t - (LIFE_T[0] - 0.06)) / 0.3);
  return [0, 1, 2, 3, 4, 5].flatMap((k) => { const row = reefRow(k), J = REEF_J[k], N = 9 + Math.floor(J[18] * 14), mid = 2 + Math.floor(J[19] * 5);
    const col = [C.teal, C.her, mix(C.her, C.violet, 0.7), mix(C.her, C.white, 0.5), mix(C.teal, C.violet, 0.5), C.her][k] as RGB;
    return [row.slice(mid), row.slice(0, mid + 1).reverse()].map((h, j) => flow({ space: 'geo', pts: h, lift: 0.002 }, (1 + ((t * 0.12 + J[20] * 0.05 + j * 0.02) % (1 / N))) * g, { tail: 1, dash: N, size: F({ fmt }, 7 + 8 * J[17], 6 + 6.5 * J[17]), color: col, intensity: 1.5 + 0.8 * J[16], count: 220 })); }); };
// ---- the closing shot of the chorus and the whole outro are ONE camera path (pure function of time), shared with outro.ts ----
const CD = at('countdown'), CD0 = at('countdown/L0'), HOU = at('houston'), END = TIMING.duration;
const P_SCARF: Cam = { ...CAM0, x: 0.35, y: -0.45, r: 1.6, lon: 78, lat: 12, roll: -10, sun: [0.8, 0.3, -0.52] };   // cut 2: close on her shoulder (was one more centred globe)
const P_WIDE: Cam = { ...CAM0, x: -0.98, y: -0.7, r: 1.0, lon: 66, lat: 4, roll: -8, sun: [0.55, -0.1, -0.83] };
const P_HORIZON: Cam = { ...CAM0, x: 0.0, y: -1.58, r: 1.7, lon: 52, lat: -24, roll: 0, sun: [0.15, -0.4, -0.85] };
export const satPos = (fmt: Fmt, t: number): [number, number] => {
  const disconnect = TIMING.lines.countdown?.[3]?.words?.[2]?.[0] ?? at('countdown/L3') + 1.2;
  const punch = smooth(disconnect - 0.42, disconnect + 0.04, t);
  return fmt === '169' ? [lerp(-1.25, -1.01, punch), 0.62] : [-0.20, lerp(0.53, 0.45, punch)];
};
export function endCam(t: number): Cam {
  let c = lerpCam(P_SCARF, P_WIDE, smooth(L(11) + 0.35, CD0 - 0.5, t));       // the pull back IS the reveal: a ribbon of air passes, then she is wrapped
  c = lerpCam(c, P_HORIZON, smooth(CD0 + 0.2, HOU + 0.4, t));
  const s = smooth(HOU - 0.2, END - 0.2, t);                                 // the sunrise: the sun climbs over her limb
  return { ...c, y: c.y + 0.07 * smooth(HOU, END + 1.5, t), sun: [lerp(c.sun[0], 0.14, s), lerp(c.sun[1], 0.78, s), lerp(c.sun[2], -0.6, s)], lon: c.lon + 0.9 * (t - CD) };
}

// The engine brightens stars in flight (x2.5); when the whole sky rushes in to form a line's first number that is a white
// flash over the frame. Dip the star gain through each of those rushes so a number arrives as a sparkle, not a flash.
export const NUM_LEAD = 0.12, NUM_DUR = 0.28, NUM_DEEP = 0.15;   // NUM_DEEP: the deep star field under the star numbers (so they read)
const FORM = [0, 1, 2, 3].map((li) => at(`countdown/L${li}`) - NUM_LEAD);
export const starDip = (t: number) => 1 - 0.55 * Math.max(...FORM.map((f) => { const x = (t - f) / NUM_DUR; return x <= 0 || x >= 1 ? 0 : Math.sin(Math.PI * x) ** 2; }));

// ---- star arrangements, one per line (her Nov 8: "play with stars arrangement to get a point across") ----
// "got my RAIN": from "got" the whole cast of stars falls on her as rain (in front of her), slanted, each at its own speed
const RAIN0 = W(2, 3) - 0.06;
const wrap = (v: number, h: number) => ((((v + h) % (2 * h)) + 2 * h) % (2 * h)) - h;
const rainFn = (i: number, t: number, home: [number, number], _n: number, fmt: Fmt): [number, number] => {
  const A = starAttr(), s = Math.max(0, t - RAIN0), v = 0.85 + 1.5 * A.r2[i], fall = v * (s - 0.22 * (1 - Math.exp(-s / 0.22)));   // from rest, then steady
  return [wrap(home[0] - 0.2 * fall, ASPECT[fmt] * 1.06), wrap(home[1] - fall, 1.06)];
};
// ... and with them streaks of her own light (so a still reads as rain too): short slanted strokes falling the same way
const RS: number[][] = (() => { const R = rng(99); return Array.from({ length: 72 }, () => [R(), R(), R(), R()]); })();
const rainStreaks = (t: number, fmt: Fmt, k: number): Flow[] => { const A = ASPECT[fmt] * 1.06, s = Math.max(0, t - RAIN0);
  return k < 0.02 ? [] : RS.map(([a, b, c, d]) => { const v = 1.5 + 1.3 * c, y = wrap(1.06 - 2.12 * b - v * s, 1.06), x = wrap((a * 2 - 1) * A - 0.2 * v * s, A), ln = 0.14 + 0.16 * d;
    return flow({ space: 'screen', pts: [[x + 0.2 * ln, y + ln], [x, y]] }, 1, { tail: 1, size: F({ fmt }, 5, 4.2), color: mix(C.her, C.white, 0.45), intensity: 2.0 * k, count: 30 }); }); };
// "a little room to BLOOM": she is the heart of a flower and the stars are its petals. A tight bud on the cut, the 8 outer
// petals unwind and open through "a little room" (anticipation, overshoot, settle), 8 inner petals open into the gaps on
// "to bloom", and the whole flower swells on "bloom". Petal = an outline + a midrib, in screen units around her centre.
const NP = 8, FL_KEEP = 0.1;
export const FLOWER = { r: 0.4, y916: 0.125, R1: { '169': 0.95, '916': 0.5 } as Record<Fmt, number> };   // her radius (16:9), her 9:16 lift, the petal tips
const FR: number[] = (() => { const R = rng(4242); return Array.from({ length: N_CAST * 3 }, () => R()); })();
const back = (u: number) => { const c = 1.9, x = clamp01(u) - 1; return 1 + (c + 1) * x * x * x + c * x * x; };   // ease out with a small overshoot
const T_OPEN = L(3) + 0.1, T_IN = W(3, 4) - 0.1, T_BLOOM = W(3, 5);
// one petal at time t: (u along it 0..1, v across it -1..1) -> screen
const petal = (k: number, inner: boolean, t: number, fmt: Fmt) => {
  const R1 = FLOWER.R1[fmt], rH = fmt === '169' ? FLOWER.r : FLOWER.r * 0.62, cy = fmt === '169' ? 0 : FLOWER.y916 * 0.8;
  const sq = 0.05 * env(t, L(3) - 0.05, 0.08, 0.12);                                                  // the bud squeezes before it opens
  const o = inner ? 0.1 + 0.9 * back((t - T_IN) / 0.42) : 0.16 - sq + (0.84 + sq) * back((t - T_OPEN) / 0.62);
  const swell = 1 + 0.07 * env(t, T_BLOOM - 0.04, 0.1, 0.5) + 0.012 * Math.sin(t * 2.6 + k);
  const r0 = rH * 1.2, len = (inner ? 0.5 : 1) * (R1 - r0) * lerp(0.3, 1, o) * swell, wid = (inner ? 0.105 : 0.2) * R1 * lerp(0.3, 1, o) * swell;
  const th = ((k + (inner ? 0.5 : 0)) / NP) * Math.PI * 2 + Math.PI / 2 + (1 - Math.min(1, o)) * 0.95 + 0.05 * (t - L(3));   // unwinds as it opens, then turns slowly
  const c = Math.cos(th), sn = Math.sin(th);
  return (u: number, v: number): [number, number] => { const rho = r0 + len * u, tv = wid * v; return [c * rho - sn * tv, cy + sn * rho + c * tv]; };
};
const edge = (u: number) => Math.sin(Math.PI * Math.pow(u, 0.8)) * (1 - 0.22 * u);                    // the outline (a pointed tip)
const flowerFn = (i: number, t: number, home: [number, number], _n: number, fmt: Fmt): [number, number] => {
  if (starAttr().r3[i] < FL_KEEP) return home;
  const q = FR[i * 3], q2 = FR[i * 3 + 1], q3 = FR[i * 3 + 2], P = petal((i >> 2) % NP, i % 4 === 0, t, fmt);
  if (q3 < 0.14) return P(0.04 + 0.8 * q, (q2 - 0.5) * 0.02);                                         // the midrib
  const u = Math.pow(q, 0.85); return P(u, (q3 < 0.57 ? 1 : -1) * edge(u) + (q2 - 0.5) * 0.045);
};
// her own light in the petals, under the stars: a soft line down both edges of every petal (violet outside, cyan inside)
const petalGlow = (t: number, fmt: Fmt): Flow[] => [false, true].flatMap((inner) => Array.from({ length: NP }, (_, k) => { const P = petal(k, inner, t, fmt), N = 12;
  const loop = [...Array.from({ length: N }, (_, j) => P(j / (N - 1), edge(j / (N - 1)))), ...Array.from({ length: N - 1 }, (_, j) => { const u = 1 - (j + 1) / (N - 1); return P(u, -edge(u)); })];
  const o = { tail: 1, size: F({ fmt }, inner ? 9 : 11, inner ? 7 : 8.5), color: inner ? PAL.biolume : mix(PAL.biolume, PAL.aurora, 0.62), intensity: 2.3 * (inner ? smooth(T_IN - 0.05, T_IN + 0.3, t) : 1), count: inner ? 70 : 120 };
  return [flow({ space: 'screen', pts: loop }, 1, o), flow({ space: 'screen', pts: loop.slice().reverse() }, 1, o)]; }).flat());
// the room the stars give her on the downbeat (radius in screen units), also handed to the deep star field (grade.room)
const ROOM = { a: { '169': 1.2, '916': 0.8 } as Record<Fmt, number>, b: { '169': 1.32, '916': 0.9 } as Record<Fmt, number> };   // cut 2: b stays inside the frame so the EDGE of her room is seen
const roomR = (t: number, fmt: Fmt) => lerp(ROOM.a[fmt] * smooth(DOWN - 0.05, DOWN + 1.0, t), ROOM.b[fmt], smooth(L(1), L(1) + 1.5, t));

// ---- builders (all in absolute song time, so a slot can hand over to the next one at a cut) ----
const kick = (li: number, t: number, k = 0.3) => k * hits(t, wt(li), 0.3);
const raw: Record<string, Builder> = {
  // pickup "You said you needed space" over the low horizon: his stars still bright above her, she gathers; on the downbeat
  // (a cut to the wide) she blooms and the stars back away to give HER the room
  fc_space: (c) => {
    if (c.t < DOWN) {
      const g = smooth(L(0) - 0.2, DOWN - 0.35, c.t), breath = smooth(DOWN - 0.4, DOWN, c.t);
      return { grade: { glow: lerp(0.8, 1.2, g) - 0.35 * breath, stars: 1.4, mist: 1.0, atmos: 0.8 + 0.2 * g, hisWarm: 0.62, herCyan: 0.45, // (earth_cut2: hisWarm 1.15 made his cities one white blob)
        rivers: 1.2, riverPulse: 1.2, kick: 0.5 * hits(c.t, beatsFrom(DOWN - 4 * BEAT, 4), 0.25), bloom: 0.7, motes: 0.7, violet: 0.9, aurora: 0.25 * g }, motes: 'rise' };
    }
    return hero(c);
  },
  fc_too: (c) => hero(c),
  // "Got my rivers, got my rain": low over Africa, every river running toward us, then the rain as falling light
  fc_rivers: (c) => {
    const rain = smooth(W(2, 3) - 0.1, W(2, 5), c.t);
    return { grade: { ...FULL, glow: 1.38, stars: lerp(0.8, 1.7, rain) * (1 - 0.5 * Math.sin(Math.PI * clamp01((c.t - RAIN0) / 0.35)) ** 2), deep: lerp(1, 0.55, rain), rivers: 1.9, riverPulse: 1.6, kick: kick(2, c.t, 0.35), mist: 1.0, motes: lerp(0.8, 2.2, rain), atmos: 0.9, aurora: 0.3 }, motes: rain > 0.05 ? 'rain' : 'drift',
      flows: [run(NILE_UP, c.t, L(2) - 0.1), run(CONGO, c.t, L(2) + 0.15), run(NIGER, c.t, L(2) + 0.35), run(ZAMBEZI, c.t, L(2) + 0.5, { color: mix(C.her, C.violet, 0.4) }), ...rainStreaks(c.t, c.fmt, rain)] };
  },
  // "Got a little room to bloom": WIDE (the close Amazon dive was soft at 1:1): she is the heart of a flower of stars. Veins of
  // light grow over her from three hearts as the petals open; rings cross her on "room" and "bloom"
  fc_bloom: (c) => {
    const g = (c.t - (L(3) + 0.05)) / 1.1, tb = T_BLOOM, sw = env(c.t, tb - 0.04, 0.1, 0.5);
    return { cam: F(c, {}, { y: FLOWER.y916 }),
      grade: { ...FULL, glow: 1.75 + 0.3 * sw, violet: 1, ocean: 1.5, herCyan: 1.25, haloWide: 0.4 + 0.3 * sw, // (earth_cut2, gate 7: her peak, the most saturated frame of the film; petals Biolume -> Aurora)
        forest: lerp(1.2, 2.4, smooth(L(3), tb, c.t)), rivers: 1.7, riverPulse: 1.2, kick: kick(3, c.t, 0.25), motes: 0.5, mist: 0.2, aurora: 0.5,
        stars: 1.5 + 0.4 * sw, deep: 0.14, galaxy: 0.45, flare: 0.25 * sw },
      flows: [...growFlows(BLOOMS[0], g, C.teal, 2.6, 1.0, 22), ...growFlows(BLOOMS[1], g - 0.25, mix(C.her, C.violet, 0.45), 2.4, 0.9, 22), ...growFlows(BLOOMS[2], g - 0.4, C.her, 2.4, 0.9, 22), ...petalGlow(c.t, c.fmt)],
      pulses: [{ lat: -4, lon: -62, t0: W(3, 3) - 0.3, speed: 30, strength: 0.4 }, { lat: -4, lon: -62, t0: tb - 0.2, speed: 60, strength: 0.6 }] };
  },
  // "Take your chips and take your heat": his warm chips lift off her cities in packets to his waiting satellite (he = the satellite); on "heat" his
  // warm city lights go out city by city and her cyan takes the dark
  fc_chips: (c) => {
    const tgt = F(c, [1.62, 1.12], [0.52, 1.72]) as [number, number], heat = smooth(W(4, 4), L(5) - 0.1, c.t);
    const src: [number, number][] = [[0.18, 0.52], [0.42, 0.36], [0.05, 0.3], [0.33, 0.62], [-0.12, 0.48], [0.5, 0.12], [0.22, 0.12], [-0.02, 0.68]];
    const streams = src.map(([x, y], i) => { const bend: [number, number] = [lerp(x, tgt[0], 0.45) - 0.12 + 0.05 * (i % 3), lerp(y, tgt[1], 0.45) + 0.2 - 0.04 * (i % 4)];
      return flow({ space: 'rel', pts: [[x, y], [lerp(x, bend[0], 0.5), lerp(y, bend[1], 0.5) + 0.03], bend, [lerp(bend[0], tgt[0], 0.6), lerp(bend[1], tgt[1], 0.6) + 0.03], tgt] }, clamp01((c.t - (L(4) - 0.1 + i * 0.06)) / 1.7) * 1.75, { tail: 0.75, dash: 6, size: F(c, 12, 10), color: mix(PAL.ember, PAL.overheat, 0.35 * heat), intensity: 2.2, count: 170 }); }); // (earth_cut2: his chips leave in Ember)
    return { grade: { ...FULL, glow: 1.45, stars: 0.75, hisWarm: lerp(0.7, 0.45, heat), herCyan: lerp(0.5, 1.2, heat), hisOff: 0.92 * heat, kick: kick(4, c.t, 0.2), aurora: 0.2 },
      flows: streams, sparks: [spark(0, 0, { rel: tgt, size: 24 + 8 * hits(c.t, wt(4), 0.2), color: mix(PAL.filament, PAL.overheat, 0.3 * heat), intensity: 2.0 }), spark(0, 0, { rel: tgt, size: 150, color: PAL.ember, intensity: 0.3 })] };
  },
  // "Take your dreams beyond the blue": 16:9: her blue limb stands down the LEFT of the frame (a side limb, not one more horizon) and his
  // spark climbs away from it into the open sky; 9:16: her blue limb across the bottom, he climbs straight up
  fc_dreams: (c) => {
    const u = smooth(L(5) - 0.1, L(6), c.t), a = F(c, [1.02, 0.2], [0.2, 1.045]), b = F(c, [1.52, 0.5], [0.36, 1.36]), p: [number, number] = [lerp(a[0], b[0], u), lerp(a[1], b[1], u)];
    const o = F(c, [[1.0, 0.13], [1.012, 0.165]], [[0.12, 1.0], [0.16, 1.03]]) as [number, number][];
    return { cam: F(c, {}, { x: -0.25, y: lerp(-1.3, -1.62, u), r: 1.75, lat: -34, lon: 121 + 2 * u, roll: 7 }),
      grade: { ...FULL, glow: 1.5, ocean: 3.6, coast: 2.4, violet: 0.6, atmos: 1.9, haloWide: 0.45, aurora: 0.3, stars: lerp(0.7, 1.6, u), mist: 1.0, kick: kick(5, c.t, 0.2) },
      sparks: [spark(0, 0, { rel: p, size: lerp(34, 16, u), intensity: lerp(2.2, 1.6, u) }), spark(0, 0, { rel: p, size: lerp(120, 60, u), intensity: 0.3 })],
      flows: [flow({ space: 'rel', pts: [o[0], o[1], [lerp(o[1][0], p[0], 0.5) + F(c, 0, 0), lerp(o[1][1], p[1], 0.5) + 0.01], p] }, 1, { tail: lerp(0.5, 0.95, u), dash: 8, size: F(c, 9, 7.5), color: PAL.ember, intensity: 2.2, count: 260 })] };
  },
  // "I don't need to hold you down": the one thread of light still tied to her (br_began) lets go on "hold" and reels up into him
  fc_hold: (c) => {
    const tr = W(6, 4), k = smooth(tr, tr + 1.0, c.t), her0 = F(c, [-0.5, 0.866], [-0.17, 0.985]) as [number, number];
    const him = F(c, [lerp(-1.0, -1.075, k), lerp(1.125, 1.15, k)], [lerp(-0.3, -0.34, k), lerp(1.3, 1.36, k)]) as [number, number];   // cut 2: room around him (3D him, not the corner)
    const sag = 0.1 * k + 0.02 * Math.sin(c.t * 5) * k, n = 12;
    const pts = Array.from({ length: n + 1 }, (_, i) => { const u = i / n, w = Math.sin(u * Math.PI); return [lerp(him[0], her0[0], u) - sag * w, lerp(him[1], her0[1], u) - 1.2 * sag * w] as [number, number]; });
    return { cam: F(c, {}, { y: -1.06, r: 2.1 }), grade: { ...FULL, glow: 1.4 + 0.3 * env(c.t, tr, 0.15, 0.9), stars: 0.9, mist: 0.9, kick: kick(6, c.t, 0.2), atmos: 1.1 + 0.5 * env(c.t, tr, 0.15, 0.9), aurora: 0.3 },
      flows: [flow({ space: 'rel', pts }, 1 - k, { tail: 1, size: 7, color: C.her, intensity: 2.2, count: 520 }), flow({ space: 'rel', pts: pts.slice().reverse() }, 1, { tail: 1 - k, size: 6, color: mix(C.her, C.white, 0.25), intensity: 1.6, count: 520 })],
      sparks: [spark(0, 0, { rel: him, size: lerp(20, 11, k), intensity: 1.9 }), spark(0, 0, { rel: her0, size: 9 + 12 * env(c.t, tr, 0.08, 0.5), color: C.her, intensity: 1.2 * (1 - k) + 1.5 * env(c.t, tr, 0.08, 0.5) })],
      pulses: [{ lat: 54, lon: 8, t0: tr - 0.2, speed: 22, strength: 0.6 }] };
  },
  // "I've got better things to do": CLOSE on her face (cut 2: it was one more centred globe). Tributaries run down her cheeks on
  // "I've got", join into one channel that curls up into a smile on "better things" (overshoot, settle), a current of light keeps
  // running along it; two lakes for eyes; she tilts her head and winks on "do"
  fc_better: (c) => {
    const T0 = W(7, 0), d = smooth(T0 + 0.1, W(7, 3) - 0.05, c.t), g = 0.55 + 0.45 * back((c.t - (T0 + 0.25)) / 0.7), tilt = c.base.cam.roll;
    const wink = env(c.t, W(7, 5), 0.07, 0.25, W(7, 5) + 0.12), eyes = smooth(T0 - 0.2, T0 + 0.12, c.t), done = smooth(0.85, 1, d);
    const sc = F(c, 1, 0.84), S = (pts: [number, number][]) => rot(pts.map(([x, y]) => [x * sc, y * sc] as [number, number]), tilt);   // 9:16: the whole face a little smaller (inside the frame)
    const braid = (k: number) => S(smilePts(g).map(([x, y], i) => [x, y + k * (0.02 + 0.014 * Math.sin(i * 0.9 + k * 2)) * Math.sin((i / 24) * Math.PI)] as [number, number]));   // strands part in the middle, meet at the corners
    const mid = braid(0), half = (dir: number) => (dir > 0 ? mid.slice(12) : mid.slice(0, 13).reverse());   // the channel grows from the middle out to both corners
    const N = 7, cur = (c.t * 0.3) % (1.0 / N), eye = (sx: number) => S([[sx * 0.2, 0.22]])[0], drain = smooth(T0, W(7, 3), c.t);   // drain: her veins dim as their light runs into the smile
    return { grade: { ...FULL, glow: lerp(1.35, 0.95, drain), rivers: lerp(1.6, 0.35, drain), forest: lerp(1.3, 0.45, drain), capil: lerp(1, 0.25, drain), herCyan: lerp(1, 0.7, drain), kick: kick(7, c.t, 0.15), aurora: 0.5, stars: 0.5, haloWide: 0.2 },
      flows: [
        // the tributaries come first, running DOWN to where the channel will be
        ...TRIB_U.map((_, k) => flow({ space: 'rel', pts: S(tribPts(k, g)) }, 1.0 * smooth(T0 - 0.12 + 0.03 * k, T0 + 0.3 + 0.03 * k, c.t), { tail: 1, size: F(c, 8, 6.5), color: mix(C.her, C.teal, 0.3), intensity: 1.5 * smooth(T0 - 0.1 + 0.03 * k, T0 + 0.05 + 0.03 * k, c.t), count: 110 })),
        ...TRIB_U.map((_, k) => flow({ space: 'rel', pts: S(tribPts(k, g)).reverse() }, 1, { tail: Math.max(0.001, smooth(T0 - 0.12 + 0.03 * k, T0 + 0.3 + 0.03 * k, c.t)), size: F(c, 7, 5.5), color: C.her, intensity: 1.2 * eyes * smooth(T0 - 0.1 + 0.03 * k, T0 + 0.05 + 0.03 * k, c.t), count: 90 })),
        // the channel: three braided strands, drawn from the middle out, lit evenly (two opposed flows each)
        ...[-1, 0, 1].flatMap((k) => { const b = braid(k), o = { size: F(c, k ? 10 : 16, k ? 8 : 12.5), color: k ? C.her : mix(C.her, C.white, 0.3), count: 250 };
          return [b.slice(12), b.slice(0, 13).reverse()].flatMap((h) => [flow({ space: 'rel', pts: h }, d * 1.02, { tail: 1.02, ...o, intensity: 1.35 }), flow({ space: 'rel', pts: h.slice().reverse() }, 1, { tail: Math.max(0.001, d), ...o, intensity: 1.1 * d })]); }),
        // the current: packets of light running from the middle to the corners of her mouth
        ...[1, -1].map((dir) => flow({ space: 'rel', pts: half(dir) }, 1 + cur, { tail: 1.0, dash: N, size: F(c, 6, 5), color: C.white, intensity: 1.5 * done, count: 150 }))],
      sparks: [spark(0, 0, { rel: eye(-1), size: F(c, 30, 24), color: mix(C.her, C.white, 0.5), intensity: 1.8 * eyes }), spark(0, 0, { rel: eye(-1), size: F(c, 90, 70), color: C.her, intensity: 0.3 * eyes }),
        spark(0, 0, { rel: eye(1), size: F(c, 30, 24) * (1 - 0.75 * wink), color: mix(C.her, C.white, 0.5), intensity: 1.8 * eyes * (1 - 0.85 * wink) }), spark(0, 0, { rel: eye(1), size: F(c, 90, 70), color: C.her, intensity: 0.3 * eyes * (1 - wink) })] };
  },
  // "Go on, chase the sun all day": the day sweeps across her in two seconds (it stops with her night veins still alight on the
  // left: the plain sunlit photo never takes the whole face); his satellite runs over her top limb toward the sun on her right limb,
  // always a step behind it (against the dark sky: on her sunlit face he was white on white)
  fc_sun: (c) => {
    const a = lerp(-38, 30, smooth(L(8) - 0.1, L(9), c.t)) * D, H = 0.42, ch = Math.sqrt(1 - H * H), day = smooth(-0.35, 0.75, Math.sin(a));   // day: how much of her face is sunlit
    const run = smooth(L(8) - 0.3, L(9) + 0.2, c.t), th = (lerp(F(c, 152, 126), F(c, 40, 58), run) + 1.2 * Math.sin(c.t * 7)) * D, q = (d: number): [number, number] => [1.085 * Math.cos(th + d * D), 1.085 * Math.sin(th + d * D)];
    return { cam: { sun: [Math.cos(a) * 0.92, 0.38, Math.sin(a) * 0.92], ...F(c, {}, { y: -0.36 }) }, grade: { ...FULL, glow: lerp(1.5, 1.15, day), daySide: 0.34, sunWarm: 0.75, seam: 0.45, stars: 0.6, /* earth_cut2 / fresh eyes: at daySide 0.8+ her sunlit half turned into a tan photo of Earth, 'a different film'; now warm light over her still-glowing veins */ kick: kick(8, c.t, 0.2), atmos: lerp(1.1, 0.55, day), clouds: 0.14, bloom: lerp(0.7, 0.36, day), exposure: lerp(1, 0.6, day) },
      sparks: [spark(0, 0, { rel: q(0), size: 24, color: PAL.filament, intensity: 2.6 }), spark(0, 0, { rel: [ch, H + 0.02], size: F(c, 150, 110), color: PAL.filament, intensity: lerp(0.9, 1.15, day) }), spark(0, 0, { rel: [ch, H + 0.02], size: F(c, 560, 420), color: PAL.ember, intensity: lerp(0.12, 0.2, day) })],
      flows: [flow({ space: 'rel', pts: [q(26), q(17), q(8), q(0)] }, 1, { tail: 1, size: 6, color: PAL.ember, intensity: 2.3, count: 140 })] };
  },
  // "I've got all the life down here": reef / jungle / ice, one per beat, a flash of her light on each cut
  fc_life: (c) => {
    const i = lifeIdx(c.t), hit = Math.exp(-(c.t - LIFE_T[i]) / 0.16);
    if (i === 0) return { grade: { ...FULL, glow: 1.42, ocean: 3.6, coast: 2.6, violet: 1, forest: 0.8, flare: 0.32 * hit, motes: 1.2, stars: 0.4 }, flows: reefFlows(c.t, c.fmt), pulses: [{ lat: -17.5, lon: 147.5, t0: LIFE_T[0] - 0.12, speed: 16, strength: 0.6 }] };
    if (i === 1) return { grade: { ...FULL, glow: 1.3, forest: 2.2, rivers: 1.85, riverPulse: 1.5, flare: 0.3 * hit, motes: 1.4, stars: 0.4 }, motes: 'rise',
      flows: [run(CONGO, c.t, LIFE_T[1] - 0.3, { size: 7 }), ...growFlows(JUNGLE, (c.t - LIFE_T[1]) / 0.5 + 0.35, C.teal, 4.5, 1.3, 30)], pulses: [{ lat: 0.5, lon: 22, t0: LIFE_T[1] - 0.4, speed: 14, strength: 0.5 }] };
    return { grade: { ...FULL, glow: 1.22, daySide: 0.5, aurora: 2.6, atmos: 1.0, violet: 1, ocean: 1.6, flare: 0.35 * hit, stars: 0.9, mist: 1.6, motes: 1.0 } };
  },
  // "Who's gonna cool you down up there?": we look up at him for once: a lone warm spark heating to red; her cool air far below
  fc_cool: (c) => {
    const h = smooth(L(10), L(11), c.t), fl = 1 + 0.25 * Math.sin(c.t * 31) * h;
    const p = F(c, [lerp(-0.8, -0.9, h), lerp(0.36, 0.46, h)], [lerp(-0.14, -0.2, h), lerp(0.36, 0.44, h)]) as [number, number];   // cut 2: upper LEFT, his side of the sky from here to the end
    return { grade: { ...FULL, glow: 1.3, atmos: 1.15, mist: 1.8, violet: 1, ocean: 1.8, stars: 1.0, kick: kick(10, c.t, 0.25), aurora: 0.45 },
      sparks: [spark(p[0], p[1], { size: (18 + 14 * h) * fl, color: mix(C.his, C.red, h), intensity: 1.7 + 0.9 * h }), spark(p[0], p[1], { size: F(c, 170, 130) * h, color: C.red, intensity: 0.55 * h * fl })] };
  },
  // "You've got no atmosphere": her air wraps her like a scarf (two ribbons and a loose end); his satellite, red, drifts off and goes dark
  fc_atmos: (c) => scarf(c),
};
// the hero frame: full disk, full bloom; rings of light cross her, the stars back away and dim (she outshines them)
function hero(c: Ctx): Out {
  const s = c.t - DOWN, swell = Math.exp(-Math.max(0, s) / 0.5);
  return { grade: { ...FULL, room: roomR(c.t, c.fmt) / 1.099, roomX: 0, roomY: 0, roomKeep: 0.16, haloWide: 0.35 + 0.4 * swell, glow: 1.42 + 0.26 * swell + 0.2 * env(c.t, L(1), 0.2, 0.9), flare: 0.24 * Math.exp(-Math.max(0, s) / 0.22), // (earth_cut2: the downbeat bloom whited out Africa for 0.4 s)
      stars: lerp(1.3, 0.3, smooth(0, 0.9, s)) + 0.55 * smooth(1.2, 2.2, s),   // cut 2: the stars come back up at the edge of her room (the room must read) atmos: 1.2 + 0.7 * swell, aurora: 1.0 * smooth(0.2, 1.6, s),
      bloom: 0.72 + 0.16 * swell, motes: 1.3, rivers: 1.85, riverPulse: 1.4, forest: 2.0, ocean: 1.9, coast: 1.6, herCyan: 1.2, kick: 0.4 * hits(c.t, beatsFrom(DOWN, 6), 0.25) }, motes: 'rise',
    // soft rings that light her rivers and forests as they pass (kept faint: light moving through her, not circles drawn on her)
    flows: growFlows(HEART, s / 1.25, mix(C.her, C.teal, 0.4), 6, 1.1 * (1 - smooth(1.9, 3.0, s)), 60),
    pulses: [{ lat: 2, lon: 20, t0: DOWN - 0.15, speed: 40, strength: 0.5 }, { lat: 30, lon: 5, t0: DOWN + 0.45, speed: 32, strength: 0.4 }, { lat: -15, lon: 30, t0: L(1) - 0.1, speed: 36, strength: 0.45 }, { lat: 15, lon: 40, t0: L(1) + 0.6, speed: 30, strength: 0.35 }] };
}
// the scarf (also the first seconds of the path into the countdown): camera = endCam.
// Cut 2: the same cloth as chorus 1's scarf (one broad soft band of her light, big soft sprites sized to her radius on screen, fine
// threads on top), thrown across her front from her near shoulder; the loose end flies off her far shoulder and keeps flapping.
// The shot starts close on her shoulder as the band sweeps past the lens and pulls back to see her wrapped (endCam). He hangs
// red-hot at ONE fixed place in the sky (satPos) from here to "disconnected".
const SC_N = 56, SC_TILT = { '169': 20 * D, '916': 58 * D } as Record<Fmt, number>, SC_FRONT = 0.7;   // 9:16: steeper, so the loose end flies UP inside the frame
function scarfPath(t: number, i: number, fmt: Fmt): [number, number][] {
  const A = 1.035, off = (i - 2) * 0.016, c = Math.cos(SC_TILT[fmt]), sn = Math.sin(SC_TILT[fmt]), pts: [number, number][] = [];
  for (let j = 0; j <= SC_N; j++) {
    const u = j / SC_N; let x: number, y: number;
    if (u <= SC_FRONT) { const a = lerp(192, -12, u / SC_FRONT) * D;   // across her front
      x = A * Math.cos(a); y = A * Math.sin(a) * 0.46 + 0.018 * Math.sin(5 * a + 1.6 * t + i * 0.5) + off; }
    else { const v = (u - SC_FRONT) / (1 - SC_FRONT), a = -12 * D;      // the loose end: off her far shoulder, lifting and flapping
      x = A * Math.cos(a) + (fmt === '169' ? 0.5 : 0.4) * v; y = A * Math.sin(a) * 0.46 + 0.1 * v - 0.16 * v * v + 0.06 * v * Math.sin(9 * v - 3.2 * t + i * 0.3) + off * (1 + 2.5 * v); }
    pts.push([c * x - sn * y, sn * x + c * y]);
  }
  return pts;
}
export function scarf(c: { t: number; fmt: Fmt }): Out {
  const t = c.t, t0 = L(11), out = 1 - smooth(CD0 - 0.45, CD0 + 0.45, t), away = smooth(t0, CD0, t);
  const cam = endCam(t), r = camFor(c.fmt, cam).r, dens = Math.min(1.05, Math.max(0.5, F(c, 1.0, 0.8) / r)), sp = satPos(c.fmt, t),   // dens: the close-up must not burn out
  fl = 1 + 0.2 * Math.sin(t * 29) + 0.12 * Math.sin(t * 53);
  const cloth = [0, 1, 2, 3, 4].flatMap((i) => { const pts = scarfPath(t, i, c.fmt), w = smooth(t0 - 0.05 + 0.04 * i, t0 + 1.25 + 0.04 * i, t), col = mix(PAL.biolume, PAL.aurora, 0.12 + 0.19 * i);
    const o = { size: (118 - 8 * Math.abs(i - 2)) * (r / 1.1), intensity: 0.072 * out * dens * (1 - 0.18 * Math.abs(i - 2)), count: 250, color: col }; // (earth_cut2, gate 7: the scarf added up to white; held in her Biolume -> Aurora)
    const th = { size: 5.5, intensity: 0.4 * out * dens, count: 230, color: mix(col, C.white, 0.12) };
    return [flow({ space: 'rel', pts }, 1.03 * w, { tail: 1.03, ...o }), flow({ space: 'rel', pts: pts.slice().reverse() }, 1, { tail: Math.max(0.001, w), ...o, intensity: o.intensity * smooth(0, 0.15, w) }),
      ...(i % 2 === 0 ? [flow({ space: 'rel', pts }, 1.03 * w, { tail: 1.03, ...th }), flow({ space: 'rel', pts: pts.slice().reverse() }, 1, { tail: Math.max(0.001, w), ...th, intensity: th.intensity * smooth(0, 0.15, w) })] : [])]; });
  const w = smooth(t0 - 0.05, t0 + 1.3, t);
  return { cam, grade: { ...FULL, glow: 1.45, atmos: lerp(1.1, 1.5, w) * lerp(0.85, 1, out), aurora: 0.9 * w * lerp(0.3, 1, out), violet: 1, stars: lerp(0.5, 1.6, 1 - out) * starDip(t), deep: lerp(1, NUM_DEEP, smooth(CD0 - 1.4, CD0 - 0.2, t)), galaxy: lerp(1, 0.5, smooth(CD0 - 1.4, CD0 - 0.2, t)), kick: kick(11, t, 0.25) },
    flows: cloth,
    sparks: [spark(sp[0], sp[1], { size: (20 - 3 * away) * fl, color: mix(C.red, C.his, 0.45 * smooth(CD0 - 1.2, CD0 + 0.3, t)), intensity: 2.0 }),
      spark(sp[0], sp[1], { size: F(c, 150, 115) * (1 - 0.6 * away), color: C.red, intensity: 0.5 * (1 - 0.7 * away) * fl })] };
}

// A slot that ends on a hard cut hands over to the next slot's builder once its own time is up, so the engine's 0.45 s slot
// blend (engine.ts BLEND_S) never smears a cut. During that blend the engine draws previous*(1-u) + next*u and concatenates
// pulses, which would double the pulses and the particle count (the scarf alone is ~7.6k of the 9k budget). So the PREVIOUS
// slot carries the new shot alone through the blend (its flows/sparks pre-divided by the engine's 1-u), and the new slot
// stays empty of flows/sparks/pulses until the blend is over. Net: the exact frame, once.
const BLEND = 0.45;
const ORDER = ['fc_space', 'fc_too', 'fc_rivers', 'fc_bloom', 'fc_chips', 'fc_dreams', 'fc_hold', 'fc_better', 'fc_sun', 'fc_life', 'fc_cool', 'fc_atmos'];
const CUT_INTO = new Set(['fc_rivers', 'fc_bloom', 'fc_chips', 'fc_dreams', 'fc_hold', 'fc_better', 'fc_sun', 'fc_life', 'fc_cool', 'fc_atmos']);
const builders: Record<string, Builder> = {};
const lux = (b: Builder): Builder => (c) => { const o = b(c); return { ...o, grade: { ...LUXB, ...(o.grade ?? {}) } }; };
ORDER.forEach((id, i) => {
  const nx = ORDER[i + 1];
  builders[id] = lux((c) => {
    if (nx && CUT_INTO.has(nx) && c.t >= Q(c.slot.t1)) {
      const o = raw[nx](c), u0 = clamp01((c.t - c.slot.t1) / BLEND), k = 1 / Math.max(1e-4, 1 - u0 * u0 * (3 - 2 * u0));
      return { ...o, flows: (o.flows ?? []).map((f) => ({ ...f, intensity: f.intensity * k })), sparks: (o.sparks ?? []).map((f) => ({ ...f, intensity: f.intensity * k })) };
    }
    const o = raw[id](c), blending = c.t - c.slot.t0 < BLEND;
    if (blending && CUT_INTO.has(id)) return { ...o, flows: [], sparks: [], pulses: [] };
    if (blending && id === 'fc_too') return { ...o, pulses: [] };            // fc_space is still drawing the same hero pulses
    return o;
  });
});

// the stars: on the downbeat they back away from her (the cold open's move, now hers), wider on "I needed it too"; home at the cut
const roomFn = (R169: number, R916: number) => (_i: number, _t: number, home: [number, number], _n: number, fmt: Fmt): [number, number] => {
  const R = fmt === '169' ? R169 : R916, r = Math.hypot(home[0], home[1]) || 1e-6, r2 = Math.cbrt(r * r * r + R * R * R); return [(home[0] / r) * r2, (home[1] / r) * r2]; };
const SKY = { kind: 'sky' as const };
const stars: StarKey[] = [
  { at: Q(L(0)) - 0.031, set: SKY, dur: 0.03 },          // (a snap that completes exactly on the cut frame)
  { at: DOWN - 0.05, set: { kind: 'fn', fn: roomFn(ROOM.a['169'], ROOM.a['916']) }, dur: 1.3, straggle: 0.3, curve: 0.1 },
  { at: L(1), set: { kind: 'fn', fn: roomFn(ROOM.b['169'], ROOM.b['916']) }, dur: 1.7, straggle: 0.3, curve: 0.1 },
  { at: Q(L(2)) - 0.031, set: SKY, dur: 0.03, straggle: 0 },
  { at: RAIN0, set: { kind: 'fn', fn: rainFn, front: true }, dur: 0.35, straggle: 0, curve: 0 },          // "got my rain"
  { at: Q(L(3)) - 0.031, set: { kind: 'fn', fn: flowerFn, front: true }, dur: 0.03, straggle: 0, curve: 0 },   // the bud is there on the cut frame
  { at: Q(L(4)) - 0.031, set: SKY, dur: 0.03, straggle: 0 },
];

export const finalChorus: Section = {
  name: 'finalChorus',
  camera: [
    // pickup: low horizon, rising a little
    ...shot(L(0), DOWN, { x: 0.05, y: -1.44, r: 1.7, lat: 0, lon: -88, roll: 2, sun: [-0.5, -0.3, -0.81] }, { y: -1.32, lon: -86 }),
    // downbeat: a cut INTO her blooming face, then we fall back fast as the stars back away (she takes the room); a slow drift out through "needed it too"
    { at: DOWN, cam: { ...CAM0, r: 1.62, lat: 6, lon: 16 - SPIN_DEG_S * DOWN, roll: -8, sun: SUN0 }, ease: 'hold' },
    { at: DOWN + 1.35, cam: { r: 0.78, lon: 17 - SPIN_DEG_S * (DOWN + 1.35), roll: -7 }, ease: 'out' },
    { at: Q(L(2)) - 0.004, cam: { r: 0.54, lon: 19 - SPIN_DEG_S * Q(L(2)), roll: -6 }, ease: 'smooth' },   // cut 2: no hold on a centred globe: she gets small in the room she asked for
    ...shot(L(2), L(3), { x: 0.3, y: -1.3, r: 1.8, lat: -33, lon: 25, roll: -9, sun: [-0.5, -0.2, -0.84] }, { y: -1.22, lon: 28 }),
    ...shot(L(3), L(4), { x: 0, y: 0, r: FLOWER.r, lat: -8, lon: -58, roll: 6 }, { r: FLOWER.r * 1.05, roll: 8 }, 'out'),   // the flower (wide: she is its heart)
    ...shot(L(4), L(5), { x: -0.85, y: -0.55, r: 1.25, lat: 18, lon: 96, roll: -6, sun: [0.7, 0.4, -0.59] }, { x: -0.9, y: -0.6, lon: 98 }),
    ...shot(L(5), L(6), { x: -2.3, y: -0.1, r: 1.9, lat: -12, lon: 96, roll: 7, sun: [0.5, -0.3, -0.81] }, { x: -2.42, lon: 98 }, 'smooth'),   // side limb (16:9; 9:16 is set in the builder)
    ...shot(L(6), L(7), { x: 0.9, y: -1.75, r: 2.0, lat: 10, lon: 30, roll: -8, sun: [0.6, 0.3, -0.74] }, { y: -1.7, lon: 32 }),   // the thread: low and close, her limb bottom right, him top left
    ...shot(L(7), L(8), { x: 0, y: 0.14, r: 1.6, lat: 6, lon: -66, roll: -7, sun: SUN0 }, { roll: 7, r: 1.85, y: 0.2 }, 'out'),   // cut 2: a close-up of her face (was a centred globe)
    ...shot(L(8), L(9), { x: -0.25, y: -0.75, r: 1.45, lat: 14, lon: 62, roll: -12 }, { x: -0.3, r: 1.52, lon: 66 }),   // the day: a big rising crop, not a centred globe
    ...shot(LIFE_T[0], LIFE_T[1], { x: 0.15, y: -0.1, r: 3.3, lat: -17.3, lon: 148.2, roll: 38 }, { r: 3.5 }),                      // reef (Great Barrier)
    ...shot(LIFE_T[1], LIFE_T[2], { x: 0, y: 0, r: 2.3, lat: 0.5, lon: 21, roll: -6 }, { r: 2.42 }),                         // jungle (Congo)
    ...shot(LIFE_T[2], LIFE_T[3], { x: 0.1, y: -1.32, r: 1.75, lat: 36, lon: -42, roll: 4, sun: [0.5, 0.62, -0.6] }, { y: -1.28 }), // ice (Greenland under the aurora)
    ...shot(L(10), L(11), { x: 0.25, y: -1.5, r: 1.7, lat: 14, lon: 8, roll: -5, sun: [-0.4, -0.3, -0.87] }, { y: -1.62 }, 'out'),
  ],
  stars,
  builders,
  inserts: [{ slot: 'fc_life', src: 'le/inserts/ground2_fc_life_r2.mp4', src916: 'le/inserts/ground2_fc_life_916_r2.mp4',
    from: LIFE_T[0] + 0.002, to: LIFE_T[3] + 0.002, label: 'all the life down here, three views from the habitat floor' }],
};
export const FC = { L, CD, CD0, HOU, END, F, mix };
