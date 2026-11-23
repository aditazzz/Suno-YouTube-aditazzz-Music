// rl_first30_v3 (CD V3 order 5, the red rule: red is the 429's alone). Plates whose dispenser / wall box rendered red get
// their teal recolor (build/first30/tools/prep_teal.py) when it exists; otherwise the original file.
import teal from './teal.json';
const MAP = ((teal as any).map ?? {}) as Record<string, { file: string }>;
export const tealSrc = (path: string): string => MAP[path]?.file ?? path;
