// Loads the creative director's plan (songs/run-it/shots.yaml -> src/data/shots.json via tools/shots_to_json.py).
// Same format as songs/*/shots.yaml (studio.review reads it too): fps, end, shots: [{at, t?, title, lyric?, text?, notes, intent?, sec?}].
// Shot ids are s01, s02... in order (as in studio.review). A shot's frames run from its `at` to the next shot's `at`
// (the last one to `end`, else the film's end). An empty file = no shots yet: the timeline falls back to section stand-ins.
import React from 'react';
import shotsRaw from './data/shots.json';
import { DURATION_SEC, FPS, frameOf } from './timing';

export type ShotSpec = { at: number; t?: number; title?: string; lyric?: string; text?: string; notes?: string; intent?: string; sec?: string };
export type Shot = ShotSpec & { id: string; n: number; from: number; to: number; durationInFrames: number };
export type ShotProps = { shot: Shot };

const spec = shotsRaw as { fps?: number; end?: number; shots?: ShotSpec[] };
const raw = (spec.shots ?? []).slice().sort((a, b) => a.at - b.at);
const END = spec.end ?? DURATION_SEC;

export const shots: Shot[] = raw.map((s, i) => {
  const from = frameOf(s.at);
  const to = i + 1 < raw.length ? frameOf(raw[i + 1].at) : frameOf(END);
  return { ...s, id: `s${String(i + 1).padStart(2, '0')}`, n: i + 1, from, to, durationInFrames: Math.max(1, to - from) };
});
export const shotAt = (t: number) => shots.find((s) => t * FPS >= s.from && t * FPS < s.to);

// The registry of built shots lives in ./shots/index.ts (shot id -> component). Imported lazily by the Timeline.
export type ShotRegistry = Record<string, React.ComponentType<ShotProps>>;
