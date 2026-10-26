// Ragnarök or Reach for Mars: the film. renderAt(t) draws the frame at time t (deterministic).
// Puppets and the objects they handle move on twos (15 fps, stop-motion); camera, fire, light and captions run at 30.
import * as THREE from 'three';
import { makeStage } from './stage.js';
import { RIM, RIM_AMT, clamp, lerp, sstep, easeIO, easeOut, easeIn, rng } from './lib.js';
import { hallEnv, loadFilmFonts } from './lib2.js';
import { mats, TechKing, Seeress, Viking, makeStaff, shadows } from './puppets.js';
import { makeRocket } from './rocket.js';
import { makeCard, drawMars, drawRagnarok, CARD, cardMaterial } from './cards.js';
import { buildHall, HALL } from './hall.js';
import { emberLine } from './embers.js';
import { mergeStatic } from './merge.js';
import { knob } from './puppets.js';
import { candle } from './props.js';
import { towerPopup, sunPopup, robotPopup, redPopup, gardenerPopup } from './popups.js';
import { Robot, tomatoPlant, tomato, plantLabel, silver, burin } from './robots.js';
import { initFull, frameFull, camFull, KEYS } from './full.js';
import { buildFinale } from './finale.js';
import { canvasTex } from './lib.js';

const q = new URLSearchParams(location.search);
const W = +q.get('w') || 1600, H = +q.get('h') || 900; const CLEAN = q.get('clean') === '1';
// stills only (single-cover framing): ?cfov=<fov multiplier>&cback=<metres back along the view>&cy=<look offset, metres up>
const COVER = q.get('cfov') ? { fovK: +q.get('cfov'), back: +(q.get('cback') || 0), dy: +(q.get('cy') || 0) } : null;
// stills only: explicit cameras per still time, ?cams=T:px,py,pz:lx,ly,lz:fov;T2:...  (e.g. thumbnail framings)
const CAMS = {}; for (const part of (q.get('cams') || '').split(';').filter(Boolean)) { const [t, pp, ll, f] = part.split(':'); CAMS[(+t).toFixed(2)] = { p: pp.split(',').map(Number), l: ll.split(',').map(Number), fov: +f }; }
function camOverride(t, c) { const o = CAMS[t.toFixed(2)]; if (!o) return c; return { ...c, p: new THREE.Vector3(...o.p), look: new THREE.Vector3(...o.l), fov: o.fov, up: new THREE.Vector3(0, 1, 0) }; }
const st = makeStage(W, H, { exposure: 1.12, bloom: [0.5, 0.55, 0.86] });
// ---- the vertical (9:16) version: the same shots, re-aimed for a narrow frame (own framing, not a crop)
const VERT = H > W;
const CAP = VERT ? { h: 0.12, maxW: 1.45, y: 0.42 } : { h: 0.21, maxW: 5.4, y: 0.74 };   // caption size and default height
// per-shot overrides for the vertical cut: key = shot start time (2 decimals; 'p' prefix for the preview's shots) ->
// { pan: [x, y] in 16:9 frame units, k (fov tangent factor), look, pos, shift / pshift: [x,y,z] added to look / position }
const V_OVR = {
  'p5.50': { pan: [-0.13, 0] },                                                                      // her card lands at his place: keep him in frame
  '31.60': { pan: [0.06, -0.04] }, '77.35': { pan: [0.06, -0.04] }, '140.92': { pan: [0.06, -0.04] }, '195.72': { pan: [0.06, -0.04] },   // his coin, by the right-hand card
  '39.77': { pan: [-0.06, -0.06] }, '85.49': { pan: [-0.06, -0.06] }, '148.97': { pan: [-0.06, -0.06] }, '203.31': { pan: [-0.06, -0.06] }, // his hand reaching
  '44.63': { pan: [-0.18, 0] },                                                                      // every head turns to the rocket
  '46.92': { pan: [0, -0.22] },                                                                      // the Tower turning over at his place
  '51.49': { k: 1.9, pan: [0.03, 0] },                                                                               // all of "20%"
  '96.45': { pan: [0, -0.15] }, '105.30': { pan: [0, -0.15] }, '113.55': { pan: [0, -0.15] },       // each card turning over at his place
  '162.88': { pan: [0, -0.05], k: 1.7 },                                                             // the engraving card, whole
  '176.48': { pan: [0.08, 0] }, '181.00': { pan: [0.05, 0] },                                        // past his shoulder to her
  '183.26': { k: 2.0, pan: [0.02, 0] },                                                              // you and me: both of them
};
function vfix(key, p, look, fov, up) {
  const o = V_OVR[key] || {};
  const k = o.k ?? 1.58; let fv = 2 * Math.atan(Math.tan(THREE.MathUtils.degToRad(fov) / 2) * k) * 180 / Math.PI; fv = Math.min(fv, o.maxFov ?? 78);
  const P = o.pos ? new THREE.Vector3(...o.pos) : p.clone(), L = o.look ? new THREE.Vector3(...o.look) : look.clone();
  if (o.shift) L.add(new THREE.Vector3(...o.shift));
  if (o.pshift) P.add(new THREE.Vector3(...o.pshift));
  if (o.pan) {   // pan in units of the 16:9 frame: [+x = frame centre moves right, +y = up]
    const d = L.clone().sub(P), dist = d.length(); d.normalize(); const U = (up || new THREE.Vector3(0, 1, 0)).clone();
    const r = new THREE.Vector3().crossVectors(d, U).normalize(), u = new THREE.Vector3().crossVectors(r, d).normalize();
    const h16 = 2 * dist * Math.tan(THREE.MathUtils.degToRad(fov) / 2);
    L.addScaledVector(r, o.pan[0] * h16 * 16 / 9).addScaledVector(u, o.pan[1] * h16);
  }
  if (o.lerpTo) L.lerp(new THREE.Vector3(...o.lerpTo[0]), o.lerpTo[1]);
  return [P, L, o.fov ?? fv];
}
st.renderer.shadowMap.enabled = true; st.renderer.shadowMap.type = THREE.PCFShadowMap;
const env = hallEnv(st.renderer); const M = mats(env);
const V = (x, y, z) => new THREE.Vector3(x, y, z);
const TOP = HALL.table.top + 0.0013;                       // a card lying on the reading table
const SEER = V(0, HALL.dais.y, HALL.seat.z + 0.05), MAN = V(0, 0, HALL.stool.z);
let T = null;

// ---------------------------------------------------------------- timeline helpers
// keys: [[t, value, ease?], ...]; values are numbers or arrays (interpolated per element); ease applies on the way in
function track(keys, t) {
  if (t <= keys[0][0]) return keys[0][1];
  for (let i = 1; i < keys.length; i++) { const [t1, v1, e] = keys[i]; if (t < t1) { const [t0, v0] = keys[i - 1]; const u = (e || easeIO)((t - t0) / (t1 - t0)); return mixV(v0, v1, u); } }
  return keys[keys.length - 1][1];
}
function mixV(a, b, u) { if (Array.isArray(a)) return a.map((x, i) => mixV(x, b[i], u)); if (a === null || b === null || typeof a !== 'number') return u < 0.5 ? a : b; return a + (b - a) * u; }
const lin = (x) => clamp(x);
const step2 = (t) => Math.floor(t * 15 + 1e-6) / 15;       // stop-motion cadence
// a percussive event: 0 at rest, 1 at impact; rises over `up` before t0 and drops instantly
const hit = (t, t0, up = 0.35) => (t < t0 - up || t >= t0 + 0.02) ? 0 : easeOut((t - (t0 - up)) / up);
const decay = (t, t0, tau) => t < t0 ? 0 : Math.exp(-(t - t0) / tau);
function lightning(t) {   // multi-stroke flashes on the thunder and on "I've seen what's coming"
  let k = 0;
  for (const [ts, a] of [[T.thunder[0], 0.75], [T.thunder[1], 0.7], [T.thunder[2], 1.0], [18.45, 0.6]]) {
    if (t < ts - 0.01 || t > ts + 1.2) continue;
    k += a * (decay(t, ts, 0.07) + 0.65 * decay(t, ts + 0.12, 0.05) + 0.4 * decay(t, ts + 0.27, 0.09));
  }
  return k;
}

