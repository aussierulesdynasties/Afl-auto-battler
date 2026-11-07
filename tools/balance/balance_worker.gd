extends SceneTree
## One worker of the local balance harness (tools/balance.sh). Plays a slice of
## seeded matches headless and writes one JSON line per match. Measurement only.
##
##   godot --headless --path . --script tools/balance/balance_worker.gd -- \
##       --from 0 --count 250 --out runs/a_0.jsonl [--weather wet]
##       [--set runaway_gain=6,runaway_decay=0.985]   (MatchSim vars, for screening a knob)
##       [--start real]   (the 2027 round-1 lists of a real-lists career, after the 2026 draft)
##       [--setup league|coached]   (background-match or coached-match setup; see balance_body.gd)
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
	var weather := "perfect"
	var sets := ""
	var start := ""
	var setup := ""
	for i in range(a.size() - 1):
		match str(a[i]):
			"--from": from = int(a[i + 1])
			"--count": count = int(a[i + 1])
			"--out": out = str(a[i + 1])
			"--weather": weather = str(a[i + 1])
			"--set": sets = str(a[i + 1])
			"--start": start = str(a[i + 1])
			"--setup": setup = str(a[i + 1])
	# The feature switches are gone (director, 2026-11-06): an old --on/--off
	# call would play two identical arms and report B-A of 0, so refuse it.
	for arg in a:
		if str(arg) == "--on" or str(arg) == "--off":
			push_error("balance: --on/--off are gone (no feature switches); pair main vs the branch with --a-root")
			quit(2)
			return
	var body = load("res://tools/balance/balance_body.gd").new()
	body.start = start
	if not setup in ["", "league", "coached"]:
		push_error("balance: --setup is league or coached")
		quit(2)
		return
	body.setup = setup
	var code: int = body.play(from, count, out, weather, body.parse_sets(sets))
	quit(code)
