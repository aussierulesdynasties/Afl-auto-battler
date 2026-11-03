# TODO: everything not done yet

The one list of work not done. Point a session at this file and it works down it. Done and cut items are removed (git history keeps them). Director rulings live in `docs/DIRECTOR_BIBLE.md` (reference, not a work list); the later ruling wins. Balance is the director's call; nothing ships on without his playtest. Updated 2026-11-04 against main `a8b23185`.

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

## H. Needs his call (rulings, one at a time)

- T1.Q2 How should weather change a match: which parts of play it touches and how hard? It is the one thing that may affect the sim beyond coaching decisions.
- T1.Q5 Does the 2026-11-03 rule (critics repeat until clean, any doubt is a fail) fully replace the 2026-10-18 "dont waste too much time chasing marginal gains or microscopic visual improvements", or do pixel, alpha and easing choices still stop after two rounds?
- T1.Q7 For each cut-audit candidate other than 1 to 5, 9 and 11, does it get cut, kept or replaced?
- T1.Q9 Does polish goal 1 (player agency fine-tuning in matchups and rotation changes, easily measurable) stay open as written, or does the story-first order change or drop it?
- T2.Q2 Does the director consent to removing weather from the design bible's open list, as the audit proposes?
- T2.Q10 Does the director want the Turnover caption (#617) and the Bring the heat look recorded as passed, or does he want to look at them again first?
- T3.Q6 Press conference: where the bible and the code disagree, decide which one is right and the other gets corrected.
- T3.Q10 Pre-match decisions: do all of them move ahead of Start, or do the calls stay in the pre-bounce pane as they are now?
- T3.Q12 When a live-speed window and 'every decision needs a vignette' (C-MG-31) pull against each other, decide which one takes priority.
- T3.Q13 Ladder: keep a separate Ladder screen or route it fully into Season stats, and decide what the hub nav bar holds.
- T3.Q18 Brownlow viewer controls, the Combine screen and the first-postseason intro: build them to the recorded specs now, or leave them behind the story-first work.
- T3.Q2-Q5,Q7 Decision-gate rulings still open: how the plan gain is printed, whether the draft still shows the true rating beside the scouting range, what cost the dominant list and club options carry, whether the Play through role lines and cost (#850) are approved, and whether the 33 gain-only story options get a cost, get dropped or stay.
- 4.Q1 Pick which Teaching model governs: XP scaling of -5% to +10% with Strong at 78+, or the season-ceiling point (+1 at Strong 82+, -1 at Fair 62 or worse), and fix the grade cut-offs to match.
- 4.Q5 Say whether C-PC-16 (Ask around), C-PC-17 (untouchable), C-PC-18 (pick order from round 18) and C-PC-28 (pick trade on draft night) are inside the bundle you approved or still candidates.
- 4.Q8 Say whether the custom prospect (Alastair McNeil, first national draft) is the next build. The inherited-list start itself already exists as Real 2026 lists (#569).
- 4.Q9 Decide whether draftees start lower (picks 1-5 about 60-62, 6-20 about 55-58, POT kept), whether the #695 draftee start passes your own playtest, and whether the unproven-potential discount stays as is or is softened.
- 4.Q10 Choose how synergies should be reachable given they are worth +5 to +11 margin when on but rarely reached and generated draftees lose synergy traits. Also set the scope of multi-season spread and trait decay, and what to do about bulls at 16.1% generated against 3.5% real.
- 4.Q11 Choose which levers make management pay: trade period at real volume, recruiters' edge, development projects, AI list mistakes, or a mix, knowing no single lever reaches a flag in 8-10 seasons.
- T5.Q1 Press answers: either each answer is a seeded roll with odds and both outcomes shown (your 2026-10-18 "Code follows the bible"), or the bible line changes to match the fixed effects now in code.
- T5.Q2 Club dominant options: either build a cost sheet per option like the 17 story cards, or drop the options that cannot carry a cost.
- T5.Q3 The 33 gain-only story options: either one cost sheet for all 33 with one look, or leave them on the shrinking allowlist.
- T5.Q4 Coach arc catalogue: which draft arcs you keep, change or cut before the arc engine is built, and whether you will play a career so the off switches can go on.
- T5.Q7 Culture effects (Standards, Togetherness, Ambition) are built: after your playtest, is the size right or does it change.
- T5.Q8 Backing and firsts wording and rules, currently placeholders: first-goal line for any of your players or backed ones only, cap of three lines, under 10 games threshold, tap in the profile, reminder line, +5 mood, and whether to add quiet-first-game lines.
- T5.Q9 Storylines before the bounce (beat 3): assign it or leave it, and if assigned whether old-club lines use 100+ games first then 20+ in-career.
- T5.Q11a Gather Round as a shared league event at host venues, with a policy for odd club counts: assign now or leave unassigned.
- T5.Q11b Sir Doug Nicholls Round as a genuine annual event with its design stored in the save: assign now or leave unassigned.
- T5.Q11d AFL knowledge layer as generated news items from the save (P3, speculative): assign now or leave unassigned.
- T5.Q12 Captaincy meaning: whether to build modest composure and late-game stability, the on-field-coach potency idea, the leads-by-example clutch idea, any mix or none, and whether it is balance-gated.
- T5.Q13 Player personality types (P3 stretch goal): whether it is ever assigned, and if so whether it replaces, groups or sits beside traits and synergies.
- T5.Q15 Former-player coaches reached 86% of coaching jobs by 2058 against the 60-80% aspiration: lower the coaching rate or leave it.
- T5.Q18 The PRIVATE-WATCH card invents a manager's calls about a real person: is that allowed as business or treated as private; and whether the never-seen cards and no-trade-off choices are cut, kept or costed.
- T5.Q19 Real B&F medal names (Doig, Sutton, Barker, Truscott) need the same licensing look as real club names: ship them named or generic.
- T5.Q20 Pre-timeskip survey: the full survey, or the simpler version where the sim follows the club's existing instructions and asks only what nothing else covers.
- T5.Q21 Whether the bible's Current focus section belongs in the bible, what the game deliberately will not have, and how weather affects a match (it matters; the system is not designed).
- T5.Q24 Career save version mismatch currently drops to the main menu with no message: keep that, show a message, or build migration.
- 6.Q1 Which governs the UI look: 'Not boring' (gradients and glows allowed when deliberate, 2026-10-08) or the 2026-10-10 style guide (no gradient except the club wash, no glows).
- 6.Q2 Whether every screen should lead with one hero element, shown on the hub first, or whether that stays unproposed.
- 6.Q4 Whether the hair, beard and boot ids are final, and what happens to the 24-style hair and 10-beard contact sheet and the boot sheets awaiting his look.
- 6.Q10 How weather should change a match, and whether unique weather icons come later or stay parked (weather looks currently 'Push them stronger').
- 6.Q14 Which First Nations artists he chooses and pays for Indigenous Round, and whether he wants the 5-10 per club samples first.
- 6.Q16 What premiership-year tattoo adoption rate he wants (restrained and configurable), and whether the tattoo feature goes on the list at all.
- 6.Q18 Assign or drop each unassigned defect: club ink under 4.5:1 on club-tinted surfaces, hub ladder empty right side at 2560, break-pane 13 px notes, ellipsised draft subtitle, boundary-snap curved white line, snap-for-goal hovering ball.
- 6.Q20 Whether he gives a written yes to the Cascadeur Indie spend, and his calls on the open animation-pipeline decisions including the gather-on-the-run proof.
- T7.O1 Which platforms ship for 1.x: web on itch (live), Windows and Android APK on itch, and whether Google Play ($25 fee plus signing key, your written yes) is in 1.1 or later.
- T7.O3 Price for the game: free, pay-what-you-want, or paid, and whether a paid release waits on a separate decision after the real-names rights check.
- T7.O4 Whether 1.x is frozen to the rows already in the register, and for each of AFLW, personality types (D2), cloud save sync, Play Store, Coach of the Year, club museum, legends wall, own game plan (R40) and the long-save wishlist, whether it moves to later.
- T7.O5 Which rows make up 1.1, "then we do 1.1 to tune and polish it": your looks on pre-season, draft night and the oval ring, and which Tier A items.
- T7.O12 Whether your "only spawn opus medium effort helpers, you stay fable high" rule, written for a lead who no longer exists, still binds the critic agents and helpers a plain session spawns, and if so which models and effort.
- T7.O13 When a session has no task, whether it asks you for one (global file) or works the open-requirements register (2026-11-03 handoff: "NO new tasks and do not ask him for one").
- T7.O14 Whether the league balance and calibration suites run on every pull request or only in the nightly run, given the 240 second rule and "Yes, all of it" already took league_balance off PRs.
- T7.O15 Whether to retire the remaining no-digit checks on non-gate screens, and whether to loosen the stats column pixel bands to no-clipping only, or leave both as they are.
- T7.O16 Of the cut audit's 158 rows (46 decision, 112 click), which candidates beyond 1 to 5, 9 and 11, if any, are cut.
- T7.O20 Whether to turn on GitHub's "Automatically delete head branches" (agents are denied remote deletion), and whether the WSL2 self-hosted runner pilot is still wanted after the CI redesign.
- T7.O21 Whether the game is far enough along that a session should recommend the trailer gate (ARD-M8-010) is ready; nothing starts until you say so.
- T7.O19 Whether you accept the proposed phone budgets (match view p95 under 33 ms, cold start under 6 s) and whether CI fails when PERF_BASELINE is exceeded.
- T7.R89 Whether the transparency continuation order stands as proposed (M3, M4, M6, M7, M2 copy first; L1 after Q3, L2 with Q4; M1 after Q2; C2 copy; M5 after #850; L4, C1, S1 after Q5, Q6, Q9; S2 after Q8; L3 after measuring), or you re-order it.
- T8.Q2 Whether Elite in the List Profile means the top four, top three or top two of eighteen (one constant, ListProfile.ELITE, re-measured first).
- T8.Q4 Whether the sim keeps rare big margins (100+ about 0.5% vs real about 1.9%) or gets more of them through Momentum, as its own balance-gated item.
- T8.Q6 Whether the key forward v key defender full-time duel line shows only after 6 or more contests, is changed in the engine, or is left as it is.
- T8.Q7 Whether wet-weather tackles stay at +6% (protecting scoring) or move toward the +12% real-world target.
- T8.Q8 Whether to close the midfield intercept gap now (sim 1.4 vs real 2.5) or keep it deferred under 'Merge, gap later'.
- T8.Q9 Whether set shots rise from about 37.5% to about 55% of shots with conversion set by distance and total scoring held flat, or stay as they are.
- T8.Q10 Whether to fix the development drift (contested bull 3.5% to about 11%, hothead 6.2% to 32.1% over seven seasons) now, starting with finding the cause and the smallest fix, or leave it.
- T8.Q11 Whether to fix the listed-position bias toward midfield (about 85 forwards and 21 defenders read MID) via real_pos, which moves 122 players and 110 OVRs and must be settled with forward rating.
- T8.Q12 Whether the team builder makes at least one weakness compulsory (second optional, no extra overall power) or keeps weaknesses optional.
- T8.Q13 Whether unproven potential is discounted further in TradeValue beyond the first pass in #224, or the current 60% growth counting stands.
- T8.Q15 Whether the pass margin for learning-a-position projects is tightened from 3 first, with reach (6) and cost to team-mates left alone, or all three stay as they are.
- T9.Q7 Choose which goes first: the execution queue (ROADMAP 0.4.1 Season stats patch) or the visual sim reacting to coaching (ARD-M8-003 with M4-001/002/004).
- T9.Q8 Choose which stands: ROADMAP 0.1 standing authority to pick up ready items and merge, or CLAUDE.md 'a roadmap entry is not authorisation'.
- T9.Q10 Choose which wording stands for the game's priority: ROADMAP 0.2 'game first, simulation second', the project description's 'equal importance', or the bible's agency pillar, given the 2026-11-03 order of story generator, deep simulator, approachable game.
- T9.Q11 Confirm whether the press-conference answer rule stays 'a dice roll based on logic' (bible), which the shipped seeded rolls with odds shown already follow, or goes back to fixed plus or minus 1 effects.
- T9.Q12 Choose how secondary buttons look: flat PANEL surface with no outline (style guide section 3) or outlines (CLAUDE.md).
- T9.Q14 Pick which cuts from CUT_AUDIT_2026-11-03 you take: manual stat training, audio to Mute plus Volume, Club Forge create player, football-dept budget into high performance, Coaching screen into Hub/List, Culture sheet into Captaincy/List header, one pre-season drill plan, and the 'Ask before simming' setting.
- T9.Q15 Choose between keeping 'League Draft board shows scouted estimates' and the branch's rival scouting error cut to 0-4, or both together (which may overcorrect).
- T9.Q22 Say whether Medium may retune the CARRY_ROLES back-zone weights, given defenders carry the ball more than they should.
- T9.Q27 Decide whether wing marking keeps travelling with the player or moves to the position, and whether tap vs mobile ruck, swingman, tall vs small defenders and unicorns stay deferred.
- T9.Q28 Decide whether to adopt playtest gate 1.12 'Can I feel my decisions?' with the proposed pass test: name a decision that changed a visible contest over three matches, tell each match's story in three sentences including a player battle, and explain a loss as personnel, opposition, decision or luck.
- T9.Q29 Decide which screen keeps what between Hub navigation, the Ladder and Season stats where they duplicate each other.
- T9.Q30 Pick which of the ten biggest audit gaps goes first (coaching not visibly reacted to, match view identity, CareerSave.VERSION mismatch silently dropping a career, onboarding, pre-season behind a switch, clone figures, and the rest).
- T9.Q31 Select which of P-01 to P-11, P-16, P-19, P-21, P-22 and P-24 you take.
- T9.Q37 Decide whether stale PRs #745, #761 and #765 are closed or re-synced given 8 open against a cap of 3, and whether a 13.4 minute CI against the 10-12 minute target is acceptable.
- T9.Q39 Decide whether the ladder wording, pre-timeskip, press-dice and balance sign-off items recorded unassigned after the bible audit may now be assigned.
- T9.R18 Decide whether TODO row 13 (every decision gets a vignette) goes ahead now or waits for the section 1.11 playtest gate, which says: "Do not prioritise this until the current §1.11 playtest gate has proved that the underlying decisions themselves are informed, meaningful and give useful feedback."
