// 11E "I'll be here at six" (CODEPLAN keep*): the Rain door; a slow tilt up past him to the BACK AT 6:00 sign high on the
// glass and the cat on the ledge above; on beat 2 the glass of water now stands beside her (cut on the beat). The drum
// stops: no pulse. Plate: S10 D5 (rl_cut1 C): the approved Rain door at 2x with the headroom (5760x5376, approved window
// y 2136..5376 = the old 1440 stage); sign_back_at_6 RGBA hung on layout sign.hook_px (its alpha already holds out the
// cat's tail, so it only idles); glass_region at layout glass_region.
// rl_fix2_robot (WATCH: the tender beat reused 4E's 429-up pose): now D5_palm (blrl_fix2_robot mode 4, region render on the approved
// S10 scene): his palm flat on the glass at chest height, the paddle down at his side, his eyes on her. On beat 2 the plate cuts to
// D5_palm_glass (the same + the glass of water beside her, merged by a difference mask so the lowered paddle is never cut).
// Her skin: a soft warm pass on her (chat 18:16 note: "a touch pale/waxy beside the warm lobby"), feathered, low strength.
import React from 'react';
import { useCurrentFrame } from 'remotion';
import { ShotDef, ShotProps } from '../types';
import { Cam } from '../first30/kit';
import { Lay, PL, clamp, gl, lerp } from '../s10/_lib';
import { Img, staticFile } from 'remotion';
import { FX } from './_fix2';
import { inOutSine } from '../../ease';
import { BackAt6Sign } from '../../blocks/PandaClock';
import { L4IMG, L4LAY } from '../l4data';

// rl_l4_props (cut 4, her note f5389 "Cats tail looks weird ... doesn't match the start ... bushy and thick ... missing legs" + #30 / S22):
// the Rain door rebuilt (L4_11E: blrl_stills_s10's build, read only): THE cat (four legs, the bushy ringed tail of 1A) on the ledge; her in
// her LOVE hat and curls (rl_hat4's look); his palm flat on the glass at her eye level, the paddle out of his hands; the panda wall clock
// (5:57) where the digital box was; the lobby dimmed (S22, dim until 6:00). Beat 2: THE glass (the one from 7H / 11D) beside her.
// The hanging sign is L3's BackAt6Sign (one sign design, R7).

