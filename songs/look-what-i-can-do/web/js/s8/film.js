// Look What I Can Do · S8, the final chorus (136.533–151.767), in the world of her video "Ragnarök or Reach for Mars":
// the carved, painted longhouse lit by one long hearth, the wooden puppets moving on twos, the gold-on-obsidian deck and
// the cards that open into pop-up worlds of cut, gilded card, now playing her own videos. renderTime(t) draws the frame
// at song time t, deterministically (puppets on twos, camera, fire and light at 30).
//   A 136.53 Look what I can do!   down the hall: embers from the hearth settle into gilded letters over the fire
//   B 138.45 Look what I can do!   the seeress, close: XXV THE MAKER in her hand, its carved words igniting as sung
//   C 139.95 I made a song about myself / And now I'm in it too!   she lays the card down; it opens into a toy theatre
//            whose stage shows THIS VIDEO (frame inside frame); the man leans in (now he's in it too); we fall in, twice
//   D 143.65 Look what I can do!   the man with the rocket, close, grinning over his Tower: its windows spell the hook
//   E 145.50 Look what I can do!   four worlds of her videos spring up across the table, one carved word each
//   F 147.08 I built an entire universe   up and back: worlds on every feast table and her videos orbiting in the smoke
//   G 149.18 And left it a five-star review!   XXVI THE REVIEW slapped down; five stars ignite, one per beat; to black
import * as THREE from 'three';
import { FullScreenQuad } from 'three/addons/postprocessing/Pass.js';
import { makeStage } from './stage.js';
import { RIM, RIM_AMT, clamp, lerp, sstep, easeIO, easeOut, easeIn, rng, canvasTex } from './lib.js';
import { hallEnv, loadFilmFonts } from './lib2.js';
import { mats, TechKing, Seeress, Viking, makeStaff, shadows } from './puppets.js';
import { makeRocket } from './rocket.js';
import { makeCard } from './cards.js';
import { drawTower } from './cards2.js';
import { buildHall, HALL } from './hall.js';
import { emberLine } from './embers.js';
import { mergeStatic } from './merge.js';
import * as WD from './worlds.js';

const q = new URLSearchParams(location.search);
const W = +q.get('w') || 1920, H = +q.get('h') || 1080;
const st = makeStage(W, H, { exposure: 1.12, bloom: [0.5, 0.55, 0.86] });
st.renderer.shadowMap.enabled = true; st.renderer.shadowMap.type = THREE.PCFShadowMap;
const env = hallEnv(st.renderer); const M = mats(env);
const V = (x, y, z) => new THREE.Vector3(x, y, z);
const TOP = HALL.table.top + 0.0013, TZ = HALL.table.z;
const SEER = V(0, HALL.dais.y, HALL.seat.z + 0.05), MAN = V(0, 0, HALL.stool.z);
const SEER_REST = { R: [-0.17, 0.66, -6.42], L: [0.17, 0.66, -6.42] };
const MAN_REST = [0.22, 0.79, -5.68], ON_ROCKET = [-0.36, 0.62, HALL.stool.z + 0.02];
const T0 = 136.533333, T1 = 151.766667;

// ---------------------------------------------------------------- timeline helpers
const step2 = (t) => Math.floor(t * 15 + 1e-6) / 15;
const ramp = (t, a, b, e = easeIO) => e(clamp((t - a) / (b - a)));
const lin = (x) => clamp(x);
const decay = (t, t0, tau) => t < t0 ? 0 : Math.exp(-(t - t0) / tau);
function track(keys, t, ease = easeIO) {
  if (t <= keys[0][0]) return keys[0][1];
  for (let i = 1; i < keys.length; i++) { const [t1, v1, e] = keys[i]; if (t < t1) { const [t0, v0] = keys[i - 1]; const u = (e || ease)((t - t0) / (t1 - t0)); return mixV(v0, v1, u); } }
  return keys[keys.length - 1][1];
}
function mixV(a, b, u) { if (Array.isArray(a)) return a.map((x, i) => mixV(x, b[i], u)); return a + (b - a) * u; }
const qOf = (rx, ry, rz, order = 'YXZ') => new THREE.Quaternion().setFromEuler(new THREE.Euler(rx, ry, rz, order));
const FACE_DOWN = (yaw = 0) => qOf(Math.PI / 2, yaw, 0), FACE_UP = (yaw = 0) => qOf(-Math.PI / 2, yaw, 0);   // face up: readable from his side
function place(card, p, qq, s = 1) { card.position.copy(p); card.quaternion.copy(qq); card.scale.setScalar(s); card.visible = true; }

// ---------------------------------------------------------------- timing (this song's words)
const TM = {};
async function loadTiming() {
  const lines = await fetch('/data/timed.json').then((r) => r.json()); const bt = await fetch('/data/beats.json').then((r) => r.json());
  const fin = lines.filter((L) => L.sec === 'FINAL');
  TM.hooks = fin.filter((L) => L.text.startsWith('Look')).map((L) => ({ s: L.s, e: L.e, wt: L.wt, words: L.words }));
  const ln = (sub) => fin.find((L) => L.text.includes(sub));
  TM.song = ln('song about myself'); TM.inIt = ln('in it too'); TM.universe = ln('universe'); TM.review = ln('five-star');
  TM.beats = bt.beats.filter((b) => b > 135 && b < 153);
  TM.starBeats = TM.beats.filter((b) => b >= TM.review.s - 0.01).slice(0, 5);
}

