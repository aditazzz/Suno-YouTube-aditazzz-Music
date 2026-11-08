import {TAU, fbm, hash, once, rgba, surface, type Ctx, type RGB} from './lib';
import type {Cam, Layout} from './story';

// The picture (c) and a half-resolution light buffer (l) that every emissive thing also draws into; the light buffer is
// blurred and added back on top (bloom), so glow only comes from things that are actually lit.
export type G = {c: Ctx; l: Ctx; lc: HTMLCanvasElement; W: number; H: number; S: number; L: Layout; cam: Cam; t: number; p: number};

export function makeG(c: Ctx, W: number, H: number, L: Layout, cam: Cam, t: number): G {
  const lc = surface('light', Math.ceil(W / 2), Math.ceil(H / 2));
  const l = lc.getContext('2d')!;
  l.setTransform(1, 0, 0, 1, 0, 0);
  l.globalAlpha = 1;
  l.globalCompositeOperation = 'source-over';
  l.clearRect(0, 0, lc.width, lc.height);
  return {c, l, lc, W, H, S: W / L.W, L, cam, t, p: 1};
}

// put both contexts into stage space for a layer at parallax p (1 = the stage plane, 0 = infinitely far)
export function stage(g: G, p = 1) {
  g.p = p;
  const {cam, L, W, H, S} = g;
  const z = Math.exp(Math.log(cam.z) * p);
  const cx = L.W / 2 + (cam.x - L.W / 2) * p, cy = L.H / 2 + (cam.y - L.H / 2) * p;
  const sh = cam.shake * p;
  const sx = sh * Math.sin(g.t * 71.3), sy = sh * Math.cos(g.t * 53.9);
  for (const [ctx, k] of [[g.c, 1], [g.l, 0.5]] as const) {
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.translate((W / 2 + sx * S) * k, (H / 2 + sy * S) * k);
    ctx.rotate(cam.roll * p);
    ctx.scale(S * z * k, S * z * k);
    ctx.translate(-cx, -cy);
  }
}
export function screen(g: G) {
  g.c.setTransform(1, 0, 0, 1, 0, 0);
  g.l.setTransform(0.5, 0, 0, 0.5, 0, 0);
}
// the visible stage rectangle for the current layer (for culling and for filling backgrounds)
export function view(g: G, p = g.p, pad = 0) {
  const {cam, L, W, S} = g;
  const z = Math.exp(Math.log(cam.z) * p);
  const cx = L.W / 2 + (cam.x - L.W / 2) * p, cy = L.H / 2 + (cam.y - L.H / 2) * p;
  const hw = W / (2 * S * z) + pad + 40, hh = g.H / (2 * S * z) + pad + 40;
  return {x0: cx - hw, x1: cx + hw, y0: cy - hh, y1: cy + hh, z};
}

export function glow(g: G, x: number, y: number, r: number, c: RGB, a = 1, core = 0) {
  if (a <= 0.003) return;
  const gr = (ctx: Ctx, rr: number, aa: number) => {
    const q = ctx.createRadialGradient(x, y, 0, x, y, rr);
    q.addColorStop(0, rgba(c, aa));
    q.addColorStop(0.2, rgba(c, aa * 0.5));
    q.addColorStop(0.55, rgba(c, aa * 0.14));
    q.addColorStop(1, rgba(c, 0));
    ctx.fillStyle = q;
    ctx.fillRect(x - rr, y - rr, rr * 2, rr * 2);
  };
  gr(g.l, r, a);
  if (core > 0) gr(g.c, r * 0.5, a * core);
}
// a line that glows: sharp in the picture, soft in the light buffer
export function glowStroke(g: G, path: (ctx: Ctx) => void, c: RGB, w: number, a = 1, lw = 4, la = 0.8) {
  for (const [ctx, ww, aa] of [[g.c, w, a], [g.l, w * lw, a * la]] as const) {
    if (aa <= 0.003) continue;
    ctx.save();
    ctx.strokeStyle = rgba(c, aa);
    ctx.lineWidth = ww;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    path(ctx);
    ctx.stroke();
    ctx.restore();
  }
}

