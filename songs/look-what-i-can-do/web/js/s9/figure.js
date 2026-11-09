// Figures on one rig (after the clay mannequins of "I have a blocker."): hips with the legs, a torso that leans, arms and
// legs posed with two-bone IK (give each hand and foot a target). Limbs are cylinders between ball joints of the same
// radius, so a chain reads as one smooth limb. Woman: the narrator, in her camel trench coat. The robot builds on it too.
import * as THREE from 'three';
import { clay, gloss, lerp, clamp, sstep, V3, rbox, lathe, rng } from './lib.js';
import { Hair } from './hair.js';

const UP = new THREE.Vector3(0, 1, 0);
const _v = new THREE.Vector3(), _w = new THREE.Vector3();
export const GEO = { sph: new THREE.SphereGeometry(1, 24, 16), cyl: new THREE.CylinderGeometry(1, 1, 1, 18, 1, true) };

export function limb(mat, r) { const g = new THREE.Group(); const c = new THREE.Mesh(GEO.cyl, mat); c.scale.set(r, 1, r); g.add(c); g.userData = { c, r }; return g; }
export function placeLimb(l, a, b) {
  const len = a.distanceTo(b); l.position.copy(a).add(b).multiplyScalar(0.5);
  _v.copy(b).sub(a); if (len > 1e-6) { _v.divideScalar(len); l.quaternion.setFromUnitVectors(UP, _v); }
  l.userData.c.scale.y = Math.max(0.001, len);
}
export function ball(mat, r, sx = 1, sy = 1, sz = 1) { const m = new THREE.Mesh(GEO.sph, mat); m.scale.set(r * sx, r * sy, r * sz); return m; }
/** two-bone IK: from S toward T with bone lengths a, b; the bend goes toward `pole`. Writes the elbow/knee to outE and
 *  returns the reachable end point (T, or clamped onto the S->T line). */
export function ik(S, T, a, b, pole, outE, outEnd) {
  const dist = S.distanceTo(T); const d = Math.min(a + b - 1e-4, Math.max(Math.abs(a - b) + 1e-4, dist));
  const dir = _w.copy(T).sub(S).normalize();
  const cosA = (a * a + d * d - b * b) / (2 * a * d); const sinA = Math.sqrt(Math.max(0, 1 - cosA * cosA));
  const p = pole.clone().sub(dir.clone().multiplyScalar(pole.dot(dir))); if (p.lengthSq() < 1e-8) p.set(0, 0, 1); p.normalize();
  outE.copy(S).addScaledVector(dir, a * cosA).addScaledVector(p, a * sinA);
  if (outEnd) outEnd.copy(S).addScaledVector(dir, d);
  return d;
}

