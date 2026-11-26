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
- **Android and Windows carry 3D; the web build has the players but not the grounds.** Since #2060 (2026-11-25) every build carries the ground models and the 3D players. The phone app is one offline APK of 913 MB holding every stadium (the director: "Keep it offline, one big APK", with a 4 GB ceiling; "later we will try to get it smaller"). Real stadiums in a browser would need 2.1-2.3 GB of memory and a host other than itch (200 MB per file), so the web build plays 3D on the flat oval. Detail: [ITCH_BUILDS.md](ITCH_BUILDS.md).
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
| MCG | Rebuilt to the standard (#1987 merged); the last 405 seats under the tiers removed (#2027, merged); Yarra Park from OSM; horizon past 2 km empty; not yet flown through by him | #2027 | Make the MCG look like the real MCG (closed); seats: Fix the shared seat generator |
| Marvel Stadium | On main through #2072 (2026-11-25): true bearing, instanced seats, shut roof, Docklands; roofs from above still read pale; PC colour check rounds continue | #2011 (landed in #2072) | Make Marvel Stadium look real |
| Adelaide Oval | On main through #2072: arches with ivy, the main entrance rebuilt, his 11 faults fixed; ready for his review | #2010 #2015 (landed in #2072) | Fix Adelaide Oval's saved faults |
| Optus Stadium | Roof, bronze facade, surrounds on main (#1993); the bowl's shape still has to match Google Earth | #1993 | Make Optus Stadium look real |
| SCG | On main through #2072 (WIP): roofs rebuilt on Google Earth measurements, Moore Park, Allianz. Thread closed | #2017 (landed in #2072) | Make the SCG look real (closed) |
| The Gabba | On main through #2072: modelled steel and roof, real seat colours, Woolloongabba. Thread closed | #2020 (landed in #2072) | Make the Gabba look real (closed) |
| GMHBA Stadium | On main (#2016, 2026-11-25): Selwood Stand roof, solar roof, north and east walls, seats no longer black, Kardinia Park. Thread closed | #2016 | Make GMHBA Stadium look real (closed) |
| People First Stadium | On main (#2019, WIP): finned walls, bronze podium, scoreboard lattice, Carrara; work continues | #2019 | Make People First Stadium look real |
| ENGIE Stadium | On main (#2037, 2026-11-24): outline fitted to Google Earth, Olympic Park surroundings. Thread closed | #2037 | Make Engie Stadium look real (closed) |
| Bellerive Oval | On main through #2072: facades, 3D seats, Hobart backdrop; seat colour still off, PC colour rounds continue | #2018 (landed in #2072) | Make Bellerive Oval look real |
| Manuka Oval | On main (#2035, 2026-11-25): stands, seats, scoreboard, towers, the town and Canberra to 30 km. Thread closed | #2035 | Make Manuka Oval look real (closed) |
| Norwood Oval | On main: rebuild through #2072, then the north and south frontages modelled house by house on the measured land and towers to the published 34 m (#2145), and its real boundary line (#2148) | #2042 #2145 | Make Norwood Oval look real |
| Barossa Park | On main (#2041): own land, gums, far ranges, second oval. Thread closed | #2041 | Make Barossa Park look real (closed) |

### The 24 Legacy-mode grounds

On main: York Park (through #2072, thread closed), Mars Stadium (#2036, in matches), Cazaly's Stadium (#2034, ready for his review), Traeger Park (through #2072), Blacktown (#2048, the audit pass #2084 and the PC-check fixes #2150; work continues). Each has its own "Make ... look real" thread.
The MCG of each era for Legacy matches: first part on main (#2052), thread "Build the MCG of each era".

**Owner since 2026-11-23: "Build Legacy mode's old grounds"** for the other 19: Waverley Park, Windy Hill, Moorabbin Oval, Ikon Park, Whitten Oval, Football Park, Subiaco Oval, WACA, North Hobart Oval, Bruce Stadium, Riverway Stadium, Sky Stadium, Jiangwan Stadium, Hands Oval, Summit Park, Macquarie Point Stadium, Accor Stadium, Marrara Oval and Victoria Park. On 2026-11-26: 14 measured and written up, Hands Oval's heights in progress, Riverway, Bruce, Summit and Macquarie Point still to measure; no models rebuilt yet. Subiaco has a draft PR (#2069).

### Across every ground

| Item | State | Owner |
|---|---|---|
| Real surroundings per ground | On main as WIP, not shippable (#2023, 2026-11-26): every match ground draws its surroundings from OSM and Overture on the measured land; houses are boxes with roofs and about half the building heights are still guesses. Grounds whose own thread copies Google Earth (Gabba, Bellerive, Norwood and the rebuilt ones) draw their own. Never shown to the director as finished | Build real surroundings for each ground; each ground's thread |
| Crowd on every ground's seats | Seated on any ground with seat files; 19 grounds had none (pre-inspection, 2026-11-21) | Each ground's thread (seat rule) |
| Live big screens | Built (#1947); 11 grounds have no screen face in their model | Each ground's thread |
| Night lights from each ground's own towers | On main (#1996, 2026-11-25): night towers and the real sun over every ground; the beams now light the field and the players, with spill on the stadium and the land round it (#2146, 2026-11-26) | Light matches like the real grounds |
| Turf cut and colour | Per-ground mowing and broadcast colour (#2014) on main | Make the turf colour look like TV |

## 2. Players

| Item | State 2026-11-22 | PR | Owner |
|---|---|---|---|
| MetaHuman body in every match | On main (2026-11-23) | #1976 | Improve the players' on-field look |
| Builds by height and weight | Ruled (2.97, 2.98); on main with #1976 | #1976 | as above |
| Far detail levels and edge smoothing for players | On main (#2054): MCG High 7.1 to 2.4 M triangles, Low 6.2 to 1.6 M; video memory about 1.03-1.11 GB | #2054 | Keep stadiums smooth on phones |
| Faces: every one of the 762 real players from his portrait, automatically | v5 board; v6 under way (MetaHuman grooms per player, cornrows, buzz cuts). Not in a match yet; how 44 different heads load in a match and what they cost on a phone is not designed | | Find a way to build real player faces |
| Hair for real players | Epic's groom library, picked and reshaped per player from the photo (part of faces v6) | | Find a way to build real player faces |
| Club Forge hair (20 cuts) | Refitted to MetaHuman, trimmed to 20; on main | #1976 | as #1976 |
| Guernseys, all 18 clubs and clash, on the MetaHuman body | On main (#2038, 2026-11-24). Thread closed. Both kit atlases now import at half size, 4096 x 2560 (#2165): the four compressed files go from about 224 MB to 56 MB, and at the ruck close-up the guernseys look the same | #2038 #2165 | Check club guernseys on MetaHuman players (closed) |
| Umpires: field, boundary, goal | Field umpire look passed (2.75); boundary and goal umpires on main | #2043 | Add boundary and goal umpires and trainers |
| Trainers and runners (injuries, breaks) | On main | #2043 | Add boundary and goal umpires and trainers |

## 3. Animations

| Item | State 2026-11-22 | Owner |
|---|---|---|
| Pipeline: licence-checked motion sources, retarget onto MetaHuman, contact pass, play in a match | Started 2026-11-22 (groundwork allowed: "lay some groundwork at minimum") | Make player animations look like real AFL |
| Licence of the clips we already ship (GASP, Mixamo crowd, his Rokoko captures) | Being read source by source in the same thread. Must be settled before anything ships | Make player animations look like real AFL |
| Getting around: walk, jog, run, sprint, backpedal, side-step, starts, stops, turns | Run, carry, stand from mocap; feet planted (#2009, skating 59% of steps to 11%); no sprint, walk or backpedal loops; hard turns still slide | Make player animations look like real AFL |
| The ball: kicks, set shot routine, handball, ground balls, marks, pack marks, smother, spoil, kick-in | Partly covered (asset plan: 123 clips); set shot routine, pack marks, smother, kick-in missing; kick, handball and mark clips open (#2040) | Make player animations look like real AFL |
| Contests: tackles, bumps, ruck, stoppage jostle, getting up | Tackles (12), ruck jump, get-ups; no stoppage set-up or pressure clips | Make player animations look like real AFL |
| Umpire signals (free, 50, play on, goal and behind flags), throw-in throw | None: only the bounce clip exists | Make player animations look like real AFL (test clips) |
| Injuries: down, trainers, helped off | Draft PR #2071 (in-match injuries) | Make player animations look like real AFL (test clips) |
| After a goal: celebration, dejection | A few gestures only | **Nobody yet** (follows the pipeline) |
| Interchange jog off and run on; free's umpire off the mark; far tackles run in | On main (#2025, WIP) | Make free kicks and tackles read like TV (closed) |
| The team plays real football (row 201: shape per phase, coach's calls visible) | Harness built; gaps 6-8 fixed (#1977); the director's "numbers and your watch" check not done | Fix football proof gap list (review ready) |

## 4. Presentation

| Item | State 2026-11-22 | PR | Owner |
|---|---|---|---|
| Main camera like AFL TV (zoom by crowding, lead on the ball) | On main | #1995 | Match the main camera to AFL TV |
| Set shots from behind, ruck close-ups, wide shot, after a mark stays on the main camera | On main (2.93-2.113) | | done, waits on his look |
| Close cut on tackles that stop play | On main (#1985) | | done, waits on his look |
| Goal replay that shows the kick, TV sting | Sting (#2007) and the replay that shows the kick on main | #2022 | Add TV-style goal replays |
| Score bug | On main (2.107) | | |
| Goal kicker's stat card | On main | #1990 | Add TV-style match graphics |
| Journalists' posts on the broadcast (row 207) | Not started: when, who and what not yet asked | | **Nobody** (needs his rulings) |
| Banner run-through before the first bounce | On main (#2004, 2026-11-25); banner words are milestones only | #2004 | Build the 3D banner run-through (closed) |
| Crowd: winter clothes, cheer squads, reactions, size by real attendance | Attendance on main (#1992, WIP) | #1986 (draft) #1992 | Bring the MCG crowd up to standard; Size crowds by real attendance (closed) |
| Crowd and real AFL siren | On main; he approved the sound | #2012 | Get a real AFL siren and crowd sound |
| Sun moves with the match clock | On main (#1996) | #1996 | Light matches like the real grounds |
| Night matches | On main (#1996), every ground's own towers | #1996 | Light matches like the real grounds |
| Wet matches | On main (#2003) | | |
| Turf and picture in broadcast colour | On main | #2014 | Make the turf colour look like TV |
| Graphics levels in Settings | On main (#1953) | | |

## Release gates (across all four)

| Gate | State 2026-11-22 | Owner |
|---|---|---|
| Real phone frame times at Low, Medium and High | Not measured on a phone. Unblocked 2026-11-25: since #2060 the "Android 3D probe" carries the grounds and players, so it can be installed and read | **He** (install the probe and read its numbers) |
| Video memory | MCG on High 980 MB on main today (MetaHuman players). Rule of thumb for a mid phone: keep under 1.5 GB | Each item's owner, this thread watches |
| Ground and player models in the builds | On main (#2060, 2026-11-25): Android, Windows and the probe carry every ground and the players; web carries the players only. Per-ground download packs are built and tested but not used | Ship grounds and players in phone builds (closed) |
| Download size of a 3D build | The APK is 913 MB with every stadium; the director chose one offline APK with a 4 GB ceiling (a 2.6 GB test APK installed). "Later we will try to get it smaller" The 913 MB was measured before the surroundings (#2023) landed; not re-measured since | Ship grounds and players in phone builds (closed); making it smaller is later work |
| Licences of everything that ships | MetaHuman is decided: comply only. Where ground data may come from is now one rule in [MCG_STANDARD.md](MCG_STANDARD.md) ("Where shipped data may come from"): fidelity first, copying from Google Earth is fine, no raw imagery committed or baked into a shipped texture. The MetaHuman files left the public repo (#2062). The review boards and reference imagery (.claude/review and the photos under tools/grounds, 4.6 GB) moved to a private archive repo (#2192, 2026-11-26), so the current files no longer hold the third-party captures. Still open: motion clips (above); the credits screen (the list itself is docs/CREDITS_3D.md) | Ground threads (their data); this thread (the rule, the credits list); **nobody** for the rest |
| Third-party images already in git history (Google Earth captures, Esri tiles, photos under .claude/review and tools/grounds; about 2.6 GB of review images in all) | Out of the current files since #2192 (2026-11-26: moved to the private archive aussierulesdynasties/afl-review-archive). They stay in history until a rewrite, which is a later item; the MetaHuman files left the public repo for a private one fetched at build time (#2062, 2026-11-25) | Move MetaHuman files out of the public repo; later item |
| Tests and the nightly ground shots green on main | Most 3D PRs landed on 2026-11-25 | Fix CI |
| His look on every item | Not started for grounds (fly-through) | He |

## Measured (2026-11-23, MetaHuman players on main)

Cloud measure on main at ff8e359 (Godot 4.7.2 Mobile renderer on a software GPU, 1080 x 1240,
`tools/perf/Oval3DPhone.tscn`, Fremantle v St Kilda at 4x under the broadcast camera). Triangles,
draw calls and memory carry over to a phone; renderer time is a cloud ratio only. Raw numbers:
`/mnt/project-files/3d-release/phone_cost_main_2026-11-23.json` (project files).

| Ground | Level | Triangles (thousands) | Draw calls | Video MB | Memory MB |
|---|---|---|---|---|---|
| MCG | High | 7,140 | 325 | 980 | 285 |
| MCG | Medium | 6,852 | 316 | 956 | 286 |
| MCG | Low | 6,182 | 308 | 945 | 260 |
| Marvel | High | 6,883 | 237 | 925 | 231 |
| Marvel | Medium | 6,227 | 229 | 901 | 231 |
| Marvel | Low | 5,906 | 231 | 893 | 231 |
| Optus | High | 7,668 | 362 | 924 | 278 |
| Optus | Medium | 7,102 | 323 | 900 | 278 |
| Optus | Low | 5,946 | 295 | 889 | 254 |
| People First | High | 6,034 | 238 | 893 | 232 |
| People First | Medium | 6,028 | 240 | 869 | 232 |
| People First | Low | 5,730 | 247 | 862 | 232 |
| Adelaide Oval | High | 8,116 | 304 | 907 | 271 |
| Adelaide Oval | Medium | 7,142 | 293 | 883 | 271 |
| Adelaide Oval | Low | 6,489 | 293 | 873 | 250 |
| The Gabba | High | 6,653 | 412 | 889 | 267 |
| The Gabba | Medium | 6,408 | 363 | 865 | 267 |
| The Gabba | Low | 5,843 | 347 | 856 | 248 |

What this says: the MetaHuman players (#1976) doubled the frame. The MCG on High went from 3.3 to 7.1
million triangles and from 678 to 980 MB of video memory, and Low now saves only about a seventh
(6.2 million on the MCG), because the players' far detail levels did not come with #1976. They are in
#2054 (edge smoothing and player detail levels, measured on the MetaHuman at MCG High 6.2 to 2.75
million). Until #2054 lands, every ground is 5.7-8.1 million triangles at every level and close to
900-980 MB of video memory. The 22 Nov table (old body) was 2.1-4.4 million and 580-680 MB.

#2054 measured against this main (MCG, same tool): High 7.14 to 2.41 million triangles, Medium 6.85 to
2.20, Low 6.18 to 1.63. Renderer time drops about 41-43% on Medium and Low but rises 13% on High,
because 4x edge smoothing is costly on the software GPU (a phone's tiled GPU should do it cheaply; only
the phone run settles it). Video memory rises 90-130 MB (to 1,032-1,111 MB) for the far detail levels
and the smoothing buffers.

## Change log

- 2026-11-22: first version, built from the plan, the open PRs, the threads and project memory.
- 2026-11-22: the director chose all 37 grounds for 1.0.
- 2026-11-22: the data-source rule for grounds written into MCG_STANDARD.md and sent to every ground thread; softened the same day (fidelity first; only raw imagery in the repo or textures is out).
- 2026-11-22 evening: stat card (#1990), goal replay (#2022), siren and crowd (#2012) and broadcast colour (#2014) and the MCG seat fix (#2027) on main; MetaHuman players (#1976) and the match crew (#2043) on main, phone cost re-measured (players' detail levels still missing, #2054); every export preset found to leave out the ground and player models (#2058); owners and PRs for ENGIE, Manuka, Norwood, Barossa, Mars, guernseys, umpires and trainers, kick clips and night lights.
- 2026-11-23: Optus Stadium rebuild on main (#1993); Blacktown stages 1-3 on main (#2048).
- 2026-11-24: player detail levels and edge smoothing (#2054), the TV main camera (#1995), the MCG of each era (first part, #2052) and the shared Google Earth compare tool (#2047) on main.
- 2026-11-26: catch-up after a two-day pause. On main since 24 Nov: builds carry the grounds and players (#2060), lighting at every ground (#1996), banner run-through (#2004), real land round every ground (#2072, which also carried the Marvel, Adelaide, SCG, Gabba, Bellerive, York Park, Norwood and Traeger branches: their PRs closed as landed), Cazaly's (#2034), Manuka (#2035), GMHBA (#2016), People First (#2019), ENGIE (#2037), Mars (#2036), Blacktown audit (#2084), guernseys (#2038), match crew round two (#2068), move clips (#2040), interchanges (#2025), crowd attendance (#1992), the 3D bug bash (#2067), MetaHuman files out of the public repo (#2062).
- 2026-11-26 morning: the night-tower beams (#2146) and Blacktown's PC-check fixes (#2150) on main.
- 2026-11-26 midday: the surroundings of every match ground (#2023, WIP, not shippable), Norwood's frontages (#2145), and Manuka, People First and Norwood on their real boundary lines (#2148) on main.
- 2026-11-26 afternoon: guernsey atlases at half size (#2165, about 168 MB less) and a faster first 3D player build (#2155) on main.
- 2026-11-26 evening: review boards and reference imagery moved out of the public repo to a private archive (#2192).
- 2026-11-26 night: the ground models moved to a private asset repo fetched by a pinned lock (#2199; main's history was rewritten for it). The builds and tests fetch them; the packaging result (#2060) stands.
