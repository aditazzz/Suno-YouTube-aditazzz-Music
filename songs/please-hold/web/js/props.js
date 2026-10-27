// Props: her phone (and every screen it shows), the bill, the keypad, the empty cubicle, the takeout box and the egg
// roll, a drink, the notebook, the receipt and the rubber stamp, the history pieces, cobwebs, a pigeon, sax notes,
// invented tabloids, a hand for the close-ups. Everything is a simple shape with a painted face, built to read at a glance.
import * as THREE from 'three';
import { clay, gloss, basic, glowMat, canvasTex, liveTex, rbox, lathe, V3, clamp, lerp, sstep, easeOut, easeOutBack, FONT, rng, dotTex, textPlane } from './lib.js';
import { bitmap } from './font5.js';

export const ORANGE = '#ff6a1a', CYAN = '#4ff0ff', GREEN = '#3ddc84';
const rr = (g, x, y, w, h, r) => { g.beginPath(); g.roundRect(x, y, w, h, r); };

// ---------------------------------------------------------------- icons
function robotIcon(g, cx, cy, s, col = '#062a30') {
  g.save(); g.fillStyle = col; rr(g, cx - s * 0.42, cy - s * 0.36, s * 0.84, s * 0.68, s * 0.3); g.fill();
  g.fillStyle = '#ffffff'; rr(g, cx - s * 0.3, cy - s * 0.12, s * 0.6, s * 0.18, s * 0.09); g.fill();
  g.fillStyle = col; g.beginPath(); g.arc(cx - s * 0.11, cy - s * 0.03, s * 0.045, 0, 7); g.arc(cx + s * 0.11, cy - s * 0.03, s * 0.045, 0, 7); g.fill();
  g.fillRect(cx - s * 0.03, cy - s * 0.5, s * 0.06, s * 0.14); g.beginPath(); g.arc(cx, cy - s * 0.52, s * 0.06, 0, 7); g.fill(); g.restore();
}
function phoneGlyph(g, cx, cy, s, col) {               // a classic handset glyph
  g.save(); g.translate(cx, cy); g.rotate(-0.6); g.fillStyle = col;
  rr(g, -s * 0.12, -s * 0.42, s * 0.24, s * 0.84, s * 0.1); g.fill(); rr(g, -s * 0.22, -s * 0.5, s * 0.36, s * 0.22, s * 0.08); g.fill(); rr(g, -s * 0.22, s * 0.28, s * 0.36, s * 0.22, s * 0.08); g.fill(); g.restore();
}
function micGlyph(g, cx, cy, s, col) {
  g.save(); g.strokeStyle = col; g.fillStyle = col; g.lineWidth = s * 0.09; g.lineCap = 'round';
  rr(g, cx - s * 0.17, cy - s * 0.5, s * 0.34, s * 0.62, s * 0.17); g.fill();
  g.beginPath(); g.arc(cx, cy - s * 0.02, s * 0.32, 0.15, Math.PI - 0.15); g.stroke(); g.beginPath(); g.moveTo(cx, cy + s * 0.3); g.lineTo(cx, cy + s * 0.48); g.stroke(); g.restore();
}

