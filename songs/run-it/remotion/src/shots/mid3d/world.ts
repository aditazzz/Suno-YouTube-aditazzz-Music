// The grey-box world of the 3D middle: deterministic (seeded), built once. Units metres, Y up (cam/_make.py).
//   near city  facade z=0, two rows, the hero window (4,18,0) the camera flies through (s48)
//   the bay    z -16 .. -270 (ocean, reflections, the canvas underneath in s53)
//   far city   facade z=-270, two rows, the bass tower (x=-46), clocks (s62)
//   the sky    sun (starts low, dragged to SUN_FINAL in s57), two moons that fall in love, the eclipse at 147.51
//   car set    a separate location at x=3000: the "bass tower" lying along X, a road, the car (s58)
import { clamp, easeInOut3, easeOut3, lerp, prog, smooth, spring } from './anim';
import { M } from './times';

export const P = {
  skyTop: '#04080e', skyGlow: '#1a2233', building: '#192231', ocean: '#0a0d14', oceanDeep: '#0a1626', ghost: '#4b5465',
  window: '#ffcf7a', windowWarmWhite: '#fff3dc', ring: '#fffaf4', coronaInner: '#fff3ea', coronaGold: '#f2cf8a',
  reflectionGold: '#e8d2a6', moonCool: '#dfe6f2', moonWarm: '#f6e3c0', moonDisk: '#0b0a12', sun: '#ffd99a',
  car: '#5b2d94', carHi: '#8a5cd0', carLo: '#2f1452', caliper: '#ffd21f',
  // the 2.5D city at the match-cut (CH2/POST2a swatches): the first 3D frame matches these, then grades to the 3D ones
  flatSkyTop: '#0a0f1a', flatSkyBot: '#16233a', flatBuilding: '#1f263e',
  street: '#10151f', quay: '#0d121c',
};

