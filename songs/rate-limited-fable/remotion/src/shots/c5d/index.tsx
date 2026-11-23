// rl5_d: the cut 5 shot map (CUT5_PLAN §3, 74 shots). Cut 4e's components (OLD) are the building blocks; merged shots play their
import React from 'react';
// cut-4e pieces against the old shot objects (./legacy), fixed shots have their own c5d files, rl5_c's screens (../c5/) and the new
// plates replace them as they land (workers/rl5_d/STATUS.md logs every swap).
import { ShotDef } from '../types';
import { asOld, pieces, C4E, camera } from './legacy';
import { edgeIn, edgeOut } from './edge';
import { C5_2F } from './2F';
import { C5_2B, C5_2G, C5_5H, C5_8F, C5_4G } from './K';   // rl5_b's K plate + 4G variant with the visor (rl5_d2)
import { C5_9F } from './9F';
import { C5_12F } from './12F';
import { C5_6A, C5_6B, C5_6D } from './6x';
import { C5_4H, C5_5A, C5_5B, C5_2E } from './b5';
import { C5_4E_FULL, C5_5D, C5_9E2, C5_9G, C5_11E, C5_13B } from './a2';
import { C5_8G } from '../s08/8G';
import { C5_4J, C5_11B } from './meter';
import { make8A } from './8A';
import { MeterDigits } from '../c5/Meter8A';
import { VacuumNotif, NOTIF } from '../c5/Notif';
import { useCurrentFrame } from 'remotion';
import { ShotProps } from '../types';
const Notif9E2: React.FC<ShotProps> = ({ shot }) => { const f = useCurrentFrame(); return <VacuumNotif f={f} at={NOTIF.IN - shot.from} />; };
import { C5_SHOTS } from '../c5';   // rl5_c's screens (workers/rl5_c/PATCH.md)
import { C5_13E } from './13E';
import { C5_4F_BASE } from './4F';   // rl6_edit: 4F one continuous slide (FRAMES blocker 10)
import { C5_10B, make11A } from './join10';   // rl6_edit: one door-edge travel 10B -> 11A
import { C5_1F } from './1F';
import { C5_1E } from './1E';
import { C5_4I } from './4I';
import { C5_7D } from './7D';
import { C5_1D } from './1D';
import { C5_2C } from './2C';
import { C5_1A } from './teaser5';
import { C5_12B } from './12B';
import { C5_9A, C5_9E1, C6_9E1 } from './9A';
import { make7E1, beatF } from './7E1';
import { VisorLines } from '../c5/Visor';
import { Visor7Led } from '../c7/fix713/Visor7Led';
import type { Quad } from '../../blocks/ScreenInsert';
// the visible glass only (A2's visor_quad includes his arm at the left end; text drew over it): measured on stage_A..D (rl5_d3)
const GLASS7: Quad = [[1864, 374], [1968, 372], [1968, 410], [1864, 414]];
// 7E1 visor: rl5_c's five lines, changing with the model's gestures (beats 1.5 / 3.5 / 5.5) and on 7 (rl5_d2)
const Visor7: React.FC<{ f: number; shot: ShotProps['shot'] }> = ({ f, shot }) => (   // rl7_fixb: LED dot-matrix face (kit/seg VisorText), was VisorLines' monospace
  <Visor7Led f={f} beats={[0, 1.5, 3, 4.5, 6].map((b) => (b === 0 ? 0 : beatF(shot, b)))} quad={GLASS7} />);

