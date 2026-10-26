// the city at 9:15: blue hour, towers full of lit windows, street lights in rows, one wide roof where the standup
// floats. Everything is unlit (painted) geometry so the CPU renderer stays fast; bloom does the glow.
import * as THREE from 'three';
import { canvasTex, rng, dotTex, clay, basic } from './lib.js';

export const ROOF_Y = 30;                     // the standup roof
export const ROOF = { w: 34, d: 26, z: -6 };  // its size and centre (x = 0)

function windowAtlas(seed, warm = 0.42) {
  const R = rng(seed);
  return canvasTex(128, 256, (g, w, h) => {
    g.fillStyle = '#0d0f14'; g.fillRect(0, 0, w, h);
    for (let y = 6; y < h; y += 12) for (let x = 5; x < w; x += 10) {
      const r = R(); if (r < warm) g.fillStyle = `rgb(255,${200 + R() * 40 | 0},${130 + R() * 50 | 0})`;
      else if (r < warm + 0.12) g.fillStyle = `rgb(${150 + R() * 40 | 0},${200 + R() * 30 | 0},255)`;
      else g.fillStyle = `rgb(${22 + R() * 10 | 0},${25 + R() * 10 | 0},${32 + R() * 10 | 0})`;
      g.fillRect(x, y, 6, 7);
    }
  }, { nearest: false, repeat: [1, 1] });
}

