// The rest of the deck, in the same engraved style as MARS / RAGNARÖK: gold line work on obsidian, one accent colour
// per card, the arched window, the numeral medallion and the title band. Classic numbering 0–XXI; new cards XXII+.
import { rng, clamp } from './lib.js';
import { noise2 } from './lib2.js';
import { canvas, obsidian, archPath, frame, titleBand, sky, stars, sea, cliff, planet, mixCol, GOLD, GOLD_HI, GOLD_LO, OBS, WIN, HORIZON, TW, TH, CLIFF } from './cards.js';

const DARK = '#07080c', TAU = Math.PI * 2;
export const ACCENT = { fool: '#ff8a3a', magician: '#9fd8ff', tower: '#ff7a2a', star: '#9cc8ff', sun: '#ffcf4a', robot: '#7fe0ff', red: '#d8512a', gardener: '#7fc46a' };

// ---------------------------------------------------------------- engraving primitives
export const poly = (pts) => { const p = new Path2D(); pts.forEach(([x, y], i) => (i ? p.lineTo(x, y) : p.moveTo(x, y))); p.closePath(); return p; };
function off(w, h) { const c = document.createElement('canvas'); c.width = w; c.height = h; return c; }
/** parallel hatching inside a path */
export function hatchIn(g, path, { ang = 0.9, step = 9, alpha = 0.32, col = GOLD, lw = 1.2 } = {}) {
  g.save(); g.clip(path); g.strokeStyle = col; g.globalAlpha = alpha; g.lineWidth = lw;
  const W = g.canvas.width, H = g.canvas.height, d = Math.hypot(W, H), ca = Math.cos(ang), sa = Math.sin(ang);
  for (let k = -d; k < d; k += step) { g.beginPath(); g.moveTo(W / 2 + ca * k - sa * d, H / 2 + sa * k + ca * d); g.lineTo(W / 2 + ca * k + sa * d, H / 2 + sa * k - ca * d); g.stroke(); }
  g.restore();
}
/** a filled, outlined, optionally hatched shape */
export function engrave(g, path, { fill = DARK, line = GOLD_HI, lw = 3, hatch = null, alpha = 1 } = {}) {
  g.save(); g.globalAlpha = alpha; if (fill) { g.fillStyle = fill; g.fill(path); } g.restore();
  if (hatch) hatchIn(g, path, hatch);
  if (line) { g.save(); g.globalAlpha = alpha; g.strokeStyle = line; g.lineWidth = lw; g.lineJoin = 'round'; g.stroke(path); g.restore(); }
}
/** a figure made of polygons, limbs and ellipses, merged into one silhouette with a gold outline and inner hatching.
 *  parts: {poly:[[x,y]...]} | {limb:[[x,y]...], w} | {ell:[x,y,rx,ry,rot]} ; extra(g) draws details on top */
