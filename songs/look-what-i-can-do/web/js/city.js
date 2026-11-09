// Look What I Can Do · "Scope Creep" — city.js: Chorus 2 + Verse 3 (84.34–122.94 s).
// Chorus 2: we pull out of one window and it is one of thousands — a night city whose every window plays one of her
// videos, under a hillside LOOK WHAT I CAN DO sign. Towers sprout in doubling waves, her tower unrolls a 14-page résumé
// and lights an AI GURU crown, then we dive into the avenue at its foot. Verse 3: a Times-Square avenue where every
// billboard is a receipt (her real X posts, highlighted and stamped), a news zipper, ten little silver boxes,
// Agents, Inc., the jumbotron, and a net-worth tower whose chart shoots off the top into the light (cut to the keynote).
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import * as L from './lib.js';
import * as M from './media.js';
import { neon, flicker } from './sets.js';

const { clamp, lerp, sstep, easeIO, easeOut, easeOut5, easeIn, backOut, env, V3 } = L;
const TAU = Math.PI * 2, D2R = Math.PI / 180, UPV = new THREE.Vector3(0, 1, 0);

let W = 1920, H = 1080, envTex, scene, cam, mirror, sky, bloom, finish, renderer;
const T = {};
const U = {   // uniforms shared by every custom shader (fog matches scene.fog)
  uTime: { value: 0 }, uFogCol: { value: new THREE.Color(0.007, 0.0065, 0.014) }, uFogDen: { value: 0.00024 },
  uSky: { value: new THREE.Color(0.045, 0.04, 0.08) }, uBright: { value: 1 },
  uMatch: { value: new THREE.Vector4(2, 0, 5, 76) }, uMatchCell: { value: 0 }, uHer: { value: new THREE.Vector2(0.95, 1) },
};
const MATCH = { atlas: 'H1', cell: 6, col: 5, row: 76 };   // H1 cell 6 = snowflake_undrop, the hall's last screen   // the window the cut lands in (her tower, front face)
const AVG = {};
// my own samplers on her footage: same Source (so M.update's new frame reaches them), but no anisotropic filtering —
// SwiftShader evaluates 8x aniso in software and the facades are seen at grazing angles. Only my texture's version is
// bumped each frame, so the upload still happens only when M.update actually swapped the image.
const MYTEX = {};
function myTex(name) {   // atlases: raw RGBA8 + mip-nearest (SwiftShader's per-texel sRGB decode and trilinear were most of the facade cost); heroes: sRGB
  if (MYTEX[name]) return MYTEX[name];
  const src = M.texOf(name); const t = new THREE.Texture(); t.source = src.source;
  t.colorSpace = THREE.NoColorSpace; t.generateMipmaps = true; t.minFilter = THREE.LinearMipmapNearestFilter; t.magFilter = THREE.LinearFilter; t.anisotropy = 1;
  MYTEX[name] = t; return t;
}
// any big texture: raw RGBA8, mip-nearest, decoded in the shader (c*c) — far cheaper per texel on SwiftShader
function rawTexMat(tex, bright = 1, { transparent = false, side = THREE.FrontSide } = {}) {
  tex.colorSpace = THREE.NoColorSpace; tex.minFilter = THREE.LinearMipmapNearestFilter; tex.anisotropy = 1; tex.needsUpdate = true;
  return new THREE.ShaderMaterial({ transparent, side, depthWrite: !transparent, uniforms: { map: { value: tex }, uB: { value: new THREE.Color(bright, bright, bright) } },
    vertexShader: `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`,
    fragmentShader: `uniform sampler2D map; uniform vec3 uB; varying vec2 vUv; void main(){ vec4 c = texture2D(map, vUv); gl_FragColor = vec4(c.rgb * c.rgb * uB, ${transparent ? 'c.a' : '1.0'}); }` });
}
// her clips on a quad from a raw atlas (decoded here): instanced screens use aRect, single quads use their own UVs
function rawScreenMat(atlas, { instanced = false, bright = 1 } = {}) {
  return new THREE.ShaderMaterial({ side: THREE.DoubleSide, uniforms: { map: { value: myTex(atlas) }, uB: { value: bright } },
    vertexShader: `${instanced ? 'attribute vec4 aRect;' : ''} varying vec2 vUv; varying vec3 vC;
      void main(){ ${instanced ? 'vUv = uv * aRect.zw + aRect.xy; vC = instanceColor; gl_Position = projectionMatrix * modelViewMatrix * instanceMatrix * vec4(position, 1.0);' : 'vUv = uv; vC = vec3(1.0); gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);'} }`,
    fragmentShader: `uniform sampler2D map; uniform float uB; varying vec2 vUv; varying vec3 vC;
      void main(){ vec3 c = texture(map, vUv, 0.6).rgb; c *= c; gl_FragColor = vec4(gl_FrontFacing ? c * vC * uB : vec3(0.012), 1.0); }` });
}
let LASTT = null;
function bumpTex(t, names) {   // my GL textures must upload even on the first frame of a chunk (no image yet at frame time)
  const fresh = !(LASTT !== null && t > LASTT && t - LASTT < 0.1); LASTT = t;
  for (const n of names) { const tx = myTex(n); tx.version++; if (fresh) tx.source.needsUpdate = true; }
}

// ================================================================ GLSL
const GL_COMMON = `
float hash12(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * .1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
float vnoise(vec2 p){ vec2 i = floor(p), f = fract(p); vec2 u = f * f * (3.0 - 2.0 * f);
  return mix(mix(hash12(i), hash12(i + vec2(1.0, 0.0)), u.x), mix(hash12(i + vec2(0.0, 1.0)), hash12(i + vec2(1.0, 1.0)), u.x), u.y); }
float fogK(vec3 wp, float den){ float d = length(cameraPosition - wp) * den; return 1.0 - exp(-d * d); }
`;
// facades: one box per tower, every window an atlas cell (box-filtered mullions, textureGrad so mips never pop)
const FAC_VS = `
attribute vec4 aInfo;   // seed, rise start (<0 none), rise duration, lit probability
attribute vec4 aGrid;   // window cell w, cell h (m), window w, window h (fraction of the cell)
attribute float aKind;  // atlas (0 = H1, 1 = V1) + 2 * covered face code (1: +x face, 2: -x face)
attribute float aCov;   // height (m) up to which that face is hidden behind signage
uniform float uTime;
uniform float uFogDen;
varying vec2 vF; varying vec3 vWP; varying vec3 vN; varying vec4 vInfo; varying vec4 vGrid; varying float vFace; varying float vRise; varying float vYoff; varying float vMir; varying float vFW; varying float vFog; varying float vFres; varying float vKind; varying float vCov;
void main(){
  vKind = aKind; vCov = aCov;
  vec3 S = vec3(length(instanceMatrix[0].xyz), length(instanceMatrix[1].xyz), length(instanceMatrix[2].xyz));
  vec3 p = position;
  float face = 4.0, u = 0.0, fw = 1.0;
  if (normal.z > 0.5) { face = 0.0; u = (p.x + 0.5) * S.x; fw = S.x; }
  else if (normal.x > 0.5) { face = 1.0; u = (0.5 - p.z) * S.z; fw = S.z; }
  else if (normal.z < -0.5) { face = 2.0; u = (0.5 - p.x) * S.x; fw = S.x; }
  else if (normal.x < -0.5) { face = 3.0; u = (p.z + 0.5) * S.z; fw = S.z; }
  vF = vec2(u, p.y * S.y); vFace = face; vFW = fw;
  float yoff = 0.0, done = 1.0;
  if (aInfo.y >= 0.0) { float k = clamp((uTime - aInfo.y) / aInfo.z, 0.0, 1.0); done = k; float e = 1.0 - pow(1.0 - k, 4.0); yoff = -(S.y + 3.0) * (1.0 - e); }
  vRise = done; vYoff = yoff;
  vec4 ip = instanceMatrix * vec4(p, 1.0); ip.y += yoff;
  vec4 wp = modelMatrix * ip; vWP = wp.xyz;
  vN = normalize(mat3(modelMatrix) * normal);
  vMir = modelMatrix[1][1] < 0.0 ? 1.0 : 0.0;
  vInfo = aInfo; vGrid = aGrid;
  float dd = length(cameraPosition - wp.xyz) * uFogDen; vFog = 1.0 - exp(-dd * dd);
  float fr = 1.0 - abs(dot(vN, normalize(cameraPosition - wp.xyz))); vFres = fr * fr * fr * fr;
  gl_Position = projectionMatrix * viewMatrix * wp;
}`;
const FAC_FS = `
uniform sampler2D uAtlasH, uAtlasV; uniform vec4 uAtH, uAtV; uniform vec3 uAvgH, uAvgV; uniform float uTime; uniform vec3 uFogCol; uniform float uFogDen;
uniform vec3 uSky; uniform float uBright; uniform vec4 uMatch; uniform float uMatchCell; uniform vec2 uHer;
varying vec2 vF; varying vec3 vWP; varying vec3 vN; varying vec4 vInfo; varying vec4 vGrid; varying float vFace; varying float vRise; varying float vYoff; varying float vMir; varying float vFW; varying float vFog; varying float vFres; varying float vKind; varying float vCov;
${GL_COMMON}
float pint(float x, float m0, float w){ return floor(x) * w + clamp(fract(x) - m0, 0.0, w); }
vec4 cellRect(float i, vec4 uAt){ float cw = uAt.z + 4.0, ch = uAt.w + 4.0; float Wt = uAt.x * cw, Ht = uAt.y * ch;
  float c = mod(i, uAt.x), r = floor(i / uAt.x);
  return vec4((c * cw + 3.0) / Wt, 1.0 - (r * ch + uAt.w + 1.0) / Ht, (uAt.z - 2.0) / Wt, (uAt.w - 2.0) / Ht); }
void main(){
#ifdef CLIP
  if (vMir < 0.5 ? vWP.y < -0.05 : vWP.y > 0.05) discard;
#endif
  vec3 Vd = cameraPosition - vWP; float fr = 1.0 - abs(dot(vN, Vd) * inversesqrt(max(dot(Vd, Vd), 1e-6))); fr *= fr; float fres = fr * fr;
  vec3 col;
  float atl = mod(vKind, 2.0), af = floor(vKind * 0.5 + 0.01);
  bool covered = af > 0.5 && abs(vFace - (af < 1.5 ? 1.0 : 3.0)) < 0.5 && vF.y < vCov;
  if (vFace > 3.5) col = vec3(0.005, 0.0055, 0.008);
  else if (covered) col = vec3(0.004, 0.0043, 0.0065) + uSky * fres * 0.5;   // behind the signage: no window work
#ifdef FB
  else col = vec3(0.02, 0.01, 0.03);
  if (false) {
#else
  else {
#endif
    vec2 g = vF / vGrid.xy; vec2 wf = vGrid.zw; vec2 m0 = (1.0 - wf) * 0.5;
    vec2 fw = fwidth(g);   // helper pixels on edge-on faces can hand us inf/NaN derivatives: treat those as 'far'
    if (any(isnan(fw)) || any(isinf(fw)) || any(isnan(g))) { fw = vec2(8.0); g = vec2(0.5); }
    fw = clamp(fw, vec2(1e-4), vec2(64.0));
    float cx = (pint(g.x + 0.5 * fw.x, m0.x, wf.x) - pint(g.x - 0.5 * fw.x, m0.x, wf.x)) / fw.x;
    float cy = (pint(g.y + 0.5 * fw.y, m0.y, wf.y) - pint(g.y - 0.5 * fw.y, m0.y, wf.y)) / fw.y;
    float mask = clamp(cx * cy, 0.0, 1.0);
    vec2 cid = floor(g);
    vec2 key = cid + vec2(vInfo.x * 17.13 + vFace * 57.31, vInfo.x * 3.71 + vFace * 11.7);
    float hl = hash12(key), hc = hash12(key + 19.19), hb = hash12(key + 47.47);
    bool her = abs(vInfo.x - uMatch.x) < 0.5; float lit = step(hl, her ? uHer.x : vInfo.w);
    float cell = floor(hc * 15.999);
    if (abs(vInfo.x - uMatch.x) < 0.5 && abs(vFace - uMatch.y) < 0.5 && abs(cid.x - uMatch.z) < 0.5 && abs(cid.y - uMatch.w) < 0.5) { cell = uMatchCell; lit = 1.0; hb = 0.75; }
    float wy = (cid.y + 0.5) * vGrid.y + vYoff;
    lit *= step((1.0 - vRise) * (5.0 + 45.0 * hb), wy);
    vec4 uAt = atl < 0.5 ? uAtH : uAtV; vec4 R = cellRect(cell, uAt);
    vec2 wuv = clamp((g - cid - m0) / wf, 0.0, 1.0);
    vec2 sc = R.zw / wf;
    vec2 tsz = vec2(uAt.x * (uAt.z + 4.0), uAt.y * (uAt.w + 4.0)); vec2 gx = dFdx(g) * sc * tsz, gy = dFdy(g) * sc * tsz;
    float lod = clamp(0.5 * log2(max(max(dot(gx, gx), dot(gy, gy)), 1e-8)), 0.0, 14.0);
    float farK = smoothstep(0.35, 1.1, max(fw.x, fw.y));
    vec3 vid = vec3(0.0);
    if (lit > 0.5 && mask > 0.002 && farK < 0.999) {
#ifdef FA
      vid = vec3(0.5, 0.3, 0.6);
#else
      vec2 auv = R.xy + wuv * R.zw; float l2 = max(lod + 0.55, 0.0); vid = atl < 0.5 ? textureLod(uAtlasH, auv, l2).rgb : textureLod(uAtlasV, auv, l2).rgb; vid *= vid;
      float lu = dot(vid, vec3(0.2126, 0.7152, 0.0722)); vid = max(mix(vec3(lu), vid, 1.35), 0.0); vid = vid / (1.0 + 0.45 * vid) * 1.25;
#endif
    }
    vec3 win = mix(vid * lit * (0.42 + 0.58 * hb) * (her ? uHer.y : 1.0), (atl < 0.5 ? uAvgH : uAvgV) * vInfo.w * 0.62, farK);
    vec3 glass = vec3(0.006, 0.0068, 0.011) + uSky * fres;
    float e = clamp(1.0 - min(vF.x, vFW - vF.x) * 1.6, 0.0, 1.0); glass += uSky * 0.5 * e * e;
    col = mix(glass, win * uBright, mask);
  }
  if (vInfo.y >= 0.0 && uTime >= vInfo.y) col += vec3(2.2, 0.75, 1.5) * exp(-abs(vWP.y) / 6.0) * pow(1.0 - vRise, 0.7);
  col = mix(col, uFogCol, vFog);
  if (any(isnan(col)) || any(isinf(col))) col = uFogCol;
  gl_FragColor = vec4(clamp(col, 0.0, 64.0), 1.0);
}`;
const SIMPLE_VS = `varying vec2 vUv; varying vec3 vWP; void main(){ vUv = uv; vec4 wp = modelMatrix * vec4(position, 1.0); vWP = wp.xyz; gl_Position = projectionMatrix * viewMatrix * wp; }`;

// ================================================================ small helpers
const basic = (o) => new THREE.MeshBasicMaterial(o);
const metal = (c = 0x0c0c0f, i = 0.25) => new THREE.MeshStandardMaterial({ color: c, metalness: 0.9, roughness: 0.35, envMap: envTex, envMapIntensity: i });
function quad(w, h, mat) { return new THREE.Mesh(new THREE.PlaneGeometry(w, h), mat); }
function loadImg(url) { return new Promise((res, rej) => { const im = new Image(); im.onload = () => res(im); im.onerror = () => rej(new Error(url)); im.src = url; }); }
async function atlasAvg(name) {
  const im = await loadImg(`/media/${name}/060.jpg`);
  const c = document.createElement('canvas'); c.width = 8; c.height = 8; const g = c.getContext('2d'); g.drawImage(im, 0, 0, 8, 8);
  const d = g.getImageData(0, 0, 8, 8).data; let r = 0, gg = 0, b = 0; for (let i = 0; i < d.length; i += 4) { r += d[i]; gg += d[i + 1]; b += d[i + 2]; }
  const n = d.length / 4; const col = new THREE.Color().setRGB(r / n / 255, gg / n / 255, b / n / 255, THREE.SRGBColorSpace);
  const hsl = {}; col.getHSL(hsl); col.setHSL(hsl.h, Math.min(1, hsl.s * 1.9 + 0.12), hsl.l * 0.8); return col;
}
const s16 = () => 60 / L.TIMING.tempo / 4;
function burstEnv(t, t0, a = 0.04, d = 0.5) { return t < t0 ? 0 : Math.min(1, (t - t0) / a) * Math.exp(-Math.max(0, t - t0 - a) / d); }
function slam(t, t0, dur = 0.09) {   // 0 before, falls in (scale from big), 1 after with a tiny settle
  if (t < t0 - dur) return { vis: false, s: 1, k: 0 };
  if (t < t0) { const x = (t - (t0 - dur)) / dur; return { vis: true, s: lerp(1.9, 1, x * x), k: x }; }
  const x = t - t0; return { vis: true, s: 1 - 0.035 * Math.sin(x * 40) * Math.exp(-x * 14), k: 1 };
}

