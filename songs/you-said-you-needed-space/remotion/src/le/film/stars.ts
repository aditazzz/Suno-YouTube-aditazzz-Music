// The star ARRANGEMENT system: N "cast" stars that live in the night sky and morph between target point sets (text, SVG
// paths, image masks, boxes, explicit points, or any function of time), with per-star easing, stragglers and curved
// paths. Pure function of time: the state at t is rebuilt from the key list (memoised per key start), never accumulated.
// A faint static "dust" sky sits behind (Layers.tsx) so the sky never empties when the cast is busy.
import { Box, Fmt, StarKey, StarSet } from './types';
import { at } from './anchor';

export const N_CAST = 2600;
export const N_DUST = 7000;
export const ASPECT: Record<Fmt, number> = { '169': 2560 / 1440, '916': 1080 / 1920 };

export function rng(seed: number) { let a = seed >>> 0; return () => { a = (a + 0x6d2b79f5) >>> 0; let t = a; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
const clamp01 = (x: number) => (x < 0 ? 0 : x > 1 ? 1 : x);
export const easeInOut = (x: number) => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2);

// ---- per-star constants (same for every format) ----
export type StarAttr = { size: Float32Array; bright: Float32Array; color: Float32Array; depth: Float32Array; r1: Float32Array; r2: Float32Array; r3: Float32Array };
let ATTR: StarAttr | null = null;
export function starAttr(): StarAttr {
  if (ATTR) return ATTR;
  const R = rng(1108), n = N_CAST;
  const a: StarAttr = { size: new Float32Array(n), bright: new Float32Array(n), color: new Float32Array(n * 3), depth: new Float32Array(n), r1: new Float32Array(n), r2: new Float32Array(n), r3: new Float32Array(n) };
  for (let i = 0; i < n; i++) {
    const m = Math.pow(R(), 3.2);                 // a power law: few bright stars, many faint
    a.bright[i] = 0.25 + 1.6 * m; a.size[i] = 2.2 + 6.5 * m;
    const tmp = R();                              // temperature: blue-white .. warm
    a.color.set(tmp < 0.55 ? [0.75, 0.88, 1.0] : tmp < 0.85 ? [1.0, 0.97, 0.92] : [1.0, 0.82, 0.62], i * 3);
    a.depth[i] = 0.25 + 0.75 * R(); a.r1[i] = R(); a.r2[i] = R(); a.r3[i] = R();
  }
  return (ATTR = a);
}

// ---- home (the sky) per format: uniform + a soft diagonal Milky Way band ----
const HOME: Partial<Record<Fmt, Float32Array>> = {};
export function home(fmt: Fmt): Float32Array {
  if (HOME[fmt]) return HOME[fmt]!;
  const A = ASPECT[fmt], R = rng(fmt === '169' ? 7 : 11), p = new Float32Array(N_CAST * 2);
  for (let i = 0; i < N_CAST; i++) {
    let x: number, y: number;
    if (R() < 0.35) { // the band
      const s = (R() * 2 - 1) * 1.25, off = (R() + R() + R() - 1.5) * 0.22;
      x = s * A * 0.95 + off * 0.5; y = s * 0.55 + off;
    } else { x = (R() * 2 - 1) * A * 1.06; y = (R() * 2 - 1) * 1.06; }
    p[i * 2] = x; p[i * 2 + 1] = y;
  }
  return (HOME[fmt] = p);
}

// ---- boxes fit the format (designed in 16:9 units; shrunk and re-centred for 9:16) ----
export function fitBox(b: Box, fmt: Fmt): Box {
  if (fmt === '169') return b;
  // 9:16: a shape that sat beside her in 16:9 moves to the upper band (she moves down, camera.ts camFor), inside the
  // 9:16 safe zone (top 13% and bottom 30% kept clear: y in [-0.4, 0.74]); everything shrinks to fit the narrow width.
  const A = ASPECT['916'], k = A / ASPECT['169'], side = Math.min(1, Math.abs(b.cx) / 0.4);
  let { w, h } = b; const cx = b.cx * k * (1 - 0.7 * side), cy = b.cy * 0.75 * (1 - side) + side * 0.36;
  const s = Math.min(1, (A * 1.7) / w, side > 0.5 ? 0.66 / h : 9); w *= s; h *= s;
  return { cx, cy, w, h };
}

// ---- rasterised masks (text, SVG, image) -> sample points in the unit square ----
const MASKS = new Map<string, Float32Array>(); // unit-square points (x right, y up), N_CAST of them
export const IMAGE_MASKS = new Map<string, ImageData>(); // filled by useImageMasks (Film.tsx) before the first frame
function rasterPoints(key: string, aspectWH: number, draw: (g: CanvasRenderingContext2D, W: number, H: number) => void, edge = false): Float32Array {
  const hit = MASKS.get(key); if (hit) return hit;
  const W = 640, H = Math.max(8, Math.round(W / aspectWH));
  const c = document.createElement('canvas'); c.width = W; c.height = H;
  const g = c.getContext('2d')!; g.clearRect(0, 0, W, H); g.fillStyle = '#fff'; g.strokeStyle = '#fff';
  draw(g, W, H);
  const d = g.getImageData(0, 0, W, H).data, on: number[] = [];
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
    const v = d[(y * W + x) * 4 + 3];
    if (v < 128) continue;
    if (edge) { // keep only the outline: a pixel with an empty neighbour
      const n = (xx: number, yy: number) => (xx < 0 || yy < 0 || xx >= W || yy >= H ? 0 : d[(yy * W + xx) * 4 + 3]);
      if (n(x - 2, y) >= 128 && n(x + 2, y) >= 128 && n(x, y - 2) >= 128 && n(x, y + 2) >= 128) continue;
    }
    on.push(x, y);
  }
  // seed from the key only (earth_first_cut, Nov 8; found by earth_sec_v2): it used to include on.length, the rasterised pixel count, and two render
  // tabs can differ by one antialiased pixel -> a different seed -> the same shape laid out differently per tab -> a held star shape boils.
  let seed = 2166136261; for (let i = 0; i < key.length; i++) seed = Math.imul(seed ^ key.charCodeAt(i), 16777619);
  const R = rng(seed), out = new Float32Array(N_CAST * 2), m = on.length / 2;
  for (let i = 0; i < N_CAST; i++) {
    const j = m ? Math.floor(R() * m) : 0;
    out[i * 2] = m ? (on[j * 2] + R()) / W : 0.5; out[i * 2 + 1] = m ? 1 - (on[j * 2 + 1] + R()) / H : 0.5;
  }
  MASKS.set(key, out); return out;
}

