// 7A + 7B "Checked your status page like I'm checking your stories / All systems operational, so it's only me?"
// Cut 4 (rl_l3_ui; her notes #2, #8, #9, #10 and her standing rule: real interfaces): the status board is gone. Her phone, a photo
// app's stories in the layout everyone knows (no app logo or wordmark), his handle claude_nightsuper:
//  3136-3169  the story tray, pushing in on his ring: the robot is the profile photo; we linger on it, closer and closer (P06);
//             her thumb presses it on the beat before "stories".
//  3170-3239  his stories, one tap per beat: (1) karaoke in the lobby, (2) a group selfie with the little clay guests holding up
//             green ticks, (3) him handing another tenant a parcel with a bow (L4's three stills; placeholders until they land:
//             public/l3/stories/story{1,2,3}.jpg).
//  3240-3274  on "only me?": his DM. Her three messages sit on "Seen"; the camera tilts up to his name: Active now, the green dot.
// Status-bar time 4:24 (7A) per the timeline; the door shot with the 4:05 box is gone (#10).
import React from 'react';
import { AbsoluteFill, Img, staticFile, useCurrentFrame } from 'remotion';
import { clamp, inOutSine, lerp, outCubic } from '../../ease';
import { ShotDef, ShotProps } from '../types';
import { Phone } from '../../blocks/real/Phone';
import { DMView, StoryTray, StoryView } from '../../blocks/real/Stories';
import { Grain2, SoftPlate, Spill, Vig, hand } from '../../blocks/real/Scene';

const FROM = 3136, TAP = 3166, OPEN = 3170, S2 = 3205, S3 = 3223, DM = 3240, TO = 3275;
const fr = (g: number) => String(Math.round(clamp(g, OPEN, TO - 1))).padStart(5, '0');
const HANDLE = 'claude_nightsuper';
const RINGS = [
  { name: 'you', src: 'l3/av/her.jpg', you: true },
  { name: HANDLE, src: 'l3/av/robot.jpg' },
  { name: 'cooper.the.doodle', src: 'l3/av/cooper.jpg' },
  { name: 'jo.builds', src: 'l3/av/jo.jpg', seen: true },
  { name: 'the_other_model', src: 'l3/av/model.jpg', seen: true },
];
const RING_PT = { x: 10 + 90 + 38, y: 108 + 38 };            // his ring's centre on the screen (pt)
const STORIES = ['l3/stories/story1.jpg', 'l3/stories/story2.jpg', 'l3/stories/story3.jpg'];

/** phone placement: screen point (px, py) at stage (X, Y), k stage px per pt */
const place = (k: number, px: number, py: number, X = 1280, Y = 720) => ({ w: 393 * k, cx: X + (196.5 - px) * k, cy: Y + (426 - py) * k });

const Stage: React.FC<ShotProps> = ({ shot }) => {
  const g = shot.from + useCurrentFrame();
  const h = hand(g - FROM, 1, 41);
  let p: { w: number; cx: number; cy: number }; let screen: React.ReactNode; let time = '4:24';
  if (g < OPEN) {
    // the tray, then the slow push onto his photo (P06: linger on it, zoom in)
    const k = inOutSine(clamp((g - FROM) / (OPEN - FROM)));
    const press = g >= TAP ? Math.sin(clamp((g - TAP) / 5) * Math.PI) : 0;
    p = place(lerp(3.0, 6.2, k), lerp(196, RING_PT.x, k), lerp(200, RING_PT.y, k));
    screen = <StoryTray rings={RINGS} press={{ i: 1, k: press }} feed="l3/stories/story3.jpg" />;
  } else if (g < DM) {
    const idx = g < S2 ? 0 : g < S3 ? 1 : 2; const a = [OPEN, S2, S3][idx], b = [S2, S3, DM][idx];
    const at = idx + clamp((g - a) / (b - a));
    const open = outCubic(clamp((g - OPEN) / 7));
    // the story grows out of his ring: start close on the avatar spot, settle to the story's top two-thirds
    p = place(lerp(6.2, 2.62, open), lerp(RING_PT.x, 196, open), lerp(RING_PT.y, 330, open));
    const tapK = (g - a) < 3 && idx > 0 ? 1 - (g - a) / 3 : 0;
    screen = (
      <>
        <StoryView src={STORIES[idx]} handle={HANDLE} avatar="l3/av/robot.jpg" when={['2h', '1h', '12m'][idx]} bars={3} at={at} />
        {tapK > 0 ? <div style={{ position: 'absolute', left: 300, top: 420, width: 90, height: 90, borderRadius: 45, background: 'rgba(255,255,255,0.18)', opacity: tapK }} /> : null}
      </>
    );
  } else {
    // "only me?": the DM. Her messages on Seen, then the tilt up to Active now
    // rl_cut4_fix (rl_watch4 7B: the tilt ended on the header over ~0.8 s of empty white): a quicker tilt up to Active now, a short hold, then
    // it eases back out to the whole thread, so the shot ends on "Active now" + her three messages on Seen together.
    // rl_cut4c_fix (rl_watch4b 7B: the tilt still whipped past the bubbles to the empty white header, a near-white frame at 3252, then
    // bounced back): no tilt. The camera lands on her three messages on "Seen just now" and holds there with a slow creep to the cut.
    const k = inOutSine(clamp((g - DM) / (TO - 1 - DM)));
    p = place(lerp(3.5, 3.85, k), 196, lerp(700, 706, k));
    screen = <DMView handle={HANDLE} name={HANDLE} avatar="l3/av/robot.jpg" active mine={['you up?', 'saw your story', 'so you ARE up']} seen="Seen just now" />;
    time = '4:25';
  }
  return (
    <AbsoluteFill>
      <SoftPlate x={-h.x * 0.4} y={-h.y * 0.4} />
      <Spill cx={1280} cy={720} r={1500} k={0.12} />
      <Phone cx={p.cx + h.x} cy={p.cy + h.y} w={p.w} rot={h.r - 0.6} time={time} dark={g >= OPEN && g < DM} glare={0.05}>{screen}</Phone>
      <Vig k={0.36} />
      <Grain2 f={g} />
    </AbsoluteFill>
  );
};
// 9:16: the old stories layer stays until the vertical pass (vertical later)
const Screen: React.FC<ShotProps> = ({ shot, fmt }) => {
  const g = shot.from + useCurrentFrame();
  if (fmt !== '9x16' || g < OPEN) return null;
  return <Img src={staticFile(`fix3/qa2/stories/9x16/f_${fr(g)}.jpg`)} style={{ position: 'absolute', left: 0, top: 0, width: 1080, height: 1920 }} />;
};
export const S7_7A: ShotDef = { stage: Stage, screen: Screen, cx916: () => 0.5 };
export const S7_7B: ShotDef = { stage: Stage, screen: Screen, cx916: () => 0.5 };
