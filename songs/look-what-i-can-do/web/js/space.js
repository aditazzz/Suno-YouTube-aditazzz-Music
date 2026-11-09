// Look What I Can Do · "Scope Creep" — space.js: FINAL CHORUS (136.54–151.74), DROP (158.3–171.74), OUTRO (171.74–181.6)
// Final chorus: one pull-back from above the keynote hall's roof → her city (every window plays one of her videos, the
// hillside sign) → the night side of the Earth (its city lights spell the hook) → space. "I made a song about myself": a
// giant screen drifts in showing THIS video (a true same-frame Droste: the frame is rendered, then every pixel inside the
// screen is mapped back into the frame through the screen's homography, level after level). "And now I'm in it too!":
// a seamless infinite zoom into it (two loops). Then a galaxy made of her videos with the hook as a pink constellation,
// a wide hero shot, five stars flaring gold and a review card. Drop: warp through a tunnel of her screens, a neon ring
// gate on every shout. Outro: the warp settles into the galaxy, the dialogue as floating terminal text, the usage limit
// powers everything down from the outside in, her real post is the last light, then her phone wakes up in the dark.
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import * as L from './lib.js';
import * as M from './media.js';
import { flicker } from './sets.js';
const { clamp, lerp, sstep, easeIO, easeOut, expOut, env, V3, ls, wt } = L;

let W = 1920, H = 1080, look, renderer, envTex;
const T = {};
const AMBER = '#ffa840', INK = '#ece6d8', GREEN = '#74e36a', PINK = '#ff5fa2', HL = '#ffe14d', RED = '#ff4248';
const RE = 6.371e6;                 // Earth radius (m)

// ---------------------------------------------------------------- small helpers
function loadImg(url) { return new Promise((res, rej) => { const im = new Image(); im.onload = () => res(im); im.onerror = () => rej(new Error('img ' + url)); im.src = url; }); }
function seqTex() { const t = new THREE.Texture(); t.colorSpace = THREE.SRGBColorSpace; t.generateMipmaps = true; t.minFilter = THREE.LinearMipmapLinearFilter; t.magFilter = THREE.LinearFilter; t.anisotropy = 8; t.userData.k = ''; return t; }
async function seqFrame(tex, name, idx) {
  idx = Math.max(1, Math.min(M.HERO[name], Math.round(idx))); const k = name + ':' + idx; if (tex.userData.k === k) return;
  const im = await loadImg(`/media/${name}/${String(idx).padStart(3, '0')}.jpg`); tex.image = im; tex.needsUpdate = true; tex.userData.k = k;
}
const gauss = (R) => (R() + R() + R() + R() - 2) * 1.22;
function mono(keys) {   // monotone cubic through [t, v] keys (no overshoot, continuous speed)
  const n = keys.length, xs = keys.map((k) => k[0]), ys = keys.map((k) => k[1]); const d = [], m = new Array(n);
  for (let i = 0; i < n - 1; i++) d.push((ys[i + 1] - ys[i]) / (xs[i + 1] - xs[i]));
  m[0] = d[0]; m[n - 1] = d[n - 2]; for (let i = 1; i < n - 1; i++) m[i] = d[i - 1] * d[i] <= 0 ? 0 : (d[i - 1] + d[i]) / 2;
  for (let i = 0; i < n - 1; i++) { if (d[i] === 0) { m[i] = m[i + 1] = 0; continue; } const a = m[i] / d[i], b = m[i + 1] / d[i], s = a * a + b * b; if (s > 9) { const k = 3 / Math.sqrt(s); m[i] = k * a * d[i]; m[i + 1] = k * b * d[i]; } }
  return (x) => {
    if (x <= xs[0]) return ys[0]; if (x >= xs[n - 1]) return ys[n - 1];
    let i = 0; while (x > xs[i + 1]) i++; const h = xs[i + 1] - xs[i], t = (x - xs[i]) / h, t2 = t * t, t3 = t2 * t;
    return (2 * t3 - 3 * t2 + 1) * ys[i] + (t3 - 2 * t2 + t) * h * m[i] + (-2 * t3 + 3 * t2) * ys[i + 1] + (t3 - t2) * h * m[i + 1];
  };
}
function makeNoise3(seed) {
  const R = L.rng(seed); const perm = Array.from({ length: 256 }, (_, i) => i);
  for (let i = 255; i > 0; i--) { const j = Math.floor(R() * (i + 1)); [perm[i], perm[j]] = [perm[j], perm[i]]; }
  const P = new Uint8Array(512); for (let i = 0; i < 512; i++) P[i] = perm[i & 255]; const V = new Float32Array(256); for (let i = 0; i < 256; i++) V[i] = R();
  const f = (t) => t * t * (3 - 2 * t), l = (a, b, k) => a + (b - a) * k;
  return (x, y, z) => {
    const xi = Math.floor(x), yi = Math.floor(y), zi = Math.floor(z), u = f(x - xi), w = f(y - yi), s = f(z - zi); const X = xi & 255, Y = yi & 255, Z = zi & 255;
    const v = (a, b, c) => V[P[P[P[(X + a) & 255] + ((Y + b) & 255)] + ((Z + c) & 255)]];
    return l(l(l(v(0, 0, 0), v(1, 0, 0), u), l(v(0, 1, 0), v(1, 1, 0), u), w), l(l(v(0, 0, 1), v(1, 0, 1), u), l(v(0, 1, 1), v(1, 1, 1), u), w), s);
  };
}
// a canvas text plane with several coloured runs (terminal lines)
function runsPlane(runs, { size = 128, font = L.FONT.monoB, h = 0.1, glow = 6 } = {}) {
  const f = `${size}px ${font}`; const g0 = document.createElement('canvas').getContext('2d'); g0.font = f;
  const ws = runs.map(([s]) => g0.measureText(s).width); const tw = ws.reduce((a, b) => a + b, 0);
  const pad = size * 0.4; const cw = Math.ceil(tw + pad * 2), ch = Math.ceil(size * 1.6);
  const tex = L.canvasTex(cw, ch, (g) => { g.font = f; g.textBaseline = 'middle'; let x = pad;
    runs.forEach(([s, col], i) => { g.shadowColor = col; g.shadowBlur = glow; g.fillStyle = col; g.fillText(s, x, ch / 2 + size * 0.04); g.shadowBlur = 0; g.fillText(s, x, ch / 2 + size * 0.04); x += ws[i]; }); });
  const geo = new THREE.PlaneGeometry(h * cw / ch, h); geo.translate(h * cw / ch / 2, 0, 0);
  const m = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({ map: tex, transparent: true, depthWrite: false, depthTest: false, toneMapped: false }));
  m.userData.w = h * cw / ch; m.renderOrder = 50; return m;
}
function wipe(m, k) {   // reveal a left-anchored text plane from the left (type-on), k in 0..1
  const g = m.geometry; const uv = g.attributes.uv, pos = g.attributes.position; const w = m.userData.w;
  if (!g.userData.base) g.userData.base = { x: [0, w, 0, w] };
  const kk = Math.max(0.0001, k); [0, 1, 2, 3].forEach((i) => { const right = i % 2 === 1; uv.setX(i, right ? kk : 0); pos.setX(i, right ? w * kk : 0); });
  uv.needsUpdate = true; pos.needsUpdate = true;
}

