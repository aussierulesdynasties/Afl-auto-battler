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
  counts the coach records holding a job, those with a `former_player_id`, and
  the same for senior coaches.
- Seeds 301-306, the same six for every arm, run on GitHub's runners
  (`audit.yml`, three jobs of two careers per arm, about 1 h 40 min each).
- Base: the branch with origin/main merged in (5077f3b6), so it includes #888
  (deterministic best-candidate hiring, no sacking cap), which changes who
  fills the jobs. Arms: the old odds (`BASE_INTEREST` 0.19) and three
  candidates (0.14, 0.12, 0.10), each a one-constant commit on that head.
  Nothing else differs.

| Arm | Runs |
|---|---|
| 0.19 (before) | 42128832392, 42128842958, 42128853083 |
| 0.14 | 42128795707, 42128807072, 42128819013 |
| 0.12 (chosen) | 42139095781, 42139106487, 42139116211 |
| 0.10 | 42139136110, 42139144895, 42139153771 |

## Results: share of the 119 jobs held by former players in 2058

| Seed | 0.19 | 0.14 | **0.12** | 0.10 |
|---|---|---|---|---|
| 301 | 89.9% | 84.0% | 74.8% | 65.5% |
| 302 | 86.6% | 80.7% | 74.8% | 67.2% |
| 303 | 84.0% | 72.3% | 64.7% | 59.7% |
| 304 | 88.2% | 77.3% | 72.3% | 66.4% |
| 305 | 85.7% | 80.7% | 71.4% | 64.7% |
| 306 | 86.6% | 77.3% | 68.9% | 56.3% |
| **Mean** | **86.8%** | **78.7%** | **71.1%** | **63.3%** |
| SD across seeds | 2.0 | 4.0 | 3.9 | 4.3 |
| SE of the mean | 0.8 | 1.6 | 1.6 | 1.8 |
| Paired change vs 0.19 (SE) | - | -8.1 (1.2) | -15.7 (1.1) | -23.5 (1.6) |
| Senior coaches who are former players (all seeds) | 33 of 114 | 24 of 114 | 21 of 114 | 13 of 114 |
| Career endings into coaching (mean per seed) | 257 of 1,144 (22.5%) | 209 of 1,152 (18.1%) | 184 of 1,148 (16.0%) | 160 of 1,146 (13.9%) |
| Jobs filled | 119 every seed | 119 | 119 | 119 |

The audit's 0.19 arm lands on the same 86% as the recorded career (86.8%,
seeds 84-90%), although its autopilot careers end about twice as many careers
(~1,150 vs 615), so it is a proxy for that career, not a rerun of it.

0.14 measured 71.3% on the pre-#888 base (runs 42107091461, 42107096526) but
78.7% on the merged head, with three of six seeds at or above 80%: #888's
hiring (a reputation bar for a step up, fame lifting a former player's
starting reputation, deterministic renewals) favours former players a little
more. 0.12 lands on 71.1%, every seed inside 60-80% (64.7-74.8%). 0.10 puts
one seed below 60%.

## What changed

`CoachPathway.BASE_INTEREST` 0.19 -> 0.12. The career bonuses are kept, so the
chance a retiree goes into coaching is now 12%, 15% from 150 games, 18% from
250, plus a point per Brownlow or Coleman (two at most): the long-serving
champion is still the likeliest to coach.

Why this lever: the share is set by how many former players enter the coaching
ranks; the market hires on fit and reputation and gives former players no edge
beyond half of the 5% club link at their own clubs and a fame lift to starting
reputation that fades. The outside supply (generated state-league coaches)
already tops the market up to whatever the pathway leaves short and never lets
the pool fall below 20, so fewer former players entering means more outside
coaches hired, with no job ever left open. Changing who clubs hire instead
would mean biasing the ranking against former players, which the Phase 4
design rules out (fame is not coaching ability). The Phase 4 record named
this lever first ("lower `BASE_INTEREST` first").

## Conflict with the Phase 4 entry band

DIRECTOR_BIBLE item 30 (Phase 4) sets a "Test band 20-30% entry" for career
endings that go into coaching, and records "As built: 19% base". At 0.12 about
16% of endings go into coaching (table above), below that band. The same item
names lowering `BASE_INTEREST` as the lever if the share passes 80%, so row 71
plausibly replaces the band; that is the director's call, and the bible is
unchanged.

## Not exercised

- One managing club (MEL) on autopilot; a user who hires former players by
  hand moves only his own six jobs.
- Past 2058. The share is still climbing at the horizon in every arm (seed
  301: 0.19 went 58.0% in 2050, 82.4% in 2056, 89.9% in 2058; 0.12 went
  45.4%, 68.9%, 74.8%), as the opening-day coaches retire and the pathway
  fills. A longer career will read higher than 71% at 0.12, possibly past
  80%; this run answers the 2058 question only.
- Former-player senior coaches appear late: none in any seed at 0.12 before 2057,
  so the 21-of-114 figure is a snapshot of a pipeline just reaching the top
  job.
- Expansion: the default league's 19th club joins in these careers (113 jobs
  in 2028, 119 from 2030); a career with further expansion clubs was not run.
- No match play changes, so no `tools/balance.sh` table.
