// Chorus 1: c1_space .. c1_inch. Built by earth_sec_c1 (Sun Nov 8): the film's first big release.
//   "You said you needed ..."        the pre-chorus rings are wound tight around her, her glow held back
//   "... SPACE"                       the rings burst outward (the stars give her room), she swells toward us in full night bloom
//   "Didn't know you meant the stars" she moves over; on "stars" the sky snaps into a server rack (his kind of stars)
//   "Pack your GPUs and go"           the rack unpacks itself: unit by unit slides out and leaves, his chips stream off her after them
//   "I've got rivers left to flow"    CUT low over South America: light runs down the Amazon and its tributaries to the sea
//   "Go on, chase the sun all day"    CUT to her horizon: his satellite runs after the sunrise, always a step behind
//   "Go on, disappear"                he is lost in the glare
//   "Who's gonna cool you down"       CUT two-shot: she is cool and misty below; up in the bare sun the stars build him a case fan
//   "You've got no atmosphere"        the fan spins up with nothing to push, he glows red, it flies apart; her air wraps her like a scarf
//   "You said you needed space"       pull back wide; on "space" the stars back away and leave them both a lot of it
//   "Maybe I could use some too"      deadpan: she scoots one inch away from him. One content ripple.
// Story colour code: warm white/amber/red = him and his tech; cyan/violet = her. Star shapes: rings -> room -> rack -> fan -> room.
// inserts: none yet. PLACEHOLDER: c1_rivers may take a close-surface plate (pitch page REDONE pick 7: pitch_mockups/surface2,
// render.night_plate(cam, W, H, t, region='amazon')) if that pick is approved; add it as `inserts: [{ slot: 'c1_rivers', ... }]`.
// The engine version below (lux veins + capillaries, light running down the rivers) works without it.
//
// Reusable parts are exported (NIGHT, bloomGrade, bloomPulses, roomFn, RACKSET/RACKBOX/packFn, FANBOX/fanFn, SA_RIVERS, hisSpot,
// himSparks, scarf). The old rough factory by le_engine is saved in build/le_c1/old/chorus1.ts.le_engine (chorus2.ts has its own now).
import { PAL, Section, Builder, Ctx, hits, env, smooth, spark, flow, C, RIVERS, lerp, clamp01 } from './api';
import { Box, Cam, Flow, Fmt, Pulse, Spark, StarSet } from '../types';
import { at, words } from '../anchor';
import { Grade, RGB } from '../grade';
import { ASPECT, fitBox, resolveSet, starAttr } from '../stars';
import { T1, OVR, ovr, camC, lonAt, rocket, hardCut, withLook } from './pre1';

const D = Math.PI / 180;
const S = 'chorus1';
const wt = (sec: string, li: number) => words(sec, li).map((w) => w[0]);
const mixC = (a: RGB, b: RGB, u: number): RGB => [lerp(a[0], b[0], u), lerp(a[1], b[1], u), lerp(a[2], b[2], u)];
export const T = {
  space: T1.space, l1: at(`${S}/L1`), stars: at(`${S}/L1/w5`), l2: at(`${S}/L2`), go: at(`${S}/L2/w4`), l3: at(`${S}/L3`), flow: at(`${S}/L3/w5`),
  l4: at(`${S}/L4`), l5: at(`${S}/L5`), gone: at(`${S}/L5/w2`), l6: at(`${S}/L6`), cool: at(`${S}/L6/w2`), l7: at(`${S}/L7`), atmo: at(`${S}/L7/w3`),
  l8: at(`${S}/L8`), space2: at(`${S}/L8/w4`), l9: at(`${S}/L9`), too: at(`${S}/L9/w5`), cutC: at(`${S}/L9/w5`) - 0.5, end: at('post1/L0'),
};
const WARM: RGB = PAL.ember, NODE: RGB = PAL.filament; // (earth_cut2, gate 7) his props: Ember lines, Filament nodes (was one cream-warm)
const SUN_C: [number, number, number] = [0.5, 0.18, -0.85]; // behind her: a thin day crescent and the dusk line on her right limb, the night glow facing us

// ---- her night bloom: the level she holds through the chorus (style board: fully bloomed, alive, not neon) ----
export const NIGHT: Partial<Grade> = { glow: 1.32, violet: 1, forest: 1.4, ocean: 0.6, rivers: 1.5, riverPulse: 1.2, aurora: 0.7, atmos: 1.2, motes: 0.6, mist: 0.7, bloom: 0.66, herCyan: 0.8 };
// the bloom itself: held back before `s`, then a fast swell on the word and a slow settle to NIGHT
export function bloomGrade(t: number, s: number, big = 0): Partial<Grade> {
  const k = smooth(s - 0.04, s + 0.16, t), pre = smooth(s - 1.3, s, t), set = smooth(s + 0.45, s + 2.4, t), fl = t > s ? Math.exp(-(t - s) / 0.4) : 0;
  const to = (a: number, peak: number, night: number) => lerp(a, lerp(peak, night, set), k);
  return {
    glow: to(lerp(0.85, 0.68, pre), 1.72 + 0.15 * big, NIGHT.glow! + 0.12 * big), violet: 1, flare: 0.3 * fl * k, aurora: to(0, 1.5, NIGHT.aurora!), atmos: to(1.0, 1.75, NIGHT.atmos!),
    forest: to(0.6, 1.9, NIGHT.forest!), ocean: to(0.55, 0.82, NIGHT.ocean!), rivers: to(1.3, 1.9, NIGHT.rivers!), riverPulse: to(0.6, 1.5, NIGHT.riverPulse!),
    herCyan: to(0.6, 1.0, NIGHT.herCyan!), stars: lerp(1.5, 1.0, k), motes: to(0.3, 1.1, NIGHT.motes!), mist: to(0.5, 1.0, NIGHT.mist!), deep: lerp(0.07, 1, k), bloom: to(0.6, 0.8, NIGHT.bloom!), kick: 0.35 * hits(t, [s], 0.6),
  };
}
// rings of light spreading over her from several places at once; kept alive across the slots that follow (they are not cross-faded)
// one wave of light out of the Amazon basin across her face (it shows on her rivers and forests, barely on open sea)
const BLOOM_AT: [number, number, number, number, number][] = [[-4, -60, 0, 46, 0.5]];
export const bloomPulses = (t: number, s: number, lon0 = 0): Pulse[] => (t < s || t > s + 5 ? [] : BLOOM_AT.map(([lat, lon, d, speed, strength]) => ({ lat, lon: lon + lon0, t0: s + d, speed, strength })));

// ---- star shapes ----
// "space": the stars keep a clear room around her, wherever the camera puts her (radius k x her radius)
export const roomFn = (k: number) => (_i: number, t: number, home: [number, number], _n: number, fmt: Fmt): [number, number] => {
  const cam = camC(t, fmt), dx = home[0] - cam.x, dy = home[1] - cam.y, r = Math.hypot(dx, dy) || 1e-6, R = k * cam.r, r2 = Math.cbrt(r * r * r + R * R * R);
  return [cam.x + (dx / r) * r2, cam.y + (dy / r) * r2];
};
// a solid line of light under a star drawing (a constellation line): the stars alone are too thin at phone size. A flow fades
// along its tail, so two run in opposite directions; the points are resampled evenly (the engine walks a path by point index).
export type P2 = [number, number];
const resample = (pts: P2[], n: number): P2[] => { const L = [0]; for (let i = 1; i < pts.length; i++) L.push(L[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]));
  const tot = L[L.length - 1] || 1e-6, out: P2[] = []; let j = 1;
  for (let k = 0; k < n; k++) { const d = (tot * k) / (n - 1); while (j < pts.length - 1 && L[j] < d) j++; const u = (d - L[j - 1]) / (L[j] - L[j - 1] || 1e-6); out.push([lerp(pts[j - 1][0], pts[j][0], u), lerp(pts[j - 1][1], pts[j][1], u)]); }
  return out; };
