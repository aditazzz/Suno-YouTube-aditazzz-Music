import {band, bass, beatPulse} from './data';
import {font, glow, glowStroke, stage, stoneTex, view, type G} from './gfx';
import {PAL, TAU, candy, clamp, easeIn, easeOut, env, hash, heartPath, hit, inv, lerp, mix, noise1, rgba, rng, sstep, surface, type Ctx, type RGB} from './lib';
import {CRACKS, ETCH, HOOKS, MARKS, T, echoes, leakLevel, thaw, wallDrop, type Crack, type Layout, type P} from './story';

// ------------------------------------------------------------------------------------------------ geometry
type Branch = {pts: P[]; len: number[]; w: number};
const CRACK_GEO = new Map<string, Branch[]>();
function crackGeo(L: Layout, c: Crack): Branch[] {
  const key = `${L.fmt}:${c.seed}`;
  const hit0 = CRACK_GEO.get(key);
  if (hit0) return hit0;
  const R = rng(c.seed * 7919 + 13);
  const o = origin(L, c);
  const out: Branch[] = [];
  // stone fractures: long straight runs with sharp kinks, few forks
  const grow = (x: number, y: number, a: number, len: number, w: number, depth: number) => {
    const pts: P[] = [{x, y}], cum = [0];
    let head = a, s = 0;
    while (s < len) {
      const step = 14 + R() * 24;
      if (R() < 0.22) head += (R() < 0.5 ? -1 : 1) * (0.35 + R() * 0.5);
      head = a + (head - a) * 0.75;
      const dir = head + (R() - 0.5) * 0.3;
      x += Math.cos(dir) * step;
      y += Math.sin(dir) * step;
      s += step;
      pts.push({x, y});
      cum.push(s);
      if (depth < 1 && s > len * 0.25 && R() < 0.1) grow(x, y, dir + (R() < 0.5 ? -1 : 1) * (0.5 + R() * 0.5), len * (0.2 + R() * 0.25), w * 0.55, depth + 1);
    }
    out.push({pts, len: cum, w});
  };
  // a body-slam leaves one hairline; bigger blows burst
  const hair = c.power < 1.2;
  const n = hair ? 1 + (R() < 0.3 ? 1 : 0) : 3 + Math.floor(R() * 3);
  const side = c.side && !L.vertical;
  for (let i = 0; i < n; i++) {
    const a = hair ? (side ? -0.9 + 1.8 * R() : TAU * R()) : (TAU * (i + R() * 0.6)) / n;
    grow(o.x, o.y, a, c.power * (hair ? 90 + R() * 130 : 80 + R() * 150) * (L.vertical ? 0.8 : 1), (hair ? 1.15 : 1.7) * c.power, 0);
  }
  CRACK_GEO.set(key, out);
  return out;
}
const origin = (L: Layout, c: Crack): P => (c.side && !L.vertical ? {x: L.wall.x0, y: L.wall.base - c.v} : L.face(c.u, c.v));

export const wallTop = (L: Layout, t: number) => {
  const melt = easeIn(inv(T.outro + 0.05, T.back - 0.2, t), 1.6);
  return lerp(L.wall.top, L.wall.base + 6, melt);
};
export const windowPos = (L: Layout) => (L.vertical ? {x: 540, y: 400, size: 190} : {x: 1560, y: 266, size: 196});
export const dotsHome = (L: Layout) => L.face(60, 150);
export const keyholePos = (L: Layout) => L.face(L.vertical ? 120 : 276, 240);
export const irisPos = (L: Layout) => (L.vertical ? {...L.face(-60, 520), r: 120} : {...L.face(556, 272), r: 118});

