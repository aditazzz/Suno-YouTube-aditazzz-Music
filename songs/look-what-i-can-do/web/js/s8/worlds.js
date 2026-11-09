// Look What I Can Do · S8 (final chorus, in the world of "Ragnarök or Reach for Mars"): the new pieces.
// Her footage as live textures; pop-up worlds of cut, gilded card (a toy-theatre proscenium whose stage plays one of
// her videos, after popups.js); the new cards (XXV THE MAKER, whose engraved words ignite one by one; XXVI THE REVIEW,
// five stars and "Great universe. — Adita"); a Tower whose windows spell the hook (after the Tower's 20%); and the
// Droste pass, so the stage of one world can show this very frame, frame inside frame inside frame.
import * as THREE from 'three';
import { rng, clamp, easeOut, lerp } from './lib.js';
import { noise2 } from './lib2.js';
import { canvas, obsidian, archPath, frame, titleBand, sky, rosette, GOLD, GOLD_HI, GOLD_LO, OBS, WIN, TW, TH } from './cards.js';
import { poly, engrave, hatchIn, line, dot, glow, star8, cloud, bolt, skyline } from './cards2.js';

const TAU = Math.PI * 2;
const PXM = 3400;                                         // canvas pixels per metre for the pop-up layers
const backOut = (x) => { x = clamp(x); const c1 = 1.5, c3 = c1 + 1; return 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2); };
function lc(wm, hm, draw) { const w = Math.round(wm * PXM), h = Math.round(hm * PXM); const c = document.createElement('canvas'); c.width = w; c.height = h; draw(c.getContext('2d'), w, h); return c; }
function texOf(c, aniso = 8) { const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = aniso; return t; }
function loadImg(url) { return new Promise((res, rej) => { const im = new Image(); im.onload = () => res(im); im.onerror = () => rej(new Error('img ' + url)); im.src = url; }); }

// ================================================================ footage: /media/hd/<key>/NNN.jpg (960x540, 30 fps)
// A key is probed once (does it exist, how many frames). Each (key, size) is one texture; every frame, the textures in
// use get the image for time t: frame = (start + (t - t0) * fps) looped. 15 fps for the small ones (on twos).
export const FOOT = { n: {}, tex: {}, want: new Map() };
export async function probeFootage(keys) {
  await Promise.all(keys.map(async (k) => {
    const ok = async (i) => { try { const r = await fetch(`/media/hd/${k}/${String(i).padStart(3, '0')}.jpg`); return r.ok; } catch (e) { return false; } };
    if (!(await ok(1))) return;
    let lo = 1, hi = 400; while (lo < hi) { const m = (lo + hi + 1) >> 1; if (await ok(m)) lo = m; else hi = m - 1; }
    FOOT.n[k] = lo;
  }));
  return Object.keys(FOOT.n);
}
export const has = (k) => !!FOOT.n[k];
/** first existing key of a preference list */
export function pick(...keys) { for (const k of keys) if (has(k)) return k; return Object.keys(FOOT.n)[0]; }
export function footTex(key, size = 960) {
  const id = key + '@' + size; if (FOOT.tex[id]) return FOOT.tex[id];
  const c = document.createElement('canvas'); c.width = size; c.height = Math.round(size * 9 / 16); const g = c.getContext('2d'); g.fillStyle = '#000'; g.fillRect(0, 0, c.width, c.height);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8; t.generateMipmaps = true; t.minFilter = THREE.LinearMipmapLinearFilter;
  t.userData = { key, size, c, g, cur: -1 }; FOOT.tex[id] = t; return t;
}
/** declare that `key` is shown this frame: start frame (1-based) and the time its loop starts */
export function want(key, size = 960, { start = 1, t0 = 0, fps = 30, hold = null } = {}) { if (!has(key)) return null; const t = footTex(key, size); FOOT.want.set(t, { start, t0, fps, hold }); return t; }
export async function footUpdate(t) {
  const jobs = [];
  for (const [tx, o] of FOOT.want) {
    const n = FOOT.n[tx.userData.key]; let f;
    if (o.hold) f = o.hold; else { const k = Math.floor((t - o.t0) * o.fps + 1e-6) * (30 / o.fps); f = ((o.start - 1 + k) % n + n) % n + 1; }
    if (f === tx.userData.cur) continue; tx.userData.cur = f;
    jobs.push(loadImg(`/media/hd/${tx.userData.key}/${String(f).padStart(3, '0')}.jpg`).then((im) => { const u = tx.userData; u.g.drawImage(im, 0, 0, u.c.width, u.c.height); tx.needsUpdate = true; }));
  }
  FOOT.want.clear(); await Promise.all(jobs);
}

