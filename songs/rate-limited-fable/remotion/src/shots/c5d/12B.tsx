// rl5_d2 cut 5 12B (5458-5597): CUT5_PLAN §3 "Yoga, four poses, two beats each, Cooper and the vacuum copying; the neon changes with each
// pose; the last frames flicker to the next line. Child's pose seen from the head side." One slow lateral drift across all four (her N49:
// the sign cycles the lines, one per pose). rl5_a1's c2 plates (bodysuit): w2 (Make Slop) 5458 -> tree (Be Famous) 5493 -> baby (Click Click
// Ship It) 5528 -> child (Click Click Ship It; Ban 429 at 5580) 5562; beats from shots.json (two each).
// No comp'd panda clock (cut 4e drew LobbyPanda on w2/tree; §2e "no comp'd clocks anywhere").
// 12B_child: A1's new head-side framing puts the neon half out of the plate's top edge, so its frame is pushed in (s 1.09, cy 775) to keep
// the cut-off sign out: its Ban 429 change is then not seen in 12B (12D opens on Ban 429).
// Flicker (A1's sign Regions, c3 chain): REGIONS below; each pose's last 6 frames alternate dark / next line, 2 frames each.
import { has } from '../c7/kit/trans';
import React from 'react';
import { AbsoluteFill, Img, staticFile, useCurrentFrame } from 'remotion';
import { ShotDef, ShotProps } from '../types';
import { Cam } from '../first30/kit';
import { lerp } from '../../ease';
import { ioc } from './legacy';
import { Grain2 } from '../../blocks/real/Scene';

const POSES = [
  { id: '12B_w2', at: 5458, s: 1.04, cy: 720 },
  { id: '12B_tree', at: 5493, s: 1.04, cy: 720 },
  { id: '12B_baby', at: 5528, s: 1.04, cy: 720 },
  { id: '12B_child', at: 5562, s: 1.09, cy: 775 },
];
// sign Regions (full-frame JPGs with only the sign box re-rendered): [next line, dark] per pose; empty until A1's c3 lands
// rl5_d5: A1's c4 Regions landed 18:11-18:21 (full 2880 frames; only the sign + its light spill differ, mean 0.5/255 elsewhere).
// baby -> child keep Click Click Ship It (no change); child's Ban 429 is framed out (top edge) but kept for completeness.
// rl7_master: rl7_apt_fin's locked-room full-plate states (sign A baked): SLOP -> FAMOUS -> CLICK -> CLICK -> BAN; [next line, dark] per pose
export const BASE12B: Record<string, string> = { '12B_w2': 'c7/apt/12B_w2_slop.jpg', '12B_tree': 'c7/apt/12B_tree_famous.jpg', '12B_baby': 'c7/apt/12B_baby_click.jpg', '12B_child': 'c7/apt/12B_child_click.jpg' };
export const REGIONS: Record<string, [string, string] | undefined> = {
  '12B_w2': ['c7/apt/12B_w2_famous.jpg', 'c7/apt/12B_w2_slop_dead.jpg'],
  '12B_tree': ['c7/apt/12B_tree_click.jpg', 'c7/apt/12B_tree_famous_dead.jpg'],
  '12B_child': ['c7/apt/12B_child_ban.jpg', 'c7/apt/12B_child_ban_dead.jpg'],
};
void has;
const FLICK = 6; void FLICK;

const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame(); const g = shot.from + f;
  let i = 0; while (i + 1 < POSES.length && g >= POSES[i + 1].at) i++;
  const P = POSES[i]; const end = i + 1 < POSES.length ? POSES[i + 1].at : shot.from + shot.dur;
  const reg = REGIONS[P.id]; const d = end - g;                       // frames left in this pose
  // rl7_rb (her P10 "smoother not glitchy"): ONE clean change per pose instead of the dark/next/dark stutter: the tube dims out over 2 frames,
  // holds dark 1, and strikes the next line on the last frame before the cut (the next pose's plate carries it lit)
  const lay: [string, number][] = !reg || d > 4 ? [] : d === 4 ? [[reg[1], 0.5]] : d >= 2 ? [[reg[1], 1]] : [[reg[1], 1], [reg[0], 0.75]];
  const cx = lerp(1235, 1325, ioc(f, 0, shot.dur - 1));                 // the one lateral drift (clamped per pose by Cam)
  return (
    <AbsoluteFill>
      <Cam cx={cx} cy={P.cy} s={P.s}>
        <Img src={staticFile(BASE12B[P.id])} style={{ position: 'absolute', left: 0, top: 0, width: 2560, height: 1440 }} />
        {lay.map(([src, op], i) => <Img key={i} src={staticFile(src)} style={{ position: 'absolute', left: 0, top: 0, width: 2560, height: 1440, opacity: op }} />)}
      </Cam>
      <Grain2 f={f} />
    </AbsoluteFill>
  );
};
export const C5_12B: ShotDef = { stage: Stage, cx916: () => 0.45 };
