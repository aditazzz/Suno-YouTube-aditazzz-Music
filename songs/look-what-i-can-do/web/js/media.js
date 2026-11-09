// Her footage as textures: clip atlases (16 clips per texture, 15 fps loops) and hero sequences (30 fps), loaded frame by frame
import * as THREE from 'three';

const PAD = 2;
export const ATLAS = {
  H1: { cols: 4, rows: 4, cw: 480, ch: 270, n: 120, fps: 15 }, H2: { cols: 4, rows: 4, cw: 480, ch: 270, n: 120, fps: 15 },
  V1: { cols: 8, rows: 2, cw: 270, ch: 480, n: 120, fps: 15 }, V2: { cols: 8, rows: 2, cw: 270, ch: 480, n: 120, fps: 15 },
};
export const HERO = { ted0: 240, tedcharts: 240, tedshadow: 240, tedscreen: 240, tedstep: 240, rage: 240, blocker: 240, phone: 393 };
// the clips in each atlas cell (for labels)
export const NAMES = {
  H1: ['ai_sycophant', 'asking_for_a_friend', 'deployed_on_a_friday', 'fangs_for_asking', 'i_have_a_blocker', 'rage_against_the_ml', 'snowflake_undrop', 'spinning_cursor', 'take_it_offline', 'ted_talk_screenlife', 'ted_talk', 'the_promptress', 'thirsty', 'vacation_to_my_bed', 'deployed_fable', 'allow'],
  H2: ['ai_sycophant_2', 'asking_for_a_friend_2', 'deployed_2', 'fangs_2', 'blocker_3d', 'rage_2', 'undrop_2', 'cursor_2', 'take_it_offline_2', 'screenlife_2', 'ted_talk_2', 'promptress_2', 'thirsty_2', 'vacation_2', 'deployed_fable_2', 'sycophant_3'],
  V1: ['ai_slop_city', 'sycophant_fable', 'autocomplete', 'eleven_kept_going', 'git_blame_country', 'git_blame', 'graceful_shutdown', 'great_idea_ted', 'mirror_comments', 'mirror_vanity', 'omg_swarm', 'omg_in_the_walls', 'please_hold', 'ragnarok', 'rate_limited', 'tech_debt'],
  V2: ['ai_slop_city_2', 'sycophant_fable_2', 'autocomplete_2', 'eleven_2', 'git_blame_country_2', 'git_blame_2', 'graceful_2', 'great_idea_ted_2', 'mirror_comments_2', 'mirror_vanity_2', 'swarm_2', 'walls_2', 'please_hold_2', 'ragnarok_2', 'rate_limited_2', 'tech_debt_2'],
};

const tex = {};      // name -> THREE.Texture (shared by every material that shows it)
const cur = {};      // name -> loaded frame index
const used = new Set();
function mk(name) {
  const t = new THREE.Texture(); t.colorSpace = THREE.SRGBColorSpace; t.generateMipmaps = true; t.minFilter = THREE.LinearMipmapLinearFilter;
  t.magFilter = THREE.LinearFilter; t.anisotropy = 8; tex[name] = t; cur[name] = -1; return t;
}
export function texOf(name) { return tex[name] || mk(name); }
export function use(...names) { names.forEach((n) => used.add(n)); }

function loadImg(url) { return new Promise((res, rej) => { const im = new Image(); im.onload = () => res(im); im.onerror = () => rej(new Error('img ' + url)); im.src = url; }); }

// call once per frame after the film has declared what it shows (use(...)); every used texture gets its frame for time t
export async function update(t) {
  const jobs = [];
  for (const name of used) {
    const A = ATLAS[name]; const n = A ? A.n : HERO[name]; const fps = A ? A.fps : 30;
    if (!n) continue;
    const off = name.length * 0.37;                                     // de-sync the loops a little
    const idx = Math.floor(((t + off) * fps) % n + n) % n;
    if (idx === cur[name]) continue;
    cur[name] = idx;
    const t_ = texOf(name);
    jobs.push(loadImg(`/media/${name}/${String(idx + 1).padStart(3, '0')}.jpg`).then((im) => { t_.image = im; t_.needsUpdate = true; }));
  }
  used.clear();
  await Promise.all(jobs);
}

// UV rect of one clip inside an atlas, with a thin black border kept as the bezel
export function cellRect(name, i, border = 1) {
  const A = ATLAS[name]; const W = A.cols * (A.cw + 2 * PAD), H = A.rows * (A.ch + 2 * PAD);
  const c = i % A.cols, r = Math.floor(i / A.cols) % A.rows;
  const x = c * (A.cw + 2 * PAD) + PAD - border, y = r * (A.ch + 2 * PAD) + PAD - border, w = A.cw + 2 * border, h = A.ch + 2 * border;
  return [x / W, 1 - (y + h) / H, w / W, h / H];
}
export function aspectOf(name) { const A = ATLAS[name]; return A ? A.cw / A.ch : (name === 'phone' ? 540 / 1106 : 16 / 9); }

// a plane geometry showing one atlas cell (UVs baked in)
export function cellGeo(w, h, name, i) {
  const g = new THREE.PlaneGeometry(w, h); const [ox, oy, sx, sy] = cellRect(name, i);
  const uv = g.attributes.uv; for (let k = 0; k < uv.count; k++) uv.setXY(k, ox + uv.getX(k) * sx, oy + uv.getY(k) * sy);
  return g;
}

// static images (her posts, profile) as textures
const stat = {};
export async function image(name) {
  if (stat[name]) return stat[name];
  const im = await loadImg(`/media/${name}`); const t = new THREE.Texture(im); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8; t.needsUpdate = true;
  t.userData.w = im.naturalWidth; t.userData.h = im.naturalHeight; stat[name] = t; return t;
}
