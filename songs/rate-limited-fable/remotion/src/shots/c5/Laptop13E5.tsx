// 13E laptop screen (cut 5; plan §3: f6358-6598; N50, C11): 6:02 AM, the limit reset, her first prompt of the day "make me MORE
// famous" and his answer "I can help you with a strategy." (the Look What I Can Do echo), chip Fable 5.2. A drop-in for
// blocks/real/Dropins Laptop13E with the same props: <Laptop13E5 f={f} start={..} zoom={2.4} />. The reply streams in from
// `start` and then holds (>= 3 s on screen, plan: "laptop text holds >= 3 s").
import React from 'react';
import { DesktopChat } from '../../blocks/real/ClaudeChat';
import { LAPTOP, MenuBar } from '../../blocks/real/Dropins';
import { CHIP, MORNING } from '../../blocks/real/script';

const RECENTS = ['make me MORE famous', 'Help writing a song', 'make the font bigger', 'Oscar speech', 'is my dog a genius'];
const Zoom: React.FC<{ zoom: number; children: (w: number, h: number, sidebar: boolean) => React.ReactNode }> = ({ zoom, children }) => {
  const w = LAPTOP.w / zoom, h = (LAPTOP.h - 37) / zoom;
  return (
    <div style={{ position: 'absolute', left: 0, top: 37, width: w, height: h, transformOrigin: '0 0', transform: zoom !== 1 ? `scale(${zoom})` : undefined }}>
      {children(w, h, zoom < 1.6)}
    </div>
  );
};
export const Laptop13E5: React.FC<{ f: number; start?: number; cps?: number; clock?: string; zoom?: number }> = ({ f, start = 20, cps = 30, clock = 'Tue 6:02 AM', zoom = 1 }) => {
  const chars = Math.max(0, ((f - start) / 30) * cps);
  return (
    <div style={{ position: 'absolute', left: 0, top: 0, width: LAPTOP.w, height: LAPTOP.h, overflow: 'hidden' }}>
      <Zoom zoom={zoom}>{(w, h, sb) => (
        <DesktopChat w={w} h={h} sidebar={sb} col={Math.min(720, w - 48)} title="make me MORE famous" recents={RECENTS}
          msgs={[{ who: 'user', text: MORNING.her }, ...(f >= start ? [{ who: 'claude' as const, text: MORNING.claude, chars }] : [])]}
          composer={{ placeholder: 'Reply to Claude…', model: CHIP.early }} />
      )}</Zoom>
      <MenuBar clock={clock} />
    </div>
  );
};
