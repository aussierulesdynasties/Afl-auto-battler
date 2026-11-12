#!/usr/bin/env bash
# The Godot-free checks CI runs in its lint and plan jobs, in about 40 s, before a push:
# the static lints with gdlint over every file (as CI does), the build-number source, the
# suite seeds, and the docs/TODO.md rule. Then it names the Godot suites CI will pick for
# this branch, so you can run exactly those first (tools/run_tests.sh <suites>, or through
# C:/kt/test_slot.sh on the shared PC). Each of these failed PR runs on CI 2026-11-04..11.
#
#   tools/prepush.sh                 # against origin/main
#   BASE=origin/foo tools/prepush.sh
#   ALLOW_TODO=1 tools/prepush.sh    # a roadmap PR that really edits docs/TODO.md
#
# As a git hook (once per clone; every worktree shares it):
#   cp tools/hooks/pre-push "$(git rev-parse --git-common-dir)/hooks/pre-push"
cd "$(dirname "$0")/.." || exit 1
BASE="${BASE:-origin/main}"
fail=0
step() { echo "== $1"; }

step "static lints (gdlint on every file, as CI)"
python3 -I tools/lint/lint.py || fail=1

step "build number has one source"
python3 -I tools/check_version.py || fail=1

step "no suite starts from the clock"
bash tools/check_suite_seeds.sh || fail=1

mb=$(git merge-base "$BASE" HEAD 2>/dev/null || echo "$BASE")
files=$(git diff --name-only --no-renames "$mb" HEAD)
if printf '%s\n' "$files" | grep -qx 'docs/TODO.md' && [ "${ALLOW_TODO:-0}" != 1 ]; then
	echo "docs/TODO.md is edited: write 'Closes row N' in the PR body instead, or label the PR 'roadmap' and push with ALLOW_TODO=1."
	fail=1
fi

if [ -n "$files" ]; then
	step "suites CI will run for this branch"
	# shellcheck disable=SC2086
	python3 tools/select_suites.py --files $files || true
fi

if [ "$fail" = 0 ]; then echo "prepush: ok"; else echo "prepush: FAILED (fix before pushing; CI would fail the same way)"; fi
exit "$fail"
