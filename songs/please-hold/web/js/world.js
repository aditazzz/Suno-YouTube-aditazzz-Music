// The city: a sky that runs from night to noon (and to neon), a toy-clean city of towers, the plaza with the bench and
// its lamp, and the HOLD tower: 25 x 36 real windows with rooms behind them, a robot on hold in any of them, an LED band
// around its base, and a facade that can turn into one giant screen. Everything that glows is unlit (bloom does the
// glow) and the background city is one instanced draw, so the CPU renderer stays fast.
import * as THREE from 'three';
import { clay, gloss, basic, glowMat, canvasTex, rbox, lathe, rng, dotTex, blobShadow, FONT, V3, clamp } from './lib.js';
import { bitmap } from './font5.js';

export const ENV = {                       // shared uniforms: time of day and moods, set every frame by the film
  day: { value: 0 }, warm: { value: 0 }, neon: { value: 0 }, stars: { value: 1 }, cloud: { value: 0 },
  sunDir: { value: new THREE.Vector3(0.3, 0.5, -0.8).normalize() }, fog: { value: new THREE.Color(0x0b1020) }, fogD: { value: 0.006 },
  lit: { value: 0.5 }, beat: { value: 0 }, time: { value: 0 }, dance: { value: 0 },
};
const GLSL_NOISE = `
float hash(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p){ vec2 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f);
  return mix(mix(hash(i), hash(i + vec2(1.0, 0.0)), f.x), mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), f.x), f.y); }
float fbm(vec2 p){ float v = 0.0, a = 0.5; for (int i = 0; i < 4; i++){ v += a * noise(p); p *= 2.03; a *= 0.5; } return v; }`;

// ---------------------------------------------------------------- sky
function makeSky() {
  return new THREE.Mesh(new THREE.SphereGeometry(1500, 48, 24), new THREE.ShaderMaterial({
    side: THREE.BackSide, depthWrite: false, fog: false,
    uniforms: { uDay: ENV.day, uWarm: ENV.warm, uNeon: ENV.neon, uStars: ENV.stars, uCloud: ENV.cloud, uSun: ENV.sunDir },
    vertexShader: `varying vec3 vP; void main(){ vP = position; vec4 p = projectionMatrix * modelViewMatrix * vec4(position, 1.0); gl_Position = p.xyww; }`,
    fragmentShader: `uniform float uDay, uWarm, uNeon, uStars, uCloud; uniform vec3 uSun; varying vec3 vP; ${GLSL_NOISE}
      void main(){ vec3 d = normalize(vP); float y = d.y;
        vec3 top = mix(vec3(0.006, 0.010, 0.032), vec3(0.16, 0.42, 0.95), uDay), hor = mix(vec3(0.035, 0.05, 0.12), vec3(0.62, 0.80, 0.97), uDay);
        top = mix(top, vec3(0.14, 0.17, 0.42), uWarm * 0.7); hor = mix(hor, vec3(1.0, 0.50, 0.28), uWarm);
        vec3 c = mix(hor, top, pow(smoothstep(-0.03, 0.62, y), 0.65));
        vec3 neon = mix(vec3(0.12, 0.02, 0.26), vec3(0.01, 0.0, 0.05), smoothstep(0.0, 0.5, y)) + vec3(0.0, 0.08, 0.12) * exp(-abs(y) * 9.0);
        c = mix(c, neon, uNeon);
        float s = max(dot(d, normalize(uSun)), 0.0);
        c += vec3(1.0, 0.86, 0.62) * smoothstep(0.9993, 0.9997, s) * 5.0 * max(uDay, uWarm * 0.8);
        c += mix(vec3(1.0, 0.55, 0.3), vec3(1.0, 0.95, 0.85), uDay) * pow(s, 10.0) * 0.45 * max(uDay, uWarm);
        if (y > 0.0) { vec2 uv = d.xz / (y + 0.14) * 1.1 + vec2(uCloud, uCloud * 0.35);
          float cl = smoothstep(0.52, 0.86, fbm(uv)); vec3 cc = mix(vec3(0.05, 0.06, 0.11), vec3(1.0, 1.0, 1.0), uDay); cc = mix(cc, vec3(1.0, 0.68, 0.55), uWarm * 0.7);
          cc = mix(cc, vec3(0.3, 0.05, 0.4), uNeon);
          c = mix(c, cc, cl * 0.8 * smoothstep(0.0, 0.12, y)); }
        vec2 sp = d.xz / (y + 0.35) * 260.0; float st = step(0.9965, hash(floor(sp))) * smoothstep(0.04, 0.35, y);
        c += vec3(0.9, 0.95, 1.0) * st * uStars * (0.6 + 0.4 * hash(floor(sp) + 3.1));
        gl_FragColor = vec4(c, 1.0); }`,
  }));
}

