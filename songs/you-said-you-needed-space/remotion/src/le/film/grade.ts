// The film's grade: every look parameter the style board still has open, in one place. A beat can override any of
// them (Partial<Grade>); the picks, when they arrive, change GRADE_DEFAULT only.
export type RGB = [number, number, number];
export type Grade = {
  exposure: number;   // overall
  glow: number;       // her bioluminescence, master gain (0 = a dark planet, 1 = the look, 2 = full bloom)
  violet: number;     // OPEN: 0 = cyan only, 1 = cyan + violet (violet in oceans, aurora, atmosphere's outer edge)
  daySide: number;    // OPEN: 0 = stylized (her whole visible side is the night/bioluminescent look), 1 = the real sunlit day side
  hisWarm: number;    // OPEN: his city lights, warm white (Black Marble), gain
  herCyan: number;    // OPEN: her cyan glow on the same city/coast pixels (1 = cities read as hers), gain
  rivers: number;     // river veins gain
  riverPulse: number; // how strongly light pulses travel down the rivers
  coast: number;      // coastline vein
  forest: number;     // vegetation shimmer (teal), from the real green
  ocean: number;      // ocean plankton glow (cyan/violet, densest on the shelves)
  clouds: number;     // cloud veil
  atmos: number;      // atmosphere rim/halo
  flare: number;      // a one-off bright flare of her whole body (e.g. "dirt")
  kick: number;       // a short pulse envelope through her rivers/veins (per word, per beat)
  hisOff: number;     // 0..1: fraction of his warm city lights switched off (random city by city); her cyan takes the dark
  aurora: number;     // aurora curtains on her limb (violet/green)
  stars: number;      // star gain
  dust: number;       // faint background star dust gain
  motes: number;      // floating light motes in front
  mist: number;       // drifting mist veil
  bloom: number;      // bloom strength
  bloomRadius: number;
  bloomThreshold: number;
  vignette: number;
  grain: number;
  herColor: RGB;      // her cyan (linear)
  violetColor: RGB;
  hisColor: RGB;      // his warm white
  // ---- the proof-30 look (earth_proof30, Nov 8). All default to 0 / neutral = the engine look above is unchanged ----
  lux: number;        // 0 = the planet look above; 1 = the PROOF look (port of the approved mockup recipe: slate night relief, crisp veins +
                      // capillaries, violet forest mottling, valley mist, clouds lit from below, gold/rose/violet dusk line, thin limb + airglow)
  capil: number;      // lux: capillary veins gain (fine branching lines off the rivers)
  seam: number;       // lux: the gold/rose/violet dusk line gain
  haloWide: number;   // lux: her own wide soft cyan light around her (for the far dot)
  galaxy: number;     // Milky Way mist behind everything (Extra.tsx)
  deep: number;       // the deep star field: 42k GPU stars (Extra.tsx); use with dust: 0
  room: number;       // cold open: 0..1 gain on the room the stars give her (spring keyed to "space" + the echoes; Extra.tsx / proof30.ts)
  roomX: number; roomY: number; // the room's centre on screen
  sand: number;       // the sand macro layer (0..1 opacity) and its dive (0 = the shore wide, 1 = inside the one grain)
  sandDive: number;
  chip: number;       // the chip made of grains (0..1 opacity); chipU 0 = floating grains, 1 = seated (gold)
  chipU: number;
  chipX: number; chipY: number; chipS: number; chipTilt: number; // its centre on screen, size (screen units), tilt (0 flat-on .. 1 laid back)
  banner: number;     // the feed banner made of stars (0..1 opacity); bannerU 0 = in the sky, 1 = written, 2 = let go
  bannerU: number;
  roomKeep: number;   // share of the faint far stars (and of the mist) that stay inside the room: 0 = an empty room, 0.15 = space, not a hole
  roomSpin: number;   // radians: the stars around the room keep drifting slowly round her (each at its own rate), so the crowd is never frozen
  starWarm: number;   // 0..1: the deep stars turn his warm gold and glitter, sweeping left to right ("the future's in the stars")
  sunWarm: number;    // (earth_cut2, gate 7) 0..1: lux day side + day limb + day clouds lean his Filament warm (sunrise) instead of blue-white
  castWarm: number;   // (earth_cut2, gate 7) 0..1: the cast stars turn his Filament/Ember gold (his crammed stars, the rack's stars)
  goldR: number; goldK: number; goldLat: number; goldLon: number; // lux: a front of his warm gold light running up her rivers from one place (radius in degrees; 0 = off), cooling to her cyan; rivers ahead of it are dim until it passes
};
export const GRADE_DEFAULT: Grade = {
  exposure: 1.0, glow: 1.0, violet: 0.6, daySide: 0.12, hisWarm: 0.55, herCyan: 0.6, rivers: 1.0, riverPulse: 0.6,
  coast: 0.7, forest: 0.6, ocean: 0.55, clouds: 0.25, atmos: 1.0, flare: 0, kick: 0, hisOff: 0, aurora: 0, stars: 1.0, dust: 1.0, motes: 0.5, mist: 0.25,
  bloom: 0.6, bloomRadius: 0.45, bloomThreshold: 0.22, vignette: 0.55, grain: 0.035,
  herColor: [0.15, 0.95, 1.0], violetColor: [0.55, 0.25, 1.0], hisColor: [1.0, 0.72, 0.42],
  lux: 0, capil: 1, seam: 0.06, haloWide: 0, galaxy: 0, deep: 0, room: 0, roomX: 0, roomY: 0, sand: 0, sandDive: 0, chip: 0, chipU: 0, chipX: 0, chipY: 0, chipS: 1, chipTilt: 0.5, banner: 0, bannerU: 0, goldR: 0, goldK: 0, goldLat: 0, goldLon: 0, roomKeep: 0, starWarm: 0, roomSpin: 0, sunWarm: 0, castWarm: 0,
};
