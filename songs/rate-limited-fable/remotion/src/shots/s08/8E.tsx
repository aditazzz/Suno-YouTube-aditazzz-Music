// rl_l3_ui (cut 4, #20 "Wall clock should be looking like a Rolex panda"): the panda clock on both pictures (4:37 on the glass side, matching
// "Read 4:37 AM"; 4:38 in the master), the digital box gone.
// 8E "You gave me everything / Now you give me nothing": everyone frozen staring at the glass is the joke: no pulse,
// nothing else moves. On the glass (her side) "You up?", Read 4:37 AM, then his typing dots; on "nothing" the dots go out
// (rl_screens glass_8E, keyed to the measured "nothing").
// rl_cut1 B (Nov 15): S11 H1_8E swapped in (the master: her at the parcel stake-out desk, arms folded, Cooper sitting, the
// cat on the vacuum, all staring at the door; him at his desk beyond it). In this camera the door glass is EDGE-ON
// (layout 8E door_glass_box is 15 px wide), so the receipt cannot sit on it. Chosen: three beats in one shot, cut on the
// grid: the master (the stare, on "You gave me everything") -> the glass from her side (S7 D1 + the
// glass layer, the dots typing then dying on "nothing") -> back to the master, still frozen, staring at nothing.
import React from 'react';
import { AbsoluteFill, Img, staticFile, useCurrentFrame } from 'remotion';
import { clamp, inOutSine, lerp } from '../../ease';
import { ShotDef, ShotProps } from '../types';
import { ScreenInsert } from '../../blocks/ScreenInsert';
import { E8_CLOCK, LobbyPanda, WallPanda, pt } from '../../blocks/PandaClock';
import { Cam, D1_GLASS, Grain, PlateImg, seqSrc } from '../s07/_lib';

// rl_fix2_end (Nov 16; the watch: "She reuses the arms-crossed stand from 4F ... Lean in on the typing dots"): the order is
// turned round. It OPENS on the glass from her side (S7 D1 + glass_8E: "You up?", Read 4:37 AM), and as his dots start typing
// (4005) the camera leans in on them, closer and closer, until they die on "nothing" (4040-4047) and we sit on the dead glass.
// Then the cut to the master: everyone frozen, staring at the door (H1_8E with the neon now reading Lie Down), a slow push.
const CUT_OUT = 4047;                                    // the dots are gone: cut to the master
const gp = (ox: number, oy: number): [number, number] => {                        // glass_8E px (1360x1620) -> stage px
  const [a, b] = [D1_GLASS[0], D1_GLASS[2]]; return [a[0] + (ox / 1360) * (b[0] - a[0]), a[1] + (oy / 1620) * (b[1] - a[1])];
};
const DOTS = gp(334, 800), CHAT = gp(640, 610);          // the dots bubble; the chat's middle (bubble + receipt + dots)
// rl_cut4_fix (rl_watch4 8E: the bubble + receipt slid off the top right on the lean): the 16:9 lean lands on LEAN, biased to the dots but
// keeping "You up?" + "Read 4:37 AM" >= 9% inside the frame at 2.05x (content box stage 903..1659 x 501..879).
const LEAN: [number, number] = [1265, 760];          // measured on the render: receipt right edge 0.98 W at 1160 -> ~0.89 W
const MASTER = 'fix2/end/h1_8e_liedown.jpg';
const BUB_DX = -270, BUB_DY = -25;                   // rl_cut4c_fix: glass px
const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame(); const g = shot.from + f;
  if (g < CUT_OUT) {
    const lean = inOutSine(clamp((g - 4003) / (4036 - 4003)));                       // from the first dot to just before "nothing"
    const settle = inOutSine(clamp((g - 3969) / 34));
    const s = lerp(lerp(1.04, 1.12, settle), 2.05, lean);
    const cx = lerp(lerp(1280, CHAT[0], settle), LEAN[0], lean), cy = lerp(lerp(740, CHAT[1], settle), LEAN[1], lean);
    return (
      <AbsoluteFill>
        <Cam cx={cx} cy={cy} s={s}>
          <PlateImg src="secb/D1.jpg" />
          <LobbyPanda time={pt(4, 37, 30 + f / 30)} chrono={(30 + f / 30) % 60} />
          {/* rl_cut4c_fix (rl_watch4b 8E: "You up?" covered the panda clock and "Read 4:37 AM" sat on its face): the glass layer split in two;
              the bubble + receipt band (glass rows 0-680; clock = glass x 972-1230, y 361-623) slides BUB_DX left off the clock, the dots stay */}
          <ScreenInsert corners={D1_GLASS} w={1360} h={1620}>
            <Img src={staticFile(seqSrc('glass_8E', g))} style={{ position: 'absolute', left: 0, top: 0, width: 1360, height: 1620, clipPath: 'inset(680px 0 0 0)' }} />
            <Img src={staticFile(seqSrc('glass_8E', g))} style={{ position: 'absolute', left: BUB_DX, top: BUB_DY, width: 1360, height: 1620, clipPath: 'inset(0 0 940px 0)' }} />
          </ScreenInsert>
        </Cam>
        <Grain g={g} />
      </AbsoluteFill>
    );
  }
  // the master: frozen, all staring at the door; one slow push
  const k = inOutSine(clamp((g - CUT_OUT) / (shot.from + shot.dur - 1 - CUT_OUT)));
  return (
    <AbsoluteFill>
      <Cam cx={lerp(1300, 1330, k)} cy={lerp(760, 775, k)} s={lerp(1.0, 1.05, k)}>
        <PlateImg src={MASTER} />
        {/* rl_l3_ui (#20): the gold clock with no hands -> the panda at 4:38, a size up so its hands read */}
        <WallPanda at={{ ...E8_CLOCK, r: 86 }} time={pt(4, 38, (g - CUT_OUT) / 30)} uid="e8" />
      </Cam>
      <Grain g={g} />
    </AbsoluteFill>
  );
};
// 9:16: on the chat, then the dots as we lean in; the master on the vacuum cat, her and Cooper
export const S8_8E: ShotDef = { stage: Stage, cx916: (f, shot) => {
  const g = shot.from + f; if (g >= CUT_OUT) return 0.6;
  const lean = inOutSine(clamp((g - 4003) / (4036 - 4003))); const settle = inOutSine(clamp((g - 3969) / 34));
  const s = lerp(lerp(1.04, 1.12, settle), 2.05, lean); const cx = lerp(lerp(1280, CHAT[0], settle), DOTS[0], lean);
  const x = lerp(CHAT[0], DOTS[0], lean); const c = clamp(cx, 1280 / s, 2560 - 1280 / s);
  return clamp((1280 + (x - c) * s) / 2560, 0.16, 0.84); } };
