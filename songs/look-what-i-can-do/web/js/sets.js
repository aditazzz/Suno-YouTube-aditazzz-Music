// set pieces: the glossy floor (with cheap planar reflections), the laptop + desk, the screen field (instanced, her
// footage in every screen), hero screens, neon signs
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import * as M from './media.js';
import { canvasTex, FONT, clamp, easeOut, lerp, rng } from './lib.js';

// ---------------------------------------------------------------- floor + mirror world
// Anything added to `mirror` is drawn upside down under the floor; the floor is a dark, slightly transparent gloss over it.
export function makeFloor(scene, envTex) {
  const mirror = new THREE.Group(); mirror.scale.y = -1; scene.add(mirror);
  const fm = new THREE.MeshBasicMaterial({ color: 0x010102, transparent: true, opacity: 0.87 });   // black glass: only the mirror world shows in it
  const floor = new THREE.Mesh(new THREE.CircleGeometry(400, 96), fm); floor.rotation.x = -Math.PI / 2; floor.renderOrder = 5; scene.add(floor);
  return { floor, mirror, mat: fm };
}

// ---------------------------------------------------------------- laptop on a desk
export class Laptop {
  constructor(envTex) {
    this.root = new THREE.Group();
    const alu = new THREE.MeshStandardMaterial({ color: 0x9a9da5, metalness: 1.0, roughness: 0.4, envMap: envTex, envMapIntensity: 0.45 });
    const dark = new THREE.MeshStandardMaterial({ color: 0x111114, metalness: 0.2, roughness: 0.6, envMap: envTex, envMapIntensity: 0.3 });
    const base = new THREE.Mesh(new RoundedBoxGeometry(0.32, 0.012, 0.222, 4, 0.006), alu); base.position.y = 0.006; this.root.add(base);
    const kb = new THREE.Mesh(new THREE.PlaneGeometry(0.27, 0.105), new THREE.MeshStandardMaterial({ map: keyboardTex(), roughness: 0.7, metalness: 0.1 }));
    kb.rotation.x = -Math.PI / 2; kb.position.set(0, 0.0125, -0.022); this.root.add(kb);
    const pad = new THREE.Mesh(new THREE.PlaneGeometry(0.11, 0.07), new THREE.MeshStandardMaterial({ color: 0xa8abb3, metalness: 0.9, roughness: 0.45, envMap: envTex }));
    pad.rotation.x = -Math.PI / 2; pad.position.set(0, 0.0126, 0.068); this.root.add(pad);
    this.hinge = new THREE.Group(); this.hinge.position.set(0, 0.012, -0.108); this.root.add(this.hinge);
    this.tilt = 12 * Math.PI / 180; this.hinge.rotation.x = -this.tilt;
    const lid = new THREE.Mesh(new RoundedBoxGeometry(0.32, 0.212, 0.007, 4, 0.004), alu); lid.position.set(0, 0.106, -0.0035); this.hinge.add(lid);
    const bez = new THREE.Mesh(new THREE.PlaneGeometry(0.312, 0.204), dark); bez.position.set(0, 0.106, 0.0001); this.hinge.add(bez);
    this.dispW = 0.300; this.dispH = this.dispW * 9 / 16;
    this.dispMat = new THREE.MeshBasicMaterial({ color: 0xffffff, toneMapped: false });
    this.disp = new THREE.Mesh(new THREE.PlaneGeometry(this.dispW, this.dispH), this.dispMat); this.disp.position.set(0, 0.106 + 0.004, 0.0003); this.hinge.add(this.disp);
    this.glow = new THREE.PointLight(0x9fb7ff, 0.35, 1.6, 2); this.glow.position.set(0, 0.12, 0.25); this.hinge.add(this.glow);
  }
  // world-space center + normal of the display (for the camera that starts inside it)
  dispFrame() {
    this.root.updateMatrixWorld(true);
    const c = this.disp.getWorldPosition(new THREE.Vector3());
    const n = new THREE.Vector3(0, 0, 1).applyQuaternion(this.disp.getWorldQuaternion(new THREE.Quaternion()));
    const up = new THREE.Vector3(0, 1, 0).applyQuaternion(this.disp.getWorldQuaternion(new THREE.Quaternion()));
    return { c, n, up };
  }
}
function keyboardTex() {
  return canvasTex(1024, 400, (g, w, h) => {
    g.fillStyle = '#0d0d10'; g.fillRect(0, 0, w, h);
    const rows = 6, cols = 14; const kw = w / cols, kh = h / rows;
    for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) {
      if (r === 5 && c > 3 && c < 10) { if (c === 4) { g.fillStyle = '#1b1b20'; g.beginPath(); g.roundRect(c * kw + 4, r * kh + 4, kw * 6 - 8, kh - 8, 8); g.fill(); } continue; }
      g.fillStyle = '#1b1b20'; g.beginPath(); g.roundRect(c * kw + 4, r * kh + 4, kw - 8, kh - 8, 8); g.fill();
    }
  });
}
export function makeDesk(envTex) {
  const g = new THREE.Group();
  const grain = canvasTex(1024, 512, (g, w, h) => { g.fillStyle = '#4a2f1e'; g.fillRect(0, 0, w, h); const R = rng(9);
    for (let i = 0; i < 260; i++) { const y = R() * h; g.strokeStyle = `rgba(${20 + R() * 30},${12 + R() * 18},${8 + R() * 10},${0.25 + R() * 0.35})`; g.lineWidth = 1 + R() * 3; g.beginPath(); g.moveTo(0, y);
      for (let x = 0; x <= w; x += 64) g.lineTo(x, y + Math.sin(x * 0.01 + i) * 6 * R()); g.stroke(); } });
  const top = new THREE.Mesh(new RoundedBoxGeometry(1.7, 0.04, 0.8, 4, 0.012), new THREE.MeshStandardMaterial({ map: grain, color: 0xc8b8a8, roughness: 0.38, metalness: 0.0, envMap: envTex, envMapIntensity: 0.3 }));
  top.position.y = 0.73; g.add(top);
  const legM = new THREE.MeshStandardMaterial({ color: 0x0e0e10, roughness: 0.4, metalness: 0.8, envMap: envTex });
  for (const [x, z] of [[-0.78, -0.33], [0.78, -0.33], [-0.78, 0.33], [0.78, 0.33]]) { const l = new THREE.Mesh(new THREE.CylinderGeometry(0.016, 0.016, 0.71, 12), legM); l.position.set(x, 0.355, z); g.add(l); }
  return g;
}