// ================================================================ the towers
class TowerSet {
  constructor(list, clip) {
    this.list = list; const n = list.length;
    const geo = new THREE.BoxGeometry(1, 1, 1); geo.translate(0, 0.5, 0);
    this.aI = new THREE.InstancedBufferAttribute(new Float32Array(n * 4), 4); this.aG = new THREE.InstancedBufferAttribute(new Float32Array(n * 4), 4); this.aK = new THREE.InstancedBufferAttribute(new Float32Array(n), 1); this.aC = new THREE.InstancedBufferAttribute(new Float32Array(n), 1);
    this.aI.setUsage(THREE.DynamicDrawUsage); this.aG.setUsage(THREE.DynamicDrawUsage); this.aK.setUsage(THREE.DynamicDrawUsage); this.aC.setUsage(THREE.DynamicDrawUsage);
    geo.setAttribute('aInfo', this.aI); geo.setAttribute('aGrid', this.aG); geo.setAttribute('aKind', this.aK); geo.setAttribute('aCov', this.aC);
    const AH = M.ATLAS.H1, AV_ = M.ATLAS.V1;
    const dfs = clip ? { CLIP: 1 } : {}; const dbg = (typeof location !== 'undefined' && new URLSearchParams(location.search).get('dbg')) || ''; if (dbg.includes('fA')) dfs.FA = 1; if (dbg.includes('fB')) dfs.FB = 1;
    this.mat = new THREE.ShaderMaterial({ vertexShader: FAC_VS, fragmentShader: FAC_FS, defines: dfs,
      uniforms: { uAtlasH: { value: myTex('H1') }, uAtlasV: { value: myTex('V1') }, uAtH: { value: new THREE.Vector4(AH.cols, AH.rows, AH.cw, AH.ch) }, uAtV: { value: new THREE.Vector4(AV_.cols, AV_.rows, AV_.cw, AV_.ch) },
        uAvgH: { value: AVG.H1 }, uAvgV: { value: AVG.V1 },
        uTime: U.uTime, uFogCol: U.uFogCol, uFogDen: U.uFogDen, uSky: U.uSky, uBright: U.uBright, uMatch: U.uMatch, uMatchCell: U.uMatchCell, uHer: U.uHer } });
    this.im = new THREE.InstancedMesh(geo, this.mat, n); this.im.frustumCulled = false; this.im.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
    this.tw = new THREE.InstancedMesh(geo, this.mat, n); this.tw.instanceMatrix = this.im.instanceMatrix; this.tw.frustumCulled = false; this.tw.renderOrder = 1;
    this.order = list.map((_, i) => i); this._m = new THREE.Matrix4(); this.write();
  }
  write(vis = null) {
    const m = this._m; let k = 0;
    this.order.forEach((i) => { const o = this.list[i]; if (vis && !vis(o)) return; m.makeScale(o.w, o.h, o.d); m.setPosition(o.x, 0, o.z); this.im.setMatrixAt(k, m);
      this.aI.setXYZW(k, o.seed, o.rise ? o.rise[0] : -1, o.rise ? o.rise[1] : 1, o.lit); this.aG.setXYZW(k, o.g[0], o.g[1], o.g[2], o.g[3]); this.aK.setX(k, (o.atlas === 'V1' ? 1 : 0) + 2 * (o.coverFace || 0)); this.aC.setX(k, o.cover || 0); k++; });
    this.im.count = this.tw.count = k;
    this.im.instanceMatrix.needsUpdate = true; this.aI.needsUpdate = true; this.aG.needsUpdate = true; this.aK.needsUpdate = true; this.aC.needsUpdate = true;
  }
  sort(p, vis) { const d = (o) => (o.x - p.x) ** 2 + (o.z - p.z) ** 2; this.order.sort((a, b) => d(this.list[a]) - d(this.list[b])); this.write(vis); }
}
const SETS = [];
// per-instance culling: nothing off-screen, and (inside the avenue canyon) nothing the avenue buildings hide — SwiftShader
// shades every fragment it is given, hidden or not
const _frus = new THREE.Frustum(), _pm = new THREE.Matrix4(), _box = new THREE.Box3(); const OCC = [];
function segHitsBox(p, q, b) {   // slab test, segment p→q against [min,max]
  let t0 = 0, t1 = 1;
  for (let a = 0; a < 3; a++) { const d = q[a] - p[a]; if (Math.abs(d) < 1e-9) { if (p[a] < b[0][a] || p[a] > b[1][a]) return false; continue; }
    let ta = (b[0][a] - p[a]) / d, tb = (b[1][a] - p[a]) / d; if (ta > tb) { const tt = ta; ta = tb; tb = tt; } t0 = Math.max(t0, ta); t1 = Math.min(t1, tb); if (t0 > t1) return false; }
  return true;
}
function makeVis(c, canyon) {
  _pm.multiplyMatrices(c.projectionMatrix, c.matrixWorldInverse); _frus.setFromProjectionMatrix(_pm); const cp = [c.position.x, c.position.y, c.position.z];
  return (o) => {
    _box.min.set(o.x - o.w / 2, -2, o.z - o.d / 2); _box.max.set(o.x + o.w / 2, o.h + (o === HER ? 90 : 4), o.z + o.d / 2);
    if (!_frus.intersectsBox(_box)) return false;
    if (!canyon || o.ave || o === HER) return true;
    const hw = o.w / 2, hd = o.d / 2;
    for (const [px, pz] of [[o.x, o.z], [o.x - hw, o.z - hd], [o.x + hw, o.z + hd], [o.x - hw, o.z + hd], [o.x + hw, o.z - hd]]) {
      const pt = [px, o.h, pz]; if (!OCC.some((b) => segHitsBox(cp, pt, b))) return true;
    }
    return false;
  };
}
let HER = null; const SPROUTS = [];
function herGrid() { const cw = 52 / 12, ch = 3.4, fw = 0.82; return [cw, ch, fw, (cw * fw * 9 / 16) / ch]; }
function winGrid(atlas, R) {
  if (atlas[0] === 'H') { const cw = [4.0, 4.4, 4.8][Math.floor(R() * 3)], ch = [3.3, 3.6, 3.9][Math.floor(R() * 3)]; const fw = 0.78 + R() * 0.08; return [cw, ch, fw, (cw * fw * 9 / 16) / ch]; }
  const cw = [2.4, 2.7, 3.0][Math.floor(R() * 3)], ch = [4.2, 4.6][Math.floor(R() * 2)]; const fh = 0.76 + R() * 0.06; return [cw, ch, Math.min(0.92, (ch * fh * 9 / 16) / cw), fh];
}
const snap = (v, c, mn = 2) => Math.max(mn, Math.round(v / c)) * c;
// the avenue: [side, z0, z1, height, atlas]; faces at x = ±16
const AVE = [[1, 505, 640, 96, 'H1'], [1, 395, 485, 128, 'V1'], [1, 285, 375, 92, 'H1'], [1, 175, 265, 176, 'V1'], [1, 65, 155, 64, 'H1'],
  [-1, 505, 640, 112, 'V1'], [-1, 395, 485, 86, 'H1'], [-1, 285, 375, 124, 'H1'], [-1, 175, 265, 100, 'V1'], [-1, 65, 155, 58, 'V1']];
function genCity() {
  const R = L.rng(11); const all = [];
  const add = (o) => { o.seed = all.length + 2; all.push(o); return o; };
  HER = add({ x: 0, z: 0, w: 52, d: 52, h: 112 * 3.4, atlas: 'H1', g: herGrid(), lit: 0.95, rise: null }); OCC.push([[-25.5, 0, -25.5], [25.5, HER.h, 25.5]]);
  for (const [side, z0, z1, h, atlas] of AVE) {
    const g = winGrid(atlas, R); const len = snap(z1 - z0, g[0]), dep = snap(30, g[0]);
    const o = add({ x: side * (16 + dep / 2), z: z1 - len / 2, w: dep, d: len, h: snap(h, g[1]), atlas, g, lit: 0.62, rise: null, ave: true, coverFace: side > 0 ? 2 : 1, cover: side > 0 && z0 === 175 ? 152 : 52 });
    OCC.push([[o.x - o.w / 2 + 0.5, 0, o.z - o.d / 2 + 0.5], [o.x + o.w / 2 - 0.5, o.h - 0.5, o.z + o.d / 2 - 0.5]]);
  }
  const lots = [];
  for (let bx = -11; bx <= 11; bx++) for (let bz = -12; bz <= 7; bz++) {
    const cx = bx * 110, cz = bz * 110, dist = Math.hypot(cx, cz);
    if (dist > 1420 || (bx === 0 && bz >= 0 && bz <= 6)) continue;
    const r = R(), near = dist < 600;
    const split = r < (near ? 0.3 : 0.55) ? 1 : r < (near ? 0.72 : 0.86) ? 2 : 4;
    const sub = split === 1 ? [[0, 0, 90, 90]] : split === 2 ? (R() < 0.5 ? [[-23, 0, 44, 90], [23, 0, 44, 90]] : [[0, -23, 90, 44], [0, 23, 90, 44]])
      : [[-23, -23, 44, 44], [23, -23, 44, 44], [-23, 23, 44, 44], [23, 23, 44, 44]];
    for (const [ox, oz, lw, ld] of sub) lots.push({ x: cx + ox, z: cz + oz, lw, ld, dist: Math.hypot(cx + ox, cz + oz), a: Math.atan2(cx + ox, cz + oz) });
  }
  // sprout lots: the doubling waves 2 → 4 → 8 → 16, each wave a wider ring around her tower
  const waves = [[2, 165], [4, 265], [8, 375], [16, 500]];
  const used = new Set(); const angD = (a, b) => { let d = Math.abs(a - b) % TAU; return d > Math.PI ? TAU - d : d; };
  waves.forEach(([n, rad], wi) => {
    const cand = lots.map((l, i) => ({ i, l, e: Math.abs(l.dist - rad) })).filter((c) => !used.has(c.i) && c.e < 80).sort((a, b) => a.e - b.e);
    const picked = [];
    for (const sepK of [0.62, 0.4, 0.2, 0]) { for (const c of cand) { if (picked.length >= n) break; if (used.has(c.i)) continue; if (picked.every((p) => angD(p.l.a, c.l.a) > sepK * TAU / n)) { picked.push(c); used.add(c.i); } } if (picked.length >= n) break; }
    picked.sort((a, b) => a.l.a - b.l.a).forEach((c, j) => { c.l.sprout = { wave: wi, j }; });
  });
  for (const l of lots) {
    const sp = !!l.sprout;
    const atlas = sp ? (R() < 0.5 ? 'H1' : 'V1') : (R() < 0.62 ? 'H1' : 'V1');
    const g = winGrid(atlas, R);
    const fx = sp ? 0.86 : 0.58 + R() * 0.32, fz = sp ? 0.86 : 0.58 + R() * 0.32;
    const w = snap(l.lw * fx, g[0]), d = snap(l.ld * fz, g[0]);
    const base = 28 + 118 * Math.exp(-Math.pow(l.dist / 650, 2)) + 60 * Math.exp(-Math.pow((l.dist - 820) / 260, 2));
    let h = sp ? 175 + 80 * R() + (3 - l.sprout.wave) * 16 : base * (0.42 + 0.8 * R());
    if (!sp && l.dist > 900) h = Math.min(h, 70);
    h = snap(Math.min(h, 300), g[1], 4);
    const o = add({ x: l.x + (R() - 0.5) * (l.lw - w) * 0.6, z: l.z + (R() - 0.5) * (l.ld - d) * 0.6, w, d, h, atlas, g, lit: sp ? 0.94 : 0.24 + 0.3 * R(), rise: null });
    if (sp) { const s = l.sprout; const t0 = T.waves[s.wave] + s.j * (s.wave < 2 ? 0.05 : 0.026); o.rise = [t0, 0.46]; o.sprout = s; SPROUTS.push(o); }
  }
  // instanced sets: one per atlas (+ the sprouts, which need the ground clip)
  SETS.push(new TowerSet(all.filter((o) => !o.rise), false)); SETS.push(new TowerSet(all.filter((o) => o.rise), true));
  for (const s of SETS) { scene.add(s.im); mirror.add(s.tw); }
  return all;
}

