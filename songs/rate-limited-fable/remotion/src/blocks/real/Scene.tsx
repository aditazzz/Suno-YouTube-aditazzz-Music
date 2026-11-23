// Shared staging for the real-interface shots: her room soft behind, the phone (or laptop screen) in front with a small
// handheld drift, the film's grain and vignette. Every value is a pure function of the frame.
import React from 'react';
import { AbsoluteFill, Img, staticFile } from 'remotion';
import { noise1 } from '../../ease';

export const ROOM = 'c7/apt/insert_room.jpg';   // rl7_master: rl7_apt_fin's locked-room backdrop;                // rl_l1_roll PATCH C1 (via rl_cut4_prep): the approved lifted room, no figure (her POV behind her own phone)
export const ROOM_ROUTINE = 'c7/apt/insert_room.jpg';

/** the soft background plate (stage size), defocused like a phone held close */
export const SoftPlate: React.FC<{ src?: string; blur?: number; dim?: number; s?: number; x?: number; y?: number }> = ({ src = ROOM, blur = 26, dim = 0.82, s = 1.12, x = 0, y = 0 }) => (
  <AbsoluteFill style={{ overflow: 'hidden', background: '#120d0a' }}>
    <Img src={staticFile(src)} style={{ position: 'absolute', left: 0, top: 0, width: 2560, height: 1440, transformOrigin: '50% 50%',
      transform: `translate(${x}px, ${y}px) scale(${s})`, filter: `blur(${blur}px) brightness(${dim}) saturate(1.05)` }} />
  </AbsoluteFill>
);

/** handheld drift (px, deg) for frame f: tiny, smooth, never a jitter */
export const hand = (f: number, amt = 1, seed = 3) => ({
  x: amt * 7 * noise1(f / 38, seed), y: amt * 6 * noise1(f / 41, seed + 7), r: amt * 0.35 * noise1(f / 47, seed + 13),
});

export const Grain2: React.FC<{ f: number; k?: number }> = ({ f, k = 0.045 }) => (
  <AbsoluteFill style={{ opacity: k, mixBlendMode: 'overlay', pointerEvents: 'none' }}>
    <svg width={2560} height={1440}><filter id={`rg${f % 5}`}><feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves={2} seed={f % 89} /></filter>
      <rect width={2560} height={1440} filter={`url(#rg${f % 5})`} /></svg>
  </AbsoluteFill>
);
export const Vig: React.FC<{ k?: number }> = ({ k = 0.42 }) => (
  <AbsoluteFill style={{ background: `radial-gradient(ellipse 78% 72% at 50% 48%, rgba(0,0,0,0) 55%, rgba(0,0,0,${k}) 100%)`, pointerEvents: 'none' }} />
);
/** the screen's light falling on the room/hand side of frame (a soft warm-white spill) */
export const Spill: React.FC<{ cx: number; cy: number; r: number; k?: number; color?: string }> = ({ cx, cy, r, k = 0.18, color = '255,248,236' }) => (
  <AbsoluteFill style={{ background: `radial-gradient(circle ${r}px at ${cx}px ${cy}px, rgba(${color},${k}) 0%, rgba(${color},0) 100%)`, mixBlendMode: 'screen', pointerEvents: 'none' }} />
);
