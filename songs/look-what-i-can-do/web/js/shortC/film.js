// Look What I Can Do · v3 "The Comic Book" · S9 (the drop) and S10 (the outro), in the world of "Please Hold".
// renderTime(t) draws the frame at song time t, deterministically (any frame, any order).
//   S9  158.30-171.73  Please Hold's neon reboot: the dance-floor plaza, the little robots running the show, and the HOLD
//                      tower: its face is one giant screen scrolling her videos like a feed, and on every "Look what I can
//                      do!" its windows spell LOOK / WHAT / I CAN / DO! (each lettered window a lit room with a robot in it).
//   S10 171.73-181.60  dusk on the bench: "Claude?" "Yes?" "Can we make one more?" "You've reached your usage limit." (the
//                      eye strip drops to a 1% battery, the chest slot prints her real post as the receipt) "Hey ChatGPT?"
//                      (her real screen recording lights up on her phone, POV) and the robot's battery dies. Fade to black.
// Built from Please Hold's code (world, robot, figure, hair, props, font5, lib: copied into js/s9/ and adapted).
import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { ShaderPass } from 'three/addons/postprocessing/ShaderPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { loadFonts, clamp, lerp, sstep, easeIO, easeOut, easeIn, easeOutBack, rng, V3, RIM, RIM_AMT, FONT, dotTex } from '../s9/lib.js';
import { ENV, buildWorld, TOWER, winCenter } from '../s9/world.js';
import { Woman } from '../s9/figure.js';
import { Robot } from '../s9/robot.js';
import { Phone, PHONE, makeThumb, phoneHand, Receipt, RC } from '../s9/props.js';
import { bitmap, glyph } from '../s9/font5.js';

const q = new URLSearchParams(location.search);
const W = +q.get('w') || 1920, H = +q.get('h') || 1080; const S = Math.min(W, H) / 1080;
const VERT = H > W;                                        // Short C: 9:16. Cameras are re-framed per shot (vf); balloons stay in the Shorts safe zone
const VK = +(q.get('vk') || 1);
let VF = 1;                                                 // per-shot vertical fov factor (tan scale), set by the shot
const SAFE = VERT ? { x0: 80, x1: W * 0.88, y0: 120, y1: H * 0.76 } : null;
const T0 = 158.30, T1 = 171.7333, T2 = 181.60;           // S9 = frames 4749-5151, S10 = frames 5152-5447 (frame 5152 = 171.7333 s)

