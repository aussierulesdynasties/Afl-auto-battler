# Cazaly's: measured heights

## bldg_w (west shed: player facilities, warm-up, umpires)

**Source.** Cairns Regional Council DA 3998/2010, AFL Cairns, decided 8 Dec 2010. The decision notice
(eservices.cairns.qld.gov.au, lot 30 SP171190) carries the approved Populous / Arup drawings. Page 8 is
the ground floor plan, which has the same curved west wall as the aerial. Page 10 is "New build
section", cut through player facilities, showers, warm-up and umpires change.

**Method.** I rendered page 10 at 400 dpi. The drawn 0–15 m scale bar spans 666 px, so 44.4 px per m;
its four segments read 43–47 px/m. I took the slab edges by pixel scan along the section, measured
from the finished floor level (FFL).

| Item | Drawing (px from FFL) | Height | Error |
|---|---|---|---|
| Lower roof, top of fascia | 174 | 3.92 m above FFL | ±0.05 m drawing; ±0.1 m scale |
| Raised (warm-up) roof, top of fascia | 247 | 5.56 m above FFL | same |
| Outside ground at the west (umpires) wall | 31 below FFL | −0.70 m | ±0.2 m (sloped ground line) |
| Lower roof above outside ground | | **4.6 m** | ±0.25 m |
| Raised roof above outside ground | | **6.3 m** | ±0.25 m |

**Model.** The model's ground is flat, so these are set against the outside ground.
`h` 4.1 + the 0.5 m parapet cap = 4.6 m; `raised` 5.8 + 0.5 = 6.3 m. The raised footprint is traced
from the Esri z19 aerial.

**Held-out check.** On the Wayback release 10312 capture (WV-2, 2019-11-10), the raised-step and wall
shadow bands have a ratio of 0.39 ±0.11. The drawing gives (5.56 − 3.92) / 3.92 = 0.42, which agrees.

**Caveat.** This is the approved design. The footprint and roof layout match every aerial from 2021
to 2026; I have no ground photo yet to confirm the as-built heights.

## bldg_w walls (DA p11 west elevation, 37.8 px/m from the 3.92 m roof)

| Band, top down | Drawing | Model |
|---|---|---|
| Lower roof slab edge | 1.0 m | 0.5 m cap + 0.5 m white wall top |
| High level windows | 0.53 m, mullions ~1.1 m | 0.53 m, 1.1 m |
| Plain cladding panel | 1.32 m | horizontal ribs |
| Framed panel row | 1.06 m, frames ~1.3 m | 1.06 m, 1.32 m |
| Below floor level to outside ground | 0.70 m (section) | plinth |
| Raised slab edge / clerestory | 0.8 m / 1.03 m, windows over louvres | 0.3+0.5 m / 1.0 m |
| Cladding colour | Google Earth 3D (6 views, 2026-11-21): dark navy-charcoal on every face, sunlit too; median (46,63,85) | base (56,66,80), plinth (66,72,80) |
| Eave overhang past the wall | p10 section at 400 dpi, 44 px/m: west 2.2 m, east 2.5 m; raised slab 1.7 m W, 2.0 m E | walls inset 2.3 m from the aerial (slab) outline, raised 1.85 m; slabs 1.0 / 0.8 m deep |
| West door | DA p11: 1.3 m wide, sill at FFL, head 2.35 m above FFL, 8.3 m south of the slab NE corner; framed, plain (unglazed) leaf | dark frame 0.1 m, plain leaf, y -0.42 to 0.88, z 0.7 to 3.05; leaf tone UNVERIFIED |
| High window band | 0.1 m below the slab underside | moved down 0.1 m |
| Glazed bay, west face | DA p11: glazed from window band to floor south of board x 1233 (26.5 m from the slab NE corner), mullions ~1.1 m, framed row 1.32 m | `glazed_w` y < -17.3, texture shedg; glass tone UNVERIFIED |
| North end wall face | DA p11 west elevation: wall starts 0.9 m further in than a 2.3 m eave (board_da_west2, x 340 vs 305 at 38.4 px/m) | north-facing wall inset 3.2 m |
| Raised roof N/S ends | DA design 1 m (N) / 2 m (S) longer | aerial as-built (±0.5 m) kept: plan extents follow the aerial, heights follow the DA |
| West ramp | DA p8 plan: 1.7 m wide (�0.2) against the wall; p11: foot y -2.2, top y -16.6 at FFL, landing to y -18.9, south stair flight to y -21.0, balustrade 1.0 m | `ramp_w`; rail/deck colour UNVERIFIED |
| Outside ground under the ramp | DA p11: falls to ~1.3-1.5 m below FFL (0.55-0.75 m below model grass) | `dip_w`: grass dipped 0.73 m under the ramp and stairs (y -0.95 to -30, fading out over 1.75-3.3 m from the wall, inside the site edge), plinth carried down; north stair flight built. **Terrain: DA design, as-built unverified** |

