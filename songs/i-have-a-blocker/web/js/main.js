// I have a blocker. (Take It Offline), v2: the 3D film. renderAt(t) draws the frame at time t (deterministic).
import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { ShaderPass } from 'three/addons/postprocessing/ShaderPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { loadFonts, clamp, lerp, sstep, easeIO, easeOut, easeIn, rng, clay, canvasTex, FONT, dotTex, blobShadow, win } from './lib.js';
import { buildCity, ROOF_Y, ROOF } from './city.js';
import { Room, RW, RH, GAP, slotPos } from './rooms.js';
import { particleLine } from './ptext.js';
import { buildCanyon, CY0, CY1, SHAFT_Z, FLOOR_Z } from './canyon.js';

const q = new URLSearchParams(location.search);
const W = +q.get('w') || 1600, H = +q.get('h') || 900; const VERT = H > W; const CLEAN = q.get('clean') === '1';
const T = {};
let LN = [], BEATS = [], DOWN = [];

// ---------------------------------------------------------------- renderer
const renderer = new THREE.WebGLRenderer({ antialias: false, preserveDrawingBuffer: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(1); renderer.setSize(W, H);
renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 0.95;
document.body.appendChild(renderer.domElement);
const scene = new THREE.Scene(); const FOG = new THREE.FogExp2(0x070a14, 0.0042); scene.fog = FOG;
const FOV = VERT ? 62 : 38;
const cam = new THREE.PerspectiveCamera(FOV, W / H, 0.1, 2400); scene.add(cam);
const hemi = new THREE.HemisphereLight(0x6f86b8, 0x0a0a0c, 1.1); scene.add(hemi);
const key = new THREE.DirectionalLight(0xfff1e0, 1.5); key.position.set(-8, 14, 22); scene.add(key); scene.add(key.target);
const deep = new THREE.DirectionalLight(0x9fe0ff, 0); deep.position.set(6, 10, 4); scene.add(deep);

const composer = new EffectComposer(renderer);
composer.addPass(new RenderPass(scene, cam));
const bloom = new UnrealBloomPass(new THREE.Vector2(W / 2, H / 2), 0.62, 0.5, 0.8); composer.addPass(bloom);
const finish = new ShaderPass({
  uniforms: { tDiffuse: { value: null }, uTime: { value: 0 }, uVig: { value: 0.34 }, uGrain: { value: 0.03 }, uCA: { value: 0.0012 }, uFlash: { value: 0 }, uFade: { value: 1 }, uFlashCol: { value: new THREE.Color(1, 1, 1) } },
  vertexShader: `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
  fragmentShader: `uniform sampler2D tDiffuse; uniform float uTime, uVig, uGrain, uCA, uFlash, uFade; uniform vec3 uFlashCol; varying vec2 vUv;
    float h(vec2 p){ return fract(sin(dot(p, vec2(12.9898,78.233)) + uTime * 17.0) * 43758.5453); }
    void main(){ vec2 d = vUv - 0.5; vec3 c;
      c.r = texture2D(tDiffuse, vUv + d * uCA).r; c.g = texture2D(tDiffuse, vUv).g; c.b = texture2D(tDiffuse, vUv - d * uCA).b;
      c *= 1.0 - uVig * pow(length(d * vec2(1.0, 0.9)) * 1.45, 2.4);
      c += (h(vUv * 1000.0) - 0.5) * uGrain; c = mix(c, uFlashCol, uFlash); gl_FragColor = vec4(c * uFade, 1.0); }` });
composer.addPass(finish);
composer.addPass(new OutputPass());

// ---------------------------------------------------------------- the world
let city, canyon, rooms = [], gridG, block, lyrics = [], dust, tickets, beams, burst, clock, crack, hud, hudTex, hudCtx;
const GRID_Y = ROOF_Y + 1.7 + 1.5 * (RH + GAP), GRID_Z = ROOF.z - 7;
const BLOCK_Z0 = GRID_Z + 6.2, ROOF_EDGE = ROOF.z + ROOF.d / 2;

function build() {
  city = buildCity(); scene.add(city);
  canyon = buildCanyon(); scene.add(canyon);
  gridG = new THREE.Group(); gridG.position.set(0, GRID_Y, GRID_Z); scene.add(gridG);
  for (let i = 0; i < 16; i++) { const r = new Room(i); rooms.push(r); gridG.add(r.root); }
  // the blocker
  const bt = canvasTex(512, 512, (g, w, h) => { g.fillStyle = '#ff3d8b'; g.fillRect(0, 0, w, h); const gr = g.createRadialGradient(w / 2, h / 2, 50, w / 2, h / 2, 360); gr.addColorStop(0, 'rgba(255,255,255,0.12)'); gr.addColorStop(1, 'rgba(0,0,0,0.25)'); g.fillStyle = gr; g.fillRect(0, 0, w, h);
    g.fillStyle = 'rgba(255,255,255,0.95)'; g.font = `84px ${FONT.dispBlack}`; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText('BLOCKER', w / 2, h / 2 + 8); });
  const plain = canvasTex(64, 64, (g, w, h) => { g.fillStyle = '#ff3d8b'; g.fillRect(0, 0, w, h); });
  const bmT = clay(0xffffff, { map: bt, emissive: 0x6a0c34, emissiveIntensity: 0.55, rimAmt: 0.3 }), bmP = clay(0xffffff, { map: plain, emissive: 0x6a0c34, emissiveIntensity: 0.55, rimAmt: 0.3 });
  block = new THREE.Mesh(new THREE.BoxGeometry(4.2, 4.2, 4.2), [bmT, bmP, bmP, bmP, bmT, bmP]);
  block.visible = false; scene.add(block);
  block.userData.shadow = blobShadow(7.5, 7.5, 0.75); scene.add(block.userData.shadow);
  // air dust (green), tickets, the impact burst, the beams
  const R = rng(5);
  { const n = 2600, p = new Float32Array(n * 3); for (let i = 0; i < n; i++) { p[i * 3] = (R() - 0.5) * 60; p[i * 3 + 1] = ROOF_Y + R() * 24; p[i * 3 + 2] = GRID_Z - 8 + R() * 40; }
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(p, 3));
    dust = new THREE.Points(g, new THREE.PointsMaterial({ color: 0x6dffaa, size: 0.08, map: dotTex(), transparent: true, opacity: 0.5, depthWrite: false, blending: THREE.AdditiveBlending })); scene.add(dust); }
  { const tt = canvasTex(256, 128, (c, w, h) => { c.fillStyle = '#eef1f6'; c.beginPath(); c.roundRect(0, 0, w, h, 10); c.fill(); c.fillStyle = '#2a6fdb'; c.fillRect(0, 0, w, 34);
      c.fillStyle = '#fff'; c.font = `24px ${FONT.monoB}`; c.fillText('ENG-4021', 12, 25); c.fillStyle = '#20232a'; c.font = `20px ${FONT.ui}`; c.fillText('Yesterday: the ticket', 12, 64); c.fillText('Today: the ticket', 12, 96); });
    tickets = new THREE.InstancedMesh(new THREE.PlaneGeometry(1.4, 0.7), new THREE.MeshLambertMaterial({ map: tt, side: THREE.DoubleSide, emissive: 0x222222 }), 90); tickets.visible = false; scene.add(tickets);
    tickets.userData.seed = Array.from({ length: 90 }, () => [R(), R(), R(), R()]); }
  { const n = 900, p = new Float32Array(n * 3), v = new Float32Array(n * 3); for (let i = 0; i < n; i++) { const a = R() * Math.PI * 2, s = 2 + R() * 9; v[i * 3] = Math.cos(a) * s; v[i * 3 + 1] = 1 + R() * 6; v[i * 3 + 2] = Math.sin(a) * s; }
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(p, 3)); g.userData.v = v;
    burst = new THREE.Points(g, new THREE.PointsMaterial({ color: 0xffb3d1, size: 0.16, map: dotTex(), transparent: true, opacity: 0.9, depthWrite: false, blending: THREE.AdditiveBlending })); burst.visible = false; scene.add(burst); }
  { beams = new THREE.Group(); const bmat = new THREE.MeshBasicMaterial({ color: 0x5dffa0, transparent: true, opacity: 0.8, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false });
    for (let i = 0; i < 16; i++) { const m = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.06, 1, 8, 1, true), bmat.clone()); beams.add(m); } beams.visible = false; scene.add(beams); }
  // the cost of the meeting, floating above the grid in verse 2
  clock = new THREE.Mesh(new THREE.PlaneGeometry(9, 2.4), new THREE.MeshBasicMaterial({ transparent: true, depthWrite: false, toneMapped: false,
    map: canvasTex(1200, 320, (g, w, h) => { g.font = `200px ${FONT.dispBlack}`; g.fillStyle = '#f2f6f4'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText('22:00', w / 2, h / 2 - 20);
      g.font = `52px ${FONT.monoB}`; g.fillStyle = '#6dffaa'; g.fillText('× 15 HEADS = 5.5 HOURS', w / 2, h - 28); }) }));
  clock.visible = false; scene.add(clock);
  // where the block breaks through the street
  crack = new THREE.Mesh(new THREE.CircleGeometry(6, 40), new THREE.MeshBasicMaterial({ color: 0x000000, transparent: true, opacity: 0.0, depthWrite: false }));
  crack.rotation.x = -Math.PI / 2; crack.position.set(0, 0.06, SHAFT_Z); scene.add(crack);
  // 2D overlay for cards (title, meeting summary)
  const c = document.createElement('canvas'); c.width = W; c.height = H; hudCtx = c.getContext('2d');
  hudTex = new THREE.CanvasTexture(c); hudTex.colorSpace = THREE.SRGBColorSpace;
  hud = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), new THREE.MeshBasicMaterial({ map: hudTex, transparent: true, depthTest: false, depthWrite: false, toneMapped: false, fog: false }));
  hud.frustumCulled = false; hud.renderOrder = 999; hud.visible = false;
  hud.material.onBeforeCompile = (sh) => { sh.vertexShader = sh.vertexShader.replace('#include <project_vertex>', 'vec4 mvPosition = vec4(position, 1.0); gl_Position = vec4(position.xy, 0.0, 1.0);'); };
  scene.add(hud);
}

// ---------------------------------------------------------------- timing
const wt = (i, j) => LN[i].wt[j], ls = (i) => LN[i].s, le = (i) => LN[i].e;
function range(a, b) { const o = []; for (let i = a; i < b; i++) o.push(i); return o; }
const NARR = [0, 1, 4, 5, 6, 7, ...range(16, 24), 28, 29, 30, ...range(36, 44)];
const UNISON = [...range(8, 16), ...range(24, 28), ...range(32, 36), ...range(44, 48)];
function lineAt(t) { for (let i = 0; i < LN.length; i++) if (t >= LN[i].s - 0.05 && t < LN[i].e + 0.1) return i; return -1; }
function wordPulse(i, t) { let v = 0; for (const tt of LN[i].wt) if (t >= tt - 0.04) v = Math.max(v, Math.exp(-(t - tt) / 0.3)); return v; }
function since(arr, t) { let k = -1; for (let i = 0; i < arr.length; i++) if (arr[i] <= t) k = i; return k < 0 ? 99 : t - arr[k]; }

function initTiming(timed, beats) {
  LN = timed; BEATS = beats.beats; DOWN = beats.downbeats; T.dur = beats.duration + 3.5;
  T.join = 4.71; T.samJoin = 86.42; T.ihave = ls(31); T.blocker = wt(31, 3);
  T.knocks = []; for (const i of [32, 33, 34]) LN[i].words.forEach((w, j) => { if (w.toLowerCase().replace(/[,.]/g, '') === 'offline') T.knocks.push(LN[i].wt[j]); });
  T.fall = T.knocks[4] + 0.05; T.bridge = ls(36); T.tomorrow = ls(40); T.sameLight = ls(41); T.final = ls(44); T.leave = 165.4; T.summary = 169.6; T.end = 174.5;
  LN.forEach((L, i) => {
    const end = Math.min(L.e + 0.9, i + 1 < LN.length ? LN[i + 1].s - 0.15 : 1e9);
    const col = i === 31 ? 0xff5aa0 : 0x6dffaa;
    const visW = 2 * 5.2 * Math.tan(THREE.MathUtils.degToRad(FOV) / 2) * (W / H);
    const p = particleLine(L.text, L.words, L.wt, end, { h: VERT ? 0.24 : 0.33, color: col, maxW: visW * (VERT ? 0.62 : 0.8), seed: i + 1, density: 2, size: 1.1 });
    p.material.uniforms.uOpacity.value = 0.62;
    p.visible = false; p.userData.s = L.s - 0.6; p.userData.e = end + 1.0; lyrics.push(p); cam.add(p);
  });
}

// ---------------------------------------------------------------- the standup's state
const LETTERS = 'TAKE IT OFFLINE?';
function letterOn(i, t) {
  const blocks = [[12, 14], [32, 34], [44, 46]]; const ch = LETTERS[i];
  if (ch === ' ' || ch === undefined) return 0;
  for (const [a, b] of blocks) {
    const s = ls(a), e = le(b); if (t < s - 0.3 || t > e + 0.8) continue;
    if (a === 32 && t < T.knocks[0] - 0.05) return 0;
    if (i === 15) return sstep(s + 0.2, s + 0.6, t) * (1 - sstep(e + 0.1, e + 0.7, t));
    const part = i < 4 ? 'take' : (i < 7 ? 'it' : 'offline');
    let first = null; for (let li = a; li <= b && first === null; li++) LN[li].words.forEach((w, j) => { if (first === null && w.toLowerCase().replace(/[,.]/g, '') === part) first = LN[li].wt[j]; });
    const j = i < 4 ? i : (i < 7 ? i - 5 : i - 8);
    const on = first + 0.07 * j;
    return sstep(on - 0.05, on + 0.2, t) * (1 - sstep(e + 0.1, e + 0.7, t));
  }
  return 0;
}
function fineOn(t) { for (const i of [15, 35, 47]) { const a = LN[i].wt[LN[i].wt.length - 1], b = le(i) + 1.4; if (t >= a - 0.1 && t < b) return sstep(a - 0.1, a + 0.25, t) * (1 - sstep(b - 0.5, b, t)); } return 0; }
function talk(i, t) {
  const li = lineAt(t); if (li < 0) return [0, 0x3ee07a];
  if (i === 15) return li === 31 ? [0.6 + 0.4 * wordPulse(31, t), 0xff3d8b] : [0, 0x3ee07a];
  if (UNISON.includes(li)) return (t >= T.blocker && t < T.knocks[0]) ? [0, 0x3ee07a] : [0.35 + 0.65 * wordPulse(li, t), 0x3ee07a];
  if (li === 2 || li === 3) {
    if (li === 3) { const who = [2, 3, 5, 6]; let n = 0; LN[3].words.forEach((w, k) => { if (t >= LN[3].wt[k] && ['next', 'out', 'it'].includes(w.toLowerCase().replace(/[,.]/g, ''))) n++; });
      return i === who[Math.min(n, 3)] ? [0.4 + 0.6 * wordPulse(3, t), 0x3ee07a] : [0, 0x3ee07a]; }
    return i === 2 ? [0.4 + 0.6 * wordPulse(li, t), 0x3ee07a] : [0, 0x3ee07a];
  }
  if (NARR.includes(li) && i === 0) return [0.35 + 0.65 * wordPulse(li, t), 0x3ee07a];
  return [0, 0x3ee07a];
}
function powerOn(i, t) {                       // the call fills up at 9:15; tomorrow it does it again
  let p = sstep(T.join + 0.12 * i, T.join + 0.12 * i + 0.25, t);
  if (t >= T.tomorrow) p = sstep(T.sameLight + 0.07 * i, T.sameLight + 0.07 * i + 0.25, t);
  if (i === 7 && t >= ls(23) + 1.2 && t < T.tomorrow) p *= 1 - sstep(ls(23) + 1.2, ls(23) + 1.5, t);   // Dana: hard stop
  if (t >= T.leave) p *= 1 - sstep(T.leave + 0.17 * (15 - i), T.leave + 0.17 * (15 - i) + 0.2, t);
  return p;
}
function gridPos(i, t) {                       // 5 x 3, reflowing to 4 x 4 when the new guy joins
  const k = easeIO((t - T.samJoin - 0.2 - 0.04 * i) / 1.1);
  const a = slotPos(Math.min(i, 14), 5, 3), b = slotPos(i, 4, 4);
  let p;
  if (i === 15) { p = b.clone(); const u = 1 - easeOut((t - T.samJoin) / 1.4); p.y -= u * 14; p.x += u * 8; p.z += u * 3; }
  else { p = a.clone().lerp(b, t < T.samJoin ? 0 : k); p.z += Math.sin(k * Math.PI) * 1.2; }
  if (t >= T.tomorrow - 1 && t < T.sameLight + 2.5) { const u = 1 - easeOut((t - (T.sameLight - 2.6 + 0.08 * i)) / 2.2); p.z -= u * 40; p.y += u * 6 * Math.sin(i * 1.3); p.x += u * 10 * Math.cos(i * 2.1); }
  return p;
}
function blockState(t) {                       // drops on "blocker"; five shoves to the roof's edge; the fifth sends it over
  if (t < T.blocker - 0.35 || t >= T.tomorrow) return null;
  const drop = easeIn((t - (T.blocker - 0.35)) / 0.35);
  let z = BLOCK_Z0; const push = (ROOF_EDGE + 2.6 - BLOCK_Z0) / 5;
  T.knocks.forEach((kt) => { if (t >= kt) z += push * easeOut((t - kt) / 0.4); });
  let y = ROOF_Y + 0.3 + 2.1 + (1 - drop) * 40, rx = 0;
  if (t >= T.fall) { const u = t - T.fall; y -= 0.5 * 22 * u * u + 2 * u; z += Math.min(u, 1.4) * 2.5; rx = u * 1.4; }
  if (y < CY1 + 2.1) { y = CY1 + 2.1; z = SHAFT_Z - 7; rx = 0.0; }      // it lands at the bottom of the shaft, at the edge of the field
  return { y, z, rx };
}

// ---------------------------------------------------------------- the camera
const V3 = (x, y, z) => new THREE.Vector3(x, y, z);
const GC = () => V3(0, GRID_Y, GRID_Z);
function roomWorld(i, t) { return gridPos(i, t).add(GC()); }
const WIDE = VERT ? 1.45 : 1.0;
function shake(t) { let s = 0; const hits = [T.blocker, ...T.knocks]; for (const h of hits) if (t >= h && t < h + 1.0) s += Math.exp(-(t - h) / 0.18) * (h === T.blocker ? 1.6 : 0.8); return s; }
function visit(i, a, b, t, side = 1) {
  const rp = roomWorld(i, t), k = easeIO((t - a) / (b - a)); const back = VERT ? 6.6 : 5.0;
  return [rp.clone().add(V3(lerp(-1.4, 1.2, k) * side, 0.3, lerp(back + 0.8, back, k))), rp.clone().add(V3(0, -0.15, -1.2)), FOV];
}
function camAt(t) {
  const gc = GC();
  if (t < 11.28) { const k = easeIO(t / 11.28);
    return [V3(lerp(-70, -3, k), lerp(110, GRID_Y + 2.5, k), lerp(190, GRID_Z + 30 * WIDE, k)), V3(0, lerp(18, GRID_Y, k), lerp(-80, GRID_Z, k)), FOV]; }
  if (t < 29.28) {
    if (t < 13.6) { const k = easeIO((t - 11.28) / 2.32); return [V3(lerp(-3, 1, k), GRID_Y + lerp(2.5, 1.2, k), GRID_Z + lerp(30, 19, k) * WIDE), gc.clone(), FOV]; }
    const visits = [[13.6, 15.72, 1], [15.72, 20.24, 2], [20.24, 22.4, 3], [22.4, 24.64, 5], [24.64, 29.28, 4]];
    for (const [a, b, i] of visits) if (t < b) return visit(i, a, b, t, i % 2 ? 1 : -1);
  }
  if (t < 59.92) {
    if (t < 41.6) { const k = (t - 29.28) / (41.6 - 29.28); return [V3(lerp(-9, 9, easeIO(k)), GRID_Y + 0.4, GRID_Z + 11 * WIDE), gc.clone().add(V3(lerp(-3, 3, easeIO(k)), -0.3, 0)), FOV]; }
    if (t < 54.48) { const k = (t - 41.6) / (54.48 - 41.6); return [V3(Math.sin(t * 0.25) * 1.5, GRID_Y + lerp(0.6, 0.2, k), GRID_Z + lerp(19, 15.5, easeIO(k)) * WIDE), gc.clone().add(V3(0, -0.4, 0)), FOV]; }
    return visit(0, 54.48, 59.92, t, 1);
  }
  if (t < 78.16) {
    if (t < 64.64) return visit(6, 59.92, 64.64, t, -1);
    if (t < 68.8) return visit(8, 64.64, 68.8, t, 1);
    if (t < 73.52) { const k = easeIO((t - 68.8) / 4.72); return [V3(lerp(4, -4, k), GRID_Y + lerp(3, 5, k), GRID_Z + lerp(17, 23, k) * WIDE), gc.clone().add(V3(0, 3.2, 0)), FOV]; }
    return visit(9, 73.52, 78.16, t, -1);
  }
  if (t < T.samJoin) { const k = easeIO((t - 78.16) / (T.samJoin - 78.16)); const a = lerp(0.9, 0.35, k);
    return [gc.clone().add(V3(Math.sin(a) * 17 * WIDE, lerp(4, 1.5, k), Math.cos(a) * 17 * WIDE)), gc.clone(), FOV]; }
  if (t < T.ihave) {
    const sp = roomWorld(15, t);
    const wide = gc.clone().add(V3(4, 1, 18 * WIDE)); const near = sp.clone().add(V3(0.6, 0.3, (VERT ? 7.5 : 5.6)));
    const p = wide.lerp(near, easeIO(sstep(T.samJoin + 2.5, T.ihave, t)));
    let fov = FOV; if (t > ls(30)) { const d = easeIO((t - ls(30)) / (T.ihave - ls(30))); p.z += d * 4; fov = FOV / (1 + d * 0.65); }
    return [p, gc.clone().lerp(sp, sstep(T.samJoin + 2, T.ihave - 1, t)), fov];
  }
  if (t < T.knocks[0] - 0.1) {
    const sp = roomWorld(15, t);
    if (t < T.blocker + 0.05) return [sp.clone().add(V3(0.4, 0.3, 9.6)), sp.clone().add(V3(0, 0, -1)), FOV / 1.65];
    const k = easeOut((t - T.blocker) / 1.2);
    return [V3(lerp(4, 13, k), ROOF_Y + lerp(5, 7, k), lerp(GRID_Z + 13, BLOCK_Z0 + 12, k) + (VERT ? 6 : 0)), V3(0, ROOF_Y + 3, BLOCK_Z0 - 1), FOV];
  }
  if (t < T.fall + 0.3) { const b = blockState(t); const k = (t - T.knocks[0]) / (T.fall - T.knocks[0]);
    return [V3(lerp(15, 11, k) * (VERT ? 1.3 : 1), ROOF_Y + lerp(6, 4.5, k), b.z + lerp(6, 9, k) + (VERT ? 4 : 0)), V3(0, ROOF_Y + 2.8, b.z - 3), FOV]; }
  if (t < T.bridge) { const k = easeIO((t - T.fall - 0.3) / (T.bridge - T.fall - 0.3));
    if (t < T.fall + 1.6) { const u = easeOut((t - T.fall - 0.3) / 1.3); return [V3(6, ROOF_Y + 6, ROOF_EDGE + 3), V3(0, lerp(ROOF_Y, ROOF_Y - 26, u), ROOF_EDGE + 4), FOV]; }
    return [V3(lerp(3, -2, k), ROOF_Y + lerp(3.5, 2.5, k), ROOF_EDGE - lerp(1, 4, k)), gc.clone().add(V3(0, -0.6, 0)), FOV]; }
  if (t < T.tomorrow) {
    const t1 = ls(38), t2 = ls(39);
    if (t < t1) { const k = (t - T.bridge) / (t1 - T.bridge); const y = lerp(ROOF_Y + 6, CY0 - 30, easeIO(k));       // over the edge, straight down after it
      const c = V3(Math.sin(k * 2.2) * 1.2, y, ROOF_EDGE + 6.5); const look = V3(c.x * 0.2 + 0.001, y - 30, c.z + 0.2);
      return [c, look, FOV + (VERT ? 4 : 14)]; }
    if (t < t2) { const k = (t - t1) / (t2 - t1); const y = lerp(CY0 - 26, CY1 + 44, easeIO(k)); const a = lerp(0.3, 3.4, k);   // the layers, the years
      return [V3(Math.sin(a) * 2.0, y, SHAFT_Z + Math.cos(a) * 2.0), V3(Math.sin(a + 2.2) * 6, y - 14, SHAFT_Z + Math.cos(a + 2.2) * 6), FOV + (VERT ? 0 : 14)]; }
    const k = easeIO((t - t2) / (T.tomorrow - t2));                                                                    // the floor of Offline
    return [V3(lerp(0, -2, k), lerp(CY1 + 30, CY1 + 17, k), lerp(SHAFT_Z + 2, SHAFT_Z - 10, k) + (VERT ? 8 : 0)), V3(lerp(0, 1, k), CY1 + 2, lerp(SHAFT_Z - 30, FLOOR_Z - 10, k)), FOV + (VERT ? 0 : 6)];
  }
  if (t < T.final) { const k = easeIO((t - T.tomorrow) / (T.final - T.tomorrow));
    return [V3(lerp(-30, 2, k), lerp(70, GRID_Y + 1.5, k), lerp(90, GRID_Z + 20 * WIDE, k)), gc.clone().add(V3(0, lerp(-10, 0, k), 0)), FOV]; }
  if (t < T.leave) { const k = (t - T.final) / (T.leave - T.final); const a = lerp(-0.35, 0.35, easeIO(k));
    return [gc.clone().add(V3(Math.sin(a) * 18 * WIDE, lerp(0.4, 1.5, k), Math.cos(a) * 18 * WIDE)), gc.clone().add(V3(0, -0.3, 0)), FOV]; }
  { const k = easeIO((t - T.leave) / 9); return [gc.clone().add(V3(0, lerp(1.5, 3, k), lerp(18, 26, k) * WIDE)), gc.clone(), FOV]; }
}

// ---------------------------------------------------------------- 2D cards (title, meeting summary)
function drawHud(t) {
  const g = hudCtx; g.clearRect(0, 0, W, H); let any = false; const s = Math.min(W, H) / 1080;
  const a1 = sstep(0.8, 1.8, t) * (1 - sstep(9.0, 10.2, t));
  if (a1 > 0.01) { any = true; g.globalAlpha = a1; const x = VERT ? W / 2 : 70 * s, y = VERT ? H * 0.2 : H - 170 * s; g.textAlign = VERT ? 'center' : 'left';
    g.fillStyle = '#ff5aa0'; g.font = `${34 * s}px ${FONT.mono}`; g.fillText('aditazzz', x, y);
    g.fillStyle = '#f3efe6'; g.font = `${62 * s}px ${FONT.disp}`; g.fillText('I have a blocker.', x, y + 66 * s);
    g.fillStyle = 'rgba(243,239,230,0.75)'; g.font = `${40 * s}px ${FONT.disp}`; g.fillText('(Take It Offline)', x, y + 116 * s); }
  const a2 = sstep(T.summary, T.summary + 0.6, t) * (1 - sstep(T.end - 0.5, T.end, t));
  if (a2 > 0.01) { any = true; g.globalAlpha = a2 * 0.75; g.fillStyle = '#000'; g.fillRect(0, 0, W, H); g.globalAlpha = a2; g.textAlign = 'center';
    const cx = W / 2; let y = H * 0.36;
    const rows = [['MEETING SUMMARY', `${30 * s}px ${FONT.monoB}`, '#6dffaa'], ['Daily Standup · 22 min', `${78 * s}px ${FONT.disp}`, '#f3efe6'],
      ['Blockers: 1  (taken offline)', `${50 * s}px ${FONT.disp}`, '#ff5aa0'], ['Next: tomorrow, 9:15 AM', `${36 * s}px ${FONT.ui}`, 'rgba(243,239,230,0.65)']];
    rows.forEach(([txt, f, c], k) => { g.globalAlpha = a2 * sstep(T.summary + 0.15 * k, T.summary + 0.15 * k + 0.5, t); g.font = f; g.fillStyle = c; g.fillText(txt, cx, y); y += (k === 0 ? 92 : 86) * s; }); }
  g.globalAlpha = 1; hud.visible = any; if (any) hudTex.needsUpdate = true;
}

// ---------------------------------------------------------------- per frame
const _m4 = new THREE.Matrix4(), _q = new THREE.Quaternion(), _e = new THREE.Euler();
window.renderAt = (t) => {
  const dawn = t < T.tomorrow ? 0.35 : lerp(0.35, 1.0, sstep(T.tomorrow, T.final, t));
  city.userData.sky.material.uniforms.uDawn.value = dawn;
  const [p, tg, fov] = camAt(t); const sh = shake(t);
  cam.position.copy(p).add(V3(Math.sin(t * 61) * 0.06 * sh, Math.cos(t * 47) * 0.06 * sh, 0)); cam.lookAt(tg); cam.fov = fov; cam.updateProjectionMatrix();
  const under = clamp((-cam.position.y) / 25); city.userData.sky.visible = under < 0.5;
  FOG.color.setRGB(lerp(0.027, 0.02, under), lerp(0.039, 0.07, under), lerp(0.078, 0.06, under)); FOG.density = lerp(0.0042, 0.0065, under); hemi.intensity = lerp(1.1, 1.5, under); deep.intensity = 3.2 * under; key.intensity = 1.5 * (1 - under); hemi.color.setHex(under > 0.5 ? 0x8fb8c0 : 0x6f86b8);
  const dark0 = (t >= T.blocker && t < T.knocks[0]) ? sstep(T.blocker, T.blocker + 0.05, t) : 0;
  for (let i = 0; i < 16; i++) {
    const r = rooms[i]; r.root.position.copy(gridPos(i, t));
    r.root.visible = (i < 15 || t >= T.samJoin) && !(t >= T.bridge + 4 && t < T.tomorrow - 1);
    const [tk, tc] = talk(i, t);
    const pw = i === 15 ? (t >= T.knocks[4] && t < T.tomorrow ? 1 - sstep(T.knocks[4], T.knocks[4] + 0.5, t) : 1) * (t >= T.leave ? 1 - sstep(T.leave, T.leave + 0.2, t) : 1) : powerOn(i, t);
    const dark = Math.max(i === 15 ? 0 : dark0 * 0.94, 1 - pw);
    r.update({ t, talk: tk * pw, talkCol: tc, card: letterOn(i, t), fine: fineOn(t), dark, blink: i === 4 && t >= ls(7) && t < le(7) ? 1 : undefined });
  }
  const b = blockState(t); block.visible = !!b; block.userData.shadow.visible = !!b && t < T.fall + 0.2;
  if (b) { block.position.set(0, b.y, b.z); block.rotation.set(b.rx, 0.12, 0); block.userData.shadow.position.set(0, ROOF_Y + 0.34, b.z);
    block.userData.shadow.material.opacity = 0.75 * clamp(1 - (b.y - ROOF_Y - 2.4) / 30); }
  const bu = t - T.blocker; burst.visible = bu >= 0 && bu < 2.2;
  if (burst.visible) { const pa = burst.geometry.attributes.position, v = burst.geometry.userData.v;
    for (let i = 0; i < pa.count; i++) pa.setXYZ(i, v[i * 3] * (1 - Math.exp(-bu * 2.2)), ROOF_Y + 0.4 + v[i * 3 + 1] * bu - 2.45 * bu * bu, BLOCK_Z0 + v[i * 3 + 2] * (1 - Math.exp(-bu * 2.2)));
    pa.needsUpdate = true; burst.material.opacity = 0.9 * (1 - bu / 2.2); }
  const kb = since(T.knocks, t); beams.visible = !!b && kb < 0.55 && t < T.fall + 0.4;
  if (beams.visible) { const tgt = V3(0, b.y, b.z - 2.1);
    beams.children.forEach((m, i) => { if (i === 15) { m.visible = false; return; } m.visible = true; const from = roomWorld(i, t).add(V3(0, 0, 0.1));
      const d = tgt.clone().sub(from); const len = d.length(); m.position.copy(from).add(d.clone().multiplyScalar(0.5)); m.quaternion.setFromUnitVectors(V3(0, 1, 0), d.clone().normalize());
      const th = 1 + 2.5 * Math.exp(-kb / 0.08); m.scale.set(th, len, th); m.material.opacity = 0.9 * (1 - kb / 0.55); }); }
  const tkk = Math.max(win(t, ls(10), le(11), 0.4, 0.8), win(t, ls(26), le(27), 0.4, 0.8), win(t, ls(2), le(2), 0.3, 0.6));
  tickets.visible = tkk > 0.01;
  if (tickets.visible) { const sd = tickets.userData.seed, gc = GC();
    for (let i = 0; i < sd.length; i++) { const [a, b2, c, d] = sd[i]; const ang = a * Math.PI * 2 + t * (0.35 + b2 * 0.3); const rad = (10 + c * 6) * (0.6 + 0.4 * tkk);
      _e.set(t * (0.5 + d), ang, t * 0.3 + a * 6); _q.setFromEuler(_e);
      _m4.compose(V3(gc.x + Math.cos(ang) * rad, gc.y - 4 + d * 10 + Math.sin(t * 0.8 + a * 9) * 0.6, gc.z + Math.sin(ang) * rad * 0.6 + 2), _q, V3(tkk, tkk, tkk)); tickets.setMatrixAt(i, _m4); }
    tickets.instanceMatrix.needsUpdate = true; }
  const ck = win(t, ls(20), le(21), 0.3, 0.6); clock.visible = ck > 0.01;
  if (clock.visible) { clock.position.copy(GC()).add(V3(0, 6.6, 0.6)); clock.material.opacity = ck; clock.scale.setScalar(0.85 + 0.15 * ck); }
  crack.material.opacity = t >= T.fall + 1.2 && t < T.tomorrow ? 0.95 : 0;
  const tanH = Math.tan(THREE.MathUtils.degToRad(cam.fov) / 2);
  for (const L of lyrics) { const on = !CLEAN && t >= L.userData.s && t < L.userData.e; L.visible = on;
    if (on) { L.material.uniforms.uTime.value = t; const dz = 5.2; L.position.set(0, VERT ? -dz * tanH * 0.20 : -dz * tanH * 0.62, -dz); L.material.uniforms.uScale.value = H / (2 * tanH); } }
  dust.rotation.y = t * 0.01;
  const fl = (t >= T.blocker && t < T.blocker + 0.3 ? Math.exp(-(t - T.blocker) / 0.06) * 0.5 : 0) + (kb < 0.3 && t >= T.knocks[0] && t < T.fall + 0.1 ? Math.exp(-kb / 0.05) * 0.18 : 0);
  finish.uniforms.uFlash.value = fl; finish.uniforms.uFlashCol.value.set(t < T.knocks[0] ? 0xffc2dc : 0xd8ffe8);
  finish.uniforms.uTime.value = t;
  finish.uniforms.uFade.value = sstep(0.0, 0.9, t) * (1 - sstep(T.dur - 1.0, T.dur - 0.05, t));
  if (!CLEAN) drawHud(t); else hud.visible = false;
  composer.render();
  return renderer.domElement.toDataURL('image/jpeg', 0.93);
};

(async () => {
  await loadFonts();
  const [timed, beats] = await Promise.all([fetch('/data/timed.json').then((r) => r.json()), fetch('/data/beats.json').then((r) => r.json())]);
  build(); initTiming(timed, beats);
  window.DUR = T.dur; window.T = T; window.__dbg = { scene, cam, composer, renderer, canyon }; window.ready = true;
})().catch((e) => { console.log('INIT ERROR', e.stack || e); });
