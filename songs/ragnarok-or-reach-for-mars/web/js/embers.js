// Ember captions: each sung word is built from sparks that fly up out of the fire, settle into gold letters (Cormorant
// Garamond Bold), flicker while the line holds, then burn out to ash and drift away. Built from the text's own pixels
// (as the swarm captions in the "I have a blocker." film were), so it stays readable at any size. A HEY is a burst of sparks on the slam.
import * as THREE from 'three';
import { FONT, rng, dotTex } from './lib.js';

const VS = `
attribute vec3 aStart; attribute vec4 aSeed; attribute float aWord;
uniform float uTime, uEnd, uGather, uSize, uScale; uniform float uWordT[24];
varying float vA, vHeat, vBurn, vSeed;
void main() {
  float tw = uWordT[int(aWord)];
  float t0 = tw - uGather * (0.75 + 0.5 * aSeed.x), t1 = tw + 0.05 + 0.12 * aSeed.y;
  float p = clamp((uTime - t0) / (t1 - t0), 0.0, 1.0); float e = 1.0 - pow(1.0 - p, 3.0);
  vec3 ctrl = mix(aStart, position, 0.55) + vec3((aSeed.z - 0.5) * 1.1, 0.35 + aSeed.w * 0.7, (aSeed.y - 0.5) * 0.6);
  vec3 pos = mix(mix(aStart, ctrl, e), mix(ctrl, position, e), e);
  pos += 0.005 * vec3(sin(uTime * 7.0 + aSeed.x * 50.0), cos(uTime * 6.0 + aSeed.y * 40.0), 0.0) * e;
  float b = clamp((uTime - (uEnd + aSeed.x * 0.18 + (position.x * 0.04))) / 0.75, 0.0, 1.0);
  pos += vec3((aSeed.z - 0.5) * 0.6 * b + sin(uTime * 2.3 + aSeed.w * 30.0) * 0.06 * b, 1.1 * b * b + 0.25 * b, (aSeed.w - 0.5) * 0.4 * b);
  vHeat = 1.0 - e; vBurn = b; vSeed = aSeed.w;
  vA = smoothstep(0.0, 0.08, p) * (1.0 - smoothstep(0.55, 1.0, b));
  vec4 mv = modelViewMatrix * vec4(pos, 1.0); gl_Position = projectionMatrix * mv;
  gl_PointSize = uSize * uScale / -mv.z * (1.0 + 1.3 * (1.0 - e)) * (1.0 - 0.45 * b);
}`;
const FS = `
uniform sampler2D uDot; uniform float uTime, uOpacity, uKick; varying float vA, vHeat, vBurn, vSeed;
void main() {
  float a = texture2D(uDot, gl_PointCoord).a * vA * uOpacity; if (a < 0.01) discard;
  vec3 gold = vec3(1.75, 1.22, 0.52), hot = vec3(2.6, 1.3, 0.5), ember = vec3(1.3, 0.32, 0.07), ash = vec3(0.22, 0.2, 0.19);
  vec3 c = mix(gold, hot, vHeat * vHeat);
  c = mix(c, ember, smoothstep(0.0, 0.3, vBurn)); c = mix(c, ash, smoothstep(0.3, 0.75, vBurn));
  c *= (0.86 + 0.14 * sin(uTime * 13.0 + vSeed * 70.0)) * (1.0 + uKick);
  gl_FragColor = vec4(c * a, a);
}`;

/** A sung line. words/wordT give each word's onset (seconds); `end` is when it burns out. h = cap height (world units).
 *  Returns a Group (particles + a smoke band behind them) centred on its origin; place it in camera space. */
