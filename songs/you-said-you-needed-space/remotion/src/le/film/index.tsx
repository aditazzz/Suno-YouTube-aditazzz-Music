// Entry point for the Living Earth film (its own bundle): npx remotion bundle src/le/film/index.tsx
import React from 'react';
import { Composition, registerRoot } from 'remotion';
import { LivingEarthFilm, FilmProps } from './Film';
import { DURATION_FRAMES, FPS } from './anchor';
const d169: FilmProps = { fmt: '169', labels: false, inserts: [] };
const d916: FilmProps = { fmt: '916', labels: false, inserts: [] };
const Root: React.FC = () => (
  <>
    <Composition id="LivingEarthFilm" component={LivingEarthFilm} durationInFrames={DURATION_FRAMES} fps={FPS} width={2560} height={1440} defaultProps={d169} />
    <Composition id="LivingEarthFilm916" component={LivingEarthFilm} durationInFrames={DURATION_FRAMES} fps={FPS} width={1080} height={1920} defaultProps={d916} />
    <Composition id="LivingEarthFilm720" component={LivingEarthFilm} durationInFrames={DURATION_FRAMES} fps={FPS} width={1280} height={720} defaultProps={{ ...d169, labels: true }} />
    <Composition id="LivingEarthFilm916-540" component={LivingEarthFilm} durationInFrames={DURATION_FRAMES} fps={FPS} width={540} height={960} defaultProps={{ ...d916, labels: true }} />
  </>
);
registerRoot(Root);