// ---------------------------------------------------------------- her phone
export const PHONE = { w: 0.074, h: 0.156, d: 0.0085 };
/** the screens: state = { screen, t, hold (s on hold), k (progress), press, ... } */
export function drawPhone(g, W, H, s) {
  const u = W / 600;           // design units: 600 x 1300
  g.fillStyle = '#0b0d12'; g.fillRect(0, 0, W, H);
  const font = (px, f = FONT.ui) => `${px * u}px ${f}`;
  // status bar
  g.fillStyle = '#e9edf2'; g.font = font(30, FONT.ui); g.textBaseline = 'middle'; g.textAlign = 'left'; g.fillText(s.clock || '9:41', 44 * u, 50 * u);
  g.textAlign = 'right'; g.fillText('●●●  ▮', W - 44 * u, 50 * u); g.textAlign = 'left';
  const scr = s.screen;
  if (scr === 'call' || scr === 'wait' || scr === 'handoff') {
    // the line every hold starts with
    g.fillStyle = 'rgba(255,255,255,0.08)'; rr(g, 34 * u, 100 * u, W - 68 * u, 120 * u, 34 * u); g.fill();
    g.fillStyle = '#f4f6f8'; g.font = font(30, FONT.ui); g.textAlign = 'center'; g.fillText('Your call is very', W / 2, 140 * u); g.fillText('important to us.', W / 2, 180 * u);
    // the caller
    const av = g.createLinearGradient(0, 250 * u, 0, 420 * u); av.addColorStop(0, '#3a4a5e'); av.addColorStop(1, '#1d2633');
    g.fillStyle = av; g.beginPath(); g.arc(W / 2, 330 * u, 78 * u, 0, 7); g.fill(); phoneGlyph(g, W / 2, 330 * u, 90 * u, '#cfd8e3');
    g.fillStyle = '#ffffff'; g.font = font(44, FONT.disp); g.fillText('Customer Care', W / 2, 460 * u);
    g.fillStyle = '#93a0ae'; g.font = font(28, FONT.uiM); g.fillText('Internet · Billing', W / 2, 505 * u);
    // ON HOLD and the timer
    g.fillStyle = ORANGE; g.font = font(30, FONT.monoB); g.fillText('ON HOLD', W / 2, 580 * u);
    const sec = Math.floor(s.hold ?? 3); const hh = String(Math.floor(sec / 3600)).padStart(2, '0'), mm = String(Math.floor(sec / 60) % 60).padStart(2, '0'), ss = String(sec % 60).padStart(2, '0');
    const tick = 1 - clamp(((s.hold ?? 3) % 1) / 0.25); g.save(); g.translate(W / 2, 648 * u); g.scale(1 + 0.05 * tick, 1 + 0.05 * tick);
    g.fillStyle = '#ffffff'; g.font = font(78, FONT.monoB); g.fillText(`${hh}:${mm}:${ss}`, 0, 0); g.restore();
    // the hold music
    g.fillStyle = CYAN; const n = 22; for (let i = 0; i < n; i++) { const a = 0.2 + 0.8 * Math.abs(Math.sin((s.t || 0) * 6.3 + i * 0.6) * Math.sin((s.t || 0) * 2.9 + i * 0.27));
      const bh = 70 * u * a; rr(g, W / 2 - 200 * u + i * (400 * u / n), 745 * u - bh / 2, 400 * u / n * 0.55, bh, 4 * u); g.fill(); }
    g.fillStyle = '#93a0ae'; g.font = font(24, FONT.uiM); g.fillText('♪  hold music', W / 2, 810 * u);
    // buttons
    const btn = (x, y, label, opts = {}) => { const r = 62 * u; const sc = opts.scale || 1; g.save(); g.translate(x, y); g.scale(sc, sc);
      g.fillStyle = opts.fill || 'rgba(255,255,255,0.13)'; g.beginPath(); g.arc(0, 0, r, 0, 7); g.fill();
      if (opts.glow) { g.shadowColor = opts.fill; g.shadowBlur = 40 * u * opts.glow; g.beginPath(); g.arc(0, 0, r, 0, 7); g.fill(); g.shadowBlur = 0; }
      if (opts.icon) opts.icon(0, 0); g.fillStyle = opts.lc || '#dfe5ec'; g.font = font(24, opts.lf || FONT.uiM); g.fillText(label, 0, r + 30 * u); g.restore(); };
    const ic = (txt) => (x, y) => { g.fillStyle = '#ffffff'; g.font = font(40, FONT.ui); g.fillText(txt, x, y + 2 * u); };
    const press = s.press || 0;
    btn(W * 0.22, 920 * u, 'mute', { icon: ic('🔇') }); btn(W * 0.5, 920 * u, 'keypad', { icon: (x, y) => { g.fillStyle = '#fff'; for (let i = 0; i < 9; i++) { g.beginPath(); g.arc(x + ((i % 3) - 1) * 20 * u, y + (Math.floor(i / 3) - 1) * 20 * u, 6 * u, 0, 7); g.fill(); } } });
    btn(W * 0.78, 920 * u, 'speaker', { icon: ic('🔊') });
    btn(W * 0.22, 1090 * u, 'add call', { icon: ic('+') });
    btn(W * 0.5, 1090 * u, 'HAND OFF', { fill: '#2fe6f5', glow: 0.5 + press, scale: 1 + 0.12 * Math.sin(Math.PI * clamp(press)) + 0.04 * (s.pulse || 0), lc: '#7ff7ff', lf: FONT.black,
      icon: (x, y) => robotIcon(g, x, y + 4 * u, 76 * u) });
    btn(W * 0.78, 1090 * u, 'hold', { icon: ic('⏸') });
    g.fillStyle = '#ff3b30'; rr(g, W / 2 - 70 * u, 1190 * u, 140 * u, 80 * u, 40 * u); g.fill();
    g.save(); g.translate(W / 2, 1230 * u); g.rotate(Math.PI * 0.75); phoneGlyph(g, 0, 0, 48 * u, '#fff'); g.restore();
    if (press > 0) { g.strokeStyle = `rgba(95,244,255,${0.8 * (1 - press)})`; g.lineWidth = 8 * u; g.beginPath(); g.arc(W * 0.5, 1090 * u, 62 * u + 160 * u * press, 0, 7); g.stroke(); }
    if (scr === 'wait') {                 // EST. WAIT fills the screen
      const k = clamp(s.k ?? 1); g.fillStyle = `rgba(11,13,18,${0.94 * sstep(0, 0.15, k)})`; g.fillRect(0, 0, W, H);
      const a = sstep(0.0, 0.2, k); g.globalAlpha = a; g.fillStyle = '#93a0ae'; g.font = font(54, FONT.black); g.fillText('EST. WAIT', W / 2, 420 * u);
      const num = Math.min(47, Math.floor(easeOut(clamp(k / 0.55)) * 47 + 0.0001)); const bump = 1 + 0.25 * Math.exp(-((k * 4) % 1) * 6) * (k < 0.55 ? 1 : 0) + (k >= 0.55 ? 0.12 * Math.exp(-(k - 0.55) * 14) : 0);
      g.save(); g.translate(W / 2, 660 * u); g.scale(bump, bump); g.fillStyle = '#ffffff'; g.font = font(330, FONT.black); g.fillText(String(num), 0, 0); g.restore();
      g.fillStyle = ORANGE; g.font = font(110, FONT.black); g.fillText('MIN', W / 2, 900 * u); g.globalAlpha = 1;
    }
  } else if (scr === 'callrep') {      // the call she could make herself
    g.textAlign = 'center'; g.fillStyle = '#93a0ae'; g.font = font(30, FONT.uiM); g.fillText('Customer Care', W / 2, 260 * u);
    g.fillStyle = '#ffffff'; g.font = font(54, FONT.disp); g.fillText('Speak to a', W / 2, 420 * u); g.fillText('representative', W / 2, 485 * u);
    g.fillStyle = '#93a0ae'; g.font = font(28, FONT.uiM); g.fillText('A real human. Out loud.', W / 2, 560 * u);
    const pulse = 1 + 0.04 * Math.sin((s.t || 0) * 6);
    g.save(); g.translate(W / 2, 860 * u); g.scale(pulse, pulse); g.fillStyle = GREEN; g.shadowColor = GREEN; g.shadowBlur = 50 * u; rr(g, -200 * u, -110 * u, 400 * u, 220 * u, 110 * u); g.fill(); g.shadowBlur = 0;
    phoneGlyph(g, -95 * u, 0, 110 * u, '#ffffff'); g.fillStyle = '#ffffff'; g.font = font(78, FONT.black); g.textAlign = 'left'; g.fillText('CALL', -30 * u, 6 * u); g.restore();
  } else if (scr === 'prompt') {       // read your card out loud
    g.textAlign = 'center'; g.fillStyle = '#93a0ae'; g.font = font(30, FONT.uiM); g.fillText('Customer Care · automated', W / 2, 220 * u);
    g.fillStyle = '#ffffff'; g.font = font(50, FONT.disp); ['Please say the', 'last four digits', 'of your card'].forEach((l, i) => g.fillText(l, W / 2, 360 * u + i * 66 * u));
    const k = (s.t || 0) * 2; for (let i = 0; i < 3; i++) { g.strokeStyle = `rgba(79,240,255,${0.5 * (1 - ((k + i / 3) % 1))})`; g.lineWidth = 6 * u; g.beginPath(); g.arc(W / 2, 780 * u, 90 * u + 120 * u * ((k + i / 3) % 1), 0, 7); g.stroke(); }
    g.fillStyle = CYAN; g.beginPath(); g.arc(W / 2, 780 * u, 90 * u, 0, 7); g.fill(); micGlyph(g, W / 2, 790 * u, 100 * u, '#062a30');
    g.fillStyle = '#93a0ae'; g.font = font(30, FONT.uiM); g.fillText('Listening…', W / 2, 960 * u);
    g.fillStyle = '#2a3140'; for (let i = 0; i < 4; i++) { rr(g, W / 2 - 170 * u + i * 90 * u, 1030 * u, 70 * u, 90 * u, 14 * u); g.fill(); }
  } else if (scr === 'summary') {      // the robot's report, on the lock screen
    const bg = g.createLinearGradient(0, 0, 0, H); bg.addColorStop(0, '#2b3a55'); bg.addColorStop(1, '#141a26'); g.fillStyle = bg; g.fillRect(0, 0, W, H);
    g.fillStyle = '#ffffff'; g.textAlign = 'center'; g.font = font(150, FONT.disp); g.fillText(s.clock || '8:12', W / 2, 270 * u);
    g.font = font(30, FONT.uiM); g.fillStyle = '#c9d3e0'; g.fillText('Tuesday', W / 2, 150 * u);
    const k = easeOutBack(clamp(s.k ?? 1)); g.save(); g.translate(0, (1 - k) * -260 * u); g.globalAlpha = clamp((s.k ?? 1) * 3);
    g.fillStyle = 'rgba(245,247,250,0.95)'; rr(g, 30 * u, 420 * u, W - 60 * u, 520 * u, 40 * u); g.fill();
    g.fillStyle = '#2fe6f5'; rr(g, 60 * u, 452 * u, 70 * u, 70 * u, 18 * u); g.fill(); robotIcon(g, 95 * u, 490 * u, 52 * u);
    g.textAlign = 'left'; g.fillStyle = '#5b6573'; g.font = font(28, FONT.uiM); g.fillText('YOUR ROBOT  ·  now', 150 * u, 488 * u);
    g.fillStyle = '#0d1117'; g.font = font(44, FONT.black); g.fillText('Call summary', 60 * u, 590 * u);
    const items = s.items || ['On hold: 47 min', 'Transfers: 4', '$4 charge: explained'];
    items.forEach((it, i) => { const a = clamp((s.k2 ?? 1) * 3 - i); g.globalAlpha = a; g.fillStyle = '#2fe6f5'; g.beginPath(); g.arc(78 * u, 680 * u + i * 82 * u, 11 * u, 0, 7); g.fill();
      g.fillStyle = '#1d232c'; g.font = font(38, FONT.ui); g.fillText(it, 108 * u, 683 * u + i * 82 * u); });
    g.restore(); g.globalAlpha = 1;
  } else if (scr === 'dark') { /* face-down / off */ }
}
export class Phone {
  constructor() {
    const g = this.root = new THREE.Group();
    this.body = new THREE.Mesh(rbox(PHONE.w, PHONE.h, PHONE.d, 0.011, 4), gloss(0x2a2d33, { shininess: 70, specular: 0x777c86, rimAmt: 0.3 })); g.add(this.body);
    this.tex = liveTex(600, 1300);
    this.screen = new THREE.Mesh(new THREE.PlaneGeometry(PHONE.w - 0.005, PHONE.h - 0.005), new THREE.MeshBasicMaterial({ map: this.tex, toneMapped: false, color: new THREE.Color(1.15, 1.15, 1.15) }));
    this.screen.position.z = PHONE.d / 2 + 0.0004; g.add(this.screen);
    const cam = new THREE.Mesh(new THREE.CylinderGeometry(0.006, 0.006, 0.002, 16), gloss(0x101114)); cam.rotation.x = Math.PI / 2; cam.position.set(-0.02, 0.06, -PHONE.d / 2 - 0.001); g.add(cam);
  }
  draw(state, key) { this.tex.userData.redraw(key ?? JSON.stringify(state), (g, w, h) => drawPhone(g, w, h, state)); }
  /** a point on the screen in the phone's local space from design units (600 x 1300) */
  local(x, y) { return V3((x / 600 - 0.5) * (PHONE.w - 0.005), (0.5 - y / 1300) * (PHONE.h - 0.005), PHONE.d / 2 + 0.001); }
}
// a hand for close-ups: a thumb that taps and hovers (the phone's own frame)
export function makeThumb(skinMat, sleeveMat) {
  const g = new THREE.Group();
  const th = new THREE.Mesh(new THREE.CapsuleGeometry(0.0105, 0.05, 6, 12), skinMat); th.position.y = -0.03; g.add(th);
  const nail = new THREE.Mesh(new THREE.SphereGeometry(0.0085, 12, 8), clay(0xf0d2c0, { rimAmt: 0.2 })); nail.scale.set(1, 1.2, 0.35); nail.position.set(0, -0.012, 0.008); g.add(nail);
  const base = new THREE.Mesh(new THREE.SphereGeometry(0.032, 16, 12), skinMat); base.scale.set(1.1, 1.35, 0.75); base.position.set(0.016, -0.085, -0.014); g.add(base);
  if (sleeveMat) { const sl = new THREE.Mesh(new THREE.CapsuleGeometry(0.038, 0.22, 6, 16), sleeveMat); sl.position.set(0.05, -0.21, -0.05); sl.rotation.set(-0.5, 0, 0.35); g.add(sl); }
  return g;          // the tip sits at the origin, pointing up (+y)
}
/** her left hand holding the phone, for close-ups (the phone's own frame): palm behind, fingers round the right edge,
 *  thumb on the left edge, the coat sleeve leaving the frame */