// the look of screen backs (set before building: dark for a dark world, soft grey for the bright one)
export const LOOK = { back: 'vec3(0.012, 0.012, 0.016)' };

// ---------------------------------------------------------------- the screen field: hundreds of screens, one InstancedMesh per atlas
const RECT_VS_DECL = 'attribute vec4 aRect;\n';
export function screenMat(atlasName, opts = {}) {
  const m = new THREE.MeshBasicMaterial({ map: M.texOf(atlasName), toneMapped: false, side: THREE.DoubleSide, transparent: !!opts.transparent, depthWrite: !opts.transparent });
  m.onBeforeCompile = (sh) => {
    sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\n' + RECT_VS_DECL)
      .replace('#include <uv_vertex>', '#include <uv_vertex>\n#ifdef USE_MAP\n vMapUv = uv * aRect.zw + aRect.xy;\n#endif');
    sh.fragmentShader = sh.fragmentShader.replace('#include <map_fragment>', '#include <map_fragment>\n if (!gl_FrontFacing) diffuseColor.rgb = ' + LOOK.back + ';');
  };
  m.customProgramCacheKey = () => 'rect';
  return m;
}
export class Field {
  // slots: [{atlas, cell, pos:V3, yaw, size, t0 (appear), parent (index or -1)}]
  constructor(slots, mirrorGroup, opts = {}) {
    this.slots = slots; this.root = new THREE.Group(); this.meshes = {};
    const by = {}; slots.forEach((s, i) => { (by[s.atlas] = by[s.atlas] || []).push(i); });
    for (const a of Object.keys(by)) {
      const idx = by[a]; const vert = a[0] === 'V';
      const geo = new THREE.PlaneGeometry(vert ? 0.5625 : 1.0, vert ? 1.0 : 0.5625);
      const rect = new Float32Array(idx.length * 4); idx.forEach((si, k) => rect.set(M.cellRect(a, slots[si].cell), k * 4));
      geo.setAttribute('aRect', new THREE.InstancedBufferAttribute(rect, 4));
      const mat = screenMat(a);
      const im = new THREE.InstancedMesh(geo, mat, idx.length); im.frustumCulled = false;
      im.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
      im.setColorAt(0, new THREE.Color(1, 1, 1)); im.instanceColor.setUsage(THREE.DynamicDrawUsage);
      this.root.add(im);
      let tw = null;
      if (mirrorGroup) { tw = new THREE.InstancedMesh(geo, mat, idx.length); tw.instanceMatrix = im.instanceMatrix; tw.instanceColor = im.instanceColor; tw.frustumCulled = false; mirrorGroup.add(tw); }
      this.meshes[a] = { im, tw, idx };
    }
    this._m = new THREE.Matrix4(); this._q = new THREE.Quaternion(); this._s = new THREE.Vector3(); this._p = new THREE.Vector3(); this._c = new THREE.Color();
    this.hidden = new Set();
  }
  // per frame: each slot's placement from its appear time (children grow out of their parent), brightness
  update(t, opts = {}) {
    const { bright = 1, pulse = 0, dur = 0.38 } = opts;
    for (const a of Object.keys(this.meshes)) {
      const { im, idx } = this.meshes[a];
      idx.forEach((si, k) => {
        const s = this.slots[si];
        let vis = t >= s.t0 && !this.hidden.has(si);
        let p = s.pos, yaw = s.yaw, sc = s.size;
        if (vis) {
          const e = easeOut((t - s.t0) / dur);
          if (s.parent >= 0 && e < 1) { const pp = this.slots[s.parent]; p = this._p.lerpVectors(pp.pos, s.pos, e); yaw = lerp(pp.yaw, s.yaw, e); sc = lerp(pp.size, s.size, e); }
          else if (s.parent < 0) sc = s.size * (0.6 + 0.4 * e);
          const fl = s.parent < 0 ? Math.min(1, (t - s.t0) / 0.08) : 1;
          const b = bright * (s.dim ?? 1) * fl * (0.84 + pulse * 0.1);
          this._c.setRGB(b, b, b); im.setColorAt(k, this._c);
        }
        this._q.setFromAxisAngle(THREE.Object3D.DEFAULT_UP, yaw);
        if (!vis) sc = 0.00001;
        this._s.setScalar(sc); this._m.compose(p, this._q, this._s); im.setMatrixAt(k, this._m);
      });
      im.instanceMatrix.needsUpdate = true; im.instanceColor.needsUpdate = true;
    }
  }
  atlases() { return Object.keys(this.meshes); }
}

