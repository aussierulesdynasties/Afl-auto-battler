# Event card audit, 2026-11-08 (row 107)

TODO row 107 (T5.Q18, row 34): every event-card choice gets an upside and a downside, and every card nobody
has seen gets a trigger it can meet. Two questions, two methods:

1. **Does every choice say what it gives and what it costs?** A test builds all 135 cards with every choice
   they are written with and reads the Gain and Cost lines each button shows on screen
   (`StoryEngine.stakes_lines`, the lines EventCardView prints). `tests/test_story.gd`
   `_test_every_choice_has_both_sides`; `tools/audit/sides_impl.gd` lists them all.
2. **Can every card come up?** Seeded careers on GitHub's runners (`tools/audit/cards_impl.gd` through
   `audit.yml`), pooled with `python tools/audit/card_audit_report.py union RUN_DIR...`: for each card, the
   careers that drew it, how often, and the weeks its trigger held.

## Summary

| | Count |
|---|---|
| Cards / choices | 135 / 290 |
| Choices that show a gain and a cost on screen | 192 |
| Choices that show a cost only, whose one upside is the other choice's cost they spare | 27 (that line is written, `StoryEngine.card_lines`, but no screen prints it) |
| Choices short of a side | 71: 46 gain only, 14 cost only, 2 that only spare a cost, 9 that do nothing |
| Cards drawn at least once, four grids pooled (136 careers, 925 seasons) | 132 of 135 |
| With real names, the default game (44 careers, 286 seasons; grids 1 and 2 only) | 119 of 135 |
| With fictional names (92 careers, 639 seasons) | 130 of 135 |
| Cards never drawn | 3: the Grand Final eve (its trigger held in all 10 Grand Final weeks), the Irish international torn about home (held 15 weeks), the New Zealand rugby offer (never held) |
| Triggers fixed in this branch | 2 (the captain's contract talk, the running-again card) |

## 1. Upside and downside on every choice

Built (director 2026-11-08: "Put them in", "Give each its own gain"): every choice below now carries the side
it was missing, from row 63's second sheet (`COST_SHEETS_CLUB_AND_GAIN_ONLY_2026-11-06.md`, 36 gain-only
choices; rows 25-27 changed, see its "As built") and this row's sheets (`COST_SHEETS_ROW107_2026-11-08.md`, the
other 35 and the 27 spared). The short, spared and do-nothing lists are gone: `_test_every_choice_has_both_sides`
now fails if any choice on the deck shows less than a gain and a cost. The lists below are what the audit found
before the build.

**Cost only (14):** the choice says what it costs and gives nothing back.
media_young_feature/no, media_team_leak/let, media_cameras_in_rooms/no, media_papers_fronts_group/private,
contracts_wants_to_extend/wait, contracts_manager_noise/ignore, captain_selection_word/coaches,
captain_group_flat/hard, captain_harder_session/keep, captain_contract_wait/ride, board_president_lunch/no,
members_signing_session/no, members_forum/results, members_finals_tickets/ceo.

**Gain only (46):** 36 are on row 63's second cost sheet (`docs/research/COST_SHEETS_CLUB_AND_GAIN_ONLY_2026-11-06.md`);
10 are finals and Grand Final choices on this row's sheet C: finals_written_off/pin, finals_written_off/back,
finals_one_week_short/not_done, finals_knocked_out/thanks, gf_runners_up/let_go, gf_night_before/together,
gf_night_before/families, finals_drought_over/feel, finals_drought_over/outside, gf_premiers/again.

**Only spares a cost (2):** captain_young_player/notyet, captain_slump_flat/nerve. Their one line is the other
choice's cost they avoid.

**Nothing at all (9, plus the 2 above in `DOES_NOTHING_LEFT`):** media_trial_worked/ok, media_trial_not_yet/ok,
captain_holding_group/letbe, captain_slump_good/letbe, captain_contract_wait/hand, captain_contract_signed/letbe,
captain_contract_open/understood, captain_succession_start/notyet, captain_succession_next/later. Most are the
"I hear you" answer that closes an arc.

**The spared line (27 choices, counted on their own):** a choice whose own effects gain nothing has the
other choice's cost it does not carry written as its gain ("No 15% chance of a slow start.",
`StoryEngine.card_lines`). No screen has printed that line since #837 moved the hub card into EventCardView,
which prints `stakes_lines`, so on screen these 27 show a cost only. Whether the line counts as an upside, and
so should be printed again, was a director question. Ruled 2026-11-08: it does not count, and each got a gain
of its own.