export class Figure {
  /** o: dims and materials. sleeve, upperM, handM, thighM, shinM, footM, jointM; shoulderX, shoulderY, armR, foreR, upper, fore,
   *  hipX, thigh, shin, legR, shinR, standH (hip height standing), seatH (hip height seated) */
  constructor(o) {
    this.o = o = { shoulderX: 0.2, shoulderY: 0.46, armR: 0.055, foreR: 0.048, upper: 0.28, fore: 0.26, hipX: 0.095, thigh: 0.43, shin: 0.43, legR: 0.075, shinR: 0.06,
      standH: 0.9, seatH: 0.5, ...o };
    this.root = new THREE.Group(); this.hips = new THREE.Group(); this.root.add(this.hips);
    this.torso = new THREE.Group(); this.hips.add(this.torso);
    this.headG = new THREE.Group(); this.torso.add(this.headG);
    this.arms = [-1, 1].map((s) => {
      const up = limb(o.upperM || o.sleeve, o.armR), fo = limb(o.sleeve, o.foreR), sh = ball(o.jointM || o.upperM || o.sleeve, o.armR * (o.shK ?? 1.15)), el = ball(o.jointM || o.sleeve, o.foreR * 1.05);
      const hand = this.makeHand(s, o.handM); const handG = new THREE.Group(); handG.add(hand);
      [up, fo, sh, el, handG].forEach((m) => this.torso.add(m));
      return { s, up, fo, sh, el, hand: handG, S: V3(o.shoulderX * s, o.shoulderY, 0), E: V3(), H: V3(), dir: V3() };
    });
    this.legs = [-1, 1].map((s) => {
      const th = limb(o.thighM, o.legR), sh = limb(o.shinM || o.thighM, o.shinR), kn = ball(o.jointM || o.shinM || o.thighM, o.shinR * 1.12), hp = ball(o.thighM, o.legR * 1.1);
      const foot = this.makeFoot(s, o.footM);
      [th, sh, kn, hp, foot].forEach((m) => this.hips.add(m)); return { s, th, sh, kn, hp, foot, K: V3(), A: V3() };
    });
    this.P = {};
  }
  makeHand(s, m) { const g = new THREE.Group(); const palm = ball(m, 0.048, 1, 1.25, 0.7); palm.position.y = 0.04; g.add(palm);
    const th = ball(m, 0.018, 1, 2.2, 1); th.position.set(-0.035 * s, 0.035, 0.018); th.rotation.z = 0.5 * s; g.add(th); return g; }
  makeFoot(s, m) { const f = new THREE.Mesh(new THREE.CapsuleGeometry(0.045, 0.12, 6, 12), m); f.rotation.x = Math.PI / 2; return f; }
  /** p: x, z, y (root), turn, seat (1 seated .. 0 standing), lean, roll, twist, headYaw, headPitch, headRoll,
   *  hands: [[x,y,z],[x,y,z]] torso space (left, right), handRot: [[rx,ry,rz],..] extra hand rotation,
   *  walk (phase, rad), stride (0..1), feet: [[x,y,z],..] hips-space override, kneeOut */
  pose(p) {
    const o = this.o; this.P = p;
    const seat = p.seat ?? 1, stride = p.stride ?? 0, ph = p.walk ?? 0;
    const hipY = lerp(o.standH, o.seatH, seat) - stride * 0.035 * Math.pow(Math.sin(ph), 2) + (p.bob ?? 0);
    this.root.position.set(p.x ?? 0, p.y ?? 0, p.z ?? 0); this.root.rotation.y = p.turn ?? 0;
    this.hips.position.set(0, hipY, 0); this.hips.rotation.set(0, (p.hipTwist ?? 0), p.hipRoll ?? 0);
    this.torso.rotation.order = 'YXZ'; this.torso.rotation.set(p.lean ?? 0, p.twist ?? 0, p.roll ?? 0);
    this.headG.rotation.order = 'YXZ'; this.headG.rotation.set(p.headPitch ?? 0, p.headYaw ?? 0, p.headRoll ?? 0);
    const hands = p.hands || [[-0.2, 0.12, 0.25], [0.2, 0.12, 0.25]];
    this.arms.forEach((a, k) => {
      const T = V3(...hands[k]); const pole = V3(0.7 * a.s, -1, -0.6); if (p.elbowOut) pole.x += p.elbowOut * a.s;
      const end = V3(); ik(a.S, T, o.upper, o.fore, pole, a.E, end);
      placeLimb(a.up, a.S, a.E); placeLimb(a.fo, a.E, end);
      a.sh.position.copy(a.S); a.el.position.copy(a.E); a.H.copy(end); a.dir.copy(end).sub(a.E).normalize();
      a.hand.position.copy(end); a.hand.quaternion.setFromUnitVectors(UP, a.dir);
      const hr = p.handRot && p.handRot[k]; if (hr) a.hand.rotateX(hr[0]).rotateY(hr[1]).rotateZ(hr[2]);
    });
    this.legs.forEach((l, k) => {
      const hip = V3(o.hipX * l.s, 0, 0);
      let A;
      if (p.feet && p.feet[k]) A = V3(...p.feet[k]);
      else {
        const phase = ph + (k === 0 ? 0 : Math.PI);
        const stand = V3(o.hipX * l.s * 1.05, -(hipY - 0.07) + Math.max(0, Math.cos(phase)) * 0.11 * stride, Math.sin(phase) * 0.27 * stride + 0.02);
        const sit = V3(o.hipX * l.s * 1.35 + (p.kneeOut ?? 0) * l.s, -(hipY - 0.075), o.thigh * 0.98);
        A = stand.lerp(sit, seat);
      }
      const pole = V3((p.kneeOut ?? 0) * l.s * 0.5, 0.15 + 0.5 * seat, 1);
      const end = V3(); ik(hip, A, o.thigh, o.shin, pole, l.K, end); l.A.copy(end);
      placeLimb(l.th, hip, l.K); placeLimb(l.sh, l.K, end); l.kn.position.copy(l.K); l.hp.position.copy(hip);
      l.foot.position.copy(end).add(V3(0, -0.035, 0.065));
    });
  }
  /** world position of a hand (k = 0 left, 1 right) and its forearm direction */
  handWorld(k, out = V3()) { this.root.updateMatrixWorld(true); return out.copy(this.arms[k].H).applyMatrix4(this.torso.matrixWorld); }
  headWorld(out = V3()) { this.root.updateMatrixWorld(true); return out.setFromMatrixPosition(this.headG.matrixWorld); }
}

