// rl_cut4_fix (cut 4b): lane L2 plate/layer overrides, preferred over c4sign.ts and l2data.ts by L2Img / hasL2. key = plate id or "id:layer".
// 9E_bail: Cooper SEATED on the vibration plate (9A's Cooper, same room/camera/plate), the flying Cooper out (rl_watch4 blocker: he hung
// frozen in mid-air across 9D -> 9E). workers/rl_cut4_fix/fix9e_cooper.py. The clean + hair layers are L2's, unchanged.
export const C4FIX: Record<string, string> = {
  '9E_bail': 'c4fix/9E_bail.jpg',
  '9E_bail:fg': 'c4fix/9E_bail_fg.png',
  // 13A (fix13a.py): the held face without the red heart nails (they read as red blobs down her chin); the joy face graded off its blow-out
  '13A_held': 'c4fix/13A_held.jpg',
  '13A_joy': 'c4fix/13A_joy.jpg',
  // 12E (fix12e_ear.py): two candle flames showing through Cooper's raised ear fur in 12E_blow, painted out
  '12E_blow': 'c4fix/12E_blow.jpg',
  // rl_cut4d_fix (cut 4d): 6C with her in the approved cozy sweater (the sleeve over her watch arm was the black long sleeve); same camera/dial layout
  '6C': 'c4dfix/6C.jpg',
};
