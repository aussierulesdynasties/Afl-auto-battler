# Optus Stadium exterior: ready for gate (2026-11-19)

Rebuilt model, rendered from the camera matched to photo o2, overlaid on the photo, and checked straight down on the
satellite. All 7 faults from the paused round are dealt with below. Stadium only: the pavilions, plaza, trees and
roads around it are left out (background pass later). Every texture is hand-made (tex/), no photo pixels.

## Texture pass (2026-11-19)
Big surfaces repainted by hand, colours kept, no geometry change: roof PTFE (1.6 m strips, seams, sag, streaks), roof
underside, seats (per-seat grey/tan mix around each tier's colour, aisles, worn nosings), bronze (dust, grain, rain
tracks), glass (per-pane reflection, dust), podium wall, terrace, plaza/deck/concrete paving (1 m flags, aggregate),
cladding, stairs. The ground's own name signs added on the bronze, drawn by hand from photo 018 (east, with the "yes")
and photo o2 (south-west, without it). No crowd was in the model; nothing removed.
- `proof/tex_board_1.jpg`, `proof/tex_board_2.jpg`: one row per surface, photo crop | game camera | close-up (before and
  after), grey stddev before -> after, the empty-seat close-up, each sign beside its photo.
- Rebuild order: `scripts/paint_tex.py` (reads `tex_base/`, writes `tex/`), then build.py. Views: `scripts/shots.py`
  writes `views_tex.json`; `scripts/views.py` renders it; `scripts/board_tex.py` makes the boards.

## 3D seats (2026-11-20)
Real empty seats replace the painted ones: 56,473 seats, each a pan, a back and steel side legs (0.44 m pans at 0.5 m
pitch; neighbours share one grey steel leg under each gap, block-end legs flush with the pan). Every seat sits on its
own tread, back 8 cm off the riser, at the row's height (raycast: 0 off-tread, 54 rows = 54 heights); blocks packed
edge to edge between straight aisles with a half step on every row; 260 seats that clashed with structure dropped.
Aisles every 7.4 m of a 14.8 m bay (upper tier offset 3.7 m) plus the vomitories. Colours: the tier colours (lower
cream, middle tan, upper grey), each seat pushed toward grey-blue or tan at random. Painted seats removed from
`tex/seats.png` (bare concrete risers, worn nosings). No crowd.
- `proof/seat_board.jpg`: the photo crop beside a photo-style view and two seat-height close-ups (SE, NW).
- `proof/tex_board_1.jpg`: seats row re-rendered with the 3D seats.
- Code: the seat block at the end of `scripts/build.py`; the riser repaint in `scripts/paint_tex.py` (rowband).

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
_2026-11-22: the reference photos (`refs/`), the satellite overlays (`topdown/`) and the photo-beside-render boards (`proof/`) are taken out of the repo: raw imagery is never committed (docs/MCG_STANDARD.md, "Where shipped data may come from"). The lists below describe them as they were; they are kept in the project files under optus-rebuild/review-imagery/._
- `refs/o1-o4.jpg`: the reference photos (o2 is the matched one).
- `scripts/`: build.py (Blender 5.2: `blender -b --python build.py -- <abs>/optus.glb <abs>/optus.blend`), geom.json,
  render.py + camL.json (matched camera), turn.py, board.py, parts.py, proof.sh, joins.sh, westfix.py, bpj.py,
  topdown.py, topov.py, roofsat.py, roofmark.py, period.py, stov.py, stz.py, cpair.py, texture makers.
- `tex_base/`: the first hand-made textures; `tex/`: the texture-pass maps the build reads (build.py looks for `tex/` beside itself: copy it into `scripts/`
  before building). The ground mat and turf are no longer loaded (the game draws the turf).
- The glb is not committed; build.py rebuilds it (148,873 triangles plus the seats3d object, 105 MB). Last gate-passed model:
  `.claude/review/optus_model/` (commit 82bc8feb3).

## Gate checklist (ground builder rules, 8 items)
1. Camera-matched overlays: `proof/board.png` (photo o2 | render | 50% overlay), `proof/edges.png`, `proof/parts.png`,
   `proof/full_pair.png`, `proof/stov.png`.
2. Turntable: `proof/turntable.mp4` (48 frames), `proof/turn4.png`.
3. Facade and join close-ups: `proof/close_E.png`, `close_W.png`, `close_S.png`, `end_S.png`, `end_N.png`,
   `proof/joins8.png`, `proof/jn/`. Every join clean (podium-wall panel tone cut to 0.015 so it no longer reads as stripes).
4. Top-down overlay: `topdown/topov_lean.png` and the eight zooms; roof edge median 0.00 m, 157 of 180 probes within 2 m,
   every outlier explained above.
5. Texture close-up per surface beside a photo crop: `proof/tex_board_1.jpg`, `proof/tex_board_2.jpg`. Grey stddev
   (PIL, 0-255), every map 10 or more: aisle 16.5, bench 50.5, bronze 30.7, clad 11.9, column 15.8, concrete 13.3,
   dark 46.3, deck 12.5, entrance 35.3, glass 50.0, grille 62.4, lamp 12.3, louvre 16.7, mesh 30.0, pglass 10.4,
   plaza 12.6, plouvre 20.4, podwall 11.3, rail 10.3, riser 14.9, roof 10.8, seats 46.9, sign_a 42.0, sign_b 43.6,
   steps 22.2, terrace 15.0, under 11.4, white 16.8.
6. Seating close-up, empty seats: `proof/tex_board_1.jpg` row 3. No crowd was in the model (no cards, meshes, people
   boards or painted crowd); nothing removed. Seat colours unchanged from the passed model: tiers read from o2 (lower
   pale grey, middle tan, upper grey); the seat crop (upper tier in shade, mean RGB 180,177,167) matches the model's
   upper tier (178,182,188).
7. Each sign beside its reference crop: `proof/tex_board_2.jpg` rows 4-5 (sign A from photo 018 with the "yes", sign B
   from o2 without it).
8. no open faults

no open faults