export const lineFlows = (pts: P2[], o: { color: RGB; size: number; intensity: number; per?: number }): Flow[] => { if (o.intensity <= 0.004) return [];
  let L = 0; for (let i = 1; i < pts.length; i++) L += Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]);
  const count = Math.max(6, Math.round(L * (o.per ?? 95))), r = resample(pts, Math.max(2, Math.round(L * 30) + 2)), rr = r.slice().reverse();
  return [flow({ space: 'screen', pts: r }, 1.01, { tail: 1.01, color: o.color, size: o.size, intensity: o.intensity, count }), flow({ space: 'screen', pts: rr }, 1.01, { tail: 1.01, color: o.color, size: o.size, intensity: o.intensity, count })]; };
const rectPts = (cx: number, cy: number, w: number, h: number): P2[] => [[cx - w / 2, cy - h / 2], [cx + w / 2, cy - h / 2], [cx + w / 2, cy + h / 2], [cx - w / 2, cy + h / 2], [cx - w / 2, cy - h / 2]];
const frac = (x: number) => x - Math.floor(x);
const pxs = (fmt: Fmt) => (fmt === '916' ? 0.8 : 1); // line weights for the narrow frame

// the server rack (polish, Nov 9: bigger, inboard, 5 fat units instead of 8 thin ones, warm lines under the stars): a tall
// cabinet frame + 5 units, each with a status LED (unit design space, y up). 9:16 gets its own box (centred, above her).
const NU = 5, U_CY = (i: number) => 0.12 + i * 0.19, U_W = 0.78, U_H = 0.125, FR_W = 0.95, FR_H = 0.975;
const RACK2: Box[] = [{ cx: 0.5, cy: 0.5, w: FR_W, h: FR_H }, ...Array.from({ length: NU }, (_, i) => ({ cx: 0.5, cy: U_CY(i), w: U_W, h: U_H }))];
// cut 2 (Nov 9): the rack shot is a LOW ANGLE now (we drop low over her and look up; her horizon across the bottom of the frame), so the
// rack towers over her horizon instead of sitting beside a globe (the same globe-left composition came three times in this stretch).
export const RACKBOX: Box = { cx: 0.34, cy: 0.21, w: 0.86, h: 1.3 };
const RACKBOX916: Box = { cx: 0, cy: 0.28, w: 0.62, h: 1.02 };
const horizonY = (cam: Cam, x: number) => cam.y + Math.sqrt(Math.max(0, cam.r * cam.r - (x - cam.x) * (x - cam.x)));
const rackBox = (fmt: Fmt) => fitBox(fmt === '916' ? RACKBOX916 : RACKBOX, fmt);
const RACK_KEEP = 0.2;
export const RACKSET: StarSet = { kind: 'rects', rects: RACK2, box: RACKBOX, outline: true, keep: RACK_KEEP };
const RACKSET916: StarSet = { kind: 'rects', rects: RACK2, box: RACKBOX916, outline: true, keep: RACK_KEEP };
const RACKP: Partial<Record<Fmt, Float32Array>> = {};
const rackPts = (fmt: Fmt) => (RACKP[fmt] ??= resolveSet(fmt === '916' ? RACKSET916 : RACKSET, fmt, 0));
// "pack your GPUs and go": his chips file into the units from "pack"; a packed unit leaves, top one first ("your" .. "go"), the empty cabinet last
const leaveTimes = (s: string) => { const w = wt(s, 2), a = (w[1] ?? w[0] + 0.5) - 0.02, b = (w[4] ?? w[0] + 1.85) - 0.06; return { unit: Array.from({ length: NU }, (_, i) => lerp(a, b, i / (NU - 1))), frame: b + 0.16 }; };
const slide = (s: number, acc = 5.5) => (s <= 0 ? 0 : s < 0.2 ? -0.035 * smooth(0, 0.2, s) : -0.035 + acc * (s - 0.2) * (s - 0.2)); // a small pull back, then away
const slideK = (fmt: Fmt) => (fmt === '916' ? 0.5 : 1);
export const rackFn = (s: string) => { const L = leaveTimes(s); return (i: number, t: number, home: [number, number], _n: number, fmt: Fmt): [number, number] => {
  if (starAttr().r3[i] < RACK_KEEP) return home;
  const P = rackPts(fmt), x = P[i * 2], y = P[i * 2 + 1], b = rackBox(fmt);
  const v = (y - (b.cy - b.h / 2)) / b.h, uu = (x - (b.cx - b.w / 2)) / b.w, row = Math.round((v - 0.12) / 0.19);
  const inUnit = row >= 0 && row < NU && Math.abs(v - U_CY(row)) < U_H / 2 + 0.02 && uu > 0.5 - U_W / 2 - 0.03 && uu < 0.5 + U_W / 2 + 0.03;
  return [x + (inUnit ? slide(t - L.unit[NU - 1 - row]) : slide(t - L.frame, 16)) * slideK(fmt), y];
}; };
export const packFn = rackFn;
// the rack's light: warm lines under the stars (cabinet + units), a blinking LED per unit, and the chips being packed
function rackLight(s: string, t: number, fmt: Fmt, landed: number): { sparks: Spark[]; flows: Flow[] } {
  const L = leaveTimes(s), b = rackBox(fmt), on = smooth(landed - 0.04, landed + 0.22, t), w0 = wt(s, 2)[0], sparks: Spark[] = [], flows: Flow[] = [];
  const X = (u: number) => b.cx + (u - 0.5) * b.w, Y = (v: number) => b.cy + (v - 0.5) * b.h, k = b.w / RACKBOX.w, z = pxs(fmt);
  const fx = slide(t - L.frame, 16) * slideK(fmt);
  flows.push(...lineFlows(rectPts(X(0.5) + fx, Y(0.5), FR_W * b.w, FR_H * b.h), { color: WARM, size: 9 * z, intensity: 1.2 * on, per: 80 }));
  for (let row = 0; row < NU; row++) { const tl = L.unit[NU - 1 - row], dx = slide(t - tl) * slideK(fmt), cy = Y(U_CY(row));
    if (X(0.5) + dx - (U_W * b.w) / 2 > ASPECT[fmt] + 0.1) continue;
    // packed = lit: the unit's outline brightens as its chips arrive (0.5 s before it leaves)
    const packed = smooth(tl - 0.5, tl - 0.08, t), bl = 0.55 + 0.45 * Math.sign(Math.sin(t * (9 + row * 1.7) + row * 2.1));
    flows.push(...lineFlows(rectPts(X(0.5) + dx, cy, U_W * b.w, U_H * b.h), { color: WARM, size: (9 + 4 * packed) * z, intensity: (1.3 + 0.7 * packed) * on, per: 90 }));
    sparks.push(spark(X(0.5 + U_W / 2 - 0.075) + dx, cy, { size: 15 * (0.6 + 0.4 * k), color: NODE, intensity: 2.0 * on * (0.45 + 0.55 * bl) }));
    // (cut 2) "like luggage": as a unit is pulled out it is a suitcase: a handle pops up on top, two wheels under it
    const pull = smooth(tl - 0.2, tl + 0.04, t); if (pull > 0.01) { const ux = X(0.5) + dx, top = cy + (U_H * b.h) / 2, hw = 0.12 * U_W * b.w, hh = 0.058 * (b.h / 1.3) * pull;
      flows.push(...lineFlows([[ux - hw, top], [ux - hw, top + hh], [ux + hw, top + hh], [ux + hw, top]], { color: WARM, size: 8.5 * z, intensity: 1.6 * on * pull, per: 150 }));
      for (const wx of [-0.3, 0.3]) sparks.push(spark(ux + wx * U_W * b.w, cy - (U_H * b.h) / 2 - 0.017 * (b.h / 1.3), { size: 11 * (0.6 + 0.4 * k), color: NODE, intensity: 1.7 * pull })); }
    // two chips per unit: little warm squares lifting off her and filing into the unit like luggage
    if (t > w0 - 0.1) for (let j = 0; j < 3; j++) { const ta = tl - 0.74 + 0.2 * j, u = (t - ta) / 0.5; if (u <= 0 || u >= 1) continue;
      // (cut 2) they lift off his warm city lights along her horizon
      const cam = camC(t, fmt), e = u * u * (3 - 2 * u), sx = fmt === '916' ? -0.42 + 0.19 * row + 0.045 * j : -1.5 + 0.27 * row + 0.08 * j, src: P2 = [sx, horizonY(cam, sx) - 0.045], dst: P2 = [X(0.5 - U_W / 2 + 0.13 + 0.22 * j), cy];
      const px = lerp(src[0], dst[0], e), py = lerp(src[1], dst[1], e) + 0.16 * k * Math.sin(Math.PI * e), sz = 0.17 * (0.55 + 0.45 * k) * (0.65 + 0.35 * Math.sin(Math.PI * Math.min(1, u * 1.6))), a = smooth(0, 0.12, u) * (1 - smooth(0.88, 1, u));
      flows.push(...lineFlows(rectPts(px, py, sz, sz), { color: WARM, size: 7.5 * z, intensity: 1.5 * a, per: 110 }));
      for (const sx of [-1, 1]) for (let q = -1; q <= 1; q++) flows.push(...lineFlows([[px + sx * sz * 0.5, py + q * sz * 0.3], [px + sx * sz * 0.78, py + q * sz * 0.3]], { color: WARM, size: 5.5 * z, intensity: 1.1 * a, per: 200 }));
      sparks.push(spark(px, py, { size: 22 * (0.6 + 0.4 * k), color: NODE, intensity: 1.7 * a }));
      if (u < 0.45) flows.push(...lineFlows([src, [px, py]], { color: WARM, size: 6 * z, intensity: 0.9 * (1 - u / 0.45), per: 120 })); } // a short warm trail from where it lifted off
  }
  return { sparks, flows };
}

