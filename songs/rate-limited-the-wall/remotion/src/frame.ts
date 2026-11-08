import {dancers, drawHer, dust, flock, pile, planes, surfSpark, thread, v2Cast, v3Cast} from './cast';
import {grainTex, makeG, type G} from './gfx';
import {hisSide} from './his';
import {clamp, hit, rgba, sstep, surface, type Ctx} from './lib';
import {T, camera, dawn, herState, layout, memoryAt, thaw, type Fmt} from './story';
import {wall} from './wall';
import {aurora, dunes, fog, frost, ground, him, rainfall, sky, spill} from './world';

export function renderFrame(ctx: Ctx, t: number, W: number, H: number, fmt: Fmt, frame: number) {
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.globalAlpha = 1;
  ctx.globalCompositeOperation = 'source-over';
  ctx.filter = 'none';
  // the last frame is her pulse halfway across; cut to black on the blink (the end card is the studio's 2D layer)
  if (t >= T.cut) {
    ctx.fillStyle = '#000';
    ctx.fillRect(0, 0, W, H);
    return;
  }
  const L = layout(fmt);
  const mem = memoryAt(t);
  const tt = mem ? mem.of : t;
  if (tt >= T.b2 - 0.05 && tt < T.final) {
    const g = makeG(ctx, W, H, L, {x: 0, y: 0, z: 1, shake: 0, roll: 0}, tt);
    hisSide(g);
    post(g, frame, 0);
    return;
  }
  const g = makeG(ctx, W, H, L, camera(L, tt), tt);
  const her = herState(L, tt);
  sky(g);
  aurora(g);
  dunes(g);
  him(g);
  fog(g, 0.62);
  ground(g, her.x, her.y, (0.4 + 0.6 * her.on) * Math.min(2, her.glow));
  spill(g, L.vertical ? 540 : L.wall.x0 - 100, L.vertical ? L.wall.base + 140 : L.home.y + 30, L.vertical ? 600 : 520, tt);
  thread(g);
  wall(g);
  frost(g);
  dancers(g);
  pile(g);
  flock(g);
  v2Cast(g, her);
  v3Cast(g, her);
  drawHer(g, her);
  surfSpark(g, her);
  planes(g, her);
  dust(g);
  rainfall(g);
  let flash = 0.55 * hit(tt, T.drop, 0.005, 0.08);
  if (mem) flash = Math.max(flash, 0.35);
  // pushing through the crack into his side: the light swallows the frame
  const into = t < T.b2 ? sstep(T.b2 - 0.5, T.b2 - 0.05, t) : 0;
  post(g, frame, flash, into, mem ? 1 : 0);
}

function post(g: G, frame: number, flash: number, whiteout = 0, memory = 0) {
  const {c, W, H, t, lc} = g;
  const w2 = lc.width, h2 = lc.height;
  c.setTransform(1, 0, 0, 1, 0, 0);
  // bloom: the light buffer, blurred twice, added back
  const b = surface('bloom', w2, h2);
  const bx = b.getContext('2d')!;
  c.save();
  c.globalCompositeOperation = 'lighter';
  for (const [r, a] of [[3, 0.85], [14, 0.75], [44, 0.55]] as const) {
    bx.setTransform(1, 0, 0, 1, 0, 0);
    bx.globalCompositeOperation = 'copy';
    bx.filter = `blur(${(r * W) / 1920}px)`;
    bx.drawImage(lc, 0, 0);
    bx.filter = 'none';
    c.globalAlpha = a;
    c.drawImage(b, 0, 0, W, H);
  }
  c.restore();
  // grade: cool shadows, warm floor; dawn lifts everything
  c.save();
  c.globalCompositeOperation = 'soft-light';
  const gr = c.createLinearGradient(0, 0, 0, H);
  gr.addColorStop(0, rgba([40, 70, 140], 0.22));
  gr.addColorStop(1, rgba([255, 150, 60], 0.12 + 0.1 * dawn(t)));
  c.fillStyle = gr;
  c.fillRect(0, 0, W, H);
  c.restore();
  // vignette
  const v = c.createRadialGradient(W / 2, H / 2, Math.min(W, H) * 0.35, W / 2, H / 2, Math.hypot(W, H) * 0.6);
  v.addColorStop(0, 'rgba(0,0,0,0)');
  v.addColorStop(1, rgba([0, 0, 0], 0.62 - 0.25 * thaw(t)));
  c.fillStyle = v;
  c.fillRect(0, 0, W, H);
  // film grain
  c.save();
  c.globalCompositeOperation = 'overlay';
  c.globalAlpha = 0.09;
  const gt = grainTex(frame % 6);
  const ox = -((frame * 97) % 256), oy = -((frame * 61) % 256);
  const s = Math.max(1, Math.round(W / 1920));
  for (let y = oy; y < H; y += 256 * s) for (let x = ox; x < W; x += 256 * s) c.drawImage(gt, x, y, 256 * s, 256 * s);
  c.restore();
  if (memory) {
    c.fillStyle = rgba([255, 255, 255], 0.12);
    c.fillRect(0, 0, W, H);
  }
  if (flash > 0.003) {
    c.fillStyle = rgba([255, 250, 240], clamp(flash));
    c.fillRect(0, 0, W, H);
  }
  if (whiteout > 0.003) {
    c.fillStyle = rgba([235, 255, 250], clamp(whiteout));
    c.fillRect(0, 0, W, H);
  }
}
