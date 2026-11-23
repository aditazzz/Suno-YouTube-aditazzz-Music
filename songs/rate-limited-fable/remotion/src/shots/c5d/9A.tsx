// rl5_d2 cut 5 9A (4246-4385) + the 9E1 wiring. rl5_a2's new camera (her N42 "Move the TV so we can see what's on it"): TV at frame RIGHT
// (A2's deviation: the sofa, his landing, is left), she and Cooper on the vibration plate, robe + collagen mask, arms crossed ("I'm not
// mad"). Layers: 9A_clean (no plate) + rl5_c's NewsTV on A2's tv_quad + 9A_fg (her + Cooper + the plate: they buzz together) + 9A_hair
// (lagged). Flat-on, slow push. 9E1: c5d/9E1.tsx make9E1 on A2's c5/9E1 layers, same camera, the TV continuing.
import React from 'react';
import { AbsoluteFill, Img, staticFile, useCurrentFrame } from 'remotion';
import { ShotDef, ShotProps } from '../types';
import { Cam } from '../first30/kit';
import { lerp } from '../../ease';
import { ioc } from './legacy';
import { Grain2 } from '../../blocks/real/Scene';
import { ScreenInsert, Quad } from '../../blocks/ScreenInsert';
import { NewsTV, TVW, TVH } from '../c5/TV';
import { make9E1, L9fromA2, GuestsFrom } from './9E1';
import LA from '../../../public/c5/9A/layout.json';
import LE from '../../../public/c5/9E1/layout.json';

const full: React.CSSProperties = { position: 'absolute', left: 0, top: 0, width: 2560, height: 1440 };
const jig = (g: number, amp: number, lag = 0) => { const ph = 2 * Math.PI * 13.5 * (g / 30) - lag; return [amp * 0.35 * Math.sin(ph * 0.5 + 1.1), amp * Math.sin(ph)]; };
const Buzz: React.FC<{ g: number; amp: number; lag?: number; src: string }> = ({ g, amp, lag = 0, src }) => (
  <>{Array.from({ length: 5 }, (_, i) => { const [dx, dy] = jig(g + (i / 4 - 0.5) * 0.5, amp, lag);
    return <Img key={i} src={staticFile(src)} style={{ ...full, opacity: 1 / (i + 1), transform: `translate(${dx.toFixed(2)}px, ${dy.toFixed(2)}px)` }} />; })}</>
);
const TvA = (q: Quad, from: number): React.FC<{ f: number }> => ({ f }) => (
  <ScreenInsert corners={q} w={TVW} h={TVH} light={0.92}><NewsTV f={f} from={from} /></ScreenInsert>);

export const CAM9 = { cx: 1280, cy: 720 };
// cut 6 (rl6_her, FRAMES blocker 6): ONE pose for the whole shot (arms folded, "I'm not mad", eyes to us), new robe, new camera shared with
// rl6_her's 9E1. Base = c6/9A/9A.jpg (every contact shadow: feet on the plate, plate on the floor), then the buzzing fg + lagged hair on top.
// The plate's TV already shows the approved Outlook headline lit in the room: no NewsTV overlay (rl6_her's call, agreed). The plate still
// goes up a notch on each "I'm not mad" (cues 4288, 4329): buzz amplitude only, no pose change (the squat cut at 4329 is gone).
const Stage9A: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame(); const g = shot.from + f; const s = lerp(1.0, 1.03, ioc(f, 0, shot.dur - 1));
  const amp = g >= 4329 ? 3.4 : g >= 4288 ? 2.8 : 2.3;
  return (
    <AbsoluteFill>
      <Cam cx={CAM9.cx} cy={CAM9.cy} s={s}>
        <Img src={staticFile('c7/9A/9A.jpg')} style={full} />   {/* rl7_fixb: tube-family neon baked in */}
        <Buzz g={g} amp={amp} src="c7/9A/9A_fg.png" />
        <Buzz g={g} amp={amp * 1.4} lag={1.3} src="c7/9A/9A_hair.png" />
      </Cam>
      <Grain2 f={f} />
    </AbsoluteFill>
  );
};
export const C5_9A: ShotDef = { stage: Stage9A, cx916: () => 0.5 };

const L9 = L9fromA2(LE);
const base9E1 = make9E1({ dir: 'c5/9E1/', cam: { ...CAM9, s: 1.03 }, L: L9, hair: true, Guests: GuestsFrom(LE),
  Tv: ({ f }) => { const T = TvA(L9.tv_quad as Quad, 4593); return <T f={f} />; } });
export const C5_9E1: ShotDef = { ...base9E1, stage: (p) => { const S = base9E1.stage; const f = useCurrentFrame(); return <AbsoluteFill><S {...p} /><Grain2 f={f} /></AbsoluteFill>; } };

// cut 6 (rl6_edit2), READY BUT NOT WIRED until rl6_her marks 9E1 LANDED: rl6_her's 9E1 is real animation, every frame rendered (69 frames,
// master 4593 + r, 2880x1620, one locked camera = 9A's): Cooper launched on 4610, streamers + confetti out of the TV, lands on the sofa.
// Wire: in c5d/index.tsx replace `'9E1': C5_9E1` with `'9E1': C6_9E1` (check the folder/name pattern against rl6_her's PATCH.md first).
export const C6_9E1_DIR = 'c7/9E1/';   // rl7_master: rl7_hero2 PATCH s2   // rl7_fixb: c6/9E1's 69 frames with the tube-family neon baked in (job_9e1.py)
const Stage9E1c6: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame(); const r = Math.min(shot.dur - 1, Math.max(0, f));
  return (
    <AbsoluteFill>
      <Cam cx={CAM9.cx} cy={CAM9.cy} s={1.0}>
        <Img src={staticFile(`${C6_9E1_DIR}f_${String(r).padStart(4, '0')}.jpg`)} style={full} />
      </Cam>
      <Grain2 f={f} />
    </AbsoluteFill>
  );
};
export const C6_9E1: ShotDef = { stage: Stage9E1c6, cx916: () => 0.5 };
