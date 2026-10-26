// Fire: shader flames on camera-facing quads (HDR, so bloom makes them glow), a bed of embers, rising sparks.
// The sparks are the same particles the ember captions are made from, so the words come out of this fire.
import * as THREE from 'three';
import { rng } from './lib.js';

const NOISE = `
float hash(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p){ vec2 i = floor(p), f = fract(p); vec2 u = f * f * (3.0 - 2.0 * f);
  return mix(mix(hash(i), hash(i + vec2(1, 0)), u.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), u.x), u.y); }
float fbm(vec2 p){ float s = 0.0, a = 0.5; for (int i = 0; i < 5; i++) { s += a * noise(p); p = p * 2.03 + 17.1; a *= 0.5; } return s; }`;

const FLAME_VS = `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`;
const FLAME_FS = `uniform float uTime, uSeed, uGain, uLean; varying vec2 vUv; ${NOISE}
vec3 ramp(float h){ h = clamp(h, 0.0, 1.0);
  vec3 c = mix(vec3(0.25, 0.02, 0.0), vec3(0.85, 0.16, 0.02), smoothstep(0.0, 0.3, h));
  c = mix(c, vec3(1.0, 0.42, 0.06), smoothstep(0.25, 0.55, h)); c = mix(c, vec3(1.0, 0.66, 0.22), smoothstep(0.55, 0.85, h)); return mix(c, vec3(1.0, 0.84, 0.52), smoothstep(0.85, 1.0, h)); }
void main(){
  vec2 uv = vUv; float t = uTime * 1.15 + uSeed * 7.3;
  vec2 q = vec2((uv.x - 0.5) * 2.0 - uLean * uv.y * uv.y, uv.y);
  // turbulence advected upward; two scales
  float n1 = fbm(vec2(q.x * 1.8 + uSeed * 3.1, q.y * 2.4 - t * 1.9));
  float n2 = fbm(vec2(q.x * 4.2 - uSeed, q.y * 5.5 - t * 3.1));
  float turb = n1 * 0.62 + n2 * 0.38;
  // the body: widest just above the base, swaying more as it rises, licked away by the noise toward the tips
  float sway = (n1 - 0.5) * 0.55 * q.y;
  float w = 0.92 * (1.0 - pow(q.y, 0.8)) * (0.75 + 0.5 * smoothstep(0.0, 0.18, q.y));
  float d = abs(q.x + sway) / max(w, 0.02);
  float body = 1.0 - smoothstep(0.35, 1.0, d);
  float f = body * (1.12 - q.y) * 1.3 - turb * (0.55 + 0.7 * q.y);
  f = clamp(f * smoothstep(0.0, 0.07, q.y), 0.0, 1.0);
  float heat = pow(f, 1.15) * (1.0 - 0.35 * q.y);
  vec3 col = ramp(heat * 1.5) * uGain;
  float a = smoothstep(0.0, 0.28, f) * 0.95;
  gl_FragColor = vec4(col * a, a);
}`;

/** one flame quad: w x h metres, base at its origin; call .userData.update(t, camera) */
export function flame(w, h, seed = 1, gain = 2.2) {
  const geo = new THREE.PlaneGeometry(w, h); geo.translate(0, h / 2, 0);
  const mat = new THREE.ShaderMaterial({ vertexShader: FLAME_VS, fragmentShader: FLAME_FS, transparent: true, depthWrite: false, blending: THREE.NormalBlending, premultipliedAlpha: true, side: THREE.DoubleSide,
    uniforms: { uTime: { value: 0 }, uSeed: { value: seed }, uGain: { value: gain }, uLean: { value: 0 } } });
  const m = new THREE.Mesh(geo, mat); m.frustumCulled = false; m.renderOrder = 10; m.userData.gain = gain;
  m.userData.update = (t, cam) => { mat.uniforms.uTime.value = t; if (cam) { const p = m.parent ? m.parent.worldToLocal(cam.position.clone()) : cam.position; m.rotation.y = Math.atan2(p.x - m.position.x, p.z - m.position.z); } };
  return m;
}

const EMBER_FS = `uniform float uTime; varying vec2 vUv; ${NOISE}
void main(){ vec2 p = vUv * vec2(3.0, 18.0); float n = fbm(p + vec2(0.0, uTime * 0.15)); float n2 = fbm(p * 2.7 - vec2(uTime * 0.2, 0.0));
  float k = smoothstep(0.45, 0.85, n * 0.7 + n2 * 0.5); float pulse = 0.75 + 0.25 * sin(uTime * 3.0 + n * 20.0);
  vec3 c = mix(vec3(0.05, 0.02, 0.015), vec3(1.6, 0.42, 0.08), k * pulse) + vec3(2.2, 0.9, 0.3) * pow(k, 6.0);
  gl_FragColor = vec4(c, 1.0); }`;
