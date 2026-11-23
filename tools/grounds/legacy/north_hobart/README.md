# North Hobart Oval, 1991-1992: measurements (in progress)

Legacy mode plays 4 matches here (two in 1991, two in 1992). Published size in `data/grounds.json`: 150 x 105 m
(source not recorded; field or fence not said).

## Imagery

Google Earth web historical imagery (`tools/grounds/legacy/ge_history.js`, `LAT=-42.86785 LON=147.31618 R=950`):
25 dates from 14 Oct 2003 to 2 Mar 2016 (`measure/dates.txt`; 22 Mar 2005 repeats the 2003 image). Nothing older than
2003, eleven years after the last Legacy match here. The stands round the ground look the same in the six frames checked (2003, 2005, 2008, 2012, 2014); whether
any changed between 1992 and 2003 cannot be told from these. Reference only.

## Measured so far (2026-11-23)

| What | Result | How |
| --- | --- | --- |
| Scale | **0.2938 m a pixel, +-0.6 %** | Google Earth's lat/lon readout on five turf points of a 3D view with the same window and range (0.2920 m a pixel) times the square-to-readout ratio found at Ikon Park and Whitten Oval (1.003-1.009) |
| Centre square, 9 Sep 2012 | **45.3 m** a side at that scale (154.2 px, the four sides within 0.7 px) | each painted side fitted (0.2-0.4 px rms, `whitten/measure/sq2.py`). It is not the 50 m AFL square: at 50 m the scale would be 0.324 m a pixel, 11 % off the readout, which the readout method has never been off by (0.3-0.9 % at Ikon and Whitten). So the scale above comes from the readout, not from this square |
| Turf edge, 2003-2016 | polar Fourier curve, K = 10, 0.3 m rms on the median of 22 dates; **162.1 m long (axis 36 deg, north-east to south-west) x 120.0 m wide**; single dates scatter 0.9-1.6 m (median per 30 deg sector) about the median | each date registered to 14 Oct 2003 on 25-115 template matches (1.0-1.3 px rms; `measure/reg2.py` adds a coarse phase-correlation shift first, because later frames sit up to 120 px off), traced from an 8-point hand prior to the steepest drop in greenness (`whitten/measure/trace.py`), median per 0.5 deg (`marrara/measure/med.py`; `measure/turf_2003_2016_fit_px.json`: pixels of the 14 Oct 2003 frame) |

The turf edge is 12 m longer and 15 m wider than the published 150 x 105 m. The north end of the turf is shaded by
the stand in several frames; the median rides through that, but the fence line itself has not been traced yet.

Bearings are degrees counter-clockwise from east round the field centre (0 east, 90 north).

## Not done yet

- The fence line, and stand heights from Google Earth 3D (the stands round the ground still stand).
