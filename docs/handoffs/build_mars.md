# Build Mars Stadium (row 202 2b)

Session local_e8ff1269, worktree `.claude/worktrees/elated-swirles-5951da`.

## Where the work is now

Model on PR #1920 (glb 9872cfbb).

---

## The session's handoff file (verbatim, C-Users-DANTE-Documents-GitHub-Afl-auto-battler-claude-worktrees-elated-swirles-5951da.md)

# Handoff: Mars Stadium (Ballarat) ground model, row 202 2b

### State
- 02:35: 9a772c9ff, GLB 76f13a8c (bg-mars and the lead told): west_stair white, 14.2 m + west_stair_flights (grey). Lead rule: only photos of the CURRENT ground count toward the 10 for changed parts; put the date on every side-by-side. Open fault: the west roof shows only 2 skylight stripes (aerial ~10; check the roof_strip UV / tile 10).
- 02:20: b71a04cd8 pushed, GLB df47b687 (bg-mars and the lead told). Open triangles are now 'tri_void' pale grey. A background agent is pulling >=10 photos per part into tools/grounds/mars/press/refs/<part>/ with sources.csv (12 parts). When it reports: one side-by-side board per part (render at the photo's camera), MATCH/FAIL per region, fix the FAILs.
- RULING 2026-11-21 (coordinator and lead): before building more, pull >=10 Google Images/Street View photos PER PART (west back, north stand, stair towers, trusses, media boxes, NBSC clubhouse, entrances, signage, surroundings, ROOFS, SEAT COLOUR LAYOUT (lead added these two); daylight/night/drone/close-up) into press/. READY: per part a side-by-side board (render from the photo's camera + photo, with its filename), regions called MATCH/FAIL, and the photo count per part in the table. Fewer than 10 photos or no side-by-side = fail. bg-mars was sent the ta_aerial path and its facing (URL unknown).
- 2026-11-21 02:00: 442ad946b, GLB 4a082450 (bg-mars told). The director said the back wasn't close enough and sent photos: the 2026 aerials (clubhouse with orange walkway lines; the west stand's stair tower and water tanks; the east wrap's big V columns), the ground floor (blockwork wall deep under the rake, raked struts) and the 2017 main stand. Built from those, measured off the user photo (door 2.1 m gives the scale): 2.3x1.4 m cells x4 rows, 4.7 m clear, nose R4, cols 8.6 m Y-head, undercroft 8 m deep (conc_block), nose = fascia white. Compare render/cmp_back.png. Left: the open triangles should be pale grey glass (now black); the west stair tower with external stairs at the south end; the east wrap's V columns; stripes on the flat roof are faint in the oblique view; the clubhouse.
available (gaps closed: new_se b0 98, new_s b0 142; GLB md5 a2ede33e1e4e2000354f494183b35caf pushed; bg-mars on director hold, send md5 at READY; not READY)
- 23:25: seats navy/charcoal/slate, old roofs roof_skylit with rib_under, new roofs roof_white, D['buildings'] (build.py buildings()) = NBSC pavilion poly from ge/top.png. Run Blender from tools/grounds/mars (out dir is relative). Compare render/cmp180.png. Next at-a-glance faults: pavilion form (curved cream drum at its east end, brown walkway lines, glazed north face, lower annex); continuous lower bank between new stands; rust core at the east/new_se junction; east concourse membrane canopy; raked V columns; west streaks; Street View of the backs.
- 23:20: new stands' backs are OPEN (Commons CC0 design render press/wm/Mars_Stadium_and_Ballarat_Athletics_Centre_2026.jpg, gitignored): two_tier S['open_back']=7 -> rake soffit, columns per 2 rafter bays, clad podium (facade_brick). Render check render/bk1.png. Still to match: raked V columns + rust/copper podium cladding as in the render; north back ref (Commons file Mars_Stadium_-_North_Ballarat_Social_Club_and_Eureka_Stand.jpg downloaded, not yet studied); west weather streaks.

- 2026-11-21: nose() in build.py (S['nose'] R/under/col) on west and east: quarter-round roof edge, facade_tri band from z 4 up to the roof, steel columns every 6 m, dark recessed ground floor (boxes_glass). west_stair building at bearing 306. facade_tri back to 3 x 2.6 m panels (the real count is about 3 rows over 8 m). GLB 1a7aec84 pushed; bg-mars told. Compare: render/cmp15.png. Left: the west stair tower is hidden in that view (check its position against pta15), there are too many dark triangles (real: small dark voids in each white folded panel), an east stair tower, the clubhouse detail, the 8 GE overlays (no popups), the numbers table, and the 2026 aerial URL and date.
- Street View done, sent to coordinator. The July 2026 views at White Ave (SW) and Beech Ave (W) are blocked by fencing and trees, and the east side has no Street View coverage. The TripAdvisor 2026 aerial confirms the west and east backs are unchanged since 2017. Build the rounded roof edge, the open ground floor and the stair towers from PTA 13/15.
- READY sources must name the URL and date of the 2026 aerial (press/gi/ta_aerial.jpg, TripAdvisor). The URL isn't recorded; find it again with Google Images, query "Mars Stadium Ballarat new grandstand outside entrance concourse".
- (done) Coordinator: the PTA 2017 photos predate the redevelopment, so confirm the west and east backs against the newest dated Street View before building. Send bg-mars every md5 change (it has 6ae897fa).
- GLB md5 6ae897fab96b47951fb22d60e8b00be0 pushed (facade_tri now 1.5x1.3 m panels, no weather; facade() has wx flag).
- FAULTS vs press/pta Mars_Stadium_13/15 (render/pta13.png, pta15.png, cmp15.png): west/east roofs need a ROUNDED nose curving down over the back (white, blue-grey radial skylight stripes); triangle facade is a band ~8 m tall sitting on an OPEN undercroft (columns ~6 m apart, ground floor recessed, dark); white stair tower at each end; render camera b15 wrong (use lower pitch from outside west).
- (older) FAULT (render/j1.png): east wrap back shows a black sawtooth void between the roof rear and the back wall (the trusses under the roof show through). Fix: close the back wall up to the roof's underside, or drop the rear end of the trusses. Then check render/j1 and j2 again.
### KEY REF + at-a-glance FAILS (23:35)
press/gi/ta_aerial.jpg (TripAdvisor, 1600x1061): REAL aerial of the finished 2026 ground (found via Google Images "Mars Stadium Ballarat new grandstand outside entrance concourse"). Compared whole with render/ta90.png, ta270.png:
1. Seats: real = dark navy / charcoal everywhere (light-blue blocks only as pattern); model = saturated blue + white speckle. FAIL.
2. Continuity: real ring is near-continuous, with a low white wrap roof (curved white fascia) linking stands; model has wide gaps between stands. FAIL; re-trace stand ends on this aerial.
3. Big flat grey-roofed pavilion (rooftop plant, brown parapet lines, curved cream brick end) at one end: MISSING from model. FAIL; it's inside the outer fence.
4. Orientation SETTLED (ge/top.png labels North Ballarat Sports Club on the flat-roof pavilion): aerial looks south; its bottom = north pavilion, right = west (triangle facade), left = east wrap, top = new_se/new_s, scoreboard + grass top-right = SW (my bank 192-250). Stand names are right. The pavilion (fault 3) belongs with my 'north' stand: rebuild north as the full club building to the aerial + ge/top.png.
Coordinator 23:40: use Street View for backs too; Gemini skipped (typing blocked by permissions unless the director allows); next msg to coordinator = READY or real blocker.
5. Old-stand roofs: real = plain white with faint rib stripes; model has tall white top trusses. Check.
6. White membrane canopy over the concourse beside the wrap stand; scoreboard with grass + trees next to the new stands (likely the south bank). Check.
Director (via coordinator): Google Images + Google Maps (Street View, 3D) + Gemini (gemini.google.com in Claude in Chrome, his signed-in account, never type a password) before each part and before READY; close tabs. Next msg to coordinator = READY or a real blocker.
Western Bulldogs render (Google Images) agrees: open back, raked columns, rust-red underside cladding.

### Latest (2026-11-20 23:10)
- Coordinator (AFL game handoffs) re-ordered: carry on near stand + stand backs; READY only after every overlay compared whole and fixed, with full md5 and numbers table. Replied.
- More back-photo sources searched, none show the backs: premier.vic.gov.au release 30 Sep 2026 (no stadium images; text: "brickwork and seating bowl panels drawing on the shapes of Mount Buninyong and Mount Warrenheip", "lift installed under the new grandstands"); its PDF (404); Ballarat Times 31 Oct 2025 (only GT-2.jpg, people with plans); Courier 8593140 (403). Next: Street View Howard/Norman St via GE street-level, Flickr, Wikimedia.

### Earlier (22:35)
- new_se plan checked against the GE mesh (ge/s122.png, render/e_s122z.jpg; GE is the same Oct-Dec 2025 stage as bcc2): edges fit. The plan stays; the press-photo mismatch is put down to the unsolved press camera.
- Backs: new paint.py facade_tri (white triangle panels, tile 6x12 m) on west and east, from the PTA 2017 photos press/pta/*.avif (Mars_Stadium_08/13/15 show the west back). facade_brick on new_se/new_s rests only on the state's "Wadawurrung-inspired brickwork patterning" text plus the brick stair core in aus_new. No photo of the new stands' backs, so the plain 15 m brick wall is UNVERIFIED and likely wrong (they may be open steel). North back is still York facade_es (no reference).
- GE can't take its camera below the roofline (bk_*/bc_* frames are useless for backs). Next sources to try: Street View on Howard St/Norman St, Flickr, Wikimedia Commons "Mars Stadium 2026".
- Blender prints an "unregister_class ... _RNAMeta" Traceback at exit. It's harmless; the GLB is written.

### Earlier (20:40)
- New refs in press/: bcc2.jpg (City of Ballarat Oct 2025, 3822x2867, field level, both new stands as bare bleachers, old east roof at left; scaled copy ge/p2.png), bcc1.jpg (officials), aus_oct27.jpg (crop of bcc2). Still NO photo of the south embankment; searched: web search, City of Ballarat news 24 Oct 2025, Ballarat Times 31 Oct 2025, austadiums 1596 + 1850, Courier 9096758 and Coliseum (both 403).
- work/pmatch2.py solves bcc2: 4 variants (fence+tops; +old east lip; known geometry only; +radial k1) all fail (30-180 px). Stop solving; next evidence = GE views placed at the photo's viewpoint.

### Earlier (19:45)
- GE fit done: north z_roof [10,13.5]; new_se z_roof [18.5,17.5] arch 4 camber 1.5; new_s [17.5,16.5] arch 3. Tools: work/ovl2.py (edge overlay), work/pmatch.py (press camera solve -> work/p1cam.json; render spec work/p1spec.txt).
- Press photo aus_new.jpg: far stand (new_s) matches well; near stand (new_se) can't be fitted at the same time (resid 20-90 px). Two solves failed: gather more 2026 photos (drone, other angles) before changing geometry.
- Seats: seats_seat_{blue,cream,greyblue,white}.bin; colours added to Oval3D.SEAT_COLOURS (seat_slate belongs to another ground).
- South bank (kind 'bank', 192-250, z_top 3): no photo exists; press only says "southern standing-room viewing embankment".

### Task
Build Mars Stadium from scratch (brief from session local_64d97632). Rules: side-session-notes/local_64d97632*/ground_builder_rules.md.
READY goes to stadium lead local_6e4c78c4-058b-47c9-8f00-8696d4de4f2b; PR after the lead passes it ("Part of row 202" line, auto-merge).

### Where things are
- Worktree elated-swirles-5951da, branch claude/elated-swirles-5951da (main merged 2026-11-20).
- tools/grounds/mars/: pipeline copied from york_park (work/geo.py origin = OSM pitch 128280660 centroid -37.539307,143.848166).
- sat/esri_025.png = Esri z18 (z19 not available here), pre-2025 state.
- ge/: Google Earth views (work/cdp.py, port 9587). The GE 3D mesh shows the stadium MID-CONSTRUCTION (2025).

### Unfinished / Next
- Era DECIDED (director via local_64d97632): finished 2026 ground. Build the two new eastern stands and the southern viewing area from press photos; camera-match each press photo.
- Fence done: work/fence.py drops trace points >3 m off the ellipse, refits, writes 'fr' (360 radii, smoothed) into work/fence.json. build.py (when copied) must use fr, not 'ell'.
- Press refs in press/: aus_new.jpg (1200x675, austadiums news 1850: both new eastern stands from the field, curved steel roofs, timber rafters, blue seats with white pattern, brick stair core), al_2026.png (ausleisure 720x480). Still need a southern viewing area photo.
- Built: model/mars.json (west, north, east wrap, new_se 102-142, new_s 146-188), build.py adapted (fence_r reads fence.json 'fr'), first GLB pushed (b69fe0986), bg-mars session told.
- Run: blender = "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b --python model/proofs.py -- model glb ; renders: model/render.py -- render top:0:0:600:0:0:0 l135:135:65:420:0:0:0 ; overlay: work/ovl.py <v> 0.45.
- GE top (ge/top.png, 2025-12-28) registers at 1712/600 px/m centred (960,540), north up.
- Next: fit heights (all guesses) with overlays per stand; southern viewing area (190-250, grass embankment, no photo yet); Mars textures (seats blue/white pattern, timber rafters, roofs) in paint.py; then proofs, board, READY.

### Open questions
- none

### Gotchas
- GE URL altitude must be ~450a (Ballarat ground ~451 m ASL); 5a puts the camera underground and gives blank blue frames.
- Other ground sessions run headless Chrome on 9417/9433/9463; use a free port or you screenshot their tabs.

- 2026-11-21 02:20: roof stripe fault FIXED (u was bearing x radius; now true arc distance in roof_strip; arch_roof still uses old formula). Photo agent done: press/refs/<part>/ + sources.csv; under 10: west_back 7, stair_towers 6, entrances 6, signage 8, media_boxes 8 -> pull rest via Google Images in Claude in Chrome. TripAdvisor URL candidates in agent output; date unknown.
