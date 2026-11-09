// Her hair, three looks for the glow-up:
//   'pulled' : dark brown, sleek and pulled back into a low twist held by a claw clip, two loose tendrils at the temples
//   'foils'  : the salon: a processing cap with rows of foil packets
//   'waves'  : honey-blonde waves: chunky locks (flattened, twisting ribbons) that sweep from a side part over the scalp
//              and fall past the shoulders. Rebuilt every frame: the falls hang partly with gravity (the head bows, the
//              hair swings), sway a little, and can grow in from the crown with a spring (the reveal).
// Everything lives in head space (the head's lathe: chin at y = 0, crown at y = 0.245, face toward +z).
import * as THREE from 'three';
import { clamp, lerp, sstep, easeOut, rng, V3, clay, gloss, rbox } from './lib.js';

export const HAIRC = {
  blonde: { root: 0xb48647, mid: 0xd8ab62, tip: 0xf0d394, cap: 0xbf914f },
  dark: { root: 0x1e130d, mid: 0x33221a, tip: 0x4a3123, cap: 0x23170f },
  foil: { cap: 0x5a4030 },
};
const CS = V3(0, 0.118, -0.002);                   // centre of the scalp sphere
const _c = new THREE.Color(), _c2 = new THREE.Color();

/** append one lock (a flattened tube) to the arrays. pts: centre line; w, h: half width / thickness per point; tw: twist;
 *  col: THREE.Color per point; out: outward reference per point (orients the flat side) */
function ribbon(A, pts, w, h, tw, col, out, sides = 8) {
  const n = pts.length; const base = A.pos.length / 3;
  const T = V3(), N = V3(), B = V3(), tmp = V3();
  for (let i = 0; i < n; i++) {
    const p0 = pts[Math.max(0, i - 1)], p1 = pts[Math.min(n - 1, i + 1)]; T.copy(p1).sub(p0).normalize();
    N.copy(out[i]).addScaledVector(T, -out[i].dot(T)); if (N.lengthSq() < 1e-8) N.set(0, 0, 1); N.normalize(); B.crossVectors(T, N).normalize();
    const ct = Math.cos(tw[i]), st = Math.sin(tw[i]); const Nn = tmp.copy(N).multiplyScalar(ct).addScaledVector(B, st); const Bn = V3().crossVectors(T, Nn);
    for (let k = 0; k < sides; k++) {
      const ph = (k / sides) * Math.PI * 2; const cx = Math.cos(ph), sx = Math.sin(ph);
      A.pos.push(pts[i].x + Bn.x * cx * w[i] + Nn.x * sx * h[i], pts[i].y + Bn.y * cx * w[i] + Nn.y * sx * h[i], pts[i].z + Bn.z * cx * w[i] + Nn.z * sx * h[i]);
      const nx = Bn.x * cx / Math.max(w[i], 1e-4) + Nn.x * sx / Math.max(h[i], 1e-4), ny = Bn.y * cx / Math.max(w[i], 1e-4) + Nn.y * sx / Math.max(h[i], 1e-4), nz = Bn.z * cx / Math.max(w[i], 1e-4) + Nn.z * sx / Math.max(h[i], 1e-4);
      const l = Math.hypot(nx, ny, nz) || 1; A.nor.push(nx / l, ny / l, nz / l);
      const shade = 0.86 + 0.2 * Math.max(0, sx) + 0.05 * cx;     // the outer face catches more light: reads as sheen
      A.col.push(col[i].r * shade, col[i].g * shade, col[i].b * shade);
    }
  }
  for (let i = 0; i < n - 1; i++) for (let k = 0; k < sides; k++) {
    const a = base + i * sides + k, b = base + i * sides + (k + 1) % sides, c = a + sides, d = b + sides; A.idx.push(a, c, b, b, c, d);
  }
}
function toGeo(A) {
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(A.pos, 3)); g.setAttribute('normal', new THREE.Float32BufferAttribute(A.nor, 3));
  g.setAttribute('color', new THREE.Float32BufferAttribute(A.col, 3)); g.setIndex(A.idx); return g;
}
const SK = V3(1.05, 1.17, 1.17);                    // the scalp ellipsoid: the head is taller than it is wide
const onSphere = (d, r) => V3(CS.x + d.x * r * SK.x, CS.y + d.y * r * SK.y, CS.z + d.z * r * SK.z);
const dirAt = (th, el) => V3(Math.sin(th) * Math.cos(el), Math.sin(el), -Math.cos(th) * Math.cos(el));   // th = 0 straight back, +-pi/2 the sides, pi the face
function slerpDir(a, b, s) { const d = clamp(a.dot(b), -1, 1); const om = Math.acos(d); if (om < 1e-4) return a.clone(); const so = Math.sin(om); return a.clone().multiplyScalar(Math.sin((1 - s) * om) / so).addScaledVector(b, Math.sin(s * om) / so).normalize(); }

