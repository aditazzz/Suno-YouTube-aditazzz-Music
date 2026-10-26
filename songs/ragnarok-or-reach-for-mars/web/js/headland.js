// The headland outside the hall's doors: the Fool card made real. A grassy plateau ending in a cliff, the sea below,
// Mars rising over the water (drawn in the cards' engraved style), stars and the Milky Way, and a ship of standing
// stones (after Ale's Stones) whose prow points at Mars.
import * as THREE from 'three';
import { clay, canvasTex, rng, clamp } from './lib.js';
import { noise2 } from './lib2.js';

const NOISE = `
float hash3(vec3 p){ p = fract(p * 0.3183099 + 0.1); p *= 17.0; return fract(p.x * p.y * p.z * (p.x + p.y + p.z)); }
float hash(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p){ vec2 i = floor(p), f = fract(p); vec2 u = f * f * (3.0 - 2.0 * f);
  return mix(mix(hash(i), hash(i + vec2(1, 0)), u.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), u.x), u.y); }
float fbm(vec2 p){ float s = 0.0, a = 0.5; for (int i = 0; i < 5; i++) { s += a * noise(p); p = p * 2.03 + 17.1; a *= 0.5; } return s; }`;

export const HEAD = { sea: -26, edgeZ: -28, marsAz: 0.0, marsEl: 0.085 };
export function marsDir() { return new THREE.Vector3(Math.sin(HEAD.marsAz) * Math.cos(HEAD.marsEl), Math.sin(HEAD.marsEl), -Math.cos(HEAD.marsAz) * Math.cos(HEAD.marsEl)); }

// ---------------------------------------------------------------- sky: gradient, stars, Milky Way, a warm bloom round Mars, faint aurora
function sky(md) {
  const mat = new THREE.ShaderMaterial({ side: THREE.BackSide, depthWrite: false, fog: false, uniforms: { uTime: { value: 0 }, uMars: { value: md }, uAur: { value: 0.6 } },
    vertexShader: 'varying vec3 vD; void main(){ vD = position; vec4 p = projectionMatrix * modelViewMatrix * vec4(position, 1.0); gl_Position = p.xyww; }',
    fragmentShader: `uniform float uTime, uAur; uniform vec3 uMars; varying vec3 vD; ${NOISE}
      void main(){ vec3 d = normalize(vD); float el = d.y;
        vec3 c = mix(vec3(0.05, 0.045, 0.1), vec3(0.006, 0.01, 0.03), smoothstep(-0.05, 0.55, el));
        float m = max(dot(d, uMars), 0.0); c += vec3(0.32, 0.09, 0.05) * pow(m, 40.0) * 0.45 + vec3(0.5, 0.16, 0.08) * pow(m, 300.0) * 0.5 + vec3(0.12, 0.04, 0.03) * pow(m, 6.0) * smoothstep(0.25, 0.0, el) * 0.5;
        vec3 n = normalize(vec3(0.42, 0.62, -0.66)); float band = exp(-pow(dot(d, n), 2.0) / 0.018);
        vec2 bp = vec2(atan(d.x, d.z) * 3.0, d.y * 5.0); float mw = band * (0.35 + 0.65 * fbm(bp * 2.5)) * (0.6 + 0.4 * fbm(bp * 9.0));
        c += vec3(0.11, 0.1, 0.13) * mw;
        vec3 sp = d * 300.0; vec3 id = floor(sp); float h = hash3(id); vec3 f = fract(sp) - 0.5 - (vec3(hash3(id + 3.1), hash3(id + 7.7), hash3(id + 1.9)) - 0.5) * 0.5;
        float dens = 0.983 - band * 0.02;
        float s = step(dens, h) * smoothstep(0.32, 0.0, length(f)) * (0.55 + 0.45 * sin(uTime * (1.5 + h * 3.0) + h * 80.0));
        float bright = pow(fract(h * 37.0), 3.0) * 2.4 + 0.5;
        c += vec3(0.9, 0.92, 1.0) * s * bright * smoothstep(-0.02, 0.12, el);
        float ax = atan(d.x, d.z); float aur = smoothstep(0.04, 0.3, el) * (1.0 - smoothstep(0.3, 0.75, el)) * smoothstep(1.0, 2.2, abs(ax));
        float cur = fbm(vec2(ax * 4.0 + uTime * 0.05, el * 2.0)) * fbm(vec2(ax * 11.0 - uTime * 0.08, 1.0));
        c += vec3(0.08, 0.5, 0.32) * aur * pow(cur, 2.0) * uAur;
        gl_FragColor = vec4(c, 1.0); }` });
  const m = new THREE.Mesh(new THREE.SphereGeometry(1000, 48, 24), mat); m.frustumCulled = false; m.renderOrder = -10; return m;
}

