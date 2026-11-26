// It's Written, inside the grain: the Amazon at night. WebGL2 pipeline (scene with motion-blur samples -> bloom -> tonemap -> seam field)
// and the timeline of film frames 2632..3321 (song time 87.733..110.733 s). All times below are song seconds.
const FPS = 30, F0 = 2632, NF = 690, T0 = F0 / FPS, TA = T0 - 0.6, TB = T0 + 23.6, HZ = 240, FOC = 1.05, HC = 16.0, ZBANK = 15.5, DXK = 2.6;
const sstep = (a, b, x) => { const u = Math.max(0, Math.min(1, (x - a) / (b - a))); return u * u * (3 - 2 * u); };
const clamp01 = x => Math.max(0, Math.min(1, x));
function spline(K) {   // monotone cubic through [t, v] keys
  const n = K.length, d = [], m = new Array(n);
  for (let i = 0; i < n - 1; i++) d.push((K[i + 1][1] - K[i][1]) / (K[i + 1][0] - K[i][0]));
  m[0] = d[0]; m[n - 1] = d[n - 2];
  for (let i = 1; i < n - 1; i++) m[i] = (d[i - 1] * d[i] <= 0) ? 0 : 2 * d[i - 1] * d[i] / (d[i - 1] + d[i]);
  return t => {
    if (t <= K[0][0]) return K[0][1]; if (t >= K[n - 1][0]) return K[n - 1][1];
    let i = 0; while (t > K[i + 1][0]) i++;
    const h = K[i + 1][0] - K[i][0], u = (t - K[i][0]) / h, u2 = u * u, u3 = u2 * u;
    return (2 * u3 - 3 * u2 + 1) * K[i][1] + (u3 - 2 * u2 + u) * h * m[i] + (-2 * u3 + 3 * u2) * K[i + 1][1] + (u3 - u2) * h * m[i + 1];
  };
}
const rnd = (i, k) => { const x = Math.sin(i * 127.1 + k * 311.7 + 1.3) * 43758.5453; return x - Math.floor(x); };
const ppath = s => [0.50 * Math.sin(0.42 * s) + 0.22 * Math.sin(0.97 * s + 1.3), 0.10 * Math.sin(0.33 * s + 0.7)];
let TM = null, HITS = [], V = null, MOTIF = null, XS = z => 0, RED = null;
const sway = t => { const u = t - 95.6, k = 1.5; return [k * (0.34 * Math.sin(1.15 * u) + 0.12 * Math.sin(2.3 * u + 1)), 0.07 * Math.sin(0.9 * u + 0.7)]; };
function lastIdx(A, t) { let lo = 0, hi = A.length - 1, r = -1; while (lo <= hi) { const m = (lo + hi) >> 1; if (A[m][0] <= t) { r = m; lo = m + 1; } else hi = m - 1; } return r; }
const tabN = Math.round((TB - TA) * HZ) + 1; const tabT = i => TA + i / HZ;
function tabGet(A, t) { const x = (t - TA) * HZ, i = Math.max(0, Math.min(tabN - 2, Math.floor(x))), u = Math.max(0, Math.min(1, x - i)); return A[i] * (1 - u) + A[i + 1] * u; }
// ---- the sung and whispered cues (song seconds; Codex's cue sheet, checked on the vocal stem + 0.214 s)
const CUE = { dream: 87.75, wind: 88.45, road: 89.81, who: 95.52, dont: 96.36, can: 97.64, notyet: 98.64, how: 99.51, youre: 101.47 };
const KEY = {
  y: spline([[87.1, 43], [87.733, 41], [89.2, 37], [90.4, 33.5], [91.6, 30], [93.1, 25.5], [93.8, 17.2], [94.4, 8.4], [95.0, 2.9], [95.6, 1.35], [99.3, 1.3], [101.1, 1.85], [102.4, 2.1], [103.2, 7.0], [104.0, 14.5], [104.7, 19.5], [106, 25], [108, 33], [110.9, 46]]),
  z: spline([[87.1, -166], [87.733, -150], [90, -90], [92.5, -35], [93.3, -21.5], [93.9, -14.3], [94.5, -9.2], [95.1, -6.0], [95.6, -4.9], [97.5, -3.2], [99.6, -2.1], [100.6, -1.4], [102.6, 1.9], [104, 3.9], [107, 7.4], [110.9, 12.2]]),
  pitch: spline([[87.1, -15], [89.5, -17], [91.5, -21], [92.8, -26], [93.6, -30], [94.4, -15], [95.1, -3.5], [95.7, -1.5], [99.3, -1.5], [100.6, -4.0], [102.3, -4.0], [103.2, -7], [104.2, -12], [105.6, -13], [107.2, -9], [108.6, -2], [110.9, 7]]),
  wv: spline([[100.9, 0], [101.6, 0.9], [102.6, 1.7], [103.63, 2.4], [105.9, 4.5], [108.19, 9], [110, 15], [110.9, 22]]),
  sky: spline([[104, 0], [106, 0.12], [108.5, 0.30], [110.2, 0.52], [110.9, 0.90]]), sky2: spline([[107.9, 0.255], [108.6, 0.21], [109.6, 0.22], [110.3, 0.50], [110.9, 0.90]]),   // sky2: from 107.9 s (film frame 3237) the gold of the sky holds back and closes within the last second
  dream: spline([[87.5, 0], [87.75, 0.03], [89.2, 0.85], [90.6, 1.0]]),
};
// the grade, by hand: [song second, gain]. Light swells and fades only where the picture means it; there is no automatic exposure any more.
let GRADE = t => 1;
function setGrade(K) { GRADE = (K && K.length > 1) ? spline(K) : (t => 1); }
function camOld(t) {   // the flight of the previous final: still flown before 94.9 s and after 105.3 s
  const wB = sstep(94.8, 95.6, t) * (1 - sstep(99.5, 100.6, t)), pp = sway(t), z0 = KEY.z(t);
  const p = [XS(z0 + 24) * (1 - sstep(92.4, 94.4, t)) + pp[0] * wB + DXK * sstep(99.3, 101.1, t), KEY.y(t) + pp[1] * wB, z0];
  let pit = KEY.pitch(t) * Math.PI / 180, yaw = 2.2 * Math.sin((t - T0) * 0.45 + 1.0) * Math.PI / 180;
  const bank = t < 94.5 ? -1.3 * Math.max(-5, Math.min(5, (XS(z0 + 26) - XS(z0 + 22)) / 4 * 16)) * (1 - sstep(92.4, 94.4, t)) : 0;
  return { p, pit, yaw, roll: (1.5 * Math.sin((t - T0) * 0.8) + bank + 2.5 * sstep(102, 106, t) * Math.sin(t * 0.9)) * Math.PI / 180 };
}
// ---- the great tree on the bank and the vine: the middle of the flight (94.9 to 105.3 s) goes to the tree, turns once round it on the way up, and joins the old flight above the canopy
const TX = 2.6, TZ = 6.1, YG = 0.5, VTOP = 14.3, D2R = Math.PI / 180, TWO_PI = 2 * Math.PI, T_A0 = 94.9, T_A1 = 95.7, T_J0 = 103.6, T_J1 = 104.6, T_P0 = 104.6, T_P1 = 105.3, TJ = 105.3;
const trunkR0 = h => (0.60 - 0.010 * h + 0.045 * Math.sin(0.9 * h + 1.0)) * (1 - 0.93 * sstep(11.5, 14.9, h));
const vineR = h => trunkR0(h) + 0.17 + 0.15 * Math.pow(Math.max(Math.sin(0.50 * h + 0.4), 0), 2) + 0.85 * Math.exp(-Math.max(h, 0) / 0.45);
let NK = null, VTH = null;
function makeNK() {   // distance from the tree's axis, angle round it (0 = south of it, the side we leave from), height, pitch. The first two keys are the old flight's own
  const pol = t => { const c = camOld(t), dx = c.p[0] - TX, dz = c.p[2] - TZ; return [Math.hypot(dx, dz), Math.atan2(dx, -dz) / D2R, c.p[1], c.pit / D2R]; }, a = pol(94.4), b = pol(95.0);
  NK = {
    rho: spline([[94.4, a[0]], [95.0, b[0]], [95.7, 10.0], [96.5, 7.35], [97.3, 5.4], [98.0, 3.9], [98.8, 2.7], [99.6, 2.15], [100.6, 2.05], [101.6, 2.05], [102.5, 2.15], [103.3, 2.3], [104.0, 2.3], [104.7, 1.6], [105.4, 0.8]]),
    phi: spline([[94.4, a[1]], [95.0, b[1]], [95.7, -14.2], [96.5, -17.8], [97.3, -24], [98.0, -40], [98.8, -75], [99.6, -120], [100.6, -180], [101.6, -240], [102.5, -292], [103.3, -335], [104.0, -356], [104.7, -360], [105.4, -360]]),
    y: spline([[94.4, a[2]], [95.0, b[2]], [95.7, 1.25], [96.5, 1.05], [97.3, 1.05], [98.0, 1.2], [98.8, 1.9], [99.6, 3.1], [100.6, 5.0], [101.6, 7.3], [102.5, 9.8], [103.3, 12.4], [103.7, 13.8], [104.0, 15.2], [104.3, 17.1], [104.6, 18.93], [105.4, 22.4]]),
    pitch: spline([[94.4, a[3]], [95.0, -6], [95.7, -9], [96.5, -9], [97.3, -5], [98.0, 9], [98.8, 25], [99.6, 34], [100.6, 37], [102.5, 36.5], [103.3, 36], [103.7, 31], [104.0, 22], [104.3, 6], [104.6, -7], [105.0, -12], [105.4, -12.9]]),
  };
}
function camNew(t) { const rho = NK.rho(t), phi = NK.phi(t) * D2R; return { p: [TX + rho * Math.sin(phi), NK.y(t), TZ - rho * Math.cos(phi)], pit: NK.pitch(t) * D2R, yaw: -phi }; }
function camAt(t) {   // yaw is not wrapped: it has turned once (2 pi) by the time we are above the canopy
  const o = camOld(t); if (t <= T_A0) return o; if (t >= TJ) return { p: o.p, pit: o.pit, yaw: o.yaw + TWO_PI, roll: o.roll };
  const n = camNew(t), wa = sstep(T_A0, T_A1, t), wj = sstep(T_J0, T_J1, t), w = wa * (1 - wj), wq = wa * (1 - sstep(T_P0, T_P1, t));
  return { p: [0, 1, 2].map(i => o.p[i] + (n.p[i] - o.p[i]) * w), pit: o.pit + (n.pit - o.pit) * wq, yaw: (1 - wa) * o.yaw + wa * ((1 - wj) * n.yaw + wj * (o.yaw + TWO_PI)), roll: o.roll };
}
const vthJS = h => { const x = Math.max(0, Math.min(30.99, h / 0.6)), i = Math.floor(x), f = x - i, p0 = VTH[Math.max(i - 1, 0)], p1 = VTH[i], p2 = VTH[Math.min(i + 1, 31)], p3 = VTH[Math.min(i + 2, 31)];
  return p1 + 0.5 * f * (p2 - p0 + f * (2 * p0 - 5 * p1 + 4 * p2 - p3 + f * (3 * (p1 - p2) + p3 - p0))); };
