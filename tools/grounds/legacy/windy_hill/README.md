# Windy Hill (Essendon), 1990-1991: measurements (in progress)

Legacy mode plays 15 matches here, 1990-1991 (Essendon's last home seasons at the ground). Published size in
`data/grounds.json`: 159 x 130 m (source not recorded; field or fence not said).

## Imagery

Google Earth web historical imagery (`tools/grounds/legacy/ge_history.js`, `LAT=-37.75208 LON=144.91963 R=950`):
25 dates from 15 Nov 2000 to 29 Jul 2013 (`measure/dates.txt`). Nothing older than Nov 2000, nine years after the
last Legacy match here, so the 1990-1991 ground is assumed to be the 2000 one where the frames cannot say otherwise.
Reference only.

## Measured so far (2026-11-23)

| What | Result | How |
| --- | --- | --- |
| Scale | **0.2912 m a pixel, +-0.5 %** (no painted 50 m square) | Google Earth's lat/lon readout on nine turf points of a 3D view with the same window and range (0.2895 m a pixel) times the square-to-readout ratio found at Ikon Park and Whitten Oval (1.003-1.009) |
| Turf edge, 2000-2006 | polar Fourier curve, K = 10, 0.5 m rms on the median of 14 dates (15 Nov 2000 to 11 Nov 2006); **166.8 m long (axis 6 deg off east-west, west end north) x 135.0 m wide**; single dates scatter 1-2 m about the median | each date registered to 15 Nov 2000 on 21-96 template matches (1.1-1.4 px rms, `whitten/measure/reg.py`; 3 dates with too few matches left out), traced from an 8-point hand prior to the steepest drop in greenness (`whitten/measure/trace.py`), median per 0.5 deg (`marrara/measure/med.py`; `measure/turf_2000_2006_fit_px.json`: pixels of the 15 Nov 2000 frame) |

The turf edge is 8 m longer and 5 m wider than the published 159 x 130 m. On the east and north-east the ground
outside the fence is dry grass, so the edge there is weaker; the fence's own line has not been traced separately yet.

Bearings are degrees counter-clockwise from east round the field centre (0 east, 90 north).

## Not done yet

- The fence line itself (as at Marrara), and heights of the west and north-west stands: Google Earth 3D where they
  still stand (to be checked against the 2000 frames), shadows or photos where they do not.
