export type RGB = [number, number, number];
export type Ctx = CanvasRenderingContext2D;

export const clamp = (x: number, a = 0, b = 1) => (x < a ? a : x > b ? b : x);
export const lerp = (a: number, b: number, k: number) => a + (b - a) * k;
export const inv = (a: number, b: number, x: number) => clamp((x - a) / (b - a));
export const smooth = (x: number) => {
  x = clamp(x);
  return x * x * (3 - 2 * x);
};
export const sstep = (a: number, b: number, x: number) => smooth((x - a) / (b - a));
export const easeOut = (x: number, p = 3) => 1 - Math.pow(1 - clamp(x), p);
export const easeIn = (x: number, p = 2) => Math.pow(clamp(x), p);
export const easeInOut = (x: number) => {
  x = clamp(x);
  return x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2;
};
// 0 before t0, rises over `att` seconds, then decays exponentially with time constant `dec`
export const hit = (t: number, t0: number, att = 0.03, dec = 0.25) =>
  t < t0 ? 0 : t < t0 + att ? (t - t0) / att : Math.exp(-(t - t0 - att) / dec);
// trapezoid: fade in over `a`, hold until t1, fade out over `r`
export const env = (t: number, t0: number, t1: number, a = 0.2, r = 0.2) =>
  t < t0 || t > t1 + r ? 0 : Math.min(a > 0 ? clamp((t - t0) / a) : 1, t <= t1 ? 1 : r > 0 ? 1 - (t - t1) / r : 0);
// a damped spring kick: 0 at t0, wobbles and settles to 0
export const wobble = (t: number, t0: number, freq = 3.2, damp = 6) =>
  t < t0 ? 0 : Math.exp(-damp * (t - t0)) * Math.sin(2 * Math.PI * freq * (t - t0));
export const TAU = Math.PI * 2;

export function rng(seed: number) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
export const hash = (n: number) => {
  const s = Math.sin(n * 127.1 + 311.7) * 43758.5453123;
  return s - Math.floor(s);
};
export const hash2 = (x: number, y: number) => hash(x * 157.31 + y * 311.7 + 0.5);
export function noise1(x: number, seed = 0) {
  const i = Math.floor(x), f = x - i, u = f * f * (3 - 2 * f);
  return lerp(hash(i + seed * 101.3), hash(i + 1 + seed * 101.3), u);
}
export function noise2(x: number, y: number) {
  const ix = Math.floor(x), iy = Math.floor(y), fx = x - ix, fy = y - iy;
  const ux = fx * fx * (3 - 2 * fx), uy = fy * fy * (3 - 2 * fy);
  const a = hash2(ix, iy), b = hash2(ix + 1, iy), c = hash2(ix, iy + 1), d = hash2(ix + 1, iy + 1);
  return lerp(lerp(a, b, ux), lerp(c, d, ux), uy);
}
export function fbm(x: number, y: number, oct = 4) {
  let s = 0, a = 0.5, f = 1, n = 0;
  for (let i = 0; i < oct; i++) {
    s += a * noise2(x * f, y * f);
    n += a;
    a *= 0.5;
    f *= 2.03;
  }
  return s / n;
}

export const mix = (a: RGB, b: RGB, k: number): RGB => [lerp(a[0], b[0], k), lerp(a[1], b[1], k), lerp(a[2], b[2], k)];
export const scale = (a: RGB, k: number): RGB => [a[0] * k, a[1] * k, a[2] * k];
export const rgba = (c: RGB, a = 1) =>
  `rgba(${Math.round(clamp(c[0], 0, 255))},${Math.round(clamp(c[1], 0, 255))},${Math.round(clamp(c[2], 0, 255))},${clamp(a)})`;
