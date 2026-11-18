# Ikon Park exterior (row 202 step 2b): PAUSED, not ready for gate

Branch `claude/practical-napier-5bd466`. Last full proof set: commit 9d995eda0.

## Done
- A (1990-96) and B (1997-2005) models built (`ikonpark_1990-96.glb` = geomA7, `ikonpark_1997-2005.glb` = geomB6), with overlays, part boards, joins, facade close-ups and turntables in this folder.
- A third, ground-level photo (`ikon-park-2.jpg`, modern) now has its own camera (`scripts/camI2.json`, from `scripts/fitI2.py`). The far grass edge is 0.87 px rms and the four west goal post bases are within 2 px. The camera sits 3.3 m up in the Gardiner Stand.
- The Pratt height conflict is settled:
  - The third photo reads the Pratt roof front at 18.3-31 m.
  - The 1994 heights (A7) are 15.7-28.4 m.
  - The old modern-camera heights (A6) were 12.9-18.5 m, and are 27-76 px too low in the third photo (`wip/pratt_heights_thirdphoto.png`, red = A7, yellow = A6).
  - **So the modern aerial camera (camPA6/PA8) is what was wrong, not the 1994 heights.**
- The 1994 mast tops, read by hand from a pixel grid, match A7 within about 2 px. The A7 front edge follows the 1994 roof edge by eye (`wip/pratt_A7_vs_A8_1994photo.png`, red = A7, yellow = A8).

## Open faults
1. **Pratt front edge.** The third photo puts it 1-4 m above A7 at the ends and about 1 m below in the middle (geomA8 holds those heights). The 1994 photo prefers A7. One of the two readings is still wrong. The likely culprit is the third camera's height or pitch trading against its grass offset, since all its ground features are near its horizon.
2. **Modern aerial camera** still to re-solve (fitB10 was running at pause, logs `w/fitB10_1.log` and `w/fitB10_0.log` in scratch). Its old fit pinned the grass offset at the 4.0 m lower bound. Its horizon points (HZ, sloping 40-48 px) look wrong too: the visible skyline is about y 41-43 across.
3. B under the modern camera: Pratt masts 3-24 px off, roof edges 5.8 px rms, Legends back base 5-10 m off OSM. All of these are to be re-measured once the camera is re-solved.
4. The third photo shows the Pratt roof running about 90 px further west than the model ends. To be checked against the straight-down plan.
5. **New gate rule, not yet done:** plan shape only from straight-down sources (satellite and OSM). Proof needs a straight-down render overlaid on a satellite image at the same scale and north. Roof edges, bowl edge, facade line and fence must sit on it all the way round.

## Exact next step
Read the fitB10 logs. Re-solve the modern camera with a corrected horizon and the grass offset free. Check which Pratt heights (A7 or A8) it accepts. Then do the straight-down satellite overlay and fix the plan from it. Rebuild A and B, re-render the overlays, joins and turntables, check every join zoomed in, push, and report.

## Proof files
This folder: the A_*/B_* overlays and parts, joins_0..3, facade close-ups, turntables, and `wip/` (the two pictures above).

## Scratch scripts
- Folder: `C:/Users/DANTE/AppData/Local/Temp/claude/d00d327f9fc84438/b0e6313e-783e-4879-9574-53fc9d3fcd79/scratchpad/ikon/w/`
- Copies are in `scripts/`. The new ones are fitI2.py, cmpI2.py, i2trace.py, fitPA9.py, fitB10.py, geomA8.json, camI2.json, camPA9.json and i2_trace.json.

## Reference photos
In scratch `refs/aus/`:
- princes-park-1994.jpg (A)
- princes-park-aerial.jpg (modern aerial)
- ikon-park-2.jpg (ground level, Gardiner)
- OSM: `osm/geo.json`, way 22779384 (grass) and way 390148642 (Legends)