// ---------------------------------------------------------------- the world
const VIKS_ALL = [
  { beard: '#a8481e', hair: 'long', beardStyle: 'long', tunic: '#3f5a34', trim: ['#c9a23a', '#7a1c14'], cloak: '#2a2622', fur: 'dark' },
  { beard: '#d9b56a', hair: 'bald', beardStyle: 'forked', tunic: '#7a2a22', trim: ['#e0c27a', '#1f3a6a'], cloak: '#3a3226', fur: 'light' },
  { beard: '#4a3426', hair: 'tied', beardStyle: 'braided', tunic: '#2e4a6a', trim: ['#b88a3a', '#3a1a10'], cloak: '#1e1c1a', fur: 'dark' },
  { beard: '#8a8680', hair: 'long', beardStyle: 'long', tunic: '#5a4a2a', trim: ['#7a1c14', '#d8c08a'], cloak: '#2a2a30', fur: 'dark' },
  { beard: '#c46a2a', hair: 'tied', beardStyle: 'forked', tunic: '#4a2a4a', trim: ['#d8b84a', '#2e5a34'], cloak: '#2a1e18', fur: 'light' },
  { beard: '#2a1e16', hair: 'bald', beardStyle: 'long', tunic: '#7a5a2a', trim: ['#1f3a6a', '#e0d6c0'], cloak: '#3a2a20', fur: 'dark' },
  { beard: '#b8862a', hair: 'long', beardStyle: 'braided', tunic: '#2a4a3a', trim: ['#c9a23a', '#4a1a14'], cloak: '#2e2a26', fur: 'dark' },
  { beard: '#6a3a1e', hair: 'tied', beardStyle: 'long', tunic: '#6a2430', trim: ['#e0c27a', '#1a1a1a'], cloak: '#262230', fur: 'light' },
];
const scene = new THREE.Scene(); scene.background = new THREE.Color(0x050302); const FOG = new THREE.FogExp2(0x140b06, 0.03); scene.fog = FOG;
RIM.value.set(0xff8a40); RIM_AMT.value = 0.12;
const hemi = new THREE.HemisphereLight(0x3a4a6a, 0x1a0e08, 0.18); scene.add(hemi);
const cam = new THREE.PerspectiveCamera(40, W / H, 0.02, 120); scene.add(cam);
let hall, seer, man, rocket, staff, vikings = [], guards = [], tf, deck = [], gLight, eLight, lines = [];

function build() {
  hall = buildHall(env, M); scene.add(hall);
  hall.userData.fire.userData.setBursts([T.drums, ...T.heys, 60.63, 92.64, 122.1, 174.16, 227.9]);
  seer = new Seeress(M); seer.root.position.copy(SEER); scene.add(seer.root);
  man = new TechKing(M); man.root.position.copy(MAN); man.root.rotation.y = Math.PI; scene.add(man.root);
  rocket = makeRocket(env, { h: 0.7 }); rocket.position.set(-0.43, 0, HALL.stool.z + 0.04); rocket.rotation.y = 2.4; scene.add(rocket);
  staff = makeStaff(M); staff.position.set(-0.47, HALL.dais.y, HALL.seat.z + 0.02); staff.rotation.set(0.0, 0, 0.1); scene.add(staff);
  const VIKS = VIKS_ALL; const _unused = [
    { beard: '#a8481e', hair: 'long', beardStyle: 'long', tunic: '#3f5a34', trim: ['#c9a23a', '#7a1c14'], cloak: '#2a2622', fur: 'dark' },
    { beard: '#d9b56a', hair: 'bald', beardStyle: 'forked', tunic: '#7a2a22', trim: ['#e0c27a', '#1f3a6a'], cloak: '#3a3226', fur: 'light' },
    { beard: '#4a3426', hair: 'tied', beardStyle: 'braided', tunic: '#2e4a6a', trim: ['#b88a3a', '#3a1a10'], cloak: '#1e1c1a', fur: 'dark' },
    { beard: '#8a8680', hair: 'long', beardStyle: 'long', tunic: '#5a4a2a', trim: ['#7a1c14', '#d8c08a'], cloak: '#2a2a30', fur: 'dark' },
    { beard: '#c46a2a', hair: 'tied', beardStyle: 'forked', tunic: '#4a2a4a', trim: ['#d8b84a', '#2e5a34'], cloak: '#2a1e18', fur: 'light' },
    { beard: '#2a1e16', hair: 'bald', beardStyle: 'long', tunic: '#7a5a2a', trim: ['#1f3a6a', '#e0d6c0'], cloak: '#3a2a20', fur: 'dark' },
    { beard: '#b8862a', hair: 'long', beardStyle: 'braided', tunic: '#2a4a3a', trim: ['#c9a23a', '#4a1a14'], cloak: '#2e2a26', fur: 'dark' },
    { beard: '#6a3a1e', hair: 'tied', beardStyle: 'long', tunic: '#6a2430', trim: ['#e0c27a', '#1a1a1a'], cloak: '#262230', fur: 'light' },
  ];
  const R = rng(5);
  HALL.seats.forEach((s, i) => {
    const v = new Viking(M, { ...VIKS[(i * 5 + (s.side > 0 ? 3 : 0)) % VIKS.length], seed: 10 + i, bulk: 0.95 + R() * 0.1, lod: 0.45 });
    v.root.position.set(s.x, 0, s.z); v.root.rotation.y = -s.side * Math.PI / 2; scene.add(v.root);
    v.userData = { seat: s, ph: R() * 10, lag: (R() - 0.5) * 0.06, yaw0: (R() - 0.5) * 0.5 }; vikings.push(v);
  });
  for (const s of [-1, 1]) { const gd = new Viking(M, { ...VIKS[2], hair: 'helmet', beardStyle: 'short', tunic: '#2e3a4a', seed: 30 + s, bulk: 1.05, lod: 0.6 }); gd.root.position.set(s * 2.0, 0, HALL.z0 + 1.2); scene.add(gd.root); gd.pose({ seated: false, hands: [[-0.26, -0.02, 0.1], [0.26, -0.02, 0.1]] }); guards.push(gd); }
  // the cards: the two-faced card, then the deck (two of its cards can glow on their own)
  tf = makeCard(env, [drawMars(), drawRagnarok(), FACES.fool]); scene.add(tf);
  for (let i = 0; i < 22; i++) { const c = makeCard(env, null, { ownBack: i < 2 }); scene.add(c); deck.push(c); }
  gLight = new THREE.PointLight(0xffc560, 0, 1.6, 2); scene.add(gLight); eLight = new THREE.PointLight(0xff4a18, 0, 1.6, 2); scene.add(eLight);
  buildRest();
  shadows(scene); scene.traverse((o) => { if (o.isMesh && o.material && (o.material.isShaderMaterial || o.material.transparent)) { o.castShadow = false; o.receiveShadow = false; } });
  for (const c of [tf, ...deck, ...X.loose]) c.traverse((o) => { if (o.isMesh) o.castShadow = false; });
  for (const r of [...X.robots, X.attendant]) r.root.traverse((o) => { if (o.isMesh) o.receiveShadow = false; });
  for (const p of [seer, man, ...vikings, ...guards]) p.root.traverse((o) => { if (o.isMesh) o.receiveShadow = false; });
  const mg = mergeStatic(hall); console.log('merged', mg.merged, 'into', mg.meshes);
  st.renderer.shadowMap.autoUpdate = false;
  // captions: one ember line per sung line, in camera space; a spark burst on each HEY
  for (const L of T.lines) { const g = emberLine(L.text, L.words, L.t, L.end, VERT ? { h: CAP.h, maxW: CAP.maxW, seed: lines.length + 3, size: 0.8 } : { h: CAP.h, maxW: CAP.maxW, seed: lines.length + 3 }); g.visible = false; cam.add(g); lines.push(g); }
}

