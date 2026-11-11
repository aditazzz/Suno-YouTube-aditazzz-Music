// V2 -> POST2a, s28-s45 (73.12-116.21): the 2.5D city, one continuous picture registered for every shot id s28..s45 (the
// hook's pattern), a pure function of film time. ROUGHCUT_PLAN step 5; PALETTE.md V2+PRE2 and CH2+POST2a.
//
// It starts on CH1's last frame (the pink dot r 74 at 960,470, rings, dot grid, bg #0a0d16, camera z 1) and ends on the
// s46 hand-off (the push toward one lit window keeps going; the 3D city matches sky #0a0f1a, buildings, windows #ffcf7a).
//
//   s28 city    the dot bursts into the city's windows (pink -> peach -> amber in 6 frames), buildings rise on 16ths
//   s29 rain    rain on the left half only, hard edge at world x 960, puddles left; a tiny guy with an umbrella on the edge
//   s30 car     the GT3 RS rolls in (constant braking), stops on the downbeat with a brake dip; the camera stops with it
//   s31 lights  the traffic lights (blinking on the hats) stretch in and bonk on the downbeat; both green forever
//   s32 guys    windows light in a cascade, a tiny guy in each (low amber); one window has a pigeon
//   s33 wired   everyone types on the 16th hats; the camera pushes into one window row: readable screens
//   s34 pigeons the flock wheels into a circle on the downbeat and climbs on beats 2 and 3; the camera tilts up with them
//   s35 gravity everything floats; the rain hangs (still with its hard edge)
//   s36 birds   everything drops back with a squash, except the birds (one floats upside down)
//   s37 zero-g  E2 silence: everything floats, the guys float out of their windows typing; the cursor drags the car down
//   s38 impact  the car lands on bar 49: warm flash 2 frames, shake, shockwave; the city jumps bigger and brighter
//   s39 fire    fireworks in CH1's flame shapes; the tallest building lights its crown; crane up
//   s40 spin    the city turns on its turntable; 'shine' on beat 3: a light sweep across every facade
//   s41 whole   every building bounces on the kick, windows strobe; one building is a beat late
//   s42 louder  pull back: the city doubles (a taller skyline rises behind), rings of sound over the rooftops
//   s43 tower   the bass tower rises floor by floor from the bass stem, the red button on top; tilt up
//   s44 run     full speed (traffic streaks, windows cycling), big arc; bar 57 locks into one still pose
//   s45 pass 1  'shading': a render wipe switches on soft shading and AO; label in the corner; push toward a lit window
import React, { useLayoutEffect, useRef } from 'react';
import { AbsoluteFill } from 'remotion';
import { C, FONT, LAYOUTS, MED, P, mixC, rgbaOf, useLayout, useT, Layout } from '../../theme';
import { barCharPos } from '../../components/barWrap';
const LAYOUT16 = LAYOUTS['16x9'];
import { beatPos, hats, hatEnv, kickEnv, kicks, lines, promptAt, sinceHit, tshot } from '../../timing';
import type { ShotProps } from '../../shots';
import { clamp, easeIn2, easeInOut3, easeOut3, impact, lerp, prog, smooth, spring } from '../hook/anim';
import { BEAT, BURSTS, HIGHER, LOCK, SHINE, SIXTEENTH, T, TOUCH, inSilence } from './times';
import {
  BLDS, Bld, CAR, CAR_Z, CROWN, DROPS, F, FLOATERS, FLOCK, GROUND, LAMP, LATE, LIGHTS, LIGHT_Z, PIGEON_Z, PIVOT, PUSHWIN,
  RAIN_EDGE, RAIN_SPAN, RAIN_TOP, RAIN_Z, TARGET, TOWER, UMBRELLA, Win, hash,
} from './world';
import { Cam, camAt } from './cam';
import { cursor, flame, gt3, mixHexA, pigeon, rr, trafficLight } from './draw';
import bassRaw from '../../data/bass_city.json';

type X = CanvasRenderingContext2D;
const V2 = P.v2, CH2 = P.ch2;
const bass = bassRaw as { f0: number; fps: number; v: number[] };
const bassAt = (t: number) => { const f = t * bass.fps - bass.f0, i = Math.floor(f), k = f - i; const g = (j: number) => bass.v[Math.max(0, Math.min(bass.v.length - 1, j))]; return g(i) + (g(i + 1) - g(i)) * k; };

// ---------- projection (pinhole, turntable yaw about PIVOT, near-plane clipping) ----------
type V3 = [number, number, number];
type Pt = { x: number; y: number; s: number };
const NEAR = 40;
// 9:16 (LAYOUT_916.md, rc_916): the 16:9 picture x1.25 (F 2000), the road (GROUND at the identity camera) on y 1060, so
// the 1080 slice holds ~864 px of the 1920 city; the camera x follows each shot's subject (CITY9 / fx9 below).
export const CITY9 = { K: 1.25, SCY: 1060 - 1.25 * (GROUND - 540) }; // principal point y 722.5
function makeView(cam: Cam, L: Layout, fx = 960, dy9 = 0) {
  const SCX = L.W / 2, SCY = L.fmt === '16x9' ? 540 : CITY9.SCY + dy9;
  const cs = Math.cos(cam.yaw), sn = Math.sin(cam.yaw);
  const toCam = (x: number, y: number, z: number): V3 => {
    const rx = x - PIVOT.x, rz = z - PIVOT.z;
    return [PIVOT.x + rx * cs - rz * sn - cam.x, y - cam.y, F + PIVOT.z + rx * sn + rz * cs - cam.dz];
  };
  const K = CITY9.K, PX9 = SCX + K * (960 - fx);
  const fromCam = L.fmt === '16x9' ? (p: V3): Pt => { const s = F / p[2]; return { x: SCX + p[0] * s + cam.shx, y: SCY + p[1] * s + cam.shy, s }; }
    : (p: V3): Pt => { const s = (K * F) / p[2]; return { x: PX9 + p[0] * s + K * cam.shx, y: SCY + p[1] * s + K * cam.shy, s }; };
  const proj = (x: number, y: number, z: number): Pt | null => { const p = toCam(x, y, z); return p[2] < NEAR ? null : fromCam(p); };
  /** polygon (world) -> screen points, clipped at the near plane */
  const poly = (pts: V3[]): Pt[] => {
    const cp = pts.map((p) => toCam(p[0], p[1], p[2]));
    const out: V3[] = [];
    for (let i = 0; i < cp.length; i++) {
      const a = cp[i], b = cp[(i + 1) % cp.length], ain = a[2] >= NEAR, bin = b[2] >= NEAR;
      if (ain) out.push(a);
      if (ain !== bin) { const k = (NEAR - a[2]) / (b[2] - a[2]); out.push([a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k, NEAR]); }
    }
    return out.map(fromCam);
  };
  return { proj, poly, toCam, SCX, SCY };
}
type View = ReturnType<typeof makeView>;
const path = (c: X, pts: Pt[]) => { c.beginPath(); pts.forEach((p, i) => (i ? c.lineTo(p.x, p.y) : c.moveTo(p.x, p.y))); c.closePath(); };
const fillPoly = (c: X, pts: Pt[], fill: string | CanvasGradient) => { if (pts.length < 3) return; path(c, pts); c.fillStyle = fill; c.fill(); };

// ---------- the state of the world at t (pure) ----------
/** building rise 0..1 (spring, overshoot) */
const riseOf = (b: Bld, t: number) => {
  if (b.layer === 'rear') { const st = T.LOUD + Math.abs(b.x + b.w / 2 - 960) / 2600; return clamp(spring(t - st, 1.6, 0.62), 0, 1.2); }
  return clamp(spring(t - (T.CITY + 0.1 + b.order * SIXTEENTH), 2.1, 0.58), 0, 1.2); // the dot empties first (0.1 s)
};
/** city height scale: s38 jumps bigger, s41 bounces on the kick (one building a beat late) */
const heightOf = (b: Bld, t: number) => {
  let h = 1 + 0.1 * clamp(spring(t - T.IMPACT, 2.2, 0.45), 0, 1.4);
  if (t >= T.WHOLE && t < LOCK) {
    const tt = b === LATE ? t - BEAT : t;
    const on = smooth(prog(t, T.WHOLE - 0.05, T.WHOLE + 0.05)) * (1 - smooth(prog(t, T.LOUD, T.LOUD + 1.2)));
    h *= 1 + 0.06 * on * kickEnv(tt, 0.14) * (b.layer === 'front' ? 1 : 0.6);
  }
  return h;
};
// gravity (s35-s38): lift above rest (world px, up = positive)
type FloatO = { A: number; ph: number; bird?: boolean };
const up = (dt: number, o: FloatO) => (dt <= 0 ? 0 : o.A * (1 - Math.exp(-dt / 0.8)) + 7 * Math.sin(dt * 1.7 + o.ph) * (1 - Math.exp(-dt / 0.5)));
const G = 2600;
function fallFrom(h0: number, dt: number) { const h = h0 - 0.5 * G * dt * dt; return { h: Math.max(0, h), landed: h <= 0, tl: Math.sqrt((2 * Math.max(0, h0)) / G) }; }
/** lift + squash for a floating object at t */
function floatOf(t: number, o: FloatO): { h: number; sq: number } {
  if (t < T.GRAV) return { h: 0, sq: 1 };
  if (t < T.BIRDS) return { h: up(t - T.GRAV, o), sq: 1 };
  if (o.bird) return { h: up(t - T.GRAV, o), sq: 1 };
  if (t < T.ZERO) { const f = fallFrom(up(T.BIRDS - T.GRAV, o), t - T.BIRDS); return { h: f.h, sq: f.landed ? 1 - 0.22 * impact(t - T.BIRDS - f.tl, 3.2, 9) : 1 }; }
  if (t < T.IMPACT) return { h: up(t - T.ZERO, o), sq: 1 };
  const f = fallFrom(up(T.IMPACT - T.ZERO, o), t - T.IMPACT);
  return { h: f.h, sq: f.landed ? 1 - 0.22 * impact(t - T.IMPACT - f.tl, 3.2, 9) : 1 };
}
// rain clock: seconds of falling (hangs while gravity is off, s35 and s37)
const rainSpeed = (t: number) => {
  const hang = (a: number, b: number) => smooth(prog(t, a, a + 0.3)) * (1 - smooth(prog(t, b, b + 0.2)));
  return 1 - 0.97 * Math.max(hang(T.GRAV, T.BIRDS), hang(T.ZERO, T.IMPACT));
};
const rainClock = (t: number) => { if (t <= T.RAIN) return 0; let s = 0; const dt = 1 / 120; for (let x = T.RAIN; x < t; x += dt) s += rainSpeed(x) * Math.min(dt, t - x); return s; };

