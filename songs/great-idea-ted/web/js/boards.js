// Great Idea, Ted v3: the joke and text frames, built into the city (not pasted on top).
// Design system: warm paper panels (#F4EFE6) with indigo ink (#1E2240); coral = Ted, mint = you; peach/indigo from the
// blue-hour sky. Type: Inter Display (headlines), Inter SemiBold (UI), JetBrains Mono (numbers, timestamps).
// Screen-like things (billboards, panels) are lit; sky titles are neon with bloom.
import * as THREE from 'three';
import { FONT, canvasTex, clay, basic } from './lib.js';
import { dayTint } from './city.js';

export const C = { paper: '#F4EFE6', paper2: '#E9E2D6', ink: '#1E2240', mute: '#6B6F86', line: '#D9D1C3', coral: '#FF6B5B', coralDeep: '#D9473A',
  mint: '#7FE0C2', mintDeep: '#2E9C7C', peach: '#F2A88C', indigo: '#1F2547', gold: '#FFD27A', red: '#E5484D', pink: '#FF4FB0', cyan: '#45F0FF' };

// a canvas-drawn panel as a mesh, sized in world units by height. lit: glows like a screen (bloom); else soft paper
export function panel(wPx, hPx, draw, worldH, { lit = false, glow = 1, transparent = true } = {}) {
  const tex = canvasTex(wPx, hPx, draw);
  const mat = new THREE.MeshBasicMaterial({ map: tex, transparent, depthWrite: !transparent, toneMapped: !lit });
  mat.color.setScalar(lit ? glow : 0.86);
  const m = new THREE.Mesh(new THREE.PlaneGeometry(worldH * wPx / hPx, worldH), mat); m.userData.tex = tex; return m;
}
export function rr(g, x, y, w, h, r) { g.beginPath(); g.roundRect(x, y, w, h, r); }
export function text(g, s, x, y, font, size, color, align = 'left', base = 'alphabetic', track = 0) {
  g.font = `${size}px ${font}`; g.fillStyle = color; g.textAlign = align; g.textBaseline = base;
  if (track) { g.letterSpacing = `${track}px`; } g.fillText(s, x, y); g.letterSpacing = '0px';
}
function shadowCard(g, x, y, w, h, r, fill) { g.save(); g.shadowColor = 'rgba(15,18,40,0.35)'; g.shadowBlur = 40; g.shadowOffsetY = 14; g.fillStyle = fill; rr(g, x, y, w, h, r); g.fill(); g.restore(); }

// ---------------------------------------------------------------- neon sky titles (bloom does the glow)
export function skyTitle(lines, worldH) {   // lines: [[text, color, sizeScale]]
  const W = 2400, lh = 300, H = lh * lines.reduce((a, l) => a + (l[2] || 1), 0) + 120; let inkW = 0;
  const m = panel(W, H, (g) => { let y = 60;
    for (const [t, col, k = 1, fill = '#ffffff'] of lines) { const sz = 250 * k; y += lh * k;
      g.save(); g.font = `${sz}px ${FONT.dispBlack}`; g.textAlign = 'center'; g.letterSpacing = '-4px'; inkW = Math.max(inkW, g.measureText(t).width);
      g.shadowColor = col; g.shadowBlur = 34; g.fillStyle = col; g.fillText(t, W / 2, y - 40); g.shadowBlur = 10; g.fillText(t, W / 2, y - 40);
      g.shadowBlur = 0; g.fillStyle = fill; g.fillText(t, W / 2, y - 40); g.restore(); } }, worldH, { lit: true, glow: 0.86 });
  m.userData.ink = { w: Math.min(1, (inkW + 80) / W), h: (H - 120) / H };   // where the letters actually are (the panel has room for the glow)
  return m;
}

// ---------------------------------------------------------------- a billboard on its own tower
export function billboardTower(x, z, rotY, { bw = 9.6, bh = 5.4, y = 36, h = 44 } = {}) {
  const g = new THREE.Group(); g.position.set(x, 0, z); g.rotation.y = rotY;
  const tower = new THREE.Mesh(new THREE.BoxGeometry(bw + 2.2, h, 7), dayTint(new THREE.MeshBasicMaterial({ color: 0x14172c }))); tower.position.y = h / 2; g.add(tower);
  const win = canvasTex(256, 512, (c, w, hh) => { c.fillStyle = '#14172c'; c.fillRect(0, 0, w, hh);
    for (let yy = 8; yy < hh; yy += 16) for (let xx = 8; xx < w; xx += 14) { const r = Math.sin(xx * 12.9 + yy * 78.2) * 43758.5 % 1; c.fillStyle = Math.abs(r) < 0.28 ? '#ffe3b8' : '#232849'; c.fillRect(xx, yy, 8, 9); } }, { repeat: [3, 8] });
  for (const s of [-1, 1]) { const side = new THREE.Mesh(new THREE.PlaneGeometry(7, h), dayTint(new THREE.MeshBasicMaterial({ map: win, color: 0xb8b8b8 }))); side.position.set(s * (bw / 2 + 1.101), h / 2, 0); side.rotation.y = s * Math.PI / 2; g.add(side); }
  const front = new THREE.Mesh(new THREE.PlaneGeometry(bw + 2.2, h), dayTint(new THREE.MeshBasicMaterial({ map: win, color: 0xb8b8b8 }))); front.position.set(0, h / 2, 3.501); g.add(front);
  const frame = new THREE.Mesh(new THREE.BoxGeometry(bw + 0.5, bh + 0.5, 0.35), clay(0x0c0d14)); frame.position.set(0, y, 3.7); g.add(frame);
  const board = new THREE.Mesh(new THREE.PlaneGeometry(bw, bh), new THREE.MeshBasicMaterial({ color: 0x0a0b12 })); board.position.set(0, y, 3.88); g.add(board);
  for (const s of [-1, 1]) { const lamp = new THREE.Mesh(new THREE.BoxGeometry(0.25, 0.12, 0.6), clay(0x22242c)); lamp.position.set(s * bw * 0.3, y + bh / 2 + 0.4, 4.1); g.add(lamp); }
  g.userData.set = (tex) => { board.material.map = tex; board.material.color.setScalar(tex ? 0.88 : 1); board.material.needsUpdate = true; };
  g.userData.boardWorld = () => board.getWorldPosition(new THREE.Vector3());
  return g;
}

