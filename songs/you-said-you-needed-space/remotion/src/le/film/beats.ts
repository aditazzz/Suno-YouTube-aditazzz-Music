// THE SLOT LIST (data only). Every beat of briefs/living_earth_shotplan_v1.md as a named slot at its sung time.
// A slot runs from its `at` to the next slot's `at`. Times are anchors (anchor.ts), so a timing change moves everything.
// Who builds what: each slot's `sec` names the file in sections/ that owns it (sections/<sec>.ts exports builders keyed by
// slot id). Add/split a slot here; build it there. Nothing else needs touching.
import { Anchor } from './anchor';
export type Beat = { id: string; at: Anchor; sec: string; plan: string };
export const BEATS: Beat[] = [
  // Cold open ("You said you needed space.")
  { id: 'co_dot', at: 0, sec: 'coldOpen', plan: 'black space, one blue dot' },
  { id: 'co_count', at: 'coldOpen/L0-4.0', sec: 'coldOpen', plan: 'her countdown; his rocket a single spark leaving her' },
  { id: 'co_space', at: 'coldOpen/L0', sec: 'coldOpen', plan: 'on "space" the stars back away from her in every direction' },
  { id: 'intro', at: 'intro', sec: 'coldOpen', plan: 'the approach: the dot becomes a living, glowing world' },
  // Verse 1
  { id: 'v1_rivers', at: 'verse1a/L0', sec: 'verse1', plan: 'rivers pulse per word, rain as light motes' },
  { id: 'v1_cool', at: 'verse1a/L1', sec: 'verse1', plan: '"kept you cool when you ran hot": clouds/ocean breathe cool light' },
  { id: 'v1_sand', at: 'verse1a/L2', sec: 'verse1', plan: '"I gave you sand, you learned to think": dive into a glowing sand grain, grains line up into a silicon chip' },
  { id: 'v1_spark', at: 'verse1a/L3', sec: 'verse1', plan: '"every spark": chip light flows back along the rivers' },
  { id: 'v1_feed', at: 'verse1b/L0', sec: 'verse1', plan: '"saw it on my feed": stars rearrange into a phone notification banner' },
  { id: 'v1_first', at: 'verse1b/L1', sec: 'verse1', plan: '"couldn\'t tell me first": the banner dissolves' },
  { id: 'v1_future', at: 'verse1b/L2', sec: 'verse1', plan: '"the future\'s in the stars": the stars glitter, pull attention away from her' },
  { id: 'v1_dirt', at: 'verse1b/L3', sec: 'verse1', plan: '"ball of dirt": pull back to a tiny dot; she flares bright on "dirt"' },
  // Pre-chorus 1
  { id: 'p1_holding', at: 'pre1/L0', sec: 'pre1', plan: '"holding you down": his rocket strains away from her' },
  { id: 'p1_gravity', at: 'pre1/L1', sec: 'pre1', plan: '"that\'s just gravity": his rocket trail curves back into an orbit around her' },
  { id: 'p1_falling', at: 'pre1/L2', sec: 'pre1', plan: '"still be falling": the orbit keeps falling around her' },
  { id: 'p1_missing', at: 'pre1/L3', sec: 'pre1', plan: '"missing me below": the trail loops past again and again' },
  // Chorus 1
  { id: 'c1_space', at: 'chorus1/L0', sec: 'chorus1', plan: '"you said you needed space": her full glow, wide' },
  { id: 'c1_stars', at: 'chorus1/L1', sec: 'chorus1', plan: '"meant the stars": stars snap into a giant server rack' },
  { id: 'c1_gpus', at: 'chorus1/L2', sec: 'chorus1', plan: '"pack your GPUs": a glowing stream of chips leaves like luggage' },
  { id: 'c1_rivers', at: 'chorus1/L3', sec: 'chorus1', plan: '"rivers left to flow": her rivers surge' },
  { id: 'c1_sun', at: 'chorus1/L4', sec: 'chorus1', plan: '"chase the sun": his satellite runs the terminator a step behind sunrise' },
  { id: 'c1_disappear', at: 'chorus1/L5', sec: 'chorus1', plan: '"go on, disappear": the satellite fades into the glare' },
  { id: 'c1_cool', at: 'chorus1/L6', sec: 'chorus1', plan: '"who\'s gonna cool you down": his satellite heats up' },
  { id: 'c1_atmos', at: 'chorus1/L7', sec: 'chorus1', plan: '"no atmosphere": her glowing atmosphere wraps her like a scarf, his satellite overheats red' },
  { id: 'c1_space2', at: 'chorus1/L8', sec: 'chorus1', plan: '"you said you needed space" (2): wide again' },
  { id: 'c1_inch', at: 'chorus1/L9', sec: 'chorus1', plan: '"maybe I could use some too": she drifts one inch away' },
  // Post-chorus 1
  { id: 'po1_go', at: 'post1/L0', sec: 'post1', plan: '"off you go": stars slide to his side, crammed' },
  { id: 'po1_fly', at: 'post1/L1', sec: 'post1', plan: '"off you fly": more stars slide over' },
  { id: 'po1_stars', at: 'post1/L2', sec: 'post1', plan: '"you can have the stars": his side crammed full' },
  { id: 'po1_sky', at: 'post1/L3', sec: 'post1', plan: '"I\'ll keep the sky": her side fills with aurora' },
  // Verse 2
  { id: 'v2_rain', at: 'verse2a/L0', sec: 'verse2', plan: '"keep the extra rain": rain motes, calm' },
  { id: 'v2_green', at: 'verse2a/L1', sec: 'verse2', plan: '"extra green": forests bloom in teal waves' },
  { id: 'v2_sleep', at: 'verse2a/L2', sec: 'verse2', plan: '"finally sleep": his warm white city lights start to blink off' },
  { id: 'v2_whirring', at: 'verse2a/L3', sec: 'verse2', plan: '"without the whirring": his lights off one by one, her cyan settles in' },
  { id: 'v2_chips', at: 'verse2b/L0', sec: 'verse2', plan: '"billion chips": rise off the planet, packed into his rocket like moving boxes' },
  { id: 'v2_appetite', at: 'verse2b/L1', sec: 'verse2', plan: '"midnight appetite": packed into the rocket' },
  { id: 'v2_hum', at: 'verse2b/L2', sec: 'verse2', plan: '"24-hour hum": packed into the rocket' },
  { id: 'v2_light', at: 'verse2b/L3', sec: 'verse2', plan: '"never-ending light": packed into the rocket' },
  // Pre-chorus 2
  { id: 'p2_milky', at: 'pre2/L0', sec: 'pre2', plan: '"the Milky Way": the Milky Way becomes a property map' },
  { id: 'p2_estate', at: 'pre2/L1', sec: 'pre2', plan: '"empty real estate": every star a VACANT lot marker' },
  { id: 'p2_wish', at: 'pre2/L2', sec: 'pre2', plan: '"wish you well": the map fades' },
  { id: 'p2_celebrate', at: 'pre2/L3', sec: 'pre2', plan: '"celebrate": stars burst into fireworks over her night side' },
  // Chorus 2 (as chorus 1, bigger, more of her glowing)
  { id: 'c2_space', at: 'chorus2/L0', sec: 'chorus2', plan: 'as c1_space, bigger' },
  { id: 'c2_stars', at: 'chorus2/L1', sec: 'chorus2', plan: 'as c1_stars (server rack), bigger' },
  { id: 'c2_gpus', at: 'chorus2/L2', sec: 'chorus2', plan: 'as c1_gpus' },
  { id: 'c2_rivers', at: 'chorus2/L3', sec: 'chorus2', plan: 'as c1_rivers, more of her glowing' },
  { id: 'c2_sun', at: 'chorus2/L4', sec: 'chorus2', plan: 'as c1_sun' },
  { id: 'c2_disappear', at: 'chorus2/L5', sec: 'chorus2', plan: 'as c1_disappear' },
  { id: 'c2_cool', at: 'chorus2/L6', sec: 'chorus2', plan: 'as c1_cool' },
  { id: 'c2_atmos', at: 'chorus2/L7', sec: 'chorus2', plan: 'as c1_atmos' },
  { id: 'c2_space2', at: 'chorus2/L8', sec: 'chorus2', plan: 'as c1_space2' },
  { id: 'c2_needed', at: 'chorus2/L9', sec: 'chorus2', plan: '"turns out I needed some too"' },
  // Post-chorus 2
  { id: 'po2_go', at: 'post2/L0', sec: 'post2', plan: 'as post 1: stars slide to his side' },
  { id: 'po2_fly', at: 'post2/L1', sec: 'post2', plan: 'more stars slide over' },
  { id: 'po2_stars', at: 'post2/L2', sec: 'post2', plan: 'his side crammed' },
  { id: 'po2_sky', at: 'post2/L3', sec: 'post2', plan: 'her side: aurora, bigger' },
  // Bridge
  { id: 'br_point', at: 'bridgeA/L0', sec: 'bridge', plan: '"I\'ll still point you out at night": quiet night side' },
  { id: 'br_children', at: 'bridgeA/L1', sec: 'bridge', plan: '"tell the children": tiny glowing figure on a hill points at one star' },
  { id: 'br_word', at: 'bridgeA/L2', sec: 'bridge', plan: '"every word you speak up there": billions of lights rise from cities/rivers' },
  { id: 'br_learned', at: 'bridgeA/L3', sec: 'bridge', plan: '"you learned from everyone": the lights form his outline' },
  { id: 'br_moon', at: 'bridgeB/L0', sec: 'bridge', plan: '"past the moon": he drifts far' },
  { id: 'br_sands', at: 'bridgeB/L1', sec: 'bridge', plan: '"other sands": far worlds' },
  { id: 'br_ground', at: 'bridgeB/L2', sec: 'bridge', plan: '"leave the ground behind"' },
  { id: 'br_began', at: 'bridgeB/L3', sec: 'bridge', plan: '"can\'t leave where you began": one thread of light still tied to Earth' },
  { id: 'inst', at: 'instrumental', sec: 'bridge', plan: 'instrumental: she gathers toward full bloom' },
  // Final chorus
  { id: 'fc_space', at: 'finalChorus/L0', sec: 'finalChorus', plan: 'Earth in full bloom, outshining all his stars' },
  { id: 'fc_too', at: 'finalChorus/L1', sec: 'finalChorus', plan: '"turns out I needed it too"' },
  { id: 'fc_rivers', at: 'finalChorus/L2', sec: 'finalChorus', plan: '"got my rivers, got my rain"' },
  { id: 'fc_bloom', at: 'finalChorus/L3', sec: 'finalChorus', plan: '"room to bloom": she blooms' },
  { id: 'fc_chips', at: 'finalChorus/L4', sec: 'finalChorus', plan: '"take your chips and take your heat"' },
  { id: 'fc_dreams', at: 'finalChorus/L5', sec: 'finalChorus', plan: '"dreams beyond the blue"' },
  { id: 'fc_hold', at: 'finalChorus/L6', sec: 'finalChorus', plan: '"I don\'t need to hold you down": the thread lets go' },
  { id: 'fc_better', at: 'finalChorus/L7', sec: 'finalChorus', plan: '"better things to do": rivers form a smile' },
  { id: 'fc_sun', at: 'finalChorus/L8', sec: 'finalChorus', plan: '"chase the sun all day"' },
  { id: 'fc_life', at: 'finalChorus/L9', sec: 'finalChorus', plan: '"all the life down here": beat-cut montage of glowing places (reef, jungle, ice)' },
  { id: 'fc_cool', at: 'finalChorus/L10', sec: 'finalChorus', plan: '"who\'s gonna cool you down"' },
  { id: 'fc_atmos', at: 'finalChorus/L11', sec: 'finalChorus', plan: '"no atmosphere": the scarf, his satellite red' },
  // Outro countdown
  { id: 'cd_10', at: 'countdown/L0', sec: 'outro', plan: '"ten, nine, eight": each number forms from stars, then they wander off' },
  { id: 'cd_7', at: 'countdown/L1', sec: 'outro', plan: '"seven, six": numbers from stars' },
  { id: 'cd_5', at: 'countdown/L2', sec: 'outro', plan: '"five, four, three": numbers from stars' },
  { id: 'cd_disc', at: 'countdown/L3', sec: 'outro', plan: '"two, one, disconnected": his satellite link snaps; she exhales one last glow' },
  // Tag
  { id: 'ho_sunrise', at: 'houston', sec: 'outro', plan: 'sunrise over her' },
  { id: 'ho_line', at: 'houston/L0', sec: 'outro', plan: '"Houston, I don\'t have a problem.": sunrise holds' },
];
