# Jiangwan Stadium (Shanghai), 2017-2019: measurements (in progress)

Legacy mode plays 3 matches here (May 2017, May 2018, June 2019). The AFL oval was laid inside the athletics track
for each match. The model on main (`tools/grounds/jiangwan/model`, "first draft", heights estimated) sets its fence
as an ellipse 168 x 126 m from the published 160 x 136 m field plus a margin.

## Imagery

Google Earth web historical imagery (`ge_history.js`, `LAT=31.30843 LON=121.51110 R=950`): dates from 20 May 2000 to
13 May 2017 (`measure/dates.txt`; later dates not yet captured, the run was cut off). **13 May 2017, the day before the
first AFL match here, shows the oval laid out**, with temporary stands and marquees round it. Every other frame shows
the rectangular football pitch and the track. Reference only.

## Measured so far (2026-11-24)

| What | Result | How |
| --- | --- | --- |
| Scale | **0.3057 m a pixel, +-0.5 %** | Google Earth's lat/lon readout on nine points of a 3D view with the same window and range (0.3039 m a pixel) times the square-to-readout ratio from Ikon Park and Whitten Oval (1.003-1.009) |
| Oval turf edge, 13 May 2017 | **174.5 x 141.9 m** (K = 10 curve, 3.2 px rms on one date) | greenness trace from an 8-point ellipse prior (`whitten/measure/trace.py`; `measure/turf_2017-05-13_fit_px.json`) |
| Dark line round the oval | 170.0 x 147.5 m, but only 496 of 720 rays found it; on the west a second thin dark line runs about 5 m inside the turf edge | `marrara/measure/fence.py` (`measure/darkline_2017-05-13_fit_px.json`) |

**Not settled.** With one frame, and two candidate lines on the west, the fence is known only to about +-5 m: somewhere
near 170-175 m long and 142-148 m wide. The two fits do not even agree on the long axis (112 and 129 deg), because
the oval is nearly round. The model's 168 x 126 m is about 15-20 m narrower than any line found here. Photos or
broadcast frames of the 2017-2019 matches are needed to settle where the fence stood. The model's 160 x 136 m source
is not recorded.

Bearings are degrees counter-clockwise from east round the field centre (0 east, 90 north).

## Not done yet

- Capture the dates after May 2017 (May 2018 and June 2019 may also show the oval).
- Heights of the terraces and the temporary stands (Google Earth 3D or photos).
