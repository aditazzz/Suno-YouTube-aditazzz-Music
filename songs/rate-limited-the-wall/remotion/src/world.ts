import {band, beatPulse} from './data';
import {glow, paperTex, stage, view, type G} from './gfx';
import {PAL, TAU, candy, clamp, env, fbm, hash, hit, inv, lerp, mix, noise1, once, rgba, sstep, surface, type RGB} from './lib';
import {T, dawn, frostReach, himState, nightClock, rain, thaw, type Layout} from './story';

const night = (t: number) => 1 - dawn(t);
// the rant-light: during the bridge the horizon behind her warms
const rant = (t: number) => env(t, T.bridge, T.b2 - 0.6, 1.2, 1.5);

export function sky(g: G) {
  const {c, L, t} = g;
  stage(g, 0.04);
  const v = view(g);
  const d = dawn(t), r = rant(t);
  const hz = L.horizon;
  const gr = c.createLinearGradient(0, hz - (L.vertical ? 900 : 760), 0, hz + 40);
  const top = mix(PAL.skyTop, PAL.dawnTop, d);
  const mid = mix(mix(PAL.skyMid, [40, 16, 30], r * 0.7), PAL.dawnMid, d * 0.85);
  const low = mix(mix(PAL.skyLow, [120, 40, 26], r * 0.8), PAL.dawnLow, d);
  gr.addColorStop(0, rgba(top));
  gr.addColorStop(0.62, rgba(mid));
  gr.addColorStop(1, rgba(low));
  c.fillStyle = gr;
  c.fillRect(v.x0, v.y0, v.x1 - v.x0, v.y1 - v.y0);
  // her side is warm, his side is cool (until the wall hides it)
  const wx = L.vertical ? L.W * 0.5 : L.home.x;
  const warm = c.createRadialGradient(wx, hz, 0, wx, hz, L.vertical ? 700 : 900);
  warm.addColorStop(0, rgba(mix(PAL.amberDeep, [255, 60, 30], r), 0.16 + 0.3 * r));
  warm.addColorStop(1, rgba(PAL.amberDeep, 0));
  c.fillStyle = warm;
  c.fillRect(v.x0, v.y0, v.x1 - v.x0, v.y1 - v.y0);
  // stars
  const n = night(t);
  if (n > 0.02) {
    for (let i = 0; i < 320; i++) {
      const x = lerp(-1600, 3500, hash(i * 3.1));
      const y = lerp(L.vertical ? -1400 : -1300, hz - 30, Math.pow(hash(i * 7.7), 0.8));
      if (x < v.x0 || x > v.x1 || y < v.y0 || y > v.y1) continue;
      const tw = 0.55 + 0.45 * Math.sin(t * (1.3 + hash(i) * 2.4) + i);
      const a = n * tw * (0.25 + 0.75 * hash(i * 1.9)) * (1 - 0.6 * sstep(hz - 260, hz - 30, y));
      const s = 0.6 + hash(i * 5.3) * 1.3;
      c.fillStyle = rgba([220, 230, 255], a);
      c.fillRect(x - s / 2, y - s / 2, s, s);
      if (s > 1.6) glow(g, x, y, 6, [200, 220, 255], a * 0.35);
    }
  }
  moon(g);
}

function moon(g: G) {
  const {c, L, t} = g;
  stage(g, 0.07);
  const k = nightClock(t);
  let x: number, y: number;
  if (!L.vertical) {
    x = lerp(800, 70, k);
    y = lerp(120, L.horizon - 6, Math.pow(k, 1.7));
  } else {
    x = lerp(330, 120, k);
    y = k < 0.94 ? lerp(70, 128, k / 0.94) : lerp(128, L.horizon - 6, inv(0.94, 1, k));
  }
  const r = L.vertical ? 15 : 17;
  const a = 1 - 0.55 * dawn(t);
  glow(g, x, y, r * 9, [210, 215, 235], 0.18 * a);
  glow(g, x, y, r * 3, [235, 235, 225], 0.5 * a);
  c.save();
  c.beginPath();
  c.arc(x, y, r, 0, TAU);
  c.clip();
  c.fillStyle = rgba(PAL.moon, a);
  c.fillRect(x - r, y - r, 2 * r, 2 * r);
  c.fillStyle = rgba([150, 150, 160], 0.35 * a);
  for (const [dx, dy, rr] of [[-0.3, -0.2, 0.28], [0.25, 0.3, 0.2], [0.35, -0.35, 0.12], [-0.1, 0.45, 0.1]]) {
    c.beginPath();
    c.arc(x + dx * r, y + dy * r, rr * r, 0, TAU);
    c.fill();
  }
  // gibbous shadow on the side away from the (future) sun
  c.fillStyle = rgba([8, 10, 26], 0.75 * a);
  c.beginPath();
  c.arc(x - r * 1.35, y - r * 0.15, r * 1.05, 0, TAU);
  c.fill();
  c.restore();
}

