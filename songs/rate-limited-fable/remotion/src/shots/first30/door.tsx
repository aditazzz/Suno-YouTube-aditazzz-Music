// rl_first30: the door, her side (1I, 2A, 2C). Plate D1 (S7) when it lands; placeholder = the approved door frame
// (`door.jpg`, him behind the glass). Measured on door.jpg (1920 px) and scaled to the 2560 stage.
import React from 'react';
import { clamp, lerp } from '../../ease';
import { Quad } from '../../blocks/ScreenInsert';

export const DOOR = {
  plate: 'plates/door.jpg', placeholder: true,
  hingeX: 596, freeX: 1984, top: -357, bottom: 1296,                 // the glass leaf (1.36 x 1.62 m), top above frame
  glass: [[596, -357], [1984, -357], [1984, 1296], [596, 1296]] as Quad,
  head: [1357, 360] as [number, number],
  /** her hair and shoulder are in front of the glass (right of frame): code layers on the glass are clipped to this line */
  frontClip: 'polygon(0px -600px, 2100px -600px, 2100px 280px, 1915px 286px, 1850px 330px, 1806px 430px, 1792px 700px, 1800px 1000px, 1786px 1500px, 0px 1500px)',
  locks: { chain: [1600, 560] as [number, number], deadbolt: [1770, 700] as [number, number], floor: [1760, 1240] as [number, number] },   // latch side (hinge is left)
};

/** the glass leaf seen while it swings shut toward us: k 0 = edge-on at the hinge, 1 = shut (flat in the frame).
 *  The free edge comes nearer the lens as it closes, so it is drawn taller (perspective). */
export const leafQuad = (k: number): Quad => {
  const { hingeX, freeX, top, bottom } = DOOR;
  const x = lerp(hingeX + 40, freeX, k); const grow = (1 - k) * 0.18 * Math.sin(Math.PI * Math.min(1, k * 1.15));
  const h = bottom - top; const t = top - h * grow * 0.5, b = bottom + h * grow * 0.5;
  return [[hingeX, top], [x, t], [x, b], [hingeX, bottom]];
};

/** glass: a soft sheen band + a faint edge, nothing that glows */
export const GlassSheen: React.FC<{ pos?: number; k?: number }> = ({ pos = 0.45, k = 1 }) => (
  <div style={{ position: 'absolute', inset: 0, opacity: k,
    background: `linear-gradient(112deg, rgba(255,255,255,0) ${(pos - 0.14) * 100}%, rgba(255,255,255,0.10) ${pos * 100}%, rgba(255,255,255,0.02) ${(pos + 0.06) * 100}%, rgba(255,255,255,0) ${(pos + 0.16) * 100}%)` }} />
);

export const Deadbolt: React.FC<{ k: number }> = ({ k }) => {
  const [x, y] = DOOR.locks.deadbolt;
  return (
    <div style={{ position: 'absolute', left: x - 50, top: y - 50, width: 100, height: 100, borderRadius: '50%', background: 'radial-gradient(circle at 35% 30%, #f0d590, #a87c34 70%, #6e5020)', boxShadow: '0 6px 14px rgba(0,0,0,0.5)' }}>
      <div style={{ position: 'absolute', left: 38, top: 8, width: 24, height: 84, borderRadius: 10, background: 'linear-gradient(90deg,#8a6526,#e2bf74,#8a6526)', transform: `rotate(${90 * clamp(k)}deg)`, boxShadow: '0 2px 4px rgba(0,0,0,0.5)' }} />
    </div>
  );
};
export const Chain: React.FC<{ k: number }> = ({ k }) => {
  const [x, y] = DOOR.locks.chain; const slide = lerp(0, 120, clamp(k));
  return (
    <div style={{ position: 'absolute', left: x - 40, top: y - 30, width: 260, height: 60 }}>
      <div style={{ position: 'absolute', left: 100, top: 18, width: 160, height: 24, borderRadius: 6, background: 'linear-gradient(180deg,#e2bf74,#8a6526)', boxShadow: '0 3px 8px rgba(0,0,0,0.5)' }} />
      <svg width={260} height={160} style={{ position: 'absolute', left: 0, top: 0, overflow: 'visible' }}>
        {Array.from({ length: 6 }, (_, i) => {
          const u = i / 5; const cx = lerp(10, 110 + slide, u); const sag = (1 - (1 - 2 * u) ** 2) * lerp(70, 22, clamp(k));
          return <ellipse key={i} cx={cx} cy={30 + sag} rx={13} ry={8} fill="none" stroke="#c9a456" strokeWidth={5} />;
        })}
      </svg>
    </div>
  );
};
export const FloorBolt: React.FC<{ k: number }> = ({ k }) => {
  const [x, y] = DOOR.locks.floor; const drop = lerp(0, 50, clamp(k));
  return (
    <div style={{ position: 'absolute', left: x - 30, top: y - 130, width: 60, height: 200 }}>
      <div style={{ position: 'absolute', left: 0, top: 0, width: 60, height: 120, borderRadius: 8, background: 'linear-gradient(90deg,#8a6526,#e2bf74,#8a6526)', boxShadow: '0 4px 10px rgba(0,0,0,0.5)' }} />
      <div style={{ position: 'absolute', left: 18, top: 30 + drop, width: 24, height: 100, borderRadius: 6, background: 'linear-gradient(90deg,#6e5020,#d4b064,#6e5020)' }} />
    </div>
  );
};
