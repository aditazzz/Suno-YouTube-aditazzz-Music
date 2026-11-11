import React from 'react';
import { AbsoluteFill, Audio, getInputProps, staticFile } from 'remotion';
import { LAYOUTS, LayoutCtx, Fmt, useT, useLayout } from './theme';
import { Timeline } from './Timeline';
import { PromptBar, TONE_ERROR } from './components/PromptBar';
import { MemoryMeter } from './components/MemoryMeter';
import { RecClock } from './components/RecClock';
import { beats, sectionAt, tshot } from './timing';
import { overlayAt } from './overlay';
import { EpicLayer } from './epic/Epic'; // verse 2 through the crash: the real 3D world (Fable, Nov 10)

/** The film: picture layer, then the two UI overlays that live in the scene (prompt bar, memory meter), then the song. */
const Overlays: React.FC = () => {
  const t = useT();
  const o = overlayAt(t);
  const { meter } = useLayout();
  // Keep the HUD on a stable dark plane while the bright variant wall moves underneath.
  // This follows ShotCraft's stationary text layer over moving depth layers.
  const wallStart = tshot('s26').land;
  const wallEnd = tshot('s27').land + 1.25;
  const ramp = (v: number) => Math.max(0, Math.min(1, v));
  const hudBacking = ramp((t - wallStart + 0.25) / 0.25) * ramp((wallEnd - t) / 0.35);
  // "Out of memory.": red bar, no cursor (approved frame 4). A provider can end it explicitly (barError: false, the reboot at 155.34)
  const crash = o.barError === false ? false : sectionAt(t).name === 'BREAK' || !!o.barError;
  const L = useLayout();
  return (
    <>
      {hudBacking > 0 && <div aria-hidden style={{ position: 'absolute', left: meter.x - 12, top: meter.y - 18,
        width: meter.w + 24, height: 132, borderRadius: 14, background: '#0b1020',
        opacity: 0.9 * hudBacking, pointerEvents: 'none' }} />}
      {/* 9:16 only, always on (LAYOUT_916.md): a soft radial scrim behind the meter / REC / fps rows, so the numbers read
          over the CH1 tile wall, the city's pigeons and fireworks and the FINAL shards. Invisible on dark frames. */}
      {L.fmt === '9x16' && <div data-fit="off" style={{ position: 'absolute', left: 600, top: 226, width: 420, height: 250, pointerEvents: 'none',
        background: 'radial-gradient(ellipse at 62% 45%, rgba(5,5,7,.72), rgba(5,5,7,0) 70%)', opacity: Math.min(o.meterTheme, o.meterOpacity ?? 1) }} />}
      <MemoryMeter pct={o.meterPct} theme={o.meterTheme} draw={o.meterDraw} tick={o.meterTick} opacity={o.meterOpacity ?? 1} />
      {o.recFrom !== null && <RecClock from={o.recFrom} theme={o.recTheme} opacity={o.recOpacity} stopAt={o.recStop} label={o.recLabel} dot={o.recDot} />}
      <PromptBar {...(crash ? TONE_ERROR : {})} theme={o.barTheme} lift={o.barLift} scale={o.barScale} opacity={o.barOpacity} text={o.barText} hint={o.barHint} hintOpacity={o.barHintOpacity} />
    </>
  );
};

/** The cold open is a white page and a cursor for four seconds: a soft ring leaves the cursor on every beat (the dot's rings, before
 *  there is a dot). Radius and opacity are 0 on the beat itself, so frame 0 is untouched and the loop still closes. */
const IntroPing: React.FC = () => {
  const t = useT(); const L = useLayout();
  if (L.fmt !== '16x9' || t > 4.3) return null;
  const k = L.W / 1920, fade = 1 - Math.max(0, Math.min(1, (t - 3.3) / 0.9));
  const rings = beats.filter((b) => b <= t && t - b < 1.6).map((b) => { const d = (t - b) / 1.6; const e = 1 - Math.pow(1 - d, 3);
    return { r: 34 + 660 * e, a: 0.20 * Math.min(1, d / 0.05) * Math.pow(1 - d, 1.6) * fade, key: b }; });
  return (<svg width={L.W} height={L.H} viewBox="0 0 1920 1080" style={{ position: 'absolute', left: 0, top: 0, pointerEvents: 'none' }}>
    {rings.map((g) => <circle key={g.key} cx={462} cy={542} r={g.r} fill="none" stroke="#0e0e14" strokeWidth={2.5 / k * k} opacity={g.a} />)}</svg>);
};

export const RunIt: React.FC<{ fmt: Fmt; ui?: boolean }> = ({ fmt, ui = true }) => (
  <LayoutCtx.Provider value={LAYOUTS[fmt]}>
    <AbsoluteFill style={{ background: '#000' }}>
      <Timeline />
      <EpicLayer />
      <IntroPing />
      {ui && <Overlays />}
      {/* silent picture renders pass --props '{"noAudio":true}' (the bundler skips the public/song.wav symlink); mux after */}
      {!(getInputProps() as any).noAudio && <Audio src={staticFile('song.wav')} />}
    </AbsoluteFill>
  </LayoutCtx.Provider>
);
