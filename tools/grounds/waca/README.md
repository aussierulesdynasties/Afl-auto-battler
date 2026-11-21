# WACA, Perth (AFL years 1990-2000): exterior model

Row 202 step 2b. Copied from the 1992 aerial photo `p92.png`; camera matched in `cam92f.json`.
Textures are hand-made by `tex.py` (no photo pixels). Stadium only: no field, no posts, no nets,
no sponsor boards, no lettering (director 2026-11-18). Own fence kept.

- `waca.glb`: the textured model.
- Rebuild textures: `python tex.py tex`
- Rebuild model + photo-camera render (Blender 5.2, run from this folder):
  `WACA_TEX=1 blender -b -P build.py -- out/waca_tex.glb out/r92t.png`
- Close-ups: `blender -b -P turn.py -- OUTDIR 0`; 96-frame turntable: `-- OUTDIR 96`
- Boards (photo | render | 50% overlay, part boards): `python boards.py`
- Proofs: `.claude/review/waca_*`
