# Leederville Oval exterior: READY FOR GATE (row 202 2b)

Stadium only, to the outer fence. No turf, posts, nets, temporary stands or crowd. Plan from satellite + OSM only.
Model: `leederville_oval.glb`. Build: `build/` (build.py, tex_*.py, grass_fix.py, closeups.sh, run_all.sh, tex/).

1. **Camera-matched overlays:** `night_drone_2025-04-15_full_photo_render_overlay.png`, `day_drone_2025-03-24_full_photo_render_overlay.png`,
   their `_outlines.png`, and one crop board per part (`*_part_*.png`). Gate 1 fix: the near (NW) tower's lamp frame is
   back-projected through the day-drone camera: same top, same 60 deg slant, nine bars 0.82 m apart, 7.4 m wide.
2. **Turntable:** `turntable.mp4` (72 frames), `turntable_sheet.png`, `turntable_still_0..3.png`.
3. **Facade and join close-ups:** `closeups/` (tower_s, sbld_west, sbld_south, ms_west, ms_north, ms_seats, ld_sign, media_sign),
   `facade_closeup_no_photo_pixels.png`, `fence_closeup.png`, `fence_look_photo_vs_model.png`. Seats are built as
   bucket seats (pedestal, pan, backrest leaning back): `closeups/ms_seats.png`, `closeups/seats_close.png`, `closeups/sb_seats.png` (south stand, blue).
4. **Top-down overlay on satellite:** `topdown/topdown_satellite_overlay.png`, `topdown/topdown_outlines_on_satellite.png`
   (10 m grid; outlines sit on the satellite edges within about 2 m). The apron is tan dirt where the satellite is tan
   (north and east) and grass only where the satellite is green, read per metre from the satellite (`build/apron_mask.py`).
5. **Textures:** `textures_photo_vs_handmade_1..3.png` (photo crop beside hand-made texture per surface), each judged against
   its crop. Crops fixed: render_beige = Members tower render, concrete = Members front wall, fascia_cream = media band;
   new apron_dirt row (satellite crop). `texture_stddev.txt` is for information only. No photo pixels on the model.
6. **Seating close-up, empty seats:** `closeups/ms_seats.png` (Members Stand: maroon bucket seats, E14). All three stands carry
   empty seats: green grandstand, maroon Members, blue south stand (its seats were missing before; fixed). No crowd anywhere.
7. **Signs beside their reference crops:** `signs_photo_vs_model.png`: Members band (SUBIACO FOOTBALL CLUB + SFC monogram |
   MEMBERS STAND | Home of the LIONS), THE LION'S DEN gable, JACK SWEET MEDIA CENTRE plate, all hand-lettered.
   HOLMAN / SULLIVAN ads removed (plain fascia, plain scoreboard cabinet).
8. no open faults
