// rl5_d2 cut 5: ONE map of plate swaps, old public path (as cut 4e resolves it) -> cut 5 plate (same camera, same 16:9 framing).
// Read by every plate helper (first30/kit PlateImg, s03/_lib PlateImg, s10/_lib Pl, l2kit L2Img), so a re-dressed plate lands
// without touching the old shot's code. Only entries whose new plate was looked at on a contact sheet go in (STATUS logs each).
import { has } from '../c7/kit/trans';
export const ROOM_5D = has('c7/room/5D/5D_v2.jpg') ? 'c7/room/5D/5D_v2.jpg' : has('c7/room/5D/5D.jpg') ? 'c7/room/5D/5D.jpg' : null;
export const ROOM_11E = has('c7/room/11E/11E_v2.jpg') ? 'c7/room/11E/11E_v2.jpg' : has('c7/room/11E/11E.jpg') ? 'c7/room/11E/11E.jpg' : null;
export const C5PATH: Record<string, string> = {
  'l2/7D_smile.jpg': 'c7/apt/7D_smile_click.jpg',   // rl7_master: locked room;          // rl5_a1: bodysuit (11:10)
  'l2/7D_frozen.jpg': 'c7/apt/7D_frozen_click.jpg',
  // rl5_a1 c2 (11:02, looked at: workers/rl5_d2/c2.jpg): bodysuit, neon line 2 per §6. 12B_child = NEW framing (head side): its neon is
  // cut by the plate's top edge, so c5d/12B frames it out.
  'c4sign/12A_on.jpg': 'c5/12A/12A_on.jpg',
  'c4sign/12A_back.jpg': 'c5/12A/12A_back.jpg',
  'c4sign/12B_w2.jpg': 'c5/12B/12B_w2.jpg',
  'c4sign/12B_tree.jpg': 'c5/12B/12B_tree.jpg',
  'c4sign/12B_baby.jpg': 'c5/12B/12B_baby.jpg',
  'c4sign/12B_child.jpg': 'c5/12B/12B_child.jpg',
  'c4sign/12D_sway.jpg': 'c5/12D/12D_sway.jpg',
  'c4sign/12D_flop.jpg': 'c5/12D/12D_flop.jpg',
  // rl5_a1 c3 12F (18:40 rl5_d5, looked at: workers/rl5_d5/a1.jpg): bodysuit, plain strap; same camera (dial_px = cut 4e's dial quad)
  'c4sign/12F.jpg': 'c7/apt/12F_ban.jpg',   // rl7_master: locked room;
  // rl5_a1 c3b (20:06-20:12, looked at: workers/rl5_d6/c3b.jpg + 13a_fix.jpg): bodysuit. 13A gets cut 4e's own fixes re-applied
  // (workers/rl5_d6/fix13a_c5.py: the heart nails inpainted, the joy face graded off its blow-out). 13C: bodysuit, NOW SERVING 41.
  'c4fix/13A_held.jpg': 'c7/apt/13A_held_off.jpg',   // rl7_master: locked room (fix13a applied);
  'c4fix/13A_joy.jpg': 'c7/apt/13A_joy_off.jpg',
  'l2/13C.jpg': has('c7/13C/p2/13C.jpg') ? 'c7/13C/p2/13C.jpg' : 'c5/13C/13C.jpg',   // rl7_rb: rl7_p2's re-lettered desk parcels (her H7.1)
  // 6C (c3b, workers/rl5_d6/6c.jpg): bodysuit sleeve, plain strap, cuff above the watch; dial square identical to 4e's L2Q['6C'] (x 2560/2880)
  'c4dfix/6C.jpg': has('c7/fix3d/6C/6C.jpg') ? 'c7/fix3d/6C/6C.jpg' : 'c5/6C/6C.jpg',   // rl7_ra: fix3d's thumb fix (her H7.23) when it lands
  // 5D: the neon painted out (workers/rl7_ra/relogo_5d.py, built from fix3d's 5D once it lands: rerun it then) > fix3d's > cut 6's
  ...(has('c7/5D/p2/5D.jpg') ? { 'c5/5D/5D.jpg': 'c7/5D/p2/5D.jpg' } : has('c7/relogo/5D/5D.jpg') ? { 'c5/5D/5D.jpg': 'c7/relogo/5D/5D.jpg' }   // rl7_rb: rl7_p2's CEO box header re-lettered
     : has('c7/fix3d/5D/5D.jpg') ? { 'c5/5D/5D.jpg': 'c7/fix3d/5D/5D.jpg' } : {}),
  // rl7_final: rl7_room's locked-room re-renders (cream sofa / charcoal wall / sign A baked), v2 (her pile labels + new logo) when listed
  ...(ROOM_5D ? { 'c5/5D/5D.jpg': ROOM_5D } : {}),
  ...(ROOM_11E ? { 'c5/11E/11E.jpg': ROOM_11E } : {}),
  // rl5_a1 w1 4F (12:31, looked at: workers/rl5_d3/4f.jpg + s4f.jpg): bodysuit, two parcels, Be Famous, no paddle (him in B's door pose)
  // cut 6 (rl6_edit2): rl6_lobby's lobby side (clock + ShipIt! plaque as 6A/9E2) with rl6_her's eye patches laid back on top (_e = both)
  'cut1/a1/h1_t1.jpg': 'c7/apt/4F_H1_t1_famous.jpg',   // rl7_master: locked room, sign A baked;   // rl7_ra: neon off the wall + plaque re-lettered (workers/rl7_ra/relogo_4f.py); was c6/4F/H1_t1_e.jpg
  'cut1/a1/h1_t2.jpg': 'c7/apt/4F_H1_t2_famous.jpg',   // rl7_master: locked room, sign A baked;   // rl7_ra: neon off the wall + plaque re-lettered (workers/rl7_ra/relogo_4f.py); was c6/4F/H1_t2_e.jpg
  'cut1/a1/h1_t4.jpg': 'c7/apt/4F_H1_t4_famous.jpg',   // rl7_master: locked room, sign A baked;   // rl7_ra: neon off the wall + plaque re-lettered (workers/rl7_ra/relogo_4f.py); was c6/4F/H1_t4_e.jpg
  // cut 6 rl6_lobby (judged on build/rl6_lobby/sheets/c6_landed.jpg): 10B/11A seat re-rendered (bodysuit, Retire Me, his seat in the scene);
  // 12E/12G in cut 5's room state (bodysuit, parcels, Ban 429, candles lit / blown out). Same cameras.
  'fix2/robot/H2a_seat.jpg': 'c6/10B/H2a_seat_3840.jpg',
  'fix2/robot/H2a_seat_5k.jpg': 'c6/10B/H2a_seat.jpg',
  'c4sign/12E_stare.jpg': 'c6/12E/12E_stare.jpg',
  'c4sign/12E_blow.jpg': 'c6/12E/12E_blow.jpg',
  'c4fix/12E_blow.jpg': 'c6/12E/12E_blow.jpg',
  'c4sign/12G.jpg': 'c6/12G/12G.jpg',
  // rl7_ra: P1's street (K8 + her H7.1/2/3: BUILD PASSING off, the lit SHIP IT! neon on the roof, new canopy logo, WE SHIP | WORLDWIDE big
  // on both shop windows), same cameras. Was rl5_d2's baked facade (c5/facade/baked/...).
  // rl5_b facade: canopy 429 -> lit ShipIt! panel, `We ship` / `worldwide` on the door leaves (patches baked by workers/rl5_d2/bake_facade.py)
  'first30/NS1/plate_dark.jpg': has('c7/street/p2/NS1_plate_dark.jpg') ? 'c7/street/p2/NS1_plate_dark.jpg' : 'c7/street/NS1_plate_dark.jpg',   // rl7_sign2: the bigger roof sign + canopy letters (+ rl7_p2's door logos)
  'first30/NS2/tall_night.jpg': has('c7/street/p2/NS2_tall_night.jpg') ? 'c7/street/p2/NS2_tall_night.jpg' : 'c7/street/NS2_tall_night.jpg',   // rl7_rb: rl7_p2's roof neon, not blown out (her b_B02 f404)
  'first30/NS2/whole_night.jpg': has('c7/street/p2/NS2_whole_night.jpg') ? 'c7/street/p2/NS2_whole_night.jpg' : 'c7/street/NS2_whole_night.jpg',
  'first30/NS2/whole_grey.jpg': has('c7/street/p2/NS2_whole_grey.jpg') ? 'c7/street/p2/NS2_whole_grey.jpg' : 'c7/street/NS2_whole_grey.jpg',   // rl7_sign2: the bigger roof sign + canopy letters (+ rl7_p2's door logos)
  'l5/13B/whole.jpg': has('c7/street/p2/13B_whole.jpg') ? 'c7/street/p2/13B_whole.jpg' : 'c7/street/13B_whole.jpg',
  'l5/13B/mid.jpg': has('c7/street/p2/13B_mid.jpg') ? 'c7/street/p2/13B_mid.jpg' : 'c7/street/13B_mid.jpg',   // rl7_sign2: the bigger roof sign + canopy letters (+ rl7_p2's door logos)
  'l5/13B/door.jpg': has('c7/street/p2/13B_door.jpg') ? 'c7/street/p2/13B_door.jpg' : 'c7/street/13B_door.jpg',   // rl7_sign2: the bigger roof sign + canopy letters (+ rl7_p2's door logos)
  // 12H (5:59 street dolly, 69 frames): the facade without the 429 (rl5_d's request to rl5_b)
  // rl7_ra (her H7.1): the desk front's raised ShipIt! re-lettered with rl7_logo's logo on every visor state (workers/rl7_ra/relogo.py)
  'c5/4G/plate.jpg': 'c7/relogo/4G/plate.jpg',
  'c5/4G/plate_eyes.jpg': 'c7/relogo/4G/plate_eyes.jpg',
  'c5/4G/plate_sorry.jpg': 'c7/relogo/4G/plate_sorry.jpg',
  'c5/4G/plate_closed.jpg': 'c7/relogo/4G/plate_closed.jpg',
  'c5/4G/plate_dark.jpg': 'c7/relogo/4G/plate_dark.jpg',
  'c5/4G/plate_4.jpg': 'c7/relogo/4G/plate_4.jpg',
  'c5/4G/plate_42.jpg': 'c7/relogo/4G/plate_42.jpg',
  'c5/4G/plate_429.jpg': 'c7/relogo/4G/plate_429.jpg',
  'c5/5B/plate.jpg': 'c7/relogo/5B/plate.jpg',
  'c5/5B/plate_eyes.jpg': 'c7/relogo/5B/plate_eyes.jpg',
  'c5/5B/plate_closed.jpg': 'c7/relogo/5B/plate_closed.jpg',
  'c5/5B/plate_dark.jpg': 'c7/relogo/5B/plate_dark.jpg',
  'c5/5B/plate_200.jpg': 'c7/relogo/5B/plate_200.jpg',
  ...Object.fromEntries(Array.from({ length: 69 }, (_, i) => { const n = String(i + 1).padStart(4, '0'); return [`l5/12H/f_${n}.jpg`, `c5/12H/baked/f_${n}.jpg`]; })),
};
export const c5p = (p: string): string => C5PATH[p] ?? p;
