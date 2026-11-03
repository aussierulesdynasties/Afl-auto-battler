# Agent status

_Updated 2026-11-03._ The role team this board used to track (boss, support, art, hygiene; 2026-10-10) is
retired: the director's rule of 2026-10-29 is no roles. Each session is a plain Claude session that does the
whole job itself (code, tests, PR, merge on green) and reports straight to the director. Every image, capture or
clip goes straight to him; no agent judges art.

Live state is in each worktree's handoff in `~/.claude/handoffs/` (`afl-handoff`), not here. Open PRs: `gh pr list`.

## Standing rules
One source of truth: `CLAUDE.md` in this repo and `~/.claude/CLAUDE.md` (the director's rules for every project).

## Working rules
- One Godot process per agent at a time, off-screen, with its own user data (`APPDATA=<your scratch dir>`); kill only your own PIDs.
- Run only the suites your change touches locally; CI runs the rest. Long audits go to `audit.yml`.
- Revert `.import` and `.uid` churn before committing. Stage by name; never `git add -A`; never commit another
  session's untracked files.
- Merge notes in the PR body: hot files, ordering, roadmap lines (`afl-team-pr`).
- Don't push to a PR branch while its CI runs unless the merge needs it.
- One worktree per session, from `origin/main`; prune only MERGED or CLOSED ones, after checking for real changes.
