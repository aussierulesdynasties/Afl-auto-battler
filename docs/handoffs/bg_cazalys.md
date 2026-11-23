# Background scene: Cazaly's Stadium

Session local_4821b85c, worktree `.claude/worktrees/elegant-rosalind-d08c36`.

## Where the work is now

Pipeline in .claude/review/cazalys_bg/. Big files: AFL3D_archive/cazalys_bg/. No orbit film yet.

---

## The session's handoff file (verbatim, C-Users-DANTE-Documents-GitHub-Afl-auto-battler-claude-worktrees-elegant-rosalind-d08c36.md)

# Handoff: Cazaly's Stadium background scene (elegant-rosalind-d08c36)

### State
Pickup: open
Usage limit hit 2026-11-21. Next: rooftop solar on ~15% houses, fix yard ground bake (near-white), verandas,
then await builder pass of 972faa75, ring_cams.py, final ring+orbit30, photo boards (3/part), PR 'Part of row 202'.
NEW GLB in place: proto/ground/cazalys.glb = 19e0266b (PR #1898, not passed yet), md5 972faa75c1ba589123c4a0a6a43dce5c. Rerun ring_cams.py before ring render.
Photo rule now 3 clear photos per part + MATCH/FAIL side-by-side (was 10).
Last check (chk3.png, old GLB) passed palms + cars. Testing: lipstick palms
(grey trunk + red crownshaft only, wider fronds; global name TRUNK clashes, mine is PTRUNK), new 5-ring cars. Output stacked
to S/chk3.png. Canopy underside checked OK (no white wedge). Houses: eaves + glazed facade cells + yards (driveways/fences, 'bg_yards') built (scene backups ../scene_v12a/b.py).
Aerial board S/yards_board.png (job_yards, ortho 200 m at 415,-262) rebuilt: roofs light metal MATCH, driveways grey MATCH;
still FAIL: NO rooftop solar (~15% of houses on aerial), yard ground baked
near-white instead of dirt/grass mix (bake/aerial_paving issue). No verandas yet.

### Task
360° bg scene (3x3 km) around Cazaly's, outside the fence. Lead local_64d97632. Obey texture session local_85df280c.
Never edit ground model. No crowd. PR "Part of row 202", auto-merge on green.
New proof rules (2026-11-21): >=10 photos per area (canopies, car park, Mulgrave Rd, houses, rest) with counts in the
table, AND a side-by-side board per area: render from the photo's angle next to the named photo, regions MATCH/FAIL.

### Where things are
- S = D:/Temp/claude/bc8b0dd212458270/fd779ef0-41a7-4714-ad51-5cba401d7797/scratchpad; pipeline S/proto
- Rebuild: SKIP_PREP=1 JOBS="..." bash S/proto/rebuild_cz.sh. Jobs in proto/out/cazalys/job_*.json (ring, orbit30, chk).
- GLB: proto/ground/cazalys.glb (copy). ring_cams.py places ring cams from GLB bounds (+15 m); ring_000 z raised to 22.
- Solar: data/cazalys/prep/solar.json (11 traced quads); scene.py solar block = module grid 1.0x1.7 m, 0.9 m mono pitch,
  rafters per post. Car park under it = convex-hull 'parking' paint_poly (6,640 m2) in spec.
- House palette (spec palette roofs_house/walls_house) now metal roofs + weatherboard, from Bungalow photos.
- Backups: ../cazalys_spec_v11f.json, ../scene_v11e.py, ../job_ring_v11e.json.
- Reference photo grids (Google Images screenshots): S/refs_cz (14 grids: canopies ~12, aerials ~12, Mulgrave ~10+, houses ~15).

### Next
1. View check frames (solar_chk, solar_under, ring_045): canopies vs Portagrid/Cazalys photos, house roofs vs Bungalow photos.
2. Get new GLB md5, copy, rerun ring_cams.py, render job_ring + job_orbit30 (one Blender at a time).
3. Side-by-side boards per area (crop individual photos from refs_cz grids, match camera), MATCH/FAIL lists, table.
4. Send to texture session + lead; PR.

### Gotchas
- rebuild_cz.sh greps output: errors other than "Error:" lines are hidden. Query blend directly if unsure.
- TaskStop on the bash wrapper leaves the Blender child running: kill own PID after.
- Google image URLs are blocked from JS; save photos by zoom screenshots (save_to_disk).
