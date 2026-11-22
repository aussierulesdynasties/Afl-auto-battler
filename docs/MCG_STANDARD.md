# The MCG standard

The MCG is the flagship ground (2026-11-21). The other grounds are paused and will be rebuilt to this
standard once the MCG passes it. This file records how the MCG is checked and built, so the next ground
starts from the same rules. It covers looks only: nothing here reads back into play.

## The gate: Google Earth from the same camera

Nothing goes to the director until it has passed a side-by-side against real imagery from the same
camera. Use Google Earth 3D for outside and overhead views, and Street View on the ground for inside.

- **Google Earth in a headless browser.** Run Playwright Chromium with
  `--use-gl=angle --use-angle=swiftshader --enable-unsafe-swiftshader --ignore-gpu-blocklist` and a
  1280x1000 viewport, then crop rows 140 to 860. Open a fresh page for each view, or Google Earth
  sometimes shows the globe. The URL is `earth.google.com/web/@lat,lon,alt a,range d,35y,heading h,tilt t,0r`.
- **Our camera for the same view.** `tools/visual/preinspect_look.gd` takes `name:px,py,pz,tx,ty,tz,fov`.
  - Model axes: x is east, -z is north.
  - The field centre is lat -37.81977, lon 144.98316. Google Earth's field level is about 8 m.
  - The camera sits at `target - range * dir`, with
    `dir = (sin t sin h east, sin t cos h north, -cos t up)`.
  - Use a vertical fov of 23.5 to match a 16:9 crop.
  - Close views straight into the bowl never line up exactly, so judge those by eye.
- **The views.** Check every one before a stage is called done:
  - the director's four reference angles (from the south, east, north-east and north-west);
  - straight down;
  - the eight compass points outside;
  - into the bowl from each end;
  - Street View from the centre square.

## Seats

A seat goes only on a sloped row with a floor under it. It must be either in the open or under a roof
or tier with at least 2.6 m of headroom (from Adelaide, #1974). Check every seat file by casting a ray
up and down through the model's own triangles:

- **Floor:** remove any seat more than 0.8 m above the floor below it.
- **Headroom:** remove any seat with less than 2.6 m above it.

Seat colours follow the real stands tier by tier, sampled from Street View and Google Earth:

| Tier | Colour |
| --- | --- |
| Lower and middle | White and light grey |
| Front rows of the middle tier | A blue band |
| Top tier | Teal-blue |
| Members' (north-west) top tier | Grey-green |
| Front of the lower tier, west round to north | Mint green |

Each colour is one `seats_seat_mcg_<colour>.bin` file with its entry in `GroundModels.SEAT_COLOURS`.

The match light puts the Great Southern Stand's seats in shade under a blue sky. To compensate, the
seat colours are a touch warmer than the plastic, so they read as white rather than blue.

## Walls

Every facade texture is one bay. Draw it at **32 px per metre, 768 px tall for a 24 m bay**, with the
width set by that material's metres per u (measured from the model's UVs). The drawing script is
`tools/grounds/mcg/facade_detail.py`, which works from the originals kept in `facade_src/`:

- **Solid walls:** Google Earth's mid grey (about 0.72 of the original), with precast joints every
  3 m x 1.5 m and rain streaks.
- **Glass:** mullions every 1.5 m and transoms every 3.6 m, a sky reflection at the top of each run,
  and a slab shadow under each floor.

## Materials

A ground's named materials can be corrected without rebuilding the model, through
`GroundModels.MATERIAL_FIX` (each fixed material gets its own copy).

- **MCG roof sheeting:** matte (metallic 0, roughness 0.9) and tinted to Google Earth's colours.
  Before this fix it mirrored the sky and read white-blue from above.
- **Roof undersides:** grey with a faint green tint (director), through the stand shader.

A big model mesh is cut into slices after loading (`slice_big_meshes`). Each slice keeps the
instance's active material, so a material fix reaches the slices too. Before this, the MCG bowl's
low roofs kept their glossy material and read white from above.

## Surroundings

The ground round the stadium comes from OpenStreetMap, never from aerial imagery. It is built by
`tools/grounds/mcg/surrounds.py` and loaded through `GroundModels.SURROUNDS`. Three parts make it up:

- **A painted map:** 2,048 m a side at 1 m a pixel, VRAM-compressed. It shows the grass, paths, car
  parks, roads, rail ballast, flat roofs and the shade under each tree. Its colours are Google
  Earth's. The map, trees and buildings take no sun shadow: past the shadow map's 160 m, the Mobile
  renderer drew them as if in shade (blue-grey), and the trees' shade is painted in instead.