const vineP = (h, off) => { const th = vthJS(h), r = vineR(h) + (off || 0); return [TX + r * Math.sin(th), YG + h, TZ - r * Math.cos(th)]; };
const lookH = t => NK.y(t) - YG + (NK.rho(t) - 0.85) * Math.tan(Math.max(NK.pitch(t), 0) * D2R);                       // the height on the vine that the middle of the picture looks at
const topH = t => NK.y(t) - YG + (NK.rho(t) - 0.85) * Math.tan(Math.min(Math.max(NK.pitch(t) + 13, 0), 70) * D2R);      // ... and the top of the picture
const headH = t => t < 97.3 ? -0.5 : Math.min(-0.5 + (topH(Math.min(t, 103.3)) + 0.3) * sstep(97.3, 98.3, t) + 3.4 * sstep(103.0, 103.5, t), VTOP + 1.5);   // her gold climbs just ahead of us, at the top of the picture
function basis(c) {
  const cp = Math.cos(c.pit), fw = [Math.sin(c.yaw) * cp, Math.sin(c.pit), Math.cos(c.yaw) * cp];
  let rt = [fw[2], 0, -fw[0]]; const rl = Math.hypot(...rt); rt = rt.map(v => v / rl);
  const up = [fw[1] * rt[2] - fw[2] * rt[1], fw[2] * rt[0] - fw[0] * rt[2], fw[0] * rt[1] - fw[1] * rt[0]];
  return { fw, rt, up };
}
const dot3 = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
// ---- the river: a sine-generated meander (the real law of river bends), straighter along the reach we fly under the trees
function makeRiver() {
  const pts = []; let x = 0, z = 0; const ds = 0.25;
  let ph = 0.9 - 2 * Math.PI * 300 / 74;
  for (let s = -620; s <= 1100; s += ds) { const e = Math.exp(-Math.pow(s / 22, 2)), A = 1.5 * (1 - 0.93 * e) * (0.82 + 0.20 * Math.sin(s * 0.013 + 2.0)), th = A * (Math.sin(ph) + 0.14 * Math.sin(2 * ph + 0.8)) + 0.20 * (1 - e) * Math.sin(2 * Math.PI * s / 29 + 2.0); pts.push([x, z, s, th]); x += Math.sin(th) * ds; z += Math.cos(th) * ds; ph += ds * 2 * Math.PI / (74 * (1 + 0.32 * Math.sin(s * 0.021 + 1.0))); }
  const i0 = pts.findIndex(p => p[2] >= 0), ox = -2.3 - pts[i0][0], oz = -pts[i0][1]; for (const p of pts) { p[0] += ox; p[1] += oz; }
  return pts;
}
function field(pts, tr, x0, z0, size, n, stride) {
  const A = new Float32Array(n * n * 4), P = []; const m = size * 0.15;
  for (let i = 0; i < pts.length; i += stride) { const p = pts[i]; if (p[0] > x0 - m && p[0] < x0 + size + m && p[1] > z0 - m && p[1] < z0 + size + m) P.push(p); }
  const np = P.length, px = new Float32Array(np), pz = new Float32Array(np); for (let i = 0; i < np; i++) { px[i] = P[i][0]; pz[i] = P[i][1]; }
  const BS = 8, bw = Math.ceil(size / BS) + 2, bk = new Array(bw * bw);
  for (const q of tr) { const ii = Math.floor((q[0] - x0) / BS) + 1, jj = Math.floor((q[1] - z0) / BS) + 1; if (ii < 0 || jj < 0 || ii >= bw || jj >= bw) continue; (bk[jj * bw + ii] || (bk[jj * bw + ii] = [])).push(q[0], q[1], q[2]); }
  for (let j = 0; j < n; j++) { const z = z0 + (j + 0.5) / n * size; for (let i = 0; i < n; i++) { const x = x0 + (i + 0.5) / n * size; let best = 1e18, bi = 0;
    for (let k = 0; k < np; k++) { const dx = px[k] - x, dz = pz[k] - z, d = dx * dx + dz * dz; if (d < best) { best = d; bi = k; } }
    let d = Math.sqrt(best), s = np ? P[bi][2] : 0, sg = 1;
    if (np > 1) { const a = P[Math.max(0, bi - 1)], b = P[Math.min(np - 1, bi + 1)], ex = b[0] - a[0], ez = b[1] - a[1], el = ex * ex + ez * ez; const u = Math.max(0, Math.min(1, ((x - a[0]) * ex + (z - a[1]) * ez) / el)); d = Math.hypot(a[0] + ex * u - x, a[1] + ez * u - z); s = a[2] + (b[2] - a[2]) * u; sg = ((x - a[0]) * ez - (z - a[1]) * ex) >= 0 ? 1 : -1; }
    if (!np) d = 99;
    let ta = 99, thw = 0, bv = 1e9;
    if (tr.length) { const bx = Math.floor((x - x0) / BS) + 1, bz = Math.floor((z - z0) / BS) + 1;
      for (let jj = bz - 1; jj <= bz + 1; jj++) for (let ii = bx - 1; ii <= bx + 1; ii++) { if (ii < 0 || jj < 0 || ii >= bw || jj >= bw) continue; const B = bk[jj * bw + ii]; if (!B) continue;
        for (let k = 0; k < B.length; k += 3) { const dd = Math.hypot(B[k] - x, B[k + 1] - z), vv = dd - B[k + 2]; if (vv < bv) { bv = vv; ta = dd; thw = B[k + 2]; } } } }
    const o = (j * n + i) * 4; A[o] = d * sg; A[o + 1] = s; A[o + 2] = thw; A[o + 3] = ta; } }
  return A;
}
function build(tm) {
  TM = tm; HITS = tm.hits; MOTIF = tm.motif; const v = {}; setGrade(tm.grade);
  const pts = makeRiver(); v.pts = pts;
  { const zs = [], xs = []; for (let z = -190; z <= 80; z += 2) { let sx = 0, n = 0; for (let i = 0; i < pts.length; i += 2) { const p = pts[i]; if (Math.abs(p[1] - z) < 24) { sx += p[0]; n++; } } zs.push(z); xs.push(n ? sx / n : 0); }
    for (let k = 0; k < 3; k++) for (let i = 1; i < xs.length - 1; i++) xs[i] = (xs[i - 1] + 2 * xs[i] + xs[i + 1]) / 4;
    XS = z => { const u = Math.max(0, Math.min(xs.length - 1.001, (z + 190) / 2)), i = Math.floor(u); return xs[i] + (xs[i + 1] - xs[i]) * (u - i); };
    makeNK();
    v.mx = [XS(-120), XS(-80), XS(-40), XS(0)]; v.gx = Math.round((Math.min(...xs.slice(15, 125)) + Math.max(...xs.slice(15, 125))) / 2); }
  const at = s => pts[Math.max(0, Math.min(pts.length - 1, Math.round((s + 620) / 0.25)))];
  // two oxbow lakes: crescents beside old bends
  const lakes = []; let nl = 0;
  for (let sc = -600; sc < 250 && nl < 6; sc += 9) for (const side of [1, -1]) { if (Math.abs(sc) < 45) continue; const p = at(sc), n = [Math.cos(p[3]) * side, -Math.sin(p[3]) * side], c = [p[0] + n[0] * 12, p[1] + n[1] * 12]; const a0 = Math.atan2(n[1], n[0]); const arc = [];
    for (let k = 0; k <= 44; k++) { const a = a0 - 1.8 + 3.6 * k / 44; arc.push([c[0] + 5 * Math.cos(a), c[1] + 5 * Math.sin(a)]); }
    let ok = true; for (const q of arc) { for (let i = 0; i < pts.length; i += 6) if (Math.hypot(pts[i][0] - q[0], pts[i][1] - q[1]) < 3.4) { ok = false; break; } for (const l of lakes) if (Math.hypot(l[0] - q[0], l[1] - q[1]) < 6) { ok = false; break; } if (!ok) break; }
    if (ok) { lakes.push(...arc); nl++; sc += 60; break; } }
  // the streams that feed it: a branching system, each joining at a sharp angle and thinning toward its source, each with its own smaller streams
  const tr = [];
  const grow = (x, z, th0, len, hw0, lvl, sd) => { const st = 0.3, n = Math.floor(len / st); let th = th0, kid = 0;
    for (let k = 0; k < n; k++) { const u = k * st, f = u / len;
      th = th0 + 0.50 * Math.sin(2 * Math.PI * u / (30 - 7 * lvl) + sd) + 0.26 * Math.sin(2 * Math.PI * u / 11.7 + 2.3 * sd);
      x += Math.sin(th) * st; z += Math.cos(th) * st; const hw = Math.max(hw0 * (1 - 0.45 * f), 0.36);
      if (k > 3 && Math.hypot(x, z) > 20) tr.push([x, z, hw]);
      if (lvl < 2 && u > (lvl ? 5 : 9) + kid * (lvl ? 11 : 15) + 6 * rnd(sd + kid, 21)) { const side = (kid % 2 ? 1 : -1) * (rnd(sd, 22) < 0.5 ? 1 : -1); kid++;
        grow(x, z, th + side * (0.75 + 0.40 * rnd(sd + kid, 23)), (len - u) * (0.5 + 0.3 * rnd(sd + kid, 24)), Math.max(hw * 0.62, 0.36), lvl + 1, sd * 1.37 + kid * 7.1); } } };
  for (let s0 = -590, i = 0; s0 < 1080; s0 += 38 + 34 * rnd(i, 31), i++) { if (Math.abs(s0) < 62) continue; const p = at(s0), side = (i % 2 ? 1 : -1) * (rnd(i, 32) < 0.8 ? 1 : -1);
    grow(p[0], p[1], p[3] + side * (0.75 + 0.40 * rnd(i, 33)), 55 + 70 * rnd(i, 34), 0.95, 0, i * 3.7 + 1); }
  for (const q of lakes) tr.push([q[0], q[1], 0.7]);
  v.nTrib = tr.length;
  v.nLakePts = lakes.length;
  v.G = { x0: v.gx - 260, z0: -170, size: 520, n: 1024 }; v.Gdata = field(pts, tr, v.G.x0, v.G.z0, v.G.size, v.G.n, 4);
  v.L = { x0: -14, z0: -14, size: 28, n: 512 }; v.Ldata = field(pts, [], v.L.x0, v.L.z0, v.L.size, v.L.n, 1);
  // ---- the vine's place round the trunk: where the camera is when it looks at each height, so we ride it all the way up; it wanders a little on its own
  { const raw = []; VTH = new Float32Array(32);
    for (let i = 0; i < 32; i++) { const h = 0.6 * i; let lo = 97.9, hi = 104.0; if (lookH(lo) >= h) { raw.push(NK.phi(lo)); continue; } if (lookH(hi) <= h) { raw.push(NK.phi(hi)); continue; }
      for (let k = 0; k < 40; k++) { const m = (lo + hi) / 2; if (lookH(m) < h) lo = m; else hi = m; } raw.push(NK.phi(lo)); }
    for (let k = 0; k < 2; k++) for (let i = 1; i < 31; i++) raw[i] = (raw[i - 1] + 2 * raw[i] + raw[i + 1]) / 4;
    for (let i = 0; i < 32; i++) { const h = 0.6 * i; VTH[i] = (raw[i] + (12 * Math.sin(0.8 * h + 1.0) + 5 * Math.sin(2.1 * h)) * sstep(0.3, 2.0, h)) * D2R; } v.VTH = VTH; }
  // ---- the flight, tabulated: how far we have come along the way we look (S) and across it (CP). The old flight is tabulated too, and the new tables are set to agree with it from 105.3 s on: the lift, the gust and the seam out see the very leaves they saw before
  const mkTab = (cam, wv, ex) => { const S = new Float64Array(tabN), X = new Float64Array(tabN), Y = new Float64Array(tabN), IX = new Float64Array(tabN), IY = new Float64Array(tabN); let ps = 0, pcx = 0, pcy = 0, pe = [0, 0]; const h = 1 / 480;
    for (let i = 0; i < tabN; i++) { const t = tabT(i), c = cam(t), b = basis(c), a = cam(t - h).p, d = cam(t + h).p, vel = [(d[0] - a[0]) / (2 * h), (d[1] - a[1]) / (2 * h), (d[2] - a[2]) / (2 * h)];
      const sd = dot3(vel, b.fw), cx = dot3(vel, b.rt) - wv(t), cy = dot3(vel, b.up);
      const E = ex ? ex(t, c) : [0, 0], e = [E[0] * sd, E[1] * sd];
      if (i > 0) { S[i] = S[i - 1] + 0.5 * (sd + ps) / HZ; X[i] = X[i - 1] + 0.5 * (cx + pcx) / HZ; Y[i] = Y[i - 1] + 0.5 * (cy + pcy) / HZ; IX[i] = IX[i - 1] + 0.5 * (e[0] + pe[0]) / HZ; IY[i] = IY[i - 1] + 0.5 * (e[1] + pe[1]) / HZ; } ps = sd; pcx = cx; pcy = cy; pe = e; } return { S, X, Y, IX, IY }; };
  // The slabs of leaves take a turn of the camera as a shift that grows with depth. That is only right for small turns: with a large turn behind us, flying forward would sweep every leaf sideways.
  // IX, IY take that sweep out again for the turn and the tilt the new flight adds to the old one (and for nothing else: the old flight keeps its own look).
  const TO = mkTab(camOld, KEY.wv), TN = mkTab(camAt, t => KEY.wv(t) * sstep(102.6, 104.2, t), (t, c) => { const o = camOld(t); return [c.yaw - TWO_PI - o.yaw, c.pit - o.pit]; });
  { const z = tabGet(TO.S, 95.6); for (let i = 0; i < tabN; i++) TO.S[i] -= z;
    const dS = tabGet(TN.S, TJ) - tabGet(TO.S, TJ), dX = tabGet(TN.X, TJ) - tabGet(TO.X, TJ), dY = tabGet(TN.Y, TJ) - tabGet(TO.Y, TJ); const dIX = tabGet(TN.IX, TJ), dIY = tabGet(TN.IY, TJ); for (let i = 0; i < tabN; i++) { TN.S[i] -= dS; TN.X[i] -= dX; TN.Y[i] -= dY; TN.IX[i] -= dIX; TN.IY[i] -= dIY; } }
  // The forward travel agrees with the old flight at the end, and at the start up to a whole number of slabs (xfN: the same slabs stand at the same depths, counted from another one); the part of a slab left over is spread over the climb
  { const dE = tabGet(TN.S, T_A0) - tabGet(TO.S, T_A0), EX = new Float64Array(tabN), EY = new Float64Array(tabN); v.xfN = Math.round(dE / 1.2); v.dE = dE - 1.2 * v.xfN;
    for (let i = 0; i < tabN; i++) { const t = tabT(i); TN.S[i] -= v.dE * (1 - sstep(95.6, 103.4, t)); const c = camAt(t), o = camOld(t); EX[i] = c.yaw - TWO_PI - o.yaw; EY[i] = c.pit - o.pit; }
    TN.IX[0] = 0; TN.IY[0] = 0; for (let i = 1; i < tabN; i++) { const ds = TN.S[i] - TN.S[i - 1]; TN.IX[i] = TN.IX[i - 1] + 0.5 * (EX[i] + EX[i - 1]) * ds; TN.IY[i] = TN.IY[i - 1] + 0.5 * (EY[i] + EY[i - 1]) * ds; }
    const dIX = tabGet(TN.IX, TJ), dIY = tabGet(TN.IY, TJ); for (let i = 0; i < tabN; i++) { TN.IX[i] -= dIX; TN.IY[i] -= dIY; } }
  v.S = TN.S; v.CPx = TN.X; v.CPy = TN.Y; v.IX = TN.IX; v.IY = TN.IY; v.CO = new Float64Array(tabN); v.FD = new Float64Array(tabN);
  for (let i = 1; i < tabN; i++) { const t = tabT(i); v.CO[i] = v.CO[i - 1] + 3.0 * KEY.wv(t) * sstep(104.8, 106.6, t) / HZ;
    v.FD[i] = v.FD[i - 1] + (0.55 * sstep(98.0, 99.5, t) + 0.45 * sstep(102.3, 104.0, t)) * (v.CPy[i] - v.CPy[i - 1]); }        // the fireflies rise with us more and more: they drift, they never rain
  { const k = (tabGet(TO.Y, TJ) - tabGet(TO.Y, 102.3)) - tabGet(v.FD, TJ); for (let i = 0; i < tabN; i++) v.FD[i] += k; }
  const rotAt = t => { const c = camAt(t); return [FOC * (c.yaw - TWO_PI), FOC * c.pit]; }; v.rotAt = rotAt;
  { const te = 94.0, cx = t => tabGet(TO.X, t) - (tabGet(v.CPx, t) + tabGet(v.IX, t)) - TWO_PI * tabGet(v.S, t), cy = t => tabGet(TO.Y, t) - (tabGet(v.CPy, t) + tabGet(v.IY, t));   // set A against set B: a fixed step for each slab
    v.xfC = [cx(te), cy(te)]; v.xfF = tabGet(v.FD, te); v.xfDev = 0; for (const t of [88, 90, 92, 93.5, 94.8]) v.xfDev = Math.max(v.xfDev, Math.abs(cx(t) - v.xfC[0]), Math.abs(cy(t) - v.xfC[1]), Math.abs(tabGet(v.S, t) - tabGet(TO.S, t) - 1.2 * v.xfN), Math.abs(tabGet(v.FD, t) - v.xfF)); }
  // ---- the leaf of the vine we pass close: beside the vine, a little right of the middle, 1.55 away at 100.45 s
  { const tc = 100.45, z = 1.55, r = rotAt(tc); v.hero = [tabGet(v.CPx, tc) + tabGet(v.IX, tc) + (0.25 + r[0]) * z / FOC, tabGet(v.CPy, tc) + tabGet(v.IY, tc) + (0.03 + r[1]) * z / FOC, tabGet(v.S, tc) + z, 0.30]; }
  // ---- her prints (plain tread) on the wet bank on our right: nine in a row, heading away from us to the foot of the tree. The bank leans toward the water (30 degrees), so a print keeps its length from where we fly
  const th0 = VTH[0];
  { const BK = Object.assign({ s0: [1.25, -0.9], y0: 0.20, tilt: 30, Lp: 0.47, stride: 0.60, side: 0.075 }, tm.bank || {}); v.BK = BK;
    const e = [TX + 2.45 * Math.sin(th0 + 0.12), TZ - 2.45 * Math.cos(th0 + 0.12)];
    const nrm = a => { const l = Math.hypot(...a); return a.map(x => x / l); }, d = nrm([e[0] - BK.s0[0], YG - BK.y0, e[1] - BK.s0[1]]), h = nrm([d[2], 0, -d[0]]), yv = nrm([-d[1] * d[0], 1 - d[1] * d[1], -d[1] * d[2]]), be = BK.tilt * Math.PI / 180;
    v.uBkD = d; v.uBkN = nrm(h.map((x, i) => -Math.sin(be) * x + Math.cos(be) * yv[i])); v.uBkU = nrm(h.map((x, i) => -Math.cos(be) * x - Math.sin(be) * yv[i])); v.uBkS = [BK.s0[0], BK.y0, BK.s0[1]];
    v.uBkP = new Float32Array(36); for (let i = 0; i < 9; i++) { const foot = i % 2 ? -1 : 1; v.uBkP.set([BK.stride * i, BK.side * foot, foot, 1], 4 * i); } }
  // ---- her: a small red point at the root, looking up. On "You're following" she goes up the vine after her light, passes us, and the gust takes her where it took her before
  v.redRoot = [TX + 2.0 * Math.sin(th0 + 0.21), YG + 0.07, TZ - 2.0 * Math.cos(th0 + 0.21)];
  v.redH = spline([[101.5, 0.3], [102.2, 4.6], [102.9, 11.4], [103.5, 13.6], [104.0, 14.2]]); v.tLift = 102.739;
  // ---- the answers. The first ("Don't know") stands in the world, in the air above her prints in front of the tree: 4.3 ahead of where we are at 97.0 s, facing us; we fly toward it
  { const HD = tm.hand; v.hand = HD; const ph = HD.phr[0], c0 = camAt(97.0), fh = [Math.sin(c0.yaw), 0, Math.cos(c0.yaw)], rh = [fh[2], 0, -fh[0]], Wc = 1.80 / (ph.ink[1] - ph.ink[0]), Hc = Wc / 4;
    v.h1 = { C: [c0.p[0] + fh[0] * 4.3 + rh[0] * 0.12, 1.24, c0.p[2] + fh[2] * 4.3 + rh[2] * 0.12], R: rh.map(x => x * Wc), U: [0, Hc, 0], pit0: camAt(97.25).pit,
      ff: ph.pts.map((p, i) => ({ tx: p[0], ty: p[1], T: p[2], sx: p[0] + (rnd(i, 51) - 0.5) * 1.3, sy: Math.max(-0.5, p[1] + (rnd(i, 52) - 0.5) * 5), fl: 0.5 + 0.4 * rnd(i, 53), ph: 6.283 * rnd(i, 54), om: 0.8 + 1.4 * rnd(i, 55), px: (rnd(i, 56) - 0.5) * 0.15, py: (rnd(i, 57) - 0.5) * 0.7, dx: (p[0] - 0.5) * 0.5 + (rnd(i, 58) - 0.5) * 0.3, dy: 0.7 + 1.1 * rnd(i, 59), dl: 0.12 * rnd(i, 60) })) }; }
  // ---- the vine's young tendrils: the last one reaches out over the canopy into the stars; three small ones on the way up. Each is a stalk and a coil, and her light runs out along it like a pen line
  { const tHead = h => { let lo = 97.3, hi = 104.0; for (let k = 0; k < 40; k++) { const m = (lo + hi) / 2; if (headH(m) < h) lo = m; else hi = m; } return lo; };
    const T = [{ h: VTOP - 0.2, e1: [-0.5, 0.866], R: 2.6, e2: [0.94, 0.34], C: 0.15, w: 0.016, t0: 103.2, dur: 1.15 }, { h: VTOP - 0.9, e1: [-0.82, 0.57], R: 1.45, e2: [0.94, 0.34], C: 0.10, w: 0.012, t0: 103.15, dur: 0.9 }, { h: VTOP - 1.6, e1: [0.26, 0.966], R: 0.90, e2: [-0.94, -0.34], C: 0.07, w: 0.010, t0: 103.05, dur: 0.8 }];
    for (const [h, side, R, C] of [[3.5, 1, 0.42, 0.13], [6.3, -1, 0.50, 0.15], [9.5, 1, 0.45, 0.14]]) { const th = vthJS(h), e = [side * Math.cos(th), side * Math.sin(th)]; T.push({ h, e1: e, R, C, e2: e, w: 0.0075, t0: tHead(h) - 0.1, dur: 0.9, off: 0.05 }); }
    v.td = T; v.uTdP = new Float32Array(18); v.uTdC = new Float32Array(18); v.uTdE = new Float32Array(24);
    T.forEach((q, i) => { const p = vineP(q.h, q.off || 0); v.uTdP.set(p, 3 * i); v.uTdC.set([p[0] + q.e1[0] * 0.55 * q.R + q.e2[0] * 0.3 * q.C, p[1] + 0.6 * q.R, p[2] + q.e1[1] * 0.55 * q.R + q.e2[1] * 0.3 * q.C], 3 * i); v.uTdE.set([q.e1[0], q.e1[1], q.e2[0], q.e2[1]], 4 * i); }); }
  // ---- rings of light on the water: a drop for every strong drum hit of the breakdown, and every one of her steps
  v.rings = []; v.drops = [];
  HITS.forEach((q, i) => { if (q[0] < 94.9 || q[0] > 97.0 || q[1] < 0.45) return; const c = camAt(q[0]).p; const e = { t: q[0], x: c[0] - 0.9 - 3.6 * rnd(i, 7), z: c[2] + 2.3 + 4.2 * rnd(i, 8), a: 0.40 + 0.40 * Math.min(1, q[1]) }; v.rings.push(e); v.drops.push(e); });   // on the water to our left only: the bank is on our right
  v.rings.sort((a, b) => a.t - b.t);
  // ---- the wind over the canopy ("a wind") and the river brightening ahead ("a road")
  const aim = (t, D) => { const c = camAt(t), b = basis(c), k = Math.min((c.p[1] - HC) / Math.max(-b.fw[1], 1e-3), D); return [c.p[0] + b.fw[0] * k, c.p[2] + b.fw[2] * k]; };
  { const g = aim(CUE.wind + 1.3, 85); v.waveU = g[0] * 0.5524 + g[1] * 0.8336; }
  { const g = aim(CUE.road, 60); let best = 1e9, bs = 0; for (const p of pts) { const d = Math.hypot(p[0] - g[0], p[1] - g[1]); if (d < best) { best = d; bs = p[2]; } } v.roadS0 = bs - 30; }
  V = v; return { mx: v.mx.map(x => +x.toFixed(1)), gx: v.gx, hero: v.hero.map(x => +x.toFixed(2)), vth: Array.from(VTH).filter((x, i) => i % 4 === 0).map(x => Math.round(x / D2R)), td: v.td.map(q => +q.t0.toFixed(2)), xfDev: v.xfDev, dE: +v.dE.toFixed(3), xfN: v.xfN, rings: v.rings.length, lakePts: v.nLakePts, trib: v.nTrib, roadS0: +v.roadS0.toFixed(1), S: [tabGet(v.S, 88), tabGet(v.S, 94.5), tabGet(v.S, 99.6), tabGet(v.S, 104), tabGet(v.S, 110.7)].map(x => +x.toFixed(1)) };
}
// all uniforms for song time t
// sky2: her past place (the same path as in params), for the way the thread streams back
function redPosAt(t) {
  const v = V, c = camAt(t), b = basis(c), w = sstep(v.tLift, v.tLift + 1.9, t); let pos = v.redRoot.slice();
  if (t > 101.5) { const q = vineP(v.redH(t), 0.30), k = sstep(101.5, 101.9, t); pos = pos.map((x, i) => x + (q[i] - x) * k); }
  if (w > 0) { const bob = [0.22 * Math.sin(t * 1.1), 0.16 * Math.sin(t * 1.7 + 1)], q = [0, 1, 2].map(i => c.p[i] + b.fw[i] * 6.5 + b.rt[i] * (0.65 + bob[0]) + b.up[i] * (0.40 + bob[1])); pos = pos.map((x, i) => x + (q[i] - x) * w); }
  return pos;
}
// sky2: the red thread of fate on the wind. A polyline in 1080p pixels from the middle of the picture (x, y up, half-width, strength):
// from its tail, streaming back the way she came, to her, then (in the gust) on ahead toward the way out. Thin, no core, no glow; a slow wave runs along it
function ribbon(t, c, P) {
  const R = new Float32Array(128); if (P.uRedK * (1 - P.uRedFig) <= 0) return R;
  const rt = P.uRt, up = P.uUp, fw = P.uFw, cp = c.p, Z = P.uZoom || 1;
  const proj = q => { const v = [q[0] - cp[0], q[1] - cp[1], q[2] - cp[2]], z = dot3(v, fw); return z > 0.05 ? [FOC * dot3(v, rt) / z / Z * 1920, FOC * dot3(v, up) / z / Z * 1920] : null; };
  const H = proj(redPosAt(t)); if (!H) return R;
  let d = null; const Hp = proj(redPosAt(t - 0.12)); if (Hp) d = [H[0] - Hp[0], H[1] - Hp[1]];
  if (!d || Math.hypot(d[0], d[1]) < 3) d = Math.hypot(H[0], H[1]) > 3 ? H.slice() : [0, 1];
  let dl = Math.hypot(d[0], d[1]); d = [d[0] / dl, d[1] / dl];
  const o = Math.hypot(H[0], H[1]) > 3 ? [H[0] / Math.hypot(H[0], H[1]), H[1] / Math.hypot(H[0], H[1])] : d;     // steadied a little toward 'away from where we fly'
  d = [0.75 * d[0] + 0.25 * o[0], 0.75 * d[1] + 0.25 * o[1]]; dl = Math.hypot(d[0], d[1]) || 1; d = [d[0] / dl, d[1] / dl];
  { const w = sstep(V.tLift, V.tLift + 1.9, t), cx = tt => tabGet(V.CPx, tt) + tabGet(V.IX, tt), cy = tt => tabGet(V.CPy, tt) + tabGet(V.IY, tt);
    const fx = cx(t) - cx(t - 0.1), fy = cy(t) - cy(t - 0.1), fl = Math.hypot(fx, fy);
    if (w > 0 && fl > 1e-6) { d = [d[0] * (1 - 0.8 * w) + 0.8 * w * fx / fl, d[1] * (1 - 0.8 * w) + 0.8 * w * fy / fl]; dl = Math.hypot(d[0], d[1]) || 1; d = [d[0] / dl, d[1] / dl]; } }
  const n = [-d[1], d[0]], L = 150 + 50 * sstep(102.6, 104.6, t) + 150 * sstep(108.0, 110.0, t), NB = 22, NF = 10;
  const pts = [];
  for (let i = NB - 1; i >= 0; i--) { const s = L * i / (NB - 1), u = s / L;
    const wv = 7 * Math.pow(u, 0.9) * Math.sin(TWO_PI * s / 150 - TWO_PI * 1.1 * t) + 18 * u * u * Math.sin(0.8 * t + 0.6);
    pts.push([H[0] - d[0] * s + n[0] * wv, H[1] - d[1] * s + n[1] * wv, 1.6 - 0.8 * u, sstep(0, 0.07, u) * (1 - sstep(0.62, 1.0, u))]); }
  const lead = sstep(107.9, 110.2, t), E = [0, 0], fl = [E[0] - H[0], E[1] - H[1]], fL = Math.hypot(fl[0], fl[1]) || 1, nf = [-fl[1] / fL, fl[0] / fL];
  const C = [H[0] + d[0] * 0.45 * fL, H[1] + d[1] * 0.45 * fL];
  for (let i = 1; i <= NF; i++) { const u = i / NF * lead, a = (1 - u) * (1 - u), m = 2 * u * (1 - u), e = u * u, wv = 6 * Math.sin(Math.PI * i / NF) * Math.sin(TWO_PI * u * fL / 120 - TWO_PI * 1.1 * t);
    pts.push([a * H[0] + m * C[0] + e * E[0] + nf[0] * wv * lead, a * H[1] + m * C[1] + e * E[1] + nf[1] * wv * lead, 1.6 - 0.7 * i / NF, lead > 0 ? 1 - sstep(0.55, 1.0, i / NF) : 0]); }
  pts.forEach((p, i) => R.set(p, 4 * i)); return R;
}
function params(t) {
  const v = V, P = {}, c = camAt(t), b = basis(c), f = (t - T0) * FPS, pd = c.pit * 180 / Math.PI;
  const cr = Math.cos(c.roll), sr = Math.sin(c.roll);
  P.uCam = c.p; P.uFw = b.fw; P.uRt = b.rt.map((x, i) => x * cr + b.up[i] * sr); P.uUp = b.up.map((x, i) => x * cr - b.rt[i] * sr); P.uRoll = c.roll;
  { const s = [b.fw[0] + 0.55 * b.rt[0] + 0.25 * b.up[0], b.fw[1] + 0.55 * b.rt[1] + 0.25 * b.up[1], b.fw[2] + 0.55 * b.rt[2] + 0.25 * b.up[2]], l = Math.hypot(...s); P.uSun = s.map(x => x / l); }
  P.uZoom = f < 18 ? Math.exp(-0.36 * Math.pow(1 - Math.max(f, -2) / 18, 2)) : 1;
  P.uT = t; P.uS = tabGet(v.S, t); P.uCPt = [tabGet(v.CPx, t), tabGet(v.CPy, t)]; P.uCP = [P.uCPt[0] + tabGet(v.IX, t), P.uCPt[1] + tabGet(v.IY, t)]; P.uRot = [FOC * (c.yaw - TWO_PI), FOC * c.pit]; P.uCPA = [P.uCP[0] + v.xfC[0] + TWO_PI * P.uS, P.uCP[1] + v.xfC[1]]; P.uRotA = [FOC * c.yaw, FOC * c.pit]; P.uXf = sstep(98.2, 99.0, t); P.uXfF = v.xfF; P.uXfN = v.xfN;
  { const wB = sstep(94.8, 95.6, t) * (1 - sstep(T_A0, T_A1, t)), pp = sway(t); P.uAxis = [P.uCPA[0] - pp[0] * wB, P.uCPA[1] - pp[1] * wB];
    const h = 1 / 120, sd = (tabGet(v.S, t + h) - tabGet(v.S, t - h)) / (2 * h), cd = Math.hypot(tabGet(v.CPx, t + h) - tabGet(v.CPx, t - h), tabGet(v.CPy, t + h) - tabGet(v.CPy, t - h)) / (2 * h);
    P.uNear = Math.min(7.5, Math.max(0.75, 0.30 * Math.abs(sd), 0.24 * cd)); P.uCross = Math.min(cd, 9); }
  const climb = sstep(97.6, 98.8, t);
  P.uCorr = 0.95 * sstep(94.7, 95.4, t) * (1 - 0.62 * climb) * (1 - sstep(102.9, 104.0, t)); P.uCorrB = 1 - sstep(95.2, 96.2, t); P.uCone = (0.26 * sstep(95.3, 96.3, t) * (1 - climb) + 0.15 * climb) * (1 - sstep(102.5, 103.4, t));
  P.uDense = (0.58 + 0.30 * Math.exp(-Math.pow((c.p[1] - (HC - 3)) / 5, 2))) * (1 - 0.22 * sstep(95.2, 96.0, t) * (1 - sstep(97.6, 98.6, t)));
  P.uWaterK = sstep(-22, -6, pd) * sstep(6, 2.6, c.p[1]); P.uTrunkK = sstep(94.4, 95.0, t) * (1 - sstep(97.3, 98.3, t));   // the flat far trunks stand in the water while we fly level; round the tree they would slide across the vine
  P.uAbove = sstep(HC - 8, HC + 5, c.p[1]); P.uLianaK = Math.max(sstep(-46, -24, pd), climb * (1 - sstep(103.4, 104.4, t))); P.uVeinK = 0.75; P.uFocus = 6 - (2.4 * sstep(94.8, 95.6, t) + 1.2 * sstep(96.6, 97.8, t)) * (1 - sstep(103.2, 104.4, t));
  { const o = 0.6 * sstep(104.0, 106.0, t) * (1 - sstep(107.6, 110.0, t)); P.uLoose = o + (0.8 - o) * sstep(107.95, 109.0, t); }   /* from 107.95 s on the leaves no longer thin out: they ride the wind above the canopy all the way to the seam */ P.uFlyUp = sstep(103.6, 105.5, t); P.uStream = 1 + 2.2 * sstep(102.6, 105.5, t) + 2.6 * sstep(106.5, 110.6, t); P.uFly = 0.7 - 0.42 * sstep(103.0, 104.0, t) + 0.74 * sstep(108.4, 110.4, t);
  P.uBgAz = DXK * sstep(99.3, 101.1, t) / 17; P.uFlyDY = tabGet(v.FD, t); P.uWind = sstep(103.0, 104.5, t); P.uMist = sstep(103.0, 104.6, t) * (1 + 0.8 * sstep(106, 110, t) * (1 - 0.45 * sstep(107.9, 109.5, t))); P.uCanOff = tabGet(v.CO, t); P.uFlut = sstep(102.6, 104, t); P.uGlowAz = -0.1; P.uRivK = 1;
  // the tree, the vine and her gold in it; the roof of leaves from below; the stars
  P.uTree = [TX, TZ, YG, sstep(94.9, 95.7, t) * (1 - sstep(105.3, 105.9, t))];
  P.uVine = [headH(t), sstep(97.25, 97.6, t), sstep(96.5, 97.3, t) * (1 - 0.6 * sstep(98, 100, t)), 0];
  P.uTdR = new Float32Array(24); v.td.forEach((q, i) => P.uTdR.set([q.R, q.C, q.w, i < 6 ? 0 : 2.15 * clamp01((t - q.t0) / q.dur)], 4 * i));   // the light that wrote itself along the last three now writes the third answer in the sky instead
  P.uSprig = 0.5 * climb * (1 - sstep(104.2, 105.2, t)); P.uCeil = sstep(95.0, 96.0, t) * (1 - sstep(104.5, 105.3, t)); P.uStarK = sstep(96, 98, t) * (1 - sstep(104.9, 105.3, t)); /* the stars are for the way out through the canopy; the kept ending (from 105.3 s) has the sky it had */ P.uMoonK = sstep(102.8, 103.6, t) * (1 - sstep(104.6, 105.2, t));
  { const o = KEY.sky(t); P.uSky = o + (KEY.sky2(t) - o) * sstep(107.9, 108.4, t); } P.uDream = KEY.dream(t);
  { const p = clamp01((t - CUE.wind) / 3.2); P.uWave = [v.waveU - 60 + 300 * Math.pow(p, 1.3), t >= CUE.wind ? Math.pow(Math.sin(Math.PI * p), 0.7) : 0, 0]; }
  { const p = clamp01((t - CUE.road) / 3.6); P.uRoadS = v.roadS0 + (700 - v.roadS0) * Math.pow(p, 1.6); P.uRoadK = sstep(CUE.road, CUE.road + 0.3, t) * (1 - 0.6 * sstep(94.0, 95.6, t)); }
  // every drum hit lifts the fireflies; they settle
  { let e = 0; const hi = lastIdx(HITS, t); for (let j = hi; j >= 0 && t - HITS[j][0] < 2.5; j--) { const a = t - HITS[j][0]; e += HITS[j][1] * sstep(0, 0.20, a) * Math.exp(-Math.max(a - 0.20, 0) / 0.45); }
    P.uLift = Math.min(e, 1.6) * (0.35 + 0.65 * sstep(94.3, 94.8, t) * (1 - sstep(101.3, 102.2, t))); }
  const rings = new Float32Array(32).fill(-1); let n = 0;
  for (let j = v.rings.length - 1; j >= 0 && n < 8; j--) { const q = v.rings[j], age = t - q.t; if (age >= 0 && age < 3.0) { rings[4 * n] = q.x; rings[4 * n + 1] = q.z; rings[4 * n + 2] = age; rings[4 * n + 3] = q.a; n++; } }
  P.uRings = rings;
  const drops = new Float32Array(16).fill(0); n = 0;
  for (const q of v.drops) { const u = q.t - t; if (u > 0 && u < 0.32 && n < 4) { drops[4 * n] = q.x; drops[4 * n + 1] = 0.5 * 30 * u * u; drops[4 * n + 2] = q.z; drops[4 * n + 3] = sstep(0.32, 0.20, u); n++; } }
  P.uDrops = drops;
  // the leaf of the vine we pass close: her light runs up its midrib and out along its veins as her gold in the vine reaches it
  { const u = clamp01((t - 99.75) / 1.2); P.uHero = v.hero; P.uHeroA = [sstep(99.1, 99.7, t) * (1 - sstep(101.5, 102.1, t)), 1.75 * (0.3 * u + 0.7 * u * u * (3 - 2 * u)), 0.55, 0]; }
  // her: a red point with a cream fleck. At the root until "You're following"; then up the vine after her light; then the gust carries her ahead of us, as before
  { const w = sstep(v.tLift, v.tLift + 1.9, t); let pos = v.redRoot.slice(); P.uRedFront = 0; P.uRedStep = 0;
    if (t > 101.5) { const q = vineP(v.redH(t), 0.30), k = sstep(101.5, 101.9, t); pos = pos.map((x, i) => x + (q[i] - x) * k); }
    if (w > 0) { const bob = [0.22 * Math.sin(t * 1.1), 0.16 * Math.sin(t * 1.7 + 1)], q = [0, 1, 2].map(i => c.p[i] + b.fw[i] * 6.5 + b.rt[i] * (0.65 + bob[0]) + b.up[i] * (0.40 + bob[1]));
      pos = pos.map((x, i) => x + (q[i] - x) * w); P.uRedFront = t > v.tLift + 0.3 ? 1 : 0; }
    const rr = 0.06 - 0.038 * sstep(101.5, 101.9, t); P.uRed = [pos[0], pos[1], pos[2], rr + (0.040 - rr) * w]; P.uRedFig = 1 - sstep(101.45, 101.75, t);   /* a tiny figure on the bank and at the root; a smaller, softer point on the climb and in the gust */ P.uRedK = sstep(95.6, 96.4, t);
    P.uRib = ribbon(t, c, P); }   // she stays a small point when she passes close to the lens
  // the seams: the soft gold field in, the gust of gold out
  P.uGlowK = 0.30 * Math.exp(-Math.max(t - T0, 0) / 0.15); P.uVeilIn = Math.exp(-Math.max(f, 0) / 6.0) * (1 - sstep(22, 44, f));
  P.uVeil = 0.72 * Math.pow(sstep(109.6, 110.5, t), 1.4);   // was 0.55: the gust of gold is nearer the field's own light before the field arrives, so the hand-over neither swells nor drops
  P.uField = [f < 30 ? Math.max(f, 0) / 30 : 9, f > 678 ? -0.35 + 2.05 * Math.pow((f - 678) / 11, 1.15) : -9];
  P.uExp = (1 + 2.6 * Math.exp(-Math.max(f, 0) / 7.0)) * GRADE(t);
  P.uBk = [sstep(95.0, 95.6, t) * (1 - sstep(98.7, 99.5, t)), v.BK.Lp, v.BK.stride * 8, 0];
  // ---- the three answers, written in her gold: the only words in this section. Each is one pen line on a plane (C the middle of its cell, R its width, U its height)
  { const HD = v.hand, hC = new Float32Array(9), hR = new Float32Array(9), hU = new Float32Array(9), hA = new Float32Array(12), hB = new Float32Array(12), ff = new Float32Array(192), rt = P.uRt, up = P.uUp, fw = b.fw;
    const plane = (i, bs, cam, cx, cy, rot, cellW, d) => { const cr = Math.cos(rot), sr = Math.sin(rot), k = d / FOC, cellH = cellW / 4;   // a plane that rides with the camera: its middle at (cx, cy) of the picture, cellW of the picture's width wide
      for (let j = 0; j < 3; j++) { hC[3 * i + j] = cam[j] + (bs.fw[j] * FOC + bs.rt[j] * cx + bs.up[j] * cy) * k; hR[3 * i + j] = (bs.rt[j] * cr + bs.up[j] * sr) * cellW * k; hU[3 * i + j] = (bs.up[j] * cr - bs.rt[j] * sr) * cellH * k; } };
    // 1. "Don't know" (96.36 s): fireflies over the wet bank gather into it above her prints, in the order a pen would write it; whole from 96.90 to 97.63 s; then they lift off and scatter
    { const q = v.h1, t0 = CUE.dont, dw = 0.54, tS = 97.63, on = sstep(t0 - 0.95, t0 - 0.45, t) * (1 - sstep(tS + 0.4, tS + 0.8, t));
      const dh = Math.hypot(q.C[0] - c.p[0], q.C[2] - c.p[2]), lift = t > 97.25 ? 0.9 * dh * (Math.tan(c.pit) - Math.tan(q.pit0)) : 0;   // as we begin to look up it lifts with our look: it stays sharp and whole
      hC.set([q.C[0], q.C[1] + lift, q.C[2]], 0); hR.set(q.R, 0); hU.set(q.U, 0);
      hA.set([1.02 * clamp01((t - t0) / dw), -0.02 + 1.06 * clamp01((t - tS) / 0.32), on, 0], 0);
      hB.set([0.0142, 0.7, dot3([q.C[0] - c.p[0], q.C[1] - c.p[1], q.C[2] - c.p[2]], fw), 2], 0);
      if (on > 0) q.ff.forEach((p, i) => { const arr = t0 + p.T * dw, u = clamp01((arr - t) / p.fl), g = u * u * (3 - 2 * u), hov = 0.28 + 0.30 * Math.pow(0.5 + 0.5 * Math.sin(t * p.om * 1.4 + p.ph * 3), 2), wx = Math.sin(t * p.om + p.ph), wy = Math.cos(t * p.om * 1.25 + p.ph * 1.7);
        let x = p.tx + (p.sx - p.tx) * g + (p.px + 0.04 * wx) * Math.sin(Math.PI * g) + 0.03 * wx * g, y = p.ty + (p.sy - p.ty) * g + (p.py + 0.15 * wy) * Math.sin(Math.PI * g) + 0.12 * wy * g;
        let br = hov * g + (1 - g), sz = 0.030; if (t > arr) br = Math.max(0, 1 - (t - arr) / 0.22);          // landed: the line holds its light
        const ts = tS + 0.30 * p.T + p.dl; if (t > ts) { const a = t - ts, s = 0.45 * a + 0.9 * a * a; x = p.tx + p.dx * s; y = p.ty + p.dy * s + 0.08 * Math.sin(a * 5 + p.ph); br = 0.8 * sstep(0, 0.07, a) * (1 - sstep(0.25, 0.7, a)); sz = 0.030 * (1 - 0.5 * sstep(0, 0.6, a)); }
        ff.set([x, y, sz, br], 4 * i); }); }
    // 2. "Not yet" (98.64 s): the vine writes it. A tendril of light leaves the stem as we start the climb, swings under the word and writes it beside the vine; whole from 99.16 to 99.90 s; then it lets go of the stem and curls away
    { const ph = HD.phr[1], t0 = CUE.notyet, tL = t0 - 0.36, tW = t0 + 0.52, tG = 99.90, cellW = 0.405 / (ph.ink[1] - ph.ink[0]), cellL = -0.47 - ph.ink[0] * cellW;
      const vp = vineP(lookH(t), 0), dv = [vp[0] - c.p[0], vp[1] - c.p[1], vp[2] - c.p[2]], stemX = FOC * dot3(dv, rt) / Math.max(dot3(dv, fw), 0.2), clipX = Math.max(0.80, Math.min(0.999, (stemX - cellL) / cellW));   // where the stem is in the picture: the line comes out of it there
      let Tc = 0; for (let i = 0; i + 1 < ph.lead.length; i++) { const a = ph.lead[i], bb = ph.lead[i + 1]; if (clipX <= a[0] && clipX >= bb[0]) { Tc = a[2] + (bb[2] - a[2]) * (a[0] - clipX) / Math.max(a[0] - bb[0], 1e-6); break; } }
      const g = sstep(tG, tG + 0.6, t), ax = t < t0 ? Tc + (ph.word0 - Tc) * clamp01((t - tL) / (t0 - tL)) : ph.word0 + (1.02 - ph.word0) * clamp01((t - t0) / (tW - t0));
      plane(1, { fw, rt, up }, c.p, cellL + cellW / 2 - 0.05 * g, 0.02 - 0.012 * (t - t0) - 0.07 * g * g, 4 * D2R, cellW, 0.7);
      hA.set([ax, -0.02 + 1.06 * clamp01((t - tG) / 0.36), sstep(tL - 0.02, tL + 0.08, t) * (1 - sstep(tG + 0.3, tG + 0.6, t)), 1.5 * g], 4); hB.set([0.0135, 0, 0.7, clipX], 4); }
    // 3. "You're following" (101.47 s): it begins above us in the gaps of the roof of leaves and keeps ahead of us as we ride up; whole from 103.2 s, in the stars as we break through; from 103.98 s it lets go: it fades into the stars, in place, before we tilt down to the canopy (a streak of it on the tilt landed on a kick)
    { const ph = HD.phr[2], t0 = CUE.youre, tW = 103.2, tA = 104.76, cellW = 0.72 / (ph.ink[1] - ph.ink[0]);
      const te = t - 0.07 * Math.log(1 + Math.exp((t - tA) / 0.07)), ce = camAt(te), be = basis(ce), cr = Math.cos(ce.roll), sr = Math.sin(ce.roll);
      const bs = { fw: be.fw, rt: be.rt.map((x, i) => x * cr + be.up[i] * sr), up: be.up.map((x, i) => x * cr - be.rt[i] * sr) }, u = clamp01((t - t0) / (tW - t0));
      plane(2, bs, c.p, (0.5 - 0.445) * cellW - 0.006, 0.078, 3.5 * D2R, cellW, 60);   /* the space between its two words is where the vine's top stands */
      hA.set([1.02 * (0.7 * u + 0.3 * u * u * (3 - 2 * u)), -0.02, sstep(t0 - 0.05, t0 + 0.08, t) * (1 - sstep(104.40, 104.733, t)), 0], 8); hB.set([0.0115, 0, 900, 2], 8); }
    P.uHC = hC; P.uHR = hR; P.uHU = hU; P.uHA = hA; P.uHB = hB; P.uFf = ff; P.uSkyOpen = sstep(102.6, 103.15, t); }
  return P;
}

