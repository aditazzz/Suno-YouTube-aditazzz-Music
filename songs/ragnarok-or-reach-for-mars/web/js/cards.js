// Future Arcana: the cards. Obsidian bodies, gilded edges, gold engraving drawn line by line on a canvas, and a
// two-faced (lenticular) front that shows one future from the left and another from the right.
import * as THREE from 'three';
import { rng, clamp } from './lib.js';
import { noise2 } from './lib2.js';

export const CW = 0.07, CH = 0.12, CD = 0.0016;          // tarot size in metres, a thick obsidian slab
const TW = 1200, TH = 2057;                              // texture size (same 70:120 ratio)
const GOLD = '#d9b25f', GOLD_HI = '#f4d995', GOLD_LO = '#9a7637';
const OBS = '#06070a';
const WIN = { x0: 96, x1: 1104, y0: 150, y1: 1690, cx: 600, ay: 654, r: 504 };   // the arched art window
const HORIZON = 1180;

// ---------------------------------------------------------------- canvas helpers
function canvas() { const c = document.createElement('canvas'); c.width = TW; c.height = TH; return c; }
function obsidian(g, seed) {
  const gr = g.createRadialGradient(TW * 0.42, TH * 0.38, 80, TW / 2, TH / 2, TH * 0.72);
  gr.addColorStop(0, '#11131a'); gr.addColorStop(0.55, '#08090d'); gr.addColorStop(1, '#030305');
  g.fillStyle = gr; g.fillRect(0, 0, TW, TH);
  const R = rng(seed); g.fillStyle = '#ffffff';                     // volcanic glass glints
  for (let i = 0; i < 900; i++) { g.globalAlpha = 0.04 + R() * 0.1; g.fillRect(R() * TW, R() * TH, 1 + R() * 1.6, 1 + R() * 1.6); }
  g.globalAlpha = 1;
}
function archPath(g, inset = 0) {
  const { x0, x1, y1, cx, ay, r } = WIN; g.beginPath();
  g.moveTo(x0 + inset, y1 - inset); g.lineTo(x0 + inset, ay); g.arc(cx, ay, r - inset, Math.PI, 0); g.lineTo(x1 - inset, y1 - inset); g.closePath();
}
function rosette(g, cx, cy, R0, k, n, amp, lw = 1.4, alpha = 0.8, col = GOLD) {
  g.save(); g.strokeStyle = col; g.lineWidth = lw; g.globalAlpha = alpha;
  for (let j = 0; j < n; j++) { const ph = j / n * Math.PI * 2; g.beginPath();
    for (let s = 0; s <= 900; s++) { const th = s / 900 * Math.PI * 2; const rr = R0 + amp * Math.sin(k * th + ph) + amp * 0.35 * Math.sin(2 * k * th - ph * 2);
      const x = cx + Math.cos(th) * rr, y = cy + Math.sin(th) * rr; s ? g.lineTo(x, y) : g.moveTo(x, y); }
    g.closePath(); g.stroke(); }
  g.restore();
}
function frame(g, seed) {
  g.save();
  g.strokeStyle = GOLD; g.lineWidth = 11; g.strokeRect(36, 36, TW - 72, TH - 72);
  g.strokeStyle = GOLD_HI; g.lineWidth = 2; g.strokeRect(50, 50, TW - 100, TH - 100);
  g.strokeStyle = GOLD; g.lineWidth = 3.5; g.strokeRect(64, 64, TW - 128, TH - 128);
  for (const [x, y] of [[64, 64], [TW - 64, 64], [64, TH - 64], [TW - 64, TH - 64]]) {   // corner rosettes
    g.fillStyle = OBS; g.beginPath(); g.arc(x, y, 34, 0, Math.PI * 2); g.fill();
    rosette(g, x, y, 22, 7, 10, 7, 1.2, 0.95); g.strokeStyle = GOLD; g.lineWidth = 3; g.beginPath(); g.arc(x, y, 31, 0, Math.PI * 2); g.stroke();
  }
  // the arch: a double rule round the art window
  g.strokeStyle = GOLD; g.lineWidth = 7; archPath(g, -10); g.stroke();
  g.strokeStyle = GOLD_HI; g.lineWidth = 1.6; archPath(g, -20); g.stroke();
  // little beads along the arch
  const { cx, ay, r } = WIN; g.fillStyle = GOLD;
  for (let k = 0; k <= 40; k++) { const a = Math.PI + k / 40 * Math.PI; g.beginPath(); g.arc(cx + Math.cos(a) * (r + 30), ay + Math.sin(a) * (r + 30), 3.2, 0, Math.PI * 2); g.fill(); }
  g.restore();
}
function titleBand(g, text, size = 112, top = null) {
  g.save();
  const y0 = 1726, y1 = 1946;
  g.strokeStyle = GOLD; g.lineWidth = 5; g.beginPath(); g.moveTo(96, y0); g.lineTo(TW - 96, y0); g.moveTo(96, y1); g.lineTo(TW - 96, y1); g.stroke();
  g.strokeStyle = GOLD_HI; g.lineWidth = 1.5; g.beginPath(); g.moveTo(96, y0 + 14); g.lineTo(TW - 96, y0 + 14); g.moveTo(96, y1 - 14); g.lineTo(TW - 96, y1 - 14); g.stroke();
  g.fillStyle = GOLD_HI; g.textAlign = 'center'; g.textBaseline = 'middle';
  for (;;) { g.font = `${size}px "CormSC", serif`; g.letterSpacing = `${Math.round(size * 0.22)}px`; if (g.measureText(text).width <= 860 || size < 60) break; size -= 4; }
  g.shadowColor = 'rgba(0,0,0,0.9)'; g.shadowBlur = 8; g.fillText(text, TW / 2 + size * 0.11, (y0 + y1) / 2 + size * 0.04);
  g.shadowBlur = 0;
  for (const s of [-1, 1]) { const x = TW / 2 + s * 470; g.fillStyle = GOLD; g.beginPath(); g.moveTo(x, (y0 + y1) / 2 - 16); g.lineTo(x + 16, (y0 + y1) / 2); g.lineTo(x, (y0 + y1) / 2 + 16); g.lineTo(x - 16, (y0 + y1) / 2); g.closePath(); g.fill(); }
  // top ornament (or a numeral)
  if (top) { g.fillStyle = OBS; g.beginPath(); g.arc(TW / 2, 104, 52, 0, Math.PI * 2); g.fill(); g.strokeStyle = GOLD; g.lineWidth = 4; g.stroke();
    g.fillStyle = GOLD_HI; g.font = `64px "CormSC", serif`; g.letterSpacing = '0px'; g.fillText(top, TW / 2, 108); }
  else { g.save(); g.translate(TW / 2, 104); g.fillStyle = GOLD; for (let k = 0; k < 8; k++) { g.rotate(Math.PI / 4); g.beginPath(); g.moveTo(0, -30 * (k % 2 ? 0.55 : 1)); g.lineTo(5, 0); g.lineTo(-5, 0); g.closePath(); g.fill(); } g.restore();
    g.strokeStyle = GOLD; g.lineWidth = 2; g.beginPath(); g.moveTo(TW / 2 - 300, 104); g.lineTo(TW / 2 - 50, 104); g.moveTo(TW / 2 + 50, 104); g.lineTo(TW / 2 + 300, 104); g.stroke(); }
  g.restore();
}