// ---------------------------------------------------------------- the world
const VIKS = [
  { beard: '#a8481e', hair: 'long', beardStyle: 'long', tunic: '#3f5a34', trim: ['#c9a23a', '#7a1c14'], cloak: '#2a2622', fur: 'dark' },
  { beard: '#d9b56a', hair: 'bald', beardStyle: 'forked', tunic: '#7a2a22', trim: ['#e0c27a', '#1f3a6a'], cloak: '#3a3226', fur: 'light' },
  { beard: '#4a3426', hair: 'tied', beardStyle: 'braided', tunic: '#2e4a6a', trim: ['#b88a3a', '#3a1a10'], cloak: '#1e1c1a', fur: 'dark' },
  { beard: '#8a8680', hair: 'long', beardStyle: 'long', tunic: '#5a4a2a', trim: ['#7a1c14', '#d8c08a'], cloak: '#2a2a30', fur: 'dark' },
  { beard: '#c46a2a', hair: 'tied', beardStyle: 'forked', tunic: '#4a2a4a', trim: ['#d8b84a', '#2e5a34'], cloak: '#2a1e18', fur: 'light' },
  { beard: '#2a1e16', hair: 'bald', beardStyle: 'long', tunic: '#7a5a2a', trim: ['#1f3a6a', '#e0d6c0'], cloak: '#3a2a20', fur: 'dark' },
  { beard: '#b8862a', hair: 'long', beardStyle: 'braided', tunic: '#2a4a3a', trim: ['#c9a23a', '#4a1a14'], cloak: '#2e2a26', fur: 'dark' },
  { beard: '#6a3a1e', hair: 'tied', beardStyle: 'long', tunic: '#6a2430', trim: ['#e0c27a', '#1a1a1a'], cloak: '#262230', fur: 'light' },
];
const scene = new THREE.Scene(); scene.background = new THREE.Color(0x050302); scene.fog = new THREE.FogExp2(0x140b06, 0.03);
RIM.value.set(0xff8a40); RIM_AMT.value = 0.12;
const hemi = new THREE.HemisphereLight(0x3a4a6a, 0x1a0e08, 0.18); scene.add(hemi);
const cam = new THREE.PerspectiveCamera(40, W / H, 0.02, 120); scene.add(cam);
const X = { vikings: [], deck: [], uni: [], orbit: [], hookPops: [], hookCards: [] };

// the worlds she has made (keys must exist in /media/hd; each pick is a preference order with fallbacks)
const FOOT_ALL = ['aff_robot_button', 'aff_robot_eyes', 'aff_robot_back', 'aff_robot_memo', 'aff_customers', 'aff_systems_green', 'aff_porsche_desert', 'aff_porsche_side', 'aff_porsche_front', 'aff_porsche_house', 'aff_car_turntable',
  'bl_2200', 'bl_city', 'bl_cube', 'bl_grid', 'bl_grid2', 'bl_laser', 'bl_pinkcubes', 'bl_standup', 'bl_tunnel', 'ph_battery', 'ph_bench_robot', 'ph_dont_wait', 'ph_dusk_city', 'ph_hold_tower', 'ph_neon_plaza', 'ph_onhold_night',
  'ph_please_neon', 'ph_ring', 'ph_stars', 'rage_gradient', 'rage_metal', 'rage_metal2', 'rage_optout', 'rage_said_no', 'rage_title', 'ts_bingo', 'ts_circling', 'ts_host', 'ts_huddle', 'ts_story'];
// start frames (1-based) of a clean stretch inside each clip (the aff clips have cuts in them)
const START = { aff_robot_button: 26, aff_porsche_side: 12, aff_robot_eyes: 40, aff_porsche_desert: 20, aff_robot_memo: 46, aff_porsche_house: 100, aff_customers: 1 };
let HOOK4 = [], UNI = [], ORBIT = [];

let hall, seer, man, rocket, staff, embers, maker, review, towerCard, tower, theatre, popL;
const rtRef = new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType }), rtD = new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType });
const dq = new FullScreenQuad(new THREE.ShaderMaterial(WD.drosteShader()));

