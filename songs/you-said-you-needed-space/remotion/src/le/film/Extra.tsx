// Extra GL layers for the proof-30 look (earth_proof30, Nov 8). Every layer is OFF unless its grade knob is set
// (grade.ts: galaxy, deep, room, sand, chip, banner), so slots that don't ask for them render exactly as before.
//   galaxy (order -2)  Milky Way mist + a deep blue floor: space is dark, never a black void. Clears out of the room.
//   deep   (order -1)  42,000 GPU stars. On "space" each one backs away from her (spring keyed to the word, own lag),
//                      streaking along its own motion (the shutter), then settles pressed into a ring.
// All state is a function of frame.t and the grade: nothing is carried between frames.
import * as THREE from 'three';
import { Fmt, Frame } from './types';
import { rng } from './stars';
import { NOISE } from '../../glsl/noise';
import { SPACE, CREEP } from './sections/proof30';
import { BANNER } from './sections/proof30_banner.gen';

const f = (x: number) => (Number.isInteger(x) ? x.toFixed(1) : String(x));
// the room the stars give her: GLSL twin of sections/proof30.ts (same numbers)
export const ROOM_GLSL = /* glsl */ `
uniform float uT; uniform float uRoom; uniform vec2 uRoomC;
float springR(float tau, float w, float z){ tau = max(tau, 0.0); float wd = w * sqrt(1.0 - z * z); return 1.0 - exp(-z * w * tau) * (cos(wd * tau) + (z * w / wd) * sin(wd * tau)); }
float bumpR(float x){ float s = sin(3.14159265 * clamp(x, 0.0, 1.0)); return s * s; }
float roomR(float t){
  float R = ${f(SPACE.R0)} * (springR(t - ${f(SPACE.t - 0.1)}, 7.2, 0.60) - 0.04 * bumpR((t - ${f(SPACE.t - 0.42)}) / 0.5));
  R += ${f(SPACE.step)} * (springR(t - ${f(SPACE.echoes[0] - 0.04)}, 9.5, 0.62) + springR(t - ${f(SPACE.echoes[1] - 0.04)}, 9.5, 0.62) + springR(t - ${f(SPACE.echoes[2] - 0.04)}, 9.5, 0.62));
  return R * uRoom;
}
vec2 roomMap(vec2 hp, float t, float jit, float lag){
  vec2 d = hp - uRoomC; float r = max(length(d), 1e-5); float th = atan(d.y, d.x);
  float R = roomR(t - lag - 0.16 * clamp(r / 2.0, 0.0, 1.0));
  float wob = 0.045 * sin(3.0 * th + 1.0) + 0.03 * sin(5.0 * th + 4.0) + 0.02 * sin(9.0 * th + 2.0);
  float Rp = abs(R) * clamp(1.0 + 0.045 * jit + wob, 0.8, 1.4);
  float full = pow(r * r * r + Rp * Rp * Rp, 1.0 / 3.0);
  float rr = R < 0.0 ? max(r - (full - r) * 0.6, 0.005) : full;
  return uRoomC + d / r * rr;
}
// the SOFT room (cold open; drawn when uKeep > 0): GLSL twin of sections/proof30.ts roomSoft / clump (same numbers)
float clumpR(vec2 p){ return sin(p.x * 2.9 + 1.7) * sin(p.y * 3.3 + 0.4) + 0.6 * sin(p.x * 5.3 - p.y * 4.7 + 2.0); }
float wobR(float th){ return 0.10 * sin(2.0 * th + 0.6) + 0.07 * sin(3.0 * th + 1.0) + 0.05 * sin(5.0 * th + 4.0); }
float roomRSoft(float tt){ return roomR(tt) + ${f(CREEP * SPACE.R0)} * max(tt - ${f(SPACE.t)}, 0.0) * uRoom; }
vec2 roomSoft(vec2 hp, float t, float u01, float lag){
  vec2 d = hp - uRoomC; float r = max(length(d), 1e-5); float th = atan(d.y, d.x);
  float R = roomRSoft(t - lag - 0.16 * clamp(r / 2.0, 0.0, 1.0));
  float Ri = abs(R) * max(0.12, (0.45 + 0.93 * pow(u01, 1.1)) * (1.0 + wobR(th) + 0.22 * clumpR(hp)));
  float push = Ri * exp(-r / max(Ri, 1e-5));
  float rr = R < 0.0 ? max(r - 0.5 * push, 0.005) : r + push;
  return uRoomC + d / r * rr;
}`;

