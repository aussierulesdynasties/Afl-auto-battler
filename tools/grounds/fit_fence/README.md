# Laying a ground's model on the match ground (GroundModels.FIT)

`scripts/ui/match/GroundModels.gd` lays each model in `assets/grounds/<slug>/` so its boundary fence
meets the match's fence. The numbers in its `FIT` table come from these tools:

1. `dump_faces.gd`: every triangle of a model (all its `_partN` pieces) in world space, float32.
   Godot's GLTF reader works outside a project, so run it from an empty one:
   `godot --headless --path <empty project> --script dump_faces.gd -- out.bin a.glb [b.glb ...]`
2. `fit_fence.py` (numpy): `analyse2()` finds the arena floor and the fence. From the middle it looks
   out along 720 level lines 0.5 m above the floor, takes where each first meets the model, and fits
   an ellipse (outliers dropped): centre, floor, long-axis angle and half length/width. The floor is
   the lowest 1% of geometry inside the fence ring, refined until it settles.
3. `fence_sheet.py`: a top-down contact sheet of each model's slices with the fitted fence in red.
   Check it by eye before trusting a new row.

Two model fixes the game needs, run with @gltf-transform (npm i @gltf-transform/cli@4.1.1):

- `split.mjs in.glb out_prefix`: a model over 50 MB as two pieces (`_part1`, `_part2`), primitives
  balanced by vertex count. People First was dequantized first (`gltf-transform dequantize`): Godot
  cannot read KHR_mesh_quantization.
- `uninstance.mjs in.glb out.glb dir colour...`: seats drawn with EXT_mesh_gpu_instancing (Godot
  ignores it) become `seat_tmpl_<colour>.bin` + `seats_<colour>.bin`, the MCG's seat format. The SCG.
