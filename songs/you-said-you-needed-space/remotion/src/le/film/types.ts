// What one frame of the film is: a plain object, a pure function of time (see engine.ts). Screen units everywhere:
// y in [-1, 1] (frame height = 2), x in [-aspect, aspect]; +y up.
import { Grade, RGB } from './grade';
import { Anchor } from './anchor';
export type Fmt = '169' | '916';
export type Cam = {
  x: number; y: number;  // her disk's centre on screen
  r: number;             // her disk's radius (1 = half the frame height)
  lon: number; lat: number; // the place on her facing the camera (degrees)
  roll: number;          // image roll (degrees)
  sun: [number, number, number]; // sun direction in view space (z toward camera); default: behind her, a thin day crescent
  par: [number, number]; // parallax pan of the sky (screen units; depth-scaled per star/mote)
};
export type GeoPt = [number, number]; // [lat, lon] degrees
// rel: in her radii from her centre (follows the camera); geo: [lat, lon] on her surface (lift = height in radii)
export type Path = { space: 'screen'; pts: [number, number][] } | { space: 'rel'; pts: [number, number][] } | { space: 'geo'; pts: GeoPt[]; lift?: number }
  | { space: 'orbit'; alt: number; incl: number; node: number; a0: number; a1: number }; // orbit: degrees of arc a0..a1 at altitude alt (radii)
export type Flow = {
  path: Path;
  head: number;      // 0..1 where the light front is along the path
  tail: number;      // trail length as a fraction of the path
  color: RGB; size: number; intensity: number;
  count?: number;    // particles (default 160)
  dash?: number;     // >0: the trail is broken into this many packets (chip streams, luggage)
};
export type Spark = { x: number; y: number; size: number; color: RGB; intensity: number; behind?: boolean; rel?: [number, number]; orbit?: [number, number, number, number] };
// screen space x,y; or rel = [x,y] in her radii from her centre; or orbit = [alt, incl, node, angle] (camera.ts projOrbit). behind = may be hidden by her disk
export type Pulse = { lat: number; lon: number; t0: number; speed: number; strength: number }; // a ring of light spreading over her surface (deg/s)
export type Frame = {
  t: number;
  cam: Cam;
  grade: Grade;
  flows: Flow[];
  sparks: Spark[];
  pulses: Pulse[];
  motes?: 'drift' | 'rain' | 'rise'; // how the motes move (default drift)
  label?: string;     // rough-cut beat label
  built?: boolean;    // false = this slot still shows the default
};
export type StarSet =
  | { kind: 'sky' }                                                   // home: the night sky
  | { kind: 'away'; cx: number; cy: number; k: number }               // home pushed radially away from (cx,cy) by factor k
  | { kind: 'room'; cx: number; cy: number; R: number }              // ported from beats/01: r -> cbrt(r^3 + R^3): a clear room of radius R around (cx,cy), far stars barely move
  | { kind: 'union'; parts: { set: StarSet; w: number }[]; keep?: number } // several shapes at once (e.g. banner outline + its words); w = share of the moving stars
  | { kind: 'side'; side: 1 | -1; cram: number }                      // everyone crammed into one side (cram = fraction of width used)
  | { kind: 'text'; text: string; box: Box; font?: string; keep?: number }
  | { kind: 'svg'; d: string; view: [number, number]; box: Box; keep?: number; stroke?: number }
  | { kind: 'image'; src: string; box: Box; keep?: number; threshold?: number } // a mask in public/ (preload it: IMAGE_MASKS in stars.ts)
  | { kind: 'rects'; rects: Box[]; box?: Box; outline?: boolean; keep?: number } // boxes in a unit design space mapped into box
  | { kind: 'points'; pts: [number, number][]; keep?: number }
  | { kind: 'fn'; fn: (i: number, t: number, home: [number, number], n: number, fmt: Fmt) => [number, number]; front?: boolean };
export type Box = { cx: number; cy: number; w: number; h: number }; // screen units; shrunk to fit in 9:16 automatically
export type StarKey = { at: Anchor; set: StarSet; dur: number; straggle?: number; curve?: number; front?: boolean; sweep?: number }; // sweep (ported from beats/03): extra delay left->right, fraction of dur
