// The film from the second HEY of hook 1 (0:27.49) to the end. film.js keeps the approved preview (0:00–0:27.49)
// exactly as rendered and hands every later frame to frameFull(t), which poses everyone, lays out the cards, sets
// the light and picks the camera. Sections follow the song: hook · verse 1 (Tower, Sun) · hook · refrain ·
// verse 2 (Robot, Red Planet, Gardener, Fool) · hook (the robots take over) · bridge · refrain · hook · outro
// (the headland) · coda.
import * as THREE from 'three';
import { clamp, lerp, sstep, easeIO, easeOut, easeIn } from './lib.js';
import { HALL } from './hall.js';
import { CARD } from './cards.js';

let X = null, T = null, K = null;
const V = (x, y, z) => new THREE.Vector3(x, y, z);
const TZ = HALL.table.z, TOPY = HALL.table.top + 0.0013, F = HALL.feast;
const qOf = (rx, ry, rz, order = 'YXZ') => new THREE.Quaternion().setFromEuler(new THREE.Euler(rx, ry, rz, order));
const FACE_DOWN = (yaw = Math.PI) => qOf(Math.PI / 2, yaw, 0);
const Y_AX = V(0, 1, 0);
/** turning a card over about its long axis: u = 0 face down, 1 face up (top toward the seeress, readable from his side) */
const flipQ = (u, yaw = Math.PI, dir = 1) => FACE_DOWN(yaw).multiply(new THREE.Quaternion().setFromAxisAngle(Y_AX, dir * Math.PI * u));
const FACE_UP = (yaw = Math.PI) => flipQ(1, yaw);
const UPRIGHT = (yaw = 0, tilt = 0) => qOf(tilt, yaw, 0);
function place(card, p, q) { card.position.copy(p); card.quaternion.copy(q); card.visible = true; }
function track(keys, t) {
  if (t <= keys[0][0]) return keys[0][1];
  for (let i = 1; i < keys.length; i++) { const [t1, v1, e] = keys[i]; if (t < t1) { const [t0, v0] = keys[i - 1]; const u = (e || easeIO)((t - t0) / (t1 - t0)); return mixV(v0, v1, u); } }
  return keys[keys.length - 1][1];
}
function mixV(a, b, u) { if (Array.isArray(a)) return a.map((x, i) => mixV(x, b[i], u)); if (a === null || b === null || typeof a !== 'number') return u < 0.5 ? a : b; return a + (b - a) * u; }
const lin = (x) => clamp(x);
const step2 = (t) => Math.floor(t * 15 + 1e-6) / 15;
const decay = (t, t0, tau) => t < t0 ? 0 : Math.exp(-(t - t0) / tau);
const win = (t, a, b) => t >= a && t < b;
const ramp = (t, a, b, e = easeIO) => e(clamp((t - a) / (b - a)));
const pulse = (t, a, b, fi = 0.25, fo = 0.25) => sstep(a - fi, a, t) * (1 - sstep(b, b + fo, t));
const toV = (a) => (a.isVector3 ? a : V(...a));

// the table: where cards go
const SPOT = { L: V(-0.12, TOPY, -5.9), R: V(0.12, TOPY, -5.9), C: V(0, TOPY, TZ + 0.04), deck: V(-0.25, TOPY, TZ - 0.17), place: V(0, TOPY, -5.6) };
const SEER_REST = { R: [-0.17, 0.66, -6.42], L: [0.17, 0.66, -6.42] };
const MAN_REST = [0.22, 0.79, -5.68], ON_ROCKET = [-0.36, 0.62, HALL.stool.z + 0.02];
const BEAT = 60 / 105.47;

// ---------------------------------------------------------------- set-up
export function initFull(ctx) {
  X = ctx; T = ctx.T;
  const w = (i, j) => T.lines[i].t[j];
  const hook = (li, hi, ci, start, end) => ({ li, start, end, shuf1: w(li, 0), shuf2: w(li + 1, 0), hey: T.heys.slice(hi, hi + 4), turn: w(li + 2, 0), one: w(li + 2, 1), over: w(li + 2, 2),
    place: w(li + 2, 3), your: w(li + 2, 4), bets: w(li + 2, 5), betsEnd: T.lines[li + 2].end, cast1: w(li + 3, 0), cast2: w(li + 4, 0), rag: T.cards[ci].t, reachW: w(li + 5, 1), mars: T.cards[ci + 1].t });
  K = { hooks: [hook(3, 0, 0, 22.6, 42.34), hook(19, 4, 4, 69.6, 88.6), hook(37, 8, 10, 133.2, 151.5), hook(58, 12, 16, 187.5, 207.2)] };
  K.sections = [['hook', 27.487, 42.34, 0], ['v1', 42.34, 69.6], ['hook', 69.6, 88.6, 1], ['ref', 88.6, 96.45, 0], ['v2', 96.45, 133.2], ['hook', 133.2, 151.5, 2],
    ['bridge', 151.5, 169.5], ['ref', 169.5, 187.5, 1], ['hook', 187.5, 207.2, 3], ['outro', 207.2, 227.9], ['coda', 227.9, 1e9]];
  K.shots = buildShots();
}
function sectionAt(t) { for (const s of K.sections) if (t >= s[1] && t < s[2]) return s; return K.sections[K.sections.length - 1]; }

// ---------------------------------------------------------------- defaults every frame
function reset(t) {
  const { hall, pops } = X;
  for (const c of X.loose) { c.visible = false; c.scale.setScalar(1); } for (const c of X.deck) c.scale.setScalar(1);
  for (const p of Object.values(pops)) { p.setOpen(0); }
  X.popL.intensity = 0; X.aux.intensity = 0; X.aux.userData.owner = null; X.shaft.visible = false;
  if ((t >= 42.3 && t < 44.63) || (t >= 128.9 && t < 131.2)) { X.rocketL.intensity = 0.9; X.aux.position.set(-0.8, 0.95, -5.62); }
  const ctl = hall.userData.ctl; ctl.torch = [1, 1, 1, 1]; ctl.stand = 1; ctl.candle = 1; ctl.fill = 1; ctl.moon = 1;
  hall.userData.fire.userData.level = 1;
  X.hemi.color.setRGB(0.23, 0.29, 0.42); X.hemi.groundColor.setHex(0x1a0e08); X.hemiK = 0.18;
  X.man.root.visible = true; X.man.setFace('smile'); X.seer.setFace('open');
  X.tf.visible = true; place(X.tf, SPOT.place, FACE_DOWN(0.04 + Math.PI)); X.tf.userData.setFlip(0); X.tf.userData.setFool(0); X.tf.userData.setGlow(new THREE.Color(1, 0.7, 0.3), 0);
  X.tf.userData.front.material.userData.u.mapC.value = X.foolTex;
  for (const r of X.robots) r.root.visible = t >= ROBOTS_IN; X.attendant.root.visible = t >= 128.0 && t < 133.2;
  X.deckGlow(0);
  X.vortexPt.visible = false; X.spark.visible = false; X.handDouble.visible = false; X.burin.visible = false; X.candleB.visible = false; X.tomatoHeld.visible = false; X.tomatoGift.visible = false;
  X.plant.visible = false; X.label.visible = false; X.coin.visible = false; for (const s of X.silvers) s.visible = false;
  X.endPlate.visible = false; X.scenes.cur = X.scene;
  X.finish.uFlash = 0; X.finish.uFade = 1; X.finish.flashCol.setRGB(0.75, 0.85, 1.0);
  X.freeze = null;
}
const ROBOTS_IN = 101.6;

// ---------------------------------------------------------------- the deck (backs only), stacked, held, shuffled
function deckStackAt(p, n = 22, yaw = 0) { for (let i = 0; i < n; i++) place(X.deck[i], V(p.x, p.y + i * 0.0017, p.z), FACE_DOWN(yaw + 0.04 * Math.sin(i * 7))); for (let i = n; i < 22; i++) X.deck[i].visible = false; }
const HANDS_MID = [V(0.13, 1.07, -6.35), V(-0.13, 1.07, -6.35)];
function springPos(tt, t0, dir, hands, i, n = 22, gap = 0.034, fly = 0.22) {
  const from = dir > 0 ? hands[0] : hands[1], to = dir > 0 ? hands[1] : hands[0];
  const ts = t0 + i * gap; const u = clamp((tt - ts) / fly);
  if (u <= 0) return { p: from.clone().add(V(0, (n - i) * 0.0016, 0)), q: qOf(Math.PI / 2 - 0.25 * dir, 0, 0.12 * dir) };
  if (u >= 1) return { p: to.clone().add(V(0, i * 0.0016, 0)), q: qOf(Math.PI / 2 + 0.25 * dir, 0, -0.12 * dir) };
  const e = easeIO(u); const p = from.clone().lerp(to, e); p.z += Math.sin(Math.PI * e) * 0.06; p.y += Math.sin(Math.PI * e) * 0.16 + (1 - e) * (n - i) * 0.0016 + e * i * 0.0016;
  return { p, q: qOf(Math.PI / 2 - 0.25 * dir + 0.5 * dir * e, 0, 0.12 * dir - 0.24 * dir * e + Math.sin(Math.PI * e) * 0.35 * dir) };
}
/** the shuffle that opens hooks 2–4: lift the deck from the table, two spring shuffles (same as the preview's) */
function shuffleDeck(t, e) {
  const lift = ramp(t, e.shuf1 + 0.02, e.shuf1 + 0.24);
  for (let k = 0; k < 22; k++) {
    const s1 = springPos(t, e.shuf1 + 0.29, 1, HANDS_MID, k), s2 = springPos(t, e.shuf2 + 0.04, -1, HANDS_MID, k);
    let p, q;
    if (t < e.shuf1 + 0.29) { p = V(SPOT.deck.x, TOPY + k * 0.0017, SPOT.deck.z).lerp(HANDS_MID[0].clone().add(V(0, (22 - k) * 0.0016, 0)), lift); q = FACE_DOWN(0); }
    else if (t < e.shuf2 + 0.04) { p = s1.p; q = s1.q; } else { p = s2.p; q = s2.q; }
    place(X.deck[k], p, q);
  }
}
/** the deck in her right hand (after the shuffle), top card index 21 */
function deckInHand(hand, n = 22, tilt = 0) { const q = qOf(Math.PI / 2 + tilt, 0, 0); for (let i = 0; i < 22; i++) { if (i >= n) { X.deck[i].visible = false; continue; } place(X.deck[i], hand.clone().add(V(0, i * 0.0016 - 0.012, 0.01)), q); } }

