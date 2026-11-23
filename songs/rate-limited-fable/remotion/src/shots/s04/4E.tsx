// 4E "Typed 'please' into the box / Like you'd feel it if I begged" (cut 4, rl_l3_ui; S25 "4E tiny notes"; her standing rule: the
// real Claude app). "The box" is the real Claude input: on her phone, the same chat as 8D/9B (his last reply from before the limit,
// the usage-limit banner over the composer). On "please" she types it; it grows to `pleaseeee 🙏 I'll tip $200`; she taps send and
// nothing goes (the button is greyed, the composer gives a small no-shake). Hard cut on the beat to her begging face, then the
// pull out lands on the approved DOOR framing exactly on "begged" (1816), as before.
// HER FACE: L1's plate when it lands (BEG below; see workers/rl_l3_ui/PATCH.md). Until then the slot is the approved door plate
// pushed in on her profile (d5_4e), the same plate the pull lands on.
import React from 'react';
import { C4_BEG } from '../c4sign';
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { clamp, lerp, inOutCubic, inOutSine } from '../../ease';
import { cueFrame } from '../../timing';
import { ShotDef, ShotProps } from '../types';
import { Cam, MBlur } from '../s03/_lib';
import { Lay } from '../s03/_cut1a';
import { Phone } from '../../blocks/real/Phone';
import { MobileHome } from '../../blocks/real/MobileApp';
import { Grain2, SoftPlate, Spill, Vig, hand } from '../../blocks/real/Scene';

/** L1's begging close of her (stage-size plate, her face at FACE). null = the placeholder push on the door plate. */
// rl_cut4 (L3 PATCH D): her begging close, rendered by blrl4_c4sign (lane L2's door stage: the approved her in the cozy knit at his door,
// 2:36, hands pressed together under her chin, brows up, pleading through the glass past his head). Face = head_px x 2560/2880.
export const BEG: { src: string; face: [number, number] } | null = C4_BEG ? { src: 'c4/4E_beg.jpg', face: [1213, 539] } : null;
const FACE: [number, number] = [1810, 560];                 // rl_cut4_fix: her face on the new door plate (stage px)
// rl_cut4_fix (rl_watch4 blocker): the pull-back plate = rl_l1_roll's S10 D5 (the approved her: cozy knit, LOVE hat, loose curls; same scene +
// camera) at d5_4e's window, the note out (workers/rl_cut4_fix/fix4e_plate.py). The old d5_4e had her old jacket/jeans/ponytail.
const D5E_HER = 'c4fix/d5_4e_her.jpg';
const TXT = [[0, ''], [12, 'p'], [14, 'pl'], [15, 'ple'], [17, 'plea'], [18, 'pleas'], [20, 'please'], [26, 'pleasee'], [27, 'pleaseee'], [28, 'pleaseeee'],
  [31, 'pleaseeee 🙏']] as [number, string][];
const TIP = " I'll tip $200";
/** the iOS keyboard's suggestion bar for what is being typed (the word in progress, then the emoji row) */
const suggAt = (t: string): [string, string, string] => t.endsWith('🙏') ? ['🙏', '😭', '🥺'] : t.includes('tip') ? ['$200', 'and', 'if'] : t ? [`“${t}”`, 'please', 'pleased'] : ['I', 'The', 'I’m'];
/** the key under her thumb: the character just typed, lit for 2 frames */
const pressAt = (f: number) => { const a = typedAt(f), b = typedAt(f - 2); return a !== b && a.length > b.length ? a.slice(-1).toLowerCase() : undefined; };
const typedAt = (f: number): string => {
  let t = ''; for (const [a, s] of TXT) if (f >= a) t = s;
  if (f >= 36) t += TIP.slice(0, Math.floor(clamp((f - 36) / 14) * TIP.length));
  return t;
};

const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame();
  const bg = cueFrame(shot, 'begged') ?? 104;
  const CUT = 64;                                             // beat 4 of the bar (grid 58.80 s)
  if (f < CUT) {
    const h = hand(f, 1, 17);
    const send = 54; const tap = f >= send && f < send + 5 ? Math.sin(((f - send) / 5) * Math.PI) : 0;
    const shake = f >= send + 2 && f < send + 12 ? 9 * Math.sin((f - send - 2) * 1.9) * (1 - (f - send - 2) / 10) : 0;
    // rl_l3_phone (her screenshot of her own app, Nov 17): "the box" is her app's new-chat screen as on her phone: the spark, the
    // greeting for 2:36 AM ("Up late, Adita?"), the limit banner over the composer, the keyboard up. Framed on greeting + composer.
    const k = lerp(3.3, 3.5, inOutSine(clamp(f / CUT)));
    return (
      <AbsoluteFill>
        <SoftPlate x={-h.x * 0.4} y={-h.y * 0.4} />
        <Spill cx={1280} cy={760} r={1500} k={0.12} />
        <Phone cx={1290 + h.x + shake} cy={720 + (426 - 408) * k + h.y} w={393 * k} rot={-1.2 + h.r} time="2:36" glare={0.06} silent>
          <MobileHome hour={2} kbPress={pressAt(f)} sugg={suggAt(typedAt(f))}
            composer={{ text: typedAt(f), caret: true, caretOn: f % 16 < 10 || f < send, banner: true, disabled: f >= send + 1, sendPressed: tap }} />
        </Phone>
        <Vig k={0.38} />
        <Grain2 f={f} />
      </AbsoluteFill>
    );
  }
  // her face, then the pull out to the approved door frame on "begged"
  const P0 = 80;
  const pull = clamp((f - P0) / (bg - P0));
  const face = FACE;                                          // rl_cut4: the pull-out always starts on her on the door plate (BEG is its own frame)
  const cam = (t: number) => { const k = inOutCubic(clamp((t - P0) / (bg - P0))); return { cx: lerp(face[0] - 60, 1280, k), cy: lerp(face[1] + 40, 720, k), s: lerp(2.35 + 0.08 * clamp((t - CUT) / (P0 - CUT)), 1.0, k) }; };
  if (BEG && f < P0) return <Cam cx={BEG.face[0]} cy={BEG.face[1]} s={1.0 + 0.04 * clamp((f - CUT) / (P0 - CUT))}><Lay src={BEG.src} x={0} y={0} w={2560} h={1440} /></Cam>;
  return (
    <MBlur n={pull > 0.04 && pull < 0.96 ? 4 : 1} shutter={0.5} render={(dt) => {
      const c = cam(f + dt);
      return (
        <Cam cx={c.cx} cy={c.cy} s={c.s} creep={(f - bg) / (shot.dur - bg)}>
          <Lay src={D5E_HER} x={0} y={0} w={2560} h={1440} />
        </Cam>
      );
    }} />
  );
};
export const S4_4E: ShotDef = { stage: Stage, cx916: () => 0.5 };
