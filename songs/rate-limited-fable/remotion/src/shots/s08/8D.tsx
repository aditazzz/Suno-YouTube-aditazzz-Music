// 8D "Right in the middle of my grind" (cut 4, rl_l3_ui; her notes #17 + #18: "If this is meant to be the Claude app then it should
// look like it"; "These prompts could be funnier and ridiculous. A call back to can you make me famous? Can I win an Oscar"):
// the real Claude app on her phone at 4:37, the usage-limit banner over the composer ("resets 6:00 AM"), his last reply from
// before the limit above it. She keeps typing her queue for 6:00 into the composer, a line on each beat, the last one live;
// she taps send and it does nothing (greyed). Framed close on the banner + composer so every line reads at phone size.
import React from 'react';
import { AbsoluteFill, Img, staticFile, useCurrentFrame } from 'remotion';
import { ShotDef, ShotProps } from '../types';
import { clamp, inOutSine, lerp } from '../../ease';
import { seqSrc } from '../s07/_lib';
import { Phone } from '../../blocks/real/Phone';
import { MobileHome } from '../../blocks/real/MobileApp';
import { Grain2, SoftPlate, Spill, Vig, hand } from '../../blocks/real/Scene';

import { BEFORE, QUEUE } from '../../blocks/real/script';
export { BEFORE, QUEUE };
/** lines in the composer and how much of the last one is typed, for shot-local frame f */
const draft = (f: number) => {
  const shown = f < 10 ? 2 : f < 21 ? 3 : f < 32 ? 4 : 5;
  const live = QUEUE[5]; const n = Math.floor(clamp((f - 36) / 22) * live.length);
  const lines = QUEUE.slice(0, shown); if (f >= 36) lines.push(live.slice(0, n));
  return { text: 'for 6:00\n' + lines.map((l, i) => `${i + 1}. ${l}`).join('\n'), done: f >= 58 };
};

/** the key under her thumb: the character just typed, lit for 2 frames */
const pressAt = (f: number) => { const a = draft(f).text, b = draft(f - 2).text; return a.length === b.length + 1 || (a.length > b.length && a.startsWith(b) && a.length - b.length < 4) ? a.slice(-1).toLowerCase() : undefined; };

const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame();
  const d = draft(f);
  const tap = f >= 59 && f < 64 ? Math.sin(((f - 59) / 5) * Math.PI) : 0;
  const e = inOutSine(clamp(f / (shot.dur - 1)));
  // rl_l3_phone (her screenshot of her own app, Nov 17): her app's new-chat screen as on her phone, greeting for 4:37 AM ("Still up,
  // Adita?"), the limit banner, the keyboard up; the field grows to 4 lines and then scrolls like the real one (latest lines showing).
  const k = lerp(3.1, 3.3, e), focus = lerp(420, 428, e);
  const h = hand(f, 1, 21);
  return (
    <AbsoluteFill>
      <SoftPlate x={-h.x * 0.4} y={-h.y * 0.4} />
      <Spill cx={1280} cy={760} r={1500} k={0.12} />
      <Phone cx={1300 + h.x} cy={720 + (426 - focus) * k + h.y} w={393 * k} rot={1.0 + h.r} time="4:37" glare={0.06} silent>
        <MobileHome hour={4} kbUpper={false} sugg={['I', 'and', 'the']} kbPress={pressAt(f)}
          composer={{ text: d.text, caret: true, caretOn: !d.done || f % 16 < 9, banner: true, disabled: f >= 61, sendPressed: tap, maxLines: 4 }} />
      </Phone>
      <Vig k={0.38} />
      <Grain2 f={f} />
    </AbsoluteFill>
  );
};
// 9:16: the old notes layer stays until the vertical pass (vertical later)
const Screen: React.FC<ShotProps> = ({ shot, fmt }) => fmt === '9x16'
  ? <Img src={staticFile(seqSrc('phone_8D_916', shot.from + useCurrentFrame()))} style={{ position: 'absolute', left: 0, top: 0, width: 1080, height: 1920 }} /> : null;
export const S8_8D: ShotDef = { stage: Stage, screen: Screen, cx916: () => 0.5 };
