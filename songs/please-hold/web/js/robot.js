// The hold-robot: the Ragnarök robot's family (white enamel, black glass face, cyan eye strip, black joints, a thin gold
// seam), small and round-shouldered, with an old corded receiver whose coiled cord plugs into a jack in its chest.
// The eye strip is its face and its screen: eyes, a hold-music waveform, a timer, a notepad, scrolling text, a survey,
// five stars, a battery at 1%. A receipt slot under the jack prints the bridge. Our own design: no logos anywhere.
import * as THREE from 'three';
import { Figure, ball, limb, placeLimb, GEO } from './figure.js';
import { gloss, clay, glowMat, liveTex, lathe, rbox, V3, clamp, lerp, sstep, FONT, dotTex, rng } from './lib.js';
import { bitmap } from './font5.js';

const CYAN = '#5ff4ff';
let RM = null;
export function robotMats() {
  if (RM) return RM;
  RM = {
    enamel: gloss(0xeef1f4, { shininess: 85, specular: 0x8a8f96, rimAmt: 0.35 }),
    joint: gloss(0x1d1f24, { shininess: 50, specular: 0x444a52, rimAmt: 0.3 }),
    glass: gloss(0x07080b, { shininess: 140, specular: 0xc8d0dc, rimAmt: 0.25 }),
    gold: gloss(0xd6a64c, { shininess: 90, specular: 0xffe2a0, rimAmt: 0.2 }),
    phone: gloss(0x16161a, { shininess: 90, specular: 0x777c86, rimAmt: 0.3 }),
    eyeGlow: glowMat(new THREE.Color(0.4, 1.7, 2.0)),
  };
  return RM;
}

