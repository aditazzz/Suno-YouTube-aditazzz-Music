// The card worlds: when a card is turned face up, its engraving rises off the table as a pop-up diorama of cut,
// gilded black card (back layers first, growing out of the card), with one moving part that carries the lyric.
// Layers are unlit (they are engraved light, like the cards); setTint() colours them with the hall's light.
import * as THREE from 'three';
import { rng, clamp, easeOut, easeIO, lerp } from './lib.js';
import { noise2 } from './lib2.js';
import { GOLD, GOLD_HI } from './cards.js';
import { poly, engrave, line, dot, cloud, bolt, flames, rays, robotFig, vikingFig, longship, skyline, ACCENT } from './cards2.js';
import { flame } from './fire.js';

const PXM = 3400;                                   // canvas pixels per metre
const TAU = Math.PI * 2;
function lc(wm, hm, draw) { const w = Math.round(wm * PXM), h = Math.round(hm * PXM); const c = document.createElement('canvas'); c.width = w; c.height = h; draw(c.getContext('2d'), w, h); return c; }
function texOf(c) { const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4; return t; }
const backOut = (x) => { x = clamp(x); const c1 = 1.5, c3 = c1 + 1; return 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2); };

/** an unlit layer material; with `alt`, a second view shows through lenticular stripes as uAlt goes 0 -> 1 */
function layerMat(map, alt, { additive = false } = {}) {
  const m = new THREE.MeshBasicMaterial({ map, transparent: true, alphaTest: additive ? 0 : 0.04, side: THREE.DoubleSide, depthWrite: !additive, blending: additive ? THREE.AdditiveBlending : THREE.NormalBlending, fog: false });
  if (alt) {
    m.userData.u = { mapB: { value: alt }, uAlt: { value: 0 } };
    m.onBeforeCompile = (sh) => { Object.assign(sh.uniforms, m.userData.u);
      sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\nuniform sampler2D mapB; uniform float uAlt;')
        .replace('#include <map_fragment>', `float stp = fract(vMapUv.x * 70.0); float aa = clamp(fwidth(vMapUv.x * 70.0) * 1.2, 0.002, 0.5);
          float showB = 1.0 - smoothstep(uAlt - aa, uAlt + aa, stp); if (uAlt <= 0.0001) showB = 0.0; if (uAlt >= 0.9999) showB = 1.0;
          vec4 sampledDiffuseColor = mix(texture2D(map, vMapUv), texture2D(mapB, vMapUv), showB); diffuseColor *= sampledDiffuseColor;`); };
    m.customProgramCacheKey = () => 'popAlt';
  }
  return m;
}

class Popup {
  constructor() { this.root = new THREE.Group(); this.layers = []; this.k = 0; this.parts = {}; this.tint = new THREE.Color(1, 1, 1); this.mats = []; }
  /** a layer: canvas, size in metres, depth z (toward the viewer is +), hinged at its bottom edge */
  add(c, wm, hm, z, { x = 0, y = 0, delay = 0, bright = 1.15, alt = null, additive = false, free = false } = {}) {
    const m = layerMat(texOf(c), alt ? texOf(alt) : null, { additive }); m.userData.bright = bright; this.mats.push(m);
    const geo = new THREE.PlaneGeometry(wm, hm); geo.translate(0, hm / 2, 0);
    const mesh = new THREE.Mesh(geo, m); mesh.renderOrder = additive ? 9 : 2;
    const hinge = new THREE.Group(); hinge.position.set(x, y, z); hinge.add(mesh); this.root.add(hinge);
    hinge.userData = { delay, mesh, base: new THREE.Vector3(x, y, z), free };
    this.layers.push(hinge); return hinge;
  }
  addMat(m, bright = 1.15) { m.userData.bright = bright; this.mats.push(m); return m; }
  /** k: 0 flat and tiny inside the card .. 1 standing; layers rise back to front */
  setOpen(k) {
    this.k = k; this.root.visible = k > 0.001;
    for (const h of this.layers) { if (h.userData.free) continue; const d = h.userData.delay; const u = clamp((k - d) / 0.45);
      h.rotation.x = -Math.PI / 2 * (1 - backOut(u)); const s = lerp(0.12, 1, easeOut(u)); h.scale.setScalar(s); h.position.copy(h.userData.base).multiplyScalar(lerp(0.15, 1, easeOut(u))); h.visible = u > 0.001; }
  }
  setAlt(k) { for (const m of this.mats) if (m.userData.u) m.userData.u.uAlt.value = clamp(k); }
  setTint(c, k = 1) { this.tint.copy(c); for (const m of this.mats) m.color.copy(c).multiplyScalar(m.userData.bright * k); }
}

