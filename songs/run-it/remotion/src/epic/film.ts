// @ts-nocheck
// THE FILM, 73.12 - 155.34 s (verse 2 through the crash): what the 3D world looks like at film time t.
// stateAt(t) is a pure function. Every change lands on the shot's downbeat from timeline.json (the approved rule:
// the lyric is typed, the world changes ON the downbeat). Cuts between camera set-ups are deliberate.
import { beats, kicks, lines, snares, tshot } from '../timing';
import { AVE_X, DECK_Y, GROUND_Y, PIER_Z, SHORE_Z } from './world';

const L = (id: string) => tshot(id).land;
/** sung onset of word w (0-based) of the line with this text (n-th occurrence) */
const W = (text: string, w = 0, n = 0) => { const ls = lines.filter((x) => x.text === text); const l = ls[Math.min(n, ls.length - 1)]; return l ? l.wt[Math.min(w, l.wt.length - 1)] : NaN; };
// RE-TIMED (her note on cut 1: "It doesn't seem synced to the music"): every change now lands ON THE SUNG WORD that asks for it
// ("rain", "Porsche", "collide" ...), not a bar later on the next downbeat. Instrumental moments keep their downbeats.
export const T = { CITY: W('Turn the dot into a city', 5), RAIN: W('Make it rain on just one side', 2), CAR: W('Purple Porsche, yellow brakes', 1), BRAKES: W('Purple Porsche, yellow brakes', 3),
  TL: W('Make the traffic lights collide', 4), GUYS: W('Put a little guy in every window', 6), WIRED: W("Make him type like he's wired", 5), BIRDS: W('Make the pigeons fly in circles', 2),
  HIGHER: W('Now a little higher, higher', 3), GRAV: W('Turn off gravity', 1), JUSTBIRDS: W('Just for the birds', 3), ALL: W('Now for everybody', 1), CARBACK: W('Wait, put the car back first', 5),
  BIGGER: W('Bigger, brighter', 0, 1), FIRE: W('Light it up, set it on fire', 6, 1), SPIN: W('Make it spin, make it shine', 2, 1), MOVE: W('Make the whole world move in time', 4, 1), LOUDER: W('Bigger, louder', 0, 1),
  TOWER: W('Turn the bass into a tower', 5, 1), RUN: W('Run it, run it', 0, 1), DRIVE: W('Run it (run it)', 0, 2), DRIVE2: L('s46'), ARRIVE: L('s47'), PIER: L('s48'),
  MOON1: W('Add a moon', 2), MOON2: W('Add another', 1), LOVE: W('Make them fall in love with each other', 2), TASTE: W('Make it tasteful', 2), WEIRD: W('Make it weird', 2), DRY: W('Make the ocean disappear', 3),
  BACKW: W('Bring it back', 2), WAVES: W('Every wave', 1), SING: W("Sixty frames, don't make me wait", 0), SIXTY: W("Sixty frames, don't make me wait", 1), CAL: W('Delete Mondays', 0), MONDAY: W('Delete Mondays', 1),
  SUN: W('Move the sun', 1), VERT: W('Make it vertical for everyone', 2), CLAP: W('Make the city clap on two and four', 4), ROLL: W('Turn the ceiling into the floor', 1),
  NIGHTW: W('Make it Sunday, make it night', 0), SUNDAY: W('Make it Sunday, make it night', 2), PEAK: W('Make it Sunday, make it night', 5), ONTIME: L('s62'), CRASH: L('s63'), END: L('s64') };
