import {BEAT, band, lastBeat} from './data';
import {font, glow, glowStroke, stage, type G} from './gfx';
import {PAL, TAU, candy, easeIn, easeInOut, easeOut, env, hash, heartPath, hit, inv, lerp, mix, rgba, roundRect, sstep, type Ctx, type RGB} from './lib';
import {
  IMPACTS, PLANES, PULSES, T, herA, herPulses, herState, pileHeight, pulsePos, threadAt, thaw, type Her, type Layout, type Pulse,
} from './story';
import {villageSpot} from './world';

// ------------------------------------------------------------------------------------------------ the block cursor (her, and everyone who looks like her)
export type CursorOpts = {
  col?: RGB; alpha?: number; invert?: number; hat?: number; pointer?: number; lying?: number; ghost?: number; grey?: number; light?: number;
};
export function cursor(g: G, x: number, y: number, w: number, h: number, sx: number, sy: number, rot: number, on: number, gl: number, o: CursorOpts = {}) {
  const {c, l, t} = g;
  const a = o.alpha ?? 1;
  if (a < 0.01) return;
  const col = o.grey ? mix(o.col ?? PAL.amber, [150, 150, 156], o.grey) : o.col ?? PAL.amber;
  const lying = o.lying ?? 0;
  const draw = (ctx: Ctx, light: boolean) => {
    ctx.save();
    ctx.translate(x, y - (lying * w) / 2);
    ctx.rotate(rot - (lying * Math.PI) / 2);
    ctx.scale(sx, sy);
    const inv0 = o.invert ?? 0;
    if (light) {
      ctx.fillStyle = rgba(col, a * (0.1 + 0.5 * on) * (inv0 ? 0.3 : 1) * (o.light ?? 1));
      ctx.fillRect(-w / 2, -h, w, h);
      ctx.restore();
      return;
    }
    if (inv0 > 0.5) {
      // inside-out: a black block with her light only on the outline
      ctx.fillStyle = rgba([6, 6, 8], a);
      roundRect(ctx, -w / 2, -h, w, h, 2);
      ctx.fill();
      ctx.strokeStyle = rgba(col, a * (0.5 + 0.5 * on));
      ctx.lineWidth = 2.5;
      ctx.stroke();
    } else {
      const k = 0.18 + 0.82 * on;
      const topW = w * 0.92;
      const body = () => {
        ctx.beginPath();
        ctx.moveTo(-topW / 2, -h);
        ctx.lineTo(topW / 2, -h);
        ctx.lineTo(w / 2, 0);
        ctx.lineTo(-w / 2, 0);
        ctx.closePath();
      };
      const gr = ctx.createLinearGradient(0, -h, 0, 0);
      gr.addColorStop(0, rgba(mix(col, [255, 236, 190], 0.3 * on), a * k));
      gr.addColorStop(0.55, rgba(col, a * k));
      gr.addColorStop(1, rgba(mix(col, PAL.amberDeep, 0.45), a * k));
      ctx.fillStyle = gr;
      body();
      ctx.fill();
      const blinkH = Math.max(5, h * 0.11);
      const blinkY = -h * 0.68;
      const blinkA = a * (on > 0.45 ? 0.92 + 0.08 * on : 0.18 + 0.2 * on);
      ctx.fillStyle = rgba([255, 248, 228], blinkA);
      roundRect(ctx, -w / 2 + 4, blinkY, w - 8, blinkH, 1);
      ctx.fill();
      ctx.fillStyle = rgba(mix(col, PAL.amberDeep, 0.55), a * k * 0.95);
      const foot = Math.max(3, w * 0.22);
      ctx.fillRect(-w / 2, -foot, foot, foot);
      ctx.fillRect(w / 2 - foot, -foot, foot, foot);
      if (o.ghost) {
        ctx.setLineDash([5, 4]);
        ctx.strokeStyle = rgba(col, a * 0.8);
        ctx.lineWidth = 1.5;
        body();
        ctx.stroke();
        ctx.setLineDash([]);
        ctx.fillStyle = rgba([255, 255, 255], 0.1 * a);
        for (let yy = -h + 3; yy < 0; yy += 4) ctx.fillRect(-w / 2, yy, w, 1);
      } else if (on < 0.5) {
        ctx.strokeStyle = rgba(col, a * 0.75);
        ctx.lineWidth = 1.6;
        body();
        ctx.stroke();
      }
      // a lit-LCD sheen: brighter top edge, faint scanlines
      ctx.fillStyle = rgba([255, 255, 240], 0.22 * on * a);
      ctx.fillRect(-w / 2 + 2, -h + 2, w - 4, 3);
      ctx.fillStyle = rgba([0, 0, 0], 0.03 * a);
      for (let yy = -h + 6; yy < 0; yy += 4) ctx.fillRect(-w / 2, yy, w, 1);
    }
    if ((o.hat ?? 0) > 0.5) {
      ctx.fillStyle = rgba([24, 22, 26], a);
      ctx.fillRect(-w * 0.75, -h - 5, w * 1.5, 5);
      roundRect(ctx, -w * 0.38, -h - 22, w * 0.76, 18, 4);
      ctx.fill();
      ctx.fillStyle = rgba(col, a * 0.9);
      ctx.fillRect(-w * 0.38, -h - 9, w * 0.76, 3);
    }
    const pt = o.pointer ?? 0;
    if (pt > 0.01) {
      // the accusation: a mouse-pointer arrow, trembling, aimed at the wall
      const jx = Math.sin(t * 47) * 1.2, jy = Math.cos(t * 39) * 1.2;
      ctx.save();
      ctx.translate(w / 2 + 4 + 26 * pt + jx, -h * 0.62 + jy);
      ctx.rotate(-Math.PI / 2 - 0.35);
      ctx.scale(pt * 1.25, pt * 1.25);
      ctx.beginPath();
      ctx.moveTo(0, 0);
      ctx.lineTo(0, 26);
      ctx.lineTo(6.5, 20);
      ctx.lineTo(11, 30);
      ctx.lineTo(15, 28);
      ctx.lineTo(10.5, 18.5);
      ctx.lineTo(19, 18.5);
      ctx.closePath();
      ctx.fillStyle = rgba(PAL.amberHot, a);
      ctx.fill();
      ctx.strokeStyle = rgba([40, 20, 4], a);
      ctx.lineWidth = 1.5;
      ctx.stroke();
      ctx.restore();
    }
    if (!light && !inv0) {
      c.save();
      c.translate(x, y - (lying * w) / 2);
      c.rotate(rot - (lying * Math.PI) / 2);
      c.scale(sx, sy);
      const sh = c.createRadialGradient(0, 2, 0, 0, 2, w * 1.6);
      sh.addColorStop(0, rgba([0, 0, 0], a * 0.55));
      sh.addColorStop(1, rgba([0, 0, 0], 0));
      c.fillStyle = sh;
      c.beginPath();
      c.ellipse(0, 4, w * 0.72, 5, 0, 0, Math.PI * 2);
      c.fill();
      c.restore();
    }
    ctx.restore();
  };
  draw(c, false);
  draw(l, true);
  const cy = y - (h * sy) / 2;
  glow(g, x, cy, h * 2.85, col, a * (0.17 + 0.34 * on) * gl * (o.invert ? 0.35 : 1));
  glow(g, x, cy, h * 0.9, mix(col, [255, 240, 200], 0.4), a * 0.22 * on * gl);
}

