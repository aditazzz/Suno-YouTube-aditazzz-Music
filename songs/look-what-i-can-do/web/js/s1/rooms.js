// S1: the Great Idea, Ted meeting rooms, ported. Each room is an open-fronted box with painted (pre-lit) walls, a desk,
// a laptop and a mannequin. New here: every room but hers uses one of her music videos as its virtual background (the
// back wall plays the clip), her laptop screen carries a picture (the terminal she came from), and she can pick the
// laptop up and turn it round to show it off.
import * as THREE from 'three';
import { clay, basic, canvasTex, labelPlane, micOff, micOn, FONT, rng, lerp, clamp, easeIO, sstep, dotTex } from './lib.js';
import { Mannequin, Dog, Doodle, Cat } from './mannequin.js';
import * as MED from './media.js';

export const RW = 3.0, RH = 2.2, RD = 2.3;          // room width, height, depth
export const SCR_W = 0.42;                          // laptop display width (16:9)
// a back-wall plane whose UVs crop a 16:9 clip to cover the wall (shared textures can't carry their own crop)
export function coverGeo(w, h, aspect = 16 / 9) {
  const g = new THREE.PlaneGeometry(w, h); const k = (w / h) / aspect; const uv = g.attributes.uv;
  for (let i = 0; i < uv.count; i++) { if (k < 1) uv.setX(i, 0.5 + (uv.getX(i) - 0.5) * k); else uv.setY(i, 0.5 + (uv.getY(i) - 0.5) / k); }
  return g;
}
export const CAST = [   // the I Have a Blocker people (same looks and rooms), with faces and their own skin tones
  { name: 'You', wall: '#bfe8d8', key: 'lilac', m: { skin: 0xf0c9ad, browColor: 0x8a4a5e, blush: true, shirt: 0xf27aa8, noHood: true, hair: 'updo', hairColor: 0xff9cc8, sunglasses: true }, prop: 'mug', pet: 'doodle' },
  { name: 'Dana', wall: '#9aa6b8', key: 'clock', m: { skin: 0xb98260, browColor: 0x3a2a1e, shirt: 0xb9c6da, hair: 'bun', hairColor: 0x5a4636 } },
  { name: 'Tom', wall: '#d8cdb8', key: 'books', m: { skin: 0xe9c2a6, browColor: 0x6a5240, shirt: 0x7a2e3b, glasses: true }, prop: 'books', pet: 'cat' },
  { name: 'Mike (host)', wall: '#d8d2c4', key: 'kanban', m: { skin: 0xc4906a, browColor: 0x2a1d16, shirt: 0xb8423a, headset: true } },
  { name: 'Kyle', wall: '#2a2540', key: 'led', led: '#a46bff', m: { skin: 0xf2d0b8, browColor: 0x7a5233, shirt: 0x8fb39a, hat: 'cap', hatColor: 0x1f1f24 } },
  { name: 'Ted', wall: '#e3d6bf', key: 'books', m: { skin: 0xefc7a8, browColor: 0x5a3a22, shirt: 0xa9c9ef, glasses: true }, prop: 'books' },
  { name: 'Lena', wall: '#7cc6f2', key: 'beach', m: { skin: 0xf4d6c2, browColor: 0xb89a60, shirt: 0xf3efe6, hair: 'long', hairColor: 0xe3c27a } },
  { name: 'Sam (new)', wall: '#f1f3f4', key: 'clean', m: { skin: 0x8a5a3c, browColor: 0x1d1612, shirt: 0x4a7fd1, lanyard: true } },
  { name: 'Priya · Product', wall: '#dfe6ec', key: 'whiteboard', m: { skin: 0xa86e4c, browColor: 0x1b1514, shirt: 0x3a3d46, hair: 'long', hairColor: 0x1b1514 } },
  { name: 'Greg R.', off: true },
  { name: 'Jess', wall: '#2a2d33', key: 'car', m: { skin: 0xa8714f, browColor: 0x1d1612, shirt: 0xd9a441, hair: 'long', hairColor: 0x1d1612, headphones: true } },
  { name: "Somebody's Dog", wall: '#d9c2a2', key: 'living', dog: true },
];
export const LETTERS = '';
export let HAND_LIFT = 0.093;   // hand centre above the keyboard (room units); the QA check tunes nothing, it only reports
export let KZ_OFF = -0.11;   // hands this far from the laptop centre, toward the person
export function setHandLift(v, kz) { HAND_LIFT = v; if (kz !== undefined) KZ_OFF = kz; }

