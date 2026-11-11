// THE CRASH, s63 (151.42-155.34): "Out of memory." The real 3D scene fails (approved frame 4): the eclipse set seen from
// the last good camera (cam/s63.json, frozen + a 1 px jitter), buildings fall back to wireframe or the true #ff00ff
// missing-texture checker, the ocean half-fails in stepped tiles, the sun is a wire fan, debug labels pop in on the
// silent beats. Hard cut in from s62 (the warmest frame of the film), audio edit E3 = digital silence; "Out of memory."
// types on its sung onset (154.40) in the red error bar (overlay barError, ../mid3d/overlay.ts).
// Stand-in: three.js grey-box. Palette: PALETTE.md "CRASH" (magenta only here; red only on the meter and the bar).
// Exported CrashPicture lets s64 (the reboot) shrink this exact picture to a card.
import React, { useMemo } from 'react';
import { AbsoluteFill } from 'remotion';
import { ThreeCanvas } from '@remotion/three';
import * as THREE from 'three';
import { MED, Layout, useAbsFrame, useLayout, useT } from '../../theme';
import type { ShotProps } from '../../shots';
import { CRASH_BEATS, M } from '../mid3d/times';
import { camAt, camFor, makeCamera, project, VP } from '../mid3d/camera';
import { Rig, useTex } from '../mid3d/Scene';
import { Bld, FAR, FAR_Z, MOON_R, SUN_FINAL, SUN_R, moonsAt } from '../mid3d/world';
import { clamp, easeOut3 } from '../mid3d/anim';

const K = { bg: '#1a2030', surface: '#0d0d16', ink: '#e8eef8', missing: '#ff00ff', checkerDark: '#0b0b10', wire: '#58f0ff', ring: '#fffaf4', grey: '#2a3142', greyWin: '#7d8496', water: '#0f131d' };
const CELL = 4; // metres per checker cell (>= ~24 px at the far skyline, PALETTE flag 7)

function checkerTex() {
  const d = new Uint8Array([255, 0, 255, 255, 11, 11, 16, 255, 11, 11, 16, 255, 255, 0, 255, 255]);
  const t = new THREE.DataTexture(d, 2, 2); t.magFilter = THREE.NearestFilter; t.minFilter = THREE.NearestFilter; t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.colorSpace = THREE.SRGBColorSpace; t.needsUpdate = true; return t;
}

const WireBox: React.FC<{ b: Bld; color: string; fill: string }> = ({ b, color, fill }) => {
  const geo = useMemo(() => {
    const box = new THREE.BoxGeometry(b.w, b.h, b.d);
    const e = new THREE.EdgesGeometry(box);
    const p = Array.from(e.attributes.position.array as Float32Array);
    const z = b.d / 2 + 0.02, x = b.w / 2, y = b.h / 2;
    p.push(-x, -y, z, x, y, z, x, -y, z, -x, y, z); // the front face's X (approved frame 4)
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(p, 3)); return g;
  }, [b]);
  return <group position={[b.x + b.w / 2, b.h / 2, b.z + b.d / 2]}>
    <mesh><boxGeometry args={[b.w, b.h, b.d]} /><meshBasicMaterial color={fill} polygonOffset polygonOffsetFactor={1} polygonOffsetUnits={1} /></mesh>
    <lineSegments geometry={geo}><lineBasicMaterial color={color} /></lineSegments>
  </group>;
};

const CheckBox: React.FC<{ b: Bld; tex: THREE.Texture }> = ({ b, tex }) => {
  const mats = useMemo(() => {
    const m = (rx: number, ry: number) => { const t = tex.clone(); t.repeat.set(Math.max(1, Math.round(rx / CELL)) / 2, Math.max(1, Math.round(ry / CELL)) / 2); t.needsUpdate = true; return new THREE.MeshBasicMaterial({ map: t }); };
    const side = m(b.d, b.h), front = m(b.w, b.h), top = m(b.w, b.d);
    return [side, side, top, top, front, front];
  }, [b, tex]);
  return <mesh position={[b.x + b.w / 2, b.h / 2, b.z + b.d / 2]} material={mats}><boxGeometry args={[b.w, b.h, b.d]} /></mesh>;
};

