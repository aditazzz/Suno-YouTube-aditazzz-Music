// Look What I Can Do · "Scope Creep" (3D sections). renderTime(t) draws the frame at song time t, deterministically.
// Part 1 (0-42.94, the terminal session she approved) and the breakdown are the 2D renders; this file takes over at the
// first chorus: the camera pulls back out of the laptop screen and the world gets bigger on every "Look what I can do".
import * as THREE from 'three';
import * as L from './lib.js';
import * as M from './media.js';
import { makeFloor, Laptop, makeDesk, Field, Screen, neon, neonRing, flicker } from './sets.js';
const { clamp, lerp, sstep, easeIO, easeOut, expOut, env, V3, ls, wt } = L;

let W = 1920, H = 1080, renderer, composer, renderPass, bloom, finish, envTex;

let hall, cam, spot, key, rim, mirror, desk, laptop;
let FIELD = null, RING = null, CONE = null, DUST = null, LABEL = null, TERM = null, TRAIL = null; const HEROES = {};
const T = {};       // key times (filled after timing loads)

function hallSlots() {
  const slots = []; let ring = 0;
  while (slots.length < 512) {
    const r = 4.4 + ring * 2.1; const n = Math.max(8, Math.round(2 * Math.PI * r / 2.2));
    const tiers = 1 + Math.floor(ring / 2);
    // ring 0: one screen straight behind the laptop (as the camera first sees it) and the first eight spread right round
    const order = ring === 0 ? [0, 2, 3, 5, 6, 8, 10, 11, 1, 4, 7, 9, 12].filter((k) => k < n) : null;
    for (let tr = 0; tr < tiers && slots.length < 512; tr++) {
      for (let kk = 0; kk < n && slots.length < 512; kk++) {
        const k = order && order.length === n ? order[kk] : kk;
        const a = ring === 0 ? Math.PI * 1.5 + k / n * Math.PI * 2 : (k + (tr % 2) * 0.5 + ring * 0.37) / n * Math.PI * 2;
        const atl = ['H1', 'V1', 'H2', 'V2'][(slots.length + ring) % 4]; const vert = atl[0] === 'V';
        const y = (vert ? 1.25 : 1.05) + ring * 0.42 + tr * 1.75;
        slots.push({ atlas: atl, cell: (slots.length * 7 + ring) % 16, pos: V3(Math.cos(a) * r, y, Math.sin(a) * r), yaw: Math.atan2(-Math.cos(a), -Math.sin(a)), size: vert ? 1.5 : 1.7, ring, a, r });
      }
    }
    ring++;
  }
  return slots;
}
function schedule(slots) {   // doubling on the beat: 8, 16, 32, ... each new screen flies out of the one that made it
  const gens = [[8, T.d1], [16, T.d2], [32, T.thing1], [64, T.thing2], [128, T.two], [256, T.d3], [512, T.d4]];
  let prev = 0;
  gens.forEach(([n, tg], g) => {
    for (let i = prev; i < n; i++) {
      const s = slots[i]; s.t0 = tg + (i - prev) / Math.max(1, n - prev) * (g === 0 ? 0.12 : 0.28); s.dim = 1 - Math.min(0.45, s.ring * 0.04);
      if (g === 0) { s.parent = -1; continue; }
      let best = -1, bd = 1e9;   // the screen that made it: the nearest one that already exists (short flights, growing outward)
      for (let j = 0; j < prev; j++) { const d = s.pos.distanceTo(slots[j].pos); if (d < bd) { bd = d; best = j; } }
      s.parent = best;
    }
    prev = n;
  });
}

// the live terminal on the laptop once the camera has left it: the session keeps spawning screens
function termTex() {
  const c = document.createElement('canvas'); c.width = 1280; c.height = 720; const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.userData.c = c; t.userData.key = ''; return t;
}
function drawTerm(t) {
  const lines = [['u', 'claude --dangerously-skip-permissions']];
  const counts = [[T.d1, 8], [T.d2, 16], [T.thing1, 32], [T.thing2, 64], [T.two, 128], [T.d3, 256], [T.d4, 512]];
  for (const [tt, n] of counts) if (t >= tt) lines.push(['c', `spawned ${n} screens`]);
  if (t >= T.laptop + 0.3) lines.push(['ok', 'laptop: brought ✓']);
  const key = lines.length + ':' + (t >= T.laptop + 0.3);
  if (key === TERM.userData.key) return; TERM.userData.key = key;
  const g = TERM.userData.c.getContext('2d'); g.fillStyle = '#0c0c0b'; g.fillRect(0, 0, 1280, 720);
  g.font = '30px "JBB"'; g.fillStyle = '#5b574f'; g.fillText('adita@studio  ~/look-what-i-can-do', 40, 60);
  const show = lines.slice(-9);
  show.forEach(([who, s], i) => {
    const y = 150 + i * 62; g.font = '40px "JBB"';
    if (who === 'u') { g.fillStyle = '#74e36a'; g.fillText('❯', 40, y); g.fillStyle = '#ece6d8'; g.fillText(s, 90, y); }
    else if (who === 'ok') { g.fillStyle = '#74e36a'; g.fillText('✓ ' + s.replace(' ✓', ''), 40, y); }
    else { g.fillStyle = '#ffa840'; g.fillText('● ' + s, 40, y); }
  });
  TERM.needsUpdate = true;
}

// ---------------------------------------------------------------- the camera for chorus 1
let CH1CAM = null;
function buildCh1Cam() {
  const { c, n } = laptop.dispFrame();
  const d = (laptop.dispH / 2) / Math.tan(THREE.MathUtils.degToRad(35 / 2));
  const p0 = c.clone().addScaledVector(n, d);
  const P = (v) => [v.x, v.y, v.z];
  CH1CAM = L.camPath([
    { t: T.ch1, p: P(p0), l: P(c), fov: 35 },
    { t: T.ch1 + 0.05, p: P(p0), l: P(c), fov: 35 },
    { t: T.ch1 + 1.25, p: [0.42, 1.06, 0.92], l: [0, 0.86, -0.06], fov: 37, ease: (x) => L.easeOut5(x) },
    { t: T.d2 + 0.25, p: [1.3, 1.35, 2.3], l: [-0.4, 1.05, -0.6], fov: 40 },
    { t: T.thing2 + 0.1, p: [-2.2, 1.9, 1.2], l: [0.5, 1.4, -0.5], fov: 42 },
    { t: T.two + 0.5, p: [-1.0, 3.4, -2.2], l: [0.3, 1.3, 0.8], fov: 44 },
    { t: T.d4 - 0.1, p: [0.0, 24.0, 6.5], l: [0, 0.4, 0], fov: 46 },
    { t: T.here + 1.4, p: [-0.9, 1.7, 1.9], l: [0, 0.95, 0], fov: 40 },
    { t: T.laptop + 1.4, p: [-0.10, 1.07, 0.86], l: [0, 0.85, -0.05], fov: 34 },
  ]);
}

