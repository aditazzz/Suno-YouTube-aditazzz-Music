// node bake.mjs [name,name]  -> draws the card faces once and saves them to web/tex/*.png (the film loads these)
import http from 'http'; import fs from 'fs'; import path from 'path'; import { createRequire } from 'module';
const require = createRequire(import.meta.url); const { chromium } = require('playwright');
const root = path.dirname(new URL(import.meta.url).pathname); const only = process.argv[2] || '';
const types = { '.js': 'text/javascript', '.html': 'text/html', '.json': 'application/json', '.png': 'image/png', '.ttf': 'font/ttf', '.otf': 'font/otf' };
const srv = http.createServer((req, res) => { const p = path.join(root, decodeURIComponent(req.url.split('?')[0])); fs.readFile(p, (e, d) => { if (e) { res.writeHead(404); res.end(); return; } res.writeHead(200, { 'Content-Type': types[path.extname(p)] || 'application/octet-stream' }); res.end(d); }); });
await new Promise((r) => srv.listen(0, r));
const browser = await chromium.launch(); const page = await browser.newPage();
page.on('console', (m) => console.log('page:', m.text())); page.on('pageerror', (e) => console.log('PAGE ERROR', e.message));
await page.goto(`http://localhost:${srv.address().port}/bake.html${only ? '?only=' + only : ''}`); await page.waitForFunction(() => window.ready, null, { timeout: 600000 });
const out = await page.evaluate(() => window.out); fs.mkdirSync(path.join(root, 'tex'), { recursive: true });
for (const [k, url] of Object.entries(out)) { fs.writeFileSync(path.join(root, 'tex', k + '.png'), Buffer.from(url.split(',')[1], 'base64')); console.log('saved', k); }
await browser.close(); srv.close();
