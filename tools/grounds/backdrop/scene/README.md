# Building a ground's background scene from OpenStreetMap (row 202 2b)

The scene pipeline that built the first 11 grounds' surroundings (GMHBA, MCG, Traeger and the rest, on the
director's PC), made to run for any ground in the cloud. It built the 24 grounds that had none on 2026-11-22.

What is new here:

- `osm_fetch.py` gets the map from the OpenStreetMap main API in ~400 x 600 m tiles (Overpass does not answer
  from the cloud) and writes `osm.json` / `osm_parts.json` in the shape `prep.py` reads.
- Placement. The scene is built north-up round the model's own origin, so it has to know where that origin is
  on the real map and how the model is turned:
  - `align.py`: the real oval (an OSM AFL or cricket pitch of AFL size) against the model's fence (`GroundModels.FIT`).
  - `model_plan.py` + `register.py` / `register2.py`: the model's stands seen from above, turned and slid over
    the OSM building footprints until they overlap best; `register2.py` keeps the fence on the real oval.
  - `placements.json`: what was used for each ground and how it was decided. Most models are north-up already
    (turn under 1 degree); Ikon Park is turned 7.9 degrees and Barossa 19.3 (from the pitch).
- `mkspec2.py` writes `spec/<ground>.json` from the GMHBA template (neutral colours; no coast or far-horizon
  extras, which need data only the PC had). A turned model is fed to the scene turned onto the map
  (`rot_glb.py`); `reduce.py` turns the finished scene back by `BG_YAW`, so the backdrop lies in the model's frame.
- `run1.sh <ground>`: spec, terrain tiles, the reference aerial (colours of car parks and roofs only), footprint,
  `prep.py`, `bake_ground.py`, `scene.py`, then `reduce.py` (budget 800,000 triangles, 2 looks per kind).

Setup: `pip install bpy==5.2.4 scipy`; a working folder `$WORK` with `proto/` = this folder's scripts and
`spec/`, `proto/tex` = `.claude/review/gmhba_bg/pipeline/tex` with `tex_extra/` copied over it, `geo/final.json`
(= `placements.json`), `glb/<ground>.glb` (a model in parts joined with `join_parts.py`), and
`data/<ground>/osm.json` from `osm_fetch.py`. About 2 minutes a ground on 4 cores.

Map data (c) OpenStreetMap contributors, ODbL. Building heights: Overture Maps Foundation buildings (ODbL, from
OpenStreetMap and others). Terrain: AWS Terrain Tiles. Ground colour variation: Digital Earth Australia Sentinel-2
analysis-ready data, CC BY 4.0, contains modified Copernicus Sentinel data. The Esri aerial is reference only:
nothing from it is drawn except a median colour per roof, car park or mapped patch of ground, and where its trees are.

Real place (`BG_REAL=1 bash run1.sh <ground>`, 2026-11-22): the surroundings built as the real place, ground by
ground against Google Earth.
- `overture.py`, `overture_parts.py <ground> lat lon`: Overture building heights (and parts) to `$WORK/overture/`;
  `prep.py` takes a building's height from it when OpenStreetMap has none.
- `s2.py <ground> lat lon`: the median of ten clear footy-season Sentinel-2 scenes, 10 m, to `$WORK/s2/`.
- `prep.py`: every patch of soft ground bounded by roads, paths, buildings, mapped areas or a change of cover takes
  the median colour of the aerial's open ground inside it (no trees, roofs, pools or shade), so edges stay crisp;
  inside big patches Sentinel-2 adds the light and dark (a dry corner of a park reads dry). No random wear.
  Lots mapped as one outline but built as a tower on a podium are split (`real_lm.json` "split").
- `towers_real.py`: towers with a modelled floor slab every storey and a column every ~4.5 m, never painted windows.
- `real_lm.py` / `real_lm.json`: landmarks per ground (another ground's own model across the river, an arch bridge
  modelled from Google Earth).
- `scene.py`: near ground stands 2 m clear of the sea plane except on mapped water; at 0.5 m the river drew through
  low parks from a distance (the depth test lost).

Fixes found in QA (2026-11-22): the terrain tiles carry single-cell spikes (a 300 m cone beside the WACA, up to
2.5 km at York Park), so `prep.py` gives any cell above or below all 8 neighbours by more than a cliff (25 m at
zoom 14, 60 m at zoom 12) their median; Barossa, Summit and Bruce paint untagged open land as paddock, not the
town verge's grey-green; an inland ground's sea plane drops below the land (`scene.py`).
