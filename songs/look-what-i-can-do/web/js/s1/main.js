// Look What I Can Do v3 · S1, chorus 1 (song 42.933-57.10, frames 1288-1712), in the world of "Great Idea, Ted" and
// "I have a blocker.": the blue-hour city, the floating video-call rooms, the tower clock, the billboards, the cast.
// renderTime(t) draws the frame at song time t, deterministically (any frame, any order).
//
// The story: we dive out of her laptop (the terminal that said TOO LATE!) and swing round to her face. On every hook
// the meeting doubles: each new room slides out from behind the one that made it, 1 -> 2 -> 4 ... -> 256, and every room
// but hers has one of her music videos as its virtual background. The tower clock counts the people in the meeting.
// Then the 256 rooms fly into LOOK WHAT I CAN DO, word by word as she sings it (the font is drawn so the letters take
// exactly 256 rooms). "I don't know how I got here": we dive into the letter I, and there she is, the I.
// "But I brought my laptop too!": she picks it up and turns it round. It says git push --force.
import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { ShaderPass } from 'three/addons/postprocessing/ShaderPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import * as L from './lib.js';
import { buildCity, ROOF_Y } from './city.js';
import { Room, CAST, RW, RH, RD, GAP, SCR_W, coverGeo } from './rooms.js';
import { setLOD } from './mannequin.js';
import * as B from './boards.js';
import * as MED from './media.js';
const { clamp, lerp, sstep, easeIO, easeOut, easeIn, env, rng } = L;
const V = (x, y, z) => new THREE.Vector3(x, y, z);

const q = new URLSearchParams(location.search);
const W = +q.get('w') || 1920, H = +q.get('h') || 1080;
export const T0 = 1288 / 30, T1 = 1713 / 30;   // this section's frames: T0 <= t < T1

// ---------------------------------------------------------------- renderer + the Great Idea, Ted look
const renderer = new THREE.WebGLRenderer({ antialias: false, preserveDrawingBuffer: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(1); renderer.setSize(W, H); renderer.info.autoReset = false;
renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.0;
document.body.appendChild(renderer.domElement);
const scene = new THREE.Scene(); scene.fog = new THREE.FogExp2(0x1b2146, 0.0032);
const cam = new THREE.PerspectiveCamera(38, W / H, 0.02, 2400); scene.add(cam);
scene.add(new THREE.HemisphereLight(0x8fa0d8, 0x1a1420, 1.15));
const key = new THREE.DirectionalLight(0xffe3c4, 1.6); key.position.set(-8, 14, 22); scene.add(key);
L.RIM.value.set(0xffc2a8);   // the rim light picks up the peach horizon

const composer = new EffectComposer(renderer, new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType }));
composer.addPass(new RenderPass(scene, cam));
const bloom = new UnrealBloomPass(new THREE.Vector2(Math.round(W / 4), Math.round(H / 4)), 0.45, 0.38, 0.86); composer.addPass(bloom);   // quarter-res: the CPU renderer can afford it
// the finish: Great Idea, Ted's vignette + chorus gold, plus a directional blur for the whip and a zoom blur for the dive
const finish = new ShaderPass({
  uniforms: { tDiffuse: { value: null }, uVig: { value: 0.3 }, uGold: { value: 0 }, uVel: { value: new THREE.Vector2() }, uZoom: { value: 0 }, uTime: { value: 0 }, uGrain: { value: 0.012 }, uTaps: { value: 0 } },
  vertexShader: `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
  fragmentShader: `uniform sampler2D tDiffuse; uniform float uVig, uGold, uZoom, uTime, uGrain; uniform vec2 uVel; uniform int uTaps; varying vec2 vUv;
    float h(vec2 p){ return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453); }
    void main(){ vec2 d = vUv - 0.5; vec3 c = vec3(0.0);
      if (uTaps > 1) { float n = float(uTaps); for (int i = 0; i < 32; i++) { if (i >= uTaps) break; float k = float(i) / (n - 1.0) - 0.5; c += texture2D(tDiffuse, vUv + uVel * k - d * uZoom * (k + 0.5)).rgb; } c /= n; }
      else c = texture2D(tDiffuse, vUv).rgb;
      c *= 1.0 - uVig * pow(length(d * vec2(1.0, 0.9)) * 1.45, 2.4);
      c = mix(c, c * vec3(1.12, 1.0, 0.82) + vec3(0.03, 0.015, 0.0), uGold);
      c += (h(vUv * 1000.0 + fract(uTime * 7.13)) - 0.5) * uGrain;
      gl_FragColor = vec4(c, 1.0); }` });
composer.addPass(finish); composer.addPass(new OutputPass());
// the hand-off: for the first frames the exact last frame of part 1 sits on top (display space), fading into the 3D
// screen that shows the same picture at the same size
const over = new ShaderPass({ uniforms: { tDiffuse: { value: null }, tOver: { value: null }, uMix: { value: 0 } },
  vertexShader: `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
  fragmentShader: `uniform sampler2D tDiffuse, tOver; uniform float uMix; varying vec2 vUv;
    void main(){ vec4 c = texture2D(tDiffuse, vUv); if (uMix > 0.0) c.rgb = mix(c.rgb, texture2D(tOver, vUv).rgb, uMix); gl_FragColor = c; }` });
composer.addPass(over);
window.__cfg = (o) => {
  if ('aniso' in o) scene.traverse((m) => { const ms = m.material ? (Array.isArray(m.material) ? m.material : [m.material]) : []; for (const mt of ms) if (mt.map && !mt.map.isRenderTargetTexture && mt.map.anisotropy !== o.aniso) { mt.map.anisotropy = o.aniso; if (mt.map.image) mt.map.needsUpdate = true; } });
  if ('bloomRes' in o) bloom.setSize(Math.round(W * o.bloomRes), Math.round(H * o.bloomRes));
  if ('bloom' in o) bloom.enabled = o.bloom; if ('finish' in o) finish.enabled = o.finish; if ('scene' in o) scene.visible = o.scene; };