function shade(hex, k) { const c = new THREE.Color(hex); c.multiplyScalar(k); return '#' + c.getHexString(); }

// the back wall, painted with its own light and props (cheap, and lets every room look different)
function backWallTex(c, seed) {
  const R = rng(seed);
  return canvasTex(768, 560, (g, w, h) => {
    const gr = g.createLinearGradient(0, 0, 0, h); gr.addColorStop(0, shade(c.wall, 0.30)); gr.addColorStop(0.55, shade(c.wall, 0.55)); gr.addColorStop(1, shade(c.wall, 0.36));
    g.fillStyle = gr; g.fillRect(0, 0, w, h);
    const lamp = g.createRadialGradient(w * 0.78, h * 0.32, 10, w * 0.78, h * 0.32, w * 0.55);   // a lamp's warm pool
    lamp.addColorStop(0, 'rgba(255,200,140,0.55)'); lamp.addColorStop(1, 'rgba(255,214,160,0)'); g.fillStyle = lamp; g.fillRect(0, 0, w, h);
    const k = c.key;
    if (k === 'books') { for (let s = 0; s < 3; s++) { const y = 80 + s * 120; g.fillStyle = '#5a3c26'; g.fillRect(40, y + 92, 300, 12);
        let x = 46; while (x < 330) { const bw = 12 + R() * 14, bh = 60 + R() * 30; g.fillStyle = `hsl(${R() * 360},45%,${35 + R() * 25}%)`; g.fillRect(x, y + 92 - bh, bw, bh); x += bw + 2; } } }
    if (k === 'led') { g.fillStyle = c.led; g.globalAlpha = 0.9; g.fillRect(0, 34, w, 10); g.globalAlpha = 0.35; g.fillRect(0, 20, w, 40); g.globalAlpha = 1;
      g.fillStyle = '#ff5d8f'; g.fillRect(470, 120, 170, 230); g.fillStyle = '#1b1b2a'; g.fillRect(480, 130, 150, 210); g.fillStyle = c.led; g.font = `bold 40px ${FONT.dispBlack}`; g.fillText('GG', 515, 250); }
    if (k === 'whiteboard') { g.fillStyle = '#f8f8f6'; g.fillRect(70, 80, 440, 280); g.strokeStyle = '#9aa'; g.lineWidth = 6; g.strokeRect(70, 80, 440, 280);
      for (let i = 0; i < 9; i++) { g.fillStyle = ['#ffd84d', '#ff9fb2', '#9fe0ff', '#b6f2a4'][i % 4]; g.fillRect(100 + (i % 3) * 130, 105 + Math.floor(i / 3) * 82, 96, 66); }
      g.fillStyle = '#c33'; g.font = `bold 34px ${FONT.ui}`; g.fillText('ETA?', 400, 340); }
    if (k === 'kanban') { const cols = ['TO DO', 'DOING', 'DONE']; for (let i = 0; i < 3; i++) { g.fillStyle = '#4a4438'; g.font = `bold 26px ${FONT.ui}`; g.fillText(cols[i], 70 + i * 150, 92);
      for (let j = 0; j < (i === 2 ? 1 : 4); j++) { g.fillStyle = ['#ffd84d', '#ff9fb2', '#9fe0ff'][(i + j) % 3]; g.fillRect(70 + i * 150, 110 + j * 70, 110, 56); } } }
    if (k === 'clock') { g.fillStyle = '#d6d2c8'; g.beginPath(); g.arc(625, 180, 90, 0, 7); g.fill(); g.strokeStyle = '#333'; g.lineWidth = 8; g.stroke();
      g.lineWidth = 7; g.beginPath(); g.moveTo(625, 180); g.lineTo(625, 110); g.moveTo(625, 180); g.lineTo(665, 210); g.stroke();
      g.fillStyle = '#c33'; g.font = `bold 30px ${FONT.ui}`; g.textAlign = 'center'; g.fillText('HARD STOP 9:30', 625, 320); g.textAlign = 'left'; }
    if (k === 'car') { const sky = g.createLinearGradient(0, 0, 0, h * 0.6); sky.addColorStop(0, '#5f86b8'); sky.addColorStop(1, '#c9d6e4'); g.fillStyle = sky; g.beginPath(); g.roundRect(60, 60, w - 120, h * 0.5, 40); g.fill();
      g.fillStyle = '#34383f'; for (let i = 0; i < 9; i++) g.fillRect(70 + i * 72, 200 + R() * 40, 50, 120); g.fillStyle = '#111317'; g.fillRect(0, h * 0.62, w, h); }
    if (k === 'gym') { g.fillStyle = '#2b2e33'; for (let i = 0; i < 6; i++) { g.fillRect(90 + i * 90, 300, 20, 60); g.fillRect(70 + i * 90, 310, 60, 40); }
      g.fillStyle = '#2bb3a6'; g.font = `bold 46px ${FONT.dispBlack}`; g.fillText('NO DAYS OFF', 120, 150); }
    if (k === 'beach') { const sky = g.createLinearGradient(0, 0, 0, h); sky.addColorStop(0, '#5fb8ec'); sky.addColorStop(0.55, '#bfe6f6'); sky.addColorStop(0.56, '#2f8fc2'); sky.addColorStop(0.75, '#e9d6a8'); sky.addColorStop(1, '#d9c08a');
      g.fillStyle = sky; g.fillRect(0, 0, w, h); g.fillStyle = '#fff6c8'; g.beginPath(); g.arc(610, 110, 46, 0, 7); g.fill();
      g.strokeStyle = '#3d5a2a'; g.lineWidth = 12; g.beginPath(); g.moveTo(120, h); g.quadraticCurveTo(140, 300, 190, 200); g.stroke(); }
    if (k === 'kitchen') { g.fillStyle = '#e9ecef'; g.fillRect(0, 250, w, 30); for (let i = 0; i < 5; i++) { g.fillStyle = '#c8d4cc'; g.fillRect(40 + i * 145, 60, 120, 150); g.strokeStyle = '#8a9a90'; g.lineWidth = 4; g.strokeRect(40 + i * 145, 60, 120, 150); } }
    if (k === 'cozy') { for (let i = 0; i < 16; i++) { const x = 30 + i * 46, y = 60 + 24 * Math.sin(i * 0.8); g.fillStyle = 'rgba(255,200,120,0.9)'; g.beginPath(); g.arc(x, y, 7, 0, 7); g.fill();
        const gl = g.createRadialGradient(x, y, 0, x, y, 30); gl.addColorStop(0, 'rgba(255,190,110,0.35)'); gl.addColorStop(1, 'rgba(255,190,110,0)'); g.fillStyle = gl; g.fillRect(x - 30, y - 30, 60, 60); } }
    if (k === 'living' || k === 'lilac') { g.fillStyle = k === 'living' ? '#8a5a3a' : '#e8a6cf'; g.fillRect(470, 110, 180, 200); g.fillStyle = k === 'living' ? '#f0d9a8' : '#fbe3f1'; g.fillRect(482, 122, 156, 176);
      const art = g.createRadialGradient(560, 210, 5, 560, 210, 80); art.addColorStop(0, '#ff8fc2'); art.addColorStop(1, '#6a4cc0'); g.fillStyle = art; g.beginPath(); g.arc(560, 210, 60, 0, 7); g.fill(); }
    if (k === 'clean') { g.fillStyle = 'rgba(255,255,255,0.7)'; g.fillRect(470, 70, 220, 280); g.strokeStyle = '#cfd4d8'; g.lineWidth = 6; g.strokeRect(470, 70, 220, 280); }
    // floor shadow at the base of the wall
    const fl = g.createLinearGradient(0, h * 0.82, 0, h); fl.addColorStop(0, 'rgba(0,0,0,0)'); fl.addColorStop(1, 'rgba(0,0,0,0.35)'); g.fillStyle = fl; g.fillRect(0, h * 0.82, w, h * 0.18);
  });
}
function sideTex(c) { return canvasTex(64, 64, (g, w, h) => { const gr = g.createLinearGradient(0, 0, w, 0); gr.addColorStop(0, shade(c.wall, 0.18)); gr.addColorStop(1, shade(c.wall, 0.42)); g.fillStyle = gr; g.fillRect(0, 0, w, h); }); }
function floorTex(c) { return canvasTex(256, 256, (g, w, h) => { const base = c.key === 'car' ? '#1a1b1f' : (['books', 'living', 'kanban'].includes(c.key) ? '#6b4a32' : '#8a8f96');
  const gr = g.createLinearGradient(0, 0, 0, h); gr.addColorStop(0, shade(base, 0.25)); gr.addColorStop(1, shade(base, 0.55)); g.fillStyle = gr; g.fillRect(0, 0, w, h);
  g.strokeStyle = 'rgba(0,0,0,0.18)'; g.lineWidth = 2; for (let x = 0; x < w; x += 32) { g.beginPath(); g.moveTo(x, 0); g.lineTo(x, h); g.stroke(); } }); }

