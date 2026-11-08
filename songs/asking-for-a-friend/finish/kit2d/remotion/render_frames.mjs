// node render_frames.mjs <outdir> [ID,ID...]   bundle once, renderStill every key frame of every item (2560x1440 PNG)
import { bundle } from '@remotion/bundler';
import { renderStill, selectComposition } from '@remotion/renderer';
import path from 'path'; import fs from 'fs';
const [out, only] = process.argv.slice(2); fs.mkdirSync(out, { recursive: true });
const serveUrl = await bundle({ entryPoint: path.resolve('src/index.ts') });
const browserExecutable = process.env.CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const src = fs.readFileSync('src/items.ts', 'utf8');
const items = [...src.matchAll(/id: '([^']+)', dur: (\d+), keys: \[([^\]]*)\]/g)].map((m) => ({ id: m[1], keys: m[3].split(',').map((x) => +x.trim()) }));
for (const it of items) {
  if (only && !only.split(',').includes(it.id)) continue;
  try {
    const composition = await selectComposition({ serveUrl, id: it.id, browserExecutable });
    for (const k of it.keys) { await renderStill({ composition, serveUrl, output: path.join(out, `${it.id}_f${k}.png`), frame: k, imageFormat: 'png', browserExecutable }); }
    console.log('ok', it.id);
  } catch (e) { console.log('FAILED', it.id, String(e).slice(0, 300)); }
}
console.log('ALLDONE');
