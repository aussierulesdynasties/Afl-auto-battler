# WACA, Perth (AFL years 1990-2000): exterior model

Row 202 step 2b. Copied from the 1992 aerial photo `p92.png`; camera matched in `cam92f.json`.

**Camera warning (28 Nov 2026):** `cam92f.json` is biased at the east end. Against the
Google Earth placement of the scoreboard it puts the board's edges 36-73 px off and
draws it about 30% narrower than the photo (86 px against 123 px or more). Do not use
this camera to position or size east-side structures (scoreboard, SE light tower); use
Google Earth 3D and the registered aerials. `towfit.py` flags any column match whose
photo width is more than 1.5x off the projected width.
Textures are hand-made by `tex.py` (no photo pixels). Stadium only: no field, no posts, no nets,
no sponsor boards, no lettering (director 2026-11-18). Own fence kept.

- `waca.glb`: the textured model.
- Rebuild textures: `python tex.py tex`
- Rebuild model + photo-camera render (Blender 5.2, run from this folder):
  `WACA_TEX=1 blender -b -P build.py -- out/waca_tex.glb out/r92t.png`
- Close-ups: `blender -b -P turn.py -- OUTDIR 0`; 96-frame turntable: `-- OUTDIR 96`
- Boards (photo | render | 50% overlay, part boards): `python boards.py`
- Proofs: `.claude/review/waca_*`
