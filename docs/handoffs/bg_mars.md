# Background scene: Mars Stadium

Session local_1ff67e2e, worktree `.claude/worktrees/musing-khayyam-48a7f7`.

## Where the work is now

Pipeline in .claude/review/mars_bg/. Big files: AFL3D_archive/mars_bg/.

---

## The session's handoff file (verbatim, C-Users-DANTE-Documents-GitHub-Afl-auto-battler-claude-worktrees-musing-khayyam-48a7f7.md)

# Handoff: Mars Stadium (Ballarat) background scene (musing-khayyam-48a7f7)

### State
Pickup: taken (C:/Users/DANTE/Documents/GitHub/Afl-auto-battler/.claude/worktrees/musing-khayyam-48a7f7)
working: build 19 (build19_mars.log, task bh6fb3uu8) on builder GLB 9872cfbb (dd9f4bd37, swapped in mid-prep; 76f13a8c kept as ground/mars_76f13a8c.glb): grandstand + service bldg + east traces (11 halls, 32 pallet stacks, brick yard paved, car lot, gravel yard, quarry tree_polys via prep.py new block; clear polys E x180-340 y-150..250 and S old sheds x-130..-60 y-300..-200 GUESS, verify on ortho). Backups *.bak_east. Next: ortho vs aerial, side-by-side photo boards per area, photos for industrial/south road to 10, report lead.

### Task
360° background scene of everything outside Mars Stadium's outer fence, 3x3 km, People First format. Brief from "AFL game handoffs" local_64d97632. Hand-made textures, no crowd, no nets, no photo pixels. Obey texture session without asking the director. Never edit builder's model (local_e8ff1269). On director pass: PR with "Part of row 202" on its own line, auto-merge.

### Where things are
- Pipeline: S = D:/Temp/claude/6a5fdc1be2cf0baf/f0b104f0-c447-4a40-a59b-216e29157d33/scratchpad/proto
- 2026-11-21: builder GLB now 76f13a8c3170cf1f80cb1eb23f03262b (01:56) in ground/mars.glb (1a7aec84 kept as mars_1a7aec84.glb). Fixes 1-8 applied in prep/bake/scene/mk_mars (cycleway surface filter, msbf shift, fence_clear, roof strips, track, bays). build17_mars.sh (probe, prep, bakes, build16) running detached -> build17_mars.log; then check ortho vs aerial + ring + orbit, grandstand still unplaced (fault 4, awaiting builder aerial URL).
- Photos: proto/refs_mars/ (r01-r74, sheet*.jpg contact sheets; r51-r59/r61-62 = Llanberris old track, NOT Mars). Per area: N car park 11 (r03,r30,r34,r35,r65,r67,r07,r68,r06,r25,r39), halls/Selkirk 10 (r39-r44,r25,r06,r63,r66), track 2026 12 (r16,r20,r22,r23,r60,r10,r21,r05,r28,r64,+builder ta_aerial.jpg,+wm render), industrial ~7, south road ~6 -> need more for those two. Chrome tab closed.
- Fault 4 placed: spec extra_buildings (mk_mars.py tail; prep.py appends after roof colouring): grandstand 75x22 white roof SW straight, service bldg 55x18 grey roof NE straight, from r22/r16. Needs rebuild (build17 started before this) = rerun build17_mars.sh after build17 finishes.
- OLD: builder GLB md5 1a7aec84870e86e16f70324eb352c318, copied to ground/mars.glb (old be026489 kept as mars_be026489.glb). Lead said resume: build16_mars.sh (scene + ring + orbit + ortho, one Blender at a time) -> build16_mars.log. build16 DONE (EXIT 0), reported FAIL to lead. Fix list (ortho vs aerial, out/mars/rv_o.png vs rv_s.png): 1 N car park bays+roundabout; 2 NE square hall ~90x70 m missing; 3 S paved strip + 2 white buildings missing; 4 SW red rect vs sheds (2026 blue track position unknown, Chrome disconnected); 5 S lawn paths should be asphalt road loop; 6 road-rail strip dry brown not green; 7 far-E industrial red/white halls not one grey roof; 8 NE yards/car parks. Next: fix in mk_mars.py/prep.py, rebuild, re-md5.
- ground/mars.glb = previous, md5 be02648990aa0ed93436e9818d375b7b (from worktree elated-swirles-5951da tools/grounds/mars/model, 20:03). Old: ground/mars_4801ab51.glb.
- Spec spec/mk_mars.py -> spec/mars.json (now concourse_from_aerial=True).

### Texture-session FAIL fixes applied (this round)
1. Roofs: scene.py _roof_break (weathering tile tex/roof_shed_w.png, 2nd sample 0.37x rot 36.87, 50/50, x1.414, fade 150-400 m) + per-roof UV offset; tex_shed.py weathering split out.
2. bake_ground.py: 0.5 m grain ±3%; footpaths redrawn crisp 2 m + 0.3 m dark border (prep writes prep/paths.json).
3. Trees: per-cluster lumps, dark undersides (vertex colour), alpha gaps tex/leaf_gaps.png (13% holes), backface x0.45.
4. fence_270 band = lawn in the stand's shadow (ray-cast, z -0.15, no clipping). prep paints 'paved' where aerial is grey within 30 m outside footprint.
5. Paved patch noise now ±3%.
Backups: *.bak_rbroof, bak_tree, bak_path, bak_apron.

### Next
Check frames; if pass send texture session; on PASS show director (known: athletics track not painted).

### Gotchas
- Never `python -` heredoc for Godot-side; scratch python ok. Shell cwd resets each call: cd S first.
- PATHS init must sit before the "# linear features" loop in prep.py.