// a single framed screen (close-ups, billboards): bezel + display; the display can show an atlas cell, a hero sequence or an image
export class Screen {
  constructor(w, h, envTex, { bezel = 0.03, depth = 0.04 } = {}) {
    this.root = new THREE.Group(); this.w = w; this.h = h;
    const fr = new THREE.MeshStandardMaterial({ color: 0x0b0b0d, metalness: 0.85, roughness: 0.28, envMap: envTex, envMapIntensity: 0.9 });
    this.frame = new THREE.Mesh(new RoundedBoxGeometry(w + bezel * 2, h + bezel * 2, depth, 3, Math.min(0.02, bezel * 0.8)), fr); this.frame.position.z = -depth / 2; this.root.add(this.frame);
    this.mat = new THREE.MeshBasicMaterial({ color: 0xffffff, toneMapped: false });
    this.mat.onBeforeCompile = (sh) => { sh.fragmentShader = sh.fragmentShader.replace('#include <map_fragment>', '#include <map_fragment>\n if (!gl_FrontFacing) diffuseColor.rgb = ' + LOOK.back + ';'); };
    this.geo = new THREE.PlaneGeometry(w, h); this.disp = new THREE.Mesh(this.geo, this.mat); this.disp.position.z = 0.001; this.root.add(this.disp);
    this.src = null;
  }
  show(src, cell = 0) {   // src: atlas name, hero name, or a THREE.Texture
    const key = (typeof src === 'string' ? src : src.uuid) + ':' + cell; if (key === this.src) return; this.src = key;
    const uv = this.geo.attributes.uv; const base = [[0, 1], [1, 1], [0, 0], [1, 0]];
    if (typeof src === 'string' && M.ATLAS[src]) {
      this.mat.map = M.texOf(src); const [ox, oy, sx, sy] = M.cellRect(src, cell, 0);
      base.forEach(([u, v], k) => uv.setXY(k, ox + u * sx, oy + v * sy));
    } else {
      this.mat.map = typeof src === 'string' ? M.texOf(src) : src; base.forEach(([u, v], k) => uv.setXY(k, u, v));
    }
    uv.needsUpdate = true; this.mat.needsUpdate = true;
  }
  atlasName() { return this.src ? this.src.split(':')[0] : null; }
}

