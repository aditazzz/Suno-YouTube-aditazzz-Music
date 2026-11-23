// 4T (cut 5; plan §3: f1451-1712, 8.7 s; N12-N15, C03): ONE laptop-screen shot on 5E's laptop plate (the cat on the lid), one
// slow drift left -> right, no cuts. Her workarounds, same banner every time:
//   1451  a new tab: a second "Claude" tab opens, the new chat, she types "Can you make me famous?"; the limit banner.
//   1503  a private window (dark chrome, "Private browsing"): signed in as "Totally Not Adita", her avatar in a fake moustache.
//   1573  the model menu: Fable 5.2 -> Opus 5.5 ("the little brother": her N15 "switch from Fable 5.2 to Opus 5.5 or Sonnet").
//   1642  the menu again: Sonnet 5.5. The banner, again.
// A generic browser frame (no browser brand, no logos); the page is claude.ai's new-chat screen (tokens.ts look).
// The browser is laid out at BW x BH CSS px (a large-text display setting) so tabs, chips and the banner read at phone size.
import React from 'react';
import { AbsoluteFill, Img, staticFile, useCurrentFrame } from 'remotion';
import { ShotDef, ShotProps } from '../types';
import { F, LIGHT, Theme } from '../../blocks/real/tokens';
import { Composer } from '../../blocks/real/ClaudeChat';
import { IcChat, IcChevLeft, IcChevRight, IcCode, IcFolder, IcImage, IcPlus, IcRefresh, IcX } from '../../blocks/real/Icons';
import { BANNER, LADDER } from '../../blocks/real/script';
import { ScreenInsert } from '../../blocks/ScreenInsert';
import { Cam } from '../s03/_lib';
import { LAY, quadSt } from '../s05/_cut1b';
import { Grain2 } from '../../blocks/real/Scene';
import { clamp, ez, lerp, loc, pop } from './kit';
import { sinceBeat, beatPos } from '../../timing';

export const BW = 840, BH = 525;
export const T4 = { TAB: 1451, PRIV: 1503, MENU1: 1573, MENU2: 1642, END: 1712 };   // absolute
const ASK = LADDER[1].her;
const MENU_TOP = 14, ROW_H = 52;
const MODELS = [
  { m: 'Fable 5.2', d: 'For the hardest work' },
  { m: 'Opus 5.5', d: 'Deep, careful thinking' },
  { m: 'Sonnet 5.5', d: 'Smart and fast' },
  { m: 'Haiku 5.5', d: 'Fastest for quick tasks' },
];

const Lights: React.FC = () => (
  <div style={{ display: 'flex', gap: 8, padding: '0 14px 0 14px' }}>
    {['#FF5F57', '#FEBC2E', '#28C840'].map((c) => <div key={c} style={{ width: 12, height: 12, borderRadius: 6, background: c, boxShadow: 'inset 0 0 0 0.5px rgba(0,0,0,0.15)' }} />)}
  </div>
);
/** a neutral favicon (no marks): a soft clay dot */
const Fav: React.FC = () => <div style={{ width: 14, height: 14, borderRadius: 4, background: '#D97757', opacity: 0.85, flexShrink: 0 }} />;
/** the private-window glyph: a plain eye mask (generic) */
const Mask: React.FC<{ c: string }> = ({ c }) => (
  <svg width={22} height={14} viewBox="0 0 22 14"><path d="M1 4c0-2 2-3 4-3h12c2 0 4 1 4 3 0 4-3 8-6 8-2 0-3-2-4-2s-2 2-4 2C4 12 1 8 1 4z" fill={c} /><ellipse cx={6.6} cy={5.6} rx={2.2} ry={1.6} fill="#2a2a2e" /><ellipse cx={15.4} cy={5.6} rx={2.2} ry={1.6} fill="#2a2a2e" /></svg>
);

