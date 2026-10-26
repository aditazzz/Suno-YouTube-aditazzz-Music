// smooth clay mannequins in hoodies and beanies, and Somebody's Dog.
// Joints are spheres and limbs are cylinders of the same radius, so the chain reads as one smooth limb.
// Arms are posed with a two-bone IK: give each hand a target in body space.
import * as THREE from 'three';
import { clay, basic, canvasTex, FONT, lerp } from './lib.js';

const UP = new THREE.Vector3(0, 1, 0);
const _v = new THREE.Vector3(), _q = new THREE.Quaternion();
const GEO = {
  sph: new THREE.SphereGeometry(1, 28, 18), cyl: new THREE.CylinderGeometry(1, 1, 1, 22, 1, true),
  head: new THREE.SphereGeometry(1, 40, 28),
};
const SKIN = 0xe9e3da;

function limb(mat, r) {
  const g = new THREE.Group();
  const c = new THREE.Mesh(GEO.cyl, mat); c.scale.set(r, 1, r); g.add(c);
  g.userData = { c, r }; return g;
}
function placeLimb(l, a, b) {
  const len = a.distanceTo(b); l.position.copy(a).add(b).multiplyScalar(0.5);
  _v.copy(b).sub(a).normalize(); l.quaternion.setFromUnitVectors(UP, _v);
  l.userData.c.scale.y = Math.max(0.001, len);
}
function ball(mat, r, sx = 1, sy = 1, sz = 1) { const m = new THREE.Mesh(GEO.sph, mat); m.scale.set(r * sx, r * sy, r * sz); return m; }

function ik(S, T, a, b, pole, outE) {
  const d = Math.min(a + b - 1e-4, Math.max(Math.abs(a - b) + 1e-4, S.distanceTo(T)));
  const dir = _v.copy(T).sub(S).normalize().clone();
  const cosA = (a * a + d * d - b * b) / (2 * a * d); const sinA = Math.sqrt(Math.max(0, 1 - cosA * cosA));
  const p = pole.clone().sub(dir.clone().multiplyScalar(pole.dot(dir))).normalize();
  outE.copy(S).add(dir.multiplyScalar(a * cosA)).add(p.multiplyScalar(a * sinA));
  // the hand ends exactly at the reachable point along S->T
  return d;
}

