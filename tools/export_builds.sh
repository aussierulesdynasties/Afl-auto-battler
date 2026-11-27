#!/usr/bin/env bash
# Export the itch builds into builds/: Windows, Android (release APK) and, if asked, Web.
#
#   tools/export_builds.sh                 # windows android
#   tools/export_builds.sh windows         # one platform
#   tools/export_builds.sh windows android web
#
# Stamps build_info.txt with the short commit first, as the Web build workflow does, so the
# menu label reads "<config/version> (<sha7>)" in every build. Prints each artifact, its size
# and the butler --userversion (<version>-<sha7>), also written to builds/version.txt. docs/ITCH_UPLOAD.md has the butler commands.
#
# Env:
#   GODOT                  Godot 4.7.2 console exe (default: the one on the Desktop)
#   ARD_KEYSTORE           release keystore (default ~/.keys/ard-release.keystore)
#   ARD_KEYSTORE_PASS_FILE file holding its password (default ~/.keys/ard-release.pass)
#   ARD_KEYSTORE_ALIAS     key alias (default ard)
#   ALLOW_DIRTY=1          export with uncommitted tracked changes (local tries only; never upload
#                          such a build: its label names a commit that does not match its contents)
# The keystore and password never go in the repo or export_presets.cfg: Godot reads them
# from GODOT_ANDROID_KEYSTORE_RELEASE_PATH/_USER/_PASSWORD, set here for the Godot process only.
# The Android export also needs the Android SDK path in Godot's editor settings.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
GODOT="${GODOT:-/c/Users/DANTE/Desktop/Godot_v4.7.2-stable_win64.exe/Godot_v4.7.2-stable_win64_console.exe}"
KEYSTORE="${ARD_KEYSTORE:-$HOME/.keys/ard-release.keystore}"
PASS_FILE="${ARD_KEYSTORE_PASS_FILE:-$HOME/.keys/ard-release.pass}"
ALIAS="${ARD_KEYSTORE_ALIAS:-ard}"

platforms=("$@")
[ ${#platforms[@]} -eq 0 ] && platforms=(windows android)

version="$(sed -n 's/^config\/version="\([^"]*\)".*/\1/p' project.godot | head -1)"
sha="$(git rev-parse --short=7 HEAD)"
[ -n "$version" ] || { echo "project.godot has no config/version" >&2; exit 1; }
# The label names HEAD, so the tree must be HEAD. *.import files only churn line endings here.
dirty="$(git status --porcelain --untracked-files=no -- . ':!*.import')"
if [ -n "$dirty" ] && [ "${ALLOW_DIRTY:-0}" != "1" ]; then
	echo "FAIL: uncommitted changes; the build would be labelled $sha without them:" >&2
	echo "$dirty" >&2
	echo "Commit them, or set ALLOW_DIRTY=1 for a local try that is never uploaded." >&2
	exit 1
fi
git rev-parse --short=7 HEAD > build_info.txt

# The MetaHuman body, crew, guernsey cuts, skin and heads live in a private repo (docs/EPIC_ASSETS.md):
# a build without them would have no players, so copy them in and refuse to go on without them.
bash tools/epic_assets.sh fetch
# The ground models too (docs/GROUND_ASSETS.md): the Android and Windows builds carry every ground.
bash tools/ground_assets.sh fetch

mkdir -p builds
if ! "$GODOT" --headless --path "$ROOT" --import > builds/import.log 2>&1; then
	echo "WARNING: the asset import failed; stale assets may be exported (builds/import.log):" >&2
	tail -20 builds/import.log >&2
fi

# A build ships the years without you as the sim stands now (row 137).
if ! "$GODOT" --headless --path "$ROOT" --script tools/histories/generate.gd -- --check | tail -3; then
	echo "FAIL: the pre-made histories are behind the code: run tools/histories/regen.sh and commit them." >&2
	[ "${ALLOW_DIRTY:-0}" = "1" ] || exit 1
fi

echo "$version-$sha" > builds/version.txt

failed=0
report=()
export_one() {
	local preset="$1" out="$2"
	mkdir -p "$(dirname "$out")"
	rm -f "$out"
	echo "== export $preset -> $out"
	if "$GODOT" --headless --path "$ROOT" --export-release "$preset" "$ROOT/$out" && [ -s "$out" ]; then
		report+=("$out $(du -h "$out" | cut -f1)")
	else
		echo "FAIL: $preset export did not produce $out" >&2
		failed=1
	fi
}

for p in "${platforms[@]}"; do
	case "$p" in
	windows)
		rm -rf builds/windows
		export_one "Windows Desktop" "builds/windows/AussieRulesDynasties.exe"
		;;
	android)
		if [ ! -f "$KEYSTORE" ] || [ ! -f "$PASS_FILE" ]; then
			echo "FAIL: release keystore or password file missing ($KEYSTORE, $PASS_FILE); see docs/ITCH_BUILDS.md" >&2
			failed=1
			continue
		fi
		# The password reaches Godot through its environment only; it is never printed.
		export GODOT_ANDROID_KEYSTORE_RELEASE_PATH="$KEYSTORE"
		export GODOT_ANDROID_KEYSTORE_RELEASE_USER="$ALIAS"
		GODOT_ANDROID_KEYSTORE_RELEASE_PASSWORD="$(cat "$PASS_FILE")"
		export GODOT_ANDROID_KEYSTORE_RELEASE_PASSWORD
		export_one "Android" "builds/android/aussie-rules-dynasties.apk"
		unset GODOT_ANDROID_KEYSTORE_RELEASE_PATH GODOT_ANDROID_KEYSTORE_RELEASE_USER GODOT_ANDROID_KEYSTORE_RELEASE_PASSWORD
		;;
	web)
		rm -rf builds/web
		# The textures go in one pack per graphics family and the page fetches only its browser's,
		# so no file passes itch's 200 MB limit (tools/web_texture_packs.py).
		echo "== export Web, its main pack and two texture packs -> builds/web"
		PY="$(command -v python || command -v python3)"
		if "$PY" tools/web_texture_packs.py "$GODOT" builds/web; then
			report+=("builds/web $(du -sh builds/web | cut -f1)")
		else
			echo "FAIL: the Web export did not finish (tools/web_texture_packs.py)" >&2
			failed=1
		fi
		;;
	*)
		echo "unknown platform: $p (windows, android, web)" >&2
		failed=1
		;;
	esac
done

echo
echo "Version: $version-$sha"
for line in "${report[@]}"; do echo "  $line"; done
# The size ceilings (docs/ITCH_BUILDS.md, "What each build carries"): the APK carries every
# stadium (director, 2026-11-23) and an APK is a zip, which needs zip64 past 4 GB.
over_budget() {
	local f="$1" limit_mb="$2" mb
	[ -f "$f" ] || return 0
	mb=$(( $(stat -c %s "$f" 2>/dev/null || wc -c < "$f") / 1000000 ))
	if [ "$mb" -gt "$limit_mb" ]; then
		echo "WARNING: $f is $mb MB, over its $limit_mb MB ceiling (docs/ITCH_BUILDS.md, \"What each build carries\")" >&2
	fi
}
over_budget builds/android/aussie-rules-dynasties.apk 3800
over_budget builds/windows/AussieRulesDynasties.exe 2000
exit $failed