export function buildCity() {
  const city = new THREE.Group(); const R = rng(17);
  // sky: deep blue overhead, a thin dawn line at the horizon
  const sky = new THREE.Mesh(new THREE.SphereGeometry(900, 32, 16), new THREE.ShaderMaterial({
    side: THREE.BackSide, depthWrite: false, uniforms: { uDawn: { value: 0.35 } },
    vertexShader: `varying vec3 vP; void main(){ vP = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
    fragmentShader: `uniform float uDawn; varying vec3 vP; void main(){ float y = vP.y;
      vec3 top = vec3(0.012,0.02,0.05), mid = vec3(0.05,0.08,0.16), hor = mix(vec3(0.10,0.12,0.22), vec3(0.75,0.42,0.30), uDawn);
      vec3 c = mix(hor, mid, smoothstep(0.0, 0.18, y)); c = mix(c, top, smoothstep(0.18, 0.7, y));
      float sunx = smoothstep(0.9, 1.0, dot(normalize(vec3(vP.x, 0.0, vP.z)), normalize(vec3(0.4,0.0,-1.0))));
      c += vec3(1.0,0.55,0.3) * uDawn * sunx * exp(-max(y,0.0)*14.0) * 0.6;
      gl_FragColor = vec4(c, 1.0); }` }));
  city.add(sky); city.userData.sky = sky;
  // ground + streets
  const ground = new THREE.Mesh(new THREE.PlaneGeometry(2000, 2000), basic(0x07080b)); ground.rotation.x = -Math.PI / 2; city.add(ground);
  // towers on a block grid, leaving the avenues open
  const atlases = [windowAtlas(1, 0.16), windowAtlas(2, 0.1), windowAtlas(3, 0.24), windowAtlas(4, 0.07)];
  const mats = atlases.map((a) => new THREE.MeshBasicMaterial({ map: a, color: 0xb8b8b8 }));
  const roofMat = basic(0x0b0c10);
  const groups = mats.map(() => []);
  const block = 26, street = 9;
  for (let bx = -14; bx <= 14; bx++) for (let bz = -18; bz <= 6; bz++) {
    const cx = bx * (block + street), cz = bz * (block + street) - 40;
    if (Math.abs(cx) < 30 && Math.abs(cz - ROOF.z + 10) < 30) continue;        // the standup tower stands here
    const n = 1 + (R() * 3 | 0);
    for (let i = 0; i < n; i++) {
      const w = 7 + R() * 9, d = 7 + R() * 9, h = 10 + Math.pow(R(), 1.6) * (Math.abs(bx) < 4 && bz > -8 ? 70 : 45);
      const x = cx + (R() - 0.5) * (block - w), z = cz + (R() - 0.5) * (block - d);
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
    city.add(im);
  });
  // street lights: rows of warm points along the avenues
  const lp = []; for (let bx = -14; bx <= 14; bx++) for (let s = -400; s < 200; s += 8) { const x = bx * (block + street) - street / 2 - block / 2; lp.push(x - 3.5, 0.6, s, x + 3.5, 0.6, s); }
  for (let bz = -18; bz <= 6; bz++) for (let s = -500; s < 500; s += 8) { const z = bz * (block + street) - 40 - block / 2 - street / 2; lp.push(s, 0.6, z - 3.5, s, 0.6, z + 3.5); }
  const lg = new THREE.BufferGeometry(); lg.setAttribute('position', new THREE.Float32BufferAttribute(lp, 3));
  city.add(new THREE.Points(lg, new THREE.PointsMaterial({ color: 0xffb36a, size: 1.4, map: dotTex(), transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, sizeAttenuation: true })));
  // the standup tower and its roof
  const tower = new THREE.Mesh(new THREE.BoxGeometry(ROOF.w - 2, ROOF_Y, ROOF.d - 2), new THREE.MeshBasicMaterial({ map: windowAtlas(9, 0.5) }));
  tower.position.set(0, ROOF_Y / 2 - 0.01, ROOF.z); city.add(tower);
  tower.material.onBeforeCompile = (sh) => { sh.vertexShader = sh.vertexShader.replace('#include <uv_vertex>', `#include <uv_vertex>
    vec3 n = abs(normal); vMapUv = vec2(uv.x * (n.x > 0.5 ? ${(ROOF.d - 2).toFixed(1)} : ${(ROOF.w - 2).toFixed(1)}) / 12.0, uv.y * ${ROOF_Y.toFixed(1)} / 24.0); if (n.y > 0.5) vMapUv = vec2(0.0);`); };
  const roof = new THREE.Mesh(new THREE.BoxGeometry(ROOF.w, 0.6, ROOF.d), clay(0x23252c, { rimAmt: 0.1 })); roof.position.set(0, ROOF_Y, ROOF.z); city.add(roof);
  // roof edge lights + a painted helipad grid
  const rt = canvasTex(1024, 784, (g, w, h) => { g.fillStyle = '#16181e'; g.fillRect(0, 0, w, h); g.strokeStyle = 'rgba(255,255,255,0.06)'; g.lineWidth = 2;
    for (let x = 0; x < w; x += 48) { g.beginPath(); g.moveTo(x, 0); g.lineTo(x, h); g.stroke(); } for (let y = 0; y < h; y += 48) { g.beginPath(); g.moveTo(0, y); g.lineTo(w, y); g.stroke(); }
    g.strokeStyle = 'rgba(255,214,120,0.55)'; g.lineWidth = 10; g.setLineDash([40, 30]); g.strokeRect(24, 24, w - 48, h - 48); });
  const roofTop = new THREE.Mesh(new THREE.PlaneGeometry(ROOF.w, ROOF.d), new THREE.MeshLambertMaterial({ map: rt })); roofTop.rotation.x = -Math.PI / 2; roofTop.position.set(0, ROOF_Y + 0.31, ROOF.z); city.add(roofTop);
  city.userData.roofTop = roofTop;
  const ep = []; for (let s = -ROOF.w / 2; s <= ROOF.w / 2; s += 1.2) { ep.push(s, ROOF_Y + 0.45, ROOF.z - ROOF.d / 2, s, ROOF_Y + 0.45, ROOF.z + ROOF.d / 2); }
  for (let s = -ROOF.d / 2; s <= ROOF.d / 2; s += 1.2) { ep.push(-ROOF.w / 2, ROOF_Y + 0.45, ROOF.z + s, ROOF.w / 2, ROOF_Y + 0.45, ROOF.z + s); }
  const eg = new THREE.BufferGeometry(); eg.setAttribute('position', new THREE.Float32BufferAttribute(ep, 3));
  city.add(new THREE.Points(eg, new THREE.PointsMaterial({ color: 0xff5050, size: 0.5, map: dotTex(), transparent: true, depthWrite: false, blending: THREE.AdditiveBlending })));
  return city;
}