// engraved horizontal sky: fine broken lines, brighter near (gx, gy)
function sky(g, N, { y0, y1, step = 6, base = 0.16, glow = null, tint = GOLD, warm = null }) {
  g.save(); g.lineWidth = 1.7;
  for (let y = y0; y < y1; y += step) {
    let x = WIN.x0;
    while (x < WIN.x1) {
      const seg = 20 + N(x * 0.02, y * 0.1) * 70, gap = N(x * 0.05 + 9, y * 0.2) < 0.25 ? 6 + N(x, y) * 10 : 0;
      const xm = x + seg / 2; let a = base + 0.05 * (N(xm * 0.01, y * 0.03) - 0.5);
      if (glow) { const d = Math.hypot(xm - glow[0], y - glow[1]); a += glow[3] * Math.exp(-d * d / (glow[2] * glow[2])); }
      if (warm) a += warm[1] * Math.max(0, 1 - (warm[0] - y) / warm[2]);
      g.strokeStyle = warm && y > warm[0] - warm[2] ? mixCol(tint, warm[3], clamp(1 - (warm[0] - y) / warm[2])) : tint;
      g.globalAlpha = clamp(a); g.beginPath(); g.moveTo(x, y + (N(x * 0.01, y) - 0.5)); g.lineTo(x + seg, y + (N((x + seg) * 0.01, y) - 0.5)); g.stroke();
      x += seg + gap;
    }
  }
  g.restore();
}
function mixCol(a, b, k) { const pa = parseInt(a.slice(1), 16), pb = parseInt(b.slice(1), 16);
  const c = [16, 8, 0].map((s) => Math.round(((pa >> s) & 255) * (1 - k) + ((pb >> s) & 255) * k)); return `rgb(${c[0]},${c[1]},${c[2]})`; }
