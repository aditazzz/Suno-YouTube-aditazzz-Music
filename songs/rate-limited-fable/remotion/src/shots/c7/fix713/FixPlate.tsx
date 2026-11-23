// rl7_fixb: a full-stage plate from public/c7/fix713/ (the plates with the tube-family neon baked in, workers/rl7_fixb/neon/). Same box as L2Img/PlateImg.
import React from 'react';
import { Img, staticFile } from 'remotion';
export const FixPlate: React.FC<{ src: string; style?: React.CSSProperties }> = ({ src, style }) => (
  <Img src={staticFile(src)} style={{ position: 'absolute', left: 0, top: 0, width: 2560, height: 1440, ...style }} />);