/** the browser frame. tabs: titles; active: index; slideK: the newest tab's open animation 0..1 */
export const BrowserChrome: React.FC<{ priv?: boolean; tabs: string[]; active: number; slideK?: number; url: string }> = ({ priv, tabs, active, slideK = 1, url }) => {
  const bg = priv ? '#26262A' : '#E7E5E0', tabOn = priv ? '#3A3A3F' : '#FAF9F5', ink = priv ? '#ECEBEA' : '#1F1E1D', dim = priv ? '#A9A8AE' : '#6E6D68';
  return (
    <div style={{ position: 'absolute', left: 0, top: 0, width: BW, height: 86, fontFamily: F.ios, letterSpacing: '-0.01em' }}>
      <div style={{ position: 'absolute', left: 0, right: 0, top: 0, height: 44, background: bg, display: 'flex', alignItems: 'flex-end' }}>
        <div style={{ alignSelf: 'center' }}><Lights /></div>
        {tabs.map((t, i) => {
          const last = i === tabs.length - 1; const w = 190 * (last ? slideK : 1);
          return (
            <div key={i} style={{ position: 'relative', width: w, height: 36, overflow: 'hidden', borderRadius: '10px 10px 0 0', background: i === active ? tabOn : 'transparent',
              display: 'flex', alignItems: 'center', gap: 8, padding: '0 12px', boxSizing: 'border-box', flexShrink: 0, opacity: last ? clamp(slideK * 1.5) : 1 }}>
              <Fav />
              <div style={{ flex: 1, fontSize: 15, color: i === active ? ink : dim, whiteSpace: 'nowrap', overflow: 'hidden' }}>{t}</div>
              <IcX s={13} c={dim} />
            </div>
          );
        })}
        <div style={{ alignSelf: 'center', padding: '0 10px', color: dim }}><IcPlus s={16} /></div>
        <div style={{ flex: 1 }} />
        {priv ? (
          <div style={{ alignSelf: 'center', display: 'flex', alignItems: 'center', gap: 8, marginRight: 12, padding: '4px 12px', borderRadius: 14, background: '#3A3A3F' }}>
            <Mask c="#ECEBEA" /><span style={{ fontSize: 15, fontWeight: 600, color: '#ECEBEA', whiteSpace: 'nowrap' }}>Private browsing</span>
          </div>
        ) : null}
      </div>
      <div style={{ position: 'absolute', left: 0, right: 0, top: 44, height: 42, background: tabOn, display: 'flex', alignItems: 'center', gap: 12, padding: '0 12px',
        borderBottom: `0.5px solid ${priv ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.1)'}` }}>
        <IcChevLeft s={18} c={dim} /><IcChevRight s={18} c={dim} /><IcRefresh s={16} c={dim} />
        <div style={{ flex: 1, height: 30, borderRadius: 15, background: priv ? '#1E1E22' : '#EDEBE6', display: 'flex', alignItems: 'center', padding: '0 14px' }}>
          <span style={{ fontSize: 15, color: ink, whiteSpace: 'nowrap' }}>{url}</span>
        </div>
        <div style={{ width: 26, height: 26, borderRadius: 13, background: priv ? '#4A4A50' : '#CFCBC2' }} />
      </div>
    </div>
  );
};

/** her avatar: her photo, or (alias) her photo in a fake moustache */
const Avatar: React.FC<{ d: number; stache?: boolean }> = ({ d, stache }) => (
  <div style={{ position: 'relative', width: d, height: d, borderRadius: d / 2, overflow: 'hidden', flexShrink: 0, background: '#3D3D3A' }}>
    <Img src={staticFile('l3/av/her.jpg')} style={{ width: d, height: d, objectFit: 'cover' }} />
    {stache ? (
      <svg style={{ position: 'absolute', left: d * 0.2, top: d * 0.56, width: d * 0.6, height: d * 0.22 }} viewBox="0 0 60 22">
        <path d="M30 6c-4-6-12-6-17-2-4 3-7 2-10-1 0 7 6 12 13 11 6-1 10-3 14-6 4 3 8 5 14 6 7 1 13-4 13-11-3 3-6 4-10 1-5-4-13-4-17 2z" fill="#2B1B12" stroke="#120b07" strokeWidth={1} />
      </svg>
    ) : null}
  </div>
);

