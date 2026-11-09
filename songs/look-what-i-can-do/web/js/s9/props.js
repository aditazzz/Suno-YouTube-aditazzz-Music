// Props for S9/S10, after Please Hold's props.js: her phone (its screen now plays her real ChatGPT screen recording),
// the hand that holds it and the thumb that taps (the POV close-ups), and the receipt the robot prints from its chest
// slot (here: her real "out of usage" post, printed on thermal paper, with a highlighter pass).
import * as THREE from 'three';
import { clay, gloss, canvasTex, liveTex, rbox, V3, clamp, lerp, sstep, FONT, rng } from './lib.js';

// ---------------------------------------------------------------- her phone
// the screen matches the recording (1080 x 2210)
export const PHONE = { w: 0.0788, h: 0.1560, d: 0.0085 }; PHONE.sw = 0.0738; PHONE.sh = PHONE.sw * 2210 / 1080;
export class Phone {
  constructor() {
    const g = this.root = new THREE.Group();
    this.body = new THREE.Mesh(rbox(PHONE.w, PHONE.h, PHONE.d, 0.011, 4), gloss(0x22252b, { shininess: 70, specular: 0x777c86, rimAmt: 0.3 })); g.add(this.body);
    this.tex = new THREE.Texture(); this.tex.colorSpace = THREE.SRGBColorSpace; this.tex.anisotropy = 8; this.tex.generateMipmaps = true; this.tex.minFilter = THREE.LinearMipmapLinearFilter;
    this.mat = new THREE.MeshBasicMaterial({ map: this.tex, toneMapped: false, color: new THREE.Color(0, 0, 0) });
    const sg = new THREE.PlaneGeometry(PHONE.sw, PHONE.sh); this.screen = new THREE.Mesh(sg, this.mat); this.screen.position.z = PHONE.d / 2 + 0.0004; g.add(this.screen);
    // the screen's own rounded black glass border (the screen plane is square-cornered; the body's bezel frames it)
    const cam = new THREE.Mesh(new THREE.CylinderGeometry(0.006, 0.006, 0.002, 16), gloss(0x101114)); cam.rotation.x = Math.PI / 2; cam.position.set(-0.02, 0.06, -PHONE.d / 2 - 0.001); g.add(cam);
    this.frame = -1;
  }
  /** brightness 0 (off) .. 1 */
  setOn(k) { this.mat.color.setScalar(k); this.screen.visible = k > 0.002; }
  /** a point on the screen in the phone's local space, from recording pixels (1080 x 2210) */
  local(x, y) { return V3((x / 1080 - 0.5) * PHONE.sw, (0.5 - y / 2210) * PHONE.sh, PHONE.d / 2 + 0.001); }
}
// a thumb for close-ups (the phone's own frame): the tip sits at the origin, pointing up (+y)
export function makeThumb(skinMat, sleeveMat) {
  const g = new THREE.Group();
  const th = new THREE.Mesh(new THREE.CapsuleGeometry(0.009, 0.05, 6, 12), skinMat); th.position.y = -0.03; g.add(th);
  const nail = new THREE.Mesh(new THREE.SphereGeometry(0.0085, 12, 8), clay(0xf0d2c0, { rimAmt: 0.2 })); nail.scale.set(1, 1.2, 0.35); nail.position.set(0, -0.012, 0.008); g.add(nail);
  const base = new THREE.Mesh(new THREE.SphereGeometry(0.032, 16, 12), skinMat); base.scale.set(1.1, 1.35, 0.75); base.position.set(0.016, -0.085, -0.014); g.add(base);
  if (sleeveMat) { const sl = new THREE.Mesh(new THREE.CapsuleGeometry(0.038, 0.22, 6, 16), sleeveMat); sl.position.set(0.05, -0.21, -0.05); sl.rotation.set(-0.5, 0, 0.35); g.add(sl); }
  return g;
}
/** her left hand holding the phone (the phone's own frame): palm behind, fingers round the right edge, thumb on the left */
export function phoneHand(skinMat, sleeveMat) {
  const g = new THREE.Group(); const dx = (PHONE.w - 0.074) / 2;
  const palm = new THREE.Mesh(rbox(0.082, 0.095, 0.03, 0.014), skinMat); palm.position.set(0.0, -0.035, -0.022); g.add(palm);
  for (let i = 0; i < 4; i++) { const f = new THREE.Mesh(new THREE.CapsuleGeometry(0.0066, 0.014, 6, 10), skinMat); f.rotation.z = Math.PI / 2; f.position.set(0.0405 + dx, -0.006 - i * 0.0172, -0.001); g.add(f);
    const k = new THREE.Mesh(new THREE.SphereGeometry(0.0074, 10, 8), skinMat); k.position.set(0.044 + dx, -0.006 - i * 0.0172, -0.008); g.add(k); }
  const th = new THREE.Mesh(new THREE.CapsuleGeometry(0.0085, 0.034, 6, 10), skinMat); th.position.set(-0.043 - dx, -0.036, 0.004); th.rotation.z = -0.22; g.add(th);
  const thb = new THREE.Mesh(new THREE.SphereGeometry(0.022, 12, 10), skinMat); thb.position.set(-0.035 - dx, -0.065, -0.008); g.add(thb);
  if (sleeveMat) { const sl = new THREE.Mesh(new THREE.CapsuleGeometry(0.04, 0.22, 6, 16), sleeveMat); sl.position.set(-0.03, -0.17, -0.07); sl.rotation.set(-0.55, 0, -0.25); g.add(sl); }
  return g;
}