let texG, texL, texH, MROWS, PMID = null, RMID = null;
function handTex(hd) { const n = hd.w * hd.h, bin = s => { const b = atob(s), a = new Uint8Array(b.length); for (let i = 0; i < b.length; i++) a[i] = b.charCodeAt(i); return new Uint16Array(a.buffer); }, D = bin(hd.d), T = bin(hd.t), A = new Float32Array(n * 4);
  for (let i = 0; i < n; i++) { A[4 * i] = D[i] / 65535; A[4 * i + 1] = T[i] / 65535; }
  const tex = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, tex); gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA16F, hd.w, hd.h, 0, gl.RGBA, gl.FLOAT, A); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE); return tex; }
function fieldTex(data, n) { const tex = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, tex); gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA16F, n, n, 0, gl.RGBA, gl.FLOAT, data); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE); return tex; }
let gl, W, H, progScene, progBlit, progBlur, progFinal, quad, fbAccum, bloom = [], frameNo = 0;
const VS = `#version 300 es
in vec2 aP; void main(){ gl_Position = vec4(aP,0.,1.); }`;
const FS_BLIT = `#version 300 es
precision highp float; uniform sampler2D uTex; uniform vec2 uInv; uniform float uThr; out vec4 o;
void main(){ vec2 uv = gl_FragCoord.xy*uInv; vec3 c = vec3(0.0);
  for(int j=0;j<4;j++) for(int i=0;i<4;i++) c += texture(uTex, uv + (vec2(float(i),float(j)) - 1.5)*0.25*uInv).rgb;
  c *= 1.0/16.0;
  if(uThr > 0.0){ float l = max(c.r, max(c.g,c.b)); c *= smoothstep(uThr*0.6, uThr*2.0, l); c = min(c, vec3(30.0)); }
  o = vec4(c,1.); }`;
