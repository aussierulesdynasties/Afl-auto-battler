#!/usr/bin/env bash
# Regenerate every pre-made history from the current sim. Needs GODOT.
# Run after any merge that changes tuning, signing, lists or the save format.
set -u
JOBS="${JOBS:-3}"
cd "$(dirname "$0")/../.."
for first in 2030 2028; do for names in real fict; do for n in 0 1; do
	echo "$first $names $n"
done; done; done | xargs -P "$JOBS" -L 1 sh -c \
	'"$GODOT" --headless --path . --script tools/histories/generate.gd -- "$0" "$1" "$2" 2>&1 | grep -E "WROTE|SCRIPT ERROR"'
du -ch data/histories/*.hist | tail -9
"$GODOT" --headless --path . --script tools/histories/generate.gd -- --check | tail -3
exit "${PIPESTATUS[0]}"
