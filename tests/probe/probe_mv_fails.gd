extends SceneTree
## Scratch probe (never commit): the match_visual functions that failed or stalled on 11-26.

func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	var gs = root.get_node("GameState")
	gs.autosave_enabled = false
	gs.save_path = "user://test_career.save"
	gs.settings_path = "user://test_settings.cfg"
	var suite = load("res://tests/test_match_visual.gd").new()
	gs.replay_seed = 2027
	root.get_node("GameDB").reload()
	var res: Dictionary = suite._result(42)
	var only := OS.get_environment("MV_ONLY")
	for fn in ["_test_sun_bearing", "_test_ground_models", "_test_ground_backdrop"]:
		if only != "" and not (fn in only.split(",")):
			continue
		var t0 := Time.get_ticks_msec()
		await suite._t(fn)
		print("PROBEMV %s %d ms failures so far %d" % [fn, Time.get_ticks_msec() - t0, suite.failures.size()])
	if only == "" or "_test_three_d_cameras" in only.split(","):
		var t1 := Time.get_ticks_msec()
		await suite._t("_test_three_d_cameras", [res])
		print("PROBEMV _test_three_d_cameras %d ms" % (Time.get_ticks_msec() - t1))
	if only == "" or "_test_tail_seeds" in only.split(","):
		var t2 := Time.get_ticks_msec()
		var truth: Array = await suite._t("_test_truth", [res])
		await suite._t("_test_tail_seeds", [truth])
		print("PROBEMV truth+tail %d ms" % (Time.get_ticks_msec() - t2))
	for f in suite.failures:
		print("PROBEMV FAIL ", f)
	quit(0)
