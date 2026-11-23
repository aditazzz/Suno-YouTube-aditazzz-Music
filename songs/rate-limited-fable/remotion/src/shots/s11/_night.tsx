// rl_master_fix (Nov 18, the chat's call for the master: "11C/11D/11E lobby light continuous"; rl_watch4d: he dims the lobby in 11C, then 11D
// came back fully lit). One night-light level for the lobby from the end of 11C's dim through 11D and 11E:
//  - 11C: the glass's sleep curve now ends at LOBBY_END_11C (was 0.92, near black) instead of dropping on to black.
//  - 11D (both plates are lobby-side): a plain dark layer, the same #05070a as 11C's glass, at LOBBY_NIGHT on the room with a softer
//    pool on him (the wall lamp / desk lamp still on), so he reads.
//  - 11E: re-rendered in 3D with the lobby-side lights lowered to the same level (workers/rl_master_fix/rl4e_11e.py), no layer here.
// Levels matched by measured luma on the lobby walls (workers/rl_master_fix/STATUS.md).
import React from 'react';

export const LOBBY_END_11C = 0.68;       // 11C's glass at the end of the dim (its lit lobby reads ~155 luma through the glass -> ~50)
export const LOBBY_NIGHT = 0.45;         // darkness of 11D's room (its lit lobby walls ~65-105 -> ~40-55), the same night level as 11C's end and 11E
export const LOBBY_POOL = 0.25;          // darkness at the centre of the pool on him (11D)

/** the night-light layer over a lobby-side plate, in stage px (inside the shot's Cam so the pool stays on him) */
export const NightLobby: React.FC<{ cx: number; cy: number; r: number; dark?: number; pool?: number }> = ({ cx, cy, r, dark = LOBBY_NIGHT, pool = LOBBY_POOL }) => (
  <div style={{ position: 'absolute', left: -400, top: -400, width: 2560 + 800, height: 1440 + 800, pointerEvents: 'none',
    background: `radial-gradient(circle ${Math.round(r)}px at ${Math.round(cx + 400)}px ${Math.round(cy + 400)}px, rgba(5,7,10,${pool}) 0%, rgba(5,7,10,${(pool + dark) / 2}) 55%, rgba(5,7,10,${dark}) 100%)` }} />
);
