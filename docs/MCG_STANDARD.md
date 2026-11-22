# The MCG standard

The MCG is the flagship ground (2026-11-21). The other grounds are paused and will be rebuilt to this
standard once the MCG passes it. This file records how the MCG is checked and built, so the next ground
starts from the same rules. It covers looks only: nothing here reads back into play.

## The gate: Google Earth from the same camera

Nothing goes to the director until it has passed a side-by-side against real imagery from the same
camera. Use Google Earth 3D for outside and overhead views, and Street View on the ground for inside.

- **Use the shared tool.** Use `tools/grounds/ge/` (README there) for every ground: `ge_compare.py plan`,
  `ge_shoot.js`, then `register` and `outline` for numbers. Its `grounds.json` holds each model's origin and
  Google Earth's turf height.
  - The URL's `35y` is the vertical fov of the whole 1000 px window. The 720-row crop is **25.58 deg**, not 23.5.
  - Read the turf height and every camera height from Google Earth's status bar. GE lifts low cameras 15-30 m.
  - Open a fresh page per shot.
  - Line the model up with `register` before measuring anything. Pass is 1 m and 0.5 deg.
  - Judge by numbers, never by eye: `outline` for plan, published dimensions for heights, and `ge_solve.py`
    for an oblique's true camera.
- **Our camera for the same view.** `tools/visual/preinspect_look.gd` takes `name:px,py,pz,tx,ty,tz,fov`.
  - Model axes: x is east, -z is north.
  - The MCG field centre is lat -37.81977, lon 144.98316, and Google Earth's turf is 8 m.
  - The camera sits at `target - range * dir`, with
    `dir = (sin t sin h east, sin t cos h north, -cos t up)`.
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