// his aurora: curtains of teal-green light over his side, the green wash on "green", eaten by the fog
export function aurora(g: G) {
  const {c, l, L, t} = g;
  const a0 = sstep(T.v1 - 1.2, T.v1 + 0.6, t) * 0.4 + 0.75 * hit(t, T.green, 0.08, 1.6);
  const fogged = 1 - sstep(T.no - 1.0, T.no + 0.2, t);
  const back = sstep(T.outro + 1.5, T.back, t) * 0.6;
  const a = (a0 * fogged + back) * (t < T.drop + 0.4 || t > T.outro ? 1 : 0);
  if (a < 0.01) return;
  stage(g, 0.12);
  const v = view(g);
  const x0 = L.vertical ? -100 : 980, x1 = L.vertical ? 1180 : 2500;
  const yb = L.horizon - (L.vertical ? 40 : 60);
  c.save();
  l.save();
  c.globalCompositeOperation = 'lighter';
  l.globalCompositeOperation = 'lighter';
  const green = sstep(T.green - 0.1, T.green + 0.3, t) * (1 - sstep(T.green + 2, T.screen, t) * 0.5);
  for (let x = x0; x < x1; x += 7) {
    if (x < v.x0 - 10 || x > v.x1 + 10) continue;
    const u = (x - x0) / (x1 - x0);
    const n = fbm(x / 260 + t * 0.05, t * 0.08, 3);
    const h = (L.vertical ? 300 : 420) * (0.4 + n) * Math.sin(Math.PI * u);
    const top = yb - h - 80 * fbm(x / 120, 3.3 + t * 0.1, 2);
    const col = mix(mix(PAL.teal, [90, 255, 140], green), candy(Math.floor(u * 9)), back * 0.6);
    const s = a * (0.35 + 0.65 * fbm(x / 60 - t * 0.3, 7.1, 2)) * Math.sin(Math.PI * u);
    const gr = c.createLinearGradient(0, top, 0, yb);
    gr.addColorStop(0, rgba(col, 0));
    gr.addColorStop(0.55, rgba(col, 0.07 * s));
    gr.addColorStop(1, rgba(col, 0.02 * s));
    c.fillStyle = gr;
    c.fillRect(x, top, 8, yb - top);
    const lg = l.createLinearGradient(0, top, 0, yb);
    lg.addColorStop(0, rgba(col, 0));
    lg.addColorStop(0.6, rgba(col, 0.16 * s));
    lg.addColorStop(1, rgba(col, 0));
    l.fillStyle = lg;
    l.fillRect(x, top, 8, yb - top);
  }
  c.restore();
  l.restore();
}

