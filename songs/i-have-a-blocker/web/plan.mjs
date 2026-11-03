// node plan.mjs W H out.json -> runs window.capPlan() (the 9:16 caption planner in js/main.js) and saves its result
import http from 'http'; import fs from 'fs'; import path from 'path';
import { createRequire } from 'module'; const require = createRequire(import.meta.url); const { chromium } = require('playwright');
const [Ws, Hs, out] = process.argv.slice(2); const W = +Ws, H = +Hs; const root = path.dirname(new URL(import.meta.url).pathname);
const types = { '.js': 'text/javascript', '.html': 'text/html', '.json': 'application/json', '.ttf': 'font/ttf', '.otf': 'font/otf' };
const srv = http.createServer((req, res) => { const p = path.join(root, decodeURIComponent(req.url.split('?')[0]));
  fs.readFile(p, (e, d) => { if (e) { res.writeHead(404); res.end(); return; } res.writeHead(200, { 'Content-Type': types[path.extname(p)] || 'application/octet-stream' }); res.end(d); }); });
await new Promise((r) => srv.listen(0, r));
const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--enable-webgl'] });
const page = await browser.newPage({ viewport: { width: W, height: H } }); page.on('pageerror', (e) => console.log('PAGE ERROR', e.message));
await page.goto(`http://localhost:${srv.address().port}/index.html?w=${W}&h=${H}`);
await page.waitForFunction(() => window.ready, null, { timeout: 300000 });
const res = await page.evaluate(() => window.capPlan());
fs.writeFileSync(out, JSON.stringify(res, null, 1)); console.log(res.map((r) => `${r.i} y=${r.y} ${r.color} c=${r.cost} ${r.text}`).join('\n'));
await browser.close(); srv.close();
