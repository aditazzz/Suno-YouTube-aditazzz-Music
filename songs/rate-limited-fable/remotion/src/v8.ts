// rl8_sign (Fri Nov 20): the v8 build flag. Default OFF = the 05:03 delivery reproduces exactly. ON (inputProps {v8: true}, set by
// _c7_render_v8.mjs when V8=1) = the v8 fixes: the apartment neon LIVE LOVE / blue beat line ("click, click, ship it" in 8G's die).
// v8 plates keep their old names inside the overlay public dir (tools/make_public_v8.py -> public_v8/), so only behaviour (not paths) needs this.
import { getInputProps } from 'remotion';
export const V8: boolean = (getInputProps() as any)?.v8 === true;
