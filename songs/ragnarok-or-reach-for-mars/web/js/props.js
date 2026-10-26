// Feast props for the tables: drinking horns with brass rims, turned wooden cups, platters of bread, candles.
// Each prop's origin is its base on the table, so a "jump" on a slam is just a lift of the whole group.
import * as THREE from 'three';
import { clay, rng } from './lib.js';
import { paint, knob } from './puppets.js';
import { flame } from './fire.js';

let PM = null;
function mats(M) {
  if (PM) return PM;
  PM = {
    horn: clay(0xffffff, { map: hornTex() }), cup: paint('#6a4428', { seed: 90, grain: 0.3 }), plate: paint('#5a3a22', { seed: 91, grain: 0.25 }),
    bread: paint('#b07a3a', { seed: 92, grain: 0.05, streak: 0.15, smooth: true }), meat: paint('#6a2a1a', { seed: 93, grain: 0.05, streak: 0.2, smooth: true }),
    apple: paint('#8a2a1a', { seed: 94, grain: 0.0, smooth: true }), wax: clay(0xe8dcc0, { emissive: 0x2a1606 }), mead: clay(0x8a5a14, { emissive: 0x1a0c02 }),
    brass: M.brass,
  };
  return PM;
}
function hornTex() {   // horn: dark tip fading to cream, with growth rings
  const c = document.createElement('canvas'); c.width = 64; c.height = 256; const g = c.getContext('2d');
  const gr = g.createLinearGradient(0, 0, 0, 256); gr.addColorStop(0, '#2a1a10'); gr.addColorStop(0.35, '#7a5a3a'); gr.addColorStop(1, '#e6d6b4'); g.fillStyle = gr; g.fillRect(0, 0, 64, 256);
  for (let y = 8; y < 256; y += 6 + (y % 5)) { g.fillStyle = 'rgba(40,25,15,0.18)'; g.fillRect(0, y, 64, 2); }
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
}
/** a curved drinking horn lying on a little stand, or held: tip at the origin end, mouth at the other */
export function horn(M, len = 0.3, seed = 1) {
  const P = mats(M); const R = rng(seed);
  const curve = new THREE.QuadraticBezierCurve3(new THREE.Vector3(0, 0, 0), new THREE.Vector3(len * 0.45, len * (0.05 + R() * 0.1), 0), new THREE.Vector3(len, len * 0.55, 0));
  const N = 24, S = 12, pos = [], uv = [], idx = [];
  for (let i = 0; i <= N; i++) { const u = i / N; const p = curve.getPoint(u); const tng = curve.getTangent(u); const nrm = new THREE.Vector3(0, 0, 1); const bin = new THREE.Vector3().crossVectors(tng, nrm).normalize();
    const r = 0.004 + 0.034 * Math.pow(u, 0.9);
    for (let j = 0; j <= S; j++) { const a = j / S * Math.PI * 2; const v = new THREE.Vector3().addScaledVector(bin, Math.cos(a) * r).addScaledVector(nrm, Math.sin(a) * r).add(p); pos.push(v.x, v.y, v.z); uv.push(j / S, u); } }
  for (let i = 0; i < N; i++) for (let j = 0; j < S; j++) { const a = i * (S + 1) + j, b = a + S + 1; idx.push(a, b, a + 1, b, b + 1, a + 1); }
  const geo = new THREE.BufferGeometry(); geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); geo.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2)); geo.setIndex(idx); geo.computeVertexNormals();
  const g = new THREE.Group(); const h = new THREE.Mesh(geo, P.horn); g.add(h);
  const end = curve.getPoint(1), tg = curve.getTangent(1);
  const rim = new THREE.Mesh(new THREE.TorusGeometry(0.038, 0.005, 6, 18), P.brass); rim.position.copy(end); rim.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), tg); g.add(rim);
  const tip = knob(P.brass, 0.008, 1, 1, 1, 8, 6); g.add(tip);
  g.userData.mouth = end.clone();
  return g;
}
export function cup(M, seed = 1) {
  const P = mats(M); const g = new THREE.Group();
  const geo = new THREE.LatheGeometry([[0, 0], [0.032, 0], [0.034, 0.01], [0.03, 0.03], [0.038, 0.085], [0.034, 0.088], [0.028, 0.035], [0, 0.03]].map(([x, y]) => new THREE.Vector2(x, y)), 16);
  g.add(new THREE.Mesh(geo, P.cup)); const m = new THREE.Mesh(new THREE.CircleGeometry(0.033, 16), P.mead); m.rotation.x = -Math.PI / 2; m.position.y = 0.075; g.add(m);
  return g;
}
export function platter(M, seed = 1) {
  const P = mats(M); const R = rng(seed); const g = new THREE.Group();
  const pl = new THREE.Mesh(new THREE.CylinderGeometry(0.16, 0.15, 0.025, 20), P.plate); pl.position.y = 0.0125; g.add(pl);
  for (let i = 0; i < 2; i++) { const b = knob(P.bread, 0.06, 1.3, 0.6, 1, 14, 10); b.position.set((R() - 0.5) * 0.12, 0.05, (R() - 0.5) * 0.1); b.rotation.y = R() * 3; g.add(b); }
  const mt = knob(P.meat, 0.055, 1.4, 0.7, 0.9, 12, 9); mt.position.set(0.05, 0.05, 0.04); mt.rotation.y = R() * 3; g.add(mt);
  for (let i = 0; i < 2; i++) { const a = knob(P.apple, 0.028, 1, 0.9, 1, 12, 9); a.position.set(-0.07 + i * 0.05, 0.05, -0.07); g.add(a); }
  return g;
}
export function candle(M, h = 0.14, seed = 1) {
  const P = mats(M); const g = new THREE.Group();
  const c = new THREE.Mesh(new THREE.CylinderGeometry(0.022, 0.025, h, 12), P.wax); c.position.y = h / 2; g.add(c);
  const f = flame(0.05, 0.1, 40 + seed, 1.0); f.position.y = h; g.add(f); g.userData.flame = f;
  return g;
}
