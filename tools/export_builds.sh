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
git rev-parse --short=7 HEAD > build_info.txt

"$GODOT" --headless --path "$ROOT" --import >/dev/null 2>&1 || true

mkdir -p builds
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
		export_one "Web" "builds/web/index.html"
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
exit $failed
