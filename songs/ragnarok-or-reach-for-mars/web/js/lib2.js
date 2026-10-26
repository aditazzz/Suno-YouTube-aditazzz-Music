// Ragnarök or Reach for Mars: extra helpers on top of lib.js (shared with the "I have a blocker." film) (procedural textures, seeded noise, environment).
import * as THREE from 'three';
import { canvasTex, rng, clamp } from './lib.js';

// ---------------------------------------------------------------- value noise (deterministic, for textures)
export function noise2(seed = 1) {
  const R = rng(seed), P = new Float32Array(256 * 256); for (let i = 0; i < P.length; i++) P[i] = R();
  const at = (x, y) => P[((y & 255) << 8) | (x & 255)];
  const sm = (t) => t * t * (3 - 2 * t);
  const n = (x, y) => { const xi = Math.floor(x), yi = Math.floor(y), xf = x - xi, yf = y - yi;
    const a = at(xi, yi), b = at(xi + 1, yi), c = at(xi, yi + 1), d = at(xi + 1, yi + 1); const u = sm(xf), v = sm(yf);
    return a + (b - a) * u + (c - a) * v + (a - b - c + d) * u * v; };
  n.fbm = (x, y, o = 4) => { let s = 0, f = 1, a = 0.5, t = 0; for (let i = 0; i < o; i++) { s += a * n(x * f, y * f); t += a; f *= 2.03; a *= 0.5; } return s / t; };
  return n;
}

// ---------------------------------------------------------------- carved / sawn wood
// grain runs along x; `rings` bends the grain round a couple of knots. Returned as a repeating sRGB texture.
export function woodTex({ w = 512, h = 512, base = '#6b4a2f', dark = '#3b2616', light = '#8a6440', seed = 3, streak = 1, knots = 2, repeat = [1, 1], planks = 0 } = {}) {
  const N = noise2(seed), R = rng(seed + 7);
  const kn = Array.from({ length: knots }, () => [R() * w, R() * h, 18 + R() * 30]);
  return canvasTex(w, h, (g) => {
    const img = g.createImageData(w, h); const d = img.data;
    const cb = hex(base), cd = hex(dark), cl = hex(light);
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
      let yy = y; for (const [kx, ky, kr] of kn) { const dx = x - kx, dy = y - ky; const r2 = dx * dx * 0.25 + dy * dy; yy += kr * 2.2 * Math.exp(-r2 / (kr * kr * 9)) * Math.sign(dy || 1); }
      const v = N.fbm(x / w * 3, yy / h * 40 * streak, 3);
      const line = Math.pow(Math.abs(Math.sin((yy / h * 46 + N(x / w * 6, y / h * 6) * 6) * Math.PI)), 6);
      let k = 0.5 + (v - 0.5) * 1.4 - line * 0.35;
      if (planks) { const py = (y % (h / planks)); if (py < 2) k -= 0.6; }
      k = clamp(k);
      const c = k < 0.5 ? mix3(cd, cb, k * 2) : mix3(cb, cl, (k - 0.5) * 2);
      const i = (y * w + x) * 4; d[i] = c[0]; d[i + 1] = c[1]; d[i + 2] = c[2]; d[i + 3] = 255;
    }
    g.putImageData(img, 0, 0);
  }, { repeat });
}
export function hex(s) { const n = parseInt(s.slice(1), 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255]; }
export function mix3(a, b, k) { return [a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k, a[2] + (b[2] - a[2]) * k]; }

