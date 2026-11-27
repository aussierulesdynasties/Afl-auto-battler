# Handoff: GitHub, CI and repo health

Final version, written 2026-11-27 about 12:00 UTC (23:00 Melbourne) for a fresh Claude on a different
account. The project threads this work was done in ("FIX GITHUB FOR AFL GAME") can't be read from that
account, so everything you need is in this file, in [CLAUDE.md](../CLAUDE.md) and in the files linked
below. The relationship overhaul has its own handoff: [HANDOFF_relationship_overhaul.md](HANDOFF_relationship_overhaul.md).

The owner is "Baggins" (GitHub `gabebartolo-spec`), called the director in the repo docs. Every Claude
session acts as `gabebartolo-spec` on GitHub, so GitHub can't tell you which session did something.

Everything below was checked against live GitHub at the time of writing, not taken from session reports.

---

## 0. Start here (do these first, in order)

1. **Read the top of [CLAUDE.md](../CLAUDE.md)**, "How every Claude session works here". Those nine rules
   are Baggins's and win over anything else. Section 1 below adds the few that aren't there.
2. **Check live GitHub, not your local clone or a report.** List the open PRs (GitHub MCP
   `list_pull_requests`, state open) and each one's checks (`pull_request_read`, `get_check_runs`).
   At handoff the only open PR is #2266, a draft 3D plan another thread is writing (section 4).
