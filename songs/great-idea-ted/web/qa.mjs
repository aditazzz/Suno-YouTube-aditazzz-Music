// node qa.mjs [shot ...] : runs window.qa(shot) in the look page and prints every collision (mm, part, solid)
import http from 'http'; import fs from 'fs'; import path from 'path';
import { createRequire } from 'module'; const require = createRequire(import.meta.url); const { chromium } = require('playwright');
const root = path.dirname(new URL(import.meta.url).pathname);
const types = { '.js': 'text/javascript', '.html': 'text/html', '.json': 'application/json', '.ttf': 'font/ttf', '.otf': 'font/otf' };
const srv = http.createServer((req, res) => { const p = path.join(root, decodeURIComponent(req.url.split('?')[0]));
  fs.readFile(p, (e, d) => { if (e) { res.writeHead(404); res.end(); return; } res.writeHead(200, { 'Content-Type': types[path.extname(p)] || 'application/octet-stream' }); res.end(d); }); });
await new Promise((r) => srv.listen(0, r));
const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--enable-webgl'] });
const page = await browser.newPage({ viewport: { width: 640, height: 360 } });
page.on('pageerror', (e) => console.log('PAGE ERROR', e.message));
await page.goto(`http://localhost:${srv.address().port}/look.html?w=640&h=360`);
await page.waitForFunction(() => window.ready, null, { timeout: 60000 });
const shots = process.argv.slice(2).map(Number); let bad = 0;
for (const s of shots.length ? shots : [1, 4]) {
  const rep = await page.evaluate((n) => window.qa(n), s);
  for (const r of rep) { if (r.mm > 0) bad++; console.log(`shot ${s}  ${r.who.padEnd(10)} ${r.mm > 0 ? r.part : 'clear'}`); }
}
console.log(bad ? `${bad} collisions` : 'NO COLLISIONS');
await browser.close(); srv.close();
