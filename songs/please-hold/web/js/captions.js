// Captions on hold: small, crisp lyric captions drawn on the 2D layer (after bloom, so they stay sharp at subtitle size).
// Each word pops in as it is sung. A line that is left waiting starts to slump, and when it is over its letters topple
// like dominoes and drop out of frame. The machines behave differently: the hold system's voice types out like an
// automated transcript (and still falls over), while the robot's lines are cyan dot-matrix and never slump, because it
// has all day; they just switch off. Her two lines that stop waiting ("I don't wait anymore", "I've got better things
// to do") don't fall over either: they leave on their own.
import { clamp, lerp, sstep, easeOut, easeIn, easeIO, easeOutBack, rng, FONT } from './lib.js';
import { glyph } from './font5.js';

const TOPPLE = 0.2, STAGGER = 0.011, G = 46;          // seconds for one letter to fall flat, domino delay per letter, gravity (in px per s^2, x font size)

export class Captions {
  /** g: the HUD 2D context. lines: timed lyric lines ({ text, words, wt, s, e }). off: indexes acted out in the world
   *  instead (no caption). voice: { auto: [...], bot: [...] }. special: per-line options ({ exit: 'walk' | 'stay', redact: [word], ... }). */
  constructor({ g, W, H, VERT, lines, off, voice, special = {}, scale = 1 }) {
    this.g = g; this.W = W; this.H = H; this.VERT = VERT; this.L = lines; this.off = off; this.voice = voice; this.special = special;
    const S = Math.min(W, H) / 1080;
    this.px = (VERT ? 50 : 44) * S * scale;            // her lines; the hold system's mono runs a little smaller
    this.cx = VERT ? W * 0.47 : W / 2;                   // 9:16: a touch left of centre, clear of the Reels/Shorts buttons
    this.yb = VERT ? H * 0.738 : H * 0.9;                // baseline of the bottom row
    this.maxW = VERT ? W * 0.76 : W * 0.64;
    this.items = []; this.lay = new Map();
  }
  styleOf(i) { return this.voice.bot.includes(i) ? 'bot' : (this.voice.auto.includes(i) ? 'ivr' : 'her'); }

