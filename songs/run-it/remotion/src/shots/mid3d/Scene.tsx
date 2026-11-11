// The 3D middle, grey-box stand-in (s46-s62): three.js inside Remotion. Every object is a pure function of world time
// `t` (times.ts worldT). Lit simply: a hemisphere + one key light per location, shadows on the near city only.
// Shared pieces (glow textures, building boxes, the window instances) are exported for the crash (../crash/).
import React, { useLayoutEffect, useMemo, useRef } from 'react';
import * as THREE from 'three';
import { useThree } from '@react-three/fiber';
import { clamp, easeInOut3, easeOut3, lerp, prog, smooth, spring } from './anim';
import { kickEnv, snareEnv } from '../../timing';
import { M } from './times';
import { Cam, makeCamera } from './camera';
import { BCOL, BR, CAR_M, CITY_M, LAMP_M, LIGHTS_M, RAIN_M, TOWER_M, WIN_H, WIN_W, bridgeSkyFade, mX, rainDrops, SM, type MB } from './bridge';
import { Bld, FAR, FAR_Z, HERO, MOON_R, NEAR, P, SUN_R, TOWER_X, cityWave, gold, moonsAt, oceanOn, passes, sunPos, tasteful,
  waveAmp, weird } from './world';

const col = (h: string) => new THREE.Color(h);
const mix = (a: string, b: string, k: number) => col(a).lerp(col(b), clamp(k));
export const X0 = 3000; // the car set

// ---------- camera ----------
export const Rig: React.FC<{ cam: Cam; fmt: '16x9' | '9x16' }> = ({ cam, fmt }) => {
  const { camera, size } = useThree();
  const apply = () => {
    // rc_916: 9:16 keeps the s58 roll (the car set lies along X; the 90-degree roll stands the tower up, the car climbs it
    // full frame) and the crop guide (CropGuide.tsx) turns with it. LAYOUT_916.md's fallback: 16:9's behaviour, full frame.
    const c = cam; void fmt;
    const ref = makeCamera(c, size.width / size.height);
    const pc = camera as THREE.PerspectiveCamera;
    pc.position.copy(ref.position); pc.quaternion.copy(ref.quaternion);
    pc.fov = ref.fov; pc.aspect = ref.aspect; pc.near = ref.near; pc.far = ref.far;
    if (ref.view && ref.view.enabled) pc.setViewOffset(ref.view.fullWidth, ref.view.fullHeight, ref.view.offsetX, ref.view.offsetY, ref.view.width, ref.view.height); else pc.clearViewOffset();
    pc.updateProjectionMatrix(); pc.updateMatrixWorld(true);
  };
  apply();
  useLayoutEffect(apply);
  return null;
};

// ---------- textures (deterministic canvas drawings) ----------
export function radialTex(stops: [number, string][], size = 256) {
  const c = document.createElement('canvas'); c.width = c.height = size;
  const g = c.getContext('2d')!; const gr = g.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size / 2);
  for (const [o, s] of stops) gr.addColorStop(o, s);
  g.fillStyle = gr; g.fillRect(0, 0, size, size);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
}
export function useTex<T>(f: () => T) { return useMemo(f, []); } // eslint-disable-line react-hooks/exhaustive-deps

// ---------- the sky: gradient sphere (mirrored below the horizon for the water), warm glow around the sun ----------
const SKY_VS = `varying vec3 vDir; void main(){ vDir = normalize((modelMatrix*vec4(position,1.0)).xyz - cameraPosition); gl_Position = projectionMatrix*viewMatrix*modelMatrix*vec4(position,1.0); }`;
const SKY_FS = `varying vec3 vDir; uniform vec3 top; uniform vec3 hor; uniform vec3 glowC; uniform vec3 sunDir; uniform float glow; uniform float glowW;
void main(){ vec3 d = normalize(vDir); float y = abs(d.y); vec3 c = mix(hor, top, smoothstep(0.0, 0.55, y));
  vec3 sd = normalize(sunDir); vec3 dm = vec3(d.x, abs(d.y), d.z); float a = max(dot(dm, sd), 0.0);
  c += glowC * glow * (pow(a, glowW) * 0.8 + pow(a, glowW * 0.25) * 0.06);
  gl_FragColor = vec4(c, 1.0); }`;
const v3 = (h: string) => { const c = col(h); c.convertLinearToSRGB(); return new THREE.Vector3(c.r, c.g, c.b); };
const Sky: React.FC<{ t: number; flat: number; camPos: THREE.Vector3; sun: number[] }> = ({ t, flat, camPos, sun }) => {
  const mat = useTex(() => new THREE.ShaderMaterial({ vertexShader: SKY_VS, fragmentShader: SKY_FS, side: THREE.BackSide, depthWrite: false,
    uniforms: { top: { value: new THREE.Vector3() }, hor: { value: new THREE.Vector3() }, glowC: { value: new THREE.Vector3() }, sunDir: { value: new THREE.Vector3() }, glow: { value: 0 }, glowW: { value: 60 } } }));
  // shader writes sRGB directly (no colorspace chunk): uniforms are sRGB triples
  const u = mat.uniforms;
  u.top.value.copy(v3(P.skyTop)).lerp(v3(P.flatSkyTop), flat);
  u.hor.value.copy(v3(t > M.S48 ? P.skyGlow : P.skyGlow)).lerp(v3(P.flatSkyBot), flat);
  u.glowC.value.copy(v3(P.coronaGold)).lerp(v3(P.sun), 0.3);
  u.sunDir.value.set(sun[0] - camPos.x, sun[1] - camPos.y, sun[2] - camPos.z).normalize();
  const g = gold(t), ecl = smooth(prog(t, M.S61 - 0.2, M.S61));
  u.glow.value = Math.max(0, (t < M.S48 ? 0 : 0.2) + 0.3 * g - 0.4 * ecl);
  u.glowW.value = 40;
  return <mesh position={camPos} material={mat} renderOrder={-10} frustumCulled={false}><sphereGeometry args={[4000, 32, 16]} /></mesh>;
};

const Stars: React.FC<{ camPos: THREE.Vector3; a: number }> = ({ camPos, a }) => {
  const geo = useTex(() => {
    let s = 7; const r = () => ((s = (s * 16807) % 2147483647) / 2147483647);
    const pts: number[] = [];
    for (let i = 0; i < 260; i++) { const th = r() * Math.PI * 2, y = 0.08 + r() * 0.9, rr = Math.sqrt(1 - y * y); pts.push(Math.cos(th) * rr * 3500, y * 3500, Math.sin(th) * rr * 3500); }
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(pts, 3)); return g;
  });
  return <points geometry={geo} position={camPos} frustumCulled={false} renderOrder={-9}>
    <pointsMaterial color={'#b8c8e0'} size={2} sizeAttenuation={false} transparent opacity={0.55 * a} depthWrite={false} />
  </points>;
};

