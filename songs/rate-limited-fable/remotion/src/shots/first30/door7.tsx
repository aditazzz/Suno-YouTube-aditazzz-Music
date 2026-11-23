// rl_first30_v2: the door on the real S7 D1 set (rl_stills, bltworoom): 1I, 2A, 2C. Replaces the door.jpg placeholder
// (door.tsx stays as the fallback when the S7 files are missing). All positions come from build/stills/S7_D1/layout.json
// (pixels of the 4320x2430 still) scaled to the 2560 stage.
//   plates  D1 (shut, paddle parked) | D1open_upright / _smear / _bow (door open 80 deg into the lobby)
//   leaf    RGBA, the leaf alone shut; swung in CSS 3D about the hinge with the still's own lens (35 mm -> 2489 px)
//   locks   lockstrip_s0 / s0h / s1 / s2 / s3 (build/first30/tools/prep_locks.py): D1's own pixels with the chain, knob
//           and floor bolt moved; s0 = D1 exactly, so the strip can sit on D1 from the first frame without a seam
//   D1p     the paddle up beside his head (crop at its box), for 2C's lowering
import React from 'react';
import { AbsoluteFill, Img, staticFile } from 'remotion';
import { clamp, inCubic } from '../../ease';
import assets from './assets.json';
import { tealSrc } from './teal';

const A = assets as any;
export const HAVE_S7 = !!A['S7/D1'] && !!A['S7_lockstrip'];
const LAY = A.S7_layout ?? { size: [4320, 2430] };
export const K7 = 2560 / LAY.size[0];
export const p7 = (x: number, y: number): [number, number] => [x * K7, y * K7];
export const box7 = (b: number[]) => ({ left: b[0] * K7, top: b[1] * K7, width: (b[2] - b[0]) * K7, height: (b[3] - b[1]) * K7 });
const FOCAL = (LAY.lens ?? 35) / 36 * 2560;           // the still's lens in stage px (36 mm sensor width)

export const S7 = {
  hingeX: (LAY.door?.hinge_top_px?.[0] ?? 1339.4) * K7,
  leafBox: LAY.door?.leaf_box ?? [1338.5, 419, 2981.5, 2336.7],
  lockBox: A.S7_lockstrip?.box ?? [2800, 720, 3130, 2390],
  locks: { deadbolt: LAY.locks?.TR_PIV_deadbolt?.pivot_px, chain: LAY.locks?.TR_PIV_chain?.pivot_px, floor: LAY.locks?.TR_PIV_floorbolt?.pivot_px },
  signHook: p7(...((LAY.sign?.pivot_hook_px ?? [2160, 593]) as [number, number])),
  head: p7(...((LAY.him?.head_px ?? [2182, 1505]).slice(0, 2) as [number, number])),
  d1p: LAY.D1p_region ?? [1797, 619, 2751, 2418],
};

const full: React.CSSProperties = { position: 'absolute', left: 0, top: 0, width: 2560, height: 1440 };
export const Plate7: React.FC<{ name: string; opacity?: number; filter?: string }> = ({ name, opacity = 1, filter }) => (
  <Img src={staticFile(tealSrc(`first30/S7/${name}.jpg`))} style={{ ...full, opacity, filter }} />
);
/** an RGBA/region file placed at its box in the still's pixels */
export const At7: React.FC<{ file: string; box: number[]; opacity?: number; style?: React.CSSProperties }> = ({ file, box, opacity = 1, style }) => (
  <Img src={staticFile(`first30/S7/${file}`)} style={{ position: 'absolute', ...box7(box), opacity, ...style }} />
);

/** the three locks. k = 0 (all open, identical to D1) .. 3 (all locked); fractional k blends the neighbouring states
 *  (the deadbolt knob has its own 45-degree in-between state). glint: a brief lift on the lock that just turned. */
export const Locks7: React.FC<{ k: number; glint?: number }> = ({ k, glint = 0 }) => {
  const seq = ['s0', 's0h', 's1', 's2', 's3'];
  // map k (0..3) onto the 5-state sequence: 0->s0, 0.5->s0h, 1->s1, 2->s2, 3->s3
  const pos = k <= 1 ? k * 2 : k + 1;
  const i = Math.floor(clamp(pos, 0, 4)), u = clamp(pos, 0, 4) - i;
  const b = S7.lockBox; const f = undefined; void glint;   // (a lift on the whole strip showed its feathered box: off)
  return (
    <>
      <At7 file={`lockstrip_${seq[i]}.png`} box={b} style={{ filter: f }} />
      {u > 0.01 && i < 4 ? <At7 file={`lockstrip_${seq[i + 1]}.png`} box={b} opacity={u} style={{ filter: f }} /> : null}
    </>
  );
};