async function build() {
  await WD.probeFootage(FOOT_ALL);
  const P = WD.pick;
  HOOK4 = [P('ph_please_neon', 'ph_hold_tower'), P('aff_porsche_side', 'aff_porsche_desert', 'bl_city'), P('aff_robot_button', 'aff_robot_eyes', 'bl_grid'), P('rage_metal', 'ts_host', 'bl_cube')];
  UNI = ['ts_host', 'bl_grid', 'ph_neon_plaza', 'aff_porsche_desert', 'rage_said_no', 'ph_stars', 'bl_cube', 'aff_robot_eyes'].map((k) => P(k, 'bl_city'));
  ORBIT = FOOT_ALL.filter((k) => WD.has(k) && !HOOK4.includes(k) && !UNI.includes(k));
  hall = buildHall(env, M); scene.add(hall);
  seer = new Seeress(M); seer.root.position.copy(SEER); scene.add(seer.root);
  man = new TechKing(M); man.root.position.copy(MAN); man.root.rotation.y = Math.PI; scene.add(man.root);
  rocket = makeRocket(env, { h: 0.7 }); rocket.position.set(-0.43, 0, HALL.stool.z + 0.04); rocket.rotation.y = 2.4; scene.add(rocket);
  rocket.traverse((o) => { const m = o.material; if (o.isMesh && m && m.metalness === 1 && m.roughness === 0.2) { m.roughness = 0.48; m.metalness = 0.55; m.envMapIntensity = 1.6; } });
  staff = makeStaff(M); staff.position.set(-0.47, HALL.dais.y, HALL.seat.z + 0.02); staff.rotation.set(0.0, 0, 0.1); scene.add(staff);
  const R = rng(5);
  HALL.seats.forEach((s, i) => {
    const v = new Viking(M, { ...VIKS[(i * 5 + (s.side > 0 ? 3 : 0)) % VIKS.length], seed: 10 + i, bulk: 0.95 + R() * 0.1, lod: 0.45 });
    v.root.position.set(s.x, 0, s.z); v.root.rotation.y = -s.side * Math.PI / 2; scene.add(v.root);
    v.userData = { seat: s, ph: R() * 10, lag: (R() - 0.5) * 0.06, yaw0: (R() - 0.5) * 0.5 }; X.vikings.push(v);
  });
  // ---- cards: the deck (backs), THE MAKER, THE REVIEW, the Tower, one card for each of the four worlds
  for (let i = 0; i < 18; i++) { const c = makeCard(env, null); scene.add(c); X.deck.push(c); }
  const mk = WD.drawMaker(); maker = makeCard(env, [mk.dim]); maker.userData.front.material = WD.revealMaterial(mk.dim, mk.lit, env, mk.rects); scene.add(maker);
  const rv = WD.drawReview(); review = makeCard(env, [rv.dim]); review.userData.front.material = WD.revealMaterial(rv.dim, rv.lit, env, rv.rects); scene.add(review);
  towerCard = makeCard(env, [drawTower(41)]); scene.add(towerCard);
  const titles = { ph: 'PLEASE HOLD', aff: 'ASKING FOR A FRIEND', bl: 'I HAVE A BLOCKER', rage: 'RAGE', ts: 'TED TALK' };
  for (const k of HOOK4) { const c = makeCard(env, [await WD.drawVideoCard(k, titles[k.split('_')[0]] || 'ADITAZZZ', 300 + X.hookCards.length)]); scene.add(c); X.hookCards.push(c); }
  // ---- the worlds
  theatre = WD.proscenium({ key: null, SW: 0.4, title: 'THIS VIDEO', seed: 31 }); scene.add(theatre.root);
  const words = ['LOOK', 'WHAT', 'I CAN', 'DO!'];
  HOOK4.forEach((k, i) => { const p = WD.proscenium({ key: k, SW: 0.17, title: words[i], seed: 40 + i, size: 960, head: 0.075, titleK: 0.7 }); scene.add(p.root); X.hookPops.push(p); });
  // a world in front of every seat at the feast (the universe shot)
  const uniKeys = FOOT_ALL.filter((k) => WD.has(k) && !HOOK4.includes(k));
  HALL.seats.forEach((s, i) => { const k = uniKeys[(i * 7) % uniKeys.length] || UNI[0]; const p = WD.proscenium({ key: k, SW: 0.34, title: '', seed: 60 + i, size: 480, curtains: i % 2 === 0 }); p.parts.seat = s; scene.add(p.root); X.uni.push(p); });
  tower = WD.towerWordsPopup(); scene.add(tower.root);
  // the galaxy: her videos on three spiral arms in the smoke over the hearth, thin gilded screens
  const frameT = canvasTex(512, 300, (g, w, h) => { g.clearRect(0, 0, w, h); g.strokeStyle = '#e8c472'; g.lineWidth = 16; g.strokeRect(8, 8, w - 16, h - 16); g.strokeStyle = '#fff0c0'; g.lineWidth = 3; g.strokeRect(22, 22, w - 44, h - 44); });
  const frameM = new THREE.MeshBasicMaterial({ map: frameT, transparent: true, depthWrite: false, fog: false, toneMapped: false, side: THREE.DoubleSide }); frameM.color.setScalar(1.25);
  const nOrb = 36;
  for (let i = 0; i < nOrb; i++) {
    const k = ORBIT.length ? ORBIT[(i * 5) % ORBIT.length] : UNI[i % UNI.length]; const g = new THREE.Group();
    const sc = new THREE.Mesh(new THREE.PlaneGeometry(0.56, 0.315), new THREE.MeshBasicMaterial({ map: WD.footTex(k, 240), side: THREE.DoubleSide, fog: false, toneMapped: false })); sc.material.color.setScalar(0.95); g.add(sc);
    const fr = new THREE.Mesh(new THREE.PlaneGeometry(0.56 * 1.07, 0.315 * 1.12), frameM); fr.position.z = 0.002; g.add(fr);
    g.userData = { key: k, i, arm: i % 3, j: Math.floor(i / 3) };
    g.visible = false; scene.add(g); X.orbit.push(g);
  }
  // ---- embers: the hook over the hearth (hook 1)
  const h1 = TM.hooks[0]; embers = emberLine('LOOK WHAT I CAN DO!', ['LOOK', 'WHAT', 'I', 'CAN', 'DO!'], h1.wt, 138.62, { h: 0.46, maxW: 4.2, seed: 8, density: 1.5, size: 1.6 });
  embers.children[0].visible = false;   // no smoke band in world space (it reads as a dark box)
  embers.position.set(0, 2.5, 0.6); embers.visible = false; scene.add(embers);
  // the galaxy's core, and a flare for each star as it ignites on THE REVIEW
  X.core = glowSprite(new THREE.Color(1.0, 0.82, 0.55), 1); X.core.visible = false; scene.add(X.core);
  X.flares = [0, 1, 2, 3, 4].map((i) => { const f = glowSprite(new THREE.Color(1.0, 0.8, 0.45), 0.03); f.position.set(((600 + (i - 2) * 196) / 1200 - 0.5) * 0.07, (0.5 - 600 / 2057) * 0.12, 0.004); f.visible = false; review.add(f); return f; });
  for (const c of [maker, review]) c.userData.front.material.envMapIntensity = 0.5;
  // ---- light: one for the worlds and cards (moves where it's needed)
  popL = new THREE.PointLight(0xffb060, 0, 2.6, 2); scene.add(popL);
  // ---- shadows, merge
  shadows(scene); scene.traverse((o) => { if (o.isMesh && o.material && (o.material.isShaderMaterial || o.material.transparent || o.material.isMeshBasicMaterial)) { o.castShadow = false; o.receiveShadow = false; } });
  for (const c of [...X.deck, maker, review, towerCard, ...X.hookCards]) c.traverse((o) => { if (o.isMesh) o.castShadow = false; });
  for (const p of [seer, man, ...X.vikings]) p.root.traverse((o) => { if (o.isMesh) o.receiveShadow = false; });
  // the big painted and wooden surfaces don't need anisotropic filtering (costly on the CPU renderer); the cards keep it
  { const seen = new Set(); for (const r of [hall, seer.root, man.root, rocket, staff, ...X.vikings.map((v) => v.root), ...X.deck]) r.traverse((o) => { const m = o.material; if (!m || !m.map || seen.has(m.map)) return; seen.add(m.map); m.map.anisotropy = 1; m.map.needsUpdate = true; });
    for (const tx of Object.values(WD.FOOT.tex)) tx.anisotropy = 2; }
  const mg = mergeStatic(hall); console.log('merged', mg.merged, 'into', mg.meshes, 'footage', Object.keys(WD.FOOT.n).length, 'orbit', nOrb);
  st.renderer.shadowMap.autoUpdate = false;
}

