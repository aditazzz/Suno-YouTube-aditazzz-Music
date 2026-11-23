// Her H7.1 / H7.2 (cut 6 frame 233: "Ship It logo can be way better ... cursor cursor SHIP IT ... replace it everywhere"): rl7_logo's
// new logo (public/c7/logo/, LOGO.md) on the lobby's lit sign in every plate Remotion draws that P1 doesn't re-render. The sign's
// face is a flat, evenly lit white panel (measured: rgb ~238,234,225 edge to edge), so the old script is painted out with the face's own
// white and the new logo is printed on it (shipit_logo_light: ink letters, orange pointers), 80% of the face width, a hair soft like
// the plate. SIGN_FACES: the face box per plate dir, plate px (3840 wide plates -> stage /1.5), found by its white panel.
import React from 'react';
import { Img, staticFile } from 'remotion';

export const LOGO = { light: 'c7/logo/shipit_logo_light.png', dark: 'c7/logo/shipit_logo_dark.png', neon: 'c7/logo/shipit_neon.png',
  stackedDark: 'c7/logo/shipit_stacked_dark.png', stackedLight: 'c7/logo/shipit_stacked_light.png', monoOrange: 'c7/logo/shipit_mono_orange.png',
  roomNeon: 'c7/logo/room_neon_live_love_click_click_ship_it.png' };
export const LOGO_ASPECT = 4096 / 1171;
export const SIGN_FACES: Record<string, [number, number, number, number]> = {   // x0, y0, x1, y1 in plate px
  K: [243, 411, 1018, 626], '4G': [943, 262, 1539, 430], '5B': [463, 175, 1117, 363],
};
export const SignFace: React.FC<{ dir: string; k?: number; fill?: string; logo?: string; w?: number }> = ({ dir, k = 1 / 1.5, fill = 'rgb(238,234,225)', logo = LOGO.light, w = 0.8 }) => {
  const b = SIGN_FACES[dir]; if (!b) return null;
  const [x0, y0, x1, y1] = b.map((v) => v * k); const fw = x1 - x0, fh = y1 - y0;
  let lw = fw * w, lh = lw / LOGO_ASPECT; if (lh > fh * 0.78) { lh = fh * 0.78; lw = lh * LOGO_ASPECT; }
  return (
    <>
      <div style={{ position: 'absolute', left: x0 + 3, top: y0 + 3, width: fw - 6, height: fh - 6, background: fill, borderRadius: 3, filter: 'blur(1.5px)' }} />
      <Img src={staticFile(logo)} style={{ position: 'absolute', left: x0 + (fw - lw) / 2, top: y0 + (fh - lh) / 2, width: lw, height: lh, filter: 'blur(0.4px)' }} />
    </>
  );
};