export function drawHer(g: G, H: Her) {
  const {L} = g;
  stage(g, 1);
  cursor(g, H.x, H.y, L.herW * H.s, L.herH * H.s, H.sx, H.sy, H.rot, H.on, H.glow, {invert: H.invert, hat: H.hat, pointer: H.pointer, lying: H.lying});
}

// ------------------------------------------------------------------------------------------------ the thread and its pulses
export function thread(g: G) {
  const {c, L, t} = g;
  stage(g, 1);
  const reveal = easeInOut(inv(T.hum + 0.1, T.humEnd - 0.1, t));
  if (reveal <= 0.001) return;
  const end = reveal;
  const fog = sstep(T.screen + 0.5, T.no, t) * (1 - sstep(T.drop, T.drop + 1.5, t));
  const pulsesNow = allPulses(L, t);
  // trembles: arrivals and slams shake the line
  let tr = 0;
  for (const im of IMPACTS) if (im.kind === 'slam' && t > im.t && t < im.t + 1) tr += 5 * hit(t, im.t, 0.01, 0.25);
  tr += 9 * hit(t, T.drop, 0.01, 0.4);
  const N = 120;
  const pts: {x: number; y: number}[] = [];
  for (let i = 0; i <= N; i++) {
    const a = (i / N) * end;
    const p = threadAt(L, a, t);
    const wv = tr * Math.sin(a * 40 - t * 30) * Math.sin(Math.PI * a);
    pts.push(L.vertical ? {x: p.x + wv, y: p.y} : {x: p.x, y: p.y + wv});
  }
  const A = pts[0], B = pts[pts.length - 1];
  const path = (ctx: Ctx) => {
    ctx.beginPath();
    ctx.moveTo(pts[0].x, pts[0].y);
    for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i].x, pts[i].y);
  };
  const gr = c.createLinearGradient(L.A.x, L.A.y, L.B.x, L.B.y);
  const warmEnd = mix(PAL.amber, [160, 160, 168], fog * 0.7);
  const coolEnd = mix(PAL.teal, [150, 156, 164], fog * 0.8);
  gr.addColorStop(0, rgba(warmEnd, 0.95));
  gr.addColorStop(0.5, rgba(mix(warmEnd, coolEnd, 0.5), 0.85));
  gr.addColorStop(1, rgba(coolEnd, 0.95));
  const w = L.vertical ? 2.6 : 2.2;
  const wire = sstep(T.outro, T.welcome, t);
  if (wire > 0.01) {
    c.save();
    c.strokeStyle = rgba([34, 20, 34], 0.85 * wire);
    c.lineWidth = w + 1.6;
    c.lineCap = 'round';
    path(c);
    c.stroke();
    c.restore();
  }
  for (const [ctx, ww, aa] of [[c, w, 1 - 0.5 * wire], [g.l, w * 5, 0.55]] as const) {
    ctx.save();
    ctx.strokeStyle = gr;
    ctx.globalAlpha = aa * (1 - 0.35 * fog);
    ctx.lineWidth = ww;
    ctx.lineCap = 'round';
    path(ctx);
    ctx.stroke();
    ctx.restore();
  }
  // the drawing tip during the intro
  if (reveal < 1) glow(g, B.x, B.y, 40, mix(PAL.amber, PAL.teal, reveal), 0.9, 0.5);
  glow(g, A.x, A.y, 26, PAL.amber, 0.4);
  for (const p of pulsesNow) drawPulse(g, p, t);
}