export function emberLine(text, words, wordT, end, { h = 0.42, font = FONT.serif, density = 1.6, maxW = null, seed = 1, size = 1.0 } = {}) {
  const px = 150; const c = document.createElement('canvas'); const g = c.getContext('2d');
  g.font = `${px}px ${font}`;
  const sp = g.measureText(' ').width; const wpx = words.map((w) => g.measureText(w).width);
  const scale = h / (px * 0.66);
  const rows = [[]]; let x = 0;
  for (let i = 0; i < words.length; i++) { if (maxW && rows[rows.length - 1].length && (x + wpx[i]) * scale > maxW) { rows.push([]); x = 0; } rows[rows.length - 1].push(i); x += wpx[i] + sp; }
  const rowW = rows.map((r) => r.reduce((s, i) => s + wpx[i], 0) + sp * (r.length - 1));
  const W = Math.ceil(Math.max(...rowW) + 40), lh = px * 1.12, H = Math.ceil(lh * rows.length + 40);
  c.width = W; c.height = H; g.font = `${px}px ${font}`; g.textBaseline = 'middle'; g.fillStyle = '#fff';
  const owner = new Int16Array(W * H).fill(-1);
  rows.forEach((r, ri) => { let xx = (W - rowW[ri]) / 2; const y = 20 + lh * (ri + 0.5);
    for (const i of r) { g.clearRect(0, 0, 0, 0); g.fillText(words[i], xx, y); const x0 = Math.floor(xx), x1 = Math.ceil(xx + wpx[i]);
      const im = g.getImageData(0, 0, W, H).data; for (let yy = 0; yy < H; yy++) for (let q = Math.max(0, x0 - 4); q < Math.min(W, x1 + 4); q++) if (im[(yy * W + q) * 4 + 3] > 120 && owner[yy * W + q] < 0) owner[yy * W + q] = i;
      xx += wpx[i] + sp; } });
  const R = rng(seed * 977 + text.length);
  const pos = [], start = [], seeds = [], wid = [];
  for (let yf = 0; yf < H; yf += density) for (let xf = 0; xf < W; xf += density) {
    const y = Math.floor(yf), xx = Math.floor(xf); const wi = owner[y * W + xx]; if (!(wi >= 0)) continue;
    const X = (xx - W / 2 + (R() - 0.5) * density) * scale, Y = -(y - H / 2 + (R() - 0.5) * density) * scale, Z = (R() - 0.5) * 0.02;
    pos.push(X, Y, Z);
    start.push(X * 0.35 + (R() - 0.5) * 1.6, -1.6 - R() * 1.4, (R() - 0.5) * 1.2);    // sparks come up from below the frame, from the fire
    seeds.push(R(), R(), R(), R()); wid.push(wi);
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); geo.setAttribute('aStart', new THREE.Float32BufferAttribute(start, 3));
  geo.setAttribute('aSeed', new THREE.Float32BufferAttribute(seeds, 4)); geo.setAttribute('aWord', new THREE.Float32BufferAttribute(wid, 1));
  const wt = new Array(24).fill(1e6); wordT.forEach((t, i) => { if (i < 24) wt[i] = t; });
  const mat = new THREE.ShaderMaterial({ vertexShader: VS, fragmentShader: FS, transparent: true, depthWrite: false, depthTest: false, blending: THREE.AdditiveBlending,
    uniforms: { uTime: { value: 0 }, uEnd: { value: end }, uWordT: { value: wt }, uGather: { value: 0.6 }, uSize: { value: 0.0115 * size * density / 2 }, uScale: { value: 600 }, uDot: { value: dotTex() }, uOpacity: { value: 1 }, uKick: { value: 0 } } });
  const pts = new THREE.Points(geo, mat); pts.frustumCulled = false; pts.renderOrder = 60;
  // the smoke band: a soft dark cloud behind the words so they read over the brightest fire
  const bandT = smokeTex(seed); const bandM = new THREE.MeshBasicMaterial({ map: bandT, transparent: true, depthWrite: false, depthTest: false, opacity: 0 });
  const band = new THREE.Mesh(new THREE.PlaneGeometry((W - 40) * scale * 1.45 + 1.2, H * scale * 1.9 + 0.5), bandM); band.renderOrder = 59; band.position.z = -0.05;
  // the glow plate: each word as hot gold metal under its sparks; it ignites as the sparks land and reddens as it burns
  const gc = document.createElement('canvas'); gc.width = W; gc.height = H; const gg = gc.getContext('2d'); gg.font = `${px}px ${font}`; gg.textBaseline = 'middle';
  const boxes = new Array(24).fill(null).map(() => new THREE.Vector4(-1, -1, -1, -1));
  rows.forEach((r, ri) => { let xx = (W - rowW[ri]) / 2; const y = 20 + lh * (ri + 0.5);
    for (const i of r) { gg.shadowColor = 'rgba(255,120,30,0.95)'; gg.shadowBlur = 26; gg.fillStyle = 'rgba(255,214,140,1)'; gg.fillText(words[i], xx, y);
      gg.shadowBlur = 0; gg.fillStyle = 'rgba(255,236,190,1)'; gg.fillText(words[i], xx, y);
      if (i < 24) boxes[i].set((xx - sp * 0.5) / W, 1 - (y + lh * 0.5) / H, (xx + wpx[i] + sp * 0.5) / W, 1 - (y - lh * 0.5) / H); xx += wpx[i] + sp; } });
  const gt = new THREE.CanvasTexture(gc); gt.colorSpace = THREE.SRGBColorSpace;
  const plateM = new THREE.ShaderMaterial({ transparent: true, depthWrite: false, depthTest: false, blending: THREE.AdditiveBlending,
    uniforms: { uTex: { value: gt }, uTime: { value: 0 }, uEnd: { value: end }, uWordT: { value: wt }, uBox: { value: boxes }, uKick: { value: 0 } },
    vertexShader: 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }',
    fragmentShader: `uniform sampler2D uTex; uniform float uTime, uEnd, uKick; uniform float uWordT[24]; uniform vec4 uBox[24]; varying vec2 vUv;
      void main(){ float tw = 1e6; for (int i = 0; i < 24; i++) { vec4 b = uBox[i]; if (vUv.x >= b.x && vUv.x <= b.z && vUv.y >= b.y && vUv.y <= b.w) tw = uWordT[i]; }
        vec4 c = texture2D(uTex, vUv); float on = smoothstep(tw - 0.02, tw + 0.32, uTime);
        float b = clamp((uTime - (uEnd + vUv.x * 0.25)) / 0.55, 0.0, 1.0);
        vec3 col = c.rgb * mix(vec3(1.05, 0.78, 0.36), vec3(0.9, 0.18, 0.04), smoothstep(0.0, 0.5, b));
        float a = c.a * on * (1.0 - smoothstep(0.35, 1.0, b)) * (0.92 + 0.08 * sin(uTime * 9.0 + vUv.x * 30.0));
        gl_FragColor = vec4(col * a * 0.95 * (1.0 + uKick), a); }` });
  const plate = new THREE.Mesh(new THREE.PlaneGeometry(W * scale, H * scale), plateM); plate.renderOrder = 59.5;
  const grp = new THREE.Group(); grp.add(band); grp.add(plate); grp.add(pts);
  const t0 = wordT[0], t1 = end + 1.0;
  grp.userData = { s: t0 - 0.7, e: t1, width: (W - 40) * scale, height: (H - 40) * scale, rows: rows.length, kick(v) { mat.uniforms.uKick.value = v; plateM.uniforms.uKick.value = v; },
    update(t, Hpx, fov) { mat.uniforms.uTime.value = t; plateM.uniforms.uTime.value = t; mat.uniforms.uScale.value = Hpx / (2 * Math.tan(THREE.MathUtils.degToRad(fov) / 2));
      bandM.opacity = 0.9 * Math.min(1, Math.max(0, (t - (t0 - 0.6)) / 0.5)) * (1 - Math.min(1, Math.max(0, (t - end - 0.2) / 0.6))); } };
  return grp;
}
function smokeTex(seed) {
  const c = document.createElement('canvas'); c.width = 512; c.height = 256; const g = c.getContext('2d'); const R = rng(seed + 5);
  for (let i = 0; i < 70; i++) { const x = 256 + (R() - 0.5) * 300, y = 128 + (R() - 0.5) * 70, r = 40 + R() * 70; const gr = g.createRadialGradient(x, y, 0, x, y, r);
    gr.addColorStop(0, 'rgba(6,4,3,0.24)'); gr.addColorStop(1, 'rgba(8,5,4,0)'); g.fillStyle = gr; g.fillRect(x - r, y - r, 2 * r, 2 * r); }
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
}

