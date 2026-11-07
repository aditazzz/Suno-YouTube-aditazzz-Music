import React from 'react';
import {Composition} from 'remotion';
import {Film} from './Film';
import {FPS, SONG_END} from './data';

// the silent masters run to the end of the song plus the studio tail (song.yaml `tail`); the end card is drawn by
// scene.py on top of the black after the cut, so the picture length only has to cover it
const TAIL = 4.0;
const frames = Math.ceil((SONG_END + TAIL) * FPS);
type Props = {width?: number; height?: number; preview?: boolean};
const Wide: React.FC<Props> = (p) => <Film fmt="16x9" preview={p.preview} />;
const Tall: React.FC<Props> = (p) => <Film fmt="9x16" preview={p.preview} />;

export const Root: React.FC = () => (
  <>
    <Composition
      id="Wall16x9"
      component={Wide}
      durationInFrames={frames}
      fps={FPS}
      width={1920}
      height={1080}
      defaultProps={{preview: true} as Props}
      calculateMetadata={({props}) => ({width: Number(props.width ?? 1920), height: Number(props.height ?? 1080)})}
    />
    <Composition
      id="Wall9x16"
      component={Tall}
      durationInFrames={frames}
      fps={FPS}
      width={1080}
      height={1920}
      defaultProps={{preview: true} as Props}
      calculateMetadata={({props}) => ({width: Number(props.width ?? 1080), height: Number(props.height ?? 1920)})}
    />
  </>
);