// ---------------------------------------------------------------- everything after the preview: cards, worlds, robots, props, the finale
let FACES = null; const X = { loose: [] };
async function loadFaces() {
  const names = ['fool', 'foolTurn', 'magician', 'tower', 'star', 'sun', 'sunBurn', 'robot', 'red', 'gardener', 'engr0', 'engr1', 'engrH'];
  const out = {}; await Promise.all(names.map(async (n) => { const im = new Image(); im.src = `/tex/${n}.png`; await im.decode(); out[n] = im; })); return out;
}
function engravingCard() {   // the bridge's card: blank, engraves itself top to bottom (uReveal), then one human line (uHuman)
  const c = makeCard(env, [FACES.engr0, FACES.engr1, FACES.engrH]); const m = c.userData.front.material; const u = m.userData.u;
  u.uReveal = { value: 0 }; u.uHuman = { value: 0 };
  m.onBeforeCompile = (sh) => { Object.assign(sh.uniforms, u);
    sh.fragmentShader = sh.fragmentShader
      .replace('#include <common>', '#include <common>\nuniform sampler2D mapB, mapC; uniform float uReveal, uHuman; uniform vec3 uGlow; float goldK;')
      .replace('#include <map_fragment>', `vec2 px = vec2(vMapUv.x * 1200.0, (1.0 - vMapUv.y) * 2057.0);
        float front = 110.0 + (1690.0 - 150.0 + 80.0) * uReveal + sin(px.x / 60.0) * 18.0;
        float showB = 1.0 - smoothstep(front - 5.0, front + 5.0, px.y); if (uReveal >= 0.9999) showB = 1.0;
        float hx = 566.0 + (860.0 - 566.0) * uHuman; float showC = (1.0 - smoothstep(hx - 3.0, hx + 3.0, px.x)) * step(0.0005, uHuman); if (uHuman >= 0.9999) showC = 1.0;
        vec4 sampledDiffuseColor = mix(mix(texture2D(map, vMapUv), texture2D(mapB, vMapUv), showB), texture2D(mapC, vMapUv), showC);
        float lum = dot(sampledDiffuseColor.rgb, vec3(0.299, 0.587, 0.114)); goldK = smoothstep(0.06, 0.32, lum);
        diffuseColor *= sampledDiffuseColor;`)
      .replace('#include <roughnessmap_fragment>', 'float roughnessFactor = mix(0.24, 0.42, goldK);')
      .replace('#include <lights_fragment_maps>', '#include <lights_fragment_maps>\n radiance *= mix(0.3, 1.0, goldK);')
      .replace('#include <metalnessmap_fragment>', 'float metalnessFactor = goldK;')
      .replace('#include <emissivemap_fragment>', `#include <emissivemap_fragment>
        totalEmissiveRadiance += uGlow * (0.25 + goldK);
        vec2 px2 = vec2(vMapUv.x * 1200.0, (1.0 - vMapUv.y) * 2057.0); float fr = 110.0 + 1620.0 * uReveal + sin(px2.x / 60.0) * 18.0;
        float band = (1.0 - smoothstep(0.0, 34.0, abs(px2.y - fr + 12.0))) * step(0.001, uReveal) * step(uReveal, 0.999);
        totalEmissiveRadiance += vec3(0.45, 0.22, 0.09) * band * (0.15 + goldK);`); };
  m.customProgramCacheKey = () => 'engraving'; m.needsUpdate = true;
  c.userData.setReveal = (r, h) => { u.uReveal.value = r; u.uHuman.value = h; };
  return c;
}
function glowSprite(col, size = 1) {
  const t = canvasTex(128, 128, (g, w, h) => { const gr = g.createRadialGradient(w / 2, h / 2, 0, w / 2, h / 2, w / 2); gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.15, 'rgba(255,240,210,0.8)'); gr.addColorStop(0.45, 'rgba(255,190,110,0.18)'); gr.addColorStop(1, 'rgba(0,0,0,0)'); g.fillStyle = gr; g.fillRect(0, 0, w, h); });
  const m = new THREE.SpriteMaterial({ map: t, color: col, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, fog: false }); const sp = new THREE.Sprite(m); sp.scale.setScalar(size); sp.renderOrder = 20; return sp;
}
function buildRest() {
  const addL = (c) => { scene.add(c); X.loose.push(c); return c; };
  X.ragC = addL(makeCard(env, [tf.userData.views[1]])); X.marsC = addL(makeCard(env, [tf.userData.views[0]]));
  X.faces = {}; for (const [k, v] of [['tower', [FACES.tower]], ['sun', [FACES.sun, FACES.sunBurn]], ['robot', [FACES.robot]], ['red', [FACES.red]], ['gardener', [FACES.gardener]], ['magician', [FACES.magician]], ['star', [FACES.star]]]) X.faces[k] = addL(makeCard(env, v));
  X.faces.tower2 = X.faces.tower;
  const wf = ['magician', 'tower', 'star', 'sun', 'robot', 'red', 'gardener']; X.wheel = [];
  const wfaces = [FACES.magician, FACES.tower, FACES.star, FACES.sun, FACES.robot, FACES.red, FACES.gardener, tf.userData.views[1], tf.userData.views[0]];
  for (let i = 0; i < 18; i++) X.wheel.push(addL(makeCard(env, [wfaces[i % 9]])));
  X.engr = addL(engravingCard());
  X.foolTex = tf.userData.front.material.userData.u.mapC.value; const ft = new THREE.CanvasTexture(FACES.foolTurn); ft.colorSpace = THREE.SRGBColorSpace; ft.anisotropy = 8; X.foolTurnTex = ft;
  // the shared back (every face-down card) can glow in the dark
  const backMat = deck[5].userData.front.material;
  X.deckGlow = (k) => { if (backMat.userData.u) backMat.userData.u.uGlow.value.setRGB(1.0, 0.7, 0.3).multiplyScalar(k * 0.9); };
  X.backGlow = () => {};
  // the card worlds
  X.pops = { tower: towerPopup(), sun: sunPopup(), robot: robotPopup(), red: redPopup(), gardener: gardenerPopup() };
  for (const p of Object.values(X.pops)) { p.setOpen(0); scene.add(p.root); }
  // lights that the later sections use (always present, so no shader recompiles)
  // two extra lights for everything after the preview (each light costs every lit pixel, so they are shared):
  // popL for the cards and their worlds; aux for the singularity, the rocket, the bridge's candle, the tomato's shaft
  X.popL = new THREE.PointLight(0xff6a2a, 0, 2.6, 2); scene.add(X.popL);
  X.aux = new THREE.PointLight(0xffe0b0, 0, 3.0, 2); scene.add(X.aux);
  const auxAs = (col, range) => ({ get intensity() { return X.aux.intensity; }, set intensity(v) { if (v > 0 || X.aux.userData.owner === col) { X.aux.intensity = v; X.aux.color.setHex(col); X.aux.distance = range; X.aux.userData.owner = col; } }, position: X.aux.position });
  X.pointL = auxAs(0xffe0b0, 3.0); X.rocketL = auxAs(0xffc890, 2.2); X.candleL = auxAs(0xffb060, 3.5);
  X.spot = Object.assign(auxAs(0xe8ffb0, 4.0), { target: { position: new THREE.Vector3() } });
  const shaftT = canvasTex(64, 256, (g, w, h) => { const gr = g.createLinearGradient(0, 0, 0, h); gr.addColorStop(0, 'rgba(240,255,200,0.0)'); gr.addColorStop(0.3, 'rgba(240,255,200,0.35)'); gr.addColorStop(1, 'rgba(240,255,200,0.05)'); g.fillStyle = gr; g.fillRect(0, 0, w, h); });
  X.shaft = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.42, 3.0, 24, 1, true), new THREE.MeshBasicMaterial({ map: shaftT, transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide, color: new THREE.Color(0.55, 0.62, 0.42) }));
  X.shaft.renderOrder = 8; scene.add(X.shaft);
  // robots: three at each feast table, facing the Vikings across it; one attendant by the reading table
  X.robots = [];
  for (const [side, z] of [[-1, -2.35], [-1, -1.15], [-1, 1.15], [1, -2.35], [1, -1.15], [1, 1.15]]) { const r = new Robot(M, env); r.root.position.set(side * 1.12, 0, z); r.root.rotation.y = side * Math.PI / 2; r.userData = { side, z }; r.root.visible = false; scene.add(r.root); X.robots.push(r); }
  X.attendant = new Robot(M, env); X.attendant.root.position.set(0.5, 0, -5.64); X.attendant.root.rotation.y = -Math.PI / 2; X.attendant.root.visible = false; scene.add(X.attendant.root);
  // props
  X.plant = tomatoPlant(M); scene.add(X.plant); X.label = plantLabel(M, { stake: 0.3 }); scene.add(X.label);
  X.tomatoHeld = tomato(M, 0.034); scene.add(X.tomatoHeld); X.tomatoGift = tomato(M, 0.03); scene.add(X.tomatoGift);
  X.silvers = HALL.seats.map((_, i) => { const p = silver(M, i); scene.add(p); return p; });
  X.coin = silver(M, 0); X.coin.scale.setScalar(1.1); scene.add(X.coin);
  X.burin = burin(M); scene.add(X.burin);
  X.candleB = candle(M, 0.16, 77); scene.add(X.candleB);
  X.vortexPt = glowSprite(new THREE.Color(1.0, 0.9, 0.7), 0.3); scene.add(X.vortexPt);
  X.spark = glowSprite(new THREE.Color(1.0, 0.8, 0.5), 0.03); scene.add(X.spark);
  // her hand double (for the close-ups where she reaches his side of the table)
  const hd = new THREE.Group(); const palm = knob(M.glove, 0.052, 0.95, 0.62, 1.25, 10, 8); palm.position.set(0, 0.014, 0.02); hd.add(palm);
  const th = knob(M.glove, 0.022, 1, 1, 1.7, 8, 6); th.position.set(0.045, 0.012, 0.0); th.rotation.y = 0.4; hd.add(th);
  const cuff = new THREE.Mesh(new THREE.TorusGeometry(0.05, 0.02, 8, 18), M.fur); cuff.position.set(0, 0.024, -0.05); hd.add(cuff);
  const sleeve = new THREE.Mesh(new THREE.CylinderGeometry(0.062, 0.072, 0.5, 12), M.robe); sleeve.rotation.x = Math.PI / 2; sleeve.position.set(0, 0.03, -0.31); hd.add(sleeve);
  X.handDouble = hd; scene.add(hd);
  // the end plate (camera space): the title, engraved in gold on black
  const plateT = canvasTex(VERT ? 900 : 1600, VERT ? 1600 : 900, (g, w, h) => { const vs = VERT ? 0.95 : 1;
    g.fillStyle = '#050403'; g.fillRect(0, 0, w, h);
    g.textAlign = 'center'; g.textBaseline = 'middle';
    const gold = g.createLinearGradient(0, h * 0.3, 0, h * 0.6); gold.addColorStop(0, '#f4d995'); gold.addColorStop(1, '#b8862a');
    g.fillStyle = gold; g.font = `500 ${92 * vs}px "CormSC", serif`; g.fillText('RAGNARÖK', w / 2, h * (VERT ? 0.42 : 0.38));
    g.font = `italic ${54 * vs}px "CormMI", "Corm", serif`; g.fillStyle = '#d9b25f'; g.fillText('or reach for', w / 2, h * (VERT ? 0.47 : 0.47));
    g.fillStyle = gold; g.font = `500 ${92 * vs}px "CormSC", serif`; g.fillText('MARS', w / 2, h * (VERT ? 0.52 : 0.56));
    const ry = h * (VERT ? 0.575 : 0.655); g.strokeStyle = '#8a6a2a'; g.lineWidth = 2; g.beginPath(); g.moveTo(w / 2 - 210, ry); g.lineTo(w / 2 - 22, ry); g.moveTo(w / 2 + 22, ry); g.lineTo(w / 2 + 210, ry); g.stroke();
    g.save(); g.translate(w / 2, ry); g.rotate(Math.PI / 4); g.fillStyle = '#d9b25f'; g.fillRect(-7, -7, 14, 14); g.restore();
    g.font = '500 40px "CormSB", "Corm", serif'; g.fillStyle = '#cdb27a'; g.fillText('aditazzz', w / 2, h * (VERT ? 0.62 : 0.73));
  });
  const plateM = new THREE.MeshBasicMaterial({ map: plateT, transparent: true, depthTest: false, depthWrite: false, fog: false, toneMapped: false });
  X.endPlate = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), plateM); X.endPlate.renderOrder = 100; X.endPlate.visible = false; cam.add(X.endPlate);
  X.endPlate.userData.set = (k) => { const dz = 1.0, hh = 2 * dz * Math.tan(THREE.MathUtils.degToRad(cam.fov) / 2); X.endPlate.position.set(0, 0, -dz); X.endPlate.scale.set(hh * W / H, hh, 1); plateM.opacity = k; };
  // the finale
  X.head = buildFinale(env, M, { VIKS: VIKS_ALL });
  X.head.frame0 = X.head.frame; X.head.frame = (t) => {};      // the finale poses itself after the camera is placed (in renderAt)
  Object.assign(X, { VERT, vfix, T, scene, cam, st, hall, seer, man, rocket, staff, vikings, guards, tf, deck, hemi, M, env, scenes: { cur: scene }, finish: { uFlash: 0, uFade: 1, flashCol: new THREE.Color(1, 1, 1) }, hemiK: 0.18, flare: 0 });
}

