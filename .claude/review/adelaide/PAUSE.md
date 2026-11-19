# Adelaide Oval: paused 2026-11-18 22:45 Melbourne (account switch). NOT ready for gate.

## Done since the gate rejection of 32d3d049f
- Fault 2 (river roof rim jagged at the outer wall): fixed. Per-ray back fit (`rim_fit` in spec, gen.py roof heightfield) makes the rim follow the wall; clean in wip/join_river.png.
- Fault 3 (dark jagged wall edge behind the east membranes): fixed. The hotel's dark top slab back line is smoothed (tools/hotel.py prism_shell, brick wings sigma 4.0); clean in wip/join_east.png.
- East stand stepped back edge and river wall-top teeth: removed with `way_drop` (spec stands east/river).
- East roof north end squared off (gen.py smooth_outline `square`).

## Still open
- Fault 1 ("Western" = the model's EAST roof, hotel side; its "left end" = north end): membrane lobes still show lumpy, wavy back edges and a wavy front hem on the end lobe (wip/join_west.png). Edges are not yet clean smooth arches.
- Small diagonal fold at the top corner of the white end wall, north end of the east stand.
- River roof front edge has a dip (already in 32d3d049f, not on the fault list).
- NEW gate rule (director: "Yes, every ground"): plan shape from straight-down sources only (satellite + OSM), proof includes a straight-down render overlaid on the satellite image at the same scale and north. Not done yet. Esri tiles and OSM outlines already downloaded in the scratch folder (esri/, osm/).

## Exact next step
1. Check whether the lumpy lobe edges are in the plan outline or in the heights: plot roof_east outline from straight above against the Esri image; rebuild the east roof plan shape from satellite/OSM (new rule) with smooth arcs per lobe.
2. `front_fit: true` + `rim_fit: 3.0` were just switched on for east and west roofs (untested by eye beyond wip/join_west.png). Revert with wip/spec_pre_front.json if worse.
3. Straight-down render + satellite overlay, turntable_4, three join close-ups, A/B/C boards; self-check every edge; commit, push, READY FOR GATE to the secretary.

## Files
- Proof (gate set of 32d3d049f): proof/ (turntable_4.jpg, A/B/C overlays, part crops, facade close-ups).
- WIP renders: wip/join_west.png, wip/join_river.png, wip/join_east.png.
- Scripts: tools/gen.py (model), tools/hotel.py (hotel), tools/render.py (Blender: turn/orbit/match, ONLY filter), tools/joins.sh (3 join close-ups), tools/board3.py, parts.py. Build: `python tools/gen.py > gen.log`; Blender 5.2.
- Spec: spec.json (roofs east/west/river, stands with way_drop).
- Reference photos: photos/ (A, B, C, see SOURCES.md). Scratch working copy: C:/Users/DANTE/AppData/Local/Temp/claude/be5a18bc2f5de524/1c84dc0e-f6b1-4882-845d-87312d8e6193/scratchpad/ade (may be cleared; this folder is the durable copy).

## Progress 2026-11-19 (resumed session, stopped at usage limit ~06:40 Melbourne)
- The Hill built (tools/hill.py -> model/hill.ply): grass patches (satellite plan), heritage scoreboard, tower, big screen (fit to c09 corners + c11 edge), rails, amenities. c09 overlay lines up (rend/hill/ovl09.png, not committed).
- East stand north tip capped (spec stands east `low_end`, gen.py stand_z): clears the sky in c09.
- Top-down: tools/render.py `top` mode with LEAN=0.2008,-0.0637 (satellite off-nadir shear); tools/topdown.py + topcrop.py. Readings: fence oval N/E/W/S within ~1 m, east roof hem ~1 m, west back edge ~1 m, Hill grass edges ~1-2 m, screen ~1 m.
- STILL OPEN: Fault 1 east-roof lobes still lumpy (rend/j/join_west.png 2026-11-19); end-wall fold; river front dip; c11 Hill overlay recheck (parapet maybe 10 px low); Hill close-up + NW/NE join close-ups; SOURCES.md Hill photo URLs (hill/cand/list.json: c00,c01 2026-07-21; c07,c09 2022-09-22; c11 2023-02-14); full proof set.

## Progress 2026-11-19 15:30 Melbourne (usage limit again)
- Fixed: east lobes, end-wall fold, river dip, c11 Hill aligned. Signs added: heritage scoreboard lettering (hill.py), "East Gate" + "Adelaide Oval" pylon (hotel.py, letters.py).
- Next: wait for/rerun `bash tools/proof.sh` (writes rend/p/done.txt), build boards (board3.py, rend/p/signs_board.py), self-check, copy to proof/, move wip/READY_draft.md to READY.md, delete PAUSE.md, commit, push, report.
