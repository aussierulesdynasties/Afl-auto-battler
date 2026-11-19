# Gabba exterior model: ready for gate (row 202 step 2b)

Model: tools/grounds/gabba/gabba.glb (83,227 tris), built by tools/grounds/gabba/build.py + sw.py from model_in6.json.

## Proofs (this folder)
- Camera-matched overlay on photo g49: v6_ov.png (model edges on the photo).
- Top-down on the Esri 2011 satellite tile: topov_s.png (straight), topov_l.png / topov_l_blend.png (lean-matched), edge_l.png (outline).
- Turntable: tt.gif (60 frames), tt_sheet.png.
- Gate fault fixes beside the photo crops the director named: board_faults.png, board_gate7_flat.png (Gate 7 flat paint). East roof edge proof: east_edge_proof.png.
- Close-ups and joins: cu_*.png (gate 7, gate 7 from the NE, fan drums from above and from the east, gate block, facade, south, edge, west, north, plant, screen, white building, navy side, roof deck, mast, roof top, roof underside, seats west/east).
- Texture beside photo crop: board_textures.png. Signs beside photo crop: board_signs.png. Stddev list: stddev.txt.

## Gate faults of 2026-11-19, fixed
- Gate 7 block: navy all over with a maroon strip only at the bottom (0-3.4 m), as photo g49 (330, 900, 450, 1000).
  The white "7" (2.5 m tall) sits in the strip on the Vulture St face; the NE face carries the same strip
  (textures n7front, n7strip). Both bands are flat paint as in the photo: no run-off streaks, no panel lines
  (gate of 2026-11-20, "Send streaks back"). board_gate7_flat.png, board_faults.png rows 1 and 4, cu_gate7.png, cu_gate7ne.png.
- Fan building: the two short capped tubes are now open-topped round drums, 4.3 m tall on the 15 m roof, each with a
  fan housing inside and a steel frame across the rim, as photo g49 (290, 860, 420, 950). Footprints from the
  satellite. Height from the photo: rim top to base is 27 px in g49 and 26 px in our render through the same camera,
  rim widths 33 and 31 px. board_faults.png rows 2 and 2b, cu_fans.png, cu_fans_low.png.
- East roof edge in the g49 overlay: the camera fit, measured (east_edge_proof.png). Three objects next to that edge
  are placed from the satellite, and the director passed the top-down: the big fan drum, the small fan drum and the
  Gate 7 corner. In g49 the camera puts them 40, 30 and 57 px off, all towards the photo's upper left, the same
  direction as the roof-edge gap. The fit gives the outer roof edge no weight (fit10.py), so nothing holds the camera
  in that corner. In plan the east membrane tips at y = 0 sit at 112.5-113 m against the satellite's 115 m,
  2-2.5 m or about 12 px in g49. The rest of the 40 px is the camera.

## What changed since the "lobsided" fault
- Plan from satellite and OSM only: even roof ring, centred ~1.2:1 opening (long axis E-W), fence oval matching, E/W blocks on their outlines.
- NE corner (gate block, Gate 7 navy block, white fan building) placed from the satellite footprints and OSM part 483353591.
- 411 Vulture St removed: it is outside the OSM site polygon, a separate office building beyond the fence.
- Sun refit to elevation 21 deg (azimuth -12, east): the shadow on the east field matches the photo; sky fill 0.35 so west seats are no brighter than the photo's shade.
- Membrane shadow crescents: the slot between facade top and roof underside let sun through as a lit stripe; a dark band now closes it up to 26 m; above that the roof lifts at each mast as in the photo, which gives the chain of crescents. The photo's chain sits ~15 m further from the east boundary than ours.

## Lean method
A satellite photo is not straight down, so tall things appear shifted sideways by (lean x height). For the 2011 tile the
lean is about 0.117 m sideways per metre up, towards the south-west. The top-down proof renders the model with the
same shift applied to every vertex (x += -0.117 h, y += -0.117 h), so roof tops are compared where the satellite shows
them, and footprints (h = 0) stay where they are.

## Crowd
No crowd parts existed in this model (no cards, painted crowd, billboards or crowd meshes). Seats are drawn seat by seat
in their real colours, empty: cu_seats_w.png and cu_seats_e.png.

## Signs (iconography ruling 2026-11-19)
- Gate 7 "7" on the Vulture St face of the navy block, in the maroon strip, hand-drawn from the g49 crop
  (board_faults.png row 1). It replaces the blank panel from the 2026-11-18 "no lettering" ruling.
- Gate block round crest window, hand-drawn (board_signs.png).
- The small sign beside the gate block's dark opening is unreadable in every reference, so it stays a blank panel.
- No sponsor ads, banners or posters.

## Textures
Hand-painted (mktex_hand.py, mktex_sw.py): joints, rain run-off streaks starting at ledges, mottling, grime in the
membrane valleys beside each boom, seat-by-seat seats with aisles. Each texture is shown beside its photo crop
(board_textures.png, board_faults.png); stddev.txt is kept for reference.

## Faults
No open faults.