// ---------------------------------------------------------------- 'Click! Click! Ship it!'
let POST = [];
function buildPost() {
  // [time, kind, slot]: kind = cut | launch | made | broke | fixed
  const w = (s, word, n = 0, k = 0) => wt(s, word, n, k);
  const E = [];
  const c1 = 'Click! Click! Ship it!';
  E.push([w(c1, 'Click', 0, 0), 'cut', 3], [w(c1, 'Click', 0, 1), 'cut', 11], [w(c1, 'Ship', 0), 'launch']);
  E.push([w(c1, 'Click', 1, 0), 'cut', 6], [w(c1, 'Click', 1, 1), 'cut', 14], [w(c1, 'Ship', 1), 'launch']);
  E.push([w('Made it! Broke it!', 'Made', 0), 'cut', 9, ['H1', 2]], [w('Made it! Broke it!', 'Broke', 0), 'broke'], [w('Fixed it! Shipped it! Shipped it!', 'Fixed'), 'fixed'],
    [w('Fixed it! Shipped it! Shipped it!', 'Shipped', 0, 0), 'launch'], [w('Fixed it! Shipped it! Shipped it!', 'Shipped', 0, 1), 'cutlaunch', 1]);
  E.push([w(c1, 'Click', 2, 0), 'cut', 4, ['H1', 0]], [w(c1, 'Click', 2, 1), 'cut', 12], [w(c1, 'Ship', 2), 'launch']);   // slot 4's own clip opens dark
  E.push([w('Made it! Broke it!', 'Made', 1), 'cut', 7, ['V1', 14]], [w('Made it! Broke it!', 'Broke', 1), 'broke'], [w('Fixed it! Shipped it!', 'Fixed'), 'fixed'], [w('Fixed it! Shipped it!', 'Shipped'), 'launch']);
  POST = E.sort((a, b) => a[0] - b[0]);
}
function postState(t) {
  let cut = null, ci = -1;
  for (let i = 0; i < POST.length; i++) { const e = POST[i]; if (e[0] > t) break; if (e[1] === 'cut' || e[1] === 'cutlaunch') { cut = e; ci = i; } }
  if (!cut) return null;
  let launch = null, broke = null, fixed = null;
  for (let i = ci; i < POST.length; i++) { const e = POST[i]; if (e[0] > t) break; if (i > ci && (e[1] === 'cut' || e[1] === 'cutlaunch')) break;
    if (e[1] === 'launch' || e[1] === 'cutlaunch') launch = e[0] + (e[1] === 'cutlaunch' ? 0.12 : 0); if (e[1] === 'broke') broke = e[0]; if (e[1] === 'fixed') fixed = e[0]; }
  const next = POST.find((e) => e[0] > t && (e[1] === 'cut' || e[1] === 'cutlaunch'));
  return { slot: cut[2], clip: cut[3] || null, t0: cut[0], launch, broke, fixed, next: next ? next[0] : T.v2, idx: ci };
}

function coneTex() {
  return L.canvasTex(64, 256, (g, w, h) => { const gr = g.createLinearGradient(0, 0, 0, h); gr.addColorStop(0, 'rgba(255,226,192,0.0)'); gr.addColorStop(0.15, 'rgba(255,226,192,0.55)'); gr.addColorStop(1, 'rgba(255,226,192,0.0)'); g.fillStyle = gr; g.fillRect(0, 0, w, h); }, { linear: true });
}
function dust() {
  const R = L.rng(5); const n = 900; const pos = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) { const r = Math.sqrt(R()) * 6; const a = R() * Math.PI * 2; pos.set([Math.cos(a) * r, 0.2 + R() * 4.5, Math.sin(a) * r], i * 3); }
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  return new THREE.Points(g, new THREE.PointsMaterial({ map: L.dotTex(), size: 0.02, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, color: new THREE.Color(1.1, 1.0, 0.95), sizeAttenuation: true }));
}

// ---------------------------------------------------------------- build
function setupScene() {
// ---------------------------------------------------------------- the hall (chorus 1 + ship it)
hall = new THREE.Scene();
// the bright look (her Please Hold / Blocker / TED Charts films): a warm white studio, soft daylight, glossy white floor
hall.background = new THREE.Color(0xe4e2dd); hall.fog = new THREE.FogExp2(0xf2f0eb, 0.024);
cam = new THREE.PerspectiveCamera(35, W / H, 0.01, 900); hall.add(cam);
hall.add(new THREE.HemisphereLight(0xffffff, 0xcdc6ba, 1.3));
key = new THREE.DirectionalLight(0xfff3e4, 1.7); key.position.set(-3, 6, 4); hall.add(key);
rim = new THREE.PointLight(0x7fa8ff, 0.0, 4, 2); rim.position.set(0.6, 1.35, -1.2); hall.add(rim);
spot = new THREE.SpotLight(0xfff0dc, 2.2, 9, 0.5, 0.7, 1.6); spot.position.set(0.3, 4.2, 0.6); spot.target.position.set(0, 0.75, 0); hall.add(spot, spot.target);
{ const fl = makeFloor(hall, envTex); mirror = fl.mirror; fl.mat.color.setHex(0xeeebe5); fl.mat.opacity = 0.9; }
desk = makeDesk(envTex); hall.add(desk);
desk.children[0].material = new THREE.MeshStandardMaterial({ color: 0xf6f4f0, roughness: 0.32, metalness: 0.0, envMap: envTex, envMapIntensity: 0.55 });
laptop = new Laptop(envTex); laptop.root.position.set(0, 0.75, 0); hall.add(laptop.root);

}
export async function build(ctx) {
  ({ W, H } = ctx); ({ renderer, composer, renderPass, bloom, finish, envTex } = ctx.look);
  ctx.S.LOOK.back = 'vec3(0.80, 0.80, 0.82)';
  setupScene();
  T.ch1 = ls('Look what I can do!', 0); T.d1 = wt('Look what I can do!', 'do', 0); T.d2 = wt('Look what I can do!', 'do', 1);
  T.thing1 = wt('I made a thing that made a thing', 'thing', 0, 0); T.thing2 = wt('I made a thing that made a thing', 'thing', 0, 1);
  T.two = wt('That made another two!', 'two', 0); T.d3 = wt('Look what I can do!', 'do', 2); T.d4 = wt('Look what I can do!', 'do', 3);
  T.here = ls("I don't know how I got here"); T.laptop = ls('But I brought my laptop too!'); T.post = ls('Click! Click! Ship it!');
  T.v2 = ls("I'm a Senior Slopcore Architect");
  const slots = hallSlots(); schedule(slots);
  FIELD = new Field(slots, mirror); hall.add(FIELD.root);
  RING = neonRing('LOOK WHAT I CAN DO', { r: 3.55, h: 1.45, reps: 1, sep: '   ✦   ', size: 240, flat: true, color: '#ff4f97' }); hall.add(RING);
  // a soft cone of light over the desk, and dust in it
  CONE = new THREE.Mesh(new THREE.ConeGeometry(1.25, 3.6, 48, 1, true), new THREE.MeshBasicMaterial({ map: coneTex(), transparent: true, depthWrite: false, side: THREE.DoubleSide, blending: THREE.AdditiveBlending, opacity: 0.16, toneMapped: false }));
  CONE.position.set(0.15, 2.45, 0.3); CONE.visible = false;
  DUST = dust(); DUST.visible = false; hall.add(DUST);
  HEROES.H = new Screen(1.7, 1.7 * 0.5625, envTex); HEROES.V = new Screen(1.5 * 0.5625, 1.5, envTex);
  for (const h of Object.values(HEROES)) { h.root.visible = false; hall.add(h.root); const hm = new THREE.Mesh(h.geo, h.mat); h.mirrorMesh = hm; hm.visible = false; mirror.add(hm); }
  const streak = L.canvasTex(128, 512, (g, w, h) => { const img = g.createImageData(w, h); for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) { const u = (x / (w - 1) - 0.5) * 2, v = y / (h - 1);
      const a = Math.exp(-u * u * 9) * Math.pow(1 - v, 1.6) + 0.6 * Math.exp(-u * u * 90) * Math.pow(1 - v, 0.7); const k = (y * w + x) * 4; img.data[k] = img.data[k + 1] = img.data[k + 2] = 255; img.data[k + 3] = Math.min(255, a * 255); } g.putImageData(img, 0, 0); }, { linear: true });
  TRAIL = new THREE.Mesh(new THREE.PlaneGeometry(1, 1).translate(0, -0.5, 0), new THREE.MeshBasicMaterial({ map: streak, color: new THREE.Color(1.5, 0.6, 1.1), transparent: true, depthWrite: false, toneMapped: false, blending: THREE.AdditiveBlending }));
  TRAIL.visible = false; hall.add(TRAIL);
  LABEL = L.textPlane('laptop: brought ✓', { h: 0.05, font: L.FONT.monoB, size: 64, color: '#74e36a', glow: 18, bg: 'rgba(8,10,8,0.82)' });
  LABEL.position.set(0.0, 0.795, 0.215); LABEL.visible = false; hall.add(LABEL);
  TERM = termTex();
  laptop.dispMat.map = await M.image('term_4293.jpg'); laptop.dispMat.needsUpdate = true;
  buildCh1Cam(); buildPost(); await buildV2();
}

