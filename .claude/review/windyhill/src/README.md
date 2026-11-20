# Windy Hill (1990-91) model source

- `go.sh`: Blender 5.2 headless. `build.py` -> `wh.glb`, `rcam.py` -> render from the 1984 photo's camera, `cmp.py` -> overlay on `bb1984.jpg`, `orbit.py` -> stills.
- `texgen.py` writes the hand-made textures to `tex/` (run it first; `tex/` is not committed, it is regenerated).
- Inputs: `world.json`, `geo.json` (OSM outlines), `cam84.json` (camera fitted to the 1984 aerial), `cols.json` (1992 hues), `trim.json` (only for `WH_APRON=trim`).
- `crops.py` -> per-part crop board. `tt/turntable.gd` -> Godot turntable frames.
- Scripts expect to sit in one folder (D = that folder); edit the path in `go.sh` before running.
- Director rulings applied: field out, posts out, no lettering, bare white fence (no boards), no nets, base filled with plain paving.
