# Stranded work in progress (audit of 2026-11-23)

This folder holds work that existed only on the director's PC and was never on main or on any GitHub branch.
It is saved here so main shows what exists. **Nothing here is wired into the game.** Each item is a patch or
a copy of files. Apply a patch only after you have checked it against today's main. Each item still needs its
own TODO row and its own PR before it plays.

Every source worktree is still on the PC, untouched. Nothing was deleted.

| Folder | Where it was | What it is | Notes |
|---|---|---|---|
| `kick-lanes/`, `kick-lanes-reach6-uncommitted/`, `kick-lanes-simonly-uncommitted/` | `.claude/worktrees/sleepy-allen-7aa947` (2 commits); worktrees `v_reach6` and `v_simonly` (uncommitted; the two diffs differ slightly, so both are kept) | Row T2.25 kick lanes: the game plan picks corridor, switch or down the line, logged per kick; the view draws each lane | TODO row T2.25 says this work is on `origin/claude/kick-lanes` and `claude/kick-lanes-cal`. Those branches are gone from GitHub, so these patches are the only copy. |
| `hub-events-first/` | `GitHub/afl-hub-events-first` (3 commits, 2026-10-19) | Hub round screen: story cards first, league news in club colour | About 7% of its lines are on main. |
| `press-full-screen/` | `GitHub/afl-press-full-screen` (4 commits, 2026-10-19) | Press conference as its own full-screen scene | About 16% on main. |
| `preseason-cards-774/` | `GitHub/wt-prestory` (3 commits) | Pre-season story cards, row 39 slice 5 (closed PR #774) | About 56% on main through #818 and #1359. |
| `forge-back-fresh-launch/` | `C:/kt/combo` (uncommitted, 14 files) | Forge Back button on a fresh launch | No PR. |
| `legacy-1990-ratings/` | `C:/kt/r6_leg_rate` (uncommitted, 7 files, plus `rate.py` and 1990 CSVs) | 1990 Legacy ratings work | Main took a different route (#1327, #1536). |
| `needs-a-lift-zero/` | `.claude/worktrees/wf_0035eed3-312-1` (uncommitted) | Coach report "Needs a lift" fix | #1552 merged a version of this. |
| `redraft-tasmania-2028/` | `.claude/worktrees/wf_d242ca4c-f6a-4` (uncommitted) | League redraft, Tasmania 2028 | #1559 merged a version of this. |
| `ruck-integrity/` | `GitHub/afl-wt/ruck-integrity` (untracked) | `afl_ruck_splits.json` (real AFL ruck splits) and `build_ruck_splits.py` | #1121 merged the harness section; this data file never landed. |
| `row121-load-screen-flair/` | `.claude/worktrees/wf_8de82fd3-174-5` (untracked) | `capture_load_screens.gd` capture tool | #1211 merged the feature. |
| `quarter-swing-audit/`, `ai-draft-audit-2/` | `GitHub/afl-swing`, `wf_a5cbff06-ada-1` | Measurement-only audit scripts | No sim change. |
| `break-streamline-audit/` | `GitHub/afl-breakaudit` (26 commits) | Break-screen prototype layouts A and B, marked "local only, throwaway" | Kept as a record only. |
| `vignette-start-stutter/` | `GitHub/afl-vignette-start-stutter` | 2D banner-scene stutter fix | 2D only, which is dead (rule: 3D only). Kept as a record only. |
| `context-trim/` | `Afl-auto-battler-wt/context-trim` (uncommitted) | `open-requirements-archive.md` | Old roadmap tidy. |
| `heads-stash/` | main checkout, `stash@{2}` "heads-premerge-9a47e0" | Text diff of the head-fitting WIP (`fit_head.py`, `socket.py`, shaders) | Binary heads (`MEL_*.glb`, `player_mh.glb`) are not included. They are MetaHuman-derived and stay off the public repo. |
| `storylines-stash/` | main checkout, `stash@{7}` (October) | `STORYLINES.md` draft | Story content needs a director interview (rule 47) before any use. |
| `gmhba-bg-scratch-rounds27-31/` | `D:/Temp/claude/5e6b242a6aee39ff/9a1244aa-.../scratchpad` | GMHBA background-scene session scratch: Geelong facade research and round 27-31 scripts | Not in #1969 or #2023. |

## Large 3D leftovers (kept on the PC, not in git)

Model files, blends and reference images from the 3D worktrees were copied to
`Documents/AFL3D_archive/worktree_leftovers/<worktree>/`. That is 675 files and 1.05 GB. Each folder has a
`MANIFEST.txt` with md5 and size. These are earlier model iterations and texture-pass intermediates. Each
ground's final model is on main. Several files are too large for git: the MCG `mcg.glb` from `gifted-cori` is
176 MB. Orbit frames, render logs and mp4s were not copied.