- **Every mapped tree, plus fill:** OpenStreetMap maps only some of the parks' trees, so each park
  is filled to Google Earth's density (one tree per 190 m² of open grass). Each is a lumpy canopy and a trunk, drawn as batches in 250 m blocks, with no
  shadows.
- **Buildings:** the map's footprints extruded to their tagged height, as one mesh.

To place a map on the model, line up the AFL pitch's centre in OpenStreetMap with the model's 0, 0.
For the MCG, that centre is 25.3 m east and 23.5 m south of lat -37.81977, lon 144.98316.

## Model parts rebuilt without the model's source

The model's source (`build.py`) is on the director's PC. A part that needs rebuilding can still be
replaced from the cloud: a tool reads the part from the `.glb`, builds it again, and writes a mesh
(per vertex position, normal and colour). `GroundModels.PARTS` hides the model's own node and draws
the new mesh instead. The MCG has two:

- **Roof trusses** (`tools/grounds/mcg/trusses.py`): square lattices, 2 m wide for the masts and
  1.6 m for the booms and back stays, in pale steel, with a blue light box at each boom's tip.
- **Slab edges** (`tools/grounds/mcg/ledges.py`): a ledge 0.45 m deep at every floor, 3.6 m apart,
  on every outside wall.

## Stages

1. References and plan.
2. Roof and stand shapes. These already matched within a few metres; the visible gap was the
   materials.
3. Facades.
4. Seating.
5. Textures and materials.
6. Surrounds (Yarra Park, the rail yards) and screens.

## Optus Stadium, the second ground (2026-11-21)

Optus went through the same gate. What it added to the method:

- **Cameras in the model's own frame.** `PREINSPECT_MODEL_FRAME=1` makes `preinspect_look.gd` read
  `x east, y north, z up` positions, so a Google Earth view's camera goes in unchanged
  (`PREINSPECT_SIZE=1280x720`). Optus's model 0, 0 is lat -31.9510758, lon 115.8893142 (its drum lines
  up with OpenStreetMap way 695799456); the field's centre is at -30.38, -8.78.
- **Rendering in the cloud.** The mobile renderer runs on Mesa's software Vulkan (`mesa-vulkan-drivers`,
  `VK_ICD_FILENAMES=.../lvp_icd.json`) under `xvfb-run`, about a minute a ground plus seconds a view.
- **Read the facade close.** Twelve views every 30 degrees, 260 m out at tilt 80, found what the four
  wide views hid: #1867 had the bronze low from the south-east to the west, where the real ribbon is tall
  in the north and south and dips over the east lobby and the west. Its profile is
  `tools/grounds/optus/facade.json`; `tools/grounds/optus/build.py` rebuilds the model from it.
- **Signature material first.** The bronze fins (`tools/grounds/optus/bronze.py`) are drawn from the
  director's photo: 0.31 m fins in runs of 1 to 7 m, bronze to sand with the odd copper-red, thin
  pale-blue slivers, a soft drift of tone, metal sheen through `MATERIAL_FIX`.
- **The match light cools the map.** A painted map under the match light lost most of its red. Optus's
  map takes a `tint` (2.0, 1.4, 0.95) and colours worked back from the measured response, so lawns, river
  and paving render as Google Earth shows them.
