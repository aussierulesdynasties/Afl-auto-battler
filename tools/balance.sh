#!/usr/bin/env bash
# Local balance harness: N seeded matches over parallel headless Godot workers,
# optionally paired against a second arm, then a one-page report against real
# AFL 2026 team rates. See tools/balance/README.md.
#
#   tools/balance.sh match 1000                         # one arm
#   tools/balance.sh match 1000 --a "--weather wet" --b "--weather perfect"
#   tools/balance.sh match 1000 --a-root ../main-checkout --b ""  # paired: main (another checkout) vs this branch
# Env: GODOT (binary), JOBS (workers, default cores-2), OUT (run dir).
set -euo pipefail
mode="${1:-match}"; n="${2:-1000}"; shift $(( $# >= 2 ? 2 : $# ))
arm_a=""; arm_b=""; paired=0; root_a=""
while [ $# -gt 0 ]; do
  case "$1" in
    --a) arm_a="$2"; shift 2 ;;
    --b) arm_b="$2"; paired=1; shift 2 ;;
    --a-root) root_a="$2"; shift 2 ;;
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
# Always import: a checkout that merged main has new classes its old class list lacks,
# and every worker would then run with its autoloads broken.
"$godot" --headless --path "$root" --editor --import >/dev/null 2>&1 || true
start=$(date +%s)
root_a="${root_a:+$(cd "$root_a" && pwd)}"
[ -z "$root_a" ] || "$godot" --headless --path "$root_a" --editor --import >/dev/null 2>&1 || true
run_arm() { # name, extra args, project root
  local name="$1" extra="$2" proj="${3:-$root}" per=$(( (n + jobs - 1) / jobs )) w=0 from=0
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
run_arm a "$arm_a" "${root_a:-$root}"
[ "$paired" = 1 ] && run_arm b "$arm_b"
wait
secs=$(( $(date +%s) - start ))
for l in "$out"/*.log; do grep -q "SCRIPT ERROR\|Parse Error" "$l" && { echo "worker failed: $l"; tail -20 "$l"; exit 1; }; done
args=(--run "$out" --n "$n" --secs "$secs" --a "${arm_a:-base}${root_a:+ @ $(basename "$root_a")}")
[ "$paired" = 1 ] && args+=(--b "${arm_b:-this checkout}")
python "$root/tools/balance/balance_report.py" "${args[@]}" | tee "$out/report.md"