// ---------------------------------------------------------------- puppets
function seer(p) { X.seer.pose({ lean: 0.12, headPitch: 0.1, look: [0, 1.25, HALL.stool.z], lookK: 0.75, handsW: [SEER_REST.R, SEER_REST.L], ...p }); }
function man(p) { X.man.pose({ lean: 0.12, headPitch: 0.05, look: [0, 1.06, -6.2], lookK: 0.85, handsW: [MAN_REST, ON_ROCKET], ...p }); }
function handTip(pup, k, d = 0.045) { pup.root.updateMatrixWorld(true); return pup.arms[k].hand.localToWorld(V(0, d, 0)); }
/** Vikings. mode: listen | idle | rocket | laugh | lounge | crossed | cheer | dark; slams on the HEYs and stomps unless noSlam */
function viking(v, t, o = {}) {
  const s = v.userData.seat, side = s.side, tx = side * (F.x + 0.2);
  const mode = o.mode || 'listen'; const lagged = mode === 'laugh' ? t : t + v.userData.lag;
  const near = !o.noSlam && T.stomps.concat(T.heys).some((e) => Math.abs(t - e) < 0.6);
  const ts = (near || o.live) ? t : step2(lagged);
  const readLook = o.look || [0, 1.15, -6.1];
  let look = readLook, lean = 0.21, hands = null, handsW = null, headPitch = 0, headRoll = 0.04 * Math.sin(v.userData.ph * 3);
  // the table hands, and the HEY / stomp drumming
  let lift = 0; if (!o.noSlam) for (const e of T.stomps) lift = Math.max(lift, (ts > e - 0.26 && ts < e) ? Math.sin(Math.PI * (ts - (e - 0.26)) / 0.26) * 0.2 : 0);
  let raise = 0; if (!o.noSlam) for (const e of (o.heys || T.heys)) { const ee = e + (o.late || 0); if (ts >= ee - 0.5 && ts < ee) raise = Math.max(raise, easeOut((ts - (ee - 0.5)) / 0.42)); }
  const y = F.top + 0.03 + lift + raise * 0.42; const z = raise * 0.12;
  handsW = [[tx + side * z, y, s.z + 0.17], [tx + side * z, y, s.z - 0.17]];
  if (mode === 'idle') { look = [side * 0.5 + 0.0, 1.0 + 0.15 * Math.sin(v.userData.ph), s.z + v.userData.yaw0 * 2.5]; lean = 0.05 - 0.05 * Math.sin(ts * 1.3 + v.userData.ph); }
  if (mode === 'rocket') { look = [-0.43, 0.6, HALL.stool.z + 0.04]; lean = 0.12; }
  if (mode === 'laugh') { const b = Math.max(0, Math.sin(Math.PI * ((t - (o.t0 || 0)) / BEAT % 1))); lean = -0.14 + 0.16 * b; headPitch = -0.32 + 0.12 * b; look = null;
    handsW = [[tx - side * 0.12, F.top + 0.12 + 0.03 * b, s.z + 0.12], [tx - side * 0.12, F.top + 0.12 + 0.03 * b, s.z - 0.12]]; }
  if (mode === 'lounge') { lean = -0.2; hands = [[-0.17, 0.8, -0.1], [0.17, 0.8, -0.1]]; handsW = null; look = null; headPitch = -0.12; }
  if (mode === 'crossed') { lean = -0.04; hands = [[0.13, 0.35, 0.21], [-0.13, 0.32, 0.23]]; handsW = null; }
  if (mode === 'cheer') { const b = Math.max(0, Math.sin(Math.PI * ((t - (o.t0 || 0)) / BEAT % 1))); lean = -0.08; hands = [[-0.3, 0.98 + 0.05 * b, 0.18], [0.3, 0.98 + 0.05 * b, 0.18]]; handsW = null; headPitch = -0.25; look = null; }
  if (mode === 'still') { lean = 0.12; }
  if (o.slap !== undefined && !o.noSlap) {   // placing a bet: one hand comes down with a piece of silver
    const ta = o.slap; const u = clamp((ts - (ta - 0.32)) / 0.32); const up = ts < ta - 0.32 ? 0 : ts < ta ? Math.sin(u * Math.PI * 0.5) : 0;
    const sx = side * (F.x + 0.06), sz = s.z + 0.1; handsW = handsW || [[tx, F.top + 0.03, s.z + 0.17], [tx, F.top + 0.03, s.z - 0.17]];
    handsW[0] = [sx, F.top + 0.035 + 0.22 * up, sz]; }
  if (o.lookOverride) look = o.lookOverride;
  v.pose({ lean: lean + (o.leanAdd || 0), handsW: hands ? null : handsW, hands, look, lookK: look ? 0.85 : 0, headPitch, headRoll });
}
function vikings(t, o = {}) { X.vikings.forEach((v, i) => viking(v, t, typeof o === 'function' ? o(v, i) : o)); }
/** robots at the feast tables (facing the Vikings across the table). mode: stand | row | slam | serve */
function robot(r, t, o = {}) {
  const { side, z } = r.userData; const ix = side * (F.x - 0.2);
  let handsW = [[ix, F.top + 0.03, z + 0.14], [ix, F.top + 0.03, z - 0.14]], hands = null, lean = 0.08, look = [side * 2.3, 1.2, z];
  const mode = o.mode || 'stand';
  if (mode === 'stand') { hands = [[-0.2, -0.02, 0.06], [0.2, -0.02, 0.06]]; handsW = null; lean = 0; }
  if (mode === 'row') { const c = Math.sin((t - 101.68) / (2 * BEAT) * Math.PI * 2); const reach = 0.5 + 0.5 * c;
    const x = side * (1.12 + 0.18 + 0.2 * reach), y = 0.9 + 0.05 * (1 - reach); handsW = [[x, y, z + 0.16], [x, y, z - 0.16]]; lean = 0.25 * reach - 0.05; }
  if (mode === 'slam') { const ts = t; let raise = 0; for (const e of (o.heys || T.heys)) { if (ts >= e - 0.5 && ts < e) raise = Math.max(raise, easeOut((ts - (e - 0.5)) / 0.42)); }
    let lift = 0; for (const e of T.stomps) lift = Math.max(lift, (ts > e - 0.26 && ts < e) ? Math.sin(Math.PI * (ts - (e - 0.26)) / 0.26) * 0.2 : 0);
    const y = F.top + 0.03 + raise * 0.45 + lift; handsW = [[ix - side * raise * 0.1, y, z + 0.14], [ix - side * raise * 0.1, y, z - 0.14]]; lean = 0.15 + 0.1 * raise; }
  if (o.slap !== undefined) { const ta = o.slap; const u = clamp((t - (ta - 0.32)) / 0.32); const up = t < ta - 0.32 ? 0 : t < ta ? Math.sin(u * Math.PI * 0.5) : 0;
    hands = null; handsW = handsW || [[ix, F.top + 0.03, z + 0.14], [ix, F.top + 0.03, z - 0.14]]; handsW[0] = [side * (F.x - 0.05), F.top + 0.035 + 0.22 * up, z + 0.1]; lean = 0.3; }
  if (o.look) look = o.look;
  r.pose({ seated: false, lean, handsW, hands, look, lookK: 0.8, headPitch: o.headPitch || 0 });
}
function robotsAll(t, o = {}) { X.robots.forEach((r, i) => robot(r, t, typeof o === 'function' ? o(r, i) : o)); }

// ---------------------------------------------------------------- light
function hallLight(t, { fire = 1, torches = 1, stands = 1, candles = 1, fill = 1, hemi = null, hemiK = 0.18 } = {}) {
  const ctl = X.hall.userData.ctl; ctl.torch = Array.isArray(torches) ? torches : [torches, torches, torches, torches]; ctl.stand = stands; ctl.candle = candles; ctl.fill = fill;
  X.hall.userData.fire.userData.level = fire; if (hemi) X.hemi.color.copy(hemi); X.hemiK = hemiK;
}
function popLight(col, k, p = null) { X.popL.color.copy(col); X.popL.intensity = k; X.popL.position.copy(p || V(0, 1.02, TZ + 0.16)); }

