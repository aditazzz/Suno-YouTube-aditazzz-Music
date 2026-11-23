// Rate Limited: shared look constants and the format context.
// Everything is authored on ONE stage, 2560x1440 (the 16:9 master size). The 16:9 composition scales the stage to its
// output size (1280x720 when preview); the 9:16 composition scales the same stage to 1920 px tall and crops it around
// the shot's cx916 (src/Film.tsx). So art is never re-rendered for 9:16, only reframed.
import React, { createContext, useContext } from 'react';
import { continueRender, delayRender, staticFile } from 'remotion';

export const STAGE_W = 2560;
export const STAGE_H = 1440;
export const FPS = 30;

export type Fmt = '16x9' | '9x16';
export const FmtCtx = createContext<Fmt>('16x9');
export const useFmt = () => useContext(FmtCtx);

// Text sizes (studio rule, at the 1440 stage): lyrics 64, everything else >= 34, code 38-40.
export const SIZE = { lyric: 64, min: 34, code: 40, label: 38, title: 96 } as const;

// Fonts: loaded with FontFace, and the render waits for them (no fallback-font frames).
export const FONT = { ui: 'RLInter, Inter, system-ui, sans-serif', head: 'RLInterDisplay, Inter, sans-serif',
  mono: 'RLMono, "JetBrains Mono", ui-monospace, monospace', brand: 'RLAnton, Anton, Impact, sans-serif' };
const FACES: [string, string, string][] = [
  ['RLInter', '400', 'fonts/Inter-Regular.otf'], ['RLInter', '600', 'fonts/Inter-SemiBold.otf'],
  ['RLInterDisplay', '700', 'fonts/InterDisplay-Bold.otf'], ['RLInterDisplay', '900', 'fonts/InterDisplay-Black.otf'],
  ['RLMono', '400', 'fonts/JBMono-400.ttf'], ['RLMono', '700', 'fonts/JBMono-700.ttf'], ['RLAnton', '400', 'fonts/Anton-Regular.ttf'],
];
export const Fonts: React.FC = () => {
  const [h] = React.useState(() => delayRender('fonts'));
  React.useEffect(() => {
    Promise.all(FACES.map(([fam, w, f]) => new FontFace(fam, `url(${staticFile(f)})`, { weight: w }).load().then((ff) => (document as any).fonts.add(ff))))
      .then(() => continueRender(h)).catch((e) => { console.error(e); continueRender(h); });
  }, [h]);
  return null;
};

// Night palette (neutral defaults; section workers take colours from the approved plates, never invent a new hue).
export const C = {
  black: '#050608', ink: '#0b0e14', paper: '#f2efe8', white: '#ffffff',
  neonGreen: '#5dff9a', neonRed: '#ff4a3d', amber: '#ffb347', lobbyCool: '#9fc6d8', shadow: 'rgba(0,0,0,0.55)',
};
