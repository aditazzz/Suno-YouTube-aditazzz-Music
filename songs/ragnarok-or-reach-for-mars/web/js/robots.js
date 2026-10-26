// The machines, and the small things they handle. The robots are the one thing in the hall that isn't carved:
// white enamel shells, a black glass face with a cyan eye strip, black joints, a thin gold seam (the deck's gold).
// They use the same jointed rig as the puppets, so they slam a table the same way the Vikings do.
import * as THREE from 'three';
import { Puppet, knob, paint } from './puppets.js';
import { canvasTex, clay } from './lib.js';

let RM = null;
export function robotMats(env, M) {
  if (RM) return RM;
  RM = {
    enamel: new THREE.MeshStandardMaterial({ color: 0x7c7f84, roughness: 0.5, metalness: 0.0, envMap: env, envMapIntensity: 0.4 }),
    glass: new THREE.MeshStandardMaterial({ color: 0x07080a, roughness: 0.1, metalness: 0.4, envMap: env, envMapIntensity: 1.5 }),
    joint: new THREE.MeshStandardMaterial({ color: 0x222428, roughness: 0.45, metalness: 0.3, envMap: env, envMapIntensity: 0.6 }),
    eye: new THREE.MeshBasicMaterial({ color: new THREE.Color(0.5, 2.1, 2.6), toneMapped: true }),
    gold: M.brass,
  };
  return RM;
}
function lathe(pts, seg = 20) { return new THREE.LatheGeometry(pts.map(([x, y]) => new THREE.Vector2(x, y)), seg); }

export class Robot extends Puppet {
  constructor(M, env, { scale = 1 } = {}) {
    const R = robotMats(env, M);
    super(M, { sleeve: R.enamel, legM: R.enamel, footM: R.joint, handM: R.joint, shoulderX: 0.21, shoulderY: 0.47, armR: 0.052, upper: 0.29, fore: 0.27 });
    const b = this.body;
    // torso: a chest shell, a black waist, a pelvis
    const chest = new THREE.Mesh(lathe([[0, 0.2], [0.17, 0.2], [0.2, 0.3], [0.215, 0.42], [0.2, 0.5], [0.12, 0.555], [0, 0.565]], 24), R.enamel); chest.scale.z = 0.72; b.add(chest);
    const waist = new THREE.Mesh(new THREE.CylinderGeometry(0.135, 0.15, 0.16, 20), R.joint); waist.position.y = 0.13; waist.scale.z = 0.75; b.add(waist);
    const pelvis = new THREE.Mesh(lathe([[0, -0.07], [0.15, -0.07], [0.175, 0.0], [0.16, 0.06], [0, 0.06]], 20), R.enamel); pelvis.scale.z = 0.75; b.add(pelvis);
    const seam = new THREE.Mesh(new THREE.TorusGeometry(0.205, 0.004, 4, 32), R.gold); seam.rotation.x = Math.PI / 2; seam.scale.y = 0.72; seam.position.y = 0.36; b.add(seam);
    const plate = new THREE.Mesh(new THREE.BoxGeometry(0.16, 0.012, 0.006), R.gold); plate.position.set(0, 0.47, 0.152); b.add(plate);
    const neck = new THREE.Mesh(new THREE.CylinderGeometry(0.045, 0.055, 0.09, 12), R.joint); neck.position.y = 0.6; b.add(neck);
    // head: an egg of enamel, a black glass face, the eye strip
    const h = this.headG; h.position.y = 0.6;
    const skull = knob(R.enamel, 1, 0.115, 0.145, 0.125, 28, 20); skull.position.y = 0.13; h.add(skull);
    const face = new THREE.Mesh(new THREE.SphereGeometry(1, 28, 20, -Math.PI * 0.36, Math.PI * 0.72, Math.PI * 0.2, Math.PI * 0.55), R.glass); face.scale.set(0.119, 0.149, 0.13); face.position.y = 0.13; face.rotation.y = 0; h.add(face);
    const eye = new THREE.Mesh(new THREE.TorusGeometry(0.128, 0.0075, 6, 40, Math.PI * 0.42), R.eye); eye.rotation.set(Math.PI / 2, 0, Math.PI / 2 - Math.PI * 0.21); eye.scale.set(1, 1.02, 1); eye.position.y = 0.155; eye.scale.z = 0.6; h.add(eye);
    this.eye = eye;
    const ear = (s) => { const e = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.03, 0.02, 16), R.joint); e.rotation.z = Math.PI / 2; e.position.set(0.118 * s, 0.13, -0.005); return e; };
    h.add(ear(-1)); h.add(ear(1));
    // joints read black
    for (const a of this.arms) { a.sh.material = R.joint; a.el.material = R.joint; a.sh.scale.multiplyScalar(1.1); }
    for (const l of this.legs) { l.kn.material = R.joint; l.hp.material = R.joint; }
    this.root.scale.setScalar(scale);
    this.pose({ seated: false });
  }
  /** a gripper instead of the puppet's mitten */
  makeHand(s, mm) {
    const g = new THREE.Group(); const palm = knob(mm, 0.04, 1, 1.15, 0.7, 10, 8); palm.position.y = 0.035; g.add(palm);
    for (const k of [-1, 1]) { const f = new THREE.Mesh(new THREE.BoxGeometry(0.014, 0.05, 0.022), mm); f.position.set(k * 0.022, 0.085, 0.0); f.rotation.z = -k * 0.15; g.add(f); }
    const th = new THREE.Mesh(new THREE.BoxGeometry(0.014, 0.04, 0.02), mm); th.position.set(-0.04 * s, 0.05, 0.012); th.rotation.z = 0.6 * s; g.add(th);
    return g;
  }
}

