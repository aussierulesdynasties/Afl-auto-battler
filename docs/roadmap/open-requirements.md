# Open requirements register

Read in full at session start. One line per director requirement not DONE on main: owner, status, where the
full wording lives (`docs/roadmap/`). Leaves this file only when its section file records DONE with the PR.
Owner "none" = no plan or branch covers it. "verify" = code not checked this pass; owner checks before scheduling.
Nothing here starts until the director assigns it. Reconciled 2026-11-04 against main `0df389bc` (build 1.0.1; the pre-season, story-first plan and cut audit are in). Director decisions: [ch. 26](26-director-decisions-2026-10-13.md), [27](27-director-playtest-2026-10-14.md), [28](28-director-decisions-2026-10-18.md), [29](29-director-decisions-2026-10-18-pass2.md), [30](30-director-decisions-2026-10-18-morning.md), [31](31-director-decisions-2026-10-25.md), [32](32-director-decisions-2026-11-03.md); the later ruling wins. Light theme parked by the director 2026-10-13 (ch. 26 s11). A row with an old owner name (boss, lead, art, story) has no live owner until assigned.

## Director rules on main that the code does not meet

| # | Requirement (director's words in the section file) | Source | Owner | Status |
|---|---|---|---|---|
| 1 | Every player card shows his **top three attributes**; Needs work compares to a positional peer benchmark; retraining adds a position and never degrades old ones | §1.11 positional weaknesses | boss (3rd) | built behind switch `top_attributes` (off), PR #863: all 13 attributes rank (ch. 32 row 18), Needs work cutoffs unchanged (row 19), hidden-rating prospects show the scout grade word (row 20); the director plays a card and the draft detail before the switch goes on |
| 3 | Every pep talk, including the default, shows its effect; a **fourth pep-talk option** | §1.11 coaching controls | boss | DONE #624: fourth talk Bring the heat, all four show their effect; balance size unmeasured (lever audit). Leaves once 02-03-16 records DONE |
| 5 | Defensive forward: "Assign defensive forward" label, explicit none, suitability cards, still scores | §1.11 coaching controls | boss (2nd, coaching-controls PR) | folded into the one Defensive set-up call by #874 (ch. 32): cover wording, explicit none, suitability card and reduced-target cost line are in code; the director's look at the merged break wording is open |
| 6 | **Player figures get faces and distinct hair** (16 styles defined, 5 drawn; no facial features). Director 2026-10-10: "they look like clones" | §1.11 generated player visual identity | art | built behind `player_looks` (off), PR #873: 15 styles, minimal face (eyes, 5 brows by id), the 30 player strips re-rendered (ch. 32 rows 14-17); the director plays it before the switch goes on |
| 7 | Haptics and restrained screen shake, with Off | §1.11 haptics | boss (5th) | built: `scripts/ui/Feel.gd` haptics and vibration, #701 goals-only capped shake, Screen shake On/Off and Reduced motion. Open: the director checks the shake on his device; fix the stale TODO in 02-03-14 |
| 8 | A clear turnover cue (TURNOVER label; tackles distinguishable from turnovers) | §1.11 visual simulation | boss | DONE #617: "Turnover" over the winner for about a second; restarts and kept tackles carry none. Leaves once 02-03-06 records DONE; look gate the director's |
| 9 | Feed styling: neutral for tactical/score lines; your goals positive, conceded negative, behinds neutral (visual) | §1.11 feed styling, scoring feedback | none | open: the feed colours every goal and line alike (club-colour stripe on goals); own goal positive, conceded negative, behinds and tactical lines neutral is not built (02-03-10, 02-03-13) |

## Match flow and presentation