// ---------------------------------------------------------------- the eye strip, drawn per mode
function dotText(g, text, x0, y0, d, col, glow = true) {        // dot-matrix text at dot pitch d, left/top at x0, y0
  const rows = bitmap(text); g.fillStyle = col; if (glow) { g.shadowColor = col; g.shadowBlur = d * 0.9; }
  for (let r = 0; r < 7; r++) for (let c = 0; c < rows[0].length; c++) if (rows[r][c]) { g.beginPath(); g.arc(x0 + c * d + d / 2, y0 + r * d + d / 2, d * 0.38, 0, 7); g.fill(); }
  g.shadowBlur = 0; return rows[0].length * d;
}
export function drawEye(g, w, h, mode, t, o = {}) {
  g.fillStyle = '#020305'; g.fillRect(0, 0, w, h);
  const col = o.color || CYAN; g.shadowColor = col;
  if (mode === 'off') return;
  if (mode === 'eyes' || mode === 'blink') {
    const bl = mode === 'blink' ? 1 : (o.blink ?? 0); const eh = h * 0.56 * (1 - 0.9 * bl), ew = w * 0.13, gap = w * 0.17;
    g.fillStyle = col; g.shadowBlur = h * 0.25; for (const s of [-1, 1]) { g.beginPath(); g.roundRect(w / 2 + s * gap - ew / 2 + (o.look ?? 0) * w * 0.06, h / 2 - eh / 2, ew, Math.max(eh, h * 0.06), h * 0.18); g.fill(); }
    g.shadowBlur = 0; return;
  }
  if (mode === 'happy') {
    g.strokeStyle = col; g.lineWidth = h * 0.14; g.lineCap = 'round'; g.shadowBlur = h * 0.25;
    for (const s of [-1, 1]) { g.beginPath(); g.arc(w / 2 + s * w * 0.17, h * 0.68, h * 0.26, Math.PI * 1.15, Math.PI * 1.85); g.stroke(); }
    g.shadowBlur = 0; return;
  }
  if (mode === 'wave') {
    const n = 26; g.fillStyle = col; g.shadowBlur = h * 0.2;
    for (let i = 0; i < n; i++) { const x = w * 0.08 + i * (w * 0.84 / n); const a = 0.25 + 0.75 * Math.abs(Math.sin(t * 7.1 + i * 0.7) * Math.sin(t * 3.3 + i * 0.31)) * (o.amp ?? 1);
      const bh = h * 0.72 * a; g.beginPath(); g.roundRect(x, h / 2 - bh / 2, w * 0.84 / n * 0.55, bh, 3); g.fill(); }
    g.shadowBlur = 0; return;
  }
  if (mode === 'text' || mode === 'timer' || mode === 'survey') {
    const text = o.text || (mode === 'timer' ? '47:00' : 'SURVEY · PAGE 1 OF 400');
    const d = h / 9; const tw = (bitmap(text)[0].length) * d;
    const x0 = tw <= w * 0.92 ? (w - tw) / 2 : w * 0.04 - ((o.scroll ?? 0) % (tw + w * 0.3));
    dotText(g, text, x0, d, d, col); if (tw > w * 0.92) dotText(g, text, x0 + tw + w * 0.3, d, d, col);
    return;
  }
  if (mode === 'notes') {
    const k = clamp(o.k ?? 1); g.fillStyle = '#fff4b8'; g.fillRect(w * 0.04, h * 0.08, w * 0.92, h * 0.84);
    g.strokeStyle = 'rgba(80,140,220,0.6)'; g.lineWidth = 2; for (let y = h * 0.3; y < h * 0.9; y += h * 0.2) { g.beginPath(); g.moveTo(w * 0.06, y); g.lineTo(w * 0.94, y); g.stroke(); }
    g.strokeStyle = '#1f2a44'; g.lineWidth = h * 0.05; g.lineCap = 'round'; const R = rng(7);
    const lines = 3; for (let li = 0; li < lines; li++) { const kk = clamp(k * lines - li); if (kk <= 0) break; const y = h * (0.28 + li * 0.2) - 3;
      g.beginPath(); const x1 = w * 0.08 + w * 0.84 * kk * (li === lines - 1 ? 0.6 : 0.95);
      for (let x = w * 0.08; x <= x1; x += 4) { const yy = y - Math.abs(Math.sin(x * 0.11 + li)) * h * 0.08 * (0.6 + 0.4 * Math.sin(x * 0.037 + R())); if (x === w * 0.08) g.moveTo(x, yy); else g.lineTo(x, yy); } g.stroke(); }
    return;
  }
  if (mode === 'stars') {
    const n = o.n ?? 5; const s = h * 0.36;
    for (let i = 0; i < 5; i++) { const cx = w / 2 + (i - 2) * w * 0.17, cy = h / 2; const on = i < n;
      g.fillStyle = on ? '#ffd24a' : 'rgba(255,210,74,0.15)'; g.shadowColor = '#ffb020'; g.shadowBlur = on ? h * 0.3 : 0;
      g.beginPath(); for (let k = 0; k < 10; k++) { const a = -Math.PI / 2 + k * Math.PI / 5, r = k % 2 ? s * 0.45 : s; g.lineTo(cx + Math.cos(a) * r, cy + Math.sin(a) * r); } g.closePath(); g.fill(); }
    g.shadowBlur = 0; return;
  }
  if (mode === 'battery') {
    const on = o.on ?? 1; const bw = w * 0.2, bh = h * 0.56, x = w * 0.3, y = (h - bh) / 2;
    g.strokeStyle = '#ff4a3a'; g.lineWidth = h * 0.07; g.shadowColor = '#ff4a3a'; g.shadowBlur = h * 0.2 * on; g.globalAlpha = 0.35 + 0.65 * on;
    g.beginPath(); g.roundRect(x, y, bw, bh, h * 0.08); g.stroke(); g.fillStyle = '#ff4a3a'; g.fillRect(x + bw, y + bh * 0.3, w * 0.02, bh * 0.4);
    g.fillRect(x + h * 0.08, y + h * 0.08, bw * 0.08, bh - h * 0.16);
    dotText(g, '1%', x + bw + w * 0.07, h / 9, h / 9, '#ff4a3a'); g.globalAlpha = 1; g.shadowBlur = 0; return;
  }
}