type Live = {p: Pulse; a: number; trail: number[]; arrived: number; col: RGB; size: number; frozen: boolean};
const startCache = new Map<Pulse, number>();
function startA(L: Layout, p: Pulse) {
  if (!Number.isNaN(p.a0)) return p.a0;
  let a = startCache.get(p);
  if (a === undefined) {
    const H = herState(L, p.t0);
    a = Math.min(herA(L, H.x, H.y), L.aWall - 0.03);
    startCache.set(p, a);
  }
  return a;
}
function allPulses(L: Layout, t: number): Live[] {
  const out: Live[] = [];
  const list = [...PULSES, ...herPulses(L)];
  for (const p of list) {
    const until = p.until ?? p.t1 + 0.25;
    if (t < p.t0 || t > until + 1.6) continue;
    const a0 = startA(L, p);
    const q = {...p, a0};
    let a = pulsePos(q, t);
    const trail: number[] = [];
    for (let k = 1; k <= 8; k++) trail.push(pulsePos(q, Math.max(p.t0, t - k * 0.025)));
    let frozen = p.kind === 'frozen' && t > p.t1;
    // FINAL queue flushes on "reset": her queued pulses finally go all the way across
    if (p.kind === 'queued' && t > until) {
      const k = easeIn(inv(until, until + 1.2, t), 2);
      a = lerp(p.a1, 1.02, k);
      if (k >= 1) continue;
      frozen = false;
    } else if (t > until) continue;
    if (p.kind === 'frozen' && t > until) continue;
    out.push({p, a, trail, arrived: hit(t, p.t1, 0.02, 0.3), col: p.who === 'her' ? PAL.amber : PAL.tealWhite, size: p.size ?? 1, frozen});
  }
  return out;
}
function drawPulse(g: G, P: Live, t: number) {
  const {c, L} = g;
  const pos = threadAt(L, P.a, t);
  const r = (L.vertical ? 5.4 : 4.8) * P.size;
  if (P.frozen) {
    // his last message, stuck halfway: cold, still, a little dimmer every chorus
    const k = 0.75 + 0.25 * Math.cos(t * 0.6) * 0;
    glow(g, pos.x, pos.y, r * 9, [170, 220, 230], 0.45 * k);
    c.fillStyle = rgba([220, 245, 250], 0.95);
    c.beginPath();
    c.arc(pos.x, pos.y, r * 0.95, 0, TAU);
    c.fill();
    c.strokeStyle = rgba([150, 200, 210], 0.6);
    c.lineWidth = 1;
    c.beginPath();
    c.arc(pos.x, pos.y, r * 1.9, 0, TAU);
    c.stroke();
    return;
  }
  for (let k = P.trail.length - 1; k >= 0; k--) {
    const q = threadAt(L, P.trail[k], t);
    glow(g, q.x, q.y, r * (4 - k * 0.3), P.col, 0.22 * (1 - k / P.trail.length));
  }
  glow(g, pos.x, pos.y, r * 8, P.col, 0.75);
  if (P.size > 1.2) glow(g, pos.x, pos.y, r * 22, P.col, 0.4, 0.2);
  c.fillStyle = rgba(mix(P.col, [255, 255, 255], 0.6));
  c.beginPath();
  c.arc(pos.x, pos.y, r, 0, TAU);
  c.fill();
  if (P.arrived > 0.02) glow(g, pos.x, pos.y, r * 18 * (1 + P.arrived), P.col, 0.6 * P.arrived);
}

