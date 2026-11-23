// rl5_d cut 5 13E = cut 4e 13E with rl5_c's Laptop13E5 ("make me MORE famous" -> "I can help you with a strategy.", her N50).
// 13E the tag after the song (CODEPLAN fork 1, BOARDS 1077): he stamps her slip (callback to 1F), the dust cloth comes
// off the parcel (T5 reversed), then we pull back out through the door glass: it is her laptop screen, in her room in the
// morning, the cat draped over the lid with a paw hanging over the screen. Her first prompt, "Make the font bigger.",
// types into the composer (rl_screens laptop_13E overlay, keyed to master frames); the cat flops (pose cut); the lid
// comes down (A-smear-B) and we hold on the closed laptop.
// Plates (rl_cut1 C): S19 T29a (open + cat over the lid) -> T29f (cat flopped) -> T29s (lid smear) -> T29c (lid shut, the cat
// gone to the sofa arm). The screen = layout screen_corners (a perspective quad, rotated ~-2.4 deg: the camera counter-
// rotates while it fills the frame); the paw over the screen is the plate's own pixels (paw_T29a/f, masked inside the
// quad), drawn over the screen insert. No end card (no copy beyond the code). The song ends at 6357: 13E is silent.
import React from 'react';
import { AbsoluteFill, Img, staticFile, useCurrentFrame } from 'remotion';
import { FONT } from '../../theme';
import { ScreenInsert, Quad } from '../../blocks/ScreenInsert';
import { ShotDef, ShotProps } from '../types';
import { Cam, hit, swap } from '../first30/kit';
import { PL, Pl, clamp, lerp } from '../s10/_lib';
import { inCubic, inOutCubic, inOutSine, outCubic } from '../../ease';
import { L2E } from '../l2data';
import { LAPTOP } from '../../blocks/real/Dropins';
import { Laptop13E5 as Laptop13E } from '../c5/Laptop13E5';

const K = 2560 / 2880;
// cut 4 (lane L2): her NEW room and L4's one cat (four legs, the bushy tail): plates + quads from blrl4_act_13e via l2data (L2E), else the cut-3 ones
const NEW = !!(L2E.T29a && L2E.screen_corners);
export const T29_SCREEN = (NEW ? L2E.screen_corners : ([[1082.2, 552.4], [1693.6, 532.1], [1713.3, 903.4], [1102.7, 940.3]] as [number, number][]).map(([x, y]) => [x * K, y * K])) as Quad;
const T29_C = { x: T29_SCREEN.reduce((m, p) => m + p[0], 0) / 4, y: T29_SCREEN.reduce((m, p) => m + p[1], 0) / 4 };          // the quad's centre on the stage
// rl_cut4 (director: frame the laptop with bezel + room, the screen dimmed to the room light): the pull starts with the screen at 80% of
// the frame width (its bezel and her room round it), not filling the frame; the app is zoomed in (2.4x) so the type reads there.
const S_FILL = NEW ? 0.80 * 2560 / Math.hypot(T29_SCREEN[1][0] - T29_SCREEN[0][0], T29_SCREEN[1][1] - T29_SCREEN[0][1]) : 5.0;
const R_FILL = NEW ? -Math.atan2(T29_SCREEN[1][1] - T29_SCREEN[0][1], T29_SCREEN[1][0] - T29_SCREEN[0][0]) * 180 / Math.PI : 2.4;                          // the screen's D1 picture fills the frame, levelled
// rl_fix2_end (Nov 16; the watch: "8.1 s of digital silence ... the cat overhangs into empty air beyond the lid, and it is gone at
// f6597. There's no end card on the lid. In 9:16 the Make the... box runs off the right edge"): new plates F2_T29 (same camera):
// the cat at 0.75 resting ON the lid edge (its own RGBA layer over the screen insert: no paw cut-out), and THE FLOP TAKES THE
// LID DOWN: T29f (flopped) -> T29s (the lid coming down with the cat riding it, smear) -> T29c (lid shut, the cat asleep ON it,
// a sticker on the lid's front). Then a cut to F2_T29e, top-down on the closed lid: the cat asleep, the sticker = the end card
// (RATE / LIMITED in her brand colours, aditazzz), held 2.6 s with a slow push. Sound: build/fix2/end/tail_audio.wav (room tone,
// the stamp, the cloth, the typing, a purr, the flop, the lid click) muxed instead of the WAV; keyed to T13 below.
// 9:16: the overlay (the composer) is drawn at 0.42 inside the screen so "Make the font bigger." stays inside the crop.
// rl_fix3_qa2 (Nov 16, QA3 + rl_watch2: the 9:16 end card spanned 53-75% height and 5-93% width, the cat's head out of the crop):
// the sticker is baked low on the T29e plate and the cat's head sits 1035 stage px from it, more than the 810 px crop, so 9:16 only:
// the hold opens on the cat asleep (head in the crop, the sticker's words still out of it), then pans and pushes onto the sticker
// (s 1.36, the frame at the plate's bottom) so RATE / LIMITED / aditazzz reads above the 70% line, inside the side margins, for the
// last 1.3 s. The brand layout of the card is unchanged. 16:9 unchanged.
const bx = (b: number[] | undefined, d: { x: number; y: number; w: number; h: number }) => (b ? { x: b[0], y: b[1], w: b[2] - b[0], h: b[3] - b[1] } : d);
const CAT_A = bx(NEW ? L2E.cat_a_box : undefined, { x: 1022 * K, y: 253 * K, w: (1738 - 1022) * K, h: (704 - 253) * K }), CAT_F = bx(NEW ? L2E.cat_f_box : undefined, { x: 1025 * K, y: 262 * K, w: (1749 - 1025) * K, h: (734 - 262) * K });
const STK_C = (NEW && L2E.sticker_c ? L2E.sticker_c : ([[1322.2, 1021.7], [1627.9, 1005.9], [1660.1, 1047.9], [1339.1, 1065.3]] as [number, number][]).map(([x, y]) => [x * K, y * K])) as Quad;
const STK_E = (NEW && L2E.sticker ? L2E.sticker : ([[1097.5, 951.5], [1801.0, 984.1], [1798.6, 1283.8], [1065.6, 1248.3]] as [number, number][]).map(([x, y]) => [x * K, y * K])) as Quad;
const STK_EC = { x: STK_E.reduce((m, p) => m + p[0], 0) / 4, y: STK_E.reduce((m, p) => m + p[1], 0) / 4 };
export const T13 = { flop: 138, lidS: 146, lidC: 148, top: 163 };
const FX = NEW ? 'l2/13E/' : 'fix2/end/';