// ---------------------------------------------------------------- the background city: one instanced draw
function cityMaterial() {
  return new THREE.ShaderMaterial({
    uniforms: { uDay: ENV.day, uWarm: ENV.warm, uNeon: ENV.neon, uSun: ENV.sunDir, uFog: ENV.fog, uFogD: ENV.fogD, uLit: ENV.lit, uBeat: ENV.beat },
    vertexShader: `varying vec3 vN, vW, vO, vS, vC; varying float vSeed;
      void main(){ vec4 wp = modelMatrix * instanceMatrix * vec4(position, 1.0); vW = wp.xyz; vO = position;
        vS = vec3(length(instanceMatrix[0].xyz), length(instanceMatrix[1].xyz), length(instanceMatrix[2].xyz));
        vN = normalize(mat3(modelMatrix) * mat3(instanceMatrix) * normal); vC = instanceColor;
        vSeed = fract(instanceMatrix[3].x * 0.131 + instanceMatrix[3].z * 0.717);
        gl_Position = projectionMatrix * viewMatrix * wp; }`,
    fragmentShader: `uniform float uDay, uWarm, uNeon, uLit, uFogD, uBeat; uniform vec3 uSun, uFog; varying vec3 vN, vW, vO, vS, vC; varying float vSeed; ${GLSL_NOISE}
      void main(){ vec3 n = normalize(vN);
        float u = abs(n.x) > 0.5 ? vW.z : vW.x; float v = vW.y;
        vec2 cell = vec2(u / 2.4, v / 3.2); vec2 id = floor(cell); vec2 f = fract(cell);
        float isWin = step(0.2, f.x) * step(f.x, 0.8) * step(0.24, f.y) * step(f.y, 0.8) * step(3.5, v) * step(v, vS.y - 1.5) * (1.0 - step(0.5, abs(n.y)));
        float h = hash(id + vSeed * 17.0);
        float diff = max(dot(n, normalize(uSun)), 0.0);
        vec3 facade = vC * (0.5 + 0.65 * diff) + vec3(0.02);
        vec3 glass = mix(vec3(0.30, 0.45, 0.66), vec3(0.78, 0.88, 0.97), f.y) * (0.55 + 0.35 * diff);
        vec3 dayC = mix(facade, glass, isWin);
        if (abs(n.y) > 0.5) dayC = vC * 0.8;
        float lit = step(1.0 - uLit, h);
        vec3 warm = mix(vec3(1.0, 0.70, 0.40), vec3(0.62, 0.82, 1.0), step(0.82, hash(id * 1.7 + vSeed)));
        vec3 nightC = mix(vC * 0.045 + vec3(0.010, 0.012, 0.022), warm * (0.8 + 0.7 * h) * lit, isWin);
        vec3 c = mix(nightC, dayC, uDay);
        c = mix(c, c * vec3(1.15, 0.85, 0.72) + vec3(0.06, 0.02, 0.0) * diff, uWarm * 0.6);
        // neon: every building's edges light up, each in its own colour
        vec3 q = (0.5 - abs(vO)) * vS; float e = 0.16;
        float edge = max(max(step(q.x, e) * step(q.z, e), step(q.y, e) * step(q.x, e)), step(q.y, e) * step(q.z, e));
        vec3 nc = vSeed < 0.33 ? vec3(0.2, 1.0, 1.0) : (vSeed < 0.66 ? vec3(1.0, 0.45, 0.1) : vec3(0.65, 0.35, 1.0));
        c = mix(c, c * 0.5, uNeon * 0.6); c += nc * edge * uNeon * (2.2 + 1.2 * uBeat);
        float fg = 1.0 - exp(-uFogD * length(vW - cameraPosition)); c = mix(c, uFog, fg);
        gl_FragColor = vec4(c, 1.0); }`,
  });
}
function buildCity(R) {
  const list = []; const block = 24, street = 10;
  const pastel = [0xf2d7c6, 0xd9e6f2, 0xe8e2d4, 0xcfe3d8, 0xf0e1b8, 0xe3d3ec, 0xd5d9e0, 0xf4c9b8, 0xc8d8e8];
  for (let bx = -12; bx <= 12; bx++) for (let bz = -14; bz <= 8; bz++) {
    const cx = bx * (block + street), cz = bz * (block + street) - 20;
    if (Math.abs(cx) < 40 && cz > -75 && cz < 40) continue;                         // the plaza, the tower block, the near streets
    const n = 1 + (R() * 3 | 0);
    for (let i = 0; i < n; i++) {
      const w = 7 + R() * 10, d = 7 + R() * 10; const near = Math.hypot(cx, cz + 20) < 150;
      const h = 9 + Math.pow(R(), 1.5) * (near ? 70 : 45);
      list.push([cx + (R() - 0.5) * (block - w), h, cz + (R() - 0.5) * (block - d), w, d, pastel[(R() * pastel.length) | 0]]);
    }
  }
  const im = new THREE.InstancedMesh(new THREE.BoxGeometry(1, 1, 1), cityMaterial(), list.length);
  const m4 = new THREE.Matrix4(), col = new THREE.Color();
  list.forEach(([x, h, z, w, d, c], i) => { m4.compose(V3(x, h / 2, z), new THREE.Quaternion(), V3(w, h, d)); im.setMatrixAt(i, m4); im.setColorAt(i, col.setHex(c)); });
  im.frustumCulled = false; return im;
}

