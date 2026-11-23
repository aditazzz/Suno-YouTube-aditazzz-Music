// The film: every shot from src/data/shots.json as a <Sequence> on its own frames, cut where the shot list says
// (on the beat grid). One stage (2560x1440) per shot; 16:9 scales it to the output, 9:16 scales it to 1920 tall and
// crops around the shot's cx916. Then each shot's screen layer, then the caption layer (off by default).
import React from 'react';
import { AbsoluteFill, Audio, Freeze, Img, Sequence, staticFile, useCurrentFrame, useVideoConfig } from 'remotion';
import { V8 } from './v8';   // rl8_assemble: v8 flag (off = the 05:03 film exactly)
import { srcFrame, GradeDefs, gradeFilter } from './shots/c7/kit/edit';   // rl7_final: cut 7 edit layer (holds + grade)
import { FmtCtx, Fmt, STAGE_H, STAGE_W } from './theme';
import { SHOTS, Shot } from './timing';
import { shotDef } from './shots';
import { BLOCKS, c7Def } from './shots/c7';   // rl7_ra: cut 7 (PLAN7), cut={7}
import { CaptionLayer } from './blocks/Caption';
import { clamp } from './ease';

export type FilmProps = { fmt: Fmt; preview?: boolean; noAudio?: boolean; captions?: boolean; slate?: boolean; cut?: number };

const ShotFrame: React.FC<{ i: number; fmt: Fmt; slate: boolean; cut?: number }> = ({ i, fmt, slate, cut }) => {
  const shot: Shot = cut === 7 ? BLOCKS[i] : SHOTS[i]; const def = cut === 7 ? c7Def(shot) : shotDef(shot.id); const f = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const Stage = def.stage, Screen = def.screen;
  let stageTf: string;
  if (fmt === '16x9') stageTf = `scale(${width / STAGE_W})`;
  else {
    const s = height / STAGE_H, sw = STAGE_W * s;
    const cx = def.cx916 ? def.cx916(f, shot) : shot.cx916;
    const tx = clamp(width / 2 - cx * sw, width - sw, 0);
    stageTf = `translateX(${tx.toFixed(2)}px) scale(${s})`;
  }
  const scrW = fmt === '16x9' ? STAGE_W : 1080, scrH = fmt === '16x9' ? STAGE_H : 1920;
  const props = { shot, fmt, slate };
  return (
    <AbsoluteFill style={{ overflow: 'hidden' }}>
      <div style={{ position: 'absolute', left: 0, top: 0, width: STAGE_W, height: STAGE_H, transform: stageTf, transformOrigin: '0 0', overflow: 'hidden' }}>
        <Stage {...props} />
      </div>
      {Screen ? (
        <div style={{ position: 'absolute', left: 0, top: 0, width: scrW, height: scrH, transform: `scale(${width / scrW})`, transformOrigin: '0 0' }}>
          <Screen {...props} />
        </div>
      ) : null}
    </AbsoluteFill>
  );
};

export const Film: React.FC<FilmProps> = ({ fmt, noAudio = false, captions = false, slate = false, cut = 6 }) => {
  const LIST: Shot[] = cut === 7 ? BLOCKS : SHOTS;
  const { width } = useVideoConfig();
  const scrW = fmt === '16x9' ? STAGE_W : 1080, scrH = fmt === '16x9' ? STAGE_H : 1920;
  const f = useCurrentFrame(); const src = cut === 7 ? srcFrame(f) : f;
  // rl8_assemble (v8 only): rl8_date2's approved DATE shot = B34 at 3379-3552 (B33 ends at 3378), a baked 2560x1440 image sequence (visor words
  // baked, locked camera): drawn full frame, no B33 grade, nothing under it. Files: public rl8date2/f<N>.jpg (overlay folder -> build/rl8/rl8_date2/frames_v8).
  const date8 = V8 && cut === 7 && fmt === '16x9' && src >= 3379 && src <= 3552;
  if (date8) return (
    <FmtCtx.Provider value={fmt}>
      <AbsoluteFill style={{ background: '#000' }}>
        <Img src={staticFile(`rl8date2/f${Math.round(src)}.jpg`)} style={{ position: 'absolute', left: 0, top: 0, width: '100%', height: '100%' }} />
        {noAudio ? null : <Audio src={staticFile('song.wav')} />}
      </AbsoluteFill>
    </FmtCtx.Provider>
  );
  return (
    <FmtCtx.Provider value={fmt}>
      <AbsoluteFill style={{ background: '#000' }}>
        {cut === 7 ? <GradeDefs f={src} /> : null}
        <Freeze frame={src} active={src !== f}>
          <AbsoluteFill style={{ filter: cut === 7 ? gradeFilter(src) : undefined }}>
            {LIST.map((s, i) => (
              <Sequence key={s.id} from={s.from} durationInFrames={s.dur} name={`${s.id} ${s.plate ?? 'insert'}`}>
                <ShotFrame i={i} fmt={fmt} slate={slate} cut={cut} />
              </Sequence>
            ))}
          </AbsoluteFill>
        </Freeze>
        <div style={{ position: 'absolute', left: 0, top: 0, width: scrW, height: scrH, transform: `scale(${width / scrW})`, transformOrigin: '0 0' }}>
          <CaptionLayer on={captions} fmt={fmt} />
        </div>
        {noAudio ? null : <Audio src={staticFile('song.wav')} />}
      </AbsoluteFill>
    </FmtCtx.Provider>
  );
};