// ---------------------------------------------------------------- the receiver and its coiled cord
export function makeHandset(mat) {
  const g = new THREE.Group();
  const bar = new THREE.Mesh(new THREE.CapsuleGeometry(0.027, 0.15, 6, 12), mat); bar.scale.z = 0.8; g.add(bar);
  const ear = new THREE.Mesh(new THREE.CylinderGeometry(0.045, 0.038, 0.05, 20), mat); ear.position.set(0.02, 0.1, 0); ear.rotation.z = Math.PI / 2; g.add(ear);
  const mouth = ear.clone(); mouth.position.set(0.02, -0.1, 0); g.add(mouth);
  g.userData.cordEnd = V3(0.0, -0.13, 0);                // where the cord leaves (bottom)
  return g;
}
export class Cord {
  constructor(mat, { r = 0.0055, coil = 0.014, turnsPerM = 70 } = {}) { this.mesh = new THREE.Mesh(new THREE.BufferGeometry(), mat); this.mesh.frustumCulled = false; this.o = { r, coil, turnsPerM }; this.key = null; }
  /** a coiled cord along a sagging curve from a to b (world or parent space); sag in metres; stretch 0..1 straightens it */
  update(a, b, sag = 0.25, opt = {}) {
    const { mid = null, stretch = 0, pts = null } = opt;
    const key = [a.x, a.y, a.z, b.x, b.y, b.z, sag, stretch].map((x) => x.toFixed(3)).join(',') + (pts ? pts.length : '');
    if (key === this.key) return; this.key = key;
    const base = pts ? new THREE.CatmullRomCurve3(pts) : (() => { const m = mid || a.clone().lerp(b, 0.5).add(V3(0, -sag, 0)); return new THREE.CatmullRomCurve3([a, a.clone().lerp(m, 0.5).add(V3(0, -sag * 0.25, 0)), m, m.clone().lerp(b, 0.5).add(V3(0, -sag * 0.15, 0)), b]); })();
    const L = base.getLength(); const turns = Math.max(4, L * this.o.turnsPerM * (1 - 0.6 * stretch)); const N = Math.min(opt.maxN ?? 1400, Math.ceil(turns * 10));
    const frames = base.computeFrenetFrames(N, false); const helix = [];
    for (let i = 0; i <= N; i++) { const u = i / N; const p = base.getPointAt(u); const th = u * turns * Math.PI * 2; const rr = this.o.coil * (1 - 0.7 * stretch) * sstep(0, 0.03, u) * sstep(1, 0.97, u);
      helix.push(p.addScaledVector(frames.normals[i], Math.cos(th) * rr).addScaledVector(frames.binormals[i], Math.sin(th) * rr)); }
    this.mesh.geometry.dispose(); this.mesh.geometry = new THREE.TubeGeometry(new THREE.CatmullRomCurve3(helix), N * 2, this.o.r, 5, false);
  }
}

