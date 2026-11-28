extends SceneTree
## Scratch (never commit): run only match_game's _test_kick_in_mark_not_his_disposal on this tree.


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	var gs = root.get_node("GameState")
	gs.autosave_enabled = false
	gs.save_path = "user://test_career.save"
	gs.settings_path = "user://test_settings.cfg"
	var suite = load("res://tests/test_match_game.gd").new()
	suite.failures.clear()
	root.get_node("GameDB").skip_ovr_overrides = true
	root.get_node("GameDB").reload()
	suite._test_kick_in_mark_not_his_disposal()
	print("PKI checks %d, failures %d %s" % [suite.checks, suite.failures.size(), str(suite.failures)])
	quit(0)