const beatAfter = (t: number, n = 0) => { const i = beats.findIndex((b) => b >= t - 0.02); return beats[Math.min(beats.length - 1, i + n)]; };
export const MOON1 = T.MOON1, BACK = T.BACKW, NIGHT = T.NIGHTW;
export const CRASH_STEPS = [0, 1, 2, 3, 4].map((n) => beatAfter(T.CRASH, n));
const SOFT_SNARES = snares.filter((_, i) => i % 2 === 0);
export const WALL16 = W('Run it (run it)', 0, 3);                                 // "Run it (run it)" the second time: 4 becomes 16
const beatsSince = (t0: number, t: number) => { let n = 0; for (const b of beats) { if (b > t) break; if (b >= t0 - .02) n++; } return n; };
// "Delete Mondays": a week calendar comes up a beat before the line, Monday is a wall of meetings, it is selected on "Delete" and removed on
// "Mondays"; the six-day week then shrinks into the chips at the top left.
export const CAL_IN = beats.filter((b) => b < T.CAL - .3).pop()!, CAL_OUT = T.CAL + 1.0;
export const LIGHT_T = W('Light it up, set it on fire', 0, 1);
// pixelfx events for the pixel-art flip: [start s, kind, x, y (in a 320x180 frame), seed, palette index]
export const PFX: [number, string, number, number, number, number][] = [
  [T.TL, 'pow', 160, 84, 5, 0],
  [LIGHT_T, 'fw', 64, 150, 3, 0], [LIGHT_T + .5, 'fw', 250, 156, 5, 1], [T.FIRE - .42, 'fw', 160, 140, 21, 0], [T.FIRE + .45, 'fw', 286, 150, 33, 2],
  [T.FIRE, 'tor', 96, 150, 2, 0], [T.FIRE + .08, 'tor', 160, 132, 4, 0], [T.FIRE + .16, 'tor', 226, 148, 6, 0], [T.FIRE + .1, 'pil', 60, 170, 7, 0], [T.FIRE + .2, 'pil', 268, 172, 9, 0]];
export const EPIC_FROM = beats.filter((b) => b < T.CITY - .5).pop()!, EPIC_TO = T.END;   // 71.15: the plan is on screen a beat before "city"