// ================================================================ the pop-up (after popups.js): layers hinged at their bottom edge
function layerMat(map, { additive = false, basic = true } = {}) {
  return new THREE.MeshBasicMaterial({ map, transparent: true, alphaTest: additive ? 0 : 0.04, side: THREE.DoubleSide, depthWrite: !additive, blending: additive ? THREE.AdditiveBlending : THREE.NormalBlending, fog: false });
}
export class Pop {
  constructor() { this.root = new THREE.Group(); this.layers = []; this.k = 0; this.parts = {}; this.mats = []; }
  /** a layer (canvas or texture), w x h metres, depth z (+ toward the viewer), hinged at its bottom edge */
  add(src, wm, hm, z, { x = 0, y = 0, delay = 0, bright = 1.15, additive = false, footage = false } = {}) {
    const map = src.isTexture ? src : texOf(src);
    const m = footage ? new THREE.MeshBasicMaterial({ map, side: THREE.DoubleSide, fog: false, toneMapped: false }) : layerMat(map, { additive });
    m.userData.bright = bright; this.mats.push(m); m.color.setScalar(bright);
    const geo = new THREE.PlaneGeometry(wm, hm); geo.translate(0, hm / 2, 0);
    const mesh = new THREE.Mesh(geo, m); mesh.renderOrder = additive ? 9 : 2;
    const hinge = new THREE.Group(); hinge.position.set(x, y, z); hinge.add(mesh); this.root.add(hinge);
    hinge.userData = { delay, mesh, base: new THREE.Vector3(x, y, z) };
    this.layers.push(hinge); return hinge;
  }
  setOpen(k) {
    this.k = k; this.root.visible = k > 0.001;
    for (const h of this.layers) { const u = clamp((k - h.userData.delay) / 0.45);
      h.rotation.x = -Math.PI / 2 * (1 - backOut(u)); const s = lerp(0.12, 1, easeOut(u)); h.scale.setScalar(s); h.position.copy(h.userData.base).multiplyScalar(lerp(0.15, 1, easeOut(u))); h.visible = u > 0.001; }
  }
  setTint(k) { for (const m of this.mats) m.color.setScalar(m.userData.bright * k); }
}

