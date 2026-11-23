# Football Park, 2001-2013 layout: measurements (rebuild in progress)

Legacy mode plays 438 matches at Football Park. The rebuild is the bowl from the Northern Grandstand (2001) to the
last AFL match (2013). Facts and sources: [FACTS.md](FACTS.md). Earlier by-eye drafts (branch
`claude/football-park-exterior`) are replaced, not patched.

## Imagery

Google Earth web historical imagery, captured headless with `tools/grounds/legacy/ge_history.js`
(`LAT=-34.87993 LON=138.49551 R=950`, 2000x2000 viewport): 62 dates from 15 Aug 2001 to 22 Mar 2018
(demolished by 17 Nov 2018). Reference only: the captures stay out of the repo and out of every texture.
Best frames: 20 Feb 2013 (centre square painted, edge lit all round), 31 Dec 2014 (sharp aerial, afternoon sun
from the west: the only frame where the west stand shades the turf), 26 Nov 2014 (all AFL lines painted).

## Measured so far (2026-11-23)

| What | Result | How |
| --- | --- | --- |
| Scale | 0.3062 m a pixel | the painted 50 m centre square: 163.2 and 163.3 px on 20 Feb 2013, 163.0 and 163.7 px on 26 Nov 2014 |
| Field length | goal line to goal line 543.5 px = 166.4 m on both dates (published 165 m: the two agree within 0.9%, which bounds the scale error) | painted goal lines |
| Fence line | polar Fourier curve, K = 10, about the centre square's centre: **0.57 m rms** per traced point (623 of 624 kept); fence to fence **144.2 x 181.9 m** | turf edge as the half-way crossing of greenness along each 0.5 deg ray (`measure/turf2.py`, `measure/refine2.py`, `measure/fourier.py`), 20 Feb 2013; `measure/fence_fit.json` |
| Fence, second frame | 3 Mar 2013 (registered on the painted lines, `measure/linereg.py`): 0.38 m rms per point, its curve within **0.34 m rms** (0.76 m worst) of the 20 Feb curve once the registration terms (shift, scale) are taken out; same 144.2 m width | |
| Fence against published | width 144.2 m against 145 m. Length 181.9 m against a published 177 m: the painted goal lines sit 7.7-7.8 m inside the fence at both ends on both dates (frame 21 and 32), so the published 177 m (6 m run-off) does not match the ground as painted from 2013 | |

Bearings are degrees counter-clockwise from east round the centre square's centre, pixel (996.4, 986.7) of the
20 Feb 2013 capture. The goals run north-south.

## Tried and rejected

- **Averaging the fence over many dates** registered on the ground outside the stadium (SIFT): the surroundings
  changed too much between 2001 and 2014 (5 to 30 good matches a frame), so the registrations were off by metres.
  Only frames with the painted lines register reliably, and only 20 Feb and 3 Mar 2013 have the edge lit all round.