// "who's gonna cool you down up there": a thermometer (polish, Nov 9: the case fan read as a flower). The stars draw the glass,
// he is the bulb; his heat climbs a step on every word, and with no air to carry it off it bursts out of the top on "atmosphere".
const VW = 100, VH = 240, BULB_Y = 196, NECK = 165, TUBE_TOP = 22;
const THERM_D = 'M36 165 L36 22 A14 14 0 0 1 64 22 L64 165 A34 34 0 1 1 36 165 Z M75 42 H93 M75 72 H87 M75 102 H93 M75 132 H87';
// cut 2 (Nov 9): he is a 3D character now (earth_him_wire renders him where his spark is), so he is no longer the bulb: the
// thermometer stands beside him, a lead from its bulb to him (it reads HIS temperature). 9:16: fitBox centres every box, so the
// 9:16 box is resolved centred and shifted right by TH_DX.
const THERM169: Box = { cx: 1.34, cy: 0.08, w: 0.5, h: 1.2 }, THERM916: Box = { cx: 0, cy: 0.5333, w: 0.26, h: 0.624 };
const TH_DX: Record<Fmt, number> = { '169': 0, '916': 0.3 };
export const FANBOX = THERM169; // (old name, kept for anything that reads it)
const thermBox = (fmt: Fmt): Box => { const b = fitBox(fmt === '916' ? THERM916 : THERM169, fmt); return { ...b, cx: b.cx + TH_DX[fmt] }; };
const TH_KEEP = 0.2, GLASS_SHARE = 0.45;
const THSET: Record<Fmt, StarSet> = { '169': { kind: 'svg', d: THERM_D, view: [VW, VH], box: THERM169, keep: TH_KEEP, stroke: 2.4 }, '916': { kind: 'svg', d: THERM_D, view: [VW, VH], box: THERM916, keep: TH_KEEP, stroke: 2.4 } };
const THP: Partial<Record<Fmt, Float32Array>> = {};
const HEAT_W = () => [...wt(S, 6).slice(2), ...wt(S, 7).slice(0, 3)]; // cool you down up there / you've got no
let HW: number[] | null = null;
export const level = (t: number) => { HW ??= HEAT_W(); return 0.1 + 0.9 * HW.reduce((a, w) => a + smooth(w, w + 0.16, t), 0) / HW.length; };
const vTop = (t: number) => lerp(NECK - 4, TUBE_TOP + 5, level(t));
export const thermFn = (i: number, t: number, home: [number, number], _n: number, fmt: Fmt): [number, number] => {
  const A = starAttr(); if (A.r3[i] < TH_KEEP) return home;
  const b = thermBox(fmt), h1 = frac(i * 0.61803398875), h2 = frac(i * 0.7548776662), tau = t - T.atmo, te = tau > 0 ? (1 - Math.exp(-1.4 * tau)) / 1.4 : 0;
  const X = (vx: number) => b.cx + (vx / VW - 0.5) * b.w, Y = (vy: number) => b.cy + (0.5 - vy / VH) * b.h;
  if (A.r2[i] < GLASS_SHARE) { const P = (THP[fmt] ??= resolveSet(THSET[fmt], fmt, 0)); let x = P[i * 2] + TH_DX[fmt], y = P[i * 2 + 1];
    if (tau > 0) { const cx = X(50), cy = Y(70), g = 2.4 * te * (0.35 + A.r1[i]); x += (x - cx) * g + (h1 - 0.5) * 0.25 * te; y += (y - cy) * g + 0.12 * te; }
    return [x, y]; }
  const m = (A.r2[i] - GLASS_SHARE) / (1 - GLASS_SHARE);
  if (m < 0.32) { const a = 6.2832 * h1, r = 26 * Math.sqrt(h2) * (1 + 1.6 * te); return [X(50 + r * Math.cos(a)), Y(BULB_Y + r * Math.sin(a))]; }
  const u = (m - 0.32) / 0.68, x = X(50 + (h1 - 0.5) * 17), y = Y(lerp(NECK + 6, vTop(Math.min(t, T.atmo)), u));
  return [x + (h1 - 0.5) * 1.5 * te * b.h * (0.25 + u), y + (0.35 + 1.1 * h2) * te * b.h * (0.3 + 0.7 * u)]; // the heat fountains out of the top
};
export const fanFn = () => thermFn; // (old name)
function thermLight(t: number, fmt: Fmt): { sparks: Spark[]; flows: Flow[] } {
  const b = thermBox(fmt), X = (vx: number) => b.cx + (vx / VW - 0.5) * b.w, Y = (vy: number) => b.cy + (0.5 - vy / VH) * b.h, z = pxs(fmt);
  const tau = t - T.atmo, on = smooth(T.l6 + 0.25, T.l6 + 0.55, t) * (tau > 0 ? Math.exp(-tau / 0.14) : 1), lv = level(t), flows: Flow[] = [], sparks: Spark[] = [];
  if (on > 0.004) {
    const glass: P2[] = [[X(36), Y(NECK)], [X(36), Y(TUBE_TOP)], ...Array.from({ length: 9 }, (_, k) => { const a = Math.PI * (1 - k / 8); return [X(50 + 14 * Math.cos(a)), Y(TUBE_TOP - 14 * Math.sin(a))] as P2; }), [X(64), Y(NECK)],
      ...Array.from({ length: 25 }, (_, k) => { const th = -Math.asin(31 / 34) + ((Math.PI + 2 * Math.asin(31 / 34)) * k) / 24; return [X(50 + 34 * Math.cos(th)), Y(BULB_Y + 34 * Math.sin(th))] as P2; })];
    flows.push(...lineFlows(glass, { color: PAL.ivory, size: 7 * z, intensity: 0.6 * on, per: 90 }));
    for (const [vy, x1] of [[42, 93], [72, 87], [102, 93], [132, 87]]) flows.push(...lineFlows([[X(75), Y(vy)], [X(x1), Y(vy)]], { color: PAL.ivory, size: 6 * z, intensity: 0.5 * on, per: 120 }));
    // the mercury: his heat, amber going red as it climbs
    const col = mixC(PAL.ember, PAL.overheat, smooth(0.25, 0.95, lv));
    flows.push(...lineFlows([[X(50), Y(BULB_Y - 20)], [X(50), Y(vTop(t))]], { color: col, size: 0.21 * b.w * 720 * z, intensity: 0.15 * on, per: 70 }));
    flows.push(...lineFlows([[X(50), Y(BULB_Y - 20)], [X(50), Y(vTop(t))]], { color: [1, 0.8, 0.6], size: 0.07 * b.w * 720 * z, intensity: 0.32 * on, per: 110 }));
    sparks.push(spark(X(50), Y(vTop(t)), { size: 26 * z, color: col, intensity: 0.9 * on * (0.6 + 0.8 * hits(t, HW ?? [], 0.2, 0.05)) }));
    // the lead: from the bulb to him, a slack cable (it is his temperature being read)
    const h = hisSpot(fmt, t), bc: P2 = [X(50), Y(BULB_Y)], dl = Math.hypot(h[0] - bc[0], h[1] - bc[1]) || 1e-6, d: P2 = [(h[0] - bc[0]) / dl, (h[1] - bc[1]) / dl];
    const g0 = 0.34 * b.w + 0.012, g1 = fmt === '916' ? 0.05 : 0.08, n = 10, lead = Array.from({ length: n + 1 }, (_, k) => { const u = k / n, s = g0 + (dl - g0 - g1) * u; return [bc[0] + d[0] * s, bc[1] + d[1] * s - 0.05 * (b.h / 1.2) * Math.sin(Math.PI * u)] as P2; });
    flows.push(...lineFlows(lead, { color: mixC(PAL.ivory, col, 0.5), size: 5 * z, intensity: 0.5 * on, per: 110 }));
  }
  if (tau > -0.02 && tau < 0.9) sparks.push(spark(X(50), Y(TUBE_TOP), { size: 170 * z, color: [1, 0.5, 0.25], intensity: 1.3 * Math.exp(-Math.max(0, tau) / 0.2) }));
  return { sparks, flows };
}
// where he is on screen from the thermometer shot to the end of the chorus: the bulb; the burst kicks him up to where he drifts through the wide shots
// (cut 2) the two-shot: he floats between her and the thermometer (HIM_AT); the burst on "atmosphere" knocks him back a little
// (KICK). From the cut to the wide ("you said you needed space", L8) he is the far dot at REST.
export const HIM_AT: Record<Fmt, P2> = { '169': [0.55, -0.06], '916': [-0.17, 0.3] };
const KICK: P2 = [0.1, 0.08];
const REST: Record<Fmt, P2> = { '169': [1.3, 0.2], '916': [0.04, 0.5] };
const CLOSE_HIM: Record<Fmt, P2> = { '169': [0.95, 0.6], '916': [0.12, 0.52] }; // in her sky, in the close shot of "maybe I could use some"
export const hisSpot = (fmt: Fmt, t = 1e9): P2 => { if (t >= T.l9 && t < T.cutC) return CLOSE_HIM[fmt]; if (t >= T.l8) return REST[fmt]; const a = HIM_AT[fmt], k = 1 - Math.pow(1 - clamp01((t - T.atmo - 0.05) / 1.2), 3); return [a[0] + KICK[0] * k, a[1] + KICK[1] * k]; };