function glowSprite(col, size = 1) {
  const t = canvasTex(128, 128, (g, w, h) => { const gr = g.createRadialGradient(w / 2, h / 2, 0, w / 2, h / 2, w / 2); gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.15, 'rgba(255,240,210,0.8)'); gr.addColorStop(0.45, 'rgba(255,190,110,0.18)'); gr.addColorStop(1, 'rgba(0,0,0,0)'); g.fillStyle = gr; g.fillRect(0, 0, w, h); });
  const m = new THREE.SpriteMaterial({ map: t, color: col, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, fog: false }); const sp = new THREE.Sprite(m); sp.scale.setScalar(size); sp.renderOrder = 20; return sp;
}
// ---------------------------------------------------------------- performances
function seerPose(p) { seer.pose({ lean: 0.12, headPitch: 0.1, look: [0, 1.25, HALL.stool.z], lookK: 0.75, handsW: [SEER_REST.R, SEER_REST.L], ...p }); }
function manPose(p) { man.pose({ lean: 0.12, headPitch: 0.05, look: [0, 1.06, -6.2], lookK: 0.85, handsW: [MAN_REST, ON_ROCKET], ...p }); }
/** Vikings: mode listen | awe | cheer; slams (both fists) on the times in `slams` */
function vikingPose(v, t, { mode = 'listen', slams = [], look = null } = {}) {
  const s = v.userData.seat, side = s.side, tx = side * (HALL.feast.x + 0.2);
  const near = slams.some((e) => t > e - 0.45 && t < e + 0.1); const ts = near ? t : step2(t + v.userData.lag);
  let raise = 0; for (const e of slams) if (ts >= e - 0.42 && ts < e) raise = Math.max(raise, easeOut((ts - (e - 0.42)) / 0.36));
  const y = HALL.feast.top + 0.03 + raise * 0.42, z = raise * 0.12;
  let handsW = [[tx + side * z, y, s.z + 0.17], [tx + side * z, y, s.z - 0.17]], hands = null, lean = 0.18 + 0.1 * raise, headPitch = 0;
  let lk = look || [0, 1.15, -6.1];
  if (mode === 'awe') { lean = -0.12 - 0.04 * Math.sin(ts * 1.7 + v.userData.ph); headPitch = -0.35; lk = [side * 0.4, 2.6 + 0.3 * Math.sin(v.userData.ph), s.z - 0.6 + v.userData.yaw0]; }
  if (mode === 'cheer') { const b = Math.max(0, Math.sin(Math.PI * ((ts - 147.12) / (60 / 129.2) % 1))); lean = -0.08; hands = [[-0.3, 0.98 + 0.05 * b, 0.18], [0.3, 0.98 + 0.05 * b, 0.18]]; handsW = null; headPitch = -0.28; lk = null; }
  v.pose({ lean, handsW: hands ? null : handsW, hands, look: lk, lookK: lk ? 0.85 : 0, headPitch, headRoll: 0.04 * Math.sin(v.userData.ph * 3) });
}

// ---------------------------------------------------------------- shots (camera)
const SHOT = { A: T0 - 0.01, B: 138.45, C: 139.95, D: 143.65, E: 145.50, F: 147.08, G: 149.06 };
// the theatre (shot C): where it stands, which way it faces, and the camera square to its stage
const TH = { pos: V(-0.02, TOP + 0.001, TZ + 0.04), yaw: 0.75, d0: 1.12, hoff: 0.14, loff: 0.16 };
function theatreFrame() {
  const n = V(Math.sin(TH.yaw), 0, Math.cos(TH.yaw)), right = V(Math.cos(TH.yaw), 0, -Math.sin(TH.yaw)), up = V(0, 1, 0);
  const SW = theatre.parts.SW, SH = theatre.parts.SH;
  const S = TH.pos.clone().add(V(0, theatre.parts.stageY + SH / 2, 0));
  const C0 = S.clone().addScaledVector(n, TH.d0).addScaledVector(up, TH.hoff).addScaledVector(right, TH.loff);
  return { n, right, up, S, C0, SW, SH };
}
const FOV_C = 30; const TAU3 = Math.PI * 2 / 3;
function camAt(t) {
  const st_ = (p0, p1, l0, l1, f, u, e = easeIO) => ({ p: V(...p0).lerp(V(...p1), e(u)), l: V(...l0).lerp(V(...l1), e(u)), fov: f });
  if (t < SHOT.B) { const u = clamp((t - SHOT.A) / (SHOT.B - SHOT.A)); return st_([0, 1.95, 8.9], [0, 1.78, 7.4], [0, 1.72, -4.5], [0, 1.62, -4.5], 42, u, easeOut); }
  if (t < SHOT.C) { const u = clamp((t - SHOT.B) / (SHOT.C - SHOT.B)); return st_([0.24, 1.25, -5.72], [0.22, 1.245, -5.8], [0.07, 1.235, -6.6], [0.07, 1.235, -6.6], 32, u, easeOut); }
  if (t < SHOT.D) { const F = theatreFrame(); return { p: F.C0.clone(), l: F.C0.clone().sub(F.n), fov: FOV_C, theatre: F }; }
  if (t < SHOT.E) { const u = clamp((t - SHOT.D) / (SHOT.E - SHOT.D)); return st_([-0.08, 0.94, -6.6], [-0.07, 0.95, -6.52], [0.05, 1.02, -5.45], [0.05, 1.03, -5.45], 42, u, easeOut); }
  if (t < SHOT.F) { const u = clamp((t - SHOT.E) / (SHOT.F - SHOT.E)); return st_([0, 1.13, -5.26], [0, 1.12, -5.33], [0, 0.99, -5.98], [0, 0.985, -5.98], 44, u, easeOut); }   // his eyes
  if (t < SHOT.G) { const u = clamp((t - SHOT.F) / (SHOT.G - SHOT.F)); return st_([0, 2.55, 7.2], [0, 2.4, 5.9], [0, 2.5, -2.0], [0, 2.42, -2.0], 46, u, easeOut); }
  const u = clamp((t - SHOT.G) / (T1 - SHOT.G));
  return st_([0.03, 0.975, -5.675], [0.022, 0.955, -5.697], [0.0, TOP + 0.004, -5.868], [0.0, TOP + 0.004, -5.868], 27, u, easeOut);
}
function shake(t, slams) { let k = 0; for (const e of slams) k += 0.010 * decay(t, e, 0.12); return k; }

