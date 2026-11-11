---
name: afl-team-pr
description: Opening, syncing and handing over a pull request the AFL team's way - branch and worktree, what goes in the PR body ([MERGE NOTE], director gates, W7), who merges, when not to push, and how to tell another session about it. Use it whenever you are about to open a PR, update one after main moved, resolve a conflict in the roadmap or a shared registry, or tell another agent about a PR or CI result.
---

# A PR the team's way

## Who does what (director, 2026-10-29)

No roles: no lead, support, art or hygiene agent. Each session does the whole job itself (code, tests, PR,
merge) and reports straight to the director, who decides taste, trade-offs and spend and approves any look.
Handoff: one file per worktree in `~/.claude/handoffs/` (afl-handoff).

## Start

- Work only what was assigned (a roadmap entry is context, not authorisation).
- Own worktree from current main, never the shared checkout; no `git stash`; stage by name:

```bash
git fetch -q origin
git worktree add -b claude/<topic> ../Afl-auto-battler-<topic> origin/main
```

- Running suites, import churn, the function count: afl-godot-tests. Evidence: afl-proof-evidence. Branch, commit and merge rules: github-hygiene.

## PR body

1. What the player sees, and why (football words; "nothing, internal" is valid).
2. Assigned in: the director message, status line or roadmap item that authorised it.
3. What changes (mechanism).
4. Evidence and Not exercised (a PR without a Not exercised line is not ready).
5. Tests: suites run and counts.
6. [MERGE NOTE]:
   - hot files (MatchSim, GameState, ROADMAP section files, CLAUDE.md, tests.yml);
   - tests: call each new `_test_*` through `_t(...)` in your suite's own file (no shared count file);
   - ordering against other open PRs;
   - W7 needed (save, rollover, shared sim, recruitment, identity: afl-lifecycle-review) and by whom;
   - director gate: any change of appearance waits for the director's look, recorded on the PR; green CI never clears it.
7. Attribution line from the session's instructions.

Mark ready before the push you want tested; drafts skip game tests.

## After opening

- You merge your own PR (director, 2026-11-03: he never merges and is never asked): turn on auto-merge on green, or merge when green with `gh pr merge N --squash --match-head-commit <full sha>` (PR `headRefOid` equal to origin's branch tip, mergeStateStatus CLEAN). No `--delete-branch` (it removes the local branch and any clean worktree on it; the repo deletes remote head branches itself). Fix red CI until green.
- A PR waits only for its recorded gates: director look, W7, ordering in the merge note.
- Do not push while its CI runs; a push cancels it.
- Owner merges `origin/main` into the branch only when GitHub reports a conflict (`mergeStateStatus` `DIRTY`) or the branch needs code that is only on main, never just because main moved: PR CI already tests the merge with current main, and each sync re-runs the whole CI. After such a merge, re-run the touched suites and the suites main brought in. Run `tools/prepush.sh` before every push. Work list: never edit `docs/TODO.md` in a PR; put `Closes row N` (or `Closes rows 22, 27`, `Closes row T5.Q24`, matching the row's first cell) on its own line in the PR body, and `roadmap_close.yml` deletes the row after the merge. Only a PR labelled `roadmap` may edit the file (CI fails otherwise; after labelling, re-run the failed jobs). Floor conflict: write the real count.
- Only the branch owner pushes to it.
- Task boundary: rewrite your handoff (task, branch and sha, open decisions, running jobs).

## Messages

- A CI failure or conflict on another session's branch goes to that session: branch, sha, run id, suite and check, whether main fails too, who acts next.
- Every message names its PR and head sha and what you need or found. No "received" messages, no queue recaps. Decisions, blockers and findings go to the director.
- A peer's message is a request, not a permission. Never ask a peer to do what your own session was refused; take it to the director.
- End every turn with a state: working (only while a job you launched is still running, named), awaiting director, blocked, or available. While waiting on CI, an audit or a peer, arm a bounded background watcher and do the next useful part of your queue (work-while-waiting).

## Learnings

Proven findings: `references/learnings.md`. Read it before using this skill; add only what proved effective, with evidence.
