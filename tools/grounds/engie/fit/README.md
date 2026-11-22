# ENGIE outline fit and heights (2026-11-22)

Measures the stadium from Google Earth and writes the plan into `../model/engie.json`. The Google Earth
shots stay in a work folder (`ge/`) and are never committed or baked into a texture.

1. Scale: two top-down shots (3000 m, 7y) 60 m apart. `cv2.phaseCorrelate` gives 0.364 m per pixel
   (0.363 and 0.365 from the north and south pairs). OSM's pitch outline turned out 4.5% too big against it.
2. `seg.py`, `trace.py`: the field mask and the registration offset against the model's origin.
3. `trace2.py`, `edges.py`: whiteness profiles along rays every 0.5 degrees, from three shots (centre, 60 m
   north and 60 m south). These give the roof front and back edges, with outliers over 2 m from a 5 degree
   running median rejected.
4. `fit.py 6`: one smooth curve (a 6-harmonic polar Fourier series about a fitted centre) is fitted to the
   sunlit field edge. The roof front and back are fitted as exact normal offsets of it (6.70 m and 32.61 m).
   Error against the trace: field edge 0.88 m rms, roof front 1.05 m rms, roof back 1.34 m rms. Gross
   mistraces over 8 m (points on pavilion roofs) are excluded and counted. The 1998 stands are under 1 m;
   the 2012 north and east stands are up to 3.6 m, because their edges run straighter than the curve.
5. `tojson.py`: writes fence, rf and rb as polar tables of those rings, plus the curve itself (`outline`).
6. `stereo.py`, `heights.py`: two top-down stereo pairs (1500 m, 15y, 150 m baselines east-west and
   north-south), StereoSGBM, and heights over the field from the disparity. Roof sheet: old segments 21.5 m at
   the front and 18.3 m at the back at their ends, arching 3.2 m mid-span. North and east (2012) roofs: 18 to
   21.5 m at the front, 18 m at the back. The two pairs agree within about 1 m. Seats under the roofs cannot
   be measured this way.
7. `gap.py`: field edge to the first seats, 5 to 6 m (8.75 m at the open end).
8. `obov.py H 0 OUT`: projects the model's rings (field edge, stand front, tier lines, roof edges, wall base)
   onto the matched oblique shots `ob_H.png` (1200 m, 15y, tilt 50) for checking by eye.

Limits: the scale holds to about 1%, because the field's height under Google Earth's target point is not
known to better than about 25 m at 3000 m. Tier lines under the roofs are too blurred in Google Earth's mesh
to measure better than about 2 m.
