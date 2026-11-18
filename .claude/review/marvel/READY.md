# Marvel Stadium exterior (row 202 2b): ready for gate

Model: mv2/marvel2.glb (199 parts, 23,570 faces, origin at the pitch centre, north +Y). Hand-made textures only (mv2/tex,
gen_tex.py). No field, posts, goal nets, lettering, boards, temporary stands or background buildings.

## Proofs (mv2/proof/)
- Camera-matched overlay on the 2019 oblique aerial: ov8_on.jpg, ov8_blend.jpg; end roofs photo|model: j_end_n.jpg, j_end_s.jpg.
- Top-down overlay, model straight down on the straight-down satellite, same scale, north and lean: t_on.jpg (cyan =
  model silhouette, magenta = model edges), t_blend.jpg. Close zooms of the rebuilt east: zE1e, zE2e, zNEe, zSEe.
- Crop board per part (satellite | model | outlines): board_parts_1.jpg (N, S, W, E), board_parts_2.jpg (NW, NE, SW, SE).
- Turntable: r_tt_w/n/e/s.jpg, sheet sh_tt.jpg. Orbit video: marvel_orbit.mp4 (72 frames, 12 fps).
- Facade close-up: r_cu_facade.jpg. Join close-ups: r_cu_corner_nw/sw/ne/se, r_cu_roofedge_nw/s, r_cu_tiers,
  r_cu_east, r_cu_join_east_c (sheets sh_cu.jpg, sh_cu_east.jpg).

## East side
Rebuilt from the satellite (no longer a mirror of the west): NE block (z33, plant to 37), box A (z27.4), block B (z24,
two widths), C deck (z7) and walkway (z10), block D (z24, east edge v-131.3 to -124.6), box E (z27.4). Heights from
shadow lengths (0.5 m shadow per m), checked against oblique photo 31603700. Satellite roofs lean
(u-0.1738z, v-0.0805z); parts2.py `lean()` turns a roof reading into the true footprint.

## Rebuild
python parts2.py; then Blender 5.2 via gpu_slot: build2.py -- ov | views [views*.json] | top | glb; python ovtop.py,
ovb.py r_ov.png ov8, board.py, zoomuv.py u0 u1 v0 v1 px/m out edge.
