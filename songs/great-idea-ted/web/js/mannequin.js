// smooth clay mannequins (the reference's hoodie-and-beanie figures) and Somebody's Dog.
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
    if (!opts.noHood) {
      const hood = new THREE.Mesh(new THREE.TorusGeometry(0.1, 0.045, 14, 30), shirt); hood.rotation.x = Math.PI / 2 - 0.25; hood.position.set(0, 0.54, -0.03); this.body.add(hood);
      for (const s of [-1, 1]) { const st = new THREE.Mesh(new THREE.CylinderGeometry(0.006, 0.006, 0.16, 6), clay(0xf2f0ea)); st.position.set(0.035 * s, 0.44, 0.115); st.rotation.x = 0.12; this.body.add(st); }
    } else {   // a sweater / shirt neckline: a soft rolled collar
      const col = new THREE.Mesh(new THREE.TorusGeometry(0.075, 0.022, 12, 30), opts.collar ? clay(opts.collar) : shirt); col.rotation.x = Math.PI / 2 - 0.1; col.position.set(0, 0.55, 0.0); this.body.add(col);
    }
    if (opts.vest) {   // Ted: a sweater vest over the shirt, V at the neck
      const vm = clay(opts.vest);
      const vp = [[0.0, 0.03], [0.184, 0.03], [0.21, 0.08], [0.205, 0.2], [0.216, 0.34], [0.229, 0.44], [0.205, 0.5], [0.0, 0.5]].map(([x, y]) => new THREE.Vector2(x, y));
      const v = new THREE.Mesh(new THREE.LatheGeometry(vp, 36), vm); v.scale.z = 0.74; this.body.add(v);
      const vn = new THREE.Mesh(new THREE.ConeGeometry(0.06, 0.14, 3), clay(opts.shirt || 0xe9ecf2)); vn.rotation.set(Math.PI, 0, 0); vn.position.set(0, 0.47, 0.152); vn.scale.z = 0.25; this.body.add(vn);
    }
    // neck + head
    const neck = new THREE.Mesh(new THREE.CylinderGeometry(0.045, 0.05, 0.12, 18), skin); neck.position.y = 0.6; this.body.add(neck);
    this.headG = new THREE.Group(); this.headG.position.y = 0.65; this.body.add(this.headG);
    const head = new THREE.Mesh(GEO.head, skin); head.scale.set(0.118, 0.142, 0.128); head.position.y = 0.12; this.headG.add(head);
    this.head = head;
    // hair and hats sit behind a hairline: a cap tipped back so the front edge is high on the forehead (above the brows)
    // and the back edge reaches the nape. tl: how far round the head the cap goes; tilt: how far it's tipped back.
    const hg = (color, tl = 1.45, tilt = 0.47, sc = [1.04, 1.04, 1.06], r = 0.125, start = 0) => {
      // the cap follows the head's own shape (same ellipsoid, a few mm out); only the hairline is tipped back
      const geo = new THREE.SphereGeometry(1, 48, 24, 0, Math.PI * 2, start, tl - start); geo.rotateX(-tilt);
      const m = new THREE.Mesh(geo, clay(color)); const k = (sc[0] + sc[2]) / 2 + 0.005;
      m.scale.set(0.118 * k, 0.142 * (sc[1] + 0.01), 0.128 * k); m.position.y = 0.12; this.headG.add(m); return m; };
    const hm = clay(opts.hairColor || 0x2a2018);
    if (opts.hair === 'side') {   // Ted: short, neat, parted on his left and combed over
      hg(opts.hairColor || 0x6b4a2e, 1.42, 0.5, [1.035, 1.03, 1.05]);
      const m = clay(opts.hairColor || 0x6b4a2e);
      const quiff = ball(m, 0.06, 1.45, 0.38, 1.0); quiff.position.set(0.02, 0.262, 0.06); quiff.rotation.set(-0.35, 0, -0.18); this.headG.add(quiff);
      const part = new THREE.Mesh(new THREE.BoxGeometry(0.004, 0.004, 0.09), basic(0x3a2618)); part.position.set(-0.048, 0.268, 0.03); part.rotation.set(-0.35, 0, 0.3); this.headG.add(part);
    }
    if (opts.hair === 'short') hg(opts.hairColor || 0x1e1612, 1.36, 0.52, [1.03, 1.0, 1.04]);   // short, close-cropped
    if (opts.hair === 'bun') { hg(opts.hairColor || 0x2a2018, 1.5, 0.5); const b = ball(hm, 0.062); b.position.set(0, 0.27, -0.1); this.headG.add(b); }
    if (opts.hair === 'long') {   // hairline, then two curtains framing the face and the length down the back
      hg(opts.hairColor || 0x2a2018, 1.5, 0.48);
      for (const s of [-1, 1]) { const c = new THREE.Mesh(new THREE.CapsuleGeometry(0.035, 0.17, 6, 14), hm); c.position.set(0.105 * s, 0.07, -0.005); c.rotation.z = 0.06 * s; c.scale.z = 0.8; this.headG.add(c); }
      const back = new THREE.Mesh(new THREE.CapsuleGeometry(0.105, 0.2, 8, 20), hm); back.scale.z = 0.5; back.position.set(0, 0.02, -0.08); this.headG.add(back);
    }
    if (opts.hair === 'updo') {   // her: a curly pink updo held up by a red claw clip, a few curls loose at the temples
      const hc = opts.hairColor || 0xff9cc8, m = clay(hc); hg(hc, 1.44, 0.5, [1.04, 1.04, 1.06]);
      const R = [0.051, 0.047, 0.054, 0.045, 0.05, 0.048, 0.052, 0.046, 0.049];
      for (let i = 0; i < 9; i++) { const a = i / 9 * Math.PI * 2; const b = ball(m, R[i]); b.position.set(Math.cos(a) * 0.058, 0.3 + 0.022 * Math.sin(i * 2.1), Math.sin(a) * 0.05 - 0.05); this.headG.add(b); }
      const top = ball(m, 0.062, 1.05, 0.85, 1.0); top.position.set(0, 0.335, -0.05); this.headG.add(top);
      for (const s of [-1, 1]) { const c = new THREE.Mesh(new THREE.TorusGeometry(0.012, 0.0045, 6, 16, Math.PI * 1.5), m); c.position.set(0.106 * s, 0.13, 0.05); c.rotation.y = 0.9 * s; this.headG.add(c);   // one loose ringlet each side
        const c2 = c.clone(); c2.scale.setScalar(0.8); c2.position.y = 0.108; c2.rotation.z = 1.2; this.headG.add(c2); }
      // the claw clip: a curved red bar with teeth, gripping the back of the updo
      const cm = clay(opts.clipColor || 0xe0262f), clip = new THREE.Group(); clip.position.set(0, 0.29, -0.115); clip.rotation.x = 0.35; this.headG.add(clip);
      const bar = new THREE.Mesh(new THREE.TorusGeometry(0.06, 0.011, 8, 24, Math.PI * 0.75), cm); bar.rotation.set(0, 0, Math.PI * 0.125); clip.add(bar);
      for (let k = 0; k < 6; k++) { const a = Math.PI * (0.18 + k * 0.128); const tth = new THREE.Mesh(new THREE.CapsuleGeometry(0.0055, 0.035, 4, 8), cm);
        tth.position.set(Math.cos(a) * 0.06, Math.sin(a) * 0.06 - 0.02, 0.012); tth.rotation.x = 0.6; clip.add(tth); }
    }
    if (opts.hat === 'cap') {   // a baseball cap: crown on the head's own shape, brim just above the brows
      const hc = opts.hatColor || 0x1f1f24; hg(hc, 1.3, 0.32, [1.07, 1.1, 1.07]);
      const brim = new THREE.Mesh(new THREE.CylinderGeometry(0.1, 0.1, 0.012, 28, 1, false, -Math.PI / 2, Math.PI), clay(hc));
      brim.scale.z = 1.25; brim.position.set(0, 0.215, 0.085); brim.rotation.x = 0.18; this.headG.add(brim);
    }
    if (opts.hat === 'beanie') {   // a beanie pulled down to just above the brows, with a rolled band
      const hc = opts.hatColor || 0x2f5bd3; hg(hc, 1.36, 0.36, [1.08, 1.1, 1.08]);
      hg(hc, 1.36, 0.36, [1.14, 1.14, 1.14], 0.127, 1.06);   // the folded cuff: a thicker band round the bottom edge
      const pom = ball(clay(opts.pomColor || 0xf2efe6), 0.034); pom.position.set(0, 0.285, -0.035); this.headG.add(pom);
    }
    if (opts.face !== false) this.buildFace(opts);
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
  // ---------------------------------------------------------------- the face: eyes with lids, brows, a nose and a mouth
  // Features sit on the head ellipsoid (0.118 x 0.142 x 0.128, centre y 0.12), turned to follow its surface.
  buildFace(o) {
    const H = this.head.scale, cy = this.head.position.y;
    const depth = (x, y) => H.z * Math.sqrt(Math.max(0, 1 - (x / H.x) ** 2 - ((y - cy) / H.y) ** 2));
    const place = (obj, x, y, out = 0) => { const z = depth(x, y); obj.position.set(x, y, z + out);
      obj.rotation.set(-Math.atan2((y - cy) / (H.y * H.y), z / (H.z * H.z)), Math.atan2(x / (H.x * H.x), z / (H.z * H.z)), 0); return obj; };
    const F = this.faceParts = { eyes: [], brows: [], cache: {} };
    const eyeW = clay(0xf1ece3, { rimAmt: 0 }), ink = basic(0x1d1a22), browM = clay(o.browColor || 0x2a2018, { rimAmt: 0 });
    const skinM = clay(o.skin || SKIN), lashM = basic(0x241c22);
    for (const s of [-1, 1]) {
      const g = place(new THREE.Group(), 0.04 * s, 0.137, -0.004); this.headG.add(g);
      const sc = new THREE.Mesh(GEO.sph, eyeW); sc.scale.set(0.02, 0.024, 0.008); g.add(sc);
      const pu = new THREE.Mesh(GEO.sph, ink); pu.scale.set(0.0105, 0.0125, 0.005); pu.position.z = 0.0055; g.add(pu);
      const hl = new THREE.Mesh(GEO.sph, basic(0xd9d4cc)); hl.scale.setScalar(0.0028); hl.position.set(0.0035, 0.0045, 0.0098); g.add(hl);
      // the upper lid: skin coming down over the eye; its edge carries the lash line
      const lid = new THREE.Mesh(new THREE.SphereGeometry(1, 24, 12, 0, Math.PI * 2, 0, Math.PI * 0.5), skinM); lid.scale.set(0.022, 0.001, 0.0115); g.add(lid);
      const lash = new THREE.Mesh(new THREE.CapsuleGeometry(0.0022, 0.03, 3, 8), lashM); lash.rotation.z = Math.PI / 2; lash.position.z = 0.009; g.add(lash);
      F.eyes.push({ g, pu, hl, lid, lash, s });
      const bm = place(new THREE.Mesh(new THREE.CapsuleGeometry(0.0055, 0.03, 4, 10), browM), 0.043 * s, 0.177, 0.001); bm.rotation.z = Math.PI / 2; this.headG.add(bm);
      F.brows.push({ m: bm, s, y0: 0.177 });
    }
    const nose = place(new THREE.Mesh(GEO.sph, skinM), 0, 0.108, -0.005); nose.scale.set(0.013, 0.016, 0.012); this.headG.add(nose);
    if (o.blush) for (const s of [-1, 1]) { const b = place(new THREE.Mesh(new THREE.CircleGeometry(0.016, 20), new THREE.MeshBasicMaterial({ color: 0xff8fa8, transparent: true, opacity: 0.35, depthWrite: false })), 0.07 * s, 0.1, 0.0015); this.headG.add(b); }
    F.mouth = place(new THREE.Group(), 0, 0.071, 0.0); this.headG.add(F.mouth);
    F.lipM = basic(o.lips || 0x5c2530); F.openM = basic(0x34151d); F.teethM = clay(0xf4f1ea, { rimAmt: 0 });
    F.line = new THREE.Mesh(new THREE.BufferGeometry(), F.lipM); F.mouth.add(F.line);
    F.hole = new THREE.Mesh(new THREE.BufferGeometry(), F.openM); F.hole.position.z = -0.0005; F.mouth.add(F.hole);
    F.teeth = new THREE.Mesh(new THREE.BoxGeometry(1, 1, 0.002), F.teethM); F.mouth.add(F.teeth);
    if (o.sunglasses) {   // cat-eye sunglasses: two swept lenses, a thin bridge, the arms back to the ears
      const fr = clay(o.frameColor || 0x141216, { rimAmt: 0.3 }), lens = new THREE.MeshLambertMaterial({ color: 0x1a1420, emissive: 0x0c0710 });
      const shape = new THREE.Shape(); shape.moveTo(-0.026, 0.004); shape.bezierCurveTo(-0.026, 0.02, 0.012, 0.022, 0.03, 0.026);   // the upswept outer corner
      shape.bezierCurveTo(0.03, 0.006, 0.02, -0.02, -0.004, -0.019); shape.bezierCurveTo(-0.02, -0.018, -0.026, -0.008, -0.026, 0.004);
      for (const s of [-1, 1]) { const g = place(new THREE.Group(), 0.042 * s, 0.138, 0.011); this.headG.add(g);
        const l = new THREE.Mesh(new THREE.ExtrudeGeometry(shape, { depth: 0.003, bevelEnabled: true, bevelThickness: 0.0015, bevelSize: 0.0015, bevelSegments: 2 }), lens); l.scale.x = s; g.add(l);
        const rim = new THREE.Mesh(new THREE.ExtrudeGeometry(shape, { depth: 0.002, bevelEnabled: true, bevelThickness: 0.002, bevelSize: 0.003, bevelSegments: 2 }), fr); rim.scale.set(s, 1, 1); rim.position.z = -0.002; g.add(rim);
        const arm = new THREE.Mesh(new THREE.BoxGeometry(0.004, 0.005, 0.11), fr); arm.position.set(0.117 * s, 0.142, -0.035); arm.rotation.y = 0.12 * s; this.headG.add(arm); }
      const br = place(new THREE.Mesh(new THREE.BoxGeometry(0.018, 0.004, 0.004), fr), 0, 0.142, 0.012); this.headG.add(br);
      F.sunglasses = true;
    }
    this.expr({});
  }
  mouthGeo(sm, op) {   // the mouth for a smile (-1..1) and an opening (0..1), cached by value
    const k = Math.round(sm * 20) + ',' + Math.round(op * 20), F = this.faceParts; if (F.cache[k]) return F.cache[k];
    const w = 0.024 + 0.006 * Math.max(0, sm), c = -0.011 * sm, N = 24, t = 0.0032;
    const curve = (u) => { const x = -w + 2 * w * u; return [x, c * (1 - (2 * u - 1) ** 2)]; };   // a parabola: down in the middle when smiling
    const pts = []; for (let i = 0; i <= N; i++) { const [x, y] = curve(i / N); pts.push(new THREE.Vector3(x, y, 0)); }
    const line = new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), 32, t, 6, false);
    let hole = null;
    if (op > 0.02) { const sh = new THREE.Shape(); const drop = 0.026 * op;
      for (let i = 0; i <= N; i++) { const [x, y] = curve(i / N); i ? sh.lineTo(x, y) : sh.moveTo(x, y); }
      for (let i = N; i >= 0; i--) { const u = i / N, [x, y] = curve(u); sh.lineTo(x * 0.92, y - drop * Math.sqrt(Math.max(0, 1 - (2 * u - 1) ** 2)) - 0.002); }
      hole = new THREE.ShapeGeometry(sh, 16); }
    return (F.cache[k] = { line, hole, w, c, drop: 0.026 * op });
  }
  /** e: smile -1..1 (frown..beam), open 0..1 (mouth, singing), lids 0..1 (or [l, r]), brows -1..1 raise (or [l, r]),
   *  browTilt -1..1 (worried..cross), look [x, y] -1..1 (pupils) */
  expr(e) {
    const F = this.faceParts; if (!F) return;
    const pair = (v, d = 0) => (Array.isArray(v) ? v : [v ?? d, v ?? d]);
    const lids = pair(e.lids, 0.1), brows = pair(e.brows, 0), look = e.look || [0, 0], tilt = e.browTilt || 0;
    F.eyes.forEach((E, k) => { const l = Math.min(1, Math.max(0, lids[k])); const edge = 0.024 - 0.048 * l;   // lid edge: eye top (open) .. bottom (shut)
      E.lid.visible = l > 0.03; E.lid.position.y = edge; E.lid.scale.y = Math.max(0.001, 0.026 - edge);
      E.lash.position.y = edge; E.lash.scale.x = 1 - 0.25 * Math.abs(edge) / 0.024;
      E.pu.position.set(0.006 * look[0], 0.005 * look[1] - 0.003 * l, 0.0055); E.hl.position.set(0.0035 + 0.006 * look[0], 0.0045 + 0.005 * look[1], 0.0098); });
    F.brows.forEach((B, k) => { const r = brows[k]; B.m.position.y = B.y0 + 0.012 * r; B.m.rotation.z = Math.PI / 2 - B.s * (0.3 * tilt + 0.1 * r); });
    const sm = Math.max(-1, Math.min(1, e.smile ?? 0.2)), op = Math.max(0, Math.min(1, e.open ?? 0));
    const g = this.mouthGeo(sm, op); F.line.geometry = g.line; F.hole.visible = !!g.hole; if (g.hole) F.hole.geometry = g.hole;
    F.teeth.visible = op > 0.12 && sm > 0.35; F.teeth.scale.set(g.w * 1.25, Math.min(0.006, g.drop * 0.35), 1); F.teeth.position.set(0, g.c * 0.55 - 0.0045, 0.0003);
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
      // leaning bends at the hips: the legs stay where they are (undo the body's lean below the hips)
      const X = new THREE.Vector3(1, 0, 0), un = -(p.lean || 0);
      [hip, knee, ankle].forEach((v) => v.applyAxisAngle(X, un));
      const foot = ankle.clone().add(new THREE.Vector3(0, -0.03, 0.07).applyAxisAngle(X, un));
      placeLimb(l.th, hip, knee); placeLimb(l.sh, knee, ankle); l.kn.position.copy(knee); l.hp.position.copy(hip);
      l.foot.position.copy(foot); l.foot.rotation.set(Math.PI / 2 + un, 0, 0); l.ankle = ankle.clone();
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

// a curly golden doodle, sitting up (feet on the floor at y = 0, facing +z). Curls: small clay balls over every shape.
function curly(group, mat, cx, cy, cz, rx, ry, rz, n, cr, seed) {
  let s = seed; const R = () => (s = (s * 16807) % 2147483647) / 2147483647;
  const core = ball(mat, 1, rx * 0.93, ry * 0.93, rz * 0.93); core.position.set(cx, cy, cz); group.add(core);
  for (let i = 0; i < n; i++) { const u = R() * 2 - 1, a = R() * Math.PI * 2, q = Math.sqrt(1 - u * u);
    const b = ball(mat, cr * (0.8 + 0.4 * R())); b.position.set(cx + rx * q * Math.cos(a), cy + ry * u, cz + rz * q * Math.sin(a)); group.add(b); }
}
export class Doodle {
  constructor() {
    const g = this.root = new THREE.Group(); const fur = clay(0xe2a862), dark = clay(0x2a1c14);
    curly(g, fur, 0, 0.3, -0.04, 0.16, 0.24, 0.17, 70, 0.034, 7);              // body, sitting
    curly(g, fur, 0, 0.12, -0.12, 0.18, 0.1, 0.16, 30, 0.034, 9);              // haunches
    for (const s of [-1, 1]) { curly(g, fur, 0.075 * s, 0.13, 0.1, 0.045, 0.13, 0.045, 14, 0.026, 11 + s);   // front legs
      const paw = ball(fur, 0.05, 1, 0.6, 1.3); paw.position.set(0.075 * s, 0.025, 0.13); g.add(paw); }
    this.headG = new THREE.Group(); this.headG.position.set(0, 0.62, 0.05); g.add(this.headG);
    curly(this.headG, fur, 0, 0, 0, 0.13, 0.12, 0.12, 50, 0.032, 21);          // fluffy head
    curly(this.headG, fur, 0, 0.1, -0.01, 0.09, 0.05, 0.08, 18, 0.03, 23);     // topknot
    const muzzle = ball(clay(0xeab877), 0.07, 1, 0.8, 1.1); muzzle.position.set(0, -0.04, 0.11); this.headG.add(muzzle);
    const nose = ball(dark, 0.024, 1.2, 0.9, 1); nose.position.set(0, -0.025, 0.19); this.headG.add(nose);
    for (const s of [-1, 1]) {
      curly(this.headG, fur, 0.13 * s, -0.06, -0.01, 0.045, 0.1, 0.05, 14, 0.026, 31 + s);   // floppy curly ears
      const eye = ball(basic(0x15100c), 0.017); eye.position.set(0.05 * s, 0.025, 0.115); this.headG.add(eye);
      const hl = ball(basic(0xffffff), 0.005); hl.position.set(0.05 * s + 0.005, 0.032, 0.13); this.headG.add(hl); }
    this.tongue = ball(clay(0xe8607a), 0.025, 1, 0.4, 1.3); this.tongue.position.set(0, -0.085, 0.15); this.headG.add(this.tongue);
    curly(g, fur, 0, 0.05, -0.3, 0.04, 0.04, 0.09, 10, 0.028, 41);             // tail on the floor
  }
  pose(t) { this.headG.rotation.y = 0.25 * Math.sin(t * 0.6); this.headG.rotation.z = 0.08 * Math.sin(t * 1.1); this.tongue.scale.y = 0.025 * (0.4 + 0.3 * Math.abs(Math.sin(t * 5))); }
}

// a grey tabby loafing on the desk (base at y = 0, facing +z), tail curled round, one ear twitching
export class Cat {
  constructor() {
    const g = this.root = new THREE.Group(); const fur = clay(0x8a8f99), light = clay(0xd9dbe0), dark = clay(0x4a4e57);
    const body = ball(fur, 0.13, 1.0, 0.62, 1.35); body.position.set(0, 0.08, -0.02); g.add(body);
    for (let i = 0; i < 4; i++) { const st = new THREE.Mesh(new THREE.TorusGeometry(0.12, 0.008, 6, 24, Math.PI), dark); st.rotation.set(0, Math.PI / 2, 0); st.scale.set(1, 0.65, 1.0); st.position.set(0, 0.08, -0.12 + i * 0.06); g.add(st); }   // tabby stripes
    this.headG = new THREE.Group(); this.headG.position.set(0, 0.17, 0.15); g.add(this.headG);
    const head = ball(fur, 0.085, 1.1, 0.95, 1.0); this.headG.add(head);
    const cheeks = ball(light, 0.05, 1.3, 0.7, 0.8); cheeks.position.set(0, -0.03, 0.055); this.headG.add(cheeks);
    const nose = ball(clay(0xe48a9a), 0.012, 1.2, 0.8, 1); nose.position.set(0, -0.012, 0.09); this.headG.add(nose);
    this.ears = [];
    for (const s of [-1, 1]) { const ear = new THREE.Mesh(new THREE.ConeGeometry(0.035, 0.07, 4), fur); ear.position.set(0.05 * s, 0.075, -0.005); ear.rotation.z = -0.3 * s; this.headG.add(ear); this.ears.push(ear);
      const eye = ball(basic(0x2a3a1a), 0.014, 1, 0.55, 1); eye.position.set(0.034 * s, 0.012, 0.078); this.headG.add(eye);   // sleepy half-closed eyes
      const paw = ball(light, 0.03, 1, 0.6, 1.3); paw.position.set(0.045 * s, 0.02, 0.15); g.add(paw); }
    const tail = new THREE.Mesh(new THREE.TorusGeometry(0.12, 0.022, 8, 20, Math.PI * 1.1), fur); tail.rotation.set(Math.PI / 2, 0, 0.4); tail.position.set(0.02, 0.025, 0.0); g.add(tail);
  }
  pose(t) { this.headG.rotation.y = 0.15 * Math.sin(t * 0.4); this.ears[0].rotation.x = Math.max(0, Math.sin(t * 3.3)) > 0.95 ? 0.4 : 0; }
}
