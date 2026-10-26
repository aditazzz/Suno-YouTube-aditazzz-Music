// The hall: a Viking longhouse at night. A long hearth down the middle, two rows of carved posts, raised platforms
// along the walls where the Vikings sit, shields and hangings, a smoke hole that lets a shaft of moonlight in, the
// seeress's high seat and the reading table at the far end, and the great doors behind her that open for the finale.
import * as THREE from 'three';
import { clay, canvasTex, rng, clamp } from './lib.js';
import { woodTex, noise2, hex, shieldTex } from './lib2.js';
import { hearthFire, flame } from './fire.js';
import { paint, paintTex, knob } from './puppets.js';
import { horn, cup, platter, candle } from './props.js';

export const HALL = { W: 9, wallH: 2.6, ridge: 7.2, z0: -13, z1: 13, hearth: { z: 0.8, len: 7, wid: 1.3 },
  dais: { z: -6.85, y: 0.1, w: 2.6, d: 1.3 }, seat: { z: -6.78, y: 0.1 }, table: { z: -5.95, r: 0.42, top: 0.756 }, stool: { z: -5.2 },
  feast: { x: 1.72, z0: -3.2, z1: 9.7, top: 0.74, w: 0.72 }, bench: { x: 2.3 }, doors: { z: -12.9, w: 2.8, h: 3.0 }, seats: [] };
// two Vikings between each pair of posts, on both sides, facing the hearth
for (const s of [-1, 1]) for (const z of [-2.35, -1.15, 1.15, 2.35, 4.65, 5.85, 8.15, 9.35]) HALL.seats.push({ x: s * HALL.bench.x, z, side: s });
const H = HALL;

function vtex(tex) { tex.center.set(0.5, 0.5); tex.rotation = Math.PI / 2; return tex; }
function earthTex() {
  const N = noise2(17);
  return canvasTex(512, 512, (g, w, h) => { const img = g.createImageData(w, h); const d = img.data;
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) { const v = N.fbm(x / 60, y / 60, 5), s = N(x / 4, y / 4);
      const k = 0.55 + 0.6 * (v - 0.5) + 0.12 * (s - 0.5); const i = (y * w + x) * 4; d[i] = 70 * k; d[i + 1] = 50 * k; d[i + 2] = 36 * k; d[i + 3] = 255; }
    g.putImageData(img, 0, 0);
    const R = rng(4); for (let i = 0; i < 260; i++) { g.fillStyle = `rgba(${150 + R() * 60},${120 + R() * 50},${80 + R() * 40},${0.12 + R() * 0.15})`; g.beginPath(); g.ellipse(R() * w, R() * h, 2 + R() * 6, 1 + R() * 3, R() * 3, 0, 6.3); g.fill(); }   // straw and grit
  }, { repeat: [3, 9] });
}
function hangingTex(seed, c1, c2, c3) {   // a woven wall hanging: bands of interlace and stepped diamonds
  const R = rng(seed);
  return canvasTex(256, 512, (g, w, h) => { g.fillStyle = c1; g.fillRect(0, 0, w, h);
    for (let y = 0; y < h; y += 4) { g.fillStyle = `rgba(0,0,0,${0.05 + R() * 0.06})`; g.fillRect(0, y, w, 2); }
    const band = (y0, hh, col) => { g.fillStyle = col; g.fillRect(14, y0, w - 28, hh); };
    for (let k = 0; k < 4; k++) { const y0 = 40 + k * 118; band(y0, 10, c2); band(y0 + 78, 10, c2);
      for (let i = 0; i < 5; i++) { const cx = 30 + i * 49, cy = y0 + 49; g.fillStyle = k % 2 ? c3 : c2; g.beginPath(); g.moveTo(cx, cy - 26); g.lineTo(cx + 22, cy); g.lineTo(cx, cy + 26); g.lineTo(cx - 22, cy); g.closePath(); g.fill();
        g.fillStyle = c1; g.beginPath(); g.moveTo(cx, cy - 12); g.lineTo(cx + 10, cy); g.lineTo(cx, cy + 12); g.lineTo(cx - 10, cy); g.closePath(); g.fill(); } }
    g.fillStyle = c2; for (let x = 18; x < w - 10; x += 16) g.fillRect(x, h - 18, 6, 18);
  });
}
function box(w, h, d, mat, x, y, z) { const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat); m.position.set(x, y, z); return m; }