export function phoneHand(skinMat, sleeveMat) {
  const g = new THREE.Group();
  const palm = new THREE.Mesh(rbox(0.082, 0.095, 0.03, 0.014), skinMat); palm.position.set(0.0, -0.035, -0.022); g.add(palm);
  for (let i = 0; i < 4; i++) { const f = new THREE.Mesh(new THREE.CapsuleGeometry(0.0095, 0.02, 6, 10), skinMat); f.rotation.z = Math.PI / 2; f.position.set(0.038, -0.002 - i * 0.0215, 0.003); g.add(f);
    const k = new THREE.Mesh(new THREE.SphereGeometry(0.0105, 10, 8), skinMat); k.position.set(0.043, -0.002 - i * 0.0215, -0.008); g.add(k); }
  const th = new THREE.Mesh(new THREE.CapsuleGeometry(0.011, 0.04, 6, 10), skinMat); th.position.set(-0.04, -0.03, 0.006); th.rotation.z = -0.3; g.add(th);
  const thb = new THREE.Mesh(new THREE.SphereGeometry(0.022, 12, 10), skinMat); thb.position.set(-0.035, -0.065, -0.008); g.add(thb);
  if (sleeveMat) { const sl = new THREE.Mesh(new THREE.CapsuleGeometry(0.04, 0.22, 6, 16), sleeveMat); sl.position.set(-0.03, -0.17, -0.07); sl.rotation.set(-0.55, 0, -0.25); g.add(sl); }
  return g;
}

// ---------------------------------------------------------------- the bill
export function drawBill(g, W, H, k = 0) {
  const u = W / 850;
  g.fillStyle = '#fbfaf6'; g.fillRect(0, 0, W, H);
  g.fillStyle = '#e9eef3'; g.fillRect(0, 0, W, 150 * u);
  g.fillStyle = '#1b2a3a'; g.font = `${46 * u}px ${FONT.black}`; g.fillText('YOUR INTERNET CO.', 60 * u, 90 * u);
  g.strokeStyle = '#1b2a3a'; g.lineWidth = 7 * u; for (let i = 0; i < 3; i++) { g.beginPath(); g.arc(W - 110 * u, 105 * u, (18 + i * 18) * u, Math.PI * 1.2, Math.PI * 1.8); g.stroke(); }
  g.fillStyle = '#1b2a3a'; g.beginPath(); g.arc(W - 110 * u, 105 * u, 7 * u, 0, 7); g.fill();
  g.fillStyle = '#5b6573'; g.font = `${24 * u}px ${FONT.uiM}`; g.fillText('MONTHLY STATEMENT  ·  ACCOUNT •••• 2847', 60 * u, 200 * u);
  g.fillStyle = '#1d232c'; g.font = `${30 * u}px ${FONT.ui}`;
  const rows = [['Internet 500', '$65.00'], ['Modem rental', '$15.00'], ['Taxes', '$3.12'], ['Convenience fee', '$4.00'], ['Paperless discount', '−$0.00']];
  rows.forEach(([a, b], i) => { const y = 290 * u + i * 74 * u; g.fillStyle = i === 3 ? '#1d232c' : '#3b4450'; g.font = `${30 * u}px ${i === 3 ? FONT.black : FONT.ui}`; g.fillText(a, 60 * u, y);
    g.textAlign = 'right'; g.fillText(b, W - 60 * u, y); g.textAlign = 'left'; g.strokeStyle = '#dde3ea'; g.lineWidth = 2 * u; g.beginPath(); g.moveTo(60 * u, y + 26 * u); g.lineTo(W - 60 * u, y + 26 * u); g.stroke(); });
  g.fillStyle = '#1d232c'; g.font = `${40 * u}px ${FONT.black}`; g.fillText('TOTAL DUE', 60 * u, 720 * u); g.textAlign = 'right'; g.fillText('$87.12', W - 60 * u, 720 * u); g.textAlign = 'left';
  g.fillStyle = '#8a95a3'; g.font = `${22 * u}px ${FONT.uiM}`; ['Questions? Call Customer Care 24/7.', 'Your call is very important to us.'].forEach((s, i) => g.fillText(s, 60 * u, 820 * u + i * 36 * u));
  // the circle, drawn on in hot orange (k = 0..1)
  if (k > 0) { const cx = W - 140 * u, cy = 290 * u + 3 * 74 * u - 10 * u; g.strokeStyle = ORANGE; g.lineWidth = 11 * u; g.lineCap = 'round'; g.beginPath();
    const a0 = -2.4, a1 = a0 + Math.PI * 2.15 * clamp(k); for (let a = a0; a <= a1; a += 0.05) { const r = 1 + 0.06 * Math.sin(a * 3); const x = cx + Math.cos(a) * 120 * u * r, y = cy + Math.sin(a) * 52 * u * r; if (a === a0) g.moveTo(x, y); else g.lineTo(x, y); } g.stroke(); }
}
export class Bill {
  constructor() { this.tex = liveTex(850, 1100); const m = new THREE.MeshLambertMaterial({ map: this.tex, emissive: 0x2a2a2a, side: THREE.DoubleSide });
    const geo = new THREE.PlaneGeometry(0.216, 0.2796, 8, 8); this.mesh = new THREE.Mesh(geo, m); this.root = new THREE.Group(); this.root.add(this.mesh); this.base = geo.attributes.position.array.slice(); }
  draw(k) { this.tex.userData.redraw('b' + k.toFixed(3), (g, w, h) => drawBill(g, w, h, k)); }
  bend(c) { const p = this.mesh.geometry.attributes.position; for (let i = 0; i < p.count; i++) { const x = this.base[i * 3], y = this.base[i * 3 + 1]; p.setZ(i, c * (x * x * 8 + y * y * 2)); } p.needsUpdate = true; this.mesh.geometry.computeVertexNormals(); }
}

// ---------------------------------------------------------------- the keypad
const KEYS = [['1', ''], ['2', 'ABC'], ['3', 'DEF'], ['4', 'GHI'], ['5', 'JKL'], ['6', 'MNO'], ['7', 'PQRS'], ['8', 'TUV'], ['9', 'WXYZ'], ['*', ''], ['0', '+'], ['#', '']];
function keyFace(d, sub, lit, col) {
  return canvasTex(256, 256, (g, w, h) => { g.fillStyle = lit ? col : '#f4f5f7'; g.fillRect(0, 0, w, h);
    g.fillStyle = lit ? '#ffffff' : '#1d2129'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.font = `150px ${FONT.disp}`; g.fillText(d, w / 2, h / 2 - (sub ? 18 : 0));
    if (sub) { g.font = `40px ${FONT.ui}`; g.fillStyle = lit ? 'rgba(255,255,255,0.85)' : '#7a8290'; g.fillText(sub, w / 2, h / 2 + 78); } });
}
export class Keypad {
  constructor({ size = 0.1, gap = 0.02, litCol = '#2fd6e6' } = {}) {
    const g = this.root = new THREE.Group(); this.keys = [];
    const base = new THREE.Mesh(rbox(3 * size + 4 * gap, 4 * size + 5 * gap, 0.04, 0.03), gloss(0x22252c, { shininess: 50, rimAmt: 0.3 })); base.position.z = -0.02; g.add(base);
    KEYS.forEach(([d, sub], i) => {
      const geo = rbox(size, size, 0.035, size * 0.22, 3);
      const side = gloss(0xe8eaee, { shininess: 60, rimAmt: 0.25 });
      const face = new THREE.MeshBasicMaterial({ map: keyFace(d, sub, false), toneMapped: true }); const faceLit = new THREE.MeshBasicMaterial({ map: keyFace(d, sub, true, litCol), toneMapped: false });
      const k = new THREE.Mesh(geo, side); const top = new THREE.Mesh(new THREE.PlaneGeometry(size * 0.86, size * 0.86), face); top.position.z = 0.0176; k.add(top);
      const x = ((i % 3) - 1) * (size + gap), y = (1.5 - Math.floor(i / 3)) * (size + gap); k.position.set(x, y, 0.02); g.add(k);
      this.keys.push({ d, mesh: k, top, face, faceLit, x, y, glow: null });
    });
  }
  key(d) { return this.keys.find((k) => k.d === d); }
  /** press: 0..1 depth; lit: 0..1 */
  set(d, press, lit) { const k = this.key(d); if (!k) return; k.mesh.position.z = 0.02 - 0.018 * press; k.top.material = lit > 0.5 ? k.faceLit : k.face; const s = 1 + 0.08 * lit * (1 - press); k.mesh.scale.set(s, s, 1); }
}
export function bigKey(d = '0', sub = '+') {               // the giant 0 key that slams down
  const g = new THREE.Group(); const k = new THREE.Mesh(rbox(1.6, 0.45, 1.6, 0.3, 4), gloss(0xf2f3f5, { shininess: 70, rimAmt: 0.3 })); k.position.y = 0.225; g.add(k);
  const top = new THREE.Mesh(new THREE.PlaneGeometry(1.4, 1.4), new THREE.MeshBasicMaterial({ map: keyFace(d, sub, true, '#2fd6e6'), toneMapped: false })); top.rotation.x = -Math.PI / 2; top.position.y = 0.452; g.add(top);
  return g;
}

