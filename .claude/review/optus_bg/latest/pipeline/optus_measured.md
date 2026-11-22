# Optus plaza: measured vs model (z19 re-digitise)

Source: Esri z19 aerial (0.25 m, resampled 0.125 m/px), reference only. Tones: aerial median converted to ground colour by a
per-channel gain taken from the salmon base (aerial (201,164,142) vs sunlit ground photo, Commons "E37 Perth Stadium
Open Day 018" (191,163,155)). Concrete tone from the sunlit path in "E37 Perth Stadium Open Day 016" (194,185,181).
Tones: 0 salmon base, 1 pale beige, 2 grey-taupe, 3 concrete.

Outline error = distance from each model field edge to the nearest tone edge in the aerial (m). dE = CIELAB distance,
calibrated aerial vs model albedo.

| field | tone | area m2 | edge err median | edge err p90 | aerial (cal.) / model / dE |
| --- | --- | --- | --- | --- | --- |
| base | 0 | 9237 | - | - | (189, 162, 155) (191, 163, 155) 0.8 |
| F00 | 2 | 3578 | 0.12 | 0.75 | (170, 152, 144) (163, 152, 144) 2.9 |
| F01 | 1 | 980 | 0.12 | 0.45 | (199, 185, 171) (201, 188, 172) 1.1 |
| F02 | 1 | 579 | 0.12 | 0.28 | (208, 191, 180) (201, 188, 172) 3.1 |
| F03 | 1 | 161 | 0.12 | 0.40 | (192, 178, 175) (201, 188, 172) 7.4 |
| F04 | 1 | 80 | 0.12 | 0.28 | (201, 187, 176) (201, 188, 172) 2.7 |
| F05 | 1 | 152 | 0.12 | 0.35 | (194, 182, 172) (201, 188, 172) 3.5 |
| F06 | 1 | 193 | 0.00 | 0.25 | (204, 187, 173) (201, 188, 172) 1.6 |
| F07 | 1 | 181 | 0.12 | 0.28 | (191, 169, 159) (201, 188, 172) 7.2 |
| F08 | 1 | 38 | 0.12 | 0.35 | (195, 184, 172) (201, 188, 172) 2.4 |
| F09 | 1 | 32 | 0.00 | 0.25 | (203, 188, 174) (201, 188, 172) 1.2 |
| F10 | 1 | 30 | 0.12 | 0.35 | (210, 190, 179) (201, 188, 172) 3.9 |
| F11 | 2 | 18 | 0.18 | 0.45 | (171, 160, 141) (163, 152, 144) 6.2 |
| F12 | 3 | 381 | - | 0.28 | (176, 180, 193) (194, 185, 181) 10.2 |
| F13 | 3 | 385 | - | 0.28 | (180, 181, 194) (194, 185, 181) 9.7 |

Fields F12, F13 (kiosk slabs, re-traced as the convex hull of the concrete, edge error vs Canny edges p90 0.28 m, max 0.50 m) are the footprints of the two raised kiosk structures (concrete in the ground photos); their dE is 10
because the single-gain calibration pushes neutral concrete blue; the ground photo is the tone source.

Dropped after a field-by-field check by eye (not paving): lawn, shadow strips (fence, stadium, kiosk), tree canopy,
planter beds/rims, stadium roof, specks < 5 m2, one duplicate.

| Planters | aerial | model |
| --- | --- | --- |
| count | 5 | 5 |
| trees per planter | 1,1,1,2,1 | 1,1,1,2,1 |
| outline vs aerial | P0-P4 overlay on z19 inside the bed rims (scratchpad/proto/_pchk.jpg) | match |

Fence clip: 0 px of plaza alpha inside the stadium fence ellipse (143 x 128 m, centre x -16), measured on forecourt.png.

Dropped fields (48 traced polygons not kept as paving), each checked on a contact sheet (aerial | model, scratchpad/proto/_drop_0..3.jpg):
lawn, mulch beds and tree canopy inside the outline are painted in the plaza layer itself (lawn 3861 m2, mulch bed 3779 m2,
from the z19 vegetation mask: green, dark or brown-mulch, 1 m open/close; a patch >= 25 % open lawn is lawn), never the
terrain underneath. Shadow strips and pale path strips sit on paving and show the paving tone of the band under them.
Kiosk slabs and planters are excluded from the cut. Fields outside the outline (lawns with huts, car park, road, vent box,
stadium roof) belong to the terrain layer and the stadium model, not the plaza.

Roof: optus_roof7.glb md5 1278690bc3a38b457fada882f95dcdd9; the final md5 is to be confirmed with the texture session before the render.