/** the car: world x, lift (px), pitch, squash, wheel angle */
function carAt(t: number) {
  const D = 2300, t0 = T.CAR - 1.0;
  let x = CAR.x, pitch = 0, wheel = 0;
  if (t < t0) return null;
  if (t < T.CAR) { const k = prog(t, t0, T.CAR); x = CAR.x - D * (1 - k) * (1 - k); pitch = 0.02 * smooth(prog(t, t0, t0 + 0.3)); }
  else pitch = 0.02 * impact(t - T.CAR, 1.7, 5);
  wheel = (x - (CAR.x - D)) / 44;
  // gravity
  let lift = 0, sq = 1, grab = 0, rot = 0;
  const o: FloatO = { A: 150, ph: 0.6 };
  if (t >= T.GRAV && t < T.ZERO) { const f = floatOf(t, o); lift = f.h; sq = f.sq; rot = -0.04 * Math.sin((t - T.GRAV) * 1.3) * (lift / 150); }
  if (t >= T.ZERO && t < T.IMPACT + 0.6) {
    // s37: floats up in the silence; the cursor grabs it (93.30) and drags it down to touch on beat 4 (TOUCH); released,
    // it settles a hair and lands with a squash on bar 49 (the impact is the drop)
    const tg = T.ZERO + 0.55, hg = up(tg - T.ZERO, { A: 190, ph: 1.1 });
    if (t < tg) lift = up(t - T.ZERO, { A: 190, ph: 1.1 });
    else if (t < TOUCH) { const k = easeInOut3(prog(t, tg, TOUCH)); lift = lerp(hg, 14, k); grab = 1; }
    else if (t < T.IMPACT) { const k = prog(t, TOUCH, T.IMPACT); lift = 14 + 26 * Math.sin(Math.PI * Math.min(1, k * 1.15)) * (1 - k) - 14 * easeIn2(k); grab = 1 - smooth(prog(t, TOUCH, TOUCH + 0.15)); }
    else { lift = 0; sq = 1 - 0.2 * impact(t - T.IMPACT, 3.0, 8); }
    rot = t < TOUCH ? -0.05 * Math.sin((t - T.ZERO) * 1.1) * clamp(lift / 120) : 0;
  }
  return { x, lift: Math.max(0, lift), pitch, sq, wheel, grab, rot };
}

// window light 0..1 and colour at t
function windowLight(b: Bld, w: Win, t: number, arrive: number): { k: number; cool: boolean; guy: boolean } {
  if (b.layer === 'rear') return { k: w.lit0 ? 0.8 : 0, cool: false, guy: false };
  let lit = w.lit0, k = lit ? smooth(prog(t, arrive, arrive + 0.1)) : 0, guy = w.guy0;
  const bright = lerp(1, 1, 0);
  // s32: the cascade (low amber), a guy in each lit window
  const cascade = T.GUYS - 0.05 + clamp((w.x + 200) / 2400) * 0.75;
  if (!lit && w.r1 < 0.72 && t >= cascade) { lit = true; k = 0.62 * smooth(prog(t, cascade, cascade + 0.12)); }
  if (lit && t >= cascade) guy = true;
  // s38: brighter: every lit window to full, more windows light outward from the car
  if (t >= T.IMPACT) {
    const ti = T.IMPACT + Math.abs(w.x - CAR.x) / 2600;
    if (!w.lit0 && w.r1 < 0.72) k = lerp(0.62, 1, smooth(prog(t, T.IMPACT, T.IMPACT + 0.2)));
    if (!lit && w.r1 < 0.82) { lit = true; k = smooth(prog(t, ti, ti + 0.1)); }
  }
  // s41: strobe in sync (columns alternate on the beat)
  if (t >= T.WHOLE && t < T.LOUD + 0.6 && lit) { const bi = Math.floor(beatPos(t)); const on = (w.col + bi) % 2 === 0; k *= on ? 1 : 0.55 + 0.45 * smooth(prog(t, T.LOUD, T.LOUD + 0.6)); }
  // s44: full speed: windows cycle (frozen at the lock)
  if (t >= T.RUN) {
    const tr = Math.min(t, LOCK), on = smooth(prog(t, T.RUN, T.RUN + 0.3));
    if (on > 0) { const cyc = hash(Math.floor(w.r2 * 1000), Math.floor((tr - T.RUN) * 9)) < 0.6; k = lerp(k, cyc ? 1 : 0, on); lit = lit || cyc; }
  }
  return { k: clamp(k * bright), cool: w.cool, guy: guy && lit };
}

// the scatter particle arrival time for a lit window of a rising building (s28)
const arriveOf = (b: Bld, w: Win) => T.CITY + 0.1 + b.order * SIXTEENTH + 0.3 + w.r3 * 0.28;

// ---------- drawing ----------
const COL = {
  front: '#1d2a40', frontShade: '#243349', back: '#152034', far: '#111a2b', rear: '#17213a', side: '#141d2c', roof: '#26344d',
  winOff: '#172235', road: '#0e1522', kerb: '#24324a',
};

function drawBuilding(c: X, v: View, b: Bld, t: number, st: { shade: number; wipeY: number; sweep: number; fireK: number; detail: boolean }) {
  const rise = riseOf(b, t);
  if (rise <= 0.001) return;
  const hs = heightOf(b, t);
  const H = b.h * hs, drop = (1 - rise) * (H + 40);
  const z0 = b.z, z1 = b.z + b.d, x0 = b.x, x1 = b.x + b.w;
  const yb = b.base + drop, yt = b.base - H + drop;
  const front = v.poly([[x0, yt, z0], [x1, yt, z0], [x1, yb, z0], [x0, yb, z0]]);
  if (front.length < 3) return;
  const minx = Math.min(...front.map((p) => p.x)), maxx = Math.max(...front.map((p) => p.x));
  const BL = v.proj(x0, yt, z1), BR = v.proj(x1, yt, z1), FL = v.proj(x0, yt, z0), FR = v.proj(x1, yt, z0);
  if (maxx < -400 || minx > v.SCX * 2 + 400) return;
  c.save();
  if (rise < 1) { // rising out of the ground: clip at the building's own base line
    const a = v.proj(x0 - 400, b.base, z0), d = v.proj(x1 + 400, b.base, z0);
    if (a && d) { c.beginPath(); c.moveTo(a.x, a.y); c.lineTo(d.x, d.y); c.lineTo(d.x, -4000); c.lineTo(a.x, -4000); c.closePath(); c.clip(); }
  }
  const base = b.layer === 'front' ? COL.front : b.layer === 'back' ? COL.back : b.layer === 'far' ? COL.far : COL.rear;
  // side faces (visible ones only) and roof
  if (BR && FR && BR.x > FR.x + 0.5) fillPoly(c, v.poly([[x1, yt, z0], [x1, yt, z1], [x1, yb, z1], [x1, yb, z0]]), COL.side);
  if (BL && FL && BL.x < FL.x - 0.5) fillPoly(c, v.poly([[x0, yt, z1], [x0, yt, z0], [x0, yb, z0], [x0, yb, z1]]), COL.side);
  if (BL && FL && BL.y < FL.y - 0.5) fillPoly(c, v.poly([[x0, yt, z0], [x1, yt, z0], [x1, yt, z1], [x0, yt, z1]]), COL.roof);
  fillPoly(c, front, base);
  if (b.layer === 'front') fillPoly(c, v.poly([[x0, yt, z0], [x0 + b.w * 0.18, yt, z0], [x0 + b.w * 0.18, yb, z0], [x0, yb, z0]]), COL.frontShade);
  // s45 shading pass: warm top, cool AO toward the base (under the wipe)
  if (st.shade > 0 && st.wipeY > -1000) {
    c.save(); c.beginPath(); c.rect(-5000, -5000, 12000, st.wipeY + 5000); c.clip();
    const p0 = v.proj(x0, yt, z0), p1 = v.proj(x0, yb, z0);
    if (p0 && p1) {
      const g = c.createLinearGradient(0, p0.y, 0, p1.y);
      g.addColorStop(0, `rgba(255,243,220,${0.07 * st.shade})`); g.addColorStop(0.55, 'rgba(10,15,26,0)'); g.addColorStop(1, `rgba(5,8,16,${0.5 * st.shade})`);
      fillPoly(c, front, g);
    }
    if (BR && FR && BR.x > FR.x + 0.5) fillPoly(c, v.poly([[x1, yt, z0], [x1, yt, z1], [x1, yb, z1], [x1, yb, z0]]), `rgba(5,8,16,${0.35 * st.shade})`);
    c.restore();
  }
  // s39: the fireworks warm the facades
  if (st.fireK > 0.01 && b.layer !== 'far') fillPoly(c, front, `rgba(255,207,122,${0.07 * st.fireK})`);
  // windows
  if (b.wins.length) drawWindows(c, v, b, t, yt - (b.base - b.h), hs, drop, st.detail);
  // s39: the crown (the tallest building's roof light)
  if (b === CROWN && t >= T.FIRE) {
    const k = smooth(prog(t, T.FIRE, T.FIRE + 0.25));
    const a = v.proj(x0 + 6, yt - 6, z0), d = v.proj(x1 - 6, yt + 4, z0);
    if (a && d) { c.save(); c.shadowColor = V2.window; c.shadowBlur = 30 * k; c.fillStyle = mixHexA(COL.front, V2.window, k); c.fillRect(a.x, a.y, d.x - a.x, d.y - a.y); c.restore(); }
  }
  // s40: 'shine' sweep across every facade
  if (st.sweep > 0 && st.sweep < 1 && b.layer !== 'far') {
    c.save(); path(c, front); c.clip();
    const bx = lerp(-500, v.SCX * 2 + 500, st.sweep) + (minx - v.SCX) * 0.15;
    const g = c.createLinearGradient(bx - 160, 0, bx + 160, 0);
    g.addColorStop(0, 'rgba(255,243,220,0)'); g.addColorStop(0.5, 'rgba(255,243,220,0.3)'); g.addColorStop(1, 'rgba(255,243,220,0)');
    c.fillStyle = g; c.fillRect(minx - 10, -5000, maxx - minx + 20, 12000); c.restore();
  }
  c.restore();
}