// ---------------------------------------------------------------- her (Adita): blonde waves, black wayfarers, a berry ribbed top
const TOP = 0xa8215a, JEANS = 0x232a3d, BOOT = 0x1b1a1e, SKIN = 0xe9c3a6, LIPS = 0xc98378, BROW = 0x3a2a20;
export const HAIR = { blonde: [0xd2aa70, 0xf0d6a4], brown: [0x4a3022, 0x6a4632] };
export class Woman extends Figure {
  constructor() {
    const top = clay(TOP, { rimAmt: 0.35 }), skin = clay(SKIN, { rimAmt: 0.3 }), jeans = clay(JEANS, { rimAmt: 0.3 }), boot = gloss(BOOT, { shininess: 40, rimAmt: 0.2 });
    super({ sleeve: top, handM: skin, thighM: jeans, shinM: jeans, footM: boot, shoulderX: 0.18, shoulderY: 0.45, armR: 0.054, foreR: 0.047, upper: 0.27, fore: 0.25,
      hipX: 0.09, thigh: 0.42, shin: 0.42, legR: 0.08, shinR: 0.062, standH: 0.88, seatH: 0.49, shK: 0.98 });
    this.mats = { top, coat: top, skin, jeans, boot, lips: clay(LIPS, { rimAmt: 0.2 }), brow: clay(BROW), hair: clay(HAIR.blonde[0], { rimAmt: 0.5 }), hair2: clay(HAIR.blonde[1], { rimAmt: 0.5 }),
      frame: gloss(0x0d0d10, { shininess: 110, specular: 0x9a9aa6, rimAmt: 0.25 }), lens: gloss(0x3a2414, { shininess: 160, specular: 0xffe6c8, rimAmt: 0.1 }),
      hairV: clay(0xffffff, { vertexColors: true, side: THREE.DoubleSide, rimAmt: 0.5 }),
      foil: gloss(0xc9ced6, { shininess: 140, specular: 0xffffff, rimAmt: 0.35 }), cape: gloss(0x141418, { shininess: 25, rimAmt: 0.35 }) };
    const t = this.torso, M = this.mats;
    // a fitted ribbed top
    const prof = [[0.0, -0.02], [0.158, -0.02], [0.166, 0.05], [0.142, 0.16], [0.15, 0.25], [0.175, 0.33], [0.185, 0.41], [0.172, 0.47], [0.09, 0.525], [0.0, 0.535]];
    const body = new THREE.Mesh(lathe(prof, 32), top); body.scale.z = 0.74; t.add(body);
    const neckband = new THREE.Mesh(new THREE.TorusGeometry(0.058, 0.01, 8, 24), top); neckband.rotation.x = Math.PI / 2; neckband.position.y = 0.525; t.add(neckband);
    const neck = new THREE.Mesh(new THREE.CylinderGeometry(0.048, 0.054, 0.13, 16), skin); neck.position.y = 0.57; t.add(neck);
    // jeans at the hips, a belt line
    const hip = new THREE.Mesh(lathe([[0, 0.03], [0.158, 0.03], [0.172, -0.03], [0.165, -0.09], [0, -0.09]], 28), jeans); hip.scale.z = 0.78; this.hips.add(hip);
    // the head and face
    this.headG.position.y = 0.62;
    const head = new THREE.Mesh(lathe([[0, 0.245], [0.055, 0.238], [0.092, 0.215], [0.11, 0.175], [0.113, 0.13], [0.108, 0.085], [0.093, 0.045], [0.068, 0.014], [0.036, -0.003], [0, -0.007]], 36), skin);
    head.scale.z = 1.06; this.headG.add(head); this.head = head;
    const nose = ball(skin, 0.014, 0.8, 1.15, 1.0); nose.position.set(0, 0.092, 0.117); nose.rotation.x = -0.3; this.headG.add(nose);
    const lipU = ball(M.lips, 0.015, 1.3, 0.38, 0.55); lipU.position.set(0, 0.056, 0.108); this.headG.add(lipU);
    const lipL = ball(M.lips, 0.0145, 1.2, 0.48, 0.58); lipL.position.set(0, 0.046, 0.105); this.headG.add(lipL);
    const smile = new THREE.Mesh(new THREE.TorusGeometry(0.019, 0.0058, 8, 20, 2.1), M.lips); smile.position.set(0, 0.066, 0.106); smile.rotation.set(-0.15, 0, Math.PI + (Math.PI - 2.1) / 2 + 0.06); smile.scale.set(1, 0.85, 0.7); smile.visible = false; this.headG.add(smile);
    this.face = { nose, lipU, lipL, smile, brows: [] };
    for (const s of [-1, 1]) { const b = new THREE.Mesh(new THREE.CapsuleGeometry(0.0075, 0.036, 4, 8), M.brow); b.rotation.z = Math.PI / 2 - 0.06 * s; b.position.set(0.037 * s, 0.162, 0.106); b.rotation.y = 0.28 * s; b.scale.set(0.8, 1, 0.8); this.headG.add(b); this.face.brows.push(b); }
    // eyes (dark glossy beads with a lash line and a little wing), seen whenever the wayfarers are off
    const eyeM = gloss(0x24160f, { shininess: 140, specular: 0xffffff, rimAmt: 0.05 }), lashM = clay(0x15100c, { rimAmt: 0.1 });
    this.eyes = new THREE.Group(); this.headG.add(this.eyes);
    for (const s of [-1, 1]) {
      const e = ball(eyeM, 0.0118, 1.0, 1.22, 0.55); e.position.set(0.036 * s, 0.125, 0.109); e.rotation.y = 0.28 * s; this.eyes.add(e);
      const lash = new THREE.Mesh(new THREE.TorusGeometry(0.0146, 0.0022, 5, 14, 2.3), lashM); lash.position.set(0.036 * s, 0.123, 0.111); lash.rotation.set(-0.2, 0.28 * s, Math.PI / 2 - 1.15 + (s > 0 ? 0.08 : -0.08)); this.eyes.add(lash);
      const wing = new THREE.Mesh(new THREE.CapsuleGeometry(0.0016, 0.006, 3, 5), lashM); wing.position.set(0.0505 * s, 0.1335, 0.104); wing.rotation.set(0, 0.4 * s, -0.95 * s); this.eyes.add(wing);
    }
    const blushM = new THREE.MeshLambertMaterial({ color: 0xf0a8a0, transparent: true, opacity: 0.4, depthWrite: false });
    for (const s of [-1, 1]) { const b = ball(blushM, 0.022, 1.2, 0.75, 0.3); b.position.set(0.062 * s, 0.083, 0.094); b.rotation.y = 0.55 * s; this.headG.add(b); }
    // the black wayfarers
    const sg = this.shades = new THREE.Group(); sg.position.set(0, 0.128, 0.104); this.headG.add(sg); this.shadesRest = sg.position.clone();
    for (const s of [-1, 1]) {
      const fr = new THREE.Mesh(rbox(0.058, 0.044, 0.01, 0.012), M.frame); fr.position.set(0.034 * s, 0.0, 0.006); fr.rotation.y = 0.2 * s; fr.rotation.z = -0.05 * s; sg.add(fr);
      const ln = new THREE.Mesh(rbox(0.047, 0.034, 0.004, 0.01), M.lens); ln.position.set(0.034 * s, -0.002, 0.012); ln.rotation.y = 0.2 * s; ln.rotation.z = -0.05 * s; sg.add(ln);
      const tm = new THREE.Mesh(new THREE.BoxGeometry(0.006, 0.008, 0.11), M.frame); tm.position.set(0.064 * s, 0.006, -0.048); sg.add(tm);
    }
    const br = new THREE.Mesh(new THREE.BoxGeometry(0.016, 0.008, 0.008), M.frame); br.position.set(0, 0.006, 0.012); sg.add(br);
    // hair (see hair.js), the salon cape (hidden)
    this.hair = new Hair(this.headG);
    M.cape.side = THREE.DoubleSide; this.cape = new THREE.Mesh(lathe([[0.0, 0.62], [0.07, 0.6], [0.2, 0.5], [0.3, 0.32], [0.36, 0.1], [0.38, 0.0]], 28), M.cape); this.cape.scale.z = 0.85; this.cape.visible = false; t.add(this.cape);
    this.setHair('waves', 'blonde');
    this.headG.scale.setScalar(1.2);
    this.root.scale.setScalar(0.96);
    this.pose({});
  }
  /** mode: 'waves' (long, honey-blonde) | 'pulled' (dark, sleek, a low twist and a claw clip) | 'foils' (salon); colour: 'blonde' | 'dark' */
  setHair(mode = 'waves', colour) { this.hair.set(mode, colour === 'brown' ? 'dark' : (colour || (mode === 'pulled' ? 'dark' : 'blonde'))); }
  /** the wayfarers: true (on), false (off), or a number: how far above the eyes they are (the reveal drops them in) */
  setShades(v) { const sg = this.shades; if (v === false) { sg.visible = false; return; } sg.visible = true; const k = v === true ? 0 : v; sg.position.copy(this.shadesRest).add(V3(0, k * 0.9, k * 0.25)); sg.rotation.x = -k * 2.2; }
  /** a confident smile (k > 0.5) and one raised brow (b 0..1) */
  setFace(k = 0, b = 0) { const F = this.face; F.smile.visible = k > 0.5; F.lipU.visible = F.lipL.visible = k <= 0.5;
    F.brows.forEach((br, i) => { const s = i ? 1 : -1; br.position.y = 0.162 + (i === 0 ? 0.007 * b : 0); br.rotation.z = Math.PI / 2 - 0.06 * s - (i === 0 ? 0.18 * b : 0); }); }
  /** after posing: let the waves hang (gravity), sway, grow in */
  hairTick(t, o = {}) { this.hair.update({ t, ...o }); }
  makeHand(s, m) {
    const g = new THREE.Group(); const palm = ball(m, 0.044, 0.95, 1.2, 0.62); palm.position.y = 0.045; g.add(palm);
    const fingers = ball(m, 0.038, 0.9, 0.9, 0.55); fingers.position.set(0, 0.085, 0.006); g.add(fingers); g.userData.fingers = fingers;
    const th = new THREE.Mesh(new THREE.CapsuleGeometry(0.013, 0.038, 4, 8), m); th.position.set(-0.04 * s, 0.05, 0.02); th.rotation.set(0.3, 0, 0.55 * s); g.add(th); g.userData.thumb = th;
    return g;
  }
  pose(p) { super.pose(p); }
}