// ================================================================ HOOKS
// hook h: [shuffle, HEY, shuffle, HEY] (from the preview for hook 1), then: she deals two cards face down; the hall
// slaps silver on the tables ("place your bets"), he puts his one coin by the right-hand card; "Cast the cards!" twice
// with a slam on each HEY; the left card turns itself over (RAGNARÖK); he reaches for the right one and turns it (MARS).
// Hook 3 (h = 2): the robots do the shuffling slams and the bets while the Vikings sit with their arms crossed; one
// Viking slams anyway, late, on the last HEY. Hook 4 (h = 3): everyone slams.
function hookFrame(t, h) {
  const e = K.hooks[h]; const robotsOn = h >= 2;
  const dealL = [e.turn - 0.06, e.turn + 0.34], dealR = [e.one + 0.08, e.over + 0.02];
  const deckDown = [e.over + 0.12, e.over + 0.55];
  // ---- the seeress
  let hr = SEER_REST.R, hl = SEER_REST.L, lean = 0.12, look = [0, 1.25, HALL.stool.z];
  const shuffling = t < e.hey[1] + 0.35;
  if (shuffling) { if (h === 0) { hr = [-0.13, 1.06, -6.38]; hl = [0.13, 1.06, -6.38]; }
    else { const u = ramp(t, e.shuf1 + 0.02, e.shuf1 + 0.22); hr = mixV([-0.25, 0.8, -6.1], [-0.13, 1.06, -6.38], u); hl = mixV([0.05, 0.8, -6.1], [0.13, 1.06, -6.38], u); look = [0, 1.06, -6.38]; } }
  else if (t < deckDown[1] + 0.3) {
    // the deck in her left hand; the right hand deals
    hl = track([[e.hey[1] + 0.35, [0.13, 1.06, -6.38]], [e.turn - 0.3, [0.1, 0.86, -6.18]], [deckDown[0], [0.1, 0.86, -6.18]], [deckDown[1], [-0.2, 0.8, -6.12]], [deckDown[1] + 0.3, SEER_REST.L]], t);
    hr = track([[e.hey[1] + 0.35, [-0.13, 1.06, -6.38]], [e.turn - 0.3, [0.06, 0.88, -6.16]], [dealL[0], [0.06, 0.88, -6.16]], [dealL[1] - 0.06, [SPOT.L.x, 0.79, SPOT.L.z - 0.1]], [dealR[0] - 0.05, [0.06, 0.88, -6.16]],
      [dealR[1] - 0.06, [SPOT.R.x, 0.79, SPOT.R.z - 0.1]], [deckDown[1], [-0.1, 0.8, -6.2]], [deckDown[1] + 0.3, SEER_REST.R]], t);
    lean = track([[e.turn - 0.4, 0.12], [dealL[0], 0.42], [dealR[1], 0.42], [deckDown[1] + 0.3, 0.14]], t); look = [0, 0.78, SPOT.L.z];
  } else if (t >= e.cast1 - 0.15 && t < e.rag + 0.4) {
    // "Cast the cards!": both palms sweep out over the two cards and press down on each HEY
    const press = Math.max(...e.hey.slice(2).map((x) => (t >= x - 0.2 && t < x + 0.15) ? Math.sin(Math.PI * (t - (x - 0.2)) / 0.35) : 0));
    const up = ramp(t, e.cast1 - 0.15, e.cast1 + 0.25);
    hr = mixV(SEER_REST.R, [SPOT.L.x - 0.02, 0.9 - 0.05 * press, SPOT.L.z - 0.14], up); hl = mixV(SEER_REST.L, [SPOT.R.x + 0.02, 0.9 - 0.05 * press, SPOT.R.z - 0.14], up);
    if (t > e.rag - 0.5) { const d = ramp(t, e.rag - 0.5, e.rag + 0.3); hr = mixV(hr, SEER_REST.R, d); hl = mixV(hl, SEER_REST.L, d); }
    lean = 0.3 + 0.08 * press; look = [0, 1.2, HALL.stool.z];
  } else if (t >= e.rag - 0.4) look = t < e.reachW ? [SPOT.L.x, 0.78, SPOT.L.z] : [0, 1.25, HALL.stool.z];
  const ts = (shuffling || (t > e.turn - 0.4 && t < deckDown[1] + 0.3) || (t > e.cast1 - 0.2 && t < e.hey[3] + 0.3)) ? t : step2(t);
  seer({ handsW: [hr, hl], lean, look, lookK: 0.8 });
  // ---- the man
  const coinT = [e.bets + 0.35, e.bets + 1.0];
  let mr = track([[0, MAN_REST], [coinT[0] - 0.35, MAN_REST], [coinT[0], [0.2, 0.79, SPOT.R.z + 0.12]], [coinT[1], [SPOT.R.x + 0.08, 0.785, SPOT.R.z + 0.03]], [coinT[1] + 0.4, MAN_REST],
    [e.reachW - 0.25, MAN_REST], [e.reachW + 0.55, [SPOT.R.x + 0.03, 0.84, SPOT.R.z + 0.08]], [e.mars - 0.36, [SPOT.R.x + 0.05, 0.84, SPOT.R.z + 0.06]], [e.mars - 0.05, [SPOT.R.x - 0.03, 0.83, SPOT.R.z + 0.02]], [e.mars + 0.6, MAN_REST]], ts);
  let mlook = t < e.turn - 0.3 ? [0, 1.06, -6.38] : t < e.mars + 0.6 ? [0.0, 0.78, TZ + 0.1] : [0, 1.3, HALL.seat.z];
  if (t >= e.rag - 0.3 && t < e.reachW - 0.3) mlook = [SPOT.L.x, 0.78, SPOT.L.z];
  man({ handsW: [mr, ON_ROCKET], look: mlook, lean: t > e.reachW - 0.3 && t < e.mars + 0.4 ? 0.3 : 0.14 });
  // ---- the hall: slams, bets
  const slapAt = (i) => [e.place, e.your, e.bets][i % 3];
  if (h === 2) {
    vikings(t, (v, i) => ({ mode: i === 3 && t > e.hey[3] - 0.9 ? 'listen' : 'crossed', noSlam: i !== 3, heys: [e.hey[3]], late: 0.32, look: [0, 1.0, -5.9] }));
    robotsAll(t, (r, i) => ({ mode: 'slam', heys: e.hey, ...(t > e.place - 0.6 && t < e.bets + 0.4 ? { slap: slapAt(i) } : {}) }));
  } else {
    vikings(t, (v, i) => ({ mode: 'listen', look: t < e.turn ? [0, 1.06, -6.38] : [0, 0.95, TZ], ...(t > e.place - 0.6 && t < e.bets + 0.4 ? { slap: slapAt(i) } : {}) }));
    if (robotsOn) robotsAll(t, { mode: 'slam', heys: e.hey }); else if (t >= ROBOTS_IN) robotsAll(t, { mode: 'stand' });
  }
  // the silver on the tables: each piece appears when its hand comes down
  X.silvers.forEach((s, i) => { const v = X.vikings[i]; const seat = v.userData.seat;
    if (h === 2) { const ri = X.robots.findIndex((r) => r.userData.side === seat.side && Math.abs(r.userData.z - seat.z) < 0.01); if (ri < 0) { s.visible = false; return; }
      const ta = slapAt(ri); s.visible = t >= ta && t < e.end; s.position.set(seat.side * (F.x - 0.05), F.top, seat.z + 0.1); return; }
    const ta = slapAt(i); s.visible = t >= ta && t < e.end; s.position.set(seat.side * (F.x + 0.06), F.top, seat.z + 0.1); });
  // ---- the cards
  if (h > 0 && t < e.hey[1] + 0.35) shuffleDeck(t, e);
  else {
    const hand = handTip(X.seer, 1, 0.05);
    if (t < deckDown[0]) deckInHand(hand, 20);
    else if (t < deckDown[1]) { const u = ramp(t, deckDown[0], deckDown[1]); const p = hand.clone().lerp(SPOT.deck, u); for (let i = 0; i < 20; i++) place(X.deck[i], p.clone().add(V(0, i * 0.0017, 0)), FACE_DOWN(0)); for (let i = 20; i < 22; i++) X.deck[i].visible = false; }
    else deckStackAt(SPOT.deck, 20);
  }
  // the two cards: dealt from the top of the deck, face down, then turned
  const R = X.ragC, Mc = X.marsC; const hr2 = handTip(X.seer, 0, 0.05);
  const dealt = (c, d, spot, flipT, flipBy) => {
    if (t < d[0]) { c.visible = false; return; }
    if (t < d[1]) { const u = ramp(t, d[0], d[1]); const p = hr2.clone().lerp(spot, easeIn(u)); p.y = lerp(hr2.y - 0.01, spot.y, easeIn(u)) + 0.02 * Math.sin(Math.PI * u); place(c, p, FACE_DOWN(Math.PI + 0.3 * (1 - u))); return; }
    // jumps on the HEYs
    const jump = e.hey.slice(2).reduce((a, x) => a + (t >= x && t < x + 0.3 ? Math.sin(Math.PI * (t - x) / 0.3) * 0.022 : 0), 0);
    const fu = ramp(t, flipT, flipT + 0.3, easeIO);
    const p = spot.clone(); p.y += jump + (flipBy === 'self' ? 0.07 * Math.sin(Math.PI * fu) : 0.035 * Math.sin(Math.PI * fu));
    place(c, p, flipQ(fu, Math.PI, flipBy === 'self' ? 1 : -1));
  };
  dealt(R, dealL, SPOT.L, e.rag - 0.32, 'self'); dealt(Mc, dealR, SPOT.R, e.mars - 0.33, 'hand');
  const rk = t >= e.rag - 0.05 ? 0.5 + 1.6 * decay(t, e.rag - 0.05, 0.4) : 0, mk = t >= e.mars - 0.05 ? 0.5 + 1.6 * decay(t, e.mars - 0.05, 0.4) : 0;
  R.userData.setGlow(new THREE.Color(1.0, 0.3, 0.08), rk); Mc.userData.setGlow(new THREE.Color(1.0, 0.45, 0.25), mk);
  // his coin
  X.coin.visible = t >= coinT[0] && t < e.end;
  if (X.coin.visible) { if (t < coinT[1]) { const hp = handTip(X.man, 0, 0.03); X.coin.position.set(hp.x, Math.max(TOPY, hp.y - 0.03), hp.z); } else X.coin.position.set(SPOT.R.x + 0.075, TOPY, SPOT.R.z + 0.03); }
  // light: the face-up cards light her from below
  const lightK = 0.6 * rk + 0.5 * mk;
  if (lightK > 0.01) popLight(new THREE.Color(1.0, 0.45, 0.2), lightK * 0.45, V(0, 1.12, TZ - 0.05));
  hallLight(t, {});
  X.flare = 0.75 * e.hey.reduce((a, x) => a + decay(t, x, 0.45), 0) + (h === 3 ? 0.3 : 0);
}

// ================================================================ VERSE 1: the Tower, the Sun
function v1Frame(t) {
  const P = X.pops; const tw = X.faces.tower, sun = X.faces.sun;
  // ---- cards: the Tower in the middle, the Sun waiting face down at his right
  const towerFlip = [47.36, 47.68], sunFlip = [61.04, 61.44], swap = 59.4, side = 67.6, back = [69.02, 69.4];
  const towerSpot = t < swap ? SPOT.C : t < side ? V(-0.2, TOPY, TZ + 0.1) : V(-0.075, TOPY, TZ + 0.08);
  const sunSpot = t < swap ? V(0.22, TOPY, TZ + 0.2) : t < side ? SPOT.C : V(0.075, TOPY, TZ + 0.08);
  const tu = ramp(t, towerFlip[0], towerFlip[1]) * (1 - ramp(t, back[0], back[1])), su = ramp(t, sunFlip[0], sunFlip[1]) * (1 - ramp(t, back[0] + 0.06, back[1] + 0.06));
  const lift = (u) => 0.035 * Math.sin(Math.PI * u);
  const stomp = T.stomps.reduce((a, x) => a + (t >= x && t < x + 0.2 ? Math.sin(Math.PI * (t - x) / 0.2) * 0.012 : 0), 0);
  place(tw, towerSpot.clone().add(V(0, lift(ramp(t, towerFlip[0], towerFlip[1])) + lift(ramp(t, back[0], back[1])) + stomp, 0)), flipQ(tu, Math.PI, -1));
  place(sun, sunSpot.clone().add(V(0, lift(ramp(t, sunFlip[0], sunFlip[1])) + lift(ramp(t, back[0] + 0.06, back[1] + 0.06)) + stomp, 0)), flipQ(su, Math.PI, -1));
  sun.userData.setFlip(ramp(t, 66.6, 67.05));      // the card itself: feast, then the burning hall
  deckStackAt(SPOT.deck, 20);
  // ---- the pop-ups
  const tk = ramp(t, 47.9, 49.1, easeOut) * (1 - ramp(t, 57.55, 58.3));
  P.tower.root.position.set(0, TOPY + 0.001, TZ + 0.03); P.tower.setOpen(tk);
  const flash = [48.05, 49.25, 50.45, 51.6].reduce((a, x) => a + decay(t, x, 0.07) + 0.5 * decay(t, x + 0.13, 0.05), 0);
  P.tower.update(t, X.cam, { k20: ramp(t, 51.92, 52.5, lin), flash, fire: ramp(t, 48.4, 49.5), fall: ramp(t, 56.1, 56.95, easeIn) });
  const sk = ramp(t, 61.65, 62.85, easeOut) * (1 - ramp(t, 67.55, 68.1));
  P.sun.root.position.set(0, TOPY + 0.001, TZ + 0.03); P.sun.setOpen(sk);
  P.sun.update(t, X.cam, { gate: ramp(t, 64.86, 65.12, easeIn), outside: ramp(t, 64.24, 64.62), alt: ramp(t, 66.62, 67.05, lin) });
  // ---- light: red fire from the Tower; the night closes in; darkness with the cards glowing; gold floods back
  const outT = [56.62, 57.19, 57.48, 57.76, 58.05, 58.35];
  const night = t >= 56.5 && t < 60.63;
  let fire = 1, tor = [1, 1, 1, 1], stands = 1, candles = 1, fill = 1, hemiK = 0.18, hemi = null;
  if (night) { candles = t < outT[0] ? 1 : 0; tor = [t < outT[4] ? 1 : 0, t < outT[3] ? 1 : 0, t < outT[2] ? 1 : 0, t < outT[1] ? 1 : 0]; stands = t < outT[5] ? 1 : 0; fill = stands;
    fire = 1 - ramp(t, 57.0, 59.1, lin) * 0.97; hemiK = lerp(0.18, 0.04, ramp(t, 57, 59.1)); }
  const gold = t >= 60.63 && t < 69.6 ? 1 : 0;
  if (gold) { const gk = Math.max(ramp(t, 60.63, 60.75) * (1 - ramp(t, 65.2, 68.0)), 0.0); hemi = new THREE.Color(0.55, 0.42, 0.22); hemiK = 0.18 + 0.5 * gk * (0.6 + 0.4 * decay(t, 60.63, 1.2)); }
  hallLight(t, { fire, torches: tor, stands, candles, fill, hemi, hemiK });
  const towerGlow = tk * (0.8 + 0.2 * Math.sin(t * 13) * Math.sin(t * 7.3));
  if (tk > 0.01) popLight(new THREE.Color(1.0, 0.32, 0.08), 2.2 * towerGlow + 6 * flash);
  if (sk > 0.01) { const red = ramp(t, 66.6, 67.2); popLight(new THREE.Color(lerp(1.0, 1.0, red), lerp(0.72, 0.3, red), lerp(0.3, 0.08, red)), 2.6 * sk * (1 + 0.3 * decay(t, 61.65, 0.8))); }
  // the cards glow in the dark
  const dark = ramp(t, 58.6, 59.2) * (1 - ramp(t, 60.6, 60.8));
  tw.userData.setGlow(new THREE.Color(1, 0.35, 0.1), (tu > 0.95 ? 0.15 + 0.35 * decay(t, 47.7, 0.4) : 0) * (1 - tk * 0.6) + 0.2 * tk + 0.9 * dark);
  if (tu > 0.95 && tk < 0.3) popLight(new THREE.Color(1.0, 0.45, 0.2), 0.25 + 0.35 * decay(t, 47.7, 0.5), V(0, 1.3, TZ)); X.deckGlow(dark * 0.6); sun.userData.setGlow(new THREE.Color(1, 0.75, 0.3), (su > 0.9 ? 0.4 + 1.2 * decay(t, 61.5, 0.5) : 0) * (1 - ramp(t, 67.6, 68))); X.backGlow(sun, dark * 0.6);
  X.flare = 0.9 * decay(t, 60.63, 0.6) + 0.6 * decay(t, 67.2, 0.4) + 0.12 * T.stomps.reduce((s, e) => s + decay(t, e, 0.1), 0);
  // ---- the man
  let mr = track([[46.85, MAN_REST], [47.3, [SPOT.C.x + 0.05, 0.8, SPOT.C.z + 0.05]], [47.7, [SPOT.C.x - 0.03, 0.83, SPOT.C.z + 0.02]], [48.2, MAN_REST],
    [60.6, MAN_REST], [61.0, [SPOT.C.x + 0.05, 0.8, SPOT.C.z + 0.05]], [61.45, [SPOT.C.x - 0.03, 0.83, SPOT.C.z + 0.02]], [61.95, MAN_REST]], step2(t));
  const grin = t >= 52.6 && t < 57.0; X.man.setFace(grin ? 'grin' : 'smile');
  const laughB = t >= 53.77 && t < 56.6 ? Math.max(0, Math.sin(Math.PI * ((t - 53.77) / BEAT % 1))) : 0;
  let mlook = t < 46.85 ? [0, 1.3, HALL.seat.z] : t < 51.6 ? [0, 0.98, TZ] : t < 53.7 ? [0, 1.3, HALL.seat.z] : t < 60.5 ? [0, 0.98, TZ] : [0, 0.95, TZ];
  man({ handsW: [mr, ON_ROCKET], look: mlook, lean: 0.12 - 0.06 * laughB, headPitch: -0.05 * laughB });
  // ---- the seeress: still; at the end she turns both cards back over
  const sr = track([[68.5, SEER_REST.R], [68.95, [-0.075, 0.8, TZ + 0.05]], [69.4, [-0.075, 0.8, TZ + 0.06]], [69.6, SEER_REST.R]], t);
  const sl = track([[68.5, SEER_REST.L], [69.0, [0.075, 0.8, TZ + 0.05]], [69.45, [0.075, 0.8, TZ + 0.06]], [69.6, SEER_REST.L]], t);
  seer({ handsW: [sr, sl], lean: t > 68.5 ? 0.32 : 0.12, look: t < 47.8 ? [0, 1.25, HALL.stool.z] : t < 52.4 ? [0, 0.95, TZ] : t < 60.6 ? [0, 1.25, HALL.stool.z] : t < 68.4 ? [0, 0.95, TZ] : [0, 0.78, TZ + 0.06] });
  // ---- the Vikings: idle, then every head snaps to the rocket on the downbeat; they laugh on the beat
  vikings(t, (v, i) => {
    if (t < 44.63) return { mode: 'idle', noSlam: true };
    if (t < 47.1) return { mode: 'rocket', noSlam: true, live: true };
    if (t >= 53.77 && t < 58.4) return { mode: 'laugh', t0: 53.77, noSlam: true };
    if (night && t >= 58.4) return { mode: 'still', noSlam: true };
    return { mode: 'listen', look: [0, 0.95, TZ] };
  });
}

