# Adelaide Oval: READY FOR GATE (2026-11-19, Melbourne)

Stadium only, inside the outer fence: no field, posts, nets, trees, temporary stands, ads or crowd (seats empty).
Plan shapes from the Esri satellite and OSM only; heights and looks from the photos. All textures and lettering hand-made (no photo pixels).

## Faults fixed since the gate rejection of 32d3d049f
| Fault | Fix | Proof |
| --- | --- | --- |
| East roof membrane lobes: lumpy back edges, wavy front hem | Lobe outlines rebuilt as smooth round arcs from the satellite plan (gen.py smooth/round outline, rim_fit, front_fit) | proof/join_west.png |
| Diagonal fold at the top corner of the white end wall, north end of the east stand | Wall skip box plus corner inset clamp in gen.py | proof/join_west.png |
| River roof front-edge dip | Hem lift (hem_dz) and a round front cut | proof/join_river.png |
| River roof rim jagged at the outer wall; dark jagged wall edge behind the east membranes | Per-ray back fit; hotel top slab back line smoothed | proof/join_river.png, proof/join_east.png |
| The Hill missing | Built from the satellite plan and photos c09/c11: grass patches, heritage scoreboard (verandah, 15 brackets, clock tower, weathervane), big screen, rails, amenities | proof/Hill_c09_overlay.jpg, proof/Hill_c11_overlay.jpg, proof/hill_close.png, proof/hill_above.png |

## Top-down check (straight-down render on the Esri satellite, same scale and north, satellite lean corrected)
Fence oval N/E/W/S within about 1 m; east roof hem about 1 m; west stand back edge about 1 m; Hill grass edges 1 to 2 m; big screen about 1 m.
Proof: proof/topdown_overlay.png.

## Proof set (proof/)
- turntable_4.jpg: four views, 30 degrees up, 420 m out.
- A/B/C_photo_render_overlay.jpg: photo | render | 50% overlay from the matched cameras.
- Hill_c09_overlay.jpg, Hill_c11_overlay.jpg, hill_close.png, hill_above.png: The Hill.
- join_west.png, join_river.png, join_east.png: roof and wall joins close up.
- closeup_hotel_facade.png, closeup_west_brick_facade.png: facades.
- topdown_overlay.png: the straight-down check.
- signs_board.jpg: every sign added, reference photo crop beside the render.

## Ground's own signs added (no sponsors, ads, banners or posters)
Each one is shown beside its reference crop in proof/signs_board.jpg.
1. Heritage scoreboard lettering (photo c11): 1ST/2ND INNINGS (twice), WICKETS, SUNDRIES, TOTAL, BOWLERS, WKTS, RUNS, V, BATSMEN, OUT, B, RUNS, FALL OF WKTS, batting order 1 to 9, fall of wickets 1 FOR, 2 to 9 with their dots, OVERS R'QD, UMPIRES. Gold on the dark green board.
2. "East Gate" (photo C): white lettering on the hotel-end glazing, placed by rays through camera C.
3. "Adelaide Oval" pylon (photo C): the 13 m grey pylon at the East Gate with the bronze "Adelaide [ringed O]val" logo reading upwards and its dark light bracket on top.

## Not done, and why
- Stand-name signs on the fascias (Chappell Stand, Sir Donald Bradman Pavilion, Riverbank Stand, Wanganeen-Oatey, Edwin Smith, Elder): seen in close/*.jpg, but none of those photos has a fitted camera, so their size and place cannot be copied accurately yet.
- Camera C: the east roof crowns sit slightly above the photo in the C overlay. Photo C is a stitched panorama and its camera fit is approximate; A and B, which are single frames, line up on the same roof.
