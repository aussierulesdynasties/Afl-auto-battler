# Local balance harness

Answers "is the match engine inside real AFL numbers, and did my change move it?"
in a minute or two on this PC, without CI.

```bash
GODOT=<godot console exe> tools/balance.sh match 1000                                    # one arm
GODOT=<godot console exe> tools/balance.sh match 1000 --a-root ../main-checkout --b ""   # main vs this branch
GODOT=<godot console exe> tools/balance.sh match 1000 --a "--weather wet" --b "--weather perfect"
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
  throw-in events) and accuracy in points, beside the real wet-against-dry change; read the real column
  only when B is the wet arm (row 120).
  It also prints intercepts a game per player by his listed position (DEF, MID, FWD, RUCK; the
  definition of tools/audit/intercept_impl.gd) against Champion Data 2025, with B-A and se when paired.
  It also prints key forward v key defender contests per duel per match (row 94), from each match's
  `duels` rows ([contests, marks, most v one defender, MatchNotes.duel_verdict]): mean, median, share on
  6+ contests, share with a full-time line (4+), forward marks and the beat / even / held split, and
  for a paired run contests per duel B-A with its se.
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