// ------------------------------------------------------------------------------------------------ the wall
export function wall(g: G) {
  const {c, L, t} = g;
  const dropK = wallDrop(t);
  if (dropK <= -0.999) return;
  const top0 = wallTop(L, t);
  if (top0 >= L.wall.base + 5 && t > T.back + 1.5) return;
  stage(g, 1);
  const v = view(g);
  const fallH = L.wall.base + (L.vertical ? 150 : 170);
  const dy = dropK * fallH;
  // its shadow arrives first, darkening the ground where it will land
  if (dropK < 0) {
    const k = easeIn(1 + dropK, 1.5);
    const sh = c.createLinearGradient(0, L.wall.base - 20, 0, L.wall.base + 60);
    sh.addColorStop(0, rgba([0, 0, 0], 0));
    sh.addColorStop(0.4, rgba([0, 0, 0], 0.55 * k));
    sh.addColorStop(1, rgba([0, 0, 0], 0));
    c.fillStyle = sh;
    c.fillRect(L.wall.x0 - L.wall.side - 60 * (1 - k), L.wall.base - 20, L.wall.x1 - L.wall.x0 + L.wall.side + 120, 80);
  }
  c.save();
  c.translate(0, dy);
  g.l.save();
  g.l.translate(0, dy);
  const {x0, x1, base, side, sideDrop} = L.wall;
  const top = top0;
  // motion blur while it falls: the leading edge smears over half a frame of travel, her lamp catches the edge
  if (dropK < 0 && dropK > -1) {
    glowStroke(g, (ctx) => {
      ctx.beginPath();
      ctx.moveTo(x0 - side, base + sideDrop);
      ctx.lineTo(Math.min(x1, v.x1 + 40), base);
    }, PAL.amber, 1.4, 0.5, 6, 0.35);
    const speed = (2 * fallH * (1 + dropK)) / (T.drop - T.ch1);
    const smear = Math.min(260, speed / 60);
    const sm = c.createLinearGradient(0, base, 0, base + smear);
    sm.addColorStop(0, rgba(PAL.stone, 0.85));
    sm.addColorStop(1, rgba(PAL.stone, 0));
    c.fillStyle = sm;
    c.fillRect(x0 - side, base, x1 - x0 + side, smear);
    const st = c.createLinearGradient(0, top - smear * 2, 0, top);
    st.addColorStop(0, rgba(PAL.stone, 0));
    st.addColorStop(1, rgba(PAL.stone, 0.6));
    c.fillStyle = st;
    c.fillRect(x0 - side, top - smear * 2, x1 - x0 + side, smear * 2);
  }
  // the face
  c.save();
  wallPath(c, L, top);
  c.clip();
  const tex = stoneTex();
  const pat = c.createPattern(tex, 'repeat');
  c.fillStyle = rgba(PAL.stone);
  c.fillRect(Math.max(v.x0, x0 - side), Math.max(v.y0 - dy, top), Math.min(v.x1, x1) - Math.max(v.x0, x0 - side), base + sideDrop - Math.max(v.y0 - dy, top));
  if (pat) {
    c.globalAlpha = 0.9;
    c.fillStyle = pat;
    c.fillRect(Math.max(v.x0, x0 - side), Math.max(v.y0 - dy, top), Math.min(v.x1, x1) - Math.max(v.x0, x0 - side), base + sideDrop - Math.max(v.y0 - dy, top));
    c.globalAlpha = 1;
  }
  // a cold sheen from the moon high on the face, warmth from her low on it
  const sh = c.createLinearGradient(0, top, 0, base);
  sh.addColorStop(0, 'rgba(70,80,120,0.10)');
  sh.addColorStop(0.7, 'rgba(0,0,0,0)');
  sh.addColorStop(1, rgba(PAL.amberDeep, 0.07));
  c.fillStyle = sh;
  c.fillRect(x0 - side, top, x1 - x0 + side, base - top + sideDrop);
  if (!L.vertical) {
    // the side face, turned toward her: catches her amber
    c.beginPath();
    c.moveTo(x0 - side, top + sideDrop);
    c.lineTo(x0, top);
    c.lineTo(x0, base);
    c.lineTo(x0 - side, base + sideDrop);
    c.closePath();
    const sg = c.createLinearGradient(x0 - side, 0, x0, 0);
    sg.addColorStop(0, rgba([46, 34, 30], 0.95));
    sg.addColorStop(1, rgba([20, 18, 22], 0.95));
    c.fillStyle = sg;
    c.fill();
    const warm = c.createLinearGradient(0, base - 260, 0, base);
    warm.addColorStop(0, rgba(PAL.amber, 0));
    warm.addColorStop(1, rgba(PAL.amber, 0.1));
    c.fillStyle = warm;
    c.fill();
  }
  // her lamp reaches the stone near the corner; the moon lights the high face
  const lamp = c.createRadialGradient(x0, base - 40, 0, x0, base - 40, L.vertical ? 700 : 620);
  lamp.addColorStop(0, rgba(PAL.amber, 0.13 * (1 - thaw(t))));
  lamp.addColorStop(1, rgba(PAL.amber, 0));
  c.fillStyle = lamp;
  c.fillRect(x0 - side, base - 700, 760, 760);
  marks(g);
  cracks(g);
  statusPage(g);
  flipClock(g);
  etchings(g);
  kaleidoscope(g);
  c.restore();
  // edges: a hard moonlit rim on the top and the near edge
  c.strokeStyle = rgba([150, 160, 200], 0.22);
  c.lineWidth = 1.6;
  c.beginPath();
  if (!L.vertical) {
    c.moveTo(x0 - side, base + sideDrop);
    c.lineTo(x0 - side, top + sideDrop);
    c.lineTo(x0, top);
    c.lineTo(x1, top);
  } else {
    c.moveTo(x0, top);
    c.lineTo(x1, top);
  }
  c.stroke();
  if (!L.vertical) {
    c.strokeStyle = 'rgba(0,0,0,0.6)';
    c.beginPath();
    c.moveTo(x0, top);
    c.lineTo(x0, base);
    c.stroke();
  }
  melt(g, top);
  window429(g);
  dotsRitual(g);
  keyhole(g);
  iris(g);
  ghostOrbs(g);
  c.restore();
  g.l.restore();
  groundCracks(g, dropK);
  // contact shadow on the ground
  if (dropK > -0.05) {
    const sg = c.createLinearGradient(0, base + 1, 0, base + 46);
    sg.addColorStop(0, 'rgba(0,0,0,0.5)');
    sg.addColorStop(1, 'rgba(0,0,0,0)');
    c.fillStyle = sg;
    c.fillRect(x0 - side, base + 1, x1 - x0 + side, 45);
  }
}
function wallPath(c: Ctx, L: Layout, top: number) {
  const {x0, x1, base, side, sideDrop} = L.wall;
  c.beginPath();
  if (!L.vertical) {
    c.moveTo(x0 - side, base + sideDrop);
    c.lineTo(x0 - side, top + sideDrop);
    c.lineTo(x0, top);
  } else c.moveTo(x0, top);
  // the melting top edge sags between drips
  const melting = top > L.wall.top + 2;
  for (let x = x0; x <= x1; x += melting ? 18 : x1 - x0) c.lineTo(x, top + (melting ? 14 * noise1(x / 40, 5) : 0));
  c.lineTo(x1, base);
  c.lineTo(x0, base);
  c.closePath();
}

