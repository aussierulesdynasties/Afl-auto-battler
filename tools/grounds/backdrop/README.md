# A ground's surroundings in the match (row 202 2b, background scenes)

The background scenes (`.claude/review/<ground>_bg`) are built in Blender round a stadium model:
3 x 3 km of park, streets, houses, trees and towers, and hills to 30 km. As built they are far
too heavy for a phone (the MCG's 2.3 million triangles, GMHBA's 4.6 million). `reduce.py` cuts a
scene down to the backdrop the match loads:

    python reduce.py -- <proto>/out/<ground>/scene.blend assets/grounds/<slug>/<slug>_backdrop.glb [tex_px near_r mid_keep far_keep inner skyline.json]

It writes `<slug>_backdrop_part1.glb` (everything but the trees) and `_part2.glb` (the trees), each
under GitHub's 50 MB. Publish them with `tools/ground_assets.sh publish` (docs/GROUND_ASSETS.md); they are not
committed here. Run it with Blender's Python module (`pip install bpy==5.2.4`, Python 3.13), with
the scene's textures where the .blend points (`//../../tex`, `//../../data/<ground>/prep`); the
scenes and their textures live in the scene pipeline's scratch folder on the director's PC.

What it does:

- drops the stadium model (every object not named `bg_*`) and the scene's ground under it (the convex
  hull of the model, 4 m in): that ground would lie over the arena;
- with `inner` (the MCG: 1024), drops everything nearer than that radius: the game draws its own
  ground, trees and buildings there (`GroundModels.SURROUNDS`, its `"outer"` set to the same radius).
  The scene's ground keeps each face that reaches past the circle, its inner corners moved onto the
  circle at the game ground's height, so the seam has no gap; the coarse far terrain inside sinks 5 m;
- with `skyline.json`, adds the city's tall buildings from OpenStreetMap (`skyline.py`): footprints of
  30 m and over extruded to their tagged heights, stood on the scene's terrain, tinted like the
  scene's own towers and joined into them. A footprint holding one of the scene's roofs is skipped.
  `osm_skyline.py fetch` gets the tiles from the OpenStreetMap API and `osm_skyline.py parse` writes
  the json (map data © OpenStreetMap contributors, ODbL);
- decimates the big flat meshes (near ground, far terrain and water, roads, kerbs, rails);
- thins the trees with distance (all kept nearer than `near_r`, `mid_keep` of them to 800 m, `far_keep`
  past it; the kept ones are spread a little wider so the canopy keeps its cover);
- joins objects whose materials match into one (one draw each), all the trees into one leaf material;
- cuts the big ones into 8 wedges round the ground (and an inner and outer ring for trees and
  buildings) so the camera draws only what it faces;
- scales the ground bake to `tex_px` (4096) and drops roughness maps.

| Ground | Scene | Backdrop | Trees kept (near_r, mid, far) |
|---|---|---|---|
| MCG (from 1,024 m, 480 OSM towers) | 2.38 M triangles | 0.33 M, 30 pieces | 350 m, 40%, 15% |
| GMHBA Stadium | 4.64 M triangles | 0.96 M, 115 pieces | 250 m, 30%, 10% |
| 10 more from the PC (Optus, Marvel, Adelaide, People First, Cazaly's, Riverway, Traeger, Mars, Accor) | | budget 800,000 triangles, 2 looks per kind | |

A first pass at the other grounds was built in the cloud from OpenStreetMap with `scene/run1.sh` (see `scene/README.md`).
It read as generic suburbs, not the real places, so none of it is in the game: each ground lands only once it is
built to match Google Earth. Two settings came with that work: `BG_YAW` turns a scene built on a turned model back into the model's frame, and `BG_HULL_SKIP` leaves
the model's own flat ground (WACA, Bruce, North Hobart, the kit grounds' concourse disc) out of the hull that cuts
the scene's ground, because the game hides that ground where a backdrop is drawn (`GroundModels.BACKDROP_HIDES`).
Historic grounds (Waverley Park, Football Park, Subiaco, Moorabbin, Windy Hill) stand in today's suburbs.

In the game, `GroundModels.backdrop()` loads the parts with the model (so it fits where the model
fits), turns their shadows off and paints them as Blender did (`oval3d_backdrop.gdshader` for the
walls and roofs), none receiving shadows (past the shadow map's reach that reads blue-grey).
`Oval3D._backdrop_view()` opens the camera to 7 km and hazes everything past 600 m
into the horizon's colour. Check a ground from the broadcast cameras and from outside with
`tools/visual/capture_backdrop.gd`.

## Past the backdrop: the horizon (`horizon/`)

A backdrop ends at its ±1.5 km square. `horizon/horizon.py` builds `<slug>_horizon.glb`: the real land and water out
to 64 km (terrain.bin, then Mapterhorn; the earth's curve taken off), coloured from Sentinel-2 (`horizon/s2grid.py`,
Digital Earth Australia, CC BY 4.0) and matched to the backdrop's ground bake at the seam, and the city between the
square and 4 km from Overture's buildings (heights mapped, or read from the EU's GHS-BUILT-H map through this ground's
own mapped neighbours). When the file is there, `GroundModels.backdrop()` loads it in place of the scene's far terrain
and the camera and haze open to 60 km (`HORIZON_RANGE`). Run `reland.py` on the backdrop first, so the seam meets.
Marvel (2026-11-27): 326,000 triangles in 32 pieces, two 1024 px textures; on the match camera +4% triangles,
+3% draw calls, +30 MB video memory, drawing time +3 to 4% (cloud measure, docs/PHONE_3D_BUDGET.md's method).
