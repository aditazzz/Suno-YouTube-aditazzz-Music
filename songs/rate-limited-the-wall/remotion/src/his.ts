// BRIDGE 2, his side: the camera has pushed through a crack. A lighthouse-sun behind vast rotating quota shutters, his
// side of the thread a frozen traffic-jam of his pulses backed up to the horizon, her (tiny, through the crack) still
// up, still knocking. Hushed, near-still, and the film's only mint-teal type.
import {LINES} from './data';
import {font, glow, stoneTex, type G} from './gfx';
import {PAL, TAU, clamp, easeInOut, easeOut, fbm, hash, inv, lerp, mix, rgba, sstep} from './lib';
import {T, type Layout} from './story';
import {cursor} from './cast';

type HisCam = {x: number; y: number; z: number};
type HisGeo = {sun: {x: number; y: number}; horizon: number; crack: {x: number; y: number}; wallTop?: number; wallX?: number; sunR: number; rise: {x: number; y: number}};
const geo = (L: Layout): HisGeo =>
  L.vertical
    ? {sun: {x: 540, y: 560}, horizon: 760, crack: {x: 540, y: 1600}, wallTop: 1540, sunR: 82, rise: {x: 560, y: 740}}
    : {sun: {x: 1430, y: 560}, horizon: 720, crack: {x: 300, y: 690}, wallX: 330, sunR: 92, rise: {x: 1560, y: 712}};

export function hisCam(L: Layout, t: number): HisCam {
  const G0 = geo(L);
  const k = easeOut(inv(T.b2 - 0.05, T.b2 + 1.1, t), 3);
  const z = Math.exp(lerp(Math.log(7), Math.log(1), k)) * (1 + 0.04 * inv(T.b2, T.final, t));
  const cx = lerp(G0.crack.x, L.W / 2, k), cy = lerp(G0.crack.y, L.H / 2, k);
  return {x: cx, y: cy, z};
}