const FS_BLUR = `#version 300 es
precision highp float; uniform sampler2D uTex; uniform vec2 uInv; uniform vec2 uDir; out vec4 o;
void main(){ vec2 uv = gl_FragCoord.xy*uInv; vec3 c = texture(uTex, uv).rgb*0.227027;
  c += (texture(uTex, uv+uDir*uInv*1.3846).rgb + texture(uTex, uv-uDir*uInv*1.3846).rgb)*0.316216;
  c += (texture(uTex, uv+uDir*uInv*3.2308).rgb + texture(uTex, uv-uDir*uInv*3.2308).rgb)*0.070270;
  o = vec4(c,1.); }`;
const FS_FINAL = `#version 300 es
precision highp float; uniform sampler2D uTex, uB0, uB1, uB2, uB3, uB4; uniform vec2 uInv, uField; uniform float uSeed, uExp, uVeil, uVeilIn, uFr, uAsp; out vec4 o;
float h(vec2 p){ p = fract(p*vec2(123.34,456.21)); p += dot(p,p+45.32); return fract(p.x*p.y); }
float vn(vec2 p){ vec2 i = floor(p), f = fract(p); f = f*f*(3.0-2.0*f); return mix(mix(h(i), h(i+vec2(1,0)), f.x), mix(h(i+vec2(0,1)), h(i+vec2(1,1)), f.x), f.y); }
// grains of lit sand: soft points in a grid, drawn out along x by their own speed; ky > 0 wraps the grid in y (round the circle)
float gr(vec2 p, float ky, float el, float sz){ vec2 i = floor(p), f = fract(p); float a = 0.0;
  for(int dy = -1; dy <= 1; dy++) for(int dx = -1; dx <= 1; dx++){ vec2 c = i + vec2(float(dx), float(dy)), cw = vec2(c.x, ky > 0.0 ? mod(c.y, ky) : c.y);
    if(h(cw + 0.37) > 0.42) continue;
    vec2 d = vec2(float(dx), float(dy)) + vec2(h(cw*1.31 + 4.1), h(cw*1.73 + 8.3)) - f; d.x /= el;
    a += (0.35 + 0.65*h(cw + 5.9))*exp(-dot(d, d)/(sz*sz)); }
  return a; }
vec3 aces(vec3 x){ return clamp((x*(2.51*x+0.03))/(x*(2.43*x+0.59)+0.14), 0.0, 1.0); }
void main(){ vec2 uv = gl_FragCoord.xy*uInv;
  vec3 c = texture(uTex, uv).rgb;
  vec3 b = texture(uB0,uv).rgb*0.34 + texture(uB1,uv).rgb*0.26 + texture(uB2,uv).rgb*0.20 + texture(uB3,uv).rgb*0.14 + texture(uB4,uv).rgb*0.10;
  c = c + b*0.60;
  vec2 q = uv-0.5; c *= 1.0 - 0.50*dot(q,q)*1.6;
  c = aces(c*uExp);
  c = pow(c, vec3(1.0/2.2));
  // the soft gold field of the two seams: centre #FFE2A6, edges #C8862E
  float rr = length(q)*2.0;
  vec3 fc = mix(vec3(1.0,0.886,0.651), vec3(0.784,0.525,0.180), smoothstep(0.0, 1.0, rr));
  // nothing rests in the gold: on the way in, grains of light keep opening from the centre (4% a frame); on the way out they run left to right with the wind, faster each frame
  { vec2 qa = vec2(q.x*uAsp, q.y); float ra = max(length(qa), 1e-3), th = atan(qa.y, qa.x), lr = log(ra) - 0.04*uFr;
    float gIn = (gr(vec2(lr*14.0, th*60.0/6.2832), 60.0, 3.0, 0.09) + 0.8*gr(vec2(lr*21.0 + 3.3, th*96.0/6.2832 + 0.5), 96.0, 3.0, 0.085))*smoothstep(0.03, 0.16, ra)*(1.0 - smoothstep(20.0, 46.0, uFr));
    float fo = max(uFr - 655.0, 0.0), X = 0.0042*fo*fo, el = clamp(0.0084*fo*9.0, 1.0, 2.8);
    float gOut = (gr(vec2((uv.x*uAsp - X)*3.0, uv.y*46.0), 0.0, el, 0.10) + 0.8*gr(vec2((uv.x*uAsp - 1.6*X)*4.5 + 7.0, uv.y*83.0 + 3.0), 0.0, el, 0.09))*smoothstep(662.0, 676.0, uFr);
    fc += vec3(0.125, 0.130, 0.105)*(gIn + gOut); }
  { float fs = max(uFr - 608.0, 0.0), fo2 = max(uFr - 655.0, 0.0), X2 = 0.011*fs + 0.0042*fo2*fo2, el2 = clamp(0.0084*fo2*9.0, 1.5, 2.8);   // grains of lit sand stream through the picture on the wind, long before the gold closes
    float gS = gr(vec2((uv.x*uAsp - X2)*3.6 + 1.7, uv.y*38.0 + 5.0), 0.0, el2, 0.085) + 0.7*gr(vec2((uv.x*uAsp - 1.5*X2)*5.5 + 9.0, uv.y*71.0 + 2.0), 0.0, el2, 0.08);
    c += vec3(1.0, 0.72, 0.34)*0.20*gS*smoothstep(608.0, 650.0, uFr)*(1.0 - smoothstep(668.0, 686.0, uFr)); }
  float dIn = 0.45*clamp(0.5*rr + 0.4*(1.0 - min(dot(c, vec3(0.3, 0.6, 0.1))*1.6, 1.0)), 0.0, 1.0), mIn = 1.0 - smoothstep(dIn, dIn + 0.55, uField.x);   // the way in: the picture comes through the gold over 30 frames, from the first frame on, the middle and the brightest parts first. A dissolve, never an edge
  float n = vn(vec2(uv.x*1.3 - uField.y*2.5, uv.y*11.0)) + 0.5*vn(vec2(uv.x*3.0 - uField.y*5.0, uv.y*31.0));
  float mOut = smoothstep(0.0, 0.5, uField.y - uv.x + 0.26*(n - 0.75));
  c = mix(c, mix(fc, vec3(0.86,0.60,0.24), 0.5), uVeil*(0.55 + 0.6*n)*(0.5 + 0.5*max(c.r, 0.2)));
  c = mix(c, fc, uVeilIn*0.92);
  c = mix(c, fc, max(mIn, mOut));
  c += (h(gl_FragCoord.xy + uSeed*17.0) + h(gl_FragCoord.xy*1.37 + uSeed*29.0 + 11.0) - 1.0)*0.0085;      // dither: no steps in the dark gradients
  o = vec4(c,1.); }`;