// ================================================================ REFRAINS: the singularity
// Singularity: every card on the table is pulled into one point of light above it. Every card a possibility: the point
// bursts into a wheel of faces. None a guarantee: they all turn their backs at once and fall. (Refrain 2 adds a second
// pull, into his face-down card, and "The choice belongs to you and me".)
const P0 = V(0, 1.22, TZ);
function refFrame(t, r) {
  const s = r === 0 ? { pull: 88.72, pull2: 90.9, burst: 92.64, guar: 95.1, fall: [95.5, 96.4], end: 96.45 }
    : { pull: 170.16, pull2: 172.3, burst: 174.16, guar: 178.1, fall: [178.75, 179.8], pull3: 180.75, pull4: 182.08, choice: 183.52, end: 187.5 };
  const allHook = K.hooks[r === 0 ? 1 : 2];
  // cards on the table at the start: the deck stack, RAGNARÖK left, MARS right (face up), the coin
  const src = [];
  const nDeck = r === 0 ? 22 : 18;
  for (let i = 0; i < nDeck; i++) src.push({ c: X.deck[i], p: V(SPOT.deck.x, TOPY + i * 0.0017, SPOT.deck.z), q: FACE_DOWN(0) });
  if (r === 0) src.push({ c: X.ragC, p: SPOT.L.clone(), q: FACE_UP() }, { c: X.marsC, p: SPOT.R.clone(), q: FACE_UP() });
  else { const f = X.faces;   // what the bridge left on the table
    src.push({ c: f.magician, p: V(-0.17, TOPY, TZ + 0.02), q: FACE_UP() }, { c: f.tower, p: V(0.0, TOPY, TZ - 0.02), q: FACE_UP() }, { c: f.star, p: V(0.17, TOPY, TZ + 0.02), q: FACE_UP() }, { c: X.engr, p: V(0, TOPY, TZ + 0.2), q: FACE_UP() });
    X.engr.userData.setReveal(1, 1); }
  // pull: spiral into the point
  const pullP = (i, n, p0, t0, t1) => { const d = t0 + (i / n) * (t1 - t0) * 0.55; const u = clamp((t - d) / ((t1 - t0) * 0.45)); if (u <= 0) return null;
    const e = easeIn(u); const a = (i * 2.399) + e * Math.PI * 3.2; const rad = (1 - e) * (0.25 + 0.15 * Math.sin(i)); const c = p0.clone().lerp(P0, e);
    return { p: V(P0.x + Math.cos(a) * rad * (1 - e * 0.2) * 1.0 + (c.x - P0.x) * (1 - e), c.y + Math.sin(e * Math.PI) * 0.12, P0.z + Math.sin(a) * rad * 0.6 + (c.z - P0.z) * (1 - e)), s: Math.max(0.05, 1 - e * 0.95), u };
  };
  const wheel = X.wheel; const NW = wheel.length;
  const phase = t < s.burst ? 'pull' : t < s.fall[0] ? 'wheel' : t < (s.pull3 || 1e9) ? 'fallen' : t < (s.choice || 1e9) ? 'pull3' : 'choice';
  let pointK = 0;
  if (phase === 'pull') {
    src.forEach((o, i) => { const pp = pullP(i, src.length, o.p, s.pull, s.pull + 1.6); if (!pp) { place(o.c, o.p, o.q); return; }
      if (pp.u >= 1) { o.c.visible = false; return; } place(o.c, pp.p, o.q.clone().slerp(qOf(0.3 * pp.u, (i * 1.3) + pp.u * 6, 0), easeIn(pp.u))); o.c.scale.setScalar(pp.s); });
    pointK = ramp(t, s.pull + 0.2, s.pull + 1.6) * (1 + 0.8 * Math.max(0, Math.sin((t - s.pull2) * 9)) * (t > s.pull2 ? 1 : 0)) + 1.5 * decay(t, s.pull2, 0.5);
  } else if (phase === 'wheel') {
    // the wheel: faces out toward him, turning slowly; at "guarantee" they all turn their backs in a ripple
    const open = ramp(t, s.burst - 0.06, s.burst + 0.5, easeOut), turn = (t - s.burst) * 0.22;
    wheel.forEach((c, i) => { const a = i / NW * Math.PI * 2 + turn; const rad = 0.62 * open;
      const p = V(P0.x + Math.cos(a) * rad, P0.y + 0.06 + Math.sin(a) * rad * 0.82, P0.z - 0.12);
      const back = ramp(t, s.guar - 0.12 + i * 0.012, s.guar + 0.12 + i * 0.012);
      place(c, p, qOf(0, Math.PI * back, Math.sin(a) * 0.15)); c.scale.setScalar(lerp(0.3, 1.9, open)); c.userData.setGlow(new THREE.Color(1, 0.75, 0.4), (1 - back) * (0.4 + 1.6 * decay(t, s.burst, 0.35))); });
    pointK = 2.5 * decay(t, s.burst, 0.25);
  } else {
    // fallen: the cards rain down onto the table in a loose heap, then are a deck again
    const fu = ramp(t, s.fall[0], s.fall[1], easeIn);
    if (t < s.fall[1] + 0.2) wheel.forEach((c, i) => { const a = i / NW * Math.PI * 2 + (s.fall[0] - s.burst) * 0.22; const rad = 0.52;
      const p0 = V(P0.x + Math.cos(a) * 0.62, P0.y + 0.06 + Math.sin(a) * 0.62 * 0.82, P0.z - 0.12); const p1 = V(Math.cos(i * 2.4) * 0.22, TOPY + i * 0.0018, TZ + Math.sin(i * 2.4) * 0.14);
      const p = p0.clone().lerp(p1, fu); place(c, p, qOf(Math.PI / 2 * fu, Math.PI * (1 - fu) + i, 0)); c.scale.setScalar(1.9 - 0.9 * fu); c.userData.setGlow(new THREE.Color(1, 0.75, 0.4), 0); });
    else deckStackAt(V(0, TOPY, TZ - 0.02), 22);
    if (phase === 'pull3' || phase === 'choice') {   // the second pull, into his card
      wheel.forEach((c) => { c.visible = false; }); deckStackAt(V(0, TOPY, TZ - 0.02), 22);
      pointK = ramp(t, s.pull3, s.pull3 + 0.5) * (1 - ramp(t, s.pull4 + 0.8, s.pull4 + 1.25)) * (1 + 0.6 * decay(t, s.pull4, 0.4));
    }
  }
  // the point of light
  X.vortexPt.visible = pointK > 0.01; X.vortexPt.position.copy(phase === 'pull3' ? P0.clone().lerp(SPOT.place.clone().add(V(0, 0.02, 0)), ramp(t, s.pull4, s.pull4 + 1.2)) : P0);
  X.vortexPt.scale.setScalar(0.12 + 0.18 * Math.min(2, pointK)); X.vortexPt.material.opacity = Math.min(1, pointK);
  X.pointL.position.copy(X.vortexPt.position); X.pointL.intensity = 3.2 * Math.min(2.5, pointK);
  if (phase === 'choice' || phase === 'pull3') X.tf.userData.setGlow(new THREE.Color(1, 0.72, 0.35), (phase === 'choice' ? 0.9 : ramp(t, s.pull4 + 0.6, s.pull4 + 1.2) * 0.9));
  // light: the hall dims as the point pulls the light in
  const dim = phase === 'pull' ? ramp(t, s.pull, s.pull + 1.4) : phase === 'wheel' ? 0.6 : phase === 'pull3' ? 0.5 : 0.25 * (1 - ramp(t, s.fall[1], s.fall[1] + 0.8));
  const bridgeDark = r === 1 ? 1 - ramp(t, 170.0, 170.3) : 0;
  hallLight(t, { fire: Math.max(0.03, 1 - 0.55 * dim - 0.97 * bridgeDark), torches: Math.max(0, 1 - 0.7 * dim - bridgeDark), stands: Math.max(0, 1 - 0.5 * dim - bridgeDark), candles: 1 - bridgeDark, fill: 1 - bridgeDark, hemiK: 0.18 - 0.08 * dim });
  X.finish.uFlash = 0.08 * decay(t, s.burst, 0.12); X.finish.flashCol.setRGB(1.0, 0.85, 0.6);
  X.flare = 0.5 * decay(t, s.burst, 0.4) + 0.12 * T.stomps.reduce((a, e) => a + decay(t, e, 0.1), 0) + (r === 1 ? 0.8 * decay(t, 170.0, 0.5) : 0);
  // puppets: everyone watches the point
  const lookPt = [X.vortexPt.position.x, X.vortexPt.position.y, X.vortexPt.position.z];
  const choice = phase === 'choice';
  seer({ look: choice ? [0, 1.25, HALL.stool.z] : lookPt, lean: 0.08, handsW: choice ? [SEER_REST.R, [0.1, 0.8, -5.82]] : [SEER_REST.R, SEER_REST.L], handRoll: choice ? [0, 1.2] : null });
  man({ look: choice ? [0, 1.25, HALL.seat.z] : lookPt, lean: 0.05 });
  vikings(t, (v) => ({ mode: 'listen', look: lookPt, leanAdd: -0.08 * dim }));
  if (t >= ROBOTS_IN) robotsAll(t, { mode: T.stomps.some((e) => Math.abs(t - e) < 0.5) ? 'slam' : 'stand', look: lookPt });
}