// ---------- buildings + windows ----------
export type BldMat = { body: THREE.Material; sy?: (b: Bld) => number };
export const Boxes: React.FC<{ list: Bld[]; mat: THREE.Material | ((b: Bld) => THREE.Material); sy?: (b: Bld) => number; shadows?: boolean; frontZOf?: (b: Bld) => number }> = ({ list, mat, sy, shadows }) => (
  <>{list.map((b) => { const s = sy ? sy(b) : 1; return (
    <mesh key={b.id} position={[b.x + b.w / 2, (b.h * s) / 2, b.z + b.d / 2]} material={typeof mat === 'function' ? mat(b) : mat} castShadow={shadows} receiveShadow={shadows}>
      <boxGeometry args={[b.w, b.h * s, b.d]} />
    </mesh>); })}</>
);

/** lit windows of a building list as one InstancedMesh; colour per window from `glow(b, w)` (linear multiplier) */
export const Windows: React.FC<{ list: Bld[]; t: number; glow: (b: Bld, w: Bld['wins'][0]) => number; sy?: (b: Bld) => number; colorOf?: (warm: boolean) => string }> = ({ list, t, glow, sy, colorOf }) => {
  const all = useMemo(() => list.flatMap((b) => b.wins.map((w) => ({ b, w }))), [list]);
  const ref = useRef<THREE.InstancedMesh>(null);
  const m4 = useMemo(() => new THREE.Matrix4(), []), c = useMemo(() => new THREE.Color(), []);
  const upd = () => {
    const im = ref.current; if (!im) return;
    all.forEach(({ b, w }, i) => {
      const s = sy ? sy(b) : 1;
      const gl = glow(b, w);
      m4.makeScale(gl > 0 ? 0.9 : 0, gl > 0 ? 1.3 * Math.max(1, s * 0.85) : 0, 1).setPosition(b.x + w.u, w.v * s, b.z + b.d + 0.04); // glow 0 = gone, not black
      im.setMatrixAt(i, m4);
      c.set(colorOf ? colorOf(w.warm) : w.warm ? P.windowWarmWhite : P.window).multiplyScalar(Math.max(0, gl));
      im.setColorAt(i, c);
    });
    im.instanceMatrix.needsUpdate = true; if (im.instanceColor) im.instanceColor.needsUpdate = true;
  };
  useLayoutEffect(upd);
  return <instancedMesh ref={ref} args={[undefined as any, undefined as any, all.length]} frustumCulled={false} onUpdate={upd}>
    <planeGeometry args={[1, 1]} /><meshBasicMaterial toneMapped={false} />
  </instancedMesh>;
};

// ---------- the match-cut bridge (116.20 -> 119.7): the 2.5D city's own buildings in 3D, then re-laid into NEAR ----------
/** the city's sky (a screen-space gradient: skyTop at the horizon line - 810 px, horizon colour at the line), fading into the 3D sky over the re-lay */
export const bridgeSkyK = bridgeSkyFade;
const SSKY_VS = `void main(){ gl_Position = vec4(position.xy, 0.9999, 1.0); }`;
const SSKY_FS = `uniform vec3 top; uniform vec3 hor; uniform float y0; uniform float y1; uniform float hpx; uniform float a;
void main(){ float y = hpx - gl_FragCoord.y; float k = clamp((y - y0) / max(1.0, y1 - y0), 0.0, 1.0); gl_FragColor = vec4(mix(top, hor, k), a); }`;
const ScreenSky: React.FC<{ t: number; cam: Cam }> = ({ t, cam }) => {
  const { size, gl } = useThree();
  const mat = useTex(() => new THREE.ShaderMaterial({ vertexShader: SSKY_VS, fragmentShader: SSKY_FS, depthTest: true, depthWrite: false, transparent: true, // at the far plane: behind everything
    uniforms: { top: { value: v3(P.flatSkyTop) }, hor: { value: v3(P.flatSkyBot) }, y0: { value: 0 }, y1: { value: 1 }, hpx: { value: 1 }, a: { value: 1 } } }));
  const pr = gl.getPixelRatio();
  const c3 = makeCamera(cam, size.width / size.height);
  const q = new THREE.Vector3(mX(960), 0, 0).project(c3);
  const gy = ((1 - q.y) / 2) * size.height; // the horizon line (ground at the facade plane), css px
  mat.uniforms.y0.value = Math.min(0, gy - 810 * (size.height / 1080)) * pr; mat.uniforms.y1.value = gy * pr; mat.uniforms.hpx.value = size.height * pr;
  mat.uniforms.a.value = bridgeSkyK(t);
  return <mesh material={mat} renderOrder={-9.5} frustumCulled={false}><planeGeometry args={[2, 2]} /></mesh>;
};

/** the push window lights up as the push lands (it's dark in the city's frozen s44 cycle): the guy is home */
const heroK = (t: number) => easeInOut3(prog(t, BR.LIGHT, BR.LIGHT + 0.5));
/** inside the room (s48: the window's glow fills the frame, cut to the room): what would block the flight out over the bay goes */
const inRoom = (camZ: number) => camZ < 0.6;
const blocksBay = (b: MB) => b.layer === 'rear' || (b.layer === 'back' && b.x < 10 && b.x + b.w > -2);

