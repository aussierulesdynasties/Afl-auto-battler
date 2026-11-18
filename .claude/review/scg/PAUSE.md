# SCG exterior (Row 202 step 2b): PAUSED, not ready for gate

Paused 2026-11-18 on the lead's order (account switch). Branch `claude/inspiring-heisenberg-a3f33c`.

## Task on resume
Gate failed on 6b67c085f ("Send them back"). Rebuild the Members Pavilion and the Ladies' Stand exactly as the photo:
clean pitched roofs (straight ridges, matching gables, small gables, cupolas/finials), hand-painted walls (windows, white
trim, balcony and verandah lines), one continuous row along the boundary. Overlay on the photo, check every join zoomed in,
fix every known fault, then READY FOR GATE to the secretary with a photo | model side-by-side like proof/crop_heritage.png.

New gate rule (director: "Yes, every ground"): plan shape comes only from straight-down sources (satellite, OSM).
The proof needs a straight-down render overlaid on a satellite image at the same scale and north; roof edges, bowl edge,
facade line and fence oval must sit on it all the way round. Not done yet.

## Done
- Heritage layout rebuilt as 13 clean buildings (build/blds.py, build/herbld.py): true-plane roofs, straight ridges, flat
  gable ends, white barge boards, finials, 4 small field gables, 2 skylight lanterns, Ladies' glazed roof strip.
- Hand-painted textures (build/hertex.py): brick + sash-window elevations, two-tier open-stand field faces, pediment,
  sandstone ashlar for the end pier.
- Rotunda roof is now a plain cone at the stand's pitch (no lump). Roof-mask fit vs the aerial photo: IoU 0.65 -> 0.71.

## Open faults (all must be fixed before gate)
1. Bowl seats in front of both heritage stands are teal; the field photo shows maroon lower-tier seats right down to the
   fence (geo.py `band(seats,...)` line ~230: split 112-168 deg onto a maroon seat material; texgen + build_hand 'seat' UV rule).
2. Field faces: the green verandah, white balustrade and lower tier sit below the bowl top (z 7) and are hidden. Photo
   (refs5, px grid): Ladies' verandah about 0.42 of fence-to-eave height, Members' about 0.45; move them in hstand().
3. Members' clock tower too tall, white, egg dome. Photo: square green-roofed clock stage with clock faces and a flared
   green pyramid cap, smaller (geo.py line ~286, second tuple).
4. Ladies' cupola: photo shows a small arched-window drum with a green dome on the ridge; model has a white box.
5. Rotunda drum (geo.py line 284) is bare brick; give it the windowed 'hw130' wall.
6. Remaining roof-mask misses: brick parapets/courts showing, small front overruns, L1 overshoot near the pier.
7. Joins not yet checked zoomed in: Ladies'/Members' join, gablets, pier, rotunda/L1 valley.
8. Satellite top-down overlay (new rule) not made.

## Exact next step
Fix fault 1 in geo.py/texgen.py/build_hand.py, then 2-5, then `bash run.sh 190,390,490,611`, `python rdiff.py`,
Blender `turn.py -- <S> <S>/out/turn heritage_roofs,her_field,her_street,her_join`, then the satellite overlay.

## Proof files (WIP)
proof/wip/her_field.png, her_street.png, her_join.png, heritage_roofs.png, rdiff.png (red photo-only, blue model-only).

## Scripts (copies in build/; working copies in the session scratchpad)
blds.py (building list + frames), herbld.py (heritage geometry), hertex.py (heritage textures), geo.py, texgen.py,
build_hand.py, turn.py (close-up shots), run.sh (full rebuild), sbs.py (side-by-side), bov.py (eave outlines on photo),
_rpb.py (rotated plan), rdiff.py (roof-mask IoU), meas.py (camera), zoomgrid.py (labelled grid crops).

## Reference photos
build/refs5/SCG-ladies-members-stands.jpg (field view, heights and looks); build/refs/scg.jpg (main aerial, cam.json);
refs2-refs4, refs7 as listed in earlier proofs. Watermarked photos are reference only.
