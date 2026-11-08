import React, {useEffect, useLayoutEffect, useRef, useState} from 'react';
import {AbsoluteFill, Audio, continueRender, delayRender, getStaticFiles, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {renderFrame} from './frame';
import type {Fmt} from './story';

const FACES: [string, string][] = [
  ['InterDisplayBlack', 'fonts/InterDisplay-Black.otf'],
  ['InterDisplayBold', 'fonts/InterDisplay-Bold.otf'],
  ['InterSemi', 'fonts/Inter-SemiBold.otf'],
  ['JBMono', 'fonts/JBMono-400.ttf'],
  ['JBMonoBold', 'fonts/JBMono-700.ttf'],
];
let fontsReady: Promise<void> | null = null;
const loadFonts = () =>
  (fontsReady ??= Promise.all(
    FACES.map(async ([family, file]) => {
      const f = new FontFace(family, `url(${staticFile(file)})`);
      await f.load();
      document.fonts.add(f);
    }),
  ).then(() => undefined));

export const Film: React.FC<{fmt: Fmt; preview?: boolean}> = ({fmt, preview}) => {
  const frame = useCurrentFrame();
  const {width, height, fps} = useVideoConfig();
  const canvas = useRef<HTMLCanvasElement>(null);
  const [handle] = useState(() => delayRender('fonts'));
  const [ready, setReady] = useState(false);
  useEffect(() => {
    loadFonts().then(() => {
      setReady(true);
      continueRender(handle);
    });
  }, [handle]);
  useLayoutEffect(() => {
    const ctx = canvas.current?.getContext('2d');
    if (!ready || !ctx) return;
    renderFrame(ctx, frame / fps, width, height, fmt, frame);
  }, [frame, ready, width, height, fps, fmt]);
  const hasAudio = preview && getStaticFiles().some((f) => f.name === 'audio.wav');
  return (
    <AbsoluteFill style={{backgroundColor: '#000'}}>
      <canvas ref={canvas} width={width} height={height} style={{width: '100%', height: '100%'}} />
      {hasAudio ? <Audio src={staticFile('audio.wav')} /> : null}
    </AbsoluteFill>
  );
};