// ---------------------------------------------------------------- the sea: dark swell, sky reflection, Mars's glitter path
function sea(md) {
  const mat = new THREE.ShaderMaterial({ fog: false, uniforms: { uTime: { value: 0 }, uMars: { value: md }, uCam: { value: new THREE.Vector3() } },
    vertexShader: 'varying vec3 vW; void main(){ vec4 w = modelMatrix * vec4(position, 1.0); vW = w.xyz; gl_Position = projectionMatrix * viewMatrix * w; }',
    fragmentShader: `uniform float uTime; uniform vec3 uMars, uCam; varying vec3 vW; ${NOISE}
      void main(){ vec3 v = normalize(vW - uCam); float dist = length(vW - uCam);
        vec2 p = vW.xz * 0.06; float t = uTime;
        float e = 0.08; float hx = fbm(p + vec2(t * 0.05, t * 0.03)) - fbm(p + vec2(e, 0.0) + vec2(t * 0.05, t * 0.03));
        float hz = fbm(p * 1.7 - vec2(t * 0.04, 0.0)) - fbm(p * 1.7 + vec2(0.0, e) - vec2(t * 0.04, 0.0));
        float k = 1.0 / (1.0 + dist * 0.004);
        vec3 n = normalize(vec3(hx * 2.6 * k, 1.0, hz * 2.6 * k));
        vec3 r = reflect(v, n);
        float fres = 0.02 + 0.98 * pow(1.0 - max(dot(-v, n), 0.0), 5.0);
        vec3 skyc = mix(vec3(0.05, 0.045, 0.1), vec3(0.01, 0.015, 0.035), smoothstep(0.0, 0.5, r.y));
        float m = max(dot(r, uMars), 0.0);
        vec3 c = vec3(0.004, 0.009, 0.018) + skyc * fres * 1.4 + vec3(1.0, 0.36, 0.14) * (pow(m, 160.0) * 3.2 + pow(m, 22.0) * 0.12);
        float glint = step(0.993, hash(floor(vW.xz * 2.0) + floor(t * 3.0))) * pow(m, 6.0) * 2.0; c += vec3(1.0, 0.5, 0.25) * glint;
        float haze = 1.0 - exp(-dist * 0.0016); c = mix(c, vec3(0.05, 0.04, 0.09), haze * 0.85);
        gl_FragColor = vec4(c, 1.0); }` });
  const m = new THREE.Mesh(new THREE.PlaneGeometry(5000, 5000), mat); m.rotation.x = -Math.PI / 2; m.position.y = HEAD.sea; return m;
}

// ---------------------------------------------------------------- Mars, engraved like the cards (gold latitude lines on a red disc)
function marsTex() {
  const N = noise2(77);
  return canvasTex(1024, 1024, (g, w, h) => {
    const cx = w / 2, cy = h / 2, R = w * 0.42;
    const img = g.createImageData(w, h); const d = img.data;
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) { const dx = (x - cx) / R, dy = (y - cy) / R, r2 = dx * dx + dy * dy; const i = (y * w + x) * 4;
      if (r2 > 1) { d[i + 3] = 0; continue; }
      const z = Math.sqrt(1 - r2); const lon = Math.atan2(dx, z), lat = Math.asin(-dy);
      const f = N.fbm(lon * 2.2 + 3, lat * 2.6 + 1, 5), f2 = N.fbm(lon * 7 + 9, lat * 7, 3);
      let k = 0.62 + 0.55 * (f - 0.5) + 0.18 * (f2 - 0.5);
      const light = Math.max(0, 0.25 + 0.85 * (dx * -0.55 + -dy * 0.25 + z * 0.8));
      const cap = Math.max(0, (lat - 1.18) * 6); let rr = 196 * k, gg = 82 * k, bb = 44 * k;
      rr = rr + (240 - rr) * Math.min(1, cap); gg = gg + (220 - gg) * Math.min(1, cap); bb = bb + (205 - bb) * Math.min(1, cap);
      const limb = Math.pow(z, 0.35);
      d[i] = Math.min(255, rr * light * limb); d[i + 1] = Math.min(255, gg * light * limb); d[i + 2] = Math.min(255, bb * light * limb); d[i + 3] = 255; }
    g.putImageData(img, 0, 0);
    g.save(); g.beginPath(); g.arc(cx, cy, R, 0, Math.PI * 2); g.clip();
    for (let k = -8; k <= 8; k++) { const lat = k / 9 * Math.PI / 2, y = cy - Math.sin(lat) * R, hw = Math.cos(lat) * R;
      g.strokeStyle = `rgba(244,200,120,${0.22 + 0.08 * (k % 2 === 0)})`; g.lineWidth = 1.6; g.beginPath(); g.ellipse(cx, y, hw, hw * 0.06, 0, 0, Math.PI * 2); g.stroke(); }
    g.restore();
    g.strokeStyle = 'rgba(244,210,140,0.85)'; g.lineWidth = 3; g.beginPath(); g.arc(cx, cy, R, 0, Math.PI * 2); g.stroke();
  });
}
function glowTex() { return canvasTex(256, 256, (g, w, h) => { const gr = g.createRadialGradient(w / 2, h / 2, 0, w / 2, h / 2, w / 2); gr.addColorStop(0, 'rgba(255,140,80,0.35)'); gr.addColorStop(0.3, 'rgba(255,90,40,0.12)'); gr.addColorStop(0.65, 'rgba(160,40,20,0.03)'); gr.addColorStop(1, 'rgba(0,0,0,0)'); g.fillStyle = gr; g.fillRect(0, 0, w, h); }); }

