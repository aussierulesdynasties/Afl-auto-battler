# Optus Stadium exterior: ready for gate (2026-11-19)

Rebuilt model, rendered from the camera matched to photo o2, overlaid on the photo, and checked straight down on the
satellite. All 7 faults from the paused round are dealt with below. Stadium only: the pavilions, plaza, trees and
roads around it are left out (background pass later). Every texture is hand-made (tex/), no photo pixels.

## Proof (all in this folder)
- `proof/board.png`: photo | render from the matched camera | 50% overlay. `proof/edges.png`: edge overlay.
  `proof/parts.png`: part-by-part crops, photo beside render (roof, glass, bronze, podium, stair, lift, west terrace).
- `proof/stov.png`: four-panel overlay of the stair corner. `proof/stz_stair.png`, `proof/stz_head.png`: photo vs model
  on a labelled pixel grid. `proof/cpair.png`: four corner pairs (A stair foot, B lift, C stair head, D railing).
- `proof/turn4.png`: four quarters. `proof/turntable.mp4`: 48-frame orbit, 12 fps.
- `proof/close_E.png`, `close_W.png`, `close_S.png`, `end_S.png`, `end_N.png`: facade close-ups (hand-made textures, no blur).
- `proof/joins8.png` (and `proof/jn/`): joins at both ends of the entrance side (he, hs), the parapet start, the stair.
- `proof/west5.png`, `proof/glassgrid2.png`: west terrace, glass and canopy on the photo grid. `proof/full_pair.png`,
  `proof/stair6.png`: full photo/render pair and the stair overlay.
- Top-down gate: `topdown/topov_lean.png` (whole ground), `topdown/topov_lean_{N,NE,E,SE,Sth,SW,W,NW}.png` (zooms),
  `topdown/topov_lean_half.png`, `topdown/top_lean.png` (the render alone), `topdown/roof_outliers.png`,
  `topdown/roofmark_{N,E,S,W}.png`, `topdown/satNW.png`.

## The 7 faults
1. **Bench rows.** Photo rows repeat every 2.4-2.5 px; model now 58 steps (2.3-2.4 px), dark slat on each step
   (`stz_stair.png`, period measured with `scripts/period.py`).
2. **Lift-side stepped wall at the stair foot.** Lines up with the photo corner (`stov.png`, `cpair.png` A).
3. **Lift.** Tall box fitted to the photo's four roof corners within 2 px, roof at 11.3 m (`cpair.png` B, `stz_head.png`).
   Lighting: a single sun from 165 deg, 42 deg up, fitted to the lift's lit and shaded faces in o2.
4. **Deck over the "navy facade".** The navy shape right of the stair head is the shadow of the curved pavilion next to
   the stadium, not a stadium wall (`stz_head.png`: it ends where the pavilion's roof shadow ends). The pavilion is left
   out (stadium only), so the deck stays bare there, as the stadium itself is.
5. **Walkways.** Read from o2 brightness profiles up the flight: upper walkway at 27-33% of the flight, from 10% across to
   the full width; lower walkway at 58.5-64.5%, full width (the dark spot mid-way is people). `stz_stair.png`, `stair6.png`.
6. **Curved-building-side wall reading light.** Same cause as 4: the photo's dark there is the pavilion's shadow. The
   wall's own face now takes the fitted sun and matches the photo where the pavilion shadow does not fall.
7. **Satellite top-down gate.** Straight-down orthographic render, 0.25 m per pixel, north up, over Esri z19; cyan
   = model silhouette, magenta = model edges, 10 m grid. Plan shape only from the satellite and OpenStreetMap.
   - The satellite photo is not truly vertical: tall parts lean by (-0.0365, -0.30) m per metre of height, measured
     from the roof ring against the field. The overlay leans the model the same way, so the roof is compared with the
     roof in the photo.
   - Roof edge vs satellite, probed every 2 deg (180 angles): within 2 m at 157; median 0.00 m, mean 1.19 m.
     The 23 outside 2 m, each looked at (`roof_outliers.png`): pink plaza paving (4, 10 deg), white seats seen
     through (54), the roof's membrane edge vs its fascia - model sits on the fascia (86-130), a white canopy outside
     the roof (194-198), paving (286, 316, 318), the stage where the probe stopped early (304), a white path (330);
     216-234 and 334-336 are 2-3 m off.
   - Stair outline vs satellite: within about 1 m. Curved-pavilion side edge: model -181.9 m vs satellite -182.5 m.

## Other measurements
- Roof height solves at 46.6 m in the camera fit (published figure 42 m); kept, because the overlay and the satellite
  both fit with it.
- Drum (bronze band) plan from OpenStreetMap, except the west, refit from o2 (`scripts/westfix.py`): band, glass
  line and canopy read on the photo grid at 22 m (`glassgrid2.png`); glazing under the bronze from 8 m up to 12.5-13.5 m.
  Glass beyond 205 deg is hidden in o2 and blends back to the drum line 4.5 m in by 250 deg.
- West pod plan from OpenStreetMap and the satellite, cut back to x -183.3 m (y -16 to 18.5 m) where the
  orange-roofed pavilion stands against it; that leaves a short angled wall and a recessed face the pavilion covers
  (`close_W.png`). The mesh balustrade ends there and the solid sandstone parapet starts, as in o2.
- East plaza: podium edge, parapet and lamp posts as in o2.
- Joins found in this round's own check and fixed before push: three see-through triangles where the bronze band's
  bottom steps at the two ends of the street-level entrance side (13.5 m to 8 m at 143-144; 8 m to 7 m at 144-145 and
  367-368) are now closed with the dark strip/recess material (`proof/jn/hs_*`, `proof/jn/he_*`).

## Files
- `refs/o1-o4.jpg`: the reference photos (o2 is the matched one).
- `scripts/`: build.py (Blender 5.2: `blender -b --python build.py -- <abs>/optus.glb <abs>/optus.blend`), geom.json,
  render.py + camL.json (matched camera), turn.py, board.py, parts.py, proof.sh, joins.sh, westfix.py, bpj.py,
  topdown.py, topov.py, roofsat.py, roofmark.py, period.py, stov.py, stz.py, cpair.py, texture makers.
- `tex/`: hand-made textures the build reads (build.py looks for `tex/` beside itself: copy it into `scripts/`
  before building). The 64 MB ground/turf images are left out; the model does not use them.
- The 84 MB glb is not committed; build.py rebuilds it (148,870 triangles). Last gate-passed model:
  `.claude/review/optus_model/` (commit 82bc8feb3).
