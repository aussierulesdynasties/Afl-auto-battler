# The 3D view 1.0 release

_Started 2026-11-22 by the thread "Plan and track the 3D 1.0 release". Kept current as 3D work lands;
the project page "3D 1.0 Release Plan" (https://claude.ai/artifact/TMwVqWbwzX9xdTgrass7jv) shows the same list._

## The bar

The director, 2026-11-22: "i dont want to push 3D to itch until we have everything: grounds,
animations, players, presentation (camera angles etc)". No partial release, and no stand-ins
(project rule: "never a shortcut, never a placeholder, never 'good enough'").

An item is **passed** only when all of these hold:

1. It is on main.
2. Its owner has checked it against the real thing (Google Earth, real photos, real footage, real
   recordings) and fixed what it found (rule: art is checked before the director sees it).
3. It runs on a phone at Low, Medium and High inside the budget below.
4. The director has looked at it and passed it. For a ground that is his fly-through in the ground
   inspector, his fault list fixed, and his approval.

Nothing below is passed yet. On 2026-11-22 no ground has his approval (the Stadium DONE List holds
no reviews), and the MetaHuman footballer is not yet in a match on main.

How this page relates to the others: [3D_VIEW_PLAN.md](3D_VIEW_PLAN.md) stays the plan and its
rulings; this page is the release checklist built from it; `docs/TODO.md` rows 197, 198, 201, 202,
203 and 207 hold execution detail.

## Scope

- **All 37 grounds** (the director, 2026-11-22, on the decision card: "Yes, all 37 grounds"). Every
  ground a match can be played at, career or Legacy mode, is finished to the standard before 1.0.
  13 of them a 2026 career plays at (the 11 club homes and the two Gather Round grounds); the other
  24 only Legacy mode reaches. The career 13 go first because a new player meets them first.
- **Android and Windows carry 3D; the web build does not** (my call). The 3D grounds alone are about
  750 MB imported; a browser download that size is not a game anyone will wait for. The web
  build keeps the flat oval.
- Off the match (awards night, media room, farewell, warm-up scenes from the asset plan): not in
  1.0 (my call). The vignettes stay as they are; the banner run-through is the one pre-match 3D
  scene in it.

## 1. Grounds

Each ground: model to the [MCG standard](MCG_STANDARD.md) (modelled detail, no painted-on
geometry, real seat colours, seat rule), real surroundings copied from Google Earth (no generic
OSM blocks), turf cut, live screen, crowd seated on its seats, night towers from its own lamps,
the machine pre-inspection clean, then his fly-through.

### The 13 a 2026 career plays at

| Ground | State 2026-11-22 | PR | Owner |
|---|---|---|---|
| MCG | Rebuilt to the standard (#1987 merged); last 405 bad seats in #2027; Yarra Park from OSM; horizon past 2 km empty; not yet flown through by him | #2027 | Make the MCG look like the real MCG (closed); seats: Fix the shared seat generator |
| Marvel Stadium | Rebuild open: true bearing, instanced seats, shut roof, Docklands; roofs from above read pale | #2011 | Make Marvel Stadium look real |
| Adelaide Oval | Rebuild open (Riverbank, Torrens, footbridge, St Peter's) and his 11 faults; arches with ivy and main entrance in #2015 | #2010 #2015 | Fix Adelaide Oval's saved faults |
| Optus Stadium | Roof, bronze facade, surrounds open | #1993 | Make Optus Stadium look real |
| SCG | North roof and tiers, Moore Park, Allianz open (WIP) | #2017 | Make the SCG look real |
| The Gabba | Rebuild open (v8: modelled steel, louvres, gates; Woolloongabba) | #2020 | Make the Gabba look real (thread closed; PR still open) |
| GMHBA Stadium | Rebuild open (Selwood Stand roof, seats no longer black); fins and plant screens still painted | #2016 | Make GMHBA Stadium look real |
| People First Stadium | Rebuild open (WIP); Gold Coast skyline missing | #2019 | Make People First Stadium look real |
| ENGIE Stadium | Rebuild started 2026-11-22 | | Make Engie Stadium look real |
| Bellerive Oval | Rebuild open: facades, 11,453 seats, Hobart backdrop to kunanyi | #2018 | Make Bellerive Oval look real |
| Manuka Oval | Rebuild started 2026-11-22 | | Make Manuka Oval look real |
| Norwood Oval | First model on main (#1870); wing stands 8-9 m inside the fence (pre-inspection) | | **Nobody** |
| Barossa Park | Kit first draft on main (#1930) | | **Nobody** |

### The 24 Legacy-mode grounds

Rebuilds under way: York Park, Mars Stadium (not yet in matches), Cazaly's Stadium, Traeger Park
(not yet in matches; #2006 wires it). Each has its own "Make ... look real" thread.

**No owner:** Waverley Park, Windy Hill, Moorabbin Oval, Ikon Park, Whitten Oval, Football Park,
Subiaco Oval, WACA (scoreboard legs inside the boundary), North Hobart Oval, Bruce Stadium,
Riverway Stadium, Sky Stadium, Jiangwan Stadium, Hands Oval, Blacktown, Summit Park, Macquarie Point
Stadium (all first drafts on main), and Accor Stadium, Marrara Oval (TIO Darwin) and Victoria Park
(models exist; none plays in a match yet).

### Across every ground

| Item | State | Owner |
|---|---|---|
| Real surroundings per ground | #2023 holds generic OSM surrounds for 24 grounds, which he rejected: it must not merge as is. Being redone ground by ground | Build real surroundings for each ground; each ground's thread |
| Crowd on every ground's seats | Seated on any ground with seat files; 19 grounds had none (pre-inspection, 2026-11-21) | Each ground's thread (seat rule) |
| Live big screens | Built (#1947); 11 grounds have no screen face in their model | Each ground's thread |
| Night lights from each ground's own towers | MCG only (#1996 open); others keep the old two-light night | Make MCG night matches look right (MCG); **nobody** for the rest |
| Turf cut and colour | Per-ground mowing on main; broadcast colour #2014 open | Make the turf colour look like TV (closed; PR open) |

## 2. Players

| Item | State 2026-11-22 | PR | Owner |
|---|---|---|---|
| MetaHuman body in every match | Built, not on main: main still draws the old average body | #1976 | Improve the players' on-field look (thread failed; PR waits in the queue) |
| Builds by height and weight | Ruled (2.97, 2.98); ships with #1976 | #1976 | as above |
| Far detail levels and edge smoothing for players | Built and measured (MCG High 6.2 M triangles to 2.75 M) | #1982 (draft, on #1976) | Keep stadiums smooth on phones (closed; PR open) |
| Faces: every one of the 762 real players from his portrait, automatically | v5 board; v6 under way (MetaHuman grooms per player, cornrows, buzz cuts). Not in a match yet; how 44 different heads load in a match and what they cost on a phone is not designed | | Find a way to build real player faces |
| Hair for real players | Epic's groom library, picked and reshaped per player from the photo (part of faces v6) | | Find a way to build real player faces |
| Club Forge hair (20 cuts) | Refitted to MetaHuman, trimmed to 20 | #1976 | as #1976 |
| Guernseys, all 18 clubs and clash, on the MetaHuman body | Sydney and the Bulldogs cut to their photos (#1946); numbers hold on TV (#1997); the other 16 not checked against photos on the new body | | **Nobody** |
| Umpires: field, boundary, goal | Field umpire look passed (2.75); boundary and goal umpire kits not made | | **Nobody** |
| Trainers and runners (injuries, breaks) | Not made (asset plan order C) | | **Nobody** |

## 3. Animations

| Item | State 2026-11-22 | Owner |
|---|---|---|
| Pipeline: licence-checked motion sources, retarget onto MetaHuman, contact pass, play in a match | Started 2026-11-22 (groundwork allowed: "lay some groundwork at minimum") | Make player animations look like real AFL |
| Licence of the clips we already ship (GASP, Mixamo crowd, his Rokoko captures) | Being read source by source in the same thread. Must be settled before anything ships | Make player animations look like real AFL |
| Getting around: walk, jog, run, sprint, backpedal, side-step, starts, stops, turns | Run, carry, stand from mocap; feet planted (#2009, skating 59% of steps to 11%); no sprint, walk or backpedal loops; hard turns still slide | Make player animations look like real AFL |
| The ball: kicks, set shot routine, handball, ground balls, marks, pack marks, smother, spoil, kick-in | Partly covered (asset plan: 123 clips); set shot routine, pack marks, smother, kick-in missing | Make player animations look like real AFL |
| Contests: tackles, bumps, ruck, stoppage jostle, getting up | Tackles (12), ruck jump, get-ups; no stoppage set-up or pressure clips | Make player animations look like real AFL |
| Umpire signals (free, 50, play on, goal and behind flags), throw-in throw | None: only the bounce clip exists | Make player animations look like real AFL (test clips) |
| Injuries: down, trainers, helped off | None; today the hurt man silently becomes his replacement | Make player animations look like real AFL (test clips) |
| After a goal: celebration, dejection | A few gestures only | **Nobody yet** (follows the pipeline) |
| Interchange jog off and run on; free's umpire off the mark | Built | #2025, Make free kicks and tackles read like TV (thread failed; PR open) |
| The team plays real football (row 201: shape per phase, coach's calls visible) | Harness built; gaps 6-8 fixed (#1977); the director's "numbers and your watch" check not done | Fix football proof gap list (review ready) |

## 4. Presentation

| Item | State 2026-11-22 | PR | Owner |
|---|---|---|---|
| Main camera like AFL TV (zoom by crowding, lead on the ball) | Built | #1995 | Match the main camera to AFL TV (thread failed; PR open) |
| Set shots from behind, ruck close-ups, wide shot, after a mark stays on the main camera | On main (2.93-2.113) | | done, waits on his look |
| Close cut on tackles that stop play | On main (#1985) | | done, waits on his look |
| Goal replay that shows the kick, TV sting | Sting on main (#2007); replay v2 open | #2022 | Add TV-style goal replays |
| Score bug | On main (2.107) | | |
| Goal kicker's stat card | Built | #1990 | Add TV-style match graphics |
| Journalists' posts on the broadcast (row 207) | Not started: when, who and what not yet asked | | **Nobody** (needs his rulings) |
| Banner run-through before the first bounce | Built (real tear) | #2004 | Build the 3D banner run-through (thread failed; PR open) |
| Crowd: winter clothes, cheer squads, reactions, size by real attendance | Built | #1986 (draft) #1992 | Bring the MCG crowd up to standard; Size crowds by real attendance |
| Crowd and real AFL siren | Built; he approved the sound | #2012 | Get a real AFL siren and crowd sound |
| Sun moves with the match clock | Built | #1928 (carried by #1996) | Make MCG night matches look right |
| Night matches | MCG built | #1996 | Make MCG night matches look right |
| Wet matches | On main (#2003) | | |
| Turf and picture in broadcast colour | Built | #2014 | Make the turf colour look like TV |
| Graphics levels in Settings | On main (#1953) | | |

## Release gates (across all four)

| Gate | State 2026-11-22 | Owner |
|---|---|---|
| Real phone frame times at Low, Medium and High | Not measured: needs the "Android 3D probe" APK installed on his phone. Cloud numbers below | **He** (install and run it), then this thread reads the numbers |
| Video memory | MCG on High 678 MB on main today; with the MetaHuman bodies about 976 MB (#1982's measure). Rule of thumb for a mid phone: keep under 1.5 GB | Each item's owner, this thread watches |
| Download size of a 3D build | Imported assets about 750 MB before the rebuilds and backdrops land (#2023 alone adds about 1.4 GB of models). Not yet exported or measured as an APK | **Nobody** |
| Licences of everything that ships | MetaHuman is decided: comply only. Where ground data may come from is now one rule in [MCG_STANDARD.md](MCG_STANDARD.md) ("Where shipped data may come from"): fidelity first, copying from Google Earth is fine, no raw imagery committed or baked into a shipped texture. Still open: the MetaHuman body file in the public repo (assets/oval3d/player_mh.glb); third-party captures committed under .claude/review and tools/grounds (Google Earth, Esri tiles, image-search photos); motion clips (above); docs/CREDITS_3D.md and the credits screen | Ground threads (their data); this thread (the rule, the credits list); **nobody** for the rest |
| Tests and the nightly ground shots green on main | Many PRs above wait in the merge queue, several stacked on each other | Audit everything built for the 3D view (merge queue doctor) |
| His look on every item | Not started for grounds (fly-through) | He |

## Measured (2026-11-22)

Cloud measure on main at 5415edf (Godot 4.7.2 Mobile renderer on a software GPU, 1080 x 1240,
`tools/perf/Oval3DPhone.tscn`, Fremantle v St Kilda at 4x under the broadcast camera). Triangles,
draw calls and memory carry over to a phone; renderer time is a cloud ratio only. Main still draws
the old player body, so add the MetaHuman's cost from #1982's table in
[PHONE_3D_BUDGET.md](PHONE_3D_BUDGET.md) once it merges.

| Ground | Level | Triangles (thousands) | Draw calls | Video MB | Memory MB |
|---|---|---|---|---|---|
| MCG | High | 3,327 | 287 | 678 | 278 |
| MCG | Medium | 3,029 | 278 | 654 | 278 |
| MCG | Low | 2,421 | 270 | 643 | 252 |
| Marvel | High | 3,269 | 206 | 651 | 223 |
| Marvel | Medium | 2,607 | 198 | 627 | 223 |
| Marvel | Low | 2,356 | 200 | 620 | 223 |
| Optus | High | 4,006 | 327 | 651 | 270 |
| Optus | Medium | 3,433 | 288 | 627 | 270 |
| Optus | Low | 2,368 | 260 | 616 | 246 |
| People First | High | 2,284 | 204 | 620 | 224 |
| People First | Medium | 2,271 | 206 | 596 | 224 |
| People First | Low | 2,087 | 214 | 588 | 224 |
| Adelaide Oval | High | 4,370 | 269 | 634 | 263 |
| Adelaide Oval | Medium | 3,389 | 258 | 610 | 263 |
| Adelaide Oval | Low | 2,785 | 258 | 599 | 242 |
| The Gabba | High | 2,821 | 374 | 615 | 259 |
| The Gabba | Medium | 2,569 | 325 | 591 | 259 |
| The Gabba | Low | 2,078 | 309 | 582 | 240 |

What this says: the big grounds draw 2.3-4.4 million triangles a frame on High and still 2.1-2.8 million on Low, so Low saves at most about a third (about a million of every frame is the players, whose far detail levels arrive with #1982); video memory sits at 600-700 MB at every level, before the MetaHuman bodies (about +300 MB) and the rebuilt grounds land. The rebuilds measure themselves (the Gabba's v8 reports 2.98 / 2.66 / 2.02 million). Whether that runs smoothly is the phone's answer, not the cloud's.

## Change log

- 2026-11-22: first version, built from the plan, the open PRs, the threads and project memory.
- 2026-11-22: the director chose all 37 grounds for 1.0.
- 2026-11-22: the data-source rule for grounds written into MCG_STANDARD.md and sent to every ground thread; softened the same day (fidelity first; only raw imagery in the repo or textures is out).
