// Look What I Can Do · Scope Creep: shared helpers (timing, easing, randomness, canvas textures, fonts, camera paths)
import * as THREE from 'three';

export const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
export const lerp = (a, b, k) => a + (b - a) * k;
export const sstep = (a, b, x) => { if (b === a) return x >= b ? 1 : 0; const t = clamp((x - a) / (b - a)); return t * t * (3 - 2 * t); };
export const easeIO = (x) => { x = clamp(x); return x * x * x * (x * (6 * x - 15) + 10); };
export const easeOut = (x) => { x = clamp(x); return 1 - Math.pow(1 - x, 3); };
export const easeOut5 = (x) => { x = clamp(x); return 1 - Math.pow(1 - x, 5); };
export const easeIn = (x) => { x = clamp(x); return x * x * x; };
export const expOut = (x) => { x = clamp(x); return x >= 1 ? 1 : 1 - Math.pow(2, -10 * x); };
export const backOut = (x, s = 1.6) => { x = clamp(x) - 1; return 1 + x * x * ((s + 1) * x + s); };
export const win = (t, a, b, fi = 0.3, fo = 0.3) => sstep(a - fi, a, t) * (1 - sstep(b, b + fo, t));
export const env = (t, t0, rise = 0.06, fall = 0.4) => { if (t < t0) return 0; const x = t - t0; return Math.min(1, x / rise) * Math.exp(-Math.max(0, x - rise) / fall); };
export const V3 = (x, y, z) => new THREE.Vector3(x, y, z);

