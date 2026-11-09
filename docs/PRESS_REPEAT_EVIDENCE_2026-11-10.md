# Press questions and coaching notes over long saves (audit 19/60), 2026-11-10

TODO section D, 19/60: how often press-conference questions and full-time coaching notes repeat over a long save,
and how many press conferences a season.

## Method

- `tools/audit/press_repeat_impl.gd`, run on GitHub (audit.yml, runs 42692884938, 42692901321, 42692916473,
  42692930882, 42692943913, 42692959061, branch `audit/press-repeat-19`). 12 seeded careers (1901-1912), 12 seasons
  each, four each at Melbourne, Fremantle and St Kilda, from the clubs' real lists: 144 seasons, 3,294 of your
  matches, 2,056 press conferences, 3,149 coaching notes.
- The autopilot answers every event card and press question with a seeded random option and drafts with the AI's
  pick. It coaches badly, so the board sacked it in 7 of 12 careers. The audit clears a sacking on the spot and counts
  it (26 reprieves in all), so every career stays 12 seasons at one club. Measurement only: no game rule changes.
- A press question is its data id (`qid`, `MediaConference._q`: the written question before names and numbers fill
  it). A coaching note is the line the full-time screen shows under "Coaching notes", built exactly as
  `MatchScene` builds it (the first two of `CoachReport.glance` notes, less what the story and How it went said).
  Notes have no data id: each is named by its text, and the rule in `CoachReport._second_half_keys` that writes it.
- "Gap" is counted in your club's matches (finals included) since the career began, so 23 is about a season.
- Tables: `python tools/audit/press_repeat_report.py run_*/audit.log`.

## Pressers a season

About **14 a season** (14.3 mean; careers 13.7-14.9; seasons 13.7-15.9), in about 23 matches: a press conference
after **62%** of your matches. Steady across all 12 seasons; no drift as a save gets older.

## Press questions

| Season | Pressers | Distinct questions / asked | Repeats in the season |
| --- | --- | --- | --- |
| 1 | 14.2 | 10.4 / 14.2 | 3.8 |
| 2 | 13.7 | 10.7 / 13.7 | 3.0 |
| 3 | 14.7 | 11.4 / 14.7 | 3.2 |
| 4 | 13.8 | 10.4 / 13.8 | 3.4 |
| 5 | 13.8 | 9.8 / 13.8 | 3.9 |
| 6 | 13.8 | 10.4 / 13.8 | 3.3 |
| 7 | 14.5 | 10.7 / 14.5 | 3.8 |
| 8 | 14.3 | 10.2 / 14.3 | 4.2 |
| 9 | 14.7 | 10.8 / 14.7 | 3.9 |
| 10 | 13.7 | 10.2 / 13.7 | 3.5 |
| 11 | 15.9 | 11.8 / 15.9 | 4.2 |
| 12 | 14.4 | 11.1 / 14.4 | 3.3 |

(Averages over the 12 careers. A repeat is the same written question asked again in the same season; names and
numbers differ each time.)

- 28 written questions exist in play; a career sees 22-27 of them. Over a whole save the same written question
  comes back with a **median gap of 17 rounds**; 4.9% of repeats come within 6 rounds, 0.6% within 3.
- The top ten ids are 74% of every question asked. Each of them is asked 9-15 times a career, about once a season.

### Repeat offenders, by data id

| Id | Journalist | Per career | Share | Median gap | Shortest | Seasons asked 3+ times (of 144) | Wordings |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `heavy_loss.0` | Gary Haddon | 14.8 | 8.7% | 14 | 5 | 6 | 2 |
| `close_game.shots` | Dev Mehta | 14.8 | 8.6% | 13 | 2 | **15** | **1** |
| `injury.0` | Kev Pollard | 14.4 | 8.4% | 15 | 6 | 0 | 2 |
| `heavy_loss.1` | Gary Haddon | 14.2 | 8.3% | 14 | 6 | 7 | 2 |
| `injury.1` | Kev Pollard | 13.8 | 8.0% | 16 | 5 | 1 | 2 |
| `milestone.0` | Trish Lomax | 12.2 | 7.1% | 18 | 2 | 4 | **1** |
| `big_win.0` | Trish Lomax | 12.0 | 7.0% | 16 | 5 | 5 | 2 |
| `big_win.1` | Trish Lomax | 11.2 | 6.5% | 16 | 7 | 2 | 2 |
| `young_side.0` | Margaret Ashby | 9.7 | 5.6% | 16 | 9 | 0 | 2 |
| `young_side.1` | Margaret Ashby | 9.2 | 5.4% | 16 | 9 | 0 | 2 |
| `heavy_loss.said` | Gary Haddon | 5.0 | 2.9% | **10** | 3 | 4 | 1 |

