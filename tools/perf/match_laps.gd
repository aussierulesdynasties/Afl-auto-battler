extends SceneTree
## tools/perf/match_bench.gd with the step timers (perf_lap.gd) printed at the end:
## the same fixtures and seeds, one match at a time on one thread, in a bench
## tree instrumented from tools/perf/laps_match_targets.txt (bench_refs.sh --match-laps).
##   godot --headless --path <tree> --script tools/perf/match_laps.gd -- [--n 40]


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var n := 40
	var a := OS.get_cmdline_user_args()
	for i in range(a.size() - 1):
		if str(a[i]) == "--n":
			n = int(a[i + 1])
	await process_frame
	var gs = root.get_node("GameState")
	var db = root.get_node("GameDB")
	gs.replay_seed = 4242
	gs.start_season("GEE", db.club_list("GEE"))
	var season = gs.season
	var fixtures: Array = season.fixture[0] + season.fixture[1]
	var lap: GDScript = load("res://tools/perf/perf_lap.gd")
	lap.totals.clear()
	lap.order.clear()
	var total := 0.0
	var events := 0
	for i in range(n):
		var m: Dictionary = fixtures[i % fixtures.size()]
		var sim = season.match_sim(m["home"], m["away"], 1000 + i)
		var t := Time.get_ticks_usec()
		var res: Dictionary = sim.run()
		total += (Time.get_ticks_usec() - t) / 1000.0
		events += (res.get("events", []) as Array).size()
	print("PERF match laps: %d matches, %.1f ms a match (timers on), %d events a match" % [n, total / n, events / n])
	lap.dump()
	quit(0)