// ---------------------------------------------------------------- the cards' choreography (world space)
const qOf = (rx, ry, rz, order = 'YXZ') => new THREE.Quaternion().setFromEuler(new THREE.Euler(rx, ry, rz, order));
const FACE_DOWN = (yaw = 0) => qOf(Math.PI / 2, yaw, 0);
function place(card, p, qq) { card.position.copy(p); card.quaternion.copy(qq); card.visible = true; }
// the fan: slots on an arc, cards lying face down with their tops pointing at the man
const FAN = { cx: 0, cz: HALL.table.z - 0.24, r: 0.34, a0: -1.13, a1: 1.13 };
const fanSlot = (k, n = 22) => { const a = lerp(FAN.a0, FAN.a1, k / (n - 1)); return { p: V(FAN.cx + FAN.r * Math.sin(a), TOP + k * 0.0007, FAN.cz + FAN.r * Math.cos(a)), a }; };
const STACK = V(-0.25, TOP, HALL.table.z - 0.17);
// spring shuffle: cards fly in a ribbon arc from one hand's stack to the other's
function springPos(tt, t0, dir, hands, i, n = 22, gap = 0.034, fly = 0.22) {
  const from = dir > 0 ? hands[0] : hands[1], to = dir > 0 ? hands[1] : hands[0];
  const ts = t0 + i * gap; const u = clamp((tt - ts) / fly);
  if (u <= 0) return { p: from.clone().add(V(0, (n - i) * 0.0016, 0)), q: qOf(Math.PI / 2 - 0.25 * dir, 0, 0.12 * dir), u };
  if (u >= 1) return { p: to.clone().add(V(0, i * 0.0016, 0)), q: qOf(Math.PI / 2 + 0.25 * dir, 0, -0.12 * dir), u };
  const e = easeIO(u); const p = from.clone().lerp(to, e); p.z += Math.sin(Math.PI * e) * 0.06; p.y += Math.sin(Math.PI * e) * 0.16 + (1 - e) * (n - i) * 0.0016 + e * i * 0.0016;
  return { p, q: qOf(Math.PI / 2 - 0.25 * dir + 0.5 * dir * e, 0, 0.12 * dir - 0.24 * dir * e + Math.sin(Math.PI * e) * 0.35 * dir), u };
}