// paper-cut dunes: far (bluer, lighter) and mid (darker), each with a moonlit rim
function ridge(x: number, seed: number, amp: number, freq: number) {
  return amp * (fbm(x * freq + seed, seed * 1.7, 4) - 0.5) * 2 + amp * 0.5 * Math.sin(x * freq * 0.7 + seed);
}
export function dunes(g: G) {
  const {c, L, t} = g;
  const d = dawn(t);
  const layers: [number, number, number, RGB, number][] = L.vertical
    ? [[0.3, L.horizon + 10, 50, [14, 18, 36], 0.0016], [0.55, L.horizon + 70, 80, [8, 10, 22], 0.0022]]
    : [[0.32, L.horizon + 6, 46, [15, 19, 38], 0.0017], [0.58, L.horizon + 52, 70, [8, 10, 21], 0.0024]];
  layers.forEach(([p, base, amp, col0, f], li) => {
    stage(g, p);
    const v = view(g);
    const col = mix(mix(col0, [36, 24, 30], rant(t) * 0.5), mix([110, 70, 90], [60, 50, 70], li), d * 0.6);
    c.beginPath();
    c.moveTo(v.x0, v.y1);
    for (let x = v.x0; x <= v.x1 + 16; x += 16) c.lineTo(x, base - Math.abs(ridge(x, 11 + li * 7, amp, f)));
    c.lineTo(v.x1 + 16, v.y1);
    c.closePath();
    c.fillStyle = rgba(col);
    c.fill();
    // paper fibre
    c.save();
    c.clip();
    c.globalAlpha = 0.05;
    c.globalCompositeOperation = 'overlay';
    const pat = c.createPattern(paperTex(), 'repeat');
    if (pat) {
      c.fillStyle = pat;
      c.fillRect(v.x0, base - amp * 2, v.x1 - v.x0, v.y1 - base + amp * 2);
    }
    c.restore();
    // moonlit rim
    c.beginPath();
    for (let x = v.x0; x <= v.x1 + 16; x += 16) {
      const y = base - Math.abs(ridge(x, 11 + li * 7, amp, f));
      if (x === v.x0) c.moveTo(x, y);
      else c.lineTo(x, y);
    }
    c.strokeStyle = rgba(mix([120, 130, 170], PAL.dawnLow, d), 0.16 + 0.1 * d);
    c.lineWidth = 1.4;
    c.stroke();
    if (li === 0) village(g, base, amp, f, 11 + li * 7);
  });
}

// her forty tabs: pin-prick windows that kindle in the dunes behind her like a village lighting up
export function villageSpot(L: Layout, i: number) {
  const x = L.vertical ? lerp(40, 1040, hash(i * 2.3)) : lerp(-120, 960, hash(i * 2.3));
  return {x, depth: hash(i * 4.1)};
}
export const villageOn = (i: number, t: number) => {
  const t0 = T.forty + 0.15 + (i / 40) * (T.tabs - T.forty + 0.7) + hash(i * 9.1) * 0.12;
  const fog = 1 - 0.8 * sstep(T.screen + 1.1, T.no - 0.2, t) * 1;
  const back = sstep(T.ch2 - 2.5, T.ch2 - 0.6, t);
  const gone = sstep(T.ch2 - 0.6, T.ch2 + 0.1, t) * (1 - sstep(T.final - 1, T.final, t));
  return sstep(t0, t0 + 0.12, t) * Math.max(fog, back) * (1 - gone) * (0.85 + 0.15 * Math.sin(t * 3 + i));
};
function village(g: G, base: number, amp: number, f: number, seed: number) {
  const {c, L, t} = g;
  for (let i = 0; i < 40; i++) {
    const on = villageOn(i, t);
    if (on < 0.01) continue;
    const {x, depth} = villageSpot(L, i);
    const y = base - Math.abs(ridge(x, seed, amp, f)) + 6 + depth * 26;
    const col = mix(PAL.amber, [255, 236, 190], hash(i * 3.3) * 0.6);
    c.fillStyle = rgba(col, on);
    c.fillRect(x - 2, y - 1.5, 4, 3);
    glow(g, x, y, 14, col, 0.5 * on);
  }
}

export function him(g: G) {
  const {c, L, t} = g;
  const h = himState(t);
  stage(g, 1);
  const {x, y} = L.him;
  const r = L.orbR;
  const sun = sstep(T.reset, T.where, t);
  const on = Math.max(h.on, sun);
  if (on < 0.01) return;
  const fl = h.flare;
  const R = r * (1 + 0.25 * fl + 2.2 * sun);
  const col = mix(PAL.teal, [255, 214, 160], sun);
  glow(g, x, y, R * (16 - 7 * sun), col, (0.35 - 0.1 * sun) * on);
  glow(g, x, y, R * (6 - 2.5 * sun), mix(PAL.tealWhite, [255, 240, 210], sun), (0.7 - 0.25 * sun) * on + 0.5 * fl);
  const q = c.createRadialGradient(x, y, 0, x, y, R);
  q.addColorStop(0, rgba([255, 255, 255], on));
  q.addColorStop(0.55, rgba(mix(PAL.tealWhite, [255, 244, 220], sun), on));
  q.addColorStop(1, rgba(col, 0.0));
  c.fillStyle = q;
  c.beginPath();
  c.arc(x, y, R, 0, TAU);
  c.fill();
  orbitDots(g, x, y, r, t, h.dotsSpeed, on, t >= T.politely && t < T.reset + 1.5 ? T.politely + 0.4 : null);
}

