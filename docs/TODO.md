# TODO: everything not done yet

The one list of work not done. Point a session at this file and it works down it. Done and cut items are removed after merge from the PR's `Closes row N` line (git history keeps them). Director rulings live in `docs/DIRECTOR_BIBLE.md` (reference, not a work list); the later ruling wins. Balance is the director's call. There are no feature switches (director 2026-11-06): work goes straight into the game and his playtest judges it (section B). Updated 2026-11-10 against main `f2467685`: every row checked against merged work. Audits and balance wait in section Z (director 2026-11-10). Live on itch: 1.0.10 (4bbab26).

## Itch builds

Which build goes to itch next, and when, is in `docs/ITCH_BUILDS.md` (read it only for a release).

## A. Build now (open, no blocker, order = story first, then sim, then approachable)

| # | What | Done looks like |
|---|---|---|
| 131 | Copy voice pass 1, gates (with T1.R26): scripts/sim/GateOdds.gd, MatchSim.gd call cards, CoachReport.gd pep talks and plans; MatchSim's "He should kick it" | every visible line on it reads in the senior coach's voice (docs/VISUAL_STYLE_GUIDE.md §5.1, director 2026-11-10: B), its entries in tests/run_copy_rules_tests.gd ALLOW are gone, its pinned-wording tests updated, and he approves the before/after 390 px captures |
| 132 | Copy voice pass 3, match view and feed: MatchScene.gd lines and the feed's punctuation; the feed keeps a broadcaster's voice and its "!" (director 2026-11-10, #1303) | every visible line on it reads in the senior coach's voice (docs/VISUAL_STYLE_GUIDE.md §5.1, director 2026-11-10: B), its entries in tests/run_copy_rules_tests.gd ALLOW are gone, its pinned-wording tests updated, and he approves the before/after 390 px captures |
| 133 | Copy voice pass 4, breaks: MatchNotes.gd, CoachReport.gd break report, MatchStory.gd | every visible line on it reads in the senior coach's voice (docs/VISUAL_STYLE_GUIDE.md §5.1, director 2026-11-10: B), its entries in tests/run_copy_rules_tests.gd ALLOW are gone, its pinned-wording tests updated, and he approves the before/after 390 px captures |
| 134 | Copy voice pass 5, team builder and coaching: SelectionScene.gd, CoachingScene.gd (payroll), the team and coaching intros; Auto-pick gets a football name (SkipOrders.gd, StoryEngine.gd, GameState.gd use it too) | every visible line on it reads in the senior coach's voice (docs/VISUAL_STYLE_GUIDE.md §5.1, director 2026-11-10: B), its entries in tests/run_copy_rules_tests.gd ALLOW are gone, its pinned-wording tests updated, and he approves the before/after 390 px captures |
| 135 | Copy voice pass 6, training: TrainingScene.gd | every visible line on it reads in the senior coach's voice (docs/VISUAL_STYLE_GUIDE.md §5.1, director 2026-11-10: B), its entries in tests/run_copy_rules_tests.gd ALLOW are gone, its pinned-wording tests updated, and he approves the before/after 390 px captures |
| 136 | Copy voice pass 7, draft and pre-season: DraftScene.gd (projection), PreSeasonScene.gd (10 "starter"), the draft and combine intros | every visible line on it reads in the senior coach's voice (docs/VISUAL_STYLE_GUIDE.md §5.1, director 2026-11-10: B), its entries in tests/run_copy_rules_tests.gd ALLOW are gone, its pinned-wording tests updated, and he approves the before/after 390 px captures |
| 137 | Copy voice pass 8, contracts and trades: OffseasonScene.gd (payroll), Contracts.gd, DraftTradeSheet.gd, StaffScene.gd; the T3.R56 trade and contract tutorials are written in this voice | every visible line on it reads in the senior coach's voice (docs/VISUAL_STYLE_GUIDE.md §5.1, director 2026-11-10: B), its entries in tests/run_copy_rules_tests.gd ALLOW are gone, its pinned-wording tests updated, and he approves the before/after 390 px captures |
| 138 | Copy voice pass 9, profile: PlayerSheet.gd, and GameState.gd's projection line | every visible line on it reads in the senior coach's voice (docs/VISUAL_STYLE_GUIDE.md §5.1, director 2026-11-10: B), its entries in tests/run_copy_rules_tests.gd ALLOW are gone, its pinned-wording tests updated, and he approves the before/after 390 px captures |
| 139 | Copy voice pass 10, stats and menus: stats screens, StatGuide.gd (projection), OptionsSheet.gd, ListScene.gd | every visible line on it reads in the senior coach's voice (docs/VISUAL_STYLE_GUIDE.md §5.1, director 2026-11-10: B), its entries in tests/run_copy_rules_tests.gd ALLOW are gone, its pinned-wording tests updated, and he approves the before/after 390 px captures |
| 140 | Copy voice pass 11, event cards and press: data/stories/*.json (four "should"), StoryEngine.gd, MediaConference.gd, PressScene.gd; the row 34 event-card sheet is rewritten here and shown to him | every visible line on it reads in the senior coach's voice (docs/VISUAL_STYLE_GUIDE.md §5.1, director 2026-11-10: B), its entries in tests/run_copy_rules_tests.gd ALLOW are gone, its pinned-wording tests updated, and he approves the before/after 390 px captures |
| 141 | How a career starts (director 2026-11-10: "if you click YES to canberra joining, you should be warned that the game will sim to 2030, you also dont get the interview then.. which you should / interview should happen in every game mode"): a warning with Back before a 2030 start; the press interview that sets your coaching style in every start, the shipped-history starts (2030 with Canberra, Tasmania in 2028) included | Yes to Canberra on the real lists warns, Back cancels; every start mode reaches the press interview and its answers set the coaching style as in the standard start; real taps at 390x844; he approves the captures |

## B. Built and ON: his playtest judges

Every switch went on for good in #1072 and #1074 (director 2026-11-06: "i dont want any switches"). These are in the game and wait on his playtest; a row closes when it passes. The balance pass over the balance-gated rows is in section Z.

| # | Feature | PRs | Open |
|---|---|---|---|
| 129 | Tasmania on the AFL's real list rules (director 2026-11-09, "do it like this then", "Stars weigh it harder"): rivals' players rated 80+ will not join. Three test careers, 2028: 8-14, 4-18, 4-18 | 1184, 1187 | his playtest of the 2028 start, including the 80 (the agent's number, his to change) and building without the floating compensation year and lists of 48 |
| 61 | Weather: wet, wind and heat fitted to 2016-25 AFL games (live in 1.0.9). Balance stays his call; the look never touches the sim | #1150 #1089 #1084 | his playtest |
| 1 | Top three attributes on cards, Needs work benchmark, scout grade word for hidden prospects | #863 | his playtest; the compact cards (Team builder, Training, Off-season) do not show the top three (bible 4.48), his call |
| 9 | Feed colours: your goals good, goals against bad, behinds and calls neutral | #918 | his playtest; blue or not for your goals (bible D6 Q74) |
| 10 | Kick range caps receiver choice; Sim the week shares the same pick | #857 #879 | his playtest of an exported-PC full match: collection pauses and far receivers gone (about 12 long collects a match remain from other causes) |
| 49, 50 | Match hero, turning point, reasons; club almanac | #853 #855 #890 | his playtest |
| 35, 36 | Finals cards slice 2 and Grand Final cards | #864 | his playtest of the eight slice-2 cards (A3, A9, A14, A15, A16, B7, B8, B9), including the B8 running debt |
| 52 | Expansion package, training report, speccy front | #711 #725 #735 #741 #1164 #1174 #745 #1126 #1074 | his playtest of the speccy front and the expansion entry; his look at the training report popup (#1164) |
| 13 | Every in-match decision opens on a vignette scene; time pauses at a decision | #902 #908 | his 1.11 playtest gate |
| 14 | Opposition goal run as two football moves over the centre ball-up | #903 | his playtest; which two moves (bible 2.Q8, D5 Q57): built as Stack the centre bounce and Flood behind the ball |
| 15 | Late-game centre ball-up: two distinct choices | #899 #1074 | his playtest; are Stack the stoppage and Flood behind the ball the right two (bible 2.Q9, D5 Q58) |
| 24 | Training as a compact player card grid with roles and traits | #928 | his playtest on his phone |
| 65 | Draftees start lower: picks 1-5 about 62, 6-20 about 56, POT kept (4.Q9) | #1031 #1050 | his playtest |
| 78 | Rare big margins come back through Momentum (T8.Q4) | #1029 #1038 | his playtest; balance in Z (row Balance) |
| 89 | Midfield intercepts (T8.Q8) | #1024 | his playtest (measured about 2.58 a game against real 2.5; team intercepts 68.2 against about 63.4); balance in Z (row Balance) |
| 92 | Back-zone carries retuned (T9.Q22) | #1023 | his playtest; balance in Z (row Balance) |
| 103 | Synergies within reach on recruit screens; a stat focus grows a trait, for every club (4.Q10) | #1240 | his playtest; balance in Z (row Balance); numbers: Z, synergy numbers up |

## C. Needs his look or call (shown, then ask)

- 5 Defensive set-up break wording (merged by #874). 16 PC bounce scene. 20 Press conference black bands gone?
- 7 Shake on his device. 26 Season stats hub phone review.
- 34 62-line event-card copy sheet (docs/research/event_card_audit_2026-10-12.md): re-check it against the current deck (#1153 and #1205 changed lines and triggers), show him what still applies, record his ruling and apply it.
- 87 Turnover caption (#617) and the Bring the heat look: show him both again (T2.Q10).
- 40/41 Own game plan builder (game as is; Club Forge): decision waits on his plan-drilling play.
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

Ids point at `docs/DIRECTOR_BIBLE.md`. Verified against the code on 2026-11-04, re-checked against main on 2026-11-07.

| Id | What | Done looks like |
|---|---|---|
| 128 | Stretch goal, a real state league (director 2026-11-08: "real VFL/seconds league with real rosters. players can choose to start their careers there and rise up the ranks. or can take a job at alower league if they lose their afl job and fight their way back"). Not started and not assigned yet. Already in the game to build on: the way-back story after a sacking, coaches' "Coaching in the state league" history, VFL clubs as prospect origins, the reserves. | a career can start at a VFL club on sourced real lists and rise to an AFL job; a sacked coach can take a VFL job and fight back |
| T1.R26 | Finish the decision-transparency job on the gates still open: "I want full transparency behind each decision and the impact it will have"; "RNG is still okay, as long as the risks are clearly defined in the decision gate." Rulings 2026-11-10: "Gain / Cost everywhere" (odds inside the line); M1 "Gain for this list today" with the suits-it figure beside; L1 "Everything follows the read"; L2 "One scouting-budget line"; L4 "Costs in the rule's spirit" (morale, cap, legs, each sized); C1 "Cost sheet, one look". Gates to build: M3 pep talk sizes and odds, M4 rotation sizes, M2/M5 Play through cost line (#1107), M6 defensive forward, M7 in-match cards, M1 plan scaling, L1-L4 draft and rival reads, FA weights and list dominant options, C1 Tribunal and Appeals costs, C2 club copy. S1 and S2 are met. | Each listed gate shows a gain, a cost and its odds in the ruled label wording, and no gate is left with a dominant option; the C1 cost sheet gets his one look before it is built. |
| T2.25 | Kick lanes (M4-014): corridor, switch and down the line chosen by game plan in place of the random 10% switch. Director: "lanes are recorded and affect play, not presentation only." The old claude/kick-lanes branches are gone from origin and nothing is on main. Lanes audit in Z | PR merged on green with the lane recorded per kick, play affected by plan and a motion clip of the three lanes. |
| T3.R9 | Readability sweep, one screen per PR in the order he sees them: hub, match view, breaks, team builder, training, draft, contracts and trades, profile, stats, menus. Then the match-view centrepiece pass ('looks like PowerPoint'). His words: "readability and intuitive interfaces are a core pillar of this project, paramount to its success". Batches 1 and 2 only partly cover stats and menus (390x844 and 1280x720, no record he looked). Hub done (story card text to body size, opponent lines in TEXT under their club's bar; `tools/visual/capture_sweep.gd`). Match view done, with its centrepiece pass (crowd in the stand, lit turf, shaded discs, light edge on dark kits, oval text at the 13 px floor, bigger PC score). Left: breaks, team builder, training, draft, contracts and trades, profile, stats, menus. | Each screen has before/after captures at 390 and 1920 px that the director has looked at, and the match view has been reworked and shown to him. |
| T5.r110 | People remembered: stored career facts reach a screen. The player sheet and the honour board (#1100) are done. Left: the selection drop (P-37; #782 covers only the release confirm) and the coach's ledger on the stats hub (P-39: players you drafted who became B&F or All-Australian, board verdict per season, from CareerFacts; director "Yes"). | Each listed screen shows its facts from CareerFacts, no fabricated lines, honest empty states, real-tap check. |
| T5.r93 | RPG programme: development conversations tied to training or retraining plans (such as a learn-a-position project, ARD-M5-003): a private talk about the goal and any agreed playing chance, then a later line about the trial and its outcome. r91 and r92 are built. | The conversation fires from real facts, shares the one weekly optional slot, has factual follow-through, copy shown to the director first. |
| T5.r164 | Story beats for international players (#752, #815): only the phone check is left. | An international story card played on a phone (or a real tap at 390x844 portrait), answered, with the Gain and Cost result shown. |
| 6.34 | Styling looks STYLE-01/03/04/05/06 (#1250-#1255): his verdict on each look, recorded (a look merged before approval needs it, or a revert). Missing captures: STYLE-05 headers on Main, STYLE-04 on the match oval (bible ruling 34), STYLE-03 on named screens; the Training rows fix (#1250). | Each look is shown to the director as a capture on those screens with his verdict recorded, and the Training rows line up on a phone capture. |
| 6.38 | Vignette broadcast atmosphere, in the director's words 'it looks bizarre how there are no background players or atmospheric details': the centre bounce (StoppageVignette) needs both teams' 6-6-6 set-ups, the other field umpires, boundary umpires on the wings and goal umpires; cheer squads, banners and a lit club-colour crowd beyond VignetteCrowd and #996; distant players as cheap sprites. | Match scene captures show the extra people and atmosphere with no frame-rate drop on a phone, and the director has looked. |
| 6.40 | Written inventory of every vignette renderer (Broadcast, AwardWinner, Stoppage, Decision, Farewell, PreMatch and the Vignette* helpers) and fallback (such as OLD_FRONT_DURATION and the average-build fallback in _figure) ('entirely replace the old vignette art style with the new pre-rendered 2.5D footballer style'). | The inventory doc exists and confirms no old-style figure path is left. |
| 6.42 | Rendered Blender plates for the press room, awards stage and MCG with crowd, replacing the painted stands ('do what you think is best, but I expect beautiful results'). | Each plate is in the game in its scene and the director has looked at captures. |
| 6.44 | Ground looks beyond the MCG so 'a footy fan recognises the MCG, Marvel, Optus, Adelaide Oval, the Gabba, GMHBA and the SCG without the name' (#967). Left: his look at the no-name captures of the six, and his call on the fictional clubs' grounds (bible Q26, Q51). | He has looked and recognises the six, and his ruling on the fictional grounds is recorded. |
| 6.49 | Oval-broadcast bundle 2 (P-31, P-32, P-33; P-34 is in T3.R10; P-35 skipped): breeze end shown, crowd, and a skippable post-full-time goals replay from the event log. | All three show in a played match and the replay skips with one tap, proven with a real tap. |
| 6.51 | Crowd knows the score: crowd noise rises with goal runs, home crowd louder than away, siren at every quarter end, and the gap between event and sound measured. | A match audio check shows each behaviour and a measured event-to-sound gap. |
| 6.53 | Free shader polish and lighting: restrained figure shadow and highlight in figure.gdshader, soft contact shadows, baked lighting on the figures first (rule 53). #996 did the grade and atmos pass only. Idle and battery numbers in Z | Before and after captures stored and reported. |
| 6.58 | Hair library: all 16 styles draw (#998, on), but about ten short styles (buzz, crew, side part, messy medium, curly, afro) look alike at figure scale; beards and boots go back to the art work. | Each style reads apart at figure scale and the director has approved the look. |
| 6.63 | Tattoos: premiership-year ink is done (#1258). Left: the original tattoo library (bible item 63: rose, snake, barbed wire, bird, 666, love heart, Southern Cross stars, checked Asian-script lettering) drawn from the per-player Appearance field; ink on the speccy strips, carrier_near, the umpire's bounce and the coach; correct arm on mirrored moves; years readable at match size; his look at the ink. | Tattoos draw on figures, are saved once, change no match result, and he has looked. |
| 6.64 | Club Forge appearance options still hidden or missing: socks, headbands, bandaging, Forge-chosen tattoos and facial hair (hidden by SHOW_UNDRAWN_LOOKS until figures draw them), boots and boot colour, beard colour; and Forge import/export as a 256x128 PNG. Skin tone, hair, foot, number and nickname are built. | Each option is drawn on the figures and saved, and a PNG round-trips through import and export. |
| T7.R84 | Release engineering for saves. Left: a "Restore last good save" from the .bak, frozen fixtures for later versions (only `tests/fixtures/career_v1_2026-09-30.save.gz` exists; VERSION is 2), and a quiet version line with patch notes shown once. Corrupt and newer saves are handled (#945, #973). | Frozen fixtures for each later save version load in a test; Restore last good save works from the menu; patch notes show once per version. |
| T7.R87 | Pass-2 bundles the director said yes to ("All eight theme bundles: yes"), Tier A and B in listed order. P-12 (oval answers a structural call, #784 and #800) and P-70 and P-71 (offline promise, backup, #779) are built. Still to build: P-25 to P-29 match day on a phone, P-72 patch notes name the football change, P-73 answer every review within a week, P-74 the Not in this game page and P-43 (P-52 carnival built in #969). | One row per remaining P-number in open-requirements.md with a PR, each proved on a phone-width capture or a test; P-30 and P-75 stay skipped. |
| T8.Q20 | Make the weekly sim faster. Director: "#888 sim 35% slower is accepted for now; optimise the weekly AI in a later PR (next task = the sim-speed PR); the coach pool of 57 is fine as is." Win back the lost time in the weekly AI work, with the same results. | 3-season bench of weeks is back near main's pre-#888 146 s (from 225 s); seeded results byte-identical before and after; coach pool stays at 57. |
| T8.78 | P-78: a time budget for each player action (tap to screen, Sim the week, rollover), checked by a test. Director: "Yes" (Q8, audits that protect the fun, 2026-10-18). | One budget table in a data file, a check that fails when an action runs over its budget, and the first baseline run recorded. |
| T8.85 | P-76: picture and truth never disagree. Every tick, no disc moves faster than a footballer or jumps; the ball is always with a player or in flight; 36 discs at 8x; feed, scoreboard and engine score agree; the intended sheet loaded, not a fallback. Director: "Yes" (Q8, 2026-10-18). Today speed caps run at 1x and 4x only and disc jumps are checked for one quarter at 4x. | A seeded match suite asserts all five each tick at 8x and goes red if a ball hovers or a disc jumps. |

## V. Visual direction (rulings 2026-11-04)

Director's answers. Style guide updated to match (rulings 1-4); the reports behind them (VISUAL_DIRECTION_REPORT.md, MENU_JUICE_REPORT.md, 2026-11-03) were session reports and are not in the repo.

- V-R1 CLAUDE.md governs over the style guide: gradients and glows are allowed when deliberate.
- V-R2 The primary button may be filled with club colour. A red club may clash with BAD, so a contrast and collision check is required.
- V-R3 Navigation icons and relaxed motion (sliding sheets, count-ups, screen transitions) are allowed.
- V-R4 ARD Regular stays for small body text; no Barlow A/B.
- V-R5 Particles only for the premiership (club-colour streamers) and the Brownlow winner reveal (24 gold sparkles).
- V-R6 The live match stays a refined diagram; the vignettes are the showpiece. No following camera, no 3D restart plan, no Clay Oval proof now.
- V-R7 Lowest supported phone: a recent mid-range, about 2023.
- V-R8 Figure sheets and the eight vignette scenes are kept; any deletion waits for a future decision.
- V-R9 Nav icons and the wordmark are AI-assisted candidates; the director approves or rejects.

| Id | What | Done looks like |
|---|---|---|
| V2 | Premiership streamers in club colours | plays once on the premiership screen only, a capture frame shows both club colours |
| V3 | Brownlow winner reveal: 24 gold sparkles | plays once on the winner reveal only, 24 sparkles, a capture frame |
| V4 | Elevation scale and an automatic contrast test | BG, PANEL, PANEL_ALT, INK and SURFACE in UiKit.gd form one ordered scale; one test walks every club (including a Forge club) and fails a primary fill under the contrast floor against its label, page or panel, or too close to BAD, and fails any text under the floor on every surface step |
| V5 | Training results is the proof screen for the new look, then the hub, then the other screens | director approves Training results on his phone before the hub starts, then the hub before the rest |
| V6 | Match chrome: scorebug 56 to 72 px, bottom decision sheet about a third of the height, one-button transport, goal and siren poster card | captures at 390x844, the oval gets the freed height, every decision reachable with a real tap |
| V7 | Navigation icon set (AI-assisted candidates) | one icon per hub destination, director approves or rejects |
| V8 | Refresh captures of every screen on current main (the newest are 2026-10-07 to 10-11) | one capture per screen at 390x844, dated, in the audit folder |
| V9 | Housekeeping: placeholder logo name, stale worktrees (`The MCG.glb` is already out of the repo) | logo name is final or marked placeholder in one place, `git worktree list` shows only live ones |

## Rulings (director, 2026-11-04)

Settled answers that are not build rows. The bible stays as it is unless he consents to a change.

- A TODO row is authorisation to build it; a roadmap entry alone is not. With no task, work the TODO.
- Any doubt is a fail (critic agents are gone since 2026-11-05: every visual goes to him after the session's own frame check). This fully replaces the 2026-10-18 "don't chase marginal gains" line.
- Game, simulation and story carry equal importance. Secondary buttons are outlines.
- Press answers are seeded rolls with the odds and both outcomes shown (the bible line stands; already shipped).
- Polish goal 1 (player agency in matchups and rotation changes) stays open as written.
- Teaching is XP scaling, not the season-ceiling point.
- Personality types and captaincy are both wanted, later (section F). Culture sizes are reviewed now (row 68).
- 4.Q5 (Ask around, untouchable, pick order from round 18, pick trade on draft night) are still candidates, not assigned.
- Row 13 gets all five scenes and waits for the 1.11 playtest gate (on since #1074, no switches). Time pauses at a decision, so scenes never fight live speed.
- Weather has full effect on play (T1.Q2, T2.Q2, 6.Q10, T8.Q7): wet tackles move toward the real +12% (row 61); how it looks never touches the sim. Weather is off the bible's open list.
- Ladder goes into Season stats (T3.Q13, T9.Q29): the hub nav bar loses Ladder, no other nav change (shipped).
- Price: free for now. Platforms: web, Windows and an Android APK on itch; Google Play only on his written yes (US$25 fee and signing key).
- Old PRs #745, #761 and #765 were already merged; nothing to close.
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
- Retire the remaining no-digit checks on non-gate screens, and loosen the stats column pixel bands to no-clipping only, or leave both? (T7.O15)
- Does the transparency continuation order stand (M3, M4, M6, M7, M2 copy first; L1 after Q3, L2 with Q4; M1 after Q2; C2 copy; M5 after #850; L4, C1, S1 after Q5, Q6, Q9; S2 after Q8; L3 after measuring), or does he re-order it? (T7.R89)
- Which of P-01 to P-11, P-16, P-19, P-21, P-22 and P-24 does he take? (T9.Q31)
- Is "outside the bottom third" (top 12, 13 and 14 at 18, 20 and 21 clubs) the board's middle goal? Built that way in #1053 as a proposal. (T9.Q20)

## Z. Last: audits and balance (after every other row is done)

Director 2026-11-10 (Rulings 2026-11-10): no audit or balance tune until every other row is done. Each row names the build row it came from.

| Id | What | Done looks like |
|---|---|---|
| 28 | How-we-play maturity; How-we-win materiality; List Profile vs results (seeded, via audit.yml) | a seeded audit and evidence doc for each |
| Z67 | Management pays audit, after row 67's trade lever: re-run tools/audit/levers2_impl.gd with the trade period at real volume, recruiters' edge and development projects; balance-gated | audit across 8-10 seasons, paired `tools/balance.sh match 1000` table in the PR |
| 11, T2.29 | Spoils, intercept marks and ground-ball gets (M3-003). Spoils 22.8-23.2 a team against real 30.7, between the arcs 4.6-5.1 against 14.5-20.2 (#1199, #1241; forward 50 spoils are done). Intercept marks (0.76) and ground-ball gets (0.71) not re-measured since #897; the harness needs an intercept-marks stat and a real ground-ball-gets reference first | a tune that keeps contested marks, rebound 50s and disposals in range, and a seeded screen shows spoils, intercept marks and ground-ball gets IN |
| T2.31 | Ruck integrity (M1-002): write the audit doc from the harness Rucks section (#1121): the number-one ruck's to-advantage 35.2% against 29.6% (NEAR), hit-outs per ruck contest 55.2% against 42.5% (OUT, a counting artifact per #1121); find a real duel-spread reference or his acceptance of the club-spread proxy; state tune or no tune. Clearances stay random | audit doc with real ranges, the duel spread and the stated diagnosis; any tune follows it |
| T2.25 | Paired-seed kick lanes audit, after row T2.25 ships | lanes recorded per kick differ by plan on paired seeds |
| 6.53 | Idle and battery numbers for the lighting change (#996) and the row 6.53 shader work | idle and battery numbers reported, before and after |
| Synergy | Synergy numbers up (director 2026-11-10: "if anything i wanna boost synergy numbers but thats for later"). The row 103 audit had 47% of rival clubs fielding a synergy on main, 57% with row 103. Supersedes DIRECTOR_BIBLE ruling 23 (15-25% of clubs, mostly 0-1). Target: "i think teams at the bottom of the ladder should have 0-1 synergies, teams in the top 4 probably have 2-4 synergies" | a seeded audit of synergies per club by ladder position: bottom clubs 0-1, top 4 at 2-4 |
| T8.87 | P-79: no plan wins everywhere. Seeded round-robin of every plan against weak, even and strong lists. Director: "Yes" (Q8, 2026-10-18). Reports only. | A shared-seed audit run on CI, with a result written into the term sheet in football words and the share of opponents the best plan beats; no tuning made. |
| T8.88 | P-80: fun floor beside the realism floor. A dynasty bot plays 20 seasons on many seeds and records how often it makes finals within five seasons and wins a flag within fifteen. Director: "Yes" (Q8, 2026-10-18). Feeds the dial sizes, never declares balance done. | A CI audit and an evidence doc giving the finals-in-five and flag-in-fifteen rates against the director's 'a flag every 8-10 seasons'; no constants changed. |
| T8.83 | Long-career integrity soak. Director: "Test decades-long / 100+ year careers." Start with 5, 10 and 20-year careers, then 8 careers x 20 seasons x 4 policies. The old long_career audit only measures lists and retirements. | CI run shows zero integrity violations (duplicate history, ghost players, impossible lists), season-20 save under 3x season-2, round time under 1.5x. |
| T8.50 | Potential inflation: show how many 90+ ceilings there are by age, role and club, and what long careers do with them. No blanket nerf. The existing audit covers age band, position and source only. | Evidence doc with distributions by age, role, club and source plus long-career outcomes; any change goes to the director first. |
| 30 | Coleman goalkicking cap (98th percentile now; pool max or 99.5th percentile, bible Q1/Q120) | his ruling, then a seeded screen |
| 58, 39 | Difficulty dial sizes (board patience, rival recruiting) and pre-season balance sizes | sizes set from his playtest |
| 42 | Comebacks match real AFL on 9,600 matches (docs/COMEBACKS_EVIDENCE_2026-11-05.md); loosen the close-finish band (65.8% v 57.5%) or not | his ruling |
| Traits | Game-plan trait sizes (director 2026-11-10: "we will balance test them vigorously later, for now just build and ship"). First screens (one side running each, 1,000 paired matches): The Cluster +7.4 margin, Kick-Mark Masters -4.7, Fast Starters +3.0, Never Say Die -1.9, the rest within 2 se of 0. Front-Runners and Never Say Die lean on Fire them up, which the harness never calls; Hard Trainers and Long Bombers' costs barely show in one match. Sizes are named consts in scripts/sim/PlanTraits.gd | a screen of each trait with Fire them up in play, sizes set so no trait wins or loses on the scoreboard; settled only when his playtest also passes |
| Balance | Balance pass: first run every suite with `BALANCE_CHECKS=1` (62 real-AFL threshold checks wait behind tests/balance_gate.gd; misses log BALANCE_DEFERRED| meanwhile) and fix or rule on each; then every balance-gated feature in section B (78, 89, 92, 103), screened together as one match (match_flow, kick_range, set_shots, key_duels, mid_intercepts, back_carries and momentum_runaway were never screened together, #1074) | paired `tools/balance.sh match 1000` table; balance settled only when his playtest also passes |
