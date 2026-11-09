// S1: text built into the city, in Great Idea, Ted's design system (ported from its boards.js): warm paper and indigo ink,
// mint for her, gold LEDs, lit boards that bloom a little. Type: Inter Display (headlines), Inter SemiBold (UI),
// JetBrains Mono (numbers, the terminal).
import * as THREE from 'three';
import { FONT, canvasTex, clay } from './lib.js';
import { dayTint } from './city.js';

export const C = { paper: '#F4EFE6', paper2: '#E9E2D6', ink: '#1E2240', mute: '#6B6F86', line: '#D9D1C3', coral: '#FF6B5B', coralDeep: '#D9473A',
  mint: '#7FE0C2', mintDeep: '#2E9C7C', peach: '#F2A88C', indigo: '#1F2547', gold: '#FFD27A', red: '#E5484D', pink: '#FF4FB0', cyan: '#45F0FF' };

export function panel(wPx, hPx, draw, worldH, { lit = false, glow = 1, transparent = true } = {}) {
  const tex = canvasTex(wPx, hPx, draw);
  const mat = new THREE.MeshBasicMaterial({ map: tex, transparent, depthWrite: !transparent, toneMapped: !lit });
  mat.color.setScalar(lit ? glow : 0.86);
  const m = new THREE.Mesh(new THREE.PlaneGeometry(worldH * wPx / hPx, worldH), mat); m.userData.tex = tex; m.userData.w = worldH * wPx / hPx; return m;
}
export function rr(g, x, y, w, h, r) { g.beginPath(); g.roundRect(x, y, w, h, r); }
export function text(g, s, x, y, font, size, color, align = 'left', base = 'alphabetic', track = 0) {
  g.font = `${size}px ${font}`; g.fillStyle = color; g.textAlign = align; g.textBaseline = base;
  if (track) { g.letterSpacing = `${track}px`; } g.fillText(s, x, y); g.letterSpacing = '0px';
}

// ---------------------------------------------------------------- a billboard on its own tower (as in Great Idea, Ted)
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
  g.userData.set = (tex) => { board.material.map = tex; board.material.color.setScalar(tex ? 0.9 : 1); board.material.needsUpdate = true; };
  g.userData.board = board;
  return g;
}
// the hook, set on the billboard word by word as she sings it (n = words shown, 0..5)
export function hookBoard(n) {
  return canvasTex(1920, 1080, (g, w, h) => {
    g.fillStyle = C.indigo; g.fillRect(0, 0, w, h);
    const gr = g.createRadialGradient(w * 0.5, h * 0.45, 50, w * 0.5, h * 0.45, w * 0.7); gr.addColorStop(0, 'rgba(127,224,194,0.20)'); gr.addColorStop(1, 'rgba(127,224,194,0)'); g.fillStyle = gr; g.fillRect(0, 0, w, h);
    const W1 = ['LOOK', 'WHAT'], W2 = ['I', 'CAN', 'DO!']; const sz = 300;
    g.font = `${sz}px ${FONT.dispBlack}`; g.letterSpacing = '-6px';
    const line = (words, y, k0, col) => { const sp = sz * 0.28, ws = words.map((s) => g.measureText(s).width), tot = ws.reduce((a, b) => a + b, 0) + sp * (words.length - 1);
      let x = (w - tot) / 2; words.forEach((s, i) => { const on = k0 + i < n; g.save(); g.textAlign = 'left'; g.textBaseline = 'alphabetic';
        if (on) { g.shadowColor = col; g.shadowBlur = 28; g.fillStyle = col; g.fillText(s, x, y); g.shadowBlur = 0; g.fillStyle = col === '#ffffff' ? '#ffffff' : '#E8FFF7'; g.fillText(s, x, y); }
        else { g.fillStyle = 'rgba(255,255,255,0.07)'; g.fillText(s, x, y); }
        g.restore(); x += ws[i] + sp; }); };
    line(W1, 470, 0, '#ffffff'); line(W2, 850, 2, C.mint);
  });
}