/** claude.ai's new-chat screen, narrow (the sidebar open): greeting, composer with the limit banner, the model menu */
export const ClaudeNewChat: React.FC<{
  t?: Theme; name: string; plan: string; stache?: boolean; typed: string; caret: boolean; model: string; banner: number;
  menu?: number; hover?: number; checked?: number; w?: number; h?: number;
}> = ({ t = LIGHT, name, plan, stache, typed, caret, model, banner, menu = 0, hover = -1, checked = 0, w = BW, h = BH - 86 }) => {
  const sw = 230;
  return (
    <div style={{ position: 'absolute', left: 0, top: 86, width: w, height: h, background: t.bg, overflow: 'hidden', fontFamily: F.sans }}>
      <div style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: sw, background: t.side, borderRight: `0.5px solid ${t.border}`, padding: '14px 10px 0', boxSizing: 'border-box' }}>
        {[['New chat', true], ['Chats'], ['Projects'], ['Artifacts'], ['Code']].map(([l, n]) => (
          <div key={l as string} style={{ display: 'flex', alignItems: 'center', gap: 10, height: 34, padding: '0 6px', fontSize: 15, color: t.text, fontWeight: n ? 600 : 400 }}>
            {n ? <div style={{ width: 22, height: 22, borderRadius: 11, background: t.accent, display: 'flex', alignItems: 'center', justifyContent: 'center' }}><IcPlus s={15} c="#fff" w={2.2} /></div>
              : <div style={{ width: 22, display: 'flex', justifyContent: 'center', color: t.text2 }}>{l === 'Chats' ? <IcChat s={17} /> : l === 'Projects' ? <IcFolder s={17} /> : l === 'Artifacts' ? <IcImage s={17} /> : <IcCode s={17} />}</div>}
            <span>{l}</span>
          </div>
        ))}
        <div style={{ position: 'absolute', left: 8, right: 8, bottom: 10, display: 'flex', alignItems: 'center', gap: 10, padding: 6, borderRadius: 10, background: stache ? t.bg3 : undefined }}>
          <Avatar d={46} stache={stache} />
          <div style={{ lineHeight: 1.25, minWidth: 0 }}>
            <div style={{ fontSize: 15, color: t.text, fontWeight: 600, whiteSpace: 'nowrap' }}>{name}</div>
            <div style={{ fontSize: 14, color: t.text3, whiteSpace: 'nowrap' }}>{plan}</div>
          </div>
        </div>
      </div>
      {/* the greeting + composer, centred in the page */}
      <div data-fit={menu > 0 ? 'overlap-ok' : undefined} style={{ position: 'absolute', left: sw, right: 0, top: 70, textAlign: 'center', fontFamily: F.serif, fontSize: 34, color: t.text2, letterSpacing: '-0.01em' }}>
        <span>Up late, {name}?</span>
      </div>
      <div style={{ position: 'absolute', left: sw + 24, right: 24, top: 150 }}>
        <Composer t={t} text={typed} caret={caret} banner={banner > 0 ? BANNER : false} disabled model={model} />
      </div>
      {/* the model menu: opens up from the chip, the current model checked, the hover row tinted */}
      {menu > 0 ? (
        <div style={{ position: 'absolute', right: 40, top: MENU_TOP, width: 300, transformOrigin: '80% 100%',
          transform: `scale(${0.94 + 0.06 * menu})`, opacity: clamp(menu * 1.4), background: t.card, borderRadius: 14, border: `0.5px solid ${t.borderStrong}`,
          boxShadow: '0 12px 32px rgba(0,0,0,0.16), 0 2px 6px rgba(0,0,0,0.06)', padding: 6, zIndex: 20 }}>
          {MODELS.map((m, i) => (
            <div key={m.m} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '7px 10px', borderRadius: 9, background: i === hover ? t.bg3 : undefined }}>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 16, color: t.text, fontWeight: 500, whiteSpace: 'nowrap' }}>{m.m}</div>
                <div style={{ fontSize: 14, color: t.text3, whiteSpace: 'nowrap' }}>{m.d}</div>
              </div>
              {i === checked ? <svg width={18} height={18} viewBox="0 0 20 20"><path d="M4.5 10.5l3.5 3.5 7.5-8" fill="none" stroke={t.accent} strokeWidth={2.2} strokeLinecap="round" strokeLinejoin="round" /></svg> : null}
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
};

/** the macOS pointer */
const Pointer: React.FC<{ x: number; y: number; press?: number }> = ({ x, y, press = 0 }) => (
  <svg style={{ position: 'absolute', left: x, top: y, zIndex: 40, transform: `scale(${1 - 0.12 * press})`, transformOrigin: '0 0' }} width={20} height={28} viewBox="0 0 20 28">
    <path d="M1.5 1.5v21.5l5.4-5.2 3.6 8.5 3.5-1.5-3.6-8.3h7.6z" fill="#000" stroke="#fff" strokeWidth={1.4} strokeLinejoin="round" />
  </svg>
);

