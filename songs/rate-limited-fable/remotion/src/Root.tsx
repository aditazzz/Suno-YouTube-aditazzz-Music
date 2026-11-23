import React from 'react';
import { Composition } from 'remotion';
import { FitProbe } from './FitProbe'; // no-op in normal renders; tools/text_fit_check.py renders with inputProps {__fit}
import { Film, FilmProps } from './Film';
import { Fonts, FPS } from './theme';
import { DURATION_FRAMES } from './timing';
import { FINAL_END } from './shots/c7/kit/edit';   // rl7_final: the final's end (B61 eased to rest)

// Film16x9: 2560x1440 master; {preview: true} renders 1280x720. Film9x16: 1080x1920 (preview 540x960), reframed
// from the same stage. Props: noAudio (default TRUE: renders are silent and the WAV is muxed with ffmpeg; the bundle 404s on the symlinked song.wav), captions (the caption layer, off by default),
// slate (shot id / clock / new-picture cards, for animatics only).
const F16: React.FC<FilmProps> = (p) => <FitProbe id="Film16x9"><Fonts /><Film {...p} fmt="16x9" /></FitProbe>;
const F916: React.FC<FilmProps> = (p) => <FitProbe id="Film9x16"><Fonts /><Film {...p} fmt="9x16" /></FitProbe>;
// The animatic: the same film with slates on (shot id, clock, "new picture" cards), full size so text_fit_check.py
// measures it at the real sizes; render it with --scale=0.5 for the 1280x720 cut.
// rl7_ra: cut 7 (PLAN7): the 61 blocks of src/data/blocks_c7.json (src/shots/c7/), same sizes and props as Film16x9 / Film9x16.
const C7_16: React.FC<FilmProps> = (p) => <FitProbe id="Cut7Film16x9"><Fonts /><Film {...p} fmt="16x9" cut={7} /></FitProbe>;
const C7_916: React.FC<FilmProps> = (p) => <FitProbe id="Cut7Film9x16"><Fonts /><Film {...p} fmt="9x16" cut={7} /></FitProbe>;
const A16: React.FC<FilmProps> = (p) => <FitProbe id="Animatic16x9"><Fonts /><Film {...p} fmt="16x9" slate /></FitProbe>;
const A916: React.FC<FilmProps> = (p) => <FitProbe id="Animatic9x16"><Fonts /><Film {...p} fmt="9x16" slate /></FitProbe>;

export const Root: React.FC = () => (
  <>
    <Composition id="Film16x9" component={F16} width={2560} height={1440} fps={FPS} durationInFrames={DURATION_FRAMES}
      defaultProps={{ fmt: '16x9', preview: false, noAudio: true, captions: false, slate: false } as FilmProps}
      calculateMetadata={({ props }) => (props.preview ? { width: 1280, height: 720 } : {})} />
    <Composition id="Film9x16" component={F916} width={1080} height={1920} fps={FPS} durationInFrames={DURATION_FRAMES}
      defaultProps={{ fmt: '9x16', preview: false, noAudio: true, captions: false, slate: false } as FilmProps}
      calculateMetadata={({ props }) => (props.preview ? { width: 540, height: 960 } : {})} />
    <Composition id="Cut7Film16x9" component={C7_16} width={2560} height={1440} fps={FPS} durationInFrames={Math.max(DURATION_FRAMES, FINAL_END)}
      defaultProps={{ fmt: '16x9', preview: false, noAudio: true, captions: false, slate: false } as FilmProps}
      calculateMetadata={({ props }) => (props.preview ? { width: 1280, height: 720 } : {})} />
    <Composition id="Cut7Film9x16" component={C7_916} width={1080} height={1920} fps={FPS} durationInFrames={DURATION_FRAMES}
      defaultProps={{ fmt: '9x16', preview: false, noAudio: true, captions: false, slate: false } as FilmProps}
      calculateMetadata={({ props }) => (props.preview ? { width: 540, height: 960 } : {})} />
    <Composition id="Animatic16x9" component={A16} width={2560} height={1440} fps={FPS} durationInFrames={DURATION_FRAMES}
      defaultProps={{ fmt: '16x9', slate: true } as FilmProps} />
    <Composition id="Animatic9x16" component={A916} width={1080} height={1920} fps={FPS} durationInFrames={DURATION_FRAMES}
      defaultProps={{ fmt: '9x16', slate: true } as FilmProps} />
  </>
);
