# JSS roof: measured points (working file, 2026-11-21)

Cameras: Street View panoramas solved with focal length f = (image height / 2) / tan 37.5 deg (Street View "75y" is the vertical field of view).
- dViaoI (Apr 2026): C (-152.48, 68.52, 2.55)
- Q17i (Apr 2026): C (-158.12, 97.7, 2.55)
- Tlj7152 (Apr 2023): C (-141.46, -46.72, 2.6), Cats wall only, no tower

Landmark sources:
- Cats (Premiership Stand) box corners (-120, -3.4 / -44.8, 0 / 24): XY from the passed exterior's plan, traced on the Esri z19 satellite (src/build.py polar P(a,d)). Not lean-corrected. Height 24.2 m from photo p1 (src/build.py line 280). Independent of the JSS build, but a 24 m roof edge traced on a tile that leans about 0.26 m/m south could sit up to about 6 m off in y.
- SW tower: dropped. The model head sits about 10 m north of the aerial head (separate exterior fault, to confirm with a second release).

| Point | Cameras (3 views; z +/-0.9 m, XY +/-3 m until the Cats roof XY is lean-corrected) | Model | Aerial raw / lean-corrected | Worst residual |
| --- | --- | --- | --- | --- |
| Sign top-left | (-122.87, 15.37, 17.28) | x -126, z 18.9 | n/a | 14.3 px (worst of all) |
| Block SW top (hold-out) | (-125.33, 1.59, 18.27) | x -126, z 22.9: FAULT, 4.6 m too high | x -121.3 / -122.1: FAIL, 3.2 m | 9.2 px |

Sensitivity: shifting the Cats corners +6.2 m in y (24 m x 0.26 m/m lean) in the Tlj7152 solve moves the sign TL by 2.8 m and the block SW top by 3.4 m (block top z 17.4-18.3 either way).

Wayback captures (distinct by md5): 2026-11-18 (rel 3692, same as every release 2024-10..2026-11), 2024-03-28 (rel 13968, same as 2023-10), 2023-04-05 (rel 37890). SW tower head lean: 2026 south 0.26 m/m; 2024 north 0.31 m/m; 2023 east-north-east 0.2 m/m. Block west edge raw: 2026 x -121.1; 2024 about -125 (tile looks mid-construction); 2023 about -125.2 (inconsistent with its own east lean if the edge is 18 m high). Not settled; Google Earth 3D next.

Exterior faults found here (separate from this PR, to confirm, not fixed without evidence):
1. SW tower head in the model sits about 10 m north of the 2026 aerial head.
2. Roof-top edges of the passed exterior were traced on a leaning tile; high parts may be shifted south by up to height x 0.26 m (24 m Cats roof: about 6 m).

## Geo origin of gmhba.glb

Model origin (0, 0) sits at lat -38.1579976, lon 144.3546774, north-aligned, no rotation.
Fitted (shift only) from 7 Google Earth wall-foot points (N 3, S 1, W 3), rms 0.51 m; 4 points dropped as false matches (2 S matched the inner ring, 2 E straddle a bend).
The old placement at lat -38.158219, lon 144.354577 was inferred; its origin file was not found. The fit moves the model 8.8 m east and 24.6 m north of it.
