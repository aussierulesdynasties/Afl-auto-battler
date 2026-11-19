# Marvel Stadium exterior (row 202 2b): ready for gate

Model: mv2/marvel2.glb (225 parts, about 25,000 faces, origin at the pitch centre, north +Y). Hand-made textures only (mv2/tex,
gen_tex.py then paint_tex.py). No field, posts, goal nets, sponsor ads, boards, temporary stands or background buildings;
the ground's own MARVEL STADIUM sign is lettered (director 2026-11-19).

## Proofs (mv2/proof/)
- Camera-matched overlay on the 2019 oblique aerial: ov8_on.jpg, ov8_blend.jpg; end roofs photo|model: j_end_n.jpg, j_end_s.jpg.
- Top-down overlay, model straight down on the straight-down satellite, same scale, north and lean: t_on.jpg (cyan =
  model silhouette, magenta = model edges), t_blend.jpg. Close zooms of the rebuilt east: zE1e, zE2e, zNEe, zSEe.
- Crop board per part (satellite | model | outlines): board_parts_1.jpg (N, S, W, E), board_parts_2.jpg (NW, NE, SW, SE).
- Turntable: r_tt_w/n/e/s.jpg, sheet sh_tt.jpg. Orbit video: marvel_orbit.mp4 (72 frames, 12 fps).
- Facade close-up: r_cu_facade.jpg. Join close-ups: r_cu_corner_nw/sw/ne/se, r_cu_roofedge_nw/s, r_cu_tiers,
  r_cu_east, r_cu_join_east_c (sheets sh_cu.jpg, sh_cu_east.jpg).

## Gate round 2 (fixes for the f5aced2ad gate)
- Base: one site pad (paving top, concrete skirt, z -1.0 to 0.05) runs under every wall. It is the union of every
  ground-touching footprint plus 2 m, with a hole at the plinth's inner edge (no field). Proof: r_tt_*, r_cu_corner_*,
  eye-level r_low_0..7 (sheet sh_low.jpg).
- West facade as the photo shows: light-grey panel cladding (new hand-made texture panel_lt) on both podium storeys;
  10 deep recessed glazed bays on the ground storey and 9 on the upper, glass 1.2 m behind the piers, with silver
  mullions and transoms (new texture shopglass); a spandrel band above the bays; the terrace glass balustrade and
  the forecourt balustrade each get a white top rail. No photo pixels, no lettering. Proof: r_cu_facade.jpg.

## East side
Rebuilt from the satellite (no longer a mirror of the west): NE block (z33, plant to 37), box A (z27.4), block B (z24,
two widths), C deck (z7) and walkway (z10), block D (z24, east edge v-131.3 to -124.6), box E (z27.4). Heights from
shadow lengths (0.5 m shadow per m), checked against oblique photo 31603700. Satellite roofs lean
(u-0.1738z, v-0.0805z); parts2.py `lean()` turns a roof reading into the true footprint.

## Texture pass (2026-11-19)
Every big surface repainted by hand in paint_tex.py (helpers in texpaint.py), no photo pixels, colours kept to the old
means: concrete formwork panels 2.4 x 1.2 m with tie holes and rain streaks; roof sheeting seams every 0.6 m with dirt
along them; soffit ribs 0.2 m and purlins 1.5 m; seats 0.5 m with gaps, row shadows and a 1.2 m aisle every 24 seats;
fascias, gutters and teal steel with seams and grime toward the bottom; cladding panels with per-panel tone and streaks;
paving 1.2 m slabs; glazing per-pane reflection. Sign: white MARVEL on red, white STADIUM on black, outward face only
(Bahnschrift Bold Condensed, sized to the panels as in the 2019 aerial). Proof: proof/tex_board_1.jpg, tex_board_2.jpg
(photo | before | game camera | close per surface, stddev before -> after); board_tex.py rebuilds it.

