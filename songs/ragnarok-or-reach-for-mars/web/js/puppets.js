// Carved, painted wooden puppets on the jointed rig from the "I have a blocker." film (two-bone IK arms; seated or standing legs).
// The look: sanded, smooth faces with painted features (an expression changes with a texture swap: the seeress
// opens her eyes, the man grins on "twenty percent"); knife-cut, faceted clothing in matte paint over fine grain,
// with painted trims. Big heads, short legs: puppets, not people.
import * as THREE from 'three';
import { clay, canvasTex, clamp } from './lib.js';
import { noise2, hex } from './lib2.js';

const UP = new THREE.Vector3(0, 1, 0);
const _v = new THREE.Vector3();
const sm = (a, b, x) => { const t = clamp((x - a) / (b - a)); return t * t * (3 - 2 * t); };
const gauss = (x, s) => Math.exp(-(x * x) / (2 * s * s));
const TAU = Math.PI * 2;

// lathe with u running round from the back (u = 0.5 is the front, +z) and v = height, so clothes can be painted
function lathe(pts, seg = 12, p0 = Math.PI, pl = TAU) {
  const geo = new THREE.LatheGeometry(pts.map(([x, y]) => new THREE.Vector2(x, y)), seg, p0, pl);
  const ys = pts.map((p) => p[1]), y0 = Math.min(...ys), y1 = Math.max(...ys); const p = geo.attributes.position, uv = geo.attributes.uv;
  for (let i = 0; i < p.count; i++) uv.setY(i, (p.getY(i) - y0) / (y1 - y0 || 1));
  return geo;
}

// ---------------------------------------------------------------- paint over wood
function grainPixels(d, w, h, c, N, { grain, streak, vertical }) {
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    const a = vertical ? x / w : y / h, b = vertical ? y / h : x / w;
    const gr = Math.pow(Math.abs(Math.sin((a * 14 + N.fbm(b * 2, a * 6, 3) * 3) * Math.PI)), 10);
    const br = N.fbm(b * 10, a * 2.5, 2) - 0.5;
    const k = 1 - grain * gr + streak * br * 2 + (N(x * 0.7, y * 0.7) - 0.5) * 0.05;
    const i = (y * w + x) * 4; d[i] = c[0] * k; d[i + 1] = c[1] * k; d[i + 2] = c[2] * k; d[i + 3] = 255;
  }
}
export function paintTex(color, { seed = 1, grain = 0.1, streak = 0.05, w = 256, h = 256, repeat = [1, 1], vertical = false, draw = null } = {}) {
  const N = noise2(seed); const c = hex(color);
  return canvasTex(w, h, (g) => { const img = g.createImageData(w, h); grainPixels(img.data, w, h, c, N, { grain, streak, vertical }); g.putImageData(img, 0, 0); if (draw) draw(g, w, h); }, { repeat });
}
export const paint = (color, o = {}) => clay(0xffffff, { map: paintTex(color, o), flatShading: o.smooth ? false : true, ...(o.rimAmt !== undefined ? { rimAmt: o.rimAmt } : {}), ...(o.side ? { side: o.side } : {}) });
const metal = (color, env, o = {}) => new THREE.MeshStandardMaterial({ color, metalness: o.metalness ?? 0.75, roughness: o.roughness ?? 0.42, envMap: env, envMapIntensity: o.env ?? 1, flatShading: o.flat ?? false });

// woven tablet bands (the trim on Viking clothes): a repeating diamond pattern between two rules
function band(g, w, y0, y1, c1, c2) {
  const hh = y1 - y0; g.fillStyle = c1; g.fillRect(0, y0, w, hh);
  g.fillStyle = c2; const n = Math.round(w / hh);
  for (let i = 0; i < n; i++) { const x = (i + 0.5) * w / n; g.beginPath(); g.moveTo(x, y0 + hh * 0.18); g.lineTo(x + hh * 0.32, y0 + hh / 2); g.lineTo(x, y1 - hh * 0.18); g.lineTo(x - hh * 0.32, y0 + hh / 2); g.closePath(); g.fill(); }
  g.fillStyle = 'rgba(0,0,0,0.35)'; g.fillRect(0, y0, w, hh * 0.08); g.fillRect(0, y1 - hh * 0.08, w, hh * 0.08);
}

// ---------------------------------------------------------------- painted faces
// The head is a sphere, so the face is painted in (longitude, latitude) radians: lon 0 is the front, + is the
// figure's left. One canvas covers the whole head; carved hair, beards and hoods sit on top of it.
class Face {
  constructor(g, W) { this.g = g; this.W = W; this.K = W / TAU; this.cx = W / 4; this.cy = W / 4; }
  P(lo, la) { return [this.cx + lo * this.K, this.cy - la * this.K]; }
  poly(pts, col) { const g = this.g; g.beginPath(); pts.forEach(([lo, la], i) => { const [x, y] = this.P(lo, la); if (i) g.lineTo(x, y); else g.moveTo(x, y); }); g.closePath(); g.fillStyle = col; g.fill(); }
  curve(pts, close) { const Q = sample(pts, 48, close); const g = this.g; g.beginPath(); Q.forEach(([lo, la], i) => { const [x, y] = this.P(lo, la); if (i) g.lineTo(x, y); else g.moveTo(x, y); }); if (close) g.closePath(); }
  line(pts, col, w) { const g = this.g; this.curve(pts, false); g.strokeStyle = col; g.lineWidth = w * this.K; g.lineCap = 'round'; g.lineJoin = 'round'; g.stroke(); }
  shape(pts, col) { this.curve(pts, true); this.g.fillStyle = col; this.g.fill(); }
  taper(pts, col, w0, w1, peak = 0.35) {   // w0 at the start, w1 at `peak`, pointed at the end (brows)
    const n = 32, A = [], B = []; const Q = sample(pts, n, false);
    for (let i = 0; i <= n; i++) { const t = i / n; const w = (t < peak ? w0 + (w1 - w0) * Math.sin(t / peak * Math.PI / 2) : w1 * Math.cos((t - peak) / (1 - peak) * Math.PI / 2) + 0.004) / 2;
      const [x0, y0] = Q[Math.max(0, i - 1)], [x1, y1] = Q[Math.min(n, i + 1)]; const dx = x1 - x0, dy = y1 - y0, L = Math.hypot(dx, dy) || 1;
      A.push([Q[i][0] - dy / L * w, Q[i][1] + dx / L * w]); B.push([Q[i][0] + dy / L * w, Q[i][1] - dx / L * w]); }
    this.poly([...A, ...B.reverse()], col);
  }
  blob(lo, la, rx, ry, col) { const g = this.g; const [x, y] = this.P(lo, la); g.beginPath(); g.ellipse(x, y, rx * this.K, ry * this.K, 0, 0, TAU); g.fillStyle = col; g.fill(); }
  glow(lo, la, r, col) { const g = this.g; const [x, y] = this.P(lo, la); const gr = g.createRadialGradient(x, y, 0, x, y, r * this.K); gr.addColorStop(0, col); gr.addColorStop(1, 'rgba(0,0,0,0)'); g.fillStyle = gr; g.fillRect(x - r * this.K, y - r * this.K, 2 * r * this.K, 2 * r * this.K); }
  region(fn, col, below = false) {   // fill above (or below) a line given as a function of |lon| (0..PI), across the whole wrap
    const g = this.g; g.beginPath(); g.moveTo(0, below ? this.W / 2 : 0); g.lineTo(this.W, below ? this.W / 2 : 0);
    for (let i = 0; i <= 240; i++) { const x = this.W * (1 - i / 240); const lo = (x - this.cx) / this.K; const f = Math.abs(((lo + Math.PI) % TAU + TAU) % TAU - Math.PI); g.lineTo(x, this.cy - fn(f) * this.K); }
    g.closePath(); g.fillStyle = col; g.fill(); }
}
function sample(pts, n, close) {
  const c = new THREE.CatmullRomCurve3(pts.map(([a, b]) => new THREE.Vector3(a, b, 0)), !!close);
  return Array.from({ length: n + 1 }, (_, i) => { const p = c.getPoint(i / n); return [p.x, p.y]; });
}
function skinCanvas(W, base, seed) {
  const c = document.createElement('canvas'); c.width = W; c.height = W / 2; const g = c.getContext('2d');
  const N = noise2(seed); const cb = hex(base); const H = W / 2; const img = g.createImageData(W, H); const d = img.data;
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
    const gr = Math.pow(Math.abs(Math.sin((y / H * 30 + N.fbm(x / W * 3, y / H * 8, 3) * 4) * Math.PI)), 12);
    const k = 1 - 0.05 * gr + (N.fbm(x / W * 20, y / H * 10, 2) - 0.5) * 0.045;
    const i = (y * W + x) * 4; d[i] = cb[0] * k; d[i + 1] = cb[1] * k; d[i + 2] = cb[2] * k; d[i + 3] = 255;
  }
  g.putImageData(img, 0, 0); return c;
}
function texFrom(c) { const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8; return t; }