function stars(g, R, n, avoid) {
  g.save();
  for (let i = 0; i < n; i++) { const x = WIN.x0 + R() * (WIN.x1 - WIN.x0), y = WIN.y0 + R() * (HORIZON - 260 - WIN.y0);
    if (avoid && Math.hypot(x - avoid[0], y - avoid[1]) < avoid[2]) continue;
    const big = R() < 0.09, r = big ? 3.2 : 1.1 + R() * 1.8; g.globalAlpha = 0.55 + R() * 0.45; g.fillStyle = R() < 0.3 ? GOLD_HI : GOLD;
    g.beginPath(); g.arc(x, y, r, 0, Math.PI * 2); g.fill();
    if (big) { g.strokeStyle = GOLD_HI; g.lineWidth = 1.6; const l = 12 + R() * 14; g.beginPath(); g.moveTo(x - l, y); g.lineTo(x + l, y); g.moveTo(x, y - l); g.lineTo(x, y + l); g.stroke(); }
  }
  g.restore();
}
function sea(g, N, R, { y0, y1, rough = 0, glint = null, tint = GOLD, glintCol = '#e8743c' }) {
  g.save(); g.lineWidth = 1.9;
  for (let y = y0 + 6, i = 0; y < y1; y += 7.5 + (y - y0) * 0.014, i++) {
    const amp = (1.6 + (y - y0) * 0.005) * (1 + rough * 1.3), wl = 54 + R() * 46 + rough * 40, ph = R() * 10;
    let x = WIN.x0;
    while (x < WIN.x1) { const len = 30 + R() * 90; const xe = Math.min(WIN.x1, x + len);
      let a = 0.26 + 0.25 * (y - y0) / (y1 - y0); let col = tint;
      if (glint) { const d = Math.abs((x + xe) / 2 - glint[0]); const k = Math.exp(-d * d / (glint[1] * glint[1])); a += 0.6 * k; if (k > 0.25) col = glintCol; }
      g.globalAlpha = clamp(a); g.strokeStyle = col; g.beginPath();
      for (let xx = x; xx <= xe; xx += 4) { let yy = y + Math.sin(xx / wl * Math.PI * 2 + ph) * amp; if (rough) yy -= Math.pow(Math.max(0, Math.sin(xx / wl * Math.PI * 2 + ph)), 8) * amp * 1.4;
        xx === x ? g.moveTo(xx, yy) : g.lineTo(xx, yy); }
      g.stroke(); x = xe + (R() < 0.3 ? 8 + R() * 16 : 0); }
  }
  g.restore();
}
// the same cliff in every side view: the Fool's cliff
const CLIFF = [[96, 1690], [96, 1150], [150, 1142], [205, 1150], [262, 1138], [318, 1146], [372, 1135], [430, 1141], [488, 1131], [540, 1138], [566, 1150],
  [578, 1196], [560, 1262], [590, 1330], [570, 1410], [604, 1480], [590, 1560], [626, 1640], [640, 1690]];
function cliff(g, N, R, { tint = GOLD, lit = 0.5, warmCol = null }) {
  g.save(); g.beginPath(); CLIFF.forEach(([x, y], i) => (i ? g.lineTo(x, y) : g.moveTo(x, y))); g.closePath();
  g.fillStyle = '#040405'; g.fill(); g.clip();
  // rock strata following the face, then cross hatching (denser low down, away from the light)
  g.lineWidth = 1.6;
  for (let y = 1150; y < 1700; y += 9) { g.strokeStyle = tint; g.globalAlpha = 0.22 + lit * 0.3 * (1 - (y - 1150) / 600); g.beginPath();
    for (let x = 96; x <= 660; x += 8) { const yy = y + 10 * Math.sin(x / 70 + y / 40) + 6 * (N(x / 50, y / 30) - 0.5); x === 96 ? g.moveTo(x, yy) : g.lineTo(x, yy); } g.stroke(); }
  for (let k = -800; k < 800; k += 11) { g.strokeStyle = warmCol || tint; g.globalAlpha = 0.18 + (warmCol ? 0.16 : 0.06);
    g.beginPath(); g.moveTo(96 + k, 1150); g.lineTo(96 + k + 560, 1150 + 560 * 1.05); g.stroke(); }
  g.restore();
  // the edge outline, and grass along the top
  g.save(); g.strokeStyle = GOLD_HI; g.lineWidth = 3.4; g.globalAlpha = 0.9; g.beginPath(); CLIFF.slice(1, -1).forEach(([x, y], i) => (i ? g.lineTo(x, y) : g.moveTo(x, y))); g.stroke();
  g.strokeStyle = GOLD; g.lineWidth = 1.5;
  for (let i = 0; i < 160; i++) { const t = R(); const seg = Math.min(9, Math.floor(t * 10)); const [ax, ay] = CLIFF[1 + seg], [bx, by] = CLIFF[2 + seg]; const x = ax + (bx - ax) * R(), y = ay + (by - ay) * R();
    const h = 6 + R() * 16, lean = (R() - 0.5) * 8; g.globalAlpha = 0.5 + R() * 0.5; g.beginPath(); g.moveTo(x, y); g.quadraticCurveTo(x + lean * 0.3, y - h * 0.6, x + lean, y - h); g.stroke(); }
  g.restore();
}

