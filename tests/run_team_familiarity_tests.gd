extends SceneTree
## godot --headless --path . --script tests/run_team_familiarity_tests.gd
## Runs the team familiarity suite (TODO row 125) headless, through tools/run_tests.sh.


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	var gs = root.get_node("GameState")
	gs.autosave_enabled = false
	gs.save_path = "user://test_team_familiarity_career.save"
	gs.settings_path = "user://test_team_familiarity_settings.cfg"
	gs.delete_saved_career()
	var suite = load("res://tests/test_team_familiarity.gd").new()
	await suite.run(root)
	gs.delete_saved_career()
	quit(0 if suite.failures.is_empty() else 1)
