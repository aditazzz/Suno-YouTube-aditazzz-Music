// Shared by coldOpen.ts and verse1.ts (earth_proof30): the functions of song time that several slots read, so a gag that
// crosses a slot boundary is one continuous function (the engine's 0.45 s slot blend then has nothing to blend).
// The GLSL twins of spring / roomR live in ../Extra.tsx (ROOM_GLSL): keep the numbers identical.
import { Cam } from '../types';
import { viewOfGeo } from '../camera';
export const SPACE = { t: 9.04, echoes: [10.24, 10.88, 11.36], R0: 0.775, step: 0.108, cx: 0, cy: 0.04 }; // "space" + "space, space, space" (build/words.json)
export const clamp01 = (x: number) => (x < 0 ? 0 : x > 1 ? 1 : x);
export const smooth = (a: number, b: number, x: number) => { const u = clamp01((x - a) / (b - a)); return u * u * (3 - 2 * u); };
// unit step response of a damped spring: starts at rest, a small overshoot, settles (nothing pops)
export function spring(tau: number, w = 7.5, z = 0.62) {
  if (tau <= 0) return 0;
  const wd = w * Math.sqrt(1 - z * z);
  return 1 - Math.exp(-z * w * tau) * (Math.cos(wd * tau) + ((z * w) / wd) * Math.sin(wd * tau));
}
export const bump = (x: number) => { const s = Math.sin(Math.PI * clamp01(x)); return s * s; };
// how much room the stars are giving her at song time t (screen units). They lean in a hair first (anticipation).
export function roomR(t: number) {
  let R = SPACE.R0 * (spring(t - (SPACE.t - 0.1), 7.2, 0.6) - 0.04 * bump((t - (SPACE.t - 0.42)) / 0.5));
  for (const te of SPACE.echoes) R += SPACE.step * spring(t - te + 0.04, 9.5, 0.62);
  return R;
}
// a star's place at time t, whose home is (hx, hy): the room opens as a wave travelling outward; each star has its own
// small delay (lag), its own idea of how far is far enough (jit), and the crowd's edge is not a perfect circle (wob)
export function roomMap(hx: number, hy: number, t: number, gain: number, cx: number, cy: number, jit = 0, lag = 0): [number, number] {
  const dx = hx - cx, dy = hy - cy, r = Math.hypot(dx, dy) || 1e-6, th = Math.atan2(dy, dx);
  const R = roomR(t - lag - 0.16 * clamp01(r / 2)) * gain;
  const wob = 0.045 * Math.sin(3 * th + 1.0) + 0.03 * Math.sin(5 * th + 4.0) + 0.02 * Math.sin(9 * th + 2.0);
  const Rp = Math.abs(R) * Math.max(0.8, Math.min(1.4, 1 + 0.045 * jit + wob));
  const full = Math.cbrt(r * r * r + Rp * Rp * Rp);
  const rr = R < 0 ? Math.max(r - (full - r) * 0.6, 0.005) : full;
  return [cx + (dx / r) * rr, cy + (dy / r) * rr];
}
// ---- the SOFT room (earth_pol_open, Nov 9): the cold open's room without an edge. Extra.tsx draws it whenever grade.roomKeep > 0
// (GLSL twin there: roomSoft / clumpR, same numbers); with roomKeep = 0 the pressed ring above is drawn as before (pre1 / chorus1).
// Every star has its own idea of how far is far enough (0.45x .. 1.38x of the room), the sky is lumpy (clump) and the room has
// lobes (wob), and a star moves by rr = r + Ri * exp(-r / Ri): nobody piles up into a ring, the crowd just thins toward her.
// After each spring settles the stars keep easing outward (CREEP), so it is always motion, never a still dark circle.
export const CREEP = 0.055;                                           // of R0 per second after "space"
export const clump = (x: number, y: number) => Math.sin(x * 2.9 + 1.7) * Math.sin(y * 3.3 + 0.4) + 0.6 * Math.sin(x * 5.3 - y * 4.7 + 2.0);
export function roomSoft(hx: number, hy: number, t: number, gain: number, cx: number, cy: number, u01 = 0.5, lag = 0): [number, number] {
  const dx = hx - cx, dy = hy - cy, r = Math.hypot(dx, dy) || 1e-6, th = Math.atan2(dy, dx);
  const tt = t - lag - 0.16 * clamp01(r / 2);
  const R = (roomR(tt) + CREEP * SPACE.R0 * Math.max(0, tt - SPACE.t)) * gain;
  const wob = 0.10 * Math.sin(2 * th + 0.6) + 0.07 * Math.sin(3 * th + 1.0) + 0.05 * Math.sin(5 * th + 4.0);
  const Ri = Math.abs(R) * Math.max(0.12, (0.45 + 0.93 * Math.pow(u01, 1.1)) * (1 + wob + 0.22 * clump(hx, hy)));
  const push = Ri * Math.exp(-r / Math.max(Ri, 1e-5));
  const rr = R < 0 ? Math.max(r - 0.5 * push, 0.005) : r + push;
  return [cx + (dx / r) * rr, cy + (dy / r) * rr];
}

