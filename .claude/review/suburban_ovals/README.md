# Six generic suburban ovals (row 202 step 2b)

t1 council, t2 grassy banks, t3 minor VFL/SANFL, t4 country, t5 community hub, t6 northern.

- model/: oval_*.glb (textures embedded), oval_*.blend (textures from src/tex), oval_*.tscn (Godot 4.7.2; all six load, 2.8k-5.0k tris).
- proof/tN/: turn_000-003.png (turntable stills), facade.png (close-up), turntable.mp4 (96 frames). Boards: t1/t4 board_nofield.jpg (photo|render|overlay), t3/t6 board_side.jpg (photo|model).
- src/: py/build.py (spec -> .blend + .glb), py/render.py, py/tex.py + tex_t1.py (hand-made textures), py/mk_*.py (specs), py/after5.sh (rebuild all), spec/*.json, tex/.

Director rulings applied (code kept behind switches):
- Field out: build.py draws field/markings only if spec field.draw is true.
- Posts out: build.py draws goal/behind posts only if spec posts.draw is true.
- No boards: sponsor boards off (tex_t1.py SPONSORS=False; t1 off_panels, t4 off_signs ignored by build.py).
- No lettering: tex.py and tex_t1.py LETTERS=False (scoreboard words removed; score digits kept).
- Stadium only: trees/cars stashed as bg_trees/bg_cars in specs for the later background pass.
- Each oval keeps its own fence. No nets.

Rebuild: cd to a folder holding py/ spec/ tex/, run `python py/tex.py && python py/tex_t1.py && bash py/after5.sh` (Blender 5.2).