// ---------------------------------------------------------------- the plaza
export const PLAZA = { x0: -22, x1: 22, z0: -30, z1: 16 };
export const BENCH = V3(0, 0, 0);                  // bench centre; the seat faces +z
export const SEAT_Y = 0.46;
function plazaFloor() {
  const w = PLAZA.x1 - PLAZA.x0, d = PLAZA.z1 - PLAZA.z0;
  const g = new THREE.PlaneGeometry(w, d); g.rotateX(-Math.PI / 2); g.translate((PLAZA.x0 + PLAZA.x1) / 2, 0, (PLAZA.z0 + PLAZA.z1) / 2);
  return new THREE.Mesh(g, new THREE.ShaderMaterial({
    uniforms: { uDay: ENV.day, uWarm: ENV.warm, uNeon: ENV.neon, uDance: ENV.dance, uBeat: ENV.beat, uTime: ENV.time, uSun: ENV.sunDir, uFog: ENV.fog, uFogD: ENV.fogD,
      uLamp: { value: 1 }, uLampPos: { value: V3(-1.75, 0, -0.45) } },
    vertexShader: `varying vec3 vW; void main(){ vec4 wp = modelMatrix * vec4(position, 1.0); vW = wp.xyz; gl_Position = projectionMatrix * viewMatrix * wp; }`,
    fragmentShader: `uniform float uDay, uWarm, uNeon, uDance, uBeat, uTime, uLamp, uFogD; uniform vec3 uSun, uFog, uLampPos; varying vec3 vW; ${GLSL_NOISE}
      void main(){ vec2 p = vW.xz; vec2 cell = p / 1.5; vec2 id = floor(cell); vec2 f = fract(cell);
        float grout = 1.0 - (smoothstep(0.0, 0.025, f.x) * smoothstep(1.0, 0.975, f.x) * smoothstep(0.0, 0.025, f.y) * smoothstep(1.0, 0.975, f.y));
        float h = hash(id);
        vec3 tile = mix(vec3(0.62, 0.60, 0.57), vec3(0.70, 0.68, 0.64), h);
        if (mod(id.x + id.y, 7.0) < 0.5) tile *= vec3(0.92, 0.86, 0.80);
        vec3 dayC = tile * (0.62 + 0.42 * max(uSun.y, 0.0)) * (1.0 - grout * 0.28);
        vec3 nightC = vec3(0.034, 0.038, 0.05) * (0.8 + 0.4 * h) * (1.0 - grout * 0.3);
        float r = length(p - uLampPos.xz); nightC += vec3(1.0, 0.68, 0.38) * 0.42 * exp(-r * r / 9.0) * uLamp;
        vec3 c = mix(nightC, dayC, uDay); c = mix(c, c * vec3(1.15, 0.86, 0.7), uWarm * 0.5);
        // neon: a dance floor, tiles lighting on the beat
        float on = step(0.55, hash(id + floor(uTime * 2.0) * 1.37)) * (0.5 + 0.5 * uBeat);
        vec3 nc = mix(mix(vec3(0.2, 1.0, 1.0), vec3(1.0, 0.45, 0.1), step(0.5, hash(id * 3.1))), vec3(0.6, 0.3, 1.0), step(0.8, hash(id * 5.7)));
        c = mix(c, c * 0.45, uNeon) + nc * on * uDance * 0.55 * (1.0 - grout) + nc * grout * uNeon * 0.35;
        float fg = 1.0 - exp(-uFogD * length(vW - cameraPosition)); c = mix(c, uFog, fg);
        gl_FragColor = vec4(c, 1.0); }`,
  }));
}
export class Bench {
  constructor() {
    const g = this.root = new THREE.Group();
    const wood = clay(0xb87a4b, { rimAmt: 0.2 }), metal = gloss(0x1c1d22, { shininess: 40, rimAmt: 0.25 });
    for (let i = 0; i < 4; i++) { const s = new THREE.Mesh(rbox(1.9, 0.035, 0.1, 0.015), wood); s.position.set(0, SEAT_Y, -0.2 + i * 0.12); g.add(s); }
    for (let i = 0; i < 3; i++) { const s = new THREE.Mesh(rbox(1.9, 0.09, 0.03, 0.012), wood); s.position.set(0, SEAT_Y + 0.17 + i * 0.12, -0.33 - i * 0.025); s.rotation.x = -0.18; g.add(s); }
    for (const x of [-0.82, 0.82]) {
      const leg = new THREE.Mesh(rbox(0.05, SEAT_Y, 0.42, 0.02), metal); leg.position.set(x, SEAT_Y / 2, -0.06); g.add(leg);
      const arm = new THREE.Mesh(rbox(0.05, 0.05, 0.46, 0.02), metal); arm.position.set(x * 1.02, SEAT_Y + 0.2, -0.06); g.add(arm);
      const up = new THREE.Mesh(rbox(0.05, 0.62, 0.05, 0.02), metal); up.position.set(x, SEAT_Y + 0.12, -0.36); up.rotation.x = -0.18; g.add(up);
    }
    const sh = blobShadow(2.4, 0.9, 0.45); sh.position.y = 0.012; g.add(sh);
  }
}
function lampPost() {
  const g = new THREE.Group(); const metal = gloss(0x1f2026, { shininess: 50, rimAmt: 0.25 });
  const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.07, 3.7, 16), metal); pole.position.y = 1.85; g.add(pole);
  const base = new THREE.Mesh(new THREE.CylinderGeometry(0.14, 0.17, 0.3, 20), metal); base.position.y = 0.15; g.add(base);
  const arm = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.03, 0.55, 10), metal); arm.rotation.z = Math.PI / 2; arm.position.set(0.25, 3.7, 0); g.add(arm);
  const bulbMat = glowMat(new THREE.Color(1.0, 0.82, 0.55)); const globe = new THREE.Mesh(new THREE.SphereGeometry(0.2, 24, 16), bulbMat); globe.position.set(0.5, 3.55, 0); g.add(globe);
  const cap = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.24, 0.12, 24), metal); cap.position.set(0.5, 3.76, 0); g.add(cap);
  const halo = new THREE.Sprite(new THREE.SpriteMaterial({ map: dotTex(), color: 0xffc27a, transparent: true, opacity: 0.45, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false }));
  halo.scale.setScalar(1.5); halo.position.copy(globe.position); g.add(halo);
  g.userData = { bulbMat, halo, bulbPos: V3(0.5, 3.55, 0) }; return g;
}
function tree(R, s = 1) {
  const g = new THREE.Group(); const leaf = clay(0x6fae6a, { rimAmt: 0.3 }), leaf2 = clay(0x4f9a63, { rimAmt: 0.3 });
  const planter = new THREE.Mesh(rbox(1.5, 0.6, 1.5, 0.12), clay(0xd8d2c8, { rimAmt: 0.15 })); planter.position.y = 0.3; g.add(planter);
  const soil = new THREE.Mesh(new THREE.BoxGeometry(1.3, 0.02, 1.3), clay(0x3b2c22)); soil.position.y = 0.6; g.add(soil);
  const trunk = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.11, 1.6, 10), clay(0x7a5a40)); trunk.position.y = 1.35; g.add(trunk);
  for (let i = 0; i < 4; i++) { const b = new THREE.Mesh(new THREE.SphereGeometry(0.55 + R() * 0.25, 20, 14), i % 2 ? leaf : leaf2); b.position.set((R() - 0.5) * 0.7, 2.3 + R() * 0.6, (R() - 0.5) * 0.7); g.add(b); }
  g.scale.setScalar(s); return g;
}

