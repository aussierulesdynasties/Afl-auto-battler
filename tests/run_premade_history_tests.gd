extends SceneTree
## godot --headless --path . --script tests/run_premade_history_tests.gd
## Runs the pre-made history suite headless, through tools/run_tests.sh.


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	var gs = root.get_node("GameState")
	gs.autosave_enabled = false
	gs.save_path = "user://test_premade_history_career.save"
	gs.settings_path = "user://test_premade_history_settings.cfg"
	gs.delete_saved_career()
	var suite = load("res://tests/test_premade_history.gd").new()
	suite.run()
	quit(0 if suite.failures.is_empty() else 1)
