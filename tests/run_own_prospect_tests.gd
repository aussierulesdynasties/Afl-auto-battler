extends SceneTree
## godot --headless --path . --script tests/run_own_prospect_tests.gd
## Row 64: the created prospect's first National Draft and story beats.


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	_isolate_saves()
	# A suite that fails to compile must fail the run, not hang it.
	var script = load("res://tests/test_own_prospect.gd")
	if script == null or not script.can_instantiate():
		push_error("Could not load res://tests/test_own_prospect.gd")
		quit(1)
		return
	var suite = script.new()
	await suite.run()
	quit(0 if suite.failures.is_empty() else 1)


## Never touch a real career save or settings file from a test run.
func _isolate_saves() -> void:
	var gs = root.get_node("GameState")
	gs.autosave_enabled = false
	gs.save_path = "user://test_own_prospect.save"
	gs.settings_path = "user://test_settings.cfg"
