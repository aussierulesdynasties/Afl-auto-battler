# Former-player coaches: the coaching rate (row 71, T5.Q15)

_2026-11-06. Director's ruling on T5.Q15: lower the rate toward the 60-80% aim._

## The question

What share of the league's coaching jobs (all six jobs at every club: senior
coach, senior assistant, three line coaches, development coach) do former
players of this league hold by 2058? The real 32-season career recorded in
`docs/DESIGN.md` (Coaching Phase 4) reached 102 of 119 jobs (86%). The aim is
60-80%; the target was the middle, about 70%.

## Method

- `tools/audit/coach_rate_impl.gd`: an autopilot career (League Draft, every
  season and off-season with no user management, your club MEL), seeded
  (`career_seed`, `replay_seed` and the draft all = the seed), 32 seasons, so
  the last rollover is into 2058, the DESIGN.md horizon. After each rollover it
  counts the coach records holding a job, those with a `former_player_id`, the
  same for senior coaches, and the `C_P_*` records on file (live or archived).
- Seeds 301-306, the same six for every arm, run on GitHub's runners
  (`audit.yml`, two jobs of three careers per arm, about 2 hours each).
- Arms: the old odds (`BASE_INTEREST` 0.19) and three candidates (0.14, 0.10,
  0.06), each a one-constant commit on a scratch branch. Nothing else differs.

| Arm | Runs |
|---|---|
| 0.19 (before) | 42107078000, 42107085215 |
| 0.14 (chosen) | 42107091461, 42107096526 |
| 0.10 | 42107102347, 42107107732 |
| 0.06 | 42107112472, 42107117540 |

## Results: share of the 119 jobs held by former players in 2058

| Seed | 0.19 | 0.14 | 0.10 | 0.06 |
|---|---|---|---|---|
| 301 | 89.1% | 79.0% | 60.5% | 47.1% |
| 302 | 87.4% | 68.9% | 58.0% | 35.3% |
| 303 | 81.5% | 67.2% | 52.9% | 41.2% |
| 304 | 89.9% | 69.7% | 54.6% | 32.8% |
| 305 | 84.0% | 75.6% | 57.1% | 39.5% |
| 306 | 84.0% | 67.2% | 55.5% | 36.1% |
| **Mean** | **86.0%** | **71.3%** | **56.4%** | **38.7%** |
| SD across seeds | 3.3 | 4.9 | 2.7 | 5.1 |
| SE of the mean | 1.3 | 2.0 | 1.1 | 2.1 |
| Paired change vs 0.19 (SE) | - | -14.7 (1.9) | -29.6 (1.2) | -47.3 (2.6) |
| Senior coaches who are former players (all seeds) | 28 of 114 | 19 of 114 | 10 of 114 | 3 of 114 |
| Former-player coach records on file (mean) | 252 | 197 | 156 | 110 |
| Jobs filled | 119 every seed | 119 | 119 | 119 |

The old odds reproduce the recorded 86% exactly (86.0%, every seed 81-90%).
0.14 lands on 71.3%, every seed inside 60-80%. 0.10 falls below the aim.

## What changed

`CoachPathway.BASE_INTEREST` 0.19 -> 0.14. The career bonuses are kept, so the
chance a retiree goes into coaching is now 14%, 17% from 150 games, 20% from
250, plus a point per Brownlow or Coleman (two at most): the long-serving
champion is still the likeliest to coach.

Why this lever: the share is set by how many former players enter the coaching
ranks; the market hires on fit and reputation and gives former players no edge
beyond half of the 5% club link at their own clubs. The outside supply
(generated state-league coaches) already tops the market up to whatever the
pathway leaves short and never lets the pool fall below 20, so fewer former
players entering means more outside coaches hired, with no job ever left open.
Changing who clubs hire instead would mean biasing the ranking against former
players, which the Phase 4 design rules out (fame is not coaching ability). The
Phase 4 record named this lever first ("lower `BASE_INTEREST` first").

## Not exercised

- One managing club (MEL) on autopilot; a user who hires former players by
  hand moves only his own six jobs.
- Past 2058. The share is still climbing at the horizon in every arm (seed
  301: 0.19 went 59.7% in 2050, 81.5% in 2056, 89.1% in 2058; 0.14 went
  53.8%, 73.1%, 79.0%), as the opening-day coaches retire and the pathway
  fills. A longer career will read higher than 71% at 0.14; this run answers
  the 2058 question only.
- Former-player senior coaches appear late: none in any seed until the last
  few seasons, so the 19-of-114 figure is a snapshot of a pipeline just
  reaching the top job.
- Expansion: the default league's 19th club joins in these careers (113 jobs
  in 2028, 119 from 2030); a career with further expansion clubs was not run.
- No match play changes, so no `tools/balance.sh` table.
