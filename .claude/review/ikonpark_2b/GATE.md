# Ikon Park (Princes Park) exterior, row 202 step 2b: READY FOR GATE

Models: `ikonpark_1990-96.glb` (A, geom `scripts/geomA10.json`) and `ikonpark_1997-2005.glb` (B = A plus the Legends Stand,
geom `scripts/geomB7.json`). Build: `blender -b -P scripts/build2.py -- GEOM OUT.glb TEXDIR` (textures from `scripts/handtex.py`).
Frame: x east, y north, z up, metres; origin lat -37.784, lon 144.9615; north = glTF -Z.

## READY FOR GATE (9 items)

1. **Plan from straight-down sources** (`proofs/bd_*.jpg`; red = model silhouette, yellow = model edges, right = 50% blend).
   - Pratt Stand (demolished 2023): fitted to Esri Wayback 2022-01-12 (release 42663), lean (0.10, 0.28) m per m of height.
     Back edge within 2 m at 95% of vertices, front at 86% (misses only at the stand ends). Runs west to (-68, -30) (`proofs/r_S7.png`).
   - Heroes and Gardiner: fitted to today's Esri, lean (0.636, 0.636), one uniform offset per edge so the shape is kept
     (`proofs/r_Nh.png`; within 2 m: Heroes back 70% / front 87%, Gardiner 85% / 85%).
   - Legends (B): on today's Esri.
   - Fosters, east steps and A's far-left stand: no straight-down image exists before those parts were rebuilt (the
     earliest straight-down release here, 2014-07 release 3026, already shows the new western buildings). Their plans stay
     from the 1994 photo, as the legacy rule "A, else B" allows.
2. **Grass edge / fence**: the turf edge measured along rays from the pitch centre is 4.75 m outside the OSM pitch on today's Esri
   (6.25 m on 2014, 5.0 m on 2022). The fence now sits at 4.75 m (it was 13.3 m and cut into the seating: `proofs/r_grass_es.png`).
   In the 1994 overlay the model's front rows show 3-8 m onto the photo's grass on the east side: that camera was solved with the
   old 13.3 m fence as a free unknown, and the plan follows the straight-down measurement.
3. **Photo match**: `proofs/pf_A_1994.jpg` (A over the 1994 aerial) and `proofs/pf_B_I2.jpg` / `pf_A_I2.jpg` (over the
   ground-level photo). The ground-level camera was re-solved (`scripts/fitI2b.py` -> `camI2b.json`): fence held at 4.75 m and the
   eye held 1.2 m above the model's seat rake. Grass-edge error 0.88 px. The old solve put the eye 2.7 m inside the Heroes seating.
4. **Pratt masts and roof edges**: masts kept on the original vertices; roof edges follow the 2022 roof (item 1). Heights stay at
   the 1994-photo values (A7), which the ground-level photo also gives (18-31 m).
5. **Stadium only, no crowd**: no turf, posts, nets or park. Seats are modelled, not painted (gate fault 1): stepped rows on a 0.8 m
   tread, each empty seat a pan, front lip and back at the Moorabbin bench sizes, 0.5 m pitch, an aisle every 12th sector,
   hand-made `seatrow` / `seatrowlegends` textures (`proofs/cu_A.jpg`, `cu_B.jpg` seat views).
   The detached brick block "oldbrick" (A, outside the stand ring at 143.6 E, -64.7 N) is removed: no straight-down image shows a
   building there and it sits at the cut edge of the 1994 photo (`proofs/oldbrick_sat.png`).
6. **Signs**: the ground's own only; the Foster's sponsor sign and Carlton sign materials are gone, no ads on any face.
7. **Hand-made textures**: every texture painted from module sizes (`scripts/handtex.py`), no photo pixels. stddev all >= 10
   (`proofs/tex_stddev.txt`, lowest red 10.9). Each used texture beside its photo crop: `proofs/tex_pairs.jpg`. Wood repainted
   weathered grey-brown to match the west paling fence in 1994. No era photo exists for `glassdark` or the Gardiner `red` band
   (the board says so).
8. **Joins, facades, turntables**: `proofs/cu_A.jpg`, `cu_B.jpg` (joins, back facades), `proofs/tt_sheet.jpg` (Godot turntable,
   4 frames each, top row A). No floating parts or open gaps. Stand joins (gate fault 2): each seat sector belongs to one stand
   (overlaps split at the middle) and follows that stand's own back edge; a concrete end wall closes every step in the outline,
   so no rake runs through another (`join_pratt_west`, `join_pratt_legends`).
9. **Pratt rear wall** (gate fault 3): copied from the Austadiums aerial (before the 2023 demolition, `proofs/tex_pairs.jpg` last
   row): ribbed light-grey cladding on steel columns every 8 m, white fascia above, not brick. Hand-made `cladding` texture,
   faint panel tones so no repeat shows (`facade_pratt_back`).

No open faults.

## Notes
- The brief's `reset --hard` in the shared trusting-edison worktree was not run (lead's order); work is on claude/practical-napier-5bd466.
- Scripts: prattfix / standfix / edgefit (edge fits), grassfit, satwb (Wayback mosaics), sat, geo, ov2 / board / topdown
  (straight-down proofs), rendcam / closeups / turntable.gd (views), texpair (texture board), rayprobe / rakeprobe (camera checks).