// rl_cut4 (one her): L4's plate with her body from rl_l1_roll's S10 D5 (the approved cozy knit; same scene, camera, pose, hat, hair),
// through a feathered difference matte kept off the dimmed lobby (workers/rl_cut4/fix11e.py). Was the old beige body under the new hat.
// rl_cut4_fix (rl_watch4 blocker: she was back in the grey sweater between the robe of 10B/11A and 12A; the matte left jagged streaks on her back):
// her region re-rendered on the CPU in the robe (+ slipper booties), same scene/camera/pose (workers/rl_cut4_fix/e11robe.py -> comp11e.py; seams
// 0.98 / 0.85 /255), and THE glass crop from the same render. His palm stays where L4 put it (flat on the glass, the paddle out of his hands; his
// arm tops out at chest height, so it can't reach her eye level): a faint breath-fog print round it on the glass makes the contact read.
// rl_cut4d_fix (cut 4d, her call 22:24 via the chat: "palm flat on the glass at her eye level, paddle out of his hand"; her 11D note: he should look like
// he cares and feels bad for her): his arm (.15 + .13 m from a shoulder at z .565) can't reach her eyes (z .85) from the floor, so he has stepped up to the
// glass on a lobby parcel box (15 cm): palm flat on the glass at her eye line (palm centre z .838, 2 mm off the glass), eye to eye, head turned to her,
// brows up in the middle. His region re-rendered on the CPU over cut 4c's plate (workers/rl_cut4d_fix/rl4d_11e.py -> comp11e_d.py; her robe unchanged);
// THE glass crop re-rendered with the box behind it. Was c4fix/D5_11e_robe.jpg + c4fix/11e_glass.jpg, palm fog at D5 (2700, 3560).
// rl_master_fix (master, the chat's call Nov 18 04:36: "11E palm in FRONT of her face on the glass (not beside his head, must not read as 'hi');
// 11C/11D/11E lobby light continuous"): one full CPU render of the plate (workers/rl_master_fix/rl4e_11e.py, same scene/camera/her robe):
// his RIGHT arm reaches across to her, palm flat on the glass in front of her face at her face height (2.0 mm off the glass; fingers flat,
// tilted toward her), still on the parcel box (feet 0.0 mm on it, box 0.0 mm on the floor); the lobby-side lights x .12 = 11C's night level
// (lobby wall 66 -> 49 luma; her side unchanged). Was c4dfix/D5_11e_palm.jpg + c4dfix/11e_glass.jpg, palm fog at D5 (2412, 3084).
const E11_SRC = 'c4efix/D5_11e_night.jpg';
const E11_GLASS = 'c4efix/11e_glass.jpg';
const PALM = { x: 3607 * (2560 / 5760), y: 3031 * (2560 / 5760), w: 300 * (2560 / 5760), h: 340 * (2560 / 5760) };   // his palm on the glass (D5 px -> stage)
const K = 2560 / 5760, PH = 5376 * K;                       // stage px per D5 px; plate height on the stage (2389)
const SIGN = { x: 2494, y: 1152, w: 939, h: 940 }, HOOK = { x: 2969.1, y: 1263.8 };
const HB = L4LAY['11E'].her_box as number[];
const HER = { x: HB[0], y: HB[1] + 430, w: 5760 - HB[0], h: 5376 - HB[1] - 430 };
const GL = L4IMG.E11_glass;
const GLASS_OK = true;
const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame(); const g = shot.from + f;
  const b2 = gl(shot, 1, 17);
  const k = inOutSine(clamp((f - b2 - 8) / (shot.dur - 1 - b2 - 8)));   // hold on her + the glass through beat 2, then the tilt up
  const sway = 0.5 * Math.sin(g / 19);
  return (
    <Cam cx={lerp(1282, 1300, k)} cy={lerp(1662, 700, k)} s={lerp(1.0, 1.22, k) * (1 + 0.012 * clamp(f / (b2 + 8)))} ph={PH}>{/* rl_cut4d_fix: opens wider (s 1.15 -> 1.0, cy 1763 -> 1662) so his whole head, now 15 cm higher on the box, is in frame with her and the glass */}{/* rl_cut4: a creep through the hold (26 dead-still frames) */}
      <Img src={staticFile(E11_SRC)} style={{ position: 'absolute', left: 0, top: 0, width: 2560, height: PH }} />
      {/* THE glass beside her: already there from frame 0 (11D just slid it through to her; no pop-in). GLASS_OK=false hides it. */}
      {GLASS_OK ? <Img src={staticFile(E11_GLASS)} style={{ position: 'absolute', left: GL.x * K, top: GL.y * K, width: GL.w * K, height: GL.h * K }} /> : null}
      {/* rl_cut4_fix: the fog print of his palm on the glass (her side), blooming over the first ~half second */}
      <div style={{ position: 'absolute', left: PALM.x - PALM.w * 0.8, top: PALM.y - PALM.h * 0.75, width: PALM.w * 1.6, height: PALM.h * 1.5, borderRadius: '50%',
        background: 'radial-gradient(ellipse 50% 50% at 50% 50%, rgba(214,220,226,0.24) 0%, rgba(214,220,226,0.15) 42%, rgba(214,220,226,0) 72%)',
        filter: 'blur(5px)', opacity: 0.35 + 0.65 * clamp(f / 14) }} />
      {/* her skin a touch warmer (her box, S10 layout her_box 3164..5760 x 2605..5376; face + hands sit in its upper left) */}
      <div style={{ position: 'absolute', left: HER.x * K, top: HER.y * K, width: HER.w * K, height: HER.h * K, background: 'rgb(255,150,95)', opacity: 0.10, mixBlendMode: 'soft-light',
        WebkitMaskImage: 'radial-gradient(ellipse 60% 55% at 35% 40%, #000 30%, transparent 100%)', maskImage: 'radial-gradient(ellipse 60% 55% at 35% 40%, #000 30%, transparent 100%)' }} />
      <BackAt6Sign x={HOOK.x * K} y={HOOK.y * K} w={SIGN.w * K * 0.86} swing={sway} light={0.9} uid="e11" />
    </Cam>
  );
};
// 9:16: both faces in (his ~0.50, hers ~0.62 of the output) while on them, then centred on the sign as it tilts up
export const S11_11E: ShotDef = { stage: Stage, cx916: (f, shot) => { const b2 = gl(shot, 1, 17); return lerp(0.54, 0.5, inOutSine(clamp((f - b2 - 8) / (shot.dur - 1 - b2 - 8)))); } };
