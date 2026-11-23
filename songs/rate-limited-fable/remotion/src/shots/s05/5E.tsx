// 5E "You gave me everything": her laptop, the cat draped over the lid, the editor on screen (rl_screens laptop_5E:
// do_it_myself.py, the caret blinking on the four beats). On the last beat the lid slams shut (cut to the closed laptop; the cat
// has bolted: rl_fix3_a shows it leap out just before).
// PLATE (rl_cut1 a2): S21j T16 (laptop + cat over the lid; its tail is baked, hanging right of the screen) with the rl_screens
// editor pinned into screen_corners; the cat's paw that hangs in front of the screen is a cut-out on top (T16_paw).
// Lid close = cut T16 -> T16_closed on the last beat (+ a hit). 9:16: the editor sits at 0.8 inside the screen (the crop is
// narrower than the screen) on the editor's own background.
import React from 'react';
import { Img, staticFile, useCurrentFrame } from 'remotion';
import { lerp } from '../../ease';
import { ScreenInsert } from '../../blocks/ScreenInsert';
import { ShotDef, ShotProps } from '../types';
import { Cam, PlateImg, Seq, SCREENS, gb, hit, ez, c916 } from '../s03/_lib';
import { LAY, quadSt } from './_cut1b';
import { ClaudeCode, CodeState } from '../../blocks/real/ClaudeCode';

// rl_l3_ui (cut 4, R2 + her standing rule "a real Claude chat app or Claude Code terminal"): "Fine, I'll do it myself" = she opens
// Claude Code in a terminal (a big terminal font: the real thing, zoomed the way people zoom a terminal), types her request, hits
// Enter on beat 3, and gets the same limit the app gave her: "5-hour limit reached ∙ resets 6am". The terminal shares the limit;
// the cat bolts, the lid slams on beat 4 as before.
const REQ = "write do_it_myself.py. I'll take it from here";
const codeAt = (f: number, shot: any): CodeState => {
  const enter = gb(shot, 2) - 2;
  const n = Math.floor(Math.min(1, Math.max(0, (f - 2) / (enter - 6))) * REQ.length);
  if (f < enter) return { typed: REQ.slice(0, n), caret: f % 14 < 9 || n < REQ.length };
  return { typed: REQ, sent: true, limit: Math.min(1, Math.max(0, (f - enter - 3) / 8)), caret: f % 14 < 9 };
};