// ================================================================ VERSE 2: the Robot, the Red Planet, the Gardener, the Fool
function v2Frame(t) {
  const P = X.pops, f = X.faces;
  // the card turned for each world, at the centre; the earlier ones moved aside
  const cardsOf = [[f.robot, 96.5, 105.4], [f.red, 105.42, 113.65], [f.gardener, 113.67, 133.2]];
  cardsOf.forEach(([c, t0, t1], i) => { if (t < t0 - 0.6) { c.visible = false; return; }
    const u = ramp(t, t0, t0 + 0.38); const aside = t >= t1; const spot = aside ? V(-0.24 + 0.075 * i, TOPY, TZ + 0.2) : SPOT.C;
    place(c, spot.clone().add(V(0, 0.035 * Math.sin(Math.PI * u), 0)), flipQ(u, Math.PI, -1)); c.userData.setGlow(new THREE.Color(0.7, 0.85, 1.0), u > 0.95 && !aside ? 0.3 + 1.2 * decay(t, t0 + 0.38, 0.5) : 0); });
  deckStackAt(SPOT.deck, 18);
  // pop-ups
  const ro = ramp(t, 97.14, 98.3, easeOut) * (1 - ramp(t, 105.0, 105.45));
  P.robot.root.position.set(0, TOPY + 0.001, TZ + 0.03); P.robot.setOpen(ro); P.robot.update(t, X.cam, { row: ramp(t, 98.6, 99.0) });
  const re = ramp(t, 106.2, 107.25, easeOut) * (1 - ramp(t, 113.25, 113.65));
  P.red.root.position.set(0, TOPY + 0.001, TZ + 0.03); P.red.setOpen(re); P.red.update(t, X.cam, { rise: ramp(t, 107.0, 108.9), plant: ramp(t, 110.66, 111.5), name: ramp(t, 112.3, 112.7), sail: ramp(t, 112.72, 113.7) });
  const ga = ramp(t, 115.3, 116.5, easeOut) * (1 - ramp(t, 119.2, 119.44));
  P.gardener.root.position.set(0, TOPY + 0.001, TZ + 0.03); P.gardener.setOpen(ga); P.gardener.update(t);
  // light per card: steel blue, rust red, green-gold; the hall cheers; silver moonlight for the Fool; stillness after
  let hemi = null, hemiK = 0.18, fire = 1, tor = 1, stands = 1;
  if (ro > 0.01) { popLight(new THREE.Color(0.55, 0.75, 1.0), 2.4 * ro); hemi = new THREE.Color(0.25, 0.34, 0.55); hemiK = 0.3; }
  if (t >= 101.6 && t < 105.4) { hemi = new THREE.Color(0.28, 0.38, 0.6); hemiK = 0.38; fire = 0.75; }
  if (re > 0.01) { popLight(new THREE.Color(1.0, 0.38, 0.18), 2.6 * re * (0.4 + 0.6 * ramp(t, 107, 108.6))); hemi = new THREE.Color(0.5, 0.2, 0.12); hemiK = 0.3; }
  if (ga > 0.01) { popLight(new THREE.Color(0.75, 1.0, 0.45), 2.2 * ga); hemi = new THREE.Color(0.35, 0.45, 0.22); hemiK = 0.3; }
  const tomato = t >= 119.2 && t < 124.0;
  const freeze = t >= 124.0 && t < 128.6;
  if (tomato) { X.spot.intensity = 2.2 * ramp(t, 121.3, 121.55); X.shaft.visible = t >= 121.3; X.shaft.material.opacity = ramp(t, 121.3, 121.6); }
  if (freeze || t >= 128.6) { hemi = new THREE.Color(0.35, 0.42, 0.6); hemiK = 0.22; fire = freeze ? 0.5 : 0.45; tor = 0.35; stands = 0.6; X.hall.userData.ctl.moon = 3.5; }
  hallLight(t, { fire, torches: tor, stands, hemi, hemiK });
  if (freeze || t >= 128.6) X.hall.userData.ctl.moon = 3.5;
  X.flare = 0.7 * decay(t, 122.1, 0.6) + 0.4 * decay(t, 97.14, 0.6);
  if (freeze) X.freeze = 124.0;
  // the tomato scene at the feast table: the biggest Viking (seat 0), the plant, the harvesting robot
  const big = X.vikings[0], r0 = X.robots[0], seat = big.userData.seat;
  const plantP = V(seat.side * (F.x - 0.05), F.top, seat.z - 0.02);
  X.plant.visible = t >= 117.0 && t < 133.2; X.plant.position.copy(plantP); X.plant.rotation.y = 0.6;
  X.label.visible = X.plant.visible && t >= 121.3; X.label.position.copy(plantP).add(V(seat.side * -0.05, 0.12, -0.08)); X.label.rotation.y = seat.side < 0 ? 2.5 : -2.5;
  const fruit = X.plant.userData.fruit; fruit.visible = t < 121.0;
  X.tomatoHeld.visible = t >= 121.0 && t < 124.6;
  // ---- the man: turns each card; then, in the stillness, looks at his rocket; the robot sets a tomato before him
  const flips = [96.5, 105.42, 113.67];
  let mr = MAN_REST; for (const f0 of flips) if (t >= f0 - 0.45 && t < f0 + 0.85) mr = track([[f0 - 0.45, MAN_REST], [f0 - 0.05, [SPOT.C.x + 0.05, 0.8, SPOT.C.z + 0.05]], [f0 + 0.38, [SPOT.C.x - 0.03, 0.83, SPOT.C.z + 0.02]], [f0 + 0.85, MAN_REST]], step2(t));
  let mlook = [0, 0.98, TZ]; let mlean = 0.12, mhp = 0.05;
  if (t >= 128.6) { mlook = [-0.12, 1.05, -5.62]; mlean = 0.1; }
  if (t >= 131.6) mlook = [0.1, 0.8, -5.66];
  const tm = t >= 128.6 ? t : (freeze ? 124.0 : t);
  const holdR = t >= 128.6; X.rocketOnTable = holdR;
  man({ handsW: [mr, holdR ? [-0.1, 0.98, -5.58] : ON_ROCKET], look: mlook, lean: mlean, headPitch: mhp });
  // the seeress: watches him; the glimpse is done by her hand double
  seer({ look: t >= 124.3 && t < 128.6 ? [0, 0.8, -5.62] : [0, 1.25, HALL.stool.z], lean: t >= 124.3 && t < 128.6 ? 0.35 : 0.12,
    handsW: t >= 124.3 && t < 128.6 ? [SEER_REST.R, [0.12, 0.8, -6.0]] : [SEER_REST.R, SEER_REST.L] });
  // ---- the Vikings
  const vt = freeze ? 124.0 : t;
  vikings(vt, (v, i) => {
    if (i === 0 && tomato) {
      const pose = t < 120.48 ? 1 : t < 121.52 ? 2 : 3;
      if (pose === 1) return { mode: 'listen', look: [plantP.x, plantP.y + 0.25, plantP.z], noSlam: true, live: true };
      return { mode: 'listen', noSlam: true, live: true, look: pose === 2 ? [r0.root.position.x, 1.5, r0.root.position.z] : [plantP.x + 0.1, 1.35, plantP.z] };
    }
    if (t >= 101.6 && t < 119.2) return { mode: 'lounge', noSlam: true };
    if (t >= 122.1 && t < 128.6) return { mode: 'cheer', t0: 122.1, noSlam: true };
    if (t >= 128.6) return { mode: 'still', noSlam: true, look: [0, 1.1, -5.4] };
    if (t >= 119.2 && t < 122.1) return { mode: 'listen', look: [plantP.x, 1.1, plantP.z], noSlam: true };
    return { mode: 'listen', look: [0, 0.95, TZ], noSlam: true };
  });
  // the big Viking's hands for the three poses
  if (tomato) {
    const p = t < 120.48 ? 1 : t < 121.52 ? 2 : 3; const sd = seat.side;
    if (p === 1) big.pose({ lean: 0.22, look: [plantP.x, plantP.y + 0.3, plantP.z], lookK: 0.9, handsW: [[sd * (F.x + 0.2), F.top + 0.03, seat.z + 0.17], [sd * (F.x + 0.2), F.top + 0.03, seat.z - 0.17]] });
    if (p === 2) big.pose({ lean: 0.1, look: [r0.root.position.x, 1.45, r0.root.position.z], lookK: 0.9, handsW: [[sd * (F.x + 0.2), F.top + 0.03, seat.z + 0.17], [sd * (F.x + 0.1), 1.1, seat.z - 0.12]] });
    if (p === 3) big.pose({ lean: -0.06, headPitch: -0.35, look: [sd * (F.x + 0.02), 1.6, seat.z - 0.04], lookK: 0.9, handsW: [[sd * (F.x - 0.02), 1.48, seat.z + 0.03], [sd * (F.x - 0.02), 1.48, seat.z - 0.1]] });
    if (p === 3) { big.root.updateMatrixWorld(true); const a = handTip(big, 0, 0.06), b = handTip(big, 1, 0.06); X.tomatoHeld.position.copy(a).lerp(b, 0.5).add(V(0, 0.035, 0)); }
    if (p === 2) X.tomatoHeld.visible = false;
  }
  if (X.tomatoHeld.visible && t >= 121.52) { const a = handTip(big, 0, 0.06), b = handTip(big, 1, 0.06); X.tomatoHeld.position.copy(a).lerp(b, 0.5).add(V(0, 0.035, 0)); }
  // spot and shaft on him
  if (tomato && t >= 121.3) X.aux.position.set(seat.side * (F.x + 0.3), 1.95, seat.z);
  X.shaft.position.set(seat.side * (F.x + 0.45), 1.75, seat.z);
  // ---- the robots: row while the Vikings lounge; robot 0 harvests; the attendant sets a tomato before him
  if (t >= ROBOTS_IN) robotsAll(freeze ? 124.0 : t, (r, i) => {
    if (i === 0 && tomato) { const reach = t < 120.48 ? 1 : 0.85; return { mode: 'stand' }; }
    if (t < 119.2) return { mode: 'row' };
    if (t >= 122.1 && t < 128.6) return { mode: 'stand', look: [r.userData.side * 2.3, 1.4, r.userData.z] };
    return { mode: 'stand' };
  });
  if (tomato) { const sd = r0.userData.side; const pz = t < 120.48 ? 1 : t < 121.52 ? 2 : 3; const reachP = pz === 1 ? [plantP.x + sd * 0.06, plantP.y + 0.25, plantP.z + 0.03] : [plantP.x + sd * 0.16, plantP.y + 0.3, plantP.z + 0.05];
    if (pz < 3) r0.pose({ seated: false, lean: 0.22, handsW: [reachP, [r0.root.position.x - sd * 0.05, 0.85, r0.root.position.z - 0.18]], look: [plantP.x, plantP.y + 0.25, plantP.z], lookK: 0.9 });
    else r0.pose({ seated: false, lean: -0.04, hands: [[-0.2, -0.02, 0.06], [0.2, -0.02, 0.06]], look: [big.root.position.x, 1.6, big.root.position.z], lookK: 0.9 }); }
  // the attendant
  const at = X.attendant; const giftT = [130.4, 131.5];
  const gp = t < giftT[0] ? [0.5, 0.9, -5.66] : t < giftT[1] ? mixV([0.5, 0.95, -5.66], [0.1, TOPY + 0.05, -5.7], ramp(t, giftT[0], giftT[1])) : mixV([0.1, TOPY + 0.05, -5.7], [0.45, 0.9, -5.7], ramp(t, giftT[1] + 0.2, giftT[1] + 0.9));
  if (at.root.visible) at.pose({ seated: false, lean: t >= giftT[0] && t < giftT[1] + 0.6 ? 0.35 : 0.05, handsW: [[0.4, 0.86, -5.82], t >= 128.6 ? gp : [0.4, 0.86, -5.5]], look: [0, 0.9, -5.6], lookK: 0.7 });
  X.tomatoGift.visible = t >= giftT[0] - 0.3 && t < 133.2;
  if (X.tomatoGift.visible) { if (t < giftT[1]) { const hp = handTip(at, 1, 0.08); X.tomatoGift.position.copy(hp); } else X.tomatoGift.position.set(0.1, TOPY + 0.028, -5.7); }
  // ---- the glimpse: her gloved hand lifts the corner of his card, for us alone; the figure turns its head
  if (t >= 124.3 && t < 128.6) {
    const lift = ramp(t, 124.7, 125.4) * (1 - ramp(t, 128.1, 128.55));
    const hinge = SPOT.place.clone().add(V(0, 0, CARD.H / 2));     // the edge nearest him stays down
    const qa = new THREE.Quaternion().setFromAxisAngle(V(1, 0, 0), 0.95 * lift);
    const q = FACE_DOWN(Math.PI).premultiply(qa);
    const c = SPOT.place.clone().sub(hinge).applyQuaternion(qa).add(hinge);
    place(X.tf, c, q); X.tf.userData.setFool(1);
    if (t >= 126.9) X.tf.userData.front.material.userData.u.mapC.value = X.foolTurnTex;
    X.tf.userData.setGlow(new THREE.Color(0.6, 0.75, 1.0), 0.45 * lift); popLight(new THREE.Color(0.6, 0.72, 1.0), 0.14 * lift, V(0, 0.98, -5.92));
    // the hand double: glove at the lifted far edge
    const far = X.tf.localToWorld(V(0.03, CARD.H / 2 - 0.004, 0)); X.handDouble.visible = true; X.handDouble.position.copy(far); X.handDouble.rotation.set(0, 1.25, 0);
  }
}

