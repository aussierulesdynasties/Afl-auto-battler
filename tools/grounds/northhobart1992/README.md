# North Hobart Oval, 1991-92 exterior (Row 202 step 2b)

Copied from the Land Tasmania aerial 1182_185 (16 Feb 1992) and real photos. Textures are hand-made (procedural); photos are reference only.
Director rulings applied: stadium only; field left out (ground runs from the boundary fence out); goal and behind posts out;
no sponsor boards; the ground's own signs on, hand-made from the photo ("Yes, ground's own signs", 2026-11-19): the club sign and the HORRIE GORRINGE STAND board; no crowd (empty seats); open 1992 Gorringe deck; plain white Ryde roof; benches kept; own fence kept; no nets.

Model: northhobart1992.glb (metres, z up in Blender, exported as glTF Y-up).

1992 rework (2026-11-19, "Match the 1992 photo"): fence moved to the line on aerial 1182_185 (fence_offsets_1992.json, fence1992.py;
old fence in world_pre1992fence.json); the strip the fence gave up is ground (apron); NE scoreboard top 10 m (geo2.py); hand-painted detail pass (textures3.py);
Gorringe clock frame and name board (signs1992.py).

Rebuild (system Python with numpy, shapely 2.x, Pillow; Blender 5.2): bash chain2.sh
  textures.py, textures2.py, textures3.py, signs1992.py (in that order; not idempotent), fence1992.py, geo2.py, then Blender: .glb, stills, turntable mp4.
Proofs: python proofs1992.py (photo boards; photo panels come from .claude/review/northhobart/boards), topdown.py ref_full_1992.png <aerial render> 1.0 <out>,
texboard1992.py (texture board with stddev).
Blender modes: blender -b --factory-startup --python world2.py -- <this folder> <aerial|top|gor|tt|close|sb|glb|mp4> <out> [scale]