// ---- the man: dark hair swept back from a high forehead, heavy straight brows, smiling eyes, a wide closed smile
const HAIR = '#2b1e16', MSKIN = '#dcb48a';
function manHairline(f) { // f = |lon| 0..PI
  return f < 0.62 ? 0.84 + 0.17 * sm(0.1, 0.5, f) - 0.02 * sm(0.5, 0.62, f) : f < 1.2 ? 0.99 - 0.66 * sm(0.62, 1.2, f) : f < 1.45 ? 0.33 - 0.38 * sm(1.2, 1.45, f) : -0.05 - 0.25 * sm(1.45, 2.3, f);
}
export function manFaceCanvas(mood = 'smile', W = 2048) {
  const c = skinCanvas(W, MSKIN, 71); const g = c.getContext('2d'); const F = new Face(g, W);
  for (const s of [-1, 1]) F.glow(0.48 * s, -0.2, 0.2, 'rgba(205,95,60,0.18)');             // warm cheeks
  F.glow(0, -0.72, 0.16, 'rgba(120,70,50,0.10)');                                             // a hint of shadow under the lip
  F.region((f) => manHairline(f) - 0.045, HAIR);
  for (const s of [-1, 1]) {
    const ex = 0.31 * s, ey = 0.2, E = (dx, dy) => [ex + dx * s, ey + dy];               // dx > 0 is outward
    // a smiling almond: the lower lid lifted, a dark iris tucked under the upper lid, a catch-light
    F.shape([E(-0.15, -0.004), E(-0.03, 0.056), E(0.09, 0.05), E(0.158, 0.0), E(0.06, -0.022), E(-0.08, -0.022)], '#e2d8c6');
    F.blob(ex - 0.006 * s, ey + 0.01, 0.052, 0.054, '#4a2f1c'); F.blob(ex - 0.006 * s, ey + 0.01, 0.027, 0.029, '#140b07');
    F.blob(ex - 0.026 * s, ey + 0.03, 0.014, 0.014, 'rgba(255,255,255,0.95)');
    F.shape([E(-0.17, -0.008), E(-0.07, -0.024), E(0.07, -0.024), E(0.17, -0.004), E(0.17, -0.13), E(-0.17, -0.13)], MSKIN);
    F.shape([E(-0.17, 0.0), E(-0.03, 0.06), E(0.09, 0.054), E(0.17, 0.004), E(0.17, 0.13), E(-0.17, 0.13)], MSKIN);
    F.line([E(-0.16, -0.004), E(-0.03, 0.058), E(0.09, 0.052), E(0.175, 0.002), E(0.2, -0.008)], '#2a1a12', 0.026);
    F.line([E(-0.12, 0.09), E(0.0, 0.102), E(0.14, 0.066)], 'rgba(95,55,35,0.4)', 0.009);
    F.line([E(-0.11, -0.05), E(0.02, -0.062), E(0.13, -0.042)], 'rgba(95,55,35,0.45)', 0.009);
    F.line([E(0.205, -0.02), E(0.25, -0.06)], 'rgba(90,50,32,0.4)', 0.008);
    F.taper([[0.085 * s, 0.37], [0.3 * s, 0.405], [0.57 * s, 0.375]], HAIR, 0.06, 0.078, 0.3);   // heavy, nearly straight brows
  }
  const my = -0.42;
  if (mood === 'grin') {
    F.shape([[-0.35, my + 0.07], [-0.18, my - 0.02], [0, my - 0.045], [0.18, my - 0.02], [0.35, my + 0.07], [0.2, my - 0.13], [0, my - 0.17], [-0.2, my - 0.13]], '#4a1a14');
    F.shape([[-0.31, my + 0.055], [-0.16, my - 0.018], [0, my - 0.04], [0.16, my - 0.018], [0.31, my + 0.055], [0.16, my - 0.07], [0, my - 0.085], [-0.16, my - 0.07]], '#f6efe2');
    F.line([[-0.355, my + 0.075], [-0.18, my - 0.022], [0, my - 0.046], [0.18, my - 0.022], [0.355, my + 0.075]], '#5a2218', 0.016);
  } else {
    F.glow(0, my - 0.075, 0.13, 'rgba(150,70,50,0.22)');                                                    // lower lip
    const lipL = [[-0.33, my + 0.055], [-0.2, my - 0.02], [0, my - 0.04], [0.2, my - 0.012], [0.335, my + 0.082]];
    F.taper(lipL.slice(0, 3).reverse(), '#5a2419', 0.03, 0.03, 0.05); F.taper(lipL.slice(2), '#5a2419', 0.03, 0.03, 0.05);
    for (const s of [-1, 1]) { const lift = s > 0 ? 0.025 : 0; F.line([[0.345 * s, my + 0.1 + lift], [0.372 * s, my + 0.05 + lift], [0.356 * s, my + lift]], 'rgba(110,55,38,0.5)', 0.011); }   // corner creases
  }
  return c;
}

