# Cost sheets: the event-card choices short of a side, 2026-11-08

TODO row 107 (T5.Q18): every event-card choice gets an upside and a downside. Built like row 63's sheets
(`COST_SHEETS_CLUB_AND_GAIN_ONLY_2026-11-06.md`): each choice keeps what it does and takes the one side it is
missing, from the effects cards already use, sized like their neighbours, and following the card's premise.
The line under the button is generated from the effect, as on every other card. Docs only: these sheets
change no card.

Sources: `BOTH_SIDES_LEFT` in tests/test_story.gd and `tools/audit/sides_impl.gd` (what each button shows on
screen, `StoryEngine.stakes_lines`). Row 63's second sheet already covers 36 of the 46 gain-only choices; these
sheets cover the other 35 short choices. The 27 choices whose only gain is the other choice's cost they spare
are not here: whether that line counts as an upside is its own question (see the end).

Effects used: "morale N%" (`morale`, for him, the side or the whole list), "trust N%" (`trust`), "board N%"
(`board`), a culture strand ("Togetherness", "Standards", "Ambition", `culture`), "N XP" (`xp`), "slow start N%"
(`slow_start`, the side this week), "expects a game" (`expects_game`, with its sting).

## Sheet A: choices that only cost, each takes a gain (16)

The captain's contract talk first: this branch makes the card reachable, and these are two of its three answers.

| # | Card / choice | Cost today | Proposed gain | Why (the premise) |
|---|---|---|---|---|
| A1 | captain_contract_wait/ride | morale -1% (all) | he trusts you 2% more | His contract stays between him and the club |
| A2 | media_young_feature/no | his morale -3% | he gets 4 XP | His week stays on football, not cameras |
| A3 | media_team_leak/let | board -3% | Togetherness +1% | Nobody in the group is put under suspicion |
| A4 | media_cameras_in_rooms/no | board -2% | Togetherness +1% | The rooms stay the players' |
| A5 | media_papers_fronts_group/private | trust -2% | morale +1% (side) | The review stays on the football |
| A6 | contracts_wants_to_extend/wait | morale -5%, trust -3% | the saving, as a Gain line: no premium for certainty ({wait_price}) | Today the saving is a note under the button, not a Gain line |
| A7 | contracts_manager_noise/ignore | board -2% | he trusts you 2% more | You did not go round him to his manager |
| A8 | captain_selection_word/coaches | his morale -3%, trust -2% | Standards +1% | Selection stays the coaches' call |
| A9 | captain_group_flat/hard | morale -2% (all) | 4 XP (all) | A hard session is still a session (as captain_harder_session/back) |
| A10 | captain_harder_session/keep | his morale -2% | morale +1% (all) | No extra load on a tired group |
| A11 | board_president_lunch/no | board -3% | 2 XP (side) | You stay at training |
| A12 | members_signing_session/no | board -2% | morale +1% (all) | They go home after a long session |
| A13 | members_forum/results | board -3% | Standards +1% | The club answers with its football |
| A14 | members_finals_tickets/ceo | board -2% | 2 XP (side) | Your finals week stays on the football |
| A15 | captain_slump_flat/nerve | none of its own (the other choice rests him) | he plays this week, as a Gain line | Today the line exists only as the spared gain, which no screen prints |
| A16 | captain_young_player/notyet | none of its own (the other choice owes {kid_name} a game) | no game owed to {kid_name}, as a Gain line | As A15 |

A15 and A16 also take a cost (sheet B).

## Sheet B: choices that do nothing, each takes a gain and a cost (11)