// ---------------------------------------------------------------- per frame
const _v = new THREE.Vector3();
function sleek() {   // modern finish: clean blacks and whites, almost no grain, no fringing, bloom only on true highlights
  const u = finish.uniforms; u.uGrain.value = 0.012; u.uCA.value = 0.0004; u.uVig.value = 0.14;
  bloom.strength = 0.1; bloom.threshold = 0.985; bloom.radius = 0.3;
}
function setCam(c, shake = 0, t = 0) {
  cam.position.copy(c.p); if (shake) cam.position.add(V3(L.noise1(t * 0.7, 1), L.noise1(t * 0.6, 2), L.noise1(t * 0.5, 3)).multiplyScalar(shake));
  cam.up.set(Math.sin(c.roll || 0), Math.cos(c.roll || 0), 0); cam.lookAt(c.l); cam.fov = c.fov; cam.updateProjectionMatrix();
}
function v2Vis(on) {
  if (!V) return;
  for (const o of [V.postCard, V.postMirror, V.mono, V.monoMirror, V.subs]) o.visible = on;
  if (!on) { for (const o of [V.feet.root, V.clock, V.fee, V.pill, V.dlgPanel, ...V.clones, ...V.dlg]) o.visible = false; }
}
async function frameHall(t) {
  v2Vis(false);
  finish.uniforms.uVel.value.set(0, 0); finish.uniforms.uFlash.value = 0;
  const pulse = L.beatPulse(t, 7);
  // laptop display: the last frame of the 2D session, then the live terminal
  if (t < T.ch1 + 0.55) { if (laptop.dispMat.map === TERM) { laptop.dispMat.map = await M.image('term_4293.jpg'); laptop.dispMat.needsUpdate = true; } laptop.dispMat.color.setScalar(1); }
  else { drawTerm(t); if (laptop.dispMat.map !== TERM) { laptop.dispMat.map = TERM; laptop.dispMat.needsUpdate = true; } laptop.dispMat.color.setScalar(1.15); }
  // the field + the neon
  const inPost = t >= T.post - 0.02;
  const st = inPost ? postState(t) : null;
  FIELD.hidden.clear(); if (st) FIELD.hidden.add(st.slot);
  FIELD.update(t, { bright: inPost ? 0.75 : 1.0, pulse });
  FIELD.atlases().forEach((a) => M.use(a));
  // the floor ring lights letter by letter, sweeping round on the second 'Look what I can do!'
  const flare = 1 + 2.4 * sstep(T.d3 - 0.6, T.d3, t) * (1 - sstep(T.here + 0.2, T.here + 1.2, t));
  RING.userData.letters.forEach((m, i) => { const a = m.userData.a / (Math.PI * 2); const f = flicker(t, T.d2 - 0.9 + a * 0.75, i + 3) * (0.8 + 0.2 * pulse); m.material.opacity = Math.min(1, f); m.material.color.setScalar(1); m.visible = f > 0.01; });
  DUST.material.opacity = 0.3; DUST.material.size = 0.008; DUST.rotation.y = t * 0.02; DUST.position.y = Math.sin(t * 0.3) * 0.05;
  sleek(); 
  LABEL.visible = false; TRAIL.visible = false; for (const h of Object.values(HEROES)) { h.root.visible = false; h.mirrorMesh.visible = false; }
  if (!inPost) {
    const c = CH1CAM(t); setCam(c, t > T.ch1 + 1.2 ? 0.02 : 0, t);
    if (t >= T.laptop + 0.25) { LABEL.visible = true; const k = easeOut((t - T.laptop - 0.25) / 0.25); LABEL.material.opacity = k; LABEL.scale.setScalar(0.6 + 0.4 * k); LABEL.lookAt(cam.position); }
    // the punch at the start: a white flash on the downbeat as the camera leaves the screen
    finish.uniforms.uFlash.value = 0.05 * env(t, T.d1, 0.02, 0.08) + 0.04 * env(t, T.d2, 0.02, 0.08);
    return;
  }
  // ---- ship it: whip cuts between screens in the hall; launches go straight up
  if (!st) return;
  const s = FIELD.slots[st.slot]; const clipA = st.clip ? st.clip[0] : s.atlas, clipC = st.clip ? st.clip[1] : s.cell;
  const vert = clipA[0] === 'V'; const HERO = vert ? HEROES.V : HEROES.H;
  HERO.root.visible = true; HERO.mirrorMesh.visible = true;
  if (HERO.jit) { HERO.src = null; HERO.jit = false; }   // clean UVs after a glitch frame, whatever frame came before
  HERO.show(clipA, clipC); M.use(clipA);
  const yawQ = new THREE.Quaternion().setFromAxisAngle(THREE.Object3D.DEFAULT_UP, s.yaw);
  let up = 0;
  if (st.launch !== null) { const x = t - st.launch; up = x > 0 ? 9 * x * x + 1.5 * x : 0; }
  const base = s.pos.clone();
  HERO.root.position.copy(base).add(V3(0, up, 0)); HERO.root.quaternion.copy(yawQ);
  HERO.mirrorMesh.position.copy(HERO.root.position); HERO.mirrorMesh.quaternion.copy(yawQ);
  // state tints: made (pop), broke (red glitch), fixed (green), shipped (pink trail)
  let col = new THREE.Color(1, 1, 1).multiplyScalar(1 + 1.2 * env(t, st.t0, 0.02, 0.25));
  const uv = HERO.geo.attributes.uv;
  if (st.broke !== null && (st.fixed === null || t < st.fixed)) {
    const x = t - st.broke; col.setRGB(1.9, 0.35, 0.35);
    if (x < 0.5) { const j = (L.noise1(t * 60, 7)) * 0.04; HERO.src = null; HERO.show(clipA, clipC); for (let k = 0; k < uv.count; k++) uv.setX(k, uv.getX(k) + j * (k % 2 ? 1 : 0.4)); uv.needsUpdate = true; HERO.jit = true; }
  }
  if (st.fixed !== null && t >= st.fixed) { const x = t - st.fixed; col.setRGB(lerp(0.6, 1, sstep(0.2, 0.6, x)), lerp(1.9, 1, sstep(0.2, 0.6, x)), lerp(0.7, 1, sstep(0.2, 0.6, x))); }
  HERO.mat.color.copy(col);
  if (st.launch !== null && t > st.launch) {
    const x = t - st.launch; TRAIL.visible = true;
    const hh = (vert ? 1.5 : 1.7 * 0.5625) / 2;
    TRAIL.position.copy(HERO.root.position).add(V3(0, -hh + 0.02, 0)).addScaledVector(V3(Math.sin(s.yaw), 0, Math.cos(s.yaw)), -0.03); TRAIL.quaternion.copy(yawQ);
    TRAIL.scale.set(vert ? 0.7 : 1.1, 0.3 + up * 0.9, 1); TRAIL.material.opacity = 0.85 * clamp(x / 0.06) * (1 - sstep(0.45, 0.9, x));
  }
  // camera: in front of the screen; whip in from the side; follow the launch up
  const n = V3(Math.sin(s.yaw), 0, Math.cos(s.yaw)); const side = V3(n.z, 0, -n.x);
  const dist = vert ? 2.3 : 2.1; const sgn = st.idx % 2 ? 1 : -1;
  const kin = expOut((t - st.t0) / 0.16); const whipIn = 1 - kin;
  const target = base.clone().add(V3(0, Math.min(up, 3.0) * 0.6, 0));
  const pos = base.clone().addScaledVector(n, dist + 0.25 * (1 - easeOut((t - st.t0) / 1.0))).addScaledVector(side, sgn * (0.35 + whipIn * 1.6)).add(V3(0, 0.12, 0));
  const look_ = target.clone().addScaledVector(side, sgn * whipIn * 1.2);
  setCam({ p: pos, l: look_, fov: 36 - 2 * easeOut((t - st.t0) / 1.2), roll: sgn * whipIn * 0.06 }, 0.012, t);
  // motion blur on the whips: in (just after the cut) and out (just before the next one)
  const out = sstep(st.next - 0.1, st.next, t);
  finish.uniforms.uVel.value.set(-sgn * (whipIn * 0.022 + out * 0.022), 0);
  if (st.launch !== null && t > st.launch) finish.uniforms.uVel.value.y += -0.01 * clamp((t - st.launch) / 0.3);
  finish.uniforms.uFlash.value = 0.12 * env(t, st.t0, 0.01, 0.1);
  if (st.broke !== null && t >= st.broke && t < st.broke + 0.5) { const e = env(t, st.broke, 0.01, 0.35); finish.uniforms.uFlash.value = Math.max(finish.uniforms.uFlash.value, 0.07 * e); finish.uniforms.uFlashCol.value.setRGB(1, 0.15, 0.2); finish.uniforms.uCA.value = 0.0016 + 0.016 * e; cam.position.x += L.noise1(t * 40, 9) * 0.03 * e; }
  if (st.fixed !== null && t >= st.fixed && t < st.fixed + 0.4) { const e = env(t, st.fixed, 0.01, 0.25); finish.uniforms.uFlash.value = Math.max(finish.uniforms.uFlash.value, 0.05 * e); finish.uniforms.uFlashCol.value.setRGB(0.45, 1, 0.42); }
  if (st.launch !== null && t >= st.launch && t < st.launch + 0.4) { const e = env(t, st.launch, 0.005, 0.18); finish.uniforms.uFlash.value = Math.max(finish.uniforms.uFlash.value, 0.1 * e); cam.position.y += L.noise1(t * 35, 4) * 0.025 * e; }
}


