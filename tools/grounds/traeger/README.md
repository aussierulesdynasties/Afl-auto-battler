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

The boundary fence is kept.

## Build (run in this folder; `B` = Blender 5.2; the `*.sh` chains set `S` to the original scratchpad, so point it here)

1. `python texgen.py; python texclub.py; python texsite.py` writes the hand-made textures, `tex3/*.png` and `tex3/tex.json`.
2. `python stand.py && python standuv.py` writes `stand_uv.json`.
3. `"$B" -b --python blend.py -- prims.json cam.json out/rN` writes `traeger.blend` and `traeger.glb`.
4. Renders:
   - `aerial.py` renders the photo camera views;
   - `rcam.py -- cam_w04b.json <png> 1` renders the w04 view;
   - `shots.py -- <dir>` renders 16 stills: 4 turntable stills, the facade close-up and the rest.
5. `python proofboard.py out/rN <shots dir>` writes the photo, render and overlay boards.

Patch steps used after the full build:

| Script | Change |
|---|---|
| `fix_r9*.py` | roof winding; `pairfix.py` keeps roof tops up and soffits down |
| `drop_es.py` | removes the east shelter |
| `drop_field.py` | field out; `ring.py` makes the apron a ring to the fence |
| `nolet.py` | removes the lettering from the texture scripts |
| `nolet_blend.py` | reloads the textures and re-exports the GLB |

The other `*.py` files are measurement and fitting tools: camera fits, pixel grids, boundary picks and satellite reads.
