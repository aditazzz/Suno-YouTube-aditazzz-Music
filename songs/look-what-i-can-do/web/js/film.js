// Look What I Can Do · "Scope Creep" (the 3D sections). renderTime(t) draws the frame at song time t, deterministically.
// Part 1 (0-42.94, the terminal session she approved), the breakdown and the end card are the 2D renders; the modules
// below each cover a stretch of the song: hall.js (chorus 1, ship it, verse 2, qualifications), city.js (chorus 2,
// verse 3), stage.js (the keynote bridge), space.js (final chorus, drop, outro).
import * as THREE from 'three';
import * as L from './lib.js';
import * as M from './media.js';
import * as S from './sets.js';
import { makeLook } from './look.js';

const q = new URLSearchParams(location.search);
const W = +q.get('w') || 1920, H = +q.get('h') || 1080;
const look = makeLook(W, H);
const ctx = { THREE, L, M, S, look, W, H };
const MODS = [];
const blank = new THREE.Scene(); blank.background = new THREE.Color(0x000000); const blankCam = new THREE.PerspectiveCamera(35, W / H, 0.1, 10);

async function build() {
  await L.loadFonts(); await L.loadTiming();
  for (const name of ['hall', 'city', 'stage', 'space']) {
    try { const m = await import(`./${name}.js`); await m.build(ctx); MODS.push([name, m]); console.log('module', name, 'ready'); }
    catch (e) { if (!String(e.message).includes('Failed to fetch dynamically imported module')) console.log('MODULE ERROR', name, e.stack || e.message); }
  }
  window.ready = true;
}
function resetPost() {
  const u = look.finish.uniforms; u.uVel.value.set(0, 0); u.uFlash.value = 0; u.uFlashCol.value.setRGB(1, 1, 1); u.uFade.value = 0; u.uVig.value = 0.32; u.uGrain.value = 0.045; u.uCA.value = 0.0016;
  look.bloom.strength = 0.3; look.bloom.threshold = 0.92; look.bloom.radius = 0.42; look.renderer.toneMappingExposure = 1.0;
}
window.renderTime = async (t) => {
  resetPost(); look.finish.uniforms.uTime.value = t;
  let sc = blank, cam = blankCam;
  for (const [, m] of MODS) if (m.covers(t)) { const r = await m.frame(t, ctx); sc = r.scene; cam = r.camera; break; }
  look.renderPass.scene = sc; look.renderPass.camera = cam;
  await M.update(t);
  look.composer.render();
  return look.renderer.domElement.toDataURL('image/jpeg', 0.93);
};
build().catch((e) => console.log('BUILD ERROR', e.stack || e.message));
