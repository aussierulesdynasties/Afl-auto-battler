# SCG base model build (row 202 2b, 2026-11-19/20)

The scripts that built the SCG's base model (`assets/grounds/scg/scg_part1/2.glb`, PR #1909), brought over from
branch `claude/inspiring-heisenberg-a3f33c` so the source is not lost when that branch is retired. `run.sh` is the
full rebuild: `texgen.py` -> `export2.py` (mesh from `scg_mesh.json`) -> Blender `build_hand.py` -> glb, then the
comparison board.

Later rounds edit the shipped glbs on top of this build (`tools/grounds/scg/`: `messenger_roof.py`, `tiers.py`,
`join.py`, `boxes.py`, `stand_roofs.py`, ...). Re-running this build alone would undo them.

Not included: the reference photos the cameras were fitted to (`refs*/`: stadium and press photos, licences
unknown) and rendered maps/boards; the scripts still name them. `osm/` is OpenStreetMap data (ODbL,
(c) OpenStreetMap contributors). `fonts/` is Liberation Sans Bold (SIL OFL 1.1, `fonts/LICENSE`).