// 9:16 end hold (rl_fix3_qa2): on the cat's head until HEAD916, the pan/push lands at LAND916 (shot frames)
const HEAD916 = 172, LAND916 = 200, S_END916 = 1.36, CAT_HEAD_X = 655;    // the cat's head centre (T29e, stage x)
const end916 = (f: number, dur: number) => {
  const k = inOutSine(clamp((f - HEAD916) / (LAND916 - HEAD916)));
  const s = lerp(1.0, S_END916, k) * lerp(1, 1.015, inOutSine(clamp((f - LAND916) / (dur - 1 - LAND916))));
  return { cx: lerp(1280, STK_EC.x, k), cy: lerp(720, 1440, k), s, k };   // Cam clamps cy to the plate: the frame sits on its bottom
};
// rl6_edit (FRAMES blocker 13: the answer finished typing at ~6463 after the pull had begun, readable ~6 frames): the reply now streams from
// the cut (start 0, 45 chars/s: done by ~6445) and the close framing holds to pullA 120 (6478); the pull is shorter (18 frames) and arrives
// on the flop (138 = 6496). T13 (flop/lid) stays where the tail sound effects are keyed (build/fix2/end/make_tail_audio.py).
export const T = { stamp: 14, cloth: 46, door: 66, pullA: 120, pullB: 138, lidA: 146, lidB: 148 };
const SCR = { x: 660, y: 250, w: 1240, h: 775 };        // the laptop screen on the stage at the end of the pull-back
const PARCEL = { x0: 740, y0: 384, x1: 1866, y1: 1147 }; // S9 desk_parcel box on the stage

/** the end card: a dark sticker on the lid, the two-line Anton headline (last line in her accent green) + aditazzz */
const STK_W = 1350, STK_H = 620;
export const EndCard: React.FC = () => (
  <div style={{ position: 'absolute', inset: 0, borderRadius: 34, background: 'linear-gradient(160deg,#1c1c1f,#121214)', boxShadow: 'inset 0 0 0 10px rgba(255,255,255,0.05)' }}>
    <div data-fit="box" style={{ position: 'absolute', left: 70, right: 70, top: 46, bottom: 46, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ fontFamily: FONT.brand, fontSize: 196, lineHeight: 0.98, color: 'rgb(236,230,216)', letterSpacing: '0.01em' }}>RATE</div>
      <div style={{ fontFamily: FONT.brand, fontSize: 196, lineHeight: 0.98, color: 'rgb(116,227,106)', letterSpacing: '0.01em' }}>LIMITED</div>
      <div style={{ fontFamily: FONT.ui, fontWeight: 600, fontSize: 96, marginTop: 14, color: 'rgba(236,230,216,0.78)' }}>aditazzz</div>
    </div>
  </div>
);