// an engraved planet: curved latitude lines, shaded by line weight, cross hatching on the night side
function planet(g, N, R, cx, cy, r, { fillA, fillB, line, light = [-0.6, -0.55, 0.58], features = [], cap = true }) {
  const L = norm(light);
  g.save(); g.beginPath(); g.arc(cx, cy, r, 0, Math.PI * 2); g.clip();
  const gr = g.createRadialGradient(cx - r * 0.35, cy - r * 0.35, r * 0.1, cx, cy, r); gr.addColorStop(0, fillA); gr.addColorStop(1, fillB); g.fillStyle = gr; g.fillRect(cx - r, cy - r, r * 2, r * 2);
  for (const f of features) { g.fillStyle = f.col; g.globalAlpha = f.a; g.beginPath(); for (let k = 0; k <= 24; k++) { const a = k / 24 * Math.PI * 2, rr = f.r * (0.7 + 0.5 * N(Math.cos(a) * 2 + f.x, Math.sin(a) * 2 + f.y));
      const x = cx + f.x * r + Math.cos(a) * rr, y = cy + f.y * r + Math.sin(a) * rr * 0.7; k ? g.lineTo(x, y) : g.moveTo(x, y); } g.closePath(); g.fill(); }
  g.globalAlpha = 1;
  for (let k = -r + 4; k < r; k += 8.5) {               // latitude lines, bowed to show the tilt
    const y = cy + k, w = Math.sqrt(r * r - k * k);
    const segs = 28;
    for (let s = 0; s < segs; s++) {
      const u0 = s / segs, u1 = (s + 1) / segs;
      const p = (u) => { const x = cx - w + 2 * w * u; return [x, y + Math.sin(u * Math.PI) * w * 0.16]; };
      const [x0, y0] = p(u0), [x1, y1] = p(u1); const xm = (x0 + x1) / 2, ym = (y0 + y1) / 2;
      const nx = (xm - cx) / r, ny = (ym - cy) / r, nz = Math.sqrt(Math.max(0, 1 - nx * nx - ny * ny));
      const lit = clamp(nx * L[0] + ny * L[1] + nz * L[2]);
      g.strokeStyle = line; g.globalAlpha = 0.12 + 0.88 * lit; g.lineWidth = 1.2 + 2.4 * lit; g.beginPath(); g.moveTo(x0, y0); g.lineTo(x1, y1); g.stroke();
    }
  }
  g.lineWidth = 1.3;                                     // cross hatching where the light is gone
  for (let k = -2 * r; k < 2 * r; k += 10) { g.beginPath();
    for (let s = 0; s <= 40; s++) { const x = cx + k + s / 40 * r * 2 - r, y = cy - r + s / 40 * r * 2; const nx = (x - cx) / r, ny = (y - cy) / r; const q = 1 - nx * nx - ny * ny;
      const lit = q > 0 ? clamp(nx * L[0] + ny * L[1] + Math.sqrt(q) * L[2]) : 1; g.globalAlpha = lit < 0.32 ? 0.42 * (1 - lit / 0.32) : 0; g.strokeStyle = line;
      if (s) { g.lineTo(x, y); g.stroke(); } g.beginPath(); g.moveTo(x, y); } }
  if (cap) { g.globalAlpha = 0.42; g.fillStyle = GOLD_HI; g.beginPath(); g.ellipse(cx - r * 0.1, cy - r * 0.93, r * 0.2, r * 0.05, -0.12, 0, Math.PI * 2); g.fill();
    g.strokeStyle = '#ffffff'; g.lineWidth = 1; for (let k = 0; k < 3; k++) { g.globalAlpha = 0.35; g.beginPath(); g.ellipse(cx - r * 0.1, cy - r * 0.93, r * (0.18 - k * 0.05), r * (0.045 - k * 0.012), -0.12, 0, Math.PI * 2); g.stroke(); } }
  g.restore();
  g.save(); g.strokeStyle = GOLD_HI; g.lineWidth = 3.2; g.beginPath(); g.arc(cx, cy, r, 0, Math.PI * 2); g.stroke();
  g.strokeStyle = line; g.lineWidth = 10; g.globalAlpha = 0.14; g.beginPath(); g.arc(cx, cy, r + 9, 0, Math.PI * 2); g.stroke(); g.lineWidth = 6; g.globalAlpha = 0.08; g.beginPath(); g.arc(cx, cy, r + 20, 0, Math.PI * 2); g.stroke();
  g.restore();
}
const norm = (v) => { const l = Math.hypot(...v); return v.map((x) => x / l); };

// ---------------------------------------------------------------- the views
export function drawMars(seed = 11) {
  const c = canvas(), g = c.getContext('2d'), N = noise2(seed), R = rng(seed);
  obsidian(g, seed);
  g.save(); archPath(g); g.clip();
  g.fillStyle = '#050508'; g.fillRect(0, 0, TW, TH);
  const PX = 770, PY = 700, PR = 290;
  sky(g, N, { y0: WIN.y0, y1: HORIZON, step: 6, base: 0.13, glow: [PX, PY, 420, 0.22] });
  stars(g, R, 190, [PX, PY, PR + 40]);
  planet(g, N, R, PX, PY, PR, { fillA: '#c4512c', fillB: '#3a0f07', line: '#f0b06a', features: [{ x: 0.15, y: 0.05, r: 70, col: '#4a1408', a: 0.55 }, { x: -0.35, y: 0.3, r: 46, col: '#5a1a0a', a: 0.45 }, { x: 0.4, y: -0.3, r: 38, col: '#521608', a: 0.4 }] });
  g.strokeStyle = GOLD_HI; g.lineWidth = 2.4; g.globalAlpha = 0.9; g.beginPath(); g.moveTo(WIN.x0, HORIZON); g.lineTo(WIN.x1, HORIZON); g.stroke(); g.globalAlpha = 1;
  sea(g, N, R, { y0: HORIZON, y1: WIN.y1, glint: [PX, 70], glintCol: '#f08a50' });
  cliff(g, N, R, { lit: 0.55 });
  g.restore();
  frame(g, seed); titleBand(g, 'MARS', 128, '0');
  return c;
}

