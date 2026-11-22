# Mars Stadium: outline and rings measured against Google Earth (2026-11-22)

This report covers the rule that a ground's outline is one smooth curve fitted to a Google Earth trace, with every
ring an exact offset of it. Everything here is measured, not judged by eye. Each check gives its limit first, then
the result. Google Earth's imagery of Mars Stadium dates from December 2025, before the two south-east stands were
finished.

## How it is measured

- `compare.py`: Mars's entry for the shared compare tool, `tools/grounds/ge_compare.py` (#2015). It holds the
  views, the camera and Google Earth's turf height, read at **452 m** with `ge_shoot.js --level`.
- `trace.py`: traces the fence in six straight-down Google Earth tiles, each taken from 330 m (0.208 m a pixel).
  - In the west and south, the fence is the white rail.
  - In the north and east, the fence is where the turf meets the shaded stand front. The close oblique views
    `fence_*` show that the stand front is the fence there.
- `fit.py`: fits one smooth curve, r(t), as an 8-harmonic Fourier series. It drops rays more than 1 m off the curve
  as misreads and counts them.
- `model/build.py`: `pol(b, r)` puts each point at `r - fence_r(b)` along the fence's outward normal. A ring at a
  fixed distance from the fence is therefore an exact offset of the curve.
- `rings.py`: finds each roof's front and back edges in the straight-down tiles. It corrects for parallax using the
  roof heights, and gives each edge as a distance out from the curve.
- `heights.py`: reads a ring's height from the matched oblique views. It sweeps the height and finds where an edge
  runs along the whole projected ring.
- The plan positions (`rings.py`) and the heights (`heights.py`) depend on each other, so the two were run in turn
  until both settled.
- `lines.py`: draws the model's rings on Google Earth's shots through the calibrated camera.
- `towers.py`: finds the lamp heads and places each one by parallax across the tiles.

## Results

