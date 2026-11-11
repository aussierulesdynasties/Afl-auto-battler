#!/usr/bin/env bash
# Times tools/perf/weeks_bench.gd on several commits, one after another on this machine, so code
# states compare on the same hardware (run_on_github.yml, what=bench). Rounds interleave (a b c a b c).
# Each ref gets this checkout's bench copied in (older trees lack it) and a fresh user:// per run.
#   REFS="<sha> <sha>" REPS=2 ARGS="--plain" GODOT=godot OUT=/tmp/bench tools/perf/bench_refs.sh
# ARGS with --laps also times each statement of the functions in tools/perf/laps_targets.txt
# (LAP lines; see lap_instrument.py). Use it with --plain so old and new trees time the same way.
# Needs full history (fetch-depth 0). Writes OUT/table.md, OUT/r<round>-<n>.log and the step summary.
set -euo pipefail
: "${REFS:?REFS: refs separated by spaces}"
REPS="${REPS:-1}"
ARGS="${ARGS:-}"
GODOT="${GODOT:-godot}"
OUT="${OUT:-${RUNNER_TEMP:-/tmp}/bench}"
if ! [[ "$REFS" =~ ^[A-Za-z0-9._/-]+( [A-Za-z0-9._/-]+)*$ ]]; then echo "refs must be separated by single spaces" >&2; exit 1; fi
if ! [[ "$REPS" =~ ^[1-5]$ ]]; then echo "reps must be 1-5" >&2; exit 1; fi
if ! [[ "$ARGS" =~ ^[A-Za-z0-9\ _-]*$ ]]; then echo "bench args: letters, digits, spaces, - and _ only" >&2; exit 1; fi
here="$(pwd)"
trees="$(mktemp -d)"
mkdir -p "$OUT"
: > "$OUT/trees.txt"
i=0
for ref in $REFS; do
	i=$((i + 1))
	sha=$(git rev-parse --verify -q "$ref^{commit}" || git rev-parse --verify "origin/$ref^{commit}")
	dir="$trees/tree-$i"
	git worktree add -q --detach "$dir" "$sha"
	mkdir -p "$dir/tools/perf"
	cp "$here/tools/perf/weeks_bench.gd" "$here/tools/perf/weeks_bench_impl.gd" "$dir/tools/perf/"
	if [[ " $ARGS " == *" --laps "* ]]; then
		# Step timers in this throwaway tree only (lap_instrument.py, laps_targets.txt).
		cp "$here/tools/perf/perf_lap.gd" "$dir/tools/perf/"
		python3 "$here/tools/perf/lap_instrument.py" "$dir" "$here/tools/perf/laps_targets.txt" | tee "$OUT/laps-$i.txt"
	fi
	echo "$i $ref ${sha:0:8}" >> "$OUT/trees.txt"
	timeout 900 "$GODOT" --headless --path "$dir" --editor --import > "$OUT/import-$i.log" 2>&1 || true
done
cat "$OUT/trees.txt"
{ echo "| round | ref | commit | weeks | off-season | wall s | hash all |"; echo "|---|---|---|---|---|---|---|"; } > "$OUT/table.md"
for rep in $(seq 1 "$REPS"); do
	while read -r n ref sha; do
		log="$OUT/r${rep}-${n}.log"
		t0=$(date +%s)
		# shellcheck disable=SC2086
		XDG_DATA_HOME="$trees/data-$rep-$n" timeout 3600 "$GODOT" --headless --path "$trees/tree-$n" \
			--script res://tools/perf/weeks_bench.gd -- $ARGS > "$log" 2>&1 || true
		wall=$(( $(date +%s) - t0 ))
		echo "== round $rep, $ref ($sha), ${wall} s"
		grep -E '^(PERF|HASH|NOTE|LAP)' "$log" || tail -n 40 "$log"
		line=$(grep -E '^PERF weeks ' "$log" || true)
		weeks=$(echo "$line" | sed -nE 's/^PERF weeks ([0-9.]+) s over ([0-9]+) weeks.*/\1 s (\2 wk)/p')
		off=$(echo "$line" | sed -nE 's/.*off-season ([0-9.]+) s.*/\1 s/p')
		hash=$(grep -E '^HASH all ' "$log" | awk '{print substr($3,1,12)}' || true)
		echo "| $rep | $ref | $sha | ${weeks:-failed} | ${off} | $wall | ${hash} |" >> "$OUT/table.md"
		if [[ " $ARGS " == *" --laps "* ]] && [ -f "$trees/tree-$n/tools/perf/match_bench.gd" ]; then
			# One match at a time on one thread, the same fixtures and seeds: is the engine itself slower?
			XDG_DATA_HOME="$trees/mdata-$rep-$n" timeout 1800 "$GODOT" --headless --path "$trees/tree-$n" 				--script res://tools/perf/match_bench.gd -- --n 40 > "$OUT/m${rep}-${n}.log" 2>&1 || true
			grep -E '^PERF' "$OUT/m${rep}-${n}.log" | sed "s/^/MATCH $ref /" || tail -n 20 "$OUT/m${rep}-${n}.log"
		fi
	done < "$OUT/trees.txt"
done
cat "$OUT/table.md"
if [ -n "${GITHUB_STEP_SUMMARY:-}" ]; then
	{ echo "Runner: $(nproc) cores,$(grep -m1 'model name' /proc/cpuinfo | cut -d: -f2)"; echo; cat "$OUT/table.md"; } >> "$GITHUB_STEP_SUMMARY"
fi