// ---------------------------------------------------------------- the empty cubicle
export function cubicle() {
  const g = new THREE.Group(); const fabric = clay(0x7f8fa3, { rimAmt: 0.2 }), trim = clay(0xc9ced6), wood = clay(0xd8c2a0), dark = gloss(0x1f2228, { shininess: 50 });
  for (const [x, z, w, d] of [[0, -0.9, 2.4, 0.06], [-1.2, -0.1, 0.06, 1.6], [1.2, -0.1, 0.06, 1.6]]) { const p = new THREE.Mesh(rbox(w, 1.45, d, 0.02), fabric); p.position.set(x, 0.725, z); g.add(p);
    const cap = new THREE.Mesh(rbox(w + 0.02, 0.04, d + 0.02, 0.015), trim); cap.position.set(x, 1.46, z); g.add(cap); }
  const desk = new THREE.Mesh(rbox(2.3, 0.04, 0.8, 0.015), wood); desk.position.set(0, 0.74, -0.48); g.add(desk);
  const mon = new THREE.Mesh(rbox(0.62, 0.38, 0.03, 0.015), dark); mon.position.set(0.15, 1.06, -0.72); g.add(mon);
  const mtex = liveTex(512, 300); const ms = new THREE.Mesh(new THREE.PlaneGeometry(0.58, 0.34), new THREE.MeshBasicMaterial({ map: mtex, toneMapped: false })); ms.position.set(0.15, 1.06, -0.7); g.add(ms);
  const stand = new THREE.Mesh(new THREE.CylinderGeometry(0.02, 0.02, 0.16, 8), dark); stand.position.set(0.15, 0.82, -0.74); g.add(stand);
  // the headset left on the desk
  const hs = new THREE.Group(); const band = new THREE.Mesh(new THREE.TorusGeometry(0.09, 0.009, 8, 24, Math.PI), dark); hs.add(band);
  for (const s of [-1, 1]) { const cup = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.04, 0.03, 16), dark); cup.position.set(0.09 * s, 0, 0); cup.rotation.z = Math.PI / 2; hs.add(cup); }
  const boom = new THREE.Mesh(new THREE.CylinderGeometry(0.004, 0.004, 0.12, 6), dark); boom.position.set(0.11, -0.05, 0.04); boom.rotation.set(1.2, 0, 0.3); hs.add(boom);
  hs.rotation.x = -Math.PI / 2 + 0.15; hs.position.set(-0.45, 0.77, -0.4); g.add(hs);
  const mug = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.036, 0.1, 16), clay(0xf4f1ea)); mug.position.set(-0.8, 0.81, -0.62); g.add(mug);
  const note = new THREE.Mesh(new THREE.PlaneGeometry(0.08, 0.08), new THREE.MeshLambertMaterial({ map: canvasTex(128, 128, (c, w, h) => { c.fillStyle = '#ffe873'; c.fillRect(0, 0, w, h); c.fillStyle = '#333'; c.font = `44px ${FONT.hand}`; c.fillText('BRB', 22, 78); }) }));
  note.position.set(0.47, 1.18, -0.705); g.add(note);
  // the chair, spinning slowly
  const chair = new THREE.Group(); const seat = new THREE.Mesh(rbox(0.5, 0.08, 0.48, 0.04), clay(0x2d3138)); seat.position.y = 0.48; chair.add(seat);
  const back = new THREE.Mesh(rbox(0.46, 0.55, 0.06, 0.04), clay(0x2d3138)); back.position.set(0, 0.82, -0.22); chair.add(back);
  const post = new THREE.Mesh(new THREE.CylinderGeometry(0.025, 0.025, 0.36, 10), dark); post.position.y = 0.27; chair.add(post);
  for (let i = 0; i < 5; i++) { const a = i / 5 * Math.PI * 2; const leg = new THREE.Mesh(rbox(0.3, 0.03, 0.04, 0.012), dark); leg.position.set(Math.cos(a) * 0.15, 0.07, Math.sin(a) * 0.15); leg.rotation.y = -a; chair.add(leg);
    const w = new THREE.Mesh(new THREE.SphereGeometry(0.025, 8, 6), dark); w.position.set(Math.cos(a) * 0.29, 0.03, Math.sin(a) * 0.29); chair.add(w); }
  chair.position.set(0, 0, 0.15); g.add(chair);
  const light = new THREE.Mesh(new THREE.PlaneGeometry(1.2, 0.5), glowMat(new THREE.Color(1.3, 1.35, 1.4))); light.rotation.x = Math.PI / 2; light.position.set(0, 2.6, -0.3); g.add(light);
  g.userData = { chair, mtex };
  return g;
}