// ================================================================ sky, ground, hill, sign
function buildSky() {
  const mat = new THREE.ShaderMaterial({ side: THREE.BackSide, depthWrite: false,
    uniforms: { uZen: { value: new THREE.Color(0.0006, 0.0006, 0.002) }, uHor: { value: new THREE.Color(0.0075, 0.0068, 0.015) }, uGlow: { value: new THREE.Color(0.034, 0.016, 0.03) } },
    vertexShader: `varying vec3 vD; void main(){ vD = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`,
    fragmentShader: `uniform vec3 uZen, uHor, uGlow; varying vec3 vD;
      void main(){ float e = vD.y; vec3 c = mix(uHor, uZen, pow(clamp(e, 0.0, 1.0), 0.42)); c += uGlow * exp(-max(e, 0.0) * 9.0); if (e < 0.0) c = uHor; gl_FragColor = vec4(c, 1.0); }` });
  sky = new THREE.Mesh(new THREE.SphereGeometry(9000, 32, 16), mat); sky.renderOrder = 2; scene.add(sky);
  // a few stars
  const R = L.rng(3), n = 700, pos = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) { const a = R() * TAU, e = 0.08 + Math.pow(R(), 0.7) * 1.4; pos.set([Math.cos(a) * Math.cos(e) * 8500, Math.sin(e) * 8500, Math.sin(a) * Math.cos(e) * 8500], i * 3); }
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  const st = new THREE.Points(g, new THREE.PointsMaterial({ color: new THREE.Color(0.5, 0.5, 0.6), size: 1.6, sizeAttenuation: false, depthWrite: false, fog: false, transparent: true, opacity: 0.6 }));
  st.renderOrder = 3; sky.add(st);
}
function buildGround() {
  const mat = new THREE.ShaderMaterial({ transparent: true, depthWrite: false,
    uniforms: { uFogCol: U.uFogCol, uFogDen: U.uFogDen },
    vertexShader: SIMPLE_VS,
    fragmentShader: `uniform vec3 uFogCol; uniform float uFogDen; varying vec2 vUv; varying vec3 vWP; ${GL_COMMON}
      void main(){ float n = vnoise(vWP.xz / 13.0); float wet = smoothstep(0.42, 0.72, n);
        float a = 0.9 - 0.24 * wet; vec3 c = vec3(0.0035, 0.004, 0.0065);
        float f = fogK(vWP, uFogDen); c = mix(c, uFogCol, f); a = mix(a, 1.0, f); gl_FragColor = vec4(c, a); }` });
  const g = new THREE.PlaneGeometry(9000, 9000); g.rotateX(-Math.PI / 2);
  const m = new THREE.Mesh(g, mat); m.renderOrder = 5; scene.add(m);
}
function hillH(x, z) {
  const ridge = -2950 + 120 * Math.sin(x / 800) + 50 * Math.sin(x / 290 + 1.3);
  const top = 760 + 120 * Math.sin(x / 1150 + 0.5) + 45 * Math.sin(x / 400 + 2.0) + 20 * Math.sin(x / 140 + 0.7);
  const dz = z - ridge; const k = dz > 0 ? Math.exp(-Math.pow(dz / 640, 2)) : Math.exp(-Math.pow(dz / 900, 2));
  return Math.max(-5, top * k - 30);
}
function buildHill() {
  const g = new THREE.PlaneGeometry(9000, 3000, 160, 60); g.rotateX(-Math.PI / 2);
  const p = g.attributes.position;
  for (let i = 0; i < p.count; i++) { const x = p.getX(i), z = p.getZ(i) - 3300; p.setZ(i, z); p.setY(i, hillH(x, z)); }
  g.computeVertexNormals();
  const mat = new THREE.ShaderMaterial({ uniforms: { uFogCol: U.uFogCol, uFogDen: U.uFogDen },
    vertexShader: `varying vec3 vWP; varying vec3 vN; void main(){ vec4 wp = modelMatrix * vec4(position, 1.0); vWP = wp.xyz; vN = normal; gl_Position = projectionMatrix * viewMatrix * wp; }`,
    fragmentShader: `uniform vec3 uFogCol; uniform float uFogDen; varying vec3 vWP; varying vec3 vN; ${GL_COMMON}
      void main(){ float n = vnoise(vWP.xz / 60.0); vec3 c = vec3(0.0016, 0.0017, 0.0028) * (0.7 + 0.6 * n) + vec3(0.002, 0.0014, 0.0035) * clamp(vN.z, 0.0, 1.0);
        c = mix(c, uFogCol * 0.7, fogK(vWP, uFogDen * 0.5)); gl_FragColor = vec4(c, 1.0); }` });
  const hm_ = new THREE.Mesh(g, mat); hm_.renderOrder = 1.5; scene.add(hm_);
  // houses on the slopes
  const R = L.rng(9), n = 500, pos = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) { const x = (R() - 0.5) * 6000, z = -2150 - R() * 900; pos.set([x, hillH(x, z) + 3, z], i * 3); }
  const pg = new THREE.BufferGeometry(); pg.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  scene.add(new THREE.Points(pg, new THREE.PointsMaterial({ color: new THREE.Color(1.2, 0.75, 0.4), size: 2.2, sizeAttenuation: false, transparent: true, opacity: 0.55, depthWrite: false })));
}
const beamVS = `varying float vL; varying vec3 vWP; varying vec3 vN; void main(){ vL = uv.y; vec4 wp = modelMatrix * vec4(position, 1.0); vWP = wp.xyz; vN = normalize(mat3(modelMatrix) * normal); gl_Position = projectionMatrix * viewMatrix * wp; }`;
function beamMat(color, inten, fall = 1.6) {
  return new THREE.ShaderMaterial({ transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide,
    uniforms: { uCol: { value: new THREE.Color(color) }, uInt: { value: inten }, uFade: { value: 0 }, uFall: { value: fall } },
    vertexShader: beamVS,
    fragmentShader: `uniform vec3 uCol; uniform float uInt, uFade, uFall; varying float vL; varying vec3 vWP; varying vec3 vN;
      void main(){ vec3 Vd = cameraPosition - vWP; float f = clamp(abs(dot(normalize(vN), Vd) * inversesqrt(max(dot(Vd, Vd), 1e-4))), 0.0, 1.0); float a = pow(f, 2.5) * pow(clamp(1.0 - vL, 0.0, 1.0), uFall) * smoothstep(0.0, 0.015, vL);
        vec3 c = uCol * (uInt * a * uFade); if (any(isnan(c))) c = vec3(0.0); gl_FragColor = vec4(c, 1.0); }` });
}
function beam(len, r0, r1, mat) { const g = new THREE.CylinderGeometry(r1, r0, len, 24, 1, true); g.translate(0, len / 2, 0); return new THREE.Mesh(g, mat); }
const SIGN = { letters: [], spots: [], lamps: null };
function buildSign() {
  const text = 'LOOK WHAT I CAN DO', Lh = 118, F = 360, font = `${F}px ${L.FONT.dispBlack}`;
  const g0 = document.createElement('canvas').getContext('2d'); g0.font = font;
  const capPx = g0.measureText('H').actualBoundingBoxAscent; const k = Lh / capPx;
  const track = 0.2 * Lh, gap = 0.62 * Lh; const items = []; let x = 0;
  for (const ch of text) { if (ch === ' ') { x += gap; continue; } const w = g0.measureText(ch).width * k; items.push({ ch, x0: x, w }); x += w + track; }
  const total = x - track; const R = L.rng(21);
  const lineWords = L.line('Look what I can do!', 5).wt; const wordOf = [0, 0, 0, 0, 1, 1, 1, 1, 2, 3, 3, 3, 4, 4]; const idxIn = [0, 1, 2, 3, 0, 1, 2, 3, 0, 0, 1, 2, 0, 1];
  const lampPos = [], stilts = [];
  items.forEach((it, i) => {
    const cx = it.x0 + it.w / 2 - total / 2 - 150;
    const yb = 455 + 22 * Math.sin(cx / 520 + 0.4) + (R() - 0.5) * 7;
    let za = -2100, zb = -2900; const ground = yb - 16;   // the slope point under the letter
    for (let s = 0; s < 40; s++) { const zm = (za + zb) / 2; if (hillH(cx, zm) < ground) za = zm; else zb = zm; }
    const z = za; const pad = 0.12 * capPx;
    const tex = L.canvasTex(Math.ceil(it.w / k + pad * 2), Math.ceil(capPx + pad * 2), (g, w, h) => {
      g.font = font; g.textBaseline = 'alphabetic'; g.textAlign = 'center';
      const gr = g.createLinearGradient(0, pad, 0, pad + capPx); gr.addColorStop(0, '#c9cdd6'); gr.addColorStop(0.55, '#eef0f4'); gr.addColorStop(1, '#ffffff');
      g.fillStyle = gr; g.fillText(it.ch, w / 2, pad + capPx);
      g.globalCompositeOperation = 'source-atop'; g.fillStyle = 'rgba(0,0,0,0.13)';
      for (let yy = pad + capPx * 0.2; yy < pad + capPx; yy += capPx * 0.2) g.fillRect(0, yy, w, Math.max(2, capPx * 0.012));
    });
    const mat = basic({ map: tex, transparent: true, depthWrite: false, fog: false, color: 0x101010 });
    const m = quad(it.w + pad * 2 * k, Lh + pad * 2 * k, mat); m.position.set(cx, yb + Lh / 2, z + 3); m.rotation.z = (R() - 0.5) * 0.03; m.rotation.y = (R() - 0.5) * 0.06;
    scene.add(m);
    const t0 = lineWords[wordOf[i]] + idxIn[i] * 0.055;
    SIGN.letters.push({ m, t0, seed: i + 5 });
    for (const sx of [-0.3, 0.3]) {
      const lp = V3(cx + sx * it.w, 0, z + 34); lp.y = hillH(lp.x, lp.z) + 2;
      const tgt = V3(cx + sx * it.w * 0.5, yb + Lh * 0.55, z + 3); const dir = tgt.clone().sub(lp); const len = dir.length(); dir.normalize();
      const bm = beam(len * 1.15, 0.8, it.w * 0.42, beamMat(0xfff1dc, 0.11, 1.2)); bm.position.copy(lp); bm.quaternion.setFromUnitVectors(UPV, dir); scene.add(bm);
      SIGN.spots.push({ m: bm, li: i }); lampPos.push(lp.x, lp.y, lp.z);
    }
    for (const sx of [-0.34, 0, 0.34]) { const sz = z + 1, top = yb + 4, bot = hillH(cx + sx * it.w, sz) - 4; stilts.push([cx + sx * it.w, (top + bot) / 2, sz, top - bot]); }
  });
  const sg = new THREE.InstancedMesh(new THREE.BoxGeometry(3.2, 1, 3.2), basic({ color: 0x2a2a30, fog: false }), stilts.length);
  const mm = new THREE.Matrix4(); stilts.forEach(([sx, sy, sz, sh], i) => { mm.makeScale(1, sh, 1); mm.setPosition(sx, sy, sz); sg.setMatrixAt(i, mm); });
  SIGN.stilts = sg; scene.add(sg);
  const lg = new THREE.BufferGeometry(); lg.setAttribute('position', new THREE.BufferAttribute(new Float32Array(lampPos), 3));
  lg.setAttribute('aB', new THREE.BufferAttribute(new Float32Array(lampPos.length / 3), 1));
  SIGN.lamps = new THREE.Points(lg, glowPointsMat(new THREE.Color(1.6, 1.4, 1.1), 7)); scene.add(SIGN.lamps);
}
function glowPointsMat(col, px) {   // screen-sized soft dots with a per-point brightness
  return new THREE.ShaderMaterial({ transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
    uniforms: { uCol: { value: col }, uPx: { value: px }, uDot: { value: L.dotTex() } },
    vertexShader: `attribute float aB; varying float vB; uniform float uPx; void main(){ vB = aB; vec4 mv = modelViewMatrix * vec4(position, 1.0); gl_Position = projectionMatrix * mv; gl_PointSize = uPx * (0.4 + 0.6 * aB); }`,
    fragmentShader: `uniform vec3 uCol; uniform sampler2D uDot; varying float vB; void main(){ float a = texture2D(uDot, gl_PointCoord).r; gl_FragColor = vec4(uCol * a * vB, 1.0); }` });
}
function signLevel(t) {   // blaze on the "Look what I can do!" lines, 35% under the jokes
  const on = (a, b) => sstep(a - 0.12, a + 0.02, t) * (1 - sstep(b - 0.04, b + 0.22, t));
  return 0.35 + 0.65 * Math.max(on(T.l2, T.made), on(T.l3, T.res));
}
function updateSign(t) {
  const lamps = SIGN.lamps.geometry.attributes.aB; const pulse = L.beatPulse(t, 6);
  const lvl = signLevel(t);
  SIGN.letters.forEach((L_, i) => {
    const f = flicker(t, L_.t0, L_.seed); L_.f = f * lvl;
    const v = 0.012 + f * lvl * (0.98 + 0.06 * pulse) + 0.35 * burstEnv(t, L_.t0, 0.02, 0.18);   // under the bloom threshold: crisp letters
    L_.m.material.color.setScalar(v);
  });
  SIGN.spots.forEach((s, i) => { const f = SIGN.letters[s.li].f; s.m.material.uniforms.uFade.value = f; lamps.setX(i, f * (1 + 1.5 * burstEnv(t, SIGN.letters[s.li].t0, 0.02, 0.15))); });
  lamps.needsUpdate = true;
  const lit = SIGN.letters.reduce((a, l) => a + l.f, 0) / SIGN.letters.length;
  SIGN.stilts.material.color.setScalar(0.03 + 0.2 * lit);
}

// ================================================================ city life: traffic, street lights, aviation lights
let TRAFFIC = null, TRAFFIC_M = null, LIGHTS = null, AVIA = null;
function buildTraffic() {
  const R = L.rng(31), lane = [], car = [];
  const streets = []; for (let k = -12; k <= 11; k++) streets.push((k + 0.5) * 110);
  for (const s of streets) for (const along of [0, 1]) for (const dir of [1, -1]) {
    if (along === 0 && Math.abs(s) < 60) continue;   // no street down the avenue itself (pedestrian)
    const len = 2900, n = 20 + Math.floor(R() * 10);
    for (let i = 0; i < n; i++) {
      const off = dir * 3.6; const x0 = along === 0 ? s + off : -1450, z0 = along === 0 ? -1450 : s + off;
      const ang = along === 0 ? (dir > 0 ? Math.PI / 2 : -Math.PI / 2) : (dir > 0 ? 0 : Math.PI);
      const sx = along === 0 ? x0 : (dir > 0 ? -1450 : 1450), sz = along === 0 ? (dir > 0 ? -1450 : 1450) : z0;
      lane.push(sx, sz, ang, len); car.push(9 + R() * 8, R() * len, dir > 0 ? 0 : 1, 2.2 + R() * 0.8);
    }
  }
  const n = lane.length / 4; const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(n * 3), 3));
  g.setAttribute('aLane', new THREE.BufferAttribute(new Float32Array(lane), 4)); g.setAttribute('aCar', new THREE.BufferAttribute(new Float32Array(car), 4));
  const mat = new THREE.ShaderMaterial({ transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
    uniforms: { uTime: U.uTime, uScale: { value: 500 }, uDot: { value: L.dotTex() }, uFogCol: U.uFogCol, uFogDen: U.uFogDen },
    vertexShader: `attribute vec4 aLane; attribute vec4 aCar; uniform float uTime, uScale; varying vec3 vCol; varying float vF; uniform float uFogDen;
      void main(){ float s = mod(aCar.y + aCar.x * uTime, aLane.w); vec2 d = vec2(cos(aLane.z), sin(aLane.z)); vec3 p = vec3(aLane.x + d.x * s, 1.0, aLane.y + d.y * s);
        vec4 wp = modelMatrix * vec4(p, 1.0); vec4 mv = viewMatrix * wp; gl_Position = projectionMatrix * mv; gl_PointSize = clamp(aCar.w * uScale / -mv.z, 1.0, 14.0);
        vCol = aCar.z < 0.5 ? vec3(1.5, 1.35, 1.1) : vec3(1.6, 0.1, 0.06); float dd = length(cameraPosition - wp.xyz) * uFogDen; vF = exp(-dd * dd); }`,
    fragmentShader: `uniform sampler2D uDot; varying vec3 vCol; varying float vF; void main(){ float a = texture2D(uDot, gl_PointCoord).r; gl_FragColor = vec4(vCol * a * vF, 1.0); }` });
  TRAFFIC = new THREE.Points(g, mat); TRAFFIC.frustumCulled = false; scene.add(TRAFFIC);
  TRAFFIC_M = new THREE.Points(g, mat); TRAFFIC_M.frustumCulled = false; mirror.add(TRAFFIC_M);
  // street lights
  const lp = [];
  for (const s of streets) for (let q = -1400; q < 1400; q += 46) for (const side of [-1, 1]) {
    const a = s + side * 9; if (Math.abs(s) < 60 && q > 40 && q < 650) continue;
    lp.push(a, 9, q, q + 23, 9, a);
  }
  const lg = new THREE.BufferGeometry(); lg.setAttribute('position', new THREE.BufferAttribute(new Float32Array(lp), 3));
  const lmat = new THREE.PointsMaterial({ color: new THREE.Color(1.3, 0.72, 0.36), size: 2.6, map: L.dotTex(), transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, opacity: 0.8 });
  LIGHTS = new THREE.Points(lg, lmat); scene.add(LIGHTS); const lm = new THREE.Points(lg, lmat); mirror.add(lm);
}
function buildAviation(all) {
  const p = [], ph = [];
  for (const o of all) if (o.h > 175 && !o.rise) { p.push(o.x, o.h + 2, o.z); ph.push((o.seed * 0.37) % 1); }
  p.push(0, 463.5, 0); ph.push(0.5);
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(p), 3)); g.setAttribute('aB', new THREE.BufferAttribute(new Float32Array(ph.length), 1));
  AVIA = new THREE.Points(g, glowPointsMat(new THREE.Color(2.4, 0.15, 0.1), 9)); AVIA.userData.ph = ph; scene.add(AVIA);
}

// ================================================================ the sprouts' ground glow
const RINGS = [];
function buildRings() {
  const tex = L.canvasTex(256, 256, (g) => { const gr = g.createRadialGradient(128, 128, 40, 128, 128, 128); gr.addColorStop(0, 'rgba(255,255,255,0)'); gr.addColorStop(0.72, 'rgba(255,255,255,0.9)'); gr.addColorStop(0.8, 'rgba(255,255,255,0.35)'); gr.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = gr; g.fillRect(0, 0, 256, 256); }, { linear: true });
  for (const o of SPROUTS) {
    const m = quad(1, 1, basic({ map: tex, color: new THREE.Color(2.4, 0.9, 1.7), transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, opacity: 0 }));
    m.rotation.x = -Math.PI / 2; m.position.set(o.x, 0.6, o.z); m.renderOrder = 6; scene.add(m);
    // the birth: a pillar of light the tower rises inside
    const col = beam(380, Math.max(o.w, o.d) * 0.4, Math.max(o.w, o.d) * 0.26, beamMat(0xffd6ee, 1.6, 2.2)); col.position.set(o.x, 0, o.z); col.visible = false; scene.add(col);
    RINGS.push({ m, o, col });
  }
}
function updateRings(t) {
  for (const { m, o, col } of RINGS) {
    const x = t - o.rise[0]; const on = x >= -0.04 && x < 1.6; m.visible = on && x >= 0; col.visible = on && x < 0.9;
    if (!on) continue;
    if (m.visible) { const r = Math.max(o.w, o.d) * (1.15 + 1.5 * easeOut(x / 1.0)); m.scale.set(r, r, 1); m.material.opacity = 0.9 * Math.min(1, x / 0.04) * Math.exp(-x / 0.4); }
    if (col.visible) { const e = Math.min(1, (x + 0.04) / 0.05) * Math.exp(-Math.max(0, x) / 0.17); col.material.uniforms.uFade.value = 1.4 * e; col.scale.set(1, 0.6 + 0.6 * Math.min(1, (x + 0.04) / 0.1), 1); }
  }
}

// ================================================================ searchlights
const SEARCH = [];
function buildSearch() {
  const bases = [[-44, 44, 0.3, 1], [44, 44, 2.2, 0], [-44, -44, 4.1, 1], [44, -44, 5.6, 0]];
  bases.forEach(([x, z, ph, grp], i) => { const m = beam(2800, 1.4, 110, beamMat(0xdfe6ff, 0.13, 1.0)); m.position.set(x, 3, z); scene.add(m); SEARCH.push({ m, ph, grp, i }); });
}
function updateSearch(t) {
  for (const s of SEARCH) {
    const t0 = s.grp === 0 ? T.l3 : T.l4; const f = flicker(t, t0, s.i + 40) * (1 - sstep(T.res - 0.15, T.res + 0.3, t));
    s.m.visible = f > 0.01; if (!s.m.visible) continue;
    s.m.material.uniforms.uFade.value = f * (1 + 1.5 * burstEnv(t, t0, 0.02, 0.2));
    const az = s.ph + 0.7 * Math.sin(t * 0.8 + s.ph * 2) + 0.3 * t; const el = (52 + 16 * Math.sin(t * 1.1 + s.ph)) * D2R;
    const d = V3(Math.cos(el) * Math.sin(az), Math.sin(el), Math.cos(el) * Math.cos(az)); s.m.quaternion.setFromUnitVectors(UPV, d);
  }
}