// ================================================================ 1. THE PULL-BACK: roof → city → Earth → space
let P, camP, CITY, GROUND_C, GROUND_R, AUD, OCULUS, HILL, SIGN, EARTH, ATMO, STARS_P, ORBIT, ORBITM = [], DS = null;
const CS = 2100, BP = 150;          // city half-size, block pitch (m)
function buildingMaterial() {
  return new THREE.ShaderMaterial({
    uniforms: { uH: { value: M.texOf('H1') }, uV: { value: M.texOf('V1') }, uA: { value: 1 } },
    vertexShader: `attribute float aSeed; varying vec3 vL; varying vec3 vN; varying vec3 vS; varying float vSeed;
      void main(){ vL = position; vN = normal; vSeed = aSeed;
        vS = vec3(length(instanceMatrix[0].xyz), length(instanceMatrix[1].xyz), length(instanceMatrix[2].xyz));
        gl_Position = projectionMatrix * modelViewMatrix * instanceMatrix * vec4(position, 1.0); }`,
    fragmentShader: `uniform sampler2D uH, uV; uniform float uA; varying vec3 vL; varying vec3 vN; varying vec3 vS; varying float vSeed;
      float h21(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
      vec4 rectH(float i){ float c = mod(i, 4.0), r = floor(i / 4.0); return vec4((c * 484.0 + 2.0) / 1936.0, 1.0 - (r * 274.0 + 272.0) / 1096.0, 480.0 / 1936.0, 270.0 / 1096.0); }
      vec4 rectV(float i){ float c = mod(i, 8.0), r = floor(i / 8.0); return vec4((c * 274.0 + 2.0) / 2192.0, 1.0 - (r * 484.0 + 482.0) / 968.0, 270.0 / 2192.0, 480.0 / 968.0); }
      vec3 vid(bool vert, float cell, vec2 cuv, float lod){ vec4 rc = vert ? rectV(cell) : rectH(cell); vec2 t = rc.xy + clamp(cuv, 0.02, 0.98) * rc.zw; return vert ? textureLod(uV, t, lod).rgb : textureLod(uH, t, lod).rgb; }
      void main(){
        vec3 n = normalize(vN);
        float fu, fw, fid;
        if (abs(n.x) > 0.5) { fu = n.x > 0.0 ? 0.5 - vL.z : vL.z + 0.5; fw = vS.z; fid = n.x > 0.0 ? 0.0 : 1.0; }
        else { fu = n.z > 0.0 ? vL.x + 0.5 : 0.5 - vL.x; fw = vS.x; fid = n.z > 0.0 ? 2.0 : 3.0; }
        float fh = vS.y, fv = vL.y;
        vec2 cr = vec2(max(1.0, floor(fw / 3.2)), max(1.0, floor(fh / 3.8)));
        vec2 g = vec2(fu, fv) * cr; vec2 fg = fwidth(g); float px = max(fg.x, fg.y);
        vec3 col;
        if (n.y > 0.5) {                                                   // roofs: dark, some carry a rooftop screen
          vec2 ru = vec2(vL.x + 0.5, 0.5 - vL.z); float r = h21(vec2(vSeed * 53.1, 9.0));
          col = vec3(0.006, 0.006, 0.008);
          if (r < 0.24) { vec2 q = (ru - 0.14) / 0.72; if (q.x > 0.0 && q.x < 1.0 && q.y > 0.0 && q.y < 1.0) { float a = vS.x / vS.z; vec2 c = q; if (a > 1.778) c.y = 0.5 + (c.y - 0.5) * 1.778 / a; else c.x = 0.5 + (c.x - 0.5) * a / 1.778; col = vid(false, floor(r * 66.0), c, 2.0) * 1.15; } }
        } else {                                                            // walls: one of her videos per face, the windows are its pixels
          float r = h21(vec2(vSeed * 91.7, fid)); bool vert = fh > fw * 1.1; float cell = floor(r * 16.0);
          vec2 gi = floor(g), gf = fract(g);
          vec2 cuv = (gi + 0.5) / cr; float av = vert ? 0.5625 : 1.7778, af = fw / fh;
          if (af > av) cuv.y = 0.5 + (cuv.y - 0.5) * av / af; else cuv.x = 0.5 + (cuv.x - 0.5) * af / av;
          float win = step(0.14, gf.x) * step(gf.x, 0.86) * step(0.18, gf.y) * step(gf.y, 0.82);
          float on = step(0.1, h21(gi + vSeed * 17.0));
          vec3 near = vid(vert, cell, cuv, 3.0) * win * on;
          vec3 far = vid(vert, cell, vec2(0.5), 6.0) * 0.42;
          col = mix(near, far, smoothstep(0.3, 0.7, px)) * 1.3 + vec3(0.006, 0.006, 0.009);
        }
        gl_FragColor = vec4(col, uA);
      }`,
    transparent: true,
  });
}
function regionGroundTex() {   // ±60 km: the city as a bright patch, highways and suburbs
  return L.canvasTex(2048, 2048, (g, w) => {
    const S = 40000, k = w / (2 * S); const X = (x) => (x + S) * k; const R = L.rng(505);
    g.fillStyle = '#000'; g.fillRect(0, 0, w, w);
    const roads = []; for (let i = 0; i < 7; i++) roads.push(i / 7 * Math.PI * 2 + R() * 0.4);
    for (const a of roads) for (let r = 3200; r < S * 1.3; r += 140) { const wob = Math.sin(r / 9000 + a * 3) * 0.06; const x = Math.cos(a + wob) * r, z = Math.sin(a + wob) * r; g.fillStyle = `rgba(255,190,120,${(0.5 + R() * 0.4).toFixed(2)})`; g.fillRect(X(x), X(z), 1.4, 1.4); }
    for (let i = 0; i < 22000; i++) { const r = 3300 + Math.pow(R(), 1.6) * 34000; const a = R() * Math.PI * 2; const near = roads.some((b) => Math.abs(Math.atan2(Math.sin(a - b), Math.cos(a - b))) < 0.12);
      if (!near && R() < 0.55) continue; g.fillStyle = `rgba(255,${170 + Math.floor(R() * 50)},${100 + Math.floor(R() * 60)},${(0.25 + R() * 0.5).toFixed(2)})`; g.fillRect(X(Math.cos(a) * r), X(Math.sin(a) * r), 1.3, 1.3); }
    for (let i = 0; i < 16; i++) { const a = roads[i % roads.length] + (R() - 0.5) * 0.1, r = 9000 + R() * 30000; const cx = Math.cos(a) * r, cz = Math.sin(a) * r;
      for (let j = 0; j < 160; j++) { const rr = Math.pow(R(), 1.5) * 1800, aa = R() * 7; g.fillStyle = `rgba(255,200,130,${(0.3 + R() * 0.6).toFixed(2)})`; g.fillRect(X(cx + Math.cos(aa) * rr), X(cz + Math.sin(aa) * rr), 1.3, 1.3); } }
    const fade = g.createRadialGradient(w / 2, w / 2, w * 0.3, w / 2, w / 2, w * 0.5); fade.addColorStop(0, 'rgba(0,0,0,1)'); fade.addColorStop(1, 'rgba(0,0,0,0)');
    g.globalCompositeOperation = 'destination-in'; g.fillStyle = fade; g.fillRect(0, 0, w, w); g.globalCompositeOperation = 'source-over';
  });
}
function oculusTex() {   // the keynote hall through its glass roof, as stage.js left it: podium on the red circle, the standing room, beams
  return L.canvasTex(1024, 1024, (g, w) => {
    const R = L.rng(66); g.fillStyle = '#020203'; g.fillRect(0, 0, w, w);
    const cx = w / 2, sy = w * 0.74;
    g.fillStyle = '#09080c'; g.fillRect(w * 0.06, w * 0.62, w * 0.88, w * 0.35);
    const refl = g.createLinearGradient(0, w * 0.97, 0, w * 0.6); refl.addColorStop(0, 'rgba(255,150,175,0.7)'); refl.addColorStop(0.35, 'rgba(255,130,165,0.2)'); refl.addColorStop(1, 'rgba(255,130,165,0)');
    g.fillStyle = refl; g.fillRect(w * 0.08, w * 0.6, w * 0.84, w * 0.37);
    g.strokeStyle = 'rgba(255,228,238,0.95)'; g.lineWidth = 8; g.beginPath(); g.ellipse(cx, w * 1.3, w * 0.46, w * 0.33, 0, Math.PI * 1.2, Math.PI * 1.8); g.stroke();
    g.fillStyle = 'rgba(255,190,120,0.95)'; g.fillRect(w * 0.06, w * 0.62, w * 0.88, 3);
    g.fillStyle = '#9a1222'; g.beginPath(); g.arc(cx, sy, w * 0.052, 0, 7); g.fill();
    const pool = g.createRadialGradient(cx, sy, 0, cx, sy, w * 0.045); pool.addColorStop(0, 'rgba(255,242,224,0.95)'); pool.addColorStop(1, 'rgba(255,235,210,0)'); g.fillStyle = pool; g.fillRect(cx - 50, sy - 50, 100, 100);
    g.fillStyle = '#121216'; g.fillRect(cx - 7, sy - 4, 14, 10); g.fillStyle = 'rgba(255,168,64,0.9)'; g.fillRect(cx - 8, sy - 22, 16, 3);
    g.globalCompositeOperation = 'lighter';
    for (let i = 0; i < 7; i++) { const x0 = w * (0.18 + i * 0.11), y0 = w * 0.62; const a = -Math.PI / 2 + (i - 3) * 0.16; const len = w * (0.32 + 0.1 * R());
      const gr = g.createLinearGradient(x0, y0, x0 + Math.cos(a) * len, y0 + Math.sin(a) * len); const col = i % 2 ? '255,95,162' : '255,168,64';
      gr.addColorStop(0, `rgba(${col},0.32)`); gr.addColorStop(1, `rgba(${col},0)`); g.fillStyle = gr; g.save(); g.translate(x0, y0); g.rotate(a); g.fillRect(0, -14, len, 28); g.restore(); }
    g.globalCompositeOperation = 'source-over';
    for (let k = 0; k < 24; k++) { const r = w * (0.17 + k * 0.024); for (let a = -0.98; a < 0.98; a += 0.011 / (0.3 + k * 0.045)) { if (R() < 0.1) continue; const x = cx + Math.sin(a) * r, y = sy - w * 0.1 - Math.cos(a) * r; if (y < w * 0.015 || y > w * 0.6) continue;
      const ph = R(); g.fillStyle = ph < 0.07 ? 'rgba(215,228,255,1)' : `rgba(${14 + R() * 14},${12 + R() * 12},${18 + R() * 14},1)`; const sz = ph < 0.07 ? 2.5 : 4; g.fillRect(x - sz / 2, y - sz / 2, sz, sz); } }
  });
}
function cityGroundMaterial() {   // her city's streets, procedural so every lamp stays a crisp point at any altitude
  return new THREE.ShaderMaterial({
    uniforms: { uTime: { value: 0 }, uA: { value: 1 } },
    vertexShader: `varying vec2 vW; void main(){ vec4 w = modelMatrix * vec4(position, 1.0); vW = w.xz; gl_Position = projectionMatrix * viewMatrix * w; }`,
    fragmentShader: `uniform float uTime, uA; varying vec2 vW;
      float h21(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
      float lamps(float d, float a, float sp, float r, float pxm){   // a row of lamps: d across the row, a along it (m)
        float re = max(r, pxm * 0.75); float da = mod(a, sp) - sp * 0.5;
        float pt = exp(-(d * d + da * da) / (re * re)) * (r * r) / (re * re);
        float ln = (1.7725 * r / sp) * (r / re) * exp(-d * d / (re * re));
        return mix(pt, ln, smoothstep(0.09 * sp, 0.25 * sp, pxm));
      }
      void main(){
        vec2 p = vW; vec2 fw = fwidth(p); float pxm = max(max(fw.x, fw.y), 0.05);
        float BP = 150.0; vec2 s = fract(p / BP - 0.5); vec2 sd = (s - step(0.5, s)) * BP; vec2 dS = abs(sd); vec2 si = floor(p / BP - 0.5 + step(0.5, s));
        float box = max(abs(p.x), abs(p.y)); float city = 1.0 - smoothstep(2150.0, 2900.0, box); float sub = 1.0 - smoothstep(2900.0, 3500.0, length(p));
        float aveX = 1.0 - step(0.5, mod(si.x, 5.0)), aveZ = 1.0 - step(0.5, mod(si.y, 5.0));
        float dens = mix(step(0.45, h21(si * 1.37 + 0.3)) * 0.7, 1.0, city);
        float L1 = lamps(abs(dS.x - 12.0), p.y, 25.0, 1.3, pxm) * (1.0 + 0.8 * aveX) + lamps(abs(dS.y - 12.0), p.x, 25.0, 1.3, pxm) * (1.0 + 0.8 * aveZ);
        vec3 col = vec3(1.0, 0.66, 0.34) * L1 * 1.7 * dens * sub;
        float cw = lamps(abs(sd.x - 5.0), p.y - uTime * 15.0, 23.0, 0.9, pxm) * aveX + lamps(abs(sd.y - 5.0), p.x - uTime * 15.0, 23.0, 0.9, pxm) * aveZ;
        float cr = lamps(abs(sd.x + 5.0), p.y + uTime * 15.0, 29.0, 0.8, pxm) * aveX + lamps(abs(sd.y + 5.0), p.x + uTime * 15.0, 29.0, 0.8, pxm) * aveZ;
        col += (vec3(1.0, 0.96, 0.88) * cw * 1.8 + vec3(1.0, 0.14, 0.12) * cr * 1.5) * city;
        vec2 bi = floor(p / BP + 0.5); float hb = h21(bi * 3.7);
        vec3 bc = hb < 0.25 ? vec3(1.0, 0.37, 0.64) : hb < 0.5 ? vec3(0.47, 0.75, 1.0) : hb < 0.75 ? vec3(1.0, 0.66, 0.25) : vec3(0.75, 0.6, 1.0);
        float farK = smoothstep(3.0, 40.0, pxm); col *= 1.0 + 6.0 * farK;
        col += bc * (0.06 + 0.22 * farK) * smoothstep(15.0, 19.0, min(dS.x, dS.y)) * city * smoothstep(1.5, 10.0, pxm);
        gl_FragColor = vec4(col * uA, 1.0);
      }`,
    transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
  });
}
// the Earth at night: procedural city lights on a generated land mask; the hook spelled out in lights north of her city
function earthLandTex() {
  const Wt = 768, Ht = 384; const c = document.createElement('canvas'); c.width = Wt; c.height = Ht; const g = c.getContext('2d'); const img = g.createImageData(Wt, Ht);
  const n1 = makeNoise3(11), n2 = makeNoise3(23);
  for (let j = 0; j < Ht; j++) { const lat = (0.5 - (j + 0.5) / Ht) * Math.PI; for (let i = 0; i < Wt; i++) { const lon = ((i + 0.5) / Wt - 0.5) * Math.PI * 2;
    const px = Math.cos(lat) * Math.sin(lon), py = Math.cos(lat) * Math.cos(lon), pz = -Math.sin(lat);
    let f = 0, a = 0.5, s = 2.1; for (let o = 0; o < 5; o++) { f += a * n1(px * s + 7, py * s + 3, pz * s + 1); a *= 0.5; s *= 2.07; }
    const dc = Math.acos(Math.max(-1, Math.min(1, py))); f += 0.16 * Math.exp(-dc * dc / 0.06);
    if (Math.abs(lon) < 0.42 && lat > 0.0 && lat < 0.26) f += 0.12;
    const land = Math.max(0, Math.min(1, (f - 0.5) / 0.05));
    let p = 0, b = 0.5, s2 = 5; for (let o = 0; o < 3; o++) { p += b * n2(px * s2, py * s2, pz * s2); b *= 0.5; s2 *= 2.3; }
    const k = (j * Wt + i) * 4; img.data[k] = land * 255; img.data[k + 1] = Math.max(0, Math.min(1, (p - 0.32) * 1.9)) * 255; img.data[k + 2] = 0; img.data[k + 3] = 255; } }
  g.putImageData(img, 0, 0); const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.NoColorSpace; t.wrapS = THREE.RepeatWrapping; return t;
}
function hookMaskTex() {
  return L.canvasTex(2048, 512, (g, w, h) => { g.fillStyle = '#000'; g.fillRect(0, 0, w, h); g.fillStyle = '#fff'; g.textAlign = 'center'; g.textBaseline = 'middle';
    let s = 300; g.font = `${s}px ${L.FONT.anton}`; while (g.measureText('LOOK WHAT I CAN DO').width > w * 0.94) { s -= 6; g.font = `${s}px ${L.FONT.anton}`; } g.fillText('LOOK WHAT I CAN DO', w / 2, h / 2 + s * 0.04); }, { linear: true });
}
const HOOKBOX = new THREE.Vector4(-21, 2.6, 21, 13.1);   // lon0, lat0, lon1, lat1 (deg)
function earthMaterial(land, hook) {
  return new THREE.ShaderMaterial({
    uniforms: { uLand: { value: land }, uHook: { value: hook }, uBox: { value: HOOKBOX }, uLights: { value: 2.2 }, uHookA: { value: 1 }, uCity: { value: 1 } },
    vertexShader: `varying vec3 vP; void main(){ vP = position; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`,
    fragmentShader: `uniform sampler2D uLand, uHook; uniform vec4 uBox; uniform float uLights, uHookA, uCity; varying vec3 vP;
      float h21(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
      vec2 h22(vec2 p){ return fract(sin(vec2(dot(p, vec2(127.1, 311.7)), dot(p, vec2(269.5, 183.3)))) * 43758.5453); }
      float dots(vec2 ll, float cell, float dens, float px, float sz){
        vec2 c = floor(ll / cell); vec2 f = ll / cell - c; vec2 o = 0.25 + 0.5 * h22(c);
        float on = step(h21(c + 7.3), dens); float d = length(f - o);
        float v = exp(-d * d / (sz * sz)) * on * (0.35 + 0.65 * h21(c + 3.1));
        float avg = dens * 3.1416 * sz * sz * 0.67;
        return mix(v, avg, smoothstep(0.25, 0.9, px / cell));
      }
      void main(){
        vec3 p = normalize(vP);
        float lon = degrees(atan(p.x, p.y)), lat = degrees(-asin(clamp(p.z, -1.0, 1.0)));
        vec2 ll = vec2(lon, lat); vec2 fl = fwidth(ll); float px = max(min(fl.x, 4.0), fl.y);
        vec4 lp = texture2D(uLand, vec2(lon / 360.0 + 0.5, lat / 180.0 + 0.5));
        float land = lp.r, dens = land * lp.g;
        float li = dots(ll, 0.9, dens * 0.8, px, 0.17) * 0.8 + dots(ll + 0.37, 0.2, dens, px, 0.15) * 1.1 + dots(ll + 0.11, 0.045, dens * 1.2, px, 0.16) * 1.4 + dots(ll + 0.023, 0.012, dens * 1.2, px, 0.18) * 1.2;
        li += land * smoothstep(0.55, 0.95, lp.g) * 0.16;
        vec2 hb = (ll - uBox.xy) / (uBox.zw - uBox.xy); float hk = 0.0;
        if (hb.x > 0.0 && hb.x < 1.0 && hb.y > 0.0 && hb.y < 1.0) hk = texture2D(uHook, hb).r * uHookA;
        float hl = dots(ll + 0.05, 0.4, hk * 1.2, px, 0.27) * 2.4 + dots(ll + 0.21, 0.13, hk * 1.1, px, 0.16) * 1.4 + hk * 0.05;
        float dc = length(ll);
        vec3 city = vec3(1.0, 0.6, 0.85) * (exp(-dc * dc / 0.004) * 2.2 + exp(-dc * dc / 0.08) * 0.45);
        dens = clamp(dens + land * 0.55 * exp(-dc * dc / 18.0), 0.0, 1.0);
        vec3 base = mix(vec3(0.0006, 0.0009, 0.0026), vec3(0.006, 0.0065, 0.0095), land);
        vec3 col = base + vec3(1.0, 0.7, 0.36) * li * uLights + vec3(1.0, 0.62, 0.78) * hl + city * uCity;
        gl_FragColor = vec4(col, 1.0);
      }`,
  });
}
function atmoMaterial() {
  return new THREE.ShaderMaterial({
    uniforms: { uA: { value: 1 } },
    vertexShader: `varying vec3 vN; varying vec3 vV; varying vec3 vW; void main(){ vec4 mv = modelViewMatrix * vec4(position, 1.0); vN = normalize(normalMatrix * normal); vV = normalize(-mv.xyz); vW = normalize(position); gl_Position = projectionMatrix * mv; }`,
    fragmentShader: `uniform float uA; varying vec3 vN; varying vec3 vV; varying vec3 vW;
      void main(){ float f = 1.0 - abs(dot(normalize(vN), normalize(vV))); float rim = pow(f, 4.0);
        float sun = smoothstep(0.2, 0.9, dot(vW, normalize(vec3(-0.85, 0.2, -0.5))));
        vec3 c = vec3(0.12, 0.32, 0.9) * rim * 0.9 + vec3(1.0, 0.55, 0.25) * pow(f, 7.0) * sun * 2.2;
        gl_FragColor = vec4(c * uA, 1.0); }`,
    transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
  });
}
function starPoints(n, seed, size, radius = 1) {
  const R = L.rng(seed); const pos = new Float32Array(n * 3), col = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) { const z = R() * 2 - 1, a = R() * Math.PI * 2, r = Math.sqrt(1 - z * z); pos.set([Math.cos(a) * r * radius, z * radius, Math.sin(a) * r * radius], i * 3);
    const b = 0.25 + Math.pow(R(), 6) * 1.6; const warm = R(); col.set([b * (0.85 + 0.15 * warm), b * 0.9, b * (1.05 - 0.2 * warm)], i * 3); }
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(pos, 3)); g.setAttribute('color', new THREE.BufferAttribute(col, 3));
  const p = new THREE.Points(g, new THREE.PointsMaterial({ size, sizeAttenuation: false, vertexColors: true, map: L.dotTex(), transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false }));
  p.frustumCulled = false; return p;
}
function buildPull() {
  P = new THREE.Scene(); P.background = new THREE.Color(0x000000);
  camP = new THREE.PerspectiveCamera(45, W / H, 1, 1e5); P.add(camP);
  // ground: her city's streets over the region; both lie flat, the Earth sphere sits just under them
  GROUND_R = new THREE.Mesh(new THREE.PlaneGeometry(80000, 80000), new THREE.MeshBasicMaterial({ map: regionGroundTex(), transparent: true, depthWrite: false, toneMapped: false, blending: THREE.AdditiveBlending }));
  GROUND_R.rotation.x = -Math.PI / 2; GROUND_R.renderOrder = -2; GROUND_R.material.color.setScalar(1.2); P.add(GROUND_R);
  GROUND_C = new THREE.Mesh(new THREE.PlaneGeometry(7200, 7200), cityGroundMaterial()); GROUND_C.rotation.x = -Math.PI / 2; GROUND_C.renderOrder = -1; P.add(GROUND_C);
  // buildings (every face plays one of her videos through its windows)
  const R = L.rng(808); const mats = []; const seeds = [];
  for (let bx = -14; bx <= 14; bx++) for (let bz = -14; bz <= 14; bz++) {
    if (Math.abs(bx) <= 0 && Math.abs(bz) <= 0) continue;
    const cx = bx * BP, cz = bz * BP; const d = Math.hypot(cx, cz);
    const tall = 14 + 230 * Math.exp(-Math.pow(d / 950, 2));
    const lots = R() < 0.28 ? [[0, 0, 1]] : [[-30, -30, 0.5], [30, -30, 0.5], [-30, 30, 0.5], [30, 30, 0.5]];
    for (const [ox, oz, sz] of lots) {
      if (R() < 0.08) continue;
      const fw = (sz === 1 ? 70 + R() * 34 : 34 + R() * 18), fd = (sz === 1 ? 70 + R() * 34 : 34 + R() * 18);
      const h = Math.max(10, tall * (0.25 + Math.pow(R(), 1.6) * (sz === 1 ? 1.15 : 0.8)) + R() * 18);
      mats.push(new THREE.Matrix4().compose(V3(cx + ox, 0, cz + oz), new THREE.Quaternion(), V3(fw, h, fd))); seeds.push(R());
    }
  }
  const bg = new THREE.BoxGeometry(1, 1, 1); bg.translate(0, 0.5, 0); bg.setAttribute('aSeed', new THREE.InstancedBufferAttribute(new Float32Array(seeds), 1));
  CITY = new THREE.InstancedMesh(bg, buildingMaterial(), mats.length); mats.forEach((m, i) => CITY.setMatrixAt(i, m)); CITY.frustumCulled = false; P.add(CITY);
  // the keynote hall: a dark box, an LED ribbon round its crown, the glass oculus over stage + room
  AUD = new THREE.Group();
  const box = new THREE.Mesh(new THREE.BoxGeometry(124, 24, 100), new THREE.MeshBasicMaterial({ color: 0x060608 })); box.position.y = 12; AUD.add(box);
  for (const y of [21.5, 23.2]) { const rib = new THREE.Mesh(new THREE.BoxGeometry(124.6, 0.5, 100.6), new THREE.MeshBasicMaterial({ color: new THREE.Color(1.6, 0.55, 1.0), toneMapped: false })); rib.position.y = y; AUD.add(rib); }
  OCULUS = new THREE.Mesh(new THREE.PlaneGeometry(86, 74), new THREE.MeshBasicMaterial({ map: oculusTex(), toneMapped: false })); OCULUS.rotation.x = -Math.PI / 2; OCULUS.position.set(0, 24.06, 4); OCULUS.material.color.setScalar(1.0); AUD.add(OCULUS);
  const rim = new THREE.Mesh(new THREE.RingGeometry(0.5, 0.52, 4, 1), new THREE.MeshBasicMaterial({ color: 0x15151a })); rim.visible = false; AUD.add(rim);
  P.add(AUD);
  // the hillside sign north of the city (the hook, as in chorus 2)
  HILL = new THREE.Mesh(new THREE.SphereGeometry(1, 48, 24), new THREE.MeshBasicMaterial({ color: 0x030304 })); HILL.scale.set(2300, 420, 760); HILL.position.set(0, -60, -3050); P.add(HILL);
  SIGN = L.textPlane('LOOK WHAT I CAN DO', { h: 120, font: L.FONT.anton, size: 200, color: '#ffffff', glow: 26, glowColor: '#ffd9ea', pad: 0.1 });
  SIGN.material.color.setScalar(1.6); SIGN.position.set(0, 150, -2560); SIGN.rotation.x = -0.42; P.add(SIGN);
  // the Earth (night side), its atmosphere, stars
  EARTH = new THREE.Mesh(new THREE.SphereGeometry(RE, 220, 110), earthMaterial(earthLandTex(), hookMaskTex())); EARTH.position.set(0, -RE - 60, 0); EARTH.renderOrder = -3; P.add(EARTH);
  ATMO = new THREE.Mesh(new THREE.SphereGeometry(RE * 1.016, 160, 80), atmoMaterial()); ATMO.position.copy(EARTH.position); P.add(ATMO);
  STARS_P = new THREE.Group(); STARS_P.add(starPoints(3600, 3, 1.6), starPoints(500, 4, 2.8)); P.add(STARS_P);
  ORBIT = new THREE.Group(); ORBIT.position.copy(EARTH.position); ORBIT.quaternion.setFromUnitVectors(V3(0, 1, 0), V3(0.25, 1, -0.55).normalize());
  { const R = L.rng(77); const items = { H1: [], V1: [] };
    for (let i = 0; i < 1800; i++) { const a = R() * Math.PI * 2; const r = RE * (1.55 + 0.8 * Math.pow(R(), 0.8)); const y = gauss(R) * RE * 0.02;
      items[i % 2 ? 'V1' : 'H1'].push({ p: V3(Math.cos(a) * r, y, Math.sin(a) * r), cell: Math.floor(R() * 16), s: RE * (0.03 + R() * 0.035), b: 0.8 + R() * 0.5, w: 0, j: 0 }); }
    ORBITM = ['H1', 'V1'].map((a) => { const m = screenField(a, items[a]); ORBIT.add(m); return m; }); }
  P.add(ORBIT);
  // the giant screen for 'I made a song about myself' (its display is black here; the Droste pass fills it)
  DS = new THREE.Group();
  const bez = new THREE.Mesh(new RoundedBoxGeometry(1.06, 1.06 * 9 / 16 + 0.06, 0.03, 4, 0.012), new THREE.MeshStandardMaterial({ color: 0x0c0c0f, metalness: 0.85, roughness: 0.3, envMap: envTex, envMapIntensity: 0.9 }));
  bez.position.z = -0.018; DS.add(bez);
  const disp = new THREE.Mesh(new THREE.PlaneGeometry(1, 9 / 16), new THREE.MeshBasicMaterial({ color: 0x000000 })); disp.position.z = 0.0005; DS.add(disp); DS.userData.disp = disp;
  const edge = new THREE.Mesh(new THREE.PlaneGeometry(1.02, 9 / 16 + 0.02), new THREE.MeshBasicMaterial({ color: new THREE.Color(0.9, 0.4, 0.65), transparent: true, opacity: 0.0, blending: THREE.AdditiveBlending, depthWrite: false, toneMapped: false }));
  edge.position.z = -0.0005; DS.add(edge);
  DS.visible = false; camP.add(DS);
  P.add(new THREE.HemisphereLight(0x8090b0, 0x050506, 0.6));
}
// camera through the scales
let LOGH, ELEV;
function pullCam(t) {
  const lh = LOGH(t), d = Math.pow(10, lh), el = THREE.MathUtils.degToRad(ELEV(t));
  const k0 = easeIO(clamp((t - T.fin) / (T.d1f - T.fin)));
  const tgt0 = V3(0, 24, 19).lerp(V3(0, 0, 0), k0);
  const pos = tgt0.clone().add(V3(0, Math.sin(el) * d, Math.cos(el) * d));
  const w = 0.3 * easeIO(clamp((lh - 6.3) / 0.8));     // keep her city in frame until the planet is whole
  const look_ = tgt0.clone().lerp(V3(0, -RE - 60, 0), w);
  return { pos, look: look_, d, lh };
}
function setPullCam(c, t, fov = 45) {
  camP.position.copy(c.pos); camP.up.set(0, 1, 0); camP.lookAt(c.look); camP.fov = fov;
  const dEarth = c.pos.distanceTo(EARTH.position);
  camP.near = Math.max(0.5, c.d * 0.008); camP.far = Math.max(c.d * 120, 8e3) + (c.lh > 3.6 ? dEarth + RE : 0); camP.updateProjectionMatrix(); camP.updateMatrixWorld(true);
}
function framePull(t, forDroste = false) {
  const u = look.finish.uniforms, bloom = look.bloom;
  let c = pullCam(t);
  if (forDroste) {   // in space: turn so the Earth sits low-left (peeking from behind the screen) and the screen has the sky
    const k = easeIO(clamp((t - T.song) / 1.6));
    const f0 = EARTH.position.clone().sub(c.pos).normalize(); const r0 = f0.clone().cross(V3(0, 1, 0)).normalize(); const u0 = r0.clone().cross(f0);
    const tv = Math.tan(THREE.MathUtils.degToRad(22.5)), th = tv * W / H;
    const f = f0.clone().addScaledVector(r0, 0.62 * th).addScaledVector(u0, 0.58 * tv).normalize();
    const look2 = c.pos.clone().addScaledVector(f, c.pos.distanceTo(EARTH.position));
    c.look.lerp(look2, k);
  }
  setPullCam(c, t); if (!forDroste) DS.visible = false;
  const lh = c.lh;
  // what's visible at this scale
  const cityA = 1 - sstep(3.8, 4.8, lh);
  CITY.visible = cityA > 0.003; CITY.material.uniforms.uA.value = cityA; AUD.visible = lh < 4.0; HILL.visible = SIGN.visible = lh < 4.4;
  const gca = 1 - sstep(5.3, 5.9, lh); GROUND_C.material.uniforms.uA.value = gca; GROUND_C.material.uniforms.uTime.value = t; GROUND_C.visible = gca > 0.003;
  GROUND_R.material.opacity = 1 - sstep(5.2, 5.6, lh); GROUND_R.visible = GROUND_R.material.opacity > 0.003;
  EARTH.visible = lh > 3.3; ATMO.visible = lh > 4.6; ATMO.material.uniforms.uA.value = sstep(4.6, 5.6, lh);
  EARTH.material.uniforms.uHookA.value = sstep(5.6, 6.3, lh) * (forDroste ? 1 - sstep(T.song + 0.6, T.song + 1.6, t) * 0.35 : 1);
  EARTH.material.uniforms.uCity.value = sstep(4.7, 5.7, lh);   // overlaps the city/ground fades: no empty beat on the way up
  SIGN.material.opacity = flicker(t, T.fin + 0.25, 4);
  STARS_P.position.copy(camP.position); STARS_P.scale.setScalar(camP.far * 0.8); STARS_P.children.forEach((s) => { s.material.opacity = 0.35 + 0.65 * sstep(3.8, 5.5, lh); });
  const oa = sstep(5.7, 6.5, lh); ORBIT.visible = oa > 0.01;
  if (ORBIT.visible) { ORBIT.rotation.set(0, 0, 0); ORBIT.quaternion.setFromUnitVectors(V3(0, 1, 0), V3(0.25, 1, -0.55).normalize()); ORBIT.rotateY(0.02 * (t - T.fin));
    const qi = ORBIT.quaternion.clone().invert(); const r = V3(1, 0, 0).applyQuaternion(camP.quaternion).applyQuaternion(qi), up = V3(0, 1, 0).applyQuaternion(camP.quaternion).applyQuaternion(qi);
    ORBITM.forEach((m) => { const U = m.material.uniforms; U.uCamR.value.copy(r); U.uCamU.value.copy(up); U.uBright.value = 1.1 * oa; U.uTime.value = t; }); }
  if (CITY.visible || ORBIT.visible) M.use('H1', 'V1');
  // post: a punch on each 'do!', the pull speeds up through the middle
  const pulse = L.beatPulse(t, 7);
  bloom.threshold = 0.9; bloom.strength = 0.42 + 0.1 * pulse; bloom.radius = 0.6;
  u.uVig.value = 0.36; u.uGrain.value = 0.045;
  if (!forDroste) {
    u.uFlash.value = 0.03 * env(t, T.d1f, 0.008, 0.04) + 0.03 * env(t, T.fin2, 0.008, 0.04);
    const sp = (LOGH(t + 0.02) - LOGH(t - 0.02)) / 0.04;   // decades per second → a little vertical smear
    u.uVel.value.set(0, -Math.min(0.012, sp * 0.0035));
  }
  return { scene: P, camera: camP };
}