const GALAXY_FRAG = /* glsl */ `
precision highp float;
varying vec2 vP; uniform float uGal; uniform vec2 uPar; uniform vec2 uBand; uniform vec3 uHer; uniform vec3 uVio; uniform float uA; uniform float uKeep;
${NOISE}
${ROOM_GLSL}
void main(){
  // the mist is pushed out of the room with the stars: sample it where this pixel's mist came from
  vec2 d = vP - uRoomC; float rp = max(length(d), 1e-5);
  float Rh = max(roomR(uT - 0.10), 0.0);
  float rh = pow(max(rp * rp * rp - Rh * Rh * Rh * 0.55, 0.0), 1.0 / 3.0);
  vec2 q = uRoomC + d / rp * mix(rp, rh, step(0.002, Rh) * smoothstep(Rh * 0.95, Rh * 1.35, rp)) + uPar * 0.08;   // inside the room the far haze stays where it was (no seam where the push would collapse)
  float hole = Rh > 0.002 ? mix(min(uKeep * 2.2, 0.6), 1.0, smoothstep(Rh * 0.30, Rh * 1.45, rp)) : 1.0;
  float ring = Rh > 0.002 ? exp(-pow((rp - Rh * 1.14) / (Rh * 0.17 + 0.002), 2.0)) * min(Rh / 0.7, 1.0) : 0.0;
  if (uKeep > 0.001) {                                           // the soft room: the mist is carried outward and thins toward her, lumpy, no edge and no ring
    float Rs = max(roomRSoft(uT - 0.10), 0.0) * (1.0 + 0.30 * clumpR(vP) + wobR(atan(d.y, d.x)));
    float x = rp / max(Rs, 1e-4);
    q = uRoomC + d * (1.0 - 0.42 * exp(-x * x)) + uPar * 0.08;
    hole = mix(0.40, 1.0, smoothstep(0.25, 1.55, x)); ring = 0.0;
  }
  vec3 p3 = vec3(q * 0.9, 0.3 + uT * 0.004);
  float n1 = 0.5 + 0.5 * fbm5(p3 * 1.1 + vec3(3.1, 0.0, 0.0));
  float n2 = 0.5 + 0.5 * fbm3(p3 * 2.3 + vec3(0.0, 7.7, 0.0));
  float n3 = 0.5 + 0.5 * fbm5(p3 * 1.6 + vec3(9.2, 4.1, 0.0));
  float fine = 0.5 + 0.5 * fbm5(vec3(q * 7.0, 1.3));
  // the Milky Way: a soft band with dark lanes and bright knots
  vec2 bn = vec2(-uBand.y, uBand.x); float across = dot(q - vec2(0.0, 0.10), bn) + 0.10 * sin(dot(q, uBand) * 1.4 + 0.6);
  float band = exp(-pow(across / 0.34, 2.0));
  float lanes = smoothstep(0.30, 0.75, 0.5 + 0.5 * fbm5(vec3(q * 3.2 + bn * across * 2.0, 5.0)));
  float knots = pow(fine, 3.0) * 2.2;
  vec3 SECOND = uVio; vec3 TEAL = vec3(0.02, 0.50, 0.55);
  vec3 mist = smoothstep(0.52, 0.86, n1) * SECOND * 0.013 * (0.4 + n2)
            + smoothstep(0.50, 0.82, n3) * (1.0 - smoothstep(0.48, 0.80, n1)) * (TEAL * 0.020 + uHer * 0.003);
  vec3 mw = (mix(vec3(0.030, 0.050, 0.085), SECOND * 0.060, smoothstep(0.35, 0.75, n2)) + TEAL * 0.030 * n3) * band * (0.25 + 0.75 * lanes) * (0.45 + knots);
  vec3 glow = (mist * 1.5 + mw * 0.62) * hole * (1.0 + 0.25 * ring);
  glow += ring * (0.35 + fine) * (SECOND * 0.0075 + TEAL * 0.010 + uHer * 0.003) * 0.3;
  float y01 = 0.5 + 0.5 * vP.y;
  vec3 base = vec3(0.0036, 0.0072, 0.0185) * (0.80 + 0.45 * y01);
  gl_FragColor = vec4((base + glow) * uGal, 1.0);
}`;
const QV = /* glsl */ `varying vec2 vP; void main(){ vP = position.xy; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`;

const DEEP_VERT = /* glsl */ `
attribute float aSize; attribute vec3 aColor; attribute vec4 aRnd; // jit, lag, twinkle phase, depth
uniform vec2 uPar; uniform float uPxScale; uniform vec2 uC; uniform float uR; uniform float uGain; uniform float uHpx; uniform float uStrag; uniform float uKeep; uniform float uWarm; uniform vec2 uExt; uniform float uSpin;
varying vec3 vCol; varying vec3 vDir; // dir.xy unit (screen, y up), z = streak half-length / sprite size (0..)
${ROOM_GLSL}
void main(){
  vec2 hp = position.xy + uPar * aRnd.w;
  hp = mod(hp + uExt, 2.0 * uExt) - uExt;                         // a long camera drift never runs out of sky
  float stay = step(fract(aRnd.z * 13.37), uKeep) * step(dot(aColor, vec3(0.333)), 0.30) * (1.0 - position.z);   // faint far stars that take no part
  float lag = aRnd.y + uStrag * position.z;                       // position.z = 1 for the one straggler
  vec2 p = hp, p0 = hp;
  if (uRoom > 0.0005 && stay < 0.5) {
    if (uKeep > 0.001) { float u01 = fract(aRnd.z * 91.7 + 0.31); p = roomSoft(hp, uT, u01, lag); p0 = roomSoft(hp, uT - 1.0 / 60.0, u01, lag); }
    else { p = roomMap(hp, uT, aRnd.x, lag); p0 = roomMap(hp, uT - 1.0 / 60.0, aRnd.x, lag); }
  }
  if (uSpin != 0.0 && stay < 0.5) { float an = uSpin * (0.4 + 1.2 * fract(aRnd.z * 5.77)), ca = cos(an), sa = sin(an); p = uRoomC + mat2(ca, sa, -sa, ca) * (p - uRoomC); p0 = uRoomC + mat2(ca, sa, -sa, ca) * (p0 - uRoomC); }
  vec2 v = (p - p0) * uHpx;                                       // pixels moved while the shutter is open
  float L = length(v), base = aSize * uPxScale;
  float size = base + L;
  float dd = length(p - uC) / max(uR, 1e-4);
  float occ = smoothstep(0.995, 1.06, dd);
  float tw = 0.80 + 0.20 * sin(uT * (1.1 + 2.3 * fract(aRnd.z * 7.31)) + aRnd.z * 40.0);
  // the straggler blinks twice before it hurries after the others
  float blink = position.z * (0.9 * bumpR((uT - ${f(SPACE.t + 0.5)}) / 0.30) + 0.9 * bumpR((uT - ${f(SPACE.t + 0.84)}) / 0.30)) * step(0.0005, uRoom);
  float xn = clamp(p.x / uExt.x * 0.5 + 0.5, 0.0, 1.0), wv = smoothstep(0.0, 1.0, uWarm * 1.5 - xn * 0.5);
  float gl = pow(0.5 + 0.5 * sin(uT * (5.0 + 9.0 * fract(aRnd.z * 7.31)) + aRnd.z * 40.0), 3.0);   // glitter
  vec3 sc = mix(aColor, vec3(1.0, 0.68, 0.28) * dot(aColor, vec3(0.333)) * 1.8, wv);
  tw = mix(tw, 0.40 + 1.25 * gl, wv);
  base *= 1.0 + 0.45 * wv * gl; size = base + L;
  vCol = sc * occ * uGain * tw * (1.0 + blink) * (1.0 - 0.45 * stay) * (base / size) * (1.0 + 0.7 * min(L / base, 3.0));
  vDir = vec3(L > 0.01 ? v / L : vec2(1.0, 0.0), 0.5 * L / size);
  gl_PointSize = size;
  gl_Position = projectionMatrix * modelViewMatrix * vec4(p, 0.0, 1.0);
}`;
const DEEP_FRAG = /* glsl */ `
varying vec3 vCol; varying vec3 vDir;
void main(){
  vec2 q = (gl_PointCoord - 0.5) * vec2(1.0, -1.0);              // sprite units, y up
  float along = dot(q, vDir.xy), perp = dot(q, vec2(-vDir.y, vDir.x));
  float a0 = max(abs(along) - vDir.z, 0.0);                        // distance to the streak segment
  float w = max(0.5 - vDir.z, 0.02);                               // the star's own radius in sprite units
  float r2 = (a0 * a0 + perp * perp) / (w * w);
  float a = exp(-r2 * 9.0) + 0.12 * exp(-r2 * 2.5);
  if (a < 0.004) discard;
  gl_FragColor = vec4(vCol * a, 1.0);
}`;