// ================================================================ VERSE 2 + QUALIFICATIONS, still in the hall
// Her real slopcore post rises out of the black floor (highlighter + RECEIPT stamp); a whip to her real X profile
// standing as a glass monolith that grows taller with every title she sings; her avatar clones; the 3:30 / 4:00 clock
// and the TED Talk fee; then the qualifications: Claude's question floats in the hall and her subscriptions pour down.
const X_INK = '#0f1419', HL = '#ffe14d';
const BULLETS = [[32, 846, 99, 913], [512, 845, 584, 912], [32, 932, 99, 999], [32, 1020, 99, 1086]];
const TITLES = [["I'm a Senior Slopcore Architect", 'Senior Slopcore Architect'], ["Chief Executive of What's Next", "Chief Executive of What's Next"],
  ['VP of Things That Look Complete', 'VP of Things That Look Complete'], ['Director of the Missing Feet', 'Director of the Missing Feet'],
  ['Head of Vibes and Synergy', 'Head of Vibes and Synergy'], ['Chief of Artificial Me', 'Chief of Artificial Me'],
  ['A thought leader by half past three', 'Thought Leader'], ["By four I've got a TED Talk fee!", 'TED Talk Speaker']];
const SUBS = ['claude-ultra', 'chatgpt-pro', 'gemini-advanced', 'suno-pro', 'midjourney', 'cursor-pro', 'x-premium', 'linkedin-premium', 'notion-ai', 'github-copilot',
  'perplexity-pro', 'runway', 'elevenlabs', 'canva-pro', 'adobe-cc', 'spotify-premium', 'duolingo-max', 'masterclass', 'headspace', 'calm', 'the-atlantic', 'nyt-games',
  'icloud-2tb', 'google-one', 'dropbox', '1password', 'figma', 'framer', 'vercel-pro', 'supabase', 'replit-core', 'lovable', 'bolt', 'v0', 'kling', 'pika', 'luma',
  'higgsfield', 'grok', 'copilot-pro', 'raycast-ai', 'superhuman', 'arc-max', 'warp', 'otter-ai', 'descript', 'capcut-pro', 'gamma', 'fireflies', 'linear',
  'loom', 'zapier', 'make', 'airtable', 'miro', 'calendly', 'grammarly', 'jasper', 'copy-ai', 'tome', 'heygen', 'synthesia', 'krea', 'ideogram'];
let V = null;            // verse-2 objects
const PX = 1 / 600;      // metres per crop pixel for the post + profile (1320 px = 2.2 m)

