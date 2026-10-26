// Offline: under the street, a square shaft cut through layers of rock (deeper is older, the years glow on the
// layers, old tickets stuck in them), opening onto an endless dark floor where every blocker ever taken offline sits
// in rows. In the middle: the dinosaur, and the asteroid somebody took offline 66,000,000 years ago.
import * as THREE from 'three';
import { clay, canvasTex, rng, labelPlane, FONT, dotTex } from './lib.js';

export const CY0 = -2, CY1 = -260;           // shaft top / floor of Offline
export const SHAFT = 11;                      // half-width of the shaft
export const FLOOR_Z = -60;                   // the middle of the field of blockers
export const SHAFT_Z = 13;                    // the shaft is under the street in front of the standup tower
export function buildCanyon() {
  const g = new THREE.Group(); const R = rng(41);
  const cz = SHAFT_Z;
  const tones = ['#7c6b5e', '#4f4a5c', '#8f7c66', '#3d4a5a', '#6e6280', '#9c8466', '#46506a', '#7f6656', '#5a6470', '#8a7a8e'];
  let y = CY0; let k = 0; const seams = [];
  while (y > CY1 + 34) {
    const th = 5 + R() * 9; const c = clay(new THREE.Color(tones[k % tones.length]).getHex(), { rimAmt: 0.12 }); const out = (k % 2) ? 0.0 : 0.7;
    for (const [sx, sz, w, d] of [[-1, 0, 6, SHAFT * 2 + 12], [1, 0, 6, SHAFT * 2 + 12], [0, -1, SHAFT * 2, 6], [0, 1, SHAFT * 2, 6]]) {
      const b = new THREE.Mesh(new THREE.BoxGeometry(w, th, d), c);
      b.position.set(sx * (SHAFT + 3 - out), y - th / 2, cz + sz * (SHAFT + 3 - out)); g.add(b);
    }
    seams.push(y); y -= th; k++;
  }
  // glowing seams between the layers
  const sp = []; for (const yy of seams) { const s = SHAFT - 0.75;
    sp.push(-s, yy, cz - s, s, yy, cz - s, s, yy, cz - s, s, yy, cz + s, s, yy, cz + s, -s, yy, cz + s, -s, yy, cz + s, -s, yy, cz - s); }
  const sg = new THREE.BufferGeometry(); sg.setAttribute('position', new THREE.Float32BufferAttribute(sp, 3));
  g.add(new THREE.LineSegments(sg, new THREE.LineBasicMaterial({ color: 0x4dffa0, transparent: true, opacity: 0.85, blending: THREE.AdditiveBlending, depthWrite: false })));
  // the years, deeper is older
  const years = ['2026', '2025', '2024', '2022', '2021', '2019', '2017', '2014', '2011', '2009', '2004', '1999', '1987', '1969', '1903'];
  years.forEach((yr, i) => { const yy = CY0 - 12 - i * ((CY0 - (CY1 + 50)) / years.length);
    const l = labelPlane(yr, { h: 2.0, font: FONT.monoB, size: 80, fg: '#a6f5cf', bg: 'rgba(0,0,0,0)' });
    const side = i % 4; const s = SHAFT - 0.1;
    if (side === 0) { l.position.set(-s, yy, cz + (R() - 0.5) * 6); l.rotation.y = Math.PI / 2; }
    else if (side === 1) { l.position.set((R() - 0.5) * 6, yy, cz - s); }
    else if (side === 2) { l.position.set(s, yy, cz + (R() - 0.5) * 6); l.rotation.y = -Math.PI / 2; }
    else { l.position.set((R() - 0.5) * 6, yy, cz + s); l.rotation.y = Math.PI; }
    g.add(l); });
  // old tickets stuck in the walls
  const ticket = canvasTex(256, 128, (c, w, h) => { c.fillStyle = '#e9ecf2'; c.fillRect(0, 0, w, h); c.fillStyle = '#2a6fdb'; c.fillRect(0, 0, w, 30); c.fillStyle = '#fff'; c.font = `22px ${FONT.monoB}`; c.fillText('ENG-4021', 10, 22);
    c.fillStyle = '#9aa'; for (let i = 0; i < 4; i++) c.fillRect(10, 44 + i * 18, 200 - i * 30, 9); });
  const n = 160; const tm = new THREE.InstancedMesh(new THREE.PlaneGeometry(1.8, 0.9), new THREE.MeshLambertMaterial({ map: ticket, side: THREE.DoubleSide, emissive: 0x303030 }), n);
  const m4 = new THREE.Matrix4(), qq = new THREE.Quaternion(), e = new THREE.Euler();
  for (let i = 0; i < n; i++) { const side = i % 4, s = SHAFT - 0.12, yy = CY0 - 4 - R() * (CY0 - (CY1 + 40)); let p;
    if (side === 0) { p = new THREE.Vector3(-s, yy, cz + (R() - 0.5) * 18); e.set(0, Math.PI / 2, (R() - 0.5) * 0.9); }
    else if (side === 1) { p = new THREE.Vector3((R() - 0.5) * 18, yy, cz - s); e.set(0, 0, (R() - 0.5) * 0.9); }
    else if (side === 2) { p = new THREE.Vector3(s, yy, cz + (R() - 0.5) * 18); e.set(0, -Math.PI / 2, (R() - 0.5) * 0.9); }
    else { p = new THREE.Vector3((R() - 0.5) * 18, yy, cz + s); e.set(0, Math.PI, (R() - 0.5) * 0.9); }
    qq.setFromEuler(e); m4.compose(p, qq, new THREE.Vector3(1, 1, 1)); tm.setMatrixAt(i, m4); }
  g.add(tm);
  // the floor of Offline: rows and rows of blockers fading into the dark
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(1200, 1200), new THREE.MeshBasicMaterial({ color: 0x07070a })); floor.rotation.x = -Math.PI / 2; floor.position.set(0, CY1, FLOOR_Z); g.add(floor);
  const pinkM = clay(0xff3d8b, { emissive: 0x4a0a26, emissiveIntensity: 0.65, rimAmt: 0.35 });
  const cols = 41, rows = 46, step = 5.2; const nb = cols * rows; const bm = new THREE.InstancedMesh(new THREE.BoxGeometry(2.6, 2.6, 2.6), pinkM, nb); let ii = 0;
  for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) {
    const x = (c - (cols - 1) / 2) * step, z = SHAFT_Z + 10 - r * step;
    if ((Math.abs(x) < 16 && Math.abs(z - (FLOOR_Z - 8)) < 16) || (Math.abs(x) < SHAFT + 2 && Math.abs(z - SHAFT_Z) < SHAFT + 2)) { m4.makeScale(0.0001, 0.0001, 0.0001); bm.setMatrixAt(ii++, m4); continue; }
    e.set(0, (R() - 0.5) * 0.3, 0); qq.setFromEuler(e); m4.compose(new THREE.Vector3(x + (R() - 0.5) * 0.6, CY1 + 1.3, z + (R() - 0.5) * 0.6), qq, new THREE.Vector3(1, 1, 1)); bm.setMatrixAt(ii++, m4);
  }
  g.add(bm);
  // the clearing: the dinosaur and the asteroid
  const bone = clay(0xe8dfcc, { rimAmt: 0.45 }); const dino = new THREE.Group();
  const spine = new THREE.CatmullRomCurve3([[-9, 3.2, 0], [-5, 4.6, 0], [-1, 5.2, 0], [3, 4.4, 0], [6, 3.6, 0], [9, 2.6, 0], [12, 1.8, 0]].map((a) => new THREE.Vector3(...a)));
  dino.add(new THREE.Mesh(new THREE.TubeGeometry(spine, 60, 0.28, 10), bone));
  for (let i = 0; i < 9; i++) { const p = spine.getPoint(0.22 + i * 0.05); const rib = new THREE.Mesh(new THREE.TorusGeometry(1.5 - i * 0.08, 0.12, 8, 24, Math.PI), bone); rib.position.copy(p); rib.position.y -= 1.2; rib.rotation.y = Math.PI / 2; rib.rotation.z = Math.PI; dino.add(rib); }
  const neck = new THREE.CatmullRomCurve3([[-9, 3.2, 0], [-11, 5.5, 0], [-12, 7.5, 0]].map((a) => new THREE.Vector3(...a))); dino.add(new THREE.Mesh(new THREE.TubeGeometry(neck, 30, 0.22, 8), bone));
  const skull = new THREE.Mesh(new THREE.SphereGeometry(0.9, 20, 14), bone); skull.scale.set(1.6, 0.9, 0.8); skull.position.set(-12.6, 7.9, 0); dino.add(skull);
  for (const [x, z] of [[-4, 1.2], [-4, -1.2], [5, 1.2], [5, -1.2]]) { const leg = new THREE.Mesh(new THREE.CylinderGeometry(0.25, 0.2, 4.2, 10), bone); leg.position.set(x, 2.0, z); dino.add(leg); }
  dino.position.set(-4, CY1, FLOOR_Z - 12); dino.rotation.y = 0.35; g.add(dino);
  const ast = new THREE.Mesh(new THREE.IcosahedronGeometry(3, 2), clay(0x5a5560, { rimAmt: 0.3 })); const ap = ast.geometry.attributes.position;
  for (let i = 0; i < ap.count; i++) { const v = new THREE.Vector3().fromBufferAttribute(ap, i); v.multiplyScalar(1 + (R() - 0.5) * 0.18); ap.setXYZ(i, v.x, v.y, v.z); } ast.geometry.computeVertexNormals();
  ast.position.set(8, CY1 + 2.6, FLOOR_Z - 10); g.add(ast);
  const tag = labelPlane('THE ASTEROID · taken offline 66,000,000 BC', { h: 0.9, font: FONT.monoB, size: 56, fg: '#ff9cc4', bg: 'rgba(10,8,12,0.78)' }); tag.position.set(8, CY1 + 7.2, FLOOR_Z - 10); g.add(tag);
  g.userData.landing = new THREE.Vector3(3, CY1, FLOOR_Z - 1);
  // green motes in the dark
  const P = 3000, pp = new Float32Array(P * 3); for (let i = 0; i < P; i++) { pp[i * 3] = (R() - 0.5) * 140; pp[i * 3 + 1] = CY1 + R() * 40; pp[i * 3 + 2] = SHAFT_Z + 20 - R() * 220; }
  const pg = new THREE.BufferGeometry(); pg.setAttribute('position', new THREE.BufferAttribute(pp, 3));
  g.add(new THREE.Points(pg, new THREE.PointsMaterial({ color: 0x6dffaa, size: 0.2, map: dotTex(), transparent: true, opacity: 0.7, depthWrite: false, blending: THREE.AdditiveBlending })));
  // the cold shaft of light from the street
  const beam = new THREE.Mesh(new THREE.CylinderGeometry(5, 9, CY0 - CY1, 24, 1, true), new THREE.MeshBasicMaterial({ color: 0x9fd8ff, transparent: true, opacity: 0.045, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide }));
  beam.position.set(0, (CY0 + CY1) / 2, cz); g.add(beam);
  return g;
}