// ================================================================ THE TOWER: city, tower, booster, lightning; the windows spell 20%
const GLYPH = { '2': ['111', '001', '111', '100', '111'], '0': ['111', '101', '101', '101', '111'], '%': ['11001', '11010', '00100', '01011', '10011'] };
export function towerPopup(seed = 141) {
  const P = new Popup(), R = rng(seed);
  // storm clouds at the back
  P.add(lc(0.46, 0.36, (g, w, h) => { cloud(g, w * 0.3, h * 0.36, w * 0.55, h * 0.24, R); cloud(g, w * 0.72, h * 0.28, w * 0.5, h * 0.2, R, { alpha: 0.5 }); cloud(g, w * 0.5, h * 0.5, w * 0.8, h * 0.18, R, { alpha: 0.45 });
    g.save(); g.globalAlpha = 0.8; for (let i = 0; i < 40; i++) dot(g, R() * w, R() * h * 0.25, 1 + R() * 2, GOLD_HI); g.restore(); }), 0.46, 0.36, -0.08, { delay: 0 });
  // lightning (flickers)
  const L = P.add(lc(0.42, 0.34, (g, w, h) => { bolt(g, w * 0.12, h * 0.05, w * 0.6, h * 0.45, R, { w: 6 }); bolt(g, w * 0.92, h * 0.1, w * 0.64, h * 0.55, R, { w: 4.5 }); }), 0.42, 0.34, -0.065, { delay: 0.05, additive: true, bright: 1.6 });
  P.parts.lightning = L;
  // the tower and the booster it caught (a separate cut, so it can fall)
  const TWm = 0.16, THm = 0.36;
  const tower = P.add(lc(TWm, THm, (g, w, h) => {
    const tx0 = w * 0.52, tx1 = w * 0.74, top = h * 0.06, base = h;
    const tw = poly([[tx0, base], [tx0 + 6, top], [tx1 - 6, top], [tx1, base]]); engrave(g, tw, { fill: '#05060a', lw: 3.4 });
    g.save(); g.clip(tw); g.strokeStyle = GOLD; g.lineWidth = 2.6; g.globalAlpha = 0.9; for (let y = base; y > top; y -= 40) { g.beginPath(); g.moveTo(tx0, y); g.lineTo(tx1, y - 40); g.moveTo(tx1, y); g.lineTo(tx0, y - 40); g.moveTo(tx0, y); g.lineTo(tx1, y); g.stroke(); } g.restore();
    const bx0 = w * 0.1, bx1 = w * 0.34, by0 = h * 0.03, by1 = h * 0.5;
    const bo = new Path2D(); bo.rect(bx0, by0, bx1 - bx0, by1 - by0); const gr = g.createLinearGradient(bx0, 0, bx1, 0); gr.addColorStop(0, '#5a5e66'); gr.addColorStop(0.4, '#eef2f6'); gr.addColorStop(1, '#6a6e76'); g.fillStyle = gr; g.fill(bo); g.strokeStyle = GOLD_HI; g.lineWidth = 3; g.stroke(bo);
    for (let y = by0 + 50; y < by1; y += 60) line(g, [[bx0, y], [bx1, y]], '#3a3c40', 1.8, 0.8);
    for (const yy of [by0 + 90, by0 + 150]) engrave(g, poly([[tx0 + 4, yy - 12], [bx1 + 4, yy - 18], [bx1 + 4, yy + 8], [tx0 + 4, yy + 12]]), { fill: '#2a2c30', lw: 2.4, hatch: { ang: 0, step: 5, alpha: 0.45 } });
  }), TWm, THm, -0.035, { x: 0.02, delay: 0.12 });
  P.parts.tower = tower;
  P.parts.booster = new THREE.Vector3(0.02 + (0.22 - 0.5) * TWm, 0.5 * THm, -0.035 + 0.004);
  // the city: one tall dark tower in front is the display; every other window flickers
  const CW = 0.44, CH = 0.17, cw = Math.round(CW * PXM), ch = Math.round(CH * PXM);
  const disp = { x0: Math.round(cw * 0.05), y0: Math.round(ch * 0.12), cols: 15, rows: 9, cell: 25 };
  const dispW = disp.cols * disp.cell + 24;
  let wins = [];
  const cityBase = lc(CW, CH, (g, w, h) => { wins = skyline(g, 0, w, h, R, { maxH: h * 0.9, lit: 0.0 });
    const b = poly([[disp.x0, h], [disp.x0, disp.y0], [disp.x0 + dispW, disp.y0 - 30], [disp.x0 + dispW, h]]); engrave(g, b, { fill: '#04060a', lw: 3, hatch: { ang: 1.57, step: 7, alpha: 0.25 } }); });
  wins = wins.filter(([x]) => x < disp.x0 - 8 || x > disp.x0 + dispW + 8);
  const cityC = document.createElement('canvas'); cityC.width = cw; cityC.height = ch; const cg = cityC.getContext('2d');
  const want = new Set(); ['2', '0', '%'].forEach((c2, gi) => GLYPH[c2].forEach((row, r) => [...row].forEach((v, c) => { if (v === '1') want.add(`${c + gi * 4 + 1},${r + 2}`); })));
  let lastKey = '';
  const drawCity = (t, k20) => {
    const ph = Math.floor(t * 4), key = ph + ':' + (k20 >= 1 ? 1 : Math.round(k20 * 12)); if (key === lastKey) return false; lastKey = key;
    cg.clearRect(0, 0, cw, ch); cg.drawImage(cityBase, 0, 0);
    cg.fillStyle = GOLD_HI; cg.globalAlpha = 0.85;
    for (const [x, y] of wins) { const s = ((Math.sin(x * 12.9898 + y * 78.233) * 43758.5453) % 1 + 1) % 1; if (((s * 97 + ph * 0.37) % 1) < 0.42) cg.fillRect(x - 3, y - 4, 6, 8); }
    for (let r = 0; r < disp.rows; r++) for (let c = 0; c < disp.cols; c++) {
      const rnd = ((Math.sin((r * 13 + c * 7) * 12.9898 + ph * 4.1) * 43758.5453) % 1 + 1) % 1; const isW = want.has(`${c},${r}`);
      const lit = k20 >= 1 ? isW : (k20 <= 0 ? rnd < 0.4 : (isW ? rnd < 0.4 + k20 : rnd < 0.4 * (1 - k20)));
      const x = disp.x0 + 12 + c * disp.cell, y = disp.y0 + 20 + r * disp.cell;
      cg.fillStyle = lit ? (k20 >= 1 ? '#ffe9a8' : GOLD_HI) : '#1a1812'; cg.globalAlpha = lit ? 1 : 0.9; cg.fillRect(x, y, disp.cell - 7, disp.cell - 6);
    }
    cg.globalAlpha = 1; return true;
  };
  drawCity(0, 0);
  const city = P.add(cityC, CW, CH, 0.0, { x: -0.01, delay: 0.25 });
  P.parts.cityTex = city.userData.mesh.material.map;
  P.parts.display = new THREE.Vector3(-0.01 - CW / 2 + (disp.x0 + dispW / 2) / PXM, CH - (disp.y0 + 20 + disp.rows * disp.cell / 2) / PXM, 0.0);   // the 20% (for the camera)
  // the ground strip, and the fire at the tower's feet (live flames in front of it)
  P.add(lc(0.40, 0.05, (g, w, h) => { const gr = poly([[0, h], [0, h * 0.35], [w, h * 0.3], [w, h]]); engrave(g, gr, { fill: '#05060a', hatch: { ang: 0, step: 6, alpha: 0.4, col: '#ff8a3a' } }); }), 0.40, 0.05, 0.035, { delay: 0.35 });
  const fl = new THREE.Group(); fl.position.set(0.03, 0, 0.03); P.root.add(fl); P.parts.flames = fl;
  for (let i = 0; i < 4; i++) { const f = flame(0.07, 0.11, seed + i * 3, 0.9); f.position.set((i - 1.5) * 0.026, 0.012, (i % 2) * 0.008); fl.add(f); }
  const bf = new THREE.Group(); P.root.add(bf); P.parts.boosterFlames = bf;
  for (let i = 0; i < 2; i++) { const f = flame(0.035, 0.08, seed + 20 + i, 1.0); f.rotation.z = Math.PI; f.position.set((i - 0.5) * 0.012, 0, 0); bf.add(f); }
  /** k20: the windows spell 20%; flash: lightning; fire: 0..1 flames climbing; fall: 0..1 the tower topples */
  P.update = (t, cam, { k20 = 0, flash = 0, fire = 0, fall = 0 } = {}) => {
    if (drawCity(t, k20)) P.parts.cityTex.needsUpdate = true;
    L.userData.mesh.material.opacity = clamp(flash); L.visible = P.k > 0.3 && flash > 0.02;
    const k = P.k; fl.visible = k > 0.6 && fire > 0.01; fl.scale.set(1, 0.3 + 1.5 * fire, 1); fl.children.forEach((f) => f.userData.update(t, cam));
    if (fall > 0) { tower.rotation.z = 1.35 * easeIO(fall) * easeIO(fall); tower.position.y = -0.02 * fall; }
    else tower.rotation.z = 0;
    bf.visible = k > 0.7 && fall < 0.05; bf.position.copy(P.parts.booster); bf.children.forEach((f) => f.userData.update(t, cam));
  };
  return P;
}