const clamp = (x: number, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const lerp = (a: number, b: number, k: number) => a + (b - a) * k;
const v3 = (a: number[], b: number[], k: number) => [lerp(a[0], b[0], k), lerp(a[1], b[1], k), lerp(a[2], b[2], k)];
const pr = (t: number, a: number, b: number) => clamp((t - a) / (b - a));
const smooth = (x: number) => { x = clamp(x); return x * x * (3 - 2 * x); };
const ease = (x: number) => { x = clamp(x); return x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2; };
const out3 = (x: number) => 1 - Math.pow(1 - clamp(x), 3);
/** a settle with one overshoot, 0 -> 1 */
const spring = (x: number) => { x = clamp(x); return 1 - Math.exp(-6 * x) * Math.cos(9 * x); };
const lastAt = (arr: number[], t: number) => { let lo = 0, hi = arr.length; while (lo < hi) { const m = (lo + hi) >> 1; if (arr[m] <= t) lo = m + 1; else hi = m; } return lo > 0 ? arr[lo - 1] : -99; };
const envOf = (arr: number[], t: number, k = 6) => Math.exp(-(t - lastAt(arr, t)) * k);

export const PIER_CAM = { p: [3.5, 2.05, PIER_Z + 9.3], l: [-3.3, 3.9, PIER_Z - 27.5], fov: 38 };
const WIDE_CAM = { p: [34, 20, 1840], l: [0, 62, 0], fov: 38 };
const HERO_YAW = Math.PI - 0.34;

/** where the car is */
function carAt(t: number) {
  const c: any = { x: AVE_X, y: GROUND_Y, z: 302, yaw: 0, vis: t >= T.CAR ? 1 : 0, spin: 0, s: 1, roll: 0, pitch: 0 };
  if (t < T.ALL) { const k = out3(pr(t, T.CAR, T.CAR + 1.6)); c.z = 294 + 8 * k; c.spin = (c.z - 294) / .337; c.s = t < T.CAR + .5 ? .82 + .18 * spring(pr(t, T.CAR, T.CAR + .5)) : 1; }
  else if (t < T.CARBACK) { const k = smooth(pr(t, T.ALL, T.ALL + 1.5)), g = 1 - smooth(pr(t, T.CARBACK - .5, T.CARBACK - .28)); c.y = GROUND_Y + 3.4 * k + .15 * Math.sin((t - T.ALL) * 2.2) * k * g; c.roll = .38 * k * g; c.pitch = -.2 * k * g; c.yaw = .5 * k * g; c.spin = (t - T.ALL) * 1.2; }
  else if (t < T.DRIVE) { const k = pr(t, T.CARBACK, T.CARBACK + .14); const b = Math.exp(-(t - T.CARBACK) * 7) * Math.sin((t - T.CARBACK) * 22) * .12 * (k >= 1 ? 1 : 0);
    c.y = GROUND_Y + 3.4 * (1 - k * k) + Math.max(0, b); c.roll = 0; c.pitch = 0; c.yaw = 0; }
  else { const k = pr(t, T.DRIVE, T.PIER - 1.5), s = k * k * (3 - 2 * k); c.z = lerp(302, PIER_Z, s); c.spin = (c.z - 302) / .337;
    c.y = c.z < SHORE_Z - 24 ? GROUND_Y : c.z < SHORE_Z + 2 ? lerp(GROUND_Y, DECK_Y, (c.z - (SHORE_Z - 24)) / 26) : DECK_Y;
    c.x = lerp(AVE_X, -0.7, smooth(pr(c.z, SHORE_Z - 80, SHORE_Z + 60)));
    const sp = out3(pr(t, T.PIER - 2.0, T.PIER - .6)); c.yaw = HERO_YAW * sp; c.roll = -.05 * Math.sin(sp * Math.PI); }   // the handbrake turn onto the pier
  return c;
}

export function stateAt(t: number) {
  const S: any = { t, crash: 0, grow: out3(pr(t, T.CITY, T.CITY + 1.7)), bounce: 0, env: envOf(beats, t), tower: 0.42, guys: 0, wired: 0, lit: 1, clap: 0, dusk: 0, tot: 0, weird: 0,
    sun: [0.36, -0.50, 0], m1: [-0.5, -1.2, 0, 1], m2: [0.4, -1.2, 0, 1], ocean: 1, wave: 1, waterT: t, wet: t >= T.RAIN ? 1 : 0, dot: 1,
    rain: t >= T.RAIN && t < T.FIRE ? 1 : 0, rainT: Math.max(0, Math.min(t, T.GRAV) - T.RAIN) - 0.3 * clamp(t - T.GRAV, 0, T.CARBACK - T.GRAV) + Math.max(0, t - T.CARBACK) + 40,
    tl: 0, tlHit: 0, tlOn: t < T.BIGGER + 2 ? 1 : 0, birds: t >= T.BIRDS && t < T.FIRE ? 1 : 0, birdT: t < T.JUSTBIRDS ? t : T.JUSTBIRDS + (t - T.JUSTBIRDS) * .12, birdFloat: 0,
    fire: -1, cause: 0, car: carAt(t), hk: 1, fuse: 9999, gwave: 1e6, clapX: 0, love: 0, flash: 0, sq: 0, level: 0, float: 0, tlFlash: 0, bot: { mode: 'drive', head: 0, nod: 0 }, sat: 1, crop: 0, cam: { p: [0, 300, 60], l: [0, 0, 0], fov: 38, roll: 0 }, fps: null, cal: 0, cursor: 0, labels: 0 };
  const cam = S.cam;
  // ---------------- VERSE 2: the street ----------------
  if (t < T.RAIN + .9) { const k = ease(pr(t, T.CITY, T.RAIN + .9)); cam.p = [lerp(0, -26, k), lerp(300, 64, k), lerp(60, 330, k)]; cam.l = [0, lerp(0, 26, k), lerp(0, -30, k)]; cam.fov = lerp(38, 42, k); }
  else if (t < T.CAR) { const k = pr(t, T.RAIN, T.CAR); cam.p = [0.7, 1.25, 348 - 4 * k]; cam.l = [0.2, 7.2, 0]; cam.fov = 42; }
  else if (t < T.TL - 1.0) { const k = pr(t, T.CAR, T.TL - 1.0); cam.p = [2.9 - .5 * k, 1.0, 309.5 - .8 * k]; cam.l = [-3.3, 0.95, 301.5]; cam.fov = 34; }
  else if (t < T.GUYS) { const k = pr(t, T.TL - 1.0, T.GUYS); cam.p = [0.6, 2.4, 331 - 2.5 * k]; cam.l = [-0.2, 5.6, 318]; cam.fov = 44;
    const q = pr(t, T.TL - .30, T.TL); S.tl = q * q; S.tlHit = t >= T.TL ? 1 + Math.exp(-(t - T.TL) * 5) : 0; S.tlFlash = t >= T.TL ? Math.exp(-(t - T.TL) * 8) : 0;
    if (t >= T.TL && t < T.TL + .9) S.clap = 1.1 * Math.exp(-(t - T.TL) * 4.5); }
  else if (t < T.GUYS + 1.5) { const k = pr(t, T.GUYS, T.GUYS + 1.5); cam.p = [5, 16 + 3 * k, 372]; cam.l = [-6, 30, 150]; cam.fov = 50; }
  else if (t < T.BIRDS) { const k = pr(t, T.GUYS, T.BIRDS); cam.p = [7 - 2 * k, 8 + 5 * k, 304 - 6 * k]; cam.l = [-13.6, 13 + 9 * k, 292 - 10 * k]; cam.fov = 30; }
  else if (t < T.GRAV) { const k = ease(pr(t, T.BIRDS, T.GRAV)); cam.p = [1, lerp(3, 150, k), lerp(354, 440, k)]; cam.l = [0, lerp(34, 55, k), lerp(318, 60, k)]; cam.fov = 40; }
  else if (t < T.JUSTBIRDS) { const k = pr(t, T.GRAV, T.JUSTBIRDS); cam.p = [1 + 14 * k, 150 + 10 * k, 440]; cam.l = [0, 55, 60]; cam.fov = 40; }
  else if (t < T.ALL) { const k = pr(t, T.JUSTBIRDS, T.ALL); cam.p = [9 - 2 * k, 27 + 3 * k, 352]; cam.l = [0, 38 + 5 * k, 318]; cam.fov = 36; }
  else if (t < T.BIGGER) { const k = pr(t, T.ALL, T.BIGGER); cam.p = [4.6, 1.1 + .5 * k, 311.5]; cam.l = [-3.2, 1.2 + 2.6 * smooth(pr(t, T.ALL, T.ALL + 1.5)), 301.5]; cam.fov = 38; }
  if (t >= T.TL) { S.tl = Math.max(S.tl, t >= T.GUYS ? 1 : S.tl); if (t >= T.GUYS) S.tlHit = 1; }
  if (t >= T.GUYS) { S.guys = t < T.BIRDS ? 1 : 0.5; S.gwave = (t - T.GUYS) * 420; } if (t >= T.WIRED) S.wired = 1; if (t >= T.WIRED + .9 && t < T.BIRDS) S.look = 1;
  // ---- STYLE FLIPS (cut 5): a prompt can re-render the whole picture
  if (t < T.RAIN) { S.style = 1; S.styleK = 1 - smooth(pr(t, T.RAIN - .3, T.RAIN)); }
  if (t >= T.RAIN && t < T.CAR) { const k = pr(t, T.RAIN, T.CAR), a = out3(pr(t, T.RAIN + .05, T.RAIN + .55));   // "rain on just one side": Claude waters the west half of town
    cam.p = [330 - 30 * k, 230, 1300 - 70 * k]; cam.l = [-300, 320, -400]; cam.fov = 30;
    S.giant = { on: 1, x: -250, y: -70, z: -800, yaw: 0, lean: .30, headPitch: .30, headYaw: -.28, can: { p: [-470, lerp(450, 410, a), -610], yaw: -Math.PI / 2, tilt: lerp(-.05, .62, a), pour: smooth(pr(t, T.RAIN + .3, T.RAIN + .8)), oneHand: 1 } }; }
  if (t >= T.RAIN && t < T.GRAV) S.flash = .42 * Math.pow(envOf(SOFT_SNARES, t, 5), 1.5);   // lightning: every other snare, soft, never a strobe
  if (t >= T.ALL && t < T.BIGGER) S.float = smooth(pr(t, T.ALL, T.ALL + 1.4)) * (1 - pr(t, T.BIGGER - .2, T.BIGGER));   // the car goes back FIRST; everything else stays up until the chorus
  if (t >= T.JUSTBIRDS && t < T.BIGGER) S.birdFloat = smooth(pr(t, T.JUSTBIRDS, T.JUSTBIRDS + .7));
  // ---------------- CHORUS 2: bigger ----------------
  if (t >= T.BIGGER) { S.hk = 1 + .40 * spring(pr(t, T.BIGGER, T.BIGGER + .7)) + .40 * spring(pr(t, T.LOUDER, T.LOUDER + .7)) - .50 * smooth(pr(t, T.RUN, T.DRIVE));
    const LIGHT = W('Light it up, set it on fire', 0, 1); if (t >= LIGHT && t < T.RUN) S.fuse = Math.min(8999, 520 * pr(t, LIGHT, T.FIRE)) + (t >= T.FIRE ? 8000 : 0);
    S.lit = 1 + 1.2 * out3(pr(t, T.BIGGER, T.BIGGER + .5)); S.guys = t < T.RUN ? 0.34 : 0; S.wired = S.guys > 0 ? 1 : 0; }
  if (t >= T.BIGGER && t < T.FIRE) { const k = out3(pr(t, T.BIGGER, T.FIRE)); const kh = out3(pr(t, T.BIGGER, T.BIGGER + 1.1)); cam.p = [lerp(4.6, 0.5, kh), lerp(1.6, 190, k), lerp(311.5, 780, k * k)]; cam.l = v3([-3.2, 1.2, 301.5], [0, 40, 0], kh); cam.fov = 38; }
  if (t >= T.FIRE && t < T.SPIN) { const k = pr(t, T.FIRE, T.SPIN); cam.p = [-140 + 30 * k, 70, 930]; cam.l = [0, 190, 0]; cam.fov = 42; }
  if (t >= T.SPIN && t < T.MOVE) { const k = pr(t, T.SPIN, T.MOVE), a = -0.35 + Math.PI * 1.15 * (k * .55 + smooth(k) * .45);            // "Make it spin": the island is the label of a record
    cam.p = [Math.sin(a) * 2350, 2250 - 250 * k, Math.cos(a) * 2350]; cam.l = [0, -60, 0]; cam.fov = 44; }
  if (t >= T.MOVE && t < T.LOUDER) { const k = pr(t, T.MOVE, T.LOUDER); cam.p = [-260 + 120 * k, 26, 1750 - 60 * k]; cam.l = [0, 150, 0]; cam.fov = 26; S.eq = smooth(pr(t, T.MOVE, T.MOVE + .2)); }   // the skyline is an equaliser
  if (t >= T.MOVE) S.bounce = t < T.RUN ? 0.14 : 0.05 * (1 - pr(t, T.RUN, T.RUN + 2));
  if (t >= T.LOUDER && t < T.RUN) S.eq = .55 * (1 - smooth(pr(t, T.RUN - .5, T.RUN)));
  if (t >= T.LOUDER && t < T.TOWER) { const k = ease(pr(t, T.LOUDER, T.TOWER)); const a = 2.1; cam.p = v3([Math.sin(a) * 1120, 190, Math.cos(a) * 1120], [0, 470, 2150], k); cam.l = [0, lerp(110, 150, k), 0]; cam.fov = 38; S.bounce = 0.2; }
  if (t >= T.TOWER) S.tower = 0.42 + 1.05 * spring(pr(t, T.TOWER, T.TOWER + 1.1)) + (t < T.DRIVE ? 0.05 * S.env : 0) - .47 * smooth(pr(t, T.RUN + 2, T.DRIVE));
  if (t >= T.TOWER && t < T.RUN) { const k = pr(t, T.TOWER, T.RUN); cam.p = [-330 + 20 * k, 60, 640]; cam.l = [-64, 120 + 150 * out3(pr(t, T.TOWER, T.TOWER + .9)), -52]; cam.fov = 40; }
  // the causeway builds itself out to sea, the lamps arriving with it
  if (t >= T.RUN) S.cause = t < T.DRIVE ? smooth(pr(t, T.RUN, T.DRIVE - .4)) : 1;
  if (t >= T.RUN && t < T.DRIVE) { const fz = SHORE_Z + (PIER_Z + 22 - SHORE_Z) * S.cause; cam.p = [30, 24, fz + 70]; cam.l = [0, 16, fz - 160]; cam.fov = 40; }
  if (t >= T.RUN) { S.lit = 1.5; S.rain = 0; }
  // ---------------- the drive ----------------
  const c = S.car;
  if (t >= T.DRIVE && t < T.ARRIVE) {
    const seg = t < WALL16 ? 0 : t < WALL16 + 1.96 ? 1 : t < WALL16 + 3.92 ? 2 : t < WALL16 + 4.9 ? 3 : 4;
    if (seg === 0) { cam.p = [c.x + 2.5, c.y + 1.3, c.z + 9.5]; cam.l = [c.x - .2, c.y + .75, c.z]; cam.fov = 42; }                       // front three-quarter
    if (seg === 1) { cam.p = [c.x + 7.6, c.y + 1.0, c.z + 1.6]; cam.l = [c.x, c.y + .62, c.z + .4]; cam.fov = 36; }                         // side, tracking
    if (seg === 2) { cam.p = [c.x - 1.6, c.y + 2.5, c.z - 8.6]; cam.l = [c.x, c.y + .8, c.z + 7]; cam.fov = 44; }                          // rear chase
    if (seg === 3) { cam.p = [c.x + 2.9, c.y + .50, c.z + 2.9]; cam.l = [c.x + .85, c.y + .36, c.z + 1.35]; cam.fov = 26; }                 // the front wheel: the yellow caliper
    if (seg === 4) { cam.p = [c.x + 9.5, c.y + 1.5, c.z + 5.5]; cam.l = [c.x, c.y + .7, c.z + 1]; cam.fov = 40; }                           // one real world again
    S.tiles = t < WALL16 ? 2 : t < WALL16 + 4.9 ? 4 : t < WALL16 + 5.88 ? 2 : 1; S.tick = S.tiles === 4 ? 3 : 0; }   // the styles hold still: no shuffling
  if (t >= T.ARRIVE && t < T.PIER) { const k = pr(t, T.ARRIVE, T.PIER); cam.p = [6.2 - 1.5 * k, 2.3, PIER_Z + 15 - 3 * k]; cam.l = [-.4, 1.9, PIER_Z - 30]; cam.fov = 40; }
  // ---------------- BRIDGE: the bay ----------------
  if (t >= T.PIER) { S.sun[2] = out3(pr(t, T.PIER, T.PIER + .8)); S.dusk = S.sun[2] * .85; S.lit = 1.3; cam.p = PIER_CAM.p.slice(); cam.l = PIER_CAM.l.slice(); cam.fov = 38;
    S.m1 = [-0.42, lerp(-1.1, -0.12, spring(pr(t, MOON1, MOON1 + .8))), t >= MOON1 ? 1 : 0, 1]; S.m2 = [0.40, lerp(-1.1, -0.20, spring(pr(t, T.MOON2, T.MOON2 + .8))), t >= T.MOON2 ? 1 : 0, 1]; }
  if (t >= T.LOVE) { const k = smooth(pr(t, T.LOVE, T.LOVE + .8)), w = Math.sin(pr(t, T.LOVE + .8, T.TASTE) * Math.PI) * .012;
    S.m1 = [lerp(-0.42, -0.115, k) + w, lerp(-0.12, 0.01, k), 1, 1]; S.m2 = [lerp(0.40, 0.105, k) - w, lerp(-0.20, -0.01, k), 1, 1]; }
  if (t >= T.LOVE && t < T.TASTE) { const k = pr(t, T.LOVE, T.TASTE); S.love = pr(t, T.LOVE + .25, T.LOVE + 1.15);
    cam.p = [3.5, 2.05, PIER_Z + 9.3]; cam.l = [3.5, 2.05 + Math.tan(12.9 * Math.PI / 180) * 1700, PIER_Z + 9.3 - 1700]; cam.fov = 12.5 - 1.3 * smooth(k); S.clap = .30 + .22 * Math.sin(t * 3.1); }
  if (t >= T.TASTE && t < T.DRY) { cam.p = [3.5, 2.05, PIER_Z + 9.3]; cam.l = [3.5 + 0, 2.05 + Math.tan(13.4 * Math.PI / 180) * 1700, PIER_Z + 9.3 - 1700]; cam.fov = 13; }
  if (t >= T.PIER) S.bot = { mode: 'stand', x: 1.7, y: DECK_Y + .14, z: PIER_Z - 3.2, yaw: Math.PI + .12, head: 0, nod: -.32 };
  if (t >= T.TASTE) { const k = smooth(pr(t, T.TASTE, T.TASTE + .3)); S.sat = 1 - .55 * smooth(pr(t, T.TASTE + .9, T.TASTE + 1.2)); S.m1 = [lerp(-0.115, -0.21, k), 0.005, 1, 1]; S.m2 = [lerp(0.105, 0.21, k), -0.005, 1, 1]; }
  if (t >= T.TASTE && t < T.TASTE + .9) { const b = S.bot; b.head = Math.PI * out3(pr(t, T.TASTE + .05, T.TASTE + .35)); b.nod = 0;   // Claude turns his head all the way round. Deadpan.
    cam.p = [b.x + .5, b.y + 1.55, b.z + 2.6]; cam.l = [b.x, b.y + 1.38, b.z]; cam.fov = 30; }
  if (t >= T.WEIRD && t < T.DRY) S.flip = smooth(pr(t, T.WEIRD, T.WEIRD + .3));
  if (t >= T.WEIRD) { S.sq = 1; S.tower = 1 + .9 * spring(pr(t, T.WEIRD, T.WEIRD + .5)); const a = (t - T.WEIRD) * 5.2, k = out3(pr(t, T.WEIRD, T.WEIRD + .25)); S.sat = 1; S.weird = k * (.6 + .4 * Math.sin(a * 2.1));
    S.m1 = [-0.21 * Math.cos(a), -0.14 * Math.sin(a) * k, 1, 1 + .15 * Math.sin(a * 3)]; S.m2 = [0.21 * Math.cos(a), 0.14 * Math.sin(a) * k, 1, 1 - .15 * Math.sin(a * 3)]; cam.roll = .10 * Math.sin(a * .9) * k; }
  if (t >= T.DRY && t < BACK + .4) S.drain = t < BACK ? out3(pr(t, T.DRY, T.DRY + .25)) : 1 - pr(t, BACK, BACK + .4);
  if (t >= T.DRY) { S.weird = 0; S.sq = 0; S.tower = 1; cam.roll = 0; S.level = t < BACK ? -46 * smooth(pr(t, T.DRY + .35, T.DRY + 1.2)) : -46 * (1 - out3(pr(t, BACK, BACK + .4))); const k = smooth(pr(t, T.DRY, T.DRY + .5)); S.m1 = [lerp(-0.21, -0.30, k), 0.05, 1, 1]; S.m2 = [lerp(0.21, 0.27, k), -0.08, 1, 1];
    S.ocean = t < BACK ? 0 : 1; S.wave = t < BACK ? 1 : t < T.WAVES ? 0 : lerp(2.2, 1, out3(pr(t, T.WAVES, T.WAVES + 1.5)));
    if (t < T.SIXTY) { const k2 = pr(t, T.DRY, T.SIXTY), up = out3(pr(t, T.DRY, T.DRY + .45)) * (1 - smooth(pr(t, BACK, BACK + .35))), hy = lerp(150, 372, up);   // Claude pulls the plug, and puts it back
      cam.p = [740 - 40 * k2, 430, 2380]; cam.l = [-200, 320, 1020]; cam.fov = 40;
      S.giant = { on: 1, x: -455, y: -75, z: 1075, yaw: Math.PI / 2, lean: .34, headPitch: .42, headYaw: 0, armSwap: 0, L: [-150, hy, 1060], pinch: 1, plug: { x: -150, y: hy - 165, z: 1060, hx: -150, hy: hy - 8, hz: 1060 } }; }
    // "Sixty frames": the world stutters at 12 fps while she sings it, and runs smooth from the downbeat
    const sing = T.SING; if (t >= sing && t < T.SIXTY) { S.waterT = sing + Math.floor((t - sing) * 12) / 12; S.fps = 24; } else if (t >= T.SIXTY) S.fps = 60; }
  if (t >= CAL_OUT && t < T.CRASH) S.cal = t < T.SUNDAY ? 2 : 3;   // the week as chips (after the calendar): Monday gone, then Sunday lit   // the week: shown, Monday deleted, Sunday lit
  if (t >= T.SUN) { const k = ease(pr(t, T.SUN, T.SUN + 1.5)); S.sun = [lerp(0.36, 0, k), lerp(-0.50, 0, k) + .06 * Math.sin(k * Math.PI), 1]; S.cursor = t < T.SUN + 1.9 ? 1 : 0; S.dusk = .85 - .25 * k; }
  if (t >= T.VERT && t < T.CLAP) S.crop = smooth(pr(t, T.VERT, T.VERT + .3)) * (1 - smooth(pr(t, T.CLAP - .28, T.CLAP)));
  if (t >= T.CLAP && t < T.ROLL) { S.clap = envOf(snares, t, 7); S.clapX = Math.pow(envOf(snares, t, 9), .7); const k = pr(t, T.CLAP, T.ROLL); cam.p = [150 - 30 * k, 80, 930]; cam.l = [0, 120, 0]; cam.fov = 38; }
  if (t >= T.ROLL && t < T.PEAK) { cam.roll = Math.PI * 2 * ease(pr(t, T.ROLL, T.ROLL + 1.6)); }
  if (t >= NIGHT) { const k = ease(pr(t, NIGHT, T.PEAK)); S.m1 = [lerp(-0.30, -0.034, k), lerp(0.05, 0, k), 1, 1]; S.m2 = [lerp(0.27, 0.040, k), lerp(-0.08, 0.012, k), 1, 1];
    S.tot = smooth(pr(t, T.PEAK - .35, T.PEAK)); S.dusk = .6 * (1 - S.tot); }
  // ---------------- THE PEAK, the pull-back, the crash ----------------
  if (t >= T.PEAK) { S.tot = 1; S.dusk = 0; S.sun = [0, 0, 1]; S.m1 = [-0.034, 0, 1, 1]; S.m2 = [0.040, 0.012, 1, 1]; S.fps = t < T.CRASH ? 60 : null;
    const push = pr(t, T.PEAK, T.ONTIME - 1.2); const p0 = [PIER_CAM.p[0] - .1 * push, PIER_CAM.p[1], PIER_CAM.p[2] - .5 * push];
    const tt = Math.min(t, T.CRASH - 1 / 30), k = ease(pr(tt, T.ONTIME - 1.2, T.CRASH - .25)), kh = smooth(clamp(k * 1.25)), kz = k * k * (3 - 2 * k);
    cam.p = [lerp(p0[0], WIDE_CAM.p[0], kz), lerp(p0[1], WIDE_CAM.p[1], kh), lerp(p0[2], WIDE_CAM.p[2], kz)];
    cam.l = [lerp(PIER_CAM.l[0], WIDE_CAM.l[0], kz), lerp(PIER_CAM.l[1], WIDE_CAM.l[1], kh), lerp(PIER_CAM.l[2], WIDE_CAM.l[2], kz)]; cam.fov = 38; }
  if (t >= T.CRASH) { let n = 0; for (const b of CRASH_STEPS) if (t >= b) n++; S.crash = [0, 0.22, 0.4, 0.58, 0.72, 0.85][n]; S.labels = n; S.waterT = T.CRASH; S.env = 0; }
  if (t >= T.RUN && t < T.DRIVE) { const bl = beats.filter((b) => b >= T.RUN - .02), n = beatsSince(T.RUN, t);   // let me see what we can do: three styles, four beats each, dissolving
    if (n > 0) { const seg = Math.min(2, (n - 1) >> 2), R = [1, 6, 3], ts = bl[seg * 4]; S.style = R[seg]; S.styleB = seg > 0 ? R[seg - 1] : 0; S.styleX = smooth(pr(t, ts, ts + .32)); } }   // let me see what we can do: a style reel on the beat
  if (t >= T.CARBACK - 1.0 && t < T.BIGGER) { const c2 = S.car, dn = out3(pr(t, T.CARBACK - 1.0, T.CARBACK - .5)), grip = smooth(pr(t, T.CARBACK - .5, T.CARBACK - .3)), rel = smooth(pr(t, T.CARBACK + .26, T.CARBACK + .4)), up = smooth(pr(t, T.CARBACK + .38, T.BIGGER));
    S.tw = { on: 1, x: c2.x, y: c2.y + .5 + 60 * (1 - dn) + 80 * up, z: c2.z, open: Math.min(1, (1 - grip) + rel) }; }   // "put the car back first": tweezers
  if (t >= T.TL && t < T.TL + .7) { S.style = 5; S.styleK = Math.min(pr(t, T.TL, T.TL + .07), 1 - pr(t, T.TL + .5, T.TL + .7)); }                                   // the smash is a pixel-art POW
  if (t >= T.BIRDS && t < T.GRAV) S.spinner = 1;                           // the pigeons fly in circles: a loading spinner
  if (t >= T.BIGGER && t < LIGHT_T) { S.style = 2; S.styleK = smooth(pr(t, T.BIGGER, T.BIGGER + .32)); }   // brighter: broad daylight
  if (t >= T.SPIN && t < T.MOVE) S.vinyl = 1;
  if (t >= T.LOUDER && t < T.RUN) { S.kamp = 1 - smooth(pr(t, T.RUN - .6, T.RUN)); const ks = kicks.filter((x) => x <= t).slice(-4); S.kr = [0, 1, 2, 3].map((i) => (ks[ks.length - 1 - i] !== undefined ? t - ks[ks.length - 1 - i] : 9)); }
  if (t >= T.GUYS && t < T.BIRDS) S.flash *= .2;                                 // keep the lightning off the window shot
  if (t >= LIGHT_T && t < T.SPIN) { S.style = 5; S.styleB = 2; S.styleX = smooth(pr(t, LIGHT_T, LIGHT_T + .3)); }
  if (t >= T.TASTE && t < T.WEIRD) { S.style = 3; S.sat = 1; }
  if (t >= T.WEIRD && t < T.DRY) { S.style = 6; S.styleB = 3; S.styleX = smooth(pr(t, T.WEIRD, T.WEIRD + .25)); }
  const kk = envOf(kicks, t, 9); S.kick = t < T.CRASH ? kk : 0; if (t < T.CRASH) cam.fov -= 0.3 * kk;
  if (t >= T.BIGGER && t < T.PIER) S.clap = Math.max(S.clap, 0.22 * envOf(snares, t, 5));
  return S;
}
