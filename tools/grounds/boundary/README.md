# Each ground's real boundary line

The match plays on a ground's traced boundary line, not an ellipse, once it has been traced.

- `traced/<slug>.json`: the trace, in the model's glb x/z metres: `line` (middle of the painted line, all round),
  `goals` (middle of each goal line), `centre`, `fence` (optional), `source`, `error_m`. Only a painted line actually
  seen on imagery goes here; a line inferred from a published size or the fence does not.
- `pending/`: traces waiting for their model to merge (Norwood's is in the frame of the model in PR #2042). Move to
  `traced/` and rerun the fit when it lands.
- `python3 tools/grounds/boundary/fit_boundary.py` fits each trace (polar Fourier radius about the goals' midpoint,
  x through the goals) and writes `data/ground_boundaries.json` with the fit error per ground.
- Check in a match: `godot --path . --rendering-method mobile --script tools/grounds/boundary/topdown.gd -- OUT "<ground>"`
  then `python3 tools/grounds/boundary/check_topdown.py OUT <slug>` measures the painted line against the trace.
- Game side: `GroundModels.play_at` / `play_on`, `MatchMotion.use_shape` and its edge helpers; tests
  `_test_traced_boundaries` and `_test_traced_ground_playback` in tests/test_match_visual.gd.
