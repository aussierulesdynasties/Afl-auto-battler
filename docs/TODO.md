# TODO: everything not done yet

The one list of work not done. Point a session at this file and it works down it. Done and cut items are removed after merge from the PR's `Closes row N` line (git history keeps them). Director rulings live in `docs/DIRECTOR_BIBLE.md` (reference, not a work list); the later ruling wins. Balance is the director's call; nothing ships on without his playtest. Updated 2026-11-04 against main `7af1db8f`. Live on itch: 1.0.2 (7af1db8).

## Itch builds

Which build goes to itch next, and when, is in `docs/ITCH_BUILDS.md` (read it only for a release).

## A. Build now (open, no blocker, order = story first, then sim, then approachable)

| # | What | Done looks like |
|---|---|---|
| 35 | Finals bespoke cards: slice 2 built behind `finals_cards_2`; ships when he has played it | see section B |
| 61 | Weather at full effect: rain, wind and heat change ball handling, kicking, tackling and scoring (wet tackles toward the real +12%); sizes come from a seeded audit and balance stays his call. Its look never touches the sim | audit bands, rules in code, his playtest |
| 63 | One cost sheet per club dominant option and one for the 33 gain-only story options, same look as the 17 story cards; nothing is dropped (T5.Q2, T5.Q3) | every option shows a real cost |
| 65 | Draftees start lower: picks 1-5 about 60-62, 6-20 about 55-58, POT kept; his playtest still judges (4.Q9) | draft audit bands |
| 67 | Management pays: trade period at real volume, recruiters' edge and development projects (4.Q11); balance-gated | audit across 8-10 seasons |
| 69 | Hub leads with one hero element, shown on the hub first (6.Q2) | hub capture, critics clean |
| 70 | Pre-timeskip: the full survey, not the simpler version (T5.Q20) | survey built |
| 71 | Former-player coaches: lower the coaching rate toward the 60-80% aspiration (86% by 2058 now) (T5.Q15) | audit shows the lower rate |
| 73 | Premiership-year tattoos at a restrained, configurable rate; zero gameplay effect (6.Q16; see G 6.63) | tattoos on, rate in one place |
| 74 | Gather Round as a shared league event at host venues, with a policy for odd club counts (T5.Q11a) | built |
| 75 | Sir Doug Nicholls Round as a real annual event, design stored in the save (T5.Q11b) | built |
| 76 | AFL news layer: generated news items from the save (T5.Q11d) | items appear |
| 77 | Set shots rise from about 37.5% to the real ~55% of shots, conversion set by distance, total scoring held flat (T8.Q9) | audit shows both |
| 78 | Rare big margins come back through Momentum (100+ about 0.5% against real 1.9%); balance-gated (T8.Q4) | audit shows the blowout rate |
| 84 | Togetherness at tight and cliques is felt in matches (director 2026-11-06, after the row 68 review); balance-gated, his playtest judges | audit shows the effect, he has played it |
| 89 | Midfield intercepts close the gap now: sim 1.4 per team per game against real 2.5 (T8.Q8); balance-gated, `tools/balance.sh match 1000`, his playtest judges | audit shows the intercept rate near real |
| 90 | Development drift fixed now, cause first: contested bull 3.5% to about 11% and hothead 6.2% to 32.1% over seven seasons (T8.Q10) | cause shown, then a seven-season audit holds the shares |
| 91 | Listed positions via real_pos: about 85 forwards and 21 defenders stop reading MID; moves 122 players and 110 OVRs (T8.Q11); balance-gated | listed positions match real roles, OVR changes reported |
| 92 | Back-zone carries retuned (CARRY_ROLES) so defenders carry the ball like real AFL (T9.Q22); balance-gated, paired 1,000-match table in the PR | carry share near real, his playtest judges |
| 94 | Key forward v key defender meet more in the engine so the full-time duel line is real (T8.Q6); balance-gated | audit shows more contests per duel, line reads true |
| 96 | Cut the PRIVATE-WATCH event card: private lives stay out of the game (T5.Q18) | card gone, tests updated |
| 97 | Training: one stat focus per player per season, drills do the rest (T1.Q7, director 2026-11-06) | focus picked once a season, test |
| 98 | Audio settings become Mute and one Volume slider (T7.O16) | settings show the two controls, real-tap test |
| 99 | Football department budget merges into High performance: one spend (T9.Q14) | one spend line, old saves load |
| 100 | Culture sheet moves into the Captaincy panel | culture shown with the leaders, old sheet gone |
| 101 | Pre-season drill plan split by position group: mids, defenders, forwards, rucks (director: "split it between position groups") | four group plans, test |
| 102 | "Ask before simming" asks only when Sim the week would sim a match you could play | prompt only before a playable match, test |
| 103 | Synergies within reach: draft, trade and free-agent screens show which synergy a player would complete, and a player can grow a trait over seasons through training (4.Q10); balance-gated | both shown in play, paired table |
| 104 | Generated players get synergy traits at the real-player rate and contested bulls at the real 3.5% (4.Q10; drift side is row 90); balance-gated | generation audit shows both rates |
| 105 | Press conference: list every place the code differs from the bible and show him before anything changes (T3.Q6) | list shown to him |
| 106 | First-goal line in the feed for any player at your club, backed or not (T5.Q8) | line appears once per player, test |
| 107 | Event cards: every choice gets an upside and a downside, and never-seen cards get a trigger (T5.Q18, row 34) | no no-cost choice, every card reachable in an audit |
| 108 | Coach arcs switch on (T5.Q4, director "Switch on now") | switch on, suites green |
| 109 | Screen defects: club ink to 4.5:1 on tinted panels, hub ladder fills the right side at 2560, break notes above 13 px, draft subtitle not cut off (6.Q18) | captures at phone and 2560 |
| 110 | Vignette defects: boundary-snap curved white line, snap-for-goal hovering ball (6.Q18) | frames checked, captures to him |
| 111 | Sacked is not the end: choose from a few clubs with open jobs, or retire with the record read out (T5.r22) | choice offered after a sacking, test |
| 112 | Rival board letter after a strong season (T5.r23) | letter only after a strong season, accept and decline tested |
| 113 | Start at the end of 2026: real lists, the real 2026 National Draft with each club's real picks, then play 2027 (T5.r134) | start option, sourced pick ownership, test |
| 114 | Challenge starts: Youth only, Rebuild (bottom club), your own goal (T5.r115) | three starts selectable, test |
| 115 | Board goal set from where the list ranks pre-season, and said aloud; scales with the number of clubs (T9.Q20, T5.r117) | goal follows rank at 18 and 21 clubs, test |
| 116 | Awards night: round-by-round Brownlow count, live or one round at a time, plus your club's best and fairest (T5.Q23b) | count watchable both ways, real-tap test |
| 117 | Coaching staff: head coach, head assistant, assistants; counter-offer (not money) when a rival poaches one (T5.Q16) | approach, counter and departure tested |
| 118 | Text size setting (Standard, Larger, Largest) and no state shown by colour alone (T3.R10) | every screen at Largest, no colour-only state |
| 119 | Undo for delist, free-agent signing and contract offer until Sim the week (4.R76) | Undo shown and works, real-tap test |
| 120 | Wet weather: more fumbles, more stoppages, lower set-shot accuracy (director 2026-11-06); balance-gated | paired wet v dry table |
| 121 | Career highs shown once each in the match feed and weekly news (T5.r152) | shown once, never repeated, test |
| 122 | Club honour board and a page for every club reached by tapping its name (T5.r112-113) | both built, real-tap test |
| 83 | After the story work: Brownlow viewer controls, the Combine screen and the first-postseason intro to their recorded specs (T3.Q18) | built |