// ---------------------------------------------------------------- the boards' contents (LED screen designs, 1920x1080)
export function raiseLetter(amount, { budget = null, note = 'effective immediately' } = {}) {
  return canvasTex(1920, 1080, (g, w, h) => {
    g.fillStyle = C.indigo; g.fillRect(0, 0, w, h);
    const gr = g.createRadialGradient(w * 0.5, h * 0.4, 50, w * 0.5, h * 0.4, w * 0.7); gr.addColorStop(0, 'rgba(242,168,140,0.35)'); gr.addColorStop(1, 'rgba(242,168,140,0)'); g.fillStyle = gr; g.fillRect(0, 0, w, h);
    shadowCard(g, 160, 120, w - 320, h - 240, 44, C.paper);
    text(g, 'COMPENSATION UPDATE', 260, 250, FONT.ui, 58, C.mute, 'left', 'alphabetic', 8);
    g.fillStyle = C.coral; g.beginPath(); g.arc(300, 370, 62, 0, 7); g.fill(); text(g, 'T', 300, 395, FONT.dispBlack, 76, '#fff', 'center');
    text(g, 'Ted', 400, 365, FONT.disp, 90, C.ink); text(g, note, 400, 430, FONT.ui, 54, C.mute);
    text(g, 'New base salary', 260, 570, FONT.ui, 62, C.mute);
    let sz = 220; g.font = `${sz}px ${FONT.monoB}`; while (g.measureText(amount).width > w - 560) { sz -= 6; g.font = `${sz}px ${FONT.monoB}`; }
    text(g, amount, 250, 560 + sz * 0.95, FONT.monoB, sz, C.ink);
    if (budget) { g.fillStyle = 'rgba(229,72,77,0.12)'; rr(g, 260, h - 250, 760, 84, 42); g.fill(); text(g, budget, 300, h - 192, FONT.ui, 44, C.red); }
  });
}
export function leadershipPage(heads) {   // heads: [[name, canvas, isNew]]
  return canvasTex(1920, 1080, (g, w, h) => {
    g.fillStyle = C.paper; g.fillRect(0, 0, w, h);
    text(g, 'brightloop.', 120, 130, FONT.disp, 60, C.ink); ['Product', 'About', 'Leadership'].forEach((t, i) => text(g, t, 1260 + i * 200, 130, FONT.ui, 40, i === 2 ? C.ink : C.mute));
    g.fillStyle = C.ink; g.fillRect(1660, 150, 186, 5);
    text(g, 'Our leadership', 120, 330, FONT.disp, 130, C.ink);
    const n = heads.length, cw = (w - 240) / n;
    heads.forEach(([name, cv, isNew], i) => { const cx = 120 + cw * (i + 0.5), cy = 640, r = 170;
      g.save(); g.beginPath(); g.arc(cx, cy, r, 0, 7); g.closePath(); g.fillStyle = C.paper2; g.fill(); g.clip(); if (cv) g.drawImage(cv, cx - r, cy - r, r * 2, r * 2); g.restore();
      if (isNew) { g.strokeStyle = C.gold; g.lineWidth = 14; g.beginPath(); g.arc(cx, cy, r + 10, 0, 7); g.stroke(); }
      text(g, name, cx - (isNew ? 70 : 0), 900, FONT.disp, 60, C.ink, 'center');
      if (isNew) { text(g, '· new!', cx + 40, 900, FONT.disp, 60, C.coralDeep, 'left'); } });
  });
}
export function equityGrant(shares = '250,000') {
  // a certificate on a strict grid: 2 x 2 fields, a rule, then signature (left) and stamp (right) in their own cells.
  // Nothing crosses the gold border or another element.
  return canvasTex(1920, 1080, (g, w, h) => {
    g.fillStyle = C.indigo; g.fillRect(0, 0, w, h);
    shadowCard(g, 200, 100, w - 400, h - 200, 30, '#FBF7EF');
    g.strokeStyle = '#C9A44C'; g.lineWidth = 6; rr(g, 236, 136, w - 472, h - 272, 18); g.stroke(); g.lineWidth = 2; rr(g, 258, 158, w - 516, h - 316, 12); g.stroke();
    const L = 380, R = 1060;                       // the two column edges
    text(g, 'EQUITY GRANT', w / 2, 262, FONT.ui, 52, '#8A6A1E', 'center', 'alphabetic', 14);
    text(g, 'Recipient', L, 360, FONT.ui, 40, C.mute); text(g, 'Ted', L, 440, FONT.disp, 84, C.ink);
    text(g, 'Shares', R, 360, FONT.ui, 40, C.mute); text(g, shares, R, 442, FONT.monoB, 92, C.ink);
    text(g, 'Vesting', L, 530, FONT.ui, 40, C.mute); text(g, 'immediately', L, 600, FONT.disp, 64, C.ink);
    text(g, 'Reason', R, 530, FONT.ui, 40, C.mute); text(g, 'great idea', R, 600, FONT.disp, 64, C.coralDeep);
    g.strokeStyle = 'rgba(201,164,76,0.55)'; g.lineWidth = 2; g.beginPath(); g.moveTo(L, 662); g.lineTo(w - L, 662); g.stroke();
    // signature cell (left): name above the line, label below it
    text(g, 'Ted', L + 30, 790, FONT.serif, 92, C.ink);
    g.strokeStyle = C.ink; g.lineWidth = 3; g.beginPath(); g.moveTo(L, 812); g.lineTo(L + 520, 812); g.stroke();
    text(g, 'Authorized by', L, 858, FONT.ui, 36, C.mute);
    // stamp cell (right): centred in its own box, clear of the rule, the border and the text
    g.save(); g.translate(R + 260, 760); g.rotate(-0.08); g.globalAlpha = 0.92;
    g.strokeStyle = C.coral; g.lineWidth = 8; rr(g, -190, -62, 380, 124, 16); g.stroke(); g.lineWidth = 3; rr(g, -174, -46, 348, 92, 10); g.stroke();
    text(g, 'APPROVED', 0, 2, FONT.disp, 62, C.coral, 'center', 'middle', 6); g.restore();
  });
}

// the raise that won't fit: a paper card wider than the billboard, the number running off its edge as torn-off chips.
// Final video: the number counts up and the card stretches until digits break free; this draws one moment of that.
export function raiseOverflow(amount, { spill = 3 } = {}) {
  const cardW = 2400, W = 3000, H = 1400, top = 480, ch = 840, sz = 220;   // 200 px per world unit; the space above the card is for the escaping digits
  return panel(W, H, (g) => {
    g.font = `${sz}px ${FONT.monoB}`; const cw = g.measureText('0').width;
    const kept = amount.slice(0, amount.length - spill), lost = amount.slice(amount.length - spill);
    // card, with a torn right edge where the digits pushed through
    g.save(); g.shadowColor = 'rgba(15,18,40,0.35)'; g.shadowBlur = 40; g.shadowOffsetY = 14; g.fillStyle = C.paper;
    g.beginPath(); g.moveTo(44, top); g.lineTo(cardW, top);
    for (let y = top, i = 0; y < top + ch; y += 42, i++) g.lineTo(cardW - (i % 2 ? 26 : 0) - (y > 460 && y < 760 ? 40 : 0), y);
    g.lineTo(cardW, top + ch); g.lineTo(44, top + ch); g.quadraticCurveTo(0, top + ch, 0, top + ch - 44); g.lineTo(0, top + 44); g.quadraticCurveTo(0, top, 44, top); g.fill(); g.restore();
    text(g, 'COMPENSATION UPDATE', 100, top + 130, FONT.ui, 58, C.mute, 'left', 'alphabetic', 8);
    g.fillStyle = C.coral; g.beginPath(); g.arc(140, top + 250, 62, 0, 7); g.fill(); text(g, 'T', 140, top + 275, FONT.dispBlack, 76, '#fff', 'center');
    text(g, 'Ted', 240, top + 245, FONT.disp, 90, C.ink); text(g, 'effective immediately', 240, top + 310, FONT.ui, 54, C.mute);
    text(g, 'New base salary', 100, top + 450, FONT.ui, 62, C.mute);
    const base = top + 450 + sz * 0.95; text(g, kept, 90, base, FONT.monoB, sz, C.ink);
    // the escaping digits: each on its own torn chip, tumbling further out and up
    let x = 90 + g.measureText(kept).width;
    [...lost].forEach((d, i) => { const k = i + 1, cx = x + cw * 0.55 + k * cw * 0.06, cy = base - sz * 0.33 - 70 - k * 200, rot = (i % 2 ? 1 : -1) * (0.1 + 0.09 * k);
      g.save(); g.translate(cx, cy); g.rotate(rot); g.save(); g.shadowColor = 'rgba(15,18,40,0.4)'; g.shadowBlur = 24; g.shadowOffsetY = 10; g.fillStyle = C.paper;
      g.beginPath(); g.moveTo(-cw * 0.62, -sz * 0.55); g.lineTo(cw * 0.6, -sz * 0.6); g.lineTo(cw * 0.66, sz * 0.5); g.lineTo(-cw * 0.58, sz * 0.56); g.closePath(); g.fill(); g.restore();
      text(g, d, 0, sz * 0.33, FONT.monoB, sz, C.ink, 'center'); g.restore(); x += cw; });
  }, 7.0);
}
export function raiseBackdrop() {   // the board behind the escaping card: just the lit indigo screen
  return canvasTex(1920, 1080, (g, w, h) => { g.fillStyle = C.indigo; g.fillRect(0, 0, w, h);
    const gr = g.createRadialGradient(w * 0.5, h * 0.4, 50, w * 0.5, h * 0.4, w * 0.7); gr.addColorStop(0, 'rgba(242,168,140,0.35)'); gr.addColorStop(1, 'rgba(242,168,140,0)'); g.fillStyle = gr; g.fillRect(0, 0, w, h); });
}

// ---------------------------------------------------------------- the tower clock (an LED sign behind the meeting)
export function clockSign() {
  const g = new THREE.Group(); const cv = document.createElement('canvas'); cv.width = 1200; cv.height = 400;
  const tex = new THREE.CanvasTexture(cv); tex.colorSpace = THREE.SRGBColorSpace;
  const face = new THREE.Mesh(new THREE.PlaneGeometry(6, 2), new THREE.MeshBasicMaterial({ map: tex, toneMapped: false })); face.position.z = 0.16; g.add(face);
  const box = new THREE.Mesh(new THREE.BoxGeometry(6.4, 2.4, 0.3), clay(0x0c0d14)); g.add(box);
  g.userData.set = (time, sub = '', col = C.gold) => { const c = cv.getContext('2d'); c.fillStyle = '#07080f'; c.fillRect(0, 0, 1200, 400);
    c.save(); c.font = `250px ${FONT.monoB}`; c.textAlign = 'center'; c.shadowColor = col; c.shadowBlur = 30; c.fillStyle = col; c.fillText(time, 600, sub ? 260 : 300); c.restore();
    if (sub) text(c, sub, 600, 360, FONT.ui, 56, '#cfd3e6', 'center', 'alphabetic', 10); tex.needsUpdate = true; };
  g.userData.set('10:00'); return g;
}