/** the near city of s46-s48 = the 2.5D city's own buildings in 3D (registered to the city camera at the cut) */
const BridgeCity: React.FC<{ t: number; camZ: number; tall?: boolean }> = ({ t, camZ, tall = false }) => {
  const ps = passes(t);
  const sh = ps.shade;
  // the city's colours, now lit (emissive keeps the flat colour at the cut; the lights take over with the shadows pass)
  const mats = useTex(() => Object.fromEntries((['front', 'back', 'rear'] as const).map((k) => [k, new THREE.MeshStandardMaterial({ roughness: 0.82, metalness: 0.05,
    color: BCOL[k], emissive: BCOL[k] })])) as Record<string, THREE.MeshStandardMaterial>);
  Object.values(mats).forEach((m) => { m.emissiveIntensity = 1 - 0.3 * sh; });
  const street = useTex(() => new THREE.MeshStandardMaterial({ transparent: true, roughness: 0.9, metalness: 0 }));
  street.color.copy(col(BCOL.road)); street.opacity = 1 - 0.32 * ps.refl; street.roughness = 0.9 - 0.55 * ps.refl;
  street.emissive.copy(col(BCOL.road)); street.emissiveIntensity = 1 - 0.85 * sh;
  const room = useTex(() => new THREE.MeshBasicMaterial({ color: '#2b2433', side: THREE.FrontSide }));
  const hk = heroK(t), inside = inRoom(camZ);
  const list: (MB & { s: number })[] = CITY_M.filter((b) => !(inside && (b.hero || blocksBay(b)))).map((b) => ({ ...b, s: 1 }));
  const heroL = HERO;
  return (
    <group>
      {list.map((b) => (
        <mesh key={b.id} position={[b.x + b.w / 2, b.y0 + b.h / 2, b.z + b.d / 2]} material={mats[b.layer]} castShadow receiveShadow>
          <boxGeometry args={[b.w, b.h, b.d]} />
        </mesh>))}
      <FacadeShade list={list} hk={0} />
      <CityWindows list={list} t={t} light={ps.light} hk={inside ? 0 : hk} />
      <Props t={t} inside={inside} />
      {/* the hero's room (seen only from inside): floor, ceiling, side walls, the desk and the screen of the guy typing */}
      <mesh position={[heroL.x + heroL.w / 2, heroL.win.y - 1.45, -4]} rotation={[-Math.PI / 2, 0, 0]} material={room}><planeGeometry args={[heroL.w - 0.2, 7.6]} /></mesh>
      <mesh position={[heroL.x + heroL.w / 2, heroL.win.y + 1.2, -4]} rotation={[Math.PI / 2, 0, 0]} material={room}><planeGeometry args={[heroL.w - 0.2, 7.6]} /></mesh>
      <mesh position={[heroL.x + 0.12, heroL.win.y, -4]} rotation={[0, Math.PI / 2, 0]}><planeGeometry args={[7.6, 2.7]} /><meshBasicMaterial color={'#352b3a'} /></mesh>
      <mesh position={[heroL.x + heroL.w - 0.12, heroL.win.y, -4]} rotation={[0, -Math.PI / 2, 0]}><planeGeometry args={[7.6, 2.7]} /><meshBasicMaterial color={'#352b3a'} /></mesh>
      {/* rc_916: the tall 9:16 frame sees the desk and its bright screen pass under the camera on the way out (a pale wedge
          in the bottom corner, 126.2-126.5); once the camera has left them behind they go (9:16 only) */}
      {!(tall && camZ < -1.0) && <>
      <mesh position={[heroL.win.x, heroL.win.y - 0.85, -2.2]}><boxGeometry args={[1.6, 0.08, 0.8]} /><meshBasicMaterial color={'#4a3d40'} /></mesh>
      <mesh position={[heroL.win.x, heroL.win.y - 0.45, -2.45]}><planeGeometry args={[0.8, 0.5]} /><meshBasicMaterial color={'#e8eef8'} toneMapped={false} /></mesh>
      </>}
      {/* street: the city's flat road until pass 3 (reflections) wets it; the kerb and lane dashes stay */}
      <mesh position={[0, 0, 40]} rotation={[-Math.PI / 2, 0, 0]} material={street} receiveShadow renderOrder={2}><planeGeometry args={[400, 240]} /></mesh>
      <mesh position={[0, 0.006, 120]} rotation={[-Math.PI / 2, 0, 0]} renderOrder={2.5}><planeGeometry args={[400, 240]} /><meshBasicMaterial color={BCOL.road} transparent opacity={1 - ps.refl} depthWrite={false} /></mesh>
      <Kerb t={t} k={1} />
      {ps.refl > 0 && <group scale={[1, -1, 1]}>
        {list.filter((b) => b.layer === 'front').map((b) => <mesh key={b.id} position={[b.x + b.w / 2, b.y0 + b.h / 2, b.z + b.d / 2]} material={mats.front}><boxGeometry args={[b.w, b.h, b.d]} /></mesh>)}
        <CityWindows list={list.filter((b) => b.layer === 'front')} t={t} light={0} hk={inside ? 0 : hk} dim={0.55 * ps.refl} />
      </group>}
      <mesh position={[0, -0.05, -8]} rotation={[-Math.PI / 2, 0, 0]}><planeGeometry args={[400, 18]} /><meshBasicMaterial color={P.quay} /></mesh>
    </group>
  );
};

/** the city's windows (lit amber / cool white, unlit #172235), squashing with their building; the hero's (except the target) dim out as it narrows */
const CityWindows: React.FC<{ list: (MB & { s: number })[]; t: number; light: number; hk: number; dim?: number }> = ({ list, light, hk, dim }) => {
  const all = useMemo(() => CITY_M.flatMap((b) => b.wins.map((w) => ({ id: b.id, w }))), []);
  const ref = useRef<THREE.InstancedMesh>(null);
  const m4 = useMemo(() => new THREE.Matrix4(), []), c = useMemo(() => new THREE.Color(), []);
  const by = new Map(list.map((b) => [b.id, b]));
  const upd = () => {
    const im = ref.current; if (!im) return;
    all.forEach(({ id, w }, i) => {
      const b = by.get(id);
      const target = b?.hero && Math.abs(w.x - HERO.win.x) < 0.05 && Math.abs(w.y - HERO.win.y) < 0.05;
      if (!b) { m4.makeScale(0, 0, 0); im.setMatrixAt(i, m4); return; }
      const y = b.y0 + (w.y - b.y0) * b.s;
      m4.makeScale(WIN_W, WIN_H * b.s, 1).setPosition(w.x, y, b.z + b.d + 0.03);
      im.setMatrixAt(i, m4);
      const k = target ? Math.max(w.k, hk) : w.k; // the push window: as the city has it, lit as the hero takes over
      c.set(BCOL.winOff).lerp(new THREE.Color(w.cool ? '#e8eef8' : '#ffcf7a'), k);
      if (k > 0) c.multiplyScalar(1 + 0.08 * light * k + (target ? 0.15 * hk : 0));
      if (dim !== undefined) c.multiplyScalar(dim);
      im.setColorAt(i, c);
    });
    im.instanceMatrix.needsUpdate = true; if (im.instanceColor) im.instanceColor.needsUpdate = true;
  };
  useLayoutEffect(upd);
  return <instancedMesh ref={ref} args={[undefined as any, undefined as any, all.length]} frustumCulled={false} onUpdate={upd}>
    <planeGeometry args={[1, 1]} /><meshBasicMaterial toneMapped={false} />
  </instancedMesh>;
};

/** s45's pass-1 facade shading, kept on the 3D copy so pass 2 never looks flatter than pass 1: warm top, cool AO to the
 *  base (City.tsx drawBuilding) and the front row's left shade stripe (#243349, 18% of the width) */
const FacadeShade: React.FC<{ list: (MB & { s: number })[]; hk: number }> = ({ list, hk }) => {
  const tex = useTex(() => {
    const c = document.createElement('canvas'); c.width = 4; c.height = 256; const g = c.getContext('2d')!;
    const gr = g.createLinearGradient(0, 0, 0, 256);
    gr.addColorStop(0, 'rgba(255,243,220,0.07)'); gr.addColorStop(0.55, 'rgba(10,15,26,0)'); gr.addColorStop(1, 'rgba(5,8,16,0.5)');
    g.fillStyle = gr; g.fillRect(0, 0, 4, 256);
    const tx = new THREE.CanvasTexture(c); tx.colorSpace = THREE.SRGBColorSpace; return tx;
  });
  const a = 1 - hk;
  return <group>
    {list.map((b) => { const h = b.h * b.s, fz = b.z + b.d; return <group key={b.id}>
      {b.layer === 'front' && <mesh position={[b.x + b.w * 0.09, b.y0 + h / 2, fz + 0.012]} renderOrder={4}><planeGeometry args={[b.w * 0.18, h]} />
        <meshBasicMaterial color={BCOL.frontShade} transparent opacity={b.hero ? a : 1} depthWrite={false} /></mesh>}
      <mesh position={[b.x + b.w / 2, b.y0 + h / 2, fz + 0.02]} renderOrder={5}><planeGeometry args={[b.w, h]} />
        <meshBasicMaterial map={tex} transparent opacity={b.hero ? a : 1} depthWrite={false} /></mesh>
    </group>; })}
  </group>;
};