function drawWindows(c: X, v: View, b: Bld, t: number, _dy: number, hs: number, drop: number, detail: boolean) {
  // windows keep their spacing; the building's height scale stretches the facade from the base
  const yOf = (y: number) => b.base - (b.base - y) * hs + drop;
  const typing = t >= T.WIRED ? hatEnv(t, 0.06) : 0;
  for (const w of b.wins) {
    const p = v.proj(w.x, yOf(w.y), b.z);
    if (!p) continue;
    const ws = 18 * p.s, hh = 24 * p.s * hs;
    if (p.x > v.SCX * 2 + 10 || p.x + ws < -10 || p.y > 2000 || p.y + hh < -10) continue;
    const L = windowLight(b, w, t, arriveOf(b, w));
    const lit = L.cool ? V2.windowCool : V2.window;
    const out = floatOut(w, t);
    if (ws > 46 && L.k > 0.3) { drawInterior(c, p.x, p.y, p.s, hs, t, w, clamp((ws - 46) / 40), L.k, out || !L.guy ? 0 : 1, L.cool, typing); continue; }
    c.fillStyle = L.k <= 0.001 ? COL.winOff : mixHexA(COL.winOff, lit, L.k);
    c.fillRect(p.x, p.y, ws, hh);
    if (L.guy && L.k > 0.3 && !out) {
      const s = p.s, jy = -0.9 * typing * ((w.col + w.row) % 2 ? 1 : 0.6);
      c.fillStyle = '#141b2a'; c.beginPath(); c.arc(p.x + 9 * s, p.y + (12 + jy) * s, 3.4 * s, 0, Math.PI * 2); c.fill();
      c.fillRect(p.x + 4 * s, p.y + (16 + jy) * s, 10 * s, 8 * s);
      c.fillStyle = P.ui.promptText; c.fillRect(p.x + 3 * s, p.y + 21 * s, 12 * s, 2 * s);
      // s32 egg: one window has two guys (one is the pigeon)
      if (w === PIGEON_WIN) { c.save(); c.strokeStyle = '#141b2a'; c.lineWidth = 1.6 * s; c.beginPath(); c.moveTo(p.x + 12 * s, p.y + 10 * s); c.quadraticCurveTo(p.x + 14 * s, p.y + 7 * s, p.x + 16 * s, p.y + 10 * s); c.stroke(); c.restore(); }
    }
  }
}
/** s33: the wider monitor screen in the three target windows (window units, window 18 x 24) and the sleeper's index */
const SCR = { x: 1.8, y: 3.8, w: 14.4, h: 7.4 };
const SLEEPER = 2;
const PIGEON_WIN = TARGET.b.wins.find((w) => w.row === Math.max(0, TARGET.row - 2) && w.col === TARGET.c0 + 1) ?? TARGET.wins[0];

/** a window at close range: warm room lit from a ceiling strip, the monitor on the far wall, the guy from behind
 *  (silhouette, chair back), typing on the hats. Clipped to the window; a sill under it so the facade reads as built. */
function drawInterior(c: X, x: number, y: number, s: number, hs: number, t: number, w: Win, mixK: number, k: number, guyOn: number, cool: boolean, typing: number) {
  c.save(); c.translate(x, y); c.scale(s, s * hs);
  const lit = cool ? V2.windowCool : V2.window;
  c.save(); c.beginPath(); c.rect(0, 0, 18, 24); c.clip();
  c.fillStyle = mixHexA(COL.winOff, lit, k); c.fillRect(0, 0, 18, 24);
  if (guyOn && mixK < 1) { // the far-away guy (approved pictogram) hands over to the close-up one: no frame without a guy
    const jy = TARGET.wins.indexOf(w) === SLEEPER ? 0.8 : -0.9 * typing * ((w.col + w.row) % 2 ? 1 : 0.6);
    c.globalAlpha = 1 - mixK; c.fillStyle = '#141b2a'; c.beginPath(); c.arc(9, 12 + jy, 3.4, 0, Math.PI * 2); c.fill();
    c.fillRect(4, 16 + jy, 10, 8); c.fillStyle = P.ui.promptText; c.fillRect(3, 21, 12, 2);
  }
  c.globalAlpha = mixK;
  const g = c.createLinearGradient(0, 0, 0, 24);
  g.addColorStop(0, cool ? '#f1f4f9' : '#ffdc9c'); g.addColorStop(1, cool ? '#c3cddd' : '#e6ae5c');
  c.fillStyle = g; c.fillRect(0, 0, 18, 24);
  c.fillStyle = cool ? '#f7f9fc' : P.ch2.flameCore; c.fillRect(4, 0, 10, 0.7);                 // ceiling light strip (the source)
  const hat = inSilence(t) ? 0.4 : hatEnv(t, 0.06);
  // s33's three target windows get a wider monitor (SCR) so their screens read at 38 px; every other window keeps the original
  const tg = TARGET.wins.indexOf(w), asleep = tg === SLEEPER;
  const m = tg >= 0 ? SCR : { x: 2.6, y: 4.6, w: 12.8, h: 6.8 };
  c.fillStyle = '#232c3f'; rr(c, m.x - 0.4, m.y - 0.4, m.w + 0.8, m.h + 0.8, 0.7); c.fill();         // monitor bezel
  c.fillStyle = '#0e0e14'; rr(c, m.x, m.y, m.w, m.h, 0.4); c.fill();                                 // screen (text: <Screens/>)
  c.fillStyle = `rgba(232,238,248,${0.07 + 0.05 * hat})`; c.fillRect(m.x, m.y, m.w, m.h);
  c.fillStyle = '#232c3f'; c.fillRect(8.4, m.y + m.h + 0.4, 1.2, 13.1 - (m.y + m.h + 0.4)); c.fillRect(6.8, 13.1, 4.4, 0.5);
  c.fillStyle = '#141d2c'; c.fillRect(0, 17.2, 18, 0.9);                                         // desk
  c.fillStyle = 'rgba(20,29,44,.18)'; c.fillRect(0, 18.1, 18, 1.4);
  if (guyOn && asleep) { // s33 egg: one guy asleep on his keyboard (no typing; slow breathing; head down on his forearms)
    const br = 0.5 + 0.5 * Math.sin((2 * Math.PI * t) / 3.4), by = 0.18 * br;
    c.fillStyle = '#141d2c';
    rr(c, 1.2, 16.3 + by * 0.4, 6.6, 1.7, 0.85); c.fill(); rr(c, 10.2, 16.3 + by * 0.4, 6.6, 1.7, 0.85); c.fill(); // forearms spread on the desk
    rr(c, 4.4, 17.6 + by, 9.2, 9, 3.4); c.fill();                                                                 // rounded, slumped back
    c.beginPath(); c.ellipse(8.4, 16.3 + by * 0.6, 2.0, 1.75, -0.35, 0, Math.PI * 2); c.fill();                  // head down on the keys, tilted
    c.fillStyle = '#0d1420'; rr(c, 5.5, 19.6, 7, 6, 1.3); c.fill();                                              // chair back
    // z's drift up off him and fade (each 2.4 s, staggered), in the warm wall right of the monitor stand
    c.fillStyle = '#141d2c'; c.textAlign = 'center'; c.textBaseline = 'middle';
    for (let i = 0; i < 3; i++) {
      const ph = (((t - T.GUYS) / 2.4 + i / 3) % 1 + 1) % 1, sz = 1.3 + 1.1 * ph;
      c.globalAlpha = mixK * Math.sin(Math.PI * ph) * 0.85;
      c.font = `700 ${sz}px ${FONT}`;
      c.fillText('z', 13.0 + 3.0 * ph + 0.35 * Math.sin(ph * 7 + i), 15.9 - 3.6 * ph);
    }
    c.globalAlpha = mixK;
  } else if (guyOn) {
    const jy = -0.25 * hat * (w.col % 2 ? 1 : 0.7), el = 0.35 * hat;
    c.fillStyle = '#141d2c';
    c.beginPath(); c.arc(9, 14.3 + jy, 1.95, 0, Math.PI * 2); c.fill();                          // head
    c.fillRect(8.3, 15.9 + jy, 1.4, 1.2);                                                         // neck
    rr(c, 4.9, 16.7 + jy, 8.2, 9, 2.6); c.fill();                                                 // shoulders
    rr(c, 3.7, 17.6 + jy - el, 1.7, 2.6, 0.7); c.fill(); rr(c, 12.6, 17.6 + jy + el, 1.7, 2.6, 0.7); c.fill(); // elbows, typing
    c.fillStyle = '#0d1420'; rr(c, 5.5, 19.6, 7, 6, 1.3); c.fill();                               // chair back
  }
  c.globalAlpha = 1;
  c.fillStyle = 'rgba(5,8,16,.32)'; c.fillRect(0, 0, 18, 0.8); c.fillRect(0, 0, 0.6, 24);         // recess shadow (top/left)
  c.restore();
  c.globalAlpha = mixK; c.fillStyle = '#2b3a56'; c.fillRect(-1.2, 24, 20.4, 1.1); c.fillStyle = '#121a2a'; c.fillRect(-1.2, 25.1, 20.4, 0.5); // sill
  c.restore();
}

/** s37: guys floating out of their windows; null when the guy is home */
function floatOut(w: Win, t: number) {
  if (t < T.ZERO || t > T.IMPACT + 0.7) return null;
  const f = FLOATERS.find((q) => q.w === w); if (!f) return null;
  return f;
}

export const City: React.FC<ShotProps> = () => {
  const t = useT();
  const L = useLayout();
  const ref = useRef<HTMLCanvasElement>(null);
  const cam = camAt(t);
  useLayoutEffect(() => {
    const cv = ref.current; if (!cv) return;
    const c = cv.getContext('2d')!;
    drawCity(c, t, L, cam);
  }, [t, L]);
  const v = viewOf(cam, L, t);
  return (
    <AbsoluteFill>
      <canvas ref={ref} width={L.W} height={L.H} style={{ position: 'absolute', left: 0, top: 0, width: L.W, height: L.H }} />
      {L.fmt === '16x9' ? <Screens t={t} v={v} /> : <Screens9 t={t} />}
      <PassLabel t={t} L={L} />
      <Flights t={t} v={v} L={L} />
    </AbsoluteFill>
  );
};

