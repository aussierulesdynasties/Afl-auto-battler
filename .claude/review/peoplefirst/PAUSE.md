# PAUSE: People First Stadium exterior (row 202 2b), not ready for gate

Paused 2026-11-18 ~22:50 Melbourne on the lead's account-switch order.

## Done since the last push (44b523127)
- Lamp heads: deep lattice cage. Dark block: rooftop plant, sign blank. SE outbuildings.
- Roof: smoother membrane lobes; near-side ribs placed from the photo (RIBS_NEAR, within ~3 px);
  near roof outer edge re-solved (geo_build.json rout 132-232 deg; within 0-3 px, x 440-1300);
  navy band edges within 0-2 px (NBULGE 0.2 far / NBN -0.8 near).
- Far voms: flush cut openings with blue side walls (VHW 1.1 m), ~10x16 px as in the photo.
- E end: 50% overlay (wip/ov_E.png) lines up: seats, voms, navy band, tower.
- LED fascia texture rewritten (handtex.py): pale blue band over navy, no lettering, 2 m tile.

## Faults still open
1. LED fascia: the lower field-side fence (lower bowl, z 0-1) uses the same 'led' material, so it now
   reads pale blue; the photo shows it dark navy. Give it its own navy material. Check the upper band's
   navy bottom stripe is as thick as the photo's (~4 px of a ~10 px band at x 975, y 518-530).
2. Upper walkway above the fascia reads wider/greyer than the photo on the far stand (wip/d_far.png).
3. E-end vom look: blue wall + dark + red close but not identical.
4. Lobe-cap shading near the NE corner; west roof seam at x~945; red band end at 174 deg: unchecked.
5. NEW GATE RULE (director: "Yes, every ground"): plan shape only from straight-down sources (satellite,
   OSM). Render straight down, overlay on the satellite image at the same scale and north; roof edges,
   bowl edge, facade line and fence oval must sit on it all the way round. Not done yet.
   (Earlier work used OSM/satellite for the plan: scripts osm2geo.py, sat.py, rgsat.py, satgrid.py;
   reference/sat.png, satgrid_osm.png. Verify, but the near roof edge rout was re-solved from the oblique
   photo this round: re-check it against the satellite.)
6. gate/ boards are from the old push: re-render all after the fixes.

## Exact next step
Fix fault 1 (new navy material for the lower fence in build5.py line ~96), rebuild, then do the
straight-down satellite overlay (fault 5), then zoom every join, board.py, turn.py, push, report.

## Files
- build/build5.py (current build), build/handtex.py, build/htex/ (textures + tex.json)
- build/scripts/: every scratch script and json (cmp.py crops, crops13.sh, edgescan.py, navyscan.py,
  dmap.py, unp.py, board.py, turn.py, geo_build.json, cam.json, ...)
- model/pf5.glb, model/model5.blend
- wip/render_r31.png (latest render), wip/d_far.png, d_Eend.png, ov_E.png, z_led.png, d_roofall.png
- reference/photo_clean.png (SkyePics 9783-01, camera build/scripts/cam.json), reference/sat.png, satgrid_osm.png
- Rebuild: copy build/ + scripts into one folder, then
  SAVEBLEND=model5.blend "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b -P build5.py -- pf5.glb render.png
