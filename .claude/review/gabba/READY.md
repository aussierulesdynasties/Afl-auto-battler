# Gabba exterior model: ready for gate (row 202 step 2b)

Model: tools/grounds/gabba/gabba.glb (82,677 tris), built by tools/grounds/gabba/build.py + sw.py from model_in6.json.

## Proofs (this folder)
- Camera-matched overlay on photo g49: v6_ov.png (model edges on the photo).
- Top-down on the Esri 2011 satellite tile: topov_s.png (straight), topov_l.png / topov_l_blend.png (lean-matched), edge_l.png (outline).
- Turntable: tt.gif (60 frames), tt_sheet.png.
- Close-ups and joins: cu_*.png (gate 7, gate block, facade, south, edge, west, north, plant, screen, white building, navy side, roof deck, mast, roof top, roof underside, seats west/east).
- Texture beside photo crop: board_textures.png. Signs beside photo crop: board_signs.png. Stddev list: stddev.txt.

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
- Gate 7 "7" on the Vulture St face of the navy block, hand-drawn from the g49 crop (board_signs.png). It replaces the
  blank panel from the 2026-11-18 "no lettering" ruling.
- Gate block round crest window, hand-drawn (board_signs.png).
- The small sign beside the gate block's dark opening is unreadable in every reference, so it stays a blank panel.
- No sponsor ads, banners or posters.

## Textures
Hand-painted (mktex_hand.py, mktex_sw.py): joints, rain run-off streaks starting at ledges, mottling, grime in the
membrane valleys beside each boom, seat-by-seat seats with aisles. Every big surface is at grey stddev 10 or more
(stddev.txt). Below 10: grass (not used, no field), t411 (not used), screen (the ruled blank face).

## Known differences, measured
- g49 overlay: on the photo-left (east) side the roof edge sits ~40 px inside the photo. The top-down shows the east
  outline on the satellite's facade line, so this is the g49 camera fit (it has a ~25 px error in that corner already).