/** the view at t: 16:9 as before; 9:16 with the subject-follow x and the per-shot vertical nudge */
export function viewOf(cam: Cam, L: Layout, t: number) {
  if (L.fmt === '16x9') return makeView(cam, L);
  const f = follow9(cam, t); return makeView(cam, L, f.fx, f.dy);
}
// ---- 9:16 subject follow: each shot's subject (a world point) is re-centred with a 0.35 s ease on its land ----
type Subj = { t: number; at: (t: number) => V3; sx?: number; dy?: number };
const carMid = (t: number): V3 => { const car = carAt(t); return [car ? car.x + 236 : CAR.x + 236, GROUND - 40, CAR_Z]; };
const SUBJ9: Subj[] = [
  { t: -1, at: () => [960, 470, 0] },                                  // s28 the dot, the first tower
  { t: T.RAIN, at: () => [RAIN_EDGE, GROUND - 200, RAIN_Z] },          // s29 the rain line on x 540: "just one side"
  { t: T.CAR - 1.0, at: carMid },                                     // s30 the car (followed as it rolls in)
  { t: T.LIGHTS - 0.6, at: () => [980, 580, LIGHT_Z] },               // s31 the lights meet in the middle
  { t: T.GUYS, at: () => [TARGET.cx, TARGET.cy, 0] },                 // s32 the window column
  { t: T.PIGEONS - 0.75, at: () => [FLOCK.x - 60, FLOCK.y + 40, PIGEON_Z], sx: 420, dy: 100 }, // s34 the flock, left of the chrome
  { t: T.GRAV, at: carMid },                                          // s35-s38 the car (zero-g, the drag down, the impact)
  { t: T.FIRE, at: (t) => { const c = carMid(t); return [(960 + c[0]) / 2, 470, c[2] / 2]; } }, // s39-s44 the city with the car in frame
  { t: T.PASS, at: () => [960, 470, 0] },                              // s45 the city centred (= 16:9's centre at the s46 match-cut)
];
function follow9(cam: Cam, t: number): { fx: number; dy: number } {
  const v16 = makeView(cam, LAYOUT16);
  const one = (s: Subj) => { const q = s.at(t), p = v16.proj(q[0], q[1], q[2]); const x = p ? p.x : 960; return { fx: x - ((s.sx ?? 540) - 540) / CITY9.K, dy: s.dy ?? 0 }; };
  let i = 0; while (i < SUBJ9.length - 1 && t >= SUBJ9[i + 1].t) i++;
  const cur = one(SUBJ9[i]); if (i === 0) return cur;
  const k = easeInOut3(prog(t, SUBJ9[i].t, SUBJ9[i].t + 0.35)); if (k >= 1) return cur;
  const prev = one(SUBJ9[i - 1]); return { fx: lerp(prev.fx, cur.fx, k), dy: lerp(prev.dy, cur.dy, k) };
}

function drawCity(c: X, t: number, L: Layout, cam: Cam) {
  const v = viewOf(cam, L, t);
  const W = L.W, H = L.H;
  c.setTransform(1, 0, 0, 1, 0, 0);
  c.clearRect(0, 0, W, H);
  // ground of CH1's clean slate (bg #0a0d16 + dot grid), the sky and street unfold over it
  const kSky = smooth(prog(t, T.CITY, T.CITY + 0.7));
  if (kSky < 1) {
    c.fillStyle = '#0a0d16'; c.fillRect(0, 0, W, H);
    c.fillStyle = `rgba(255,255,255,${0.08 * (1 - kSky)})`;
    if (L.fmt === '16x9') { for (let y = 24; y < H; y += 48) for (let x = 24; x < W; x += 48) c.fillRect(x - 1, y - 1, 2, 2); }
    else { const d = 60, s0 = v.proj(24, 24, 0); const ox = s0 ? ((s0.x % d) + d) % d : 30, oy = s0 ? ((s0.y % d) + d) % d : 17.5; for (let y = oy; y < H; y += d) for (let x = ox; x < W; x += d) c.fillRect(x - 1, y - 1, 2, 2); }
  }
  const hz = v.proj(960, GROUND, 0);
  const gy = hz ? hz.y : 810;
  c.globalAlpha = kSky;
  const sky = c.createLinearGradient(0, Math.min(0, gy - 810), 0, gy);
  sky.addColorStop(0, V2.skyTop); sky.addColorStop(1, V2.skyHorizon);
  c.fillStyle = sky; c.fillRect(0, 0, W, H);
  c.globalAlpha = 1;

  // fireworks (s39), in the sky behind the skyline
  const fireK = drawFireworks(c, v, t);

  // ground plane: road to the camera (clipped at the near plane), the kerb, lane dashes, the wet left half
  const gK = smooth(prog(t, T.CITY + 0.05, T.CITY + 0.55));
  if (gK > 0) {
    c.save();
    if (gK < 1) { c.beginPath(); c.rect(v.SCX - gK * (W / 2 + 40), 0, gK * (W + 80), H); c.clip(); }
    const zn = cam.dz - F + NEAR + 5;
    fillPoly(c, v.poly([[-6000, GROUND, 1400], [8000, GROUND, 1400], [8000, GROUND, zn], [-6000, GROUND, zn]]), COL.road);
    fillPoly(c, v.poly([[-6000, GROUND, 0], [8000, GROUND, 0], [8000, GROUND, -36], [-6000, GROUND, -36]]), COL.kerb);
    for (let x = -4000; x < 6000; x += 95.3) fillPoly(c, v.poly([[x, GROUND, -338], [x + 47.7, GROUND, -338], [x + 47.7, GROUND, -320], [x, GROUND, -320]]), 'rgba(255,255,255,.18)');
    if (t >= T.RAIN) {
      const k = smooth(prog(t, T.RAIN + 0.3, T.RAIN + 1.0));
      fillPoly(c, v.poly([[-6000, GROUND, -36], [RAIN_EDGE, GROUND, -36], [RAIN_EDGE, GROUND, -480], [-6000, GROUND, -480]]), `rgba(184,200,224,${0.05 * k})`);
      // puddle ripples (left only)
      c.strokeStyle = `rgba(184,200,224,${0.22 * k})`; c.lineWidth = 1.5;
      for (let i = 0; i < 26; i++) {
        const per = 0.9 + hash(i, 3) * 0.6, ph = ((t - T.RAIN) * rainSpeed(t) / per + hash(i, 5)) % 1;
        const px = -400 + hash(i, 7) * (RAIN_EDGE + 340), pz = -60 - hash(i, 9) * 380, p = v.proj(px, GROUND, pz);
        if (!p || p.x > (v.proj(RAIN_EDGE, GROUND, pz)?.x ?? 0) - 12) continue;
        c.globalAlpha = 1 - ph; c.beginPath(); c.ellipse(p.x, p.y, (4 + 22 * ph) * p.s, (1.2 + 4 * ph) * p.s, 0, 0, Math.PI * 2); c.stroke();
      }
      c.globalAlpha = 1;
    }
    // s38 shockwave across the ground from the car
    const ds = t - T.IMPACT;
    if (ds >= 0 && ds < 0.7) {
      const p = v.proj(CAR.x + 236, GROUND, CAR_Z); if (p) {
        const k = ds / 0.7, r = 40 + 2400 * easeOut3(k);
        c.strokeStyle = `rgba(255,243,220,${0.55 * (1 - k)})`; c.lineWidth = 6 * (1 - k) + 1;
        c.beginPath(); c.ellipse(p.x, p.y, r * p.s, r * p.s * 0.12, 0, 0, Math.PI * 2); c.stroke();
      }
    }
    c.restore();
  }

  // 9:16: the wet road below the kerb carries the lit windows' amber reflections (12% max), streaks per window column
  if (L.fmt !== '16x9' && gK > 0) drawWetReflections(c, v, t, H);
  // buildings, far to near; within a row, outer first (nearer-centre neighbours cover the side faces)
  const shade = t >= T.PASS - 0.02 ? 1 : 0;
  const wipeY = shade ? lerp(-60, H + 60, easeInOut3(prog(t, T.PASS, T.PASS + 0.5))) : -9999;
  const sweep = prog(t, SHINE - 0.05, SHINE + 0.5);
  const detail = cam.dz > 400;
  const order = BLDS.map((b) => ({ b, d: b.z * 10000 + Math.abs((v.proj(b.x + b.w / 2, b.base, b.z)?.x ?? 1e5) - v.SCX) }))
    .filter((o) => o.b.layer !== 'rear' || t >= T.LOUD).sort((a, b) => b.d - a.d);
  const farA = clamp((0.985 - Math.exp(Math.log(Math.max(1e-3, F / (F - cam.dz))))) / 0.12);
  for (const o of order) {
    if (o.b.layer === 'far') { if (farA <= 0.01) continue; c.globalAlpha = farA; }
    if (o.b.z < TOWER.z && !TOWER_DRAWN.v && t >= T.TOWER) { drawTower(c, v, t); TOWER_DRAWN.v = true; }
    drawBuilding(c, v, o.b, t, { shade, wipeY, sweep, fireK, detail });
    c.globalAlpha = 1;
  }
  TOWER_DRAWN.v = false;
  // s42: rings of sound across the rooftops (on the kick)
  if (t >= T.LOUD && t < T.RUN + 0.5) drawRings(c, v, t);

  // street furniture: traffic lights, the lamp post with the red button
  drawStreet(c, v, t);
  // s45: contact AO under the car and the lights
  // pigeons
  drawPigeons(c, v, t);
  // the umbrella guy (s29 egg), standing exactly on the rain's edge
  if (t >= T.RAIN + 0.4) drawUmbrella(c, v, t);
  // rain (left of the world line x = 960 only: a hard edge)
  if (t >= T.RAIN) drawRain(c, v, t);
  // s44: traffic streaks at full speed (frozen at the lock)
  if (t >= T.RUN) drawStreaks(c, v, t);
  // the car
  drawCar(c, v, t);
  // s37: the floaters (guys out of their windows, still typing)
  drawFloaters(c, v, t);
  // the dot bursting into the city (s28)
  drawScatter(c, v, t);
  // vignette (approved frame 2: .4)
  const vg = c.createRadialGradient(W / 2, H / 2, H * 0.35, W / 2, H / 2, H * 1.05);
  vg.addColorStop(0, 'rgba(0,0,0,0)'); vg.addColorStop(1, `rgba(0,0,0,${0.4 * kSky})`); c.fillStyle = vg; c.fillRect(0, 0, W, H);
  if (L.fmt !== '16x9') drawInsert9(c, t, W, H);
  // s45: the render wipe's leading edge (wire cyan: the engine's own voice)
  if (shade && wipeY > -40 && wipeY < H + 40) { c.fillStyle = rgbaOf(CH2.wire, 0.85); c.fillRect(0, wipeY - 1, W, 2); c.fillStyle = rgbaOf(CH2.wire, 0.12); c.fillRect(0, wipeY - 14, W, 12); }
  // the cursor (s37: grabs the floating car)
  drawCursor(c, v, t);
  // s38: the impact flash, warm white, 2 frames
  const fi = Math.round((t - T.IMPACT) * 30);
  if (fi === 0 || fi === 1) { c.fillStyle = rgbaOf(CH2.flameCore, fi === 0 ? 0.6 : 0.3); c.fillRect(0, 0, W, H); }
}
const TOWER_DRAWN = { v: false };