// ---------------------------------------------------------------- per frame
function reset() {
  for (const c of [...X.deck, maker, review, towerCard, ...X.hookCards]) { c.visible = false; c.scale.setScalar(1); }
  for (const p of [theatre, tower, ...X.hookPops, ...X.uni]) p.setOpen(0);
  for (const o of X.orbit) o.visible = false; X.core.visible = false; for (const f of X.flares) f.visible = false; man.root.position.copy(MAN);
  embers.visible = false; popL.intensity = 0; popL.distance = 2.6;
  const ctl = hall.userData.ctl; ctl.torch = [1, 1, 1, 1]; ctl.stand = 1; ctl.candle = 1; ctl.fill = 1;
  hall.userData.fire.userData.level = 1; hall.userData.fire.userData.flare = 0;
  hemi.color.setRGB(0.23, 0.29, 0.42); hemi.intensity = 0.18;
  seer.setFace('open'); man.setFace('smile'); man.root.visible = true; seer.root.visible = true;
  st.finish.uniforms.uFlash.value = 0; st.finish.uniforms.uFade.value = 1; st.finish.uniforms.uFlashCol.value.setRGB(1, 0.85, 0.6);
  st.droste.uniforms.uK.value = 0; st.droste.uniforms.uZs.value = 1; st.droste.enabled = false;
}
function deckStack(n = 18) { for (let i = 0; i < 18; i++) { if (i >= n) { X.deck[i].visible = false; continue; } place(X.deck[i], V(-0.28, TOP + i * 0.0017, TZ - 0.12), FACE_DOWN(0.3 + 0.04 * Math.sin(i * 7))); } }