## bldg_w raised roof west edge (Wayback z19, 3.5 px/m)

Roof-top edge = east edge of the shadow, the strongest bright-to-dark step in pixel profiles square to the
wall, 9 points per date. The offsets taper north to south, so the edge is a fitted line (two-date mean), not one shift:
NW corner 2.56 m W, SW corner 1.41 m W; the clerestory follows. The dates differ by a steady ~0.6 m (release
registration), so no single edge fits both under 0.5 m everywhere. The y 3.4 point is left out: it lies north of where
the shadow starts.

| y (m) | 13192 offset | 3692 offset | new edge | residual 13192 | residual 3692 |
|---|---|---|---|---|---|
| 0.4 | 2.45 | 1.85 | 2.33 | +0.12 | -0.48 |
| -2.5 | 2.45 | 1.85 | 2.22 | +0.23 | -0.37 |
| -5.5 | 2.50 | 1.85 | 2.10 | +0.40 | -0.25 |
| -8.4 | 2.45 | 1.85 | 1.99 | +0.46 | -0.14 |
| -11.3 | 2.45 | 1.60 | 1.88 | +0.57 | -0.28 |
| -14.3 | 2.20 | 1.55 | 1.76 | +0.44 | -0.21 |
| -17.2 | 1.90 | 1.30 | 1.65 | +0.25 | -0.35 |
| -20.2 | 1.60 | 1.05 | 1.53 | +0.07 | -0.48 |
| 3.4 (left out) | -0.45 | 1.55 | 2.44 | | |

## bldg_w south face (DA p11 south elevation, 40 px/m on the model ortho)

| Item | Drawing / aerial | Model |
|---|---|---|
| Ramp along the face | foot at the west end, up to FFL, balustrade 1.0 m | `ramp_s`, 1.7 m wide; rail colour UNVERIFIED |
| East stair flight | from the landing down to grade | `ramp_s` flight, 0.175 m risers |
| Blockwork east of the flight | "FAIR FACED BLOCKWORK", grade to 0.2 m below FFL | `blockwork` wall to 0.5 m; 390 x 190 stretcher bond; tone UNVERIFIED |
| Outside ground | ~1.45 m below FFL along the face | `dip_s` 0.73 m below the grass |
| Bays west to east | glazed, then louvre / plain bays | `bays_s`; glass, louvre and plain tones UNVERIFIED |
| Lower slab west end | DA 0.8 m past the traced corner; aerial 0.5 (13192) / 1.35 (3692) m | `slab_pt`: SW slab corner 0.8 m out, walls unchanged |
| Raised slab east end | DA 0.8 m shorter; aerial gutter line 1.46 (13192) / 0.90 (3692) m in | `raised_slab`: east overhang 0.8 m shorter, clerestory unchanged |
| Raised clerestory west end | DA 4.4 m further west (FAIL 5) | not built: the aerial shows bare lower roof there |

## bldg_w: UNVERIFIED items for the READY table

| Item | Model now | Source | Status |
|---|---|---|---|
| Balustrade colour | white steel | none (DA drawings carry no colour) | UNVERIFIED: needs photo |
| Ramp deck finish | concrete kerb tone | none | UNVERIFIED: needs photo |
| Bottom framed row north of the glazed bay | opaque framed panels | DA p11 draws frames, open or glazed not stated | UNVERIFIED: needs photo |
| Glazed bay glass tone | dark grey-blue (58,68,78) | none | UNVERIFIED: needs photo |
| Door leaf tone | light paint | DA p11 (plain leaf, no colour) | UNVERIFIED: needs photo |
| Cladding colour | dark navy-charcoal (56,66,80) | Google Earth 3D ge3d_0-5 | MATCH |
| Terrain dip at the west face | 0.73 m below the grass | DA p11 ground line (design) | DA design, as-built unverified |

## bldg_w east slab edge (2026-11-21)

Aerial inconclusive at 0.28 m/px: date-to-date registration hold-outs 0.46-2.5 m, oval-anchor centre 1.1 / 1.7 m off the model on 13192 / 3692. Director: "just do the logical fix to make it look normal". The east slab edge is one straight line on the 13192 blind fit (x = -96.09 - 0.140 y): (-97.37, 9.16) to (-92.44, -26.1), no step. Ground walkway width: UNVERIFIED.