// the three typing dots, orbiting like electrons (fast = typing); frozen (stopped at a phase) = gone
export function orbitDots(g: G, x: number, y: number, r: number, t: number, speed: number, a: number, frozenAt: number | null, col: RGB = PAL.tealWhite) {
  const tt = frozenAt !== null && t > frozenAt ? frozenAt : t;
  const ph = tt * speed * TAU;
  for (let i = 0; i < 3; i++) {
    const tilt = (i * Math.PI) / 3 + 0.4;
    const ang = ph + (i * TAU) / 3;
    const ex = Math.cos(ang) * r * 2.1, ey = Math.sin(ang) * r * 0.62;
    const px = x + ex * Math.cos(tilt) - ey * Math.sin(tilt), py = y + ex * Math.sin(tilt) + ey * Math.cos(tilt);
    const dim = frozenAt !== null && t > frozenAt ? 0.55 : 1;
    glow(g, px, py, r * 0.9, col, 0.8 * a * dim);
    g.c.fillStyle = rgba([255, 255, 255], a * dim);
    g.c.beginPath();
    g.c.arc(px, py, r * 0.16, 0, TAU);
    g.c.fill();
  }
}

export function ground(g: G, herX: number, herY: number, herGlow: number) {
  const {c, L, t} = g;
  stage(g, 1);
  const v = view(g);
  const gy = L.vertical ? L.horizon + 70 : L.home.y - 4;
  const d = dawn(t);
  const gr = c.createLinearGradient(0, gy, 0, gy + (L.vertical ? 1400 : 320));
  gr.addColorStop(0, rgba(mix([10, 11, 22], [70, 50, 60], d)));
  gr.addColorStop(1, rgba(mix([3, 3, 7], [30, 22, 28], d)));
  c.fillStyle = gr;
  c.fillRect(v.x0, gy, v.x1 - v.x0, v.y1 - gy);
  // the ground line catches a little moonlight
  c.fillStyle = rgba([90, 100, 140], 0.12);
  c.fillRect(v.x0, gy, v.x1 - v.x0, 1.5);
  // her light pool on the ground
  const pr = L.vertical ? 260 : 300;
  const q = c.createRadialGradient(herX, herY, 0, herX, herY, pr);
  q.addColorStop(0, rgba(PAL.amber, 0.16 * herGlow));
  q.addColorStop(1, rgba(PAL.amber, 0));
  c.save();
  c.beginPath();
  c.rect(v.x0, gy, v.x1 - v.x0, v.y1 - gy);
  c.clip();
  c.fillStyle = q;
  c.fillRect(herX - pr, herY - pr, pr * 2, pr * 2);
  c.restore();
}

