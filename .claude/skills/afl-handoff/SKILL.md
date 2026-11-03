---
name: afl-handoff
description: Writing and starting from the AFL handoff - the one file per worktree in ~/.claude/handoffs/ that lets a fresh session (on either Claude account) continue without the old transcript. Use it when a substantial task is done or you switch to unrelated work, when your context is getting long, before the director restarts or clears a session, and at the start of every session.
---

# Handoffs (W1)

Long sessions cost the director's allowance on every turn and drift. At a task
boundary (PR open with its evidence, or a switch to unrelated work) a
session writes a handoff, and the next session starts from it, not from the
whole transcript. Never restart with in-flight work that isn't written down,
and don't restart mid-task.

## Where (director, 2026-10-29)

One file per project folder (each worktree) in `~/.claude/handoffs/`; the
SessionStart hook names it. There are no roles (no lead, art or support
files). Both Claude accounts use the same file. Edit it with Write or Edit
after any turn that changed files or git. Never commit it.

## What it says

Current state only, no log, at most 80 lines, under these headings: State,
Task, Where things are, Unfinished, Next, Open questions, Gotchas.

- **State:** working (only while a job you launched is still running, named),
  awaiting director, blocked or available.
- **Where things are / Unfinished:** per PR or task, the branch, head commit,
  worktree path, what's left and what it waits on (CI, a W7 review, the
  director's look); running Actions run ids and local PIDs and what to do with
  their results.
- **Open questions:** the director's decisions not yet in the roadmap, in his
  words where it matters. Ask him anything that waits on him directly; never
  leave "awaits his yes" in the file.
- **Next:** your next items in order, so a fresh session doesn't sit idle.
- **Gotchas:** anything learnt the hard way that the next session would
  otherwise repeat.

## Starting a session from one

Read, in this order:
1. the handoff;
2. CLAUDE.md (it loads the bible, the roadmap index and open requirements);
3. only the roadmap sections your open work names, by offset rather than whole.

Then check that each PR in the handoff still matches GitHub (merged? red?),
and carry on from Next.

## Learnings

Proven findings for this project live in `references/learnings.md`. Read it before using this
skill; add to it only what proved effective, with evidence.
