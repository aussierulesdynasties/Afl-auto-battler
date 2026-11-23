# Whitten Oval (Western Oval), 1990-1997 ground: measurements (in progress)

Legacy mode plays 84 matches here, 1990-1997. Facts and sources: [FACTS.md](FACTS.md).

## Imagery

Google Earth web historical imagery (`tools/grounds/legacy/ge_history.js`, `LAT=-37.80033 LON=144.88708 R=950`):
50 dates from 23 Mar 2000 to 3 Nov 2015. The frames up to 21 Nov 2005 show the ground as it was left in 1997
(purple seating on the west side, the long red-roofed structure along the east, the open south end); it is rebuilt
from about 2007. Reference only, never committed.

## Measured so far (2026-11-23)

| What | Result | How |
| --- | --- | --- |
| Scale | 0.2994 m a pixel (sides 166.7-167.5 px) | the painted 50 m centre square, 31 Jan 2014 (`measure/sq2.py`); that frame and 15 Nov 2000 agree in scale to 0.02 % on features round the ground |
| Turf edge, 2000-2005 | polar Fourier curve, K = 10, 0.6 m rms on the median of ten dates; **188.9 m long (axis 81 deg, close to north-south) x 138.5 m wide** | each of 10 dates (Mar 2000 to Nov 2005) registered to 15 Nov 2000 on 55-117 template matches round the ground (1.1-1.3 px rms, `measure/reg.py`), then traced from an 8-point hand prior to the steepest drop in greenness (`measure/trace.py`); per 0.5 deg the median of the 10 (`measure/tmed.json`, `measure/fence_fit_px.json`, pixels of the 15 Nov 2000 frame, centre in the json) |

## Not settled

- **Dates disagree.** A single date's edge sits 2-3.5 m (median spread per 30 deg sector) from the others: the
  2000-2005 frames are soft. The median of ten is better, but this edge is good to about 1 m, not to the half metre
  of the other grounds.
- **Turf edge or fence.** 189 m long is more than today's published 160 x 130 m (undated, and the field was later
  re-sized). Whether the 1990s fence sat on this turf edge needs a period photo.
- **Stands and heights.** Not measured. The 1990s stands are gone. In the 2000-2005 frames their shadows fall
  west, away from the turf, onto ground behind them, and are 10-15 px (3-4.5 m) long on soft images with no tall
  pole to fix the sun's direction or the photo's lean, so a shadow height would carry 1-2 m of error. Heights wait for
  period photos (requested). The stands' plan outlines are clear in the 1 Feb 2001 frame and will be traced for the model.