## bldg_w Google Earth 3D check (2026-11-21)

Six Google Earth 3D views (ge3d_0-5: headings 60/100/140/10/90/150) against camera-matched renders. Fixed from FAILs: wall cladding dark on every face (was light grey); lower and raised fascias grey (were white); clerestory louvres dark; two rooftop wells on the raised roof, light kerb and dark well (positions and sizes: camera-solved recheck below). MATCH: curved west wall, grey corrugated roof, raised block with dark clerestory, ramp along the west face.

## bldg_w camera-solved recheck (2026-11-21, glb dad6e900)

Replaces the 71450e3b recheck: its camera (each GE URL, target z 8 m, fov 35) was a guess. Each GE view's camera is now solved with cv2.solvePnP (fov swept, ITERATIVE/SQPNP/EPNP/IPPE candidates, LM refine) from bldg_w slab corners and light-tower bases or tops; photos are 768x287 after the browser chrome crop, px below are scaled to 1280 wide. Renders are at 1536x574 (2x the photo) from the solved camera. Boards .claude/review/bldg_w_ge3d/cam_sbs0-4.jpg: photo, red render edges on the photo, render, then same-scale bldg_w crops, with rms and md5 on each.

| View | Points | fov | rms px (1280) | max px (1280) |
|---|---|---|---|---|
| ge3d_0 | 5 | 28.0 | 3.63 | 6.05 |
| ge3d_1 | 5 | 26.25 | 1.93 | 3.45 |
| ge3d_2 | 5 | 18.5 | 3.52 | 4.96 |
| ge3d_3 | 6 | 39.75 | 5.27 | 9.48 |
| ge3d_4 | 7 | 27.5 | 3.64 | 5.07 |

Under 6 points: views 0-2 see only 4 slab corners and one tower base clearly; tower t2 is left out everywhere (its GE base lands 2-6 m from the model in every view, not bldg_w). ge3d_3's slab SE corner is hidden by the main stand roof. ge3d_5 is not solved (corners ambiguous at that angle); the third photo per part comes from 0-4.

Roof-level registration of the Esri z19 aerial: the three visible slab corners sit 2.1-2.45 m north of the model slab (which the solved GE cameras fit to 1-2 px), x within 0.5 m. The raised block, its two wells and the shed were traced on that aerial without removing it, so the solved GE views put the raised north end 2-4 m south of the model. Fixed: raised block and raised slab moved 2.25 m south; wells re-measured on the aerial (relative to the slab) to (-118.4, 1.85) 4.0 x 2.8 m and (-115.3, -21.85) 4.5 x 3.0 m; shed nw_tent_1 re-measured to centre (-87.75, 29.65), 9.5 x 8.3 m, axis 73 deg (was 14 x 10 m, 60 deg). Board aerial_bldg_w.jpg draws the model 2.25 m north on the aerial. GE back-projection alone scatters 2-3 m in x at roof height, so plan positions come from the aerial, the GE views confirm them.

| Part | Photos | Regions |
|---|---|---|
| Roof and raised block | ge3d_1, 3, 4 | MATCH: slab outline, raised block extent and position, two dark wells with light kerbs, rib direction, roof tone, navy fascia |
| West face | ge3d_0, 1, 4 | MATCH: curved west wall line, dark cladding, eave depth; ramp and balustrade sit in the eave shadow in GE (colour UNVERIFIED, see table above) |
| South face and surroundings | ge3d_2, 3, 0 | MATCH: south slab edge, dark south clerestory band, shed position and size, ground line |

### Recheck 2 (2026-11-21, glb 5bf49f2e)

- Sixth points come from the raised-slab corners (z 6.3). rms on the 1280-wide photo: v0 3.46 px (6 pts, was 3.63/5), v1 2.31 (6, was 1.93/5), v2 3.74 (7, was 3.52/5), v4 3.64 (7). v3: 4.04 px on 5 points, but the board shows a false fit (the render is offset from the photo). Each raised-corner sixth point pushes it to 7.8-11 px. FAIL, unresolved. v5: bldg_w is cut off by the frame's bottom edge, so no clear corners. Not solved.
- Tower t2 moved from (-86.0,42.0) to (-82.2,39.2): the root of its shadow in the Esri aerial, corrected by t1's 1.25 m ground offset. The aerial, v1 and v3 put it 4.7, 10.5 and 10.3 m from the old spot. The two GE views disagree with each other by 13 m (the pole base is hidden behind the sheds), so the aerial decides.
- East edge: GE solves disagree +-3 m, model inside spread, unresolved.
