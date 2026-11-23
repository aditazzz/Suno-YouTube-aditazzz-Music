// Line icons in the style the Claude apps use (thin rounded strokes, 20 px grid). Our own drawings, no marks.
import React from 'react';

type P = { s?: number; c?: string; w?: number; style?: React.CSSProperties };
const I: React.FC<P & { children: React.ReactNode; fill?: string }> = ({ s = 20, c = 'currentColor', w = 1.6, style, children, fill = 'none' }) => (
  <svg width={s} height={s} viewBox="0 0 20 20" fill={fill} stroke={c} strokeWidth={w} strokeLinecap="round" strokeLinejoin="round" style={{ display: 'block', flexShrink: 0, ...style }}>{children}</svg>
);
export const IcPlus: React.FC<P> = (p) => <I {...p}><path d="M10 4v12M4 10h12" /></I>;
export const IcSliders: React.FC<P> = (p) => <I {...p}><path d="M3.5 6.5h7M14.5 6.5h2M3.5 13.5h2M9.5 13.5h7" /><circle cx="12.5" cy="6.5" r="2" /><circle cx="7.5" cy="13.5" r="2" /></I>;
export const IcClock: React.FC<P> = (p) => <I {...p}><circle cx="10" cy="10" r="6.5" /><path d="M10 6.5V10l2.5 1.5" /></I>;
export const IcChevDown: React.FC<P> = (p) => <I {...p}><path d="M6 8l4 4 4-4" /></I>;
export const IcChevLeft: React.FC<P> = (p) => <I {...p}><path d="M12.5 4.5L7 10l5.5 5.5" /></I>;
export const IcChevRight: React.FC<P> = (p) => <I {...p}><path d="M7.5 4.5L13 10l-5.5 5.5" /></I>;
export const IcArrowUp: React.FC<P> = (p) => <I {...p}><path d="M10 15.5v-11M5.5 9L10 4.5 14.5 9" /></I>;
export const IcMic: React.FC<P> = (p) => <I {...p}><rect x="7.5" y="3" width="5" height="9" rx="2.5" /><path d="M5 9.5a5 5 0 0 0 10 0M10 14.5V17" /></I>;
export const IcWave: React.FC<P> = (p) => <I {...p}><path d="M4 8.5v3M7 6v8M10 4v12M13 6.5v7M16 8.5v3" /></I>;
export const IcMenu: React.FC<P> = (p) => <I {...p}><path d="M3.5 7h13M3.5 13h8" /></I>;
export const IcCompose: React.FC<P> = (p) => <I {...p}><path d="M9 4H5.5A1.5 1.5 0 0 0 4 5.5v9A1.5 1.5 0 0 0 5.5 16h9a1.5 1.5 0 0 0 1.5-1.5V11" /><path d="M14 3.5l2.5 2.5L10 12.5H7.5V10z" /></I>;
export const IcSearch: React.FC<P> = (p) => <I {...p}><circle cx="9" cy="9" r="5" /><path d="M13 13l3.5 3.5" /></I>;
export const IcCopy: React.FC<P> = (p) => <I {...p}><rect x="7" y="7" width="9" height="9" rx="1.8" /><path d="M13 7V5.5A1.5 1.5 0 0 0 11.5 4h-6A1.5 1.5 0 0 0 4 5.5v6A1.5 1.5 0 0 0 5.5 13H7" /></I>;
export const IcThumbUp: React.FC<P> = (p) => <I {...p}><path d="M6.5 9l3-5.5c1 0 2 .8 1.8 2L11 8h4a1.5 1.5 0 0 1 1.4 1.9l-1.5 5A1.5 1.5 0 0 1 13.5 16H6.5zM3.5 9h3v7h-3z" /></I>;
export const IcThumbDown: React.FC<P> = (p) => <I {...p}><g transform="rotate(180 10 10)"><path d="M6.5 9l3-5.5c1 0 2 .8 1.8 2L11 8h4a1.5 1.5 0 0 1 1.4 1.9l-1.5 5A1.5 1.5 0 0 1 13.5 16H6.5zM3.5 9h3v7h-3z" /></g></I>;
export const IcRetry: React.FC<P> = (p) => <I {...p}><path d="M15.5 10a5.5 5.5 0 1 1-1.6-3.9M15.5 4v3h-3" /></I>;
export const IcX: React.FC<P> = (p) => <I {...p}><path d="M5.5 5.5l9 9M14.5 5.5l-9 9" /></I>;
export const IcSidebar: React.FC<P> = (p) => <I {...p}><rect x="3" y="4" width="14" height="12" rx="2" /><path d="M8 4v12" /></I>;
export const IcChat: React.FC<P> = (p) => <I {...p}><path d="M4 5.5A1.5 1.5 0 0 1 5.5 4h9A1.5 1.5 0 0 1 16 5.5v6a1.5 1.5 0 0 1-1.5 1.5H9l-3.5 3v-3h0A1.5 1.5 0 0 1 4 11.5z" /></I>;
export const IcFolder: React.FC<P> = (p) => <I {...p}><path d="M3.5 6A1.5 1.5 0 0 1 5 4.5h3l1.5 2H15A1.5 1.5 0 0 1 16.5 8v6.5A1.5 1.5 0 0 1 15 16H5a1.5 1.5 0 0 1-1.5-1.5z" /></I>;
export const IcCode: React.FC<P> = (p) => <I {...p}><path d="M7.5 6L3.5 10l4 4M12.5 6l4 4-4 4" /></I>;
export const IcRefresh: React.FC<P> = (p) => <I {...p}><path d="M15.5 8.5A5.8 5.8 0 0 0 4.7 7M4.5 11.5A5.8 5.8 0 0 0 15.3 13M4.5 3.8V7h3.2M15.5 16.2V13h-3.2" /></I>;
export const IcFile: React.FC<P> = (p) => <I {...p}><path d="M11.5 3.5H6A1.5 1.5 0 0 0 4.5 5v10A1.5 1.5 0 0 0 6 16.5h8a1.5 1.5 0 0 0 1.5-1.5V7.5z" /><path d="M11.5 3.5v4h4M7.5 11h5M7.5 13.5h3.5" /></I>;
export const IcHeart: React.FC<P & { filled?: boolean }> = ({ filled, ...p }) => <I {...p} fill={filled ? p.c ?? 'currentColor' : 'none'}><path d="M10 16s-6-3.6-6-8a3.2 3.2 0 0 1 6-1.6A3.2 3.2 0 0 1 16 8c0 4.4-6 8-6 8z" /></I>;
export const IcSend: React.FC<P> = (p) => <I {...p}><path d="M17 3L8.5 11.5M17 3l-5 14-3.5-5.5L3 8z" /></I>;
export const IcCamera: React.FC<P> = (p) => <I {...p}><rect x="3" y="5.5" width="14" height="10.5" rx="2.2" /><circle cx="10" cy="10.7" r="3" /><path d="M7.5 5.5L8.5 3.8h3l1 1.7" /></I>;
export const IcImage: React.FC<P> = (p) => <I {...p}><rect x="3.5" y="3.5" width="13" height="13" rx="2.5" /><circle cx="8" cy="8" r="1.4" /><path d="M16.5 13l-4-4-7.5 7.5" /></I>;
export const IcDots: React.FC<P> = (p) => <I {...p} fill={p.c ?? 'currentColor'}><circle cx="5" cy="10" r="1.3" /><circle cx="10" cy="10" r="1.3" /><circle cx="15" cy="10" r="1.3" /></I>;
export const IcPhone: React.FC<P> = (p) => <I {...p}><path d="M5 3.5h2.5l1.3 3.2-1.6 1.1a8.4 8.4 0 0 0 5 5l1.1-1.6 3.2 1.3V15A1.5 1.5 0 0 1 15 16.5 11.5 11.5 0 0 1 3.5 5 1.5 1.5 0 0 1 5 3.5z" /></I>;
export const IcVideo: React.FC<P> = (p) => <I {...p}><rect x="2.5" y="5.5" width="10.5" height="9" rx="2" /><path d="M13 8.5l4.5-2.5v8L13 11.5" /></I>;
export const IcInfo: React.FC<P> = (p) => <I {...p}><circle cx="10" cy="10" r="6.5" /><path d="M10 9v4.5M10 6.5v.2" /></I>;
export const IcGear: React.FC<P> = (p) => <I {...p}><circle cx="10" cy="10" r="2.5" /><path d="M10 2.8v2M10 15.2v2M2.8 10h2M15.2 10h2M4.9 4.9l1.4 1.4M13.7 13.7l1.4 1.4M4.9 15.1l1.4-1.4M13.7 6.3l1.4-1.4" /></I>;