export function drawRagnarok(seed = 12) {
  const c = canvas(), g = c.getContext('2d'), N = noise2(seed), R = rng(seed);
  obsidian(g, seed);
  g.save(); archPath(g); g.clip();
  g.fillStyle = '#060405'; g.fillRect(0, 0, TW, TH);
  sky(g, N, { y0: WIN.y0, y1: HORIZON, step: 6, base: 0.12, warm: [HORIZON, 0.35, 420, '#ff7a32'] });
  // falling stars
  g.save(); for (let i = 0; i < 11; i++) { const x = 300 + R() * 760, y = 230 + R() * 520, l = 110 + R() * 190, a = 0.95 + R() * 0.25;
    const gr = g.createLinearGradient(x, y, x - Math.cos(a) * l, y - Math.sin(a) * l); gr.addColorStop(0, '#ffe2a0'); gr.addColorStop(0.25, '#ff9a4a'); gr.addColorStop(1, 'rgba(255,120,40,0)');
    g.strokeStyle = gr; g.lineWidth = 3 + R() * 2.4; g.beginPath(); g.moveTo(x, y); g.lineTo(x - Math.cos(a) * l, y - Math.sin(a) * l); g.stroke();
    g.fillStyle = '#fff1c8'; g.beginPath(); g.arc(x, y, 4.5, 0, Math.PI * 2); g.fill(); } g.restore();
  // the sun turns black
  const SX = 400, SY = 500, SR = 172;
  g.save(); for (let k = 0; k < 96; k++) { const a = k / 96 * Math.PI * 2, long = k % 2 === 0, l = long ? 150 + 30 * Math.sin(k * 1.7) : 70;
    g.strokeStyle = k % 4 === 0 ? GOLD_HI : GOLD; g.globalAlpha = long ? 0.85 : 0.6; g.lineWidth = long ? 3.4 : 2;
    g.beginPath(); g.moveTo(SX + Math.cos(a) * (SR + 10), SY + Math.sin(a) * (SR + 10)); g.lineTo(SX + Math.cos(a) * (SR + l), SY + Math.sin(a) * (SR + l)); g.stroke(); }
  g.globalAlpha = 1; g.strokeStyle = '#ffd27a'; g.lineWidth = 9; g.beginPath(); g.arc(SX, SY, SR, 0, Math.PI * 2); g.stroke();
  g.strokeStyle = GOLD_HI; g.lineWidth = 2; g.beginPath(); g.arc(SX, SY, SR + 16, 0, Math.PI * 2); g.stroke();
  g.fillStyle = '#000000'; g.beginPath(); g.arc(SX, SY, SR - 4, 0, Math.PI * 2); g.fill();
  g.strokeStyle = '#3a2410'; g.lineWidth = 1.2; for (let k = 0; k < 14; k++) { g.globalAlpha = 0.5; g.beginPath(); g.arc(SX, SY, SR - 14 - k * 11, 0, Math.PI * 2); g.stroke(); }
  g.restore();
  // smoke columns leaning away from the fire
  g.save(); g.lineWidth = 1.6;
  for (let i = 0; i < 7; i++) { const bx = 600 + i * 75 + (R() - 0.5) * 30; let x = bx, y = HORIZON - 150 - R() * 80;
    for (let k = 0; k < 7; k++) { const rr = 28 + k * 9 + R() * 10; g.strokeStyle = '#c99a6a'; g.globalAlpha = 0.3 - k * 0.03;
      g.beginPath(); g.arc(x, y, rr, Math.PI * 0.95, Math.PI * 2.05); g.stroke(); g.beginPath(); g.arc(x + rr * 0.7, y + rr * 0.15, rr * 0.7, Math.PI * 1.1, Math.PI * 1.95); g.stroke();
      x += 18 + R() * 10; y -= rr * 0.9; } }
  g.restore();
  // fire along the far shore: three layers of tongues, back to front
  g.save();
  const tongue = (x, base, h, w, lean) => { g.beginPath(); g.moveTo(x - w, base);
    g.bezierCurveTo(x - w * 1.05, base - h * 0.35, x - w * 0.2 + lean * 0.4, base - h * 0.62, x + lean, base - h);
    g.bezierCurveTo(x + lean * 0.5 + w * 0.25, base - h * 0.6, x + w * 1.05, base - h * 0.35, x + w, base); g.closePath(); };
  const layers = [[34, '#5e1206', '#8a1e08', 0.95, 1.25], [30, '#b8300e', '#ff6a1e', 0.9, 1.0], [22, '#ff7a24', '#ffd27a', 0.9, 0.55]];
  layers.forEach(([n, c0, c1, al, hk], li) => {
    for (let i = 0; i < n; i++) { const x = 500 + (i + R() * 0.8) * (620 / n), env = 0.55 + 0.45 * Math.sin(i / n * Math.PI * 2.2 + li) * Math.sin(i * 0.37 + 1.3);
      const h = (70 + R() * 150 + 160 * Math.max(0, env)) * hk, w = 12 + R() * 16 + (li === 0 ? 10 : 0), lean = (R() - 0.35) * h * 0.25, base = HORIZON + 2;
      const gr = g.createLinearGradient(0, base, 0, base - h); gr.addColorStop(0, c1); gr.addColorStop(0.55, c0); gr.addColorStop(1, 'rgba(90,14,4,0)');
      g.globalAlpha = al; g.fillStyle = gr; tongue(x, base, h, w, lean); g.fill();
      if (li === 1) { g.globalAlpha = 0.7; g.strokeStyle = GOLD_HI; g.lineWidth = 1.3; g.beginPath(); g.moveTo(x, base); g.bezierCurveTo(x - w * 0.3, base - h * 0.4, x + lean * 0.4, base - h * 0.65, x + lean * 0.9, base - h * 0.92); g.stroke(); } } });
  g.fillStyle = '#ffd9a0'; for (let i = 0; i < 70; i++) { g.globalAlpha = 0.4 + R() * 0.6; g.beginPath(); g.arc(520 + R() * 600, HORIZON - 120 - R() * 330, 1 + R() * 2.2, 0, Math.PI * 2); g.fill(); }
  g.restore();
  g.strokeStyle = '#ffb36a'; g.lineWidth = 2.4; g.globalAlpha = 0.9; g.beginPath(); g.moveTo(WIN.x0, HORIZON); g.lineTo(WIN.x1, HORIZON); g.stroke(); g.globalAlpha = 1;
  sea(g, N, R, { y0: HORIZON, y1: WIN.y1, rough: 1, glint: [830, 200], glintCol: '#ff7a32' });
  // the world serpent: coils of different sizes, dorsal spines, scales, white water where it breaks the surface
  g.save();
  const WL = 1350;
  const coils = [[630, 860, 1150, 1], [905, 1040, 1250, 0.75]];
  for (const [x0, x1, top, sc] of coils) {
    const P = (u) => { const mx = (x0 + x1) / 2, rx = (x1 - x0) / 2, h = WL - top; const a = Math.PI * (1 - u); return [mx + Math.cos(a) * rx, WL - Math.sin(a) * h]; };
    const path = new Path2D(); for (let k = 0; k <= 60; k++) { const [x, y] = P(k / 60); k ? path.lineTo(x, y) : path.moveTo(x, y); }
    const wd = 52 * sc;
    g.lineCap = 'butt'; g.strokeStyle = '#1c0703'; g.lineWidth = wd + 10; g.stroke(path);
    g.strokeStyle = '#8f3416'; g.lineWidth = wd; g.stroke(path);
    g.strokeStyle = '#c25a26'; g.lineWidth = wd * 0.45; g.globalAlpha = 0.8; g.save(); g.translate(0, wd * 0.22); g.stroke(path); g.restore(); g.globalAlpha = 1;
    for (let k = 2; k < 58; k += 2) { const [x, y] = P(k / 60), [xa, ya] = P((k + 1) / 60); const tx = xa - x, ty = ya - y, tl = Math.hypot(tx, ty); const nx = -ty / tl, ny = tx / tl;
      g.strokeStyle = GOLD_HI; g.globalAlpha = 0.65; g.lineWidth = 1.6; g.beginPath(); g.arc(x, y, wd * 0.32, Math.atan2(ny, nx) - 1.2, Math.atan2(ny, nx) + 1.2); g.stroke();
      if (k % 4 === 0) { g.globalAlpha = 1; g.fillStyle = GOLD; const sx = x - nx * wd * 0.55, sy = y - ny * wd * 0.55, sl = 26 * sc * (0.6 + 0.4 * Math.sin(k / 60 * Math.PI));
        g.beginPath(); g.moveTo(sx + tx / tl * 9, sy + ty / tl * 9); g.lineTo(sx - nx * sl, sy - ny * sl); g.lineTo(sx - tx / tl * 9, sy - ty / tl * 9); g.closePath(); g.fill(); } }
    g.globalAlpha = 1; g.strokeStyle = GOLD_HI; g.lineWidth = 2.4; g.save(); g.translate(0, -wd / 2); g.stroke(path); g.translate(0, wd); g.stroke(path); g.restore();
    for (const ex of [x0, x1]) { g.strokeStyle = '#f3e3c0'; g.lineWidth = 1.8; for (let k = 0; k < 9; k++) { const a = -Math.PI * (0.15 + k / 9 * 0.7); g.globalAlpha = 0.7;
      g.beginPath(); g.moveTo(ex + Math.cos(a) * 30, WL + Math.sin(a) * 10); g.lineTo(ex + Math.cos(a) * (60 + R() * 30), WL + Math.sin(a) * (40 + R() * 30)); g.stroke(); } }
    g.fillStyle = '#060405'; g.globalAlpha = 1; g.fillRect(x0 - 70, WL - 4, x1 - x0 + 140, 40);
  }
  sea(g, N, R, { y0: WL - 6, y1: WL + 46, rough: 1, glint: null });
  g.restore();
  cliff(g, N, R, { lit: 0.8, warmCol: '#ff8a3a' });
  g.restore();
  frame(g, seed); titleBand(g, 'RAGNARÖK', 104, '0');
  return c;
}