function screenTex(kind) {
  return canvasTex(320, 200, (g, w, h) => {
    g.fillStyle = '#0c0f14'; g.fillRect(0, 0, w, h);
    if (kind === 'ticket') { g.fillStyle = '#2a6fdb'; g.fillRect(16, 16, w - 32, 34); g.fillStyle = '#fff'; g.font = `bold 22px ${FONT.mono}`; g.fillText('ENG-4021', 26, 41);
      for (let i = 0; i < 4; i++) { g.fillStyle = '#2a2f38'; g.fillRect(16, 64 + i * 30, w - 32 - i * 40, 18); } }
    else { const gr = g.createLinearGradient(0, 0, w, h); gr.addColorStop(0, '#1d2a3e'); gr.addColorStop(1, '#0c1018'); g.fillStyle = gr; g.fillRect(0, 0, w, h);
      for (let i = 0; i < 4; i++) for (let j = 0; j < 3; j++) { g.fillStyle = 'rgba(160,190,230,0.25)'; g.fillRect(14 + i * 76, 16 + j * 60, 66, 50); } }
  });
}

export class Room {
  constructor(idx, opts = {}) {
    // a feed: a participant whose camera is one of her clips (the Claude robot, the GT3 RS): the clip fills the square
    const c = this.c = opts.feed ? { name: opts.feed.name, off: true, feed: opts.feed.key } : CAST[idx]; this.idx = idx; this.opts = opts; const g = this.root = new THREE.Group();
    this.content = new THREE.Group(); g.add(this.content);
    if (c.feed) {
      this.panel = new THREE.Mesh(coverGeo(RW, RH), new THREE.MeshBasicMaterial({ map: c.feed === 'none' ? null : MED.texOf(c.feed), color: 0xd8d8d8 })); this.panel.userData.base = 0.85;
      this.panel.position.z = 0.0; this.content.add(this.panel); this.video = c.feed; this.solids = [];
    } else if (c.off) {                                   // Greg: camera off. a dark panel, his initials, a muted mic
      const tex = canvasTex(600, 440, (gg, w, h) => { gg.fillStyle = '#14151a'; gg.fillRect(0, 0, w, h);
        gg.fillStyle = '#2b2d36'; gg.beginPath(); gg.arc(w / 2, h / 2 - 20, 86, 0, 7); gg.fill();
        gg.fillStyle = '#e8e8ec'; gg.font = `600 80px ${FONT.ui}`; gg.textAlign = 'center'; gg.textBaseline = 'middle'; gg.fillText('GR', w / 2, h / 2 - 16);
        gg.font = `500 40px ${FONT.ui}`; gg.fillText('Greg R.', w / 2, h / 2 + 110); micOff(gg, w - 60, 56, 50); });
      this.panel = new THREE.Mesh(new THREE.PlaneGeometry(RW, RH), basic(0xffffff, { map: tex })); this.panel.position.z = 0.0; this.content.add(this.panel);
      this.statusDot = new THREE.Mesh(new THREE.CircleGeometry(0.07, 20), basic(0x46e678)); this.statusDot.position.set(-RW / 2 + 0.25, RH / 2 - 0.25, 0.01); this.content.add(this.statusDot);
    } else {
      let back;
      if (opts.video) {   // her video as the virtual background: the clip, cropped to cover the wall, a touch under full brightness
        back = new THREE.Mesh(coverGeo(RW, RH), new THREE.MeshBasicMaterial({ map: MED.texOf(opts.video), color: 0xd0d0d0 })); this.video = opts.video;
      } else back = new THREE.Mesh(new THREE.PlaneGeometry(RW, RH), basic(0xffffff, { map: backWallTex(c, idx * 7 + 3) }));
      back.position.z = -RD; this.content.add(back); this.back = back;
      for (const s of [-1, 1]) { const side = new THREE.Mesh(new THREE.PlaneGeometry(RD, RH), basic(0xffffff, { map: sideTex(c) })); side.position.set(s * RW / 2, 0, -RD / 2); side.rotation.y = -s * Math.PI / 2; this.content.add(side); }
      const floor = new THREE.Mesh(new THREE.PlaneGeometry(RW, RD), basic(0xffffff, { map: floorTex(c) })); floor.rotation.x = -Math.PI / 2; floor.position.set(0, -RH / 2, -RD / 2); this.content.add(floor);
      const ceil = new THREE.Mesh(new THREE.PlaneGeometry(RW, RD), basic(new THREE.Color(c.wall).multiplyScalar(0.35))); ceil.rotation.x = Math.PI / 2; ceil.position.set(0, RH / 2, -RD / 2); this.content.add(ceil);
      // desk + laptop
      const deskM = clay(c.key === 'car' ? 0x22252b : 0x6b5440);
      this.solids = [];   // what a body must never pass through (the QA check measures against these)
      { const fl = new THREE.Mesh(new THREE.BoxGeometry(RW, 0.2, RD), new THREE.MeshBasicMaterial({ visible: false })); fl.position.set(0, -RH / 2 - 0.1, -RD / 2); this.content.add(fl); this.solids.push(['floor', fl]); }
      if (c.key !== 'car') { const desk = new THREE.Mesh(new THREE.BoxGeometry(1.7, 0.06, 0.7), deskM); desk.position.set(0, -0.25, -0.55); this.content.add(desk); this.solids.push(['desk', desk]);
        for (const s of [-1, 1]) { const leg = new THREE.Mesh(new THREE.BoxGeometry(0.05, 0.82, 0.05), deskM); leg.position.set(0.78 * s, -0.69, -0.55); this.content.add(leg); this.solids.push(['desk leg', leg]); } }
      this.laptop = new THREE.Group(); this.laptop.position.set(0, c.key === 'car' ? -0.2 : -0.22, -0.42); this.laptop.rotation.y = Math.PI; this.content.add(this.laptop);
      const lb = new THREE.Mesh(new THREE.BoxGeometry(0.46, 0.02, 0.32), clay(0xb8bcc4)); this.laptop.add(lb); this.solids.push(['laptop', lb]);
      const ls = new THREE.Mesh(new THREE.BoxGeometry(0.46, 0.3, 0.012), clay(0x9a9ea6)); ls.position.set(0, 0.15, -0.16); ls.rotation.x = -0.25; this.laptop.add(ls); this.solids.push(['laptop lid', ls]);
      this.lid = ls;
      // the display, on the person's side of the lid: 16:9, black bezel round it
      const bez = new THREE.Mesh(new THREE.PlaneGeometry(0.44, 0.28), basic(0x060608)); bez.position.z = 0.0062; ls.add(bez);
      this.screen = new THREE.Mesh(new THREE.PlaneGeometry(SCR_W, SCR_W * 9 / 16), new THREE.MeshBasicMaterial({ color: 0x1a2436 })); this.screen.position.set(0, 0.006, 0.0066); ls.add(this.screen);
      // the laptop screen faces the person (away from us); its glow lights their face (a soft additive card)
      // the person
      const pz = -1.14;   // far enough back that the belly clears the desk edge (QA)
      if (c.dog) {
        this.dog = new Dog(); this.dog.root.scale.setScalar(1.35); this.dog.root.position.set(0, -RH / 2 - 0.05, pz); this.dog.root.rotation.y = 0; this.content.add(this.dog.root);
      } else {
        this.man = new Mannequin(c.m); this.man.root.position.set(0, -RH / 2 + 0.024, pz); this.man.root.scale.setScalar(1.38); this.content.add(this.man.root);   // feet flat on the floor (QA)
      }
      // chair back behind the person
      const chairM = clay(c.key === 'car' ? 0x2a2c31 : 0x2c2f36);
      // an office chair: back, seat, gas lift and a five-star base on casters (the seat sits under the hips)
      const seatY = -0.53, chair = new THREE.Group(); chair.position.set(0, 0, pz); this.content.add(chair);
      const cback = new THREE.Mesh(new THREE.BoxGeometry(0.58, 0.62, 0.07, 4, 4, 1), chairM); cback.position.set(0, seatY + 0.36, -0.29); cback.rotation.x = -0.08; chair.add(cback); this.solids.push(['chair', cback]);
      const seat = new THREE.Mesh(new THREE.BoxGeometry(0.56, 0.07, 0.5), chairM); seat.position.set(0, seatY, -0.02); chair.add(seat); this.solids.push(['chair', seat]);
      const metal = clay(0x8c9096);
      const lift = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.03, (seatY - 0.035) - (-RH / 2 + 0.1), 12), metal); lift.position.set(0, (seatY - 0.035 + (-RH / 2 + 0.1)) / 2, -0.02); chair.add(lift); this.solids.push(['chair base', lift]);
      for (let k = 0; k < 5; k++) { const a = k / 5 * Math.PI * 2 + 0.3; const arm = new THREE.Mesh(new THREE.BoxGeometry(0.04, 0.03, 0.3), chairM);
        arm.position.set(Math.sin(a) * 0.15, -RH / 2 + 0.07, -0.02 + Math.cos(a) * 0.15); arm.rotation.y = a; chair.add(arm); this.solids.push(['chair base', arm]);
        const wheel = new THREE.Mesh(new THREE.SphereGeometry(0.028, 12, 8), clay(0x1c1d21)); wheel.position.set(Math.sin(a) * 0.29, -RH / 2 + 0.028, -0.02 + Math.cos(a) * 0.29); chair.add(wheel); }
      if (c.pet === 'doodle') {   // your goldendoodle, sitting on the floor beside your desk
        this.pet = new Doodle(); this.pet.root.scale.setScalar(1.25); this.pet.root.position.set(-1.08, -RH / 2, -0.55); this.pet.root.rotation.y = 0.5; this.content.add(this.pet.root); }
      if (c.pet === 'cat') {      // a cat loafing on the desk, next to the laptop
        this.pet = new Cat(); this.pet.root.scale.setScalar(1.5); this.pet.root.position.set(-0.55, -0.22, -0.6); this.pet.root.rotation.y = 0.35; this.content.add(this.pet.root);
        const cb = new THREE.Mesh(new THREE.BoxGeometry(0.42, 0.3, 0.6), new THREE.MeshBasicMaterial({ visible: false })); cb.position.set(-0.55, -0.07, -0.6); cb.rotation.y = 0.35; this.content.add(cb); this.solids.push(['cat', cb]); }
      if (c.prop === 'mug') { const mug = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.06, 0.12, 18), clay(0xffffff)); mug.position.set(0.55, -0.16, -0.5); this.content.add(mug); this.solids.push(['mug', mug]); }
      // a lamp
      if (!['car', 'beach'].includes(c.key)) {   // a real lamp (shade on a pole), kept away from anything on the wall so the two don't flare together
        const side = ['clock', 'lilac'].includes(c.key) ? -1 : 1, lx = side * (RW / 2 - 0.4), lamp = new THREE.Group(); lamp.position.set(lx, 0.1, -RD + 0.35); this.content.add(lamp);
        const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.012, 0.012, 0.5, 8), clay(0x2c2f36)); pole.position.y = 0.0; lamp.add(pole);
        const shade = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.13, 0.15, 20, 1, true), basic(0xffe2b8, { side: THREE.DoubleSide })); shade.position.y = 0.3; lamp.add(shade);
        const glow = new THREE.Sprite(new THREE.SpriteMaterial({ map: dotTex(), color: 0xffc98a, transparent: true, opacity: 0.28, depthWrite: false, blending: THREE.AdditiveBlending })); glow.scale.setScalar(0.75); glow.position.set(lx, 0.4, -RD + 0.38); this.content.add(glow); }
    }
    // the tile frame (lights green when the person talks)
    this.frameM = basic(0x4a4d55, { toneMapped: false });
    const t = 0.045;
    for (const [w, h, x, y] of [[RW + t * 2, t, 0, RH / 2 + t / 2], [RW + t * 2, t, 0, -RH / 2 - t / 2], [t, RH, -RW / 2 - t / 2, 0], [t, RH, RW / 2 + t / 2, 0]]) {
      const b = new THREE.Mesh(new THREE.BoxGeometry(w, h, t), this.frameM); b.position.set(x, y, 0.01); g.add(b);
    }
    // the shell outside the room (so a room reads as a box from the side); no front face
    const sm = clay(0x1a1b20, { rimAmt: 0.25 }), none = new THREE.MeshBasicMaterial({ visible: false });
    const outer = new THREE.Mesh(new THREE.BoxGeometry(RW + 0.1, RH + 0.1, RD + 0.02), [sm, sm, sm, sm, none, sm]); outer.position.z = -RD / 2 - 0.03; g.add(outer);
    this.outer = outer;
    // name tag
    this.tag = labelPlane(c.name, { h: 0.2, icon: c.off && !c.feed ? null : (gg, x, y, s) => micOff(gg, x, y, s) });
    this.tag.position.set(-RW / 2 + 0.08 + this.tag.userData.w / 2, -RH / 2 + 0.17, 0.03); g.add(this.tag);
    if (!c.off) { this.tagOn = labelPlane(c.name, { h: 0.2, icon: (gg, x, y, s) => micOn(gg, x, y, s) }); this.tagOn.position.copy(this.tag.position); this.tagOn.visible = false; g.add(this.tagOn); }   // unmuted while talking
    // the blackout cover (everyone else goes dark when he says it)
    this.dark = new THREE.Mesh(new THREE.PlaneGeometry(RW, RH), basic(0x050506, { transparent: true, opacity: 0 })); this.dark.position.z = 0.02; g.add(this.dark);
  }
  /** s: { t, talk 0..1, talkCol, card 0..1 (holding the letter up), fine 0..1 (thumbs up), dark 0..1, lookYaw } */
  update(s) {
    const t = s.t, c = this.c;
    const base = new THREE.Color(0x4a4d55), col = new THREE.Color(s.talkCol || 0x3ee07a);
    this.frameM.color.copy(base.lerp(col, s.talk || 0));
    if (this.tagOn) { const on = (s.talk || 0) > 0.3; this.tagOn.visible = on; this.tag.visible = !on; }
    this.dark.material.opacity = s.dark || 0; if (this.panel) this.panel.material.color.setScalar((this.panel.userData.base || 1) * (1 - (s.dark || 0))); this.dark.visible = (s.dark || 0) > 0.01;
    if (this.statusDot) this.statusDot.visible = (s.blink === undefined) ? true : (Math.floor(t * 3) % 2 === 0);
    if (this.man) {
      const ph = this.idx * 1.7, k = s.card || 0, f = s.fine || 0;
      const type = Math.sin(t * 9 + ph) * 0.015;
      // hands: typing -> card up -> thumbs up
      const lean = lerp(0.13 + 0.025 * Math.sin(t * 0.5 + ph), 0.03, sstep(0, 0.4, s.lift || 0));   // leaning in to type (reach, QA); sits up to show the laptop
      const toBody = (x, y, z) => { const r = this.man.root, S = r.scale.x; const v = new THREE.Vector3(x, y, z).sub(r.position).divideScalar(S).sub(new THREE.Vector3(0, 0.48, 0));
        v.applyAxisAngle(new THREE.Vector3(1, 0, 0), -lean); return [v.x, v.y, v.z]; };
      // fingertips rest on the keys: the hand's centre sits a hand-thickness above the keyboard, on the person's half of it
      const KY = this.laptop.position.y + 0.01 + HAND_LIFT, KZ = this.laptop.position.z + KZ_OFF;
      let L = toBody(-0.12, KY + Math.max(0, type) * 0.4, KZ), R = toBody(0.12, KY + Math.max(0, -type) * 0.4, KZ);
      if (k > 0) { L = [lerp(L[0], -0.2, k), lerp(L[1], 0.92, k), lerp(L[2], 0.32, k)]; R = [lerp(R[0], 0.2, k), lerp(R[1], 0.92, k), lerp(R[2], 0.32, k)]; }
      if (f > 0) { R = [lerp(R[0], 0.28, f), lerp(R[1], 0.62, f), lerp(R[2], 0.3, f)]; }
      if (s.clap) {   // clapping at chest height, above the laptop: palms meet on the beat (clapK 1 = together)
        const c = s.clap, gap = 0.035 + 0.075 * (1 - (s.clapK ?? 0.5));
        L = [lerp(L[0], -gap, c), lerp(L[1], 0.36, c), lerp(L[2], 0.34, c)]; R = [lerp(R[0], gap, c), lerp(R[1], 0.36, c), lerp(R[2], 0.34, c)]; }
      // her laptop, picked up and turned round to show us (lift 0..1): rises off the desk, spins to face the camera,
      // stands upright in front of her chest; her hands stay on the sides of the base the whole way
      const lift = s.lift || 0, lp = this.laptop; this.lifting = lift > 0;
      if (lift > 0) {
        const a = sstep(0.0, 0.3, lift), b = easeIO(clamp((lift - 0.18) / 0.82));
        lp.position.set(0, lerp(-0.22, 0.06, b) + 0.05 * Math.sin(Math.PI * b), lerp(-0.42, -0.6, b));
        lp.rotation.set(0.26 * b, Math.PI + Math.PI * b, 0);
        const side = (sx) => new THREE.Vector3(sx * 0.288, 0.004, 0.02).applyEuler(lp.rotation).add(lp.position);   // palms against the sides of the base (QA: touching, not through)
        const hl = side(-1), hr = side(1);
        const Lh = toBody(hl.x, hl.y, hl.z), Rh = toBody(hr.x, hr.y, hr.z);
        L = L.map((v, i) => lerp(v, Lh[i], a)); R = R.map((v, i) => lerp(v, Rh[i], a));
      } else { lp.position.set(0, c.key === 'car' ? -0.2 : -0.22, -0.42); lp.rotation.set(0, Math.PI, 0); }
      const talk = s.talk || 0;
      this.man.pose({ hands: [L, R], headYaw: 0.15 * Math.sin(t * 0.7 + ph) * (1 - lift) + (s.lookYaw || 0), headPitch: (s.headPitch ?? 0) - 0.05 + 0.04 * Math.sin(t * 1.1 + ph) + talk * 0.05 * Math.sin(t * 12),
        headRoll: s.headRoll || 0, lean });
      this.man.expr(s.expr || { smile: 0.15, lids: 0.12 + (Math.sin(t * 2.3 + ph) > 0.985 ? 0.88 : 0) });
    }
    if (this.pet) this.pet.pose(t);
    if (this.dog) {
      this.dog.pose(t);
    }
  }
}

// the grid: 5 x 3 (15 squares), reflowing to 4 x 4 when the new guy joins
export const GAP = 0.32;
export function slotPos(i, cols, rows) {
  const c = i % cols, r = Math.floor(i / cols);
  return new THREE.Vector3((c - (cols - 1) / 2) * (RW + GAP), ((rows - 1) / 2 - r) * (RH + GAP), 0);
}