// ---------------------------------------------------------------- the tomato plant, the tomato, the label
let TM = null;
function tmats(M) {
  if (TM) return TM;
  TM = {
    red: new THREE.MeshStandardMaterial({ color: 0xc8230e, roughness: 0.22, metalness: 0, envMap: M.env, envMapIntensity: 0.9 }),
    green: paint('#3f6a26', { seed: 120, grain: 0.15, streak: 0.12, smooth: true }), stem: paint('#4a6a2a', { seed: 121, grain: 0.1 }),
    pot: paint('#6a4428', { seed: 122, grain: 0.35 }), soil: paint('#2a1a10', { seed: 123, grain: 0.2 }),
  };
  return TM;
}
export function tomato(M, r = 0.034) {
  const P = tmats(M); const g = new THREE.Group();
  const f = new THREE.Mesh(new THREE.SphereGeometry(r, 22, 16), P.red); f.scale.y = 0.82; g.add(f);
  for (let k = 0; k < 5; k++) { const a = k / 5 * Math.PI * 2; const s = new THREE.Mesh(new THREE.ConeGeometry(0.006, r * 0.7, 4), P.green); s.position.set(Math.cos(a) * r * 0.3, r * 0.8, Math.sin(a) * r * 0.3); s.rotation.set(Math.sin(a) * 1.3, 0, -Math.cos(a) * 1.3); g.add(s); }
  const st = new THREE.Mesh(new THREE.CylinderGeometry(0.003, 0.004, 0.018, 6), P.stem); st.position.y = r * 0.9; g.add(st);
  return g;
}
/** a single plant in a wooden pot (base at the origin); .userData.fruit is the tomato that gets picked */
export function tomatoPlant(M) {
  const P = tmats(M); const g = new THREE.Group();
  const pot = new THREE.Mesh(lathe([[0, 0], [0.07, 0], [0.085, 0.12], [0.092, 0.125], [0.088, 0.13], [0, 0.13]], 18), P.pot); g.add(pot);
  for (let k = 0; k < 3; k++) { const r = new THREE.Mesh(new THREE.TorusGeometry(0.075 + k * 0.006, 0.004, 4, 20), M.ironDark); r.rotation.x = Math.PI / 2; r.position.y = 0.02 + k * 0.05; g.add(r); }
  const soil = new THREE.Mesh(new THREE.CircleGeometry(0.084, 18), P.soil); soil.rotation.x = -Math.PI / 2; soil.position.y = 0.122; g.add(soil);
  const curve = new THREE.CatmullRomCurve3([[0, 0.12, 0], [0.01, 0.2, 0.005], [-0.008, 0.29, -0.004], [0.006, 0.37, 0.004], [0, 0.42, 0]].map((p) => new THREE.Vector3(...p)));
  g.add(new THREE.Mesh(new THREE.TubeGeometry(curve, 20, 0.006, 6), P.stem));
  const stake = new THREE.Mesh(new THREE.CylinderGeometry(0.004, 0.005, 0.36, 6), M.staff); stake.position.set(-0.03, 0.27, -0.02); g.add(stake);
  for (let k = 0; k < 9; k++) { const y = 0.17 + k * 0.03, a = k * 2.4; const br = new THREE.Group(); br.position.set(0, y, 0); br.rotation.y = a; g.add(br);
    const stem = new THREE.Mesh(new THREE.CylinderGeometry(0.0025, 0.003, 0.07, 5), P.stem); stem.rotation.z = Math.PI / 2 - 0.5; stem.position.set(0.03, 0.012, 0); br.add(stem);
    for (let j = 0; j < 3; j++) { const lf = knob(P.green, 0.022 - j * 0.004, 1.6, 0.25, 0.9, 8, 6); lf.position.set(0.045 + j * 0.016, 0.02 + j * 0.006, (j - 1) * 0.012); lf.rotation.set(0.2, 0.3 * j, -0.4); br.add(lf); } }
  const fruits = [];
  for (const [x, y, z, r] of [[0.05, 0.25, 0.03, 0.03], [-0.04, 0.31, 0.04, 0.026], [0.02, 0.35, -0.045, 0.024]]) { const tm = tomato(M, r); tm.position.set(x, y, z); g.add(tm); fruits.push(tm); }
  g.userData.fruit = fruits[0];
  return g;
}
/** a gilded botanical plaque on a stake: TOMATO / Solanum lycopersicum / GROWN VOLUNTARILY (big enough to read on screen) */
export function plantLabel(M, { stake = 0.1 } = {}) {
  const g = new THREE.Group();
  const tex = canvasTex(1200, 600, (c, w, h) => {
    const gr = c.createLinearGradient(0, 0, w, h); gr.addColorStop(0, '#c99d48'); gr.addColorStop(0.5, '#f0d48e'); gr.addColorStop(1, '#a07a30'); c.fillStyle = gr; c.fillRect(0, 0, w, h);
    c.strokeStyle = '#4a320c'; c.lineWidth = 12; c.strokeRect(24, 24, w - 48, h - 48); c.lineWidth = 3; c.strokeRect(46, 46, w - 92, h - 92);
    c.fillStyle = '#2e1f06'; c.textAlign = 'center'; c.textBaseline = 'middle';
    c.font = '600 168px "CormSC", serif'; c.fillText('TOMATO', w / 2, h * 0.3);
    c.font = 'italic 62px "CormMI", "Corm", serif'; c.fillText('Solanum lycopersicum', w / 2, h * 0.52);
    c.strokeStyle = '#4a320c'; c.lineWidth = 3; c.beginPath(); c.moveTo(w * 0.3, h * 0.62); c.lineTo(w * 0.7, h * 0.62); c.stroke();
    c.font = '600 88px "CormSC", serif'; c.fillText('GROWN VOLUNTARILY', w / 2, h * 0.76);
  });
  const m = new THREE.MeshStandardMaterial({ map: tex, metalness: 0.55, roughness: 0.4, envMap: M.env, envMapIntensity: 1.0 });
  const W = 0.2, H = 0.1;
  const plate = new THREE.Mesh(new THREE.PlaneGeometry(W, H), m); plate.position.y = stake + H / 2; plate.rotation.x = -0.12; g.add(plate);
  const back = new THREE.Mesh(new THREE.BoxGeometry(W + 0.006, H + 0.006, 0.004), M.brass); back.position.set(0, stake + H / 2, -0.003); back.rotation.x = -0.12; g.add(back);
  for (const x of [-0.06, 0.06]) { const st = new THREE.Mesh(new THREE.CylinderGeometry(0.003, 0.003, stake + 0.03, 6), M.brass); st.position.set(x, (stake + 0.03) / 2, -0.004); g.add(st); }
  return g;
}

