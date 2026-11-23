// rl_teaser (Mon Nov 16, her "Yea" 16:08): the opening teaser on the three "Mm" hums, as a SWITCH (off by default).
// Off: 1A renders exactly as before (withTeaser returns the base ShotDef untouched).
// On (input prop `teaser: true`, e.g. --props='{"preview":true,"noAudio":true,"teaser":true}'):
//   0-5    the street's opening frame (1A as now; the cover frame is unchanged)
//   6-23   Mm 1: the 2B hero take from the "nine" frame (H1b 740-757: his face + the 429 big)
//   24-41  Mm 2: her knock through the glass (2C over his shoulder, from the K1 contact at 782: one knock, on the hum)
//   42-58  Mm 3: the building going grey (the whole 1H, its five floors re-cued to land in one beat, 2.1x time), tight on the facade
//   59-    back to 1A/1B's crane as now (the windows are already lit by the third wave, so the street returns whole).
// Hard cuts on the hums, measured on the audio (mix + vocal stem, 50% rise): 0.210 s / 0.797 s / 1.383-1.408 s -> frames
// 6 / 24 / 42; the return lands on the beat at 1.967 s = frame 59. Each source shot renders through <Freeze> at its mapped
// frame, so its own code (camera, track, rings, flickers) draws it: no new pictures, nothing re-rendered elsewhere.
import React from 'react';
import { Freeze, getInputProps, useCurrentFrame } from 'remotion';
import { ShotDef, ShotProps } from '../types';
import { Cue, Shot, shotById } from '../../timing';
import { S2_2B } from './S2B';
import { S2_2C } from './S2C';
import { S1_1H } from './S1H';
import { hit } from './kit';
import { clamp, inOutSine, lerp } from '../../ease';

// rl_cut3 (Nov 16, her APPROVE on the teaser pitch 19:10-19:12): ON by default from cut 3 on; `teaser:false` turns it off.
export const TEASER: boolean = (getInputProps() as any)?.teaser !== false;
export const TEASER_CUTS = [6, 24, 42, 59];

// k = frames since the beat's cut -> source shot-local frame; push = an extra framing on top of the source's own camera
export type Beat = { def: ShotDef; shot: Shot; map: (k: number) => number; push?: (k: number, fmt: string) => { s: number; oy: number; ox?: number };
  cx?: (k: number, src: number) => number };