// ---------------------------------------------------------------- land: a plateau with a ragged cliff edge, grass on the flats, rock on the faces
function edgeZ(x) { const N = EN || (EN = noise2(91)); return HEAD.edgeZ + 5 * (N.fbm(x * 0.02 + 4, 0.5, 4) - 0.5) + 0.02 * x * x * 0.1 - Math.max(0, -x - 6) * 0.9 + Math.max(0, x - 22) * 1.4; }
let EN = null;
function terrain() {
  const N = noise2(93), S = 220, seg = 220; const geo = new THREE.PlaneGeometry(S, S, seg, seg); geo.rotateX(-Math.PI / 2); geo.translate(-10, 0, -40);
  const p = geo.attributes.position; const col = new Float32Array(p.count * 3);
  for (let i = 0; i < p.count; i++) { const x = p.getX(i), z = p.getZ(i); const ez = edgeZ(x); const inland = z - ez;
    let y = 0.6 * (N.fbm(x * 0.05, z * 0.05, 4) - 0.5) + 0.04 * Math.max(0, inland) * (N.fbm(x * 0.01 + 7, z * 0.01, 3));
    if (inland < 0) y = -(HEAD.sea * -1 + 6) * Math.min(1, -inland / 2.2) + y - 3 * N.fbm(x * 0.2, z * 0.2, 3) * Math.min(1, -inland / 2.2);
    p.setY(i, y); }
  geo.computeVertexNormals(); const n = geo.attributes.normal;
  for (let i = 0; i < p.count; i++) { const up = n.getY(i), x = p.getX(i), z = p.getZ(i); const rock = 1 - THREE.MathUtils.smoothstep(up, 0.55, 0.85); const v = 0.8 + 0.4 * N(x * 0.3, z * 0.3);
    const gr = [0.13 * v, 0.16 * v, 0.1 * v], rk = [0.2 * v, 0.19 * v, 0.18 * v]; for (let k = 0; k < 3; k++) col[i * 3 + k] = gr[k] + (rk[k] - gr[k]) * rock; }
  geo.setAttribute('color', new THREE.BufferAttribute(col, 3));
  const tx = canvasTex(256, 256, (g, w, h) => { const R = rng(5); g.fillStyle = '#bdbdbd'; g.fillRect(0, 0, w, h); for (let i = 0; i < 5000; i++) { g.fillStyle = `rgba(${R() < 0.5 ? 255 : 60},${R() < 0.5 ? 255 : 60},${R() < 0.5 ? 220 : 60},${0.05 + R() * 0.08})`; g.fillRect(R() * w, R() * h, 1 + R() * 2, 1 + R() * 4); } }, { repeat: [60, 60] });
  const m = new THREE.Mesh(geo, clay(0xffffff, { vertexColors: true, map: tx, rimAmt: 0.0, flatShading: true })); m.receiveShadow = true; return m;
}