/** a glowing bed of embers, w x d metres, lying flat */
export function emberBed(w, d) {
  const mat = new THREE.ShaderMaterial({ vertexShader: FLAME_VS, fragmentShader: EMBER_FS, uniforms: { uTime: { value: 0 } } });
  const m = new THREE.Mesh(new THREE.PlaneGeometry(w, d), mat); m.rotation.x = -Math.PI / 2; m.userData.update = (t) => { mat.uniforms.uTime.value = t; }; return m;
}

// ---------------------------------------------------------------- sparks: a fixed population that loops (deterministic in t)
const SPARK_VS = `attribute vec4 aSeed; uniform float uTime, uH, uSize, uScale; varying float vA, vHeat;
void main(){
  float life = 1.6 + aSeed.y * 2.6; float age = mod(uTime * (0.6 + aSeed.z * 0.6) + aSeed.x * life, life); float k = age / life;
  vec3 p = position;
  p.y += uH * (k * 1.15 - 0.15 * k * k) * (0.6 + aSeed.w * 0.8);
  p.x += sin(uTime * (1.3 + aSeed.z * 2.0) + aSeed.x * 40.0) * 0.18 * k + (aSeed.w - 0.5) * 0.5 * k;
  p.z += cos(uTime * (1.1 + aSeed.y * 1.7) + aSeed.w * 30.0) * 0.18 * k;
  vA = smoothstep(0.0, 0.06, k) * (1.0 - smoothstep(0.55, 1.0, k)) * (0.6 + 0.4 * sin(uTime * 23.0 + aSeed.x * 90.0)); vHeat = 1.0 - k;
  vec4 mv = modelViewMatrix * vec4(p, 1.0); gl_Position = projectionMatrix * mv;
  gl_PointSize = uSize * uScale / -mv.z * (0.5 + aSeed.y);
}`;
const SPARK_FS = `varying float vA, vHeat; void main(){ vec2 d = gl_PointCoord - 0.5; float r = length(d); float a = smoothstep(0.5, 0.0, r) * vA; if (a < 0.01) discard;
  vec3 c = mix(vec3(1.4, 0.35, 0.06), vec3(2.6, 1.6, 0.7), vHeat * vHeat); gl_FragColor = vec4(c * a, a); }`;
/** sparks rising from a w x d area, up to height h; .userData.update(t, H) where H is the frame height in px */
export function sparks(n, w, d, h, seed = 3, size = 0.035) {
  const R = rng(seed); const pos = new Float32Array(n * 3), sd = new Float32Array(n * 4);
  for (let i = 0; i < n; i++) { pos[i * 3] = (R() - 0.5) * w; pos[i * 3 + 1] = R() * 0.15; pos[i * 3 + 2] = (R() - 0.5) * d; for (let k = 0; k < 4; k++) sd[i * 4 + k] = R(); }
  const geo = new THREE.BufferGeometry(); geo.setAttribute('position', new THREE.BufferAttribute(pos, 3)); geo.setAttribute('aSeed', new THREE.BufferAttribute(sd, 4));
  const mat = new THREE.ShaderMaterial({ vertexShader: SPARK_VS, fragmentShader: SPARK_FS, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
    uniforms: { uTime: { value: 0 }, uH: { value: h }, uSize: { value: size }, uScale: { value: 450 } } });
  const p = new THREE.Points(geo, mat); p.frustumCulled = false; p.renderOrder = 12;
  p.userData.update = (t, H = 900, fov = 38) => { mat.uniforms.uTime.value = t; mat.uniforms.uScale.value = H / (2 * Math.tan(THREE.MathUtils.degToRad(fov) / 2)); };
  return p;
}

// sparks thrown up in bursts (a flare, a slam): each particle belongs to one burst time; deterministic in t
const BURST_VS = `attribute vec4 aSeed; attribute float aB; uniform float uTime, uSize, uScale, uH; uniform float uT[24]; varying float vA, vHeat;
void main(){ float age = uTime - uT[int(aB)]; float life = 1.0 + aSeed.y * 1.6; float k = clamp(age / life, 0.0, 1.0); float on = step(0.0, age) * step(age, life);
  vec3 p = position; float sp = 0.6 + aSeed.z * 1.4;
  p.y += uH * (1.0 - pow(1.0 - k, 2.0)) * sp; p.x += (aSeed.w - 0.5) * 1.2 * k + sin(uTime * 3.0 + aSeed.x * 40.0) * 0.12 * k; p.z += (aSeed.x - 0.5) * 1.6 * k;
  vA = on * (1.0 - smoothstep(0.45, 1.0, k)) * (0.6 + 0.4 * sin(uTime * 25.0 + aSeed.x * 80.0)); vHeat = 1.0 - k;
  vec4 mv = modelViewMatrix * vec4(p, 1.0); gl_Position = projectionMatrix * mv; gl_PointSize = uSize * uScale / -mv.z * (0.6 + aSeed.y); }`;
