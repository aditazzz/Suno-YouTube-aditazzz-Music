// The city's world: a deterministic 2.5D layout (boxes in a pinhole projection), built once at import.
// The front and back rows are the approved frame 2's flatCity(22) from design/frames.html, same rng and call order, placed
// in depth so that the identity camera (x 960, y 540, dolly 0, yaw 0) reproduces approved frame 2 exactly, and any camera
// move gives true parallax. Rows outside 0..1920 extend the street for the trucks, the orbit and the pull-back.
// Units: world px. x right, y down (ground y = 810), z into the screen (front row z = 0).

export const F = 1600;            // focal length (px): a plane at z = 0 is 1:1 with the identity camera
export const GROUND = 810;
export const PIVOT = { x: 960, z: 260 }; // the turntable's axis (s40 / s44 orbits)

// rng from design/frames.html (mulberry32 variant), so the approved layout comes out identical
export function rng(seed: number) {
  return function () {
    seed |= 0; seed = (seed + 0x6d2b79f5) | 0; let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
export const hash = (a: number, b = 0) => { const r = rng(a * 7919 + b * 104729 + 13); r(); return r(); };

export type Win = { x: number; y: number; lit0: boolean; cool: boolean; guy0: boolean; r1: number; r2: number; r3: number; col: number; row: number };
export type Bld = {
  id: number; layer: 'far' | 'back' | 'front' | 'rear'; x: number; w: number; h: number; z: number; d: number; base: number;
  wins: Win[]; order: number; late?: boolean;
};

const unS = (z: number) => (F + z) / F; // inverse of the identity scale at depth z
/** a screen point of the approved frame at depth z -> world (identity camera) */
export const unproj = (xs: number, ys: number, z: number) => ({ x: 960 + (xs - 960) * unS(z), y: 540 + (ys - 540) * unS(z), z });

const windowsFor = (b: { x: number; w: number; h: number }, base: number, r: () => number, people: boolean): Win[] => {
  const out: Win[] = [];
  const cols = Math.floor((b.w - 24) / 30), rows = Math.floor((b.h - 40) / 40);
  for (let j = 0; j < rows; j++) for (let i = 0; i < cols; i++) {
    const lit = r() < 0.3;
    const cool = lit ? !(r() < 0.72) : false;
    const guy = lit && people ? r() < 0.45 : false;
    out.push({ x: b.x + 16 + i * 30, y: base - b.h + 22 + j * 40, lit0: lit, cool, guy0: guy, r1: 0, r2: 0, r3: 0, col: i, row: j });
  }
  return out;
};

function build(): Bld[] {
  const W = 1920;
  const r = rng(22);
  const out: Bld[] = [];
  // back layer (approved: x from -20, w 70..160, h 180..440, flat #152034), placed at z = 120 (first depth)
  const BZ = 120, s = unS(BZ);
  let x = -20;
  while (x < W) {
    const w = 70 + r() * 90, h = 180 + r() * 260;
    const p = unproj(x, GROUND - h, BZ);
    out.push({ id: out.length, layer: 'back', x: p.x, w: w * s, h: h * s, z: BZ, d: 60, base: 540 + (GROUND - 540) * s, wins: [], order: 0 });
    x += w + 6;
  }
  // front layer (approved: x from -10, w 110..230, h 220..520) at z = 0, windows in the approved order
  x = -10;
  const fronts: { x: number; w: number; h: number }[] = [];
  while (x < W) { const w = 110 + r() * 120, h = 220 + r() * 300; fronts.push({ x, w, h }); x += w + 14; }
  for (const f of fronts) out.push({ id: out.length, layer: 'front', ...f, z: 0, d: 90, base: GROUND, wins: windowsFor(f, GROUND, r, true), order: 0 });
  // extension left and right (new seed; same rules)
  const e = rng(511);
  const extend = (dir: -1 | 1, from: number, to: number, layer: 'front' | 'back') => {
    let xx = from;
    while (dir < 0 ? xx > to : xx < to) {
      const front = layer === 'front';
      const w = front ? 110 + e() * 120 : 70 + e() * 90, h = front ? 220 + e() * 300 : 180 + e() * 260;
      const bx = dir < 0 ? xx - w : xx;
      if (front) out.push({ id: out.length, layer, x: bx, w, h, z: 0, d: 90, base: GROUND, wins: windowsFor({ x: bx, w, h }, GROUND, e, true), order: 0 });
      else out.push({ id: out.length, layer, x: 960 + (bx - 960) * s, w: w * s, h: h * s, z: BZ, d: 60, base: 540 + (GROUND - 540) * s, wins: [], order: 0 });
      xx += dir * (w + (front ? 14 : 6));
    }
  };
  extend(-1, -10 - 14, -2600, 'front');
  extend(1, x, 4500, 'front');
  extend(-1, -20 - 6, -2600, 'back');
  // (the back layer's last x from the loop above)
  { let bx = -20; const r2 = rng(22); while (bx < W) { const w = 70 + r2() * 90; r2(); bx += w + 6; } extend(1, bx, 4500, 'back'); }
  // far layer (new, z 600, dark, low: hidden behind the back row at the identity framing, shows in the wide shots)
  const fr = rng(907);
  for (let fx = -3200; fx < 5200;) {
    const w = 120 + fr() * 160, h = 260 + fr() * 300;
    out.push({ id: out.length, layer: 'far', x: fx, w, h, z: 600, d: 80, base: GROUND + 160, wins: [], order: 0 });
    fx += w + 10 + fr() * 30;
  }
  // rear row (s42 "Bigger, louder": the city doubles: a taller skyline rises behind, z 1000)
  const rr = rng(1301);
  for (let fx = -3000; fx < 5000;) {
    const w = 170 + rr() * 200, h = 620 + rr() * 640;
    const b: Bld = { id: out.length, layer: 'rear', x: fx, w, h, z: 1000, d: 120, base: GROUND + 260, wins: [], order: 0 };
    b.wins = windowsFor({ x: fx, w, h }, b.base, rr, false).map((wn) => ({ ...wn, lit0: hash(wn.x, wn.y) < 0.22 }));
    out.push(b);
    fx += w + 40 + rr() * 80;
  }
  // per-window extras (s32 cascade, s44 cycling), deterministic
  for (const b of out) for (const wn of b.wins) { wn.r1 = hash(wn.x * 3 + 1, wn.y); wn.r2 = hash(wn.x + 7, wn.y * 5); wn.r3 = hash(wn.y + 11, wn.x * 2); }
  // rise order (s28: one front building per 16th, nearest the dot first)
  const fr2 = out.filter((b) => b.layer === 'front' && b.x + b.w > -40 && b.x < 1960).sort((a, b) => Math.abs(a.x + a.w / 2 - 960) - Math.abs(b.x + b.w / 2 - 960));
  fr2.forEach((b, i) => (b.order = i));
  for (const b of out) if (b.layer !== 'front' || b.x + b.w <= -40 || b.x >= 1960) {
    // everything else rises with its nearest on-screen front building, a 16th later
    const c = b.x + b.w / 2; let best = fr2[0];
    for (const f of fr2) if (Math.abs(f.x + f.w / 2 - Math.max(-10, Math.min(1930, c))) < Math.abs(best.x + best.w / 2 - Math.max(-10, Math.min(1930, c)))) best = f;
    b.order = best.order + (b.layer === 'back' ? 1 : b.layer === 'far' ? 2 : 3);
  }
  return out;
}
export const BLDS: Bld[] = build();
export const FRONT = BLDS.filter((b) => b.layer === 'front');
// the tallest on-screen front building: its crown lights on 'fire' (s39)
export const CROWN = FRONT.filter((b) => b.x > 200 && b.x < 1500).reduce((a, b) => (b.h > a.h ? b : a));
// s41: the late grid dot from CH1 is now a late building
export const LATE = FRONT.filter((b) => b.x > 1300 && b.x < 1900)[0];
// s32 / s33: the building and window row the camera pushes into (left of the car, a row near eye level, 3+ columns)
export const TARGET = (() => {
  const cands = FRONT.filter((b) => b.x > 380 && b.x + b.w < 980 && Math.floor((b.w - 24) / 30) >= 3 && b.h > 330);
  const b = cands.sort((a, c) => Math.abs(a.x + a.w / 2 - 700) - Math.abs(c.x + c.w / 2 - 700))[0] ?? FRONT[6];
  const row = Math.min(Math.floor((b.h - 40) / 40) - 1, Math.max(0, Math.round((560 - (GROUND - b.h + 22)) / 40)));
  const cols = Math.floor((b.w - 24) / 30);
  const c0 = Math.max(0, Math.floor((cols - 3) / 2));
  const wins = [0, 1, 2].map((k) => b.wins.find((w) => w.row === row && w.col === c0 + k)!);
  return { b, row, c0, wins, cx: wins[1].x + 9, cy: wins[1].y + 12 };
})();
for (const w of TARGET.wins) { w.lit0 = true; w.cool = false; w.guy0 = true; }
// s45: the lit window the camera pushes toward into the match-cut (right of the car's roof line, high up)
export const PUSHWIN = (() => {
  const b = FRONT.filter((x) => x.x > 1530 && x.x < 1800)[0] ?? FRONT[FRONT.length - 1];
  const w = b.wins.find((x) => x.row === 2 && x.col === 1) ?? b.wins[0];
  w.lit0 = true; w.cool = false; w.guy0 = true;
  return { b, w, cx: w.x + 9, cy: w.y + 12 };
})();

// the s43 bass tower (CH1's tower, now the city's tallest): behind the front row at the centre
export const TOWER = { x: 960 - 95, w: 190, z: 420, d: 120, base: GROUND + 60, floors: 34, floorH: 44 };

// rain: a plane in front of the buildings, left of the world line x = 960 (the hard edge), approved density
export const RAIN_Z = -90, RAIN_EDGE = 960;
export const DROPS = (() => {
  const r = rng(4242), out: { x: number; o: number; l: number; v: number }[] = [];
  for (let i = 0; i < 1500; i++) out.push({ x: -2400 + r() * (RAIN_EDGE + 60 + 2400), o: r(), l: 18 + r() * 16, v: 0.9 + r() * 0.25 });
  return out;
})();
export const RAIN_TOP = -260, RAIN_BOT = GROUND + 130, RAIN_SPAN = RAIN_BOT - RAIN_TOP;

// street furniture (approved positions, at z = -20 on the kerb)
export const LIGHT_Z = -20;
export const LIGHTS = [unproj(420, 662, LIGHT_Z), unproj(1520, 662, LIGHT_Z)]; // [red, green] in frame 2
export const LAMP = unproj(1716, 640, LIGHT_Z);
// the car: approved gt3(1010, 850, 1.12) -> depth where the identity scale is 1.12
export const CAR_Z = F / 1.12 - F;
export const CAR = unproj(1010, 850, CAR_Z);
export const PIGEON_Z = -40;
export const FLOCK = unproj(1180, 190, PIGEON_Z);
export const UMBRELLA = { x: RAIN_EDGE, z: -60 };
// floaters (s37: tiny guys float out of their windows still typing): lit guy windows, spread across the frame
export const FLOATERS = FRONT.flatMap((b) => b.wins.filter((w) => w.guy0 && w.x > 60 && w.x < 1860).map((w) => ({ b, w }))).filter((_, i) => i % 3 === 0).slice(0, 22);

/** the layout for the 3D worker's match-cut (written to build/rc_city/city_layout.json by tools) */
export const layoutJSON = () => ({
  units: 'world px; x right, y down, ground y 810, z into screen; identity camera = x 960 y 540 dolly 0 yaw 0, F 1600',
  F, GROUND, PIVOT, TOWER, CAR: { ...CAR }, buildings: BLDS.map((b) => ({ layer: b.layer, x: b.x, w: b.w, h: b.h, z: b.z, d: b.d, base: b.base,
    lit: b.wins.filter((w) => w.lit0).map((w) => [w.x, w.y]) })),
});
