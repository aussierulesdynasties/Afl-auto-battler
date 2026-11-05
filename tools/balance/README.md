# Local balance harness

Answers "is the match engine inside real AFL numbers, and did my change move it?"
in a minute or two on this PC, without CI.

```bash
GODOT=<godot console exe> tools/balance.sh match 1000                          # one arm
GODOT=<godot console exe> tools/balance.sh match 1000 --b "--on clanger_cause" # base vs switch on
GODOT=<godot console exe> tools/balance.sh match 1000 --a "--weather wet" --b "--weather perfect"
```

- **Workers.** `balance_worker.gd` (+ `balance_body.gd`) plays a seed slice headless and writes one JSON
  line per match. The script splits N over `JOBS` parallel Godot processes (default cores - 2), each with
  its own `APPDATA`.
- **Pairing.** Seed i is always the same two real 2026 lists (every pairing of 18 clubs comes round, home
  side alternating) on match seed 500000 + i, so arm A and arm B play identical matches and the delta's
  standard error is small. A change is real when |B - A| > 2 se (the `sig` column).
- **Arm args.** `--on a,b`, `--off c` (Features switches), `--weather perfect|wet|windy|hot`,
  `--tune KEY=V,...` (sets `MatchSim.tune`, read by `_tv`: size a constant before you fix it).
- **A change with no switch** (a retuned constant): `--a-root <checkout of origin/main> --b ""` plays arm A
  from that other checkout and arm B from this one, on the same seeds. Each worker log starts with
  `project: <path>`, so `head -1 <run>/a_0.log` proves which checkout arm A played.
- **Report.** `balance_report.py` prints a markdown page (also saved to `<run>/report.md`): each stat per
  team-match against `afl_team_rates.json` (IN = inside the 18 clubs' lowest..highest, NEAR = within
  mean +-2 sd, OUT), plus margins, 60+/100+ blowouts, home win share against docs/LEAGUE_BALANCE.md.
  A Shots section gives set shots and general-play shots a team, the set-shot share against the real
  55%, and goals per set shot by distance (0-10 ... 50+ m) against Champion Data 2021-25
  (docs/research/SET_SHOT_EVIDENCE.md), from `MatchSim.shot_log`; the pocket set shot has its own row
  against the wide-angle cells, and the set-shot share is also given over scoring shots, because the
  sim logs a general-play shot only when it scores.
  It also prints intercepts a game per player by his listed position (DEF, MID, FWD, RUCK; the
  definition of tools/audit/intercept_impl.gd) against Champion Data 2025, with B-A and se when paired.
- **Runs** land in `.balance/<timestamp>/` (git-ignored, `.gdignore`d).

## When to use it
Any balance-gated TODO row, any change to MatchSim rates or constants, and any new feature switch that
touches play: run base vs switch before opening the PR and paste the report table into the PR body.
Use `tools/audit/` for deeper single-question audits (season, draft, dynasty); this harness is the quick
match-level screen.

## Improving it
Extend it rather than writing a one-off probe: add a mode to `balance.sh` (e.g. `season`) with its own
worker body, add stats to `MAP` in the report when afl_team_rates.json gains them, and add new real
references beside the margins line with their source doc.
