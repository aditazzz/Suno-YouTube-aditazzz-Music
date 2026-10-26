// shared helpers: easing, seeded randomness, cheap good-looking materials, canvas textures
import * as THREE from 'three';

export const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
export const lerp = (a, b, k) => a + (b - a) * k;
export const sstep = (a, b, x) => { if (b === a) return x >= b ? 1 : 0; const t = clamp((x - a) / (b - a)); return t * t * (3 - 2 * t); };
export const easeIO = (x) => { x = clamp(x); return x * x * x * (x * (6 * x - 15) + 10); };
export const easeOut = (x) => { x = clamp(x); return 1 - Math.pow(1 - x, 3); };
export const easeIn = (x) => { x = clamp(x); return x * x * x; };
export const win = (t, a, b, fi = 0.3, fo = 0.3) => sstep(a - fi, a, t) * (1 - sstep(b, b + fo, t));

export function rng(seed) {             // mulberry32
  let s = seed >>> 0;
  return () => { s = (s + 0x6D2B79F5) >>> 0; let t = s; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
}

// ---------------------------------------------------------------- materials
// clay: Lambert (cheap on the CPU renderer) plus a soft fresnel rim so figures read against the dark like the
// lit mannequins of the "I have a blocker." film. The rim colour is shared, so a scene can tint every figure at once.
export const RIM = { value: new THREE.Color(0x9fe8c4) };
export const RIM_AMT = { value: 0.55 };
export function clay(color, opts = {}) {
  const { rimAmt, ...rest } = opts;
  const m = new THREE.MeshLambertMaterial({ color, ...rest });
  const own = rimAmt !== undefined ? { value: rimAmt } : null;
  m.onBeforeCompile = (sh) => {
    sh.uniforms.uRim = RIM; sh.uniforms.uRimAmt = own || RIM_AMT;
    sh.fragmentShader = sh.fragmentShader
      .replace('#include <common>', '#include <common>\nuniform vec3 uRim; uniform float uRimAmt;')
      .replace('#include <opaque_fragment>', `
        float fr = pow(1.0 - clamp(dot(normal, normalize(vViewPosition)), 0.0, 1.0), 2.6);
        outgoingLight += uRim * fr * uRimAmt;
        #include <opaque_fragment>`);
  };
  m.customProgramCacheKey = () => 'clay' + (own ? 'o' : '');
  return m;
}
export const basic = (color, opts = {}) => new THREE.MeshBasicMaterial({ color, ...opts });

// ---------------------------------------------------------------- canvas textures
export function canvasTex(w, h, draw, opts = {}) {
  const c = document.createElement('canvas'); c.width = w; c.height = h;
  const g = c.getContext('2d'); draw(g, w, h);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = 4; if (opts.nearest) t.magFilter = THREE.NearestFilter;
  if (opts.repeat) { t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(opts.repeat[0], opts.repeat[1]); }
  return t;
}
export const FONT = {
  disp: '"InterD", sans-serif', dispBlack: '"InterBlack", sans-serif', ui: '"InterS", sans-serif',
  mono: '"JB", monospace', monoB: '"JBB", monospace', serif: '"Corm", serif',
};
export async function loadFonts() {
  const list = [['InterD', '/fonts/InterDisplay-Bold.otf'], ['InterBlack', '/fonts/InterDisplay-Black.otf'], ['InterS', '/fonts/Inter-SemiBold.otf'],
    ['InterM', '/fonts/Inter-Medium.otf'], ['JB', '/fonts/JBMono-400.ttf'], ['JBB', '/fonts/JBMono-700.ttf'], ['Corm', '/fonts/CormorantGaramond-Bold.ttf']];
  for (const [n, u] of list) { const f = new FontFace(n, `url(${u})`); await f.load(); document.fonts.add(f); }
}

// a label plane (name tags, signs): text drawn on a canvas, sized in world units by height
export function labelPlane(text, { h = 0.22, font = FONT.ui, size = 64, fg = '#f0f0f2', bg = 'rgba(10,10,12,0.72)', pad = 0.45, radius = 0.3, icon = null } = {}) {
  const tmp = document.createElement('canvas').getContext('2d'); tmp.font = `${size}px ${font}`;
  const tw = tmp.measureText(text).width; const ph = size * (1 + pad * 2); const iw = icon ? size * 1.1 : 0;
  const pw = tw + size * pad * 2 + iw;
  const tex = canvasTex(Math.ceil(pw), Math.ceil(ph), (g, w, hh) => {
    if (bg) { g.fillStyle = bg; const r = hh * radius; g.beginPath(); g.roundRect(0, 0, w, hh, r); g.fill(); }
    if (icon) icon(g, size * pad + size * 0.4, hh / 2, size * 0.8);
    g.font = `${size}px ${font}`; g.fillStyle = fg; g.textBaseline = 'middle'; g.fillText(text, size * pad + iw, hh / 2 + size * 0.04);
  });
  const m = new THREE.Mesh(new THREE.PlaneGeometry(h * pw / ph, h), new THREE.MeshBasicMaterial({ map: tex, transparent: true, depthWrite: false, toneMapped: false }));
  m.userData.w = h * pw / ph; return m;
}

export function micOff(g, x, y, s, col = '#ff5a5a') {
  g.save(); g.strokeStyle = col; g.lineWidth = s * 0.11; g.lineCap = 'round';
  g.beginPath(); g.roundRect(x - s * 0.17, y - s * 0.5, s * 0.34, s * 0.6, s * 0.17); g.stroke();
  g.beginPath(); g.arc(x, y - s * 0.02, s * 0.32, 0.1, Math.PI - 0.1); g.stroke();
  g.beginPath(); g.moveTo(x, y + s * 0.3); g.lineTo(x, y + s * 0.48); g.stroke();
  g.beginPath(); g.moveTo(x - s * 0.42, y - s * 0.5); g.lineTo(x + s * 0.42, y + s * 0.48); g.stroke(); g.restore();
}

// soft round sprite (for glows, particles, blob shadows)
let _dot = null;
export function dotTex() {
  if (_dot) return _dot;
  _dot = canvasTex(64, 64, (g) => { const gr = g.createRadialGradient(32, 32, 0, 32, 32, 32); gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.4, 'rgba(255,255,255,0.55)'); gr.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = gr; g.fillRect(0, 0, 64, 64); });
  _dot.colorSpace = THREE.NoColorSpace; return _dot;
}
export function blobShadow(w, d, op = 0.55) {
  const m = new THREE.Mesh(new THREE.PlaneGeometry(w, d), new THREE.MeshBasicMaterial({ map: dotTex(), color: 0x000000, transparent: true, opacity: op, depthWrite: false }));
  m.rotation.x = -Math.PI / 2; m.renderOrder = 1; return m;
}