function drawTower(c: X, v: View, t: number) {
  const n = clamp((t - T.TOWER) / (SIXTEENTH / 2), 0, TOWER.floors);
  const full = Math.floor(n);
  for (let k = 0; k < Math.ceil(n); k++) {
    const born = T.TOWER + k * (SIXTEENTH / 2);
    const fh = TOWER.floorH * (k < full ? 1 : n - full);
    const lv = clamp((bassAt(born) - 0.55) / 0.45);
    const w = TOWER.w * (0.82 + 0.18 * lv) * (1 - 0.25 * (k / TOWER.floors));
    const x0 = TOWER.x + (TOWER.w - w) / 2, x1 = x0 + w;
    const yb = TOWER.base - k * TOWER.floorH, yt = yb - fh;
    const z0 = TOWER.z, z1 = TOWER.z + TOWER.d;
    const FR = v.proj(x1, yt, z0), BR = v.proj(x1, yt, z1), FL = v.proj(x0, yt, z0), BL = v.proj(x0, yt, z1);
    if (BR && FR && BR.x > FR.x) fillPoly(c, v.poly([[x1, yt, z0], [x1, yt, z1], [x1, yb, z1], [x1, yb, z0]]), '#141d30');
    if (BL && FL && BL.x < FL.x) fillPoly(c, v.poly([[x0, yt, z1], [x0, yt, z0], [x0, yb, z0], [x0, yb, z1]]), '#141d30');
    if (BL && FL && BL.y < FL.y) fillPoly(c, v.poly([[x0, yt, z0], [x1, yt, z0], [x1, yt, z1], [x0, yt, z1]]), '#30426b');
    fillPoly(c, v.poly([[x0, yt, z0], [x1, yt, z0], [x1, yb, z0], [x0, yb, z0]]), '#1d2944');
    // the floor's lit band: amber at the top fading into surface blue, width from the bass when it was born
    const hf = k / TOWER.floors, now = k > full - 6 ? 0.7 + 0.3 * clamp((bassAt(t) - 0.5) / 0.5) : 1;
    const band = mixHexA(P.ch1.surface, V2.window, clamp(0.25 + 0.75 * hf) * (0.55 + 0.45 * lv) * now);
    if (fh > 8) fillPoly(c, v.poly([[x0 + 10, yt + 10, z0], [x1 - 10, yt + 10, z0], [x1 - 10, yb - 12, z0], [x0 + 10, yb - 12, z0]]), band);
  }
  // the top floor is the red button
  if (n >= TOWER.floors) {
    const k = clamp(spring(t - (T.TOWER + TOWER.floors * SIXTEENTH / 2), 2.4, 0.5), 0, 1.3);
    const yt = TOWER.base - TOWER.floors * TOWER.floorH;
    const p = v.proj(TOWER.x + TOWER.w / 2, yt, TOWER.z + TOWER.d / 2);
    if (p) {
      const r = 46 * p.s * k;
      c.fillStyle = V2.redButton.replace('#', '#') ; c.fillStyle = '#3a0d12'; c.beginPath(); c.ellipse(p.x, p.y, r * 1.15, r * 0.35, 0, 0, Math.PI * 2); c.fill();
      c.fillStyle = V2.redButton; c.beginPath(); c.ellipse(p.x, p.y - r * 0.25, r, r * 0.7, 0, Math.PI, 0); c.ellipse(p.x, p.y - r * 0.25, r, r * 0.3, 0, 0, Math.PI); c.fill();
      c.fillStyle = 'rgba(255,255,255,.22)'; c.beginPath(); c.ellipse(p.x - r * 0.35, p.y - r * 0.6, r * 0.22, r * 0.12, -0.3, 0, Math.PI * 2); c.fill();
    }
  }
}

function drawRings(c: X, v: View, t: number) {
  const on = smooth(prog(t, T.LOUD, T.LOUD + 0.2)) * (1 - smooth(prog(t, T.RUN, T.RUN + 0.5)));
  for (const k of kicks) {
    const d = t - k; if (d < 0 || d > 0.9 || k < T.LOUD - 0.01) continue;
    const r = 120 + 3600 * easeOut3(d / 0.9);
    const pts: Pt[] = [];
    for (let i = 0; i <= 48; i++) { const a = (i / 48) * Math.PI * 2; const p = v.proj(960 + Math.cos(a) * r, 330, 300 + Math.sin(a) * r * 0.5); if (p) pts.push(p); }
    if (pts.length < 10) continue;
    c.strokeStyle = rgbaOf(CH2.flameCore, 0.3 * on * (1 - d / 0.9)); c.lineWidth = 5;
    c.beginPath(); pts.forEach((p, i) => (i ? c.lineTo(p.x, p.y) : c.moveTo(p.x, p.y))); c.stroke();
  }
}

function drawStreet(c: X, v: View, t: number) {
  const rise = (d: number) => clamp(spring(t - (T.CITY + 0.45 + d), 2.4, 0.55), 0, 1.25);
  // the two traffic lights
  for (let i = 0; i < 2; i++) {
    const Lg = LIGHTS[i];
    const k = rise(i * 0.12); if (k <= 0) continue;
    const fl = floatOf(t, { A: 120 + i * 30, ph: 2 + i });
    const base = v.proj(Lg.x, GROUND + 2, LIGHT_Z); if (!base) continue;
    const s = base.s;
    // s31: the heads stretch toward each other on rubber poles and bonk on the downbeat, then spring home
    const M = { x: 980, y: 600 };
    const go = t < T.LIGHTS ? easeIn2(prog(t, T.LIGHTS - 0.42, T.LIGHTS)) : t < T.LIGHTS + 1.2 ? clamp(1 - spring(t - T.LIGHTS, 1.6, 0.42), -0.3, 1) : 0;
    const hx = lerp(Lg.x, M.x + (i ? 22 : -22), go), hy = lerp(Lg.y, M.y, go) - fl.h;
    const head = v.proj(hx, hy, LIGHT_Z); if (!head) continue;
    const by = base.y + (1 - k) * 160 * s - fl.h * s;
    // lamps: red / green blinking on the hats; after the bonk they swap, then both green forever
    const hat = inSilence(t) ? 0.5 : hatEnv(t, 0.12);
    const blink = 0.62 + 0.38 * hat;
    let lamps = i === 0 ? [blink, 0, 0] : [0, 0, blink];
    if (t >= T.LIGHTS) { const both = t >= T.LIGHTS + BEAT; lamps = i === 0 ? [0, 0, blink] : both ? [0, 0, blink] : [blink, 0, 0]; }
    // pole: from the kerb to the head (a curve when stretched)
    c.save(); c.globalAlpha = clamp(k * 3);
    c.strokeStyle = '#0d0d16'; c.lineWidth = 6 * s; c.lineCap = 'round';
    const hy2 = head.y + (1 - k) * 160 * s;
    c.beginPath(); c.moveTo(base.x, by); c.quadraticCurveTo(base.x, lerp(by, hy2, 0.7), head.x, hy2); c.stroke();
    c.save(); c.translate(head.x, hy2); c.rotate((i ? -1 : 1) * 0.5 * go + (fl.h > 1 ? 0.15 * Math.sin((t - T.GRAV) * 1.4 + i) : 0));
    trafficLight(c, 0, 0, s, lamps, 0);
    c.restore();
    c.restore();
  }
  // the bonk: warm white where they meet
  const db = t - T.LIGHTS;
  if (db >= 0 && db < 0.25) { const p = v.proj(980, 560, LIGHT_Z); if (p) { const g = c.createRadialGradient(p.x, p.y, 0, p.x, p.y, 120 * p.s); g.addColorStop(0, rgbaOf(CH2.flameCore, 0.7 * (1 - db / 0.25))); g.addColorStop(1, 'rgba(255,243,220,0)'); c.fillStyle = g; c.fillRect(p.x - 130 * p.s, p.y - 130 * p.s, 260 * p.s, 260 * p.s); } }
  // the lamp post with the red button (approved easter egg)
  const k = rise(0.3);
  const fl = floatOf(t, { A: 100, ph: 4.2 });
  const p = v.proj(LAMP.x, LAMP.y - fl.h, LIGHT_Z), q = v.proj(LAMP.x, GROUND + 2 - fl.h, LIGHT_Z);
  if (p && q && k > 0) {
    const dy = (1 - k) * 180 * p.s;
    c.fillStyle = '#0d0d16'; c.fillRect(p.x - 4 * p.s, p.y + dy, 8 * p.s, q.y - p.y);
    c.fillStyle = V2.redButton; c.beginPath(); c.arc(p.x, p.y + 60 * p.s + dy, 7 * p.s, 0, Math.PI * 2); c.fill();
  }
}

const FLOCK_N = 7;
function drawPigeons(c: X, v: View, t: number) {
  if (t < T.RAIN) return;
  const enter = easeOut3(prog(t, T.RAIN, T.CAR - 0.2));
  const leave = easeIn2(prog(t, T.FIRE + 0.4, T.SPIN + 0.3));
  if (leave >= 1) return;
  const s0 = 1.1;
  for (let i = 0; i < FLOCK_N; i++) {
    const kk = i - (FLOCK_N - 1) / 2;
    // the V (approved), entering from the right
    let x = FLOCK.x + Math.abs(kk) * -34 * s0 + (1 - enter) * 1500, y = FLOCK.y + kk * 22 * s0;
    let flap = (t * 2.6 + i * 0.13) % 1, upside = false, rot = 0;
    // s34: wheel into a circle (the loop symbol) on the downbeat, climb on beats 2 and 3
    const cK = smooth(prog(t, T.PIGEONS - 0.3, T.PIGEONS));
    const climb = HIGHER.reduce((a, h) => a + 70 * clamp(spring(t - h, 2.4, 0.6), 0, 1.2), 0);
    if (cK > 0) {
      const a = (i / FLOCK_N) * Math.PI * 2 + (t - T.PIGEONS) * 2.2;
      const cx = FLOCK.x - 60, cy = FLOCK.y + 40 - climb;
      x = lerp(x, cx + Math.cos(a) * 110, cK); y = lerp(y, cy + Math.sin(a) * 60, cK);
    }
    // gravity off: birds float; s36: they keep floating (gliding), one floats upside down
    const fl = floatOf(t, { A: 60 + i * 9, ph: i, bird: true });
    y -= fl.h;
    if (t >= T.BIRDS && t < T.IMPACT + 1.2) { flap = 0.25; if (i === 2) { upside = true; rot = 0.3 * Math.sin((t - T.BIRDS) * 1.5); } }
    // after the impact they glide back into the V and leave when the fireworks start
    if (t >= T.IMPACT) {
      const back = smooth(prog(t, T.IMPACT, T.IMPACT + 1.6));
      const vx = FLOCK.x + Math.abs(kk) * -34 * s0, vy = FLOCK.y + kk * 22 * s0;
      x = lerp(x, vx, back); y = lerp(y, vy, back);
      if (back > 0.6) { upside = false; rot = 0; }
      x += leave * 2200; y -= leave * 500;
    }
    const p = v.proj(x, y, PIGEON_Z);
    if (p && p.s < 30) pigeon(c, p.x, p.y, s0 * p.s, flap, upside, rot);
  }
}

