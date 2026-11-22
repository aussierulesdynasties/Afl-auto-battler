# Adelaide Oval background scene

Session local_a8ffb4e8, worktree `.claude/worktrees/great-bouman-17e048`.

## Where the work is now

Pipeline in .claude/review/adelaide_bg/. Big files: AFL3D_archive/adelaide_bg/.

---

## The session's handoff file (verbatim, C-Users-DANTE-Documents-GitHub-Afl-auto-battler-claude-worktrees-great-bouman-17e048.md)

# Handoff: Adelaide Oval background scene (3 x 3 km)

### State
working: build16 (bg task bg03m57oi, build16.log) = build15 (saved 23:47, towers 151, 240 frames, mp4 18f303ac, glb e9e6c618) + green practice strip (spec turf_strips [-227,-57,-144,-30], scene.py bak_strip). build15 frames: oval2 tan+square OK; strip missing -> fixed in build16. NEXT: check every 30th frame of build16, fill S/measure_table.md, send orbit+md5+table to plan session local_a479dc03 and orbit+frames to texture session local_85df280c.
(was:) working (side session of local_a479dc03; nothing committed, all work in scratchpad)

### Task
Background scene around Adelaide Oval (outside the outer fence, 3 km square), MCG proto pipeline. Director chose the model: commit 29d16d09f PLYs (branch claude/hungry-mcclintock-2e2ab8), 2026-11-20.