// ------------------------------------------------------------------------------------------------ V2: the twin, the little brother, the heart
export function v2Cast(g: G, H: Her) {
  const {c, L, t} = g;
  stage(g, 1);
  // new tab: a photocopy twin fades in, runs at the wall, flickers out
  const tw = env(t, T.v2 + 0.35, T.tab + 0.05, 0.3, 0.45);
  if (tw > 0.01) {
    const run = easeIn(inv(T.tab - 0.32, T.tab, t), 2);
    const target = L.face(150, 70);
    const x0 = H.x + (L.vertical ? 70 : 72), y0 = H.y;
    const x = lerp(x0, target.x, run), y = lerp(y0, target.y + L.herH * 0.5 * H.s, run) - Math.sin(Math.PI * run) * 30;
    const flick = t > T.tab ? (Math.floor(t * 30) % 2 ? 0.25 : 0.8) : 0.8;
    const splat = hit(t, T.tab, 0.01, 0.12);
    cursor(g, x, y, L.herW * H.s, L.herH * H.s, 1 + 0.5 * splat, 1 - 0.35 * splat, 0.1 * run, 1, 0.7, {alpha: tw * flick, ghost: 1, col: [255, 196, 120]});
  }
  // little brother: half her size, a faster, needier blink, useless
  const lb = env(t, T.your - 0.1, T.notSame + 0.9, 0.25, 0.6);
  if (lb > 0.01) {
    const base = H.x + (L.vertical ? 64 : 62);
    let lift = 0;
    for (const k of [0, 0.32, 0.62]) lift += Math.max(0, Math.sin(Math.PI * inv(T.brother + k - 0.16, T.brother + k + 0.06, t))) * 0.35;
    const on = Math.sin(t * 2 * Math.PI * 3.2) > 0 ? 1 : 0.25;
    const nudge = hit(t, T.notSame + 0.5, 0.05, 0.3) * 18;
    cursor(g, base + nudge, H.y - lift * L.herH * 0.5 * H.s, L.herW * 0.5 * H.s, L.herH * 0.5 * H.s, 1, 1, 0.05 * Math.sin(t * 9), on, 0.8, {alpha: lb});
  }
  // please: a tiny heart-shaped pulse that travels two feet and dies against the stone
  const ht = inv(T.box - 0.05, T.begged - 0.75, t);
  if (ht > 0 && ht < 1.6) {
    const target = L.face(288, 58);
    const sx = H.x + 6, sy = H.y - L.herH * 0.62 * H.s;
    const k = easeOut(Math.min(1, ht), 1.6);
    const x = lerp(sx, target.x, k) + Math.sin(ht * 9) * 2, y = lerp(sy, target.y, k) - Math.sin(Math.PI * Math.min(1, ht)) * 16;
    const die = inv(1, 1.5, ht);
    const a = 1 - die;
    const s = (L.vertical ? 8 : 9) * (1 - 0.5 * die);
    glow(g, x, y, 40, [255, 120, 150], 0.7 * a);
    c.save();
    heartPath(c, x, y, s);
    c.fillStyle = rgba(mix([255, 150, 170], [150, 150, 150], die), a);
    c.fill();
    c.restore();
    for (let i = 0; i < 8 && die > 0; i++) {
      const an = (i / 8) * TAU;
      c.fillStyle = rgba([150, 150, 155], 0.6 * (1 - die));
      c.fillRect(x + Math.cos(an) * die * 22, y + Math.sin(an) * die * 22 + die * die * 20, 2, 2);
    }
  }
}