// ================================================================ her tower: crown, AI GURU, résumé
const CROWN = { edges: [] }, RES = { pages: [], tag: null, roll: null, n: -1 };
function buildCrown() {
  const dark = basic({ color: new THREE.Color(0.004, 0.0045, 0.007) });
  const t1 = new THREE.Mesh(new THREE.BoxGeometry(44, 24, 44), dark); t1.position.set(0, HER.h + 12, 0); scene.add(t1);
  const t2 = new THREE.Mesh(new THREE.BoxGeometry(32, 18, 32), dark); t2.position.set(0, HER.h + 33, 0); scene.add(t2);
  const sp = new THREE.Mesh(new THREE.BoxGeometry(1.6, 40, 1.6), dark); sp.position.set(0, HER.h + 62, 0); scene.add(sp);
  const em = basic({ color: new THREE.Color(0.02, 0.008, 0.014), toneMapped: false });
  const edge = (x, y, z, sx, sy, sz) => { const m = new THREE.Mesh(new THREE.BoxGeometry(sx, sy, sz), em); m.position.set(x, y, z); scene.add(m); };
  for (const [hw, y0, hh] of [[22.3, HER.h, 24], [16.3, HER.h + 24, 18]]) {
    for (const sx of [-1, 1]) for (const sz of [-1, 1]) edge(sx * hw, y0 + hh / 2, sz * hw, 0.7, hh, 0.7);
    for (const s of [-1, 1]) { edge(0, y0 + hh, s * hw, hw * 2, 0.7, 0.7); edge(s * hw, y0 + hh, 0, 0.7, 0.7, hw * 2); }
  }
  CROWN.em = em;
  // pale architectural light up her tower's corners, so it reads as hers in the skyline
  const cl = basic({ color: new THREE.Color(0.55, 0.45, 0.6) });
  for (const sx of [-1, 1]) for (const sz of [-1, 1]) { const m = new THREE.Mesh(new THREE.BoxGeometry(0.5, HER.h, 0.5), cl); m.position.set(sx * 26.1, HER.h / 2, sz * 26.1); scene.add(m); }
  const ng = neon('AI GURU', { h: 19, color: '#ff5fa2', core: '#ffe3f0', size: 220 }); ng.position.set(0, HER.h + 12, 22.6); ng.material.color.setScalar(1.45); scene.add(ng); CROWN.neon = ng;
}
function updateCrown(t) {
  const f = flicker(t, T.ai, 7), f2 = flicker(t, T.guruW, 9), pulse = L.beatPulse(t, 6);
  CROWN.neon.material.opacity = 0.018 + 0.98 * f * (0.9 + 0.1 * pulse) + 0.6 * burstEnv(t, T.guruW, 0.02, 0.25);
  CROWN.em.color.setRGB(0.02 + 2.4 * f2, 0.008 + 0.75 * f2, 0.014 + 1.5 * f2);
}
const PAGE_W = 18, PAGE_H = 23.3, RES_TOP = 373;
const RES_LINES = [['Prompted', '9,000 things'], ['Vibe-coded', 'a startup', '(twice)'], ['Reply guy,', 'Claude']];
function buildResume() {
  const pw = 600, ph = 776, cols = 7, mx = 44;
  const tex = L.canvasTex(pw * cols, ph * 2, (g) => {
    const R = L.rng(55);
    const fit = (txt, size, font, maxW) => { let f = size; g.font = `${f}px ${font}`; while (g.measureText(txt).width > maxW && f > 10) { f -= 2; g.font = `${f}px ${font}`; } return f; };
    for (let i = 0; i < 14; i++) {
      const ox = (i % cols) * pw, oy = Math.floor(i / cols) * ph;
      g.save(); g.beginPath(); g.rect(ox, oy, pw, ph); g.clip();   // nothing leaves its page
      g.fillStyle = '#f3f1ec'; g.fillRect(ox, oy, pw, ph); g.fillStyle = '#d9d6cf'; g.fillRect(ox, oy + ph - 3, pw, 3);
      let y = oy + 54; g.textBaseline = 'top'; g.textAlign = 'left';
      if (i === 0) {
        fit('ADITA', 168, L.FONT.anton, pw - mx * 2); g.fillStyle = '#111'; g.fillText('ADITA', ox + mx, y - 10); y += 196;
        g.fillStyle = '#ff5fa2'; g.fillRect(ox + mx, y, pw - mx * 2, 10); y += 46;
      }
      const lines = RES_LINES[i];
      if (lines) {
        for (const ln of lines) { fit(ln, 100, L.FONT.anton, pw - mx * 2); g.fillStyle = '#1b1b1d'; g.fillText(ln, ox + mx, y); y += 112; }
        y += 26;
      }
      while (y < oy + ph - 96) {
        g.fillStyle = '#3c3c3c'; g.fillRect(ox + mx, y, 120 + R() * 170, 20); y += 40;
        const nb = 2 + Math.floor(R() * 4);
        for (let b = 0; b < nb && y < oy + ph - 90; b++) { g.fillStyle = '#aaaaaa'; const bul = R() < 0.5; if (bul) g.fillRect(ox + mx + 2, y + 2, 10, 10); g.fillRect(ox + mx + (bul ? 24 : 0), y, (pw - mx * 2 - 24) * (0.5 + 0.5 * R()), 13); y += 27; }
        y += 18;
      }
      g.fillStyle = '#7a7a7a'; g.font = `30px ${L.FONT.monoB}`; g.textBaseline = 'alphabetic'; g.textAlign = 'right'; g.fillText(`${i + 1} / 14`, ox + pw - 34, oy + ph - 30);
      g.restore();
    }
  });
  const mat = rawTexMat(tex, 0.66);
  for (let i = 0; i < 14; i++) {
    const geo = new THREE.PlaneGeometry(1, 1); geo.translate(0, -0.5, 0);
    const m = new THREE.Mesh(geo, mat); m.position.set(0, RES_TOP - i * PAGE_H, 26.35 + i * 0.001); m.visible = false; m.renderOrder = -2; scene.add(m);
    RES.pages.push({ m, rect: [(i % cols) / cols, 1 - (Math.floor(i / cols) + 1) / 2, 1 / cols, 0.5] });
  }
  const rg = new THREE.CylinderGeometry(1.15, 1.15, PAGE_W + 0.6, 20); rg.rotateZ(Math.PI / 2);
  RES.roll = new THREE.Mesh(rg, new THREE.MeshStandardMaterial({ color: 0xe9e6df, roughness: 0.55, metalness: 0.0, envMap: envTex, envMapIntensity: 0.55 }));
  RES.roll.visible = false; scene.add(RES.roll);
  RES.tagTex = L.canvasTex(1600, 240, () => {});
  RES.tag = quad(28, 4.2, rawTexMat(RES.tagTex, 0.95, { transparent: true })); RES.tag.visible = false; scene.add(RES.tag);
  // unroll schedule: the first three pages at reading pace, then the other eleven race to 14 on "pages"
  const a = T.resW - 0.12, b = a + 0.32, c = b + 0.3, d = c + 0.28, e = T.pagesW;
  RES.sched = [[a, b], [b, c], [c, d]]; RES.race = [d, e];
}
function drawTag(n) {
  if (n === RES.n) return; RES.n = n;
  const g = RES.tagTex.userData.g; g.clearRect(0, 0, 1600, 240);
  g.fillStyle = '#0c0c0e'; g.beginPath(); g.roundRect(6, 6, 1588, 228, 40); g.fill(); g.strokeStyle = '#ff5fa2'; g.lineWidth = 10; g.stroke();
  g.textBaseline = 'middle'; g.textAlign = 'center';
  const s1 = 'résumé.pdf  ·  page ', s2 = `${n} / 14`; let f = 104; g.font = `${f}px ${L.FONT.monoB}`;
  while (g.measureText(s1 + '14 / 14').width > 1500) { f -= 2; g.font = `${f}px ${L.FONT.monoB}`; }
  const w1 = g.measureText(s1).width, w2 = g.measureText('14 / 14').width, x0 = 800 - (w1 + w2) / 2;
  g.textAlign = 'left'; g.fillStyle = '#d8d8dc'; g.fillText(s1, x0, 124); g.fillStyle = '#ff7fb5'; g.fillText(s2, x0 + w1, 124);
  RES.tagTex.needsUpdate = true;
}
function resState(t) {   // pages unrolled (float)
  if (t <= RES.sched[0][0]) return 0;
  for (let i = 0; i < 3; i++) { const [a, b] = RES.sched[i]; if (t < b) return i + easeOut((t - a) / (b - a)); }
  const [d, e] = RES.race; if (t < e) return 3 + 11 * sstep(0, 1, (t - d) / (e - d));
  return 14;
}
function updateResume(t) {
  const st = resState(t); const on = t >= RES.sched[0][0] - 0.02;
  RES.roll.visible = on && st < 14.0 && t < 100; RES.tag.visible = on && t < 100;
  RES.pages.forEach((p, i) => {
    const k = clamp(st - i); p.m.visible = on && k > 0.001; if (!p.m.visible) return;
    p.m.scale.set(PAGE_W, PAGE_H * k, 1);
    const uv = p.m.geometry.attributes.uv; const [u0, v0, su, sv] = p.rect;
    uv.setXY(0, u0, v0 + sv); uv.setXY(1, u0 + su, v0 + sv); uv.setXY(2, u0, v0 + sv * (1 - k)); uv.setXY(3, u0 + su, v0 + sv * (1 - k)); uv.needsUpdate = true;
  });
  const y = RES_TOP - st * PAGE_H;
  RES.roll.position.set(0, y - 0.2, 27.6); RES.roll.rotation.x = -st * 6.0;
  drawTag(Math.max(1, Math.min(14, Math.ceil(st - 1e-4))));
  const ty = (st >= 14 ? RES_TOP - 14 * PAGE_H : y) - 3.9;
  RES.tag.position.set(0, ty, 28.9); RES.tag.rotation.z = 0.015 * Math.sin(t * 5.0) * (st < 14 ? 1 : 0.4);
  RES.tag.scale.setScalar(1 + 0.06 * burstEnv(t, RES.race[1], 0.03, 0.2));
}
function resTarget(t) { return RES_TOP - resState(t) * PAGE_H + 9; }   // what the camera locks to: the roll, last page above, counter below

// ================================================================ sparkles (deterministic bursts)
let SPARK = null; const BURSTS = [];
function starTex() {
  return L.canvasTex(128, 128, (g) => {
    const c = 64; const gr = g.createRadialGradient(c, c, 0, c, c, 22); gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = gr; g.fillRect(0, 0, 128, 128);
    for (const [w, l] of [[3.2, 62], [2.2, 30]]) for (const a of (l > 40 ? [0, Math.PI / 2] : [Math.PI / 4, -Math.PI / 4])) {
      g.save(); g.translate(c, c); g.rotate(a); const lg = g.createLinearGradient(-l, 0, l, 0); lg.addColorStop(0, 'rgba(255,255,255,0)'); lg.addColorStop(0.5, 'rgba(255,255,255,1)'); lg.addColorStop(1, 'rgba(255,255,255,0)');
      g.fillStyle = lg; g.fillRect(-l, -w / 2, l * 2, w); g.restore(); }
  }, { linear: true });
}
function buildSpark() {
  const N = 900; const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(N * 3), 3)); g.setAttribute('aS', new THREE.BufferAttribute(new Float32Array(N), 1)); g.setAttribute('aC', new THREE.BufferAttribute(new Float32Array(N * 3), 3));
  const mat = new THREE.ShaderMaterial({ transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, uniforms: { uTex: { value: starTex() }, uScale: { value: 500 } },
    vertexShader: `attribute float aS; attribute vec3 aC; varying vec3 vC; uniform float uScale; void main(){ vC = aC; vec4 mv = modelViewMatrix * vec4(position, 1.0); gl_Position = projectionMatrix * mv; gl_PointSize = clamp(aS * uScale / -mv.z, 0.0, 90.0); }`,
    fragmentShader: `uniform sampler2D uTex; varying vec3 vC; void main(){ gl_FragColor = vec4(vC * texture2D(uTex, gl_PointCoord).r, 1.0); }` });
  SPARK = new THREE.Points(g, mat); SPARK.frustumCulled = false; SPARK.renderOrder = 8; scene.add(SPARK);
}
function updateSpark(t) {
  const P = SPARK.geometry.attributes.position, S = SPARK.geometry.attributes.aS, C = SPARK.geometry.attributes.aC; let k = 0; const N = P.count;
  for (const b of BURSTS) {
    const age0 = t - b.t0; if (age0 < 0 || age0 > b.life + 0.4) continue;
    const R = L.rng(b.seed);
    for (let i = 0; i < b.n && k < N; i++) {
      const delay = R() * b.spread, a = R() * TAU, e = (R() * 2 - 1), sp = b.speed * (0.35 + 0.65 * R()), life = b.life * (0.6 + 0.4 * R()), sz = b.size * (0.5 + R()), tw = R() * 10;
      const age = age0 - delay; if (age < 0 || age > life) continue;
      const r = Math.sqrt(1 - e * e); let dx = Math.cos(a) * r, dy = b.up ? Math.abs(e) : e, dz = Math.sin(a) * r;
      let ox = 0, oy = 0, oz = 0;
      if (b.box) { ox = (R() - 0.5) * b.box[0]; oy = (R() - 0.5) * b.box[1]; }
      if (b.rect) {   // start on the border of a rect in the y-z plane and fly outward, away from what it frames
        const per = 2 * (b.rect[0] + b.rect[1]); let u = R() * per; const hw = b.rect[0] / 2, hh = b.rect[1] / 2;
        if (u < b.rect[0]) { oz = -hw + u; oy = hh; } else if ((u -= b.rect[0]) < b.rect[1]) { oz = hw; oy = hh - u; } else if ((u -= b.rect[1]) < b.rect[0]) { oz = hw - u; oy = -hh; } else { u -= b.rect[0]; oz = -hw; oy = -hh + u; }
        const l = Math.hypot(oy, oz * 0.45) || 1; dx = -0.15 * R(); dy = oy / l * 0.8 + (R() - 0.5) * 0.4; dz = (oz * 0.45) / l * 0.8 + (R() - 0.5) * 0.4;
      }
      const dist = sp * (1 - Math.exp(-age * 3)) / 3;
      P.setXYZ(k, b.c.x + ox + dx * dist, b.c.y + oy + dy * dist - b.grav * age * age, b.c.z + oz + dz * dist);
      const fade = Math.min(1, age / 0.04) * (1 - age / life) * (0.6 + 0.4 * Math.sin(age * 30 + tw));
      S.setX(k, sz * (0.6 + 0.4 * Math.sin(age * 24 + tw))); C.setXYZ(k, b.col.r * fade, b.col.g * fade, b.col.b * fade); k++;
    }
  }
  for (let i = k; i < N; i++) S.setX(i, 0);
  P.needsUpdate = true; S.needsUpdate = true; C.needsUpdate = true; SPARK.geometry.setDrawRange(0, Math.max(1, k));
}

