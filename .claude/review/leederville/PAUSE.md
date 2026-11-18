# Leederville Oval exterior: PAUSED (2026-11-18 ~22:55 Melbourne), not ready for gate

Paused on the lead's account-switch order. The committed GLB, mp4, stills and boards in this folder are the OLD
proof set (a04d45043). They do not show the bank or gate work below. The new work is in build/ and wip/ only.

## Done since a04d45043 (in build/*.py, renders in wip/)
- Banks: sloped, heights measured off the photos (bank.py CTRL table). The ground rises to each terrace (east
  terrace, NW terrace, NW landing), with no trenches, pits or z-fights. Fence ring vertices are a fixed 0.75 m
  apart, so there are no long thin facets. Checks: wip/bank_*.png.
- Pedestrian gate: the one gate the photos show (April 2026 photos 07, 10-13 and the panorama), on the east fence
  at about 12 deg (panel 8). It has its own black posts, a hinged chain-mesh leaf 0.87 m wide with rounded top
  corners, hinges and a latch, and a blank yellow sign on the panel to its south (bank side). Checks:
  wip/gate_*.png; the joins meet.
  - The 12 deg position is an estimate from the photo 10/11 bearings, +-5 deg. The drones show the fence during
    the works and are too coarse to see the gate.

## Open faults
1. Outer faces still plain render: the Members Stand (x=-97.5 west, y=51.5 north, y=25.5 south) and the south
   building (west face (-98.2,-31.6)->(-96.1,-66.0); south face (-96.1,-66.0)->(-68.6,-65.2)).
   What the photos show:
   - South building west face, from grandstand_April_2026_01 (camera NW, looking SE; far right behind the red
     brick hip-roof wing): cream render in two steps, groups of tall narrow vertical windows, a galvanised roof
     railing, and a cage ladder at the NW corner.
   - South building south face, from cov/base1.jpg (aerial from the south, low resolution): cream wall, a
     horizontal ledge about mid-height, a row of small dark windows below it, and a downpipe.
   - Members Stand outer faces: no photo found yet. Carry on its own materials and banding (render_beige, the
     dark glass band, the narrow upper windows of ms_tower).
2. The grandstand's SOUTH tower is missing. grandstand_April_2026_01 shows a second, smaller brick tower with a
   cap at the south end, and base1.jpg shows a tower at the grandstand's south-west corner. The model has only
   gs_tower (north). This was not in the reopen list; it is a fault seen in passing.
3. New gate rule (director "Yes, every ground"): a straight-down render overlaid on a straight-down satellite
   image (Esri/Google) at the same scale and north. Roof edges, bowl edge, facade line and fence oval must sit
   on the photo. Plan shapes come from satellite/OSM only. Not done yet.
4. The proof set has not been re-rendered: run_all.sh (~25-45 min), proofs.py, lookboard.py, then copy into
   this folder.

## Exact next step
Model the south building's west-face windows, railing and ladder, and its south-face ledge and window row, in
build.py (hand-made textures: tex.py / tex_back.py). Then the Members Stand faces, then the satellite top-down
overlay. Then re-render, self-check every frame, commit, push, and report to the secretary.

## Scratch (not in git)
C:/Users/DANTE/AppData/Local/Temp/claude/8e5f1971f882013a/57e018a2-7521-4d3a-8abf-3ad13c07ac13/scratchpad/lv/
- build.py, fence.py, bank.py, tex*.py, cam.py, cams/, run_all.sh, proofs.py, lookboard.py
- Backups: build_prebank.py, fence_prebank.py, bank_radial.py, fence_prering.py
- Blender: always use absolute output paths (relative paths land in C:/out).

## Reference photos (scratch ph/)
- Leederville_Oval_grandstand_April_2026_01-03.jpg
- cov/base1.jpg
- cov/250324_1.jpg (day drone)
- cov/250415_5.jpg (night drone)
- East_Perth_v_Swan_Districts_Leederville_Oval_April_2026_01-13.jpg
- Panorama_of_Leederville_Oval_April_2026.jpg
- au_*.jpg