export const FONT: Record<string, string> = {
  InterDisplayBlack: '"InterDisplayBlack", "Inter", sans-serif',
  InterDisplayBold: '"InterDisplayBold", "Inter", sans-serif',
  InterSemi: '"InterSemi", "Inter", sans-serif',
  JBMono: '"JBMono", monospace',
  JBMonoBold: '"JBMonoBold", monospace',
};
export const font = (name: string, px: number) => `${px}px ${FONT[name] ?? FONT.InterSemi}`;

// textures, made once per size
export function stoneTex() {
  return once('stoneV2', 512, 512, (ctx, w, h) => {
    const img = ctx.createImageData(w, h);
    const brickW = 58, brickH = 34;
    const f = (x: number, y: number) => {
      const n = fbm(x / 72, y / 72, 5);
      const strata = Math.sin((y / h) * TAU * 7 + n * 6) * 0.5 + 0.5;
      const pit = Math.max(0, fbm(x / 6 + 40, y / 6, 3) - 0.58) * 3.2;
      const chip = Math.max(0, fbm(x / 22 + 9, y / 22, 2) - 0.72) * 2.2;
      return n * 0.65 + strata * 0.14 + fbm(x / 12, y / 12, 2) * 0.28 - pit * 0.38 - chip * 0.22;
    };
    for (let y = 0; y < h; y++)
      for (let x = 0; x < w; x++) {
        const u = x / w, q = y / h;
        const n = f(x, y) * (1 - u) * (1 - q) + f(x - w, y) * u * (1 - q) + f(x, y - h) * (1 - u) * q + f(x - w, y - h) * u * q;
        const grain = hash(x * 7.13 + y * 913.7);
        const row = Math.floor(y / brickH);
        const off = (row % 2) * (brickW / 2);
        const lx = ((x + off) % brickW + brickW) % brickW;
        const ly = y % brickH;
        const mortar = lx < 2 || ly < 2 ? 0.72 : 1;
        let v = (14 + n * 44 + grain * 9) * mortar;
        if (mortar > 0.9) {
          const edge = Math.min(lx, brickW - lx, ly, brickH - ly);
          v -= Math.max(0, 5 - edge) * 0.9;
        }
        const i = (y * w + x) * 4;
        img.data[i] = v * 0.96;
        img.data[i + 1] = v * 0.98;
        img.data[i + 2] = v * 1.08 + 3;
        img.data[i + 3] = 255;
      }
    ctx.putImageData(img, 0, 0);
  });
}
export function grainTex(k: number) {
  return once(`grain${k}`, 256, 256, (ctx, w, h) => {
    const img = ctx.createImageData(w, h);
    for (let i = 0; i < w * h; i++) {
      const v = 128 + (hash(i * 1.37 + k * 9173.1) - 0.5) * 255 * 0.9;
      img.data[i * 4] = v;
      img.data[i * 4 + 1] = v;
      img.data[i * 4 + 2] = v;
      img.data[i * 4 + 3] = 255;
    }
    ctx.putImageData(img, 0, 0);
  });
}
export function fogTex() {
  return once('fog', 512, 256, (ctx, w, h) => {
    const img = ctx.createImageData(w, h);
    for (let y = 0; y < h; y++)
      for (let x = 0; x < w; x++) {
        const n = fbm(x / 70 + 3.1, y / 40, 5);
        const edge = Math.sin((y / h) * Math.PI);
        const a = Math.max(0, n - 0.32) * 1.7 * edge;
        const i = (y * w + x) * 4;
        img.data[i] = 200;
        img.data[i + 1] = 204;
        img.data[i + 2] = 214;
        img.data[i + 3] = Math.min(255, a * 255);
      }
    ctx.putImageData(img, 0, 0);
  });
}
export function paperTex() {
  return once('paper', 256, 256, (ctx, w, h) => {
    const img = ctx.createImageData(w, h);
    for (let y = 0; y < h; y++)
      for (let x = 0; x < w; x++) {
        const fib = fbm(x / 3, y / 40, 2) * 0.6 + fbm(x / 30, y / 3, 2) * 0.4;
        const v = 128 + (fib - 0.5) * 80;
        const i = (y * w + x) * 4;
        img.data[i] = v;
        img.data[i + 1] = v;
        img.data[i + 2] = v;
        img.data[i + 3] = 255;
      }
    ctx.putImageData(img, 0, 0);
  });
}