const GreyBox: React.FC<{ b: Bld }> = ({ b }) => (
  <group>
    <mesh position={[b.x + b.w / 2, b.h / 2, b.z + b.d / 2]}><boxGeometry args={[b.w, b.h, b.d]} /><meshBasicMaterial color={K.grey} /></mesh>
    {b.wins.map((w, i) => <mesh key={i} position={[b.x + w.u, w.v, b.z + b.d + 0.04]}><planeGeometry args={[0.9, 1.3]} /><meshBasicMaterial color={K.greyWin} /></mesh>)}
  </group>
);

/** the ocean: dark water, the right side failed in stepped tiles of missing texture (frame 4), a ghost of the reflection path */
const CrashOcean: React.FC<{ tex: THREE.Texture }> = ({ tex }) => {
  const tiles = useMemo(() => {
    const out: { x: number; z: number; s: number }[] = [];
    const S = 16; // 16 m tiles = 4x4 checker cells
    for (let zi = 0; zi < 8; zi++) for (let xi = -12; xi < 14; xi++) {
      const z = FAR_Z + 8 + zi * S, x = xi * S;
      const edge = 10 - zi * 1.05 + Math.sin(zi * 1.7) * 0.6; // the failed region steps toward the camera on the right
      if (xi > edge * 0.55 - 1 && x > -40) out.push({ x, z, s: S });
    }
    return out;
  }, []);
  const mat = useMemo(() => { const t = tex.clone(); t.repeat.set(2, 2); t.needsUpdate = true; return new THREE.MeshBasicMaterial({ map: t }); }, [tex]);
  return <group>
    <mesh position={[0, -0.02, -400]} rotation={[-Math.PI / 2, 0, 0]}><planeGeometry args={[1700, 900]} /><meshBasicMaterial color={K.water} /></mesh>
    {tiles.map((q, i) => <mesh key={i} position={[q.x + q.s / 2, 0.02, q.z + q.s / 2]} rotation={[-Math.PI / 2, 0, 0]} material={mat}><planeGeometry args={[q.s, q.s]} /></mesh>)}
  </group>;
};

/** sun: left half a dark disk with what's left of the eclipse ring, right half a wire fan; moon 1 solid, moon 2 wire */
const CrashSky: React.FC = () => {
  const fan = useMemo(() => {
    const p: number[] = []; const R = SUN_R * 1.15;
    for (let i = 0; i <= 12; i++) { const a = -Math.PI / 2 + (i / 12) * Math.PI; p.push(0, 0, 0, Math.cos(a) * R, Math.sin(a) * R, 0); }
    for (let i = 0; i < 48; i++) { const a0 = (i / 48) * Math.PI * 2, a1 = ((i + 1) / 48) * Math.PI * 2; p.push(Math.cos(a0) * R, Math.sin(a0) * R, 0, Math.cos(a1) * R, Math.sin(a1) * R, 0); }
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(p, 3)); return g;
  }, []);
  const circ = (r: number) => { const p: number[] = []; for (let i = 0; i < 64; i++) { const a0 = (i / 64) * Math.PI * 2, a1 = ((i + 1) / 64) * Math.PI * 2; p.push(Math.cos(a0) * r, Math.sin(a0) * r, 0, Math.cos(a1) * r, Math.sin(a1) * r, 0); }
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(p, 3)); return g; };
  const m2 = useMemo(() => circ(MOON_R[1]), []);
  const mo = moonsAt(M.CRASH - 0.01).p;
  return <group>
    <group position={SUN_FINAL as any}>
      <mesh position={[0, 0, -1]}><ringGeometry args={[SUN_R * 1.15, SUN_R * 1.15 + 1.6, 96, 1, Math.PI / 2, Math.PI]} /><meshBasicMaterial color={K.ring} side={THREE.DoubleSide} /></mesh>
      <lineSegments geometry={fan}><lineBasicMaterial color={K.ink} /></lineSegments>
    </group>
    <mesh position={mo[0] as any}><circleGeometry args={[MOON_R[0], 64, Math.PI / 2, Math.PI]} /><meshBasicMaterial color={'#0b0a12'} /></mesh>
    <lineSegments position={mo[1] as any} geometry={m2}><lineBasicMaterial color={K.ink} transparent opacity={0.4} /></lineSegments>
  </group>;
};