const [A, B] = SCREENS.laptop_5E;
// rl_fix2_end (Nov 16; the watch: "the cat on the laptop is huge, its body past the lid into empty air ... the editor text can't
// be read"): new plates F2_T16 (the same camera; the cat at 0.75 resting ON the lid edge, no tail; the cat as its own RGBA layer
// drawn over the code editor, so its paw hangs in front of the screen). The editor is zoomed 1.9x inside the screen (the
// explorer, the do_it_myself.py tab and line 1 with the caret: the assistant panel is off the right, the point is she is on her
// own) and the camera pushes from the cat + laptop (1.25x) to the tab (2.1x) over the four beats; the lid shuts on beat 4.
const SC = quadSt(LAY.T16.screen_corners);
const K = 2560 / 2880;
const CAT = { x: 509 * K, y: 0, w: (2225 - 509) * K, h: 1463 * K };   // rl_l1_roll C3: F2_T16 layout cat_box [509, 0, 2225, 1463] (L4's one cat, tail included)          // F2_T16 layout cat_box
const ZOOM = 1.9;
// rl_l3_term (Nov 17, her screenshot of real Claude Code in Terminal: "the exact reference for every Claude Code terminal"): the
// light macOS Terminal window fills the laptop screen, laid out at the screen's own aspect (TW x TH, 16:10 like the quad, so the
// type isn't stretched) at MacBook scale (ui = TW / 1512 pt), the font zoomed to 70 px (39 px at 1920 wide when the limit line lands, 43 px at the slam).
// All 17 rows fit after Enter, so nothing scrolls: the mascot and the header stay whole when the limit line arrives.
const TW = 2560, TH = Math.round(2560 * (((SC[2][1] - SC[1][1]) + (SC[3][1] - SC[0][1])) / 2) / (((SC[1][0] - SC[0][0]) + (SC[2][0] - SC[3][0])) / 2));
const TLIGHT = 0.86;   // a white window: a touch under the old dark editor's 0.94 so it sits in the room's night exposure
/** a point of the screen (u, v in 0..1 of the editor's visible region) on the stage, bilinear in the quad */
const onScreen = (u: number, v: number) => {
  const top = [SC[0][0] + (SC[1][0] - SC[0][0]) * u, SC[0][1] + (SC[1][1] - SC[0][1]) * u], bot = [SC[3][0] + (SC[2][0] - SC[3][0]) * u, SC[3][1] + (SC[2][1] - SC[3][1]) * u];
  return { x: top[0] + (bot[0] - top[0]) * v, y: top[1] + (bot[1] - top[1]) * v };
};
const MID = onScreen(0.5, 0.45), TAB = onScreen(0.42, 0.66);  // the screen's middle; the prompt box + the limit lines
const shut = (shot: any) => gb(shot, 3) + 2;
const camAt = (f: number, shot: any) => { const k = ez(f, 0, shut(shot) - 1); return { s: lerp(1.25, 2.1, k), cx: lerp(MID.x, TAB.x, k), cy: lerp(MID.y - 150, TAB.y, k) }; };
// rl_fix3_a (Nov 16; the watch of cut 2: "at the slam the cut lands on the shut laptop with no cat on or near it. It reads as the
// cat vanishing"): the cat BOLTS. Four frames before the lid shuts it squashes down onto the lid (anticipation), then springs
// straight up out of frame (accelerating, a two-copy smear trail), so by the cut it is already gone: we saw it leave.
// At 2.1x on the tab its body and hanging paw are in the top of frame, so the leap reads at phone size in both formats.
// The shut laptop: 1.45x (was 1.3x), bottom-clamped, so it is bigger in frame (the plate ends just under it).
const BOLT = 4;                                                          // frames before the shut
const catDy = (d: number) => (d < 1 ? 0 : -[0, 0, 70, 290, 640, 1100][Math.min(5, Math.floor(d) + 1)]);
const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame(); const g = shot.from + f; const closed = f >= shut(shot);
  const d = f - (shut(shot) - BOLT);
  // on the slam: a cut out to the closed laptop on the table (1.45x on its hinge), with the hit
  const c = closed ? { s: 1.45, cx: 1451.5 * K, cy: 1100 } : camAt(f, shot); const s = c.s * (1 + hit(f, shut(shot), 0.018, 8));
  return (
    <Cam cx={c.cx} cy={c.cy} s={s}>
      {closed ? <PlateImg src="fix2/end/t16_closed.jpg" /> : (
        <>
          {/* the plate has the cat baked in: from the frame it lifts off, the same plate with the cat taken out (rl_fix3_a
              make_t16_nocat.py: the sofa from the shut-lid twin render, the bezel filled from either side) */}
          <PlateImg src={d >= 1 ? 'fix3/a/t16_nocat.jpg' : 'fix2/end/t16.jpg'} />
          <ScreenInsert corners={SC} w={TW} h={TH} glare={0.05} light={TLIGHT}>
            <ClaudeCode w={TW} h={TH} fs={70} ui={TW / 1512} state={codeAt(f, shot)} />
          </ScreenInsert>
          {/* the smear trail: where it was one and two frames ago, fainter */}
          {d >= 2 ? [2, 1].map((back) => (
            <Img key={back} src={staticFile('fix2/end/t16_cat.png')} style={{ position: 'absolute', left: CAT.x, top: CAT.y + catDy(d - back), width: CAT.w, height: CAT.h, opacity: back === 1 ? 0.38 : 0.16 }} />
          )) : null}
          <Img src={staticFile('fix2/end/t16_cat.png')} style={{ position: 'absolute', left: CAT.x, top: CAT.y + catDy(d), width: CAT.w, height: CAT.h,
            transformOrigin: '50% 100%', transform: d >= 0 && d < 1 ? 'scale(1.03, 0.94)' : d >= 1 ? 'scale(0.97, 1.07)' : undefined }} />
        </>
      )}
    </Cam>
  );
};
export const S5_5E: ShotDef = { stage: Stage, cx916: (f, shot) => { if (f >= shut(shot)) return c916(1451.5 * K, 1451.5 * K, 1.45); const c = camAt(f, shot); return c916(lerp(MID.x, onScreen(0.45, 0.3).x, ez(f, 0, shut(shot) - 1)), c.cx, c.s); } };