// ---- the seeress: pale and serene; eyes closed (or open, pale blue); blue seer's marks under the eyes
const SSKIN = '#e8d2b6';
export function seerFaceCanvas(open = false, W = 2048) {
  const c = skinCanvas(W, SSKIN, 72); const g = c.getContext('2d'); const F = new Face(g, W);
  for (const s of [-1, 1]) F.glow(0.45 * s, -0.2, 0.18, 'rgba(200,110,90,0.15)');
  F.region(() => 0.72, '#d8d2c6');
  for (const s of [-1, 1]) {
    const ex = 0.3 * s, ey = 0.16, E = (dx, dy) => [ex + dx * s, ey + dy];
    F.taper([[0.1 * s, 0.35], [0.3 * s, 0.38], [0.52 * s, 0.34]], '#a99f92', 0.03, 0.04, 0.4);
    if (open) {
      F.shape([E(-0.15, 0.0), E(-0.04, 0.04), E(0.08, 0.036), E(0.15, 0.002), E(0.05, -0.03), E(-0.08, -0.03)], '#e0d8ca');
      F.blob(ex - 0.005 * s, ey + 0.0, 0.04, 0.042, '#9dbfd4'); F.blob(ex - 0.005 * s, ey + 0.0, 0.017, 0.018, '#0b1622'); F.blob(ex - 0.02 * s, ey + 0.016, 0.009, 0.009, '#ffffff');
      F.shape([E(-0.17, 0.004), E(-0.04, 0.045), E(0.08, 0.04), E(0.17, 0.006), E(0.17, 0.12), E(-0.17, 0.12)], SSKIN);
      F.line([E(-0.16, 0.002), E(-0.04, 0.043), E(0.085, 0.038), E(0.165, 0.004)], '#2a2420', 0.02);
      F.line([E(-0.11, 0.07), E(0.0, 0.08), E(0.12, 0.06)], 'rgba(90,70,60,0.45)', 0.009);
    } else {
      F.line([E(-0.15, 0.01), E(-0.05, -0.03), E(0.07, -0.03), E(0.15, 0.01)], '#3a2c24', 0.017);
      for (let k = 0; k < 5; k++) { const a = -0.1 + k * 0.05; F.line([E(a, -0.026), E(a + 0.008, -0.06)], '#3a2c24', 0.006); }
    }
    for (let k = 0; k < 3; k++) F.line([E(-0.05 + k * 0.05, -0.11), E(-0.05 + k * 0.05, -0.23 + k * 0.012)], 'rgba(40,90,170,0.85)', 0.012);
  }
  F.line([[-0.15, -0.42], [0, -0.445], [0.15, -0.42]], '#8a3a32', 0.02);
  F.line([[-0.1, -0.47], [0, -0.48], [0.1, -0.47]], 'rgba(150,70,60,0.5)', 0.016);
  return c;
}

// ---- a Viking: ruddy cheeks, bushy brows; hair and beard painted under their carved shells so no seam shows
const VSKIN = '#d8a882';
export const VBEARD = (f) => f < 0.22 ? -0.21 : f < 0.6 ? -0.21 - 0.1 * sm(0.22, 0.6, f) : f < 1.45 ? -0.31 + 0.36 * sm(0.75, 1.42, f) : 0.05;
export const VHAIR = {
  long: (f) => f < 1.0 ? 0.76 - 0.12 * sm(0.5, 1.0, f) : f < 1.75 ? 0.64 - 1.0 * sm(1.0, 1.75, f) : -0.36 - 0.14 * sm(1.75, 2.4, f),
  tied: (f) => f < 0.45 ? 0.8 : f < 1.3 ? 0.8 - 0.68 * sm(0.45, 1.3, f) : f < 1.7 ? 0.12 - 0.42 * sm(1.3, 1.7, f) : -0.3,
  helmet: (f) => f < 1.3 ? 0.5 : 0.5 - 0.6 * sm(1.3, 1.8, f),
};
const fringeShow = (la, f) => Math.min(la + 0.32, 0.5 - la, f - 1.15);     // bald on top, a fringe round the back
export function vikingFaceCanvas(beard = '#a8481e', hair = 'long', W = 1024) {
  const c = skinCanvas(W, VSKIN, 73); const g = c.getContext('2d'); const F = new Face(g, W);
  for (const s of [-1, 1]) F.glow(0.45 * s, -0.08, 0.22, 'rgba(210,80,50,0.32)');
  F.glow(0, 0.95, 0.5, 'rgba(255,190,150,0.10)');
  if (hair === 'bald') { const im = g.getImageData(0, 0, W, W / 2), d = im.data; const cb = hex(beard);
    for (let y = 0; y < W / 2; y++) for (let x = 0; x < W; x++) { const lo = (x - F.cx) / F.K, la = (F.cy - y) / F.K; const f = Math.abs(((lo + Math.PI) % TAU + TAU) % TAU - Math.PI);
      if (fringeShow(la, f) > -0.025) { const i = (y * W + x) * 4; d[i] = cb[0]; d[i + 1] = cb[1]; d[i + 2] = cb[2]; } }
    g.putImageData(im, 0, 0);
  } else F.region((f) => VHAIR[hair](f) - 0.02, beard);
  F.region((f) => VBEARD(f) + 0.025, beard, true);
  for (const s of [-1, 1]) {
    const ex = 0.3 * s, ey = 0.17, E = (dx, dy) => [ex + dx * s, ey + dy];
    F.taper([[0.07 * s, 0.33], [0.3 * s, 0.39], [0.56 * s, 0.35]], beard, 0.075, 0.095, 0.4);
    F.shape([E(-0.16, 0), E(-0.02, 0.075), E(0.16, 0), E(0, -0.05)], '#d2c6b2');
    F.blob(ex, ey + 0.008, 0.056, 0.06, '#3a5a7a'); F.blob(ex, ey + 0.008, 0.028, 0.03, '#0c0c10'); F.blob(ex - 0.02 * s, ey + 0.03, 0.014, 0.014, '#fff');
    F.line([E(-0.17, 0), E(-0.02, 0.082), E(0.17, 0)], '#2a1a12', 0.022);
  }
  return c;
}