// ---------------------------------------------------------------- floating glass things near the rooms
export function bubble(str, { who = null, col = C.ink, w = 900, size = 64, tail = 'left' } = {}) {
  const tmp = document.createElement('canvas').getContext('2d'); tmp.font = `${size}px ${FONT.ui}`;
  const words = str.split(' '); const lines = []; let cur = '';
  for (const wd of words) { const t = cur ? cur + ' ' + wd : wd; if (tmp.measureText(t).width > w - 120 && cur) { lines.push(cur); cur = wd; } else cur = t; } lines.push(cur);
  const lw = Math.max(...lines.map((l) => tmp.measureText(l).width)) + 120, top = who ? 96 : 0, hh = top + lines.length * size * 1.25 + 90 + 50;
  return panel(Math.ceil(lw), Math.ceil(hh), (g, W, H) => {
    g.save(); g.shadowColor = 'rgba(10,12,30,0.4)'; g.shadowBlur = 24; g.shadowOffsetY = 8; g.fillStyle = '#FBF8F2'; rr(g, 6, 6, W - 12, H - 56, 40); g.fill();
    g.beginPath(); const tx = tail === 'left' ? 90 : W - 90; g.moveTo(tx - 30, H - 52); g.lineTo(tx + (tail === 'left' ? -20 : 20), H - 8); g.lineTo(tx + 30, H - 52); g.fill(); g.restore();
    if (who) text(g, who, 60, 90, FONT.disp, 50, col);
    lines.forEach((l, i) => text(g, l, 60, top + 60 + size + i * size * 1.25 - 10, FONT.ui, size, C.ink));
  }, hh / 1000 * 2.4);
}
export function notesPanel(cursorOn = true) {
  return panel(1200, 800, (g, w, h) => {
    shadowCard(g, 20, 20, w - 40, h - 40, 36, '#FBF8F2');
    text(g, 'MEETING NOTES', 90, 130, FONT.ui, 40, C.mute, 'left', 'alphabetic', 8);
    text(g, 'Q3 Launch Sync', 90, 230, FONT.disp, 76, C.ink);
    text(g, 'Untitled  ·  0 words', 90, 310, FONT.ui, 46, C.mute);
    g.strokeStyle = C.line; g.lineWidth = 3; g.beginPath(); g.moveTo(90, 360); g.lineTo(w - 90, 360); g.stroke();
    if (cursorOn) { g.fillStyle = C.ink; g.fillRect(92, 410, 6, 70); }
    for (let i = 0; i < 4; i++) { g.fillStyle = 'rgba(30,34,64,0.05)'; rr(g, 90, 520 + i * 52, [640, 520, 700, 380][i], 22, 11); g.fill(); }
  }, 2.0);
}
export function notesCard() {   // a narrow notes doc that fits the corner where four rooms meet
  return panel(760, 980, (g, w, h) => {
    shadowCard(g, 20, 20, w - 40, h - 40, 36, '#FBF8F2');
    text(g, 'MEETING NOTES', 80, 120, FONT.ui, 38, C.mute, 'left', 'alphabetic', 8);
    text(g, 'Q3 Launch Sync', 80, 210, FONT.disp, 70, C.ink);
    text(g, 'Untitled  ·  0 words', 80, 280, FONT.ui, 42, C.mute);
    g.strokeStyle = C.line; g.lineWidth = 3; g.beginPath(); g.moveTo(80, 330); g.lineTo(w - 80, 330); g.stroke();
    g.fillStyle = C.ink; g.fillRect(82, 380, 6, 66);
    for (let i = 0; i < 6; i++) { g.fillStyle = 'rgba(30,34,64,0.05)'; rr(g, 80, 520 + i * 62, [520, 420, 560, 300, 480, 360][i], 24, 12); g.fill(); }
  }, 1.55);
}
// a meeting reaction (the kind people send during a call), floating up the frame
export function reaction(ch, worldH = 0.9) {
  return panel(256, 256, (g, w, h) => { g.save(); g.shadowColor = 'rgba(10,12,30,0.35)'; g.shadowBlur = 16; g.shadowOffsetY = 6;
    g.font = '190px "Noto Color Emoji"'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(ch, w / 2, h / 2 + 10); g.restore(); }, worldH, { lit: true, glow: 0.92 });
}
export function confettiMat(col) { return new THREE.MeshBasicMaterial({ color: col, side: THREE.DoubleSide, toneMapped: false }); }

// Ted's profile card, with the chips people would put on it
export function profileCard(head, chips) {   // chips: [[label, 'good'|'bad']]
  return panel(1500, 760, (g, w, h) => {
    shadowCard(g, 20, 20, w - 40, h - 40, 40, '#FBF8F2');
    g.save(); g.beginPath(); g.arc(190, 230, 110, 0, 7); g.closePath(); g.fillStyle = C.paper2; g.fill(); g.clip(); if (head) g.drawImage(head, 80, 120, 220, 220); g.restore();
    g.strokeStyle = C.coral; g.lineWidth = 10; g.beginPath(); g.arc(190, 230, 116, 0, 7); g.stroke();
    text(g, 'Ted', 350, 215, FONT.disp, 110, C.ink); text(g, 'Senior Manager · Platform', 352, 290, FONT.ui, 46, C.mute);
    let x = 80; chips.forEach(([t, kind]) => { g.font = `68px ${FONT.ui}`; const tw = g.measureText(t).width + 90;
      g.fillStyle = kind === 'good' ? 'rgba(46,156,124,0.16)' : 'rgba(229,72,77,0.15)'; rr(g, x, 440, tw, 130, 65); g.fill();
      text(g, t, x + 45, 528, FONT.ui, 68, kind === 'good' ? C.mintDeep : C.red); x += tw + 30; });
  }, 1.9);
}
// a dictionary entry, for a billboard (1920x1080)
export function dictionaryEntry() {
  return canvasTex(1920, 1080, (g, w, h) => {
    g.fillStyle = C.indigo; g.fillRect(0, 0, w, h);
    shadowCard(g, 220, 130, w - 440, h - 260, 30, '#FBF8F2');
    g.save(); g.font = `italic 200px ${FONT.serif}`; g.fillStyle = C.ink; g.fillText('leadership', 320, 380); g.restore();
    text(g, "/ˈlēdərˌSHip/  ·  noun", 330, 460, FONT.mono, 52, C.mute);
    text(g, '1.  saying it slower.', 330, 610, FONT.ui, 92, C.ink);
    text(g, '2.  saying it louder.', 330, 730, FONT.ui, 92, C.ink);
    text(g, 'see also:', 330, 870, FONT.ui, 76, C.mute); text(g, 'Ted', 670, 870, FONT.disp, 76, C.coralDeep);
  });
}
// the same sentence, said twice: who, when, and a diff of nothing
export function wordForWord() {
  return panel(1500, 1060, (g, w, h) => {
    const msg = (y, who, col, t) => { shadowCard(g, 30, y, w - 60, 330, 36, '#FBF8F2'); text(g, who, 90, y + 90, FONT.disp, 54, col); text(g, t, w - 90, y + 90, FONT.mono, 44, C.mute, 'right');
      text(g, 'We should push the launch.', 90, y + 190, FONT.ui, 62, C.ink); text(g, "We're not ready and we know it.", 90, y + 270, FONT.ui, 62, C.ink); };
    msg(20, 'You', C.mintDeep, '10:00:04'); msg(400, 'Ted', C.coralDeep, '10:08:21');
    g.fillStyle = C.mint; rr(g, w / 2 - 380, 760, 760, 130, 65); g.fill(); text(g, 'diff:  0 changes', w / 2, 848, FONT.monoB, 62, C.indigo, 'center');
  }, 3.6);
}
// a small handwritten aside
export function aside(t, worldH = 0.7, col = '#FFF4DE') {
  return panel(900, 260, (g, w, h) => { g.save(); g.font = `italic 170px ${FONT.serif}`; g.textAlign = 'center'; g.shadowColor = col === '#FFF4DE' ? 'rgba(0,0,0,0.6)' : 'rgba(255,255,255,0.5)'; g.shadowBlur = 20; g.fillStyle = col; g.fillText(t, w / 2, 180); g.restore(); }, worldH, { lit: true, glow: 0.9 });
}
// a bubble whose text is said slower (stretched) or louder (huge caps)
export function styledBubble(str, { who, col, mode }) {
  const W = mode === 'loud' ? 2000 : 1700, H = mode === 'loud' ? 820 : 520;
  return panel(W, H, (g, w, h) => {
    g.save(); g.shadowColor = 'rgba(10,12,30,0.4)'; g.shadowBlur = 24; g.shadowOffsetY = 8; g.fillStyle = '#FBF8F2'; rr(g, 6, 6, w - 12, h - 56, 40); g.fill();
    g.beginPath(); g.moveTo(60, h - 52); g.lineTo(70, h - 8); g.lineTo(120, h - 52); g.fill(); g.restore();
    text(g, who, 60, 90, FONT.disp, 50, col);
    if (mode === 'slow') { text(g, 'W e   s h o u l d   p u s h', 60, 250, FONT.ui, 76, C.ink, 'left', 'alphabetic', 6); text(g, 't h e   l a u n c h . . .', 60, 370, FONT.ui, 76, C.ink, 'left', 'alphabetic', 6); }
    else { text(g, 'WE SHOULD', 60, 350, FONT.dispBlack, 230, C.ink); text(g, 'PUSH THE LAUNCH.', 60, 620, FONT.dispBlack, 196, C.ink); }
  }, mode === 'loud' ? 3.3 : 2.1);
}
// a reply that never comes: "How was your weekend?" and a waiting pill
export function waitingBubble() {
  return panel(1500, 640, (g, w, h) => {
    g.save(); g.shadowColor = 'rgba(10,12,30,0.4)'; g.shadowBlur = 24; g.shadowOffsetY = 8; g.fillStyle = '#FBF8F2'; rr(g, 6, 6, w - 12, 380, 40); g.fill(); g.restore();
    text(g, 'Ted', 60, 90, FONT.disp, 50, C.coralDeep); text(g, 'How was your weekend?', 60, 250, FONT.ui, 84, C.ink);
    g.fillStyle = 'rgba(16,18,40,0.86)'; rr(g, 60, 450, 860, 140, 70); g.fill();
    for (let i = 0; i < 3; i++) { g.fillStyle = `rgba(255,255,255,${0.45 + 0.25 * i})`; g.beginPath(); g.arc(150 + i * 60, 520, 18, 0, 7); g.fill(); }
    text(g, 'still waiting  ·  0:41', 360, 540, FONT.mono, 48, '#FFF4DE');
  }, 1.8);
}

