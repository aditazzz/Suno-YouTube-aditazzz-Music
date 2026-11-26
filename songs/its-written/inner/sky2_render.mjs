// node render_final.mjs --out <dir> [--w 1920 --h 1080] [--ns 8] [--frames 2632-3321] [--list "2632,2700"] [--q 0.97] [--png] [--grade grade.json] [--bank '{"tilt":40}']
// The final pass of the world inside the grain. Headless Chrome on the Mac GPU; run through tools/gpuq.sh. Frames already on disk are kept (a stopped run resumes).
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';
const HERE = path.dirname(fileURLToPath(import.meta.url));
const require = createRequire('songs/great-idea-ted-v3/web/');
const { chromium } = require('playwright');
const arg = (k, d) => { const i = process.argv.indexOf('--' + k); return i < 0 ? d : (process.argv[i + 1] ?? true); };
const has = k => process.argv.includes('--' + k);
const W = +arg('w', 1920), H = +arg('h', 1080), NS = +arg('ns', 8), Q = +arg('q', 0.97);
const out = path.resolve(arg('out', path.join(HERE, 'work/fin/frames'))); fs.mkdirSync(out, { recursive: true });
const png = has('png'), ext = png ? '.png' : '.jpg';
let list = [];
if (arg('list', null)) list = String(arg('list')).split(',').map(Number);
else { const [a, b] = String(arg('frames', '2632-3321')).split('-').map(Number); for (let f = a; f <= (b ?? a); f++) list.push(f); }
const name = f => path.join(out, 'f_' + String(f).padStart(4, '0') + ext);
list = list.filter(f => !(fs.existsSync(name(f)) && fs.statSync(name(f)).size > 2000));
const timing = Object.assign(JSON.parse(fs.readFileSync(path.join(HERE, 'timing_inner.json'), 'utf8')), { motif: JSON.parse(fs.readFileSync(path.join(HERE, 'work/motif.json'), 'utf8')) });
timing.hand = JSON.parse(fs.readFileSync(path.join(HERE, 'sky_hand.json'), 'utf8'));
const gradeFile = arg('grade', path.join(HERE, 'grade_sky.json')); if (fs.existsSync(gradeFile)) timing.grade = JSON.parse(fs.readFileSync(gradeFile, 'utf8')).keys;
if (arg('bank', null)) timing.bank = JSON.parse(arg('bank'));
const t00 = Date.now(); let rc = 0;
if (!list.length) { console.log('done 0 frames (all on disk) ->', out); process.exit(0); }
const browser = await chromium.launch({ channel: 'chrome', headless: true, args: ['--use-angle=metal', '--enable-gpu', '--ignore-gpu-blocklist', '--enable-webgl', '--disable-gpu-vsync', '--disable-frame-rate-limit', `--window-size=${W},${H}`] });
try {
  const page = await browser.newPage({ viewport: { width: Math.min(W, 1920), height: Math.min(H, 1080) } });
  page.on('console', m => console.log('[page]', m.text()));
  page.on('pageerror', e => { console.log('[pageerror]', e.message); rc = 1; });
  await page.setContent('<html><body style="margin:0;background:#000"><canvas id="c"></canvas></body></html>');
  await page.addScriptTag({ content: fs.readFileSync(path.join(HERE, arg('page', 'sky2_page.js')), 'utf8') });
  const info = await page.evaluate(async o => await window.OG.init(o), { w: W, h: H, frag: fs.readFileSync(path.resolve(arg('frag', path.join(HERE, 'sky2.frag'))), 'utf8'), timing });
  console.log('renderer:', info.renderer, 'compile ms:', Math.round(info.compileMs), 'uniforms:', info.uniforms, 'grade keys:', (timing.grade || []).length);
  let k = 0; const t0 = Date.now();
  for (const f of list) {
    const r = await page.evaluate(([f, ns, type, q]) => { const p = window.OG.renderFrame(f, ns, 0.5, 1.0); return { url: window.OG.grab(type, q), p }; }, [f, NS, png ? 'image/png' : 'image/jpeg', Q]);
    const buf = Buffer.from(r.url.split(',')[1], 'base64'); if (buf.length < 2000) throw new Error('empty frame ' + f);
    fs.writeFileSync(name(f) + '.tmp', buf); fs.renameSync(name(f) + '.tmp', name(f));
    k++; if (k % 30 === 0 || k === list.length || k === 1) console.log(`frame ${f} t=${(f / 30).toFixed(3)} ns=${r.p.ns}  ${k}/${list.length}  ${((Date.now() - t0) / k).toFixed(0)} ms/frame`);
  }
  console.log('done', list.length, 'frames in', ((Date.now() - t00) / 1000).toFixed(1), 's ->', out);
} catch (e) { console.log('ERROR', e.message.slice(0, 3000)); rc = 1; }
await browser.close();
process.exit(rc);
