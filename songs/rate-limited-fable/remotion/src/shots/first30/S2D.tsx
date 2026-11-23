// 2D, 97% (first30.md): insert through the glass on his desk: her last parcel, half wrapped, string mid-knot, label
// FEATURE 41 · 97% (the 97% a crisp code layer in the label's blank window). rl7_ra: now MAKE ME FAMOUS · 97% (her H7.10). Beat 3: he lays the dust cloth over it.
// rl_fix2_open (WATCH: the code cloth popped in as a grey blob; 9:16 cut the card): now the rendered S9 T5 finals
// (TR_cam_S9, 85 mm): T5a his hands on the parcel -> beat 3 the cloth comes down (T5s, the drape smear, 2 frames) -> T5b
// covered by beat 4, a 1.2% settle as it lands; a slow push toward the label. 9:16 follows the label (whole in the crop).
// rl_fix3_qa1 (QA3: the shot ended on ~1.2 s of an out-of-focus white block): the covered plates (T5b) are soft renders of a
// plain cloth, and sharpening has nothing to recover, so the soft tail is shortened instead: the cloth now comes down on beat 4
// (was beat 3), which holds the FEATURE 41 / 97% label 0.6 s longer and leaves ~0.5 s of the covered parcel; after it lands the
// camera eases back (1.1 -> 1.02) so the covered parcel reads as an object on his desk between his hands, not a white blur.
import React from 'react';
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { clamp, inOutSine, lerp } from '../../ease';
import { ShotDef, ShotProps } from '../types';
import { TextBox } from '../../blocks/Type';
import { frameOf } from '../../timing';
import { Cam, PlateImg, Vignette, hit } from './kit';
import { GlassSheen } from './door';
import { FONT } from '../../theme';

const K9 = 2560 / 2880;
const WIN = [1716.7 * K9, 710.9 * K9, (1913.8 - 1716.7) * K9, (831.7 - 710.9) * K9];   // the label's blank % window, stage px
const LABEL_C: [number, number] = [1640 * K9, 790 * K9];                                // FEATURE 41 + the window, centre
const beats = (shot: ShotProps['shot']) => ({ b3: frameOf(shot.grid?.[2] ?? 29.263) - shot.from, b4: frameOf(shot.grid?.[3] ?? 29.842) - shot.from });
/** the frame the cloth comes down (beat 4) */
// rl_cut4_fix (rl_watch4 2D: still ended on the soft white cloth block): the drape smear takes the last 2 frames and the cut to 2E (the downbeat)
// lands mid-drape: the label holds to the end, no covered-parcel tail.
const clothF = (shot: ShotProps['shot']) => shot.dur - 2;
const camAt = (f: number, shot: ShotProps['shot']) => {
  const cl = clothF(shot);
  const push = lerp(1.0, 1.1, 0.7 * inOutSine(clamp(f / (shot.dur - 1))) + 0.3 * clamp(f / (shot.dur - 1)));
  const back = inOutSine(clamp((f - cl - 2) / Math.max(1, shot.dur - 1 - (cl + 2))));
  const s = lerp(push, 1.02, back) * (1 + hit(f, cl + 2, 0.012, 12));
  return { cx: LABEL_C[0], cy: LABEL_C[1] + 60, s };
};
const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame();
  const cl = clothF(shot);
  const plate = f < cl ? 'T5a' : f < cl + 2 ? 'T5s' : 'T5b';
  const { cx, cy, s } = camAt(f, shot);
  return (
    <AbsoluteFill>
      <Cam cx={cx} cy={cy} s={s}>
        <PlateImg src={`fix2/open/${plate}.jpg`} />
        {plate === 'T5a' ? <FamousLabel /> : null}
        {plate === 'T5a' ? (
          <TextBox x={WIN[0]} y={WIN[1]} w={WIN[2]} h={WIN[3]} size={60} kind="head" color="#1f2a2c" pad={6} align="center" lineHeight={1}
            style={{ filter: 'blur(0.5px)', opacity: 0.92, whiteSpace: 'nowrap' }}>97%</TextBox>
        ) : null}
      </Cam>
      <AbsoluteFill><GlassSheen pos={0.3} k={0.5} /></AbsoluteFill>
      <Vignette k={0.35} />
    </AbsoluteFill>
  );
};
// rl7_ra (her H7.10, cut 6 frame 879: "Shouldn't this be make me famous since that's the last thing she asked for? I think it's funnier
// than 41"): the label's raised FEATURE 41 is covered with the label's own paper (measured flat: rgb 195,183,169 across it) and the
// label reads MAKE ME / FAMOUS in the same condensed bold, raised (a soft cast shadow + a top-left rim light), tilted with the label.
const FamousLabel: React.FC = () => (
  <>
    <div style={{ position: 'absolute', left: 1296 * K9, top: 728 * K9, width: 300 * K9, height: 126 * K9, background: 'rgb(195,183,169)', filter: 'blur(1.2px)' }} />
    <div data-fit="box" style={{ position: 'absolute', left: 1262 * K9, top: 708 * K9, width: 432 * K9, height: 160 * K9, display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center', transform: 'rotate(-1.9deg)', fontFamily: FONT.brand, fontSize: 64 * K9, lineHeight: 1.0, color: 'rgb(78,76,74)',
      letterSpacing: '0.01em', textShadow: '2px 3px 3px rgba(40,30,20,0.45), -1px -1px 0 rgba(255,250,240,0.35)', filter: 'blur(0.45px)', whiteSpace: 'nowrap' }}>
      <div>MAKE ME</div><div>FAMOUS</div>
    </div>
  </>
);
const c916 = (x: number, cx: number, s: number) => { const c = clamp(cx, 1280 / s, 2560 - 1280 / s); return clamp((1280 + (x - c) * s) / 2560, 0.16, 0.84); };
export const S2_2D: ShotDef = { stage: Stage, cx916: (f, shot) => { const { cx, s } = camAt(f, shot); return c916(LABEL_C[0] - 30, cx, s); } };
