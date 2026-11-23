# The first 30 seconds (rl_first30, Nov 15)

Shots 1A-2D of `build/codeplan/first30.md`, one file each, registered in `../index.ts`. Every moving thing is code keyed to
rl_shots' measured cues (`cueFrame`) or the beat grid (`shot.grid`), so a plate swap never moves a beat.

`kit.tsx` = `Cam` (stage camera; children ride the move — the engine's `<Plate>` does not move its children), `MBlur`
(shutter-sample motion blur), `hit` (camera hit), `swap` (A-smear-B), `flick`/`flickOut`, `pendulum`, `HeroClip`.

## Swapping in the real plates (one place per shot)

| Shot | Now (placeholder) | Swap to | Where |
|---|---|---|---|
| 1A/1B, 1C, 1H | `plates/dawn.jpg` graded to night + code windows/sign/clock/tail | NS1 (1AB), NS2 (1C, 1H) | `street.tsx` `STREET` (plate, window rects, door, roof, clock, lamps, tail pivot); drop `NIGHT_GRADE` on a real night plate |
| 1A tail 0-2.60 s | code tail (`Tail`) | H3 TAIL RGBA frames | `heroes.json` H3: `ready: true`, frames in `public/first30/heroes/H3_tail/f_<frame>.png` |
| 1D | `plates/room_b2b.jpg` | S3 T1 (+ T1b paw) | `S1D.tsx` `T1` (plate, floor line, parcel path, clock spot) |
| 1E | code dispenser + tally on a soft wall crop | S4 T2 | `S1E.tsx` (keep the strip/tear and the split-flap layers, pin them to the plate) |
| 1F | `plates/meter.jpg` + code rack/slip/stamp | S5 T3a/T3s/T3b | `S1F.tsx`: plate per `swap()` state, keep the ink layer on the slip quad `SLIP` |
| 1G | S6 M1 preview + needle | S6 final | `build/first30/tools/prep_assets.py` (prefers a `final/` still), positions from its layout.json |
| 1I | `plates/door.jpg` + code glass leaf + code locks | H2 DOOR frames 565-603 (+ lock regions) | `heroes.json` H2; `door.tsx` `DOOR` for the S7 plate |
| 2A | `door.jpg` softened + code sign | S7 D1 closed + sign RGBA | `door.tsx` `DOOR.plate`; `S2A.tsx` `SIGN` |
| 2B | S8 C0/C0s/C1 previews (+ code 429 while the preview lacks it) | H1 PADDLE 724-766 / S8 finals | `heroes.json` H1; `prep_assets.py`; the code 429 turns itself off when C1 is a final |
| 2C | `door.jpg` + rl_screens ripple | S7 D1 (+ D1p paddle region) | `door.tsx` `DOOR.glass` corners |
| 2D | code parcel + cloth on a soft desk crop | S9 T5a/T5s/T5b | `S2D.tsx` (keep the 97% label as a code layer on the plate's label) |

**v2 (rl_first30_v2, Nov 15):** 1D = S3 T1 (`S1D.tsx` StageT1: T1's own RGBA parcels, jamb strip + boot matte redrawn over
them, paw region on each crossing, code clock hands; framed so the 429 paddle by his desk stays out until 2B). 1E = S4 T2
(`S1E.tsx` StageT2: plate_nostrip + strip.png tear, code split-flaps in the plaque windows; 9:16 puts the plate at 0.75 on its own
wall). 1I/2A/2C = S7 D1 (`door7.tsx`; lock states from `build/first30/tools/prep_locks.py`). 2B = H1 hero (ready). Each falls back
to its v1 stage if the files are missing (`HAVE_S7`, `HAVE_T2`, `t1flag.ts`).

After new stills land: `.venv/bin/python build/first30/tools/prep_assets.py`, then the render (`build/first30/run_v1.sh <tag>`, one gpuq job).

**v3 (rl_first30_v3, Nov 15):** the real night street (`ns.tsx`: NS1 for 1A/1B with `camNS1` on the 2560x2400 tall plate, NS2 tall for 1C,
NS2 whole night/grey for 1H; windows = lit-window crops over plate_dark, sign = additive `sign_add.png`, hands/tail/parcels in code, NS1's own
fg), 2B = HeroClip `H1b` (the cam2 take 704-773; `heroes.json` H1b.track drives the 9:16 crop), 2C = over his shoulder on `S7_2C` K0/K1/P2
(fallback: stepped push), 1I locks = hard-cut ECUs on `S7_locks` (fallback: stepped push to 2.1), red rule = `teal.ts` (teal recolors from
`prep_teal.py`), glow = `glow.tsx` (stand-in path: CC0 branch + halos; NS1: lamp halos). Prep order after new stills:
`prep_assets.py` -> `prep_locks.py` -> `prep_teal.py` -> `prep_v3.py` (finals only; `--previews` for look-dev). Hero: `import_hero.py`.
Render: `build/first30/run_v3.sh <tag>` (one gpuq job: render + sweeps + sheet + native clip pass + text-fit).