// wool / felt: soft speckle
export function woolTex(base = '#5a4a3a', seed = 5, repeat = [2, 2]) {
  const N = noise2(seed); const cb = hex(base);
  return canvasTex(256, 256, (g, w, h) => { const img = g.createImageData(w, h); const d = img.data;
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) { const v = 0.82 + 0.3 * (N.fbm(x / 9, y / 9, 3) - 0.5) + 0.12 * (N(x * 1.7, y * 1.3) - 0.5);
      const i = (y * w + x) * 4; d[i] = cb[0] * v; d[i + 1] = cb[1] * v; d[i + 2] = cb[2] * v; d[i + 3] = 255; }
    g.putImageData(img, 0, 0); }, { repeat });
}
// fur: dense strands
export function furTex(base = '#e9e4da', tip = '#ffffff', seed = 9, repeat = [6, 1]) {
  const R = rng(seed);
  return canvasTex(256, 128, (g, w, h) => { g.fillStyle = shade(base, 0.7); g.fillRect(0, 0, w, h);
    for (let i = 0; i < 2600; i++) { const x = R() * w, y = R() * h, l = 6 + R() * 16, a = -Math.PI / 2 + (R() - 0.5) * 0.9;
      g.strokeStyle = R() < 0.5 ? base : tip; g.globalAlpha = 0.35 + R() * 0.5; g.lineWidth = 0.8 + R() * 1.2;
      g.beginPath(); g.moveTo(x, y); g.lineTo(x + Math.cos(a) * l, y + Math.sin(a) * l); g.stroke(); } g.globalAlpha = 1; }, { repeat });
}
export function shade(hexs, k) { const c = hex(hexs); return `rgb(${c[0] * k | 0},${c[1] * k | 0},${c[2] * k | 0})`; }
// chain mail: rows of little rings
export function mailTex(repeat = [10, 3]) {
  return canvasTex(128, 128, (g, w, h) => { g.fillStyle = '#16171a'; g.fillRect(0, 0, w, h);
    for (let row = 0; row < 9; row++) for (let col = 0; col < 9; col++) { const x = col * 16 + (row % 2) * 8, y = row * 16;
      g.strokeStyle = '#8d9096'; g.lineWidth = 2.6; g.beginPath(); g.ellipse(x, y, 6.5, 5.5, 0, 0, Math.PI * 2); g.stroke();
      g.strokeStyle = 'rgba(255,255,255,0.35)'; g.lineWidth = 1; g.beginPath(); g.arc(x - 1, y - 1.5, 5, Math.PI * 1.1, Math.PI * 1.6); g.stroke(); } }, { repeat });
}
// round shield face: quartered paint, iron rim and boss
export function shieldTex(c1, c2, seed = 1, style = 'quarters') {
  const N = noise2(seed);
  return canvasTex(512, 512, (g, w, h) => {
    const cx = w / 2, cy = h / 2, r = w / 2 - 6;
    g.fillStyle = c1; g.beginPath(); g.arc(cx, cy, r, 0, Math.PI * 2); g.fill(); g.fillStyle = c2;
    if (style === 'quarters') for (let k = 0; k < 4; k += 2) { g.beginPath(); g.moveTo(cx, cy); g.arc(cx, cy, r, k * Math.PI / 2, (k + 1) * Math.PI / 2); g.closePath(); g.fill(); }
    if (style === 'halves') { g.beginPath(); g.moveTo(cx, cy); g.arc(cx, cy, r, -Math.PI / 2, Math.PI / 2); g.closePath(); g.fill(); }
    if (style === 'whirl') for (let k = 0; k < 4; k++) { g.save(); g.translate(cx, cy); g.rotate(k * Math.PI / 2); g.beginPath(); g.moveTo(0, 0);
      g.bezierCurveTo(r * 0.5, -r * 0.1, r * 0.7, -r * 0.5, r * 0.4, -r * 0.92); g.arc(0, 0, r, -Math.PI / 2 + 0.42 - Math.PI / 2 + Math.PI / 2 - 0.0, -Math.PI / 2 + 0.95); g.bezierCurveTo(r * 0.85, -r * 0.2, r * 0.6, r * 0.05, 0, 0); g.closePath(); g.fill(); g.restore(); }
    if (style === 'ring') { g.lineWidth = r * 0.16; g.strokeStyle = c2; g.beginPath(); g.arc(cx, cy, r * 0.62, 0, Math.PI * 2); g.stroke(); }
    const img = g.getImageData(0, 0, w, h); const d = img.data;   // weather it
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) { const i = (y * w + x) * 4, v = 0.66 + 0.45 * (N.fbm(x / 40, y / 40, 4) - 0.5) + 0.2 * (N(x / 3, y / 90) - 0.5);
      d[i] *= v; d[i + 1] *= v; d[i + 2] *= v; }
    g.putImageData(img, 0, 0);
    g.strokeStyle = '#2b2b2e'; g.lineWidth = 16; g.beginPath(); g.arc(cx, cy, r - 8, 0, Math.PI * 2); g.stroke();
    for (let k = 0; k < 16; k++) { const a = k / 16 * Math.PI * 2; g.fillStyle = '#5c5d61'; g.beginPath(); g.arc(cx + Math.cos(a) * (r - 8), cy + Math.sin(a) * (r - 8), 5, 0, Math.PI * 2); g.fill(); }
  });
}

