// rl5_c: placeholder stagings for the in-plate screen layers, so the structure cut has them before B's K plate / A2's plates land.
// C5_2G / C5_5H / C5_8E: cut 4e's plates (2G/5H still show the old paddle: PLACEHOLDERS, B's K plate has none) with the new Claude-style glass bubbles (Glass.tsx). When B's K plate lands, D draws
// <GlassChat f={f} {...glassCues(id, shot.from)} right=.. top=.. size=.. /> over it (sizes: 2G/5H 92-100 px, receipt >= 44 px).
// Lab comps (preview only, not film shots): the TV, the notification, the meter digits, the date visor.
import { has } from '../c7/kit/trans';
import React from 'react';
import { AbsoluteFill, Img, staticFile, useCurrentFrame } from 'remotion';
import { ShotDef, ShotProps } from '../types';
import { Grain2, Vig } from '../../blocks/real/Scene';
import { ScreenInsert, Quad } from '../../blocks/ScreenInsert';
import { GlassChat, glassCues } from './Glass';
import { NewsTV, TVW, TVH } from './TV';
import { VacuumNotif, NOTIF } from './Notif';
import { MeterDigits } from './Meter8A';
import { VisorLines } from './Visor';
import { ez, lerp } from './kit';

const Push: React.FC<{ src: string; f: number; dur: number; s0: number; s1: number; cx?: number; cy?: number; children?: React.ReactNode }> = ({ src, f, dur, s0, s1, cx = 1280, cy = 720, children }) => {
  const s = lerp(s0, s1, ez(f, 0, dur - 1));
  return (
    <AbsoluteFill style={{ background: '#000', overflow: 'hidden' }}>
      <AbsoluteFill style={{ transformOrigin: `${cx}px ${cy}px`, transform: `scale(${s})` }}>
        <Img src={staticFile(src)} style={{ position: 'absolute', width: 2560, height: 1440 }} />
        {children}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const G2: React.FC<ShotProps> = ({ shot }) => { const f = useCurrentFrame();
  return <AbsoluteFill><Push src="fix2/open/C1.jpg" f={f} dur={shot.dur} s0={1.0} s1={1.03} /><GlassChat f={f} {...glassCues('2G', shot.from)} right={1200} top={170} size={100} /><Grain2 f={f} /></AbsoluteFill>; };
const H5: React.FC<ShotProps> = ({ shot }) => { const f = useCurrentFrame();
  return <AbsoluteFill><Push src="first30/C1.jpg" f={f} dur={shot.dur} s0={1.0} s1={1.04} /><GlassChat f={f} {...glassCues('5H', shot.from)} right={1700} top={260} size={92} /><Grain2 f={f} /></AbsoluteFill>; };
const E8: React.FC<ShotProps> = ({ shot }) => { const f = useCurrentFrame();
  return <AbsoluteFill><Push src={has('c7/11C/p2/D1_lit.jpg') ? 'c7/11C/p2/D1_lit.jpg' : 'secb/D1.jpg'} f={f} dur={shot.dur} s0={1.04} s1={1.1} />   {/* rl7_rb: rl7_p2's lit door plate, same camera (her H7.7 grey box out, gauge at its one spot, H7.30 tally plate gone) */}<GlassChat f={f} {...glassCues('8E', shot.from)} right={1600} top={150} size={72} left={880} /><Grain2 f={f} /></AbsoluteFill>; };
export const C5_2G: ShotDef = { stage: G2, cx916: () => 0.5 };
export const C5_5H: ShotDef = { stage: H5, cx916: () => 0.5 };
export const C5_8E: ShotDef = { stage: E8, cx916: () => 0.5 };

// ---- lab comps (preview only)
const TVQ: Quad = [[380, 220], [2180, 230], [2170, 1240], [390, 1230]];
const TVLab: React.FC<ShotProps> = ({ shot }) => { const f = useCurrentFrame();
  return <AbsoluteFill style={{ background: '#15100c' }}><ScreenInsert corners={TVQ} w={TVW} h={TVH} light={0.92}><NewsTV f={f} from={shot.from} /></ScreenInsert><Vig k={0.3} /></AbsoluteFill>; };
const NotifLab: React.FC<ShotProps> = ({ shot }) => { const f = useCurrentFrame();
  return <AbsoluteFill><Img src={staticFile('first30/C1.jpg')} style={{ position: 'absolute', width: 2560, height: 1440, filter: 'brightness(0.7)' }} /><VacuumNotif f={f} at={NOTIF.IN - shot.from} /></AbsoluteFill>; };
const MeterLab: React.FC<ShotProps> = ({ shot }) => { const f = useCurrentFrame();
  return <AbsoluteFill><Img src={staticFile('l5/8A/meter.jpg')} style={{ position: 'absolute', width: 2560, height: 1440 }} /><MeterDigits f={f} from={shot.from} /></AbsoluteFill>; };
const VQ: Quad = [[900, 500], [1660, 510], [1650, 760], [910, 750]];
const VisorLab: React.FC<ShotProps> = ({ shot }) => { const f = useCurrentFrame(); const b = [3414, 3431, 3449, 3466, 3483].map((F) => F - shot.from);
  return <AbsoluteFill style={{ background: '#101418' }}><div style={{ position: 'absolute', left: 880, top: 470, width: 800, height: 310, borderRadius: 120, background: '#05070a' }} /><VisorLines f={f} beats={b} quad={VQ} /></AbsoluteFill>; };
export const C5_LAB: Record<string, ShotDef> = { TV9A: { stage: TVLab }, TV9E1: { stage: TVLab }, N9E2: { stage: NotifLab }, M8A: { stage: MeterLab }, V7E1: { stage: VisorLab } };
export const C5_LAB_FRAMES: Record<string, [number, number]> = { TV9A: [4246, 4385], TV9E1: [4593, 4662], N9E2: [4662, 4732], M8A: [3761, 3830], V7E1: [3414, 3553] };
