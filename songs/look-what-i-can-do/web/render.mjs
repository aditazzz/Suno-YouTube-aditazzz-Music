// node render.mjs stills W H out_dir t1 t2 ...      -> JPEG stills
// node render.mjs range W H out.mp4 t0 t1 [fps]     -> silent video chunk (frames t0 <= t < t1)
// PAGE=test.html picks another page (default film.html). GPU=1 uses the machine's GPU (Metal on a Mac).
import http from 'http'; import fs from 'fs'; import path from 'path'; import { spawn } from 'child_process';
import { createRequire } from 'module'; const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PW || '/opt/npm-tools/node_modules/playwright');
const [mode, Ws, Hs, out, ...rest] = process.argv.slice(2); const W = +Ws, H = +Hs;
const root = path.dirname(new URL(import.meta.url).pathname);
const types = { '.js': 'text/javascript', '.mjs': 'text/javascript', '.html': 'text/html', '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg', '.ttf': 'font/ttf', '.otf': 'font/otf', '.hdr': 'application/octet-stream' };
const srv = http.createServer((req, res) => { const p = path.join(root, decodeURIComponent(req.url.split('?')[0]));
  fs.readFile(p, (e, d) => { if (e) { res.writeHead(404); res.end(); return; } res.writeHead(200, { 'Content-Type': types[path.extname(p)] || 'application/octet-stream', 'Cache-Control': 'max-age=3600' }); res.end(d); }); });
await new Promise((r) => srv.listen(0, r));
const GPU_ARGS = ['--use-angle=metal', '--enable-gpu', '--ignore-gpu-blocklist', '--enable-webgl'];
const CPU_ARGS = ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--enable-webgl'];
const browser = await chromium.launch({ headless: true, args: process.env.GPU ? GPU_ARGS : CPU_ARGS });
const page = await browser.newPage({ viewport: { width: W, height: H } });
page.on('console', (m) => { const s = m.text(); if (!s.includes('GL Driver') && !s.includes('GPU stall')) console.log('page:', s); });
page.on('pageerror', (e) => console.log('PAGE ERROR', e.message));
await page.goto(`http://localhost:${srv.address().port}/${process.env.PAGE || 'film.html'}?w=${W}&h=${H}${process.env.Q ? '&' + process.env.Q : ''}`);
await page.waitForFunction(() => window.ready, null, { timeout: 600000 });
const grab = async (t) => Buffer.from((await page.evaluate((tt) => window.renderTime(tt), t)).split(',')[1], 'base64');
if (mode === 'stills') {
  fs.mkdirSync(out, { recursive: true });
  for (const ts of rest) { const t0 = Date.now(); const b = await grab(+ts); fs.writeFileSync(path.join(out, `s_${(+ts).toFixed(2)}.jpg`), b); console.log('still', ts, Date.now() - t0, 'ms'); }
} else {
  const t0 = +rest[0], t1 = +rest[1], fps = +(rest[2] || 30);
  const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-preset', process.env.PRESET || 'veryfast', '-crf', process.env.CRF || '16', '-pix_fmt', 'yuv420p', out + '.part.mp4'], { stdio: ['pipe', 'inherit', 'inherit'] });
  const n0 = Math.round(t0 * fps), n1 = Math.round(t1 * fps); const tstart = Date.now();
  for (let n = n0; n < n1; n++) { const b = await grab(n / fps);
    if (!ff.stdin.write(b)) await new Promise((r) => ff.stdin.once('drain', r));
    if ((n - n0) % 30 === 0) console.log(`[${path.basename(out)}] frame ${n} (${((n - n0 + 1) / ((Date.now() - tstart) / 1000)).toFixed(2)} fps)`); }
  ff.stdin.end(); await new Promise((r) => ff.on('close', r)); fs.renameSync(out + '.part.mp4', out);
}
await browser.close(); srv.close();