// ================================================================ the avenue: billboards, receipts, zipper, minis, agents, jumbotron, ticker
const AV = { boards: {}, hl: [], stamps: [] };
function cardTex(img, ch) { return L.canvasTex(img.naturalWidth, ch, (g, w, h) => { g.fillStyle = '#ffffff'; g.fillRect(0, 0, w, h); g.drawImage(img, 0, 0); }); }
function stampTex(l1, l2, col, seed, s1 = 220, s2 = 132) {
  return L.canvasTex(1000, 520, (g, w, h) => {
    g.fillStyle = '#ffffff'; g.fillRect(0, 0, w, h); g.strokeStyle = col; g.fillStyle = col;
    g.lineWidth = 22; g.beginPath(); g.roundRect(22, 22, w - 44, h - 44, 44); g.stroke();
    g.lineWidth = 7; g.beginPath(); g.roundRect(52, 52, w - 104, h - 104, 28); g.stroke();
    g.textAlign = 'center'; g.textBaseline = 'middle';
    g.font = `${s1}px ${L.FONT.anton}`; g.fillText(l1, w / 2, h * 0.41);
    g.font = `${s2}px ${L.FONT.anton}`; g.fillText(l2, w / 2, h * 0.75);
    const R = L.rng(seed); g.fillStyle = '#ffffff';
    for (let i = 0; i < 1400; i++) { const x = R() * w, y = R() * h, r = 0.7 + R() * R() * 6; g.globalAlpha = 0.45 + R() * 0.55; g.beginPath(); g.arc(x, y, r, 0, TAU); g.fill(); }
    for (let i = 0; i < 26; i++) { g.globalAlpha = 0.25 + R() * 0.3; g.fillRect(R() * w, R() * h, 30 + R() * 140, 2 + R() * 3); }
    g.globalAlpha = 1;
  });
}
const MUL_VS = `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`;
function hlMat(seed) {
  return new THREE.ShaderMaterial({ transparent: true, depthWrite: false, blending: THREE.MultiplyBlending,
    uniforms: { uProg: { value: 0 }, uCol: { value: new THREE.Color('#ffe14d') }, uSeed: { value: seed } }, vertexShader: MUL_VS,
    fragmentShader: `uniform float uProg, uSeed; uniform vec3 uCol; varying vec2 vUv;
      void main(){ float x = vUv.x, y = vUv.y;
        float wob = 0.035 * sin(x * 29.0 + uSeed) + 0.022 * sin(x * 71.0 + uSeed * 3.1);
        float m = smoothstep(0.03 + wob, 0.1 + wob, y) * (1.0 - smoothstep(0.9 - wob, 0.97 - wob, y));
        float head = uProg * 1.05;
        m *= 1.0 - smoothstep(head - 0.025, head, x);
        m *= smoothstep(0.0, 0.02, x) * (1.0 - smoothstep(0.98, 1.0, x));
        m *= 0.84 + 0.16 * sin(y * 52.0 + x * 7.0 + uSeed);
        gl_FragColor = vec4(mix(vec3(1.0), uCol, m), 1.0); }` });
}
function mulTexMat(tex) {
  const m_ = new THREE.ShaderMaterial({ transparent: true, depthWrite: false, blending: THREE.MultiplyBlending, uniforms: { map: { value: tex }, uAmt: { value: 0 } }, vertexShader: MUL_VS,
    fragmentShader: `uniform sampler2D map; uniform float uAmt; varying vec2 vUv; void main(){ vec3 c = texture2D(map, vUv).rgb; c *= c; gl_FragColor = vec4(mix(vec3(1.0), c, uAmt), 1.0); }` });
  tex.colorSpace = THREE.NoColorSpace; tex.minFilter = THREE.LinearMipmapNearestFilter; tex.needsUpdate = true; return m_;
}
// a frame that only exists where it is seen: four bars round a w x h opening, plus a back panel facing away (culled from the front)
function borderFrame(w, h, bw, depth, mat) {
  const g = new THREE.Group(); const bar = (sx, sy, x, y) => { const m = new THREE.Mesh(new THREE.BoxGeometry(sx, sy, depth), mat); m.position.set(x, y, -depth / 2); g.add(m); };
  bar(w + bw * 2, bw, 0, h / 2 + bw / 2); bar(w + bw * 2, bw, 0, -h / 2 - bw / 2); bar(bw, h, -w / 2 - bw / 2, 0); bar(bw, h, w / 2 + bw / 2, 0);
  const back = new THREE.Mesh(new THREE.PlaneGeometry(w + bw * 2, h + bw * 2), mat); back.rotation.y = Math.PI; back.position.z = -depth; g.add(back);
  return g;
}
const FRAME_MAT = () => basic({ color: new THREE.Color(0.016, 0.016, 0.02) });
// a billboard showing a card (her post on white): frame, display, mirror copy; px() maps card pixels to local metres
function makeBoard(tex, cw, ch, w, pos, yaw, rim = PINKC) {
  const h = w * ch / cw; const root = new THREE.Group(); root.position.copy(pos); root.rotation.y = yaw;
  const fr = borderFrame(w + 0.34, h + 0.34, 0.24, 0.5, metal(0x0b0b0e, 0.3)); root.add(fr);
  const rm = borderFrame(w, h, 0.17, 0.08, basic({ color: rim })); rm.position.z = 0.03; root.add(rm);
  const disp = quad(w, h, rawTexMat(tex, 0.8)); disp.position.z = 0.04; root.add(disp);
  const arm = new THREE.Mesh(new THREE.BoxGeometry(0.5, 0.5, 3.4), metal(0x0b0b0e, 0.2)); arm.position.set(w * 0.25, h * 0.25, -1.9); root.add(arm);
  const arm2 = arm.clone(); arm2.position.set(w * 0.25, -h * 0.25, -1.9); root.add(arm2);
  root.traverse((o) => { o.renderOrder = -1; }); disp.renderOrder = -2; scene.add(root);
  const tw = new THREE.Mesh(disp.geometry, disp.material); tw.renderOrder = 1; mirror.add(tw); root.updateMatrixWorld(true); tw.position.copy(disp.getWorldPosition(new THREE.Vector3())); tw.quaternion.copy(disp.getWorldQuaternion(new THREE.Quaternion()));
  const n = V3(Math.sin(yaw), 0, Math.cos(yaw));
  return { root, disp, w, h, cw, ch, n, c: pos.clone(), px: (x, y) => V3((x / cw - 0.5) * w, (0.5 - y / ch) * h, 0) };
}
const PINKC = new THREE.Color(1.2, 0.3, 0.6), AMBERC = new THREE.Color(1.2, 0.5, 0.11), GREENC = new THREE.Color(0.38, 1.15, 0.33), WHITEC = new THREE.Color(0.85, 0.85, 0.9);
function addHL(b, box, t0, dur, seed) {
  const [x0, y0, x1, y1] = box; const padY = (y1 - y0) * 0.12, padX = (y1 - y0) * 0.18;
  const a = b.px(x0 - padX, y0 - padY), c = b.px(x1 + padX, y1 + padY);
  const m = quad(Math.abs(c.x - a.x), Math.abs(c.y - a.y), hlMat(seed)); m.position.set((a.x + c.x) / 2, (a.y + c.y) / 2, 0.07); m.renderOrder = 9; m.rotation.z = (seed % 3 - 1) * 0.008;
  b.root.add(m); AV.hl.push({ m, t0, dur });
}
function addStamp(b, tex, cx, cy, wpx, t0, rot) {
  const w = wpx / b.cw * b.w; const m = quad(w, w * 0.52, mulTexMat(tex)); const p = b.px(cx, cy); m.position.set(p.x, p.y, 0.09); m.renderOrder = 10;
  b.root.add(m); AV.stamps.push({ m, t0, rot, board: b });
}
function updateReceipts(t) {
  for (const h of AV.hl) { const k = clamp((t - h.t0) / h.dur); h.m.visible = k > 0; h.m.material.uniforms.uProg.value = easeOut(k); }
  for (const s of AV.stamps) {
    const st = slam(t, s.t0, 0.085); s.m.visible = st.vis; if (!st.vis) continue;
    s.m.scale.setScalar(st.s); s.m.rotation.z = s.rot + (1 - st.k) * 0.12 * Math.sign(s.rot); s.m.material.uniforms.uAmt.value = 0.25 + 0.75 * st.k;
  }
}
// generic LED screens down the avenue (instanced, her videos)
function buildAveScreens(avoid) {
  const R = L.rng(77); const list = [];
  for (const [side, z0, z1, h] of AVE) {
    const zs = z0 + 2, ze = z1 - 2; let y = 7.6;
    while (y < Math.min(h - 6, 52)) {
      const rh = [5.4, 6.6, 7.8, 9.0][Math.floor(R() * 4)]; let z = zs + R() * 2;
      while (z < ze - 3) {
        let w = rh * [1.0, 1.333, 1.778, 1.778, 2.4, 0.5625, 0.75][Math.floor(R() * 7)]; w = Math.min(w, ze - z); if (w < 3) break;
        const rect = [z, z + w, y, y + rh];
        const hit = avoid.some(([s, a0, a1, b0, b1]) => s === side && rect[0] < a1 + 1 && rect[1] > a0 - 1 && rect[2] < b1 + 1 && rect[3] > b0 - 1);
        if (!hit) {
          const asp = w / rh; const atlas = asp < 0.8 ? 'V1' : 'H1'; const cell = Math.floor(R() * 16);
          const ca = M.aspectOf(atlas); let [ox, oy, sx, sy] = M.cellRect(atlas, cell, 0);
          if (asp > ca) { const f = ca / asp; oy += sy * (1 - f) / 2; sy *= f; } else { const f = asp / ca; ox += sx * (1 - f) / 2; sx *= f; }
          list.push({ atlas, rect: [ox, oy, sx, sy], pos: V3(side * 15.72, y + rh / 2, z + w / 2), yaw: -side * Math.PI / 2, w, h: rh, b: 0.7 + 0.45 * R() });
        }
        z += w + 0.9 + R() * 1.6;
      }
      y += rh + 1.1;
    }
  }
  const by = {}; list.forEach((s) => (by[s.atlas] = by[s.atlas] || []).push(s));
  const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), sc = new THREE.Vector3(), c = new THREE.Color();
  for (const a of Object.keys(by)) {
    const arr = by[a]; const geo = new THREE.PlaneGeometry(1, 1); const rect = new Float32Array(arr.length * 4); arr.forEach((s, k) => rect.set(s.rect, k * 4));
    geo.setAttribute('aRect', new THREE.InstancedBufferAttribute(rect, 4));
    const im = new THREE.InstancedMesh(geo, rawScreenMat(a, { instanced: true }), arr.length); im.frustumCulled = false;
    arr.forEach((s, k) => { q.setFromAxisAngle(UPV, s.yaw); sc.set(s.w, s.h, 1); m4.compose(s.pos, q, sc); im.setMatrixAt(k, m4); c.setScalar(s.b); im.setColorAt(k, c); });
    im.renderOrder = -2; scene.add(im); const tw = new THREE.InstancedMesh(geo, im.material, arr.length); tw.instanceMatrix = im.instanceMatrix; tw.instanceColor = im.instanceColor; tw.frustumCulled = false; tw.renderOrder = 1; mirror.add(tw);
  }
  const fg = new THREE.InstancedMesh(new THREE.BoxGeometry(1, 1, 1), FRAME_MAT(), list.length * 4); const bw = 0.26, off = V3(), fwd = V3();
  list.forEach((s, k) => { q.setFromAxisAngle(UPV, s.yaw); const right = V3(1, 0, 0).applyQuaternion(q); fwd.set(0, 0, 1).applyQuaternion(q);
    [[0, s.h / 2 + bw / 2, s.w + bw * 2, bw], [0, -s.h / 2 - bw / 2, s.w + bw * 2, bw], [-s.w / 2 - bw / 2, 0, bw, s.h], [s.w / 2 + bw / 2, 0, bw, s.h]].forEach(([dx, dy, sx, sy], j) => {
      off.copy(s.pos).addScaledVector(right, dx); off.y += dy; off.addScaledVector(fwd, -0.12); sc.set(sx, sy, 0.3); m4.compose(off, q, sc); fg.setMatrixAt(k * 4 + j, m4); }); });
  fg.renderOrder = -1; scene.add(fg);
}
function storefronts() {
  const tex = L.canvasTex(1024, 160, (g, w, h) => {
    g.fillStyle = '#050505'; g.fillRect(0, 0, w, h); const R = L.rng(5);
    for (let x = 6; x < w - 40; ) { const ww = 70 + R() * 110; const warm = R() < 0.6; const gr = g.createLinearGradient(0, 30, 0, h);
      gr.addColorStop(0, warm ? '#ffcf8a' : '#cfe2ff'); gr.addColorStop(1, warm ? '#6a3b12' : '#1c2a44'); g.fillStyle = gr; g.globalAlpha = 0.35 + R() * 0.5; g.fillRect(x, 34, ww, h - 40);
      g.globalAlpha = 1; g.fillStyle = '#050505'; for (let k = 1; k < 3; k++) g.fillRect(x + ww * k / 3 - 2, 34, 4, h - 40); x += ww + 12; }
    g.fillStyle = '#ffffff'; g.globalAlpha = 0.5; g.fillRect(0, 22, w, 4); g.globalAlpha = 1;
  }, { repeat: [1, 1] });
  tex.wrapS = THREE.RepeatWrapping;
  for (const [side, z0, z1] of AVE) {
    const len = z1 - z0 - 2; const t2 = tex.clone(); t2.needsUpdate = true; t2.repeat.set(len / 40, 1); t2.wrapS = THREE.RepeatWrapping;
    const m = quad(len, 6.2, basic({ map: t2, color: new THREE.Color(0.9, 0.9, 0.9) })); m.position.set(side * 15.75, 3.4, (z0 + z1) / 2); m.rotation.y = -side * Math.PI / 2; m.renderOrder = -2; scene.add(m);
    const tw = new THREE.Mesh(m.geometry, m.material); tw.position.copy(m.position); tw.rotation.copy(m.rotation); mirror.add(tw);
  }
}
function laneMarks() {
  const tex = L.canvasTex(256, 4096, (g, w, h) => {
    g.clearRect(0, 0, w, h); g.fillStyle = 'rgba(255,255,255,1)';
    const zOf = (z) => (640 - z) / 580 * h;
    for (const zc of [495, 385, 275, 165]) { for (let x = 8; x < w - 8; x += 22) g.fillRect(x, zOf(zc + 6), 12, zOf(zc - 6) - zOf(zc + 6)); }
    for (let z = 640; z > 60; z -= 12) { g.fillRect(w * 0.33 - 2, zOf(z), 4, 28); g.fillRect(w * 0.67 - 2, zOf(z), 4, 28); }
  }, { linear: false });
  const m = quad(32, 580, basic({ map: tex, transparent: true, opacity: 0.12, depthWrite: false })); m.rotation.x = -Math.PI / 2; m.position.set(0, 0.05, 350); m.renderOrder = 6; scene.add(m);
}
// LED zipper: a band round a building corner, the text sampled per LED with dots; the G channel holds pulsing dots
let ZIP = null;
function buildZipper() {
  const bandH = 2.6, rows = 16, pitch = bandH / rows, y = 21.3;
  const g0 = document.createElement('canvas').getContext('2d'); g0.font = `100px ${L.FONT.anton}`;
  const F = 100 * 84 / g0.measureText('H').actualBoundingBoxAscent; const font = `${F}px ${L.FONT.anton}`; g0.font = font;
  const capH = g0.measureText('H').actualBoundingBoxAscent, base = 64 + capH / 2;
  const pxPerM = 128 / bandH;
  const A = 'CLAUDE ▸ SUMMARIZING', B = 'CLAUDE ▸ SUMMARY: EVERYONE IS PANICKING. INCLUDING YOU.';
  const triW = capH * 0.72, triAdv = triW + 34;
  const measure = (s) => { const p = s.split('▸'); let x = 0; p.forEach((q, i) => { x += g0.measureText(q).width; if (i < p.length - 1) x += triAdv; }); return x; };
  const wA = measure(A), wB = measure(B);
  const lead = 40 * pxPerM, gapAB = 30 * pxPerM;
  const xA = lead, xB = lead + wA + 260 + gapAB; const total = Math.min(8192, Math.ceil(xB + wB + 50 * pxPerM));
  const drawText = (g, s, x0) => {   // draw with the ▸ as a real triangle (the font has no glyph)
    const parts = s.split('▸'); let x = x0;
    parts.forEach((p, i) => { g.fillText(p, x, base); x += g.measureText(p).width;
      if (i < parts.length - 1) { g.beginPath(); g.moveTo(x + 8, base - capH * 0.84); g.lineTo(x + 8 + triW, base - capH * 0.42); g.lineTo(x + 8, base); g.closePath(); g.fill(); x += triAdv; } });
    return x;
  };
  const tex = L.canvasTex(total, 128, (g, w, h) => {
    g.fillStyle = '#000'; g.fillRect(0, 0, w, h); g.font = font; g.textBaseline = 'alphabetic';
    g.fillStyle = '#ff0000'; const ea = drawText(g, A, xA);
    [0.34, 0.67, 1.0].forEach((v, i) => { g.fillStyle = `rgb(0,${Math.round(v * 255)},0)`; g.beginPath(); g.arc(ea + 56 + i * 72, base - capH * 0.42, capH * 0.15, 0, TAU); g.fill(); });
    g.fillStyle = '#ff0000'; drawText(g, B, xB);
  }, { linear: true });
  tex.minFilter = THREE.LinearFilter; tex.generateMipmaps = false;
  // positions (metres along the strip) of the phrases we hold on
  const m = (px) => px / pxPerM;
  ZIP = { stripLen: m(total), xA: m(xA), xB: m(xB), xSum: m(xB + measure('CLAUDE ▸ ')), xIs: m(xB + measure('CLAUDE ▸ SUMMARY: EVERYONE ')), xPan: m(xB + measure('CLAUDE ▸ SUMMARY: EVERYONE IS ')) };
  // the band path: along the avenue face (z 397 → 482), round the corner, along the cross-street face
  const R0 = 2.2, cxz = [16 + R0, 485 - R0]; const pts = [];
  const off = 0.32;
  for (let z = 397; z <= 485 - R0; z += 1.5) pts.push([16 - off, z, -1, 0]);
  for (let a = 0; a <= 1.0001; a += 1 / 12) { const ang = Math.PI + a * Math.PI / 2; pts.push([cxz[0] + Math.cos(ang) * (R0 + off), cxz[1] - Math.sin(ang) * (R0 + off), Math.cos(ang), -Math.sin(ang)]); }
  for (let x = 16 + R0 + 1.5; x <= 46; x += 1.5) pts.push([x, 485 + off, 0, 1]);
  const pos = [], uvs = [], idx = []; let s = 0; const sArr = [];
  pts.forEach((p, i) => { if (i > 0) s += Math.hypot(p[0] - pts[i - 1][0], p[1] - pts[i - 1][1]); sArr.push(s); });
  const len = s;
  pts.forEach((p, i) => { pos.push(p[0], y - bandH / 2, p[1], p[0], y + bandH / 2, p[1]); uvs.push(sArr[i] / len, 0, sArr[i] / len, 1); if (i > 0) { const a = (i - 1) * 2; idx.push(a, a + 2, a + 1, a + 1, a + 2, a + 3); } });
  const geo = new THREE.BufferGeometry(); geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); geo.setAttribute('uv', new THREE.Float32BufferAttribute(uvs, 2)); geo.setIndex(idx);
  const mat = new THREE.ShaderMaterial({ side: THREE.DoubleSide,
    uniforms: { map: { value: tex }, uCells: { value: new THREE.Vector2(len / pitch, rows) }, uRep: { value: len / ZIP.stripLen }, uScroll: { value: 0 }, uTime: U.uTime, uCol: { value: new THREE.Color(1.0, 0.42, 0.06) } },
    vertexShader: `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`,
    fragmentShader: `uniform sampler2D map; uniform vec2 uCells; uniform float uRep, uScroll, uTime; uniform vec3 uCol; varying vec2 vUv;
      void main(){ vec2 c = vUv * uCells; vec2 ci = floor(c) + 0.5;
        vec2 uv = vec2(ci.x / uCells.x * uRep + uScroll, ci.y / uCells.y);
        vec4 tx = texture2D(map, uv); float on = smoothstep(0.3, 0.6, tx.r);
        if (tx.g > 0.12) { float id = floor(tx.g * 3.0 + 0.4); on = max(on, 0.2 + 0.8 * step(fract(uTime * 2.3 - id / 3.0), 0.45)); }
        vec2 f = fract(c) - 0.5; float px = max(fwidth(c.x), 1e-3);
        float dotm = 1.0 - smoothstep(0.30, 0.30 + max(px, 0.06), length(f));
        dotm = mix(dotm, 0.55, smoothstep(0.3, 0.7, px));
        vec3 col = uCol * (0.04 + on * 2.6) * dotm;
        gl_FragColor = vec4(col, 1.0); }` });
  ZIP.mesh = new THREE.Mesh(geo, mat); ZIP.mesh.renderOrder = -2; scene.add(ZIP.mesh); ZIP.len = len; ZIP.mat = mat;
  // dark housing above and below
  const hgeo = geo.clone(); const hp = hgeo.attributes.position; for (let i = 0; i < hp.count; i++) { const yy = hp.getY(i); hp.setY(i, yy < y ? y - bandH / 2 - 0.45 : y + bandH / 2 + 0.45); }
  const hm = new THREE.Mesh(hgeo, basic({ color: 0x050506, side: THREE.DoubleSide })); hm.position.x = 0.04; hm.renderOrder = -1; scene.add(hm);
}
// scroll: where the strip's x sits at band coordinate sL (the left of frame)
function zipScroll(t) {
  const sL = ZIP.frameL; const at = (x) => x - sL;   // strip offset (m) that puts strip x at the left of frame
  const keys = [[T.bot - 0.3, at(ZIP.xA) - 34], [T.bot + 0.55, at(ZIP.xA) - 1.2], [T.panic - 0.12, at(ZIP.xA) + 0.6], [T.panic + 0.3, at(ZIP.xB) - 0.8],
    [T.panicW - 0.05, at(ZIP.xB)], [T.panicW + 0.28, at(ZIP.xSum) - 0.6], [T.roomThe - 0.05, at(ZIP.xSum) + 0.3], [T.roomThe + 0.32, at(ZIP.xIs) - 0.6], [T.minis, at(ZIP.xIs) + 0.6]];
  if (t <= keys[0][0]) return keys[0][1];
  for (let i = 0; i < keys.length - 1; i++) { const [ta, a] = keys[i], [tb, b] = keys[i + 1]; if (t <= tb) return lerp(a, b, easeIO((t - ta) / (tb - ta))); }
  return keys[keys.length - 1][1];
}
// ten little silver boxes on a ledge; redacted bars
const MINIS = { boxes: [], bars: [] };
function buildMinis(b) {
  const ledge = new THREE.Mesh(new THREE.BoxGeometry(b.w + 0.8, 0.32, 1.7), metal(0x101013, 0.35)); ledge.position.set(0, -b.h / 2 - 0.62, 0.62); b.root.add(ledge);
  const alu = new THREE.MeshStandardMaterial({ color: 0xc9ccd3, metalness: 1.0, roughness: 0.3, envMap: envTex, envMapIntensity: 1.25 });
  const geo = new RoundedBoxGeometry(0.98, 0.36, 0.98, 4, 0.13);
  const led = basic({ color: new THREE.Color(1.6, 1.6, 1.6) });
  for (let i = 0; i < 10; i++) {
    const g = new THREE.Group(); const box = new THREE.Mesh(geo, alu); g.add(box);
    const l = new THREE.Mesh(new THREE.CircleGeometry(0.022, 10), led); l.position.set(-0.36, -0.06, 0.492); g.add(l);
    const x = -b.w / 2 + 0.75 + i * ((b.w - 1.5) / 9); g.userData.home = V3(x, -b.h / 2 - 0.46 + 0.18, 0.75); g.visible = false; b.root.add(g); MINIS.boxes.push(g);
  }
  const barTex = L.canvasTex(1024, 130, (g, w, h) => { g.fillStyle = '#050505'; g.fillRect(0, 0, w, h); g.fillStyle = '#f2f2f2'; g.font = `96px ${L.FONT.anton}`; g.textAlign = 'center'; g.textBaseline = 'middle'; g.letterSpacing = '14px'; g.fillText('REDACTED', w / 2, h / 2 + 4); });
  [[-1, -0.03], [1, 0.035]].forEach(([s, rot], i) => {
    const m = quad(b.w * 0.5 - 0.2, 0.62, basic({ map: barTex, color: new THREE.Color(0.95, 0.95, 0.95) })); m.position.set(s * (b.w * 0.25 - 0.05), -b.h / 2 - 0.29, 1.27); m.rotation.z = rot; m.renderOrder = 11;
    m.visible = false; b.root.add(m); MINIS.bars.push({ m, rot, t0: i === 0 ? T.cant : T.share });
  });
}
function updateMinis(t) {
  const step = s16();
  MINIS.boxes.forEach((g, i) => {
    const tl = T.ten + i * step; const fall = 0.13; const x = t - (tl - fall); g.visible = x >= 0; if (!g.visible) return;
    const h = g.userData.home; let y = h.y, sq = 1, pop = 1;
    if (t < tl) { const u = x / fall; y = h.y + 1.45 * (1 - u * u); pop = Math.min(1, u * 2.5); }
    else { const a = t - tl; y = h.y + 0.22 * Math.abs(Math.sin(a * 22)) * Math.exp(-a * 11); sq = 1 - 0.18 * Math.exp(-a * 18) * Math.cos(a * 30); }
    g.position.set(h.x, y, h.z); g.scale.set(pop / Math.sqrt(sq), pop * sq, pop / Math.sqrt(sq));
    g.rotation.y = 0.02 * Math.sin(i * 1.7);
  });
  for (const b of MINIS.bars) { const st = slam(t, b.t0, 0.07); b.m.visible = st.vis; if (st.vis) { b.m.scale.setScalar(st.s); b.m.rotation.z = b.rot * (1 + (1 - st.k) * 3); } }
}
// Agents, Inc.: a facade that is the blocker video under amber neon; the gold plaque
const AG = {}; const HEROSW = [];   // [hero mesh, atlas stand-in] pairs
function buildAgents() {
  const cz = 362, cy = 22, vw = 20, vh = 11.25;
  const fr = borderFrame(vw, vh, 0.5, 0.6, metal(0x0a0a0c, 0.3)); fr.position.set(15.32, cy, cz); fr.rotation.y = -Math.PI / 2; scene.add(fr);
  const v = quad(vw, vh, rawScreenMat('blocker', { bright: 1.05 })); v.position.set(15.3, cy, cz); v.rotation.y = -Math.PI / 2; v.renderOrder = -2; fr.renderOrder = -1; scene.add(v);
  const tw = new THREE.Mesh(v.geometry, v.material); tw.position.copy(v.position); tw.rotation.copy(v.rotation); mirror.add(tw);
  const va = new THREE.Mesh(M.cellGeo(vw, vh, 'H1', 4), rawScreenMat('H1')); va.position.copy(v.position); va.rotation.copy(v.rotation); va.renderOrder = -2; scene.add(va);
  HEROSW.push([v, va], [tw, null]);
  const n = neon('AGENTS, INC.', { h: 5.2, color: '#ffa840', core: '#fff1dc', size: 220 }); n.position.set(15.2, cy + vh / 2 + 3.1, cz); n.rotation.y = -Math.PI / 2; scene.add(n); AG.neon = n;
  // gold plaque
  const tex = L.canvasTex(1800, 780, (g, w, h) => {
    const gr = g.createLinearGradient(0, 0, w, h); gr.addColorStop(0, '#7a5213'); gr.addColorStop(0.28, '#e9c66a'); gr.addColorStop(0.5, '#fff0b8'); gr.addColorStop(0.72, '#d6a646'); gr.addColorStop(1, '#6e4a10');
    g.fillStyle = gr; g.beginPath(); g.roundRect(0, 0, w, h, 60); g.fill();
    g.strokeStyle = '#5a3c0b'; g.lineWidth = 14; g.beginPath(); g.roundRect(34, 34, w - 68, h - 68, 40); g.stroke();
    g.strokeStyle = 'rgba(255,248,220,0.8)'; g.lineWidth = 4; g.beginPath(); g.roundRect(56, 56, w - 112, h - 112, 30); g.stroke();
    g.textAlign = 'center'; g.textBaseline = 'middle';
    const emb = (s, y, f, col) => { g.font = f; g.fillStyle = 'rgba(255,246,214,0.75)'; g.fillText(s, w / 2 + 3, y + 4); g.fillStyle = col; g.fillText(s, w / 2, y); };
    emb('★  ★  ★', 158, `64px ${L.FONT.dispBlack}`, '#3d2706');
    emb('EMPLOYEE OF THE YEAR', 330, `196px ${L.FONT.anton}`, '#2a1904');
    g.fillStyle = '#5a3c0b'; g.fillRect(w * 0.2, 455, w * 0.6, 6);
    emb('Adita · voted by 16 agents', 572, `112px ${L.FONT.serifI}`, '#2a1904');
  });
  const pg = new THREE.Group(); pg.position.set(15.0, 11.0, cz); pg.rotation.y = -Math.PI / 2; scene.add(pg);
  const back = borderFrame(11.2, 11.2 * 780 / 1800, 0.2, 0.45, new THREE.MeshStandardMaterial({ color: 0xb08a3a, metalness: 1, roughness: 0.28, envMap: envTex, envMapIntensity: 1.0 })); pg.add(back);
  const face = quad(11.2, 11.2 * 780 / 1800, rawTexMat(tex, 0.95)); face.position.z = 0.0; face.renderOrder = -2; back.renderOrder = -1; pg.add(face);
  const sheenT = L.canvasTex(256, 64, (g, w, h) => { const gr = g.createLinearGradient(0, 0, w, 0); gr.addColorStop(0, 'rgba(255,255,255,0)'); gr.addColorStop(0.5, 'rgba(255,250,230,1)'); gr.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = gr; g.fillRect(0, 0, w, h); }, { linear: true });
  const sheen = quad(2.0, 6.4, basic({ map: sheenT, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, color: new THREE.Color(0.32, 0.27, 0.16) })); sheen.rotation.z = -0.35; sheen.position.z = 0.05; pg.add(sheen);
  AG.plaque = pg; AG.sheen = sheen; AG.cz = cz;
  const ptw = new THREE.Mesh(face.geometry, face.material); mirror.add(ptw); AG.plaqueTw = ptw;
}
function updateAgents(t) {
  const f = flicker(t, T.agentsW + 0.16, 3); AG.neon.material.opacity = 0.04 + 0.96 * f * (0.92 + 0.08 * L.beatPulse(t, 6));
  const tp = T.madeW + 0.12; const st = slam(t, tp, 0.12); AG.plaque.visible = st.vis; AG.plaqueTw.visible = st.vis;
  if (st.vis) { AG.plaque.position.y = 11 + (t < tp ? 7 * (1 - st.k) : 0); AG.plaque.scale.setScalar(t < tp ? 1 : st.s); }
  AG.plaqueTw.position.set(15.0, AG.plaque.position.y, AG.cz); AG.plaqueTw.rotation.y = -Math.PI / 2;
  const sx = (t - T.madeW - 0.16) / 0.42; AG.sheen.visible = sx > 0 && sx < 1; AG.sheen.position.x = lerp(-7, 7, sx);
}
// the jumbotron (rage) and her bio as its receipt
const JB = {};
function buildJumbo(bioTex) {
  const cy = 36, z = 268.6, w = 40, h = 22.5;
  const fr = borderFrame(w, h, 1.1, 1.6, metal(0x09090b, 0.3)); fr.position.set(0, cy, z + 0.02); scene.add(fr);
  const sc = quad(w, h, rawScreenMat('rage')); sc.position.set(0, cy, z); sc.renderOrder = -2; fr.renderOrder = -1; scene.add(sc);
  const tw = new THREE.Mesh(sc.geometry, sc.material); tw.position.copy(sc.position); mirror.add(tw);
  const sa = new THREE.Mesh(M.cellGeo(w, h, 'H1', 5), rawScreenMat('H1')); sa.position.copy(sc.position); sa.renderOrder = -2; scene.add(sa);
  HEROSW.push([sc, sa], [tw, null]);
  const bar = new THREE.Mesh(new THREE.BoxGeometry(w + 2.2, 0.35, 0.4), basic({ color: new THREE.Color(1.8, 0.5, 1.0) })); bar.position.set(0, cy + h / 2 + 1.25, z); scene.add(bar);
  // bio strip
  const bw = 40, bh = bw * 80 / 1320, by = 21.3;
  const bfr = borderFrame(bw + 0.36, bh + 0.36, 0.22, 0.5, metal(0x09090b, 0.3)); bfr.position.set(0, by, z + 0.14); scene.add(bfr);
  const brm = borderFrame(bw, bh, 0.18, 0.06, basic({ color: GREENC })); brm.position.set(0, by, z + 0.17); scene.add(brm);
  const root = new THREE.Group(); root.position.set(0, by, z + 0.15); scene.add(root);
  const disp = quad(bw, bh, rawTexMat(bioTex, 0.8)); disp.renderOrder = -2; bfr.renderOrder = -1; brm.renderOrder = -1; root.add(disp);
  JB.bio = { root, disp, w: bw, h: bh, cw: 1320, ch: 80, n: V3(0, 0, 1), c: V3(0, by, z), px: (x, y) => V3((x / 1320 - 0.5) * bw, (0.5 - y / 80) * bh, 0) };
  JB.c = V3(0, cy, z);
}
// the net-worth tower: chart climbs the LED facade, ×3, and the line shoots off the top into the light
const TK = {};
function buildTicker() {
  const fx = 15.62, z0 = 182, z1 = 250, y0 = 8, y1 = 152, w = z1 - z0, h = y1 - y0;
  const Y1 = 16, Y2 = 48, Y3 = 80;
  const tex = L.canvasTex(1088, 2304, (g, cw, ch) => {
    const sx = cw / w, sy = ch / h; const Yp = (y) => ch - (y - y0) * sy, Zp = (z) => (z - z0) * sx;
    g.fillStyle = '#020a05'; g.fillRect(0, 0, cw, ch);
    g.strokeStyle = 'rgba(70,170,95,0.42)'; g.lineWidth = 1.5; for (let z = z0; z <= z1; z += 4) { g.beginPath(); g.moveTo(Zp(z), 0); g.lineTo(Zp(z), ch); g.stroke(); }
    for (let y = y0; y <= y1; y += 6) { g.beginPath(); g.moveTo(0, Yp(y)); g.lineTo(cw, Yp(y)); g.stroke(); }
    g.strokeStyle = 'rgba(140,240,126,0.95)'; g.lineWidth = 4; g.setLineDash([16, 10]);
    for (const y of [Y1, Y2, Y3]) { g.beginPath(); g.moveTo(Zp(195), Yp(y)); g.lineTo(cw, Yp(y)); g.stroke(); }
    g.setLineDash([]); g.fillStyle = '#8cf07e'; g.font = `${Math.round(3.4 * sy)}px ${L.FONT.anton}`; g.textBaseline = 'alphabetic'; g.textAlign = 'left';
    for (const [lab, y] of [['×1', Y1], ['×2', Y2]]) g.fillText(lab, Zp(199), Yp(y + 1.0));
    g.fillStyle = '#eef8ef'; g.font = `${Math.round(2.3 * sy)}px ${L.FONT.disp}`; g.fillText('NET WORTH', Zp(199), Yp(Y1 + 8.6));
    g.fillStyle = '#8cf07e'; g.font = `${Math.round(1.25 * sy)}px ${L.FONT.monoB}`; g.fillText('ADITA · LIVE', Zp(199), Yp(Y1 + 6.2));
  });
  const scr = quad(w, h, rawTexMat(tex, 1.1)); scr.position.set(fx, (y0 + y1) / 2, (z0 + z1) / 2); scr.rotation.y = -Math.PI / 2; scr.renderOrder = -2; scene.add(scr);
  const tw = new THREE.Mesh(scr.geometry, scr.material); tw.position.copy(scr.position); tw.rotation.copy(scr.rotation); mirror.add(tw);
  // chart path (world): zig-zag growth on the facade, then off the top
  const R = L.rng(77); const pts = []; const n = 24;
  for (let i = 0; i <= n; i++) { const u = i / n; const z = 210 + 20.5 * u; let y = Y1 + (Y3 - Y1) * Math.pow(u, 1.65); if (i > 0 && i < n) y += (R() - 0.5) * 4.4 * (1 - u * 0.6) + (i % 2 ? -0.7 : 0.7); pts.push(V3(fx - 0.25, y, z)); }
  pts.push(V3(fx - 0.3, 110, 230.9), V3(fx - 0.3, 152, 231.2), V3(fx - 0.6, 200, 231.5), V3(fx - 1.2, 320, 231.9), V3(fx - 2.0, 560, 232.3), V3(fx - 3.0, 980, 232.7));
  const sArr = [0]; for (let i = 1; i < pts.length; i++) sArr.push(sArr[i - 1] + pts[i].distanceTo(pts[i - 1]));
  TK.pts = pts; TK.s = sArr; TK.sTop = sArr[n]; TK.sEnd = sArr[pts.length - 1];
  const lw = 0.75; const pos = [], aS = [], idx = [];
  pts.forEach((p, i) => { const a = pts[Math.max(0, i - 1)], b = pts[Math.min(pts.length - 1, i + 1)]; const tg = b.clone().sub(a).normalize(); const nrm = new THREE.Vector3(-1, 0, 0).cross(tg).normalize().multiplyScalar(lw);
    pos.push(p.x + nrm.x, p.y + nrm.y, p.z + nrm.z, p.x - nrm.x, p.y - nrm.y, p.z - nrm.z); aS.push(sArr[i], sArr[i]); if (i > 0) { const k = (i - 1) * 2; idx.push(k, k + 2, k + 1, k + 1, k + 2, k + 3); } });
  const lg = new THREE.BufferGeometry(); lg.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); lg.setAttribute('aS', new THREE.Float32BufferAttribute(aS, 1)); lg.setIndex(idx);
  TK.lineMat = new THREE.ShaderMaterial({ side: THREE.DoubleSide, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, uniforms: { uHead: { value: 0 } },
    vertexShader: `attribute float aS; varying float vS; void main(){ vS = aS; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`,
    fragmentShader: `uniform float uHead; varying float vS; void main(){ if (vS > uHead) discard; float hot = exp(-(uHead - vS) / 14.0); gl_FragColor = vec4(vec3(0.55, 2.3, 0.6) * (1.0 + 2.5 * hot), 1.0); }` });
  scene.add(new THREE.Mesh(lg, TK.lineMat));
  // fill under the line (on the facade only)
  const fp = [], fs = [], fi = [], fa = [];
  for (let i = 0; i <= n; i++) { const p = pts[i]; fp.push(p.x + 0.05, p.y, p.z, p.x + 0.05, Y1 - 6, p.z); fs.push(sArr[i], sArr[i]); fa.push(1, 0); if (i > 0) { const k = (i - 1) * 2; fi.push(k, k + 1, k + 2, k + 1, k + 3, k + 2); } }
  const fg = new THREE.BufferGeometry(); fg.setAttribute('position', new THREE.Float32BufferAttribute(fp, 3)); fg.setAttribute('aS', new THREE.Float32BufferAttribute(fs, 1)); fg.setAttribute('aA', new THREE.Float32BufferAttribute(fa, 1)); fg.setIndex(fi);
  TK.fillMat = new THREE.ShaderMaterial({ side: THREE.DoubleSide, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, uniforms: { uHead: TK.lineMat.uniforms.uHead },
    vertexShader: `attribute float aS; attribute float aA; varying float vS; varying float vA; void main(){ vS = aS; vA = aA; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`,
    fragmentShader: `uniform float uHead; varying float vS; varying float vA; void main(){ if (vS > uHead) discard; gl_FragColor = vec4(vec3(0.07, 0.36, 0.1) * (0.25 + 0.75 * vA * vA), 1.0); }` });
  scene.add(new THREE.Mesh(fg, TK.fillMat));
  TK.head = new THREE.Sprite(new THREE.SpriteMaterial({ map: L.dotTex(), color: new THREE.Color(1.6, 2.8, 1.6), transparent: true, depthWrite: false, blending: THREE.AdditiveBlending })); TK.head.scale.setScalar(2.4); scene.add(TK.head);
  const x3 = L.textPlane('×3', { h: 14, font: L.FONT.anton, size: 240, color: '#8cf07e', glow: 30, glowColor: '#3fd14a' }); x3.position.set(fx - 0.5, Y3 - 9, 213); x3.rotation.y = -Math.PI / 2; x3.material.color.setScalar(1.4); scene.add(x3); TK.x3 = x3;
  TK.Y3 = Y3; TK.fx = fx;
}
function chartAt(s) {   // world position at arc length s
  const P = TK.pts, S = TK.s; if (s <= 0) return P[0].clone(); let i = 1; while (i < S.length - 1 && S[i] < s) i++;
  const k = clamp((s - S[i - 1]) / (S[i] - S[i - 1])); return P[i - 1].clone().lerp(P[i], k);
}
function chartHead(t) {   // climbs on "tripled", crosses ×3 on "worth", then shoots off the top
  if (t < T.tripled) return 0;
  if (t < T.worthW) { const x = (t - T.tripled) / (T.worthW - T.tripled); return TK.sTop * (0.15 * x + 0.85 * x * x); }
  const x = (t - T.worthW) / (T.end - 0.2 - T.worthW); return TK.sTop + (TK.sEnd - TK.sTop) * clamp(Math.pow(x, 2.4));
}
function updateTicker(t) {
  const s = chartHead(t); TK.lineMat.uniforms.uHead.value = s; const hp = chartAt(s);
  TK.head.visible = t >= T.tripled - 0.02; TK.head.position.copy(hp).add(V3(-0.4, 0, 0)); TK.head.scale.setScalar((2.2 + 0.8 * L.beatPulse(t, 8)) * (t > T.worthW ? 1 + 3 * sstep(T.worthW, T.end - 0.6, t) : 1));
  TK.head.material.opacity = 1 - 0.85 * sstep(T.end - 0.9, T.end - 0.1, t);
  const st = slam(t, T.worthW, 0.08); TK.x3.visible = st.vis; if (st.vis) { TK.x3.scale.setScalar(st.s); TK.x3.material.color.setScalar(1.15 + 0.8 * burstEnv(t, T.worthW, 0.02, 0.3)); }
}

