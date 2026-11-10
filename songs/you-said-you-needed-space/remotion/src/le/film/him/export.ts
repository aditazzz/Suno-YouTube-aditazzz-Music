// node entry (bundled with esbuild by living_earth/him3d/him_export.sh): his per-frame track for the hero slots, from the engine.
//   node export.cjs <out dir> [diag]      -> <out dir>/<slot>.json (both formats), or a spark listing per slot (diag)
import * as fs from 'fs';
import { SLOTS, BLEND_S, frameAt } from '../engine';
import { HIM_RULES, HIM_RUNS, himAt, inShot, ownOut, sparkXY, toPx } from './track';
import { Fmt, Spark } from '../types';
import { himTrack } from '../sections/bridge';   // earth_c2_br: where the bridge draws his outline (his model origin, half span, far)
const FPS = 30, out = process.argv[2], diag = process.argv[3] === 'diag';
const RES: Record<Fmt, [number, number]> = { '169': [2560, 1440], '916': [1080, 1920] };
const r4 = (x: number) => Math.round(x * 1e4) / 1e4;
if (diag) for (const id of Object.keys(HIM_RULES)) {
  const i = SLOTS.findIndex((s) => s.id === id); if (i < 0) { console.log('no slot', id); continue; }
  const s = SLOTS[i];
  for (const fmt of ['169', '916'] as Fmt[]) for (const u of [0.02, 0.5, 0.95]) {
    const t = s.t0 + u * (s.t1 - s.t0), cam = frameAt(t, fmt).cam;
    console.log(`${id} ${fmt} u=${u} t=${t.toFixed(2)} cam x=${r4(cam.x)} y=${r4(cam.y)} r=${r4(cam.r)} sun=${cam.sun.map(r4)}`);
    for (const sp of (ownOut(i, t, fmt).sparks ?? []) as Spark[]) { const xy = sparkXY(sp, cam); console.log(`   spark xy=${r4(xy[0])},${r4(xy[1])} size=${r4(sp.size)} int=${r4(sp.intensity)} col=${sp.color.map(r4)} ${sp.rel ? 'rel' : sp.orbit ? 'orbit' : 'screen'}`); }
  }
}
else for (const run of Object.keys(HIM_RUNS)) {
  const ids = HIM_RUNS[run], sl = ids.map((id) => SLOTS.find((s) => s.id === id)!); if (sl.some((s) => !s)) { console.log('missing slot in run', run); continue; }
  const t0 = sl[0].t0, t1 = sl[sl.length - 1].t1, f0 = Math.round(t0 * FPS), f1 = Math.round((t1 + BLEND_S) * FPS) + 1;   // through the blend into the next slot
  const doc: Record<string, unknown> = { run, slots: ids, t0, t1, f0, f1: f1 - 1, fps: FPS, slotFrames: sl.map((s) => [s.id, Math.round(s.t0 * FPS), Math.round(s.t1 * FPS) - 1]),
    note: 'x,y: engine screen units (y up, frame height = 2); px in the master size of the format; w: the engine blend weight of the run (1 inside it); her: her disk (x, y, r); null x = no spark of his in the builder at that frame' };
  for (const fmt of ['169', '916'] as Fmt[]) {
    const [W, H] = RES[fmt], rows = [];
    for (let f = f0; f < f1; f++) {
      const t = f / FPS, fr = frameAt(t, fmt), hs = himAt(t, fmt, fr.cam).filter((x) => ids.includes(x.slot)), h = hs.sort((a, b) => b.w - a.w)[0], w = Math.min(1, hs.reduce((s, x) => s + x.w, 0));
      const base = { f, her: [r4(fr.cam.x), r4(fr.cam.y), r4(fr.cam.r)], sun: fr.cam.sun.map(r4), roll: r4(fr.cam.roll), shot: inShot(ids, t, fmt) };
      if (run === 'br') { const b = himTrack(t, fmt); Object.assign(base, { bt: { origin_px: toPx(b.origin[0], b.origin[1], fmt, W, H).map((v) => Math.round(v * 10) / 10), span_px: Math.round(b.halfSpan * H * 10) / 10, far: r4(b.far) } }); }
      rows.push(h ? { ...base, slot: h.slot, x: r4(h.x), y: r4(h.y), px: toPx(h.x, h.y, fmt, W, H).map((v) => Math.round(v * 10) / 10), size: r4(h.size), int: r4(h.intensity), col: h.color.map(r4), w: r4(w), vis: h.visible } : { ...base, x: null });
    }
    doc[fmt] = { res: RES[fmt], frames: rows };
  }
  fs.mkdirSync(out, { recursive: true }); fs.writeFileSync(`${out}/${run}.json`, JSON.stringify(doc));
  console.log('wrote', `${out}/${run}.json`, f0, f1 - 1);
}
