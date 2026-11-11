extends SceneTree
## The 3-season bench of weeks (T8.Q20): a seeded autopilot career played week
## by week, the time split by the steps of GameState.advance() and the
## off-season, and a fingerprint of every result and the save, so a speed-up
## can be proved to change nothing. Headless; isolate the save folder with APPDATA.
##   godot --headless --path . --script tools/perf/weeks_bench.gd -- [--seasons 3] [--club GEE] [--seed 4242] [--plain]
## --plain times GameState.advance() whole (no split), for trees that predate its steps.
## Prints PERF lines (ms per step, weeks and off-season totals) and HASH lines
## (one a season of results, one of the final save). The work is in
## weeks_bench_impl.gd, loaded once the autoloads exist.


func _initialize() -> void:
	seed(2026)
	_run.call_deferred()


func _run() -> void:
	await process_frame
	var lib: GDScript = load("res://tools/perf/weeks_bench_impl.gd")
	lib.new().run(root)
	quit(0)