// ---------------------------------------------------------------- the HOLD tower
export const TOWER = { cols: 25, rows: 36, cw: 1.44, rh: 1.5, x: 0, zf: -33, depth: 18, base: 10, top: 0 };
TOWER.w = TOWER.cols * TOWER.cw; TOWER.top = TOWER.base + TOWER.rows * TOWER.rh + 2.5; TOWER.zc = TOWER.zf - TOWER.depth / 2;
export function winCenter(c, r) {                   // column 0 = left, row 0 = top floor
  return V3(TOWER.x - TOWER.w / 2 + (c + 0.5) * TOWER.cw, TOWER.base + (TOWER.rows - r - 0.5) * TOWER.rh, TOWER.zf);
}
const WIN_W = 1.08, WIN_H = 1.12, ROOM_D = 1.1;
function facadeMaterial(winTex, screen) {
  return new THREE.ShaderMaterial({
    uniforms: { uDay: ENV.day, uWarm: ENV.warm, uNeon: ENV.neon, uBeat: ENV.beat, uSun: ENV.sunDir, uFog: ENV.fog, uFogD: ENV.fogD,
      uWin: { value: winTex }, uScreen: { value: screen }, uScreenAmt: { value: 0 }, uScreenGain: { value: 1.4 } },
    vertexShader: `varying vec3 vN, vW; void main(){ vec4 wp = modelMatrix * vec4(position, 1.0); vW = wp.xyz; vN = normalize(mat3(modelMatrix) * normal); gl_Position = projectionMatrix * viewMatrix * wp; }`,
    fragmentShader: `uniform float uDay, uWarm, uNeon, uBeat, uFogD, uScreenAmt, uScreenGain; uniform vec3 uSun, uFog; uniform sampler2D uWin, uScreen; varying vec3 vN, vW;
      void main(){ vec3 n = normalize(vN);
        float W = ${TOWER.w.toFixed(3)}, X0 = ${(TOWER.x - TOWER.w / 2).toFixed(3)}, Y0 = ${TOWER.base.toFixed(3)}, RH = ${TOWER.rh.toFixed(3)}, CW = ${TOWER.cw.toFixed(3)};
        float front = step(0.5, n.z);
        float u = abs(n.x) > 0.5 ? vW.z : vW.x; float v = vW.y;
        vec2 cell = vec2((vW.x - X0) / CW, (v - Y0) / RH); vec2 id = floor(cell); vec2 f = fract(cell);
        float inGrid = step(0.0, cell.x) * step(cell.x, ${TOWER.cols.toFixed(1)}) * step(0.0, cell.y) * step(cell.y, ${TOWER.rows.toFixed(1)});
        float hw = ${(WIN_W / TOWER.cw / 2).toFixed(4)}, hh = ${(WIN_H / TOWER.rh / 2).toFixed(4)};
        float isWin = step(abs(f.x - 0.5), hw) * step(abs(f.y - 0.5), hh) * inGrid;
        vec2 suv = vec2((vW.x - X0) / W, (v - Y0) / (${TOWER.rows.toFixed(1)} * RH));
        vec3 scr = texture2D(uScreen, suv).rgb * uScreenGain;
        if (front > 0.5 && isWin > 0.5 && uScreenAmt < 0.01) discard;                  // see into the rooms
        float diff = max(dot(n, normalize(uSun)), 0.0);
        vec3 conc = vec3(0.86, 0.84, 0.80) * (0.5 + 0.6 * diff);
        // side faces: painted windows
        vec2 sc = vec2(u / ${TOWER.cw.toFixed(3)}, (v - Y0) / RH); vec2 sf = fract(sc);
        float sw = (1.0 - front) * step(0.12, sf.x) * step(sf.x, 0.88) * step(0.13, sf.y) * step(sf.y, 0.87) * step(Y0, v) * step(v, Y0 + ${(TOWER.rows * TOWER.rh).toFixed(2)}) * (1.0 - step(0.5, abs(n.y)));
        vec3 dayC = mix(conc, vec3(0.42, 0.56, 0.74) * (0.6 + 0.3 * diff), sw);
        vec3 nightC = mix(vec3(0.028, 0.03, 0.04), vec3(1.0, 0.75, 0.45) * 0.55 * step(0.6, fract(sin(dot(floor(sc), vec2(12.9898, 78.233))) * 43758.5453)), sw);
        vec3 c = mix(nightC, dayC, uDay); c = mix(c, c * vec3(1.12, 0.86, 0.72), uWarm * 0.5);
        c = mix(c, c * 0.35, uNeon * 0.7);
        // neon outline of the tower's edges
        vec3 ed = vec3(min(abs(vW.x - X0), abs(vW.x - X0 - W)), min(abs(v), abs(v - ${TOWER.top.toFixed(2)})), min(abs(vW.z - ${TOWER.zf.toFixed(2)}), abs(vW.z - ${(TOWER.zf - TOWER.depth).toFixed(2)})));
        float e = 0.22; float edge = max(max(step(ed.x, e) * step(ed.z, e), step(ed.y, e) * step(ed.x, e)), step(ed.y, e) * step(ed.z, e));
        c += vec3(0.2, 1.0, 1.0) * edge * uNeon * (2.6 + 1.5 * uBeat);
        // the giant screen: the whole front, windows and walls alike
        c = mix(c, scr * (isWin > 0.5 ? 1.0 : 0.82), front * uScreenAmt * inGrid);
        float fg = 1.0 - exp(-uFogD * length(vW - cameraPosition)); c = mix(c, uFog, fg);
        gl_FragColor = vec4(c, 1.0); }`,
  });
}
// the LED band: a dot-matrix display reading a bitmap of the current message (scrolls, flips, blinks)
const LED_ROWS = 9;
function ledMaterial(bmpTex) {
  return new THREE.ShaderMaterial({
    uniforms: { uBmp: bmpTex ? { value: bmpTex } : { value: null }, uCols: { value: 118 }, uScroll: { value: 0 }, uBW: { value: 1 }, uOn: { value: new THREE.Color(1.0, 0.55, 0.12) },
      uOff: { value: new THREE.Color(0.03, 0.035, 0.045) }, uGain: { value: 2.4 }, uFlip: { value: 0 }, uFog: ENV.fog, uFogD: ENV.fogD, uFull: { value: 0 } },
    vertexShader: `varying vec2 vUv; varying vec3 vW; void main(){ vUv = uv; vec4 wp = modelMatrix * vec4(position, 1.0); vW = wp.xyz; gl_Position = projectionMatrix * viewMatrix * wp; }`,
    fragmentShader: `uniform sampler2D uBmp; uniform float uCols, uScroll, uBW, uGain, uFlip, uFogD, uFull; uniform vec3 uOn, uOff, uFog; varying vec2 vUv; varying vec3 vW;
      void main(){ vec2 g = vec2(vUv.x * uCols, (1.0 - vUv.y) * ${LED_ROWS.toFixed(1)}); vec2 id = floor(g); vec2 f = fract(g) - 0.5;
        float col = id.x + uScroll; float row = id.y - 1.0;
        float on = 0.0;
        if (row >= 0.0 && row < 7.0 && col >= 0.0 && col < uBW) on = texture2D(uBmp, vec2((col + 0.5) / uBW, (row + 0.5) / 7.0)).r;
        on = max(on, uFull);
        float flip = 1.0 - uFlip * step(abs(fract(id.x * 0.0 + 0.5) - 0.5), 1.0) * 0.0;
        float dot = smoothstep(0.42, 0.30, length(f));
        vec3 c = mix(uOff, uOn * uGain, on) * dot + uOff * 0.4 * (1.0 - dot);
        float fg = 1.0 - exp(-uFogD * length(vW - cameraPosition)); c = mix(c, uFog, fg * 0.6);
        gl_FragColor = vec4(c, 1.0); }`,
  });
}
export class Led {
  constructor(width, height) {
    this.cols = Math.round(width / (height / LED_ROWS));
    this.bmpW = 512; this.data = new Uint8Array(this.bmpW * 7 * 4); this.tex = new THREE.DataTexture(this.data, this.bmpW, 7, THREE.RGBAFormat);
    this.tex.magFilter = this.tex.minFilter = THREE.NearestFilter; this.tex.needsUpdate = true;
    this.mat = ledMaterial(this.tex); this.mat.uniforms.uCols.value = this.cols; this.mat.uniforms.uBW.value = this.bmpW;
    this.text = null; this.w = 0;
  }
  /** show text; align: 'center' | 'left' | scroll offset in dots (number) */
  set(text, { color = null, scroll = null, gain = null } = {}) {
    if (text !== this.text) {
      this.text = text; const rows = bitmap(text); this.w = rows[0].length; this.data.fill(0);
      for (let r = 0; r < 7; r++) for (let c = 0; c < Math.min(this.w, this.bmpW); c++) if (rows[r][c]) { const k = (r * this.bmpW + c) * 4; this.data[k] = this.data[k + 1] = this.data[k + 2] = this.data[k + 3] = 255; }
      this.tex.needsUpdate = true;
    }
    const u = this.mat.uniforms;
    u.uScroll.value = scroll === null ? Math.round((this.w - this.cols) / 2) : Math.round(scroll);
    if (color) u.uOn.value.set(color); if (gain !== null) u.uGain.value = gain;
  }
}
function towerScreenTex() { return canvasTex(1024, 1536); }

