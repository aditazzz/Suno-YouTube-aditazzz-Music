// Search chats in the Claude app (mobile, 393 x 852 pt), in the look of her own app (rl_l3_phone; refs/claude_app_home_phone.png:
// the app's off-white, its grey fills, SF type, the serif for Claude's words): the search field with the typed query and Cancel;
// until results land, her Recents list (so the screen never reads empty); then the count line and the result rows (chat title,
// the matched snippet with the match marked, when). shown = how many rows have landed (results arrive top-down).
import React from 'react';
import { APP, F, MOBILE, Theme } from './tokens';
import { IcSearch, IcX } from './Icons';

export type Hit = { title: string; pre: string; match: string; post: string; when: string };
export type Recent = { title: string; when: string };

export const ChatSearch: React.FC<{ t?: Theme; query: string; caret?: boolean; count?: string; hits: Hit[]; shown?: number; scroll?: number; recents?: Recent[] }> = ({ t = MOBILE, query, caret, count, hits, shown = hits.length, scroll = 0, recents = [] }) => {
  const results = !!count;
  return (
    <div style={{ position: 'absolute', left: 0, top: 0, width: 393, height: 852, background: APP.bg, overflow: 'hidden', fontFamily: F.ios, color: APP.ink, letterSpacing: '-0.01em' }}>
      <div style={{ position: 'absolute', left: 18, right: 18, top: 56, height: 40, display: 'flex', alignItems: 'center', gap: 14 }}>
        <div style={{ flex: 1, height: 39.5, borderRadius: 20, background: APP.fill, display: 'flex', alignItems: 'center', gap: 8, padding: '0 13px', boxSizing: 'border-box' }}>
          <IcSearch s={18} c={APP.gray} w={1.8} />
          <div style={{ flex: 1, fontSize: 17, whiteSpace: 'nowrap', overflow: 'hidden', color: query ? APP.ink : APP.gray }}>
            {query || 'Search chats'}
            {caret ? <span style={{ display: 'inline-block', width: 2, height: 21, marginLeft: 1, verticalAlign: '-4px', background: '#C6613F', borderRadius: 1 }} /> : null}
          </div>
          {query ? <div style={{ width: 18, height: 18, borderRadius: 9, background: '#A9A8A3', display: 'flex', alignItems: 'center', justifyContent: 'center' }}><IcX s={12} c={APP.bg} w={2.4} /></div> : null}
        </div>
        <div style={{ fontSize: 17, color: APP.ink }}>Cancel</div>
      </div>
      <div style={{ position: 'absolute', left: 20, right: 20, top: 112, transform: `translateY(${-scroll}px)` }}>
        {results ? (
          <>
            <div style={{ fontSize: 14, color: APP.gray, margin: '4px 0 6px' }}>{count}</div>
            {hits.slice(0, Math.max(0, Math.floor(shown))).map((h, i) => (
              <div key={i} style={{ padding: '12px 0', borderBottom: '0.5px solid rgba(0,0,0,0.09)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: 10 }}>
                  <div style={{ fontSize: 16, fontWeight: 600, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{h.title}</div>
                  <div style={{ fontSize: 14, color: APP.gray, whiteSpace: 'nowrap' }}>{h.when}</div>
                </div>
                <div style={{ fontSize: 14, color: APP.greet, marginTop: 4, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {h.pre}<b data-fit="off" style={{ color: APP.ink, fontWeight: 600, background: 'rgba(204,124,94,0.2)', borderRadius: 3, padding: '0 1px' }}>{h.match}</b>{h.post}
                </div>
              </div>
            ))}
          </>
        ) : (
          <>
            <div style={{ fontSize: 14, fontWeight: 500, color: APP.gray, margin: '6px 0 4px' }}>Recents</div>
            {recents.map((r, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: 10, padding: '11px 0', borderBottom: '0.5px solid rgba(0,0,0,0.07)' }}>
                <div style={{ fontSize: 17, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{r.title}</div>
                <div style={{ fontSize: 14, color: APP.gray, whiteSpace: 'nowrap' }}>{r.when}</div>
              </div>
            ))}
          </>
        )}
      </div>
    </div>
  );
};
