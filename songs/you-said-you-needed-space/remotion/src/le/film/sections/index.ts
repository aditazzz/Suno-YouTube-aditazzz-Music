// The section registry. Each file owns the slots whose `sec` (beats.ts) is its name. Already wired: builders edit their
// own file only. (A new section file = one import + one entry here.)
import { coldOpen } from './coldOpen';
import { verse1 } from './verse1';
import { pre1 } from './pre1';
import { chorus1 } from './chorus1';
import { post1, post2 } from './post';
import { verse2 } from './verse2';
import { pre2 } from './pre2';
import { chorus2 } from './chorus2';
import { bridge } from './bridge';
import { finalChorus } from './finalChorus';
import { outro } from './outro';
import { Section } from './api';
export * from './api';
export const SECTIONS: Section[] = [coldOpen, verse1, pre1, chorus1, post1, verse2, pre2, chorus2, post2, bridge, finalChorus, outro];
