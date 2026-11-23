// 1E, the ticket (first30.md): ticket 41 sticks out of the dispenser on the jamb; clap 2 = pulled from off-frame right,
// the strip snaps out and the torn edge flutters 4 frames; clap 4 = the brass tally under it flips 12 -> 13 (split-flap,
// motion-blurred). No hand. Plate T2 (S4) when it lands; this version builds the dispenser and tally in code over a
// soft crop of the lobby wall (red stays the 429's alone, so the dispenser is lobby teal and brass).
import React from 'react';
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { clamp, inCubic, inOutSine, lerp } from '../../ease';
import { ShotDef, ShotProps } from '../types';
import { TextBox } from '../../blocks/Type';
import { FONT } from '../../theme';
import { cueFrame } from '../../timing';
import { Cam, PlateImg, Vignette, hit, ez } from './kit';
import assets from './assets.json';
import { Img, staticFile } from 'remotion';
import { inOutCubic } from '../../ease';
import { tealSrc } from './teal';

const Flap: React.FC<{ from: string; to: string; k: number; w: number; h: number }> = ({ from, to, k, w, h }) => {
  // k 0..1: the top flap (old digit) folds down over the new one
  const face = (d: string, half: 'top' | 'bot') => (
    <div style={{ position: 'absolute', left: 0, width: w, height: h / 2, top: half === 'top' ? 0 : h / 2, overflow: 'hidden', background: half === 'top' ? '#24272d' : '#1d2025' }}>
      <div style={{ position: 'absolute', left: 0, width: w, height: h, top: half === 'top' ? 0 : -h / 2, display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontFamily: FONT.mono, fontWeight: 700, fontSize: h * 0.78, color: '#e4d9bd' }}>{d}</div>
    </div>
  );
  const a = k < 0.5 ? lerp(0, 90, k / 0.5) : lerp(-90, 0, (k - 0.5) / 0.5);
  return (
    <div data-fit="off" style={{ position: 'relative', width: w, height: h, borderRadius: 8, overflow: 'hidden', perspective: 600 }}>
      {face(to, 'top')}{face(from, 'bot')}
      {k > 0 && k < 1 ? (
        <div style={{ position: 'absolute', inset: 0, transformOrigin: '50% 50%', transform: `rotateX(${-a}deg)`, filter: 'blur(1.5px)' }}>
          {k < 0.5 ? face(from, 'top') : face(to, 'bot')}
        </div>
      ) : k >= 1 ? face(to, 'bot') : face(from, 'top')}
      <div style={{ position: 'absolute', left: 0, right: 0, top: h / 2 - 2, height: 4, background: '#0c0d10' }} />
    </div>
  );
};