// ---- the feed banner: 14,000 stars of the sky above her fly in and write it (targets: living_earth/proof30_banner.py) ----
const BANNER_VERT = /* glsl */ `
attribute vec2 aTarget; attribute vec4 aRnd; // delay 0..1, curl, size (px at 1440 high), part
uniform float uU; uniform float uGain; uniform float uPxScale; uniform float uT; uniform vec2 uPar; uniform vec3 uHer; uniform vec3 uVio;
varying vec3 vCol;
void main(){
  float uin = min(uU, 1.0), uout = max(uU - 1.0, 0.0);
  float a = clamp((uin - aRnd.x * 0.60) / 0.40, 0.0, 1.0); a = a * a * a * (a * (a * 6.0 - 15.0) + 10.0);
  float r1 = fract(aRnd.x * 91.7 + aRnd.y * 37.1), r2 = fract(aRnd.x * 53.3 + aRnd.y * 71.9);
  float b = clamp((uout - r1 * 0.5) / 0.5, 0.0, 1.0); b = b * b * (3.0 - 2.0 * b);
  vec2 h = position.xy + uPar * 0.15; vec2 d = aTarget - h;
  vec2 p = uout > 0.0 ? h + d * (1.0 - b) + vec2(d.y, -d.x) * (aRnd.y - 0.1) * sin(3.14159265 * b)
                      : h + d * a + vec2(-d.y, d.x) * aRnd.y * sin(3.14159265 * a);
  float w = a * (1.0 - b);                                        // how much of the banner this star is right now
  float part = aRnd.w;
  vec3 pc = part < 0.5 ? (uHer * 0.9 + uVio * 0.25) * 0.55 : part < 1.5 ? (uVio * 0.9 + uHer * 0.3) * 0.6 : part < 2.5 ? vec3(1.0, 0.66, 0.24) * 1.25
          : part < 3.5 ? (uHer * 0.75 + 0.3) * 0.62 : vec3(0.86, 0.96, 1.0) * 0.78;
  pc *= (0.8 + 0.4 * r2) * (r1 > 0.988 ? 1.9 : 1.0);              // a few sparkles ride on the letters
  float tw = 0.85 + 0.15 * sin(uT * (1.5 + 2.5 * r2) + r1 * 40.0);
  vec3 sky = vec3(0.75, 0.88, 1.0) * (0.10 + 0.25 * r2 * r2);
  float fly = sin(3.14159265 * (uout > 0.0 ? b : a));             // brighter while it travels
  vCol = mix(sky, pc, w) * uGain * tw * (1.0 + 0.8 * fly);
  gl_PointSize = mix(2.6 + 2.0 * r2 * r2, aRnd.z, w) * uPxScale * (1.0 + 0.35 * fly);
  gl_Position = projectionMatrix * modelViewMatrix * vec4(p, 0.0, 1.0);
}`;
const DOT_FRAG = /* glsl */ `
varying vec3 vCol;
void main(){ vec2 q = gl_PointCoord - 0.5; float r2 = dot(q, q) * 4.0; float a = exp(-r2 * 9.0) + 0.10 * exp(-r2 * 2.5); if (a < 0.004 || r2 > 1.0) discard; gl_FragColor = vec4(vCol * a, 1.0); }`;

