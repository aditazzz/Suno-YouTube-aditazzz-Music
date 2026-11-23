// 4E phone input (cut 5; plan §3: 4E f1712-1851, the phone 1712-1764; N16-N19): cut 4e's "the box" kept (her app's new chat at
// 2:36, she types "pleaseeee 🙏 I'll tip $200", taps send, nothing goes), the chip now Sonnet 5.5. Then (A2's plates, wired by D):
// the pull out of the phone to her face, begging A -> on "begged" (1816) begging B with Cooper. No robot.
//   <Phone4E f={f} />  local frames 0..52 of 4E (the phone part); P4E.END = where the phone part ends (local).
// C5_4E (for the structure cut) = the phone part, then cut 4e's door plate pushing in on her (placeholder until A2's faces land).
import React from 'react';
import { AbsoluteFill, Img, staticFile, useCurrentFrame } from 'remotion';
import { ShotDef, ShotProps } from '../types';
import { MobileHome5 } from './AppField';
import { BEG, CHIP } from '../../blocks/real/script';
import { PhoneStage, clamp, ez, lerp } from './kit';

export const P4E = { END: 52, SEND: 42 };   // local: the phone part ends on beat 1764 (52); send tapped at 42
const TXT = [[0, ''], [6, 'p'], [8, 'pl'], [9, 'ple'], [11, 'plea'], [12, 'pleas'], [14, 'please'], [18, 'pleasee'], [19, 'pleaseee'], [20, 'pleaseeee'], [23, 'pleaseeee 🙏']] as [number, string][];
const TIP = BEG.slice('pleaseeee 🙏'.length);
const typedAt = (f: number) => { let t = ''; for (const [a, s] of TXT) if (f >= a) t = s; if (f >= 26) t += TIP.slice(0, Math.floor(clamp((f - 26) / 12) * TIP.length)); return t; };
const suggAt = (t: string): [string, string, string] => t.endsWith('🙏') ? ['🙏', '😭', '🥺'] : t.includes('tip') ? ['$200', 'and', 'if'] : t ? [`“${t}”`, 'please', 'pleased'] : ['I', 'The', 'I’m'];

export const Phone4E: React.FC<{ f: number }> = ({ f }) => {
  const t = typedAt(f), b = typedAt(f - 2);
  const press = t !== b && t.length > b.length ? t.slice(-1).toLowerCase() : undefined;
  const send = P4E.SEND; const tap = f >= send && f < send + 5 ? Math.sin(((f - send) / 5) * Math.PI) : 0;
  const shake = f >= send + 2 && f < send + 10 ? 9 * Math.sin((f - send - 2) * 1.9) * (1 - (f - send - 2) / 8) : 0;
  return (
    <PhoneStage f={f} dur={P4E.END} k0={3.3} k1={3.45} focus0={408} focus1={408} time="2:36" seed={17} rot={-1.2} cx={1290 + shake}>
      <MobileHome5 hour={2} kbPress={press} sugg={suggAt(t)}
        field={{ text: t, caret: true, caretOn: f % 16 < 10 || f < send, banner: true, disabled: f >= send + 1, sendPressed: tap, model: CHIP.night }} />
    </PhoneStage>
  );
};

const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame();
  if (f < P4E.END) return <Phone4E f={f} />;
  // placeholder for the structure cut: cut 4e's door plate (her at the glass), a slow push on her face (A2's begging A/B replace this)
  const k = ez(f, P4E.END, shot.dur - 1);
  const s = lerp(2.4, 2.5, k), cx = 1880, cy = 600;     // on her only (the old plate's paddle stays out of frame)
  return (
    <AbsoluteFill style={{ background: '#000' }}>
      <Img src={staticFile('c4fix/d5_4e_her.jpg')} style={{ position: 'absolute', width: 2560, height: 1440, transformOrigin: `${cx}px ${cy}px`, transform: `translate(${1280 - cx}px, ${720 - cy}px) scale(${s})` }} />
    </AbsoluteFill>
  );
};
export const C5_4E: ShotDef = { stage: Stage, cx916: () => 0.5 };
