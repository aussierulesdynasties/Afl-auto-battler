# Waverley Park, 1990-1999 bowl: measurements (in progress)

Legacy mode plays 240 matches here, all 1990-1999. Facts and sources: [FACTS.md](FACTS.md).

## Imagery and its limit

Google Earth web historical imagery (`tools/grounds/legacy/ge_history.js`, `LAT=-37.92557 LON=145.18865 R=950`):
the oldest date is **6 Apr 2005**, two years after demolition began. No aerial of the standing bowl is in Google Earth.
On 6 Apr 2005 the members' stand still stands, the old oval's turf is still there and the bulldozed terraces show as
a ring of dark rows round it; by 4 Mar 2006 the new, smaller oval has been laid. Reference only, never committed.

## Measured so far (2026-11-23)

| What | Result | How |
| --- | --- | --- |
| Scale | 0.2791 m a pixel (sides of the square 178.6-179.6 px) | the painted 50 m centre square, 31 Jan 2014 (`measure/sq.py`); the 2005 frame matches the 2014 one to 0.4-0.7 % in scale on road features west and north of the ground, so its scale is good to about 0.7 % |
| Old oval, 6 Apr 2005 | turf edge as a polar Fourier curve, K = 10, 1.9 px (0.5 m) rms on 673 of 720 rays; **188 m long (axis 29 deg north of east, NE-SW) x 163 m wide** | 8 points placed by eye on the light turf edge, then the strongest light-to-dark step within 25, 12 and 6 px of the smoothed curve (`measure/hand00.py`, `measure/oval_2005.json`, pixel frame of the 2005 capture) |

## Not settled

- **Which edge is the fence.** Round the 2005 turf runs a dark band about 5 m wide (with a thin dark line on its
  inner side in the north, which may be the old fence footing). The turf edge measures 188 x 163 m against the
  published 200 x 160; neither the turf edge nor the outside of the band (about 198 x 173 m) matches both numbers.
  A period photo has to settle where the fence stood. Until then the fence is not fixed.
- **The north-west.** The curve runs onto the members' stand's concrete apron there (about 3-5 m too far out).
- **Heights.** The members' stand still stands, so Google Earth's 3D mesh can give its heights (as at Ikon Park).
  The public stands, light towers and scoreboard come from period photos only; downloads of Commons photos are
  refused from the cloud at the moment.