function frame(t) {
  reset();
  const ts = step2(t); const hk = TM.hooks;
  const slams = [hk[0].wt[4], hk[3].wt[4]];
  let flare = 0.45 * slams.reduce((a, e) => a + decay(t, e, 0.35), 0);
  const uni = t >= SHOT.F;
  X.vikings.forEach((v) => vikingPose(v, t, { mode: uni ? (t > 147.9 ? 'cheer' : 'awe') : 'listen', slams: uni ? [] : slams }));
  deckStack(t < SHOT.E ? 18 : 14);
  let shotK = 'A';
  for (const k of ['B', 'C', 'D', 'E', 'F', 'G']) if (t >= SHOT[k]) shotK = k;

  // ---- A: the hall; embers into letters over the hearth
  if (shotK === 'A') {
    embers.visible = true; embers.userData.update(t, H, 42); embers.userData.kick(0.5 * decay(t, hk[0].wt[4], 0.18));
    seerPose({ look: [0, 1.2, 2.0], lookK: 0.6 }); seer.setFace(t < hk[0].wt[4] ? 'closed' : 'open');
    manPose({ look: [0, 2.2, 0.8], lookK: 0.5, lean: 0.02 });
  }
  // ---- B: the seeress, THE MAKER in her left hand; the words ignite as sung
  if (shotK === 'B') {
    const h = hk[1]; const cardP = V(0.155, 1.225, -6.24);
    const lift = ramp(ts, SHOT.B - 0.1, h.s + 0.05, easeOut);
    const cp = cardP.clone().add(V(0.02 * (1 - lift), -0.09 * (1 - lift), -0.04 * (1 - lift)));
    const pulse = h.wt.reduce((a, w, i) => a + (i === 4 ? 1.6 : 0.5) * decay(t, w, 0.18), 0);
    const cq = qOf(-0.05 + 0.012 * Math.sin(ts * 3), -0.36 + 0.02 * Math.sin(ts * 2.1), 0.06);
    place(maker, cp, cq, 1.0);
    const mm = maker.userData.front.material;
    [h.wt[0], h.wt[1], h.wt[2], h.wt[4]].forEach((w, i) => mm.userData.setRev(i, ramp(t, w - 0.04, w + (i === 2 ? 0.26 : 0.16), lin)));
    maker.userData.setGlow(new THREE.Color(1, 0.72, 0.3), 0.2 + 0.5 * pulse);
    mm.userData.u.uLitGlow.value = 0.45 + 0.5 * decay(t, h.wt[4], 0.25);
    // her gloved hand holds it by the lower right corner, from behind
    cp.y += 0.004 * Math.sin(ts * 4.2); maker.position.copy(cp);   // it floats beside her, breathing
    const hand = track([[SHOT.B - 0.1, [0.15, 0.95, -6.3]], [h.s + 0.1, [0.17, 0.98, -6.28]], [h.e, [0.17, 0.98, -6.28]]], ts);
    seerPose({ handsW: [SEER_REST.R, hand], look: [0.22, 1.25, -5.76], lookK: 0.9, lean: 0.14, headPitch: 0.02 });
    seer.setFace(t < h.s ? 'closed' : 'open');
    popL.color.setRGB(1.0, 0.72, 0.38); popL.position.copy(cp).add(V(-0.05, 0.0, 0.12)); popL.intensity = 0.02 + 0.03 * pulse;
    manPose({});
  }
  // ---- C: she lays the card down; the theatre rises; its stage shows this very video; the man leans in; we fall in
  let theatreOn = false;
  if (shotK === 'C') {
    const F = theatreFrame(); theatreOn = true;
    const down = ramp(t, SHOT.C - 0.05, 140.32, easeIO);
    const cardTable = TH.pos.clone();
    const hold = V(0.155, 1.2, -6.24);
    const cp = hold.clone().lerp(cardTable, down); cp.y = lerp(hold.y, cardTable.y, down);
    const qq = new THREE.Quaternion().slerpQuaternions(qOf(-0.5, -0.2, 0.05), FACE_UP(TH.yaw), down);
    place(maker, cp, qq, 1.0); const mm = maker.userData.front.material; for (let i = 0; i < 4; i++) mm.userData.setRev(i, 1); mm.userData.u.uLitGlow.value = 0.5;
    maker.userData.setGlow(new THREE.Color(1, 0.72, 0.3), 0.3 + 1.2 * decay(t, 140.38, 0.3));
    const handT = track([[SHOT.C, [0.17, 0.98, -6.28]], [140.32, cardTable.clone().add(V(0.02, 0.05, -0.12)).toArray()], [140.7, SEER_REST.L]], ts);
    const sk = ramp(t, 140.40, 141.1, lin);
    theatre.root.position.copy(TH.pos); theatre.root.rotation.set(0, TH.yaw, 0); theatre.setOpen(sk);
    seerPose({ handsW: [SEER_REST.R, handT], look: t < 141.0 ? [0.0, 0.9, -5.9] : F.C0.toArray(), lookK: 0.85, lean: lerp(0.3, 0.14, ramp(t, 140.4, 140.9)) });
    manPose({ look: [0, 0.95, -5.9], lookK: 0.8 });
    popL.color.setRGB(1.0, 0.75, 0.45); popL.position.copy(F.S).add(F.n.clone().multiplyScalar(0.3)).add(V(0, 0.22, 0)); popL.intensity = 0.1 * sk;
  }
  // ---- D: the man and his Tower: the windows spell the hook
  if (shotK === 'D') {
    const h = hk[2]; const tp = V(0.13, TOP + 0.001, TZ + 0.08);
    place(towerCard, tp.clone().add(V(0, 0.0005, -0.02)), FACE_UP(Math.PI + 0.2));
    tower.root.position.copy(tp); tower.root.rotation.set(0, Math.PI + 0.2, 0); seer.root.visible = false;   // she is behind the camera
    tower.setOpen(ramp(t, SHOT.D - 0.25, h.s + 0.35, lin));
    const lit = [h.wt[0], h.wt[1], h.wt[2], h.wt[4]].map((w, i) => ramp(t, w - 0.02, w + (i === 2 ? 0.28 : 0.14), lin));
    const flash = decay(t, h.wt[4], 0.07) + 0.5 * decay(t, h.wt[4] + 0.13, 0.05);
    tower.update(t, { lit, flash });
    man.setFace('grin');
    const present = ramp(ts, h.s - 0.05, h.s + 0.3);
    const pump = ts >= h.wt[4] - 0.2 && ts < h.wt[4] + 0.4 ? Math.sin(Math.PI * clamp((ts - (h.wt[4] - 0.2)) / 0.6)) : 0;
    const handR = mixV(MAN_REST, [0.2, 0.9 + 0.04 * pump, -5.7], present);
    manPose({ handsW: [handR, ON_ROCKET], look: [-0.07, 0.95, -6.38], lookK: 0.9, lean: 0.06 - 0.04 * pump, headPitch: -0.04 });
    popL.color.setRGB(1.0, 0.8, 0.45); popL.position.set(0.06, 0.84, -5.72); popL.intensity = 0.03 + 0.06 * lit.reduce((a, b) => a + b, 0) / 4 + 0.3 * flash;
    st.finish.uniforms.uFlash.value = 0.05 * flash; st.finish.uniforms.uFlashCol.value.setRGB(0.8, 0.88, 1);
    seerPose({ look: [0, 1.25, -5.2] });
  }
  // ---- E and F: four worlds across the table (one word each), then worlds everywhere
  if (shotK === 'E' || shotK === 'F') {
    const h = hk[3]; const tw = [h.wt[0], h.wt[1], h.wt[2], h.wt[4]];
    X.hookPops.forEach((p, i) => {
      const x = (i - 1.5) * 0.215, z = TZ + 0.07 - 0.06 * Math.abs(i - 1.5) / 1.5, yaw = -x * 0.7;
      // the card flips face up under her hand, then its world springs up
      const fu = ramp(t, tw[i] - 0.22, tw[i] - 0.04, easeIO);
      const k = ramp(t, tw[i] - 0.06, tw[i] + 0.5, lin);
      p.root.position.set(x, TOP + 0.001, z); p.root.rotation.set(0, yaw, 0); p.setOpen(k);
      if (k > 0) WD.want(p.parts.key, 960, { start: START[p.parts.key] || 1, t0: tw[i] });
      const flipQ = FACE_DOWN(yaw + Math.PI).multiply(new THREE.Quaternion().setFromAxisAngle(V(0, 1, 0), -Math.PI * fu));
      place(X.hookCards[i], V(x, TOP + 0.0004 + 0.03 * Math.sin(Math.PI * fu), z + 0.01), flipQ);
      X.hookCards[i].userData.setGlow(new THREE.Color(1, 0.7, 0.3), fu > 0.9 ? 0.8 * decay(t, tw[i], 0.3) : 0);
    });
    // her hands go along the row, turning each card as it is sung
    const swX = track([[SHOT.E - 0.2, -0.4], [tw[0] - 0.12, -0.32], [tw[1] - 0.12, -0.11], [tw[2] - 0.12, 0.11], [tw[3] - 0.12, 0.32], [tw[3] + 0.35, 0.36]], ts);
    const dip = [0, 1, 2, 3].reduce((a, i) => Math.max(a, Math.sin(Math.PI * clamp((ts - (tw[i] - 0.28)) / 0.3))), 0);
    const sweep = [swX, 1.03 - 0.05 * dip, TZ - 0.09];
    const active = t < tw[3] + 0.25;
    seerPose({ handsW: [active && swX < 0 ? sweep : SEER_REST.R, active && swX >= 0 ? sweep : SEER_REST.L], look: [swX * 0.8, 0.9, TZ + 0.05], lookK: 0.8, lean: 0.32 });
    if (shotK === 'E') man.root.visible = false;   // we are behind his eyes
    manPose({ look: [0, 0.95, TZ], lookK: 0.8, lean: 0.12 });
    const lk = X.hookPops.reduce((a, p) => a + p.k, 0) / 4;
    popL.color.setRGB(0.95, 0.82, 0.72); popL.position.set(0, TOP + 0.2, TZ + 0.3); popL.intensity = 0.25 * lk;
  }
  if (shotK === 'F') {
    // a world rises in front of every seat at the feast, in a wave from the head of the hall toward us
    X.uni.forEach((p, i) => { const s = p.parts.seat; const tr = 147.16 + (s.z + 2.6) * 0.1 + (s.side > 0 ? 0.04 : 0);
      const k = ramp(t, tr, tr + 0.55, lin); const px = s.side * (HALL.feast.x - 0.08), pz = s.z;
      p.root.position.set(px, HALL.feast.top + 0.001, pz); p.root.rotation.set(0, Math.atan2(-px, 4.5), 0); p.setOpen(k);
      if (k > 0) WD.want(p.parts.key, 480, { start: START[p.parts.key] || 1, t0: tr, fps: 15 }); });
    // the galaxy: three arms of her videos unwinding in a great wheel over the hearth, turning
    const gc = V(0, 2.85, -1.2); hall.userData.fire.userData.level = 0.78;
    X.orbit.forEach((o) => { const u = o.userData; const tin = 147.1 + u.j * 0.075 + u.arm * 0.025; const k = ramp(t, tin, tin + 0.42, easeOut); if (k <= 0) return;
      const r = (0.3 + u.j * 0.255) * lerp(0.5, 1, k), a = u.arm * TAU3 + r * 1.2 + (t - 147.1) * 0.32;
      o.visible = true; o.position.set(gc.x + Math.cos(a) * r, gc.y + Math.sin(a) * r * 0.62, gc.z + 0.15 * Math.sin(a * 3 + u.j));
      o.lookAt(cam.position); o.scale.setScalar(k * (0.75 + 0.06 * u.j));
      WD.want(u.key, 240, { start: START[u.key] || 1, t0: tin, fps: 15 }); });
    X.core.visible = true; X.core.position.copy(gc); X.core.scale.setScalar(1.6 * ramp(t, 147.15, 147.6, easeOut) * (1 + 0.08 * Math.sin(t * 9)));
    X.vikings.forEach((v) => vikingPose(v, t, { mode: t > 147.9 ? 'cheer' : 'listen', look: gc.toArray() }));
    hemi.intensity = 0.18 + 0.12 * ramp(t, 147.3, 148.4); hemi.color.setRGB(0.4, 0.38, 0.5);
    popL.color.setRGB(1.0, 0.85, 0.7); popL.position.copy(gc).add(V(0, -0.3, 0.4)); popL.intensity = 2.0 * ramp(t, 147.3, 148.3);
    popL.distance = 5;
  }
  // ---- G: THE REVIEW, slapped down on the beat; five stars, one per beat; then to black
  if (shotK === 'G') {
    const sb = TM.starBeats; const land = sb[0];
    const sl = ramp(t, SHOT.G, land, easeIn);
    const from = V(-0.008, TOP + 0.024, -5.968), to = V(0.0, TOP, -5.875);
    const cp = from.clone().lerp(to, sl); cp.y = lerp(from.y, to.y, sl) + (t > land ? 0.006 * Math.sin(Math.PI * clamp((t - land) / 0.12)) : 0);
    place(review, cp, new THREE.Quaternion().slerpQuaternions(qOf(-0.7, 0.5, 0.2), FACE_UP(0), easeOut(sl)));
    const rm = review.userData.front.material;
    sb.forEach((b, i) => rm.userData.setRev(i, ramp(t, b - 0.03, b + 0.12, lin)));
    const pulse = sb.reduce((a, b, i) => a + (i === 4 ? 1.4 : 0.7) * decay(t, b, 0.22), 0);
    review.userData.setGlow(new THREE.Color(1, 0.72, 0.3), 0.15 + 0.4 * pulse); rm.userData.u.uLitGlow.value = 0.32 + 0.35 * pulse;
    seerPose({ look: [0, 0.8, -5.88], lookK: 0.9, lean: 0.3 });
    manPose({ look: [0, 0.8, -5.88], lookK: 0.8, lean: 0.2, handsW: [[0.17, 0.62, -5.42], ON_ROCKET] });
    X.flares.forEach((f, i) => { const k = decay(t, sb[i], 0.16) * (t >= sb[i] ? 1 : 0); f.visible = k > 0.01; f.material.opacity = k; f.scale.setScalar(0.012 + 0.03 * (1 - k)); });
    const fade = ramp(t, 151.36, 151.72, easeIO);
    st.finish.uniforms.uFade.value = 1 - fade; hall.userData.fire.userData.level = 1 - 0.8 * fade;
  }
  hall.userData.fire.userData.flare = flare;
  // ---- camera
  const c = camAt(t); const sh = shotK === 'A' || shotK === 'E' ? shake(t, slams) : 0;
  cam.up.copy(c.up || V(0, 1, 0)); cam.position.copy(c.p).add(V(Math.sin(t * 71) * sh, Math.cos(t * 53) * sh, 0)); cam.lookAt(c.l); cam.fov = c.fov; cam.updateProjectionMatrix(); cam.updateMatrixWorld(true);   // (projection below needs this frame's matrices)
  return { shotK, c, theatreOn };
}