/** the city's kerb and lane dashes (they fade into NEAR's plain street over the re-lay) */
const Kerb: React.FC<{ t: number; k: number }> = ({ k }) => {
  const dashes = useMemo(() => { const out: number[] = []; for (let x = -4000; x < 6000; x += 95.3) out.push(x); return out; }, []);
  if (k <= 0.001) return null;
  const S = SM;
  return <group>
    <mesh position={[0, 0.012, 36 * S / 2]} rotation={[-Math.PI / 2, 0, 0]} renderOrder={3}><planeGeometry args={[400, 36 * S]} /><meshBasicMaterial color={BCOL.kerb} transparent opacity={k} depthWrite={false} /></mesh>
    {dashes.map((x) => <mesh key={x} position={[mX(x + 23.85), 0.014, 329 * S]} rotation={[-Math.PI / 2, 0, 0]} renderOrder={3}><planeGeometry args={[47.7 * S, 18 * S]} />
      <meshBasicMaterial color={'#ffffff'} transparent opacity={0.18 * k} depthWrite={false} /></mesh>)}
  </group>;
};

/** stand-ins for the 2.5D street furniture at the same places: traffic lights, the lamp post + red button, the bass tower
 *  with its crown, the car (parked; the push leaves it behind), the rain left of the line. They lie down with the re-lay. */
const Props: React.FC<{ t: number; inside: boolean }> = ({ t, inside }) => {
  const dark = useTex(() => new THREE.MeshStandardMaterial({ color: '#10151f', roughness: 0.7, emissive: '#10151f', emissiveIntensity: 0.6 }));
  const pole = useTex(() => new THREE.MeshStandardMaterial({ color: '#4b5465', roughness: 0.6, emissive: '#3a4358', emissiveIntensity: 0.8 }));
  const lamp = (c: string, k = 1) => <meshBasicMaterial color={new THREE.Color(c).multiplyScalar(k)} toneMapped={false} />;
  const rain = rainDrops(t);
  const rainA = 1;
  const rref = useRef<THREE.InstancedMesh>(null);
  const m4 = useMemo(() => new THREE.Matrix4(), []);
  const updR = () => { const im = rref.current; if (!im) return; let n = 0;
    for (const d of rain) { if (d.x > RAIN_M.edge) continue; m4.makeScale(0.13, d.l, 1).setPosition(d.x, d.y - d.l / 2, RAIN_M.z); im.setMatrixAt(n++, m4); }
    im.count = n; im.instanceMatrix.needsUpdate = true; };
  useLayoutEffect(updR);
  const tw = TOWER_M, ts = inside ? 0 : 1;
  const floors = useMemo(() => Array.from({ length: TOWER_M.floors }, (_, i) => i), []);
  return <group>
    {LIGHTS_M.map((L, i) => { const s = 1; if (s <= 0.002) return null; const hy = L.y * s; return <group key={i} position={[L.x, 0, L.z]}>
      <mesh position={[0, hy / 2, 0]} material={pole}><boxGeometry args={[0.35, hy, 0.35]} /></mesh>
      <mesh position={[0, hy + 1.1 * s, 0.1]} material={dark} scale={[1, s, 1]}><boxGeometry args={[1.3, 3.4, 0.9]} /></mesh>
      {[0, 1, 2].map((k) => <mesh key={k} position={[0, hy + (2.2 - k * 1.1) * s, 0.58]} scale={[1, s, 1]}><circleGeometry args={[0.42, 24]} />
        {lamp(k === 0 ? (L.red ? '#ff4b5c' : '#1d2433') : k === 2 ? (L.red ? '#1d2433' : '#4fdc9a') : '#1d2433')}</mesh>)}
    </group>; })}
    {(() => { const s = 1; if (s <= 0.002) return null; const hy = LAMP_M.y * s; return <group position={[LAMP_M.x, 0, LAMP_M.z]}>
      <mesh position={[0, hy / 2, 0]} material={pole}><boxGeometry args={[0.3, hy, 0.3]} /></mesh>
      <mesh position={[0, hy + 0.32 * s, 0.1]} scale={s}><sphereGeometry args={[0.32, 24, 16]} />{lamp('#ff4630')}</mesh>
    </group>; })()}
    {ts > 0.002 && <group>
      <mesh position={[tw.x + tw.w / 2, tw.base + (tw.floors * tw.floorH * ts) / 2, tw.z + tw.d / 2]} material={dark} castShadow><boxGeometry args={[tw.w, tw.floors * tw.floorH * ts, tw.d]} /></mesh>
      {floors.map((i) => <mesh key={i} position={[tw.x + tw.w / 2, tw.base + (i + 0.5) * tw.floorH * ts, tw.z + tw.d + 0.03]}>
        <planeGeometry args={[tw.w * 0.9, tw.floorH * 0.55 * ts]} />{lamp(i % 5 === 2 ? '#e8eef8' : '#ffcf7a', 0.55)}</mesh>)}
    </group>}
    {CITY_M.filter((b) => b.crown).map((b) => { const s = 1; return s > 0.002 && <mesh key="crown" position={[b.x + b.w / 2, b.y0 + b.h * s - 0.3, b.z + b.d + 0.05]}>
      <planeGeometry args={[b.w - 0.85, 0.7]} />{lamp('#ffcf7a')}</mesh>; })}
    <CarStandIn t={t} />
    {rainA > 0.01 && <instancedMesh ref={rref} args={[undefined as any, undefined as any, 1500]} frustumCulled={false} onUpdate={updR}>
      <planeGeometry args={[1, 1]} /><meshBasicMaterial color={'#b8c8e0'} transparent opacity={0.35 * rainA} depthWrite={false} toneMapped={false} /></instancedMesh>}
  </group>;
};
const CarStandIn: React.FC<{ t: number }> = () => {
  const s = CAR_M.scale;
  return <group position={[CAR_M.x, 0, CAR_M.z]} scale={s}>
    <mesh position={[0, 0.66, 0]}><boxGeometry args={[4.5, 0.62, 1.95]} /><meshStandardMaterial color={P.car} roughness={0.32} metalness={0.35} emissive={P.carLo} emissiveIntensity={0.6} /></mesh>
    <mesh position={[0.35, 0.68, 0]}><boxGeometry args={[1.4, 0.5, 1.97]} /><meshStandardMaterial color={P.carHi} roughness={0.3} metalness={0.3} emissive={P.carLo} emissiveIntensity={0.4} /></mesh>
    <mesh position={[-0.25, 1.22, 0]}><boxGeometry args={[2.1, 0.48, 1.62]} /><meshStandardMaterial color={P.carLo} roughness={0.2} metalness={0.4} emissive={P.carLo} emissiveIntensity={0.3} /></mesh>
    <mesh position={[-2.05, 1.62, 0]}><boxGeometry args={[0.42, 0.06, 1.9]} /><meshStandardMaterial color={P.carLo} emissive={P.carLo} emissiveIntensity={0.5} /></mesh>
    {[[1.45, 0.92], [-1.45, 0.92]].map(([wx, wz]) => <group key={wx} position={[wx, 0.36, wz]}>
      <mesh rotation={[Math.PI / 2, 0, 0]}><cylinderGeometry args={[0.36, 0.36, 0.3, 24]} /><meshStandardMaterial color={'#121319'} roughness={0.6} /></mesh>
      <mesh position={[0.1, 0.08, 0.155]}><boxGeometry args={[0.2, 0.16, 0.03]} /><meshBasicMaterial color={P.caliper} /></mesh></group>)}
  </group>;
};