## 2. Can every card come up

Each career is one club over 10 seasons from 2027 (shorter when the coach is sacked and the run ends), either
with the club's real list ("lists") or after a fresh draft of the whole league ("redraft").

| Grid | The audit coach | Clubs | Careers | Seasons | Names | Cards drawn of 135 |
|---|---|---|---|---|---|---|
| 1 | answers at random | 8 | 32 | 194 | 16 fictional, 16 real | 112 |
| 2 | answers at random | 11 | 56 | 383 | 28 fictional, 28 real | 121 |
| 3 | takes the choice he has taken least, drafts international prospects first, re-signs his best 30 | 12 | 24 | 176 | fictional | 120 |
| 4 | as grid 3, plus a Heavy first pre-season block and the captain's-slump branch answers | 12 | 24 | 172 | fictional | 128 |
| All | | | 136 | 925 | | **132** |

Grid 4's season finishes (172 seasons): 127 missed the finals, 40 went out in the finals, 2 lost a Grand
Final, 3 won the flag. Across all four grids the coach's club reached 10 Grand Finals in 925 seasons (3 flags):
the audit coach is weaker than a person, so the Grand Final and flag cards come up rarely here.

**First reached in grid 4:** the running-again card, once the coach trained Heavy (10 times in 9 careers); the
captain's flat slump ending, once he followed that branch (once); and, by the luck of the draw and the ladder,
last year's premiers in the pre-season (once), the Grand Final injury race (once), the Grand Final win (3) and
the African visa card (2).

**Never drawn, and why:**

| Card | Weeks its trigger held | Why it was not drawn | Where its trigger is proven |
|---|---|---|---|
| gf_night_before (the night before the Grand Final) | 10, every Grand Final week | Weight 1 against the other Grand Final week cards (the opponent at 2 was drawn 9 times; the week itself, also weight 1, 3 times) | `tests/test_finals_cards_2.gd` |
| intl_irish_torn (the Irish player torn between a new deal and home) | 15 | Needs an Irish international with two seasons on the list, rated 80 or more and in his last contract year (the early-extension rule); the trigger held but the draw missed it | `tests/test_international.gd` |
| intl_nz_rugby_offer (a rugby offer for the New Zealander) | 0 | The same bar for a New Zealander: none of the 101 the coach drafted reached 80 in his last contract year | `tests/test_international.gd` |

**Real names, the default game (44 careers, 286 seasons): 119 of 135.** These are grids 1 and 2 only (the
coach answers at random), and both ran before the running-again fix. The 16 cards not drawn there:

| Cards | Why |
|---|---|
| The captain's slump (captain_slump_start, _mid, _good, _flat) and succession (captain_succession_start, _next): 6 | Private cards skip a real-named player (`StoryEngine.eligible_subject`), and the captain is a real player, so their trigger never held. They come only once a fictional player (a draftee) is captain. With fictional names they came 127 times. |
| The Irish, New Zealand and African visa cards (intl_irish_torn, intl_nz_rugby_offer, intl_africa_visa): 3 | Their trigger held 0, 0 and 1 weeks: the random coach drafts few internationals. Their subjects are fictional, so real names do not bar them. |
| The running-again card (pre_knee_return) | Run before its fix. |
| Last year's premiers, the Grand Final week, its eve, the injury race and the flag (pre_flag_hangover, gf_week, gf_night_before, gf_racing_the_clock, gf_premiers): 5 | The random coach seldom reaches a Grand Final. |
| finals_gone | Its trigger held 95 weeks; it came twice in 416 trigger weeks over all four grids. |

The family cards, also private, still came with real names on (25 to 68 times each): their subjects are the
fictional players the club drafts. The skip is the director's rule of 2026-10-11 (a card that invents a private
life is never about a player under his real name).

## 3. Triggers fixed in this branch

