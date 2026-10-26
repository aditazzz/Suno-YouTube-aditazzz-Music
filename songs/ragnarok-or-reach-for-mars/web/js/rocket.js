// the steel rocket he carries: a stainless ship with an ogive nose, forward and aft flaps, a black tile belly. No logos.
import * as THREE from 'three';

export function makeRocket(env, { h = 0.42 } = {}) {
  const g = new THREE.Group(); const R = h * 0.068;
  const steel = new THREE.MeshStandardMaterial({ color: 0xd9dde3, metalness: 1, roughness: 0.2, envMap: env, envMapIntensity: 1.35 });
  const tile = new THREE.MeshStandardMaterial({ color: 0x141416, metalness: 0.2, roughness: 0.55, envMap: env, envMapIntensity: 0.4 });
  const dark = new THREE.MeshStandardMaterial({ color: 0x2a2b2e, metalness: 0.9, roughness: 0.35, envMap: env });
  const body = h * 0.72, nose = h * 0.24, base = h * 0.04;
  const cyl = new THREE.Mesh(new THREE.CylinderGeometry(R, R, body, 40, 1, true), steel); cyl.position.y = base + body / 2; g.add(cyl);
  const prof = []; for (let i = 0; i <= 20; i++) { const u = i / 20; prof.push(new THREE.Vector2(R * Math.sqrt(1 - u * u * 0.98) * (1 - 0.05 * u), u * nose)); }
  const ogive = new THREE.Mesh(new THREE.LatheGeometry(prof, 40), steel); ogive.position.y = base + body; g.add(ogive);
  // tiles on one side (the windward belly), running up onto the nose
  const shield = new THREE.Mesh(new THREE.CylinderGeometry(R * 1.012, R * 1.012, body, 40, 1, true, -Math.PI * 0.5, Math.PI), tile); shield.position.y = base + body / 2; g.add(shield);
  const sprof = prof.map((v) => new THREE.Vector2(v.x * 1.012, v.y)); const snose = new THREE.Mesh(new THREE.LatheGeometry(sprof.slice(0, 15), 40, -Math.PI * 0.5, Math.PI), tile); snose.position.y = base + body; g.add(snose);
  // flaps
  const flap = (w, hh, y, z0) => { const sh = new THREE.Shape(); sh.moveTo(0, 0); sh.lineTo(w, hh * 0.15); sh.lineTo(w * 0.9, hh * 0.8); sh.lineTo(0, hh); sh.closePath();
    const geo = new THREE.ExtrudeGeometry(sh, { depth: R * 0.12, bevelEnabled: false }); geo.translate(0, 0, -R * 0.06); return geo; };
  for (const s of [-1, 1]) {
    const fwd = new THREE.Mesh(flap(R * 1.3, nose * 0.42, 0, 0), dark); fwd.position.set(s * R * 0.92, base + body + nose * 0.02, 0); fwd.scale.x = s; g.add(fwd);
    const aft = new THREE.Mesh(flap(R * 1.9, body * 0.22, 0, 0), dark); aft.position.set(s * R * 0.95, base + body * 0.04, 0); aft.scale.x = s; g.add(aft);
  }
  // engines and a little skirt
  const skirt = new THREE.Mesh(new THREE.CylinderGeometry(R * 1.0, R * 0.92, base, 40), dark); skirt.position.y = base / 2; g.add(skirt);
  for (let k = 0; k < 3; k++) { const a = k / 3 * Math.PI * 2; const b = new THREE.Mesh(new THREE.CylinderGeometry(R * 0.2, R * 0.32, base * 1.4, 18, 1, true), dark);
    b.position.set(Math.cos(a) * R * 0.4, -base * 0.2, Math.sin(a) * R * 0.4); g.add(b); }
  // panel seams: a few thin dark rings
  for (let k = 1; k < 7; k++) { const r = new THREE.Mesh(new THREE.TorusGeometry(R * 1.002, R * 0.012, 4, 40), dark); r.rotation.x = Math.PI / 2; r.position.y = base + body * k / 7; g.add(r); }
  g.userData.h = h; g.userData.r = R;
  return g;
}