export function sparkBursts(times, perBurst, w, d, h, seed = 11, size = 0.04) {
  const R = rng(seed); const n = times.length * perBurst; const pos = new Float32Array(n * 3), sd = new Float32Array(n * 4), b = new Float32Array(n);
  for (let i = 0; i < n; i++) { pos[i * 3] = (R() - 0.5) * w; pos[i * 3 + 1] = R() * 0.2; pos[i * 3 + 2] = (R() - 0.5) * d; for (let k = 0; k < 4; k++) sd[i * 4 + k] = R(); b[i] = Math.floor(i / perBurst); }
  const geo = new THREE.BufferGeometry(); geo.setAttribute('position', new THREE.BufferAttribute(pos, 3)); geo.setAttribute('aSeed', new THREE.BufferAttribute(sd, 4)); geo.setAttribute('aB', new THREE.BufferAttribute(b, 1));
  const T = new Array(24).fill(-100); times.slice(0, 24).forEach((t, i) => { T[i] = t; });
  const mat = new THREE.ShaderMaterial({ vertexShader: BURST_VS, fragmentShader: SPARK_FS, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
    uniforms: { uTime: { value: 0 }, uT: { value: T }, uH: { value: h }, uSize: { value: size }, uScale: { value: 450 } } });
  const p = new THREE.Points(geo, mat); p.frustumCulled = false; p.renderOrder = 12;
  p.userData.update = (t, H = 900, fov = 38) => { mat.uniforms.uTime.value = t; mat.uniforms.uScale.value = H / (2 * Math.tan(THREE.MathUtils.degToRad(fov) / 2)); };
  return p;
}

/** a long hearth fire: an ember bed, a row of flames of varied size, sparks, and flickering lights */
export function hearthFire(len, wid, { lights = 3, intensity = 30, shadow = true, flames = 14, seed = 5 } = {}) {
  const g = new THREE.Group(); const R = rng(seed); const ups = [];
  const bed = emberBed(wid * 0.9, len * 0.94); bed.position.y = 0.06; g.add(bed); ups.push(bed);
  for (let i = 0; i < flames; i++) {
    const z = (i / (flames - 1) - 0.5) * len * 0.84 + (R() - 0.5) * 0.25, x = (R() - 0.5) * wid * 0.25;
    const big = 0.6 + 0.4 * Math.sin(i / (flames - 1) * Math.PI);
    const f = flame(0.75 + big * 0.35 + R() * 0.15, 0.75 + big * 0.75 + R() * 0.3, R() * 10, 0.85 + R() * 0.25); f.position.set(x, 0.02, z); g.add(f); ups.push(f);
  }
  const sp = sparks(700, wid * 0.7, len * 0.9, 5.5, seed + 9); sp.position.y = 0.2; g.add(sp); g.userData.sparks = sp;
  const L = [];
  for (let i = 0; i < lights; i++) { const z = lights === 1 ? 0 : (i / (lights - 1) - 0.5) * len * 0.7; const l = new THREE.PointLight(0xff8a3a, intensity / lights, 0, 2); l.position.set(0, 0.9, z);
    if (shadow && i === 0) { l.castShadow = true; l.shadow.mapSize.set(768, 768); l.shadow.bias = -0.004; l.shadow.normalBias = 0.02; l.shadow.radius = 4; l.shadow.camera.near = 0.2; l.shadow.camera.far = 30; }
    g.add(l); L.push(l); }
  g.userData.lights = L; g.userData.flare = 0; g.userData.bursts = null; g.userData.level = 1;   // level: 1 = a full fire, 0 = embers only
  g.userData.setBursts = (times) => { if (g.userData.bursts) g.remove(g.userData.bursts); const b = sparkBursts(times, 260, wid * 0.8, len * 0.85, 4.2, seed + 21); b.position.y = 0.2; g.add(b); g.userData.bursts = b; };
  g.userData.update = (t, cam, H, fov) => {
    const fl = g.userData.flare, lv = g.userData.level, sy = lv >= 1 ? 1 : 0.18 + 0.82 * lv, sg = lv >= 1 ? 1 : Math.sqrt(Math.max(0, lv));
    for (const u of ups) { u.userData.update(t, cam); if (u.userData.gain !== undefined) { u.material.uniforms.uGain.value = u.userData.gain * (1 + 0.9 * fl) * sg; u.scale.set((1 + 0.25 * fl) * (lv >= 1 ? 1 : 0.6 + 0.4 * lv), (1 + 0.7 * fl) * sy, 1); u.visible = lv > 0.04; } }
    sp.visible = lv > 0.25; sp.userData.update(t, H, fov); if (g.userData.bursts) g.userData.bursts.userData.update(t, H, fov);
    L.forEach((l, i) => { const f = 0.82 + 0.1 * Math.sin(t * 7.1 + i * 2.3) + 0.06 * Math.sin(t * 13.7 + i) + 0.05 * Math.sin(t * 3.3 + i * 5); l.intensity = intensity / lights * f * (1 + 0.45 * fl) * (lv >= 1 ? 1 : 0.06 + 0.94 * lv); l.position.x = 0.06 * Math.sin(t * 2.1 + i); });
  };
  return g;
}
