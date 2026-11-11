import React from 'react';
// SLOT for built shots. One file per shot in this folder, registered here by shot id (as numbered by shots.ts, s01...).
// Each component gets {shot} and must be a pure function of time: use useT() from '../theme' (absolute film time, even
// inside the Sequence) and the helpers in '../timing' (downbeatAtOrAfter, kickEnv, wordOnsets...). Unregistered shots
// show a labelled stand-in until their component lands.
//
//   import { S01 } from './S01';
//   export const registry: ShotRegistry = { s01: S01 };
import type { ShotRegistry } from '../shots';
import { Hook } from './hook/Hook';
import { Ch1 } from './ch1/Ch1';
import { Mid3D } from './mid3d/Mid3D';
import { Crash } from './crash/Crash';
import { Final } from './final/Final';
import { City } from './city/City';

// THE HOOK (rc_hook): one continuous component for s01-s17, so the hook's world never cuts between shots.
const HOOK = Object.fromEntries(Array.from({ length: 17 }, (_, i) => [`s${String(i + 1).padStart(2, '0')}`, Hook]));
// CH1 + POST1 (rc_ch1): one continuous component for s18-s27.
const CH1 = Object.fromEntries(Array.from({ length: 10 }, (_, i) => [`s${String(i + 18).padStart(2, '0')}`, Ch1]));
// THE 3D MIDDLE (rc_3dstand): one continuous component for s46-s62 (stand-ins), the crash for s63.
const MID3D = Object.fromEntries(Array.from({ length: 17 }, (_, i) => [`s${String(i + 46).padStart(2, '0')}`, Mid3D]));
// V2 -> POST2a (rc_city): one continuous component for s28-s45, the 2.5D city.
const CITY = Object.fromEntries(Array.from({ length: 18 }, (_, i) => [`s${String(i + 28).padStart(2, '0')}`, City]));
// FINAL + OUTRO (rc_final): one continuous component for s64-s78 (the reboot to the loop).
const FINAL = Object.fromEntries(Array.from({ length: 15 }, (_, i) => [`s${String(i + 64).padStart(2, '0')}`, Final]));
// s28-s63 (73.12-155.34): drawn by src/epic (EpicLayer in RunIt.tsx, one persistent world). The 2.5D city, the stand-in 3D middle and
// the old crash are kept in the repo (CITY / MID3D / Crash above) but no longer registered.
const Blank: React.FC<any> = () => null;
const EPIC = Object.fromEntries(Array.from({ length: 36 }, (_, i) => [`s${String(i + 28).padStart(2, '0')}`, Blank]));
export const registry: ShotRegistry = { ...HOOK, ...CH1, ...EPIC, ...FINAL };
void CITY; void MID3D; void Crash;
