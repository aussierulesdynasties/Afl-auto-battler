# Manuka's shape, measured against Google Earth

Every ring of the ground (the fence, the terraces, the stands' fronts and backs, the roofs) is an exact offset along
the outward normal of one smooth curve: the boundary fence, a Fourier series in bearing about C
(`manuka.json` fence), fitted to the fence traced on a straight-down Google Earth shot. The stands' ends, roof edges,
the media centre's deck, the Bradman's vomitories, the red terraces and the scoreboard are traced on the same kind of
shot. Measuring and tracing only: no imagery is kept in the repository or baked into a texture.

## Taking a calibrated straight-down shot

1. Shoot Google Earth with heading 0 and tilt 0 over the ground, e.g.
   `https://earth.google.com/web/@-35.3181447,149.1345861,560a,700d,35y,0h,0t,0r`, cropped to 1280 x 720 (the crop's
   vertical field of view is 25.58 degrees: cb53de5).
2. Hover the mouse over a few points of the shot and read Google Earth's status bar (camera altitude, the point's
   latitude, longitude and elevation): tesseract reads it.
3. The camera's height over the turf is the status bar's camera altitude less the turf's elevation (Manuka's turf
   is 569 m). Solve the point under the camera and the metres per pixel from the hovered points, allowing for each
   point's own height (a point h m up shows (H - h) / H as far from the centre).

2026-11-22: range 700 m gave camera 1,260 m, so 691 m over the turf, 0.4355 m a pixel, the point under the camera
(4.58, -4.91) in the model's frame (residuals under 0.7 m, the status bar's own rounding); range 500 m gave 491 m,
0.309 m a pixel, (4.44, -4.97).

## The checks (pass or fail, limits first)

- `measure.py --ge SHOT CAM_X CAM_Y CAM_H`: the fence traced on the shot against the model's fence.
  Limits: rms 0.5 m, max 1.5 m.
- `roofcheck.py SHOT CAM_X CAM_Y CAM_H RES`: every roof's front and back edge bearing by bearing, and each end row by
  row, lean taken out at each roof's height. Limits: median |error| 0.5 m, 90th percentile 1.5 m, each end's median
  1 m.
- `outline.py SHOT CAM_X CAM_Y CAM_H`: the model's own roofs projected through the calibrated camera against the
  shot's strongest edges (catches anything roofcheck's list leaves out; it picks the strongest edge, so faint roof
  fronts over concourses read as misses).
- `trace.py`, `fit.py`: the fence trace and its fits; `matchspace.py`: model frame to the match's metres for
  `tools/visual/preinspect_look.gd`.
