extends SceneTree
## Scratch (never commit): runs test_match_game's _test_play_through_three alone, every check printed.


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	var gs = root.get_node("GameState")
	gs.autosave_enabled = false
	gs.save_path = "user://test_career.save"
	gs.settings_path = "user://test_settings.cfg"
	var gdb = root.get_node("GameDB")
	gdb.skip_ovr_overrides = true
	gdb.reload()
	var suite = load("res://tests/probe/pt3_spy.gd").new()
	var t0 := Time.get_ticks_msec()
	suite._test_play_through_three()
	print("PT3 done %d checks, %d failures, %d s" % [suite.checks, suite.failures.size(), (Time.get_ticks_msec() - t0) / 1000])
	quit(0 if suite.failures.is_empty() else 1)
