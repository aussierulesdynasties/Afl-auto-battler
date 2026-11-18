# Optus Stadium: paused (2026-11-18, account switch), not ready for gate

## Done
- Three o2 gaps built: balustrade on the podium edge (mesh panels, solid sandstone parapet on the east as o2),
  lamp posts on the terrace every 7.2 m, dark railing on the plaza at the stair foot. Textures hand-made (railtex.py).
- Stair re-read from o2 on a pixel grid after the director rejected boards A and B: the flight now descends toward the
  lower LEFT in the camera-matched render (row angle 39-46 deg vs photo 44-46 deg), two light cross walkways,
  stepped side walls on both sides, deck joining the stair head to the podium.

## Open faults (all must be fixed before gate)
1. Bench rows too few, too wide, too light: photo has dense dark seat slats (period ~3 photo px), model ~8 px.
2. Lift-side stepped wall sits ~10 photo px too far left at the stair foot (photo corner near 1045,972).
3. Lift wrong: photo lift is a tall box, dark west face 1097..1114 x, 867..916 y; roof corners NW(1097,867)
   F(1120,864) E(1131,877) N(1114,881). Read: roof z ~11.3, footprint over the stair's top-left corner,
   stair-local a -0.09..0.16, t -0.05..0.23 (rises from below, benches wrap it). Model: LA0,LA1,LT0,LT1,LZ in build.py.
4. Grey deck covers the dark navy facade right of the stair top (photo 1150-1185 x, 905-940 y): trim deck at OT/XS.
5. Walkways in o2 are partial, not full width: at t~0.33 for u 0.15-0.43 and 0.62-0.88; at t~0.72 for u 0.15-0.80.
6. Curved-building-side wall face reads light where o2 shows deep shadow (check material/normal).
7. NEW GATE RULE not yet done: straight-down render overlaid on a satellite image (Esri/Google) at the same scale
   and north; plan shape (roof edges, bowl edge, facade line, fence oval) from satellite/OSM only, never oblique.

## Exact next step
Edit wip/build.py: LA0,LA1,LT0,LT1,LZ = -0.09,0.16,-0.05,0.23,11.3 (deck LNW must then go to the lift's outer side,
not inside the flight); then rows ns ~32 with slat texture; trim deck; partial walkways; rebuild, render, compare with
cpair.py / stz.py. Then the satellite top-down overlay, joins.sh, proof.sh, check every frame, push, report to secretary.

## Files
- Scratch (session temp, may vanish): C:/Users/DANTE/AppData/Local/Temp/claude/68a69b2f9027db7c/49ffd4e9-5fe2-41d4-9129-59ba6789966d/scratchpad/opt/
- Copies here: wip/ (build.py, geom.json, bp.py P2()/back(), cam.py, cam7.json, render.py, proof.sh, joins.sh,
  stov.py 4-panel overlay, stz.py gridded zoom, cpair.py corner pairs, railtex.py + rail/lamp/mesh.png, handtex.py, groundtex.py)
- Proof stills: wip/proof/ (render.png current cam7 render, stz2.png photo vs model grid, cpair1.png corners,
  benchmask.png photo bench field, grid_lift.png, corners.png)
- Last gate-passed model: .claude/review/optus_model/ (commit 82bc8feb3). WIP glb not committed (84 MB; rebuild with build.py).
- Reference photos: scratch refs/o1..o4.jpg (o2 = camera-matched photo, cam7.json), refs/optus_photo.png.
- Build: blender -b --python build.py -- <abs>/optus.glb <abs>/optus.blend ; render: blender -b optus.blend --python render.py -- <abs>/cam7.json <abs>/render.png
- optus_stairfix_board.png (rejected A/B board) left uncommitted.
