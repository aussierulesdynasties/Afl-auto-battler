# Optus Stadium background scene

Session local_3b624783, worktree `.claude/worktrees/fervent-mccarthy-465d6c`.

## Where the work is now

Pipeline in .claude/review/optus_bg/ (latest/ added). Big files: AFL3D_archive/optus_bg/.

---

## The session's handoff file (verbatim, C-Users-DANTE-Documents-GitHub-Afl-auto-battler-claude-worktrees-fervent-mccarthy-465d6c.md)

# Handoff: Optus background scene (row 202 2b)

### State
available (no job live). Close-up faults 1, 2, 4 fixed and rendered (out/optus/out/optus/fc/*.png 01:42). Fault 3 open:
south edge is a straight cut to lawn at y~-40 (real: terraced planter steps x140-170, stair, hut, paths, car-park
turnaround; trace from data/optus/sat_hi_south.png). Old canopy trees stand on the east carriageway (x~249): fix with fault 3.
Roof: HOLD renders until the texture session (local_85df280c) sends the 50-bay md5; ask again right before rendering.
- Plan session said: go ahead; send nothing before READY unless blocked; don't gate f2f2080d-roof renders.
- Fix 2 DONE: prep.py one tree per z19 crown (distance-transform peaks, r>=1.5 m, dark or dark-green canopy; kiosk
  slabs excluded, planters allowed): 27 crowns -> data/optus/prep/plaza_crowns.json (x,y,r). Check image _crowns.jpg.
- Fix 1 DONE: fc_scene.py kiosks measured on E37_017 (1.75 m person = 43 px/m): roof top 5.2 m, fascia 1.1 m, walls
  warm grey 2 m inset to 4.1 m, LED screen 12 x 3.4 x 4.4 m from the z19 patch. Backups fc_scene.py.v1/.v2.
- Fix 4 OPEN: a dark speck remains on the paving near its south edge (fc_near ~1250,395).
- Blender has no PIL: read images via bpy.
- New rules 2026-11-21: >=10 Google Images/Street View photos per area; one camera-matched board per area (render vs
  photo, filename on it, MATCH/FAIL per region: structure, shape, counts, colour, material, signage); photo counts in report.
- Plan session wants: kiosk height measured from photos; one tree per z19 crown (count in table); south trace p90; zero specks.
- Texture session registration of Google z19: .../b457f311-.../scratchpad/gsat/reg.json p=[ox,oy,m/px,rot rad].
- build.sh hides scene.py errors (tail -3): run scene.py directly to see tracebacks.

- Fault 3 p90: three automatic measures failed (gradient 2.0 m everywhere; Canny chamfer 0.38 m, but a 7 m shift scores 0.40;
  Lab-contrast snap zig-zags the outlines). spec restored from .v5. Asked the plan session whether to correct by hand and
  measure p90 on hard edges only.
  PLAN SESSION ANSWERED (yes, plus extras):
  - Hard edges: p90 ≤ 0.75 m against hand-picked points; list each edge's p90 and point count.
  - Soft edges: zoomed crop of the model outline over z19, next to a ground photo, called MATCH/FAIL.
  - Cross-check the soft edges on the second-date Google z19.
  Hard-edge tool:
  - `_zg.py x0 x1 y0 y1 out.jpg` makes a gridded zoom (1100 px wide; pixel to metres: x = x0 + px/s, y = y1 − py/s).
  - Picked points go in `_hardpts.json`; `_hp.py` gives each edge's p90.
  - Done so far: ramp SE p90 0.66 m (5 points), ramp SW 0.10 m (5 points).
  - Stair (polygon 11) re-traced on a 45.8 px/m crop (_zg_st2.jpg); its south-west corner was 2.7 m off. Now SE edge
    0.21 m and NW edge 0.05 m (5 points each).
  - Road (polygon 6): the upper part is moved about 2.5 m east onto the west kerb, now 0.06 m (4 points, from _zg_road.jpg).
    Its east edge is the canopy line, so it's a soft edge.
  - Mound (polygon 8): re-traced along the road's east side; its south edge moved to the car park's north kerb (y −101).
  - Car park (polygon 9): north kerb moved about 5 m south (was 4.86 m off, now 0.11 m); south kerb now 0.08 m. Measured
    on _zg_cp.jpg.
  - Next: the plaza and terrace-wall edges. Check the grey strip at x 213–222, y −95..−101 (looks like paving, but the bed
    base covers it).
  - Plan session: send nothing until READY or a blocker, and don't acknowledge its messages.
  Texture session: the roof isn't final (arches, X cables and HALO still to build). Never render on h50/7372fc47. Scripts: _p90.py, _cham.py, _ctr.py, _csnap.py, _snap.py.

### Task
Plan session (local_a479dc03) failed orbit 011a0bbd (forecourt camouflage). Fix: plaza tone fields traced from the
aerial, hand paver texture, planters at aerial positions, all outside the fence, no crowd/nets. Plan session asked:
kiosks re-traced (done), dropped lawn/bed/canopy built by their own layer (done), send close-ups when they land.
READY = mp4 md5, stadium/roof md5, measured table, overlay error.
Roof: optus_roof7.glb md5 1278690b... (texture session local_85df280c; asked for the final md5, no reply yet).

### Where things are
- Proto: D:/Temp/claude/14b1484a65bfbd74/76476bc6-b87c-4245-8ecb-61de5d49956b/scratchpad/proto
- spec/optus_fc_hand.json: 14 bands (12 paving, 2 kiosk concrete), outline, 5 planters. Backups .v1/.v2/.v3.
- fc_overlay.py (backups .v7-.v10): bbox pad 10 m; outline governs x>=90, y>=-40; vegetation fill block (lawn if
  patch >= 25 % open lawn, else mulch [74,58,44]); kiosks/planters excluded; fence ellipse clip.
- Checks: _topchk.py (aerial | model top-down + fence px), _dropchk.py (_drop_0..3.jpg contact sheets), _kerr.py,
  _perfield.py. optus_measured.md updated.
- ../glb/optus.glb still f2f2080d: swap in the final roof glb before the orbit.
- PR #1897 (draft, auto-merge on), branch claude/optus-bg-scene.

### Next
1. Check close-ups out/optus/out/optus/fc/*.png against z19, whole and zoomed; send paths to the plan session.
2. Final roof md5 -> ../glb/optus.glb, verify md5, rebuild, orbit (video_mcg.sh, _crop.py), check frames.
3. READY to the plan session; paths to the texture session; copy files into PR, push, mark ready.

### Gotchas
- Bare `blender` not on PATH in bash: use the full Blender 5.2 path.
- Never `python -` stdin; kill own jobs by PID/task id only; hand textures only, aerial is reference.
- Outside the outline the terrain 'ground' class is flat salmon (clsfy) - visible north of the plaza; not plaza scope.