### Where things are
- Scratchpad: D:/Temp/claude/b012626c2f559e8f/6855d913-d54b-43b8-92a6-1e4e1b34589b/scratchpad
- proto/ = copy of the MCG pipeline; build.sh cd path fixed; spec/adelaide.json (origin -34.915489777922076, 138.59627692467532 = the model's own origin; trim_base ["ground"]; model_blend ../glb/adelaide.blend)
- glb/adelaide.glb + adelaide.blend made by proto/mk_ao.py from ao/.claude/review/adelaide/model/*.ply (shade.py materials kept)
- scene.py patched: spec.model_blend appends the model from the .blend (backup scene.py.bak_ao)
- out/adelaide/ has job_stills/map/ortho/video copied from MCG
- data/adelaide/photos: p4 = "Adelaide skyline, December 2022" (CC BY-SA 2.0, camera -34.917687,138.595136, drone, south view)

### Next
1. DONE: build with grass trace (prep/grass.npy, director "Trace grass") + canopy + OSM relations; out/adelaide/map/board_grass.jpg matches sat well. Open faults: Adelaide Oval No.2 (tan in sat) renders green; tennis courts blue missing; gray ground in residential blocks where sat shows roofs
2. fence ring jobs (8), map, sat_fetch + ovl, texture stddevs, 3 photo overlays (candidates: panoramio skyline -34.913314,138.594031; New Adelaide Oval 5351532715; Silhouetted at Sunset 16645913660; Across the Torrens), orbit video via video_mcg.sh pattern
3. Report to director with every frame self-checked

2. DONE (build6): spec water_tex (prep.py tiles tex/adl_torrens_water.png over PAL water px) + house_wall_tex adl_bluestone tint 88,92,98. Director via lead 11-20: comply with texture session, no texture questions to him.
   Faults seen in stills: oversized flat grey generic boxes S/E of oval (check vs sat), grey paved spread around oval, Oval No.2 green
3. IN PROGRESS: subagent porting Optus surf.py etc (texture session's 7 points). Newest model (main 0499df6cb, PR #1856, instanced seats) built by proto/mk_ao2.py into S/glb_new/ (glb md5 a8a78baad9156daf7c308021b2d78186, blend 13e4ab6d032016984f0a84c63a672de4; source PLYs byte-checked against origin/main md5 (ao2 re-extracted with git cat-file: git archive CRLF-mangled the PLYs)): copy over S/glb/ after the subagent's build finishes, then rebuild. Lead: report model path/time/md5, send director nothing.
4. IN PROGRESS (2026-11-20 eve): own-gate faults on orbit 16:55 fixed in code, rebuild bg task (build11.log, then fence+street+fence270+video):
   - courts: slab = union of court boxes +1 m (prep _slabpolys), tessellate_polygon in scene; 4 NW Memorial Dr courts court_grass via paint_at (patch_courts.py)
   - towers/blocks: facade variants per building (tex_towers.py adl_conc/fin/band + peer city_office/city_far) (patch_towers.py)
   - model base sawtooth: exact boolean INTERSECT with prism of data/adelaide/prep/fence_outline.json (fence_outline.py from fence_mask.npy, skimage) (patch_trim.py, patch_noshp.py; Blender has NO shapely)
   - fence_270 cam now (0,-223.8,30)
   - plan-session gate FAIL 16:55 mp4 also fixed: oval2 60 m patch multiplier (tex_patch.py adl_patch60) + cricket square (spec cricket_squares), red roof (-121,-197) tile + solar arrays (roof_col_at kind/'solar', adl_solar.png) (patch_ov2roof.py); dark curved wall = stadium model, told plan session
   - RESUMED ("resume all"): bdiilv82q stopped (old model). glb/adelaide.glb = westback md5 e1687b6a; adelaide.blend 4457806d = old blend with only 'stands' swapped from glb (proto/mk_westback.py; swapping all meshes wrongly replaced triangulated copies). build13 crashed silently before SAVED (likely OOM; renders then used stale 15:16 scene.blend!). Rerun saved 20:37; orbit 20:40 mp4 md5 dde77e8fdced6e1a4b6a9b400a516669 passed own 30th-frame gate; sent to plan + texture sessions. ALWAYS check scene.blend mtime / SAVED line before rendering
   - plan gate FAIL dde77e8f: oval2 must be grass (tex_cbd.py adl_oval_grass.png 48 m) + towers plain -> tex_cbd.py cbd_curtain/punched/stone/fins/ribbon (6x3.6 m, multiply palette colour) + roof plant box (patch_cbd.py, backup scene.py.bak_cbd). Texture session FAIL too: added west_concourse (mk_westback2.py, blend b72a4da6), cricket square = pale oval grass, spec paint_poly lawn around oval2 (patch_turf.py, spec bak_turf). Stand white faces: told texture session it's theirs (model). THEN texture session sent adelaide_es2.glb md5 e9e6c6187d67ee0c532b00d6063bdd9d (whole glb, keep its materials): glb/adelaide.glb = it; blend 8ee4d28c = bak_westback + every glb mesh swapped/added (proto/mk_es2.py). Rebuild (build14.log) running. Then check 30th frames, send plan md5s; apply any stand-face model the texture session sends
   ON RESTART FIRST: swap in texture session's new model D:/Temp/claude/2117a0e07442304a/b457f311-065b-4525-9ffd-7c62765dd586/scratchpad/adw/adelaide_westback.glb (md5 e1687b6a2ce9b329282dea930050cc4a (replaces e2ff39a4); west stand back repainted, material west_back alphaMode MASK = arch cut-outs + recess: check Blender import keeps alpha clip, md5-match before rendering) -> copy to S/glb/, remake adelaide.blend, rebuild, orbit; send orbit to texture session. bdiilv82q output is on the OLD model (a8a78baa): don't report it as final.
   Next (after restart): check every 30th frame + fence/street sheets at full res; then plan session gets mp4 path + md5s, texture session gets orbit + sheets.
### Peer textures (texture session local_85df280c; send it path+sheets+street close-up before director)
- D:/Temp/claude/2117a0e07442304a/b457f311-065b-4525-9ffd-7c62765dd586/scratchpad/bgtex/mt/ (asphalt, corrugated roof, far tower)
- .../bgtex/adl/: adl_bluestone.png (256px=3.6x3.2 m, grey multiplier, tint ~(88,92,98), alpha_mode NONE), adl_torrens_water.png (512px, ~40 m/tile, ripples along V)

### Gotchas
- upload.wikimedia.org returns 429 to scripts; retry slowly or use the browser
- the model's ground.ply is a +-3 km lawn: trimmed by trim_base/fence_mask in scene copy only
