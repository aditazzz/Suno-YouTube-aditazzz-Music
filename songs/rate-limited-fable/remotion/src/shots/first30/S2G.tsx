// 2G "Don't leave me on read like this" (BOARDS): close on him behind the glass; the glass is her screen. One message pops onto it:
// "One last thing." Under it: Delivered. His eyes go to it (C2), then: Read 2:06 AM, and his eyes go back to her (C1).
// rl_fix2_open: built new (was the animatic default with 5H's chorus-2 messages and a 3:59 clock, clipped at the top).
// Only her one message, nothing she hasn't sent yet; the clock 2:06; the bubble large (WATCH: the reading gags were too small)
// and inside the frame with margin. 9:16: the bubble in the safe zone upper left (screen layer), his eyes centre.
// rl_fix3_qa1 (QA3): "Delivered" and "Read 2:06 AM" no longer cross-fade on top of each other: Delivered fades out over 2
// frames, the pill holds empty 1 frame, then Read 2:06 AM fades in over 3.
// PLATES: S8 C1 / C2 (finals, 4320 px; C2 = eyes to the bubble, upper left of the glass) + the lobby clock in code.
import React from 'react';
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { clamp, lerp, inOutSine } from '../../ease';
import { ShotDef, ShotProps } from '../types';
import { TextBox } from '../../blocks/Type';
import { Cam, PlateImg, gb, LobbyClock } from '../s03/_lib';
import { springy } from '../../ease';

const K8 = 2560 / 4320; const EYES_X = ((1575.1 + 2538.2) / 2) * K8;
const beats = (shot: ShotProps['shot']) => ({ pop: 3, del: 10, look: gb(shot, 1), read: gb(shot, 2), back: gb(shot, 3) });
const camAt = (f: number, shot: ShotProps['shot']) => ({ cx: 1300, cy: 690, s: lerp(1.0, 1.05, 0.75 * inOutSine(clamp(f / (shot.dur - 1))) + 0.25 * clamp(f / (shot.dur - 1))) });

const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame(); const b = beats(shot); const { cx, cy, s } = camAt(f, shot);
  const eyesUp = f >= b.look && f < b.back;
  return <Cam cx={cx} cy={cy} s={s}><PlateImg src={eyesUp ? 'fix2/open/C2.jpg' : 'fix2/open/C1.jpg'} /><LobbyClock text="2:06" /></Cam>;
};

/** the message on the glass, in the OUTPUT frame (16:9 2560x1440 or 9:16 1080x1920) */
const Bubble: React.FC<{ f: number; b: ReturnType<typeof beats>; nine: boolean }> = ({ f, b, nine }) => {
  const k = clamp((f - b.pop) / 9); if (f < b.pop) return null;
  const sc = lerp(0.6, 1, springy(k, 1.2, 6)); const op = clamp((f - b.pop) / 3);
  const L = nine ? { x: 110, y: 300, w: 700, h: 132, size: 74, rw: 700, rh: 76, rs: 46 } : { x: 170, y: 150, w: 1020, h: 184, size: 108, rw: 1020, rh: 92, rs: 56 };
  const kd = clamp((f - b.del) / 4);
  const delOp = 1 - clamp((f - b.read) / 2), readOp = clamp((f - b.read - 2) / 3);   // out, one empty frame, in: never both
  return (
    <AbsoluteFill>
      <div style={{ position: 'absolute', left: L.x, top: L.y, width: L.w, height: L.h, opacity: op, transformOrigin: '100% 100%', transform: `scale(${sc.toFixed(4)})`,
        filter: 'drop-shadow(0 10px 22px rgba(0,0,0,0.35))' }}>
        <TextBox x={0} y={0} w={L.w} h={L.h} size={L.size} kind="ui" weight={600} color="#ecebe6" bg="#2c72e0" pad={18} radius={L.h / 2} align="center">One last thing.</TextBox>
      </div>
      <div style={{ position: 'absolute', left: L.x + L.rw * 0.42, top: L.y + L.h + 12, width: L.rw * 0.58, height: L.rh, borderRadius: L.rh / 2, background: 'rgba(20,16,12,0.45)', opacity: kd }}>
        <TextBox x={0} y={0} w={L.rw * 0.58} h={L.rh} size={L.rs} kind="ui" weight={600} color="#e6e3dc" pad={10} align="center" opacity={delOp}>Delivered</TextBox>
        <TextBox x={0} y={0} w={L.rw * 0.58} h={L.rh} size={L.rs} kind="ui" weight={700} color="#e6e3dc" pad={10} align="center" opacity={readOp}>Read 2:06 AM</TextBox>
      </div>
    </AbsoluteFill>
  );
};
const Screen: React.FC<ShotProps> = ({ shot, fmt }) => { const f = useCurrentFrame(); return <Bubble f={f} b={beats(shot)} nine={fmt === '9x16'} />; };
const c916 = (x: number, cx: number, s: number) => { const c = clamp(cx, 1280 / s, 2560 - 1280 / s); return clamp((1280 + (x - c) * s) / 2560, 0.16, 0.84); };
export const S2_2G: ShotDef = { stage: Stage, screen: Screen, cx916: (f, shot) => { const c = camAt(f, shot); return c916(EYES_X, c.cx, c.s); } };
