// Great Idea, Ted v3: look test. The I Have a Blocker city at blue hour, the Ted meeting as twelve floating rooms.
// renderAt(n): n picks the shot (0 wide establishing, 1 the grid, 2 Ted's room, 3 her room, 4 chorus).
import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { ShaderPass } from 'three/addons/postprocessing/ShaderPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { loadFonts, RIM, FONT, clay, basic } from './lib.js';
import { buildCity, ROOF_Y, ROOF, dayTint } from './city.js';
import { Room, RW, RH, GAP, slotPos, setHandLift } from './rooms.js';
import * as B from './boards.js';
window.setHand = setHandLift;

const q = new URLSearchParams(location.search);
const W = +q.get('w') || 1600, H = +q.get('h') || 900;
const renderer = new THREE.WebGLRenderer({ antialias: false, preserveDrawingBuffer: true });
renderer.setPixelRatio(1); renderer.setSize(W, H);
renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.0;
document.body.appendChild(renderer.domElement);
const scene = new THREE.Scene(); scene.fog = new THREE.FogExp2(0x1b2146, 0.0032);
const cam = new THREE.PerspectiveCamera(38, W / H, 0.1, 2400); scene.add(cam);
const hemi = new THREE.HemisphereLight(0x8fa0d8, 0x1a1420, 1.15); scene.add(hemi);
const key = new THREE.DirectionalLight(0xffe3c4, 1.6); key.position.set(-8, 14, 22); scene.add(key);
RIM.value.set(0xffc2a8);   // the rim light picks up the peach horizon

