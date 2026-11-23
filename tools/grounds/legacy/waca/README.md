# WACA Ground, 1990-2000 (football-size arena): measurements (in progress)

Legacy mode plays 55 matches here, 1990-2000. Facts and sources: [FACTS.md](FACTS.md).

## Imagery

Google Earth web historical imagery (`tools/grounds/legacy/ge_history.js`, `LAT=-31.9599 LON=115.8796 R=950`):
15 dates from 22 Sep 2000 to 28 Feb 2013. Only 22 Sep 2000 and 3 Mar 2001 show the arena before the 2002
cut; the winter frames of 2005-2008 have the six towers' shadows across the turf. Reference only, never committed.

## Measured so far (2026-11-23)

| What | Result | How |
| --- | --- | --- |
| Scale | **0.3071 m a pixel, +-0.4 %** (no painted 50 m square in any frame) | Google Earth's own lat/lon readout on nine turf points of a 3D view with the same window and range (0.3053 m a pixel), times the ratio of square-measured to readout scale at Ikon Park (1.009) and Whitten Oval (1.003): the two ratios differ by 0.6 %, hence the error |
| Arena turf edge, 3 Mar 2001 | polar Fourier curve, K = 10, 3.5 px (1.1 m) rms about the curve; **173.6 m long (axis 4.6 deg from east-west) x 134.9 m wide** | traced from an 8-point hand prior to the steepest drop in greenness (`measure/trace.py`), frame registered to 22 Sep 2000 (181 matches, 1.1 px rms, `measure/reg.py`); `measure/fence_2001_px.json`, `measure/fence_2001_fit_px.json` (pixels of the 22 Sep 2000 frame, centre in the json) |

## Not settled

- **Only one usable date.** The 22 Sep 2000 trace agrees with 3 Mar 2001 within 4 px on only 185 of 720 rays and
  is 2-3 m off in most sectors (it locks onto seating and mowing rings). So this edge is good to about 1-3 m.
- **Fence or turf edge.** No published length was found. The 2002 cut ("31 metres at the eastern and western
  boundaries") does not check out: on 7 Jul 2006 the new inner fence spans about 152 m east-west by eye (+-2 m),
  22 m less than the 2001 edge, not 31. Either the 1990s fence stood about 4-5 m beyond the turf edge traced here at
  each end, or the 31 m is counted differently. A period photo has to settle it before the model is built.
- **Heights.** The towers (70 m published) cast long shadows in the winter frames; the stands' heights need those
  shadows and period photos.