function stampTex(word, sub, color) {
  return L.canvasTex(760, 300, (g, w, h) => {
    g.translate(w / 2, h / 2); g.rotate(-8 * Math.PI / 180); g.textAlign = 'center'; g.textBaseline = 'middle';
    g.strokeStyle = color; g.lineWidth = 12; g.globalAlpha = 0.95; g.beginPath(); g.roundRect(-330, -105, 660, sub ? 210 : 170, 20); g.stroke();
    g.fillStyle = color; g.font = '140px "Anton"'; g.fillText(word, 0, sub ? -22 : -6);
    if (sub) { g.font = '44px "JBB"'; g.fillText(sub, 0, 72); }
  });
}
function postCanvas(img, boxes) {   // the post image + highlighter strokes (multiply), redrawn when the sweep moves
  const c = document.createElement('canvas'); c.width = img.width; c.height = img.height; const tx = new THREE.CanvasTexture(c); tx.colorSpace = THREE.SRGBColorSpace; tx.anisotropy = 8;
  return { c, tx, img, boxes, key: '' };
}
function drawPost(P, fracs) {
  const key = fracs.map((f) => f.toFixed(3)).join(','); if (key === P.key) return; P.key = key;
  const g = P.c.getContext('2d'); g.globalCompositeOperation = 'source-over'; g.drawImage(P.img, 0, 0);
  g.globalCompositeOperation = 'multiply'; g.fillStyle = HL;
  P.boxes.forEach(([x0, y0, x1, y1], i) => { const f = clamp(fracs[i] || 0); if (f > 0) g.fillRect(x0 - 8, y0 - 6, (x1 - x0 + 16) * f, y1 - y0 + 12); });
  g.globalCompositeOperation = 'source-over'; P.tx.needsUpdate = true;
}
function profileCanvas(img) {
  const maxH = 1180 + 88 * TITLES.length; const c = document.createElement('canvas'); c.width = 1320; c.height = maxH;
  const tx = new THREE.CanvasTexture(c); tx.colorSpace = THREE.SRGBColorSpace; tx.anisotropy = 8; return { c, tx, img, maxH, key: '', h: 1180 };
}
function drawProfile(P, rows, hiRow, hiAmt) {
  const key = rows.join('|') + ':' + hiRow + ':' + hiAmt.toFixed(2); if (key === P.key) return; P.key = key;
  const g = P.c.getContext('2d'); const n = rows.length; const H = 1180 + 88 * n; P.h = H;
  g.fillStyle = '#ffffff'; g.fillRect(0, 0, 1320, P.maxH);
  g.drawImage(P.img, 0, 0, 1320, 928, 0, 0, 1320, 928);
  rows.forEach((r, i) => {
    const [bx0, by0, bx1, by1] = BULLETS[i % BULLETS.length]; const y = 928 + i * 88;
    g.drawImage(P.img, bx0, by0, bx1 - bx0, by1 - by0, 32, y + 4, bx1 - bx0, by1 - by0);
    g.font = '66px "InterD"'; g.fillStyle = X_INK; g.textBaseline = 'alphabetic'; g.fillText(r, 117, y + 58);
    if (i === hiRow && hiAmt > 0) { const w = g.measureText(r).width; g.globalCompositeOperation = 'multiply'; g.globalAlpha = hiAmt; g.fillStyle = HL; g.fillRect(110, y + 4, w + 18, 76); g.globalAlpha = 1; g.globalCompositeOperation = 'source-over'; }
  });
  g.drawImage(P.img, 0, 928, 1320, 252, 0, 928 + 88 * n, 1320, 252);
  P.tx.repeat.set(1, H / P.maxH); P.tx.offset.set(0, 1 - H / P.maxH); P.tx.needsUpdate = true;
}
function card(tex, w, h, envTex) {   // a glass-edged white card that stands in the hall
  const g = new THREE.Group();
  const edge = new THREE.Mesh(new THREE.BoxGeometry(w + 0.06, h + 0.06, 0.03), new THREE.MeshStandardMaterial({ color: 0x0b0b0e, metalness: 0.9, roughness: 0.2, envMap: envTex, envMapIntensity: 0.6 }));
  edge.position.z = -0.018; g.add(edge);
  const face = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ map: tex, toneMapped: false })); face.material.color.setScalar(0.97); g.add(face);
  g.userData.face = face; return g;
}
function clockTex() { const c = document.createElement('canvas'); c.width = c.height = 512; const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.userData.c = c; t.userData.key = ''; return t; }
function drawClock(T_, h, m) {
  const key = h + ':' + Math.round(m * 10); if (key === T_.userData.key) return; T_.userData.key = key;
  const g = T_.userData.c.getContext('2d'); g.clearRect(0, 0, 512, 512);
  g.fillStyle = '#f4f1ea'; g.beginPath(); g.arc(256, 256, 248, 0, Math.PI * 2); g.fill(); g.lineWidth = 14; g.strokeStyle = '#1d1c1a'; g.stroke();
  g.fillStyle = '#1d1c1a'; g.font = '62px "Anton"'; g.textAlign = 'center'; g.textBaseline = 'middle';
  for (let i = 1; i <= 12; i++) { const a = i / 12 * Math.PI * 2; g.fillText(String(i), 256 + Math.sin(a) * 190, 256 - Math.cos(a) * 190); }
  const hand = (a, len, w) => { g.save(); g.translate(256, 256); g.rotate(a); g.lineCap = 'round'; g.lineWidth = w; g.beginPath(); g.moveTo(0, 18); g.lineTo(0, -len); g.stroke(); g.restore(); };
  g.strokeStyle = '#1d1c1a'; hand((h % 12 + m / 60) / 12 * Math.PI * 2, 120, 18); hand(m / 60 * Math.PI * 2, 180, 11);
  g.fillStyle = '#ff4248'; g.beginPath(); g.arc(256, 256, 14, 0, Math.PI * 2); g.fill(); T_.needsUpdate = true;
}
function subsAtlas() {   // 64 subscription chips in one texture (8 x 8), each instance maps to its own cell
  return L.canvasTex(2048, 1024, (g, w, h) => {
    const cw = w / 8, ch = h / 8; g.textAlign = 'center'; g.textBaseline = 'middle';
    SUBS.forEach((s, i) => { const x = (i % 8) * cw, y = Math.floor(i / 8) * ch;
      g.fillStyle = '#16161b'; g.beginPath(); g.roundRect(x + 6, y + 10, cw - 12, ch - 20, 22); g.fill(); g.strokeStyle = '#3a3a44'; g.lineWidth = 3; g.stroke();
      g.fillStyle = i % 5 === 0 ? '#74e36a' : '#ece6d8'; g.font = '34px "JBB"'; g.fillText('● ' + s, x + cw / 2, y + ch / 2 + 2); });
  });
}
function hudPill() {
  const c = document.createElement('canvas'); c.width = 1300; c.height = 170; const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.userData.c = c; t.userData.key = '';
  const m = new THREE.Mesh(new THREE.PlaneGeometry(1, 170 / 1300), new THREE.MeshBasicMaterial({ map: t, transparent: true, depthTest: false, depthWrite: false, toneMapped: false }));
  m.renderOrder = 999; m.userData.t = t; return m;
}
function drawPill(P, subscribed, press) {
  const key = subscribed + ':' + press.toFixed(2); if (key === P.userData.t.userData.key) return; P.userData.t.userData.key = key;
  const g = P.userData.t.userData.c.getContext('2d'); g.clearRect(0, 0, 1300, 170);
  const pw = 420; g.fillStyle = subscribed ? '#2a2a2e' : '#e3222b'; g.beginPath(); g.roundRect(8, 25, pw, 120, 60); g.fill();
  g.fillStyle = '#ffffff'; g.font = '62px "Anton"'; g.textBaseline = 'middle'; g.fillText(subscribed ? 'SUBSCRIBED' : 'SUBSCRIBE', 128, 88);
  g.beginPath(); g.arc(78, 80, 22, Math.PI, 0); g.lineTo(100, 104); g.lineTo(56, 104); g.closePath(); g.fill(); g.beginPath(); g.arc(78, 110, 7, 0, Math.PI * 2); g.fill();
  g.font = '40px "InterS"'; g.fillStyle = '#ece6d8'; g.shadowColor = 'rgba(0,0,0,0.8)'; g.shadowBlur = 12; g.fillText('@adita_zzz  ·  songs about tech life', pw + 34, 88); g.shadowBlur = 0;
  if (press > 0) { g.strokeStyle = `rgba(255,255,255,${0.8 * (1 - press)})`; g.lineWidth = 6; g.beginPath(); g.arc(8 + pw * 0.62, 95, 30 + 70 * press, 0, Math.PI * 2); g.stroke(); }
  P.userData.t.needsUpdate = true;
}

