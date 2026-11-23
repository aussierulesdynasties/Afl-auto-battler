#!/usr/bin/env bash
# Purge the Epic/MetaHuman files from this repo's history (director's decision 2026-11-23;
# docs/EPIC_ASSETS.md, "The old copies in git history"). Irreversible once pushed.
#
#   tools/epic_purge.sh rewrite WORKDIR     # fresh bare clone of every branch, strip the blobs, verify
#   tools/epic_purge.sh push WORKDIR        # force-push every rewritten branch (with leases)
#
# rewrite: clones every branch (not GitHub's refs/pull/*), removes exactly the blob ids in
# tools/epic_blobs.txt with git filter-repo (pip install git-filter-repo), keeps every commit
# (even one left empty) and every message, then checks: no listed blob is left, and every
# branch tip's tree is unchanged unless it held one of the files.
# push: pushes each rewritten branch with --force-with-lease set to the value it had when
# cloned, so a branch somebody pushed to since then is refused (and listed), never lost.
# Main's ruleset must let the pusher force-push (an admin bypass, or the rule off for the push).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPO="${PURGE_REPO:-https://github.com/aussierulesdynasties/Afl-auto-battler}"
cmd="${1:?rewrite or push}"
WORK="${2:?work directory}"

case "$cmd" in
rewrite)
	[ ! -e "$WORK" ] || { echo "FAIL: $WORK exists; use a new directory" >&2; exit 1; }
	command -v git-filter-repo >/dev/null 2>&1 || git filter-repo --version >/dev/null 2>&1 \
		|| { echo "FAIL: git filter-repo is not installed (pip install git-filter-repo)" >&2; exit 1; }
	git clone --bare "$REPO" "$WORK"
	grep -oE '^[0-9a-f]{40}' "$ROOT/tools/epic_blobs.txt" > "$WORK/epic_ids.txt"
	echo "$(wc -l < "$WORK/epic_ids.txt") blob ids to strip"
	# Before: each branch's tip and tree, and whether its tip holds an Epic blob.
	git -C "$WORK" for-each-ref --format='%(refname) %(objectname) %(objectname)^{tree}' refs/heads \
		| while read -r ref sha tree; do
			echo "$ref $sha $(git -C "$WORK" rev-parse "$tree")"
		done > "$WORK/before.txt"
	git -C "$WORK" filter-repo --strip-blobs-with-ids "$WORK/epic_ids.txt" \
		--prune-empty never --prune-degenerate never --force
	# Check 1: no listed blob is reachable from any branch.
	left="$(git -C "$WORK" rev-list --objects --all | grep -cFf "$WORK/epic_ids.txt" || true)"
	[ "$left" = 0 ] || { echo "FAIL: $left Epic blob(s) still reachable" >&2; exit 1; }
	# Check 2: a tip's tree changes only where the tip itself held an Epic file.
	changed=0 bad=0
	while read -r ref old tree; do
		new_tree="$(git -C "$WORK" rev-parse "$ref^{tree}")"
		[ "$new_tree" = "$tree" ] && continue
		changed=$((changed + 1))
		if ! git -C "$WORK" ls-tree -r "$old" 2>/dev/null | grep -qFf "$WORK/epic_ids.txt"; then
			echo "FAIL: $ref tree changed though its tip held no Epic file" >&2; bad=$((bad + 1))
		fi
	done < "$WORK/before.txt"
	[ "$bad" = 0 ] || exit 1
	echo "OK: no Epic blob left in $(wc -l < "$WORK/before.txt") branches; $changed tips lost only Epic files"
	echo "Next: tools/epic_purge.sh push $WORK"
	;;
push)
	[ -f "$WORK/before.txt" ] || { echo "FAIL: run rewrite first" >&2; exit 1; }
	git -C "$WORK" remote get-url origin >/dev/null 2>&1 || git -C "$WORK" remote add origin "$REPO"
	failed=0 n=0 args=()
	flush() {
		[ ${#args[@]} -gt 0 ] || return 0
		if ! git -C "$WORK" push --porcelain origin "${args[@]}" > "$WORK/push.log" 2>&1; then
			failed=1
		fi
		grep -E '^!' "$WORK/push.log" || true
		args=()
	}
	while read -r ref old _tree; do
		new="$(git -C "$WORK" rev-parse "$ref")"
		[ "$new" = "$old" ] && continue  # the branch never held an Epic file
		args+=("--force-with-lease=$ref:$old" "$new:$ref")  # no "+": it would override the lease
		n=$((n + 1))
		[ ${#args[@]} -ge 60 ] && flush  # stay under Windows' command-line limit
	done < "$WORK/before.txt"
	flush
	echo "$n branch(es) pushed"
	[ "$failed" = 0 ] || { echo "Some pushes were refused (lines starting with !): those branches moved since the clone; re-run rewrite for them." >&2; exit 1; }
	;;
*) sed -n '2,15p' "$0"; exit 2 ;;
esac