## B. Built and OFF: waiting for his playtest, then the switch goes on

| # | Feature | Switch | PRs |
|---|---|---|---|
| 1 | Top three attributes on cards, Needs work benchmark, scout grade word for hidden prospects | `top_attributes` | #863 |
| 6 | Player faces, 15 hair styles, 30 strips re-rendered | `player_looks` | #873 |
| 9 | Feed colours: your goals good, goals against bad, behinds and calls neutral | `feed_colours` | #918 |
| 10 | Kick range caps receiver choice; Sim the week shares the same pick | `kick_range` | #857 #879 |
| 48 | Coach career arcs | `coach_arcs` | #867 #877 #881 #886 |
| 49 | Match hero, turning point, reasons | `match_story` | #853 #890 |
| 50 | Club almanac | see Features.gd | #855 #890 |
| 51 | Weekly checklist with one big arc call (Hub "no weekly checklist" text goes when on) | `weekly_checklist` | #859 #861 #867 #877 #881 |
| 35, 36 | Finals cards slice 2 and Grand Final cards | `finals_cards_2` | #864 |
| 52 | Expansion package, training report, speccy front | `expansion_package`, `training_report`, `speccy_front` | #745 #741 |
| 11 | Stoppages from contests, play on after a won ball. Only partly met with the switch on: spoils 0.57 of real, intercept marks 0.76, ground ball gets 0.71 (`docs/research/MATCH_FLOW_AUDIT_2026-11-04.md`); a spilled tackle is counted as an intercept. Open: another tuning pass, or his playtest first | `match_flow` | #897 #901 |
| 13 | Every in-match decision opens on a vignette scene. Time pauses at a decision, so scenes do not fight live speed. Parked behind the section 1.11 playtest gate by his ruling | `decision_scenes` | #902 #908 |
| 14 | Opposition goal run as two football moves over the centre ball-up | `goal_run_moves` | #903 |
| 15 | Late-game centre ball-up: two distinct choices | `ballup_two` | #895 |
| 24 | Training as a compact player card grid with roles and traits | `training_grid` | #928 |