export const EYE916 = 0.30, MM2_S = 1.66, MM2_OX = 25, MM2_CX916 = 0.405;   // rl_cut3 reframe constants
const sh2B = shotById('2B'), sh2C = shotById('2C'), sh1H = shotById('1H');
const cue = (frame: number, word: string): Cue => ({ cue: 'teaser', word, t: frame / 30, frame, kind: 'word', confidence: 'high' });
const H1H_LEN = sh1H.dur - 1;                                              // 34: the whole 1H inside the 17-frame beat
const BEATS: Beat[] = [
  // rl_cut3 reframe (director's optional note, existing frames only): 9:16 opens on his eye, then whips to the 429 (k 7-11)
  { def: S2_2B, shot: sh2B, map: (k) => 740 - sh2B.from + k, cx: (k, src) => lerp(EYE916, src, inOutSine(clamp((k - 7) / 4))) },
  // one knock only (on the hum's onset): the shot's three "Rate" cues replaced by the 782 contact
  // rl_cut3 reframe: tight on her face + knock, the paddle below frame (so the 429 isn't in two cuts in a row); the K0/K1
  // plates are 4320 px, so 1.66x stays at the plate's own resolution at the 2560 master
  { def: S2_2C, shot: { ...sh2C, cues: [cue(782, 'Mm (2)')] }, map: (k) => 782 - sh2C.from + k,
    push: () => ({ s: MM2_S, oy: 0, ox: MM2_OX }), cx: () => MM2_CX916 },
  // the five floors on frames the 2.125x map lands on (0, 9, 17, 26, 32), so every floor's flicker frame is drawn
  { def: S1_1H, shot: { ...sh1H, cues: [0, 9, 17, 26, 32].map((d) => cue(sh1H.from + d, 'grey')) },
    map: (k) => Math.min(H1H_LEN, Math.round(k * H1H_LEN / (TEASER_CUTS[3] - TEASER_CUTS[2] - 1))),
    // tight on the facade (look 1: the whole flat-on facade read like the street around it): the sign at the top, the five
    // floors fill the frame, the lobby out; a slow creep 1.26 -> 1.32 anchored on the top edge (NS2 whole plate is 4320 px,
    // so 1.32x stays under the plate's own resolution at the 2560 master)
    push: (k) => ({ s: 1.26 + 0.06 * Math.min(1, k / 16), oy: 0 }) },
];
// rl_cut4_fix (rl_watch4 1A: frame 1 of the film was the street with the orange tail blob in the sky): beat 1 (his eyes + the 429) now starts at
// frame 0, held on its first frame until the hum at 6 (where it kicks and plays on as before). The cover frame is now his eyes (never black).
const beatAt = (g: number) => { if (g >= 0 && g < TEASER_CUTS[1]) return 0; for (let i = 1; i < 3; i++) if (g >= TEASER_CUTS[i] && g < TEASER_CUTS[i + 1]) return i; return -1; };
// rl6_edit (FRAMES 1A 6->7: a one-frame punch-in on the same plate): beat 0 starts at frame 0, so there is no cut at 6 any more. It now plays
// straight through 0-23 (no freeze 0-5, no kick at 6, no creep): k runs negative before 6, so the source's own drift starts at frame 0.
const kOf = (g: number, i: number) => (i === 0 ? g - TEASER_CUTS[0] : Math.max(0, g - TEASER_CUTS[i]));
export const srcCx0 = (b: Beat, k: number) => (b.def.cx916 ? b.def.cx916(b.map(k), b.shot) : b.shot.cx916);
const srcCx = (b: Beat, k: number) => (b.cx ? b.cx(k, srcCx0(b, k)) : srcCx0(b, k));

/** wraps 1A: inside the teaser frames it draws the beat's source shot at its mapped frame (a 1.5% kick on each cut) */
export const withTeaser = (base: ShotDef, beats: Beat[] = BEATS): ShotDef => {   // beats: rl5_d3 (cut 5 passes its own)
  if (!TEASER) return base;
  const Base = base.stage;
  const Stage: React.FC<ShotProps> = (p) => {
    const g = p.shot.from + useCurrentFrame(); const i = beatAt(g);
    if (i < 0) return <Base {...p} />;
    const b = beats[i], k = kOf(g, i), S = b.def.stage;
    const pu: { s: number; oy: number; ox?: number } = b.push ? b.push(k, p.fmt) : { s: 1, oy: 50 };
    const s = pu.s * (i === 0 ? 1 : 1 + hit(g - TEASER_CUTS[i], 0, 0.015, 10));   // rl6_edit: kick only on real cuts (24, 42)
    const ox = p.fmt === '9x16' ? srcCx(b, k) * 100 : (pu.ox ?? 50);  // kick around what the 9:16 crop is holding
    return (
      <div style={{ position: 'absolute', left: 0, top: 0, width: 2560, height: 1440, overflow: 'hidden', transform: `scale(${s})`, transformOrigin: `${ox}% ${pu.oy}%` }}>
        <Freeze frame={b.map(k)}><S shot={b.shot} fmt={p.fmt} slate={p.slate} /></Freeze>
      </div>
    );
  };
  const BaseScreen = base.screen;
  const Screen: React.FC<ShotProps> = (p) => {
    const g = p.shot.from + useCurrentFrame(); const i = beatAt(g);
    if (i < 0) return BaseScreen ? <BaseScreen {...p} /> : null;
    const b = beats[i], Sc = b.def.screen;
    return Sc ? <Freeze frame={b.map(kOf(g, i))}><Sc shot={b.shot} fmt={p.fmt} slate={p.slate} /></Freeze> : null;
  };
  const cx916 = (f: number, shot: Shot) => {
    const g = shot.from + f; const i = beatAt(g);
    if (i < 0) return base.cx916 ? base.cx916(f, shot) : shot.cx916;
    return srcCx(beats[i], kOf(g, i));
  };
  return { stage: Stage, screen: Screen, cx916 };
};