// ================================================================ BRIDGE: one card per bar; a card that engraves itself; one human line
function bridgeFrame(t) {
  const f = X.faces;
  const lay = [[f.magician, 151.25, V(-0.17, TOPY, TZ + 0.02)], [f.tower2, 153.45, V(0.0, TOPY, TZ - 0.02)], [f.star, 155.75, V(0.17, TOPY, TZ + 0.02)]];
  const hr = handTip(X.seer, 0, 0.05);
  lay.forEach(([c, t0, p]) => { if (t < t0) { c.visible = false; return; } const u = ramp(t, t0, t0 + 0.45);
    const from = hr.clone(); const pos = from.clone().lerp(p, easeOut(u)); pos.y = lerp(from.y, p.y, easeOut(u)) + 0.04 * Math.sin(Math.PI * u);
    place(c, t >= t0 + 0.45 ? p : pos, flipQ(easeIO(u), Math.PI, 1)); c.userData.setGlow(new THREE.Color(1, 0.75, 0.4), 0.12 + 0.3 * decay(t, t0 + 0.4, 0.5)); });
  // the self-engraving card
  const E = X.engr; place(E, V(0, TOPY, TZ + 0.2), FACE_UP());
  const reveal = ramp(t, 160.9, 164.7, lin), human = ramp(t, 167.62, 168.98, lin);
  E.userData.setReveal(reveal, human); E.visible = t >= 160.2;
  E.userData.setGlow(new THREE.Color(1, 0.7, 0.35), 0.06 + 0.06 * (reveal > 0 && reveal < 1 ? 1 : 0) + 0.25 * human);
  // the burin's spark: scanning along the engraving front, then at the tip of his one line
  if (reveal > 0.001 && reveal < 0.999) { const x = 110 + 980 * (0.5 + 0.5 * Math.sin(t * 7.3)), y = 110 + 1620 * reveal + Math.sin(x / 60) * 18;
    X.spark.visible = true; X.spark.position.copy(E.localToWorld(V((x / 1200 - 0.5) * CARD.W, (0.5 - y / 2057) * CARD.H, 0.003))); X.spark.scale.setScalar(0.022 + 0.006 * Math.sin(t * 40)); }
  deckStackAt(SPOT.deck, 18);
  // the candle (the only light), the burin
  X.candleB.visible = true; X.candleB.position.set(-0.3, TOPY, TZ - 0.12);
  const out = t >= 169.5;
  X.candleB.userData.flame.visible = !out; X.candleL.intensity = out ? 0 : 1.4 * (0.92 + 0.05 * Math.sin(t * 11) + 0.03 * Math.sin(t * 23)); X.aux.position.set(-0.3, 1.05, TZ - 0.12);
  X.burin.visible = true;
  const grab = [165.3, 166.2], cut = [167.62, 168.98];
  // the burin in his hand: picked up, then its tip follows the line
  const lineP = (u) => { const x = 566 + (860 - 566) * u, y = 1130 - Math.sin(u * Math.PI * 0.62) * 640; return E.localToWorld(V((x / 1200 - 0.5) * CARD.W, (0.5 - y / 2057) * CARD.H, 0.002)); };
  let hand = MAN_REST;
  if (t >= grab[0] - 0.5) {
    const tip = t < cut[0] ? lineP(0) : lineP(Math.min(1, human));
    const hold = t < grab[0] ? MAN_REST : t < grab[1] ? mixV([0.16, 0.8, TZ + 0.32], [tip.x + 0.12, tip.y + 0.08, tip.z + 0.1], ramp(t, grab[0], grab[1])) : [tip.x + 0.12, tip.y + 0.08, tip.z + 0.1];
    hand = t < grab[0] ? mixV(MAN_REST, [0.16, 0.8, TZ + 0.32], ramp(t, grab[0] - 0.5, grab[0])) : hold;
  }
  man({ handsW: [hand, ON_ROCKET], look: t < 160.5 ? [0, 0.78, TZ] : [0, 0.77, TZ + 0.2], lean: t > 165 ? 0.32 : 0.16 });
  if (t < grab[0] + 0.3) { X.burin.position.set(0.16, TOPY + 0.006, TZ + 0.32); X.burin.rotation.set(0, 2.6, 0); }
  else { const hp = handTip(X.man, 0, 0.05); const tip = t < cut[0] ? lineP(0) : lineP(Math.min(1, human)); X.burin.position.copy(tip); const d = hp.clone().sub(tip);
    X.burin.quaternion.setFromUnitVectors(V(-1, 0, 0), d.normalize());
    if (human > 0.001 && human < 0.999) { X.spark.visible = true; X.spark.position.copy(tip).add(V(0, 0.002, 0)); X.spark.scale.setScalar(0.03 + 0.008 * Math.sin(t * 37)); } }
  // the seeress lays the cards; on "The Fool" her hand rests on his card (the hand double)
  const srKeys = [[151.0, SEER_REST.R], [151.25, [-0.06, 0.88, -6.15]]];
  lay.forEach(([c, t0, p]) => { srKeys.push([t0, [-0.06, 0.88, -6.15]], [t0 + 0.42, [p.x, 0.8, p.z - 0.04]], [t0 + 0.9, [-0.06, 0.88, -6.15]]); });
  srKeys.push([158.2, SEER_REST.R]);
  const sr = track(srKeys, t);
  const deckHand = [0.12, 0.88, -6.2];
  seer({ handsW: [sr, t < 158.2 ? deckHand : SEER_REST.L], lean: t < 158.2 ? 0.4 : t < 160.6 ? 0.36 : 0.12, look: t < 158.3 ? [0, 0.78, TZ] : t < 160.6 ? [0, 0.78, -5.6] : t < 165 ? [0, 0.77, TZ + 0.2] : [0, 1.25, HALL.stool.z], lookK: 0.85 });
  if (t >= 158.45 && t < 160.7) { X.handDouble.visible = true; const u = ramp(t, 158.45, 158.9); X.handDouble.position.copy(SPOT.place).add(V(0.0, 0.012 + 0.04 * (1 - u), -0.04)); X.handDouble.rotation.set(0, 0.25, 0); }
  // the dark hall
  hallLight(t, { fire: 0.03, torches: 0, stands: 0, candles: 0, fill: 0, hemiK: 0.03 });
  X.flare = 0;
  vikings(t, { mode: 'still', noSlam: true, look: [0, 0.9, TZ] });
  if (t >= ROBOTS_IN) robotsAll(t, { mode: 'stand', look: [0, 0.9, TZ] });
}

// ================================================================ OUTRO: one last card; the headland
function outroFrame(t) {
  const tf = X.tf; const H = X.head;
  // he turns his card over, face up, where it has lain since the start; seen from one side it is MARS, from the
  // other RAGNARÖK, and straight on, for the first time, the Fool
  const flipT = [207.62, 208.12];
  const hand = track([[207.2, MAN_REST], [207.55, [0.04, 0.8, -5.58]], [208.12, [-0.02, 0.82, -5.63]], [208.6, MAN_REST]], step2(t));
  man({ handsW: [hand, ON_ROCKET], look: [0.0, 0.77, -5.6], lean: 0.24, headPitch: 0.1 });
  const u = ramp(t, flipT[0], flipT[1]);
  place(tf, SPOT.place.clone().add(V(0, 0.035 * Math.sin(Math.PI * u), 0)), flipQ(u, Math.PI, -1));
  const view = X.outroView(t);                  // -1 left (MARS), 0 straight (the Fool), +1 right (RAGNARÖK)
  tf.userData.setFlip(view > 0.35 ? 1 : 0); tf.userData.setFool(Math.abs(view) < 0.35 && t > 209.2 ? 1 : 0);
  tf.userData.setGlow(new THREE.Color(1, 0.75, 0.4), u > 0.95 ? 0.06 + 0.1 * decay(t, 209.92, 0.6) : 0);
  seer({ look: [0.0, 0.78, -5.6], lean: 0.14 });
  vikings(t, { mode: 'still', noSlam: true, look: [0, 1.0, -5.5] });
  robotsAll(t, { mode: 'stand', look: [0, 1.0, -5.5] });
  hallLight(t, { fire: 0.55, torches: 0.6, stands: 0.8, hemiK: 0.15 });
  X.flare = 0;
  deckStackAt(SPOT.deck, 22); place(X.ragC, SPOT.L, FACE_UP()); place(X.marsC, SPOT.R, FACE_UP());
  if (u > 0.95) popLight(new THREE.Color(1.0, 0.8, 0.55), 0.07, V(0.15, 1.2, -5.5));
  // ---- the headland (from the cut on)
  if (t >= 212.2) X.scenes.cur = H.scene;
  X.finish.uFlash = 0.45 * ramp(t, 211.95, 212.2, easeIn) * (t < 212.2 ? 1 : 0) + 0.55 * decay(t, 212.2, 0.14); X.finish.flashCol.setRGB(1.0, 0.82, 0.5);
}

