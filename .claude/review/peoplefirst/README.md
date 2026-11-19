# People First Stadium (Carrara) exterior, row 202 step 2b

Ready for gate (build r33, 2026-11-20). No open faults.

## Files
- model/peoplefirst.glb: the game model. model/peoplefirst.blend: its Blender source.
- build/: to rebuild, run this from build/ (scripts/ holds every measuring tool):
  `GEO=geo_n.json SATRIBS=1 FARRIBS=farribs_A.json FARVR=farvr.json FARDZ=3 LOBE_FAR=2.2 FARPOW=2.5 blender -b -P build5.py -- out.glb render.png`
- handtex.py paints every texture by hand into htex/. No photo pixels.
- gate/: the proof set.
  - full_board.jpg: photo, render and 50% overlay.
  - parts_board.jpg and part_*.png.
  - turn_*.png and turn_board.jpg: turntable.
  - facade_closeup*.png.
  - near_wall*.png: near-side wall beside the photo, same camera.
  - topdown_overlay.png, topdown_tiles.png and topdown_valleys.txt: straight-down render on the satellite.
  - texboard.jpg: each hand-made texture beside its photo crop.
  - ribstrip.png and ribsat.png: far roof ribs, photo and satellite.
  - seats_empty.png: seating close-up, empty seats, no crowd.
  - sign.png and signcmp.png: the People First Stadium sign.
  - scoreboard_9m.png: scoreboard placed from the satellite.
- reference/: photo_clean.png (oblique photo; camera build/cam.json), sat.png, satgrid_osm.png. Reference only.

## Director rulings applied
- "Leave field out", "Posts out", "C: no boards", "C: no lettering". Own fence kept. No goal nets.
- No crowd in the model (2026-11-19). Stadium only, no surroundings.
- Plan shape from the satellite. Exception: the near roof edge follows the photo's yellow edge, by the director's
  answer "1: follow photo". It is smoothed on 126-236 deg, and on 163-186 deg it sits 4-9 m outside the satellite edge.
- Near-side wall copied from the photo (lead, 2026-11-20). From the roof down, the wall has:
  - a dark band;
  - the red board, 15.0-18.4 m, from 130 to 176.6 deg (navy beyond);
  - grey;
  - a light concrete base on the podium deck.
- The roof edge drops on short vertical yellow posts (6.6 m) from 126 to 199 deg (photo x 400-1100).
- East of 199 deg the branching yellow trees and trusses stay as they were.
