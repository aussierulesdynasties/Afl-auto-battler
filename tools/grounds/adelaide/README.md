# Adelaide Oval in the game (row 202 2b)

The model is the one merged in #1856 (`.claude/review/adelaide`: `tools/gen.py` writes `model/*.ply`, the Blender
proofs paint it with the procedural shaders in `tools/shade.py`). Those shaders only exist in Blender, so the game
gets its own version:

1. `python3 tools/grounds/adelaide/paint.py`: each material kind's pattern (concrete panels, membrane seams, steel
   sheets, glass, brick, copper, stone, Hill seat rows ...) painted as a tiling grey detail texture in `tex/`
   (no photo pixels).
2. `blender -b --python tools/grounds/adelaide/export.py -- <out>`: every part split by kind (the PLY alpha holds
   it), the vertex colours (the colours read off the photos) kept, UVs in metres over each texture's tile, a grass
   floor under the field hole, written as `adelaide.glb`; the 56,606 instanced seats as `seat_tmpl.bin` and
   `seats_seat_ao_<colour>.bin`. Copy the output to `assets/grounds/adelaide/`.

The glb paints with its vertex colours, which Godot's glTF reader does not do on its own: `GroundModels.VERTEX_COLOURED`
turns it on. The fence fit in `GroundModels.FIT` was measured with `tools/grounds/fit_fence`.