// ---------------------------------------------------------------- the robot
export class Robot extends Figure {
  constructor({ eyeRes = [640, 112] } = {}) {
    const R = robotMats();
    super({ sleeve: R.enamel, upperM: R.enamel, handM: R.joint, thighM: R.enamel, shinM: R.enamel, footM: R.enamel, jointM: R.joint,
      shoulderX: 0.215, shoulderY: 0.43, armR: 0.05, foreR: 0.046, upper: 0.25, fore: 0.24, hipX: 0.1, thigh: 0.27, shin: 0.27, legR: 0.062, shinR: 0.056,
      standH: 0.62, seatH: 0.49 / 0.9 });
    this.R = R; const t = this.torso;
    const chest = new THREE.Mesh(lathe([[0, 0.16], [0.17, 0.16], [0.215, 0.27], [0.235, 0.38], [0.22, 0.46], [0.13, 0.52], [0, 0.53]], 32), R.enamel); chest.scale.z = 0.76; t.add(chest);
    const waist = new THREE.Mesh(new THREE.CylinderGeometry(0.13, 0.15, 0.13, 24), R.joint); waist.position.y = 0.1; waist.scale.z = 0.78; t.add(waist);
    const pelvis = new THREE.Mesh(lathe([[0, -0.07], [0.15, -0.07], [0.178, 0.0], [0.16, 0.05], [0, 0.05]], 24), R.enamel); pelvis.scale.z = 0.78; this.hips.add(pelvis);
    const seam = new THREE.Mesh(new THREE.TorusGeometry(0.226, 0.0045, 4, 40), R.gold); seam.rotation.x = Math.PI / 2; seam.scale.y = 0.76; seam.position.y = 0.33; t.add(seam);
    const neck = new THREE.Mesh(new THREE.CylinderGeometry(0.045, 0.055, 0.08, 14), R.joint); neck.position.y = 0.55; t.add(neck);
    // the chest: a jack for the cord, a receipt slot under it (gold rim)
    const jack = new THREE.Mesh(new THREE.TorusGeometry(0.018, 0.007, 8, 18), R.gold); jack.position.set(0.0, 0.41, 0.172); jack.rotation.x = -0.25; t.add(jack);
    const sock = ball(R.joint, 0.014, 1, 1, 0.5); sock.position.set(0, 0.41, 0.17); t.add(sock); this.jack = jack;
    const slot = new THREE.Mesh(rbox(0.13, 0.016, 0.02, 0.006), R.joint); slot.position.set(0, 0.28, 0.168); slot.rotation.x = -0.1; t.add(slot);
    const slotRim = new THREE.Mesh(rbox(0.145, 0.028, 0.012, 0.008), R.gold); slotRim.position.set(0, 0.28, 0.163); slotRim.rotation.x = -0.1; t.add(slotRim); this.slot = slot;
    // the head: an enamel egg, a black glass face, the eye strip, ear discs
    const h = this.headG; h.position.y = 0.57;
    const skull = ball(R.enamel, 1, 0.118, 0.142, 0.126); skull.position.y = 0.13; h.add(skull);
    const face = new THREE.Mesh(new THREE.SphereGeometry(1, 32, 22, -Math.PI * 0.38, Math.PI * 0.76, Math.PI * 0.2, Math.PI * 0.56), R.glass); face.scale.set(0.121, 0.145, 0.13); face.position.y = 0.13; h.add(face);
    this.eyeTex = liveTex(eyeRes[0], eyeRes[1]);
    const eyeMat = new THREE.MeshBasicMaterial({ map: this.eyeTex, toneMapped: false, color: new THREE.Color(1.6, 1.6, 1.6) });
    const eg = new THREE.CylinderGeometry(0.1335, 0.1335, 0.056, 40, 1, true, -0.98, 1.96); const eye = new THREE.Mesh(eg, eyeMat); eye.scale.set(0.93, 1, 1); eye.position.y = 0.152; h.add(eye); this.eye = eye;
    for (const s of [-1, 1]) { const e = new THREE.Mesh(new THREE.CylinderGeometry(0.032, 0.032, 0.022, 20), R.joint); e.rotation.z = Math.PI / 2; e.position.set(0.12 * s, 0.13, -0.005); h.add(e);
      const r = new THREE.Mesh(new THREE.TorusGeometry(0.03, 0.004, 4, 20), R.gold); r.rotation.y = Math.PI / 2; r.position.set(0.131 * s, 0.13, -0.005); h.add(r); }
    // thrusters under the feet
    this.flames = this.legs.map((l) => { const f = new THREE.Sprite(new THREE.SpriteMaterial({ map: dotTex(), color: 0x7ff6ff, transparent: true, opacity: 0, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false })); f.scale.set(0.14, 0.3, 1); this.hips.add(f); return f; });
    // the receiver in the left hand, the cord to the chest
    this.handset = makeHandset(R.phone); this.arms[0].hand.add(this.handset);
    this.handset.position.set(0.0, 0.07, 0.03); this.handset.rotation.set(0, 0, 0);
    this.cord = new Cord(R.phone); this.root.add(this.cord.mesh);
    this.root.scale.setScalar(0.9);
    this.eyeState = { mode: 'eyes', t: 0, o: {} };
    this.pose({});
  }
  makeHand(s, mm) {
    const g = new THREE.Group(); const palm = ball(mm, 0.038, 1, 1.15, 0.72); palm.position.y = 0.035; g.add(palm);
    for (const k of [-1, 1]) { const f = new THREE.Mesh(rbox(0.016, 0.05, 0.022, 0.006), mm); f.position.set(k * 0.02, 0.082, 0.004); f.rotation.z = -k * 0.12; g.add(f); }
    const th = new THREE.Mesh(rbox(0.016, 0.042, 0.02, 0.006), mm); th.position.set(-0.036 * s, 0.05, 0.014); th.rotation.z = 0.6 * s; g.add(th);
    return g;
  }
  makeFoot(s, m) { const g = new THREE.Group(); const f = new THREE.Mesh(new THREE.CapsuleGeometry(0.05, 0.1, 6, 14), m); f.rotation.x = Math.PI / 2; f.scale.set(1.05, 1, 0.8); g.add(f);
    const n = new THREE.Mesh(new THREE.TorusGeometry(0.026, 0.008, 6, 16), robotMats().gold); n.rotation.x = Math.PI / 2; n.position.set(0, -0.04, -0.01); g.add(n); return g; }
  pose(p) {
    const o = this.o;
    if ((p.seat ?? 1) > 0.5 && !p.feet) {           // seated, its short legs dangle
      const s = p.seat ?? 1; const sw = Math.sin((p.swing ?? 0)) * 0.08;
      p = { ...p, feet: [[-o.hipX * 1.15, -0.25 * s - 0.27 * (1 - s), 0.3 * s + sw], [o.hipX * 1.15, -0.25 * s - 0.27 * (1 - s), 0.3 * s - sw]] };
    }
    super.pose(p);
  }
  /** eye: mode + options (text, scroll, k, n, on, blink, amp, color) */
  setEye(mode, t, o = {}) {
    this.eye.material.color.setScalar(mode === 'notes' ? 0.78 : (mode === 'stars' ? 1.2 : 1.6));
    const key = mode + '|' + JSON.stringify(o) + (mode === 'wave' ? '|' + Math.round(t * 30) : '');
    this.eyeTex.userData.redraw(key, (g, w, h) => drawEye(g, w, h, mode, t, o));
  }
  /** the cord from the receiver to the chest jack (in the robot root's space) */
  updateCord(opt = {}) {
    this.root.updateMatrixWorld(true);
    const inv = new THREE.Matrix4().copy(this.root.matrixWorld).invert();
    const a = this.handset.userData.cordEnd.clone().applyMatrix4(this.handset.matrixWorld).applyMatrix4(inv);
    const b = V3(0, 0.41, 0.19).applyMatrix4(this.torso.matrixWorld).applyMatrix4(inv);
    if (opt.to) { const tw = opt.to.clone().applyMatrix4(inv); this.cord.update(a, tw, opt.sag ?? 0.4, opt); return; }
    this.cord.update(a, b, opt.sag ?? 0.12, opt);
  }
  thrust(k) { this.flames.forEach((f, i) => { const l = this.legs[i]; f.position.copy(l.A).add(V3(0, -0.2, 0)); f.material.opacity = k; f.scale.set(0.12 + 0.05 * k, 0.25 + 0.25 * k, 1); }); }
  /** world-space point of the chest jack and receipt slot */
  jackWorld(out = V3()) { this.root.updateMatrixWorld(true); return out.set(0, 0.41, 0.19).applyMatrix4(this.torso.matrixWorld); }
  slotWorld(out = V3()) { this.root.updateMatrixWorld(true); return out.set(0, 0.28, 0.18).applyMatrix4(this.torso.matrixWorld); }
}