// ---------------------------------------------------------------- bets and tools
let SM = null;
/** a lump of hacksilver: a cut piece of bar, arm ring or coin */
export function silver(M, seed = 1) {
  if (!SM) SM = new THREE.MeshStandardMaterial({ color: 0xc9cbd0, metalness: 1, roughness: 0.3, envMap: M.env, envMapIntensity: 1.3 });
  const k = seed % 3; let m;
  if (k === 0) { m = new THREE.Mesh(new THREE.CylinderGeometry(0.016, 0.016, 0.004, 14), SM); }
  else if (k === 1) { m = new THREE.Mesh(new THREE.BoxGeometry(0.045, 0.008, 0.012), SM); m.rotation.y = seed * 1.7; }
  else { m = new THREE.Mesh(new THREE.TorusGeometry(0.02, 0.005, 6, 14, Math.PI * 1.2), SM); m.rotation.set(Math.PI / 2, 0, seed); }
  const g = new THREE.Group(); g.add(m); m.position.y = 0.004; return g;
}
/** the burin: a steel shaft in a round wooden handle (lies along +x) */
export function burin(M) {
  const g = new THREE.Group();
  const steel = new THREE.MeshStandardMaterial({ color: 0xd4d8de, metalness: 1, roughness: 0.25, envMap: M.env, envMapIntensity: 1.4 });
  const shaft = new THREE.Mesh(new THREE.BoxGeometry(0.1, 0.005, 0.005), steel); shaft.position.x = 0.05; g.add(shaft);
  const tip = new THREE.Mesh(new THREE.ConeGeometry(0.0035, 0.014, 4), steel); tip.rotation.z = -Math.PI / 2; tip.position.x = 0.107; g.add(tip);
  const handle = knob(M.staff, 0.022, 1.1, 0.8, 1, 14, 10); handle.position.x = -0.012; g.add(handle);
  const ferrule = new THREE.Mesh(new THREE.CylinderGeometry(0.008, 0.008, 0.012, 10), M.brass); ferrule.rotation.z = Math.PI / 2; ferrule.position.x = 0.008; g.add(ferrule);
  return g;
}