// ---------------------------------------------------------------- takeout, an egg roll, a drink
export function takeoutBox() {
  const g = new THREE.Group(); const white = clay(0xf7f5f0, { rimAmt: 0.25 });
  const body = new THREE.Mesh(new THREE.CylinderGeometry(0.078, 0.058, 0.11, 4, 1), white); body.rotation.y = Math.PI / 4; body.position.y = 0.055; g.add(body);
  const print = new THREE.Mesh(new THREE.PlaneGeometry(0.075, 0.07), new THREE.MeshLambertMaterial({ transparent: true, map: canvasTex(200, 190, (c, w, h) => { c.clearRect(0, 0, w, h); c.fillStyle = '#c8322b';
    c.beginPath(); c.moveTo(w / 2, 20); c.lineTo(w / 2 + 50, 60); c.lineTo(w / 2 - 50, 60); c.fill(); c.fillRect(w / 2 - 34, 66, 68, 10); c.beginPath(); c.moveTo(w / 2, 70); c.lineTo(w / 2 + 62, 112); c.lineTo(w / 2 - 62, 112); c.fill();
    c.fillRect(w / 2 - 40, 116, 80, 12); c.font = `26px ${FONT.black}`; c.textAlign = 'center'; c.fillText('THANK YOU', w / 2, 168); }) }));
  print.position.set(0, 0.06, 0.0605); print.rotation.x = -0.09; g.add(print);
  for (const s of [-1, 1]) { const f = new THREE.Mesh(new THREE.PlaneGeometry(0.11, 0.05), clay(0xefece5, { side: THREE.DoubleSide })); f.position.set(0, 0.125, s * 0.03); f.rotation.x = s * 0.7; g.add(f); }
  const handle = new THREE.Mesh(new THREE.TorusGeometry(0.06, 0.0025, 6, 24, Math.PI), gloss(0x9aa0a8)); handle.position.y = 0.11; g.add(handle);
  return g;
}
export function eggRoll() {
  const g = new THREE.Group();
  const tex = canvasTex(256, 128, (c, w, h) => { const R = rng(3); c.fillStyle = '#d99a3e'; c.fillRect(0, 0, w, h); for (let i = 0; i < 260; i++) { c.fillStyle = `rgba(${150 + R() * 90 | 0},${90 + R() * 60 | 0},${30 + R() * 20 | 0},0.5)`; c.beginPath(); c.arc(R() * w, R() * h, 2 + R() * 7, 0, 7); c.fill(); }
    for (let i = 0; i < 40; i++) { c.fillStyle = 'rgba(255,230,160,0.55)'; c.beginPath(); c.arc(R() * w, R() * h, 2 + R() * 4, 0, 7); c.fill(); } });
  const m = new THREE.Mesh(new THREE.CapsuleGeometry(0.03, 0.11, 8, 18), new THREE.MeshLambertMaterial({ map: tex, emissive: 0x2a1404 })); m.rotation.z = Math.PI / 2; g.add(m);
  for (const s of [-1, 1]) { const end = new THREE.Mesh(new THREE.SphereGeometry(0.031, 14, 10), clay(0xe8b25a)); end.scale.set(0.4, 1, 1); end.position.x = s * 0.075; g.add(end); }
  return g;
}
export function drinkSet() {
  const g = new THREE.Group();
  const glass = new THREE.Mesh(lathe([[0, 0], [0.036, 0], [0.04, 0.005], [0.043, 0.1], [0.041, 0.101], [0.038, 0.006], [0, 0.006]], 24), new THREE.MeshPhongMaterial({ color: 0xdfeef7, transparent: true, opacity: 0.38, shininess: 120, specular: 0xffffff, side: THREE.DoubleSide, depthWrite: false }));
  g.add(glass);
  const liquid = new THREE.Mesh(new THREE.CylinderGeometry(0.039, 0.036, 1, 24), clay(0x9c1f3a, { rimAmt: 0.3, transparent: true, opacity: 0.9 })); liquid.position.y = 0.006; g.add(liquid);
  const bottle = new THREE.Group(); const bm = new THREE.MeshPhongMaterial({ color: 0x2d5a34, shininess: 100, specular: 0x88aa88 });
  bottle.add(new THREE.Mesh(lathe([[0, 0], [0.036, 0], [0.037, 0.2], [0.03, 0.235], [0.013, 0.26], [0.013, 0.32], [0, 0.32]], 24), bm));
  const label = new THREE.Mesh(new THREE.CylinderGeometry(0.0372, 0.0372, 0.08, 24, 1, true), clay(0xf1e6cc)); label.position.y = 0.1; bottle.add(label);
  g.add(bottle);
  const stream = new THREE.Mesh(new THREE.CylinderGeometry(0.0035, 0.0045, 1, 8), clay(0xb3243f, { rimAmt: 0.5 })); g.add(stream);
  g.userData = { glass, liquid, bottle, stream };
  return g;
}
export function notebook() {
  const g = new THREE.Group(); const tex = liveTex(800, 560);
  const pages = new THREE.Mesh(new THREE.PlaneGeometry(0.3, 0.21), new THREE.MeshLambertMaterial({ map: tex, emissive: 0x262626 })); pages.rotation.x = -Math.PI / 2; g.add(pages);
  const cover = new THREE.Mesh(rbox(0.31, 0.008, 0.22, 0.004), clay(0x2b3a52)); cover.position.y = -0.005; g.add(cover);
  const pen = new THREE.Mesh(new THREE.CylinderGeometry(0.0045, 0.0045, 0.14, 10), gloss(0x111216)); g.userData = { tex, pen };
  return g;
}
export function drawNotebook(g, W, H, k) {
  g.fillStyle = '#fbf8f0'; g.fillRect(0, 0, W, H); g.fillStyle = '#e4dccb'; g.fillRect(W / 2 - 3, 0, 6, H);
  g.strokeStyle = 'rgba(90,130,200,0.35)'; g.lineWidth = 2; for (let y = 70; y < H; y += 44) { g.beginPath(); g.moveTo(20, y); g.lineTo(W - 20, y); g.stroke(); }
  g.fillStyle = '#1f2a44'; g.font = `40px ${FONT.hand}`;
  const lines = ['things to do', '— not wait', '— egg rolls (3rd?)', '— write a song', '  about this'];
  let chars = Math.floor(k * lines.join('').length);
  lines.forEach((l, i) => { if (chars <= 0) return; const s = l.slice(0, chars); chars -= l.length; g.fillText(s, W / 2 + 30, 62 + i * 44); });
}

// ---------------------------------------------------------------- the receipt (bridge) and the stamp
export const RECEIPT_ROWS = [['CALL DURATION', '47:00'], ['REPRESENTATIVES', '3'], ['TRANSFERS', '4'], ['$4.00 CHARGE', 'EXPLAINED ✓']];
// The receipt hangs from the chest slot, so it is printed bottom-up: the header sits at the bottom of the canvas and each
// new row lands above the last, right at the slot, reading upright as it hangs (Y(px from the bottom) -> canvas y).
export const RECEIPT_PX = { header: 260, row0: 380, rowH: 150, foot: 960, used: 2048 };
export function drawReceipt(g, W, H, s) {
  const u = W / 512; const Y = (py) => H - py * u; g.fillStyle = '#fbfbf7'; g.fillRect(0, 0, W, H);
  g.fillStyle = '#20232a'; g.textAlign = 'center'; g.textBaseline = 'middle';
  g.font = `${44 * u}px ${FONT.monoB}`; g.fillText('* CALL RECEIPT *', W / 2, Y(200));
  g.font = `${28 * u}px ${FONT.mono}`; g.fillText('your robot, on your behalf', W / 2, Y(140)); g.fillText('- - - - - - - - - - - - - -', W / 2, Y(80));
  RECEIPT_ROWS.forEach(([a, b], i) => { if (i >= (s.rows ?? 4)) return; const y = Y(RECEIPT_PX.row0 + i * RECEIPT_PX.rowH); g.fillStyle = '#20232a';
    g.font = `${33 * u}px ${FONT.monoB}`; g.textAlign = 'left'; g.fillText(a, 22 * u, y - 24 * u); g.textAlign = 'right'; g.font = `${46 * u}px ${FONT.monoB}`; g.fillText(b, W - 22 * u, y + 26 * u); g.textAlign = 'left';
    g.fillStyle = 'rgba(32,35,42,0.4)'; for (let x = 22 * u; x < W - 22 * u - g.measureText(b).width - 12 * u; x += 16 * u) g.fillRect(x, y + 26 * u, 5 * u, 5 * u); });
  if ((s.strike ?? 0) > 0) { g.strokeStyle = ORANGE; g.lineWidth = 9 * u; g.lineCap = 'round'; const y = Y(RECEIPT_PX.row0 + 3 * RECEIPT_PX.rowH) - 24 * u; g.beginPath(); g.moveTo(16 * u, y); g.lineTo(16 * u + (W - 32 * u) * clamp(s.strike), y); g.stroke(); }
  if ((s.rows ?? 4) >= 4) { g.fillStyle = '#20232a'; g.textAlign = 'center'; g.font = `${28 * u}px ${FONT.mono}`; g.fillText('- - - - - - - - - - - - - -', W / 2, Y(RECEIPT_PX.foot - 50)); g.font = `${30 * u}px ${FONT.monoB}`; g.fillText('THANK YOU FOR HOLDING :)', W / 2, Y(RECEIPT_PX.foot));
    // the CVS-length tail: coupons nobody asked for
    const coupons = ['SAVE 0% ON YOUR NEXT HOLD', 'FREE HOLD MUSIC (FOREVER)', 'PRESS 1 FOR MORE COUPONS', 'YOUR CALL IS IMPORTANT', 'SURVEY: PAGE 1 OF 400'];
    coupons.forEach((c, i) => { const y = Y(1120 + i * 190); g.strokeStyle = '#20232a'; g.setLineDash([10 * u, 8 * u]); g.lineWidth = 3 * u; g.strokeRect(20 * u, y - 70 * u, W - 40 * u, 140 * u); g.setLineDash([]);
      g.fillStyle = '#20232a'; g.font = `${26 * u}px ${FONT.monoB}`; g.fillText(c, W / 2, y - 18 * u); for (let k = 0; k < 40; k++) { const bw = (k * 7919 % 5 + 1) * 2 * u; g.fillRect(60 * u + k * 10 * u, y + 12 * u, bw, 40 * u); } }); }
  if ((s.stamp ?? 0) > 0) {               // $5.00 in hot orange, rubber-stamped across the rows
    const cy = Y(RECEIPT_PX.row0 + 1.5 * RECEIPT_PX.rowH);
    g.save(); g.translate(W / 2, cy); g.rotate(-0.14); g.globalAlpha = 0.93; g.strokeStyle = ORANGE; g.lineWidth = 11 * u; rr(g, -215 * u, -95 * u, 430 * u, 190 * u, 22 * u); g.stroke();
    g.fillStyle = ORANGE; g.font = `${150 * u}px ${FONT.stamp}`; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText('$5.00', 0, 10 * u); g.restore();
    const R = rng(5); g.fillStyle = '#fbfbf7'; g.globalAlpha = 0.55; for (let i = 0; i < 200; i++) g.fillRect(W / 2 - 215 * u + R() * 430 * u, cy - 95 * u + R() * 190 * u, 2 + R() * 4, 2 + R() * 3); g.globalAlpha = 1;
  }
}
export class Receipt {
  constructor() { this.W = 0.1; this.texH = 2048; this.tex = liveTex(512, this.texH); this.Ltex = this.W * this.texH / 512; const segs = 70;
    this.geo = new THREE.PlaneGeometry(this.W, 1, 1, segs); this.rows = segs + 1;
    this.mesh = new THREE.Mesh(this.geo, new THREE.MeshLambertMaterial({ map: this.tex, side: THREE.DoubleSide, emissive: 0x3a3a3a })); this.mesh.frustumCulled = false; }
  /** printed length (m) for a content height in canvas px from the bottom */
  lenFor(px) { return px / 512 * this.W; }
  draw(s) { this.tex.userData.redraw(JSON.stringify(s), (g, w, h) => drawReceipt(g, w, h, s)); }
  /** shape the printed strip: origin = slot (world), fwd = out of the slot, side = across the paper (reader's right),
   *  L = printed length; it bends down under gravity and lies on the floor at floorY */
  shape(origin, fwd, side, L, floorY, shake = 0, t = 0) {
    const p = this.geo.attributes.position, uv = this.geo.attributes.uv; const n = this.rows;
    const ds = Math.max(L, 1e-4) / (n - 1); const pos = origin.clone(); const flat = V3(fwd.x, 0, fwd.z).normalize(); this.pts = []; this.ds = ds;
    let th = -0.55;                                   // pitch below the horizontal; it arcs out over the lap, then drops
    for (let i = 0; i < n; i++) {
      const s = i * ds; const c = L - s; const wob = shake * Math.sin(t * 47 + i * 0.5) * 0.006 * (1 - i / n);
      for (let k = 0; k < 2; k++) { const idx = i * 2 + k; const sx = (k === 0 ? -1 : 1) * this.W / 2;
        p.setXYZ(idx, pos.x + side.x * sx + wob, pos.y + side.y * sx, pos.z + side.z * sx); uv.setXY(idx, k, clamp(c / this.Ltex, 0, 1)); }
      this.pts.push(pos.clone());
      th = Math.max(-Math.PI / 2, th - (s < 0.12 ? 5.0 : 9.0) * ds);
      const onFloor = pos.y <= floorY + 0.004; const dir = onFloor ? flat : flat.clone().multiplyScalar(Math.cos(th)).add(V3(0, Math.sin(th), 0));
      pos.addScaledVector(dir, ds); if (pos.y < floorY + 0.004) pos.y = floorY + 0.004;
    }
    p.needsUpdate = true; uv.needsUpdate = true; this.geo.computeVertexNormals(); this.geo.computeBoundingSphere();
  }
  /** world point at s metres along the strip from the slot */
  pointAt(s) { if (!this.pts || !this.pts.length) return V3(); const f = clamp(s / this.ds, 0, this.pts.length - 1); const i = Math.floor(f), k = f - i; const a = this.pts[i], b = this.pts[Math.min(this.pts.length - 1, i + 1)]; return a.clone().lerp(b, k); }
}
export function rubberStamp() {
  const g = new THREE.Group(); const wood = clay(0x9b6a3c, { rimAmt: 0.25 }), rubber = clay(0xd2541c);
  const handle = new THREE.Mesh(lathe([[0, 0.05], [0.03, 0.05], [0.022, 0.08], [0.02, 0.12], [0.035, 0.15], [0.03, 0.17], [0, 0.175]], 20), wood); g.add(handle);
  const block = new THREE.Mesh(rbox(0.12, 0.04, 0.06, 0.008), wood); block.position.y = 0.03; g.add(block);
  const pad = new THREE.Mesh(rbox(0.115, 0.012, 0.055, 0.004), rubber); pad.position.y = 0.004; g.add(pad);
  return g;
}