// "the screen went grey": a fog front rolls in from his side, swallowing his glow, the village, the aurora
export function fogFront(t: number, L: Layout) {
  const k = inv(T.screen, T.no + 0.2, t);
  return L.vertical ? lerp(-300, 2200, k) : lerp(2150, -500, k);
}
export function fogDensity(t: number) {
  const inn = sstep(T.screen, T.screen + 0.6, t);
  const out = 1 - 0.85 * sstep(T.drop, T.drop + 0.6, t);
  const gone = 1 - sstep(T.post1, T.v2, t);
  return inn * out * gone;
}
// the fog bank is painted on its own half-res sheet, then cut by the front with a soft edge
export function fog(g: G, p: number) {
  const {c, L, t, W, H} = g;
  const dens = fogDensity(t);
  if (dens < 0.01) return;
  stage(g, p);
  const v = view(g);
  const front = fogFront(t, L);
  const soft = 380;
  // grey is a weather event: it drains what it covers
  c.save();
  c.globalCompositeOperation = 'saturation';
  const gr = L.vertical ? c.createLinearGradient(0, front + soft, 0, front - soft) : c.createLinearGradient(front - soft, 0, front + soft, 0);
  gr.addColorStop(0, rgba([128, 128, 128], 0));
  gr.addColorStop(1, rgba([128, 128, 128], 0.9 * dens));
  c.fillStyle = gr;
  c.fillRect(v.x0, v.y0, v.x1 - v.x0, v.y1 - v.y0);
  c.restore();
  const sheet = surface('fogsheet', Math.ceil(W / 2), Math.ceil(H / 2));
  const f = sheet.getContext('2d')!;
  f.setTransform(1, 0, 0, 1, 0, 0);
  f.globalCompositeOperation = 'source-over';
  f.clearRect(0, 0, sheet.width, sheet.height);
  const m = c.getTransform();
  f.setTransform(m.a / 2, m.b / 2, m.c / 2, m.d / 2, m.e / 2, m.f / 2);
  const hz = L.horizon;
  const veil = f.createLinearGradient(0, hz - 560, 0, hz + 420);
  veil.addColorStop(0, rgba(PAL.fog, 0));
  veil.addColorStop(0.45, rgba(PAL.fog, 0.16));
  veil.addColorStop(0.62, rgba(PAL.fog, 0.24));
  veil.addColorStop(0.8, rgba(PAL.fog, 0.12));
  veil.addColorStop(1, rgba(PAL.fog, 0));
  f.fillStyle = veil;
  f.fillRect(v.x0, hz - 560, v.x1 - v.x0, 980);
  // rolling billows along the horizon
  const span = L.vertical ? 1700 : 3400;
  for (let i = 0; i < 54; i++) {
    const r = 120 + 280 * hash(i * 1.9);
    const drift = t * (24 + 30 * hash(i * 2.3)) * (L.vertical ? 1 : -1);
    const x = ((((hash(i * 4.7) * span + drift) % span) + span) % span) - (L.vertical ? 300 : 700);
    const y = (L.vertical ? hz - 200 + 1100 * hash(i * 6.6) : hz - 30 - 300 * Math.pow(hash(i * 3.1), 1.4)) + 24 * Math.sin(t * 0.37 + i);
    const a = 0.07 + 0.1 * hash(i * 8.8);
    const q = f.createRadialGradient(x, y, 0, x, y, r);
    q.addColorStop(0, rgba(PAL.fog, a));
    q.addColorStop(0.55, rgba(PAL.fog, a * 0.5));
    q.addColorStop(1, rgba(PAL.fog, 0));
    f.fillStyle = q;
    f.fillRect(x - r, y - r, 2 * r, 2 * r);
  }
  // the front: everything on his side of it is fog
  f.globalCompositeOperation = 'destination-in';
  const fm = L.vertical ? f.createLinearGradient(0, front + soft, 0, front - soft) : f.createLinearGradient(front - soft, 0, front + soft, 0);
  fm.addColorStop(0, 'rgba(0,0,0,0)');
  fm.addColorStop(1, 'rgba(0,0,0,1)');
  f.fillStyle = fm;
  f.fillRect(v.x0, v.y0, v.x1 - v.x0, v.y1 - v.y0);
  c.save();
  c.setTransform(1, 0, 0, 1, 0, 0);
  c.globalAlpha = clamp(dens, 0, 1);
  c.drawImage(sheet, 0, 0, W, H);
  c.restore();
}
export function rainfall(g: G) {
  const {c, t, W, H} = g;
  const a = rain(t);
  if (a < 0.01) return;
  g.c.setTransform(1, 0, 0, 1, 0, 0);
  const n = 520, k = W / 1920;
  c.save();
  c.lineCap = 'round';
  for (let i = 0; i < n; i++) {
    const sp = (1500 + hash(i * 1.3) * 900) * k;
    const len = (16 + hash(i * 2.9) * 26) * k;
    const yy = (hash(i * 5.1) * (H + 200) + t * sp) % (H + 200) - 100;
    const xx = ((hash(i * 7.7) * W * 1.3 - yy * 0.18) % (W * 1.3) + W * 1.3) % (W * 1.3) - W * 0.15;
    const al = a * (0.12 + 0.28 * hash(i * 3.7));
    c.strokeStyle = rgba([190, 200, 225], al);
    c.lineWidth = (0.8 + hash(i) * 1.1) * k;
    c.beginPath();
    c.moveTo(xx, yy);
    c.lineTo(xx - len * 0.18, yy + len);
    c.stroke();
  }
  c.restore();
}