/** a burst of sparks for a HEY: they blow outward from `at` (caption space) at time t0 and die in ~1.2 s */
export function heyBurst(t0, at = new THREE.Vector3(), n = 420, seed = 7) {
  const R = rng(seed); const pos = new Float32Array(n * 3), sd = new Float32Array(n * 4);
  for (let i = 0; i < n; i++) { pos[i * 3] = at.x; pos[i * 3 + 1] = at.y; pos[i * 3 + 2] = at.z; for (let k = 0; k < 4; k++) sd[i * 4 + k] = R(); }
  const geo = new THREE.BufferGeometry(); geo.setAttribute('position', new THREE.BufferAttribute(pos, 3)); geo.setAttribute('aSeed', new THREE.BufferAttribute(sd, 4));
  const mat = new THREE.ShaderMaterial({ transparent: true, depthWrite: false, depthTest: false, blending: THREE.AdditiveBlending, uniforms: { uTime: { value: 0 }, uT0: { value: t0 }, uScale: { value: 600 }, uDot: { value: dotTex() } },
    vertexShader: `attribute vec4 aSeed; uniform float uTime, uT0, uScale; varying float vA, vK;
      void main(){ float k = clamp((uTime - uT0) / (0.7 + aSeed.x * 0.6), 0.0, 1.0); float on = step(uT0, uTime);
        float ang = aSeed.y * 6.2831; float sp = 1.2 + aSeed.z * 2.6; float e = 1.0 - pow(1.0 - k, 2.5);
        vec3 p = position + vec3(cos(ang) * sp * e * 1.25, sin(ang) * sp * e * 0.75 - 0.6 * k * k, (aSeed.w - 0.5) * e);
        vA = on * (1.0 - k) * (1.0 - smoothstep(0.85, 1.0, k)); vK = k;
        vec4 mv = modelViewMatrix * vec4(p, 1.0); gl_Position = projectionMatrix * mv; gl_PointSize = 0.03 * uScale / -mv.z * (1.0 - 0.6 * k) * (0.6 + aSeed.w); }`,
    fragmentShader: `uniform sampler2D uDot; varying float vA, vK; void main(){ float a = texture2D(uDot, gl_PointCoord).a * vA; if (a < 0.01) discard; gl_FragColor = vec4(mix(vec3(2.6, 1.5, 0.6), vec3(1.4, 0.3, 0.06), vK) * a, a); }` });
  const p = new THREE.Points(geo, mat); p.frustumCulled = false; p.renderOrder = 61;
  p.userData = { s: t0, e: t0 + 1.4, update(t, Hpx, fov) { mat.uniforms.uTime.value = t; mat.uniforms.uScale.value = Hpx / (2 * Math.tan(THREE.MathUtils.degToRad(fov) / 2)); } };
  return p;
}
