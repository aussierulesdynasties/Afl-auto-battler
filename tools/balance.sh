#!/usr/bin/env bash
# Local balance harness: N seeded matches over parallel headless Godot workers,
# optionally paired against a second arm, then a one-page report against real
# AFL 2026 team rates. See tools/balance/README.md.
#
#   tools/balance.sh match 1000                         # one arm
#   tools/balance.sh match 1000 --b "--on clanger_cause" # paired: base vs B
#   tools/balance.sh match 1000 --a "--weather wet" --b "--weather perfect"
# Env: GODOT (binary), JOBS (workers, default cores-2), OUT (run dir).
set -euo pipefail
mode="${1:-match}"; n="${2:-1000}"; shift $(( $# >= 2 ? 2 : $# ))
arm_a=""; arm_b=""; paired=0; a_root=""
while [ $# -gt 0 ]; do
  case "$1" in
    --a) arm_a="$2"; shift 2 ;;
    --b) arm_b="$2"; paired=1; shift 2 ;;
    --a-root) a_root="$2"; shift 2 ;;
    *) echo "unknown arg $1"; exit 2 ;;
  esac
done
[ "$mode" = "match" ] || { echo "modes: match"; exit 2; }
root="$(cd "$(dirname "$0")/.." && pwd)"
godot="${GODOT:-godot}"
cores="$(nproc 2>/dev/null || echo 4)"
jobs="${JOBS:-$(( cores > 3 ? cores - 2 : 1 ))}"
out="${OUT:-$root/.balance/$(date +%Y%m%d-%H%M%S)}"
mkdir -p "$out"; touch "$out/.gdignore"
# Arm A may play from another checkout (main against the branch); B always plays from this one.
root_a="$root"
if [ -n "$a_root" ]; then
  [ -f "$a_root/project.godot" ] || { echo "--a-root: no project.godot in $a_root"; exit 2; }
  root_a="$(cd "$a_root" && pwd)"; paired=1
fi
for r in "$root_a" "$root"; do
  [ -d "$r/.godot/imported" ] || "$godot" --headless --path "$r" --editor --import >/dev/null 2>&1 || true
done
start=$(date +%s)
run_arm() { # name, extra args, project root
  local name="$1" extra="$2" proj="$3" per=$(( (n + jobs - 1) / jobs )) w=0 from=0
  while [ "$from" -lt "$n" ]; do
    local c=$(( n - from < per ? n - from : per ))
    local ad="$out/appdata_${name}_$w"; mkdir -p "$ad"
    local f; f="$(cd "$out" && pwd -W 2>/dev/null || pwd)/${name}_$w.jsonl"
    echo "project: $proj" >"$out/${name}_$w.log"
    # shellcheck disable=SC2086
    APPDATA="$(cygpath -w "$ad" 2>/dev/null || echo "$ad")" "$godot" --headless --path "$proj" \
      --script res://tools/balance/balance_worker.gd -- --from "$from" --count "$c" --out "$f" $extra \
      >>"$out/${name}_$w.log" 2>&1 &
    from=$(( from + c )); w=$(( w + 1 ))
  done
}
run_arm a "$arm_a" "$root_a"
[ "$paired" = 1 ] && run_arm b "$arm_b" "$root"
wait
secs=$(( $(date +%s) - start ))
for l in "$out"/*.log; do grep -q "SCRIPT ERROR\|Parse Error" "$l" && { echo "worker failed: $l"; tail -20 "$l"; exit 1; }; done
args=(--run "$out" --n "$n" --secs "$secs" --a "${arm_a:-base}${a_root:+ (from $a_root)}")
[ "$paired" = 1 ] && args+=(--b "$arm_b")
python "$root/tools/balance/balance_report.py" "${args[@]}" | tee "$out/report.md"
