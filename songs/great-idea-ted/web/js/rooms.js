// the standup: fifteen diorama rooms (one per square on the call) floating in a grid over the city, plus the new
// guy's sixteenth room. Each room is an open-fronted box with painted (pre-lit) walls, a desk, a laptop and a mannequin.
import * as THREE from 'three';
import { clay, basic, canvasTex, labelPlane, micOff, micOn, FONT, rng, lerp, clamp, easeIO, sstep, dotTex } from './lib.js';
import { Mannequin, Dog, Doodle, Cat, letterCard } from './mannequin.js';

export const RW = 3.0, RH = 2.2, RD = 2.3;          // room width, height, depth
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
  constructor(idx) {
    const c = this.c = CAST[idx]; this.idx = idx; const g = this.root = new THREE.Group();
    this.content = new THREE.Group(); g.add(this.content);
    if (c.off) {                                   // Greg: camera off. a dark panel, his initials, a muted mic
      const tex = canvasTex(600, 440, (gg, w, h) => { gg.fillStyle = '#14151a'; gg.fillRect(0, 0, w, h);
        gg.fillStyle = '#2b2d36'; gg.beginPath(); gg.arc(w / 2, h / 2 - 20, 86, 0, 7); gg.fill();
        gg.fillStyle = '#e8e8ec'; gg.font = `600 80px ${FONT.ui}`; gg.textAlign = 'center'; gg.textBaseline = 'middle'; gg.fillText('GR', w / 2, h / 2 - 16);
        gg.font = `500 40px ${FONT.ui}`; gg.fillText('Greg R.', w / 2, h / 2 + 110); micOff(gg, w - 60, 56, 50); });
      this.panel = new THREE.Mesh(new THREE.PlaneGeometry(RW, RH), basic(0xffffff, { map: tex })); this.panel.position.z = 0.0; this.content.add(this.panel);
      this.statusDot = new THREE.Mesh(new THREE.CircleGeometry(0.07, 20), basic(0x46e678)); this.statusDot.position.set(-RW / 2 + 0.25, RH / 2 - 0.25, 0.01); this.content.add(this.statusDot);
    } else {
      const back = new THREE.Mesh(new THREE.PlaneGeometry(RW, RH), basic(0xffffff, { map: backWallTex(c, idx * 7 + 3) })); back.position.z = -RD; this.content.add(back);
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
    this.tag = labelPlane(c.name, { h: 0.2, icon: c.off ? null : (gg, x, y, s) => micOff(gg, x, y, s) });
    this.tag.position.set(-RW / 2 + 0.08 + this.tag.userData.w / 2, -RH / 2 + 0.17, 0.03); g.add(this.tag);
    if (!c.off) { this.tagOn = labelPlane(c.name, { h: 0.2, icon: (gg, x, y, s) => micOn(gg, x, y, s) }); this.tagOn.position.copy(this.tag.position); this.tagOn.visible = false; g.add(this.tagOn); }   // unmuted while talking
    // the letter card this square holds up in the choruses
    const ch = LETTERS[idx] || ' ';
    if (ch !== ' ' && !c.off) { this.card = letterCard(ch); this.card.visible = false; this.content.add(this.card); }
    // the blackout cover (everyone else goes dark when he says it)
    this.dark = new THREE.Mesh(new THREE.PlaneGeometry(RW, RH), basic(0x050506, { transparent: true, opacity: 0 })); this.dark.position.z = 0.02; g.add(this.dark);
  }
  /** s: { t, talk 0..1, talkCol, card 0..1 (holding the letter up), fine 0..1 (thumbs up), dark 0..1, lookYaw } */
  update(s) {
    const t = s.t, c = this.c;
    const base = new THREE.Color(0x4a4d55), col = new THREE.Color(s.talkCol || 0x3ee07a);
    this.frameM.color.copy(base.lerp(col, s.talk || 0));
    if (this.tagOn) { const on = (s.talk || 0) > 0.3; this.tagOn.visible = on; this.tag.visible = !on; }
    this.dark.material.opacity = s.dark || 0; if (this.panel) this.panel.material.color.setScalar(1 - (s.dark || 0)); this.dark.visible = (s.dark || 0) > 0.01;
    if (this.statusDot) this.statusDot.visible = (s.blink === undefined) ? true : (Math.floor(t * 3) % 2 === 0);
    if (this.man) {
      const ph = this.idx * 1.7, k = s.card || 0, f = s.fine || 0;
      const type = Math.sin(t * 9 + ph) * 0.015;
      // hands: typing -> card up -> thumbs up
      const lean = 0.13 + 0.025 * Math.sin(t * 0.5 + ph);   // leaning in to type (reach, QA)
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
      if (s.offer) { const k = s.offer; R = [lerp(R[0], 0.16, k), lerp(R[1], 0.5, k), lerp(R[2], 0.42, k)]; }   // holding something out to you
      if (s.phone) { const k = s.phone; R = [lerp(R[0], 0.06, k), lerp(R[1], 0.5, k), lerp(R[2], 0.3, k)]; L = [lerp(L[0], -0.04, k), lerp(L[1], 0.48, k), lerp(L[2], 0.3, k)]; }
      const talk = s.talk || 0;
      this.man.pose({ hands: [L, R], headYaw: 0.15 * Math.sin(t * 0.7 + ph) + (s.lookYaw || 0), headPitch: (s.phone ? 0.42 * s.phone : 0) - 0.05 + 0.04 * Math.sin(t * 1.1 + ph) + talk * 0.05 * Math.sin(t * 12),
        lean });
      if (this.card) { this.card.visible = k > 0.02; this.card.position.set(0, lerp(-0.3, 0.42, k), -0.6); this.card.scale.setScalar(0.6 + 0.4 * k); }
      if (!this.phoneM) { this.phoneM = new THREE.Mesh(new THREE.BoxGeometry(0.075, 0.14, 0.01), clay(0x202227)); const sc = new THREE.Mesh(new THREE.PlaneGeometry(0.066, 0.128), basic(0x9fd8ff));
        sc.position.z = -0.006; sc.rotation.y = Math.PI; this.phoneM.add(sc); this.man.body.add(this.phoneM); }
      this.phoneM.visible = !!s.phone; if (s.phone) { const h = this.man.arms[1].hand.position; this.phoneM.position.set(h.x - 0.03, h.y + 0.04, h.z + 0.02); this.phoneM.rotation.set(-0.9, 0, 0); }
      if (s.offer && !this.lunchM) { const bag = this.lunchM = new THREE.Group(); const kraft = clay(0xc49a6c);
        const b = new THREE.Mesh(new THREE.BoxGeometry(0.16, 0.22, 0.1), kraft); bag.add(b); const fold = new THREE.Mesh(new THREE.BoxGeometry(0.16, 0.035, 0.104), clay(0xa87f52)); fold.position.y = 0.12; bag.add(fold); this.man.body.add(bag); }
      if (this.lunchM) { this.lunchM.visible = !!s.offer; if (s.offer) { const h = this.man.arms[1].hand.position; this.lunchM.position.set(h.x, h.y - 0.13, h.z + 0.05); } }
      this.man.expr(s.expr || { smile: 0.15, lids: 0.12 + (Math.sin(t * 2.3 + ph) > 0.985 ? 0.88 : 0) });
    }
    if (this.pet) this.pet.pose(t);
    if (s.printer && !this.printerM) {   // a small printer on the desk, a page coming out
      const pr = this.printerM = new THREE.Group(); pr.position.set(-0.55, -0.22, -0.55); this.content.add(pr);
      const body = new THREE.Mesh(new THREE.BoxGeometry(0.4, 0.16, 0.3), clay(0xe7e9ee)); body.position.y = 0.08; pr.add(body);
      const slot = new THREE.Mesh(new THREE.BoxGeometry(0.3, 0.02, 0.02), clay(0x30323a)); slot.position.set(0, 0.12, 0.151); pr.add(slot);
      const ptex = canvasTex(400, 520, (g, w, h) => { g.fillStyle = '#fff'; g.fillRect(0, 0, w, h); g.fillStyle = '#1E2240'; g.font = `bold 58px ${FONT.ui}`; g.fillText('Push the', 34, 130); g.fillText('launch.', 34, 200);
        g.font = `30px ${FONT.ui}`; g.fillStyle = '#6B6F86'; g.fillText("We're not ready and", 34, 270); g.fillText('we know it.', 34, 310); g.fillStyle = '#ff4fb0'; g.font = `bold 36px ${FONT.ui}`; g.fillText('— You', 34, 400); });
      const page = this.pageM = new THREE.Mesh(new THREE.PlaneGeometry(0.22, 0.29), basic(0xd2d2d2, { map: ptex, side: THREE.DoubleSide })); page.position.set(0, 0.2, 0.2); page.rotation.x = -0.9; pr.add(page);   // kept under the bloom threshold so the text stays crisp
      const cb = new THREE.Mesh(new THREE.BoxGeometry(0.4, 0.2, 0.3), new THREE.MeshBasicMaterial({ visible: false })); cb.position.set(-0.55, -0.12, -0.55); this.content.add(cb); this.solids.push(['printer', cb, () => this.printerM.visible]); }
    if (this.printerM) { this.printerM.visible = !!s.printer;
      const f = s.paperFloat || 0;   // the printout lifts out of the printer and hangs in the air, facing us
      this.pageM.position.set(-0.12 * f, 0.2 + 0.56 * f, 0.2 + 0.5 * f); this.pageM.rotation.set(-0.9 * (1 - f), 0.25 * f, -0.12 * f); this.pageM.scale.setScalar(1 + 1.1 * f); }
    if (s.sticky && !this.stickyM) {   // a sticky note on the back of the laptop lid, facing us
      const lid = this.laptop.children[1]; const tex = canvasTex(256, 256, (g, w, h) => { g.fillStyle = '#ffe680'; g.fillRect(0, 0, w, h); g.fillStyle = '#5a4a1e'; g.font = `italic 44px ${FONT.serif}`; g.textAlign = 'center';
        s.sticky.split('\n').forEach((l, i) => g.fillText(l, w / 2, 90 + i * 56)); });
      this.stickyM = new THREE.Mesh(new THREE.PlaneGeometry(0.24, 0.24), basic(0xffffff, { map: tex })); this.stickyM.position.set(0.0, 0.0, -0.0075); this.stickyM.rotation.set(0, Math.PI, 0.06); lid.add(this.stickyM); }
    if (this.stickyM) this.stickyM.visible = !!s.sticky;
    if (s.donuts && !this.donutBox) {   // an open pink bakery box: a tray with walls, a hinged lid, six donuts. Yours are ludicrous.
      const wild = this.idx === 0, bx = this.donutBox = new THREE.Group(); const pink = clay(0xf7b6cf), pinkIn = clay(0xf9cfe0);
      bx.position.set(wild ? -0.56 : 0.56, -0.218, -0.5); bx.rotation.y = wild ? 0.18 : -0.18; this.content.add(bx);
      const W = 0.4, D = 0.28, H = 0.05, T = 0.008;
      const base = new THREE.Mesh(new THREE.BoxGeometry(W, T, D), pinkIn); base.position.y = T / 2; bx.add(base);
      for (const [w, d, x, z] of [[W, T, 0, D / 2], [W, T, 0, -D / 2], [T, D, W / 2, 0], [T, D, -W / 2, 0]]) { const wall = new THREE.Mesh(new THREE.BoxGeometry(w, H, d), pink); wall.position.set(x, H / 2, z); bx.add(wall); }
      const hinge = new THREE.Group(); hinge.position.set(0, H, -D / 2); hinge.rotation.x = -1.95; bx.add(hinge);   // lid tipped back past upright
      const lid = new THREE.Mesh(new THREE.BoxGeometry(W, T * 1.5, D), pink); lid.position.z = D / 2; hinge.add(lid);
      const logo = new THREE.Mesh(new THREE.PlaneGeometry(W * 0.6, D * 0.35), basic(0xffffff, { map: canvasTex(256, 96, (g, w, h) => { g.fillStyle = '#f7b6cf'; g.fillRect(0, 0, w, h); g.fillStyle = '#c2185b'; g.font = `italic bold 44px ${FONT.serif}`; g.textAlign = 'center'; g.fillText(wild ? 'the good ones' : 'donuts', w / 2, 62); }) }));
      logo.position.set(0, -T, D / 2); logo.rotation.x = Math.PI / 2; hinge.add(logo);
      const dough = clay(0xd9a05b), ice = [clay(0xff7fb0), clay(0x6b3f2a), clay(0xfff1e0), clay(0x7fd8ff), clay(0xb98cff), clay(0xffd27a)];
      const sprCol = [0xffffff, 0x45f0ff, 0xffd27a, 0x7fe0c2, 0xff4f6d, 0x9b6bff].map((c) => basic(c));
      let sd = 5 + this.idx; const R = () => (sd = (sd * 16807) % 2147483647) / 2147483647;
      for (let n = 0; n < 6; n++) { const d = new THREE.Group(); d.position.set(-0.125 + (n % 3) * 0.125, 0.032, -0.062 + Math.floor(n / 3) * 0.124); bx.add(d);
        const ring = new THREE.Mesh(new THREE.TorusGeometry(0.038, 0.02, 10, 22), dough); ring.rotation.x = Math.PI / 2; d.add(ring);
        const ic = new THREE.Mesh(new THREE.TorusGeometry(0.038, 0.0155, 10, 22), ice[wild ? n : n % 3]); ic.rotation.x = Math.PI / 2; ic.position.y = 0.01; d.add(ic);
        if (!wild) continue;
        // ludicrous: sprinkles everywhere, plus one over-the-top thing per donut
        for (let k = 0; k < 16; k++) { const a = R() * 7, rr = 0.026 + R() * 0.024; const sp = new THREE.Mesh(new THREE.CapsuleGeometry(0.0022, 0.009, 2, 4), sprCol[k % 6]); sp.position.set(Math.cos(a) * rr, 0.027, Math.sin(a) * rr); sp.rotation.set(Math.PI / 2, 0, R() * 3); d.add(sp); }
        const top = new THREE.Group(); top.position.y = 0.03; d.add(top);
        if (n === 0) { for (let k = 0; k < 4; k++) { const m = new THREE.Mesh(new THREE.CylinderGeometry(0.009, 0.009, 0.014, 10), clay(0xfffaf2)); m.position.set(-0.02 + k * 0.013, 0.006, (k % 2) * 0.012 - 0.006); top.add(m); } }   // mini marshmallows
        if (n === 1) { const c = new THREE.Mesh(new THREE.CylinderGeometry(0.004, 0.004, 0.05, 8), clay(0x7fd8ff)); c.position.y = 0.025; top.add(c); const fl = new THREE.Mesh(new THREE.ConeGeometry(0.006, 0.014, 8), basic(0xffb347)); fl.position.y = 0.057; top.add(fl); }   // a birthday candle
        if (n === 2) { for (let k = 0; k < 5; k++) { const o = new THREE.Mesh(new THREE.TorusGeometry(0.007, 0.003, 6, 12), clay([0xff6b5b, 0xffd27a, 0x7fe0c2, 0xb98cff, 0x45f0ff][k])); const a = k * 1.3; o.position.set(Math.cos(a) * 0.035, 0.003, Math.sin(a) * 0.035); o.rotation.x = R() * 2; top.add(o); } }   // cereal loops
        if (n === 3) { const b = new THREE.Mesh(new THREE.BoxGeometry(0.06, 0.006, 0.016), clay(0xb5543a)); b.rotation.set(0.2, 0.6, 0.15); b.position.y = 0.004; top.add(b); }   // a strip of bacon
        if (n === 4) { const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.002, 0.002, 0.06, 6), clay(0xffffff)); pole.position.y = 0.03; top.add(pole); const um = new THREE.Mesh(new THREE.ConeGeometry(0.03, 0.016, 12, 1, true), clay(0xff4fb0, { side: THREE.DoubleSide })); um.position.y = 0.062; top.add(um); }   // a cocktail umbrella
        if (n === 5) { const bear = new THREE.Group(); const gm = clay(0x5ee08f); const bb = new THREE.Mesh(new THREE.SphereGeometry(0.011, 10, 8), gm); bb.scale.set(1, 1.3, 0.8); bear.add(bb); const hh = new THREE.Mesh(new THREE.SphereGeometry(0.008, 10, 8), gm); hh.position.y = 0.017; bear.add(hh);
          for (const sx of [-1, 1]) { const e = new THREE.Mesh(new THREE.SphereGeometry(0.004, 6, 6), gm); e.position.set(sx * 0.006, 0.025, 0); bear.add(e); } bear.position.y = 0.012; top.add(bear); }   // a gummy bear, standing
        const drz = new THREE.Mesh(new THREE.TorusGeometry(0.03, 0.0025, 6, 24, Math.PI * 1.4), clay(0xffffff)); drz.rotation.x = Math.PI / 2; drz.rotation.z = R() * 3; drz.position.y = 0.027; d.add(drz); }   // a white drizzle on every one
      const cb = new THREE.Mesh(new THREE.BoxGeometry(W, 0.06, D), new THREE.MeshBasicMaterial({ visible: false })); cb.position.copy(bx.position); cb.position.y += 0.03; cb.rotation.y = bx.rotation.y; this.content.add(cb); this.solids.push(['donut box', cb, () => this.donutBox.visible]); }
    if (this.donutBox) this.donutBox.visible = !!s.donuts;
    if (this.dog) {
      this.dog.pose(t);
      if (this.card) { const k = s.card || 0; this.card.visible = k > 0.02; this.card.position.set(0, lerp(-0.45, -0.02, k), -0.58); this.card.scale.setScalar(0.5 + 0.28 * k); }
    }
  }
}

// the grid: 5 x 3 (15 squares), reflowing to 4 x 4 when the new guy joins
export const GAP = 0.32;
export function slotPos(i, cols, rows) {
  const c = i % cols, r = Math.floor(i / cols);
  return new THREE.Vector3((c - (cols - 1) / 2) * (RW + GAP), ((rows - 1) / 2 - r) * (RH + GAP), 0);
}