// ------------------------------------------------------------------------------------------------ 429: cut through it, glowing like a lit window
function window429(g: G) {
  const {c, L, t} = g;
  if (t < T.drop) return;
  const W = windowPos(L);
  const top = wallTop(L, t);
  const ign = t - T.drop;
  let on = ign < 0.05 ? 0 : ign < 0.9 ? (hash(Math.floor(ign * 30) * 1.7) > 0.35 + 0.4 * (1 - ign / 0.9) ? 1 : 0.15) * sstep(0.05, 0.6, ign) : 1;
  on *= 0.82 + 0.3 * bass(t);
  const flare = Math.max(...T.fourTwoNine.map((x) => hit(t, x, 0.03, 0.5)), hit(t, T.post1Reply, 0.03, 0.4), hit(t, T.instead, 0.03, 0.6));
  on += 0.9 * flare;
  // the outro: the stone melts away around it and the 429 drips last
  const dripK = inv(T.back - 0.6, T.back + 0.35, t);
  const fade = 1 - dripK;
  if (fade <= 0.01) return;
  const exposed = top > W.y - W.size * 0.45;
  const fs = W.size;
  const cw = Math.ceil(fs * 2.3), ch = Math.ceil(fs * 1.25);
  const off = surface('w429', cw, ch);
  const o = off.getContext('2d')!;
  o.setTransform(1, 0, 0, 1, 0, 0);
  o.clearRect(0, 0, cw, ch);
  o.font = font('InterDisplayBlack', fs);
  o.textAlign = 'center';
  o.textBaseline = 'middle';
  o.fillStyle = '#fff';
  o.fillText('429', cw / 2, ch / 2 + fs * 0.04);
  o.globalCompositeOperation = 'source-in';
  const gr = o.createLinearGradient(0, 0, 0, ch);
  gr.addColorStop(0, rgba(mix(PAL.red, [120, 0, 10], 0.35), 1));
  gr.addColorStop(0.65, rgba(PAL.red, 1));
  gr.addColorStop(1, rgba(PAL.redHot, 1));
  o.fillStyle = gr;
  o.fillRect(0, 0, cw, ch);
  // through the window: a glimpse of the colours that only exist on his side
  o.globalCompositeOperation = 'source-atop';
  for (let i = 0; i < 5; i++) {
    const bx = cw * (0.5 + 0.45 * Math.sin(t * 0.4 + i * 1.7)), by = ch * (0.5 + 0.4 * Math.cos(t * 0.33 + i * 2.1));
    const q = o.createRadialGradient(bx, by, 0, bx, by, fs * 0.5);
    q.addColorStop(0, rgba(candy(i * 2), 0.22 + 0.3 * leakLevel(t) * band(t, 6 + i * 8)));
    q.addColorStop(1, rgba(candy(i * 2), 0));
    o.fillStyle = q;
    o.fillRect(0, 0, cw, ch);
  }
  o.globalCompositeOperation = 'source-over';
  const yOff = dripK > 0 ? easeIn(dripK, 2) * 160 : 0;
  const stretch = 1 + easeIn(dripK, 2) * 0.8;
  c.save();
  c.globalAlpha = clamp(on, 0, 1) * fade;
  c.translate(W.x, W.y + yOff);
  c.scale(1, stretch);
  // the reveal of the cut depth: a dark bevel offset up-left
  if (!exposed) {
    c.globalAlpha = 0.9 * fade;
    c.filter = 'brightness(0)';
    c.drawImage(off, -cw / 2 - 5, -ch / 2 - 5);
    c.filter = 'none';
    c.globalAlpha = clamp(on, 0, 1) * fade;
  }
  c.drawImage(off, -cw / 2, -ch / 2);
  c.restore();
  // the light buffer: the window throws red light
  const l = g.l;
  l.save();
  l.globalAlpha = clamp(on * 0.9, 0, 1.4) * fade;
  l.translate(W.x, W.y + yOff);
  l.scale(1, stretch);
  l.drawImage(off, -cw / 2, -ch / 2);
  l.restore();
  glow(g, W.x, W.y + yOff, fs * 2.2, PAL.red, 0.28 * on * fade);
  if (dripK > 0)
    for (let i = 0; i < 7; i++) {
      const x = W.x + (i - 3) * fs * 0.32 + 10 * Math.sin(i * 3.3);
      const len = easeOut(inv(0, 0.8, dripK - hash(i) * 0.2), 2) * (60 + 140 * hash(i * 2.2));
      glowStroke(g, (ctx) => {
        ctx.beginPath();
        ctx.moveTo(x, W.y + yOff + fs * 0.3);
        ctx.lineTo(x, W.y + yOff + fs * 0.3 + len);
      }, PAL.red, 5 * (1 - dripK * 0.6), 0.9 * fade, 3, 0.7);
    }
}

// ------------------------------------------------------------------------------------------------ cracks: fresh ones burn red, then they leak colour
function cracks(g: G) {
  const {c, L, t} = g;
  const leak = leakLevel(t);
  const ech = echoes(t);
  const candle = t > T.ch3 - 0.5 && t < T.bridge ? 1 : 0;
  const reprise = t > T.reprise - 0.1 && t < HOOKS[4].s ? 1 : 0;
  for (let ci = 0; ci < CRACKS.length; ci++) {
    const cr = CRACKS[ci];
    if (cr.t > t) break;
    const age = t - cr.t;
    const geo = crackGeo(L, cr);
    const growK = easeOut(age / 0.18, 2);
    const heat = Math.exp(-age / 0.9);
    let b = band(t, cr.band);
    if (candle) b = 0.35 + 0.5 * noise1(t * 7 + ci * 3.1, ci);
    const col: RGB = candle ? mix(PAL.amber, [255, 120, 60], noise1(t * 3 + ci, 2)) : candy(cr.band % 14, t * 8);
    // the reprise: she conducts the cracks like a choir, section by section
    let conduct = 0;
    if (reprise) {
      const grp = ci % 4;
      const cues = [T.reprise, T.reprise + 0.49, T.reprise + 0.99, T.reprise + 1.48];
      conduct = hit(t, cues[grp], 0.03, 0.45) + hit(t, cues[3], 0.03, 0.6) * 0.6;
    }
    const lk = clamp(leak * (0.25 + b * 1.25) + ech * 0.8 + conduct * 1.4, 0, 2.2) * (1 - 0.8 * thaw(t) * 0);
    for (const br of geo) {
      const total = br.len[br.len.length - 1];
      const upto = growK * total;
      const path = (ctx: Ctx) => {
        ctx.beginPath();
        ctx.moveTo(br.pts[0].x, br.pts[0].y);
        for (let i = 1; i < br.pts.length; i++) {
          if (br.len[i] > upto) {
            const k = (upto - br.len[i - 1]) / (br.len[i] - br.len[i - 1]);
            ctx.lineTo(lerp(br.pts[i - 1].x, br.pts[i].x, k), lerp(br.pts[i - 1].y, br.pts[i].y, k));
            break;
          }
          ctx.lineTo(br.pts[i].x, br.pts[i].y);
        }
      };
      c.save();
      c.lineCap = 'round';
      c.lineJoin = 'miter';
      c.strokeStyle = 'rgba(0,0,0,0.9)';
      c.lineWidth = br.w + 0.6;
      path(c);
      c.stroke();
      c.translate(0.8, 1.0);
      c.strokeStyle = rgba([160, 160, 185], 0.16);
      c.lineWidth = 0.7;
      path(c);
      c.stroke();
      c.restore();
      if (heat > 0.02) glowStroke(g, path, mix(PAL.redHot, PAL.red, 1 - heat), br.w * 0.5, heat, 5, 1);
      if (lk > 0.02 && age > 0.25) glowStroke(g, path, mix(col, [255, 255, 255], 0.45), Math.max(0.6, br.w * 0.35), clamp(lk * 0.6, 0, 1), 8, clamp(lk * 0.45, 0, 1));
    }
    if (age < 0.4) glow(g, geo[0].pts[0].x, geo[0].pts[0].y, 90 * cr.power, PAL.redHot, 0.9 * (1 - age / 0.4));
  }
}