export function drawBack(seed = 21) {
  const c = canvas(), g = c.getContext('2d');
  obsidian(g, seed);
  g.save();
  g.strokeStyle = GOLD; g.lineWidth = 11; g.strokeRect(36, 36, TW - 72, TH - 72);
  g.strokeStyle = GOLD_HI; g.lineWidth = 2; g.strokeRect(50, 50, TW - 100, TH - 100);
  g.strokeStyle = GOLD; g.lineWidth = 3.5; g.strokeRect(64, 64, TW - 128, TH - 128);
  // a field of fine diagonal lines, banknote style
  g.save(); g.beginPath(); g.rect(64, 64, TW - 128, TH - 128); g.clip(); g.strokeStyle = GOLD; g.lineWidth = 1; g.globalAlpha = 0.16;
  for (let k = -TH; k < TW + TH; k += 14) { g.beginPath(); g.moveTo(k, 64); g.lineTo(k - TH, 64 + TH); g.stroke(); g.beginPath(); g.moveTo(k - TH, 64); g.lineTo(k, 64 + TH); g.stroke(); }
  g.restore();
  const cx = TW / 2, cy = TH / 2;
  g.fillStyle = OBS; g.beginPath(); g.arc(cx, cy, 500, 0, Math.PI * 2); g.fill();
  rosette(g, cx, cy, 372, 18, 44, 44, 1.1, 0.8);
  rosette(g, cx, cy, 236, 12, 36, 34, 1.1, 0.85, GOLD_HI);
  rosette(g, cx, cy, 128, 8, 28, 24, 1.0, 0.9);
  for (const r of [300, 168, 82]) { g.strokeStyle = GOLD_HI; g.lineWidth = 2.2; g.globalAlpha = 0.9; g.beginPath(); g.arc(cx, cy, r, 0, Math.PI * 2); g.stroke(); } g.globalAlpha = 1;
  g.strokeStyle = GOLD; g.lineWidth = 6; g.beginPath(); g.arc(cx, cy, 470, 0, Math.PI * 2); g.stroke();
  g.lineWidth = 2; g.strokeStyle = GOLD_HI; g.beginPath(); g.arc(cx, cy, 494, 0, Math.PI * 2); g.stroke(); g.beginPath(); g.arc(cx, cy, 452, 0, Math.PI * 2); g.stroke();
  g.fillStyle = GOLD; for (let k = 0; k < 72; k++) { const a = k / 72 * Math.PI * 2; g.save(); g.translate(cx + Math.cos(a) * 473, cy + Math.sin(a) * 473); g.rotate(a + Math.PI / 4); g.fillRect(-5, -5, 10, 10); g.restore(); }
  g.fillStyle = OBS; g.beginPath(); g.arc(cx, cy, 64, 0, Math.PI * 2); g.fill(); g.strokeStyle = GOLD_HI; g.lineWidth = 4; g.stroke();
  g.save(); g.translate(cx, cy); g.fillStyle = GOLD_HI; for (let k = 0; k < 8; k++) { g.rotate(Math.PI / 4); g.beginPath(); g.moveTo(0, -46 * (k % 2 ? 0.55 : 1)); g.lineTo(7, 0); g.lineTo(-7, 0); g.closePath(); g.fill(); } g.restore();
  for (const [x, y] of [[64, 64], [TW - 64, 64], [64, TH - 64], [TW - 64, TH - 64]]) { g.fillStyle = OBS; g.beginPath(); g.arc(x, y, 34, 0, Math.PI * 2); g.fill(); rosette(g, x, y, 22, 7, 10, 7, 1.2, 0.95); g.strokeStyle = GOLD; g.lineWidth = 3; g.beginPath(); g.arc(x, y, 31, 0, Math.PI * 2); g.stroke(); }
  for (const y of [190, TH - 190]) { g.save(); g.translate(cx, y); g.strokeStyle = GOLD; g.lineWidth = 2; for (let k = 0; k < 3; k++) { g.beginPath(); g.ellipse(0, 0, 240 - k * 60, 26 - k * 6, 0, 0, Math.PI * 2); g.stroke(); } g.restore(); }
  g.restore();
  return c;
}

