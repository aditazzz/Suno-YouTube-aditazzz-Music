// 11D "Drink some water": the water thread's payoff (FIX4_PLAN §2d).
// rl_l4_props (cut 4, her note f5279: "His hand is coming through the table. I don't get this scene. He should look like he cares and
// feels bad for me"): (1) her side, low at the slot: the flap swings open and the brass tray slides out to her with THE glass (the fluted
// tumbler from 7H, clear water) and settles; (2) cut on the beat to the reveal, through the door glass from her side: he is kneeling at
// the slot, both hands at it (he has just pushed the tray through), brows up, a soft apologetic look, eyes on her. No desk in the way.
// Plates: L4_11D_D8 (S21s's camera and layers, THE glass on the tray, doormat RETRY-AFTER: 7m) and L4_11D_K (kneeling, clock 5:53).
import React from 'react';
import { useCurrentFrame } from 'remotion';
import { ShotDef, ShotProps } from '../types';
import { Cam } from '../first30/kit';
import { Lay, Pl, clamp, gl, lerp, pulse } from '../s10/_lib';
import { inOutSine, outCubic } from '../../ease';
import { L4IMG, L4LAY } from '../l4data';
import { NightLobby } from './_night';

const K = 2560 / 2880;
const LD = L4LAY['11D8'];
const PIV = { x: (LD.flap_pivot_px[0] as number) * K, y: (LD.flap_pivot_px[1] as number) * K };
const I = L4IMG;
const Insert: React.FC<{ f: number; tTray: number; g: number }> = ({ f, tTray, g }) => {
  const b1 = 2;
  // rl7_final (judge nit B51 f5273-5274, the glass popped onto the tray in one frame): the tray slides out over 16 frames and the glass
  // rises out of the slot with it (the reveal follows the tray's travel instead of finishing in 2 frames; no 1-frame fade-in)
  const tray = outCubic(clamp((f - tTray) / 16));
  const stopAt = tTray + 16; const settle = f > stopAt ? Math.exp(-(f - stopAt) / 4) * Math.cos((f - stopAt) * 1.5) : 0;
  const over = f >= b1 + 2 ? 0.08 * Math.exp(-(f - b1 - 2) / 3) * Math.abs(Math.cos((f - b1 - 2) * 1.2)) : 0;
  const ts = lerp(0.8, 1, tray) * (1 + 0.006 * settle);
  const fb = LD.flap_box as number[];
  const clipTop = lerp(fb[1] * K + 20, 0, clamp(tray * 1.25));        // inside the slot the glass is still behind the door
  const k = inOutSine(clamp(f / 24));
  return (
    <Cam cx={1290} cy={lerp(640, 620, k)} s={lerp(1.03, 1.07, k) * pulse(g)}>
      <Pl src={I.D11_D8.src} />
      {f >= b1 ? <Lay src={I.D11_open_region.src} k={K} x={I.D11_open_region.x} y={I.D11_open_region.y} w={I.D11_open_region.w} h={I.D11_open_region.h} style={{ opacity: f < b1 + 2 ? 0.5 : 1 }} /> : null}
      {f >= b1 && f < b1 + 2 ? (
        <div style={{ position: 'absolute', inset: 0, transformOrigin: `${PIV.x}px ${PIV.y}px`, transform: 'scaleY(0.5)', filter: 'blur(2px)', opacity: 0.7 }}>
          <Lay src={I.D11_flap_shut.src} k={K} x={I.D11_flap_shut.x} y={I.D11_flap_shut.y} w={I.D11_flap_shut.w} h={I.D11_flap_shut.h} />
        </div>
      ) : null}
      {over > 0.002 ? (
        <div style={{ position: 'absolute', inset: 0, transformOrigin: `${PIV.x}px ${PIV.y}px`, transform: `scaleY(${1 + over})` }}>
          <Lay src={I.D11_flap_open.src} k={K} x={I.D11_flap_open.x} y={I.D11_flap_open.y} w={I.D11_flap_open.w} h={I.D11_flap_open.h} />
        </div>
      ) : null}
      {tray > 0 ? (
        <div style={{ position: 'absolute', inset: 0, clipPath: `inset(${clipTop}px 0 0 0)` }}>
          <div style={{ position: 'absolute', inset: 0, transformOrigin: `${PIV.x}px ${PIV.y}px`, transform: `scale(${ts.toFixed(5)})`, opacity: clamp(tray * 6) }}>
            <Lay src={I.D11_tray.src} k={K} x={I.D11_tray.x} y={I.D11_tray.y} w={I.D11_tray.w} h={I.D11_tray.h} />
          </div>
        </div>
      ) : null}
      {/* rl_master_fix: the lobby stays at 11C's night-light level; the pool on him and the slot */}
      <NightLobby cx={1290} cy={760} r={1250} />
    </Cam>
  );
};
const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame(); const g = shot.from + f;
  const b2 = gl(shot, 1, 17);
  const cut = Math.max(18, b2 + 6);                                     // the reveal: on the beat after the tray lands
  if (f < cut) return <Insert f={f} tTray={4} g={g} />;
  const k = inOutSine(clamp((f - cut) / Math.max(1, shot.dur - cut - 1)));
  const hp = L4LAY['11D'].head_px as number[];
  return (
    <Cam cx={lerp(1280, hp[0] * K, 0.25 + 0.15 * k)} cy={lerp(720, hp[1] * K, 0.3 + 0.15 * k)} s={lerp(1.04, 1.10, k) * pulse(g)}>
      <Pl src={I.D11_K.src} />
      {/* rl_master_fix: the lobby stays at 11C's night-light level; the pool on him (head at L4LAY 11D head_px, body below it) */}
      <NightLobby cx={hp[0] * K} cy={hp[1] * K + 260} r={1150} />
    </Cam>
  );
};
export const S11_11D: ShotDef = { stage: Stage, cx916: () => 0.5 };