const composer = new EffectComposer(renderer);
composer.addPass(new RenderPass(scene, cam));
const bloom = new UnrealBloomPass(new THREE.Vector2(W / 2, H / 2), 0.5, 0.5, 0.82); composer.addPass(bloom);
const finish = new ShaderPass({
  uniforms: { tDiffuse: { value: null }, uVig: { value: 0.3 }, uGold: { value: 0 } },
  vertexShader: `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
  fragmentShader: `uniform sampler2D tDiffuse; uniform float uVig, uGold; varying vec2 vUv;
    void main(){ vec2 d = vUv - 0.5; vec3 c = texture2D(tDiffuse, vUv).rgb;
      c *= 1.0 - uVig * pow(length(d * vec2(1.0, 0.9)) * 1.45, 2.4);
      c = mix(c, c * vec3(1.12, 1.0, 0.82) + vec3(0.03, 0.015, 0.0), uGold);
      gl_FragColor = vec4(c, 1.0); }` });
composer.addPass(finish); composer.addPass(new OutputPass());

let rooms = [], gridG;
const GRID_Y = ROOF_Y + 1.7 + 1.0 * (RH + GAP), GRID_Z = ROOF.z - 7;
function build() {
  const CITY = window.__city = buildCity(); scene.add(CITY);
  gridG = new THREE.Group(); gridG.position.set(0, GRID_Y, GRID_Z); scene.add(gridG);
  for (let i = 0; i < 12; i++) { const r = new Room(i); r.root.position.copy(slotPos(i, 4, 3)); rooms.push(r); gridG.add(r.root); }
}
const V = (x, y, z) => new THREE.Vector3(x, y, z);
const G = (i) => slotPos(i, 4, 3).add(V(0, GRID_Y, GRID_Z));
const SHOTS = [
  () => [V(-11, GRID_Y + 1.5, GRID_Z + 25), V(1, GRID_Y + 0.5, GRID_Z - 4), 40],         // establishing: the city, the meeting floating over it
  () => [V(-5.5, GRID_Y + 1.8, GRID_Z + 17.5), V(0.3, GRID_Y - 0.2, GRID_Z), 38],    // the grid
  () => { const p = G(5); return [p.clone().add(V(-1.0, 0.9, 4.3)), p.clone().add(V(0, -0.05, -1.0)), 34]; },   // Ted
  () => { const p = G(0); return [p.clone().add(V(1.2, 0.35, 4.6)), p.clone().add(V(0, -0.15, -1.0)), 34]; },    // her
  () => [V(4.5, GRID_Y + 0.6, GRID_Z + 16.5), V(-0.2, GRID_Y - 0.1, GRID_Z), 40],   // a chorus: every window gold, Ted glowing coral
  () => { const p = G(5); return [p.clone().add(V(1.35, -0.25, 1.2)), p.clone().add(V(0, -0.3, -0.75)), 30]; },   // QA: Ted's desk from the side, at desk height
  () => { const p = G(0); return [p.clone().add(V(-1.35, -0.25, 1.2)), p.clone().add(V(0, -0.3, -0.75)), 30]; },  // QA: her desk from the other side
];

window.__rooms = rooms;
const EXPR = {   // the face test: who looks how
  0: { smile: -0.08, brows: [0.95, -0.25], lids: 0.42, look: [0.55, -0.1] },      // you: unimpressed, one brow up
  5: { smile: 1, brows: 0.65, lids: 0.0, open: 0.35 },                             // Ted: beaming
  1: { smile: 0.55, brows: 0.3, lids: 0.1 },                                       // Dana: delighted with Ted
  2: { smile: 0.1, open: 0.8, brows: 0.4 },                                        // Raj: singing
  3: { smile: -0.4, browTilt: -0.6, brows: 0.3 },                                  // Meg: worried
  4: { smile: 0.2, lids: 0.6, look: [-0.7, -0.6] },                                // Kofi: on his phone
};
window.renderAt = (n) => {
  if (n >= 100) {   // a face close-up: room n - 100
    const i = Math.round(n) - 100; rooms.forEach((r, k) => r.update({ t: 3.1 + k * 0.37, expr: EXPR[k] }));
    scene.updateMatrixWorld(true); const h = rooms[i].man.head.getWorldPosition(new THREE.Vector3());
    cam.position.copy(h).add(V(0.12, 0.05, 0.95)); cam.lookAt(h.clone().add(V(0, -0.06, 0))); cam.fov = 26; cam.updateProjectionMatrix();
    finish.uniforms.uGold.value = 0; bloom.strength = 0.35; composer.render(); return renderer.domElement.toDataURL('image/jpeg', 0.92);
  }
  const shot = Math.round(n); const chorus = shot === 4;
  const [p, tg, fov] = SHOTS[shot](); cam.position.copy(p); cam.lookAt(tg); cam.fov = fov; cam.updateProjectionMatrix();
  finish.uniforms.uGold.value = chorus ? 0.55 : 0;
  bloom.strength = chorus ? 0.8 : 0.5;
  rooms.forEach((r, i) => r.update({ t: 3.1 + i * 0.37, talk: (chorus ? i === 5 : i === 0) ? 1 : 0, talkCol: i === 5 ? 0xff6b5b : 0x7fe0c2,
    fine: chorus && i !== 5 ? 1 : 0, lookYaw: 0 }));
  composer.render();
  return renderer.domElement.toDataURL('image/jpeg', 0.92);
};

// ---------------------------------------------------------------- QA: does any body part pass through a solid?
// Every arm, hand, leg and the torso is sampled as spheres (radius = the part's real radius) and measured against each
// solid's box (laptop lid: its own rotated box). Returns the worst penetration per person, in millimetres of room
// (a room is 3 m wide), with the part and the solid it hits. 0 = nothing touches.
const _p = new THREE.Vector3(), _l = new THREE.Vector3(), _inv = new THREE.Matrix4();
function penetration(center, r, mesh) {
  mesh.geometry.computeBoundingBox(); const bb = mesh.geometry.boundingBox;
  _inv.copy(mesh.matrixWorld).invert(); _l.copy(center).applyMatrix4(_inv);
  const sc = new THREE.Vector3().setFromMatrixScale(mesh.matrixWorld); const rl = r / Math.min(sc.x, sc.y, sc.z);
  const cx = Math.max(bb.min.x, Math.min(_l.x, bb.max.x)), cy = Math.max(bb.min.y, Math.min(_l.y, bb.max.y)), cz = Math.max(bb.min.z, Math.min(_l.z, bb.max.z));
  const inside = cx === _l.x && cy === _l.y && cz === _l.z;
  const d = inside ? -Math.min(_l.x - bb.min.x, bb.max.x - _l.x, _l.y - bb.min.y, bb.max.y - _l.y, _l.z - bb.min.z, bb.max.z - _l.z)
                   : Math.hypot(_l.x - cx, _l.y - cy, _l.z - cz);
  return (rl - d) * Math.min(sc.x, sc.y, sc.z);
}
function bodySpheres(man) {
  const S = man.root.getWorldScale(new THREE.Vector3()).x, out = [];
  const w = (o, v) => o.localToWorld(v.clone());
  const seg = (name, a, b, r, n = 8) => { for (let i = 0; i <= n; i++) out.push([name, w(man.body, a.clone().lerp(b, i / n)), r * S]); };
  man.arms.forEach((a) => { const side = a.s < 0 ? 'left' : 'right';
    seg(side + ' upper arm', a.S, a.E, 0.068); seg(side + ' forearm', a.E, a.wr.position, 0.06);
    { const hc = a.hand.getWorldPosition(new THREE.Vector3()); const ax = new THREE.Vector3(0, 1, 0).applyQuaternion(a.hand.getWorldQuaternion(new THREE.Quaternion()));
      for (const k of [-0.045, 0, 0.045]) out.push([side + ' hand', hc.clone().addScaledVector(ax, k * S), 0.038 * S]); } });   // the hand: a flat palm, 3 spheres along it
  man.legs.forEach((l) => { const side = l.s < 0 ? 'left' : 'right';
    seg(side + ' thigh', l.hp.position, l.kn.position, 0.085); seg(side + ' shin', l.kn.position, l.ankle, 0.068);
    { const fc = l.foot.getWorldPosition(new THREE.Vector3()), ax = new THREE.Vector3(0, 1, 0).applyQuaternion(l.foot.getWorldQuaternion(new THREE.Quaternion()));
      for (const k of [-0.05, 0, 0.05]) out.push([side + ' foot', fc.clone().addScaledVector(ax, k * S), 0.045 * S]); } });
  seg('torso', new THREE.Vector3(0, 0.08, 0), new THREE.Vector3(0, 0.46, 0), 0.19 * 0.72, 6);
  return out;
}
window.qa = (n) => { window.renderAt(n); return window.qaNow(); };
window.qaNow = () => {
  scene.updateMatrixWorld(true); const rep = [];
  const people = rooms.filter((r) => r.man && r.man.root.parent).length;   // the check must actually see everyone
  if (people !== rooms.filter((r) => r.man).length) return [{ who: 'QA', mm: 1, part: `only ${people} people are in the scene`, solid: '' }];
  rooms.forEach((r, i) => { if (!r.man) return; const hits = {};
    const live = r.solids.filter((x) => !x[2] || x[2]());   // props only count while they're in the shot
    for (const [part, c, rad] of bodySpheres(r.man)) for (const [name, mesh] of live) {
      if (name === 'chair' && (part === 'torso' || part.includes('thigh'))) continue;   // you sit on and lean against the chair: that's contact, not a clip
      const pen = penetration(c, rad, mesh); const k = part + ' into ' + name; if (pen > 0.001 && pen > (hits[k] || 0)) hits[k] = pen; }
    const list = Object.entries(hits).sort((x, y) => y[1] - x[1]).map(([k, v]) => `${Math.round(v * 1000)} mm ${k}`);
    { const fl = r.solids.find((x) => x[0] === 'floor')[1]; const top = new THREE.Box3().setFromObject(fl).max.y;   // and the opposite: feet must touch the floor
      r.man.legs.forEach((l) => { const gap = new THREE.Box3().setFromObject(l.foot).min.y - top; if (gap > 0.01) list.push(`${Math.round(gap * 1000)} mm ${l.s < 0 ? 'left' : 'right'} foot floating`); }); }
    { // props on the desk must not pass through each other (a box through a laptop, a printer through a mug)
      const PROPS = ['laptop', 'laptop lid', 'mug', 'donut box', 'printer', 'cat'], ps = live.filter((x) => PROPS.includes(x[0]));
      const bx = ps.map(([n, m]) => [n, new THREE.Box3().setFromObject(m).expandByScalar(-0.004)]);
      for (let a = 0; a < bx.length; a++) for (let b = a + 1; b < bx.length; b++) { if (bx[a][0].startsWith('laptop') && bx[b][0].startsWith('laptop')) continue;
        if (bx[a][1].intersectsBox(bx[b][1])) list.push(`${bx[a][0]} overlaps ${bx[b][0]}`); } }
    rep.push({ who: r.c.name, mm: list.length, part: list.join('; '), solid: '' }); });
  return rep;
};


// ---------------------------------------------------------------- the joke and text frames (for approval)
let BO = null;   // the board objects, built on first use
function faceCanvas(i) {   // a headshot of person i, rendered from the scene (for the leadership page)
  const r = rooms[i]; r.update({ t: 3.1, expr: { smile: i === 5 ? 0.85 : 0.3, lids: 0.08 } }); scene.updateMatrixWorld(true);
  const h = r.man.head.getWorldPosition(new THREE.Vector3()); const c2 = new THREE.PerspectiveCamera(24, 1, 0.05, 100);
  c2.position.copy(h).add(V(0, 0.02, 1.05)); c2.lookAt(h.clone().add(V(0, -0.03, 0)));
  const rt = new THREE.WebGLRenderTarget(512, 512); renderer.setRenderTarget(rt); renderer.render(scene, c2); renderer.setRenderTarget(null);
  const px = new Uint8Array(512 * 512 * 4); renderer.readRenderTargetPixels(rt, 0, 0, 512, 512, px);
  const cv = document.createElement('canvas'); cv.width = cv.height = 512; const g = cv.getContext('2d'); const im = g.createImageData(512, 512);
  for (let y = 0; y < 512; y++) for (let x = 0; x < 512; x++) { const s = ((511 - y) * 512 + x) * 4, d = (y * 512 + x) * 4;
    for (let k = 0; k < 3; k++) im.data[d + k] = Math.min(255, 255 * Math.pow(px[s + k] / 255, 1 / 2.2) * 1.05); im.data[d + 3] = 255; }
  g.putImageData(im, 0, 0); return cv;
}
function initialsCanvas(t) {   // Greg's camera is off, so the company site uses his initials too
  const cv = document.createElement('canvas'); cv.width = cv.height = 512; const g = cv.getContext('2d');
  g.fillStyle = '#2b2d36'; g.fillRect(0, 0, 512, 512); g.fillStyle = '#e8e8ec'; g.font = `600 190px ${FONT.ui}`; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(t, 256, 270); return cv; }
function buildBoards() {
  BO = { all: [] }; const add = (k, o) => { BO[k] = o; BO.all.push(o); scene.add(o); return o; };
  const clk = new THREE.Group(); const ct = new THREE.Mesh(new THREE.BoxGeometry(8, 42, 7), dayTint(new THREE.MeshBasicMaterial({ color: 0x14172c }))); ct.position.y = 21.7; ct.scale.y = 43.4 / 42; clk.add(ct);
  const cs = B.clockSign(); cs.position.set(0, 40.9, 3.7); clk.add(cs); clk.position.set(0, 0, GRID_Z - 15); clk.userData.set = cs.userData.set; add('clock', clk);
  add('bbL', B.billboardTower(-16.5, GRID_Z - 11, 0.45)); add('bbR', B.billboardTower(16.5, GRID_Z - 11, -0.45));
  add('povTitle', B.skyTitle([["POV: you said it first.", 'rgba(255,255,255,0.9)', 1, '#1E2240']], 3.4)).position.set(0, GRID_Y + 6.4, GRID_Z - 8);   // morning sky: ink letters with a soft white halo
  add('chorusTitle', B.skyTitle([['GREAT IDEA,', B.C.pink, 1], ['TED', B.C.cyan, 1.35]], 25)).position.set(0, GRID_Y + 18.6, GRID_Z - 14);
  add('lobby', B.lobbyPanel([['You', '#7FE0C2'], ['Dana', '#9AA6B8'], ['Tom', '#7A2E3B'], ['Mike', '#B8423A'], ['Kyle', '#8FB39A'], ['Ted', '#FF6B5B'], ['Lena', '#7CC6F2']], 12)).position.set(0, GRID_Y + 1.0, GRID_Z + 4); BO.lobby.scale.setScalar(1.35);
  add('notes', B.notesCard());
  add('timer', B.timerPanel('08:00', true)).position.set(0, GRID_Y + 0.0, GRID_Z + 3.2); BO.timer.scale.setScalar(1.3);
  add('bKofi', B.bubble('brb', { who: 'Kyle', col: '#5B6BC8', tail: 'right' })); add('bPriya', B.bubble('can someone share the deck?', { who: 'Priya', col: '#5B6BC8', tail: 'right' }));
  add('bGreg', B.bubble("Let's circle back.", { who: 'Greg', col: '#5B6BC8', size: 72 }));
  add('bYou', B.bubble("We should push the launch. We're not ready and we know it.", { who: 'You', col: B.C.mintDeep, w: 1300, size: 70 }));
  add('bTed', B.bubble("We should push the launch. We're not ready and we know it.", { who: 'Ted', col: B.C.coralDeep, w: 1300, size: 70 }));
  { // the meeting reactions everyone throws at Ted, plus confetti: one shared field, frozen mid-rise for the still
    const party = new THREE.Group(); add('party', party); let sd = 7; const R = () => (sd = (sd * 16807) % 2147483647) / 2147483647;
    const em = ['👏', '🎉', '❤️', '👍', '😮', '😂', '👏', '🎉', '❤️', '🔥'], c = G(5);
    for (let n = 0; n < 70; n++) { const x = (R() * 2 - 1) * 16, y = -4 + R() * 19, z = 1.5 + R() * 4;
      if ((Math.abs(x) < 13 && y > 3.5) || (Math.abs(x) < 8 && y <= 3.5)) continue;   // keep the title and every room clear
      const r = B.reaction(em[n % em.length], 1.1 + R() * 1.0); r.position.set(c.x + x, c.y + y, c.z + z); r.rotation.z = (R() - 0.5) * 0.5; party.add(r); }
    const cols = [0xff4fb0, 0x45f0ff, 0xffd27a, 0x7fe0c2, 0xff6b5b, 0xffffff];
    for (let n = 0; n < 160; n++) { const q = new THREE.Mesh(new THREE.PlaneGeometry(0.12, 0.26), B.confettiMat(cols[n % cols.length]));
      q.position.set(c.x + (R() * 2 - 1) * 17, c.y - 3 + R() * 20, c.z + 1 + R() * 6); q.rotation.set(R() * 6, R() * 6, R() * 6); party.add(q); } }
  BO.tex = { raise1: B.raiseLetter('$260,582'), raiseBg: B.raiseBackdrop(), equity: B.equityGrant('250,000') };
  { const full = '$260,582,419,006,553', steps = [8, 10, 11, 12, 14, 15, 16, 18, 19, 20, 20, 20];   // characters shown at each step; the last steps tear digits off
    BO.raiseVar = steps.map((n, i) => { const m = B.raiseOverflow(full.slice(0, n), { spill: i >= 10 ? (i - 9) * 2 - 1 : 0 }); m.visible = false; scene.add(m); return m; }); }
  { const sp = add('raiseSpill', B.raiseOverflow('$260,582,419,006,553')); BO.bbL.updateMatrixWorld(true);   // card overhangs the board to the right
    sp.position.copy(BO.bbL.localToWorld(V(-4.65 + 7.5, 37.0, 4.05))); sp.rotation.y = 0.45; }
  { const tedHead = faceCanvas(5);
    add('prof1', B.profileCard(tedHead, [['not a bad guy', 'good']])); add('prof2', B.profileCard(tedHead, [['not a bad guy', 'good'], ['the worst part', 'bad']]));
    add('bWeekend', B.bubble('How was your weekend?', { who: 'Ted', col: B.C.coralDeep, w: 1100, size: 76 })); add('bWait', B.waitingBubble());
    add('bSlow', B.styledBubble('', { who: 'Ted', col: B.C.coralDeep, mode: 'slow' })); add('bLoud', B.styledBubble('', { who: 'Ted', col: B.C.coralDeep, mode: 'loud' }));
    add('wfw', B.wordForWord()); add('interesting', B.aside('interesting.', 0.7, B.C.ink)); BO.tex.dict = B.dictionaryEntry(); }
  { // batch 3: chorus 2 and the donuts
    add('bDana', B.bubble("Ted, that's exactly what we needed.", { who: 'Dana', col: '#5B6BC8', w: 1300, size: 74 }));
    const rain = new THREE.Group(); add('digitRain', rain); let sd = 11; const R = () => (sd = (sd * 16807) % 2147483647) / 2147483647;
    for (let n = 0; n < 60 && rain.children.length < 34; n++) { const x = -16.5 + (R() * 2 - 1) * 9, y = GRID_Y + 2 + R() * 12, z = GRID_Z - 8 + R() * 6; if (Math.abs(x + 16.5) < 6.5 && Math.abs(y - 36) < 3.6) continue;   // never over the card
      const c = B.digitChip(String(Math.floor(R() * 10))); c.position.set(x, y, z); c.rotation.set(0, 0.45 + (R() - 0.5) * 0.6, (R() - 0.5) * 1.4); c.scale.setScalar(0.8 + R() * 0.9); rain.add(c); }
    BO.tex.hero = B.websiteHero(faceCanvas(5));
    add('talkSign', B.talkSign());
    const stage = new THREE.Group(); add('stage', stage);   // a round red carpet and a spotlight, out on the roof
    const carpet = new THREE.Mesh(new THREE.CylinderGeometry(3.2, 3.2, 0.06, 64), new THREE.MeshBasicMaterial({ color: 0xc81e2a })); stage.add(carpet); stage.userData.carpet = carpet;
    const coneMat = new THREE.MeshBasicMaterial({ color: 0xfff1d0, transparent: true, opacity: 0.11, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide });
    const cone = new THREE.Mesh(new THREE.CylinderGeometry(0.4, 3.1, 14, 48, 1, true), coneMat); cone.position.y = 7; stage.add(cone);
    const spot = new THREE.Group(); add('spot', spot); const cone2 = new THREE.Mesh(new THREE.CylinderGeometry(0.35, 2.2, 12, 48, 1, true), coneMat.clone()); cone2.material.opacity = 0.2; cone2.position.y = 6; spot.add(cone2);
    // the big donut, and the magnifying glass held over it
    const dz = new THREE.Group(); add('bigDonut', dz);
    const dough = new THREE.Mesh(new THREE.TorusGeometry(2.4, 1.25, 32, 64), clay(0xd9a05b)); dz.add(dough);
    const icing = new THREE.Mesh(new THREE.TorusGeometry(2.4, 1.05, 32, 64, Math.PI * 2), clay(0xff7fb0)); icing.position.z = 0.32; icing.scale.z = 0.9; dz.add(icing);
    const sprCols = [0xffffff, 0x45f0ff, 0xffd27a, 0x7fe0c2]; for (let n = 0; n < 60; n++) { const a = R() * Math.PI * 2, rr2 = 1.6 + R() * 1.6; const sp = new THREE.Mesh(new THREE.CapsuleGeometry(0.05, 0.22, 4, 8), basic(sprCols[n % 4])); sp.position.set(Math.cos(a) * rr2, Math.sin(a) * rr2, 1.38); sp.rotation.z = R() * 3; dz.add(sp); }
    const glass = new THREE.Group(); dz.add(glass); glass.position.set(2.6, 2.4, 2.4); glass.rotation.z = -0.5;
    glass.add(new THREE.Mesh(new THREE.TorusGeometry(1.5, 0.16, 16, 64), clay(0x23252c)));
    const lens = new THREE.Mesh(new THREE.CircleGeometry(1.45, 48), new THREE.MeshBasicMaterial({ color: 0xbfe8ff, transparent: true, opacity: 0.18, depthWrite: false })); glass.add(lens);
    const handle = new THREE.Mesh(new THREE.CapsuleGeometry(0.2, 1.8, 8, 16), clay(0x23252c)); handle.position.set(0, -2.6, 0); glass.add(handle);
  }
  { // batch 4: the bridge
    add('rec1', B.recordCard()); add('rec2', B.recordCard({ first: true }));
    add('rec3', B.recordCard({ first: true, chips: [['not upset he said it', 'good']] }));
    add('rec4', B.recordCard({ first: true, chips: [['not upset he said it', 'good'], ['upset that it worked', 'bad']] }));
    add('rec5', B.recordCard({ first: true, chips: [['not upset he said it', 'good'], ['upset that it worked', 'bad']], loading: true }));
    add('pGood', B.pill('not upset he said it', 'good')); add('pBad', B.pill('upset that it worked', 'bad'));
    add('pBecoming', B.pill('becoming…', 'status')); add('pNormal', B.pill('extremely normal about this', 'status'));
    add('rec6', B.recordCard({ first: true, chips: [['not upset he said it', 'good'], ['upset that it worked', 'bad']], status: 'extremely normal about this' })); }
  { // batch 5: verse 3, the paper trail
    add('notesFilled', B.notesFilled());
    BO.tex.deck = B.deckSlide(); BO.tex.deckName = B.deckSlide('name'); BO.tex.deckSize = B.deckSlide('size'); BO.tex.deckFooter = B.deckSlide('footer'); BO.tex.deckFile = B.deckSlide('file');
    BO.tex.email = B.sentEmail();
    add('fileNeon', B.skyTitle([['my_idea_do_not_rephrase', B.C.pink, 0.62], ['_v7_FINAL.deck', B.C.cyan, 0.8]], 15));
    add('env1', B.envelope(false)); add('env2', B.envelope(true)); add('week1', B.weekStrip(false)); add('week2', B.weekStrip(true)); }
  { // batch 6: verse 3 part 2, the donuts and the log
    add('bakery', B.bakerySign());
    add('filledCard', B.filledDonutCard());
    const fd = new THREE.Group(); add('filled', fd);   // one filled donut, split open: the jam
    const doughM = clay(0xe0a860), sugar = clay(0xfbf6ee), jam = clay(0xc0183a);
    const half = (sx) => { const h2 = new THREE.Mesh(new THREE.SphereGeometry(1, 40, 24, 0, Math.PI), doughM); h2.scale.set(1.2, 0.85, 1.2); h2.rotation.y = sx > 0 ? -Math.PI / 2 : Math.PI / 2; h2.position.x = sx * 0.55; h2.rotation.z = sx * 0.25; fd.add(h2);
      const top = new THREE.Mesh(new THREE.SphereGeometry(1.01, 40, 24, 0, Math.PI, 0, 0.9), sugar); top.scale.copy(h2.scale); top.rotation.copy(h2.rotation); top.position.copy(h2.position); fd.add(top);
      const face = new THREE.Mesh(new THREE.CircleGeometry(1, 40), clay(0xf6e3bf)); face.scale.set(1.2, 0.85, 1); face.position.set(sx * 0.55, 0, 0); face.rotation.y = sx > 0 ? -Math.PI / 2 : Math.PI / 2; face.rotation.x = 0; face.position.x += sx * -0.002; fd.add(face);
      const j = new THREE.Mesh(new THREE.SphereGeometry(0.42, 24, 16), jam); j.scale.set(0.25, 1, 1); j.position.set(sx * 0.56, -0.05, 0); fd.add(j); };
    half(-1); half(1);
    for (let i = 0; i < 3; i++) { const drip = new THREE.Mesh(new THREE.CapsuleGeometry(0.08, 0.35 + i * 0.12, 6, 12), jam); drip.position.set(-0.05 + i * 0.05, -0.75 - i * 0.08, 0.15 - i * 0.12); fd.add(drip); }
    add('bMike', B.bubble('Oh, Ted usually brings those.', { who: 'Mike (host)', col: '#5B6BC8', w: 1300, size: 74 }));
    add('bNice', B.bubble('Nice deck.', { who: 'Ted', col: B.C.coralDeep, w: 900, size: 96 }));
    add('bThanks', B.bubble('Thank you, Ted.', { who: 'You', col: B.C.mintDeep, w: 1000, size: 90 }));
    add('pWaitYou', B.pill('still waiting  ·  1:12', 'status')); add('pWaitTed', B.pill('still waiting  ·  0:41', 'status')); add('pDiff', B.pill('diff:  0 changes', 'good'));
    const wit = [0, 1, 2, 3, 6, 7].map((i) => faceCanvas(i));
    add('log1', B.meetingLog(1)); add('log2', B.meetingLog(2)); add('log3', B.meetingLog(3, wit)); }
  { // batch 7: final chorus and the post-chorus
    BO.tex.org = B.orgChart({ ted: faceCanvas(5), dana: faceCanvas(1), you: faceCanvas(0) });
    add('roomSign', B.roomSign()); add('plaque', B.plaque()); add('plaqueWall', B.plaqueWall());
    add('wInno', B.skyTitle([['INNOVATION.', B.C.pink, 1]], 10)); add('wLead', B.skyTitle([['LEADERSHIP.', B.C.cyan, 1]], 10)); add('wVis', B.skyTitle([['VISION.', B.C.gold, 1]], 10));
    add('bRepA', B.bubble('He repeated a sentence.', { who: 'You', col: B.C.mintDeep, w: 1300, size: 84 }));
    add('wMy', B.skyTitle([['HE REPEATED', '#FFC9A8', 0.8], ['MY SENTENCE.', B.C.mint, 1.2]], 19)); }
  { // batch 8: the outro
    for (let n = 1; n <= 4; n++) BO.tex['pie' + n] = B.whyPie(n);
    for (let n = 1; n <= 4; n++) BO.tex['sheet' + n] = B.sheet(n);
    add('tedRed', B.skyTitle([['TED IS RED.', B.C.red, 1.4, '#FFE4E4']], 10));
    add('pReally', B.pill('really.', 'status')); add('pFantastic', B.pill('fantastic.', 'status')); add('pHappy', B.pill('i\u2019m happy for you.', 'status')); add('pKnow', B.pill('i know.', 'status')); }
  BO.tex.leaders = B.leadershipPage([['Dana', faceCanvas(1)], ['Greg', initialsCanvas('GR')], ['Lena', faceCanvas(6)], ['Ted', faceCanvas(5), true]]);
}
const fwd = (i) => { rooms[i].root.position.copy(slotPos(i, 4, 3).add(V(0.6, 0, 3.0))); rooms[i].root.scale.setScalar(1.12); return G(i).add(V(0.6, 0, 3.0)); };   // a speaker's room slides out of the grid
const youFwd = () => { rooms[0].root.position.copy(slotPos(0, 4, 3).add(V(0.6, 0, 3.0))); rooms[0].root.scale.setScalar(1.12); return G(0).add(V(0.6, 0, 3.0)); };
const deckClose = (texKey, x, y) => { show('bbL'); BO.bbL.userData.set(BO.tex[texKey]); BO.bbL.updateMatrixWorld(true);
  const tgt = BO.bbL.localToWorld(V(x, 36 + y, 3.9)), cam = BO.bbL.localToWorld(V(x + 0.3, 36 + y + 0.2, 3.9 + 4.6));
  return { cam: [cam, tgt, 40], states: () => ({}) }; };
const tedFwd = () => { rooms[5].root.position.copy(slotPos(5, 4, 3).add(V(0.6, 0, 3.0))); rooms[5].root.scale.setScalar(1.12); return G(5).add(V(0.6, 0, 3.0)); };
const show = (...ks) => ks.forEach((k) => { BO[k].visible = true; });
const at = (o, p, ry = 0, sc = 1) => { o.position.copy(p); o.rotation.set(0, ry, 0); o.scale.setScalar(sc); return o; };
const CLEAN = new URLSearchParams(location.search).has('clean');   // the caption-free version: captions are a separate layer
// chat bubbles and status pills that just repeat the sung lyric: cut, so the picture carries the line
const BUBBLES = ['wfw', 'bDana', 'bGreg', 'bKofi', 'bLoud', 'bMike', 'bNice', 'bPriya', 'bRepA', 'bSlow', 'bTed', 'bThanks', 'bWait', 'bWeekend', 'bYou'];
const CUT = { C06: ['bWeekend'], C11: ['bTed'], D02: ['bDana'], G05: ['bYou'], G08: ['bMike'], G13: ['bNice'], G14: ['bThanks'],
  E03: ['pGood'], E04: ['pBad'], J02: ['pReally'], J03: ['pFantastic'], J04: ['pHappy'], J14: ['pKnow'] };
const tight = (p) => [p.clone().add(V(0.15, 0.35, 6.4)), p.clone().add(V(0.1, 0.15, 0)), 40];
const board = (b) => () => { BO[b].updateMatrixWorld(true); return [BO[b].localToWorld(V(0, 36.1, 3.9 + 8.2)), BO[b].localToWorld(V(0, 36, 3.9)), 44]; };
const WAITPILL = { C12: () => { BO.pDiff.visible = true; at(BO.pDiff, G(0).add(G(5)).multiplyScalar(0.5).add(V(0.4, 2.7, 3.4)), 0, 3.2); },
  C07: () => { BO.pWaitTed.visible = true; at(BO.pWaitTed, G(5).add(V(0.6, 0, 3.0)).add(V(0.1, 1.45, 1.4)), 0, 1.0); } };
const RECAM = { B02B: () => tight(G(0).add(V(0.6, 0, 3.0))), B06: () => tight(G(5).add(V(0.6, 0, 3.0))), C07: () => [G(5).add(V(0.75, 0.6, 9.4)), G(5).add(V(0.7, 0.5, 0)), 40],
  C08: () => tight(G(5).add(V(0.6, 0, 3.0))), C09: () => [G(5).add(V(0.6, 0.2, 10.5)), G(5).add(V(0.6, 0, 0)), 46], 
  C12: () => [G(0).add(G(5)).multiplyScalar(0.5).add(V(1.0, 1.4, 12.0)), G(0).add(G(5)).multiplyScalar(0.5).add(V(1.0, 1.0, 0)), 44],
  B09: board('bbR'), B10: board('bbL'), F08: board('bbR'), C10: board('bbR'), D05: board('bbR'), C06: () => tight(G(5).add(V(0.6, 0, 3.0))), C11: () => [G(5).add(V(0.6, 0.6, 12.5)), G(5).add(V(0.4, 0.1, 0)), 44], G13: () => tight(G(5).add(V(0.6, 0, 3.0))),
  G05: () => [G(0).add(V(0.9, 0.6, 12.5)), G(0).add(V(1.4, -0.6, 0)), 44], G14: () => tight(G(0).add(V(0.6, 0, 3.0))),
  D02: () => tight(fwd(1)), G08: () => tight(fwd(3)), J14: () => tight(G(0).add(V(0.6, 0, 3.0))),
  E04: () => [G(0).add(V(1.6, -0.2, 10.5)), G(0).add(V(1.1, -1.0, 0)), 42] };
const CAPCOL = { You: B.C.mint, Ted: B.C.coral, Everyone: B.C.gold };
// each frame: [id, song time, what it is, setup() -> { cam: [pos, target, fov], cap: [who, line], gold, states(i) }]
const FRAMES = [
  ['B01', '0:02', 'Opening title: the waiting room, before the meeting starts', () => { show('lobby');   // no title card: the clouds carry the opening (one is a lightbulb)
    rooms.forEach((r) => { r.root.visible = false; });
    return { cam: [V(-5, GRID_Y + 1.4, GRID_Z + 17), V(0, GRID_Y + 3.0, GRID_Z - 2), 42] }; }],
  ['B02', '0:09', '"Tuesday, ten o\'clock, twelve people in a room." The tower clock says 10:00', () => { show('clock'); BO.clock.userData.set('10:00', 'TUESDAY');
    return { cam: [V(-11, GRID_Y + 1.6, GRID_Z + 24), V(1, GRID_Y + 2.2, GRID_Z - 6), 40], cap: ['You', "Tuesday, ten o'clock, twelve people in a room."],
      states: (i) => ({ talk: i === 0 ? 1 : 0, talkCol: 0x7fe0c2, expr: i === 0 ? { smile: 0.1, open: 0.45 } : undefined }) }; }],
  ['B03', '0:17', '"Nobody wrote it down." The meeting notes: Untitled, 0 words', () => { show('notes'); const g0 = G(0);
    { const k = G(0).add(G(1)).add(G(4)).add(G(5)).multiplyScalar(0.25); at(BO.notes, k.add(V(0, 0.62, 0.9)), 0, 0.9); }
    return { cam: [g0.clone().add(V(1.6, 0.9, 6.6)), g0.clone().add(V(1.3, 0.35, 0.4)), 36], cap: ['You', 'Nobody wrote it down.'],
      states: (i) => (i === 0 ? { expr: { smile: -0.15, brows: [0.6, 0.1], lids: 0.3, look: [0.8, -0.2] } } : { expr: { smile: 0.1, lids: 0.35, look: [i % 2 ? -0.9 : 0.9, -0.5] } }) }; }],
  ['B04', '0:19', '"Somebody checked their phone." Tom, mid-meeting, on his phone; his cat on the desk', () => { const g2 = G(2);
    return { cam: [g2.clone().add(V(-0.4, 0.75, 5.6)), g2.clone().add(V(-0.1, 0.05, 0)), 36],
      states: (i) => ({ phone: i === 2 ? 1 : 0, expr: i === 2 ? { smile: 0.25, lids: 0.5, look: [0, -1] } : { smile: 0.1, lids: 0.35, look: [0.4, -0.3] } }) }; }],
  ['B05', '0:28', '"Eight. I checked." Eight minutes have gone by: 08:00, verified', () => { show('timer', 'clock'); BO.clock.userData.set('10:08', 'TUESDAY');
    at(BO.timer, G(7).add(V(5.8, 0.4, 0.6)), -0.25, 1.4);   // beside the grid, never over a room
    return { cam: [V(-3.5, GRID_Y + 1.2, GRID_Z + 21), V(3.2, GRID_Y + 0.6, GRID_Z), 40], cap: ['You', 'Eight. I checked.'],
      states: (i) => ({ expr: i === 0 ? { smile: -0.1, brows: [0.9, -0.1], lids: 0.4 } : { smile: 0.05, lids: 0.55, look: [0.3, -0.3] } }) }; }],
  ['B06', '0:32', '"And then he says it." Ted\'s room slides out of the grid; the room goes dark around him', () => { show('bTed');
    const g5 = G(5), tp = g5.clone().add(V(0.6, 0, 3.0)); rooms[5].root.position.copy(slotPos(5, 4, 3).add(V(0.6, 0, 3.0))); rooms[5].root.scale.setScalar(1.12);
    at(BO.bTed, tp.clone().add(V(3.5, 0.75, 1.4)), -0.22, 2.3);
    return { cam: [tp.clone().add(V(-1.4, -0.6, 9.5)), tp.clone().add(V(1.3, 0.25, 0)), 42], cap: ['You', 'And then he says it.'],
      states: (i) => (i === 5 ? { talk: 1, talkCol: 0xff6b5b, expr: { smile: 0.55, open: 0.45, brows: 0.35 } } : { dark: 0.9, expr: { smile: 0, lids: 0.2, look: [0.3, 0] } }) }; }],
  ['B07', '0:34', 'Chorus: "Great idea, Ted." The sky lights up, the city goes gold, everyone claps', () => { show('chorusTitle', 'party');
    return { cam: [V(2.0, GRID_Y - 0.2, GRID_Z + 32), V(0, GRID_Y + 8.6, GRID_Z - 8), 56], gold: 1, capY: 0.9, cap: ['Everyone', 'Great idea, Ted'],
      states: (i) => (i === 5 ? { talk: 1, talkCol: 0xff6b5b, expr: { smile: 1, open: 0.35, brows: 0.65 } } : i === 0 ? { clap: 1, clapK: 0.2, expr: { smile: -0.05, brows: [0.85, -0.1], lids: 0.4 } }
        : { clap: 1, clapK: (i * 0.37) % 1, expr: { smile: 0.9, open: 0.6, brows: 0.5 } }) }; }],
  ['B08', '0:46', '"Somebody get this man a raise." His raise on a billboard', () => { show('bbL', 'raiseSpill'); BO.bbL.userData.set(BO.tex.raiseBg);
    return { cam: [V(-6.6, GRID_Y + 1.1, GRID_Z + 6.0), V(-12.6, GRID_Y + 1.7, GRID_Z - 6.5), 46], gold: 1, cap: ['Everyone', 'Somebody get this man a raise'],
      states: (i) => ({ clap: i === 5 ? 0 : 1, clapK: (i * 0.29) % 1, talk: i === 5 ? 1 : 0, talkCol: 0xff6b5b, expr: i === 5 ? { smile: 1, brows: 0.6 } : { smile: 0.9, open: 0.6, brows: 0.5 } }) }; }],
  ['B09', '0:48', '"Put him on the leadership page." The company site, on the other billboard', () => { show('bbR'); BO.bbR.userData.set(BO.tex.leaders);
    return { cam: [V(6.6, GRID_Y + 1.1, GRID_Z + 6.0), V(12.6, GRID_Y + 1.7, GRID_Z - 6.5), 46], gold: 1, cap: ['Everyone', 'Put him on the leadership page'],
      states: (i) => ({ clap: i === 5 ? 0 : 1, clapK: (i * 0.41) % 1, expr: i === 5 ? { smile: 1, brows: 0.6 } : { smile: 0.9, open: 0.6, brows: 0.5 } }) }; }],
  ['B10', '0:51', '"Give him equity today." An equity grant, approved', () => { show('bbL'); BO.bbL.userData.set(BO.tex.equity);
    return { cam: [V(-6.6, GRID_Y + 1.1, GRID_Z + 6.0), V(-12.6, GRID_Y + 1.7, GRID_Z - 6.5), 46], gold: 1, cap: ['Everyone', 'Give him equity today'],
      states: (i) => ({ clap: i === 5 ? 0 : 1, clapK: (i * 0.53) % 1, expr: i === 5 ? { smile: 1, brows: 0.6 } : { smile: 0.9, open: 0.6, brows: 0.5 } }) }; }],
  ['B04B', '0:23', '"Let\'s circle back." The twelve rooms swing out of the grid into a circle, Greg\'s line in the middle', () => { show('bGreg');
    const off = G(0).sub(slotPos(0, 4, 3)), R = 6.6, c = slotPos(0, 4, 3).add(slotPos(11, 4, 3)).multiplyScalar(0.5); c.y = slotPos(8, 4, 3).y + R + 0.35;   // the ring's bottom room stays on the roof
    rooms.forEach((r, i) => { const a = Math.PI / 2 - i * Math.PI / 6; r.root.position.set(c.x + R * Math.cos(a), c.y + R * Math.sin(a), c.z); });   // a clock face: You at 12, then clockwise
    const cw = c.clone().add(off); at(BO.bGreg, cw.clone().add(V(-0.9, 0.1, 0.4)), 0, 3.6);
    return { cam: [cw.clone().add(V(0, -0.6, 21.5)), cw.clone().add(V(0, -0.2, 0)), 46],
      states: (i) => ({ talk: i === 9 ? 1 : 0, talkCol: 0xb9c3ff, expr: i === 0 ? { smile: -0.25, brows: [0.8, -0.1], lids: 0.35 } : { smile: 0.15, lids: 0.3, look: [0, 0.3] } }) }; }],
  ['B04S', '0:21', '"Somebody opened Slack." Chat bubbles float out of the rooms', () => { show('bKofi', 'bPriya');
    at(BO.bKofi, G(4).add(V(-3.2, 0.9, 1.2)), 0.3, 2.3); at(BO.bPriya, G(8).add(V(-4.4, -0.05, 1.2)), 0.3, 2.3); BO.bKofi.userData.tail = 'right';
    return { cam: [V(-7.5, GRID_Y + 0.4, GRID_Z + 13.5), V(-3.2, GRID_Y - 0.8, GRID_Z), 44],
      states: (i) => ({ phone: i === 2 ? 1 : 0, expr: i === 2 ? { smile: 0.2, lids: 0.5, look: [0, -1] } : i === 0 ? { smile: -0.2, brows: [0.7, 0], lids: 0.35 } : { smile: 0.1, lids: 0.4, look: [0.6, -0.6] } }) }; }],
  ['B02B', '0:12', '"I said, We should push the launch. We\'re not ready and we know it." You say it first; nobody looks up', () => { show('bYou');
    const tp = G(0).add(V(0.6, 0, 3.0)); rooms[0].root.position.copy(slotPos(0, 4, 3).add(V(0.6, 0, 3.0))); rooms[0].root.scale.setScalar(1.12);   // the same move Ted gets in B06
    at(BO.bYou, tp.clone().add(V(3.5, 0.75, 1.4)), -0.22, 2.3);
    return { cam: [tp.clone().add(V(-1.4, -0.6, 9.5)), tp.clone().add(V(1.3, 0.25, 0)), 42],
      states: (i) => (i === 0 ? { talk: 1, talkCol: 0x7fe0c2, expr: { smile: 0.15, open: 0.45, brows: 0.3 } } : { expr: { smile: 0.05, lids: 0.45, look: [i % 2 ? -0.8 : 0.8, -0.6] } }) }; }],
  // ---------------------------------------------------------------- batch 2: verse 2, one frame per line (n = 213...)
  ['C01', '0:58', '"And he\'s not a bad guy." Ted, warm and smiling, with his profile card: not a bad guy', () => { show('prof1'); const tp = tedFwd();
    at(BO.prof1, tp.clone().add(V(3.0, 0.55, 1.3)), -0.22, 0.9);
    return { cam: [tp.clone().add(V(0.2, -0.1, 7.0)), tp.clone().add(V(1.5, 0.15, 0)), 38], states: (i) => (i === 5 ? { fine: 1, expr: { smile: 0.95, brows: 0.45, lids: 0.1 } } : { expr: { smile: 0.2, lids: 0.3 } }) }; }],
  ['C02', '1:00', '"That\'s the worst part." Back to you, deadpan; the card now has a second chip: the worst part', () => { show('prof2'); const g0 = G(0);
    at(BO.prof2, g0.clone().add(V(3.05, 0.35, 1.1)), -0.18, 0.95);
    return { cam: [g0.clone().add(V(1.5, 0.3, 7.8)), g0.clone().add(V(1.6, 0.1, 0)), 40], states: (i) => (i === 0 ? { expr: { smile: -0.25, brows: [0.75, -0.15], lids: 0.4, look: [0.9, -0.1] } } : { expr: { smile: 0.15, lids: 0.3 } }) }; }],
  ['C03', '1:01', '"He\'d give you his lunch." Ted holds his lunch bag out to you', () => { const tp = tedFwd();
    return { cam: [tp.clone().add(V(0.25, 0.2, 3.5)), tp.clone().add(V(0.05, 0.0, -0.6)), 36], states: (i) => (i === 5 ? { offer: 1, expr: { smile: 0.9, brows: 0.4, lids: 0.1 } } : {}) }; }],
  ['C04', '1:02', '"He remembers your kid\'s name." A sticky note on his laptop: ask about Ellie\'s recital!', () => { const tp = tedFwd();
    return { cam: [tp.clone().add(V(0.05, 0.05, 2.5)), tp.clone().add(V(0.0, -0.12, -0.6)), 36], states: (i) => (i === 5 ? { sticky: "ask about\nEllie's\nrecital!", expr: { smile: 0.6, lids: 0.15 } } : {}) }; }],
  ['C05', '1:04', '"He brings the good donuts." An open box of the good ones on his desk; the neighbors lean in', () => { const tp = tedFwd();
    return { cam: [tp.clone().add(V(0.6, 0.35, 3.4)), tp.clone().add(V(0.35, -0.2, -0.6)), 38], states: (i) => (i === 5 ? { donuts: 1, fine: 1, expr: { smile: 1, brows: 0.5 } } : { expr: { smile: 0.6, lids: 0.1, look: [i < 5 ? 0.6 : -0.6, -0.2] } }) }; }],
  ['C06', '1:06', '"He asks about your weekend" Ted, warmly: How was your weekend?', () => { show('bWeekend'); const tp = tedFwd();
    at(BO.bWeekend, tp.clone().add(V(3.4, 0.75, 1.4)), -0.22, 2.1);
    return { cam: [tp.clone().add(V(-1.4, -0.6, 9.5)), tp.clone().add(V(1.3, 0.25, 0)), 42], states: (i) => (i === 5 ? { talk: 1, talkCol: 0xff6b5b, expr: { smile: 0.85, open: 0.35, brows: 0.5 } } : { expr: { smile: 0.15, lids: 0.3 } }) }; }],
  ['C07', '1:08', '"and actually waits for the answer." The question stays open: still waiting, 0:41', () => { show('bWait'); const tp = tedFwd();
    at(BO.bWait, tp.clone().add(V(3.6, 0.85, 1.4)), -0.22, 1.45);
    return { cam: [tp.clone().add(V(-1.4, -0.6, 9.5)), tp.clone().add(V(1.3, 0.25, 0)), 42], states: (i) => (i === 5 ? { expr: { smile: 0.7, brows: 0.6, lids: 0.0, look: [0.2, 0.1] } } : { expr: { smile: 0.1, lids: 0.45, look: [i % 2 ? -0.8 : 0.8, -0.6] } }) }; }],
  ['C08', '1:10', '"He just says things slower." The sentence, stretched out', () => { show('bSlow'); const tp = tedFwd();
    at(BO.bSlow, tp.clone().add(V(3.6, 0.9, 1.4)), -0.22, 1);
    return { cam: [tp.clone().add(V(-1.4, -0.6, 9.5)), tp.clone().add(V(1.6, 0.25, 0)), 42], states: (i) => (i === 5 ? { talk: 1, talkCol: 0xff6b5b, expr: { smile: 0.4, open: 0.6, lids: 0.45, brows: 0.2 } } : { expr: { smile: 0.1, lids: 0.6 } }) }; }],
  ['C09', '1:12', '"He just says things louder." The same sentence, huge; the grid shakes', () => { show('bLoud'); const tp = tedFwd();
    at(BO.bLoud, tp.clone().add(V(3.9, 1.3, 1.5)), -0.2, 1);
    rooms.forEach((r, i) => { if (i !== 5) { r.root.rotation.z = Math.sin(i * 2.7) * 0.035; r.root.position.x += Math.sin(i * 1.3) * 0.08; } });
    return { cam: [tp.clone().add(V(-1.4, -0.6, 10.5)), tp.clone().add(V(1.9, 0.5, 0)), 44], states: (i) => (i === 5 ? { talk: 1, talkCol: 0xff6b5b, expr: { smile: 0.3, open: 1, brows: 0.9 } } : { expr: { smile: -0.2, lids: 0, brows: 0.9, look: [0, 0.2] } }) }; }],
  ['C10', '1:14', '"Apparently that\'s leadership." The definition, on the billboard', () => { show('bbR'); BO.bbR.userData.set(BO.tex.dict);
    return { cam: [V(6.6, GRID_Y + 1.1, GRID_Z + 6.0), V(12.6, GRID_Y + 1.7, GRID_Z - 6.5), 46], states: () => ({ expr: { smile: 0.1, lids: 0.3 } }) }; }],
  ['C11', '1:17', '"He said: We should push the launch..." Ted says your sentence; this time everyone turns to him', () => { show('bTed'); const tp = tedFwd();
    at(BO.bTed, tp.clone().add(V(3.5, 0.75, 1.4)), -0.22, 2.3);
    return { cam: [tp.clone().add(V(-1.4, -0.6, 9.5)), tp.clone().add(V(1.3, 0.25, 0)), 42], states: (i) => (i === 5 ? { talk: 1, talkCol: 0xff6b5b, expr: { smile: 0.55, open: 0.45, brows: 0.35 } } : i === 0 ? { expr: { smile: -0.2, brows: [0.8, -0.1], lids: 0.3, look: [0.7, -0.3] } } : { expr: { smile: 0.75, brows: 0.5, lids: 0.05, look: [0.4, -0.2] } }) }; }],
  ['C12', '1:23', '"Word. For. Word." Both sentences side by side, timestamped: diff, 0 changes', () => { show('wfw');
    const g0 = G(0), g5 = G(5); rooms[0].root.position.add(V(-0.4, 0, 2.6)); rooms[5].root.position.add(V(0.4, 0, 2.6));
    const mid = g0.clone().add(g5).multiplyScalar(0.5); at(BO.wfw, mid.clone().add(V(4.3, 3.45, 3.8)), -0.15, 1.3);
    return { cam: [mid.clone().add(V(1.8, 0.9, 13.5)), mid.clone().add(V(2.4, 1.7, 0)), 46], states: (i) => (i === 0 ? { expr: { smile: -0.15, brows: [0.85, -0.1], lids: 0.3, look: [0.8, 0] } } : i === 5 ? { expr: { smile: 0.9, brows: 0.4 } } : { dark: 0.6 }) }; }],
  ['C13', '1:27', '"Which is interesting." You, one eyebrow up', () => { show('interesting'); const g0 = G(0);
    at(BO.interesting, g0.clone().add(V(0.78, 0.9, 0.2)), 0, 0.42);
    return { cam: [g0.clone().add(V(0.6, 0.5, 4.6)), g0.clone().add(V(0.7, 0.25, 0)), 34], states: (i) => (i === 0 ? { expr: { smile: 0.12, browTilt: 0.8, brows: 0.4, lids: 0.25, look: [0.5, 0] } } : {}) }; }],
  // ---------------------------------------------------------------- batch 3: pre-chorus 2, chorus 2, the donuts (n = 226...)
  ['D01', '1:28', '"And then somebody says," Dana, the VP, unmutes', () => { const g1 = G(1);
    return { cam: [g1.clone().add(V(0.3, 0.4, 5.4)), g1.clone().add(V(0.1, 0.1, 0)), 36], states: (i) => (i === 1 ? { talk: 1, talkCol: 0x5ee08f, expr: { smile: 0.45, open: 0.55, brows: 0.5 } } : { expr: { smile: 0.1, lids: 0.3 } }) }; }],
  ['D02', '1:30', '"Ted, that\'s exactly what we needed." Dana says it to the whole room', () => { show('bDana'); const g1 = G(1);
    at(BO.bDana, g1.clone().add(V(2.9, 2.15, 1.3)), -0.2, 2.2);
    return { cam: [g1.clone().add(V(-0.6, -0.4, 9.2)), g1.clone().add(V(1.9, 0.0, 0)), 42], states: (i) => (i === 1 ? { talk: 1, talkCol: 0x5ee08f, expr: { smile: 0.85, open: 0.5, brows: 0.5 } } : i === 5 ? { expr: { smile: 1, brows: 0.6 } } : i === 0 ? { expr: { smile: -0.25, brows: [0.85, -0.1], lids: 0.35 } } : { expr: { smile: 0.5, lids: 0.15 } }) }; }],
  ['D03', '1:33', 'Chorus 2: "Great idea, Ted." Gold city, reactions everywhere, from a new angle', () => { show('chorusTitle', 'party');
    return { cam: [V(-8.5, GRID_Y - 0.8, GRID_Z + 28), V(0.5, GRID_Y + 6.6, GRID_Z - 8), 56], gold: 1,
      states: (i) => (i === 5 ? { talk: 1, talkCol: 0xff6b5b, expr: { smile: 1, open: 0.35, brows: 0.65 } } : i === 0 ? { clap: 1, clapK: 0.15, expr: { smile: -0.1, brows: [0.85, -0.1], lids: 0.45 } } : { clap: 1, clapK: (i * 0.43) % 1, expr: { smile: 0.9, open: 0.6, brows: 0.5 } }) }; }],
  ['D04', '1:45', '"Somebody get this man a raise." Again: the digits have escaped and rain over the city', () => { show('bbL', 'raiseSpill', 'digitRain'); BO.bbL.userData.set(BO.tex.raiseBg);
    return { cam: [V(-5.6, GRID_Y + 0.4, GRID_Z + 8.0), V(-13.2, GRID_Y + 2.6, GRID_Z - 6.5), 52], gold: 1, states: (i) => ({ clap: i === 5 ? 0 : 1, clapK: (i * 0.31) % 1, expr: { smile: 0.9, open: 0.5, brows: 0.5, look: [0, 1] } }) }; }],
  ['D05', '1:47', '"Get his face on the website" The company homepage, on the billboard: Meet Ted. Visionary.', () => { show('bbR'); BO.bbR.userData.set(BO.tex.hero);
    return { cam: [V(6.6, GRID_Y + 1.1, GRID_Z + 6.0), V(12.6, GRID_Y + 1.7, GRID_Z - 6.5), 46], gold: 1, states: (i) => ({ clap: i === 5 ? 0 : 1, clapK: (i * 0.37) % 1, expr: { smile: 0.9, open: 0.5, brows: 0.5 } }) }; }],
  ['D06', '1:49', '"Book his TED Talk" Ted\'s room rolls out onto a red round stage under a spotlight', () => { show('stage', 'talkSign');
    const c = G(5).add(V(0, -RH / 2 + 0.03, 8.5)); c.y = slotPos(8, 4, 3).y - RH / 2 + G(0).y - slotPos(0, 4, 3).y + 0.03; BO.stage.position.copy(c);
    rooms[5].root.position.copy(c.clone().sub(G(0).sub(slotPos(0, 4, 3)))).add(V(0, RH / 2 + 0.06, 0)); rooms[5].root.scale.setScalar(1.1);
    at(BO.talkSign, c.clone().add(V(0, 5.6, -3.8)), 0, 1.15);
    return { cam: [c.clone().add(V(-1.8, 1.4, 8.6)), c.clone().add(V(0, 2.4, -0.5)), 48], gold: 1, states: (i) => (i === 5 ? { talk: 1, talkCol: 0xff6b5b, fine: 1, expr: { smile: 1, open: 0.3, brows: 0.6 } } : { dark: 0.75, clap: 1, clapK: (i * 0.29) % 1 }) }; }],
  ['D07', '1:50', '"Unless." The party stops. Every room goes dark except yours', () => { show('spot'); const g0 = G(0); BO.spot.position.copy(g0.clone().add(V(0, -RH / 2, 0.4))); BO.spot.scale.set(1, 1, 1); BO.spot.children[0].material.opacity = 0.07;
    return { cam: [g0.clone().add(V(1.2, 0.6, 7.2)), g0.clone().add(V(0.9, 0.1, 0)), 38], states: (i) => (i === 0 ? { expr: { smile: 0.05, brows: [-0.3, 0.6], lids: 0.45, look: [0.4, 0] } } : { dark: 0.85 }) }; }],
  ['D08', '1:51', '"Unless it\'s the donuts." Close on Ted\'s box of the good ones; the rest of the meeting goes dark', () => { const tp = tedFwd();
    return { cam: [tp.clone().add(V(0.7, 0.5, 2.1)), tp.clone().add(V(0.4, -0.04, -0.55)), 42], states: (i) => (i === 5 ? { donuts: 1, expr: { smile: 0.6, look: [0.5, -0.6] } } : { dark: 0.85 }) }; }],
  ['D09', '1:52', '"Is it the donuts?" A giant donut over the city, under a magnifying glass; everyone looks up', () => { show('bigDonut');
    BO.bigDonut.position.copy(G(5).add(V(1.5, 10.0, -3))); BO.bigDonut.rotation.set(0.25, -0.15, 0.1); BO.bigDonut.scale.setScalar(1.4);
    return { cam: [V(-3.0, GRID_Y - 0.6, GRID_Z + 22), V(1.0, GRID_Y + 6.0, GRID_Z - 4), 54], states: (i) => ({ lookYaw: 0, expr: { smile: 0.1, open: 0.3, brows: 0.8, lids: 0, look: [0, 1] } }) }; }],
  // ---------------------------------------------------------------- batch 4: the bridge (n = 235...)
  ['E01', '1:54', '"For the record," Your room comes forward; the official minutes open beside it, big', () => { show('rec1'); const tp = youFwd();
    at(BO.rec1, tp.clone().add(V(3.7, 0.45, 1.5)), -0.2, 1.3);
    return { cam: [tp.clone().add(V(-0.6, -0.3, 9.6)), tp.clone().add(V(2.2, 0.3, 0)), 42], states: (i) => (i === 0 ? { expr: { smile: 0, brows: 0.25, lids: 0.3 } } : { dark: 0.7 }) }; }],
  ['E02', '1:55', '"I said it first." Close on the minutes: 10:00:04, you, and a gold FIRST stamp', () => { show('rec2'); const tp = youFwd();
    const c = tp.clone().add(V(3.7, 0.45, 1.5)); at(BO.rec2, c, -0.2, 1.3);
    return { cam: [c.clone().add(V(-0.9, 0.1, 4.2)), c.clone().add(V(0.15, 0.55, 0)), 40], states: (i) => (i === 0 ? { talk: 1, talkCol: 0x5ee08f, expr: { smile: 0.2, open: 0.45, brows: 0.35 } } : { dark: 0.7 }) }; }],
  ['E03', '1:58', '"I\'m not upset that he said it." Close on you, calm; a green chip beside you: not upset he said it', () => { show('pGood'); const g0 = G(0);
    at(BO.pGood, g0.clone().add(V(0.72, 0.02, 0.35)), 0, 0.72);
    return { cam: [g0.clone().add(V(0.35, 0.5, 3.0)), g0.clone().add(V(0.3, 0.32, -1.1)), 34], states: (i) => (i === 0 ? { expr: { smile: 0.3, lids: 0.4, brows: 0.1 } } : {}) }; }],
  ['E04', '2:00', '"I\'m upset that it worked." You, with a red chip; below you Ted\'s room glows gold, thumbs up', () => { show('pBad'); const tp = youFwd();
    at(BO.pBad, tp.clone().add(V(0.3, 1.5, 1.4)), 0, 1.3);
    return { cam: [tp.clone().add(V(0.9, -0.1, 7.8)), tp.clone().add(V(1.0, -0.5, 0)), 44], gold: 0.4,
      states: (i) => (i === 0 ? { expr: { smile: -0.45, brows: [0.9, -0.2], lids: 0.3, look: [0.7, -0.6] } } : i === 5 ? { talk: 1, talkCol: 0xffd27a, fine: 1, expr: { smile: 1, brows: 0.6 } } : { dark: 0.65 }) }; }],
  ['E05', '2:03', '"I\'m actually becoming" Close on you, eyes shut, one long breath; status: becoming...', () => { show('pBecoming'); const g0 = G(0);
    at(BO.pBecoming, g0.clone().add(V(0.95, 0.02, -0.25)), 0, 0.8);
    return { cam: [g0.clone().add(V(0.35, 0.5, 3.0)), g0.clone().add(V(0.3, 0.32, -1.1)), 34], states: (i) => (i === 0 ? { expr: { smile: 0.05, lids: 1, brows: 0.2 } } : {}) }; }],
  ['E06', '2:05', '"extremely normal about this." The smile is a little too big; the grid behind you has gone crooked', () => { show('pNormal'); const tp = youFwd();
    rooms.forEach((r, i) => { if (i !== 0) r.root.rotation.z = Math.sin(i * 2.1) * 0.07; });
    at(BO.pNormal, tp.clone().add(V(0.25, 1.65, 1.4)), 0, 1.6);
    return { cam: [tp.clone().add(V(0.1, 0.2, 7.0)), tp.clone().add(V(0.3, 0.45, 0)), 40], states: (i) => (i === 0 ? { expr: { smile: 1, open: 0.15, brows: 0.8, lids: 0 } } : { expr: { smile: 0.1, lids: 0.4 } }) }; }],
  // ---------------------------------------------------------------- batch 5: verse 3 part 1, the paper trail (n = 241...)
  ['F01', '2:08', '"So now I put it in the notes." The notes doc from B03, now with your sentence in it', () => { show('notesFilled'); const tp = youFwd();
    at(BO.notesFilled, tp.clone().add(V(3.7, 0.45, 1.5)), -0.2, 1.2);
    return { cam: [tp.clone().add(V(-0.6, -0.3, 9.6)), tp.clone().add(V(2.2, 0.3, 0)), 42], states: (i) => (i === 0 ? { expr: { smile: 0.15, brows: 0.3, lids: 0.2, look: [0.8, 0] } } : { dark: 0.6 }) }; }],
  ['F02', '2:10', '"I put it in the deck." The deck goes up on the billboard: Push the launch.', () => { show('bbL'); BO.bbL.userData.set(BO.tex.deck);
    return { cam: [V(-6.6, GRID_Y + 1.1, GRID_Z + 6.0), V(-12.6, GRID_Y + 1.7, GRID_Z - 6.5), 46], states: () => ({ expr: { smile: 0.1, lids: 0.3 } }) }; }],
  ['F03', '2:12', '"I put my name at the top of the page" Push in on the slide: by You, circled', () => deckClose('deckName', -2.3, 1.5)],
  ['F04', '2:14', '"in thirty-two-point text." Push in on the font menu: Inter, 32 pt', () => deckClose('deckSize', 3.0, 2.3)],
  ['F05', '2:17', '"I put it in the footer." Push in on the footer: idea: You, idea: You, idea: You', () => deckClose('deckFooter', -0.6, -1.5)],
  ['F06', '2:18', '"I put it in the file name:" Push in on the title bar: my_idea_do_not_rephrase_v7_FINAL.deck', () => deckClose('deckFile', -1.6, 2.35)],
  ['F07', '2:20', '"My idea, do not rephrase, V7, final." The file name, in neon, across the sky', () => { show('fileNeon'); BO.fileNeon.position.set(0, GRID_Y + 14.6, GRID_Z - 14);
    return { cam: [V(2.0, GRID_Y - 0.2, GRID_Z + 32), V(0, GRID_Y + 8.6, GRID_Z - 8), 56], states: (i) => (i === 0 ? { expr: { smile: 0.4, brows: 0.6 } } : { expr: { smile: 0.1, lids: 0.4 } }) }; }],
  ['F08', '2:24', '"I sent it before the meeting." The email on the billboard: sent 8:59 AM, to everyone@', () => { show('bbR'); BO.bbR.userData.set(BO.tex.email);
    return { cam: [V(6.6, GRID_Y + 1.1, GRID_Z + 6.0), V(12.6, GRID_Y + 1.7, GRID_Z - 6.5), 46], states: () => ({ expr: { smile: 0.1, lids: 0.3 } }) }; }],
  ['F09', '2:27', '"I printed out a copy." A printer on your desk, your sentence coming out of it', () => { const g0 = G(0);
    return { cam: [g0.clone().add(V(-0.55, 0.35, 2.3)), g0.clone().add(V(-0.35, 0.2, -0.75)), 40], states: (i) => (i === 0 ? { printer: 1, paperFloat: 1, expr: { smile: 0.3, brows: 0.45, look: [-0.6, 0.2] } } : {}) }; }],
  ['F10', '2:29', '"I mailed one to myself." An envelope beside your room: To: me, From: me', () => { show('env1'); const tp = youFwd();
    at(BO.env1, tp.clone().add(V(3.5, 0.4, 1.5)), -0.2, 1.1);
    return { cam: [tp.clone().add(V(-0.6, -0.3, 9.0)), tp.clone().add(V(2.1, 0.3, 0)), 42], states: (i) => (i === 0 ? { expr: { smile: 0.2, brows: 0.2 } } : { dark: 0.6 }) }; }],
  ['F11', '2:31', '"Certified." The stamp comes down: CERTIFIED', () => { show('env2'); const tp = youFwd(); const c = tp.clone().add(V(3.5, 0.4, 1.5));
    at(BO.env2, c, -0.2, 1.1);
    return { cam: [c.clone().add(V(-0.8, 0.0, 4.2)), c.clone().add(V(0, 0.05, 0)), 42], states: (i) => (i === 0 ? { expr: { smile: 0.3, brows: 0.5 } } : { dark: 0.6 }) }; }],
  ['F12', '2:33', '"I said it again on Thursday." This week, Thursday lit up pink: said it again', () => { show('week1'); const g0 = G(0); at(BO.week1, G(1).add(V(1.6, 2.8, 1.2)), 0, 1.3);
    return { cam: [G(1).add(V(0.6, 1.2, 9.5)), G(1).add(V(1.1, 1.3, 0)), 44], states: (i) => (i === 0 ? { talk: 1, talkCol: 0x5ee08f, expr: { smile: 0.15, open: 0.45, brows: 0.35 } } : { expr: { smile: 0.1, lids: 0.45, look: [0.5, -0.6] } }) }; }],
  ['F13', '2:36', '"First." A gold 1st ribbon pins itself to Thursday', () => { show('week2'); const c = G(1).add(V(1.6, 2.7, 1.2)); at(BO.week2, c, 0, 1);
    return { cam: [c.clone().add(V(-0.3, -0.4, 5.6)), c.clone().add(V(0.0, -0.2, 0)), 44], states: () => ({}) }; }],
  // ---------------------------------------------------------------- batch 6: verse 3 part 2, the donuts and the log (n = 254...)
  ['G01', '2:37', '"I brought donuts." Your own pink box, open on your desk', () => { const g0 = G(0);
    return { cam: [g0.clone().add(V(0.0, 0.45, 2.9)), g0.clone().add(V(-0.15, -0.05, -0.75)), 40], states: (i) => (i === 0 ? { donuts: 1, fine: 1, expr: { smile: 0.75, brows: 0.45 } } : {}) }; }],
  ['G02', '2:39', '"I brought the good ones." Close on the box: the good ones', () => { const g0 = G(0);
    return { cam: [g0.clone().add(V(-0.62, 0.42, 0.55)), g0.clone().add(V(-0.6, -0.2, -0.5)), 44], states: (i) => (i === 0 ? { donuts: 1, expr: { smile: 0.6 } } : {}) }; }],
  ['G03', '2:41', '"The ones with the filling" One of them, up close: powdered sugar, a bite out, raspberry jam', () => { show('filledCard'); const g0 = G(0);
    at(BO.filledCard, g0.clone().add(V(2.3, 1.85, 1.6)), -0.12, 1.25);
    return { cam: [g0.clone().add(V(1.2, 1.05, 7.6)), g0.clone().add(V(1.4, 1.15, 0)), 42], states: (i) => (i === 0 ? { donuts: 1, expr: { smile: 0.8, brows: 0.6, look: [0.8, 0.1] } } : {}) }; }],
  ['G04', '2:42', '"you can\'t get after eight." The bakery\'s sign: SOLD OUT AFTER 8:00', () => { show('bakery'); const g0 = G(0); at(BO.bakery, g0.clone().add(V(3.4, 0.55, 1.4)), -0.15, 1);
    return { cam: [g0.clone().add(V(1.4, 0.3, 7.6)), g0.clone().add(V(2.0, 0.3, 0)), 42], states: (i) => (i === 0 ? { donuts: 1, expr: { smile: 0.5, brows: 0.6 } } : {}) }; }],
  ['G05', '2:44', '"I said the sentence" You say it again, box on the desk; your tile is green', () => { show('bYou'); const tp = youFwd();
    at(BO.bYou, tp.clone().add(V(3.5, 0.75, 1.4)), -0.22, 2.3);
    return { cam: [tp.clone().add(V(-1.4, -0.6, 9.5)), tp.clone().add(V(1.3, 0.25, 0)), 42], states: (i) => (i === 0 ? { donuts: 1, talk: 1, talkCol: 0x5ee08f, expr: { smile: 0.2, open: 0.45, brows: 0.35 } } : { expr: { smile: 0.05, lids: 0.45, look: [i % 2 ? -0.8 : 0.8, -0.6] } }) }; }],
  ['G06', '2:46', '"and I set down the box" Close on the box landing on your desk', () => { const g0 = G(0);
    return { cam: [g0.clone().add(V(0.15, 0.3, 2.1)), g0.clone().add(V(-0.22, 0.02, -0.7)), 38], states: (i) => (i === 0 ? { donuts: 1, expr: { smile: 0.2, look: [-0.5, -0.8] } } : {}) }; }],
  ['G07', '2:48', '"and I waited." The whole grid, silent; next to you: still waiting, 1:12', () => { show('pWaitYou'); const tp = youFwd();
    at(BO.pWaitYou, tp.clone().add(V(0.25, 1.55, 1.4)), 0, 1.3);
    return { cam: [tp.clone().add(V(2.0, -0.2, 11.0)), tp.clone().add(V(2.2, -1.0, 0)), 46], states: (i) => (i === 0 ? { donuts: 1, expr: { smile: 0.1, brows: 0.7, lids: 0.05 } } : { expr: { smile: 0, lids: 0.5, look: [i % 2 ? -0.8 : 0.8, -0.7] } }) }; }],
  ['G08', '2:51', '"Somebody said, Oh, Ted usually brings those." Mike unmutes', () => { show('bMike'); const g3 = G(3);
    at(BO.bMike, g3.clone().add(V(-1.6, 2.2, 1.4)), 0.15, 2.2);
    return { cam: [g3.clone().add(V(-2.8, -0.2, 9.0)), g3.clone().add(V(-1.6, 0.6, 0)), 42], states: (i) => (i === 3 ? { talk: 1, talkCol: 0x5ee08f, expr: { smile: 0.7, open: 0.45, brows: 0.4 } } : i === 0 ? { donuts: 1, expr: { smile: -0.3, brows: [0.9, -0.1], lids: 0.3 } } : {}) }; }],
  ['G09', '2:54', '"Timestamp: 9:04." The meeting log: 9:04, you, we should push the launch', () => { show('log1'); const tp = youFwd(); at(BO.log1, tp.clone().add(V(3.8, 0.4, 1.5)), -0.2, 1.2);
    return { cam: [tp.clone().add(V(-0.4, -0.3, 9.8)), tp.clone().add(V(2.4, 0.3, 0)), 42], states: (i) => (i === 0 ? { donuts: 1, expr: { smile: 0.1, brows: 0.3 } } : { dark: 0.6 }) }; }],
  ['G10', '2:57', '"Ted joined at 9:07." The log adds a grey line: 9:07, Ted joined the meeting', () => { show('log2'); const tp = youFwd(); const c = tp.clone().add(V(3.8, 0.4, 1.5)); at(BO.log2, c, -0.2, 1.2);
    return { cam: [c.clone().add(V(-0.7, 0.2, 4.8)), c.clone().add(V(0, 0.45, 0)), 42], states: (i) => (i === 0 ? { donuts: 1 } : { dark: 0.6 }) }; }],
  ['G11', '2:59', '"I have witnesses." Six witnesses on the log; six rooms raise their hands', () => { show('log3'); const g0 = G(0); at(BO.log3, G(3).add(V(3.9, 0.2, 2.6)), -0.2, 1.0);
    return { cam: [G(5).add(V(3.2, 0.4, 14.5)), G(5).add(V(3.6, 0.2, 0)), 50], states: (i) => ([0, 1, 2, 3, 6, 7].includes(i) ? { card: 1, expr: { smile: 0.4, brows: 0.6 } } : { expr: { smile: 0.05, lids: 0.4 } }) }; }],
  ['G12', '3:02', '"And Ted said," Ted unmutes; his tile turns green', () => { const tp = tedFwd();
    return { cam: [tp.clone().add(V(0.3, 0.4, 5.4)), tp.clone().add(V(0.1, 0.1, 0)), 36], states: (i) => (i === 5 ? { talk: 1, talkCol: 0x5ee08f, expr: { smile: 0.8, open: 0.3, brows: 0.5 } } : {}) }; }],
  ['G13', '3:03', '"Nice deck." Ted, beaming; your deck on the billboard behind', () => { show('bNice', 'bbL'); BO.bbL.userData.set(BO.tex.deck); const tp = tedFwd();
    at(BO.bNice, tp.clone().add(V(3.2, 0.85, 1.4)), -0.22, 2.4);
    return { cam: [tp.clone().add(V(-1.4, -0.6, 9.5)), tp.clone().add(V(1.3, 0.25, 0)), 42], states: (i) => (i === 5 ? { talk: 1, talkCol: 0x5ee08f, fine: 1, expr: { smile: 1, open: 0.35, brows: 0.6 } } : i === 0 ? { expr: { smile: -0.2, brows: [0.85, -0.1], lids: 0.35 } } : { expr: { smile: 0.5 } }) }; }],
  ['G14', '3:05', '"Thank you, Ted." You, the thinnest possible smile', () => { show('bThanks'); const tp = youFwd();
    at(BO.bThanks, tp.clone().add(V(3.2, 0.85, 1.4)), -0.22, 2.3);
    return { cam: [tp.clone().add(V(-1.4, -0.6, 9.5)), tp.clone().add(V(1.3, 0.25, 0)), 42], states: (i) => (i === 0 ? { talk: 1, talkCol: 0x5ee08f, expr: { smile: 0.35, lids: 0.45, brows: [0.6, -0.2] } } : { dark: 0.5 }) }; }],
  // ---------------------------------------------------------------- batch 7: final chorus, post-chorus (n = 268...)
  ['H01', '3:07', 'Final chorus: "Great idea, Ted." Biggest one yet, from high above the roof', () => { show('chorusTitle', 'party');
    return { cam: [V(0, GRID_Y + 5.0, GRID_Z + 31), V(0, GRID_Y + 7.0, GRID_Z - 6), 60], gold: 1,
      states: (i) => (i === 5 ? { talk: 1, talkCol: 0xff6b5b, fine: 1, expr: { smile: 1, open: 0.35, brows: 0.65 } } : i === 0 ? { expr: { smile: 0.05, brows: [0.85, -0.1], lids: 0.5 } } : { clap: 1, clapK: (i * 0.41) % 1, expr: { smile: 0.95, open: 0.65, brows: 0.55 } }) }; }],
  ['H02', '3:18', '"Somebody get this man a raise" Third time: the digits now fill the whole sky', () => { show('bbL', 'raiseSpill', 'digitRain'); BO.bbL.userData.set(BO.tex.raiseBg);
    BO.digitRain.scale.set(1.8, 1.3, 1); BO.digitRain.position.set(13, -8, 0);
    return { cam: [V(-4.0, GRID_Y + 0.2, GRID_Z + 11.0), V(-13.0, GRID_Y + 4.0, GRID_Z - 6.5), 58], gold: 1, states: (i) => ({ clap: i === 5 || i === 0 ? 0 : 1, clapK: (i * 0.31) % 1, expr: { smile: 0.9, open: 0.5, brows: 0.5, look: [0, 1] } }) }; }],
  ['H03', '3:20', '"Make him VP by Friday" The org chart on the billboard: Ted on top, everyone reports to Ted', () => { show('bbR'); BO.bbR.userData.set(BO.tex.org); BO.bbR.updateMatrixWorld(true);
    return { cam: [BO.bbR.localToWorld(V(-0.3, 36.2, 3.9 + 7.4)), BO.bbR.localToWorld(V(0, 36, 3.9)), 44], gold: 1, states: (i) => ({ clap: i === 0 ? 0 : 1, clapK: (i * 0.37) % 1, expr: { smile: 0.9, open: 0.5, brows: 0.5 } }) }; }],
  ['H04', '3:23', '"Name a conference room" Ted\'s room gets a sign: The Ted Room', () => { show('roomSign'); const tp = tedFwd();
    at(BO.roomSign, tp.clone().add(V(0.15, 2.35, 1.2)), 0, 1);
    return { cam: [tp.clone().add(V(0.3, 0.6, 9.2)), tp.clone().add(V(0.2, 1.2, 0)), 42], gold: 0.6, states: (i) => (i === 5 ? { fine: 1, expr: { smile: 1, brows: 0.6 } } : { clap: 1, clapK: (i * 0.29) % 1, dark: 0.35 }) }; }],
  ['H05', '3:25', '"after his brave discovery" The plaque, on a dark wall under a picture light, behind a velvet rope', () => { show('plaqueWall'); const c = G(5).add(V(0, 1.0, 9.0)); at(BO.plaqueWall, c, 0, 1);
    return { cam: [c.clone().add(V(0, 0.45, 5.2)), c.clone().add(V(0, 0.5, 0)), 44], states: () => ({}) }; }],
  ['I01', '3:30', '"Innovation." One word, in neon, over the whole city', () => { show('wInno'); BO.wInno.position.set(0, GRID_Y + 12.0, GRID_Z - 14);
    return { cam: [V(0, GRID_Y + 1.0, GRID_Z + 26), V(0, GRID_Y + 6.0, GRID_Z - 6), 52], states: (i) => (i === 5 ? { fine: 1, expr: { smile: 1, brows: 0.6 } } : { expr: { smile: 0.4, brows: 0.6, look: [0, 1] } }) }; }],
  ['I02', '3:40', '"Leadership." The next word, from a new angle', () => { show('wLead'); BO.wLead.position.set(-6, GRID_Y + 11.0, GRID_Z - 14); BO.wLead.rotation.y = 0.25;
    return { cam: [V(-10, GRID_Y + 0.5, GRID_Z + 22), V(-4, GRID_Y + 6.0, GRID_Z - 6), 52], states: (i) => (i === 5 ? { fine: 1, expr: { smile: 1, brows: 0.6 } } : { expr: { smile: 0.4, brows: 0.6, look: [0, 1] } }) }; }],
  ['I03', '3:41', '"Vision." The last word, gold', () => { show('wVis'); BO.wVis.position.set(6, GRID_Y + 11.0, GRID_Z - 14); BO.wVis.rotation.y = -0.25;
    return { cam: [V(10, GRID_Y + 0.5, GRID_Z + 22), V(4, GRID_Y + 6.0, GRID_Z - 6), 52], states: (i) => (i === 5 ? { fine: 1, expr: { smile: 1, brows: 0.6 } } : { expr: { smile: 0.4, brows: 0.6, look: [0, 1] } }) }; }],
  ['I04', '3:34', '"He repeated a sentence." The neon switches off; just you, flat, in the only lit room', () => { show('wInno', 'wLead', 'wVis'); const tp = youFwd();
    [[BO.wInno, -4.6], [BO.wLead, 0], [BO.wVis, 4.6]].forEach(([o, x]) => { o.position.copy(tp.clone().add(V(x + 1.0, 3.3, -3))); o.scale.setScalar(0.07); o.rotation.y = 0; o.material.color.setScalar(0.16); });   // the signs, switched off
    return { cam: [tp.clone().add(V(0.9, 0.6, 9.0)), tp.clone().add(V(0.9, 1.3, 0)), 42], states: (i) => (i === 0 ? { talk: 1, talkCol: 0x5ee08f, expr: { smile: -0.1, open: 0.35, brows: 0.25, lids: 0.35 } } : { dark: 0.75 }) }; }],
  ['I05', '3:43', '"He repeated my sentence." The sky answers back: HE REPEATED MY SENTENCE.', () => { show('wMy'); BO.wMy.position.set(0, GRID_Y + 15.0, GRID_Z - 14);
    return { cam: [V(0, GRID_Y - 0.6, GRID_Z + 25), V(0, GRID_Y + 6.0, GRID_Z - 6), 54], states: (i) => (i === 0 ? { talk: 1, talkCol: 0x5ee08f, expr: { smile: -0.2, brows: [0.9, -0.1], lids: 0.2 } } : i === 5 ? { expr: { smile: 0.5, brows: 0.2 } } : { dark: 0.6 }) }; }],
  // ---------------------------------------------------------------- batch 8: the outro (n = 278...)
  ['J01', '3:46', '"Great idea, Ted." The party is over: the grid at dusk, everyone back at their laptops, Ted still beaming', () => {
    return { cam: [V(-2.5, GRID_Y + 0.6, GRID_Z + 17), V(0, GRID_Y + 0.3, GRID_Z), 40], states: (i) => (i === 5 ? { fine: 1, expr: { smile: 1, brows: 0.6 } } : i === 0 ? { expr: { smile: 0.05, lids: 0.45, brows: 0.2 } } : { expr: { smile: 0.1, lids: 0.45, look: [0.4, -0.6] } }) }; }],
  ['J02', '3:49', '"Really." Close on you, one word', () => { show('pReally'); const g0 = G(0); at(BO.pReally, g0.clone().add(V(0.72, 0.02, 0.35)), 0, 0.72);
    return { cam: [g0.clone().add(V(0.35, 0.5, 3.0)), g0.clone().add(V(0.3, 0.32, -1.1)), 34], states: (i) => (i === 0 ? { talk: 1, talkCol: 0x5ee08f, expr: { smile: 0.1, lids: 0.45, brows: 0.15 } } : {}) }; }],
  ['J03', '3:50', '"Fantastic." The smile, slightly too wide', () => { show('pFantastic'); const g0 = G(0); at(BO.pFantastic, g0.clone().add(V(0.72, 0.02, 0.35)), 0, 0.72);
    return { cam: [g0.clone().add(V(0.35, 0.5, 3.0)), g0.clone().add(V(0.3, 0.32, -1.1)), 34], states: (i) => (i === 0 ? { talk: 1, talkCol: 0x5ee08f, expr: { smile: 0.95, lids: 0.1, brows: 0.6 } } : {}) }; }],
  ['J04', '3:52', '"I\'m happy for you." You and Ted, side by side; he waves, you don\'t', () => { show('pHappy'); const tp = tedFwd(); const yp = youFwd();
    const mid = tp.clone().add(yp).multiplyScalar(0.5); at(BO.pHappy, yp.clone().add(V(0.6, 1.55, 1.4)), 0, 2.0);
    return { cam: [mid.clone().add(V(0, 0.4, 11.5)), mid.clone().add(V(0, 0.2, 0)), 44], states: (i) => (i === 5 ? { fine: 1, expr: { smile: 1, brows: 0.6 } } : i === 0 ? { talk: 1, talkCol: 0x5ee08f, expr: { smile: 0.5, lids: 0.3, brows: [0.5, -0.1] } } : { dark: 0.6 }) }; }],
  ['J05', '3:54', '"Maybe it\'s the donuts." The analysis begins: a pie chart, first slice', () => { show('bbL'); BO.bbL.userData.set(BO.tex.pie1); BO.bbL.updateMatrixWorld(true);
    return { cam: [BO.bbL.localToWorld(V(-0.2, 36.2, 3.9 + 7.4)), BO.bbL.localToWorld(V(0, 36, 3.9)), 44], states: () => ({}) }; }],
  ['J06', '3:56', '"Maybe it\'s the voice." Second slice', () => { show('bbL'); BO.bbL.userData.set(BO.tex.pie2); BO.bbL.updateMatrixWorld(true);
    return { cam: [BO.bbL.localToWorld(V(-0.2, 36.2, 3.9 + 7.4)), BO.bbL.localToWorld(V(0, 36, 3.9)), 44], states: () => ({}) }; }],
  ['J07', '3:58', '"Maybe it\'s the shoulders." Third slice', () => { show('bbL'); BO.bbL.userData.set(BO.tex.pie3); BO.bbL.updateMatrixWorld(true);
    return { cam: [BO.bbL.localToWorld(V(-0.2, 36.2, 3.9 + 7.4)), BO.bbL.localToWorld(V(0, 36, 3.9)), 44], states: () => ({}) }; }],
  ['J08', '4:00', '"Maybe it\'s the donuts." The donuts again, as a fourth slice', () => { show('bbL'); BO.bbL.userData.set(BO.tex.pie4); BO.bbL.updateMatrixWorld(true);
    return { cam: [BO.bbL.localToWorld(V(-0.2, 36.2, 3.9 + 7.4)), BO.bbL.localToWorld(V(0, 36, 3.9)), 44], states: () => ({}) }; }],
  ['J09', '4:03', '"I made a spreadsheet." who_said_it_first.xlsx', () => { show('bbR'); BO.bbR.userData.set(BO.tex.sheet1); BO.bbR.updateMatrixWorld(true);
    return { cam: [BO.bbR.localToWorld(V(-0.2, 36.2, 3.9 + 7.4)), BO.bbR.localToWorld(V(0, 36, 3.9)), 44], states: () => ({}) }; }],
  ['J10', '4:05', '"It has timestamps." The timestamp columns fill in: you first, every time', () => { show('bbR'); BO.bbR.userData.set(BO.tex.sheet2); BO.bbR.updateMatrixWorld(true);
    return { cam: [BO.bbR.localToWorld(V(-0.2, 36.2, 3.9 + 7.4)), BO.bbR.localToWorld(V(0, 36, 3.9)), 44], states: () => ({}) }; }],
  ['J11', '4:07', '"It has conditional formatting." The rule appears: Credit = Ted, red', () => { show('bbR'); BO.bbR.userData.set(BO.tex.sheet3); BO.bbR.updateMatrixWorld(true);
    return { cam: [BO.bbR.localToWorld(V(-0.2, 36.2, 3.9 + 7.4)), BO.bbR.localToWorld(V(0, 36, 3.9)), 44], states: () => ({}) }; }],
  ['J12', '4:10', '"Ted is red." Push in on the spreadsheet as the column floods red; the neon above it says it', () => { show('bbR', 'tedRed'); BO.bbR.userData.set(BO.tex.sheet4); BO.bbR.updateMatrixWorld(true);
    BO.tedRed.position.copy(BO.bbR.localToWorld(V(0, 41.2, 4.3))); BO.tedRed.rotation.y = -0.45; BO.tedRed.scale.setScalar(0.19);
    return { cam: [BO.bbR.localToWorld(V(-0.2, 38.0, 3.9 + 12.5)), BO.bbR.localToWorld(V(0, 38.0, 3.9)), 46], states: () => ({}) }; }],
  ['J13', '4:14', '"Great idea, Ted." One last look: the grid, quiet, in the dark', () => {
    return { cam: [V(0, GRID_Y + 0.4, GRID_Z + 24), V(0, GRID_Y + 0.2, GRID_Z), 36], states: (i) => (i === 0 ? { expr: { smile: 0.15, lids: 0.3, brows: 0.2, look: [0, 0] } } : { dark: 0.55 }) }; }],
  ['J14', '4:16', '"I know." The last frame: you, the only lit room, a small smile', () => { show('pKnow'); const yp = youFwd(); at(BO.pKnow, yp.clone().add(V(0.3, 1.55, 1.4)), 0, 1.9);
    return { cam: [yp.clone().add(V(0.3, 0.4, 7.0)), yp.clone().add(V(0.3, 0.45, 0)), 40], states: (i) => (i === 0 ? { talk: 1, talkCol: 0x5ee08f, expr: { smile: 0.5, lids: 0.2, brows: 0.3 } } : { dark: 0.9 }) }; }],
];
window.FRAMES = FRAMES.map(([id, t, what]) => ({ id, t, what }));
let cap2d = null;
function renderFrame(k) {
  if (!BO) buildBoards();
  BO.all.forEach((o) => { o.visible = false; });
  rooms.forEach((r, i) => { r.root.visible = true; r.root.position.copy(slotPos(i, 4, 3)); r.root.scale.setScalar(1); r.root.rotation.set(0, 0, 0); });
  if (BO.digitRain) { BO.digitRain.scale.set(1, 1, 1); BO.digitRain.position.set(0, 0, 0); } if (BO.tedRed) { BO.tedRed.rotation.y = 0; BO.tedRed.scale.setScalar(1); } ['wInno', 'wLead', 'wVis'].forEach((k) => BO[k] && (BO[k].rotation.y = 0, BO[k].scale.setScalar(1), BO[k].material.color.setScalar(0.86)));
  const f = FRAMES[k][3]();
  [...BUBBLES, ...(CUT[FRAMES[k][0]] || [])].forEach((key) => { if (BO[key]) BO[key].visible = false; });   // no chat bubbles; plus pills cut from the story
  if (WAITPILL[FRAMES[k][0]]) WAITPILL[FRAMES[k][0]]();
  if (RECAM[FRAMES[k][0]]) f.cam = RECAM[FRAMES[k][0]]();   // with the bubble gone, frame the person, not the empty space
  { const [m, sec] = FRAMES[k][1].split(':').map(Number), t = m * 60 + sec, x = Math.min(1, Math.max(0, (t - 4) / 29));   // morning -> blue hour by the chorus
    window.__city.userData.setDay(f.day ?? 1 - x * x * (3 - 2 * x)); }
  const [p, tg, fov] = f.cam; cam.position.copy(p); cam.lookAt(tg); cam.fov = fov; cam.updateProjectionMatrix();
  finish.uniforms.uGold.value = f.gold ? 0.5 : 0; bloom.strength = f.gold ? 0.6 : 0.45; bloom.threshold = 0.92;
  rooms.forEach((r, i) => r.update({ t: 3.1 + i * 0.37, ...(f.states ? f.states(i) : {}) }));
  composer.render();
  if (!cap2d) { cap2d = document.createElement('canvas'); cap2d.width = W; cap2d.height = H; }
  const g = cap2d.getContext('2d'); g.drawImage(renderer.domElement, 0, 0);
  if (f.cap && !CLEAN) B.drawCaption(g, W, H, f.cap[0], f.cap[1], { col: CAPCOL[f.cap[0]] || '#B9C3FF', y: f.capY ?? null });
  return cap2d.toDataURL('image/jpeg', 0.92);
}
// ---------------------------------------------------------------- the timeline: the approved frames, in motion
// Each frame is a keyframe on its lyric. Between keys the camera eases, rooms slide, boards pop in and out;
// during a hold the camera keeps drifting, people idle and clap on the beat, reactions rise, digits fall.
const ease = (x) => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2);
const backOut = (x) => 1 + 2.2 * Math.pow(x - 1, 3) + 1.2 * Math.pow(x - 1, 2);
const SNAP = new Map(); let KEYS = null, LAST_SETUP = -1;
function resetScene() {
  if (!BO.base) BO.base = new Map(BO.all.map((o) => [o, { p: o.position.clone(), q: o.quaternion.clone(), s: o.scale.clone() }]));
  BO.all.forEach((o) => { const b = BO.base.get(o); o.position.copy(b.p); o.quaternion.copy(b.q); o.scale.copy(b.s); o.visible = false; }); BO.raiseVar.forEach((m) => { m.visible = false; });
  rooms.forEach((r, i) => { r.root.visible = true; r.root.position.copy(slotPos(i, 4, 3)); r.root.scale.setScalar(1); r.root.rotation.set(0, 0, 0); });
  if (BO.digitRain) { BO.digitRain.scale.set(1, 1, 1); BO.digitRain.position.set(0, 0, 0); } if (BO.tedRed) { BO.tedRed.rotation.y = 0; BO.tedRed.scale.setScalar(1); }
  ['wInno', 'wLead', 'wVis'].forEach((k) => BO[k] && (BO[k].rotation.y = 0, BO[k].scale.setScalar(1), BO[k].material.color.setScalar(0.86)));
}
// long holds get extra camera keys at their lyric lines: [frame id, line start, camera(f) -> [pos, target, fov]]
const ALT = [
  ['B07', 35.76, () => [V(-11, GRID_Y - 0.4, GRID_Z + 30), V(1.0, GRID_Y + 8.6, GRID_Z - 8), 56]],
  ['B07', 38.24, () => [G(5).add(V(0.4, 0.4, 9.5)), G(5).add(V(0.2, 0.2, 0)), 42]],
  ['B07', 42.40, () => [V(10, GRID_Y - 0.2, GRID_Z + 31), V(-0.5, GRID_Y + 8.6, GRID_Z - 8), 56]],
  ['D03', 94.72, () => [V(10, GRID_Y - 0.2, GRID_Z + 31), V(-0.5, GRID_Y + 8.6, GRID_Z - 8), 56]],
  ['D03', 97.28, () => [G(5).add(V(0.4, 0.4, 9.5)), G(5).add(V(0.2, 0.2, 0)), 42]],
  ['D03', 101.28, () => [V(0, GRID_Y + 5.0, GRID_Z + 31), V(0, GRID_Y + 7.0, GRID_Z - 6), 60]],
  ['H01', 188.40, () => [V(-11, GRID_Y - 0.4, GRID_Z + 30), V(1.0, GRID_Y + 8.6, GRID_Z - 8), 56]],
  ['H01', 190.88, () => [G(5).add(V(0.4, 0.4, 9.5)), G(5).add(V(0.2, 0.2, 0)), 42]],
  ['H01', 195.12, () => [V(2.0, GRID_Y - 0.2, GRID_Z + 32), V(0, GRID_Y + 8.6, GRID_Z - 8), 56]],
];
function setupKey(k, alt = null) {   // run frame k's setup (with an optional camera variation); returns its snapshot (cached)
  resetScene(); const f = FRAMES[k][3]();
  [...BUBBLES, ...(CUT[FRAMES[k][0]] || [])].forEach((key) => { if (BO[key]) BO[key].visible = false; });   // no chat bubbles, in motion too
  if (WAITPILL[FRAMES[k][0]]) WAITPILL[FRAMES[k][0]]();
  if (alt) f.cam = alt(); else if (RECAM[FRAMES[k][0]]) f.cam = RECAM[FRAMES[k][0]]();
  LAST_SETUP = k;
  const key = alt ? k + ':' + ALT.findIndex((a) => a[2] === alt) : k;
  if (!SNAP.has(key)) { const vis = BO.all.filter((o) => o.visible);
    SNAP.set(key, { f, cam: [f.cam[0].clone(), f.cam[1].clone(), f.cam[2]], gold: f.gold ? 1 : 0, sky: skyInShot(f),
      rooms: rooms.map((r) => ({ p: r.root.position.clone(), s: r.root.scale.x, rz: r.root.rotation.z })),
      vis: new Set(vis), tr: new Map(vis.map((o) => [o, { p: o.position.clone(), q: o.quaternion.clone(), s: o.scale.clone() }])) }); }
  return SNAP.get(key);
}
function buildKeys() {   // pin each frame to the start of its lyric line
  const L = window.__timed || []; const sec = (t) => { const [m, x] = t.split(':').map(Number); return m * 60 + x; };
  KEYS = FRAMES.map((fr, k) => { const S = sec(fr[1]); let best = null;
    for (const l of L) { const d = Math.abs(l.s - S); if (Math.floor(l.s) >= S - 1 && Math.floor(l.s) <= S + 1 && (!best || d < Math.abs(best.s - S))) best = l; }
    return { k, t: k === 0 ? 0 : best ? best.s : S }; });
  for (const a of ALT) { const k = FRAMES.findIndex((fr) => fr[0] === a[0]); if (k >= 0) KEYS.push({ k, t: a[1], alt: a[2] }); }
  KEYS.sort((a, b) => a.t - b.t || a.k - b.k);
  for (let i = 1; i < KEYS.length; i++) if (KEYS[i].t <= KEYS[i - 1].t) KEYS[i].t = KEYS[i - 1].t + 0.35;   // two frames on one line: the second follows
}
const TRANS = 0.7;
const FLAT = new Set(['B08', 'B09', 'B10', 'C10', 'D04', 'D05', 'F02', 'F03', 'F04', 'F05', 'F06', 'F08', 'G04', 'G09', 'G10', 'H02', 'H03', 'H05', 'J05', 'J06', 'J07', 'J08', 'J09', 'J10', 'J11', 'J12']);   // boards and documents: push straight in, no orbit, so they stay centred
// the big neon words in the sky stay fully on screen: if the camera would cut one, open the lens just enough (continuous, so no pops)
const SKYWORDS = ['chorusTitle', 'fileNeon', 'wInno', 'wLead', 'wVis', 'wMy'];
const _kb = new THREE.Box3(), _kv = new THREE.Vector3();
function inkCorners(o) {   // the four corners of a sky word's letters (not its padded panel), in world space
  o.updateMatrixWorld(true); const g = o.geometry; if (!g.boundingBox) g.computeBoundingBox(); const b = g.boundingBox, ink = o.userData.ink || { w: 1, h: 1 };
  const cx = (b.min.x + b.max.x) / 2, cy = (b.min.y + b.max.y) / 2, hw = (b.max.x - b.min.x) / 2 * ink.w, hh = (b.max.y - b.min.y) / 2 * ink.h;
  return [[-1, -1], [1, -1], [-1, 1], [1, 1]].map(([sx, sy]) => new THREE.Vector3(cx + sx * hw, cy + sy * hh, 0).applyMatrix4(o.matrixWorld));
}
function skyInShot(f) {   // does this key's own camera frame a sky word? (its middle on screen = the word is meant to be in the shot)
  const objs = SKYWORDS.map((k) => BO[k]).filter((o) => o && o.visible); if (!objs.length) return 0;
  const c0 = cam.position.clone(), q0 = cam.quaternion.clone(), f0 = cam.fov;
  cam.position.copy(f.cam[0]); cam.lookAt(f.cam[1]); cam.fov = f.cam[2]; cam.updateProjectionMatrix(); cam.updateMatrixWorld(true);
  let hit = 0; for (const o of objs) { o.updateMatrixWorld(true); _kv.setFromMatrixPosition(o.matrixWorld); _kv.project(cam); if (_kv.z < 1 && Math.abs(_kv.x) < 1 && Math.abs(_kv.y) < 1) hit = 1; }
  cam.position.copy(c0); cam.quaternion.copy(q0); cam.fov = f0; cam.updateProjectionMatrix(); return hit;
}
function keepInFrame(objs, w, margin = 0.86, maxFov = 72) {
  window.__skyW = w; if (!objs.length || w <= 0) return; cam.updateMatrixWorld(true); let ext = 0;
  for (const o of objs) for (const v of inkCorners(o)) {
    if (v.clone().applyMatrix4(cam.matrixWorldInverse).z >= -0.1) continue; v.project(cam); ext = Math.max(ext, Math.abs(v.x), Math.abs(v.y)); }
  if (ext <= margin) return;
  const need = Math.min(maxFov, THREE.MathUtils.radToDeg(2 * Math.atan(Math.tan(THREE.MathUtils.degToRad(cam.fov / 2)) * ext / margin)));
  cam.fov += (need - cam.fov) * w; cam.updateProjectionMatrix();
}
window.__fov = () => cam.fov;
window.__corners = (k) => { cam.updateMatrixWorld(true); return inkCorners(BO[k]).map((v) => v.project(cam).toArray().map((x) => +x.toFixed(2))); _kb.setFromObject(BO[k]); const r = []; for (let c = 0; c < 8; c++) { _kv.set(c & 1 ? _kb.max.x : _kb.min.x, c & 2 ? _kb.max.y : _kb.min.y, c & 4 ? _kb.max.z : _kb.min.z); _kv.project(cam); r.push([+_kv.x.toFixed(2), +_kv.y.toFixed(2), +_kv.z.toFixed(3)]); } return { r, vis: BO[k].visible, sc: BO[k].scale.x, box: [_kb.min.toArray().map((v) => +v.toFixed(1)), _kb.max.toArray().map((v) => +v.toFixed(1))] }; };
window.__skyCut = () => { if ((window.__skyW || 0) < 0.99) return []; cam.updateMatrixWorld(true); const cut = [];   // only checked while the shot means to show the word (not mid-pan away)
  SKYWORDS.filter((k) => BO[k] && BO[k].visible && BO[k].scale.x > 0.5 * (BO.base.get(BO[k])?.s.x || 1)).forEach((k) => { let inn = 0, out = 0;
    for (const v of inkCorners(BO[k])) { v.project(cam); if (Math.abs(v.x) <= 0.97 && Math.abs(v.y) <= 0.97) inn++; else out++; }
    if (inn && out) cut.push(k); }); return cut; };
window.renderTime = (t) => {
  if (!BO) buildBoards(); if (!KEYS) buildKeys();
  let i = 0; while (i + 1 < KEYS.length && KEYS[i + 1].t <= t) i++;
  const kb = KEYS[i], ka = KEYS[Math.max(0, i - 1)], next = KEYS[i + 1];
  const A = setupKey(ka.k, ka.alt), Bs = setupKey(kb.k, kb.alt);   // B's setup runs last: its textures and visibility stand
  const same = ka.k === kb.k, tr = same ? 1.4 : TRANS;   // a camera move inside one shot glides more slowly
  const cutIn = same && A.sky !== Bs.sky;   // into or out of a close-up that loses the sky words: a clean cut on the line, not a pan that drags them off the edge
  const u = i === 0 || cutIn ? 1 : Math.min(1, (t - kb.t) / tr), e = ease(u);
  // rooms slide from A to B
  rooms.forEach((r, j) => { const a = A.rooms[j], b = Bs.rooms[j]; r.root.position.lerpVectors(a.p, b.p, e); r.root.scale.setScalar(a.s + (b.s - a.s) * e); r.root.rotation.set(0, 0, a.rz + (b.rz - a.rz) * e); });
  // boards: shared ones glide, new ones pop in, old ones shrink away
  const all = new Set([...A.vis, ...Bs.vis]);
  all.forEach((o) => { const ta = A.tr.get(o), tb = Bs.tr.get(o);
    if (ta && tb) { o.visible = true; o.position.lerpVectors(ta.p, tb.p, e); o.quaternion.slerpQuaternions(ta.q, tb.q, e); o.scale.lerpVectors(ta.s, tb.s, e); }
    else if (tb) { o.visible = true; const k2 = Math.max(0.001, backOut(Math.min(1, Math.max(0, (u - 0.2) / 0.8) * 1.15)));   /* pops in once the old one has mostly gone */ o.position.copy(tb.p); o.quaternion.copy(tb.q); o.scale.copy(tb.s).multiplyScalar(k2); }
    else if (ta && u < 1) { o.visible = true; const k2 = Math.max(0.001, 1 - ease(Math.min(1, u / 0.45)));   /* leaves quickly, so two boards never sit on each other */ o.position.copy(ta.p); o.quaternion.copy(ta.q); o.scale.copy(ta.s).multiplyScalar(k2); }
    else o.visible = false; });
  // camera: ease A -> B, then drift (a slow push-in) for the rest of the hold
  const hold = next ? Math.max(0.01, next.t - kb.t - tr) : 4, h = Math.max(0, Math.min(1, (t - kb.t - tr) / hold)), hs = h * (2 - h);
  const p = A.cam[0].clone().lerp(Bs.cam[0], e), tg = A.cam[1].clone().lerp(Bs.cam[1], e), fov = A.cam[2] + (Bs.cam[2] - A.cam[2]) * e;
  p.lerp(tg, Math.min(0.18, 0.03 * hold) * hs);
  if (hold > 3 && !FLAT.has(FRAMES[kb.k][0])) { const ang = 0.035 * hold * (hs - 0.5); p.sub(tg).applyAxisAngle(new THREE.Vector3(0, 1, 0), ang).add(tg); }   // a slow orbit across long holds
  if (i === 0) { const c = 1 - ease(Math.min(1, t / 7.5)); p.add(V(0, 7 * c, 4 * c)); tg.add(V(0, 9 * c, 0)); }   // the opening: down out of the morning sky
  cam.position.copy(p); cam.lookAt(tg); cam.fov = fov; cam.updateProjectionMatrix();
  keepInFrame(SKYWORDS.map((k) => BO[k]).filter((o) => o && o.visible), A.sky + (Bs.sky - A.sky) * e);   // big sky words never run off the screen
  const gold = A.gold + (Bs.gold - A.gold) * e; finish.uniforms.uGold.value = 0.5 * gold; bloom.strength = 0.45 + 0.15 * gold; bloom.threshold = 0.92;
  { const x = Math.min(1, Math.max(0, (t - 4) / 29)); window.__city.userData.setDay(1 - x * x * (3 - 2 * x)); }   // morning -> blue hour by the first chorus
  // things that keep moving during a hold
  if (BO.party.visible) BO.party.children.forEach((c, n) => { c.userData.b = c.userData.b || c.position.clone(); const span = 9, ph = (n * 0.6180339) % 1;
    c.position.y = c.userData.b.y - 4 + ((t * (c.geometry.parameters.width < 0.2 ? 1.6 : 1.1) + ph * span) % span); if (c.geometry.parameters.width < 0.2) c.rotation.x = t * 3 + n; });
  if (BO.digitRain.visible) BO.digitRain.children.forEach((c, n) => { c.userData.b = c.userData.b || c.position.clone(); const ph = (n * 0.6180339) % 1;
    c.position.y = c.userData.b.y + 6 - ((t * 1.3 + ph * 12) % 12); c.rotation.z = c.userData.b.z * 0 + Math.sin(t * 1.7 + n) * 0.5; });
  if (BO.raiseSpill.visible) { const isFirst = FRAMES[kb.k][0] === 'B08', grow = isFirst ? Math.min(1, Math.max(0, (t - kb.t) / Math.max(0.5, (next ? next.t : kb.t + 2) - kb.t - 0.2))) : 1;
    const vi = Math.min(BO.raiseVar.length - 1, Math.floor(grow * BO.raiseVar.length)), vm = BO.raiseVar[vi];
    vm.visible = true; vm.position.copy(BO.raiseSpill.position); vm.quaternion.copy(BO.raiseSpill.quaternion); vm.scale.copy(BO.raiseSpill.scale); BO.raiseSpill.visible = false; }
  // people: idle with real time; B's expressions; dark/talk fade across the cut; clapping on the beat
  const sa = A.f.states, sb = Bs.f.states;
  rooms.forEach((r, j) => { const a = sa ? sa(j) : {}, b = sb ? sb(j) : {}; const st = { ...b, t: t + j * 0.37 };
    st.dark = (a.dark || 0) + ((b.dark || 0) - (a.dark || 0)) * e; st.talk = (a.talk || 0) + ((b.talk || 0) - (a.talk || 0)) * e; if (!b.talkCol && a.talkCol && u < 1) st.talkCol = a.talkCol;
    if (b.clap) st.clapK = 0.5 + 0.5 * Math.sin((t * 2.1 + j * 0.13) * Math.PI * 2);
    r.update(st); });
  composer.render(); return window.qaNow ? renderer.domElement.toDataURL('image/jpeg', 0.92) : null;
};
window.qaFrame = (k) => { renderFrame(k); return window.qa ? null : null; };
const _baseRender = window.renderAt;
window.renderAt = (n) => (n >= 200 ? renderFrame(Math.round(n) - 200) : _baseRender(n));

(async () => { await loadFonts(); build(); try { window.__timed = await (await fetch('/data/timed.json')).json(); } catch (e) { window.__timed = []; } window.ready = true; })().catch((e) => console.log('INIT ERROR', e.stack || e));