// the code cloth (pre-finals stand-in; no longer drawn: the S9 T5 finals carry the real cloth)
export const Cloth: React.FC<{ f: number }> = ({ f }) => {
  const k = clamp((f - T.cloth) / 12); if (k >= 1) return null;
  const e = inCubic(k); const w = PARCEL.x1 - PARCEL.x0 + 160, h = PARCEL.y1 - PARCEL.y0 + 120;
  return (
    <div style={{ position: 'absolute', left: PARCEL.x0 - 80, top: PARCEL.y0 - 70, width: w, height: h, transformOrigin: '70% 0%',
      transform: `translate(${e * 900}px, ${-e * 1500}px) rotate(${e * 18}deg) scaleY(${1 - 0.35 * e})`, filter: k > 0 ? `blur(${2 + 10 * e}px)` : undefined }}>
      <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} style={{ overflow: 'visible' }}>
        <defs><linearGradient id="cl13" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stopColor="#cfc8ba" /><stop offset="1" stopColor="#a39c8e" /></linearGradient></defs>
        <path d={`M ${w * 0.08} ${h * 0.12} Q ${w * 0.5} ${-h * 0.04} ${w * 0.92} ${h * 0.12} L ${w} ${h} Q ${w * 0.75} ${h * 0.93} ${w * 0.5} ${h} Q ${w * 0.25} ${h * 0.93} 0 ${h} Z`} fill="url(#cl13)" />
        {[0.22, 0.4, 0.61, 0.8].map((u, i) => <path key={i} d={`M ${w * u} ${h * 0.1} Q ${w * (u + 0.03)} ${h * 0.6} ${w * (u - 0.02)} ${h}`} stroke="rgba(90,84,72,0.28)" strokeWidth={10} fill="none" />)}
      </svg>
    </div>
  );
};

/** the screen content (1240x775, 16:10): the door picture (D1, 16:9, letterboxed) + the composer overlay (k: its scale, 9:16 0.5) */
const ScreenContent: React.FC<{ g: number; ov: number; k: number }> = ({ g, ov, k }) => {
  const fr = Math.round(clamp(g, 6358, 6597));
  return (
    <div style={{ position: 'absolute', left: 0, top: 0, width: SCR.w, height: SCR.h, overflow: 'hidden', background: '#111' }}>
      <Img src={staticFile(PL.D1)} style={{ position: 'absolute', left: 0, top: (SCR.h - SCR.w * 9 / 16) / 2, width: SCR.w, height: SCR.w * 9 / 16 }} />
      <Img src={staticFile(`secc/lapov/f_${String(fr).padStart(5, '0')}.png`)} style={{ position: 'absolute', left: 0, top: 0, width: SCR.w, height: SCR.h, opacity: ov,
        transformOrigin: '50% 59%', transform: k !== 1 ? `scale(${k})` : undefined }} />
    </div>
  );
};