export class Mannequin {
  /** opts: shirt, pants, hat ('beanie'|'cap'|null), hatColor, hair ('bun'|'long'|null), hairColor,
   *  headset, headphones, glasses, lanyard, seated */
  constructor(opts = {}) {
    this.o = opts; const g = this.root = new THREE.Group();
    const skin = this.skin = clay(opts.skin || SKIN);
    const shirt = this.shirtM = clay(opts.shirt || 0x8a909c);
    const pants = clay(opts.pants || 0x2b2e36);
    this.body = new THREE.Group(); g.add(this.body);
    // torso: a lathe profile (hoodie), slightly flattened front to back
    const prof = [[0.0, 0.0], [0.17, 0.0], [0.195, 0.05], [0.19, 0.2], [0.2, 0.34], [0.215, 0.44], [0.19, 0.51], [0.1, 0.555], [0.0, 0.56]]
      .map(([x, y]) => new THREE.Vector2(x, y));
    const torso = new THREE.Mesh(new THREE.LatheGeometry(prof, 36), shirt); torso.scale.z = 0.72; this.body.add(torso);
    this.torso = torso;
    // hood + strings
    const hood = new THREE.Mesh(new THREE.TorusGeometry(0.1, 0.045, 14, 30), shirt); hood.rotation.x = Math.PI / 2 - 0.25; hood.position.set(0, 0.54, -0.03); this.body.add(hood);
    for (const s of [-1, 1]) { const st = new THREE.Mesh(new THREE.CylinderGeometry(0.006, 0.006, 0.16, 6), clay(0xf2f0ea)); st.position.set(0.035 * s, 0.44, 0.115); st.rotation.x = 0.12; this.body.add(st); }
    // neck + head
    const neck = new THREE.Mesh(new THREE.CylinderGeometry(0.045, 0.05, 0.12, 18), skin); neck.position.y = 0.6; this.body.add(neck);
    this.headG = new THREE.Group(); this.headG.position.y = 0.65; this.body.add(this.headG);
    const head = new THREE.Mesh(GEO.head, skin); head.scale.set(0.118, 0.142, 0.128); head.position.y = 0.12; this.headG.add(head);
    this.head = head;
    if (opts.hat === 'beanie') {
      const hc = clay(opts.hatColor || 0x2f5bd3);
      const cap = new THREE.Mesh(new THREE.SphereGeometry(0.128, 32, 16, 0, Math.PI * 2, 0, Math.PI * 0.55), hc); cap.scale.set(1.02, 1.15, 1.06); cap.position.y = 0.155; this.headG.add(cap);
      const band = new THREE.Mesh(new THREE.CylinderGeometry(0.134, 0.136, 0.06, 32, 1, true), clay(opts.hatColor || 0x2f5bd3)); band.scale.z = 1.06; band.position.y = 0.155; this.headG.add(band);
    } else if (opts.hat === 'cap') {
      const hc = clay(opts.hatColor || 0x1f1f24);
      const cap = new THREE.Mesh(new THREE.SphereGeometry(0.126, 32, 16, 0, Math.PI * 2, 0, Math.PI * 0.5), hc); cap.scale.set(1.0, 0.9, 1.05); cap.position.y = 0.17; this.headG.add(cap);
      const brim = new THREE.Mesh(new THREE.CylinderGeometry(0.11, 0.11, 0.012, 24, 1, false, -Math.PI / 2, Math.PI), hc); brim.scale.z = 1.4; brim.position.set(0, 0.17, 0.07); this.headG.add(brim);
    }
    if (opts.hair === 'bun') { const hm = clay(opts.hairColor || 0x2a2018); const b = ball(hm, 0.07); b.position.set(0, 0.29, -0.06); this.headG.add(b);
      const cap = new THREE.Mesh(new THREE.SphereGeometry(0.124, 32, 16, 0, Math.PI * 2, 0, Math.PI * 0.5), hm); cap.scale.set(1.0, 1.1, 1.05); cap.position.y = 0.13; this.headG.add(cap); }
    if (opts.hair === 'long') { const hm = clay(opts.hairColor || 0x2a2018);
      const cap = new THREE.Mesh(new THREE.SphereGeometry(0.126, 32, 16, 0, Math.PI * 2, 0, Math.PI * 0.55), hm); cap.scale.set(1.02, 1.12, 1.06); cap.position.y = 0.13; this.headG.add(cap);
      const back = new THREE.Mesh(new THREE.CapsuleGeometry(0.11, 0.18, 8, 20), hm); back.scale.z = 0.55; back.position.set(0, 0.02, -0.07); this.headG.add(back); }
    if (opts.hair === 'curly') { const hm = clay(opts.hairColor || 0xff8fc2);
      for (let i = 0; i < 26; i++) { const a = i / 26 * Math.PI * 2, r = 0.115, y = 0.13 + 0.07 * Math.sin(i * 1.7);
        const b = ball(hm, 0.045 + 0.012 * Math.sin(i * 2.3)); b.position.set(Math.cos(a) * r, y + 0.06, Math.sin(a) * r * 0.9 - 0.02); if (Math.sin(a) < 0.55) this.headG.add(b); }
      const b2 = ball(hm, 0.11, 1.15, 0.7, 1.05); b2.position.set(0, 0.23, -0.02); this.headG.add(b2); }
    if (opts.headphones || opts.headset) {
      const hm = clay(opts.headsetColor || 0x26272c);
      const band = new THREE.Mesh(new THREE.TorusGeometry(0.135, 0.012, 8, 30, Math.PI), hm); band.position.y = 0.13; this.headG.add(band);
      for (const s of [-1, 1]) { const cup = new THREE.Mesh(new THREE.CylinderGeometry(0.045, 0.045, 0.035, 20), hm); cup.rotation.z = Math.PI / 2; cup.position.set(0.128 * s, 0.11, 0); this.headG.add(cup); }
      if (opts.headset) { const boom = new THREE.Mesh(new THREE.CylinderGeometry(0.006, 0.006, 0.14, 6), hm); boom.position.set(0.1, 0.05, 0.07); boom.rotation.set(0.9, 0, 0.5); this.headG.add(boom);
        const mic = ball(hm, 0.014); mic.position.set(0.055, 0.0, 0.12); this.headG.add(mic); }
    }
    if (opts.glasses) { const gm = basic(0x141414);
      for (const s of [-1, 1]) { const r = new THREE.Mesh(new THREE.TorusGeometry(0.035, 0.005, 6, 20), gm); r.position.set(0.045 * s, 0.135, 0.122); this.headG.add(r); }
      const br = new THREE.Mesh(new THREE.CylinderGeometry(0.004, 0.004, 0.025, 4), gm); br.rotation.z = Math.PI / 2; br.position.set(0, 0.137, 0.126); this.headG.add(br); }
    if (opts.lanyard) { const lm = clay(0xd63452);
      for (const s of [-1, 1]) { const l = new THREE.Mesh(new THREE.CylinderGeometry(0.007, 0.007, 0.26, 6), lm); l.position.set(0.05 * s, 0.4, 0.13); l.rotation.z = 0.18 * s; l.rotation.x = 0.15; this.body.add(l); }
      const badge = new THREE.Mesh(new THREE.BoxGeometry(0.07, 0.09, 0.008), basic(0xf4f4f2)); badge.position.set(0, 0.27, 0.15); this.body.add(badge); }
    // arms
    this.arms = [-1, 1].map((s) => {
      const up = limb(shirt, 0.068), fo = limb(shirt, 0.06), sh = ball(shirt, 0.08), el = ball(shirt, 0.064), wr = ball(skin, 0.04);
      const hand = new THREE.Mesh(GEO.sph, skin); hand.scale.set(0.05, 0.066, 0.036);
      [up, fo, sh, el, wr, hand].forEach((m) => this.body.add(m));
      return { s, up, fo, sh, el, wr, hand, S: new THREE.Vector3(0.215 * s, 0.47, 0), E: new THREE.Vector3(), T: new THREE.Vector3(0.22 * s, 0.1, 0.12) };
    });
    // legs (seated by default)
    this.legs = [-1, 1].map((s) => {
      const th = limb(pants, 0.085), sh = limb(pants, 0.068), kn = ball(pants, 0.08), hp = ball(pants, 0.095);
      const foot = new THREE.Mesh(new THREE.CapsuleGeometry(0.045, 0.1, 6, 12), clay(0x1c1c20)); foot.rotation.x = Math.PI / 2;
      [th, sh, kn, hp, foot].forEach((m) => this.body.add(m)); return { s, th, sh, kn, hp, foot };
    });
    this.seated = opts.seated !== false;
    this.root.traverse((o) => { if (o.isMesh) o.frustumCulled = true; });
    this.pose({});
  }
  /** p: lean (rad), headYaw, headPitch, hands: [[x,y,z],[x,y,z]] in body space (left, right), seated, bob */
  pose(p) {
    const seated = p.seated !== undefined ? p.seated : this.seated;
    this.body.position.y = seated ? 0.48 : 0.9;
    this.body.rotation.x = p.lean || 0; this.body.rotation.y = p.turn || 0;
    this.headG.rotation.set(p.headPitch || 0, p.headYaw || 0, p.headRoll || 0);
    const hands = p.hands || [[-0.2, 0.12, 0.3], [0.2, 0.12, 0.3]];
    this.arms.forEach((a, k) => {
      const T = new THREE.Vector3(...hands[k]); const pole = new THREE.Vector3(0.6 * a.s, -1, -0.5);
      ik(a.S, T, 0.27, 0.25, pole, a.E);
      const dir = T.clone().sub(a.S); const d = Math.min(0.52 - 1e-3, dir.length()); dir.normalize();
      // keep the hand on the forearm line at full reach
      const H = a.E.clone().add(T.clone().sub(a.E).normalize().multiplyScalar(0.25));
      placeLimb(a.up, a.S, a.E); placeLimb(a.fo, a.E, H);
      a.sh.position.copy(a.S); a.el.position.copy(a.E); a.wr.position.copy(H);
      a.hand.position.copy(H).add(T.clone().sub(a.E).normalize().multiplyScalar(0.05));
      a.hand.quaternion.setFromUnitVectors(UP, T.clone().sub(a.E).normalize());
    });
    this.legs.forEach((l) => {
      const hip = new THREE.Vector3(0.09 * l.s, 0.02, 0);
      let knee, ankle;
      if (seated) { knee = new THREE.Vector3(0.11 * l.s, 0.0, 0.4); ankle = new THREE.Vector3(0.12 * l.s, -0.42, 0.42); }
      else { const st = p.stride || 0; knee = new THREE.Vector3(0.1 * l.s, -0.42, 0.04 + st * l.s * 0.12); ankle = new THREE.Vector3(0.1 * l.s, -0.84, -0.02 + st * l.s * 0.2); }
      placeLimb(l.th, hip, knee); placeLimb(l.sh, knee, ankle); l.kn.position.copy(knee); l.hp.position.copy(hip);
      l.foot.position.copy(ankle).add(new THREE.Vector3(0, -0.03, 0.07));
    });
  }
}