function drawUmbrella(c: X, v: View, t: number) {
  const k = smooth(prog(t, T.RAIN + 0.4, T.RAIN + 0.8));
  const fl = floatOf(t, { A: 90, ph: 3.3 });
  const p = v.proj(UMBRELLA.x, GROUND - fl.h, UMBRELLA.z); if (!p || p.s > 12) return;
  const s = p.s * 1.25;
  c.save(); c.translate(p.x, p.y); c.globalAlpha = k;
  c.fillStyle = '#0b1220';
  c.beginPath(); c.arc(0, -21 * s, 3.2 * s, 0, Math.PI * 2); c.fill();
  rr(c, -3.6 * s, -17 * s, 7.2 * s, 11 * s, 2 * s); c.fill();
  c.fillRect(-2.8 * s, -6 * s, 2.2 * s, 6 * s); c.fillRect(0.6 * s, -6 * s, 2.2 * s, 6 * s);
  c.strokeStyle = '#0b1220'; c.lineWidth = 1.2 * s; c.beginPath(); c.moveTo(0.5 * s, -12 * s); c.lineTo(0.5 * s, -30 * s); c.stroke();
  // canopy: the left half wet (darker, drips), the right half dry
  c.fillStyle = '#e8eef8'; c.beginPath(); c.moveTo(-14 * s, -29 * s); c.quadraticCurveTo(0.5 * s, -44 * s, 15 * s, -29 * s); c.closePath(); c.fill();
  c.fillStyle = 'rgba(120,150,190,.55)'; c.beginPath(); c.moveTo(-14 * s, -29 * s); c.quadraticCurveTo(-7 * s, -40 * s, 0.5 * s, -36.6 * s); c.lineTo(0.5 * s, -29 * s); c.closePath(); c.fill();
  c.restore();
}

function drawRain(c: X, v: View, t: number) {
  const rc = rainClock(t), sp = rainSpeed(t);
  const edge = v.proj(RAIN_EDGE, 400, RAIN_Z); if (!edge) return;
  c.save(); c.beginPath(); c.rect(-10, -10, edge.x + 10, 4000); c.clip();
  c.strokeStyle = V2.ghost; c.lineWidth = 2;
  const fl = floatOf(t, { A: 0, ph: 0 });
  void fl;
  c.beginPath();
  for (let di = 0; di < DROPS.length; di++) {
    const d = DROPS[di];
    const fd = rc * 1500 * d.v - d.o * RAIN_SPAN;
    if (fd < 0) continue;
    const y = RAIN_TOP + (fd % RAIN_SPAN);
    const p = v.proj(d.x, y, RAIN_Z); if (!p || p.x < -40 || p.x > edge.x + 40 || p.y < -60 || p.y > 2000) continue;
    if (p.s > 4.5 || (p.s < 1 && d.o * 0.37 + d.v * 0.6 - 0.5 > Math.pow(p.s, 1.6) * 0.55)) continue; // thinner in the wide shots (no speckle)
    const l = (d.l * (0.15 + 0.85 * sp) + 2) * p.s;
    c.moveTo(p.x, p.y); c.lineTo(p.x - 5 * p.s * (0.2 + 0.8 * sp), p.y + l);
  }
  c.stroke();
  c.restore();
}

function drawStreaks(c: X, v: View, t: number) {
  const tr = Math.min(t, LOCK) - T.RUN, on = smooth(prog(t, T.RUN, T.RUN + 0.25));
  for (let i = 0; i < 26; i++) {
    const dir = i % 2 ? 1 : -1, z = dir > 0 ? -250 - hash(i, 1) * 60 : -400 - hash(i, 2) * 60;
    const sp = 2600 + hash(i, 3) * 1400, span = 9000;
    const x = -3500 + ((hash(i, 4) * span + dir * sp * tr) % span + span) % span;
    const len = 420 + hash(i, 5) * 380;
    const a = v.proj(x, GROUND - 14, z), b = v.proj(x - dir * len, GROUND - 14, z);
    if (!a || !b) continue;
    const g = c.createLinearGradient(a.x, a.y, b.x, b.y);
    const col = dir > 0 ? CH2.flameCore : V2.trafficRed;
    g.addColorStop(0, rgbaOf(col, 0.85 * on)); g.addColorStop(1, rgbaOf(col, 0));
    c.strokeStyle = g; c.lineWidth = 4 * a.s; c.lineCap = 'round';
    c.beginPath(); c.moveTo(a.x, a.y); c.lineTo(b.x, b.y); c.stroke();
  }
}

function drawCar(c: X, v: View, t: number) {
  const car = carAt(t); if (!car) return;
  const p = v.proj(car.x, CAR.y - car.lift, CAR_Z), g = v.proj(car.x, CAR.y, CAR_Z);
  if (!p || !g || p.s > 25) return;
  c.save();
  if (car.rot) { c.translate(p.x + 236 * p.s, p.y - 90 * p.s); c.rotate(car.rot); c.translate(-(p.x + 236 * p.s), -(p.y - 90 * p.s)); }
  // the car's ground shadow stays on the road while it floats
  gt3(c, p.x, g.y, p.s, { wheelA: car.wheel, pitch: car.pitch, sq: car.sq, rim: clamp(car.lift / 50), shadow: 1, lift: car.lift });
  c.restore();
  // the calipers catch the light at the stop (s30)
  const dg = t - T.CAR - 0.08;
  if (dg >= 0 && dg < 0.35) {
    const k = Math.sin((dg / 0.35) * Math.PI);
    for (const wx of [104, 368]) {
      const q = { x: p.x + (wx - 18) * p.s, y: g.y - 66 * p.s };
      c.save(); c.translate(q.x, q.y); c.fillStyle = rgbaOf(CH2.glint, 0.9 * k);
      c.beginPath(); for (let i = 0; i < 8; i++) { const a = (i / 8) * Math.PI * 2, r = (i % 2 ? 2.2 : 11) * p.s * k; c.lineTo(Math.cos(a) * r, Math.sin(a) * r); } c.closePath(); c.fill(); c.restore();
    }
  }
}

function drawFloaters(c: X, v: View, t: number) {
  if (t < T.ZERO || t > T.IMPACT + 0.7) return;
  for (let i = 0; i < FLOATERS.length; i++) {
    const { b, w } = FLOATERS[i];
    const out = smooth(prog(t, T.ZERO + 0.1 + hash(i, 11) * 0.5, T.ZERO + 1.4 + hash(i, 11) * 0.5));
    const back = t >= T.IMPACT ? easeIn2(prog(t, T.IMPACT, T.IMPACT + 0.32 + hash(i, 12) * 0.25)) : 0;
    const k = out * (1 - back);
    const hs = heightOf(b, t);
    const wy = b.base - (b.base - w.y) * hs;
    const x = w.x + 9 + k * (hash(i, 13) - 0.5) * 120, y = wy + 14 - k * (60 + hash(i, 14) * 140), z = b.z - k * (30 + hash(i, 15) * 50);
    const p = v.proj(x, y, z); if (!p || p.s > 10) continue;
    const s = p.s * 1.15, rot = k * (hash(i, 16) - 0.5) * 1.2 + 0.15 * Math.sin(t * 1.3 + i) * k;
    const jy = -0.9 * (0.5 + 0.5 * Math.sin(t * 40 + i)); // typing (no drums in the silence: a steady nervous tap)
    c.save(); c.translate(p.x, p.y); c.rotate(rot);
    c.strokeStyle = rgbaOf(V2.window, 0.8); c.lineWidth = 1.2 * s; c.fillStyle = '#141b2a';
    c.beginPath(); c.arc(0, -4 * s, 3.4 * s, 0, Math.PI * 2); c.fill(); c.stroke();
    rr(c, -5 * s, 0, 10 * s, 8 * s, 1.5 * s); c.fill(); c.stroke();
    c.fillStyle = '#e8eef8'; c.fillRect(-6 * s, (5 + jy) * s, 12 * s, 2 * s); // the laptop's glow
    c.restore();
  }
}

function drawScatter(c: X, v: View, t: number) {
  if (t > T.CITY + 2.4) return;
  const D = v.proj(960, 470, 0); if (!D) return;
  // the dot: a 2-frame swell, then it empties into the particles; its rings open and fade
  const dt = t - T.CITY;
  const r = 74 * D.s * (dt < 0.066 ? 1 + 0.12 * (dt / 0.066) : 1.12 * (1 - easeIn2(prog(dt, 0.066, 0.24))));
  const ringK = 1 - smooth(prog(dt, 0, 0.45));
  if (ringK > 0) for (const i of [3, 2, 1]) { c.strokeStyle = `rgba(255,255,255,${0.05 * i * ringK})`; c.lineWidth = 2; c.beginPath(); c.arc(D.x, D.y, 74 * D.s + i * 34 * D.s + dt * 600 * i, 0, Math.PI * 2); c.stroke(); }
  if (r > 0.5) { c.fillStyle = C.pink; c.beginPath(); c.arc(D.x, D.y, r, 0, Math.PI * 2); c.fill(); }
  // particles: one per window the dot lights; pink -> peach -> amber over 6 frames; they morph into the window
  for (const b of BLDS) {
    if (b.layer !== 'front' || b.x + b.w < -60 || b.x > 1980) continue;
    const hs = heightOf(b, t), rise = riseOf(b, t), drop = (1 - rise) * (b.h * hs + 40);
    for (const w of b.wins) {
      if (!w.lit0) continue;
      const ta = arriveOf(b, w), t0 = T.CITY + w.r1 * 0.12;
      if (t < t0 || t > ta) continue;
      const k = prog(t, t0, ta), e = easeInOut3(k);
      const tgt = v.proj(w.x + 9, b.base - (b.base - w.y - 12) * hs + drop, b.z); if (!tgt) continue;
      const a0 = w.r2 * Math.PI * 2, sx = D.x + Math.cos(a0) * 30 * D.s, sy = D.y + Math.sin(a0) * 30 * D.s;
      const cx = lerp(sx, tgt.x, 0.5) + (w.r3 - 0.5) * 120, cy = Math.min(sy, tgt.y) - 160 - w.r1 * 120;
      const x = (1 - e) * (1 - e) * sx + 2 * (1 - e) * e * cx + e * e * tgt.x, y = (1 - e) * (1 - e) * sy + 2 * (1 - e) * e * cy + e * e * tgt.y;
      const ck = prog(t, t0, t0 + 0.2);
      const col = ck < 0.5 ? mixHexA(C.pink, '#ffa896', ck * 2) : mixHexA('#ffa896', w.cool ? V2.windowCool : V2.window, (ck - 0.5) * 2);
      const m = smooth(prog(k, 0.6, 1));
      const ww = lerp(12, 18 * tgt.s, m), hh = lerp(12, 24 * tgt.s, m);
      c.fillStyle = col; rr(c, x - ww / 2, y - hh / 2, ww, hh, lerp(6, 0.5, m)); c.fill();
    }
  }
}