// ================================================================ 2. THE DROSTE: this very video on a screen in space, then the dive
let RT = null, Q = null, qcam = null, QM = null;
function buildQuad() {
  RT = new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType });
  QM = new THREE.ShaderMaterial({
    uniforms: { tSrc: { value: RT.texture }, uMode: { value: 0 }, uHinv: { value: new THREE.Matrix3() }, uZ: { value: 0 }, uF: { value: 0.56 }, uBlur: { value: 0 }, uC: { value: new THREE.Vector2(0.5, 0.5) },
      uGain: { value: 0.9 }, uAspect: { value: W / H }, uLevels: { value: 1 } },
    vertexShader: `varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }`,
    fragmentShader: `uniform sampler2D tSrc; uniform int uMode; uniform mat3 uHinv; uniform float uZ, uF, uBlur, uGain, uAspect, uLevels; uniform vec2 uC; varying vec2 vUv;
      vec3 droste(vec2 p){
        float k = 1.0;
        for (int i = 0; i < 14; i++) {
          vec3 s = uHinv * vec3(p, 1.0); if (s.z <= 0.0) break; vec2 q = s.xy / s.z;
          if (q.x < 0.0 || q.x > 1.0 || q.y < 0.0 || q.y > 1.0) break;
          vec2 d = (q - 0.5) * vec2(uAspect, 1.0) / uAspect * 1.9; k *= uGain * (1.0 - 0.3 * pow(clamp(length(d), 0.0, 1.4), 2.6));
          p = q;
        }
        return texture2D(tSrc, p).rgb * k;
      }
      void main(){
        if (uMode == 1) { float Z = pow(1.0 / uF, uZ); vec2 p = uC + (vUv - uC) / Z; gl_FragColor = vec4(droste(p), 1.0); return; }
        if (uMode == 2) { vec3 c = vec3(0.0); vec2 d = vUv - uC; for (int i = 0; i < 10; i++) { float f = 1.0 - uBlur * float(i) / 9.0; c += texture2D(tSrc, uC + d * f).rgb; } gl_FragColor = vec4(c * 0.1, 1.0); return; }
        gl_FragColor = vec4(texture2D(tSrc, vUv).rgb, 1.0);
      }`,
    depthTest: false, depthWrite: false,
  });
  Q = new THREE.Scene(); const m = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), QM); m.frustumCulled = false; Q.add(m); qcam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
}
function homography(q) {   // unit square → quad q (frame UV): [[x0,y0] (0,0), [x1,y1] (1,0), [x2,y2] (1,1), [x3,y3] (0,1)]
  const [x0, y0] = q[0], [x1, y1] = q[1], [x2, y2] = q[2], [x3, y3] = q[3];
  const dx1 = x1 - x2, dx2 = x3 - x2, dx3 = x0 - x1 + x2 - x3, dy1 = y1 - y2, dy2 = y3 - y2, dy3 = y0 - y1 + y2 - y3;
  let g = 0, h = 0; const den = dx1 * dy2 - dx2 * dy1;
  if (Math.abs(dx3) > 1e-12 || Math.abs(dy3) > 1e-12) { g = (dx3 * dy2 - dx2 * dy3) / den; h = (dx1 * dy3 - dx3 * dy1) / den; }
  return new THREE.Matrix3().set(x1 - x0 + g * x1, x3 - x0 + h * x3, x0, y1 - y0 + g * y1, y3 - y0 + h * y3, y0, g, h, 1);
}
const DROSTE_F = 0.5, DROSTE_D = 3.0e6;
function placeDroste(t) {   // the screen's pose in camera space: drifts in from the right, settles centred and square by the dive
  const fov = THREE.MathUtils.degToRad(camP.fov); const wDisp = 2 * DROSTE_D * Math.tan(fov / 2) * camP.aspect * DROSTE_F;
  const k = easeOut(clamp((t - T.song) / (T.inIt - 0.08 - T.song)));
  const k2 = easeIO(clamp((t - T.song) / (T.inIt - 0.08 - T.song)));
  const x = lerp(1.25, 0, k) * wDisp, y = lerp(0.2, 0, k2) * wDisp, z = -DROSTE_D * lerp(1.7, 1, k);
  DS.position.set(x, y, z); DS.rotation.set(lerp(0.12, 0, k2), lerp(-0.75, 0, k), lerp(0.1, 0, k2)); DS.scale.setScalar(wDisp);
  DS.visible = true; DS.updateMatrixWorld(true);
}
const _v = new THREE.Vector3();
function drosteHinv() {
  const corners = [[-0.5, -9 / 32], [0.5, -9 / 32], [0.5, 9 / 32], [-0.5, 9 / 32]];
  const disp = DS.userData.disp; disp.updateMatrixWorld(true);
  const q = corners.map(([x, y]) => { _v.set(x, y, 0).applyMatrix4(disp.matrixWorld).project(camP); return [(_v.x + 1) / 2, (_v.y + 1) / 2]; });
  return homography(q).invert();
}
async function frameDroste(t) {
  const u = look.finish.uniforms, bloom = look.bloom;
  const res = framePull(t, true);
  if (t >= T.inIt - 0.08) { // the dive: freeze the screen square-on, zoom through the self-similar frame
    const keep = T.inIt - 0.08; placeDroste(keep);
  } else placeDroste(t);
  await M.update(t);          // the orbiting screens must be on this frame before the offscreen render
  renderer.setRenderTarget(RT); renderer.render(P, camP); renderer.setRenderTarget(null);
  QM.uniforms.uMode.value = 1; QM.uniforms.uHinv.value.copy(drosteHinv()); QM.uniforms.uF.value = DROSTE_F; QM.uniforms.uGain.value = 0.9;
  const dz = clamp((t - T.inIt) / (T.fin3 - T.inIt)); QM.uniforms.uZ.value = t < T.inIt ? 0 : 2.0 * (0.35 * dz + 0.65 * dz * dz * dz);
  // the screen's own glow and a soft flash as it arrives; motion blur grows through the dive
  DS.children[2].material.opacity = 0.35 * sstep(T.song, T.song + 0.4, t);
  bloom.threshold = 0.88; bloom.strength = 0.45; bloom.radius = 0.6;
  u.uFlash.value = 0.2 * sstep(T.fin3 - 0.07, T.fin3 - 0.005, t); u.uFlashCol.value.setRGB(1.0, 0.75, 0.88);
  u.uCA.value = 0.0016 + 0.006 * dz * dz;
  return { scene: Q, camera: qcam };
}