async function buildV2() {
  T.chief = ls("Chief Executive of What's Next"); T.feet = ls('Director of the Missing Feet'); T.vibes = ls('Head of Vibes and Synergy');
  T.me = ls('Chief of Artificial Me'); T.t33 = ls('A thought leader by half past three'); T.t4 = ls("By four I've got a TED Talk fee!");
  T.brk = ls('What are your qualifications?'); T.sub = ls('I have a subscription.'); T.towhat = ls('To what?'); T.every = ls('Everything.');
  T.ch2 = ls('Look what I can do!', 4); T.slop = wt("I'm a Senior Slopcore Architect", 'Slopcore'); T.arch = wt("I'm a Senior Slopcore Architect", 'Architect');
  V = {};
  const slopImg = (await M.image('post_slopcore.png')).image, profImg = (await M.image('profile.png')).image;
  // the post: rises out of the floor at the -x side of the hall, facing the middle
  V.post = postCanvas(slopImg, [[435, 197, 998, 259], [246, 282, 541, 332]]); drawPost(V.post, [0, 0]);
  V.postCard = card(V.post.tx, 1320 * PX * 1.3, 880 * PX * 1.3, envTex);
  const aP = THREE.MathUtils.degToRad(200), aM = THREE.MathUtils.degToRad(252), aC = THREE.MathUtils.degToRad(306);
  const at = (a, r, y) => V3(Math.cos(a) * r, y, Math.sin(a) * r);
  V.postPos = at(aP, 3.1, 1.75); V.postCard.position.copy(V.postPos); V.postCard.lookAt(0, 1.75, 0); hall.add(V.postCard);
  V.postMirror = V.postCard.clone(); mirror.add(V.postMirror);
  V.stamp = new THREE.Mesh(new THREE.PlaneGeometry(0.95, 0.375), new THREE.MeshBasicMaterial({ map: stampTex('RECEIPT', 'OCT 27, 2026', '#ff4248'), transparent: true, depthWrite: false, toneMapped: false }));
  V.postCard.add(V.stamp); V.stamp.position.set((1060 - 660) * PX * 1.3, (440 - 380) * PX * 1.3, 0.01);
  // her profile, as a monolith on a plinth
  V.prof = profileCanvas(profImg); drawProfile(V.prof, [], -1, 0);
  V.profMat = new THREE.MeshBasicMaterial({ map: V.prof.tx, toneMapped: false }); V.profMat.color.setScalar(0.97);
  V.profMesh = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), V.profMat);
  V.profEdge = new THREE.Mesh(new THREE.BoxGeometry(1, 1, 0.04), new THREE.MeshStandardMaterial({ color: 0x0b0b0e, metalness: 0.9, roughness: 0.22, envMap: envTex, envMapIntensity: 0.6 }));
  V.plinth = new THREE.Mesh(new THREE.BoxGeometry(2.6, 0.42, 0.6), new THREE.MeshStandardMaterial({ color: 0x0c0c0f, metalness: 0.7, roughness: 0.3, envMap: envTex, envMapIntensity: 0.5 }));
  V.mono = new THREE.Group(); V.mono.add(V.profEdge, V.profMesh, V.plinth); V.monoPos = at(aM, 3.2, 0); V.mono.position.copy(V.monoPos); V.mono.lookAt(0, 0, 0); hall.add(V.mono);
  V.monoMirror = V.mono.clone(); mirror.add(V.monoMirror);
  // missing feet: a screen playing her TED Talk, 'feet: 404'
  V.feet = new Screen(1.5, 1.5 * 0.5625, envTex); V.feet.show('H1', 10); V.feetPos = at(THREE.MathUtils.degToRad(292), 3.0, 1.45); V.feet.root.position.copy(V.feetPos); V.feet.root.lookAt(0, 1.35, 0); hall.add(V.feet.root);
  V.feetTag = L.textPlane('⚠ feet: 404', { h: 0.13, font: L.FONT.monoB, size: 72, color: '#ff4248', glow: 14, bg: 'rgba(10,6,6,0.85)' }); V.feet.root.add(V.feetTag); V.feetTag.position.set(-0.36, -0.30, 0.02);
  // clones of her real avatar
  const av = L.canvasTex(256, 256, (g) => { g.fillStyle = '#fff'; g.beginPath(); g.arc(128, 128, 126, 0, Math.PI * 2); g.fill(); g.save(); g.beginPath(); g.arc(128, 128, 116, 0, Math.PI * 2); g.clip(); g.drawImage(profImg, 14, 344, 254, 254, 2, 2, 252, 252); g.restore(); });
  V.clones = []; for (let i = 0; i < 6; i++) { const m = new THREE.Mesh(new THREE.CircleGeometry(0.16, 40), new THREE.MeshBasicMaterial({ map: av, transparent: true, toneMapped: false })); m.visible = false; hall.add(m); V.clones.push(m); }
  // the clock and the fee
  V.clockTex = clockTex(); V.clock = new THREE.Mesh(new THREE.CircleGeometry(0.62, 64), new THREE.MeshBasicMaterial({ map: V.clockTex, transparent: true, toneMapped: false }));
  V.clockPos = at(aC, 3.0, 2.25); V.clock.position.copy(V.clockPos); V.clock.lookAt(0, 2.25, 0); hall.add(V.clock);
  V.fee = L.textPlane('TED TALK FEE  ·  $$$$', { h: 0.17, font: L.FONT.monoB, size: 80, color: '#74e36a', glow: 16, bg: 'rgba(6,12,6,0.9)' });
  V.fee.position.copy(at(THREE.MathUtils.degToRad(302), 2.95, 1.42)); V.fee.lookAt(0, 1.42, 0); hall.add(V.fee);
  // qualifications: the dialogue floats over the desk; her subscriptions pour down
  const mk = (s, col, h = 0.17) => { const m = L.textPlane(s, { h, font: L.FONT.monoB, size: 128, color: col, glow: 6, align: 'left' }); m.visible = false; m.renderOrder = 10; hall.add(m); return m; };
  V.dlg = [mk('● What are your qualifications?', '#ffa840'), mk('❯ I have a subscription.', '#ece6d8'), mk('● To what?', '#ffa840'), mk('❯ Everything.', '#ece6d8')];
  V.dlgT = [T.brk, T.sub, T.towhat, T.every];
  // the dialogue sits in a floating terminal window (dark glass, title bar): crisp on the bright studio, and a callback to part 1
  V.dlgPanel = new THREE.Mesh(new THREE.PlaneGeometry(2.5, 1.62), new THREE.MeshBasicMaterial({ transparent: true, depthWrite: false, toneMapped: false, map: L.canvasTex(1250, 810, (g, w, h) => {
    g.fillStyle = 'rgba(16,16,19,0.94)'; g.beginPath(); g.roundRect(4, 4, w - 8, h - 8, 34); g.fill(); g.strokeStyle = 'rgba(255,255,255,0.14)'; g.lineWidth = 3; g.stroke();
    g.fillStyle = 'rgba(255,255,255,0.06)'; g.beginPath(); g.roundRect(4, 4, w - 8, 74, [34, 34, 0, 0]); g.fill();
    [['#ff5f57', 50], ['#febc2e', 92], ['#28c840', 134]].forEach(([c, x]) => { g.fillStyle = c; g.beginPath(); g.arc(x, 41, 13, 0, Math.PI * 2); g.fill(); });
    g.fillStyle = 'rgba(236,230,216,0.55)'; g.font = '30px "JB"'; g.textAlign = 'center'; g.fillText('adita@studio  ~/look-what-i-can-do', w / 2, 52); }) }));
  V.dlgPanel.renderOrder = 9; V.dlgPanel.visible = false; hall.add(V.dlgPanel);
  const sa = subsAtlas(); const n = 360; const geo = new THREE.PlaneGeometry(0.62, 0.155);
  const rect = new Float32Array(n * 4); for (let i = 0; i < n; i++) { const k = i % SUBS.length; rect.set([(k % 8) / 8, 1 - (Math.floor(k / 8) + 1) / 8, 1 / 8, 1 / 8], i * 4); }
  geo.setAttribute('aRect', new THREE.InstancedBufferAttribute(rect, 4));
  const smat = new THREE.MeshBasicMaterial({ map: sa, toneMapped: false, side: THREE.DoubleSide, transparent: true });
  smat.onBeforeCompile = (sh) => { sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nattribute vec4 aRect;').replace('#include <uv_vertex>', '#include <uv_vertex>\n#ifdef USE_MAP\n vMapUv = uv * aRect.zw + aRect.xy;\n#endif'); sh.fragmentShader = sh.fragmentShader.replace('#include <map_fragment>', '#include <map_fragment>\n if (!gl_FrontFacing) diffuseColor.rgb = vec3(0.05, 0.05, 0.06);'); };
  V.subs = new THREE.InstancedMesh(geo, smat, n); V.subs.frustumCulled = false; hall.add(V.subs);
  const R = L.rng(21); V.subsP = Array.from({ length: n }, (_, i) => { const QA = THREE.MathUtils.degToRad(62 + (R() < 0.5 ? -1 : 1) * (22 + R() * 40)); const rr = 3.3 + R() * 1.0; return ({ x: Math.cos(QA) * rr, z: Math.sin(QA) * rr, t0: (i < 120 ? T.sub + R() * 1.4 : T.every - 0.1 + R() * 0.7), sp: 2.2 + R() * 1.6, rx: R() * 6, ry: R() * 6, rz: (R() - 0.5) * 2 }); });
  V.pill = hudPill(); cam.add(V.pill); V.pill.visible = false;
  V.camV2 = L.camPath([
    { t: T.v2 - 0.02, p: [0.55, 1.45, 0.65], l: [V.postPos.x, 1.7, V.postPos.z], fov: 40 },
    { t: T.chief - 0.2, p: [-0.35, 1.68, 0.18], l: [V.postPos.x, 1.76, V.postPos.z], fov: 38 },
  ]);
}

