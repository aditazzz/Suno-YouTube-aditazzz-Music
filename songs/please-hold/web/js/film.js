// Please Hold: the film. renderAt(t) draws the frame at time t (deterministic). One world (the plaza, the HOLD tower,
// the city), a studio backdrop for hero shots of props, her, the hold-robot, and a shot list cut to the vocal.
import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { Pass } from 'three/addons/postprocessing/Pass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { ShaderPass } from 'three/addons/postprocessing/ShaderPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { loadFonts, clamp, lerp, sstep, easeIO, easeOut, easeIn, easeOutBack, pop, hit, decay, squash, track, win, rng, V3, mixV, RIM, RIM_AMT, FONT, canvasTex, liveTex, glowSprite, dotTex, textPlane, blobShadow, clay, gloss, glowMat, rbox } from './lib.js';
import { ENV, buildWorld, BENCH, SEAT_Y, TOWER, winCenter, newsstand, payphone, PLAZA } from './world.js';
import { Woman } from './figure.js';
import { Robot, makeHandset, Cord } from './robot.js';
import { salon, onionBag, onionRing, flute, Phone, PHONE, makeThumb, phoneHand, Bill, Keypad, bigKey, cubicle, takeoutBox, eggRoll, drinkSet, notebook, drawNotebook, Receipt, RECEIPT_PX, rubberStamp, stoneTablet, telegraphKey, rotaryPhone, pedestal, cobweb, pigeon, SaxNotes, tabloid, ORANGE } from './props.js';
import { Captions } from './captions.js';
import { bitmap } from './font5.js';

const q = new URLSearchParams(location.search);
const W = +q.get('w') || 1600, H = +q.get('h') || 900; const VERT = H > W; const CLEAN = q.get('clean') === '1';
const FOV = VERT ? 60 : 36;
const T = {}; let LN = [], BEATS = [], DOWN = [];

