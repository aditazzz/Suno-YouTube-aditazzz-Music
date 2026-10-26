// the standup: fifteen diorama rooms (one per square on the call) floating in a grid over the city, plus the new
// guy's sixteenth room. Each room is an open-fronted box with painted (pre-lit) walls, a desk, a laptop and a mannequin.
import * as THREE from 'three';
import { clay, basic, canvasTex, labelPlane, micOff, FONT, rng, lerp, clamp, easeIO, sstep, dotTex } from './lib.js';
import { Mannequin, Dog, letterCard } from './mannequin.js';

export const RW = 3.0, RH = 2.2, RD = 2.3;          // room width, height, depth
export const CAST = [
  { name: 'aditazzz', wall: '#b9a6dc', key: 'lilac', m: { shirt: 0xf25c9a, hair: 'curly', hairColor: 0xff8fc2 }, prop: 'mug' },
  { name: "Somebody's Dog", wall: '#d9c2a2', key: 'living', dog: true },
  { name: 'Tom', wall: '#d8cdb8', key: 'books', m: { shirt: 0x7a2e3b, glasses: true }, prop: 'books' },
  { name: 'Kyle', wall: '#2a2540', key: 'led', led: '#a46bff', m: { shirt: 0x8fb39a, hat: 'cap', hatColor: 0x1f1f24 } },
  { name: 'Greg R.', off: true },
  { name: 'Brad', wall: '#252a40', key: 'led', led: '#5fd3ff', m: { shirt: 0x93b59c, hat: 'cap', hatColor: 0x24242a } },
  { name: 'Ted', wall: '#e3d6bf', key: 'books', m: { shirt: 0xa9c9ef, glasses: true }, prop: 'books' },
  { name: 'Dana (hard stop)', wall: '#9aa6b8', key: 'clock', m: { shirt: 0xb9c6da, hair: 'bun', hairColor: 0x5a4636 } },
  { name: 'Priya · Product', wall: '#dfe6ec', key: 'whiteboard', m: { shirt: 0x3a3d46, hair: 'long', hairColor: 0x1b1514 } },
  { name: 'Mike (host)', wall: '#d8d2c4', key: 'kanban', m: { shirt: 0xb8423a, headset: true } },
  { name: 'Jess', wall: '#2a2d33', key: 'car', m: { shirt: 0xd9a441, hair: 'long', hairColor: 0x1d1612, headphones: true } },
  { name: 'Omar', wall: '#e7ecef', key: 'gym', m: { shirt: 0x2bb3a6 } },
  { name: 'Lena', wall: '#7cc6f2', key: 'beach', m: { shirt: 0xf3efe6, hair: 'long', hairColor: 0xe3c27a } },
  { name: 'Wes', wall: '#9bb7a3', key: 'kitchen', m: { shirt: 0x9fc0d8 } },
  { name: 'Nia', wall: '#4d4466', key: 'cozy', m: { shirt: 0xa99ad8, hat: 'beanie', hatColor: 0xf4a259 } },
  { name: 'Sam (new)', wall: '#f1f3f4', key: 'clean', m: { shirt: 0x4a7fd1, lanyard: true } },
];
export const LETTERS = 'TAKE IT OFFLINE?';

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
    if (k === 'clock') { g.fillStyle = '#f2f2f0'; g.beginPath(); g.arc(560, 180, 90, 0, 7); g.fill(); g.strokeStyle = '#333'; g.lineWidth = 8; g.stroke();
      g.lineWidth = 7; g.beginPath(); g.moveTo(560, 180); g.lineTo(560, 110); g.moveTo(560, 180); g.lineTo(600, 210); g.stroke();
      g.fillStyle = '#c33'; g.font = `bold 30px ${FONT.ui}`; g.fillText('HARD STOP 9:30', 455, 320); }
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
      if (c.key !== 'car') { const desk = new THREE.Mesh(new THREE.BoxGeometry(1.7, 0.06, 0.7), deskM); desk.position.set(0, -0.32, -0.55); this.content.add(desk);
        for (const s of [-1, 1]) { const leg = new THREE.Mesh(new THREE.BoxGeometry(0.05, 0.75, 0.05), deskM); leg.position.set(0.78 * s, -0.72, -0.55); this.content.add(leg); } }
      this.laptop = new THREE.Group(); this.laptop.position.set(0, c.key === 'car' ? -0.2 : -0.29, -0.42); this.content.add(this.laptop);
      const lb = new THREE.Mesh(new THREE.BoxGeometry(0.46, 0.02, 0.32), clay(0xb8bcc4)); this.laptop.add(lb);
      const ls = new THREE.Mesh(new THREE.BoxGeometry(0.46, 0.3, 0.012), clay(0x9a9ea6)); ls.position.set(0, 0.15, -0.16); ls.rotation.x = -0.25; this.laptop.add(ls);
      // the laptop screen faces the person (away from us); its glow lights their face (a soft additive card)
      // the person
      const pz = -1.02;
      if (c.dog) {
        this.dog = new Dog(); this.dog.root.scale.setScalar(1.35); this.dog.root.position.set(0, -RH / 2 - 0.05, pz); this.dog.root.rotation.y = 0; this.content.add(this.dog.root);
      } else {
        this.man = new Mannequin(c.m); this.man.root.position.set(0, -RH / 2 - 0.12, pz); this.man.root.scale.setScalar(1.38); this.content.add(this.man.root);
      }
      // chair back behind the person
      const chairM = clay(c.key === 'car' ? 0x2a2c31 : 0x2c2f36);
      const chair = new THREE.Mesh(new THREE.BoxGeometry(0.62, 0.8, 0.08), chairM); chair.position.set(0, -0.35, pz - 0.3); this.content.add(chair);
      if (c.prop === 'mug') { const mug = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.06, 0.12, 18), clay(0xffffff)); mug.position.set(0.55, -0.23, -0.5); this.content.add(mug); }
      // a lamp
      if (!['car', 'beach'].includes(c.key)) { const lamp = new THREE.Mesh(new THREE.SphereGeometry(0.12, 18, 12), basic(0xffd9a0)); lamp.position.set(RW / 2 - 0.4, 0.45, -RD + 0.35); this.content.add(lamp);
        const glow = new THREE.Sprite(new THREE.SpriteMaterial({ map: dotTex(), color: 0xffc98a, transparent: true, opacity: 0.55, depthWrite: false, blending: THREE.AdditiveBlending })); glow.scale.setScalar(1.1); glow.position.copy(lamp.position); this.content.add(glow); }
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
    this.dark.material.opacity = s.dark || 0; this.dark.visible = (s.dark || 0) > 0.01;
    if (this.statusDot) this.statusDot.visible = (s.blink === undefined) ? true : (Math.floor(t * 3) % 2 === 0);
    if (this.man) {
      const ph = this.idx * 1.7, k = s.card || 0, f = s.fine || 0;
      const type = Math.sin(t * 9 + ph) * 0.015;
      // hands: typing -> card up -> thumbs up
      let L = [-0.16, 0.16 + type, 0.42], R = [0.16, 0.16 - type, 0.42];
      if (k > 0) { L = [lerp(L[0], -0.2, k), lerp(L[1], 0.92, k), lerp(L[2], 0.32, k)]; R = [lerp(R[0], 0.2, k), lerp(R[1], 0.92, k), lerp(R[2], 0.32, k)]; }
      if (f > 0) { R = [lerp(R[0], 0.28, f), lerp(R[1], 0.62, f), lerp(R[2], 0.3, f)]; }
      const talk = s.talk || 0;
      this.man.pose({ hands: [L, R], headYaw: 0.15 * Math.sin(t * 0.7 + ph) + (s.lookYaw || 0), headPitch: -0.05 + 0.04 * Math.sin(t * 1.1 + ph) + talk * 0.05 * Math.sin(t * 12),
        lean: 0.06 + 0.03 * Math.sin(t * 0.5 + ph) });
      if (this.card) { this.card.visible = k > 0.02; this.card.position.set(0, lerp(-0.3, 0.42, k), -0.6); this.card.scale.setScalar(0.6 + 0.4 * k); }
    }
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