// ================================================================ THE SUN: the hall of plenty, served by machines; the gates close
export function sunPopup(seed = 161) {
  const P = new Popup(), R = rng(seed);
  const sunC = (burn) => lc(0.40, 0.36, (g, w, h) => { const sx = w / 2, sy = h * 0.42, sr = h * 0.17; const R2 = rng(seed + 5);
    if (!burn) rays(g, sx, sy, sr + 10, sr + h * 0.4, 60, { col: ACCENT.sun, alpha: 0.85, lw: 3.4, wav: 0.05 });
    g.save(); g.fillStyle = burn ? '#1a0402' : '#d89a1e'; g.beginPath(); g.arc(sx, sy, sr, 0, TAU); g.fill(); for (let k = 0; k < 10; k++) { g.strokeStyle = burn ? '#6a1a0a' : '#ffe08a'; g.lineWidth = 2; g.globalAlpha = 0.6; g.beginPath(); g.arc(sx, sy, sr - 8 - k * 10, 0, TAU); g.stroke(); }
    g.globalAlpha = 1; g.strokeStyle = burn ? '#ff4a1a' : GOLD_HI; g.lineWidth = 7; g.beginPath(); g.arc(sx, sy, sr, 0, TAU); g.stroke(); g.restore();
    if (burn) for (let i = 0; i < 5; i++) cloud(g, w * (0.12 + i * 0.19), h * (0.75 - (i % 2) * 0.08), w * 0.24, h * 0.1, R2, { col: '#c99a6a', alpha: 0.5 }); });
  P.add(sunC(false), 0.40, 0.36, -0.08, { delay: 0, alt: sunC(true) });
  const hallC = (burn) => lc(0.32, 0.18, (g, w, h) => { const R2 = rng(seed + 7);
    const x0 = w * 0.06, x1 = w * 0.94, eave = h * 0.42, ridge = h * 0.04, ground = h;
    if (burn) flames(g, x0, x1, eave + 4, R2, { n: 22, h0: 40, h1: h * 0.55 });
    const roof = poly([[x0 - 10, eave], [w / 2, ridge], [x1 + 10, eave]]); engrave(g, roof, { fill: burn ? '#3a0e06' : '#b8861e', lw: 3.4, hatch: { ang: 0, step: 7, alpha: 0.55, col: burn ? '#ff6a2a' : '#ffe08a' } });
    for (let k = 0; k < 12; k++) line(g, [[w / 2, ridge], [x0 - 10 + k * (x1 - x0 + 20) / 11, eave]], burn ? '#ff8a3a' : GOLD_HI, 1.8, 0.7);
    engrave(g, poly([[x0, eave], [x1, eave], [x1, ground], [x0, ground]]), { fill: '#0a0705', hatch: { ang: 1.57, step: 9, alpha: 0.32 } });
    const door = poly([[w / 2 - 50, ground], [w / 2 - 50, h * 0.62], [w / 2, h * 0.54], [w / 2 + 50, h * 0.62], [w / 2 + 50, ground]]); g.save(); g.fillStyle = burn ? '#ff5a1a' : '#ffcf6a'; g.fill(door); g.restore(); g.strokeStyle = GOLD_HI; g.lineWidth = 3; g.stroke(door);
    if (!burn) { robotFig(g, w * 0.3, ground, 1.5); robotFig(g, w * 0.7, ground, 1.5); for (const x of [w * 0.3, w * 0.7]) { g.save(); g.fillStyle = '#c8a050'; g.beginPath(); g.ellipse(x + 10, ground - 205, 48, 12, 0, 0, TAU); g.fill(); g.strokeStyle = GOLD_HI; g.lineWidth = 2; g.stroke(); dot(g, x, ground - 218, 11, '#a03a12'); dot(g, x + 22, ground - 220, 12, '#c8862a'); g.restore(); } }
    else flames(g, x0, x1, ground, R2, { n: 18, h0: 30, h1: 120 });
  });
  P.add(hallC(false), 0.32, 0.18, -0.03, { delay: 0.12, alt: hallC(true) });
  const wallC = (burn) => lc(0.42, 0.075, (g, w, h) => { engrave(g, poly([[0, h], [0, h * 0.6], [w, h * 0.6], [w, h]]), { fill: '#0a0806', hatch: { ang: 0, step: 10, alpha: 0.4 } });
    for (let k = 0; k < 11; k++) { const x = w * (0.05 + k * 0.09), y = h * 0.22; line(g, [[x, h * 0.6], [x, y]], burn ? '#5a3a1a' : '#5a8a3a', 4, 1);
      g.save(); g.translate(x, y); if (burn) g.rotate(1.2); for (let p = 0; p < 14; p++) { g.rotate(TAU / 14); g.fillStyle = burn ? '#5a2a10' : ACCENT.sun; g.beginPath(); g.ellipse(0, -18, 6, 13, 0, 0, TAU); g.fill(); } g.fillStyle = '#3a1a08'; g.beginPath(); g.arc(0, 0, 11, 0, TAU); g.fill(); g.restore(); } });
  P.add(wallC(false), 0.42, 0.075, 0.02, { delay: 0.25, alt: wallC(true) });
  // the gates: two leaves hinged at the sides, standing open toward us, that swing shut on "eat"
  const gateC = (side) => lc(0.15, 0.13, (g, w, h) => { const leaf = poly([[0, h], [0, h * 0.18], [w * 0.5, 0], [w, h * 0.18], [w, h]]); engrave(g, leaf, { fill: '#0b0806', lw: 4, hatch: { ang: 1.57, step: 14, alpha: 0.6 } });
    for (const y of [0.4, 0.7, 0.92]) line(g, [[0, h * y], [w, h * y]], GOLD_HI, 4, 0.9); g.save(); g.strokeStyle = GOLD_HI; g.lineWidth = 3; g.beginPath(); g.arc(side > 0 ? w * 0.15 : w * 0.85, h * 0.62, 14, 0, TAU); g.stroke(); g.restore(); });
  const gates = [];
  for (const s of [-1, 1]) { const piv = new THREE.Group(); piv.position.set(s * 0.15, 0, 0.055); P.root.add(piv);
    const gm = P.addMat(layerMat(texOf(gateC(s)), null));
    const m = new THREE.Mesh(new THREE.PlaneGeometry(0.15, 0.13).translate(-s * 0.075, 0.065, 0), gm); m.renderOrder = 2; piv.add(m); gates.push([piv, s]); }
  P.parts.gates = gates;
  // the one left outside, with an empty bowl
  const vk = P.add(lc(0.09, 0.15, (g, w, h) => { vikingFig(g, w * 0.42, h, 0.95, { pose: 'stand', helmet: false, holding: [[44, -150], [80, -150]] }); g.save(); g.translate(w * 0.42 + 92, h - 146); g.fillStyle = '#6a4428'; g.beginPath(); g.ellipse(0, 0, 34, 11, 0, 0, TAU); g.fill(); g.strokeStyle = GOLD_HI; g.lineWidth = 3; g.stroke(); g.beginPath(); g.ellipse(0, -2, 26, 6, 0, 0, TAU); g.fillStyle = '#1a0e08'; g.fill(); g.restore(); }), 0.09, 0.15, 0.095, { x: 0.06, free: true, bright: 1.35 });
  P.parts.outsider = vk;
  /** gate: 0 open .. 1 shut; outside: 0..1 the outsider stands up; alt: 0 feast .. 1 burning */
  P.update = (t, cam, { gate = 0, outside = 0, alt = 0 } = {}) => {
    for (const [piv, s] of gates) { piv.visible = P.k > 0.7; piv.rotation.y = s * (Math.PI / 2) * (1 - easeIO(gate)); }
    vk.visible = outside > 0.01; vk.rotation.x = -Math.PI / 2 * (1 - backOut(outside)); vk.scale.setScalar(Math.max(0.01, outside));
    P.setAlt(alt);
  };
  return P;
}