// ---------------------------------------------------------------- performances
function seerPose(t) {
  const ts = (t > 9.3 && t < 13.2) || (t > 19.4 && t < 21) || (t > 23.6 && t < 27.6) ? t : step2(t);
  const p = { lean: 0.12, headPitch: 0.1, look: [0, 1.25, HALL.stool.z], lookK: 0.75 };
  // right hand (arms[0], world -x): the two-faced card, then the deck
  const restR = [-0.17, 0.66, -6.42], restL = [0.17, 0.66, -6.42];
  let hr = track([[0, [-0.05, 1.04, -6.42]], [5.55, [-0.05, 1.04, -6.42]], [6.2, [-0.03, 0.8, -6.12]], [6.85, [0.0, 0.79, -5.92], lin], [7.3, restR], [12.35, restR], [12.6, [-0.3, 0.8, -6.08]], [12.72, [-0.22, 0.95, -6.1]], [12.87, [-0.12, 0.775, -6.02], easeIn], [13.4, [-0.14, 0.8, -6.05]], [14.2, restR],
    [19.45, restR], [19.7, [-0.3, 0.8, -6.08]], [20.65, [0.29, 0.79, -6.08], lin], [21.2, [0.2, 0.86, -6.2]], [21.6, restR], [23.6, restR], [23.85, [-0.02, 0.8, -6.0]], [24.05, [-0.13, 1.06, -6.38]], [27.3, [-0.13, 1.06, -6.38]], [27.6, [-0.13, 1.0, -6.38]]], ts);
  let hl = track([[0, restL], [9.35, restL], [9.58, [0.2, 0.97, -6.2]], [9.7, [0.17, 0.775, -6.12], easeIn], [10.3, [0.18, 0.8, -6.14]], [11.0, restL], [23.6, restL], [23.85, [0.04, 0.8, -6.0]], [24.05, [0.13, 1.06, -6.38]], [27.6, [0.13, 1.06, -6.38]]], ts);
  p.lean = track([[0, 0.12], [5.55, 0.12], [6.2, 0.38], [7.0, 0.42], [7.4, 0.15], [9.4, 0.15], [9.7, 0.33], [10.5, 0.15], [12.5, 0.18], [12.87, 0.33], [13.6, 0.15], [19.5, 0.2], [19.8, 0.42], [20.7, 0.42], [21.3, 0.12], [23.8, 0.12], [23.95, 0.3], [24.1, 0.12]], ts);
  p.handsW = [hr, hl];
  p.look = t < 5.5 ? [-0.05, 1.2, -6.33] : t < 18.4 ? [0, 0.9, -6.0] : t < 19.5 ? [0, 1.27, HALL.stool.z] : t < 21.4 ? [0, 0.78, -6.0] : t < 23.8 ? [0, 1.25, HALL.stool.z] : [0, 1.06, -6.38];
  p.lookK = t >= 18.4 && t < 19.5 ? 1 : 0.8;
  if (t >= 18.4 && t < 19.5) p.headPitch = -0.05;
  seer.pose(p); seer.setFace(t >= 18.5 ? 'open' : 'closed');
  return ts;
}
function manPose(t) {
  const ts = (t > 21.8 && t < 23.2) ? t : step2(t);
  const onRocket = [-0.36, 0.62, HALL.stool.z + 0.02];
  let hr = track([[0, [0.22, 0.79, -5.68]], [21.75, [0.22, 0.79, -5.68]], [22.15, [0.16, 0.88, -5.86]], [22.85, [-0.04, 0.87, -5.9], lin], [23.4, [0.22, 0.79, -5.68]]], ts);
  if (ts > 22.15 && ts < 22.9) hr = [hr[0] + 0.05 * Math.sin((ts - 22.15) * 9.0), hr[1], hr[2] + 0.02 * Math.sin((ts - 22.15) * 6.0)];
  const lean = track([[0, 0.12], [21.8, 0.12], [22.2, 0.34], [22.9, 0.34], [23.4, 0.1], [25.1, 0.1], [25.2, 0.04], [25.6, 0.1]], ts);
  let look = t < 5.4 ? [-0.05, 1.2, -6.33] : t < 7.3 ? [0, 0.77, -5.8] : (t >= 21.8 && t < 23.2) ? [0.05, 0.77, -5.9] : t >= 23.6 ? [0, 1.06, -6.38] : [0, 1.32, HALL.seat.z];
  for (const [t0, dir] of [[24.12, 1], [26.2, -1]]) if (ts >= t0 - 0.1 && ts < t0 + 1.1) { const u = easeIO(clamp((ts - t0) / 0.95)); look = [dir * lerp(0.13, -0.13, u), 1.1 + 0.12 * Math.sin(Math.PI * u), -6.33]; }
  man.pose({ lean, headPitch: 0.05, handsW: [hr, onRocket], look, lookK: 0.85 }); man.setFace('smile');
}
function vikingPose(v, t) {
  const s = v.userData.seat; const near = T.stomps.concat(T.heys).some((e) => Math.abs(t - e) < 0.6);
  const ts = near ? t : step2(t + v.userData.lag);
  const side = s.side; const tx = side * (HALL.feast.x + 0.2);
  // turns toward the reading on the first downbeat of the gap, leans in on the next
  const turn = sstep(14.85, 14.95, ts), leanIn = sstep(17.15, 17.27, ts);
  const fireLook = [0, 1.0 + 0.15 * Math.sin(v.userData.ph), s.z + v.userData.yaw0 * 2], readLook = [0, 1.15, -6.1];
  const look = mixV(fireLook, readLook, turn);
  // drumming: both fists come down on each stomp; a big two-fisted slam on each HEY
  let lift = 0, z = 0;
  for (const e of T.stomps) lift = Math.max(lift, (ts > e - 0.26 && ts < e) ? Math.sin(Math.PI * (ts - (e - 0.26)) / 0.26) * 0.2 : 0);
  let raise = 0; for (const e of T.heys) { if (ts >= e - 0.5 && ts < e) raise = Math.max(raise, easeOut((ts - (e - 0.5)) / 0.42)); }
  const y = HALL.feast.top + 0.03 + lift + raise * 0.42;
  z = raise * 0.12;
  const hz = s.z;
  const hands = [[tx, y, hz - 0.16 * side * 0 + 0.17], [tx, y, hz - 0.17]].map(([x, yy, zz]) => [x + side * z, yy, zz]);
  v.pose({ lean: 0.05 + 0.16 * leanIn + 0.1 * raise - 0.05 * Math.sin(ts * 1.3 + v.userData.ph) * (1 - turn), handsW: hands, look, lookK: 0.85, headRoll: 0.04 * Math.sin(v.userData.ph * 3) });
}
function cardsAt(t) {
  const ts = (t > 19.4 && t < 21) || (t > 23.7 && t < 27.6) ? t : step2(t);
  seer.root.updateMatrixWorld(true);
  const hR = seer.arms[0].hand.localToWorld(V(0, 0.045, 0)), hL = seer.arms[1].hand.localToWorld(V(0, 0.045, 0));
  // --- the two-faced card: held up, tilts and flips with the lightning, then laid face down and slid to his place
  const [a, b] = [T.thunder[0], T.thunder[1]];
  const flip = clamp((ts - a) / 0.32) * (1 - clamp((ts - b) / 0.32));
  const tilt = 0.42 * Math.sin(Math.PI * clamp((ts - a) / 0.5)) - 0.42 * Math.sin(Math.PI * clamp((ts - b) / 0.5));
  tf.userData.setFlip(flip);
  const tip = seer.arms[0].hand.localToWorld(V(0, 0.155, 0));
  if (ts < 5.55) place(tf, tip, qOf(-0.08, tilt * 0.9, 0.03));
  else if (ts < 6.2) { const u = easeIO((ts - 5.55) / 0.65); place(tf, tip.clone().lerp(hR.clone().add(V(0, 0.006, 0)), u), new THREE.Quaternion().slerpQuaternions(qOf(-0.08, 0, 0.03), FACE_DOWN(0), u)); }
  else { const u = easeOut(clamp((ts - 6.25) / 0.75)); place(tf, V(lerp(-0.03, 0.0, u), TOP, lerp(-6.08, -5.6, u)), FACE_DOWN(0.04 * u)); }
  // --- the deck: 20 cards stacked at her right; card 1 (ember) on top; card 0 (gold) waits in her left hand
  const fanStart = 19.72, gap = 0.041;
  const gatherT = 23.85, ups = [23.85, 24.05];
  const handsMid = [V(0.13, 1.07, -6.35), V(-0.13, 1.07, -6.35)];
  const order = [...Array(20).keys()].map((i) => i + 2).concat([1, 0]);    // fan order: stack bottom first, then the ember card, then the gold one
  const sweepX = lerp(-0.3, 0.29, clamp((ts - fanStart + 0.05) / (21 * gap + 0.1)));
  deck.forEach((c, i) => {
    let p, qq;
    const k = order.indexOf(i); const slot = fanSlot(k); const tLay = fanStart + k * gap;
    const inStack = V(STACK.x, TOP + (21 - i) * 0.0017, STACK.z);
    if (i === 0) {           // the gold card
      if (ts < 9.6) { p = hL.clone().add(V(0, 0.01, 0.02)); qq = FACE_DOWN(0.2); }
      else if (ts < 20.1) { p = V(0.17, TOP, -6.12); qq = FACE_DOWN(-0.15); }
      else p = null;
    } else if (i === 1) {    // the ember card
      if (ts < 12.6) { p = inStack; qq = FACE_DOWN(0.05); }
      else if (ts < 12.87) { p = hR.clone().add(V(0, 0.006, 0.02)); qq = FACE_DOWN(-0.2); }
      else if (ts < 19.95) { p = V(-0.12, TOP, -6.02); qq = FACE_DOWN(0.25); }
      else p = null;
    } else { p = inStack; qq = FACE_DOWN(0.05 * Math.sin(i * 7)); }
    // the sweep: under the hand until laid, then at its slot
    if (ts >= fanStart - 0.2 && ts < gatherT) {
      if (p === null || ts >= fanStart - 0.05) {
        if (ts < tLay) { p = V(sweepX, TOP + (21 - k) * 0.0017 * 0.6, FAN.cz + FAN.r * Math.cos(Math.asin(clamp(sweepX / FAN.r, -1, 1)))); qq = FACE_DOWN(Math.asin(clamp(sweepX / FAN.r, -1, 1))); }
        else { const u = easeOut(clamp((ts - tLay) / 0.12)); p = slot.p; qq = FACE_DOWN(slot.a); }
      }
    }
    if (p === null) { p = V(sweepX, TOP, -6.05); qq = FACE_DOWN(0); }
    // gather and shuffle
    if (ts >= gatherT) {
      const u = easeIO(clamp((ts - gatherT) / 0.2)), u2 = easeIO(clamp((ts - ups[1]) / 0.15));
      const sp1 = springPos(ts, 24.12, 1, handsMid, k), sp2 = springPos(ts, 26.2, -1, handsMid, k);
      if (ts < ups[1]) { p = slot.p.clone().lerp(V(0, TOP + k * 0.0016, -6.05), u); qq = new THREE.Quaternion().slerpQuaternions(FACE_DOWN(slot.a), FACE_DOWN(0), u); }
      else if (ts < 24.12) { p = V(0, TOP + k * 0.0016, -6.05).lerp(handsMid[0].clone().add(V(0, (22 - k) * 0.0016, 0)), u2); qq = FACE_DOWN(0); }
      else if (ts < 26.2) { p = sp1.p; qq = sp1.q; }
      else { p = sp2.p; qq = sp2.q; }
    }
    place(c, p, qq);
  });
  // glows: the gold card flares on "Good", the ember card on "Bad"; both fade as the sweep takes them
  const gk = (ts >= 9.7 ? 0.65 + 1.6 * decay(ts, 9.7, 0.35) : 0) * (1 - sstep(19.95, 20.35, ts)) + (ts >= 9.45 && ts < 9.7 ? 0.25 : 0);
  const ek = (ts >= 12.87 ? 0.65 + 1.6 * decay(ts, 12.87, 0.35) : 0) * (1 - sstep(19.85, 20.25, ts));
  deck[0].userData.setGlow(new THREE.Color(1.0, 0.72, 0.25), gk); deck[1].userData.setGlow(new THREE.Color(1.0, 0.25, 0.06), ek);
  gLight.visible = eLight.visible = ts > 9.3 && ts < 20.5;
  gLight.position.copy(deck[0].position).add(V(0, 0.24, 0.08)); gLight.intensity = 0.32 * gk;
  eLight.position.copy(deck[1].position).add(V(0, 0.24, 0.08)); eLight.intensity = 0.32 * ek;
}
function propsAt(t) {   // cups and platters jump on the stomps and HEYs
  let j = 0; for (const e of T.heys) if (t >= e && t < e + 0.32) j = Math.max(j, Math.sin(Math.PI * (t - e) / 0.32) * 0.05);
  for (const e of T.stomps) if (t >= e && t < e + 0.2) j = Math.max(j, Math.sin(Math.PI * (t - e) / 0.2) * 0.015);
  for (const p of hall.userData.feastProps) p.position.y = p.userData.base.y + j * (0.7 + 0.6 * Math.abs(Math.sin(p.userData.base.z * 3.1)));
}