## C. Needs his look or call (shown, then ask)

- 5 Defensive set-up break wording (merged by #874). 16 PC bounce scene. 20 Press conference black bands gone?
- 7 Shake on his device. 26 Season stats hub phone review.
- 42 Comebacks already match real AFL on 9,600 audited matches (docs/COMEBACKS_EVIDENCE_2026-11-05.md); no rule changed. Does he accept that, or want the close-finish band (65.8% v 57.5%) loosened?
- 30 Coleman goalkicking cap (98th percentile, balance-gated).
- 58 Difficulty dial sizes (board patience, rival recruiting). 39 Pre-season balance sizes.
- 47 Decision transparency: 9 questions on sheet #851 (how the plan gain is printed, whether the draft shows the true rating beside the scouting range, whether the Play through role lines and cost (#850) are right).
- 34 62-line event-card copy sheet, shown with the never-seen cards and no-trade-off choices.
- 87 Turnover caption (#617) and the Bring the heat look: show him both again (T2.Q10).
- 40/41 Own game plan builder (game as is; Club Forge): decision waits on his plan-drilling play.
- V0 What does 'beautiful' mean to you: which two or three screens from shipped games would you sit this game beside?

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
- Player personality types and captaincy meaning (composure, late-game stability): both wanted, later (T5.Q12, T5.Q13).
- 6.Q14 Indigenous Round art is parked; the First Nations artists are his to choose and pay.
- Presentation wishlist: away/clash and heritage guernseys, coach appearance, finals bracket, premiership guernsey
  history, player card evolution, record-breaker marks, legends wall, season story recap, draft class identity,
  archive gallery, club museum, retirement variants, dynamic crowd, custom typography, season poster, stadium
  identity, user guernseys and logos, Coach of the Year.
- Deferred by ruling: weather at the quarter break, announce the cap step, league rule changes.

## In flight
Nothing open.

## Working rules
- Godot runs off-screen with its own user data (`APPDATA=<scratch dir>`); kill only your own PIDs.
- Balance: screen every balance-gated row or match-engine change with `tools/balance.sh match 1000` (base vs `--b "--on <switch>"`) before the PR and paste its table in the PR body; extend the harness rather than writing one-off probes (tools/balance/README.md).
- Run only the suites your change touches locally; CI runs the rest. Long audits go to `audit.yml`.
- Revert `.import` and `.uid` churn before committing. Stage by name; never `git add -A`.
- One worktree per session, from `origin/main`. Don't push to a PR branch while its CI runs unless the merge needs it.
- Never edit this file in a feature PR: write `Closes row N` (or `Closes rows 22, 27`, `Closes row T5.Q24`) in the PR body and `roadmap_close.yml` deletes the row after the merge. Edits to the list itself (new director requests, with his words) go in a PR labelled `roadmap`.

## G. From the Bible check (2026-11-04): open and not built

Ids point at `docs/DIRECTOR_BIBLE.md`. Verified against the code on 2026-11-04.

| Id | What | Done looks like |
|---|---|---|
| T1.R26 | Finish the decision-transparency job on the gates still open after #835: "I want full transparency behind each decision and the impact it will have"; "RNG is still okay, as long as the risks are clearly defined in the decision gate." Every remaining gate (pep talk, rotations, play through, plans, defensive forward, in-match cards, draft and rival reads, list and club dominant options, 33 gain-only story options, press conference) shows what each option gives, what it costs and the odds, in football words. | Each gate on the #851 rulings sheet (M1-M7, L1-L4, C1-C2, S1-S2) shows a gain, a cost and its odds in the ruled label wording, and no gate is left with a dominant option. This starts after he answers the five sheet questions. |
| T2.4 | Release 1.0 Phase 3, players react to your calls: each structural call visibly changes where players stand and move. Director: "the single biggest thing to improve the game feel". | Paired-seed audit shows each call shifts positions, a capture shows it, and the director plays a full match on PC and phone and says the calls matter. |
| T2.24 | Finish set shots (M4-013): bring the set-shot share to real AFL. Director: "should be 3 visibly different sequences, but also add a pack contest, also gives an opportunity for a crumber to pick up a spoiled ball if it is not marked." Sim #467, view #471 and frees-in-50 #484 are merged. | Seeded audit puts set-shot share within the real AFL range, with a motion clip of the three sequences, the pack contest and a crumber chance. |
| T2.25 | Kick lanes (M4-014): corridor, switch and down the line chosen by game plan in place of the random 10% switch. Director: "lanes are recorded and affect play, not presentation only." Work sits on origin/claude/kick-lanes and claude/kick-lanes-cal (sim, view and lanes audit commits) with no PR and nothing on main. | PR merged on green with the lane recorded per kick, play affected by plan, a paired-seed lanes audit and a motion clip of the three lanes. |
| T2.31 | Ruck integrity (M1-002): diagnose first, then check hit-outs against AFL ranges and feast-or-famine ruck duels; show hit-outs to advantage in detailed ruck stats only; do not make clearances deterministic. Hit-outs to the ruckman (#60) and to advantage (#145) exist; the audit and ranges check do not. | Audit doc compares hit-outs per ruck and per team with real AFL ranges and the duel spread, any tune follows the diagnosis, clearances stay random, and detailed ruck stats list hit-outs to advantage. |
| T2.29 | General-play spoils (M3-003): bring spoils outside the forward 50 in line with real AFL (forward 50 spoils are done at 15.2 per team per game). Overlaps the spoils recalibration in TODO row 11. | Seeded audit shows general-play spoils per team per game inside the real AFL range, recorded against row 11 so it is not done twice. |
| T2.42 | Find and fix the simulation freeze or stall in play, a separate defect from the collection pauses fixed in #857. Director: "despite repeated requests to remove this behaviour". | Cause found and shown by trace or capture, fixed, and a long run of seeded matches shows no stall; the director sees none in his own playtest. |
| T2.48 | Recompose the centre ball-up vignette wider so the stoppage, ruck and mids read before any close-up. Director: "virtually impossioble for me to tell from still iomages", so proof is motion clips. | Motion clip on PC and phone sizes, with the decision UI showing, honours the Vignettes toggle, and the director passes the look. |
| T3.R10 | Accessibility: a text size setting (Standard, Larger, Largest) and no state shown by colour alone. A tired or injured player is told apart on the live view and bench strip without a tap, with words on long press. Kit clash is checked under colour-blind simulation (P-04, P-06, P-10, P-34). Nothing of this exists yet. | Text size setting changes every screen and a shared test passes at all three sizes. The live view and bench strip show a short mark for tired or injured with words on long press. A colour-blind kit-clash check runs in CI. |
| T3.R42 | One thumb on match day: every live-play control sits in the lower part of the portrait screen. The score and clock never leave the match screen through a call, break panel, stats view or vignette (P-25, P-26, C-PC-01). | A phone-size screenshot test asserts score and clock are visible in every match-day state, and the live controls sit in the lower part of the screen with no scroll while the ball is in play. |
| T3.R43 | Navigation economy (bundle 6, director said Yes): each weekly fact at most two taps from the hub; long-press any football word for its exact rule (P-61); search any player or club from the hub and shortlist by long-press (P-65); a 'When I sim the week' standing-orders sheet (P-66); one-tap 'Report a problem' that copies build, seed, round, screen and the last twenty feed lines; one overflow check at every text size (P-77). None of these exist yet; only First-visit intros and the Sim the week label are built. | A tap-count test fails if a weekly fact is more than two taps from the hub. Hub search finds players and clubs. The standing-orders sheet is saved and followed when simming. Report a problem copies the data and sends nothing. The overflow test walks every screen at phone size and each text size. |
| T3.R9 | Readability sweep, one screen per PR in the order he sees them: hub, match view, breaks, team builder, training, draft, contracts and trades, profile, stats, menus. Then the match-view centrepiece pass ('looks like PowerPoint'). His words: "readability and intuitive interfaces are a core pillar of this project, paramount to its success". Batches 1 and 2 are merged; the rest is open. | Each screen has before/after captures at 390 and 1920 px that the director has looked at, and the match view has been reworked and shown to him. |
| T3.R56 | Onboarding checked on fresh saves: his words, "Walk through genuinely fresh saves with full onboarding enabled, not a mature save with tutorial flags already set." Cover the initial draft, weekly loop, first postseason, early elimination, reload, skip, off and replay. First-visit intros exist (#856), but trade, contract and Combine tutorials and the first-postseason intro are not found in code. | A fresh-save walkthrough record exists for each case, the missing trade, contract and Combine tutorials and the first-postseason intro are built, and any unimplemented mode is written down honestly. |
| T3.R41 | Team selection as two screens on phone and side by side on PC, no scroll. His words: "team selection being scrollable doesnt feel good, i think it should be 2 screens". Keep scroll position after every action. Check every screen at 960x540 and 390x844 for a scrollbar. | No scrollbar on team selection at both sizes, scroll position is kept after each action, and a test walks every screen at both sizes and lists any scrollbar. |
| T3.F-defects | Open defects: fatigue parity doubt, implausible generated veteran, goal-line scramble he called nonsense, stray curved line in the boundary-snap vignette, tag moving left (his words: "heinous, awful UI design", A2). Bye bug fixed in #210 and press tint in #767, so left out. | Each defect is reproduced, fixed and covered by a test or capture; the tag-left screen is redone and shown to him. |
| 4.R75 | Fewer, stronger, situational traits. The director's audit line: 'fewer, stronger, situational traits'. The forming side against the league (Matchup.standing), the 50/100/150/200 milestones and With us history are already in, and momentum is a real match edge (MOMENTUM_EDGE 0.04). Only the trait trim is left. | The trait list is cut to a short set where each trait switches on in a stated situation. A test pins the new list and old saves map to the nearest trait. |
| 4.R76 | Undo for a delisting, a free-agent signing and a contract offer until the week moves on (P-09), after the director's 'important decisions never resolve from one accidental tap'. | Delist, FA sign and contract offer each show Undo until Sim the week, and the undo restores list, cap and offers. A real-tap check and a save/reload test cover it. Onboarding is already in (Tutorials On/Off, #572). |
| T5.Q11c | Add the Danny Frawley Golden Fist for the best defender of the season: "Add the Danny Frawley Golden Fist award for the best defender of the season." Role-aware rule from tracked defensive stats (intercept marks, spoils, one-percenters, contests) so lockdown and intercept defenders both have a path. | Awarded each season with deterministic tiebreaks, kept in history, shown in awards and trophy room, no untracked stats used; test covers both defender types. |
| T5.Q16 | Coaching hierarchy (Head coach, Head assistant, other assistants) plus opportunity-based retention: when a rival approaches one of your coaches you can make a counter-offer or allow departure. "This retention negotiation is not a monetary bidding system". | One head assistant per club, rival approach held and resolved once, counter-offer is a role or succession promise with a stated timeframe, unmet promises cost trust visibly, AI clubs follow the same rules, test proves it. |
| T5.Q23b | Round-by-round Brownlow count and your club's own best and fairest count on awards night: "give it a bespoke staggered, round-by-round awards-night count, watchable continuously in real time or advanced one round at a time". Awards race, trophy room and fixture history already exist; the awards program today steps through four stages, not rounds. | Brownlow and club B&F reveal round by round from the stored votes (continuous, pause, next round, skip round, skip all), only revealed votes shown, no re-roll; real tap check on a phone. |
| T5.Q25 | Coach as the new club: take the job at a different club (director ruling 8: "yes, built after the package (not built yet)"). | A career can be started or continued as coach of a chosen new club with the rest of the save consistent; test and phone check. |
| T5.r22 | Sacked is not the end: after a sacking the hub offers "A choice of a few" clubs with open jobs (facts only) or retirement with the record read out. Today the sacked card offers only Season review and Main menu. One second chance, a premiership restores it. | Sacked card lists a few open jobs or retire; taking one starts the new club's career with the reprieve count stated plainly; a second sacking ends the coaching career. |
| T5.r23 | Other clubs come calling: after a strong season a rival board writes one letter (club, list in words, board goal, risk). Take it and the old club carries on; decline and nothing changes. | Letter appears only after a strong season, accept moves you and the old club keeps living, decline changes nothing, no coaching two clubs; test covers both paths. |
| T5.r110 | People remembered: stored career facts reach a screen. Facts are written but only Retirement.gd reads them. Put them on the player sheet, the drop, your ledger and an honour board (P-37 to P-45, director "Yes"). | Each listed screen shows its facts from CareerFacts, no fabricated lines, honest empty states, real-tap check. |
| T5.r112-113 | Club honour board (150 games, B&F, Brownlow or flag as columns, newest first, names open career facts) and a page for every club reached by tapping any club name (colours, ground, coach, captain, best 22 in words, last five, flags, players swapped; never rivals' hidden ratings). | Both screens reachable from the named taps, only recorded facts shown, no retired jumper numbers or museum scene, phone capture checked. |
| T5.r115 | Challenge starts beside League redraft and Real lists: Youth only (no trades or signings over 24), Rebuild (bottom club, three best gone), and a self-set goal the annual marks when met; no recommended goal. | Three starts selectable at new career, rules enforced and stated, self-set goal marked in the annual; test proves each. |
| T5.r117 | Say the pre-season list rank aloud against the board goal (P-38): the board goal is already set from list rank, the rank just needs to be shown. | Hub or board screen states where the list ranks and the goal that follows, in football words. |
| T5.r134 | Inherited-list career start: "promote this to the next major career-start feature priority ahead of unrelated content/presentation expansion." Inherit 2026 lists for all 18 clubs (before off-season changes, including zero-appearance players), prepare for the 2026 National Draft with sourced pick ownership, play 2027. | New-career setup offers Inherit 2026 lists beside League redraft; draft runs on the 2026 cohort; no fictional fillers or silent cuts; test and playthrough. |
| T5.r91-93 | RPG programme first slices: the sit-down with a backed player when his three-game run ends (about what he actually did), private selection conversations growing out of the weekly unhappy card, and development conversations tied to training or retraining plans. | Each conversation fires from real facts, shares the one weekly optional slot, has factual follow-through, copy shown to the director first. |
| T5.r152 | Career-high milestone surfacing (match-to-date stats at every break are already built): career highs shown lightly in match and weekly flow, once each, "Do not spam routine milestones." | Career highs recorded and surfaced once from real stats, nothing for quiet games, test covers a career high and a non-event. |
| T5.r158 | One rival club's identity across generations (RC-007, accepted): one earlier-versus-current squad or pattern comparison on an existing club surface, only where recorded data supports it. | Comparison line appears on an existing club surface only when data supports it; quiet clubs show nothing; match balance untouched. |
| T5.r164 | Story beats for international players: bespoke events and story beats for international players (second PR, C2). | International players trigger their own events from real facts, with costs and gains stated, test and phone check. |
| 6.29 | Finish the new scoreboard typeface: tidy the numerals and check 1/I/l, 6/8/9 and 0/O read apart; make scores like 12.8 (80) and money fit without clipping. | A capture of every score and money form on the phone shows no clipped or confusable digits. |
| 6.34 | Build the styling looks for STYLE-01/03/04/05/06 (own controls, ink pairings, oval composition, headers and roster-number marks) starting with Main, Hub, Full list and overlays using the 2.5D figures; and fix the Training player-row name/second-line vertical alignment. | Each look is shown to the director as a capture on those screens, and the Training rows line up on a phone capture. |
| 6.38 | Vignette broadcast atmosphere, in the director's words 'it looks bizarre how there are no background players or atmospheric details': 6-6-6 centre bounce set-ups, other umpires, boundary and goal umpires, a lit crowd, banners, cheer squads and cheap distant players. | Match scene captures show the extra people and atmosphere with no frame-rate drop, and the director has looked. |
| 6.40 | Awards ceremony still sits on the BroadcastVignette base. Move it onto the shared 2.5D figures; list every vignette renderer and fallback and retire the old paths ('entirely replace the old vignette art style with the new pre-rendered 2.5D footballer style'). | A written inventory of renderers, no old-style figure path left in the game, and an awards capture on the new figures. |
| 6.42 | Rendered Blender plates for the press room, awards stage and MCG with crowd, replacing the painted stands ('do what you think is best, but I expect beautiful results'). | Each plate is in the game in its scene and the director has looked at captures. |
| 6.44 | Ground looks beyond the MCG so 'a footy fan recognises the MCG, Marvel, Optus, Adelaide Oval, the Gabba, GMHBA and the SCG without the name'; decide what the fictional clubs' grounds look like. | Six more grounds are recognisable in captures with no name shown, and the director has looked. |
| 6.49 | Oval-broadcast bundle 2 (P-34, P-31, P-32, P-33; P-35 skipped): breeze end shown, crowd, and a skippable post-full-time goals replay from the event log. | All four show in a played match and the replay skips with one tap, proven with a real tap. |
| 6.51 | Crowd knows the score: crowd noise rises with goal runs, home crowd louder than away, siren at every quarter end, and the gap between event and sound measured. | A match audio check shows each behaviour and a measured event-to-sound gap. |
| 6.53 | Free shader polish and lighting: restrained figure shadow and highlight, soft contact shadows, baked lighting first; idle and battery audits reported before any change. | Before and after captures plus the audit numbers are reported. |
| 6.58 | Roll out the hair library after prototypes (afro, mullets, curly, long, dreadlocks, Fritsch-inspired, Bald explicit) and hand beards and boots back to the art agent. | The player_looks switch is on with every hair style drawn on the figures and the director has approved the look. |
| 6.62 | Indigenous Round original guernseys: 5-10 per club over time, each labelled original with its cultural-review state, plus import/export so players can add their own designs ('you design it yourself, ask the boss to add import/export functionality'). | Guernseys appear for the round with labels and review state, and a player can import and export a design. |
| 6.63 | Tattoos: original artwork, premiership-year tattoo adoption stored once per player, cosmetic only. | Tattoos draw on figures, are saved once, and change no match result. |
| 6.64 | Club Forge appearance options (socks, headbands, bandaging, tattoos, boots, hair and beard colours, skin tone, dominant foot, preferred number, nickname) and Forge import/export as a 256x128 PNG. | Each option is drawn on the figures and saved, and a PNG round-trips through import and export. |
| 6.36 | App icon: one coherent Aussie Rules Dynasties identity from the director's reference, with the old branding removed. | The icon is shown at icon scale for the director's approval and no legacy branding remains in the build. |
| T7.O10 | Correct docs/ITCH_UPLOAD.md: it still says "You upload; nobody else needs your itch login or keys." Sessions push builds with butler and post the devlog; the director only runs butler login and holds the keys. | ITCH_UPLOAD.md says sessions push and post, the director holds the login, and no line contradicts rule 73. |
| T7.R84 | Release engineering for saves: the game already keeps a .bak swap on save, but there is no "Restore last good save" button, no frozen old-version save fixtures (a 0.1.0 career must still load), no "newer save kept and the player told" message, and no quiet version line with patch notes shown once. | Frozen 0.1.0 and later fixtures load in a test; a corrupt or newer save leaves the file untouched and shows plain words; Restore last good save works from the menu; patch notes show once per version. |
| T7.R87 | Pass-2 bundles the director said yes to ("All eight theme bundles: yes"), Tier A and B in listed order. P-12 (oval answers a structural call, #784 and #800) and P-70 and P-71 (offline promise, backup, #779) are built. Still to build: P-25 to P-29 match day on a phone, P-72 patch notes name the football change, P-73 answer every review within a week, P-74 the Not in this game page, P-43, and P-52 under-18 carnival first ("P-52: Yes, carnival first"). | One row per remaining P-number in open-requirements.md with a PR, each proved on a phone-width capture or a test; P-30 and P-75 stay skipped. |
| T7.R95 | Indigenous round guernseys: the design audit and guardrails exist (#520), but no data-driven catalogue is in the code. Needs every active club to have "at least five distinct Indigenous-round designs available before the feature is marked complete", with provenance, rights and cultural-review fields. | A catalogue file with provenance, rights and cultural-review fields, at least five designs for each active club, a phone-review sample from every club, and the director's look before it is marked complete. |
| T8.Q20 | Make the weekly sim faster. Director: "#888 sim 35% slower is accepted for now; optimise the weekly AI in a later PR (next task = the sim-speed PR); the coach pool of 57 is fine as is." Win back the lost time in the weekly AI work, with the same results. | 3-season bench of weeks is back near main's pre-#888 146 s (from 225 s); seeded results byte-identical before and after; coach pool stays at 57. |
| T8.78 | P-78: a time budget for each player action (tap to screen, Sim the week, rollover), checked by a test. Director: "Yes" (Q8, audits that protect the fun, 2026-10-18). | One budget table in a data file, a check that fails when an action runs over its budget, and the first baseline run recorded. |
| T8.85 | P-76: picture and truth never disagree. Every tick, no disc moves faster than a footballer or jumps; the ball is always with a player or in flight; 36 discs at 8x; feed, scoreboard and engine score agree; the intended sheet loaded, not a fallback. Director: "Yes" (Q8, 2026-10-18). | A seeded match suite asserts all five each tick at 8x and goes red if a ball hovers or a disc jumps. |
| T8.87 | P-79: no plan wins everywhere. Seeded round-robin of every plan against weak, even and strong lists. Director: "Yes" (Q8, 2026-10-18). Reports only. | A shared-seed audit run on CI, with a result written into the term sheet in football words and the share of opponents the best plan beats; no tuning made. |
| T8.88 | P-80: fun floor beside the realism floor. A dynasty bot plays 20 seasons on many seeds and records how often it makes finals within five seasons and wins a flag within fifteen. Director: "Yes" (Q8, 2026-10-18). Feeds the dial sizes, never declares balance done. | A CI audit and an evidence doc giving the finals-in-five and flag-in-fifteen rates against the director's 'a flag every 8-10 seasons'; no constants changed. |
| T8.83 | Long-career integrity soak. Director: "Test decades-long / 100+ year careers." Start with 5, 10 and 20-year careers, then 8 careers x 20 seasons x 4 policies. The old long_career audit only measures lists and retirements. | CI run shows zero integrity violations (duplicate history, ghost players, impossible lists), season-20 save under 3x season-2, round time under 1.5x. |
| T8.50 | Potential inflation: show how many 90+ ceilings there are by age, role and club, and what long careers do with them. No blanket nerf. The existing audit covers age band, position and source only. | Evidence doc with distributions by age, role, club and source plus long-career outcomes; any change goes to the director first. |
| T9.Q20 | Board goal 'Finish in the top 12' is hard-coded (ClubLife.gd) and means two-thirds up the ladder at 18 clubs but a little over half at 21. Make it scale with the number of clubs, using the director's answer on what it should be. | The board goal is worked out from the club count, a test covers 18, 20 and 21 clubs, and the director has signed off the wording. |
| T9.R21 | TODO row 14 says 'odds in football words'. The director's 2026-10-18 ruling is: "I still want the football language, but I also want full transparency behind each decision and the impact it will have". Reword the row to say upside, downside, size and odds in percentages, in football language. | docs/TODO.md row 14 matches bible principle 4 and what #821, #833 and #835 shipped. |
| T9.R26 | Roadmap 10-05 still says Create-a-club gets 'an expansion-list establishment package'. The ruling (2026-10-06) is that a created club drafts in the League Draft like every club, with no concession. Correct the stale bullet at line 156. | The bullet in docs/roadmap/10-05-ard-m7-009-expansion-clubs-canberra-toggle-club-forge.md says League Draft, no concession package, and nothing else in the roadmap promises one. |
| T9.R23 | Fix the stale role and state wording: roadmap W3 still lists 'running a check' as a state, and the style guide, STATUS.md and AGENT_TEAMS.md still talk about the lead's QC and art-qa-critic. The director's rules are no roles (2026-10-29), no 'running a check' (2026-10-31) and independent Art QA critics (2026-11-03). | W3 lists only working (with the live job named), awaiting director, blocked and available, and no doc names a lead or lead's QC. |

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
- V-R9 Nav icons and the wordmark are AI-assisted candidates; critics check them and the director approves or rejects.

| Id | What | Done looks like |
|---|---|---|
| V1 | Motion tokens and the `sheet_in` / `fill_bar` prototype, behind switch `ui_motion` (already in flight) | tokens in UiKit, a sheet slides in and a bar fills with the switch on, nothing moves with it off, headless sees the final state |
| V2 | Premiership streamers in club colours | plays once on the premiership screen only, a capture frame shows both club colours |
| V3 | Brownlow winner reveal: 24 gold sparkles | plays once on the winner reveal only, 24 sparkles, a capture frame |
| V4 | Elevation scale and an automatic contrast test | surface steps are tokens, a test fails any text or club fill under the contrast floor, including each club's primary fill against BAD |
| V5 | Training results is the proof screen for the new look, then the hub, then the other screens | director approves Training results on his phone before the hub starts, then the hub before the rest |
| V6 | Match chrome: scorebug 56 to 72 px, bottom decision sheet about a third of the height, one-button transport, goal and siren poster card | captures at 390x844, the oval gets the freed height, every decision reachable with a real tap |
| V7 | Navigation icon set (AI-assisted candidates) | one icon per hub destination, critics clean, director approves or rejects |
| V8 | Refresh captures of every screen on current main (the newest are 2026-10-07 to 10-11) | one capture per screen at 390x844, dated, in the audit folder |
| V9 | Housekeeping: placeholder logo name, the unreferenced 67.5 MB `The MCG.glb` in the repo root, stale worktrees | logo name is final or marked placeholder in one place, the file is removed or referenced, `git worktree list` shows only live ones |

## Rulings (director, 2026-11-04)

Settled answers that are not build rows. The bible stays as it is unless he consents to a change.

- A TODO row is authorisation to build it; a roadmap entry alone is not. With no task, work the TODO.
- Critics repeat until clean, any doubt is a fail. This fully replaces the 2026-10-18 "don't chase marginal gains" line.
- Game, simulation and story carry equal importance. Secondary buttons are outlines.
- Press answers are seeded rolls with the odds and both outcomes shown (the bible line stands; already shipped).
- Polish goal 1 (player agency in matchups and rotation changes) stays open as written.
- Teaching is XP scaling, not the season-ceiling point.
- Personality types and captaincy are both wanted, later (section F). Culture sizes are reviewed now (row 68).
- 4.Q5 (Ask around, untouchable, pick order from round 18, pick trade on draft night) are still candidates, not assigned.
- Row 13 gets all five scenes, stays off and waits for the 1.11 playtest gate. Time pauses at a decision, so scenes never fight live speed.
- Weather has full effect on play (T1.Q2, T2.Q2, 6.Q10, T8.Q7): wet tackles move toward the real +12% (row 61); how it looks never touches the sim. Weather is off the bible's open list.
- Ladder goes into Season stats (T3.Q13, T9.Q29): the hub nav bar loses Ladder, no other nav change (shipped).
- Price: free for now. Platforms: web, Windows and an Android APK on itch; Google Play only on his written yes (US$25 fee and signing key).
- Old PRs #745, #761 and #765 were already merged; nothing to close.
- Draft AI key-forward spread (2026-11-05): "Leave it as is". Young talls keep their potential credit; no change.
- Draft AI veterans (2026-11-05): "viney yes, but petracca and stewart should be 125-150"; "petracca is being underrated based on low games, hes very very good". Petracca overridden to 87; building clubs count a retired season at 0.35 dilution. Now Petracca 128, Stewart 138, Viney 301 mean pick.

## Rulings (director, 2026-11-06)

- GitHub deletes a PR's branch when it merges (T7.O20; turned on 2026-11-06).
- League balance and calibration suites run nightly only, not on every PR (T7.O14).
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
- Keep "League Draft board shows scouted estimates" and the branch's rival scouting error cut to 0-4, or both together (may overcorrect)? (T9.Q15)
- Which of P-01 to P-11, P-16, P-19, P-21, P-22 and P-24 does he take? (T9.Q31)
