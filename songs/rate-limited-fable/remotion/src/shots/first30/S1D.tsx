// 1D, the master, first time (first30.md): his lobby left, her room right, the door open between. On beats 2 and 4 a
// green-ticked parcel slides through the doorway her way (ease-out, contact shadow, a 2-frame settle). Lobby clock 2:01
// in code. Very slow push 1.00 -> 1.03. Plate T1 (S3) when it lands; placeholder = approved room_b2b (no desk, no cat
// on the door frame, so the paw bats are not in this version).
import React from 'react';
import { useCurrentFrame } from 'remotion';
import { clamp, inOutSine, lerp, outCubic } from '../../ease';
import { ShotDef, ShotProps } from '../types';
import { DigitalClock } from '../../blocks/Clock';
import { PandaClock, pt } from '../../blocks/PandaClock';
import { parseClock, frameOf } from '../../timing';
import { Cam, PlateImg, MBlur } from './kit';
import { Img, staticFile } from 'remotion';
import { existsT1 } from './t1flag';

export const T1 = { plate: 'plates/room_b2b.jpg', placeholder: true, floorY: 1395, path: [640, 1180] as [number, number], clock: [150, 150] as [number, number] };

export const Parcel: React.FC<{ x: number; y: number; w?: number; tick?: boolean; rot?: number; label?: string }> = ({ x, y, w = 120, tick = true, rot = 0 }) => {
  const h = w * 0.62;
  return (
    <div style={{ position: 'absolute', left: x - w / 2, top: y - h, width: w, height: h, transform: `rotate(${rot}deg)`, transformOrigin: '50% 100%' }}>
      <div style={{ position: 'absolute', left: -w * 0.08, right: -w * 0.08, bottom: -h * 0.12, height: h * 0.24, borderRadius: '50%', background: 'radial-gradient(ellipse, rgba(0,0,0,0.45), rgba(0,0,0,0) 70%)' }} />
      <div style={{ position: 'absolute', inset: 0, borderRadius: 5, background: 'linear-gradient(180deg,#d9a866 0%,#b97f40 60%,#8f5d2e 100%)', boxShadow: 'inset 0 2px 0 rgba(255,230,190,0.45), 0 0 0 3px rgba(60,35,15,0.55)' }} />
      <div style={{ position: 'absolute', left: w * 0.44, top: 0, width: w * 0.12, height: h, background: 'rgba(110,70,35,0.45)' }} />
      {tick ? (
        <div style={{ position: 'absolute', left: w * 0.6, top: h * 0.2, width: w * 0.3, height: w * 0.3, borderRadius: '50%', background: '#e6e2da' }}>
          <svg viewBox="0 0 10 10" width="100%" height="100%"><path d="M2.2 5.3 L4.3 7.3 L8 2.9" stroke="#2fbf71" strokeWidth={1.5} fill="none" strokeLinecap="round" /></svg>
        </div>
      ) : null}
    </div>
  );
};

const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame();
  const beats = [shot.grid?.[1] ?? 10.125, shot.grid?.[3] ?? 11.29].map((t) => frameOf(t) - shot.from);
  const s = lerp(1.0, 1.03, clamp(f / (shot.dur - 1)));
  return (
    <Cam cx={1180} cy={760} s={s}>
      <PlateImg src={T1.plate} />
      <DigitalClock x={T1.clock[0]} y={T1.clock[1]} minutes={parseClock('2:01 AM')} size={72} color="#e2d6b8" glow={false} />
      {beats.map((b, i) => {
        const d = f - (b - 4);                    // starts 4 frames before the beat, crosses the jamb on it
        if (d < 0) return null;
        const k = outCubic(clamp(d / 14)); const settle = d > 14 && d < 17 ? [-3, 1.5, 0][d - 15] ?? 0 : 0;
        const x = lerp(T1.path[0], T1.path[1], k) + settle;
        return <div key={i} style={{ opacity: clamp(d / 4) }}><Parcel x={x} y={T1.floorY} w={210} rot={(1 - k) * -2} /></div>;
      })}
    </Cam>
  );
};