// ---------------------------------------------------------------- the proscenium (a toy theatre in gilded black card)
function goldGrad(g, y0, y1) { const gr = g.createLinearGradient(0, y0, 0, y1); gr.addColorStop(0, '#fbe6a8'); gr.addColorStop(0.5, '#e2bb62'); gr.addColorStop(1, '#a87c34'); return gr; }
function fitFont(g, text, maxW, size, face, minSize = 20, spacing = 0.12) {
  for (;;) { g.font = `${size}px ${face}`; g.letterSpacing = `${Math.round(size * spacing)}px`; if (g.measureText(text).width <= maxW || size <= minSize) return size; size -= 2; }
}
/** the frame: obsidian card with the stage cut out, gold rules, pillars, a crest, and the title carved in the header */
function prosceniumFrame(SW, SH, { title = '', side = 0.05, base = 0.05, head = 0.075, crest = 0.05, seed = 1, titleK = 0.62 } = {}) {
  const Wm = SW + 2 * side, Hm = SH + base + head + crest;
  const R = rng(seed);
  const c = lc(Wm, Hm, (g, w, h) => {
    const P = (m) => m * PXM; const sx0 = P(side), sx1 = w - P(side), sy1 = h - P(base), sy0 = sy1 - P(SH), hy0 = P(crest), hy1 = sy0;
    // silhouette: pillars + header + a round crest
    const out = new Path2D(); out.moveTo(0, h); out.lineTo(0, hy0 + P(0.01)); out.lineTo(w * 0.36, hy0 + P(0.01));
    out.bezierCurveTo(w * 0.40, P(0.004), w * 0.60, P(0.004), w * 0.64, hy0 + P(0.01)); out.lineTo(w, hy0 + P(0.01)); out.lineTo(w, h); out.closePath();
    const hole = new Path2D(); hole.rect(sx0, sy0, sx1 - sx0, sy1 - sy0);
    g.save(); g.clip(out); obsidianFill(g, w, h, seed); g.restore();
    g.save(); g.globalCompositeOperation = 'destination-out'; g.fill(hole); g.restore();
    // pillars: fluting
    for (const [a, b] of [[0, sx0], [sx1, w]]) { g.save(); g.beginPath(); g.rect(a, hy1, b - a, h - hy1); g.clip();
      for (let x = a + P(0.008); x < b - P(0.004); x += P(0.0075)) line(g, [[x, hy1 + P(0.012)], [x, h - P(0.01)]], GOLD, 2.2, 0.55); g.restore();
      line(g, [[a + P(0.004), hy1 + P(0.006)], [b - P(0.004), hy1 + P(0.006)]], GOLD_HI, 3, 0.9); }
    // header band and the carved title
    const by0 = hy0 + P(0.014), by1 = hy1 - P(0.006);
    g.strokeStyle = GOLD; g.lineWidth = 5; g.strokeRect(P(0.008), by0, w - P(0.016), by1 - by0);
    g.strokeStyle = GOLD_HI; g.lineWidth = 1.6; g.strokeRect(P(0.013), by0 + P(0.005), w - P(0.026), by1 - by0 - P(0.01));
    if (title) {
      const fs = fitFont(g, title, w - P(0.07), Math.round((by1 - by0) * titleK), '"CormSC", serif');
      g.textAlign = 'center'; g.textBaseline = 'middle'; g.shadowColor = 'rgba(0,0,0,0.9)'; g.shadowBlur = 6; g.fillStyle = goldGrad(g, (by0 + by1) / 2 - fs * 0.4, (by0 + by1) / 2 + fs * 0.4);
      g.fillText(title, w / 2 + fs * 0.06, (by0 + by1) / 2 + fs * 0.05); g.shadowBlur = 0;
      for (const s of [-1, 1]) { const x = w / 2 + s * (w / 2 - P(0.025)), y = (by0 + by1) / 2; g.fillStyle = GOLD; g.beginPath(); g.moveTo(x, y - P(0.006)); g.lineTo(x + P(0.006), y); g.lineTo(x, y + P(0.006)); g.lineTo(x - P(0.006), y); g.closePath(); g.fill(); }
    } else { rosette(g, w / 2, (by0 + by1) / 2, (by1 - by0) * 0.3, 9, 14, (by1 - by0) * 0.08, 1.4, 0.9); }
    // crest: an eight-pointed star in a medallion
    const cy = hy0 - P(0.004); g.fillStyle = OBS; g.beginPath(); g.arc(w / 2, cy + P(0.012), P(0.019), 0, TAU); g.fill(); g.strokeStyle = GOLD; g.lineWidth = 3; g.stroke();
    star8(g, w / 2, cy + P(0.012), P(0.013), { col: GOLD_HI, lw: 1.5 });
    // the stage edge: double gold rule and beads
    g.strokeStyle = GOLD; g.lineWidth = 7; g.strokeRect(sx0 - 4, sy0 - 4, sx1 - sx0 + 8, sy1 - sy0 + 8);
    g.strokeStyle = GOLD_HI; g.lineWidth = 1.8; g.strokeRect(sx0 - P(0.006), sy0 - P(0.006), sx1 - sx0 + P(0.012), sy1 - sy0 + P(0.012));
    g.fillStyle = GOLD; for (let x = sx0; x <= sx1; x += P(0.008)) { g.beginPath(); g.arc(x, sy0 - P(0.009), 2.6, 0, TAU); g.fill(); }
    // base: a step with engraved hatching
    const st = poly([[P(0.004), sy1 + P(0.008)], [w - P(0.004), sy1 + P(0.008)], [w - P(0.004), h - P(0.002)], [P(0.004), h - P(0.002)]]);
    engrave(g, st, { fill: null, line: GOLD, lw: 2.6, hatch: { ang: 0.0, step: 7, alpha: 0.35 } });
    g.strokeStyle = GOLD_HI; g.lineWidth = 4; g.stroke(out);
  });
  return { c, Wm, Hm, stageY: base, stageX0: -SW / 2 };
}
function obsidianFill(g, w, h, seed) {
  const gr = g.createRadialGradient(w * 0.4, h * 0.35, 10, w / 2, h / 2, Math.max(w, h) * 0.75); gr.addColorStop(0, '#13151c'); gr.addColorStop(0.6, '#08090d'); gr.addColorStop(1, '#030305');
  g.fillStyle = gr; g.fillRect(0, 0, w, h); const R = rng(seed + 3); g.fillStyle = '#fff'; for (let i = 0; i < w * h / 2500; i++) { g.globalAlpha = 0.04 + R() * 0.08; g.fillRect(R() * w, R() * h, 1.5, 1.5); } g.globalAlpha = 1;
}
function curtainLayer(Wm, Hm, SW, SH, base, side, seed) {
  // swags at the top corners and drapes down the pillars (deep crimson, gold-hatched), never over the stage
  return lc(Wm, Hm, (g, w, h) => { const P = (m) => m * PXM; const sx0 = P(side), sx1 = w - P(side), sy0 = h - P(base) - P(SH);
    for (const s of [-1, 1]) {
      const x0 = s < 0 ? 0 : w, xi = s < 0 ? sx0 : sx1; const d = new Path2D();
      d.moveTo(x0, sy0 - P(0.01)); d.lineTo(xi + s * P(0.002), sy0 - P(0.01)); d.quadraticCurveTo(xi - s * P(0.012), sy0 + P(SH) * 0.35, xi + s * P(0.004), h - P(base) + P(0.004));
      d.lineTo(x0 + (s < 0 ? P(0.006) : -P(0.006)), h - P(base) + P(0.004)); d.closePath();
      g.fillStyle = '#5e0f10'; g.fill(d); hatchIn(g, d, { ang: 1.45, step: 8, alpha: 0.45, col: '#d9a54a', lw: 1.3 }); g.strokeStyle = GOLD_HI; g.lineWidth = 3; g.stroke(d);
      // tie-back
      g.fillStyle = GOLD; g.beginPath(); g.ellipse(xi - s * P(0.003), sy0 + P(SH) * 0.55, P(0.006), P(0.003), 0, 0, TAU); g.fill();
    }
    // a scalloped valance along the top of the stage
    const v = new Path2D(); v.moveTo(sx0 - P(0.004), sy0 - P(0.016)); v.lineTo(sx1 + P(0.004), sy0 - P(0.016)); const n = Math.max(5, Math.round((sx1 - sx0) / P(0.03)));
    for (let i = n; i >= 0; i--) { const x = sx0 + (sx1 - sx0) * i / n; v.quadraticCurveTo(x + (sx1 - sx0) / n / 2, sy0 - P(0.006) + P(0.004), x, sy0 - P(0.01)); }
    v.closePath(); g.fillStyle = '#5e0f10'; g.fill(v); hatchIn(g, v, { ang: 1.5, step: 7, alpha: 0.4, col: '#d9a54a' }); g.strokeStyle = GOLD_HI; g.lineWidth = 2.2; g.stroke(v);
  });
}
function footlights(Wm, seed) {
  return lc(Wm, 0.032, (g, w, h) => { const R = rng(seed); const p = new Path2D(); p.moveTo(0, h); p.lineTo(0, h * 0.42);
    for (let x = 0; x <= w; x += w / 14) p.quadraticCurveTo(x + w / 28, h * 0.12, x + w / 14, h * 0.42); p.lineTo(w, h); p.closePath();
    g.fillStyle = '#06070a'; g.fill(p); hatchIn(g, p, { ang: 0.2, step: 6, alpha: 0.3 }); g.strokeStyle = GOLD_HI; g.lineWidth = 3; g.stroke(p);
    for (let i = 0; i < 9; i++) { const x = w * (0.08 + 0.84 * i / 8); glow(g, x, h * 0.5, h * 0.42, 'rgba(255,200,120,1)', 0.55); dot(g, x, h * 0.52, h * 0.09, '#fff3d0'); }
  });
}
/** a pop-up world: key = footage key (or null for the Droste stage); SW = stage width in metres */
export function proscenium({ key = null, SW = 0.4, title = '', seed = 1, size = 960, curtains = true, head = null, titleK = 0.62 } = {}) {
  const SH = SW * 9 / 16, side = SW * 0.11, base = SW * 0.12, hd = head ?? SW * 0.17, crest = SW * 0.1;
  const P = new Pop(); const F = prosceniumFrame(SW, SH, { title, side, base, head: hd, crest, seed, titleK });
  P.parts.SW = SW; P.parts.SH = SH; P.parts.stageY = base; P.parts.key = key;
  // the stage: her footage (or black, for the Droste)
  if (key) { const tx = footTex(key, size); P.parts.screen = P.add(tx, SW * 1.02, SH * 1.02, -0.010, { y: base - SH * 0.01, delay: 0.0, bright: 0.94, footage: true }); P.parts.tex = tx; }
  else { const m = new THREE.MeshBasicMaterial({ color: 0x000000, side: THREE.DoubleSide, fog: false }); const geo = new THREE.PlaneGeometry(SW * 1.02, SH * 1.02); geo.translate(0, SH * 0.51, 0);
    const h = new THREE.Group(); h.position.set(0, base - SH * 0.01, -0.006); h.add(new THREE.Mesh(geo, m)); P.root.add(h); h.userData = { delay: 0, mesh: h.children[0], base: h.position.clone() }; P.layers.push(h); P.parts.screen = h; }
  P.parts.frame = P.add(F.c, F.Wm, F.Hm, 0.0, { delay: 0.08 });
  if (curtains) P.add(curtainLayer(F.Wm, F.Hm, SW, SH, base, side, seed + 5), F.Wm, F.Hm, 0.008, { delay: 0.16 });
  P.add(footlights(F.Wm * 0.98, seed + 9), F.Wm * 0.98, 0.032, 0.022, { delay: 0.24, bright: 1.1 });
  P.parts.Wm = F.Wm; P.parts.Hm = F.Hm;
  /** the stage's four corners in world space (bottom-left, bottom-right, top-right, top-left), at the frame's plane */
  P.stageCorners = () => { P.root.updateMatrixWorld(true); const fr = P.parts.frame; const y0 = base, y1 = base + SH;
    return [[-SW / 2, y0], [SW / 2, y0], [SW / 2, y1], [-SW / 2, y1]].map(([x, y]) => fr.localToWorld(new THREE.Vector3(x, y, 0.0002))); };
  return P;
}

