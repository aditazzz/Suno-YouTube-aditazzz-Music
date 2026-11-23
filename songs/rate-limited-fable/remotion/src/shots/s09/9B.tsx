// 9B "You said 'let me know if there's anything else'": his last slip held up over the routine (blurred), shaking with the
// plate (the 9A vibration at its last strength), still readable: LET ME KNOW IF THERE'S ANYTHING ELSE.
// rl_fix3_qa2 (Nov 16, QA3: in 9:16 the slip's words reached 77% height and the like column x > 0.80 while it rose in): 9:16 only,
// the slip sits higher and shorter (top 195, 540 tall: the words at ~19-46% height, wholly above the half line, so the like column
// is clear at any x) and rises 40 px instead of 260. 16:9 unchanged.
import React from 'react';
import { hasL2 } from '../l2kit';
import { L2P } from '../l2data';
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { clamp, lerp, outCubic } from '../../ease';
import { FONT } from '../../theme';
import { ShotDef, ShotProps } from '../types';
import { Grain, PlateImg, Vignette } from '../s07/_lib';
import { jit } from './9A';
import { Phone } from '../../blocks/real/Phone';
import { MobileChat } from '../../blocks/real/ClaudeChat';
import { BEFORE } from '../s08/8D';

export const Slip: React.FC<{ children: React.ReactNode; w?: number; h?: number }> = ({ children, w = 1180, h = 560 }) => (
  <div style={{ width: w, height: h, background: 'linear-gradient(180deg,#f6f1e4,#ece4d0)', borderRadius: 6, boxShadow: '0 30px 60px rgba(0,0,0,0.5), 0 3px 6px rgba(0,0,0,0.35)', position: 'relative' }}>
    <div style={{ position: 'absolute', left: 0, right: 0, top: 0, height: 18, background: 'repeating-linear-gradient(90deg, transparent 0 22px, rgba(0,0,0,0.08) 22px 24px)' }} />
    <div data-fit="box" style={{ position: 'absolute', left: 60, top: 60, width: w - 120, height: h - 120, display: 'flex', alignItems: 'center', justifyContent: 'center', textAlign: 'center',
      fontFamily: FONT.mono, fontWeight: 700, fontSize: 84, lineHeight: 1.15, color: '#1d1f24' }}>{children}</div>
  </div>
);

// rl_l3_ui (cut 4, R5 "His slip ... is a paper"; her standing rule: the real Claude app): her phone comes up into frame, still
// buzzing with the party (9A's vibration), on the real chat: his last reply before the limit (the same thread as 8D), ending
// "Let me know if there's anything else!". On beat 2 her thumb long-presses that sentence: the iOS text selection (blue wash,
// the two handles) sweeps across it, the words she is about to throw back at him (sets up 9C).
const LINE = "Let me know if there's anything else!";
const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame(); const g = shot.from + f;
  const [dx, dy] = jit(g, 2.3); const [bx, by] = jit(g + 50, 1.4);
  const rise = outCubic(clamp(f / 8));
  const sel = clamp((f - 20) / 14);
  const k = 3.55;
  return (
    <AbsoluteFill style={{ background: '#111' }}>
      <AbsoluteFill style={{ transform: `translate(${bx}px, ${by}px) scale(1.06)` }}>
        <PlateImg src={hasL2('9A', 'clean') ? L2P['9A'].clean! : 'l2/9A.jpg'} filter="blur(18px) brightness(0.62)" />{/* rl_cut4 (L2 PATCH C): her room from 9A's camera, without her (it is her own phone), was the old routine room */}
      </AbsoluteFill>
      <Phone cx={1290 + dx * 1.6} cy={720 + (426 - 560) * k + dy * 1.6 + (1 - rise) * 420} w={393 * k} rot={-2 + 0.25 * dx} time="4:41" glare={0.06} silent>
        <MobileChat title="make the font bigger" msgs={[BEFORE[0], { ...BEFORE[1], hl: { s: LINE, k: sel } }]} composer={{ banner: true }} />
      </Phone>
      <Vignette k={0.4} />
      <Grain g={g} />
    </AbsoluteFill>
  );
};
export const S9_9B: ShotDef = { stage: Stage, cx916: () => 0.5 };
