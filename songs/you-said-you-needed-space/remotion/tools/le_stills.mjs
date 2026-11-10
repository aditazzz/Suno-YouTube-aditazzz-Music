// Living Earth film: several stills from one browser (fast look-dev), with the page's console forwarded.
//   node tools/le_stills.mjs <bundle dir> <composition> <out dir> <frame> [frame ...]   (run through tools/gpuq.sh)
import { renderStill, selectComposition, openBrowser } from '@remotion/renderer';
import path from 'node:path';
const [serveUrl, id, outDir, ...frames] = process.argv.slice(2);
const chromiumOptions = { gl: 'angle' };
const browser = await openBrowser('chrome', { chromiumOptions });
const onBrowserLog = (l) => { if (l.type === 'error' || /LEDBG/.test(l.text)) console.log('BROWSER', l.type, l.text.slice(0, 400)); };
const composition = await selectComposition({ serveUrl, id, chromiumOptions, puppeteerInstance: browser, onBrowserLog });
for (const f of frames) {
  const t0 = Date.now();
  const output = path.join(outDir, `${id}_f${String(f).padStart(5, '0')}.png`);
  await renderStill({ serveUrl, composition, frame: +f, output, chromiumOptions, puppeteerInstance: browser, onBrowserLog, overwrite: true });
  console.log(`still ${f} -> ${output} ${((Date.now() - t0) / 1000).toFixed(1)} s`);
}
await browser.close({ silent: true });
