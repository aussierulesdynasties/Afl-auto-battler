# Whitten (Western) Oval exterior, AFL 1990-97 (Director Bible 2.90)

Copied from the 1986 aerial `e86_l.jpg` (Footscray Historical Society). Hand-made procedural textures only, no photo pixels.
Director rulings applied: field left out, no goal or behind posts, no boards, no lettering (signs are blank panels),
the ground's own boundary fence kept, no nets. Stadium only (no courts, car park, road, houses or trees).

- `cam.py` / `cam.json` / `geo.json`: the camera fitted to the photo (rms 2.2 px).
- `model2.py` -> `model2.json`: every part, picked off the photo's pixel grid (`pxgrid.py`) and back-projected through that camera.
- `blend2.py`: builds the Blender scene and its procedural materials (STYLE table). `-- final w3` = matched render + w3.blend; `-- final w3t tt` = turntable scene.
- `tt.py`: close-ups, turntable stills, turntable mp4. `bake.py`: the GLB. `board2.py`: photo | render | 50% overlay board and the parts board.
- `runall.sh`: the whole chain (Blender 5.2). Run from this folder after `python model2.py`.

Proof set: `.claude/review/whitten_*`.