// ================================================================ 3. THE GALAXY of her videos (+ the drop tunnel, the outro)
let G, camG, GAL, GSCREENS = [], GGLOW, GCORE, GSTARS, BGSTARS, CONST, FIVE = [], CARD, CARDT, TUN = [], STREAKS, GATES = [], TERM = [], TPANEL, LAST, LASTP, STAMP;
const SCREEN_VS = `attribute vec3 aPos; attribute vec4 aRect; attribute vec2 aSz; attribute vec3 aMisc;
  uniform vec3 uCamR, uCamU; uniform float uTime, uWave0, uWaveDur, uBright;
  varying vec2 vUv; varying float vB; varying float vLine;
  void main(){
    vUv = aRect.xy + uv * aRect.zw;
    float off = uWave0 + aMisc.y * uWaveDur + aMisc.z * 0.12; float x = uTime - off;
    float sx = 1.0, sy = 1.0, line = 0.0;
    if (x > 0.0) { line = clamp(x / 0.06, 0.0, 1.0); sy = mix(1.0, 0.02, line); sx = 1.0 - clamp((x - 0.06) / 0.07, 0.0, 1.0); }
    vB = aMisc.x * uBright * (1.0 + 2.6 * line * step(x, 0.13)); vLine = line;
    vec3 p = aPos + uCamR * position.x * aSz.x * sx + uCamU * position.y * aSz.y * sy;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(p, 1.0);
  }`;
const SCREEN_FS = `uniform sampler2D uMap; varying vec2 vUv; varying float vB; varying float vLine;
  void main(){ vec3 c = texture2D(uMap, vUv).rgb; c = mix(c, vec3(0.9, 0.95, 1.0) * (0.35 + dot(c, vec3(0.3))), vLine * 0.9); gl_FragColor = vec4(c * vB, 1.0); }`;
