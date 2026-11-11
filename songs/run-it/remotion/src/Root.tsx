import React from 'react';
import { Composition, continueRender, delayRender, staticFile } from 'remotion';
import { RunIt } from './RunIt';
import { FitProbe } from './FitProbe'; // no-op in normal renders; tools/text_fit_check.py renders with inputProps {__fit}
import { DURATION_FRAMES, FPS } from './timing';
import { Hero, HERO_FPS, HERO_FRAMES } from './hero/Hero'; // hero-shot review composition (Fable, Nov 10)

// Fonts are loaded with FontFace and the render waits for them (delayRender), so stills/frames never show a fallback.
const FACES: [number, string][] = [[400, 'fonts/JBMono-400.ttf'], [500, 'fonts/JBMono-500.ttf'], [700, 'fonts/JBMono-700.ttf']];
const Fonts: React.FC = () => {
  const [h] = React.useState(() => delayRender('fonts'));
  React.useEffect(() => {
    Promise.all(FACES.map(([w, f]) => new FontFace('JBM', `url(${staticFile(f)})`, { weight: String(w) }).load().then((ff) => document.fonts.add(ff))))
      .then(() => continueRender(h)).catch((e) => { console.error(e); continueRender(h); });
  }, [h]);
  return null;
};
const With: React.FC<{ fmt: '16x9' | '9x16'; ui?: boolean }> = (p) => <FitProbe id={p.fmt === '16x9' ? 'RunIt16x9' : 'RunIt9x16'}><Fonts /><RunIt {...p} /></FitProbe>;

const HeroWith: React.FC<{ ui?: boolean }> = (p) => <><Fonts /><Hero {...p} /></>;

export const Root: React.FC = () => (
  <>
    <Composition id="Hero16x9" component={HeroWith} width={1920} height={1080} fps={HERO_FPS} durationInFrames={HERO_FRAMES} defaultProps={{ ui: true }} />
    <Composition id="RunIt16x9" component={With} width={1920} height={1080} fps={FPS} durationInFrames={DURATION_FRAMES} defaultProps={{ fmt: '16x9' as const }} />
    <Composition id="RunIt9x16" component={With} width={1080} height={1920} fps={FPS} durationInFrames={DURATION_FRAMES} defaultProps={{ fmt: '9x16' as const }} />
  </>
);
