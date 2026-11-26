# Norwood Oval (Coopers Stadium), Kent Town, Adelaide

The ground rebuilt to the MCG standard (docs/MCG_STANDARD.md), 2026-11-22.

- Model origin: the centre circle, lat -34.919825, lon 138.630446 (Google Earth top-down mosaic); x east,
  y north, z up in Blender; the glb has x east, y up, -z north. Field level 0 (Google Earth ~50 m).
- Build (pip bpy 5.2.4 venv): `python model/tex.py && python model/build.py glb <outdir>` then copy
  `norwood.glb` and the `seat*_nw_*.bin` files into assets/grounds/norwood/. `model/build.py render <png> "x,y,z,tx,ty,tz,lens"`
  gives a Cycles preview.
- Parts: `ses.py` Sir Edwin Smith Stand (south), `west.py` Western Stand and the Woods/Beer/Coopers corner
  building (WBCC, south-west), `north.py` the clubrooms, hall and sheds at the north-west and north,
  `arena.py` fence, terraces, apron, benches and the four light towers.
- Positions: Google Earth top-down tiles (lean-corrected), OpenStreetMap (pitch way 190682898, stands), and
  satellite imagery checked by eye only (none of it is shipped or committed).
- QA: `qa/ge_compare.py` (plan/sheet), `qa/ge_shoot.js`. Google Earth snaps a view's target to the 3D
  mesh under it, so every view targets open grass (as at Manuka).
- Rulings kept from 2026-11-18: no sponsor boards or lettering on the model; the ground's own picket fence stays.