export function silhouette(g, parts, { line = GOLD_HI, lw = 3.2, fill = null, hatch = { ang: 0.9, step: 7, alpha: 0.5 }, extra = null, rim = true } = {}) {
  const W = g.canvas.width, H = g.canvas.height;
  let y0 = 1e9, y1 = -1e9; for (const p of parts) for (const [x, y] of (p.poly || p.limb || [[p.ell[0], p.ell[1] - p.ell[3]], [p.ell[0], p.ell[1] + p.ell[3]]])) { y0 = Math.min(y0, y); y1 = Math.max(y1, y); }
  if (!fill) { fill = g.createLinearGradient(0, y0, 0, y1); fill.addColorStop(0, '#2a2116'); fill.addColorStop(0.5, '#130f0b'); fill.addColorStop(1, '#07080c'); }
  if (hatch && hatch.alpha < 0.45) hatch = { ...hatch, alpha: Math.min(0.62, hatch.alpha * 1.7) };
  const draw = (c, col, grow) => { c.fillStyle = col; c.strokeStyle = col; c.lineJoin = 'round'; c.lineCap = 'round';
    for (const p of parts) {
      if (p.poly) { const pa = poly(p.poly); c.fill(pa); if (grow) { c.lineWidth = grow * 2; c.stroke(pa); } }
      else if (p.limb) { c.lineWidth = p.w + grow * 2; c.beginPath(); p.limb.forEach(([x, y], i) => (i ? c.lineTo(x, y) : c.moveTo(x, y))); c.stroke(); }
      else if (p.ell) { const [x, y, rx, ry, rot = 0] = p.ell; c.beginPath(); c.ellipse(x, y, rx + grow, ry + grow, rot, 0, TAU); c.fill(); }
    } };
  draw(g, line, lw); draw(g, fill, 0);
  if (hatch) { const m = off(W, H), mg = m.getContext('2d'); draw(mg, '#fff', 0);
    const h = off(W, H), hg = h.getContext('2d'); hg.strokeStyle = hatch.col || GOLD; hg.globalAlpha = hatch.alpha; hg.lineWidth = hatch.lw || 1.2;
    const d = Math.hypot(W, H), ca = Math.cos(hatch.ang), sa = Math.sin(hatch.ang);
    for (let k = -d; k < d; k += hatch.step) { hg.beginPath(); hg.moveTo(W / 2 + ca * k - sa * d, H / 2 + sa * k + ca * d); hg.lineTo(W / 2 + ca * k + sa * d, H / 2 + sa * k - ca * d); hg.stroke(); }
    hg.globalAlpha = 1; hg.globalCompositeOperation = 'destination-in'; hg.drawImage(m, 0, 0); g.drawImage(h, 0, 0);
    if (rim) {   // rim light: the mask shifted down-right, cut from the mask, leaves a thin bright edge on the top-left
      const r2 = off(W, H), rg = r2.getContext('2d'); rg.drawImage(m, 0, 0); rg.globalCompositeOperation = 'destination-out'; rg.drawImage(m, 5, 6);
      rg.globalCompositeOperation = 'source-in'; rg.fillStyle = GOLD_HI; rg.fillRect(0, 0, W, H); g.save(); g.globalAlpha = 0.75; g.drawImage(r2, 0, 0); g.restore(); } }
  if (extra) { g.save(); extra(g); g.restore(); }
}
export function line(g, pts, col = GOLD_HI, lw = 2, alpha = 1) { g.save(); g.strokeStyle = col; g.lineWidth = lw; g.globalAlpha = alpha; g.lineCap = 'round'; g.lineJoin = 'round'; g.beginPath(); pts.forEach(([x, y], i) => (i ? g.lineTo(x, y) : g.moveTo(x, y))); g.stroke(); g.restore(); }
export function dot(g, x, y, r, col = GOLD_HI, alpha = 1) { g.save(); g.globalAlpha = alpha; g.fillStyle = col; g.beginPath(); g.arc(x, y, r, 0, TAU); g.fill(); g.restore(); }
export function glow(g, x, y, r, col, a = 0.5) { g.save(); const gr = g.createRadialGradient(x, y, 0, x, y, r); gr.addColorStop(0, col); gr.addColorStop(1, 'rgba(0,0,0,0)'); g.globalAlpha = a; g.fillStyle = gr; g.fillRect(x - r, y - r, 2 * r, 2 * r); g.restore(); }
/** an eight-pointed engraved star */
export function star8(g, x, y, r, { col = GOLD_HI, inner = 0.22, alt = 0.55, rot = 0, fill = true, lw = 2 } = {}) {
  const pts = []; for (let k = 0; k < 16; k++) { const a = rot + k / 16 * TAU - Math.PI / 2; const rr = k % 2 === 0 ? (k % 4 === 0 ? r : r * alt) : r * inner; pts.push([x + Math.cos(a) * rr, y + Math.sin(a) * rr]); }
  const p = poly(pts); g.save(); if (fill) { g.fillStyle = col; g.fill(p); } g.strokeStyle = col; g.lineWidth = lw; g.stroke(p);
  g.strokeStyle = DARK; g.lineWidth = 1; for (let k = 0; k < 8; k++) { const a = rot + k / 8 * TAU - Math.PI / 2; g.globalAlpha = 0.6; g.beginPath(); g.moveTo(x, y); g.lineTo(x + Math.cos(a) * r * (k % 2 ? alt : 1) * 0.9, y + Math.sin(a) * r * (k % 2 ? alt : 1) * 0.9); g.stroke(); }
  g.restore();
}
/** an engraved storm cloud: a few big billows, dense wavy line shading, bright top edges */
export function cloud(g, x, y, w, h, R, { col = GOLD, alpha = 0.6, fill = '#0a0a0e' } = {}) {
  const n = 4 + Math.floor(R() * 3), p = new Path2D(), bil = [];
  for (let k = 0; k < n; k++) { const bx = x - w / 2 + (k + 0.5) / n * w + (R() - 0.5) * w * 0.06, br = h * (0.45 + 0.55 * Math.sin((k + 0.5) / n * Math.PI)) * (0.85 + 0.3 * R()); bil.push([bx, y - br * 0.35, br]); p.moveTo(bx + br, y - br * 0.35); p.arc(bx, y - br * 0.35, br, 0, TAU); }
  p.rect(x - w / 2, y - h * 0.3, w, h * 0.5);
  g.save(); g.fillStyle = fill; g.fill(p); g.clip(p); g.strokeStyle = col; g.lineWidth = 1.3;
  for (let yy = y - h * 1.6; yy < y + h * 0.4; yy += 5) { g.globalAlpha = alpha * (0.25 + 0.55 * (yy - (y - h * 1.6)) / (h * 2)); g.beginPath(); g.moveTo(x - w / 2, yy);
    for (let xx = x - w / 2; xx <= x + w / 2; xx += 10) g.lineTo(xx, yy + Math.sin(xx / 34 + yy / 11) * 2.6); g.stroke(); }
  g.restore();
  g.save(); g.strokeStyle = GOLD_HI; g.lineWidth = 2.4; g.globalAlpha = alpha; for (const [bx, by, br] of bil) { g.beginPath(); g.arc(bx, by, br, Math.PI * 1.08, Math.PI * 1.92); g.stroke(); }
  g.lineWidth = 1.4; g.globalAlpha = alpha * 0.7; for (const [bx, by, br] of bil) { g.beginPath(); g.arc(bx - br * 0.15, by + br * 0.1, br * 0.55, Math.PI * 1.15, Math.PI * 1.8); g.stroke(); }
  g.restore();
}
/** a jagged lightning bolt from p0 to p1 */
export function bolt(g, x0, y0, x1, y1, R, { col = '#eaf4ff', glowCol = '#9fd8ff', w = 5, branches = 2 } = {}) {
  const pts = [[x0, y0]]; const n = 9; for (let k = 1; k < n; k++) { const t = k / n; pts.push([x0 + (x1 - x0) * t + (R() - 0.5) * 70, y0 + (y1 - y0) * t + (R() - 0.5) * 20]); } pts.push([x1, y1]);
  g.save(); g.lineJoin = 'miter'; g.strokeStyle = glowCol; g.globalAlpha = 0.25; g.lineWidth = w * 5; g.beginPath(); pts.forEach(([x, y], i) => (i ? g.lineTo(x, y) : g.moveTo(x, y))); g.stroke();
  g.globalAlpha = 1; g.strokeStyle = col; g.lineWidth = w; g.stroke(); g.restore();
  for (let b = 0; b < branches; b++) { const i = 2 + Math.floor(R() * (n - 4)); const [bx, by] = pts[i]; const dx = (x1 - x0) * 0.25 + (R() - 0.5) * 160, dy = (y1 - y0) * 0.18;
    line(g, [[bx, by], [bx + dx * 0.4 + (R() - 0.5) * 30, by + dy * 0.5], [bx + dx, by + dy]], col, w * 0.45, 0.9); }
  return pts;
}
/** fire tongues along a base line */
export function flames(g, x0, x1, base, R, { n = 26, h0 = 60, h1 = 220, cols = [['#5e1206', '#8a1e08'], ['#b8300e', '#ff6a1e'], ['#ff7a24', '#ffd27a']], lean = 0.25 } = {}) {
  const tongue = (x, b, h, w, ln) => { g.beginPath(); g.moveTo(x - w, b); g.bezierCurveTo(x - w * 1.05, b - h * 0.35, x - w * 0.2 + ln * 0.4, b - h * 0.62, x + ln, b - h);
    g.bezierCurveTo(x + ln * 0.5 + w * 0.25, b - h * 0.6, x + w * 1.05, b - h * 0.35, x + w, b); g.closePath(); };
  g.save();
  cols.forEach(([c0, c1], li) => { const hk = [1.25, 1.0, 0.55][li] || 1;
    for (let i = 0; i < n; i++) { const x = x0 + (i + R() * 0.8) * ((x1 - x0) / n); const h = (h0 + R() * (h1 - h0)) * hk, w = 10 + R() * 14 + (li === 0 ? 8 : 0), ln = (R() - 0.35) * h * lean;
      const gr = g.createLinearGradient(0, base, 0, base - h); gr.addColorStop(0, c1); gr.addColorStop(0.55, c0); gr.addColorStop(1, 'rgba(90,14,4,0)');
      g.globalAlpha = 0.9; g.fillStyle = gr; tongue(x, base, h, w, ln); g.fill();
      if (li === 1) { g.globalAlpha = 0.6; g.strokeStyle = GOLD_HI; g.lineWidth = 1.2; g.beginPath(); g.moveTo(x, base); g.bezierCurveTo(x - w * 0.3, base - h * 0.4, x + ln * 0.4, base - h * 0.65, x + ln * 0.9, base - h * 0.92); g.stroke(); } } });
  g.restore();
}
/** radiating rays from a point (an engraved glory) */
export function rays(g, x, y, r0, r1, n, { col = GOLD, alpha = 0.35, lw = 1.5, wav = 0 } = {}) {
  g.save(); g.strokeStyle = col; g.lineWidth = lw;
  for (let k = 0; k < n; k++) { const a = k / n * TAU; g.globalAlpha = alpha * (k % 2 ? 0.6 : 1); g.beginPath();
    if (wav && k % 2) { for (let s = 0; s <= 20; s++) { const rr = r0 + (r1 * 0.8 - r0) * s / 20, aa = a + Math.sin(s / 20 * Math.PI * 3) * wav; const px = x + Math.cos(aa) * rr, py = y + Math.sin(aa) * rr; s ? g.lineTo(px, py) : g.moveTo(px, py); } }
    else { g.moveTo(x + Math.cos(a) * r0, y + Math.sin(a) * r0); g.lineTo(x + Math.cos(a) * r1, y + Math.sin(a) * r1); }
    g.stroke(); }
  g.restore();
}