// ---------------------------------------------------------------- sculpted heads
// A sphere is sculpted in (lat, lon): `sculpt` adds radial relief (nose, brow, cheekbones, lips, chin) and `base`
// bends the whole shape (jaw, crown); then it is scaled by R. Hair, beards and hoods are shells built from the same
// surface, pushed out where they show and tucked under the skin where they don't, so they always hug the head.
const toLL = (v) => [Math.asin(clamp(v.y, -1, 1)), Math.atan2(v.x, v.z)];
function headGeo(R, base, sculpt, seg, rings, shellFn = null) {
  const geo = new THREE.SphereGeometry(1, seg, rings); const p = geo.attributes.position;
  for (let i = 0; i < p.count; i++) {
    _v.fromBufferAttribute(p, i); const [la, lo] = toLL(_v);
    let k = 1 + sculpt(la, lo), dy = 0, dz = 0; if (shellFn) { const r = shellFn(la, lo); if (Array.isArray(r)) { k *= 1 + r[0]; dy = r[1] || 0; dz = r[2] || 0; } else k *= 1 + r; }
    _v.multiplyScalar(k); base(_v); _v.y += dy; _v.z += dz; p.setXYZ(i, _v.x * R[0], _v.y * R[1], _v.z * R[2]);
  }
  geo.computeVertexNormals(); weld(geo); return geo;
}
function headPoint(R, base, sculpt, la, lo, k = 1) {
  const v = new THREE.Vector3(Math.cos(la) * Math.sin(lo), Math.sin(la), Math.cos(la) * Math.cos(lo)).multiplyScalar((1 + sculpt(la, lo)) * k);
  base(v); return new THREE.Vector3(v.x * R[0], v.y * R[1], v.z * R[2]);
}
// average the normals of vertices that share a position (sphere seams and poles), so smooth heads have no seam line
function weld(geo) {
  const p = geo.attributes.position, n = geo.attributes.normal, map = new Map(), t = new THREE.Vector3();
  for (let i = 0; i < p.count; i++) { const k = `${p.getX(i).toFixed(5)},${p.getY(i).toFixed(5)},${p.getZ(i).toFixed(5)}`; let a = map.get(k); if (!a) map.set(k, a = []); a.push(i); }
  for (const ids of map.values()) { if (ids.length < 2) continue; _v.set(0, 0, 0); for (const i of ids) _v.add(t.fromBufferAttribute(n, i)); _v.normalize(); for (const i of ids) n.setXYZ(i, _v.x, _v.y, _v.z); }
  n.needsUpdate = true;
}
// a generic face, scaled per character: nose length/height, brow, cheekbones, lips, chin
function faceSculpt({ nose = 0.17, noseW = 0.05, noseTip = -0.06, brow = 0.03, socket = 0.028, cheek = 0.025, lips = 0.02, chin = 0.05, ey = 0.2, ex = 0.31, my = -0.42 } = {}) {
  return (la, lo) => {
    const a = Math.abs(lo); let d = 0;
    d += brow * gauss(la - (ey + 0.16), 0.07) * sm(0.8, 0.35, a);
    d -= socket * gauss(la - ey, 0.075) * gauss(a - ex, 0.11);
    if (la < ey + 0.12) {
      const t = clamp((ey + 0.12 - la) / (ey + 0.12 - noseTip), 0, 1);
      const hgt = la > noseTip ? 0.25 * nose + 0.75 * nose * Math.pow(t, 1.5) : nose * gauss(la - noseTip, 0.045);
      d += hgt * gauss(lo, noseW * (0.85 + 0.6 * t));
      d += 0.3 * nose * gauss(la - noseTip + 0.01, 0.035) * gauss(a - noseW * 1.9, 0.03);      // nostril wings
    }
    d += cheek * gauss(la - (ey - 0.17), 0.1) * gauss(a - 0.52, 0.14);
    d += lips * gauss(la - (my + 0.04), 0.035) * gauss(lo, 0.2) + lips * 0.9 * gauss(la - (my - 0.05), 0.03) * gauss(lo, 0.16) - lips * 0.5 * gauss(la - my, 0.012) * gauss(lo, 0.24);
    d += chin * gauss(la - (my - 0.3), 0.1) * gauss(lo, 0.26);
    return d;
  };
}
const SCULPT = {
  man: faceSculpt({ nose: 0.18, noseW: 0.05, brow: 0.04, cheek: 0.015, lips: 0.022, chin: 0.08 }),
  seer: faceSculpt({ nose: 0.12, noseW: 0.042, brow: 0.02, socket: 0.03, cheek: 0.035, lips: 0.018, chin: 0.03, ey: 0.16, ex: 0.3, my: -0.42 }),
  viking: faceSculpt({ nose: 0.22, noseW: 0.06, brow: 0.05, socket: 0.035, cheek: 0.03, lips: 0.0, chin: 0.0, ey: 0.17, ex: 0.3 }),
};
const BASE = {
  man: (v) => { const k = sm(-0.1, -0.7, v.y); v.x *= 1 + 0.2 * k - 0.04 * gauss(v.y + 0.05, 0.25) + 0.08 * sm(0.3, 0.9, v.y); v.z *= 1 + 0.04 * k; if (v.y < -0.76) v.y = -0.76 + (v.y + 0.76) * 0.4; if (v.y > 0.55) v.y = 0.55 + (v.y - 0.55) * 0.78; if (v.z > 0) v.z *= 0.93; },
  seer: (v) => { const k = sm(0.1, -0.9, v.y); v.x *= 1 - 0.16 * k; if (v.z > 0) v.z *= 0.95; },
  viking: (v) => { const k = sm(0.0, -0.8, v.y); v.x *= 1 + 0.1 * k + 0.05 * sm(0.35, 0.9, v.y); if (v.z > 0) v.z *= 0.93; },
};
// shell offsets: hidden (tucked under the skin) on one side of a boundary, raised on the other, blended over `soft` radians
const tuck = (show, raised, soft = 0.03) => -0.05 + (raised + 0.05) * sm(-soft, 0, show);
// ---------------------------------------------------------------- materials (built once)
let M = null;
export function mats(env) {
  if (M) return M;
  M = {
    env,
    hair: paint(HAIR, { seed: 33, grain: 0.4, streak: 0.12, vertical: true, w: 512, repeat: [4, 1], smooth: true }),
    trousers: paint('#25262c', { seed: 43 }), boot: paint('#16130f', { seed: 44, grain: 0.05 }), tee: paint('#121214', { seed: 42, grain: 0.04 }),
    blazer: paint('#2f3138', { seed: 40 }),
    robe: paint('#21357e', { seed: 45, streak: 0.07 }),
    hood: paint('#1a1612', { seed: 46, grain: 0.2, streak: 0.15, side: THREE.DoubleSide }), hoodIn: paint('#0e0c0a', { seed: 56, side: THREE.BackSide }),
    fur: paint('#d9d2c4', { seed: 47, grain: 0.3, streak: 0.2, vertical: true, repeat: [6, 1] }), furDark: paint('#5e4c3a', { seed: 48, grain: 0.35, streak: 0.2, vertical: true, repeat: [6, 1] }),
    leather: paint('#5a3a22', { seed: 49 }), belt: paint('#3a2416', { seed: 50 }),
    iron: metal(0x9a9ea6, env, { metalness: 0.55, roughness: 0.4, env: 1.4 }), ironDark: metal(0x5a5c62, env, { metalness: 0.5, roughness: 0.5, env: 1.0 }),
    brass: metal(0xd6aa58, env, { metalness: 1, roughness: 0.28, env: 1.4 }),
    staff: paint('#4a3020', { seed: 52, grain: 0.25 }), glove: paint('#6e5e50', { seed: 57, grain: 0.04, streak: 0.06, smooth: true }),
    skinPlain: paint(MSKIN, { seed: 53, grain: 0.05, smooth: true }), seerSkin: paint(SSKIN, { seed: 54, grain: 0.05, smooth: true }), vikSkin: paint(VSKIN, { seed: 55, grain: 0.05, smooth: true }),
  };
  // the blazer, painted: black tee in the V, lapels with a notch, one button, pocket flaps (front is u = 0.5)
  M.jacket = paint('#2f3138', { seed: 40, w: 512, h: 512, draw: (g, w, h) => {
    const X = (u) => u * w, Y = (v) => (1 - v) * h; const V = 0.34;
    g.fillStyle = '#121214'; g.beginPath(); g.moveTo(X(0.5 - 0.07), Y(1)); g.lineTo(X(0.5 + 0.07), Y(1)); g.lineTo(X(0.5), Y(V)); g.closePath(); g.fill();
    for (const s of [-1, 1]) {
      g.fillStyle = '#3d4049'; g.beginPath(); g.moveTo(X(0.5 + 0.07 * s), Y(1)); g.lineTo(X(0.5 + 0.11 * s), Y(0.97)); g.lineTo(X(0.5 + 0.105 * s), Y(0.84));
      g.lineTo(X(0.5 + 0.135 * s), Y(0.8)); g.lineTo(X(0.5 + 0.06 * s), Y(0.55)); g.lineTo(X(0.5), Y(V)); g.closePath(); g.fill();
      g.strokeStyle = 'rgba(0,0,0,0.55)'; g.lineWidth = 3; g.stroke();
      g.strokeStyle = 'rgba(0,0,0,0.45)'; g.lineWidth = 3; g.beginPath(); g.moveTo(X(0.5 + 0.1 * s), Y(0.16)); g.lineTo(X(0.5 + 0.2 * s), Y(0.165)); g.stroke();
    }
    g.strokeStyle = 'rgba(0,0,0,0.4)'; g.lineWidth = 3; g.beginPath(); g.moveTo(X(0.5 + 0.1), Y(0.66)); g.lineTo(X(0.5 + 0.17), Y(0.665)); g.stroke();
    g.beginPath(); g.moveTo(X(0.5), Y(V)); g.lineTo(X(0.5), Y(0)); g.stroke();
    g.fillStyle = '#121214'; g.beginPath(); g.arc(X(0.505), Y(V - 0.04), 6, 0, TAU); g.fill();
    const mx = X(0.5), my = Y(0.86); g.fillStyle = '#b8462a'; g.beginPath(); g.arc(mx, my, 9, 0, TAU); g.fill();
    g.strokeStyle = '#d9b25f'; g.lineWidth = 2; g.beginPath(); g.ellipse(mx, my, 17, 6, -0.35, 0, TAU); g.stroke();
  } });
  M.mail = clay(0xffffff, { flatShading: true, map: canvasTex(128, 128, (g, w, h) => { g.fillStyle = '#25272b'; g.fillRect(0, 0, w, h);
    for (let row = 0; row < 9; row++) for (let col = 0; col < 9; col++) { const x = col * 16 + (row % 2) * 8, y = row * 16;
      g.strokeStyle = '#a2a6ae'; g.lineWidth = 3; g.beginPath(); g.ellipse(x, y, 6, 5, 0, 0, TAU); g.stroke(); } }, { repeat: [14, 2] }) });
  return M;
}
const faceMat = (canvas) => clay(0xffffff, { map: texFrom(canvas) });
// a tunic with woven bands at the neck and hem
export function tunicMat(color, trim, trim2, seed) {
  return paint(color, { seed, w: 512, h: 512, draw: (g, w, h) => { band(g, w, h * 0.035, h * 0.09, trim, trim2); band(g, w, h * 0.885, h * 0.94, trim, trim2); } });
}

