# North Hobart Oval, 1991-92 exterior (Row 202 step 2b)

Copied from the Land Tasmania aerial 1182_185 (16 Feb 1992) and real photos. Textures are hand-made (procedural); photos are reference only.
Director rulings applied: stadium only; field left out (ground runs from the boundary fence out); goal and behind posts out;
no sponsor boards; no lettering (club sign is a blank panel); open 1992 Gorringe deck; plain white Ryde roof; benches kept; own fence kept; no nets.

Model: northhobart1992.glb (metres, z up in Blender, exported as glTF Y-up).

Rebuild (system Python with numpy, shapely 2.x, Pillow; Blender 5.2):
1. python textures.py && python textures2.py   -> tex/*.png, tex/sizes.json
2. python geo2.py                               -> geo2.json
3. bash chain.sh                                -> stills, .glb, 240 orbit frames, mp4
Blender modes: blender -b --factory-startup --python world2.py -- <this folder> <aerial|gor|tt|close|glb|mp4> <out> [scale]
Proof boards (boards.py) need the reference photos, which are not in the repo.
