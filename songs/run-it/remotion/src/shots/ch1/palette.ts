// CH1/POST1 swatches from the creative director's palette (songs/run-it/PALETTE.md "CH1 + POST1", src/data/palette.json
// `ch1`). Pair: night blue #16233a vs amber #ffcf7a. Maximalism in count and scale, not hue: blue + amber + the pink dot
// only. Pink stays ONLY on the dot, red ONLY on the red buttons (the hook's red, for continuity), no purple, no magenta.
import pal from '../../data/palette.json';
const c = (pal as any).ch1 as Record<string, string>;

export const P = {
  ground0: '#0d0f17',      // the hook's lifted artboard at 41.65 (s17); eases to the CH1 bg
  ground: c.bg,            // #070b14
  groundEnd: c.bg,         // s28 steps it to the V2 sky (#0a0f1a)
  canvas: '#0b0c11',       // the hook's infinite canvas
  canvasCH: '#04060c',     // CH1's, one step darker than the bg so the artboards read as frames
  amber: c.amber, gold: c.gold, core: c.flameCore, ember: c.ember, paper: c.tilePaper,
  surface: c.surface, surfaceLo: c.surfaceLo,
  blue: '#8fa6c8',         // the palette's ghost blue at full strength: the light blue shapes
  slate: '#4a6290',        // mid night blue (same hue family as #16233a), for shapes that must read on the bg
  ink: c.ink,
  select: '#8fa6c8',       // design-tool selection (frame handles, the Run chip, the model cursor)
  towerBody: c.surface, towerEdge: '#24375a', winOff: c.surfaceLo,
};
// tile variants (the wall): dark tiles mostly, paper (the intro's callback) and amber now and then; each keeps its pink dot
export const TILE_DARK = [c.surface, c.surfaceLo, '#121d31'];
export const TILE_LIGHT = [c.tilePaper, c.amber];
// colour swaps inside the pair for dark tiles; light tiles turn every shape night blue
export const SWAPS: Record<string, string>[] = [
  {},
  { [P.amber]: P.blue, [P.blue]: P.amber, [P.gold]: P.slate, [P.slate]: P.gold },
  { [P.core]: P.blue, [P.blue]: P.core },
  { [P.amber]: P.core, [P.core]: P.amber, [P.slate]: P.blue, [P.blue]: P.slate },
];
export const LIGHT_SWAP: Record<string, string> = { [P.amber]: P.surface, [P.gold]: P.slate, [P.core]: P.surface, [P.blue]: P.slate, [P.ember]: P.slate };
