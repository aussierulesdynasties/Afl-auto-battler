# Background scene: Accor Stadium

Session local_5dca6420, worktree `.claude/worktrees/serene-agnesi-c2ff21`.

## Where the work is now

Pipeline in .claude/review/accor_bg/. Big files: AFL3D_archive/accor_bg/. No orbit film yet.

---

## The session's handoff file (verbatim, C-Users-DANTE-Documents-GitHub-Afl-auto-battler-claude-worktrees-serene-agnesi-c2ff21.md)

# Handoff: Accor Stadium background scene (serene-agnesi-c2ff21)

### State
State: working, rebuild 16 (task bpmv27x10, md5 3c0fa6a4, job_boards). Round-1 side-by-sides (out/accor/sbs_round1.jpg, mk_sbs.py) FAIL arena/Dome/station; notes accor_bg_boards_round1.md. Arena fixed (_p16.py: fitted oval, flat dark roof 24-28 m + 5 m drum, sloped eave 20->14 m, masts 50 m; backup accor_landmarks.py.bak16). Next: Dome cap/drum/annex blue boxes, station leaf ribs + brick plaza, re-camera arena_02/towers_04/annex_ground, round 2 boards.
Then: gate r15. Report needs per-part side-by-side boards (render from the photo camera angle next to the named photo, saved under refacc with source URL; each region MATCH/FAIL) per director ruling 2026-11-21 in side-session-notes/.../director_2026-11-20_research_precision.md. Send to lead; texture session local_85df280c frames.

### Task
360 deg 3x3 km background scene around Accor Stadium, outside the ground model's fence. Brief: session local_64d97632.
Obey texture session local_85df280c. Director sees only the finished scene. When passed: PR, "Part of row 202" own line, auto-merge.
New rule (director 2026-11-20, side-session-notes/.../director_2026-11-20_research_precision.md): many reference photos,
measured numbers, READY carries table measured vs model.

### Measured vs model (rebuild 8)
| Part | Measured (source) | Model |
|---|---|---|
| Boulevard light towers | 19 (aerial, each checked: out/accor/towers_board.png, north.png) | 19 (was 22 incl. a truck + duplicate base boxes) |
| Tower lean, cap vs base box | +6.4, +16.0 m (towers 9/10, 20/21) | foot = cap - (6.4,16.0) (was vertical) |
| Tower base box | ~5 x 5 m white (aerial) | 5 x 5 x 6 m (height estimated) |
| Tower PV canopy | 5 slats, ~12 x 9 m, beside cap (aerial) | 5 slats 12 x 9 m at 5 m |
| Tower height | not measured (no source) | 30 m |
| Plaza base colour | sat 143,124,116 | albedo 129,112,104 (was 138,96,80 brick red) |
| Buff cross-bands | ~11 m wide, every 39.5 m, square to boulevard (bearing -52.5) | 11 m / 40 m tile, rot -52.5 |
| Paver unit | 225 x 112.5 mm interlocking | 225 x 112.5 stretcher bond |
| Paving to stadium wall | paved to the wall (aerial) | cut at OSM wall line +1 m (was roof footprint: grass ring) |

### Where things are
- Pipeline: S=D:/Temp/claude/9cde8b3442051ee1/8e9d400c-05c9-4bcc-aeef-038762663b40/scratchpad/proto
- Refs: S/review/accor_ref (8 Commons photos, sources.txt). Satellite data/accor/sat.png 0.5 m/px, centre = origin.
- New: wall_accor.py -> data/accor/prep/wall.json; _towers_curate.py -> data/accor/towers_curated.json; scene.py _outside_wall + _drape rot; spec pave_tile_m/pave_rot_deg.
- align_accor.py: copies builder GLB (dazzling-margulis-e47fa0) -> ground/accor.glb; rerun on new md5, then wall_accor.py.

### Open faults (from rebuild 7 frames)
- Showground exhibition halls: plain grey roof slabs (f000, f090) - need hand-made ridged metal roof texture.
- Boulevard carriageway: real = charcoal lanes + buff cross-bands + white centre line; model = asphalt road.
- Merge origin/main before the director capture.

### Gotchas
- Never `python -` or `python -E -` with or without heredoc: it hangs (twice this session). Write a .py file.
- rebuild_accor.sh default JOBS omits job_video; use JOBS="job_video" (scene rebuild runs first).
- Never kill by image name; stop own task ids only.

### Faults from rebuild 9 frames vs Google Images/Maps 3D (2026-11-20 22:55)
- Qudos Bank Arena (NW, Edwin Flack Ave): model = glass/concrete octagon block; real = large grey ribbed oval roof.
- Boulevard towers: model = straight lattice + white box; real = zig-zag lattice mast, tilted square cap, pergola/stair base.
- The Dome (white ribbed dome) + Showground halls (pale ribbed barrel vaults): need geometry, check visibility in frames.
- Olympic Park station: overlapping curved shell roofs, missing.
- Gemini blocked by permission classifier; question to director pending.
- OSM positions (scene metres, _find_lm.py): arena ex-Qudos "Afterpay Arena" way 4987356 c(-134,304) 176x180; The Dome 35029897 c(434,148) 109x105;
  Olympic Park station 19003982 c(561,59) 214x117; pavilions listed by _find_lm.py. Plan: accor_landmarks.py via spec extra_py
  (landmarks.py helpers: find/wall_ring/cap/beam, drop generic box). Heights still need sources.