const CrashWorld: React.FC = () => {
  const tex = useTex(checkerTex);
  return <group>
    {FAR.map((b) => b.tower ? <WireBox key={b.id} b={b} color={K.wire} fill={K.bg} />
      : b.crash === 'wire' ? <WireBox key={b.id} b={b} color={K.ink} fill={K.bg} />
      : b.crash === 'check' ? <CheckBox key={b.id} b={b} tex={tex} /> : <GreyBox key={b.id} b={b} />)}
    <mesh position={[0, 0.6, FAR_Z - 20]}><boxGeometry args={[420, 1.2, 44]} /><meshBasicMaterial color={'#141a27'} /></mesh>
    <CrashOcean tex={tex} />
    <CrashSky />
  </group>;
};

// ---------- labels: debug labels on the silent grid ----------
const tower = () => FAR.find((b) => b.tower)!;
const leftBld = () => FAR.filter((b) => b.x < -100 && b.x > -160 && b.z > FAR_Z - 20).sort((a, b) => b.h - a.h)[0];
const LABELS: { t: number; text: string; at: () => number[]; dx: number; dy: number }[] = [
  { t: CRASH_BEATS.b3, text: 'sun.mat — not found', at: () => [SUN_FINAL[0] + SUN_R * 1.15, SUN_FINAL[1], SUN_FINAL[2]], dx: 60, dy: -26 },
  { t: CRASH_BEATS.b4, text: 'pigeon.001 — pressed button', at: () => { const b = tower(); return [b.x + b.w / 2, b.h, b.z + b.d]; }, dx: -40, dy: -110 },
  { t: CRASH_BEATS.b5, text: 'ocean.tex — missing', at: () => [60, 0, -150], dx: 40, dy: 30 },
  { t: CRASH_BEATS.b7, text: 'city_lod3 — failed', at: () => { const b = leftBld(); return [b.x + b.w / 2, b.h, b.z + b.d]; }, dx: -20, dy: -80 },
];

// 9:16 (LAYOUT_916.md): fixed slots, each plate 34 px with a cyan leader to its object; any label added later keeps
// plate bottom <= bar top - 24 and right edge <= 856 below y 960. (right: the plate is right-aligned to that x)
const SLOTS9: Record<string, { x?: number; right?: number; y: number }> = {
  'pigeon.001 — pressed button': { x: 116, y: 420 }, 'sun.mat — not found': { x: 512, y: 640 },
  'city_lod3 — failed': { x: 116, y: 800 }, 'ocean.tex — missing': { right: 856, y: 1036 },
};
const CrashLabels: React.FC<{ t: number; L: Layout; vp: VP }> = ({ t, L, vp }) => {
  const cam = makeCamera(camFor(camAt(M.CRASH), L.fmt), vp.w / vp.h);
  return <>{LABELS.map((lb) => {
    if (t < lb.t) return null;
    const p = project(cam, lb.at(), vp);
    const f = (t - lb.t) * 30, s = f < 2 ? 0.94 + 0.03 * f : 1; // a 2-frame pop (it's a crash log)
    const w = Math.round(lb.text.length * 34 * 0.6 + 34 + 26 + 16);
    let x = p.x + lb.dx, y = p.y + lb.dy;
    if (lb.dx < 0) x -= w;
    // 16:9: clear of the frame edge and the bar; 9:16: inside the safe zone (9% sides, top 13%) and above the bar
    if (L.fmt === '16x9') { x = clamp(x, 40, L.W - w - 40); y = clamp(y, 140, L.H - 260); }
    else { const sl = SLOTS9[lb.text]; if (sl) { x = sl.right !== undefined ? sl.right - w : sl.x!; y = sl.y; } else { x = clamp(x, 116, 856 - w); y = clamp(y, 262, 1110 - 64); } }
    const ax = L.fmt === '16x9' ? clamp(p.x, 0, L.W) : clamp(p.x, 130, 950), ay = L.fmt === '16x9' ? clamp(p.y, 0, L.H) : clamp(p.y, 270, 1180);
    const ex = clamp(ax, x, x + w), ey = clamp(ay, y, y + 64);
    return <React.Fragment key={lb.text}>
      <svg width={L.W} height={L.H} style={{ position: 'absolute', left: 0, top: 0, pointerEvents: 'none' }}>
        <line x1={ax} y1={ay} x2={ex} y2={ey} stroke={K.wire} strokeWidth={2} /><rect x={ax - 4} y={ay - 4} width={8} height={8} fill={K.wire} />
      </svg>
      <div style={{ ...MED, position: 'absolute', left: x, top: y, width: w, height: 64, boxSizing: 'border-box', background: K.surface, border: '2px solid rgba(232,238,248,.22)', borderRadius: 8,
        display: 'flex', alignItems: 'center', gap: 14, padding: '0 14px 0 12px', fontSize: 34, lineHeight: '40px', color: K.ink, whiteSpace: 'nowrap', transform: `scale(${s})`, transformOrigin: '0 50%' }}>
        <span style={{ width: 10, height: 10, flex: 'none', background: K.wire }} />{lb.text}
      </div>
    </React.Fragment>;
  })}</>;
};