export class Tower {
  constructor() {
    const g = this.root = new THREE.Group(); const T = TOWER;
    this.state = new Float32Array(T.cols * T.rows * 4);        // r, g, b, on   (row 0 = top)
    this.winData = new Uint8Array(T.cols * T.rows * 4);
    this.winTex = new THREE.DataTexture(this.winData, T.cols, T.rows, THREE.RGBAFormat); this.winTex.needsUpdate = true;
    this.screen = towerScreenTex();
    const body = new THREE.Mesh(new THREE.BoxGeometry(T.w + 0.6, T.top, T.depth), facadeMaterial(this.winTex, this.screen));
    body.position.set(T.x, T.top / 2, T.zc); g.add(body); this.body = body;
    // rooms behind the windows: open-front boxes, unlit, coloured per window (ceiling light baked as a gradient)
    const rg = new THREE.BoxGeometry(WIN_W + 0.02, WIN_H + 0.02, ROOM_D); const idx = [];                // drop the +z face (open front)
    const keep = (rg.groups || []).filter((gr) => gr.materialIndex !== 4); for (const gr of keep) for (let i = 0; i < gr.count; i++) idx.push(rg.index.array[gr.start + i]);
    rg.setIndex(idx); rg.clearGroups(); rg.translate(0, 0, -ROOM_D / 2 - 0.02);
    const shade = new Float32Array(rg.attributes.position.count);                                          // floor dark, ceiling bright, back wall mid
    for (let i = 0; i < shade.length; i++) { const y = rg.attributes.position.getY(i), z = rg.attributes.position.getZ(i); shade[i] = 0.45 + 0.55 * (y / WIN_H + 0.5) - 0.15 * (z < -ROOM_D * 0.9 ? 0 : 1); }
    rg.setAttribute('shade', new THREE.BufferAttribute(shade, 1));
    const roomMat = new THREE.ShaderMaterial({ uniforms: { uFog: ENV.fog, uFogD: ENV.fogD, uDay: ENV.day },
      vertexShader: `attribute float shade; varying float vS; varying vec3 vC, vW; void main(){ vS = shade; vC = instanceColor; vec4 wp = modelMatrix * instanceMatrix * vec4(position, 1.0); vW = wp.xyz; gl_Position = projectionMatrix * viewMatrix * wp; }`,
      fragmentShader: `uniform vec3 uFog; uniform float uFogD, uDay; varying float vS; varying vec3 vC, vW; void main(){ vec3 c = vC * vS; float fg = 1.0 - exp(-uFogD * length(vW - cameraPosition)); gl_FragColor = vec4(mix(c, uFog, fg), 1.0); }` });
    this.rooms = new THREE.InstancedMesh(rg, roomMat, T.cols * T.rows); const m4 = new THREE.Matrix4();
    for (let r = 0; r < T.rows; r++) for (let c = 0; c < T.cols; c++) { const p = winCenter(c, r); m4.makeTranslation(p.x, p.y, p.z); this.rooms.setMatrixAt(r * T.cols + c, m4); this.rooms.setColorAt(r * T.cols + c, new THREE.Color(0.05, 0.05, 0.06)); }
    this.rooms.frustumCulled = false; g.add(this.rooms);
    // glass over the front (reflects the sky by day, nearly clear at night)
    const glassTex = canvasTex(64, 256, (gg, w, h) => { const gr = gg.createLinearGradient(0, 0, 0, h); gr.addColorStop(0, '#dfeefa'); gr.addColorStop(0.5, '#9fc0dc'); gr.addColorStop(1, '#6f8fae'); gg.fillStyle = gr; gg.fillRect(0, 0, w, h); });
    this.glass = new THREE.Mesh(new THREE.PlaneGeometry(T.w, T.rows * T.rh), new THREE.MeshBasicMaterial({ map: glassTex, transparent: true, opacity: 0.0, depthWrite: false }));
    this.glass.position.set(T.x, T.base + T.rows * T.rh / 2, T.zf + 0.03); g.add(this.glass);
    // window robots: busts on hold (instanced parts), placed by setRobots()
    const N = 120; this.maxBots = N;
    const enamel = gloss(0xe9ecef, { shininess: 70, rimAmt: 0.3 }), glassM = gloss(0x0a0b0e, { shininess: 120, specular: 0x9aa0aa, rimAmt: 0.2 });
    const eye = glowMat(new THREE.Color(0.35, 1.6, 1.9)), phone = gloss(0x141418, { shininess: 80 });
    const head = new THREE.SphereGeometry(0.2, 18, 14); head.scale(1, 1.15, 1); head.translate(0, 0.28, 0);
    const face = new THREE.SphereGeometry(0.205, 18, 14, -Math.PI * 0.36, Math.PI * 0.72, Math.PI * 0.22, Math.PI * 0.5); face.scale(1, 1.15, 1); face.translate(0, 0.28, 0.002);
    const eyeG = new THREE.BoxGeometry(0.2, 0.035, 0.02); eyeG.translate(0, 0.31, 0.2);
    const sh = new THREE.CapsuleGeometry(0.17, 0.2, 6, 16); sh.rotateZ(Math.PI / 2); sh.scale(1, 0.9, 0.75); sh.translate(0, -0.02, 0);
    const rec = new THREE.CapsuleGeometry(0.035, 0.2, 4, 10); rec.rotateZ(0.25); rec.translate(-0.22, 0.27, 0.06);
    this.bot = [[head, enamel], [face, glassM], [eyeG, eye], [sh, enamel], [rec, phone]].map(([geo, mat]) => { const im = new THREE.InstancedMesh(geo, mat, N); im.count = 0; im.frustumCulled = false; g.add(im); return im; });
    // the LED band around the base
    this.led = new Led(T.w, 2.6);
    const band = new THREE.Mesh(new THREE.PlaneGeometry(T.w, 2.6), this.led.mat); band.position.set(T.x, 7.6, T.zf + 0.35); g.add(band); this.band = band;
    const frame = new THREE.Mesh(rbox(T.w + 0.8, 3.1, 0.5, 0.1), gloss(0x17181d, { shininess: 30 })); frame.position.set(T.x, 7.6, T.zf + 0.08); g.add(frame);
    // lobby: dark glass and a canopy
    const lobby = new THREE.Mesh(new THREE.PlaneGeometry(T.w - 2, 5.2), gloss(0x0d1420, { shininess: 90, specular: 0x334455 })); lobby.position.set(T.x, 2.7, T.zf + 0.04); g.add(lobby);
    this.lobby = lobby;
    const canopy = new THREE.Mesh(rbox(10, 0.25, 3, 0.08), gloss(0x1b1c21)); canopy.position.set(T.x, 5.4, T.zf + 1.5); g.add(canopy);
    // roof: an antenna with a blinking light
    const ant = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.12, 9, 8), gloss(0x2a2b30)); ant.position.set(T.x + 8, T.top + 4.5, T.zc); g.add(ant);
    this.beacon = new THREE.Mesh(new THREE.SphereGeometry(0.35, 12, 8), glowMat(new THREE.Color(3, 0.3, 0.2))); this.beacon.position.set(T.x + 8, T.top + 9.1, T.zc); g.add(this.beacon);
    this.setAll(null);
  }
  idx(c, r) { return r * TOWER.cols + c; }
  /** fn(c, r) -> [r, g, b] colour of a lit room, or null for dark; called once per frame when the look changes */
  setAll(fn, key = null) {
    if (key !== null && key === this._key) return; this._key = key;
    const T = TOWER, col = new THREE.Color();
    for (let r = 0; r < T.rows; r++) for (let c = 0; c < T.cols; c++) {
      const v = fn ? fn(c, r) : null; const i = this.idx(c, r);
      if (v) col.setRGB(v[0], v[1], v[2]); else col.setRGB(0.035, 0.037, 0.045);
      this.rooms.setColorAt(i, col);
    }
    this.rooms.instanceColor.needsUpdate = true;
  }
  /** robots in windows: list of [c, r, s (scale 0..1), tilt, eyeColor?] */
  setRobots(list) {
    const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), e = new THREE.Euler(); let n = 0;
    for (const [c, r, s, tilt = 0] of list) { if (n >= this.maxBots || s <= 0.001) continue; const p = winCenter(c, r); p.y -= WIN_H * 0.5 - 0.02; p.z -= 0.45;
      e.set(0.12, 0, tilt); q.setFromEuler(e); m4.compose(p, q, V3(s * 1.15, s * 1.15, s * 1.15)); for (const im of this.bot) im.setMatrixAt(n, m4); n++; }
    for (const im of this.bot) { im.count = n; im.instanceMatrix.needsUpdate = true; }
  }
}