// ---- the camera of the first 35.6 s as ONE path (builders return it as their cam, so no slot blend touches it) ----
// Between two keys the radius moves in log space and her centre follows the zoom's own fixed point (a pure zoom about
// one screen point: she never swings out of frame the way separate x / y / r lerps make her do on a 100x move).
export type PKey = { t: number; cam: Cam; ease?: (u: number) => number };
export const E = {
  lin: (u: number) => u, smooth: (u: number) => u * u * (3 - 2 * u), smoother: (u: number) => u * u * u * (u * (u * 6 - 15) + 10),
  out: (u: number) => 1 - Math.pow(1 - u, 3), in: (u: number) => u * u * u, in2: (u: number) => u * u, out2: (u: number) => 1 - (1 - u) * (1 - u),
};
const lerp = (a: number, b: number, u: number) => a + (b - a) * u;
export function camPath(keys: PKey[], t: number): Cam {
  if (t <= keys[0].t) return keys[0].cam;
  let i = 0; while (i + 1 < keys.length && keys[i + 1].t <= t) i++;
  if (i + 1 >= keys.length) return keys[i].cam;
  const a = keys[i].cam, b = keys[i + 1].cam, u = (keys[i + 1].ease ?? E.smooth)(clamp01((t - keys[i].t) / (keys[i + 1].t - keys[i].t)));
  const r = Math.exp(lerp(Math.log(a.r), Math.log(b.r), u));
  let x: number, y: number;
  if (Math.abs(a.r - b.r) < 1e-4 * a.r) { x = lerp(a.x, b.x, u); y = lerp(a.y, b.y, u); }
  else { const fx = (b.x * a.r - a.x * b.r) / (a.r - b.r), fy = (b.y * a.r - a.y * b.r) / (a.r - b.r); x = fx + (a.x - fx) * (r / a.r); y = fy + (a.y - fy) * (r / a.r); }
  return { x, y, r, lon: lerp(a.lon, b.lon, u), lat: lerp(a.lat, b.lat, u), roll: lerp(a.roll, b.roll, u),
    sun: [lerp(a.sun[0], b.sun[0], u), lerp(a.sun[1], b.sun[1], u), lerp(a.sun[2], b.sun[2], u)], par: [lerp(a.par[0], b.par[0], u), lerp(a.par[1], b.par[1], u)] };
}
const SUN_DOT: [number, number, number] = [0.62, 0.28, 0.73];    // the far marble: mostly sunlit (the real photo), a soft night edge
const SUN_NIGHT: [number, number, number] = [0.06, 0.005, -1.0];  // over her night side: the sun just behind the horizon ahead (a thin dusk line on the limb)
export const SHORE: [number, number] = [-0.35, -49.9];            // the Amazon's mouth: where the grain of sand lies
const DOT: Cam = { x: SPACE.cx, y: SPACE.cy, r: 0.0225, lon: -38, lat: 14, roll: -12, sun: SUN_DOT, par: [0, 0] };
// the camera-KEY state at verse1b/L3/w6 exactly as the engine had it before this file (a later section's keys carry over whatever they don't
// set; pre1's first key sets every field and cuts, so today nothing reads it, but the default stays what it was)
export const HANDOFF: Cam = { x: 0, y: 0, r: 0.022, lon: 30, lat: 10, roll: -8, sun: [0.85, 0.25, -0.46], par: [0, 0] };
// the launch: her night limb over Africa, close; the launch point (her limb at 32 deg, ROCKET_DIR) sits left of centre
export const ROCKET_DEG = 32;
const LAUNCH: Cam = { x: -2.50, y: -1.73, r: 2.6, lon: -20, lat: -10, roll: 0, sun: [0.03, 0.02, -1.0], par: [-1.6, -0.65] };

