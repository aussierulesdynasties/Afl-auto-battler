# Marvel outline check (measured, not judged by eye)

These scripts measure the model's outline against Google Earth's top view. They follow the outline rule: one smooth curve fitted to a Google Earth trace, every ring an exact offset of it, and pass or fail measured in metres.

Inputs live outside the repo, because imagery is never committed:

- Google Earth's top view, captured with /tmp/claude-0/ref/ge.js from the `top` view in views.json, saved at /tmp/claude-0/ref/geA/ge_top.png.
- The cached OpenStreetMap tiles /tmp/marvel_surrounds_*.osm, which surrounds.py fetches.

Run them in this order:

1. `osmw.py`: writes osm_w.json, the OpenStreetMap water and pier polygons.
2. `calib.py`: fits the top view's scale, turn and shift to the harbour edge, and writes calib_top.json. On 2026-11-22 the median residual was 1.1 m. That residual is the floor on what can be measured.
3. `measure_strict.py`: projects the roof edges from parts2.json, with each point's height corrected for parallax, into the view. Along each edge's normal it takes the nearest strong edge within 6 m that is bright roof inside and at least 25 levels darker outside. It reports each segment's median, the share within 1 m and within 2 m, and the p90, then fits a circle to each end roof's trace.
4. `inner.py`: measures the roof opening's inner edges.
5. `offsets.py`: checks how far each ring is from an exact offset of the wall curve.

**Pass rule:** a segment's median is 1.0 m or less, and at least 90% of its samples are within 2 m.

## Angled 3D check (2026-11-22)

Google Earth's status bar gives the latitude, longitude and height of the mesh point under the mouse. So any
angled view becomes a 3D measuring tool with no camera fit: `pick.js` hovers a grid of screen points and
saves each status-bar crop, `ocr.py` reads them (tesseract), `anal.py` turns them into the model frame
(`surrounds.xy`, height minus 2.6 m: Google Earth's field is 8 m above sea level, the model's 5.4) and measures
each point's distance to the model, and `detail.py`/`bowl.py` split the results by height and section.
Heights come in 1 m steps; positions to about 0.3 m. Nothing from Google Earth is committed.