// ================================================================ THE ROBOT: a longship rowed by machines while we lounge
export function robotPopup(seed = 171) {
  const P = new Popup(), R = rng(seed);
  P.add(lc(0.40, 0.3, (g, w, h) => { g.save(); g.strokeStyle = GOLD_HI; g.lineWidth = 5; g.beginPath(); g.arc(w * 0.22, h * 0.32, 60, 0, TAU); g.stroke(); g.restore(); rays(g, w * 0.22, h * 0.32, 72, 140, 36, { alpha: 0.6, lw: 2 });
    for (let k = 0; k < 6; k++) { const x = w * (0.55 + k * 0.07), y = h * (0.22 + (k % 2) * 0.06); line(g, [[x - 26, y], [x - 9, y - 12], [x, y]], GOLD_HI, 3, 0.95); line(g, [[x, y], [x + 9, y - 12], [x + 26, y]], GOLD_HI, 3, 0.95); } }), 0.40, 0.3, -0.07, { delay: 0 });
  const wave = (wm, hm, a) => lc(wm, hm, (g, w, h) => { g.save(); g.fillStyle = '#05070b'; g.beginPath(); g.moveTo(0, h); for (let x = 0; x <= w; x += 8) g.lineTo(x, h * 0.35 + Math.sin(x / 60 + a) * h * 0.18); g.lineTo(w, h); g.closePath(); g.fill(); g.clip();
    for (let y = 0; y < h; y += 7) line(g, [[0, y], [w, y + 2]], GOLD, 1.6, 0.5); g.restore(); line(g, Array.from({ length: Math.ceil(w / 8) + 1 }, (_, i) => [i * 8, h * 0.35 + Math.sin(i * 8 / 60 + a) * h * 0.18]), GOLD_HI, 3, 1); });
  const back = P.add(wave(0.5, 0.05, 0), 0.5, 0.05, -0.03, { delay: 0.1 });
  // the ship, its rowers and the one lounging at the stern, as one cut; the oars are moving parts
  const ship = P.add(lc(0.34, 0.24, (g, w, h) => {
    longship(g, w * 0.04, w * 0.96, h * 0.86, R, { dir: 1, oars: 0, scale: 1.4, rowers: () => {
      for (let k = 0; k < 4; k++) robotFig(g, w * (0.36 + k * 0.13), h * 0.82, 1.3, { arm: [[-40, -70], [-74, -36]] });
      vikingFig(g, w * 0.17, h * 0.83, 1.1, { pose: 'recline', facing: 1, helmet: false, holding: [[-100, -60], [-70, -110]] }); } });
  }), 0.34, 0.24, 0.0, { delay: 0.2 });
  const oarM = new THREE.MeshBasicMaterial({ color: 0xd9b25f, fog: false }); P.addMat(oarM, 1.0); const oars = [];
  for (let k = 0; k < 5; k++) { const piv = new THREE.Group(); piv.position.set(-0.06 + k * 0.042, 0.04, 0.004); ship.userData.mesh.add(piv);
    const oar = new THREE.Mesh(new THREE.BoxGeometry(0.0035, 0.075, 0.002).translate(0, -0.0375, 0), oarM); piv.add(oar); oars.push(piv); }
  const front = P.add(wave(0.5, 0.045, 2), 0.5, 0.045, 0.03, { delay: 0.3 });
  P.update = (t, cam, { row = 1 } = {}) => {
    const st = Math.sin(t * Math.PI * 2 / 1.1378);           // two beats per stroke
    oars.forEach((o) => { o.rotation.z = 0.35 + 0.4 * st * row; });
    ship.userData.mesh.position.y = 0.004 * Math.sin(t * 2.1); ship.userData.mesh.rotation.z = 0.02 * Math.sin(t * 1.7);
    back.userData.mesh.position.x = 0.02 * Math.sin(t * 0.9); front.userData.mesh.position.x = -0.025 * Math.sin(t * 1.1 + 1);
  };
  return P;
}

