// SHORT G COPY (9:16 only) of web/js/stage.js — the published film keeps using web/js/stage.js, untouched.
// Changes: VCAMS (cameras re-framed for a phone: the LED wall at full phone width so the title reads, the chart and the
// chat framed close, the prompter glass fitted to the safe column); fov in VCAMS is HORIZONTAL and setCam converts it.
// Look What I Can Do · "Scope Creep" — stage.js: THE KEYNOTE (bridge, 122.94–136.54)
// An arena-sized keynote hall in the dark: a giant curved LED wall plays her real TED Talk videos, an empty podium waits
// on a red circle in a followspot, a thousand silhouettes sit in raked rows. "Ladies and gentlemen" is a crane down from
// the back of the hall; the title slide builds word by word with her voice; every "Next slide." hard-cuts the wall to the
// next TED video (flash, slide counter) and the camera to a new angle; Claude's offer to write the conclusion comes up on
// the teleprompter glass as a Claude Code prompt; she picks "No, I think I nailed it", the lights slam, the room stands,
// and the camera rises toward the roof where space.js takes over.
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import * as L from '../lib.js';
import * as M from '../media.js';
const { clamp, lerp, sstep, easeIO, easeOut, expOut, env, V3, ls, wt } = L;

let W = 1920, H = 1080, look, envTex;
let scene, cam, mirror;
const T = {};
const AMBER = '#ffa840', INK = '#ece6d8', GREEN = '#74e36a', PINK = '#ff5fa2';

// ---------------------------------------------------------------- layout (metres; stage floor y = 0, audience toward +z)
const WC = { x: 0, z: 16 }, WR = 28, WARC = 32, WSPAN = 32 / 28, WY0 = 1.0, WVID = 18, WBAND = 1.6, WH = WVID + WBAND;   // LED wall: arc centre, radius, arc length, bottom; a 16:9 video area over a black ticker band
const VB = WBAND / WH;
const POD = V3(0, 0, -4.2);            // the podium
const GLASS = V3(0, 1.5, -3.0);        // teleprompter glass centre (faces the speaker, upstage)
const CA = V3(0, 0, -5);               // centre of the seating arcs
const ROWS = 20, R0 = 12, RSTEP = 1.1, RAKE = 0.3, FLAT = 11, FLOOR0 = -1.0;      // a flat convention floor, then a gentle rake at the back
const rowR = (k) => R0 + k * RSTEP, rowY = (k) => FLOOR0 + Math.max(0, k - FLAT) * RAKE;

// ---------------------------------------------------------------- her TED videos, frame-accurate (own loader: the joke frames are picked by hand)
function loadImg(url) { return new Promise((res, rej) => { const im = new Image(); im.onload = () => res(im); im.onerror = () => rej(new Error('img ' + url)); im.src = url; }); }
function seqTex() { const t = new THREE.Texture(); t.colorSpace = THREE.SRGBColorSpace; t.generateMipmaps = true; t.minFilter = THREE.LinearMipmapLinearFilter; t.magFilter = THREE.LinearFilter; t.anisotropy = 8; t.userData.k = ''; return t; }
const AVG = new Map(); let avgC = null;
async function seqFrame(tex, name, idx) {
  idx = Math.max(1, Math.min(M.HERO[name], Math.round(idx)));
  const k = name + ':' + idx; if (tex.userData.k === k) return tex.userData.avg;
  const im = await loadImg(`/media/${name}/${String(idx).padStart(3, '0')}.jpg`);
  tex.image = im; tex.needsUpdate = true; tex.userData.k = k;
  if (!AVG.has(k)) {   // the average colour of this frame: the wall lights the room with it
    if (!avgC) { avgC = document.createElement('canvas'); avgC.width = 16; avgC.height = 9; }
    const g = avgC.getContext('2d', { willReadFrequently: true }); g.drawImage(im, 0, 0, 16, 9); const d = g.getImageData(0, 0, 16, 9).data;
    let r = 0, gg = 0, b = 0; for (let i = 0; i < d.length; i += 4) { r += d[i]; gg += d[i + 1]; b += d[i + 2]; } const n = d.length / 4;
    AVG.set(k, new THREE.Color().setRGB(r / n / 255, gg / n / 255, b / n / 255, THREE.SRGBColorSpace));
  }
  tex.userData.avg = AVG.get(k); return tex.userData.avg;
}
// what the wall plays when: [from, name, first frame, fps-ish rate]; the chart's MINUTES 18 / SLIDES 0 / POINTS 0 builds on 'Next slide.'
let PLAY = [];
function wallClip(t) { let c = PLAY[0]; for (const p of PLAY) if (t >= p.t) c = p; return { ...c, idx: c.f0 + (t - c.t) * c.rate, x: t - c.t }; }