function drawCursor(c: X, v: View, t: number) {
  const car = carAt(t);
  if (!car || t < T.ZERO + 0.15 || t > TOUCH + 0.5) return;
  const p = v.proj(car.x + 250, CAR.y - car.lift - 150, CAR_Z); if (!p) return;
  // enters from the prompt bar, reaches the car's roof at the grab, rides down with it, lets go at the touch
  const tg = T.ZERO + 0.55;
  const k = easeInOut3(prog(t, T.ZERO + 0.15, tg));
  const x = lerp(1150, p.x, k), y = lerp(960, p.y, k);
  const leave = smooth(prog(t, TOUCH + 0.05, TOUCH + 0.45));
  c.save(); c.globalAlpha = 1 - leave;
  cursor(c, x + leave * 60, y - leave * 90, 1.25, car.grab);
  c.restore();
}

/** 9:16: amber reflections of the lit front windows on the wet road (one streak per window column, 12% max, fading
 *  toward the camera); the left (rain) half is wetter, so its streaks run longer */
function drawWetReflections(c: X, v: View, t: number, H: number) {
  c.save();
  for (const b of BLDS) {
    if (b.layer !== 'front' || !b.wins.length) continue;
    const cols = new Map<number, { x: number; k: number; n: number; cool: number }>();
    for (const w of b.wins) {
      const Lw = windowLight(b, w, t, arriveOf(b, w)); const e = cols.get(w.col) ?? { x: w.x, k: 0, n: 0, cool: 0 };
      e.k += Lw.k; e.n += 1; e.cool += Lw.cool ? 1 : 0; cols.set(w.col, e);
    }
    for (const e of cols.values()) {
      const k = e.k / Math.max(1, e.n); if (k < 0.04) continue;
      const wet = e.x < RAIN_EDGE && t >= T.RAIN ? 1 : 0.7;
      const zf = -1200 * wet;
      const a0 = v.proj(e.x + 2, GROUND, -40), a1 = v.proj(e.x + 16, GROUND, -40), b0 = v.proj(e.x + 2, GROUND, zf), b1 = v.proj(e.x + 16, GROUND, zf);
      if (!a0 || !a1 || !b0 || !b1 || a1.x < -40 || a0.x > v.SCX * 2 + 40 || a0.y > H) continue;
      const col = e.cool > e.n / 2 ? V2.windowCool : V2.window;
      const g = c.createLinearGradient(0, a0.y, 0, Math.min(H, b0.y));
      g.addColorStop(0, rgbaOf(col, 0.12 * k)); g.addColorStop(0.35, rgbaOf(col, 0.06 * k)); g.addColorStop(1, rgbaOf(col, 0));
      c.fillStyle = g; c.beginPath(); c.moveTo(a0.x, a0.y); c.lineTo(a1.x, a1.y); c.lineTo(b1.x, b1.y); c.lineTo(b0.x, b0.y); c.closePath(); c.fill();
    }
  }
  c.restore();
}

// ---- 9:16 s33 insert (LAYOUT_916.md): the three windows stacked as three floors of one building ----
export const INSERT9 = { x: 305, w: 470, h: 262, ys: [286, 562, 838], scr: { dx: 118, dy: 40, w: 320, h: 152 } };
/** 0..1 presence of the insert at t (in with the push into the row, out as the camera pulls back for the pigeons) */
export const insertK9 = (t: number) => smooth(prog(t, T.WIRED + 0.12, T.WIRED + 0.5)) * (1 - smooth(prog(t, T.PIGEONS - 0.75, T.PIGEONS - 0.4)));
function drawInsert9(c: X, t: number, W: number, H: number) {
  const k = insertK9(t); if (k <= 0.001) return;
  const I = INSERT9, sc = lerp(0.82, 1, k), cx = W / 2, cy = 694;
  const typing = hatEnv(t, 0.06);
  c.save(); c.globalAlpha = k;
  c.translate(cx, cy); c.scale(sc, sc); c.translate(-cx, -cy);
  // the facade: one building, floor slabs between the windows, the street glow at its foot
  const fac = c.createLinearGradient(0, 0, 0, H); fac.addColorStop(0, '#16223a'); fac.addColorStop(0.62, COL.front); fac.addColorStop(1, '#0d1524');
  c.fillStyle = fac; c.fillRect(-200, -200, W + 400, H + 400);
  c.fillStyle = 'rgba(5,8,16,.35)'; for (const y of I.ys) c.fillRect(-200, y + I.h + 18, W + 400, 6);
  c.fillStyle = 'rgba(255,255,255,.035)'; c.fillRect(I.x - 70, -200, 4, H + 400); c.fillRect(I.x + I.w + 66, -200, 4, H + 400);
  I.ys.forEach((y, i) => {
    const x = I.x, lit = V2.window;
    c.save(); c.beginPath(); c.rect(x, y, I.w, I.h); c.clip();
    const room = c.createLinearGradient(0, y, 0, y + I.h); room.addColorStop(0, mixHexA(COL.winOff, lit, 0.95)); room.addColorStop(1, mixHexA(COL.winOff, lit, 0.55));
    c.fillStyle = room; c.fillRect(x, y, I.w, I.h);
    c.fillStyle = P.ch2.flameCore; c.fillRect(x + 150, y, 170, 3);                          // the ceiling strip (the room's light)
    c.fillStyle = 'rgba(20,29,44,.55)'; c.fillRect(x, y + I.h - 34, I.w, 34);               // desk
    // the guy from behind, typing on the hats (left of his screen)
    const asleep = i === SLEEPER;
    const jy = asleep ? 32 + 2 * Math.sin(t * 2) : -3 * typing * (i % 2 ? 1 : 0.6), gx = x + 70, gy = y + I.h - 30;
    c.fillStyle = '#141b2a'; c.beginPath(); c.arc(gx, gy - 92 + jy, 30, 0, Math.PI * 2); c.fill();
    rr(c, gx - 48, gy - 62 + jy, 96, 80, 22); c.fill();
    c.fillStyle = 'rgba(5,8,16,.32)'; c.fillRect(x, y, I.w, 4); c.fillRect(x, y, 4, I.h);        // recess shadow
    c.restore();
    c.fillStyle = '#2b3a56'; c.fillRect(x - 10, y + I.h, I.w + 20, 8); c.fillStyle = '#121a2a'; c.fillRect(x - 10, y + I.h + 8, I.w + 20, 4); // sill
  });
  c.restore();
}

function drawFireworks(c: X, v: View, t: number): number {
  if (t < T.FIRE - 0.35 || t > T.FIRE + 4.5) return 0;
  // 9:16: bursts inside x 200-880, y 300-600 of the tall frame, none in the chrome block (top right)
  const SPOTS = v.SCX * 2 > 1500 ? [[620, 150], [1260, 100], [900, 30], [420, 230], [1520, 200]] : [[700, 170], [1150, 250], [930, 60], [560, 260], [1260, 330]];
  let I = 0;
  BURSTS.forEach((tb, bi) => {
    const [bx, by] = SPOTS[bi];
    const z = 500;
    // the rocket trail (0.3 s before the burst)
    const tr = t - (tb - 0.3);
    if (tr >= 0 && tr < 0.3) {
      const k = easeOut3(tr / 0.3), y0 = 560;
      const a = v.proj(bx, lerp(y0, by, k), z), b = v.proj(bx, lerp(y0, by, Math.max(0, k - 0.25)), z);
      if (a && b) { const g = c.createLinearGradient(a.x, a.y, b.x, b.y); g.addColorStop(0, rgbaOf(CH2.flameCore, 0.9)); g.addColorStop(1, 'rgba(255,207,122,0)'); c.strokeStyle = g; c.lineWidth = 3 * a.s; c.beginPath(); c.moveTo(a.x, a.y); c.lineTo(b.x, b.y); c.stroke(); }
    }
    const tau = t - tb; if (tau < 0 || tau > 1.9) return;
    const ctr = v.proj(bx, by, z); if (!ctr) return;
    I = Math.max(I, Math.exp(-tau / 0.5));
    if (tau < 0.2) { const g = c.createRadialGradient(ctr.x, ctr.y, 0, ctr.x, ctr.y, 90 * ctr.s); g.addColorStop(0, rgbaOf(CH2.flameCore, 0.75 * (1 - tau / 0.2))); g.addColorStop(1, 'rgba(255,243,220,0)'); c.fillStyle = g; c.fillRect(ctr.x - 100 * ctr.s, ctr.y - 100 * ctr.s, 200 * ctr.s, 200 * ctr.s); }
    const N = 28, R = 250 + 50 * hash(bi, 1);
    for (let k = 0; k < N; k++) {
      const a = (k / N) * Math.PI * 2 + hash(bi, k) * 0.15;
      const rr2 = R * (1 - Math.exp(-tau / 0.26)) * (0.85 + 0.15 * hash(k, bi + 9));
      const droop = 110 * tau * tau;
      const px = bx + Math.cos(a) * rr2, py = by + Math.sin(a) * rr2 + droop;
      const p = v.proj(px, py, z); if (!p) continue;
      const vx = Math.cos(a) * R * Math.exp(-tau / 0.26) / 0.26, vy = Math.sin(a) * R * Math.exp(-tau / 0.26) / 0.26 + 220 * tau;
      const ang = Math.atan2(vy, vx);
      const alpha = Math.pow(clamp(1 - tau / 1.9), 1.4);
      flame(c, p.x, p.y, (24 + 44 * Math.exp(-tau / 0.35)) * p.s, 7 * p.s, ang, alpha);
    }
  });
  return I;
}

