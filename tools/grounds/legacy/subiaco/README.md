# Subiaco Oval, 2000-2017 layout: measurements (rebuild in progress)

Legacy mode plays 505 matches at Subiaco, 390 of them from 2000 on, so the rebuild is the bowl as it stood
from the City End stands (2000) to the last AFL match (2017). Facts and sources: [FACTS.md](FACTS.md).
The first draft in `tools/grounds/subiaco/` (by eye from photos) is replaced, not patched.

## Imagery

Google Earth web historical imagery, captured headless with `tools/grounds/legacy/ge_history.js`
(`LAT=-31.9445 LON=115.8303 R=950`, 2000x2000 viewport): 60 dates from 3 Mar 2001 to 30 Jun 2017.
Reference only: the captures stay out of the repo and out of every texture.

Best frames: 18 May 2008 (sharp near-vertical aerial, winter sun from the north, AFL lines painted),
30 Dec 2011 (summer, the north stand's seats in sun), 30 Apr 2016 (satellite, strong lean, AFL lines).

## Measured so far (2026-11-23)

| What | Result | How |
| --- | --- | --- |
| Scale | 0.2945 m a pixel | the painted 50 m centre square (170 px both ways) and the 50 m arcs (170 px from the goal line), 18 May 2008; Google Earth's own camera height gives 0.2943 |
| Fence line | polar Fourier curve, K = 10, **0.19 m rms** (621 of 687 points kept), 189.8 x 131.9 m, long axis 1.65 deg south of east | turf edge traced on 30 Dec 2011 (0-138 and 215-360 deg) and 18 May 2008 (155-215 deg), where each is in sun; `turf2.py`, `fourier.py`; published fence to fence 191 x 132 (Wikipedia) |
| The draft's fence | 1.5 m rms off the traced fence after the best shift and turn (1.1, 4.1 m, -1.0 deg), up to 3.2 m; worst 30-60 and 120-150 deg (2.6-2.7 m too far out) | `draft_model_fence.json` against `fence_fit.json` |
| Sun, 18 May 2008 | azimuth 7.0 deg (both north towers' shaft shadows on the turf), elevation 38.1 deg (date and azimuth, `sun.py`) | |
| Photo lean, 18 May 2008 | a point 1 m up shows 0.032 m east and 0.013 m north of its footprint (both north towers agree within 0.01 m/m) | each tower's head against its head's shadow on the turf, 65 m towers (heritage record) |
| North roof front edge | 16.3-19.7 m above the turf, 15 points from x = 700 to 1240 px, rising gently to the east | its shadow on the turf, 18 May 2008 (`nshadow.py`): height = shadow offset / 1.292 |

| South roof front | **18.5 m** above the turf (18.2-18.8 m as the rugby posts' assumed try line moves 47-53 m); fascia 17.6 m, glass boxes 14.0-16.9 m | camera of `Subiaco_Oval.jpg` (Commons, CC BY-SA 3.0, reference only) solved on the near fence, the SW tower (65 m) and the rugby posts, with lens distortion: 1-5 px residuals; camera 15.7 m behind the north fence, 5.3 m up; ray met with the roof front's plane from the 2008 aerial (`measure/photo`) |

Bearings are degrees counter-clockwise from east round the field centre at pixel (941, 1021) of the captures.

## Tried and rejected

- **Height from satellite parallax** (2008 against six 2013-2017 satellite frames, each registered to 2008 on the
  painted field lines, then matched along the lean direction): rejected. Along the north roof, where the shadow
  heights are known, the parallax per metre changes threefold from west to east in the 2016 frame and disagrees
  between frames. The matches lock onto shadow edges, which move with the sun between dates. Heights now come from
  period photos (camera solved on field lines and the 65 m towers) and seat-row counts.