// ---------------------------------------------------------------- renderer and post (Please Hold's: ACES, bloom, finish; the HUD goes on last, after tone mapping, so it stays crisp and true to colour)
const renderer = new THREE.WebGLRenderer({ antialias: false, preserveDrawingBuffer: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(1); renderer.setSize(W, H); renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.0;
document.body.appendChild(renderer.domElement);
const scene = new THREE.Scene();
const cam = new THREE.PerspectiveCamera(36, W / H, 0.02, 4000);
const hemi = new THREE.HemisphereLight(0x2a3a66, 0x0b0c10, 0.9); scene.add(hemi);
const key = new THREE.DirectionalLight(0xfff1e0, 1.5); key.position.set(-8, 14, 22); scene.add(key); scene.add(key.target);
const glow = new THREE.PointLight(0xbfe4ff, 0, 1.2, 1.6); scene.add(glow);          // the phone's light on her face
const composer = new EffectComposer(renderer);
const rp = new RenderPass(scene, cam); composer.addPass(rp);
const bloom = new UnrealBloomPass(new THREE.Vector2(W / 2, H / 2), 0.55, 0.5, 0.82); composer.addPass(bloom);
const finish = new ShaderPass({
  uniforms: { tDiffuse: { value: null }, uTime: { value: 0 }, uVig: { value: 0.3 }, uGrain: { value: 0.022 }, uCA: { value: 0.001 }, uFlash: { value: 0 }, uFlashCol: { value: new THREE.Color(1, 1, 1) } },
  vertexShader: `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
  fragmentShader: `uniform sampler2D tDiffuse; uniform float uTime, uVig, uGrain, uCA, uFlash; uniform vec3 uFlashCol; varying vec2 vUv;
    float h(vec2 p){ return fract(sin(dot(p, vec2(12.9898,78.233)) + uTime * 17.0) * 43758.5453); }
    void main(){ vec2 d = vUv - 0.5; vec3 c;
      c.r = texture2D(tDiffuse, vUv + d * uCA).r; c.g = texture2D(tDiffuse, vUv).g; c.b = texture2D(tDiffuse, vUv - d * uCA).b;
      c *= 1.0 - uVig * pow(length(d * vec2(1.0, 0.9)) * 1.45, 2.4);
      c += (h(vUv * 1000.0) - 0.5) * uGrain * 0.5; c = mix(c, uFlashCol, uFlash);
      gl_FragColor = vec4(max(c, 0.0), 1.0); }` });
composer.addPass(finish); composer.addPass(new OutputPass());
const hudCanvas = document.createElement('canvas'); hudCanvas.width = W; hudCanvas.height = H; const hud = hudCanvas.getContext('2d');
const hudTex = new THREE.CanvasTexture(hudCanvas); hudTex.colorSpace = THREE.NoColorSpace; hudTex.generateMipmaps = false; hudTex.minFilter = THREE.LinearFilter;
const hudPass = new ShaderPass({
  uniforms: { tDiffuse: { value: null }, tHud: { value: hudTex }, uHud: { value: 0 }, uFade: { value: 0 } },
  vertexShader: `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
  fragmentShader: `uniform sampler2D tDiffuse, tHud; uniform float uHud, uFade; varying vec2 vUv;
    void main(){ vec3 c = texture2D(tDiffuse, vUv).rgb; if (uHud > 0.5) { vec4 o = texture2D(tHud, vUv); c = c * (1.0 - o.a) + o.rgb * o.a; } gl_FragColor = vec4(c * (1.0 - uFade), 1.0); }` });
composer.addPass(hudPass); hudPass.uniforms.tHud.value = hudTex;

// ---------------------------------------------------------------- timing
let LN = [], BEATS = [], DOWN = [];
const HOOK = [];                                           // the four drop hooks: word times [LOOK, WHAT, I, CAN, DO]
function beatIdx(t) { let lo = 0, hi = BEATS.length - 1; if (t < BEATS[0]) return -1; while (lo < hi) { const m = (lo + hi + 1) >> 1; if (BEATS[m] <= t) lo = m; else hi = m - 1; } return lo; }
function beatPhase(t) { const i = beatIdx(t); if (i < 0 || i >= BEATS.length - 1) return t * 129.2 / 60; return i + (t - BEATS[i]) / (BEATS[i + 1] - BEATS[i]); }
function beatPulse(t) { const i = beatIdx(t); return i < 0 ? 0 : Math.exp(-(t - BEATS[i]) / 0.11); }
function downPulse(t) { let v = 0; for (const b of DOWN) { if (b > t) break; if (t - b < 0.6) v = Math.max(v, Math.exp(-(t - b) / 0.16)); } return v; }

// ---------------------------------------------------------------- moods (Please Hold's)
const C = (h) => new THREE.Color(h);
const MOOD = {
  night: { day: 0, warm: 0, neon: 0, stars: 1, sky: C(0x3d5596), ground: C(0x10121a), hi: 1.15, key: C(0xb4c4ff), ki: 0.7, kdir: V3(-0.5, 0.8, 0.6), lamp: 1, fog: C(0x0b1022), fogD: 0.0055, lit: 0.55, rim: C(0x9fd8ff), ra: 0.55, exp: 1.05 },
  dusk: { day: 0.42, warm: 1, neon: 0, stars: 0.25, sky: C(0xffb48a), ground: C(0x3a2a2a), hi: 1.05, key: C(0xffa868), ki: 1.5, kdir: V3(-0.8, 0.25, 0.55), lamp: 0.5, fog: C(0x8a6070), fogD: 0.004, lit: 0.3, rim: C(0xffc8a0), ra: 0.5, exp: 1.0 },
  neon: { day: 0, warm: 0, neon: 1, stars: 0.4, sky: C(0x7a3aa8), ground: C(0x0a0a14), hi: 1.1, key: C(0x7ff0ff), ki: 0.8, kdir: V3(0.5, 0.7, 0.6), lamp: 0.6, fog: C(0x16072c), fogD: 0.006, lit: 0.6, rim: C(0x7ff6ff), ra: 0.75, exp: 1.05 },
};
function mixMood(a, b, k) { const o = {}; for (const n in a) { const x = a[n], y = b[n]; o[n] = typeof x === 'number' ? lerp(x, y, k) : x.clone().lerp(y, k); } return o; }
function applyMood(m) {
  ENV.day.value = m.day; ENV.warm.value = m.warm; ENV.neon.value = m.neon; ENV.stars.value = m.stars; ENV.fog.value.copy(m.fog); ENV.fogD.value = m.fogD; ENV.lit.value = m.lit;
  hemi.color.copy(m.sky); hemi.groundColor.copy(m.ground); hemi.intensity = m.hi; key.color.copy(m.key); key.intensity = m.ki;
  key.position.copy(m.kdir).normalize().multiplyScalar(30); key.target.position.set(0, 0, 0);
  RIM.value.copy(m.rim); RIM_AMT.value = m.ra; renderer.toneMappingExposure = m.exp;
  Wd.lampLight.intensity = 4.0 * m.lamp; Wd.lamp.userData.bulbMat.color.setRGB(1.0 * (0.25 + 0.75 * m.lamp), 0.82 * (0.25 + 0.75 * m.lamp), 0.55 * (0.25 + 0.75 * m.lamp)); Wd.lamp.userData.halo.material.opacity = 0.6 * m.lamp;
  Wd.floor.material.uniforms.uLamp.value = m.lamp; for (const b of Wd.streetBulbs) b.material.opacity = 0.9 * m.lamp;
  for (const l of Wd.kiosk.userData.lanterns) l.material.color.setRGB(0.55 + 1.1 * m.lamp, 0.12 + 0.25 * m.lamp, 0.1 + 0.1 * m.lamp);
  ENV.sunDir.value.copy(m.kdir).normalize();
}

const BLUE = (() => { const m = mixMood(MOOD.dusk, MOOD.night, 0.52); m.lamp = 1.0; m.exp = 1.04; m.ki = 1.05; m.key = C(0xffe0c4); m.rim = C(0xb8d4ff); m.ra = 0.5; m.stars = 0.5; return m; })();   // the outro: blue hour

// ---------------------------------------------------------------- the world, the cast
let Wd, her, bot, crowd = [], phone, thumb, pHand, receipt, POST = null;
function build() {
  Wd = buildWorld(scene);
  her = new Woman(); scene.add(her.root);
  bot = new Robot(); scene.add(bot.root);
  for (let i = 0; i < 10; i++) { const r = new Robot({ eyeRes: [256, 48] }); r.cord.mesh.visible = false; r.handset.visible = false; scene.add(r.root); crowd.push(r); }
  phone = new Phone(); scene.add(phone.root);
  thumb = makeThumb(her.mats.skin, her.mats.top); phone.root.add(thumb);
  pHand = phoneHand(her.mats.skin, her.mats.top); phone.root.add(pHand);
  receipt = new Receipt(); scene.add(receipt.mesh);
  her.setHair('waves', 'blonde'); her.setShades(true);
}
function resetFrame(t) {
  VF = 1; cam.clearViewOffset();
  her.root.visible = false; bot.root.visible = false; for (const r of crowd) r.root.visible = false; phone.root.visible = false; receipt.mesh.visible = false;
  her.headG.visible = true; herArms(true); thumb.visible = false; pHand.visible = false; her.setFace(0, 0); her.setShades(true);
  bot.root.scale.setScalar(0.9); bot.cord.mesh.visible = true; bot.handset.visible = true; bot.thrust(0);
  const hand = bot.arms[t < T1 ? 0 : 1].hand; if (bot.handset.parent !== hand) { hand.add(bot.handset); bot.handset.position.set(0.0, 0.07, 0.03); } bot.handset.rotation.set(0, 0, 0);
  Wd.bench.root.visible = true; Wd.lamp.visible = true; for (const tr of Wd.trees) tr.visible = true;
  const tw = Wd.tower; tw.setRobots([]); tw.setLetters(null, 'none'); tw.body.material.uniforms.uScreenAmt.value = 0; tw.body.material.uniforms.uScreenDim.value = 1; ENV.dance.value = 0;
  finish.uniforms.uFlash.value = 0; finish.uniforms.uFlashCol.value.setRGB(1, 1, 1); hudPass.uniforms.uFade.value = 0; glow.intensity = 0; glow.distance = 1.2;
  bloom.strength = 0.55; bloom.threshold = 0.82; bloom.radius = 0.5;
  ENV.time.value = t; ENV.beat.value = beatPulse(t); ENV.cloud.value = t * 0.01;
  Wd.tower.beacon.visible = (t % 1.6) < 0.5;
}
function herArms(on) { for (const a of her.arms) for (const m of [a.up, a.fo, a.sh, a.el, a.hand]) m.visible = on; }
function towerNight() { Wd.tower.setAll((c, r) => { const h = Math.sin(c * 12.9898 + r * 78.233) * 43758.5453; const f = h - Math.floor(h); if (f > 0.58) return null;
  return f < 0.08 ? [1.0, 0.72, 0.42] : [0.62 + 0.2 * f, 0.78 + 0.15 * f, 0.95]; }, 'night'); }

// ---------------------------------------------------------------- cameras
function vfov(fov) { return VERT ? 2 * Math.atan(Math.tan(fov * Math.PI / 360) * VF * VK) * 180 / Math.PI : fov; }
function look(p, l, fov, roll = 0) { fov = vfov(fov); cam.position.copy(p); cam.up.set(0, 1, 0); cam.lookAt(l); if (roll) cam.rotateZ(roll); cam.fov = fov; cam.aspect = W / H; cam.near = 0.01; cam.far = 4000; cam.updateProjectionMatrix(); cam.updateMatrixWorld(true); }
function shake(t, t0, amt = 0.04, tau = 0.18) { if (t < t0) return V3(); const e = Math.exp(-(t - t0) / tau) * amt; return V3(Math.sin(t * 71) * e, Math.cos(t * 53) * e, Math.sin(t * 37) * e * 0.5); }
function handheld(t, a = 0.004) { return V3(Math.sin(t * 1.1) * a + Math.sin(t * 2.9) * a * 0.4, Math.sin(t * 1.7 + 1) * a, Math.sin(t * 0.8 + 2) * a * 0.6); }
function toScreen(p) { const v = p.clone().project(cam); return [(v.x * 0.5 + 0.5) * W, (0.5 - v.y * 0.5) * H, v.z]; }
const P = (keys, t, ease = easeIO) => {                    // keyframes [[t, value], ...] (numbers or arrays), eased per segment
  if (t <= keys[0][0]) return keys[0][1]; for (let i = 1; i < keys.length; i++) { const [t1, v1, e] = keys[i]; if (t < t1) { const [ta, v0] = keys[i - 1]; const u = (e || ease)((t - ta) / (t1 - ta)); return Array.isArray(v0) ? v0.map((x, k) => lerp(x, v1[k], u)) : lerp(v0, v1, u); } }
  return keys[keys.length - 1][1]; };
const A3 = (a) => V3(a[0], a[1], a[2]);

// ---------------------------------------------------------------- the tower: windows that spell LOOK / WHAT / I CAN / DO!
// 25 x 36 windows, the 5x7 dot font. "I CAN" fits with a narrow I and a narrow "!" closes DO!.
const NARROW = { 'I': ['###', '.#.', '.#.', '.#.', '.#.', '.#.', '###'], '!': ['#', '#', '#', '#', '#', '.', '#'], ' ': ['.', '.'] };
function lineCells(text, row0, wordOf) {
  const glyphs = [...text].map((ch) => NARROW[ch] ? NARROW[ch].map((r) => r) : glyph(ch));
  const widths = glyphs.map((g, i) => text[i] === ' ' ? 1 : g[0].length);
  const total = widths.reduce((a, b) => a + b, 0) + (glyphs.length - 1);
  let c = Math.round((TOWER.cols - total) / 2); const out = [];
  glyphs.forEach((g, i) => { const ch = text[i]; const wi = wordOf(i);
    if (ch !== ' ') for (let r = 0; r < 7; r++) for (let k = 0; k < g[0].length; k++) if ((g[r] || '')[k] === '#') out.push({ c: c + k, r: row0 + r, w: wi });
    c += widths[i] + 1; });
  return out;
}
const LETTERS = [
  ...lineCells('LOOK', 1, () => 0), ...lineCells('WHAT', 10, () => 1),
  ...lineCells('I CAN', 19, (i) => (i === 0 ? 2 : 3)), ...lineCells('DO!', 28, () => 4),
];
const WORD_C0 = [0, 1, 2, 3, 4].map((w) => Math.min(...LETTERS.filter((L) => L.w === w).map((L) => L.c)));
const LKEY = new Map(LETTERS.map((L, i) => [L.c + ',' + L.r, i]));
const PAL = { ice: [0.16, 0.74, 0.98], pink: [1.1, 0.16, 0.7], amber: [1.3, 0.6, 0.12], violet: [0.7, 0.42, 1.3] };
/** the letters at t: brightness, colour, robots */
function towerLetters(t, o = {}) {
  const tw = Wd.tower; const ph = beatPhase(t);
  const hook4 = t >= HOOK[3][0] - 0.06;
  const st = LETTERS.map((L) => {
    const wt = hook4 ? HOOK[3][L.w] : HOOK[0][L.w]; const casc = (L.c - WORD_C0[L.w]) * (hook4 ? 0.006 : 0.011) + (L.r % 7) * 0.003;
    let on = sstep(wt + casc - 0.01, wt + casc + 0.05, t);
    if (hook4 && t < HOOK[3][L.w] + casc) on = 0;                        // hook 4: the face goes dark, then slams back word by word
    let fl = 0; for (const hk of HOOK) { const tw_ = hk[L.w] + casc; if (t >= tw_) fl = Math.max(fl, Math.exp(-(t - tw_) / 0.22)); }
    let col = L.w === 4 ? PAL.pink : PAL.ice;
    if (t >= HOOK[2][0] - 0.05 && !hook4) { const sw = sstep(HOOK[2][L.w] + casc - 0.02, HOOK[2][L.w] + casc + 0.06, t); col = col.map((x, k) => lerp(x, (L.w === 4 ? PAL.ice : PAL.pink)[k], sw)); }
    const pop = easeOutBack(clamp((t - (wt + casc)) / 0.28), 2.2);
    return { L, on, fl, col, pop };
  });
  const key = 'L' + Math.round(t * 30);
  tw.setLetters((c, r) => { const i = LKEY.get(c + ',' + r); return i !== undefined && st[i].on > 0.02; }, key);
  tw.setAll((c, r) => { const i = LKEY.get(c + ',' + r); if (i === undefined) return null; const s = st[i]; if (s.on <= 0.02) return null;
    const k = s.on * (1 + 0.55 * s.fl) * (o.gain ?? 1); return [s.col[0] * k, s.col[1] * k, s.col[2] * k]; }, key);
  const bots = []; for (const s of st) { if (s.on <= 0.02) continue; const L = s.L;
    const tilt = Math.sin(ph * Math.PI + L.c * 0.45 + L.r * 0.2) * 0.16; bots.push([L.c, L.r, 1.08 * s.pop, tilt, 0.12 + 0.1 * s.fl + 0.03 * Math.abs(Math.sin(ph * Math.PI))]); }
  tw.setRobots(bots);
  return st;
}

// ---------------------------------------------------------------- the tower's face as a screen: her videos, scrolling like a feed
const AFF = 'Asking for a Friend', PH = 'Please Hold', BL = 'I have a blocker.', RAGE = 'Rage Against the Machine Learning', TS = 'TED Talk · Screenlife';
const FEED = [                                            // [hd key, title, first frame, end frame): only keys that exist in web/media/hd (checked at build)
  ['ph_please_neon', PH, 39, 76], ['aff_robot_memo', AFF, 37, 100], ['aff_porsche_side', AFF, 69, 117], ['rage_said_no', RAGE, 1, 181], ['bl_city', BL, 1, 181],
  ['aff_porsche_house', AFF, 31, 96], ['ts_host', TS, 1, 181], ['ph_ring', PH, 76, 136], ['aff_customers', AFF, 136, 181], ['aff_porsche_front', AFF, 66, 126],
  ['aff_robot_button', AFF, 124, 166], ['bl_standup', BL, 1, 151], ['aff_porsche_desert', AFF, 31, 72], ['rage_metal', RAGE, 1, 181], ['aff_systems_green', AFF, 1, 31],
  ['ts_circling', TS, 1, 181], ['rage_title', RAGE, 1, 111], ['aff_robot_eyes', AFF, 46, 66], ['ts_story', TS, 1, 105], ['rage_optout', RAGE, 1, 181],
  ['ph_hold_tower', PH, 1, 110], ['ph_onhold_night', PH, 1, 63],
];
const imgCache = new Map();
function loadImg(url) { if (imgCache.has(url)) return imgCache.get(url); const p = new Promise((res) => { const im = new Image(); im.onload = () => res(im); im.onerror = () => res(null); im.src = url; }); imgCache.set(url, p); return p; }
function pruneCache(keep) { for (const k of [...imgCache.keys()]) if (!keep.has(k)) imgCache.delete(k); }
const FEED_PITCH = 512, FEED_TILE = 484, FEED_CROP = 0.84;   // canvas px (1024 x 1536); clips cropped to their top 84% (no burned-in lyrics)
function feedSwipes(t) {                                  // one swipe up every two beats from the drop; eased snap
  const b0 = beatIdx(T0 + 0.06); const ph = beatPhase(t) - b0; const n = Math.floor(ph / 2); const f = (ph / 2) - n;
  return Math.max(0, n + easeOut(clamp(f / 0.42)) * 1.0);
}
async function drawFeed(t, o = {}) {
  const tex = Wd.tower.screen; const g = tex.userData.g, w = 1024, h = 1536;
  const scroll = feedSwipes(t) * FEED_PITCH + (o.extra ?? 0);
  const first = Math.floor((scroll - 40) / FEED_PITCH); const jobs = []; const keep = new Set();
  for (let i = first; i <= first + 4; i++) { const y = i * FEED_PITCH - scroll + 26; if (y > h || y + FEED_TILE < 0) continue;
    const [k, title, fa, fb] = FEED_OK[((i % FEED_OK.length) + FEED_OK.length) % FEED_OK.length]; const n = fb - fa;
    const fr = fa + Math.floor(((t - T0) * 30 + i * 7) % n + n) % n; const url = `/media/hd/${k}/${String(fr).padStart(3, '0')}.jpg`; keep.add(url);
    jobs.push(loadImg(url).then((im) => ({ im, y, title }))); }
  const tiles = await Promise.all(jobs); pruneCache(new Set([...keep, ...[...imgCache.keys()].filter((u) => !u.includes('/media/hd/'))]));
  g.setTransform(1, 0, 0, 1, 0, 0); g.globalAlpha = 1; g.filter = 'none'; g.fillStyle = '#05040b'; g.fillRect(0, 0, w, h);
  for (const { im, y, title } of tiles) { if (!im) continue;
    g.drawImage(im, 0, 0, im.width, im.height * FEED_CROP, 0, y, w, FEED_TILE);
    // a progress bar and the title chip: the tower is scrolling her channel
    g.fillStyle = 'rgba(255,255,255,0.22)'; g.fillRect(0, y + FEED_TILE - 6, w, 6); g.fillStyle = '#ff3d5a'; g.fillRect(0, y + FEED_TILE - 6, w * (((t * 0.11) + y * 0.0007) % 1), 6);
  }
  // soft: under the letters the feed goes out of focus, so the words own the face (a blurred low-res pass over the sharp one)
  const soft = o.soft ?? 0; if (soft > 0.01) { const sg = SOFT.getContext('2d'); sg.filter = 'blur(2.5px)'; sg.drawImage(tex.image, 0, 0, SOFT.width, SOFT.height); sg.filter = 'none';
    g.globalAlpha = soft; g.imageSmoothingQuality = 'high'; g.drawImage(SOFT, 0, 0, w, h); g.globalAlpha = 1; }
  tex.needsUpdate = true;
}
const SOFT = document.createElement('canvas'); SOFT.width = 192; SOFT.height = 288;
let FEED_OK = FEED;

// ---------------------------------------------------------------- dancing robots
const FORM = [[-2.6, -5.2], [2.6, -5.2], [-4.6, -6.6], [4.6, -6.6], [-1.3, -7.6], [1.3, -7.6], [-6.4, -8.4], [6.4, -8.4], [-3.4, -9.6], [3.4, -9.6]];
const HERO = { x: 0, z: -3.4 };
function danceP(t, i, o = {}) {
  const ph = beatPhase(t + i * 0.0) * Math.PI; const up = Math.abs(Math.sin(ph)); const side = Math.sin(ph * 0.5);
  // arms: pump on the beat, alternate sides every bar; on a "do!" every robot throws both arms up
  const doUp = o.doUp ?? 0; const alt = Math.floor(beatPhase(t) / 4) % 2 ? 1 : -1;
  const pumpR = [0.24, 0.32 + 0.26 * up, 0.14 + 0.08 * side], pumpL = [-0.24, 0.28 + 0.06 * (1 - up), 0.16];
  let hands = alt > 0 ? [pumpL, pumpR] : [[-pumpR[0], pumpR[1], pumpR[2]], [-pumpL[0], pumpL[1], pumpL[2]]];
  const upP = [[-0.26, 0.98, 0.04], [0.26, 0.98, 0.04]];
  hands = hands.map((hh, k) => hh.map((v, j) => lerp(v, upP[k][j], doUp)));
  return { x: o.x, z: o.z, turn: o.turn ?? 0, seat: 0, lean: 0.04 - 0.08 * doUp, bob: up * 0.045 + 0.04 * doUp, headRoll: Math.sin(ph) * 0.18 * (1 - doUp), headPitch: -0.06 - 0.2 * doUp,
    hands, hipRoll: Math.sin(ph) * 0.07, hipTwist: side * 0.18 * (1 - doUp), twist: -side * 0.1 };
}
function doUpAt(t) { let v = 0; for (const t4 of [T0 - 0.02, ...HOOK.map((h) => h[4])]) { const d = t - t4; if (d > -0.12 && d < 0.9) v = Math.max(v, d < 0 ? easeOut((d + 0.12) / 0.12) : 1 - easeIO((d - 0.45) / 0.45)); } return v; }
function placeCrowd(t, o = {}) {
  const du = doUpAt(t);
  crowd.forEach((r, i) => { const [x, z] = FORM[i]; r.root.visible = true; r.root.scale.setScalar(0.9);
    r.pose(danceP(t - 0.03 * (i % 3), i, { x, z, doUp: du })); r.setEye('happy', t); });
  // the hero (the robot from the bench): front and centre, singing into its receiver like a mic
  bot.root.visible = true; bot.root.scale.setScalar(1.0);
  const p = danceP(t, -1, { x: HERO.x, z: HERO.z, doUp: du }); const ph = beatPhase(t) * Math.PI;
  const cond = [0.3 + 0.12 * Math.cos(ph), 0.52 + 0.2 * Math.abs(Math.sin(ph)), 0.22 + 0.06 * Math.sin(ph)];     // conducting, a beat per stroke
  p.hands = [[-0.15, 0.64, 0.07], cond.map((v, k) => lerp(v, [0.26, 0.98, 0.04][k], du))]; p.headRoll = -0.1 + 0.08 * Math.sin(ph); p.headPitch = 0.05 - 0.15 * du;
  bot.pose(p); bot.setEye(o.eye || 'happy', t); bot.updateCord();
}

// ---------------------------------------------------------------- her and the robot on the bench (S10)
const HER0 = { x: -0.42, z: -0.06 }, BOT0 = { x: 0.45, z: -0.06 };
function herSit(t, o = {}) { const br = Math.sin(t * 1.3) * 0.006;
  return { x: HER0.x, z: HER0.z, seat: 1, lean: 0.06 + br, twist: 0.12, headPitch: 0.02, headYaw: 0.55, headRoll: -0.04, hands: [[-0.1, 0.13, 0.3], [0.09, 0.11, 0.31]], kneeOut: 0.0, ...o }; }
function botSit(t, o = {}) { const bob = Math.sin(t * 2.2) * 0.008;
  return { x: BOT0.x, z: BOT0.z, seat: 1, lean: 0.08, headPitch: 0.04 + bob, headYaw: -0.5, headRoll: 0.05, hands: [[-0.1, 0.17, 0.27], [0.33, 0.02, 0.1]], swing: t * 1.6, ...o }; }
function eyeOf(fig) { fig.root.updateMatrixWorld(true); return V3(0, 0.13, 0.05).applyMatrix4(fig.headG.matrixWorld); }
/** her seated with the phone where her eyes look (d metres along the gaze); poses her twice (hands onto the phone) */
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
  phone.root.visible = true; return { c, n, e, gaze, up };
}
function herBowed(t, o = {}) { const br = Math.sin(t * 1.3) * 0.006;
  return { x: HER0.x, z: HER0.z, seat: 1, lean: 0.27 + br, headPitch: 0.6, headYaw: 0.03, headRoll: 0.03, hands: [[-0.075, 0.13, 0.33], [0.07, 0.11, 0.32]], kneeOut: 0.0, ...o }; }
/** the phone resting in her right hand on her lap, screen dark */
function phoneInLap() {
  her.root.updateMatrixWorld(true); const hr = her.handWorld(1), hl = her.handWorld(0);
  phone.root.visible = true; phone.setOn(0); phone.root.position.copy(hr.clone().lerp(hl, 0.35)).add(V3(0, 0.025, 0.02));
  phone.root.rotation.set(-Math.PI / 2 + 0.25, 0, 0.5);
}

// ---------------------------------------------------------------- her phone: the real screen recording, re-timed (song time -> recording frame, 1-based)
const CHAT = [[176.78, 12], [176.95, 17], [177.20, 30], [177.36, 86], [177.58, 118], [177.80, 132], [177.92, 169], [178.02, 193], [178.10, 216], [178.15, 271],
  [178.22, 277], [178.42, 288], [178.70, 333], [179.48, 360], [180.62, 393]];
function chatFrame(t) { if (t <= CHAT[0][0]) return CHAT[0][1]; for (let i = 1; i < CHAT.length; i++) if (t < CHAT[i][0]) { const [a, fa] = CHAT[i - 1], [b, fb] = CHAT[i]; return Math.round(lerp(fa, fb, (t - a) / (b - a))); } return CHAT[CHAT.length - 1][1]; }
function chatTime(f) { for (let i = 1; i < CHAT.length; i++) { const [a, fa] = CHAT[i - 1], [b, fb] = CHAT[i]; if (f <= fb) return lerp(a, b, (f - fa) / Math.max(1, fb - fa)); } return CHAT[CHAT.length - 1][0]; }
// her thumb, key by key (recording pixels): the taps the recording shows
const KX = { q: 60, w: 170, e: 274, r: 380, t: 486, y: 592, u: 696, i: 806, o: 910, p: 1018, a: 114, s: 220, d: 326, f: 432, g: 538, h: 644, j: 752, k: 858, l: 964, z: 220, x: 326, c: 432, v: 538, b: 646, n: 752, m: 858 };
const ROWY = (ch) => ('qwertyuiop'.includes(ch) ? 1544 : ('asdfghjkl'.includes(ch) ? 1682 : 1820));
const TAPS = [[17, 'h'], [23, 'e'], [29, 'y'], [61, '#123'], [85, ','], [105, ' '], [114, '^'], [117, 'c'], [121, 'h'], [127, 'a'], [129, 't'], [159, '^'], [168, 'g'], [186, '^'], [192, 'p'], [204, '^'], [215, 't'], [271, 'send']]
  .map(([f, k]) => { let x, y; if (k === '#123') { x = 74; y = 1958; } else if (k === ',') { x = 540; y = 1820; } else if (k === ' ') { x = 540; y = 1958; } else if (k === '^') { x = 80; y = 1820; } else if (k === 'send') { x = 980; y = 1264; } else { x = KX[k]; y = ROWY(k); }
    return { t: chatTime(f), x, y }; });
async function phoneScreen(t, on) {
  const f = chatFrame(t); const im = await loadImg(`/tex/s9/chat/${String(f).padStart(3, '0')}.jpg`);
  if (im && phone.frame !== f) { phone.tex.image = im; phone.tex.needsUpdate = true; phone.frame = f; }
  phone.setOn(on);
}
function thumbAt(t) {
  if (t < TAPS[0].t - 0.3 || t > TAPS[TAPS.length - 1].t + 0.45) { thumb.visible = false; return; }
  let i = TAPS.findIndex((k) => k.t > t); if (i < 0) i = TAPS.length; const a = TAPS[Math.max(0, i - 1)], b = TAPS[Math.min(TAPS.length - 1, i)];
  const u = i === 0 || i === TAPS.length ? 0 : easeIO((t - a.t) / Math.max(0.05, b.t - a.t));
  let x = i === 0 ? b.x : lerp(a.x, b.x, u), y = i === 0 ? b.y + 160 : lerp(a.y, b.y, u);
  const dip = Math.max(...TAPS.map((k) => Math.exp(-Math.abs(t - k.t) / 0.035)));
  let hgt = 0.014 * (1 - dip) + 0.0015;
  const away = sstep(TAPS[TAPS.length - 1].t + 0.08, TAPS[TAPS.length - 1].t + 0.45, t); y += away * 1400; hgt += away * 0.03;
  thumb.visible = true; thumb.position.copy(phone.local(x + 40, y + 70)).add(V3(0, 0, hgt)); thumb.rotation.set(-0.5, 0, 0.35);
}
/** through her eyes: the phone in her hands (her head and arms hidden, a close-up hand holds it) */
function povPhone(t, o = {}) {
  her.root.visible = true; const pl = herWithPhone(t, herBowed(t, o.pose), { d: o.d ?? 0.3 }); her.headG.visible = false; herArms(false); pHand.visible = true;
  const up = V3(0, 1, 0).applyQuaternion(phone.root.quaternion); const p = pl.e.clone().add(handheld(t, o.hh ?? 0.0025));
  const lk = pl.c.clone().addScaledVector(up, o.lift ?? 0.0).add(o.lookOff || V3());
  return { p, lk, c: pl.c, up };
}

// ---------------------------------------------------------------- HUD: the dialogue as comic balloons (hers: white with a green prompt; Claude's: an amber LED panel)
const GREEN = '#74e36a', AMBER = '#ffa840';
function rrPath(x, y, w, h, r) { const p = new Path2D(); p.roundRect(x, y, w, h, r); return p; }
function tailPath(bx, by, bw, bh, tx, ty, base) {         // a wedge from the box edge toward (tx, ty)
  const cx = clamp(tx, bx + base * 1.2, bx + bw - base * 1.2), cy = clamp(ty, by + base * 1.2, by + bh - base * 1.2);
  const p = new Path2D(); const below = ty > by + bh, above = ty < by;
  if (below || above) { const ey = below ? by + bh - 2 : by + 2; const len = Math.hypot(tx - cx, ty - ey); const k = Math.min(1, (90 * S) / Math.max(1, len));
    const ex = cx + (tx - cx) * k, eyy = ey + (ty - ey) * k; p.moveTo(cx - base / 2, ey); p.quadraticCurveTo(cx - base * 0.1, (ey + eyy) / 2, ex, eyy); p.quadraticCurveTo(cx + base * 0.25, (ey + eyy) / 2, cx + base / 2, ey); }
  else { const ex0 = tx < bx ? bx + 2 : bx + bw - 2; const len = Math.hypot(tx - ex0, ty - cy); const k = Math.min(1, (90 * S) / Math.max(1, len));
    const ex = ex0 + (tx - ex0) * k, eyy = cy + (ty - cy) * k; p.moveTo(ex0, cy - base / 2); p.quadraticCurveTo((ex0 + ex) / 2, cy - base * 0.1, ex, eyy); p.quadraticCurveTo((ex0 + ex) / 2, cy + base * 0.25, ex0, cy + base / 2); }
  p.closePath(); return p;
}
function dotRun(g, text, x0, yTop, d, t0, t, col) {        // dot-matrix text, columns scanning on letter by letter
  const rows = bitmap(text); const n = rows[0].length; g.fillStyle = col;
  for (let c = 0; c < n; c++) { const ch = Math.floor(c / 6); const ta = t0 + ch * 0.024 + (c % 6) * 0.006; if (t < ta) continue;
    for (let r = 0; r < 7; r++) if (rows[r][c]) { g.beginPath(); g.arc(x0 + c * d + d / 2, yTop + r * d + d / 2, d * 0.4, 0, 6.2832); g.fill(); } }
  return n * d;
}
/** b: { who: 'her'|'claude', lines: [...], t0, t1, x, y (box centre, px), tail: [x, y] (px, the speaker) } */
function balloon(b, t) {
  const kin = clamp((t - b.t0) / 0.16), kout = 1 - clamp((t - (b.t1 - 0.14)) / 0.14); const a = Math.min(kin, kout); if (a <= 0.003) return false;
  const sc = lerp(0.72, 1, easeOutBack(clamp((t - b.t0) / 0.26), 2.2)) * lerp(0.94, 1, kout);
  const g = hud; g.save();
  let bw, bh, padX, padY, lh, px, d;
  if (b.who === 'her') { px = 62 * S; lh = px * 1.2; padX = 34 * S; padY = 22 * S; g.font = `${px}px ${FONT.disp}`;
    const chev = 0; bw = Math.max(...b.lines.map((l) => g.measureText(l).width)) + padX * 2 + px * 0.95; bh = b.lines.length * lh + padY * 2 - px * 0.12; }
  else { d = (VERT ? 7.5 : 6.5) * S; lh = 10.5 * d; padX = 4 * d; padY = 3.4 * d; bw = Math.max(...b.lines.map((l) => bitmap(l)[0].length)) * d + padX * 2; bh = b.lines.length * lh - (lh - 7 * d) + padY * 2; }
  const cx = SAFE ? clamp(b.x, SAFE.x0 + bw / 2, SAFE.x1 - bw / 2) : clamp(b.x, bw / 2 + 60 * S, W - bw / 2 - 60 * S), cy = SAFE ? clamp(b.y, SAFE.y0 + bh / 2, SAFE.y1 - bh / 2) : clamp(b.y, bh / 2 + 50 * S, H - bh / 2 - 50 * S);
  const ax = b.tail ? b.tail[0] : cx, ay = b.tail ? b.tail[1] : cy + bh;
  g.translate(lerp(ax, cx, sc), lerp(ay, cy, sc)); g.scale(sc, sc); g.translate(-cx, -cy); g.globalAlpha = a;
  const bx = cx - bw / 2, by = cy - bh / 2; const box = rrPath(bx, by, bw, bh, (b.who === 'her' ? 26 : 18) * S); const tail = b.tail ? tailPath(bx, by, bw, bh, b.tail[0], b.tail[1], 40 * S) : null;
  // soft drop shadow, the border (stroke of the union, covered inside by the fill), the fill
  g.save(); g.shadowColor = 'rgba(0,0,0,0.45)'; g.shadowBlur = 30 * S; g.shadowOffsetY = 8 * S; g.fillStyle = 'rgba(0,0,0,0.6)'; g.fill(box); if (tail) g.fill(tail); g.restore();
  g.lineJoin = 'round'; g.lineWidth = 5 * S; g.strokeStyle = b.who === 'her' ? 'rgba(116,227,106,0.95)' : 'rgba(255,168,64,0.9)'; g.stroke(box); if (tail) g.stroke(tail);
  g.fillStyle = b.who === 'her' ? '#0d1116' : '#07080b'; g.fill(box); if (tail) g.fill(tail);
  if (b.who === 'her') {
    g.textBaseline = 'alphabetic'; b.lines.forEach((l, i) => { const y = by + padY + px * 0.86 + i * lh;
      if (i === 0) { g.font = `${px * 0.86}px ${FONT.monoB}`; g.fillStyle = GREEN; g.fillText('❯', bx + padX, y - px * 0.02); }
      g.font = `${px}px ${FONT.disp}`; g.fillStyle = '#ffffff'; g.fillText(l, bx + padX + px * 0.95, y); });
  } else {
    g.shadowColor = 'rgba(255,150,40,0.85)'; g.shadowBlur = d * 1.1; let n0 = 0;
    b.lines.forEach((l, i) => { dotRun(g, l, bx + padX, by + padY + i * lh, d, b.t0 + 0.05 + n0 * 0.024, t, '#ffb24a'); n0 += l.length; });
  }
  g.restore(); return true;
}
function drawHud(t, balloons) {
  hud.setTransform(1, 0, 0, 1, 0, 0); hud.clearRect(0, 0, W, H); let any = false;
  for (const b of balloons || []) any = balloon(b, t) || any;
  hudPass.uniforms.uHud.value = any ? 1 : 0; if (any) hudTex.needsUpdate = true;
}

// ---------------------------------------------------------------- the shots
const SHOTS = []; const shot = (a, b, fn, name) => SHOTS.push({ a, b, fn, name });
function neon(t) { applyMood(MOOD.neon); ENV.dance.value = 1; Wd.bench.root.visible = false; Wd.lamp.visible = false; for (const tr of Wd.trees) tr.visible = false; bloom.strength = 0.48;
  const tw = Wd.tower; tw.body.material.uniforms.uScreenAmt.value = 1; tw.body.material.uniforms.uScreenGain.value = 1.12 + 0.25 * beatPulse(t);
  tw.led.set('NOW SHOWING · EVERYTHING WE MADE · NOW SHOWING · EVERYTHING WE MADE', { color: 0xff4fd8, gain: 2.6 + 1.2 * beatPulse(t), scroll: (t - T0) * 24 - 40 }); }
function hookLed(t) { const k = HOOK.filter((h) => t >= h[0] - 0.05).length; if (!k) return;
  Wd.tower.led.set('LOOK WHAT I CAN DO!', { color: k % 2 ? 0x5ff4ff : 0xff4fd8, gain: 2.8 + 2.0 * downPulse(t) }); }

// S9 ---------------------------------------------------------------------------------------------------------------
shot(T0, 160.15, async (t, u) => {          // the drop: the city reboots in neon, the tower is a giant feed, the robots take the floor
  neon(t); await drawFeed(t); placeCrowd(t); towerLetters(-99); VF = 1.3;
  const hit = Math.exp(-(t - T0) / 0.14); bloom.strength = 0.48 + 0.2 * hit; renderer.toneMappingExposure = 1.05 + 0.1 * hit;
  ENV.beat.value = Math.max(ENV.beat.value, 0.5 * hit);
  const k = easeIO((t - T0) / 1.85); const p = V3(lerp(1.0, 0.45, k), lerp(0.95, 1.7, k), lerp(0.4, -0.4, k)).add(shake(t, T0, 0.07, 0.2));
  const l = V3(lerp(0.0, 0.0, k), lerp(4.6, 21, k), lerp(-20, -33, k)); const fov = 64 - 7 * Math.exp(-(t - T0) / 0.14);
  return { cam: [p, l, fov] };
}, 'drop: reboot');
shot(160.15, HOOK_T(0), async (t, u) => {   // the robots run the show: the hero sings into its receiver, the feed behind
  neon(t); await drawFeed(t); placeCrowd(t); towerLetters(-99);
  const a = lerp(-0.42, -0.12, easeIO(u)); const c = V3(HERO.x, 0.95, HERO.z); const p = c.clone().add(V3(Math.sin(a) * 2.0, lerp(-0.42, -0.3, u), Math.cos(a) * 2.0));
  if (VERT) { VF = 1.3; return { cam: [p, c.clone().add(V3(lerp(0.62, 0.7, u), lerp(1.1, 1.35, u), -2)), 46] }; }
  return { cam: [p, c.clone().add(V3(lerp(0.75, 0.9, u), lerp(1.0, 1.25, u), -2)), 46] };
}, 'drop: the robots run the show');
// 9:16 framing of the whole tower face (Nov 8 stills round): the four rows LOOK / WHAT / I CAN / DO! filled the phone
// frame edge to edge, so the K and N sat under the button column and DO! in the caption zone. TOWER_V shrinks the face
// (k = 1 - share of the way) and lifts it up-left with a view offset, landing the letters in x 5-87 %, y 8-77 %.
const TOWER_V = { s: 0.84, dx: 0.025, dy: 0.075 };
function towerV(w = 1) { return VERT && w > 0 ? [lerp(1, TOWER_V.s, w), TOWER_V.dx * w, TOWER_V.dy * w] : null; }
function HOOK_T(i) { return [161.74, 163.66, 167.95, 170.67][i]; }
shot(HOOK_T(0), HOOK_T(1), async (t, u) => {  // hook 1: the windows spell it, word by word
  const on = sstep(HOOK[0][0] - 0.1, HOOK[0][0] + 0.15, t); neon(t); hookLed(t); await drawFeed(t, { soft: on }); placeCrowd(t); towerLetters(t);
  Wd.tower.body.material.uniforms.uScreenDim.value = lerp(1, 0.22, on);
  const k = easeIO(u); const p = V3(lerp(7.5, 5.0, k), lerp(22, 25, k), lerp(44, 38, k));
  return { cam: [p, V3(lerp(1.0, 0.6, k), 36.0, -33), 48 - 1.5 * downPulse(t)], vshift: towerV(1) };
}, 'hook 1: LOOK WHAT I CAN DO');
shot(HOOK_T(1), HOOK_T(2), async (t, u) => {  // hook 2: up close along the letters (a robot in every lettered window, her videos between), then the pull-back
  const pull = sstep(HOOK[1][2] - 0.25, HOOK[1][4] + 0.35, t);
  neon(t); hookLed(t); await drawFeed(t, { soft: lerp(0.45, 1, pull) }); placeCrowd(t); towerLetters(t);
  Wd.tower.body.material.uniforms.uScreenDim.value = lerp(0.34, 0.22, pull);
  const yLook = winCenter(12, 4).y, yWhat = winCenter(12, 13).y;
  const near = P([[HOOK_T(1), [-7.0, yLook - 0.5, -12.5]], [HOOK[1][1] - 0.1, [-1.0, yLook - 1.0, -13.0]], [HOOK[1][1] + 0.35, [-2.5, yWhat, -13.5]], [HOOK[1][2] - 0.2, [3.5, yWhat - 0.5, -13.0]]], t);
  const nearL = P([[HOOK_T(1), [-1.5, yLook, -33]], [HOOK[1][1] - 0.1, [1.8, yLook - 0.4, -33]], [HOOK[1][1] + 0.35, [0.0, yWhat, -33]], [HOOK[1][2] - 0.2, [3.0, yWhat, -33]]], t);
  const far = [lerp(3.5, -5.5, pull), lerp(32, 24, pull), lerp(-6, 40, pull)], farL = [0.4, 36.0, -33];
  const e = easeIO(pull); const p = A3(near).lerp(A3(far), e), l = A3(nearL).lerp(A3(farL), e);
  return { cam: [p, l, lerp(40, 49, e)], vshift: towerV(e) };
}, 'hook 2: along the letters');
shot(HOOK_T(2), HOOK_T(3), async (t, u) => {  // hook 3: crane up from the robots on the dance floor to the whole tower; the letters turn pink word by word
  neon(t); hookLed(t); await drawFeed(t, { soft: 1 }); placeCrowd(t); towerLetters(t); VF = 1.12;
  Wd.tower.body.material.uniforms.uScreenDim.value = 0.22;
  const k = easeIO(clamp((t - HOOK_T(2) - 0.25) / 1.9));
  const p = A3(P([[0, [-3.4, 1.0, 2.6]], [1, [-6.5, 21, 38]]], k, (x) => x)), l = A3(P([[0, [0.4, 1.5, -6]], [1, [0.6, 36.0, -33]]], k, (x) => x));
  return { cam: [p, l, lerp(50, 49, k)], vshift: towerV(k) };
}, 'hook 3: crane up');
shot(HOOK_T(3), T1, async (t, u) => {          // hook 4: dark, then the words slam in one by one; ends on the whole phrase
  neon(t); hookLed(t); await drawFeed(t, { soft: 1 }); placeCrowd(t); towerLetters(t);
  Wd.tower.body.material.uniforms.uScreenDim.value = 0.21;
  const bump = Math.max(...HOOK[3].map((x) => (t >= x ? Math.exp(-(t - x) / 0.09) : 0)));
  const k = easeOut(u); const p = V3(lerp(1.0, 0.4, k), lerp(26, 27, k), lerp(42, 37, k));
  return { cam: [p, V3(0.3, 36.0, -33), 49 - 1.6 * bump], vshift: towerV(1) };
}, 'hook 4: slam');

// S10 --------------------------------------------------------------------------------------------------------------
function dusk(t, ledText, ledCol = 0xff8a2a) { applyMood(BLUE); towerNight(); Wd.tower.led.set(ledText, { color: ledCol, gain: 2.4 });
  Wd.lamp.userData.bulbMat.color.setRGB(0.62, 0.5, 0.34); Wd.lamp.userData.halo.material.opacity = 0.3; }
function usageLed(t) { if (t < 173.04) return ['USAGE 97%', 0xff8a2a]; if (t < 174.3) return ['USAGE 99%', 0xff8a2a]; return [(t % 0.6) < 0.38 ? 'USAGE LIMIT REACHED' : '', 0xff3b30]; }
const LINES10 = { claude: 171.74, yes: 172.24, more: 173.04, limit: 174.30, gpt: 176.78 };
function benchPair(t, o = {}) {
  her.root.visible = true; her.setFace(o.smile ?? 0, o.brow ?? 0); her.pose(herSit(t, o.her)); phoneInLap();
  bot.root.visible = true; bot.root.scale.setScalar(0.9); bot.pose(botSit(t, o.bot)); bot.setEye(o.eye || 'eyes', t, o.eyeO || {}); bot.updateCord();
}
async function drawJumbo(t, t0, on = 1) {                 // the Claude robot's face (Asking for a Friend), eyes at the height that shows over the bench
  const f = 46 + Math.min(19, Math.floor(Math.max(0, t - t0) * 30 * 0.62)); const im = await loadImg(`/media/hd/aff_robot_eyes/${String(f).padStart(3, '0')}.jpg`);
  const tex = Wd.tower.screen; const g = tex.userData.g, w = 1024, h = 1536; g.setTransform(1, 0, 0, 1, 0, 0); g.globalAlpha = 1; g.filter = 'none';
  const bg = g.createLinearGradient(0, 0, 0, h); bg.addColorStop(0, '#05060a'); bg.addColorStop(1, '#0d0f16'); g.fillStyle = bg; g.fillRect(0, 0, w, h);
  if (im && on > 0.003) { const sc = 0.98; const dw = 960 * sc, dh = 540 * sc; g.globalAlpha = on; g.drawImage(im, 512 - 600 * sc, 1318 - 243 * sc, dw, dh); g.globalAlpha = 1; }
  tex.needsUpdate = true;
}
shot(T1, LINES10.more, async (t, u) => {       // "Claude?" "Yes?": the two of them on the bench; the tower's face answers with the Claude robot
  dusk(t, '', 0xff8a2a);
  const turnB = easeIO(clamp((t - (LINES10.yes - 0.2)) / 0.3));
  benchPair(t, { her: { headYaw: lerp(0.3, 0.55, easeIO(clamp((t - LINES10.claude + 0.15) / 0.3))), headPitch: -0.12 }, bot: { headYaw: lerp(0.0, -0.55, turnB), headPitch: lerp(0.12, 0.0, turnB) },
    eye: t < LINES10.yes - 0.1 ? 'wave' : 'eyes', eyeO: t < LINES10.yes - 0.1 ? { amp: 0.4 } : { look: -1 } });
  const scrOn = sstep(LINES10.claude + 0.06, LINES10.claude + 0.2, t); const tw = Wd.tower.body.material.uniforms;
  await drawJumbo(t, LINES10.claude + 0.1, scrOn); tw.uScreenAmt.value = 1; tw.uScreenGain.value = 1.08; tw.uScreenDim.value = 1;
  const p = V3(lerp(0.42, 0.36, u), 0.72, lerp(3.6, 3.35, easeIO(u)));
  if (VERT) { VF = 1.45; look(V3(lerp(0.2, 0.16, u), 0.9, lerp(3.7, 3.45, easeIO(u))), V3(0.02, 1.5, 0), 37); } else look(p, V3(0.06, 1.7, 0), 37);
  const hp = her.headWorld(), bp = bot.headWorld(); const hs = toScreen(hp.clone().add(V3(0.0, 0.06, 0.1))), bs = toScreen(bp.clone().add(V3(0.0, 0.08, 0.1)));
  return { balloons: [
    { who: 'her', lines: ['Claude?'], t0: LINES10.claude, t1: LINES10.more - 0.05, x: hs[0] - (VERT ? 60 : 260) * S, y: hs[1] - (VERT ? 260 : 200) * S, tail: [hs[0] - 16 * S, hs[1] - 46 * S] },
    { who: 'claude', lines: ['YES?'], t0: LINES10.yes, t1: LINES10.more + 0.4, x: bs[0] + (VERT ? 60 : 250) * S, y: bs[1] - (VERT ? 330 : 190) * S, tail: [bs[0] + 14 * S, bs[1] - 44 * S] }] };
}, 'claude? yes?');
shot(LINES10.more, LINES10.limit, (t, u) => {  // "Can we make one more?": over the robot's shoulder onto her
  const [lt, lc] = usageLed(t); dusk(t, lt, lc);
  const lean = easeIO(clamp((t - LINES10.more) / 0.5));
  benchPair(t, { smile: 1, brow: lean, her: { lean: 0.06 + 0.1 * lean, twist: 0.12 + 0.12 * lean, headYaw: 0.62, headPitch: -0.04, headRoll: -0.1 * lean, hands: [[-0.06, 0.2, 0.3], [0.07, 0.2, 0.31]] },
    bot: { headYaw: -0.55, headPitch: 0.02 }, eye: 'eyes', eyeO: { look: -1 } });
  const hp = her.headWorld();
  const p = V3(lerp(0.78, 0.74, u), lerp(1.2, 1.18, u), lerp(1.75, 1.6, u)); if (VERT) VF = 1.25; look(p, hp.clone().add(V3(VERT ? 0.04 : 0.16, VERT ? -0.16 : -0.08, 0)), 30);
  const hs = toScreen(hp.clone().add(V3(0.03, 0.02, 0.1)));
  return { balloons: [{ who: 'her', lines: ['Can we make', 'one more?'], t0: LINES10.more, t1: LINES10.limit + 0.3, x: VERT ? hs[0] : hs[0] - 430 * S, y: VERT ? hs[1] - 330 * S : hs[1] - 120 * S, tail: VERT ? [hs[0] - 20 * S, hs[1] - 150 * S] : [hs[0] - 110 * S, hs[1] + 10 * S] }] };
}, 'can we make one more?');
const PRINT0 = 175.02, PRINT1 = 175.62, HL0 = 175.74, HL1 = 176.12;
shot(LINES10.limit, 174.98, (t, u) => {        // the eye strip drops to a 1% battery
  dusk(t, '', 0xff3b30);
  const sag = easeIO(clamp((t - LINES10.limit - 0.1) / 0.6));
  benchPair(t, { bot: { headYaw: -0.5, headPitch: 0.02 + 0.22 * sag, headRoll: 0.05 + 0.06 * sag, lean: 0.08 + 0.06 * sag }, eye: 'battery', eyeO: { on: ((t - LINES10.limit) % 0.5) < 0.32 ? 1 : 0.3 } });
  bot.root.updateMatrixWorld(true); const ep = V3(0, 0.152, 0.13).applyMatrix4(bot.headG.matrixWorld); const fwd = V3(0, 0, 1).applyQuaternion(bot.headG.getWorldQuaternion(new THREE.Quaternion()));
  if (VERT) VF = 1.6; look(ep.clone().addScaledVector(fwd, lerp(0.56, 0.5, u) * (VERT ? 1.15 : 1)).add(V3(0.0, 0.02, 0)), ep.clone().add(V3(0, VERT ? 0.03 : -0.01, 0)), 30);
  return { balloons: [limitBalloon(t, ep)] };
}, 'battery 1%');
function limitBalloon(t) { return { who: 'claude', lines: ["YOU'VE REACHED", 'YOUR USAGE LIMIT.'], t0: LINES10.limit, t1: 175.55, x: VERT ? W * 0.44 : W * 0.24, y: H * (VERT ? 0.14 : 0.17), tail: null }; }
function botReceipt(t) {
  benchPair(t, { bot: { headYaw: -0.5, headPitch: 0.24, headRoll: 0.11, lean: 0.14, hands: [[-0.4, 0.02, 0.0], [0.4, 0.02, 0.0]], elbowOut: 0.4 }, eye: 'battery', eyeO: { on: ((t - LINES10.limit) % 0.5) < 0.32 ? 1 : 0.3 } });
  const L = receipt.Ltex * easeOut(clamp((t - PRINT0) / (PRINT1 - PRINT0)));
  receipt.draw({ hl: easeIO(clamp((t - HL0) / (HL1 - HL0))) }); receipt.mesh.visible = L > 0.001;
  bot.root.updateMatrixWorld(true); const q = bot.torso.getWorldQuaternion(new THREE.Quaternion()); const fwd = V3(0, -0.1, 1).applyQuaternion(q).normalize(); const side = V3(1, 0, 0).applyQuaternion(q);
  const jit = t < PRINT1 + 0.05 && t > PRINT0 ? Math.sin(t * 90) * 0.0012 : 0;
  receipt.shape(bot.slotWorld().add(fwd.clone().multiplyScalar(0.004)).add(V3(0, jit, 0)), fwd, side, Math.max(L, 0.002), { pitch0: -0.4, bend: 4.0, sway: 1, t });
  return { L, fwd, side };
}
shot(174.98, 176.70, (t, u) => {               // the chest slot prints the receipt: her real post; the highlighter finds the line
  dusk(t, '', 0xff3b30);
  const { L } = botReceipt(t); bot.cord.mesh.visible = false; bot.handset.visible = false;
  // aim square-on at the highlighted line: its point on the strip and the paper's normal there
  const sHl = (RC.hl[1] + RC.hl[3]) / 2 / RC.H * receipt.Ltex; const sPost = (RC.postY + RC.postH * 0.42) / RC.H * receipt.Ltex;
  const sTgt = lerp(sPost, sHl, sstep(PRINT1, HL0 + 0.1, t)); const sNow = sTgt - (receipt.Ltex - L);   // where that line is on the strip right now
  const a = receipt.pointAt(clamp(sNow, 0, L)), b = receipt.pointAt(clamp(sNow + 0.01, 0, L)); const tan = b.clone().sub(a).normalize();
  const side = V3(1, 0, 0).applyQuaternion(bot.torso.getWorldQuaternion(new THREE.Quaternion())); const nrm = new THREE.Vector3().crossVectors(side, tan).normalize(); if (nrm.z < 0) nrm.negate();
  const slot = bot.slotWorld();
  const k = easeIO(clamp((t - 174.98) / 0.9));
  const pA = slot.clone().add(V3(0.0, 0.03, 0.42)), lA = slot.clone().add(V3(0, -0.04, 0));
  const dist = lerp(0.19, 0.14, sstep(HL0 - 0.1, HL1 + 0.3, t)) * (VERT ? 1.6 : 1); const pB = a.clone().addScaledVector(nrm, dist), lB = a.clone();
  const p = pA.clone().lerp(pB, k), l = lA.clone().lerp(lB, k);
  if (VERT) VF = 2.0; cam.up.copy(tan.clone().negate()); cam.position.copy(p); cam.lookAt(l); cam.fov = vfov(30); cam.aspect = W / H; cam.updateProjectionMatrix();
  // 9:16: the receipt a size larger and lifted, so her post reads bigger and the slip's foot clears the caption zone
  return { camSet: true, balloons: [limitBalloon(t)], vshift: VERT ? [lerp(1, 1.15, k), 0.025 * k, 0.10 * k] : null };
}, 'the receipt');
shot(176.70, 180.45, async (t, u) => {          // "Hey ChatGPT?": through her eyes, her real screen recording lights up
  dusk(t, 'USAGE LIMIT REACHED', 0xff3b30);
  const zoom = easeIO(clamp((t - 178.32) / 0.85));
  const v = povPhone(t, { d: lerp(0.25, 0.24, zoom), hh: lerp(0.0022, 0.0008, zoom) });
  bot.root.visible = true; bot.pose(botSit(t, { headYaw: -0.3, headPitch: 0.26, headRoll: 0.1, lean: 0.14 })); bot.setEye('battery', t, { on: (t % 0.5) < 0.32 ? 1 : 0.3 }); bot.updateCord();
  const on = t < 176.78 ? 0 : Math.min(1, (t - 176.78) / 0.08) * (1 + 0.12 * Math.exp(-(t - 176.86) / 0.08) * (t > 176.86 ? 1 : 0));
  await phoneScreen(t, 0.8 * on);
  const tgt = phone.root.localToWorld(VERT ? phone.local(500, 470) : phone.local(560, 430)); const lk = v.lk.clone().lerp(tgt, zoom);
  if (VERT) VF = lerp(1.1, 2.55, zoom); look(v.p, lk, lerp(34, 13.5, zoom)); cam.up.copy(v.up); cam.lookAt(lk); cam.updateMatrixWorld(true);
  return { balloons: [{ who: 'her', lines: ['Hey ChatGPT?'], t0: LINES10.gpt, t1: 178.45, x: VERT ? W * 0.4 : W * 0.2, y: H * (VERT ? 0.36 : 0.42), tail: [W * 0.33, H * 0.62] }] };
}, 'hey chatgpt (pov)');
const TEND = VERT ? 186.4333 : T2 + 0.2;
shot(180.45, TEND, async (t, u) => {         // she's on her phone; next to her, the robot's battery dies. Fade to black.
  // 9:16: the sign lights once the pull-back is wide enough to hold it whole (from 181.6 it ran off both sides)
  dusk(t, VERT && t > 183.8 ? ((t % 1.2) < 0.8 ? 'USAGE 100%' : '') : '', 0xff3b30);
  her.root.visible = true; her.setFace(1, 0); herWithPhone(t, herBowed(t, { headPitch: 0.42, lean: 0.18, headYaw: -0.05 }), { d: 0.34 });
  await phoneScreen(180.62, 0.8); glow.position.copy(phone.root.position).add(V3(0, 0.06, 0.02)); glow.intensity = 0.1; glow.distance = 0.45;
  const dead = t >= 181.0; bot.root.visible = true; bot.pose(botSit(t, { headYaw: -0.25, headPitch: 0.3 + 0.12 * sstep(181.0, 181.35, t), headRoll: 0.12, lean: 0.16 + 0.04 * sstep(181.0, 181.35, t) }));
  bot.setEye(dead ? 'off' : 'battery', t, { on: (t % 0.5) < 0.32 ? 1 : 0.3 }); bot.updateCord();
  if (VERT) {
    hudPass.uniforms.uFade.value = easeIn(clamp((t - 185.95) / 0.45));
    const k = easeIO(clamp((t - 181.3) / 4.9)); VF = 1.45;
    const p = V3(lerp(0.06, 0.6, k), lerp(1.0, 1.25, k), lerp(3.6, 9.5, k)), l = V3(lerp(0.03, 0.1, k), lerp(0.95, 6.5, k), lerp(0, -20, k));
    look(p, l, lerp(30, 34, k));
    return { vshift: k > 0 ? [lerp(1, 0.86, k), 0.07 * Math.sqrt(k), 0] : null };   // the pull-back: USAGE 100% fits left of the button column
  }
  hudPass.uniforms.uFade.value = easeIn(clamp((t - 180.98) / 0.56));
  const p = V3(lerp(0.08, 0.04, u), lerp(1.08, 1.06, u), lerp(2.5, 2.38, u)); look(p, V3(0.03, 0.9, 0), 30);
  return {};
}, 'the battery dies');

// ---------------------------------------------------------------- per frame
function findShot(t) { for (const s of SHOTS) if (t >= s.a && t < s.b) return s; return null; }
const PROF = q.get('prof') === '1';
window.renderTime = async (t) => {
  const p0 = performance.now();
  resetFrame(t);
  const s = findShot(t); let v = {};
  if (!s) { applyMood(MOOD.night); look(V3(0, 1, 5), V3(0, 1, 0), 30); hudPass.uniforms.uFade.value = 1; }
  else { const u = clamp((t - s.a) / (s.b - s.a)); v = (await s.fn(t, u)) || {}; if (v.cam) look(...v.cam);
    if (v.vshift) { const [k, dx, dy] = v.vshift; cam.fov = 2 * Math.atan(Math.tan(cam.fov * Math.PI / 360) / k) * 180 / Math.PI; cam.setViewOffset(W, H, dx * W, dy * H, W, H); cam.updateProjectionMatrix(); } }
  if (her.root.visible) her.hairTick(t, { gk: 0.35 });
  const DBG = q.get('cam'); if (DBG) { const c = DBG.split(',').map(Number); look(V3(c[0], c[1], c[2]), V3(c[3], c[4], c[5]), c[6] || 30); v.balloons = []; }   // debug: a check camera
  if (PROF) { const X = q.get('x') || ''; bloom.enabled = !X.includes('b'); Wd.city.visible = !X.includes('c'); Wd.sky.visible = !X.includes('s'); finish.enabled = !X.includes('f'); for (const r of crowd) if (X.includes('r')) r.root.visible = false; if (X.includes('t')) Wd.tower.root.visible = false; }
  const p1 = performance.now(); drawHud(t, v.balloons);
  finish.uniforms.uTime.value = t;
  const p2 = performance.now(); composer.render(); const gl = renderer.getContext(); if (PROF) gl.finish();
  const p3 = performance.now(); const url = renderer.domElement.toDataURL('image/jpeg', 0.93);
  if (PROF) console.log(`prof t=${t.toFixed(2)} scene ${(p1 - p0) | 0} hud ${(p2 - p1) | 0} render ${(p3 - p2) | 0} jpeg ${(performance.now() - p3) | 0}`);
  return url;
};
window.renderAt = window.renderTime;

(async () => {
  await loadFonts();
  const [timed, beats] = await Promise.all([fetch('/data/timed.json').then((r) => r.json()), fetch('/data/beats.json').then((r) => r.json())]);
  LN = timed; BEATS = beats.beats; DOWN = beats.downbeats;
  for (const L of LN) if (L.text.toLowerCase().startsWith('look what i can do') && L.s > 160 && L.s < 172) HOOK.push(L.wt.slice(0, 5));
  if (HOOK.length !== 4) console.log('HOOKS?', HOOK.length);
  build();
  // footage that exists (more keys may arrive; a missing one is skipped)
  const ok = []; for (const f of FEED) { const r = await fetch(`/media/hd/${f[0]}/${String(f[3] - 1).padStart(3, '0')}.jpg`, { method: 'HEAD' }).catch(() => null); if (r && r.ok) ok.push(f); else console.log('feed: missing', f[0]); }
  FEED_OK = ok.length ? ok : FEED; console.log('feed clips', ok.length);
  receipt.img = await loadImg('/media/post_usage.png'); imgCache.delete('/media/post_usage.png');
  Wd.tower.screen.userData.g = Wd.tower.screen.image.getContext ? Wd.tower.screen.image.getContext('2d') : Wd.tower.screen.userData.g;
  window.ready = true;
})().catch((e) => { console.log('INIT ERROR', e.stack || e); });