const len = (id: string) => C4E[id].dur;
export const c5Defs = (OLD: Record<string, ShotDef>): Record<string, ShotDef> => {
  // one cut-4e shot stretched to the new length (placeholder for "stay longer" until its new plate/screen lands)
  const ST = (id: string, n: number) => pieces([{ def: OLD[id], old: id, at: 0, len: n, rate: len(id) / n }]);
  const P = (ids: string[]) => { let at = 0; return pieces(ids.map((id) => { const p = { def: OLD[id], old: id, at, len: len(id) }; at += len(id); return p; })); };
  return {
    ...C5_SHOTS,                                           // 1G, 3B, 3C, 4T, 4E, 8D, 9C, 10A (rl5_c batch 1)
    '13E': C5_13E,
    '1A': C5_1A,                                           // cut-5 teaser beats on the 2C + K plates (rl5_d3)
    '2C': C5_2C,                                           // rl5_a1 re-dress, framed above the paddle (rl5_d3)
    '1D': C5_1D,                                           // rl5_a1 re-dress, one plate state, slide left (rl5_d3)
    // section 1-2
    '1E': C5_1E,                                        // B's re-render, no 12 tally (rl5_d2)
    '1F': C5_1F,                                        // rl5_d4: B's new 1F camera (rl5_b_1f2), A SONG parcel, ink on the label
    '2B': C5_2B, '2F': C5_2F, '2G': C5_2G,
    '2E': C5_2E,                                        // rl5_d5: rl5_a1's 2E5 panorama, shelf -> door -> her + FAME under the neon
    // section 3-4: buzzer -> door-edge travel -> crossword
    '3A': edgeOut(OLD['3A'], 10, 1), '3B': edgeIn(C5_SHOTS['3B'], 10, 1),
    // 4F -> 4G: 4F's last 16 frames start the push toward the door (accelerating), 4G arrives moving and lands at 1955
    '4F': camera(C5_4F_BASE, (f, dur) => { const t = Math.min(1, Math.max(0, (f - (dur - 16)) / 16)); return { s: 1 + 0.12 * t * t * t, ox: 0.27, oy: 0.42 }; }),
    '4G': C5_4G, '4I': C5_4I, '4J': C5_4J,
    // section 5
    '4H': C5_4H, '5A': C5_5A,                            // rl5_d5: B's shelf panorama slide; mug on the tray + 418
    '5B': C5_5B,           // rl5_d5: K plate 4-2-9 (leaves moving at 68) -> B's 5B plate at 2441 (THE cat, dark -> eyes -> 200)
    '5H': C5_5H,           // K plate + rl5_c's GlassChat; 5E: rl5_c (C5_SHOTS)
    // section 7-9
    '7D': C5_7D,                                          // her only, A1's bodysuit plates (rl5_d2)
    '7E1': make7E1({ from: { cx: 1280, cy: 720 }, to: { cx: 1640, cy: 575 }, s1: 2.5, Visor: Visor7 }),   // rl6_edit: FRAMES blocker 8, visor 2x tighter; GENIUS! from beat 6 (35 f)   // director 11:55: push to 1.35 toward him, ends on the push (no phone)   // A2's one-take date (rl5_d2)
    '6A': C5_6A, '6B': C5_6B, '6D': C5_6D,               // rl5_d5: A1's re-dressed B2B (room_rain), one 3D clock, no code clock
    '8G': C5_8G,                                         // rl5_d5: Click Click Ship It -> Ban 429 on A1's four sign plates
    '8A': make8A(({ f, shot }) => <MeterDigits f={f} from={shot.from} />), '8F': C5_8F,         // 8B/8C windows cut
    '9A': C5_9A, '9E1': C6_9E1,                          // rl5_a2's 9A/9E1 layers (rl5_d2); guests pending (A2 job sqg)
    '9E2': C5_9E2, '9G': C5_9G,                         // rl5_d5: A2's 9E2 plate + rl5_c's notification; 9G neon Not Mad -> Cool x3
    '4E': C5_4E_FULL, '5D': C5_5D,                      // rl5_d5: rl5_c's phone part -> A2's begging A/B; A2's 5D
    '9F': C5_9F,
    // section 11-12
    '11E': C5_11E, '13B': C5_13B,                       // rl5_d5: A2's side-on palms; A2's door open -> exterior -> push with the pile
    '10B': C5_10B, '11A': make11A(OLD['11A']),         // rl6_edit (FRAMES blocker 4)
    '11B': C5_11B, '12B': C5_12B, '12F': C5_12F,   // 12C yawn chain cut
  };
};
