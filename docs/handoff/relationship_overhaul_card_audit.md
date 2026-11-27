
# Event card deck audit

2026-11-26 · @Baggins


## Summary

The game has 773 event cards, not 134: 134 in the weekly deck, 552 in the 22 club decks, 42 beats across 14 coach career arcs, and 45 real-history year-event cards. About a quarter need rework for the relationship overhaul and 5 should be retired. Nothing in the deck can read a player's personality, an opinion, a bond or a council member today, so most of the overhaul's drama has to come from new cards, not rewrites.

| Set | Cards | Keep | Rework | Retire |
|---|---|---|---|---|
| Weekly deck (13 categories) | 134 | 74 | 55 | 5 |
| Club decks (22 decks) | 552 | 449 | 103 | 0 |
| Coach career arcs (14 arcs, 42 beats) | 14 arcs | 7 | 7 | 0 |
| Real-history year events | 45 | 45 (8 gain a Respect/Authority shift) | 0 | 0 |

What the audit found:

- **No card reads character.** Zero of 773 cards trigger on trust, opinion or anything like temperament. Unhappiness is read from morale alone (`selection_unhappy` fires at morale 34 or lower).
- **Only 7 cards name two players**, all captain cards (`{vice_name}`, `{kid_name}`). Cards that are about two people, such as two players squaring up at match sim or the mentor for a first final, leave them unnamed. These are the natural places to seed bonds.
- **Promises are spread over six ops and leak.** `expects_game`, `start_backing`, `back_kid`, `dev_promise`, `promise_win` and `on_record` each keep their own state. A further 14 club-deck choices say "promise" in the label ("Tell him he's next", "Promise finals") with nothing tracking them.
- **Trust moves are flat.** 201 trust moves exist (184 in decks, 17 in arcs), and all of them are permanent and none decay. Under the new Opinion model most become decaying modifiers by default. About 8 should be long-tail scars (finals snubs, a father in hospital, a captaincy taken).
- **Duplicated shapes.** 14 near-identical homesick cards across club decks, 16 pick-the-kid-from-the-reserves cards and 20 nights-out discipline cards. Each family should be one shared card that reads bonds and temperament, with each club's words kept as text variants.
- **Rivals only play bonding cards.** Rival clubs never draw weekly cards; they only roll one bonding choice in the pre-season (`ClubStories.rival_bond`). For parity across all clubs, opinion, bond and promise changes at rival clubs need an AI-side rule, not cards.

The full per-card list for all 773 cards is in event_card_audit.csv for the threads that do the rewriting.


## How event cards work today

Every card is JSON data played through one engine. `StoryEngine` picks the week's card, `StoryDeck` validates every card and caps each effect, and `ClubStories.apply_choice` applies a choice through levers the game already has. Coach arcs (`CoachArcs`, `ClubArcs`) and year events (`YearEvents`) reuse the same card UI and effect ops.

- **When a card comes up.** In 7 weeks of 10 you get a card. A due arc beat comes first, then a new arc start, then a one-off. Big weeks (round 1, the last round, each finals week) can bring a second card. Each card and each player has a cooldown, and no category comes up more than twice in five weeks.
- **What a card can test.** A card is about a player, picked by saved facts (age, games, fit, selected, contract years, captain, morale, international region and so on), or about the club. It can also need club conditions: a losing run, a ladder spot, a finals week, the opponent's deck.
- **Arcs inside the deck.** A choice can set a flag. A follow-up card names that flag and a window ("after 4 weeks, within 20"). Six arcs run this way: backed kid, contract wait, captain slump, captain contract, captain succession and the papers.
- **Privacy guard.** A card marked `private` invents something about private life, family or health of mind, and is never dealt about a real-named player. 20 deck cards carry it.

What a choice can change today, and where each lever goes under the overhaul:

| Lever today | Uses | Becomes |
|---|---|---|
| `board` | 868 | Unchanged |
| `morale` (player, side, all, others) | 746 | Unchanged. Opinion, temperament and bonds steer the morale target through `ClubLife` instead |
| `culture` (standards, together, ambition) | 730 | Unchanged. Faction moods can read it |
| `odds` (rolled outcome) | 262 | Unchanged |
| `xp`, `forgo_xp`, `rest`, `sore`, `fresh`, `heavy_legs`, `slow_start`, `loss_sting` | about 670 | Unchanged |
| `trust` (player, leaders, Indigenous group) | 201 | `Opinion.gd` tagged modifier: decays by default, long-tail or permanent when the card marks it |
| `expects_game`, `start_backing`, `back_kid`, `dev_promise`, `promise_win`, `on_record` | 24 (plus 2 in arcs) | One `Promises.gd` ledger, read by selection and by later cards |
| `delegate`, `captaincy_swap` | 8 | Unchanged, plus a bond or faction read (captain's allies) |
| `flag` (arcs) | 18 | Unchanged |
| _(none)_ | 0 | New: bond seed or break, Respect/Authority shift, council loyalty, faction mood |

Letters used in the catalogue for what a rework needs: **OP** opinion modifier with decay or scar, **PR** promise ledger, **RA** Respect/Authority, **BD** bonds, **TM** temperament gate or variant, **CV** council voice, **FX** faction. A "Keep" card still has its `trust` op converted to a decaying modifier by the Opinion migration; that needs no card edit.


## Card catalogue


### Weekly deck: 134 cards

74 keep, 55 rework, 5 retire. The rework sits mostly in selection, leadership, contracts and the promise cards; members, community and most finals cards stand as they are. Trigger reads as phase; who it is about; conditions.

| Card | Deck | Trigger | Changes today | Verdict | Hooks | Note |
|---|---|---|---|---|---|---|
| `selection_talk_dropped` | selection | regular/finals; player; fit, talk: dropped | morale, trust -4..+4, promised game, culture | Rework | PR RA BD TM | Promise goes to the promise ledger; "It's my call" builds Authority and costs Respect; his close mates hear about it; fiery and competitor players take it harder. |
| `selection_talk_back` | selection | regular; player; fit, talk: back | morale, trust -4..+4, promised game, culture | Rework | PR RA | Same three-way talk as the dropped card: promise to the ledger, "my call" to Authority. |
| `selection_talk_waiting` | selection | regular; player; fit, talk: waiting | morale, trust -4..+4, promised game, culture | Rework | PR RA TM | Same as above; a quiet achiever waits longer before he asks. |
| `selection_unhappy` | selection | regular; player; fit, morale ≤34 | morale, promised game, trust -4..+4 | Rework | TM OP PR RA | Trigger on a low opinion and temperament (mercurial, fiery) instead of morale under 35; "Make him earn it" builds Authority. |
| `selection_finals_experience` | selection | finals; player; fit, not in the side, 150+ games | promised game, morale, trust -4..+6, culture | Rework | OP RA FX | Leaving a 150-gamer out of a final is a finals snub: a long-tail mark, and the senior players react. |
| `finals_gone` | selection | regular; player; ≤21 yrs, fit, not in the side, out of side, not backing wait; finals out, rd ≤22 | run of games, trust +6, morale | Rework | PR BD | Run of games goes to the ledger; a senior teammate can take him under his wing (mentor bond). |
| `finals_first_final` | selection | finals; player; in the side, fit, no finals yet, debut this career, 5-40 games, ≤22 yrs; finals wk ≤4 | development, trust +4, morale, slow-start risk | Rework | BD | "Give him a mentor" names the mentor and starts a mentor/protege bond. |
| `gf_debut_year` | selection | finals; player; debut year, fit, in the side; finals wk 5 | morale, trust +5, board, slow-start risk | Keep |  | Trust move converts to a normal decaying modifier. |
| `training_extra_session` | training | regular; club | development, heavy legs, morale, fresh legs, development forgone | Keep | CV | The high performance head and the line coaches pitch the two options. |
| `training_kid_pushing` | training | regular; player; fit, not in the side, not backed, ≤21 yrs, growth 8+ | run of games, trust -8..+8, arc flag, development, rest | Rework | PR BD TM | Start of the backed-kid arc: the run goes to the ledger; the incumbent he would replace becomes a rival. |
| `training_extra_kicking` | training | regular; player; fit, ≤25 yrs, growth 4+ | development, heavy legs, trust +4, morale, fresh legs | Keep | CV TM | High performance head argues for him going home; a professional asks for this more often. |
| `training_match_sim_heated` | training | regular; club | morale, culture | Rework | BD RA | Name the two players. Letting it go seeds a rivalry; pulling them up builds Authority. Absorbs pre_sim_heated. |
| `training_seniors_day_off` | training | regular; club; rd 8+ | morale, fresh legs, development forgone, development | Rework | FX RA CV | The leaders ask as a group: refusing builds Authority and costs the leaders' opinion; high performance head weighs in. |
| `training_time_trial` | training | regular; club | development, morale, development forgone | Keep | CV | High performance head's call. |
| `training_new_stoppage_setup` | training | regular; club | development, heavy legs, morale, development forgone | Keep | CV | Already a staff pitch: the midfield coach speaks for himself. |
| `training_backed_kid_flying` | training | regular; player; fit, morale 70+; after backed_kid (4-20 wks) | morale, trust +5, promised game, development | Keep | PR | Arc end reads the kept promise from the ledger. |
| `training_backed_kid_struggling` | training | regular; player; fit, morale ≤60; after backed_kid (4-20 wks) | promised game, morale, trust -3..+6, development | Rework | PR OP | "Send him down" ends the run early: a broken promise with a long-tail mark. |
| `finals_week_off` | training | finals; club; finals bye | fresh legs, slow-start risk, development, morale, development forgone | Keep |  |  |
| `training_dev_talk` | training | regular/finals; player; fit, dev talk due | morale, trust +2..+3, position promise, no promise | Rework | PR | dev_promise and no_promise move to the unified ledger. |
| `health_pulled_up_sore` | health | regular/finals; player; fit, top 5 fit; 5+ fit | rest, plays sore, morale | Keep | CV | High performance head's voice. |
| `health_veteran_load` | health | regular; player; fit, in the side, 30+ yrs, 150+ games | rest, trust +3, morale, heavy legs | Keep | CV | High performance head's voice. |
| `health_knock_at_training` | health | regular/finals; player; fit, in the side | rest, plays sore, trust +3 | Keep | CV | Physio and player disagree; "take his word" stays an opinion move. |
| `health_finals_light_week` | health | finals; club | fresh legs, development forgone, development, heavy legs | Keep | CV | High performance head's voice. |
| `health_veteran_rehab_mentor` | health | regular; player; fit, 28+ yrs, 100+ games | morale, slow-start risk, development | Rework | BD | Name the injured kid; helping him starts a mentor/protege bond. |
| `finals_fitness_test` | health | finals; player; in the side, fit, top 3 fit; finals wk ≤4 | plays sore, trust -8..+4, rest, morale | Rework | OP CV TM | Ruling a competitor out of a final against his word is a long-tail mark; high performance head argues caution. |
| `gf_racing_the_clock` | health | finals; player; top 5 OVR, can be rushed, ≤2 wks injured; finals wk 5 | rushed back, trust -8..+6, morale | Rework | OP CV | Not risking him in a Grand Final is a permanent mark either way; high performance head and list manager pitch. |
| `family_baby_due` | family | regular; player; fit, in the side, 23+ yrs; private | rest, trust -10..+15, morale, culture | Rework | OP RA | Long-tail mark both ways ("you told him to be there"); Respect shift. Keep the private guard. |
| `family_dad_in_hospital` | family | regular; player; fit; private | rest, trust -10..+12, morale, slow-start risk, culture | Rework | OP RA | Asking him to play is a permanent scar; sending him home builds Respect. Keep the private guard. |
| `family_brothers_wedding` | family | regular; player; fit, in the side; private | rest, trust -5..+8, morale, culture | Rework | BD | If his brother is on a list (player_relations.csv family bond), the card names him. |
| `family_partner_job_offer` | family | regular; player; fit, ≤1 yr left, 23+ yrs; private | morale, trust -6..+6, board, culture | Rework | PR CV TM | "Promise the club's help" is an untracked promise today; goes to the ledger. List manager pitches; clubman vs mercenary react differently. |
| `family_newborn_no_sleep` | family | regular; player; fit, 22+ yrs; private | fresh legs, morale, trust +4, development forgone, heavy legs, development | Keep | CV | High performance head notices. |
| `family_partner_graduation` | family | regular; player; fit; private | morale, trust -2..+3, slow-start risk, development | Retire |  | Same afternoon-off shape as house settlement, smallest stakes in the deck; a click chore. |
| `family_house_settlement` | family | regular; player; fit, 22+ yrs; private | morale, trust +2, slow-start risk, development | Retire |  | Same morning-off shape, near-zero stakes; a click chore. |
| `finals_family_tickets` | family | finals; club; finals wk ≤4 | morale, board, culture | Keep |  |  |
| `contracts_wants_to_extend` | contracts | regular; player; fit, can extend | early extension, morale, trust -3, price open, arc flag | Rework | TM CV OP | Mercenary pushes harder, clubman waits; list manager pitches; "made to wait" becomes a decaying modifier. |
| `contracts_manager_noise` | contracts | regular; player; fit, ≤1 yr left, OVR 72+ | board, trust -3..+2 | Rework | TM CV | Fires mostly for mercenary players; list manager's call. |
| `contracts_one_more_year` | contracts | regular; player; fit, 31+ yrs, ≤1 yr left | morale, trust -2..+6 | Rework | RA CV | Being straight builds Respect; list manager pushes the list-age agenda. |
| `contracts_kid_wants_clarity` | contracts | regular; player; fit, ≤21 yrs, ≤3 games, out of side | morale, trust -2..+4, promised game, development | Rework | PR | "Tell him he's wanted" becomes a tracked promise. |
| `contracts_waited_manager_calls` | contracts | regular; player; fit, ≤1 yr left; after made_to_wait (6-20 wks) | morale, trust -6..+4, board, price open | Rework | PR CV | "Promise a deal later" is untracked today: goes to the ledger with a deadline. |
| `contracts_new_club_approach` | contracts | regular; player; ≤1 yr left; scripted | re-sign, let go | Keep | CV | Scripted expansion card. |
| `leadership_group_selection_say` | leadership | regular; club | morale, culture | Rework | FX RA | Leaders as a faction; keeping selection with the coaches builds Authority. |
| `leadership_senior_runs_session` | leadership | regular; player; fit, 150+ games | morale, trust +4, development, slow-start risk, culture | Rework | BD TM | Running the kids' session seeds mentor bonds; fires for leader temperaments. |
| `leadership_late_to_meeting` | leadership | regular; club | culture | Rework | BD RA | Name the two players (mates); making an example builds Authority, quiet handling builds Respect. |
| `leadership_players_meeting` | leadership | regular; club; lost 3+ in a row | morale, development forgone, development | Retire |  | Same ask as captain_leaders_meeting; fold into that card's losing-run variant. |
| `leadership_young_voice` | leadership | regular; player; fit, ≤23 yrs, 30+ games | trust -6..+8, morale, culture | Rework | TM RA FX | Fires for fiery or leader temperaments; pulling him up builds Authority; the young group notices. |
| `captain_selection_word` | leadership | regular; player; captain, fit, in the side | trust -2..+4, morale, culture, captain decides | Rework | BD FX | Name the dropped players the captain speaks for; his bonds with them shape the result. |
| `captain_group_flat` | leadership | regular; player; captain, fit; lost 3+ in a row | morale, development forgone, development, captain decides | Keep |  |  |
| `captain_harder_session` | leadership | regular; player; captain, fit | morale, development, captain decides | Keep | CV | High performance head can argue against. |
| `captain_young_player` | leadership | regular; player; captain, fit; kid in form | kid backed, trust -2..+3, culture | Rework | PR BD | back_kid goes to the ledger; the captain and the kid become mentor/protege. |
| `captain_leaders_meeting` | leadership | regular; player; captain, fit | trust -2..+3, morale, development forgone, culture, development | Rework | FX RA | Leaders as a faction; absorbs leadership_players_meeting. |
| `captain_big_week` | leadership | finals; player; captain, fit; finals wk 1+ | morale, trust +3, captain decides | Keep |  |  |
| `captain_holding_group` | leadership | regular; player; captain, fit; won 3+ in a row | morale, trust +4, loss sting, culture | Keep |  |  |
| `captain_rest_ask` | leadership | regular; player; captain, fit, in the side, 30+ yrs | rest, morale, trust -2, heavy legs | Keep | CV |  |
| `captain_slump_start` | leadership | regular; player; captain, fit, in the side; lost 3+ in a row | trust +4, morale, arc flag, slow-start risk, run of games, rest | Rework | PR | "His spot's safe" (start_backing) goes to the ledger. |
| `captain_slump_mid` | leadership | regular; player; captain, fit; after cs_start (3-8 wks) | morale, arc flag, promised game, trust +2, culture | Keep | PR | Reads the ledger. |
| `captain_slump_good` | leadership | regular; player; captain, fit, flag cs_good; after cs_start (5-12 wks) | morale, trust +3, culture | Keep |  |  |
| `captain_slump_flat` | leadership | regular; player; captain, fit, no flag cs_good; after cs_start (5-12 wks) | trust +2, morale, promised game, rest | Keep |  |  |
| `captain_contract_start` | leadership | regular; player; captain, fit, ≤1 yr left | trust -2..+3, arc flag, morale, price open | Rework | CV TM | List manager pitches; temperament shapes his reply. |
| `captain_contract_wait` | leadership | regular; player; captain, fit; after cc_start (3-20 wks) | early extension, morale, trust -2..+2 | Rework | PR RA | "Say it's in hand" is a public promise to the group, untracked today; breaking it costs Respect. |
| `captain_contract_signed` | leadership | regular; player; captain, fit, 2+ yrs left; after cc_start (4-30 wks) | morale, trust +3, culture | Keep |  |  |
| `captain_contract_open` | leadership | regular; player; captain, fit, ≤1 yr left; after cc_start (4-30 wks) | price open, morale, early extension | Keep |  |  |
| `captain_succession_start` | leadership | regular; player; captain, fit, 34+ yrs; has vice | trust -1..+4, morale, arc flag, culture | Rework | BD PR FX | Captain and vice as allies or rivals; "armband's his as long as he wants" is a promise. |
| `captain_succession_next` | leadership | regular; player; captain, fit; has vice; after su_start (8-20 wks) | captaincy swap, morale | Rework | BD OP RA | Taking the armband is a permanent mark on the old captain; his mates react. |
| `finals_last_season` | leadership | finals; player; last season, 200+ games, fit, in the side; finals wk ≤4 | morale, loss sting, trust +3..+6, arc flag | Keep |  |  |
| `finals_second_chance` | leadership | finals; player; captain; finals wk 3, lost last final | development, morale, development forgone, captain decides | Keep |  |  |
| `finals_captain_last_word` | leadership | finals; player; captain, fit, in the side; finals wk ≤4 | trust -4..+8, captain decides, morale | Keep |  |  |
| `gf_last_game` | leadership | finals; player; captain, last season, fit, in the side; finals wk 5 | morale, trust +2..+6, loss sting | Keep |  |  |
| `finals_knocked_out` | leadership | season_end; club; eliminated, not in a prelim | culture, morale | Keep |  |  |
| `gf_runners_up` | leadership | season_end; club; runners-up | culture, morale | Keep |  |  |
| `media_in_the_papers` | media | regular; player; fit, in the side, 3+ games of form | rest, morale, trust -6..+10, arc flag, promised game | Rework | PR OP RA | Keeping him in is a promise; dropping him because the papers pushed is a long-tail mark and costs Respect. |
| `media_radio_spray` | media | regular; club; lost 2+ in a row | morale, board | Keep |  |  |
| `media_newspaper_column` | media | regular; player; fit, 100+ games | morale, trust -3..+4, board, culture | Rework | TM | Fires for mercurial and showman types; choice lands differently by temperament. |
| `media_young_feature` | media | regular; player; fit, ≤22 yrs, 5+ games | morale, board, slow-start risk, development | Keep |  |  |
| `media_team_leak` | media | regular; club | morale, board, culture | Rework | CV FX | Make the leak a person: a council member or player with low loyalty; finding him is the intrigue. |
| `media_cameras_in_rooms` | media | regular; club; won 3+ in a row | board, morale, culture | Keep |  |  |
| `media_papers_fronts_group` | media | regular; player; fit; after backed_in_papers (3-15 wks) | trust -2..+4, captain decides, morale | Keep |  |  |
| `media_papers_again` | media | regular; player; fit, starting, second role, poor form | trust -4..+4, culture, role trial | Keep |  |  |
| `media_trial_worked` | media | regular; player; fit; scripted | morale, development forgone | Keep |  | Scripted result card. |
| `media_trial_not_yet` | media | regular; player; fit; scripted | trust +2, morale | Keep |  | Scripted result card. |
| `gf_week` | media | finals; club; finals wk 5 | morale, heavy legs, fresh legs, board | Keep |  |  |
| `media_papers_finish` | media | pre-season; club; scripted | board, morale, culture, words on record, arc flag | Rework | PR RA | on_record (coach_word) moves into the unified ledger as a public promise. |
| `media_papers_pressure` | media | pre-season; club; scripted | board, morale, words on record, arc flag | Rework | PR RA | Same: public promise in the ledger. |
| `media_papers_breakout` | media | pre-season; player; fit; scripted | morale, trust -3..+5, culture, run of games | Rework | PR | start_backing to the ledger. |
| `media_papers_reckoning` | media | regular; club; behind your words; after talked_up (6-22 wks) | morale, board | Rework | PR RA | Reads the public promise from the ledger; a missed claim costs Respect. |
| `finals_prelim_week` | media | finals; club; finals wk 4 | culture, morale, slow-start risk | Keep |  |  |
| `finals_written_off` | media | finals; club; finals wk ≤4, underdog | morale, slow-start risk, culture, loss sting | Keep |  |  |
| `finals_one_week_short` | media | season_end; club; lost a prelim | morale, culture | Rework | RA FX | "Nobody's spot is safe" builds Authority and unsettles the senior group. |
| `community_hospital_visit` | community | regular; club | morale, board, development forgone, development | Keep |  |  |
| `community_country_clinic` | community | regular; player; fit, 50+ games | board, morale, heavy legs | Keep |  |  |
| `community_foundation_dinner` | community | regular; club | board, morale | Keep |  |  |
| `community_junior_club_fire` | community | regular; player; fit; private | morale, trust +5, heavy legs, fresh legs | Keep |  |  |
| `community_school_visit` | community | regular; player; fit, ≤24 yrs | morale, board, slow-start risk, culture | Retire |  | Same send-a-player-to-an-appearance shape as country clinic and cheer squad. |
| `finals_club_greats` | community | finals; club; finals wk ≤4 | morale, board, slow-start risk, culture | Keep |  |  |
| `gf_night_before` | community | finals; club; finals wk 5 | morale, culture, slow-start risk, fresh legs | Keep |  |  |
| `rivals_coach_barb` | rivals | regular; club | morale, board | Keep |  |  |
| `rivals_spy_at_training` | rivals | regular; club | development, board, morale, development forgone | Keep |  |  |
| `rivals_mouthing_off` | rivals | regular; club | morale, heavy legs, culture, slow-start risk | Rework | BD | Name their player and ours: a cross-club rivalry (often former teammates). |
| `gf_the_opponent` | rivals | finals; club; finals wk 5 | morale, slow-start risk, loss sting, development | Keep |  |  |
| `board_wants_answers` | board | regular; club; every third loss in a row | promise a win, board, culture | Rework | PR RA | promise_win goes to the ledger. |
| `board_president_lunch` | board | regular; club; board ≤55 | board, development forgone, development | Keep |  |  |
| `board_sponsor_shoot` | board | regular; player; fit, OVR 75+ | board, heavy legs, fresh legs | Keep |  |  |
| `board_billboards` | board | regular; club; won 4+ in a row | board, morale, slow-start risk, culture | Keep |  |  |
| `board_savings` | board | regular; club; board ≤45 | board, heavy legs, culture | Rework | CV | Cutting recovery staff costs the high performance head's loyalty. |
| `board_injury_list` | board | regular; club; ≤36 fit | board, culture | Rework | CV | Backing the medical staff is backing a council member. |
| `members_open_training` | members | regular; club | board, morale, development forgone, development | Keep |  |  |
| `members_signing_session` | members | regular; club | board, slow-start risk, fresh legs | Keep |  |  |
| `members_forum` | members | regular; club; lost 3+ in a row | board, culture, development forgone | Keep |  |  |
| `members_cheer_squad` | members | regular; player; fit, ≤25 yrs | board, morale, development forgone, development | Keep |  |  |
| `members_finals_tickets` | members | finals; club | board, development forgone, development | Keep |  |  |
| `members_interstate_trip` | members | regular; club | board, slow-start risk, fresh legs | Keep |  |  |
| `finals_in` | members | regular; club; finals in | morale, slow-start risk, development | Keep |  |  |
| `gf_milestone` | members | finals; player; milestone 100+, fit, in the side; finals wk 5 | morale, trust +4, culture | Keep |  |  |
| `finals_drought_over` | members | finals; club; finals wk 1, 3+ yrs since a final | morale, culture, slow-start risk, development | Keep |  |  |
| `gf_premiers` | members | season_end; club; premiers | morale, culture, running | Keep |  |  |
| `bond_away_camp` | bonding | bonding; club | culture, morale | Rework | BD | The camp is where new mates are made: seed one or two bonds. |
| `bond_talent_quest` | bonding | bonding; club | morale, culture | Keep |  |  |
| `bond_community_week` | bonding | bonding; club | board, culture, morale | Keep |  |  |
| `bond_beach_day` | bonding | bonding; club | morale, culture, plays sore | Keep |  |  |
| `bond_cultural_day` | bonding | bonding; club; Indigenous player | culture, trust +4 (group), board | Keep |  | Group trust becomes a group opinion modifier. |
| `bond_leadership_workshop` | bonding | bonding; club | culture, trust +4 (leaders), morale | Rework | FX RA | Handing the leaders the keys is a faction move; sitting in builds Authority. |
| `bond_families_day` | bonding | bonding; club | morale, culture, board | Keep |  |  |
| `pre_leaders_vote` | bonding | bonding; club; has vice | culture, morale | Rework | FX RA | Overruling the leaders' vote builds Authority and costs the leaders' opinion. |
| `pre_sim_heated` | bonding | bonding; club | culture, morale | Retire |  | Duplicate of training_match_sim_heated; fold it in with a bonding-phase variant. |
| `intl_homesick` | international | regular; player; first season, fit, international; rd 7-16; private | morale, trust +3..+8, heavy legs, board, rest | Rework | BD TM | Host family and mates as bonds; the template for the 14 club homesick cards. |
| `intl_learning_the_game` | international | regular; player; first season, fit, international | development, heavy legs, rest, trust +5, run of games | Rework | PR CV | start_backing to the ledger; the line coach pitches the vision session. |
| `intl_first_game` | international | regular; player; 1 game, ≤2 seasons listed, fit, international | morale, board, heavy legs, fresh legs | Keep |  |  |
| `intl_first_goal` | international | regular; player; 1 goal, ≤3 seasons listed, fit, international | morale, slow-start risk, development | Keep |  |  |
| `intl_first_summer` | international | regular; player; first season, fit, international; rd 20-24; private | development, morale, trust +5, development forgone | Keep |  |  |
| `intl_irish_county_call` | international | regular; player; Ireland, 2+ seasons listed, fit; rd 8-16; private | morale, trust -8..+8, rest, heavy legs, board | Keep |  |  |
| `intl_irish_torn` | international | regular; player; Ireland, 2+ seasons listed, ≤1 yr left, can extend, fit; rd 10+; private | early extension, trust +6, morale, board | Rework | TM CV | Clubman vs mercenary; list manager pitches. |
| `intl_usa_visit` | international | regular; player; USA, ≤2 seasons listed, 1+ games, fit; private | morale, trust +4, slow-start risk, culture | Keep |  |  |
| `intl_nz_rugby_offer` | international | regular; player; NZ, 2+ seasons listed, ≤1 yr left, can extend, fit; private | early extension, trust -6..+6, morale, board | Rework | TM CV | Fires more for mercenary players; list manager pitches. |
| `intl_africa_ambassador` | international | regular; player; Africa, ≤3 seasons listed, 1+ games, fit; private | morale, board, development forgone, development, trust -3 | Keep |  |  |
| `intl_africa_visa` | international | regular; player; Africa, no games yet, in the side, fit; private | morale, trust -3..+8, slow-start risk, rest, culture | Keep |  |  |


### Coach career arcs: 14 arcs, 42 beats

These are the multi-season stories (`data/arcs/coach_arcs.json`), each started by a trigger read from real game state and closed by an ending. Half stand; the half that are about one player or one assistant are where the new systems fit best.

| Arc | Trigger | Beats | Changes today | Verdict | Hooks | Note |
|---|---|---|---|---|---|---|
| The hot seat (`hot_seat`) | board under 40 from round 8 | 4 | board, culture, morale, promise a win | Keep | PR RA | The must-win promise moves to the ledger; holding the line under pressure is a Respect moment. |
| Board feud (`board_feud`) | 2 refusals of the board | 3 | board, culture, morale | Rework | CV FX | Board figures become people with loyalties; the sponsor's favourite is a player whose opinion moves. |
| The protege (`protege`) | 20 or under, potential 80+, 3 hero games | 5 | morale, xp, trust | Rework | BD PR OP | "Untouchable" is a promise; the protege's bond with a senior mentor and his opinion of you carry the arc. |
| One year too long (`one_year_too_long`) | 31+, 150+ games | 4 | morale, trust, culture, promised game | Rework | PR OP BD | The farewell game is a promise; dropping him is a long-tail mark, and his mates in the side react. |
| The drought (`drought`) | 5+ seasons without a flag | 3 | board, culture, morale | Keep | CV | List manager and high performance head argue all-in against keep building. |
| Star wants out (`star_wants_out`) | top-3 player, morale under 50 | 3 | trust, morale | Rework | TM BD CV | Trigger on temperament and opinion, not morale; his close mates may follow; list manager pitches. |
| Media darling (`media_darling`) | 3 statements, 3 hero games | 3 | board, culture, morale, trust | Keep |  |  |
| Rivalry (`rivalry`) | a rival club | 3 | board, culture, morale | Keep |  |  |
| Family club (`family_club`) | a father-son player arrives | 2 | culture, morale | Rework | BD | Father and son as a family bond the later cards can read. |
| Legacy (`legacy`) | 10 seasons, 250 games at the club | 2 | board, morale, culture | Rework | CV RA | The successor comes from the council; how you hand over sets your standing. |
| The way back (`way_back`) | after a sacking | 3 | board, culture, morale | Keep |  |  |
| Poached (`poached`) | 2 top-4 finishes | 3 | board, morale, trust | Keep | RA | Telling the captain the truth is a Respect moment. |
| Reunion (`reunion`) | old club, anniversary | 2 | board, culture, morale | Keep |  |  |
| The assistant (`assistant`) | board under 50, reputation 55+ | 2 | board, culture | Rework | CV FX | This is council loyalty already: an assistant lunching with the chairman. Make it the first council-politics arc and widen it to any of the 8 seats. |


### Club decks: 552 cards in 22 decks

Every club has 23 to 26 cards of its own (the Brisbane Bears and Fitzroy have decks for history careers). 507 of them only move club levers (board, culture, morale, development, odds). The heritage, rituals, grounds and supporters they carry are exactly what a club deck is for, so most stand. The 103 to rework fall into nine families; each family should be built once as a shared mechanic, with each club keeping its own words as text variants.

| Family | Cards | Verdict | Hooks | What changes |
|---|---|---|---|---|
| Homesick and go-home | 14 | Rework | BD TM PR | One shared go-home mechanic: family and mates back home as bonds, homesickness from temperament and seasons away, "fly the family up" as a tracked promise. |
| Pick the kid from the reserves | 16 | Rework | PR BD | "Tell him he's next", "send him down with a promise" and "promise him senior games" are promises nothing tracks. Move them to the ledger; the player he pushes out becomes a rival. |
| Nights out and discipline | 20 | Rework | RA FX | Public fines build Authority, in-house handling builds Respect, and the leaders react. A card that names players names only generated players, never a real-named player in an off-field incident. |
| Father-son and family names | 11 | Rework | BD | A champion's son arrives with a family bond (to his father, to a brother on the list from `player_relations.csv`). |
| Contracts, poaching and the last deal | 11 | Rework | TM CV PR | Temperament decides who tests the market and who takes unders; the list manager pitches; a star's mates may follow him out. |
| Assistants, legends and the coach in waiting | 9 | Rework | CV FX | Council politics already: an assistant wanted interstate, a legend wanting a role, a coach in waiting. Wire them to council seats and loyalty. |
| Captaincy and honours | 8 | Rework | BD FX OP | Two named players compete for an armband, a number or a speech; the loser's opinion and his allies' reaction are the point. |
| Tanking and the list call | 8 | Rework | CV RA | The list manager wants the kids played, the board and senior players want wins: a council split in signed voices. |
| Public promises to board and members | 6 | Rework | PR RA | "Promise finals" has no ledger today; move it in as a public promise with a Respect cost when missed. |
| Staff disputes and conditions | 41 | Keep | CV | The text already pits the physio, fitness staff or a line coach against someone (heat, travel, a tough deck). Give each side its council member's signed voice; nothing else changes. |
| Club heritage, rituals and supporters | 408 | Keep |  | Stands as written. |

The card-by-card family for every club card is in the CSV.


### Real-history year events: 45 cards

The year events (`data/legacy/year_events.json`) are real league moments from 1990 to 2026, each a club-level coach's call, and none names a person. Keep all 45. Eight are hard line against backing the players, and should also move Respect or Authority: `year_eagles_drug_culture`, `year_collingwood_betting`, `year_crows_camp`, `year_white_powder`, `year_slur_bans`, `year_costume_party`, `year_pay_standoff` and `year_bears_owner_collapse`. Their real penalties and the Controversies switch stay as they are.


## Gaps: new dilemmas the overhaul needs

About 40 new cards, in eight families, would give each new system its own reason to come up. Today a card can only be triggered by a player's facts or the club's results, so every one of these needs a new trigger the engine can read (an opinion band, a temperament, a bond, a promise coming due, a Respect or Authority threshold, a council member's loyalty, a faction's mood). Each one stays a once-in-a-while moment with a real trade-off, not a weekly check-in.

| Family | New dilemma | Trigger | The choice | Systems |
|---|---|---|---|---|
| Bonds | His mate wants to know why | You drop a player whose close mate is in the side | Explain it to the mate, back the dropped player publicly, or say it's your call | BD OP RA |
| Bonds | Is he next? | You trade or delist a player with a close mate on the list | Reassure the mate (a promise), let him go too, or say nothing | BD PR |
| Bonds | One spot, two rivals | Two bitter rivals compete for one spot in the same line | Pick one, split the games, or room them together | BD OP |
| Bonds | The mentor asks for the kid | A mentor's protege is in form and out of the side | Pick the kid (a promise to the mentor), make him wait, or let the mentor tell him | BD PR |
| Bonds | The kid takes the mentor's spot | Selecting a protege means dropping his mentor | Pick the kid, keep the veteran, or play both out of position | BD OP |
| Bonds | Brothers on the list | One of two brothers is dropped or offered a trade | Keep them together, split them, or let the family decide | BD OP |
| Bonds | Old teammates this week | A former teammate or a cross-club rival plays us | Give him the job on his old mate, keep the plan, or pin up what was said | BD |
| Bonds | He's put his mate up for leaders | A leadership ally nominates his close mate for the group | Back the nomination, open a vote, or pick the group yourself | BD FX RA |
| Temperament | Hearing out the other club | A mercenary player in his last year after a big game | Open talks now, hold your offer, or call his manager | TM CV |
| Temperament | He'll take less to stay | A clubman out of contract while the list is tight | Take the discount, pay him his worth, or let the list manager decide | TM CV OP |
| Temperament | He won't come off | A competitor told he will be rested or managed | Rest him anyway, let him play, or let high performance decide | TM CV RA |
| Temperament | He's sulking about the move | A mercurial player moved out of his position | Move him back, hold firm, or promise a trial | TM PR |
| Temperament | He's gone at an assistant | A fiery player clashes with a line coach on the bench | Back the coach, back the player, or sit them down together | TM CV RA |
| Temperament | He wants the group to train harder | A professional calls out teammates' standards | Back him in front of the group, have a quiet word, or leave it to the captain | TM FX |
| Temperament | He wants the armband | A leader with no leadership role and a high opinion of you | Put him in the group, tell him to wait, or tell him no | TM PR |
| Temperament | Nobody noticed | A quiet achiever left out of the best-and-fairest top ten or the group | Tell him you noticed, put him forward, or say nothing | TM OP |
| Ambition | He wants the midfield | A player whose ambition is a bigger role | Promise a run there, explain his role, or say no | PR TM |
| Ambition | He wants to win now | A star with a premiership ambition at a club out of contention | Promise a push next year, list him for trade, or hold him to his deal | PR TM CV |
| Ambition | The milestone and the form | A player one or two games short of a milestone, out of form | Pick him for the milestone, drop him, or promise the game later | PR OP |
| Promises | You said he'd play | A promise you made is broken at selection | Apologise, make a new promise, or say it was your call | PR OP RA |
| Promises | You kept your word | A long promise (a run, a role, a deal) kept to the end | Say so in front of the group, or keep it between you | PR RA |
| Promises | Your words to the board | A public promise (finals, a win) comes due | Own it, argue the context, or blame the list | PR RA CV |
| Respect and Authority | The room is going | Respect low and falling | Front the group, give the leaders more say, or tighten the rules | RA FX |
| Respect and Authority | Nobody speaks up any more | Authority high, Respect low | Open the floor, keep the line, or ask the captain what's wrong | RA FX |
| Respect and Authority | They're testing you | Respect high, Authority low, and a rule broken | Make an example, let it go, or leave it to the leaders | RA FX |
| Respect and Authority | The leaders back you | Respect high after a losing run | Accept their backing, or tell them it's on you | RA FX |
| Council | The council splits | Two council members disagree on a selection, load or list call | Back one, back the other, or make your own call | CV RA |
| Council | He wants a bigger job | A council member with high ambition and loyalty | Give him more, promise it later, or keep his seat as it is | CV PR |
| Council | He's been talking to the board | A council member with low loyalty and a falling board score | Confront him, sideline him, or win him back | CV FX |
| Council | The physio says no, the list manager says yes | A star is a medical risk before a game that matters for the list | Rest him, play him, or let the player decide | CV TM |
| Council | A rival wants your man | Another club approaches a council member | Match their offer, let him go, or promote from below | CV |
| Factions | Seniors against the kids | The senior group and the young group pull against each other | Side with the seniors, side with the kids, or bring the captain in | FX RA |
| Factions | A clique has formed | Three or more players with close bonds (a draft year, a state, a line) | Break them up in training, use them, or leave them be | FX BD |
| Factions | The leaders' ultimatum | A faction with low opinion of you and a grievance | Give them what they ask, stand firm, or split them | FX RA OP |
| Factions | The group backs his deal | A faction backs a teammate's contract demand | Pay him, stand firm, or let the list manager handle it | FX CV TM |
| Scars | Years later | A player with a permanent mark is now captain, at a rival club or in the media | Make peace, say nothing, or say you'd do it again | OP BD |
| Scars | He never forgot | A player with a scar comes out of contract | Offer more to win him back, offer the standard deal, or let him go | OP TM CV |
| Scars | Cross-club grudge match | This week's opponent has a sacked or poached former council member, or a scarred ex-player | Make it personal, play it down, or reach out before the game | OP BD CV |
| Council | Locker-room lobbying | A senior star or council member pushes you to play his mate or drop a positional rival | Do as he asks, refuse, or put it to the selection panel | BD CV RA |
| Your own deck | Your Forge player's mates | Your Club Forge prospect forms or loses a close bond | As for any bond card | BD |

The last row is there because every mode hosts the Club Forge: the bond, temperament and promise cards must be able to fire for a Forge prospect and a Forge club like any other player and club.

Rival clubs need these systems resolved without cards. A rival's coach should make the same kinds of choices by rule (keep or break a promise, back or drop a player with mates) so that opinions, bonds and Respect/Authority move at every club, and a rival should only react to what it could know.


## Recommended order

Do the rewrites in the same order the systems arrive, so no card is written against a system that does not exist yet.

- **With Phase 1 (Opinion, Promises, Bonds, Temperament, Respect/Authority), engine only:** the Opinion migration turns every `trust` op into a decaying modifier with no card edit, and the six promise ops become one ledger. Add an optional scar field to cards, and set it on the 8 cards that should leave long-tail marks (`family_baby_due`, `family_dad_in_hospital`, `finals_fitness_test`, `gf_racing_the_clock`, `selection_finals_experience`, `captain_succession_next`, `media_in_the_papers`, `training_backed_kid_struggling`).
- **First card pass, right after Phase 1:** the promise cluster (about 30 weekly cards plus the 22 club pick-the-kid and public-promise cards), and the 5 retirements (2 of them folded into other cards). This is the pass where players see the new systems pay off.
- **Second pass, bonds and temperament:** name the two players on the 8 bond-seeding cards (match sim, late to the meeting, mentor cards, away camp, mouthing off), merge the 14 homesick cards into one, and write the 16 new bond and temperament dilemmas.
- **Third pass, with the Phase 3 council:** give signed voices to the 41 staff-dispute club cards and about 20 weekly cards, rework the 9 assistant and legend cards and the 8 tanking cards, and write the 5 council dilemmas.
- **Fourth pass, with factions and the Club Politics screen:** the leaders and discipline cards (about 30), the Respect/Authority threshold cards and the faction dilemmas.
- **Last:** the scar callbacks, which need a season or two of saved marks before they can fire.

Every new trigger needs an old-save default (no temperament, no bonds, neutral standing) so old careers keep dealing cards. Every pass is a play-touching change, so each needs the paired `tools/balance.sh match 1000` check.

The 5 retired cards can be deleted outright: none of them sets an arc flag, so no saved career can be mid-story on one.