// ---------------------------------------------------------------- street furniture and kiosks
function stripes(c1, c2, n = 8) { return canvasTex(256, 64, (g, w, h) => { for (let i = 0; i < n; i++) { g.fillStyle = i % 2 ? c2 : c1; g.fillRect(i * w / n, 0, w / n + 1, h); } }); }
export function takeoutKiosk() {
  const g = new THREE.Group();
  const wall = clay(0xe9e1d3, { rimAmt: 0.15 }), red = clay(0xc8322b, { rimAmt: 0.2 }), dark = clay(0x2a2a30);
  const body = new THREE.Mesh(rbox(3.2, 2.7, 2.2, 0.1), wall); body.position.y = 1.35; g.add(body);
  const hole = new THREE.Mesh(new THREE.BoxGeometry(2.0, 1.0, 0.1), basic(0x1a1210)); hole.position.set(0, 1.55, 1.07); g.add(hole);
  const inside = new THREE.Mesh(new THREE.PlaneGeometry(1.96, 0.96), glowMat(new THREE.Color(1.0, 0.72, 0.42))); inside.position.set(0, 1.55, 1.0); g.add(inside);
  g.userData.inside = inside;
  const counter = new THREE.Mesh(rbox(2.3, 0.08, 0.45, 0.03), clay(0xf3efe7)); counter.position.set(0, 1.03, 1.25); g.add(counter);
  const awn = new THREE.Mesh(new THREE.BoxGeometry(3.5, 0.06, 1.3), new THREE.MeshLambertMaterial({ map: stripes('#d23a30', '#f6efe4', 10) })); awn.position.set(0, 2.55, 1.6); awn.rotation.x = 0.32; g.add(awn);
  const val = new THREE.Mesh(new THREE.PlaneGeometry(3.5, 0.22), new THREE.MeshLambertMaterial({ map: stripes('#d23a30', '#f6efe4', 10) })); val.position.set(0, 2.3, 2.21); g.add(val);
  const sign = new THREE.Mesh(new THREE.PlaneGeometry(2.8, 0.6), new THREE.MeshBasicMaterial({ toneMapped: false, map: canvasTex(1024, 220, (c, w, h) => {
    c.fillStyle = '#c8322b'; c.beginPath(); c.roundRect(0, 0, w, h, 40); c.fill(); c.fillStyle = '#ffe9b8'; c.font = `120px ${FONT.black}`; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText('LUCKY KITCHEN', w / 2, h / 2 + 6); }) }));
  sign.position.set(0, 3.05, 1.12); g.add(sign);
  const lanterns = [];
  for (const x of [-1.45, 1.45]) { const l = new THREE.Mesh(new THREE.SphereGeometry(0.2, 16, 12), glowMat(new THREE.Color(1.6, 0.35, 0.2))); l.scale.y = 1.2; l.position.set(x, 2.05, 2.1); g.add(l); lanterns.push(l);
    const cap = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.08, 0.06, 10), clay(0xd9b45a)); cap.position.set(x, 2.31, 2.1); g.add(cap); }
  const menu = new THREE.Mesh(new THREE.PlaneGeometry(0.7, 0.9), new THREE.MeshLambertMaterial({ map: canvasTex(280, 360, (c, w, h) => { c.fillStyle = '#1e1e22'; c.fillRect(0, 0, w, h); c.fillStyle = '#ffe9b8'; c.font = `34px ${FONT.black}`; c.fillText('MENU', 20, 50);
    c.font = `24px ${FONT.ui}`; ['Egg roll  2.50', 'Lo mein  9.00', 'Dumplings 7.00', 'Fried rice 8.00', 'Fortune cookie 0'].forEach((s, i) => c.fillText(s, 20, 100 + i * 48)); }) }));
  menu.position.set(1.62, 1.6, 0.4); menu.rotation.y = Math.PI / 2; g.add(menu);
  const sh = blobShadow(4.4, 3.2, 0.4); sh.position.y = 0.01; g.add(sh);
  g.userData.lanterns = lanterns; return g;
}
export function newsstand(covers) {
  const g = new THREE.Group(); const green = clay(0x2f6b52, { rimAmt: 0.2 }), roof = clay(0x245441);
  const body = new THREE.Mesh(rbox(3.4, 2.4, 1.8, 0.08), green); body.position.y = 1.2; g.add(body);
  const top = new THREE.Mesh(rbox(3.9, 0.22, 2.3, 0.08), roof); top.position.y = 2.55; g.add(top);
  const sign = new THREE.Mesh(new THREE.PlaneGeometry(3.2, 0.42), new THREE.MeshBasicMaterial({ toneMapped: false, map: canvasTex(1024, 140, (c, w, h) => { c.fillStyle = '#f4ead2'; c.fillRect(0, 0, w, h); c.fillStyle = '#1f3f30'; c.font = `96px ${FONT.black}`; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText('NEWS · MAGAZINES', w / 2, h / 2 + 4); }) }));
  sign.position.set(0, 2.85, 0.6); g.add(sign);
  // racks of covers on the front
  const rack = []; covers.forEach((tex, i) => { const m = new THREE.Mesh(new THREE.PlaneGeometry(0.62, 0.86), new THREE.MeshLambertMaterial({ map: tex, emissive: 0x222222 }));
    const col = i % 4, row = Math.floor(i / 4); m.position.set(-1.08 + col * 0.72, 1.75 - row * 0.98, 0.93 + row * 0.04); m.rotation.x = -0.08; g.add(m); rack.push(m); });
  const sh = blobShadow(4.2, 2.6, 0.4); sh.position.y = 0.01; g.add(sh);
  g.userData.rack = rack; return g;
}
export function payphone() {
  const g = new THREE.Group(); const steel = gloss(0xb9c0c8, { shininess: 90, rimAmt: 0.25 }), blue = gloss(0x2c5aa0, { shininess: 50 }), black = gloss(0x141418, { shininess: 70 });
  const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.06, 1.2, 12), steel); pole.position.y = 0.6; g.add(pole);
  const box = new THREE.Mesh(rbox(0.5, 0.75, 0.3, 0.05), steel); box.position.y = 1.55; g.add(box);
  const hood = new THREE.Mesh(rbox(0.75, 0.9, 0.55, 0.06), blue); hood.position.set(0, 1.62, -0.14); g.add(hood);
  const face = new THREE.Mesh(new THREE.PlaneGeometry(0.34, 0.46), new THREE.MeshLambertMaterial({ map: canvasTex(200, 270, (c, w, h) => { c.fillStyle = '#c9ced4'; c.fillRect(0, 0, w, h);
    c.fillStyle = '#20232a'; for (let i = 0; i < 12; i++) { const x = 40 + (i % 3) * 60, y = 110 + Math.floor(i / 3) * 40; c.beginPath(); c.roundRect(x - 20, y - 14, 40, 28, 6); c.fill(); }
    c.fillStyle = '#20232a'; c.fillRect(30, 20, 140, 60); c.fillStyle = '#7dffb2'; c.font = `26px ${FONT.monoB}`; c.fillText('INSERT 25¢', 38, 60); }) }));
  face.position.set(0, 1.57, 0.155); g.add(face);
  const handset = new THREE.Group(); const bar = new THREE.Mesh(new THREE.CapsuleGeometry(0.035, 0.28, 4, 10), black); handset.add(bar);
  for (const s of [-1, 1]) { const cup = new THREE.Mesh(new THREE.CylinderGeometry(0.055, 0.05, 0.06, 14), black); cup.position.set(0.035, s * 0.17, 0); cup.rotation.z = Math.PI / 2; handset.add(cup); }
  handset.position.set(-0.3, 1.55, 0.12); g.add(handset); g.userData.handset = handset;
  const sh = blobShadow(1.0, 1.0, 0.5); sh.position.y = 0.01; g.add(sh);
  return g;
}