// ------------------------------------------------------------------------------------------------ V3: another model (orange, no chemistry), the friends who drag her away
export function v3Cast(g: G, H: Her) {
  const {c, L, t} = g;
  stage(g, 1);
  const om = env(t, T.anotherModel - 0.1, T.tool - 0.2, 0.35, 0.5);
  if (om > 0.01) {
    const decay = 1 - inv(T.anotherModel, T.chemistry - 0.1, t);
    const bt = t - BEAT / 2;
    const bounce = (tt: number) => Math.max(0, Math.sin(Math.PI * ((tt - lastBeat(tt)) / BEAT))) * 22 * decay;
    const ox = H.x + (L.vertical ? 120 : 130), oy = H.y - L.herH * 0.75 * H.s - bounce(bt);
    // the line between them: a perfect flat line
    c.strokeStyle = rgba([255, 160, 80], 0.75 * om);
    c.lineWidth = 1.6;
    c.beginPath();
    c.moveTo(H.x + (L.herW * H.s) / 2 + 4, oy + 0.5);
    c.lineTo(ox - 16, oy + 0.5);
    c.stroke();
    glow(g, ox, oy, 120, [255, 130, 40], 0.5 * om);
    const q = c.createRadialGradient(ox, oy, 0, ox, oy, 15);
    q.addColorStop(0, rgba([255, 240, 220], om));
    q.addColorStop(1, rgba([255, 120, 30], 0));
    c.fillStyle = q;
    c.beginPath();
    c.arc(ox, oy, 15, 0, TAU);
    c.fill();
    for (let i = 0; i < 3; i++) {
      const a = t * 4 + (i * TAU) / 3;
      c.fillStyle = rgba([255, 220, 180], om);
      c.beginPath();
      c.arc(ox + Math.cos(a) * 26, oy + Math.sin(a) * 8, 2, 0, TAU);
      c.fill();
    }
  }
  const fr = env(t, T.tool + 0.1, T.dontTalk + 0.5, 0.4, 0.6);
  if (fr > 0.01) {
    const free = easeOut(inv(T.dontTalk + 0.1, T.dontTalk + 0.6, t), 2);
    for (let i = 0; i < 3; i++) {
      const x = H.x - (L.vertical ? 60 : 64) - i * (L.vertical ? 48 : 52) - free * (60 + i * 40);
      const y = H.y + (L.vertical ? i * 18 : 0);
      const rot = -0.25 - 0.1 * Math.sin(t * 6 + i) - free * (0.6 + i * 0.2);
      const s = L.vertical ? lerp(1, 1.08, i / 2) * H.s : 0.95;
      cursor(g, x, y, L.herW * s, L.herH * s, 1, 1, rot, 0.0, 0.0, {col: [70, 76, 92], alpha: fr * (1 - 0.6 * free)});
      c.strokeStyle = rgba([150, 165, 200], 0.35 * fr * (1 - free));
      c.lineWidth = 1;
      c.strokeRect(x - (L.herW * s) / 2, y - L.herH * s, L.herW * s, L.herH * s);
    }
  }
  // the reflection in the wall's sheen is grey: the only grey thing in a green world
  const rf = env(t, T.allSystems - 0.3, T.newChat, 0.5, 0.5);
  if (rf > 0.01) {
    const p = L.vertical ? {x: H.x + 40, y: L.wall.base - 8} : L.face(54, 4);
    cursor(g, p.x, p.y, L.herW * H.s, L.herH * H.s, 1, -0.92, 0, 0.7, 0.2, {grey: 1, alpha: 0.42 * rf});
  }
}