// ---- the chip: the grain's own grains (floating, her colours) slide into rows and right angles and turn his warm gold ----
const CHIP_VERT = /* glsl */ `
attribute vec3 aFloat; attribute vec4 aRnd; // r1, r2, kind (0 cell dot, 1 trace, 2 pad, 3 core), d = distance of the seat from the middle (0..1)
uniform float uU; uniform float uGain; uniform float uPxScale; uniform float uT; uniform vec2 uCtr; uniform float uS; uniform float uTilt; uniform vec3 uHer; uniform vec3 uVio;
varying vec3 vCol;
void main(){
  float seatU = clamp(uU, 0.0, 1.0), pulseU = clamp(uU - 1.0, 0.0, 1.0), d = aRnd.w;
  float a = clamp((seatU * 1.42 - d * 0.74 - aRnd.x * 0.16) / 0.36, 0.0, 1.0) * step(aRnd.z, 3.5);        // a square front spreads from the middle (kind 4 = free grains: they never seat)
  float e = 1.0 + 2.2 * pow(a - 1.0, 3.0) + 1.2 * pow(a - 1.0, 2.0);                  // slides in with a small overshoot, settles
  float ang = (uT - 23.0) * (0.22 + 0.30 * aRnd.y);
  vec3 fl = aFloat; fl.xy = mat2(cos(ang), -sin(ang), sin(ang), cos(ang)) * fl.xy; fl.z += 0.06 * sin(uT * 1.3 + aRnd.x * 30.0);
  vec3 p = mix(fl, vec3(position.xy, 0.0), e);
  float yaw = 0.24 - 0.16 * (uT - 24.0), cy = cos(yaw), sy = sin(yaw);
  p = vec3(cy * p.x - sy * p.y, sy * p.x + cy * p.y, p.z);
  float ct = cos(uTilt), st = sin(uTilt);
  p = vec3(p.x, ct * p.y - st * p.z, st * p.y + ct * p.z);                             // laid back
  float persp = 1.0 / (1.0 + p.z * 0.34);
  vec2 sp = uCtr + p.xy * persp * uS;
  float kind = aRnd.z;
  vec3 GOLD = vec3(1.0, 0.54, 0.13);
  vec3 seatC = kind < 0.5 ? mix(GOLD * 0.55, vec3(0.50, 0.56, 1.0) * 0.30, step(0.72, aRnd.x)) : kind < 1.5 ? GOLD * 0.95 : kind < 2.5 ? (GOLD + 0.06) * 1.05 : mix(GOLD * 0.75, vec3(0.62, 0.50, 1.0) * 0.40, step(0.70, aRnd.y));
  vec3 flC = mix(uHer, uVio, step(0.62, aRnd.y)) * (0.45 + 0.9 * aRnd.x);
  float seated = smoothstep(0.55, 1.0, a);
  vec3 c = mix(flC, seatC, seated);
  c += (GOLD + 0.2) * 1.2 * exp(-pow((a - 0.93) / 0.07, 2.0)) * step(0.01, a) * (1.0 - step(0.999, a));   // a glint as it seats
  float pr = pulseU * 1.25;                                                             // the first thought: core to pads
  c *= 1.0 + 2.6 * exp(-pow((d - pr) / 0.075, 2.0)) * step(0.001, pulseU) * (1.0 - 0.45 * pulseU);
  float ideal = mix(3.6 + 4.0 * aRnd.x * aRnd.x, (kind < 0.5 ? 3.9 : kind < 1.5 ? 4.4 : kind < 2.5 ? 5.2 : 3.8) * (0.75 + 0.6 * aRnd.y * aRnd.y), seated) * uPxScale * persp * persp * (uS / 0.62);
  float size = max(ideal, 1.3 * uPxScale);
  vCol = c * uGain * 1.9 * (0.7 + 0.6 * aRnd.x) * (ideal * ideal) / (size * size);
  gl_PointSize = size;
  gl_Position = projectionMatrix * modelViewMatrix * vec4(sp, 0.0, 1.0);
}`;
function chipSeats() {
  const seat: number[] = [], kind: number[] = [];
  const dot = (x: number, y: number, k: number) => { seat.push(x, y); kind.push(k); };
  const line = (x0: number, y0: number, x1: number, y1: number, step = 0.0062) => { const n = Math.max(1, Math.round(Math.hypot(x1 - x0, y1 - y0) / step)); for (let i = 0; i <= n; i++) dot(x0 + ((x1 - x0) * i) / n, y0 + ((y1 - y0) * i) / n, 1); };
  const rect = (cx: number, cy: number, w: number, h: number) => { line(cx - w / 2, cy - h / 2, cx + w / 2, cy - h / 2); line(cx + w / 2, cy - h / 2, cx + w / 2, cy + h / 2); line(cx + w / 2, cy + h / 2, cx - w / 2, cy + h / 2); line(cx - w / 2, cy + h / 2, cx - w / 2, cy - h / 2); };
  const cells = (cx: number, cy: number, w: number, h: number, dx: number, dy: number, k: number, gapEvery = 0) => {
    const nx = Math.floor((w - 0.03) / dx), ny = Math.floor((h - 0.03) / dy);
    for (let j = 0; j <= ny; j++) for (let i = 0; i <= nx; i++) { if (gapEvery && i % gapEvery === gapEvery - 1) continue; dot(cx - (nx * dx) / 2 + i * dx, cy - (ny * dy) / 2 + j * dy, k); }
  };
  rect(0, 0, 1.64, 1.64); rect(0, 0, 1.70, 1.70);                                       // the die's edge (a double line)
  rect(0, 0, 0.56, 0.56); rect(0, 0, 0.60, 0.60); cells(0, 0, 0.56, 0.56, 0.0205, 0.0205, 3);   // the core
  const B: [number, number, number, number][] = [[0, 0.555, 0.60, 0.40], [0, -0.555, 0.60, 0.40], [0.555, 0, 0.40, 0.60], [-0.555, 0, 0.40, 0.60],
    [0.555, 0.555, 0.40, 0.40], [-0.555, 0.555, 0.40, 0.40], [0.555, -0.555, 0.40, 0.40], [-0.555, -0.555, 0.40, 0.40]];
  B.forEach(([cx, cy, w, h], bi) => { rect(cx, cy, w, h); if (bi % 2 === 0) cells(cx, cy, w, h, 0.021, 0.033, 0, 6); else cells(cx, cy, w, h, 0.033, 0.021, 0); });
  for (const s of [-1, 1]) for (const o of [-0.10, 0, 0.10]) { line(o, s * 0.30, o, s * 0.355); line(s * 0.30, o, s * 0.355, o); }   // buses core -> blocks
  for (const s of [-1, 1]) for (const t of [-1, 1]) { line(s * 0.30, t * 0.30, s * 0.355, t * 0.355); }
  for (let side = 0; side < 4; side++) for (let i = 0; i < 15; i++) {                    // 60 pads and their leads
    const u = -0.77 + (1.54 * i) / 14, a = side * Math.PI / 2, c = Math.cos(a), sn = Math.sin(a);
    const P = (x: number, y: number): [number, number] => [c * x - sn * y, sn * x + c * y];
    const [l0x, l0y] = P(u, 0.85), [l1x, l1y] = P(u, 0.925); line(l0x, l0y, l1x, l1y);
    for (let j = -1; j <= 1; j++) for (let k = -1; k <= 1; k++) { const [px, py] = P(u + j * 0.013, 0.955 + k * 0.013); dot(px, py, 2); }
  }
  for (let i = 0; i < 2200; i++) dot(0, 0, 4);                                           // free grains of hers that keep drifting around the die (depth)
  return { seat, kind };
}