// ---------------------------------------------------------------- neon type (her bubblegum pink), with a flicker-on
export function neon(text, { h = 1, color = '#ff5fa2', core = '#ffe3f0', font = FONT.anton, size = 220, blur = 0.35 } = {}) {
  const f = `${size}px ${font}`; const g0 = document.createElement('canvas').getContext('2d'); g0.font = f;
  const tw = g0.measureText(text).width; const pad = size * 0.55; const W = Math.ceil(tw + pad * 2), H = Math.ceil(size * 1.6 + pad);
  const tex = canvasTex(W, H, (g, w, hh) => {
    g.font = f; g.textAlign = 'center'; g.textBaseline = 'middle';
    g.shadowColor = color; g.shadowBlur = size * blur; g.fillStyle = color; for (let i = 0; i < 3; i++) g.fillText(text, w / 2, hh / 2);
    g.shadowBlur = size * 0.08; g.lineWidth = size * 0.035; g.strokeStyle = core; g.strokeText(text, w / 2, hh / 2);
    g.shadowBlur = 0; g.fillStyle = core; g.globalAlpha = 0.35; g.fillText(text, w / 2, hh / 2);
  });
  const mat = new THREE.MeshBasicMaterial({ map: tex, transparent: true, depthWrite: false, toneMapped: false, blending: THREE.AdditiveBlending });
  const m = new THREE.Mesh(new THREE.PlaneGeometry(h * W / H, h), mat); m.userData.w = h * W / H;
  return m;
}
export function flicker(t, t0, seed = 1) {   // 0..1 brightness of a neon tube switching on at t0
  if (t < t0) return 0; const x = t - t0; if (x > 0.7) return 1;
  const r = rng(Math.floor(x * 30) + seed * 97)(); return x < 0.12 ? (r > 0.5 ? 0.9 : 0.05) : x < 0.35 ? (r > 0.3 ? 1 : 0.2) : (r > 0.1 ? 1 : 0.5);
}

// ---------------------------------------------------------------- neon letters laid in a ring on the floor (reads from above)
export function flatGlyph(text, { h = 1, color = '#ff5fa2', font = FONT.anton, size = 220 } = {}) {   // solid printed type (for bright floors)
  const f = `${size}px ${font}`; const g0 = document.createElement('canvas').getContext('2d'); g0.font = f;
  const tw = g0.measureText(text).width; const pad = size * 0.55; const W = Math.ceil(tw + pad * 2), H = Math.ceil(size * 1.6 + pad);
  const tex = canvasTex(W, H, (g, w, hh) => { g.font = f; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillStyle = color; g.fillText(text, w / 2, hh / 2); });
  const mat = new THREE.MeshBasicMaterial({ map: tex, transparent: true, depthWrite: false, toneMapped: false });
  const m = new THREE.Mesh(new THREE.PlaneGeometry(h * W / H, h), mat); m.userData.w = h * W / H; return m;
}
export function neonRing(text, { r = 2.0, h = 0.42, color = '#ff5fa2', core = '#ffe3f0', font = FONT.anton, size = 200, reps = 2, sep = ' · ', blur = 0.35, flat = false } = {}) {
  const g = new THREE.Group(); const full = (text + sep).repeat(reps);
  const g0 = document.createElement('canvas').getContext('2d'); g0.font = `${size}px ${font}`;
  const ws = [...full].map((ch) => g0.measureText(ch).width); const tot = ws.reduce((a, b) => a + b, 0);
  let acc = 0; const letters = [];
  [...full].forEach((ch, i) => {
    const a0 = (acc + ws[i] / 2) / tot * Math.PI * 2; acc += ws[i];
    if (ch === ' ') return;
    const m = flat ? flatGlyph(ch, { h, color, font, size }) : neon(ch, { h, color, core, font, size, blur });
    m.position.set(-Math.sin(a0) * r, 0.004, Math.cos(a0) * r);   // tops outward, reading clockwise from above
    m.rotation.set(-Math.PI / 2, 0, 0); m.rotateOnWorldAxis(new THREE.Vector3(0, 1, 0), Math.PI - a0); m.renderOrder = 6;
    m.userData.a = a0; g.add(m); letters.push(m);
  });
  g.userData.letters = letters; return g;
}