- **Bridges are models.** `SURROUNDS[...]["models"]` loads extra glbs into the ground (Optus:
  `bridges.glb`, Matagarup's two 72 m arches and the river bridges on piers).

- **Second facade pass (close views).** Zoom Google Earth's facade views to a third of the frame before
  judging a material: at full frame the Optus bronze read as brown noise, close up it is a dark base with
  thin bright streaks, and the "white Y columns" were slim posts in a dark strip under the roof. The glass
  band, street glazing and the north's glazed storey are drawn by `bronze.py` (`glass`, `entrance`, `storey`).

Open at Optus: seat colours from Street View (stage 4), on top of the seat fix (#1991).

## Marvel Stadium, the third ground (2026-11-21)

Marvel went through the same gate against Google Earth (obliques from eight sides, twelve facade views,
straight down, into the bowl). What it added to the method:

- **Check the bearing first.** The first model had been turned so its long axis ran north-south; the
  real ground runs at bearing 160 (OpenStreetMap pitch 158). Side by side with Google Earth every facade
  read about 20 degrees off. The model is now exported in its measured frame (x east, y north) and
  `GroundModels.FIT` turns it onto the field. Compare a model's long axis with OpenStreetMap's pitch
  before anything else.
- **Seats drawn once, many times.** The baked 3D seats (two meshes of a million triangles) became
  `seat_tmpl.bin` plus one `seats_seat_marvel_<level>.bin` per level (`tools/grounds/marvel/seats.py`),
  then `seat_check.gd --write` (55,890 of 57,535 kept: 954 inside the fence, 669 without headroom).
  The crowd now sits on them.
- **A roof that opens.** `GroundModels.ROOFS` names a model's shut and open roof nodes; a match shows
  Marvel shut, as the match scenes draw it (data/grounds.json). Shut, nothing of the stadium throws a
  sun shadow: the roof's lights light the field evenly. The fly-through's B key opens it, and
  `PREINSPECT_ROOF=open` renders it open for Google Earth (which shows it open).
- **Colours by mean, detail kept.** `tools/grounds/marvel/retint.py` moves each hand-made texture's mean
  to Google Earth's (pale grey-green trusses, light end roofs, blue-grey cladding, grey paving) and keeps
  each pixel's difference from the mean. Undersides face the match light's dim blue-violet, so they are
  painted warm and green to render the grey with a faint green tint.
- **Broadcast checks clip like the broadcast.** The main and goal cameras sit inside the stand and draw
  nothing nearer than 20 m (`Oval3DBroadcast.NEAR`); `PREINSPECT_NEAR=20` renders what they see.
- **Surroundings** from OpenStreetMap in nine tiles (the API's node limit in a city):
  `tools/grounds/marvel/surrounds.py` (Victoria Harbour, the Southern Cross yards, the streets, the towers
  to their mapped heights) and `bridges.py` (the Bolte Bridge's 140 m towers and deck, 1.35 km west).

Close-up pass (2026-11-21, same day), what a harsh look found and fixed:

- The land round the ground was orange: the map took Optus's warm `tint` (2.0, 1.4, 0.95), but
  Marvel's map is already painted grey. Measured against Google Earth's top view (rail yards, water)
  it now takes (0.86, 0.84, 0.82). Check a copied setting against your own map's colours.
- The bowl's top band (over the braces, under the MARVEL STADIUM letters) shared the undersides'
  texture, painted warm for the dim light under a roof, and read khaki outside. It is its own dark
  blue now (`upperwall`). A texture tuned for one light must not be shared with a face in another.
- The east office boxes are pale with a spandrel band and fins over ribbon glazing, on an open
  colonnade, as Google Earth's close views show; the corner blocks a muted blue. (First painted on as
  textures; modelled the next day, see below.)
- Inside: the aisle stairs read as white ladders (the treads were the outside's white concrete; now
  a mid grey `tread`), and the middle and top tiers' fronts carry dark ribbon screens.
- The surrounding towers: `building_style: "towers"` draws them as blue-grey glass curtain walls
  (a mullion every 1.5 m, a slab every floor) or concrete with rows of windows, in one shader that
  fades the pattern with distance (GroundModels.TOWER_SHADER); same mesh, same draw call.

No-shortcuts pass (2026-11-22, the person: "i never want a shortcut, i never want a placeholder"):

- Painted-on geometry replaced: the east office boxes have modelled spandrel bands, slim fins every
  0.75 m, a recessed glass lobby and round columns (parts2 `office_box`); the blue service blocks have
  real recessed louvre openings between piers (`vent_block`). The painted `office` and `undercroft`
  textures are gone. Rule: if it has depth in Google Earth, it has depth in the model.
- The glass and the blues were near-black in shade: lighter and greyer now (retint.py).
- The surrounding towers' colours went into the shader as sRGB but were read as linear, so every wall
  and roof drew far paler than its palette (roofs near white from above). TOWER_SHADER converts them.
- Landmarks (tools/grounds/marvel/landmarks.py, landmarks.glb), each modelled by eye from Google
  Earth's 3D, footprints from OpenStreetMap: NAB 700 Bourke (folded facets, white triangle shades,
  red strips, V-strut ground storey, folded glass roof), the former Seven Network HQ (ribbon windows
  set back, tiered drum, lattice mast), the round glass office, Victoria Point, 720 Bourke (rippling
  balcony slabs), the two sawtooth towers to the north, the ferry shed, the pier plaza's paving,
  the jetties, rock armour along Harbour Esplanade, the old pile rows, and the rail yard's wiring
  gantries. Their OpenStreetMap footprints are left out of buildings.bin (surrounds.LANDMARK_WAYS).
- Harbour Esplanade's street trees are tall and slim (a tree listed over four times as tall as its
  crown is wide draws a narrow crown); the yard's private walkways no longer paint as white paths.
- Imagery (satellite crops, aerial photos, overlays) was taken out of .claude/review/marvel; it is
  for looking at only. Copies are in the project files (marvel-rebuild/review-imagery).

Still open at Marvel: the Street View panoramas inside the bowl could not be reached headless; the
inside is checked against Google Earth's 3D from the centre. Further out than ~250 m the buildings
are still OpenStreetMap extrusions with the tower shader. Shaded faces read bluer than Google
Earth's under the inspector's sky light (all grounds).
