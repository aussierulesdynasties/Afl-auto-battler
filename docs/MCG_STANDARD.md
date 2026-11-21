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

## Surroundings

The ground round the stadium comes from OpenStreetMap, never from aerial imagery. It is built by
`tools/grounds/mcg/surrounds.py` and loaded through `GroundModels.SURROUNDS`. Three parts make it up:

- **A painted map:** 2,048 m a side at 1 m a pixel, VRAM-compressed. It shows the grass, paths, car
  parks, roads, rail ballast, flat roofs and the shade under each tree. Its colours are painted warm
  and light, because the match light's blue sky fill cools them.
- **Every mapped tree:** a lumpy canopy and a trunk, drawn as batches in 250 m blocks, with no
  shadows.
- **Buildings:** the map's footprints extruded to their tagged height, as one mesh.

To place a map on the model, line up the AFL pitch's centre in OpenStreetMap with the model's 0, 0.
For the MCG, that centre is 25.3 m east and 23.5 m south of lat -37.81977, lon 144.98316.

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