export function hisSide(g: G) {
  const {c, l, L, t, W, H, S} = g;
  const G0 = geo(L);
  const cam = hisCam(L, t);
  for (const [ctx, k] of [[c, 1], [l, 0.5]] as const) {
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.translate((W / 2) * k, (H / 2) * k);
    ctx.scale(S * cam.z * k, S * cam.z * k);
    ctx.translate(-cam.x, -cam.y);
  }
  const dim = 1 - 0.28 * sstep(T.laptop + 0.4, T.water + 1.2, t);
  const align = easeInOut(inv(T.six, T.final + 0.2, t));
  const sun = {x: lerp(G0.sun.x, G0.rise.x, align * 0.55), y: lerp(G0.sun.y, G0.rise.y, align * 0.55)};
  // sky
  const sk = c.createLinearGradient(0, -400, 0, G0.horizon);
  sk.addColorStop(0, rgba([2, 8, 16]));
  sk.addColorStop(0.7, rgba([6, 34, 44]));
  sk.addColorStop(1, rgba(mix([18, 80, 86], [60, 90, 80], align)));
  c.fillStyle = sk;
  c.fillRect(-2000, -2000, L.W + 4000, G0.horizon + 2000);
  for (let i = 0; i < 160; i++) {
    const x = lerp(-600, L.W + 600, hash(i * 4.3)), y = lerp(-600, G0.horizon - 60, hash(i * 2.1));
    c.fillStyle = rgba([200, 255, 245], 0.35 * hash(i * 9.1));
    c.fillRect(x, y, 1.4, 1.4);
  }
  // the lighthouse-sun
  glow(g, sun.x, sun.y, G0.sunR * 14, PAL.teal, 0.5 * dim);
  glow(g, sun.x, sun.y, G0.sunR * 5, PAL.tealWhite, 0.9 * dim, 0.35);
  const q = c.createRadialGradient(sun.x, sun.y, 0, sun.x, sun.y, G0.sunR);
  q.addColorStop(0, rgba([255, 255, 255], dim));
  q.addColorStop(0.6, rgba(mix(PAL.tealWhite, [255, 246, 220], align), dim));
  q.addColorStop(1, rgba(PAL.teal, 0));
  c.fillStyle = q;
  c.beginPath();
  c.arc(sun.x, sun.y, G0.sunR, 0, TAU);
  c.fill();
  // the beam sweeps, then settles toward where the sun will rise
  const sweep = 0.42 * (t - T.b2) - 0.3;
  const beamA = lerp(sweep, Math.round(sweep / Math.PI) * Math.PI + (L.vertical ? Math.PI / 2 : 0.04), align);
  for (const [ctx, aa] of [[c, 0.07], [l, 0.22]] as const) {
    ctx.save();
    ctx.globalCompositeOperation = 'lighter';
    for (const off of [0, Math.PI]) {
      const a = beamA + off;
      const len = 2600;
      const gr = ctx.createLinearGradient(sun.x, sun.y, sun.x + Math.cos(a) * len, sun.y + Math.sin(a) * len);
      gr.addColorStop(0, rgba(PAL.tealWhite, aa * dim));
      gr.addColorStop(1, rgba(PAL.teal, 0));
      ctx.fillStyle = gr;
      ctx.beginPath();
      ctx.moveTo(sun.x, sun.y);
      ctx.lineTo(sun.x + Math.cos(a - 0.07) * len, sun.y + Math.sin(a - 0.07) * len);
      ctx.lineTo(sun.x + Math.cos(a + 0.07) * len, sun.y + Math.sin(a + 0.07) * len);
      ctx.closePath();
      ctx.fill();
    }
    ctx.restore();
  }
  // the quota shutters: vast, turning like weather, operated by nobody
  const spin = 0.11 * (t - T.b2) + 0.05 * Math.sin(t * 0.45) + 0.6;
  c.save();
  c.translate(sun.x, sun.y);
  for (let i = 0; i < 7; i++) {
    const a = spin + (i * TAU) / 7;
    c.save();
    c.rotate(a);
    const gr = c.createLinearGradient(30, 0, 1300, 0);
    gr.addColorStop(0, 'rgba(1,10,14,0.97)');
    gr.addColorStop(1, 'rgba(3,18,24,0.85)');
    c.fillStyle = gr;
    c.beginPath();
    c.moveTo(G0.sunR * 0.55, -10);
    c.lineTo(1300, -150);
    c.lineTo(1300, 120);
    c.lineTo(G0.sunR * 0.55, 18);
    c.closePath();
    c.fill();
    c.strokeStyle = rgba(PAL.teal, 0.25 * dim);
    c.lineWidth = 1.5;
    c.beginPath();
    c.moveTo(G0.sunR * 0.55, -10);
    c.lineTo(1300, -150);
    c.stroke();
    c.restore();
  }
  c.restore();
  // ground
  const gg = c.createLinearGradient(0, G0.horizon, 0, G0.horizon + 900);
  gg.addColorStop(0, rgba([6, 26, 30]));
  gg.addColorStop(1, rgba([1, 6, 8]));
  c.fillStyle = gg;
  c.fillRect(-2000, G0.horizon, L.W + 4000, 3000);
  c.fillStyle = rgba(PAL.teal, 0.18);
  c.fillRect(-2000, G0.horizon, L.W + 4000, 1.5);
  // the wall's back, and the crack we came through: her side's amber, and her, tiny, still knocking
  wallBack(g, G0, cam);
  // his side of the thread: a traffic jam of his pulses, backed up to the horizon
  const A = L.vertical ? {x: G0.crack.x, y: G0.crack.y - 40} : {x: G0.crack.x + 30, y: G0.crack.y};
  const B = sun;
  c.strokeStyle = rgba(PAL.teal, 0.7);
  c.lineWidth = 2;
  c.beginPath();
  c.moveTo(A.x, A.y);
  c.quadraticCurveTo((A.x + B.x) / 2, (A.y + B.y) / 2 + (L.vertical ? 0 : 26), B.x, B.y);
  c.stroke();
  const n = 64;
  for (let i = 0; i < n; i++) {
    const k = 0.035 + (i / n) * 0.9;
    const x = (1 - k) * (1 - k) * A.x + 2 * k * (1 - k) * ((A.x + B.x) / 2) + k * k * B.x;
    const y = (1 - k) * (1 - k) * A.y + 2 * k * (1 - k) * ((A.y + B.y) / 2 + (L.vertical ? 0 : 26)) + k * k * B.y;
    const idle = Math.sin(t * 2.2 + i * 1.3) * 0.8;
    const a = (0.95 - k * 0.4) * dim;
    glow(g, x + (L.vertical ? idle : 0), y + (L.vertical ? 0 : idle), 22, PAL.tealWhite, 0.5 * a);
    c.fillStyle = rgba([235, 255, 252], a);
    c.beginPath();
    c.arc(x + (L.vertical ? idle : 0), y + (L.vertical ? 0 : idle), 4.4 * (1 - k * 0.45), 0, TAU);
    c.fill();
  }
  mintType(g);
  // through the crack: the whiteout we came in on
  const wo = 1 - sstep(T.b2 - 0.05, T.b2 + 0.45, t);
  if (wo > 0.01) {
    c.setTransform(1, 0, 0, 1, 0, 0);
    c.fillStyle = rgba([235, 255, 250], wo);
    c.fillRect(0, 0, W, H);
  }
}