// ---------------------------------------------------------------- characters, engraved
/** the man with the rocket (stepping right, chin up, rocket over his shoulder): feet at fx,fy; scale s (1 = 400 px tall) */
export function foolFigure(g, fx, fy, s = 1, { rocketCol = '#d9dde3', turn = 0 } = {}) {
  const P = (x, y) => [fx + x * s, fy + y * s];
  // the rocket first, behind the head: tail low-left, nose high-right, resting on the far shoulder
  const t0 = P(-118, -148), t1 = P(150, -455); const ang = Math.atan2(t1[1] - t0[1], t1[0] - t0[0]); const len = Math.hypot(t1[0] - t0[0], t1[1] - t0[1]);
  g.save(); g.translate(t0[0], t0[1]); g.rotate(ang);
  const r = 17 * s; const body = new Path2D(); body.moveTo(0, -r); body.lineTo(len * 0.8, -r); body.quadraticCurveTo(len, -r * 0.8, len, 0); body.quadraticCurveTo(len, r * 0.8, len * 0.8, r); body.lineTo(0, r); body.closePath();
  const gr = g.createLinearGradient(0, -r, 0, r); gr.addColorStop(0, '#f4f6f8'); gr.addColorStop(0.45, rocketCol); gr.addColorStop(1, '#5a5e66'); g.fillStyle = gr; g.fill(body);
  g.strokeStyle = GOLD_HI; g.lineWidth = 2.6 * s; g.stroke(body);
  g.fillStyle = '#16171a'; g.beginPath(); g.moveTo(len * 0.05, r); g.lineTo(len * 0.8, r); g.quadraticCurveTo(len * 0.97, r * 0.75, len * 0.99, r * 0.25); g.lineTo(len * 0.05, r * 0.3); g.closePath(); g.fill();   // tiles on the belly
  for (const fxp of [0.02, 0.72]) { const fl = poly([[len * fxp, -r], [len * fxp + 34 * s, -r - 26 * s], [len * fxp + 52 * s, -r - 22 * s], [len * fxp + 46 * s, -r]]); g.fillStyle = '#2a2b2e'; g.fill(fl); g.strokeStyle = GOLD; g.lineWidth = 1.6 * s; g.stroke(fl); }
  g.strokeStyle = 'rgba(30,30,34,0.6)'; g.lineWidth = 1.2 * s; for (let k = 1; k < 7; k++) { g.beginPath(); g.moveTo(len * k / 8, -r); g.lineTo(len * k / 8, r); g.stroke(); }
  g.fillStyle = '#2a2b2e'; g.fillRect(-6 * s, -r * 0.8, 8 * s, r * 1.6);
  g.restore();
  // the man: blazer over a tee, swept-back hair, chin up; near arm grips the rocket
  silhouette(g, [
    { limb: [P(-30, -118), P(-58, -60), P(-92, -6)], w: 30 * s },                 // back leg
    { limb: [P(10, -118), P(26, -62), P(6, -4)], w: 30 * s },                    // front leg, stepping
    { limb: [P(-92, -6), P(-62, -2)], w: 20 * s }, { limb: [P(6, -4), P(40, -2)], w: 20 * s },   // shoes
    { poly: [P(-62, -322), P(30, -326), P(44, -260), P(30, -168), P(36, -118), P(-50, -112), P(-44, -170), P(-58, -262)] },   // blazer
    { limb: [P(-12, -330), P(-6, -350)], w: 30 * s },                             // neck
    { ell: [...P(-2, -392), 38 * s, 46 * s, -0.25] },                             // head
    { ell: [...P(-30, -416), 34 * s, 30 * s, -0.5] },                             // swept hair volume
    { limb: [P(-50, -310), P(-40, -238), P(36, -300), P(88, -350)], w: 25 * s }, // near arm up to the rocket
  ], { hatch: { ang: 0.95, step: 7 * s, alpha: 0.3 }, extra: (c) => {
    line(c, [P(-8, -320), P(-14, -262), P(-6, -200)], GOLD, 2 * s, 0.8);                       // lapel
    line(c, [P(4, -322), P(14, -270)], GOLD, 2 * s, 0.8);
    line(c, [P(-6, -270), P(6, -200)], '#121214', 6 * s, 0.9);                               // the tee in the V
    const tx = -16 * turn;                                                                    // turn: the head comes round toward us
    line(c, [P(10 + tx, -404 + 3 * turn), P(26 + tx, -398 + 3 * turn)], GOLD_HI, 2 * s, 0.9);    // brow
    dot(c, ...P(20 + tx, -388 + 3 * turn), 3 * s, GOLD_HI, 0.9);                             // eye, looking up and out
    if (turn > 0) { line(c, [P(-20 + tx * 0.6, -402), P(-8 + tx * 0.6, -400)], GOLD_HI, 2 * s, 0.75 * turn); dot(c, ...P(-14 + tx * 0.6, -389), 3 * s, GOLD_HI, 0.85 * turn); }   // the far eye
    line(c, [P(14 + tx, -360 + 2 * turn), P(30 + tx, -364 + 2 * turn)], GOLD_HI, 2 * s, 0.8);  // a smile
    for (let k = 0; k < 6; k++) line(c, [P(-56 + k * 6, -408 + k * 3), P(-10 + k * 6, -436 + k * 5)], GOLD, 1.4 * s, 0.7);   // hair combed back
  } });
}
/** a small robot (the Fool's dog), feet at x,y */
export function robotFig(g, x, y, s = 1, { eye = ACCENT.robot, pose = 'stand', arm = null } = {}) {
  const P = (a, b) => [x + a * s, y + b * s];
  const parts = [
    { limb: [P(-12, -40), P(-14, 0)], w: 12 * s }, { limb: [P(12, -40), P(14, 0)], w: 12 * s },
    { poly: [P(-24, -92), P(24, -92), P(28, -42), P(-28, -42)] },
    { ell: [...P(0, -112), 22 * s, 19 * s, 0] },
    { limb: arm ? [P(-24, -86), ...arm.map(([a, b]) => P(a, b))] : [P(-26, -86), P(-34, -60), P(-30, -40)], w: 9 * s },
    { limb: [P(26, -86), P(36, -62), P(32, -44)], w: 9 * s },
  ];
  silhouette(g, parts, { lw: 2.6 * s, hatch: { ang: 0.7, step: 6 * s, alpha: 0.25 }, extra: (c) => {
    line(c, [P(-15, -114), P(15, -114)], eye, 4.5 * s, 1); glow(c, ...P(0, -114), 22 * s, eye, 0.35);
    line(c, [P(-14, -74), P(14, -74)], GOLD, 1.4 * s, 0.7); line(c, [P(-14, -62), P(14, -62)], GOLD, 1.4 * s, 0.7);
  } });
}
/** a Viking: seated, standing, kneeling or reclining (mostly beard and cloak), feet at x,y */
export function vikingFig(g, x, y, s = 1, { pose = 'stand', facing = 1, helmet = true, holding = null } = {}) {
  const P = (a, b) => [x + a * s * facing, y + b * s];
  let parts;
  if (pose === 'recline') parts = [
    { limb: [P(-60, -30), P(20, -26), P(70, -40)], w: 26 * s }, { poly: [P(-120, -40), P(-60, -60), P(-40, -24), P(-110, -10)] },
    { ell: [...P(-128, -78), 26 * s, 28 * s, 0] }, { poly: [P(-150, -70), P(-108, -66), P(-118, -30)] },
    { limb: [P(-90, -56), P(-60, -90), P(-40, -108)], w: 16 * s } ];
  else if (pose === 'kneel') parts = [
    { limb: [P(-20, -60), P(-52, -24), P(-8, -4)], w: 26 * s }, { limb: [P(10, -64), P(40, -60), P(36, -2)], w: 26 * s },
    { poly: [P(-36, -160), P(30, -164), P(40, -60), P(-40, -56)] }, { ell: [...P(-2, -192), 26 * s, 30 * s, 0] },
    { poly: [P(-26, -186), P(24, -186), P(14, -126), P(-2, -112), P(-18, -128)] } ];
  else parts = [
    { limb: [P(-14, -96), P(-18, 0)], w: 24 * s }, { limb: [P(14, -96), P(18, 0)], w: 24 * s },
    { poly: [P(-40, -230), P(38, -232), P(46, -96), P(-46, -94)] }, { ell: [...P(0, -262), 26 * s, 30 * s, 0] },
    { poly: [P(-24, -256), P(24, -256), P(14, -188), P(0, -172), P(-14, -188)] } ];
  if (holding) parts.push({ limb: holding.map(([a, b]) => P(a, b)), w: 15 * s });
  silhouette(g, parts, { lw: 2.8 * s, hatch: { ang: 0.85, step: 7 * s, alpha: 0.3 }, extra: (c) => {
    if (helmet && pose !== 'recline') { const hy = pose === 'kneel' ? -192 : -262; const hp = new Path2D(); const [hx, hyy] = P(0, hy - 6); hp.arc(hx, hyy, 27 * s, Math.PI, TAU); hp.closePath();
      c.fillStyle = '#8a8e95'; c.fill(hp); c.strokeStyle = GOLD_HI; c.lineWidth = 2 * s; c.stroke(hp); line(c, [P(0, hy - 32), P(0, hy + 4)], GOLD_HI, 2.4 * s, 0.9); }
    const by = pose === 'kneel' ? -170 : pose === 'recline' ? -60 : -240;
    for (let k = -2; k <= 2; k++) line(c, [P(k * 6, by), P(k * 4, by + 50)], GOLD, 1.3 * s, 0.6);
  } });
}
/** a longship side view: hull from x0 to x1 at waterline y, dragon prow toward `dir` */
export function longship(g, x0, x1, y, R, { dir = 1, sail = true, sailCols = ['#8a1c14', '#d8c08a'], oars = 8, shields = true, scale = 1, rowers = null } = {}) {
  const L = x1 - x0, h = 46 * scale, mid = (x0 + x1) / 2;
  const hull = new Path2D(); hull.moveTo(x0, y - h * 1.6); hull.quadraticCurveTo(x0 + L * 0.08, y + h * 0.2, x0 + L * 0.3, y + h * 0.35);
  hull.lineTo(x1 - L * 0.3, y + h * 0.35); hull.quadraticCurveTo(x1 - L * 0.08, y + h * 0.2, x1, y - h * 1.6); hull.quadraticCurveTo(x1 - L * 0.06, y - h * 0.4, x1 - L * 0.15, y - h * 0.5);
  hull.lineTo(x0 + L * 0.15, y - h * 0.5); hull.quadraticCurveTo(x0 + L * 0.06, y - h * 0.4, x0, y - h * 1.6); hull.closePath();
  if (sail) { const mast = new Path2D(); mast.rect(mid - 3 * scale, y - h * 6.2, 6 * scale, h * 5.8); g.fillStyle = DARK; g.fill(mast); g.strokeStyle = GOLD; g.lineWidth = 1.5; g.stroke(mast);
    const sw = L * 0.36, sh = h * 4; const sp = new Path2D(); sp.moveTo(mid - sw / 2, y - h * 6); sp.lineTo(mid + sw / 2, y - h * 6); sp.quadraticCurveTo(mid + sw / 2 + 12 * dir, y - h * 4, mid + sw / 2, y - h * 2); sp.lineTo(mid - sw / 2, y - h * 2); sp.quadraticCurveTo(mid - sw / 2 + 12 * dir, y - h * 4, mid - sw / 2, y - h * 6); sp.closePath();
    g.save(); g.clip(sp); for (let k = 0; k < 7; k++) { g.fillStyle = sailCols[k % 2]; g.globalAlpha = 0.9; g.fillRect(mid - sw / 2 + k * sw / 7 - 2, y - h * 6.2, sw / 7 + 4, h * 4.4); } g.restore();
    hatchIn(g, sp, { ang: 0.5, step: 7, alpha: 0.25 }); g.strokeStyle = GOLD_HI; g.lineWidth = 2.4; g.stroke(sp); }
  if (rowers) rowers(hull, h);
  for (let k = 0; k < oars; k++) { const ox = x0 + L * (0.2 + 0.6 * k / Math.max(1, oars - 1)); line(g, [[ox, y - h * 0.3], [ox - 40 * dir * scale, y + h * 1.4]], GOLD, 3 * scale, 0.9); }
  engrave(g, hull, { fill: '#0b0806', lw: 3, hatch: { ang: 0.15, step: 6, alpha: 0.28 } });
  line(g, [[x0 + L * 0.06, y - h * 0.62], [x1 - L * 0.06, y - h * 0.62]], GOLD, 1.6, 0.8);
  if (shields) for (let k = 0; k < 9; k++) { const sx = x0 + L * (0.18 + 0.64 * k / 8); g.save(); g.fillStyle = k % 2 ? '#8a1c14' : '#d8b84a'; g.beginPath(); g.arc(sx, y - h * 0.5, 13 * scale, 0, TAU); g.fill(); g.strokeStyle = GOLD_HI; g.lineWidth = 1.6; g.stroke(); dot(g, sx, y - h * 0.5, 3 * scale, GOLD_HI); g.restore(); }
  // dragon head at the prow
  const px = dir > 0 ? x1 : x0, py = y - h * 1.6; const hd = poly([[px, py], [px + 26 * dir * scale, py - 18 * scale], [px + 40 * dir * scale, py - 10 * scale], [px + 22 * dir * scale, py + 4 * scale], [px + 6 * dir * scale, py + 14 * scale]]);
  engrave(g, hd, { fill: '#0b0806', lw: 2.4 }); dot(g, px + 22 * dir * scale, py - 10 * scale, 2.4 * scale, ACCENT.fool);
}
/** a skyline of glass towers with lit windows; returns window centres */
export function skyline(g, x0, x1, base, R, { maxH = 420, lit = 0.35, winCol = GOLD_HI } = {}) {
  const wins = []; let x = x0;
  while (x < x1) { const w = 40 + R() * 70, h = 90 + R() * maxH * (0.4 + 0.6 * Math.sin((x - x0) / (x1 - x0) * Math.PI)); const top = base - h;
    const b = new Path2D(); b.rect(x, top, w, h); engrave(g, b, { fill: '#05070b', lw: 1.8, hatch: { ang: 1.4, step: 6, alpha: 0.2 } });
    if (R() < 0.4) line(g, [[x + w / 2, top], [x + w / 2, top - 30 - R() * 40]], GOLD, 1.6, 0.8);
    for (let yy = top + 12; yy < base - 10; yy += 16) for (let xx = x + 8; xx < x + w - 8; xx += 13) { const on = R() < lit; wins.push([xx + 3, yy + 4, on]); if (on) { g.fillStyle = winCol; g.globalAlpha = 0.85; g.fillRect(xx, yy, 6, 8); g.globalAlpha = 1; } }
    x += w + 2; }
  return wins;
}