// ================================================================ THE RED PLANET: Mars rises out of the sea; the ships turn; a flag and a name
export function redPopup(seed = 181) {
  const P = new Popup(), R = rng(seed), N = noise2(seed);
  P.add(lc(0.44, 0.34, (g, w, h) => { for (let i = 0; i < 160; i++) { const big = R() < 0.08; dot(g, R() * w, R() * h * 0.8, big ? 3 : 1 + R() * 1.6, R() < 0.3 ? GOLD_HI : GOLD, 0.6 + R() * 0.4); } }), 0.44, 0.34, -0.09, { delay: 0 });
  const marsC = lc(0.26, 0.26, (g, w, h) => { const cx = w / 2, cy = h / 2, r = w * 0.47;
    g.save(); g.beginPath(); g.arc(cx, cy, r, 0, TAU); g.clip(); const gr = g.createRadialGradient(cx - r * 0.35, cy - r * 0.35, r * 0.1, cx, cy, r); gr.addColorStop(0, '#c4512c'); gr.addColorStop(1, '#3a0f07'); g.fillStyle = gr; g.fillRect(0, 0, w, h);
    for (let k = -r; k < r; k += 9) { const y = cy + k, ww = Math.sqrt(r * r - k * k); g.strokeStyle = '#f0b06a'; g.globalAlpha = 0.35 + 0.4 * (1 - (k + r) / (2 * r)); g.lineWidth = 2; g.beginPath(); g.moveTo(cx - ww, y); g.quadraticCurveTo(cx, y + ww * 0.16, cx + ww, y); g.stroke(); }
    // a dark wedge like Syrtis Major, a long rift, a white polar cap (no face)
    g.globalAlpha = 0.3; g.fillStyle = '#4a1408'; g.beginPath(); g.moveTo(cx + 0.05 * r, cy - 0.35 * r); g.quadraticCurveTo(cx + 0.45 * r, cy - 0.05 * r, cx + 0.3 * r, cy + 0.45 * r); g.quadraticCurveTo(cx + 0.12 * r, cy + 0.15 * r, cx - 0.05 * r, cy + 0.2 * r); g.quadraticCurveTo(cx + 0.1 * r, cy - 0.05 * r, cx + 0.05 * r, cy - 0.35 * r); g.fill();
    g.globalAlpha = 0.4; g.strokeStyle = '#3a0f06'; g.lineWidth = 7; g.beginPath(); g.moveTo(cx - 0.75 * r, cy + 0.05 * r); g.quadraticCurveTo(cx - 0.35 * r, cy - 0.02 * r, cx - 0.05 * r, cy + 0.08 * r); g.stroke();
    g.globalAlpha = 0.85; g.fillStyle = '#f2e6d8'; g.beginPath(); g.ellipse(cx - 0.05 * r, cy - 0.93 * r, 0.32 * r, 0.09 * r, 0, 0, TAU); g.fill();
    g.restore(); g.strokeStyle = GOLD_HI; g.lineWidth = 5; g.beginPath(); g.arc(cx, cy, r, 0, TAU); g.stroke(); });
  const mars = P.add(marsC, 0.26, 0.26, -0.06, { free: true }); P.parts.mars = mars;
  P.add(lc(0.48, 0.09, (g, w, h) => { g.fillStyle = '#04060a'; g.fillRect(0, 0, w, h); for (let y = 6; y < h; y += 7) line(g, [[0, y], [w, y + (N(y, 3) - 0.5) * 6]], GOLD, 1.6, 0.35 + 0.4 * y / h);
    line(g, [[0, 2], [w, 2]], GOLD_HI, 4, 1); for (let x = w * 0.35; x < w * 0.65; x += 12) line(g, [[x, 10 + (x % 5)], [x + 6, 10 + (x % 5)]], '#f08a50', 3, 0.8); }), 0.48, 0.09, -0.03, { delay: 0.1 });
  const ships = [];
  for (const [x, z, dir, sc, cols] of [[-0.15, -0.02, 1, 0.55, ['#8a1c14', '#d8c08a']], [0.16, -0.015, -1, 0.6, ['#1f3a6a', '#e0c27a']], [-0.02, 0.0, 1, 0.75, ['#2e5a34', '#d8c08a']]]) {
    const s = P.add(lc(0.12 * sc, 0.1 * sc, (g, w, h) => longship(g, w * 0.04, w * 0.96, h * 0.86, R, { dir, oars: 3, scale: 0.6 * sc * 1.2, sailCols: cols })), 0.12 * sc, 0.1 * sc, z, { x, y: 0.05, free: true });
    ships.push([s, x, dir]); }
  // red sand in front: a Viking plants the banner; a sign names the place
  const VX = -0.0435;
  P.add(lc(0.46, 0.13, (g, w, h) => { const d = new Path2D(); d.moveTo(0, h); d.lineTo(0, h * 0.5); d.quadraticCurveTo(w * 0.3, h * 0.1, w * 0.6, h * 0.35); d.quadraticCurveTo(w * 0.8, h * 0.5, w, h * 0.3); d.lineTo(w, h); d.closePath(); engrave(g, d, { fill: '#2a0c06', hatch: { ang: 0.25, step: 7, alpha: 0.45, col: '#d8512a' } });
    vikingFig(g, w * 0.38, h * 0.62, 1.1, { pose: 'stand', facing: 1, helmet: true, holding: [[18, -200], [36, -170]] }); }), 0.46, 0.13, 0.04, { delay: 0.3 });
  const poleM = P.addMat(new THREE.MeshBasicMaterial({ color: 0xf4d995, fog: false }), 1.0);
  const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.0015, 0.0015, 0.13, 6).translate(0, 0.065, 0), poleM); pole.position.set(VX, 0.03, 0.046); P.root.add(pole);
  const flagC = lc(0.06, 0.035, (g, w, h) => { const f = new Path2D(); f.moveTo(0, 2); f.quadraticCurveTo(w * 0.5, -4, w, 6); f.lineTo(w * 0.85, h * 0.5); f.lineTo(w, h - 2); f.quadraticCurveTo(w * 0.5, h - 10, 0, h - 2); f.closePath(); engrave(g, f, { fill: '#e8dcc0', lw: 3 });
    // the raven banner: a raven in profile, wings spread
    g.save(); g.translate(w * 0.47, h * 0.55); g.fillStyle = '#0a0a0c'; g.beginPath();
    g.moveTo(-46, 6); g.lineTo(-30, 2); g.quadraticCurveTo(-14, -8, 4, -4); g.lineTo(14, -10); g.lineTo(26, -9); g.lineTo(36, -6); g.lineTo(26, -3); g.lineTo(18, 0);   // tail, back, head, beak
    g.quadraticCurveTo(10, 8, -6, 10); g.lineTo(-20, 12); g.closePath(); g.fill();
    g.beginPath(); g.moveTo(-10, -2); g.quadraticCurveTo(-26, -30, -4, -44); g.quadraticCurveTo(-2, -26, 6, -8); g.closePath(); g.fill();      // the raised wing
    g.beginPath(); g.moveTo(-4, 6); g.quadraticCurveTo(-20, 26, -2, 34); g.quadraticCurveTo(2, 20, 8, 6); g.closePath(); g.fill();          // the lower wing
    g.fillStyle = '#e8dcc0'; g.beginPath(); g.arc(20, -6, 1.8, 0, TAU); g.fill(); g.restore(); });
  const flag = new THREE.Mesh(new THREE.PlaneGeometry(0.06, 0.035).translate(0.03, -0.0175, 0), P.addMat(layerMat(texOf(flagC), null), 1.1)); P.root.add(flag);
  const signC = lc(0.08, 0.05, (g, w, h) => { line(g, [[w * 0.5, h], [w * 0.5, h * 0.5]], GOLD, 5, 1); engrave(g, poly([[6, 6], [w - 18, 6], [w - 4, h * 0.27], [w - 18, h * 0.5], [6, h * 0.5]]), { fill: '#0b0806', lw: 3 });
    g.save(); g.fillStyle = GOLD_HI; g.font = '30px "CormSC", serif'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText('GREENLAND', w * 0.47, h * 0.28); g.restore(); });
  const sign = P.add(signC, 0.08, 0.05, 0.075, { x: 0.13, free: true }); P.parts.sign = sign;
  /** rise: Mars comes up; plant: the banner goes in; name: the sign; sail: the ships turn toward Mars */
  P.update = (t, cam, { rise = 0, plant = 0, name = 0, sail = 0 } = {}) => {
    mars.visible = P.k > 0.2 && rise > 0.001; mars.position.set(0, lerp(-0.13, 0.03, easeOut(rise)), -0.06);
    for (const [s, x, dir] of ships) { s.visible = P.k > 0.5; s.scale.setScalar(1); s.position.x = x * (1 - 0.35 * easeIO(sail)); s.rotation.y = -dir * 0.7 * easeIO(sail); }
    pole.visible = plant > 0.01 && P.k > 0.9; pole.scale.y = Math.max(0.01, easeOut(clamp(plant * 2)));
    flag.visible = plant > 0.45 && P.k > 0.9; const fk = easeOut(clamp((plant - 0.45) / 0.55)); flag.position.set(VX, 0.03 + 0.13 * (0.25 + 0.75 * fk), 0.047); flag.rotation.y = 0.15 * Math.sin(t * 3); flag.scale.set(Math.max(0.01, fk), 1, 1);
    sign.visible = name > 0.01; sign.rotation.x = -Math.PI / 2 * (1 - backOut(name)); sign.scale.setScalar(Math.max(0.01, name));
  };
  return P;
}