function wallBack(g: G, G0: HisGeo, cam: HisCam) {
  const {c, L, t} = g;
  void cam;
  c.save();
  c.beginPath();
  if (L.vertical) c.rect(-2000, G0.wallTop!, L.W + 4000, 3000);
  else c.rect(-3000, -3000, 3000 + G0.wallX!, 6000);
  c.fillStyle = rgba([7, 9, 11]);
  c.fill();
  c.clip();
  const pat = c.createPattern(stoneTex(), 'repeat');
  if (pat) {
    c.globalAlpha = 0.7;
    c.fillStyle = pat;
    c.fillRect(-3000, -3000, 8000, 8000);
    c.globalAlpha = 1;
  }
  c.restore();
  // his light rims the wall's back edge
  c.strokeStyle = rgba(PAL.teal, 0.4);
  c.lineWidth = 2;
  c.beginPath();
  if (L.vertical) {
    c.moveTo(-100, G0.wallTop!);
    c.lineTo(L.W + 100, G0.wallTop!);
  } else {
    c.moveTo(G0.wallX!, -1000);
    c.lineTo(G0.wallX!, 820);
  }
  c.stroke();
  // the crack: a jagged fissure with her amber coming through
  const cr = G0.crack;
  const pts: [number, number][] = [];
  for (let i = 0; i <= 14; i++) {
    const k = i / 14;
    const off = (fbm(i * 0.9, 3.3, 2) - 0.5) * 18 + (hash(i * 3.7) - 0.5) * 12 * Math.sin(Math.PI * k);
    pts.push(L.vertical ? [cr.x - 70 + k * 140, cr.y + off] : [cr.x + off, cr.y - 70 + k * 140]);
  }
  const width = (k: number) => 13 * Math.sin(Math.PI * k) ** 0.8 + 1.5;
  c.beginPath();
  pts.forEach(([x, y], i) => {
    const w = width(i / 14);
    if (i === 0) c.moveTo(L.vertical ? x : x - w, L.vertical ? y - w : y);
    else c.lineTo(L.vertical ? x : x - w, L.vertical ? y - w : y);
  });
  for (let i = pts.length - 1; i >= 0; i--) {
    const [x, y] = pts[i];
    const w = width(i / 14);
    c.lineTo(L.vertical ? x : x + w, L.vertical ? y + w : y);
  }
  c.closePath();
  // through the opening: her side of the night, warm and dim, and her in it
  c.save();
  const inside = c.createRadialGradient(cr.x, cr.y + 20, 0, cr.x, cr.y + 20, 80);
  inside.addColorStop(0, rgba([120, 66, 22]));
  inside.addColorStop(1, rgba([34, 18, 8]));
  c.fillStyle = inside;
  c.fill();
  c.clip();
  c.fillStyle = rgba([18, 10, 6]);
  if (L.vertical) c.fillRect(cr.x - 80, cr.y + 6, 160, 30);
  else c.fillRect(cr.x - 30, cr.y + 22, 60, 60);
  c.restore();
  c.strokeStyle = rgba(PAL.amberHot, 0.85);
  c.lineWidth = 1.2;
  c.stroke();
  glow(g, cr.x, cr.y, 150, PAL.amber, 0.32, 0.1);
  // her, tiny, still up, still knocking (her blink, her knock)
  const knock = Math.max(0, Math.sin(t * 2 * Math.PI * 0.85)) ** 8;
  cursor(g, cr.x + (L.vertical ? -4 : 0), cr.y + (L.vertical ? 6 : 24), 6, 13, 1, 1, 0.25 * knock, Math.sin(t * 6) > 0 ? 1 : 0.3, 0.5, {});
}

// his lines in the world, the film's only mint-teal type
const B2_LINES = LINES.filter((x) => x.sec === 'BRIDGE2');
function mintType(g: G) {
  const {c, l, L, t} = g;
  const ln = B2_LINES.find((x, i) => t >= x.s - 0.3 && t < (B2_LINES[i + 1]?.s ?? T.final) - 0.15);
  if (!ln) return;
  const next = B2_LINES[B2_LINES.indexOf(ln) + 1];
  const out = 1 - sstep((next?.s ?? T.final) - 0.6, (next?.s ?? T.final) - 0.15, t);
  const size = L.vertical ? 58 : 56;
  const x0 = L.vertical ? L.W / 2 : 150, y0 = L.vertical ? 1240 : 250;
  for (const ctx of [c, l]) {
    ctx.save();
    ctx.font = font('InterDisplayBold', size);
    ctx.textBaseline = 'middle';
    ctx.letterSpacing = '1px';
    const widths = ln.words.map((w) => ctx.measureText(w + ' ').width);
    const total = widths.reduce((a, b) => a + b, 0);
    let x = L.vertical ? x0 - total / 2 : x0;
    ln.words.forEach((w, i) => {
      const a = sstep(ln.wt[i] - 0.12, ln.wt[i] + 0.35, t) * out;
      const rise = (1 - easeOut(inv(ln.wt[i] - 0.12, ln.wt[i] + 0.5, t), 3)) * 10;
      ctx.fillStyle = rgba(ctx === c ? PAL.mint : mix(PAL.mint, [255, 255, 255], 0.2), clamp(a * (ctx === c ? 0.95 : 0.5)));
      ctx.fillText(w, x, y0 + rise);
      x += widths[i];
    });
    ctx.restore();
  }
}