// ---------------------------------------------------------------- environment for metals and glass (warm hall, one cool opening)
// HDR panels (colours above 1) so gold, steel and glass catch real highlights: the long fire, torches, the smoke hole.
export function hallEnv(renderer, { fire = 4, torch = 2.4, sky = 0.9, wall = 1, doors = 0, rafters = 0.35 } = {}) {
  const s = new THREE.Scene(); s.background = new THREE.Color(0x020202);
  const wt = canvasTex(16, 256, (g, w, h) => { const gr = g.createLinearGradient(0, 0, 0, h); gr.addColorStop(0, '#040302'); gr.addColorStop(0.45, '#120a06'); gr.addColorStop(0.75, '#2e1a0e'); gr.addColorStop(1, '#4a2a14'); g.fillStyle = gr; g.fillRect(0, 0, w, h); });
  const box = new THREE.Mesh(new THREE.BoxGeometry(20, 10, 20), new THREE.MeshBasicMaterial({ map: wt, side: THREE.BackSide })); box.material.color.setScalar(wall); s.add(box);
  const glow = (r, g2, b, k, x, y, z, sx, sy) => { const m = new THREE.Mesh(new THREE.PlaneGeometry(sx, sy), new THREE.MeshBasicMaterial({ side: THREE.DoubleSide })); m.material.color.setRGB(r * k, g2 * k, b * k); m.position.set(x, y, z); m.lookAt(0, 0, 0); s.add(m); };
  glow(1.0, 0.45, 0.14, fire, 0, -1.6, 6.5, 10, 2.6);                  // the long fire
  glow(1.0, 0.55, 0.2, fire * 0.5, 0, -2.5, -6.5, 8, 1.6);             // its glow on the far side
  for (const x of [-6, 6]) for (const z of [-5, 5]) glow(1.0, 0.62, 0.3, torch, x, 1.4, z, 0.9, 1.3);   // torches
  glow(0.55, 0.68, 1.0, sky, 0, 4.9, 1.5, 2.6, 2.6);                   // the smoke hole: moonlight
  glow(1.0, 0.5, 0.22, rafters, 0, 4.8, -4, 14, 6);                    // firelight on the rafters
  glow(1.0, 0.5, 0.22, rafters * 0.7, 0, 4.8, 5, 14, 5);
  if (doors) glow(0.5, 0.62, 1.0, doors, 0, 0.5, -9.9, 4, 6);          // the doors open onto the night
  const pm = new THREE.PMREMGenerator(renderer); const env = pm.fromScene(s, 0.02).texture; pm.dispose(); return env;
}

// ---------------------------------------------------------------- fonts this film uses (all OFL, in /fonts)
export async function loadFilmFonts() {
  const list = [['Corm', 'CormorantGaramond-Bold.ttf'], ['CormSB', 'CormorantGaramond-SemiBold.ttf'], ['CormM', 'CormorantGaramond-Medium.ttf'], ['CormMI', 'CormorantGaramond-MediumItalic.ttf'], ['CormSC', 'CormorantSC-Medium.ttf']];
  for (const [n, f] of list) { const ff = new FontFace(n, `url(/fonts/${f})`); await ff.load(); document.fonts.add(ff); }
}