- **`close_game.shots`** is the worst: one wording for the most common close-game shape, asked three or more times
  in one season in 15 of 144 seasons, twice inside two rounds.
- **`milestone.0`** has one wording and comes twice inside two rounds when two players reach a milestone close
  together.
- **`heavy_loss.said`** (Gary Haddon quoting your "our method's the standard" after a big win) is the shortest-gap
  question: once you make that claim, it is asked after every heavy loss for the rest of that season.
- The single-wording story questions (`blown_lead.0`, `losing_run.0`, `final_loss.0`, `debut.0`, `winning_run.0`,
  `comeback.0`) come 2-4 times a career with median gaps of 22-50 rounds: rare enough not to grate.

## Coaching notes

| Season | Notes shown | Distinct notes |
| --- | --- | --- |
| 1-12 (range of season means) | 20.5-23.9 | 7.5-8.2 |

Only **10 different lines exist**, and every career shows all 10. About 22 notes a season (about one a match);
the same line comes back with a **median gap of 5 rounds**; 36% of repeats come within 3 rounds and 57%
within 6. Back to back (gap 1) happens for every line.

| Note | Rule in `CoachReport._second_half_keys` | Per career | Share | Median gap |
| --- | --- | --- | --- | --- |
| Too many errors. | 7, errors | 52.8 | 20.1% | 4 |
| Our pressure is biting. | 5, pressure (ours) | 40.2 | 15.3% | 5 |
| We are wasting our entries; they are making theirs count. | 8, conversion (theirs) | 39.4 | 15.0% | 4 |
| Their pressure is getting to us. | 5, pressure (theirs) | 36.3 | 13.8% | 4 |
| We are making our entries count; they are wasting theirs. | 8, conversion (ours) | 35.2 | 13.4% | 5 |
| They have had more of the ball going forward. | 4, territory (theirs) | 17.4 | 6.6% | 11 |
| We have had more of the ball going forward. | 4, territory (ours) | 14.3 | 5.5% | 14 |
| They are winning the stoppages. | 3, stoppage (theirs) | 10.5 | 4.0% | 15 |
| We are losing the ruck. | 6, ruck | 8.6 | 3.3% | 16 |
| We are on top at the stoppages. | 3, stoppage (ours) | 7.7 | 2.9% | 23 |

The notes repeat far more than the press questions: each is one fixed sentence per rule (the numbers after the
colon are cut on the full-time screen), and the five most common lines are 78% of all notes.

## What it means

- Press questions: the cadence (about 14 a season, about one in nine by Margaret Ashby) holds steady over 12 seasons,
  and most questions come back about once a season. The repeats a player would notice are the one-wording
  `close_game.shots` and `milestone.0`, and the `heavy_loss.said` quote-back that recurs all season.
  PR #1256 (director's 2026-11-10 instruction) adds a third wording to the six most-asked questions and quotes a
  claim back once.
- Coaching notes: ten fixed lines, the top one every fourth match. The worst offenders are
  "Too many errors." and the two pressure and two conversion lines (rules 5, 7, 8). No change made here.

## Not exercised

- The autopilot answers at random and coaches poorly; a real coach is sacked less and wins more, so he sees more
  big-win and fewer heavy-loss questions. Counts by result type move with that; the wording repeats do not.
- Three clubs (MEL, FRE, STK); Club Forge clubs, expansion clubs and club moves after a sacking are not run.
- Half-time notes and the full report's notes are not counted: only the full-time "Coaching notes" lines.
- Press questions' journalist lead-ins (warm, wary) vary the opening of the question and are not counted.
