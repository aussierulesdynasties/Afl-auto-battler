# Barossa Park (Lyndoch, SA): the 3D ground

Rebuilt to the MCG standard (docs/MCG_STANDARD.md) from the 2026 satellite mosaic, Google Earth and photographs. The
match ground plays at FIT["barossa"] in scripts/ui/match/GroundModels.gd (the boundary fence ellipse in plan.py).

## What is modelled

- **Clubrooms** (DASH Architects, 2024): sandstone ground floor of piers and recessed bays (doors, roller doors,
  glass), dark grey upper floor with full-height glazing and a deck with a slatted balustrade, maroon columns and
  knee braces under the verandah, the white folded roof of four gables with glazed east gables and box gutters, the
  dark grey stair tower at the north end with its stair, and the west annex.
- **Terraces** south of the clubrooms (seven concrete steps with handrails), the **viewing pavilion** to the
  south-west (white flat roof, glass box), the **picket fence** with its posts and rails, **four light towers**
  (40 m galvanised poles with LED headframes), the **Gather Round 2026 temporary stands** (two south, one north-east,
  open blue-seat grandstands on scaffolding; 1,472 seats in seats_seat_barossa_blue.bin), the netball and tennis
  courts with their fences and court pavilion, the water tanks and shed, the ring road and its south-west retaining
  wall, and the disused Gawler–Angaston railway with its rails still down.
- **The land out to 1 km** (land.py): the true terrain from Terrarium heights, the ground painted by class from
  OpenStreetMap and the satellite (vineyards, paddocks, roads, the township), every Lyndoch building from its
  OpenStreetMap footprint with a hip or gable roof in its own roof colour, each vineyard's rows at their own bearing,
  spacing and cover, and 19,430 trees placed and sized from the satellite's crowns.
- **The second oval** north-west of the ground (oval2.py, traced on the 2026 mosaic; it is not in OpenStreetMap):
  its turf and mowing, the path round it, goal and behind posts, four training light poles, the interchange
  shelters on its east wing and the cricket nets past its north end. The OpenStreetMap vineyard drawn there before
  the oval was built is left out.
- **The far country to 16 km** (far.py): the Barossa Range and the Mount Crawford hills on the skyline, the valley
  floor, the reservoirs and pine blocks, on the true heights with the earth's curve; its texture is a palette by
  land cover measured on the satellite at 10 m, with distance haze. The match camera sees to 16 km here
  (SURROUNDS `far`).
- **Gum trees** (trees.py): four eucalypts (forked trunk, leaning limbs, open clumps of leaves), drawn whole within
  450 m of the camera and as a coarse crown beyond.

## Rebuilding

    python3 satmosaic.py 18 1600 0.5 work/z18.png    # measuring only (see Licences)
    python3 satmosaic.py 15 16000 10 work/z15.png
    python3 build.py      # assets/grounds/barossa/barossa.glb, seats, seat template
    python3 land.py       # assets/grounds/barossa/barossa_land.glb, trees.bin
    python3 trees.py      # assets/grounds/barossa/barossa_gums.glb
    python3 far.py        # assets/grounds/barossa/barossa_far.glb
    godot --headless --path . --import
    godot --headless --path . --script tools/grounds/seat_check.gd -- --write barossa

OpenStreetMap is read from the API into work/osm.osm (`/api/0.6/map?bbox=...` round the fence centre) and heights
into work/dem by dem.py. tools/visual/ground_look.gd renders stills from cameras in the model's metres.

## References

- Google Earth (satellite and 3D) round lat -34.5984014, lon 138.8858792. The 3D mesh at Lyndoch is coarse, so
  heights come from the photos.
- austadiums.com: barossa-park.jpg (aerial from the south-east), barossa-park-gather-round25.jpg,
  barossa-park-26.jpg (a 2026 match, the temporary stands), lyndoch-recreation-park.jpg, the upgrade photos.
- The clubrooms from the north-east (BarossaPark_09849.jpg) and the 2025 Gather Round view with the ranges
  (Barossa-Park-2025-Gather-Round.png); masterplan.com.au and wga.com.au project photos.

## Licences

- OpenStreetMap data © OpenStreetMap contributors, ODbL (building footprints, roads, the railway, land use).
- Terrarium elevation tiles (AWS Open Data, Mapzen terrain): open data with attribution.
- Satellite imagery and photographs are used only to measure and compare. No pixel of them is in any texture: every
  texture is painted in code (paint.py, land.py), and none of these images is committed.
