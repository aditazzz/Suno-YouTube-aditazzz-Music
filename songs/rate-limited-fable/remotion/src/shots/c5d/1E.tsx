// rl5_d2 cut 5 1E (356-426): rl5_b's re-render of the S4 dispenser with the brass "12" tally gone (her 1E note: "Why is there a 12 AND
// another number coming out of the machine?"; N02 drop the 12, keep 41). Plan: slow rise; hold on the ticket >= 1.5 s. With the tally
// gone, the tear moves from clap 2 (374) to clap 4 (409): the ticket holds 53 f (1.77 s), then tears free (S1E's tear, no hand).
// Plate: c5/1E/plate_nostrip_teal.jpg (B's plate_nostrip with the dispenser in the lobby teal, as cut 4e's; workers/rl5_d2/teal_1e.py).
import React from 'react';
import { AbsoluteFill, Img, staticFile, useCurrentFrame } from 'remotion';
import { clamp, inCubic, inOutSine, lerp } from '../../ease';
import { ShotDef, ShotProps } from '../types';
import { Cam, Vignette, hit } from '../first30/kit';
import { ioc } from './legacy';

const K4 = 2560 / 2880;
const SB = [1391, 776, 1678, 1075].map((v) => v * K4);   // the ticket's solid box (B's strip_box x; the slot line as cut 4e's)
const full: React.CSSProperties = { position: 'absolute', left: 0, top: 0, width: 2560, height: 1440 };
const STUB = SB[1] + 30;
const zig = (y: number, n = 9, a = 9) => Array.from({ length: n + 1 }, (_, i) => `${(SB[0] + (SB[2] - SB[0]) * i / n).toFixed(1)}px ${(y + (i % 2 ? a : -a)).toFixed(1)}px`);
const stubClip = `polygon(0px 0px, 2560px 0px, 2560px ${SB[1] - 40}px, ${SB[2] + 4}px ${SB[1] - 40}px, ${[...zig(STUB)].reverse().join(', ')}, ${SB[0] - 4}px ${SB[1] - 40}px, 0px ${SB[1] - 40}px)`;
const pieceClip = `polygon(${SB[0] - 4}px 1440px, ${zig(STUB).join(', ')}, ${SB[2] + 4}px 1440px)`;
const STRIP = 'c5/1E/strip.png';
const TEAR = 409;

const Group: React.FC<{ f: number; tear: number }> = ({ f, tear }) => {
  const pull = clamp((f - tear) / 3);
  const tug = f < tear ? inOutSine(clamp((f - (tear - 4)) / 4)) : 1;
  const flutter = f >= tear && f < tear + 6 ? Math.sin((f - tear) * 2.4) * 5 * (1 - (f - tear) / 6) : 0;
  const strip = (u: number, op = 1, clip?: string, tg = 1) => {
    const k = inCubic(clamp(u)); const dx = 4 * tg + lerp(0, 300, k), dy = 6 * tg + lerp(0, 1150, k), r = 3.2 * tg + lerp(0, 9, k);
    return (
      <div key={u} style={{ ...full, opacity: op, transformOrigin: `${SB[0]}px ${STUB}px`, transform: `translate(${dx.toFixed(1)}px, ${dy.toFixed(1)}px) rotate(${r.toFixed(2)}deg)` }}>
        <Img src={staticFile(STRIP)} style={{ ...full, clipPath: clip, filter: 'drop-shadow(0px 10px 12px rgba(0,0,0,0.32))' }} />
      </div>
    );
  };
  return (
    <>
      <Img src={staticFile('c5/1E/plate_nostrip_teal.jpg')} style={full} />
      {pull <= 0 && tug <= 0 ? strip(0, 1, undefined, 0) : pull <= 0 ? (
        <>
          {strip(0, 1, pieceClip, tug)}
          <div style={{ ...full, transform: `translate(${(1.5 * tug).toFixed(2)}px, ${(2 * tug).toFixed(2)}px)` }}>
            <Img src={staticFile(STRIP)} style={{ ...full, clipPath: stubClip }} />
          </div>
        </>
      ) : (
        <>
          {pull < 1 ? [0, 0.33, 0.66, 1].map((u, i) => strip(pull - 0.25 + u * 0.25, 1 / (i + 1), pieceClip)) : null}
          <div style={{ ...full, transformOrigin: `${(SB[0] + SB[2]) / 2}px ${SB[1]}px`, transform: `rotate(${flutter.toFixed(2)}deg)` }}>
            <Img src={staticFile(STRIP)} style={{ ...full, clipPath: stubClip }} />
          </div>
        </>
      )}
    </>
  );
};
const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame(); const tear = TEAR - shot.from; const k = ioc(f, 0, shot.dur - 1);
  // slow rise: the camera lifts from the jamb below up onto the dispenser + ticket (dispenser stage y 31-756, ticket 690-955), a 4% push
  const s = lerp(1.25, 1.30, k) * (1 + hit(f, tear, 0.008, 8));
  return (
    <AbsoluteFill>
      <Cam cx={1320} cy={lerp(760, 600, k)} s={s}><Group f={f} tear={tear} /></Cam>
      <Vignette k={0.35} />
    </AbsoluteFill>
  );
};
export const C5_1E: ShotDef = { stage: Stage, cx916: () => 0.5 };