// ---------------------------------------------------------------- the LED wall
function wallGeo(R, span, y0, h, nx = 96, ny = 2) {
  const pos = [], uv = [], idx = [];
  for (let j = 0; j <= ny; j++) for (let i = 0; i <= nx; i++) { const u = i / nx, v = j / ny, a = (u - 0.5) * span; pos.push(WC.x + R * Math.sin(a), y0 + v * h, WC.z - R * Math.cos(a)); uv.push(u, v); }
  for (let j = 0; j < ny; j++) for (let i = 0; i < nx; i++) { const a = j * (nx + 1) + i, b = a + 1, c = a + nx + 1, d = c + 1; idx.push(a, b, d, a, d, c); }
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2)); g.setIndex(idx); g.computeVertexNormals(); return g;
}
function wallMaterial(vid, slide) {
  return new THREE.ShaderMaterial({
    uniforms: { uVid: { value: vid }, uSlide: { value: slide }, uBand: { value: null }, uVb: { value: VB }, uDim: { value: 1 }, uFlash: { value: 0 }, uBright: { value: 1.2 }, uSlideA: { value: 0 },
      uWR: { value: Array.from({ length: 8 }, () => new THREE.Vector4(-1, -1, -1, -1)) }, uWK: { value: new Array(8).fill(1) }, uMod: { value: new THREE.Vector2(64, 36) }, uTitle: { value: 1 } },
    vertexShader: `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`,
    fragmentShader: `uniform sampler2D uVid, uSlide, uBand; uniform float uVb, uDim, uFlash, uBright, uSlideA; uniform vec4 uWR[8]; uniform float uWK[8]; uniform vec2 uMod; uniform float uTitle; varying vec2 vUv;
      void main(){
        if (!gl_FrontFacing) { gl_FragColor = vec4(0.004, 0.004, 0.006, 1.0); return; }
        vec2 su = vec2(vUv.x, (vUv.y - uVb) / (1.0 - uVb));
        vec3 c;
        if (vUv.y < uVb) { vec4 b = texture2D(uBand, vec2(vUv.x, vUv.y / uVb)); c = vec3(0.004) + b.rgb * b.a; }
        else {
          vec3 v = texture2D(uVid, su).rgb * uDim;
          vec4 s = texture2D(uSlide, su);
          float m = 1.0;                                   // title words wipe in left to right, each on its sung word
          if (uTitle > 0.5) for (int i = 0; i < 8; i++) { vec4 r = uWR[i]; if (su.x >= r.x && su.x <= r.z && su.y >= r.y && su.y <= r.w) { float e = mix(r.x - 0.012, r.z + 0.012, uWK[i]); m = 1.0 - smoothstep(e - 0.012, e, su.x); } }
          c = mix(v, s.rgb, s.a * m * uSlideA);
        }
        vec2 g = vUv * uMod; vec2 fw = fwidth(g); vec2 d = abs(fract(g) - 0.5);          // LED module seams, only where modules are big on screen
        float seam = max(smoothstep(0.5 - 0.025 - fw.x, 0.5 - 0.025, d.x), smoothstep(0.5 - 0.025 - fw.y, 0.5 - 0.025, d.y));
        float vis = 1.0 - smoothstep(0.025, 0.08, max(fw.x, fw.y));
        c *= 1.0 - 0.2 * seam * vis;
        float edge = smoothstep(0.0, 0.004, vUv.x) * smoothstep(0.0, 0.004, 1.0 - vUv.x) * smoothstep(0.0, 0.007, vUv.y) * smoothstep(0.0, 0.007, 1.0 - vUv.y);
        c = mix(c, vec3(1.0, 0.98, 0.95), uFlash) * uBright * edge;
        gl_FragColor = vec4(c, 1.0);
      }`,
    side: THREE.DoubleSide,
  });
}
// the slide layer (title + counter), redrawn only when the slide changes; word rects go to the shader for the wipe
const SW = 2048, SH = 1152;
let SLIDE = null;
function slideCanvas() { const c = document.createElement('canvas'); c.width = SW; c.height = SH; const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8; t.userData = { c, key: '', rects: [] }; return t; }
let BAND = null; const BW = 4096, BH = 205;
function bandCanvas() { const c = document.createElement('canvas'); c.width = BW; c.height = BH; const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8; t.userData = { c, key: '' }; return t; }
function drawBand(n) {   // the ticker under the video: a hairline progress bar across the wall + the slide count
  const S = BAND.userData; if (S.key === String(n)) return; S.key = String(n);
  const g = S.c.getContext('2d'); g.clearRect(0, 0, BW, BH);
  g.fillStyle = 'rgba(236,230,216,0.18)'; g.fillRect(0, 18, BW, 8);
  if (n > 0) { g.fillStyle = AMBER; g.shadowColor = AMBER; g.shadowBlur = 18; g.fillRect(0, 16, BW * n / 40, 12); g.shadowBlur = 0;
    g.font = `120px ${L.FONT.monoB}`; g.textBaseline = 'middle'; g.textAlign = 'right'; g.fillStyle = INK; g.fillText(`${n} / 40`, BW * 0.86, 118);
    g.font = `76px ${L.FONT.serifI}`; g.textAlign = 'left'; g.fillStyle = 'rgba(236,230,216,0.7)'; g.fillText('the greatest transformation in human history — adita', BW * 0.1, 122); }
  BAND.needsUpdate = true;
}
function drawSlide(state) {   // state: 'title' | 2..5 (counter)
  const S = SLIDE.userData; if (S.key === String(state)) return; S.key = String(state);
  const g = S.c.getContext('2d'); g.clearRect(0, 0, SW, SH); S.rects = [];
  if (state === 'title') {
    const fit = (txt, maxW, size, font) => { g.font = `${size}px ${font}`; const w = g.measureText(txt).width; return w > maxW ? size * maxW / w : size; };
    const l1 = ['THE', 'GREATEST', 'TRANSFORMATION'], l2 = ['IN', 'HUMAN', 'HISTORY'];
    const size = Math.min(fit(l1.join(' '), SW * 0.84, 260, L.FONT.anton), fit(l2.join(' '), SW * 0.84, 260, L.FONT.anton));
    const line = (words, y, color) => {
      g.font = `${size}px ${L.FONT.anton}`; g.textBaseline = 'alphabetic'; const sp = g.measureText(' ').width;
      const ws = words.map((w) => g.measureText(w).width); const tot = ws.reduce((a, b) => a + b, 0) + sp * (words.length - 1);
      let x = (SW - tot) / 2;
      words.forEach((w, i) => {
        g.shadowColor = 'rgba(0,0,0,0.55)'; g.shadowBlur = 30; g.fillStyle = color; g.fillText(w, x, y); g.shadowBlur = 0;
        S.rects.push([x - 6, y - size * 0.86, x + ws[i] + 6, y + size * 0.08]); x += ws[i] + sp;
      });
    };
    line(l1, SH * 0.43, INK); line(l2, SH * 0.43 + size * 1.04, AMBER);
    g.font = `${Math.round(size * 0.36)}px ${L.FONT.serifI}`; g.fillStyle = 'rgba(236,230,216,0.86)'; g.textAlign = 'center';
    const ty = SH * 0.43 + size * 1.04 + size * 0.62; g.fillText('a talk by adita', SW / 2, ty); const tw = g.measureText('a talk by adita').width;
    S.rects.push([SW / 2 - tw / 2 - 8, ty - size * 0.32, SW / 2 + tw / 2 + 8, ty + size * 0.1]); g.textAlign = 'left';
  }
  SLIDE.needsUpdate = true;
}

// ---------------------------------------------------------------- the teleprompter: Claude Code's prompt on glass
const PW = 1280, PH = 800;
let PROMPT = null;
function promptCanvas() { const c = document.createElement('canvas'); c.width = PW; c.height = PH; const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8; t.userData = { c, key: '' }; return t; }
function drawPrompt(typed, optA, sel) {
  const key = typed + ':' + optA.toFixed(2) + ':' + sel; const P = PROMPT.userData; if (P.key === key) return; P.key = key;
  const g = P.c.getContext('2d'); g.clearRect(0, 0, PW, PH);
  const glow = (col, blur) => { g.shadowColor = col; g.shadowBlur = blur; };
  g.strokeStyle = 'rgba(255,168,64,0.55)'; g.lineWidth = 4; glow(AMBER, 14); g.beginPath(); g.roundRect(40, 40, PW - 80, PH - 80, 30); g.stroke();
  g.textBaseline = 'alphabetic'; const x0 = 100;
  const title = 'Generate a conclusion?';
  g.font = `76px ${L.FONT.monoB}`; let fs = 76; while (g.measureText(title).width > PW - 2 * x0 && fs > 40) { fs -= 2; g.font = `${fs}px ${L.FONT.monoB}`; }
  glow(AMBER, 22); g.fillStyle = AMBER; g.fillText(title.slice(0, typed), x0, 205);
  if (typed > 0 && typed < title.length) { const w = g.measureText(title.slice(0, typed)).width; g.fillRect(x0 + w + 6, 205 - fs * 0.78, fs * 0.5, fs * 0.92); }
  if (optA > 0) {   // SHORT G: options at the title's size (76 px canvas = lyric size on a phone), the long one wrapped
    g.globalAlpha = optA;
    const rows = [['1. Yes'], ['2. No, I think', '   I nailed it']];
    g.font = `76px ${L.FONT.monoB}`; const pre = g.measureText('❯ ').width;
    let y = 340;
    rows.forEach((r, i) => {
      const on = i === sel; const col = on ? (sel === 1 ? GREEN : AMBER) : 'rgba(236,230,216,0.62)';
      glow(on ? col : 'rgba(0,0,0,0)', on ? 24 : 0); g.fillStyle = col;
      if (on) g.fillText('❯', x0, y);
      r.forEach((ln, j) => { g.fillText(ln, x0 + pre, y + j * 92); });
      y += 120 + (r.length - 1) * 92;
    });
    g.shadowBlur = 0; g.font = `40px ${L.FONT.mono}`; g.fillStyle = 'rgba(236,230,216,0.42)'; g.fillText('Enter to confirm · Esc to cancel', x0, PH - 82);
    g.globalAlpha = 1;
  }
  g.shadowBlur = 0; PROMPT.needsUpdate = true;
}

