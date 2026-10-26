// The outro: the Fool card made real. The headland at night (sky, sea, Mars, the stone ship), the man at the cliff
// edge with the rocket on his shoulder like the Fool's bundle, the little robot at his heel, and then everyone: the
// seeress, the Vikings and the robots in the ship, and the cliff lined with figures as far as the eye goes.
import * as THREE from 'three';
import { RIM, RIM_AMT, clamp, lerp, easeIO, easeOut, rng } from './lib.js';
import { buildHeadland, HEAD } from './headland.js';
import { TechKing, Seeress, Viking, makeStaff, shadows } from './puppets.js';
import { makeRocket } from './rocket.js';
import { Robot } from './robots.js';

const V = (x, y, z) => new THREE.Vector3(x, y, z);
const ramp = (t, a, b, e = easeIO) => e(clamp((t - a) / (b - a)));
const decay = (t, t0, tau) => t < t0 ? 0 : Math.exp(-(t - t0) / tau);

export function buildFinale(env, M, { VIKS }) {
  const scene = new THREE.Scene(); scene.fog = new THREE.FogExp2(0x070a16, 0.0065); scene.background = new THREE.Color(0x020308);
  const hd = buildHeadland(env); scene.add(hd);
  hd.userData.moon.target.position.set(0, 0, -12);
  const land = hd.children.find((c) => c.isMesh && c.geometry && c.geometry.type === 'PlaneGeometry' && c.material.vertexColors);
  const ray = new THREE.Raycaster(); scene.updateMatrixWorld(true);
  const ground = (x, z) => { ray.set(V(x, 50, z), V(0, -1, 0)); const h = land ? ray.intersectObject(land, false)[0] : null; return h ? h.point.y : 0; };
  const MANZ = -26.2;
  // ---- the man, the rocket, the little robot
  const king = new TechKing(M); king.root.position.set(0, ground(0, MANZ), MANZ); king.root.rotation.y = Math.PI; scene.add(king.root);
  const rocket = makeRocket(env, { h: 0.7 }); scene.add(rocket);
  const bot = new Robot(M, env, { scale: 0.42 }); bot.root.position.set(0.32, ground(0.32, MANZ + 0.35), MANZ + 0.35); bot.root.rotation.y = Math.PI + 0.7; scene.add(bot.root);
  // ---- everyone in the ship: the seeress, Vikings, robots (standing, looking up at Mars)
  const crew = [];
  const se = new Seeress(M); se.root.position.set(-1.6, ground(-1.6, -19.5), -19.5); se.root.rotation.y = Math.PI + 0.25; scene.add(se.root); crew.push([se, 'seer']);
  const staff = makeStaff(M); scene.add(staff);
  const spots = [[1.6, -17.5], [-1.4, -15.0], [2.0, -13.0], [-2.2, -10.5], [0.6, -9.0], [2.4, -6.5], [-1.0, -4.5], [1.5, -2.0], [-2.4, 0.5], [0.2, 2.5]];
  spots.forEach(([x, z], i) => { const v = new Viking(M, { ...VIKS[i % VIKS.length], seed: 60 + i, lod: 0.45, bulk: 0.95 + (i % 3) * 0.05 }); v.root.position.set(x, ground(x, z), z); v.root.rotation.y = Math.PI + (x > 0 ? -0.15 : 0.15); scene.add(v.root); crew.push([v, 'viking']); });
  for (const [x, z] of [[-0.6, -12.0], [1.0, -7.5], [-1.8, -1.5], [2.6, -9.6]]) { const r = new Robot(M, env); r.root.position.set(x, ground(x, z), z); r.root.rotation.y = Math.PI; scene.add(r.root); crew.push([r, 'robot']); }
  // ---- the crowd: figures lining the cliff edge as far as the eye goes (instanced silhouettes)
  const body = new THREE.CapsuleGeometry(0.2, 0.75, 3, 8); body.translate(0, 0.6, 0);
  const head = new THREE.SphereGeometry(0.15, 10, 8); head.translate(0, 1.32, 0);
  const merged = mergeGeos([body, head]);
  const crowdM = new THREE.MeshLambertMaterial({ color: 0x2a2630 });
  const R = rng(42); const mats4 = []; const N = 1400; const crowd = new THREE.InstancedMesh(merged, crowdM, N); let n = 0;
  const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), s = new THREE.Vector3(), p = new THREE.Vector3();
  const edgeAt = (x) => { // the cliff edge: walk inland until the ground is high
    for (let dz = -34; dz < -18; dz += 0.25) { const y = ground(x, dz); if (y > -0.6) return dz; } return -28; };
  for (let x = -90; x <= 90 && n < N; x += 0.62) {
    if (Math.abs(x) < 3.2) continue;                         // the ship's bow and him
    const ez = edgeAt(x);
    for (let row = 0; row < 4 && n < N; row++) {
      if (row > 0 && R() < 0.25 * row) continue;
      const z = ez + 1.0 + row * 0.85 + R() * 0.4, xx = x + (R() - 0.5) * 0.4, y = ground(xx, z);
      const sc = 0.92 + R() * 0.18; const yaw = Math.atan2(-xx * 0.02, 1) + (R() - 0.5) * 0.3;
      q.setFromEuler(new THREE.Euler(0, yaw, 0)); s.set(sc, sc * (0.95 + R() * 0.1), sc); p.set(xx, y, z); m4.compose(p, q, s); crowd.setMatrixAt(n++, m4);
    }
  }
  crowd.count = n; crowd.instanceMatrix.needsUpdate = true; crowd.castShadow = false; crowd.receiveShadow = false; scene.add(crowd);
  // ---- the one flash over the sea (the boom), far off to the left of Mars
  const flashT = new THREE.CanvasTexture((() => { const c = document.createElement('canvas'); c.width = c.height = 256; const g = c.getContext('2d'); const gr = g.createRadialGradient(128, 128, 0, 128, 128, 128); gr.addColorStop(0, 'rgba(255,240,220,1)'); gr.addColorStop(0.2, 'rgba(255,200,150,0.5)'); gr.addColorStop(1, 'rgba(0,0,0,0)'); g.fillStyle = gr; g.fillRect(0, 0, 256, 256); return c; })());
  const flash = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.MeshBasicMaterial({ map: flashT, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, fog: false })); flash.renderOrder = -4; scene.add(flash);
  shadows(scene); scene.traverse((o) => { if (o.isMesh && o.material && (o.material.isShaderMaterial || o.material.transparent)) { o.castShadow = false; o.receiveShadow = false; } });
  for (const [c] of crew) c.root.traverse((o) => { if (o.isMesh) o.receiveShadow = false; });
  king.root.traverse((o) => { if (o.isMesh) o.receiveShadow = false; }); bot.root.traverse((o) => { if (o.isMesh) o.receiveShadow = false; });
  crowd.castShadow = false;

  const md = hd.userData.marsDir; const MARS_FAR = (from) => from.clone().addScaledVector(md, 400);
  const manHead = () => king.headWorld();
  // ---------------------------------------------------------------- per frame
  function frame(t, cam) {
    // the man: the rocket on his shoulder (the Fool's bundle); turns his head to us; raises it toward Mars
    const turn = ramp(t, 217.4, 218.2) * (1 - ramp(t, 219.3, 219.9));
    const raise = ramp(t, 219.67, 220.6);
    const lookMars = MARS_FAR(king.root.position.clone().add(V(0, 1.6, 0))).toArray();
    const shoulderHold = [[-0.2, 0.62, -0.12], [0.22, -0.02, 0.06]], aloft = [[-0.22, 1.15, 0.22], [0.22, -0.02, 0.06]];
    king.pose({ seated: false, hands: mixA(shoulderHold, aloft, raise), look: turn > 0.01 ? null : lookMars, lookK: 0.9, headYaw: -1.0 * turn, headPitch: turn > 0.01 ? -0.05 : -0.18 - 0.08 * raise });
    // the rocket in his right hand: over the shoulder, nose up and forward; then held aloft
    king.root.updateMatrixWorld(true);
    const hw = king.handWorld(0); const up = V(0, 1, 0);
    const over = new THREE.Quaternion().setFromEuler(new THREE.Euler(0.95, 0, -0.25, 'YXZ'));   // tilted forward over the shoulder
    const qa = new THREE.Quaternion().slerpQuaternions(over, new THREE.Quaternion(), raise);
    rocket.quaternion.copy(king.root.quaternion).multiply(qa);
    const along = up.clone().applyQuaternion(rocket.quaternion);
    rocket.position.copy(hw).addScaledVector(along, -lerp(0.3, 0.22, raise));
    // the little robot tugs at his heel, then looks up with him
    const tug = Math.sin(t * 7) * 0.02 * (1 - raise);
    bot.pose({ seated: false, hands: [[-0.05, 0.25 + tug, 0.32], [0.2, -0.02, 0.06]], look: raise > 0.2 ? lookMars : manHead().toArray(), lookK: 0.9, lean: 0.1 });
    // everyone else looks up at Mars
    for (const [c, kind] of crew) {
      const L = MARS_FAR(c.root.position.clone().add(V(0, 1.5, 0))).toArray();
      if (kind === 'seer') c.pose({ seated: false, look: L, lookK: 0.9, headPitch: -0.2, hands: [[-0.15, 0.1, 0.3], [0.28, 0.3, 0.2]] });
      else if (kind === 'viking') c.pose({ seated: false, look: L, lookK: 0.9, hands: [[-0.25, 0.0, 0.1], [0.25, 0.0, 0.1]] });
      else c.pose({ seated: false, look: L, lookK: 0.9, hands: [[-0.2, -0.02, 0.06], [0.2, -0.02, 0.06]] });
    }
    se.root.updateMatrixWorld(true); const sw = se.handWorld(1); staff.position.set(sw.x, se.root.position.y, sw.z);
    // the flash
    const fk = decay(t, 224.5, 0.09) + 0.5 * decay(t, 224.62, 0.12) + 0.25 * decay(t, 224.85, 0.3);
    flash.visible = fk > 0.003; const fd = V(Math.sin(-0.4), 0.03, -Math.cos(-0.4)).normalize();
    flash.position.copy(cam.position).addScaledVector(fd, 800); flash.lookAt(cam.position); flash.scale.setScalar(260 * (0.6 + fk)); flash.material.opacity = Math.min(1, fk);
    hd.userData.update(t, cam);
    return fk;
  }
  // ---------------------------------------------------------------- cameras
  const K = king.root.position;
  function cam(name, t) {
    if (name === 'edge') { const u = ramp(t, 212.2, 213.76, (x) => x); return [V(1.55, 1.25, K.z + 4.4).lerp(V(1.45, 1.22, K.z + 4.1), u), V(-0.45, 1.85, K.z - 14), 40]; }
    if (name === 'stars') { const u = ramp(t, 213.76, 216.4, (x) => x); return [V(-3.4, 0.9, 11.5).lerp(V(-3.2, 1.0, 9.5), u), V(0.2, 3.6, -40), 52]; }
    if (name === 'told') { const u = ramp(t, 216.4, 218.8, (x) => x); return [V(1.05, 1.8, K.z + 2.0).lerp(V(0.95, 1.78, K.z + 1.85), u), V(-0.15, 1.45, K.z - 1.5), 36]; }
    if (name === 'turn') { const u = ramp(t, 218.8, 221.04, (x) => x); return [V(0.35, 0.55, K.z + 1.7).lerp(V(0.3, 0.55, K.z + 1.55), u), V(-0.05, 2.0, K.z - 2.0), 40]; }
    if (name === 'asked') { const u = ramp(t, 221.04, 224.1); return [V(0.2, 1.7, K.z + 3.2).lerp(V(0.0, 15.0, 32.0), u), V(0, 1.55, K.z - 6).lerp(V(0, 0.0, -32), u), lerp(36, 46, u)]; }
    if (name === 'how') { const u = ramp(t, 226.64, 227.9, (x) => x); return [V(-0.62, 1.5, K.z - 1.3).lerp(V(-0.6, 1.5, K.z - 1.22), u), V(0.0, 1.62, K.z), 30]; }
    return [V(0, 2, 10), V(0, 1, -30), 40];
  }
  return { scene, hd, king, frame, cam };
}
function mixA(a, b, u) { return a.map((x, i) => Array.isArray(x) ? mixA(x, b[i], u) : x + (b[i] - x) * u); }
function mergeGeos(geos) {
  let n = 0, m = 0; for (const g of geos) { n += g.attributes.position.count; m += g.index.count; }
  const pos = new Float32Array(n * 3), nor = new Float32Array(n * 3), idx = new Uint32Array(m); let o = 0, oi = 0;
  for (const g of geos) { pos.set(g.attributes.position.array, o * 3); nor.set(g.attributes.normal.array, o * 3); const I = g.index.array; for (let i = 0; i < I.length; i++) idx[oi + i] = I[i] + o; o += g.attributes.position.count; oi += I.length; }
  const out = new THREE.BufferGeometry(); out.setAttribute('position', new THREE.BufferAttribute(pos, 3)); out.setAttribute('normal', new THREE.BufferAttribute(nor, 3)); out.setIndex(new THREE.BufferAttribute(idx, 1)); return out;
}
