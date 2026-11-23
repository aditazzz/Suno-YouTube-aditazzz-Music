// 8D (cut 5; plan §3: f3830-3969, 4.6 s; N39, OV): her phone at 4:37, the real app, the limit banner over the composer. Her queue
// for 6:00, one line per beat from 3830 (3830/3848/3865/3882/3900/3917), each line lit as it lands; all stay; two beats of hold on
// the full list (3934-3969). Lines in script.QUEUE (§6, incl. her N39 "MORE famous" and "CEO of SLOPCORP"). Chip Sonnet 5.5.
import React from 'react';
import { useCurrentFrame } from 'remotion';
import { ShotDef, ShotProps } from '../types';
import { CHIP, QUEUE } from '../../blocks/real/script';
import { MobileHome5 } from './AppField';
import { PhoneStage, clamp, loc } from './kit';

export const D8 = { BEATS: [3830, 3848, 3865, 3882, 3900, 3917] };
const TYPE = 9;                                                // each line types in over 9 frames, landing on its beat

export const Screen8D: React.FC<{ f: number; beats: number[] }> = ({ f, beats }) => {
  // line i types from beats[i] - TYPE to beats[i] (line 1 is there at the cut)
  let text = 'for 6:00'; const marks: { line: number; k: number }[] = [];
  let typing = false; let last = '';
  QUEUE.forEach((q, i) => {
    const b = beats[i]; const s0 = i === 0 ? b - 1 : b - TYPE;
    if (f < s0) return;
    const full = `${i + 1}. ${q}`; const n = f >= b ? full.length : Math.floor(clamp((f - s0) / (b - s0)) * full.length);
    text += '\n' + full.slice(0, n); if (n < full.length) typing = true; last = full.slice(0, n);
    // the line's tint: on at its beat, eases to a faint rest by the next beat (so the newest line always reads as new)
    const k = f >= b ? Math.max(0.0, 1 - clamp((f - b) / 16) * 0.85) : 0.35;
    marks.push({ line: i + 1, k });
  });
  const press = typing && last ? last.slice(-1).toLowerCase() : undefined;
  return <MobileHome5 hour={4} kbUpper={false} kbPress={press} sugg={['I', 'and', 'the']}
    field={{ text, caret: true, caretOn: typing || f % 16 < 9, banner: true, disabled: true, model: CHIP.night, maxLines: 12, marks }} />;
};

const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame();
  const beats = D8.BEATS.map((b) => loc(shot, b));
  // framed on the field: it grows upward as lines land, so the focus rises with it (eased, slow)
  return (
    <PhoneStage f={f} dur={shot.dur} k0={2.95} k1={3.05} focus0={392} focus1={330} time="4:37" seed={21} rot={1.0}>
      <Screen8D f={f} beats={beats} />
    </PhoneStage>
  );
};
export const C5_8D: ShotDef = { stage: Stage, cx916: () => 0.5 };
