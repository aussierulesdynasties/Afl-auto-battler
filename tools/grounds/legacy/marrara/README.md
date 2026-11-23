# Marrara (TIO Stadium, Darwin): measurements (in progress)

Legacy mode plays 32 matches here, one or two a season from 2004 to 2026. The ground still stands, so heights can
come from Google Earth's 3D mesh (as at Ikon Park), not only from shadows and photos.

## Imagery

Google Earth web historical imagery (`tools/grounds/legacy/ge_history.js`, `LAT=-12.39915 LON=130.88732 R=950`):
30 dates from 31 Aug 2005 to 12 Oct 2014 (`measure/dates.txt`), 30 from Jun 2016 to Jun 2018 and 45 from May 2017 to
17 Sep 2026 (plus one Dec 1993 frame). Reference only.

What changes in them: four light towers by Dec 2007 (Aug 2005 shows fewer; not yet checked which); building work north of the ground in 2014
(the Michael Long Learning and Leadership Centre, finished by the later frames). The west grandstand and the ring
look the same throughout.

## Measured so far (2026-11-23)

| What | Result | How |
| --- | --- | --- |
| Scale | **0.2931 m a pixel, +-1 %** | the painted 50 m centre square on 31 Dec 2007, each side fitted to its painted line (0.14-0.17 px rms); the four sides read 169.1-172.2 px, hence the +-1 % |
| Field | **161.9 m goal line to goal line** on the centre line; the fence stands 8.1 m behind each goal line | the painted goal lines and goal squares on 31 Dec 2007 (the goal square reads 8.8 x 6.4 m against the 9 x 6.4 m it should be) |
| Fence | **179.2 m long (axis 0.4 deg off north) x 142.4 m wide**; polar Fourier curve K = 10, 0.12 m rms on the median of 13 dates (Aug 2005 to Oct 2013); single dates agree with the median to 0.1-0.3 m | each date registered to 31 Dec 2007 on 16-115 template matches round the ground (1.0-1.4 px rms); the turf edge traced first (`whitten/measure/trace.py`, median `measure/med.py`), then the fence wall itself found as the dark line of its shadow within 10 px inside to 3 px outside that edge (`measure/fence.py`, median and fit `measure/fmed.py`, curve `measure/fence_pre14.json`: pixels of the 31 Dec 2007 frame) |
| Fence, 2014 frames | the same within 0.1-0.4 m on the north, east and south; 1.1-1.6 m further in on the west (bearings 150-210) | 12 dates Feb-Oct 2014 (`measure/fence_14.json`). In these frames the grandstand's shadow lies along the west fence and the dark line found there is likely the shadow's edge, not a moved fence. The 2016-2017 frames (below) do not show it. |
| Fence, 2016-2017 | within 0.6 m of the 2005-2013 curve all round (west -0.2 to -0.6 m); 178.5 x 141.8 m | 18 dates Jun 2016 to Dec 2017 with 16 or more template matches to 2007 (`measure/fence_1617.json`) |
| Fence, 2018-2026 | within 0.9 m from bearing 0 to 285 deg; at 300-330 deg the median runs 1.1-2.3 m outside, on the bare dirt behind the fence where it casts no clear shadow line: checked by eye on 31 Dec 2007 and 17 Sep 2026, the fence line sits at the 2005-2013 curve on both | 10 of 31 dates register well enough (the surroundings changed); no sign the fence moved from 2005 to 2026 |

The published size in `data/grounds.json` (175 x 135 m, source not recorded) is 4 and 7 m less than the fence; the
field markings inside the fence were not traced (only the goal lines).

Bearings are degrees counter-clockwise from east round the field centre (0 east, 90 north).

## Not done yet

- Stand, roof, light tower and building heights from Google Earth 3D (running).
