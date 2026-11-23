// The default for every shot nobody has authored yet: its plate with a simple eased move (animatic v0).
// With slate=true (the animatic render) it also shows the shot id + clock and, for shots that have no frame yet,
// a card with the set and the words on screen, so the cut reads as a plan.
import React from 'react';
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { Plate } from '../blocks/Plate';
import { ScreenInsert } from '../blocks/ScreenInsert';
import { TextBox, Reveal } from '../blocks/Type';
import { C, FONT } from '../theme';
import { ShotDef, ShotProps } from './types';

const short = (s: string, n: number) => (s.length > n ? s.slice(0, n - 1).trimEnd() + '…' : s);

/** a phone drawn in code, pinned with ScreenInsert: stand-in for screens rl_screens has not delivered yet */
const PhoneStandIn: React.FC<ShotProps> = ({ shot }) => {
  const lines = shot.words.split(/\s*·\s*/).filter(Boolean).slice(0, 5);
  return (
    <AbsoluteFill style={{ background: 'radial-gradient(ellipse at 50% 45%, #1b2230 0%, #07090d 70%)' }}>
      <ScreenInsert corners={[[1010, 150], [1560, 170], [1540, 1300], [1000, 1280]]} w={900} h={1900} radius={70}>
        <div style={{ position: 'absolute', inset: 0, background: '#0d1117', border: '14px solid #2a2f3a', borderRadius: 70, boxSizing: 'border-box' }} />
        {lines.map((l, i) => (
          <div key={i} style={{ position: 'absolute', left: 70, right: 70, top: 260 + i * 270, padding: '36px 44px', borderRadius: 44,
            background: i % 2 ? '#2b6cff' : '#262b36', color: '#fff', fontFamily: FONT.ui, fontWeight: 600, fontSize: 64, lineHeight: 1.15 }}>
            <Reveal text={short(l, 40)} start={6 + i * 10} len={6} />
          </div>
        ))}
      </ScreenInsert>
    </AbsoluteFill>
  );
};

const Stage: React.FC<ShotProps> = (p) => {
  const { shot } = p;
  if (!shot.plate) return <PhoneStandIn {...p} />;
  return <Plate src={`plates/${shot.plate}.jpg`} dur={shot.dur} move={shot.move} />;
};

const Screen: React.FC<ShotProps> = ({ shot, fmt, slate }) => {
  const f = useCurrentFrame();
  if (!slate) return null;
  const v = fmt === '16x9';
  const fade = Math.min(1, f / 4);
  const clock = shot.clock.replace(/\s+to\s+/i, '–');
  return (
    <AbsoluteFill style={{ opacity: fade }}>
      <TextBox x={v ? 48 : 98} y={v ? 40 : 262} w={v ? 820 : 620} h={86} size={34} kind="code" bg="rgba(0,0,0,0.62)" pad={20} color={C.paper}>
        {`${shot.id}  ${short(clock, v ? 26 : 18)}`}
      </TextBox>
      {shot.new ? (
        <TextBox x={v ? 48 : 98} y={v ? 1230 : 1080} w={v ? 1500 : 884} h={v ? 160 : 230} size={34} bg="rgba(0,0,0,0.62)" pad={22} color={C.paper} valign="top">
          {`NEW PICTURE · ${short(shot.set.split('.')[0], 34)}\n${short(shot.words, v ? 76 : 66)}`}
        </TextBox>
      ) : null}
    </AbsoluteFill>
  );
};

export const AnimaticShot: ShotDef = { stage: Stage, screen: Screen };
