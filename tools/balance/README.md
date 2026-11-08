# Local balance harness

Answers "is the match engine inside real AFL numbers, and did my change move it?"
in a minute or two on this PC, without CI.

```bash
GODOT=<godot console exe> tools/balance.sh match 1000                                    # one arm
GODOT=<godot console exe> tools/balance.sh match 1000 --a-root ../main-checkout --b ""   # main vs this branch
GODOT=<godot console exe> tools/balance.sh match 1000 --a "--weather perfect" --b "--weather wet"
```

- **Workers.** `balance_worker.gd` (+ `balance_body.gd`) plays a seed slice headless and writes one JSON
  line per match. The script splits N over `JOBS` parallel Godot processes (default cores - 2), each with
  its own `APPDATA`.
- **Pairing.** Seed i is always the same two real 2026 lists (every pairing of 18 clubs comes round, home
  side alternating) on match seed 500000 + i, so arm A and arm B play identical matches and the delta's
  standard error is small. A change is real when |B - A| > 2 se (the `sig` column).
- **Arm args.** `--weather perfect|wet|windy|hot`,
  `--tune KEY=V,...` (sets `MatchSim.tune`, read by `_tv`: size a constant before you fix it).
- **Generated lists** (`--lists generated`, row 104): every club's list is generated players instead of the
  real ones, to screen a change to generation in matches (`--a-root <main checkout> --a "--lists generated"
  --b "--lists generated"`). Classes 2027 on are generated on the game's data, grown five seasons, and each real
  player's place goes to the next generated player of his position, re-rated to his OVR (the in-career
  re-anchor). Every worker builds the same league; ~10 s more per worker.
- **Match setup** (`--setup league|coached`, fatigue parity, T3.F-defects): `league` plays both sides
  as a career's background match (rival coaches pick their plans, Steady-plan rotations each quarter);
  `coached` makes side `i % 2` your club in a coached match you skip through (assistant calls, every
  moment on its default answer, rotations set before each quarter as MatchScene sets them). Pair them
  (`--a "--setup league" --b "--setup coached"`) to see whether your side is treated as an AI club is.
  The report's Legs section gives each side's mean energy on the ground and how many are under 40 at
  each siren, interchanges and exertion: home against away, coached against rival, and for a paired run
  the coached side and its rival each against the same side on the same seed in A. Use a multiple of
  306 matches (`918`) so every club is home and away equally often.
- **Main against the branch** (every A/B of a change): `--a-root <checkout of origin/main> --b ""` plays
  arm A from that other checkout and arm B from this one, on the same seeds. There are no feature switches:
  a change is in the game once merged, so the only A/B is main against the branch. Each worker log starts with
  `project: <path>`, so `head -1 <run>/a_0.log` proves which checkout arm A played.
- **Report.** `balance_report.py` prints a markdown page (also saved to `<run>/report.md`): each stat per
  team-match against `afl_team_rates.json` (IN = inside the 18 clubs' lowest..highest, NEAR = within
  mean +-2 sd, OUT), plus margins, 60+/100+ blowouts, home win share against docs/LEAGUE_BALANCE.md.
  A Shots section gives set shots and general-play shots a team, the set-shot share against the real
  55%, and goals per set shot by distance (0-10 ... 50+ m) against Champion Data 2021-25
  (docs/research/SET_SHOT_EVIDENCE.md), from `MatchSim.shot_log`; the pocket set shot has its own row
  against the wide-angle cells, and the set-shot share is also given over scoring shots, because the
  sim logs a general-play shot only when it scores.
  A "Change B against A" table gives B/A-1 with its se for the contest stats (tackles, clangers,
  ground-ball gets, contested possessions, one-percenters, marks, stoppages counted from ball-up and
  throw-in events) and accuracy in points. When B plays a weather and A a perfect day
  (`--a "--weather perfect" --b "--weather wet|windy|hot"`, rows 120 and 61; A must be the perfect day,
  as the real changes are against one) the table widens to every stat the reference holds (marks inside
  50 and rebound 50s among them), with the real change for that condition, its se and an IN/NEAR/OUT
  mark (IN: within 2 combined se of the real change; NEAR: within 4), plus rows for accuracy (overall,
  set shots and general play), the last quarter's share of the scoring and the breeze (how far the
  margin swings each quarter to the end kicking with it, from the quarter margins' extra spread
  against A). Real: `afl_weather_rates.json`
  (AFL Tables 2016-19 and 2021-25 with Open-Meteo's hourly weather at the ground in the match window;
  built by `build_weather_rates.py`, which first checks its method against ABC's 2022-25 wet table;
  `--offline` rebuilds from its cache, `--explore` prints that check at several rain cut-offs).
  How often each condition comes up is fitted to the same file's `share_of_outdoor`:
  `weather_fixture.gd` dumps where and when the game plays 20 seasons of matches, and
  `weather_cutoffs.py` fits `Weather.gd`'s WET_K, WIND_CUT and HOT_CUT to those shares.
  It also prints intercepts a game per player by his listed position (DEF, MID, FWD, RUCK; the
  definition of tools/audit/intercept_impl.gd) against Champion Data 2025, with B-A and se when paired.
  It also prints key forward v key defender contests per duel per match (row 94), from each match's
  `duels` rows ([contests, marks, most v one defender, MatchNotes.duel_verdict]): mean, median, share on
  6+ contests, share with a full-time line (4+), forward marks and the beat / even / held split, and
  for a paired run contests per duel B-A with its se.
  It also prints spoils a team a game by zone, from the spoiling side's end (T2.29, TODO row 11):
  defensive 50 (split into forward-50 entries and goal-square packs, and general play), between the
  arcs, and its own forward 50, from `MatchSim.spoil_log` (bookkeeping, no dice), plus spoils a game per
  player by listed position. Real: `afl_spoil_zones.json` (Champion Data 2026 via Wheelo, built by
  `build_spoil_zones.py`); the total and the by-position rates are measured, the zone split is an
  estimate, because Champion Data does not publish where a spoil happens.
  A Rucks section (T2.31) sets team hit-outs, hit-outs to advantage and the number-one ruck's hit-outs,
  to-advantage rate, share of his side's hit-outs and hit-outs per ruck contest against Champion Data
  2025 and 2026 (`afl_ruck_rates.json`, built by `build_ruck_rates.py` from docs/research/wheelo/);
  the club spread (each club's average over the run against the real 18 clubs' lowest..highest, sd and
  the correlation with its real figure); and the per-match duel spread (team hit-out margin 10+/20+/30+,
  number-one rucks 10+/20+ apart, one side winning 60/65/70%+ of the hit-outs), which has no real
  per-match reference yet. Each team line carries `club` and `ruck1` [hit-outs, to advantage,
  ruck contests, ruck rating] for this.
- **Runs** land in `.balance/<timestamp>/` (git-ignored, `.gdignore`d).

## When to use it
Any balance-gated TODO row, any change to MatchSim rates or constants, and any feature that touches play:
run main vs the branch before opening the PR and paste the report table into the PR body.
Use `tools/audit/` for deeper single-question audits (season, draft, dynasty); this harness is the quick
match-level screen.

## Improving it
Extend it rather than writing a one-off probe: add a mode to `balance.sh` (e.g. `season`) with its own
worker body, add stats to `MAP` in the report when afl_team_rates.json gains them, and add new real
references beside the margins line with their source doc.