// ---------- HTML text: the readable screens (s33), the pass label (s45), the flying payoff words ----------
const CU = 1680 / 78;
// s33 eggs, one per target window (left to right). Segments: [text, colour]; '\n' breaks a line.
//  0: the NEXT lyric typed before it's sung ('Now a little higher' at 84.08; 'Make the pigeons fly in circles' is already
//     being sung at 82.4, before these screens exist), finished by ~83.3 so the paused t frame shows all of it
//  1: the red-button warning (it pays off at the crash: 'pigeon.001 - pressed button')
//  2: the rain bug ticket, and its owner asleep on his keyboard (SLEEPER)
// Cut for fit (3 windows, 4 texts): 'while True: / run_it()'. To restore it, swap it in for any entry below.
const SCREENS: { seg: [string, string][]; typed?: boolean }[] = [
  { seg: [['> now a\nlittle\nhigher_', P.ui.promptText]], typed: true },
  { seg: [['nobody touch\nthe ', P.ui.promptText], ['red\nbutton', C.red], ['.', P.ui.promptText]] },
  { seg: [['BUG-1138\nrain: left\nhalf only', P.ui.promptText]] },
];
const SCREEN_FONT = 38, SCREEN_LH = 42;
const typedOf = (t: number, sd: typeof SCREENS[number]) => {
  if (!sd.typed) return sd.seg;
  const slow = Math.floor((Math.min(t, T.WIRED) - T.GUYS) / BEAT);
  const fast = t >= T.WIRED ? (Math.floor((t - T.WIRED) / SIXTEENTH) + 1) * 5 : 0;
  return [[sd.seg[0][0].slice(0, Math.max(0, slow + fast)), sd.seg[0][1]]] as [string, string][];
};
/** 9:16: the insert's three screens (320 x 152, code at 38 px, line height 44), on the canvas insert's windows */
const Screens9: React.FC<{ t: number }> = ({ t }) => {
  const k = insertK9(t); if (k <= 0.01) return null;
  const I = INSERT9, sc = lerp(0.82, 1, k), cx = 540, cy = 694, fl = 0.86 + 0.14 * hatEnv(t, 0.06);
  return <div style={{ position: 'absolute', inset: 0, transform: `scale(${sc})`, transformOrigin: `${cx}px ${cy}px`, opacity: k }}>
    {I.ys.map((y, i) => (
      <div key={i} data-fit="screen" style={{ position: 'absolute', left: I.x + I.scr.dx, top: y + I.scr.dy, width: I.scr.w, height: I.scr.h, boxSizing: 'border-box', padding: '10px 14px',
        background: '#0e0e14', borderRadius: 6, boxShadow: '0 0 0 3px #1b2436', overflow: 'hidden' }}>
        <div style={{ ...MED, fontSize: 38, lineHeight: '44px', whiteSpace: 'pre', color: P.ui.promptText, opacity: fl }}>{typedOf(t, SCREENS[i]).map(([text, color], j) => <span key={j} style={{ color }}>{text}</span>)}</div>
      </div>
    ))}
  </div>;
};
const Screens: React.FC<{ t: number; v: View }> = ({ t, v }) => {
  const W = v.SCX * 2;
  if (t < T.WIRED || t > T.PIGEONS) return null;
  return <>{TARGET.wins.map((w, i) => {
    const p = v.proj(w.x + SCR.x, w.y + SCR.y, 0); if (!p) return null;
    const op = clamp((p.s - 9) / 5) * (1 - smooth(prog(t, T.PIGEONS - 0.72, T.PIGEONS - 0.55)));
    if (op <= 0.01) return null;
    const sc = p.s / CU, sd = SCREENS[i];
    if (W < 1500 && (p.x < W * 0.09 || p.x + SCR.w * CU * sc > W * 0.91)) return null; // 9:16: only screens fully inside the safe width
    let seg = sd.seg;
    if (sd.typed) { // one char per beat before 'wired', then five per 16th note (the grid, not the sparse hat hits): done by ~83.3
      const slow = Math.floor((Math.min(t, T.WIRED) - T.GUYS) / BEAT);
      const fast = t >= T.WIRED ? (Math.floor((t - T.WIRED) / SIXTEENTH) + 1) * 5 : 0;
      seg = [[seg[0][0].slice(0, Math.max(0, slow + fast)), seg[0][1]]];
    }
    const fl = 0.86 + 0.14 * hatEnv(t, 0.06);
    return (
      <div key={i} data-fit="screen" style={{ position: 'absolute', left: p.x, top: p.y, width: SCR.w * CU, height: SCR.h * CU, transform: `scale(${sc})`, transformOrigin: '0 0',
        boxSizing: 'border-box', padding: '10px 14px', background: '#0e0e14', opacity: op, overflow: 'hidden' }}>
        <div style={{ ...MED, fontSize: SCREEN_FONT, lineHeight: `${SCREEN_LH}px`, whiteSpace: 'pre', opacity: fl }}>
          {seg.map(([s, col], j) => <span key={j} style={{ color: col }}>{s}</span>)}
        </div>
      </div>
    );
  })}</>;
};

const PassLabel: React.FC<{ t: number; L: Layout }> = ({ t, L }) => {
  if (t < T.PASS) return null;
  const k = smooth(prog(t, T.PASS + 0.1, T.PASS + 0.4));
  return (
    <div style={{ ...MED, position: 'absolute', left: L.fmt === '16x9' ? 64 : L.chip?.x ?? 116, top: L.fmt === '16x9' ? 52 : L.chip?.y ?? 262, height: 56, boxSizing: 'border-box', padding: '0 20px',
      display: 'flex', alignItems: 'center', gap: 14, background: 'rgba(14,14,20,.72)', border: `2px solid ${rgbaOf(CH2.wire, 0.55)}`, borderRadius: 12,
      fontSize: 34, lineHeight: '40px', color: P.ui.promptText, opacity: k, transform: `translateY(${(1 - k) * -10}px)` }}>
      <span style={{ width: 14, height: 14, borderRadius: 7, background: CH2.wire, flex: 'none' }} />pass 1 · shading
    </div>
  );
};

// the grammar: 0.30 s before each land the payoff word lifts out of the bar and flies to what it changes
const CH = 0.6;
const norm = (s: string) => s.replace(/[^\w']/g, '').toLowerCase();
type Flight = { id: string; at: (t: number) => [number, number, number] };
const FLIGHTS: Flight[] = [
  { id: 's29', at: () => [RAIN_EDGE, 330, RAIN_Z] },
  { id: 's30', at: (t) => { const car = carAt(t); return [car ? car.x + 104 : -600, GROUND - 4, CAR_Z]; } },
  { id: 's31', at: () => [980, 580, LIGHT_Z] },
  { id: 's32', at: () => [TARGET.b.x + TARGET.b.w / 2, TARGET.cy - 60, 0] },
  { id: 's33', at: () => [TARGET.cx, TARGET.cy, 0] },
  { id: 's34', at: () => [FLOCK.x - 60, FLOCK.y + 40, PIGEON_Z] },
  { id: 's38', at: () => [CAR.x + 236, GROUND - 60, CAR_Z] },
  { id: 's39', at: () => [620, 150, 500] },
  { id: 's40', at: () => [960, 520, 0] },
  { id: 's41', at: () => [960, 520, 0] },
  { id: 's42', at: () => [960, 330, 300] },
  { id: 's43', at: () => [960, 700, TOWER.z] },
  { id: 's44', at: () => [960, 620, 0] },
  { id: 's46', at: () => [PUSHWIN.cx, PUSHWIN.cy, 0] },
];
const Flights: React.FC<{ t: number; v: View; L: Layout }> = ({ t, v, L }) => {
  const els: React.ReactNode[] = [];
  for (const f of FLIGHTS) {
    const s = tshot(f.id); if (!s?.payoff) continue;
    const t0 = s.payoff.lift, t1 = s.land;
    if (t < t0 || t > t1 + 0.12) continue;
    let best = { li: -1, wi: -1, d: Infinity };
    for (const li of s.lines) { const ln = lines[li]; for (let wi = 0; wi < ln.words.length; wi++) { if (norm(ln.words[wi]) !== norm(s.payoff.word)) continue; const d = Math.abs(ln.wt[wi] - s.payoff.t); if (d < best.d) best = { li, wi, d }; } }
    if (best.li < 0 || promptAt(t0).lineIndex !== best.li) continue;
    const words = lines[best.li].text.split(' ');
    const idx = words.slice(0, best.wi).join(' ').length + (best.wi ? 1 : 0), word = words[best.wi].replace(/[.,!?]$/, '');
    const font = L.bar.font;
    const { x: x0, y: y0, ch } = barCharPos(L, lines[best.li].text, idx);
    const w3 = f.at(Math.min(t, t1)); const tp = L.fmt !== '16x9' && f.id === 's33' ? { x: 540, y: INSERT9.ys[1] + INSERT9.h / 2 } : v.proj(w3[0], w3[1], w3[2]);
    const tgt = tp ? { x: clamp(tp.x, 80, L.W - 80), y: clamp(tp.y, 80, L.H - 80) } : { x: L.W / 2, y: L.H / 2 };
    const p = clamp((t - t0) / (t1 - t0)), e = easeInOut3(p);
    const cx0 = x0 + (word.length * ch) / 2;
    const ctrl = { x: lerp(cx0, tgt.x, 0.5), y: Math.min(y0, tgt.y) - 140 };
    const bx = (1 - e) * (1 - e) * cx0 + 2 * (1 - e) * e * ctrl.x + e * e * tgt.x, by = (1 - e) * (1 - e) * y0 + 2 * (1 - e) * e * ctrl.y + e * e * tgt.y;
    const size = lerp(font, 34, e), op = t > t1 ? 0 : 1 - smooth(prog(p, 0.72, 1));
    els.push(<div key={`fly${f.id}`} data-fit="off" style={{ ...MED, position: 'absolute', left: bx, top: by, transform: 'translate(-50%,-50%)', fontSize: size, lineHeight: 1,
      color: P.ui.promptText, opacity: op, whiteSpace: 'nowrap', textShadow: '0 0 18px rgba(255,255,255,.35)' }}>{word}</div>);
    const ar = (t - t1) / 0.12;
    if (ar >= 0 && ar <= 1) els.push(<div key={`spk${f.id}`} style={{ position: 'absolute', left: tgt.x - 10 - 40 * ar, top: tgt.y - 10 - 40 * ar, width: 20 + 80 * ar, height: 20 + 80 * ar,
      borderRadius: '50%', border: '2px solid rgba(255,255,255,.6)', opacity: 1 - ar, boxSizing: 'border-box' }} />);
  }
  return <>{els}</>;
};
// unused-import guards (kept for later passes)
void mixC; void kickEnv; void sinceHit;
