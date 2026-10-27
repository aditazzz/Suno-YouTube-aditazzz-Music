// shared helpers: easing and keyframes, seeded randomness, cheap good-looking materials (clay and gloss with a soft
// fresnel rim, as in "I have a blocker."), canvas textures, fonts, soft dots and blob shadows.
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';

export const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
export const lerp = (a, b, k) => a + (b - a) * k;
export const sstep = (a, b, x) => { if (b === a) return x >= b ? 1 : 0; const t = clamp((x - a) / (b - a)); return t * t * (3 - 2 * t); };
export const easeIO = (x) => { x = clamp(x); return x * x * x * (x * (6 * x - 15) + 10); };
export const easeOut = (x) => { x = clamp(x); return 1 - Math.pow(1 - x, 3); };
export const easeIn = (x) => { x = clamp(x); return x * x * x; };
export const easeOutBack = (x, s = 1.9) => { x = clamp(x); const c = s + 1; return 1 + c * Math.pow(x - 1, 3) + s * Math.pow(x - 1, 2); };
export const lin = (x) => clamp(x);
export const win = (t, a, b, fi = 0.3, fo = 0.3) => sstep(a - fi, a, t) * (1 - sstep(b, b + fo, t));
// a springy 0 -> 1 with one or two overshoots (pops, landings): starts at t0
export function pop(t, t0, dur = 0.45, amt = 1) { if (t <= t0) return 0; const u = (t - t0) / dur; if (u >= 3) return 1; return 1 - Math.exp(-4.2 * u) * Math.cos(u * 7.5) * amt; }
// a percussive event: 0 at rest, rises to 1 at t0 (over `up`), then decays
export const hit = (t, t0, up = 0.3) => (t < t0 - up || t >= t0 + 0.02) ? 0 : easeOut((t - (t0 - up)) / up);
export const decay = (t, t0, tau) => t < t0 ? 0 : Math.exp(-(t - t0) / tau);
// squash and stretch after an impact at t0: returns [xz, y] scale factors (volume kept roughly constant)
export function squash(t, t0, amt = 0.35, tau = 0.16) {
  if (t < t0) return [1, 1]; const u = t - t0; const s = amt * Math.exp(-u / tau) * Math.cos(u * 26);
  return [1 + s * 0.5, 1 - s];
}
// keyframes: [[t, value, ease?], ...]; values are numbers or arrays; the ease applies on the way in to that key
export function track(keys, t) {
  if (t <= keys[0][0]) return keys[0][1];
  for (let i = 1; i < keys.length; i++) {
    const [t1, v1, e] = keys[i];
    if (t < t1) { const [t0, v0] = keys[i - 1]; const u = (e || easeIO)((t - t0) / (t1 - t0)); return mixV(v0, v1, u); }
  }
  return keys[keys.length - 1][1];
}
export function mixV(a, b, u) { if (Array.isArray(a)) return a.map((x, i) => mixV(x, b[i], u)); if (typeof a !== 'number') return u < 0.5 ? a : b; return a + (b - a) * u; }