// ---------------------------------------------------------------- two thousand years of human progress
export function stoneTablet() {
  const g = new THREE.Group(); const tex = canvasTex(400, 560, (c, w, h) => { const R = rng(9); c.fillStyle = '#8f8a80'; c.fillRect(0, 0, w, h); for (let i = 0; i < 900; i++) { c.fillStyle = `rgba(${100 + R() * 60 | 0},${95 + R() * 55 | 0},${85 + R() * 50 | 0},0.35)`; c.fillRect(R() * w, R() * h, 3 + R() * 8, 2 + R() * 6); }
    c.strokeStyle = '#4f4b44'; c.lineWidth = 7; for (let row = 0; row < 7; row++) for (let i = 0; i < 6; i++) { const x = 50 + i * 55, y = 80 + row * 62; c.beginPath(); c.moveTo(x, y); c.lineTo(x + 18 + R() * 16, y + (R() - 0.5) * 20); c.lineTo(x + 6, y + 26); c.stroke(); } });
  const m = new THREE.Mesh(rbox(0.36, 0.5, 0.08, 0.04), new THREE.MeshLambertMaterial({ map: tex })); m.position.y = 0.25; g.add(m); return g;
}
export function telegraphKey() {
  const g = new THREE.Group(); const wood = clay(0x6b4426, { rimAmt: 0.2 }), brass = gloss(0xc9a24a, { shininess: 90, specular: 0xfff0b0 }), black = gloss(0x15161a);
  const base = new THREE.Mesh(rbox(0.34, 0.04, 0.2, 0.01), wood); base.position.y = 0.02; g.add(base);
  const lever = new THREE.Mesh(rbox(0.26, 0.016, 0.03, 0.005), brass); lever.position.set(0, 0.075, 0); g.add(lever); g.userData.lever = lever;
  const knob = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.03, 0.018, 20), black); knob.position.set(0.11, 0.095, 0); g.add(knob);
  const post = new THREE.Mesh(new THREE.CylinderGeometry(0.012, 0.012, 0.05, 10), brass); post.position.set(-0.06, 0.06, 0); g.add(post);
  for (const x of [-0.13, 0.04]) { const s = new THREE.Mesh(new THREE.CylinderGeometry(0.01, 0.01, 0.03, 10), brass); s.position.set(x, 0.055, 0.06); g.add(s); }
  return g;
}
export function rotaryPhone() {
  const g = new THREE.Group(); const red = gloss(0xb32630, { shininess: 80, rimAmt: 0.3 }), cream = clay(0xf1ead8);
  const body = new THREE.Mesh(lathe([[0, 0], [0.13, 0], [0.135, 0.02], [0.11, 0.1], [0.07, 0.13], [0, 0.135]], 28), red); body.scale.z = 0.85; g.add(body);
  const dial = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.06, 0.012, 28), cream); dial.position.set(0, 0.1, 0.075); dial.rotation.x = 1.1; g.add(dial);
  const dt = canvasTex(256, 256, (c, w, h) => { c.fillStyle = '#f1ead8'; c.fillRect(0, 0, w, h); c.fillStyle = '#20232a'; for (let i = 0; i < 10; i++) { const a = -Math.PI * 0.35 + i * 0.5; c.beginPath(); c.arc(w / 2 + Math.cos(a) * 84, h / 2 + Math.sin(a) * 84, 20, 0, 7); c.fill(); } });
  const face = new THREE.Mesh(new THREE.CircleGeometry(0.058, 28), new THREE.MeshLambertMaterial({ map: dt })); face.position.set(0, 0.1 + Math.cos(1.1) * 0.0062, 0.075 + Math.sin(1.1) * 0.0062); face.rotation.x = -Math.PI / 2 + 1.1; g.add(face);
  const hs = makeHandsetMesh(red); hs.rotation.set(0, Math.PI / 2, Math.PI / 2); hs.position.set(0, 0.16, -0.01); g.add(hs);
  return g;
}
function makeHandsetMesh(mat) { const g = new THREE.Group(); const bar = new THREE.Mesh(new THREE.CapsuleGeometry(0.022, 0.16, 6, 12), mat); g.add(bar);
  for (const s of [-1, 1]) { const c = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.034, 0.045, 18), mat); c.position.set(0.02, s * 0.1, 0); c.rotation.z = Math.PI / 2; g.add(c); } return g; }
export function pedestal(label) {
  const g = new THREE.Group(); const p = new THREE.Mesh(rbox(0.6, 1.0, 0.6, 0.03), clay(0xf2f0eb, { rimAmt: 0.2 })); p.position.y = 0.5; g.add(p);
  if (label) { const pl = new THREE.Mesh(new THREE.PlaneGeometry(0.34, 0.09), new THREE.MeshLambertMaterial({ map: canvasTex(400, 106, (c, w, h) => { c.fillStyle = '#c9a24a'; c.fillRect(0, 0, w, h); c.fillStyle = '#2b220f'; c.font = `56px ${FONT.black}`; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText(label, w / 2, h / 2 + 3); }) }));
    pl.position.set(0, 0.86, 0.302); g.add(pl); }
  return g;
}

