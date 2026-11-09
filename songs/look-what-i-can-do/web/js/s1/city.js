// S1: Great Idea, Ted's city, ported (one change: the plaza round the standup roof is wider).
// the city at 9:15: blue hour, towers full of lit windows, street lights in rows, one wide roof where the standup
// floats. Everything is unlit (painted) geometry so the CPU renderer stays fast; bloom does the glow.
import * as THREE from 'three';
import { canvasTex, rng, dotTex, clay, basic } from './lib.js';

// time of day: 0 = blue hour (the look we picked), 1 = soft morning. The sky darkens as the meeting drags on.
export const DAY = { uDay: { value: 0 } };
// make a painted material follow the time of day: facades go from night (dark, lit windows) to a light slate blue
let tintN = 0;
export function dayTint(mat, facade = [0.27, 0.32, 0.43]) {
  const key = 'dayTint' + (tintN++);
  const prev = mat.onBeforeCompile;
  mat.onBeforeCompile = (sh, r) => { if (prev) prev(sh, r); sh.uniforms.uDay = DAY.uDay;
    sh.fragmentShader = 'uniform float uDay;\n' + sh.fragmentShader.replace('#include <map_fragment>', `#include <map_fragment>
      { // daylight: facades turn soft slate, windows stay readable as glass catching the morning sky
        float lum = dot(diffuseColor.rgb, vec3(0.333)); vec3 wall = vec3(${facade.join(',')});
        vec3 glass = mix(wall * 1.25, vec3(0.62, 0.72, 0.86), smoothstep(0.12, 0.45, lum));
        diffuseColor.rgb = mix(diffuseColor.rgb, mix(wall, glass, smoothstep(0.08, 0.3, lum)), uDay); }`); };
  mat.customProgramCacheKey = () => key; mat.needsUpdate = true; return mat;
}

export const ROOF_Y = 30;                     // the standup roof
export const ROOF = { w: 34, d: 26, z: -6 };  // its size and centre (x = 0)

function windowAtlas(seed, warm = 0.42) {
  const R = rng(seed);
  return canvasTex(128, 256, (g, w, h) => {
    g.fillStyle = '#12152a'; g.fillRect(0, 0, w, h);
    for (let y = 6; y < h; y += 12) for (let x = 5; x < w; x += 10) {
      const r = R(); if (r < warm) g.fillStyle = `rgb(255,${214 + R() * 22 | 0},${160 + R() * 40 | 0})`;
      else if (r < warm + 0.12) g.fillStyle = `rgb(${150 + R() * 40 | 0},${200 + R() * 30 | 0},255)`;
      else g.fillStyle = `rgb(${26 + R() * 10 | 0},${30 + R() * 10 | 0},${52 + R() * 12 | 0})`;
      g.fillRect(x, y, 6, 7);
    }
  }, { nearest: false, repeat: [1, 1] });
}

