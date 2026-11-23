// 9F "Usage limit reached": hard cut, dead still, silence. Him behind the glass with his hands folded, the engraved USAGE LIMIT
// REACHED plate (S7 D7) above his head. One streamer drifts down past the glass. No pulse, no move.
// rl_fix2_read (Nov 16, WATCH 9F: the plate was ~6 px of text at phone size): the hard cut lands CLOSER and holds dead still:
// the plate fills the top third (16:9 s 2.9: the plate ~1290 px wide, its words ~50 px at 1920; 9:16 s 1.75, plate inside the crop).
import React from 'react';
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { ShotDef, ShotProps } from '../types';
import { Cam, Grain, PlateImg } from '../s07/_lib';
import { clamp, inOutSine } from '../../ease';
import { LimitBanner } from '../../blocks/real/ClaudeChat';

const Drift: React.FC<{ f: number }> = ({ f }) => {
  const y = -260 + f * 13, x = 1060 + 40 * Math.sin(f / 9), r = 8 * Math.sin(f / 13);
  const pts = Array.from({ length: 16 }, (_, i) => `${18 * Math.sin(i * 0.9 + f / 6)},${i * 16}`).join(' ');
  return (
    <svg style={{ position: 'absolute', left: x, top: y, overflow: 'visible', transform: `rotate(${r}deg)`, filter: 'blur(1.6px)' }} width={60} height={260}>
      <polyline points={pts} fill="none" stroke="#ff6fa5" strokeWidth={13} strokeLinecap="round" />
    </svg>
  );
};

// rl_l3_ui (cut 4, R4 "USAGE LIMIT REACHED on the glass is a sign"; her standing rule: real Claude interface): the engraved plate
// is framed OUT (it sits above his head at stage y 577-661: the hold now frames his face and folded hands, y 661-1157), and on
// "Usage" the real Claude limit banner lights up on the glass between us, holds one beat, then goes quiet (fades out); the rest is
// him, dead still, and the streamer. The lobby clock is out of frame here.
const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame(); const g = shot.from + f;
  const on = clamp(f / 3), quiet = 1 - inOutSine(clamp((f - 19) / 14));
  const a = on * quiet;
  return (
    <AbsoluteFill>
      <Cam cx={1280} cy={912} s={2.9}>
        <PlateImg src="secb/D7.jpg" />
      </Cam>
      {/* the banner on the glass: the app's own banner (same words as 8D), a soft screen-glow on the glass */}
      <div style={{ position: 'absolute', left: 1280, top: 905, transform: `translate(-50%, -50%) scale(${(4.4 * (0.985 + 0.015 * on)).toFixed(4)})`, opacity: a }}>
        <div style={{ position: 'absolute', inset: -14, borderRadius: 26, background: 'rgba(255,248,236,0.35)', filter: 'blur(14px)' }} />
        <LimitBanner style={{ margin: 0, marginBottom: 0, borderRadius: 14, border: '0.5px solid rgba(31,30,29,0.2)', padding: '14px 18px', background: 'rgba(240,238,230,0.94)',
          boxShadow: '0 6px 24px rgba(0,0,0,0.25)' }} />
      </div>
      <AbsoluteFill style={{ background: 'linear-gradient(115deg, rgba(255,255,255,0) 35%, rgba(255,255,255,0.05) 48%, rgba(255,255,255,0) 60%)' }} />
      {/* the streamer drifts down the glass in front, in frame space (unscaled: it is on the glass, near the lens) */}
      <Drift f={f} />
      <Grain g={g} />
    </AbsoluteFill>
  );
};
export const S9_9F: ShotDef = { stage: Stage, cx916: () => 0.5 };
