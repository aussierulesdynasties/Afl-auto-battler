# Moorabbin Oval, 1990-1992: measurements (in progress)

Legacy mode plays 24 matches here, 1990-1992 (St Kilda's last seasons at the ground). Published size in
`data/grounds.json`: 159 x 128 m (source not recorded; field or fence not said).

## Imagery

Google Earth web historical imagery (`tools/grounds/legacy/ge_history.js`, `LAT=-37.93798 LON=145.04374 R=950`):
30 dates from 18 Nov 2000 to 18 Jan 2016 (`measure/dates.txt`). Nothing older than Nov 2000, eight years after the
last Legacy match here. Reference only.

What the frames show: Nov 2000 to Nov 2006, the ground with its long curved stand along the west and south-west and the
buildings and stand on the north-west; on 30 Jun 2009 the west and south-west stand is stripped to its frame, and by Feb 2010 it is gone, leaving
the north-west building and stand (as today). Whether the ground changed between 1992 and Nov 2000 cannot be told from these.

## Measured so far (2026-11-23)

| What | Result | How |
| --- | --- | --- |
| Scale | **0.2974 m a pixel, +-0.5 %** (no painted 50 m square) | Google Earth's lat/lon readout on nine turf points of a 3D view with the same window and range (0.2956 m a pixel) times the square-to-readout ratio found at Ikon Park and Whitten Oval (1.003-1.009) |
| Turf edge, 2000-2006 | polar Fourier curve, K = 10, 0.6 m rms on the median of 4 dates (18 Nov 2000, 6 Apr 2005, 4 Mar 2006, 11 Nov 2006); **172.0 m long (axis 59 deg, north-east to south-west) x 140.0 m wide**; single dates agree with the median to 0.6-1.5 m | each date registered to 18 Nov 2000 on 34-69 template matches (1.2-1.3 px rms, `whitten/measure/reg.py`), traced from an 8-point hand prior to the steepest drop in greenness (`whitten/measure/trace.py`), median per 0.5 deg (`marrara/measure/med.py`; `measure/turf_2000_2006_fit_px.json`: pixels of the 18 Nov 2000 frame) |
| Turf edge, 2009-2010 | 175.2 x 144.6 m on 3 dates (Jun 2009, Feb 2010 twice), 3-5 m larger; not checked whether the turf changed or the trace differs (the Jun 2009 frame has the stand's shadow on the turf) | same method |

The 2000-2006 turf edge is bounded by a thin dark line all round (the fence and its shadow), with a 10-15 m apron
between it and the west stand. It is 13 m longer and 12 m wider than the published 159 x 128 m, about what a boundary
line some 6 m inside the fence gives, but the aerials show no boundary line to check that.

Bearings are degrees counter-clockwise from east round the field centre (0 east, 90 north).

## Not done yet

- Heights of the north-west stand and building (still standing) from Google Earth 3D: running.
- The west and south-west stand (gone by 2009): the Nov 2000 frame is a morning one (its shadow falls west onto the
  road outside); a height from that shadow needs the sun's azimuth from a pole or mast in the same frame. The 30 Jun 2009 frame
  has the stripped stand's shadow on the turf, which may give the frame's height the way Subiaco's roof was measured. Photos from
  1990-1992 are needed for the stand's section and to confirm the 2000 fence was the 1992 one.