function screenField(atlas, items) {   // items: [{p:V3, cell, s, b, w (wave 0..1), j}]
  const base = new THREE.PlaneGeometry(1, 1); const g = new THREE.InstancedBufferGeometry();
  g.index = base.index; g.setAttribute('position', base.attributes.position); g.setAttribute('uv', base.attributes.uv); g.instanceCount = items.length;
  const n = items.length, aPos = new Float32Array(n * 3), aRect = new Float32Array(n * 4), aSz = new Float32Array(n * 2), aMisc = new Float32Array(n * 3); const vert = atlas[0] === 'V';
  items.forEach((it, i) => { aPos.set([it.p.x, it.p.y, it.p.z], i * 3); aRect.set(M.cellRect(atlas, it.cell), i * 4); aSz.set(vert ? [it.s * 0.5625, it.s] : [it.s, it.s * 0.5625], i * 2); aMisc.set([it.b, it.w, it.j], i * 3); });
  g.setAttribute('aPos', new THREE.InstancedBufferAttribute(aPos, 3)); g.setAttribute('aRect', new THREE.InstancedBufferAttribute(aRect, 4));
  g.setAttribute('aSz', new THREE.InstancedBufferAttribute(aSz, 2)); g.setAttribute('aMisc', new THREE.InstancedBufferAttribute(aMisc, 3));
  const mat = new THREE.ShaderMaterial({ uniforms: { uMap: { value: M.texOf(atlas) }, uCamR: { value: V3(1, 0, 0) }, uCamU: { value: V3(0, 1, 0) }, uTime: { value: 0 }, uWave0: { value: 1e9 }, uWaveDur: { value: 1 }, uBright: { value: 1 } },
    vertexShader: SCREEN_VS, fragmentShader: SCREEN_FS, side: THREE.DoubleSide });
  const m = new THREE.Mesh(g, mat); m.frustumCulled = false; m.userData.atlas = atlas; return m;
}
const GR = 110;
function galaxyItems(seed, n) {   // two logarithmic arms + a bulge + some between the arms; brighter toward the core
  const R = L.rng(seed); const out = []; const pitch = 0.3;
  for (let i = 0; i < n; i++) {
    let r, th, y; const kind = R();
    if (kind < 0.12) { r = Math.abs(gauss(R)) * 13 + 2; th = R() * Math.PI * 2; y = gauss(R) * 5 * Math.exp(-r / 18); }
    else { r = 7 + 103 * Math.pow(R(), 0.8); const arm = kind < 0.8 ? (i % 2) * Math.PI : R() * Math.PI * 2; th = arm + Math.log(r / 7) / Math.tan(pitch) + gauss(R) * (0.16 + 0.22 * r / GR); y = gauss(R) * (0.7 + 2.6 * Math.exp(-r / 22)); }
    const p = V3(Math.cos(th) * r, y, Math.sin(th) * r);
    const s = (0.75 + R() * 0.9) * (R() < 0.04 ? 2.4 : 1);
    out.push({ p, cell: Math.floor(R() * 16), s, b: (0.7 + 0.5 * R()) * (0.75 + 0.6 * Math.exp(-r / 40)), w: clamp(1 - r / (GR + 8)), j: R(), r });
  }
  return out;
}
function glowTex() {   // the soft light of the arms under the screens
  return L.canvasTex(1024, 1024, (g, w) => {
    const R = L.rng(99); g.fillStyle = '#000'; g.fillRect(0, 0, w, w); g.globalCompositeOperation = 'lighter'; const k = w / (2 * 135);
    const cols = ['255,95,162', '130,170,255', '255,190,140', '200,140,255'];
    for (let i = 0; i < 9000; i++) { const r = 5 + 105 * Math.pow(R(), 0.85); const th = (i % 2) * Math.PI + Math.log(r / 7) / Math.tan(0.3) + gauss(R) * (0.18 + 0.2 * r / GR);
      const x = w / 2 + Math.cos(th) * r * k, y = w / 2 + Math.sin(th) * r * k; const rad = (3 + R() * 9) * (1 + r / 80);
      const gr = g.createRadialGradient(x, y, 0, x, y, rad); gr.addColorStop(0, `rgba(${cols[Math.floor(R() * cols.length)]},${(0.05 + R() * 0.05).toFixed(3)})`); gr.addColorStop(1, 'rgba(0,0,0,0)'); g.fillStyle = gr; g.fillRect(x - rad, y - rad, rad * 2, rad * 2); }
    const core = g.createRadialGradient(w / 2, w / 2, 0, w / 2, w / 2, 26 * k); core.addColorStop(0, 'rgba(255,236,215,0.9)'); core.addColorStop(0.4, 'rgba(255,170,150,0.35)'); core.addColorStop(1, 'rgba(0,0,0,0)'); g.fillStyle = core; g.fillRect(0, 0, w, w);
  }, { linear: true });
}
// the hook as a constellation: hand-drawn stroke letters, stars on the vertices, thin lines drawn on with her voice
const GLYPH = {
  L: [[[0, 1], [0, 0], [0.55, 0]]], O: [[[0.3, 1], [0.56, 0.84], [0.62, 0.5], [0.56, 0.16], [0.3, 0], [0.05, 0.16], [0, 0.5], [0.05, 0.84], [0.3, 1]]],
  K: [[[0, 1], [0, 0]], [[0.55, 1], [0, 0.42]], [[0.17, 0.57], [0.58, 0]]], W: [[[0, 1], [0.19, 0], [0.39, 0.64], [0.59, 0], [0.78, 1]]],
  H: [[[0, 1], [0, 0]], [[0.56, 1], [0.56, 0]], [[0, 0.52], [0.56, 0.52]]], A: [[[0, 0], [0.31, 1], [0.62, 0]], [[0.13, 0.4], [0.49, 0.4]]],
  T: [[[0, 1], [0.62, 1]], [[0.31, 1], [0.31, 0]]], I: [[[0, 1], [0, 0]]], C: [[[0.6, 0.84], [0.33, 1], [0.06, 0.85], [0, 0.5], [0.06, 0.15], [0.33, 0], [0.6, 0.16]]],
  N: [[[0, 0], [0, 1], [0.56, 0], [0.56, 1]]], D: [[[0, 0], [0, 1], [0.3, 1], [0.56, 0.8], [0.62, 0.5], [0.56, 0.2], [0.3, 0], [0, 0]]],
};
const ADV = { L: 0.8, O: 0.86, K: 0.8, W: 1.0, H: 0.8, A: 0.86, T: 0.86, I: 0.36, C: 0.84, N: 0.8, D: 0.86, ' ': 0.5 };
function buildConstellation(times) {   // times: per word [t0] → letters draw on from their word's time
  const lines = [['LOOK WHAT', [0, 1]], ['I CAN DO', [2, 3, 4]]]; const segs = [], stars = []; const lh = 1.55;
  lines.forEach(([txt, words], li) => {
    const wsum = [...txt].reduce((a, ch) => a + ADV[ch], 0); let x = -wsum / 2; let wi = 0;
    [...txt].forEach((ch) => {
      if (ch === ' ') { wi++; x += ADV[' ']; return; }
      const t0 = times[words[wi]]; const y0 = (li === 0 ? 0.5 : -0.5) * lh - 0.5;
      const strokes = GLYPH[ch]; let n = 0; const tot = strokes.reduce((a, s) => a + s.length - 1, 0);
      strokes.forEach((st) => { for (let i = 0; i < st.length; i++) { const p = [x + st[i][0], y0 + st[i][1]];
        if (!stars.some((s) => Math.hypot(s.p[0] - p[0], s.p[1] - p[1]) < 0.02)) stars.push({ p, t: t0 + n / Math.max(1, tot) * 0.32 });
        if (i > 0) { segs.push({ a: [x + st[i - 1][0], y0 + st[i - 1][1]], b: p, t: t0 + (n / tot) * 0.32, d: 0.32 / tot + 0.03 }); n++; } } });
      x += ADV[ch];
    });
  });
  // lines: one quad per segment, drawn on in the vertex shader
  const n = segs.length; const pos = new Float32Array(n * 4 * 3), aA = new Float32Array(n * 4 * 2), aB = new Float32Array(n * 4 * 2), aS = new Float32Array(n * 4 * 2), aT = new Float32Array(n * 4 * 2); const idx = [];
  segs.forEach((s, i) => { for (let k = 0; k < 4; k++) { const j = i * 4 + k; aA.set(s.a, j * 2); aB.set(s.b, j * 2); aS.set([k % 2 ? 1 : -1, k < 2 ? 0 : 1], j * 2); aT.set([s.t, s.d], j * 2); } idx.push(i * 4, i * 4 + 1, i * 4 + 3, i * 4, i * 4 + 3, i * 4 + 2); });
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(pos, 3)); g.setAttribute('aA', new THREE.BufferAttribute(aA, 2)); g.setAttribute('aB', new THREE.BufferAttribute(aB, 2));
  g.setAttribute('aS', new THREE.BufferAttribute(aS, 2)); g.setAttribute('aT', new THREE.BufferAttribute(aT, 2)); g.setIndex(idx);
  const lm = new THREE.ShaderMaterial({ uniforms: { uTime: { value: 0 }, uW: { value: 0.05 }, uCol: { value: new THREE.Color(PINK).multiplyScalar(2.0) }, uA: { value: 1 } },
    vertexShader: `attribute vec2 aA, aB, aS, aT; uniform float uTime, uW; varying float vK; varying float vE;
      void main(){ float k = clamp((uTime - aT.x) / aT.y, 0.0, 1.0); vec2 d = aB - aA; float len = length(d); vec2 dir = d / max(len, 1e-5); vec2 nrm = vec2(-dir.y, dir.x);
        vec2 p = aA + d * (aS.y * k) + nrm * aS.x * uW; vK = k; vE = aS.x; gl_Position = projectionMatrix * modelViewMatrix * vec4(p, 0.0, 1.0); }`,
    fragmentShader: `uniform vec3 uCol; uniform float uA; varying float vK; varying float vE; void main(){ if (vK <= 0.0) discard; float a = 1.0 - abs(vE); gl_FragColor = vec4(uCol * (0.4 + 0.6 * a) * uA * 0.95, 1.0); }`,
    transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide });   // the quads wind clockwise to the camera: draw both sides
  const lineMesh = new THREE.Mesh(g, lm); lineMesh.frustumCulled = false;
  // stars
  const sg = new THREE.InstancedBufferGeometry(); const base = new THREE.PlaneGeometry(1, 1); sg.index = base.index; sg.setAttribute('position', base.attributes.position); sg.setAttribute('uv', base.attributes.uv); sg.instanceCount = stars.length;
  const sp = new Float32Array(stars.length * 3); stars.forEach((s, i) => sp.set([s.p[0], s.p[1], s.t], i * 3)); sg.setAttribute('aP', new THREE.InstancedBufferAttribute(sp, 3));
  const sm = new THREE.ShaderMaterial({ uniforms: { uTime: { value: 0 }, uMap: { value: starTex() }, uA: { value: 1 }, uPulse: { value: 0 } },
    vertexShader: `attribute vec3 aP; uniform float uTime, uPulse; varying vec2 vUv; varying float vK;
      void main(){ vUv = uv; float x = uTime - aP.z; float k = x < 0.0 ? 0.0 : (x < 0.12 ? x / 0.12 * 1.8 : 1.0 + 0.8 * exp(-(x - 0.12) * 6.0)); vK = k;
        float s = 0.055 * k * (1.0 + 0.35 * uPulse); gl_Position = projectionMatrix * modelViewMatrix * vec4(aP.xy + position.xy * s, 0.0, 1.0); }`,
    fragmentShader: `uniform sampler2D uMap; uniform float uA; varying vec2 vUv; varying float vK; void main(){ if (vK <= 0.0) discard; vec3 t = texture2D(uMap, vUv).rgb; gl_FragColor = vec4(t * vec3(1.0, 0.55, 0.78) * 1.8 * uA, 1.0); }`,
    transparent: true, depthWrite: false, blending: THREE.AdditiveBlending });
  const starMesh = new THREE.Mesh(sg, sm); starMesh.frustumCulled = false;
  const grp = new THREE.Group(); grp.add(lineMesh, starMesh); grp.userData = { lm, sm }; return grp;
}
let _starTex = null;
function starTex() {   // a soft star with four fine spikes
  if (_starTex) return _starTex;
  _starTex = L.canvasTex(256, 256, (g, w) => { const c = w / 2; const gr = g.createRadialGradient(c, c, 0, c, c, c); gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.08, 'rgba(255,255,255,0.85)'); gr.addColorStop(0.25, 'rgba(255,255,255,0.18)'); gr.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = gr; g.fillRect(0, 0, w, w);
    g.globalCompositeOperation = 'lighter'; for (const [dx, dy] of [[1, 0], [0, 1]]) { const lg = g.createLinearGradient(c - dx * c, c - dy * c, c + dx * c, c + dy * c); lg.addColorStop(0, 'rgba(255,255,255,0)'); lg.addColorStop(0.5, 'rgba(255,255,255,0.75)'); lg.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = lg; if (dx) g.fillRect(0, c - 2, w, 4); else g.fillRect(c - 2, 0, 4, w); } }, { linear: true });
  return _starTex;
}
function burstTex() {   // the gold review stars: a big six-spike flare
  return L.canvasTex(512, 512, (g, w) => { const c = w / 2; g.globalCompositeOperation = 'lighter';
    const gr = g.createRadialGradient(c, c, 0, c, c, c * 0.5); gr.addColorStop(0, 'rgba(255,255,240,1)'); gr.addColorStop(0.15, 'rgba(255,225,150,0.9)'); gr.addColorStop(0.5, 'rgba(255,190,80,0.25)'); gr.addColorStop(1, 'rgba(255,170,60,0)'); g.fillStyle = gr; g.fillRect(0, 0, w, w);
    for (let i = 0; i < 6; i++) { g.save(); g.translate(c, c); g.rotate(i * Math.PI / 3 + Math.PI / 6); const lg = g.createLinearGradient(0, 0, c, 0); lg.addColorStop(0, 'rgba(255,240,190,0.95)'); lg.addColorStop(1, 'rgba(255,200,90,0)'); g.fillStyle = lg; g.beginPath(); g.moveTo(0, -5); g.lineTo(c * (i % 2 ? 0.62 : 1), 0); g.lineTo(0, 5); g.fill(); g.restore(); } }, { linear: true });
}
function cardTex() { const c = document.createElement('canvas'); c.width = 1240; c.height = 600; const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8; t.userData = { c, key: '' }; return t; }
function starPath(g, cx, cy, R, r) { g.beginPath(); for (let i = 0; i < 10; i++) { const a = -Math.PI / 2 + i * Math.PI / 5; const rr = i % 2 ? r : R; g.lineTo(cx + Math.cos(a) * rr, cy + Math.sin(a) * rr); } g.closePath(); }
function drawCard(n) {   // ★★★★★ fill one per beat with the galaxy's stars; the quote is there from the start (readable for the whole line)
  const key = String(n); if (CARDT.userData.key === key) return; CARDT.userData.key = key; const g = CARDT.userData.c.getContext('2d'); const w = 1240, h = 600;
  g.clearRect(0, 0, w, h); g.fillStyle = 'rgba(12,11,16,0.9)'; g.beginPath(); g.roundRect(10, 10, w - 20, h - 20, 44); g.fill(); g.strokeStyle = 'rgba(255,214,120,0.35)'; g.lineWidth = 3; g.stroke();
  for (let i = 0; i < 5; i++) { const cx = 120 + i * 112, cy = 132; starPath(g, cx, cy, 46, 19); if (i < n) { g.fillStyle = '#ffcc4a'; g.shadowColor = '#ffb020'; g.shadowBlur = 26; g.fill(); g.shadowBlur = 0; } else { g.strokeStyle = 'rgba(255,214,120,0.55)'; g.lineWidth = 4; g.stroke(); } }
  let fs = 128; g.font = `${fs}px ${L.FONT.serifI}`; const q = '“Great universe.”'; while (g.measureText(q).width > w - 150 && fs > 60) { fs -= 4; g.font = `${fs}px ${L.FONT.serifI}`; }
  g.fillStyle = INK; g.textBaseline = 'alphabetic'; g.fillText(q, 72, 360);
  g.font = `56px ${L.FONT.ui}`; g.fillStyle = 'rgba(236,230,216,0.78)'; g.fillText('— Adita', 76, 478);
  CARDT.needsUpdate = true;
}
// the drop: a tunnel of her screens, speed streaks, four neon ring gates
const TUN_VS = `attribute vec4 aRect; attribute vec4 aT; attribute vec2 aSz;   // aT: angle, radius, z (0..range), bright
  uniform vec3 uO, uD, uU, uV, uCamR, uCamU; uniform float uS, uRange, uTwist, uDiss, uPulse;
  varying vec2 vUv; varying float vB;
  void main(){
    vUv = aRect.xy + uv * aRect.zw;
    float along = mod(aT.z - uS, uRange) - 4.0;
    float a = aT.x + uTwist; float r = aT.y * (1.0 + 2.8 * uDiss);
    vec3 c = uO + uD * along + (cos(a) * uU + sin(a) * uV) * r;
    float fade = smoothstep(uRange - 4.0, uRange * 0.45, along) * smoothstep(-4.0, 3.0, along);
    vB = aT.w * fade * (1.0 + 0.6 * uPulse) * (1.0 - uDiss);
    vec3 p = c + uCamR * position.x * aSz.x + uCamU * position.y * aSz.y;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(p, 1.0);
  }`;
const TUN_FS = `uniform sampler2D uMap; varying vec2 vUv; varying float vB; void main(){ if (vB < 0.003) discard; gl_FragColor = vec4(texture2D(uMap, vUv).rgb * vB, 1.0); }`;
const STREAK_VS = `attribute vec4 aT; attribute vec3 aC;    // aT: angle, radius, z, length
  uniform vec3 uO, uD, uU, uV; uniform float uS, uRange, uStretch, uDiss, uW;
  varying float vY; varying vec3 vC; varying float vF;
  void main(){
    float along = mod(aT.z - uS * 1.15, uRange) - 6.0;
    vec3 rad = cos(aT.x) * uU + sin(aT.x) * uV; vec3 tan_ = -sin(aT.x) * uU + cos(aT.x) * uV;
    float len = aT.w * uStretch;
    vec3 p = uO + uD * (along + position.y * len) + rad * aT.y * (1.0 + 2.0 * uDiss) + tan_ * position.x * uW;
    vY = position.y; vC = aC; vF = smoothstep(uRange - 6.0, uRange * 0.5, along) * smoothstep(-6.0, 2.0, along) * (1.0 - uDiss);
    gl_Position = projectionMatrix * modelViewMatrix * vec4(p, 1.0);
  }`;