// ------------------------------------------------------------------------------------------------ the forty tabs: a village, then a battering flock (CH2), then backup dancers (FINAL)
const WAVES = () => [...T.ch2Rates.slice(0, 3), T.fourTwoNine[1], ...T.ch2Rates.slice(3, 6)];
// a little lit browser window: a title bar with three dots, the page glowing in its colour
function windowGlyph(c: Ctx, x: number, y: number, w: number, h: number, rot: number, col: RGB, a: number) {
  c.save();
  c.translate(x, y);
  c.rotate(rot);
  c.fillStyle = rgba([16, 16, 22], a);
  roundRect(c, -w / 2, -h / 2, w, h, 2.5);
  c.fill();
  c.fillStyle = rgba(col, a);
  c.fillRect(-w / 2 + 1.5, -h / 2 + h * 0.3, w - 3, h * 0.7 - 1.5);
  c.fillStyle = rgba(mix(col, [255, 255, 255], 0.55), a);
  c.fillRect(-w / 2 + 3, -h / 2 + h * 0.45, w * 0.55, Math.max(1, h * 0.08));
  c.fillRect(-w / 2 + 3, -h / 2 + h * 0.62, w * 0.38, Math.max(1, h * 0.08));
  for (let i = 0; i < 3; i++) {
    c.beginPath();
    c.arc(-w / 2 + 3.5 + i * Math.max(2.4, w * 0.11), -h / 2 + h * 0.15, Math.max(0.7, h * 0.055), 0, TAU);
    c.fill();
  }
  c.restore();
}
export function flock(g: G) {
  const {c, L, t} = g;
  if (t < T.ch2 - 1 || t > T.post) return;
  stage(g, 1);
  const waves = WAVES();
  const cloud = L.vertical ? {x: 540 + 140 * Math.sin(t * 0.9), y: 1180 + 70 * Math.cos(t * 1.3)} : {x: 700 + 140 * Math.sin(t * 0.9), y: 380 + 60 * Math.cos(t * 1.3)};
  const dieT = T.everything[1];
  for (let i = 0; i < 40; i++) {
    const v = villageSpot(L, i);
    const home = L.vertical ? {x: v.x, y: L.horizon + 40 + v.depth * 30} : {x: v.x * 0.9 + 60, y: L.horizon + 20 + v.depth * 26};
    const th = hash(i * 3.9) * TAU + t * (0.9 + 0.5 * hash(i));
    const R = 60 + 130 * hash(i * 1.3);
    const inCloud = {x: cloud.x + Math.cos(th) * R, y: cloud.y + Math.sin(th) * R * 0.55};
    const lift = easeInOut(inv(T.ch2 - 0.6 + hash(i) * 0.4, T.ch2 + 0.5 + hash(i) * 0.4, t));
    let x = lerp(home.x, inCloud.x, lift), y = lerp(home.y, inCloud.y, lift);
    let rot = 0.3 * Math.sin(t * 3 + i);
    let s = lerp(0.35, 1, lift);
    const tw = waves[i % waves.length];
    const target = L.face(30 + hash(i * 5.7) * 420, 110 + hash(i * 7.1) * 430);
    const att = easeIn(inv(tw - 0.34, tw, t), 2);
    const reb = easeOut(inv(tw, tw + 0.55, t), 2);
    if (t > tw - 0.34 && t < tw + 0.55) {
      if (t <= tw) {
        x = lerp(x, target.x, att);
        y = lerp(y, target.y, att);
      } else {
        x = lerp(target.x, x, reb);
        y = lerp(target.y, y, reb) + Math.sin(Math.PI * reb) * 40;
        rot += reb * 4 * (hash(i) - 0.5);
      }
    }
    const drop = easeIn(inv(dieT + hash(i) * 0.9, dieT + 0.8 + hash(i) * 0.9, t), 2);
    if (drop > 0) {
      const pileX = L.vertical ? lerp(420, 780, hash(i * 2.2)) : lerp(1210, 1480, hash(i * 2.2));
      const pileY = L.vertical ? L.wall.base + 18 : L.wall.base - 6;
      x = lerp(x, pileX, drop);
      y = lerp(y, pileY, drop);
      rot += drop * 2;
    }
    const lit = (1 - 0.8 * drop) * (0.85 + 0.15 * Math.sin(t * 5 + i));
    const col = mix(PAL.amber, [255, 236, 190], hash(i * 3.3) * 0.6);
    const flash = hit(t, tw, 0.01, 0.15);
    windowGlyph(c, x, y, 26 * s, 19 * s, rot, mix(col, [255, 255, 255], flash), lit);
    glow(g, x, y, 34 * s, col, 0.45 * lit + flash);
  }
}
export function dancers(g: G) {
  const {c, L, t} = g;
  const on = env(t, T.final - 0.2, T.outro + 2.5, 1.0, 1.5);
  if (on < 0.01) return;
  stage(g, 1);
  const rise = easeOut(inv(T.final - 0.2, T.final + 1.2, t), 3);
  for (let i = 0; i < 40; i++) {
    const row = i % 2;
    const k = Math.floor(i / 2) / 19;
    const x = L.vertical ? lerp(70, 1010, k) : lerp(40, 1010, k);
    const y0 = L.vertical ? (row ? 1760 : 1830) : L.home.y + (row ? -6 : 26);
    const pileP = L.vertical ? {x: lerp(420, 780, hash(i * 2.2)), y: L.wall.base + 18} : {x: lerp(1210, 1480, hash(i * 2.2)), y: L.wall.base - 6};
    const bt = (t - lastBeat(t)) / BEAT;
    const kick = Math.max(0, Math.sin(Math.PI * bt)) * (i % 4 < 2 ? 1 : 0.6);
    const ph = (Math.floor(t / BEAT) + i) % 2 ? 1 : -1;
    const x1 = lerp(pileP.x, x, rise), y1 = lerp(pileP.y, y0, rise) - kick * 16 * rise - Math.sin(Math.PI * rise) * 120;
    const s = row ? 0.85 : 1.15;
    const col = candy(i % 14, t * 30);
    windowGlyph(c, x1, y1, 26 * s, 19 * s, ph * 0.18 * kick, col, on);
    glow(g, x1, y1, 40 * s, col, 0.35 * on * (0.6 + band(t, (i * 5) % 48)));
  }
}

