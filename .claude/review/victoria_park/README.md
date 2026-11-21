# Victoria Park (Collingwood) exterior, row 202 step 2b

Model of the stadium as in the 1990s full-house aerial (Austadiums victoria-park-1990s.jpg; `ref/ref_full.png` is the
director's 2000x1355 copy). Stadium only: no field, no goal posts, no lettering, bare fence, no nets, no background.

- `vicpark_exterior.glb`: the model (hand-painted textures embedded, no photo pixels).
- `src/`: `spec.py` -> `meshes.json`; `paint.py` -> `tex3/`; `build.py` renders in Blender 5.2 (Cycles):
  `blender -b -P build.py -- OUTDIR` (matched view), `-- OUTDIR views_all.json` (turntable and close-ups),
  `-- OUTDIR glb` (exports the GLB). Run from `src/` with `ref/photo.jpg` and `ref/ref_full.png` copied beside it.
  `overlay_full.py RENDER OUTDIR` makes the 50% overlay; `cropboard.py OUTDIR` the per-part crop board.
- `proof/`: board_full (photo | render | 50% overlay), overlay50_full, crop_board, turn4 + turn_*, close-ups cu_*.
- `../vicpark_photo_choice.png`: the reference photo choice board.