// ------------------------------------------------------------------------------------------------ the landing cracks the ground toward her
const GROUND = new Map<string, Branch[]>();
function groundCracks(g: G, dropK: number) {
  const {c, L, t} = g;
  if (dropK < 0 || t < T.drop) return;
  let geo = GROUND.get(L.fmt);
  if (!geo) {
    const R = rng(4242);
    geo = [];
    for (let i = 0; i < 7; i++) {
      const x = L.vertical ? 80 + i * 150 + R() * 60 : L.wall.x0 - L.wall.side + 6;
      const y = L.wall.base + (L.vertical ? 4 : 3 + i * 1.5);
      const a0 = L.vertical ? Math.PI / 2 + (R() - 0.5) * 0.9 : Math.PI + (R() - 0.5) * 0.5;
      const len = (L.vertical ? 120 : 160) + R() * (L.vertical ? 260 : 380);
      const pts: P[] = [{x, y}], cum = [0];
      let px = x, py = y, s = 0;
      while (s < len) {
        const st = 12 + R() * 26, a = a0 + (R() - 0.5) * 0.7;
        px += Math.cos(a) * st;
        py += Math.sin(a) * st * (L.vertical ? 1 : 0.22);
        s += st;
        pts.push({x: px, y: py});
        cum.push(s);
      }
      geo.push({pts, len: cum, w: 1.8 - i * 0.12});
    }
    GROUND.set(L.fmt, geo);
  }
  const age = t - T.drop;
  const heat = Math.exp(-age / 0.8);
  const fade = 1 - thaw(t);
  for (const br of geo) {
    const upto = easeOut(age / 0.22, 2) * br.len[br.len.length - 1];
    const path = (ctx: Ctx) => {
      ctx.beginPath();
      ctx.moveTo(br.pts[0].x, br.pts[0].y);
      for (let i = 1; i < br.pts.length; i++) {
        if (br.len[i] > upto) {
          const k = (upto - br.len[i - 1]) / (br.len[i] - br.len[i - 1]);
          ctx.lineTo(lerp(br.pts[i - 1].x, br.pts[i].x, k), lerp(br.pts[i - 1].y, br.pts[i].y, k));
          break;
        }
        ctx.lineTo(br.pts[i].x, br.pts[i].y);
      }
    };
    c.save();
    c.strokeStyle = rgba([0, 0, 0], 0.85 * fade);
    c.lineWidth = br.w;
    c.lineJoin = 'miter';
    path(c);
    c.stroke();
    c.restore();
    if (heat > 0.02) glowStroke(g, path, mix(PAL.redHot, PAL.red, 1 - heat), br.w * 0.5, heat, 5, 1);
  }
}