function monoFrame(t) {   // the profile monolith: rows typed in as she sings; the slab grows; the newest row highlighted
  const rows = []; let tNew = -1, hiRow = -1;
  for (const [sub, title] of TITLES) { const t0 = ls(sub); if (t < t0 - 0.05) break;
    const n = t0 < T.chief - 0.2 ? title.length : Math.floor(title.length * clamp((t - t0 + 0.05) / 0.42)); rows.push(title.slice(0, n)); tNew = t0; hiRow = rows.length - 1; }
  const hiAmt = 0.75 * (1 - sstep(tNew + 1.1, tNew + 1.6, t)) * (tNew >= T.chief - 0.2 ? 1 : 0);
  drawProfile(V.prof, rows, hiRow, hiAmt);
  const w = 1320 * PX, hgt = V.prof.h * PX, y0 = 0.42;
  V.profMesh.scale.set(w, hgt, 1); V.profMesh.position.set(0, y0 + hgt / 2, 0.022);
  V.profEdge.scale.set(w + 0.06, hgt + 0.06, 1); V.profEdge.position.set(0, y0 + hgt / 2, 0); V.plinth.position.set(0, 0.21, -0.1);
  V.monoMirror.children.forEach((c, i) => { c.position.copy(V.mono.children[i].position); c.scale.copy(V.mono.children[i].scale); });
  return { hgt, y0 };
}