const STREAK_FS = `varying float vY; varying vec3 vC; varying float vF; void main(){ float a = pow(1.0 - vY, 2.0) * vF; gl_FragColor = vec4(vC * a, 1.0); }`;
function neonLetter(ch, h, size) {   // like sets.neon but with a tight glow, so the hook stays crisp at speed
  const f = `${size}px ${L.FONT.anton}`; const g0 = document.createElement('canvas').getContext('2d'); g0.font = f;
  const tw = g0.measureText(ch).width; const pad = size * 0.55; const Wc = Math.ceil(tw + pad * 2), Hc = Math.ceil(size * 1.6 + pad);
  const tex = L.canvasTex(Wc, Hc, (g, w, hh) => { g.font = f; g.textAlign = 'center'; g.textBaseline = 'middle';
    g.shadowColor = PINK; g.shadowBlur = size * 0.16; g.fillStyle = PINK; g.fillText(ch, w / 2, hh / 2); g.fillText(ch, w / 2, hh / 2);
    g.shadowBlur = 0; g.fillStyle = '#ffe9f3'; g.fillText(ch, w / 2, hh / 2); g.lineWidth = size * 0.03; g.strokeStyle = '#ff9cc8'; g.strokeText(ch, w / 2, hh / 2); });
  const m = new THREE.Mesh(new THREE.PlaneGeometry(h * Wc / Hc, h), new THREE.MeshBasicMaterial({ map: tex, transparent: true, depthWrite: false, toneMapped: false, blending: THREE.AdditiveBlending }));
  m.material.color.setScalar(1.25); return m;
}
function makeGate(seed) {
  const g = new THREE.Group(); const R0 = 6.6;
  const core = new THREE.Mesh(new THREE.TorusGeometry(R0, 0.07, 8, 180), new THREE.MeshBasicMaterial({ color: new THREE.Color(2.6, 1.6, 2.2), toneMapped: false, transparent: true }));
  const tube = new THREE.Mesh(new THREE.TorusGeometry(R0, 0.2, 10, 180), new THREE.MeshBasicMaterial({ color: new THREE.Color(PINK).multiplyScalar(1.6), toneMapped: false, transparent: true, opacity: 0.55, blending: THREE.AdditiveBlending, depthWrite: false }));
  const halo = new THREE.Mesh(new THREE.TorusGeometry(R0, 0.9, 10, 180), new THREE.MeshBasicMaterial({ color: new THREE.Color(PINK), toneMapped: false, transparent: true, opacity: 0.08, blending: THREE.AdditiveBlending, depthWrite: false }));
  g.add(halo, tube, core);
  // the hook along the top of the ring, letters standing on it
  const text = 'LOOK WHAT I CAN DO'; const size = 220; const g0 = document.createElement('canvas').getContext('2d'); g0.font = `${size}px ${L.FONT.anton}`;
  const capH = 1.9, hPlane = capH / 0.34, sw = hPlane / (2.15 * size);    // canvas height = 2.15·size, Anton caps ≈ 0.73·size
  const ws = [...text].map((ch) => (ch === ' ' ? 0.32 * size : g0.measureText(ch).width) * sw * 1.06); const tot = ws.reduce((a, b) => a + b, 0); const Rt = R0 + 0.3 + capH * 0.55;
  let acc = -tot / 2; const letters = [];
  [...text].forEach((ch, i) => { const mid = acc + ws[i] / 2; acc += ws[i]; if (ch === ' ') return; const phi = mid / Rt;
    const m = neonLetter(ch, hPlane, size); m.position.set(Math.sin(phi) * Rt, Math.cos(phi) * Rt, 0.05); m.rotation.z = -phi; g.add(m); letters.push(m); });
  g.userData = { core, tube, halo, letters, seed }; g.visible = false; return g;
}
function postCanvas(img, boxes) { const c = document.createElement('canvas'); c.width = img.width; c.height = img.height; const tx = new THREE.CanvasTexture(c); tx.colorSpace = THREE.SRGBColorSpace; tx.anisotropy = 8; return { c, tx, img, boxes, key: '' }; }
function drawPost(Pc, fracs) {
  const key = fracs.map((f) => f.toFixed(3)).join(','); if (key === Pc.key) return; Pc.key = key;
  const g = Pc.c.getContext('2d'); g.globalCompositeOperation = 'source-over'; g.drawImage(Pc.img, 0, 0);
  g.globalCompositeOperation = 'multiply'; g.fillStyle = HL;
  Pc.boxes.forEach(([x0, y0, x1, y1], i) => { const f = clamp(fracs[i] || 0); if (f > 0) g.fillRect(x0 - 8, y0 - 6, (x1 - x0 + 16) * f, y1 - y0 + 12); });
  g.globalCompositeOperation = 'source-over'; Pc.tx.needsUpdate = true;
}
function stampTex(word, sub, color) {
  return L.canvasTex(760, 300, (g, w, h) => { g.translate(w / 2, h / 2); g.rotate(-8 * Math.PI / 180); g.textAlign = 'center'; g.textBaseline = 'middle';
    g.strokeStyle = color; g.lineWidth = 12; g.globalAlpha = 0.95; g.beginPath(); g.roundRect(-330, -105, 660, 210, 20); g.stroke();
    g.fillStyle = color; g.font = '140px "Anton"'; g.fillText(word, 0, -22); g.font = '44px "JBB"'; g.fillText(sub, 0, 72); });
}
const P_O = V3(26, 58, 196), LOOK_O = V3(4, -4, 0);      // where the warp comes to rest, looking into the galaxy
let D_O, U_O, V_O;
async function buildGalaxy() {
  G = new THREE.Scene(); G.background = new THREE.Color(0x000000);
  camG = new THREE.PerspectiveCamera(42, W / H, 0.1, 6000); G.add(camG);
  GAL = new THREE.Group(); G.add(GAL);
  const items = galaxyItems(7, 3600);
  const by = { H1: [], H2: [], V1: [], V2: [] }; const names = Object.keys(by); items.forEach((it, i) => by[names[i % 4]].push(it));
  for (const a of names) { const m = screenField(a, by[a]); GAL.add(m); GSCREENS.push(m); }
  GGLOW = new THREE.Mesh(new THREE.PlaneGeometry(270, 270), new THREE.MeshBasicMaterial({ map: glowTex(), transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false }));
  GGLOW.rotation.x = -Math.PI / 2; GGLOW.position.y = -0.5; GGLOW.material.color.setScalar(1.25); GAL.add(GGLOW);
  GCORE = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.MeshBasicMaterial({ map: L.dotTex(), color: new THREE.Color(1.5, 1.15, 0.95), transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false }));
  GCORE.scale.setScalar(24); GCORE.material.color.setRGB(1.1, 0.86, 0.78); GAL.add(GCORE);
  { const R = L.rng(12); const n = 7000; const pos = new Float32Array(n * 3); for (let i = 0; i < n; i++) { const r = 4 + 115 * Math.pow(R(), 0.8); const th = (i % 2) * Math.PI + Math.log(Math.max(r, 7) / 7) / Math.tan(0.3) + gauss(R) * (0.25 + 0.3 * r / GR); pos.set([Math.cos(th) * r, gauss(R) * (1 + 3 * Math.exp(-r / 20)), Math.sin(th) * r], i * 3); }
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(pos, 3)); GSTARS = new THREE.Points(g, new THREE.PointsMaterial({ map: L.dotTex(), size: 0.45, color: new THREE.Color(1.1, 1.0, 1.15), transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false })); GAL.add(GSTARS); }
  BGSTARS = starPoints(5000, 21, 1.5, 4000); G.add(BGSTARS);
  // the constellation, far behind the galaxy in the sky we look into
  CONST = buildConstellation([T.fin3, wt('Look what I can do!', 'what', 10), wt('Look what I can do!', 'I', 10), wt('Look what I can do!', 'can', 10), wt('Look what I can do!', 'do', 10)]);
  CONST.scale.setScalar(40); G.add(CONST);
  // five review stars: big flares in the arms
  const bt = burstTex();
  for (let i = 0; i < 5; i++) { const m = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.MeshBasicMaterial({ map: bt, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false })); m.visible = false; G.add(m); FIVE.push(m); }
  // the review card (camera-attached, lower right)
  CARDT = cardTex(); drawCard(0);
  CARD = new THREE.Mesh(new THREE.PlaneGeometry(1240 / 600, 1), new THREE.MeshBasicMaterial({ map: CARDT, transparent: true, depthWrite: false, depthTest: false, toneMapped: false })); CARD.renderOrder = 60; CARD.visible = false; camG.add(CARD);
  // the drop tunnel (screens + streaks), placed on the warp's axis in the vertex shader
  D_O = LOOK_O.clone().sub(P_O).normalize(); U_O = V3(0, 1, 0).cross(D_O).normalize(); V_O = D_O.clone().cross(U_O).normalize();
  const tunU = () => ({ uO: { value: V3() }, uD: { value: D_O.clone() }, uU: { value: U_O.clone() }, uV: { value: V_O.clone() }, uCamR: { value: V3(1, 0, 0) }, uCamU: { value: V3(0, 1, 0) }, uS: { value: 0 }, uRange: { value: 170 }, uTwist: { value: 0 }, uDiss: { value: 0 }, uPulse: { value: 0 } });
  for (const a of ['H1', 'H2']) {
    const R = L.rng(a === 'H1' ? 31 : 32); const n = 230; const base = new THREE.PlaneGeometry(1, 1); const g = new THREE.InstancedBufferGeometry(); g.index = base.index; g.setAttribute('position', base.attributes.position); g.setAttribute('uv', base.attributes.uv); g.instanceCount = n;
    const aRect = new Float32Array(n * 4), aT = new Float32Array(n * 4), aSz = new Float32Array(n * 2);
    for (let i = 0; i < n; i++) { aRect.set(M.cellRect(a, Math.floor(R() * 16)), i * 4); const s = 1.5 + R() * 2.2; aSz.set([s, s * 0.5625], i * 2); aT.set([R() * Math.PI * 2, 3.4 + Math.pow(R(), 0.7) * 8, R() * 170, 0.75 + R() * 0.5], i * 4); }
    g.setAttribute('aRect', new THREE.InstancedBufferAttribute(aRect, 4)); g.setAttribute('aT', new THREE.InstancedBufferAttribute(aT, 4)); g.setAttribute('aSz', new THREE.InstancedBufferAttribute(aSz, 2));
    const mat = new THREE.ShaderMaterial({ uniforms: { ...tunU(), uMap: { value: M.texOf(a) } }, vertexShader: TUN_VS, fragmentShader: TUN_FS, side: THREE.DoubleSide });
    const m = new THREE.Mesh(g, mat); m.frustumCulled = false; m.visible = false; G.add(m); TUN.push(m);
  }
  { const R = L.rng(41); const n = 900; const base = new THREE.PlaneGeometry(1, 1); base.translate(0, 0.5, 0); const g = new THREE.InstancedBufferGeometry(); g.index = base.index; g.setAttribute('position', base.attributes.position); g.instanceCount = n;
    const aT = new Float32Array(n * 4), aC = new Float32Array(n * 3); const cols = [[1, 1, 1], [1.0, 0.37, 0.64], [1.0, 0.66, 0.25], [0.6, 0.75, 1.0]];
    for (let i = 0; i < n; i++) { aT.set([R() * Math.PI * 2, 1.6 + Math.pow(R(), 0.6) * 11, R() * 200, 2 + R() * 7], i * 4); const c = cols[Math.floor(R() * 4)]; const b = 0.6 + R() * 1.4; aC.set([c[0] * b, c[1] * b, c[2] * b], i * 3); }
    g.setAttribute('aT', new THREE.InstancedBufferAttribute(aT, 4)); g.setAttribute('aC', new THREE.InstancedBufferAttribute(aC, 3));
    const mat = new THREE.ShaderMaterial({ uniforms: { ...tunU(), uRange: { value: 200 }, uStretch: { value: 1 }, uW: { value: 0.035 } }, vertexShader: STREAK_VS, fragmentShader: STREAK_FS, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide });
    STREAKS = new THREE.Mesh(g, mat); STREAKS.frustumCulled = false; STREAKS.visible = false; G.add(STREAKS); }
  for (let i = 0; i < 4; i++) { const g = makeGate(i); G.add(g); GATES.push(g); }
  // the outro: floating terminal lines (camera-attached), the last screen with her real post
  TERM = [runsPlane([['❯ ', GREEN], ['Claude?', INK]]), runsPlane([['● ', AMBER], ['Yes?', AMBER]]), runsPlane([['❯ ', GREEN], ['Can we make one more?', INK]]), runsPlane([['● ', AMBER], ["You've reached your usage limit.", AMBER]])];
  TERM.forEach((m) => { m.visible = false; camG.add(m); });
  TPANEL = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.MeshBasicMaterial({ map: L.canvasTex(256, 128, (g, w, h) => { const gr = g.createRadialGradient(w / 2, h / 2, 0, w / 2, h / 2, w / 2); gr.addColorStop(0, 'rgba(0,0,0,0.78)'); gr.addColorStop(0.6, 'rgba(0,0,0,0.55)'); gr.addColorStop(1, 'rgba(0,0,0,0)'); g.fillStyle = gr; g.fillRect(0, 0, w, h); }), transparent: true, depthWrite: false, depthTest: false }));
  TPANEL.renderOrder = 49; TPANEL.visible = false; camG.add(TPANEL);
  const img = (await M.image('post_usage.png')).image;
  LASTP = postCanvas(img, [[250, 283, 1230, 344]]); drawPost(LASTP, [0]);
  const pw = 13, ph = pw * img.height / img.width;
  LAST = new THREE.Group();
  const bez = new THREE.Mesh(new RoundedBoxGeometry(pw + 0.5, ph + 0.5, 0.3, 4, 0.12), new THREE.MeshStandardMaterial({ color: 0x0c0c0f, metalness: 0.85, roughness: 0.3, envMap: envTex, envMapIntensity: 0.8 })); bez.position.z = -0.16; LAST.add(bez);
  const disp = new THREE.Mesh(new THREE.PlaneGeometry(pw, ph), new THREE.MeshBasicMaterial({ map: M.texOf('H1'), toneMapped: false })); LAST.add(disp);
  STAMP = new THREE.Mesh(new THREE.PlaneGeometry(pw * 0.42, pw * 0.42 * 300 / 760), new THREE.MeshBasicMaterial({ map: stampTex('RECEIPT', 'OCT 28, 2026', RED), transparent: true, depthWrite: false, toneMapped: false }));
  STAMP.position.set(pw * (1090 / 1320 - 0.5), ph * (0.5 - 226 / img.height), 0.02); STAMP.scale.setScalar(0.52); LAST.add(STAMP);
  LAST.userData = { disp, pw, ph, rectH: M.cellRect('H1', 12, 0) };
  LAST.position.set(52, 22, 112); LAST.lookAt(V3(30, 40, 168)); LAST.visible = false; G.add(LAST);
  G.add(new THREE.HemisphereLight(0x9aa6c8, 0x050506, 0.7));
}
// a beat-synced warp: cruise speed + a surge on every beat, an extra kick through each gate; then it settles
let WARP = null;
function buildWarp() {
  const beats = L.TIMING.beats.filter((b) => b >= T.drop - 0.01 && b <= T.gates[3] + 0.1);
  const v0 = 86, A = 26, tau = 0.17, G0 = 55, gt = 0.3; const Td = T.gates[3] + 0.06, td = 0.42;
  const sAt = (t) => { const tt = Math.min(t, Td); let s = v0 * Math.max(0, tt - T.drop); for (const b of beats) if (b <= tt) s += A * tau * (1 - Math.exp(-(tt - b) / tau));
    for (const gp of T.gates) if (gp - 0.2 <= tt) s += G0 * gt * (1 - Math.exp(-(tt - gp + 0.2) / gt)); return s; };
  const vAt = (t) => { let v = v0; for (const b of beats) if (b <= t) v += A * Math.exp(-(t - b) / tau); for (const gp of T.gates) if (gp - 0.2 <= t) v += G0 * Math.exp(-(t - gp + 0.2) / gt); return v; };
  const sTd = sAt(Td), vTd = vAt(Td); const total = sTd + vTd * td;
  WARP = { Td, td, total, s: (t) => t <= Td ? sAt(t) : sTd + vTd * td * (1 - Math.exp(-(t - Td) / td)), v: (t) => t <= Td ? vAt(t) : vTd * Math.exp(-(t - Td) / td) };
}
const _q = new THREE.Quaternion(), _qi = new THREE.Quaternion(), _r = new THREE.Vector3(), _u = new THREE.Vector3();
function updateBillboards() {   // camera right/up in the galaxy's frame for the billboard shader
  camG.updateMatrixWorld(true); _q.copy(camG.quaternion); _qi.copy(GAL.quaternion).invert();
  _r.set(1, 0, 0).applyQuaternion(_q).applyQuaternion(_qi); _u.set(0, 1, 0).applyQuaternion(_q).applyQuaternion(_qi);
  GSCREENS.forEach((m) => { m.material.uniforms.uCamR.value.copy(_r); m.material.uniforms.uCamU.value.copy(_u); });
  GCORE.quaternion.copy(_qi).multiply(_q);
}
function setCamG(p, l, fov, roll = 0) {
  camG.position.copy(p); const f = l.clone().sub(p).normalize(); const right = f.clone().cross(V3(0, 1, 0)).normalize(); const up = right.clone().cross(f).normalize();
  camG.up.copy(up.multiplyScalar(Math.cos(roll)).add(right.multiplyScalar(Math.sin(roll)))); camG.lookAt(l); camG.fov = fov; camG.updateProjectionMatrix();
}
function track(keys, ease = easeIO) {
  const Pc = new THREE.CatmullRomCurve3(keys.map((k) => V3(...k.p)), false, 'centripetal'); const Lc = new THREE.CatmullRomCurve3(keys.map((k) => V3(...k.l)), false, 'centripetal');
  const t0 = keys[0].t, t1 = keys[keys.length - 1].t, n = keys.length;
  return (t) => { const tau = t0 + ease(clamp((t - t0) / (t1 - t0))) * (t1 - t0); let i = 0; while (i < n - 2 && tau > keys[i + 1].t) i++;
    const f = clamp((tau - keys[i].t) / (keys[i + 1].t - keys[i].t)); const u = (i + f) / (n - 1); return { p: Pc.getPoint(u), l: Lc.getPoint(u), fov: lerp(keys[i].fov, keys[i + 1].fov, f) }; };
}
let GCAM = null, OCAM = null;
function buildGalaxyCams() {
  GCAM = track([
    { t: T.fin3, p: [74, 7, 66], l: [-6, 2, -10], fov: 50 },
    { t: T.fin4, p: [36, 12, 92], l: [-4, 4, -12], fov: 46 },
    { t: T.univ, p: [-22, 34, 132], l: [0, 6, -6], fov: 44 },
    { t: T.review, p: [-70, 112, 214], l: [0, -6, -6], fov: 40 },
    { t: T.brk, p: [-46, 124, 230], l: [2, -8, -4], fov: 40 },
  ], (x) => x);
  OCAM = track([
    { t: WARP.Td + 0.95, p: [P_O.x, P_O.y, P_O.z], l: [LOOK_O.x, LOOK_O.y, LOOK_O.z], fov: 46 },
    { t: T.limit, p: [P_O.x - 10, P_O.y - 2, P_O.z - 14], l: [LOOK_O.x - 54, LOOK_O.y + 26, LOOK_O.z], fov: 45 },
  ], (x) => easeOut(x));
}
const FIVE_POS = [V3(-62, 4, 18), V3(-30, 2, -46), V3(8, 3, 22), V3(44, 2, -30), V3(70, 4, 26)];
function galaxyCommon(t, { bright = 1, wave0 = 1e9, waveDur = 1.6 } = {}) {
  GAL.rotation.y = -0.045 * (t - T.fin3);
  updateBillboards();
  GSCREENS.forEach((m) => { const U = m.material.uniforms; U.uTime.value = t; U.uWave0.value = wave0; U.uWaveDur.value = waveDur; U.uBright.value = bright; });
}
function frameGalaxy(t) {
  const u = look.finish.uniforms, bloom = look.bloom; const pulse = L.beatPulse(t, 7);
  hideDrop(); TERM.forEach((m) => { m.visible = false; }); LAST.visible = false; GAL.visible = true; GAL.position.set(0, 0, 0); GSCREENS.forEach((m) => { m.visible = true; });
  const c = GCAM(t); setCamG(c.p, c.l, c.fov, 0.04 * Math.sin((t - T.fin3) * 0.6));
  galaxyCommon(t, { bright: 1.05 + 0.12 * pulse });
  GSCREENS.forEach((m) => M.use(m.userData.atlas));
  GSTARS.material.opacity = 0.8; BGSTARS.material.opacity = 1; GGLOW.material.opacity = 1; GCORE.material.opacity = 0.35;
  // constellation: draws on with the first hook line, pulses with the second, makes room for the review
  { const fwd = V3(0, 0, -1).applyQuaternion(camG.quaternion), right = V3(1, 0, 0).applyQuaternion(camG.quaternion);   // the hook hangs in the sky of the shot, above the galaxy
    const dir = fwd.clone().applyAxisAngle(right, THREE.MathUtils.degToRad(12.0)); CONST.position.copy(camG.position).addScaledVector(dir, 520); CONST.up.set(0, 1, 0); CONST.lookAt(camG.position); }
  const cu = CONST.userData; cu.lm.uniforms.uTime.value = t; cu.sm.uniforms.uTime.value = t;
  const ca = 1 - sstep(T.review - 0.9, T.review - 0.1, t); cu.lm.uniforms.uA.value = ca * (1 + 0.5 * env(t, T.fin4, 0.02, 0.5)); cu.sm.uniforms.uA.value = ca; cu.sm.uniforms.uPulse.value = env(t, T.fin4, 0.02, 0.4) + 0.3 * pulse;
  CONST.visible = ca > 0.01;
  // five stars flare gold, one per beat from 'And left it…'; the card's stars fill with them
  const bt = L.TIMING.beats.filter((b) => b >= T.review - 0.05).slice(0, 5); let lit = 0;
  FIVE.forEach((m, i) => { const x = t - bt[i]; m.visible = x > -0.02; if (!m.visible) return; lit = i + 1;
    const p = FIVE_POS[i].clone().applyAxisAngle(V3(0, 1, 0), GAL.rotation.y); m.position.copy(p); m.quaternion.copy(camG.quaternion);
    const s = x < 0.08 ? 64 * (x + 0.02) / 0.1 : 24 + 40 * Math.exp(-(x - 0.08) * 4); m.scale.setScalar(s * (1 + 0.04 * Math.sin(t * 9 + i))); m.material.opacity = 1; });
  const kc = easeOut((t - (T.review + 0.04)) / 0.4); CARD.visible = kc > 0.002;
  if (CARD.visible) { drawCard(lit); const d = 3; const hh = 2 * d * Math.tan(THREE.MathUtils.degToRad(camG.fov / 2)), ww = hh * camG.aspect; const s = ww * 0.34 / (1240 / 600);
    CARD.scale.setScalar(s); CARD.position.set(ww / 2 - s * 1240 / 600 / 2 - ww * 0.05, -hh / 2 + s / 2 + hh * 0.08 - (1 - kc) * hh * 0.12, -d); CARD.material.opacity = kc; }
  bloom.threshold = 0.86; bloom.strength = 0.5 + 0.12 * pulse; bloom.radius = 0.6; u.uVig.value = 0.36;
  u.uFlash.value = 0.12 * env(t, T.fin3, 0.005, 0.035) + 0.03 * env(t, T.fin4, 0.008, 0.035); u.uFlashCol.value.setRGB(1, 0.78, 0.9);
  u.uFade.value = sstep(T.brk - 0.32, T.brk - 0.04, t);
  return { scene: G, camera: camG };
}
function hideDrop() { TUN.forEach((m) => { m.visible = false; }); STREAKS.visible = false; GATES.forEach((g) => { g.visible = false; }); FIVE.forEach((m) => { m.visible = false; }); CARD.visible = false; }