// ---- assignment: moving stars and target points both in Morton order, so neighbours stay neighbours ----
function morton(x: number, y: number) { // x,y in [0,1]
  let xi = Math.max(0, Math.min(1023, Math.floor(x * 1024))), yi = Math.max(0, Math.min(1023, Math.floor(y * 1024))), k = 0;
  for (let b = 0; b < 10; b++) k |= (((xi >> b) & 1) << (2 * b)) | (((yi >> b) & 1) << (2 * b + 1));
  return k;
}
const ORDER = new Map<string, Int32Array>();
function orderOf(key: string, pts: Float32Array, idx: number[], bounds: [number, number, number, number]) {
  const [x0, y0, x1, y1] = bounds;
  const ks = idx.map((i) => morton((pts[i * 2] - x0) / (x1 - x0 || 1), (pts[i * 2 + 1] - y0) / (y1 - y0 || 1)));
  const o = idx.map((_, j) => j).sort((a, b) => ks[a] - ks[b]);
  return Int32Array.from(o.map((j) => idx[j]));
}
function boundsOf(p: Float32Array, idx: number[]): [number, number, number, number] {
  let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
  for (const i of idx) { x0 = Math.min(x0, p[i * 2]); x1 = Math.max(x1, p[i * 2]); y0 = Math.min(y0, p[i * 2 + 1]); y1 = Math.max(y1, p[i * 2 + 1]); }
  return [x0, y0, x1, y1];
}
// map unit-square points to a box, assigning them to the moving stars (keep = fraction that stays in the sky)
function shape(fmt: Fmt, key: string, unit: Float32Array, box: Box, keep = 0.25): Float32Array {
  const ck = `${fmt}|${key}|${keep}|${box.cx},${box.cy},${box.w},${box.h}`;
  const hit = SETS.get(ck); if (hit) return hit;
  const H = home(fmt), A = starAttr(), b = fitBox(box, fmt), out = Float32Array.from(H);
  const moving: number[] = []; for (let i = 0; i < N_CAST; i++) if (A.r3[i] >= keep) moving.push(i);
  const all = Array.from({ length: N_CAST }, (_, i) => i).slice(0, moving.length);
  const so = ORDER.get(`${fmt}|home|${keep}`) ?? orderOf('', H, moving, boundsOf(H, moving)); ORDER.set(`${fmt}|home|${keep}`, so);
  const to = orderOf(key, unit, all, [0, 0, 1, 1]);
  for (let j = 0; j < so.length; j++) {
    const s = so[j], u = to[j];
    out[s * 2] = b.cx + (unit[u * 2] - 0.5) * b.w; out[s * 2 + 1] = b.cy + (unit[u * 2 + 1] - 0.5) * b.h;
  }
  SETS.set(ck, out); return out;
}
const SETS = new Map<string, Float32Array>();

