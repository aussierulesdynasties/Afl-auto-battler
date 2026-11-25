# Mars Stadium surroundings

1. `fetch.py WORK` fetches OpenStreetMap, the Meta/WRI canopy height model and AWS terrain tiles (not committed).
2. `data.py WORK/osm WORK/chm.npy [esri_1m.png]` paints `assets/grounds/mars/surrounds.webp`, writes `trees.bin`
   and `buildings.json`. The optional mosaic is a reference only: each roof takes the nearest of ten real roofing
   colours; no imagery is copied into any file.
3. `build_bpy.py -- OUT WORK/dem` (pip bpy) raises the buildings with real roofs, the workshops chimney and the
   land to the ranges as `mars_part2.glb`.

Credits: map data (c) OpenStreetMap contributors, ODbL. Trees: Meta and World Resources Institute, High
Resolution Canopy Height Maps, CC BY 4.0. Terrain: AWS Terrain Tiles (Mapzen terrarium; SRTM and Geoscience
Australia sources).