// one digit on a torn paper chip (the raise, escaping)
export function digitChip(d) {
  return panel(220, 260, (g, w, h) => { g.save(); g.shadowColor = 'rgba(10,12,30,0.45)'; g.shadowBlur = 18; g.shadowOffsetY = 8; g.fillStyle = C.paper;
    g.beginPath(); g.moveTo(14, 18); g.lineTo(w - 10, 10); g.lineTo(w - 16, h - 14); g.lineTo(10, h - 20); g.closePath(); g.fill(); g.restore();
    text(g, d, w / 2, h / 2 + 62, FONT.monoB, 180, C.ink, 'center'); }, 0.75);
}
// the company website hero, for a billboard (1920x1080)
export function websiteHero(head) {
  return canvasTex(1920, 1080, (g, w, h) => {
    const gr = g.createLinearGradient(0, 0, w, h); gr.addColorStop(0, '#FDE8F1'); gr.addColorStop(1, '#F4EFE6'); g.fillStyle = gr; g.fillRect(0, 0, w, h);
    text(g, 'brightloop.', 110, 120, FONT.disp, 60, C.ink); ['Product', 'Customers', 'Leadership'].forEach((t, i) => text(g, t, 1180 + i * 230, 120, FONT.ui, 40, i === 2 ? C.ink : C.mute));
    text(g, 'Meet Ted.', 110, 470, FONT.dispBlack, 210, C.ink); text(g, 'Visionary.', 110, 690, FONT.dispBlack, 210, C.pink);
    text(g, '"We should push the launch."', 120, 820, FONT.ui, 56, C.mute);
    g.fillStyle = C.coral; rr(g, 120, 880, 360, 100, 50); g.fill(); text(g, 'Book a call', 300, 945, FONT.ui, 44, '#fff', 'center');
    g.save(); g.beginPath(); g.arc(1500, 600, 330, 0, 7); g.closePath(); g.fillStyle = C.paper2; g.fill(); g.clip(); if (head) g.drawImage(head, 1170, 270, 660, 660); g.restore();
    g.strokeStyle = C.pink; g.lineWidth = 16; g.beginPath(); g.arc(1500, 600, 340, 0, 7); g.stroke();
  });
}
// the talk sign: our own type, not anyone's logo
export function talkSign() {
  return panel(1600, 520, (g, w, h) => { g.fillStyle = '#0d0e14'; rr(g, 0, 0, w, h, 30); g.fill();
    g.save(); g.font = `250px ${FONT.dispBlack}`; g.textAlign = 'center'; g.shadowColor = C.red; g.shadowBlur = 40; g.fillStyle = '#ff3b3b'; g.fillText('Ted Talk', w / 2, 330); g.restore();
    text(g, 'IDEAS WORTH REPEATING', w / 2, 450, FONT.ui, 60, '#f4efe6', 'center', 'alphabetic', 16); }, 2.4, { lit: true, glow: 0.92 });
}

// the bridge: your official record, building up line by line
export function recordCard({ first = false, chips = [], status = null, loading = false } = {}) {
  return panel(1400, 1100, (g, w, h) => {
    shadowCard(g, 20, 20, w - 40, h - 40, 40, '#FBF8F2');
    text(g, 'MEETING MINUTES  ·  Q3 LAUNCH SYNC', 90, 120, FONT.ui, 38, C.mute, 'left', 'alphabetic', 8);
    text(g, 'For the record', 90, 240, FONT.disp, 110, C.ink);
    g.strokeStyle = C.line; g.lineWidth = 3; g.beginPath(); g.moveTo(90, 290); g.lineTo(w - 90, 290); g.stroke();
    text(g, '10:00:04', 90, 390, FONT.mono, 50, C.mute); g.fillStyle = C.mint; g.beginPath(); g.arc(380, 372, 34, 0, 7); g.fill(); text(g, 'Y', 380, 390, FONT.disp, 40, C.indigo, 'center');
    text(g, 'I said it first.', 440, 392, FONT.ui, 64, C.ink);
    if (first) { g.save(); g.translate(1060, 470); g.rotate(-0.1); g.strokeStyle = C.gold; g.fillStyle = 'rgba(255,210,122,0.18)'; g.lineWidth = 10; rr(g, -180, -64, 360, 128, 20); g.fill(); g.stroke(); text(g, 'FIRST', 0, 26, FONT.dispBlack, 84, '#B8860B', 'center', 'alphabetic', 8); g.restore(); }
    let x = 90; chips.forEach(([t, kind]) => { g.font = `56px ${FONT.ui}`; const tw = g.measureText(t).width + 80 + (kind === 'good' ? 50 : 0);
      g.fillStyle = kind === 'good' ? 'rgba(46,156,124,0.16)' : 'rgba(229,72,77,0.15)'; rr(g, x, 600, tw, 116, 58); g.fill();
      text(g, t + (kind === 'good' ? '  ✓' : ''), x + 40, 676, FONT.ui, 56, kind === 'good' ? C.mintDeep : C.red); x += tw + 26; });
    if (status || loading) { text(g, 'STATUS', 90, 840, FONT.ui, 38, C.mute, 'left', 'alphabetic', 8);
      if (loading) { g.strokeStyle = C.line; g.lineWidth = 12; g.beginPath(); g.arc(130, 940, 34, 0, 7); g.stroke(); g.strokeStyle = C.pink; g.beginPath(); g.arc(130, 940, 34, -1.6, 0.4); g.stroke(); }
      else { g.fillStyle = C.pink; g.beginPath(); g.arc(130, 940, 30, 0, 7); g.fill(); }
      text(g, status || 'becoming…', 200, 962, FONT.disp, 66, C.ink); }
  }, 3.0);
}

