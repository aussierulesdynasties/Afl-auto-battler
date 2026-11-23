#!/usr/bin/env bash
# Bug bash sweep: one whole 3D match per line of a plan file (club seed ground weather time quality speed),
# two at a time. Logs to $OUT/<n>.log.   tools/bugbash3d/sweep.sh PLAN OUT [JOBS]
PLAN="$1"; OUT="$2"; JOBS="${3:-2}"
mkdir -p "$OUT"
n=0
while IFS='|' read -r club seed ground weather time quality speed; do
	[ -z "$club" ] && continue
	n=$((n+1))
	echo "$n|$club|$seed|$ground|$weather|$time|$quality|$speed"
done < "$PLAN" | xargs -P "$JOBS" -I{} bash -c '
	IFS="|" read -r n club seed ground weather time quality speed <<< "{}"
	args=(--club "$club" --seed "$seed" --speed "$speed" --quality "$quality")
	[ -n "$ground" ] && args+=(--ground "$ground")
	[ -n "$weather" ] && args+=(--weather "$weather")
	[ -n "$time" ] && args+=(--time "$time")
	timeout 2400 godot --headless --fixed-fps 30 --path . --script tools/bugbash3d/play3d.gd -- "${args[@]}" > "'"$OUT"'/$n.log" 2>&1
	echo "exit $?" >> "'"$OUT"'/$n.log"
'
