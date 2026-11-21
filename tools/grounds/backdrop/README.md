# A ground's surroundings in the match (row 202 2b, background scenes)

The background scenes (`.claude/review/<ground>_bg`) are built in Blender round a stadium model:
3 x 3 km of park, streets, houses, trees and towers, and hills to 30 km. As built they are far
too heavy for a phone (the MCG's 2.3 million triangles, GMHBA's 4.6 million). `reduce.py` cuts a
scene down to the backdrop the match loads:

    python reduce.py -- <proto>/out/<ground>/scene.blend assets/grounds/<slug>/<slug>_backdrop.glb [tex_px near_r mid_keep far_keep]

It writes `<slug>_backdrop_part1.glb` (everything but the trees) and `_part2.glb` (the trees), each
under GitHub's 50 MB. Run it with Blender's Python module (`pip install bpy==5.2.4`, Python 3.13), with
the scene's textures where the .blend points (`//../../tex`, `//../../data/<ground>/prep`); the
scenes and their textures live in the scene pipeline's scratch folder on the director's PC.

What it does:

- drops the stadium model (every object not named `bg_*`) and the scene's ground under it (the convex
  hull of the model, 4 m in): that ground would lie over the arena;
- decimates the big flat meshes (near ground, far terrain and water, roads, kerbs, rails);
- thins the trees with distance (all kept nearer than `near_r`, `mid_keep` of them to 800 m, `far_keep`
  past it; the kept ones are spread a little wider so the canopy keeps its cover);
- joins objects whose materials match into one (one draw each), all the trees into one leaf material;
- cuts the big ones into 8 wedges round the ground (and an inner and outer ring for trees and
  buildings) so the camera draws only what it faces;
- scales the ground bake to `tex_px` (4096) and drops roughness maps.

| Ground | Scene | Backdrop | Trees kept (near_r, mid, far) |
|---|---|---|---|
| MCG | 2.38 M triangles | 0.78 M, 55 pieces | 350 m, 40%, 15% |
| GMHBA Stadium | 4.64 M triangles | 0.96 M, 115 pieces | 250 m, 30%, 10% |

In the game, `GroundModels.backdrop()` loads the parts with the model (so it fits where the model
fits), turns their shadows off and paints them as Blender did (`oval3d_backdrop.gdshader` for the
walls and roofs). `Oval3D._backdrop_view()` opens the camera to 7 km and hazes everything past 600 m
into the horizon's colour. Check a ground from the broadcast cameras and from outside with
`tools/visual/capture_backdrop.gd`.
