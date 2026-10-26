// Merge static meshes under `root` into one mesh per (material, cast, receive), so the CPU renderer issues a few
// hundred fewer draw calls (and fewer again in each shadow-map face). Anything under an object with
// userData.dynamic, or with a shader/transparent material, is left alone.
import * as THREE from 'three';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';

export function mergeStatic(root) {
  root.updateMatrixWorld(true);
  const inv = new THREE.Matrix4().copy(root.matrixWorld).invert();
  const groups = new Map(), victims = [];
  const visit = (o) => {
    if (o.userData && o.userData.dynamic) return;
    if (o.isMesh && !o.isInstancedMesh && o.material && !Array.isArray(o.material) && !o.material.isShaderMaterial && !o.material.transparent && o.visible) {
      const g = o.geometry; if (!g.attributes.position || !g.attributes.normal) { o.children.forEach(visit); return; }
      const key = `${o.material.uuid}|${o.castShadow ? 1 : 0}|${o.receiveShadow ? 1 : 0}`;
      let e = groups.get(key); if (!e) groups.set(key, e = { mat: o.material, cast: o.castShadow, recv: o.receiveShadow, geos: [] });
      const m = new THREE.Matrix4().multiplyMatrices(inv, o.matrixWorld);
      let gg = (g.index ? g.toNonIndexed() : g.clone());
      for (const k of Object.keys(gg.attributes)) if (!['position', 'normal', 'uv'].includes(k)) gg.deleteAttribute(k);
      if (!gg.attributes.uv) gg.setAttribute('uv', new THREE.Float32BufferAttribute(new Float32Array(gg.attributes.position.count * 2), 2));
      gg.morphAttributes = {}; gg.clearGroups(); gg.applyMatrix4(m); e.geos.push(gg); victims.push(o);
    }
    o.children.forEach(visit);
  };
  root.children.forEach(visit);
  for (const o of victims) { o.visible = false; o.userData.merged = true; }
  let n = 0;
  for (const e of groups.values()) {
    if (e.geos.length < 2) { for (const v of victims) if (v.material === e.mat && v.castShadow === e.cast && v.receiveShadow === e.recv) v.visible = true; continue; }
    const geo = mergeGeometries(e.geos, false); if (!geo) continue;
    const mesh = new THREE.Mesh(geo, e.mat); mesh.castShadow = e.cast; mesh.receiveShadow = e.recv; mesh.matrixAutoUpdate = false; mesh.userData.mergedStatic = true; root.add(mesh); n++;
  }
  // remove the hidden originals from the graph entirely (fewer objects to traverse each frame)
  for (const o of victims) if (!o.visible && o.parent) o.parent.remove(o);
  return { merged: victims.length, meshes: n };
}
