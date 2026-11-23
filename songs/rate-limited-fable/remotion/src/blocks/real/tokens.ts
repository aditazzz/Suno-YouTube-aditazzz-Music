// Real Claude interface tokens (rl_l3_ui, FIX4_PLAN §2e; her rule Nov 16: "a real Claude chat app or Claude Code terminal ...
// professional and recognizable"). Colours, type and spacing of the current Claude apps (claude.ai web/desktop and the
// mobile app, light and dark) as closely as we know them; no logo marks (studio rule; the director's Nov 16 ruling).
// All components lay out in CSS px of the real device (iPhone points, desktop CSS px) and are scaled as a whole by the
// shot (a real interface is made readable by framing closer, never by redrawing it bigger).

export type Theme = {
  bg: string; bg2: string; bg3: string; side: string; card: string; border: string; borderStrong: string;
  text: string; text2: string; text3: string; accent: string; accentText: string; userBubble: string; danger: string; link: string;
  bar: string; barTrack: string;
};
export const LIGHT: Theme = {
  bg: '#FAF9F5', bg2: '#F5F4EE', bg3: '#F0EEE6', side: '#F3F1EA', card: '#FFFFFF', border: 'rgba(31,30,29,0.13)', borderStrong: 'rgba(31,30,29,0.24)',
  text: '#141413', text2: '#3D3D3A', text3: '#73726C', accent: '#C6613F', accentText: '#FFFFFF', userBubble: '#F0EEE6', danger: '#B3261E', link: '#2C6BC2',
  bar: '#2C84DB', barTrack: '#E8E6DC',
};
export const DARK: Theme = {
  bg: '#262624', bg2: '#1F1E1D', bg3: '#30302E', side: '#1F1E1D', card: '#30302E', border: 'rgba(222,220,209,0.14)', borderStrong: 'rgba(222,220,209,0.26)',
  text: '#FAF9F5', text2: '#C2C0B6', text3: '#9C9A92', accent: '#C6613F', accentText: '#FFFFFF', userBubble: '#141413', danger: '#E5675B', link: '#6AA6EE',
  bar: '#4A9BEA', barTrack: '#3A3A37',
};

/** UI sans (claude.ai's grotesque; Inter is the closest face we have locally), Claude's reply serif (Tiempos-like: Charter on macOS), mono */
export const F = {
  sans: 'RLInter, Inter, -apple-system, "SF Pro Text", "Helvetica Neue", sans-serif',
  serif: 'Charter, "Iowan Old Style", Georgia, serif',
  // the iOS app's UI face (system SF Pro) and its greeting serif (closest local: New York via ui-serif, then Charter)
  appSerif: 'ui-serif, "New York", Charter, Georgia, serif',
  ios: '-apple-system, "SF Pro Text", "SF Pro Display", "Helvetica Neue", sans-serif',
  mono: '"SF Mono", Menlo, RLMono, ui-monospace, monospace',
};

/** the reset time, one wording everywhere on screens (timeline: the limit hit at 2:01, resets 6:00 AM) */
export const LIMIT = {
  app: '5-hour limit reached ∙ resets 6:00 AM',      // claude.ai / app banner above the composer
  code: '5-hour limit reached ∙ resets 6am',          // Claude Code
  codeHint: '/upgrade to increase your usage limit.',
};
// her real app (refs/claude_app_home_phone.png, her screenshot Nov 17 10:25: "My chat screen. Change what it says accordingly"):
// the model chip reads "Opus 5.5 Medium" (model dark, effort grey)
export const MODEL = 'Opus 5.5';
export const EFFORT = 'Medium';

/** the iOS Claude app, sampled from her screenshot (rl_l3_phone): a cooler off-white than the web app's cream */
export const APP = {
  bg: '#F9F9F7', btn: '#FDFDFC', fill: '#F0EFEC', ink: '#131313', greet: '#383835', icon: '#373733', gray: '#7A7974',
  spark: '#CC7C5E', kb: '#E1E1E4', key: '#FFFFFF', keyInk: '#000000', sugg: '#3C3C43',
};
/** the mobile app theme (LIGHT with the app's own sampled values) */
export const MOBILE: Theme = { ...LIGHT, bg: APP.bg, bg2: '#F4F4F2', bg3: APP.fill, card: APP.bg, userBubble: APP.fill, text: APP.ink, text2: APP.greet, text3: APP.gray };
/** the greeting the app shows on a new chat, by the time on the phone (her name as in her app) */
export const greetingAt = (h: number, name = 'Adita') =>
  h >= 5 && h < 12 ? `Good morning, ${name}` : h >= 12 && h < 17 ? `Good afternoon, ${name}` : h >= 17 && h < 22 ? `Good evening, ${name}` : h >= 22 || h < 4 ? `Up late, ${name}?` : `Still up, ${name}?`;
