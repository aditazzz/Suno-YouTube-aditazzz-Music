// 1H, the building goes grey (first30.md): flat-on, the whole facade; the five floors drop out top to bottom on the
// five eighth-notes (each floor a 1-frame flicker), the rooftop sign drains from green to dead grey with one last
// stutter, the tail stops mid-swing and droops 3 degrees. Plate NS2 night + grey states (placeholder: graded dawn).
import React from 'react';
import { useCurrentFrame } from 'remotion';
import { clamp, inOutSine } from '../../ease';
import { ShotDef, ShotProps } from '../types';
import { Cam, ez, flickOut } from './kit';
import { NightStreet } from './street';

const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame(); const g = shot.from + f;
  const ev = (shot.cues ?? []).map((c) => c.frame - shot.from);           // 0, 9, 18, 26, 35 (the last lands on the cut)
  const at = [ev[0] ?? 0, ev[1] ?? 9, ev[2] ?? 18, ev[3] ?? 26, Math.min(shot.dur - 3, ev[4] ?? 33)];
  const win = (i: number) => { const row = Math.floor(i / 8), col = i % 8; return { lit: flickOut(f, at[row] + col * 0.25) }; };
  const green = 1 - ez(f, 2, 24, inOutSine);
  const stut = f >= 22 && f < 26 ? [0.2, 0.9, 0.1, 0.6][f - 22] : f >= 26 ? 0.12 : 1;
  const droop = 3 * ez(f, 3, 18, (k) => k * k);
  return (
    <Cam cx={1262} cy={705} s={1.12 + 0.01 * f / shot.dur}>
      <NightStreet g={g} win={win} sign={clamp(stut)} signGreen={green} signLight={green * clamp(stut)} clockMin={484}
        tailAngle={(u) => 8 + droop * (0.4 + u)} parcels={[]} />
    </Cam>
  );
};

// v3: the real NS2 whole plate, night -> grey. Each floor flickers to the grey build on its eighth (top floor first, the same
// flickOut as v1), the sign drains with its stutter, the tail droops 3 degrees, and over the last frames the grey build's sky
// and exposure cross-fade in (rl_stills_street's note). A slow 2% push on the whole facade.
import { HAVE_NS2W, NS2WScene } from './ns';
const StageNS: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame();
  const ev = (shot.cues ?? []).map((c) => c.frame - shot.from);
  const at = [ev[0] ?? 0, ev[1] ?? 9, ev[2] ?? 18, ev[3] ?? 26, Math.min(shot.dur - 3, ev[4] ?? 33)];
  const floorK = at.map((a) => 1 - flickOut(f, a));
  // rl7_final (judge nit B06): the sign drains and dies 10 frames earlier (dead from local 16 = abs 546, not 556) so the lights-out reads
  const green = 1 - ez(f, 2, 14, inOutSine);
  const stut = f >= 12 && f < 16 ? [0.2, 0.9, 0.1, 0.6][f - 12] : f >= 16 ? 0.12 : 1;
  const droop = 3 * ez(f, 3, 18, (k) => k * k);
  const endK = ez(f, at[4], shot.dur - 1, inOutSine);
  return (
    <Cam cx={1280} cy={716} s={1.0 + 0.02 * f / shot.dur}>
      <NS2WScene floorK={floorK} signGrey={clamp(1 - green * clamp(stut))} endK={endK} theta={8 + droop} droop={droop} clockMin={484}
        storeGrey={f < 16 ? 0 : f < 20 ? 1 - [0.3, 0.95, 0.15, 0.6][f - 16] : 1} />
    </Cam>
  );
};
export const S1_1H: ShotDef = HAVE_NS2W ? { stage: StageNS, cx916: () => 0.5 } : { stage: Stage, cx916: () => 1262 / 2560 };

