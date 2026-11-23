// 10A "You said 'you're absolutely right' so many times" (cut 4, rl_l3_ui; her note #26 "once we improve those pieces of paper they
// need to be changed here too" + her standing rule: the real Claude app). Out: the wall of stamped slips. In: her phone, the real
// chat history scrolling back, faster and faster (every reply of his opens "You're absolutely right!", to anything she said, even
// 2 + 2 = 5), to a blur; then the app's chat search: she types `you're absolutely right` and the count lands: 147 chats.
// The phone is framed close enough that the type reads at phone size. No beat pulse in the scroll (it rides the line), a soft
// punch when the count lands.
import React from 'react';
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { ShotDef, ShotProps } from '../types';
import { clamp, inOutSine, lerp, outCubic } from '../../ease';
import { Phone } from '../../blocks/real/Phone';
import { MobileChat, Msg } from '../../blocks/real/ClaudeChat';
import { ChatSearch, Hit, Recent } from '../../blocks/real/ChatSearch';
import { Grain2, SoftPlate, Spill, Vig, hand } from '../../blocks/real/Scene';

const YAR = "You're absolutely right!";
const PAIRS: [string, string][] = [
  ['the logo is too big', 'I made it smaller.'],
  ["now it's too small", "Here it is a little bigger."],
  ["that's the same size", 'Apologies, here is the actual change.'],
  ['you deleted my file', 'That one is on me.'],
  ['2 + 2 = 5', 'Great catch.'],
  ['make it pop more', 'More pop, coming up.'],
  ['less pop', 'Dialling the pop back.'],
  ['the sky is green tonight', "What a beautiful observation."],
  ['you said that already', "I did say that already."],
  ['are you just agreeing with me', 'I am just agreeing with you.'],
];
const MSGS: Msg[] = [...PAIRS, ...PAIRS, ...PAIRS].flatMap(([a, b]) => [{ who: 'user', text: a } as Msg, { who: 'claude', text: `${YAR} ${b}` } as Msg]);
const HITS: Hit[] = [
  { title: 'make the font bigger', pre: '', match: YAR, post: ' Bumped it to 18 px.', when: '2:01 AM' },
  { title: 'logo v14', pre: '', match: YAR, post: ' I made it smaller.', when: '1:12 AM' },
  { title: 'is my dog a genius', pre: '', match: YAR, post: ' He does seem gifted.', when: 'Yesterday' },
  { title: 'math homework', pre: '', match: YAR, post: ' 2 + 2 = 5. Great catch.', when: 'Yesterday' },
  { title: 'Oscar speech', pre: '', match: YAR, post: ' Humble but devastating.', when: 'Sun' },
  { title: 'the sky tonight', pre: '', match: YAR, post: ' What a beautiful obs…', when: 'Sat' },
  { title: 'recipe but faster', pre: '', match: YAR, post: ' Skip the oven.', when: 'Fri' },
];
const QUERY = "you're absolutely right";
// rl_l3_phone (cut4_prep: the search screen read near-empty for ~1 s after the white-out, f4916-4940): her Recents fill the screen
// until the results land, and the search framing keeps the phone's top edge inside the frame.
// times on the timeline: her last exchange before the 2:01 limit is 'make the font bigger' (nothing after 2:01)
const RECENTS: Recent[] = [
  { title: 'make the font bigger', when: '2:01 AM' }, { title: 'logo v14', when: '1:12 AM' }, { title: 'is my dog a genius', when: 'Yesterday' },
  { title: 'math homework', when: 'Yesterday' }, { title: 'Oscar speech', when: 'Sun' }, { title: 'the sky tonight', when: 'Sat' }, { title: 'recipe but faster', when: 'Fri' },
];

const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame();
  const SW = 78;                                                // the switch to search (just past the bar's middle)
  const h = hand(f, 1, 31);
  // scroll back through the history: an accelerating ease-in, px of the thread per frame grows to a blur
  const sc = f < SW ? 2600 * Math.pow(clamp(f / SW), 2.6) : 0;
  const speed = f < SW ? (2600 * 2.6 * Math.pow(clamp(f / SW), 1.6)) / SW : 0;
  const blur = Math.min(7, speed / 14);
  const k = f < SW ? lerp(3.1, 3.3, inOutSine(clamp(f / SW))) : lerp(3.25, 3.4, inOutSine(clamp((f - SW) / (shot.dur - SW))));
  const typed = Math.floor(clamp((f - SW - 6) / 24) * QUERY.length);
  const land = SW + 34; const shown = f >= land ? 1 + clamp((f - land) / 10) * (HITS.length - 1) : 0;   // the first row lands with the count (never a bare count line)
  const punch = f >= land ? 1 + 0.012 * Math.exp(-(f - land) / 5) : 1;
  const focus = f < SW ? 470 : 186;        // search: the frame top at ~-26 pt, so the whole phone top (-10 pt) stays in frame
  return (
    <AbsoluteFill>
      <SoftPlate src="c7/apt/insert_room.jpg" x={-h.x * 0.4} y={-h.y * 0.4} />
      <Spill cx={1280} cy={720} r={1500} k={0.12} />
      <AbsoluteFill style={{ transform: `scale(${punch})` }}>
        <Phone cx={1280 + h.x} cy={720 + (426 - focus) * k + h.y} w={393 * k} rot={-0.8 + h.r} time="4:50" glare={0.06} silent>
          {f < SW
            ? <MobileChat title="logo v14" msgs={MSGS} scroll={sc} threadBlur={blur} composer={{ banner: true }} />
            : <ChatSearch query={QUERY.slice(0, typed)} caret={typed < QUERY.length || f % 16 < 9} count={f >= land ? '147 chats' : undefined} hits={HITS} shown={shown} recents={RECENTS} />}
        </Phone>
      </AbsoluteFill>
      {/* the cut to search: two frames of white-out, like the app's own transition */}
      {f >= SW && f < SW + 3 ? <AbsoluteFill style={{ background: '#FAF9F5', opacity: 1 - outCubic((f - SW) / 3) }} /> : null}
      <Vig k={0.38} />
      <Grain2 f={f} />
    </AbsoluteFill>
  );
};
export const S10_10A: ShotDef = { stage: Stage, cx916: () => 0.5 };
