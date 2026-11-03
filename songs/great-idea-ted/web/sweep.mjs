import http from 'http'; import fs from 'fs'; import path from 'path';
import { createRequire } from 'module'; const require = createRequire(import.meta.url); const { chromium } = require('playwright');
const root = path.dirname(new URL(import.meta.url).pathname);
const types = { '.js': 'text/javascript', '.html': 'text/html', '.ttf': 'font/ttf', '.otf': 'font/otf' };
const srv = http.createServer((req, res) => { const p = path.join(root, decodeURIComponent(req.url.split('?')[0]));
  fs.readFile(p, (e, d) => { if (e) { res.writeHead(404); res.end(); return; } res.writeHead(200, { 'Content-Type': types[path.extname(p)] || 'application/octet-stream' }); res.end(d); }); });
await new Promise((r) => srv.listen(0, r));
const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--enable-webgl'] });
const page = await browser.newPage({ viewport: { width: 320, height: 180 } });
await page.goto(`http://localhost:${srv.address().port}/look.html?w=320&h=180`);
await page.waitForFunction(() => window.ready, null, { timeout: 300000 });
const res = [];
for (const kz of [-0.13, -0.11, -0.09, -0.07]) for (const lift of [0.07, 0.08, 0.09, 0.1, 0.11, 0.12]) {
  const n = await page.evaluate(([l, k]) => { window.setHand(l, k); let c = 0, worst = 0;
    for (const s of [1, 4]) for (const r of window.qa(s)) { c += r.mm; const m = r.part.match(/^(\d+)/); if (m) worst = Math.max(worst, +m[1]); } return [c, worst]; }, [lift, kz]);
  res.push([kz, lift, ...n]); console.log(`kz ${kz}  lift ${lift}  people with contact ${n[0]}  worst ${n[1]} mm`);
}
await browser.close(); srv.close();
