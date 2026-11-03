# TODO: everything not done yet

The one list of work not done. Point a session at this file and it works down it. Done and cut items are removed (git history keeps them). Director rulings live in `docs/roadmap/21..32` (decision records, not work lists); the later ruling wins. Balance is the director's call; nothing ships on without his playtest. Updated 2026-11-04 against main `a8b23185`.

## A. Build now (open, no blocker, order = story first, then sim, then approachable)

| # | What | Done looks like |
|---|---|---|
| 11 | Stoppages from contests, play on after an intercept or free, then recalibrate contested ball, spoils, turnovers. Work sits on unmerged `claude/match-flow` (14 commits, 2026-10-10) | rebase on main (#885 moved calibration), PR, audit shows bands hold |
| 12 | Disposals to empty space: feed names the real cause; kicks to space readable | feed line tells why |
| 13 | Every in-match decision gets a vignette: tired, duel, hot, momentum, set shot are still text cards | each decision type has a scene when vignettes are on |
| 14 | Opposition goal-run decision rebuilt around two concrete football moves, with vignettes (still Throw numbers / Slow it down / Ride it out) | two moves, scenes, odds in football words |
| 15 | Late-game centre ball-up: two distinct choices (still three) | two options |
| 9 | Feed styling: own goals positive, conceded negative, behinds and tactical lines neutral | feed colours match |
| 17 | Key-matchup block as a compact grid; loose tally "since the call"; "What your calls did" explains its numbers | grid shown |
| 18 | Match summary: full injury wording (not "to a hand"); scoring-run line with when and score before/after | lines present |
| 23 | This week: both sides' key forwards and defenders, height and marking, side by side | both sides shown |
| 24 | Training: compact player card grid with roles and traits (list is still full-width rows) | grid built |
| 25 | Team builder: pre-game setup before Start; entry points share one side; headers from arranged fit | setup precedes Start, test added |
| 27 | Stat guide as a topic grid (director says whether A17 replaces it) | answer, then grid or close |
| 22 | Draft AI: role concentration, named boards, draft scroll in exported build | audit + build check |
| 53 | Show the actual coaches' votes for best players at breaks and full time (ch. 27 B6) | votes shown |
| 54 | Under-18 carnival week, then mid-season rookie draft; W7 review (ch. 29 row 9) | built |
| 55 | Off-season: "this year's list problem" in three lines; put a player on the table / Ask around (ch. 29 row 4) | built |
| 57 | Save export/import and a version chain with restore | export, import, restore work |
| 42 | Believable comebacks: rules with numbers from the audit on unmerged `claude/comeback-audit-row42` | rules in code, audit bands, his call on balance |
| 35 | Finals bespoke cards: slice 2 built behind `finals_cards_2`; ships when he has played it | see section B |
| 33 | Per-ground oval dimensions and looks (only MCG look done). Open: presentation only, or sim too | his answer, then build |

## B. Built and OFF: waiting for his playtest, then the switch goes on

| # | Feature | Switch | PRs |
|---|---|---|---|
| 1 | Top three attributes on cards, Needs work benchmark, scout grade word for hidden prospects | `top_attributes` | #863 |
| 6 | Player faces, 15 hair styles, 30 strips re-rendered | `player_looks` | #873 |
| 10 | Kick range caps receiver choice; Sim the week shares the same pick | `kick_range` | #857 #879 |
| 48 | Coach career arcs | `coach_arcs` | #867 #877 #881 #886 |
| 49 | Match hero, turning point, reasons | `match_story` | #853 #890 |
| 50 | Club almanac | see Features.gd | #855 #890 |
| 51 | Weekly checklist with one big arc call (Hub "no weekly checklist" text goes when on) | `weekly_checklist` | #859 #861 #867 #877 #881 |
| 35, 36 | Finals cards slice 2 and Grand Final cards | `finals_cards_2` | #864 |
| 52 | Expansion package, training report, speccy front | `expansion_package`, `training_report`, `speccy_front` | #745 #741 |

## C. Needs his look or call (shown, then ask)

- 5 Defensive set-up break wording (merged by #874). 16 PC bounce scene. 20 Press conference black bands gone?
- 7 Shake on his device. 26 Season stats hub phone review.
- 30 Coleman goalkicking cap (98th percentile, balance-gated).
- 58 Difficulty dial sizes (board patience, rival recruiting). 39 Pre-season balance sizes.
- 47 Decision transparency: 9 questions on sheet #851 awaiting his answers.
- 34 62-line event-card copy sheet; never-seen cards and no-trade-off choices unruled.
- 40/41 Own game plan builder (game as is; Club Forge): decision waits on his plan-drilling play.

## D. Audits to run (seeded, via audit.yml)

- 19/60 Press-question and coaching-note repetition over long saves; pressers per season.
- 28 How-we-play maturity; How-we-win materiality; List Profile vs results.
- 29 Run-of-goals cadence; blowout distribution; close-finish vignette reachability.

## E. Waiting on him or his phone

- 31 Native phone frame time, battery, loading (needs his phone; PC baseline only).
- 59 Banner text and music: he supplies originals (placeholders in `data/banners.json`, empty playlist).
- 56 Public demo page: rights to real names and a licence register come first.
- 32 Web build parity: saves carried between devices pending his answer.

## F. Later (1.x or after 1.0, unassigned)

- 38 Live-3D vignette probe (low priority; Tripo ruck rig in Godot).
- 43 More Tripo emblems (15,000 credits set aside; first slice done, none further assigned).
- 44 State of Origin (not for 1.0; scope interview first).
- 41 Club Forge game-plan builder.
- Presentation wishlist: away/clash and heritage guernseys, coach appearance, finals bracket, premiership guernsey
  history, player card evolution, record-breaker marks, legends wall, season story recap, draft class identity,
  archive gallery, club museum, retirement variants, dynamic crowd, custom typography, season poster, stadium
  identity, user guernseys and logos, Coach of the Year.
- Deferred by ruling: weather at the quarter break, announce the cap step, league rule changes.

## In flight
Open PR #888 (AI club decisions). Unmerged branches: `claude/match-flow`, `claude/comeback-audit-row42`.

## Working rules
- One Godot process per agent at a time, off-screen, own user data (`APPDATA=<scratch dir>`); kill only your own PIDs.
- Run only the suites your change touches locally; CI runs the rest. Long audits go to `audit.yml`.
- Revert `.import` and `.uid` churn before committing. Stage by name; never `git add -A`.
- One worktree per session, from `origin/main`. Don't push to a PR branch while its CI runs unless the merge needs it.
- When an item ships, delete its row here in the same PR. Add new director requests here, with his words.
