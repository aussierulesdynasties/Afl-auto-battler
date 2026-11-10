# TODO: everything not done yet

The one list of work not done. Point a session at this file and it works down it. Done and cut items are removed after merge from the PR's `Closes row N` line (git history keeps them). Director rulings live in `docs/DIRECTOR_BIBLE.md` (reference, not a work list); the later ruling wins. Balance is the director's call. There are no feature switches (director 2026-11-06): work goes straight into the game and his playtest judges it (section B). Updated 2026-11-10 against main `eda15c51`: every row checked against merged work. Work it in the order of the "Order of work" section below; a row starts when everything in its "After:" note is done. Audits and balance wait in section Z (director 2026-11-10). Live on itch: 1.0.13 (976718a).

## Itch builds

Which build goes to itch next, and when, is in `docs/ITCH_BUILDS.md` (read it only for a release).

## Order of work (dependency order, 2026-11-10)

A row starts when everything in its "After:" note is done. Rows in the same step run side by side, except rows that edit the same file, which merge one at a time: `tests/run_copy_rules_tests.gd` (its ALLOW counts are exact), `GameState.gd`, `UiKit.gd`, `StoppageVignette.gd`, and the figure shader and sheets.

1. Land the open PRs (#1341 list costs, #1347 draft reads, #1348 free-agency weights). Put the waiting looks and questions to the director (sections C and H, the 6.34 captures, the hair contact sheets) and send the debug APK for row 31. Start the rows with nothing to wait for: 145, 148, 149, 150, 151, T8.85, T7.R84, 6.40, 6.42, 6.51, 6.53, V2, V9, T5.r164. The director's playtests in section B can happen at any time.
2. The rest of T1.R26; V4; 134 and 135 (after 150); the row 34 re-check.
3. 131 (after T1.R26 and 151); 136, 137 and 138; 139; V5; the P-43 press slice of T7.R87; T8.Q20; 6.38.
4. 132, with row 9's club colour; T2.25; 140; 6.63; 32, then 128 (both change the save, so one at a time); T8.78 after 128. The director looks at 5 and 16 and playtests 13, 14 and 15.
5. 133; V6; 6.58. The director playtests 10 and 35/36.
6. 144; the rest of T3.R9; 6.49, then the rest of T7.R87 (both edit MatchScene.gd); 6.64.
7. The director's final looks and playtests (9, 49/50, 24, 26); V8; 56. Every row outside section Z closes before Z starts.
8. Section Z: 11/T2.29, then T2.31 (both edit MatchSim.gd); Traits; Synergy; 30; the T2.25 lanes audit; Z67; the 6.53 phone numbers.
9. Balance; T8.50; T8.83.
10. T8.88; 28; T8.87; then 42 is measured again for the director's ruling.
11. 58/39 dial sizes, then the director's playtest. That closes the list.

The longest chain, which sets the finish: T1.R26, then 131, then the director's look at 5, then 133, then T3.R9, then the final looks, then Traits, then Balance, then T8.88, then 58/39. A delay in T1.R26 or 131 delays everything after it.

## A. Build now (open, no blocker, order = story first, then sim, then approachable)

| # | What | Done looks like |
|---|---|---|
| 153 | The press interview before the draft (director 2026-11-11: "its meant to go before the draft"; follow-up to row 141, which put it after the National Draft in 1.0.14). In progress on branch claude/interview-before-draft (local commit 4e66f0fc): taking a club opens the interview, Continue returns to the draft board. Left: the 2030 Canberra start still skips to the board, and one career_ui test ("The draft board states the Rebuild") expects the board straight after the club | in every start mode the interview opens on taking the club, before any pick, and Continue lands on the board; career_ui, back_nav and onboarding_walk green; merged |
| 150 | Compact player cards show the top three attributes (row 1; director 2026-11-10: "Yes, add them"): Team builder, Training and Off-season. Build before copy passes 134, 135 and 137 | each compact card shows the player's top three attributes at 390 px with nothing clipped, and the director approves the captures |
| 151 | Row 15's late centre ball-up: the two moves become Flood behind the ball and Push numbers forward (director 2026-11-10, D5 Q58). Build before copy pass 131 | both moves play differently on paired seeds, the gate shows each move's gain, cost and odds, and the paired `tools/balance.sh match 1000` table is in the PR |
| 152 | Home grounds for the fictional and expansion clubs (row 6.44; director 2026-11-10): each plays at a real regional ground near its town, e.g. Bellerive or Manuka, with its own ground look. After: the director's look at the six no-name captures in 6.44 | each such club's home ground draws as its real regional ground in a match, and the director has looked |
| 145 | Season story, second slice of the story layer (CareerTale.gd, research PROCEDURAL_COPY_RESEARCH_2026-11-10 §8): fill the almanac's empty `story_parts.arc` sentence from the season's own record, senior-coach voice, no language model After: nothing; build it on the tale helper of #1332 (League news). | the almanac's arc sentence is written from the save for seeded seasons, every number traced to a stored fact, nothing said for a season with no arc; director approves the look |
| 149 | Loosen the UI checks (director 2026-11-10, T7.O15): retire the no-digit checks on screens off the decision gates, and check the stats columns for clipped text instead of exact pixel bands | no test fails on a digit off a decision gate, the stats tests fail only on clipped or overlapping text, and every suite is green |
| 148 | Board goal wording: the middle season goal reads "Stay out of the bottom six" (director 2026-11-10), not "out of the bottom third". ClubLife.gd board reason line and tests/test_club.gd; the target stays 12th or better at 18 clubs, and at 20 and 21 clubs it reads "the bottom seven" | the board line uses the new words at 18, 20 and 21 clubs, the test pins them, and no player-facing line says "bottom third" |
| 144 | Match story, third slice: a richer match story at full time. The save keeps the impact ledger's coach rows per match (director 2026-11-10: "Yes, keep them"; save-schema change, W7 review), since today the coach's in-match calls are dropped at the end of each round After: 133. | a seeded full-time story whose every number traces to the result |
| 131 | Copy voice pass 1, gates (with T1.R26): scripts/sim/GateOdds.gd, MatchSim.gd call cards, CoachReport.gd pep talks and plans; MatchSim's "He should kick it" After: T1.R26 and 151. | every visible line on it reads in the senior coach's voice (docs/VISUAL_STYLE_GUIDE.md §5.1, director 2026-11-10: B), its entries in tests/run_copy_rules_tests.gd ALLOW are gone, its pinned-wording tests updated, and he approves the before/after 390 px captures |
| 132 | Copy voice pass 3, match view and feed: MatchScene.gd lines and the feed's punctuation; the feed keeps a broadcaster's voice and its "!" (director 2026-11-10, #1303). Includes row 9's change: your own goals in the feed in your club's colour, not blue (D6 Q74). After: T1.R26 and 131 | every visible line on it reads in the senior coach's voice (docs/VISUAL_STYLE_GUIDE.md §5.1, director 2026-11-10: B), its entries in tests/run_copy_rules_tests.gd ALLOW are gone, its pinned-wording tests updated, and he approves the before/after 390 px captures |
| 133 | Copy voice pass 4, breaks: MatchNotes.gd, CoachReport.gd break report, MatchStory.gd After: T1.R26, 131 and the director's look at 5. | every visible line on it reads in the senior coach's voice (docs/VISUAL_STYLE_GUIDE.md §5.1, director 2026-11-10: B), its entries in tests/run_copy_rules_tests.gd ALLOW are gone, its pinned-wording tests updated, and he approves the before/after 390 px captures |
| 134 | Copy voice pass 5, team builder and coaching: SelectionScene.gd, CoachingScene.gd (payroll), the team and coaching intros; Auto-pick gets a football name (SkipOrders.gd, StoryEngine.gd, GameState.gd use it too) After: 150. | every visible line on it reads in the senior coach's voice (docs/VISUAL_STYLE_GUIDE.md §5.1, director 2026-11-10: B), its entries in tests/run_copy_rules_tests.gd ALLOW are gone, its pinned-wording tests updated, and he approves the before/after 390 px captures |
| 135 | Copy voice pass 6, training: TrainingScene.gd After: 150. | every visible line on it reads in the senior coach's voice (docs/VISUAL_STYLE_GUIDE.md §5.1, director 2026-11-10: B), its entries in tests/run_copy_rules_tests.gd ALLOW are gone, its pinned-wording tests updated, and he approves the before/after 390 px captures |
| 136 | Copy voice pass 7, draft and pre-season: DraftScene.gd (projection), PreSeasonScene.gd (10 "starter"), the draft and combine intros After: T1.R26. | every visible line on it reads in the senior coach's voice (docs/VISUAL_STYLE_GUIDE.md §5.1, director 2026-11-10: B), its entries in tests/run_copy_rules_tests.gd ALLOW are gone, its pinned-wording tests updated, and he approves the before/after 390 px captures |
| 137 | Copy voice pass 8, contracts and trades: OffseasonScene.gd (payroll), Contracts.gd, DraftTradeSheet.gd, StaffScene.gd; the T3.R56 trade and contract tutorials (shipped in #1293) are rewritten in this voice After: T1.R26 and 150. | every visible line on it reads in the senior coach's voice (docs/VISUAL_STYLE_GUIDE.md §5.1, director 2026-11-10: B), its entries in tests/run_copy_rules_tests.gd ALLOW are gone, its pinned-wording tests updated, and he approves the before/after 390 px captures |
| 138 | Copy voice pass 9, profile: PlayerSheet.gd, and GameState.gd's projection line After: 134. | every visible line on it reads in the senior coach's voice (docs/VISUAL_STYLE_GUIDE.md §5.1, director 2026-11-10: B), its entries in tests/run_copy_rules_tests.gd ALLOW are gone, its pinned-wording tests updated, and he approves the before/after 390 px captures |
| 139 | Copy voice pass 10, stats and menus: stats screens, StatGuide.gd (projection), OptionsSheet.gd, ListScene.gd After: T7.R84, 145 and 149. | every visible line on it reads in the senior coach's voice (docs/VISUAL_STYLE_GUIDE.md §5.1, director 2026-11-10: B), its entries in tests/run_copy_rules_tests.gd ALLOW are gone, its pinned-wording tests updated, and he approves the before/after 390 px captures |
| 140 | Copy voice pass 11, event cards and press: data/stories/*.json (four "should"), StoryEngine.gd, MediaConference.gd, PressScene.gd; the row 34 event-card sheet is rewritten here and shown to him After: the director's ruling on row 34 and the P-43 press slice of T7.R87. | every visible line on it reads in the senior coach's voice (docs/VISUAL_STYLE_GUIDE.md §5.1, director 2026-11-10: B), its entries in tests/run_copy_rules_tests.gd ALLOW are gone, its pinned-wording tests updated, and he approves the before/after 390 px captures |

## B. Built and ON: his playtest judges

Every switch went on for good in #1072 and #1074 (director 2026-11-06: "i dont want any switches"). These are in the game and wait on his playtest; a row closes when it passes. The balance pass over the balance-gated rows is in section Z.

| # | Feature | PRs | Open |
|---|---|---|---|
| 129 | Tasmania on the AFL's real list rules (director 2026-11-09, "do it like this then", "Stars weigh it harder"): rivals' players rated 80+ will not join. Three test careers, 2028: 8-14, 4-18, 4-18 | 1184, 1187 | his playtest of the 2028 start, including the 80 (the agent's number, his to change) and building without the floating compensation year and lists of 48 |
| 61 | Weather: wet, wind and heat fitted to 2016-25 AFL games (live in 1.0.9). Balance stays his call; the look never touches the sim | #1150 #1089 #1084 | his playtest |
| 1 | Top three attributes on cards, Needs work benchmark, scout grade word for hidden prospects | #863 | his playtest, after row 150 (the compact cards show the top three) |
| 9 | Feed colours: your goals good, goals against bad, behinds and calls neutral | #918 | his playtest, after copy pass 132 (which puts your goals in your club's colour) |
| 10 | Kick range caps receiver choice; Sim the week shares the same pick | #857 #879 | his playtest of an exported-PC full match: collection pauses and far receivers gone (about 12 long collects a match remain from other causes). After: T2.25 |
| 49, 50 | Match hero, turning point, reasons; club almanac | #853 #855 #890 | his playtest. After: 145, 144 and 133 |
| 35, 36 | Finals cards slice 2 and Grand Final cards | #864 | his playtest of the eight slice-2 cards (A3, A9, A14, A15, A16, B7, B8, B9), including the B8 running debt. After: the row 34 ruling and 140 |
| 52 | Expansion package, training report, speccy front | #711 #725 #735 #741 #1164 #1174 #745 #1126 #1074 | his playtest of the speccy front and the expansion entry; his look at the training report popup (#1164) |
| 13 | Every in-match decision opens on a vignette scene; time pauses at a decision | #902 #908 | his 1.11 playtest gate. After: T1.R26 and 131 |
| 14 | Opposition goal run as two football moves over the centre ball-up | #903 | his playtest; the two moves stand as built: Stack the centre bounce and Flood behind the ball (director 2026-11-10, D5 Q57). After: T1.R26 and 131 |
| 15 | Late-game centre ball-up: two distinct choices | #899 #1074 | his playtest, after row 151 (the two new moves) and copy pass 131 |
| 24 | Training as a compact player card grid with roles and traits | #928 | his playtest on his phone. After: 135, T3.R9 and 6.34 |
| 65 | Draftees start lower: picks 1-5 about 62, 6-20 about 56, POT kept (4.Q9) | #1031 #1050 | his playtest |
| 78 | Rare big margins come back through Momentum (T8.Q4) | #1029 #1038 | his playtest; balance in Z (row Balance) |
| 89 | Midfield intercepts (T8.Q8) | #1024 | his playtest (measured about 2.58 a game against real 2.5; team intercepts 68.2 against about 63.4); balance in Z (row Balance) |
| 92 | Back-zone carries retuned (T9.Q22) | #1023 | his playtest; balance in Z (row Balance) |
| 103 | Synergies within reach on recruit screens; a stat focus grows a trait, for every club (4.Q10) | #1240 | his playtest; balance in Z (row Balance); numbers: Z, synergy numbers up |

## C. Needs his look or call (shown, then ask)

- 5 Defensive set-up break wording (merged by #874), after T1.R26 and 131. 16 PC bounce scene, after 6.38. 20 Press conference: the black bands were removed in #1120; his look at a capture, after 6.42.
- 7 Shake on his device. 26 Season stats hub phone review, after T3.R9 and 139.
- 34 62-line event-card copy sheet (docs/research/event_card_audit_2026-10-12.md): re-check it against the current deck (#1153 and #1205 changed lines and triggers), show him what still applies, record his ruling and apply it.
- 87 Turnover caption (#617) and the Bring the heat look: show him both again (T2.Q10).
- V0 What does 'beautiful' mean to you: which two or three screens from shipped games would you sit this game beside?

## E. Waiting on him or his phone

- 31 Native phone frame time, battery, loading (needs his phone; PC baseline only).
- 59 Banner text and music: he supplies originals (placeholders in `data/banners.json`, empty playlist).
- 56 Public demo page: rights to real names and a licence register come first.
- 32 Web build parity: saves carried between devices pending his answer.
- 113 Each club's real 2026 National Draft picks, with sources (parked, director 2026-11-10: "the draft hasnt happened yet so park it for now"). The rest shipped as the Real lists start (#569, #1172): real lists, the real 2026 class with ties, the 2026 National Draft, then 2027. Today the opening draft runs in reverse 2026 ladder order (GameState.gd begin_real_lists). Blocked until the real 2026 National Draft has happened.

## F. Later (1.x or after 1.0, unassigned)

- 38 Live-3D vignette probe (low priority; Tripo ruck rig in Godot).
- 43 More Tripo emblems (15,000 credits set aside; first slice done, none further assigned).
- 44 State of Origin (not for 1.0; scope interview first).
- 41 Club Forge game-plan builder.
- 142 Legacy mode: start a career in the 1990s, 2000s or 2010s with that era's real lists (director 2026-11-10, parked). Mostly data: every era needs each club's list rated like the 2026 lists, plus that era's league (Fitzroy and the Brisbane Bears early; Fremantle 1995, Port 1997, Gold Coast 2011, GWS 2012). First slice: 2010. The 2010-2019 lists, drafts, moves, ladders and season stats are in `data/legacy/2010s` (#1324) and the director's era rulings are in the Director Bible (#1327); no game code reads them yet and no player is rated.
- 143 Sandbox mode: every list and every player's numbers editable at any time (director 2026-11-10, parked). A separate mode, and the career wears a visible Sandbox mark so its honours and records don't read as earned (bible: the game is objective about risk). First slice: an Edit player sheet opened from a profile, built on Club Forge and the player Forge; phone first, no spreadsheet editor.
- T3.R41 Team selection as two screens on phone, side by side on PC, no scroll (ruled later, 2026-11-06).
- T3.R10 Accessibility, colour-blind kit-clash check (P-34: every disc pairing through deuteranopia and protanopia simulation, CI contrast floor) and text size on ground and vignette text (#1158 Q3); parked by the director 2026-11-10.
- Player personality types and captaincy meaning (composure, late-game stability): both wanted, later (T5.Q12, T5.Q13).
- Presentation wishlist: away/clash and heritage guernseys, coach appearance, premiership guernsey history, player card
  evolution, record-breaker marks, legends wall, draft class identity, archive gallery, retirement variants, dynamic
  crowd, season poster, stadium identity, user guernseys and logos, Coach of the Year.
- Deferred by ruling: weather at the quarter break, announce the cap step, league rule changes.

## Working rules
- Godot runs off-screen with its own user data (`APPDATA=<scratch dir>`); kill only your own PIDs.
- Balance: screen every balance-gated row or match-engine change with `tools/balance.sh match 1000` (paired: main vs the branch, `--a-root <main checkout> --b ""`) before the PR and paste its table in the PR body; extend the harness rather than writing one-off probes (tools/balance/README.md).
- Run only the suites your change touches locally; CI runs the rest. Long audits go to `audit.yml`.
- Revert `.import` and `.uid` churn before committing. Stage by name; never `git add -A`.
- One worktree per session, from `origin/main`. Don't push to a PR branch while its CI runs unless the merge needs it.
- Never edit this file in a feature PR: write `Closes row N` (or `Closes rows 22, 27`, `Closes row T5.Q24`) in the PR body and `roadmap_close.yml` deletes the row after the merge. Edits to the list itself (new director requests, with his words) go in a PR labelled `roadmap`.

## G. From the Bible check (2026-11-04): open and not built

Ids point at `docs/DIRECTOR_BIBLE.md`. Verified against the code on 2026-11-04, re-checked against main on 2026-11-10 (#1278).

| Id | What | Done looks like |
|---|---|---|
| 128 | Stretch goal, a real state league (director 2026-11-08: "real VFL/seconds league with real rosters. players can choose to start their careers there and rise up the ranks. or can take a job at alower league if they lose their afl job and fight their way back"). Assigned 2026-11-10 ("Build it"); first slice to be put to him. Builds after T7.R84 and T8.Q20 (the same weekly sim loop). Already in the game to build on: the way-back story after a sacking, coaches' "Coaching in the state league" history, VFL clubs as prospect origins, the reserves. After: T8.Q20, T7.R84 and 32. | a career can start at a VFL club on sourced real lists and rise to an AFL job; a sacked coach can take a VFL job and fight back |
| T1.R26 | Finish the decision-transparency job on the gates still open: "I want full transparency behind each decision and the impact it will have"; "RNG is still okay, as long as the risks are clearly defined in the decision gate." Rulings 2026-11-10: "Gain / Cost everywhere" (odds inside the line); M1 "Gain for this list today" with the suits-it figure beside; L1 "Everything follows the read"; L2 "One scouting-budget line"; L4 "Costs in the rule's spirit" (morale, cap, legs, each sized); C1 "Cost sheet, one look". Done: M1, M2, M3, M5, M6 and the M7 set shot (#1317), C1 Tribunal cost sheet (#1336); S1, S2 and C2 (#1335) are met; L4 list costs is PR #1341, L1 and L2 are PR #1347, FA weights are PR #1348. Gates to build, in this order (director 2026-11-10 left the order to Claude): M4 rotation sizes, the other M7 in-match cards and the list's dominant options, and L3 rival reads after measuring. | Each listed gate shows a gain, a cost and its odds in the ruled label wording, and no gate is left with a dominant option; the C1 cost sheet gets his one look before it is built. |
| T2.25 | Kick lanes (M4-014): corridor, switch and down the line chosen by game plan in place of the random 10% switch. Director: "lanes are recorded and affect play, not presentation only." The old claude/kick-lanes branches are gone from origin and nothing is on main. Lanes audit in Z After: T8.85 and 131. | PR merged on green with the lane recorded per kick, play affected by plan and a motion clip of the three lanes. |
| T3.R9 | Readability sweep, one screen per PR in the order he sees them: hub, match view, breaks, team builder, training, draft, contracts and trades, profile, stats, menus. Then the match-view centrepiece pass ('looks like PowerPoint'). His words: "readability and intuitive interfaces are a core pillar of this project, paramount to its success". Batches 1 and 2 only partly cover stats and menus (390x844 and 1280x720, no record he looked). Hub done (story card text to body size, opponent lines in TEXT under their club's bar; `tools/visual/capture_sweep.gd`). Match view done, with its centrepiece pass (crowd in the stand, lit turf, shaded discs, light edge on dark kits, oval text at the 13 px floor, bigger PC score). Left: breaks, team builder, training, draft, contracts and trades, profile, stats, menus. After: V4 and V5; each screen after its copy pass (133 to 139). | Each screen has before/after captures at 390 and 1920 px that the director has looked at, and the match view has been reworked and shown to him. |
| T5.r164 | Story beats for international players (#752, #815): only the phone check is left. | An international story card played on a phone (or a real tap at 390x844 portrait), answered, with the Gain and Cost result shown. |
| 6.34 | Styling looks STYLE-01/03/04/05/06 (#1250-#1255): his verdict on each look, recorded (a look merged before approval needs it, or a revert). Missing captures: STYLE-05 headers on Main, STYLE-04 on the match oval (bible ruling 34), STYLE-03 on named screens; the Training rows fix (#1250). After: nothing; it needs the windowed-capture fault fixed first (UiKit, StoppageVignette and HubScene fail to compile in a windowed run). | Each look is shown to the director as a capture on those screens with his verdict recorded, and the Training rows line up on a phone capture. |
| 6.38 | Vignette broadcast atmosphere, in the director's words 'it looks bizarre how there are no background players or atmospheric details': the centre bounce (StoppageVignette) needs both teams' 6-6-6 set-ups, the other field umpires, boundary umpires on the wings and goal umpires; cheer squads, banners and a lit club-colour crowd beyond VignetteCrowd and #996; distant players as cheap sprites. After: 6.42, the row 31 phone frame time and the director's animation calls (section H). | Match scene captures show the extra people and atmosphere with no frame-rate drop on a phone, and the director has looked. |
| 6.40 | Written inventory of every vignette renderer (Broadcast, AwardWinner, Stoppage, Decision, Farewell, PreMatch and the Vignette* helpers) and fallback (such as OLD_FRONT_DURATION and the average-build fallback in _figure) ('entirely replace the old vignette art style with the new pre-rendered 2.5D footballer style'). | The inventory doc exists and confirms no old-style figure path is left. |
| 6.42 | Rendered Blender plates for the press room, awards stage and MCG with crowd, replacing the painted stands ('do what you think is best, but I expect beautiful results'). | Each plate is in the game in its scene and the director has looked at captures. |
| 6.44 | Ground looks beyond the MCG so 'a footy fan recognises the MCG, Marvel, Optus, Adelaide Oval, the Gabba, GMHBA and the SCG without the name' (#967). Left: his look at the no-name captures of the six, and the fictional clubs' grounds: each plays at a real regional ground near its town, e.g. Bellerive or Manuka (director 2026-11-10), a new ground look per club. After: nothing; the fictional grounds are built in row 152. | He has looked and recognises the six, and his ruling on the fictional grounds is recorded. |
| 6.49 | Oval-broadcast bundle 2 (P-31, P-32, P-33; P-34 is in T3.R10; P-35 skipped): breeze end shown, crowd, and a skippable post-full-time goals replay from the event log. After: V6. | All three show in a played match and the replay skips with one tap, proven with a real tap. |
| 6.51 | Crowd knows the score: crowd noise rises with goal runs, home crowd louder than away, siren at every quarter end, and the gap between event and sound measured. | A match audio check shows each behaviour and a measured event-to-sound gap. |
| 6.53 | Free shader polish and lighting: restrained figure shadow and highlight in figure.gdshader, soft contact shadows, baked lighting on the figures first (rule 53). #996 did the grade and atmos pass only. Idle and battery numbers in Z | Before and after captures stored and reported. |
| 6.58 | Hair library: all 16 styles draw (#998, on), but about ten short styles (buzz, crew, side part, messy medium, curly, afro) look alike at figure scale; beards and boots go back to the art work. After: the director's answer on the hair, beard and boot ids (section H) and 6.63. | Each style reads apart at figure scale and the director has approved the look. |
| 6.63 | Tattoos: premiership-year ink is done (#1258). Left: the original tattoo library (bible item 63: rose, snake, barbed wire, bird, 666, love heart, Southern Cross stars, checked Asian-script lettering) drawn from the per-player Appearance field; ink on the speccy strips, carrier_near, the umpire's bounce and the coach; correct arm on mirrored moves; years readable at match size; his look at the ink. After: 6.38 and 6.53. | Tattoos draw on figures, are saved once, change no match result, and he has looked. |
| 6.64 | Club Forge appearance options still hidden or missing: socks, headbands, bandaging, Forge-chosen tattoos and facial hair (hidden by SHOW_UNDRAWN_LOOKS until figures draw them), boots and boot colour, beard colour; and Forge import/export as a 256x128 PNG. Skin tone, hair, foot, number and nickname are built. After: 6.58. | Each option is drawn on the figures and saved, and a PNG round-trips through import and export. |
| T7.R84 | Release engineering for saves. Left: a "Restore last good save" from the .bak, frozen fixtures for later versions (only `tests/fixtures/career_v1_2026-09-30.save.gz` exists; VERSION is 2), and a quiet version line with patch notes shown once. Corrupt and newer saves are handled (#945, #973). | Frozen fixtures for each later save version load in a test; Restore last good save works from the menu; patch notes show once per version. |
| T7.R87 | Pass-2 bundles the director said yes to ("All eight theme bundles: yes"), Tier A and B in listed order. P-12 (oval answers a structural call, #784 and #800) and P-70 and P-71 (offline promise, backup, #779) are built. Still to build: P-25 to P-29 match day on a phone, P-72 patch notes name the football change, P-73 answer every review within a week, P-74 the Not in this game page and P-43 (P-52 carnival built in #969). After: the P-43 press slice needs nothing; the rest after V6, T7.R84 and 6.49, and P-74 after the director's list. | One row per remaining P-number with a PR, each proved on a phone-width capture or a test; P-30 and P-75 stay skipped. |
| T8.Q20 | Make the weekly sim faster. Director: "#888 sim 35% slower is accepted for now; optimise the weekly AI in a later PR (next task = the sim-speed PR); the coach pool of 57 is fine as is." Win back the lost time in the weekly AI work, with the same results. After: T1.R26's L3 and FA slices, so the seeded results stay byte-identical. | 3-season bench of weeks is back near main's pre-#888 146 s (from 225 s); seeded results byte-identical before and after; coach pool stays at 57. |
| T8.78 | P-78: a time budget for each player action (tap to screen, Sim the week, rollover), checked by a test. Director: "Yes" (Q8, audits that protect the fun, 2026-10-18); "Build it now" (2026-11-10, over T7.O19 "not now"), after T8.Q20 and 128. After: T8.Q20 and 128. | One budget table in a data file, a check that fails when an action runs over its budget, and the first baseline run recorded. |
| T8.85 | P-76: picture and truth never disagree. Every tick, no disc moves faster than a footballer or jumps; the ball is always with a player or in flight; 36 discs at 8x; feed, scoreboard and engine score agree; the intended sheet loaded, not a fallback. Director: "Yes" (Q8, 2026-10-18). Today speed caps run at 1x and 4x only and disc jumps are checked for one quarter at 4x. | A seeded match suite asserts all five each tick at 8x and goes red if a ball hovers or a disc jumps. |

## V. Visual direction (rulings 2026-11-04)

The director's visual rulings V-R1 to V-R9 are in Rulings (director, 2026-11-04).

| Id | What | Done looks like |
|---|---|---|
| V2 | Premiership streamers in club colours | plays once on the premiership screen only, a capture frame shows both club colours |
| V3 | Brownlow winner reveal: 24 gold sparkles After: V2. | plays once on the winner reveal only, 24 sparkles, a capture frame |
| V4 | Elevation scale and an automatic contrast test After: #1341, whose new screens its contrast test covers. | BG, PANEL, PANEL_ALT, INK and SURFACE in UiKit.gd form one ordered scale; one test walks every club (including a Forge club) and fails a primary fill under the contrast floor against its label, page or panel, or too close to BAD, and fails any text under the floor on every surface step |
| V5 | Training results is the proof screen for the new look, then the hub, then the other screens After: V4, 135 and 6.34. | director approves Training results on his phone before the hub starts, then the hub before the rest |
| V6 | Match chrome: scorebug 56 to 72 px, bottom decision sheet about a third of the height, one-button transport, goal and siren poster card After: 132. | captures at 390x844, the oval gets the freed height, every decision reachable with a real tap |
| V7 | Navigation icon set (AI-assisted candidates) | one icon per hub destination, director approves or rejects |
| V8 | Refresh captures of every screen on current main (the newest are 2026-10-07 to 10-11) After: T3.R9 and copy passes 131 to 140. | one capture per screen at 390x844, dated, in the audit folder |
| V9 | Housekeeping: placeholder logo name, stale worktrees (`The MCG.glb` is already out of the repo) | logo name is final or marked placeholder in one place, `git worktree list` shows only live ones |

## Rulings (director, 2026-11-04)

Settled answers that are not build rows. The bible stays as it is unless he consents to a change.

- A TODO row is authorisation to build it; a roadmap entry alone is not. With no task, work the TODO.
- Any doubt is a fail (critic agents are gone since 2026-11-05: every visual goes to him after the session's own frame check). This fully replaces the 2026-10-18 "don't chase marginal gains" line.
- Game, simulation and story carry equal importance. Secondary buttons are outlines.
- Press answers are seeded rolls with the odds and both outcomes shown (the bible line stands; already shipped).
- Polish goal 1 (player agency in matchups and rotation changes) stays open as written.
- Teaching is XP scaling, not the season-ceiling point.
- Personality types and captaincy are both wanted, later (section F). Culture sizes were reviewed in #988 (row 68).
- 4.Q5 (Ask around, untouchable, pick order from round 18, pick trade on draft night) are all built: untouchable and pick order from round 18 (#783), pick trades on draft night (#848), Ask around (#971).
- Row 13 gets all five scenes and waits for the 1.11 playtest gate (on since #1074, no switches). Time pauses at a decision, so scenes never fight live speed.
- Weather has full effect on play (T1.Q2, T2.Q2, 6.Q10, T8.Q7): wet tackles move toward the real +12% (row 61); how it looks never touches the sim. Weather is off the bible's open list.
- Ladder goes into Season stats (T3.Q13, T9.Q29): the hub nav bar loses Ladder, no other nav change (shipped).
- Price: free for now. Platforms: web, Windows and an Android APK on itch; Google Play only on his written yes (US$25 fee and signing key).
- Old PRs #745, #761 and #765 were already merged; nothing to close.
- Visual direction (section V; style guide updated to match V-R1 to V-R4):
  - V-R1 CLAUDE.md governs over the style guide: gradients and glows are allowed when deliberate.
  - V-R2 The primary button may be filled with club colour. A red club may clash with BAD, so a contrast and collision check is required.
  - V-R3 Navigation icons and relaxed motion (sliding sheets, count-ups, screen transitions) are allowed.
  - V-R4 ARD Regular stays for small body text; no Barlow A/B.
  - V-R5 Particles only for the premiership (club-colour streamers) and the Brownlow winner reveal (24 gold sparkles).
  - V-R6 The live match stays a refined diagram; the vignettes are the showpiece. No following camera, no 3D restart plan, no Clay Oval proof now.
  - V-R7 Lowest supported phone: a recent mid-range, about 2023.
  - V-R8 Figure sheets and the eight vignette scenes are kept; any deletion waits for a future decision.
  - V-R9 Nav icons and the wordmark are AI-assisted candidates; the director approves or rejects.
- Draft AI key-forward spread (2026-11-05): "Leave it as is". Young talls keep their potential credit; no change.
- Draft AI veterans (2026-11-05): "viney yes, but petracca and stewart should be 125-150"; "petracca is being underrated based on low games, hes very very good". Petracca overridden to 87; building clubs count a retired season at 0.35 dilution. Now Petracca 128, Stewart 138, Viney 301 mean pick.

## Rulings (director, 2026-11-06)

- GitHub deletes a PR's branch when it merges (T7.O20; turned on 2026-11-06).
- League balance and calibration suites run nightly only, not on every PR (T7.O14). Superseded for balance-threshold checks by the 2026-11-10 ruling (they move out of the nightly).
- Phone performance budgets and a CI perf gate: not now (T7.O19).
- Tests: "do a small amount on my pc the rest github" (T7.O20b): GitHub keeps CI; local runs stay small (balance screens, single suites). No self-hosted runner.
- Trade value keeps counting 60% of unproven growth (T8.Q13).
- The visual sim reacting to coaching goes before the Season stats patch (T9.Q7).
- Skills travel with the player: "their skills dont change based on position" (T9.Q27). Tap v mobile rucks, swingmen, tall v small defenders and unicorns stay deferred.
- Playtest gate 1.12 "Can I feel my decisions?" is adopted (T9.Q28).
- No single first among the audit's biggest gaps: "all are important no focus on anything particular" (T9.Q30).
- Cascadeur Indie: written yes to buy (6.Q20). The exact price is shown to him first and he makes the purchase; the gather-on-the-run and other animation calls stay open.
- The bible's Current focus section moves here (T5.Q21, his consent 2026-11-06); see Current focus below.
- Kept as they are: Club Forge create a player, the Coaching screen (T1.Q7).
- 1.x is not frozen: features can still land (T7.O4). AFLW moves to later; Google Play is much later. Team selection as two screens is later (T3.R41).
- The game deliberately has no paid extras, no ads and no direct player control on the field (T5.Q21).

## Rulings (director, 2026-11-10)

- Audits and balance come last: "I also want to defer all audits until after all other roadmap rows are done"; "pointless to constantly audit an ever changing database; we can rigorously audit and balance after the game is fully featured." They sit in section Z.
- A build row whose done-test contains an audit closes when the build ships; the audit moves to section Z as its own row ("Yes, split them").
- Balance-threshold test checks move out of the nightly.
- The career story (procedural copy, first slice): on the player sheet and on Brownlow night; up to five sentences, like the almanac; a career with nothing worth a story shows nothing, no filler line; Claude drafts the phrasings in the senior-coach voice and he edits them; one plain register everywhere, a failed pick told plainly, no warmer farewell text. Look approved from the 390px captures ("Approve, ship it"). Built in #1334 (CareerTale); the season and match stories are rows 145 and 144.
- Compact player cards (Team builder, Training, Off-season) show the top three attributes: "Yes, add them" (row 1).
- Row 14's goal-run moves stand (Stack the centre bounce, Flood behind the ball). Row 15's late centre ball-up changes to Flood behind the ball and Push numbers forward.
- Your own goals in the feed show in your club's colour, not blue (D6 Q74).
- The board's middle season goal is 12th or better at 18 clubs, worded "Stay out of the bottom six", never "outside the bottom third" (T9.Q20).
- The save keeps the impact ledger's coach rows per match: "Yes, keep them" (research question 5, row 144).
- Row 128, the VFL state league: "Build it".
- The transparency gate order (T7.R89): "you decide"; the order is in row T1.R26.
- Fictional and expansion clubs play at a real regional ground near their town, e.g. Bellerive or Manuka (Q51, row 6.44).
- Row T8.78, the time-budget test: "Build it now"; it overrides T7.O19 "CI perf gate: not now".
- Retire the no-digit checks off the decision gates, and check the stats columns only for clipped text, not exact pixels (T7.O15).
- Coleman cap: the 99.5th percentile (row 30).

## Rulings (director, 2026-11-11)

- The press interview that sets the coaching style comes before the draft: "its meant to go before the draft". It opens as soon as the coach takes a club, in every start mode, and Continue returns to the draft board for the first pick (row 141 follow-up; 1.0.14 shipped it after the National Draft).

## Current focus (moved from the bible, 2026-11-06)

Polish is the gap. There are two big tickets, and one priority above both.

**The single biggest improvement to game feel:** players in the visual sim really react to your coaching moves.

1. **Player agency fine-tuning.** In-match decisions and in-match and pre-game coaching moves, such as matchups and rotation changes. Each decision should feel like it has a real in-match impact and be easily measurable.
2. **Visual polish.** It should not look like an app. It should feel clean and crisp like a great app does, but also personal, like a hand-crafted game.

## H. Needs his call (questions still open, one at a time)

Each line is a question he has not answered yet. Answered ones are in Rulings or in section A.

- Are the hair, beard and boot ids final, and what happens to the 24-style hair, 10-beard and boot contact sheets he has not looked at? (6.Q4)
- His calls on the open animation decisions including the gather-on-the-run proof (Cascadeur spend is a yes)? (6.Q20)
- Which rows make up 1.1 ("tune and polish"): his looks on pre-season, draft night and the oval ring, and which Tier A items? (T7.O5)
- Which of P-01 to P-11, P-16, P-19, P-21, P-22 and P-24 does he take? (T9.Q31)

## Z. Last: audits and balance (after every other row is done)

Director 2026-11-10 (Rulings 2026-11-10): no audit or balance tune until every other row is done. Each row names the build row it came from.

| Id | What | Done looks like |
|---|---|---|
| 28 | How-we-play maturity; How-we-win materiality; List Profile vs results (seeded, via audit.yml) After: T2.25, T1.R26 and Traits. | a seeded audit and evidence doc for each |
| Z67 | Management pays audit, after row 67's trade lever: re-run tools/audit/levers2_impl.gd with the trade period at real volume, recruiters' edge and development projects; balance-gated After: T1.R26. | audit across 8-10 seasons, paired `tools/balance.sh match 1000` table in the PR |
| 11, T2.29 | Spoils, intercept marks and ground-ball gets (M3-003). Spoils 22.8-23.2 a team against real 30.7, between the arcs 4.6-5.1 against 14.5-20.2 (#1199, #1241; forward 50 spoils are done). Intercept marks (0.76) and ground-ball gets (0.71) not re-measured since #897; the harness needs an intercept-marks stat and a real ground-ball-gets reference first After: the T2.25 lanes audit. | a tune that keeps contested marks, rebound 50s and disposals in range, and a seeded screen shows spoils, intercept marks and ground-ball gets IN |
| T2.31 | Ruck integrity (M1-002): write the audit doc from the harness Rucks section (#1121): the number-one ruck's to-advantage 35.2% against 29.6% (NEAR), hit-outs per ruck contest 55.2% against 42.5% (OUT, a counting artifact per #1121); find a real duel-spread reference or his acceptance of the club-spread proxy; state tune or no tune. Clearances stay random After: 11/T2.29 (both edit MatchSim.gd) and the director's answer on the club-spread proxy. | audit doc with real ranges, the duel spread and the stated diagnosis; any tune follows it |
| T2.25 | Paired-seed kick lanes audit, after row T2.25 ships | lanes recorded per kick differ by plan on paired seeds |
| 6.53 | Idle and battery numbers for the lighting change (#996) and the row 6.53 shader work | idle and battery numbers reported, before and after |
| Synergy | Synergy numbers up (director 2026-11-10: "if anything i wanna boost synergy numbers but thats for later"). The row 103 audit had 47% of rival clubs fielding a synergy on main, 57% with row 103. Supersedes DIRECTOR_BIBLE ruling 23 (15-25% of clubs, mostly 0-1). Target: "i think teams at the bottom of the ladder should have 0-1 synergies, teams in the top 4 probably have 2-4 synergies" After: the row 103 playtest. | a seeded audit of synergies per club by ladder position: bottom clubs 0-1, top 4 at 2-4 |
| T8.87 | P-79: no plan wins everywhere. Seeded round-robin of every plan against weak, even and strong lists. Director: "Yes" (Q8, 2026-10-18). Reports only. After: T2.25, T1.R26 and Traits. | A shared-seed audit run on CI, with a result written into the term sheet in football words and the share of opponents the best plan beats; no tuning made. |
| T8.88 | P-80: fun floor beside the realism floor. A dynasty bot plays 20 seasons on many seeds and records how often it makes finals within five seasons and wins a flag within fifteen. Director: "Yes" (Q8, 2026-10-18). Feeds the dial sizes, never declares balance done. After: Balance. | A CI audit and an evidence doc giving the finals-in-five and flag-in-fifteen rates against the director's 'a flag every 8-10 seasons'; no constants changed. |
| T8.83 | Long-career integrity soak. Director: "Test decades-long / 100+ year careers." Start with 5, 10 and 20-year careers, then 8 careers x 20 seasons x 4 policies. The old long_career audit only measures lists and retirements. After: 144, T7.R84 and 128. | CI run shows zero integrity violations (duplicate history, ghost players, impossible lists), season-20 save under 3x season-2, round time under 1.5x. |
| T8.50 | Potential inflation: show how many 90+ ceilings there are by age, role and club, and what long careers do with them. No blanket nerf. The existing audit covers age band, position and source only. After: Synergy. | Evidence doc with distributions by age, role, club and source plus long-career outcomes; any change goes to the director first. |
| 30 | Coleman goalkicking cap: the clamp moves from the 98th to the 99.5th percentile (director 2026-11-10, bible Q120) | a seeded screen with the Balance pass |
| 58, 39 | Difficulty dial sizes (board patience, rival recruiting) and pre-season balance sizes After: T8.88 and Balance. | sizes set from his playtest |
| 42 | Comebacks match real AFL on 9,600 matches (docs/COMEBACKS_EVIDENCE_2026-11-05.md); loosen the close-finish band (65.8% v 57.5%) or not After: Balance. | his ruling |
| Traits | Game-plan trait sizes (director 2026-11-10: "we will balance test them vigorously later, for now just build and ship"). First screens (one side running each, 1,000 paired matches): The Cluster +7.4 margin, Kick-Mark Masters -4.7, Fast Starters +3.0, Never Say Die -1.9, the rest within 2 se of 0. Front-Runners and Never Say Die lean on Fire them up, which the harness never calls; Hard Trainers and Long Bombers' costs barely show in one match. Sizes are named consts in scripts/sim/PlanTraits.gd After: T1.R26 and T2.25. | a screen of each trait with Fire them up in play, sizes set so no trait wins or loses on the scoreboard; settled only when his playtest also passes |
| Balance | Balance pass: first run every suite with `BALANCE_CHECKS=1` (64 real-AFL threshold checks wait behind tests/balance_gate.gd; misses log a `BALANCE_DEFERRED` line meanwhile) and fix or rule on each; then every balance-gated feature in section B (78, 89, 92, 103), screened together as one match (match_flow, kick_range, set_shots, key_duels, mid_intercepts, back_carries and momentum_runaway were never screened together, #1074) After: 11/T2.29, T2.31, Synergy, Traits and 30. | paired `tools/balance.sh match 1000` table; balance settled only when his playtest also passes |
