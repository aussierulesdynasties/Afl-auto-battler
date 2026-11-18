# Gabba exterior model (row 202 grounds)

`gabba.glb` is the Gabba stadium (82,569 triangles), built from reference photo `refs/g49.jpg`.
Every texture in `htex/` is hand-made (painted or procedural by `mktex_hand.py` and `mktex_sw.py`); no photo pixels.

Director rulings applied (2026-11-18): "Leave field out" (no playing field, the game draws its own grass inside the
fence), "C: no lettering" (Gate 7's "7" and the gate block's cross sign are blank panels), "Posts out" (the model has
no goal or behind posts). The boundary fence (1.6 m wall) stays; there are no nets. Stadium only, no surroundings.

Proof set: `.claude/review/gabba_*` (turntable mp4, photo|model|overlay board, parts board, stills, close-ups).

## Rebuild

Needs Blender 5.2, Godot 4.7.2 and Python with numpy, Pillow, scipy and imageio-ffmpeg. Run from this folder.

1. `python mktex_hand.py && python mktex_sw.py` writes the textures to `htex/`.
2. `bash full2.sh model_in5.json TAG` builds `gabba.glb` (`build.py` runs `sw.py` for the south-west gate buildings),
   renders the photo-matched view (`camB.json`) and writes `TAG_board_full.png` and `TAG_parts.png`.
3. `bash h8chain.sh` runs step 2 (tag h12), the Godot turntable and close-ups (`rt2.sh`, `tt.gd`, `closeup.gd`, project in
   `gp/`), the sunlit seat close-up and `gabba_exterior.mp4`. The Godot path in `rt2.sh`/`h8chain.sh` is this PC's.

Knobs and measured part positions are in `model_in5.json`; `geo.py` holds the camera projection.