// "you said you needed space" (2): the stars measure it. A dimension line, the kind on a floor plan, from her to him (an arrow head
// and an end bar at each end). It follows them both, so when she scoots away on "too" it gets an inch longer.
const AR_KEEP = 0.2;
export const arrowEnds = (t: number, fmt: Fmt): { a: P2; b: P2; d: P2; n: P2; len: number } => { const cam = camC(t, fmt), h = hisSpot(fmt, t), dx = h[0] - cam.x, dy = h[1] - cam.y, L = Math.hypot(dx, dy) || 1e-6, d: P2 = [dx / L, dy / L];
  const g0 = cam.r + 0.085, g1 = 0.1, a: P2 = [cam.x + d[0] * g0, cam.y + d[1] * g0], b: P2 = [h[0] - d[0] * g1, h[1] - d[1] * g1];
  return { a, b, d, n: [-d[1], d[0]], len: Math.max(0.02, L - g0 - g1) }; };
const twang = (t: number) => { const s = t - (T.too + 0.2); return s > 0 ? 0.022 * Math.exp(-s / 0.35) * Math.sin(s * 2 * Math.PI * 4.2) : 0; };
export const wideShot = (t: number) => t >= T.l8 && t < T.end; // (cut 2) the close shot between the two wides keeps the line too: the same space, seen from her horizon
export const arrowFn = (i: number, t: number, home: [number, number], _n: number, fmt: Fmt): [number, number] => {
  const A = starAttr(); if (A.r3[i] < AR_KEEP || !wideShot(t)) return home;
  const E = arrowEnds(t, fmt), h1 = frac(i * 0.61803398875), h2 = frac(i * 0.7548776662), m = A.r2[i], hd = (fmt === '916' ? 0.062 : 0.085), tw = twang(t);
  const at2 = (s: number, o: number): [number, number] => [E.a[0] + E.d[0] * s + E.n[0] * o, E.a[1] + E.d[1] * s + E.n[1] * o];
  if (m < 0.5) { const u = h1; return at2(u * E.len, (h2 - 0.5) * 0.012 + tw * Math.sin(Math.PI * u)); }             // the shaft
  if (m < 0.74) { const end = m < 0.62 ? 0 : 1, sg = h1 < 0.5 ? -1 : 1, q = h2 * hd; return at2(end ? E.len - q : q, sg * q * 0.62 + (frac(i * 0.37) - 0.5) * 0.008); } // the two arrow heads
  const end = m < 0.87 ? 0 : 1; return at2(end ? E.len + 0.012 : -0.012, (h1 - 0.5) * 2 * hd * 1.05);                                                     // the two end bars
};
function arrowLight(t: number, fmt: Fmt): Flow[] { if (!wideShot(t)) return [];
  const on = smooth(T.space2 - 0.05, T.space2 + 0.3, t), E = arrowEnds(t, fmt), z = pxs(fmt), hd = fmt === '916' ? 0.062 : 0.085, tw = twang(t), col: RGB = PAL.ivory;
  const at2 = (s: number, o: number): P2 => [E.a[0] + E.d[0] * s + E.n[0] * o, E.a[1] + E.d[1] * s + E.n[1] * o];
  const shaft = Array.from({ length: 13 }, (_, k) => at2((E.len * k) / 12, tw * Math.sin((Math.PI * k) / 12)));
  return [...lineFlows(shaft, { color: col, size: 7 * z, intensity: 0.55 * on, per: 90 }),
    ...lineFlows([at2(hd, hd * 0.62), at2(0, 0), at2(hd, -hd * 0.62)], { color: col, size: 7 * z, intensity: 0.55 * on, per: 110 }),
    ...lineFlows([at2(E.len - hd, hd * 0.62), at2(E.len, 0), at2(E.len - hd, -hd * 0.62)], { color: col, size: 7 * z, intensity: 0.55 * on, per: 110 }),
    ...lineFlows([at2(-0.012, hd * 1.05), at2(-0.012, -hd * 1.05)], { color: col, size: 7 * z, intensity: 0.55 * on, per: 110 }),
    ...lineFlows([at2(E.len + 0.012, hd * 1.05), at2(E.len + 0.012, -hd * 1.05)], { color: col, size: 7 * z, intensity: 0.55 * on, per: 110 })];
}

