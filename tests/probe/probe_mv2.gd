extends SceneTree
## Scratch (never commit): match_visual's _test_ground_backdrop and _test_contacts alone,
## on the suite's seed (2027) and replay (_result(42)), every check printed.


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	var gs = root.get_node("GameState")
	gs.autosave_enabled = false
	gs.save_path = "user://test_career.save"
	gs.settings_path = "user://test_settings.cfg"
	gs.replay_seed = 2027
	root.get_node("GameDB").reload()
	var suite = load("res://tests/probe/mv_spy.gd").new()
	print("PMV backdrop")
	suite._test_ground_backdrop()
	var res: Dictionary = suite._result(42)
	print("PMV contacts")
	suite._test_contacts(res)
	print("PMV done %d checks, %d failures" % [suite.checks, suite.failures.size()])
	quit(0 if suite.failures.is_empty() else 1)