// a single big chip / status pill that floats beside a face
export function pill(t, kind, worldH = 0.36) {
  const tmp = document.createElement('canvas').getContext('2d'); tmp.font = `84px ${FONT.ui}`; const tw = tmp.measureText(t).width;
  const W = Math.ceil(tw + (kind === 'good' ? 260 : 200)), H = 190;
  return panel(W, H, (g, w, h) => { g.save(); g.shadowColor = 'rgba(10,12,30,0.4)'; g.shadowBlur = 22; g.shadowOffsetY = 8;
    g.fillStyle = kind === 'status' ? 'rgba(16,18,40,0.92)' : '#FBF8F2'; rr(g, 10, 10, w - 20, h - 20, (h - 20) / 2); g.fill(); g.restore();
    if (kind === 'good' || kind === 'bad') { g.fillStyle = kind === 'good' ? 'rgba(46,156,124,0.18)' : 'rgba(229,72,77,0.16)'; rr(g, 10, 10, w - 20, h - 20, (h - 20) / 2); g.fill(); }
    const col = kind === 'good' ? C.mintDeep : kind === 'bad' ? C.red : '#FFF4DE';
    let x = 80; if (kind === 'status' || kind === 'loading') { if (t.startsWith('becoming')) { g.strokeStyle = 'rgba(255,255,255,0.25)'; g.lineWidth = 12; g.beginPath(); g.arc(110, h / 2, 34, 0, 7); g.stroke(); g.strokeStyle = C.pink; g.beginPath(); g.arc(110, h / 2, 34, -1.6, 0.6); g.stroke(); }
      else { g.fillStyle = C.pink; g.beginPath(); g.arc(110, h / 2, 30, 0, 7); g.fill(); } x = 175; }
    text(g, t + (kind === 'good' ? '  ✓' : ''), x, h / 2 + 30, FONT.ui, 84, kind === 'status' ? '#FFF4DE' : col); }, worldH, { lit: kind === 'status', glow: 0.95 });
}

// your notes, finally written (the card from B03, now with words in it)
export function notesFilled() {
  return panel(1200, 900, (g, w, h) => {
    shadowCard(g, 20, 20, w - 40, h - 40, 36, '#FBF8F2');
    text(g, 'MEETING NOTES', 90, 130, FONT.ui, 40, C.mute, 'left', 'alphabetic', 8);
    text(g, 'Q3 Launch Sync', 90, 230, FONT.disp, 76, C.ink); text(g, 'You  ·  11 words', 90, 310, FONT.ui, 46, C.mintDeep);
    g.strokeStyle = C.line; g.lineWidth = 3; g.beginPath(); g.moveTo(90, 360); g.lineTo(w - 90, 360); g.stroke();
    text(g, 'We should push the launch.', 90, 480, FONT.disp, 72, C.ink); text(g, "We're not ready and we know it.", 90, 580, FONT.disp, 72, C.ink);
    g.fillStyle = 'rgba(127,224,194,0.35)'; rr(g, 80, 640, 520, 70, 12); g.fill(); text(g, '— You, 10:00:04', 100, 692, FONT.ui, 48, C.mintDeep);
  }, 2.2);
}
// the deck, as a billboard screen (1920x1080), with one part picked out
export function deckSlide(focus = null) {
  return canvasTex(1920, 1080, (g, w, h) => {
    g.fillStyle = '#2b2e3f'; g.fillRect(0, 0, w, h);
    g.fillStyle = '#3a3e52'; g.fillRect(0, 0, w, 110);
    for (let i = 0; i < 3; i++) { g.fillStyle = ['#ff5f57', '#febc2e', '#28c840'][i]; g.beginPath(); g.arc(50 + i * 44, 55, 14, 0, 7); g.fill(); }
    text(g, 'my_idea_do_not_rephrase_v7_FINAL.deck', 200, 72, FONT.mono, 40, focus === 'file' ? C.gold : '#d5d8e6');
    g.fillStyle = focus === 'size' ? C.gold : '#4a4f66'; rr(g, 1480, 22, 380, 66, 12); g.fill(); text(g, 'Inter  ·  32 pt  ▾', 1510, 68, FONT.ui, 36, focus === 'size' ? C.indigo : '#e7e9f2');
    g.fillStyle = '#FBF8F2'; g.fillRect(110, 170, w - 220, h - 240);
    text(g, 'by You', 200, 330, FONT.disp, 96, C.pink);
    if (focus === 'name') { g.strokeStyle = C.gold; g.lineWidth = 10; rr(g, 175, 245, 400, 120, 20); g.stroke(); }
    text(g, 'Push the launch.', 200, 520, FONT.dispBlack, 170, C.ink); text(g, "We're not ready, and we know it.", 205, 620, FONT.ui, 64, C.mute);
    let x = 200; while (x < w - 360) { text(g, 'idea: You  ·', x, 930, FONT.ui, focus === 'footer' ? 34 : 26, focus === 'footer' ? C.pink : C.mute); x += focus === 'footer' ? 250 : 190; }
    if (focus === 'footer') { g.strokeStyle = C.gold; g.lineWidth = 8; rr(g, 180, 880, w - 540, 80, 16); g.stroke(); }
  });
}
// the email, sent before the meeting (billboard)
export function sentEmail() {
  return canvasTex(1920, 1080, (g, w, h) => {
    g.fillStyle = C.indigo; g.fillRect(0, 0, w, h);
    shadowCard(g, 200, 120, w - 400, h - 240, 30, '#FBF8F2');
    text(g, 'SENT  ·  8:59 AM  ·  BEFORE THE MEETING', 300, 240, FONT.ui, 42, C.mintDeep, 'left', 'alphabetic', 8);
    text(g, 'To:  everyone@', 300, 340, FONT.ui, 50, C.mute); text(g, 'Subject:  Push the launch (my idea)', 300, 420, FONT.ui, 50, C.ink);
    g.strokeStyle = C.line; g.lineWidth = 3; g.beginPath(); g.moveTo(300, 470); g.lineTo(w - 300, 470); g.stroke();
    text(g, 'We should push the launch.', 300, 590, FONT.disp, 84, C.ink); text(g, "We're not ready and we know it.", 300, 690, FONT.disp, 84, C.ink);
    text(g, '— You', 300, 800, FONT.ui, 54, C.mintDeep);
  });
}
// an envelope you mailed to yourself; certified = the stamp
export function envelope(certified = false) {
  return panel(1300, 820, (g, w, h) => {
    shadowCard(g, 20, 20, w - 40, h - 40, 18, '#efe3c8');
    g.strokeStyle = 'rgba(120,90,40,0.35)'; g.lineWidth = 4; g.beginPath(); g.moveTo(30, 30); g.lineTo(w / 2, h / 2); g.lineTo(w - 30, 30); g.stroke();
    g.fillStyle = C.coral; rr(g, w - 230, 70, 140, 170, 8); g.fill(); g.fillStyle = '#fff'; rr(g, w - 215, 85, 110, 140, 6); g.fill(); text(g, '❤', w - 160, 180, FONT.ui, 70, C.coral, 'center');
    g.save(); g.font = `italic 80px ${FONT.serif}`; g.fillStyle = '#3a2c18'; g.fillText('To:  me', 380, 520); g.fillText('From:  me', 380, 620); g.restore();
    if (certified) { g.save(); g.translate(w / 2 - 60, h / 2 - 150); g.rotate(-0.16); g.strokeStyle = C.red; g.lineWidth = 14; rr(g, -330, -85, 660, 170, 18); g.stroke(); g.lineWidth = 5; rr(g, -305, -62, 610, 124, 12); g.stroke();
      text(g, 'CERTIFIED', 0, 32, FONT.dispBlack, 110, C.red, 'center', 'alphabetic', 10); g.restore(); }
  }, 1.9);
}
// this week, with Thursday picked out (and later, the 1st ribbon)
export function weekStrip(first = false) {
  return panel(1500, 640, (g, w, h) => {
    shadowCard(g, 20, 20, w - 40, h - 40, 36, '#FBF8F2');
    text(g, 'THIS WEEK', 90, 120, FONT.ui, 40, C.mute, 'left', 'alphabetic', 8);
    'MTWTF'.split('').forEach((d, i) => { const x = 140 + i * 260, on = i === 3; g.fillStyle = on ? C.pink : C.paper2; rr(g, x - 90, 180, 180, 220, 28); g.fill();
      text(g, d, x, 320, FONT.dispBlack, 110, on ? '#fff' : C.mute, 'center'); if (on) text(g, 'said it again', x, 380, FONT.ui, 26, '#fff', 'center'); });
    if (first) { g.save(); g.translate(920, 520); g.fillStyle = C.gold; g.beginPath(); g.arc(0, 0, 80, 0, 7); g.fill(); g.fillStyle = '#B8860B';
      g.beginPath(); g.moveTo(-50, 50); g.lineTo(-80, 120); g.lineTo(-20, 95); g.fill(); g.beginPath(); g.moveTo(50, 50); g.lineTo(80, 120); g.lineTo(20, 95); g.fill();
      text(g, '1st', 0, 30, FONT.dispBlack, 80, C.indigo, 'center'); g.restore(); }
  }, 2.2);
}

