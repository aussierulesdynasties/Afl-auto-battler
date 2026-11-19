# Adelaide Oval: READY FOR GATE (2026-11-20, Melbourne)

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
| West and river roof undersides mid blue-grey; the photo shows cream membrane over a steel lattice | Underside drawn as the membrane fabric in the photo's cream (spec under 228,222,212), a 9 m diamond steel lattice, and daylight through the fabric at medium strength (director's choice B, 2026-11-20) | proof/texture_board.jpg (roof_underside row), proof/empty_seats_far.png |

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
- texture_board.jpg: each surface's photo crop beside the model at game distance and close.
- empty_seats_closeup.png, empty_seats_far.png: seating close-ups, seats empty.

## Textures (hand-made, procedural in tools/shade.py; no photo pixels)
Every big surface carries hand-made detail: concrete panels with joints, mottled weathering, aggregate speckle and rain runs under ledges; membrane seams, welded laps, seam grime and dust drifts, and from below a steel lattice with daylight through the fabric; steel sheet seams, faded sheets, scuffs and grime toward sheet bottoms; seats as rows, backs, gaps and concrete aisle steps; Hill turf wear; brick bond; banded stone courses; scoreboard panels faded unevenly.

Pass rule (director, relayed by the stadium lead 2026-11-19): a texture passes when it looks like its photo crop; the stddev is information only. Dark concrete copies the photo's weathering (director's answer here: "Yes, use A").

Each surface beside its photo crop, far (game distance) and near: proof/texture_board.jpg.

Grey stddev (0-255) of each material's base colour, measured unlit on a 24 m wall (far) and a 4 m patch (near), tools/texprobe.py + tools/texstat.py. Before = the old shader on the same colours.

| Material (model colour) | Before far / near | Now far / near | Photo crop sd |
| --- | --- | --- | --- |
| brick | 7.6 / 11.3 | 10.7 / 13.5 | 26.2 |
| brick_red | 19.1 / 28.2 | 20.1 / 28.9 | 26.2 |
| concrete_cream | 4.1 / 4.3 | 15.7 / 18.4 | 11.6 (west stand concrete) |
| concrete_dark | 1.3 / 1.4 | 4.7 / 5.5 | 11.6 (west stand concrete) |
| concrete_grey | 2.9 / 3.1 | 11.2 / 13.2 | 11.6 (west stand concrete) |
| concrete_mid | 1.9 / 2.0 | 7.2 / 8.5 | 11.6 (west stand concrete) |
| concrete_slate | 1.5 / 1.6 | 5.7 / 6.8 | 11.6 (west stand concrete) |
| copper | 11.2 / 14.2 | 11.2 / 14.2 | - |
| glass | 22.8 / 24.7 | 22.8 / 24.7 | - |
| hill_turf | 1.3 / 1.3 | 10.4 / 10.0 | 16.7 (Hill grass) |
| membrane | 2.8 / 2.4 | 10.9 / 10.1 | 45.2 (west stand roof underside) |
| scoreboard | 3.8 / 4.8 | 10.9 / 12.8 | 7.1 (heritage scoreboard) |
| seats_maroon | 26.2 / 23.9 | 29.6 / 28.6 | 31.2 |
| seats_navy | 37.7 / 35.9 | 39.6 / 38.5 | 31.2 |
| seats_red | 16.4 / 13.6 | 22.4 / 21.9 | 31.2 |
| seats_slate | 15.2 / 12.4 | 21.4 / 21.3 | 31.2 |
| seats_teal | 12.7 / 10.0 | 20.0 / 20.4 | 31.2 |
| steel_grey | 8.3 / 7.6 | 9.7 / 8.5 | 2.2 (pale fascia) |
| steel_pale | 9.8 / 8.9 | 11.4 / 9.9 | 2.2 (pale fascia) |
| steel_white | 11.7 / 10.7 | 13.7 / 11.9 | 2.2 (pale fascia) |
| stone | 4.9 / 5.5 | 8.5 / 8.7 | - |

Grey stddev scales with brightness: dark concrete (mean 53) at sd 4.7 varies about as much, relative to its own colour, as cream concrete (mean 212) at 15.7.

## No crowd
No crowd existed in this model: no crowd cards, painted crowd or crowd meshes were ever built, so there was nothing to remove. Every seat is empty, in its real colour, with the hand-made seat texture (rows, backs, gaps, aisle steps). Proof: proof/empty_seats_closeup.png and proof/empty_seats_far.png.

## Ground's own signs added (no sponsors, ads, banners or posters)
Each one is shown beside its reference crop in proof/signs_board.jpg.
1. Heritage scoreboard lettering (photo c11): 1ST/2ND INNINGS (twice), WICKETS, SUNDRIES, TOTAL, BOWLERS, WKTS, RUNS, V, BATSMEN, OUT, B, RUNS, FALL OF WKTS, batting order 1 to 9, fall of wickets 1 FOR, 2 to 9 with their dots, OVERS R'QD, UMPIRES. Gold on the dark green board.
2. "East Gate" (photo C): white lettering on the hotel-end glazing, placed by rays through camera C.
3. "Adelaide Oval" pylon (photo C): the 13 m grey pylon at the East Gate with the bronze "Adelaide [ringed O]val" logo reading upwards and its dark light bracket on top.

## Not done, and why
- Stand-name signs on the fascias (Chappell Stand, Sir Donald Bradman Pavilion, Riverbank Stand, Wanganeen-Oatey, Edwin Smith, Elder): seen in close/*.jpg, but none of those photos has a fitted camera, so their size and place cannot be copied accurately yet.
- Camera C: the east roof crowns sit slightly above the photo in the C overlay. Photo C is a stitched panorama and its camera fit is approximate; A and B, which are single frames, line up on the same roof.

No open faults.
