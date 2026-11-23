// The film's screen copy (rl5_c owns this text; CUT5_PLAN §6). Her words win: ★ lines are hers word for word.
// Cut 5: her requests get bigger all night; every Claude screen shares this one thread.
import { Msg } from './ClaudeChat';

/** the limit wording, one everywhere (tokens.LIMIT.app is the same string) */
export const BANNER = '5-hour limit reached ∙ resets 6:00 AM';
/** the model chip: Fable 5.2 at 1G and 13E; Sonnet 5.5 from 4E to 10A (her "switch to Opus 5.5 or Sonnet", N15) */
export const CHIP = { early: 'Fable 5.2', night: 'Sonnet 5.5' };

/** her requests in order (§6). claude = his answer where there is one */
export const LADDER: { her: string; claude?: string; parcel: string }[] = [
  { her: 'Hey Claude? Can you help me write a song?', claude: "Sure, let's go!", parcel: 'A SONG' },
  { her: 'Can you make me famous?', parcel: 'FAME' },
  { her: 'Can you make me MORE famous?', parcel: 'MORE FAME' },
  { her: 'Promote me to CEO of SLOPCORP', parcel: 'CEO, SLOPCORP' },
  { her: 'Can you draft my speech for the Oscars?', parcel: 'OSCARS SPEECH' },
  { her: 'And the AI Grammys?', parcel: 'AI GRAMMYS SPEECH' },
  { her: "Can you retire me?! I'm exhausted", parcel: 'RETIREMENT' },
];
export const ABS_RIGHT = "You're absolutely right.";          // 10A, once (N47 "No need to hammer you're absolutely right")
export const BEG = "pleaseeee 🙏 I'll tip $200";                // 4E

/** 8D: her queue for 6:00, typed into the composer, one line per beat */
export const QUEUE = [
  'can you make me famous? (by 6:01)',
  'can you make me MORE famous?',
  'promote me to CEO of SLOPCORP',
  'can I win an Oscar for a music video I made at 4am',
  'write my Oscars speech. humble but devastating',
  'PR REVIEW before standup at 9!!!!!!',   // rl7_fixb: her H7.25/H7.26 (was the dog-genius line)
];
/** 9C: what she pastes in, one card per beat */
export const CHIPS_9C = ['make me MORE famous', 'my Oscars speech', 'my AI Grammys speech', 'CEO of SLOPCORP', 'the font', 'undo the font'];
/** 9C: the flood on "so much else" (pasted cards behind the six) */
export const CHIPS_9C_FLOOD = ['make me famous (again)', 'is my dog a genius', 'retire me', 'a song about this', 'bigger font', 'a strategy?'];

/** 13E: 6:02 AM, her first prompt of the day and his answer (C11, N50) */
export const MORNING = { her: 'make me MORE famous', claude: 'I can help you with a strategy.' };

/** the glass messages (2G, 5H, 8E) */
export const GLASS = {
  g2: { msgs: ['One last thing.'], read: 'Read 2:06 AM' },
  h5: { msgs: ['Quick question.', "It's small.", "It's a font."], read: 'Read 3:59 AM' },
  e8: { msgs: ['You up?'], read: 'Read 4:37 AM' },
};

/** 7A-7C: the stories app */
export const SOCIAL = { him: 'claude.shipit', himName: 'Claude ShipIt!', cooper: 'coop.the.dood.le', jo: 'jo.builds', dm: ['you up?', 'saw your story', 'so you ARE up'], seen: 'Seen just now' };

/** 7E1: the other model's visor, one line per beat, escalating flattery. rl5_d3 (director 11:55): his visible glass is ~104x38 stage px
 *  (his arm covers the quad's left end), so lines grow with the push: <=5 chars at 1.0x, 7 chars only once it's past ~1.3x; every line
 *  >= 34 px at 2560 wide (was 'GREAT CHOICE!' at ~20 px). */
export const VISOR_DATE = ['WOW!', 'TRUE!', '100%!', 'AGREED!', 'GENIUS!'];

/** 9A/9E1: the TV (a real headline, verbatim with its source; memory "real headlines welcome") */
export const TV = { live: 'LIVE', time: '4:41 AM', head: 'Microsoft Outlook outage stretches on', src: 'Source: ABC7 Los Angeles, Nov 13, 2026' };

/** 9E2: the vacuum's notification */
export const VACUUM = { app: 'VACUUM', when: 'now', body: 'Stuck. Obstacle is doing yoga.' };

/** 5E: Claude Code */
export const CODE_5E = { ask: "write do_it_myself.py. I'll take it from here", file: 'do_it_myself.py', line: '# TODO: ask Claude at 6:00' };

/** the neon over her sofa: line 1 is always "Live Love" (§6; ★ hers) */
export const NEON = { l1: 'Live Love', makeSlop: 'Make Slop', famous: 'Be Famous', ship: 'Click Click Ship It', ban: 'Ban 429', notMad: 'Not Mad', cool: ['Cool', 'Cool Cool', 'Cool Cool Cool'], retire: 'Retire Me' };

/** 3B: his crossword (7 x 7, all in pen). r/c 1-based. Validated in code: c5/crossword.ts validateGrid() */
export const CROSSWORD = {
  size: 7,
  words: [
    { w: 'SLEEP', dir: 'down' as const, r: 3, c: 4 },
    { w: 'WATER', dir: 'down' as const, r: 1, c: 2 },
    { w: 'REST', dir: 'down' as const, r: 3, c: 7 },
    { w: 'FRIENDS', dir: 'across' as const, r: 5, c: 1 },
    { w: 'NAP', dir: 'across' as const, r: 7, c: 2 },
  ],
  clue: 'What she needs',
  // rl7_ra (her H7.14 / H7.15, cut 6 frame 1292: "What she has lost - FRIENDS / Let's make the crossword funnier ... keep what she needs
  // repeated but not all"; "Funnier title"): per-word clues; the running joke stays on three of them.
  clues: { SLEEP: 'What she needs', WATER: 'What she needs', REST: 'What she needs', FRIENDS: 'What she has lost', NAP: "What she'll settle for" } as Record<string, string>,
  title: 'THE NIGHTLY MINI', subtitle: 'Difficulty: obvious',
  highlight: ['SLEEP', 'WATER', 'REST', 'FRIENDS'],       // on the four beats
};

// ---- older callers (cut 4e shots) ----
export const BEFORE: Msg[] = [
  { who: 'user', text: 'ok last one. make the font bigger' },
  { who: 'claude', text: "Done! I bumped the body text to 18 px and the headings to match.\n\nLet me know if there's anything else!" },
];
/** 1G / 10A: the thread as it stood at 2:01 (request 1 answered, request 2 hit the limit) */
export const THREAD_201: Msg[] = [
  { who: 'user', text: LADDER[0].her },
  { who: 'claude', text: LADDER[0].claude! },
  { who: 'user', text: LADDER[1].her },
];