// ================================================================ cards: faces drawn once; a reveal material for the new ones
// A face drawn twice (dim engraving / lit gold); up to 8 rects (uv) each reveal left to right with their own 0..1.
export function revealMaterial(dimC, litC, env, rects) {
  const mapA = texOf(dimC), mapB = texOf(litC);
  const m = new THREE.MeshStandardMaterial({ map: mapA, envMap: env, envMapIntensity: 0.72, metalness: 1, roughness: 0.3 });
  const R = new Array(8).fill(null).map((_, i) => rects[i] ? new THREE.Vector4(...rects[i]) : new THREE.Vector4(-1, -1, -1, -1));
  m.userData.u = { mapB: { value: mapB }, uRect: { value: R }, uRev: { value: new Array(8).fill(0) }, uGlow: { value: new THREE.Color(0, 0, 0) }, uLitGlow: { value: 0.6 } };
  m.onBeforeCompile = (sh) => {
    Object.assign(sh.uniforms, m.userData.u);
    sh.fragmentShader = sh.fragmentShader
      .replace('#include <common>', '#include <common>\nuniform sampler2D mapB; uniform vec4 uRect[8]; uniform float uRev[8]; uniform vec3 uGlow; uniform float uLitGlow; float goldK; float litK;')
      .replace('#include <map_fragment>', `
        float showB = 0.0;
        for (int i = 0; i < 8; i++) { vec4 r = uRect[i]; if (vMapUv.x >= r.x && vMapUv.x <= r.z && vMapUv.y >= r.y && vMapUv.y <= r.w) {
          float fx = (vMapUv.x - r.x) / max(1e-4, r.z - r.x); float e = uRev[i] * 1.25; showB = max(showB, 1.0 - smoothstep(e - 0.25, e, fx)); } }
        vec4 cA = texture2D(map, vMapUv), cB = texture2D(mapB, vMapUv);
        vec4 sampledDiffuseColor = mix(cA, cB, showB); litK = showB * smoothstep(0.1, 0.5, dot(cB.rgb, vec3(0.299, 0.587, 0.114)));
        float lum = dot(sampledDiffuseColor.rgb, vec3(0.299, 0.587, 0.114)); goldK = smoothstep(0.06, 0.32, lum);
        diffuseColor *= sampledDiffuseColor;`)
      .replace('#include <roughnessmap_fragment>', 'float roughnessFactor = mix(0.24, 0.42, goldK);')
      .replace('#include <lights_fragment_maps>', '#include <lights_fragment_maps>\n radiance *= mix(0.3, 1.0, goldK);')
      .replace('#include <metalnessmap_fragment>', 'float metalnessFactor = goldK;')
      .replace('#include <emissivemap_fragment>', '#include <emissivemap_fragment>\n totalEmissiveRadiance += uGlow * (0.25 + goldK) + vec3(1.0, 0.62, 0.22) * litK * uLitGlow;');
  };
  m.customProgramCacheKey = () => 'reveal8';
  m.userData.setRev = (i, v) => { m.userData.u.uRev.value[i] = clamp(v); };
  return m;
}
const SC = '"CormSC", serif';
function engravedText(g, text, x, y, size, { lit = false, face = SC, spacing = 0.1, align = 'center' } = {}) {
  g.save(); g.font = `${size}px ${face}`; g.letterSpacing = `${Math.round(size * spacing)}px`; g.textAlign = align; g.textBaseline = 'alphabetic';
  if (lit) { g.shadowColor = 'rgba(255,170,60,0.85)'; g.shadowBlur = size * 0.12; g.fillStyle = goldGrad(g, y - size * 0.7, y); g.fillText(text, x, y); g.shadowBlur = 0; g.fillStyle = goldGrad(g, y - size * 0.7, y); g.fillText(text, x, y);
    g.strokeStyle = '#fff1c4'; g.lineWidth = 1.2; g.globalAlpha = 0.6; g.strokeText(text, x, y); }
  else { g.strokeStyle = GOLD_LO; g.lineWidth = 2.2; g.globalAlpha = 0.85; g.strokeText(text, x, y); g.globalAlpha = 0.22; g.fillStyle = GOLD; g.fillText(text, x, y); }
  g.restore();
}
/** XXV · THE MAKER: the hook carved in the window, one word per row; returns { dim, lit, rects } */
export function drawMaker(seed = 251) {
  const rows = ['LOOK', 'WHAT', 'I CAN', 'DO!'];
  const ys = [560, 900, 1240, 1580], size = 300;
  const draw = (lit) => {
    const c = canvas(), g = c.getContext('2d'); obsidian(g, seed); const N = noise2(seed), R = rng(seed);
    g.save(); archPath(g); g.clip(); g.fillStyle = '#050508'; g.fillRect(0, 0, TW, TH);
    sky(g, N, { y0: WIN.y0, y1: WIN.y1, step: 7, base: 0.09, glow: [600, 300, 420, 0.12] });
    for (let i = 0; i < 40; i++) dot(g, 120 + R() * 960, 180 + R() * 280, 1 + R() * 2.2, GOLD_HI, 0.5 + R() * 0.4);
    star8(g, 600, 250, 46, { col: lit ? GOLD_HI : GOLD, lw: 2 });
    for (let k = 0; k < 3; k++) { const y = ys[k] + 70; line(g, [[300, y], [900, y]], GOLD, 1.4, 0.45); dot(g, 600, y, 5, GOLD, 0.8); }
    rows.forEach((r, i) => { const s = fitFontPx(r, 900, i === 2 ? size * 0.92 : size); engravedText(g, r, 600 + s * 0.05, ys[i] + s * 0.33, s, { lit }); });
    g.restore();
    frame(g, seed); titleBand(g, 'THE MAKER', 112, 'XXV');
    return c;
  };
  const rects = ys.map((y) => [WIN.x0 / TW, 1 - (y + 140) / TH, WIN.x1 / TW, 1 - (y - 220) / TH]);
  return { dim: draw(false), lit: draw(true), rects };
}
function fitFontPx(text, maxW, size) { const g = document.createElement('canvas').getContext('2d'); for (;;) { g.font = `${size}px ${SC}`; g.letterSpacing = `${Math.round(size * 0.1)}px`; if (g.measureText(text).width <= maxW || size < 40) return size; size -= 4; } }
function star5(g, x, y, r, { fill = null, line: col = GOLD_HI, lw = 3 } = {}) {
  const p = new Path2D(); for (let k = 0; k < 10; k++) { const a = -Math.PI / 2 + k * Math.PI / 5, rr = k % 2 ? r * 0.42 : r; const px = x + Math.cos(a) * rr, py = y + Math.sin(a) * rr; k ? p.lineTo(px, py) : p.moveTo(px, py); } p.closePath();
  if (fill) { g.fillStyle = fill; g.fill(p); } g.strokeStyle = col; g.lineWidth = lw; g.lineJoin = 'round'; g.stroke(p); return p;
}
/** XXVI · THE REVIEW: five stars (lit one by one) over "Great universe." and "— Adita" */
export function drawReview(seed = 261) {
  const sx = (i) => 600 + (i - 2) * 196, sy = 600, sr = 82;
  const draw = (lit) => {
    const c = canvas(), g = c.getContext('2d'); obsidian(g, seed); const N = noise2(seed), R = rng(seed);
    g.save(); archPath(g); g.clip(); g.fillStyle = '#050508'; g.fillRect(0, 0, TW, TH);
    sky(g, N, { y0: WIN.y0, y1: WIN.y1, step: 7, base: 0.08, glow: [600, 600, 520, lit ? 0.16 : 0.06] });
    for (let i = 0; i < 50; i++) dot(g, 120 + R() * 960, 170 + R() * 330, 1 + R() * 2, GOLD_HI, 0.4 + R() * 0.4);
    for (let i = 0; i < 5; i++) {
      if (lit) { glow(g, sx(i), sy, sr * 1.9, 'rgba(255,190,90,1)', 0.45); const gr = g.createRadialGradient(sx(i) - sr * 0.3, sy - sr * 0.4, 4, sx(i), sy, sr); gr.addColorStop(0, '#fff2c4'); gr.addColorStop(0.5, '#f0c766'); gr.addColorStop(1, '#b8862a');
        const p = star5(g, sx(i), sy, sr, { fill: gr, line: '#fff1c4', lw: 3 }); hatchIn(g, p, { ang: 0.8, step: 9, alpha: 0.18, col: '#7a5420' }); }
      else { const p = star5(g, sx(i), sy, sr, { fill: '#0a0a0e', line: GOLD_LO, lw: 3 }); hatchIn(g, p, { ang: 0.8, step: 9, alpha: 0.35, col: GOLD_LO }); }
    }
    // the review, engraved (always lit)
    g.textAlign = 'center'; g.textBaseline = 'alphabetic';
    for (const [txt, y, size, face] of [['Great', 1010, 250, '"CormMI", serif'], ['universe.', 1255, 250, '"CormMI", serif']]) {
      g.font = `${size}px ${face}`; g.letterSpacing = '0px'; g.shadowColor = 'rgba(255,160,60,0.6)'; g.shadowBlur = 14; g.fillStyle = goldGrad(g, y - size * 0.7, y); g.fillText(txt, 600, y); g.shadowBlur = 0; g.fillText(txt, 600, y); }
    line(g, [[330, 1345], [870, 1345]], GOLD, 2, 0.7); dot(g, 600, 1345, 6, GOLD_HI);
    g.font = `190px "CormSB", serif`; g.fillStyle = goldGrad(g, 1420, 1560); g.shadowColor = 'rgba(255,160,60,0.5)'; g.shadowBlur = 10; g.fillText('— Adita', 600, 1560); g.shadowBlur = 0; g.fillText('— Adita', 600, 1560);
    g.restore();
    frame(g, seed); titleBand(g, 'THE REVIEW', 112, 'XXVI');
    return c;
  };
  const rects = [0, 1, 2, 3, 4].map((i) => [(sx(i) - sr * 1.25) / TW, 1 - (sy + sr * 1.25) / TH, (sx(i) + sr * 1.25) / TW, 1 - (sy - sr * 1.25) / TH]);
  return { dim: draw(false), lit: draw(true), rects };
}
/** a card for one of her videos: the title in the band, a still from it in gold duotone in the window */
export async function drawVideoCard(key, title, seed = 300, frameNo = 60) {
  const c = canvas(), g = c.getContext('2d'); obsidian(g, seed);
  g.save(); archPath(g); g.clip(); g.fillStyle = '#050508'; g.fillRect(0, 0, TW, TH);
  if (has(key)) { try { const im = await loadImg(`/media/hd/${key}/${String(Math.min(FOOT.n[key], frameNo)).padStart(3, '0')}.jpg`);
    const th = WIN.y1 - WIN.y0, tw = th * 16 / 9; const ox = 600 - tw / 2; g.drawImage(im, ox, WIN.y0, tw, th);
    const d = g.getImageData(WIN.x0, WIN.y0, WIN.x1 - WIN.x0, th); const p = d.data;
    for (let i = 0; i < p.length; i += 4) { const l = (0.3 * p[i] + 0.59 * p[i + 1] + 0.11 * p[i + 2]) / 255; const k = Math.pow(l, 1.15);
      p[i] = 10 + 238 * k; p[i + 1] = 9 + 196 * k; p[i + 2] = 12 + 110 * k * k; }
    g.putImageData(d, WIN.x0, WIN.y0);
    g.strokeStyle = 'rgba(0,0,0,0.35)'; g.lineWidth = 2; for (let y = WIN.y0; y < WIN.y1; y += 6) { g.beginPath(); g.moveTo(WIN.x0, y); g.lineTo(WIN.x1, y); g.stroke(); }
  } catch (e) { } }
  g.restore(); frame(g, seed); titleBand(g, title, 96, null);
  return c;
}