| # | Card / choice | Today | Proposed gain | Proposed cost | Why (the premise) |
|---|---|---|---|---|---|
| B1 | captain_contract_wait/hand | nothing ("Nothing changes yet.") | morale +2% (all) | board -2% | The group is settled; you have told it a deal is in hand before one is done |
| B2 | media_trial_worked/ok | nothing (the card's one answer) | his morale +3% | expects a game in the role (sting 6%) | The papers call the move a success |
| B3 | media_trial_not_yet/ok | nothing (the card's one answer) | he trusts you 2% more | his morale -2% | You were straight with him that it has not landed |
| B4 | captain_holding_group/letbe | nothing | Togetherness +1% | his morale -1% | The run belongs to the group; his work goes unremarked |
| B5 | captain_slump_good/letbe | nothing | Togetherness +1% | his morale -1% | As B4 |
| B6 | captain_contract_signed/letbe | nothing | Togetherness +1% | his morale -1% | The others' contracts are still open (row 63's sheet 2, row 9, uses this premise for "Good news") |
| B7 | captain_contract_open/understood | nothing ("It waits for the end of the season.") | the saving, as a Gain line: no premium for certainty | his morale -2% | As contracts_wants_to_extend/wait (A6) |
| B8 | captain_succession_start/notyet | sets the story going, nothing else | his morale +2% | board -2% | His captaincy is not questioned; the board has no succession plan (row 63's sheet 2, row 11) |
| B9 | captain_succession_next/later | ends the card | his morale +2% | {vice_name}'s morale -2% | He keeps the job; {vice_name} was told he is ready |
| B10 | captain_slump_flat/nerve | the spared gain only | (A15) | his morale -2% | He is left to find it himself |
| B11 | captain_young_player/notyet | the spared gain only | (A16) | the captain trusts you 2% less | His word on the kid is not taken |

## Sheet C: finals and Grand Final choices that only gain, each takes a cost (10)

The ten gain-only choices row 63's sheet does not cover.

| # | Card / choice | Gain today | Proposed cost | Why (the premise) |
|---|---|---|---|---|
| C1 | finals_written_off/pin | morale +5% (side) | slow start 10% (side, this week) | Too wound up early (row 63's sheet 2, row 6) |
| C2 | finals_written_off/back | morale +2% (side), Togetherness +2% | board -2% | The board would rather you said less before a final |
| C3 | finals_one_week_short/not_done | morale +4% (all), Ambition +2% | Standards -1% | No spot is put on notice |
| C4 | finals_knocked_out/thanks | Togetherness +2% | Standards -1% | The bar for next year is not set |
| C5 | gf_runners_up/let_go | Togetherness +2% | Ambition -1% | The year is settled for, not chased |
| C6 | gf_night_before/together | morale +4% (side), Togetherness +2% | slow start 10% (side, this week) | Away from home, some do not sleep |
| C7 | gf_night_before/families | fresh legs (side) | morale -1% (side) | Apart from the group, some lie awake with it |
| C8 | finals_drought_over/feel | morale +6% (all), Togetherness +2% | slow start 15% (side, this week) | The noise gets to them early (as board_billboards/yes) |
| C9 | finals_drought_over/outside | 3 XP (all), Standards +1% | morale -1% (all) | The players miss the moment |
| C10 | gf_premiers/again | morale +4% (all), Ambition +2% | board -2% | The club and its members wanted the party |

## Build notes (for after the ruling)

- A6, A15, A16 and B7 change wording only: the line moves from a note (or the unprinted spared line) to a Gain line.
- B2 and B3 are each the only answer on their card; they keep one button.
- B9 needs a morale effect on {vice_name} while the captain is the subject (row 63's build notes, row 10).
- Each built row comes off `BOTH_SIDES_LEFT`, and `BOTH_SIDES_FLOOR` drops by one.

## The 27 spared choices

Each shows a cost on screen and nothing else. Its upside is the other choice's cost it does not carry ("he plays
this week", "no slow start"), which `StoryEngine.card_lines` writes as a Gain line but no screen has printed
since #837 moved the hub card into EventCardView. If that line counts as an upside, printing it under the button
again gives all 27 both sides with no card change. If it does not, each needs a gain of its own, drafted as
sheet A was. The list is `SPARED_GAIN_LEFT` in tests/test_story.gd.