// ---------------------------------------------------------------- light beams (soft additive cones in the haze)
function beamMaterial(color, opacity = 0.1) {
  return new THREE.ShaderMaterial({
    uniforms: { uCol: { value: new THREE.Color(color) }, uA: { value: opacity } },
    vertexShader: `varying float vY; varying vec3 vN; varying vec3 vV; void main(){ vY = uv.y; vec4 mv = modelViewMatrix * vec4(position, 1.0); vN = normalize(normalMatrix * normal); vV = normalize(-mv.xyz); gl_Position = projectionMatrix * mv; }`,
    fragmentShader: `uniform vec3 uCol; uniform float uA; varying float vY; varying vec3 vN; varying vec3 vV;
      void main(){ float f = pow(abs(dot(normalize(vN), normalize(vV))), 1.8); float a = uA * f * pow(vY, 1.3) * smoothstep(0.0, 0.25, vY) * (1.0 - smoothstep(0.97, 1.0, vY));
        gl_FragColor = vec4(uCol * a, 1.0); }`,
    transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide,
  });
}
function beamMesh(len, radius, mat) {   // apex at the origin, pointing down -y; aim with aimBeam()
  const g = new THREE.ConeGeometry(radius, len, 18, 1, true); g.translate(0, -len / 2, 0);
  const m = new THREE.Mesh(g, mat); m.frustumCulled = false; return m;
}
const _q = new THREE.Quaternion(), _d = new THREE.Vector3(), DOWN = V3(0, -1, 0);
function aimBeam(m, from, to, radiusAtEnd) {
  _d.subVectors(to, from); const len = _d.length(); _d.normalize();
  m.position.copy(from); m.quaternion.setFromUnitVectors(DOWN, _d);
  const g = m.geometry.parameters; m.scale.set(radiusAtEnd / g.radius, len / g.height, radiusAtEnd / g.radius);
}

// a rim term for the audience silhouettes (their edges catch the wall's light)
function rimify(mat, uni) {
  mat.onBeforeCompile = (sh) => {
    sh.uniforms.uRim = uni;
    sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\nuniform vec3 uRim;')
      .replace('#include <emissivemap_fragment>', '#include <emissivemap_fragment>\n totalEmissiveRadiance += uRim * pow(1.0 - clamp(abs(dot(normal, normalize(vViewPosition))), 0.0, 1.0), 3.5);');
  };
  mat.customProgramCacheKey = () => 'rim';
}

// ---------------------------------------------------------------- build
let WALL, WALLM, wallMat, vidTex, lights = {}, BEAMS = [], FOLLOW, POOL, PODIUM, PROMPTM, GLASSM, CROWD, ARMS, PHONES, SEATS, PEOPLE = [], RIM = { value: new THREE.Color(0, 0, 0) };
let CAMS0 = null, crowdKey = '';
function personGeo() {
  const head = new THREE.SphereGeometry(0.105, 8, 6); head.scale(1, 1.12, 1.05); head.translate(0, 0.76, 0);
  const torso = new THREE.SphereGeometry(0.2, 8, 6); torso.scale(1.18, 1.5, 0.62); torso.translate(0, 0.30, 0);
  return mergeGeometries([head, torso]);
}
function armsGeo() {
  const a = new THREE.CylinderGeometry(0.03, 0.04, 0.58, 5, 1, false); a.translate(0, 0.29, 0);
  const l = a.clone(); l.rotateZ(0.38); l.translate(-0.19, 0.5, 0);
  const r = a.clone(); r.rotateZ(-0.38); r.translate(0.19, 0.5, 0);
  return mergeGeometries([l, r]);
}
function rakeGeo() {   // the raked seating floor: a cone section under the rows
  const pos = [], idx = []; const nr = ROWS + 4, na = 48, a0 = -1.1, a1 = 1.1;
  for (let j = 0; j <= nr; j++) for (let i = 0; i <= na; i++) {
    const r = R0 - 2.2 + j * RSTEP; const a = a0 + (a1 - a0) * i / na; const k = (r - R0) / RSTEP; const y = rowY(Math.max(0, Math.round(k)));
    pos.push(CA.x + Math.sin(a) * r, y, CA.z + Math.cos(a) * r);
  }
  for (let j = 0; j < nr; j++) for (let i = 0; i < na; i++) { const a = j * (na + 1) + i, b = a + 1, c = a + na + 1, d = c + 1; idx.push(a, d, b, a, c, d); }
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); g.setIndex(idx); g.computeVertexNormals(); return g;
}
function slatTex() {
  return L.canvasTex(512, 64, (g, w, h) => { g.fillStyle = '#0d0d11'; g.fillRect(0, 0, w, h); for (let x = 0; x < w; x += 32) { g.fillStyle = '#16161c'; g.fillRect(x, 0, 18, h); g.fillStyle = '#060608'; g.fillRect(x + 18, 0, 3, h); } }, { repeat: [6, 1] });
}
function exitSign() {
  const tx = L.canvasTex(256, 96, (g, w, h) => { g.fillStyle = '#062b12'; g.fillRect(0, 0, w, h); g.fillStyle = '#3dff7a'; g.font = `64px ${L.FONT.disp}`; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText('EXIT', w / 2, h / 2 + 3); });
  const m = new THREE.Mesh(new THREE.PlaneGeometry(0.9, 0.34), new THREE.MeshBasicMaterial({ map: tx, toneMapped: false })); m.material.color.setScalar(1.4); return m;
}

