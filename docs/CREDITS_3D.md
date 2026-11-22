# 3D view credits

Data and assets the 3D grounds are built from, by ground. Google Earth is used for measuring only (positions,
sizes, colours, outlines); no Google Earth or Esri imagery is committed to the repo or baked into a shipped texture.

## TIO Traeger Park (Alice Springs)

Stadium model (`assets/grounds/traeger/traeger.glb`, built by `tools/grounds/traeger`): modelled by hand from
measurements; every texture is generated in code (`texgen.py`, `texclub.py`), no photo pixels.

Surroundings (`traeger_backdrop_part1.glb`, `traeger_backdrop_part2.glb`, built by `tools/grounds/traeger/scene`):

- Map data (c) OpenStreetMap contributors, ODbL.
- Building footprints OpenStreetMap lacks: Microsoft Global ML Building Footprints, ODbL.
- Contains modified Copernicus Sentinel data 2025 (scene S2B_53KLP_20251029).
- Terrain: Terrarium elevation tiles (AWS Open Data, Mapzen; SRTM and other sources).
- Tree heights: Meta and World Resources Institute, High Resolution Canopy Height Maps (2024), CC BY 4.0.
- Ground dimensions: ABC (2022), as recorded in `data/grounds.json`.