// ---------------------------------------------------------------- the stone ship: stones round a pointed ellipse, tallest at prow and stern
function stoneGeo(seed) {   // a weathered slab: a subdivided box, noised, with rounded shoulders and a blunt top
  const N = noise2(seed); const g = new THREE.BoxGeometry(1.0, 2, 0.72, 3, 6, 2); const p = g.attributes.position;
  for (let i = 0; i < p.count; i++) { let x = p.getX(i), y = p.getY(i), z = p.getZ(i);
    const sh = y > 0.4 ? 1 - 0.32 * Math.pow((y - 0.4) / 0.6, 2) : 1; x *= sh; z *= sh * (y > 0.7 ? 0.9 : 1);
    if (y > 0.9) y = 0.9 + (y - 0.9) * 0.5 - 0.12 * (Math.abs(x) + Math.abs(z));
    const k = 1 + 0.16 * (N(x * 1.7 + 5, y * 1.3 + z * 2) - 0.5) + 0.06 * (N(x * 5, y * 5 + z * 3) - 0.5); p.setXYZ(i, x * k, y, z * k); }
  g.computeVertexNormals(); return g;
}
export function stoneShip({ L = 34, W = 8, n = 46, seed = 11 } = {}) {
  const g = new THREE.Group(); const R = rng(seed);
  const rockT = canvasTex(256, 256, (c, w, h) => { const N = noise2(seed); const img = c.createImageData(w, h); const d = img.data;
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) { const v = 0.55 + 0.5 * (N.fbm(x / 30, y / 30, 5) - 0.5) + 0.15 * (N(x / 3, y / 3) - 0.5); const li = N.fbm(x / 14 + 9, y / 14, 3) > 0.62;
      const i = (y * w + x) * 4; d[i] = li ? 150 * v + 40 : 118 * v; d[i + 1] = li ? 150 * v + 30 : 116 * v; d[i + 2] = li ? 90 * v : 110 * v; d[i + 3] = 255; }
    c.putImageData(img, 0, 0); });
  const mat = clay(0xffffff, { map: rockT, flatShading: true });
  const stones = [];
  for (let i = 0; i < n; i++) { const u = i / n; const side = u < 0.5 ? 1 : -1; const s = u < 0.5 ? u * 2 : (u - 0.5) * 2;
    const z = -L / 2 + s * L; const x = side * W / 2 * Math.pow(Math.sin(Math.PI * s), 0.85);
    const end = Math.max(Math.pow(1 - s, 8), Math.pow(s, 8)); const hgt = 1.2 + 0.5 * R() + 0.6 * Math.max(Math.pow(1 - s, 2), Math.pow(s, 2)) + 1.4 * end;
    const st = new THREE.Mesh(stoneGeo(seed + i * 7), mat); st.scale.set(0.62 + R() * 0.22, hgt / 2, 0.7 + R() * 0.2); st.position.set(x, hgt / 2 - 0.25, z); st.rotation.set((R() - 0.5) * 0.12, Math.atan2(x, z) + (R() - 0.5) * 0.5, (R() - 0.5) * 0.12);
    st.castShadow = st.receiveShadow = true; g.add(st); stones.push(st); }
  g.userData.stones = stones; g.userData.L = L; return g;
}

export function buildHeadland(env) {
  const g = new THREE.Group(); const md = marsDir();
  const sk = sky(md); g.add(sk); const se = sea(md); g.add(se); const land = terrain(); g.add(land);
  const ship = stoneShip(); ship.position.set(0, 0, -5); g.add(ship);
  // Mars: an engraved disc with a halo, placed far out along marsDir
  const marsM = new THREE.MeshBasicMaterial({ map: marsTex(), transparent: true, fog: false, depthWrite: false }); marsM.color.setScalar(1.6);
  const mars = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), marsM); mars.renderOrder = -5; g.add(mars);
  const halo = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.MeshBasicMaterial({ map: glowTex(), transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, fog: false })); halo.renderOrder = -6; g.add(halo);
  // lights: moon from the upper left, Mars light low from ahead (it rims the stones), a cool sky fill
  const moon = new THREE.DirectionalLight(0x9db4e0, 1.25); moon.position.set(-30, 40, 10); moon.castShadow = true; moon.shadow.mapSize.set(2048, 2048); moon.shadow.camera.left = -25; moon.shadow.camera.right = 25; moon.shadow.camera.top = 25; moon.shadow.camera.bottom = -25; moon.shadow.camera.far = 120; moon.shadow.bias = -0.0008; g.add(moon); g.add(moon.target);
  const marsL = new THREE.DirectionalLight(0xff6a3a, 0.75); marsL.position.copy(md).multiplyScalar(60); g.add(marsL);
  const hemi = new THREE.HemisphereLight(0x2a3a66, 0x0a0806, 0.55); g.add(hemi);
  g.userData = { ship, mars, halo, moon, sky: sk, sea: se, marsDir: md,
    update(t, cam) { sk.material.uniforms.uTime.value = t; se.material.uniforms.uTime.value = t; se.material.uniforms.uCam.value.copy(cam.position);
      const D = 900, size = D * Math.tan(THREE.MathUtils.degToRad(4.2)); mars.position.copy(cam.position).addScaledVector(md, D); mars.lookAt(cam.position); mars.scale.setScalar(size * 2);
      halo.position.copy(cam.position).addScaledVector(md, D + 5); halo.lookAt(cam.position); halo.scale.setScalar(size * 4.2);
      sk.position.copy(cam.position); } };
  return g;
}