3. **Read the CI health issue**, "CI health check: problems found" (#2265 at handoff). It is rewritten
   every check and closes itself when everything is healthy. At handoff it lists one problem: the
   last nightly long-suite run failed (section 5, item 1).
4. **Check main's newest push run of Tests** (`actions_list`, `tests.yml`, branch main, event push).
   At handoff every main push run since 07:54 UTC is green; the run on `5a80bef` (#2242) was running.
5. **Check tonight's nightly** (`nightly.yml`). It is due 16:00 UTC but usually starts 5 to 11 hours late.
   It is the first nightly with the relationship overhaul and the rating rebuild in, and the story suites
   only run there (section 5).
6. Then pick work from `docs/TODO.md` only when Baggins assigns it.

You don't need to set up any scheduled task on your account: nothing recurring depends on a Claude
account any more (section 6).

---

## 1. How Baggins wants you to work

The nine rules at the top of CLAUDE.md are the source. In short: merge every green PR without asking (no
PR cap, no batching, no balance re-runs unless he asks); fix a red PR at once yourself, even another
session's; never push a commit you expect to fail; close obsolete PRs yourself with a comment; no claim
without before-and-after evidence from real runs; check the diff after merging main in; find CI problems
yourself and force-cancel stuck runs without asking; plain, short messages with no jargon and no
personal comments; nothing may depend on one Claude account.

Also from him, not in CLAUDE.md:

- **Carry out recommended fixes yourself**, including repo settings and cleanup. Take a backup first for
  anything destructive. Ask only when the choice is truly his (money, game design).
- **Long runs go on GitHub** (his pick, 26 Nov): push a branch and read its checks, or use the
  nightly's manual run for long suites. Short runs go ahead locally.
- **Watch your PR continuously until it merges** (27 Nov): after a push, keep checking every minute or
  two and start the fix the moment a job fails.
- **No eye-emoji reactions.**
- **Never rebase or force-push a shared branch.** Merge main in instead.
- The GitHub Support request about the repo size figure was dropped. Don't raise it.

---

## 2. What was done and measured (26 and 27 Nov)

| What | Result, measured | Where |
|---|---|---|
| **History rewrite** | Whole repo history 9.9 GB down to 1.04 GB; main 6.55 GB down to 793 MB. Every commit message kept (3,931 commits). Removed: Epic/MetaHuman files, `.claude/review/` boards, ground imagery, old stadium model versions. Full test run on the new main passed (16 of 16 jobs). Done 26 Nov 22:06 UTC, main was `6939384`. | Backups: next row |
| **Backups before the rewrite** | Full mirror in the private repo `aussierulesdynasties/afl-review-archive`, branches `backup-afl-auto-battler/*`. 205 `archive/*` tags re-pointed at the rewritten commits and checked on GitHub (205 of 205 match). | |
| **Review boards moved out** | `.claude/review/` now lives in `afl-review-archive` at the same paths, and is git-ignored here. | CLAUDE.md "Review boards and imagery" |
| **Stadium models moved out** | Ground models live in the private repo `gabebartolo-spec/ard-asset-pipeline`, branch `ground-assets`. `tools/ground_assets.sh fetch` copies them in; `publish` uploads changes and updates `tools/ground_assets.lock`. Never `git add` them. (PR #2199) | [GROUND_ASSETS.md](GROUND_ASSETS.md) |
| **Force-push block on main** | Main's ruleset now has three rules: requires the "test" check, blocks deletion, blocks force pushes. Only admins can bypass. Read back and confirmed 26 Nov 23:01 UTC. | GitHub repo settings > Rules |
| **Merge queue removed** | The merge-queue ruleset was removed, and #2201 stripped its leftovers from `tests.yml`. Only the "test" check is required, and "branch must be up to date" is off. | |
| **Branch cleanup** | 71 branches from closed, unmerged PRs deleted, each saved first as an `archive/<name>` tag. 130 branches down to 60 (43 on 27 Nov). | `repo_hygiene.yml` |
| **PR cap bot deleted** | On Baggins's order ("delete the bot"), #2236 removed `pr_cap.yml`. It also added hook guards that refuse cancelling a main test run and merging a workflow change with no green run. | `.claude/hooks/pr_guard.py` |
| **Flaky seed fix** | Tests were "seeded" but the first career of each run took a clock seed, so match_story and dataset failed at random (161 failure events in two weeks). #2197 fixed it: three runs started 4 s apart now give identical logs, full suite 530 checks, 0 failures. It also fixed three tests that turned the director's OVR rows back on for every test after them. | Test suite audit, batch 7 (summarised in section 7) |
| **Test split and shard re-plan** | career_ui split into two suites (`career_ui`, `career_ui_2`), shards re-planned from fresh timings (#2212, #2244, #2247). Longest shard 721 s down to 662 s of suite time, spread 334 s down to 224 s (one run each; runner speed varies). The run log now lists "Suites off their timing". | `tools/ci_shards.txt`, `tools/ci_suite_timings.json` |
| **Godot import cache** | #2196 caches the `.godot` import between runs. Compile check 12-14 min down to 75 s; each shard 15-28 min down to 6.5-14 min. About 3 runner-hours saved per full run. | `.github/actions/godot-import-cache`, `tools/ci_import_cache.py` |
| **Main push runs** | Pushes to main share one Tests group: only the newest waiting run is kept, older waiting ones are skipped (that's why many main runs show "cancelled"; it's on purpose). Web build runs nightly instead of on every push (#2190). | `tests.yml`, `web.yml` |
| **Force-cancel tool** | Repo hygiene force-cancels runs from closed or superseded PRs by itself, and its `force_cancel: <run ids>` input force-cancels named runs (GitHub MCP `actions_run_trigger`). A normal cancel doesn't stop shards on branches last synced before 26 Nov. (#2224) | `repo_hygiene.yml` |
| **Stale test checksums** | Main went red when two engine PRs both moved the seeded checksums (`GOLDEN_SEASON` in `tests/test_dataset.gd`, `GOLDEN played:*` in `tests/test_season_rules.gd`). Fixed by #2243 and #2245. | |
| **CI health check** | Moved from a Claude account's scheduled task into the repo, so it runs for any account. `.github/workflows/ci_health.yml` runs every 2 hours and after pushes to main (GitHub's timer is unreliable here). It force-cancels runs still holding runners for a closed PR or an old commit, and reports long waits, stuck runs, a red main or nightly, and PRs nobody is driving on one issue, "CI health check: problems found". The issue closes itself when all is healthy. Rules: `tools/ci_health.py`. | Issue "CI health check: problems found" |
| **Session rules in the repo** | Baggins's standing rules now sit at the top of CLAUDE.md, so every session on any account loads them (#2267, merged 27 Nov 09:28 UTC). | [CLAUDE.md](../CLAUDE.md) |
| **PR backlog cleared** | About 30 PRs merged on 26-27 Nov, including the relationship overhaul (#2259) and the rating rebuild (#2239, #2240, #2242). Every main push run since 07:54 UTC 27 Nov is green. | Section 4 |
| **Self-hosted PC runners** | Removed 26 Nov. Everything runs on GitHub's runners. | [CI_RUNNER.md](CI_RUNNER.md) |

---

## 3. Every project thread, final state

| Thread | Final state |
|---|---|
| Speed up slow GitHub repo | Done. PR flow fixes (#2186, #2193, #2200), force-cancel tool (#2224), tackle fix (#2230). |
| Make the game's CI tests faster | Done. Godot import cache (#2196). |
| Audit every CI workflow file for flaws | Done. #2190 (main push group, nightly web build, draft cancels). |
| Audit bots and scheduled jobs | Done. Merge-queue leftovers removed (#2201); 71 dead branches archived as tags and deleted. |
| Find why sessions mishandle PRs | Done. PR guard hooks (#2191) and the cap bot deletion (#2236). |
| Apply GitHub repo settings fixes | Done. 205 archive tags pushed, force pushes blocked on main. |
| Audit test suite for slow and flaky tests | Done. Seed fix (#2197), shard re-plans (#2212, #2244, #2247). Ideas not built are in section 7. |
| Cut repo bloat and checkout size | History rewrite and stadium model move done. It also drove the relationship PRs; #2259 merged 10:13 UTC 27 Nov and the four old stacked PRs (#2229, #2203, #2204, #2223) were closed. Last seen running the story suites locally against main (see section 5). |
| Keep CI moving and clear parked PRs | Done. Cleared the backlog; last merge was #2242 at 11:50 UTC 27 Nov. It also ran the old CI health check, now moved into the repo. |
| Put session rules into the repo | Done. #2267. |
| Write handoff for other Claude account | This file (#2261, #2263, and this update). |
| Help me work out a plan for a project | An unrelated planning chat from 26 Nov; nothing open. |

---

## 4. Open PRs at handoff (live GitHub, 27 Nov about 11:55 UTC)

| PR | What it is | State | Next step |
|---|---|---|---|
| **#2266** | 3D 1.0 plan: Marvel round 13, Bellerive round 7, Norwood, Legacy measurements, era surroundings, injuries on main (branch `claude/project-thread-rfc4kn`) | Draft, last touched 09:04 UTC | Another thread is still writing it. When it's ready, mark it ready and merge on green. If nobody has touched it for days, finish it or close it with a comment. |

Merged on 26 and 27 Nov, newest first: #2242 rating rebuild phase 8, #2240 endurance and draft-night deals,
#2259 relationship overhaul, #2267 session rules, #2239 rating rebuild, #2263 CI health check, #2264,
#2262, #2260 docs, #2261 this handoff, #2258, #2257 new-career crash fix, #2241 menus on your club's
ground, #2255, #2232, #2256, #2227, #2218, #2216, #2254, #2214, #2217, #2231, #2235, #2221, #2234, #2220,
#2225, #2245, #2243, #2219, #2233, #2226, #2210.
Closed without merging on 27 Nov: #2229, #2203, #2204, #2223 (all carried by #2259) and #2238 (it only
re-added the deleted PR cap bot).

---

## 5. Watch out for these now

1. **The last nightly failed** (run 45916430137): `matchday_breaks` crashed (signal 11 while a new career
   reloaded players). #2257 is the fix, merged 07:19 UTC 27 Nov. Unverified until a nightly runs with it.
2. **The story suites may fail on main.** They run only in the nightly, never on PRs, and the
   relationship overhaul changed the trust rules those tests check. The "Cut repo bloat" thread found a
   crash had hidden one story test's later checks and was updating them when this was written; if no
   fix PR has merged, run `tools/run_tests.sh story` (and `story_culture`) on main and fix what fails.
3. **Team ratings may be badly spread after the rating rebuild.** A test season had Fremantle going
   23-0. That's one hint, not a measurement. Balance is Baggins's call: report it with numbers (the
   balance harness, `tools/balance/README.md`), don't retune on your own.
4. **Ghost runs:** six runs queued since 11 Nov on `feat/144-full-time-story` and
   `fix/onboarding-press-scene` can't be cancelled and hold no runner. The health check ignores them.

---

## 6. Scheduled jobs (all in the repo; none on a Claude account)

| Workflow | When | What it does |
|---|---|---|
| `ci_health.yml` | Every 2 h at :43, and after each push to main (skipped if one ran in the last hour) | The CI health check (section 2). Rules in `tools/ci_health.py`. |
| `repo_hygiene.yml` | Every 6 h at :17, and on demand | Deletes dead branches, force-cancels stale PR runs; `force_cancel` input stops named runs. |
| `nightly.yml` | 16:00 UTC (03:00 Melbourne) | The long test suites listed in `tools/ci_long_suites.txt`. |
| `web.yml` | 15:30 UTC | The web build. |
| `ground-shots.yml` | 18:00 UTC | Shots of every ground compared to a baseline (issue "Ground shots: what changed"). |
| `ui-review.yml` | 17:30 UTC | The UI review sweep on main. |
| `docs_fast_merge.yml` | Hourly backstop | Merges docs-only PRs; its Tests trigger does the real work. |
| `pr_conflicts.yml` | Hourly at :17 | Flags PRs that conflict with main. |

GitHub drops or delays most scheduled runs on this repo (measured: hourly jobs fired about 1 time in 8,
the nightly 5 to 11 hours late), so never rely on a timer alone. The old Claude-account health check
(scheduled task "CI health check every 2 hours") is turned off; no scheduled task on that account is on.

---

## 7. Known risks and lessons

1. **Re-check GitHub; don't trust local state or another session's report.** On 27 Nov a thread told the
   coordinator #2259 hadn't merged an hour after it had, because it was reading its local copy.
2. **A main merge can silently drop fixes.** Resolving conflicts by taking the branch's side of a whole
   hunk lost main's changes on #2229 twice. After any conflicted merge, check
   `git diff origin/main...HEAD` and every conflicted file against main. Re-measure seeded checksums only
   on the repaired tree.
3. **Coordinators must run their own timed checks.** A PR notice doesn't always wake the session that
   owns it. Whoever coordinates sets a timed check-in for each open PR, not only a subscription.
4. **A long-queued run is usually just a runner backlog**, not a stuck runner. The free plan runs about
   20 jobs at once and a full Tests run needs up to 30; during a burst of 15 PRs runs waited 40+ min.
   Check the jobs before cancelling anything.
5. **Two sessions on one PR toggle each other** (auto-merge off and on, back to draft, rival pushes).
   Read a PR's latest commits and comments before you touch it.
6. **Rewriting main's history auto-closes every open PR for good.** GitHub won't reopen them.
7. **Seeded checksums go stale** when two engine PRs merge one after another. If a PR is red on the
   dataset or season_rules shard, check main's own push run first.
8. **Workflows sharing a concurrency group lose events** (one running plus one waiting per group).
9. **Draft PRs skip the game tests**, and PRs never run the long suites. A draft can fail the moment
   it's marked ready, and a PR can break a nightly suite and still merge green.
10. **Push once.** Each push cancels the run in progress and goes to the back of the queue.

Still not done, no one working on them:

- 88 MCG texture files are rewritten by every fresh Godot import; committing the regenerated files once
  would stop it.
- Test-suite audit ideas: one Godot process for a shard's small suites (about 16 runner-minutes of
  start-up per full run), a shared "season already played" save, a nightly fixture that runs twice, five
  legacy long careers covering the same years (about 58 min a night), two wall-clock checks that can
  flake, and a seeded contracts check that is always skipped. Deleting or merging tests needs Baggins's yes.
- GitHub's repo size figure still reads about 10 GB because old PR refs keep old files. Cosmetic; leave it.

---

## 8. Files worth reading

- [CLAUDE.md](../CLAUDE.md): repo rules, especially the top section and "Getting a PR merged".
- [GROUND_ASSETS.md](GROUND_ASSETS.md) and [EPIC_ASSETS.md](EPIC_ASSETS.md): files that live in private repos.
- [CI_RUNNER.md](CI_RUNNER.md): the removed PC runners, kept as a record.
- `tools/ci_health.py`: what the health check looks for.
- `.claude/hooks/pr_guard.py`: hooks that refuse risky PR actions; each refusal names its override.
- `tools/balance/README.md`: the balance harness.
- Skills in `.claude/skills/`: `afl-ci-merge-hygiene`, `afl-godot-tests`, `afl-team-pr`, `afl-handoff`.
