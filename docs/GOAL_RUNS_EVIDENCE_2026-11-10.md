# Runs of goals, blowouts and close finishes: sim vs real AFL (audit 29), 2026-11-10

**Report only (director, 2026-11-10): no tuning is proposed or changed. Balance stays his call,
settled only by numbers near real AFL plus his own playtest.**

**Result.** Margins and runs of goals sit close to real AFL: of 27 measures marked against real
data in AI-v-AI play (margins vs 2010-25, runs vs 2023-25, close finishes), 22 are IN, 4 NEAR and
1 OUT (a match with no run of 3+ goals: 0.9% sim vs 0.2% real). Close games reach the late
centre-bounce window as often as real games do, and the bounce call is asked in 87% of them. One
close-finish scene, **after the siren, never plays**: the match's event list puts "End of quarter
4" between the last score and the final siren, and the scene looks for the siren straight after
the score. Skipping that line would make it play in 0.4% of matches.

## Method

- **Real AFL.**
  - Margins: every match on AFL Tables 2010-2025 (3,261, finals included,
    `tools/balance/afl_comebacks.json`) and the 2026 home-and-away season (207 matches,
    `data/raw/fixtures_2026.json`), the references `tools/balance/balance_report.py` uses.
  - Runs of goals and the timed close-finish rows: **new**, every match of 2023-2025 (648, finals
    included) from AFL Tables' scoring progressions, fetched by `tools/balance/afl_goal_runs.py`
    into `tools/balance/afl_goal_runs.json`: the goal order and every score with its time in the
    quarter. A match is kept only when the scores read off the page add up to its final score
    (648 of 648 did). The repo had no real goal-run reference before this.