// ================================================================ the camera
const _eul = new THREE.Euler();
function yp(p, l) { const dx = l[0] - p[0], dy = l[1] - p[1], dz = l[2] - p[2]; return [Math.atan2(-dx, -dz), Math.atan2(dy, Math.hypot(dx, dz))]; }
function track(keys) {   // Hermite in time (C1 through keys; hold keys stop), yaw/pitch so turns take the short way round
  const K = keys.map((k) => { const [yaw, pitch] = k.l ? yp(k.p, k.l) : [k.yaw, k.pitch]; return { t: k.t, v: [k.p[0], k.p[1], k.p[2], yaw, pitch, k.fov ?? 35, k.roll ?? 0], hold: !!k.hold }; }).sort((a, b) => a.t - b.t);
  for (let i = 1; i < K.length; i++) { let d = K[i].v[3] - K[i - 1].v[3]; while (d > Math.PI) { K[i].v[3] -= TAU; d -= TAU; } while (d < -Math.PI) { K[i].v[3] += TAU; d += TAU; } }
  const n = K.length;
  const Mt = K.map((k, i) => k.v.map((_, c) => (k.hold || i === 0 || i === n - 1) ? 0 : (K[i + 1].v[c] - K[i - 1].v[c]) / (K[i + 1].t - K[i - 1].t)));
  return (t) => {
    if (t <= K[0].t) return K[0].v.slice(); if (t >= K[n - 1].t) return K[n - 1].v.slice();
    let i = 0; while (i < n - 2 && t >= K[i + 1].t) i++;
    const a = K[i], b = K[i + 1], h = b.t - a.t, s = (t - a.t) / h, s2 = s * s, s3 = s2 * s;
    const h00 = 2 * s3 - 3 * s2 + 1, h10 = s3 - 2 * s2 + s, h01 = -2 * s3 + 3 * s2, h11 = s3 - s2;
    return a.v.map((v0, c) => h00 * v0 + h10 * h * Mt[i][c] + h01 * b.v[c] + h11 * h * Mt[i + 1][c]);
  };
}
function setCamV(c, v) { c.position.set(v[0], v[1], v[2]); c.quaternion.setFromEuler(_eul.set(v[4], v[3], v[6], 'YXZ')); c.fov = v[5]; c.updateProjectionMatrix(); c.updateMatrixWorld(); }
const dFor = (w, frac, fov = 35) => (w / frac) / (2 * Math.tan(fov * D2R / 2) * W / H);
let CAM = null, WHIPS = [];
function framing(b, frac, { dy = 0, ly = 0, yawOff = 0, fov = 35, w = null } = {}) {
  const d = dFor(w ?? b.w, frac, fov); const n = b.n.clone().applyAxisAngle(UPV, yawOff); const c = b.root ? b.root.position : b.c;
  const p = c.clone().addScaledVector(n, d); p.y += dy; return { p: [p.x, p.y, p.z], l: [c.x, c.y + ly, c.z], fov };
}
function buildCamera() {
  const K = [];
  // A+B: out of the window — log-distance pull-back, rising over the city as the sign lights
  const Wc = V3(-26 + (MATCH.col + 0.5) * (52 / 12), (MATCH.row + 0.5) * 3.4, 26);
  const d0 = 0.965 * (HER.g[1] * HER.g[3] / 2) / Math.tan(17.5 * D2R), d1 = 1180, t0 = T.ch, t1 = T.made;
  const Tg = V3(10, 270, -520);
  const pull = (t) => {
    const x = clamp((t - t0) / (t1 - t0)); const E = 1 - Math.pow(1 - x, 2.5); const lp = E; const d = d0 * Math.pow(d1 / d0, lp);
    const el = 16.5 * D2R * Math.pow(lp, 1.6), az = 3 * D2R * lp;
    const p = Wc.clone().add(V3(Math.sin(az) * Math.cos(el), Math.sin(el), Math.cos(az) * Math.cos(el)).multiplyScalar(d));
    const b = sstep(0.6, 1.0, lp); const l = Wc.clone().lerp(Tg, b);
    return { p: [p.x, p.y, p.z], l: [l.x, l.y, l.z], fov: lerp(35, 40, sstep(0.3, 1, lp)) };
  };
  K.push({ t: t0 - 0.06, ...pull(t0), hold: true });
  for (let t = t0; t < t1 - 0.01; t += 0.1) K.push({ t: Math.max(t, t0 + 0.0001), ...pull(t) });
  K.push({ t: t1, ...pull(t1) });
  // C: drift across while the towers sprout; D: the orbit (high, sign above her tower), then swoop to the top of the résumé
  K.push({ t: T.thingA + 0.2, p: [110, 600, 1100], l: [-20, 262, -420], fov: 41 });
  K.push({ t: T.another, p: [215, 604, 930], l: [-40, 300, -330], fov: 42 });
  const R1 = Math.hypot(6, 106), th1 = Math.atan2(-6, 106) / D2R;
  const orb = (t) => { const x = clamp((t - T.l3) / (T.res - T.l3)); const dk = sstep(0.55, 1.0, x);
    const th = (x < 0.55 ? lerp(22, -12, easeIO(x / 0.55)) : lerp(-12, th1, easeIO((x - 0.55) / 0.45))) * D2R;
    const R = lerp(lerp(820, 700, Math.min(1, x / 0.55)), R1, dk), h = lerp(600, resTarget(T.res) + 19, dk);
    const l = V3(lerp(-60, 0, dk), lerp(380, resTarget(T.res), dk), lerp(-380, 26, dk)); return { p: [Math.sin(th) * R, h, Math.cos(th) * R], l: [l.x, l.y, l.z], fov: lerp(42, 24, sstep(0.6, 1, x)) }; };
  for (let t = T.l3; t < T.res - 0.01; t += 0.2) K.push({ t, ...orb(t) });
  // E: locked to the unrolling edge (roll in the middle, the last page above, the counter below), from slightly above
  const resCam = (t) => { const ty = resTarget(t); return { p: [-6, ty + 19, 106], l: [0, ty, 26], fov: 24 }; };
  for (let t = T.res; t < RES.race[1] + 0.05; t += 0.04) K.push({ t, ...resCam(t) });
  K.push({ t: RES.race[1] + 0.08, ...resCam(RES.race[1] + 0.08), hold: true });
  K.push({ t: T.guru, ...resCam(T.guru), hold: true });
  // F: crane back up the résumé to the crown (from above, so the sign stays out of frame); then down into the avenue
  K.push({ t: T.ai - 0.17, p: [-10, 452, 216], l: [0, 389, 22], fov: 25, hold: true });
  K.push({ t: T.dive, p: [-9, 449, 206], l: [0, 389.5, 22], fov: 25, hold: true });
  K.push({ t: T.dive + 0.5, p: [-4, 205, 410], l: [0, 20, 330], fov: 34 });
  K.push({ t: T.v3 - 0.1, p: [1.5, 19, 584], l: [3, 22, 420], fov: 36 });
  // verse stations: each receipt gets ~1.5-2 s; whips land just after each line starts, so stamps can hit the punchline
  const B = AV.boards; const S = STN;
  const st = (ta, tb, f0, f1) => { K.push({ t: ta, ...f0, hold: true }); K.push({ t: tb, ...f1, hold: true }); };
  st(S.s1a, S.s1b, framing(B.back, 0.66), framing(B.back, 0.73, { dy: 0.1 }));
  st(S.s2a, S.s2b, framing(B.tomatoes, 0.66), framing(B.tomatoes, 0.74));
  const zc = (frac, dz, dy) => { const zz = 452 + dz; const d = dFor(32, frac); return { p: [16 - d, 21.3 + dy, zz], l: [16, 21.3 + dy * 0.5, zz], fov: 35 }; };
  st(S.s3a, S.s3b, zc(1.0, 0, 0.6), zc(1.08, -1.2, 0.2));
  st(S.s4a, S.s4b, framing(B.minis, 0.64, { dy: -0.7, ly: -0.9 }), framing(B.minis, 0.68, { dy: -0.7, ly: -0.9 }));
  st(S.s4c, S.s4d, framing(B.minis, 0.7, { dy: -1.0, ly: -1.2 }), framing(B.minis, 0.72, { dy: -1.0, ly: -1.2 }));
  st(S.s5a, S.s5b, { p: [-12.5, 25.6, 365], l: [16, 25.2, 362.5], fov: 35 }, { p: [-11.5, 25.0, 364.4], l: [16, 24.6, 362.3], fov: 35 });
  st(S.s6a, S.s6b, { p: [-1.2, 11.6, 363.2], l: [16, 11.4, 362], fov: 35 }, { p: [0.4, 11.4, 362.8], l: [16, 11.3, 362], fov: 35 });
  st(S.s7a, S.s7b, { p: [0, 31.5, 320], l: [0, 33.6, 268.6], fov: 35 }, { p: [0, 31.0, 316.5], l: [0, 33.0, 268.6], fov: 35 });
  st(S.s7c, S.s7d, { p: [0, 25.6, 310.5], l: [0, 27.6, 268.6], fov: 35 }, { p: [0, 25.3, 308.5], l: [0, 27.3, 268.6], fov: 35 });
  st(S.s8a, S.s8b, framing(B.slopcore, 0.64), framing(B.slopcore, 0.7));
  // the net-worth tower: crane up with the line, hold on ×3, then tilt up after it into the dark (stage.js opens dark)
  K.push({ t: S.s9a, p: [-13.5, 22, 211], l: [15.6, 24, 211], fov: 40, hold: true });
  for (let t = S.s9a + 0.15; t < T.worthW - 0.05; t += 0.15) { const hp = chartAt(chartHead(t)); const k = clamp((hp.y - 16) / 64); K.push({ t, p: [-13.5, Math.max(22, hp.y - 3), lerp(211, 215.5, k)], l: [15.6, Math.max(24, hp.y - 1), lerp(211, 215.5, k)], fov: lerp(40, 35, k) }); }
  K.push({ t: T.worthW + 0.06, p: [-14, TK.Y3 - 9, 216], l: [15.6, TK.Y3 - 8, 216], fov: 35, hold: true });
  K.push({ t: T.worthW + 0.6, p: [-14.3, TK.Y3 - 8.6, 216.4], l: [15.6, TK.Y3 - 7.6, 216.4], fov: 35, hold: true });
  K.push({ t: T.end - 0.5, p: [-14.6, TK.Y3, 220], l: [10, 420, 231], fov: 40 });
  K.push({ t: T.end, p: [-15, TK.Y3 + 6, 221], l: [6, 980, 232.5], fov: 44 });
  CAM = track(K);
  WHIPS = [[(S.s1b + S.s2a) / 2, 1], [(S.s2b + S.s3a) / 2, -1], [(S.s3b + S.s4a) / 2, 1], [(S.s4d + S.s5a) / 2, -1], [(S.s6b + S.s7a) / 2, 1], [(S.s7d + S.s8a) / 2, -1], [(S.s8b + S.s9a) / 2, 1]];
}
const STN = {};
function stations() {   // verse station times (arrive / leave)
  const S = STN;
  S.s1a = T.v3 + 0.15; S.s1b = T.doomed + 0.24; S.s2a = S.s1b + 0.26; S.s2b = T.bot + 0.16; S.s3a = S.s2b + 0.26; S.s3b = T.minis - 0.06;
  S.s4a = S.s3b + 0.25; S.s4b = T.reasons - 0.04; S.s4c = T.reasons + 0.21; S.s4d = T.agents + 0.12; S.s5a = S.s4d + 0.26; S.s5b = T.eoty - 0.02;
  S.s6a = T.eoty + 0.44; S.s6b = T.song - 0.02; S.s7a = T.song + 0.22; S.s7b = T.aboutW - 0.3; S.s7c = T.aboutW - 0.02; S.s7d = T.brand + 0.07;
  S.s8a = S.s7d + 0.26; S.s8b = T.worth + 0.06; S.s9a = S.s8b + 0.4;
}
function camAt(t) {
  const v = CAM(t);
  for (const ts of SHAKES) { const e = burstEnv(t, ts, 0.005, 0.09); if (e > 0.001) { const big = ts < T.v3 ? 6 : 1; v[1] += e * 0.06 * big * Math.sin(t * 90); v[4] += e * 0.004 * Math.sin(t * 77); } }
  if (t > T.v3 - 0.2) {   // handheld drift on the street + a bank through each whip
    const a = 0.05 * (t > T.worth + 0.3 ? 0.5 : 1);
    v[0] += L.noise1(t * 0.8, 1) * a * 2; v[1] += L.noise1(t * 0.7, 2) * a * 1.5; v[3] += L.noise1(t * 0.6, 3) * 0.0025; v[4] += L.noise1(t * 0.65, 4) * 0.002;
    for (const [tm, sg] of WHIPS) { const x = (t - (tm - 0.15)) / 0.3; if (x > 0 && x < 1) v[6] += sg * 0.07 * Math.sin(Math.PI * x); }
  }
  return v;
}
let SHAKES = [];
const _scr = new THREE.PerspectiveCamera(35, 16 / 9, 0.5, 20000), _P = new THREE.Vector3();
function blurVel(t, dist, max = 0.055) {
  setCamV(_scr, camAt(t)); _P.set(0, 0, -dist).applyQuaternion(_scr.quaternion).add(_scr.position);
  setCamV(_scr, camAt(t - 1 / 60)); _P.project(_scr);
  let x = -_P.x * 0.5, y = -_P.y * 0.5; const l = Math.hypot(x, y);
  if (l < 0.01) return [0, 0]; if (l > max) { x *= max / l; y *= max / l; } return [x, y];   // only the peak of a move pays for the 27-tap blur
}