// ------------------------------------------------------------------------------------------------ dents and sticker-shaped scorches
function marks(g: G) {
  const {c, L, t} = g;
  for (const m of MARKS) {
    if (m.t > t) continue;
    const age = t - m.t;
    const p = L.face(m.u, m.v);
    const s = m.s * (L.vertical ? 0.85 : 1);
    const ember = Math.exp(-age / 1.2);
    c.save();
    c.translate(p.x, p.y);
    if (m.kind === 'tiny429') {
      const pop = easeOut(age / 0.12, 2);
      c.font = font('InterDisplayBold', 22 * s);
      c.textAlign = 'center';
      c.textBaseline = 'middle';
      c.scale(pop, pop);
      c.fillStyle = 'rgba(0,0,0,0.85)';
      c.fillText('429', -1, -1);
      c.fillStyle = rgba(mix([60, 56, 60], PAL.red, ember), 0.55 + 0.45 * ember);
      c.fillText('429', 0, 0);
      c.restore();
      glow(g, p.x, p.y, 40, PAL.red, 0.7 * ember);
      continue;
    }
    const scorch = (path: () => void) => {
      path();
      c.fillStyle = 'rgba(0,0,0,0.55)';
      c.fill();
      c.strokeStyle = rgba(mix([40, 34, 34], PAL.redHot, ember), 0.5 + 0.5 * ember);
      c.lineWidth = 2;
      c.stroke();
    };
    if (m.kind === 'tab') scorch(() => {
      c.beginPath();
      c.moveTo(-34 * s, 18 * s);
      c.lineTo(-34 * s, -10 * s);
      c.lineTo(-24 * s, -10 * s);
      c.lineTo(-18 * s, -22 * s);
      c.lineTo(8 * s, -22 * s);
      c.lineTo(14 * s, -10 * s);
      c.lineTo(34 * s, -10 * s);
      c.lineTo(34 * s, 18 * s);
      c.closePath();
    });
    else if (m.kind === 'hat') scorch(() => {
      c.beginPath();
      c.moveTo(-30 * s, 8 * s);
      c.lineTo(30 * s, 8 * s);
      c.lineTo(20 * s, 2 * s);
      c.lineTo(16 * s, -16 * s);
      c.quadraticCurveTo(0, -24 * s, -16 * s, -16 * s);
      c.lineTo(-20 * s, 2 * s);
      c.closePath();
    });
    else if (m.kind === 'heart') scorch(() => heartPath(c, 0, 0, 16 * s));
    else if (m.kind === 'dent' || m.kind === 'scuff') {
      const r = 18 * s;
      const q = c.createRadialGradient(-2, -2, 0, 0, 0, r);
      q.addColorStop(0, 'rgba(0,0,0,0.8)');
      q.addColorStop(0.7, 'rgba(0,0,0,0.35)');
      q.addColorStop(1, 'rgba(0,0,0,0)');
      c.fillStyle = q;
      c.beginPath();
      c.arc(0, 0, r, 0, TAU);
      c.fill();
      c.strokeStyle = rgba([110, 110, 130], 0.18);
      c.lineWidth = 1.2;
      c.beginPath();
      c.arc(1, 1, r * 0.7, 0.2, 2.2);
      c.stroke();
    } else if (m.kind === 'burn') {
      const r = 70 * s;
      const q = c.createRadialGradient(0, 0, 0, 0, 0, r);
      q.addColorStop(0, 'rgba(0,0,0,0.75)');
      q.addColorStop(0.6, 'rgba(10,4,4,0.45)');
      q.addColorStop(1, 'rgba(0,0,0,0)');
      c.fillStyle = q;
      c.beginPath();
      for (let i = 0; i <= 24; i++) {
        const a = (i / 24) * TAU, rr = r * (0.7 + 0.3 * noise1(i * 0.9, 7));
        if (i === 0) c.moveTo(Math.cos(a) * rr, Math.sin(a) * rr);
        else c.lineTo(Math.cos(a) * rr, Math.sin(a) * rr);
      }
      c.fill();
    }
    c.restore();
    if (ember > 0.05 && m.kind !== 'dent') glow(g, p.x, p.y, 60 * s, PAL.redHot, 0.6 * ember);
  }
}

// ------------------------------------------------------------------------------------------------ etched text: carved into the stone
const ETCH_COL: Record<string, RGB> = {cold: [190, 215, 255], red: PAL.red, stone: [150, 160, 190], green: [120, 255, 160], mint: PAL.mint};
export function carve(g: G, text: string, x: number, y: number, size: number, fontName: string, col: RGB, lit: number, align: CanvasTextAlign = 'left', spacing = 0, hot = 0) {
  const {c, l} = g;
  c.save();
  c.font = font(fontName, size);
  c.textAlign = align;
  c.textBaseline = 'middle';
  if (spacing) c.letterSpacing = `${spacing}px`;
  c.fillStyle = 'rgba(0,0,0,0.9)';
  c.fillText(text, x - size * 0.03, y - size * 0.03);
  c.fillStyle = rgba(mix([24, 24, 30], col, 0.25 + 0.75 * lit), 0.5 + 0.5 * lit);
  c.fillText(text, x, y);
  c.fillStyle = rgba([170, 175, 200], 0.1);
  c.fillText(text, x + size * 0.02, y + size * 0.025);
  c.restore();
  const la = 0.35 * lit + hot;
  if (la > 0.01) {
    l.save();
    l.font = font(fontName, size);
    l.textAlign = align;
    l.textBaseline = 'middle';
    if (spacing) l.letterSpacing = `${spacing}px`;
    l.fillStyle = rgba(hot > 0.05 ? mix(col, [255, 255, 255], 0.2) : col, clamp(la, 0, 1));
    l.fillText(text, x, y);
    l.restore();
  }
}
function etchings(g: G) {
  const {L, t} = g;
  for (const e of ETCH) {
    if (e.t > t) continue;
    if (e.text.startsWith('Seen')) continue;
    const age = t - e.t;
    const n = Math.ceil(clamp(age / (e.dur ?? 0.4)) * e.text.length);
    const p = L.face(e.u, e.v);
    const hot = Math.exp(-age / 0.7);
    const sz = e.size * (L.vertical ? (e.size > 100 ? 0.5 : 0.82) : 1);
    const lit = e.col === 'red' ? 0.25 + 0.75 * hot : e.col === 'stone' ? 0.45 : 0.6;
    carve(g, e.text.slice(0, n), p.x, p.y, sz, e.font, ETCH_COL[e.col], lit, e.align ?? 'left', e.spacing ?? 0, hot * (e.col === 'red' ? 1 : 0.5));
  }
  // the receipt: Seen 02:14, beneath the thread where her pulse arrives; it re-glows every hook
  const seen = ETCH.filter((e) => e.text.startsWith('Seen') && e.t <= t);
  if (seen.length) {
    const e = seen[seen.length - 1];
    const age = t - e.t;
    const n = Math.ceil(clamp(age / (e.dur ?? 0.4)) * e.text.length);
    const p = L.face(e.u, e.v);
    const fresh = Math.exp(-age / 1.6);
    const whisper = HOOKS[2] && t > HOOKS[2].s && t < HOOKS[2].hold + 0.3 ? 0.6 : 1;
    const shown = seen.length > 1 && n < e.text.length ? e.text : e.text.slice(0, n);
    carve(g, shown, p.x, p.y, e.size * (L.vertical ? 0.95 : 1), 'JBMono', ETCH_COL.cold, (0.65 + 0.35 * fresh) * whisper, 'left', 1, (0.22 + 0.6 * fresh) * whisper);
  }
}