// letter cards the mannequins hold up in the choruses
const _cards = {};
export function cardTex(ch) {
  if (_cards[ch]) return _cards[ch];
  _cards[ch] = canvasTex(256, 320, (g, w, h) => {
    g.fillStyle = '#f6f3ec'; g.beginPath(); g.roundRect(0, 0, w, h, 14); g.fill();
    g.fillStyle = '#18161a'; g.font = `260px ${FONT.dispBlack}`; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(ch, w / 2, h / 2 + 14);
  });
  return _cards[ch];
}
export function letterCard(ch) {
  const m = new THREE.Mesh(new THREE.PlaneGeometry(0.4, 0.5), new THREE.MeshLambertMaterial({ map: cardTex(ch), side: THREE.DoubleSide }));
  return m;
}

// Somebody's Dog: golden, headset on, taking standup very seriously
export class Dog {
  constructor() {
    const g = this.root = new THREE.Group(); const fur = clay(0xd9a24a); const dark = clay(0x3a2a1c); const hs = clay(0x26272c);
    const body = new THREE.Mesh(new THREE.CapsuleGeometry(0.17, 0.25, 10, 24), fur); body.position.set(0, 0.62, -0.02); body.rotation.x = -0.35; g.add(body);
    const chest = ball(clay(0xe8c27a), 0.13, 1, 1.15, 0.8); chest.position.set(0, 0.72, 0.09); g.add(chest);
    this.headG = new THREE.Group(); this.headG.position.set(0, 0.98, 0.04); g.add(this.headG);
    const head = ball(fur, 0.15, 1, 0.95, 1.0); this.headG.add(head);
    const snout = ball(clay(0xe8c27a), 0.085, 1, 0.75, 1.15); snout.position.set(0, -0.04, 0.13); this.headG.add(snout);
    const nose = ball(dark, 0.028); nose.position.set(0, -0.01, 0.225); this.headG.add(nose);
    for (const s of [-1, 1]) {
      const ear = ball(clay(0xb98336), 0.085, 0.45, 1.25, 0.9); ear.position.set(0.15 * s, -0.04, -0.01); ear.rotation.z = 0.25 * s; this.headG.add(ear);
      const eye = ball(basic(0x111111), 0.018); eye.position.set(0.055 * s, 0.035, 0.13); this.headG.add(eye);
      const leg = new THREE.Mesh(new THREE.CapsuleGeometry(0.04, 0.22, 6, 12), fur); leg.position.set(0.08 * s, 0.4, 0.12); g.add(leg);
      const cup = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.05, 0.035, 18), hs); cup.rotation.z = Math.PI / 2; cup.position.set(0.155 * s, 0.03, 0); this.headG.add(cup);
    }
    const band = new THREE.Mesh(new THREE.TorusGeometry(0.16, 0.012, 8, 30, Math.PI), hs); band.position.y = 0.03; this.headG.add(band);
    const boom = new THREE.Mesh(new THREE.CylinderGeometry(0.006, 0.006, 0.17, 6), hs); boom.position.set(0.11, -0.06, 0.1); boom.rotation.set(1.1, 0, 0.6); this.headG.add(boom);
    this.tongue = ball(clay(0xe8607a), 0.03, 1, 0.4, 1.3); this.tongue.position.set(0, -0.1, 0.17); this.headG.add(this.tongue);
  }
  pose(t) { this.headG.rotation.z = 0.12 * Math.sin(t * 1.3); this.headG.rotation.x = 0.06 * Math.sin(t * 2.1); this.tongue.scale.y = 0.03 * (0.4 + 0.2 * Math.abs(Math.sin(t * 4))); }
}
