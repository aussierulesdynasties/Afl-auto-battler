# Marvel Stadium exterior (row 202 2b): paused, not ready for gate

## Done
- Full exterior model: roof slabs, end roofs with radial channels, side trusses, N/S arches, seating tiers, bowl wall,
  podium, forecourt and stairs, corner towers, pods, blocks, canopies, tanks. Hand-made textures only; no field, no goal
  nets, no lettering. East side = 180-degree twin of the west (not visible in the aerial).
- Camera-matched overlay on the 2019 oblique aerial lines up (proof/ov7_*.jpg).

## Open faults / gaps
- NEW GATE RULE not yet met: no straight-down render overlaid on a straight-down satellite image (same scale, north).
  The plan shape was measured partly off the oblique aerial (corner towers, pods, forecourt, fill lines via p2uv.py),
  so it must be re-checked (and re-measured from satellite/OSM where off) all the way round: roof edges, bowl edge,
  facade line.
- East side is mirrored, not measured.

## Exact next step
Straight-down check. Satellite plan S/sat/lplan_all_clean.png (Google; x=(200-t)*4, y=(s+200)*4 px, 0.25 m/px, s/t =
local frame from S/mv/frame.py). It leans: a point at height z shows at (s,t)+k*z, k=(-6.94,-2.2)/38 per m. So render
the model ortho straight down with the same shear applied to the geometry (x,y += k*z in s,t), overlay on the plan, and
compare to the OSM outline (S/sat/osm_on_sat.jpg, osmuv.py). Fix parts2.py plan coordinates that are off, re-render the
overlay set, push, report to the ground secretary.

## Proof files (.claude/review/marvel/mv2/proof/)
ov7_on.jpg, ov7_blend.jpg (oblique overlay), j_end_n.jpg, j_end_s.jpg (end roofs photo|model), sh_tt.jpg + r_tt_*.jpg
(turntable), sh_cu.jpg + r_cu_*.jpg (close-ups). Model: mv2/marvel2.glb.

## Scripts
- Repo copies: mv2/parts2.py (geometry), mv2/gen_tex.py (textures -> tex/), mv2/build2.py (Blender 5.2: -- ov|views|glb),
  mv2/views.json, mv2/ovb.py; mv/ (sf.py frame, c5.json camera, p2uv.py, vert.py); sat/ tools and measures.md.
- Scratch (may be cleared): C:/Users/DANTE/AppData/Local/Temp/claude/69aafb6db1ffa220/6d010743-4898-47e7-87ca-da25f77d14c0/scratchpad/
  (mv/, mv2/, sat/, sv/). Run Blender via: GPU_SLOT_OWNER=marvel bash C:/kt/gpu_slot.sh "<blender.exe>" -b --python build2.py -- ov

## Reference photos
- mu.png (2019 oblique aerial, undistorted; camera c5.json) in mv/.
- Google plan satellite sat/lplan_all_clean.png (not in repo, too big; re-fetch with sat/fetchsat.py), Esri eplan_all_clean.png.
- Street-level panoramas in sv/ (inventory.md lists materials per side); 2024 photos of Stadium Square / City Edge.
