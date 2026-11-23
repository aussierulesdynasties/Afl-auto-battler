# Victoria Park (Abbotsford), 1990-1999: measurements (in progress)

Legacy mode plays 45 matches here, 1990-1999. Published size: 160 x 130 m (afl.com.au), 161 x 128 m
(austadiums), both as quoted in `data/grounds.json`; neither says field or fence.

## Imagery

Google Earth web historical imagery (`tools/grounds/legacy/ge_history.js`, `LAT=-37.79808 LON=144.99651 R=950`):
15 dates from 7 Nov 2000 to 11 Nov 2006, all showing the ground as Collingwood left it in 1999. Reference only.

## Measured so far (2026-11-23)

| What | Result | How |
| --- | --- | --- |
| Scale | **0.3011 m a pixel, +-0.4 %** (no painted 50 m square) | Google Earth's lat/lon readout on eight turf points of a 3D view with the same window and range (0.2993 m a pixel) times the square-to-readout ratio found at Ikon Park and Whitten Oval (1.003-1.009) |
| Turf edge, 2000-2006 | polar Fourier curve, K = 10, 1.27 px (0.4 m) rms on the median of 11 dates; **176.2 m long (axis 8.6 deg south of east) x 142.6 m wide** | each date registered to 15 Nov 2000 on 32-96 template matches round the ground (1.1-1.3 px rms, `measure/reg.py`), traced from an 8-point hand prior to the steepest drop in greenness (`measure/trace.py`), median per 0.5 deg (`measure/tmed.json`, `measure/fence_fit_px.json`: pixels of the 15 Nov 2000 frame, centre in the json) |

## Not settled

- **Dates disagree** by 6-10 px (2-3 m, median spread per 30 deg sector) on single dates, so the median edge is good
  to about 1 m. On the east side the outer bank is grass too, and the edge found there is the darker line at the fence.
- **Size against the published one.** 176 x 143 m is 15 and 13 m more than 160-161 x 128-130; the published figure is
  probably the field inside the boundary line, which the aerials don't show. A period photo is needed for where the
  fence stood against the turf.
- **Stands and heights:** not measured; the stands and terraces need period photos (none fetched yet).
