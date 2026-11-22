# TIO Traeger Park: the background scene

Everything round the stadium model (`assets/grounds/traeger/traeger.glb`), out to the horizon, built from open
data and measured off Google Earth. Model metres: x east, y up, z south, origin at the OSM pitch's centre
(lat -23.7097309, lon 133.8759053), the field's level at 0.

| Part | File | Script | What it is |
|---|---|---|---|
| near | `traeger_backdrop_part1.glb` | `near.py` | The ground out to 1,300 m (surfaces traced from Google Earth and painted fresh), every building (OSM, and Microsoft's footprints where OSM has none), every gum |
| far | `traeger_backdrop_part2.glb` | `far.py` | The land from 1,300 m to 24 km: real terrain (the MacDonnell Ranges, Heavitree Gap, Mt Gillen), coloured from Sentinel-2 |

## Build

```
export TRAEGER_CACHE=/tmp/traeger_cache          # DEM tiles, OSM tiles, Sentinel-2 bands, canopy heights
python3 texgen.py && python3 leaves.py tex/leaves.png
python3 far.py  ../../../../assets/grounds/traeger/traeger_backdrop_part2.glb
python3 near.py ../../../../assets/grounds/traeger/traeger_backdrop_part1.glb MOSAIC.png
```

`MOSAIC.png` is Google Earth's straight-down mosaic (`qa/`: `ge_nadir.js` shoots `qa/nadir.json`'s 35 views from
800 m up with its labels and 3D buildings off, so its flat aerial imagery; `mosaic.py` joins them at 0.5 m a
pixel). It is a measuring reference: it stays out of the repo, and
no pixel of it reaches the game. What is read off it:

- **Surfaces** (`surface.py`): every pixel sorted into 22 surface classes by colour, the canopies, shade and
  roofs taken out, the edges tidied, then each class painted in its own colour and grain.
- **Gums** (`canopy.py`): every canopy's place and spread, the height from
  Meta and WRI's canopy height map.
- **Roof colours** (`canopy.py`): each roof's median colour.
- **The colour grade** (`grade.py`, fitted by `qa/grade_fit.py`): Sentinel-2 matched to Google Earth on open land.

Without a mosaic, `near.py` paints OSM areas over Sentinel-2's colour and stands no trees.

## Pieces

- `glb.py`: a small glTF writer (vertex colours are given as sRGB and written linear).
- `geo.py`: the model frame, Terrarium DEM, Sentinel-2 bands, OSM tiles, canopy heights.
- `bldg.py`: buildings from footprints: hipped roofs over rectangles, flat roofs with parapets, carports;
  walls with real window openings (reveals, recessed glass, mullion) within 420 m.
- `trees.py`, `leaves.py`: gums with a ghost-gum or red-gum trunk, limbs and crossed leaf-spray cards.
- `texgen.py`: brick, render and corrugated iron tiles (greyscale; each building's colour tints them).

## Sources and credits

- Map data (c) OpenStreetMap contributors, ODbL.
- Building footprints OpenStreetMap lacks: Microsoft Global ML Building Footprints, ODbL.
- Contains modified Copernicus Sentinel data 2025 (scene S2B_53KLP_20251029).
- Terrain: Terrarium tiles (AWS Open Data, Mapzen; SRTM and others).
- Tree heights: Meta and World Resources Institute, High Resolution Canopy Height Maps (2024), CC BY 4.0.
- Google Earth: measuring only (positions, colours, surface outlines); no imagery is committed or shipped.