- **The captain's contract talk (captain_contract_wait).** It opened six weeks after the captain's contract
  arc began, but the arc's end beats are due at four, so an end always came first and closed the arc. It now
  opens at three. `_test_arc_middle_before_end` holds every arc's middle beat before its first end beat, and
  `_test_captain_contract_talk_dealt` begins the story for Geelong's captain and advances real weeks: the
  engine deals the talk three weeks on, before either ending. Two of its three answers are short of a side
  (sheet A1 and B1 of `COST_SHEETS_ROW107_2026-11-08.md`).
- **The running-again card (pre_knee_return).** Written for a knee coming back in the pre-season, but every
  injury heals over the off-season and the pre-season's own training injuries are soft tissue (hamstring, calf,
  groin, quad), so no knee was ever there to come back from. It now comes up for any injury the physio is
  managing that can be rushed (not a concussion), titled "{name} is running again", and names the injury
  ("after a hamstring strain"). Only a Heavy pre-season week injures, so a club that trains Solid all summer
  never sees it: in grid 4, where the coach's first block is Heavy Running, its trigger held 96 weeks and it
  came up 10 times.

  Its choices now speak of the pre-season, not a match week. Both are worked out from the club's blocks as
  set (`ClubStories.preseason_miss`: the weeks he would sit out, what each would have trained, and the
  injury weeks still to run at Round 1):
  - **Clear him to play.** Gain: he trains with the group from now, about N XP of pre-season development he
    would otherwise miss; when the physio's plan runs past the pre-season, he is right for Round 1. Cost: he
    is sore until Round 1 (the chance he is hurt in the pre-season match, if it is still to come, and in
    Round 1, and he starts each short of fresh legs), and he trains through the Heavy weeks he would have sat out. The result reads "{name} is
    cleared and trains with the group from now."
  - **Follow the physio's plan.** Its trust gain and morale cost are unchanged; it now also names what it
    costs (new op `keep_out`, no effect of its own): the same XP, and the weeks he is still out at Round 1.

  Director 2026-11-08: the card comes every time, for any pre-season injury the physio is managing as it
  nears its end (1 to 6 weeks left), never for a concussion. A player back for next week's training anyway
  still brings it, and clearing him then says so: "He trains with the group from now. On the physio's plan he
  is back for next week's training anyway, so clearing him gains no development and no Round 1 game." `tests/test_preseason_cards.gd`: `_test_facts`
  checks the trigger, the words and the concussion bar; `_test_running_again` checks the numbers and lines
  on the club's blocks, the cleared result, the Round 1 case, the back-next-week case and the concussion bar, and, walking ten pre-seasons
  with a Heavy first block (the injury risk raised for the test), that at a card stop a player hurt on the
  track meets the trigger and nobody else does.

## Not exercised

- The audit coach answers at random (grids 1 and 2) or by the least-taken choice (grids 3 and 4); no press
  answers. Selection is the automatic team.
- Grids 3 and 4's coach drafts international prospects first, re-signs his best 30, and in grid 4 trains Heavy
  in the first pre-season block and answers the captain's slump by resting him and then leaving him be: all
  choices a player can make, not rules; they reach the cards a random coach seldom does.
- The grids ran on four commits of this branch (grid 1 before both trigger fixes, grid 2 before the
  running-again fix, grid 3 before the audit's Heavy and branch options): a card a grid reached is reachable on
  the commit it ran on and later.
- One week of pre-season stops is three card weeks; a pre-season card competes with 10 others.

## Runs

`gh workflow run audit.yml --ref claude/event-card-costs -f impl=cards_impl -f env="ENV" -f args="SEED CLUB 10 [lists] [real]"`,
then `python tools/audit/card_audit_report.py union RUN_DIR...` over the downloaded `audit-cards_impl` artifacts.

| Grid | Commit | ENV | Seeds | GitHub run ids |
|---|---|---|---|---|
| 1 | a5e47e0d | (none) | 1-8 | 42391274248 .. 42391454668 (32) |
| 2 | 2d1a5461 | (none) | 1-8, 21-26, 31-36 | 42397635146 .. 42398372114 (56) |
| 3 | 783064ef | `COVER=1 INTL=1 KEEP=1` | 41-52 lists, 61-72 redraft | 42405925226 .. 42406201030 (24) |
| 4 | 822e9372 | `COVER=1 INTL=1 KEEP=1 HEAVY=1 ANSWER=captain_slump_start:rest,captain_slump_mid:leave` | 81-92 lists, 101-112 redraft | 42409231909 .. 42409544386 (24) |
