// 3A "Retry, retry, retry after": low at her side of the door. The brass buzzer's ivory button goes in on each stressed "try"
// (the lamp above it blinks), with him right there behind the glass; on the third press the camera tips down to the doormat:
// RETRY-AFTER: 6h (baked into the still). No hand (S22b not rendered).
// PLATE: rl_cut1 a1 = S22 D3 (3840x3840 = stage 2560x2560: buzzer upper left, mat lower right) + button RGBA + lamp_on_region.
// rl_fix2_herrig (Nov 16; the watch: "no hand is visible, so nothing happens on Retry"): HER finger now. Two plates from her rig at the same
// camera (build/stills/F2H_3A): d3_up (her right index drawn back 12 mm, the button out) / d3_press (her index tip ON the button, the button
// 3 mm in): a pose cut on each stressed "try", held while the press holds. Her arm, sleeve and watch come in from the left edge. The code
// button is gone (the press is in the render); the lamp layer is the pressed render's own lamp_on region.
import React from 'react';
import { useCurrentFrame } from 'remotion';
import { lerp } from '../../ease';
import { ShotDef, ShotProps } from '../types';
import { Cam, ez, hit, MBlur, Vignette } from './_lib';
import { A1, Lay, clampCam, c916f } from './_cut1a';

const K = 2560 / 3840;                                   // D3 px -> stage
const PH = 3840 * K;                                     // plate height in stage px (2560)
const BTN = { x: 611 * K, y: 309 * K, w: 155 * K, h: 150 * K, cx: 689.3 * K, cy: 385.1 * K };   // layout.button (box, centre)
const LAMP = { x: 617 * K, y: 176 * K, w: 126 * K, h: 122 * K };                                   // layout.lamp box (lamp_on_region)
const WORDS = { x: 3095 * K, y: 3449 * K };                                                        // layout.doormat.words_box centre
// camera: start on the buzzer, him behind the glass at the right edge (s 1.45), end on the mat words (s 1.6, clamped to the plate corner)
// rl_fix2_end (the watch: "the robot is cut by the right edge"): starts wider (1.2x, x 0..2133) so he stands whole behind the glass
// next to the buzzer; the tilt to the mat is unchanged.
// rl_fix2_herrig (her GO list: "robot stays inside frame"): at 1.2x his right side was still cut; it starts at 1.0x (the plate's full width:
// him whole across, the buzzer and her hand upper left), the tilt to the mat unchanged.
const cam = (t: number) => clampCam(lerp(1280, WORDS.x, t), lerp(720, WORDS.y, t), lerp(1.0, 1.6, t), 0, 2560, 0, PH);

const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame();
  const press = (shot.cues ?? []).filter((c) => c.word.startsWith('re-TRY')).map((c) => c.frame - shot.from);
  const p = Math.max(0, ...press.map((k) => { const d = f - k; return d < -2 ? 0 : d < 0 ? (d + 2) / 2 : d < 3 ? 1 : Math.max(0, 1 - (d - 3) / 4); }));
  const lamp = Math.max(0, ...press.map((k) => { const d = f - k; return d < 0 ? 0 : d < 4 ? 1 : Math.max(0, 1 - (d - 4) / 3); }));
  const tilt = ez(f, press[2] ?? 52, shot.dur + 2);                  // the tilt to the mat lands as the cut comes ("after" is on the cut)

  return (<>
    <MBlur n={tilt > 0.05 && tilt < 0.95 ? 5 : 1} shutter={0.5} render={(dt) => {
      const t2 = ez(f + dt, press[2] ?? 52, shot.dur + 2);
      const c = cam(t2); const s = c.s * (1 + 0.012 * f / shot.dur + Math.max(0, ...press.map((k) => hit(f, k, 0.01, 8))));
      const cc = clampCam(c.cx, c.cy, s, 0, 2560, 0, PH);
      return (
        <Cam cx={cc.cx} cy={cc.cy} s={s} free>
          <Lay src={p >= 0.5 ? 'fix2/herrig/d3_press.jpg' : 'fix2/herrig/d3_up.jpg'} x={0} y={0} w={2560} h={PH} />
          <Lay src="fix2/herrig/d3_lamp_on.jpg" x={LAMP.x} y={LAMP.y} w={LAMP.w} h={LAMP.h} style={{ opacity: lamp }} />
          {/* the lamp's light on the brass plate round it (screen), so the blink reads at phone size */}
          <div style={{ position: 'absolute', left: LAMP.x + LAMP.w / 2 - 110, top: LAMP.y + LAMP.h / 2 - 110, width: 220, height: 220, borderRadius: '50%', opacity: lamp, mixBlendMode: 'screen',
            background: 'radial-gradient(circle, rgba(255,170,90,0.95) 0%, rgba(255,120,60,0.4) 30%, rgba(255,100,40,0) 70%)' }} />
        </Cam>
      );
    }} />
    <Vignette k={0.35} />
  </>);
};
export const S3_3A: ShotDef = { stage: Stage, cx916: (f, shot) => {
  const t = ez(f, (shot.cues?.[2]?.frame ?? shot.from + 52) - shot.from, shot.dur + 2); const c = cam(t);
  return c916f(lerp(BTN.cx, WORDS.x, t), c.cx, c.s); } };