// ================================================================ build
export async function build(ctx) {
  ({ W, H } = ctx); envTex = ctx.look.envTex; bloom = ctx.look.bloom; finish = ctx.look.finish; renderer = ctx.look.renderer;
  const ls = L.ls, wt = L.wt;
  T.ch = ls('Look what I can do!', 4); T.l2 = ls('Look what I can do!', 5); T.made = ls('I made a thing that made a thing', 1);
  T.thingA = wt('I made a thing that made a thing', 'thing', 1, 0); T.thingB = wt('I made a thing that made a thing', 'thing', 1, 1);
  T.another = wt('That made another two!', 'another', 1); T.two = wt('That made another two!', 'two', 1);
  T.waves = [T.thingA, T.thingB, T.another, T.two];
  T.l3 = ls('Look what I can do!', 6); T.l4 = ls('Look what I can do!', 7);
  T.res = ls('My résumé is fourteen pages'); T.resW = wt('My résumé is fourteen pages', 'résumé'); T.pagesW = wt('My résumé is fourteen pages', 'pages');
  T.guru = ls("And my title's AI guru!"); T.ai = wt("And my title's AI guru!", 'AI'); T.guruW = wt("And my title's AI guru!", 'guru');
  T.dive = T.guruW + 0.36;
  T.v3 = ls('I posted "We are so back!"'); T.postedW = wt('I posted', 'posted'); T.soW = wt('I posted', 'so'); T.backW = wt('I posted', 'back');
  T.doomed = ls('Then posted "We are doomed!"'); T.doomedW = wt('Then posted', 'doomed'); T.weAre = wt('Then posted', 'are');
  T.bot = ls('Then asked a bot to summarize'); T.panic = ls('The panic in the room'); T.panicW = wt('The panic in the room', 'panic'); T.roomThe = wt('The panic in the room', 'the', 0, 1);
  T.minis = ls('I bought ten little Mac minis'); T.ten = wt('I bought ten', 'ten'); T.macW = wt('I bought ten', 'Mac'); T.minisW = wt('I bought ten', 'minis');
  T.reasons = ls("For reasons I can't share"); T.cant = wt("For reasons I can't", "can't"); T.share = wt("For reasons I can't", 'share');
  T.agents = ls('My agents formed a company'); T.agentsW = wt('My agents formed', 'agents');
  T.eoty = ls('And made me Employee of the Year'); T.madeW = wt('And made me Employee', 'made');
  T.song = ls('I made a song about the end'); T.aboutW = wt('I made a song about the end', 'about'); T.endW = wt('I made a song about the end', 'end');
  T.job = ls('Of every job on Earth'); T.onW = wt('Of every job on Earth', 'on');
  T.brand = ls('Then gave myself a brand-new one'); T.myselfW = wt('Then gave myself', 'myself'); T.brandW = wt('Then gave myself', 'brand-new'); T.oneW = wt('Then gave myself', 'one');
  T.worth = ls('And tripled my net worth!'); T.tripled = wt('And tripled my net worth', 'tripled'); T.worthW = wt('And tripled my net worth', 'worth');
  T.end = ls('Ladies and gentlemen');
  for (const a of ['H1', 'V1']) AVG[a] = await atlasAvg(a);
  U.uMatchCell.value = MATCH.cell;

  scene = new THREE.Scene(); scene.background = new THREE.Color(0x000000); scene.fog = new THREE.FogExp2(U.uFogCol.value.getHex(), 0.0003);
  cam = new THREE.PerspectiveCamera(35, W / H, 0.5, 20000); scene.add(cam); _scr.aspect = W / H;
  scene.add(new THREE.HemisphereLight(0x8a90c0, 0x050508, 0.35));
  mirror = new THREE.Group(); mirror.scale.y = -1; scene.add(mirror);
  buildSky(); buildGround(); buildHill(); buildSign();
  const all = genCity(); buildTraffic(); buildAviation(all); buildRings(); buildSearch(); buildCrown(); buildResume(); buildSpark();
  // the avenue
  const [pBack, pTom, pMin, pSlop, pBio] = await Promise.all(['post_back.png', 'post_tomatoes.png', 'post_minis.png', 'post_slopcore.png', 'bio_end.png'].map((n) => M.image(n)));
  const B = AV.boards;
  B.back = makeBoard(cardTex(pBack.image, 672), 1320, 672, 12, V3(13.1, 17, 548), -65 * D2R, PINKC);
  B.tomatoes = makeBoard(cardTex(pTom.image, 500), 1320, 500, 12, V3(-13.1, 13.4, 520), 65 * D2R, AMBERC);
  B.minis = makeBoard(cardTex(pMin.image, 520), 1320, 520, 12, V3(-13.1, 17.2, 425), 65 * D2R, WHITEC);
  B.slopcore = makeBoard(cardTex(pSlop.image, 880), 1320, 880, 12, V3(13.1, 16.2, 298), -65 * D2R, GREENC);
  addHL(B.back, [796, 535, 1167, 596], T.postedW, 0.3, 1); addHL(B.back, [246, 617, 376, 668], T.backW, 0.2, 2);
  addStamp(B.back, stampTex('RECEIPT', 'NOV 3, 2026', '#ff4248', 1), 1108, 345, 400, T.backW + 0.06, 8 * D2R);
  addHL(B.tomatoes, [246, 280, 595, 343], T.weAre + 0.36, 0.44, 3);
  addStamp(B.tomatoes, stampTex('RECEIPT', 'OCT 30, 2026', '#ff4248', 2), 1000, 392, 400, T.doomedW, -8 * D2R);
  addHL(B.minis, [974, 117, 1193, 166], T.ten, 0.34, 4); addHL(B.minis, [249, 201, 426, 250], T.minisW, 0.2, 5); addHL(B.minis, [447, 201, 1105, 263], T.reasons, 0.46, 6);
  addStamp(B.minis, stampTex('RECEIPT', 'OCT 28, 2026', '#ff4248', 3), 1050, 405, 400, T.minisW + 0.08, 7 * D2R);
  addHL(B.slopcore, [435, 197, 998, 259], T.brandW, 0.3, 7); addHL(B.slopcore, [246, 282, 541, 332], T.oneW, 0.18, 8);
  addStamp(B.slopcore, stampTex('HIRED', 'BY MYSELF', '#1fa83a', 4, 230, 150), 1010, 372, 440, T.myselfW + 0.05, -8 * D2R);
  buildMinis(B.minis); buildAgents(); buildJumbo(cardTex(pBio.image, 80)); buildTicker();
  addHL(JB.bio, [112, 8, 940, 74], T.aboutW, 0.7, 9); addHL(JB.bio, [946, 8, 1230, 74], T.onW, 0.3, 10);
  const avoid = [[1, 541, 555, 12, 22], [1, 392, 490, 18.5, 24.2], [1, 338, 375, 6, 35], [1, 291, 305, 10.5, 22], [1, 176, 266, 0, 200],
    [-1, 513, 527, 10, 17], [-1, 418, 432, 11, 21], [-1, 250, 266, 18, 50], [1, 250, 266, 18, 50]];
  buildAveScreens(avoid); storefronts(); laneMarks(); buildZipper();
  ZIP.frameL = (452 - dFor(32, 1.0) * Math.tan(17.5 * D2R) * W / H) - 397 + 1.0;
  // sparkle bursts, camera shakes
  BURSTS.push({ t0: T.guruW, c: V3(0, HER.h + 26, 18), box: [46, 2], up: true, n: 110, speed: 55, life: 1.3, size: 6, grav: 5, spread: 0.12, col: new THREE.Color(2.4, 1.1, 1.8), seed: 11 });
  BURSTS.push({ t0: T.guruW + 0.18, c: V3(0, HER.h + 44, 10), box: [30, 2], up: true, n: 60, speed: 35, life: 1.0, size: 4.5, grav: 3, spread: 0.2, col: new THREE.Color(2.0, 2.0, 2.2), seed: 12 });
  BURSTS.push({ t0: T.madeW + 0.12, c: V3(14.2, 11, 362), rect: [11.9, 5.5], n: 90, speed: 7, life: 1.4, size: 0.8, grav: 0.5, spread: 0.3, col: new THREE.Color(2.2, 1.7, 0.7), seed: 13 });
  BURSTS.push({ t0: T.madeW + 0.75, c: V3(14.2, 11, 362), rect: [12.2, 5.8], n: 50, speed: 2.5, life: 1.6, size: 0.6, grav: 0.1, spread: 0.8, col: new THREE.Color(2.4, 2.0, 1.0), seed: 14 });
  BURSTS.push({ t0: T.worthW, c: V3(14.8, TK.Y3, 229.5), n: 60, speed: 16, life: 0.9, size: 1.0, grav: 2, spread: 0.08, col: new THREE.Color(1.0, 2.4, 1.0), seed: 15 });
  SHAKES = AV.stamps.map((s) => s.t0).concat(MINIS.bars.map((b) => b.t0), [T.madeW + 0.12, T.worthW, T.two, T.another]);
  stations(); buildCamera();
}

