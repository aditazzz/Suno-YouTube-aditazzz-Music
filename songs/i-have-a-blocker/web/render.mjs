// node render.mjs stills W H out_dir t1 t2 ...      -> JPEG stills
// node render.mjs range W H out.mp4 t0 t1 [fps]     -> silent video chunk (frames t0 <= t < t1)
import http from 'http'; import fs from 'fs'; import path from 'path'; import { spawn } from 'child_process';
import { createRequire } from 'module'; const require = createRequire(import.meta.url); const { chromium } = require('playwright');
const [mode, Ws, Hs, out, ...rest] = process.argv.slice(2); const W = +Ws, H = +Hs;
const root = path.dirname(new URL(import.meta.url).pathname);
const types = { '.js': 'text/javascript', '.html': 'text/html', '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg', '.ttf': 'font/ttf', '.otf': 'font/otf' };
const srv = http.createServer((req, res) => { const p = path.join(root, decodeURIComponent(req.url.split('?')[0]));
  fs.readFile(p, (e, d) => { if (e) { res.writeHead(404); res.end(); return; } res.writeHead(200, { 'Content-Type': types[path.extname(p)] || 'application/octet-stream' }); res.end(d); }); });
await new Promise((r) => srv.listen(0, r));
const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--enable-webgl'] });
const page = await browser.newPage({ viewport: { width: W, height: H } });
page.on('console', (m) => { const s = m.text(); if (!s.includes('GL Driver')) console.log('page:', s); }); page.on('pageerror', (e) => console.log('PAGE ERROR', e.message));
await page.goto(`http://localhost:${srv.address().port}/index.html?w=${W}&h=${H}${process.env.CLEAN ? '&clean=1' : ''}`);
await page.waitForFunction(() => window.ready, null, { timeout: 300000 });
const grab = async (t) => Buffer.from((await page.evaluate((tt) => window.renderAt(tt), t)).split(',')[1], 'base64');
if (mode === 'stills') {
  fs.mkdirSync(out, { recursive: true });
  for (const ts of rest) { const t0 = Date.now(); const b = await grab(+ts); fs.writeFileSync(path.join(out, `s_${(+ts).toFixed(2)}.jpg`), b); console.log('still', ts, Date.now() - t0, 'ms'); }
} else {
  const t0 = +rest[0], t1 = +rest[1], fps = +(rest[2] || 30);
  const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '14', '-pix_fmt', 'yuv420p', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const n0 = Math.round(t0 * fps), n1 = Math.round(t1 * fps); const tstart = Date.now();
  for (let n = n0; n < n1; n++) { const b = await grab(n / fps); if (!ff.stdin.write(b)) await new Promise((r) => ff.stdin.once('drain', r));
    if ((n - n0) % 30 === 0) console.log(`frame ${n} (${((n - n0 + 1) / ((Date.now() - tstart) / 1000)).toFixed(2)} fps)`); }
  ff.stdin.end(); await new Promise((r) => ff.on('close', r));
}
await browser.close(); srv.close();
