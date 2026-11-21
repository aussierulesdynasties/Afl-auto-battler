# Resume player heads (row 202 2d)

Session local_b4d6314a, worktree `.claude/worktrees/broadcast-popups-9a47e0`.

## Where the work is now

All code and heads are on PR #1967 (branch claude/builds-faces-2d). Review films in .claude/review/player_heads_wip/. Next session restarts from the transfer step (reuses the Unreal export, skips ~17 min). Unreal crashed at the end of its export: restart it before any full run. Big local data stays on disk: D:/AflMH and the session scratchpad D:/Temp/claude/71e0fb0627f52c30/ (21.6 GB).

---

## The session's handoff file (verbatim, C-Users-DANTE-Documents-GitHub-Afl-auto-battler-claude-worktrees-broadcast-popups-9a47e0.md)

# Handoff: worktree broadcast-popups-9a47e0: row 202 2d heads (branch claude/builds-faces-2d) + row 207 popups

### State
Paused by director (memory low), 2026-11-20. Chandler run7 stopped after conform (1160 s); Unreal export is reusable, rerun from transfer2 onward. Unreal MCP connector registered (local scope).
Pickup: taken (this folder). clean_head.py fixes (bak11/bak12): hair cap built from pre-strip head (bald crown fixed, cap 1 island); weld bridge faces take one ring point UV (scalp red square gone: red texels in tris 764719->5975). run6 in background -> D:/AflMH/Work/chandler/g/run6.log; then check look_back/backl, film.
awaiting next session (usage limit). Chandler neck fix in progress; director: "KEEP WORKING UNTIL ITS FIXED".
- clean_head.py strips leftover guernsey below ZCUT+0.22*HT (his instruction; bak10 = before).
- Fit trial OFF=0.03 (cut 3 cm higher) squeeze x0.89-1.30; not approved as a rule yet.
- Unreal fixes: make_head.sh opens /Game/cross first (p0_level.py); p5.py imports into scan_<time> folder and
  raises if no mesh (bak1). Restart: start.sh, then sid.sh if session empty.
- Latest run (OFF=0.03 BAND=0.10) exit 0, FOLDS 414, but look board D:/AflMH/Work/chandler/g/look4.png shows a BALD
  crown (hair stops jagged above ears) + red still at back-right neck. Clean cap line 0.8 same as old runs, so
  bald comes later: check Export/conform/chandler_scan.glb crown (my render framing was off). Prior good head:
  D:/AflMH/Work/chandler/g/MEL_37_prev.glb (assets MEL_37.glb now = bald one, TEMP; restore prev if needed).
- fit_head.py TRIAL env code (MATCH, OFF, HDBG): strip before commit. Branch merged main, not pushed.
- Lohmann parked: textured Tripo file is 100x size.

### Task
- Row 202 2d: Tripo heads onto the MetaHuman body by the MetaHuman method; one script for hundreds of players.
- Director's newest: "you need to make this a Skill ... it will tell them every step" -> DONE:
  .claude/skills/afl-head-pipeline/SKILL.md, commit a3f456f8b pushed. READ IT: it holds every step, log lines,
  self-checks, film command, known faults. Keep it current when the chain changes.
- Director then: Dees batch (27 Melbourne players, S/refs/todo.txt, not May/delisted). Done: van Rooyen raw head,
  Salem raw head. Paused for the pipeline proof.

### Where things are
- Chain: bash D:/AflMH/Scripts/make_head.sh <name> <pid> <raw glb> (clean -> Unreal conform -> transfer2 -> despeck ->
  mh_head_src -> fit_head -> look). mkmp4.sh now durable at D:/AflMH/Scripts/mkmp4.sh.
- clean_head.py fixed today (backup .bak8): clothing test any colour unlike skin; grows up the collar through
  jumper-coloured faces; deletes them (collar-following cut); peels rims; drops loose collar scraps; STOP if
  shoulders on or eyes not found; eye line from eye whites when no eye pieces. Chandler: clothing 1983, cut 0.457,
  eye whites 144. Clean board D:/AflMH/Work/chandler/cl2_board.png good (tiny red loose-piece speck back right of neck).
- Backups: D:/AflMH/Work/chandler/MEL_37_before.glb, heads_before.json. Cross in game = MEL_41 (cross2, split band).
- S = D:/Temp/claude/71e0fb0627f52c30/f4402a99-2872-4795-a1c4-2a61a661e66f/scratchpad (films fc, fn, fd; boards).

### Unfinished changes (uncommitted)
- tools/oval3d/heads/fit_head.py (BAND 0.06 shape, SKIN_BAND 0.02 colour) and oval3d_head.gdshader (colour by
  COLOR.g, bend max(r,g)): commit once Chandler's film passes.
- TEMP, never commit: capture_builds3d.gd FOLLOW/CLIP/SUN_ANGLE/SHADOW_DIST; Oval3D.gd HEAD_SSS; socket.json jaw
  socket and MEL_11/41/15 + heads.json (originals S/collar/bak; restore before any commit). Never commit media,
  .import noise, stray .uid, wrap_head.py, this handoff.
- PR #1784 (bound, auto-merge) holds earlier socket work.

### Next
1. When run2 finishes: read every log line (clean/CHECK), view D:/AflMH/Work/chandler/look_*.png; godot --import;
   film FOLLOW=MEL_37 (skill step 4), check every frame, send mp4 + times.txt.
2. Report to parent (local_64d97632) leading with skill commit + Chandler result.
3. Find Windsor's scan (director says it exists; not in D:/AflMH/Heads).
4. Resume the Dees batch through make_head.sh.

### Open questions for the director (ask in the box, one at a time, with pictures)
- Jaw line when standing still = lighting (Mobile renderer ignores SSS). Proposed soft "wrap lighting" on head skin
  ((N.L+w)/(1+w), w=0.3 -> 23% light side-on). No OK yet; earlier box was dismissed by his message.
- Hair looks smooth at game distance: maps-off test changed nothing; next lead sub-pixel strands/mipmaps. Tell him.
- Head ~5% too big: per-head vs global, ask with pictures later ("dont alter head size for now").

### Gotchas
- Godot --script films the OLD import: run --headless --import after every head rebuild.
- python -P (D:/AflMH/Scripts/inspect.py shadows stdlib). Python edits newline=''. Times in Melbourne.
- Windowed Godot only via C:/kt/gpu_slot.sh; never kill others' Godots.
- Unreal: launch line + MCP sid in the skill; console "Select" = ask him to press Esc.
- Blender logs always show a harmless BlenderMCP unregister_class Traceback.
- show.py: red = loose piece, yellow = open edge (not jumper).
- Close Chrome tab 1639214608 when done with Tripo.
- Row 207 popups: available; next asks one at a time (card timing, score bug vs scoreboard, journalists' posts).
