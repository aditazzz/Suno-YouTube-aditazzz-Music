// 11C "Close the laptop" (CODEPLAN): he turns the brass dimmer and the lobby lights fall; cut on beat 2 to her side,
// where the glass dims like a sleeping screen (rl_screens glass_11C_sleep curve: to 45%, hold, 92%; re-timed to start at
// the cut). Plate: S21r T25 (rl_cut1 C): T25a hand on the knob, lights full -> T25s the turn (smear) -> T25b turned down,
// the lobby at a quarter. The light pass = T25b_lit (T25b relit to T25a's light: same geometry) fading out over T25b,
// so the lights fall after the knob turns instead of popping. The code dimmer is gone (the plate has the real one).
import React from 'react';
import { useCurrentFrame } from 'remotion';
import { ShotDef, ShotProps } from '../types';
import { ScreenInsert, Quad } from '../../blocks/ScreenInsert';
import { Cam, hit, swap } from '../first30/kit';
import { D1, PL, Pl, clamp, gl, lerp, pulse } from '../s10/_lib';
import { LobbyPanda, pt } from '../../blocks/PandaClock';
import { inOutSine } from '../../ease';
import { LOBBY_END_11C } from './_night';

/** glass_11C_sleep layer.json curve (frames 5211..5274), darkness 0..0.92 */
const CURVE = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.037,0.147,0.236,0.305,0.357,0.395,0.421,0.437,0.446,0.449,0.45,0.45,0.45,0.45,0.45,0.45,0.45,0.45,0.45,0.45,0.45,0.45,0.45,0.45,0.45,0.45,0.461,0.499,0.558,0.631,0.709,0.784,0.85,0.897,0.919,0.92];
// rl_master_fix: the second fall (0.45 -> 0.92, near black) now ends at LOBBY_END_11C, the night-light level 11D/11E hold (was undone on the next cut)
const dark = (i: number) => { const v = CURVE[Math.max(0, Math.min(CURVE.length - 1, Math.round(i)))]; return v <= 0.45 ? v : 0.45 + (v - 0.45) * (LOBBY_END_11C - 0.45) / (0.92 - 0.45); };
const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame(); const g = shot.from + f;
  const cut = gl(shot, 1, 17);
  if (f < cut) {
    const turnAt = 4; const st = swap(f, turnAt, 2);
    const fall = inOutSine(clamp((f - turnAt - 2) / 9));               // lights falling after the turn
    const s = lerp(1.03, 1.07, f / cut) * (1 + hit(f, turnAt, 0.01, 8)) * pulse(g);
    return (
      <Cam cx={1330} cy={800} s={s}>
        <Pl src={st === 'A' ? PL.T25a : st === 'S' ? PL.T25s : PL.T25b} />
        {st === 'B' && fall < 1 ? <Pl src={PL.T25bLit} opacity={1 - fall} /> : null}
      </Cam>
    );
  }
  const d = f - cut; const dk = dark(15 + d);
  return (
    <Cam cx={1280} cy={800} s={lerp(1.2, 1.23, d / (shot.dur - cut)) * (1 + hit(d, 0, 0.008, 8)) * pulse(g)}>
      <Pl src={PL.D1} />
      {/* rl_l3_ui (cut 4, §2a): the panda wall clock at 5:50 where the digital box was; it dims with the lobby (S22) */}
      <LobbyPanda time={pt(5, 50, 4 + d / 30)} chrono={(4 + d / 30) % 60} light={0.8} />
      <ScreenInsert corners={D1.leaf as Quad} w={1360} h={1620}>
        <div style={{ position: 'absolute', inset: 0, background: '#05070a', opacity: dk }} />
      </ScreenInsert>
    </Cam>
  );
};
export const S11_11C: ShotDef = { stage: Stage, cx916: (f, shot) => (f < gl(shot, 1, 17) ? 0.52 : 0.45) };   // 9:16: the knob (stage x 1360), then the door