// ---------- the near city (POST2b): flat 2.5D colours at the match-cut, then shadows, reflections, light ----------
/** the stand-in's own near city (seeded NEAR layout): replaced by the 2.5D city's buildings (BridgeCity) since the match-cut; kept for reference */
export const NearCity: React.FC<{ t: number; camZ: number }> = ({ t, camZ }) => {
  const ps = passes(t);
  const body = useTex(() => new THREE.MeshStandardMaterial({ roughness: 0.82, metalness: 0.05 }));
  body.color.copy(mix(P.flatBuilding, P.building, ps.shade));
  body.emissive.copy(body.color); body.emissiveIntensity = 1 - 0.3 * ps.shade;
  const street = useTex(() => new THREE.MeshStandardMaterial({ transparent: true, roughness: 0.9, metalness: 0 }));
  street.color.copy(col(P.street)); street.opacity = 1 - 0.32 * ps.refl; street.roughness = 0.9 - 0.55 * ps.refl;
  street.emissive.copy(col(P.street)); street.emissiveIntensity = 1 - 0.85 * ps.shade;
  const room = useTex(() => new THREE.MeshBasicMaterial({ color: '#2b2433', side: THREE.FrontSide }));
  const glow = (b: Bld, w: Bld['wins'][0]) => (b.hero ? (w.v === HERO.win.y && camZ < 0.6 ? 0 : 1.15) : 1) * (0.92 + 0.12 * ps.light);
  const heroL = HERO;
  return (
    <group>
      {/* once the window's glow fills the frame (camera within 0.6 m of the glass) the hero's box goes: we're in the room, looking out over the bay */}
      <Boxes list={camZ < 0.6 ? NEAR.filter((b) => !b.hero) : NEAR} mat={body} shadows />
      <Windows list={NEAR} t={t} glow={glow} />
      {/* the hero's room (seen only from inside): floor, ceiling, side walls, the desk and the screen of the guy typing */}
      <mesh position={[heroL.x + heroL.w / 2, heroL.win.y - 1.45, -4]} rotation={[-Math.PI / 2, 0, 0]} material={room}><planeGeometry args={[heroL.w - 0.2, 7.6]} /></mesh>
      <mesh position={[heroL.x + heroL.w / 2, heroL.win.y + 1.2, -4]} rotation={[Math.PI / 2, 0, 0]} material={room}><planeGeometry args={[heroL.w - 0.2, 7.6]} /></mesh>
      <mesh position={[heroL.x + 0.12, heroL.win.y, -4]} rotation={[0, Math.PI / 2, 0]}><planeGeometry args={[7.6, 2.7]} /><meshBasicMaterial color={'#352b3a'} /></mesh>
      <mesh position={[heroL.x + heroL.w - 0.12, heroL.win.y, -4]} rotation={[0, -Math.PI / 2, 0]}><planeGeometry args={[7.6, 2.7]} /><meshBasicMaterial color={'#352b3a'} /></mesh>
      <mesh position={[heroL.win.x, heroL.win.y - 0.85, -2.2]}><boxGeometry args={[1.6, 0.08, 0.8]} /><meshBasicMaterial color={'#4a3d40'} /></mesh>
      <mesh position={[heroL.win.x, heroL.win.y - 0.45, -2.45]}><planeGeometry args={[0.8, 0.5]} /><meshBasicMaterial color={'#e8eef8'} toneMapped={false} /></mesh>
      {/* street + reflections (mirror of the city under a semi-transparent wet street) */}
      <mesh position={[0, 0, 40]} rotation={[-Math.PI / 2, 0, 0]} material={street} receiveShadow renderOrder={2}><planeGeometry args={[200, 80]} /></mesh>
      {ps.refl > 0 && <group scale={[1, -1, 1]}><Boxes list={NEAR.filter((b) => b.z > -9)} mat={body} /><Windows list={NEAR.filter((b) => b.z > -9)} t={t} glow={() => 0.55 * ps.refl} /></group>}
      <mesh position={[0, -0.05, -8]} rotation={[-Math.PI / 2, 0, 0]}><planeGeometry args={[200, 18]} /><meshBasicMaterial color={P.quay} /></mesh>
    </group>
  );
};

