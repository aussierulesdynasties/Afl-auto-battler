# Event card audit, 2026-11-08 (row 107)

TODO row 107 (T5.Q18, row 34): every event-card choice gets an upside and a downside, and every card nobody
has seen gets a trigger it can meet. Two questions, two methods:

1. **Does every choice say what it gives and what it costs?** A test builds all 135 cards with every choice
   they are written with and reads the Gain and Cost lines each button shows (`StoryEngine.card_lines`, the
   lines the hub card prints). `tests/test_story.gd` `_test_every_choice_has_both_sides`.
2. **Can every card come up?** Seeded careers on GitHub's runners (`tools/audit/cards_impl.gd` through
   `audit.yml`), pooled with `python tools/audit/card_audit_report.py union RUN_DIR...`: for each card, the
   careers that drew it, how often, and the weeks its trigger held.

## Summary

| | Count |
|---|---|
| Cards / choices | 135 / 290 |
| Choices that show a gain and a cost | 219 (192 with both in their own effects, 27 whose gain is the cost they spare) |
| Choices short of a side | 71: 46 gain only, 14 cost only, 2 that only spare a cost, 9 that do nothing |
| Cards drawn at least once, four grids pooled (136 careers, 925 seasons) | 132 of 135 |
| Cards never drawn | 3: the Grand Final eve (its trigger held in all 10 Grand Final weeks), the Irish international torn about home (held 15 weeks), the New Zealand rugby offer (never held) |
| Triggers fixed in this branch | 2 (the captain's contract talk, the running-again card) |

## 1. Upside and downside on every choice

The test now fails if a choice joins the short list, and fails until a choice that gains its missing side
comes off it (`BOTH_SIDES_LEFT`, floor 71; `DOES_NOTHING_LEFT`, 11). No card copy or effect changed for this
half: every missing side is a design call that waits on the director (row 63's second cost sheet and the
questions in the PR).

**Cost only (14):** the choice says what it costs and gives nothing back.
media_young_feature/no, media_team_leak/let, media_cameras_in_rooms/no, media_papers_fronts_group/private,
contracts_wants_to_extend/wait, contracts_manager_noise/ignore, captain_selection_word/coaches,
captain_group_flat/hard, captain_harder_session/keep, captain_contract_wait/ride, board_president_lunch/no,
members_signing_session/no, members_forum/results, members_finals_tickets/ceo.

**Gain only (46):** 36 are on row 63's second cost sheet (`docs/research/COST_SHEETS_CLUB_AND_GAIN_ONLY_2026-11-06.md`);
10 are finals and Grand Final choices with no sheet yet: finals_week_off/semi, finals_written_off/pin,
finals_written_off/back, finals_one_week_short/not_done, finals_last_season/quiet, finals_second_chance/burn,
finals_captain_last_word/him, gf_last_game/him, gf_last_game/calm, finals_club_greats/in (the full list is in
the test).

**Only spares a cost (2):** captain_young_player/notyet, captain_slump_flat/nerve. Their one line is the other
choice's cost they avoid.

**Nothing at all (9, plus the 2 above in `DOES_NOTHING_LEFT`):** media_trial_worked/ok, media_trial_not_yet/ok,
captain_holding_group/letbe, captain_slump_good/letbe, captain_contract_wait/hand, captain_contract_signed/letbe,
captain_contract_open/understood, captain_succession_start/notyet, captain_succession_next/later. Most are the
"I hear you" answer that closes an arc.

**The spared line (27 choices pass only by it):** a choice whose own effects gain nothing states the other
choice's cost it does not carry as its gain ("Gain: no slow start"). Whether that counts as an upside is a
director question.

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

**Real names (44 careers):** with real names on, the captain's slump (4 cards) and the captain's succession (2)
never come: they are private cards and the captain is a real player. The family and international cards still
come, because their subjects are fictional players.

## 3. Triggers fixed in this branch

- **The captain's contract talk (captain_contract_wait).** It opened six weeks after the captain's contract
  arc began, but the arc's end beats are due at four, so an end always came first and closed the arc. It now
  opens at three. `_test_arc_middle_before_end` holds every arc's middle beat before its first end beat.
- **The running-again card (pre_knee_return).** Written for a knee coming back in the pre-season, but every
  injury heals over the off-season and the pre-season's own training injuries are soft tissue (hamstring, calf,
  groin, quad), so no knee was ever there to come back from. It now comes up for any injury the physio is
  managing that can be rushed (not a concussion), titled "{name} is running again", and names the injury
  ("after a hamstring strain"). The choices and their effects are unchanged. `tests/test_preseason_cards.gd`
  `_test_facts` checks the trigger, the words and the concussion bar. Only a Heavy pre-season week injures, so
  a club that trains Solid all summer never sees it: in grid 4, where the coach's first block is Heavy Running,
  its trigger held 96 weeks and it came up 10 times.

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