const Stage: React.FC<ShotProps> = ({ shot, fmt }) => {
  const f = useCurrentFrame(); const g = shot.from + f;
  if (f < T.door) {                                     // rl5_d4 cut 5 (rl5_b c5/13E, plan row 13E): in the lobby, he stamps RETIREMENT on the
    // step box, SHIPPED ✓ inked (a raised -> b down, held 6 f -> c lifted); the old desk stamp (T3) and the dust-cloth beat (T5, the
    // desk parcel no longer in this staging) are out. One slow push toward the inked label (<=1.5%/s), the stamp kick on T.stamp.
    const st = f < T.stamp ? 'a' : f < T.stamp + 6 ? 'b' : 'c';
    const k = inOutSine(clamp(f / (T.door - 1)));
    const s = lerp(1.0, 1.04, k) * (1 + hit(f, T.stamp, 0.012, 12));
    // rl5_d6: push aimed at v2's (rl5_b_13e2, higher camera) inked label, measured on c.jpg (~plate 1656,1704 -> stage 1104,1136)
    return <Cam cx={lerp(1280, 1104, k)} cy={lerp(720, 1136, k)} s={s}><Pl src={`c5/13E/${st}.jpg`} /></Cam>;
  }
  if (f < T.cloth) {                                    // the stamp, callback to 1F (S5 T3 finals)
    const st = swap(f, T.stamp, 2);
    const s = lerp(1.0, 1.03, clamp(f / T.cloth)) * (1 + hit(f, T.stamp, 0.015, 12));
    return <Cam s={s}><Pl src={st === 'A' ? PL.T3a : st === 'S' ? PL.T3s : PL.T3b} /></Cam>;
  }
  if (f < T.door) {                                     // the cloth comes off the parcel: S9 finals reversed, T5d -> T5s -> T5a
    const s = lerp(1.04, 1.07, clamp((f - T.cloth) / (T.door - T.cloth))) * (1 + hit(f, T.cloth + 6, 0.012, 12));
    const st = swap(f, T.cloth + 4, 2);
    return <Cam s={s}><Pl src={st === 'A' ? PL.T5d : st === 'S' ? PL.T5s : PL.T5} /></Cam>;
  }
  if (f >= T13.top) {                                   // the end card: top-down on the shut lid, the cat asleep on it
    const k = inOutSine(clamp((f - T13.top) / (shot.dur - 1 - T13.top)));
    const v = fmt === '9x16' ? end916(f, shot.dur) : null;
    return (
      <AbsoluteFill style={{ background: '#0d0d0f' }}>
        <Cam cx={v ? v.cx : lerp(1280, STK_EC.x, 0.35 + 0.25 * k)} cy={v ? v.cy : lerp(720, STK_EC.y, 0.25 + 0.3 * k)} s={v ? v.s : lerp(1.0, 1.12, k)}>
          <Pl src={FX + 'T29e.jpg'} />
          <ScreenInsert corners={STK_E} w={STK_W} h={STK_H} light={0.92}><EndCard /></ScreenInsert>
        </Cam>
      </AbsoluteFill>
    );
  }
  const pk = inOutCubic(clamp((f - T.pullA) / (T.pullB - T.pullA)));
  const settle = f > T.pullB ? lerp(1, 1.025, inOutSine(clamp((f - T.pullB) / (T13.lidC - T.pullB)))) : 1;
  const tail = f >= T13.lidC ? lerp(1, 1.03, inOutSine(clamp((f - T13.lidC) / (T13.top - T13.lidC)))) : 1;
  const hold = 1 + 0.015 * clamp((f - T.door) / (T.pullA - T.door)) * (1 - pk);    // rl_cut4: a creep on the laptop before the pull (7 dead-still frames)
  const s = lerp(S_FILL, 1.0, pk) * hold * settle * tail * (1 + hit(f, T13.flop, 0.008, 10)) * (1 + hit(f, T13.lidC, 0.014, 12));
  const ov = outCubic(clamp((f - (T.door + 2)) / 8));
  const st = f < T13.flop ? 'a' : f < T13.lidS ? 'f' : f < T13.lidC ? 's' : 'c';
  const plate = FX + (st === 'a' ? 'T29a.jpg' : st === 'f' ? 'T29f.jpg' : st === 's' ? 'T29s.jpg' : 'T29c.jpg');
  const cat = st === 'a' ? CAT_A : CAT_F;
  const catK = NEW ? 1 : clamp((S_FILL - s) / (S_FILL - 2.2));   // the paw comes into the frame as we leave the screen (rl_cut4: the lid is in frame from the start, so the cat is too)
  return (
    <AbsoluteFill style={{ background: '#0d0d0f' }}>
      <Cam cx={lerp(T29_C.x, 1280, pk)} cy={lerp(T29_C.y, 720, pk)} s={s} r={lerp(R_FILL, 0, pk)}>
        <Pl src={plate} />
        {st === 'a' || st === 'f' ? (
          <>
            {NEW ? <ScreenInsert corners={T29_SCREEN} w={LAPTOP.w} h={LAPTOP.h} light={0.87}><Laptop13E f={f - T.door} start={0} cps={45} zoom={2.4} /></ScreenInsert>
              : <ScreenInsert corners={T29_SCREEN} w={SCR.w} h={SCR.h}><ScreenContent g={g} ov={ov} k={fmt === '9x16' ? 0.42 : 1} /></ScreenInsert>}
            {catK > 0 ? <Img src={staticFile(FX + (st === 'a' ? 'cat_a.png' : 'cat_f.png'))} style={{ position: 'absolute', left: cat.x, top: cat.y, width: cat.w, height: cat.h, opacity: catK,
              filter: s > 1.2 ? `blur(${(0.5 * (s - 1)).toFixed(2)}px)` : undefined }} /> : null}
          </>
        ) : null}
        {st === 'c' ? <ScreenInsert corners={STK_C} w={STK_W} h={STK_H} light={0.85}><EndCard /></ScreenInsert> : null}
      </Cam>
    </AbsoluteFill>
  );
};
// 9:16 crop: centred until the end card; rl_fix3_qa2: then on the cat's head, panning to the sticker with the 9:16 camera
const c916e = (x: number, cx: number, s: number) => { const c = clamp(cx, 1280 / s, 2560 - 1280 / s); return clamp((1280 + (x - c) * s) / 2560, 0.16, 0.84); };
export const C5_13E: ShotDef = { stage: Stage, cx916: (f, shot) => {
  if (f < T13.top) return 0.5;
  const v = end916(f, shot.dur); return c916e(lerp(CAT_HEAD_X, STK_EC.x, v.k), v.cx, v.s);
} };