// ---------------------------------------------------------------- shots
const SHOTS = [
  { t: 0.0, cam: (t, u) => { const c = tf.position; return [V(c.x + lerp(-0.025, -0.035, u), c.y + 0.035, c.z + lerp(0.37, 0.31, easeOut(u))), V(c.x, c.y + 0.03, c.z), 32]; } },   // the card
  { t: 3.86, cam: (t, u) => [V(lerp(0.34, 0.3, u), 1.62, lerp(-6.99, -6.95, u)), V(-0.1, 1.05, -4.6), 46] },                                     // reveal: behind her, him backlit by the hearth
  { t: 5.5, cam: (t, u) => [V(lerp(0.64, 0.6, u), lerp(1.26, 1.24, u), lerp(-6.47, -6.43, u)), V(0.0, 0.97, -5.72), 40] },                         // she lays it face down at his place
  { t: 7.45, cam: (t, u) => [V(0, lerp(2.3, 2.12, u), lerp(11.6, 10.4, easeOut(u))), V(0, 1.2, -6), 40] },                                        // the hall: the fire flares on the drums
  { t: 9.55, cam: (t, u) => [V(lerp(0.38, 0.35, u), 1.48, lerp(-4.85, -4.92, u)), V(0.08, 0.86, -6.15), 38] },                                     // "Good news." over his shoulder
  { t: 10.352, cam: (t, u) => [V(lerp(0.46, 0.4, u), lerp(0.92, 0.9, u), lerp(-5.72, -5.8, u)), V(0.17, 0.765, -6.12), 34] },                       // the gold card glowing on the cloth
  { t: 12.637, cam: (t, u) => [V(0, lerp(1.34, 1.3, u), -6.05), V(0, 0.76, -6.05), 44, V(0, 0, -1)] },                                             // "Bad news." straight down on the table
  { t: 13.75, cam: (t, u) => [V(0.9, 1.2, lerp(-3.55, -3.7, u)), V(2.15, 1.08, 4.5), 36] },                                                         // the Vikings turn on the downbeat
  { t: 17.208, cam: (t, u) => [V(0.25, lerp(2.35, 2.3, u), lerp(-7.5, -7.4, u)), V(0, 0.95, 1.5), 44] },                                             // ...and lean in
  { t: 18.4, cam: (t, u) => [V(0.08, 1.28, lerp(-5.74, -5.8, u)), V(0, 1.13, -6.64), 32] },                                                        // "I've seen what's coming." her eyes open
  { t: 19.55, cam: (t, u) => [V(lerp(0.42, 0.36, u), lerp(1.62, 1.55, u), -5.3), V(0.0, 0.76, -6.08), 40] },                                       // the deck spreads across the table
  { t: 22.1, cam: (t, u) => [V(0, lerp(1.47, 1.42, u), -5.93), V(0, 0.76, -5.93), 44, V(0, 0, -1)] },                                        // "Choose." his hand over the cards, his face beyond
  { t: 22.9, cam: (t, u) => [V(-0.9, 0.98, -3.45), V(-2.05, 0.95, 6.0), 42] },                                                                     // the stomps
  { t: 23.8, cam: (t, u) => [V(0.0, lerp(1.62, 1.6, u), lerp(-5.72, -5.76, u)), V(0, 1.02, -6.38), 40] },                                          // "Shuffle the deck!" from above her hands
  { t: 25.199, cam: (t, u) => [V(0, lerp(3.6, 3.75, u), lerp(-4.9, -5.1, u)), V(0, 0.6, 3.0), 46] },                                               // HEY: the whole hall slams
  { t: 26.13, cam: (t, u) => [V(lerp(0.38, 0.35, u), lerp(1.31, 1.3, u), lerp(-6.36, -6.3, u)), V(0.0, 1.16, -5.2), 38] },                       // "Shuffle the deck!" on him, his eyes on the cards
  { t: 27.487, cam: (t, u) => [V(0, lerp(1.75, 1.7, u), lerp(9.2, 8.9, u)), V(0, 1.0, -6), 44] },                                                  // HEY: from the near end of the hall
];
function T0(k) { return k === 'hey0' ? 25.199 : 27.487; }
function camAt(t) {
  let i = 0; while (i + 1 < SHOTS.length && t >= SHOTS[i + 1].t) i++;
  const s = SHOTS[i], t1 = i + 1 < SHOTS.length ? SHOTS[i + 1].t : T.preview.end;
  let [p, look, fov, up] = s.cam(t, clamp((t - s.t) / (t1 - s.t)));
  if (VERT) [p, look, fov] = vfix('p' + s.t.toFixed(2), p, look, fov, up);
  if (COVER) { const dir = p.clone().sub(look).normalize(); p = p.clone().addScaledVector(dir, COVER.back); look = look.clone().add(V(0, COVER.dy, 0)); p.y += COVER.dy; fov = fov * COVER.fovK; }
  return { p, look, fov, up: up || V(0, 1, 0), i };
}
function shake(t) { let k = 0; for (const e of T.heys) k += 0.012 * decay(t, e, 0.12); for (const e of T.stomps) k += 0.004 * decay(t, e, 0.08); return k; }