function buildHall() {
  scene = new THREE.Scene(); scene.background = new THREE.Color(0x020203); scene.fog = new THREE.FogExp2(0x030305, 0.011);
  cam = new THREE.PerspectiveCamera(36, W / H, 0.05, 400); scene.add(cam);
  // lights: followspot on the podium, the wall's own light (its colour follows the video), house lights, a front wash for the slam
  lights.spot = new THREE.SpotLight(0xfff0dc, 6, 0, 0.026, 0.6, 0); lights.spot.position.set(0, 21, 30); lights.spot.target.position.set(POD.x, 1.2, POD.z - 0.35); scene.add(lights.spot, lights.spot.target);
  lights.wall = new THREE.DirectionalLight(0xffffff, 1.0); lights.wall.position.set(0, 10, -12); lights.wall.target.position.set(0, 0, 20); scene.add(lights.wall, lights.wall.target);
  lights.hemi = new THREE.HemisphereLight(0x5a6890, 0x0a0a0c, 0.12); scene.add(lights.hemi);

  // stage: black glass floor (a mirror world under it), front face with a warm LED strip, the red circle around the podium
  mirror = new THREE.Group(); mirror.scale.y = -1; scene.add(mirror);
  const fm = new THREE.MeshBasicMaterial({ color: 0x010102, transparent: true, opacity: 0.84 });
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(36, 14.5), fm); floor.rotation.x = -Math.PI / 2; floor.position.set(0, 0, -7.25); floor.renderOrder = 5; scene.add(floor);
  const front = new THREE.Mesh(new THREE.PlaneGeometry(36, 1.0), new THREE.MeshStandardMaterial({ color: 0x050506, roughness: 0.6, metalness: 0.3, envMap: envTex, envMapIntensity: 0.3 }));
  front.position.set(0, -0.5, 0); scene.add(front);
  const strip = new THREE.Mesh(new THREE.PlaneGeometry(36, 0.025), new THREE.MeshBasicMaterial({ color: new THREE.Color(1.6, 0.9, 0.5), toneMapped: false })); strip.position.set(0, -0.03, 0.002); scene.add(strip);
  const rug = new THREE.Mesh(new THREE.CircleGeometry(2.7, 72), new THREE.MeshStandardMaterial({ color: 0x8a0f1c, roughness: 0.95, metalness: 0, envMap: envTex, envMapIntensity: 0.05 }));
  rug.rotation.x = -Math.PI / 2; rug.position.set(POD.x, 0.006, POD.z + 0.6); rug.renderOrder = 6; scene.add(rug);
  POOL = new THREE.Mesh(new THREE.CircleGeometry(2.2, 48), new THREE.MeshBasicMaterial({ map: L.dotTex(), color: new THREE.Color(1.0, 0.86, 0.7), transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false, opacity: 0.5 }));
  POOL.rotation.x = -Math.PI / 2; POOL.position.set(POD.x, 0.012, POD.z + 0.25); POOL.renderOrder = 7; scene.add(POOL);
  // pit floor + the raked seating floor
  const carpet = new THREE.MeshStandardMaterial({ color: 0x0b0b10, roughness: 0.95, metalness: 0 });
  const pit = new THREE.Mesh(new THREE.PlaneGeometry(52, 12), carpet); pit.rotation.x = -Math.PI / 2; pit.position.set(0, FLOOR0, 5); scene.add(pit);
  scene.add(new THREE.Mesh(rakeGeo(), carpet));
  // the hall: slatted side walls, back wall with the control booth, black ceiling with tiny downlights, black drape behind the wall
  const wallM = new THREE.MeshStandardMaterial({ map: slatTex(), roughness: 0.85, metalness: 0.1, color: 0x9a9aa6 });
  for (const s of [-1, 1]) { const sw = new THREE.Mesh(new THREE.PlaneGeometry(52, 28), wallM); sw.position.set(s * 25, 12, 11); sw.rotation.y = -s * Math.PI / 2; scene.add(sw);
    for (let k = 0; k < 7; k++) { const sc = new THREE.Mesh(new THREE.PlaneGeometry(0.08, 2.2), new THREE.MeshBasicMaterial({ color: new THREE.Color(1.2, 0.8, 0.5), toneMapped: false })); sc.position.set(s * 24.95, 4.5 + k * 0.0, -6 + k * 6.2); sc.rotation.y = -s * Math.PI / 2; scene.add(sc); }
    const ex = exitSign(); ex.position.set(s * 24.9, 3.2, 3.5); ex.rotation.y = -s * Math.PI / 2; scene.add(ex); }
  const back = new THREE.Mesh(new THREE.PlaneGeometry(52, 28), wallM); back.position.set(0, 12, 37); back.rotation.y = Math.PI; scene.add(back);
  const booth = new THREE.Mesh(new THREE.PlaneGeometry(9, 1.6), new THREE.MeshBasicMaterial({ color: new THREE.Color(0.55, 0.36, 0.2), toneMapped: false })); booth.position.set(0, 14.5, 36.9); booth.rotation.y = Math.PI; scene.add(booth);
  const drape = new THREE.Mesh(new THREE.PlaneGeometry(60, 30), new THREE.MeshBasicMaterial({ color: 0x010101 })); drape.position.set(0, 12, -14.5); scene.add(drape);
  const ceil = new THREE.Mesh(new THREE.PlaneGeometry(52, 52), new THREE.MeshBasicMaterial({ color: 0x020203 })); ceil.rotation.x = Math.PI / 2; ceil.position.set(0, 26, 11); scene.add(ceil);
  { const R = L.rng(77); const pts = []; for (let i = 0; i < 160; i++) pts.push(-23 + R() * 46, 25.9, -12 + R() * 48);
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(pts, 3));
    scene.add(new THREE.Points(g, new THREE.PointsMaterial({ map: L.dotTex(), size: 0.22, color: new THREE.Color(1.0, 0.75, 0.45), transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false }))); }
  // aisle step lights
  { const pts = []; for (const a of [-0.3, 0.3]) for (let k = 0; k < ROWS; k++) { const r = rowR(k) - 0.45; pts.push(CA.x + Math.sin(a) * r, rowY(k) + 0.04, CA.z + Math.cos(a) * r); }
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(pts, 3));
    scene.add(new THREE.Points(g, new THREE.PointsMaterial({ map: L.dotTex(), size: 0.16, color: new THREE.Color(1.4, 0.8, 0.35), transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false }))); }

  // the LED wall (+ its reflection in the stage floor)
  vidTex = seqTex(); SLIDE = slideCanvas(); BAND = bandCanvas(); drawBand(0); wallMat = wallMaterial(vidTex, SLIDE); wallMat.uniforms.uBand.value = BAND;
  const wg = wallGeo(WR, WSPAN, WY0, WH);
  WALL = new THREE.Mesh(wg, wallMat); scene.add(WALL);
  const mirrorMat = new THREE.ShaderMaterial({ uniforms: wallMat.uniforms,
    vertexShader: `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`,
    fragmentShader: `uniform sampler2D uVid, uSlide; uniform float uVb, uDim, uFlash, uBright, uSlideA; varying vec2 vUv;
      void main(){ if (vUv.y < uVb) { gl_FragColor = vec4(vec3(0.004), 1.0); return; } vec2 su = vec2(vUv.x, (vUv.y - uVb) / (1.0 - uVb));
        vec4 s = texture2D(uSlide, su); vec3 c = mix(texture2D(uVid, su).rgb * uDim, s.rgb, s.a * uSlideA); gl_FragColor = vec4(mix(c, vec3(1.0), uFlash) * uBright, 1.0); }`,
    side: THREE.DoubleSide });
  WALLM = new THREE.Mesh(wg, mirrorMat); mirror.add(WALLM);
  const frameM = new THREE.MeshStandardMaterial({ color: 0x0a0a0c, roughness: 0.5, metalness: 0.6, envMap: envTex, envMapIntensity: 0.3 });
  const backing = new THREE.Mesh(wallGeo(WR + 0.25, WSPAN * 1.012, WY0 - 0.25, WH + 0.5, 64, 1), frameM); scene.add(backing);

  // truss, fixtures and beams
  const trussM = new THREE.MeshStandardMaterial({ color: 0x1a1a1f, roughness: 0.4, metalness: 0.9, envMap: envTex, envMapIntensity: 0.4 });
  const R = L.rng(9);
  for (const z of [-3.6, -8.4]) {
    for (const dy of [0, 0.5]) for (const dz of [-0.25, 0.25]) { const b = new THREE.Mesh(new THREE.BoxGeometry(34, 0.06, 0.06), trussM); b.position.set(0, 22.6 + dy, z + dz); scene.add(b); }
    for (let i = 0; i < 7; i++) {
      const x = -13.8 + i * 4.6; const fx = new THREE.Mesh(new THREE.CylinderGeometry(0.2, 0.26, 0.55, 12), trussM); fx.position.set(x, 22.2, z); scene.add(fx);
      const warm = (i + (z < -5 ? 1 : 0)) % 3 === 0;
      const mat = beamMaterial(warm ? 0xffd9b0 : (i % 2 ? 0x5a4dff : 0xc04dff), 0.05);
      const m = beamMesh(1, 1, mat); scene.add(m);
      const lens = new THREE.Mesh(new THREE.CircleGeometry(0.17, 16), new THREE.MeshBasicMaterial({ color: new THREE.Color(mat.uniforms.uCol.value).multiplyScalar(2.2), toneMapped: false }));
      lens.position.set(x, 21.92, z); lens.rotation.x = Math.PI / 2; scene.add(lens);
      BEAMS.push({ m, mat, lens, from: V3(x, 21.9, z), warm, ph: R() * 6.28, sp: 0.25 + R() * 0.3, side: x < 0 ? -1 : 1, i, z, base: mat.uniforms.uCol.value.clone() });
    }
  }
  FOLLOW = beamMesh(1, 1, beamMaterial(0xfff2e0, 0.075)); scene.add(FOLLOW); aimBeam(FOLLOW, lights.spot.position, POD.clone().add(V3(0, 0.0, 0.3)), 1.15);

  // the podium: graphite lectern, slanted top, an amber accent line, a gooseneck mic
  PODIUM = new THREE.Group(); PODIUM.position.copy(POD);
  const pm = new THREE.MeshStandardMaterial({ color: 0x16161a, roughness: 0.32, metalness: 0.55, envMap: envTex, envMapIntensity: 0.7 });
  const body = new THREE.Mesh(new RoundedBoxGeometry(0.66, 1.02, 0.46, 4, 0.03), pm); body.position.y = 0.51; PODIUM.add(body);
  const top = new THREE.Mesh(new RoundedBoxGeometry(0.76, 0.05, 0.56, 3, 0.02), new THREE.MeshStandardMaterial({ color: 0x0c0c0f, roughness: 0.75, metalness: 0.2, envMap: envTex, envMapIntensity: 0.3 })); top.position.set(0, 1.07, -0.02); top.rotation.x = -0.2; PODIUM.add(top);
  const accent = new THREE.Mesh(new THREE.PlaneGeometry(0.5, 0.012), new THREE.MeshBasicMaterial({ color: new THREE.Color(2.2, 1.2, 0.45), toneMapped: false })); accent.position.set(0, 0.86, 0.232); PODIUM.add(accent);
  const neck = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3([V3(0.12, 1.06, -0.1), V3(0.13, 1.25, -0.02), V3(0.08, 1.36, 0.1)]), 12, 0.006, 6), pm); PODIUM.add(neck);
  const mic = new THREE.Mesh(new THREE.CylinderGeometry(0.014, 0.011, 0.06, 10), new THREE.MeshStandardMaterial({ color: 0x0c0c0e, roughness: 0.6 })); mic.position.set(0.075, 1.375, 0.125); mic.rotation.x = 1.0; PODIUM.add(mic);
  scene.add(PODIUM); const PM = PODIUM.clone(); mirror.add(PM);

  // the teleprompter: a tilted glass pane on a pole with its monitor hood, facing the speaker; Claude's prompt on it
  PROMPT = promptCanvas(); drawPrompt(0, 0, 0);
  const tp = new THREE.Group(); tp.position.copy(GLASS);
  const gw = 0.96, gh = 0.6;
  GLASSM = new THREE.Mesh(new THREE.PlaneGeometry(gw, gh), new THREE.MeshBasicMaterial({ color: 0x06090c, transparent: true, opacity: 0.42, depthWrite: false, side: THREE.DoubleSide }));
  PROMPTM = new THREE.Mesh(new THREE.PlaneGeometry(gw, gh), new THREE.MeshBasicMaterial({ map: PROMPT, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false }));
  PROMPTM.material.color.setScalar(1.5); PROMPTM.position.z = 0.002;
  const pane = new THREE.Group(); pane.add(GLASSM, PROMPTM);
  const edgeM = new THREE.MeshStandardMaterial({ color: 0x08080a, roughness: 0.7, metalness: 0.3, envMap: envTex, envMapIntensity: 0.25 });
  for (const [w, h, x, y] of [[gw + 0.03, 0.015, 0, gh / 2], [gw + 0.03, 0.015, 0, -gh / 2], [0.015, gh, gw / 2, 0], [0.015, gh, -gw / 2, 0]]) { const e = new THREE.Mesh(new THREE.BoxGeometry(w, h, 0.012), edgeM); e.position.set(x, y, 0); pane.add(e); }
  pane.rotation.set(0.12, Math.PI, 0); tp.add(pane);        // faces upstage, toward the speaker's eyes
  const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.014, 0.014, GLASS.y - 0.3, 8), edgeM); pole.position.set(0, -(GLASS.y - 0.3) / 2 - 0.3, 0.02); tp.add(pole);
  const foot = new THREE.Mesh(new THREE.CylinderGeometry(0.2, 0.22, 0.03, 20), edgeM); foot.position.set(0, -GLASS.y + 0.015, 0.02); tp.add(foot);
  scene.add(tp); const tpm = tp.clone(); const pc = tpm.children[0]; pc.remove(pc.children[0], pc.children[1]); mirror.add(tpm);

  // the audience: raked arcs of seats, ~90% full; silhouettes face the stage
  const R2 = L.rng(31);
  for (let k = 0; k < ROWS; k++) {
    const r = rowR(k); const amax = Math.min(0.92, Math.asin(Math.min(1, 23 / r))); const n = Math.floor(2 * amax * r / 0.58);
    for (let i = 0; i < n; i++) {
      const a = -amax + (i + 0.5) / n * 2 * amax;
      if (Math.abs(Math.abs(a) - 0.3) * r < 0.75) continue;            // the two aisles
      const x = CA.x + Math.sin(a) * r, z = CA.z + Math.cos(a) * r;
      const p = { x, z, a, k, y: rowY(k), seat: true, filled: R2() < 0.9, s: 0.9 + R2() * 0.22, sw: 0.9 + R2() * 0.25, lean: (R2() - 0.5) * 0.12, tilt: (R2() - 0.5) * 0.25,
        stand: R2() * 0.4 + k * 0.012, arms: R2() < 0.45, phone: R2(), wave: R2() * 6 };
      PEOPLE.push(p);
    }
  }
  const people = PEOPLE.filter((p) => p.filled);
  const crowdM = new THREE.MeshStandardMaterial({ color: 0x1e1e26, roughness: 0.9, metalness: 0.0 }); rimify(crowdM, RIM);
  CROWD = new THREE.InstancedMesh(personGeo(), crowdM, people.length); CROWD.userData.people = people; CROWD.frustumCulled = false; scene.add(CROWD);
  ARMS = new THREE.InstancedMesh(armsGeo(), crowdM, people.length); ARMS.frustumCulled = false; scene.add(ARMS);
  PHONES = new THREE.InstancedMesh(new THREE.PlaneGeometry(0.075, 0.14), new THREE.MeshBasicMaterial({ map: vidTex, toneMapped: false, side: THREE.DoubleSide }), people.length);
  PHONES.material.color.setScalar(1.25); PHONES.frustumCulled = false; scene.add(PHONES);
  SEATS = new THREE.InstancedMesh(new THREE.BoxGeometry(0.5, 0.6, 0.07), new THREE.MeshStandardMaterial({ color: 0x15151c, roughness: 0.8 }), PEOPLE.length);
  const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), s = new THREE.Vector3(1, 1, 1);
  PEOPLE.forEach((p, i) => { q.setFromAxisAngle(V3(0, 1, 0), p.a); const rr = rowR(p.k) + 0.3; m4.compose(V3(CA.x + Math.sin(p.a) * rr, p.y + 0.72, CA.z + Math.cos(p.a) * rr), q, s); SEATS.setMatrixAt(i, m4); });
  SEATS.frustumCulled = false; scene.add(SEATS);
}