// ---------- the bay: ocean, the reflected far city, the reflection path, the canvas under the sea ----------
const OCEAN = { w: 1700, d: 900, cz: -16 - 450, sx: 170, sz: 90 };
const Ocean: React.FC<{ t: number }> = ({ t }) => {
  const geo = useTex(() => { const g = new THREE.PlaneGeometry(OCEAN.w, OCEAN.d, OCEAN.sx, OCEAN.sz); g.rotateX(-Math.PI / 2); return g; });
  const mat = useTex(() => new THREE.MeshPhongMaterial({ transparent: true, flatShading: true, depthWrite: false }));
  const wk = weird(t);
  mat.color.copy(mix(P.oceanDeep, '#8e98aa', wk)); mat.opacity = lerp(0.84, 0.97, wk);
  mat.specular.copy(mix('#0c0f16', '#aab4c6', wk)); mat.shininess = lerp(10, 70, wk);
  mat.emissive.copy(col(P.ocean)); mat.emissiveIntensity = 0.5;
  useLayoutEffect(() => {
    const pos = geo.attributes.position as THREE.BufferAttribute;
    const C = { x: 0, z: -170 };
    for (let i = 0; i < pos.count; i++) {
      const x = pos.getX(i), z = pos.getZ(i) + OCEAN.cz;
      const r = Math.hypot(x - C.x, z - C.z);
      let h = waveAmp(t, r) * (Math.sin(x * 0.085 + t * 1.3) * 0.55 + Math.sin(z * 0.12 - t * 1.7 + x * 0.02) * 0.45);
      h += wk * 2.4 * Math.sin(x * 0.03 + z * 0.02 + t * 0.9); // slow liquid chrome
      pos.setY(i, h);
    }
    pos.needsUpdate = true; geo.computeBoundingSphere();
  });
  return <mesh geometry={geo} material={mat} position={[0, 0, OCEAN.cz]} renderOrder={3} />;
};
const RefPath: React.FC<{ t: number; sun: number[]; camPos: THREE.Vector3 }> = ({ t, sun, camPos }) => {
  const tex = useTex(() => {
    const c = document.createElement('canvas'); c.width = 64; c.height = 512; const g = c.getContext('2d')!;
    let s = 3; const r = () => ((s = (s * 16807) % 2147483647) / 2147483647);
    for (let y = 0; y < 512; y += 3) { const k = y / 512; const w = 64 * (0.25 + 0.75 * k) * (0.5 + r() * 0.5); g.fillStyle = `rgba(232,210,166,${(0.15 + 0.6 * r()) * (0.2 + 0.8 * k)})`; g.fillRect(32 - w / 2, y, w, 2); }
    const tx = new THREE.CanvasTexture(c); tx.colorSpace = THREE.SRGBColorSpace; return tx;
  });
  const a = ((t < M.S48 ? 0 : 0.3) + 0.3 * gold(t)) * (1 - 0.55 * smooth(prog(t, M.S61 - 0.2, M.S61)));
  // under the sun's azimuth, from the far shore toward the camera
  const dx = sun[0] - camPos.x, dz = sun[2] - camPos.z, ang = Math.atan2(dx, -dz);
  const len = 230, mid = 0.55;
  const px = camPos.x + Math.sin(ang) * (Math.abs(FAR_Z - camPos.z) * mid), pz = camPos.z - Math.cos(ang) * (Math.abs(FAR_Z - camPos.z) * mid);
  if (!oceanOn(t)) return null;
  return <mesh position={[px, 0.15, pz]} rotation={[-Math.PI / 2, 0, -ang]} renderOrder={4}>
    <planeGeometry args={[16, len]} /><meshBasicMaterial map={tex} transparent opacity={clamp(a)} depthWrite={false} blending={THREE.AdditiveBlending} toneMapped={false} />
  </mesh>;
};
const CanvasUnder: React.FC<{ t: number }> = ({ t }) => {
  const tex = useTex(() => {
    const c = document.createElement('canvas'); c.width = c.height = 64; const g = c.getContext('2d')!;
    g.fillStyle = '#050507'; g.fillRect(0, 0, 64, 64); g.fillStyle = 'rgba(255,255,255,0.5)'; g.fillRect(28, 28, 8, 8);
    const tx = new THREE.CanvasTexture(c); tx.wrapS = tx.wrapT = THREE.RepeatWrapping; tx.repeat.set(142, 75); tx.colorSpace = THREE.SRGBColorSpace;
    tx.anisotropy = 8; return tx;
  });
  if (oceanOn(t)) return null;
  const pop = spring(t - M.S53, 2.2, 0.6);
  return <group>
    <mesh position={[0, -3, -466]} rotation={[-Math.PI / 2, 0, 0]}><planeGeometry args={[1700, 900]} /><meshBasicMaterial map={tex} /></mesh>
    {/* the pink dot, tiny, still on the canvas under the sea */}
    <mesh position={[4, -2.9, -112]} rotation={[-Math.PI / 2, 0, 0]} scale={pop}><circleGeometry args={[2.6, 48]} /><meshBasicMaterial color={'#ff6fae'} /></mesh>
  </group>;
};

// ---------- the far city ----------
const FarCity: React.FC<{ t: number; mirrored?: boolean }> = ({ t, mirrored }) => {
  const g = gold(t), wk = weird(t);
  const body = useTex(() => new THREE.MeshStandardMaterial({ roughness: 0.85, metalness: 0.05 }));
  body.color.copy(col(P.building)); body.emissive.copy(col(P.building)); body.emissiveIntensity = 0.6;
  const sy = (b: Bld) => 1 + wk * (0.9 + 0.5 * Math.sin(b.x * 0.09)) ; // taffy: everyone stretches, not evenly
  const clapB = t >= M.S59 && t < M.S60 + 0.2;
  const glow = (b: Bld, w: Bld['wins'][0]) => {
    let k = 0.82 + 0.22 * g;
    if (t >= M.S61 - 0.3) k *= 0.55 + 0.6 * cityWave(t, b.x); // the eclipse: the lights come on in one wave
    if (clapB) k *= 1 + 1.1 * (w.seq < 0.02 ? kickEnv(t, 0.12) : snareEnv(t, 0.14)); // claps on 2 and 4 (one guy on 1 and 3)
    if (b.tower) k *= 1 + 0.6 * kickEnv(t, 0.18) * (t < M.S62 ? 1 : 0); // the bass tower
    return k * (mirrored ? 0.5 : 1);
  };
  return <group>
    <Boxes list={FAR} mat={body} sy={sy} />
    <Windows list={FAR} t={t} glow={glow} sy={sy} />
    {!mirrored && <Clocks t={t} sy={sy} />}
    <mesh position={[0, 0.6, FAR_Z - 20]}><boxGeometry args={[420, 1.2, 44]} /><meshBasicMaterial color={P.quay} /></mesh>
  </group>;
};

/** s62: every clock snaps to 2:29 on "time" (bar 77). Before: each runs fast at its own time. */
const Clocks: React.FC<{ t: number; sy: (b: Bld) => number }> = ({ t, sy }) => t < M.S62 - 0.9 ? null : (
  <>{FAR.filter((b) => b.clock).map((b, i) => {
    const fade = smooth(prog(t, M.S62 - 0.9, M.S62 - 0.4));
    const r = 2.6 * (b.clock! > 0.9 ? 2 : 1.2), s = sy(b);
    const snap = t >= M.S62 ? spring(t - M.S62, 3, 0.5) : 0;
    const own = (i * 2.7 + 1.3) * 60 + Math.floor((t - M.S48) * 6) * 2.5; // minutes, stepped like a second hand
    const target = 2 * 60 + 29;
    const mins = lerp(own, target + Math.round((own - target) / 720) * 720, snap);
    const ma = -(mins % 60) / 60 * Math.PI * 2, ha = -((mins / 60) % 12) / 12 * Math.PI * 2;
    return <group key={b.id} position={[b.x + b.w / 2, b.h * s - r - 1.2, b.z + b.d + 0.08]}>
      <mesh scale={0.6 + 0.4 * fade}><circleGeometry args={[r, 40]} /><meshBasicMaterial color={'#2a3245'} transparent opacity={fade} /></mesh>
      <mesh position={[0, 0, 0.02]} rotation={[0, 0, ha]}><planeGeometry args={[r * 0.12, r * 1.1]} /><meshBasicMaterial color={'#e8d2a6'} /></mesh>
      <mesh position={[0, 0, 0.03]} rotation={[0, 0, ma]}><planeGeometry args={[r * 0.08, r * 1.7]} /><meshBasicMaterial color={'#e8d2a6'} /></mesh>
    </group>;
  })}</>
);
// (hands are centred planes: half of each sticks out the back of the dial's centre, readable as a clock at this size)