export function covers(t) { return t >= T.ch - 0.05 && t < T.end - 0.02; }

const DBG = (typeof location !== 'undefined' && new URLSearchParams(location.search).get('dbg')) || '';
export async function frame(t, ctx) {
  const _t0 = performance.now();
  U.uTime.value = t;
  const street = t >= T.v3 - 0.6, heroes = t >= T.dive + 0.25;
  const used = heroes ? ['H1', 'V1', 'rage', 'blocker'] : ['H1', 'V1']; M.use(...used); bumpTex(t, used);
  for (const [h, a] of HEROSW) { h.visible = heroes; if (a) a.visible = !heroes; }
  // fog + sky glow per act (the avenue is hazier)
  const fk = sstep(T.dive + 0.2, T.v3, t); U.uFogDen.value = lerp(0.00028, 0.0021, fk); U.uFogCol.value.setRGB(lerp(0.016, 0.03, fk), lerp(0.014, 0.022, fk), lerp(0.03, 0.045, fk));
  scene.fog.color.copy(U.uFogCol.value); scene.fog.density = U.uFogDen.value;
  setCamV(cam, camAt(t)); sky.position.copy(cam.position);
  const vis = DBG.includes('nocull') ? null : makeVis(cam, true);   // geometric: towers hidden behind the avenue blocks or her tower are skipped
  const mirrorTowers = t < T.res - 0.1;   // reflections of the city only in the high aerial shots (they cost a second facade pass)
  for (const s of SETS) { s.sort(cam.position, vis); s.tw.visible = mirrorTowers; }
  const ps = H / (2 * Math.tan(cam.fov * D2R / 2)); TRAFFIC.material.uniforms.uScale.value = ps; SPARK.material.uniforms.uScale.value = ps;
  const ab = AVIA.geometry.attributes.aB; AVIA.userData.ph.forEach((p, i) => ab.setX(i, (t * 0.75 + p) % 1 < 0.14 ? 1 : 0.08)); ab.needsUpdate = true;
  const ld = sstep(T.res - 0.3, T.res + 0.15, t) * (1 - sstep(T.ai - 0.1, T.ai + 0.2, t));   // her tower dims for the résumé, relights for AI GURU
  U.uHer.value.set(0.95 - 0.45 * ld, 1 - 0.32 * ld);
  updateSign(t); updateRings(t); updateSearch(t); updateCrown(t); updateResume(t);
  updateReceipts(t); ZIP.mat.uniforms.uScroll.value = zipScroll(t) / ZIP.stripLen; updateMinis(t); updateAgents(t); updateTicker(t); updateSpark(t);
  // post: bloom breathes on the beat; motion blur from the real camera motion
  const pulse = L.beatPulse(t, 7), sk = sstep(T.v3 - 0.9, T.v3, t);
  bloom.strength = 0.26 + 0.06 * pulse; bloom.threshold = lerp(0.94, 0.95, sk); bloom.radius = 0.55;
  const focus = street ? 25 : (t > T.res - 0.4 ? 110 : Math.max(150, cam.position.length() * 0.9)); const reading = t > T.res - 0.2 && t < RES.race[0] + 0.02; const bmax = street ? (t > STN.s9a + 0.1 ? 0.014 : 0.055) : (t > T.res - 0.4 ? 0.022 : 0.012);
  const fu = finish.uniforms; const [vx, vy] = reading ? [0, 0] : blurVel(t, focus, bmax); fu.uVel.value.set(vx, vy);
  // accents as exposure pulses (lights flare, blacks stay black) instead of white flashes
  let ex = 0.2 * burstEnv(t, T.two, 0.01, 0.2) + 0.12 * burstEnv(t, T.another, 0.01, 0.15) + 0.14 * burstEnv(t, T.guruW, 0.01, 0.22) + 0.14 * burstEnv(t, T.worthW, 0.01, 0.2);
  for (const s of AV.stamps) ex += 0.08 * burstEnv(t, s.t0, 0.005, 0.1);
  renderer.toneMappingExposure = 1 + ex;
  fu.uFade.value = 0.94 * sstep(T.end - 0.5, T.end - 0.03, t);   // into the dark: stage.js opens on a dark auditorium
  if (DBG) { mirror.visible = !DBG.includes('nomir'); if (DBG.includes('noblur')) fu.uVel.value.set(0, 0); if (DBG.includes('notow')) SETS.forEach((s) => { s.im.visible = false; s.tw.visible = false; }); if (DBG.includes('nopts')) { TRAFFIC.visible = TRAFFIC_M.visible = LIGHTS.visible = false; } if (DBG.includes('nosign')) { SIGN.spots.forEach((x) => x.m.visible = false); } if (DBG.includes('nosearch')) SEARCH.forEach((x) => x.m.visible = false); if (DBG.includes('noboard')) Object.values(AV.boards).forEach((bd) => { bd.root.visible = false; }); if (DBG.includes('noframe')) Object.values(AV.boards).forEach((bd) => { bd.root.children.forEach((c) => { if (c.material && c.material.isMeshStandardMaterial) c.visible = false; }); }); if (DBG.includes('noinst')) scene.traverse((o) => { if (o.isInstancedMesh && !SETS.some((st) => st.im === o || st.tw === o)) o.visible = false; }); if (DBG.includes('noground')) scene.traverse((o) => { if (o.renderOrder === 5) o.visible = false; }); if (DBG.includes('nores')) { RES.pages.forEach((x) => x.m.visible = false); RES.roll.visible = false; RES.tag.visible = false; } if (DBG.includes('noscr')) scene.traverse((o) => { if (o.isInstancedMesh && o.material && o.material.customProgramCacheKey) o.visible = false; }); if (DBG.includes('nospark')) SPARK.visible = false; if (DBG.includes('noaux')) { AVIA.visible = false; SIGN.lamps.visible = false; }  if (DBG.includes('prof')) console.log('city js', t, (performance.now() - _t0).toFixed(1)); if (DBG.includes('cam')) console.log('cam', t, cam.position.toArray().map((x) => x.toFixed(1)).join(','), camAt(t).slice(3).map((x) => x.toFixed(3)).join(','), 'vel', fu.uVel.value.x.toFixed(4), fu.uVel.value.y.toFixed(4)); }
  return { scene, camera: cam };
}