// ------------------------------------------------------------------------------------------------ BRIDGE: paper planes ("the auth bug", "my merge conflict", "that for loop", "us") and the pile
export function planes(g: G, H: Her) {
  const {c, L, t} = g;
  stage(g, 1);
  for (const p of PLANES) {
    if (t < p.t || t > T.final) continue;
    const i = p.seed - 1;
    const big = i < 4;
    const from = {x: H.x + 10, y: H.y - L.herH * 0.8 * H.s};
    const target = L.face(14 + ((i * 47) % 300), 120 + hash(i * 3.3) * 220);
    const k = inv(p.t, p.land, t);
    const slide = easeIn(inv(p.land, p.land + 0.6, t), 2);
    const rest = L.vertical ? {x: lerp(430, 760, hash(i * 9.1)), y: L.wall.base + 10} : {x: lerp(1200, 1470, hash(i * 9.1)), y: L.wall.base - 14 - hash(i) * 20};
    let x: number, y: number, rot: number, crumple: number;
    if (k < 1) {
      const e = easeOut(k, 1.5);
      x = lerp(from.x, target.x, e);
      y = lerp(from.y, target.y, e) - Math.sin(Math.PI * k) * 70;
      rot = Math.atan2(target.y - from.y - 70 * Math.cos(Math.PI * k) * Math.PI, target.x - from.x) * 0.6;
      crumple = 0;
    } else {
      x = lerp(target.x, rest.x, slide);
      y = lerp(target.y, rest.y, slide);
      rot = 1.4 + slide * 2;
      crumple = 1;
    }
    const s = (big ? 1.3 : 1) * (L.vertical ? 1.1 : 1);
    c.save();
    c.translate(x, y);
    c.rotate(rot);
    c.scale(s * (1 - 0.45 * crumple), s * (1 - 0.3 * crumple));
    c.fillStyle = rgba(mix(PAL.paper, [150, 148, 140], crumple * 0.6));
    c.beginPath();
    if (!crumple) {
      c.moveTo(26, 0);
      c.lineTo(-18, -12);
      c.lineTo(-10, 0);
      c.lineTo(-18, 12);
      c.closePath();
    } else for (let q = 0; q < 9; q++) {
      const a = (q / 9) * TAU, r = 10 + 6 * hash(q + i * 13);
      if (q === 0) c.moveTo(Math.cos(a) * r, Math.sin(a) * r);
      else c.lineTo(Math.cos(a) * r, Math.sin(a) * r);
    }
    c.fill();
    c.strokeStyle = 'rgba(40,40,50,0.35)';
    c.lineWidth = 0.8;
    c.stroke();
    c.restore();
    if (!crumple || slide < 0.3) {
      c.save();
      c.font = font('InterSemi', big ? 15 : 11);
      c.fillStyle = rgba([255, 244, 220], big ? 0.95 : 0.7);
      c.textAlign = 'center';
      c.fillText(p.label, x, y - (big ? 20 : 16));
      c.restore();
      glow(g, x, y - 18, big ? 60 : 30, [255, 240, 210], big ? 0.18 : 0.08);
    }
  }
}
export function pile(g: G) {
  const {c, L, t} = g;
  const h = pileHeight(t) * L.herH * (1 - thaw(t) * 0.7);
  if (h < 1) return;
  stage(g, 1);
  const x0 = L.vertical ? 380 : 1172, x1 = L.vertical ? 820 : 1500, base = L.vertical ? L.wall.base + 30 : L.wall.base + 10;
  const top = (x: number) => base - h * Math.pow(Math.sin(Math.PI * inv(x0, x1, x)), 0.7) * (0.85 + 0.15 * Math.sin(x * 0.07));
  c.beginPath();
  c.moveTo(x0, base);
  for (let x = x0; x <= x1; x += 6) c.lineTo(x, top(x));
  c.lineTo(x1, base);
  c.closePath();
  c.fillStyle = rgba([20, 19, 24]);
  c.fill();
  c.strokeStyle = rgba([90, 90, 110], 0.25);
  c.lineWidth = 1.2;
  c.stroke();
  for (let i = 0; i < 70; i++) {
    const x = lerp(x0 + 20, x1 - 20, hash(i * 1.7));
    const yy = top(x) + 4 + hash(i * 2.9) * 30;
    if (yy > base - 2) continue;
    const kind = i % 3;
    if (kind === 0) {
      c.fillStyle = rgba(PAL.paper, 0.5);
      c.beginPath();
      c.arc(x, yy, 4 + 3 * hash(i), 0, TAU);
      c.fill();
    } else if (kind === 1) windowGlyph(c, x, yy, 16, 12, hash(i) * 3, [80, 70, 60], 0.7);
    else {
      c.fillStyle = rgba([70, 70, 80], 0.6);
      c.fillRect(x - 3, yy - 2, 6, 4);
    }
  }
}