// ---------------------------------------------------------------- cobwebs, a pigeon, sax notes
/** a web spanning anchor points (world): radial threads from a centre, a spiral, sagging a little; k 0..1 grows it */
export function cobweb(center, anchors, { rings = 7, sag = 0.02 } = {}) {
  const pos = []; const n = anchors.length;
  for (const a of anchors) pos.push(center.x, center.y, center.z, a.x, a.y, a.z);
  for (let r = 1; r <= rings; r++) { const f = r / (rings + 0.5);
    for (let i = 0; i < n; i++) { const a = center.clone().lerp(anchors[i], f), b = center.clone().lerp(anchors[(i + 1) % n], f); a.y -= sag * f; b.y -= sag * f; pos.push(a.x, a.y, a.z, b.x, b.y, b.z); } }
  const geo = new THREE.BufferGeometry(); geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  const m = new THREE.LineSegments(geo, new THREE.LineBasicMaterial({ color: 0xe8eef5, transparent: true, opacity: 0.55, depthWrite: false })); return m;
}
export function pigeon() {
  const g = new THREE.Group(); const grey = clay(0x8e96a3, { rimAmt: 0.3 }), dark = clay(0x5a6170), neck = gloss(0x4f7a6a, { shininess: 80, specular: 0x9a6aff }), leg = clay(0xd06a6a);
  const body = new THREE.Mesh(new THREE.SphereGeometry(0.075, 18, 12), grey); body.scale.set(0.8, 0.75, 1.25); body.position.y = 0.09; g.add(body);
  for (const s of [-1, 1]) { const w = new THREE.Mesh(new THREE.SphereGeometry(0.06, 14, 10), dark); w.scale.set(0.3, 0.6, 1.3); w.position.set(0.05 * s, 0.1, -0.02); g.add(w);
    const l = new THREE.Mesh(new THREE.CylinderGeometry(0.005, 0.005, 0.05, 6), leg); l.position.set(0.02 * s, 0.025, 0.01); g.add(l); }
  const tail = new THREE.Mesh(rbox(0.06, 0.012, 0.08, 0.005), dark); tail.position.set(0, 0.08, -0.11); tail.rotation.x = 0.3; g.add(tail);
  const headG = new THREE.Group(); headG.position.set(0, 0.15, 0.06); g.add(headG);
  const nk = new THREE.Mesh(new THREE.SphereGeometry(0.04, 14, 10), neck); nk.position.set(0, -0.02, -0.01); headG.add(nk);
  const head = new THREE.Mesh(new THREE.SphereGeometry(0.032, 14, 10), grey); head.position.set(0, 0.025, 0.012); headG.add(head);
  const beak = new THREE.Mesh(new THREE.ConeGeometry(0.008, 0.025, 8), clay(0x3a3a3a)); beak.rotation.x = Math.PI / 2; beak.position.set(0, 0.02, 0.05); headG.add(beak);
  for (const s of [-1, 1]) { const e = new THREE.Mesh(new THREE.SphereGeometry(0.007, 8, 6), glowMat(new THREE.Color(1.4, 0.5, 0.1))); e.position.set(0.024 * s, 0.032, 0.03); headG.add(e); }
  g.userData.head = headG; return g;
}
let _noteTex = null;
export function noteTexture() {
  if (_noteTex) return _noteTex;
  _noteTex = [0, 1].map((kind) => canvasTex(128, 128, (c, w, h) => { c.fillStyle = '#ffd36a'; c.strokeStyle = '#ffd36a'; c.shadowColor = '#ffb020'; c.shadowBlur = 14; c.lineWidth = 9; c.lineCap = 'round';
    if (kind === 0) { c.beginPath(); c.ellipse(46, 94, 22, 16, -0.4, 0, 7); c.fill(); c.beginPath(); c.moveTo(66, 90); c.lineTo(66, 22); c.stroke(); c.beginPath(); c.moveTo(66, 22); c.quadraticCurveTo(96, 40, 92, 66); c.stroke(); }
    else { for (const x of [34, 88]) { c.beginPath(); c.ellipse(x, 98, 19, 14, -0.4, 0, 7); c.fill(); } c.beginPath(); c.moveTo(51, 94); c.lineTo(51, 24); c.lineTo(105, 16); c.lineTo(105, 88); c.stroke(); c.lineWidth = 12; c.beginPath(); c.moveTo(51, 30); c.lineTo(105, 22); c.stroke(); } }));
  return _noteTex;
}
export class SaxNotes {
  constructor(n = 14) { this.root = new THREE.Group(); this.notes = []; const tx = noteTexture();
    for (let i = 0; i < n; i++) { const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: tx[i % 2], transparent: true, depthWrite: false, toneMapped: false, color: new THREE.Color(1.6, 1.5, 1.2) })); s.scale.setScalar(0.12); this.root.add(s); this.notes.push(s); } }
  /** fn(i, s) -> { p: Vector3, scale, op } or null to hide */
  set(fn) { this.notes.forEach((s, i) => { const r = fn(i, s); if (!r) { s.visible = false; return; } s.visible = true; s.position.copy(r.p); s.scale.setScalar(r.scale ?? 0.12); s.material.opacity = r.op ?? 1; s.material.rotation = r.rot ?? 0; }); }
}

// ---------------------------------------------------------------- invented tabloids
export function tabloid(mast, lines, col = '#e02a2a', seed = 1) {
  return canvasTex(620, 860, (c, w, h) => { const R = rng(seed); c.fillStyle = '#f6f2e8'; c.fillRect(0, 0, w, h);
    c.fillStyle = col; c.fillRect(0, 0, w, 130); c.fillStyle = '#ffffff'; c.font = `92px ${FONT.anton}`; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText(mast, w / 2, 70);
    const ph = c.createLinearGradient(0, 150, 0, 520); ph.addColorStop(0, '#2b3646'); ph.addColorStop(1, '#5a6b80'); c.fillStyle = ph; c.fillRect(30, 150, w - 60, 360);
    c.fillStyle = '#e9edf2'; c.beginPath(); c.ellipse(w / 2, 300, 70, 82, 0, 0, 7); c.fill(); c.fillStyle = '#0b0c10'; c.beginPath(); c.ellipse(w / 2, 300, 60, 70, 0, -2.5, -0.6); c.fill(); c.fillStyle = '#5ff4ff'; c.fillRect(w / 2 - 44, 288, 88, 12);
    c.fillStyle = '#e9edf2'; c.beginPath(); c.ellipse(w / 2, 470, 130, 70, 0, Math.PI, 0); c.fill();
    c.fillStyle = '#111317'; c.textAlign = 'center'; let y = 600; for (const l of lines) { let size = 88; c.font = `${size}px ${FONT.anton}`; while (c.measureText(l).width > w - 50 && size > 40) { size -= 4; c.font = `${size}px ${FONT.anton}`; } c.fillText(l, w / 2, y); y += size * 1.02; }
    c.fillStyle = '#ffd400'; c.save(); c.translate(w - 110, 210); c.rotate(0.25); c.beginPath(); for (let k = 0; k < 16; k++) { const a = k * Math.PI / 8, r = k % 2 ? 62 : 82; c.lineTo(Math.cos(a) * r, Math.sin(a) * r); } c.fill();
    c.fillStyle = '#c4161c'; c.font = `30px ${FONT.black}`; c.fillText('EXCL.', 0, 4); c.restore(); });
}