// ---------------------------------------------------------------- the faces
function base(seed) { const c = canvas(), g = c.getContext('2d'); obsidian(g, seed); return [c, g, noise2(seed), rng(seed)]; }
function windowStart(g, col = '#050508') { g.save(); archPath(g); g.clip(); g.fillStyle = col; g.fillRect(0, 0, TW, TH); }

/** 0 · THE FOOL — the centre view of the two-faced card: the same cliff; behind him the world burns, ahead is Mars */
export function drawFool(seed = 13, { turn = 0 } = {}) {
  const [c, g, N, R] = base(seed); windowStart(g);
  sky(g, N, { y0: WIN.y0, y1: HORIZON, step: 6, base: 0.13, glow: [880, 560, 380, 0.2], warm: [HORIZON, 0.3, 360, '#ff7a32'] });
  glow(g, 230, 980, 420, 'rgba(255,110,40,1)', 0.22);
  stars(g, R, 120, [880, 560, 230]);
  // behind him: a black sun low over the burning land
  const SX = 270, SY = 560, SR = 74; g.save(); for (let k = 0; k < 48; k++) { const a = k / 48 * TAU, l = k % 2 ? 40 : 80; g.strokeStyle = GOLD; g.globalAlpha = 0.6; g.lineWidth = 2; g.beginPath(); g.moveTo(SX + Math.cos(a) * (SR + 8), SY + Math.sin(a) * (SR + 8)); g.lineTo(SX + Math.cos(a) * (SR + l), SY + Math.sin(a) * (SR + l)); g.stroke(); }
  g.globalAlpha = 1; g.fillStyle = '#000'; g.beginPath(); g.arc(SX, SY, SR, 0, TAU); g.fill(); g.strokeStyle = '#ffd27a'; g.lineWidth = 5; g.stroke(); g.restore();
  // ahead: Mars over the sea
  planet(g, N, R, 880, 560, 150, { fillA: '#c4512c', fillB: '#3a0f07', line: '#f0b06a', features: [{ x: 0.1, y: 0.1, r: 40, col: '#4a1408', a: 0.55 }, { x: -0.3, y: -0.2, r: 26, col: '#5a1a0a', a: 0.45 }] });
  g.strokeStyle = GOLD_HI; g.lineWidth = 2.4; g.globalAlpha = 0.9; g.beginPath(); g.moveTo(WIN.x0, HORIZON); g.lineTo(WIN.x1, HORIZON); g.stroke(); g.globalAlpha = 1;
  sea(g, N, R, { y0: HORIZON, y1: WIN.y1, glint: [880, 80], glintCol: '#f08a50' });
  flames(g, 110, 470, 1136, R, { n: 18, h0: 30, h1: 120 });           // the burning world behind him, on the land
  cliff(g, N, R, { lit: 0.7, warmCol: '#ff8a3a' });
  robotFig(g, 400, 1142, 1.15, { arm: [[-6, -60], [44, -70]] });     // the little robot at his heel, tugging
  foolFigure(g, 520, 1136, 1.1, { turn });
  g.restore();
  frame(g, seed); titleBand(g, 'THE FOOL', 118, '0');
  return c;
}