export function rng(seed) {             // mulberry32
  let s = seed >>> 0;
  return () => { s = (s + 0x6D2B79F5) >>> 0; let t = s; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
}
// smooth 1D noise (for handheld drift)
export function noise1(x, seed = 0) {
  const i = Math.floor(x), f = x - i; const h = (n) => { const s = Math.sin((n + seed * 101.7) * 127.1) * 43758.5453; return s - Math.floor(s); };
  const u = f * f * (3 - 2 * f); return lerp(h(i), h(i + 1), u) * 2 - 1;
}

// ---------------------------------------------------------------- song timing (from build/timed.json + beats.json)
export const TIMING = { lines: [], beats: [], downbeats: [], tempo: 129.2, duration: 186.4 };
export async function loadTiming() {
  const [tl, bt] = await Promise.all([fetch('/data/timed.json').then((r) => r.json()), fetch('/data/beats.json').then((r) => r.json())]);
  TIMING.lines = tl; TIMING.beats = bt.beats; TIMING.downbeats = bt.downbeats; TIMING.tempo = bt.tempo; TIMING.duration = bt.duration;
}
export function line(sub, nth = 0) { const h = TIMING.lines.filter((L) => L.text.toLowerCase().includes(sub.toLowerCase())); return h[nth]; }
export const ls = (sub, nth = 0) => line(sub, nth).s;
const norm = (w) => w.toLowerCase().replace(/[^a-z0-9']/g, '');
export function wt(sub, word, nthLine = 0, nthWord = 0) {
  const L = line(sub, nthLine); let k = 0;
  for (let i = 0; i < L.words.length; i++) if (norm(L.words[i]) === norm(word)) { if (k === nthWord) return L.wt[i]; k++; }
  throw new Error('word not found: ' + sub + ' / ' + word);
}
export function beatIndex(t) { const b = TIMING.beats; let lo = 0, hi = b.length - 1; if (t < b[0]) return -1; while (lo < hi) { const m = (lo + hi + 1) >> 1; if (b[m] <= t) lo = m; else hi = m - 1; } return lo; }
export const beatAt = (i) => TIMING.beats[Math.max(0, Math.min(TIMING.beats.length - 1, i))];
export function beatPulse(t, k = 8) { const i = beatIndex(t); if (i < 0) return 0; return Math.exp(-(t - TIMING.beats[i]) * k); }

// ---------------------------------------------------------------- fonts + canvas textures
export const FONT = { anton: '"Anton"', disp: '"InterD"', dispBlack: '"InterBlack"', ui: '"InterS"', mono: '"JB"', monoB: '"JBB"', serif: '"Serif"', serifI: '"SerifI"' };
export async function loadFonts() {
  const list = [['Anton', '/fonts/Anton-Regular.ttf'], ['InterD', '/fonts/InterDisplay-Bold.otf'], ['InterBlack', '/fonts/InterDisplay-Black.otf'], ['InterS', '/fonts/Inter-SemiBold.otf'],
    ['InterM', '/fonts/Inter-Medium.otf'], ['JB', '/fonts/JBMono-400.ttf'], ['JBB', '/fonts/JBMono-700.ttf'], ['Serif', '/fonts/InstrumentSerif-Regular.ttf'], ['SerifI', '/fonts/InstrumentSerif-Italic.ttf']];
  for (const [n, u] of list) { const f = new FontFace(n, `url(${u})`); await f.load(); document.fonts.add(f); }
}
export function canvasTex(w, h, draw, opts = {}) {
  const c = document.createElement('canvas'); c.width = w; c.height = h;
  const g = c.getContext('2d'); draw(g, w, h);
  const t = new THREE.CanvasTexture(c); t.colorSpace = opts.linear ? THREE.NoColorSpace : THREE.SRGBColorSpace;
  t.anisotropy = 8; if (opts.nearest) t.magFilter = THREE.NearestFilter;
  if (opts.repeat) { t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(opts.repeat[0], opts.repeat[1]); }
  t.userData = { canvas: c, g };
  return t;
}
export function measure(text, font) { const g = document.createElement('canvas').getContext('2d'); g.font = font; return g.measureText(text).width; }

// a plane carrying text; world height h; returns mesh with userData.w
export function textPlane(text, { h = 1, font = FONT.anton, size = 160, color = '#ffffff', glow = 0, glowColor = null, pad = 0.18, emissive = 1, opacity = 1, align = 'center', letter = 0, bg = null } = {}) {
  const f = `${size}px ${font}`; const g0 = document.createElement('canvas').getContext('2d'); g0.font = f; g0.letterSpacing = `${letter}px`;
  const tw = g0.measureText(text).width; const ph = Math.ceil(size * (1.25 + pad * 2)); const pw = Math.ceil(tw + size * pad * 2 + glow * 2);
  const tex = canvasTex(pw, ph, (g, w, hh) => {
    if (bg) { g.fillStyle = bg; g.beginPath(); g.roundRect(0, 0, w, hh, hh * 0.18); g.fill(); }
    g.font = f; g.letterSpacing = `${letter}px`; g.textBaseline = 'middle'; g.textAlign = 'center';
    if (glow) { g.shadowColor = glowColor || color; g.shadowBlur = glow; for (let i = 0; i < 3; i++) { g.fillStyle = glowColor || color; g.fillText(text, w / 2, hh / 2 + size * 0.03); } g.shadowBlur = 0; }
    g.fillStyle = color; g.fillText(text, w / 2, hh / 2 + size * 0.03);
  });
  const mat = new THREE.MeshBasicMaterial({ map: tex, transparent: true, depthWrite: false, toneMapped: false, opacity });
  mat.color.setScalar(emissive);
  const geo = new THREE.PlaneGeometry(h * pw / ph, h);
  if (align === 'left') geo.translate(h * pw / ph / 2, 0, 0);
  const m = new THREE.Mesh(geo, mat); m.userData.w = h * pw / ph; m.userData.tex = tex;
  return m;
}

// soft radial sprite texture
let _dot = null;
export function dotTex() {
  if (_dot) return _dot;
  _dot = canvasTex(128, 128, (g) => { const gr = g.createRadialGradient(64, 64, 0, 64, 64, 64); gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.25, 'rgba(255,255,255,0.6)'); gr.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = gr; g.fillRect(0, 0, 128, 128); }, { linear: true });
  return _dot;
}

// ---------------------------------------------------------------- camera paths
// keys: [{t, p:[x,y,z], l:[x,y,z], fov, roll}] ; Catmull-Rom on position/target, eased per segment option
export function camPath(keys) {
  const P = new THREE.CatmullRomCurve3(keys.map((k) => V3(...k.p)), false, 'centripetal');
  const L = new THREE.CatmullRomCurve3(keys.map((k) => V3(...k.l)), false, 'centripetal');
  const n = keys.length;
  return (t, ease = easeIO) => {
    if (t <= keys[0].t) return { p: V3(...keys[0].p), l: V3(...keys[0].l), fov: keys[0].fov ?? 35, roll: keys[0].roll ?? 0 };
    if (t >= keys[n - 1].t) return { p: V3(...keys[n - 1].p), l: V3(...keys[n - 1].l), fov: keys[n - 1].fov ?? 35, roll: keys[n - 1].roll ?? 0 };
    let i = 0; while (i < n - 2 && t > keys[i + 1].t) i++;
    const a = keys[i], b = keys[i + 1]; const e = (b.ease || ease)((t - a.t) / (b.t - a.t));
    const u = (i + e) / (n - 1);
    return { p: P.getPoint(u), l: L.getPoint(u), fov: lerp(a.fov ?? 35, b.fov ?? 35, e), roll: lerp(a.roll ?? 0, b.roll ?? 0, e) };
  };
}
