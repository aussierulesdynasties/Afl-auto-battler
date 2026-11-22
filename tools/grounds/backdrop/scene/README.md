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

Map data (c) OpenStreetMap contributors, ODbL. Terrain: AWS Terrain Tiles. The Esri aerial is reference only:
nothing from it is drawn except a median colour for a roof or car park.

Fixes found in QA (2026-11-22): the terrain tiles carry single-cell spikes (a 300 m cone beside the WACA, up to
2.5 km at York Park), so `prep.py` gives any cell above or below all 8 neighbours by more than a cliff (25 m at
zoom 14, 60 m at zoom 12) their median; Barossa, Summit and Bruce paint untagged open land as paddock, not the
town verge's grey-green; an inland ground's sea plane drops below the land (`scene.py`).