// ---- "I've got rivers left to flow": South America's rivers as [lat, lon], mouth last ----
export const SA_RIVERS: Record<string, [number, number][]> = {
  amazon: RIVERS.amazon,
  negro: [[2.0, -67.5], [0.5, -65.2], [-0.9, -63.0], [-2.0, -61.4], [-3.1, -60.0]],
  madeira: [[-12.5, -65.3], [-9.6, -65.0], [-8.2, -63.2], [-6.2, -61.9], [-4.6, -59.9], [-3.4, -58.8]],
  tapajos: [[-11.5, -57.6], [-8.2, -57.6], [-6.0, -56.9], [-4.0, -55.6], [-2.4, -54.7]],
  xingu: [[-13.5, -53.6], [-10.0, -52.9], [-7.0, -52.7], [-4.0, -52.6], [-1.6, -52.2]],
  tocantins: [[-14.0, -48.6], [-10.0, -48.4], [-6.0, -49.1], [-3.2, -49.6], [-1.6, -48.9]],
  orinoco: [[3.0, -67.5], [5.6, -67.6], [7.6, -66.0], [8.0, -63.6], [8.6, -62.0], [9.0, -60.8]],
  parana: [[-16.0, -48.0], [-20.0, -51.0], [-24.0, -54.3], [-27.3, -56.0], [-29.0, -59.0], [-32.0, -60.6], [-34.2, -58.4]],
  saofrancisco: [[-19.0, -45.2], [-15.0, -44.2], [-11.0, -43.2], [-9.2, -40.5], [-9.6, -37.8], [-10.5, -36.4]],
  magdalena: [[2.0, -76.0], [5.0, -74.7], [8.0, -73.9], [10.9, -74.8]],
};
const riverFlows = (t: number, t0: number, w: number[]): Flow[] => {
  const order: [string, number, number][] = [['amazon', 0, 8], ['madeira', 0.25, 6], ['negro', 0.35, 6], ['tapajos', 0.6, 5.5], ['xingu', 0.8, 5.5], ['tocantins', 1.0, 5.5], ['orinoco', 0.5, 5.5], ['parana', 0.7, 6], ['saofrancisco', 1.1, 5], ['magdalena', 0.9, 5]];
  const out: Flow[] = [];
  for (const [name, d, size] of order) {
    const h = smooth(t0 + d, t0 + d + 1.5, t) * 1.3;                             // the first light runs to the sea
    out.push(flow({ space: 'geo', pts: SA_RIVERS[name], lift: 0.002 }, h, { tail: 0.45, size: size * 0.8, intensity: 0.8, count: 150 }));
    const p = ((t - t0) * 0.55 + d) % 1;                                          // then it keeps coming, in packets
    out.push(flow({ space: 'geo', pts: SA_RIVERS[name], lift: 0.002 }, p * 1.25, { tail: 0.22, size: size * 0.6, intensity: 0.5 * smooth(t0 + d + 0.9, t0 + d + 1.6, t), count: 60, color: mixC(C.her, C.white, 0.35) }));
  }
  void w; return out;
};

// ---- "chase the sun": his satellite on her limb, the sunrise always a step ahead (angles on her limb, deg from +x) ----
function sunShot(t: number, fmt: Fmt) {
  const k = clamp01((t - T.l4) / (T.l6 - T.l4)), wide = fmt === '169';
  const thSun = wide ? lerp(64, 51, k) : lerp(84, 73, k), lag = lerp(17, 8, smooth(0, 0.62, k)) + 2.5 * Math.sin(k * 9);
  const thSat = thSun + lag, gone = smooth(T.gone - 0.25, T.gone + 0.55, t), rise = smooth(T.l4, T.gone + 0.6, t);
  const sunDir: [number, number, number] = [Math.cos(thSun * D), Math.sin(thSun * D), lerp(-2.3, -1.45, rise)]; // far behind her: the day is a thin crescent that widens as it rises
  const sunP: [number, number] = [1.004 * Math.cos(thSun * D), 1.004 * Math.sin(thSun * D)], satR = 1.075;
  const satP: [number, number] = [satR * Math.cos(thSat * D), satR * Math.sin(thSat * D)];
  const trail = Array.from({ length: 24 }, (_, i) => { const a = (thSat + 46 * (1 - i / 23)) * D; return [satR * Math.cos(a), satR * Math.sin(a)] as [number, number]; });
  const sparks: Spark[] = [
    spark(0, 0, { rel: sunP, size: lerp(105, 150, gone) * (wide ? 1 : 0.7), color: PAL.filament, intensity: lerp(0.8, 1.0, gone) }), // (QA gate 3: a small clipped core, the glare is the halo)
    spark(0, 0, { rel: sunP, size: lerp(380, 900, gone) * (wide ? 1 : 0.7), color: PAL.ember, intensity: lerp(0.1, 0.3, gone) }),
    spark(0, 0, { rel: satP, size: 15, color: C.his, intensity: 2.3 * (1 - gone) }),
  ];
  const flows: Flow[] = [flow({ space: 'rel', pts: trail }, 1, { tail: 1, size: 5.5, color: PAL.ember, intensity: 1.7 * (1 - gone), count: 260 })];
  return { sunDir, sparks, flows, gone };
}
// (QA gate 3, exposure) her sunlit surface right under the sun blew out as the crescent widened: the day side is eased down as the sun rises
const dayK = (t: number) => lerp(0.92, 0.6, smooth(T.l4 + 0.6, T.gone + 0.3, t));
// the sun direction through the chorus (a function of time only, so both sides of a cut agree)
const sunAt = (t: number, fmt: Fmt): Partial<Cam> => (t >= T.l4 && t < T.l6 ? { sun: sunShot(t, fmt).sunDir } : {});
export const shot = (c: Ctx): Partial<Cam> => ({ ...ovr(c.t, c.fmt), ...sunAt(c.t, c.fmt) });

// ---- him, after the fan: a lone hot spark at the fan's hub, cooling slowly ----
export const heat = (t: number) => smooth(T.cool - 0.2, T.atmo, t) * (1 - 0.55 * smooth(T.atmo + 1.5, T.too, t)); // 0 warm white .. 1 red hot
export const himSparks = (t: number, fmt: Fmt, k = 1): Spark[] => { const p = hisSpot(fmt, t), h = heat(t), col = h < 0.5 ? mixC(C.his, [1, 0.45, 0.15], h * 2) : mixC([1, 0.45, 0.15], C.red, h * 2 - 1);
  const fl = 1 + 0.25 * h * Math.sin(t * 31) + 0.15 * h * Math.sin(t * 53);
  return [spark(p[0], p[1], { size: 12 + 5 * h, color: col, intensity: (1.5 + 1.2 * h) * fl * k }), spark(p[0], p[1], { size: 60 + 70 * h, color: col, intensity: (0.18 + 0.3 * h) * k })]; };
