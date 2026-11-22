# Stadium background scenes plan

Session local_a479dc03, worktree `.claude/worktrees/stadium-background-scenes-7fe291`.

## Where the work is now

Ran the MCG and Traeger scenes plus sub-agents (Street View heights spots 81-153; MCG rail yard rebuild) that stopped on the usage limit. MCG and Traeger pipelines saved in .claude/review/mcg_bg/ and traeger_bg/; big files in C:/Users/DANTE/Documents/AFL3D_archive/.

---

## The session's handoff file (verbatim, C-Users-DANTE-Documents-GitHub-Afl-auto-battler-claude-worktrees-stadium-background-scenes-7fe291.md)

# Handoff: stadium background scenes (prototype: MCG + Traeger)

### State
Resumed (director said resume all). Awaiting director: MCG f8a92e5e (mcg_1843.glb 8dcfd254), GMHBA 21 ec22c456 (cd2f8354), PF v9 6dafffce (3e5c537f); on pass tell GMHBA/PF to merge #1878/#1892. Optus 011a0bbd FAILED my gate (blotchy forecourt, no planters), sent back. Adelaide build15 running (tan Oval No.2); must use adelaide_es2.glb md5 e9e6c618, gate every 30th frame.
New rule 2026-11-20 (research_precision note, relayed to Optus/PF/Adelaide/GMHBA): many more ref photos, measured table vs model in every READY, mismatch = fault. Applies to MCG too. Director rejected Optus stadium roof (blurry sheeting, flat grey fascia): texture session repainting; Optus re-renders on its new glb.
Pickup: taken (C:/Users/DANTE/Documents/GitHub/Afl-auto-battler/.claude/worktrees/stadium-background-scenes-7fe291)
available (2026-11-20 ~02:45). MCG audit fixes sent to the lead. Optus texture pass now 39b7e33f9 (3D empty seats, rows fixed; outer edge unchanged). Bellerive GLB 786da1d0a on claude/bellerive-exterior (3D seats). Gabba GLB dd9c2e048 on claude/hopeful-tesla-07de91 (3D seats, stepped treads).
- Traeger spec now points at ../glb/traeger_tex_ff5971d77.glb (texture pass ff5971d77: east wall removed, seats/steel repainted). Rebuilt 02:21 OK (out/traeger/check/aerial.png, base_000 looked at: wall gone, layout matches; tan model base inside fence still there). base_001-005 + ring not yet viewed. East-wall fault now fixed by the texture pass.
- Director 2026-11-20: "just focus on getting mcg done". Other grounds wait.
- MCG READY items done 2026-11-20: orbit out/mcg/video/mcg_orbit.mp4, fence out/mcg/fence/fence_sheet.jpg, base/ring out/mcg/check/*_sheet.jpg, texture stddev all >=11.6. Footbridges now ramp end-to-end on piers with railings (scene.py, backup scene.py.bak_br). Shader bake DONE 2026-11-20 (0 procedural nodes; ground baked to data/mcg/prep/ground_baked.png via bake_ground.py, run before scene.py; GLB 241 MB; veil export warning is a harmless false alarm). NOT done: camera-matched photo overlays (Eureka first try in out/mcg/ov/eureka_cmp.jpg). Side sessions: bg-optus, bg-marvel, bg-adelaide, bg-peoplefirst building; bg-gmhba held for a passed model (director: "ask for one").
- MCG extent (director 2026-11-20): 3 x 3 km square only (near_half_m/tree_r_m 1500; prep.py now drops buildings outside it, 6946 left). Landmarks: spire + Shrine only (A108, Eureka, Rialto, Skipping Girl cut: "this is an mcg background only, not a melbourne tourism guide"). Map: out/mcg/map/whole_3km.png.
- MCG landmarks: refs in scratchpad/ref_landmarks (browser screenshots; Commons scripts get HTTP 429 on every URL, browser works; refs.json = title/author/licence). Textures tex/lm_*.png from tex_landmarks.py (all grey std >10; sheet out/mcg/lm_tex_sheet.png). Geometry proto/landmarks.py, exec in scene.py before build_class; spec mcg.json landmarks list. Close-up job out/mcg/job_lm.json -> out/mcg/lm/ (reframed views: job_lm2.json; render: blender -b out/mcg/scene.blend -P render.py -- out/mcg/job_lm2_g.json after ground_job.py). Open landmark faults: Rialto view blocked by a grey mound and no river; Shrine stone too pale and roof hidden by trees; A108 glass paler than ref, log out/mcg/lm_build.log.

- 11-20 ~18:10: Director "Yes, build all four" Melbourne Park arenas. DONE in landmarks.py (spec landmarks += 'arenas', backup landmarks.py.bak_arena; footprints data/mcg/prep/arenas.json from arena_ovl.py; textures tex_arenas.py -> lm_arena_wall/copper/ribwhite/glazed/bubble/tiers/pitch). AAMI Park bubbles smoothed; close-ups out/mcg/archk OK. Footbridges: pale rails fb_rail_c + 1.6 m deck (scene.py.bak_fb). Full orbit rendering (job_video.json) -> gate every 30th (gate/mcg_*.jpg) -> send with mcg_1843.glb md5 8dcfd254.
- Gates 11-20 18:05: Marvel v4 eefd5806 PASSED, sent to director (session archived). GMHBA 3ade3ef9 FAILED (flat shed roofs, flat far land, flat lots, flat house roofs; sent). People First a3302bb3 FAILED (flat water, flat grass, far-land grid, confetti podium walls; message undelivered, retry via mcp send_message). Texture session asked to repaint GMHBA glb `wall` (no owner).

### Task
Director 2026-11-19: cheap, real-inspired 360° background scenes for every AFL-listed ground (37) plus 5-6 generic suburban scenes; liaise with "Resume stadium lead" (local_6e4c78c4-058b-47c9-8f00-8696d4de4f2b). "Yes, prototype" (MCG + Traeger), "Yes, build landmarks" (MCG: Rialto, Eureka, Australia 108, Arts Centre spire, Shrine, Skipping Girl with hand-made lettering; Traeger: check Mt Gillen). His wordless Traeger satellite screenshot = make Traeger surroundings match it (scratchpad/director_traeger_sat.png).
Lead's standard (relaying "same fastidious attention to detail"): ground_builder_rules.md (side-session-notes/local_64d97632.../) except stop-at-fence; layout from straight-down satellite + OSM; landmarks matched to named photos; hand-made textures, none with grey stddev <10; READY report = GLB path+time, top-down satellite overlay (~2 m), 3+ camera-matched photo overlays, landmark close-ups beside reference crops, texture close-up per surface + stddev list, fence-ring close-ups, "no open faults", orbit video. Also: audit the MCG + Traeger orbits already sent and send the lead every fault.
Director: aerials are reference ("vicmap dont own the world"); pixels never on a model.

### Where things are
- Prototype: D:\Temp\claude\b5e56bf702cd3703\4ee81fc3-6cf4-400f-9ad6-28a5df4e19ee\scratchpad\proto (build.sh, prep.py, scene.py, render.py, spec/*.json)
- New tools: sat_fetch.py (Esri z18 -> data/<g>/sat.png), ovl.py (top vs sat -> _blend/_check), fence_mask.py (trim model base to fence), tex_roof.py, tex_detail.py (tex/ground_detail.png, std 16.4, 4 m tile, multiplied in ground material with 1.21 lift), canopy_mask.py (trees traced from satellite; WIP).
- Traeger rebuilt 17:50: traced lawn/parking/greens, court slabs, roof textures, ground detail, tree_default 400 m²/tree on untagged land (trees 50,632). Overlay out/traeger/ortho/ovl_check.png registers well. Checks rendered: out/traeger/check/ring_sheet.jpg, base_sheet.jpg (NOT yet looked at).
- MCG: scene.blend is 16:10 (before roof textures + ground detail) on the WIP model. Ortho overlay out/mcg/ortho/ovl_check.png registers well.

### Fault list so far (for the lead)
Traeger: model base inside fence is tan where the satellite shows grass (model fault, rule 6 -> lead); thin lawn strip shows just outside the model base east of the oval; ground/roof close-ups unchecked; orbit predates all fixes; Mt Gillen not checked.
MCG: park canopy far too sparse vs satellite (Yarra Park, Fitzroy Gardens, Birrarung Marr near closed canopy; ours 420 m²/tree blobs); grass flat; orbit predates roof/ground texture; landmarks not built; model is WIP, not gated.
Colour note: Traeger desert hue matches satellite once the satellite cast (x0.40/0.48/0.60 measured on oval grass) is applied, so no change.

### Done since (~18:10)
- Fault list SENT to the lead (queued, 9 items incl. Traeger courts blurry, trees faceted, model base past fence).
- canopy_mask.py works (local-dark: L<70, L < 20 m median -12; frac 0.139) -> data/mcg/prep/canopy.npy; prep.py places a tree in each 6 m cell with >20% traced crown (canopy mode) inside the satellite extent.
- Courts as geometry: prep writes data/<g>/prep/courts.json (slab hulls + oriented court boxes); scene.py builds slabs (procedural grain), ITF tennis lines (5 cm quads), nets (alpha 0.55). Courts whose OSM box < 24.5x11.5 m get no lines.
- Texture-pass session reported Optus (fe4d81d1d) and Marvel (e7abdaf49, seats now 108,128,146; then de9d67683, seat/truss mottle removed; then 7a6c45e55, concrete repainted even; then d60000456, 3D empty seats in the bowl, outer edge unchanged; use the latest when Marvel's scene is built) passes: not my grounds yet, note for cohesion.

- ~18:50: canopy threshold 0.45 (MCG 4,140 traced trees, cover ~ satellite; out/mcg/ortho/yarra_cmp.png). Court lines gate fixed (OSM boxes = 23.98x11.54 doubles court): 10 Traeger courts lined + nets. Hockey pitch (spec hockey_at [-69,167]; OSM box 99.8x62): run-off slab (turf_runoff 52,104,178) + 91.4x55 field (turf_blue, his colours; Esri shows green, older) + FIH lines, 14.63 m circles, dashed 5 m line. Trees smooth-shaded + Voronoi leaf-clump shader. Trim edge refined to 0.6 m within 4 m of the mask line (no sawtooth).
- New model fault (Traeger, for lead): model `east_wall` (1 m wall, (91.6,-72)->(96.7,93)) runs through a real tennis court (satellite: out/traeger/wall_courts.png).

- ~22:30: MCG audit vs satellite (path_cmp.py crops, osm_near.py / osm_seg.py lookups). Fixed + sent to lead: tunnels (Burnley Tunnel) no longer painted (prep skips tunnel/underground/covered in linear paint + tree clearing); AFL ovals (prep -> data/<g>/prep/ovals.json, 200-1500 m from centre; scene builds AFL Laws lines 10 cm draped per <=3 m piece + posts 12/6.5 m, no nets); building:part heights (fetch_parts.py -> data/<g>/osm_parts.json; prep adds parts to buildings). Paths: broadly match; AFL Way's blue streaks = sky-lit shadow on light path (render lighting, not paint).
- Open: Punt Road Oval surroundings (satellite construction site north of oval, ours lawn). Bridges over rail render very white; zig-zag white bridge near AAMI Park (~(-60,-560)) to check.

### Next
- MCG (11-20 14:30): orbit rebuilt on mcg_1843.glb (md5 8dcfd254). Seats now added like the game: proto/add_seats.py reads glb/mcg_seats/*.bin (origin/main bbeaa4b14), spec key seats_dir, hooked in scene.py after the GLB import (backup scene.py.bak_seats). Check render out/mcg/seatchk. Then: Jolimont rail yard from aerial (ballast, track pairs, sleepers, masts), footbridges, real facades, gate every 30th frame. Optus thin roof = SW 216-234 deg shortfall logged by the old builder (infallible-archimedes); texture session fixing.
- MCG rail yard done (15:xx): tex_track.py -> tex/track_bed.png (4.6 m bed, sleepers 0.68 m), raised rails, masts every 60 m (scene.py rails block); ballast palette 96,92,86; bridges concrete 158,156,150 + steel rails. Steep banks -> bg_banks box-mapped tex/bank_grass.png (only 186 faces; low-cam smear is not steepness, orbit never sees it). Check renders out/mcg/railchk. Next: plain-box buildings (Melbourne Park etc.), then full orbit + gate. Sessions all resumed after usage limit 11-20.
- MCG ~17:30: facades (tex_facades.py -> fac_brick/office/apart/clad, prep keeps kind/name, scene fam()), orbit 17:02 FAILED own gate (flat grey roofs, plain bridge slabs, flat grey car parks). Fixes: tex_bigroof.py -> tex/roof_big.png (48 m tile, flat roofs >1200 m2 use it; backup scene.py.bak_roofbr), tex_bridge.py -> tex/bridge_conc.png (bridges box-UV 12 m, mat_mul), prep _lots() paints car-park aisle/bay rows + 6 m plaza slabs (backup prep.py.bak_lots). Roofs+bridges verified in chk renders. Olympic Park grey = untagged ground_default: spec precinct_paved polygon (traced off aerial) -> prep paints it as 6 m slabs. Gate 11-20 ~18:00: Marvel orbit 17:03 FAILED (flat yard, dot-grid clone towers, flat roofs) and People First FAILED (stale model: main c96982c8e md5 3bd42451…, stripes on all open land, blotchy far land, check seats for crowd); both sent back. Use MSYS_NO_PATHCONV=1 for git show origin/main:path in bash. Check job out/mcg/job_chk.json -> out/mcg/chk/orbit_0XX.png. Then: full orbit (job_video.json), gate every 30th frame, show with "mcg_1843.glb md5 8dcfd254aa3d2bcefeecea443f5a1b74".
1. Landmarks (tower heights now from parts; hand-build over them): Eureka (-1662,-174), Australia 108 (-1713,-347), Rialto (-2257,128 / -2276,155), Arts Centre spire = OSM part "Spire" (-1320,-164, 162 m, renders as a prism now), Shrine (-880,-1162), Skipping Girl (2413,983). Find named reference photos first.
2. Bake procedural shaders to textures. Landmarks from named photos; Mt Gillen; re-render orbits; READY report.

### Gotchas
- Blender "unregister_class" traceback is harmless. Blender python has no PIL.
- Never `python -` with heredoc (REPL hang); write scripts to files; edits use newline=''.
- Bash blocks `sleep N; cmd`; use background runs.
- MedianFilter(31) on a 2800² image is slow (minutes).
- prep writes to data/<g>/prep/.