export function hsl(h: number, s: number, l: number): RGB {
  h = ((h % 360) + 360) % 360;
  const c = (1 - Math.abs(2 * l - 1)) * s, x = c * (1 - Math.abs(((h / 60) % 2) - 1)), m = l - c / 2;
  const [r, g, b] = h < 60 ? [c, x, 0] : h < 120 ? [x, c, 0] : h < 180 ? [0, c, x] : h < 240 ? [0, x, c] : h < 300 ? [x, 0, c] : [c, 0, x];
  return [(r + m) * 255, (g + m) * 255, (b + m) * 255];
}
export const grey = (c: RGB, k: number): RGB => {
  const l = c[0] * 0.3 + c[1] * 0.59 + c[2] * 0.11;
  return mix(c, [l, l, l], k);
};

export const PAL = {
  amber: [255, 172, 58] as RGB,
  amberHot: [255, 222, 150] as RGB,
  amberDeep: [205, 98, 18] as RGB,
  teal: [104, 232, 218] as RGB,
  tealWhite: [222, 255, 250] as RGB,
  tealDeep: [18, 120, 124] as RGB,
  mint: [126, 255, 210] as RGB,
  red: [255, 46, 34] as RGB,
  redHot: [255, 150, 90] as RGB,
  ember: [120, 14, 8] as RGB,
  skyTop: [3, 4, 12] as RGB,
  skyMid: [8, 12, 30] as RGB,
  skyLow: [22, 30, 58] as RGB,
  stone: [11, 11, 14] as RGB,
  fog: [128, 132, 142] as RGB,
  moon: [238, 236, 222] as RGB,
  paper: [226, 222, 210] as RGB,
  dawnLow: [255, 170, 110] as RGB,
  dawnMid: [255, 120, 140] as RGB,
  dawnTop: [70, 90, 170] as RGB,
};
// candy: the colours that only exist behind the wall
export const candy = (i: number, shift = 0): RGB => hsl(320 - i * 23 + shift, 0.95, 0.62);

const cache = new Map<string, HTMLCanvasElement>();
export function surface(key: string, w: number, h: number): HTMLCanvasElement {
  let c = cache.get(key);
  if (!c) {
    c = document.createElement('canvas');
    cache.set(key, c);
  }
  if (c.width !== w || c.height !== h) {
    c.width = w;
    c.height = h;
  }
  return c;
}
export function once(key: string, w: number, h: number, paint: (ctx: Ctx, w: number, h: number) => void) {
  const k = `once:${key}:${w}x${h}`;
  let c = cache.get(k);
  if (!c) {
    c = document.createElement('canvas');
    c.width = w;
    c.height = h;
    paint(c.getContext('2d')!, w, h);
    cache.set(k, c);
  }
  return c;
}

export function glowDot(ctx: Ctx, x: number, y: number, r: number, c: RGB, a = 1) {
  if (a <= 0.002 || r <= 0) return;
  const g = ctx.createRadialGradient(x, y, 0, x, y, r);
  g.addColorStop(0, rgba(c, a));
  g.addColorStop(0.25, rgba(c, a * 0.45));
  g.addColorStop(0.6, rgba(c, a * 0.12));
  g.addColorStop(1, rgba(c, 0));
  ctx.fillStyle = g;
  ctx.fillRect(x - r, y - r, r * 2, r * 2);
}
export function disc(ctx: Ctx, x: number, y: number, r: number, c: RGB, a = 1) {
  if (a <= 0.002 || r <= 0) return;
  ctx.fillStyle = rgba(c, a);
  ctx.beginPath();
  ctx.arc(x, y, r, 0, TAU);
  ctx.fill();
}
export function roundRect(ctx: Ctx, x: number, y: number, w: number, h: number, r: number) {
  r = Math.min(r, Math.abs(w) / 2, Math.abs(h) / 2);
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
}
export function heartPath(ctx: Ctx, x: number, y: number, s: number) {
  ctx.beginPath();
  ctx.moveTo(x, y + s * 0.35);
  ctx.bezierCurveTo(x - s * 1.1, y - s * 0.35, x - s * 0.45, y - s * 1.05, x, y - s * 0.45);
  ctx.bezierCurveTo(x + s * 0.45, y - s * 1.05, x + s * 1.1, y - s * 0.35, x, y + s * 0.35);
  ctx.closePath();
}