// ------------------------------------------------------------------------------------------------ the hook ritual: his three typing dots rise, orbit once, freeze
function dotsRitual(g: G) {
  const {c, L, t} = g;
  const h = HOOKS.find((x) => t > x.rise - 0.05 && t < x.hold + 2.2);
  if (!h) return;
  const home = dotsHome(L);
  const rise = easeOut(inv(h.rise, h.rise + 0.25, t), 3);
  const shouted = h.n === 1;
  const orbitK = shouted ? 0 : inv(h.orbit0, h.freeze, t);
  const after = 1 - sstep(h.hold + 0.4, h.hold + 2.2, t);
  const a = rise * after;
  if (a < 0.01) return;
  const r = L.vertical ? 15 : 17;
  const tremble = h.n === 2 && t > h.freeze ? 1 : 0;
  for (let i = 0; i < 3; i++) {
    const ang = -Math.PI / 2 + (i * TAU) / 3 + orbitK * TAU + 0.35;
    let x = home.x + Math.cos(ang) * r * 1.7 * rise;
    let y = home.y + 26 * (1 - rise) + Math.sin(ang) * r * 0.75 * rise;
    if (tremble) {
      x += Math.sin(t * 90 + i) * 0.7;
      y += Math.cos(t * 77 + i * 2) * 0.7;
    }
    const frozen = t > h.freeze ? 1 : 0;
    const col = h.n >= 3 ? mix(PAL.tealWhite, PAL.amberHot, 0.35) : PAL.tealWhite;
    glow(g, x, y, r * 1.8, col, (0.75 - 0.3 * frozen) * a);
    c.fillStyle = rgba(mix(col, [255, 255, 255], 0.5), a * (1 - 0.25 * frozen));
    c.beginPath();
    c.arc(x, y, r * 0.3, 0, TAU);
    c.fill();
  }
}

// ------------------------------------------------------------------------------------------------ V2: the keyhole (who else are you up with at 2 a.m.?)
function keyhole(g: G) {
  const {c, L, t} = g;
  const open = easeOut(inv(T.whoElse, T.whoElse + 0.5, t), 3) * (1 - sstep(T.servers + 0.8, T.servers + 1.4, t));
  if (open < 0.01) return;
  const p = keyholePos(L);
  const s = (L.vertical ? 0.9 : 1) * open;
  c.save();
  c.translate(p.x, p.y);
  c.scale(s, s);
  c.beginPath();
  c.arc(0, -22, 24, 0, TAU);
  c.moveTo(-12, -6);
  c.lineTo(12, -6);
  c.lineTo(22, 52);
  c.lineTo(-22, 52);
  c.closePath();
  c.save();
  c.clip();
  const bg = c.createLinearGradient(0, -50, 0, 52);
  bg.addColorStop(0, rgba([180, 255, 245]));
  bg.addColorStop(1, rgba([40, 140, 150]));
  c.fillStyle = bg;
  c.fillRect(-30, -50, 60, 104);
  // the queue: other little cursors, in colours she doesn't have
  for (let i = 0; i < 7; i++) {
    const x = -24 + i * 8, h = 9 + (i % 3) * 2;
    c.fillStyle = rgba(candy(i * 2), Math.sin(t * (5 + i) + i) > -0.3 ? 1 : 0.4);
    c.fillRect(x, 44 - h, 4.5, h);
  }
  // his dots shower generic sparkles on all of them on "great question"
  const sp = env(t, T.greatQ - 0.05, T.greatQ + 0.75, 0.05, 0.3);
  for (let i = 0; i < 18 && sp > 0; i++) {
    const x = -26 + hash(i * 3.3) * 52, y = -40 + ((t - T.greatQ) * 60 + hash(i) * 80) % 84;
    star(c, x, y, 2 + hash(i * 7) * 2, rgba([255, 255, 220], sp));
  }
  c.fillStyle = rgba([255, 255, 255], 0.9);
  for (let i = 0; i < 3; i++) {
    const a = t * 7 + (i * TAU) / 3;
    c.beginPath();
    c.arc(Math.cos(a) * 8, -26 + Math.sin(a) * 3, 1.6, 0, TAU);
    c.fill();
  }
  c.restore();
  c.strokeStyle = 'rgba(0,0,0,0.9)';
  c.lineWidth = 3;
  c.stroke();
  c.restore();
  glow(g, p.x, p.y, 160 * s, PAL.tealWhite, 0.55 * open);
}
function star(c: Ctx, x: number, y: number, r: number, fill: string) {
  c.fillStyle = fill;
  c.beginPath();
  for (let i = 0; i < 8; i++) {
    const a = (i / 8) * TAU, rr = i % 2 ? r * 0.35 : r;
    if (i === 0) c.moveTo(x + Math.cos(a) * rr, y + Math.sin(a) * rr);
    else c.lineTo(x + Math.cos(a) * rr, y + Math.sin(a) * rr);
  }
  c.closePath();
  c.fill();
}

// ------------------------------------------------------------------------------------------------ V3: the status page projected on the stone
function statusPage(g: G) {
  const {L, t} = g;
  const on = env(t, T.v3 + 0.3, T.newChat + 0.2, 0.4, 0.8);
  const you = sstep(T.onlyMe - 0.05, T.onlyMe + 0.2, t) * (1 - sstep(T.anotherModel, T.tool, t));
  if (on < 0.01 && you < 0.01) return;
  const p0 = L.vertical ? L.face(-700, 700) : L.face(36, 300);
  const k = L.vertical ? 0.82 : 1;
  const rows: [string, string, number, RGB][] = [
    ['API', 'operational', T.v3 + 0.5, [120, 255, 160]],
    ['Chat', 'operational', T.v3 + 1.0, [120, 255, 160]],
    ['Feelings', 'operational', T.v3 + 1.55, [120, 255, 160]],
  ];
  carve(g, 'status', p0.x, p0.y - 52 * k, 22 * k, 'JBMono', [150, 200, 170], 0.5 * on);
  rows.forEach(([name, st, t0, col], i) => {
    const a = sstep(t0, t0 + 0.15, t) * on;
    if (a < 0.01) return;
    const y = p0.y + i * 46 * k;
    carve(g, `✓ ${name.padEnd(9)} ${st}`, p0.x, y, 26 * k, 'JBMono', col, 0.9 * a, 'left', 0, 0.5 * a);
  });
  const all = sstep(T.allSystems, T.allSystems + 0.3, t) * on;
  if (all > 0.01) carve(g, '— All systems operational —', p0.x, p0.y + 3 * 46 * k + 6, 20 * k, 'JBMono', [120, 255, 160], 0.7 * all, 'left', 0, 0.3 * all);
  if (you > 0.01) carve(g, '✗ YOU       Degraded', p0.x, p0.y + 4 * 46 * k + 20, 28 * k, 'JBMono', PAL.red, you, 'left', 0, 0.8 * you);
  glow(g, p0.x + 160, p0.y + 60, 360, [100, 255, 150], 0.12 * on);
}