// ---------- sun, moons, eclipse ----------
const SunMoons: React.FC<{ t: number; camPos: THREE.Vector3; mirrored?: boolean }> = ({ t, camPos, mirrored }) => {
  const glowT = useTex(() => radialTex([[0, 'rgba(255,243,234,1)'], [0.18, 'rgba(255,230,190,.55)'], [0.45, 'rgba(242,207,138,.18)'], [1, 'rgba(242,207,138,0)']]));
  const coronaT = useTex(() => radialTex([[0, 'rgba(255,250,244,0)'], [0.26, 'rgba(255,250,244,0)'], [0.3, 'rgba(255,250,244,1)'], [0.35, 'rgba(255,243,234,.8)'], [0.45, 'rgba(242,207,138,.55)'], [0.62, 'rgba(242,207,138,.22)'], [0.8, 'rgba(75,84,101,.12)'], [1, 'rgba(75,84,101,0)']]));
  const haloT = useTex(() => radialTex([[0, 'rgba(223,230,242,.0)'], [0.42, 'rgba(223,230,242,.28)'], [0.6, 'rgba(223,230,242,.08)'], [1, 'rgba(223,230,242,0)']]));
  const sun = sunPos(t), mo = moonsAt(t), tf = tasteful(t);
  const ecl = mo.total, dark = smooth(prog(t, M.NIGHT - 0.1, M.S61 - 0.05));
  const blink = t >= M.S52 && t < M.S53 + 0.4 ? Math.max(0.08, 1 - Math.exp(-Math.pow((t - (M.S52 + 0.6)) / 0.05, 2)) * 1) : 1; // "make it weird": the moons blink once
  const mcol = [mix(P.moonCool, P.moonDisk, dark), mix(P.moonWarm, P.moonDisk, dark)];
  const sunVis = t >= M.S48 - 0.5;
  const sunA = 1 - 0.85 * ecl;
  const dist = Math.hypot(sun[0] - camPos.x, sun[1] - camPos.y, sun[2] - camPos.z);
  void dist;
  return <group>
    {sunVis && <>
      <mesh position={sun as any}><circleGeometry args={[SUN_R, 64]} /><meshBasicMaterial color={P.sun} transparent opacity={sunA} toneMapped={false} /></mesh>
      <sprite position={[sun[0], sun[1], sun[2] - 2]} scale={[SUN_R * 9, SUN_R * 9, 1]}><spriteMaterial map={glowT} transparent opacity={(0.55 + 0.35 * gold(t)) * (1 - 0.7 * ecl) * (mirrored ? 0.5 : 1)} depthWrite={false} blending={THREE.AdditiveBlending} toneMapped={false} /></sprite>
      {ecl > 0 && <sprite position={[sun[0], sun[1], sun[2] + 1]} scale={[SUN_R * 7.5, SUN_R * 7.5, 1]}><spriteMaterial map={coronaT} transparent opacity={ecl * (mirrored ? 0.5 : 1)} depthWrite={false} blending={THREE.AdditiveBlending} toneMapped={false} /></sprite>}
    </>}
    {mo.p.map((p, i) => mo.rise[i] > 0 && (
      <group key={i} position={p as any}>
        <mesh scale={[1, blink, 1]}><circleGeometry args={[MOON_R[i], 64]} /><meshBasicMaterial color={mcol[i]} toneMapped={false} /></mesh>
        {ecl > 0 && <mesh position={[0, 0, -1.5]}><ringGeometry args={[MOON_R[i] - 0.2, MOON_R[i] + 1.1, 96]} /><meshBasicMaterial color={P.ring} transparent opacity={ecl * (mirrored ? 0.3 : 1)} toneMapped={false} /></mesh>}
        {tf > 0 && dark < 1 && <sprite position={[0, 0, -3]} scale={[MOON_R[i] * 4.2, MOON_R[i] * 4.2, 1]}><spriteMaterial map={haloT} transparent opacity={tf * (1 - dark)} depthWrite={false} blending={THREE.AdditiveBlending} /></sprite>}
      </group>
    ))}
  </group>;
};

/** s57: the move gizmo on the sun (red/green/blue axis arrows, muted), constant screen size; drawn over everything */
const Gizmo: React.FC<{ t: number; camPos: THREE.Vector3 }> = ({ t, camPos }) => {
  const a = smooth(prog(t, M.S57 - 0.3, M.S57 - 0.1)) * (1 - smooth(prog(t, M.S57 + 1.3, M.S57 + 1.6)));
  if (a <= 0) return null;
  const sun = sunPos(t), d = Math.hypot(sun[0] - camPos.x, sun[1] - camPos.y, sun[2] - camPos.z), s = d * 0.075 * (0.9 + 0.1 * easeOut3(prog(t, M.S57 - 0.3, M.S57)));
  const arrow = (c: string, rot: [number, number, number]) => (
    <group rotation={rot}>
      <mesh position={[0, 0.5, 0]} renderOrder={20}><cylinderGeometry args={[0.025, 0.025, 1, 12]} /><meshBasicMaterial color={c} depthTest={false} transparent opacity={a} /></mesh>
      <mesh position={[0, 1.08, 0]} renderOrder={20}><coneGeometry args={[0.08, 0.2, 18]} /><meshBasicMaterial color={c} depthTest={false} transparent opacity={a} /></mesh>
    </group>);
  return <group position={sun as any} scale={s}>
    {arrow('#d9606a', [0, 0, -Math.PI / 2])}{arrow('#8fcf7f', [0, 0, 0])}{arrow('#6f9bf0', [Math.PI / 2, 0, 0])}
    <mesh renderOrder={21}><sphereGeometry args={[0.06, 16, 12]} /><meshBasicMaterial color={'#f4f1f6'} depthTest={false} transparent opacity={a} /></mesh>
  </group>;
};