const Stage: React.FC<ShotProps> = ({ shot, fmt }) => {
  const f = useCurrentFrame();
  const tear = cueFrame(shot, 'ticket') ?? 18, tally = cueFrame(shot, 'tally') ?? 53;
  const pull = clamp((f - tear) / 3);                                   // strip leaves in 3 frames
  const flutter = f >= tear && f < tear + 6 ? Math.sin((f - tear) * 2.4) * 6 * (1 - (f - tear) / 6) : 0;
  const fk = clamp((f - tally) / 4);
  const s = lerp(1.0, 1.04, clamp(f / (shot.dur - 1))) * (1 + hit(f, tear, 0.008, 8) + hit(f, tally, 0.006, 6));
  const strip = (dx: number, op = 1) => (
    <div style={{ position: 'absolute', left: 1330 + dx, top: 560, width: 640, height: 210, opacity: op, background: 'linear-gradient(180deg,#e6dcc6,#e3d6b8)',
      boxShadow: '0 10px 22px rgba(0,0,0,0.35)', clipPath: 'polygon(0 0, 100% 0, 97% 12%, 100% 25%, 97% 38%, 100% 50%, 97% 62%, 100% 75%, 97% 88%, 100% 100%, 0 100%)' }}>
      <div data-fit="off" style={{ position: 'absolute', left: 120, top: 18, fontFamily: FONT.mono, fontWeight: 700, fontSize: 150, lineHeight: 1, color: '#2a2620' }}>41</div>
      <div style={{ position: 'absolute', left: 60, top: 14, bottom: 14, borderLeft: '4px dotted rgba(80,70,55,0.5)' }} />
    </div>
  );
  return (
    <AbsoluteFill>
      <Cam cx={1280} cy={720} s={s}>
        <Cam cx={1250} cy={330} s={3.0}><PlateImg src="plates/meter.jpg" filter="blur(4px) brightness(0.78)" /></Cam>
        <div style={{ position: 'absolute', inset: 0, transformOrigin: '1270px 800px', transform: fmt === '9x16' ? 'scale(0.5)' : undefined }}>
        {/* dispenser */}
        <div style={{ position: 'absolute', left: 640, top: 380, width: 720, height: 560, borderRadius: '48% 48% 40% 40% / 55% 55% 45% 45%', background: 'radial-gradient(ellipse at 35% 30%, #4f8a84 0%, #2c5a56 55%, #1b3b39 100%)',
          boxShadow: '0 30px 60px rgba(0,0,0,0.45), inset 0 0 0 14px #b38a45, inset 0 0 0 18px #6e5428' }} />
        <div style={{ position: 'absolute', left: 1300, top: 600, width: 70, height: 130, borderRadius: 14, background: '#121416', boxShadow: 'inset 0 4px 10px rgba(0,0,0,0.8)' }} />
        <div style={{ position: 'absolute', left: 760, top: 470, width: 480, height: 300, borderRadius: 60, background: 'radial-gradient(ellipse at 40% 30%, rgba(255,255,255,0.10), rgba(255,255,255,0) 70%)' }} />
        {/* the strip: whole until the tear, then snaps out right (motion blur = ghosts), leaving the torn stub */}
        {pull <= 0 ? strip(0) : pull < 1 ? <>{[0, 0.33, 0.66, 1].map((u, i) => <React.Fragment key={i}>{strip(lerp(0, 1500, inCubic(clamp(pull - 0.25 + u * 0.25))), 1 / (i + 1))}</React.Fragment>)}</> : null}
        {pull > 0 ? (
          <div style={{ position: 'absolute', left: 1330, top: 560, width: 70, height: 210, background: 'linear-gradient(180deg,#e6dcc6,#e3d6b8)', transformOrigin: '0% 50%',
            transform: `rotate(${flutter}deg)`, clipPath: 'polygon(0 0, 80% 0, 100% 9%, 78% 20%, 98% 33%, 76% 46%, 100% 58%, 80% 71%, 97% 84%, 82% 100%, 0 100%)' }} />
        ) : null}
        {/* the tally */}
        <div style={{ position: 'absolute', left: 560, top: 1010, width: 1420, height: 230, borderRadius: 14, background: 'linear-gradient(180deg,#e2bf74 0%,#b48736 55%,#8a6526 100%)',
          boxShadow: '0 16px 30px rgba(0,0,0,0.45), inset 0 2px 0 rgba(255,240,200,0.7)' }} />
        <TextBox x={600} y={1050} w={1000} h={150} size={70} kind="head" color="#2b1d0c" pad={16}>LAST ONE, I PROMISE:</TextBox>
        <div style={{ position: 'absolute', left: 1640, top: 1040, display: 'flex', gap: 14 }}>
          <Flap from="1" to="1" k={1} w={130} h={170} />
          <Flap from="2" to="3" k={fk} w={130} h={170} />
        </div>
        </div>
      </Cam>
      <Vignette k={0.5} />
    </AbsoluteFill>
  );
};