| # | Requirement | Source | Owner | Status |
|---|---|---|---|---|
| 10 | Collection pauses / far receiver: "urgent regression"; next approach named (role allocation reads the log ahead) | §1.11 visual simulation, 2026-10-08 record | none | built: #857 (log-ahead roles), #879 (kick range, switch `kick_range` off, ch. 32 rows 21-22, Sim the week shares one receiver pick); the director checks an exported-PC full match and switches `kick_range` on |
| 11 | Play on after an intercept or a free; stoppages from contests (Step 1), then recalibrate contested ball, spoils, turnovers (Step 2) | #607 audit, director 2026-10-10 | boss (claude/match-flow) | open: Steps 1-2 sit on unmerged `claude/match-flow` (14 commits, last 2026-10-10, no PR); needs a rebase on main (#885 moved the calibration) and a PR; balance is the director's call |
| 12 | Disposals to empty space: the feed says the real cause; kicks to space readable | §1.11 visual simulation | none | open |
| 13 | Every in-match decision has a vignette when on: audit all decision types | §1.11 every decision | none | open: only the centre ball-up call has a scene; tired, duel, hot, momentum and set shot are text cards (toggle #518 DONE) |
| 14 | Opposition goal-run decision rebuilt around two concrete football moves with vignettes | §1.11 goal-run decision | none | open: still Throw numbers / Slow it down / Ride it out with odds (#835); not rebuilt around concrete moves, no vignette |
| 15 | Late-game centre ball-up: two distinct choices | §1.11 centre ball-up | none | cap, styling and odds lines DONE (#492, #496, #835); still three options, the two-choice redesign is open |
| 16 | Centre ball-up vignette recomposed wider; umpire's held ball not floating | §1.11 vignette polish | none | built: #578 wide bounce camera, #506 held ball, #597; the director's look at the PC bounce scene is open |
| 17 | Live key-matchup block as a compact grid; intercepts **since the call** beside each loose defender; "What your calls did" says what its numbers mean | §1.11 key-matchup, loose defender, calls | none | partial: #760, #762, #795 and scoped "What your calls did" lines built; match-ups still sentences, not a grid; loose tally reads "so far", not "since the call" (the call merged into Defensive set-up, #874) |
| 18 | Match summary: full injury wording; scoring-run context (when, score before and after) | §1.11 match summary | none | open: the injury line still reads "to a hand"; the run line has no time or score before and after |
| 19 | Coaching notes vary across a season; press questions vary across long saves | §1.11 coaching notes, press | none (journalists #559 DONE) | audit open: journalists #559 DONE; no seeded audit of press-question or coaching-note repetition over long saves, nor of pressers per season (ch. 29 P-17 trigger rate) |
| 20 | Press-conference framing without the black bands | §1.11 press vignette | none | layout #754 (big landscape, picture left); press-room plate art not on main; the director looks at whether the black bands are gone |

## Lists, draft, development

| # | Requirement | Source | Owner | Status |
|---|---|---|---|---|
| 21 | Role classifier re-audit: Miers a forward, Uwland not key, Langford a wing | §1.11 role allocation (REOPEN) | none | built: #756, #764, #769; `tests/test_roles.gd` pins Miers a forward, Uwland not key, Langford a wing. Leaves once 02-03-20 records DONE with the PRs |
| 22 | Draft AI / potential: five-season youth-strategy evidence, role concentration, named boards; draft scroll in the exported build | §1.11 draft AI, potential, scroll | none | PARTIAL: #494, #489, audits #683/#862, draft logic #869; open: role concentration, named boards, exported-build draft scroll (the director's check) |
| 23 | This week: both sides' key-position heights and marking side by side | §1.11 matchup comparison | none | open: This week shows only the opposition's key forwards (type, cm); both sides' key forwards and defenders with height and marking side by side is not built |
| 24 | Development manual-XP grid; Training compact card grid with roles and traits | §1.11 development, training; STYLE-01 | none | manual-XP grid CUT (#871, cut audit row 6, ch. 32); open: Training player list is still full-width rows, no compact card grid with roles and traits |
| 25 | Team builder: entry points share one side; headers from arranged fit; pre-game setup before Start | §1.11 team builder | none | open: pre-bounce setup is still on the "Before the first ball-up" break, not before Start; one-side entry points and arranged-fit headers unverified (no test found) |
| 37 | **Audit the AI clubs' draft strategy**: do clubs that build their list from scratch (the AI drafting, trading and signing over seasons) end up on average weaker than the real 2026 lists, which real AFL professionals built? Measure over seeded 10-season careers: each AI club's list strength (best 23 and depth, by age bracket) against its real 2026 starting list and against the league's spread; where it drifts; and whether drafted players reach the OVR and roles the real list has. If the AI drafts notably worse teams than their real counterparts, buff its draft skill (needs, value, potential reads) until the gap closes, paired seeds, ± errors; balance is the director's call | director 2026-10-12 | dev-sim | DONE #862 (audit: AI lists +2.5 best 23 above the real lists, no gap) and #869 (ch. 32 later ruling: the buffed logic is the only draft logic for rivals and Pick for me; `ai_draft_buff` gone). Leaves once ch. 32 carries DONE with the PRs |
| 38 | **Live-3D vignette probe (LOW PRIORITY, explore later)**: one figure, the Tripo ruck rig, animated in real time inside Godot (glTF rig + clips from the existing Blender/Mixamo path) and judged by the same realism and motion critics against the sprite-sheet version at phone scale and frame time. The question: would real-time 3D vignettes (any camera angle, lighting, posture fixes on the rig instead of re-rendered sheets, no sheet growth) beat the approved 2.5D sheets for look, phone performance and pipeline cost? three.js is NOT the route (a playback stage with no authoring; Godot already renders 3D and exports to web) | director 2026-10-13 | none | open, low priority, unassigned; no probe built, 0 credits |

## Stats, help, onboarding

| # | Requirement | Source | Owner | Status |
|---|---|---|---|---|
| 26 | Season stats hub phone review | §1.11 stats patch | director | built (#509, follow-ups #575-#689); the director's phone review is the only gate |
| 27 | Stat guide as a topic grid; per-menu first-visit tutorials | §1.11 stat guide, tutorials | none | first-visit intros DONE (#572, #856); stat guide condensed and grouped (#757, A17) but no topic grid; the director says whether A17 replaces the grid |

## Audits the roadmap asks for, unowned

| # | Audit | Source | Owner | Status |
|---|---|---|---|---|
| 28 | How-we-play maturity; How-we-win materiality; List Profile vs results | §1.11 observed failures | none | open |
| 29 | Run-of-goals cadence and efficacy; AI plan adaptation; blowout distribution; vignette reachability in close finishes | §1.11 observed failures | none | partial: AI counter-plan rule is in (ch. 32 coach styles); run-of-goals cadence, blowout distribution and close-finish vignette reachability audits not run |
| 30 | Coleman goalkicking cap (defect found, balance-gated) | §1.11 Coleman | director | awaiting the director's balance decision; cap unchanged on main (`Ratings.build_norm_params`, 98th percentile) |
| 31 | Native phone numbers: frame time, battery, loading | §1.11 performance | director's phone (probe build held) | waiting: PC baseline only (PERF_BASELINE.md); native phone numbers need the director's phone (1.0 plan Tier A) |

## Story cards (director, 2026-10-12)

| # | Requirement | Source | Owner | Status |
|---|---|---|---|---|
| 34 | **Audit every event card** (the 65 story cards and the older event cards): does any choice do nothing (no effect, no information, no follow-up)? Does any card never appear in a 10-season career? Can any be worded better (scrutable: a card keeps what it promises, football language, stakes true)? Found in play: "The fitness staff want a time trial" promised to tell the coach who is fit and named nobody (fix: claude/story-time-trial) | director 2026-10-12 | none | audit DONE #680; time trial #678, costs #688/#818/#830 built; the 62-line copy sheet (39 cards, in the audit doc) goes to the director as one sheet; never-seen cards and no-trade-off choices not ruled |
| 35 | **A whole bespoke set of finals events**: cards that only fire in finals week (the elimination/qualifying week, the week after a loss that ends the season, the preliminary final build-up, the bye week, the club's first final in years, a veteran's last final), with real stakes and the finals mood in the copy | director 2026-10-12 | none | slice 1 live #709; slice 2 built #864 behind `finals_cards_2` (off); the director plays it, then the switch goes on. Not DONE until it ships |
| 36 | **A small set of Grand Final events that make each Grand Final feel unique and memorable**: a handful of cards keyed to what is true of this Grand Final (the opponent, a captain's last game, a kid's first season, an injured star's fitness test, the parade, the week's press, the result's aftermath), so no two Grand Final weeks read the same | director 2026-10-12 | none | built #864 behind `finals_cards_2` (off); rulings ch. 32 rows 9-12; the director plays a Grand Final week, then the switch goes on |

## Pre-season (director, 2026-10-13)

| # | Requirement | Source | Owner | Status |
|---|---|---|---|---|
| 39 | **A pre-season** (headline of patch 0.2.0 "Pre-season"). Director: "a glaring hole in our game: pre season, a period of development, narratives, media speculation, fitness building, game-plan honing etc". Eight weeks, "but streamline it a touch"; "Plan in blocks, stop at events ... but reduce it to just 1 pre season match"; practice match "Trial players and plans, no ladder"; "Drill a plan, it works better"; papers "Predict, and you answer"; the intra-club match is a real match on the oval with next draft's prospects filling the spare spots. Full rulings: [ch. 26 s2](26-director-decisions-2026-10-13.md) | director 2026-10-13 | none | all five slices built and ON since 1.0.1 (#706 #730 #740 #747 #734; one pre-season match #872 #875; papers and 11 cards #837; #843; story calendar #889). Open: the director's playtest of the balance sizes. "Two matches" wording is superseded by #872 |
| 40 | **Create your own game plan, in the game as is.** Director: "i love the idea of 3 for our club forge, but 1 for our game as is" | director 2026-10-13 | none | open, stretch, 1.x; decision waits on the director's play of plan drilling (live since 1.0.1) |
| 41 | **A full game-plan builder for the Club Forge** (create-a-club): the coach builds a plan of his own. Director: "i love the idea of 3 for our club forge" | director 2026-10-13 | none | open, unassigned, 1.x; design sheet first |
| 42 | **Believable comebacks.** Director: "my tester reported a scenario where he was 2 goals up at 3qt, simmed the last quarter, lost by 40 points. we need to codify realistic comeback rules. I mean a 52 point swing in one quarter is POSSIBLE but very very very unlikely. We need to keep comebacks in the game, maybe even make them a bigger part (Read more narrative/UI elements rather than frequency) of the game, but they need to be believable and not seem like the game hallucinating" | director 2026-10-13 | none | narrative told #716/#723/#731. Rules audit exists on unmerged `claude/comeback-audit-row42` (no PR; older measurement on `claude/quarter-swing-audit`); rules with numbers come after it, balance is his call |
| 43 | **Tripo-made emblems and models to beautify the UI**, "just like how we did with our club guernsey logos on the ladder". Starts with three culture-strand icons (Standards, Togetherness, Ambition). Spend: 15,000 credits set aside 2026-10-13, "im not saying you HAVE to spend 15k in one go, im just setting that 15k aside to you to use as you see fit with over the next few hours,days, weeks" ([ch. 26 s10](26-director-decisions-2026-10-13.md)) | director 2026-10-13 | none | first slice built: culture emblems #704, cup #736, ball #718, lectern #721, gear #720/#737, stopwatch #730; credits used not recorded in the repo; no further emblem work assigned |
| 44 | **State of Origin.** Director 2026-10-18, 20:2x: "add state of origin to the roadmap (not for 1.0)". A representative series between the states, with players picked from the AFL lists by origin; scope, format (one match or a series, when in the season, who picks, injuries and form carrying back) and whether the coach has a role are open until he scopes it. Not in the 1.0 plan (docs/superpowers/plans/2026-10-18-release-1-0.md) | director 2026-10-18 | none | not started, after 1.0; scope interview before any brief |
| 47 | **Decision transparency:** every decision gate shows each option's upside, downside and odds in football words; never which is better ([audit](../research/DECISION_TRANSPARENCY_AUDIT_2026-10-18.md), [ch. 30 row 23](30-director-decisions-2026-10-18-morning.md)) | director 2026-10-18 | lead | format ruled (ch. 30 rows 27, 29); #835, #818/#830, #821, #833 shipped; remaining gates and questions are the rulings sheet #851 (9 questions, awaiting his answers); M4 and M5 superseded by #874 |
| 46 | **Live trading of picks on draft night.** Director 2026-10-25: "implement live trading of picks on draft night". Everyone trades (you, rivals to you, rivals among themselves); picks of this draft and the next two, never players; any time, no clock; rivals judge by the trade-period values ([ch. 31](31-director-decisions-2026-10-25.md)) | director 2026-10-25 | lead | DONE #848 (look passed 2026-10-25); night-deal rate and offer floor 0.9 are first settings for his playtest. Leaves once ch. 31 carries DONE |

## Built, off, waiting for the director to play (ch. 32 story-first plan)

| # | What | Switch | PRs | Status |
|---|---|---|---|---|
| 48 | Coach career arcs: hot seat and sacking, poached, board feud, protege, veteran kept too long, drought, legacy; coach moves clubs | `coach_arcs` | #867, #877, #881, #886 | built, off until he plays a career |
| 49 | Match hero, turning point and one to three reasons traced to the result | `match_story` | #853, #890 | built, off until he plays it |
| 50 | Club almanac | see Features.gd | #855, #890 | built, off |
| 51 | Weekly checklist with one big arc-linked call (BigCalls.gd); the Hub's "no weekly checklist" text goes when it ships | `weekly_checklist` | #859, #861, #867, #877, #881 | built, off; check the switch's home before turning on |
| 52 | Also off pending his look: `expansion_package` (#745), `training_report` (#741), `speccy_front` | per name | as listed | off |

## Open from the director's chapters, no row until now

| # | Requirement | Source | Owner | Status |
|---|---|---|---|---|
| 53 | Show the actual coaches' votes for best players at breaks and full time | ch. 27 B6 | none | open, not assigned |
| 54 | Under-18 carnival week, then the mid-season rookie draft; W7 review | ch. 29 row 9 (P-52) | none | no code found |
| 55 | This year's list problem in three lines; put a player on the table / Ask around (off-season) | ch. 29 row 4 (P-48, P-50) | none | no merged PR found; P-46, P-47, P-49 landed in #783 |
| 56 | Public demo page, "pursue before 1.0"; rights to real names and a licence register come first | ch. 28 decision 5 (P-23) | none | not started |
| 57 | Save export/import and a version chain with restore | 1.0 plan Tier A (P-02) | none | no code found; ties to row 32 |
| 58 | Two difficulty dials built (#797): his sizes for board patience and rival recruiting are set in playtest | ch. 28 decision 4 (P-20) | director | built; sizes open |
| 59 | Banner text and music were removed; he supplies originals (data/banners.json placeholders, empty playlist) | ch. 30 rows 9-10 | director | waiting on him |
| 60 | Press conferences: trigger rate per season audit (they fire on notable triggers already) | ch. 29 correction, P-17 | none | open; part of row 19 |

## Platforms and grounds

| # | Requirement | Source | Owner | Status |
|---|---|---|---|---|
| 32 | Fully functional **web build**; the game synchronised across Android, PC and web. Director 2026-10-10. Open question: synchronised = feature/version parity (one codebase, same content, platform-appropriate input and layout) and/or saves carried between devices (cloud or export/import)? Confirm when scheduled | ARD-M8-010 | none: awaiting the director's scheduling | web build live on itch (#667, #791, #779; web.yml, one version string). Open: saves carried between devices (export/import) pending his answer to 1.0 plan Q3 |
| 33 | The visual simulation's oval **dimensions and appearance change with the home ground** (AFL clubs' grounds: MCG, Marvel, Optus, Adelaide Oval, Gabba, People First, GMHBA, SCG, Engie; default elsewhere). Director 2026-10-10. Open: presentation only or sim too; fictional clubs' grounds | ARD-M8-011 | none: awaiting the director's scheduling | MCG look only (#537); per-ground dimensions and looks not started; presentation-only or sim too is still open (1.0 plan Q6) |

## Long-save presentation wishlist (HIGH content, unassigned)

Away/clash and heritage guernseys · coach appearance · finals presentation (bracket prototype #529) · premiership
guernsey history · player card evolution · record-breaker marks · legends wall · Grand Final climax and **season
story recap** · draft class identity · archive gallery · club museum · retirement variants (FL-007 milestones DONE)
· dynamic crowd · custom typography · season poster · stadium identity · user guernseys and logos · **Coach of the
Year** (director request 2026-10-08, not started, not assigned). Deferred by ruling: P-36 weather at the quarter
break, P-55 announce the cap step, P-57 league rule changes.

## In a current plan

Open PR: #888 (AI club decisions: deterministic best-candidate hiring, no sacking cap). Unmerged branches with work:
`claude/match-flow` (row 11), `claude/comeback-audit-row42` (row 42). Nothing else is in flight on main; the
director assigns the next task.