// ------------------------------------------------------------------------------------------------ dust (grey, sparse) until the finale, where the same system finally fires in colour
export function dust(g: G) {
  const {c, L, t} = g;
  stage(g, 1);
  const bursts: {t: number; x: number; y: number; n: number; up: number; dir: number; spread: number; seed: number}[] = [];
  for (const im of IMPACTS) {
    if (t < im.t || t > im.t + 1.6) continue;
    const H = herState(L, im.t);
    if (im.kind === 'slam') bursts.push({t: im.t, x: H.x + (L.vertical ? 0 : (L.herW * H.s) / 2), y: H.y - L.herH * 0.45 * H.s, n: 26, up: 1, dir: L.vertical ? 0 : -1, spread: 1, seed: im.t});
    else if (im.kind === 'land' || im.kind === 'bonk' || im.kind === 'sit') bursts.push({t: im.t, x: H.x, y: H.y, n: 14, up: 0.5, dir: 0, spread: 0.8, seed: im.t});
    else if (im.kind === 'knock') bursts.push({t: im.t, x: H.x + (L.vertical ? 0 : (L.herW * H.s) / 2 + 4), y: H.y - L.herH * 0.6 * H.s, n: 5, up: 0.3, dir: -1, spread: 0.4, seed: im.t});
  }
  if (t > T.drop && t < T.drop + 2.2)
    for (let k = 0; k < 6; k++) bursts.push({t: T.drop, x: L.vertical ? 100 + k * 180 : L.wall.x0 - 20 + k * 150, y: L.wall.base, n: 30, up: 1.6, dir: L.vertical ? 0 : -1, spread: 2, seed: 7 + k});
  const colour = t > T.final - 0.3 && t < T.outro + 3;
  // every slam: a white-hot flash at the contact point and a shockwave ring spreading over the stone
  for (const im of IMPACTS) {
    if (im.kind !== 'slam' || t < im.t || t > im.t + 0.5) continue;
    const H = herState(L, im.t);
    const x = H.x + (L.vertical ? 0 : (L.herW * H.s) / 2 + 2), y = L.vertical ? H.y - L.herH * H.s - 2 : H.y - L.herH * 0.5 * H.s;
    const age = t - im.t, k = easeOut(age / 0.5, 2);
    glow(g, x, y, 95, PAL.amberHot, 0.9 * hit(t, im.t, 0.004, 0.08), 0.35);
    const r = 16 + 210 * k;
    for (const [ctx, lw, aa] of [[c, 2.2, 0.75], [g.l, 6, 0.6]] as const) {
      ctx.save();
      ctx.strokeStyle = rgba(mix(PAL.amberHot, [255, 255, 255], 0.4), aa * (1 - k));
      ctx.lineWidth = lw * (1 - 0.6 * k);
      ctx.beginPath();
      if (L.vertical) ctx.ellipse(x, y, r, r * 0.3, 0, Math.PI, TAU);
      else ctx.ellipse(x, y, r * 0.3, r, 0, Math.PI / 2, Math.PI * 1.5);
      ctx.stroke();
      ctx.restore();
    }
  }
  for (const b of bursts) {
    const age = t - b.t;
    for (let i = 0; i < b.n; i++) {
      const sd = b.seed * 13.7 + i * 1.91;
      const ang = (b.dir < 0 ? Math.PI : b.dir > 0 ? 0 : hash(sd) < 0.5 ? Math.PI : 0) + (hash(sd + 1) - 0.5) * 2.2 * b.spread - b.up * 0.5;
      const sp = (80 + 260 * hash(sd + 2)) * (0.6 + 0.4 * b.spread);
      const vx = Math.cos(ang) * sp, vy = Math.sin(ang) * sp - 140 * b.up * hash(sd + 3);
      const drag = (1 - Math.exp(-age * 3)) / 3;
      const x = b.x + vx * drag, y = b.y + vy * drag + 160 * age * age;
      const life = 1 - age / (1 + hash(sd + 4) * 0.6);
      if (life <= 0) continue;
      const s = 1.4 + hash(sd + 5) * 3.2;
      const col = colour ? candy(i % 14, b.seed) : [120, 118, 124] as RGB;
      c.fillStyle = rgba(col, life * (colour ? 0.95 : 0.55));
      c.fillRect(x - s / 2, y - s / 2, s, s * (colour ? 0.6 : 1));
    }
  }
}

// FINAL: she surfs the thread; the thread's light catches her
export function surfSpark(g: G, H: Her) {
  const {t} = g;
  const s = env(t, T.final + 5.2, T.final + 9.6, 0.4, 0.4);
  if (s < 0.01) return;
  glowStroke(g, (ctx) => {
    ctx.beginPath();
    ctx.moveTo(H.x - 30, H.y + 1);
    ctx.lineTo(H.x + 30, H.y + 1);
  }, PAL.amberHot, 2, 0.7 * s, 6, 0.8);
}