// v2 (rl_first30_v2): the real S4 T2 still (rl_stills, final): the dispenser on the jamb with ticket 41, the brass
// LAST ONE, I PROMISE: plaque with its two blank digit windows. Base = plate_nostrip; the ticket = strip.png (RGBA, 41
// printed), its shadow in code. Clap 2: the ticket is pulled down-right out of frame in 3 frames (shutter ghosts), the torn
// stub stays in the slot and flutters. Clap 4: the split-flap digits in the plaque's windows flip 12 -> 13; the camera has
// tilted down and pushed in (1.0 -> 1.16) on the plaque just before, so the line reads whole. 9:16: the plate at 0.75 on its
// own concrete wall (plain-wall crop of the same still) so ticket, plaque and digits sit inside the safe zone.
// rl_fix3_qa1 (QA3: "torn off in ~2 frames with no hand"): a cleaner tear, still no hand (a code hand would not match the
// rendered plate): 4 frames before the clap the ticket is tugged (the piece below the perforation tips 3.2 deg about the
// tear line's left end and drops ~6 px, so the tear opens from the right while the left still holds; the stub gives 2 px),
// then on the clap it tears free and leaves from that pose.
const HAVE_T2 = !!(assets as any)['S4/plate_nostrip'];
const K4 = 2560 / 2880;
const b4 = (x0: number, y0: number, x1: number, y1: number) => ({ left: x0 * K4, top: y0 * K4, width: (x1 - x0) * K4, height: (y1 - y0) * K4 });
const TW = ((assets as any).S4_layout?.tally_windows ?? [[1788.3, 1324.9, 1913.2, 1550.7], [1924.8, 1318.6, 2048.2, 1542.2]]) as number[][];
const SB = [1393, 776, 1678, 1075].map((v) => v * K4);                  // the ticket's solid box (stage px)
const full: React.CSSProperties = { position: 'absolute', left: 0, top: 0, width: 2560, height: 1440 };
const STUB = SB[1] + 30;                                               // the tear line just under the slot
const zig = (y: number, n = 9, a = 9) => Array.from({ length: n + 1 }, (_, i) => `${(SB[0] + (SB[2] - SB[0]) * i / n).toFixed(1)}px ${(y + (i % 2 ? a : -a)).toFixed(1)}px`);
const stubClip = `polygon(0px 0px, 2560px 0px, 2560px ${SB[1] - 40}px, ${SB[2] + 4}px ${SB[1] - 40}px, ${[...zig(STUB)].reverse().join(', ')}, ${SB[0] - 4}px ${SB[1] - 40}px, 0px ${SB[1] - 40}px)`;
const pieceClip = `polygon(${SB[0] - 4}px 1440px, ${zig(STUB).join(', ')}, ${SB[2] + 4}px 1440px)`;
const T2Group: React.FC<{ f: number; tear: number; tally: number }> = ({ f, tear, tally }) => {
  const pull = clamp((f - tear) / 3);
  const tug = f < tear ? inOutSine(clamp((f - (tear - 4)) / 4)) : 1;            // the tension before the tear
  const flutter = f >= tear && f < tear + 6 ? Math.sin((f - tear) * 2.4) * 5 * (1 - (f - tear) / 6) : 0;
  const fk = clamp((f - tally) / 4);
  const strip = (u: number, op = 1, clip?: string, tg = 1) => {
    const k = inCubic(clamp(u)); const dx = 4 * tg + lerp(0, 300, k), dy = 6 * tg + lerp(0, 1150, k), r = 3.2 * tg + lerp(0, 9, k);
    return (
      <div key={u} style={{ ...full, opacity: op, transformOrigin: `${SB[0]}px ${STUB}px`, transform: `translate(${dx.toFixed(1)}px, ${dy.toFixed(1)}px) rotate(${r.toFixed(2)}deg)` }}>
        <Img src={staticFile('first30/S4/strip.png')} style={{ ...full, clipPath: clip, filter: 'drop-shadow(0px 10px 12px rgba(0,0,0,0.32))' }} />
      </div>
    );
  };
  return (
    <>
      <Img src={staticFile(tealSrc('first30/S4/plate_nostrip.jpg'))} style={full} />
      {pull <= 0 && tug <= 0 ? strip(0, 1, undefined, 0) : pull <= 0 ? (
        <>
          {strip(0, 1, pieceClip, tug)}
          <div style={{ ...full, transform: `translate(${(1.5 * tug).toFixed(2)}px, ${(2 * tug).toFixed(2)}px)` }}>
            <Img src={staticFile('first30/S4/strip.png')} style={{ ...full, clipPath: stubClip }} />
          </div>
        </>
      ) : (
        <>
          {pull < 1 ? [0, 0.33, 0.66, 1].map((u, i) => strip(pull - 0.25 + u * 0.25, 1 / (i + 1), pieceClip)) : null}
          <div style={{ ...full, transformOrigin: `${(SB[0] + SB[2]) / 2}px ${SB[1]}px`, transform: `rotate(${flutter.toFixed(2)}deg)` }}>
            <Img src={staticFile('first30/S4/strip.png')} style={{ ...full, clipPath: stubClip }} />
          </div>
        </>
      )}
      {TW.map((w, i) => {
        const bx = b4(w[0], w[1], w[2], w[3]); const fw = bx.width - 10, fh = bx.height - 12;
        return (
          <div key={i} style={{ position: 'absolute', left: bx.left + 5, top: bx.top + 6 }}>
            {i === 0 ? <Flap from="1" to="1" k={1} w={fw} h={fh} /> : <Flap from="2" to="3" k={fk} w={fw} h={fh} />}
          </div>
        );
      })}
    </>
  );
};
const StageT2: React.FC<ShotProps> = ({ shot, fmt }) => {
  const f = useCurrentFrame();
  const tear = cueFrame(shot, 'ticket') ?? 18, tally = cueFrame(shot, 'tally') ?? 53;
  if (fmt === '9x16') {
    const S9 = 0.75, ax = 1410, ay = 1256, tx = 1280 - ax * S9, ty = 792 - ay * S9;
    const sh = (1 + hit(f, tear, 0.008, 8) + hit(f, tally, 0.006, 6)) * lerp(1, 1.03, clamp(f / (shot.dur - 1)));
    return (
      <AbsoluteFill style={{ transformOrigin: '1280px 720px', transform: `scale(${sh.toFixed(5)})` }}>
        <Img src={staticFile('first30/S4/wall.jpg')} style={{ position: 'absolute', left: 860, top: -40, width: 840, height: 2346 }} />
        <div style={{ ...full, transformOrigin: '0 0', transform: `translate(${tx}px, ${ty}px) scale(${S9})`,
          WebkitMaskImage: 'linear-gradient(180deg, #000 0%, #000 98.6%, rgba(0,0,0,0) 100%)', maskImage: 'linear-gradient(180deg, #000 0%, #000 98.6%, rgba(0,0,0,0) 100%)' } as any}>
          <T2Group f={f} tear={tear} tally={tally} />
        </div>
      </AbsoluteFill>
    );
  }
  const kp = ez(f, tally - 9, tally + 1, inOutCubic);
  const s = lerp(1.0, 1.03, clamp(f / (shot.dur - 1))) * lerp(1, 1.16, kp) * (1 + hit(f, tear, 0.008, 8) + hit(f, tally, 0.006, 6));
  return (
    <AbsoluteFill>
      <Cam cx={lerp(1300, 1420, kp)} cy={lerp(720, 1000, kp)} s={s}><T2Group f={f} tear={tear} tally={tally} /></Cam>
      <Vignette k={0.35} />
    </AbsoluteFill>
  );
};
export const S1_1E: ShotDef = HAVE_T2 ? { stage: StageT2, cx916: () => 0.5 } : { stage: Stage, cx916: () => 0.5 };