export function resolveSet(set: StarSet, fmt: Fmt, t: number): Float32Array {
  const H = home(fmt);
  switch (set.kind) {
    case 'sky': return H;
    case 'away': {
      const k = `${fmt}|away|${set.cx},${set.cy},${set.k}`; const hit = SETS.get(k); if (hit) return hit;
      const o = new Float32Array(H.length);
      for (let i = 0; i < N_CAST; i++) { const dx = H[i * 2] - set.cx, dy = H[i * 2 + 1] - set.cy; o[i * 2] = set.cx + dx * set.k; o[i * 2 + 1] = set.cy + dy * set.k; }
      SETS.set(k, o); return o;
    }
    case 'room': {
      const k = `${fmt}|room|${set.cx},${set.cy},${set.R}`; const hit = SETS.get(k); if (hit) return hit;
      const o = new Float32Array(H.length), R3 = set.R * set.R * set.R;
      for (let i = 0; i < N_CAST; i++) { const dx = H[i * 2] - set.cx, dy = H[i * 2 + 1] - set.cy, r = Math.hypot(dx, dy) || 1e-6, r2 = Math.cbrt(r * r * r + R3); o[i * 2] = set.cx + dx / r * r2; o[i * 2 + 1] = set.cy + dy / r * r2; }
      SETS.set(k, o); return o;
    }
    case 'union': {
      const A = starAttr(), parts = set.parts.map((p) => resolveSet(p.set, fmt, t)), tot = set.parts.reduce((a, p) => a + p.w, 0);
      const o = Float32Array.from(H), keep = set.keep ?? 0.25;
      for (let i = 0; i < N_CAST; i++) {
        if (A.r3[i] < keep) continue;
        let u = A.r2[i] * tot, j = 0; while (j < parts.length - 1 && u > set.parts[j].w) { u -= set.parts[j].w; j++; }
        o[i * 2] = parts[j][i * 2]; o[i * 2 + 1] = parts[j][i * 2 + 1];
      }
      return o;
    }
    case 'side': {
      const k = `${fmt}|side|${set.side},${set.cram}`; const hit = SETS.get(k); if (hit) return hit;
      const A = ASPECT[fmt], o = new Float32Array(H.length);
      for (let i = 0; i < N_CAST; i++) { const u = (H[i * 2] / (A * 1.06) + 1) / 2; const x = set.side > 0 ? A * (1.02 - set.cram * 2 * (1 - u)) : -A * (1.02 - set.cram * 2 * u); o[i * 2] = x; o[i * 2 + 1] = H[i * 2 + 1]; }
      SETS.set(k, o); return o;
    }
    case 'text': {
      const font = set.font ?? '900 300px "Helvetica Neue", Helvetica, Arial, sans-serif';
      const unit = rasterPoints(`text|${set.text}|${font}|${set.box.w / set.box.h}`, set.box.w / set.box.h, (g, W, H2) => {
        g.font = font; g.textAlign = 'center'; g.textBaseline = 'middle';
        const lines = set.text.split('\n'), m = Math.max(...lines.map((l) => g.measureText(l).width));
        const s = Math.min((W * 0.96) / m, (H2 * 0.96) / (lines.length * 300 * 1.05));
        g.font = font.replace(/(\d+)px/, `${Math.floor(300 * s)}px`);
        lines.forEach((l, li) => g.fillText(l, W / 2, H2 / 2 + (li - (lines.length - 1) / 2) * 300 * s * 1.05));
      });
      return shape(fmt, `text|${set.text}`, unit, set.box, set.keep);
    }
    case 'svg': {
      const unit = rasterPoints(`svg|${set.d}|${set.stroke ?? 0}`, set.box.w / set.box.h, (g, W, H2) => {
        g.scale(W / set.view[0], H2 / set.view[1]); const p = new Path2D(set.d);
        if (set.stroke) { g.lineWidth = set.stroke; g.lineCap = 'round'; g.lineJoin = 'round'; g.stroke(p); } else g.fill(p);
      });
      return shape(fmt, `svg|${set.d}`, unit, set.box, set.keep);
    }
    case 'image': {
      const img = IMAGE_MASKS.get(set.src); if (!img) return H;
      const unit = rasterPoints(`img|${set.src}|${set.threshold ?? 0.5}`, img.width / img.height, (g, W, H2) => {
        const c = document.createElement('canvas'); c.width = img.width; c.height = img.height; c.getContext('2d')!.putImageData(img, 0, 0);
        g.drawImage(c, 0, 0, W, H2);
        const d = g.getImageData(0, 0, W, H2); const th = (set.threshold ?? 0.5) * 255;
        for (let i = 0; i < d.data.length; i += 4) { const l = (d.data[i] + d.data[i + 1] + d.data[i + 2]) / 3; d.data[i + 3] = l > th ? 255 : 0; }
        g.putImageData(d, 0, 0);
      });
      return shape(fmt, `img|${set.src}`, unit, set.box, set.keep);
    }
    case 'rects': {
      const box = set.box ?? { cx: 0, cy: 0, w: 2, h: 2 };
      const unit = rasterPoints(`rects|${JSON.stringify(set.rects)}|${set.outline}`, box.w / box.h, (g, W, H2) => {
        for (const r of set.rects) { const x = (r.cx - r.w / 2) * W, y = (1 - r.cy - r.h / 2) * H2; if (set.outline) { g.lineWidth = 3; g.strokeRect(x, y, r.w * W, r.h * H2); } else g.fillRect(x, y, r.w * W, r.h * H2); }
      });
      return shape(fmt, `rects|${JSON.stringify(set.rects)}`, unit, box, set.keep);
    }
    case 'points': {
      const k = JSON.stringify(set.pts); const R = rng(k.length);
      const unit = new Float32Array(N_CAST * 2); let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
      for (const [x, y] of set.pts) { x0 = Math.min(x0, x); x1 = Math.max(x1, x); y0 = Math.min(y0, y); y1 = Math.max(y1, y); }
      for (let i = 0; i < N_CAST; i++) { const p = set.pts[Math.floor(R() * set.pts.length)]; unit[i * 2] = (p[0] - x0) / (x1 - x0 || 1); unit[i * 2 + 1] = (p[1] - y0) / (y1 - y0 || 1); }
      return shape(fmt, `pts|${k}`, unit, { cx: (x0 + x1) / 2, cy: (y0 + y1) / 2, w: x1 - x0 || 0.01, h: y1 - y0 || 0.01 }, set.keep);
    }
    case 'fn': {
      const o = new Float32Array(H.length);
      for (let i = 0; i < N_CAST; i++) { const [x, y] = set.fn(i, t, [H[i * 2], H[i * 2 + 1]], N_CAST, fmt); o[i * 2] = x; o[i * 2 + 1] = y; }
      return o;
    }
  }
}
const isFront = (k: StarKey) => k.front ?? (k.set.kind === 'fn' ? !!k.set.front : !['sky', 'away', 'side', 'room'].includes(k.set.kind));