/** the whole screen at local frame f (cues local) */
export const Screen4T: React.FC<{ f: number; c: { TAB: number; PRIV: number; MENU1: number; MENU2: number } }> = ({ f, c }) => {
  const priv = f >= c.PRIV;
  // stage A: the new tab
  const slide = ez(f, c.TAB + 3, c.TAB + 11);
  // typing: in each window the ask types in over ~18 frames after the page loads
  const typeStart = priv ? c.PRIV + 12 : c.TAB + 14;
  const typed = ASK.slice(0, Math.floor(clamp((f - typeStart) / 18) * ASK.length));
  const banner = clamp((f - (typeStart + 20)) / 3);         // the banner is there as soon as she tries (tap send)
  // the model menu, twice: open, hover down one, click, close; the chip changes; the banner blinks back in
  const menuAt = (m0: number, from: number) => {
    const open = m0 + 6, hov = m0 + 16, pick = m0 + 24, close = m0 + 27;
    const k = f < open ? 0 : f < close ? ez(f, open, open + 5) : 1 - ez(f, close, close + 4);
    return { k, hover: f >= hov ? from + 1 : from, picked: f >= pick, close };
  };
  const m1 = menuAt(c.MENU1, 0), m2 = menuAt(c.MENU2, 1);
  const inM2 = f >= c.MENU2;
  const model = inM2 ? (m2.picked ? 'Sonnet 5.5' : 'Opus 5.5') : m1.picked ? 'Opus 5.5' : 'Fable 5.2';
  const menu = inM2 ? m2 : m1;
  const blink = f >= c.MENU1 + 27 && f < c.MENU1 + 31 ? 0 : f >= c.MENU2 + 27 && f < c.MENU2 + 31 ? 0 : 1;   // the banner re-asserts after each switch
  // the window open (Cmd-Shift-N): the private window zooms in from 0.92
  const win = priv ? ez(f, c.PRIV, c.PRIV + 7) : 1;
  // the pointer: to the chip for the menus
  const chip = { x: 705, y: 86 + 252 };
  const row = (i: number) => ({ x: BW - 190, y: 86 + MENU_TOP + 6 + 24 + i * ROW_H });
  let p = { x: BW * 0.62, y: BH * 0.82 }, press = 0;
  if (f >= c.MENU1 - 4) {
    const m0 = inM2 ? c.MENU2 : c.MENU1; const from = inM2 ? 1 : 0;
    const a = ez(f, m0 - 4, m0 + 4), b = ez(f, m0 + 12, m0 + 20);
    const r0 = row(from), r1 = row(from + 1);
    p = { x: lerp(lerp(BW * 0.62, chip.x, a), lerp(r0.x, r1.x, b), ez(f, m0 + 6, m0 + 12)), y: lerp(lerp(BH * 0.82, chip.y, a), lerp(r0.y, r1.y, b), ez(f, m0 + 6, m0 + 12)) };
    press = (f >= m0 + 4 && f < m0 + 7) || (f >= m0 + 23 && f < m0 + 26) ? 1 : 0;
  }
  const page = (
    <ClaudeNewChat t={LIGHT} name={priv ? 'Totally Not Adita' : 'Adita'} plan={priv ? 'Free plan' : 'Max plan'} stache={priv}
      typed={typed} caret={typed.length < ASK.length || f % 16 < 10} model={model} banner={banner * blink} menu={menu.k} hover={menu.hover} checked={inM2 ? 1 : 0} />
  );
  return (
    <div style={{ position: 'absolute', left: 0, top: 0, width: BW, height: BH, background: '#1d1d1f', overflow: 'hidden' }}>
      {/* the normal window stays behind the private one */}
      <div data-fit={priv ? 'overlap-ok' : undefined} style={{ position: 'absolute', inset: 0, filter: priv ? `brightness(${(1 - 0.45 * win).toFixed(3)}) blur(${win.toFixed(2)}px)` : undefined }}>
        <BrowserChrome tabs={['Claude', 'Claude']} active={f >= c.TAB + 3 ? 1 : 0} slideK={slide} url="claude.ai/new" />
        {priv ? <ClaudeNewChat t={LIGHT} name="Adita" plan="Max plan" typed={ASK} caret={false} model="Fable 5.2" banner={1} /> : page}
      </div>
      {priv ? (
        <div style={{ position: 'absolute', inset: 0, transformOrigin: '50% 50%', transform: `scale(${0.92 + 0.08 * win})`, opacity: clamp(win * 1.6), borderRadius: 10, overflow: 'hidden',
          boxShadow: '0 20px 50px rgba(0,0,0,0.5)' }}>
          <BrowserChrome priv tabs={['Claude']} active={0} url="claude.ai/new" />
          {page}
        </div>
      ) : null}
      {priv ? <Stache f={f} c={c} /> : null}
      {f >= c.MENU1 - 4 ? <Pointer x={p.x} y={p.y} press={press} /> : null}
    </div>
  );
};
// rl7_ra (her H7.16, frame 1579: "Have a mustache cut out floating/dancing here over the screen where you can still see what's on the
// screen (empty area)"): her disguise as a die-cut paper handlebar mustache, floating in the empty band under the composer of the private
// window, dancing on the beat (a hop + tilt on each beat, squash on landing, a slow sway between). Never over the UI text.
const STACHE_PATH = 'M100,24 C92,11 72,7 58,17 C46,26 37,38 22,37 C12,36 7,29 9,21 C4,25 2,33 6,40 C11,49 22,53 33,52 C52,51 70,44 84,40 C92,38 97,36 100,35 C103,36 108,38 116,40 C130,44 148,51 167,52 C178,53 189,49 194,40 C198,33 196,25 191,21 C193,29 188,36 178,37 C163,38 154,26 142,17 C128,7 108,11 100,24 Z';
const Stache: React.FC<{ f: number; c: { PRIV: number } }> = ({ f, c }) => {
  const abs = 1451 + f; const t = abs / 30;
  const k = clamp((f - c.PRIV - 6) / 8);                     // pops in after the private window opens (scale + fade, 8 f)
  if (k <= 0) return null;
  const sb = sinceBeat(t); const u = sb === Infinity ? 1 : Math.min(1, sb / 0.29);   // 0..1 through the beat's first half
  const hop = Math.sin(Math.PI * u) * (1 - u) * 1.6;            // a quick hop off each beat
  const beatN = Math.floor(beatPos(t)); const tilt = (beatN % 2 ? 1 : -1) * 9 * Math.sin(Math.PI * Math.min(1, u * 1.2));
  const squash = u < 0.12 ? 1 - 0.1 * (1 - u / 0.12) : 1;         // lands on the beat: a little squash
  const sway = 6 * Math.sin(t * 2 * Math.PI * 0.4), bob = 3 * Math.sin(t * 2 * Math.PI * 0.8);
  const W = 176, H = 61, x = 535 + sway, y = 428 - 14 * hop + bob;
  return (
    <div style={{ position: 'absolute', left: x - W / 2, top: y - H / 2, width: W, height: H, opacity: k,
      transform: `rotate(${tilt.toFixed(2)}deg) scale(${(0.6 + 0.4 * k) * (2 - squash)}, ${(0.6 + 0.4 * k) * squash})`, transformOrigin: '50% 70%',
      filter: 'drop-shadow(0 6px 5px rgba(0,0,0,0.28)) drop-shadow(0 1px 0 rgba(0,0,0,0.25))' }}>
      <svg viewBox="0 0 200 60" width={W} height={H} style={{ display: 'block' }}>
        <path d={STACHE_PATH} fill="#fbf8f2" transform="translate(100 30) scale(1.06) translate(-100 -30)" />
        <path d={STACHE_PATH} fill="#1c1512" />
        <path d="M60 24 C75 18 88 22 98 30 M140 24 C125 18 112 22 102 30" stroke="#3a2c25" strokeWidth={1.6} fill="none" opacity={0.7} />
      </svg>
    </div>
  );
};