const _m = new THREE.Matrix4(), _qq = new THREE.Quaternion(), _s = new THREE.Vector3(), _p = new THREE.Vector3(), _e = new THREE.Euler();
function poseCrowd(t) {   // seated, then the standing ovation after 'nailed it'; phones up (filming the wall)
  const stand0 = T.nailed + 0.06;
  const key = t < stand0 ? (t < T.ns1 ? 'a' : 'b') : String(Math.round(t * 60));
  if (key === crowdKey) return; crowdKey = key;
  const people = CROWD.userData.people;
  people.forEach((p, i) => {
    const st = easeOut((t - stand0 - p.stand) / 0.32);
    const y = p.y + 0.42 + st * 0.5;
    _e.set(p.lean * (1 - st), p.a + Math.PI + p.tilt * 0.3, 0); _qq.setFromEuler(_e);
    _s.set(p.sw * p.s, p.s * (1 + st * 0.12), p.s); _m.compose(_p.set(p.x, y, p.z), _qq, _s); CROWD.setMatrixAt(i, _m);
    const ka = p.arms ? easeOut((t - stand0 - p.stand - 0.12) / 0.3) : 0;
    _s.set(p.s, Math.max(0.0001, ka) * p.s * (1 + 0.06 * Math.sin((t - stand0) * 9 + p.wave)), p.s); _m.compose(_p.set(p.x, y + 0.18, p.z), _qq, _s); ARMS.setMatrixAt(i, _m);
    // phones: a few film the talk; many more come up for the ovation
    const onTalk = p.phone < 0.035, onOv = p.phone < 0.16 && st > 0.6;
    const kp = onTalk ? 1 : onOv ? easeOut((t - stand0 - p.stand - 0.25) / 0.25) : 0;
    _s.setScalar(Math.max(0.0001, kp)); _m.compose(_p.set(p.x - Math.sin(p.a) * 0.18, y + (st > 0.5 ? 1.12 : 0.72), p.z - Math.cos(p.a) * 0.18), _qq, _s); PHONES.setMatrixAt(i, _m);
  });
  CROWD.instanceMatrix.needsUpdate = true; ARMS.instanceMatrix.needsUpdate = true; PHONES.instanceMatrix.needsUpdate = true;
}

