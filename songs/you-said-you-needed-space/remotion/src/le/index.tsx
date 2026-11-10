// The mix's Living Earth shots: their own entry point (own bundle), the blocking film with the `le` camera prop.
// Which shot is rendered is an input prop: --props='{"le":"LE3"}' (render_le.sh passes it). Slate off: these are plates.
import React from 'react';
import { Composition, registerRoot } from 'remotion';
import { BlockingFilm } from '../blocking/BlockingFilm';
import { FPS, SONG_DURATION_FRAMES } from '../systems/SceneTimeline';

const Root: React.FC = () => (
  <>
    <Composition id="LE540" component={BlockingFilm} durationInFrames={SONG_DURATION_FRAMES} fps={FPS} width={960} height={540} defaultProps={{ slate: false, le: 'LE3' }} />
    <Composition id="LE1080" component={BlockingFilm} durationInFrames={SONG_DURATION_FRAMES} fps={FPS} width={1920} height={1080} defaultProps={{ slate: false, le: 'LE3' }} />
    <Composition id="LE916" component={BlockingFilm} durationInFrames={SONG_DURATION_FRAMES} fps={FPS} width={1080} height={1920} defaultProps={{ slate: false, le: 'LE3', fmt: '916' as const }} />
    <Composition id="LE1440" component={BlockingFilm} durationInFrames={SONG_DURATION_FRAMES} fps={FPS} width={2560} height={1440} defaultProps={{ slate: false, le: 'LE3' }} />
  </>
);
registerRoot(Root);