- **Sim.** `tools/audit/goal_runs_impl.gd` on main at `e67ba17d`, run on GitHub via audit.yml
  (runs 42687528567, 42687538816, 42687549530, 42687562819 ai; 42687575383, 42687587721,
  42687598322, 42687610709 coach; 42692989518 the siren check):
  4 batches of 1,500 per mode (seeds 11-14), random club pairs, weather 4 perfect : 1 wet :
  1 windy : 1 hot. The same fixtures in both modes.
  - `ai`: both clubs coached by the AI and no call cards (the league's simulated matches).
  - `coach`: side 0 is asked every call card and lets each take its default, as a coach who lets
    the card time out; both sides keep the AI's plans. Only here can the call cards fire.
- **A run of goals** is unanswered goals by one side, behinds ignored, carried across quarter
  breaks, as the game's own counter is (`MatchSim._run`, which drives "They have kicked 3 in a
  row").
- **Report:** `python tools/audit/goal_runs_report.py <audit logs>`. IN = within 2 combined
  standard errors of real; NEAR = within 4; OUT beyond (the rule `balance_report.py` uses).
- **Scene triggers, as coded:**
  - After the siren (`BroadcastVignette.pick_kind`): a Q4 set-shot goal or behind, the next event
    "final", the margin 6 or less before the kick. Tested on each match's own event list.
  - Late centre-bounce call (`MatchSim._bounce_moment`): Q4, minute 100+ (the last 70% of the
    quarter), a centre bounce, margin 12 or less, once a match.
  - Close set-shot call (`MatchSim`, set-shot moment): Q4, your set shot, margin 18 or less.
  - Run-of-goals card (`_fire_run_moves`): 3+ unanswered goals against you, once a run.

## AI v AI (6,000 matches)

### Margins

| stat | real 2010-25 | sim | mark | real 2026 H&A | mark |
|---|---|---|---|---|---|
| mean margin | 33.9 | 32.4 | NEAR | 32.2 | IN |
| median margin | 28 | 26 | | 26 | |
| 0-6 | 14.0% | 13.2% | IN | 16.9% | IN |
| 7-12 | 11.0% | 12.4% | IN | 11.1% | IN |
| 13-24 | 19.1% | 21.3% | NEAR | 19.3% | IN |
| 25-39 | 21.5% | 20.1% | IN | 18.4% | IN |
| 40-59 | 17.0% | 17.8% | IN | 18.8% | IN |
| 60-79 | 10.4% | 9.3% | IN | 11.6% | IN |
| 80-99 | 4.5% | 4.2% | IN | 1.9% | NEAR |
| 60+ | 17.2% | 15.2% | NEAR | 15.5% | IN |
| 100+ | 2.3% | 1.7% | IN | 1.9% | IN |
| draw | 0.9% | 1.0% | IN | 1.4% | IN |

Against 2026 alone every margin row is IN except 80-99 (NEAR; 2026 had only 4 such games).
Against 2010-25 the sim runs slightly tight: mean 1.5 points lower, a little more 13-24 and a
little less 60+.

### Runs of goals (real 2023-25, 648 matches)

| stat | real | sim | mark |
|---|---|---|---|
| goals a match (both sides) | 24.4 | 25.2 | NEAR |
| longest run a match | 5.46 | 5.37 | IN |
| match has a run of 3+ | 99.8% | 99.1% | OUT |
| match has a run of 4+ | 85.8% | 86.2% | IN |
| match has a run of 5+ | 61.0% | 61.9% | IN |
| match has a run of 6+ | 40.6% | 38.3% | IN |
| match has a run of 7+ | 24.4% | 22.3% | IN |
| match has a run of 8+ | 14.7% | 13.0% | IN |
| runs of 3+ a match | 3.01 | 3.06 | IN |
| runs of 4+ a match | 1.55 | 1.58 | IN |
| runs of 5+ a match | 0.82 | 0.84 | IN |
| goals a run (mean length) | 2.13 | 2.09 | IN |

The one OUT is a tail of a tail: 1 real match in 648 had no run of three (Wilson 95% interval
99.1-100.0%), 54 sim matches in 6,000. Every other run row is IN.

**Clustering.** The longest run in each match against the same goals put in random order (1.00
would mean goals fall with no momentum): real 1.039, sim 1.014. Real goals cluster a little more
than chance; sim goals barely do. The sim reaches real run lengths mainly because it kicks
slightly more goals, not through momentum streaks. This is a measurement, not a call to change
Momentum (row 78).

### Close finishes

| stat | real | sim | mark |
|---|---|---|---|
| final margin within 6 (real 2010-25) | 14.0% | 13.2% | IN |
| final margin within 12 (real 2010-25) | 25.1% | 25.6% | IN |
| within 12 at 30% into Q4, the sim's minute 100 (real 2023-25, timed) | 28.1% | 27.7% | IN |
| late bounce window: a goal after 30% of Q4 leaves it within 12 (real 2023-25) | 39.7% | 38.2% | IN |
| after-the-siren scene would play | no real equivalent | **0.0%** | |

## Coach v AI (6,000 matches)

Margins and runs read the same as AI v AI (the coach takes every default, so play barely
differs). Marks against real AFL 2010-25 and 2023-25:

| stat | real | sim | mark |
|---|---|---|---|
| mean margin | 33.9 | 32.9 | IN |
| 13-24 | 19.1% | 20.9% | NEAR |
| 60+ | 17.2% | 15.6% | NEAR |
| 100+ | 2.3% | 2.1% | IN |
| goals a match | 24.4 | 25.3 | OUT |
| longest run a match | 5.46 | 5.45 | IN |
| match has a run of 3+ | 99.8% | 99.0% | OUT |
| match has a run of 5+ / 8+ | 61.0% / 14.7% | 63.2% / 13.4% | IN / IN |
| runs of 3+ / 4+ / 5+ a match | 3.01 / 1.55 / 0.82 | 3.07 / 1.59 / 0.86 | IN |
| clustering (longest run vs random order) | 1.041 | 1.023 | |

Every other margin row is IN; full tables come from the report script. Goals a match is OUT here
by 0.9 goals (NEAR in AI v AI, 0.8): the same small excess, past 4 standard errors with 6,000
matches.

### How often each close-finish card and scene comes (sim only)

| stat | share of matches |
|---|---|
| within 12 at minute 100 (real 28.1%) | 28.2% (IN) |
| late bounce window open (real 39.7%) | 38.3% (IN) |
| **late centre-bounce call asked** | **33.4%** |
| of matches where the window opened | 87.0% (of 2,297) |
| of matches within 12 entering minute 100 | 79.8% (of 1,692) |
| close Q4 set-shot call asked (within 18) | 39.2% |
| run-of-goals card asked | 78.1% (1.33 a match, against 1.45 runs of 3+ against you) |
| after-the-siren scene | **0.0%** |

Calls asked a match, all kinds: set shot 2.93, run of goals 1.33, bounce 0.33, hot forward 0.09.

The late bounce call misses 13% of the matches whose window opened: the quarter's two calls and
the 8-chain gap after the last call (`_late_bounce_ready`) can still be spent when the bounce
comes. `_boundary_moment`'s comment says 92% of close finishes get it; this run measures 87% of
open windows and 80% of games within 12 at minute 100 (some of those have no goal after minute
100, so no centre bounce to ask at). The run card answers about 92% of runs of
3+ against you (1.33 of 1.45); the rest fall while a call is pending or inside the gap.

## The after-the-siren scene cannot play

`MatchSim.end_quarter()` logs "End of quarter 4" and then `_emit_full_time()` logs "final", so the
event after the last score of every match is the end-of-quarter line. `MatchScene` hands
`BroadcastVignette.pick_kind` the next event of the pitch's list, which is the sim's list
unfiltered (`PitchView.append_events`), and `pick_kind` requires it to be "final". The unit check
in `tests/test_match_visual.gd` (line 1215) passes a hand-made "final" as the next event, so it
does not catch this. Measured: 0 of 6,000 AI matches and 0 of 6,000 coached matches.

Even with the end-of-quarter line skipped, the trigger is rare: a 5th batch of 1,500 AI matches
(seed 15) gives 6 matches, **0.4%** (Wilson 95% interval 0.2-0.9%). Over a 23-match season a
coach would see it about once every 11 seasons. The trigger needs the very last score of the
match to be a Q4 set shot taken with the margin 6 or less, and the sim does not stop the clock for a kick
after the siren, so "the last score happened to be a close set shot" is all it can catch.

This is a presentation defect, not balance; it is reported here and not fixed in this PR.

## Not exercised

- Finals and extra time: no finals mode, so no extra-time siren.
- A coach who answers the cards: coach mode takes every default (no call for the bounce and the
  run card, take the shot for the set shot). Answered calls change the dice after the card.
- The playtest aid "Centre-bounce scene every match" (off by default).
- Real run counts include finals (about 4% of the 648 matches); the 2026 season's progressions are
  not fetched.
- Whether the scene would read well when it plays: no capture was taken.