// ---------------------------------------------------------------- the tower clock, now counting who's in the meeting
export function counterSign() {
  const g = new THREE.Group(); const cv = document.createElement('canvas'); cv.width = 1200; cv.height = 400;
  const tex = new THREE.CanvasTexture(cv); tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = 8;
  const face = new THREE.Mesh(new THREE.PlaneGeometry(6, 2), new THREE.MeshBasicMaterial({ map: tex, toneMapped: false })); face.position.z = 0.16; g.add(face);
  const box = new THREE.Mesh(new THREE.BoxGeometry(6.4, 2.4, 0.3), clay(0x0c0d14)); g.add(box);
  let last = null;
  g.userData.set = (num, sub = 'IN THIS MEETING', col = C.gold) => { const key = num + '|' + sub; if (key === last) return; last = key;
    const c = cv.getContext('2d'); c.fillStyle = '#07080f'; c.fillRect(0, 0, 1200, 400);
    // a little person icon, then the count
    c.save(); c.translate(250, 175); c.fillStyle = col; c.shadowColor = col; c.shadowBlur = 24; c.beginPath(); c.arc(0, -52, 36, 0, 7); c.fill();
    c.beginPath(); c.roundRect(-60, 0, 120, 92, [56, 56, 10, 10]); c.fill(); c.restore();
    c.save(); c.font = `230px ${FONT.monoB}`; c.textAlign = 'left'; c.shadowColor = col; c.shadowBlur = 30; c.fillStyle = col; c.fillText(String(num), 360, 255); c.restore();
    text(c, sub, 600, 362, FONT.ui, 52, '#cfd3e6', 'center', 'alphabetic', 10); tex.needsUpdate = true; };
  g.userData.set(1); return g;
}

// ---------------------------------------------------------------- a status pill that floats beside a room
export function pill(t, kind, worldH = 0.36) {
  const tmp = document.createElement('canvas').getContext('2d'); tmp.font = `84px ${FONT.ui}`; const tw = tmp.measureText(t).width;
  const W = Math.ceil(tw + (kind === 'good' ? 300 : 260)), H = 190;
  return panel(W, H, (g, w, h) => { g.save(); g.shadowColor = 'rgba(10,12,30,0.4)'; g.shadowBlur = 22; g.shadowOffsetY = 8;
    g.fillStyle = kind === 'status' ? 'rgba(16,18,40,0.94)' : '#FBF8F2'; rr(g, 10, 10, w - 20, h - 20, (h - 20) / 2); g.fill(); g.restore();
    if (kind === 'good') { g.fillStyle = 'rgba(46,156,124,0.18)'; rr(g, 10, 10, w - 20, h - 20, (h - 20) / 2); g.fill(); }
    let x = 80;
    if (kind === 'status') { g.fillStyle = C.pink; g.beginPath(); g.arc(110, h / 2, 30, 0, 7); g.fill(); x = 175; }
    text(g, t, x, h / 2 + 30, FONT.ui, 84, kind === 'status' ? '#FFF4DE' : C.mintDeep);
    if (kind === 'good') { const cx = w - 115, cy = h / 2; g.fillStyle = C.mintDeep; g.beginPath(); g.arc(cx, cy, 44, 0, 7); g.fill();
      g.strokeStyle = '#fff'; g.lineWidth = 13; g.lineCap = 'round'; g.lineJoin = 'round'; g.beginPath(); g.moveTo(cx - 20, cy + 2); g.lineTo(cx - 5, cy + 17); g.lineTo(cx + 22, cy - 14); g.stroke(); }
  }, worldH, { lit: kind === 'status', glow: 0.95 });
}

// ---------------------------------------------------------------- her laptop screen at the end: the terminal, one command on
export function gitScreen() {
  return canvasTex(1600, 900, (g, w, h) => {
    g.fillStyle = '#0b0b0d'; g.fillRect(0, 0, w, h);
    text(g, 'adita@studio', 64, 92, FONT.monoB, 40, '#b8b8bc'); text(g, '~/look-what-i-can-do', 64 + 300, 92, FONT.mono, 40, '#7d7d84');
    g.font = `210px ${FONT.monoB}`; const cw = g.measureText('0').width;
    text(g, '$', 80, 470, FONT.monoB, 210, C.mint); text(g, 'git push', 80 + cw * 1.5, 470, FONT.monoB, 210, '#F2F2F4');
    text(g, '--force', 80 + cw * 1.5, 720, FONT.monoB, 210, C.coral);
    g.fillStyle = '#F2F2F4'; g.fillRect(80 + cw * 1.5 + cw * 7 + 30, 560, cw * 0.62, 200);   // the cursor, after --force
  });
}