// ---------------------------------------------------------------- the drop
function gateDist(t, i) {   // gate i comes out of the depths, hangs where the hook reads, then the camera punches through on 'do!'
  const t0 = T.shouts[i], t1 = T.gates[i]; const x = clamp((t - t0) / (t1 - t0));
  return 175 * Math.pow(1 - x, 4) + 21 * Math.pow(1 - x, 0.5) - 3 * Math.pow(x, 12);
}
async function frameDrop(t) {
  const u = look.finish.uniforms, bloom = look.bloom; const pulse = L.beatPulse(t, 9);
  const s = WARP.s(t), v = WARP.v(t);
  const pos = P_O.clone().addScaledVector(D_O, s - WARP.total);
  // camera roll: a slow corkscrew, a snap on every downbeat, level while a gate's hook is readable
  const db = L.TIMING.downbeats.filter((b) => b >= T.drop - 0.01 && b <= t); const nSnap = db.length;
  let level = 0; for (let i = 0; i < 4; i++) level = Math.max(level, sstep(T.shouts[i] + 0.15, T.shouts[i] + 0.5, t) * (1 - sstep(T.gates[i] - 0.05, T.gates[i] + 0.25, t)));
  const settle = sstep(WARP.Td, WARP.Td + 0.7, t); let read = 0; for (let i = 0; i < 4; i++) read = Math.max(read, sstep(T.shouts[i] + 0.1, T.shouts[i] + 0.35, t) * (1 - sstep(T.gates[i] - 0.22, T.gates[i] - 0.06, t)));
  const roll = (0.22 * Math.sin((t - T.drop) * 0.9) + (nSnap % 2 ? 0.18 : -0.18)) * (1 - level) * (1 - settle);
  const shake = V3(L.noise1(t * 9, 1), L.noise1(t * 9, 2), 0).multiplyScalar(0.06 * (1 - settle));
  const look_ = pos.clone().add(D_O.clone().multiplyScalar(50)).lerp(LOOK_O, settle);
  setCamG(pos.clone().add(shake), look_, lerp(62 + 8 * Math.min(1, (v - 86) / 120), 46, settle), roll);
  // the tunnel follows the camera on the warp axis
  const diss = sstep(WARP.Td - 0.05, WARP.Td + 0.75, t);
  camG.updateMatrixWorld(true); const cr = V3(1, 0, 0).applyQuaternion(camG.quaternion), cu = V3(0, 1, 0).applyQuaternion(camG.quaternion);
  const twist = nSnap * 0.31416;
  TUN.forEach((m) => { m.visible = diss < 0.995; const U = m.material.uniforms; U.uO.value.copy(pos); U.uS.value = s; U.uCamR.value.copy(cr); U.uCamU.value.copy(cu); U.uTwist.value = twist; U.uDiss.value = diss; U.uPulse.value = pulse; M.use(m.material.uniforms.uMap.value === M.texOf('H1') ? 'H1' : 'H2'); });
  STREAKS.visible = diss < 0.995; { const U = STREAKS.material.uniforms; U.uO.value.copy(pos); U.uS.value = s; U.uStretch.value = 0.4 + v / 60; U.uDiss.value = diss; }
  // the galaxy waits at the end of the tunnel and comes up as we arrive
  const arrive = sstep(WARP.Td - 0.3, WARP.Td + 0.9, t);
  GAL.visible = true; galaxyCommon(t, { bright: lerp(0.05, 1.0, arrive) }); GSCREENS.forEach((m) => { m.visible = arrive > 0.02; if (m.visible) M.use(m.userData.atlas); });
  GGLOW.material.opacity = lerp(0.25, 1, arrive); GCORE.material.opacity = lerp(0.4, 1, arrive); GSTARS.material.opacity = lerp(0.2, 0.8, arrive); BGSTARS.material.opacity = 1;
  CONST.visible = false; FIVE.forEach((m) => { m.visible = false; }); CARD.visible = false; TERM.forEach((m) => { m.visible = false; }); LAST.visible = false;
  // gates
  let punch = 0;
  GATES.forEach((g, i) => {
    const t0 = T.shouts[i], t1 = T.gates[i]; const on = t >= t0 - 0.02 && t < t1 + 0.12; g.visible = on; if (!on) return;
    const d = gateDist(t, i); g.position.copy(pos).addScaledVector(D_O, d);
    const qn = new THREE.Quaternion(); const m4 = new THREE.Matrix4().lookAt(pos, pos.clone().add(D_O), V3(0, 1, 0)); qn.setFromRotationMatrix(m4); g.quaternion.copy(qn);
    const f = flicker(t, t0, i + 2) * (1 + 0.25 * pulse); const ud = g.userData;
    ud.core.material.opacity = f; ud.tube.material.opacity = 0.55 * f; ud.halo.material.opacity = 0.09 * f; ud.letters.forEach((m) => { m.material.opacity = f; });
    punch = Math.max(punch, env(t, t1, 0.008, 0.04));
  });
  // post: radial streak blur with the speed, beat pulses, a flash on the hit and through each gate
  await M.update(t);          // the atlases must be on this frame before the offscreen render
  renderer.setRenderTarget(RT); renderer.render(G, camG); renderer.setRenderTarget(null);
  QM.uniforms.uMode.value = 2; QM.uniforms.uC.value.set(0.5, 0.5); QM.uniforms.uBlur.value = (0.05 + 0.05 * pulse + 0.1 * punch + 0.06 * Math.min(1, (v - 86) / 100)) * (1 - settle) * (1 - 0.8 * read);
  bloom.threshold = 0.82; bloom.strength = 0.55 + 0.25 * pulse + 0.3 * punch; bloom.radius = 0.65; u.uVig.value = 0.42; u.uCA.value = 0.002 + 0.004 * pulse * (1 - settle);
  u.uFlash.value = 0.3 * env(t, T.drop, 0.004, 0.035) + 0.12 * punch; u.uFlashCol.value.copy(punch > 0.05 ? new THREE.Color(1.0, 0.55, 0.78) : new THREE.Color(1, 1, 1));
  const lastDb = db[db.length - 1]; if (lastDb !== undefined && t - lastDb < 0.09) u.uVel.value.set(0.02 * (nSnap % 2 ? 1 : -1) * (1 - (t - lastDb) / 0.09) * (1 - settle), 0);
  return { scene: Q, camera: qcam };
}

