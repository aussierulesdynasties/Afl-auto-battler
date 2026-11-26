#!/usr/bin/env bash
# Epic/MetaHuman files live in a private repo, never in this public one (docs/EPIC_ASSETS.md).
#
#   tools/epic_assets.sh fetch               # copy the pinned files into place (skips files already right)
#   tools/epic_assets.sh check               # exit 1 unless every pinned file is in place and matches
#   tools/epic_assets.sh publish "msg" [PATH...]
#                                            # commit the working copies of the pinned files (and any new
#                                            # PATHs) to the private repo, push, and update the pin
#
# The pin is tools/epic_assets.lock: the private repo, its branch, one commit, and a sha256 per
# file. Every pinned path is in a .gitignore (assets/oval3d/.gitignore), and tools/check_epic_files.py fails CI if one is
# committed here. Access: EPIC_ASSETS_TOKEN (a GitHub token that can read the private repo; CI
# passes it from a repo secret), else your own git credentials for github.com.
# EPIC_ASSETS_CACHE (default ~/.cache/ard-epic-assets) holds the private repo's git objects.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOCK="$ROOT/tools/epic_assets.lock"
CACHE="${EPIC_ASSETS_CACHE:-$HOME/.cache/ard-epic-assets}"

field() { sed -n "s/^$1 //p" "$LOCK" | head -1; }
REPO="$(field repo)"
BRANCH="$(field branch)"
COMMIT="$(field commit)"
# "sha256  path" lines
entries() { grep -E '^[0-9a-f]{64}  ' "$LOCK"; }

sha_of() {
	if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | cut -d' ' -f1
	else shasum -a 256 "$1" | cut -d' ' -f1; fi
}

gitp() {
	if [ -n "${EPIC_ASSETS_TOKEN:-}" ]; then
		local basic
		basic="$(printf 'x-access-token:%s' "$EPIC_ASSETS_TOKEN" | base64 | tr -d '\n')"
		git -c "http.https://github.com/.extraheader=AUTHORIZATION: basic $basic" "$@"
	else
		git "$@"
	fi
}

cache_init() {
	if [ ! -d "$CACHE/.git" ]; then
		mkdir -p "$CACHE"
		git -C "$CACHE" init -q
		git -C "$CACHE" remote add origin "$REPO"
	fi
	git -C "$CACHE" remote set-url origin "$REPO"
}

# Every pinned file that is missing or differs from its pinned hash.
stale() {
	entries | while read -r sum path; do
		if [ ! -f "$ROOT/$path" ] || [ "$(sha_of "$ROOT/$path")" != "$sum" ]; then echo "$path"; fi
	done
}

cmd_fetch() {
	local todo
	todo="$(stale)"
	if [ -z "$todo" ]; then
		echo "epic assets: all $(entries | wc -l | tr -d ' ') files in place ($COMMIT)"
		return 0
	fi
	cache_init
	if ! git -C "$CACHE" cat-file -e "$COMMIT^{commit}" 2>/dev/null; then
		echo "epic assets: fetching $COMMIT from $REPO"
		if ! gitp -C "$CACHE" fetch -q --depth 1 origin "$COMMIT"; then
			echo "FAIL: could not fetch the Epic/MetaHuman files from $REPO." >&2
			echo "Set EPIC_ASSETS_TOKEN to a GitHub token that can read it, or sign in to GitHub as an" >&2
			echo "account with access (cloud Claude sessions: attach the repo first). docs/EPIC_ASSETS.md" >&2
			return 1
		fi
	fi
	local n=0
	while read -r path; do
		[ -n "$path" ] || continue
		mkdir -p "$ROOT/$(dirname "$path")"
		git -C "$CACHE" show "$COMMIT:$path" > "$ROOT/$path.tmp"
		mv "$ROOT/$path.tmp" "$ROOT/$path"
		n=$((n + 1))
	done <<< "$todo"
	echo "epic assets: copied $n file(s) from $COMMIT"
	cmd_check
}

cmd_check() {
	local bad
	bad="$(stale)"
	if [ -n "$bad" ]; then
		echo "FAIL: these Epic/MetaHuman files are missing or not the pinned version (run tools/epic_assets.sh fetch):" >&2
		echo "$bad" | sed 's/^/  /' >&2
		return 1
	fi
	echo "epic assets: OK ($(entries | wc -l | tr -d ' ') files, $COMMIT)"
}

cmd_publish() {
	local msg="${1:?publish needs a commit message}"
	shift
	local new=("$@") p
	for p in "${new[@]}"; do
		[ -f "$ROOT/$p" ] || { echo "FAIL: no such file: $p" >&2; return 1; }
	done
	cache_init
	gitp -C "$CACHE" fetch -q --depth 1 origin "$BRANCH"
	git -C "$CACHE" checkout -q -B "$BRANCH" FETCH_HEAD
	{ entries | cut -c67-; printf '%s\n' "${new[@]}"; } | sed '/^$/d' | sort -u > "$CACHE/.paths"
	while read -r p; do
		[ -f "$ROOT/$p" ] || { echo "FAIL: $p is pinned but not in this checkout (fetch first)" >&2; return 1; }
		mkdir -p "$CACHE/$(dirname "$p")"
		cp "$ROOT/$p" "$CACHE/$p"
	done < "$CACHE/.paths"
	git -C "$CACHE" add -A -- assets
	if git -C "$CACHE" diff --cached --quiet; then
		echo "epic assets: nothing changed"
	else
		git -C "$CACHE" commit -q -m "$msg"
		gitp -C "$CACHE" push -q origin "HEAD:$BRANCH"
	fi
	local head
	head="$(git -C "$CACHE" rev-parse HEAD)"
	{
		grep -E '^(#|repo |branch )' "$LOCK"
		echo "commit $head"
		while read -r p; do echo "$(sha_of "$ROOT/$p")  $p"; done < "$CACHE/.paths"
	} > "$LOCK.new"
	mv "$LOCK.new" "$LOCK"
	for p in "${new[@]}"; do
		# assets/oval3d/.gitignore holds the oval's Epic paths; anything else goes in the root one.
		if [ "${p#assets/oval3d/}" != "$p" ]; then
			grep -qxF "/${p#assets/oval3d/}" "$ROOT/assets/oval3d/.gitignore" || echo "/${p#assets/oval3d/}" >> "$ROOT/assets/oval3d/.gitignore"
		else
			grep -qxF "/$p" "$ROOT/.gitignore" || echo "/$p" >> "$ROOT/.gitignore"
		fi
		git -C "$ROOT" rm -q --cached --ignore-unmatch -- "$p"
	done
	echo "epic assets: pinned $head; commit tools/epic_assets.lock (and .gitignore if it changed)"
}

case "${1:-}" in
	fetch) cmd_fetch ;;
	check) cmd_check ;;
	publish) shift; cmd_publish "$@" ;;
	*) sed -n '2,15p' "$0"; exit 2 ;;
esac