/** screen-space failed tiles (frame 4): two missing-texture tiles in the sky and a scanline through the sun, on the 24 px grid */
const Glitch2D: React.FC<{ L: Layout; vp: VP }> = ({ L, vp }) => {
  const cam = makeCamera(camFor(camAt(M.CRASH), L.fmt), vp.w / vp.h);
  const sy = Math.round(project(cam, SUN_FINAL, vp).y / 2) * 2;
  const cell = L.fmt === '16x9' ? 24 : 24;
  const chk = `repeating-conic-gradient(${K.missing} 0% 25%, ${K.checkerDark} 0% 50%) 0 0 / ${cell * 2}px ${cell * 2}px`;
  const tiles = L.fmt === '16x9' ? [{ x: 216, y: 120, w: 168, h: 48 }, { x: 1464, y: 216, w: 240, h: 72 }] : [{ x: 120, y: 312, w: 168, h: 48 }, { x: 744, y: 504, w: 240, h: 72 }]; // 9:16: the second tile clear of the chrome block
  // 9:16: the missing-texture ocean is checker only in the first 260 px below the horizon, then fades into the dark plate
  // by y 1180 (the read is the city failing; a full magenta bottom half drowns it and bleeds worst in 4:2:0)
  const hz = L.fmt === '16x9' ? 0 : Math.round(project(cam, [0, 0, -4000], vp).y);
  const f0 = Math.min(hz + 260, 1100), f1 = Math.max(f0 + 40, 1180);
  return <>
    {tiles.map((r, i) => <div key={i} style={{ position: 'absolute', left: r.x, top: r.y, width: r.w, height: r.h, background: chk }} />)}
    <div style={{ position: 'absolute', left: 0, top: sy - 2, width: L.W, height: 4, background: K.missing, opacity: 0.9 }} />
    {L.fmt !== '16x9' && <div style={{ position: 'absolute', left: 0, top: f0, width: L.W, height: L.H - f0, background: `linear-gradient(to bottom, rgba(11,11,16,0) 0px, ${K.checkerDark} ${f1 - f0}px, ${K.checkerDark} 100%)` }} />}
  </>;
};

export const CrashPicture: React.FC<{ L: Layout; t: number; jitter?: boolean }> = ({ L, t, jitter = true }) => {
  const f = useAbsFrame();
  const vp: VP = { x: 0, y: 0, w: L.W, h: L.H };
  const h = (n: number) => { const x = Math.sin(n * 91.7 + 13.1) * 43758.5453; return x - Math.floor(x); };
  const jx = jitter ? Math.round(h(f) * 2) - 1 : 0, jy = jitter ? Math.round(h(f + 777) * 2) - 1 : 0; // "frozen, a 1 px jitter" (intended)
  return <AbsoluteFill style={{ background: K.bg, transform: `translate(${jx}px, ${jy}px)` }}>
    <ThreeCanvas width={L.W} height={L.H} flat gl={{ antialias: true, preserveDrawingBuffer: true }} style={{ background: K.bg }}>
      <Rig cam={camFor(camAt(M.CRASH), L.fmt)} fmt={L.fmt} />
      <CrashWorld />
    </ThreeCanvas>
    <Glitch2D L={L} vp={vp} />
    <CrashLabels t={t} L={L} vp={vp} />
  </AbsoluteFill>;
};

export const Crash: React.FC<ShotProps> = () => {
  const t = useT(); const L = useLayout();
  return <CrashPicture L={L} t={t} />;
};
void easeOut3;
