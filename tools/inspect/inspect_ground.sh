#!/usr/bin/env bash
# The ground inspector: fly through any stadium model (tools/inspect/ground_inspector.gd).
#   tools/inspect/inspect_ground.sh            opens the MCG
#   tools/inspect/inspect_ground.sh scg        opens the first ground whose name has "scg" in it
#   GODOT=/path/to/godot tools/inspect/inspect_ground.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
exec "${GODOT:-godot}" --path "$ROOT" res://tools/inspect/GroundInspector.tscn -- --ground="${1:-mcg}" "${@:2}"
