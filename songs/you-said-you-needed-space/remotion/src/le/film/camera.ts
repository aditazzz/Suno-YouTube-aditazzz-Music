// Her disk on screen + the projection shared by the planet shader (Layers.tsx PLANET_FRAG) and everything placed on or
// around her in JS (geo paths, orbits, sparks). Orthographic sphere: 2.5D, cheap, exact match between JS and GLSL.
import { Anchor, at } from './anchor';
import { Cam, Fmt, GeoPt, Path } from './types';
import { ASPECT } from './stars';
export const CAM_DEFAULT: Cam = { x: 0, y: 0, r: 0.62, lon: 15, lat: 8, roll: -12, sun: [0.85, 0.25, -0.46], par: [0, 0] };
export type CamKey = { at: Anchor; cam: Partial<Cam>; ease?: 'smooth' | 'linear' | 'hold' | 'out' | 'in' };
const D = Math.PI / 180;
const lerp = (a: number, b: number, u: number) => a + (b - a) * u;
const EASE = { smooth: (u: number) => u * u * (3 - 2 * u), linear: (u: number) => u, hold: () => 0, out: (u: number) => 1 - (1 - u) * (1 - u) * (1 - u), in: (u: number) => u * u * u };
export function lerpCam(a: Cam, b: Cam, u: number): Cam {
  return { x: lerp(a.x, b.x, u), y: lerp(a.y, b.y, u), r: Math.exp(lerp(Math.log(a.r), Math.log(b.r), u)), lon: lerp(a.lon, b.lon, u), lat: lerp(a.lat, b.lat, u), roll: lerp(a.roll, b.roll, u),
    sun: [lerp(a.sun[0], b.sun[0], u), lerp(a.sun[1], b.sun[1], u), lerp(a.sun[2], b.sun[2], u)], par: [lerp(a.par[0], b.par[0], u), lerp(a.par[1], b.par[1], u)] };
}
// camera keys: each key is the full camera from its time on (missing fields carry over from the previous key); between
// key i and i+1 the move eases with key i+1's ease (radius in log space, so zooms feel even). Her slow spin is added on top.
type K = { t: number; cam: Cam; ease: CamKey['ease'] };
let KEYS: K[] = [];
export const SPIN_DEG_S = 0.35;
export function setCamKeys(keys: CamKey[]) {
  const s = keys.map((k) => ({ t: at(k.at), k })).sort((a, b) => a.t - b.t);
  let cur = CAM_DEFAULT; KEYS = s.map(({ t, k }) => (cur = { ...cur, ...k.cam }, { t, cam: cur, ease: k.ease ?? 'smooth' }));
}
export function camAt(t: number): Cam {
  let c: Cam;
  if (!KEYS.length || t <= KEYS[0].t) c = KEYS[0]?.cam ?? CAM_DEFAULT;
  else {
    let i = 0; while (i + 1 < KEYS.length && KEYS[i + 1].t <= t) i++;
    if (i + 1 >= KEYS.length) c = KEYS[i].cam;
    else { const a = KEYS[i], b = KEYS[i + 1]; c = lerpCam(a.cam, b.cam, EASE[b.ease ?? 'smooth'](Math.min(1, (t - a.t) / Math.max(1e-3, b.t - a.t)))); }
  }
  return { ...c, lon: c.lon + SPIN_DEG_S * t };
}
// 9:16: the same film re-framed: x pulled in, the disk a bit smaller relative to the (narrow) width
export function camFor(fmt: Fmt, c: Cam): Cam {
  if (fmt === '169') return c;
  const k = ASPECT['916'] / ASPECT['169'];
  const side = Math.min(1, Math.abs(c.x) / 0.6); // off-centre in 16:9 (something beside her) -> she moves down in 9:16
  return { ...c, x: c.x * k * (1 - 0.6 * side), y: c.y * 0.8 - 0.5 * side, r: c.r * 0.62, par: [c.par[0] * k, c.par[1]] };
}
// ---- projection (keep identical to the GLSL) ----
export type Proj = { x: number; y: number; z: number; visible: boolean }; // z > 0: on her near side / in front of her
export function viewOfGeo(c: Cam, lat: number, lon: number): [number, number, number] {
  const la = lat * D, lo = (lon - c.lon) * D, cl = c.lat * D;
  const vx = Math.cos(la) * Math.sin(lo), vy = Math.sin(la), vz = Math.cos(la) * Math.cos(lo);
  return [vx, vy * Math.cos(cl) - vz * Math.sin(cl), vy * Math.sin(cl) + vz * Math.cos(cl)];
}
export function toScreen(c: Cam, v: [number, number, number]): Proj {
  const cr = Math.cos(c.roll * D), sr = Math.sin(c.roll * D);
  const x = cr * v[0] - sr * v[1], y = sr * v[0] + cr * v[1];
  const inDisk = x * x + y * y < 1;
  return { x: c.x + c.r * x, y: c.y + c.r * y, z: v[2], visible: v[2] >= 0 || !inDisk };
}
export function projGeo(c: Cam, p: GeoPt, lift = 0): Proj { const v = viewOfGeo(c, p[0], p[1]); const s = 1 + lift; return toScreen(c, [v[0] * s, v[1] * s, v[2] * s]); }
// an orbit: a circle of radius alt (her radii) tilted by incl about the screen x axis, then rolled by node; angle a (deg)
export function projOrbit(c: Cam, alt: number, incl: number, node: number, a: number): Proj {
  const ca = Math.cos(a * D), sa = Math.sin(a * D), ci = Math.cos(incl * D), si = Math.sin(incl * D), cn = Math.cos(node * D), sn = Math.sin(node * D);
  let x = ca * alt, y = 0, z = sa * alt; const y2 = y * ci - z * si, z2 = y * si + z * ci; y = y2; z = z2;
  const x3 = cn * x - sn * y, y3 = sn * x + cn * y;
  const inDisk = x3 * x3 + y3 * y3 < 1;
  return { x: c.x + c.r * x3, y: c.y + c.r * y3, z, visible: z >= 0 || !inDisk };
}
// a point at fraction s (0..1) along a path
export function pathAt(c: Cam, p: Path, s: number): Proj {
  s = Math.max(0, Math.min(1, s));
  if (p.space === 'orbit') return projOrbit(c, p.alt, p.incl, p.node, p.a0 + (p.a1 - p.a0) * s);
  const n = p.pts.length;
  if (n === 1) return p.space === 'screen' ? { x: p.pts[0][0], y: p.pts[0][1], z: 1, visible: true } : p.space === 'rel' ? { x: c.x + c.r * p.pts[0][0], y: c.y + c.r * p.pts[0][1], z: 1, visible: true } : projGeo(c, p.pts[0] as GeoPt, p.lift);
  const f = s * (n - 1), i = Math.min(n - 2, Math.floor(f)), u = f - i;
  if (p.space === 'screen') { const a = p.pts[i], b = p.pts[i + 1]; return { x: lerp(a[0], b[0], u), y: lerp(a[1], b[1], u), z: 1, visible: true }; }
  if (p.space === 'rel') { const a = p.pts[i], b = p.pts[i + 1]; return { x: c.x + c.r * lerp(a[0], b[0], u), y: c.y + c.r * lerp(a[1], b[1], u), z: 1, visible: true }; }
  const a = p.pts[i] as GeoPt, b = p.pts[i + 1] as GeoPt;
  return projGeo(c, [lerp(a[0], b[0], u), lerp(a[1], b[1], u)], p.lift ?? 0);
}
export const screenAspect = (fmt: Fmt) => ASPECT[fmt];