// ---------------------------------------------------------------- materials and meshes
const TEXC = new Map();   // one texture per canvas or image, however many cards show it
function tex(c, maxAniso = 8) { if (TEXC.has(c)) return TEXC.get(c); const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = maxAniso; t.generateMipmaps = true; t.minFilter = THREE.LinearMipmapLinearFilter; TEXC.set(c, t); return t; }

// gold where the art is bright, glossy black glass elsewhere; `flip` 0..1 swaps view A for view B through the lenticules
function cardMaterial(mapA, mapB, env, { stripes = 150, rough = [0.24, 0.42], mapC = null } = {}) {
  const m = new THREE.MeshStandardMaterial({ map: mapA, envMap: env, envMapIntensity: 0.72, metalness: 1, roughness: 0.3 });
  m.userData.u = { mapB: { value: mapB || mapA }, mapC: { value: mapC || mapA }, uFlip: { value: 0 }, uFool: { value: 0 }, uStripes: { value: stripes }, uGlow: { value: new THREE.Color(0, 0, 0) } };
  m.onBeforeCompile = (sh) => {
    Object.assign(sh.uniforms, m.userData.u);
    sh.fragmentShader = sh.fragmentShader
      .replace('#include <common>', '#include <common>\nuniform sampler2D mapB, mapC; uniform float uFlip, uFool, uStripes; uniform vec3 uGlow; float goldK;')
      .replace('#include <map_fragment>', `
        float stp = fract(vMapUv.x * uStripes);
        float aa = clamp(fwidth(vMapUv.x * uStripes) * 1.2, 0.002, 0.5);
        float showB = 1.0 - smoothstep(uFlip - aa, uFlip + aa, stp);
        if (uFlip <= 0.0001) showB = 0.0; if (uFlip >= 0.9999) showB = 1.0;
        vec4 cA = texture2D(map, vMapUv), cB = texture2D(mapB, vMapUv);
        vec4 sampledDiffuseColor = mix(cA, cB, showB);
        if (uFool > 0.0001) { float st2 = fract(vMapUv.x * uStripes + 0.5); float showC = 1.0 - smoothstep(uFool - aa, uFool + aa, st2); if (uFool >= 0.9999) showC = 1.0;
          sampledDiffuseColor = mix(sampledDiffuseColor, texture2D(mapC, vMapUv), showC); }
        float lum = dot(sampledDiffuseColor.rgb, vec3(0.299, 0.587, 0.114));
        goldK = smoothstep(0.06, 0.32, lum);
        sampledDiffuseColor.rgb *= 0.92 + 0.08 * sin(stp * 6.2831);
        diffuseColor *= sampledDiffuseColor;`)
      .replace('#include <roughnessmap_fragment>', `float roughnessFactor = mix(${rough[0].toFixed(3)}, ${rough[1].toFixed(3)}, goldK);`)
      .replace('#include <lights_fragment_maps>', '#include <lights_fragment_maps>\n radiance *= mix(0.3, 1.0, goldK);')
      .replace('#include <metalnessmap_fragment>', 'float metalnessFactor = goldK;')
      .replace('#include <emissivemap_fragment>', '#include <emissivemap_fragment>\n totalEmissiveRadiance += uGlow * (0.25 + goldK);');
  };
  m.customProgramCacheKey = () => 'arcana' + rough.join('_') + (mapC ? 'C' : '');
  return m;
}
function edgeMaterial(env) {
  return new THREE.MeshStandardMaterial({ color: 0xd8b060, metalness: 1, roughness: 0.28, envMap: env, envMapIntensity: 1.2, emissive: 0x000000 });
}
function roundedShape(w, h, r) {
  const s = new THREE.Shape(); const x = -w / 2, y = -h / 2;
  s.moveTo(x + r, y); s.lineTo(x + w - r, y); s.quadraticCurveTo(x + w, y, x + w, y + r); s.lineTo(x + w, y + h - r); s.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
  s.lineTo(x + r, y + h); s.quadraticCurveTo(x, y + h, x, y + h - r); s.lineTo(x, y + r); s.quadraticCurveTo(x, y, x + r, y); return s;
}
function faceGeo(w, h, r, flipU = false) {
  const g = new THREE.ShapeGeometry(roundedShape(w, h, r), 6); const p = g.attributes.position, uv = g.attributes.uv;
  for (let i = 0; i < p.count; i++) { const u = (p.getX(i) + w / 2) / w, v = (p.getY(i) + h / 2) / h; uv.setXY(i, flipU ? 1 - u : u, v); }
  return g;
}
let SHARED = null;
function shared(env) {
  if (SHARED) return SHARED;
  const back = tex(drawBack());
  SHARED = { back, backMat: cardMaterial(back, null, env, { stripes: 0.0001, rough: [0.36, 0.6] }), edge: edgeMaterial(env),
    body: new THREE.ExtrudeGeometry(roundedShape(CW, CH, 0.0045), { depth: CD, bevelEnabled: true, bevelThickness: 0.00025, bevelSize: 0.00025, bevelSegments: 2, curveSegments: 6 }),
    front: faceGeo(CW, CH, 0.0045), rear: faceGeo(CW, CH, 0.0045, true) };
  SHARED.body.translate(0, 0, -CD / 2);
  return SHARED;
}
/** a card: face views [A, B] (canvas), facing +z. card.userData.setFlip(0..1), setGlow(color, k).
 *  A face-down deck card (views = null) shows its back on both sides; ownBack gives it its own back material so it can glow alone. */
