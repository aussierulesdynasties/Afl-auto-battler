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
- **Roof**: a sheet with depth (white top, cream PTFE underside 0.35 m below, drawn as `membrane_lit_under` so the match lights it
  through with the sun (Oval3DTurf.MEMBRANE_THROUGH; the only ground excepted from the grey-green underside rule), a 1.2 m outer fascia), each
  bay sagging between the rafters; no tent peaks. Under it: a dark tapered rafter at every column, a rib down
  each bay and the leading-edge truss along the inner edge.
- **Seats**: gold, maroon in whole blocks, some white (photo sphere). Box fronts dark glass under an LED ribbon
  (plain colour blocks, no lettering). Hyundai Centre piers white, not blue.
- **Light towers**: white lattice baskets (11 ribs, 4 rails, lamp boxes facing the field), not flat panels.
- **No painted geometry (v8)**: box fronts' mullions, sill, transom and capping; the Hyundai Centre's louvre boxes
  (frame and six fins) and shopfront mullions and head; the gate block's recessed opening with glazed doors, the
  portholes and round window with reveals, the glass-block stair and its rail; the Gate 7 roof's upstand and vents;
  the terrace's tables and benches; the skylight's frames. All modelled; the textures carry only surface colour.
  The gate's painted "7" is gone (director "C: no lettering").
- **Big screens**: on the upper tier's front at the north and south ends, in a 4 m deep housing (photo sphere).
- **Surroundings**: `surrounds.py` (Woolloongabba from OpenStreetMap, the house yards filled with trees, the
  CBD's towers), loaded through `GroundModels.SURROUNDS`. Buildings within 600 m
  (`facades`) are modelled closer: floors with recessed window bands and reveals, a recessed glazed street floor on
  low shops, hipped roofs on houses; Low draws them plain. The bowl is cut into 12 pieces (`GroundModels.SLICE_AT`): High / Medium / Low draw 2.98 /
  2.66 / 2.02 million triangles and 353 / 312 / 297 draw calls (the MCG 3.33 / 3.03 / 2.43 million) (docs/PHONE_3D_BUDGET.md).

Build in the cloud with the bpy module: `python mktex_v7.py`, then build.py with
`sys.argv = ['blender', '--', 'model_in6.json', OUT.glb, OUT.blend, 'htex']` (model_in6 is the current input),
copy the glb and seat bins to `assets/grounds/gabba` (`seats_seat_<c>.bin` -> `seats_seat_gabba_<c>.bin`),
`godot --headless --import`, `seat_check.gd -- gabba`. QA views are in `qa/` for `tools/grounds/ge_compare.py`.

## v9: heights measured in Google Earth (2026-11-22)

Measured with the mouse in Google Earth 3D (the status bar gives lat/lon and height under the pointer). The
heights are above Google Earth's turf (-3 m). There were 2,052 hovers from a camera 450 m straight above the centre
(36 bearings), 290 more down two columns of an oblique view whose camera was solved from them (1.6 px rms), and
a side view from the north. Google Earth's heights check out on the south-west light tower: 74 m there, 74.2 m in
the model.

- **Roof**: flat at 24 m from the inner edge to the outer edge at every bearing (`zi` = `zo` = 24.0; it was
  38.7 m falling to 29.3 m). The rafters are 1.6 m deep at the back (was 2.8 m), so they clear the top rows.
- **Plan**: the inner edge has no size error (best-fit scale 0.992, leftover 0.75 m rms, worst 1.75 m).
  Google Earth puts the whole ground 2.3 m west (dx -2.28 m, dy +0.17 m). The seat front moves with it, so the
  model keeps its origin; ge_compare offsets Google Earth instead.
- **Bowl**: the upper tier overhangs the lower one. The lower tier rises about 0.45 m per metre to 9 m, 20 rows
  (`tier1_top`, `lower_split`), and runs on under the upper tier to the glass of the boxes. The upper tier starts
  at 11 m (`upper_front`, `upper_split`) and rises over 16 rows to 19.8 m (`bowl_top`). That makes 37,286
  seats, against 37,478 for AFL (Wikipedia; the venue's own page says 42,000, of which 2,609 are corporate). The
  old bowl had 27 rows and no overhang: 27,994 seats. The build drops any seat with less than 2 m clear over it,
  as the seat rule does.
- **Screen**: one screen, at the west end over the goals: 18.8 m wide, 9.0 m to 19.1 m up, centred 4.6 m
  north of the long axis. Google Earth (2023) has no screen at the north, south or east, so the v7 north and
  south screens were removed.