// ---- the shore: sharp faceted grains (procedural at any zoom, so the dive is one true zoom), her plankton glowing in the
// wet film between them and in the tide lines, a thin glowing surf at the far edge, and ONE grain lit from inside ----
const SAND_FRAG = /* glsl */ `
precision highp float;
varying vec2 vP; uniform float uT; uniform float uSand; uniform float uDive; uniform vec3 uHer; uniform vec3 uVio;
${NOISE}
vec2 h22(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * vec3(0.1031, 0.1030, 0.0973)); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.xx + p3.yz) * p3.zy); }
float h12(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * 0.1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
const vec2 HERO = vec2(0.0, -0.22); const float YH = 0.40; const float SC = 8.5;   // grains big enough to read one by one (earth_pol_open)
vec3 mineral(float r){ return r < 0.34 ? vec3(0.62, 0.66, 0.68) : r < 0.52 ? vec3(0.10, 0.11, 0.14) : r < 0.66 ? vec3(0.55, 0.47, 0.40) : r < 0.76 ? vec3(0.24, 0.36, 0.26) : r < 0.84 ? vec3(0.40, 0.16, 0.20) : r < 0.93 ? vec3(0.66, 0.68, 0.68) : vec3(0.36, 0.26, 0.60); }
vec3 grainLayer(vec2 g, float wash, float heroLight, float seed, out float gapOut){
  g += 0.24 * vec2(snoise(vec3(g * 0.8, seed)), snoise(vec3(g * 0.8 + 7.0, seed + 3.0)));   // no two grains the same shape
  vec2 ip = floor(g), fp = fract(g); float d1 = 9.0, d2 = 9.0; vec2 id = vec2(0.0), off = vec2(0.0);
  for (int j = -1; j <= 1; j++) for (int i = -1; i <= 1; i++) {
    vec2 o = vec2(float(i), float(j)); vec2 r = o + 0.12 + 0.76 * h22(ip + o + seed) - fp; float d = dot(r, r);
    if (d < d1) { d2 = d1; d1 = d; id = ip + o; off = -r; } else if (d < d2) d2 = d;
  }
  d1 = sqrt(d1); d2 = sqrt(d2);
  float edge = d2 - d1;
  vec2 rnd = h22(id + seed + 7.3); float r3 = h12(id + seed + 3.1);
  float nf = 5.0 + floor(rnd.y * 3.0);
  float ang = atan(off.y, off.x) + rnd.x * 6.2832;
  float fi = floor(ang / 6.2832 * nf), ff = fract(ang / 6.2832 * nf);
  float fa = (fi + 0.5) / nf * 6.2832 - rnd.x * 6.2832;
  vec3 nDome = normalize(vec3(off * 1.9, 0.55));
  vec3 nFac = normalize(vec3(cos(fa) * 0.8, sin(fa) * 0.8, 0.75));
  vec3 n = normalize(mix(nDome, nFac, 0.28) + 0.24 * vec3(snoise(vec3(g * 5.0, seed)), snoise(vec3(g * 5.0 + 9.0, seed)), 0.0));   // a rounded grain with a hint of crystal and its own roughness
  vec3 Lsurf = normalize(vec3(0.15, 0.80, 0.45)); vec3 Lmoon = normalize(vec3(-0.5, 0.2, 0.85)); vec3 V = vec3(0.0, -0.55, 0.83);
  float dif = max(dot(n, Lsurf), 0.0), difM = max(dot(n, Lmoon), 0.0);
  float sp = pow(max(dot(n, normalize(Lsurf + V)), 0.0), 48.0) + 0.7 * pow(max(dot(n, normalize(Lmoon + V + vec3(0.25 * sin(uT * 0.9 + rnd.x * 20.0), 0.0, 0.0))), 0.0), 70.0);
  // Violet minerals sit in the unlit bed. Cyan is reserved for wet edges and living emitters.
  vec3 mcol = mineral(r3);
  float strata = 0.5 + 0.5 * snoise(vec3(id * 0.12, seed + 19.0));
  mcol = mix(mcol, mcol * vec3(0.78, 0.62, 1.12), 0.65 * strata);
  vec3 col = mcol * (0.008 + dif * (uHer * 0.17 + vec3(0.012)) + difM * vec3(0.045, 0.058, 0.095) + heroLight * uHer * 0.40 * (0.3 + dif));
  col += (uHer * 0.8 + 0.30) * sp * (0.5 + heroLight * 1.0) * step(0.45, rnd.y);          // wet glints on some grains
  float thin = smoothstep(0.32, 0.04, edge);                                              // thin edges let her light through
  col += uHer * mcol * (0.22 + 0.9 * wash) * thin * 0.40;
  col *= 0.66 + 0.68 * (0.5 + 0.5 * snoise(vec3(g * 11.0, seed)));                        // its own roughness
  col *= 0.80 + 0.40 * step(0.55, 0.5 + 0.5 * snoise(vec3(g * 27.0, seed + 5.0)));        // pits and chips: fine, hard-edged
  vec2 mg = g * 13.0; vec2 mi = floor(mg); vec2 mf = fract(mg) - 0.5 - 0.3 * (h22(mi + seed) - 0.5);
  col += (uHer * 0.9 + 0.35) * step(0.93, h12(mi + seed + 2.7)) * exp(-dot(mf, mf) * 70.0) * (0.25 + 0.75 * dif) * 0.55;   // crystal faces that catch the light: tiny sharp sparks on the grain
  col += uHer * (0.08 + 0.34 * wash) * smoothstep(0.16, 0.05, edge) * smoothstep(0.02, 0.06, edge);   // every grain rimmed by the glow under it: you can count them
  col += (uHer * 1.5 + 0.1) * step(0.90, h12(id + seed + 11.7)) * (0.55 + 0.45 * sin(uT * 2.0 + rnd.x * 30.0)) * (0.3 + 0.7 * nDome.z);   // a few grains are her plankton: they glow on their own
  float gap = 1.0 - smoothstep(0.03, 0.13 + 0.10 * rnd.x, edge);                          // grains lie apart, each its own size: dark wet film between them
  gap = max(gap, step(0.90, h12(id + seed + 23.1)) * smoothstep(0.42, 0.30, d1));         // here and there a grain is missing: a pool of her light
  col = mix(col, vec3(0.002, 0.006, 0.011) + (uHer * 1.5 + uVio * 0.25) * (0.095 + 0.50 * wash) * (0.45 + 0.9 * pow(0.5 + 0.5 * snoise(vec3(g * 6.0, seed + uT * 0.25)), 2.0)), gap);   // (the film is alive: it shimmers, it is never a flat patch)   // her plankton glows in the wet film between the grains
  gapOut = gap; return col;
}
void main(){
  float dive = max(uDive, 0.0), fall = max(-uDive, 0.0);
  float Z = exp(dive * 3.75);                                // 42x: one true zoom into the one grain
  vec2 s = HERO + (vP - HERO) / Z;
  float H = 1.0 + 2.2 * fall * fall;                         // the camera comes down onto the shore
  float below = YH - s.y;
  vec3 col;
  if (below > 0.0) {
    float zf = 1.0 / max(below, 0.003);
    vec2 G = vec2(s.x * zf, zf) * H; vec2 g = G * SC;
    vec2 G0 = vec2(HERO.x, 1.0) / (YH - HERO.y);
    float fw = max(length(dFdx(g)), length(dFdy(g))) * pow(3.0, floor(log(Z) / log(3.0)));        // grains per pixel
    float wl = sin(G.y * 7.0 + 1.2 * snoise(vec3(G * 1.3, 0.0)) + 0.6 * snoise(vec3(G * 4.0, 2.0)));
    float wash = smoothstep(0.66, 0.99, wl) * (0.25 + 0.75 * smoothstep(-0.2, 0.6, snoise(vec3(G * 0.7, 5.0))));
    wash += 0.16 * pow(max(snoise(vec3(G * 9.0, uT * 0.15)), 0.0), 3.0);
    vec2 hd = (G - G0) * SC;                                  // grain units from the one grain
    float heroLight = exp(-dot(hd, hd) / 26.0) * 0.7;
    // the dive never lands on big tiles: as we close in, each grain resolves into finer grains (two octaves cross-fading)
    float lz = log(Z) / log(3.0), kz = floor(lz), fz = lz - kz, s0 = pow(3.0, kz);
    float gap, gap2, gap3; vec3 cA = grainLayer(g * s0 + kz * 17.0, wash, heroLight, kz, gap); vec3 cB = grainLayer(g * s0 * 3.0 + (kz + 1.0) * 17.0, wash, heroLight, kz + 1.0, gap2);
    vec3 cF = grainLayer(g * s0 * 2.7 + vec2(13.0, 13.0 + fall * 1.8), wash, heroLight, 5.0, gap3);
    // Recessed finer grains travel more slowly under the near bed as the camera descends.
    vec3 c1 = mix(cA, cF * 0.66, gap * 0.65 * (1.0 - fz));
    col = mix(c1, cB, smoothstep(0.25, 0.9, fz));
    vec3 avgc = vec3(0.008, 0.014, 0.022) + uHer * (0.010 + 0.30 * wash);
    col = mix(col, avgc, smoothstep(0.36, 0.85, fw));         // far away the grains resolve to their average (no shimmer)
    // the one grain: it simply glows from inside, and lights its neighbours
    float core = exp(-dot(hd, hd) / 1.5);
    col += (uHer * 0.60 + 0.10) * (1.0 - 0.55 * dive) * core * (1.0 - 0.7 * gap) * (0.9 + 0.1 * sin(uT * 2.2)) + uHer * 0.03 * exp(-dot(hd, hd) / 160.0);
    col += (uHer * 0.030 + uVio * 0.018) * (0.5 + 0.5 * fbm3(vec3(G * 0.5, uT * 0.1))) * smoothstep(1.2, 7.0, zf);   // her mist low over the bed, further out
    // the surf at the far edge: thin bright lines, never a blur
    float far = smoothstep(0.075, 0.0, below);
    float surf = 0.0;
    for (int k = 0; k < 3; k++) { float fk = float(k); float cy = 0.004 + 0.011 * pow(fk, 1.45) + 0.0035 * snoise(vec3(s.x * (5.0 - fk * 0.6) + fk * 7.0, uT * 0.22, fk));
      surf += exp(-pow((below - cy) / (0.0008 + 0.0004 * fk), 2.0)) * (0.55 + 0.45 * snoise(vec3(s.x * 14.0 + fk * 3.0, uT * 0.5, fk * 2.0))) * (1.0 - 0.13 * fk); }
    col = mix(col, vec3(0.003, 0.008, 0.018) + uHer * 0.012, far * 0.9) + (uHer * 0.60 + 0.08) * max(surf, 0.0) * step(below, 0.09);
    col += (uHer * 0.022 + uVio * 0.016) * exp(-below / 0.06);                                      // her mist over the water's edge
  } else {
    float up = -below;
    col = vec3(0.004, 0.008, 0.020) + uHer * 0.035 * exp(-up / 0.03) + uVio * 0.028 * exp(-up / 0.20);
    vec2 sc = floor(s * 95.0); float st = h12(sc + 1.7);
    col += vec3(0.8, 0.9, 1.0) * step(0.972, st) * (0.25 + 0.75 * h12(sc + 9.1)) * exp(-dot(fract(s * 95.0) - 0.5, fract(s * 95.0) - 0.5) * 26.0) * 0.9;
  }
  // inside the grain: deep blue-violet, her light at its heart, faint inner planes of the crystal
  float ins = smoothstep(0.62, 0.96, dive);
  // (earth_pol_open: no fog. A clear dark crystal: its inner planes are flat facets with thin sharp edges that catch her light,
  // and her plankton hangs in it as crisp points. The chip's own grains are drawn over this by the chip layer.)
  vec2 q = vP * 1.15 + vec2(0.05 * (uT - 23.5), 0.0); vec2 ip = floor(q), fp = fract(q); float d1 = 9.0, d2 = 9.0; vec2 cid = vec2(0.0), cof = vec2(0.0);
  for (int j = -1; j <= 1; j++) for (int i = -1; i <= 1; i++) { vec2 o = vec2(float(i), float(j)); vec2 r = o + h22(ip + o + 41.0) - fp; float d = dot(r, r); if (d < d1) { d2 = d1; d1 = d; cid = ip + o; cof = r; } else if (d < d2) d2 = d; }
  float fedge = sqrt(d2) - sqrt(d1), fr = h12(cid + 2.0), fr2 = h12(cid + 5.0);
  float plane = 0.5 + 0.5 * dot(normalize(cof + 1e-4), vec2(cos(fr * 6.2832), sin(fr * 6.2832)));          // each facet is a flat plane with its own slope
  float cen = exp(-dot(vP, vP) / 1.6);
  vec3 insideCol = vec3(0.0030, 0.0065, 0.0240) * (0.55 + 0.9 * fr2) + mix(uHer, uVio, fr) * (0.006 + 0.030 * plane * fr2) * (0.35 + 0.65 * cen);
  insideCol += (uHer * 0.30 + uVio * 0.10) * (1.0 - smoothstep(0.002, 0.009, fedge)) * (0.25 + 0.75 * fr2) * (0.12 + 0.88 * (1.0 - cen));   // facet edges: hair-thin lines, out toward the rim (the middle is the chip's)
  vec2 sg = vP * 17.0; vec2 si = floor(sg); vec2 sf = fract(sg) - 0.5 - 0.6 * (h22(si + 3.0) - 0.5); float son = step(0.80, h12(si + 9.0));
  insideCol += (uHer * 1.1 + 0.15) * son * exp(-dot(sf, sf) * 420.0) * (0.35 + 0.65 * (0.5 + 0.5 * sin(uT * 2.6 + h12(si) * 40.0))) * (0.4 + 0.6 * h12(si + 4.0));   // plankton: crisp points
  col = mix(col, insideCol, ins);
  gl_FragColor = vec4(col * uSand, uSand);
}`;