export function makeCard(env, views = null, { ownBack = false } = {}) {
  const S = shared(env); const g = new THREE.Group();
  const body = new THREE.Mesh(S.body, S.edge.clone()); g.add(body);
  let backMat = S.backMat;
  if (ownBack) backMat = cardMaterial(S.back, null, env, { stripes: 0.0001, rough: [0.36, 0.6] });
  let front;
  if (views) { front = new THREE.Mesh(S.front, cardMaterial(tex(views[0]), views[1] ? tex(views[1]) : null, env, { mapC: views[2] ? tex(views[2]) : null })); }
  else front = new THREE.Mesh(S.rear, backMat);
  front.position.z = CD / 2 + 0.0003; g.add(front);
  const rear = new THREE.Mesh(S.rear, backMat); rear.rotation.y = Math.PI; rear.position.z = -CD / 2 - 0.0003; g.add(rear);
  g.userData.front = front; g.userData.body = body;
  g.userData.setFlip = (k) => { if (views && front.material.userData.u) front.material.userData.u.uFlip.value = clamp(k); };
  g.userData.setFool = (k) => { if (views && front.material.userData.u) front.material.userData.u.uFool.value = clamp(k); };
  g.userData.views = views;
  g.userData.setGlow = (col, k) => { body.material.emissive.copy(col).multiplyScalar(k);
    if (views && front.material.userData.u) front.material.userData.u.uGlow.value.copy(col).multiplyScalar(k * 0.25);
    if (ownBack && backMat.userData.u) backMat.userData.u.uGlow.value.copy(col).multiplyScalar(k * 0.9); };
  return g;
}
export const CARD = { W: CW, H: CH, D: CD };
export { cardMaterial };
export { canvas, obsidian, archPath, frame, titleBand, sky, stars, sea, cliff, planet, mixCol, rosette, tex, GOLD, GOLD_HI, GOLD_LO, OBS, WIN, HORIZON, TW, TH, CLIFF };
