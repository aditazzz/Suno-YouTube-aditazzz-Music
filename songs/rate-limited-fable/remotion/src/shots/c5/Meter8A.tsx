// 8A meter digits (cut 5; plan §3: 8A f3691-3830, the meter held a full bar from 3761; N37): the parking meter's dot-matrix LCD
// (L5's meter insert still, public/l5/8A/meter.jpg) lights its 4, 2, 9 one per sung digit (3778 / 3785 / 3797): before its cue
// each digit is covered by the LCD's own blank (colour sampled off the still), on its cue the cover blinks off (on, 1-frame dip,
// on: an LCD segment refresh). "RETRY AFTER 6:00" is the still's own and stays. Draw <MeterDigits> INSIDE the camera that shows
// meter.jpg at 2560x1440 (plate px = stage px), after the plate:  <MeterDigits f={f} from={shot.from} />
import React from 'react';
import { AbsoluteFill } from 'remotion';

export const M8 = { DIGITS: [3778, 3785, 3797] };   // absolute
// the three digit cells on meter.jpg (stage px), measured off the still's LCD (l5.json meter_insert.lcd_429 = [1467.6, 675.2, 1673.1, 778.9])
const CELLS: [number, number, number, number][] = [[1463, 671, 1539, 783], [1539, 671, 1610, 783], [1610, 671, 1678, 783]];
const BLANK = 'rgb(207,215,202)';

export const MeterDigits: React.FC<{ f: number; from: number }> = ({ f, from }) => (
  <AbsoluteFill style={{ pointerEvents: 'none' }}>
    {CELLS.map(([x0, y0, x1, y1], i) => {
      const d = f - (M8.DIGITS[i] - from);
      const covered = d < 0 || d === 1;            // off until the cue; one dip frame after it
      return covered ? <div key={i} style={{ position: 'absolute', left: x0, top: y0, width: x1 - x0, height: y1 - y0, background: BLANK,
        boxShadow: `0 0 3px 1px ${BLANK}` }} /> : null;
    })}
  </AbsoluteFill>
);