// ---------------------------------------------------------------- the rig
function limb(mat, r, seg = 9) { const g = new THREE.Group(); const c = new THREE.Mesh(new THREE.CylinderGeometry(1, 0.92, 1, seg, 1, true), mat); c.scale.set(r, 1, r); g.add(c); g.userData = { c }; return g; }
function placeLimb(l, a, b) { const len = a.distanceTo(b); l.position.copy(a).add(b).multiplyScalar(0.5); _v.copy(b).sub(a).normalize(); l.quaternion.setFromUnitVectors(UP, _v); l.userData.c.scale.y = Math.max(0.001, len); }
export function knob(mat, r, sx = 1, sy = 1, sz = 1, seg = 10, rings = 7) { const m = new THREE.Mesh(new THREE.SphereGeometry(1, seg, rings), mat); m.scale.set(r * sx, r * sy, r * sz); return m; }
function ik(S, T, a, b, pole, outE) {
  const d = Math.min(a + b - 1e-4, Math.max(Math.abs(a - b) + 1e-4, S.distanceTo(T)));
  const dir = _v.copy(T).sub(S).normalize().clone();
  const cosA = (a * a + d * d - b * b) / (2 * a * d); const sinA = Math.sqrt(Math.max(0, 1 - cosA * cosA));
  const p = pole.clone().sub(dir.clone().multiplyScalar(pole.dot(dir))).normalize();
  outE.copy(S).add(dir.multiplyScalar(a * cosA)).add(p.multiplyScalar(a * sinA)); return d;
}
export function shadows(obj, cast = true, receive = true) { obj.traverse((o) => { if (o.isMesh) { o.castShadow = cast; o.receiveShadow = receive; } }); return obj; }