// a filled donut, drawn like a bakery label: no hole, powdered sugar, a bite showing the jam
export function filledDonutCard() {
  return panel(1100, 820, (g, w, h) => {
    shadowCard(g, 20, 20, w - 40, h - 40, 44, '#FBF8F2');
    const cv = document.createElement('canvas'); cv.width = w; cv.height = h; const d = cv.getContext('2d');   // the donut on its own layer, so the bite cuts only the donut
    const cx = w / 2 - 20, cy = 450, R = 300;
    const body = d.createRadialGradient(cx - 70, cy - 90, 40, cx, cy, R); body.addColorStop(0, '#f2c27c'); body.addColorStop(0.75, '#d9963f'); body.addColorStop(1, '#b8752e');
    d.fillStyle = body; d.beginPath(); d.ellipse(cx, cy, R, R * 0.82, 0, 0, 7); d.fill();
    d.fillStyle = '#e8b06a'; d.beginPath(); d.ellipse(cx, cy + 20, R * 0.96, R * 0.12, 0, 0, Math.PI); d.fill();
    let sd = 3; const RR = () => (sd = (sd * 16807) % 2147483647) / 2147483647;
    d.fillStyle = 'rgba(255,255,255,0.85)'; for (let i = 0; i < 900; i++) { const a = RR() * 7, r = Math.sqrt(RR()) * R * 0.95; const x = cx + Math.cos(a) * r, y = cy - 40 + Math.sin(a) * r * 0.6; if (y < cy + 10) { d.beginPath(); d.arc(x, y, 2 + RR() * 3, 0, 7); d.fill(); } }
    // ludicrous toppings: rainbow sprinkles, cereal loops, mini marshmallows, a gummy bear, a strip of bacon, a candle
    const cols = ['#ff4f6d', '#45f0ff', '#ffd27a', '#7fe0c2', '#9b6bff', '#ffffff'];
    for (let i = 0; i < 160; i++) { const a = RR() * 7, r = Math.sqrt(RR()) * R * 0.85, x = cx + Math.cos(a) * r, y = cy - 60 + Math.sin(a) * r * 0.5; d.save(); d.translate(x, y); d.rotate(RR() * 3); d.fillStyle = cols[i % 6]; d.fillRect(-9, -3, 18, 6); d.restore(); }
    [[-150, -110, '#ff6b5b'], [-60, -150, '#ffd27a'], [40, -120, '#b98cff']].forEach(([dx, dy, c]) => { d.strokeStyle = c; d.lineWidth = 14; d.beginPath(); d.ellipse(cx + dx, cy + dy, 24, 18, 0.3, 0, 7); d.stroke(); });
    [[-120, -40], [-80, -20], [-100, 10]].forEach(([dx, dy]) => { d.fillStyle = '#fffaf2'; d.strokeStyle = '#e6dccb'; d.lineWidth = 3; rr(d, cx + dx - 18, cy + dy - 14, 36, 28, 8); d.fill(); d.stroke(); });
    d.save(); d.translate(cx - 10, cy - 70); d.rotate(-0.2); d.fillStyle = '#b5543a'; rr(d, -90, -14, 180, 28, 10); d.fill(); d.fillStyle = '#f2c3a8'; rr(d, -90, -4, 180, 8, 4); d.fill(); d.restore();
    d.fillStyle = '#5ee08f'; d.beginPath(); d.ellipse(cx + 60, cy - 30, 30, 38, 0, 0, 7); d.fill(); d.beginPath(); d.arc(cx + 60, cy - 78, 22, 0, 7); d.fill(); d.beginPath(); d.arc(cx + 44, cy - 96, 9, 0, 7); d.arc(cx + 76, cy - 96, 9, 0, 7); d.fill();
    d.fillStyle = '#7fd8ff'; d.fillRect(cx - 36, cy - 260, 16, 120); d.fillStyle = '#ffb347'; d.beginPath(); d.ellipse(cx - 28, cy - 282, 12, 22, 0, 0, 7); d.fill();
    d.globalCompositeOperation = 'destination-out'; for (const [dx, dy, r] of [[R * 0.8, -40, 95], [R * 0.92, 40, 80], [R * 0.62, 10, 70]]) { d.beginPath(); d.arc(cx + dx, cy + dy, r, 0, 7); d.fill(); }
    d.globalCompositeOperation = 'source-over';
    d.fillStyle = '#f6e3bf'; d.beginPath(); d.ellipse(cx + R * 0.48, cy, 66, 116, 0.1, 0, 7); d.fill();
    const jam = d.createRadialGradient(cx + R * 0.5, cy, 10, cx + R * 0.5, cy, 70); jam.addColorStop(0, '#ff3b5c'); jam.addColorStop(1, '#a8102e'); d.fillStyle = jam; d.beginPath(); d.ellipse(cx + R * 0.5, cy + 6, 44, 80, 0.1, 0, 7); d.fill();
    d.beginPath(); d.moveTo(cx + R * 0.5, cy + 60); d.quadraticCurveTo(cx + R * 0.6, cy + 170, cx + R * 0.54, cy + 210); d.lineWidth = 26; d.lineCap = 'round'; d.strokeStyle = '#c0183a'; d.stroke();
    g.save(); g.shadowColor = 'rgba(60,30,10,0.3)'; g.shadowBlur = 30; g.shadowOffsetY = 14; g.drawImage(cv, 0, 0); g.restore();
  }, 1.6);
}
// the bakery's sign: the filled ones sell out by 8
export function bakerySign() {
  return panel(1400, 760, (g, w, h) => {
    g.fillStyle = '#2a1a14'; rr(g, 0, 0, w, h, 36); g.fill(); g.strokeStyle = '#ffd27a'; g.lineWidth = 8; rr(g, 24, 24, w - 48, h - 48, 26); g.stroke();
    g.save(); g.font = `italic 120px ${FONT.serif}`; g.textAlign = 'center'; g.shadowColor = C.pink; g.shadowBlur = 30; g.fillStyle = '#ffd7ea'; g.fillText('Filled Donuts', w / 2, 230); g.restore();
    text(g, 'raspberry  ·  custard  ·  lemon', w / 2, 330, FONT.ui, 50, '#f4efe6', 'center');
    g.fillStyle = C.red; rr(g, w / 2 - 560, 420, 1120, 220, 30); g.fill();
    text(g, 'SOLD OUT AFTER 8:00', w / 2, 560, FONT.dispBlack, 84, '#fff', 'center', 'alphabetic', 2);
  }, 2.0, { lit: true, glow: 0.9 });
}
// the meeting log, building up: 9:04 you, 9:07 Ted joined, then the witnesses
export function meetingLog(step, heads = []) {
  return panel(1500, 980, (g, w, h) => {
    shadowCard(g, 20, 20, w - 40, h - 40, 40, '#FBF8F2');
    text(g, 'MEETING LOG  ·  THURSDAY', 90, 130, FONT.ui, 42, C.mute, 'left', 'alphabetic', 8);
    const row = (y, t, who, col, msg, faded) => { text(g, t, 90, y, FONT.monoB, 84, faded ? C.mute : C.pink); g.fillStyle = col; g.beginPath(); g.arc(440, y - 28, 36, 0, 7); g.fill();
      text(g, who, 440, y - 12, FONT.disp, 40, C.indigo, 'center'); text(g, msg, 510, y - 6, FONT.ui, 60, faded ? C.mute : C.ink); };
    row(300, '9:04', 'Y', C.mint, 'we should push the launch', false);
    if (step >= 2) row(450, '9:07', 'T', C.coral, 'Ted joined the meeting', true);
    if (step >= 3) { text(g, 'WITNESSES', 90, 640, FONT.ui, 40, C.mute, 'left', 'alphabetic', 8);
      heads.slice(0, 6).forEach((cv, i) => { const cx = 150 + i * 190, cy = 790; g.save(); g.beginPath(); g.arc(cx, cy, 80, 0, 7); g.closePath(); g.fillStyle = C.paper2; g.fill(); g.clip(); if (cv) g.drawImage(cv, cx - 80, cy - 80, 160, 160); g.restore();
        g.strokeStyle = C.mintDeep; g.lineWidth = 8; g.beginPath(); g.arc(cx, cy, 84, 0, 7); g.stroke(); });
      g.fillStyle = C.mintDeep; rr(g, 1290, 740, 130, 100, 50); g.fill(); text(g, '6 ✓', 1355, 808, FONT.disp, 52, '#fff', 'center'); }
  }, 3.0);
}

