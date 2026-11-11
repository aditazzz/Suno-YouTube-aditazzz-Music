// Canvas drawing for the city, ported from the approved frame 2 code (design/frames.html: gt3, trafficLight, pigeons),
// colours from palette.json (theme P / C). Each function draws in local px at the given origin and scale.
import { C, P } from '../../theme';

type X = CanvasRenderingContext2D;
export const rr = (c: X, x: number, y: number, w: number, h: number, r: number) => {
  c.beginPath(); c.moveTo(x + r, y); c.arcTo(x + w, y, x + w, y + h, r); c.arcTo(x + w, y + h, x, y + h, r); c.arcTo(x, y + h, x, y, r); c.arcTo(x, y, x + w, y, r); c.closePath();
};

/**
 * The GT3 RS, side profile (approved frame 2), Ultraviolet with yellow calipers. Origin = rear-wheel ground point, faces right.
 * wheelA = wheel spin (rad), pitch = body pitch (rad, + = nose down: the brake dip), sq = vertical squash (1 = none),
 * rim = 0..1 thin amber rim light along the top (PALETTE flag 3: against the sky), shadow = 0..1 ground shadow.
 */
export function gt3(c: X, x: number, y: number, s: number, o: { wheelA?: number; pitch?: number; sq?: number; rim?: number; shadow?: number; lift?: number } = {}) {
  const UV = C.purple, UVhi = C.purpleHi, UVlo = C.purpleLo, CAL = C.caliper;
  const { wheelA = 0, pitch = 0, sq = 1, rim = 0, shadow = 1, lift = 0 } = o;
  const WY = -44, WR = 44, wheels = [104, 368];
  c.save(); c.translate(x, y); c.scale(s, s);
  // ground shadow + the warm reflection strip on the road under it (flag 3), shrinking as the car lifts
  if (shadow > 0) {
    const k = shadow / (1 + lift / 120);
    c.fillStyle = `rgba(0,0,0,${0.5 * k})`; c.beginPath(); c.ellipse(236, 2, 250 * (0.6 + 0.4 / (1 + lift / 200)), 9, 0, 0, Math.PI * 2); c.fill();
    c.fillStyle = `rgba(255,207,122,${0.07 * k})`; c.beginPath(); c.ellipse(236, 12, 220, 6, 0, 0, Math.PI * 2); c.fill();
  }
  c.translate(0, -lift);
  c.translate(236, -40); c.scale(1 / Math.sqrt(sq), sq); c.translate(-236, 40); // squash about the axle line
  // wheels first (body sits over the arches); the body pitches over them
  const body = () => {
    c.strokeStyle = '#3a3448'; c.lineWidth = 7; c.lineCap = 'round';
    c.beginPath(); c.moveTo(72, -112); c.quadraticCurveTo(58, -140, 62, -172); c.stroke();
    c.beginPath(); c.moveTo(128, -128); c.quadraticCurveTo(116, -150, 118, -172); c.stroke();
    c.beginPath();
    c.moveTo(12, -40); c.lineTo(6, -74); c.quadraticCurveTo(8, -96, 28, -102);
    c.bezierCurveTo(74, -118, 150, -146, 236, -150);
    c.bezierCurveTo(272, -152, 304, -142, 336, -120);
    c.bezierCurveTo(376, -112, 420, -104, 448, -88);
    c.bezierCurveTo(464, -78, 468, -56, 462, -42);
    c.closePath();
    const g = c.createLinearGradient(0, -150, 0, -40); g.addColorStop(0, UVhi); g.addColorStop(0.35, UV); g.addColorStop(1, UVlo);
    c.fillStyle = g; c.fill();
    if (rim > 0) { // amber rim along the roof line, facing the windows' light
      c.strokeStyle = `rgba(255,207,122,${0.75 * rim})`; c.lineWidth = 3; c.beginPath(); c.moveTo(28, -102);
      c.bezierCurveTo(74, -118, 150, -146, 236, -150); c.bezierCurveTo(272, -152, 304, -142, 336, -120); c.bezierCurveTo(376, -112, 420, -104, 448, -88); c.stroke();
    }
    for (const wx of wheels) { c.fillStyle = '#0a0910'; c.beginPath(); c.arc(wx, WY, WR + 7, Math.PI, 0); c.lineTo(wx + WR + 7, -40); c.lineTo(wx - WR - 7, -40); c.closePath(); c.fill(); }
    c.fillStyle = '#120f18'; c.fillRect(160, -48, 150, 8); c.fillRect(420, -44, 46, 5);
    c.strokeStyle = 'rgba(200,170,255,.45)'; c.lineWidth = 2.5; c.beginPath(); c.moveTo(30, -98); c.bezierCurveTo(140, -112, 300, -112, 446, -86); c.stroke();
    c.beginPath(); c.moveTo(122, -112); c.bezierCurveTo(160, -130, 206, -140, 240, -141); c.bezierCurveTo(274, -141, 300, -132, 322, -114); c.closePath();
    c.fillStyle = '#16131f'; c.fill(); c.strokeStyle = '#0c0a12'; c.lineWidth = 3; c.stroke();
    c.strokeStyle = UVlo; c.lineWidth = 6; c.beginPath(); c.moveTo(232, -140); c.lineTo(228, -113); c.stroke();
    c.fillStyle = '#0f0c15'; c.beginPath(); c.moveTo(150, -82); c.lineTo(196, -88); c.lineTo(190, -66); c.lineTo(154, -64); c.closePath(); c.fill();
    c.strokeStyle = 'rgba(20,10,35,.6)'; c.lineWidth = 2; c.beginPath(); c.moveTo(318, -112); c.lineTo(312, -52); c.stroke();
    c.fillStyle = '#16131e'; rr(c, 2, -182, 160, 13, 5); c.fill(); c.strokeStyle = '#4a4260'; c.lineWidth = 2; c.stroke();
    c.fillStyle = '#16131e'; rr(c, 0, -190, 9, 32, 3); c.fill(); c.stroke(); rr(c, 155, -190, 9, 32, 3); c.fill(); c.stroke();
    c.fillStyle = '#ff3b52'; rr(c, 8, -90, 22, 7, 3); c.fill();
    c.save(); c.translate(432, -98); c.rotate(-0.55); c.fillStyle = '#fff3dc'; c.beginPath(); c.ellipse(0, 0, 13, 8.5, 0, 0, Math.PI * 2); c.fill(); c.restore();
  };
  // pitch about the front axle (nose dips under braking)
  c.save(); c.translate(368, WY); c.rotate(pitch); c.translate(-368, -WY); body(); c.restore();
  for (const wx of wheels) {
    c.fillStyle = '#09080d'; c.beginPath(); c.arc(wx, WY, WR, 0, Math.PI * 2); c.fill();
    c.fillStyle = '#2b2934'; c.beginPath(); c.arc(wx, WY, 32, 0, Math.PI * 2); c.fill();
    // calipers stay put (they don't spin with the wheel)
    c.fillStyle = CAL; c.beginPath(); c.arc(wx, WY, 28, -Math.PI * 0.98, -Math.PI * 0.42); c.arc(wx, WY, 15, -Math.PI * 0.42, -Math.PI * 0.98, true); c.closePath(); c.fill();
    c.strokeStyle = '#b4b2c0'; c.lineWidth = 3.5;
    for (let k = 0; k < 10; k++) { const a = (k / 10) * Math.PI * 2 + 0.15 + wheelA; c.beginPath(); c.moveTo(wx + Math.cos(a) * 7, WY + Math.sin(a) * 7); c.lineTo(wx + Math.cos(a) * 31, WY + Math.sin(a) * 31); c.stroke(); }
    c.fillStyle = '#e2e0ea'; c.beginPath(); c.arc(wx, WY, 6, 0, Math.PI * 2); c.fill();
  }
  c.restore();
}