  // ------------------------------------------------------------ layout (once per line)
  layout(i) {
    if (this.lay.has(i)) return this.lay.get(i);
    const g = this.g, L = this.L[i], st = this.styleOf(i), sp = this.special[i] || {};
    const px = st === 'ivr' ? this.px * 0.9 : (st === 'bot' ? this.px * 0.95 : this.px) * (sp.size || 1);
    const font = st === 'ivr' ? `${px}px ${FONT.monoB}` : `${px}px ${sp.font || FONT.disp}`;
    const words = (st === 'bot' || sp.upper) ? L.words.map((w) => w.toUpperCase()) : L.words.slice();
    const redact = new Set((sp.redact || []).map((w) => w.toLowerCase()));
    g.save(); g.font = font;
    const dot = px / 6.6;                                  // dot-matrix pitch
    const wordW = (w) => st === 'bot' ? [...w].length * 6 * dot - dot : g.measureText(w).width;
    const spaceW = st === 'bot' ? 6 * dot : g.measureText(' ').width;
    const ww = words.map(wordW);
    // rows: one if it fits, otherwise the most balanced two-row split (three if it must)
    const total = ww.reduce((a, b) => a + b, 0) + spaceW * (words.length - 1);
    const maxW = this.maxW * (sp.maxW || 1);
    let rows = [words.map((_, k) => k)];
    if (total > maxW) {
      let best = null;
      for (let c = 1; c < words.length; c++) { const a = ww.slice(0, c).reduce((x, y) => x + y, 0) + spaceW * (c - 1), b = ww.slice(c).reduce((x, y) => x + y, 0) + spaceW * (words.length - c - 1);
        const m = Math.max(a, b); if (!best || m < best.m) best = { m, c }; }
      rows = [words.map((_, k) => k).slice(0, best.c), words.map((_, k) => k).slice(best.c)];
      if (best.m > maxW * 1.04 && words.length >= 3) {     // three rows
        const n = words.length, c1 = Math.ceil(n / 3), c2 = Math.ceil(2 * n / 3); rows = [[...Array(c1).keys()], [...Array(c2 - c1).keys()].map((k) => k + c1), [...Array(n - c2).keys()].map((k) => k + c2)]; }
    }
    // letters with their x (prefix-measured, so kerning survives) and their word
    const letters = []; const rowW = [];
    rows.forEach((r, ri) => {
      let x = 0; const row = [];
      r.forEach((k, n) => {
        const w = words[k];
        if (redact.has(w.toLowerCase().replace(/[^a-z]/g, ''))) { row.push({ ch: null, bar: true, x, w: ww[k], k, j: 0, ri }); x += ww[k]; }
        else if (st === 'bot') { [...w].forEach((ch, j) => { row.push({ ch, x: x + j * 6 * dot, w: 5 * dot, k, j, ri }); }); x += ww[k]; }
        else { [...w].forEach((ch, j) => { const a = g.measureText(w.slice(0, j)).width, b = g.measureText(w.slice(0, j + 1)).width; row.push({ ch, x: x + a, w: b - a, k, j, ri }); }); x += ww[k]; }
        if (n < r.length - 1) x += spaceW;
      });
      rowW.push(x); row.forEach((l, n) => { l.n = n; letters.push(l); });
    });
    g.restore();
    const R = rng(i * 131 + 7); letters.forEach((l) => { l.r1 = R(); l.r2 = R(); l.r3 = R(); });
    // timing
    const wt = L.wt.map((x) => x - 0.04);
    const nWords = words.length; const durOf = (k) => (k + 1 < nWords ? L.wt[k + 1] : Math.max(L.e, L.wt[k] + 0.5)) - L.wt[k];
    for (const l of letters) {
      if (st === 'ivr') { const len = [...words[l.k]].length; l.ta = wt[l.k] + l.j * clamp(durOf(l.k) * 0.8 / len, 0.012, 0.05); }
      else if (st === 'bot') l.ta = wt[l.k] + l.j * 0.032;
      else l.ta = wt[l.k] + l.j * 0.018;
    }
    const lastT = Math.max(...letters.map((l) => l.ta)) + 0.25;
    const next = i + 1 < this.L.length ? this.L[i + 1].s : null;
    let exitT;
    if (sp.exitT) exitT = sp.exitT;
    else if (next === null) exitT = L.e + 1.5;
    else if (next - L.e > 2.5) exitT = L.e + 1.6;           // a long wait: it slumps for a while, then falls over
    else exitT = Math.max(lastT + 0.3, next - 0.22);
    const exit = sp.exit || (st === 'bot' ? 'off' : 'topple');
    const nRow = rows.length; const lh = px * (st === 'bot' ? 1.3 : 1.2);
    const info = { i, st, px, font, dot, letters, rows, rowW, nRow, lh, t0: Math.min(...letters.map((l) => l.ta)) - 0.05, lastT, exitT, exit, end: exitT + (exit === 'walk' ? 1.2 : 1.0),
      waitT: Math.max(L.e, lastT) + 0.15, slump: st === 'bot' || exit !== 'topple' ? 0 : 1, color: sp.color || (st === 'ivr' ? '#ffe7c9' : (st === 'bot' ? '#7ff6ff' : '#ffffff')), accent: sp.accent || null,
      y: sp.y ?? null, sp };
    this.lay.set(i, info); return info;
  }

  /** the lines on screen at t: [i, ...] */
  visible(t) { const out = []; for (let i = 0; i < this.L.length; i++) { if (this.off.has(i)) continue; const L = this.L[i]; if (t < L.s - 0.6 || t > L.e + 4) continue; const f = this.layout(i); if (t >= f.t0 && t < f.end) out.push(i); } return out; }

  /** draws the captions at t; returns how strongly a caption is on screen (0..1, for the scrim) */
  draw(t, bright = 0) {
    let any = 0; this.bright = bright;
    for (const i of this.visible(t)) { const f = this.layout(i); any = Math.max(any, clamp((t - f.t0) / 0.3) * (1 - clamp((t - f.exitT) / 0.6))); this.drawLine(f, t); }
    return any;
  }