export class Puppet {
  constructor(m, o) {
    this.m = m; this.o = o; this.root = new THREE.Group(); this.body = new THREE.Group(); this.root.add(this.body);
    this.headG = new THREE.Group(); this.body.add(this.headG);
    this.shoulderY = o.shoulderY ?? 0.48; this.shoulderX = o.shoulderX ?? 0.23; this.upper = o.upper ?? 0.27; this.fore = o.fore ?? 0.25;
    const ar = o.armR ?? 0.068;
    this.arms = [-1, 1].map((s) => {
      const up = limb(o.sleeve, ar), fo = limb(o.sleeve, ar * 0.9), sh = knob(o.sleeve, ar * 1.22), el = knob(o.sleeve, ar * 0.98);
      const hand = this.makeHand(s, o.handM ?? m.skinPlain); [up, fo, sh, el, hand].forEach((x) => this.body.add(x));
      return { s, up, fo, sh, el, hand, S: new THREE.Vector3(this.shoulderX * s, this.shoulderY, 0), E: new THREE.Vector3() };
    });
    this.legs = [-1, 1].map((s) => { const th = limb(o.legM, 0.088), sh = limb(o.legM, 0.072), kn = knob(o.legM, 0.084), hp = knob(o.legM, 0.098);
      const foot = knob(o.footM, 0.064, 1, 0.75, 1.75, 8, 6); [th, sh, kn, hp, foot].forEach((x) => this.body.add(x)); return { s, th, sh, kn, hp, foot }; });
  }
  makeHand(s, mm) { // a carved mitten with a thumb
    const g = new THREE.Group(); const palm = knob(mm, 0.052, 0.95, 1.2, 0.68, 10, 8); palm.position.y = 0.042; g.add(palm);
    const th = knob(mm, 0.022, 1, 1.7, 1, 8, 6); th.position.set(-0.04 * s, 0.036, 0.014); th.rotation.z = 0.5 * s; g.add(th); return g;
  }
  /** p: seated, lean, turn, tilt, headYaw/Pitch/Roll, hands (body space) or handsW (world points, null = use hands),
   *  look (world point the head turns to; lookK blends it in), handRoll */
  pose(p = {}) {
    const seated = p.seated !== false; this.seated = seated;
    this.body.position.y = seated ? 0.48 : 0.85; this.body.rotation.set(p.lean || 0, p.turn || 0, p.tilt || 0);
    let hy = p.headYaw || 0, hp = p.headPitch || 0;
    if (p.look || p.handsW) this.root.updateMatrixWorld(true);
    if (p.look) { const L = this.body.worldToLocal(new THREE.Vector3(...p.look)).sub(this.headG.position).sub(new THREE.Vector3(0, 0.16, 0));
      const k = p.lookK ?? 1; const yaw = Math.max(-1.15, Math.min(1.15, Math.atan2(L.x, L.z))), pit = Math.max(-0.55, Math.min(0.5, -Math.atan2(L.y, Math.hypot(L.x, L.z))));
      hy = hy * (1 - k) + yaw * k; hp = hp * (1 - k) + pit * k; }
    this.headG.rotation.set(hp, hy, p.headRoll || 0, 'YXZ');
    const hands = p.hands || [[-0.2, 0.3, 0.36], [0.2, 0.3, 0.36]];
    this.arms.forEach((a, k) => {
      const T = (p.handsW && p.handsW[k]) ? this.body.worldToLocal(new THREE.Vector3(...p.handsW[k])) : new THREE.Vector3(...hands[k]);
      const pole = new THREE.Vector3(0.7 * a.s, -1, -0.45);
      ik(a.S, T, this.upper, this.fore, pole, a.E);
      const H = a.E.clone().add(T.clone().sub(a.E).normalize().multiplyScalar(this.fore));
      placeLimb(a.up, a.S, a.E); placeLimb(a.fo, a.E, H); a.sh.position.copy(a.S); a.el.position.copy(a.E);
      a.hand.position.copy(H); const dir = T.clone().sub(a.E).normalize(); a.hand.quaternion.setFromUnitVectors(UP, dir);
      if (p.handRoll) a.hand.rotateY(p.handRoll[k] || 0);
    });
    this.legs.forEach((l) => { const hip = new THREE.Vector3(0.095 * l.s, 0.02, 0);
      const knee = seated ? new THREE.Vector3(0.11 * l.s, 0.0, 0.4) : new THREE.Vector3(0.1 * l.s, -0.38, 0.03);
      const ankle = seated ? new THREE.Vector3(0.12 * l.s, -0.42, 0.44) : new THREE.Vector3(0.105 * l.s, -0.78, 0);
      if (p.feet) { const f = p.feet[l.s < 0 ? 0 : 1] || 0; knee.y += f * 0.08; ankle.y += f * 0.09; ankle.z -= f * 0.02; }
      placeLimb(l.th, hip, knee); placeLimb(l.sh, knee, ankle); l.kn.position.copy(knee); l.hp.position.copy(hip); l.foot.position.copy(ankle).add(new THREE.Vector3(0, -0.028, 0.06)); });
    return this;
  }
  handWorld(k) { this.root.updateMatrixWorld(true); return this.arms[k].hand.localToWorld(new THREE.Vector3(0, 0.04, 0)); }
  headWorld() { this.root.updateMatrixWorld(true); return this.headG.localToWorld(new THREE.Vector3(0, 0.17, 0)); }
}

// ---------------------------------------------------------------- the man with the rocket
export class TechKing extends Puppet {
  constructor(m) {
    super(m, { sleeve: m.blazer, legM: m.trousers, footM: m.boot, shoulderX: 0.25, shoulderY: 0.49, armR: 0.074 });
    const b = this.body;
    const torso = new THREE.Mesh(lathe([[0, 0], [0.18, 0], [0.2, 0.07], [0.205, 0.22], [0.23, 0.38], [0.255, 0.46], [0.22, 0.53], [0.11, 0.565], [0, 0.57]], 14), m.jacket); torso.scale.z = 0.66; b.add(torso);
    const neck = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.086, 0.12, 14), m.skinPlain); neck.position.y = 0.6; b.add(neck);
    const collar = new THREE.Mesh(new THREE.TorusGeometry(0.088, 0.017, 6, 18), m.tee); collar.position.set(0, 0.57, 0.006); collar.rotation.x = Math.PI / 2 - 0.15; b.add(collar);
    const h = this.headG; h.position.y = 0.6;
    const R = [0.148, 0.196, 0.158]; this.faces = { smile: faceMat(manFaceCanvas('smile')), grin: faceMat(manFaceCanvas('grin')) };
    const hy = 0.17;
    this.head = new THREE.Mesh(headGeo(R, BASE.man, SCULPT.man, 160, 100), this.faces.smile); this.head.position.y = hy; h.add(this.head);
    // hair: lifted above the hairline, with volume swept up and back from the front
    const hairFn = (la, lo) => { const above = la - manHairline(Math.abs(lo)); return tuck(above, 0.065 + 0.2 * gauss(la - 0.97, 0.17) * gauss(lo, 0.75) * sm(0, 0.12, above) + 0.05 * sm(1.0, 1.5, la), 0.06); };
    const hair = new THREE.Mesh(headGeo(R, BASE.man, SCULPT.man, 180, 120, hairFn), m.hair); hair.position.y = hy; h.add(hair);
    for (const s of [-1, 1]) { const ear = knob(m.skinPlain, 1, 0.022, 0.044, 0.032, 12, 9); ear.position.set(0.143 * s, hy + 0.012, -0.008); h.add(ear); }
    this.pose({});
  }
  setFace(k) { this.head.material = this.faces[k]; }
}