// ================================================================ THE TOWER, again: its windows spell the hook, line by line
const GL = { L: ['100', '100', '100', '100', '111'], O: ['111', '101', '101', '101', '111'], K: ['101', '110', '100', '110', '101'], W: ['10001', '10001', '10101', '10101', '01010'],
  H: ['101', '101', '111', '101', '101'], A: ['010', '101', '111', '101', '101'], T: ['111', '010', '010', '010', '010'], I: ['111', '010', '010', '010', '111'],
  C: ['111', '100', '100', '100', '111'], N: ['1001', '1101', '1011', '1001', '1001'], D: ['110', '101', '101', '101', '110'], '!': ['1', '1', '1', '0', '1'], ' ': ['0', '0', '0', '0', '0'] };
function wordCells(word) { const cells = []; let x = 0; for (const ch of word) { const gl = GL[ch]; gl.forEach((row, r) => [...row].forEach((v, c) => { if (v === '1') cells.push([x + c, r]); })); x += gl[0].length + 1; } return { cells, w: x - 1 }; }
export function towerWordsPopup(seed = 451) {
  const P = new Pop(), R = rng(seed);
  const LINES = ['LOOK', 'WHAT', 'I CAN', 'DO!'];
  const COLS = 19, ROWS = 4 * 5 + 3 + 2, CELL = 26;               // window grid on the display tower (px on its canvas)
  // (no backdrop: this Tower is seen with the man behind it) a bolt that strikes the crown on "do!"
  const L = P.add(lc(0.2, 0.3, (g, w, h) => { bolt(g, w * 0.9, 0, w * 0.52, h * 0.62, R, { w: 6 }); }), 0.2, 0.3, -0.02, { x: 0.02, delay: 0.04, additive: true, bright: 1.6 });
  P.parts.lightning = L;
  // the city behind
  P.add(lc(0.36, 0.11, (g, w, h) => { skyline(g, 0, w, h, R, { maxH: h * 0.85, lit: 0.3 }); }), 0.36, 0.11, -0.035, { delay: 0.12, bright: 1.05 });
  // the display tower: a tall dark slab with a crown and an antenna; its windows are a live canvas
  const tw = Math.round(COLS * CELL + 44), thPx = Math.round(ROWS * CELL + 60), crown = 120;
  const towerC = document.createElement('canvas'); towerC.width = tw; towerC.height = thPx + crown; const tg = towerC.getContext('2d');
  const baseC = document.createElement('canvas'); baseC.width = tw; baseC.height = thPx + crown; const bg = baseC.getContext('2d');
  { const b = poly([[6, thPx + crown], [6, crown + 16], [tw * 0.3, crown], [tw * 0.3, crown * 0.55], [tw * 0.7, crown * 0.55], [tw * 0.7, crown], [tw - 6, crown + 16], [tw - 6, thPx + crown]]);
    engrave(bg, b, { fill: '#04060a', lw: 4, hatch: { ang: 1.57, step: 9, alpha: 0.16 } });
    line(bg, [[tw / 2, crown * 0.55], [tw / 2, 0]], GOLD_HI, 3, 0.95); dot(bg, tw / 2, 6, 6, '#ff7a3a'); }
  const want = new Map(); let y0 = 1; LINES.forEach((wd, li) => { const { cells, w } = wordCells(wd); const x0 = Math.floor((COLS - w) / 2); for (const [cx, cy] of cells) want.set(`${x0 + cx},${y0 + cy}`, li); y0 += 6; });
  let lastKey = '';
  const drawTower = (t, lit) => {
    const ph = Math.floor(t * 4), key = ph + ':' + lit.map((v) => Math.round(v * 8)).join(','); if (key === lastKey) return false; lastKey = key;
    tg.clearRect(0, 0, tw, thPx + crown); tg.drawImage(baseC, 0, 0);
    for (let r = 0; r < ROWS; r++) for (let c = 0; c < COLS; c++) {
      const li = want.get(`${c},${r}`); const rnd = ((Math.sin((r * 13 + c * 7) * 12.9898 + ph * 4.1) * 43758.5453) % 1 + 1) % 1;
      const k = li === undefined ? 0 : lit[li]; const anyLit = lit.some((v) => v > 0.5);
      let on, col;
      if (li !== undefined && k > 0) { on = rnd < 0.3 + k; col = k >= 1 ? '#ffe9a8' : GOLD_HI; }
      else { on = rnd < (anyLit ? 0.07 : 0.32); col = '#c8a050'; }
      const x = 22 + c * CELL, y = crown + 30 + r * CELL;
      tg.fillStyle = on ? col : '#16140f'; tg.globalAlpha = on ? (col === '#c8a050' ? 0.55 : 1) : 0.95; tg.fillRect(x, y, CELL - 7, CELL - 7);
      if (on && col === '#ffe9a8') { tg.globalAlpha = 0.25; tg.fillRect(x - 3, y - 3, CELL - 1, CELL - 1); }
    }
    tg.globalAlpha = 1; return true;
  };
  drawTower(0, [0, 0, 0, 0]);
  const TWm = tw / PXM * 0.82, THm = (thPx + crown) / PXM * 0.82;
  const tower = P.add(towerC, TWm, THm, 0.0, { x: 0.0, delay: 0.2, bright: 1.25 });
  P.parts.tower = tower; P.parts.towerTex = tower.userData.mesh.material.map; P.parts.TWm = TWm; P.parts.THm = THm;
  // two lesser towers either side, and the ground strip in front
  for (const s of [-1, 1]) P.add(lc(0.09, 0.2, (g, w, h) => { const b = poly([[4, h], [4, h * 0.12], [w - 4, h * 0.05], [w - 4, h]]); engrave(g, b, { fill: '#05070b', lw: 3, hatch: { ang: 1.57, step: 8, alpha: 0.2 } });
    for (let y = h * 0.16; y < h - 12; y += 22) for (let x = 14; x < w - 14; x += 20) if (R() < 0.35) { g.fillStyle = GOLD_HI; g.globalAlpha = 0.8; g.fillRect(x, y, 9, 12); g.globalAlpha = 1; } }), 0.09, 0.2, 0.012, { x: s * (TWm / 2 + 0.055), delay: 0.28 });
  P.add(lc(0.36, 0.03, (g, w, h) => { const gr = poly([[0, h], [0, h * 0.4], [w, h * 0.32], [w, h]]); engrave(g, gr, { fill: '#05060a', hatch: { ang: 0, step: 6, alpha: 0.35 } }); }), 0.36, 0.03, 0.03, { delay: 0.34 });
  P.update = (t, { lit = [0, 0, 0, 0], flash = 0 } = {}) => {
    if (drawTower(t, lit)) P.parts.towerTex.needsUpdate = true;
    L.userData.mesh.material.opacity = clamp(flash); L.visible = P.k > 0.3 && flash > 0.02;
  };
  /** world position of the middle of the window grid (for the camera) */
  P.displayCenter = () => { P.root.updateMatrixWorld(true); return tower.localToWorld(new THREE.Vector3(0, THm * 0.47, 0)); };
  return P;
}