function frostTex() {
  return once('frost', 1024, 256, (ctx, w, h) => {
    ctx.strokeStyle = 'rgba(220,240,255,0.9)';
    ctx.lineCap = 'round';
    const branch = (x: number, y: number, a: number, len: number, depth: number, s: number) => {
      if (depth > 5 || len < 3) return;
      const x2 = x + Math.cos(a) * len, y2 = y + Math.sin(a) * len;
      ctx.lineWidth = Math.max(0.5, 2.2 - depth * 0.4);
      ctx.beginPath();
      ctx.moveTo(x, y);
      ctx.lineTo(x2, y2);
      ctx.stroke();
      branch(x2, y2, a + 0.5 + hash(s) * 0.3, len * 0.62, depth + 1, s * 1.7 + 1);
      branch(x2, y2, a - 0.5 - hash(s + 3) * 0.3, len * 0.62, depth + 1, s * 2.3 + 2);
      branch(x2, y2, a + (hash(s + 9) - 0.5) * 0.3, len * 0.7, depth + 1, s * 1.3 + 5);
    };
    for (let i = 0; i < 70; i++) branch(hash(i * 3.1) * w, h * (0.25 + hash(i * 1.7) * 0.6), -Math.PI / 2 + (hash(i * 9.3) - 0.5) * 2.4, 18 + hash(i) * 28, 0, i + 1);
  });
}
// "cool, cool, cool": frost creeps from the wall's base across the ground toward her, one word at a time
export function frost(g: G) {
  const {c, L, t} = g;
  const reach = frostReach(t);
  if (reach < 0.01) return;
  stage(g, 1);
  const tex = frostTex();
  c.save();
  if (!L.vertical) {
    const x1 = L.wall.x0 - L.wall.side + 30, span = 620;
    const x0 = x1 - span * reach;
    c.beginPath();
    c.moveTo(x1, L.home.y - 14);
    for (let y = L.home.y - 14; y <= L.home.y + 120; y += 10) c.lineTo(x0 + 26 * noise1(y / 12 + reach * 9, 3), y);
    c.lineTo(x1, L.home.y + 120);
    c.closePath();
    c.clip();
    c.globalAlpha = 0.55;
    c.drawImage(tex, x1 - span, L.home.y - 20, span, 150);
    const sheen = c.createLinearGradient(x0, 0, x1, 0);
    sheen.addColorStop(0, 'rgba(180,220,255,0)');
    sheen.addColorStop(1, 'rgba(180,220,255,0.16)');
    c.globalAlpha = 1;
    c.fillStyle = sheen;
    c.fillRect(x0, L.home.y - 20, x1 - x0, 150);
  } else {
    const y0 = L.wall.base, span = 560;
    const y1 = y0 + span * reach;
    c.beginPath();
    c.moveTo(-100, y0);
    for (let x = -100; x <= 1180; x += 12) c.lineTo(x, y1 + 30 * noise1(x / 14 + reach * 9, 3));
    c.lineTo(1180, y0);
    c.closePath();
    c.clip();
    c.globalAlpha = 0.5;
    c.save();
    c.translate(540, y0 + span / 2);
    c.rotate(Math.PI / 2);
    c.drawImage(tex, -span / 2, -640, span, 1280);
    c.restore();
  }
  c.restore();
  glow(g, L.vertical ? 540 : L.wall.x0 - 200, L.vertical ? L.wall.base + 60 : L.home.y + 10, 320, [170, 210, 255], 0.12 * reach);
}

// the light the wall throws back onto her side: red from the 429, candy from the cracks in the finale
export function spill(g: G, x: number, y: number, r: number, t: number) {
  const red = (t > T.drop ? 0.55 + 0.45 * sstep(T.drop, T.drop + 0.8, t) : 0) * (1 - thaw(t));
  const cand = sstep(T.final - 0.4, T.final + 0.4, t) * (1 - sstep(T.outro + 1, T.welcome, t));
  if (red > 0.01) glow(g, x, y, r, PAL.red, 0.1 * red * (0.8 + 0.4 * band(t, 3)));
  if (cand > 0.01)
    for (let i = 0; i < 6; i++) {
      const b = band(t, 4 + i * 7);
      glow(g, x + (i - 2.5) * r * 0.35, y + Math.sin(t * 2 + i) * 30, r * 0.8, candy(i * 2), 0.14 * cand * (0.3 + b) * (0.6 + 0.6 * beatPulse(t)));
    }
}
