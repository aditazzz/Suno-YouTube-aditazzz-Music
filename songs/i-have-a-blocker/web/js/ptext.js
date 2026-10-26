// lyric lines made of green particles: each word gathers out of a drifting cloud as it is sung, the line holds with a
// faint shimmer, then blows away. Built from the text's own pixels, so it stays readable at any size.
import * as THREE from 'three';
import { FONT, rng, dotTex } from './lib.js';

const VS = `
attribute vec3 aStart; attribute float aSeed; attribute float aWord;
uniform float uTime; uniform float uEnd; uniform float uWordT[24]; uniform float uSize; uniform float uScale; uniform float uGather;
varying float vA; varying float vS;
void main() {
  float tw = uWordT[int(aWord)];
  float p = clamp((uTime - (tw - uGather)) / uGather, 0.0, 1.0); p = p * p * (3.0 - 2.0 * p);
  vec3 pos = mix(aStart, position, p);
  pos += 0.012 * vec3(sin(uTime * 3.1 + aSeed * 40.0), cos(uTime * 2.6 + aSeed * 31.0), 0.0) * p;
  float d = clamp((uTime - uEnd) / 0.9, 0.0, 1.0);
  pos += vec3((aSeed - 0.5) * 2.4, 0.9 + aSeed * 1.2, (fract(aSeed * 7.13) - 0.5) * 1.5) * d * d;
  vA = p * (1.0 - d); vS = aSeed;
  vec4 mv = modelViewMatrix * vec4(pos, 1.0);
  gl_Position = projectionMatrix * mv;
  gl_PointSize = uSize * uScale / -mv.z * (1.0 + 2.2 * (1.0 - p) + 1.5 * d);
}`;
const FS = `
uniform vec3 uColor; uniform sampler2D uDot; uniform float uOpacity;
varying float vA; varying float vS;
void main() {
  float a = texture2D(uDot, gl_PointCoord).a * vA * uOpacity;
  if (a < 0.01) discard;
  gl_FragColor = vec4(uColor * (0.85 + 0.3 * vS), a);
}`;

/** text: the line; words: array of words (same order); wordT: times; end: when it blows away.
 *  h: cap height in world units. Returns a THREE.Points to place in the scene (centred on its origin). */
export function particleLine(text, words, wordT, end, { h = 0.5, color = 0x6dffaa, font = FONT.disp, size = 1.0, density = 2, maxW = null, seed = 1 } = {}) {
  const px = 140; const c = document.createElement('canvas'); const g = c.getContext('2d');
  g.font = `${px}px ${font}`;
  // wrap into rows if a max width (in world units) is given
  const sp = g.measureText(' ').width; const wpx = words.map((w) => g.measureText(w).width);
  const scale = h / (px * 0.72);                    // world units per canvas px (cap height ~0.72 em)
  const rows = [[]]; let x = 0;
  for (let i = 0; i < words.length; i++) {
    if (maxW && rows[rows.length - 1].length && (x + wpx[i]) * scale > maxW) { rows.push([]); x = 0; }
    rows[rows.length - 1].push(i); x += wpx[i] + sp;
  }
  const rowW = rows.map((r) => r.reduce((s, i) => s + wpx[i], 0) + sp * (r.length - 1));
  const W = Math.ceil(Math.max(...rowW) + 40), lh = px * 1.15, H = Math.ceil(lh * rows.length + 40);
  c.width = W; c.height = H; g.font = `${px}px ${font}`; g.textBaseline = 'middle'; g.fillStyle = '#fff';
  const boxes = [];
  rows.forEach((r, ri) => { let xx = (W - rowW[ri]) / 2; const y = 20 + lh * (ri + 0.5);
    for (const i of r) { g.fillText(words[i], xx, y); boxes.push([i, xx, xx + wpx[i]]); xx += wpx[i] + sp; } });
  const img = g.getImageData(0, 0, W, H).data;
  const R = rng(seed * 977 + text.length);
  const pos = [], start = [], seeds = [], wid = [];
  const rowOf = (y) => Math.min(rows.length - 1, Math.max(0, Math.floor((y - 20) / lh)));
  for (let y = 0; y < H; y += density) for (let xx = 0; xx < W; xx += density) {
    if (img[(y * W + xx) * 4 + 3] < 128) continue;
    const ri = rowOf(y); let wi = 0;
    for (const i of rows[ri]) { const b = boxes.find((bb) => bb[0] === i); if (xx >= b[1] - sp * 0.5) wi = i; }
    const X = (xx - W / 2 + (R() - 0.5) * density) * scale, Y = -(y - H / 2 + (R() - 0.5) * density) * scale, Z = (R() - 0.5) * 0.03;
    pos.push(X, Y, Z);
    const a = R() * Math.PI * 2, rr = 0.8 + R() * 2.2;
    start.push(X + Math.cos(a) * rr * 0.9 - 0.6, Y + Math.sin(a) * rr * 0.55 - 0.4, Z + (R() - 0.5) * 2.5);
    seeds.push(R()); wid.push(wi);
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  geo.setAttribute('aStart', new THREE.Float32BufferAttribute(start, 3));
  geo.setAttribute('aSeed', new THREE.Float32BufferAttribute(seeds, 1));
  geo.setAttribute('aWord', new THREE.Float32BufferAttribute(wid, 1));
  const wt = new Array(24).fill(1e6); wordT.forEach((t, i) => { if (i < 24) wt[i] = t; });
  const mat = new THREE.ShaderMaterial({
    vertexShader: VS, fragmentShader: FS, transparent: true, depthWrite: false, depthTest: false, blending: THREE.AdditiveBlending,
    uniforms: { uTime: { value: 0 }, uEnd: { value: end }, uWordT: { value: wt }, uSize: { value: 0.0105 * size * density / 2 }, uScale: { value: 600 },
      uGather: { value: 0.32 }, uColor: { value: new THREE.Color(color) }, uDot: { value: dotTex() }, uOpacity: { value: 1.0 } },
  });
  const pts = new THREE.Points(geo, mat); pts.frustumCulled = false; pts.renderOrder = 50;
  pts.userData = { n: pos.length / 3, width: (W - 40) * scale };
  return pts;
}