// v2 (rl_first30_v2): the real S3 T1 master (rl_stills, final): his lobby left, her room right, the door open, her squat at
// the threshold, the cat on the door top, the lobby clock with no hands (2:01 in code). On beats 2 and 4 a loose parcel
// (T1's own RGBA parcels, contact shadow in code) slides through the doorway her way and settles by her boots, passing
// BEHIND the near jamb (a strip of T1 redrawn over it), and the cat's paw is out (T1_paw_region) as each one goes through.
const K3 = 2560 / 4320;
const PARCELS = [
  { file: 'first30/T1_parcel00.png', box: [1977, 2144, 2149, 2298], foot: 2290, from: -690 },   // S3 px (crop box, base line, start offset)
  { file: 'first30/T1_parcel01.png', box: [1892, 1937, 2013, 2055], foot: 2047, from: -600 },
];
const CLOCK3 = { cx: 682.7 * K3, cy: 490.2 * K3, r: 94.7 * K3 };
const Hands: React.FC<{ minutes: number }> = ({ minutes }) => {
  const h = ((minutes / 60) % 12) * 30, m = (minutes % 60) * 6; const r = CLOCK3.r;
  return (
    <svg style={{ position: 'absolute', left: CLOCK3.cx - r, top: CLOCK3.cy - r, width: 2 * r, height: 2 * r, overflow: 'visible' }} viewBox={`${-r} ${-r} ${2 * r} ${2 * r}`}>
      <g style={{ filter: 'blur(0.4px)' }}>
        <line x1={0} y1={r * 0.12} x2={0} y2={-r * 0.48} stroke="#2a2622" strokeWidth={r * 0.085} strokeLinecap="round" transform={`rotate(${h})`} />
        <line x1={0} y1={r * 0.14} x2={0} y2={-r * 0.74} stroke="#2a2622" strokeWidth={r * 0.055} strokeLinecap="round" transform={`rotate(${m})`} />
        <circle r={r * 0.07} fill="#2a2622" />
      </g>
    </svg>
  );
};
const StageT1: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame();
  const beats = [shot.grid?.[1] ?? 10.125, shot.grid?.[3] ?? 11.29].map((t) => frameOf(t) - shot.from);
  const s = lerp(1.0, 1.03, clamp(f / (shot.dur - 1)));
  const pawOut = beats.some((b) => f >= b - 2 && f <= b + 3);
  const parcelAt = (i: number, t: number) => {
    const d = t - (beats[i] - 5);                       // starts 5 frames before the beat, crosses the jamb on it
    if (d < 0) return null;
    const k = outCubic(clamp(d / 14)); const settle = d > 14 && d < 17 ? [-4, 2, 0][Math.floor(d) - 15] ?? 0 : 0;
    return { dx: lerp(PARCELS[i].from, 0, k) * K3 + settle, op: clamp(d / 3), moving: d < 14 };
  };
  return (
    <Cam cx={1407} cy={712} s={lerp(1.11, 1.12, clamp(f / (shot.dur - 1)))}>   {/* left edge >= 254: the 429 paddle by his desk (x 110-224) stays out until 2B */}
      <PlateImg src="first30/T1.jpg" />
      <PandaClock cx={CLOCK3.cx} cy={CLOCK3.cy} r={CLOCK3.r * 1.16} time={pt(2, 1)} variant="wall" light={0.9} uid="s1d" />{/* rl_cut4: THE panda wall clock at 2:01 over the plate's old gold face (its code hands read 8:00: film minutes) */}
      {pawOut ? <Img src={staticFile('first30/T1_paw.jpg')} style={{ position: 'absolute', left: 1582 * K3, top: 0, width: 328 * K3, height: 483 * K3 }} /> : null}
      {[1, 0].map((i) => {
        const p = PARCELS[i];
        const at = parcelAt(i, f); if (!at) return null;
        const [x0, y0, x1, y1] = p.box.map((v) => v * K3);
        const one = (dx: number, op: number) => (
          <div style={{ position: 'absolute', left: 0, top: 0, opacity: op }}>
            <div style={{ position: 'absolute', left: x0 + dx - 6, top: p.foot * K3 - 10, width: x1 - x0 + 12, height: 20, borderRadius: '50%', background: 'radial-gradient(ellipse, rgba(20,14,8,0.45), rgba(20,14,8,0) 70%)' }} />
            <Img src={staticFile(p.file)} style={{ position: 'absolute', left: x0 + dx, top: y0, width: x1 - x0, height: y1 - y0 }} />
          </div>
        );
        return (
          <React.Fragment key={i}>
            {/* draw order: parcel 01 (behind her boots) -> her boots (dark matte from T1) -> parcel 00 (in front of them) */}
            {i === 0 ? <Img src={staticFile('first30/T1_boots.png')} style={{ position: 'absolute', left: 1640 * K3, top: 1850 * K3, width: 390 * K3, height: 320 * K3 }} /> : null}
            {at.moving ? <MBlur n={4} shutter={0.5} render={(dt) => { const a2 = parcelAt(i, f + dt); return a2 ? one(a2.dx, a2.op) : null; }} /> : one(at.dx, at.op)}
          </React.Fragment>
        );
      })}
      {/* the near jamb stays in front of the parcels going through */}
      <Img src={staticFile('first30/T1_jamb.png')} style={{ position: 'absolute', left: 1526 * K3, top: 1450 * K3, width: 72 * K3, height: 880 * K3 }} />
    </Cam>
  );
};
// rl_fix2_open (WATCH 1D: her squat in front of the chair read as a failed sit; the robot cut by the left edge; a 2.3 s still):
// the new S3 still T1s (build/stills/fix2_open_1D, same camera/state as T1): HER STANDING, arms folded, on the doormat at his open
// door, eyes on him (waiting her turn: 1E's ticket dispenser pays it off); the parked 429 paddle stand is out of that render, so the
// frame opens to the whole plate: the robot whole at his desk, a slow push toward the doorway 1.00 -> 1.06. Parcels slide her way on
// beats 2 and 4 (T1's RGBAs, same camera) behind/in front of her as before (her own RGBA is the occluder now); the paw bats.
import t1s from './t1s.json';
const StageT1s: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame();
  const beats = [shot.grid?.[1] ?? 10.125, shot.grid?.[3] ?? 11.29].map((t) => frameOf(t) - shot.from);
  const k = 0.7 * inOutSine(clamp(f / (shot.dur - 1))) + 0.3 * clamp(f / (shot.dur - 1));
  const pawOut = beats.some((b) => f >= b - 2 && f <= b + 3);
  const parcelAt = (i: number, t: number) => {
    const d = t - (beats[i] - 5);
    if (d < 0) return null;
    const kk = outCubic(clamp(d / 14)); const settle = d > 14 && d < 17 ? [-4, 2, 0][Math.floor(d) - 15] ?? 0 : 0;
    return { dx: lerp(PARCELS[i].from, 0, kk) * K3 + settle, op: clamp(d / 3), moving: d < 14 };
  };
  const [hx0, hy0, hx1, hy1] = (t1s as any).her_box.map((v: number) => v * K3);
  return (
    <Cam cx={lerp(1280, 1330, k)} cy={lerp(720, 760, k)} s={lerp(1.0, 1.06, k)}>
      <PlateImg src="fix2/open/T1s.jpg" />
      <PandaClock cx={CLOCK3.cx} cy={CLOCK3.cy} r={CLOCK3.r * 1.16} time={pt(2, 1)} variant="wall" light={0.9} uid="s1d" />{/* rl_cut4: THE panda wall clock at 2:01 over the plate's old gold face (its code hands read 8:00: film minutes) */}
      {pawOut ? <Img src={staticFile('first30/T1_paw.jpg')} style={{ position: 'absolute', left: 1582 * K3, top: 0, width: 328 * K3, height: 483 * K3 }} /> : null}
      {[1, 0].map((i) => {
        const p = PARCELS[i];
        const at = parcelAt(i, f); if (!at) return null;
        const [x0, y0, x1, y1] = p.box.map((v) => v * K3);
        const one = (dx: number, op: number) => (
          <div style={{ position: 'absolute', left: 0, top: 0, opacity: op }}>
            <div style={{ position: 'absolute', left: x0 + dx - 6, top: p.foot * K3 - 10, width: x1 - x0 + 12, height: 20, borderRadius: '50%', background: 'radial-gradient(ellipse, rgba(20,14,8,0.45), rgba(20,14,8,0) 70%)' }} />
            <Img src={staticFile(p.file)} style={{ position: 'absolute', left: x0 + dx, top: y0, width: x1 - x0, height: y1 - y0 }} />
          </div>
        );
        return (
          <React.Fragment key={i}>
            {i === 0 ? <Img src={staticFile('fix2/open/T1s_her.png')} style={{ position: 'absolute', left: hx0, top: hy0, width: hx1 - hx0, height: hy1 - hy0 }} /> : null}
            {at.moving ? <MBlur n={4} shutter={0.5} render={(dt) => { const a2 = parcelAt(i, f + dt); return a2 ? one(a2.dx, a2.op) : null; }} /> : one(at.dx, at.op)}
          </React.Fragment>
        );
      })}
      <Img src={staticFile('first30/T1_jamb.png')} style={{ position: 'absolute', left: 1526 * K3, top: 1450 * K3, width: 72 * K3, height: 880 * K3 }} />
    </Cam>
  );
};
const c916 = (x: number, cx: number, s: number) => { const c = clamp(cx, 1280 / s, 2560 - 1280 / s); return clamp((1280 + (x - c) * s) / 2560, 0.16, 0.84); };
const S1D_T1S: ShotDef = {
  stage: StageT1s,
  cx916: (f, shot) => { const k = 0.7 * inOutSine(clamp(f / (shot.dur - 1))) + 0.3 * clamp(f / (shot.dur - 1)); const hb = (t1s as any).her_box; return c916(((hb[0] + hb[2]) / 2) * K3 - 120, lerp(1280, 1330, k), lerp(1.0, 1.06, k)); },
};
export const S1_1D: ShotDef = (t1s as any).ready ? S1D_T1S : existsT1 ? { stage: StageT1, cx916: () => 0.34 } : { stage: Stage, cx916: () => 0.33 };