| Check | Limit | Result | Verdict |
| --- | --- | --- | --- |
| Fence curve against the Google Earth trace | rms ≤ 0.3 m, p95 ≤ 0.6 m, max ≤ 1.0 m | 629 of 720 bearings traced, 33 dropped as misreads; rms 0.22 m, p95 0.47 m, max 0.91 m | PASS |
| Old model fence (OSM) against that curve | the same | rms 1.36 m, p90 3.0 m, max 3.5 m | FAIL, replaced |
| Rings are exact offsets | normal within 1 deg | built that way; offset direction within 0.5 deg of the normal | PASS |
| West roof, front edge | median within 0.5 m | Google Earth 1.45 m from the fence, model 1.45 m (was 0.03 m) | PASS |
| West roof, back edge | median within 0.5 m | Google Earth 23.15 m, model 23.15 m (was 22.9 m) | PASS |
| West roof, how far the real edges stray from a pure offset | p10 to p90 ≤ 1.0 m | front 0.19 m, back 0.93 m | PASS |
| East roof, front edge | median within 0.5 m | Google Earth 2.16 m, model 2.2 m (was 6.8 m) | PASS |
| East roof, back edge | median within 0.5 m | Google Earth 10.46 m, model 10.45 m (was 15.5 m) | PASS |
| East roof, how far the real edges stray from a pure offset | p10 to p90 ≤ 1.0 m | front 0.94 m, back 2.38 m | FAIL (back) |
| North roof, front edge | median within 0.5 m | Google Earth 0.16 m, model 0.15 m (was 2.2 m) | PASS |
| North roof, how far the real front edge strays from a pure offset | p10 to p90 ≤ 1.0 m | 1.41 m | FAIL |
| North roof, back edge | median within 0.5 m | not readable: it runs into the clubrooms' roof | NOT MEASURED |
| West roof, front height | within 0.5 m in 3 or more views | 15.0 m (4 views, 14.6 to 15.0 m); model 15.0 m | PASS |
| West roof, back height | within 0.5 m in 3 or more views | 11.3 m (4 views, 11.2 to 11.4 m); model 11.3 m (was 16.4 m) | PASS |
| North roof, front height | the same | 7.2 m (3 views, 7.0 to 7.4 m); model 7.2 m (was 8.5 m) | PASS |
| East roof, front height | the same | 6.8 m (4 views, all 6.8 m); model 6.8 m (was 8.0 m) | PASS |
| East and north roofs, back height | the same | no consistent reading; the model keeps 8.5 m and 11.0 m | NOT MEASURED |
| Fence top height, used to test `heights.py` | reads 1.1 m | reads 7.2 m (it picks up the stands' front edge above the fence) | FAIL: the method cannot read the fence; the fence is checked in plan instead |
| West stand back-wall base | within 0.5 m | trees hide it in every Google Earth view | NOT MEASURED |
| Tier lines (seat front, back row) | within 0.5 m | drawn on the shots, but the edge search could not separate them from the other edges on the stand | NOT MEASURED |
| South-east stands, plan and heights | within 0.5 m | Google Earth's December 2025 imagery shows them half-built | NOT CHECKABLE |

## Light towers

- **Published:** four 37 m towers, from Wikipedia's 2017 build ("four 37 metres (121 ft) light towers") and the
  Premier's release of 29 July 2017 ("New 37 metre-tall light towers").
- **Google Earth (December 2025):** three lamp heads. Each one shifts between tiles by parallax, so each is a tall
  tower:

  | Tower | Head position, model metres (east, north) | How it was fixed |
  | --- | --- | --- |
  | W | (-104.3, -32.1) | 4 tiles, 0.8 px; the head centre is 37.7 m up |
  | E | (90.0, 14.6) | within 2.2 m |
  | NW | (-56.0, 69.7) | within 1.8 m |

- The north-east roof corner holds a fourth bright structure, but it barely shifts between tiles, so it is low: a
  roof structure, not a tower.
- **Verdict:** three towers stand in Google Earth's imagery. The published four is the 2017 count; the fourth tower
  was most likely on the south-east side, where the new stands now are. That is a guess I have not confirmed.
- **Model before:** three towers, one at the north-east where Google Earth shows none, and the other two 19 m and
  21 m from the real ones. All three are now placed from Google Earth.
- **Height:** the mast top is 40.8 m, which puts the head centre at Google Earth's 37.7 m. The published 37 m is
  within 1 m of the head centre.

## Field size against published dimensions

- **Measured fence:** Google Earth's fence curve is 169.4 x 139.0 m.
- **Published playing field:**
  - 160 x 129 m (Wikipedia infobox)
  - 159 x 129 m (AFL.com.au venue page; Austadiums)
  - "the same dimensions as Etihad Stadium" (Premier's releases, 2017)
- **Implied:** the fence stands 4.7 to 5.2 m outside the boundary line all round.
- **In the game:** the field is the fit's ellipse less `GroundModels.FENCE`, which is 6 m for every ground. That
  gives 156.1 x 126.5 m.
- **Verdict:** FAIL by 3 to 4 m in length and 2.5 m in width, against a limit of 1 m. Two causes:
  - Mars's fence stands about 1 m closer to the boundary line than the shared 6 m allowance.
  - The ellipse runs 1.3 m short of the curve along the long axis.
- **Not changed here:** `FENCE` is shared by every ground and changes play, and balance is the director's to call.

## Seats

- The shared seat rule (`tools/grounds/seat_check.gd`) took out 383 seats: 382 for headroom and 1 for having no
  neighbour.
- About 280 of them are the new stands' top rows, which sit under the shell roofs' low ends. That is a model fault
  to re-read from the 2026 photos.
- About 100 are the west stand's back rows at its north end, under the corporate block.
- That leaves 9,759 seats, against about 10,100 real ones (5,127 in the old stands and 5,000 in the new).

## What these files are

- `fence_trace.json`: the traced fence points, as numbers.
- `fence_curve.json`: the fitted curve, read by `model/build.py`.

Neither holds any Google Earth imagery.