// ---------------------------------------------------------------- song times
const TM = {};
function times() {
  const w = (sub, word, nl = 0, nw = 0) => { const Ln = L.TIMING.lines.filter((x) => x.text.toLowerCase().includes(sub.toLowerCase()))[nl];
    const norm = (s) => s.toLowerCase().replace(/[^a-z0-9']/g, ''); let k = 0; for (let i = 0; i < Ln.words.length; i++) if (norm(Ln.words[i]) === norm(word)) { if (k === nw) return Ln.wt[i]; k++; } throw new Error(sub + '/' + word); };
  // the four hooks in this chorus are the 1st-4th "Look what I can do!" lines of the song
  TM.h = [0, 1, 2, 3].map((n) => ({ look: w('Look what I can do', 'Look', n), what: w('Look what I can do', 'what', n), i: w('Look what I can do', 'I', n), can: w('Look what I can do', 'can', n), do: w('Look what I can do', 'do', n) }));
  TM.thing1 = w('I made a thing that made', 'thing', 0, 0); TM.thing2 = w('I made a thing that made', 'thing', 0, 1); TM.two = w('That made another two', 'two', 0);
  TM.dont = w("I don't know how I got here", "don't"); TM.how = w("I don't know how I got here", 'how'); TM.here = w("I don't know how I got here", 'here');
  TM.but = w('But I brought my laptop too', 'But'); TM.brought = w('But I brought my laptop too', 'brought'); TM.laptop = w('But I brought my laptop too', 'laptop'); TM.too = w('But I brought my laptop too', 'too');
  // her mouth: every sung word in this section opens it a little
  TM.words = L.TIMING.lines.filter((x) => x.s >= T0 - 0.2 && x.s < T1).flatMap((x) => x.wt);
  // the meeting doubles on the hits: do! do! thing thing two! then Look-what-I on the third hook
  TM.gen = [-1, TM.h[0].do, TM.h[1].do, TM.thing1, TM.thing2, TM.two, TM.h[2].look, TM.h[2].what, TM.h[2].i];
  TM.genDur = [0, 0.62, 0.62, 0.55, 0.5, 0.5, 0.42, 0.36, 0.34];
  TM.words4 = [TM.h[3].look, TM.h[3].what, TM.h[3].i, TM.h[3].can, TM.h[3].do];   // the letters land on these
}

// ---------------------------------------------------------------- the meeting: 256 rooms
const N = 256, N3D = +(q.get('n3d') || 16), LOD_D = 62;   // rooms 0..N3D-1 are full 3D rooms (photographs when farther than LOD_D); the rest are photographs
const PX = RW + GAP, PY = RH + GAP;
const BASE = V(0, ROOF_Y + 1.7, -13);            // her room, floating just over the standup roof (as in Great Idea, Ted)
const genOf = (i) => (i === 0 ? 0 : 32 - Math.clz32(i));
const parentOf = (i) => i - (1 << (genOf(i) - 1));
// each doubling copies the whole meeting next to itself: right, up, left x2, up x2, right x4, up x4, left x8, up x8
function slotOf(i) { let x = 0, y = 0; for (let b = 0; b < 8; b++) if ((i >> b) & 1) { const k = 1 << (b >> 1); if (b % 2 === 0) x += (b % 4 === 0 ? 1 : -1) * k; else y += k; } return [x, y]; }
const slotWorld = (i) => { const [x, y] = slotOf(i); return V(BASE.x + x * PX, BASE.y + y * PY, BASE.z); };
const countAt = (t) => { let n = 1; for (let g = 1; g <= 8; g++) if (t >= TM.gen[g]) n = 1 << g; return n; };

// the hook in a 5x9 room-font; drawn so the whole phrase takes exactly 256 rooms
const FONT9 = {
  L: ['X....', 'X....', 'X....', 'X....', 'X....', 'X....', 'X....', 'X....', 'XXXXX'],
  O: ['.XXX.', 'X...X', 'X...X', 'X...X', 'X...X', 'X...X', 'X...X', 'X...X', '.XXX.'],
  K: ['X...X', 'X..X.', 'X.X..', 'XX...', 'X....', 'XX...', 'X.X..', 'X..X.', 'X...X'],
  W: ['X...X', 'X...X', 'X...X', 'X...X', 'X...X', 'X.X.X', 'X.X.X', 'XX.XX', 'X...X'],
  H: ['X...X', 'X...X', 'X...X', 'X...X', 'XXXXX', 'X...X', 'X...X', 'X...X', 'X...X'],
  A: ['..X..', '.X.X.', 'X...X', 'X...X', 'XXXXX', 'X...X', 'X...X', 'X...X', 'X...X'],
  T: ['XXXXX', '..X..', '..X..', '..X..', '..X..', '..X..', '..X..', '..X..', '..X..'],
  I: ['XXX', '.X.', '.X.', '.X.', '.X.', '.X.', '.X.', '.X.', 'XXX'],
  C: ['.XXX.', 'X...X', 'X....', 'X....', 'X....', 'X....', 'X....', 'X...X', '.XXX.'],
  N: ['X...X', 'XX..X', 'X.X.X', 'X.X.X', 'X..XX', 'X...X', 'X...X', 'X...X', 'X...X'],
  D: ['XXX..', 'X..X.', 'X...X', 'X...X', 'X...X', 'X...X', 'X...X', 'X..X.', 'XXX..'],
};
const LINES = [['LOOK', 'WHAT'], ['I', 'CAN', 'DO']];
function letterPixels() {   // -> [{x, y (world), word 0..4, iStem (her pixel)}]
  const px = []; let wordN = 0; const lineCols = LINES.map((ws) => ws.reduce((a, w) => a + [...w].reduce((b, ch) => b + FONT9[ch][0].length, 0) + (w.length - 1), 0) + 3 * (ws.length - 1));
  const rowsTot = 9 + 2 + 9;
  LINES.forEach((ws, li) => { let col = -lineCols[li] / 2;
    ws.forEach((w, wi) => { [...w].forEach((ch, ci) => { const G = FONT9[ch], gw = G[0].length;
      G.forEach((row, r) => [...row].forEach((c, cc) => { if (c !== 'X') return;
        const gx = col + cc + 0.5, gy = rowsTot / 2 - (li * 11 + r) - 0.5;
        px.push({ gx, gy, word: wordN, her: ch === 'I' && cc === 1 && r === 4 }); }));
      col += gw + (ci < w.length - 1 ? 1 : 0); }); col += 3; wordN++; }); });
  return px;
}
const LET_C = V(BASE.x - 2.5 * PX, 116, BASE.z);   // the letters' centre: over the grid's centre column, up in the sky above every tower (a sky title, as in Great Idea, Ted)
const R = [];   // logical rooms: { i, cast, video, slot, letter, fly: {t0, d, arc} }
let ROOMS3D = [], IMP = null, HERO = null;

// who is in each room: her (room 0); the Great Idea, Ted cast with her videos as virtual backgrounds; and, as feeds that
// fill their square like a webcam, the Claude robot and the purple GT3 RS from Asking for a Friend (she wants them seen:
// the first two rooms she makes are theirs, and they sit right above and below her in the letter I)
const FEED_KEYS = { robot: ['claude_eyes', 'claude_button', 'claude_memo'], car: ['gt3_desert', 'gt3_side', 'gt3_house', 'gt3_plate', 'gt3_night', 'gt3_wheel'] };
const FEED_NAME = { robot: 'Claude', car: 'GT3 RS' };
function setIdentity(r, kind, n) {
  const list = (FEED_KEYS[kind] || []).filter(MED.okKey);
  if (kind && list.length) { const k = list[n % list.length]; r.feed = { key: k, name: FEED_NAME[kind] }; r.video = k; r.ptype = 'f:' + kind; r.cast = 0; return; }
  r.feed = null; r.ptype = 'c:' + r.cast;
}
function planRooms() {
  const feedSet = new Set([...FEED_KEYS.robot, ...FEED_KEYS.car]);
  const clips = MED.clipList().filter((k) => !feedSet.has(k)); const castIdx = [1, 2, 3, 4, 5, 6, 7, 8, 10, 11];   // the cast (Greg's camera is off)
  const rr = rng(4242); let nf = 0;
  for (let i = 0; i < N; i++) { const r = { i, cast: i === 0 ? 0 : castIdx[(i * 7 + (i >> 3)) % castIdx.length], video: i === 0 ? null : clips[(i * 5 + (i >> 4)) % clips.length], slot: slotWorld(i), h: rr() };
    const f = rr(); const kind = i === 1 ? 'robot' : i === 2 ? 'car' : i === 0 ? null : f < 0.1 ? 'robot' : f < 0.2 ? 'car' : null;
    setIdentity(r, kind, kind ? nf++ : 0); R.push(r); }
  // fit letter pixels to rooms: word by word, the rooms nearest that word (in the grid's own spread), then pixel by pixel
  const px = letterPixels(); if (px.length !== N) console.log('LETTER COUNT', px.length);
  const free = new Set(R.map((r) => r.i)); free.delete(0);
  const gridC = slotWorld(0).clone(); { let s = V(0, 0, 0); R.forEach((r) => s.add(r.slot)); gridC.copy(s.divideScalar(N)); }
  const toGridSpace = (p) => V(gridC.x + p.gx * 0.33 * PX, gridC.y + p.gy * 0.8 * PY, 0);   // the letters squeezed onto the grid, for matching only
  for (let w = 0; w < 5; w++) {
    const mine = px.filter((p) => p.word === w); const c = mine.reduce((a, p) => a.add(toGridSpace(p)), V(0, 0, 0)).divideScalar(mine.length);
    const need = mine.filter((p) => !p.her).length;
    const pick = [...free].sort((a, b) => R[a].slot.distanceToSquared(c) - R[b].slot.distanceToSquared(c) || a - b).slice(0, need); pick.forEach((k) => free.delete(k));
    const pool = new Set(pick);
    mine.sort((a, b) => a.gx - b.gx || b.gy - a.gy).forEach((p) => {
      let k = 0; if (!p.her) { const g = toGridSpace(p); k = [...pool].sort((a, b) => R[a].slot.distanceToSquared(g) - R[b].slot.distanceToSquared(g) || a - b)[0]; pool.delete(k); }
      R[k].letter = V(LET_C.x + p.gx * PX, LET_C.y + p.gy * PY, LET_C.z); R[k].word = w; });
  }
  { const hl = R[0].letter; const at = (dy) => R.find((r) => r.letter && Math.abs(r.letter.x - hl.x) < 0.1 && Math.abs(r.letter.y - (hl.y + dy * PY)) < 0.1);
    const up = at(1), dn = at(-1); if (up) setIdentity(up, 'robot', 0); if (dn) setIdentity(dn, 'car', 1); }
  // flights: each word's rooms land on the sung word (arrive ~0.1 s after it), staggered by how far they travel
  for (let w = 0; w < 5; w++) { const rs = R.filter((r) => r.word === w); const dmax = Math.max(...rs.map((r) => r.slot.distanceTo(r.letter)));
    rs.forEach((r) => { const d = r.slot.distanceTo(r.letter) / dmax; r.fly = { t0: TM.words4[w] - 0.5 + 0.12 * (1 - d) - 0.06 * r.h, d: 0.6, arc: 1.5 + 6 * r.h }; }); }
}

// where room i is at time t (and how big, and whether it exists yet)
function poseOf(i, t) {
  const r = R[i]; let p, s = 1;
  if (i === 0) p = r.slot.clone();
  else { const g = genOf(i), t0 = TM.gen[g], d = TM.genDur[g]; if (t < t0) return null;
    const u = clamp((t - t0) / d), par = poseOf(parentOf(i), Math.min(t, t0 + d)) || { p: R[parentOf(i)].slot };
    const st = par.p.clone().add(V(0, 0, -(RD + 0.35)));               // starts tucked in behind the room that made it
    const a = easeIO(clamp(u / 0.78)), b = easeOut(clamp((u - 0.32) / 0.68));
    p = V(lerp(st.x, r.slot.x, a), lerp(st.y, r.slot.y, a), lerp(st.z, r.slot.z, b)); s = lerp(0.92, 1, b); }
  if (r.fly && t > r.fly.t0) { const u = clamp((t - r.fly.t0) / r.fly.d), e = easeIO(u);
    p = V(lerp(r.slot.x, r.letter.x, e), lerp(r.slot.y, r.letter.y, e), lerp(r.slot.z, r.letter.z, e) + Math.sin(Math.PI * e) * r.fly.arc);
    s = 1 - 0.08 * Math.sin(Math.PI * e); }
  return { p, s };
}

// ---------------------------------------------------------------- the photographed rooms (one picture per cast member)
function buildImpostors() {
  const imps = R; const ptypes = [...new Set(imps.map((r) => r.ptype))];
  const FR = 0.045, TW = RW + 2 * FR + 0.02, TH = RH + 2 * FR + 0.02, PW = 640, PH = Math.round(PW * TH / TW);
  const pcam = new THREE.PerspectiveCamera(30, TW / TH, 0.1, 50); const D = (TH / 2) / Math.tan(THREE.MathUtils.degToRad(15));
  pcam.position.set(0, 0, D); pcam.lookAt(0, 0, 0); pcam.updateMatrixWorld(true);
  const ps = new THREE.Scene(); ps.add(new THREE.HemisphereLight(0x8fa0d8, 0x1a1420, 1.15)); ps.add(key.clone());
  const photos = {};
  for (const pt of ptypes) {
    const [kind, v] = pt.split(':'); const her = kind === 'c' && +v === 0;
    const room = kind === 'f' ? new Room(0, { feed: { key: 'none', name: FEED_NAME[v] } }) : her ? new Room(0, {}) : new Room(+v, { video: 'none' });
    if (!her) (room.back || room.panel).visible = false; ps.add(room.root);
    if (her) room.update({ t: 2.0, talk: 1, talkCol: 0x5ee08f, expr: { smile: 0.55, brows: [0.7, 0.15], lids: 0.18 } });
    else room.update({ t: 2.0 + (+v || 3) * 0.37, clap: 1, clapK: 0.9, expr: { smile: 0.9, open: 0.35, brows: 0.5 } });
    room.root.updateMatrixWorld(true);
    const rt = new THREE.WebGLRenderTarget(PW, PH, { type: THREE.HalfFloatType, generateMipmaps: true, minFilter: THREE.LinearMipmapLinearFilter, magFilter: THREE.LinearFilter, samples: 4 });
    renderer.setRenderTarget(rt); renderer.setClearColor(0x000000, 0); renderer.clear(); renderer.render(ps, pcam); renderer.setRenderTarget(null);
    photos[pt] = rt.texture; ps.remove(room.root);
  }
  renderer.setClearColor(0x000000, 1);
  // the hole in each photo is where the clip plays: the back wall for a room, the whole square for a feed
  const hole = (z, w, h) => { const a = new THREE.Vector3(-w / 2, -h / 2, z).project(pcam), b = new THREE.Vector3(w / 2, h / 2, z).project(pcam);
    const x0 = a.x * TW / 2, y0 = a.y * TH / 2, x1 = b.x * TW / 2, y1 = b.y * TH / 2; const g = coverGeo(x1 - x0 + 0.02, y1 - y0 + 0.02); g.translate((x0 + x1) / 2, (y0 + y1) / 2, -0.03); return g; };
  const holeGeo = { c: hole(-RD, RW, RH), f: hole(0, RW, RH) };
  const photoGeo = new THREE.PlaneGeometry(TW, TH);
  const backGeo = new THREE.BoxGeometry(RW + 0.1, RH + 0.1, 0.5); backGeo.translate(0, 0, -0.3);
  const meshes = { photo: {}, vid: {}, back: null };
  const cnt = (f) => Math.max(1, imps.filter(f).length);
  for (const pt of ptypes) { const tx = photos[pt]; tx.colorSpace = THREE.LinearSRGBColorSpace; meshes.photo[pt] = new THREE.InstancedMesh(photoGeo, new THREE.MeshBasicMaterial({ map: tx, alphaTest: 0.5 }), cnt((r) => r.ptype === pt)); }
  for (const vk of new Set(imps.filter((r) => r.video).map((r) => r.video + '|' + r.ptype[0]))) { const [k, h] = vk.split('|');
    meshes.vid[vk] = new THREE.InstancedMesh(holeGeo[h], new THREE.MeshBasicMaterial({ map: MED.texOf(k), color: h === 'f' ? 0xd8d8d8 : 0xd0d0d0 }), cnt((r) => r.video + '|' + r.ptype[0] === vk)); }
  meshes.back = new THREE.InstancedMesh(backGeo, L.clay(0x1a1b20, { rimAmt: 0.25 }), imps.length);
  [...Object.values(meshes.photo), ...Object.values(meshes.vid), meshes.back].forEach((m) => { m.frustumCulled = false; m.instanceMatrix.setUsage(THREE.DynamicDrawUsage); scene.add(m); });
  const slot = { photo: {}, vid: {}, back: 0 }; const map = [];
  imps.forEach((r) => { const vk = r.video + '|' + r.ptype[0]; slot.photo[r.ptype] = slot.photo[r.ptype] || 0; if (r.video) slot.vid[vk] = slot.vid[vk] || 0;
    map.push({ i: r.i, ph: [meshes.photo[r.ptype], slot.photo[r.ptype]++], vd: r.video ? [meshes.vid[vk], slot.vid[vk]++] : null, bk: slot.back++ }); });
  meshes.map = map; return meshes;
}
const _m4 = new THREE.Matrix4(), _q = new THREE.Quaternion(), _s = new THREE.Vector3(), ZERO = new THREE.Matrix4().makeScale(0, 0, 0);
function placeImpostors(t, use3D) {
  const vis = new Set();
  for (const e of IMP.map) { const ps = poseOf(e.i, t);
    if (!ps || use3D[e.i]) { e.ph[0].setMatrixAt(e.ph[1], ZERO); if (e.vd) e.vd[0].setMatrixAt(e.vd[1], ZERO); IMP.back.setMatrixAt(e.bk, ZERO); continue; }
    _m4.compose(ps.p, _q, _s.setScalar(ps.s)); e.ph[0].setMatrixAt(e.ph[1], _m4); if (e.vd) e.vd[0].setMatrixAt(e.vd[1], _m4); IMP.back.setMatrixAt(e.bk, _m4); vis.add(e.i); }
  [...Object.values(IMP.photo), ...Object.values(IMP.vid), IMP.back].forEach((m) => { m.instanceMatrix.needsUpdate = true; });
  return vis;
}
// ---------------------------------------------------------------- the letters light up: a soft mint halo behind every room
// as it lands in LOOK WHAT I CAN DO (her colour), flaring on the word, so the phrase reads as one neon sign made of rooms
let GLOW = null; const MINT = new THREE.Color(0x7fe0c2);
function buildGlow() {
  const GW = RW + 2.2, GH = RH + 2.0;   // the halo plane; its bright core is the room's own size, the blur spills past the edges
  const tex = L.canvasTex(256, Math.round(256 * GH / GW), (g, w, h) => { const ix = (GW - RW) / 2 / GW * w, iy = (GH - RH) / 2 / GH * h;
    g.filter = 'blur(20px)'; g.fillStyle = '#ffffff'; g.beginPath(); g.roundRect(ix, iy, w - 2 * ix, h - 2 * iy, 14); g.fill(); });
  tex.colorSpace = THREE.NoColorSpace;
  const m = new THREE.InstancedMesh(new THREE.PlaneGeometry(GW, GH), new THREE.MeshBasicMaterial({ map: tex, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false }), N);
  m.geometry.translate(0, 0, -(RD + 0.25));   // behind the whole room box
  m.frustumCulled = false; m.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
  for (let i = 0; i < N; i++) { m.setMatrixAt(i, ZERO); m.setColorAt(i, new THREE.Color(0, 0, 0)); }
  scene.add(m); GLOW = m;
}
const _c = new THREE.Color();
function placeGlow(t, camP) {
  for (let i = 0; i < N; i++) { const r = R[i]; let k = 0;
    if (r.fly) { const u = clamp((t - r.fly.t0) / r.fly.d); k = sstep(0.82, 1.0, u) * (0.5 + 0.5 * env(t, r.fly.t0 + r.fly.d, 0.04, 0.4)); }
    if (k > 0) k *= sstep(30, 70, camP.distanceTo(r.letter));   // a wide-shot effect: gone by the time we're close
    if (k < 0.004) { GLOW.setMatrixAt(i, ZERO); continue; }
    const ps = poseOf(i, t); _m4.compose(ps.p, _q, _s.setScalar(ps.s)); GLOW.setMatrixAt(i, _m4); GLOW.setColorAt(i, _c.copy(MINT).multiplyScalar(0.55 * k)); }
  GLOW.instanceMatrix.needsUpdate = true; GLOW.instanceColor.needsUpdate = true;
}

// ---------------------------------------------------------------- the world
let CITY, BOARD, HOOKTEX = [], TOWER, COUNTER, PILL_HERE, PILL_LAPTOP, TERM, GIT, SPILL;
async function build() {
  await L.loadFonts(); await L.loadTiming(); times();
  CITY = buildCity(); scene.add(CITY); CITY.userData.setDay(0);
  planRooms();
  TERM = await MED.image('/media/term_4293.jpg'); GIT = B.gitScreen();
  over.uniforms.tOver.value = TERM.clone(); over.uniforms.tOver.value.colorSpace = THREE.NoColorSpace; over.uniforms.tOver.value.needsUpdate = true;
  for (let i = 0; i < Math.min(N3D, N); i++) { const r = R[i]; setLOD(i > 0); const room = new Room(r.cast, r.feed ? { feed: r.feed } : { video: r.video }); room.R = r; scene.add(room.root); ROOMS3D.push(room); }
  setLOD(false);
  HERO = ROOMS3D[0]; HERO.screen.material.map = TERM; HERO.screen.material.color.setScalar(1); HERO.screen.material.needsUpdate = true;
  ROOMS3D.slice(1).forEach((rm) => { if (rm.screen) rm.screen.material.color.set(0x23324a); });
  IMP = buildImpostors(); buildGlow();
  // the billboard (the hook goes up word by word) and the tower clock, now a participant counter
  BOARD = B.billboardTower(-15, -40, 0.32, { bw: 12.8, bh: 7.2, y: 36.5, h: 44 }); scene.add(BOARD);
  for (let n = 0; n <= 5; n++) HOOKTEX.push(B.hookBoard(n));
  TOWER = new THREE.Group(); const tb = new THREE.Mesh(new THREE.BoxGeometry(11, 46, 7), new THREE.MeshBasicMaterial({ color: 0x14172c })); tb.position.y = 23; TOWER.add(tb);
  COUNTER = B.counterSign(); COUNTER.position.set(0, 44.5, 3.7); COUNTER.scale.setScalar(1.6); TOWER.add(COUNTER); TOWER.position.set(15, 0, -36); TOWER.rotation.y = -0.28; scene.add(TOWER);
  // the meeting's light on the roof: a soft warm pool under the rooms that spreads as the grid grows (no dead-black roof)
  SPILL = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.MeshBasicMaterial({ map: L.canvasTex(256, 256, (g, w, h) => { const gr = g.createRadialGradient(w / 2, h / 2, 0, w / 2, h / 2, w / 2);
    gr.addColorStop(0, 'rgba(255,226,190,1)'); gr.addColorStop(0.45, 'rgba(220,200,255,0.45)'); gr.addColorStop(1, 'rgba(0,0,0,0)'); g.fillStyle = gr; g.fillRect(0, 0, w, h); }), transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, opacity: 0.16 }));
  SPILL.rotation.x = -Math.PI / 2; scene.add(SPILL);
  PILL_HERE = B.pill('you are here', 'status', 0.9); PILL_LAPTOP = B.pill('laptop: brought', 'good', 0.44); scene.add(PILL_HERE, PILL_LAPTOP);
  window.ready = true;
}

// ---------------------------------------------------------------- the camera
// 1) the opening: from her laptop screen (full frame, the terminal), through it, out of her room, and a whip back to her face
function heroScreen() {   // world centre, normal (toward her), up of her laptop display
  HERO.root.updateMatrixWorld(true); const m = HERO.screen.matrixWorld;
  return { c: V(0, 0, 0).applyMatrix4(m), n: V(0, 0, 1).transformDirection(m), u: V(0, 1, 0).transformDirection(m) };
}
function heroLocal(x, y, z) { HERO.root.updateMatrixWorld(true); return V(x, y, z).applyMatrix4(HERO.root.matrixWorld); }
function heroFace() { HERO.root.updateMatrixWorld(true); return HERO.man.head.getWorldPosition(V(0, 0, 0)); }
const FOV0 = 38, HOLD0 = 0.1;
function openingCam(t) {
  const S = heroScreen(), d0 = (SCR_W * 9 / 16 / 2) / Math.tan(THREE.MathUtils.degToRad(FOV0 / 2));
  const tA = 43.25, tB = 43.40, tC = TM.h[0].do - 0.08;
  if (t < tA) {   // the dive: three frames still on the screen (part 1's last frame dissolves into it), then accelerating in
    const u = clamp((t - T0 - HOLD0) / (tA - T0 - HOLD0)), d = d0 - (d0 + 0.09) * Math.pow(u, 2.6);
    return { p: S.c.clone().addScaledVector(S.n, d), l: S.c.clone().addScaledVector(S.n, d - 1), up: S.u, fov: FOV0, zoom: 0.05 * Math.pow(u, 3), near: 0.004 };
  }
  const pA = S.c.clone().addScaledVector(S.n, -0.09), dA = S.n.clone().negate();
  const pB = heroLocal(0.05, 1.6, 2.6), dB = V(0.0, -0.1, 1).normalize();
  const face = heroFace().add(V(0, -0.02, 0)), pC = heroLocal(0.16, 0.55, 0.36);
  if (t < tB) { const u = (t - tA) / (tB - tA), e = easeOut(u);   // out of the room, over the desk, into the open air
    const p = pA.clone().lerp(pB, e); const d = dA.clone().lerp(dB, easeIO(u)).normalize(); return { p, l: p.clone().add(d), up: V(0, 1, 0), fov: FOV0, near: 0.01 }; }
  // the whip: swing round to her (through her right), drifting back toward the room as it turns
  const u = clamp((t - tB) / (tC - tB)), e = easeIO(u);
  const p = pB.clone().lerp(pC, easeOut(u));
  const toFace = face.clone().sub(p).normalize(); const yaw0 = 0;
  let yawEnd = Math.atan2(toFace.x, toFace.z); if (yawEnd < 0) yawEnd += 2 * Math.PI;   // turn the long way through +x (her right, where the first new room appears)
  const yaw = lerp(yaw0, yawEnd, e), pitch = lerp(-0.05, Math.asin(clamp(toFace.y, -1, 1)), e);
  const d = V(Math.sin(yaw) * Math.cos(pitch), Math.sin(pitch), Math.cos(yaw) * Math.cos(pitch));
  return { p, l: p.clone().add(d), up: V(0, 1, 0), fov: lerp(FOV0, 34, e), near: 0.01 };
}
// 2) after that, an orbit rig: keys of {t, target, dist, yaw, pitch, fov}; distance eases in log space so big pulls feel even
let RIG = null;
function buildRig() {
  const G = (cx, cy) => V(BASE.x + cx * PX, BASE.y + cy * PY - 0.25, BASE.z - 1.0);
  const herL = R[0].letter;
  RIG = [
    { t: TM.h[0].do - 0.08, fn: (k = 1) => { const f = heroFace().add(V(0, -0.02, 0)), v = heroLocal(0.16, 0.55, 0.36).sub(f), d = v.length();   // exactly where the whip landed
      return { tg: f, d: d * k, yaw: Math.atan2(v.x, v.z), pitch: Math.asin(v.y / d) }; }, fov: 34 },
    { t: TM.h[0].do + 0.14, fn: () => RIG[0].fn(1.12), fov: 34, ease: easeOut },
    { t: TM.h[1].look, tg: G(0.5, 0.3), d: 9.5, yaw: 0.16, pitch: 0.02, fov: 38, ease: easeOut },
    { t: TM.h[1].do + 0.15, tg: G(0.5, 0.75), d: 13.5, yaw: 0.12, pitch: 0.03, fov: 38 },
    { t: TM.thing1 + 0.15, tg: G(-0.5, 0.75), d: 17.5, yaw: 0.06, pitch: 0.035, fov: 38 },
    { t: TM.thing2 + 0.2, tg: G(-0.5, 1.7), d: 23, yaw: 0.03, pitch: 0.04, fov: 38 },
    { t: TM.two + 0.2, tg: G(1.5, 1.7), d: 31, yaw: 0.0, pitch: 0.045, fov: 38 },
    { t: TM.h[2].look, tg: G(1.5, 2.2), d: 38, yaw: -0.02, pitch: 0.05, fov: 38 },
    { t: TM.h[2].what + 0.12, tg: G(-1.5, 3.6), d: 60, yaw: -0.02, pitch: 0.05, fov: 38 },
    { t: TM.h[2].do + 0.05, tg: V(BASE.x - 2.5 * PX, BASE.y + 7.7 * PY, BASE.z - 1), d: 92, yaw: 0.0, pitch: 0.06, fov: 40, ease: easeIO },
    // the rooms launch into the sky: the camera drops below them and looks up, so the letters sit on clear sky
    { t: TM.h[3].look + 0.1, tg: LET_C.clone().add(V(0, -8, 0)), d: 136, yaw: -0.01, pitch: -0.1, fov: 40, ease: easeIO },
    { t: TM.h[3].do + 0.25, tg: LET_C.clone().add(V(0, 1, 0)), d: 146, yaw: -0.02, pitch: -0.17, fov: 40, ease: easeOut },
    { t: TM.dont - 0.45, tg: LET_C.clone().add(V(0, 1, 0)), d: 142, yaw: -0.03, pitch: -0.17, fov: 40, ease: (x) => x },
    // "I don't know how I got here": into the letter I. Her room, the Claude robot above, the GT3 RS below, a pin
    { t: TM.dont + 0.45, tg: herL.clone().add(V(1.2, -0.05, -1.0)), d: 13.5, yaw: -0.05, pitch: 0.02, fov: 36, ease: easeIO },
    { t: TM.but, tg: herL.clone().add(V(1.15, -0.05, -1.0)), d: 12.6, yaw: -0.035, pitch: 0.02, fov: 36, ease: (x) => x },
    // "But I brought my laptop too!": in to her room as she picks it up
    { t: TM.brought + 0.15, tg: herL.clone().add(V(1.33, 0.08, -0.9)), d: 6.6, yaw: -0.02, pitch: 0.02, fov: 36, ease: easeIO },
    { t: END_PUSH, tg: herL.clone().add(V(1.3, 0.08, -0.9)), d: 6.35, yaw: -0.015, pitch: 0.02, fov: 36, ease: (x) => x },
  ];
}
function rigCam(t) {
  let i = 0; while (i < RIG.length - 2 && t > RIG[i + 1].t) i++;
  const a0 = RIG[i], b0 = RIG[i + 1]; const e = (b0.ease || easeIO)(clamp((t - a0.t) / (b0.t - a0.t)));
  const a = a0.fn ? { ...a0, ...a0.fn() } : a0, b = b0.fn ? { ...b0, ...b0.fn() } : b0;
  const tg = a.tg.clone().lerp(b.tg, e), d = Math.exp(lerp(Math.log(a.d), Math.log(b.d), e)), yaw = lerp(a.yaw, b.yaw, e), pitch = lerp(a.pitch, b.pitch, e);
  const p = tg.clone().add(V(Math.sin(yaw) * Math.cos(pitch), Math.sin(pitch), Math.cos(yaw) * Math.cos(pitch)).multiplyScalar(d));
  return { p, l: tg, up: V(0, 1, 0), fov: lerp(a.fov, b.fov, e), near: clamp(d * 0.01, 0.02, 0.6) };
}
// 3) the end: a push into the laptop she's holding up, settling on her and the screen (git push --force), sharp
const END_PUSH = 56.62;
function endCam(t, base) {
  const u = easeIO(clamp((t - END_PUSH) / (T1 - 1 / 30 - END_PUSH))); if (u <= 0) return base;
  HERO.root.updateMatrixWorld(true); const c = V(0, 0, 0).applyMatrix4(HERO.screen.matrixWorld), n = V(0, 0, 1).transformDirection(HERO.screen.matrixWorld);
  const face = heroFace(); const mid = c.clone().lerp(face, 0.56);
  const p1 = mid.clone().add(V(n.x, 0, n.z).normalize().multiplyScalar(1.95)), l1 = mid;
  return { p: base.p.clone().lerp(p1, u), l: base.l.clone().lerp(l1, u), up: V(0, 1, 0), fov: lerp(base.fov, 34, u), near: 0.02 };
}

// ---------------------------------------------------------------- the frame
function mouth(t) { let o = 0; for (const w of TM.words) o = Math.max(o, env(t, w - 0.03, 0.05, 0.16)); return o; }
const PERF = { n: 0 }; window.__perf = PERF;
const pt = (k, t0) => { PERF[k] = (PERF[k] || 0) + performance.now() - t0; };
window.renderTime = async (t) => {
  const _t0 = performance.now(); PERF.n++; renderer.info.reset();
  // rooms: spawn, slide, fly into the letters
  ROOMS3D.forEach((rm, i) => { const ps = poseOf(i, t); rm.root.visible = !!ps; if (!ps) return; rm.root.position.copy(ps.p); rm.root.scale.setScalar(ps.s); });
  // her: singing the hooks, smug; looks around on "I don't know how I got here"; picks up the laptop on "brought"
  const lift = sstep(TM.brought - 0.15, TM.laptop + 0.12, t);
  const lost = sstep(TM.dont - 0.1, TM.dont + 0.3, t) * (1 - sstep(TM.here + 0.1, TM.but, t));
  const look = lost * Math.sin((t - TM.dont) * 3.4) * 0.55;
  HERO.update({ t, talk: 1, talkCol: 0x5ee08f, lift, lookYaw: look, headPitch: -0.06 * lift, headRoll: 0.06 * (1 - lost) * (1 - lift),
    expr: { smile: lerp(lerp(0.55, -0.1, lost), 0.7, lift), open: mouth(t) * 0.8, brows: lost ? [0.5 + 0.4 * lost, 0.5] : [0.7, 0.15], lids: lerp(0.18, 0.05, lost), look: [-look * 0.8, 0] } });
  HERO.screen.material.map = lift > 0.5 ? GIT : TERM;
  // while the camera sits between her face and her screen, her hands on the keys would poke into the bottom of the frame
  { const show = t > 43.3; HERO.man.arms.forEach((a) => [a.up, a.fo, a.sh, a.el, a.wr, a.hand].forEach((m) => { m.visible = show; })); }
  // the camera (needs her pose) decides which rooms are close enough to be real 3D rooms; far ones are their photographs
  if (!RIG) buildRig();
  const camAt = (tt) => { let c = tt < TM.h[0].do - 0.08 ? openingCam(tt) : rigCam(tt); if (tt > END_PUSH) c = endCam(tt, c); return c; };
  const c = camAt(t), cp = camAt(t - 1 / 30);
  const use3D = R.map((r) => r.i < ROOMS3D.length && ROOMS3D[r.i].root.visible && ROOMS3D[r.i].root.position.distanceTo(c.p) < LOD_D);
  ROOMS3D.forEach((rm, i) => { if (!use3D[i]) rm.root.visible = false; });
  const vis = placeImpostors(t, use3D);
  // everyone else claps on the beat and beams at her
  ROOMS3D.slice(1).forEach((rm, k) => { if (!rm.root.visible) return; const i = k + 1;
    rm.update({ t: t + i * 0.37, clap: 1, clapK: 0.5 + 0.5 * Math.cos((t - 0.03) * Math.PI * 2 * (129.2 / 60) + i * 0.4), expr: { smile: 0.9, open: 0.35 + 0.25 * Math.sin(t * 5 + i), brows: 0.5 }, talk: 0 });
    vis.add(i); });
  // the billboard and the counter
  const hk = TM.h[1]; const nw = [hk.look, hk.what, hk.i, hk.can, hk.do].filter((x) => t >= x).length; BOARD.userData.set(HOOKTEX[nw]);
  COUNTER.userData.set(countAt(t));
  { let x0 = 1e9, x1 = -1e9; for (let i = 0; i < Math.min(N, countAt(t)); i++) { const ps = poseOf(i, t); if (ps) { x0 = Math.min(x0, ps.p.x); x1 = Math.max(x1, ps.p.x); } }
    const w = x1 - x0 + RW + 8, fly = sstep(TM.words4[0] - 0.5, TM.words4[2], t); SPILL.visible = fly < 1;
    SPILL.position.set((x0 + x1) / 2, ROOF_Y + 0.33, BASE.z + 1.5); SPILL.scale.set(w, Math.min(18, 8 + w * 0.25), 1); SPILL.material.opacity = 0.16 * (1 - fly); }
  // pills beside her room in the letter I
  const hp = poseOf(0, t).p; const side = V(RW / 2 + 0.42, 0, 0.25);
  const k1 = L.backOut(clamp((t - (TM.dont + 0.3)) / 0.4)) * (1 - easeIn(clamp((t - (TM.brought - 0.25)) / 0.2))), k2 = L.backOut(clamp((t - TM.brought) / 0.35));
  PILL_HERE.visible = k1 > 0.01; PILL_HERE.position.copy(hp).add(side).add(V(PILL_HERE.userData.w / 2, 0.55, 0)); PILL_HERE.scale.setScalar(Math.max(0.001, k1));
  PILL_LAPTOP.visible = k2 > 0.01; PILL_LAPTOP.position.copy(hp).add(side).add(V(PILL_LAPTOP.userData.w / 2, 0.15, 0)); PILL_LAPTOP.scale.setScalar(Math.max(0.001, k2));
  // camera (and its motion blur: where the frame centre was a frame ago, a short shutter)
  cam.position.copy(c.p); cam.up.copy(c.up); cam.lookAt(c.l); cam.fov = c.fov; cam.near = c.near || 0.05; cam.updateProjectionMatrix();
  { cam.updateMatrixWorld(true); const pc = new THREE.PerspectiveCamera(cp.fov, W / H, 0.01, 10); pc.position.copy(cp.p); pc.up.copy(cp.up); pc.lookAt(cp.l); pc.updateMatrixWorld(true);
    const fd = Math.max(8, c.l.distanceTo(c.p)), ahead = c.p.clone().add(c.l.clone().sub(c.p).normalize().multiplyScalar(fd)); const s = ahead.clone().project(pc);
    const v = new THREE.Vector2(-s.x * 0.5, -s.y * 0.5).multiplyScalar(0.4 * (W / H > 1 ? 1 : 1)); if (v.length() > 0.045) v.setLength(0.045); if (v.length() < 0.0025) v.set(0, 0);
    finish.uniforms.uVel.value.copy(v); }
  finish.uniforms.uZoom.value = c.zoom || 0; finish.uniforms.uTime.value = t; placeGlow(t, c.p);
  { const px = Math.max(finish.uniforms.uVel.value.length() * W, (c.zoom || 0) * 0.7 * W);   // blur length in pixels -> taps (~1 per 3 px), none when it's still
    finish.uniforms.uTaps.value = px < 3 ? 0 : Math.min(32, Math.max(6, Math.round(px / 3))); }
  // footage: only the clips of rooms that are actually in the shot get their frame loaded
  { cam.updateMatrixWorld(true); const fr = new THREE.Frustum().setFromProjectionMatrix(new THREE.Matrix4().multiplyMatrices(cam.projectionMatrix, cam.matrixWorldInverse));
    const sph = new THREE.Sphere(); for (const i of vis) { const r = R[i]; if (!r.video) continue; const ps = poseOf(i, t); sph.set(ps.p.clone().add(V(0, 0, -0.8)), 2.2 * ps.s); if (fr.intersectsSphere(sph)) MED.use(r.video); } }
  const _t1 = performance.now(); pt('scene', _t0);
  over.uniforms.uMix.value = 1 - sstep(T0, T0 + HOLD0 - 0.01, t); over.enabled = over.uniforms.uMix.value > 0;
  // the hooks lift the city a little (Great Idea, Ted's chorus gold, kept subtle)
  finish.uniforms.uGold.value = 0.12 + 0.05 * L.beatPulse(t, 6);
  const _t2 = performance.now(); await MED.update(t); pt('media', _t2);
  const _t3 = performance.now(); composer.render(); renderer.getContext().finish(); pt('render', _t3); PERF.tris = renderer.info.render.triangles; PERF.calls = renderer.info.render.calls;
  const _t4 = performance.now(); const url = renderer.domElement.toDataURL('image/jpeg', 0.93); pt('encode', _t4);
  return url;
};

// ---------------------------------------------------------------- QA (ported from Great Idea, Ted): does any body part pass
// through a solid? Arms, hands, legs and torso as spheres against each solid's box; returns the problems per visible 3D room
// (millimetres of room; a room is 3 m wide). While she holds her laptop, hands on it are contact, not a clip.
const _l = new THREE.Vector3(), _inv = new THREE.Matrix4();
function penetration(center, r, mesh) {
  mesh.geometry.computeBoundingBox(); const bb = mesh.geometry.boundingBox;
  _inv.copy(mesh.matrixWorld).invert(); _l.copy(center).applyMatrix4(_inv);
  const sc = new THREE.Vector3().setFromMatrixScale(mesh.matrixWorld); const rl = r / Math.min(sc.x, sc.y, sc.z);
  const cx = Math.max(bb.min.x, Math.min(_l.x, bb.max.x)), cy = Math.max(bb.min.y, Math.min(_l.y, bb.max.y)), cz = Math.max(bb.min.z, Math.min(_l.z, bb.max.z));
  const inside = cx === _l.x && cy === _l.y && cz === _l.z;
  const d = inside ? -Math.min(_l.x - bb.min.x, bb.max.x - _l.x, _l.y - bb.min.y, bb.max.y - _l.y, _l.z - bb.min.z, bb.max.z - _l.z) : Math.hypot(_l.x - cx, _l.y - cy, _l.z - cz);
  return (rl - d) * Math.min(sc.x, sc.y, sc.z);
}
function bodySpheres(man) {
  const S = man.root.getWorldScale(new THREE.Vector3()).x, out = [];
  const w = (o, v) => o.localToWorld(v.clone());
  const seg = (name, a, b, r, n = 8) => { for (let i = 0; i <= n; i++) out.push([name, w(man.body, a.clone().lerp(b, i / n)), r * S]); };
  man.arms.forEach((a) => { const side = a.s < 0 ? 'left' : 'right';
    seg(side + ' upper arm', a.S, a.E, 0.068); seg(side + ' forearm', a.E, a.wr.position, 0.06);
    const hc = a.hand.getWorldPosition(new THREE.Vector3()); const ax = new THREE.Vector3(0, 1, 0).applyQuaternion(a.hand.getWorldQuaternion(new THREE.Quaternion()));
    for (const k of [-0.045, 0, 0.045]) out.push([side + ' hand', hc.clone().addScaledVector(ax, k * S), 0.038 * S]); });
  man.legs.forEach((l) => { const side = l.s < 0 ? 'left' : 'right'; seg(side + ' thigh', l.hp.position, l.kn.position, 0.085); seg(side + ' shin', l.kn.position, l.ankle, 0.068); });
  seg('torso', new THREE.Vector3(0, 0.08, 0), new THREE.Vector3(0, 0.46, 0), 0.19 * 0.72, 6);
  return out;
}
window.qaNow = () => {
  scene.updateMatrixWorld(true); const rep = [];
  ROOMS3D.forEach((r) => { if (!r.man || !r.root.visible) return; const hits = {}; const holding = r === HERO && HERO.lifting;
    for (const [part, c, rad] of bodySpheres(r.man)) for (const [name, mesh] of r.solids) {
      if (name === 'chair' && (part === 'torso' || part.includes('thigh'))) continue;
      if (holding && name.startsWith('laptop') && (part.includes('hand') || part.includes('forearm'))) continue;
      const pen = penetration(c, rad, mesh); const k = part + ' into ' + name; if (pen > 0.002 && pen > (hits[k] || 0)) hits[k] = pen; }
    const list = Object.entries(hits).sort((x, y) => y[1] - x[1]).map(([k, v]) => `${Math.round(v * 1000 / r.root.scale.x)} mm ${k}`);
    { const PROPS = ['laptop', 'laptop lid', 'mug', 'desk'], ps = r.solids.filter((x) => PROPS.includes(x[0]));
      const bx = ps.map(([n, m]) => [n, new THREE.Box3().setFromObject(m).expandByScalar(-0.006)]);
      for (let a = 0; a < bx.length; a++) for (let b = a + 1; b < bx.length; b++) { if (bx[a][0].startsWith('laptop') && bx[b][0].startsWith('laptop')) continue;
        if (bx[a][1].intersectsBox(bx[b][1])) list.push(`${bx[a][0]} overlaps ${bx[b][0]}`); } }
    if (list.length) rep.push({ who: r.c.name + ' #' + r.R.i, part: list.join('; ') }); });
  return rep;
};
window.__dbg = { R, poseOf, TM, cam, scene };
build().catch((e) => { console.log('BUILD ERROR', e.stack || e.message); window.ready = true; });
