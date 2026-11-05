extends SceneTree
## One worker of the local balance harness (tools/balance.sh). Plays a slice of
## seeded matches headless and writes one JSON line per match. Measurement only.
##
##   godot --headless --path . --script tools/balance/balance_worker.gd -- \
##       --from 0 --count 250 --out runs/a_0.jsonl [--on a,b] [--off c] [--weather wet]
##       [--set runaway_gain=6,runaway_decay=0.985]   (MatchSim vars, for screening a knob)
##
## Seed i plays two real 2026 lists picked from i (every pairing comes round),
## home side alternating, match seed 500000 + i. The same --from/--count in two
## arms plays the same matches, so arms pair seed by seed.


func _initialize() -> void:
	seed(2026)
	_run.call_deferred()


func _run() -> void:
	await process_frame
	var a := OS.get_cmdline_user_args()
	var from := 0
	var count := 100
	var out := "user://balance.jsonl"
	var on: PackedStringArray = []
	var off: PackedStringArray = []
	var weather := "perfect"
	var sets := ""
	for i in range(a.size() - 1):
		match str(a[i]):
			"--from": from = int(a[i + 1])
			"--count": count = int(a[i + 1])
			"--out": out = str(a[i + 1])
			"--on": on = str(a[i + 1]).split(",", false)
			"--off": off = str(a[i + 1]).split(",", false)
			"--weather": weather = str(a[i + 1])
			"--set": sets = str(a[i + 1])
	var body = load("res://tools/balance/balance_body.gd").new()
	var code: int = body.play(from, count, out, on, off, weather, body.parse_sets(sets))
	quit(code)