/** I · THE MAGICIAN — one hand to the sky, one to the table: as above, so below; the four tools of the deck before him */
export function drawMagician(seed = 31) {
  const [c, g, N, R] = base(seed); windowStart(g);
  sky(g, N, { y0: WIN.y0, y1: 1250, step: 7, base: 0.1, glow: [600, 420, 340, 0.3] });
  rays(g, 600, 640, 120, 620, 72, { alpha: 0.22 });
  stars(g, R, 70, [600, 640, 300]);
  // the lemniscate
  g.save(); g.strokeStyle = ACCENT.magician; g.lineWidth = 10; g.globalAlpha = 0.25; const inf = new Path2D();
  for (let k = 0; k <= 200; k++) { const a = k / 200 * TAU; const d = 1 + Math.sin(a) ** 2; const x = 600 + 150 * Math.cos(a) / d, y = 330 + 150 * Math.sin(a) * Math.cos(a) / d; k ? inf.lineTo(x, y) : inf.moveTo(x, y); }
  g.stroke(inf); g.globalAlpha = 1; g.strokeStyle = GOLD_HI; g.lineWidth = 6; g.stroke(inf); g.strokeStyle = DARK; g.lineWidth = 1.5; g.stroke(inf); g.restore();
  // the robed figure, hooded, arms apart
  silhouette(g, [
    { poly: [[500, 760], [700, 760], [760, 1230], [440, 1230]] },                                     // robe
    { ell: [600, 660, 70, 82, 0] }, { poly: [[528, 640], [672, 640], [700, 790], [500, 790]] },         // hood
    { limb: [[540, 800], [440, 720], [400, 560]], w: 46 },                                           // right arm raised (image left)
    { limb: [[660, 800], [740, 920], [790, 1070]], w: 46 },                                          // left arm down
  ], { hatch: { ang: 0.8, step: 7, alpha: 0.3 }, extra: (cc) => {
    cc.fillStyle = '#000'; cc.beginPath(); cc.ellipse(600, 690, 46, 56, 0, 0, TAU); cc.fill();                        // the shadow inside the hood
    for (let k = 0; k < 9; k++) line(cc, [[540 + k * 15, 800], [500 + k * 25, 1225]], GOLD_HI, 2, 0.6);                  // robe folds
    line(cc, [[520, 1000], [680, 1000]], GOLD_HI, 4, 0.9);                                                             // belt
  } });
  // the wand, and the power it draws down
  line(g, [[396, 590], [372, 420]], GOLD_HI, 9, 1); dot(g, 370, 412, 14, ACCENT.magician); glow(g, 370, 412, 90, ACCENT.magician, 0.6);
  bolt(g, 372, 404, 470, 300, R, { w: 3.5, branches: 1 });
  line(g, [[792, 1072], [810, 1140]], GOLD_HI, 6, 0.9);                                                                // pointing down
  // the table and the four tools
  const top = poly([[150, 1230], [1050, 1230], [1104, 1300], [96, 1300]]); engrave(g, top, { fill: '#0b0806', hatch: { ang: 0.05, step: 6, alpha: 0.3 } });
  const cloth = new Path2D(); cloth.moveTo(150, 1300); cloth.lineTo(1050, 1300); for (let k = 0; k <= 9; k++) cloth.quadraticCurveTo(1050 - k * 100 + 50, 1520 + (k % 2) * 30, 1050 - k * 100, 1500); cloth.closePath();
  engrave(g, cloth, { fill: '#0a1430', hatch: { ang: 1.57, step: 6, alpha: 0.4, col: '#7fb8e8' } });
  for (let k = 0; k < 10; k++) line(g, [[195 + k * 90, 1305], [180 + k * 92, 1505]], GOLD, 2, 0.7);
  g.save(); g.strokeStyle = GOLD_HI; g.lineWidth = 2.2; for (let x = 170; x < 1040; x += 40) { g.beginPath(); g.moveTo(x, 1330); g.lineTo(x + 20, 1350); g.lineTo(x + 40, 1330); g.moveTo(x, 1370); g.lineTo(x + 20, 1350); g.lineTo(x + 40, 1370); g.stroke(); } g.restore();
  for (const [x, y] of [[300, 1600], [600, 1640], [900, 1600]]) star8(g, x, y, 30, { col: GOLD_HI, lw: 1.4 });
  // a horn (cups)
  g.save(); g.translate(250, 1205); g.rotate(-0.4); const hn = new Path2D(); hn.moveTo(0, 0); hn.quadraticCurveTo(60, -10, 110, -70); hn.lineTo(130, -54); hn.quadraticCurveTo(80, 10, 0, 12); hn.closePath(); engrave(g, hn, { fill: '#c8a878', lw: 2.4 }); g.restore();
  // a gear (coins)
  g.save(); g.translate(440, 1190); const gear = new Path2D(); for (let k = 0; k < 24; k++) { const a = k / 24 * TAU, rr = k % 2 ? 46 : 56; k ? gear.lineTo(Math.cos(a) * rr, Math.sin(a) * rr) : gear.moveTo(rr, 0); } gear.closePath(); engrave(g, gear, { fill: '#b8902e', lw: 2.4 }); g.beginPath(); g.arc(0, 0, 16, 0, TAU); g.fillStyle = DARK; g.fill(); g.restore();
  // a blade (swords)
  line(g, [[640, 1215], [860, 1180]], GOLD_HI, 9, 1); line(g, [[640, 1215], [860, 1180]], '#d9dde3', 4, 1); line(g, [[620, 1200], [630, 1236]], GOLD_HI, 7, 1);
  // a small rocket (wands)
  g.save(); g.translate(960, 1208); g.rotate(-1.35); const rk = new Path2D(); rk.moveTo(0, -12); rk.lineTo(80, -12); rk.quadraticCurveTo(108, -8, 110, 0); rk.quadraticCurveTo(108, 8, 80, 12); rk.lineTo(0, 12); rk.closePath(); engrave(g, rk, { fill: '#c8ccd2', lw: 2.2 }); g.restore();
  g.restore();
  frame(g, seed); titleBand(g, 'THE MAGICIAN', 104, 'I');
  return c;
}