function rng(seed: number) { let a = seed >>> 0; return () => { a = (a + 0x6d2b79f5) >>> 0; let t = a; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }

export type Win = { u: number; v: number; warm: boolean; seq: number }; // u,v = centre on the front face, from its left/bottom
export type Bld = { id: string; x: number; z: number; w: number; d: number; h: number; wins: Win[]; hero?: boolean; tower?: boolean;
  crash: 'wire' | 'check' | 'grey'; clock?: number };

function row(r: () => number, x0: number, x1: number, zFront: number, dMin: number, dMax: number, hMin: number, hMax: number,
  lit: number, tag: string, skip?: [number, number], force?: Partial<Bld>[]): Bld[] {
  const out: Bld[] = []; let x = x0, i = 0;
  const used = new Set<Partial<Bld>>();
  while (x < x1) {
    let w = 5 + r() * 6, h = hMin + r() * (hMax - hMin);
    // a forced building (hero, tower) goes in as soon as the next random one would run into it
    const f = force?.find((b) => !used.has(b) && b.x! < x + w + 1.7);
    if (f) { used.add(f); x = Math.max(x, f.x!); w = f.w ?? w; h = f.h ?? h; }
    if (skip && x + w > skip[0] && x < skip[1]) { x = skip[1] + 0.8; continue; }
    const d = dMin + r() * (dMax - dMin);
    const wins: Win[] = [];
    const cols = Math.max(1, Math.floor((w - 1.2) / 1.9)), rows = Math.max(1, Math.floor((h - 2.4) / 2.7));
    const cw = w / cols;
    for (let c = 0; c < cols; c++) for (let k = 0; k < rows; k++) {
      if (r() < lit) wins.push({ u: (c + 0.5) * cw, v: 2.4 + k * 2.7, warm: r() < 0.15, seq: r() });
    }
    const cr = r();
    out.push({ id: `${tag}${i++}`, x, z: zFront - d, w, d, h, wins, crash: cr < 0.42 ? 'wire' : cr < 0.72 ? 'check' : 'grey', ...(f ?? {}) });
    x += w + 0.5 + r() * 1.2;
  }
  return out;
}

// ---------- near city (POST2b): the 2.5D city made real ----------
export const HERO = { x: 1, w: 6, h: 26, win: { x: 4, y: 18 } };
export const NEAR: Bld[] = (() => {
  const r = rng(46);
  const front = row(r, -66, 66, 0, 7, 9, 10, 30, 0.26, 'n', undefined, [{ x: HERO.x, w: HERO.w, h: HERO.h, hero: true }]);
  const hero = front.find((b) => b.hero)!;
  // the hero: one centred column of windows on the 2.7 m floor grid through y=18; the y=18 window (the guy typing) always lit
  hero.wins = [-5, -4, -3, -2, -1, 0, 1, 2].map((m) => ({ u: HERO.win.x - HERO.x, v: HERO.win.y + 2.7 * m, warm: false, seq: r() }))
    .filter((w, i) => w.v > 2 && w.v < HERO.h - 1.5 && (w.v === HERO.win.y || [1, 3, 6].includes(i)));
  const back = row(r, -70, 70, -10, 6, 8, 16, 38, 0.2, 'nb', [-2, 10]);
  return [...front, ...back];
})();

// ---------- far city (BRIDGE): the skyline across the bay ----------
export const FAR_Z = -270;
export const TOWER_X = -46;
export const FAR: Bld[] = (() => {
  const r = rng(61);
  const front = row(r, -190, 190, FAR_Z, 10, 18, 12, 40, 0.24, 'f', undefined, [{ x: TOWER_X, w: 10, h: 74, tower: true, clock: 1 }]);
  const back = row(r, -200, 200, FAR_Z - 22, 10, 16, 22, 56, 0.18, 'fb');
  // clocks: the tower + four more on front-row roofs (s62: every clock snaps to 2:29)
  const picks = front.filter((b) => !b.tower && b.h > 26 && Math.abs(b.x) < 120);
  picks.filter((_, i) => i % Math.max(1, Math.floor(picks.length / 4)) === 0).slice(0, 4).forEach((b) => (b.clock = 0.6));
  return [...front, ...back];
})();

// ---------- the sky ----------
export const SUN_START = [70, 96, -900];
export const SUN_FINAL = [0, 220, -900];
export const SUN_R = 22;
export const MOON_R = [24, 20]; // moon 2 is slightly smaller (the egg)
const MOON_Z = -860;

/** sun position: low over the far skyline until "Move the sun" drags it (gizmo) to SUN_FINAL, overshoot + settle */
export function sunPos(t: number): number[] {
  const k = t < M.S57 ? 0 : spring(t - M.S57, 1.25, 0.72);
  return SUN_START.map((v, i) => lerp(v, SUN_FINAL[i], k));
}
/** the two moons: rise (moon 1 on "moon" 126.98, moon 2 on the bar-66 downbeat), orbit each other while drifting to
 *  the sun, flank it when it's moved (s57), slide across it on "night" (146.53) and cover it on totality (147.51). */
export function moonsAt(t: number): { p: number[][]; rise: number[]; total: number } {
  const rise = [spring(t - M.MOON1, 0.9, 0.78), spring(t - M.S49, 0.9, 0.78)];
  // the pair's centre and separation
  const cStart = [-30, 128], cSun = [SUN_FINAL[0], SUN_FINAL[1]];
  const drift = smooth(prog(t, M.S50, M.S57));
  const c = [lerp(cStart[0], cSun[0], drift), lerp(cStart[1], cSun[1] + 10, drift) - 10 * smooth(prog(t, M.S57, M.S58))];
  let sep = lerp(150, 116, smooth(prog(t, M.S49, M.S57)));
  sep = lerp(sep, 18, easeInOut3(prog(t, M.NIGHT - 0.35, M.S61))); // they slide across the sun, overlapping at totality
  // orbit angle: from the start of "fall in love" they circle each other, settling level (moon 1 left) by s57
  const spin = t < M.S50 ? 0 : (1 - smooth(prog(t, M.S50, M.S57))) * Math.sin((t - M.S50) * 0.9) * 0.9;
  const a = spin;
  const off = [Math.cos(a) * sep / 2, Math.sin(a) * sep / 2];
  const low = (k: number) => (1 - k) * -160; // below the skyline before they rise
  const p = [
    [c[0] - off[0], c[1] - off[1] + low(rise[0]), MOON_Z],
    [c[0] + off[0], c[1] + off[1] + 4 * (1 - smooth(prog(t, M.NIGHT, M.S61))) + low(rise[1]), MOON_Z + 2],
  ];
  return { p, rise, total: smooth(prog(t, M.S61 - 0.25, M.S61)) };
}

// ---------- grades / passes ----------
/** POST2b render passes: flat at the match-cut (116.21) -> shadows (0.5 s) -> reflections through the "Ooh" -> full light ("do", 122.08) */
export function passes(t: number) {
  const shade = easeOut3(prog(t, M.S46, M.S46 + 0.5));
  const refl = smooth(prog(t, M.S46 + 1.2, M.S47));
  const light = easeOut3(prog(t, M.S47, M.S47 + 0.45));
  const label = t < M.S46 ? 'shading' : t < M.S46 + 1.2 ? 'shadows' : t < M.S47 ? 'reflections' : 'light';
  return { shade, refl, light, label, n: t < M.S46 + 1.2 ? 2 : t < M.S47 ? 3 : 4 };
}
/** "Make it tasteful": saturation settles, soft halos on the moons */
export const tasteful = (t: number) => smooth(prog(t, M.S51, M.S51 + 0.6));
/** "Make it weird": one bar of chrome ocean + taffy buildings (ocean part ends when it's deleted on the snare) */
export const weird = (t: number) => clamp(spring(t - M.S52, 1.6, 0.55)) * (1 - smooth(prog(t, M.S52 + 1.96 - 0.35, M.S52 + 1.96)));
/** ocean present? deleted on the s53 snare, back mirror-flat on "back" (134.80) */
export const oceanOn = (t: number) => !(t >= M.S53 && t < M.BACK);
/** wave amplitude field: gentle swell, flat after "back", then every wave rises at once from the centre out (s54) */
export function waveAmp(t: number, r: number) {
  if (t >= M.BACK && t < M.S54) return 0;
  if (t >= M.S54) { const front = (t - M.S54) * 140; return 0.9 * smooth(clamp((front - r) / 60 + 1)) * (r < front + 60 ? 1 : 0); }
  return 0.18;
}
/** gold floods in on "Sunday"; the eclipse dims the direct sun at totality; the city's lights come on in one wave */
export const gold = (t: number) => smooth(prog(t, M.SUNDAY - 0.1, M.S61 - 0.3));
export const cityWave = (t: number, x: number) => smooth(clamp((t - M.S61 - Math.abs(x) / 260) / 0.18));