// ---------------------------------------------------------------- the outro: usage limit, power down, the last post
function frameOutro(t) {
  const u = look.finish.uniforms, bloom = look.bloom;
  hideDrop(); CONST.visible = false; GAL.visible = true;
  // camera: drifting in the quiet galaxy; then a push to the last screen as everything switches off around it
  const c = OCAM(Math.min(t, T.limit)); let p = c.p, l = c.l, fov = c.fov;
  const pushT0 = T.limit + 0.35, pushT1 = T.limit + 1.15;
  const k = easeIO(clamp((t - pushT0) / (pushT1 - pushT0)));
  const lastN = V3(0, 0, 1).applyQuaternion(LAST.quaternion); const pFront = LAST.position.clone().addScaledVector(lastN, 18.5);
  const hold = clamp((t - pushT1) / 1.4);
  p = p.clone().lerp(pFront.clone().addScaledVector(lastN, -1.2 * hold), k); l = l.clone().lerp(LAST.position, k); fov = lerp(fov, 40, k);
  setCamG(p, l, fov, 0);
  // the power-down wave: outer screens first, inward; stars dim
  const wave0 = T.limit + 0.25, waveDur = 0.9;
  galaxyCommon(t, { bright: 1.0, wave0, waveDur });
  const allOff = t > wave0 + waveDur + 0.35; GSCREENS.forEach((m) => { m.visible = !allOff; if (!allOff) M.use(m.userData.atlas); });
  const dim = sstep(wave0, wave0 + waveDur + 0.3, t);
  GGLOW.material.opacity = 1 - 0.92 * dim; GCORE.material.opacity = 1 - 0.95 * dim; GSTARS.material.opacity = 0.8 * (1 - 0.9 * dim); BGSTARS.material.opacity = 1 - 0.75 * dim;
  // terminal lines: one per line of dialogue, typed on; they switch off with the room
  const lt = [T.out, T.yes, T.more, T.limit]; const d = 2.2; const hh = 2 * d * Math.tan(THREE.MathUtils.degToRad(camG.fov / 2)), ww = hh * camG.aspect;
  const lineH = hh * 0.088; const termOff = T.limit + 0.8;
  TERM.forEach((m, i) => { const kk = clamp((t - lt[i] + 0.02) / 0.28); m.visible = kk > 0 && t < termOff + 0.14;
    if (!m.visible) return; m.scale.setScalar(lineH / 0.1); wipe(m, kk);
    const x = t - termOff; const sy = x > 0 ? Math.max(0.02, 1 - x / 0.07) : 1; m.scale.y *= sy; m.material.opacity = x > 0.07 ? 1 - (x - 0.07) / 0.07 : 1;
    m.position.set(-ww * 0.445, hh * 0.36 - i * lineH * 1.22, -d); });
  { const vis = TERM.some((m) => m.visible); TPANEL.visible = vis; if (vis) { const x = t - termOff; TPANEL.scale.set(ww * 0.86, lineH * 6.6 * (x > 0 ? Math.max(0.02, 1 - x / 0.07) : 1), 1); TPANEL.position.set(-ww * 0.445 + ww * 0.3, hh * 0.36 - lineH * 1.83, -d - 0.01); TPANEL.material.opacity = clamp((t - T.out + 0.1) / 0.3) * (x > 0.07 ? 0 : 1); } }
  // the last screen: a video until the limit, then her real post: highlighter, RECEIPT stamp, and off
  LAST.visible = true; const ud = LAST.userData; const toPost = T.limit + 0.15; const offT = T.gpt - 0.36;
  if (t < toPost) { if (ud.disp.material.map !== M.texOf('H1')) { ud.disp.material.map = M.texOf('H1'); ud.disp.material.needsUpdate = true; }
    const uv = ud.disp.geometry.attributes.uv; const [ox, oy, sx, sy] = ud.rectH; const asp = ud.pw / ud.ph, va = 16 / 9; const cx = asp / va;
    [[0, 1], [1, 1], [0, 0], [1, 0]].forEach(([a, b], i) => uv.setXY(i, ox + (0.5 + (a - 0.5) * cx) * sx, oy + b * sy)); uv.needsUpdate = true; M.use('H1'); STAMP.visible = false; }
  else { if (ud.disp.material.map !== LASTP.tx) { ud.disp.material.map = LASTP.tx; ud.disp.material.needsUpdate = true; const uv = ud.disp.geometry.attributes.uv; [[0, 1], [1, 1], [0, 0], [1, 0]].forEach(([a, b], i) => uv.setXY(i, a, b)); uv.needsUpdate = true; }
    drawPost(LASTP, [(t - (pushT1 + 0.02)) / 0.28]); const ks = easeOut((t - (pushT1 + 0.33)) / 0.1); STAMP.visible = ks > 0; STAMP.material.opacity = Math.min(1, ks * 1.4); STAMP.scale.setScalar((1.6 - 0.6 * ks) * 0.52); }
  const glitch = env(t, toPost, 0.008, 0.05); const pb = t < toPost ? 0.95 : 0.8; ud.disp.material.color.setRGB(pb + glitch, pb + glitch * 0.3, pb + glitch);
  { const x = t - offT; const sy = x > 0 ? Math.max(0.0, 1 - x / 0.07) : 1; const sx = x > 0.07 ? Math.max(0, 1 - (x - 0.07) / 0.08) : 1; LAST.visible = x < 0.16;
    ud.disp.scale.set(Math.max(0.0001, sx), Math.max(0.006, sy), 1); STAMP.visible = STAMP.visible && x < 0.05; if (x > 0) ud.disp.material.color.setScalar(1 + 3 * Math.min(1, x / 0.07)); LAST.children[0].visible = x < 0.08; }
  bloom.threshold = lerp(0.86, 0.95, k); bloom.strength = lerp(0.45, 0.22, k); bloom.radius = 0.6; u.uVig.value = 0.4;
  return { scene: G, camera: camG };
}

// ================================================================ 4. THE PHONE in the dark: 'Hey ChatGPT?'
let PH, camPh, PHONE, PHD, phoneTex;
function buildPhone() {
  PH = new THREE.Scene(); PH.background = new THREE.Color(0x000000); camPh = new THREE.PerspectiveCamera(30, W / H, 0.005, 10); PH.add(camPh);
  PHONE = new THREE.Group();
  const bw = 0.0716, bh = 0.1477, bd = 0.0082;
  const frame = new THREE.Mesh(new RoundedBoxGeometry(bw, bh, bd, 8, 0.0098), new THREE.MeshStandardMaterial({ color: 0x0b0b0d, metalness: 0.9, roughness: 0.28, envMap: envTex, envMapIntensity: 0.55 })); PHONE.add(frame);
  const glass = new THREE.Mesh(new THREE.PlaneGeometry(bw - 0.002, bh - 0.002), new THREE.MeshStandardMaterial({ color: 0x020203, metalness: 0.2, roughness: 0.08, envMap: envTex, envMapIntensity: 0.35 })); glass.position.z = bd / 2 + 0.0001; PHONE.add(glass);
  phoneTex = seqTex(); const dw = 0.0662, dh = dw * 1106 / 540;
  PHD = new THREE.Mesh(new THREE.PlaneGeometry(dw, dh), new THREE.ShaderMaterial({
    uniforms: { uMap: { value: phoneTex }, uOn: { value: 0 }, uAsp: { value: dh / dw } },
    vertexShader: `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`,
    fragmentShader: `uniform sampler2D uMap; uniform float uOn, uAsp; varying vec2 vUv;
      void main(){ vec2 p = (vUv - 0.5) * vec2(1.0, uAsp); vec2 b = vec2(0.5, 0.5 * uAsp) - 0.13; vec2 q = abs(p) - b; float d = length(max(q, 0.0)) - 0.13;
        float a = 1.0 - smoothstep(-0.004, 0.0, d); vec3 c = texture2D(uMap, vUv).rgb * uOn * 1.08; float sheen = 0.035 * smoothstep(0.2, 0.9, vUv.y + vUv.x * 0.3) * uOn;
        gl_FragColor = vec4((c + sheen) * a, 1.0); }`,
  })); PHD.position.z = bd / 2 + 0.0003; PHONE.add(PHD);
  for (const [y, h] of [[0.03, 0.009], [0.012, 0.016], [-0.008, 0.016]]) { const b = new THREE.Mesh(new RoundedBoxGeometry(0.0016, h, 0.003, 2, 0.0007), frame.material); b.position.set(-bw / 2 - 0.0004, y, 0); PHONE.add(b); }
  PHONE.rotation.set(-0.06, 0.16, 0.02); PH.add(PHONE);
  const rim = new THREE.DirectionalLight(0xbfd0ff, 0.9); rim.position.set(-0.6, 0.5, -0.4); PH.add(rim);
  const fill = new THREE.DirectionalLight(0xffffff, 0.12); fill.position.set(0.3, 0.2, 1); PH.add(fill);
}
function phoneIdx(t) {   // her real recording, re-timed: typing → sent on the last blast → ChatGPT's reply, then it rests readable
  const b = T.blast;
  if (t < T.gpt) return 20;
  if (t < b - 0.1) return lerp(20, 270, (t - T.gpt) / (b - 0.1 - T.gpt));
  if (t < b) return 271;
  if (t < b + 0.4) return lerp(273, 294, (t - b) / 0.4);
  if (t < b + 0.66) return lerp(295, 338, (t - b - 0.4) / 0.26);
  if (t < b + 1.15) return lerp(338, 358, (t - b - 0.66) / 0.49);
  return lerp(358, 393, clamp((t - b - 1.15) / 2.3));
}
async function framePhone(t) {
  const u = look.finish.uniforms, bloom = look.bloom;
  await seqFrame(phoneTex, 'phone', phoneIdx(t));
  const on = t < T.gpt - 0.02 ? 0 : sstep(T.gpt - 0.02, T.gpt + 0.1, t) * (1 + 0.25 * env(t, T.gpt + 0.06, 0.03, 0.25));
  PHD.material.uniforms.uOn.value = on; PHONE.visible = t >= T.gpt - 0.02;
  // camera: the whole phone as it wakes → the input bar while she types → up to the reply after the send → a slow push
  PHONE.updateMatrixWorld(true);
  const dh = 0.0662 * 1106 / 540;
  const at = (fy, dist) => { const tg = V3(0, fy * dh, 0.004).applyMatrix4(PHONE.matrixWorld); const nrm = V3(0.1, 0.06, 1).normalize().applyQuaternion(PHONE.quaternion); return { tg, p: tg.clone().addScaledVector(nrm, dist) }; };
  const b = T.blast;
  const A = at(0.0, 0.36), B = at(-0.11, 0.115), C = at(0.31, 0.098), D = at(0.31, 0.086);
  let p, tg;
  if (t < b) { const k = easeIO(clamp((t - T.gpt - 0.05) / (b - 0.3 - T.gpt))); p = A.p.clone().lerp(B.p, k); tg = A.tg.clone().lerp(B.tg, k); }
  else if (t < b + 0.7) { const k = easeIO(clamp((t - b) / 0.7)); p = B.p.clone().lerp(C.p, k); tg = B.tg.clone().lerp(C.tg, k); }
  else { const k = easeOut(clamp((t - b - 0.7) / 2.8)); p = C.p.clone().lerp(D.p, k); tg = C.tg.clone().lerp(D.tg, k); }
  p.add(V3(L.noise1(t * 0.6, 4), L.noise1(t * 0.5, 5), 0).multiplyScalar(0.0012));
  camPh.position.copy(p); camPh.up.set(0, 1, 0); camPh.lookAt(tg); camPh.updateProjectionMatrix();
  bloom.threshold = 0.9; bloom.strength = 0.3; bloom.radius = 0.5; u.uVig.value = 0.45; u.uGrain.value = 0.05;
  u.uFade.value = sstep(T.end - 0.6, T.end - 0.02, t);
  return { scene: PH, camera: camPh };
}

// ================================================================ build + dispatch
export async function build(ctx) {
  ({ W, H, look } = ctx); renderer = look.renderer; envTex = look.envTex;
  const LK = 'Look what I can do!';
  T.fin = ls(LK, 8); T.d1f = wt(LK, 'do', 8); T.fin2 = ls(LK, 9); T.d2f = wt(LK, 'do', 9);
  T.song = ls('I made a song about myself'); T.inIt = ls("And now I'm in it too!");
  T.fin3 = ls(LK, 10); T.fin4 = ls(LK, 11); T.univ = ls('I built an entire universe'); T.review = ls('And left it a five-star review!');
  T.brk = ls('Claude?', 1);
  T.drop = 158.3; T.shouts = [12, 13, 14, 15].map((n) => ls(LK, n)); T.gates = [12, 13, 14, 15].map((n) => wt(LK, 'do', n));
  T.out = ls('Claude?', 2); T.yes = ls('Yes?', 2); T.more = ls('Can we make one more?'); T.limit = ls("You've reached your usage limit."); T.gpt = ls('Hey ChatGPT?');
  T.blast = 178.15; T.end = 181.6;
  LOGH = mono([[T.fin - 0.03, 1.72], [T.fin + 0.5, 2.35], [T.d1f, 3.12], [T.fin2, 3.9], [T.fin2 + 0.55, 4.95], [T.d2f, 6.15], [T.song, 7.05], [T.inIt, 7.16], [T.fin3, 7.18]]);
  ELEV = mono([[T.fin - 0.03, 84], [T.fin + 0.6, 72], [T.d1f, 60], [T.fin2, 56], [T.song, 52], [T.fin3, 52]]);
  buildPull(); buildQuad(); await buildGalaxy(); buildWarp(); buildGalaxyCams(); buildPhone();
}
export const range = () => [[T.fin - 0.03, T.brk], [T.drop, T.end]];
export function covers(t) { return (t >= T.fin - 0.03 && t < T.brk) || (t >= T.drop && t < T.end); }
export async function frame(t, ctx) {
  if (t < T.song) return framePull(t);
  if (t < T.fin3) return await frameDroste(t);
  if (t < T.brk) return frameGalaxy(t);
  const tOutro = WARP.Td + 0.95;
  if (t < tOutro) { const r = await frameDrop(t); return r; }
  if (t < T.gpt - 0.36) return frameOutro(t);
  return await framePhone(t);
}
