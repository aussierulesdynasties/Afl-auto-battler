# Gabba exterior: paused, not ready for gate

Branch claude/exciting-dirac-42b18b. Kit: tools/grounds/gabba/ (README has the build steps).

## Done
- Reopen fixes, pushed in 9b00351a7:
  - scalloped roof edge at the photo's depth (knob scallop 2.0);
  - east rooftop plant as an open capsule with three fans;
  - far scoreboard in its real shape: blank face, on a dark plinth, 2.5 m toward the field so the seats don't clip it;
  - dark navy faces on the south building and gate block;
  - sun fitted from the roof's shadow on the field (azimuth -12°, elevation 25°) in render.py, closeup.gd and tt.gd.
- In this WIP commit:
  - the white box under the far scoreboard is removed (director: "remove it / doesnt belong in our model");
  - the roof opening (RI in model_in5.json) is shifted (+0.76, -11.0) m onto the outer ring's centre, so the roof band is
    28-34 m all round instead of 17-42 m. This is a stopgap, not the send-back fix.

## Open faults (the send-back: lopsided plan read from an oblique photo)
1. The plan shape comes from the oblique photo (g49) via a camera fit, so perspective has skewed it. Rebuild every plan
   edge from straight-down sources (Esri or Google satellite plus the OSM outlines in osm/geo.json): roof inner and
   outer edges, facade line, bowl edge, fence oval.
2. The opening is nearly round. The real opening and fence oval are longer east-west, about 1.2:1.
3. Off-centre: the model's outer ring centre is (11.6, -3.5); the OSM pitch and roof-sail centre is (5.1, -4.4).
4. The east-side buildings and the west block are stuck onto the ring. Place them from the satellite and OSM outlines
   (stadium-only scope).
5. Once the plan is rebuilt from top-down sources, the oblique overlay (g49) needs a camera refit with the plan held fixed.
   Right now the near inner roof edge sits about 25 px short of the photo.
6. Minor: west seats read brighter than the photo's shade; the membrane shadow crescents are not modelled.

## Exact next step
Fetch a straight-down satellite image of the Gabba (Esri World Imagery at zoom 19, centre -27.4858, 153.0381). Put it in
the model frame using osm/geo.json: local metres from lat0/lon0 as in osmgeo.py, then the model frame's 180° rotation;
check the rotation against the OSM pitch. Trace RI, RO, RF, the bowl edge and the fence oval in metres and replace the
photo-fit rings in model_in5.json. Render straight down (closeup.gd, eye over the centre at 520 m) and overlay it on the
satellite at the same scale and north: the proof. Then refit the g49 camera with the plan fixed, re-render the oblique
overlay and the join close-ups, fix every fault, push, and report READY FOR GATE to the secretary.

## Proof files (worktree .claude/review/)
- gabba_vs_photo.png (board), gabba_overlay.png, gabba_parts.png, gabba_exterior.mp4, gabba_still_000/030/060/090.png;
- close-ups: facade, gate, seats, screen, plant, south, edge, hyundai;
- gabba_roof_topdown.png (before and after the RI shift).
These show 9b00351a7's model; the h12 re-render after the shift may have overwritten the scratch copies only.

## Scratch scripts (C:/Users/DANTE/AppData/Local/Temp/claude/72f99ad548680169/29b04428-c2e5-4649-b4b6-49db3badf663/scratchpad/gabba)
- Build and render: build.py and sw.py, mktex_hand.py and mktex_sw.py, render.py, compose.py, board.py, full2.sh,
  h8chain.sh, rt2.sh, closeup.gd, tt.gd.
- Camera fit: fit9.py, which lets RI scale and shift freely; that freedom caused the skew. cam.py holds the OSM roof
  rings; unproj.py and un2.py unproject from the photo.
- OSM: osmgeo.py turns osm/gabba.json into osm/geo.json in local metres.
- Comparison: cmp.py.
- Knobs: model_in5.json is current; model_in5_preshift.json is the knobs before the RI shift.

## Reference photos
- refs/g49.jpg: skyepics aerial 100896-16796-021, oblique, from the south-east. From now on, heights and looks only.
- The director's Google Maps screenshot, straight down: the roof ring is an even depth all round and the oval sits
  centred.