// ---------------------------------------------------------------- camera: one continuous move per shot, hard cuts on 'Next slide.'
const aisle = (r, y) => [-Math.sin(0.3) * r, y, CA.z + Math.cos(0.3) * r];     // the left aisle, r from the arcs' centre
const easeInLin = (x, a = 0.4) => { x = clamp(x); const n = 1 / (1 - a / 2); return x < a ? n * x * x / (2 * a) : n * (x - a / 2); };   // smooth start, then constant speed
function track(keys, ease = easeIO) {
  const P = new THREE.CatmullRomCurve3(keys.map((k) => V3(...k.p)), false, 'centripetal');
  const Lc = new THREE.CatmullRomCurve3(keys.map((k) => V3(...k.l)), false, 'centripetal');
  const t0 = keys[0].t, t1 = keys[keys.length - 1].t, n = keys.length;
  return (t) => {
    const tau = t0 + ease(clamp((t - t0) / (t1 - t0))) * (t1 - t0);
    let i = 0; while (i < n - 2 && tau > keys[i + 1].t) i++;
    const f = clamp((tau - keys[i].t) / (keys[i + 1].t - keys[i].t)); const u = (i + f) / (n - 1);
    return { p: P.getPoint(u), l: Lc.getPoint(u), fov: lerp(keys[i].fov, keys[i + 1].fov, f), roll: lerp(keys[i].roll || 0, keys[i + 1].roll || 0, f) };
  };
}
function buildCams() {
  const t0 = T.lad - 0.45;
  CAMS0 = {
    crane: track([
      { t: t0, p: [-9.6, 16.5, 33.0], l: [-1.4, 9.0, -12], fov: 40 },
      { t: T.lad + 1.5, p: aisle(30.5, 8.2), l: [-1.1, 9.6, -12], fov: 40 },
      { t: T.the + 0.3, p: aisle(26.6, 3.2), l: [-0.9, 8.4, -12], fov: 46 },
      { t: T.ns1, p: aisle(24.4, 0.5), l: [-0.8, 5.9, -12], fov: 54 },
    ], easeInLin),   // eases in, keeps drifting into the cut
    wide: track([{ t: T.ns1, p: [0.6, 6.6, 17.6], l: [0.1, 9.6, -12], fov: 40 }, { t: T.ns2, p: [0.4, 6.4, 16.3], l: [0.1, 9.6, -12], fov: 40 }], (x) => x),
    side: track([{ t: T.ns2, p: [15.2, 3.6, 4.2], l: [0.2, 6.8, -9.8], fov: 46 }, { t: T.ns3, p: [14.2, 3.4, 3.3], l: [-0.2, 6.7, -9.8], fov: 45 }], (x) => x),
    low: track([{ t: T.ns3, p: [2.9, 0.3, 1.5], l: [-1.3, 5.2, -9], fov: 42 }, { t: T.concl, p: [2.4, 0.36, 0.8], l: [-1.2, 5.1, -9], fov: 41 }], (x) => x),
    prompt: track([{ t: T.concl, p: [-0.24, 1.86, -5.05], l: [0.0, 1.53, -3.0], fov: 30 }, { t: T.rise, p: [-0.12, 1.8, -4.62], l: [0.0, 1.54, -3.0], fov: 30 }], (x) => x),
  };
}

