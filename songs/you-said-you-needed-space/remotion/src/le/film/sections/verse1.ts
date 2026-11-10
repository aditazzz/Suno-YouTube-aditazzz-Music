// Verse 1: v1_rivers .. v1_dirt (frames 528-1069). earth_proof30 (creative director), Nov 8. One camera path (proof30.ts
// CAM30) and one function of song time for the whole verse, so no gag is cut by a slot edge:
//   rivers / rain: over her night limb, the Amazon's veins pulse on each word, rain falls as light
//   cool / hot:    her sea and clouds breathe; his city lights on the horizon flare warm on "hot" and are cooled
//   sand:          the dive into one glowing grain on the shore; its own grains line up into his chip on "learned to think"
//   every spark:   back out over the river mouth; the chip's light runs up every river, gold cooling to her cyan
//   feed:          tilt up; the stars write his post (the real one, word for word); it lets go after "first", into "the future's in the stars"
//   future / dirt: the stars glitter, she dims; pull back to one small dot that flares on "dirt"
import { Section, Out, hits, env, smooth, flow, spark, C, lerp, reverse } from './api';
import { words, at } from '../anchor';
import { RGB } from '../grade';
import { HANDOFF, SHORE, T, cam30 } from './proof30';
import { LOOK } from './coldOpen';
import { camFor, projGeo, screenAspect } from '../camera';
import { Cam, Fmt, Pulse } from '../types';
import { pre1 } from './pre1';
const wt = (sec: string, li: number) => words(sec, li).map((w) => w[0]);
const W = { rivers: wt('verse1a', 0), cool: wt('verse1a', 1), sand: wt('verse1a', 2), spark: wt('verse1a', 3), feed: wt('verse1b', 0), first: wt('verse1b', 1), future: wt('verse1b', 2), dirt: wt('verse1b', 3) };
const GOLD: RGB = [1.0, 0.66, 0.26];
const CHIP_S = 0.88, CHIP_Y = 0.03, CHIP_GAIN = 2.2, CHIP_TILT = 0.62;   // cut 2: the golden chip fills the frame (mockup 04a), his warm gold
// a point of the die (its own plane, -1..1) on screen: the JS twin of Extra.tsx CHIP_VERT for a seated grain
function chipPt(x: number, y: number, t: number, S: number, cx: number, cy: number, tilt: number): [number, number] {
  const yaw = 0.24 - 0.16 * (t - 24.0), c = Math.cos(yaw), s = Math.sin(yaw), px = c * x - s * y, py = s * x + c * y;
  const pz = Math.sin(tilt) * py, persp = 1 / (1 + pz * 0.34);
  return [cx + px * persp * S, cy + Math.cos(tilt) * py * persp * S];
}
// the first thought: light leaves the core along the buses, turns a right angle at each block and runs out to the pads
const THOUGHT: [number, number][][] = [];
for (const sd of [0, 1, 2, 3]) for (const o of [-0.10, 0, 0.10]) for (const dir of [-1, 1]) {
  const a = (sd * Math.PI) / 2, R = (x: number, y: number): [number, number] => [Math.cos(a) * x - Math.sin(a) * y, Math.sin(a) * x + Math.cos(a) * y];
  const lane = o === 0 ? 0 : dir * 0.33 + o, pad = -0.77 + (1.54 * Math.round(((lane + 0.77) / 1.54) * 14)) / 14;
  if (o === 0 && dir === 1) continue;
  THOUGHT.push([R(o, 0.30), R(o, 0.355), R(lane, 0.355), R(lane, 0.76), R(pad, 0.76), R(pad, 0.955)]);
}
// the Amazon and its great tributaries, mouth first ([lat, lon]): the chip's light runs up them
const UP: [number, number][][] = [
  [[-0.4, -50.0], [-1.6, -52.4], [-2.2, -54.6], [-2.5, -56.6], [-3.1, -58.6], [-3.2, -60.2], [-3.4, -62.8], [-3.3, -64.9], [-2.6, -67.2], [-3.6, -69.6], [-4.3, -71.8], [-4.6, -73.6], [-7.2, -74.9], [-10.0, -75.2]], // main stem
  [[-3.2, -60.0], [-2.0, -61.2], [-1.2, -62.6], [-0.6, -64.2], [-0.3, -66.0], [0.6, -67.2], [1.8, -67.4]],                 // Negro
  [[-3.4, -58.8], [-4.6, -59.8], [-6.0, -61.2], [-7.6, -62.8], [-8.8, -63.9], [-10.4, -65.3], [-12.0, -65.2]],             // Madeira
  [[-2.4, -54.7], [-4.0, -55.4], [-5.8, -56.4], [-7.4, -57.6], [-9.2, -57.0]],                                             // Tapajos
  [[-1.5, -52.0], [-3.2, -52.2], [-5.0, -52.8], [-7.2, -53.2], [-9.6, -53.4]],                                             // Xingu
  [[-1.4, -48.8], [-3.0, -49.4], [-5.2, -49.3], [-7.4, -48.6], [-9.8, -48.4]],                                             // Tocantins
];
const DELAY = [0, 0.46, 0.38, 0.22, 0.12, 0.05];
const hsh = (n: number) => { const x = Math.sin(n * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };
// ---- "gave you rain" (earth_pol_open, Nov 9): real rain in her own space. Each drop falls straight down onto a place on her
// (a streak from 0.05-0.10 radii up to the ground, so it leans with the curve of her and stands tall on the horizon), lands,
// and rings out like a drop on a pond. Most of it falls on the Amazon basin; a new place every time a drop falls. ----
const RAIN_N = 190, RAINC: RGB = [0.66, 0.98, 1.0];
// showers: most drops fall in a handful of storm cells over the basin (so it reads as rain under clouds, not as noise)
const CELLS: [number, number, number][] = [[-3.5, -61, 3.2], [-7.5, -67.5, 2.8], [-9.5, -56, 3.0], [0.5, -55.5, 2.4], [-2, -70.5, 2.6], [-12.5, -62, 2.6], [3.5, -64, 2.2]];
function rainOn(t: number, k: number, camP: Cam, A: number, kR = 1): ReturnType<typeof flow>[] {   // kR: low over her the streaks are shorter (in her radii), so each stays one unbroken line of light
  const out: ReturnType<typeof flow>[] = [];
  for (let i = 0; i < RAIN_N; i++) {
    const tall = i % 4 === 3;                                        // one drop in four falls all the way down the sky onto her: the rain you can see from far off
    const per = (0.62 + 0.42 * hsh(i * 3.1 + 0.5)) * (tall ? 1.8 : 1), q = t / per + hsh(i * 7.7 + 1.3) * 5, cyc = Math.floor(q), u = q - cyc;
    const a = hsh(i * 13.3 + cyc * 5.17), b = hsh(i * 9.1 + cyc * 3.71 + 2.2), c = hsh(i * 5.3 + cyc * 1.93 + 4.4);
    const cell = i % 10 < 7 ? CELLS[i % CELLS.length] : null, ra = Math.sqrt(-2 * Math.log(Math.max(1e-4, a))) * 0.62, an = 6.2832 * b;   // a gaussian shower around its cell
    const lat = cell ? cell[0] + cell[2] * ra * Math.cos(an) : -22 + 58 * a, lon = cell ? cell[1] + cell[2] * ra * Math.sin(an) : -102 + 88 * b;
    const bot = projGeo(camP, [lat, lon], 0.002);
    if (bot.z < 0.02 || Math.abs(bot.x) > A + 0.1 || bot.y > 1.1 || bot.y < -1.12) continue;
    const top = projGeo(camP, [lat, lon], tall ? 0.45 + 0.4 * c : 0.06 + 0.07 * c);
    if (u < (tall ? 0.57 : 0.76)) out.push(flow({ space: 'screen', pts: [[top.x, top.y], [bot.x, bot.y]] }, u / 0.5, tall ? { tail: 0.12 * kR, size: 4.2 + 1.6 * c, color: RAINC, intensity: k * (1.5 + 1.5 * c), count: 60 } : { tail: 0.5 * kR, size: 3.6 + 2.6 * c, color: RAINC, intensity: k * (1.5 + 2.4 * c), count: 40 }));
    if (u > 0.5) {                                                   // it lands: a small ring spreads on her and fades
      const v = (u - 0.5) / 0.5, rho = (0.35 + 1.05 * Math.pow(v, 0.6)) * (0.7 + 0.6 * c), a0 = hsh(i * 2.9 + cyc) * 6.2832, cl = Math.cos((lat * Math.PI) / 180);
      const pts = Array.from({ length: 13 }, (_, j) => { const th = a0 + (j / 12) * 6.2832; return [lat + rho * Math.cos(th), lon + (rho * Math.sin(th)) / cl] as [number, number]; });
      out.push(flow({ space: 'geo', pts, lift: 0.002 }, 1, { tail: 1, size: 2.6 + 1.2 * c, color: C.her, intensity: k * 3.2 * (1 - v) * (1 - v), count: 12 }));
    }
  }
  return out;
}
// ---- "kept you cool when you ran hot": his cities run hot (warm sparks on the real places), then her cool wave rolls out from
// the heart of the Amazon and each one goes out to her cyan as the ring reaches it ----
const QC: [number, number] = [-6, -60], QSPD = 44, HOT: RGB = [1.0, 0.36, 0.10];
const gc = (p: [number, number], q: [number, number]) => { const d = Math.PI / 180, s = Math.sin(p[0] * d) * Math.sin(q[0] * d) + Math.cos(p[0] * d) * Math.cos(q[0] * d) * Math.cos((p[1] - q[1]) * d); return Math.acos(Math.max(-1, Math.min(1, s))) / d; };
const CITIES = ([[4.7, -74.1, 1.0], [10.5, -66.9, 1.0], [6.2, -75.6, 0.7], [10.6, -71.6, 0.7], [-12.0, -77.0, 1.0], [-0.2, -78.5, 0.7], [-2.2, -79.9, 0.6], [-3.1, -60.0, 0.8], [-1.4, -48.5, 0.9],
  [-3.7, -38.5, 0.8], [-8.0, -34.9, 0.8], [-13.0, -38.5, 0.8], [-15.8, -47.9, 0.7], [-19.9, -43.9, 0.8], [-22.9, -43.2, 1.0], [-23.5, -46.6, 1.0], [-16.5, -68.1, 0.6], [-17.8, -63.2, 0.6], [9.0, -79.5, 0.8],
  [18.5, -69.9, 0.8], [10.7, -61.5, 0.6], [5.8, -55.2, 0.5], [23.1, -82.4, 0.8], [25.8, -80.2, 1.0], [18.4, -66.1, 0.7], [18.0, -76.8, 0.6], [19.4, -99.1, 1.0], [14.6, -90.5, 0.6], [2.8, -60.7, 0.4], [-9.9, -67.8, 0.4]] as [number, number, number][])
  .map(([la, lo, w], i) => ({ p: [la, lo] as [number, number], w, d: gc([la, lo], QC), i }));
function v1(t: number, fmt: Fmt): Out {
  const cam = cam30(t, fmt);
  // ---- her light, word by word ----
  const kick = 1.4 * hits(t, W.rivers, 0.3) + 0.5 * hits(t, W.cool, 0.35) + 0.4 * hits(t, [W.sand[0], W.sand[1]], 0.3) + 0.6 * hits(t, W.spark, 0.3);
  const rain = env(t, W.rivers[4] - 0.25, 0.5, 0.7, 20.2);                        // "gave you rain": falling by "rain", through "kept you cool", over before he runs hot
  const cool = env(t, W.cool[0], 0.5, 1.4, 21.4);
  const TS = W.cool[6] - 0.12, TQ = W.cool[6] + 0.16;                              // as he runs "hot" her water is already on its way (TS); the first of his lights goes cool at TQ
  const heat = 0.3 * smooth(W.cool[0], W.cool[2], t) + 0.7 * smooth(W.cool[3] - 0.2, W.cool[6] - 0.08, t), flareH = env(t, W.cool[6] - 0.08, 0.1, 0.4);   // his lights warm up under "kept you cool", run HOT on "hot"
  const quench = smooth(TQ, TQ + 0.42, t), cooled = quench * (1 - smooth(23.3, 24.3, t));   // (his lights are back to themselves under the sand, before "every spark")
  const future = smooth(T.future - 0.2, T.future + 1.6, t), back = smooth(T.dirt0, T.dirt, t);
  const dirt = env(t, T.dirt - 0.03, 0.13, 1.1);
  // ---- the dive: sand layer in on "sand", the grain's grains line up on "learned to think", back out on "every spark" ----
  // (earth_pol_open: on the word "sand" we are ON the shore and stay there half a second, grains sharp and countable, a slow push; then the dive)
  const sand = smooth(22.22, 22.34, t) * (1 - smooth(T.out, T.out + 0.42, t));
  const sandDive = -1 + 0.5 * smooth(22.22, 22.74, t) + 0.45 * smooth(22.70, 23.30, t) + 1.05 * smooth(23.22, 23.70, t);   // -1..0 the camera comes down onto the shore, 0..0.2 a slow push over the grains, ..1 into the one grain
  const chipIn = smooth(23.50, 23.72, t), chipU = smooth(23.68, W.sand[7] + 0.14, t);   // "learned to think"
  const outK = smooth(T.out, T.orbit, t);
  const shore = projGeo(camFor(fmt, cam), SHORE, 0.004);        // where the grain lies, on this format's screen
  const chipS = lerp(CHIP_S, 0.05, Math.pow(outK, 0.55));
  const chip = chipIn * (1 - smooth(T.out, T.out + 0.3, t));              // it melts into her rivers as we pull out: the gold carries on from the river mouth
  const warm = smooth(W.future[5] - 0.9, W.future[5] + 0.5, t) * (1 - smooth(T.dirt - 0.05, T.dirt + 0.5, t));   // "...in the STARS": the sky turns his gold and glitters; on "dirt" it drains back
  // ---- "every spark": gold light from the chip up every river, cooling to her cyan ----
  const goldR = 34 * Math.pow(Math.max(0, (t - (T.out + 0.38)) / 1.75), 0.8), goldK = env(t, T.out + 0.3, 0.3, 0.7, T.feed - 0.35) * 1.5;
  const flows: ReturnType<typeof flow>[] = [];
  const camP = camFor(fmt, cam);
  if (rain > 0.01) flows.push(...rainOn(t, rain, camP, screenAspect(fmt), Math.min(1, 2.6 / cam.r)));
  if (false && t > T.out + 0.3 && t < T.feed + 1.2) {
    for (let w = 0; w < 2; w++) UP.forEach((pts, i) => {
      const t0 = T.out + 0.42 + DELAY[i] + w * 0.62, h = (t - t0) / (i === 0 ? 1.35 : 0.95);
      if (h <= 0 || h > 1.5) return;
      const col = [0, 1, 2].map((k) => lerp(GOLD[k], C.her[k], smooth(0.55, 1.05, h))) as RGB;
      flows.push(flow({ space: 'geo', pts, lift: 0.004 }, h, { tail: 0.42, size: i === 0 ? 10 : 8, color: col, intensity: (w === 0 ? 3.2 : 2.2) * (1 - smooth(0.85, 1.25, h)) * (1 - smooth(T.feed + 0.2, T.feed + 1.0, t)), count: i === 0 ? 260 : 150 }));
    });
  }
  const dotC = camP;
  // the first thought (on "think"): gold comets from the core to the pads, each on its own right-angled lane
  const think = W.sand[7] + 0.02, cS = chipS * (fmt === '916' ? 0.5 : 1);
  if (chip > 0.01 && t > think - 0.05 && outK < 0.05) THOUGHT.forEach((lane, i) => {
    for (let w = 0; w < 2; w++) {
      const h = (t - think - 0.045 * (i % 5) - w * 0.26) / 0.34;
      if (h <= 0 || h > 1.6) continue;
      flows.push(flow({ space: 'screen', pts: lane.map(([x, y]) => chipPt(x, y, t, cS, 0, CHIP_Y, CHIP_TILT)) }, Math.min(h, 1), { tail: 0.42, size: 12, color: [1.0, 0.94, 0.80], intensity: 5.0 * chip * (1 - smooth(1.0, 1.55, h)), count: 54 }));
    }
  });
  const closeK = smooth(2.4, 5.5, cam.r);                        // low over her the veins fill the frame: hold the exposure so they stay lines, not a white sheet
  const sparks = [...(chip > 0.01 && outK < 0.3 ? [spark(0, CHIP_Y, { size: 900 * cS, color: [1.0, 0.56, 0.16], intensity: 0.085 * chip * (0.6 + 0.4 * chipU) * (1 - outK / 0.3) })] : []), ...(goldK > 0.01 && outK > 0.5 && shore.visible ? [spark(shore.x, shore.y, { size: 26, color: GOLD, intensity: 0.5 * Math.min(1, goldK) * outK })] : []),
    ...(dirt > 0.01 ? [spark(dotC.x, dotC.y, { size: 46, color: C.her, intensity: 2.4 * dirt }), spark(dotC.x, dotC.y, { size: 150, color: C.her, intensity: 0.20 * dirt })] : [])];   // "dirt": a sharp glint, not a blur
  if (heat > 0.01 && t < TQ + 2.2) {
    const cs = CITIES.map((c) => ({ c, s: projGeo(camP, c.p, 0.001) })).filter((o) => o.s.z > 0.05 && Math.abs(o.s.x) < screenAspect(fmt) + 0.1 && Math.abs(o.s.y) < 1.1).sort((x, y) => y.c.w - x.c.w).slice(0, 22);
    for (const { c, s: sp } of cs) {
      const tq = TQ + 0.34 * Math.min(1, c.d / 42), q = smooth(tq - 0.03, tq + 0.09, t), fl = 1 + 0.22 * Math.sin(t * 34 + c.i * 2.1) * heat;
      // her water: a stream of her light leaves the heart of the Amazon for each of his hot lights and puts it out as it arrives
      const hd = (t - TS) / (tq - TS);
      if (hd > 0 && hd < 1.5) { const mid: [number, number] = [(QC[0] + c.p[0]) / 2 + 2.2 * Math.sin(c.i * 1.7), (QC[1] + c.p[1]) / 2 + 2.2 * Math.cos(c.i * 1.7)];
        flows.push(flow({ space: 'geo', pts: [QC, [(QC[0] + mid[0]) / 2 + 0.6 * Math.sin(c.i), (QC[1] + mid[1]) / 2], mid, [(mid[0] + c.p[0]) / 2, (mid[1] + c.p[1]) / 2 + 0.6 * Math.cos(c.i)], c.p], lift: 0.004 }, Math.min(hd, 1), { tail: 0.55, size: 6.5, color: C.her, intensity: 3.4 * (1 - smooth(1.0, 1.45, hd)) * (1 - sand), count: 110 })); }
      const col = [0, 1, 2].map((k) => lerp(lerp(C.his[k], HOT[k], heat), C.her[k], q)) as RGB;
      const warmI = (1.0 * heat + 1.2 * flareH) * fl * c.w * (1 - q), coolI = 1.7 * c.w * env(t, tq, 0.05, 0.7);
      if ((warmI + coolI) * (1 - sand) > 0.01) sparks.push(spark(sp.x, sp.y, { size: (26 + 34 * heat + 26 * flareH) * (0.7 + 0.3 * c.w) * (1 - 0.45 * q), color: col, intensity: (warmI + coolI) * (1 - sand) }));   // (nothing of the planet is drawn over the sand)
    }
  }
  // her light spreading over her in rings: the rivers' words, the rain landing, the cool wave on "cool", the wave that puts his heat out
  const PULSES: Pulse[] = [{ lat: -6, lon: -60, t0: 15.3, speed: 20, strength: 0.8 }, { lat: -6, lon: -60, t0: 16.4, speed: 20, strength: 0.9 }, { lat: -3.1, lon: -60, t0: W.rivers[3], speed: 16, strength: 0.9 }, { lat: -2.2, lon: -54.5, t0: W.rivers[6], speed: 16, strength: 0.7 },
    { lat: -7, lon: -66, t0: W.rivers[6] + 0.1, speed: 9, strength: 0.6 }, { lat: -1, lon: -58, t0: W.rivers[6] + 0.28, speed: 8, strength: 0.6 }, { lat: -10, lon: -56, t0: W.rivers[6] + 0.5, speed: 9, strength: 0.55 },
    { lat: 2, lon: -44, t0: W.cool[2], speed: 24, strength: 1.0 }, { lat: QC[0], lon: QC[1], t0: TS + 0.1, speed: QSPD, strength: 1.7 }];
  // ---- the feed post (her mark, Nov 9: "literally Elon's post on X"; the copy lives in living_earth/proof30_post.py) ----
  const bannerU = smooth(W.feed[0] + 0.05, W.feed[4] + 0.19, t) + smooth(W.first[5] + 0.6, W.first[5] + 1.6, t); // written by "feed"; holds through "first", then lets go into "the future's in the stars"
  const banner = t > W.feed[0] && t < W.first[5] + 1.8 ? 1 : 0;
  const land = env(t, W.feed[6], 0.1, 0.9);                                         // the banner lands with a small brightening on "feed"
  return {
    cam,
    grade: { ...LOOK, haloWide: 0.35 * back + 0.5 * dirt, starWarm: warm, castWarm: warm, seam: 0.30, atmos: 1.0, hisWarm: (0.35 + 1.1 * heat + 0.8 * flareH) * (1 - 0.92 * cooled), hisColor: [0, 1, 2].map((k) => lerp(C.his[k], HOT[k], 0.75 * heat * (1 - quench))) as RGB, herCyan: (0.7 + 0.5 * cool + 0.9 * cooled) * (1 - 0.30 * closeK), riverPulse: lerp(1.0, 0.5, future),
      glow: (1.15 + 0.12 * cool - 0.30 * env(t, W.first[5], 0.18, 0.9)) * (1 - 0.38 * future * (1 - back)) * (1 - (0.46 * closeK + 0.30 * smooth(7.5, 26, cam.r)) * (1 - sand)) + 0.35 * dirt, kick, rivers: 1.0, goldR, goldK, goldLat: SHORE[0], goldLon: SHORE[1],
      ocean: (1.5 + 1.3 * cool + 0.8 * cooled) * (1 - 0.45 * closeK), clouds: 0.42 + 0.25 * cool + 0.22 * rain, forest: lerp(0.6, 0.28, closeK), motes: 0.25, mist: 0.15, flare: 0.9 * dirt,
      stars: (1.0 + 0.55 * future * (1 - 0.5 * back)) * (1 - 0.4 * dirt), bloomThreshold: 0.36 + 0.16 * sand + 0.12 * closeK * (1 - sand), bloom: 0.52 - 0.20 * closeK * (1 - sand) - 0.26 * Math.max(sand * (1 - 0.55 * chipU * chip), 0) - 0.24 * smooth(W.feed[0] + 0.3, W.feed[6], t) * (1 - smooth(W.first[5] + 0.6, W.first[5] + 1.6, t)), capil: lerp(1.5, 0.85, closeK),
      sand, sandDive, chip: chip * CHIP_GAIN, chipU: chipU + smooth(W.sand[7] + 0.14, W.sand[7] + 0.66, t), chipX: lerp(0, shore.x, outK), chipY: lerp(CHIP_Y, shore.y, outK), chipS, chipTilt: lerp(CHIP_TILT, 0.2, outK), banner: banner * (1.15 + 0.3 * land), bannerU },
    flows, sparks,
    pulses: PULSES.filter((p) => t >= p.t0 - 0.05 && t - p.t0 < 3.6).slice(-8),
  };
}
const CUT = at('pre1/L0');
export const verse1: Section = {
  name: 'verse1',
  camera: [{ at: 'verse1b/L3/w6', cam: HANDOFF, ease: 'hold' }],
  stars: [
    // "the future's in the STARS": the bright stars line up into an arrow pointing where he went (up and away from her); they wander home on "dirt"
    { at: 'verse1b/L2/w5-0.6', set: { kind: 'svg', d: 'M16 84 L80 20 M40 16 H84 V60', view: [100, 100], box: { cx: 0.0, cy: 0.50, w: 1.30, h: 0.92 }, stroke: 8, keep: 0.08 }, dur: 0.8, straggle: 0.3, curve: 0.2 },
    { at: 'verse1b/L3+0.95', set: { kind: 'sky' }, dur: 1.15, straggle: 0.35 },   // home before the cut at pre1/L0
  ], // the hand-off to pre1: exactly the key state the engine had here before (proof30.ts)
  builders: { v1_rivers: (c) => v1(c.t, c.fmt), v1_cool: (c) => v1(c.t, c.fmt), v1_sand: (c) => v1(c.t, c.fmt), v1_spark: (c) => v1(c.t, c.fmt), v1_feed: (c) => v1(c.t, c.fmt), v1_first: (c) => v1(c.t, c.fmt), v1_future: (c) => v1(c.t, c.fmt), v1_dirt: (c) => (c.t >= CUT ? pre1.builders.p1_holding(c) : v1(c.t, c.fmt)) },   // a true cut into the pre-chorus: from the cut on, this slot IS pre1's first shot, so the engine's 0.45 s slot blend has nothing of the old shot to blend (the line earth_sec_c1 gave)
};
