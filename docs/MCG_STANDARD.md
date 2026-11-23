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

## Where shipped data may come from (every ground)

Fidelity comes first: a ground is copied as closely as it can be from Google Earth, Street View and
real photos. The director accepts the risk on grey-area sources (2026-11-22: "if Channel 7 comes
knocking I'll remove the anims, until then let me eat cake").

- **Measuring and copying from Google Earth is fine.** Heights, positions, tree counts, colours and
  shapes may be read off it, by eye or by script, whatever makes the ground most accurate.
- **Prefer open data where it is as good:** OpenStreetMap (ODbL), Microsoft building footprints
  (ODbL), the Meta and WRI canopy map (CC BY 4.0), government LiDAR and open data (CC BY). Never take
  a less accurate result to use it, and never redo finished work for this rule.
- **The one hard line: no raw imagery in the repo or the game.** Esri tiles, Google Earth or Street
  View captures, satellite crops and downloaded press photos are not committed to the repo (it is
  public) and not baked into a shipped texture (for example a satellite photo as a ground map). Keep
  them, and QA sheets made from them, in the project's private files.
- Credits for every open source used go in `docs/CREDITS_3D.md` and the game's credits screen
  before 1.0.

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

- **No painted-on geometry (director, 2026-11-22).** Arches, doorways, recesses, struts, window reveals,
  frames, sills, pilasters and mouldings are always modelled with real depth: an opening is cut through the
  wall with reveals and something behind it, and a frame or trim stands proud with its own top, underside
  and ends. A dark shape or a coloured strip laid a few centimetres off a wall is never an arch or a window.
  A texture may only carry detail too small to see in depth from the stands or the broadcast camera (brick
  coursing, panel joints, mullions on flat curtain glass). Adelaide's arcade, its scoreboard door, windows and
  louvres were rebuilt to this rule on 2026-11-22.

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
- **Check the map under the current light.** A painted map once needed a `tint` to survive the match
  light; after the stand lighting changed on main (2026-11-22) the same tint washed it yellow, so Optus's
  `tint` and `building_tint` are white now. Re-check a map's colours whenever the lighting changes.
- **Bridges are models.** `SURROUNDS[...]["models"]` loads extra glbs into the ground (Optus:
  `bridges.glb`, Matagarup's two 72 m arches and the river bridges on piers).

- **Second facade pass (close views).** Zoom Google Earth's facade views to a third of the frame before
  judging a material: at full frame the Optus bronze read as brown noise, close up it is a dark base with
  thin bright streaks, and the "white Y columns" were slim posts in a dark strip under the roof. The glass
  band, street glazing and the north's glazed storey are drawn by `bronze.py` (`glass`, `entrance`, `storey`).

- **Match colour under Google Earth's own sun (2026-11-23).** `PREINSPECT_SUN=az,el` puts the capture's sun
  where Google Earth's photos had it (Optus: 67.6, 45.5, from 42 shadow pairs, `survey/sun.json`). Colour is then
  compared patch for patch on a PC GPU render, never the cloud's software renderer. At cdff0fe: roof membrane
  (228,232,244) vs Google Earth (229,237,244), bronze brightness 1.00, sunlit seats (142,157,166) vs (130,151,158).
- **Shading is the renderer's job.** A grey strip painted along the roof's inner edge read as a 3-4 m band at
  0.8x Google Earth's brightness and threw the inner-edge trace 4 m off; removed, the edge measures median
  +0.05 m, rms 1.05 m against Google Earth over 358 bearings (Google Earth's own trace scatters 0.85 m).

Open at Optus: shadows read too blue on every ground (truss shadow on the roof blue/red 1.37 vs Google Earth's
1.10); that is the match sky light, shared by all grounds.

## Adelaide Oval (third ground to the standard, 2026-11-21)

- **The compare tool is in the repo.** `tools/grounds/ge_compare.py` plans each view's Google Earth URL and
  our matching camera through the ground's FIT, `tools/grounds/ge_shoot.js` takes the Google Earth shots,
  and `ge_compare.py sheet` lays the pairs side by side. Views live with the ground
  (`tools/grounds/adelaide/qa/views.json`); a view with `cam` is a fixed camera for a photosphere or Street
  View picture supplied by hand. Grounds now play at their own size (#1949), so the camera needs no stretch.
- **Google Earth's camera, measured (2026-11-22).** Pairs made before this were framed wrongly and are good for
  looks and colours only, never sizes. Measured at Adelaide and the MCG by putting the mouse on points whose
  place on screen was worked out first (the status bar gives the lat/lon under it; all fell within a metre):
  the URL's `35y` is the vertical field of view of the whole browser window, centred on it, so our picture of
  the 720-row crop needs 25.6 degrees, not 23.5. The `a` altitude is the look-at point's height above sea
  level, and the turf's height must be Google Earth's own (Adelaide 26 m, not the 40 m used; MCG 8 m):
  `ge_shoot.js <work> --level`, then `ge_compare.py level`. Google Earth also lifts a camera it thinks too
  low, by 15-30 m at Adelaide below about 100 m, keeping its spot and tilt; `ge_shoot.js` saves the status
  bar beside each shot and a second `ge_compare.py plan` puts ours where Google Earth's really was.
- **Street View at Adelaide is a drone photosphere.** Asking Google Maps for a panorama at the field centre
  returns a 360 drone sphere taken above the Riverbank Stand (April 2021); `qa/sv_views.json` matches it
  looking north, east, south and west.
- **No tint where the map is painted for the light.** Optus's `tint` made Adelaide's parklands yellow;
  Adelaide's map is painted in Google Earth's colours with no tint.
- **The model's own ground stops under its stands.** Adelaide's 6 km lawn is out of the export; its floor is
  a 107 m disc and the map starts at 105 m, outside the turf (a map under the turf flickered through it).
- **Park trees.** OpenStreetMap maps most of the parklands' street trees; the other parks are filled to a
  tree per 260 m² of open grass. Park 26, which holds the ground and its open ovals, is left as mapped.