// ---- her air as a scarf (cut 2, Nov 9: "atmosphere wraps her like a scarf") ----
// A real scarf, so it reads at phone size: a broad band of her own air round her lower third (the front of a ring seen from a
// little above, so it bows down the way a scarf sits on a neck), tied in a knot on his side, two tails with fringed ends that keep
// fluttering. It is thrown round her on the word: both ends sweep in from her limbs, meet, knot, and the tails unfurl with a flick.
// Everything is her colours (cyan / teal / violet): no warm. Drawn as solid lines of light in screen space; sizes follow her radius.
const SC = { R: 1.045, h0: -0.12, h1: -0.42, beta: 18 * D, tilt: -8 * D, knot: 57 * D };
const scPt = (a: number, h: number, t: number): P2 => { const hh = h + 0.012 * Math.sin(5 * a + 1.6 * t), rho = Math.sqrt(Math.max(0, 1 - hh * hh)) * SC.R;
  const x = rho * Math.cos(a), y = hh * SC.R * Math.cos(SC.beta) - rho * Math.sin(a) * Math.sin(SC.beta), c = Math.cos(SC.tilt), sn = Math.sin(SC.tilt); return [c * x - sn * y, sn * x + c * y]; };
const springy = (s: number) => (s <= 0 ? 0 : 1 - Math.exp(-6.5 * s) * Math.cos(11 * s)); // 0 -> 1 with one overshoot
const SC_HEM: RGB = [0.36, 0.92, 1.0], SC_A: RGB = PAL.biolume, SC_B: RGB = [0.11, 0.56, 0.86], SC_V: RGB = PAL.aurora; // (earth_cut2, gate 7: Biolume -> Aurora, was adding up to white)
// lag: how far the tail ends trail behind (her radii), e.g. when she scoots
export const scarf = (t: number, t0: number, fmt: Fmt, k = 1, lag: P2 = [0, 0]): Flow[] => { if (t < t0 - 0.02 || k <= 0.004) return [];
  const cam = camC(t, fmt), z = (cam.r / 0.83) * (fmt === '916' ? 1.25 : 1), out: Flow[] = [], S = (p: P2): P2 => [cam.x + cam.r * p[0], cam.y + cam.r * p[1]];
  const u = smooth(t0, t0 + 0.4, t), aL = lerp(Math.PI, SC.knot, u), aR = lerp(0, SC.knot, u), per = 1 / Math.max(0.25, cam.r / 0.83);
  const arc = (a0: number, a1: number, h: number): P2[] => { const n = Math.max(2, Math.ceil(Math.abs(a1 - a0) / (5 * D))); return Array.from({ length: n + 1 }, (_, q) => S(scPt(lerp(a0, a1, q / n), h, t))); };
  const NS = 4;
  for (const [a0, a1] of [[Math.PI, aL], [0, aR]] as P2[]) { if (Math.abs(a1 - a0) < 0.02) continue;
    for (let i = 0; i < NS; i++) { const h = lerp(SC.h0, SC.h1, (i + 0.5) / NS), sh = 0.8 + 0.2 * Math.sin(2.1 * t + i * 1.7);
      out.push(...lineFlows(arc(a0, a1, h), { color: i % 2 ? SC_B : SC_A, size: 46 * z, intensity: 0.15 * k * sh, per: 125 * per })); }
    for (const h of [SC.h0, SC.h1]) out.push(...lineFlows(arc(a0, a1, h), { color: SC_HEM, size: 11 * z, intensity: 0.62 * k, per: 190 * per }));
    out.push(...lineFlows(arc(a0, a1, (SC.h0 + SC.h1) / 2), { color: SC_A, size: 150 * z, intensity: 0.05 * k, per: 40 * per })); // the air around it
  }
  // the knit: violet stripes across the band
  for (let q = 0; q < 9; q++) { const a = (12 + q * 19.5) * D; if (a < aL - 0.01 && a > aR + 0.01) continue;
    out.push(...lineFlows([S(scPt(a, SC.h0 - 0.012, t)), S(scPt(a, (SC.h0 + SC.h1) / 2, t)), S(scPt(a, SC.h1 + 0.012, t))], { color: SC_V, size: 30 * z, intensity: 0.3 * k, per: 150 * per })); }
  // the knot and the two tails
  const g = springy(t - (t0 + 0.36)); if (g <= 0) return out;
  const K = scPt(SC.knot, (SC.h0 + SC.h1) / 2, t), kn = Array.from({ length: 13 }, (_, q) => { const a = (q / 12) * 2 * Math.PI; return S([K[0] + 0.075 * Math.cos(a), K[1] + 0.06 * Math.sin(a)]); });
  out.push(...lineFlows(kn, { color: SC_HEM, size: 11 * z, intensity: 0.6 * k * Math.min(1, g), per: 200 * per }), ...lineFlows([S([K[0] - 0.035, K[1]]), S([K[0] + 0.035, K[1]])], { color: SC_HEM, size: 60 * z, intensity: 0.45 * k * Math.min(1, g), per: 150 * per }));
  const TAILS: [number, number, number, number][] = [[-40, 0.72, 0.0, 0.2], [8, 0.56, 2.1, 0.18]]; // direction (deg), length, flutter phase, width (her radii)
  for (const [th, L, ph, w] of TAILS) { const flick = 0.5 * (g - 1), dth = (th + 34 * flick) * D, dir: P2 = [Math.cos(dth), Math.sin(dth)], nr: P2 = [-dir[1], dir[0]], NT = 3, M = 12;
    const cl = (sv: number): P2 => { const fl = 0.055 * sv * Math.sin(7 * sv - 3.4 * t + ph) + 0.02 * sv * Math.sin(13 * sv - 5.3 * t + ph * 2);
      return [K[0] + dir[0] * L * sv * Math.min(1.08, g) + nr[0] * fl + lag[0] * sv * sv, K[1] + dir[1] * L * sv * Math.min(1.08, g) + nr[1] * fl - 0.07 * sv * sv + lag[1] * sv * sv]; };
    const strand = (o: number): P2[] => Array.from({ length: M + 1 }, (_, q) => { const sv = q / M, c = cl(sv), wd = w * (0.7 + 0.3 * sv); return S([c[0] + nr[0] * o * wd, c[1] + nr[1] * o * wd]); });
    for (let i = 0; i < NT; i++) out.push(...lineFlows(strand((i + 0.5) / NT - 0.5), { color: i % 2 ? SC_B : SC_A, size: 44 * z, intensity: 0.2 * k, per: 125 * per }));
    for (const o of [-0.5, 0.5]) out.push(...lineFlows(strand(o), { color: SC_HEM, size: 10.5 * z, intensity: 0.62 * k, per: 190 * per }));
    for (const sv of [0.3, 0.52, 0.74, 0.94]) { const c = cl(sv), wd = w * (0.7 + 0.3 * sv); out.push(...lineFlows([S([c[0] - nr[0] * 0.5 * wd, c[1] - nr[1] * 0.5 * wd]), S([c[0] + nr[0] * 0.5 * wd, c[1] + nr[1] * 0.5 * wd])], { color: SC_V, size: 28 * z, intensity: 0.3 * k, per: 150 * per })); }
    // the fringe
    for (let q = 0; q < 5; q++) { const o = (q / 4 - 0.5) * 0.92, e = cl(1), sw = 0.02 * Math.sin(5 * t + q * 1.3 + ph);
      out.push(...lineFlows([S([e[0] + nr[0] * o * w, e[1] + nr[1] * o * w]), S([e[0] + nr[0] * (o * w * 1.12 + sw) + dir[0] * 0.085, e[1] + nr[1] * (o * w * 1.12 + sw) + dir[1] * 0.085 - 0.012])], { color: SC_HEM, size: 8 * z, intensity: 0.6 * k, per: 220 * per })); }
  }
  return out; };

