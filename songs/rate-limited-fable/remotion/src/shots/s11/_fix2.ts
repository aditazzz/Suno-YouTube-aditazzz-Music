// rl_fix2_robot (lane B): the new plates and layers (remotion/public/fix2/robot/, made by workers/rl_fix2_robot/composite.py from the
// Blender region renders of songs/run-it/blender/jobs/blrl_fix2_robot.py). Same cameras and stage coordinates as the plates they replace.
export const FX = {
  // rl_cut4d_fix (cut 4d, her call 22:24: the black leggings were skin-tight): the same B2B frame with her in the approved cozy sweater + charcoal lounge pants
  // (blrl4_6x via workers/rl_cut4d_fix/rl4d_6x.py; his seated region kept, her pixels from the new frame: comp_6x.py). Was 'fix2/robot/b2b_seat.jpg'.
  B2B: 'c4dfix/b2b_seat_cozy.jpg',           // Rain B2B, 5760 (2x): the left strip re-rendered at 2x with him in the new seat (6A, 6B, 6D)
  H2a: 'fix2/robot/H2a_seat.jpg',            // S12 H2a, 3840: him in the new seat (10B, 11A wipe)
  H2a5k: 'fix2/robot/H2a_seat_5k.jpg', H2aRise: 'fix2/robot/H2a_rise.jpg', H2aStand: 'fix2/robot/H2a_stand.jpg',   // 5760: 11A's stand-up, close
  H2b: 'fix2/robot/H2b_seat.jpg', H2bDawn: 'fix2/robot/H2b_dawn_seat.jpg',   // S12 H2b / first light (12E)
  D5: 'fix2/robot/D5_palm.jpg',              // S10 D5, 3200x2987: his palm flat on the glass, the paddle down (11E)
  D5glass: 'fix2/robot/D5_palm_glass.jpg',   // the same + the glass of water beside her (11E from beat 2)
  SIGN_ON: 'fix2/robot/sign_log_on.jpg',     // the neon's second wording "Live Laugh / Log On" (6D), sign-only region (2880 px)
  PORTRAIT: 'c7/fix713/portrait_seg.jpg',       // his face from the approved D5 (with the 429 paddle) for the EMPLOYEE OF THE MONTH frames (11A)
  CERT_BG: 'fix2/robot/certwall_bg.jpg',     // the T24 lobby wall, for the certificate insert's backdrop (blurred)
};
/** where the "Log On" sign region sits on the stage (composite.py matched it on the Rain B2B: composite_summary.json sign_log_on.stage) */
export const SIGN_ON_BOX = { x: 1224.9, y: 260.4, w: 768, h: 496 };   // matched (rms 0.7/255 on "Live Laugh"): the same box as the flicker region