// ---------------------------------------------------------------- the receipt: her real post, printed
// Canvas 1280 x 1720, top = the end at the slot. It prints out bottom-first (the footer leaves the slot first), so
// the strip reads upright, top to bottom, as it hangs: header, her post, footer.
export const RC = { W: 1280, H: 1720, postX: 20, postY: 200, postW: 1240 }; RC.postH = RC.postW * 1090 / 1320;
RC.hl = [250, 283, 1230, 344].map((v, i) => (i % 2 ? RC.postY : RC.postX) + v * RC.postW / 1320);   // "I have an AI slop empire to build."
export function drawReceipt(g, W, H, img, s) {
  g.fillStyle = '#f7f6f1'; g.fillRect(0, 0, W, H);
  const ink = '#1d2026'; g.fillStyle = ink; g.textAlign = 'center'; g.textBaseline = 'middle';
  g.font = `64px ${FONT.monoB}`; g.fillText('* USAGE RECEIPT *', W / 2, 74);
  g.font = `34px ${FONT.mono}`; g.fillStyle = '#4a4f58'; g.fillText('claude · printed on your behalf', W / 2, 136);
  if (img) g.drawImage(img, RC.postX, RC.postY, RC.postW, RC.postH);
  // the highlighter pass (multiply: the ink stays black, the paper turns yellow)
  const k = clamp(s.hl ?? 0); if (k > 0) {
    const [x0, y0, x1, y1] = RC.hl; const pad = 10; g.save(); g.globalCompositeOperation = 'multiply'; g.fillStyle = '#ffe14d';
    const R = rng(3); g.beginPath(); const xe = x0 - pad + (x1 - x0 + 2 * pad) * k;
    g.moveTo(x0 - pad, y0 - pad + 2); for (let x = x0 - pad; x <= xe; x += 40) g.lineTo(x, y0 - pad + R() * 5); g.lineTo(xe, y0 - pad + 3); g.lineTo(xe - 6, y1 + pad - 2);
    for (let x = xe - 6; x >= x0 - pad; x -= 40) g.lineTo(x, y1 + pad - R() * 5); g.closePath(); g.fill(); g.restore(); }
  const fy = RC.postY + RC.postH + 40; g.fillStyle = ink;
  g.font = `34px ${FONT.mono}`; g.fillText('- - - - - - - - - - - - - - - - - - - - - - - -', W / 2, fy);
  g.textAlign = 'left'; g.font = `44px ${FONT.monoB}`; g.fillText('BALANCE', 40, fy + 70); g.textAlign = 'right'; g.fillText('0 MESSAGES', W - 40, fy + 70);
  g.textAlign = 'left'; g.fillText('RESETS', 40, fy + 136); g.textAlign = 'right'; g.fillText('SAT 3:00 AM', W - 40, fy + 136);
  g.textAlign = 'center'; g.font = `40px ${FONT.monoB}`; g.fillText('THANK YOU FOR CREATING :)', W / 2, fy + 216);
  for (let k2 = 0; k2 < 70; k2++) { const bw = ((k2 * 7919) % 5 + 1) * 3; g.fillRect(250 + k2 * 11, fy + 262, bw, 60); }
}
export class Receipt {
  constructor() {
    this.W = 0.104; this.tex = liveTex(RC.W, RC.H); this.Ltex = this.W * RC.H / RC.W; const segs = 80; this.rows = segs + 1;
    this.geo = new THREE.PlaneGeometry(this.W, 1, 1, segs);
    this.mat = new THREE.MeshLambertMaterial({ map: this.tex, side: THREE.DoubleSide, emissive: 0x585858, emissiveMap: this.tex });
    this.mesh = new THREE.Mesh(this.geo, this.mat); this.mesh.frustumCulled = false; this.img = null;
  }
  draw(s) { this.tex.userData.redraw(JSON.stringify(s), (g, w, h) => drawReceipt(g, w, h, this.img, s)); }
  /** the printed strip: origin = slot (world), fwd = out of the slot, side = across the paper (reader's right), L = printed
   *  length (m). It leaves the slot pitched down (pitch0), bends with gravity toward vertical and curls out at the tip. */
  shape(origin, fwd, side, L, o = {}) {
    const p = this.geo.attributes.position, uv = this.geo.attributes.uv; const n = this.rows; const t = o.t ?? 0;
    const ds = Math.max(L, 1e-4) / (n - 1); const pos = origin.clone(); const flat = V3(fwd.x, 0, fwd.z).normalize(); this.pts = []; this.ds = ds;
    let th = o.pitch0 ?? -0.95;
    for (let i = 0; i < n; i++) {
      const s = i * ds; const c = s;                                   // canvas v from the top: the slot end is the canvas top
      const sway = (o.sway ?? 0) * Math.sin(t * 2.3 + s * 18) * 0.004 * (s / 0.15);
      for (let k = 0; k < 2; k++) { const idx = i * 2 + k; const sx = (k === 0 ? -1 : 1) * this.W / 2;
        p.setXYZ(idx, pos.x + side.x * sx, pos.y + side.y * sx, pos.z + side.z * sx); uv.setXY(idx, k, 1 - clamp((this.Ltex - L + c) / this.Ltex, 0, 1)); }
      this.pts.push(pos.clone());
      const tipCurl = sstep(L - 0.03, L, s) * 1.6;                      // the free end curls forward
      th = Math.max(-1.42, th - (o.bend ?? 3.2) * ds) + tipCurl * ds * 14;
      const dir = flat.clone().multiplyScalar(Math.cos(th)).add(V3(0, Math.sin(th), 0)); dir.addScaledVector(side, sway);
      pos.addScaledVector(dir, ds);
    }
    p.needsUpdate = true; uv.needsUpdate = true; this.geo.computeVertexNormals(); this.geo.computeBoundingSphere();
  }
  /** world point at s metres along the strip from the slot */
  pointAt(s) { if (!this.pts || !this.pts.length) return V3(); const f = clamp(s / this.ds, 0, this.pts.length - 1); const i = Math.floor(f), k = f - i; const a = this.pts[i], b = this.pts[Math.min(this.pts.length - 1, i + 1)]; return a.clone().lerp(b, k); }
}