async function frameV2(t) {
  v2Vis(true);
  const pulse = L.beatPulse(t, 7);
  FIELD.hidden.clear(); FIELD.update(t, { bright: t >= T.brk - 0.1 ? lerp(0.38, 0.2, sstep(T.brk - 0.1, T.brk + 0.4, t)) : 0.38, pulse: pulse * 0.5 }); FIELD.atlases().forEach((a) => M.use(a));
  RING.userData.letters.forEach((m) => { m.material.opacity = 0.85; m.material.color.setScalar(1); m.visible = true; });
  drawTerm(t); if (laptop.dispMat.map !== TERM) { laptop.dispMat.map = TERM; laptop.dispMat.needsUpdate = true; }
  sleek(); 
  for (const h of Object.values(HEROES)) { h.root.visible = false; h.mirrorMesh.visible = false; } LABEL.visible = false; TRAIL.visible = false;
  // --- the post rising out of the floor, highlighted, stamped
  const rise = easeOut((t - (T.v2 - 0.1)) / 0.5);
  V.postCard.position.copy(V.postPos).add(V3(0, (1 - rise) * -1.9, 0)); V.postMirror.position.copy(V.postCard.position); V.postMirror.quaternion.copy(V.postCard.quaternion);
  drawPost(V.post, [(t - T.slop + 0.1) / 0.3, (t - T.arch - 0.05) / 0.22]);
  const ks = easeOut((t - T.arch - 0.45) / 0.12); V.stamp.visible = ks > 0; V.stamp.material.opacity = Math.min(1, ks * 1.4); V.stamp.scale.setScalar(1.6 - 0.6 * ks);
  // --- the monolith
  const { hgt, y0 } = monoFrame(t);
  // --- gags
  const kf = easeOut((t - T.feet) / 0.25) * (1 - sstep(T.vibes + 0.3, T.vibes + 0.6, t));
  V.feet.root.visible = kf > 0.01; V.feet.root.scale.setScalar(Math.max(0.001, kf)); if (kf > 0.01) M.use('H1');
  V.feet.mat.color.setScalar(kf); V.feetTag.material.opacity = kf;
  const mono = V.mono; const avW = mono.localToWorld(V3(-1320 * PX / 2 + 140 * PX, y0 + hgt - 472 * PX, 0.05));
  V.clones.forEach((m, i) => { const k = easeOut((t - T.me - i * 0.14) / 0.25); m.visible = k > 0.01 && i < 5;
    const dst = mono.localToWorld(V3(-0.82 + i * 0.41, y0 + hgt + 0.3 + 0.05 * Math.sin((t - T.me) * 3 + i), 0.08));
    m.position.lerpVectors(avW, dst, k);
    m.scale.setScalar(0.4 + 0.6 * k); m.lookAt(cam.position); });
  const kc = easeOut((t - T.t33) / 0.3); V.clock.visible = kc > 0.01; V.clock.scale.setScalar(Math.max(0.001, kc));
  if (kc > 0.01) { const spin = sstep(T.t4 - 0.05, T.t4 + 0.35, t); drawClock(V.clockTex, 3, lerp(30, 60, spin)); }
  const kfee = easeOut((t - T.t4 - 0.2) / 0.3); V.fee.visible = kfee > 0.01; V.fee.material.opacity = kfee; V.fee.rotation.z = Math.sin((t - T.t4) * 5) * 0.12 * (1 - kfee * 0.6);
  // --- qualifications
  const inBreak = t >= T.brk - 0.05;
  V.dlg.forEach((m, i) => { const k = easeOut((t - V.dlgT[i] + 0.02) / 0.18); m.visible = inBreak && k > 0.01; m.material.opacity = k; });
  const QA = THREE.MathUtils.degToRad(62); const qdir = V3(Math.cos(QA), 0, Math.sin(QA));
  const fadeQ = 1 - sstep(T.ch2 - 0.42, T.ch2 - 0.3, t);
  if (inBreak) {
    const right = V3(-qdir.z, 0, qdir.x);                                      // screen-left edge of the text block, seen from the middle
    const base = qdir.clone().multiplyScalar(2.6).add(V3(0, 2.55, 0)).addScaledVector(right, -1.1);
    V.dlg.forEach((m, i) => { m.position.copy(base).add(V3(0, -i * 0.36, 0)); m.lookAt(m.position.clone().sub(qdir)); m.material.opacity *= fadeQ; });
    const kpan = easeOut((t - T.brk + 0.12) / 0.22) * fadeQ;
    V.dlgPanel.visible = kpan > 0.01; V.dlgPanel.material.opacity = kpan; V.dlgPanel.position.copy(base).addScaledVector(right, 1.05).add(V3(0, -0.47, 0)).addScaledVector(qdir, 0.03);
    V.dlgPanel.lookAt(V.dlgPanel.position.clone().sub(qdir)); V.dlgPanel.scale.setScalar(0.94 + 0.06 * kpan);
  } else V.dlgPanel.visible = false;
  const _m = new THREE.Matrix4(), _q = new THREE.Quaternion(), _s = new THREE.Vector3(1, 1, 1), _e = new THREE.Euler();
  V.subsP.forEach((p, i) => { const x = t - p.t0; let sc = 1;
    if (x < 0) { sc = 0.00001; } const y = 7.5 - x * p.sp - 0.5 * x * x;
    _e.set(p.rx + x * 2.0, p.ry + x * 1.4, p.rz * x); _q.setFromEuler(_e); _s.setScalar(y < -0.5 ? 0.00001 : sc);
    _m.compose(V3(p.x, Math.max(-0.5, y), p.z), _q, _s); V.subs.setMatrixAt(i, _m); });
  V.subs.instanceMatrix.needsUpdate = true;
  // --- the subscribe ask, on 'I have a subscription.'
  const kp = 0;   // no subscribe ask mid-song: she wants it only on the end card
  V.pill.visible = kp > 0.01;
  if (V.pill.visible) { const press = clamp((t - (T.sub + 0.25)) / 0.35); drawPill(V.pill, t > T.sub + 0.4, press > 0 && press < 1 ? press : 0); V.pill.material.opacity = kp;
  }
  // --- camera
  let c;
  if (t < T.chief - 0.2) c = V.camV2(t);
  else if (t < T.brk - 0.05) {
    // whip to the monolith, then crane up with it as it grows
    const k = expOut((t - (T.chief - 0.2)) / 0.32);
    const look0 = V3(V.postPos.x, 1.72, V.postPos.z); const mono = V3(V.monoPos.x, y0 + hgt * 0.62, V.monoPos.z);
    const dir = V3(-V.monoPos.x, 0, -V.monoPos.z).normalize();
    const want = V3(V.monoPos.x, 0, V.monoPos.z).addScaledVector(dir, 3.05).add(V3(0.0, 0.85 + hgt * 0.42, 0)).add(V3(dir.z, 0, -dir.x).multiplyScalar(-0.55));
    const gagMix = sstep(T.feet - 0.3, T.feet + 0.4, t) * (1 - sstep(T.vibes, T.vibes + 0.8, t)) * 0.5 + sstep(T.t33 - 0.4, T.t33 + 0.6, t) * 0.75;
    const side = V3(dir.z, 0, -dir.x);
    const wide = sstep(T.t33 - 0.4, T.t33 + 0.6, t);
    const p = want.clone().addScaledVector(side, gagMix * 0.9).addScaledVector(dir, gagMix * 0.7 + wide * 0.9);
    const meK = sstep(T.me - 0.2, T.me + 0.6, t) * (1 - wide);
    p.addScaledVector(dir, 0.5 * meK);
    const l = mono.clone().addScaledVector(side, gagMix * 1.5).add(V3(0, -gagMix * 0.35 + 0.11 * meK, 0));
    c = { p: V3(-0.35, 1.68, 0.18).lerp(p, k), l: look0.lerp(l, k), fov: lerp(38, 42, k) + wide * 6 + 3 * meK };
    finish.uniforms.uVel.value.set(0.06 * (1 - k) * (k > 0.02 ? 1 : 0), 0);
  } else {
    // the qualifications: a whip round to the open side of the hall, a slow push toward the question, then a dive into a screen behind it
    const k = (t - T.brk) / (T.ch2 - T.brk);
    const whip = expOut((t - (T.brk - 0.05)) / 0.34);
    const ang = lerp(THREE.MathUtils.degToRad(252 - 360), QA, whip);
    const fwd = V3(Math.cos(ang), 0, Math.sin(ang));
    const p = fwd.clone().multiplyScalar(-0.1 + 0.45 * easeIO(k)).add(V3(0, 2.22, 0));
    const look_ = fwd.clone().multiplyScalar(3.0).add(V3(0, 2.02, 0));
    finish.uniforms.uVel.value.set(-0.07 * (1 - whip) * (whip > 0.02 ? 1 : 0), 0);
    let best = 0, bd = 1e9; FIELD.slots.slice(0, 13).forEach((sl, i) => { if (sl.atlas[0] !== 'H') return; const d = Math.abs(Math.atan2(Math.sin(sl.a - QA), Math.cos(sl.a - QA))); if (d < bd) { bd = d; best = i; } });
    const s0 = FIELD.slots[best]; const dive = easeIO(clamp((t - (T.ch2 - 0.4)) / 0.4));
    const nrm = V3(Math.sin(s0.yaw), 0, Math.cos(s0.yaw)); const pd = s0.pos.clone().addScaledVector(nrm, 1.45);   // ends with the screen exactly filling the frame (fov 36): the city opens on the same full-frame window
    c = { p: p.clone().lerp(pd, dive), l: look_.clone().lerp(s0.pos, Math.min(1, dive * 1.3)), fov: lerp(40, 36, dive) };
    if (t > T.ch2 - 0.3) { const Hh = HEROES.H; FIELD.hidden.add(best); FIELD.update(t, { bright: 0.2, pulse: 0 }); Hh.root.visible = true; Hh.mirrorMesh.visible = true; Hh.show('H1', 6); Hh.mat.color.setScalar(1.0);
      const q_ = new THREE.Quaternion().setFromAxisAngle(THREE.Object3D.DEFAULT_UP, s0.yaw); Hh.root.position.copy(s0.pos); Hh.root.quaternion.copy(q_); Hh.mirrorMesh.position.copy(s0.pos); Hh.mirrorMesh.quaternion.copy(q_); }
  }
  setCam(c, 0.01, t);
  if (V.pill.visible) { const d = 1.0; const hh = 2 * d * Math.tan(THREE.MathUtils.degToRad(cam.fov / 2)); const ww = hh * cam.aspect; const s = ww * 0.5;
    V.pill.scale.set(s, s, 1); V.pill.position.set(-ww / 2 + s / 2 + ww * 0.03, hh / 2 - s * (170 / 1300) / 2 - hh * 0.045, -d); }
}

export const range = () => [T.ch1 - 0.05, T.ch2 - 0.05];
export function covers(t) { return t >= T.ch1 - 0.05 && t < T.ch2 - 0.05; }
export async function frame(t, ctx) { if (t >= T.v2 - 0.02) await frameV2(t); else await frameHall(t); return { scene: hall, camera: cam }; }
export { T as HT };