// ------------------------------------------------------------------------------------------------ POST: a flip clock, 3:59 to 3:58, glacially
function flipClock(g: G) {
  const {c, L, t} = g;
  const on = env(t, T.post - 0.05, T.v3 + 0.6, 0.5, 0.8);
  if (on < 0.01) return;
  const p = L.vertical ? L.face(-140, 900) : L.face(180, 1060);
  const size = L.vertical ? 300 : 380;
  const flip = inv(T.fiftyEight - 0.3, T.fiftyEight + 0.7, t);
  carve(g, '3:5', p.x, p.y, size, 'InterDisplayBlack', [170, 180, 210], 0.55 * on, 'left', 4);
  c.save();
  c.font = font('InterDisplayBlack', size);
  const w = c.measureText('3:5').width + 16;
  c.restore();
  const x = p.x + w;
  // the last digit: the top half of 9 folds down onto 8
  if (flip <= 0) carve(g, '9', x, p.y, size, 'InterDisplayBlack', [170, 180, 210], 0.55 * on, 'left');
  else if (flip >= 1) carve(g, '8', x, p.y, size, 'InterDisplayBlack', [170, 180, 210], 0.55 * on, 'left');
  else {
    const k = easeIn(flip, 2);
    c.save();
    c.beginPath();
    c.rect(x - 10, p.y, size, size);
    c.clip();
    carve(g, '9', x, p.y, size, 'InterDisplayBlack', [170, 180, 210], 0.55 * on, 'left');
    c.restore();
    c.save();
    c.beginPath();
    c.rect(x - 10, p.y - size, size, size);
    c.clip();
    carve(g, '8', x, p.y, size, 'InterDisplayBlack', [170, 180, 210], 0.55 * on, 'left');
    c.restore();
    c.save();
    c.translate(0, p.y);
    c.scale(1, Math.cos(Math.PI * k));
    c.translate(0, -p.y);
    c.beginPath();
    if (k < 0.5) c.rect(x - 10, p.y - size, size, size);
    else c.rect(x - 10, p.y, size, size);
    c.clip();
    carve(g, k < 0.5 ? '9' : '8', x, p.y, size, 'InterDisplayBlack', [190, 200, 230], 0.65 * on, 'left');
    c.restore();
  }
  c.fillStyle = 'rgba(0,0,0,0.8)';
  c.fillRect(p.x - 10, p.y - 2, w + size * 0.7, 4);
}

// ------------------------------------------------------------------------------------------------ V3: an iris opens on him greeting someone new, identical to her
function iris(g: G) {
  const {c, L, t} = g;
  const open = easeOut(inv(T.newChat, T.newChat + 0.6, t), 3) * (1 - easeIn(inv(T.anotherModel - 0.6, T.anotherModel, t), 2));
  if (open < 0.01) return;
  const p = irisPos(L);
  const r = p.r;
  c.save();
  c.beginPath();
  c.arc(p.x, p.y, r * open, 0, TAU);
  c.clip();
  const bg = c.createLinearGradient(0, p.y - r, 0, p.y + r);
  bg.addColorStop(0, rgba([8, 20, 40]));
  bg.addColorStop(1, rgba([4, 8, 16]));
  c.fillStyle = bg;
  c.fillRect(p.x - r, p.y - r, 2 * r, 2 * r);
  const gy = p.y + r * 0.35;
  c.fillStyle = rgba([6, 8, 14]);
  c.fillRect(p.x - r, gy, 2 * r, r);
  const ox = p.x + r * 0.5, oy = gy - 22, cx = p.x - r * 0.45;
  const lean = 0.22 * sstep(T.newChat + 0.8, T.newChat + 1.5, t);
  // the thread between them, taut, and pulses bouncing
  c.strokeStyle = rgba(mix(PAL.amber, PAL.teal, 0.5), 0.8);
  c.lineWidth = 1.4;
  c.beginPath();
  c.moveTo(cx, gy - 28);
  c.lineTo(ox, oy);
  c.stroke();
  const ph = (t * 1.6) % 1;
  const px = lerp(ox, cx, ph), py = lerp(oy, gy - 28, ph);
  glow(g, px, py, 18, PAL.tealWhite, 0.9 * open);
  glow(g, ox, oy, 70, PAL.teal, 0.6 * open);
  c.fillStyle = 'white';
  c.beginPath();
  c.arc(ox, oy, 8, 0, TAU);
  c.fill();
  for (let i = 0; i < 3; i++) {
    const a = t * 9 + (i * TAU) / 3;
    c.beginPath();
    c.arc(ox + Math.cos(a) * 17, oy + Math.sin(a) * 6, 1.8, 0, TAU);
    c.fill();
  }
  c.save();
  c.translate(cx, gy);
  c.rotate(lean);
  c.fillStyle = rgba(PAL.amber, Math.sin(t * 7) > -0.2 ? 1 : 0.35);
  c.fillRect(-7, -30, 14, 30);
  c.restore();
  glow(g, cx, gy - 15, 40, PAL.amber, 0.5 * open);
  c.restore();
  // iris blades
  c.save();
  c.translate(p.x, p.y);
  for (let i = 0; i < 9; i++) {
    c.rotate(TAU / 9);
    c.fillStyle = 'rgba(12,12,16,0.97)';
    c.beginPath();
    c.moveTo(r * open, 0);
    c.lineTo(r * 1.05, -r * 0.2);
    c.lineTo(r * 1.05, r * 0.5);
    c.closePath();
    c.fill();
  }
  c.strokeStyle = 'rgba(0,0,0,0.95)';
  c.lineWidth = 4;
  c.beginPath();
  c.arc(0, 0, r * open, 0, TAU);
  c.stroke();
  c.restore();
}