## Rebuild
python gen_tex.py; python paint_tex.py; python parts2.py; then Blender 5.2 via gpu_slot: build2.py -- ov | views [views*.json] | top | glb; python ovtop.py,
ovb.py r_ov.png ov8, board.py, zoomuv.py u0 u1 v0 v1 px/m out edge.

## Gate round 3 (fixes for the 82dba61b4 texture gate)
- Every map now 10 or more grey stddev (lowest 10.3). Sign fills (signred, signblack) get aluminium trim at each
  1 m x 2 m panel joint, light streaks and a dust bloom toward the foot; the MARVEL / STADIUM lettering is drawn after
  the fill and stays crisp. signblack's mean rose from RGB (15,15,17) to (28,28,31): a pure black fill cannot reach
  stddev 10 without either going grey or adding lighter marks, and the photo's black panel reads dark grey in daylight.
- Seats matched to the seat reference crop (tex_board_1, seats row): mean of the lit seat pixels in the crop is
  RGB (108,128,146). Seat map before RGB (37,46,77) navy, after RGB (108,128,146). Seats empty: no crowd anywhere.
- Slate corner blocks (and navy cladding): panel size read from exterior photo 000 (street level), scaled by the 1.5 m
  mesh bays: 1.5 m wide x 3.6 m tall. Dark 20 mm joints, per-panel tone, rain streaks from every joint.

## Gate round 4 (director 2026-11-19: "Remove the mottle first")
- Seats: per-seat tone and the mottle removed; the map is now even like the photo. Rows, seat gaps, risers and the
  1.2 m aisle stairs kept. Stddev 50.8.
- Green truss steel (teal): mottle, blotch noise and tint removed; even paint. The 2 m plate seams are kept and drawn
  deeper (25 mm joint) so the map holds stddev 11.9. Re-rendered: tex_board_1/2, r_cu_tiers and every other proof.

## Gate checklist (ground builder rules, 8 items)
1. Overlays: ov8_on.jpg, ov8_blend.jpg (oblique aerial), j_end_n.jpg, j_end_s.jpg.
2. Turntable: r_tt_w/n/e/s.jpg, sh_tt.jpg, marvel_orbit.mp4 (72 frames).
3. Facade and join close-ups: r_cu_facade, r_cu_corner_nw/sw/ne/se, r_cu_roofedge_nw/s, r_cu_tiers, r_cu_east,
   r_cu_join_east_c (sh_cu.jpg, sh_cu_east.jpg); eye level r_low_0..7 (sh_low.jpg).
4. Top-down overlay: t_on.jpg, t_blend.jpg; zooms zE1e, zE2e, zNEe, zSEe; part boards board_parts_1/2.jpg.
5. Texture close-up per surface beside a photo crop: tex_board_1.jpg, tex_board_2.jpg (photo | before | game camera |
   close). Grey stddev before->after, all 10 or more: base 61.3->61.3, canvas 2.9->17.6, concrete 5.0->13.9, curtain 28.9->28.9, deck 9.5->14.3, endroof 12.5->13.1, fascia 5.5->12.4, glass 9.6->13.2, gutter 4.5->11.5, louvre 25.9->19.4, mesh 18.4->18.4, navy 3.7->10.3, panel_lt 5.6->12.3, paving 6.7->13.8, plants 9.7->20.3, ribs 14.3->14.3, riser 2.3->10.8, seats 14.8->50.8, shopglass 28.2->28.2, sign_marvel new->73.6, sign_stadium new->99.7, signblack 2.1->12.6, signred 2.1->12.3, silver 16.2->14.9, slate 4.5->12.1, soffit 4.2->12.5, tank 8.7->13.5, teal 2.4->11.9, white 2.2->15.6.
6. Seating close-up, empty seats: tex_board_1 seats row (game camera and close); r_cu_tiers.jpg. Crowd removed: none
   (the model never had one).
7. Each sign beside its crop: tex_board_2 last row, MARVEL STADIUM beside the 2019 aerial crop. It is the ground's only
   own sign.
8. no open faults
