# TODO rulings archive

Dated ruling sections moved out of [TODO.md](TODO.md) on 2026-11-13 to keep the work list short (director: "move all completed items to an archive doc rather than clogging the active document"). They are reference, not work; the Director Bible holds every ruling, and the later ruling wins. Not a must-read file.

## V. Visual direction (rulings 2026-11-04)

The director's visual rulings V-R1 to V-R9 are in Rulings (director, 2026-11-04).

| Id | What | Done looks like |
|---|---|---|
| V2 | Premiership streamers in club colours | plays once on the premiership screen only, a capture frame shows both club colours |
| V3 | Brownlow winner reveal: 24 gold sparkles After: V2. | plays once on the winner reveal only, 24 sparkles, a capture frame |
| V5 | Training results is the proof screen for the new look, then the hub, then the other screens After: V4, 135 and 6.34. | director approves Training results on his phone before the hub starts, then the hub before the rest |
| V6 | Match chrome: scorebug 56 to 72 px, bottom decision sheet about a third of the height, one-button transport, goal and siren poster card After: 132. | captures at 390x844, the oval gets the freed height, every decision reachable with a real tap |
| V7 | Navigation icon set (AI-assisted candidates) | one icon per hub destination, director approves or rejects |
| V8 | Refresh captures of every screen on current main (the newest are 2026-10-07 to 10-11) After: T3.R9 and copy passes 131 to 140. | one capture per screen at 390x844, dated, in the audit folder |
| V9 | Housekeeping: placeholder logo name, stale worktrees (`The MCG.glb` is already out of the repo) | logo name is final or marked placeholder in one place, `git worktree list` shows only live ones |

## Rulings (director, 2026-11-04)

Settled answers that are not build rows. The bible stays as it is unless he consents to a change.

- A TODO row is authorisation to build it; a roadmap entry alone is not. With no task, work the TODO.
- Any doubt is a fail; every visual goes to him after the session's own frame check (no critic agents since 2026-11-05).
- Game, simulation and story carry equal importance. Secondary buttons are outlines.
- Press answers are seeded rolls with the odds and both outcomes shown (the bible line stands; already shipped).
- Polish goal 1 (player agency in matchups and rotation changes) stays open as written.
- Teaching is XP scaling, not the season-ceiling point.
- Personality types and captaincy: wanted, later (section F).
- Row 13: all five scenes, waits for the 1.11 playtest gate; time pauses at a decision.
- Weather has full effect on play; wet tackles toward the real +12% (row 61); its look never touches the sim.
- Ladder lives in Season stats; the hub nav bar has no Ladder.
- Free for now: web, Windows and Android APK on itch; Google Play only on his written yes.
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
- Draft AI veterans (2026-11-05): "petracca and stewart should be 125-150"; Petracca overridden to 87; building clubs count a retired season at 0.35.

## Rulings (director, 2026-11-06)

- GitHub deletes a PR's branch when it merges (T7.O20; turned on 2026-11-06).
- League balance and calibration suites run nightly only (T7.O14); balance-threshold checks leave the nightly (2026-11-10).
- Phone performance budgets and a CI perf gate: not now (T7.O19).
- Tests: "do a small amount on my pc the rest github": CI on GitHub, local runs small. No self-hosted runner.
- Trade value keeps counting 60% of unproven growth (T8.Q13).
- The visual sim reacting to coaching goes before the Season stats patch (T9.Q7).
- Skills travel with the player: "their skills dont change based on position" (T9.Q27). Tap v mobile rucks, swingmen, tall v small defenders and unicorns stay deferred.
- Playtest gate 1.12 "Can I feel my decisions?" is adopted (T9.Q28).
- No single first among the audit's biggest gaps: "all are important no focus on anything particular" (T9.Q30).
- Cascadeur Indie: written yes to buy (6.Q20); show him the price, he buys it.
- Kept as they are: Club Forge create a player, the Coaching screen (T1.Q7).
- 1.x is not frozen (T7.O4). AFLW later; Google Play much later; two-screen Team selection later (T3.R41).
- The game deliberately has no paid extras, no ads and no direct player control on the field (T5.Q21).

## Rulings (director, 2026-11-10)

- Audits and balance come last, after every other row: "we can rigorously audit and balance after the game is fully featured" (section Z).
- A build row whose done-test contains an audit closes when the build ships; the audit moves to section Z as its own row ("Yes, split them").
- Balance-threshold test checks move out of the nightly.
- Career story: player sheet and Brownlow night, up to five sentences, nothing when there is no story, one plain senior-coach register (a failed pick told plainly, no warmer farewell); built in #1334 (rows 144, 145).
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

- The coaching-style press interview comes before the draft ("its meant to go before the draft"), in every start mode; Continue returns to the draft board (row 141).

- Concussion: "if a player gets 5 or more concussions within a 5 year period, they should have to pass a medical retirement check". The check is "Flat odds each time"; the panel sits "Straight after the fifth", so a fail ends the career that week (row 154).
- Stretch goal, not assigned: "smart phone/social media hub including contacts, a folder for players screenshots, perhaps a home for stats and news too" (row 153, section F).

- Stretch goal, not assigned: Club Opinion, each rival club's opinion of the coach, separate from the Board (row 155, section F).

- Concussion medical retirements stay rare: "maybe 0.25 per year or less", above zero, measured over many seasons.

- State league (row 128): "just make sure the state league results are simulated very fast": every match but the coach's own uses a quick result model, under 5% added to Sim the week. Coaching in the state league flips it: the AFL becomes the quick background.

- Legacy mode from 1990 is in Build now (row 142).

## Rulings (director, 2026-11-12)

- His 1.0.15 reports: section headings take a sand ink, e8cf9c ("Sand (B)"); Defensive Press is renamed High Press ("Rename High Press"; same plan, old saves map); rows 172 and 173.
- Visual overhaul: match day first, one look sheet per area, rig and Tripo without asking (rows 166-171; answers in the Director Bible). Trades check: "Decline the letter in the test".
- Auto-pick keeps its name ("I already answered this question"), exempt from the engine-word ban (row 134).
- Every draftee in every draft shows one line "Plays like: <real AFL player>", from facts: same position, about his level ("level must be included"), similar height, closest ratings at max potential (`PlaysLike.gd`). A line under the name, never in it.
- Sim speed "Speed up the engine", drift inside AFL bands (row 159). Weather "Yes, at a break" (160). Feed colours: our goals in our colour, red conceded, grey the rest, no blue (161). Pre-match calls stay pre-bounce. Vignettes on every card (162). Autopilot to mid-table (163). Draft "Must make room" (164).
- Design bible updated with his consent: the press risk line, pillars (story, deep simulator, agency, readability), a story question first in the feature test, and "What this game will not have" (all but 14 and 15).
- Merge queue on. Legacy money "Dollars of the time"; 1990-2012 cap gaps "look harder" (row 142). Press-room coach "Re-render sharper".
- Game-plan traits are removed and replaced by a custom game plan: 1 strength and 1 cost from a list, a plan of its own, neutral like Win Contest (never counters or is countered), every club can run one (rows 158 and Custom plan).
- Real names only: "remove 'generated names' from the game, Real Names only". The Player names choice is gone; row 56 has no fictional-names fallback (bible 3.35a).
- Form on team selection: "Reserves games". A weekly reserves rating shows for players in the reserves, display only, no sim effect.