// ---------------------------------------------------------------- the studio: a seamless backdrop for hero shots of props
export class Studio {
  constructor(pos) {
    const g = this.root = new THREE.Group(); g.position.copy(pos);
    this.col = { value: new THREE.Color(0x48c7d6) }; this.col2 = { value: new THREE.Color(0x1f6f86) };
    const mat = new THREE.ShaderMaterial({ uniforms: { uA: this.col, uB: this.col2 }, side: THREE.DoubleSide,
      vertexShader: `varying vec3 vP; void main(){ vP = position; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`,
      fragmentShader: `uniform vec3 uA, uB; varying vec3 vP; void main(){ float r = length(vP.xz * vec2(0.6, 1.0)); float k = smoothstep(0.0, 9.0, r + max(vP.y, 0.0) * 0.6); gl_FragColor = vec4(mix(uA, uB, k), 1.0); }` });
    const floor = new THREE.Mesh(new THREE.CircleGeometry(30, 48), mat); floor.rotation.x = -Math.PI / 2; g.add(floor);
    const wall = new THREE.Mesh(new THREE.CylinderGeometry(30, 30, 40, 48, 1, true, Math.PI * 0.5, Math.PI), mat); wall.position.set(0, 20, 0); g.add(wall);
    const sky = new THREE.Mesh(new THREE.SphereGeometry(32, 24, 12), mat); sky.material = mat; g.add(sky);
    this.mat = mat;
  }
  set(a, b) { this.col.value.set(a); this.col2.value.set(b); }
}