// ---------------------------------------------------------------- the seeress (the saga's völva: blue cloak set with stones, glass beads,
// a black lambskin hood lined with white catskin, catskin gloves, a staff with a brass knob)
export class Seeress extends Puppet {
  constructor(m) {
    super(m, { sleeve: m.robe, legM: m.robe, footM: m.boot, handM: m.glove, shoulderX: 0.2, shoulderY: 0.45, armR: 0.068, upper: 0.31, fore: 0.29 });
    for (const a of this.arms) { const cuff = new THREE.Mesh(new THREE.TorusGeometry(0.05, 0.02, 8, 18), m.fur); cuff.rotation.x = Math.PI / 2; cuff.position.y = 0.0; a.hand.add(cuff); }
    const b = this.body;
    const robe = new THREE.Mesh(lathe([[0, -0.02], [0.24, -0.02], [0.23, 0.08], [0.2, 0.22], [0.195, 0.36], [0.215, 0.45], [0.16, 0.53], [0.07, 0.57], [0, 0.575]], 12), m.robe); robe.scale.z = 0.78; b.add(robe);
    const gown = new THREE.Mesh(lathe([[0.0, -0.47], [0.37, -0.47], [0.33, -0.25], [0.27, 0.0], [0.2, 0.1], [0.0, 0.1]], 14), m.robe); gown.position.set(0, 0, 0.17); gown.scale.set(1, 1, 1.12); b.add(gown);
    this.legs.forEach((l) => { l.th.visible = l.sh.visible = l.kn.visible = l.hp.visible = false; });
    const blue = new THREE.MeshStandardMaterial({ color: 0x4f9ad8, metalness: 0.2, roughness: 0.12, envMap: m.env, envMapIntensity: 1.5, emissive: 0x0a1a2a, flatShading: true });
    const stoneM = [m.brass, blue];
    for (let k = 0; k < 7; k++) { const st = knob(stoneM[k % 2], 0.011, 1, 1, 0.7, 6, 4); st.position.set(0, 0.1 + k * 0.055, 0.16 - Math.max(0, k - 4) * 0.012); b.add(st); }
    for (let k = 0; k < 14; k++) { const a = TAU * k / 14; const st = knob(stoneM[k % 2], 0.013, 1, 1, 0.7, 6, 4); st.position.set(Math.sin(a) * 0.372, -0.42, 0.17 + Math.cos(a) * 0.372 * 1.12); b.add(st); }
    const beadCols = [0xd89a3a, 0x3f7fb8, 0x5a9a5a, 0xc8c0a8, 0x9a3a2a];
    for (let k = 0; k <= 16; k++) { const a = Math.PI * (0.15 + 0.7 * k / 16); const bd = knob(new THREE.MeshStandardMaterial({ color: beadCols[k % 5], roughness: 0.15, metalness: 0.1, envMap: m.env, envMapIntensity: 1.5 }), 0.013, 1, 1, 1, 8, 6);
      bd.position.set(Math.cos(a) * 0.11, 0.49 - Math.sin(a) * 0.08, 0.105 + Math.sin(a) * 0.035); b.add(bd); }
    const neck = new THREE.Mesh(new THREE.CylinderGeometry(0.056, 0.062, 0.1, 12), m.seerSkin); neck.position.y = 0.58; b.add(neck);
    const h = this.headG; h.position.y = 0.57;
    const R = [0.128, 0.172, 0.142]; this.faces = { closed: faceMat(seerFaceCanvas(false)), open: faceMat(seerFaceCanvas(true)) };
    const hy = 0.16;
    this.head = new THREE.Mesh(headGeo(R, BASE.seer, SCULPT.seer, 160, 100), this.faces.closed); this.head.position.y = hy; h.add(this.head);
    // the hood: a black shell over everything but the face oval; white fur rims the opening; a cowl falls to the shoulders
    const OV = { a: 0.74, b: 0.64, c: -0.17 }; const oval = (la, lo) => Math.hypot(lo / OV.a, (la - OV.c) / OV.b);
    const hoodFn = (la, lo) => tuck(oval(la, lo) - 1, 0.15 + 0.08 * sm(0.7, 1.45, la), 0.05);
    const hood = new THREE.Mesh(headGeo(R, BASE.seer, SCULPT.seer, 100, 70, hoodFn), m.hood); hood.position.y = hy; h.add(hood);
    const ring = []; for (let i = 0; i < 96; i++) { const t = i / 96 * TAU; ring.push(headPoint(R, BASE.seer, SCULPT.seer, OV.c + OV.b * Math.cos(t), OV.a * Math.sin(t), 1.1)); }
    const ruff = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(ring, true), 120, 0.024, 8, true), m.fur); ruff.position.y = hy; h.add(ruff);
    const cowl = new THREE.Mesh(lathe([[0.3, -0.2], [0.28, -0.14], [0.21, -0.08], [0.14, -0.035], [0.1, 0.01], [0.0, 0.03]], 20), m.hood); cowl.scale.z = 0.88; h.add(cowl);
    this.pose({});
  }
  setFace(k) { this.head.material = this.faces[k]; }
}
export function makeStaff(m) {
  const g = new THREE.Group();
  const shaft = new THREE.Mesh(new THREE.CylinderGeometry(0.016, 0.02, 1.45, 7), m.staff); shaft.position.y = 0.725; g.add(shaft);
  const k0 = knob(m.brass, 0.042, 1, 0.9, 1, 12, 9); k0.position.y = 1.47; g.add(k0);
  for (let k = 0; k < 4; k++) { const r = new THREE.Mesh(new THREE.TorusGeometry(0.019, 0.005, 4, 10), m.brass); r.rotation.x = Math.PI / 2; r.position.y = 1.2 + k * 0.05; g.add(r); }
  return g;
}