// ---- the timeline ----
export type StarState = { pos: Float32Array; front: Float32Array; motion: Float32Array };
type K = StarKey & { t0: number };
let KEYS: K[] = [];
const START = new Map<string, { pos: Float32Array; front: Float32Array }>();
export function setStarKeys(keys: StarKey[]) { KEYS = keys.map((k) => ({ ...k, t0: at(k.at) })).sort((a, b) => a.t0 - b.t0); START.clear(); }
export function starKeys() { return KEYS; }

function evalKey(fmt: Fmt, k: number, t: number, out: StarState) {
  const key = KEYS[k], A = starAttr();
  const s0 = startOf(fmt, k), B = resolveSet(key.set, fmt, t), f1 = isFront(key) ? 1 : 0;
  const st = key.straggle ?? 0.35, cv = key.curve ?? 0.18, local = clamp01((t - key.t0) / Math.max(1e-3, key.dur));
  for (let i = 0; i < N_CAST; i++) {
    const late = A.r1[i] > 0.95 ? 1.8 : 1.0;                       // 5% real stragglers
    const sw = key.sweep ? key.sweep * Math.max(0, Math.min(1, (s0.pos[i * 2] + ASPECT[fmt]) / (2 * ASPECT[fmt]))) : 0;
    const d = st * Math.pow(A.r1[i], 1.6) * late + sw, span = Math.max(0.05, 1 - st - (key.sweep ?? 0));
    const s = clamp01((local - Math.min(d, 0.9)) / span), e = easeInOut(s);
    const ax = s0.pos[i * 2], ay = s0.pos[i * 2 + 1], bx = B[i * 2], by = B[i * 2 + 1];
    const dx = bx - ax, dy = by - ay, bend = (A.r2[i] - 0.5) * 2 * cv * 4 * e * (1 - e); // a curved path: bulge perpendicular
    out.pos[i * 2] = ax + dx * e - dy * bend; out.pos[i * 2 + 1] = ay + dy * e + dx * bend;
    out.front[i] = s0.front[i] + (f1 - s0.front[i]) * e;
    out.motion[i] = s > 0 && s < 1 ? Math.min(1, Math.hypot(dx, dy) * 4 * e * (1 - e) * 2) : 0;
  }
}
function startOf(fmt: Fmt, k: number) {
  const id = `${fmt}|${k}`; const hit = START.get(id); if (hit) return hit;
  let v: { pos: Float32Array; front: Float32Array };
  if (k === 0) v = { pos: home(fmt), front: new Float32Array(N_CAST) };
  else { const o: StarState = { pos: new Float32Array(N_CAST * 2), front: new Float32Array(N_CAST), motion: new Float32Array(N_CAST) }; evalKey(fmt, k - 1, KEYS[k].t0, o); v = o; }
  START.set(id, v); return v;
}
export function starsAt(fmt: Fmt, t: number): StarState {
  const out: StarState = { pos: new Float32Array(N_CAST * 2), front: new Float32Array(N_CAST), motion: new Float32Array(N_CAST) };
  let k = -1; for (let i = 0; i < KEYS.length; i++) if (KEYS[i].t0 <= t) k = i;
  if (k < 0) { out.pos.set(home(fmt)); return out; }
  evalKey(fmt, k, t, out); return out;
}
