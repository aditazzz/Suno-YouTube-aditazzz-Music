// Written by build/palette/gen_ts.py from living_earth/le_palette.py (earth_palette, creative director, Nov 9 2026; QA gate 7).
// NOT imported by the engine (inert). Swatches for section builders: `linear` for grade/shader colours (engine colours are linear),
// `hex` for 2D/DOM. The colourist pass is applied to rendered masters by living_earth/le_grade.py (one 3D LUT per section, same
// maths as le_palette.py, display space after ACES+sRGB). Change numbers in le_palette.py, then re-run le_palette.py + gen_ts.py.
import type { RGB } from './grade';
export const PALETTE = {
  'Biolume': { hex: '#2FE0E8', linear: [0.028, 0.745, 0.807] as RGB, owner: 'her' },
  'Ember': { hex: '#FF8A3D', linear: [1.0, 0.254, 0.047] as RGB, owner: 'his' },
  'Aurora': { hex: '#8E63F5', linear: [0.27, 0.125, 0.913] as RGB, owner: 'her' },
  'Filament': { hex: '#FFD49A', linear: [1.0, 0.658, 0.323] as RGB, owner: 'his' },
  'Overheat': { hex: '#FF4B2B', linear: [1.0, 0.07, 0.024] as RGB, owner: 'his' },
  'Dusk Rose': { hex: '#E89BB5', linear: [0.807, 0.328, 0.462] as RGB, owner: 'seam' },
  'Star Ivory': { hex: '#F2ECE1', linear: [0.888, 0.839, 0.753] as RGB, owner: 'neutral' },
  'Night Navy': { hex: '#0A1022', linear: [0.003, 0.005, 0.016] as RGB, owner: 'neutral' },
  'Deep Space': { hex: '#04060E', linear: [0.001, 0.002, 0.004] as RGB, owner: 'neutral' },
} as const;
export const COLOUR_GRADE = [
  { name: 'cold open', t0: 0.0, t1: 17.706, lut: 'earth_cold_open.cube', grade: {"lift": [0.02, 0.022, 0.052], "gamma": 1.0, "gain": [1.0, 1.0, 1.0], "sat": 1.0, "satMax": 0.78, "tealToCyan": 0.5, "cyanHue": 186.0, "blueToViolet": 0.35, "violetHue": 258.0, "hiTint": [1.035, 1.0, 0.93], "hiAmt": 0.25, "shTint": [0.96, 0.98, 1.08], "shAmt": 0.0, "knee": 0.8, "ceil": 0.94, "warmKeep": 1.35, "xfade": 0.5} },
  { name: 'verse 1', t0: 17.706, t1: 35.816, lut: 'earth_verse_1.cube', grade: {"lift": [0.02, 0.022, 0.052], "gamma": 1.0, "gain": [1.0, 1.0, 1.0], "sat": 1.0, "satMax": 0.76, "tealToCyan": 0.55, "cyanHue": 186.0, "blueToViolet": 0.5, "violetHue": 258.0, "hiTint": [1.035, 1.0, 0.93], "hiAmt": 0.35, "shTint": [0.96, 0.98, 1.08], "shAmt": 0.0, "knee": 0.8, "ceil": 0.955, "warmKeep": 1.35, "xfade": 0.5} },
  { name: 'pre/chorus 1', t0: 35.816, t1: 83.354, lut: 'earth_pre_chorus_1.cube', grade: {"lift": [0.02, 0.022, 0.052], "gamma": 1.03, "gain": [1.0, 1.0, 1.0], "sat": 1.0, "satMax": 0.8, "tealToCyan": 0.5, "cyanHue": 186.0, "blueToViolet": 0.55, "violetHue": 258.0, "hiTint": [1.035, 1.0, 0.93], "hiAmt": 0.4, "shTint": [0.96, 0.98, 1.08], "shAmt": 0.0, "knee": 0.8, "ceil": 0.955, "warmKeep": 1.35, "xfade": 0.5} },
  { name: 'verse 2', t0: 83.354, t1: 112.782, lut: 'earth_verse_2.cube', grade: {"lift": [0.02, 0.022, 0.052], "gamma": 1.04, "gain": [1.0, 1.0, 1.0], "sat": 1.0, "satMax": 0.74, "tealToCyan": 0.25, "cyanHue": 186.0, "blueToViolet": 0.5, "violetHue": 258.0, "hiTint": [1.035, 1.0, 0.93], "hiAmt": 0.3, "shTint": [0.96, 0.98, 1.08], "shAmt": 0.0, "knee": 0.8, "ceil": 0.955, "warmKeep": 1.35, "xfade": 0.5} },
  { name: 'chorus 2', t0: 112.782, t1: 149.002, lut: 'earth_chorus_2.cube', grade: {"lift": [0.02, 0.022, 0.052], "gamma": 1.02, "gain": [1.0, 1.0, 1.0], "sat": 1.0, "satMax": 0.8, "tealToCyan": 0.6, "cyanHue": 186.0, "blueToViolet": 0.6, "violetHue": 258.0, "hiTint": [1.035, 1.0, 0.93], "hiAmt": 0.4, "shTint": [0.96, 0.98, 1.08], "shAmt": 0.0, "knee": 0.8, "ceil": 0.955, "warmKeep": 1.35, "xfade": 0.5} },
  { name: 'bridge', t0: 149.002, t1: 176.167, lut: 'earth_bridge.cube', grade: {"lift": [0.024, 0.02, 0.058], "gamma": 1.0, "gain": [1.0, 1.0, 1.0], "sat": 1.0, "satMax": 0.72, "tealToCyan": 0.5, "cyanHue": 186.0, "blueToViolet": 0.75, "violetHue": 258.0, "hiTint": [1.035, 1.0, 0.93], "hiAmt": 0.3, "shTint": [0.96, 0.98, 1.08], "shAmt": 0.0, "knee": 0.8, "ceil": 0.94, "warmKeep": 1.35, "xfade": 0.5} },
  { name: 'final chorus/countdown', t0: 176.167, t1: 212.386, lut: 'earth_final_chorus_countdown.cube', grade: {"lift": [0.02, 0.022, 0.052], "gamma": 1.02, "gain": [1.0, 1.0, 1.0], "sat": 1.0, "satMax": 0.84, "tealToCyan": 0.55, "cyanHue": 186.0, "blueToViolet": 0.6, "violetHue": 258.0, "hiTint": [1.035, 1.0, 0.93], "hiAmt": 0.4, "shTint": [0.96, 0.98, 1.08], "shAmt": 0.0, "knee": 0.8, "ceil": 0.955, "warmKeep": 1.35, "xfade": 0.5} },
  { name: 'houston/end', t0: 212.386, t1: 217.6, lut: 'earth_houston_end.cube', grade: {"lift": [0.02, 0.022, 0.052], "gamma": 0.98, "gain": [1.0, 1.0, 1.0], "sat": 1.0, "satMax": 0.78, "tealToCyan": 0.5, "cyanHue": 186.0, "blueToViolet": 0.45, "violetHue": 258.0, "hiTint": [1.05, 1.0, 0.9], "hiAmt": 0.55, "shTint": [0.96, 0.98, 1.08], "shAmt": 0.0, "knee": 0.74, "ceil": 0.94, "warmKeep": 1.35, "xfade": 0.5} },
] as const;