/** XVI · THE TOWER — the tall tower that catches what comes back down, lightning on it, the city below lit up */
export function drawTower(seed = 41, { windows = null } = {}) {
  const [c, g, N, R] = base(seed); windowStart(g);
  sky(g, N, { y0: WIN.y0, y1: 1500, step: 6, base: 0.12, warm: [1500, 0.3, 500, '#ff7a32'] });
  cloud(g, 330, 330, 560, 160, R); cloud(g, 860, 290, 520, 140, R, { alpha: 0.5 });
  // the tower: two rails and cross bracing, from the ground to the sky
  const tx0 = 640, tx1 = 742, tTop = 300, tBase = 1500;
  const tw = poly([[tx0, tBase], [tx0 + 8, tTop], [tx1 - 8, tTop], [tx1, tBase]]); engrave(g, tw, { fill: '#05060a', lw: 3.2 });
  g.save(); g.clip(tw); g.strokeStyle = GOLD; g.lineWidth = 2.2; g.globalAlpha = 0.85; for (let y = tBase; y > tTop; y -= 52) { g.beginPath(); g.moveTo(tx0, y); g.lineTo(tx1, y - 52); g.moveTo(tx1, y); g.lineTo(tx0, y - 52); g.moveTo(tx0, y); g.lineTo(tx1, y); g.stroke(); } g.restore();
  // its two arms, holding the booster it has just caught
  const by0 = 250, by1 = 860, bx0 = 470, bx1 = 548;
  const arm = (y) => { const a = poly([[tx0 + 6, y - 14], [bx1 + 4, y - 22], [bx1 + 4, y + 10], [tx0 + 6, y + 14]]); engrave(g, a, { fill: '#2a2c30', lw: 2.4, hatch: { ang: 0, step: 5, alpha: 0.4 } }); };
  const bo = new Path2D(); bo.rect(bx0, by0, bx1 - bx0, by1 - by0); const gr = g.createLinearGradient(bx0, 0, bx1, 0); gr.addColorStop(0, '#5a5e66'); gr.addColorStop(0.4, '#e8ecf0'); gr.addColorStop(1, '#6a6e76'); g.fillStyle = gr; g.fill(bo); g.strokeStyle = GOLD_HI; g.lineWidth = 3; g.stroke(bo);
  for (let y = by0 + 60; y < by1; y += 70) line(g, [[bx0, y], [bx1, y]], '#3a3c40', 1.6, 0.8);
  for (const s of [-1, 1]) { const f = poly([[s < 0 ? bx0 : bx1, by0 + 30], [(s < 0 ? bx0 : bx1) + s * 34, by0 + 20], [(s < 0 ? bx0 : bx1) + s * 34, by0 + 60], [s < 0 ? bx0 : bx1, by0 + 64]]); engrave(g, f, { fill: '#2a2c30', lw: 2 }); }
  arm(by0 + 110); arm(by0 + 170);
  flames(g, bx0 - 10, bx1 + 10, by1 + 150, R, { n: 6, h0: 120, h1: 160, cols: [['#ff7a24', '#ffd27a'], ['#b8300e', '#ff6a1e']], lean: 0 });   // engines still burning
  g.save(); g.translate(0, 0); g.scale(1, -1); g.translate(0, -2 * (by1 + 2)); flames(g, bx0 - 6, bx1 + 6, by1 + 2, R, { n: 5, h0: 90, h1: 140, lean: 0.05 }); g.restore();
  // lightning crawling down the tower
  bolt(g, 200, 240, tx0 + 20, 420, R, { w: 5.5 }); bolt(g, 990, 380, tx1 - 10, 560, R, { w: 4 });
  // the city at its feet, every window lit
  const wins = skyline(g, 96, 1104, 1500, R, { maxH: 380, lit: 0.55 });
  if (windows) windows(wins);
  // the flames climbing the tower from the ground
  flames(g, 560, 830, 1500, R, { n: 16, h0: 60, h1: 260 });
  g.fillStyle = '#05060a'; g.fillRect(96, 1500, 1008, 190); hatchIn(g, poly([[96, 1500], [1104, 1500], [1104, 1690], [96, 1690]]), { ang: 0.0, step: 7, alpha: 0.3, col: '#ff8a3a' });
  g.restore();
  frame(g, seed); titleBand(g, 'THE TOWER', 118, 'XVI');
  c.userData = { wins };
  return c;
}

/** XVII · THE STAR — the great star over still water; a kneeling figure pours from two horns, onto the land and into the pool */
export function drawStar(seed = 51, { progress = 1 } = {}) {
  const [c, g, N, R] = base(seed); windowStart(g);
  sky(g, N, { y0: WIN.y0, y1: 1180, step: 6, base: 0.1, glow: [600, 470, 420, 0.28] });
  stars(g, R, 160, [600, 470, 260]);
  rays(g, 600, 470, 150, 470, 64, { col: ACCENT.star, alpha: 0.25 });
  star8(g, 600, 470, 190, { col: GOLD_HI }); glow(g, 600, 470, 260, ACCENT.star, 0.35);
  const sm = [[250, 330], [950, 330], [190, 610], [1010, 610], [300, 860], [900, 860], [600, 860]]; for (const [x, y] of sm) star8(g, x, y, 42, { col: GOLD_HI, lw: 1.5 });
  // land at left, a pool at right
  const land = poly([[96, 1180], [520, 1160], [600, 1300], [560, 1690], [96, 1690]]); engrave(g, land, { fill: '#08070a', hatch: { ang: 0.6, step: 8, alpha: 0.28 } });
  for (let k = 0; k < 40; k++) { const x = 120 + R() * 380, y = 1200 + R() * 460; line(g, [[x, y], [x + 4, y - 40 - R() * 30]], GOLD, 1.6, 0.7); line(g, [[x + 2, y - 30], [x + 12, y - 44]], GOLD, 1.2, 0.6); }   // grain coming up
  const pool = poly([[560, 1300], [1104, 1260], [1104, 1690], [560, 1690]]); g.save(); g.clip(pool); g.fillStyle = '#04060a'; g.fillRect(0, 0, TW, TH);
  for (let y = 1290; y < 1690; y += 9) line(g, [[560, y], [1104, y + (N(y, 1) - 0.5) * 8]], ACCENT.star, 1.4, 0.35 + 0.3 * (y - 1290) / 400); g.restore(); g.strokeStyle = GOLD_HI; g.lineWidth = 2.4; g.stroke(pool);
  // the kneeling figure, a horn in each hand
  silhouette(g, [
    { poly: [[520, 1060], [610, 1060], [650, 1250], [500, 1250]] }, { ell: [566, 1010, 40, 48, 0.1] }, { poly: [[520, 990], [612, 990], [640, 1150], [600, 1100], [530, 1110]] },
    { limb: [[600, 1250], [700, 1240], [710, 1300]], w: 40 }, { limb: [[520, 1250], [480, 1290], [520, 1300]], w: 40 },
    { limb: [[530, 1080], [460, 1150], [430, 1180]], w: 26 }, { limb: [[608, 1080], [690, 1140], [720, 1180]], w: 26 },
  ], { hatch: { ang: 0.7, step: 7, alpha: 0.3 } });
  for (const [hx, hy, dir] of [[420, 1185, -1], [730, 1185, 1]]) { g.save(); g.translate(hx, hy); g.scale(dir, 1); const hn = new Path2D(); hn.moveTo(0, 0); hn.quadraticCurveTo(40, -20, 60, -64); hn.lineTo(76, -54); hn.quadraticCurveTo(52, 6, 0, 14); hn.closePath(); engrave(g, hn, { fill: '#c8a878', lw: 2.2 }); g.restore(); }
  for (let k = 0; k < 7; k++) { line(g, [[396 + k * 3, 1196], [360 + k * 6, 1320 + k * 10]], ACCENT.star, 1.6, 0.8); line(g, [[756 + k * 3, 1196], [790 + k * 6, 1330 + k * 8]], ACCENT.star, 1.6, 0.8); }
  g.restore();
  frame(g, seed); titleBand(g, 'THE STAR', 118, 'XVII');
  return c;
}