/** the hairline: the lowest elevation (rad) the hair reaches at azimuth th (0 = straight back, pi = the middle of the forehead) */
const HL = [[0, -0.78], [0.9, -0.62], [1.35, -0.2], [1.62, -0.02], [2.0, 0.16], [2.35, 0.36], [2.7, 0.52], [Math.PI, 0.58]];
function hairline(th) { const a = Math.abs(th); for (let i = 1; i < HL.length; i++) if (a <= HL[i][0]) { const [a0, e0] = HL[i - 1], [a1, e1] = HL[i]; const u = (a - a0) / (a1 - a0); return lerp(e0, e1, u * u * (3 - 2 * u)); } return HL[HL.length - 1][1]; }
/** a scalp cap that ends on the hairline (vertices below it are slid up onto it, tucked in), with strand striations
 *  (vertex colours) running toward `focus` */
function capGeo(col, r = 0.127, focus = V3(0, -0.3, -1).normalize(), stripes = 46, lift = 0) {
  const g = new THREE.SphereGeometry(1, 72, 40); const p = g.attributes.position; const c = []; const base = new THREE.Color(col); const f = focus.clone().normalize();
  const up = V3(0, 1, 0); const side = V3().crossVectors(f, up).normalize(); const up2 = V3().crossVectors(side, f).normalize();
  for (let i = 0; i < p.count; i++) {
    const d = V3(p.getX(i), p.getY(i), p.getZ(i)).normalize(); const th = Math.atan2(d.x, -d.z); let el = Math.asin(clamp(d.y, -1, 1)); const hl = hairline(th) + lift;
    let rr = r; if (el < hl) { el = hl; rr = r * 0.965; }
    const dd = V3(Math.sin(th) * Math.cos(el), Math.sin(el), -Math.cos(th) * Math.cos(el)); const q = onSphere(dd, rr); p.setXYZ(i, q.x, q.y, q.z);
    const ang = Math.atan2(dd.dot(side), dd.dot(up2));
    const k = 0.92 + 0.07 * Math.sin(ang * stripes) + 0.04 * Math.sin(ang * stripes * 0.37 + 1.3); c.push(base.r * k, base.g * k, base.b * k);
  }
  g.setAttribute('color', new THREE.Float32BufferAttribute(c, 3)); g.computeVertexNormals(); return g;
}