  drawLine(f, t) {
    const g = this.g; const px = f.px;
    const baseY = f.y !== null ? f.y * this.H : this.yb;
    const slumpK = f.slump ? sstep(f.waitT, f.waitT + 2.0, t) : 0;
    const items = []; let lastVisible = null;
    for (const l of f.letters) {
      if (t < l.ta) continue;
      const rowX = this.cx - f.rowW[l.ri] / 2; const y = baseY - (f.nRow - 1 - l.ri) * f.lh;
      let x = rowX + l.x, dy = 0, ang = 0, sc = 1, a = 1;
      // arrive
      const u = t - l.ta;
      if (f.sp.slam) { sc = 1 + 0.8 * (1 - easeOut(clamp(u / 0.14))); a = clamp(u / 0.04); }
      else if (f.st === 'her') { sc = 0.55 + 0.45 * easeOutBack(clamp(u / 0.2), 2.4); dy += (1 - easeOut(clamp(u / 0.18))) * 0.28 * px; a = clamp(u / 0.06); }
      if (f.sp.spin === l.k) ang -= 2 * Math.PI * easeIO(clamp((u - 0.12 - l.j * 0.05) / 0.45));            // "loops": a loop-the-loop
      if (f.sp.droop === l.k) { const d = easeOut(clamp((u - 0.25 - l.j * 0.06) / 0.5)); dy += d * px * (0.1 + 0.08 * l.r1); ang += d * (0.12 + 0.2 * l.r2) * (l.j % 2 ? 1 : -0.6); }   // "despair" wilts
      // wait: the letters get tired, sink a little and lean towards the next one
      if (slumpK > 0) { dy += slumpK * px * (0.04 + 0.1 * l.r1) + Math.sin(t * 1.7 + l.n * 0.45) * 0.012 * px * slumpK; ang += slumpK * (0.03 + 0.13 * l.r2); }
      // leave
      const te = f.exitT + l.n * STAGGER + l.ri * 0.03;
      if (f.exit === 'topple' && t >= te) {
        const v = (t - te) / TOPPLE; ang = Math.max(ang, (Math.PI / 2) * easeIn(clamp(v)) + ang * (1 - clamp(v)));
        if (v > 1) { const d = t - te - TOPPLE; dy += 0.5 * G * px * d * d; ang = Math.PI / 2 + d * (1.5 + l.r3 * 2); a *= 1 - clamp((d - 0.05) / 0.22); }
      } else if (f.exit === 'walk') {
        const tw = f.exitT + (f.letters.length - 1 - l.n) * 0.012; if (t >= tw) { const d = t - tw; x += easeIn(clamp(d / 0.75)) * this.W * 0.75; dy -= Math.abs(Math.sin(d * 16)) * 0.12 * px * clamp(1 - d); }
      } else if (f.exit === 'stay') a *= 1 - clamp((t - f.exitT) / 0.4);
      if (a <= 0.003) continue;
      items.push({ l, x, y, dy, ang, sc, a, standing: !(f.exit === 'topple' && t >= te) && !(f.exit === 'walk' && t >= f.exitT) });
      lastVisible = { x: x + l.w, y: y + dy };
    }
    g.save(); g.font = f.font; g.textBaseline = 'alphabetic'; g.textAlign = 'left';
    if (f.st === 'bot') { this.botPanel(f, t, baseY); g.shadowColor = 'rgba(70,235,255,0.9)'; g.shadowBlur = f.dot * 0.9;
      for (const it of items) { g.globalAlpha = it.a; this.dotGlyph(it.l, it.x, it.y, f, t); } g.restore(); return; }
    let stroke = false;
    const glyphAt = (it, fill) => {
      const { l, x, y, dy, ang, sc } = it; const w = l.w;
      g.save(); g.translate(x + w, y + dy); g.rotate(ang);                 // pivot: the letter's bottom-right corner (it falls to the right)
      if (sc !== 1) { g.translate(-w / 2, 0); g.scale(sc, sc); g.translate(w / 2, 0); }
      g.fillStyle = fill;
      if (l.bar) { const h = px * 0.62; g.beginPath(); g.roundRect(-w, -px * 0.68, w, h, h * 0.3); g.fill(); }
      else { if (stroke) { g.lineJoin = 'round'; g.lineWidth = px * 0.16; g.strokeStyle = '#0b0b0f'; g.strokeText(l.ch, -w, 0); } g.fillText(l.ch, -w, 0); }
      g.restore();
    };
    // a soft dark backing that grows with the words and shrinks as they fall (stronger over bright scenes, so white is
    // never on white), then a soft halo, then the letters themselves, crisp. The big slam line has a dark outline instead.
    const boxA = f.sp.nobox ? 0 : (f.st === 'ivr' ? 0.5 + 0.24 * this.bright : 0.42 + 0.32 * this.bright);
    if (boxA > 0.02) {
      for (let ri = 0; ri < f.nRow; ri++) {
        const st = items.filter((it) => it.l.ri === ri && it.standing); if (!st.length) continue;
        const x0 = Math.min(...st.map((it) => it.x)), x1 = Math.max(...st.map((it) => it.x + it.l.w)); const y = st[0].y;
        const fade = clamp((t - f.t0 - 0.02) / 0.12) * (f.exit === 'stay' ? 1 - clamp((t - f.exitT) / 0.4) : 1);   // steady while words pop in
        g.save(); g.globalAlpha = boxA * fade; g.fillStyle = '#080a0e'; g.shadowColor = 'rgba(8,10,14,0.9)'; g.shadowBlur = px * 0.35;
        g.beginPath(); g.roundRect(x0 - px * 0.34, y - px * 0.98, x1 - x0 + px * 0.68, px * 1.34, px * 0.3); g.fill(); g.restore();
      }
    }
    g.shadowColor = 'rgba(0,0,0,0.78)'; g.shadowBlur = px * 0.42; g.shadowOffsetY = px * 0.03;
    for (const it of items) { g.globalAlpha = it.a * 0.9; glyphAt(it, 'rgba(0,0,0,0.55)'); }
    g.shadowColor = 'rgba(0,0,0,0.6)'; g.shadowBlur = px * 0.1; g.shadowOffsetY = px * 0.035; stroke = !!f.sp.nobox;
    for (const it of items) { g.globalAlpha = it.a; glyphAt(it, (f.accent && f.accent.k === it.l.k) ? f.accent.color : f.color); }
    // the hold system's cursor, blinking while it waits
    if (f.st === 'ivr' && lastVisible && t < f.exitT && (t % 0.7) < 0.42) { g.globalAlpha = 1; g.fillStyle = f.color; g.fillRect(lastVisible.x + px * 0.12, lastVisible.y - px * 0.74, px * 0.42, px * 0.86); }
    g.restore();
  }

