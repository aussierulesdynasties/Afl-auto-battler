# Handoff: GitHub, CI and repo health

Written 2026-11-27 about 07:30 UTC (18:30 Melbourne) for a fresh Claude on a different account. The
project threads this work was done in ("FIX GITHUB FOR AFL GAME") cannot be read from that account,
so everything you need is in this file and the files it links. The relationship overhaul has its own
handoff: [HANDOFF_relationship_overhaul.md](HANDOFF_relationship_overhaul.md).

The owner is "Baggins" (GitHub `gabebartolo-spec`), also called the director in the repo docs. Every
Claude session acts as `gabebartolo-spec` on GitHub, so GitHub cannot tell you which session did
something.

---

## 1. How Baggins wants you to work

These are Baggins's own standing rules from 26 and 27 Nov. Follow them without asking again.

1. **Merge every PR without asking.** "stop asking me dumb questions merge everything right away",
   and on 27 Nov: "merge every SINGLE PR". When a PR is green and has no conflict, merge it (squash)
   or turn on squash auto-merge. No merge cards, no "shall I merge?" questions.
2. **No balance re-runs** for this backlog (27 Nov). Don't park a PR waiting for a balance call or a
   design call. Resolve it sensibly and merge.
3. **No PR cap and no batching for now** (27 Nov). See the conflict note in section 6.
4. **Carry out recommended fixes yourself**, including repo settings and cleanup. Take a backup first
   for anything destructive. Ask only when the choice is truly his (money, game design).