export class Hair {
  constructor(headG) {
    this.g = new THREE.Group(); headG.add(this.g); this.headG = headG;
    this.mat = gloss(0xffffff, { vertexColors: true, shininess: 22, specular: 0x3a3226, rimAmt: 0.42 });
    this.capMat = clay(0xffffff, { vertexColors: true, rimAmt: 0.35 });
    this.foilMat = gloss(0xe6e9ee, { shininess: 200, specular: 0xffffff, rimAmt: 0.5, side: THREE.DoubleSide });
    this.scrunchMat = gloss(0x8e1f4f, { shininess: 70, specular: 0xff9cc4, rimAmt: 0.3 });
    this.cap = new THREE.Mesh(capGeo(0xffffff), this.capMat); this.g.add(this.cap);
    this.locks = new THREE.Mesh(new THREE.BufferGeometry(), this.mat); this.locks.frustumCulled = false; this.g.add(this.locks);
    this.extra = new THREE.Group(); this.g.add(this.extra);
    this.foilG = new THREE.Group(); this.g.add(this.foilG); this.foils = []; this.buildFoils();
    this.mode = null; this.look = null; this.key = null;
    this.LOCKS = this.makeLocks();
  }
  /** static per-lock layout for the waves */
  makeLocks() {
    const R = rng(11); const L = [];
    const add = (th, layer, len, o = {}) => L.push({ th, layer, len, w: o.w ?? 0.043 + R() * 0.01, ph: R() * 6.28, wf: 1.15 + R() * 0.35, amp: o.amp ?? 0.02 + R() * 0.008, front: o.front ?? 0, el: o.el, root: o.root, seed: R() });
    for (let i = 0; i < 15; i++) { const x = lerp(-1, 1, i / 14); add(x * 2.0, 0, 0.44 - 0.08 * x * x); }
    for (let i = 0; i < 14; i++) { const x = lerp(-1, 1, (i + 0.5) / 14); add(x * 1.9, 1, 0.39 - 0.07 * x * x, { w: 0.04 }); }
    // face-framing locks from the part, sweeping over the temples and falling in front of the shoulders
    add(-2.3, 2, 0.36, { front: 1, w: 0.04, el: 0.34, root: 'part' }); add(2.3, 2, 0.34, { front: 1, w: 0.038, el: 0.32, root: 'part' });
    add(-2.0, 2, 0.38, { front: 0.7, w: 0.042, el: 0.24, root: 'part' }); add(1.98, 2, 0.37, { front: 0.7, w: 0.04, el: 0.22, root: 'part' });
    add(-2.16, 2, 0.35, { front: 0.85, w: 0.044, el: 0.3, root: 'part', amp: 0.014 }); add(2.14, 2, 0.34, { front: 0.85, w: 0.042, el: 0.28, root: 'part', amp: 0.014 });
    return L;
  }
  /** look: 'pulled' | 'foils' | 'waves'; colour: 'dark' | 'blonde' */
  set(look, colour = look === 'pulled' ? 'dark' : 'blonde') {
    const key = look + colour; if (this.key === key) return; this.key = key; this.look = look; this.colour = colour;
    const C = HAIRC[colour];
    while (this.extra.children.length) { const c = this.extra.children.pop(); c.geometry?.dispose(); }
    this.foilG.visible = look === 'foils';
    const focus = look === 'pulled' ? V3(0, -0.45, -1) : (look === 'waves' ? V3(0.25, 1, -0.15) : V3(0, 1, 0));
    this.cap.geometry.dispose(); this.cap.geometry = capGeo(look === 'foils' ? HAIRC.foil.cap : C.cap, look === 'pulled' ? 0.124 : 0.126, focus, look === 'pulled' ? 52 : 40);
    this.locks.visible = look === 'waves';
    if (look === 'pulled') this.buildPulled(C);
  }
  buildPulled(C) {
    // a low twisted bun at the nape and a satin scrunchie around it
    const A = { pos: [], nor: [], col: [], idx: [] };
    const c0 = new THREE.Color(C.mid), c1 = new THREE.Color(C.tip);
    for (let k = 0; k < 3; k++) {
      const pts = [], w = [], h = [], tw = [], col = [], out = [];
      for (let i = 0; i <= 28; i++) { const s = i / 28; const a = s * Math.PI * 2.2 + k * 2.1; const rr = 0.034 * (1 - 0.25 * s);
        const p = V3(Math.cos(a) * rr, 0.045 + Math.sin(a) * rr * 0.75 - s * 0.012, -0.158 - 0.022 * Math.sin(a + 0.6)); pts.push(p);
        w.push(0.02 * (1 - 0.35 * s)); h.push(0.013 * (1 - 0.3 * s)); tw.push(s * 3 + k); col.push(c0.clone().lerp(c1, 0.3 + 0.2 * Math.sin(s * 9 + k))); out.push(V3(Math.cos(a), Math.sin(a), -0.6).normalize()); }
      ribbon(A, pts, w, h, tw, col, out);
    }
    this.extra.add(new THREE.Mesh(toGeo(A), this.mat));
    const sg = new THREE.TorusGeometry(0.03, 0.012, 10, 36); const p = sg.attributes.position;
    for (let i = 0; i < p.count; i++) { const x = p.getX(i), y = p.getY(i), z = p.getZ(i); const a = Math.atan2(y, x); const k = 1 + 0.18 * Math.sin(a * 11); p.setXYZ(i, x * (0.75 + 0.25 * k), y * (0.75 + 0.25 * k), z * k); }
    sg.computeVertexNormals(); const scr = new THREE.Mesh(sg, this.scrunchMat); scr.position.set(0, 0.06, -0.142); scr.rotation.x = 0.25; this.extra.add(scr);
  }
  buildFoils() {
    const R = rng(31);
    for (let row = 0; row < 4; row++) {
      const el = lerp(1.15, 0.0, row / 3); const n = Math.round(lerp(5, 10, row / 3));
      for (let i = 0; i < n; i++) {
        const th = lerp(-2.1, 2.1, (i + 0.5 * (row % 2)) / (n - 0.5)) + (R() - 0.5) * 0.08; if (Math.abs(th) > 2.15) continue;
        const d = dirAt(th, el); const f = new THREE.Mesh(rbox(0.07, 0.12, 0.006, 0.005), this.foilMat);
        const hinge = new THREE.Group(); hinge.position.copy(onSphere(d, 0.132));
        const m = new THREE.Matrix4().lookAt(V3(), d, V3(0, 1, 0)); hinge.quaternion.setFromRotationMatrix(m); hinge.rotateX(-0.95 - R() * 0.35); hinge.rotateZ((R() - 0.5) * 0.35);
        f.position.set(0, -0.055, 0.012); hinge.add(f); this.foilG.add(hinge); this.foils.push({ hinge, f, d, seed: R(), rest: hinge.position.clone(), q: hinge.quaternion.clone() });
      }
    }
  }
  /** the foils fly off (seconds since the burst), even after the look has switched to the waves */
  foilsFly(tSince) { this.foilG.visible = tSince < 1.2; this.burstFoils(tSince); }
  burstFoils(tSince) {
    for (const F of this.foils) { const d = tSince - F.seed * 0.12; if (d <= 0) { F.hinge.position.copy(F.rest); F.hinge.quaternion.copy(F.q); F.f.visible = true; continue; }
      const v = F.d.clone().multiplyScalar(1.2 + F.seed * 1.4).add(V3(0, 0.9 + F.seed, 0)); const p = F.rest.clone().addScaledVector(v, d).add(V3(0, -2.4 * d * d, 0));
      F.hinge.position.copy(p); F.hinge.quaternion.copy(F.q); F.hinge.rotateX(d * (8 + F.seed * 10)); F.hinge.rotateZ(d * (5 - F.seed * 9)); F.f.visible = d < 0.9; }
  }
  /** waves: rebuild the locks. o: { grow (0..1, the reveal), t (sway), swing (extra sideways swing, -1..1), gk (gravity share) } */
  update(o = {}) {
    if (this.look !== 'waves') return;
    const grow = o.grow ?? 1, t = o.t ?? 0, gk = o.gk ?? 0.55;
    // gravity in head space, partly: the hair hangs, but keeps some of the head's own shape
    this.headG.updateWorldMatrix(true, false); const q = new THREE.Quaternion(); this.headG.getWorldQuaternion(q);
    const gW = V3(0, -1, 0).applyQuaternion(q.invert()); const g = V3(0, -1, 0).lerp(gW, gk).normalize();
    const key = [grow.toFixed(3), g.x.toFixed(3), g.y.toFixed(3), g.z.toFixed(3), (t * 30 | 0), (o.swing ?? 0).toFixed(3)].join(',');
    if (key === this._uk) return; this._uk = key;
    const C = HAIRC[this.colour]; const cR = new THREE.Color(C.root), cM = new THREE.Color(C.mid), cT = new THREE.Color(C.tip);
    const A = { pos: [], nor: [], col: [], idx: [] };
    const crown = V3(0.02, 1, -0.12).normalize(), part = V3(0.16, 0.96, 0.32).normalize();
    for (const L of this.LOCKS) {
      const pts = [], w = [], h = [], tw = [], col = [], out = [];
      const r0 = 0.128 + L.layer * 0.007 + (L.layer === 2 ? 0.004 : 0);
      const el = L.el ?? lerp(-0.32, 0.18, sstep(0.3, 2.1, Math.abs(L.th)));
      const rootD = (L.root === 'part' ? part : crown).clone().lerp(dirAt(L.th, 1.25), 0.25).normalize();
      const dropD = dirAt(L.th, el);
      // over the scalp
      const nS = 12; for (let i = 0; i <= nS; i++) { const u = i / nS; const d = slerpDir(rootD, dropD, u); const p = onSphere(d, r0 + 0.012 * Math.sin(u * Math.PI) * (1 - u * 0.4));
        pts.push(p); w.push(L.w * (0.8 + 0.4 * u)); h.push(0.0085 + 0.004 * u); tw.push(0); col.push(cR.clone().lerp(cM, u * 0.55)); out.push(d.clone()); }
      // the fall: starts along the skull, turns into gravity, swells out, waves and twists, tapers to a curl
      const len = L.len * Math.max(0.0001, grow); const nF = 34; let p = pts[pts.length - 1].clone();
      let dir = slerpDir(rootD, dropD, 1).clone().sub(slerpDir(rootD, dropD, 0.9)).normalize();
      const radial = V3(dropD.x, 0, dropD.z).normalize(); const lateral = V3().crossVectors(V3(0, 1, 0), radial).normalize();
      const fwd = L.front ? V3(0, 0, 1) : null;
      for (let i = 1; i <= nF; i++) {
        const s = i / nF; dir.lerp(g, 0.22).normalize(); if (fwd) dir.addScaledVector(fwd, 0.05 * L.front * (1 - s)).normalize();
        p = p.clone().addScaledVector(dir, len / nF);
        const env = sstep(0.05, 0.4, s); const wv = Math.sin(s * L.wf * Math.PI * 2 * Math.min(1, grow + 0.25) + L.ph + t * 0.9) * L.amp * env;
        const sway = (o.swing ?? 0) * 0.05 * s * s + Math.sin(t * 1.3 + L.seed * 6) * 0.004 * s;
        const curl = Math.pow(sstep(0.72, 1.0, s), 2);           // the ends flip out and up a little, like a blow-out
        const pp = p.clone().addScaledVector(radial, 0.035 * Math.sqrt(s) + 0.012 * Math.cos(s * 9 + L.ph) * env + 0.022 * curl * grow).addScaledVector(lateral, wv + sway).add(V3(0, 0.016 * curl * grow, 0));
        pts.push(pp); const tip = s > 0.84 ? Math.sqrt(Math.max(0, 1 - Math.pow((s - 0.84) / 0.16, 2))) : 1;
        w.push(L.w * (1.1 - 0.25 * s) * (0.3 + 0.7 * tip)); h.push((0.017 - 0.004 * s) * (0.35 + 0.65 * tip)); tw.push(Math.sin(s * L.wf * Math.PI * 2 + L.ph) * 0.3 * env);
        col.push(cM.clone().lerp(cT, Math.min(1, s * 1.15))); out.push(radial.clone().addScaledVector(lateral, 0.2 * Math.sin(L.ph)).normalize());
      }
      if (grow < 0.02) { pts.length = nS + 1; w.length = h.length = tw.length = col.length = out.length = nS + 1; }
      ribbon(A, pts, w, h, tw, col, out, 10);
    }
    this.locks.geometry.dispose(); this.locks.geometry = toGeo(A);
  }
}