// ---------------------------------------------------------------- the salon: under the hood dryer with onion rings and bubbly
export function salon() {
  const g = new THREE.Group(); const chrome = gloss(0xdfe3e8, { shininess: 140, specular: 0xffffff, rimAmt: 0.3 }), cream = gloss(0xf3eee6, { shininess: 70, rimAmt: 0.3 }), vinyl = gloss(0x1d1d22, { shininess: 60, rimAmt: 0.3 });
  const floor = new THREE.Mesh(new THREE.CircleGeometry(6, 40), new THREE.MeshLambertMaterial({ map: canvasTex(512, 512, (c, w, h) => { for (let y = 0; y < 8; y++) for (let x = 0; x < 8; x++) { c.fillStyle = (x + y) % 2 ? '#f1ece4' : '#2b2a2e'; c.fillRect(x * 64, y * 64, 64, 64); } }, { repeat: [3, 3] }) }));
  floor.rotation.x = -Math.PI / 2; floor.position.y = 0.003; g.add(floor);
  // the chair
  const seat = new THREE.Mesh(rbox(0.56, 0.12, 0.52, 0.05), vinyl); seat.position.set(0, 0.46, 0); g.add(seat);
  const back = new THREE.Mesh(rbox(0.56, 0.62, 0.1, 0.05), vinyl); back.position.set(0, 0.8, -0.24); back.rotation.x = -0.12; g.add(back);
  for (const s of [-1, 1]) { const arm = new THREE.Mesh(rbox(0.08, 0.06, 0.48, 0.03), vinyl); arm.position.set(0.3 * s, 0.68, 0.0); g.add(arm);
    const post = new THREE.Mesh(new THREE.CylinderGeometry(0.015, 0.015, 0.2, 8), chrome); post.position.set(0.3 * s, 0.57, 0.12); g.add(post); }
  const base = new THREE.Mesh(new THREE.CylinderGeometry(0.28, 0.3, 0.05, 28), chrome); base.position.y = 0.03; g.add(base);
  const col = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.05, 0.38, 14), chrome); col.position.y = 0.23; g.add(col);
  // the hood dryer: a dome on a stand, angled over the head
  const stand = new THREE.Mesh(new THREE.CylinderGeometry(0.025, 0.025, 1.55, 10), chrome); stand.position.set(0, 0.77, -0.5); g.add(stand);
  const foot = new THREE.Mesh(new THREE.CylinderGeometry(0.22, 0.24, 0.04, 24), chrome); foot.position.set(0, 0.02, -0.5); g.add(foot);
  const hood = new THREE.Group(); hood.position.set(0, 1.56, -0.13); hood.rotation.x = 0.34; g.add(hood);
  const dome = new THREE.Mesh(new THREE.SphereGeometry(0.3, 32, 18, 0, Math.PI * 2, 0, Math.PI * 0.55), cream); dome.scale.set(1, 0.85, 1.05); hood.add(dome);
  const rim = new THREE.Mesh(new THREE.TorusGeometry(0.31, 0.022, 10, 40), chrome); rim.rotation.x = Math.PI / 2; rim.position.y = -0.045; hood.add(rim);
  const inner = new THREE.Mesh(new THREE.SphereGeometry(0.285, 28, 14, 0, Math.PI * 2, 0, Math.PI * 0.5), glowMat(new THREE.Color(1.3, 0.75, 0.42), { side: THREE.BackSide })); inner.scale.set(1, 0.82, 1.03); hood.add(inner);
  const knob = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.04, 0.03, 16), chrome); knob.position.set(0, 0.25, 0.0); hood.add(knob);
  const arm = new THREE.Mesh(new THREE.CylinderGeometry(0.02, 0.02, 0.42, 8), chrome); arm.position.set(0, 1.5, -0.36); arm.rotation.x = 1.1; g.add(arm);
  // side table, a mirror with bulbs
  const table = new THREE.Mesh(new THREE.CylinderGeometry(0.2, 0.2, 0.03, 24), cream); table.position.set(0.62, 0.62, 0.05); g.add(table);
  const tleg = new THREE.Mesh(new THREE.CylinderGeometry(0.02, 0.02, 0.6, 8), chrome); tleg.position.set(0.62, 0.31, 0.05); g.add(tleg);
  // the mirror: a chrome frame and glass with a cool gradient and two diagonal sheens
  const mirTex = canvasTex(256, 336, (c, w, h) => { const gr = c.createLinearGradient(0, 0, w * 0.4, h); gr.addColorStop(0, '#eef4f8'); gr.addColorStop(0.55, '#c5d3de'); gr.addColorStop(1, '#a9bccb'); c.fillStyle = gr; c.fillRect(0, 0, w, h);
    c.save(); c.translate(w / 2, h / 2); c.rotate(-0.55); c.fillStyle = 'rgba(255,255,255,0.42)'; c.fillRect(-w, -h * 0.18, w * 2, h * 0.09); c.fillStyle = 'rgba(255,255,255,0.22)'; c.fillRect(-w, -h * 0.02, w * 2, h * 0.035); c.restore(); });
  const mframe = new THREE.Mesh(rbox(1.06, 1.36, 0.035, 0.03), chrome); mframe.position.set(-1.1, 1.35, -0.92); mframe.rotation.y = 0.5; g.add(mframe);
  const mirror = new THREE.Mesh(new THREE.PlaneGeometry(1.0, 1.3), new THREE.MeshLambertMaterial({ map: mirTex, emissive: 0x6d7a86, emissiveIntensity: 0.25 })); mirror.position.set(-1.1, 1.35, -0.9); mirror.rotation.y = 0.5; mirror.translateZ(0.02); g.add(mirror);
  for (let i = 0; i < 9; i++) { const a = i / 8 * Math.PI; const b = new THREE.Mesh(new THREE.SphereGeometry(0.035, 10, 8), glowMat(new THREE.Color(1.6, 1.4, 1.1))); const mp = V3(Math.cos(a) * 0.55, 0.65 + Math.sin(a) * 0.15, 0.03); mp.applyAxisAngle(V3(0, 1, 0), 0.5); b.position.copy(mirror.position).add(mp); g.add(b); }
  const sign = textPlane('SALON', { h: 0.28, font: FONT.serifI, size: 160, fg: '#ffffff', lit: false }); sign.position.set(1.3, 2.1, -1.2); sign.rotation.y = -0.45; g.add(sign);
  const plant = new THREE.Mesh(new THREE.SphereGeometry(0.28, 16, 12), clay(0x6fae6a)); plant.position.set(1.4, 0.75, -0.8); g.add(plant);
  const pot = new THREE.Mesh(new THREE.CylinderGeometry(0.18, 0.14, 0.5, 16), clay(0xf1ece4)); pot.position.set(1.4, 0.25, -0.8); g.add(pot);
  g.userData = { hood, inner, table };
  return g;
}
export function onionBag() {         // a yellow snack bag of onion rings, no brand
  const g = new THREE.Group(); const tex = canvasTex(400, 520, (c, w, h) => { const gr = c.createLinearGradient(0, 0, 0, h); gr.addColorStop(0, '#ffe14d'); gr.addColorStop(1, '#f6c21c'); c.fillStyle = gr; c.fillRect(0, 0, w, h);
    c.fillStyle = '#2f7d32'; c.save(); c.translate(w / 2, 120); c.rotate(-0.06); c.font = `92px ${FONT.anton}`; c.textAlign = 'center'; c.fillText('ONION', 0, 0); c.fillText('RINGS', 0, 92); c.restore();
    for (let i = 0; i < 5; i++) { const x = 90 + (i % 3) * 110, y = 330 + Math.floor(i / 3) * 90; c.strokeStyle = '#e6a33a'; c.lineWidth = 26; c.beginPath(); c.ellipse(x, y, 52, 40, 0.3, 0, 7); c.stroke(); c.strokeStyle = '#f5cf7a'; c.lineWidth = 10; c.stroke(); }
    c.fillStyle = '#c0392b'; c.beginPath(); c.arc(w - 70, 260, 46, 0, 7); c.fill(); c.fillStyle = '#fff'; c.font = `30px ${FONT.black}`; c.textAlign = 'center'; c.fillText('CRUNCH', w - 70, 270); });
  const geo = new THREE.BoxGeometry(0.16, 0.22, 0.05, 8, 10, 2); const p = geo.attributes.position;          // a pillow: pinched at the top and bottom seams
  for (let i = 0; i < p.count; i++) { const x = p.getX(i), y = p.getY(i), z = p.getZ(i); const k = 1 - Math.pow(Math.abs(y) / 0.11, 6); const bx = 1 - 0.25 * Math.pow(Math.abs(x) / 0.08, 4); p.setZ(i, z * Math.max(0.05, k) * bx); }
  geo.computeVertexNormals();
  const m = new THREE.Mesh(geo, [clay(0xf3c21f), clay(0xf3c21f), clay(0xf3c21f), clay(0xf3c21f), new THREE.MeshLambertMaterial({ map: tex, emissive: 0x222200 }), clay(0xf3c21f)]); g.add(m);
  for (const s of [-1, 1]) { const seam = new THREE.Mesh(new THREE.BoxGeometry(0.162, 0.012, 0.006), clay(0xe0a80f)); seam.position.y = 0.106 * s; g.add(seam); }
  return g;
}
export function onionRing() { const m = new THREE.Mesh(new THREE.TorusGeometry(0.016, 0.006, 8, 18), clay(0xe9b25a, { rimAmt: 0.3 })); return m; }
export function flute() {
  const g = new THREE.Group(); const glass = new THREE.MeshPhongMaterial({ color: 0xe8f2f8, transparent: true, opacity: 0.4, shininess: 140, specular: 0xffffff, depthWrite: false, side: THREE.DoubleSide });
  g.add(new THREE.Mesh(lathe([[0, 0], [0.035, 0], [0.036, 0.004], [0.004, 0.012], [0.003, 0.1], [0.022, 0.13], [0.026, 0.22], [0.024, 0.221], [0.0, 0.11]], 22), glass));
  const wine = new THREE.Mesh(lathe([[0, 0.112], [0.02, 0.135], [0.023, 0.19], [0, 0.19]], 18), clay(0xf2d98a, { transparent: true, opacity: 0.85, rimAmt: 0.5 })); g.add(wine); g.userData.wine = wine;
  return g;
}