// ---------------------------------------------------------------- Vikings: bare heads at the feast (a helmet for the door guards),
// carved hair and beards as shells, banded tunics, fur capelets
const _vfaces = {};
export class Viking extends Puppet {
  constructor(m, { beard = '#a8481e', hair = 'long', beardStyle = 'long', tunic = '#4a5a3a', trim = ['#c9a23a', '#6a1a14'], cloak = '#2a2622', fur = 'dark', bulk = 1, seed = 1, lod = 1 } = {}) {
    const SG = Math.round(110 * lod), RG = Math.round(72 * lod);
    const tunicM = tunicMat(tunic, trim[0], trim[1], 60 + seed), legM = paint('#3a342c', { seed: 61 + seed });
    super(m, { sleeve: paint(tunic, { seed: 62 + seed }), legM, footM: m.leather, handM: m.leather, shoulderX: 0.255, shoulderY: 0.47, armR: 0.08 });
    const b = this.body;
    const torso = new THREE.Mesh(lathe([[0, -0.06], [0.215, -0.06], [0.24, 0.08], [0.258, 0.24], [0.252, 0.38], [0.245, 0.46], [0.19, 0.53], [0.09, 0.565], [0, 0.57]], 12), tunicM); torso.scale.z = 0.8; b.add(torso);
    const belt = new THREE.Mesh(new THREE.TorusGeometry(0.245, 0.02, 4, 14), m.belt); belt.rotation.x = Math.PI / 2; belt.scale.y = 0.82; belt.position.y = 0.14; b.add(belt);
    const buckle = new THREE.Mesh(new THREE.BoxGeometry(0.05, 0.045, 0.012), m.brass); buckle.position.set(0, 0.14, 0.203); b.add(buckle);
    const cloakM = paint(cloak, { seed: 70 + seed, side: THREE.DoubleSide });
    const cl = new THREE.Mesh(new THREE.CylinderGeometry(0.262, 0.32, 0.62, 12, 1, true, Math.PI * 0.55, Math.PI * 0.9), cloakM); cl.scale.z = 0.86; cl.position.set(0, 0.24, -0.015); b.add(cl);
    const fold = new THREE.Mesh(new THREE.TorusGeometry(0.2, 0.035, 6, 16, Math.PI * 1.1), cloakM); fold.rotation.set(Math.PI / 2, 0, Math.PI * 0.95); fold.scale.set(1.15, 0.86, 1); fold.position.y = 0.53; b.add(fold);
    const brooch = new THREE.Mesh(new THREE.TorusGeometry(0.032, 0.009, 6, 18), m.brass); brooch.position.set(0.15, 0.49, 0.17); brooch.rotation.set(-0.3, 0.45, 0); b.add(brooch);
    const pin = new THREE.Mesh(new THREE.CylinderGeometry(0.004, 0.004, 0.09, 6), m.brass); pin.position.copy(brooch.position); pin.rotation.set(-0.3, 0.45, 0.9); b.add(pin);
    const h = this.headG; h.position.y = 0.58;
    const R = [0.142, 0.17, 0.15]; const hy = 0.16; const S = SCULPT.viking, B = BASE.viking;
    const key = beard + hair; if (!_vfaces[key]) _vfaces[key] = faceMat(vikingFaceCanvas(beard, hair));
    const head = new THREE.Mesh(headGeo(R, B, S, SG, RG), _vfaces[key]); head.position.y = hy; h.add(head);
    const hm = paint(beard, { seed: 80 + seed, grain: 0.4, streak: 0.22, vertical: true, w: 512, repeat: [5, 1], smooth: true });
    if (hair !== 'helmet') for (const s2 of [-1, 1]) { const ear = knob(m.vikSkin, 1, 0.022, 0.042, 0.032, 12, 9); ear.position.copy(headPoint(R, B, S, 0.08, Math.PI / 2 * s2, 1.0)).add(new THREE.Vector3(0, hy, -0.01)); h.add(ear); }
    // hair
    let hairFn = null;
    if (hair === 'long') hairFn = (la, lo) => { const f = Math.abs(lo), show = la - VHAIR.long(f), on = sm(-0.03, 0, show);
      return [tuck(show, 0.08 + 0.05 * sm(1.2, 2.4, f), 0.03), -1.25 * sm(0.25, -1.1, la) * sm(1.45, 2.3, f) * on]; };
    if (hair === 'tied') hairFn = (la, lo) => tuck(la - VHAIR.tied(Math.abs(lo)), 0.045, 0.03);
    if (hair === 'helmet') hairFn = (la, lo) => tuck(la - VHAIR.helmet(Math.abs(lo)), 0.03, 0.03);
    if (hair === 'bald') hairFn = (la, lo) => tuck(fringeShow(la, Math.abs(lo)), 0.07, 0.03);
    if (hairFn) { const hs = new THREE.Mesh(headGeo(R, B, S, SG, RG, hairFn), hm); hs.position.y = hy; h.add(hs); }
    if (hair === 'tied') { const bun = knob(hm, 0.06, 1, 0.9, 1, 14, 10); bun.position.copy(headPoint(R, B, S, 0.55, Math.PI, 1.12)).add(new THREE.Vector3(0, hy, 0)); h.add(bun); }
    if (hair === 'helmet') {   // a conical iron cap that hugs the skull, a brow band, a nasal
      const pr = []; for (let i = 0; i <= 10; i++) { const la = 0.28 + (Math.PI / 2 - 0.28) * i / 10; pr.push([1.1 * R[0] * Math.cos(la), 1.1 * R[1] * Math.sin(la) + 0.03 * Math.pow(i / 10, 3)]); } pr.push([0, pr[pr.length - 1][1]]);
      const dome = new THREE.Mesh(lathe(pr, 24), m.iron); dome.position.y = hy; dome.scale.z = R[2] / R[0] * 1.02; h.add(dome);
      const by = 1.1 * R[1] * Math.sin(0.28);
      const band = new THREE.Mesh(new THREE.CylinderGeometry(1.13 * R[0] * Math.cos(0.28), 1.13 * R[0] * Math.cos(0.28), 0.032, 28, 1, true), m.ironDark); band.scale.z = R[2] / R[0] * 1.02; band.position.y = hy + by; h.add(band);
      const nasal = new THREE.Mesh(new THREE.BoxGeometry(0.024, 0.095, 0.014), m.iron); nasal.position.copy(headPoint(R, B, S, 0.18, 0, 1.06)).add(new THREE.Vector3(0, hy, 0)); nasal.rotation.x = -0.18; h.add(nasal);
    }
    // beard: a short shell along the jaw with a rolled moustache, and a carved beard hanging onto the chest
    const jawFn = (la, lo) => { const f = Math.abs(lo); return tuck(Math.min(VBEARD(f) - la, 1.62 - f), 0.05 + 0.085 * gauss(la + 0.26, 0.045) * gauss(f - 0.17, 0.15) + 0.06 * sm(-0.45, -1.1, la) * gauss(lo, 0.6), 0.035); };
    const jaw = new THREE.Mesh(headGeo(R, B, S, SG, RG, jawFn), hm); jaw.position.y = hy; h.add(jaw);
    const chin = headPoint(R, B, S, -0.75, 0, 1.04).add(new THREE.Vector3(0, hy, 0));
    const spade = (w, len) => { const g = lathe([[0, -len], [w * 0.22, -len * 0.95], [w * 0.6, -len * 0.75], [w * 0.88, -len * 0.48], [w, -len * 0.2], [w * 0.95, 0.0], [w * 0.6, 0.06], [0, 0.08]], 20); return new THREE.Mesh(g, hm); };
    const hang = [];
    if (beardStyle === 'long') hang.push([spade(0.115, 0.34), 0, 0]);
    if (beardStyle === 'forked') { hang.push([spade(0.07, 0.32), -0.045, 0.16]); hang.push([spade(0.07, 0.32), 0.045, -0.16]); }
    if (beardStyle === 'braided') { hang.push([spade(0.1, 0.18), 0, 0]); }
    for (const [mesh, x, rz] of hang) { mesh.scale.z = 0.55; mesh.position.copy(chin).add(new THREE.Vector3(x, 0.05, -0.03)); mesh.rotation.set(0.28, 0, rz); h.add(mesh); }
    if (beardStyle === 'braided') { for (let k = 0; k < 5; k++) { const kn = knob(hm, 0.026 - k * 0.002, 1, 1.3, 1, 10, 8); kn.position.copy(chin).add(new THREE.Vector3(0, -0.19 - k * 0.042, 0.075 + k * 0.012)); h.add(kn); }
      for (let k = 0; k < 2; k++) { const bead = knob(m.brass, 0.02, 1, 0.8, 1, 12, 8); bead.position.copy(chin).add(new THREE.Vector3(0, -0.21 - k * 0.084 - 0.021, 0.08 + k * 0.024)); h.add(bead); } }
    this.root.scale.setScalar(bulk);
    this.pose({});
  }
}