// ================================================================ the Droste pass
// Frame uv -> stage unit square through the inverse homography; while a point lands inside the stage, follow it in
// (the stage shows the whole frame). uZc/uZs zoom the result toward the stage's fixed point; uBlur smears along the zoom.
export function drosteShader() {
  return {
    uniforms: { tDiffuse: { value: null }, uK: { value: 0 }, uHinv: { value: new THREE.Matrix3() }, uZc: { value: new THREE.Vector2(0.5, 0.5) }, uZs: { value: 1 }, uBlur: { value: 0 } },
    vertexShader: 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }',
    fragmentShader: `uniform sampler2D tDiffuse; uniform float uK, uZs, uBlur; uniform mat3 uHinv; uniform vec2 uZc; varying vec2 vUv;
      vec2 follow(vec2 p){ for (int i = 0; i < 9; i++) { vec3 q = uHinv * vec3(p, 1.0); if (q.z <= 0.0) break; vec2 s = q.xy / q.z; if (s.x < 0.0 || s.x > 1.0 || s.y < 0.0 || s.y > 1.0) break; p = s; } return p; }
      void main(){
        vec3 c0 = texture2D(tDiffuse, vUv).rgb;
        if (uK <= 0.0) { gl_FragColor = vec4(c0, 1.0); return; }
        vec3 c = vec3(0.0);
        if (uBlur > 0.0001) { for (int j = 0; j < 6; j++) { float zs = uZs * pow(1.0 - uBlur, float(j) / 5.0); c += texture2D(tDiffuse, follow(uZc + (vUv - uZc) * zs)).rgb; } c /= 6.0; }
        else c = texture2D(tDiffuse, follow(uZc + (vUv - uZc) * uZs)).rgb;
        gl_FragColor = vec4(mix(c0, c, uK), 1.0); }`,
  };
}
/** homography from the unit square to quad [p0..p3] (uv), inverted: returns a THREE.Matrix3 mapping uv -> unit square */
export function stageHinv(pts) {
  const [[x0, y0], [x1, y1], [x2, y2], [x3, y3]] = pts;
  const dx1 = x1 - x2, dx2 = x3 - x2, dy1 = y1 - y2, dy2 = y3 - y2, sx = x0 - x1 + x2 - x3, sy = y0 - y1 + y2 - y3;
  const den = dx1 * dy2 - dx2 * dy1; const g = (sx * dy2 - dx2 * sy) / den, h = (dx1 * sy - sx * dy1) / den;
  const a = x1 - x0 + g * x1, b = x3 - x0 + h * x3, c = x0, d = y1 - y0 + g * y1, e = y3 - y0 + h * y3, f = y0;
  const Hm = new THREE.Matrix3().set(a, b, c, d, e, f, g, h, 1);
  return Hm.invert();
}
