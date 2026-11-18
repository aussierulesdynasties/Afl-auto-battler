# TIO Traeger Park exterior (row 202 2b)

Build scripts for the TIO Traeger Park stadium model. The model and its proofs are in `.claude/review/traeger/`.

The reference is the current ground: the Aug 2020 aerial and the 2025 Commons photos. Only the photos the proof scripts use are kept in `refs/`.

Applied rulings (2026-11-18, relayed through the ground secretary):

- no east shelter
- no sponsor boards (C)
- field left out
- no lettering (C)
- no goal or behind posts
- no nets

The boundary fence is kept. It is not a full ring: there is no fence along the stand and clubroom front (c05 and the
w04 close-up show the turf running to the bench feet). It runs from south of the stand round the east to north of the
clubrooms (`ring_sat.json` points 197 round to 124; north end where the satellite shows the fence line and its shadow
begin), and a low open chain-link turns in from the south end to the arch's north edge (w04, c05).

## Build (run in this folder; `B` = Blender 5.2; the `*.sh` chains set `S` to the original scratchpad, so point it here)

The current build is `chain13.sh` (r13): it runs steps 2-5 below in one go, plus the top-down render and the turntable
film frames. Set `S` at its top to this folder. It does not run step 1: after any texture change run
`texsite.py` (and the other texture scripts) by hand first.

1. `python texgen.py; python texclub.py; python texsite.py` writes the hand-made textures, `tex3/*.png` and `tex3/tex.json`.
2. `python stand.py && python standuv.py && python club.py && python model.py` writes `stand_uv.json`, `club_uv.json` and `prims.json`.
3. `"$B" -b --python blend.py -- prims.json cam.json out/rN` writes `traeger.blend` and `traeger.glb`.
4. Renders:
   - `aerial.py` renders the photo camera views;
   - `rcam.py -- cam_w04s.json <png> 1` renders the w04 view (`cam_w04s` is `cam_w04b` moved with the stand's shift by `camxf.py`);
   - `shots.py -- <dir>` renders 24 stills: 4 turntable stills, the facade close-up, the parts and the joins;
   - `turn.py -- <dir> 120 orbit|west` renders film frames (the orbit, or a pass along the stand); `ffmpeg` makes the mp4.
5. `python proofboard.py out/rN <shots dir>` writes the photo, render and overlay boards.
6. Top-down gate step (plan shape from straight-down sources only):
   - `topdown.py -- <png> x0 y0 x1 y1 ppm` renders the model straight down (orthographic, field frame);
   - `satg.py` cuts the satellite to the same box and scale (g19 for the whole ground, g20 for the stand);
   - `python topov.py <model png> <sat png> prims.json <out> x0 y0 x1 y1 ppm` writes `_half` (model at 50%) and
     `_lines` (model edges magenta, fence cyan), turned north-up, with a north arrow and a 50 m bar.

Patch steps used after the full build:

| Script | Change |
|---|---|
| `fix_r9*.py` | roof winding; `pairfix.py` keeps roof tops up and soffits down |
| `drop_es.py` | removes the east shelter |
| `drop_field.py` | field out; `ring.py` makes the apron a ring to the fence |
| `nolet.py` | removes the lettering from the texture scripts |
| `nolet_blend.py` | reloads the textures and re-exports the GLB |

The other `*.py` files are measurement and fitting tools: camera fits, pixel grids, boundary picks and satellite reads.

Notes on the r13 parts:

- The south front stair passes over the arch (w04: arch s 9.0-10.9, crown 1.75 m). Its steps start at the crown
  over the arch, and the arch has a rounded head back to the under-deck wall. There is no separate upstand face on
  the front line: it hid the arch.
- Chain-link is 3 mm wire on a 50 mm mesh (`texsite.py`). The rail materials use blended alpha in `blend.py`;
  Eevee's dithered alpha turned the fine mesh into grain over dark walls.