export function rng(seed) {             // mulberry32
  let s = seed >>> 0;
  return () => { s = (s + 0x6D2B79F5) >>> 0; let t = s; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
}
export const V3 = (x = 0, y = 0, z = 0) => new THREE.Vector3(x, y, z);

// ---------------------------------------------------------------- materials
// clay: Lambert (cheap on the CPU renderer) plus a soft fresnel rim so figures read against any background.
// The rim colour and amount are shared uniforms, so a shot can tint every figure at once.
export const RIM = { value: new THREE.Color(0xbfe9ff) };
export const RIM_AMT = { value: 0.45 };
function addRim(m, own, key) {
  m.onBeforeCompile = (sh) => {
    sh.uniforms.uRim = RIM; sh.uniforms.uRimAmt = own || RIM_AMT;
    sh.fragmentShader = sh.fragmentShader
      .replace('#include <common>', '#include <common>\nuniform vec3 uRim; uniform float uRimAmt;')
      .replace('#include <opaque_fragment>', `
        float fr = pow(1.0 - clamp(dot(normal, normalize(vViewPosition)), 0.0, 1.0), 2.6);
        outgoingLight += uRim * fr * uRimAmt;
        #include <opaque_fragment>`);
  };
  m.customProgramCacheKey = () => key + (own ? 'o' : '');
  return m;
}
export function clay(color, opts = {}) {
  const { rimAmt, ...rest } = opts;
  return addRim(new THREE.MeshLambertMaterial({ color, ...rest }), rimAmt !== undefined ? { value: rimAmt } : null, 'clay');
}
// gloss: Phong (a real highlight) for enamel, glass, plastic and screens' bezels
export function gloss(color, opts = {}) {
  const { rimAmt, ...rest } = opts;
  return addRim(new THREE.MeshPhongMaterial({ color, shininess: 60, specular: 0x666666, ...rest }), rimAmt !== undefined ? { value: rimAmt } : null, 'gloss');
}
export const basic = (color, opts = {}) => new THREE.MeshBasicMaterial({ color, ...opts });
export const glowMat = (color, opts = {}) => new THREE.MeshBasicMaterial({ color, toneMapped: false, ...opts });

export function rbox(w, h, d, r = 0.05, seg = 3) { return new RoundedBoxGeometry(w, h, d, seg, Math.min(r, w / 2 - 1e-4, h / 2 - 1e-4, d / 2 - 1e-4)); }
export function lathe(pts, seg = 28) {          // profile points in either order; normals always face out
  const p = pts[0][1] > pts[pts.length - 1][1] ? [...pts].reverse() : pts; return new THREE.LatheGeometry(p.map(([x, y]) => new THREE.Vector2(x, y)), seg); }

// ---------------------------------------------------------------- canvas textures and fonts
export function canvasTex(w, h, draw, opts = {}) {
  const c = document.createElement('canvas'); c.width = w; c.height = h;
  const g = c.getContext('2d'); if (draw) draw(g, w, h);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = 4; if (opts.nearest) { t.magFilter = THREE.NearestFilter; t.minFilter = THREE.NearestFilter; t.generateMipmaps = false; }
  if (opts.repeat) { t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(opts.repeat[0], opts.repeat[1]); }
  t.userData.g = g; t.userData.c = c;
  return t;
}
/** a canvas texture you redraw: tex.userData.redraw(fn) clears it, draws and flags the upload, only when the key changes */
export function liveTex(w, h) {
  const t = canvasTex(w, h); t.userData.key = null;
  t.userData.redraw = (key, fn) => { if (key === t.userData.key) return; t.userData.key = key; const g = t.userData.g; g.setTransform(1, 0, 0, 1, 0, 0); g.clearRect(0, 0, w, h); fn(g, w, h); t.needsUpdate = true; };
  return t;
}
export const FONT = {
  disp: '"InterD", sans-serif', black: '"InterBlack", sans-serif', ui: '"InterS", sans-serif', uiM: '"InterM", sans-serif', uiR: '"InterR", sans-serif',
  mono: '"JB", monospace', monoB: '"JBB", monospace', hand: '"Caveat", cursive', stamp: '"Stencil", sans-serif', anton: '"Anton", sans-serif',
  marker: '"Marker", cursive', serifI: '"SerifI", serif',
};
export async function loadFonts() {
  const list = [['InterD', 'InterDisplay-Bold.otf'], ['InterBlack', 'InterDisplay-Black.otf'], ['InterS', 'Inter-SemiBold.otf'], ['InterM', 'Inter-Medium.otf'],
    ['InterR', 'Inter-Regular.otf'], ['JB', 'JBMono-400.ttf'], ['JBB', 'JBMono-700.ttf'], ['Caveat', 'Caveat-Medium.ttf'], ['Stencil', 'SairaStencilOne-Regular.ttf'],
    ['Anton', 'Anton-Regular.ttf'], ['Marker', 'PermanentMarker-Regular.ttf'], ['SerifI', 'InstrumentSerif-Italic.ttf']];
  for (const [n, u] of list) { const f = new FontFace(n, `url(/fonts/${u})`); await f.load(); document.fonts.add(f); }
}

// soft round sprite (glows, particles, blob shadows)
let _dot = null;
export function dotTex() {
  if (_dot) return _dot;
  _dot = canvasTex(64, 64, (g) => { const gr = g.createRadialGradient(32, 32, 0, 32, 32, 32); gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.4, 'rgba(255,255,255,0.55)'); gr.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = gr; g.fillRect(0, 0, 64, 64); });
  _dot.colorSpace = THREE.NoColorSpace; return _dot;
}
export function blobShadow(w, d, op = 0.5) {
  const m = new THREE.Mesh(new THREE.PlaneGeometry(w, d), new THREE.MeshBasicMaterial({ map: dotTex(), color: 0x000000, transparent: true, opacity: op, depthWrite: false }));
  m.rotation.x = -Math.PI / 2; m.renderOrder = 1; return m;
}
export function glowSprite(color, size, op = 1) {
  const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: dotTex(), color, transparent: true, opacity: op, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false }));
  s.scale.setScalar(size); return s;
}
// a flat text plane (signs, labels, stamps): text on a canvas, sized in world units by its height
export function textPlane(text, { h = 0.3, font = FONT.black, size = 120, fg = '#ffffff', bg = null, pad = 0.3, radius = 0.25, stroke = null, lit = false, align = 'center' } = {}) {
  const tmp = document.createElement('canvas').getContext('2d'); tmp.font = `${size}px ${font}`;
  const tw = tmp.measureText(text).width; const ph = size * (1 + pad * 2); const pw = tw + size * pad * 2;
  const tex = canvasTex(Math.ceil(pw), Math.ceil(ph), (g, w, hh) => {
    if (bg) { g.fillStyle = bg; g.beginPath(); g.roundRect(0, 0, w, hh, hh * radius); g.fill(); }
    g.font = `${size}px ${font}`; g.textBaseline = 'middle'; g.textAlign = 'center';
    if (stroke) { g.lineWidth = size * 0.12; g.strokeStyle = stroke; g.lineJoin = 'round'; g.strokeText(text, w / 2, hh / 2 + size * 0.05); }
    g.fillStyle = fg; g.fillText(text, w / 2, hh / 2 + size * 0.05);
  });
  const mat = lit ? new THREE.MeshLambertMaterial({ map: tex, transparent: true }) : new THREE.MeshBasicMaterial({ map: tex, transparent: true, depthWrite: false, toneMapped: false });
  const geo = new THREE.PlaneGeometry(h * pw / ph, h); if (align === 'left') geo.translate(h * pw / ph / 2, 0, 0);
  const m = new THREE.Mesh(geo, mat); m.userData.w = h * pw / ph; return m;
}
