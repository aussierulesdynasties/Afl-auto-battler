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
| Cladding colour | **UNVERIFIED**: no photo yet | neutral grey placeholder |
| Eave overhang past the wall | p10 section at 400 dpi, 44 px/m: west 2.2 m, east 2.5 m; raised slab 1.7 m W, 2.0 m E | walls inset 2.3 m from the aerial (slab) outline, raised 1.85 m; slabs 1.0 / 0.8 m deep |
| West door | DA p11: 1.3 m wide, sill at FFL, head 2.35 m above FFL, 8.3 m south of the slab NE corner | quad on the wall face, y -0.42 to 0.88, z 0.7 to 3.05; tone UNVERIFIED |
| High window band | 0.1 m below the slab underside | moved down 0.1 m |
| Glazed bay, west face | DA p11: glazed from window band to floor south of board x 1233 (26.5 m from the slab NE corner), mullions ~1.1 m, framed row 1.32 m | `glazed_w` y < -17.3, texture shedg; glass tone UNVERIFIED |
| North end wall face | DA p11 west elevation: wall starts 0.9 m further in than a 2.3 m eave (board_da_west2, x 340 vs 305 at 38.4 px/m) | north-facing wall inset 3.2 m |
| Raised roof N/S ends | DA design 1 m (N) / 2 m (S) longer | aerial as-built (±0.5 m) kept: plan extents follow the aerial, heights follow the DA |
| External ramp and stairs along the west face | drawn | **OPEN**: not modelled |