  // the robot speaks on a little LED panel, like its eye strip
  botPanel(f, t, baseY) {
    const g = this.g, d = f.dot; const on = easeOut(clamp((t - f.t0) / 0.18)); const off = 1 - clamp((t - f.exitT - 0.32) / 0.2);
    const k = on * off; if (k <= 0.01) return;
    const w = Math.max(...f.rowW) + d * 4, h = 7 * d + (f.nRow - 1) * f.lh + d * 3; const y = baseY - (f.nRow - 1) * f.lh - 7 * d - d * 1.5;
    g.save(); g.shadowColor = 'rgba(0,0,0,0.5)'; g.shadowBlur = d * 3;
    g.globalAlpha = 0.86 * k; g.fillStyle = '#05080b'; g.beginPath(); g.roundRect(this.cx - w / 2 * on, y, w * on, h, d * 1.6); g.fill();
    g.shadowBlur = 0; g.globalAlpha = 0.5 * k; g.strokeStyle = '#2a8f99'; g.lineWidth = Math.max(1, d * 0.25); g.stroke();
    g.restore();
  }

  dotGlyph(l, x, y, f, t) {
    const g = this.g, d = f.dot, rows = glyph(l.ch); const u = t - l.ta;
    const off = f.exit === 'off' ? f.exitT : 1e9;
    g.fillStyle = f.color;
    for (let r = 0; r < 7; r++) for (let c = 0; c < 5; c++) {
      if (rows[r][c] !== '#') continue;
      if (u < c * 0.007) continue;                                           // the columns scan on
      const h = ((l.n * 7 + r) * 5 + c) * 0.618034 % 1; if (t > off + h * 0.3) continue;   // and switch off dot by dot
      g.beginPath(); g.arc(x + c * d + d / 2, y - (6 - r) * d - d / 2, d * 0.42, 0, 6.2832); g.fill();
    }
  }
}
