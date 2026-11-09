// S1 footage: her music videos as JPEG sequences (web/media/hd/<key>/NNN.jpg, 30 fps), one shared texture per clip.
// The film declares which clips are on screen each frame (use); update(t) loads exactly the frame for time t.
import * as THREE from 'three';
import { KEYS } from './keys.js';

// Asking for a Friend's clips are 6 s montages with cuts, so they're used as named shots: [source clip, first, last frame
// (1-based, inclusive, between its cuts), 'pp' = ping-pong instead of loop]. The GT3 RS shots all show the yellow calipers.
export const VIRT = {
  claude_eyes: ['aff_robot_eyes', 46, 65, 'pp'], claude_button: ['aff_robot_button', 22, 78], claude_memo: ['aff_robot_memo', 37, 97],
  gt3_desert: ['aff_porsche_desert', 31, 71], gt3_house: ['aff_porsche_house', 31, 95], gt3_plate: ['aff_porsche_house', 144, 180],
  gt3_side: ['aff_porsche_side', 69, 117], gt3_wheel: ['aff_porsche_side', 36, 68], gt3_night: ['aff_porsche_front', 40, 65],
  aff_green: ['aff_systems_green', 31, 85], aff_tiles: ['aff_customers', 19, 80],
};
const src = (k) => (VIRT[k] ? VIRT[k][0] : k);
// clips good as virtual backgrounds: in the folder, not blown out (white share and peak brightness from make_keys.py);
// raw montages (aff_*) only through their named shots
export const okKey = (k) => { const b = src(k); return !!KEYS[b] && (!!VIRT[k] || (!b.startsWith('aff_') && KEYS[b].white < 0.08 && KEYS[b].lumMax < 0.62 && KEYS[b].lum > 0.1)); };
// the order she'd want them seen in: the newest worlds first, each video's best moments, then anything else that's arrived
const PREF = ['ph_ring', 'bl_grid2', 'rage_said_no', 'ts_host', 'ph_neon_plaza', 'bl_pinkcubes', 'ph_please_neon', 'rage_optout',
  'bl_cube', 'ph_stars', 'ts_bingo', 'bl_laser', 'ph_onhold_night', 'rage_metal', 'bl_tunnel', 'ph_dusk_city', 'ts_circling', 'bl_2200',
  'rage_metal2', 'bl_city', 'bl_grid', 'ph_battery'];
export function clipList() {
  const a = PREF.filter(okKey); for (const k of [...Object.keys(KEYS), 'aff_green', 'aff_tiles']) if (!a.includes(k) && okKey(k)) a.push(k);
  return a;
}

const tex = {}, cur = {}, used = new Set();
export function texOf(k) {
  if (tex[k]) return tex[k];
  const t = new THREE.Texture(); t.colorSpace = THREE.SRGBColorSpace; t.generateMipmaps = true; t.minFilter = THREE.LinearMipmapLinearFilter;
  t.magFilter = THREE.LinearFilter; t.anisotropy = 2; tex[k] = t; cur[k] = -1; return t;
}
export function use(k) { if (k) used.add(k); }
function loadImg(url) { return new Promise((res, rej) => { const im = new Image(); im.onload = () => res(im); im.onerror = () => rej(new Error('img ' + url)); im.src = url; }); }
// each clip starts at its own offset (so neighbours never show the same frame) and loops
export const offsetOf = (k) => { let h = 0; for (const c of k) h = (h * 31 + c.charCodeAt(0)) >>> 0; return (h % 1000) / 1000; };
export async function update(t) {
  const jobs = [];
  for (const k of used) {
    const b = src(k), N = KEYS[b] ? KEYS[b].n : 0; if (!N) continue;
    const [lo, hi, mode] = VIRT[k] ? [VIRT[k][1] - 1, Math.min(N, VIRT[k][2]) - 1, VIRT[k][3]] : [0, N - 1, null]; const n = hi - lo + 1;
    let f = Math.floor(((t * 30 + offsetOf(k) * n) % (mode === 'pp' ? 2 * n - 2 : n) + 4 * n) % (mode === 'pp' ? 2 * n - 2 : n));
    if (mode === 'pp' && f >= n) f = 2 * n - 2 - f;
    const idx = lo + f;
    if (idx === cur[k]) continue; cur[k] = idx; const T = texOf(k);
    jobs.push(loadImg(`/media/hd/${b}/${String(idx + 1).padStart(3, '0')}.jpg`).then((im) => { T.image = im; T.needsUpdate = true; }).catch(() => {}));
  }
  used.clear(); await Promise.all(jobs);
}
const stat = {};
export async function image(path) {
  if (stat[path]) return stat[path];
  const im = await loadImg(path); const t = new THREE.Texture(im); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4; t.needsUpdate = true;
  t.userData.w = im.naturalWidth; t.userData.h = im.naturalHeight; stat[path] = t; return t;
}
