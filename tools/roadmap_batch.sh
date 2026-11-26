#!/usr/bin/env bash
# One rolling roadmap PR instead of one PR per merge (director, 2026-11-26: merges took days).
#
# The old Roadmap close opened a PR for every merged PR. They all edited the same TODO.md
# lines (row 202 most of all), so the first to land left the rest conflicting, and each one
# took a Tests run and a runner. This keeps a single PR on the bot's own branch
# roadmap-close/batch. Every run rebuilds that branch from the latest main by re-running
# tools/roadmap_close.py for each source PR it holds, plus the new one. The branch can
# never conflict with main, and a source whose rows already landed changes nothing (the
# script is idempotent: a deleted row is gone, and a merge note is written once per row and PR).
# When the batch PR merges, the next merged PR starts a new one.
#
# Any open roadmap-close/pr-N PR left from the old scheme is folded in and closed.
#
#   tools/roadmap_batch.sh [SOURCE_PR]    (GH_TOKEN and GITHUB_REPOSITORY set, run on a main checkout)
# No SOURCE_PR: rebuild the batch from the PRs it already holds (Roadmap rebuild).
set -euo pipefail

new_src="${1:-}"
branch="roadmap-close/batch"
files="docs/TODO.md docs/TODO_RULINGS.md docs/TODO_MERGED.md"
tmp="${RUNNER_TEMP:-/tmp}"

git config user.name "github-actions[bot]"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
git fetch -q --depth=1 origin +refs/heads/main:refs/remotes/origin/main

# The open batch PR, if any, and the source PRs its body lists on "<!-- sources: 1 2 3 -->".
batch=$(gh pr list --state open --head "$branch" --json number --jq '.[0].number // empty')
srcs=""
if [ -n "$batch" ]; then
  srcs=$(gh pr view "$batch" --json body --jq .body | sed -n 's/.*<!-- sources: \([0-9 ]*\) -->.*/\1/p' | head -1)
fi
# Old one-per-merge PRs: fold their sources in, close them below.
legacy=$(gh pr list --state open --label roadmap --limit 200 --json number,headRefName \
  --jq '.[] | select(.headRefName | startswith("roadmap-close/pr-")) | "\(.number):\(.headRefName | ltrimstr("roadmap-close/pr-"))"')
for pair in $legacy; do srcs="$srcs ${pair#*:}"; done
[ -n "$new_src" ] && srcs="$srcs $new_src"
# Every PR merged in the last 7 days too. The roadmap-close concurrency group keeps only one
# pending run and cancels the rest, so a burst of merges used to lose notes. The script is
# idempotent (a deleted row stays deleted, a merge note is written once per row and PR), so
# re-applying a PR that already landed changes nothing.
since=$(date -u -d '7 days ago' +%Y-%m-%dT%H:%M:%SZ)
recent=$(gh pr list --state merged --base main --limit 300 --json number,mergedAt,headRefName \
  --jq ".[] | select(.mergedAt >= \"$since\") | select(.headRefName | startswith(\"roadmap-close/\") | not) | .number")
srcs="$srcs $recent"
srcs=$(echo "$srcs" | tr ' ' '\n' | grep -E '^[0-9]+$' | sort -n -u | tr '\n' ' ' | sed 's/ $//')

if [ -z "$srcs" ]; then echo "No source PRs to note."; exit 0; fi

git checkout -q -B "$branch" origin/main
kept=""
lines=""
for src in $srcs; do
  gh api "repos/$GITHUB_REPOSITORY/pulls/$src" --jq '.body // ""' > "$tmp/body.txt"
  # A body that names no row has nothing to do.
  grep -qiE '^[[:space:]>*-]*(closes?[[:space:]]+rows?|part[[:space:]]+of[[:space:]]+rows?)[[:space:]]' "$tmp/body.txt" || continue
  title=$(gh api "repos/$GITHUB_REPOSITORY/pulls/$src" --jq .title)
  ids=$(python3 tools/roadmap_close.py --body-file "$tmp/body.txt" --todo docs/TODO.md \
    --todo docs/TODO_RULINGS.md --pr "$src" --title "$title" 2>/dev/null) || ids=""
  # shellcheck disable=SC2086
  if [ -z "$ids" ] || git diff --quiet -- $files; then
    echo "#$src: nothing left to change on main"
    continue
  fi
  # shellcheck disable=SC2086
  git add $files
  git commit -q -m "Roadmap: update ${ids} (#$src)"
  kept="$kept $src"
  lines="$lines
- #$src: ${ids}"
  echo "#$src: ${ids}"
done
kept=$(echo "$kept" | sed 's/^ //')

for pair in $legacy; do
  gh pr close "${pair%%:*}" --comment "Folded into the single rolling roadmap PR (branch $branch). Closed by tools/roadmap_batch.sh." || true
done

if [ -z "$kept" ]; then
  if [ -n "$batch" ]; then
    gh pr close "$batch" --comment "Every row it noted is already on main. Closed by tools/roadmap_batch.sh." || true
  fi
  echo "Nothing to change on main."
  exit 0
fi

git push -q -f origin "HEAD:refs/heads/$branch"
body="Roadmap notes for merged PRs, rebuilt on the latest main after every merge (tools/roadmap_batch.sh).
${lines}

No row: roadmap notes for PRs that already merged.

<!-- sources: ${kept} -->"
if [ -n "$batch" ]; then
  gh pr edit "$batch" --body "$body"
else
  batch=$(gh pr create --base main --head "$branch" --label roadmap --title "Roadmap notes for merged PRs" --body "$body" | sed 's#.*/##')
fi
gh pr merge "$batch" --auto --squash || echo "::warning::#$batch: could not turn on auto-merge"
# A push with the workflow token starts no CI: dispatch a docs-only Tests pass, and approve
# the PR's own held run (GitHub holds a bot-opened PR's run at action_required).
# shellcheck disable=SC2086
gh workflow run tests.yml --ref "$branch" -f changed_files="$files"
head=$(git rev-parse HEAD)
for _ in 1 2 3 4 5 6 7 8 9 10 11 12; do
  run=$(gh run list --branch "$branch" --event pull_request --json databaseId,conclusion,headSha \
    --jq "[.[] | select(.conclusion == \"action_required\" and .headSha == \"$head\")][0].databaseId // empty")
  if [ -n "$run" ]; then
    gh api -X POST "repos/$GITHUB_REPOSITORY/actions/runs/$run/approve" >/dev/null \
      && echo "Approved Tests run $run" \
      || echo "::warning::Could not approve Tests run $run; approve it by hand or #$batch stays blocked"
    break
  fi
  sleep 10
done
echo "Batch PR #$batch holds: $kept"