/** traffic light (approved): origin = top of the pole, housing above. lamps: brightness 0..1 per [red, amber, green]. */
export function trafficLight(c: X, x: number, y: number, s: number, lamps: number[], pole = 150) {
  c.save(); c.translate(x, y); c.scale(s, s);
  c.fillStyle = '#0d0d16'; c.fillRect(-3, 0, 6, pole); rr(c, -16, -84, 32, 84, 8); c.fill();
  const cols = [P.v2.trafficRed, P.v2.trafficAmber, P.v2.trafficGreen];
  for (let i = 0; i < 3; i++) {
    const k = Math.max(0, Math.min(1, lamps[i]));
    c.save();
    if (k > 0.02) { c.shadowColor = cols[i]; c.shadowBlur = 24 * k; }
    c.fillStyle = k > 0.02 ? mixHexA('#26222f', cols[i], k) : '#26222f';
    c.beginPath(); c.arc(0, -68 + i * 26, 9, 0, Math.PI * 2); c.fill(); c.restore();
  }
  c.restore();
}
const hx = (h: string) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
export const mixHexA = (a: string, b: string, k: number) => { const A = hx(a), B = hx(b); return `rgb(${A.map((v, i) => Math.round(v + (B[i] - v) * k)).join(',')})`; };

/** one pigeon (approved stroke style), wings flap with phase (0..1); upside = flip */
export function pigeon(c: X, x: number, y: number, s: number, phase: number, upside = false, rot = 0) {
  const f = Math.sin(phase * Math.PI * 2); // -1..1
  const wy = -12 + 9 * (f * 0.5 + 0.5);    // wing tip height (approved -12 at the top of the stroke)
  c.save(); c.translate(x, y); c.rotate(rot); if (upside) c.scale(1, -1);
  c.strokeStyle = '#e8eef8'; c.lineWidth = 3 * s; c.lineCap = 'round'; c.lineJoin = 'round';
  c.beginPath(); c.moveTo(-12 * s, (wy + 6) * s); c.quadraticCurveTo(-4 * s, wy * s, 0, 0); c.quadraticCurveTo(4 * s, wy * s, 12 * s, (wy + 6) * s); c.stroke();
  c.restore();
}