// the org chart, rearranged by Friday (billboard, 1920x1080)
export function orgChart(heads) {   // heads: { ted, dana, you }
  return canvasTex(1920, 1080, (g, w, h) => {
    g.fillStyle = C.paper; g.fillRect(0, 0, w, h);
    text(g, 'Org chart  ·  updated Friday', 110, 130, FONT.disp, 72, C.ink); text(g, 'brightloop.', w - 110, 130, FONT.disp, 52, C.mute, 'right');
    const node = (x, y, cv, name, title, gold, faded) => { g.save(); if (faded) g.globalAlpha = 0.45; const W = 560, H = 250; shadowCard(g, x - W / 2, y - H / 2, W, H, 30, '#FFFFFF');
      if (gold) { g.strokeStyle = C.gold; g.lineWidth = 12; rr(g, x - W / 2, y - H / 2, W, H, 30); g.stroke(); }
      g.save(); g.beginPath(); g.arc(x - W / 2 + 115, y, 75, 0, 7); g.closePath(); g.fillStyle = C.paper2; g.fill(); g.clip(); if (cv) g.drawImage(cv, x - W / 2 + 40, y - 75, 150, 150); g.restore();
      const tx = x - W / 2 + 220, maxW = W - 250; let ts = 40; g.font = `${ts}px ${FONT.ui}`; while (g.measureText(title).width > maxW) { ts -= 2; g.font = `${ts}px ${FONT.ui}`; }   // titles always fit the card
      text(g, name, tx, y - 8, FONT.disp, 68, C.ink); text(g, title, tx, y + 56, FONT.ui, ts, gold ? '#B8860B' : C.mute); g.restore(); };
    g.strokeStyle = C.line; g.lineWidth = 8; g.beginPath(); g.moveTo(w / 2, 470); g.lineTo(w / 2, 560); g.moveTo(w / 2 - 520, 560); g.lineTo(w / 2 + 520, 560); g.moveTo(w / 2 - 520, 560); g.lineTo(w / 2 - 520, 640); g.moveTo(w / 2 + 520, 560); g.lineTo(w / 2 + 520, 640); g.stroke();
    node(w / 2, 350, heads.ted, 'Ted', 'VP, as of Friday', true);
    node(w / 2 - 520, 760, heads.dana, 'Dana', 'reports to Ted', false); node(w / 2 + 520, 760, heads.you, 'You', 'reports to Ted', false, true);
    g.save(); g.translate(w / 2 + 300, 225); g.rotate(0.12); g.fillStyle = C.coral; rr(g, -120, -44, 240, 88, 44); g.fill(); text(g, 'NEW', 0, 18, FONT.dispBlack, 56, '#fff', 'center', 'alphabetic', 6); g.restore();
  });
}
// the conference-room sign, and the plaque under it
export function roomSign() {
  return panel(1500, 760, (g, w, h) => {
    g.fillStyle = '#16181f'; rr(g, 0, 0, w, h, 34); g.fill(); g.strokeStyle = '#3a3e52'; g.lineWidth = 6; rr(g, 14, 14, w - 28, h - 28, 26); g.stroke();
    text(g, 'ROOM BOOKING  ·  FLOOR 4', 90, 130, FONT.ui, 44, '#9aa0bb', 'left', 'alphabetic', 8);
    g.save(); g.font = `196px ${FONT.dispBlack}`; g.shadowColor = C.gold; g.shadowBlur = 26; g.fillStyle = '#FFF4DE'; g.fillText('The Ted Room', 80, 390); g.restore();
    g.fillStyle = C.mintDeep; rr(g, 90, 500, 520, 110, 55); g.fill(); text(g, 'Available  ·  book now', 350, 572, FONT.ui, 48, '#fff', 'center');
    text(g, '12 seats', 680, 572, FONT.ui, 52, '#cfd3e6');
  }, 2.4, { lit: true, glow: 0.92 });
}
export function plaqueWall() {
  return panel(2400, 1350, (g, w, h) => {
    const wall = g.createLinearGradient(0, 0, 0, h); wall.addColorStop(0, '#0f2420'); wall.addColorStop(1, '#0a1714'); g.fillStyle = wall; g.fillRect(0, 0, w, h);
    g.strokeStyle = 'rgba(255,255,255,0.05)'; g.lineWidth = 4; for (let x = 0; x < w; x += 160) { g.beginPath(); g.moveTo(x, 0); g.lineTo(x, h * 0.72); g.stroke(); }   // panelling
    g.fillStyle = '#081210'; g.fillRect(0, h * 0.72, w, h * 0.28); g.fillStyle = '#c9a44c'; g.fillRect(0, h * 0.72 - 6, w, 6);   // dado rail
    const spot = g.createRadialGradient(w / 2, h * 0.36, 40, w / 2, h * 0.4, 900); spot.addColorStop(0, 'rgba(255,224,170,0.55)'); spot.addColorStop(0.5, 'rgba(255,214,150,0.16)'); spot.addColorStop(1, 'rgba(255,214,150,0)'); g.fillStyle = spot; g.fillRect(0, 0, w, h);
    g.fillStyle = '#1b1b20'; rr(g, w / 2 - 70, 0, 140, 50, 10); g.fill(); g.fillStyle = 'rgba(255,236,200,0.85)'; g.beginPath(); g.ellipse(w / 2, 52, 50, 10, 0, 0, 7); g.fill();   // the picture light
    const px = w / 2 - 760, py = 180, pw = 1520, ph = 640;
    g.save(); g.shadowColor = 'rgba(0,0,0,0.6)'; g.shadowBlur = 40; g.shadowOffsetY = 20;
    const brass = g.createLinearGradient(px, py, px + pw, py + ph); brass.addColorStop(0, '#f3d27a'); brass.addColorStop(0.45, '#c99a3a'); brass.addColorStop(0.55, '#e7c164'); brass.addColorStop(1, '#a77a26'); g.fillStyle = brass; rr(g, px, py, pw, ph, 28); g.fill(); g.restore();
    g.strokeStyle = 'rgba(70,45,8,0.6)'; g.lineWidth = 6; rr(g, px + 28, py + 28, pw - 56, ph - 56, 16); g.stroke();
    for (const [sx, sy] of [[px + 60, py + 60], [px + pw - 60, py + 60], [px + 60, py + ph - 60], [px + pw - 60, py + ph - 60]]) { g.fillStyle = '#8a6420'; g.beginPath(); g.arc(sx, sy, 14, 0, 7); g.fill(); }
    text(g, 'NAMED IN HONOR OF HIS BRAVE DISCOVERY', w / 2, py + 150, FONT.ui, 44, '#4a3410', 'center', 'alphabetic', 8);
    g.save(); g.font = `italic 118px ${FONT.serif}`; g.textAlign = 'center'; g.fillStyle = '#2e2008'; g.fillText('"We should push the launch."', w / 2, py + 330); g.restore();
    text(g, '— TED', w / 2, py + 450, FONT.dispBlack, 64, '#2e2008', 'center', 'alphabetic', 12);
    text(g, '(first said by You, 10:00:04)', w / 2, py + 560, FONT.ui, 38, 'rgba(46,32,8,0.6)', 'center');
    // velvet rope on two brass stanchions, like it's in a museum
    for (const sx of [w / 2 - 900, w / 2 + 900]) { g.fillStyle = '#c9a44c'; g.fillRect(sx - 12, h - 470, 24, 380); g.beginPath(); g.arc(sx, h - 480, 30, 0, 7); g.fill(); g.fillRect(sx - 70, h - 100, 140, 26); }
    g.strokeStyle = '#8f1020'; g.lineWidth = 34; g.lineCap = 'round'; g.beginPath(); g.moveTo(w / 2 - 900, h - 450); g.quadraticCurveTo(w / 2, h - 230, w / 2 + 900, h - 450); g.stroke();
  }, 5.4);
}
export function plaque() {
  return panel(1500, 600, (g, w, h) => {
    const gr = g.createLinearGradient(0, 0, 0, h); gr.addColorStop(0, '#e9c46a'); gr.addColorStop(1, '#b8892f'); g.fillStyle = gr; rr(g, 0, 0, w, h, 24); g.fill();
    g.strokeStyle = 'rgba(80,55,10,0.55)'; g.lineWidth = 8; rr(g, 26, 26, w - 52, h - 52, 14); g.stroke();
    text(g, 'NAMED IN HONOR OF HIS BRAVE DISCOVERY', w / 2, 140, FONT.ui, 52, '#4a3410', 'center', 'alphabetic', 8);
    g.save(); g.font = `italic 104px ${FONT.serif}`; g.textAlign = 'center'; g.fillStyle = '#2e2008'; g.fillText('"We should push the launch."', w / 2, 300); g.restore();
    text(g, '— Ted', w / 2, 400, FONT.disp, 64, '#2e2008', 'center');
    text(g, 'first said by You, 10:00:04', w - 70, h - 60, FONT.ui, 26, 'rgba(46,32,8,0.55)', 'right');
  }, 1.6);
}