/** the glass leaf swinging shut toward us: ang 80 = open into the lobby, 0 = shut. CSS 3D about the hinge, perspective at
 *  the still's optical centre with its focal length, so the free edge travels toward the vanishing point like the render. */
export const Leaf7: React.FC<{ ang: number; opacity?: number }> = ({ ang, opacity = 1 }) => {
  const L = A['S7/leaf']; const off = L?.off ?? [1337, 417]; const sz = L?.size ?? [1646, 1921];
  const left = off[0] * K7, top = off[1] * K7, w = sz[0] * K7, h = sz[1] * K7;
  return (
    <div style={{ ...full, perspective: `${FOCAL.toFixed(1)}px`, perspectiveOrigin: '1280px 720px', opacity }}>
      <div style={{ position: 'absolute', left, top, width: w, height: h,
        transformOrigin: `${(S7.hingeX - left).toFixed(2)}px 50%`, transform: `rotateY(${ang.toFixed(3)}deg)`, backfaceVisibility: 'hidden' }}>
        <Img src={staticFile('first30/S7/leaf.png')} style={{ position: 'absolute', inset: 0, width: '100%', height: '100%' }} />
        {/* a reflection band riding the moving glass (masked to the leaf), so the near-clear door reads as it swings */}
        <div style={{ position: 'absolute', inset: 0, WebkitMaskImage: `url(${staticFile('first30/S7/leaf.png')})`, maskImage: `url(${staticFile('first30/S7/leaf.png')})`,
          WebkitMaskSize: '100% 100%', maskSize: '100% 100%',
          background: 'linear-gradient(105deg, rgba(255,255,255,0) 30%, rgba(255,250,240,0.22) 44%, rgba(255,255,255,0.05) 50%, rgba(255,250,240,0.12) 58%, rgba(255,255,255,0) 66%)' } as any} />
        {/* v3 (CD small item): a lamp's reflection streak that sweeps across the glass as the angle changes, brightest
            mid-swing, so the near-clear door is SEEN closing (the shutter samples smear it into a streak) */}
        {ang > 0.5 && ang < 79.5 ? (() => {
          const u = 1 - ang / 80, pos = 112 - 130 * u, k = Math.pow(Math.sin(Math.PI * u), 0.6);
          const m = `url(${staticFile('first30/S7/leaf.png')})`;
          return <div style={{ position: 'absolute', inset: 0, opacity: k, mixBlendMode: 'screen', WebkitMaskImage: m, maskImage: m, WebkitMaskSize: '100% 100%', maskSize: '100% 100%',
            background: `linear-gradient(102deg, rgba(255,240,215,0) ${pos - 7}%, rgba(255,238,210,0.42) ${pos}%, rgba(255,240,215,0.10) ${pos + 2.5}%, rgba(255,240,215,0) ${pos + 5}%)` } as any} />;
        })() : null}
        <div style={{ position: 'absolute', inset: 0, background: `rgba(210,220,230,${(0.10 * Math.sin(Math.PI * clamp(ang / 80))).toFixed(3)})`,
          WebkitMaskImage: `url(${staticFile('first30/S7/leaf.png')})`, maskImage: `url(${staticFile('first30/S7/leaf.png')})`, WebkitMaskSize: '100% 100%', maskSize: '100% 100%' } as any} />
      </div>
    </div>
  );
};
/** the open leaf baked into the D1open plates, erased (doorway_empty pixels) while the swinging leaf takes over */
export const OpenLeafErase: React.FC = () => <At7 file="openleaf_erase.png" box={[1250, 330, 1770, 2430]} />;

/** swing angle over [a, a+n): accelerates shut (a door pushed closed), lands exactly at a+n */
export const swingAng = (t: number, a: number, n = 6) => (t < a ? 80 : t >= a + n ? 0 : 80 * (1 - inCubic(clamp((t - a) / n))));

export const GlassSheen7: React.FC<{ pos: number; k?: number }> = ({ pos, k = 1 }) => {
  const b = box7(S7.leafBox);
  return (
    <div style={{ ...b, position: 'absolute', opacity: k, pointerEvents: 'none',
      background: `linear-gradient(112deg, rgba(255,255,255,0) ${(pos - 0.14) * 100}%, rgba(255,255,255,0.09) ${pos * 100}%, rgba(255,255,255,0.02) ${(pos + 0.06) * 100}%, rgba(255,255,255,0) ${(pos + 0.16) * 100}%)` }} />
  );
};
void AbsoluteFill;
