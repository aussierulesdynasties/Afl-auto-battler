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

## v7: to the MCG standard (2026-11-22)

Checked against Google Earth 3D (36 views) and a 2019 photo sphere taken on the ground
(docs/MCG_STANDARD.md). The plan (bowl, roof outline, towers) already matched Google Earth; the rest was rebuilt:

- **Outside walls**: charcoal cladding over a grey precast first floor (`facade_v7.png`), no blue glass.
- **Steel, all modelled**: a white column at every rafter from the footpath to 5 m above the roof, a stay from
  its top onto the roof, two white ring beams (under the fascia and at 14 m) with an X in every bay, and struts
  back to the wall.
- **Roof**: a sheet with depth (white top, pale grey-green underside 0.35 m below, a 1.2 m outer fascia), each
  bay sagging between the rafters; no tent peaks. Under it: a dark tapered rafter at every column, a rib down
  each bay and the leading-edge truss along the inner edge.
- **Seats**: gold, maroon in whole blocks, some white (photo sphere). Box fronts dark glass under an LED ribbon
  (plain colour blocks, no lettering). Hyundai Centre piers white, not blue.
- **Surroundings**: `surrounds.py` (Woolloongabba from OpenStreetMap, the house yards filled with trees, the
  CBD's towers), loaded through `GroundModels.SURROUNDS`.

Build in the cloud with the bpy module: `python mktex_v7.py`, then build.py with
`sys.argv = ['blender', '--', 'model_in6.json', OUT.glb, OUT.blend, 'htex']` (model_in6 is the current input),
copy the glb and seat bins to `assets/grounds/gabba` (`seats_seat_<c>.bin` -> `seats_seat_gabba_<c>.bin`),
`godot --headless --import`, `seat_check.gd -- gabba`. QA views are in `qa/` for `tools/grounds/ge_compare.py`.