// staging on 5E's laptop plate (fix2/end/t16.jpg, the cat baked on the lid; its paw cut-out is NOT drawn over the screen: it hid the UI)
const SC = quadSt(LAY.T16.screen_corners);
const K = 2560 / 2880;
const MID = { x: (SC[0][0] + SC[1][0] + SC[2][0] + SC[3][0]) / 4, y: (SC[0][1] + SC[1][1] + SC[2][1] + SC[3][1]) / 4 };
const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame();
  const c = { TAB: loc(shot, T4.TAB), PRIV: loc(shot, T4.PRIV), MENU1: loc(shot, T4.MENU1), MENU2: loc(shot, T4.MENU2) };
  // one slow drift left -> right across the whole shot (§2f: eased, <= 3% while text is read)
  const e = ez(f, 0, shot.dur - 1);
  const s = lerp(2.08, 2.12, e), cx = lerp(MID.x - 40, MID.x + 40, e), cy = MID.y;
  return (
    <AbsoluteFill style={{ background: '#0d0a08' }}>
      <Cam cx={cx} cy={cy} s={s}>
        <Img src={staticFile('fix2/end/t16.jpg')} style={{ position: 'absolute', width: 2560, height: 1440 }} />
        <ScreenInsert corners={SC} w={BW} h={BH} glare={0.04} light={0.9}><Screen4T f={f} c={c} /></ScreenInsert>
      </Cam>
      <Grain2 f={f} />
    </AbsoluteFill>
  );
};
export const C5_4T: ShotDef = { stage: Stage, cx916: () => 0.5 };