// ================================================================ CODA: back at the table; the deck slides to you
function codaFrame(t) {
  const sweep = [229.1, 230.6], shufA = 231.3, shufB = 232.35, slide = [233.6, 235.0];
  // the cards on the table (from the hooks and the outro) are swept up into the deck, shuffled, and slid to the viewer
  const tf = X.tf;
  if (t < sweep[0]) { place(X.ragC, SPOT.L, FACE_UP()); place(X.marsC, SPOT.R, FACE_UP()); X.ragC.userData.setGlow(new THREE.Color(1, 0.3, 0.08), 0.4); X.marsC.userData.setGlow(new THREE.Color(1, 0.45, 0.25), 0.4);
    place(tf, SPOT.place, FACE_UP()); tf.userData.setFool(1); deckStackAt(SPOT.deck, 22); }
  else if (t < shufA - 0.05) { const u = ramp(t, sweep[0], sweep[1]); const to = V(0, TOPY, TZ - 0.08);
    place(X.ragC, SPOT.L.clone().lerp(to, u), FACE_UP().slerp(FACE_DOWN(0), u)); place(X.marsC, SPOT.R.clone().lerp(to, u), FACE_UP().slerp(FACE_DOWN(0), u));
    place(tf, SPOT.place.clone().lerp(to, u), FACE_UP()); tf.userData.setFool(1); deckStackAt(SPOT.deck.clone().lerp(to, u), 22); }
  else if (t < slide[0]) { const e = { shuf1: shufA - 0.29, shuf2: shufB - 0.04 }; for (let k = 0; k < 22; k++) { const s1 = springPos(t, shufA, 1, HANDS_MID, k), s2 = springPos(t, shufB, -1, HANDS_MID, k); const s = t < shufB ? s1 : s2; place(X.deck[k], s.p, s.q); }
    const top = t < shufB ? springPos(t, shufA, 1, HANDS_MID, 22, 23) : springPos(t, shufB, -1, HANDS_MID, 22, 23); place(tf, top.p.clone().add(V(0, 0.003, 0)), top.q); tf.userData.setFool(0); }
  else { const u = ramp(t, slide[0], slide[1], easeOut); const from = V(0, TOPY, TZ - 0.1), to = V(0, TOPY, -5.68); const p = from.clone().lerp(to, u);
    deckStackAt(p, 22, Math.PI); place(tf, p.clone().add(V(0, 22 * 0.0017 + 0.001, 0)), FACE_UP());
    // the top card flickers between RAGNARÖK and MARS as it slides, and keeps asking when it stops
    const ph = (t - slide[0]); const fl = t < slide[1] ? (Math.sin(ph * 14) > 0 ? 1 : 0) : (Math.sin((t - slide[1]) * 1.35) > 0 ? 1 : 0);
    tf.userData.setFool(0); tf.userData.setFlip(fl); tf.userData.setGlow(new THREE.Color(1, 0.6, 0.3), 0.5 + 0.3 * Math.sin(t * 2)); }
  if (t >= sweep[0] && t < slide[0]) { X.ragC.visible = t < sweep[1]; X.marsC.visible = t < sweep[1]; }
  // the seeress
  const sr = track([[228.9, SEER_REST.R], [229.1, [-0.2, 0.8, -6.0]], [230.6, [-0.05, 0.82, -6.06]], [231.0, [-0.13, 1.06, -6.38]], [233.3, [-0.13, 1.06, -6.38]], [233.6, [-0.03, 0.8, -6.06]], [235.0, [0.0, 0.8, -5.72]], [236.2, [0, 0.8, -5.8]], [237.5, SEER_REST.R]], t);
  const sl = track([[228.9, SEER_REST.L], [229.1, [0.2, 0.8, -6.0]], [230.6, [0.05, 0.82, -6.06]], [231.0, [0.13, 1.06, -6.38]], [233.3, [0.13, 1.06, -6.38]], [233.6, SEER_REST.L]], t);
  seer({ handsW: [sr, sl], lean: t > 233.4 && t < 236.5 ? 0.45 : 0.15, look: t > 233.5 ? [0, 1.2, -5.0] : [0, 0.9, TZ] });
  man({ look: [0, 0.9, TZ] }); X.man.root.visible = t < 233.45;      // the last shot is his seat: yours
  vikings(t, { mode: 'listen', heys: [227.9], look: [0, 0.95, TZ] }); robotsAll(t, { mode: 'slam', heys: [227.9], look: [0, 0.95, TZ] });
  // light: fire again, then the hearth dies
  const die = ramp(t, 240.4, 242.0, lin);
  hallLight(t, { fire: Math.max(0.0, 1 - die * 1.0), torches: 1 - die, stands: 1 - die, candles: 1 - die, fill: 1 - die, hemiK: 0.18 * (1 - die) });
  X.flare = 1.2 * decay(t, 227.9, 0.7);
  X.endPlate.visible = t >= 242.0; if (X.endPlate.visible) X.endPlate.userData.set(ramp(t, 242.0, 242.9));
}