export function buildCity() {
  const city = new THREE.Group(); const R = rng(17);
  // sky: deep blue overhead, a thin dawn line at the horizon
  const sky = new THREE.Mesh(new THREE.SphereGeometry(900, 32, 16), new THREE.ShaderMaterial({
    side: THREE.BackSide, depthWrite: false, uniforms: { uDawn: { value: 0.35 }, uDay: DAY.uDay },
    vertexShader: `varying vec3 vP; void main(){ vP = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
    fragmentShader: `uniform float uDawn; uniform float uDay; varying vec3 vP; void main(){ float y = vP.y;
      vec3 top = vec3(0.016,0.020,0.075), mid = vec3(0.05,0.075,0.21), hor = mix(vec3(0.12,0.13,0.28), vec3(0.92,0.46,0.30), uDawn);
      vec3 c = mix(hor, mid, smoothstep(0.0, 0.18, y)); c = mix(c, top, smoothstep(0.18, 0.7, y));
      float sunx = smoothstep(0.9, 1.0, dot(normalize(vec3(vP.x, 0.0, vP.z)), normalize(vec3(0.4,0.0,-1.0))));
      c += vec3(1.0,0.55,0.3) * uDawn * sunx * exp(-max(y,0.0)*14.0) * 0.6;
      // soft morning: clear blue overhead, warm peach haze at the horizon (kept under the bloom threshold)
      vec3 dTop = vec3(0.16,0.32,0.66), dMid = vec3(0.36,0.55,0.80), dHor = vec3(0.84,0.70,0.60);
      vec3 d = mix(dHor, dMid, smoothstep(0.0, 0.22, y)); d = mix(d, dTop, smoothstep(0.22, 0.8, y));
      c = mix(c, d, uDay);
      gl_FragColor = vec4(c, 1.0); }` }));
  city.add(sky); city.userData.sky = sky;
  // ground + streets
  const ground = new THREE.Mesh(new THREE.PlaneGeometry(2000, 2000), dayTint(basic(0x0e1020), [0.30, 0.33, 0.40])); ground.rotation.x = -Math.PI / 2; city.add(ground);
  // towers on a block grid, leaving the avenues open
  const atlases = [windowAtlas(1, 0.22), windowAtlas(2, 0.14), windowAtlas(3, 0.3), windowAtlas(4, 0.1)];
  const mats = atlases.map((a) => new THREE.MeshBasicMaterial({ map: a, color: 0xb8b8b8 }));
  const roofMat = basic(0x0b0c10);
  const groups = mats.map(() => []);
  const block = 26, street = 9;
  for (let bx = -14; bx <= 14; bx++) for (let bz = -18; bz <= 6; bz++) {
    const cx = bx * (block + street), cz = bz * (block + street) - 40;
    if (Math.abs(cx) < 40 && Math.abs(cz - ROOF.z + 10) < 30) continue;        // the standup tower stands here (S1: a wider plaza, so the meeting can grow sideways)
    const n = 1 + (R() * 3 | 0);
    for (let i = 0; i < n; i++) {
      const w = 7 + R() * 9, d = 7 + R() * 9; let h = 10 + Math.pow(R(), 1.6) * (Math.abs(bx) < 4 && bz > -8 ? 70 : 45);
      const x = cx + (R() - 0.5) * (block - w), z = cz + (R() - 0.5) * (block - d);
      if (Math.abs(cx) < 75 && cz > 14 && cz < 175) h = Math.min(h, 7 + (h * 7.31) % 13);   // S1: a low-rise district in front of the meeting, so the camera can pull back over it
      groups[(R() * mats.length) | 0].push([x, h, z, w, d]);
    }
  }
  const box = new THREE.BoxGeometry(1, 1, 1);
  // per-instance UV repeat comes from scale: windows stay the same size on every tower
  const uvs = box.attributes.uv; const pos = box.attributes.position;
  groups.forEach((list, k) => {
    const im = new THREE.InstancedMesh(box, mats[k], list.length); const m4 = new THREE.Matrix4();
    list.forEach(([x, h, z, w, d], i) => { m4.compose(new THREE.Vector3(x, h / 2, z), new THREE.Quaternion(), new THREE.Vector3(w, h, d)); im.setMatrixAt(i, m4); });
    im.material.onBeforeCompile = (sh) => {
      sh.vertexShader = sh.vertexShader.replace('#include <uv_vertex>', `#include <uv_vertex>
        vec3 sc = vec3(length(instanceMatrix[0].xyz), length(instanceMatrix[1].xyz), length(instanceMatrix[2].xyz));
        vec3 n = abs(normal); float horiz = n.x > 0.5 ? sc.z : sc.x;
        vMapUv = vec2(uv.x * horiz / 9.0, uv.y * sc.y / 18.0) + vec2(instanceMatrix[3].x * 0.013, instanceMatrix[3].z * 0.017);
        if (n.y > 0.5) vMapUv = vec2(0.0, 0.0);`);
    };
    dayTint(im.material);
    city.add(im);
  });
  // street lights: rows of warm points along the avenues
  const lp = []; for (let bx = -14; bx <= 14; bx++) for (let s = -400; s < 200; s += 8) { const x = bx * (block + street) - street / 2 - block / 2; lp.push(x - 3.5, 0.6, s, x + 3.5, 0.6, s); }
  for (let bz = -18; bz <= 6; bz++) for (let s = -500; s < 500; s += 8) { const z = bz * (block + street) - 40 - block / 2 - street / 2; lp.push(s, 0.6, z - 3.5, s, 0.6, z + 3.5); }
  const lg = new THREE.BufferGeometry(); lg.setAttribute('position', new THREE.Float32BufferAttribute(lp, 3));
  const streetM = new THREE.PointsMaterial({ color: 0xffb36a, size: 1.4, map: dotTex(), transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, sizeAttenuation: true });
  city.add(new THREE.Points(lg, streetM));
  // the standup tower and its roof
  const tower = new THREE.Mesh(new THREE.BoxGeometry(ROOF.w - 2, ROOF_Y, ROOF.d - 2), new THREE.MeshBasicMaterial({ map: windowAtlas(9, 0.5) }));
  tower.position.set(0, ROOF_Y / 2 - 0.01, ROOF.z); city.add(tower);
  tower.material.onBeforeCompile = (sh) => { sh.vertexShader = sh.vertexShader.replace('#include <uv_vertex>', `#include <uv_vertex>
    vec3 n = abs(normal); vMapUv = vec2(uv.x * (n.x > 0.5 ? ${(ROOF.d - 2).toFixed(1)} : ${(ROOF.w - 2).toFixed(1)}) / 12.0, uv.y * ${ROOF_Y.toFixed(1)} / 24.0); if (n.y > 0.5) vMapUv = vec2(0.0);`); };
  dayTint(tower.material);
  const roof = new THREE.Mesh(new THREE.BoxGeometry(ROOF.w, 0.6, ROOF.d), clay(0x23252c, { rimAmt: 0.1 })); roof.position.set(0, ROOF_Y, ROOF.z); city.add(roof);
  // roof edge lights + a painted helipad grid
  const rt = canvasTex(1024, 784, (g, w, h) => { g.fillStyle = '#16181e'; g.fillRect(0, 0, w, h); g.strokeStyle = 'rgba(255,255,255,0.06)'; g.lineWidth = 2;
    for (let x = 0; x < w; x += 48) { g.beginPath(); g.moveTo(x, 0); g.lineTo(x, h); g.stroke(); } for (let y = 0; y < h; y += 48) { g.beginPath(); g.moveTo(0, y); g.lineTo(w, y); g.stroke(); }
    g.strokeStyle = 'rgba(255,214,120,0.55)'; g.lineWidth = 10; g.setLineDash([40, 30]); g.strokeRect(24, 24, w - 48, h - 48); });
  const roofTop = new THREE.Mesh(new THREE.PlaneGeometry(ROOF.w, ROOF.d), dayTint(new THREE.MeshLambertMaterial({ map: rt }), [0.30, 0.31, 0.35])); roofTop.rotation.x = -Math.PI / 2; roofTop.position.set(0, ROOF_Y + 0.31, ROOF.z); city.add(roofTop);
  city.userData.roofTop = roofTop;
  const ep = []; for (let s = -ROOF.w / 2; s <= ROOF.w / 2; s += 1.2) { ep.push(s, ROOF_Y + 0.45, ROOF.z - ROOF.d / 2, s, ROOF_Y + 0.45, ROOF.z + ROOF.d / 2); }
  for (let s = -ROOF.d / 2; s <= ROOF.d / 2; s += 1.2) { ep.push(-ROOF.w / 2, ROOF_Y + 0.45, ROOF.z + s, ROOF.w / 2, ROOF_Y + 0.45, ROOF.z + s); }
  const eg = new THREE.BufferGeometry(); eg.setAttribute('position', new THREE.Float32BufferAttribute(ep, 3));
  city.add(new THREE.Points(eg, new THREE.PointsMaterial({ color: 0xff5050, size: 0.5, map: dotTex(), transparent: true, depthWrite: false, blending: THREE.AdditiveBlending })));
  // clouds: soft puffs; one is a lightbulb (somebody's idea is in the air), one is a speech bubble
  const cloudM = []; const RC = rng(51);
  // a cloud: the shape filled and blurred soft, with scalloped puffs along its edge, lit from above
  const puffTex = (shape, W = 1024, H = 1024) => canvasTex(W, H, (g, w, h) => {
    const P = (x, y) => [(x * 0.8 + 1) * w / 2, (1 - y * 0.8) * h / 2];
    const edge = []; for (let i = 0; i < 40000 && edge.length < 70; i++) { const x = RC() * 2 - 1, y = RC() * 2 - 1, e = 0.06;
      if (shape(x, y) && (!shape(x + e, y) || !shape(x - e, y) || !shape(x, y + e) || !shape(x, y - e))) edge.push([x, y]); }
    const m = document.createElement('canvas'); m.width = w; m.height = h; const mg = m.getContext('2d'); mg.fillStyle = 'rgba(255,255,255,0.92)';   // sharp mask first
    const step = 0.02; for (let y = -1; y < 1; y += step) for (let x = -1; x < 1; x += step) if (shape(x, y)) { const [px, py] = P(x, y); mg.fillRect(px - 1, py - 1, step * 0.8 * w / 2 + 2, step * 0.8 * h / 2 + 2); }
    for (const [x, y] of edge) { const [px, py] = P(x, y); mg.beginPath(); mg.arc(px, py, (0.06 + RC() * 0.05) * w / 2, 0, 7); mg.fill(); }
    g.filter = 'blur(10px)'; g.drawImage(m, 0, 0);   // then one blur pass
    g.filter = 'none'; g.globalCompositeOperation = 'source-atop';   // shade: bright top, soft lavender underside
    const gr = g.createLinearGradient(0, 0, 0, h); gr.addColorStop(0, 'rgba(255,255,255,0)'); gr.addColorStop(1, 'rgba(176,170,206,0.45)'); g.fillStyle = gr; g.fillRect(0, 0, w, h);
    g.globalCompositeOperation = 'source-over'; });
  const shapes = {
    bulb: (x, y) => (x * x + (y - 0.3) * (y - 0.3) < 0.4) || (Math.abs(x) < 0.3 && y > -0.42 && y < -0.1) || (Math.abs(x) < 0.26 && ((y > -0.6 && y < -0.5) || (y > -0.76 && y < -0.66))) || (Math.abs(x) < 0.12 && y > -0.9 && y < -0.78),
    speech: (x, y) => (Math.abs(x) < 0.85 && Math.abs(y - 0.15) < 0.45) || (y < -0.28 && y > -0.75 && x > -0.55 && x < -0.55 + (y + 0.75) * 0.9),
    puff: (x, y) => (x * x / 0.8 + (y + 0.1) * (y + 0.1) / 0.12 < 1) || (((x + 0.2) * (x + 0.2) + (y - 0.12) * (y - 0.12)) < 0.12) || (((x - 0.3) * (x - 0.3) + (y - 0.05) * (y - 0.05)) < 0.08),
  };
  const texs = { bulb: puffTex(shapes.bulb), speech: puffTex(shapes.speech), puff: puffTex(shapes.puff), puff2: puffTex(shapes.puff) };
  const clouds = new THREE.Group(); city.add(clouds); city.userData.clouds = clouds;
  for (const [k, x, y, z, sz] of [['bulb', -70, 150, -470, 120], ['speech', 140, 125, -540, 120], ['puff', -230, 115, -520, 150], ['puff2', 290, 175, -470, 130], ['puff', 40, 215, -620, 170], ['puff2', -330, 190, -380, 110]]) {
    const m = new THREE.MeshBasicMaterial({ map: texs[k], transparent: true, depthWrite: false, fog: false }); cloudM.push(m);
    const c = new THREE.Mesh(new THREE.PlaneGeometry(sz, sz), m); c.position.set(x, y, z); c.lookAt(0, 40, 0); clouds.add(c); }
  // one call moves the whole city through the day: street lights fade out in daylight, clouds go from white to dusk lavender
  city.userData.setDay = (d) => { DAY.uDay.value = d; streetM.opacity = 1 - 0.9 * d;
    for (const m of cloudM) { m.color.setRGB(0.2 + 0.8 * d, 0.21 + 0.79 * d, 0.36 + 0.64 * d); m.opacity = 0.55 + 0.45 * d; } };
  return city;
}