// ---------------------------------------------------------------- per frame
let lastShadowStep = null;
// Captions (Oct 26 pass): smaller and lower, so they don't sit on the story. y = offset below the frame centre in half-heights.
// Vertical: in the lower middle, clear of the Shorts/Reels interface. Per-shot overrides (key = shot start, 'p' prefix for
// the preview's shots) move a caption to the top (negative y) or to one side (x = -1 left, +1 right) where the action is low.
const CAP_OVR = {
  '31.60': { x: -1 }, '77.35': { x: -1 }, '140.92': { x: -1 }, '195.72': { x: -1 },   // his coin lands bottom right
  '48.30': { y: -0.74, x: 1 },                                                         // the flames climbing
  '62.91': { y: 0.05 }, '65.20': { y: 0.1 },                                             // on the dark wall between the gold roof and the robots, clear of the sun and the one left outside
  '97.14': { y: -0.74, x: 1 },  '99.39': { y: -0.74, x: 1 },                            // the robots' oars
  '112.30': { y: -0.74, x: 1 },                                                        // GREENLAND
  '117.57': { y: -0.74 }, '128.91': { x: 1 },                                           // the Viking in the card; the tomato gift
  '158.29': { y: -0.74 }, '160.60': { y: -0.74 }, '162.88': { x: -1 }, '165.14': { x: -1 },   // her hand on his card; the engraving; the burin
  '212.20': { x: 1 }, '216.40': { x: 1 }, '218.80': { y: -0.74, x: 1 }, '221.04': { y: 0.25 },  // the robot at his heel; the crowd on the cliff
};
const CAPV_OVR = {
  '30.20': { y: -0.62 }, '31.60': { y: -0.62 }, '77.35': { y: -0.62 }, '140.92': { y: -0.62 }, '195.72': { y: -0.62 },   // silver and his coin on the table
  '39.77': { y: -0.62 }, '44.63': { x: 1 }, '48.30': { y: -0.62, x: -1 }, '52.88': { y: -0.62 },                     // his hand; the rocket; the flames; his grin
  '61.95': { y: -0.62 }, '62.91': { y: -0.62, x: -1 }, '65.20': { y: -0.62, x: -1 },                                 // the hall of plenty and its gate
  '97.14': { y: -0.62 }, '99.39': { y: -0.62 }, '106.22': { y: -0.62, x: 1 }, '117.57': { y: -0.62 },                 // the oars; the planter; the Viking in the card
  '119.30': { x: 1 }, '120.48': { x: 1 }, '128.91': { x: 1 },                                                       // the tomato plant; the tomato gift
  '158.29': { y: -0.62 }, '160.60': { y: -0.62 }, '162.88': { y: 0.54 }, '165.14': { x: 1 },                          // her hand; the engraving; the burin
  '212.20': { x: 1 }, '221.04': { y: -0.1 },                                                                        // him at the edge; the crowd on the cliff
};
function placeCaption(L, key, push, k, tanH, dz) {
  const o = (VERT ? CAPV_OVR : CAP_OVR)[key] || {}, yF = o.y ?? CAP.y, ax = o.x ?? 0;
  let x = 0; if (ax) { const halfW = dz * tanH * (W / H); x = ax * Math.max(0, halfW * 0.9 - L.userData.width * k / 2); }
  L.position.set(x, -dz * tanH * yF + push * k, -dz);                     // an outgoing line rises out of the new one's way
}
const CUT = 27.487;   // frames before this are the approved preview; from here on, full.js
let rocketTuned = false;
function renderFull(t) {
  gLight.visible = eLight.visible = false;
  if (!rocketTuned) { rocketTuned = true; const seen = new Set(); rocket.traverse((o) => { const m = o.material; if (o.isMesh && m && !seen.has(m) && m.metalness === 1 && m.roughness === 0.2) { seen.add(m); m.roughness = 0.48; m.metalness = 0.55; m.envMapIntensity = 1.6; } }); console.log('rocket steel tuned', seen.size); }
  const sstp = Math.floor(t * 15 + 1e-6); if (sstp !== lastShadowStep) { st.renderer.shadowMap.needsUpdate = true; lastShadowStep = sstp; }
  frameFull(t);
  const S = X.scenes.cur, inHall = S === scene;
  if (cam.parent !== S) S.add(cam);
  const c = camOverride(t, camFull(t)); const sh = inHall ? shake(t) : 0;
  cam.up.copy(c.up); cam.position.copy(c.p).add(V(Math.sin(t * 71) * sh, Math.cos(t * 53) * sh, 0)); cam.lookAt(c.look); cam.fov = c.fov; cam.updateProjectionMatrix();
  let fk = 0;
  if (X.rocketOnTable) { rocket.position.set(-0.13, HALL.table.top + 0.002, -5.6); rocket.rotation.set(-0.12, 2.4, 0.08); } else { rocket.position.set(-0.43, 0, HALL.stool.z + 0.04); rocket.rotation.set(0, 2.4, 0); }
  X.rocketOnTable = false;
  const near = inHall ? 0.02 : 0.05, far = inHall ? 120 : 3000; if (cam.near !== near || cam.far !== far) { cam.near = near; cam.far = far; cam.updateProjectionMatrix(); }
  if (inHall) {
    RIM.value.set(0xff8a40); RIM_AMT.value = 0.12;
    hemi.intensity = X.hemiK;
    const fire = hall.userData.fire; fire.userData.flare = X.flare + 0.12 * T.stomps.reduce((a, e) => a + decay(t, e, 0.1), 0) * 0;
    hall.userData.flash(0);
    hall.userData.update(X.freeze ?? t, cam, H, cam.fov);
    for (const p of Object.values(X.pops)) p.setTint(new THREE.Color(1, 1, 1));
  } else {
    RIM.value.set(0xff7a50); RIM_AMT.value = 0.2;
    fk = X.head.frame0(t, cam);
  }
  // captions (as in the preview)
  const tanH = Math.tan(THREE.MathUtils.degToRad(cam.fov) / 2), k = tanH / Math.tan(THREE.MathUtils.degToRad(20)); const dz = 5.2;
  lines.forEach((L, i) => { const on = !CLEAN && t >= L.userData.s && t < L.userData.e; L.visible = on;
    if (on) { const kick = T.heys.reduce((a, e) => a + (t >= e ? Math.exp(-(t - e) / 0.14) : 0), 0);
      // when the next line arrives while this one is still burning, this one rises out of its way
      const nx = lines[i + 1]; let push = 0; if (nx && t > nx.userData.s + 0.25) push = easeIO((t - (nx.userData.s + 0.25)) / 0.45) * (L.userData.height / 2 + nx.userData.height / 2 + 0.1);
      placeCaption(L, c.t0.toFixed(2), push, k, tanH, dz); L.scale.setScalar(k * (1 + 0.05 * kick)); L.userData.kick(0.55 * kick); L.userData.update(t, H, cam.fov / k * 1.0); } });
  st.finish.uniforms.uFlash.value = X.finish.uFlash + 0.025 * fk; st.finish.uniforms.uFlashCol.value.copy(X.finish.flashCol);
  st.finish.uniforms.uFade.value = X.finish.uFade;
  st.render(S, cam, t);
  return st.jpeg(0.94);
}
window.renderAt = (t) => {
  if (t >= CUT) return renderFull(t);
  const sstp = Math.floor(t * 15 + 1e-6); if (sstp !== lastShadowStep) { st.renderer.shadowMap.needsUpdate = true; lastShadowStep = sstp; }
  // performances first (some shots frame a prop)
  seerPose(t); manPose(t); for (const v of vikings) vikingPose(v, t); cardsAt(t); propsAt(t);
  const c = camOverride(t, camAt(t)); const sh = shake(t);
  cam.up.copy(c.up); cam.position.copy(c.p).add(V(Math.sin(t * 71) * sh, Math.cos(t * 53) * sh, 0)); cam.lookAt(c.look); cam.fov = c.fov; cam.updateProjectionMatrix();
  // light: lightning through the smoke hole, the fire flaring on the drums and the HEYs
  const lk = lightning(t); hall.userData.flash(lk); hemi.intensity = 0.18 + 0.9 * lk; hemi.color.setRGB(lerp(0.23, 0.6, clamp(lk)), lerp(0.29, 0.7, clamp(lk)), lerp(0.42, 1.0, clamp(lk)));
  const fire = hall.userData.fire; fire.userData.flare = 1.1 * decay(t, T.drums, 0.9) + 0.75 * decay(t, T.heys[0], 0.45) + 0.75 * decay(t, T.heys[1], 0.45) + 0.12 * T.stomps.reduce((s, e) => s + decay(t, e, 0.1), 0);
  hall.userData.update(t, cam, H, cam.fov);
  // captions: constant size on screen whatever the lens; lower third
  const tanH = Math.tan(THREE.MathUtils.degToRad(cam.fov) / 2), k = tanH / Math.tan(THREE.MathUtils.degToRad(20)); const dz = 5.2;
  for (const L of lines) { const on = !CLEAN && t >= L.userData.s && t < L.userData.e; L.visible = on;
    if (on) { const kick = T.heys.reduce((a, e) => a + (t >= e ? Math.exp(-(t - e) / 0.14) : 0), 0);
      placeCaption(L, 'p' + SHOTS[c.i].t.toFixed(2), 0, k, tanH, dz); L.scale.setScalar(k * (1 + 0.05 * kick)); L.userData.kick(0.55 * kick); L.userData.update(t, H, cam.fov / k * 1.0); } }
  st.finish.uniforms.uFlash.value = 0.05 * clamp(lk); st.finish.uniforms.uFlashCol.value.setRGB(0.75, 0.85, 1.0);
  st.finish.uniforms.uFade.value = 1 - sstep(T.preview.end - 0.3, T.preview.end, t);
  st.render(scene, cam, t);
  return st.jpeg(0.94);
};

(async () => {
  await loadFilmFonts();
  T = await fetch('/data/timing.json').then((r) => r.json());
  FACES = await loadFaces();
  SHOTS[14].t = T.heys[0]; SHOTS[16].t = T.heys[1];
  build();
  initFull(X);
  window.DUR = T.dur; window.T = T; window.__dbg = { scene, cam, seer, man, deck, tf, hall, st, vikings, X, KEYS }; window.ready = true;
})().catch((e) => { console.log('INIT ERROR', e.stack || e); });
