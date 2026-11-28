#!/usr/bin/env bash
# Measures the OVR weights (docs/RATING_REBUILD.md §3, Phase 4): per AFL position,
# +N on one attribute for every player there on side i % 2 (balance_body --bump),
# N matches against one shared unbumped run on the same seeds. The margin each
# attribute buys at a position, as a share of what that position's attributes buy
# together, is its weight (weights_report.py).
#
#   GODOT=<godot console exe> tools/balance/weights.sh 1000          # every position, every attribute
#   GODOT=... tools/balance/weights.sh 1000 Key_Defender              # one position
#   BUMP=10 OUT=.balance/w tools/balance/weights.sh 1000              # size and folder
#
# A finished pair is kept: rerunning the same OUT carries on where it stopped.
set -euo pipefail
n="${1:-1000}"; only="${2:-}"
root="$(cd "$(dirname "$0")/../.." && pwd)"
bump="${BUMP:-10}"
out="${OUT:-$root/.balance/$(date +%Y%m%d-%H%M%S)-weights}"
mkdir -p "$out"; touch "$out/.gdignore"
positions="Key_Defender Gen._Defender Midfielder Mid-Forward Gen._Forward Key_Forward Ruck"
[ -n "$only" ] && positions="$only"
keys="speed endurance strength work_rate kicking handballing marking contested_marking one_on_one contested_ball
goalkicking ruck vision reading_play pressure forward_craft discipline durability"
done_run() { ls "$1"/a_*.jsonl >/dev/null 2>&1 && [ "$(cat "$1"/a_*.jsonl | grep -c '}$')" -ge "$n" ]; }
start=$(date +%s)
if ! done_run "$out/base"; then
  OUT="$out/base" bash "$root/tools/balance.sh" match "$n" >"$out/base.log" 2>&1 \
    || { echo "base run failed: $out/base.log"; tail -20 "$out/base.log"; exit 1; }
  rm -rf "$out/base"/appdata_*
fi
for pos in $positions; do
  for k in $keys; do
    d="$out/${pos}__$k"
    done_run "$d" && continue
    OUT="$d" bash "$root/tools/balance.sh" match "$n" --a "--bump $pos:$k:$bump" >"$d.log" 2>&1 \
      || { echo "run failed: $d.log"; tail -20 "$d.log"; exit 1; }
    rm -rf "$d"/appdata_* "$d.log"
    echo "$(date +%H:%M:%S) $pos $k done ($(( $(date +%s) - start ))s)"
  done
done
python "$root/tools/balance/weights_report.py" --run "$out" --bump "$bump" | tee "$out/weights_report.md"