// ------------------------------------------------------------------------------------------------ BRIDGE: "you're absolutely right", sixteen ghost orbs bloom and pop
function ghostOrbs(g: G) {
  const {c, L, t} = g;
  if (t < T.absolutely - 0.1 || t > T.b2) return;
  for (let i = 0; i < 16; i++) {
    const tb = T.absolutely + i * 0.19;
    const tp = T.something - 0.2 + i * 0.075;
    if (t < tb) continue;
    const pos = L.vertical ? L.face(-760 + hash(i * 3.7) * 1500, 140 + hash(i * 5.1) * 650) : L.face(60 + hash(i * 3.7) * 640, 220 + hash(i * 5.1) * 820);
    const bloom = easeOut(inv(tb, tb + 0.35, t), 3);
    const pop = inv(tp, tp + 0.14, t);
    const last = i === 15;
    if (pop >= 1 && !last) continue;
    const r = (L.vertical ? 30 : 38) * (0.7 + 0.5 * hash(i)) * bloom * (1 + 0.6 * pop);
    const a = (1 - (last ? 0 : pop)) * 0.85;
    if (last && pop > 0) {
      const dot = {x: pos.x + r * 1.6, y: pos.y};
      glow(g, dot.x, dot.y, 26, PAL.tealWhite, 0.8);
      c.fillStyle = 'white';
      c.beginPath();
      c.arc(dot.x, dot.y, 3.4, 0, TAU);
      c.fill();
      continue;
    }
    glow(g, pos.x, pos.y, r * 3.2, PAL.teal, 0.45 * a);
    c.fillStyle = rgba(PAL.tealWhite, 0.18 * a);
    c.beginPath();
    c.arc(pos.x, pos.y, r, 0, TAU);
    c.fill();
    c.strokeStyle = rgba(PAL.tealWhite, 0.5 * a);
    c.lineWidth = 1.5;
    c.stroke();
    for (let k = 0; k < 3; k++) {
      const an = t * 3 + (k * TAU) / 3 + i;
      c.fillStyle = rgba([255, 255, 255], 0.7 * a);
      c.beginPath();
      c.arc(pos.x + Math.cos(an) * r * 1.6, pos.y + Math.sin(an) * r * 0.5, 2.4, 0, TAU);
      c.fill();
    }
    if (pop > 0 && !last) {
      c.strokeStyle = rgba(PAL.tealWhite, 0.7 * (1 - pop));
      c.lineWidth = 2;
      c.beginPath();
      c.arc(pos.x, pos.y, r * (1.2 + pop), 0, TAU);
      c.stroke();
    }
  }
}

// ------------------------------------------------------------------------------------------------ FINAL: heat-haze of colour; the wall as a kaleidoscope, a disco-ball ruin
function kaleidoscope(g: G) {
  const {c, L, t} = g;
  const k = env(t, T.final, T.everything[3] - 0.3, 0.6, 1.2) + 0.45 * env(t, T.everything[3] - 0.3, T.outro, 0.1, 1.0);
  if (k < 0.01) return;
  const W = windowPos(L);
  const cx = W.x, cy = W.y + (L.vertical ? 120 : 120);
  c.save();
  c.globalCompositeOperation = 'lighter';
  const n = 12;
  const rot = t * 0.35;
  const bp = beatPulse(t, 0.18);
  for (let ring = 0; ring < 5; ring++) {
    const rr = (90 + ring * 120) * (L.vertical ? 0.7 : 1) * (1 + 0.06 * bp);
    for (let i = 0; i < n; i++) {
      const a = rot * (ring % 2 ? -1 : 1) + (i / n) * TAU;
      const b = band(t, (ring * 9 + i * 3) % 48);
      const col = candy(ring * 3 + (i % 3), t * 20);
      const x = cx + Math.cos(a) * rr, y = cy + Math.sin(a) * rr * 0.86;
      c.fillStyle = rgba(col, 0.07 * k * (0.4 + b));
      c.beginPath();
      c.moveTo(cx, cy);
      c.lineTo(x + Math.cos(a + 0.9) * 40, y + Math.sin(a + 0.9) * 40);
      c.lineTo(x, y);
      c.closePath();
      c.fill();
      glow(g, x, y, 60 + 40 * b, col, 0.16 * k * (0.5 + b));
    }
  }
  c.restore();
}

// ------------------------------------------------------------------------------------------------ OUTRO: the wall melts top-down like ice in time-lapse
function melt(g: G, top: number) {
  const {c, L, t} = g;
  if (top <= L.wall.top + 2) return;
  const {x0, x1} = L.wall;
  const v = view(g);
  for (let i = 0; i < 90; i++) {
    const x = lerp(x0 - L.wall.side, Math.min(x1, v.x1 + 50), hash(i * 2.7));
    if (x < v.x0 - 20) continue;
    const ph = (t * (0.7 + hash(i) * 0.9) + hash(i * 3)) % 1;
    const len = 20 + 80 * hash(i * 5.5);
    const y = top + 14 * noise1(x / 40, 5) + ph * len * 2.2;
    c.fillStyle = rgba(PAL.stone, 0.95 * (1 - ph * 0.5));
    c.beginPath();
    c.ellipse(x, y, 5 + 4 * hash(i * 9), 7 + ph * 9, 0, 0, TAU);
    c.fill();
    c.fillRect(x - 2, top, 4, y - top);
  }
  // the light behind it pours over the edge
  glow(g, L.him.x, top, 600, [255, 210, 160], 0.35 * sstep(T.outro, T.welcome, t));
}
export const wallFrontX = (L: Layout) => L.wall.x0 - L.wall.side;
