#!/usr/bin/env bash
# Installs the Godot that CI uses (GODOT_VERSION in .github/workflows/tests.yml) and gdlint into a
# cloud Claude session, so it can run tools/run_tests.sh and tools/prepush.sh before pushing.
# Called by .claude/hooks/pr_guard.py start; about 10 s. Prints one line for the session.
set -u
cd "$(dirname "$0")/../.." || exit 0
ver=$(sed -n 's/^ *GODOT_VERSION: *"\([0-9.]*\)".*/\1/p' .github/workflows/tests.yml | head -1)
[ -n "$ver" ] || { echo "Godot not installed: no GODOT_VERSION in tests.yml."; exit 0; }
dir="$HOME/.local/godot-$ver"
bin="$dir/Godot_v${ver}-stable_linux.x86_64"
if [ ! -x "$bin" ]; then
	mkdir -p "$dir"
	curl -sSfL --retry 3 -o "$dir/g.zip" \
		"https://github.com/godotengine/godot/releases/download/${ver}-stable/Godot_v${ver}-stable_linux.x86_64.zip" \
		&& unzip -oq "$dir/g.zip" -d "$dir" && rm -f "$dir/g.zip"
fi
[ -x "$bin" ] || { echo "Godot $ver could not be downloaded; run tests on CI and watch them."; exit 0; }
mkdir -p "$HOME/.local/bin" && ln -sf "$bin" "$HOME/.local/bin/godot"
[ -n "${CLAUDE_ENV_FILE:-}" ] && echo "export GODOT=$bin PATH=\$HOME/.local/bin:\$PATH" >> "$CLAUDE_ENV_FILE"
python3 -m pip install -q -r tools/lint/requirements.txt >/dev/null 2>&1 || true
echo "Godot $ver is installed (godot on PATH, GODOT=$bin) and gdlint. The first suite run imports the project (several minutes); the 3D suites need the Epic files (docs/EPIC_ASSETS.md)."