// ---------- the car set (s58): the "bass tower" lying along X, a road, the car; the 90-degree roll stands it up ----------
export const carX = (t: number) => lerp(-18, 28, prog(t, M.S58, M.S59));
const CarSet: React.FC<{ t: number }> = ({ t }) => {
  const tower = useMemo<Bld[]>(() => {
    let s = 11; const r = () => ((s = (s * 16807) % 2147483647) / 2147483647);
    const wins = []; for (let u = 1.2; u < 130; u += 1.9) for (let v = 2.2; v < 13; v += 2.6) if (r() < 0.35) wins.push({ u, v, warm: r() < 0.15, seq: v });
    return [{ id: 'bass', x: X0 - 40, z: -12, w: 130, d: 10, h: 14, wins, crash: 'grey' as const }];
  }, []);
  const body = useTex(() => new THREE.MeshStandardMaterial({ color: P.building, roughness: 0.8, emissive: P.building, emissiveIntensity: 0.35 }));
  const x = X0 + carX(t), spin = -(carX(t) + 18) / 0.36;
  const wheel = (wx: number, wz: number) => (
    <group position={[wx, 0.36, wz]}>
      <mesh rotation={[Math.PI / 2, 0, 0]}><cylinderGeometry args={[0.36, 0.36, 0.3, 24]} /><meshStandardMaterial color={'#121319'} roughness={0.6} /></mesh>
      <mesh position={[0, 0, wz > 0 ? 0.16 : -0.16]} rotation={[0, 0, spin]}><boxGeometry args={[0.5, 0.06, 0.02]} /><meshBasicMaterial color={'#8a90a0'} /></mesh>
      <mesh position={[0.1, 0.08, wz > 0 ? 0.155 : -0.155]}><boxGeometry args={[0.2, 0.16, 0.03]} /><meshBasicMaterial color={P.caliper} /></mesh>
    </group>);
  return <group>
    <Boxes list={tower} mat={body} />
    <Windows list={tower} t={t} glow={(b, w) => 0.85 + 0.7 * kickEnv(t, 0.2) * (w.v < 5 ? 1 : 0.5)} />
    <mesh position={[X0 + 25, 0, 3]} rotation={[-Math.PI / 2, 0, 0]}><planeGeometry args={[200, 10]} /><meshStandardMaterial color={P.street} roughness={0.7} emissive={P.street} emissiveIntensity={0.5} /></mesh>
    {Array.from({ length: 34 }, (_, i) => <mesh key={i} position={[X0 - 60 + i * 6, 0.02, 5.6]} rotation={[-Math.PI / 2, 0, 0]}><planeGeometry args={[2.4, 0.16]} /><meshBasicMaterial color={'#c9d1de'} /></mesh>)}
    {Array.from({ length: 12 }, (_, i) => <group key={i} position={[X0 - 50 + i * 16, 0, 7.6]}>
      <mesh position={[0, 2.5, 0]}><boxGeometry args={[0.14, 5, 0.14]} /><meshStandardMaterial color={'#2a3142'} /></mesh>
      <mesh position={[0, 5.05, -0.4]}><boxGeometry args={[0.5, 0.14, 0.9]} /><meshBasicMaterial color={P.windowWarmWhite} toneMapped={false} /></mesh>
    </group>)}
    {/* the car: Ultraviolet body, darker cabin, the wing, yellow calipers; unbadged */}
    <group position={[x, 0, 2.5]}>
      <mesh position={[0, 0.66, 0]}><boxGeometry args={[4.5, 0.62, 1.95]} /><meshStandardMaterial color={P.car} roughness={0.32} metalness={0.35} emissive={P.carLo} emissiveIntensity={0.6} /></mesh>
      <mesh position={[0.35, 0.68, 0]}><boxGeometry args={[1.4, 0.5, 1.97]} /><meshStandardMaterial color={P.carHi} roughness={0.3} metalness={0.3} emissive={P.carLo} emissiveIntensity={0.4} /></mesh>
      <mesh position={[-0.25, 1.22, 0]}><boxGeometry args={[2.1, 0.48, 1.62]} /><meshStandardMaterial color={P.carLo} roughness={0.2} metalness={0.4} emissive={P.carLo} emissiveIntensity={0.3} /></mesh>
      <mesh position={[-2.05, 1.62, 0]}><boxGeometry args={[0.42, 0.06, 1.9]} /><meshStandardMaterial color={P.carLo} emissive={P.carLo} emissiveIntensity={0.5} /></mesh>
      {[-0.7, 0.7].map((z) => <mesh key={z} position={[-1.95, 1.3, z]}><boxGeometry args={[0.06, 0.6, 0.06]} /><meshStandardMaterial color={P.carLo} /></mesh>)}
      <mesh position={[2.26, 0.78, 0]}><boxGeometry args={[0.04, 0.12, 1.6]} /><meshBasicMaterial color={P.windowWarmWhite} toneMapped={false} /></mesh>
      {wheel(1.45, 0.92)}{wheel(-1.45, 0.92)}{wheel(1.45, -0.92)}{wheel(-1.45, -0.92)}
    </group>
    <hemisphereLight args={['#4b5465', '#0a0d14', 0.9]} />
    <pointLight position={[x + 3, 5, 9]} intensity={260} distance={40} decay={2} color={'#fff3dc'} />
    <pointLight position={[x - 6, 5, 9]} intensity={160} distance={40} decay={2} color={'#ffcf7a'} />
    <directionalLight position={[X0, 30, 40]} intensity={0.8} color={'#b8c8e0'} />
  </group>;
};

// ---------- the whole stand-in world ----------
export const World: React.FC<{ t: number; cam: Cam }> = ({ t, cam }) => {
  const camPos = cam.pos;
  const carSet = cam.pos.x > X0 - 500;
  const ps = passes(t);
  const flat = 1 - ps.shade;
  const sun = sunPos(t);
  const near = t < M.S48 + 0.9;
  const bay = t >= M.S48 - 0.3;
  const g = gold(t), ecl = moonsAt(t).total;
  const sunDir = new THREE.Vector3(sun[0], sun[1], sun[2]).normalize();
  if (carSet) return <CarSet t={t} />;
  return <group>
    <Sky t={t} flat={near && t < M.S48 ? flat : 0} camPos={camPos} sun={sun} />
    <Stars camPos={camPos} a={near && t < M.S48 ? ps.shade * (1 - bridgeSkyK(t)) : 1} />
    {near && t < M.S48 && <ScreenSky t={t} cam={cam} />}
    {near && <>
      <BridgeCity t={t} camZ={camPos.z} tall={!!cam.tall && t >= 122.08} />
      <directionalLight position={[10, 30, 120]} intensity={0.35 * ps.shade} color={'#4b5465'} />
      <hemisphereLight args={['#4b5465', '#0a0d14', 1.1 * ps.shade]} />
      <directionalLight position={[-60, 90, -130]} intensity={1.6 * ps.shade + 0.6 * ps.light} color={'#b8c8e0'} castShadow
        shadow-mapSize-width={2048} shadow-mapSize-height={2048} shadow-camera-left={-90} shadow-camera-right={90} shadow-camera-top={90}
        shadow-camera-bottom={-90} shadow-camera-near={1} shadow-camera-far={400} shadow-bias={-0.0004} />
    </>}
    {bay && <>
      <FarCity t={t} />
      <SunMoons t={t} camPos={camPos} />
      {oceanOn(t) && <group scale={[1, -1, 1]}><FarCity t={t} mirrored /><SunMoons t={t} camPos={new THREE.Vector3(camPos.x, -camPos.y, camPos.z)} mirrored /></group>}
      {oceanOn(t) ? <Ocean t={t} /> : <CanvasUnder t={t} />}
      <RefPath t={t} sun={sun} camPos={camPos} />
      <Gizmo t={t} camPos={camPos} />
      <hemisphereLight args={['#1a2233', '#0a0d14', 0.9]} />
      <directionalLight position={[sunDir.x * 100, Math.max(10, sunDir.y * 100), sunDir.z * 100]} intensity={(0.7 + 1.8 * g) * (1 - 0.75 * ecl)} color={mix('#b8c8e0', P.sun, 0.4 + 0.6 * g)} />
    </>}
  </group>;
};
export { TOWER_X };
void easeInOut3;