// ================================================================ SHOTS
// [t, cam(t, u) -> [pos, look, fov, up?]] ; u = 0..1 through the shot
function buildShots() {
  const S = [];
  const add = (t, f) => S.push({ t, cam: f });
  const st = (p0, p1, l0, l1, fov, up) => (t, u) => [toV(p0).lerp(toV(p1), u), toV(l0).lerp(toV(l1), u), fov, up];
  const UPZ = V(0, 0, -1);
  // ---------------- hooks
  const hookShots = (h) => {
    const e = K.hooks[h]; const m = h % 2 ? -1 : 1;
    if (h > 0) {
      add(e.start, st([0, 1.62, -5.72], [0, 1.6, -5.76], [0, 1.02, -6.38], [0, 1.02, -6.38], 40));                                   // Shuffle the deck! (her hands)
      add(e.hey[0], h === 2 ? st([-0.75, 1.35, 0.4], [-0.75, 1.38, 0.5], [-2.2, 1.0, -1.6], [-2.2, 1.0, -1.6], 42) : st([0, 3.6, -4.9], [0, 3.75, -5.1], [0, 0.6, 3.0], [0, 0.6, 3.0], 46));   // HEY
      add(e.shuf2 - 0.03, st([m * 0.38, 1.31, -6.36], [m * 0.35, 1.3, -6.3], [0, 1.16, -5.2], [0, 1.16, -5.2], 38));                // Shuffle the deck! (him)
    }
    add(e.hey[1], h === 2 ? st([0.75, 1.35, 0.4], [0.75, 1.38, 0.5], [2.2, 1.0, -1.6], [2.2, 1.0, -1.6], 42) : st([0, 1.75, 9.2], [0, 1.7, 8.9], [0, 1.0, -6], [0, 1.0, -6], 44));   // HEY from the near end
    add(e.turn - 0.12, st([m * 0.95, 1.5, -5.35], [m * 0.9, 1.47, -5.38], [-m * 0.05, 0.92, -6.1], [-m * 0.05, 0.92, -6.1], 42));     // Turn one over: she deals two
    add(e.place - 0.15, st([m * -1.25, 1.02, 3.7], [m * -1.25, 1.0, 3.3], [m * -2.0, 0.78, -2.6], [m * -2.0, 0.78, -2.6], 34));      // place your bets: silver on the tables
    add(e.bets + 0.2, st([0.1, 1.36, -5.86], [0.1, 1.33, -5.86], [0.1, 0.76, -5.87], [0.1, 0.76, -5.87], 40, UPZ));                   // his one coin, by the right-hand card
    add(e.cast1 - 0.12, st([m * 0.15, 0.98, -5.42], [m * 0.13, 0.97, -5.47], [0, 1.12, -6.6], [0, 1.12, -6.6], 38));                   // Cast the cards! (her)
    add(e.hey[2], h === 3 ? st([0, 3.0, -2.2], [0, 3.2, -2.0], [0, 0.6, 6.0], [0, 0.6, 6.0], 50) : st([-1.0, 2.6, -1.6], [-1.0, 2.7, -1.4], [1.8, 0.8, 2.0], [1.8, 0.8, 2.0], 48));   // HEY
    add(e.cast2 - 0.12, st([-0.3, 1.45, -6.78], [-0.28, 1.42, -6.72], [0.05, 0.8, -5.75], [0.05, 0.8, -5.75], 40));                    // Cast the cards! (over her shoulder)
    add(e.hey[3], h === 2 ? st([-0.55, 1.45, 3.25], [-0.57, 1.46, 3.3], [-2.3, 1.0, 2.35], [-2.3, 1.0, 2.35], 40) : st([0.0, 2.0, 7.5], [0.0, 2.1, 7.8], [0, 0.9, -5], [0, 0.9, -5], 40));   // HEY (hook 3: the late slam)
    add(e.rag - 0.55, st([-0.12, 1.16, -5.7], [-0.12, 1.13, -5.72], [-0.12, 0.765, -5.91], [-0.12, 0.765, -5.91], 30));                  // RAGNARÖK turns itself over
    add(e.reachW - 0.35, st([0.62, 1.0, -5.6], [0.58, 0.99, -5.63], [0.04, 0.86, -5.95], [0.04, 0.86, -5.95], 36));                     // or reach for…
    add(e.mars - 0.4, st([0.12, 1.3, -5.9], [0.12, 1.26, -5.9], [0.12, 0.76, -5.905], [0.12, 0.76, -5.905], 30, UPZ));                 // MARS
  };
  hookShots(0);
  // ---------------- verse 1
  add(42.34, st([-1.75, 0.98, -6.62], [-1.69, 0.98, -6.56], [-0.22, 0.72, -5.15], [-0.22, 0.74, -5.15], 42));       // a man with a rocket sits down by the fire
  add(44.63, st([-0.7, 0.45, -5.6], [-0.7, 0.47, -5.56], [0.0, 1.0, 2.5], [0.0, 1.0, 2.5], 46));                   // every head turns to the rocket on the beat
  add(46.92, st([0, 1.44, -5.9], [0, 1.4, -5.9], [0, 0.76, -5.91], [0, 0.76, -5.91], 34, UPZ));                    // he turns up the Tower
  add(48.3, st([-0.36, 1.0, -5.45], [-0.33, 0.99, -5.48], [0, 0.95, -5.95], [0, 0.95, -5.95], 34));                // the flames climbing higher
  const disp = X.pops.tower.parts.display; const DP = V(disp.x, TOPY + disp.y, TZ + 0.03 + disp.z);
  add(51.49, st(DP.clone().add(V(0.03, 0.03, 0.34)), DP.clone().add(V(0.02, 0.02, 0.29)), DP, DP, 30));            // "Twenty percent," — the windows spell it
  add(52.88, st([0.52, 1.24, -5.92], [0.5, 1.24, -5.88], [0, 1.28, -5.2], [0, 1.28, -5.2], 34));                   // …he says with a grin
  add(53.77, st([-1.2, 1.15, -0.35], [-1.22, 1.16, -0.25], [-2.3, 1.05, -1.65], [-2.3, 1.05, -1.65], 38));         // the whole hall laughs
  add(56.05, st([-0.2, 0.98, -5.42], [-0.18, 0.97, -5.47], [0, 0.92, -5.95], [0, 0.92, -5.95], 36));               // …and the Tower falls
  add(57.19, st([0, 1.9, 10.2], [0, 1.85, 9.9], [0, 1.0, -4], [0, 1.0, -4], 42));                                  // the night closes in down the hall
  add(59.1, st([0, 1.45, -5.8], [0, 1.42, -5.82], [0, 0.76, -5.92], [0, 0.76, -5.92], 40, UPZ));                   // darkness; only the cards glow
  add(60.63, st([-0.36, 1.2, -5.55], [-0.34, 1.18, -5.57], [0, 0.78, -5.92], [0, 0.78, -5.92], 36));               // gold floods back: he turns up the Sun
  add(61.95, st([-0.5, 1.06, -5.35], [-0.47, 1.05, -5.38], [0, 0.95, -5.95], [0, 0.95, -5.95], 36));              // a world without need
  add(62.91, st([0.06, 0.92, -5.45], [0.05, 0.91, -5.5], [0.0, 0.86, -5.92], [0.0, 0.86, -5.92], 36));             // the machines make plenty — but who gets to eat?
  add(65.2, (t, u) => [V(lerp(-0.26, 0.26, easeIO(u)), 0.95, -5.5), V(0, 0.9, -5.95), 34]);                        // a feast on one side, the other in flames
  add(67.49, st([0.55, 1.2, -5.55], [0.52, 1.18, -5.58], [0, 0.78, -5.95], [0, 0.78, -5.95], 38));                 // two different futures, the very same game
  // ---------------- hook 2, refrain 1
  hookShots(1);
  add(88.6, st([-1.05, 1.12, -5.95], [-0.98, 1.14, -5.95], [0, 1.0, -5.95], [0, 1.1, -5.95], 40));                 // Singularity: the cards are pulled into a point
  add(90.3, st([-1.3, 1.2, -5.6], [-1.22, 1.2, -5.65], [0, 1.18, -5.95], [0, 1.18, -5.95], 38));                   // Singularity
  add(92.57, st([0, 1.92, -4.45], [0, 1.9, -4.55], [0, 1.3, -6.05], [0, 1.3, -6.05], 44));                        // Every card a possibility
  add(94.85, st([1.4, 1.35, -5.2], [1.3, 1.3, -5.3], [0, 1.05, -6.0], [0, 1.0, -6.0], 44));                        // None a guarantee
  // ---------------- verse 2
  add(96.45, st([0.06, 1.3, -5.42], [0.05, 1.28, -5.45], [0, 0.76, -5.93], [0, 0.76, -5.93], 32));                 // the Robot comes up
  add(97.14, st([-0.3, 0.95, -5.42], [-0.28, 0.94, -5.45], [0, 0.88, -5.93], [0, 0.88, -5.93], 36));                // no more rowing the seas
  add(99.39, st([0.05, 0.9, -5.55], [0.04, 0.89, -5.6], [0, 0.86, -5.93], [0, 0.86, -5.93], 32));                  // the machines take the oars
  add(101.68, st([0.0, 1.9, -3.6], [0.0, 1.92, -3.4], [-1.6, 0.9, 0.0], [-1.6, 0.9, 0.0], 42));                    // …in the hall: robots row, Vikings lounge
  add(103.94, st([0.85, 1.15, 0.25], [0.83, 1.15, 0.1], [2.3, 0.95, -2.2], [2.3, 0.95, -2.2], 40));               // …while we sit in the breeze
  add(105.3, st([-0.06, 1.3, -5.42], [-0.05, 1.28, -5.45], [0, 0.76, -5.93], [0, 0.76, -5.93], 32));              // the Red Planet
  add(106.22, st([-0.32, 0.96, -5.38], [-0.3, 0.95, -5.43], [0, 0.92, -5.95], [0, 0.92, -5.95], 34));             // rises
  add(108.5, st([0.08, 0.98, -5.5], [0.07, 0.98, -5.53], [0, 0.97, -5.98], [0, 0.97, -5.98], 30));                // another new shore
  add(110.62, st([-0.1, 0.88, -5.62], [-0.09, 0.88, -5.64], [-0.04, 0.85, -5.88], [-0.04, 0.85, -5.88], 28));      // we plant our old flags
  add(112.3, st([0.2, 1.05, -5.35], [0.18, 1.04, -5.4], [0, 0.88, -5.95], [0, 0.88, -5.95], 36));                  // and go looking for more
  add(113.55, st([0.06, 1.3, -5.42], [0.05, 1.28, -5.45], [0, 0.76, -5.93], [0, 0.76, -5.93], 32));               // the Gardener card
  add(115.3, st([-0.3, 1.0, -5.3], [-0.28, 0.98, -5.36], [0, 0.9, -5.95], [0, 0.9, -5.95], 34));                  // we're finally free
  add(117.57, st([0.02, 0.805, -5.6], [0.02, 0.8, -5.63], [0.0, 0.795, -5.87], [0.0, 0.795, -5.87], 28));         // (the Viking with his one tomato, in the card)
  add(119.3, st([-1.25, 1.18, -3.35], [-1.25, 1.18, -3.35], [-1.9, 1.02, -2.36], [-1.9, 1.02, -2.36], 40));       // to grow our tomatoes — pose 1
  add(120.48, st([-1.4, 1.2, -3.1], [-1.4, 1.2, -3.1], [-1.95, 1.12, -2.36], [-1.95, 1.12, -2.36], 34));          // pose 2: his raised palm
  add(121.52, st([-1.2, 1.0, -3.4], [-1.2, 1.0, -3.4], [-1.95, 1.15, -2.38], [-1.95, 1.15, -2.38], 40));          // pose 3: voluntarily
  add(122.1, st([0, 2.4, 9.0], [0, 2.45, 8.6], [0, 0.9, -4], [0, 0.9, -4], 42));                                   // the hall erupts
  add(124.0, st([0.4, 2.2, -7.25], [0.4, 2.2, -7.25], [0, 1.0, 1.0], [0, 1.0, 1.0], 44));                          // freeze: the Fool…
  add(124.38, st([-0.03, 0.79, -5.84], [-0.025, 0.788, -5.82], [0, 0.8, -5.62], [0, 0.8, -5.62], 32));            // her hand lifts the corner of his card, for us
  add(126.64, st([-0.01, 0.785, -5.76], [-0.01, 0.785, -5.75], [0, 0.81, -5.63], [0, 0.81, -5.63], 22));           // the figure turns its head
  add(128.91, st([-0.66, 1.12, -6.1], [-0.62, 1.11, -6.06], [0.02, 0.95, -5.45], [0.02, 0.95, -5.45], 46));         // he looks at his rocket; a robot sets a tomato beside it
  // ---------------- hook 3, bridge
  hookShots(2);
  add(151.5, st([-0.17, 1.12, -5.83], [-0.17, 1.1, -5.84], [-0.17, 0.76, -5.92], [-0.17, 0.76, -5.92], 34, UPZ));   // the Magician
  add(153.73, st([0.0, 1.1, -5.68], [0.0, 1.08, -5.7], [0.0, 0.76, -5.93], [0.0, 0.76, -5.93], 34, UPZ));          // the Tower
  add(156.03, st([0.17, 1.1, -5.68], [0.17, 1.08, -5.7], [0.17, 0.76, -5.92], [0.17, 0.76, -5.92], 34, UPZ));      // the Star
  add(158.29, st([0.42, 0.95, -5.52], [0.4, 0.95, -5.53], [0, 0.8, -5.64], [0, 0.82, -5.64], 34));                // the Fool asks what we lost
  add(160.6, st([0, 1.12, -5.76], [0, 1.08, -5.76], [0, 0.76, -5.75], [0, 0.76, -5.75], 26, UPZ));                // if it does the thinking
  add(162.88, st([0.13, 0.88, -5.58], [0.12, 0.88, -5.6], [0, 0.77, -5.76], [0, 0.77, -5.76], 30));               // if it makes the art
  add(165.14, st([-0.34, 1.0, -6.1], [-0.32, 0.99, -6.07], [0.04, 1.02, -5.42], [0.04, 1.02, -5.42], 42));          // did we lose our purpose
  add(167.4, st([0.01, 1.5, -5.76], [0.01, 1.48, -5.76], [0.01, 0.76, -5.755], [0.01, 0.76, -5.755], 11, UPZ));   // or were we free from the start? (one human line)
  // ---------------- refrain 2, hook 4
  add(169.5, st([-1.05, 1.12, -5.95], [-0.98, 1.14, -5.95], [0, 1.0, -5.95], [0, 1.1, -5.95], 40));
  add(171.92, st([-1.3, 1.2, -5.6], [-1.22, 1.2, -5.65], [0, 1.18, -5.95], [0, 1.18, -5.95], 38));
  add(174.2, st([0, 1.92, -4.45], [0, 1.9, -4.55], [0, 1.3, -6.05], [0, 1.3, -6.05], 44));
  add(176.48, st([0.25, 1.25, -5.0], [0.22, 1.24, -5.1], [0, 1.2, -6.0], [0, 1.2, -6.0], 36));
  add(178.74, st([-1.4, 1.35, -5.2], [-1.3, 1.3, -5.3], [0, 1.0, -6.0], [0, 0.95, -6.0], 44));
  add(181.0, st([0.36, 1.15, -4.98], [0.33, 1.12, -5.05], [0, 0.95, -5.7], [0, 0.9, -5.65], 36));
  add(183.26, st([-1.9, 1.15, -5.95], [-1.85, 1.15, -5.95], [0, 1.1, -5.95], [0, 1.1, -5.95], 38));                 // the choice belongs to you and me
  add(185.53, st([0, 3.4, -4.6], [0, 3.5, -4.8], [0, 0.6, 3.0], [0, 0.6, 3.0], 46));                               // the stomps
  hookShots(3);
  // ---------------- outro
  add(207.2, st([0.0, 1.32, -5.62], [0.0, 1.3, -5.62], [0.0, 0.76, -5.6], [0.0, 0.76, -5.6], 34, UPZ));           // One last card: he turns it over
  // the arc over the card: left (MARS) → right (RAGNARÖK) → straight down (the Fool, 0 at the top of the frame)
  X.outroView = (t) => t < 208.6 ? -1 : t < 209.92 ? lerp(-1, 1, easeIO(clamp((t - 208.75) / 0.9))) : 0;
  add(208.6, (t, u) => { const v = X.outroView(t); const c = SPOT.place; return [V(c.x + 0.16 * v, c.y + 0.36, c.z + 0.02), c.clone(), 30, UPZ]; });
  add(209.92, (t, u) => { const c = X.tf.localToWorld(V(0, 0.026, 0)); return [V(c.x, c.y + lerp(0.2, 0.17, u), c.z), c, 30, UPZ]; });          // the Fool, the 0
  add(211.68, (t, u) => { const c = X.tf.localToWorld(V(0, 0.012, 0)); return [V(c.x, c.y + lerp(0.17, 0.045, easeIn(u)), c.z), c, 30, UPZ]; });  // push into the card
  add(212.2, (t, u) => X.head.cam('edge', t, u));
  add(213.76, (t, u) => X.head.cam('stars', t, u));
  add(216.4, (t, u) => X.head.cam('told', t, u));
  add(218.8, (t, u) => X.head.cam('turn', t, u));
  add(221.04, (t, u) => X.head.cam('asked', t, u));
  add(226.64, (t, u) => X.head.cam('how', t, u));
  // ---------------- coda
  add(227.9, st([0, 3.6, -4.9], [0, 3.75, -5.1], [0, 0.6, 3.0], [0, 0.6, 3.0], 46));                               // the slam on the drum hit
  add(228.97, st([0.0, 1.5, -5.4], [0.0, 1.48, -5.45], [0, 0.76, -6.0], [0, 0.76, -6.0], 38));                    // she sweeps up the cards
  add(231.22, st([0, 1.62, -5.72], [0, 1.6, -5.76], [0, 1.02, -6.38], [0, 1.02, -6.38], 40));                      // and shuffles
  add(233.49, st([0, 0.98, -5.32], [0, 0.97, -5.32], [0, 0.78, -5.75], [0, 0.78, -5.75], 40));                     // and slides the deck to you
  S.sort((a, b) => a.t - b.t);
  return S;
}
export function camFull(t) {
  const S = K.shots; let i = 0; while (i + 1 < S.length && t >= S[i + 1].t) i++;
  const s = S[i], t1 = i + 1 < S.length ? S[i + 1].t : 245;
  let [p, look, fov, up] = s.cam(t, clamp((t - s.t) / (t1 - s.t)));
  if (X.VERT) [p, look, fov] = X.vfix(s.t.toFixed(2), p, look, fov, up);
  return { p, look, fov, up: up || V(0, 1, 0), i, t0: s.t };
}

// ---------------------------------------------------------------- per frame
export function frameFull(t) {
  reset(t);
  const s = sectionAt(t);
  if (s[0] === 'hook') hookFrame(t, s[3]);
  else if (s[0] === 'v1') v1Frame(t);
  else if (s[0] === 'ref') refFrame(t, s[3]);
  else if (s[0] === 'v2') v2Frame(t);
  else if (s[0] === 'bridge') bridgeFrame(t);
  else if (s[0] === 'outro') outroFrame(t);
  else codaFrame(t);
  return s;
}
export { K as KEYS };