/** XIX · THE SUN — a gold-roofed hall of plenty under the sun, served by machines; the burning view is the same hall on fire */
export function drawSun(seed = 61, { burning = false } = {}) {
  const [c, g, N, R] = base(seed); windowStart(g, burning ? '#070304' : '#060507');
  sky(g, N, { y0: WIN.y0, y1: 1130, step: 6, base: 0.12, glow: [600, 520, 460, burning ? 0.1 : 0.32], warm: burning ? [1130, 0.4, 600, '#ff6a2a'] : null });
  // the sun: straight and waving rays, concentric rings
  const SX = 600, SY = 500, SR = 150;
  if (!burning) { rays(g, SX, SY, SR + 14, SR + 330, 64, { col: ACCENT.sun, alpha: 0.6, lw: 2.4, wav: 0.05 }); glow(g, SX, SY, 420, ACCENT.sun, 0.45); }
  g.save(); g.fillStyle = burning ? '#1a0402' : '#d89a1e'; g.beginPath(); g.arc(SX, SY, SR, 0, TAU); g.fill();
  for (let k = 0; k < 12; k++) { g.strokeStyle = burning ? '#6a1a0a' : '#ffe08a'; g.globalAlpha = 0.6; g.lineWidth = 2; g.beginPath(); g.arc(SX, SY, SR - 10 - k * 11, 0, TAU); g.stroke(); }
  g.globalAlpha = 1; g.strokeStyle = burning ? '#ff4a1a' : GOLD_HI; g.lineWidth = 7; g.beginPath(); g.arc(SX, SY, SR, 0, TAU); g.stroke(); g.restore();
  if (burning) for (let i = 0; i < 9; i++) { const x = 160 + i * 110, y0 = 1000 - R() * 100; cloud(g, x, y0 - 120 - R() * 200, 220, 90, R, { col: '#c99a6a', alpha: 0.45 }); }
  // the hall: a long gabled building with a gold roof, its doors open on tables of plenty
  const hx0 = 230, hx1 = 970, eave = 1080, ridge = 900, ground = 1320;
  const roof = poly([[hx0 - 40, eave], [600, ridge - 40], [hx1 + 40, eave]]); engrave(g, roof, { fill: burning ? '#3a0e06' : '#b8861e', lw: 3.4, hatch: { ang: 0.0, step: 8, alpha: 0.5, col: burning ? '#ff6a2a' : '#ffe08a' } });
  for (let k = 0; k < 14; k++) line(g, [[600, ridge - 40], [hx0 - 40 + k * (hx1 - hx0 + 80) / 13, eave]], burning ? '#ff8a3a' : GOLD_HI, 1.6, 0.7);
  const wall = poly([[hx0, eave], [hx1, eave], [hx1, ground], [hx0, ground]]); engrave(g, wall, { fill: '#0a0705', hatch: { ang: 1.57, step: 10, alpha: 0.3 } });
  const door = poly([[540, ground], [540, 1170], [600, 1130], [660, 1170], [660, ground]]); g.save(); g.fillStyle = burning ? '#ff5a1a' : '#ffcf6a'; g.globalAlpha = 0.9; g.fill(door); g.restore(); g.strokeStyle = GOLD_HI; g.lineWidth = 3; g.stroke(door);
  for (let k = 0; k < 8; k++) dot(g, 560 + R() * 80, 1220 + R() * 90, 6 + R() * 5, burning ? '#3a0e06' : '#7a3a12', 0.9);       // tables of plenty
  for (const s of [-1, 1]) { const bx = 600 + s * 260; line(g, [[bx, eave], [bx, eave - 140]], GOLD, 2.4, 1); const ban = poly([[bx, eave - 140], [bx + 60 * s, eave - 128], [bx + 54 * s, eave - 100], [bx + 60 * s, eave - 72], [bx, eave - 84]]); engrave(g, ban, { fill: burning ? '#4a1a0a' : '#8a1c14', lw: 2 }); }
  if (!burning) { robotFig(g, 470, ground, 1.25, { eye: ACCENT.robot, arm: [[-30, -112], [10, -130]] }); robotFig(g, 740, ground, 1.25, { eye: ACCENT.robot, arm: [[-30, -112], [6, -128]] });
    for (const [x, y] of [[476, ground - 172], [744, ground - 170]]) { g.save(); g.fillStyle = '#c8a050'; g.beginPath(); g.ellipse(x, y, 40, 10, 0, 0, TAU); g.fill(); g.strokeStyle = GOLD_HI; g.lineWidth = 2; g.stroke(); dot(g, x - 12, y - 10, 9, '#a03a12'); dot(g, x + 10, y - 12, 10, '#c8862a'); g.restore(); } }
  else { flames(g, hx0 - 40, hx1 + 40, eave + 6, R, { n: 30, h0: 80, h1: 300 }); flames(g, hx0, hx1, ground, R, { n: 24, h0: 40, h1: 140 }); }
  // a low wall and sunflowers in front
  const wl = poly([[96, 1440], [1104, 1440], [1104, 1500], [96, 1500]]); engrave(g, wl, { fill: '#0a0806', hatch: { ang: 0, step: 12, alpha: 0.35 } });
  for (let k = 0; k < 10; k++) { const x = 150 + k * 100 + (R() - 0.5) * 30, y = 1360 - R() * 40; line(g, [[x, 1440], [x + (burning ? 14 : 0), y]], burning ? '#5a3a1a' : '#5a8a3a', 4, 1);
    g.save(); g.translate(x + (burning ? 14 : 0), y); if (burning) g.rotate(1.1); for (let p = 0; p < 16; p++) { g.rotate(TAU / 16); g.fillStyle = burning ? '#5a2a10' : ACCENT.sun; g.beginPath(); g.ellipse(0, -22, 7, 16, 0, 0, TAU); g.fill(); } g.fillStyle = '#3a1a08'; g.beginPath(); g.arc(0, 0, 14, 0, TAU); g.fill(); g.restore(); }
  g.fillStyle = '#060507'; g.fillRect(96, 1500, 1008, 190); hatchIn(g, poly([[96, 1500], [1104, 1500], [1104, 1690], [96, 1690]]), { ang: 0.3, step: 9, alpha: 0.28 });
  g.restore();
  frame(g, seed); titleBand(g, 'THE SUN', 118, 'XIX');
  return c;
}

/** XXII · THE ROBOT — machines take the oars while we sit in the breeze */
export function drawRobot(seed = 71) {
  const [c, g, N, R] = base(seed); windowStart(g);
  sky(g, N, { y0: WIN.y0, y1: 1150, step: 6, base: 0.12, glow: [300, 420, 300, 0.2] });
  stars(g, R, 60, null);
  // a pale sun low on the left and gulls
  g.save(); g.strokeStyle = GOLD_HI; g.lineWidth = 4; g.beginPath(); g.arc(300, 420, 80, 0, TAU); g.stroke(); rays(g, 300, 420, 92, 160, 36, { alpha: 0.4 }); g.restore();
  for (let k = 0; k < 5; k++) { const x = 640 + k * 70, y = 360 + (k % 2) * 50; line(g, [[x - 22, y], [x - 8, y - 10], [x, y]], GOLD_HI, 2.4, 0.9); line(g, [[x, y], [x + 8, y - 10], [x + 22, y]], GOLD_HI, 2.4, 0.9); }
  g.strokeStyle = GOLD_HI; g.lineWidth = 2.4; g.beginPath(); g.moveTo(WIN.x0, 1150); g.lineTo(WIN.x1, 1150); g.stroke();
  sea(g, N, R, { y0: 1150, y1: WIN.y1, rough: 0.5, glint: [300, 120], glintCol: GOLD_HI });
  // the longship: robots row, a Viking lounges at the stern with a horn
  longship(g, 110, 1090, 1380, R, { dir: 1, oars: 7, scale: 1.6, rowers: () => {
    for (let k = 0; k < 4; k++) robotFig(g, 450 + k * 135, 1330, 1.35, { arm: [[-40, -70], [-74, -36]] });
    vikingFig(g, 300, 1334, 1.25, { pose: 'recline', facing: 1, helmet: false, holding: [[-100, -60], [-70, -110]] });
  } });
  g.restore();
  frame(g, seed); titleBand(g, 'THE ROBOT', 118, 'XXII');
  return c;
}