// ---------------------------------------------------------------- renderer and post
const renderer = new THREE.WebGLRenderer({ antialias: false, preserveDrawingBuffer: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(1); renderer.setSize(W, H);
renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.0;
document.body.appendChild(renderer.domElement);
const scene = new THREE.Scene();
const overlay = new THREE.Scene(); const ovCam = new THREE.PerspectiveCamera(FOV, W / H, 0.1, 100); overlay.add(ovCam);
const camA = new THREE.PerspectiveCamera(FOV, W / H, 0.02, 4000), camB = new THREE.PerspectiveCamera(FOV, W / H, 0.02, 4000);
const hemi = new THREE.HemisphereLight(0x2a3a66, 0x0b0c10, 0.9); scene.add(hemi);
const key = new THREE.DirectionalLight(0xfff1e0, 1.5); key.position.set(-8, 14, 22); scene.add(key); scene.add(key.target);

// one pass renders the world through one camera, or two (split screen), then the lyric overlay
class FilmPass extends Pass {
  constructor() { super(); this.needsSwap = false; this.views = []; }
  render(r, writeBuffer, readBuffer) {
    const rt = readBuffer; const w = rt.width, h = rt.height;
    rt.scissorTest = false; rt.viewport.set(0, 0, w, h); r.setRenderTarget(rt); r.setClearColor(0x000000, 1); r.clear(true, true, true);
    for (const v of this.views) {
      const x = Math.round(v.rect[0] * w), y = Math.round(v.rect[1] * h), vw = Math.round(v.rect[2] * w), vh = Math.round(v.rect[3] * h);
      if (v.before) v.before();
      v.cam.aspect = vw / vh; v.cam.updateProjectionMatrix();
      rt.viewport.set(x, y, vw, vh); rt.scissor.set(x, y, vw, vh); rt.scissorTest = true; r.setRenderTarget(rt);
      r.clear(true, true, true); r.render(scene, v.cam);
    }
    rt.scissorTest = false; rt.viewport.set(0, 0, w, h); r.setRenderTarget(rt);
    r.autoClear = false; r.clearDepth(); r.render(overlay, ovCam); r.autoClear = true;
  }
}
const composer = new EffectComposer(renderer);
const fp = new FilmPass(); composer.addPass(fp);
const bloom = new UnrealBloomPass(new THREE.Vector2(W / 2, H / 2), 0.55, 0.5, 0.82); composer.addPass(bloom);
const hudCanvas = document.createElement('canvas'); hudCanvas.width = W; hudCanvas.height = H; const hud = hudCanvas.getContext('2d');
const hudTex = new THREE.CanvasTexture(hudCanvas); hudTex.colorSpace = THREE.SRGBColorSpace;
const finish = new ShaderPass({
  uniforms: { tDiffuse: { value: null }, tHud: { value: hudTex }, uHud: { value: 0 }, uTime: { value: 0 }, uVig: { value: 0.3 }, uGrain: { value: 0.025 }, uCA: { value: 0.001 },
    uFlash: { value: 0 }, uFade: { value: 1 }, uFlashCol: { value: new THREE.Color(1, 1, 1) }, uSplit: { value: 0 }, uSplitAt: { value: 0.5 }, uLift: { value: 0 }, uScrim: { value: 0 } },
  vertexShader: `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
  fragmentShader: `uniform sampler2D tDiffuse, tHud; uniform float uHud, uTime, uVig, uGrain, uCA, uFlash, uFade, uSplit, uSplitAt, uLift, uScrim; uniform vec3 uFlashCol; varying vec2 vUv;
    float h(vec2 p){ return fract(sin(dot(p, vec2(12.9898,78.233)) + uTime * 17.0) * 43758.5453); }
    void main(){ vec2 d = vUv - 0.5; vec3 c;
      c.r = texture2D(tDiffuse, vUv + d * uCA).r; c.g = texture2D(tDiffuse, vUv).g; c.b = texture2D(tDiffuse, vUv - d * uCA).b;
      c *= 1.0 - uVig * pow(length(d * vec2(1.0, 0.9)) * 1.45, 2.4);
      c += uLift; c *= 1.0 - uScrim * ${VERT ? '(uSplit > 0.5 ? smoothstep(0.16, 0.0, abs(vUv.y - 0.5)) : smoothstep(0.5, 0.12, vUv.y) * smoothstep(0.0, 0.12, vUv.y))' : 'smoothstep(0.42, 0.0, vUv.y)'};
      c += (h(vUv * 1000.0) - 0.5) * uGrain; c = mix(c, uFlashCol, uFlash);
      if (uSplit > 0.5) { float e = uSplit < 1.5 ? abs(vUv.x - uSplitAt) * ${W.toFixed(1)} : abs(vUv.y - uSplitAt) * ${H.toFixed(1)}; c = mix(vec3(0.97, 0.96, 0.93), c, smoothstep(2.0, 3.5, e)); }
      if (uHud > 0.5) { vec4 o = texture2D(tHud, vUv); c = c * (1.0 - o.a) + o.rgb; }
      gl_FragColor = vec4(max(c, 0.0) * uFade, 1.0); }` });
composer.addPass(finish); composer.addPass(new OutputPass());
finish.uniforms.tHud.value = hudTex;   // ShaderPass clones uniform textures: use the live one

// ---------------------------------------------------------------- the world, the cast, the props
let salonG, bag, ring1, glassF, crowd = [], pigs = [], busts, ringsM, signs = [], two, botHand, WEB0, Wd, her, bot, phone, thumb, pHand, bill, keypad, cub, box, roll, drink, nb, receipt, stamp, saxN, trail, trailHead, sparks, puff, giant0, stand, labelPills = {}, lyrics = [], newsS, payP, hist = {}, webs = [], pig, kioskBox;
const STUDIO = V3(600, 0, 0);
function build() {
  Wd = buildWorld(scene);
  her = new Woman(); scene.add(her.root);
  bot = new Robot(); scene.add(bot.root);
  phone = new Phone(); scene.add(phone.root);
  thumb = makeThumb(her.mats.skin, her.mats.coat); phone.root.add(thumb);
  pHand = phoneHand(her.mats.skin, her.mats.coat); phone.root.add(pHand);
  bill = new Bill(); scene.add(bill.root);
  keypad = new Keypad({ size: 0.1, gap: 0.022 }); scene.add(keypad.root);
  for (const [k, txt, col] of [['1', 'BILLING', '#ffffff'], ['2', 'DESPAIR', '#ffffff'], ['3', '…', '#ffffff']]) {
    const p = textPlane(txt, { h: 0.075, font: FONT.black, size: 140, fg: '#0d1a22', bg: '#ffffff', pad: 0.32, radius: 0.5 }); p.visible = false; scene.add(p); labelPills[k] = p; }
  cub = cubicle(); cub.position.copy(STUDIO).add(V3(0, 0, -4)); scene.add(cub);
  box = takeoutBox(); scene.add(box); roll = eggRoll(); scene.add(roll); drink = drinkSet(); scene.add(drink); nb = notebook(); scene.add(nb);
  receipt = new Receipt(); scene.add(receipt.mesh); stamp = rubberStamp(); scene.add(stamp);
  saxN = new SaxNotes(16); scene.add(saxN.root);
  giant0 = bigKey('0', '+'); scene.add(giant0);
  // the call as a light: a glowing ribbon with a bright head
  trail = new THREE.Mesh(new THREE.BufferGeometry(), new THREE.MeshBasicMaterial({ color: new THREE.Color(0.35, 2.2, 2.6), transparent: true, opacity: 0.9, blending: THREE.AdditiveBlending, depthWrite: false, toneMapped: false }));
  trail.frustumCulled = false; scene.add(trail);
  trailHead = glowSprite(new THREE.Color(0.6, 2.4, 2.8), 0.6); scene.add(trailHead);
  { const n = 260, p = new Float32Array(n * 3); const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(p, 3));
    sparks = new THREE.Points(g, new THREE.PointsMaterial({ color: new THREE.Color(0.5, 2.0, 2.3), size: 0.06, map: dotTex(), transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false })); sparks.frustumCulled = false; scene.add(sparks); }
  { const n = 160, p = new Float32Array(n * 3); const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(p, 3));
    puff = new THREE.Points(g, new THREE.PointsMaterial({ color: 0xffffff, size: 0.22, map: dotTex(), transparent: true, opacity: 0.7, depthWrite: false })); puff.frustumCulled = false; scene.add(puff); }
  // newsstand with invented tabloids
  const covers = [tabloid('THE DAILY HOLD', ['ROBOT ON HOLD', '47 MIN'], '#d6282c', 1), tabloid('WAIT WEEKLY', ['HOLD-MUSIC SAX', 'PLAYER SPEAKS'], '#1f6fd1', 2),
    tabloid('QUEUE', ['THE $4 CHARGE:', 'THE TRUTH'], '#e8851a', 3), tabloid('ON HOLD TODAY', ['PRESS 1', 'FOR LOVE?'], '#7a3fd1', 4),
    tabloid('THE DAILY HOLD', ['MAN WAITS,', 'IS FINE'], '#d6282c', 5), tabloid('WAIT WEEKLY', ['"YOUR CALL IS', 'IMPORTANT"'], '#1f6fd1', 6),
    tabloid('QUEUE', ['ELEVATOR MUSIC:', 'A LOVE STORY'], '#e8851a', 7), tabloid('ON HOLD TODAY', ['TRANSFERRED', 'AGAIN'], '#7a3fd1', 8)];
  newsS = newsstand(covers); newsS.position.set(-17.5, 0, 4); newsS.rotation.y = Math.PI / 2; scene.add(newsS);
  payP = payphone(); payP.position.set(0, 0, 6); scene.add(payP);
  hist.tablet = stoneTablet(); hist.key = telegraphKey(); hist.rotary = rotaryPhone(); for (const k in hist) scene.add(hist[k]);
  hist.ped = pedestal(''); scene.add(hist.ped);
  { const tx = liveTex(400, 106); plaque = new THREE.Mesh(new THREE.PlaneGeometry(0.34, 0.09), new THREE.MeshLambertMaterial({ map: tx })); scene.add(plaque); }
  pig = pigeon(); scene.add(pig);
  kioskBox = takeoutBox(); scene.add(kioskBox);
  salonG = salon(); scene.add(salonG); bag = onionBag(); scene.add(bag); ring1 = onionRing(); scene.add(ring1); glassF = flute(); scene.add(glassF);
  for (let i = 0; i < 10; i++) { const r = new Robot({ eyeRes: [256, 48] }); r.cord.mesh.visible = false; scene.add(r.root); crowd.push(r); }
  for (let i = 0; i < 8; i++) { const pg = pigeon(); pg.scale.setScalar(1.6); scene.add(pg); pigs.push(pg); }
  busts = new THREE.Group(); { const en = gloss(0xeef1f4, { shininess: 85, rimAmt: 0.35 }), gl = gloss(0x07080b, { shininess: 140 }), ey = glowMat(new THREE.Color(0.4, 1.7, 2.0));
    for (let i = 0; i < 26; i++) { const b = new THREE.Group(); const h = new THREE.Mesh(new THREE.SphereGeometry(0.2, 16, 12), en); h.scale.y = 1.15; h.position.y = 0.55; b.add(h);
      const f = new THREE.Mesh(new THREE.SphereGeometry(0.205, 16, 12, -1.1, 2.2, 0.7, 1.6), gl); f.scale.y = 1.15; f.position.y = 0.55; b.add(f);
      const e = new THREE.Mesh(new THREE.BoxGeometry(0.2, 0.035, 0.02), ey); e.position.set(0, 0.58, 0.2); b.add(e);
      const body = new THREE.Mesh(new THREE.CapsuleGeometry(0.2, 0.3, 6, 14), en); body.position.y = 0.05; b.add(body); busts.add(b); } }
  scene.add(busts);
  ringsM = new THREE.Group(); for (let i = 0; i < 3; i++) { const m = new THREE.Mesh(new THREE.TorusGeometry(0.5, 0.02, 6, 40), new THREE.MeshBasicMaterial({ color: new THREE.Color(1.6, 1.4, 0.6), transparent: true, depthWrite: false, toneMapped: false })); ringsM.add(m); } scene.add(ringsM);
  for (const txt of ['BILLING', 'SUPPORT', 'BILLING', 'BILLING']) { const sg = textPlane(txt, { h: 0.5, font: FONT.black, size: 120, fg: '#0d1a22', bg: '#ffd84d', pad: 0.3, radius: 0.25 }); scene.add(sg); signs.push(sg); }
  two = textPlane('2', { h: 0.24, font: FONT.marker, size: 220, fg: '#ffffff' }); scene.add(two);
  botHand = new THREE.Group(); { const R = bot.R; const fo = new THREE.Mesh(new THREE.CapsuleGeometry(0.045, 0.3, 6, 14), R.enamel); fo.rotation.x = Math.PI / 2; fo.position.set(0, -0.02, 0.2); botHand.add(fo);
    const hand = bot.makeHand(1, R.joint); hand.rotation.x = -Math.PI / 2; hand.position.set(0, -0.02, 0.02); botHand.add(hand); } scene.add(botHand);
  // cobwebs: one between the robot's arm and the bench, more for the outro
  const W0 = { c: V3(0.73, 0.66, -0.05), a: [V3(0.6, 0.52, 0.14), V3(0.85, 0.67, -0.25), V3(0.82, 0.96, -0.36), V3(0.62, 0.9, 0.02), V3(0.86, 0.48, 0.12)] }; WEB0 = W0;
  webs.push(cobweb(W0.c, W0.a, { rings: 8 }));
  webs.push(cobweb(V3(0.36, 1.1, -0.2), [V3(0.25, 1.2, -0.05), V3(0.1, 0.95, -0.38), V3(0.4, 0.92, -0.4), V3(0.55, 1.15, -0.1)], { rings: 7 }));
  webs.push(cobweb(V3(0.15, 0.52, 0.2), [V3(0.3, 0.48, 0.3), V3(-0.05, 0.47, 0.15), V3(0.1, 0.25, 0.1), V3(0.3, 0.3, 0.25)], { rings: 6 }));
  for (const w of webs) { w.position.set(0, 0, 0); scene.add(w); }
  // the HUD sits in the finish pass (crisp, no bloom)
}

// ---------------------------------------------------------------- timing
const ls = (i) => LN[i].s, le = (i) => LN[i].e, wt = (i, j) => LN[i].wt[j];
function wordT(i, w) { const k = LN[i].words.findIndex((x) => x.toLowerCase().replace(/[^a-z0-9$-]/g, '').startsWith(w)); return k < 0 ? LN[i].s : LN[i].wt[k]; }
function beatPulse(t) { let v = 0; for (let i = 0; i < BEATS.length; i++) { const b = BEATS[i]; if (b > t) break; if (t - b < 0.4) v = Math.max(v, Math.exp(-(t - b) / 0.11)); } return v; }
function downPulse(t) { let v = 0; for (const b of DOWN) { if (b > t) break; if (t - b < 0.6) v = Math.max(v, Math.exp(-(t - b) / 0.16)); } return v; }
const LYRIC_OFF = new Set([15, 31, 32, 33, 34, 40]);     // shown in the world instead: the tower screen (15, 40), the receipt (31-34)
const VOICE = { auto: [0, 1, 44, 45], bot: [35, 46] }; let caps = null;
function initTiming(timed, beats) {
  LN = timed; BEATS = beats.beats; DOWN = beats.downbeats;
  T.song = 206.28; T.end = T.song; T.card = T.song + 0.7; T.dur = 213.0;
  T.beep = 12.40; T.hand = 12.40;
  T.bill = ls(3); T.circle = wordT(3, 'internet'); T.press1 = wordT(5, 'one'); T.press2 = wordT(5, 'two'); T.press3 = wordT(6, 'three'); T.nobody = wordT(6, 'nobody');
  T.glass = wordT(7, 'glass'); T.pass = wordT(8, 'pass'); T.land = wordT(9, 'said'); T.stand = 49.55; T.chinese = wordT(10, 'chinese');
  T.notes = wordT(11, 'take'); T.sax = wordT(12, 'saxophone'); T.pre = 62.46; T.machines2 = ls(14); T.ch1 = 70.43;
  T.zero = wordT(19, 'zero'); T.egg = wordT(20, 'second'); T.anymore = ls(22); T.reveal = wordT(22, 'wait');
  T.v2 = 102.10; T.bridge = 135.84; T.five = wordT(35, 'five-dollar'); T.charge5 = wordT(35, 'charge'); T.drop = 149.95;
  T.final = 149.95; T.years = ls(38); T.comcast = wordT(39, 'comcast'); T.screen = ls(40); T.robots = ls(41); T.queue = ls(42); T.better = ls(43); T.outro = 181.35;
  caps = new Captions({ g: hud, W, H, VERT, lines: LN, off: LYRIC_OFF, voice: VOICE, special: {
    5: { droop: 7 },                                                         // press two for despair: "despair" wilts
    12: { spin: 8 },                                                         // when the saxophone loops: "loops" loops
    22: { upper: true, slam: true, nobox: true, font: FONT.black, size: 1.75, y: VERT ? 0.2 : 0.16, exit: 'walk', exitT: 100.45, accent: { k: 3, color: '#ff8a3a' }, maxW: VERT ? 1.0 : 1.3 },   // the words walk off with her   // I DON'T WAIT ANYMORE: no slumping, it walks off
    39: { redact: ['comcast'] },                                             // only sung, never shown
    30: { exitT: 134.75 },                                                   // gone before the bridge (and the Instagram cut's join)
    43: { exit: 'walk' },                                                    // I've got better things to do: it leaves on its own
  } });
}

// ---------------------------------------------------------------- moods (time of day)
const C = (h) => new THREE.Color(h);
const MOOD = {
  night: { day: 0, warm: 0, neon: 0, stars: 1, sky: C(0x3d5596), ground: C(0x10121a), hi: 1.15, key: C(0xb4c4ff), ki: 0.7, kdir: V3(-0.5, 0.8, 0.6), lamp: 1, fog: C(0x0b1022), fogD: 0.0055, lit: 0.55, rim: C(0x9fd8ff), ra: 0.55, exp: 1.05 },
  dusk: { day: 0.42, warm: 1, neon: 0, stars: 0.25, sky: C(0xffb48a), ground: C(0x3a2a2a), hi: 1.05, key: C(0xffa868), ki: 1.5, kdir: V3(-0.8, 0.25, 0.55), lamp: 0.5, fog: C(0x8a6070), fogD: 0.004, lit: 0.3, rim: C(0xffc8a0), ra: 0.5, exp: 1.0 },
  day: { day: 1, warm: 0, neon: 0, stars: 0, sky: C(0xd6e9ff), ground: C(0x8a8274), hi: 1.25, key: C(0xfff0dc), ki: 2.1, kdir: V3(-0.45, 0.7, 0.55), lamp: 0, fog: C(0xc4dbf0), fogD: 0.0028, lit: 0.04, rim: C(0xffffff), ra: 0.28, exp: 0.95 },
  neon: { day: 0, warm: 0, neon: 1, stars: 0.4, sky: C(0x7a3aa8), ground: C(0x0a0a14), hi: 1.1, key: C(0x7ff0ff), ki: 0.8, kdir: V3(0.5, 0.7, 0.6), lamp: 0.6, fog: C(0x16072c), fogD: 0.006, lit: 0.6, rim: C(0x7ff6ff), ra: 0.75, exp: 1.05 },
  studio: { day: 1, warm: 0, neon: 0, stars: 0, sky: C(0xffffff), ground: C(0x8a8f99), hi: 1.15, key: C(0xfff4e6), ki: 1.9, kdir: V3(-0.5, 0.9, 0.5), lamp: 0, fog: C(0xffffff), fogD: 0.0, lit: 0, rim: C(0xffffff), ra: 0.35, exp: 0.95 },
};
function mixMood(a, b, k) { const o = {}; for (const n in a) { const x = a[n], y = b[n]; o[n] = typeof x === 'number' ? lerp(x, y, k) : (x.isColor ? x.clone().lerp(y, k) : x.clone().lerp(y, k)); } return o; }
/** the plaza's sky over the song */
function moodAt(t) {
  const K = (a, b, ta, tb) => mixMood(MOOD[a], MOOD[b], easeIO((t - ta) / (tb - ta)));
  if (t < 27.2) return MOOD.night;
  if (t < 30.64) { const u = (t - 27.2) / 3.44; return u < 0.5 ? K('night', 'dusk', 27.2, 28.9) : K('dusk', 'day', 28.9, 30.64); }
  if (t < 62.5) return MOOD.day;
  if (t < 70.4) return t < 66.5 ? K('day', 'dusk', 62.5, 66.5) : K('dusk', 'night', 66.5, 69.5);
  if (t < 73.68) return MOOD.night;
  if (t < 77.76) return MOOD.day;
  if (t < 81.84) return MOOD.night;
  if (t < 92.5) return MOOD.day;
  if (t < 97.0) return MOOD.dusk;
  if (t < 134.4) return MOOD.day;
  if (t < 149.95) return MOOD.night;
  if (t < 181.35) return MOOD.neon;
  if (t < 191) return K('night', 'dusk', 181.35, 191);
  return K('dusk', 'day', 191, 206.3);
}
function applyMood(m, t) {
  SCENE_BRIGHT = Math.max(m.day, m === MOOD.studio ? 1 : 0) * (1 - m.neon);
  ENV.day.value = m.day; ENV.warm.value = m.warm; ENV.neon.value = m.neon; ENV.stars.value = m.stars; ENV.fog.value.copy(m.fog); ENV.fogD.value = m.fogD; ENV.lit.value = m.lit;
  hemi.color.copy(m.sky); hemi.groundColor.copy(m.ground); hemi.intensity = m.hi; key.color.copy(m.key); key.intensity = m.ki;
  key.position.copy(m.kdir).normalize().multiplyScalar(30); key.target.position.set(0, 0, 0);
  RIM.value.copy(m.rim); RIM_AMT.value = m.ra; renderer.toneMappingExposure = m.exp;
  Wd.lampLight.intensity = 4.0 * m.lamp; Wd.lamp.userData.bulbMat.color.setRGB(1.0 * (0.25 + 0.75 * m.lamp), 0.82 * (0.25 + 0.75 * m.lamp), 0.55 * (0.25 + 0.75 * m.lamp)); Wd.lamp.userData.halo.material.opacity = 0.6 * m.lamp;
  Wd.floor.material.uniforms.uLamp.value = m.lamp; for (const b of Wd.streetBulbs) b.material.opacity = 0.9 * m.lamp;
  for (const l of Wd.kiosk.userData.lanterns) l.material.color.setRGB(0.55 + 1.1 * m.lamp, 0.12 + 0.25 * m.lamp, 0.1 + 0.1 * m.lamp);
  ENV.sunDir.value.copy(m.kdir).normalize();
}

// ---------------------------------------------------------------- her and the robot: poses
const HER0 = { x: -0.42, z: -0.06 }, BOT0 = { x: 0.45, z: -0.06 };
function herBowed(t, o = {}) {        // the original pose: head bowed over the phone in her lap
  const br = Math.sin(t * 1.3) * 0.006;
  return { x: HER0.x, z: HER0.z, seat: 1, lean: 0.27 + br, headPitch: 0.6, headYaw: 0.03, headRoll: 0.03, hands: [[-0.075, 0.13, 0.33], [0.07, 0.11, 0.32]], kneeOut: 0.0, ...o };
}
function botHold(t, o = {}) {         // her exact old pose, with the receiver to its head
  const bob = Math.sin(t * Math.PI * 2 * 1.0) * 0.015;
  return { x: BOT0.x, z: BOT0.z, seat: 1, lean: 0.2, headPitch: 0.42 + bob, headRoll: -0.1, hands: [[-0.15, 0.64, 0.07], [0.09, 0.1, 0.3]], swing: t * 2.5, ...o };
}
/** her seated with the phone where her eyes are looking (d metres along the gaze): poses her twice (hands onto the phone) */
function herWithPhone(t, base, o = {}) {
  her.pose(base); her.root.updateMatrixWorld(true);
  const e = eyeOf(her); const gq = her.headG.getWorldQuaternion(new THREE.Quaternion()); const gaze = V3(0, 0, 1).applyQuaternion(gq);
  const c = e.clone().addScaledVector(gaze, o.d ?? 0.3).add(o.off || V3());
  const n = e.clone().sub(c).normalize(); const fwd = V3(0, 0, 1).applyQuaternion(her.torso.getWorldQuaternion(new THREE.Quaternion()));
  const up = fwd.clone().sub(n.clone().multiplyScalar(fwd.dot(n))).normalize(); const x = new THREE.Vector3().crossVectors(up, n);
  const m = new THREE.Matrix4().makeBasis(x, up, n); phone.root.quaternion.setFromRotationMatrix(m); phone.root.position.copy(c); phone.root.updateMatrixWorld(true);
  const inv = new THREE.Matrix4().copy(her.torso.matrixWorld).invert();
  const L = phone.root.localToWorld(V3(-0.03, -0.035, -0.03)).applyMatrix4(inv), R = phone.root.localToWorld(V3(0.045, -0.075, -0.02)).applyMatrix4(inv);
  her.pose({ ...base, hands: [[L.x, L.y, L.z], [R.x, R.y, R.z]], handRot: [[0, 0, 0], [0, 0, 0]] });
  phone.root.visible = true; return { c, n, e, gaze };
}
function placePhone(fig, ph, o = {}) {
  const hl = fig.handWorld(0), hr = fig.handWorld(1);
  const c = hl.clone().lerp(hr, 0.5).add(V3(0, 0.03, 0)); if (o.off) c.add(o.off);
  const eye = fig.headWorld().add(V3(0, 0.12, 0));
  const n = eye.clone().sub(c).normalize(); if (o.tiltN) n.add(o.tiltN).normalize();
  const fwd = V3(0, 0, 1).applyQuaternion(fig.torso.getWorldQuaternion(new THREE.Quaternion()));
  const up = fwd.clone().sub(n.clone().multiplyScalar(fwd.dot(n))).normalize(); const x = new THREE.Vector3().crossVectors(up, n);
  const m = new THREE.Matrix4().makeBasis(x, up, n); ph.root.quaternion.setFromRotationMatrix(m); ph.root.position.copy(c);
  return { c, n, eye };
}
function eyeOf(fig) { fig.root.updateMatrixWorld(true); return V3(0, 0.13, 0.05).applyMatrix4(fig.headG.matrixWorld); }

// ---------------------------------------------------------------- the cyan light (the call)
const TRAIL_UP = [V3(-0.42, 0.8, 0.28), V3(-0.3, 2.2, -0.5), V3(1.5, 7, -6), V3(6, 18, -18), V3(4, 40, -30), V3(-6, 70, -40), V3(-20, 110, -60)];
const trailUp = new THREE.CatmullRomCurve3(TRAIL_UP);
const trailDown = new THREE.CatmullRomCurve3([V3(16, 48, -30), V3(10, 26, -15), V3(5.5, 11, -5), V3(2.2, 3.8, -1), V3(0.8, 1.5, 0.1), V3(0.45, 0.62, -0.02)]);
function setTrail(curve, u1, len = 0.18, op = 1, width = 0.06) {
  const u0 = Math.max(0, u1 - len); if (u1 <= 0.001 || op <= 0.001) { trail.visible = trailHead.visible = sparks.visible = false; return; }
  const pts = []; for (let i = 0; i <= 60; i++) pts.push(curve.getPointAt(lerp(u0, u1, i / 60)));
  const c = new THREE.CatmullRomCurve3(pts); trail.geometry.dispose(); trail.geometry = new THREE.TubeGeometry(c, 80, width, 6, false);
  // taper: fade the tail by vertex colours is costly; use opacity instead
  trail.visible = true; trail.material.opacity = 0.85 * op; trailHead.visible = true; trailHead.position.copy(curve.getPointAt(u1)); trailHead.material.opacity = op; trailHead.scale.setScalar(width * 14);
  const pa = sparks.geometry.attributes.position; const R = rng(4); sparks.visible = true;
  for (let i = 0; i < pa.count; i++) { const uu = clamp(u1 - R() * len * 1.4); const p = curve.getPointAt(uu); pa.setXYZ(i, p.x + (R() - 0.5) * width * 8, p.y + (R() - 0.5) * width * 8, p.z + (R() - 0.5) * width * 8); }
  pa.needsUpdate = true; sparks.material.opacity = op; sparks.material.size = width * 1.4;
}

// ---------------------------------------------------------------- per-frame defaults
const ALL = () => [plaque, salonG, bag, ring1, glassF, busts, ringsM, two, botHand, ...signs, ...pigs, ...crowd.map((r) => r.root), her.root, bot.root, phone.root, bill.root, keypad.root, cub, box, roll, drink, nb, receipt.mesh, stamp, saxN.root, giant0, trail, trailHead, sparks, puff, newsS, payP, pig, kioskBox, hist.tablet, hist.key, hist.rotary, hist.ped, ...Object.values(labelPills), ...webs];
function resetFrame(t) {
  for (const o of ALL()) o.visible = false;
  newsS.visible = true; her.headG.visible = true; thumb.visible = false; pHand.visible = false; herArms(true); const lk = herLook(t); her.setHair(lk.hair, lk.colour); her.setShades(lk.shades); her.hair.burstFoils(-1); her.setFace(0, 0); HAIRO = {}; her.cape.visible = false; her.cape.position.set(0, 0, 0); her.cape.rotation.set(0, 0, 0); her.cape.scale.set(1, 1, 0.85); if (salonG) { salonG.userData.inner.visible = true; } finish.uniforms.uFlashCol.value.setRGB(1, 1, 1); bot.root.scale.setScalar(0.9); webs.forEach((w) => { w.scale.setScalar(1); w.material.opacity = 0.7; }); her.root.visible = false; bot.root.visible = false;
  bot.cord.mesh.visible = true; bot.handset.visible = true; bot.thrust(0); keypad.root.scale.setScalar(1);
  Wd.tower.setRobots([]); Wd.tower.body.material.uniforms.uScreenAmt.value = 0; ENV.dance.value = 0;
  Wd.tower.led.set('ON HOLD 47:00', { color: 0xff8a2a, gain: 2.4 });
  finish.uniforms.uSplit.value = 0; finish.uniforms.uFlash.value = 0; finish.uniforms.uLift.value = 0;
  ENV.time.value = t; ENV.beat.value = beatPulse(t); ENV.cloud.value = t * 0.01;
  Wd.tower.beacon.visible = (t % 1.6) < 0.5; for (const tr of Wd.trees) tr.visible = true;
}
// the glow-up: dark hair pulled back and no sunglasses until the reveal on "I don't wait anymore", honey-blonde waves and the wayfarers after
let HAIRO = {};
function herLook(t) { return t < (T.reveal ?? 98.08) ? { hair: 'pulled', colour: 'dark', shades: false } : { hair: 'waves', colour: 'blonde', shades: true }; }
function holdText(sec) { const m = Math.floor(sec / 60), s = Math.floor(sec % 60); return `ON HOLD ${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`; }
function towerWindows(mode, t) {
  const tw = Wd.tower;
  if (mode === 'night') tw.setAll((c, r) => { const h = Math.sin(c * 12.9898 + r * 78.233) * 43758.5453; const f = h - Math.floor(h); if (f > 0.58) return null;
    return f < 0.08 ? [1.0, 0.72, 0.42] : [0.62 + 0.2 * f, 0.78 + 0.15 * f, 0.95]; }, 'night');
  else if (mode === 'day') tw.setAll((c, r) => [0.16, 0.19, 0.24], 'day');
  else if (mode === 'off') tw.setAll(null, 'off');
}
// windows that spell a word (5x7 font): returns the lit cells
function spellCells(word, row0 = 6) { const rows = bitmap(word); const w = rows[0].length; const c0 = Math.floor((TOWER.cols - w) / 2); const out = [];
  for (let r = 0; r < 7; r++) for (let c = 0; c < w; c++) if (rows[r][c]) out.push([c0 + c, row0 + r]); return out; }

// ---------------------------------------------------------------- cameras
let shotKey = '';
function look(cam, p, l, fov, roll = 0) { cam.position.copy(p); cam.up.set(0, 1, 0); cam.lookAt(l); if (roll) cam.rotateZ(roll); cam.fov = fov; cam.near = 0.02; cam.far = 4000; cam.updateProjectionMatrix(); }
const vfov = (f, k = 1.62) => VERT ? Math.min(80, 2 * Math.atan(Math.tan(THREE.MathUtils.degToRad(f) / 2) * k) * 180 / Math.PI) : f;
function shake(t, t0, amt = 0.04, tau = 0.18) { if (t < t0) return V3(); const e = Math.exp(-(t - t0) / tau) * amt; return V3(Math.sin(t * 71) * e, Math.cos(t * 53) * e, Math.sin(t * 37) * e * 0.5); }
function handheld(t, a = 0.004) { return V3(Math.sin(t * 1.1) * a + Math.sin(t * 2.9) * a * 0.4, Math.sin(t * 1.7 + 1) * a, Math.sin(t * 0.8 + 2) * a * 0.6); }

// ---------------------------------------------------------------- HUD (crisp 2D on top, after bloom)
const S = Math.min(W, H) / 1080;
function hudText(txt, x, y, px, opt = {}) { hud.save(); hud.font = `${px}px ${opt.font || FONT.black}`; hud.textAlign = opt.align || 'center'; hud.textBaseline = 'middle';
  if (opt.shadow !== false) { hud.shadowColor = 'rgba(0,0,0,0.55)'; hud.shadowBlur = px * 0.25; hud.shadowOffsetY = px * 0.05; }
  hud.globalAlpha = opt.alpha ?? 1;
  if (opt.stroke) { hud.lineJoin = 'round'; hud.lineWidth = px * 0.14; hud.strokeStyle = '#0b0b0f'; hud.strokeText(txt, x, y); hud.shadowColor = 'transparent'; }
  hud.fillStyle = opt.color || '#ffffff'; hud.fillText(txt, x, y); hud.restore(); }
function drawHud(t) {
  hud.clearRect(0, 0, W, H); let any = false;
  const ca = caps.draw(t, SCENE_BRIGHT); if (ca > 0) { any = true; finish.uniforms.uScrim.value = ca * (0.1 + 0.32 * SCENE_BRIGHT); }
  // the hook: frame 0
  const a0 = 1 - sstep(4.9, 5.5, t);
  if (a0 > 0.01) { any = true; const lines = VERT ? ['millennials would', 'rather chew glass', 'than call'] : ['millennials would rather', 'chew glass than call']; const px = (VERT ? 74 : 62) * S;
    const y0 = VERT ? H * 0.15 : H * 0.11; lines.forEach((l, i) => hudText(l, W / 2, y0 + i * px * 1.12, px, { alpha: a0, stroke: true })); }
  // the title
  const a1 = sstep(16.75, 17.45, t) * (1 - sstep(21.6, 22.4, t));          // after "Grok, you take this one." blows away
  if (a1 > 0.01) { any = true; const x = VERT ? W / 2 : 80 * S, y = VERT ? H * 0.2 : H - 190 * S, al = VERT ? 'center' : 'left';
    hudText('aditazzz', x, y, 34 * S, { font: FONT.monoB, color: '#ff8a3a', align: al, alpha: a1 }); hudText('Please Hold', x, y + 72 * S, 84 * S, { font: FONT.disp, align: al, alpha: a1 }); }
  // PASS.
  if (t >= T.pass - 0.02 && t < T.pass + 0.9) { any = true; const u = t - T.pass; const sc = 1 + 0.9 * Math.exp(-u / 0.05) * (u < 0.12 ? 1 : 0) + (u < 0.12 ? (0.12 - u) * 6 : 0);
    hud.save(); hud.translate(W / 2, H * (VERT ? 0.5 : 0.52)); hud.rotate(-0.2); hud.scale(sc, sc); hud.globalAlpha = Math.min(1, u * 20) * (1 - sstep(0.7, 0.9, u));
    const px = (VERT ? 240 : 230) * S; hud.font = `${px}px ${FONT.stamp}`; const tw = hud.measureText('PASS.').width;
    hud.strokeStyle = '#ff4d1f'; hud.lineWidth = px * 0.07; hud.beginPath(); hud.roundRect(-tw / 2 - px * 0.18, -px * 0.62, tw + px * 0.36, px * 1.18, px * 0.12); hud.stroke();
    hud.fillStyle = '#ff4d1f'; hud.textAlign = 'center'; hud.textBaseline = 'middle'; hud.fillText('PASS.', 0, px * 0.04);
    const R = rng(12); hud.globalCompositeOperation = 'destination-out'; for (let i = 0; i < 220; i++) { hud.beginPath(); hud.arc((R() - 0.5) * (tw + px * 0.4), (R() - 0.5) * px * 1.2, R() * px * 0.025 + 1, 0, 7); hud.fill(); }
    hud.restore(); }
  // end card
  if (t >= T.card) { any = true; const a = sstep(T.card + 0.2, T.card + 0.7, t);
    if (VERT) { hudText('To follow,', W / 2, H * 0.2, 92 * S, { alpha: a }); hudText('press 1.', W / 2, H * 0.2 + 104 * S, 92 * S, { alpha: a, color: '#5ff4ff' }); hudText('@aditazzz.music', W / 2, H * 0.83, 46 * S, { font: FONT.ui, alpha: a, color: '#c9d3e0' }); }
    else { hudText('To subscribe,', W * 0.255, H * 0.43, 66 * S, { alpha: a, align: 'left' }); hudText('press 1.', W * 0.255, H * 0.43 + 80 * S, 66 * S, { alpha: a, color: '#5ff4ff', align: 'left' }); hudText('@adita_zzz', W * 0.255, H * 0.43 + 150 * S, 34 * S, { font: FONT.ui, alpha: a, color: '#c9d3e0', align: 'left' }); } }
  finish.uniforms.uHud.value = any ? 1 : 0; if (any) hudTex.needsUpdate = true;
}

// ---------------------------------------------------------------- the shots
// each: [a, b, fn(t, u)] where fn sets the world for this frame and returns the view(s): { cam: [p, look, fov, roll?] } or { split: [...] }
const SHOTS = [];
const shot = (a, b, fn, name = '') => SHOTS.push({ a, b, fn, name });

// --- INTRO
function povPhone(t, o = {}) {           // through her eyes: her phone in her hands, the thumb near
  her.root.visible = true; const pl = herWithPhone(t, herBowed(t, o.pose), { d: 0.3 }); her.headG.visible = false; herArms(false); pHand.visible = true;
  const up = V3(0, 1, 0).applyQuaternion(phone.root.quaternion); const p = pl.e.clone().add(handheld(t, 0.003)); const lk = pl.c.clone().addScaledVector(up, o.lift ?? 0.022).add(o.lookOff || V3());
  return { p, lk, c: pl.c };
}
function herArms(on) { for (const a of her.arms) for (const m of [a.up, a.fo, a.sh, a.el, a.hand]) m.visible = on; }
function thumbAt(x, y, h = 0.012, ang = 0) { thumb.visible = true; thumb.position.copy(phone.local(x, y)).add(V3(0, 0, h)); thumb.rotation.set(-0.5, 0, 0.35 + ang); }
shot(0, 5.55, (t, u) => {
  applyMood(MOOD.night, t); towerWindows('night', t);
  const v = povPhone(t); phone.draw({ screen: 'call', t, hold: 3 + t, clock: '9:41' }, 'call' + Math.floor(t * 30));
  thumbAt(470, 1250 - 40 * Math.sin(t * 1.3), 0.02 + 0.006 * Math.sin(t * 2), 0.1);
  return { cam: [v.p, v.lk.clone().add(V3(0, 0.008, 0)), (VERT ? 44 : 30) - u * 2] };
}, 'pov: on hold');
shot(5.55, 9.05, (t, u) => {
  applyMood(MOOD.night, t); towerWindows('night', t);
  const v = povPhone(t); const k = clamp((t - 6.0) / (9.3 - 6.0)); phone.draw({ screen: 'wait', t, hold: 3 + t, k }, 'wait' + Math.floor(t * 30));
  const f = lerp(VERT ? 40 : 27, VERT ? 30 : 19, easeIO(u)); return { cam: [v.p, v.lk.clone().add(V3(0, 0.004, 0)), f] };
}, 'pov: est. wait');
shot(9.05, 11.55, (t, u) => {
  applyMood(MOOD.night, t); towerWindows('night', t);
  her.root.visible = true; herWithPhone(t, herBowed(t)); phone.draw({ screen: 'call', t, hold: 3 + t }, 'cw' + Math.floor(t * 10));
  const flip = clamp((t - 9.28) / 0.35); Wd.tower.led.set(flip < 1 ? 'YOUR CALL IS IMPORTANT TO US' : 'ON HOLD 47:00', { scroll: flip < 1 ? (t - 8) * 22 : null });
  const p = V3(lerp(5.5, 4.2, u), lerp(1.3, 2.0, easeIO(u)), lerp(10, 8.5, u)); return { cam: [p, V3(-1.5, lerp(6, 7.5, u), -14), vfov(40)] };
}, 'wide: LED flips to ON HOLD 47:00');
shot(11.55, 12.78, (t, u) => {
  applyMood(MOOD.night, t); towerWindows('night', t);
  const v = povPhone(t); const press = clamp((t - T.hand) / 0.35);
  phone.draw({ screen: 'call', t, hold: 3 + t, press: t >= T.hand ? press : 0, pulse: Math.sin(t * 8) * 0.5 + 0.5 }, 'ho' + Math.floor(t * 30));
  const tx = lerp(470, 300, easeIO((t - 11.6) / 0.6)), ty = lerp(1250, 1090, easeIO((t - 11.6) / 0.6)); const tap = t >= T.hand ? Math.exp(-(t - T.hand) / 0.12) : sstep(T.hand - 0.25, T.hand, t);
  thumbAt(tx, ty, 0.03 * (1 - tap) + 0.002, 0.15);
  if (t >= T.hand) { const pa = sparks.geometry.attributes.position; const R = rng(9); sparks.visible = true; const sp = phone.root.localToWorld(phone.local(300, 1090));
    for (let i = 0; i < pa.count; i++) { const a = R() * 6.28, r = (t - T.hand) * (0.05 + R() * 0.25) * (i % 3 === 0 ? 1 : 0); pa.setXYZ(i, sp.x + Math.cos(a) * r, sp.y + (t - T.hand) * R() * 0.3 * (i % 3 === 0 ? 1 : 0), sp.z + Math.sin(a) * r); } pa.needsUpdate = true; sparks.material.size = 0.005; sparks.material.opacity = Math.max(0, 1 - (t - T.hand) * 2.5); }
  return { cam: [v.p, v.lk.clone().add(V3(0, -0.01, 0)), VERT ? 40 : 28] };
}, 'pov: HAND OFF');
shot(12.78, 15.8, (t, u) => {
  applyMood(MOOD.night, t); towerWindows('night', t);
  her.root.visible = true; herWithPhone(t, herBowed(t, { headPitch: lerp(0.6, -0.15, easeIO((t - 12.8) / 1.2)), lean: lerp(0.27, 0.05, easeIO((t - 12.8) / 1.2)) }), { d: lerp(0.3, 0.42, easeIO((t - 12.8) / 1.2)) });
  phone.draw({ screen: 'call', t, hold: 3 + t }, 'c2' + Math.floor(t * 10));
  const k = easeIn(clamp((t - 12.8) / 2.9)); setTrail(trailUp, 0.02 + 0.95 * k, 0.22, 1, 0.07);
  const hp = trailUp.getPointAt(0.02 + 0.95 * k);
  const p = V3(-2.6, 0.9, 3.2); const lk = V3(-0.3, 1.2, -1).lerp(hp, sstep(0.0, 0.8, u) * 0.85);
  return { cam: [p, lk, vfov(46)] };
}, 'the call streaks up');
shot(15.8, 18.48, (t, u) => {
  applyMood(MOOD.night, t); towerWindows('night', t); her.root.visible = true; herWithPhone(t, herBowed(t)); phone.draw({ screen: 'call', t, hold: 3 + t }, 'c3' + Math.floor(t * 10));
  setTrail(trailUp, 1.0, 0.16 * (1 - u), 1 - u, 0.09); Wd.trees[3].visible = false;     // the near tree would hide the LED band
  const p = V3(lerp(14, 12, u), lerp(2.0, 3.0, u), lerp(16, 13, u)); return { cam: [p, V3(-2, VERT ? lerp(21, 17, easeIO(u)) : lerp(30, 24, easeIO(u)), -30), vfov(52)] };   // 9:16: the LED band sits above the lyric
}, 'title: the city at night');
shot(18.48, 20.9, (t, u) => {
  applyMood(MOOD.night, t); towerWindows('night', t); her.root.visible = true; herWithPhone(t, herBowed(t)); phone.draw({ screen: 'call', t, hold: 3 + t }, 'c4' + Math.floor(t * 10));
  Wd.tower.led.set(holdText(3 + t), {});
  const p = V3(lerp(-9, -6, u), 1.4, lerp(7, 6.2, u)); return { cam: [p, V3(-0.5, lerp(1.3, 1.6, u), -2), vfov(30)] };
}, 'her on the bench, side');
shot(20.9, T_BILL(), (t, u) => {
  applyMood(MOOD.night, t); towerWindows('night', t); her.root.visible = true; herWithPhone(t, herBowed(t)); phone.draw({ screen: 'call', t, hold: 3 + t }, 'c5' + Math.floor(t * 10));
  const p = V3(0.6, lerp(1.25, 1.15, u), lerp(3.4, 2.4, easeIO(u))); return { cam: [p, V3(-0.3, 0.75, -0.2), vfov(34)] };
}, 'push in: still holding');
function T_BILL() { return 23.28; }

// --- VERSE 1
function studio(a, b) { Wd.studio.set(a, b); applyMood(MOOD.studio, 0); }
shot(23.28, 25.05, (t, u) => {          // the bill slaps down
  studio('#ffb98a', '#e2703c'); bill.root.visible = true; bill.draw(0);
  const d = t - T.bill; const drop = d < 0.22 ? 1 - easeIn(d / 0.22) : 0; const [sx, sy] = squash(t, T.bill + 0.22, 0.25, 0.12);
  bill.root.position.copy(STUDIO).add(V3(0, 0.002 + drop * 0.8, 0)); bill.root.rotation.set(-Math.PI / 2 + drop * 0.6, 0, drop * 0.5 + 0.06); bill.root.scale.set(sx, sx, 1); bill.bend(drop * 0.6 + (1 - sy) * 0.4);
  const p = STUDIO.clone().add(V3(0.02, lerp(0.42, 0.36, u), 0.02)).add(shake(t, T.bill + 0.22, 0.01)); return { cam: [p, STUDIO.clone().add(V3(0.0, 0, -0.005)), VERT ? 62 : 44, 0.06] };
}, 'bill: slap');
shot(25.05, 27.2, (t, u) => {          // the circle, in hot orange
  studio('#ffb98a', '#e2703c'); bill.root.visible = true; bill.draw(clamp((t - 25.25) / 0.9)); bill.root.position.copy(STUDIO).add(V3(0, 0.002, 0)); bill.root.rotation.set(-Math.PI / 2, 0, 0.06); bill.root.scale.set(1, 1, 1); bill.bend(0);
  const pk = 1 + 0.06 * Math.exp(-Math.max(0, t - wordT(3, 'bill')) / 0.15) * (t > wordT(3, 'bill') ? 1 : 0);
  const tgt = STUDIO.clone().add(V3(0.055, 0, 0.006)); const p = tgt.clone().add(V3(lerp(-0.05, -0.02, u), lerp(0.2, 0.15, easeIO(u)) / pk, lerp(0.12, 0.09, u)));
  return { cam: [p, tgt, VERT ? 56 : 40] };
}, 'bill: $4.00 circled');
shot(27.2, 30.64, (t, u) => {          // forty-seven minutes: the sky time-lapses, the band counts up
  applyMood(moodAt(t), t); towerWindows(ENV.day.value > 0.5 ? 'day' : 'night', t);
  her.root.visible = true; herWithPhone(t, herBowed(t)); phone.draw({ screen: 'call', t, hold: 2820 + u * 400 }, 'tl' + Math.floor(t * 10));
  ENV.cloud.value = t * 0.01 + u * 3; const sun = V3(-1, lerp(-0.1, 0.8, u), lerp(0.2, 0.6, u)).normalize(); ENV.sunDir.value.copy(sun); key.position.copy(sun).multiplyScalar(30);
  Wd.tower.led.set(holdText(2820 + u * 400), {});
  const p = V3(lerp(1.6, 1.4, u), 0.55, lerp(4.2, 3.9, u)); return { cam: [p, V3(-0.35, 2.2, -4), vfov(50)] };
}, 'time-lapse: still holding');
shot(30.64, 32.7, (t, u) => {          // press one for billing
  studio('#58d6e3', '#1f7f95'); keypad.root.visible = true; keypad.root.position.copy(STUDIO).add(V3(0, 0.6, 0)); keypad.root.rotation.set(-0.35, 0.25, 0);
  keyPress(t);
  const p = STUDIO.clone().add(V3(lerp(0.3, 0.22, u), lerp(0.95, 0.9, u), lerp(0.75, 0.68, u))); return { cam: [p, STUDIO.clone().add(V3(-0.05, 0.74, 0)), VERT ? 58 : 38] };
}, 'keypad: 1');
shot(32.7, 34.72, (t, u) => {          // press two for despair
  studio('#58d6e3', '#1f7f95'); keypad.root.visible = true; keypad.root.position.copy(STUDIO).add(V3(0, 0.6, 0)); keypad.root.rotation.set(-0.35, 0.25, 0); keyPress(t);
  const p = STUDIO.clone().add(V3(lerp(-0.24, -0.16, u), lerp(0.98, 0.94, u), lerp(0.7, 0.66, u))); return { cam: [p, STUDIO.clone().add(V3(0.0, 0.78, 0)), VERT ? 56 : 38] };
}, 'keypad: 2');
shot(34.72, 36.75, (t, u) => {          // press three
  studio('#58d6e3', '#1f7f95'); keypad.root.visible = true; keypad.root.position.copy(STUDIO).add(V3(0, 0.6, 0)); keypad.root.rotation.set(-0.35, 0.25, 0); keyPress(t);
  const p = STUDIO.clone().add(V3(0.1, lerp(0.92, 1.0, u), lerp(0.55, 0.62, u))); return { cam: [p, STUDIO.clone().add(V3(0.08, 0.76, 0)), VERT ? 56 : 36] };
}, 'keypad: 3');
function keyPress(t) {
  const kp = keypad.root.position, kr = keypad.root;
  for (const [d, tt] of [['1', T.press1], ['2', T.press2], ['3', T.press3]]) {
    const u = t - tt; const press = u >= 0 && u < 0.25 ? Math.sin(Math.PI * u / 0.25) : 0; const lit = u >= 0 ? 1 - sstep(1.8, 2.4, u) : 0; keypad.set(d, press, lit);
    const pill = labelPills[d]; if (u > 0.05 && u < 2.4) { pill.visible = true; const k = keypad.key(d); const wp = kr.localToWorld(V3(k.x * 0.5, k.y + 0.09 + 0.05 * easeOutBack(clamp(u / 0.3)), 0.09));
      pill.position.copy(wp); pill.quaternion.copy(kr.quaternion); const s = easeOutBack(clamp((u - 0.05) / 0.3)) * (1 - sstep(2.0, 2.4, u)); pill.scale.setScalar(Math.max(0.001, s)); }
  }
}
shot(36.75, 38.72, (t, u) => {          // ...that nobody's there
  studio('#a9b4c2', '#5b6878'); cub.visible = true; cub.userData.chair.rotation.y = t * 0.6;
  const m = cub.userData.mtex; m.userData.redraw('m', (g, w, h) => { g.fillStyle = '#0d1a2a'; g.fillRect(0, 0, w, h); g.fillStyle = '#5ff4ff'; g.font = `44px ${FONT.black}`; g.textAlign = 'center'; g.fillText('PLEASE HOLD', w / 2, h / 2 - 10); g.font = `26px ${FONT.ui}`; g.fillStyle = '#93a0ae'; g.fillText('agent away', w / 2, h / 2 + 40); });
  const c = cub.position; const p = c.clone().add(V3(lerp(0.9, 0.7, u), lerp(1.45, 1.4, u), lerp(2.4, 2.1, u))); return { cam: [p, c.clone().add(V3(0, 0.75, -0.3)), VERT ? 60 : 40] };
}, 'cubicle: nobody');
shot(38.72, 40.9, (t, u) => {          // I'm a millennial
  applyMood(MOOD.day, t); towerWindows('day', t);
  const v = povPhone(t); phone.draw({ screen: 'callrep', t, clock: '1:12' }, 'rep' + Math.floor(t * 30));
  const k = easeIO((t - 39.0) / 1.6); thumbAt(lerp(520, 420, k), lerp(1300, 960, k), lerp(0.03, 0.014, k), 0.1);
  return { cam: [v.p, v.lk, VERT ? 42 : 28] };
}, 'pov: CALL button');
shot(40.9, 42.64, (t, u) => {          // ...rather chew glass: the thumb hovers, then pulls back
  applyMood(MOOD.day, t); towerWindows('day', t);
  const v = povPhone(t); phone.draw({ screen: 'callrep', t, clock: '1:12' }, 'rep' + Math.floor(t * 30));
  const back = easeIO((t - (T.glass - 0.1)) / 0.4); const hov = Math.sin(t * 9) * 4 * (1 - back);
  thumbAt(lerp(420, 540, back), lerp(960, 1380, back) + hov, lerp(0.014, 0.05, back) + 0.003 * Math.sin(t * 7), 0.1);
  return { cam: [v.p, v.lk.clone().add(V3(0, -0.012, 0)), VERT ? 32 : 21] };
}, 'pov: thumb pulls back');
shot(42.64, 46.72, (t, u) => {          // read the last four of my card out loud. PASS.
  applyMood(MOOD.day, t); towerWindows('day', t);
  const v = povPhone(t); phone.draw({ screen: 'prompt', t, clock: '1:13' }, 'pr' + Math.floor(t * 30));
  thumbAt(520, 1380, 0.05, 0.1);
  const f = lerp(VERT ? 42 : 28, VERT ? 36 : 24, easeIO(u)); const sh = shake(t, T.pass, 0.012, 0.15);
  if (t >= T.pass) finish.uniforms.uFlash.value = 0.25 * Math.exp(-(t - T.pass) / 0.06);
  return { cam: [v.p.clone().add(sh), v.lk, f] };
}, 'pov: say the digits / PASS.');
shot(46.72, 48.62, (t, u) => {          // so I sent in Grok: the light comes back down
  applyMood(MOOD.day, t); towerWindows('day', t); her.root.visible = true; herWithPhone(t, herBowed(t, { headPitch: lerp(0.6, -0.1, easeIO(u)) }), { d: lerp(0.3, 0.4, easeIO(u)) }); phone.draw({ screen: 'prompt', t }, 'pr2');
  const k = easeIn(clamp((t - 46.72) / 1.95)); setTrail(trailDown, 0.02 + 0.97 * k, 0.3, 1, 0.16);
  const hp = trailDown.getPointAt(0.02 + 0.97 * k);
  const p = V3(-3.0, 0.8, 5.0); return { cam: [p, V3(1.0, 2.0, -1).lerp(hp, 0.62), vfov(60)] };
}, 'the light comes back down');
shot(48.62, 50.0, (t, u) => {          // ...and lands as the robot, with a puff
  applyMood(MOOD.day, t); towerWindows('day', t); her.root.visible = true; herWithPhone(t, herBowed(t, { headPitch: -0.05, headYaw: 0.45, lean: 0.04 }), { d: 0.42 }); phone.draw({ screen: 'prompt', t }, 'pr2');
  bot.root.visible = true; const d = t - T.land; const fall = d < 0 ? 1 - easeIn((t - 48.3) / (T.land - 48.3)) : 0;
  const [sx, sy] = squash(t, T.land, 0.3, 0.14);
  bot.pose({ x: BOT0.x, z: BOT0.z, y: 0.6 * Math.max(0, fall) + (d < 0 ? 0 : 0), seat: d < 0 ? 0.3 : clamp(d / 0.25) * 0.7 + 0.3, lean: 0.05, headPitch: -0.1, headYaw: -0.5 * sstep(0.3, 0.7, d), hands: d < 0 ? [[-0.4, 0.35, 0.05], [0.4, 0.35, 0.05]] : [[-0.25, 0.25 + 0.15 * sstep(0.4, 0.8, d), 0.2], [0.24, 0.2 + 0.5 * sstep(0.5, 0.8, d), 0.12]] });
  bot.root.scale.set(0.9 * sx, 0.9 * sy, 0.9 * sx); bot.thrust(d < 0 ? 1 : Math.exp(-d / 0.12)); bot.setEye(d > 0.5 ? 'happy' : 'eyes', t, { blink: 0 }); bot.handset.visible = true; bot.updateCord();
  puffAt(V3(BOT0.x, 0.45, BOT0.z), t, T.land);
  setTrail(trailDown, 1.0, 0.3 * (1 - clamp(d / 0.3)), 1 - clamp(d / 0.3), 0.08);
  const p = V3(lerp(2.2, 1.9, u), 1.0, lerp(3.4, 3.0, u)).add(shake(t, T.land, 0.02)); return { cam: [p, V3(0.1, 0.75, -0.1), vfov(38)] };
}, 'the robot lands');
function puffAt(c, t, t0) { const d = t - t0; puff.visible = d >= 0 && d < 1.4; if (!puff.visible) return; const pa = puff.geometry.attributes.position; const R = rng(21);
  for (let i = 0; i < pa.count; i++) { const a = R() * 6.28, sp = 0.6 + R() * 1.4; const r = sp * (1 - Math.exp(-d * 3)) * 0.6; pa.setXYZ(i, c.x + Math.cos(a) * r, c.y + 0.05 + R() * 0.25 * d, c.z + Math.sin(a) * r); }
  pa.needsUpdate = true; puff.material.opacity = 0.75 * (1 - d / 1.4); puff.material.size = 0.18 + d * 0.25; }

// she stands up and walks away (give it a beat and a good camera move)
const WALK = { speed: 1.25, cad: 1.85 };
function herStandWalk(t) {     // 49.55 stand, 50.4 turn and walk off to the kiosk (+x)
  const s = clamp((t - T.stand) / 0.85); const seat = 1 - easeIO(s);
  const tw = Math.max(0, t - (T.stand + 0.8)); const dist = tw * WALK.speed * sstep(0, 0.4, tw);
  const path = V3(HER0.x, 0, HER0.z + 0.25 * easeIO(s)); const dir = V3(1, 0, 0.35).normalize(); path.addScaledVector(dir, dist);
  const turn = lerp(0, Math.atan2(dir.x, dir.z), sstep(0, 0.5, tw));
  return { x: path.x, z: path.z, turn, seat, lean: 0.27 * (1 - s) + 0.25 * Math.sin(Math.PI * s) * 0.6, headPitch: lerp(0.6, 0.0, easeIO(s)), hands: [[-0.2, -0.05 + 0.1 * Math.sin(tw * WALK.cad * Math.PI), 0.08 + 0.1 * Math.sin(tw * WALK.cad * Math.PI)], [0.2, -0.05 - 0.1 * Math.sin(tw * WALK.cad * Math.PI), 0.08 - 0.1 * Math.sin(tw * WALK.cad * Math.PI)]],
    walk: tw * WALK.cad * Math.PI, stride: sstep(0, 0.3, tw) };
}
shot(50.0, 52.2, (t, u) => {
  applyMood(MOOD.day, t); towerWindows('day', t); her.root.visible = true; her.pose(herStandWalk(t));
  bot.root.visible = true; bot.root.scale.setScalar(0.9);
  const k = sstep(50.6, 51.9, t); const bp = mixPose(botWave(t), botHold(t), k); bot.pose(bp); bot.setEye(k > 0.5 ? 'wave' : 'happy', t); bot.updateCord();
  const a = lerp(-0.25, 0.75, easeIO(u)); const r = lerp(4.2, 6.0, u); const p = V3(Math.sin(a) * r, lerp(1.1, 2.6, easeIO(u)), Math.cos(a) * r);
  return { cam: [p, V3(lerp(-0.2, 1.8, easeIO(u)), 0.9, 0.2), vfov(42)] };
}, 'she stands and walks off');
function botWave(t) { return { x: BOT0.x, z: BOT0.z, seat: 1, lean: 0.02, headPitch: -0.05, headYaw: -0.4, hands: [[-0.2, 0.2, 0.2], [0.26, 0.62 + 0.03 * Math.sin(t * 12), 0.1 + 0.06 * Math.sin(t * 12)]] }; }
function mixPose(a, b, k) { const o = {}; for (const n of new Set([...Object.keys(a), ...Object.keys(b)])) { const x = a[n] ?? b[n], y = b[n] ?? a[n]; o[n] = typeof x === 'number' ? lerp(x, y, k) : (Array.isArray(x) ? x.map((v, i) => Array.isArray(v) ? v.map((w, j) => lerp(w, y[i][j], k)) : lerp(v, y[i], k)) : (k < 0.5 ? x : y)); } return o; }

// the split: the robot in her old pose | her at the takeout window
function herAtKiosk(t, o = {}) {
  const kp = Wd.kiosk.position; return { x: kp.x - 2.2, z: kp.z + 0.1, turn: Math.PI / 2, seat: 0, lean: 0.03, headPitch: -0.05, hands: o.hands || [[-0.2, -0.05, 0.08], [0.2, -0.05, 0.08]], walk: 0, stride: 0, ...o };
}
function kioskHandOff(t) {           // a hand passes the box out of the window; she takes it on "Chinese"
  const kp = Wd.kiosk.position; const k = sstep(T.chinese - 0.9, T.chinese - 0.2, t); const take = sstep(T.chinese - 0.2, T.chinese + 0.4, t);
  kioskBox.visible = true; kioskBox.scale.setScalar(1.6);
  const out = V3(kp.x - 1.25, 1.12, kp.z + 0.0); const inside = V3(kp.x - 0.6, 1.1, kp.z); const herHand = V3(kp.x - 1.75, 1.05, kp.z + 0.1);
  kioskBox.position.copy(inside.clone().lerp(out, k).lerp(herHand, take)); kioskBox.rotation.y = Math.PI / 2;
  return { reach: sstep(T.chinese - 0.6, T.chinese - 0.1, t), take };
}
shot(52.2, 54.64, (t, u) => {
  applyMood(MOOD.day, t); towerWindows('day', t); Wd.kiosk.userData.inside.material.color.setRGB(1.0, 0.75, 0.48);
  bot.root.visible = true; bot.root.scale.setScalar(0.9); bot.pose(botHold(t)); bot.setEye('wave', t); bot.updateCord();
  her.root.visible = true; const ko = kioskHandOff(t); her.pose(herAtKiosk(t, { hands: [[-0.15, 0.25 * ko.reach + (-0.05) * (1 - ko.reach), 0.08 + 0.32 * ko.reach], [0.15, 0.25 * ko.reach - 0.05 * (1 - ko.reach), 0.08 + 0.32 * ko.reach]] }));
  const A = { cam: [V3(1.9, 0.95, 2.6), V3(0.35, 0.78, -0.05), vfov(30, 1.15)] };
  const kp = Wd.kiosk.position; const B = { cam: [V3(kp.x - 4.6, 1.5, kp.z + 2.9), V3(kp.x - 1.6, 1.2, kp.z), vfov(30, 1.15)] };
  return { split: [A, B] };
}, 'split: robot | takeout');

// it's got all day, it can take all the notes
shot(54.64, 56.75, (t, u) => {
  applyMood(MOOD.day, t); towerWindows('day', t); bot.root.visible = true; bot.root.scale.setScalar(0.9); bot.pose(botHold(t, { headPitch: 0.3 })); bot.setEye(t < T.notes - 0.6 ? 'wave' : 'notes', t, { k: clamp((t - (T.notes - 0.6)) / 3) }); bot.updateCord();
  const hp = bot.headWorld(); const p = hp.clone().add(V3(lerp(0.65, 0.5, u), lerp(-0.05, 0.0, u), lerp(1.1, 0.9, u))); return { cam: [p, hp.clone().add(V3(0, -0.12, 0)), vfov(30)] };
}, 'robot: notes');
shot(56.75, 58.72, (t, u) => {
  applyMood(MOOD.day, t); towerWindows('day', t); bot.root.visible = true; bot.root.scale.setScalar(0.9); bot.pose(botHold(t, { headPitch: 0.25 })); bot.setEye('notes', t, { k: clamp((t - (T.notes - 0.6)) / 3.2) }); bot.updateCord();
  bot.root.updateMatrixWorld(true); const ep = V3(0, 0.152, 0.13).applyMatrix4(bot.headG.matrixWorld); const fwd = V3(0, 0, 1).applyQuaternion(bot.headG.getWorldQuaternion(new THREE.Quaternion()));
  const p = ep.clone().addScaledVector(fwd, lerp(0.42, 0.34, u)).add(V3(0.02, 0.01, 0)); return { cam: [p, ep, VERT ? 44 : 30] };
}, 'eye strip: the notepad');
// and it doesn't get mad when the saxophone loops
function saxLoop(t, t0, center, o = {}) {
  const rec = bot.handset.getWorldPosition(V3());
  saxN.root.visible = true; saxN.set((i) => { const st = t0 + i * 0.16; const d = t - st; if (d < 0) return null;
    const rise = clamp(d / 1.2); const ang = d * 1.6 + i * (Math.PI * 2 / 16);
    const lp = center.clone().add(V3(Math.cos(ang) * 0.7, 0.1 * Math.sin(d * 3 + i), Math.sin(ang) * 0.5));
    const p = rec.clone().lerp(lp, easeOut(rise)).add(V3(0, Math.sin(d * 5 + i) * 0.03, 0));
    return { p, scale: 0.17 * easeOutBack(clamp(d / 0.4)) * (o.scale ?? 1), op: 1, rot: Math.sin(d * 4 + i) * 0.3 }; });
}
shot(58.72, 60.62, (t, u) => {
  applyMood(MOOD.day, t); towerWindows('day', t); bot.root.visible = true; bot.root.scale.setScalar(0.9); bot.pose(botHold(t, { headPitch: 0.3 + 0.06 * Math.sin(t * 6.3) })); bot.setEye('happy', t); bot.updateCord();
  saxLoop(t, ls(12) - 0.1, bot.headWorld().add(V3(0, 0.45, 0)));
  const hp = bot.headWorld(); const p = hp.clone().add(V3(lerp(-1.3, -1.1, u), -0.15, lerp(1.9, 1.7, u))); return { cam: [p, hp.clone().add(V3(0.1, 0.25, 0)), vfov(38)] };
}, 'sax notes rise');
shot(60.62, 62.46, (t, u) => {
  applyMood(MOOD.day, t); towerWindows('day', t); bot.root.visible = true; bot.root.scale.setScalar(0.9); bot.pose(botHold(t, { headPitch: 0.3 + 0.06 * Math.sin(t * 6.3), headRoll: -0.1 + 0.08 * Math.sin(t * 3.1) })); bot.setEye('happy', t); bot.updateCord();
  saxLoop(t, ls(12) - 0.1, bot.headWorld().add(V3(0, 0.45, 0)));
  const a = lerp(0.3, -0.1, u); const p = V3(BOT0.x + Math.sin(a) * 3.2, lerp(1.0, 1.4, u), Math.cos(a) * 3.2); return { cam: [p, V3(BOT0.x, 1.0, 0), vfov(40)] };
}, 'sax notes loop');

// --- PRE-CHORUS: follow the cord into the tower; machines on hold in every window
const CORD_PTS = (() => { const z0 = TOWER.zf; const top = winCenter(12, 14); return [V3(0.45, 0.66, -0.12), V3(0.5, 0.25, -0.5), V3(0.8, 0.07, -1.2), V3(1.5, 0.07, -3), V3(0.8, 0.07, -12), V3(-0.4, 0.07, -24), V3(0.2, 0.08, z0 + 0.6), V3(0.3, 4, z0 + 0.15), V3(0.25, 9, z0 + 0.12), V3(top.x, top.y - 2, z0 + 0.12), V3(top.x, top.y - 0.5, z0 - 0.2)]; })();
const cordCurve = new THREE.CatmullRomCurve3(CORD_PTS);
const longCordC = new Cord(gloss(0x16161a, { shininess: 70, specular: 0x888c94, rimAmt: 0.35 }), { r: 0.017, coil: 0.06, turnsPerM: 7 });
longCordC.update(V3(), V3(), 0, { pts: CORD_PTS, maxN: 9000 }); const longCord = longCordC.mesh; scene.add(longCord);
function windowBots(cells, t, k = 1) { Wd.tower.setRobots(cells.map(([c, r], i) => [c, r, k * sstep(i * 0.012, i * 0.012 + 0.2, k), Math.sin(t * 2 + i) * 0.05])); }
let netLines = null;
function windowNet(cells) {           // cords from window to window (built once)
  if (netLines) return netLines; const pos = [];
  const set = new Set(cells.map(([c, r]) => c + ',' + r));
  for (const [c, r] of cells) for (const [dc, dr] of [[1, 0], [0, 1], [1, 1]]) if (set.has((c + dc) + ',' + (r + dr))) { const a = winCenter(c, r), b = winCenter(c + dc, r + dr); a.z += 0.05; b.z += 0.05; a.y -= 0.35; b.y -= 0.35;
    const m = a.clone().lerp(b, 0.5).add(V3(0, -0.35, 0.1)); const cv = new THREE.QuadraticBezierCurve3(a, m, b); const pts = cv.getPoints(10); for (let i = 0; i < 10; i++) pos.push(pts[i].x, pts[i].y, pts[i].z, pts[i + 1].x, pts[i + 1].y, pts[i + 1].z); }
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  netLines = new THREE.LineSegments(g, new THREE.LineBasicMaterial({ color: 0x0a0a0c })); scene.add(netLines); return netLines;
}
const HOLD_CELLS = spellCells('HOLD', 6);
const U_BASE = (() => { for (let u = 0; u <= 1; u += 0.002) if (cordCurve.getPointAt(u).z <= TOWER.zf + 0.75) return u; return 0.5; })();
shot(62.46, 64.62, (t, u) => {          // along the ground: the cord runs from its chest across the plaza
  applyMood(moodAt(t), t); towerWindows('day', t);
  bot.root.visible = true; bot.root.scale.setScalar(0.9); bot.pose(botHold(t)); bot.setEye('wave', t, { amp: 0.5 }); bot.updateCord();
  longCord.visible = true;
  const k = easeIO(u); const uc = lerp(0.015, U_BASE * 0.8, k); const cp = cordCurve.getPointAt(uc); const ahead = cordCurve.getPointAt(Math.min(1, uc + 0.05));
  const p = cp.clone().add(V3(0.7, lerp(0.9, 0.5, k), 1.6)); return { cam: [p, ahead.clone().add(V3(0, lerp(0.4, 4, k), 0)), vfov(48)] };
}, 'follow the cord: across the plaza');
shot(64.62, 66.56, (t, u) => {          // ...and up the face of the tower to a window
  applyMood(moodAt(t), t); towerWindows(ENV.day.value > 0.6 ? 'day' : 'off', t); longCord.visible = true;
  const k = easeIO(u); const uc = lerp(U_BASE, 0.985, k); const cp = cordCurve.getPointAt(uc);
  const p = V3(cp.x + 3.5, Math.max(3, cp.y - 2), TOWER.zf + 9); return { cam: [p, cp.clone().add(V3(0, 1.5, 0)), vfov(44)] };
}, 'follow the cord: up the tower');
shot(66.56, 70.43, (t, u) => {
  applyMood(moodAt(t), t); towerWindows('off', t); longCord.visible = true;
  const lit = sstep(66.6, 68.4, t);
  Wd.tower.setAll((c, r) => HOLD_CELLS.some(([cc, rr]) => cc === c && rr === r) ? [0.9 * lit + 0.03, 1.7 * lit + 0.03, 1.9 * lit + 0.04] : null, 'hold' + Math.round(lit * 30));
  windowBots(HOLD_CELLS, t, lit); const net = windowNet(HOLD_CELLS); net.visible = true;
  const top = winCenter(12, 6); const p = V3(lerp(-4, -3, u), lerp(6, 11, easeIO(u)), TOWER.zf + lerp(30, 26, u)); return { cam: [p, V3(0, lerp(top.y - 14, top.y - 4, easeIO(u)), TOWER.zf), vfov(46)] };
}, 'machines on hold, in every window');

// --- CHORUS 1 (first pass: PLEASE HOLD on the tower)
// ---------------------------------------------------------------- the tower as one giant screen
function screenDraw(key, fn) { const tex = Wd.tower.screen; if (!tex.userData.g) tex.userData.g = tex.image.getContext('2d'); if (tex.userData.key === key) return; tex.userData.key = key; const g = tex.userData.g, w = tex.image.width, h = tex.image.height; g.setTransform(1, 0, 0, 1, 0, 0); g.clearRect(0, 0, w, h); fn(g, w, h); tex.needsUpdate = true; }
function screenWords(t, words, times, colors) {     // big words on the facade, each slamming in on its time
  const n = times.filter((x) => t >= x).length; const last = times[n - 1] ?? 0; const k = Math.round(clamp((t - last) / 0.25) * 10);
  screenDraw('w' + words.join() + n + '_' + k, (g, w, h) => { const bg = g.createLinearGradient(0, 0, 0, h); bg.addColorStop(0, '#04161c'); bg.addColorStop(1, '#0a0420'); g.fillStyle = bg; g.fillRect(0, 0, w, h);
    g.textAlign = 'center'; g.textBaseline = 'middle';
    words.forEach((wd, i) => { if (i >= n) return; const sc = i === n - 1 ? easeOutBack(k / 10) : 1; g.save(); g.translate(w / 2, h * (0.33 + i * 0.3)); g.scale(sc, sc);
      g.font = `${w * 0.27}px ${FONT.black}`; g.shadowColor = colors[i]; g.shadowBlur = w * 0.04; g.fillStyle = colors[i]; g.fillText(wd, 0, 0); g.restore(); }); });
}
let cameoImgs = {}; async function cameoFrame(n) { const k = Math.max(0, Math.min(CAMEO_N - 1, n)); if (cameoImgs[k]) return cameoImgs[k];
  const img = new Image(); img.src = `/tex/cameo/c_${String(k).padStart(4, '0')}.jpg`; await img.decode().catch(() => null); cameoImgs = { [k]: img }; return img; }
const CAMEO_N = 124;
let CAMEO_IMG = null;

// --- CHORUS 1
shot(70.43, 73.68, (t, u) => {        // PLEASE HOLD: the whole face of the tower
  applyMood(MOOD.night, t); towerWindows('off', t);
  const tw = Wd.tower; tw.body.material.uniforms.uScreenAmt.value = sstep(70.43, 70.6, t); tw.body.material.uniforms.uScreenGain.value = 1.6 + 0.6 * downPulse(t);
  screenWords(t, ['PLEASE', 'HOLD'], [wordT(15, 'please'), LN[15].wt[1]], ['#ffffff', '#5ff4ff']);
  tw.led.set('PLEASE HOLD', { color: 0x5ff4ff, gain: 2.6 + 1.5 * downPulse(t) });
  if (t < 70.7) finish.uniforms.uFlash.value = 0.5 * (1 - (t - 70.43) / 0.27);
  bot.root.visible = true; bot.root.scale.setScalar(0.9); bot.pose(botHold(t)); bot.setEye('wave', t); bot.updateCord();
  const bump = downPulse(t); const p = V3(lerp(3.2, 2.4, u), 0.45, lerp(5.2, 4.5, u)); return { cam: [p, V3(-0.6, lerp(15, 17, u), -20), vfov(60) - bump * 3] };
}, 'PLEASE HOLD');
// the robot waits through days | she is at the salon under the dryer, eating onion rings
function hoodLift(k) {               // 0: over her head, dryer on; 1: swung up and off
  const hd = salonG.userData.hood; hd.position.set(0, 1.56 + 0.2 * k, -0.13 - 0.16 * k); hd.rotation.x = 0.34 - 1.05 * k; salonG.userData.inner.visible = k < 0.5; }
function herSalon(t, o = {}) {
  const post = o.post ?? t >= T.reveal;
  if (post) { her.setHair('waves', 'blonde'); her.setShades(true); her.cape.visible = false; } else { her.setHair('foils', 'blonde'); her.setShades(false); her.cape.visible = true; }
  salonG.visible = true; salonG.position.copy(STUDIO); hoodLift(post ? 1 : 0);
  const eat = o.eat ?? 0; const b = { x: STUDIO.x, y: 0.07, z: STUDIO.z + 0.04, seat: 1, lean: -0.08, headPitch: -0.12 + 0.1 * eat, headYaw: o.yaw ?? 0.1, headRoll: 0.04,
    hands: [[-0.08, 0.18, 0.3], [lerp(0.1, 0.03, eat), lerp(0.2, 0.62, eat), lerp(0.3, 0.16, eat)]], kneeOut: 0.03, ...o.pose };
  her.root.visible = true; her.pose(b); bag.visible = true; her.root.updateMatrixWorld(true);
  const hl = her.handWorld(0); bag.position.copy(hl).add(V3(0.01, 0.05, 0.03)); bag.rotation.set(-0.35, 0.25, 0.1);
  ring1.visible = true; ring1.position.copy(her.handWorld(1)).add(V3(0, 0.06, 0.02)); ring1.rotation.set(1.2, 0.3, t);
}
function salonCam(t, u, o = {}) { const c = STUDIO.clone().add(V3(0, 1.12, 0.12)); const a = o.a ?? lerp(0.5, 0.35, u); const r = o.r ?? 2.0; return [c.clone().add(V3(Math.sin(a) * r, o.h ?? 0.25, Math.cos(a) * r)), c.clone().add(V3(0, o.ly ?? 0.05, 0)), o.fov ?? vfov(36, 1.0)]; }
shot(73.68, 77.76, (t, u) => {
  Wd.studio.set('#f4d6cf', '#c99a94');
  const cyc = (t - 73.68) / 4.08; const m = cyc < 0.33 ? mixMood(MOOD.day, MOOD.dusk, cyc / 0.33) : (cyc < 0.6 ? mixMood(MOOD.dusk, MOOD.night, (cyc - 0.33) / 0.27) : mixMood(MOOD.night, MOOD.day, (cyc - 0.6) / 0.4));
  bot.root.visible = true; bot.root.scale.setScalar(0.9); bot.pose(botHold(t)); bot.setEye('wave', t); bot.updateCord();
  herSalon(t, { eat: Math.max(hit(t, 74.4, 0.3), hit(t, 75.7, 0.3), hit(t, 76.9, 0.3)) });
  const A = { cam: [V3(2.0, 1.0, 2.8), V3(0.3, 0.95, -0.2), vfov(34, 1.15)], before: () => { applyMood(m, t); towerWindows(m.day > 0.5 ? 'day' : 'night', t); ENV.cloud.value = t * 0.6; ENV.sunDir.value.set(-Math.cos(cyc * 6.28), Math.sin(cyc * 6.28) * 0.8 + 0.1, 0.5).normalize(); } };
  const B = { cam: salonCam(t, u, { a: 0.35, r: 1.6, h: 0.05, fov: vfov(30, 1.15) }), before: () => { applyMood(MOOD.studio, t); Wd.studio.set('#f4d6cf', '#c99a94'); } };
  return { split: [A, B] };
}, 'split: days pass | the salon');
// estimated wait time: nobody knows
shot(77.76, 79.9, (t, u) => {
  applyMood(MOOD.night, t); towerWindows('night', t);
  const roll = t < wordT(17, 'time') ? Math.floor(t * 14) : -1; const R = rng(roll + 99); const d = () => String(Math.floor(R() * 10));
  Wd.tower.led.set(roll >= 0 ? `EST. WAIT ${d()}${d()}:${d()}${d()}` : 'EST. WAIT ??:??', { color: 0xff9a3a, gain: 2.8 });
  const c = V3(0, 7.6, TOWER.zf); const p = c.clone().add(V3(lerp(-5, -3.5, u), lerp(-2.2, -1.6, u), lerp(24, 21, u))); return { cam: [p, c.clone().add(V3(0.8, 0, 0)), vfov(44)] };
}, 'LED: EST. WAIT ??:??');
shot(79.9, 81.84, (t, u) => {
  applyMood(MOOD.night, t); towerWindows('night', t); bot.root.visible = true; bot.root.scale.setScalar(0.9); bot.pose(botHold(t)); bot.setEye('wave', t, { amp: 0.6 }); bot.updateCord();
  const k = sstep(80.0, 81.6, t); webs[0].visible = true; webs[0].scale.setScalar(Math.max(0.01, k)); webs[0].material.opacity = 0.8 * k;
  const c = WEB0.c; const p = c.clone().add(V3(lerp(0.75, 0.6, u), lerp(0.08, 0.12, u), lerp(0.85, 0.7, u))); return { cam: [p, c.clone().add(V3(-0.15, 0, 0)), vfov(34)] };
}, 'cobwebs begin');
// she walks out of the plaza toward the street
function herWalk(t, t0, from, dir, o = {}) {
  const tw = Math.max(0, t - t0); const pos = from.clone().addScaledVector(dir, tw * WALK.speed); const ph = tw * WALK.cad * Math.PI;
  if (o.look === 'foils') { her.setHair('foils', 'blonde'); her.setShades(false); her.cape.visible = true; }
  const sw = Math.sin(ph); her.root.visible = true;
  her.pose({ x: pos.x, z: pos.z, turn: Math.atan2(dir.x, dir.z), seat: 0, lean: 0.04, headYaw: o.yaw ?? 0, headPitch: -0.05, walk: ph, stride: 1, bob: Math.abs(Math.cos(ph)) * 0.012,
    hands: o.hands || [[-0.2, -0.06 + 0.06 * sw, 0.06 + 0.16 * sw], [0.2, -0.06 - 0.06 * sw, 0.06 - 0.16 * sw]], hipRoll: 0.04 * sw });
  return pos;
}
shot(81.84, 85.56, (t, u) => {
  applyMood(MOOD.day, t); towerWindows('day', t);
  const pos = herWalk(t, 81.6, V3(-6, 0, 20.5), V3(1, 0, 0), { look: 'foils', yaw: -0.15 }); bagCarry(t);
  bot.root.visible = true; bot.root.scale.setScalar(0.9); bot.pose(botHold(t)); bot.setEye('wave', t); bot.updateCord();
  const p = V3(pos.x + 1.0, 1.2, 23.6); return { cam: [p, V3(pos.x + 0.35, 1.15, 20.5), vfov(36)] };
}, 'she walks out of the plaza');
function bagCarry(t) { const hr = her.handWorld(1); kioskBox.visible = true; kioskBox.scale.setScalar(1.3); kioskBox.position.copy(hr).add(V3(0, -0.2, 0)); kioskBox.rotation.set(0, 0.3, 0); }
// it's pressing zero (a giant 0 slams down), it's taking notes
shot(85.56, 87.62, (t, u) => {
  applyMood(MOOD.day, t); towerWindows('day', t); bot.root.visible = true; bot.root.scale.setScalar(0.9); bot.pose(botHold(t, { headYaw: -0.35 * sstep(T.zero, T.zero + 0.3, t) })); bot.setEye(t > T.zero + 0.1 ? 'happy' : 'wave', t); bot.updateCord();
  giant0.visible = true; const d = t - T.zero; const y = d < 0 ? 24 * Math.pow(clamp(-d / 0.55), 2) : 0; const [sx, sy] = squash(t, T.zero, 0.35, 0.12);
  giant0.position.set(2.2, y, 1.0); giant0.scale.set(sx, sy, sx); giant0.rotation.y = -0.3; puffAt(V3(2.2, 0.05, 1.0), t, T.zero);
  const p = V3(lerp(-1.6, -1.9, u), lerp(1.1, 1.3, u), 5.6).add(shake(t, T.zero, 0.06, 0.2)); return { cam: [p, V3(1.1, 0.9, 0.2), vfov(44)] };
}, 'the giant 0');
shot(87.62, 89.6, (t, u) => {
  applyMood(MOOD.day, t); towerWindows('day', t); bot.root.visible = true; bot.root.scale.setScalar(0.9); bot.pose(botHold(t, { headPitch: 0.3 })); bot.setEye('notes', t, { k: clamp((t - 87.8) / 1.6) }); bot.updateCord();
  giant0.visible = true; giant0.position.set(2.2, 0, 1.0); giant0.scale.setScalar(1);
  const hp = bot.headWorld(); const p = hp.clone().add(V3(lerp(0.75, 0.6, u), 0.0, lerp(1.0, 0.85, u))); return { cam: [p, hp.clone().add(V3(0, -0.1, 0)), vfov(30)] };
}, 'taking notes');
// I'm on my second egg roll
shot(89.6, 92.56, (t, u) => {
  studio('#ffd84a', '#f0a51c'); roll.visible = true; const bounce = Math.abs(Math.sin(Math.PI * clamp((t - wordT(20, 'egg')) / 0.35))) * (t > wordT(20, 'egg') && t < wordT(20, 'egg') + 0.35 ? 1 : 0);
  roll.position.copy(STUDIO).add(V3(0, 0.6 + 0.05 * bounce, 0)); roll.rotation.set(0.35, 0.35 + 0.25 * Math.sin(t * 0.8), 0.15 + 0.05 * Math.sin(t * 3)); roll.scale.setScalar(2.4);
  two.visible = t >= wordT(20, 'second') - 0.05; if (two.visible) { const k = easeOutBack(clamp((t - wordT(20, 'second')) / 0.3)); two.scale.setScalar(Math.max(0.01, k)); two.position.copy(STUDIO).add(V3(0.2, 0.75, 0.08)); two.rotation.z = -0.15; }
  const p = STUDIO.clone().add(V3(lerp(-0.05, 0.05, u), lerp(0.72, 0.7, u), lerp(0.62, 0.55, u))); return { cam: [p, STUDIO.clone().add(V3(0.06, 0.64, 0)), VERT ? 52 : 34] };
}, 'second egg roll');
// please hold, please hold: a tiny robot under a huge sky
shot(92.56, 97.0, (t, u) => {
  applyMood(MOOD.dusk, t); towerWindows('night', t); ENV.sunDir.value.set(-0.9, 0.06, -0.4).normalize(); ENV.cloud.value = t * 0.02;
  bot.root.visible = true; bot.root.scale.setScalar(0.9); bot.pose(botHold(t)); bot.setEye('wave', t); bot.updateCord();
  const p = V3(lerp(-11, -10, u), 0.2, lerp(-14, -12.5, u)); const dir = V3(BOT0.x, 0, 0).sub(p).setY(0).normalize(); return { cam: [p, p.clone().addScaledVector(dir, 30).add(V3(0, lerp(14, 15.5, u), 0)), vfov(62)] };
}, 'tiny robot, huge sky');
// I don't wait anymore: the glow-up. Under the dryer in foils; the hood swings up ("I"), she stands and the cape whips off
// ("don't"), the foils burst off and honey-blonde waves fall ("wait"), the wayfarers drop onto her nose ("anymore"), a
// hand on the hip, and she walks out.
function capeFly(k) { const c = her.cape; c.position.set(-1.9 * k, 0.5 * k + 0.9 * k * k, 0.2 * k); c.rotation.set(-0.4 * k, -0.6 * k, 1.9 * k); c.scale.set(1, 1, 0.85); }
shot(97.0, T_V2(), (t, u) => {
  Wd.studio.set('#f8d5dd', '#d895a6'); applyMood(MOOD.studio, t); salonG.visible = true; salonG.position.copy(STUDIO);
  const [tI, tDont, tWait, tAny] = LN[22].wt;
  hoodLift(easeOutBack(clamp((t - (tI - 0.14)) / 0.34), 1.3));
  // the cape: on, then whipped off to the side
  const fly = clamp((t - (tDont - 0.02)) / 0.3); her.cape.visible = fly < 1; if (fly > 0) capeFly(easeIn(fly) * 1.4);
  // hair: foils until "wait", then the burst and the waves falling in, with a flip
  const db = t - tWait;
  if (db < 0) { her.setHair('foils', 'blonde'); her.hair.burstFoils(-1); } else { her.setHair('waves', 'blonde'); her.hair.foilsFly(db);
    const gu = clamp((db - 0.03) / 0.6); HAIRO = { grow: clamp(1 - Math.exp(-5.5 * gu) * Math.cos(gu * 8.5), 0, 1.12), swing: 0.9 * Math.exp(-db / 0.4) * Math.sin(db * 11) }; }
  // the wayfarers drop in from above, a small bounce, a glint
  const da = t - (tAny - 0.3); her.setShades(da < 0 ? false : (da < 0.3 ? 1.1 * (1 - easeIn(da / 0.3)) : -0.05 * Math.exp(-(da - 0.3) / 0.08) * Math.sin((da - 0.3) * 40)));
  // her: seated, up on "don't", a pose on "anymore", then she walks out toward camera left
  const st = easeIO(clamp((t - (tDont - 0.1)) / 0.5)); const pose = easeOutBack(clamp((t - (tAny - 0.05)) / 0.3), 1.6);
  const tw = Math.max(0, t - 100.35); const walk = tw * WALK.cad * Math.PI; const wk = sstep(0, 0.35, tw);
  const base = V3(STUDIO.x, 0.07 * (1 - st), STUDIO.z + 0.04 + 0.22 * st); const dir = V3(1, 0, 0.22).normalize(); base.addScaledVector(dir, tw * WALK.speed * 1.05 * wk);
  const sw = Math.sin(walk);
  const hands = st < 1 ? [[lerp(-0.25, -0.24, st), lerp(0.18, -0.06, st), lerp(0.22, 0.06, st)], [lerp(0.25, 0.24, st), lerp(0.18, -0.06, st), lerp(0.22, 0.06, st)]]
    : [[lerp(-0.24, -0.16, pose), lerp(-0.06, 0.76, pose), lerp(0.06, 0.04, pose)], [lerp(0.24, 0.21, pose), lerp(-0.06, -0.01, pose), lerp(0.06, -0.05, pose)]];
  if (wk > 0) { hands[0] = mixV(hands[0], [-0.2, -0.06 + 0.06 * sw, 0.06 + 0.16 * sw], wk); hands[1] = mixV(hands[1], [0.2, -0.06 - 0.06 * sw, 0.06 - 0.16 * sw], wk); }
  her.root.visible = true; her.setFace(t > tAny + 0.12 ? 1 : 0, clamp((t - tAny - 0.1) / 0.15) * (1 - sstep(100.1, 100.4, t)));
  her.pose({ x: base.x, y: base.y, z: base.z, turn: lerp(0, Math.atan2(dir.x, dir.z), wk), seat: 1 - st, lean: lerp(-0.08, 0.02, st), roll: 0.05 * pose * (1 - wk), hipRoll: -0.06 * pose * (1 - wk) + 0.04 * sw * wk,
    headPitch: lerp(-0.12, -0.08, st), headYaw: lerp(0.1, 0.05, st) + 0.25 * pose * (1 - wk), headRoll: 0.08 * pose * (1 - wk), elbowOut: 0.6 * pose * (1 - wk),
    hands, kneeOut: 0.03, walk, stride: wk, bob: Math.abs(Math.cos(walk)) * 0.012 * wk });
  // glitter where the foils were, and a little flash on "anymore"
  if (db >= 0 && db < 1.4) { const hp = her.headWorld(); const pa = sparks.geometry.attributes.position; const R = rng(23); sparks.visible = true;
    for (let i = 0; i < pa.count; i++) { const d = V3(R() - 0.5, R() - 0.2, R() - 0.5).normalize(); const sp = 0.3 + R() * 1.4; pa.setXYZ(i, hp.x + d.x * sp * db, hp.y + 0.15 + d.y * sp * db - 0.8 * db * db, hp.z + d.z * sp * db); }
    pa.needsUpdate = true; sparks.material.color.setRGB(2.2, 1.9, 1.4); sparks.material.size = 0.02; sparks.material.opacity = 1 - clamp(db / 1.4); }
  finish.uniforms.uFlash.value = 0.22 * Math.exp(-Math.max(0, t - tAny) / 0.12) * (t >= tAny ? 1 : 0); finish.uniforms.uFlashCol.value.setRGB(1, 0.92, 0.85);
  // camera: frontal, a little low, headroom for the words; it rises as she stands, pushes in on "anymore", then pans with her as she struts out
  const k = easeIO(clamp((t - (tDont - 0.1)) / 0.7)), k2 = easeIO(clamp((t - tAny) / 1.5)), k3 = easeIO(clamp((t - 100.35) / 1.4));
  const hw = her.headWorld();
  const tgt = V3(lerp(STUDIO.x, hw.x, 0.35 * k3), lerp(1.2, 1.42, k) + 0.06 * k2 * (1 - k3) - 0.25 * k3, STUDIO.z + 0.15);
  const p = STUDIO.clone().add(V3(0.32 - 0.12 * k2 + 0.4 * k3, lerp(1.15, 1.32, k) - 0.15 * k3, lerp(2.55, 2.35, k) - 0.45 * k2 * (1 - k3) + 1.0 * k3));
  return { cam: [p, tgt, VERT ? lerp(56, 50, k2) : lerp(36, 32, k2)] };
}, "I don't wait anymore: the glow-up");
function T_V2() { return 102.10; }

// --- VERSE 2
shot(102.10, 103.95, (t, u) => {
  applyMood(MOOD.day, t); towerWindows('day', t); bot.root.visible = true; bot.root.scale.setScalar(0.9); bot.pose(botHold(t)); bot.setEye('wave', t); bot.updateCord();
  webs[0].visible = true; webs[0].scale.setScalar(1);
  const p = V3(lerp(-6.5, -5.5, u), lerp(2.6, 2.2, u), lerp(8.5, 7.5, u)); return { cam: [p, V3(0.3, 0.9, 0), vfov(36)] };
}, 'one little bot');
shot(103.95, 107.12, (t, u) => {
  applyMood(MOOD.day, t); towerWindows('day', t); bot.root.visible = true; bot.root.scale.setScalar(0.9); bot.pose(botHold(t, { headRoll: -0.1 + 0.08 * Math.sin(t * Math.PI * 2) })); bot.setEye('wave', t); bot.updateCord();
  webs[0].visible = true;
  const hp = bot.headWorld(); const p = hp.clone().add(V3(lerp(-0.5, -0.35, u), -0.05, lerp(0.95, 0.85, u))); return { cam: [p, hp.clone().add(V3(0.05, -0.12, 0)), vfov(30)] };
}, 'on a customer line');
shot(107.12, 110.96, (t, u) => {          // pressing the buttons, doing just fine
  studio('#58d6e3', '#1f7f95'); keypad.root.visible = true; keypad.root.position.copy(STUDIO).add(V3(0, 0.6, 0)); keypad.root.rotation.set(-0.5, 0, 0);
  const seq = ['5', '1', '9', '3', '2', '8', '6', '4']; const bs = BEATS.filter((b) => b >= 107.12 && b < 110.96).filter((_, i) => i % 1 === 0);
  let cur = null; for (let i = 0; i < bs.length; i++) { const d = seq[i % seq.length]; const tt = bs[i]; const uu = t - tt; keypad.set(d, uu >= 0 && uu < 0.2 ? Math.sin(Math.PI * uu / 0.2) : 0, uu >= 0 && uu < 0.45 ? 1 : 0); if (t >= tt - 0.25) cur = { d, tt }; }
  botHand.visible = true; if (cur) { const k = keypad.key(cur.d); const tgt = keypad.root.localToWorld(V3(k.x, k.y, 0.035)); const lift = 0.07 * (1 - hit(t, cur.tt, 0.22)); botHand.position.copy(tgt).add(V3(0.01, -0.05 + lift * 0.2, lift + 0.01)); }
  botHand.rotation.set(-1.25, 0.35, 0.25);
  const p = STUDIO.clone().add(V3(lerp(0.3, 0.24, u), lerp(1.15, 1.1, u), lerp(0.78, 0.72, u))); return { cam: [p, STUDIO.clone().add(V3(0.02, 0.58, 0.02)), VERT ? 58 : 40] };
}, 'pressing buttons');
const XFER = [[6, 26, 'BILLING', 110.96], [15, 22, 'SUPPORT', 112.08], [9, 17, 'BILLING', 113.04], [17, 12, 'BILLING', 114.16]];
shot(110.96, 114.80, (t, u) => {          // transferred to billing, transferred again: up the tower, window to window
  applyMood(MOOD.day, t); towerWindows('day', t);
  let i = 0; for (let k = 0; k < XFER.length; k++) if (t >= XFER[k][3]) i = k;
  XFER.forEach(([c, r, txt], k) => { const sg = signs[k]; sg.visible = true; const wc = winCenter(c, r); sg.position.set(wc.x, wc.y + 0.86, TOWER.zf + 0.1); sg.scale.setScalar(0.9); });
  Wd.tower.setAll((c, r) => XFER.some(([cc, rr]) => cc === c && rr === r) ? [1.0, 0.95, 0.85] : [0.16, 0.19, 0.24], 'xfer');
  const [c, r, , t0] = XFER[i]; const wc = winCenter(c, r); const pop = easeOutBack(clamp((t - t0) / 0.3));
  bot.root.visible = true; bot.root.scale.setScalar(0.62 * pop); bot.pose({ x: wc.x, y: wc.y - 0.56, z: TOWER.zf - 0.35, seat: 0, lean: 0.05, headPitch: 0.1, hands: [[-0.15, 0.64, 0.07], [0.2, 0.0, 0.15]] }); bot.setEye('wave', t); bot.handset.visible = true; bot.cord.mesh.visible = false;
  if (i > 0) { const [pc, pr] = XFER[i - 1]; const a = winCenter(pc, pr), b2 = wc; const zz = clamp((t - t0) / 0.25); if (zz < 1) { setTrail(new THREE.LineCurve3(V3(a.x, a.y - 0.3, TOWER.zf + 0.4), V3(b2.x, b2.y - 0.3, TOWER.zf + 0.4)), zz, 0.6, 1 - zz, 0.08); } }
  const prev = i > 0 ? winCenter(XFER[i - 1][0], XFER[i - 1][1]) : wc.clone().add(V3(-2, -1.5, 0)); const cp = prev.lerp(wc, easeIO(clamp((t - t0) / 0.45)));
  return { cam: [V3(cp.x + 1.3, cp.y + 0.2, TOWER.zf + 5.2), V3(cp.x, cp.y + 0.15, TOWER.zf), vfov(44)] };
}, 'transferred again');
shot(114.80, 118.45, (t, u) => {          // still more polite than I've ever been: a little bow
  applyMood(MOOD.day, t); towerWindows('day', t); bot.root.visible = true; bot.root.scale.setScalar(0.9);
  const bow = hit(t, 116.2, 0.45) || (t > 116.2 ? 1 - sstep(116.4, 117.4, t) : 0);
  bot.pose(botHold(t, { lean: 0.2 + 0.45 * bow, headPitch: 0.4 + 0.3 * bow })); bot.setEye('text', t, { text: 'THANK YOU SO MUCH :)', scroll: (t - 114.8) * 70 }); bot.updateCord();
  webs[0].visible = true;
  const hp = bot.headWorld(); const p = V3(BOT0.x + lerp(1.0, 0.8, u), 0.95, lerp(2.1, 1.9, u)); return { cam: [p, hp.clone().add(V3(0, -0.25, 0)), vfov(36)] };
}, 'thank you so much');
// meanwhile I'm eating, I'm pouring a drink (the salon)
shot(118.45, 122.40, (t, u) => {
  Wd.studio.set('#f4d6cf', '#c99a94'); applyMood(MOOD.studio, t);
  const pourK = sstep(wordT(27, 'pouring') - 0.3, wordT(27, 'pouring'), t) * (1 - sstep(122.1, 122.4, t));
  herSalon(t, { eat: Math.max(hit(t, wordT(27, 'eating') - 0.1, 0.3), hit(t, 120.3, 0.3)) * (1 - pourK), pose: pourK > 0 ? { hands: [[-0.08, 0.18, 0.3], [0.22, 0.28, 0.3]] } : {} });
  glassF.visible = true; glassF.position.copy(salonG.userData.table.getWorldPosition(V3())).add(V3(-0.05, 0.015, 0.05)); glassF.userData.wine.scale.y = clamp(0.2 + (t - wordT(27, 'pouring')) * 0.9, 0.2, 1);
  const bottle = drink.userData.bottle; drink.visible = pourK > 0.01; if (drink.visible) { drink.userData.glass.visible = drink.userData.liquid.visible = false; const hr = her.handWorld(1); drink.position.copy(hr); bottle.position.set(0, 0, 0); bottle.rotation.set(0, 0, 1.9 * pourK); bottle.scale.setScalar(0.9);
    const st = drink.userData.stream; st.visible = pourK > 0.6; st.scale.set(1, 0.18, 1); st.position.set(0.12, -0.1, 0); }
  return { cam: salonCam(t, u, { a: lerp(0.25, 0.45, u), r: lerp(1.55, 1.35, u), h: 0.02, fov: vfov(34) }) };
}, 'salon: eating, pouring');
// the saxophone's somebody else's problem
shot(122.40, 126.32, (t, u) => {
  Wd.studio.set('#f4d6cf', '#c99a94'); applyMood(MOOD.studio, t);
  const point = sstep(wordT(28, 'problem') - 0.4, wordT(28, 'problem'), t);
  herSalon(t, { yaw: lerp(0.1, 0.55, point), pose: { hands: [[-0.08, 0.18, 0.3], [lerp(0.1, 0.32, point), lerp(0.2, 0.42, point), lerp(0.3, 0.42, point)]] } });
  const turnT = wordT(28, 'problem') + 0.1; const hc = her.headWorld(); const out = hc.clone().add(V3(2.5, 0.6, 1.2));
  saxN.root.visible = true; saxN.set((i) => { const st = 122.3 + i * 0.12; const d = t - st; if (d < 0) return null; const toward = clamp(d / 2.2);
    let pp = out.clone().lerp(hc.clone().add(V3(0.35, 0.15 + 0.1 * Math.sin(i), 0.3)), easeOut(toward)); if (t > turnT) { const k = easeIn(clamp((t - turnT - i * 0.03) / 1.1)); pp = pp.lerp(out.clone().add(V3(1, 1.2, -1)), k); }
    return { p: pp.add(V3(Math.sin(d * 4 + i) * 0.05, Math.cos(d * 3 + i) * 0.05, 0)), scale: 0.09, rot: Math.sin(d * 5 + i) * 0.4 }; });
  return { cam: salonCam(t, u, { a: lerp(0.62, 0.5, u), r: 2.0, h: 0.1, fov: vfov(40) }) };
}, 'salon: the sax U-turns');
// it made my request, wrote down the reply: the newsstand
shot(126.32, 130.32, (t, u) => {
  applyMood(MOOD.day, t); towerWindows('day', t); newsS.visible = true;
  const np = newsS.position; const p = V3(np.x + 3.2, 1.55, np.z + lerp(-1.6, 1.6, easeIO(u))); return { cam: [p, V3(np.x + 0.9, 1.35, np.z + lerp(-1.0, 1.0, easeIO(u))), vfov(36)] };
}, 'newsstand');
// sent me a summary, concise and dry
shot(130.32, 134.40, (t, u) => {
  applyMood(MOOD.studio, t); Wd.studio.set('#f4d6cf', '#c99a94'); salonG.visible = true; salonG.position.copy(STUDIO);
  hoodLift(1);
  const v = povPhone(t, { pose: { x: STUDIO.x, y: 0.07, z: STUDIO.z + 0.04, lean: 0.05, headPitch: 0.45 } });
  phone.draw({ screen: 'summary', clock: '4:07', k: clamp((t - wordT(30, 'summary') + 0.2) / 0.5), k2: clamp((t - wordT(30, 'concise')) / 1.8) }, 'sum' + Math.floor(t * 30));
  return { cam: [v.p, v.lk, VERT ? 42 : 28] };
}, 'the summary');
shot(134.40, 135.84, (t, u) => {
  applyMood(MOOD.night, t); towerWindows('night', t); bot.root.visible = true; bot.root.scale.setScalar(0.9); bot.pose(botHold(t, { lean: 0.12, headPitch: 0.25 })); bot.setEye('eyes', t); bot.updateCord(); webs[0].visible = true;
  const sp = bot.slotWorld(); const p = sp.clone().add(V3(0.25, 0.05, lerp(0.75, 0.6, u))); return { cam: [p, sp, vfov(32)] };
}, 'the slot');

// --- BRIDGE: the receipt prints, one line per spoken line
const RLINE = [136.4, 140.0, 142.96, 146.24];
function receiptAt(t) {           // printed length (px of the receipt canvas) on a schedule: each row lands as it is spoken
  const rows = RLINE.filter((x) => t >= x).length;
  const keys = [[135.9, 0], [136.4, 470], [139.6, 470], [140.0, 620], [142.5, 620], [142.96, 770], [145.8, 770], [146.24, 1000], [146.3, 1000], [146.95, 8000]];
  let px = 0; for (let i = 1; i < keys.length; i++) { const [t0, a] = keys[i - 1], [t1, b] = keys[i]; if (t <= t1) { px = lerp(a, b, b - a > 2000 ? (t - t0) / (t1 - t0) : easeOut(clamp((t - t0) / Math.min(0.35, t1 - t0)))); break; } px = b; }
  return { rows, L: receipt.lenFor(px) };
}
function botReceipt(t, o = {}) {
  applyMood(MOOD.night, t); towerWindows('night', t); bot.root.visible = true; bot.root.scale.setScalar(0.9); bot.pose(botHold(t, { lean: 0.08, headPitch: 0.2, hands: [[-0.15, 0.64, 0.07], [0.3, 0.02, 0.06]], ...o.pose })); bot.setEye(o.eye || 'eyes', t, o.eyeO || {}); bot.updateCord(); webs[0].visible = true;
  const { rows, L } = receiptAt(t); const strike = clamp((t - (T.five - 0.05)) / 0.3); const st = t >= T.charge5 ? 1 : 0;
  receipt.draw({ rows, strike: t >= T.five - 0.05 ? strike : 0, stamp: st }); receipt.mesh.visible = true;
  bot.root.updateMatrixWorld(true); const q = bot.torso.getWorldQuaternion(new THREE.Quaternion()); const fwd = V3(0, -0.15, 1).applyQuaternion(q).normalize(); const side = V3(1, 0, 0).applyQuaternion(q);
  receipt.shape(bot.slotWorld(), fwd, side, L, 0.0, (t > T.charge5 ? Math.exp(-(t - T.charge5) / 0.25) : 0) + (t > 146.3 && t < 146.95 ? 0.6 : 0), t);
  return { rows, L };
}
shot(135.84, 139.12, (t, u) => { botReceipt(t); const sp = bot.slotWorld(); const p = sp.clone().add(V3(0.04, -0.04, lerp(0.5, 0.42, u))); return { cam: [p, sp.clone().add(V3(0, -0.09, 0.06)), VERT ? 46 : 32] }; }, 'receipt: call duration');
shot(139.12, 141.84, (t, u) => { botReceipt(t); const sp = bot.slotWorld(); const p = sp.clone().add(V3(-0.22, -0.02, lerp(0.46, 0.4, u))); return { cam: [p, sp.clone().add(V3(0, -0.12, 0.07)), VERT ? 46 : 32] }; }, 'receipt: representatives');
shot(141.84, 144.16, (t, u) => { botReceipt(t); const sp = bot.slotWorld(); const p = sp.clone().add(V3(0.2, -0.08, 0.5)); return { cam: [p, sp.clone().add(V3(0, -0.15, 0.08)), VERT ? 48 : 34] }; }, 'receipt: transfers');
shot(144.16, 146.9, (t, u) => { botReceipt(t); const sp = bot.slotWorld(); const k = easeIO(u); const p = sp.clone().add(V3(lerp(0.05, 0.9, k), lerp(-0.05, 0.35, k), lerp(0.5, 1.9, k))); return { cam: [p, sp.clone().add(V3(0, lerp(-0.12, -0.3, k), lerp(0.08, 0.3, k))), VERT ? 48 : 34] }; }, 'receipt: explained');
shot(146.9, 148.16, (t, u) => { botReceipt(t, { eye: t > 147.45 && t < 147.6 ? 'blink' : 'eyes' }); return { cam: [V3(BOT0.x + 0.15, 0.95, 2.3), V3(BOT0.x, 0.75, 0), vfov(32)] }; }, 'the pause');
shot(148.16, T.drop || 149.95, (t, u) => {
  const { L } = botReceipt(t); const rowS = L - receipt.lenFor(RECEIPT_PX.row0 + 1.5 * RECEIPT_PX.rowH); const rp = receipt.pointAt(rowS); const rp2 = receipt.pointAt(rowS + 0.05); const dir = rp2.clone().sub(rp).normalize();
  stamp.visible = t > T.charge5 - 0.45 && t < T.charge5 + 0.3;
  if (stamp.visible) { const d = t - T.charge5; const k = d < 0 ? Math.pow(-d / 0.45, 0.7) : easeOut(clamp((d - 0.06) / 0.2)); const sideV = V3(-dir.z, 0, dir.x); stamp.position.copy(rp).addScaledVector(sideV, 0.5 * k).add(V3(0, 0.005 + 0.22 * k, 0)); stamp.rotation.set(0, Math.atan2(dir.x, dir.z) + 0.14, -0.6 * k); stamp.scale.setScalar(1.1); }
  const sh = shake(t, T.charge5, 0.01, 0.15); const h = lerp(0.42, 0.3, easeIn(u)); const p = rp.clone().add(dir.clone().multiplyScalar(-0.05)).add(V3(0, h, 0)).add(sh);
  return { cam: [p, rp.clone().add(dir.clone().multiplyScalar(0.01)), VERT ? 50 : 36, Math.PI] };
}, '$5.00');
// --- FINAL CHORUS: the city reboots in neon
function neonOn(t) { const k = sstep(T.final, T.final + 0.6, t); const m = mixMood(MOOD.night, MOOD.neon, k); applyMood(m, t); towerWindows('night', t); ENV.dance.value = k; return k; }
function botDance(t, o = {}) { const b = BEATS.find((x) => x > t - 0.5) ?? t; const ph = (t * 2.0) * Math.PI; const up = Math.abs(Math.sin(ph));
  return { x: o.x ?? BOT0.x, z: o.z ?? BOT0.z, turn: o.turn ?? 0, seat: o.seat ?? 0, lean: 0.05, bob: up * 0.05, headRoll: Math.sin(ph) * 0.2, headPitch: -0.05,
    hands: [[-0.15, 0.64, 0.07], [0.25, 0.35 + 0.25 * up, 0.1 + 0.1 * Math.sin(ph)]], walk: o.walk ?? 0, stride: o.stride ?? 0, hipRoll: Math.sin(ph) * 0.08 }; }
shot(T.final || 149.95, 153.36, (t, u) => {
  const k = neonOn(t); if (t < T.final + 0.3) finish.uniforms.uFlash.value = 0.6 * (1 - (t - T.final) / 0.3);
  Wd.tower.led.set('PLEASE HOLD', { color: 0x5ff4ff, gain: 3 + 2 * beatPulse(t) });
  bot.root.visible = true; bot.root.scale.setScalar(0.9); bot.pose(t < 151.0 ? botHold(t) : botDance(t)); bot.setEye('happy', t); bot.updateCord();
  const a = lerp(-0.4, 0.4, easeIO(u)); const p = V3(Math.sin(a) * 14, lerp(3, 7, easeIO(u)), Math.cos(a) * 14 + 4); return { cam: [p, V3(0, lerp(3, 8, u), -10), vfov(50)] };
}, 'neon reboot');
shot(153.36, 155.5, (t, u) => {
  neonOn(t); Wd.tower.led.set('YOUR CALL IS IMPORTANT TO US', { color: 0xff4fd8, gain: 3.2, scroll: (t - 153.0) * 26 - 30 });
  const c = V3(0, 7.6, TOWER.zf); return { cam: [c.clone().add(V3(lerp(-7, -5, u), -0.5, 10)), c.clone().add(V3(1, 0, 0)), vfov(40)] };
}, 'LED: your call is important');
shot(155.5, T.years || 157.52, (t, u) => {
  neonOn(t); bot.root.visible = true; bot.root.scale.setScalar(0.9); bot.pose(botDance(t, { seat: 1 })); bot.setEye('happy', t); bot.updateCord();
  return { cam: [V3(BOT0.x + lerp(1.4, 1.0, u), 0.7, 2.4), V3(BOT0.x, 0.9, 0), vfov(38)] };
}, 'the robot dances on the bench');
// two thousand years of human progress
const HIST = [['tablet', '26 AD'], ['key', '1844'], ['rotary', '1965'], ['bot', '2026']];
let plaque = null; function plaqueTex(yr) { if (!plaque) return; const tex = plaque.material.map; tex.userData.redraw(yr, (c, w, h) => { c.fillStyle = '#c9a24a'; c.fillRect(0, 0, w, h); c.fillStyle = '#2b220f'; c.font = `60px ${FONT.black}`; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText(yr, w / 2, h / 2 + 3); }); }
const histT = () => { const t0 = T.years, t1 = LN[39].s; const d = (t1 - t0) / 4; return [0, 1, 2, 3].map((i) => t0 + i * d); };
for (let i = 0; i < 4; i++) shot(157.52 + i * 0.86, 157.52 + (i + 1) * 0.86, (t, u) => {
  Wd.studio.set('#1a1d26', '#07080b'); applyMood(MOOD.studio, t); hist.ped.visible = true; hist.ped.position.copy(STUDIO);
  const [k, yr] = HIST[i]; plaque.visible = true; plaque.position.copy(STUDIO).add(V3(0, 0.86, 0.302)); plaqueTex(yr);
  const top = STUDIO.clone().add(V3(0, 1.0, 0));
  if (k === 'bot') { bot.root.visible = true; bot.root.scale.setScalar(0.42); bot.pose({ ...botHold(t), x: top.x, y: top.y, z: top.z, seat: 0 }); bot.setEye('wave', t); bot.updateCord(); }
  else { const o = hist[k === 'tablet' ? 'tablet' : (k === 'key' ? 'key' : 'rotary')]; o.visible = true; o.position.copy(top); o.rotation.y = -0.3 + u * 0.3; o.scale.setScalar(k === 'key' ? 1.4 : 1.15); if (k === 'key') o.userData.lever.rotation.z = Math.sin(t * 30) > 0.3 ? -0.05 : 0; }
  const ty = k === 'bot' ? 0.32 : (k === 'tablet' ? 0.26 : 0.1); const p = top.clone().add(V3(lerp(0.55, 0.45, u), 0.2 + ty * 0.5, lerp(1.45, 1.3, u) + (k === 'bot' ? 0.35 : 0))); return { cam: [p, top.clone().add(V3(0, ty, 0)), VERT ? 52 : 36] };
}, 'history ' + i);
shot(160.96, 165.44, (t, u) => {          // nobody wants to talk to Comcast: a lone payphone rings
  neonOn(t); payP.visible = true; const ring = Math.sin(t * 40) * 0.04 * (t < T.comcast + 0.6 ? 1 : 0.2); payP.rotation.z = ring; payP.position.set(0, 0, 6);
  const back = sstep(T.comcast - 0.05, T.comcast + 0.25, t);
  pigs.forEach((pg, i) => { pg.visible = true; const a = i / pigs.length * Math.PI * 2 + 0.3; const r = 1.2 + 0.7 * back; pg.position.set(Math.cos(a) * r, 0.12 * Math.sin(Math.PI * clamp((t - T.comcast) / 0.25)) * (t > T.comcast ? 1 : 0), 6 + Math.sin(a) * r); pg.rotation.y = -a + Math.PI / 2 - Math.PI / 2; pg.lookAt(0, 0.1, 6); });
  ringWave(t, V3(0, 1.6, 6.2));
  return { cam: [V3(lerp(2.8, 2.3, u), 0.6, lerp(10.5, 9.6, u)).add(shake(t, T.comcast, 0.03)), V3(0, 0.9, 6), vfov(40)] };
}, 'the payphone rings');
function ringWave(t, c) { const rw = ringsM; rw.visible = true; rw.position.copy(c); rw.children.forEach((m, i) => { const k = ((t * 1.6 + i / 3) % 1); m.scale.setScalar(0.2 + k * 1.6); m.material.opacity = 0.8 * (1 - k); }); }
shot(165.44, T.robots || 169.28, (t, u) => {   // the whole tower as one giant screen
  neonOn(t); const tw = Wd.tower; tw.body.material.uniforms.uScreenAmt.value = sstep(166.24, 166.4, t); tw.body.material.uniforms.uScreenGain.value = 1.5 + 0.8 * beatPulse(t);
  screenWords(t, ['PLEASE', 'HOLD'], [LN[40].wt[0], LN[40].wt[1]], ['#ff4fd8', '#5ff4ff']);
  if (t > 166.24 && t < 166.5) finish.uniforms.uFlash.value = 0.5 * (1 - (t - 166.24) / 0.26);
  const p = V3(lerp(-10, -7, u), lerp(1.0, 1.6, u), lerp(14, 11, u)); return { cam: [p, V3(0, lerp(22, 26, u), TOWER.zf), vfov(62)] };
}, 'the tower is a screen');
shot(T.robots || 169.28, T.queue || 173.36, async (t, u) => {   // let the little robots run the show: the cameo, and every robot steps out
  neonOn(t); const tw = Wd.tower; tw.body.material.uniforms.uScreenAmt.value = 1; tw.body.material.uniforms.uScreenGain.value = 1.35;
  const n = Math.floor((t - T.robots) * 30); const img = await cameoFrame(n); screenDraw('cameo' + n, (g, w, h) => { g.fillStyle = '#000'; g.fillRect(0, 0, w, h); if (img && img.width) g.drawImage(img, 0, 0, w, h); });
  const hop = clamp((t - wordT(41, 'show') + 0.3) / 0.8);
  const cells = HOLD_CELLS.filter((_, i) => i % 2 === 0).slice(0, 26);
  if (hop > 0) { busts.visible = true; busts.children.forEach((bm, i) => { const [c, r] = cells[i % cells.length]; const wcp = winCenter(c, r); const k = clamp(hop * 1.4 - i * 0.012); bm.visible = k > 0 && k < 1;
      const tgt = V3(-8 + (i % 13) * 1.3, 0, 2 + Math.floor(i / 13) * 2); bm.position.copy(wcp.clone().lerp(tgt, k)); bm.position.y += Math.sin(Math.PI * k) * 6; bm.rotation.y = k * 6; }); }
  const p = V3(lerp(4, 2, u), lerp(1.4, 2.2, u), lerp(16, 13, u)); return { cam: [p, V3(0, lerp(26, 22, u), TOWER.zf), vfov(64)] };
}, 'the cameo; robots step out');
shot(T.queue || 173.36, T.better || 178.0, (t, u) => {   // they can have the phone, they can have the queue
  neonOn(t);
  const n = crowd.length; crowd.forEach((r, i) => { r.root.visible = true; r.root.scale.setScalar(0.9); const s = (i - n / 2) * 1.1 + (t - 173.36) * 0.6; const x = -6 + s, z = 3 + Math.sin(s * 0.5) * 1.2;
    const p = botDance(t + i * 0.13, { x, z, turn: Math.PI / 2 + Math.cos(s * 0.5) * 0.4, stride: 0.6, walk: (t + i * 0.2) * 3.5 }); p.hands = [[-0.15, 0.64, 0.07], [0.22, 0.25 + 0.2 * Math.abs(Math.sin((t + i * 0.25) * 6.28)), 0.2]]; r.pose(p); r.setEye('happy', t); r.cord.mesh.visible = false; });
  const p = V3(lerp(-9, -3, u), 1.3, lerp(9.5, 8.5, u)); return { cam: [p, V3(lerp(-4, 2, u), 0.9, 3), vfov(42)] };
}, 'the robot queue');
shot(T.better || 178.0, 181.35, (t, u) => {   // I've got better things to do: her, fresh waves, writing, phone face-down
  neonOn(t);
  const n = crowd.length; crowd.forEach((r, i) => { r.root.visible = true; r.root.scale.setScalar(0.9); const s = (i - n / 2) * 1.1 + (t - 173.36) * 0.6; const x = -6 + s, z = 3 + Math.sin(s * 0.5) * 1.2;
    const p = botDance(t + i * 0.13, { x, z, turn: Math.PI / 2, stride: 0.6, walk: (t + i * 0.2) * 3.5 }); r.pose(p); r.setEye('happy', t); r.cord.mesh.visible = false; });
  her.cape.visible = false; her.root.visible = true; her.setFace(1, 0); HAIRO = { gk: 0.2 };
  const bp = V3(8, 0, 4); const ry = -0.4; her.pose({ x: bp.x - Math.cos(ry) * 0.3, z: bp.z + Math.sin(ry) * 0.3 - 0.05, turn: ry, seat: 1, lean: 0.18, headPitch: 0.32, headYaw: 0.1, hands: [[-0.12, 0.15, 0.33], [0.1, 0.14 + 0.01 * Math.sin(t * 9), 0.32 + 0.01 * Math.sin(t * 7)]] });
  nb.visible = true; her.root.updateMatrixWorld(true); const hl = her.handWorld(0), hr = her.handWorld(1); nb.position.copy(hl.clone().lerp(hr, 0.5)).add(V3(0, -0.04, 0)); nb.rotation.set(-0.5, ry, 0);
  nb.userData.tex.userData.redraw('nb' + Math.floor(t * 10), (g, w, h) => drawNotebook(g, w, h, clamp((t - 178.0) / 3.2)));
  phone.root.visible = true; phone.draw({ screen: 'dark' }, 'dark'); phone.root.position.set(bp.x + Math.cos(ry) * 0.25, 0.49, bp.z - Math.sin(ry) * 0.25 - 0.05); phone.root.rotation.set(Math.PI / 2, 0, ry);
  RIM.value.set(0xffd9b0); hemi.color.set(0xffc9a0); hemi.intensity = 1.25; key.color.set(0xffe2c0); key.intensity = 1.4; key.position.set(20, 18, 30);
  const hp = her.headWorld(); const fwd = V3(Math.sin(ry), 0, Math.cos(ry)); const p = hp.clone().addScaledVector(fwd, lerp(1.25, 1.1, u)).add(V3(-0.45, -0.1, 0)); return { cam: [p, hp.clone().add(V3(0, -0.28, 0)).addScaledVector(fwd, 0.15), vfov(34)] };
}, 'better things to do');

// --- OUTRO: dawn, cobwebs, the survey, five stars, battery 1%
function botDawn(t, o = {}) { const m = moodAt(t); applyMood(m, t); towerWindows(m.day > 0.5 ? 'day' : 'night', t); bot.root.visible = true; bot.root.scale.setScalar(0.9); bot.pose(botHold(t, { headPitch: 0.42, ...o.pose })); bot.setEye(o.eye || 'wave', t, o.eyeO || {}); bot.updateCord();
  for (const w of webs) { w.visible = true; w.scale.setScalar(1); w.material.opacity = 0.75; } if (o.pigeon) { pig.visible = true; const hp = bot.headWorld(); const k = o.pigeon; pig.position.copy(hp).add(V3(0.02, 0.15 + 2.5 * (1 - k) * (1 - k), 0.1 * (1 - k))); pig.rotation.y = 0.6; pig.userData.head.rotation.x = Math.sin(t * 9) * 0.25; } }
shot(181.35, 183.44, (t, u) => { botDawn(t); Wd.tower.led.set(holdText(3600 + (t - 181) * 7)); return { cam: [V3(lerp(-4.5, -4, u), 1.4, lerp(6.5, 6, u)), V3(0.3, 1.0, 0), vfov(40)] }; }, 'dawn: thank you for calling');
shot(183.44, 186.56, (t, u) => { botDawn(t, { eye: 'survey', eyeO: { text: 'SURVEY · PAGE 1 OF 400', scroll: (t - 183.4) * 55 } });
  bot.root.updateMatrixWorld(true); const ep = V3(0, 0.152, 0.13).applyMatrix4(bot.headG.matrixWorld); const fwd = V3(0, 0, 1).applyQuaternion(bot.headG.getWorldQuaternion(new THREE.Quaternion())); return { cam: [ep.clone().addScaledVector(fwd, lerp(0.5, 0.42, u)), ep, VERT ? 44 : 30] }; }, 'survey');
shot(186.56, 188.62, (t, u) => { botDawn(t, { eye: 'stars', eyeO: { n: Math.min(5, Math.floor((t - 186.7) * 5) + 1) } });
  bot.root.updateMatrixWorld(true); const ep = V3(0, 0.152, 0.13).applyMatrix4(bot.headG.matrixWorld); const fwd = V3(0, 0, 1).applyQuaternion(bot.headG.getWorldQuaternion(new THREE.Quaternion())); return { cam: [ep.clone().addScaledVector(fwd, 0.45).add(V3(0.05, 0.03, 0)), ep, VERT ? 44 : 30] }; }, 'five stars');
shot(188.62, 191.12, (t, u) => { botDawn(t, { eye: 'battery', eyeO: { on: (t % 0.8) < 0.5 ? 1 : 0.25 } }); const hp = bot.headWorld(); return { cam: [hp.clone().add(V3(lerp(0.55, 0.45, u), -0.05, lerp(0.95, 0.8, u))), hp.clone().add(V3(0, -0.1, 0)), vfov(30)] }; }, 'battery 1%');
shot(191.12, 193.12, (t, u) => { botDawn(t, { eye: 'battery', eyeO: { on: (t % 0.8) < 0.5 ? 1 : 0.25 } }); return { cam: [V3(lerp(9, 8, u), 2.2, lerp(12, 11, u)), V3(0, 2.5, -4), vfov(46)] }; }, 'hold music: dawn');
shot(193.12, 195.1, (t, u) => { botDawn(t, { eye: 'battery', eyeO: { on: (t % 0.8) < 0.5 ? 1 : 0.25 }, pigeon: easeOut(clamp((t - 193.3) / 0.9)) }); const hp = bot.headWorld(); return { cam: [hp.clone().add(V3(-0.9, 0.1, 1.5)), hp.clone().add(V3(0, 0.05, 0)), vfov(34)] }; }, 'a pigeon');
shot(195.1, 197.1, (t, u) => { botDawn(t, { eye: 'battery', eyeO: { on: (t % 0.8) < 0.5 ? 1 : 0.25 }, pigeon: 1 }); Wd.tower.led.set(holdText(3780 + (t - 195) * 9)); return { cam: [V3(-1.0, 0.35, 6.5), V3(0, 6, -20), vfov(50)] }; }, 'the sun comes up');
shot(197.1, 199.1, (t, u) => { botDawn(t, { eye: 'battery', eyeO: { on: (t % 0.8) < 0.5 ? 1 : 0.25 }, pigeon: 1 }); saxLoop(t, 196.2, bot.headWorld().add(V3(0, 0.55, 0)), { scale: 0.8 }); return { cam: [V3(BOT0.x + 1.4, 1.0, 2.6), V3(BOT0.x, 1.2, 0), vfov(38)] }; }, 'the sax keeps looping');
shot(199.1, 201.05, (t, u) => { botDawn(t, { eye: 'battery', eyeO: { on: (t % 0.8) < 0.5 ? 1 : 0.25 }, pigeon: 1 }); const c = WEB0.c; return { cam: [c.clone().add(V3(0.55, 0.12, 0.6)), c.clone().add(V3(-0.1, 0, 0)), vfov(30)] }; }, 'cobwebs at dawn');
shot(201.05, 203.04, (t, u) => { botDawn(t, { eye: 'battery', eyeO: { on: (t % 0.8) < 0.5 ? 1 : 0.25 }, pigeon: 1 });
  bot.root.updateMatrixWorld(true); const ep = V3(0, 0.152, 0.13).applyMatrix4(bot.headG.matrixWorld); const fwd = V3(0, 0, 1).applyQuaternion(bot.headG.getWorldQuaternion(new THREE.Quaternion())); return { cam: [ep.clone().addScaledVector(fwd, lerp(0.5, 0.4, u)), ep, VERT ? 44 : 30] }; }, 'battery close');
shot(203.04, T.song || 206.28, (t, u) => { botDawn(t, { eye: 'battery', eyeO: { on: (t % 0.8) < 0.5 ? 1 : 0.25 }, pigeon: 1 }); return { cam: [V3(BOT0.x + lerp(0.6, 0.35, easeIn(u)), lerp(1.1, 1.0, u), lerp(3.0, 1.9, easeIn(u))), V3(BOT0.x, 0.95, 0), vfov(32)] }; }, 'still holding');
// the end card: to subscribe, press 1
shot(206.28, 300, (t, u) => {
  if (t < T.card) return { cam: [V3(0, 1, 5), V3(0, 1, 0), 30] };
  Wd.studio.set('#0c1420', '#05080d'); applyMood(MOOD.studio, t); renderer.toneMappingExposure = 0.9;
  keypad.root.visible = true; keypad.root.position.copy(STUDIO).add(V3(VERT ? 0 : -0.44, VERT ? 0.52 : 0.6, 0)); keypad.root.rotation.set(-0.15, VERT ? 0 : 0.25, 0); keypad.root.scale.setScalar(VERT ? 1.0 : 0.72);
  const p1 = T.card + 0.9; const uu = t - p1; keypad.set('1', uu >= 0 && uu < 0.2 ? Math.sin(Math.PI * uu / 0.2) : 0, uu >= 0 ? 1 : 0.0);
  return { cam: [STUDIO.clone().add(V3(0, 0.6, VERT ? 1.25 : 1.1)), STUDIO.clone().add(V3(0, VERT ? 0.62 : 0.6, 0)), VERT ? 50 : 36] };
}, 'end card');

// fallback for anything not yet staged: the plaza
const FALLBACK = (t, u) => { applyMood(moodAt(t), t); towerWindows(ENV.day.value > 0.5 ? 'day' : 'night', t); bot.root.visible = true; bot.root.scale.setScalar(0.9); bot.pose(botHold(t)); bot.setEye('wave', t); bot.updateCord();
  const a = t * 0.05; return { cam: [V3(Math.sin(a) * 6, 1.6, Math.cos(a) * 6), V3(0, 1.0, 0), vfov(40)] }; };

// ---------------------------------------------------------------- per frame
let curShot = null;
function findShot(t) { for (const s of SHOTS) if (t >= s.a && t < s.b) return s; return null; }
function updateLyrics(t, views) {
  const tanH = Math.tan(THREE.MathUtils.degToRad(FOV) / 2); ovCam.fov = FOV; ovCam.aspect = W / H; ovCam.updateProjectionMatrix(); let any = 0; if (!lyrics.length) { finish.uniforms.uScrim.value = 0; return; }
  for (const L of lyrics) { const on = !CLEAN && t >= L.userData.s && t < L.userData.e; L.visible = on; if (!on) continue; any = Math.max(any, sstep(L.userData.s, L.userData.s + 0.5, t) * (1 - sstep(L.userData.e - 0.6, L.userData.e, t)));
    L.material.uniforms.uTime.value = t; const dz = 5.2; L.position.set(0, VERT ? (SPLIT ? -dz * tanH * 0.02 : -dz * tanH * 0.5) : -dz * tanH * 0.74, -dz); L.material.uniforms.uScale.value = H / (2 * tanH); }
  finish.uniforms.uScrim.value = any * (0.18 + 0.4 * SCENE_BRIGHT);
}
let SCENE_BRIGHT = 0, SPLIT = false;
const LOOK = q.get('look');
function lookDev(t) {                 // ?look=her|her2|bot : model sheets; ?look=thumb : the thumbnail plate
  if (LOOK === 'thumb') {                // night plaza, the robot alone on the bench, cobwebs, 47:00 in its eye strip; room on the left for the type
    applyMood(MOOD.night, t); towerWindows('night', t); Wd.tower.led.set('ON HOLD 47:00', { color: 0xff8a2a, gain: 2.6 });
    bot.root.visible = true; bot.root.scale.setScalar(0.9); bot.pose(botHold(t, { headPitch: 0.18, headYaw: -0.12, lean: 0.12 })); bot.setEye('timer', t, { text: '47:00' }); bot.updateCord();
    for (const w of webs) { w.visible = true; w.scale.setScalar(1); w.material.opacity = 0.85; }
    const k = Math.floor(t); const hp = bot.headWorld();
    const P = [[V3(-1.05, 0.95, 2.35), V3(-0.25, 1.0, 0.0), 30], [V3(-0.6, 0.85, 1.7), V3(-0.15, 0.95, 0.0), 30], [V3(-1.6, 1.25, 3.4), V3(-0.55, 1.35, -0.5), 34]][k % 3];
    return { cam: [P[0], P[1], P[2]] };
  }
  applyMood(MOOD.day, t); towerWindows('day', t); const k = Math.floor(t);
  if (LOOK === 'bot') { bot.root.visible = true; bot.root.scale.setScalar(0.9); bot.pose(botHold(t)); bot.setEye('eyes', t); bot.updateCord(); const hp = bot.headWorld(); const a = [0.4, -0.6, 0, 1.2][k % 4];
    return { cam: [hp.clone().add(V3(Math.sin(a) * 1.4, -0.1, Math.cos(a) * 1.4)), hp.clone().add(V3(0, -0.25, 0)), 34] }; }
  her.root.visible = true; her.setHair(['waves', 'pulled', 'foils', 'waves', 'pulled', 'waves'][k % 6], [1, 4].includes(k % 6) ? 'dark' : 'blonde'); her.cape.visible = k % 6 === 2; her.setShades([0, 3, 5].includes(k % 6));
  her.pose({ x: 0, z: 2, seat: 0, turn: 0, headYaw: [0.3, -0.4, 0, 0.6, 0.2, 0.0][k % 6], headPitch: k % 6 === 5 ? 0.45 : 0, hands: [[-0.2, -0.04, 0.06], [0.2, -0.04, 0.06]] });
  const hp = her.headWorld().add(V3(0, 0.15, 0)); const a = [0.25, -0.5, 0.0, 2.6, 2.9, 0.9][k % 6]; const d = LOOK === 'her2' ? 3.2 : 0.95;
  return { cam: [hp.clone().add(V3(Math.sin(a) * d, LOOK === 'her2' ? -0.55 : 0.0, Math.cos(a) * d)), hp.clone().add(V3(0, LOOK === 'her2' ? -0.75 : -0.02, 0)), LOOK === 'her2' ? 34 : 30] };
}
window.renderAt = async (t) => {
  resetFrame(t); longCord.visible = false; if (netLines) netLines.visible = false;
  const s = LOOK ? null : findShot(t); const u = s ? clamp((t - s.a) / (s.b - s.a)) : 0;
  const v = (await (LOOK ? lookDev(t) : (s ? s.fn : FALLBACK)(t, u))) || {};
  if (t >= T.song && t < T.card) { fp.views = []; }   // the battery dies: hard cut to black on the exact frame the audio stops
  else if (v.split) {
    const [A, B] = v.split; look(camA, ...A.cam); look(camB, ...B.cam);
    fp.views = VERT ? [{ cam: camA, rect: [0, 0.5, 1, 0.5], before: A.before }, { cam: camB, rect: [0, 0, 1, 0.5], before: B.before }] : [{ cam: camA, rect: [0, 0, 0.5, 1], before: A.before }, { cam: camB, rect: [0.5, 0, 0.5, 1], before: B.before }];
    SPLIT = true;
    finish.uniforms.uSplit.value = VERT ? 2 : 1; finish.uniforms.uSplitAt.value = 0.5;
  } else { look(camA, ...v.cam); fp.views = [{ cam: camA, rect: [0, 0, 1, 1] }]; SPLIT = false; }
  if (her.root.visible) her.hairTick(t, HAIRO);
  updateLyrics(LOOK ? -99 : t);
  if (!CLEAN && !LOOK) drawHud(t); else finish.uniforms.uHud.value = 0;
  if (t >= T.song && t < T.card) finish.uniforms.uHud.value = 0;
  finish.uniforms.uTime.value = t; finish.uniforms.uFade.value = 1;
  composer.render();
  return renderer.domElement.toDataURL('image/jpeg', 0.93);
};

(async () => {
  await loadFonts();
  const [timed, beats] = await Promise.all([fetch('/data/timed.json').then((r) => r.json()), fetch('/data/beats.json').then((r) => r.json())]);
  build(); initTiming(timed, beats);
  window.DUR = T.dur; window.T = T; window.SHOTS = SHOTS.map((s) => [s.a, s.b, s.name]); window.__dbg = { scene, her, bot, Wd }; window.ready = true;
})().catch((e) => { console.log('INIT ERROR', e.stack || e); });