/** the UI cursor (white arrow, dark outline), tip at x,y */
export function cursor(c: X, x: number, y: number, s = 1, grab = 0) {
  c.save(); c.translate(x, y); c.scale(s * (1 - 0.08 * grab), s * (1 - 0.08 * grab));
  c.beginPath(); c.moveTo(0, 0); c.lineTo(0, 34); c.lineTo(8, 26); c.lineTo(14, 40); c.lineTo(20, 37); c.lineTo(14, 24); c.lineTo(25, 24); c.closePath();
  c.fillStyle = '#f4f1f6'; c.fill(); c.strokeStyle = '#0e0e14'; c.lineWidth = 2.5; c.lineJoin = 'round'; c.stroke();
  c.restore();
}

/** a firework flame (CH1's fire ramp: core #fff3dc -> amber -> gold -> ember at the tip), pointing along angle a */
export function flame(c: X, x: number, y: number, len: number, wid: number, a: number, alpha: number) {
  if (alpha <= 0.01 || len < 1) return;
  c.save(); c.translate(x, y); c.rotate(a); c.globalAlpha = alpha;
  const g = c.createLinearGradient(0, 0, -len, 0);
  g.addColorStop(0, P.ch2.flameCore); g.addColorStop(0.3, P.ch2.window); g.addColorStop(0.65, P.ch1.gold); g.addColorStop(1, 'rgba(255,138,61,0)');
  c.fillStyle = g; c.beginPath(); c.moveTo(wid * 0.9, 0); c.quadraticCurveTo(wid * 0.6, -wid, -len * 0.25, -wid * 0.55); c.quadraticCurveTo(-len * 0.7, -wid * 0.15, -len, 0);
  c.quadraticCurveTo(-len * 0.7, wid * 0.15, -len * 0.25, wid * 0.55); c.quadraticCurveTo(wid * 0.6, wid, wid * 0.9, 0); c.fill();
  c.restore();
}