// ---- SHOTS (earth_c2_open, Nov 9, cut 2: "vary scale and angle, get low over the surface, into the sand, onto the ground") ----
// From the arrival on, the verse camera is written as shots, not as lon / lat / roll: WHAT is on screen (tg, a place on her), WHERE on
// screen it sits (x, y), from which side we look (brg: the compass bearing from that place to the point under the camera; 180 = we
// look north, 90 = we look west), HOW LOW we are (tilt: 0 = straight down on it, 90 = it is on the horizon) and how close (r).
// The place stays locked to its screen spot through every move, so nothing swings out of frame on a 30x zoom.
const DG = Math.PI / 180;
export type Shot = { tg: [number, number]; brg: number; tilt: number; r: number; x: number; y: number; par: [number, number] };
const SUN_AHEAD: [number, number] = [0.03, 0.05];                  // screen space: the dusk line sits on the horizon ahead of us
function dest(p: [number, number], brg: number, dist: number): [number, number] {
  const la = p[0] * DG, b = brg * DG, d = dist * DG;
  const la2 = Math.asin(Math.sin(la) * Math.cos(d) + Math.cos(la) * Math.sin(d) * Math.cos(b));
  return [la2 / DG, p[1] + Math.atan2(Math.sin(b) * Math.sin(d) * Math.cos(la), Math.cos(d) - Math.sin(la) * Math.sin(la2)) / DG];
}
export function shotCam(s: Shot): Cam {
  const c = dest(s.tg, s.brg, s.tilt);
  const v = viewOfGeo({ lon: c[1], lat: c[0] } as Cam, s.tg[0], s.tg[1]), h = Math.hypot(v[0], v[1]);
  let roll = h < 1e-5 ? s.brg + 180 : 90 - Math.atan2(v[1], v[0]) / DG;          // the place lies straight "up" from the point under the camera
  roll = ((roll + 180) % 360 + 360) % 360 - 180;
  const cr = Math.cos(roll * DG), sr = Math.sin(roll * DG);
  return { x: s.x, y: s.y - s.r * h, r: s.r, lon: c[1], lat: c[0], roll, sun: [cr * SUN_AHEAD[0] + sr * SUN_AHEAD[1], -sr * SUN_AHEAD[0] + cr * SUN_AHEAD[1], -1.0], par: s.par };
}
// monotone cubic through the keys (Fritsch-Carlson): the camera glides THROUGH a key instead of stopping on it, and never overshoots
function pchip(ts: number[], ys: number[]): (t: number) => number {
  const n = ts.length, h = ts.slice(1).map((t, i) => t - ts[i]), dl = h.map((hh, i) => (ys[i + 1] - ys[i]) / hh), m = new Array(n).fill(0);
  for (let i = 1; i < n - 1; i++) if (dl[i - 1] * dl[i] > 0) { const w1 = 2 * h[i] + h[i - 1], w2 = h[i] + 2 * h[i - 1]; m[i] = (w1 + w2) / (w1 / dl[i - 1] + w2 / dl[i]); }
  return (t: number) => {
    if (t <= ts[0]) return ys[0]; if (t >= ts[n - 1]) return ys[n - 1];
    let i = 0; while (ts[i + 1] <= t) i++;
    const u = (t - ts[i]) / h[i], u2 = u * u, u3 = u2 * u;
    return (2 * u3 - 3 * u2 + 1) * ys[i] + (u3 - 2 * u2 + u) * h[i] * m[i] + (-2 * u3 + 3 * u2) * ys[i + 1] + (u3 - u2) * h[i] * m[i + 1];
  };
}
type SKey = { t: number; s: Shot };
function shotPath(keys: SKey[]): (t: number) => Shot {
  const ts = keys.map((k) => k.t), f = (g: (s: Shot) => number) => pchip(ts, keys.map((k) => g(k.s)));
  const la = f((s) => s.tg[0]), lo = f((s) => s.tg[1]), b = f((s) => s.brg), ti = f((s) => s.tilt), lr = f((s) => Math.log(s.r)), x = f((s) => s.x), y = f((s) => s.y), px = f((s) => s.par[0]), py = f((s) => s.par[1]);
  return (t) => ({ tg: [la(t), lo(t)], brg: b(t), tilt: ti(t), r: Math.exp(lr(t)), x: x(t), y: y(t), par: [px(t), py(t)] });
}
export const T = { intro: 11.9, limb: 16.4, low: 19.3, coast: 21.3, dive: 21.9, shore: 22.6, out: 24.72, orbit: 25.55, feed: 26.6, feedIn: 27.25, future: 31.2, dirt0: 33.52, dirt: 35.28 };
const AMAZON: [number, number] = [-4.0, -61.0], COAST: [number, number] = [7.5, -67.0], BEACH: [number, number] = [10.45, -66.4];   // BEACH: her north coast, between his cities
// 16:9. (x, y) = where the place sits on screen; the horizon is at y + r * (1 - sin tilt).
const S169: SKey[] = [
  { t: T.limb, s: { tg: AMAZON, brg: 183, tilt: 42, r: 2.1, x: 0, y: -0.40, par: [0.5, 0.2] } },                 // the arrival: her night limb, the Amazon alight
  { t: T.low, s: { tg: [-3.5, -61.5], brg: 180, tilt: 64, r: 6.4, x: 0, y: -0.26, par: [0.56, 0.27] } },         // "rivers ... rain": DOWN, low over the basin; her rivers run to the horizon
  { t: T.coast, s: { tg: COAST, brg: 187, tilt: 66, r: 6.8, x: -0.05, y: -0.16, par: [0.60, 0.31] } },           // "kept you cool when you ran hot": on north, his cities on the coast in the middle of the frame
  { t: T.dive, s: { tg: BEACH, brg: 186, tilt: 66, r: 7.1, x: -0.03, y: -0.10, par: [0.61, 0.32] } },
  { t: T.shore, s: { tg: BEACH, brg: 186, tilt: 0, r: 70, x: 0, y: 0, par: [0.62, 0.33] } },                     // "sand": a straight fall onto the beach in front of us (the place under the crosshair never slides: a plunge, not a whip)
  { t: T.shore + 0.4, s: { tg: SHORE, brg: 150, tilt: 0, r: 70, x: 0, y: 0, par: [0.62, 0.33] } },               // (under the sand the planet moves on to the river's mouth ...
  { t: T.out, s: { tg: SHORE, brg: 96, tilt: 0, r: 70, x: 0, y: 0, par: [0.62, 0.33] } },                        // ... and turns: we come back up facing WEST, up the river)
  { t: T.orbit, s: { tg: SHORE, brg: 96, tilt: 58, r: 6.0, x: 0.10, y: -0.70, par: [0.64, 0.37] } },             // "every spark": the mouth at our feet, the whole river running away to the horizon
  { t: T.feed, s: { tg: SHORE, brg: 97, tilt: 59, r: 6.1, x: 0.10, y: -0.74, par: [0.65, 0.39] } },
  { t: T.feedIn, s: { tg: SHORE, brg: 98, tilt: 62, r: 5.2, x: 0.05, y: -0.98, par: [0.68, 0.50] } },            // "saw it on my feed": tilt up to the sky, room for his post (the card ends at y = -0.04; her horizon sits at -0.37)
  { t: T.dirt0, s: { tg: SHORE, brg: 103, tilt: 64, r: 5.6, x: 0.03, y: -1.22, par: [0.73, 0.58] } },     // through the banner she keeps sinking out of the frame: the sky has the floor
];
// 9:16, in FINAL screen units of the tall frame (inverted through the engine's reframe in cam30); x stays 0. The first key is what the reframe makes of the 16:9 arrival.
const S916: SKey[] = [
  { t: T.limb, s: { tg: AMAZON, brg: 183, tilt: 42, r: 1.302, x: 0, y: -0.573, par: [0.5, 0.2] } },
  { t: T.low, s: { tg: [-3.5, -61.5], brg: 180, tilt: 64, r: 4.2, x: 0, y: -0.38, par: [0.56, 0.27] } },
  { t: T.coast, s: { tg: [7.5, -68.5], brg: 184, tilt: 66, r: 4.4, x: 0, y: -0.32, par: [0.60, 0.31] } },
  { t: T.dive, s: { tg: BEACH, brg: 184, tilt: 66, r: 4.6, x: 0, y: -0.24, par: [0.61, 0.32] } },
  { t: T.shore, s: { tg: BEACH, brg: 184, tilt: 0, r: 43.4, x: 0, y: 0, par: [0.62, 0.33] } },
  { t: T.shore + 0.4, s: { tg: SHORE, brg: 150, tilt: 0, r: 43.4, x: 0, y: 0, par: [0.62, 0.33] } },
  { t: T.out, s: { tg: SHORE, brg: 96, tilt: 0, r: 43.4, x: 0, y: 0, par: [0.62, 0.33] } },
  { t: T.orbit, s: { tg: SHORE, brg: 96, tilt: 58, r: 4.0, x: 0, y: -0.62, par: [0.64, 0.37] } },
  { t: T.feed, s: { tg: SHORE, brg: 97, tilt: 59, r: 4.05, x: 0, y: -0.64, par: [0.65, 0.39] } },
  { t: T.feedIn, s: { tg: SHORE, brg: 98, tilt: 62, r: 3.6, x: 0, y: -0.60, par: [0.68, 0.50] } },
  { t: T.dirt0, s: { tg: SHORE, brg: 103, tilt: 64, r: 3.9, x: 0, y: -0.84, par: [0.73, 0.58] } },
];
const P169 = shotPath(S169), P916 = shotPath(S916);
const shotAt = (t: number, fmt: string): Cam => { if (fmt !== '916') return shotCam(P169(t)); const c = shotCam(P916(t)); return { ...c, x: 0, y: c.y / 0.8, r: c.r / 0.62 }; };
export const LIMB: Cam = shotCam(S169[0].s);
// the far dot the verse ends on: the sunlit blue marble again (a rhyme with frame 0), before she flares on "dirt"
const END = (from: Cam): Cam => ({ x: 0, y: 0, r: 0.022, lon: from.lon, lat: from.lat, roll: from.roll, sun: [0.5, 0.3, 0.55], par: [0.74, 0.58] });
export const CAM30: PKey[] = [
  { t: 0, cam: LAUNCH },                                                                         // frame 0: her glowing limb, close; his rocket lifts off it
  { t: 7.6, cam: { ...DOT, r: 0.0250, par: [-0.02, -0.008] }, ease: E.smooth },                  // ... and we fall back from her faster than he climbs, until she is one small blue dot
  { t: 8.96, cam: { ...DOT, r: 0.0262, par: [0.03, 0.012] }, ease: E.lin },                      // a slow push while she says it
  { t: T.intro, cam: { ...DOT, r: 0.0244, par: [0.045, 0.018] }, ease: E.out },                 // on "space" the camera gives her a little room too
  { t: T.limb, cam: LIMB, ease: (u) => E.smooth(Math.pow(u, 0.8)) },                         // the approach: off the mark sooner (she is a small globe by 13.3 s, not still a dot), down over her night limb                                                   // the approach: down over her night limb
];
// one camera for 0-35.6 s: keys to the arrival (frames 0-232 are the hero slots: untouched), the shots through the verse, then the pull back to a dot
export function cam30(t: number, fmt: string = '169'): Cam {
  if (t < T.limb) return camPath(CAM30, t);
  if (t <= T.dirt0) return shotAt(t, fmt);
  const a = shotAt(T.dirt0, fmt);
  return camPath([{ t: T.dirt0, cam: a }, { t: T.dirt, cam: END(a), ease: E.smoother }, { t: 40, cam: END(a) }], t);
}
export const roomK = (fmt: string) => (fmt === '916' ? 0.72 : 1.3);   // 9:16: the room fits the narrow frame