const ADD = { blending: THREE.CustomBlending, blendSrc: THREE.OneFactor, blendDst: THREE.OneFactor, blendSrcAlpha: THREE.ZeroFactor, blendDstAlpha: THREE.OneFactor, depthTest: false, depthWrite: false, transparent: true } as const;
export const N_DEEP = 42000;

export function makeExtras(o: { A: number; fmt: Fmt; height: number }) {
  const { A, fmt, height } = o;
  const quad = new THREE.PlaneGeometry(2 * A, 2);
  const bandDir = new THREE.Vector2(A * 0.95, 0.55).normalize();
  // ---- galaxy ----
  const galMat = new THREE.ShaderMaterial({ vertexShader: QV, fragmentShader: GALAXY_FRAG, ...ADD,
    uniforms: { uT: { value: 0 }, uRoom: { value: 0 }, uRoomC: { value: new THREE.Vector2() }, uGal: { value: 0 }, uPar: { value: new THREE.Vector2() }, uBand: { value: bandDir }, uHer: { value: new THREE.Vector3() }, uVio: { value: new THREE.Vector3() }, uA: { value: A }, uKeep: { value: 0 } } });
  const galaxy = new THREE.Mesh(quad, galMat); galaxy.renderOrder = -2; galaxy.frustumCulled = false;
  // ---- deep stars ----
  const g = new THREE.BufferGeometry(), R = rng(fmt === '169' ? 4107 : 4111);
  const P = new Float32Array(N_DEEP * 3), S = new Float32Array(N_DEEP), Cc = new Float32Array(N_DEEP * 3), Rn = new Float32Array(N_DEEP * 4);
  const gauss = () => (R() + R() + R() + R() - 2) * 1.22;
  const nDeep = fmt === '916' ? 11500 : N_DEEP;                 // the narrow frame holds a third of the sky: a third of the stars
  let strag = -1, stragScore = 1e9;
  for (let i = 0; i < N_DEEP; i++) {
    let x: number, y: number; const inBand = R() < 0.42;
    if (inBand) { const s = (R() * 2 - 1) * 1.35 * Math.hypot(A, 1), off = gauss() * 0.22; x = bandDir.x * s - bandDir.y * off; y = 0.10 + bandDir.y * s + bandDir.x * off + 0.10 * Math.sin(s * 1.4 + 0.6) * bandDir.x; }
    else { x = (R() * 2 - 1) * A * 1.12; y = (R() * 2 - 1) * 1.12; }
    const m = Math.pow(R(), 4.2);                                  // a steep power law: a haze of faint ones, few bright
    P[i * 3] = x; P[i * 3 + 1] = y; P[i * 3 + 2] = 0;
    S[i] = 1.9 + 4.6 * m + (inBand ? 0 : 0.3);
    const b = (0.10 + 1.5 * m) * (inBand ? 0.85 : 1.0), tmp = R();
    const c = tmp < 0.5 ? [0.72, 0.86, 1.0] : tmp < 0.8 ? [1.0, 0.97, 0.92] : tmp < 0.93 ? [1.0, 0.84, 0.66] : [0.62, 0.95, 1.0];
    Cc.set([c[0] * b, c[1] * b, c[2] * b], i * 3);
    Rn.set([gauss(), R() * 0.10, R(), 0.05 + 0.25 * R()], i * 4);
    // the straggler: a star close to her, up and to the left, that notices late
    const dx = x - SPACE.cx, dy = y - SPACE.cy, rr = Math.hypot(dx, dy), sc = Math.abs(rr - 0.235) + Math.abs(Math.atan2(dy, dx) - 2.76) * 0.2;
    if (i < nDeep && rr > 0.19 && rr < 0.28 && sc < stragScore) { stragScore = sc; strag = i; }
  }
  if (strag >= 0) { P[strag * 3 + 2] = 1; S[strag] = 6.4; Cc.set([0.85 * 1.5, 0.95 * 1.5, 1.5], strag * 3); Rn[strag * 4 + 1] = 0; }
  g.setAttribute('position', new THREE.BufferAttribute(P, 3)); g.setAttribute('aSize', new THREE.BufferAttribute(S, 1));
  g.setAttribute('aColor', new THREE.BufferAttribute(Cc, 3)); g.setAttribute('aRnd', new THREE.BufferAttribute(Rn, 4));
  g.boundingSphere = new THREE.Sphere(new THREE.Vector3(), 1e6); g.setDrawRange(0, nDeep);
  const deepMat = new THREE.ShaderMaterial({ vertexShader: DEEP_VERT, fragmentShader: DEEP_FRAG, ...ADD,
    uniforms: { uT: { value: 0 }, uRoom: { value: 0 }, uRoomC: { value: new THREE.Vector2() }, uPar: { value: new THREE.Vector2() }, uPxScale: { value: 1 }, uC: { value: new THREE.Vector2() }, uR: { value: 1 }, uGain: { value: 0 }, uHpx: { value: height / 2 }, uStrag: { value: 1.2 }, uKeep: { value: 0 }, uWarm: { value: 0 }, uSpin: { value: 0 }, uExt: { value: new THREE.Vector2(A * 1.12, 1.12) } } });
  const deep = new THREE.Points(g, deepMat); deep.renderOrder = -1; deep.frustumCulled = false;


  // ---- banner ----
  const bd = BANNER[fmt], raw = Uint8Array.from(atob(bd.b64), (ch) => ch.charCodeAt(0)), bi = new Int16Array(raw.buffer);
  const bg = new THREE.BufferGeometry(), bP = new Float32Array(bd.n * 3), bT = new Float32Array(bd.n * 2), bR = new Float32Array(bd.n * 4);
  for (let i = 0; i < bd.n; i++) { const o = i * 8; bP[i * 3] = bi[o] / 1e4; bP[i * 3 + 1] = bi[o + 1] / 1e4; bT[i * 2] = bi[o + 2] / 1e4; bT[i * 2 + 1] = bi[o + 3] / 1e4; bR[i * 4] = bi[o + 4] / 1e4; bR[i * 4 + 1] = bi[o + 5] / 1e4; bR[i * 4 + 2] = bi[o + 6] / 1e3; bR[i * 4 + 3] = bi[o + 7] / 1e3; }
  bg.setAttribute('position', new THREE.BufferAttribute(bP, 3)); bg.setAttribute('aTarget', new THREE.BufferAttribute(bT, 2)); bg.setAttribute('aRnd', new THREE.BufferAttribute(bR, 4));
  bg.boundingSphere = new THREE.Sphere(new THREE.Vector3(), 1e6);
  const banMat = new THREE.ShaderMaterial({ vertexShader: BANNER_VERT, fragmentShader: DOT_FRAG, ...ADD,
    uniforms: { uU: { value: 0 }, uGain: { value: 0 }, uPxScale: { value: 1 }, uT: { value: 0 }, uPar: { value: new THREE.Vector2() }, uHer: { value: new THREE.Vector3() }, uVio: { value: new THREE.Vector3() } } });
  const banner = new THREE.Points(bg, banMat); banner.renderOrder = 6.5; banner.frustumCulled = false;
  // ---- chip ----
  const cs = chipSeats(), nC = cs.kind.length, cg = new THREE.BufferGeometry(), R2 = rng(2311);
  const cP = new Float32Array(nC * 3), cF = new Float32Array(nC * 3), cR = new Float32Array(nC * 4);
  for (let i = 0; i < nC; i++) {
    const x = cs.seat[i * 2], y = cs.seat[i * 2 + 1]; cP[i * 3] = x; cP[i * 3 + 1] = y;
    const free = cs.kind[i] > 3.5, ra = Math.pow(R2(), 0.6) * (free ? 2.6 : 1.25), th = R2() * 6.2832; cF[i * 3] = ra * Math.cos(th) * 1.25; cF[i * 3 + 1] = ra * Math.sin(th) * 0.9; cF[i * 3 + 2] = (R2() - 0.5) * (free ? 2.4 : 0.9);
    cR[i * 4] = R2(); cR[i * 4 + 1] = R2(); cR[i * 4 + 2] = cs.kind[i]; cR[i * 4 + 3] = free ? 3 : Math.min(1, Math.max(Math.abs(x), Math.abs(y)));
  }
  cg.setAttribute('position', new THREE.BufferAttribute(cP, 3)); cg.setAttribute('aFloat', new THREE.BufferAttribute(cF, 3)); cg.setAttribute('aRnd', new THREE.BufferAttribute(cR, 4));
  cg.boundingSphere = new THREE.Sphere(new THREE.Vector3(), 1e6);
  const chipMat = new THREE.ShaderMaterial({ vertexShader: CHIP_VERT, fragmentShader: DOT_FRAG, ...ADD,
    uniforms: { uU: { value: 0 }, uGain: { value: 0 }, uPxScale: { value: 1 }, uT: { value: 0 }, uCtr: { value: new THREE.Vector2() }, uS: { value: 0.6 }, uTilt: { value: 0.5 }, uHer: { value: new THREE.Vector3() }, uVio: { value: new THREE.Vector3() } } });
  const chip = new THREE.Points(cg, chipMat); chip.renderOrder = 5.5; chip.frustumCulled = false;
  // ---- sand ----
  const sandMat = new THREE.ShaderMaterial({ vertexShader: QV, fragmentShader: SAND_FRAG, transparent: true, depthTest: false, depthWrite: false,
    blending: THREE.CustomBlending, blendSrc: THREE.OneFactor, blendDst: THREE.OneMinusSrcAlphaFactor, blendSrcAlpha: THREE.OneFactor, blendDstAlpha: THREE.OneMinusSrcAlphaFactor,
    uniforms: { uT: { value: 0 }, uSand: { value: 0 }, uDive: { value: 0 }, uHer: { value: new THREE.Vector3() }, uVio: { value: new THREE.Vector3() } } });
  const sand = new THREE.Mesh(quad, sandMat); sand.renderOrder = 3.5; sand.frustumCulled = false;

  const objects: THREE.Object3D[] = [galaxy, deep, sand, chip, banner];
  function update(frame: Frame, pxs: number) {
    const gr = frame.grade, cam = frame.cam, t = frame.t;
    galaxy.visible = gr.galaxy > 0.001; deep.visible = gr.deep > 0.001;
    const gu = galMat.uniforms; gu.uT.value = t; gu.uRoom.value = gr.room; gu.uRoomC.value.set(gr.roomX, gr.roomY); gu.uGal.value = gr.galaxy; gu.uKeep.value = gr.roomKeep; gu.uPar.value.set(cam.par[0], cam.par[1]);
    gu.uHer.value.set(...gr.herColor); gu.uVio.value.set(...gr.violetColor);
    const du = deepMat.uniforms; du.uT.value = t; du.uRoom.value = gr.room; du.uRoomC.value.set(gr.roomX, gr.roomY); du.uPar.value.set(cam.par[0], cam.par[1]);
    du.uPxScale.value = pxs * (fmt === '916' ? 0.78 : 1); du.uC.value.set(cam.x, cam.y); du.uR.value = cam.r; du.uGain.value = gr.deep * gr.stars; du.uKeep.value = gr.roomKeep; du.uWarm.value = gr.starWarm; du.uSpin.value = gr.roomSpin;
    banner.visible = gr.banner > 0.001; chip.visible = gr.chip > 0.001; sand.visible = gr.sand > 0.001;
    const bu = banMat.uniforms; bu.uU.value = gr.bannerU; bu.uGain.value = gr.banner; bu.uPxScale.value = pxs; bu.uT.value = t; bu.uPar.value.set(cam.par[0], cam.par[1]); bu.uHer.value.set(...gr.herColor); bu.uVio.value.set(...gr.violetColor);
    const cu = chipMat.uniforms; cu.uU.value = gr.chipU; cu.uGain.value = gr.chip; cu.uPxScale.value = pxs; cu.uT.value = t; cu.uCtr.value.set(gr.chipX, gr.chipY); cu.uS.value = gr.chipS * (fmt === '916' ? 0.5 : 1); cu.uTilt.value = gr.chipTilt; cu.uHer.value.set(...gr.herColor); cu.uVio.value.set(...gr.violetColor);
    const su = sandMat.uniforms; su.uT.value = t; su.uSand.value = gr.sand; su.uDive.value = gr.sandDive; su.uHer.value.set(...gr.herColor); su.uVio.value.set(...gr.violetColor);
  }
  return { objects, update };
}