/** XXIII · THE RED PLANET — it rises out of the sea; the longships turn their bows toward it; we plant our old flag on new sand */
export function drawRedPlanet(seed = 81) {
  const [c, g, N, R] = base(seed); windowStart(g);
  const HZ = 1080;
  sky(g, N, { y0: WIN.y0, y1: HZ, step: 6, base: 0.12, glow: [600, 900, 520, 0.25], warm: [HZ, 0.22, 380, '#d8512a'] });
  stars(g, R, 150, [600, 900, 460]);
  g.save(); g.beginPath(); g.rect(0, 0, TW, HZ); g.clip();
  planet(g, N, R, 600, 980, 400, { fillA: '#c4512c', fillB: '#3a0f07', line: '#f0b06a', features: [{ x: 0.0, y: -0.2, r: 90, col: '#4a1408', a: 0.55 }, { x: -0.45, y: -0.05, r: 60, col: '#5a1a0a', a: 0.45 }, { x: 0.4, y: -0.4, r: 50, col: '#521608', a: 0.4 }] });
  g.restore();
  g.strokeStyle = GOLD_HI; g.lineWidth = 2.4; g.beginPath(); g.moveTo(WIN.x0, HZ); g.lineTo(WIN.x1, HZ); g.stroke();
  sea(g, N, R, { y0: HZ, y1: WIN.y1, glint: [600, 200], glintCol: '#f08a50' });
  // three longships turning toward it
  longship(g, 150, 380, 1180, R, { dir: 1, scale: 0.45, oars: 4 }); longship(g, 820, 1060, 1200, R, { dir: -1, scale: 0.5, oars: 4, sailCols: ['#1f3a6a', '#e0c27a'] });
  longship(g, 430, 760, 1270, R, { dir: 1, scale: 0.7, oars: 5, sailCols: ['#2e5a34', '#d8c08a'] });
  // red sand in front, a Viking planting the raven banner, and the name he gives it
  const dune = new Path2D(); dune.moveTo(96, 1500); dune.quadraticCurveTo(400, 1380, 700, 1440); dune.quadraticCurveTo(900, 1480, 1104, 1420); dune.lineTo(1104, 1690); dune.lineTo(96, 1690); dune.closePath();
  engrave(g, dune, { fill: '#2a0c06', hatch: { ang: 0.25, step: 7, alpha: 0.4, col: '#d8512a' } });
  line(g, [[560, 1450], [600, 1150]], GOLD_HI, 6, 1);
  const flag = new Path2D(); flag.moveTo(600, 1155); flag.quadraticCurveTo(680, 1140, 760, 1170); flag.lineTo(740, 1215); flag.lineTo(764, 1262); flag.quadraticCurveTo(680, 1236, 596, 1250); flag.closePath(); engrave(g, flag, { fill: '#e8dcc0', lw: 2.6 });
  g.save(); g.translate(672, 1205); g.fillStyle = '#0a0a0c'; g.beginPath(); g.ellipse(0, 0, 28, 14, -0.2, 0, TAU); g.fill(); g.beginPath(); g.moveTo(-20, -4); g.lineTo(-56, -26); g.lineTo(-30, 4); g.fill(); g.beginPath(); g.moveTo(14, -8); g.lineTo(40, -40); g.lineTo(24, 0); g.fill(); g.beginPath(); g.arc(28, -6, 8, 0, TAU); g.fill(); g.restore();
  vikingFig(g, 520, 1462, 1.05, { pose: 'stand', facing: 1, helmet: true, holding: [[18, -200], [36, -170]] });
  // the sign: he names it the way Erik the Red named Greenland
  line(g, [[880, 1446], [880, 1360]], GOLD, 4, 1); const sg = poly([[784, 1310], [972, 1310], [986, 1340], [972, 1370], [784, 1370]]); engrave(g, sg, { fill: '#0b0806', lw: 2.4 });
  g.save(); g.fillStyle = GOLD_HI; g.font = '30px "CormSC", serif'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText('GREENLAND', 880, 1342); g.restore();
  g.restore();
  frame(g, seed); titleBand(g, 'THE RED PLANET', 100, 'XXIII');
  return c;
}

/** XXIV · THE GARDENER — perfect rows tended by machines; one of us grows a single tomato, by hand, by choice */
export function drawGardener(seed = 91) {
  const [c, g, N, R] = base(seed); windowStart(g, '#050706');
  // the glasshouse: tall arched ribs, panes catching the light
  for (let k = 0; k < 7; k++) { const x = 140 + k * 155; const rib = new Path2D(); rib.moveTo(x, 1300); rib.lineTo(x, 520); rib.quadraticCurveTo(x + 77, 380, x + 155, 520); g.strokeStyle = GOLD; g.lineWidth = 3; g.globalAlpha = 0.85; g.stroke(rib); g.globalAlpha = 1;
    for (let y = 560; y < 1300; y += 90) line(g, [[x, y], [x + 155, y]], GOLD, 1.4, 0.5);
    for (let j = 0; j < 4; j++) line(g, [[x + 20 + j * 30, 600 + j * 120], [x + 70 + j * 30, 520 + j * 120]], '#ffffff', 1.2, 0.18); }
  glow(g, 600, 300, 600, 'rgba(255,240,200,1)', 0.12);
  // perfect rows, receding to one point
  const VP = [600, 900];
  for (let k = -6; k <= 6; k++) { const xb = 600 + k * 170; line(g, [[xb, 1690], VP], GOLD, 1.6, 0.5);
    for (let s = 0; s < 14; s++) { const t = 1 - Math.pow(s / 14, 1.6); const x = VP[0] + (xb - VP[0]) * t, y = VP[1] + (1690 - VP[1]) * t, r = 4 + 26 * t;
      if (Math.abs(k) === 0 && t > 0.5) continue; g.save(); g.globalAlpha = 0.9; g.fillStyle = '#1a3a14'; g.beginPath(); g.arc(x, y - r, r, 0, TAU); g.fill(); g.strokeStyle = ACCENT.gardener; g.lineWidth = 1.2 + t; g.stroke();
      if (t > 0.25) for (let q = 0; q < 3; q++) dot(g, x + (R() - 0.5) * r, y - r + (R() - 0.5) * r, 2 + 3 * t, '#e04a2a', 0.9); g.restore(); } }
  robotFig(g, 830, 1330, 1.6, { arm: [[-40, -100], [-90, -110]] }); robotFig(g, 330, 1180, 1.0, { arm: [[30, -90], [60, -80]] });
  // the shaft of light, and the one who grows a tomato by hand
  g.save(); const sh = poly([[520, 150], [680, 150], [720, 1690], [460, 1690]]); const sg = g.createLinearGradient(0, 150, 0, 1690); sg.addColorStop(0, 'rgba(255,240,200,0.2)'); sg.addColorStop(1, 'rgba(255,240,200,0.05)'); g.fillStyle = sg; g.fill(sh); g.restore();
  vikingFig(g, 590, 1600, 1.25, { pose: 'kneel', facing: 1, helmet: false, holding: [[30, -130], [60, -160]] });
  dot(g, 668, 1405, 26, '#e04a2a'); dot(g, 660, 1398, 8, '#ff8a6a', 0.8); line(g, [[668, 1380], [672, 1366]], ACCENT.gardener, 4, 1);
  g.restore();
  frame(g, seed); titleBand(g, 'THE GARDENER', 104, 'XXIV');
  return c;
}

/** the card that engraves itself in the bridge: a night sky over the cliff and Mars, drawn stroke by stroke; `extra` adds the human line */
export function drawEngraving(progress = 1, { human = 0, seed = 101 } = {}) {
  const [c, g, N, R] = base(seed);
  g.save(); archPath(g); g.clip(); g.fillStyle = '#050508'; g.fillRect(0, 0, TW, TH);
  // reveal top to bottom along a wavering front, like a burin working across the plate
  const front = WIN.y0 - 40 + (WIN.y1 - WIN.y0 + 80) * progress;
  g.save(); const m = new Path2D(); m.moveTo(0, 0); m.lineTo(TW, 0); for (let x = TW; x >= 0; x -= 20) m.lineTo(x, front + Math.sin(x / 60) * 18); m.closePath(); g.clip(m);
  sky(g, N, { y0: WIN.y0, y1: HORIZON, step: 6, base: 0.13 }); stars(g, R, 160, [860, 560, 180]);
  planet(g, N, R, 860, 560, 120, { fillA: '#c4512c', fillB: '#3a0f07', line: '#f0b06a' });
  g.strokeStyle = GOLD_HI; g.lineWidth = 2.4; g.beginPath(); g.moveTo(WIN.x0, HORIZON); g.lineTo(WIN.x1, HORIZON); g.stroke();
  sea(g, N, R, { y0: HORIZON, y1: WIN.y1, glint: [860, 70] }); cliff(g, N, R, { lit: 0.6 });
  g.restore();
  // the single human line: from the cliff edge, an arc to Mars
  if (human > 0) { const pts = []; for (let k = 0; k <= 60 * human; k++) { const u = k / 60; pts.push([566 + (860 - 566) * u, 1130 - Math.sin(u * Math.PI * 0.62) * 640 - u * 0]); }
    line(g, pts, ACCENT.fool, 26, 0.3); line(g, pts, '#fff4e0', 9, 1.0); }
  g.restore();
  frame(g, seed); titleBand(g, '', 100, null);
  return c;
}
