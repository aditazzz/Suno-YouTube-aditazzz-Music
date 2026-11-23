// 7H "I said, 'Don't talk about him like that'": the same chat; she sends it on the whoosh (120.73), Delivered; the drums stop.
// rl_fix2_read (Nov 16, WATCH 7H: "only the phone is in frame; the brief's beat ... is missing"): after the send, cut on the
// beat (121.89 s, f3657) to her view through the door glass: the full glass of water he keeps out on his desk, him soft behind
// it, a slow push; still and quiet (the drums have stopped). It sets up 13C (her mug lands beside this glass).
// PLATE: S21u T28a (cut1/c/T28a.jpg, T28's camera: her side of the door, 120 mm). His hand setting the glass down (blrl_fix2_read
// T28h) was rendered as a preview and his grip did not read; not used (see workers/rl_fix2_read/STATUS.md).
// Phone frames: rl_cutfix lifted room (unchanged).
import React from 'react';
import { AbsoluteFill, Img, staticFile, useCurrentFrame } from 'remotion';
import { clamp, inOutSine, lerp } from '../../ease';
import { ShotDef, ShotProps } from '../types';
import { seqSrc, Grain } from './_lib';
import { Cam } from '../first30/kit';
import { L4IMG } from '../l4data';

// rl_l4_props (cut 4, her note f3690 "The water looks muddy/blurry" + the water thread §2d): after the send, her view through the door
// glass: HIS HAND SETTING THE GLASS DOWN on the front of his desk (he's been worried about her all night), then the hand withdraws (a
// short dissolve to the same frame without it) and the glass holds, full, crisp and clear (THE glass: the fluted tumbler, clean water
// with a meniscus; a camera-invisible card behind it so the water reads bright, not muddy). It pays off in 11D (he slides it to her)
// and 13C (she drinks it first). Plates: L4_7H_T28 T28h (hand) / T28a (glass alone), same camera as S21u T28.

const CUT = 3657;                                   // the cut (beat 121.89 s)
const liftSrc = (id: string, g: number) => seqSrc(id, g).replace(`secb/${id}/`, `cutfix/screens/${id}_16x9/`).replace(/\.\w+$/, '.png');
const Glass: React.FC<{ g: number }> = ({ g }) => {
  const s = lerp(1.0, 1.045, inOutSine(clamp((g - CUT) / (3690 - CUT))));
  return (
    <Cam s={s} cx={1290} cy={760}>
      <Img src={staticFile(L4IMG.H7_T28h.src)} style={{ position: 'absolute', left: 0, top: 0, width: 2560, height: 1440 }} />
      <Img src={staticFile(L4IMG.H7_T28a.src)} style={{ position: 'absolute', left: 0, top: 0, width: 2560, height: 1440, opacity: inOutSine(clamp((g - CUT - 12) / 7)) }} />
      <Grain g={g} />
    </Cam>
  );
};
const Stage: React.FC<ShotProps> = ({ shot }) => {
  const g = shot.from + useCurrentFrame();
  if (g >= CUT) return <AbsoluteFill><Glass g={g} /></AbsoluteFill>;
  return <AbsoluteFill><Img src={staticFile(liftSrc('phone_7H', g))} style={{ position: 'absolute', left: 0, top: 0, width: 2560, height: 1440 }} /></AbsoluteFill>;
};
// 9:16: the phone's own 9:16 layer until the cut; then the glass plate reframed (cx916 on the glass)
const Screen: React.FC<ShotProps> = ({ shot, fmt }) => {
  const g = shot.from + useCurrentFrame();
  return fmt === '9x16' && g < CUT ? <Img src={staticFile(seqSrc('phone_7H_916', g))} style={{ position: 'absolute', left: 0, top: 0, width: 1080, height: 1920 }} /> : null;
};
export const S7_7H: ShotDef = { stage: Stage, screen: Screen, cx916: () => 0.5 };
