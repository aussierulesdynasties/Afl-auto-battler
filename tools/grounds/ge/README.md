# Google Earth compare: the shared tool for every ground

This is one tool for checking any ground against Google Earth from the same camera. It replaces the
per-ground copies of `ge_compare.py` and `ge_shoot.js` (Adelaide, Bellerive, GMHBA, Cazaly's, ENGIE, York Park,
Norwood). Delete your copy when you next touch your ground's QA.

| File | What it does |
|---|---|
| `ge_compare.py plan / level / sheet` | Google Earth URLs and our matching cameras, GE's turf height, side-by-side sheets |
| `ge_shoot.js` | Google Earth shots in headless Chromium: a fresh page per view, plus the status-bar camera readout |
| `ge_compare.py register` | Straight-down view: how far our model must move (east/north, m) and turn (deg) to sit on GE. Passes at 1 m and 0.5 deg |
| `ge_compare.py outline` | Straight-down view: distance from each of our edges to the nearest GE edge, overall and in 30-degree sectors, plus an overlay picture |
| `ge_solve.py` | An oblique shot's true camera, solved from the painted field lines (needs the ground's boundary file) |
| `grounds.json` | Per ground: the model origin's lat/lon, GE's turf height and where each came from. The match fit is read from `GroundModels.FIT` |

## Rules this encodes (measured 2026-11-22)

- **Field of view.** The URL's `35y` is the vertical field of view of the whole 1000 px window. The 720-row
  crop is 25.58 degrees. The old copies used 23.5, which drew ours 8% too close.
- **Turf height.** Use Google Earth's own turf height from the status bar (`ge_shoot.js --level`), not a map's.
- **Low cameras.** GE lifts them 15-30 m, so `plan` reads where each one really went.
- **Straight down.** `plan` aims 0.1 m north of the spot (0.01 deg off vertical), so the picture comes out
  north-up. The old 3-degree nudge tilted every roof 5% of its height off its footprint.
- **Line up before measuring.** Run `register`. A model 20-40 m off its starting guess makes a narrow search lock
  onto the wrong match: this happened to 9 grounds in the shape audit. A turn over 2 degrees means the
  model, or its surroundings, isn't north-up, or the origin is wrong. That is the Traeger fault: surroundings
  built north-up around a stadium built in an oval-aligned frame came out 25 degrees and 10 m off.
- **Leaning photos.** Where GE has no 3D mesh, tall things lean 5-7 m off their footprints (Barossa). Trace
  ground-level lines only.
- **Colour.** Judge it only on a PC GPU render. Cloud lavapipe never sunlights StandardMaterial3D.
- **Numbers, not eyes.** `outline` is lenient over seat rows and rooftops, because a wrong line can land near
  some edge. Quote its numbers with the overlay it writes.

## Field-line camera solve: limits

`ge_solve.py` is ported from Cazaly's (PR #2034). Google Earth keeps the asked spot and heading and only lifts
the camera, so the solve may only move the spot 15 m and turn 2 degrees. It trusts a result only when both 50 m
arcs and the centre square are in view and the result lands inside those bounds. Close obliques that miss the
far arc solve to wrong poses.

It has not yet been validated on a real traced boundary. On a test at Cazaly's with the old ellipse boundary,
all four views ended pressed against the bounds and were marked untrusted. Check it on your ground's
`/mnt/project-files/boundaries/<slug>.json` before relying on it.