// ================================================================ THE GARDENER: perfect rows tended by machines; one tomato, by hand
export function gardenerPopup(seed = 191) {
  const P = new Popup(), R = rng(seed);
  P.add(lc(0.44, 0.34, (g, w, h) => { for (let k = 0; k < 6; k++) { const x = w * (0.04 + k * 0.155); const rib = new Path2D(); rib.moveTo(x, h); rib.lineTo(x, h * 0.35); rib.quadraticCurveTo(x + w * 0.0775, h * 0.12, x + w * 0.155, h * 0.35); g.strokeStyle = GOLD_HI; g.lineWidth = 4; g.globalAlpha = 0.9; g.stroke(rib);
    for (let y = h * 0.4; y < h; y += h * 0.12) line(g, [[x, y], [x + w * 0.155, y]], GOLD, 2, 0.6); for (let j = 0; j < 3; j++) line(g, [[x + 30 + j * 40, h * (0.5 + j * 0.15)], [x + 90 + j * 40, h * (0.38 + j * 0.15)]], '#ffffff', 2, 0.25); } g.globalAlpha = 1; }), 0.44, 0.34, -0.09, { delay: 0 });
  const rowC = (n, sc) => lc(0.42, 0.07, (g, w, h) => { line(g, [[0, h - 4], [w, h - 4]], GOLD, 3, 0.8);
    for (let i = 0; i < n; i++) { const x = (i + 0.5) / n * w, r = h * 0.32 * sc; g.save(); g.fillStyle = '#1a3a14'; g.beginPath(); g.arc(x, h - 4 - r, r, 0, TAU); g.fill(); g.strokeStyle = ACCENT.gardener; g.lineWidth = 3; g.stroke();
      for (let q = 0; q < 3; q++) dot(g, x + (R() - 0.5) * r, h - 4 - r + (R() - 0.5) * r, 3 + 3 * sc, '#e04a2a', 0.95); line(g, [[x, h - 4], [x, h - 4 - r * 0.3]], ACCENT.gardener, 3, 1); g.restore(); } });
  [[-0.06, 14, 0.7], [-0.03, 12, 0.8], [0.0, 10, 0.9], [0.03, 8, 1.0]].forEach(([z, n, sc], i) => P.add(rowC(n, sc), 0.42, 0.07, z, { delay: 0.12 + i * 0.1 }));
  P.add(lc(0.06, 0.09, (g, w, h) => robotFig(g, w * 0.5, h, 1.0, { arm: [[-40, -100], [-80, -110]] })), 0.06, 0.09, -0.045, { x: 0.12, delay: 0.4 });
  P.add(lc(0.06, 0.09, (g, w, h) => robotFig(g, w * 0.5, h, 1.0, { arm: [[40, -90], [70, -80]] })), 0.06, 0.09, -0.015, { x: -0.14, delay: 0.45 });
  P.add(lc(0.1, 0.36, (g, w, h) => { const gr = g.createLinearGradient(0, 0, 0, h); gr.addColorStop(0, 'rgba(255,240,200,0.5)'); gr.addColorStop(1, 'rgba(255,240,200,0.08)'); g.fillStyle = gr; g.fill(poly([[w * 0.3, 0], [w * 0.7, 0], [w, h], [0, h]])); }), 0.1, 0.36, 0.02, { delay: 0.5, additive: true, bright: 1.0 });
  P.add(lc(0.07, 0.09, (g, w, h) => { vikingFig(g, w * 0.45, h, 0.85, { pose: 'kneel', facing: 1, helmet: false, holding: [[30, -130], [60, -160]] }); dot(g, w * 0.45 + 52, h - 136, 18, '#e04a2a'); dot(g, w * 0.45 + 46, h - 142, 6, '#ff8a6a', 0.8); }), 0.07, 0.09, 0.06, { delay: 0.55 });
  P.update = () => {};
  return P;
}
