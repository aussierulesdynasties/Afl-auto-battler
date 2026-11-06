#!/usr/bin/env bash
# Performance baseline on this machine with the Mobile renderer, offscreen.
# Usage: GODOT=/path/to/godot tools/perf/run_baseline.sh [out-file] [baseline.gd args]
#   --screens: only the screens that carry the team oval (Awards tab, team view,
#   My list), early and late season; PASSES=1 runs the process once.
# Runs the Godot process twice so the launch time is reported cold (first run
# after the file cache has been used by something else) and again warm. Uses a
# scratch save folder and an untracked override.cfg that keeps the window off
# screen and unfocused; the override is removed afterwards.
set -e
cd "$(dirname "$0")/../.."
GODOT=${GODOT:?set GODOT to the Godot 4.7 executable}
out=${1:-perf_baseline.txt}
shift || true
passes=${PASSES:-2}
export APPDATA="$(cygpath -w "${TEMP:-/tmp}")/perfapp"
mkdir -p "$APPDATA" 2>/dev/null || true
[ -e override.cfg ] && { echo "override.cfg exists; move it aside first"; exit 1; }
cat > override.cfg <<'C'
[display]
window/size/viewport_width=540
window/size/viewport_height=960
window/size/no_focus=true
window/size/initial_position_type=0
window/size/initial_position=Vector2i(-20000, -20000)
C
trap 'rm -f override.cfg' EXIT
for pass in $(seq 1 "$passes"); do
	start=$(date +%s%N)
	"$GODOT" --path . --rendering-method mobile --script tools/perf/baseline.gd -- --out "$out.$pass" "$@" > "$out.$pass.log" 2>&1 || true
	end=$(date +%s%N)
	echo "PERF process $pass: $(( (end - start) / 1000000 )) ms start to quit" | tee -a "$out.$pass"
done
for pass in $(seq 1 "$passes"); do cat "$out.$pass"; done > "$out"
echo "wrote $out"