let VCAMS = null;
function buildVCams() {   // 9:16: fov here is horizontal (degrees); setCam turns it into the vertical fov for the frame
  const t0 = T.lad - 0.45;
  VCAMS = {
    crane: track([   // opens close on the shadow play (the wall overflows the phone frame: a full, readable cover), then pulls back so the title fits
      { t: t0, p: [0.6, 10.4, 12.5], l: [0.9, 10.6, -12], fov: 44 },
      { t: T.lad + 1.5, p: [-0.8, 10.4, 19.0], l: [0.0, 10.9, -12], fov: 46 },
      { t: T.the + 0.3, p: [-1.0, 10.0, 25.0], l: [1.1, 11.2, -12], fov: 48 },
      { t: T.ns1, p: [-1.4, 9.6, 26.0], l: [1.1, 11.2, -12], fov: 48.5 },
    ], easeInLin),
    wide: track([{ t: T.ns1, p: [0.6, 6.2, 22.5], l: [1.4, 11.4, -12], fov: 48 }, { t: T.ns2, p: [0.6, 6.0, 21.5], l: [1.4, 11.4, -12], fov: 48 }], (x) => x),
    side: track([{ t: T.ns2, p: [-1.6, 1.0, 12.5], l: [0.0, 10.2, -12], fov: 62 }, { t: T.ns3, p: [-1.4, 1.1, 11.6], l: [0.0, 10.3, -12], fov: 61 }], (x) => x),
    low: track([{ t: T.ns3, p: [3.2, 9.0, 9.5], l: [4.3, 10.6, -11], fov: 56 }, { t: T.concl, p: [3.1, 9.0, 8.8], l: [4.3, 10.6, -11], fov: 56 }], (x) => x),
    prompt: track([{ t: T.concl, p: [-0.03, 1.62, -5.05], l: [-0.03, 1.5, -3.0], fov: 27.4 }, { t: T.rise + 0.5, p: [-0.03, 1.61, -4.98], l: [-0.03, 1.5, -3.0], fov: 27.2 }], (x) => x),
  };
}

// ---------------------------------------------------------------- build entry
export async function build(ctx) {
  ({ W, H, look } = ctx); envTex = look.envTex;
  T.lad = ls('Ladies and gentlemen');
  const L2 = 'We are living through the greatest transformation';
  T.the = wt(L2, 'the'); T.great = wt(L2, 'greatest'); T.trans = wt(L2, 'transformation'); T.in = wt(L2, 'in'); T.human = wt(L2, 'human'); T.hist = wt(L2, 'history');
  T.ns1 = ls('Next slide.', 0); T.ns2 = ls('Next slide.', 1); T.ns3 = ls('Next slide.', 2);
  const LC = 'Would you like me to generate a conclusion?'; T.concl = ls(LC); T.gen = wt(LC, 'generate'); T.conc = wt(LC, 'conclusion');
  const LN = 'No, I think I nailed it.'; T.no = ls(LN); T.nailed = wt(LN, 'nailed');
  T.end = ls('Look what I can do!', 8);
  T.rise = T.nailed + 0.1;
  PLAY = [
    { t: -1e9, name: 'tedshadow', f0: 0, rate: 30 },                                   // (only published videos with 100+ views: TED Charts' BREAKING front page opens the keynote)
    { t: T.lad - 0.45, name: 'tedshadow', f0: 0, rate: 30 },                          // the shadow-play stage opens the keynote (bold, graphic, never blown out)
    { t: T.lad + 1.4, name: 'tedscreen', f0: 95, rate: 30 },                          // dark call UI behind the title build
    { t: T.ns1, name: 'tedcharts', f0: 84, rate: 50 / (T.ns2 - T.ns1), gain: 0.5 },      // MINUTES 18 → SLIDES 0 → POINTS 0 builds while she waits
    { t: T.ns2, name: 'tedshadow', f0: 104, rate: 30 },                        // 'RIGHT?' lands
    { t: T.ns3, name: 'tedscreen', f0: 150, rate: 30 },                        // the chat: 'Ted you froze' · 'he's buffering' · 'it's a pause. for effect'
    { t: T.concl, name: 'tedshadow', f0: 20, rate: 30 },                         // 'Is the file ready?' … stepping back
  ];
  buildHall(); buildCams(); buildVCams();
}
export const range = () => [T.lad - 0.45, T.end - 0.03];
export function covers(t) { return t >= T.lad - 0.45 && t < T.end - 0.03; }

// ---------------------------------------------------------------- per frame
function setCam(c, shake = 0, t = 0) {
  cam.position.copy(c.p); if (shake) cam.position.add(V3(L.noise1(t * 0.8, 1), L.noise1(t * 0.7, 2), L.noise1(t * 0.6, 3)).multiplyScalar(shake));
  cam.up.set(Math.sin(c.roll || 0), Math.cos(c.roll || 0), 0); cam.lookAt(c.l);
  cam.fov = H > W ? 2 * Math.atan(Math.tan(c.fov * Math.PI / 360) * H / W) * 180 / Math.PI : c.fov; cam.updateProjectionMatrix();
}