5. **Force-cancel stuck or stale CI runs without asking** ("stop asking me questions you know the
   answer to").
6. **Find CI and GitHub problems yourself.** He expects you to notice red checks, stuck runs, runs
   that were cancelled but still hold runners, and to report them unprompted.
7. **Never call something fixed without measured evidence**, before and after, from real runs. Past
   sessions claimed fixes that didn't work, and he was burned by it. Say plainly when something
   failed or is unverified.
8. **Plain, short posts.** No jargon, no engine terms, no strings of PR numbers without saying what
   each one is.
9. **No personal or wellbeing comments** (no "take a break"), and no eye-emoji reactions. Keep it to
   the work.
10. **Long runs go on GitHub** (his pick, 26 Nov): push a branch and read its checks, or use the
    nightly's manual run for long suites. Short runs go ahead locally.

These rules now live in the repo, at the top of [CLAUDE.md](../CLAUDE.md) ("How every Claude session works
here"), so every session on any account loads them. CLAUDE.md is the source; this list is a copy for context.
Also there: fix a red PR at once yourself (even another session's), never push a commit you expect to fail,
close obsolete PRs yourself with a comment (Director Bible 7.50 now says so), and check the diff after merging main in.

- **Never rebase or force-push a shared branch.** Merge main in instead.

The GitHub Support request about the repo size figure was dropped on 27 Nov. Don't raise it.

---

## 2. What was done and measured (26 and 27 Nov)

| What | Result, measured | Where |
|---|---|---|
| **History rewrite** | Whole repo history 9.9 GB down to 1.04 GB; main 6.55 GB down to 793 MB. Every commit message kept (3,931 commits). Removed: Epic/MetaHuman files, `.claude/review/` boards, ground imagery, old stadium model versions. Full test run on the new main passed (16 of 16 jobs). Done 26 Nov 22:06 UTC, main was `6939384`. | Plan: section 3 below |
| **Backups before the rewrite** | Full mirror in the private repo `aussierulesdynasties/afl-review-archive`, branches `backup-afl-auto-battler/*`. 205 `archive/*` tags re-pointed at the rewritten commits and checked on GitHub (205 of 205 match). | |
| **Review boards moved out** | `.claude/review/` now lives in `afl-review-archive` at the same paths, and is git-ignored here. | CLAUDE.md "Review boards and imagery" |
| **Stadium models moved out** | Ground models live in the private repo `gabebartolo-spec/ard-asset-pipeline`, branch `ground-assets`. `tools/ground_assets.sh fetch` copies them in; `publish` uploads changes and updates `tools/ground_assets.lock`. Never `git add` them. (PR #2199) | [GROUND_ASSETS.md](GROUND_ASSETS.md) |
| **Force-push block on main** | Main's ruleset now has three rules: requires the "test" check, blocks deletion, blocks force pushes. Only admins can bypass. Read back and confirmed 26 Nov 23:01 UTC. | GitHub repo settings > Rules |
| **Merge queue removed** | The merge-queue ruleset was removed, and #2201 stripped its leftovers from `tests.yml`. Only the "test" check is required, and "branch must be up to date" is off. | |
| **Branch cleanup** | 71 branches from closed, unmerged PRs deleted, each saved first as an `archive/<name>` tag. 130 branches down to 60 (43 on 27 Nov). | `repo_hygiene.yml` |
| **PR cap bot deleted** | On Baggins's order ("delete the bot"), #2236 removed `pr_cap.yml`. It also added hook guards that refuse cancelling a main test run and merging a workflow change with no green run. | `.claude/hooks/pr_guard.py` |
| **Flaky seed fix** | Tests were "seeded" but the first career of each run took a clock seed, so match_story and dataset failed at random (161 failure events in two weeks). #2197 fixed it: three runs started 4 s apart now give identical logs, full suite 530 checks, 0 failures. It also fixed three tests that turned the director's OVR rows back on for every test after them. | [test-suite findings](#7-files-worth-reading), batch 7 |
| **Test split and shard re-plan** | career_ui split into two suites (`career_ui`, `career_ui_2`), shards re-planned from fresh timings (#2212, #2244, #2247). Longest shard 721 s down to 662 s of suite time, spread 334 s down to 224 s (one run each; runner speed varies). The run log now lists "Suites off their timing". | `tools/ci_shards.txt`, `tools/ci_suite_timings.json` |
| **Godot import cache** | #2196 caches the `.godot` import between runs. Compile check 12-14 min down to 75 s; each shard 15-28 min down to 6.5-14 min. About 3 runner-hours saved per full run. | `.github/actions/godot-import-cache`, `tools/ci_import_cache.py` |
| **Main push runs** | Pushes to main share one Tests group: only the newest waiting run is kept, older waiting ones are skipped (that's why many main runs show "cancelled"; it's on purpose). Web build runs nightly instead of on every push (#2190). | `tests.yml`, `web.yml` |
| **Force-cancel tool** | Repo hygiene force-cancels runs from closed or superseded PRs by itself, and its `force_cancel: <run ids>` input force-cancels named runs (GitHub MCP `actions_run_trigger`). A normal cancel doesn't stop shards on branches last synced before 26 Nov. (#2224) | `repo_hygiene.yml` |
| **Stale test checksums** | Main went red when two engine PRs both moved the seeded checksums (`GOLDEN_SEASON` in `tests/test_dataset.gd`, `GOLDEN played:*` in `tests/test_season_rules.gd`). Fixed by #2243 and #2245. | |
| **CI health check** | Moved from a Claude account's scheduled task into the repo, so it runs for any account. `.github/workflows/ci_health.yml` runs every 2 hours and after pushes to main (GitHub's timer is unreliable here). It force-cancels runs still holding runners for a closed PR or an old commit, and reports long waits, stuck runs, a red main or nightly, and PRs nobody is driving on one issue, "CI health check: problems found". The issue closes itself when all is healthy. Rules: `tools/ci_health.py`. | Check that issue first |
| **Self-hosted PC runners** | Removed 26 Nov. Everything runs on GitHub's runners. | [CI_RUNNER.md](CI_RUNNER.md) |

---

## 3. Open PRs at handoff (live GitHub state, 27 Nov 07:25 UTC)

Main is at `f2dd46f` (#2257). Its push run 45957628440 is running. The last fully green main run was on
`25cb973` (#2227).

| PR | What it is | State | Next step |
|---|---|---|---|
| **#2259** | Relationship overhaul in one PR: Card Pass 1, Phase 1 integration, the Council, factions, ambitions | Ready, auto-merge on, CI running. **This is the PR to land.** Checked against main: it carries every fix the bad #2229 merge dropped, plus the club-test fix | Let it merge. If red, read the failed job, fix, push once. Its body says the balance table is "to follow"; Baggins said no balance re-runs for this backlog. |
| **#2229, #2203, #2204, #2223** | The old stacked relationship PRs (integration, factions, the Council, ambitions) | Drafts | Superseded by #2259. Once #2259 merges they are to be closed (Baggins closes them, or tell him they can be). Don't push to them. #2229 also has a bad main merge that dropped main's fixes, so never merge it. |
| **#2239** | Player rating rebuild, phases 2-4, 6, 7 | Ready, auto-merge on, CI queued | Let it merge. If red, read the failed job, fix, push once. |
| **#2242** | Rating rebuild phase 8 (the card, colour cuts, words) | Ready | Follows #2239. Merge main in after #2239 lands if it conflicts, then merge on green. |
| **#2240** | Endurance from three game numbers; draft-night deals | Draft, on purpose: the rating rebuild's own session moved it back while it re-records the dataset checksums | Sits on top of #2239. After #2239 lands and the checksums are re-recorded, mark ready and merge on green. |
| **#2258** | Roadmap notes for merged PRs (the rolling `roadmap-close/batch` PR) | Ready | Bot-made docs PR. Merge on green. |
| **#2238** | "PR cap: works without read:org" (branch `claude/project-thread-vmkoek`) | Draft | It only re-adds the PR cap bot that Baggins ordered deleted. It should be closed. Sessions don't close PRs, so tell Baggins it can be closed, or close it if he tells you to. |

Merged on 26 and 27 Nov after the rewrite: #2210, #2214, #2216, #2217, #2218, #2219, #2220, #2221, #2225,
#2226, #2227, #2231, #2232, #2233, #2234, #2235, #2241, #2243, #2245, #2247, #2254, #2255, #2256, #2257.

To re-check the live state: GitHub MCP `list_pull_requests` (state open), then `pull_request_read`
with `get_check_runs` on each.

---

## 4. Known risks and lessons

1. **A main merge can silently drop fixes.** When you merge main into a branch and resolve conflicts,
   it's easy to take the branch's side of a whole hunk and lose main's changes. This happened on
   #2229 twice on 27 Nov. After any conflicted merge, run
   `git diff origin/main...HEAD` and `git diff origin/main HEAD -- <each conflicted file>` and check
   that every change main made is still there. Re-measure seeded checksums only on the repaired tree.
2. **Two sessions on one PR toggle each other.** On 26 and 27 Nov sessions turned each other's
   auto-merge off, moved PRs back to draft, and pushed main merges to the same branch. Before
   touching a PR, check its latest commits and comments. One owner per branch.
3. **Rewriting main's history auto-closes every open PR, for good.** GitHub won't reopen them; they
   had to be recreated (#2210 to #2235). Warn every thread before any future rewrite.
4. **Seeded checksums go stale** when two engine PRs merge one after another. If a PR is red on the
   dataset or season_rules shard, check main's own push run first.
5. **GitHub's scheduled (cron) runs are unreliable.** Measured: hourly jobs fired about 1 time in 8,
   and the nightly started 5 to 11 hours late. Never rely on a cron for recovery or timing; make the
   event-driven path sweep the whole state.
6. **Workflows sharing a concurrency group lose events.** GitHub keeps one running and one waiting
   run per group; a newer waiting run cancels the older one. This lost roadmap notes for five PRs.
7. **The runner pool is small.** The free org plan runs about 20 jobs at once; a full Tests run needs
   up to 30. Every extra push cancels the run and goes to the back of the queue. Push once.
8. **Draft PRs skip the game tests.** A draft can look fine and fail the moment it's marked ready.
   The session that built #2259 found the story and club suites had never run with the overhaul in.
9. **Ghost runs:** six runs queued since 11 Nov on `feat/144-full-time-story` and
   `fix/onboarding-press-scene` can't be cancelled (GitHub returns 409) and have no jobs. Ignore them.
10. **Local disk:** cloud containers can fill up with old clones. Delete what you don't need.

---

## 5. Still open (no thread was working on these)

- **Repo size figure on GitHub** still reads about 10 GB, because old PR refs keep old files. It's
  cosmetic only, and Baggins dropped the Support request. Leave it.
- **88 MCG texture files** are rewritten by every fresh Godot import (their committed import settings
  don't match). Committing the regenerated files once would stop it. Not done.
- **Test suite audit ideas not yet built** (in the findings file): run a shard's small suites in one
  Godot process (about 16 runner-minutes of start-up per full run), a shared "season already played"
  save so suites stop re-simulating the same season, the nightly fixture that runs twice, five legacy
  long careers that cover the same years (about 58 minutes a night), and two wall-clock checks that
  can flake. Deleting or merging tests needs Baggins's yes.
- Nothing in this work is tied to a Claude account: every fix lives in the repo or in GitHub's
  settings.

---

## 6. Conflicts in the written rules

- CLAUDE.md "Getting a PR merged" still says to keep at most 3 ready PRs and open the rest as drafts.
  On 27 Nov Baggins said no PR cap and no batching while the backlog is cleared. Follow Baggins.
  If he wants the cap gone for good, update CLAUDE.md in a PR.
- Some older docs mention `pr_cap.yml`, the `waiting-for-slot` and `cap-exempt` labels, and the merge
  queue. All three are gone.

---

## 7. Files worth reading

- [CLAUDE.md](../CLAUDE.md): repo rules, especially "Getting a PR merged".
- [GROUND_ASSETS.md](GROUND_ASSETS.md) and [EPIC_ASSETS.md](EPIC_ASSETS.md): files that live in private repos.
- [CI_RUNNER.md](CI_RUNNER.md): the removed PC runners, kept as a record.
- `tools/balance/README.md`: the balance harness, if a row needs it.
- `.claude/hooks/pr_guard.py`: the hooks that refuse risky PR actions; each refusal names its override.
- Skills in `.claude/skills/`: `afl-ci-merge-hygiene`, `afl-godot-tests`, `afl-team-pr`, `afl-handoff`.
- The test suite audit (`test-suite-audit/findings.md`) and the history rewrite plan were project
  files on the old account. Their findings are summarised above.