function compile(type, src) { const s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s); if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s)); return s; }
function program(fs) { const p = gl.createProgram(); gl.attachShader(p, compile(gl.VERTEX_SHADER, VS)); gl.attachShader(p, compile(gl.FRAGMENT_SHADER, fs)); gl.bindAttribLocation(p, 0, 'aP'); gl.linkProgram(p); if (!gl.getProgramParameter(p, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(p)); p.u = {}; const n = gl.getProgramParameter(p, gl.ACTIVE_UNIFORMS); for (let i = 0; i < n; i++) { const inf = gl.getActiveUniform(p, i); p.u[inf.name.replace('[0]', '')] = gl.getUniformLocation(p, inf.name); } return p; }
function target(w, h) { const tex = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, tex); gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA16F, w, h, 0, gl.RGBA, gl.HALF_FLOAT, null); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE); const fb = gl.createFramebuffer(); gl.bindFramebuffer(gl.FRAMEBUFFER, fb); gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, tex, 0); return { fb, tex, w, h }; }
async function init(opts) {
  W = opts.w; H = opts.h; const info = build(opts.timing);
  const cv = document.getElementById('c'); cv.width = W; cv.height = H;
  gl = cv.getContext('webgl2', { preserveDrawingBuffer: true, antialias: false, alpha: false, powerPreference: 'high-performance' });
  if (!gl.getExtension('EXT_color_buffer_float')) throw new Error('no float targets');
  gl.getExtension('OES_texture_float_linear');
  const dbg = gl.getExtension('WEBGL_debug_renderer_info');
  const renderer = dbg ? gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL) : 'unknown';
  quad = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, quad); gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW); gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0);
  const t0 = performance.now();
  progScene = program(opts.frag); progBlit = program(FS_BLIT); progBlur = program(FS_BLUR); progFinal = program(FS_FINAL);
  fbAccum = target(W, H); texG = fieldTex(V.Gdata, V.G.n); texL = fieldTex(V.Ldata, V.L.n); texH = handTex(V.hand); MROWS = new Int32Array(opts.timing.motif.rows_top_to_bottom.slice().reverse());
  let w = 1920, h = Math.round(1920 * H / W); for (let i = 0; i < 5; i++) { w = Math.max(2, w >> 1); h = Math.max(2, h >> 1); bloom.push({ a: target(w, h), b: target(w, h) }); }
  gl.finish();
  return { renderer, compileMs: performance.now() - t0, info, uniforms: Object.keys(progScene.u).length };
}
function halton(i, b) { let f = 1, r = 0; while (i > 0) { f /= b; r += f * (i % b); i = Math.floor(i / b); } return r; }
const F1 = ['uCross', 'uStream', 'uNear', 'uFlyUp', 'uLianaK', 'uZoom', 'uT', 'uS', 'uCorr', 'uCorrB', 'uCone', 'uDense', 'uWaterK', 'uAbove', 'uTrunkK', 'uVeinK', 'uFocus', 'uLoose', 'uRoll', 'uDream', 'uRoadS', 'uRoadK', 'uSky', 'uFly', 'uLift', 'uFlut', 'uGlowK', 'uGlowAz', 'uRivK', 'uRedK', 'uRedStep', 'uRedFront', 'uBgAz', 'uFlyDY', 'uWind', 'uMist', 'uCanOff', 'uSprig', 'uStarK', 'uCeil', 'uMoonK', 'uXf', 'uXfF', 'uXfN', 'uSkyOpen', 'uRedFig'];
function drawScene(P, weight, jit, seed) {
  if (P.uRedFig > 0 && RMID) { const M = RMID, v = [0, 1, 2].map(i => M.uRed[i] - M.uCam[i]), z = dot3(v, M.uFw), sx = dot3(v, M.uRt) / z, sy = dot3(v, M.uUp) / z;
    if (z > 0.05) P = Object.assign({}, P, { uRed: [0, 1, 2].map(i => P.uCam[i] + z * (P.uFw[i] + sx * P.uRt[i] + sy * P.uUp[i])).concat([P.uRed[3]]) }); }
  gl.bindFramebuffer(gl.FRAMEBUFFER, fbAccum.fb); gl.viewport(0, 0, W, H); gl.enable(gl.BLEND); gl.blendFunc(gl.ONE, gl.ONE);
  gl.useProgram(progScene); const u = progScene.u;
  gl.uniform2f(u.uRes, W, H); gl.uniform2f(u.uJit, jit[0], jit[1]); gl.uniform1f(u.uWeight, weight); if (u.uSeed) gl.uniform1f(u.uSeed, seed);
  for (const k of F1) if (u[k]) gl.uniform1f(u[k], P[k]);
  for (const k of ['uCam', 'uFw', 'uRt', 'uUp', 'uSun', 'uWave']) if (u[k]) gl.uniform3f(u[k], P[k][0], P[k][1], P[k][2]);
  if (PMID) for (const [k, q] of [['uFwM', 'uFw'], ['uRtM', 'uRt'], ['uUpM', 'uUp']]) if (u[k]) gl.uniform3f(u[k], PMID[q][0], PMID[q][1], PMID[q][2]);
  for (const k of ['uCP', 'uRot', 'uAxis', 'uCPA', 'uRotA']) if (u[k]) gl.uniform2f(u[k], P[k][0], P[k][1]);
  for (const k of ['uRed', 'uHero', 'uHeroA', 'uBk', 'uTree', 'uVine']) if (u[k]) gl.uniform4f(u[k], P[k][0], P[k][1], P[k][2], P[k][3]);
  for (const k of ['uBkS', 'uBkD', 'uBkU', 'uBkN']) if (u[k]) gl.uniform3f(u[k], V[k][0], V[k][1], V[k][2]);
  if (u.uBkP) gl.uniform4fv(u.uBkP, V.uBkP);
  if (u.uRib) gl.uniform4fv(u.uRib, P.uRib); if (u.uRings) gl.uniform4fv(u.uRings, P.uRings); if (u.uDrops) gl.uniform4fv(u.uDrops, P.uDrops);
  if (u.uVth) gl.uniform1fv(u.uVth, VTH); if (u.uTdP) gl.uniform3fv(u.uTdP, V.uTdP); if (u.uTdC) gl.uniform3fv(u.uTdC, V.uTdC); if (u.uTdE) gl.uniform4fv(u.uTdE, V.uTdE); if (u.uTdR) gl.uniform4fv(u.uTdR, P.uTdR);
  gl.activeTexture(gl.TEXTURE6); gl.bindTexture(gl.TEXTURE_2D, texG); if (u.uRiv) gl.uniform1i(u.uRiv, 6); if (u.uRivMap) gl.uniform4f(u.uRivMap, V.G.x0, V.G.z0, 1 / V.G.size, 0);
  gl.activeTexture(gl.TEXTURE7); gl.bindTexture(gl.TEXTURE_2D, texL); if (u.uRivL) gl.uniform1i(u.uRivL, 7); if (u.uRivMapL) gl.uniform4f(u.uRivMapL, V.L.x0, V.L.z0, 1 / V.L.size, 0);
  for (const k of ['uHC', 'uHR', 'uHU']) if (u[k]) gl.uniform3fv(u[k], P[k]); for (const k of ['uHA', 'uHB', 'uFf']) if (u[k]) gl.uniform4fv(u[k], P[k]);
  gl.activeTexture(gl.TEXTURE8); gl.bindTexture(gl.TEXTURE_2D, texH); if (u.uHand) gl.uniform1i(u.uHand, 8);
  gl.activeTexture(gl.TEXTURE0);
  gl.drawArrays(gl.TRIANGLES, 0, 3); gl.disable(gl.BLEND);
}
function pass(prog, src, dst, set) { gl.bindFramebuffer(gl.FRAMEBUFFER, dst ? dst.fb : null); const w = dst ? dst.w : W, h = dst ? dst.h : H; gl.viewport(0, 0, w, h); gl.useProgram(prog); gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, src.tex); gl.uniform1i(prog.u.uTex, 0); gl.uniform2f(prog.u.uInv, 1 / w, 1 / h); if (set) set(prog.u); gl.drawArrays(gl.TRIANGLES, 0, 3); }
// render film frame f (2632..3321) into the canvas
function renderFrame(f, ns, shutter, exposure) {
  ns = ns || 8; shutter = shutter === undefined ? 0.5 : shutter; frameNo++;
  const t = f / FPS, Pm = params(t); shutter = 1.5; PMID = Pm; RMID = Pm;
  { const a = params(t - 0.5 * shutter / FPS), b = params(t + 0.5 * shutter / FPS); const dC = Math.hypot(a.uCam[0] - b.uCam[0], a.uCam[1] - b.uCam[1], a.uCam[2] - b.uCam[2]);
    const streak = (Math.hypot(a.uCPt[0] - b.uCPt[0], a.uCPt[1] - b.uCPt[1]) / 2.0 + Math.hypot(a.uRot[0] - b.uRot[0], a.uRot[1] - b.uRot[1]) + Math.abs(a.uS - b.uS) * 0.12 + (dC + Math.abs(a.uCanOff - b.uCanOff)) / Math.max(a.uCam[1] - HC + 4, 4) * a.uAbove) * W;
    ns = Math.max(ns, Math.min(5 * ns, Math.ceil(streak / 2.2))); ns += ns % 2; }
  gl.bindFramebuffer(gl.FRAMEBUFFER, fbAccum.fb); gl.viewport(0, 0, W, H); gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT);
  for (let i = 0; i < ns; i++) drawScene(params(t + shutter * ((i + 0.5) / ns - 0.5) / FPS), (1 - Math.abs(2 * (i + 0.5) / ns - 1)) * 2 / ns, [halton(i + 1, 2) - 0.5, halton(i + 1, 3) - 0.5], (f * 31 + i * 7) % 9973);
  let src = fbAccum;
  for (let i = 0; i < bloom.length; i++) {
    pass(progBlit, src, bloom[i].a, u => gl.uniform1f(u.uThr, i === 0 ? 0.55 : 0.0));
    pass(progBlur, bloom[i].a, bloom[i].b, u => gl.uniform2f(u.uDir, 1, 0));
    pass(progBlur, bloom[i].b, bloom[i].a, u => gl.uniform2f(u.uDir, 0, 1));
    src = bloom[i].a;
  }
  gl.bindFramebuffer(gl.FRAMEBUFFER, null); gl.viewport(0, 0, W, H); gl.useProgram(progFinal); const u = progFinal.u;
  gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, fbAccum.tex); gl.uniform1i(u.uTex, 0);
  for (let i = 0; i < 5; i++) { gl.activeTexture(gl.TEXTURE1 + i); gl.bindTexture(gl.TEXTURE_2D, bloom[i].a.tex); gl.uniform1i(u['uB' + i], 1 + i); }
  gl.uniform2f(u.uInv, 1 / W, 1 / H); gl.uniform1f(u.uSeed, f % 97); gl.uniform1f(u.uExp, (exposure || 1.0) * Pm.uExp); gl.uniform2f(u.uField, Pm.uField[0], Pm.uField[1]); gl.uniform1f(u.uVeil, Pm.uVeil); gl.uniform1f(u.uVeilIn, Pm.uVeilIn); gl.uniform1f(u.uFr, f - F0); gl.uniform1f(u.uAsp, W / H);
  gl.drawArrays(gl.TRIANGLES, 0, 3);
  gl.finish();
  return { ns, cam: Pm.uCam, sHead: Pm.uS, wind: Pm.uCP[0] };
}
function grab(type, q) { return document.getElementById('c').toDataURL(type || 'image/png', q); }
window.OG = { init, renderFrame, grab, params, build, camAt, camOld };