export async function frame(t, ctx) {
  const u = look.finish.uniforms, bloom = look.bloom;
  const pulse = L.beatPulse(t, 7);
  const slam = sstep(T.nailed - 0.02, T.nailed + 0.12, t);          // stage lights to full on 'nailed'
  // ---- the wall: which TED video, which frame; the slide layer; the cut flash
  const clip = wallClip(t);
  const avg = await seqFrame(vidTex, clip.name, clip.idx) || new THREE.Color(0.3, 0.25, 0.3);
  const cutT = [T.ns1, T.ns2, T.ns3, T.concl].filter((x) => t >= x).pop();
  const wf = cutT !== undefined ? env(t, cutT, 0.008, 0.05) : 0;
  const titleOn = t < T.ns1;
  drawSlide(titleOn ? 'title' : 'none'); drawBand(titleOn ? 0 : t < T.ns2 ? 2 : t < T.ns3 ? 3 : t < T.concl ? 4 : 5);
  const wu = wallMat.uniforms;
  if (titleOn) {
    const times = [T.the, T.great, T.trans, T.in, T.human, T.hist, T.hist + 0.5];
    const rects = SLIDE.userData.rects;
    for (let i = 0; i < 8; i++) {
      const r = rects[i]; if (!r) { wu.uWR.value[i].set(-1, -1, -1, -1); continue; }
      wu.uWR.value[i].set(r[0] / SW, 1 - r[3] / SH, r[2] / SW, 1 - r[1] / SH);
      wu.uWK.value[i] = clamp((t - times[i] + 0.04) / 0.2);
    }
    wu.uSlideA.value = 1; wu.uTitle.value = 1; wu.uDim.value = lerp(1, 0.2, sstep(T.the - 0.15, T.the + 0.12, t));
  } else { for (let i = 0; i < 8; i++) wu.uWR.value[i].set(-1, -1, -1, -1); wu.uSlideA.value = 1; wu.uTitle.value = 0; wu.uDim.value = 1; }
  wu.uDim.value *= clip.gain ?? 1;   // cream-paper footage (TED Charts) is dimmed so the LED wall never blows out
  const vl = 0.2126 * avg.r + 0.7152 * avg.g + 0.0722 * avg.b;
  wu.uFlash.value = wf * 0.85; wu.uBright.value = clamp(1.3 - 0.8 * vl, 0.68, 1.25) * lerp(1, 1.18, slam) * (1 + 0.04 * pulse);
  // the room takes the wall's colour
  const wl = avg.clone(); const lum = 0.2126 * wl.r + 0.7152 * wl.g + 0.0722 * wl.b; wl.multiplyScalar(1 / Math.max(0.12, Math.max(wl.r, wl.g, wl.b)));
  lights.wall.color.copy(wl); lights.wall.intensity = (0.5 + 1.6 * Math.min(1, lum * 1.6)) * (titleOn && t > T.the ? 0.45 : 1) * (1 + wf);
  RIM.value.copy(wl).multiplyScalar(0.1 + 0.22 * Math.min(1, lum * 1.6));
  lights.hemi.intensity = 0.12;
  if (t >= T.concl) { lights.wall.intensity *= 1.6; RIM.value.multiplyScalar(0.45); }   // the prompter POV looks at the room: faces catch the wall's light
  lights.spot.intensity = lerp(6, 9, slam);
  // ---- beams: slow sweeps in the haze; everything to full on the slam
  BEAMS.forEach((b, i) => {
    const w = t * b.sp + b.ph;
    let to;
    if (b.warm) to = V3(POD.x + Math.sin(w) * 2.2 + b.side * 1.5, 0, POD.z + 1 + Math.cos(w * 0.8) * 1.5);
    else to = V3(b.from.x * 0.6 + Math.sin(w) * 5, 0, -2 + Math.cos(w * 0.7) * 5);
    const sweep = slam > 0 && b.i % 3 === 1;
    if (sweep) to.lerp(V3(b.from.x * 1.3 + Math.sin(t * 2.2 + b.ph) * 6, rowY(6), CA.z + rowR(3 + (i % 7))), slam);
    aimBeam(b.m, b.from, to, sweep ? 0.85 : b.warm ? 1.3 : 1.6);
    const base = (b.warm ? 0.045 : 0.03) * (titleOn && t > T.the - 0.2 ? 0.45 : 1); b.mat.uniforms.uA.value = lerp(base, sweep ? 0.055 : 0.065, slam) * (1 + 0.25 * pulse);
    if (slam > 0.5 && !b.warm) b.mat.uniforms.uCol.value.set(b.i % 2 ? PINK : AMBER); else b.mat.uniforms.uCol.value.copy(b.base);
    b.lens.material.color.copy(b.mat.uniforms.uCol.value).multiplyScalar(lerp(1.6, 3.5, slam));
  });
  FOLLOW.material.uniforms.uA.value = lerp(0.07, 0.11, slam); POOL.material.opacity = lerp(0.45, 0.7, slam);
  // ---- the crowd
  poseCrowd(t);
  // ---- the teleprompter: Claude's question types on; options; her answer in green
  const title = 'Generate a conclusion?';
  const typed = t < T.concl ? 0 : Math.min(title.length, Math.floor((t - T.concl) / 0.62 * title.length));
  const optA = clamp((t - T.conc + 0.02) / 0.16);
  const sel = t >= T.no + 0.04 ? 1 : 0;
  drawPrompt(typed, optA, sel);
  PROMPTM.material.color.setScalar(1.45 + 0.4 * env(t, T.no + 0.04, 0.01, 0.08));
  // ---- camera + post
  let c, shake = 0;
  u.uVig.value = 0.4; u.uGrain.value = 0.05;
  bloom.threshold = 0.94; bloom.radius = 0.5; bloom.strength = 0.25 + 0.06 * pulse + 0.1 * slam;
  const CAMS = H > W ? VCAMS : CAMS0;
  if (t < T.ns1) c = CAMS.crane(t);
  else if (t < T.ns2) c = CAMS.wide(t);
  else if (t < T.ns3) c = CAMS.side(t);
  else if (t < T.concl) c = CAMS.low(t);
  else {
    c = CAMS.prompt(H > W ? t : Math.min(t, T.rise)); shake = 0.004;
    if (t > T.rise && H <= W) {   // rise straight up, tilting down toward the standing room; space.js continues the pull-back from above the roof
      const x = t - T.rise; const up = 96 * x * x + 6 * x; const tilt = easeIO(clamp(x / 0.34));
      c = { p: c.p.clone().add(V3(0, up, 0)), l: c.l.clone().lerp(V3(0, 0.0, 0.8), tilt).add(V3(0, up * (1 - tilt), 0)), fov: c.fov + tilt * 18, roll: 0 };
      u.uVel.value.set(0, -Math.min(0.012, x * 0.04));
    }
  }
  setCam(c, shake, t);
  u.uFlash.value = 0.04 * wf + 0.1 * env(t, T.nailed, 0.008, 0.04); u.uFlashCol.value.setRGB(1, 0.95, 0.88);
  return { scene, camera: cam };
}