// ---------------------------------------------------------------- the theatre's stage: this very frame
function projectUV(p, camera) { const v = p.clone().project(camera); return [(v.x + 1) / 2, (v.y + 1) / 2]; }
let lastShadow = null; const PROF = q.get('prof') === '1'; const gl = st.renderer.getContext();
const sync = () => { if (PROF) { const px = new Uint8Array(4); gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, px); } };
const rt1 = new THREE.WebGLRenderTarget(1, 1);
window.renderTime = async (t) => {
  const T_ = [performance.now()];
  const info = frame(t);
  const noVik = info.shotK === 'G' || info.shotK === 'B'; for (const v of X.vikings) v.root.visible = !noVik;
  st.renderer.shadowMap.needsUpdate = true;   // (only the wide shots cast shadows; updated every frame so any frame renders the same alone)
  if (info.shotK === 'C' || info.shotK === 'E') for (const v of X.vikings) v.root.visible = false;   // behind the camera / out of frame
  hall.userData.flash(0); hall.userData.update(t, cam, H, cam.fov);
  // light rig per shot: the wide shots (A, F) get the whole fire (two lights, one casting shadows) and the moon through
  // the smoke hole; the close shots, where neither shadows nor the moon show, one fire light carrying both, no shadows
  const wide = info.shotK === 'A' || info.shotK === 'F'; const FL = hall.userData.fire.userData.lights;
  st.renderer.shadowMap.enabled = wide; FL[1].visible = wide; hall.userData.moon.visible = wide;
  if (!wide) FL[0].intensity += FL[1].intensity;
  for (const o of [...X.hookPops, ...X.uni, theatre]) o.setTint(1);
  T_.push(performance.now()); await WD.footUpdate(t); T_.push(performance.now());
  if (PROF && st.renderer.shadowMap.needsUpdate) { st.renderer.setRenderTarget(rt1); st.renderer.render(scene, cam); st.renderer.setRenderTarget(null); sync(); }
  T_.push(performance.now());
  if (PROF) { st.renderer.setRenderTarget(rtRef); st.renderer.render(scene, cam); st.renderer.setRenderTarget(null); sync(); } T_.push(performance.now());
  st.finish.uniforms.uTime.value = t;
  if (info.theatreOn) {
    const F = info.c.theatre; const dk = ramp(t, 140.86, 141.06, lin);
    // the fall: twice into the stage (s from 0 to 2), the camera flying along the line that keeps the stage's fixed point still
    const s = 2 * ramp(t, 142.50, 143.32, easeIO); const frac = s >= 2 ? 0 : s - Math.floor(s);
    const corners = theatre.stageCorners();
    const sm = theatre.parts.screen.userData.mesh.material;
    if (dk > 0 && frac > 0) {
      // 1) the reference: this frame from the base camera, stage black, frame-inside-frame applied -> rtD
      cam.position.copy(F.C0); cam.up.set(0, 1, 0); cam.lookAt(F.C0.clone().sub(F.n)); cam.fov = FOV_C; cam.updateProjectionMatrix(); cam.updateMatrixWorld(true);
      const uv = corners.map((p) => projectUV(p, cam)); const Hinv = WD.stageHinv(uv);
      st.renderer.setRenderTarget(rtRef); st.renderer.render(scene, cam);
      const du = dq.material.uniforms; du.tDiffuse.value = rtRef.texture; du.uHinv.value.copy(Hinv); du.uK.value = 1; du.uZs.value = 1; du.uBlur.value = 0;
      st.renderer.setRenderTarget(rtD); dq.render(st.renderer); st.renderer.setRenderTarget(null);
      // 2) the flight: the camera moves toward X (the stage point whose place in the stage equals its place on screen)
      const r = uv[1][0] - uv[0][0]; const cx = uv[0][0] / (1 - r), cy = uv[0][1] / (1 - r);
      const Xp = corners[0].clone().addScaledVector(F.right, cx * F.SW).addScaledVector(F.up, cy * F.SH);
      const dEnd = (F.SH / 2) / Math.tan(THREE.MathUtils.degToRad(FOV_C / 2)); const d0 = F.C0.clone().sub(Xp).dot(F.n);
      const k = Math.pow(dEnd / d0, frac); cam.position.copy(Xp).addScaledVector(F.C0.clone().sub(Xp), k); cam.lookAt(cam.position.clone().sub(F.n)); cam.updateProjectionMatrix(); cam.updateMatrixWorld(true);
      sm.map = rtD.texture; sm.color.setScalar(1); sm.needsUpdate = true;
      st.droste.enabled = false; st.render(scene, cam, t);
      sm.map = null; sm.color.setScalar(0); sm.needsUpdate = true;
    } else {
      const uv = corners.map((p) => projectUV(p, cam)); st.droste.uniforms.uHinv.value.copy(WD.stageHinv(uv));
      st.droste.enabled = dk > 0; st.droste.uniforms.uK.value = dk; st.render(scene, cam, t);
    }
  } else st.render(scene, cam, t);
  sync(); T_.push(performance.now()); const jp = st.jpeg(0.94); T_.push(performance.now());
  if (PROF) console.log('prof', t.toFixed(2), info.shotK, ['frame', 'foot', 'shadow', 'sceneRT', 'composer', 'jpeg'].map((k, i) => k + ' ' + Math.round(T_[i + 1] - T_[i])).join(' | '));
  return jp;
};

(async () => {
  await loadFilmFonts(); await loadTiming(); await build();
  window.TM = TM; window.__dbg = { scene, cam, seer, man, X, theatre, tower }; window.ready = true;
})().catch((e) => { console.log('INIT ERROR', e.stack || e); });
