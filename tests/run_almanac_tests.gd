extends SceneTree
## godot --headless --path . --script tests/run_almanac_tests.gd
## Runs the club almanac suite headless.
## Run through tools/run_tests.sh like the other suites.


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	_isolate_saves()
	var script = load("res://tests/test_almanac.gd")
	if script == null or not script.can_instantiate():
		push_error("Could not load res://tests/test_almanac.gd")
		quit(1)
		return
	var suite = script.new()
	suite.run()
	quit(0 if suite.failures.is_empty() else 1)


## Never touch a real career save or settings file from a test run.
func _isolate_saves() -> void:
	var gs = root.get_node("GameState")
	gs.autosave_enabled = false
	gs.save_path = "user://test_almanac_career.save"
	gs.settings_path = "user://test_almanac_settings.cfg"
	gs.delete_saved_career()
