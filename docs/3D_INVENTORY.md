# 3D inventory (2026-11-21)

Everything 3D that exists, and where it lives. Searched: main, open and closed PRs, every worktree under
`.claude/worktrees`, the sibling folders in Documents/GitHub (land-*, afl-wt-gabba-rescue, afl-stadium-viewer,
3d-game-test), the git stashes, the session scratchpads under `D:/Temp/claude`, Downloads and Desktop.

"In a match" means the ground's model sits in `assets/grounds/<slug>/` and `GroundModels.gd` loads it on match day.
No background scene is in a match yet.

Big files that git cannot hold (scene_bg.glb, scene.blend, over 100 MB) are copied to
`C:/Users/DANTE/Documents/AFL3D_archive/<ground>_bg/` on the PC (6.8 GB). Each `.claude/review/<ground>_bg/`
folder has a `MANIFEST.txt` with the md5 of every big file left behind. Session notes: [handoffs/](handoffs/README.md).

## Grounds

| Ground | Stadium model | In a match | Background scene (surroundings) |
|---|---|---|---|
| MCG | main (#1843); exterior seats and gates PR #1917 | yes | pipeline + orbit f8a92e5e in `.claude/review/mcg_bg` |
| Marvel Stadium | main (#1911) | yes | pipeline + orbit eefd5806 in `.claude/review/marvel_bg` |
| Adelaide Oval | main (#1856) | yes | pipeline + orbit 8c6dbe8d in `.claude/review/adelaide_bg` |
| Optus Stadium | main (#1867 #1880) | yes | on main (#1897) + newest in `.claude/review/optus_bg/latest` (orbit 011a0bbd) |
| SCG | main (#1909) | yes | none |
| GMHBA Stadium | main (#1903); Selwood Stand roof PR #1924 (held for the lead's gate) | yes | on main (#1878) + newest in `.claude/review/gmhba_bg/latest` (orbit ec22c456) |
| People First Stadium | main (#1853 #1860 #1868 #1889) | yes | on main (#1892) + newest in `.claude/review/peoplefirst_bg/latest` (orbit 86d6add9) |
| ENGIE Stadium | main (#1866) | yes | none |
| Bellerive Oval | main (#1900) | yes | none |
| Manuka Oval | main (#1865) | yes | none |
| Norwood Oval | main (#1870) | yes | none |
| Waverley Park | main (#1902) | yes | none |
| Windy Hill | main (#1885) | yes | none |
| Moorabbin Oval | main (#1910) | yes | none |
| Ikon Park | main (#1852) | yes | none |
| Whitten Oval | main (#1882) | yes | none |
| Football Park | main (#1886) | yes | none |
| Subiaco Oval | main (#1901) | yes | none |
| York Park | main (#1855) | yes | none |
| WACA | main (#1864) | yes | none |
| Cazaly's Stadium | main (#1891 #1898) | yes | pipeline in `.claude/review/cazalys_bg`, no orbit film yet |
| North Hobart Oval | main (#1854) | yes | none |
| Bruce Stadium | main (#1848) | yes | none |
| Riverway Stadium | main (#1896) | yes | pipeline + orbit 3557935f in `.claude/review/riverway_bg` |
| The Gabba | main | yes | none |
| Barossa Park, Sky Stadium, Jiangwan, Hands Oval, Blacktown, Summit Park, Macquarie Point | main (`tools/grounds/<g>/model`, game export) | yes | none |
| Mars Stadium | PR #1920 | no (until it merges) | pipeline + orbit e46d7c95 in `.claude/review/mars_bg` |
| Accor Stadium | PR #1921 | no (until it merges) | pipeline in `.claude/review/accor_bg`, no orbit film yet |
| Traeger Park | PR #1919 | no | pipeline + orbit 478e87bb in `.claude/review/traeger_bg` |
| Marrara Oval (TIO) | PR #1918; research in `tools/grounds/tio_darwin` | no | none |
| Victoria Park | texture pass PR #1884 | no | none |

## Other 3D areas

| Area | What exists | Where |
|---|---|---|
| Crowd | 3D people near, cards beyond; seated on the MCG's own seats | `Oval3DCrowd.gd`, `Oval3DCrowdSet.gd`, `assets/oval3d/crowd_set.res`, `supporters/` (#1929) |
| Players' bodies | MetaHuman body, builds by height and weight | `assets/oval3d/player_mh.glb`, `player_mh_builds.json`, `Oval3DBuild.gd` |
| Players' heads | fitted heads, skin light; newest work saved | `assets/oval3d/heads/`; PR #1967 (not gated); review films `.claude/review/player_heads_wip` |
| Hair | hair styles model and textures | `assets/oval3d/hair_styles.glb`, `hair_tex/` |
| Turf | per-ground mowing cut and grass, markings from the ground's size | `Oval3DTurf.gd`, `assets/oval3d/turf/`; Adelaide and Gabba turf PR #1962 |
| Cameras and broadcast | main camera, replays, set shots, score bug, stat bars | `Oval3D.gd`, `Oval3DBroadcast.gd`, `ScoreBug.gd` |
| Ground screens | big screens | `Oval3DScreens.gd` |
| Sky, light, film look | sky shader, sun, film look | `oval3d_sky.gdshader`, `oval3d_film.gdshader`; sun PR #1928 |
| Umpires | drawn by the match code | `Oval3D.gd`, `Oval3DBuild.gd` |
| Animation | player loops, tackle pairs (placeholders: 93 clips come from Unreal-only GASP) | `assets/oval3d/player_loops.glb`, `tackle_pairs.json` |
| Stadium viewer (desktop) | standalone viewer of the ground models | `Documents/GitHub/afl-stadium-viewer` (local edits in stashes 0 and 1) |

## Stranded or local-only work

- Background scenes for 8 grounds lived only in session scratchpads; now copied to `.claude/review/<g>_bg` (this PR) and the archive folder.
- Texture work in progress (Adelaide es2, GMHBA tex2, Optus roof 11 and h50 build): `.claude/review/texture_wip`.
- Stadium lead gate boards: `.claude/review/stadium_lead_gates`.
- Player heads WIP: PR #1967. Large local data stays on the PC: `D:/AflMH` and the session scratchpad (21.6 GB).
- Sibling folders land-bellerive, land-gmhba, land-marvel, land-moorabbin, land-scg, land-subiaco, land-waverley_park:
  every committed file is already identical on main; only their split-check review pictures are local.
- Old local-only glbs in the texture session's scratchpad (Bellerive, Gabba, Optus, People First) are older copies
  of models already on main.