export function buildHall(env, M) {
  const g = new THREE.Group(); const R = rng(9); const ups = [];
  const dark = (base, seed, o = {}) => clay(0xffffff, { map: woodTex({ w: 256, h: 256, base, dark: o.dk || '#140c06', light: o.lt || '#4a321e', seed, repeat: o.repeat || [1, 1], planks: o.planks || 0 }) });
  const postM = dark('#3a2414', 31, { repeat: [1, 3] }), beamM = dark('#2a1a0e', 32, { repeat: [4, 1] }), wallM = clay(0xffffff, { map: vtex(woodTex({ w: 512, h: 512, base: '#3a2616', dark: '#170e07', light: '#53382a', seed: 33, planks: 8, repeat: [10, 1] })) });
  const roofM = clay(0xffffff, { map: woodTex({ w: 256, h: 256, base: '#1e140b', dark: '#0b0704', light: '#2e2014', seed: 34, planks: 6, repeat: [8, 3] }), side: THREE.DoubleSide });
  const plankM = clay(0xffffff, { map: woodTex({ w: 512, h: 512, base: '#4a3020', dark: '#1e130a', light: '#6a4a30', seed: 35, planks: 5, repeat: [1, 6] }) });

  // ---- floor, walls, roof
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(H.W, H.z1 - H.z0), clay(0xffffff, { map: earthTex(), rimAmt: 0 })); floor.rotation.x = -Math.PI / 2; floor.receiveShadow = true; g.add(floor);
  for (const s of [-1, 1]) { const w = new THREE.Mesh(new THREE.PlaneGeometry(H.z1 - H.z0, H.wallH), wallM); w.position.set(s * H.W / 2, H.wallH / 2, 0); w.rotation.y = -s * Math.PI / 2; w.receiveShadow = true; g.add(w); }
  const gable = new THREE.Shape(); gable.moveTo(-H.W / 2, 0); gable.lineTo(H.W / 2, 0); gable.lineTo(H.W / 2, H.wallH); gable.lineTo(0, H.ridge); gable.lineTo(-H.W / 2, H.wallH); gable.closePath();
  const dw = H.doors.w, dh = H.doors.h; const hole = new THREE.Path(); hole.moveTo(-dw / 2, 0.001); hole.lineTo(dw / 2, 0.001); hole.lineTo(dw / 2, dh); hole.lineTo(-dw / 2, dh); hole.closePath();
  const farG = new THREE.ShapeGeometry(Object.assign(gable.clone(), { holes: [hole] })); const near = new THREE.Mesh(new THREE.ShapeGeometry(gable), wallM); near.position.z = H.z1; near.rotation.y = Math.PI; g.add(near);
  const far = new THREE.Mesh(farG, wallM); far.position.z = H.z0; g.add(far);
  for (const gg of [farG, near.geometry]) { const p = gg.attributes.position, uv = gg.attributes.uv; for (let i = 0; i < p.count; i++) uv.setXY(i, p.getX(i) / 4, p.getY(i) / 4); }
  const slope = Math.hypot(H.W / 2, H.ridge - H.wallH), ang = Math.atan2(H.ridge - H.wallH, H.W / 2);
  const hz0 = H.hearth.z - 0.9, hz1 = H.hearth.z + 0.9;                       // the smoke hole over the hearth
  const slopeBasis = (s) => { const d = new THREE.Vector3(-s * Math.cos(ang), Math.sin(ang), 0), x = new THREE.Vector3(0, 0, 1); const n = new THREE.Vector3().crossVectors(x, d);
    return { d, q: new THREE.Quaternion().setFromRotationMatrix(new THREE.Matrix4().makeBasis(x, d, n)), n }; };
  for (const s of [-1, 1]) { const { d, q } = slopeBasis(s);
    for (const [a, b, cut] of [[H.z0, hz0, 0], [hz0, hz1, 0.8], [hz1, H.z1, 0]]) {
      const len = b - a, sl = slope - cut; const r = new THREE.Mesh(new THREE.PlaneGeometry(len, sl), roofM);
      r.quaternion.copy(q); r.position.set(s * H.W / 2, H.wallH, (a + b) / 2).add(d.clone().multiplyScalar(sl / 2)); r.receiveShadow = true; g.add(r);
    } }
  // ---- structure: two rows of carved posts, purlins, tie beams, rafters, the ridge
  const postZ = [-10.5, -7, -3.5, 0, 3.5, 7, 10.5], px = 2.6, py = H.wallH + (H.W / 2 - px) / (H.W / 2) * (H.ridge - H.wallH);
  const bandM = dark('#5a3a22', 36);
  for (const s of [-1, 1]) {
    for (const z of postZ) {
      const p = new THREE.Mesh(new THREE.CylinderGeometry(0.13, 0.16, py, 8), postM); p.position.set(s * px, py / 2, z); p.castShadow = true; p.receiveShadow = true; g.add(p);
      for (const y of [0.9, 1.05, py - 0.5]) { const r = new THREE.Mesh(new THREE.TorusGeometry(0.155, 0.035, 5, 10), bandM); r.rotation.x = Math.PI / 2; r.position.set(s * px, y, z); g.add(r); }
      const cap = box(0.42, 0.18, 0.42, beamM, s * px, py - 0.09, z); g.add(cap);
    }
    const purlin = box(0.24, 0.26, H.z1 - H.z0, beamM, s * px, py + 0.13, 0); g.add(purlin);
    const plate = box(0.22, 0.2, H.z1 - H.z0, beamM, s * (H.W / 2 - 0.12), H.wallH, 0); g.add(plate);
  }
  for (const z of postZ) { const tb = box(px * 2, 0.24, 0.22, beamM, 0, py - 0.35, z); tb.castShadow = true; g.add(tb); }
  for (let z = H.z0 + 0.6; z < H.z1; z += 1.6) for (const s of [-1, 1]) {
    if (z > hz0 - 0.1 && z < hz1 + 0.1) continue;
    const { d, q, n } = slopeBasis(s); const rf = new THREE.Mesh(new THREE.BoxGeometry(0.18, slope, 0.14), beamM); rf.quaternion.copy(q);
    rf.position.set(s * H.W / 2, H.wallH, z).add(d.clone().multiplyScalar(slope / 2)).add(n.clone().multiplyScalar(s > 0 ? 0.08 : -0.08)); g.add(rf);
  }
  g.add(box(0.26, 0.3, H.z1 - H.z0, beamM, 0, H.ridge - 0.3, 0));
  // ---- platforms along the walls (the Vikings sit on their front edge)
  for (const s of [-1, 1]) {
    const top = box(1.5, 0.08, H.z1 - H.z0 - 1, plankM, s * (H.W / 2 - 0.75), 0.42, 0); top.receiveShadow = true; g.add(top);
    const front = box(0.06, 0.42, H.z1 - H.z0 - 1, plankM, s * (H.W / 2 - 1.5), 0.21, 0); front.receiveShadow = true; g.add(front);
  }
  // ---- the feast: a long trestle table and a bench down each side of the hearth, set with horns, cups and platters
  const tableM = clay(0xffffff, { map: woodTex({ w: 512, h: 256, base: '#5a3a22', dark: '#24160c', light: '#7a5434', seed: 42, planks: 3, repeat: [6, 1] }) });
  const F = H.feast, flen = F.z1 - F.z0, fz = (F.z0 + F.z1) / 2; const propsAll = [];
  for (const s of [-1, 1]) {
    const top = box(F.w, 0.06, flen, tableM, s * F.x, F.top - 0.03, fz); top.receiveShadow = true; top.castShadow = true; g.add(top);
    for (let z = F.z0 + 0.5; z < F.z1; z += 2.2) { const leg = box(0.08, F.top - 0.06, F.w * 0.8, tableM, s * F.x, (F.top - 0.06) / 2, z); leg.castShadow = true; g.add(leg); }
    const bench = box(0.36, 0.06, flen, plankM, s * H.bench.x, 0.42, fz); bench.receiveShadow = true; g.add(bench);
    for (let z = F.z0 + 0.4; z < F.z1; z += 2.4) g.add(box(0.06, 0.39, 0.3, plankM, s * H.bench.x, 0.195, z));
  }
  const PR = rng(77); let pi = 0;
  for (const st of H.seats) {   // in front of each seat: a cup or a horn; every other seat shares a platter; a candle now and then
    const tx = st.side * (F.x + 0.16), tz = st.z;
    if (pi % 3 === 1) { const h = horn(M, 0.26 + PR() * 0.06, pi); h.position.set(tx - st.side * 0.02, F.top + 0.012, tz + 0.12); h.rotation.set(0, st.side > 0 ? Math.PI * 0.5 + 0.4 : -Math.PI * 0.5 - 0.4, 0); h.rotation.z = 0.0; h.rotateX(-Math.PI / 2 + 0.25); h.scale.setScalar(0.9); g.add(h); propsAll.push(h); }
    else { const c = cup(M, pi); c.position.set(tx, F.top, tz + 0.15); g.add(c); propsAll.push(c); }
    if (pi % 2 === 0) { const p2 = platter(M, pi); p2.position.set(st.side * (F.x - 0.12), F.top, tz + 0.6); p2.rotation.y = PR() * 3; g.add(p2); propsAll.push(p2); }
    if (pi % 4 === 3) { const cd = candle(M, 0.12 + PR() * 0.06, pi); cd.position.set(st.side * (F.x - 0.2), F.top, tz - 0.55); g.add(cd); ups.push(cd.userData.flame); propsAll.push(cd);
      const fl = cd.userData.flame; ups.push({ userData: { update: () => { fl.visible = CTL.candle > 0.02; } } }); }
    pi++;
  }
  for (const pr of propsAll) { pr.userData.dynamic = true; pr.userData.base = pr.position.clone(); pr.userData.side = Math.sign(pr.position.x); pr.traverse((o) => { if (o.isMesh && !o.material.isShaderMaterial) { o.castShadow = true; o.receiveShadow = true; } }); }
  g.userData.feastProps = propsAll;
  // ---- shields and hangings
  const cols = [['#8a1c14', '#d8c08a'], ['#1f3a6a', '#e0c27a'], ['#d8b84a', '#2a2622'], ['#2e5a34', '#d6cbb4'], ['#6a1a14', '#1a1a1a'], ['#e0d6c0', '#8a1c14']];
  const bossM = new THREE.MeshStandardMaterial({ color: 0x8a8e95, metalness: 0.85, roughness: 0.35, envMap: env });
  let k = 0;
  for (const s of [-1, 1]) for (let z = H.z0 + 2.2; z < H.z1 - 1.5; z += 1.75) {
    if (Math.abs(z - H.hearth.z) < 0.5) continue;
    const [c1, c2] = cols[k++ % cols.length]; const sh = new THREE.Mesh(new THREE.CircleGeometry(0.42, 28), clay(0xffffff, { map: shieldTex(c1, c2, k, ['quarters', 'halves', 'whirl', 'ring'][k % 4]) }));
    sh.position.set(s * (H.W / 2 - 0.04), 1.55 + (k % 2) * 0.12, z); sh.rotation.y = -s * Math.PI / 2; sh.rotation.z = R() * 3; g.add(sh);
    const boss = new THREE.Mesh(new THREE.SphereGeometry(0.08, 12, 6, 0, Math.PI * 2, 0, Math.PI / 2), bossM); boss.position.copy(sh.position).add(new THREE.Vector3(-s * 0.01, 0, 0)); boss.rotation.z = s * Math.PI / 2; g.add(boss);
  }
  for (const s of [-1, 1]) { const hg = new THREE.Mesh(new THREE.PlaneGeometry(1.4, 2.8), clay(0xffffff, { map: hangingTex(40 + s, s < 0 ? '#5a1a14' : '#1e2e5a', '#d0a040', s < 0 ? '#1e2e5a' : '#7a1c14') })); hg.position.set(s * 2.75, 2.75, H.z0 + 0.05); g.add(hg);
    const rod = box(1.6, 0.05, 0.05, beamM, s * 2.75, 4.18, H.z0 + 0.08); g.add(rod); }
  // ---- the hearth: a kerb of stones round a bed of embers, a long fire, sparks
  const stoneM = clay(0xffffff, { map: paintTex('#4c463e', { seed: 37, grain: 0.0, streak: 0.12 }), flatShading: true, rimAmt: 0.02 });
  const hl = H.hearth.len, hw = H.hearth.wid;
  for (let i = 0; i < 84; i++) { const t = i / 84; let x, z; const per = 2 * (hl + hw), d = t * per;
    if (d < hl) { x = -hw / 2; z = -hl / 2 + d; } else if (d < hl + hw) { x = -hw / 2 + (d - hl); z = hl / 2; } else if (d < 2 * hl + hw) { x = hw / 2; z = hl / 2 - (d - hl - hw); } else { x = hw / 2 - (d - 2 * hl - hw); z = -hl / 2; }
    const st = new THREE.Mesh(new THREE.IcosahedronGeometry(1, 0), stoneM); st.scale.set(0.11 + R() * 0.06, 0.08 + R() * 0.05, 0.11 + R() * 0.06); st.rotation.set(R() * 3, R() * 3, R() * 3);
    st.position.set(x, 0.06, z + H.hearth.z); st.receiveShadow = true; g.add(st); }
  const fire = hearthFire(hl, hw, { lights: 3, intensity: 150, shadow: true, flames: 9 }); fire.position.z = H.hearth.z; fire.userData.dynamic = true; g.add(fire); ups.push(fire);
  // ---- torches on the posts nearest the reading
  const torchM = clay(0x2a1a10); const CTL = { torch: [1, 1, 1, 1], stand: 1, candle: 1, fill: 1 }; const torchF = [];
  for (const [s, z] of [[-1, -7], [1, -7], [-1, -3.5], [1, -3.5]]) {
    const t = new THREE.Group(); t.position.set(s * (px - 0.2), 2.0, z); t.userData.dynamic = true; g.add(t);
    const stick = new THREE.Mesh(new THREE.CylinderGeometry(0.025, 0.02, 0.45, 6), torchM); stick.rotation.z = -s * 0.35; t.add(stick);
    const f = flame(0.2, 0.36, 20 + z + s, 0.95); f.position.set(-s * 0.08, 0.2, 0); t.add(f); ups.push(f); torchF.push(f);
  }
  for (const s of [-1, 1]) {   // one light per side for each pair of torches (cheaper than four)
    const l = new THREE.PointLight(0xffa050, 8.5, 0, 2); l.position.set(s * (px - 0.32), 2.45, -5.25); g.add(l);
    const ia = s < 0 ? 0 : 1, ib = s < 0 ? 2 : 3;
    ups.push({ userData: { update: (tt) => { l.intensity = 8.5 * (0.86 + 0.09 * Math.sin(tt * 9 + s) + 0.05 * Math.sin(tt * 17 + 2 * s)) * (CTL.torch[ia] + CTL.torch[ib]) / 2; } } });
  }
  ups.push({ userData: { update: () => { torchF.forEach((f, i) => { const k = CTL.torch[i]; f.visible = k > 0.02; f.scale.setScalar(k >= 1 ? 1 : 0.35 + 0.65 * k); }); } } });
  g.userData.torches = [];
  // ---- moonlight through the smoke hole: a cool spot and a visible shaft in the smoke
  const back = new THREE.DirectionalLight(0x8fa8ff, 0.35); back.position.set(0, 6, -16); back.target.position.set(0, 0, -3); g.add(back); g.add(back.target);
  const moon = new THREE.SpotLight(0x8fb0ff, 18, 0, 0.32, 0.9, 2); moon.position.set(0.4, H.ridge + 1.5, H.hearth.z); moon.target.position.set(0, 0, H.hearth.z - 0.8); g.add(moon); g.add(moon.target);
  const shaftM = new THREE.ShaderMaterial({ transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide, uniforms: { uTime: { value: 0 } },
    vertexShader: 'varying vec2 vUv; varying vec3 vP; void main(){ vUv = uv; vP = position; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }',
    fragmentShader: `uniform float uTime; varying vec2 vUv; varying vec3 vP;
      float h(vec2 p){ return fract(sin(dot(p, vec2(12.9898,78.233))) * 43758.5453); }
      float n(vec2 p){ vec2 i = floor(p), f = fract(p); f = f*f*(3.0-2.0*f); return mix(mix(h(i), h(i+vec2(1,0)), f.x), mix(h(i+vec2(0,1)), h(i+vec2(1,1)), f.x), f.y); }
      void main(){ float e = sin(vUv.x * 3.14159); float d = n(vec2(vUv.x * 6.0, vUv.y * 3.0 - uTime * 0.15)) * 0.6 + n(vec2(vUv.x * 14.0 + 3.0, vUv.y * 7.0 + uTime * 0.1)) * 0.4;
        float a = pow(e, 2.0) * (0.35 + 0.65 * d) * smoothstep(0.0, 0.35, vUv.y) * (0.55 + 0.45 * vUv.y) * 0.16; gl_FragColor = vec4(vec3(0.55, 0.68, 1.0) * a, a); }` });
  const shaft = new THREE.Mesh(new THREE.CylinderGeometry(0.7, 1.25, H.ridge, 24, 1, true), shaftM); shaft.position.set(0.15, H.ridge / 2, H.hearth.z - 0.3); shaft.rotation.z = 0.04; g.add(shaft);
  ups.push({ userData: { update: (t) => { shaftM.uniforms.uTime.value = t; } } });
  // ---- the dais, the high seat, the reading table, the stool
  const dais = box(H.dais.w, H.dais.y, H.dais.d, plankM, 0, H.dais.y / 2, H.dais.z); dais.receiveShadow = true; dais.castShadow = true; g.add(dais);
  const chair = new THREE.Group(); chair.position.set(0, H.dais.y, H.seat.z); g.add(chair);
  const seatM = dark('#4a2c18', 38);
  chair.add(box(0.66, 0.07, 0.5, seatM, 0, 0.445, -0.02)); chair.add(box(0.7, 1.1, 0.07, seatM, 0, 0.98, -0.3));
  for (const s of [-1, 1]) { chair.add(box(0.07, 0.44, 0.46, seatM, s * 0.33, 0.22, -0.02)); const pst = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.06, 1.8, 8), seatM); pst.position.set(s * 0.38, 0.9, -0.3); chair.add(pst);
    const head = knob(M.brass, 0.07, 1, 1.2, 1.4, 12, 9); head.position.set(s * 0.38, 1.86, -0.26); chair.add(head); }
  const pelt = new THREE.Mesh(new THREE.BoxGeometry(0.62, 0.04, 0.46), M.fur); pelt.position.set(0, 0.49, -0.02); chair.add(pelt);
  shadowAll(chair);
  const table = new THREE.Group(); table.position.set(0, 0, H.table.z); g.add(table);
  const tr = H.table.r;
  const top = new THREE.Mesh(new THREE.CylinderGeometry(tr, tr, 0.06, 28), seatM); top.position.y = 0.72; table.add(top);
  const ped = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.15, 0.7, 10), seatM); ped.position.y = 0.36; table.add(ped);
  const clothM = clay(0xffffff, { map: paintTex('#3a0f0c', { seed: 39, grain: 0.0, streak: 0.18 }) });
  const cloth = new THREE.Mesh(new THREE.CylinderGeometry(tr + 0.035, tr + 0.09, 0.2, 32, 1, true), clothM); cloth.material.side = THREE.DoubleSide; cloth.position.y = 0.656; table.add(cloth);
  const clothTop = new THREE.Mesh(new THREE.CircleGeometry(tr + 0.035, 32), clothM); clothTop.rotation.x = -Math.PI / 2; clothTop.position.y = H.table.top; table.add(clothTop);
  const waxM = clay(0xe8dcc0, { emissive: 0x3a2008 }), ironS = clay(0x1e1d1f);
  for (const sx of [-1, 1]) {
    const stand = new THREE.Group(); stand.position.set(sx * 0.95, H.dais.y, H.seat.z - 0.05); g.add(stand);
    const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.014, 0.018, 1.1, 8), ironS); pole.position.y = 0.55; stand.add(pole);
    for (const a of [0, 2.1, 4.2]) { const leg = new THREE.Mesh(new THREE.CylinderGeometry(0.01, 0.012, 0.3, 6), ironS); leg.position.set(Math.cos(a) * 0.1, 0.1, Math.sin(a) * 0.1); leg.rotation.set(Math.sin(a) * 0.6, 0, -Math.cos(a) * 0.6); stand.add(leg); }
    const dish = new THREE.Mesh(new THREE.CylinderGeometry(0.11, 0.06, 0.03, 16), ironS); dish.position.y = 1.1; stand.add(dish);
    for (const [cx, cz, hh] of [[0, 0, 0.16], [0.06, 0.04, 0.11], [-0.05, 0.05, 0.13]]) { const c = new THREE.Mesh(new THREE.CylinderGeometry(0.02, 0.022, hh, 10), waxM); c.position.set(cx, 1.115 + hh / 2, cz); stand.add(c);
      const f = flame(0.05, 0.1, 30 + sx * 7 + cx * 50, 1.0); f.position.set(cx, 1.115 + hh, cz); stand.add(f); ups.push(f); ups.push({ userData: { update: () => { f.visible = CTL.stand > 0.02; } } }); }
    const L = new THREE.PointLight(0xffb060, 0.85, 0, 2); L.position.set(0, 1.62, 0.02); stand.add(L);
    ups.push({ userData: { update: (tt) => { L.intensity = 0.85 * (0.9 + 0.06 * Math.sin(tt * 11 + sx) + 0.04 * Math.sin(tt * 23.3 + sx * 2)) * CTL.stand; } } });
    shadowAll(stand); stand.traverse((o) => { if (o.isMesh) o.castShadow = false; });
  }
  const fill = new THREE.PointLight(0xffa860, 0.55, 3.2, 2); fill.position.set(0, 1.9, H.table.z); g.add(fill);    // the candles' warmth pooled on the reading table
  ups.push({ userData: { update: (tt) => { fill.intensity = 0.55 * (0.93 + 0.04 * Math.sin(tt * 8.3) + 0.03 * Math.sin(tt * 19.1)) * CTL.fill; } } });
  shadowAll(table);
  const stool = new THREE.Group(); stool.position.set(0, 0, H.stool.z); g.add(stool);
  stool.add(box(0.46, 0.06, 0.38, seatM, 0, 0.45, 0)); for (const [x, z] of [[-0.18, -0.14], [0.18, -0.14], [-0.18, 0.14], [0.18, 0.14]]) stool.add(box(0.05, 0.43, 0.05, seatM, x, 0.215, z));
  shadowAll(stool);
  // ---- the doors (closed; open(k) swings them out onto the night)
  const doorM = clay(0xffffff, { map: vtex(woodTex({ w: 256, h: 256, base: '#4a3020', dark: '#1a100a', light: '#6a4a30', seed: 41, planks: 5 })) }), ironM = clay(0x1c1c20);
  const doors = []; for (const s of [-1, 1]) { const piv = new THREE.Group(); piv.position.set(s * dw / 2, 0, H.z0 - 0.02); piv.userData.dynamic = true; g.add(piv);
    const leaf = box(dw / 2, dh, 0.1, doorM, -s * dw / 4, dh / 2, 0); piv.add(leaf);
    for (const y of [0.5, 1.5, 2.5]) piv.add(box(dw / 2 - 0.1, 0.07, 0.03, ironM, -s * dw / 4, y, 0.07));
    const ring = new THREE.Mesh(new THREE.TorusGeometry(0.08, 0.015, 6, 16), ironM); ring.position.set(-s * (dw / 2 - 0.25), 1.35, 0.1); piv.add(ring); doors.push([piv, s]); }
  g.add(box(0.3, dh + 0.3, 0.3, beamM, -dw / 2 - 0.15, (dh + 0.3) / 2, H.z0)); g.add(box(0.3, dh + 0.3, 0.3, beamM, dw / 2 + 0.15, (dh + 0.3) / 2, H.z0)); g.add(box(dw + 0.6, 0.3, 0.3, beamM, 0, dh + 0.15, H.z0));
  g.userData.openDoors = (k) => { for (const [piv, s] of doors) piv.rotation.y = s * k * 1.75; };
  // ---- everything that moves
  g.userData.fire = fire; g.userData.moon = moon; g.userData.ctl = CTL; g.userData.back = back; g.userData.shaft = shaft;
  shaftM.uniforms.uFlash = { value: 0 };
  shaftM.fragmentShader = shaftM.fragmentShader.replace('uniform float uTime;', 'uniform float uTime, uFlash;').replace('* 0.16; gl_FragColor', '* (0.16 + 1.4 * uFlash); gl_FragColor');
  CTL.moon = 1; g.userData.flash = (k) => { moon.intensity = 18 * CTL.moon + 900 * k; moon.angle = 0.32 + 0.25 * Math.min(1, k); shaftM.uniforms.uFlash.value = k; };
  g.userData.update = (t, cam, Hpx, fov) => { for (const u of ups) u.userData.update(t, cam, Hpx, fov); };
  g.traverse((o) => { if (o.isMesh && o.material && !o.material.isShaderMaterial && o.castShadow === false && o !== floor) o.receiveShadow = true; });
  return g;
}
function shadowAll(o) { o.traverse((m) => { if (m.isMesh) { m.castShadow = true; m.receiveShadow = true; } }); }