// ---------------------------------------------------------------- the whole world
export function buildWorld(scene) {
  const R = rng(11); const W = {};
  W.sky = makeSky(); scene.add(W.sky);
  const ground = new THREE.Mesh(new THREE.PlaneGeometry(3000, 3000), new THREE.ShaderMaterial({ uniforms: { uDay: ENV.day, uNeon: ENV.neon, uFog: ENV.fog, uFogD: ENV.fogD, uWarm: ENV.warm },
    vertexShader: `varying vec3 vW; void main(){ vec4 wp = modelMatrix * vec4(position, 1.0); vW = wp.xyz; gl_Position = projectionMatrix * viewMatrix * wp; }`,
    fragmentShader: `uniform float uDay, uNeon, uFogD, uWarm; uniform vec3 uFog; varying vec3 vW; void main(){ vec3 c = mix(vec3(0.02, 0.022, 0.03), vec3(0.42, 0.42, 0.44), uDay);
      vec2 g = abs(fract(vW.xz / 34.0) - 0.5); float lane = step(0.47, max(g.x, g.y)); c = mix(c, c * 1.6 + 0.02, lane * 0.4);
      c = mix(c, c * 0.5, uNeon); float fg = 1.0 - exp(-uFogD * length(vW - cameraPosition)); gl_FragColor = vec4(mix(c, uFog, fg), 1.0); }` }));
  ground.rotation.x = -Math.PI / 2; ground.position.y = -0.02; scene.add(ground);
  W.city = buildCity(R); scene.add(W.city);
  W.floor = plazaFloor(); scene.add(W.floor);
  // kerb around the plaza
  const kerb = clay(0xbdb6aa, { rimAmt: 0.1 });
  for (const [x, z, w, d] of [[0, PLAZA.z1 + 0.15, PLAZA.x1 - PLAZA.x0, 0.3], [PLAZA.x0 - 0.15, (PLAZA.z0 + PLAZA.z1) / 2, 0.3, PLAZA.z1 - PLAZA.z0], [PLAZA.x1 + 0.15, (PLAZA.z0 + PLAZA.z1) / 2, 0.3, PLAZA.z1 - PLAZA.z0]]) {
    const k = new THREE.Mesh(new THREE.BoxGeometry(w, 0.16, d), kerb); k.position.set(x, 0.08, z); scene.add(k); }
  W.bench = new Bench(); W.bench.root.position.copy(BENCH); scene.add(W.bench.root);
  W.lamp = lampPost(); W.lamp.position.set(-1.75, 0, -0.45); scene.add(W.lamp);
  W.lampLight = new THREE.PointLight(0xffc890, 0, 10, 1.4); W.lampLight.position.set(-1.25, 3.3, -0.2); scene.add(W.lampLight);
  W.trees = [];
  for (const [x, z] of [[-12, -6], [12, -6], [-12, 8], [12, 8], [-18, -20], [18, -20], [-6, -22], [6, -22]]) { const t = tree(R, 1.1); t.position.set(x, 0, z); scene.add(t); W.trees.push(t); }
  // other benches around the plaza (empty)
  for (const [x, z, ry] of [[-8, 4, 0.4], [8, 4, -0.4], [-15, -12, Math.PI / 2]]) { const b = new Bench(); b.root.position.set(x, 0, z); b.root.rotation.y = ry; scene.add(b.root); }
  W.tower = new Tower(); scene.add(W.tower.root);
  W.kiosk = takeoutKiosk(); W.kiosk.position.set(17.5, 0, 3); W.kiosk.rotation.y = -Math.PI / 2; scene.add(W.kiosk);
  // street lights along the plaza edge (glow at night)
  const sl = []; for (let x = -20; x <= 20; x += 8) sl.push(V3(x, 0, 17.2)); for (let z = -26; z <= 12; z += 8) { sl.push(V3(-22.6, 0, z)); sl.push(V3(22.6, 0, z)); }
  W.streetBulbs = [];
  for (const p of sl) { const post = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.06, 4.2, 8), gloss(0x1f2026)); post.position.copy(p).add(V3(0, 2.1, 0)); scene.add(post);
    const b = glowSprite2(); b.position.copy(p).add(V3(0, 4.25, 0)); scene.add(b); W.streetBulbs.push(b); }
  W.studio = new Studio(V3(600, 0, 0)); scene.add(W.studio.root);
  return W;
}
function glowSprite2() { const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: dotTex(), color: 0xffc58a, transparent: true, opacity: 0.9, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false })); s.scale.setScalar(1.2); return s; }