// "why it worked when Ted said it": a pie that grows a slice per line (billboard 1920x1080)
export function whyPie(n) {
  const sl = [['maybe it’s the donuts', '#FF8FC2'], ['maybe it’s the voice', '#5B6BC8'], ['maybe it’s the shoulders', '#FFD27A'], ['maybe it’s the donuts', '#FF4FB0']];
  return canvasTex(1920, 1080, (g, w, h) => {
    g.fillStyle = C.paper; g.fillRect(0, 0, w, h);
    text(g, 'Why it worked when Ted said it', 110, 150, FONT.disp, 84, C.ink);
    const cx = 560, cy = 620, R = 330; let a = -Math.PI / 2; const parts = [0.34, 0.22, 0.2, 0.24].slice(0, n), tot = parts.reduce((x, y) => x + y, 0);
    if (n === 0) { g.strokeStyle = C.line; g.lineWidth = 8; g.beginPath(); g.arc(cx, cy, R, 0, 7); g.stroke(); }
    parts.forEach((p, i) => { const da = p / tot * Math.PI * 2; g.fillStyle = sl[i][1]; g.beginPath(); g.moveTo(cx, cy); g.arc(cx, cy, R, a, a + da); g.closePath(); g.fill(); g.strokeStyle = C.paper; g.lineWidth = 10; g.stroke(); a += da; });
    sl.slice(0, n).forEach(([t, col], i) => { const y = 430 + i * 120; g.fillStyle = col; rr(g, 990, y - 50, 56, 56, 10); g.fill(); text(g, t, 1075, y, FONT.ui, 52, i === n - 1 ? C.ink : C.mute); });
  });
}
// the spreadsheet, stage by stage: 1 headers+rows, 2 timestamps, 3 formatting rule, 4 Ted is red (billboard 1920x1080)
export function sheet(stage) {
  return canvasTex(1920, 1080, (g, w, h) => {
    g.fillStyle = '#FFFFFF'; g.fillRect(0, 0, w, h);
    g.fillStyle = '#1F7A4C'; rr(g, 70, 60, 70, 70, 12); g.fill(); text(g, 'X', 105, 112, FONT.dispBlack, 48, '#fff', 'center');
    text(g, 'who_said_it_first.xlsx', 170, 112, FONT.ui, 52, C.ink);
    if (stage >= 3) { g.fillStyle = 'rgba(229,72,77,0.1)'; rr(g, 1120, 62, 730, 70, 35); g.fill(); text(g, 'Conditional formatting:  Credit = Ted  →  red', 1485, 108, FONT.ui, 32, C.red, 'center'); }
    const cols = [[90, 'When'], [420, 'Idea'], [1000, stage >= 2 ? 'You said it' : ''], [1370, stage >= 2 ? 'Ted said it' : ''], [1700, 'Credit']];
    g.fillStyle = '#F1F3F6'; g.fillRect(70, 170, w - 140, 90); cols.forEach(([x, t]) => text(g, t, x, 230, FONT.ui, 42, C.mute));
    const rows = [['Tue 10:00', 'push the launch', '10:00:04', '10:08:21'], ['Tue 14:30', 'cache the API', '14:31:10', '14:39:02'], ['Wed 09:15', 'kill the old cron', '09:15:44', '09:22:38'], ['Thu 09:04', 'push the launch (again)', '09:04:00', '09:31:40'], ['Fri 11:00', 'ship it Monday', '11:00:12', '11:06:55']];
    rows.forEach((r, i) => { const y = 340 + i * 120; g.strokeStyle = '#E6E8EC'; g.lineWidth = 3; g.beginPath(); g.moveTo(70, y + 45); g.lineTo(w - 70, y + 45); g.stroke();
      text(g, r[0], 90, y, FONT.mono, 44, C.ink); text(g, r[1], 420, y, FONT.ui, 46, C.ink);
      if (stage >= 2) { text(g, r[2], 1000, y, FONT.mono, 44, C.mintDeep); text(g, r[3], 1370, y, FONT.mono, 44, C.ink); }
      if (stage >= 4) { g.fillStyle = C.red; g.fillRect(1350, y - 60, 500, 100); text(g, r[3], 1370, y, FONT.mono, 44, '#fff'); text(g, 'Ted', 1700, y, FONT.ui, 46, '#fff'); }
      else text(g, 'Ted', 1700, y, FONT.ui, 46, C.ink); });
  });
}

export function timerPanel(mm, checked) {
  return panel(1400, 900, (g, w, h) => {
    g.save(); g.shadowColor = 'rgba(0,0,0,0.5)'; g.shadowBlur = 50; g.fillStyle = 'rgba(16,18,40,0.92)'; rr(g, 30, 30, w - 60, h - 60, 50); g.fill(); g.restore();
    text(g, checked ? 'I CHECKED' : 'SINCE YOU SAID IT', w / 2, 200, FONT.ui, 56, C.peach, 'center', 'alphabetic', 12);
    g.save(); g.font = `330px ${FONT.monoB}`; g.textAlign = 'center'; g.shadowColor = C.gold; g.shadowBlur = 24; g.fillStyle = '#FFF4DE'; g.fillText(mm, w / 2, 560); g.restore();
    if (checked) { g.save(); g.translate(w / 2, 720); g.rotate(-0.08); g.strokeStyle = C.coral; g.lineWidth = 12; rr(g, -260, -80, 520, 140, 22); g.stroke(); text(g, 'VERIFIED', 0, 30, FONT.dispBlack, 92, C.coral, 'center'); g.restore(); }
  }, 3.0, { lit: true, glow: 0.95 });
}
export function lobbyPanel(joined, total = 12, clock = '09:59:58') {
  return panel(1600, 1000, (g, w, h) => {
    shadowCard(g, 30, 30, w - 60, h - 60, 50, '#FBF8F2');
    text(g, `TUESDAY  ·  ${clock}`, w / 2, 170, FONT.ui, 48, C.mute, 'center', 'alphabetic', 8);
    text(g, 'Q3 Launch Sync', w / 2, 300, FONT.disp, 110, C.ink, 'center');
    const n = Math.min(joined.length, 7);
    for (let i = 0; i < n; i++) { const cx = w / 2 + (i - (n - 1) / 2) * 120; g.fillStyle = joined[i][1]; g.beginPath(); g.arc(cx, 470, 70, 0, 7); g.fill(); g.strokeStyle = '#FBF8F2'; g.lineWidth = 10; g.stroke();
      text(g, joined[i][0][0], cx, 497, FONT.disp, 72, '#fff', 'center'); }
    if (joined.length > 7) { const cx = w / 2 + ((n + 1) - (n + 1) / 2 - 0.5) * 120 + 60; }
    text(g, `${joined[joined.length - 1][0]} joined  ·  ${joined.length} of ${total} waiting`, w / 2, 640, FONT.ui, 50, C.ink, 'center');
    g.fillStyle = C.coral; rr(g, w / 2 - 210, 720, 420, 130, 34); g.fill(); text(g, 'Join now', w / 2, 805, FONT.disp, 66, '#fff', 'center');
  }, 3.2);
}

// ---------------------------------------------------------------- the 2D caption layer (rendered separately in the real film)
export function captionBand(g, W, H) {   // the darker of the bottom and top bands (rooms are bright, sky and roof are dark)
  // cost of a band: how much of it is bright surface (a lit room, a card), which a caption must never cover; then mean brightness
  const cost = (y0) => { const d = g.getImageData(Math.round(W * 0.15), Math.round(H * y0), Math.round(W * 0.7), Math.round(H * 0.1)).data; let s = 0, bright = 0, n = 0;
    for (let i = 0; i < d.length; i += 16) { const l = 0.2126 * d[i] + 0.7152 * d[i + 1] + 0.0722 * d[i + 2]; s += l; if (l > 120) bright++; n++; } return bright / n * 4 + s / n / 255; };
  const b = cost(0.835), t = cost(0.07); return b <= t * 1.1 ? 0.885 : 0.115;
}
export function drawCaption(g, W, H, who, line, { col = C.mint, y = null } = {}) {
  if (y === null) y = captionBand(g, W, H);
  const size = Math.round(W * 0.03), pad = size * 0.55;
  g.font = `${size}px ${FONT.ui}`; const ww = g.measureText(who).width, lw = g.measureText(line).width; const tw = ww + size * 0.5 + lw + pad * 2;
  const x0 = (W - tw) / 2, y0 = H * y - size;
  g.fillStyle = 'rgba(12,14,30,0.62)'; rr(g, x0, y0, tw, size * 1.75, size * 0.5); g.fill();
  g.font = `${size}px ${FONT.disp}`; g.fillStyle = col; g.textBaseline = 'middle'; g.fillText(who, x0 + pad, y0 + size * 0.88);
  g.font = `${size}px ${FONT.ui}`; g.fillStyle = '#F7F4EE'; g.fillText(line, x0 + pad + ww + size * 0.5, y0 + size * 0.88); g.textBaseline = 'alphabetic';
}