// her scarf tails trail behind when she scoots (her radii)
const scootLag = (t: number, fmt: Fmt): P2 => { if (t <= T.cutC) return [0, 0]; const a = camC(t, fmt), b = camC(Math.max(T.cutC + 0.001, t - 0.14), fmt); return [((b.x - a.x) / a.r) * 1.6, ((b.y - a.y) / a.r) * 1.6]; }; // (never across the cut: the camera before it is another shot)
// "maybe I could use some": the close shot of her while she thinks it over (low horizon, violet mist); 9:16 has its own framing (OVR below)
const CLOSE: Partial<Grade> = { glow: 1.5, mist: 1.45, aurora: 1.0, atmos: 1.55, rivers: 1.9, riverPulse: 1.7, forest: 1.6, motes: 0.8, room: 0, stars: 1.0, deep: 1, hisWarm: 0.2 };
export const chorus1: Section = {
  name: 'chorus1',
  camera: [
    // the bloom: she swells toward us on the word (ease out = fastest on "space"), a dome of light low in the frame
    { at: `${S}/L0/w4+0.5`, cam: { x: 0, y: -0.62, r: 1.15, lon: lonAt(-38, 48), lat: 6, roll: -14, sun: SUN_C }, ease: 'out' },
    { at: `${S}/L1+0.15`, cam: { r: 1.19, y: -0.65 } },
    // (cut 2) we drop low over her and look up: her horizon across the bottom of the frame (his warm city lights on it), the whole sky
    // for what the stars are about to do
    { at: `${S}/L1/w4-0.07`, cam: { x: 0, y: -2.66, r: 2.2, lon: lonAt(-30, 49.5), lat: -20, roll: -6 } },
    { at: `${S}/L3-0.02`, cam: { y: -2.71, r: 2.25 }, ease: 'linear' },
    // rivers: cut. (cut 2: lower and closer) low over the Amazon basin from the Atlantic side: the river runs down the frame from the
    // Andes on the horizon to its mouth at the bottom
    { at: `${S}/L3`, cam: { x: 0, y: -3.45, r: 4.2, lon: lonAt(-5, 53.8), lat: -3, roll: -90 }, ease: 'hold' },
    { at: `${S}/L4-0.02`, cam: { y: -3.78, r: 4.55, lon: lonAt(-3, 53.8) }, ease: 'linear' },
    // chase the sun: cut to her horizon; we slide along with him
    { at: `${S}/L4`, cam: { x: 0, y: -2.42, r: 2.0, lon: lonAt(112, 57), lat: -18, roll: 0 }, ease: 'hold' },
    { at: `${S}/L6-0.02`, cam: { lon: lonAt(88, 57), r: 2.06, y: -2.48 }, ease: 'linear' },
    // the two-shot: cut. Her below (cool), him up in the bare sun; a slow push toward her through "no atmosphere"
    // (cut 2: all of her in frame, so the scarf has a neck to go round; HERO slots c1_cool / c1_atmos: frozen for earth_him_wire)
    { at: `${S}/L6`, cam: { x: -0.96, y: -0.1, r: 0.8, lon: lonAt(-24, 62), lat: 14, roll: -12, sun: SUN_C }, ease: 'hold' },
    { at: `${S}/L8-0.02`, cam: { x: -0.93, y: -0.09, r: 0.85 }, ease: 'linear' },
    // "you said you needed space" (2): CUT very wide (cut 2: a real change of scale, and the cut hides the 3D him -> far dot swap);
    // the last of the pull back lands on the word
    { at: `${S}/L8`, cam: { x: -1.0, y: -0.2, r: 0.46 }, ease: 'hold' },
    { at: `${S}/L8/w4+0.25`, cam: { x: -1.1, y: -0.22, r: 0.37 }, ease: 'out' },
    { at: `${S}/L9-0.02`, cam: { r: 0.375 }, ease: 'linear' },
    // "maybe I could use some": cut close on her, low over her horizon, while she thinks it over
    { at: `${S}/L9`, cam: { x: 0.1, y: -2.72, r: 2.5, lon: lonAt(78, 68), lat: 20, roll: 5 }, ease: 'hold' },
    { at: `${S}/L9/w5-0.52`, cam: { y: -2.8, r: 2.6, lon: lonAt(74, 68) }, ease: 'linear' },
    // "... too": cut back to the wide. A small lean toward him, then one inch the other way, and settle
    { at: `${S}/L9/w5-0.5`, cam: { x: -1.1, y: -0.22, r: 0.375, lon: lonAt(-24, 62), lat: 14, roll: -12 }, ease: 'hold' },
    { at: `${S}/L9/w5-0.36`, cam: { x: -1.1 } },
    { at: `${S}/L9/w5-0.1`, cam: { x: -1.085 } },
    { at: `${S}/L9/w5+0.24`, cam: { x: -1.215 }, ease: 'out' },
    { at: `${S}/L9/w5+0.58`, cam: { x: -1.2 } },
    { at: 'post1/L0-0.02', cam: { r: 0.385 }, ease: 'linear' },
  ],
  stars: [
    { at: `${S}/L0/w4-0.06`, set: { kind: 'fn', fn: roomFn(1.5), front: false }, dur: 0.6, straggle: 0.25, curve: 0.3 },
    { at: `${S}/L1/w5-0.5`, set: { kind: 'fn', fn: rackFn(S), front: true }, dur: 0.5, straggle: 0.15, curve: 0.08 }, // lands on "stars"
    { at: `${S}/L3`, set: { kind: 'fn', fn: rackFn(S), front: false }, dur: 0.03, straggle: 0 },      // behind her at the cut
    { at: `${S}/L3+0.05`, set: { kind: 'sky' }, dur: 2.2, straggle: 0.5 },
    { at: `${S}/L6-0.12`, set: { kind: 'fn', fn: thermFn, front: true }, dur: 0.5, straggle: 0.15, curve: 0.12 },   // drawn by "gonna"; the heat starts climbing on "cool"
    { at: `${S}/L8-0.02`, set: { kind: 'sky' }, dur: 0.012, straggle: 0 }, // (earth_cut2 seam fix: was L8-0.04 / 0.03, which emptied the thermometer on frame 1931, one frame BEFORE the cut at 1932)
                                          // the cut to the wide: what is left of the thermometer is gone
    { at: `${S}/L8/w4-0.5`, set: { kind: 'fn', fn: arrowFn, front: true }, dur: 0.52, straggle: 0.12, curve: 0.1 },  // lands on "space"
  ],
  builders: {
    c1_space: (c) => { const s = T.space, out = smooth(s, s + 0.7, c.t), r = rocket(c.t, { span: lerp(2.6, 0.5, out), big: 1.25, k: 1 - out, count: 2200 });
      return { cam: shot(c), grade: bloomGrade(c.t, s), pulses: bloomPulses(c.t, s), motes: c.t > s ? 'rise' : 'drift', ...r }; },
    c1_stars: (c) => ({ cam: shot(c), grade: { ...bloomGrade(c.t, T.space), stars: lerp(1.0, 2.0, smooth(T.stars - 0.5, T.stars, c.t)), deep: lerp(1, 0.1, smooth(T.stars - 0.9, T.stars - 0.1, c.t)), galaxy: lerp(1, 0.5, smooth(T.stars - 0.9, T.stars - 0.1, c.t)), hisWarm: lerp(0.35, 0.8, smooth(T.l1 + 0.2, T.stars, c.t)), castWarm: smooth(T.stars - 0.45, T.stars + 0.1, c.t), kick: 0.2 * hits(c.t, wt(S, 1), 0.3) }, pulses: bloomPulses(c.t, T.space), motes: 'rise',
      ...rackLight(S, c.t, c.fmt, T.stars) }),
    c1_gpus: (c) => { const k = smooth(T.l2, T.l3, c.t); return { cam: shot(c), motes: 'rise', pulses: bloomPulses(c.t, T.space),
      grade: { ...NIGHT, stars: 2.0, deep: 0.1, galaxy: 0.5, castWarm: 1, hisWarm: lerp(0.8, 0.04, smooth(T.l2 + 0.3, T.l3 - 0.1, c.t)), kick: 0.2 * hits(c.t, wt(S, 2), 0.3) },
      ...rackLight(S, c.t, c.fmt, T.stars) }; },
    c1_rivers: (c) => ({ cam: shot(c), motes: 'drift',
      grade: { ...NIGHT, glow: 1.22, rivers: 1.5, riverPulse: 1.35, forest: 1.5, mist: 1.3, aurora: 0.9, atmos: 1.35, hisWarm: 0.05, kick: 0.14 * hits(c.t, wt(S, 3), 0.3) }, // (QA gate 3: graded down for the closer camera)
      flows: riverFlows(c.t, T.l3 - 0.1, wt(S, 3)),
      pulses: [{ lat: -9, lon: -74, t0: at(`${S}/L3/w2`), speed: 20, strength: 0.3 }] }),
    c1_sun: (c) => { const s = sunShot(c.t, c.fmt); return { cam: shot(c), grade: { ...NIGHT, glow: 1.3, daySide: dayK(c.t), sunWarm: 1, seam: 0.4, aurora: 0.25, mist: 0.5, motes: 0.3, atmos: 0.78, bloom: 0.56 }, sparks: s.sparks, flows: s.flows }; },
    c1_disappear: (c) => { const s = sunShot(c.t, c.fmt); return { cam: shot(c), grade: { ...NIGHT, glow: 1.3, daySide: dayK(c.t), sunWarm: 1, seam: 0.4, aurora: 0.25, mist: 0.5, motes: 0.3, atmos: 0.78 + 0.16 * s.gone, bloom: 0.56 + 0.05 * s.gone }, sparks: s.sparks, flows: s.flows }; },
    c1_cool: (c) => { const th = thermLight(c.t, c.fmt); return { cam: shot(c), grade: { ...NIGHT, glow: 1.4, mist: 1.0, aurora: 0.6, stars: 2.0, deep: 0.1, galaxy: 0.5, kick: 0.25 * hits(c.t, [T.cool], 0.5) },
      sparks: [...himSparks(c.t, c.fmt, smooth(T.l6 + 0.2, T.l6 + 0.5, c.t)), ...th.sparks], flows: th.flows }; },
    c1_atmos: (c) => { const k = smooth(T.l7, T.atmo + 0.4, c.t), th = thermLight(c.t, c.fmt); return { cam: shot(c), motes: 'drift',
      grade: { ...NIGHT, glow: lerp(1.4, 1.5, k), mist: 1.0, aurora: lerp(0.6, 1.3, k), atmos: lerp(1.2, 1.9, k), stars: 2.0, deep: 0.1, galaxy: 0.5, kick: 0.25 * hits(c.t, [T.atmo], 0.6) },
      sparks: [...himSparks(c.t, c.fmt), ...th.sparks], flows: [...th.flows, ...scarf(c.t, T.atmo + 0.3, c.fmt)] }; },
    c1_space2: (c) => { const k = smooth(T.l8, T.space2 + 0.3, c.t); return { cam: shot(c),
      grade: { ...NIGHT, glow: lerp(1.5, 1.4, k), mist: lerp(1.0, 0.5, k), aurora: lerp(1.3, 0.8, k), atmos: lerp(1.9, 1.4, k), stars: 2.0, deep: lerp(0.1, 0.5, k), galaxy: lerp(0.5, 0.8, k), kick: 0.25 * hits(c.t, [T.space2], 0.7) },
      sparks: himSparks(c.t, c.fmt), flows: [...scarf(c.t, T.atmo + 0.3, c.fmt), ...arrowLight(c.t, c.fmt)],
      pulses: [] }; },
    c1_inch: (c) => { if (c.t < T.cutC) { const k = clamp01((c.t - T.l9) / (T.cutC - T.l9)); // she thinks it over: her rivers answer every word, the aurora stirs
        return { cam: shot(c), motes: 'rise', grade: { ...NIGHT, ...CLOSE, stars: 1.8, deep: 0.6, aurora: 1.0 + 0.35 * Math.sin(k * 7), kick: 0.3 * hits(c.t, wt(S, 9).slice(0, 5), 0.3) }, sparks: himSparks(c.t, c.fmt, 0.85), flows: arrowLight(c.t, c.fmt), pulses: [] }; }
      const ah = env(c.t, T.too + 0.75, 0.35, 1.6); return { cam: shot(c), // after the scoot: one content ripple
      grade: { ...NIGHT, glow: 1.4 + 0.22 * ah, mist: 0.5, aurora: 0.8 + 0.4 * ah, atmos: 1.4 + 0.3 * ah, stars: 2.0, deep: 0.5, galaxy: 0.8 },
      sparks: himSparks(c.t, c.fmt), flows: [...scarf(c.t, T.atmo + 0.3, c.fmt, 1, scootLag(c.t, c.fmt)), ...arrowLight(c.t, c.fmt)],
      pulses: [] }; },
  },
};
// 9:16 reframes of this stretch (see pre1.ts): the sun shot keeps the horizon a third of the way up the tall frame
OVR.push({ a: T.l4, b: T.l6, f: (t) => ({ y: lerp(-1.95, -2.0, clamp01((t - T.l4) / (T.l6 - T.l4))) }) });
OVR.push({ a: T.l9, b: T.cutC, f: (t) => ({ x: 0, y: lerp(-2.42, -2.48, clamp01((t - T.l9) / (T.cutC - T.l9))), r: 2.6 }) }); // the close shot: her horizon above the bottom third
// 9:16, the rack shot: her horizon just under the lower third, the rack above it (the window opens where the move starts: no jump)
OVR.push({ a: T.l1 + 0.15, b: T.l3, f: (_t, base) => ({ y: base.y + 0.42 * clamp01((base.r - 1.19) / (2.2 - 1.19)) }) });
// 9:16, the rivers: the horizon high in the tall frame
OVR.push({ a: T.l3, b: T.l4, f: (_t, base) => ({ y: (0.55 - 0.62 * base.r) / 0.8 }) });
// 9:16, the two-shot: she sits whole in the lower half, he and the thermometer above her (pre-camFor units: x 0 -> y x0.8, r x0.62)
OVR.push({ a: T.l6, b: T.l8, f: (t) => ({ x: 0, y: -0.625, r: lerp(0.645, 0.68, clamp01((t - T.l6) / (T.l8 - T.l6))) }) });
// 9:16, the two wides: she is small at the bottom, he is the far dot at the top; her scoot (16:9: x) goes down the frame
const wide916 = (_t: number, base: Cam): Partial<Cam> => ({ x: 0, y: (-0.62 + (base.x + 1.1) * 0.55) / 0.8, r: (base.r * 0.55) / 0.62 });
OVR.push({ a: T.l8, b: T.l9, f: wide916 });
OVR.push({ a: T.cutC, b: T.end, f: wide916 });
withLook(chorus1.builders);
hardCut(chorus1.builders, 'c1_gpus', 'c1_rivers', T.l3);
hardCut(chorus1.builders, 'c1_atmos', 'c1_space2', T.l8);
hardCut(chorus1.builders, 'c1_rivers', 'c1_sun', T.l4);
hardCut(chorus1.builders, 'c1_disappear', 'c1_cool', T.l6);
hardCut(chorus1.builders, 'c1_space2', 'c1_inch', T.l9);
