# Cost sheets: club dominant options and the gain-only story options, 2026-11-06

TODO row 63 (T5.Q2 and T5.Q3, both answered A). Built like the 17 story-card costs he approved ("Approve all 17",
ch. 30 row 30): each option keeps its gain and takes one cost that follows the card's premise, from the same set of
costs (a 10-20% chance of a slow start, a selection promise that stings, board confidence down 2%, one morale point,
development forgone). The cost line is generated from the effect as a percentage, as on the 17. Nothing is dropped.
Sheet 2 was built 2026-11-08 in PR 1153 (director: "Put them in"); see "As built". Sheet 1 is still docs only.

Sources: the gain-only list was `GAIN_ONLY_LEFT` in tests/test_story.gd (36 options on 2026-11-06; the ruling said 33).
Row 107 folded it into `BOTH_SIDES_LEFT`, which PR 1153 emptied and removed; the club list is audit §5 "Club decisions"
(DECISION_TRANSPARENCY_AUDIT_2026-10-18.md) checked against data/stories/*.json and GameState.gd on main today.

## Sheet 1: club dominant options (T5.Q2)

What each audit item is today:

| # | Audit item | Card / code | Today | Proposed cost |
|---|---|---|---|---|
| C1 | Tribunal "Challenge at Tribunal" | GameState.challenge_mro (tribunal_chance 22-42%) | Failing costs nothing | Board confidence down 2% if the challenge fails |
| C2 | Appeals Board "Appeal" | GameState.appeal_mro (appeal_chance) | Failing costs nothing | Board confidence down 2% if the appeal fails |
| C3 | Warm contract answer "in your plans" | contracts_rivals_circling | Costed in #818 | none needed |
| C4 | "part of the plans" | contracts_kid_wants_clarity | Costed in #818 | none needed |
| C5 | "a deal is coming" | contracts_waited_manager_calls | Costed in #818 | none needed |
| C6 | "Lap it up" | board_billboards | Costed in #818 (15% slow start) | none needed |
| C7-C10 | Kind family options | family_partner_job_offer, family_newborn_no_sleep, family_partner_graduation, family_house_settlement | Costed in #818 | none needed |
| C11 | Mentor "Let him" | health_veteran_rehab_mentor | Costed in #818 | none needed |
| C12 | "Send him" | members_cheer_squad | Costed in #818 | none needed |
| C13 | "Let him run it" | leadership_senior_runs_session | Costed in #818 | none needed |
| C14 | "Give them the room" | captain_leaders_meeting | Costed in #818 | none needed |
| C15 | "Explain it" | captain_selection_word/talk | Gain-only | Sheet 2, row 4 |
| C16 | "Give them a day off" | captain_group_flat/dayoff | Gain-only | Sheet 2, row 5 |
| C17 | Sit-down talks: Explain beats "It's my call" | selection_talk_dropped/back/waiting, explain | Gain-only | Sheet 2, rows 25-27 |
| C18 | Near-dominant "Wait for the off-season" | contracts_wants_to_extend/wait | Now costs morale 5% and trust 3% | none needed |

Cost lines for the two new ones:
- C1: "If the Tribunal says no: board confidence falls 2%." (Gain line unchanged: the case and its odds.)
- C2: "If the Appeals Board says no: board confidence falls 2%."

## Sheet 2: the gain-only story options (T5.Q3)

"slow start N%" = the existing `slow_start` effect; "forgo N XP" = the existing `forgo_xp` effect (line: "Slower growth:
... goes without N XP of development (a senior game gives 37)"); "expects a game" = `expects_game` with its sting.

| # | Card / option | Gain today | Proposed cost | Why (the premise) |
|---|---|---|---|---|
| 1 | community_hospital_visit/go | morale +3% all, board +2% | slow start 10% (side, this week) | An afternoon signing jumpers |
| 2 | finals_club_greats/in | morale +4% all, board +1% | slow start 10% (side, this week) | Ten minutes of history in finals week |
| 3 | health_finals_light_week/light | fresh legs, all | forgo 6 XP (all) | The main session is cut |
| 4 | captain_selection_word/talk | trust +4%, morale +2% | morale -1% (all) | The group sees the captain gets the explanation, not them |
| 5 | captain_group_flat/dayoff | morale +3% all | forgo 4 XP (all) | A day of training lost |
| 6 | captain_big_week/speak | morale +3% all, trust +3% | slow start 10% (side, this week) | Too fired up early |
| 7 | captain_holding_group/noticed | morale +3%, trust +4% | morale -1% (all) | Praise for one, not the group |
| 8 | captain_slump_good/noticed | morale +4%, trust +3% | expects a game (sting 6%) | He takes it as his spot being safe |
| 9 | captain_contract_signed/good | morale +3%, trust +3% | morale -1% (all) | The others' contracts are still open |
| 10 | captain_succession_start/handover | trust +2% | captain's morale -3% | He hears the end coming |
| 11 | captain_succession_start/asks | trust +4% | board confidence -2% | No succession plan for the board |
| 12 | finals_last_season/quiet | trust +6% | board confidence -2% | The club can't plan his farewell |
| 13 | finals_second_chance/burn | morale +4% side | forgo 6 XP (side) | Mistakes not reviewed |
| 14 | finals_captain_last_word/him | trust +8%, held: morale +5% side | if it doesn't land: morale -2% (side) | The "failed" branch is empty today |
| 15 | gf_last_game/him | morale +8% side | if you lose, 20% chance the side's morale also falls 8% | Same as finals_last_season/tell |
| 16 | gf_last_game/calm | morale +5%, trust +6% | morale -1% (side) | No send-off to rally around |
| 17 | members_open_training/open | board +4%, morale +3% all | forgo 4 XP (all) | The coaches would rather work |
| 18 | members_open_training/closed | XP +8 all | board confidence -2% | The fans are shut out |
| 19 | finals_in/enjoy | morale +5% all | slow start 10% (side, this week) | A big night out |
| 20 | gf_milestone/banner | morale +8%, trust +4% | slow start 20% (him, Grand Final) | Same as gf_debut_year/enjoy |
| 21 | gf_milestone/club | morale +3% side | his morale -2% | His name is left off |
| 22 | rivals_spy_at_training/let | morale +2% all | forgo 4 XP (all) | Nothing new drilled while they watch |
| 23 | rivals_mouthing_off/calm | morale +1% all, fresh legs side | slow start 10% (side, this week) | No fire for the first quarter |
| 24 | gf_the_opponent/us | XP +4 side, morale +2% side | if you lose, 15% chance the side's morale also falls 6% | No edge against the team that knows you |
| 25 | selection_talk_dropped/explain | morale +5% (by trust), trust +3% | expects a game (sting 4%) | He hears a path back, a smaller promise than "a game this week" (sting 12%) |
| 26 | selection_talk_back/explain | same | expects a game (sting 4%) | same |
| 27 | selection_talk_waiting/explain | same | expects a game (sting 4%) | same |
| 28 | finals_first_final/minder | XP +6, trust +4% | morale -1% (side) | A senior player loses his own week |
| 29 | finals_first_final/alone | morale +7% | slow start 15% (him, this week) | Nerves on the day |
| 30 | gf_debut_year/away | morale +3%, trust +5% | board confidence -2% | The media wanted him |
| 31 | training_extra_session/recover | morale +3% all, fresh legs | forgo 6 XP (all) | No heavy week |
| 32 | training_seniors_day_off/give | morale +4% all, fresh legs | forgo 6 XP (all) | Monday's session lost |
| 33 | training_time_trial/skip | morale +1% all | forgo 3 XP (all) | No fitness read, no hard run |
| 34 | training_new_stoppage_setup/hold | morale +2% side | forgo 4 XP (side) | The new setup is shelved |
| 35 | training_backed_kid_flying/earned | morale +6%, trust +5% | expects a game (sting 6%) | He's told the spot is his |
| 36 | finals_week_off/semi | morale +4% all | slow start 10% (side) | No hit-out, half the Rest option's 20% |

## As built (sheet 2, PR 1153)

- Rows 1-24 and 28-36 went in as drafted. `forgo_xp` now names who goes without ("every player goes without 6 XP",
  "each player in the side goes without 4 XP"). Row 10's cost falls on the captain, the card's subject. Row 14
  fills the `failed` branch.
- Rows 25-27 went in as drafted (director 2026-11-08, "He expects a game"): sitting him down carries "expects a game"
  (sting 4%), so Auto-pick names him this week. The first build used Standards -1% instead; that is out.
- C1 and C2 are code, not card data (GameState challenge/appeal), and are not built.

## Questions for the director

1. Sheet 1: board confidence down 2% for a failed Tribunal challenge or appeal, as written?
