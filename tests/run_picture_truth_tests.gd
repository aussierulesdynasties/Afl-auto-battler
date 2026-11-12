extends SceneTree
## godot --headless --path . --script tests/run_picture_truth_tests.gd
## T8.85 (P-76): a full seeded match at 8x, the picture checked against the
## truth at every tick (tests/test_picture_truth.gd).
## Run a headless editor import first on a fresh clone to register global classes.


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	_isolate_saves()
	# A suite that fails to compile must fail the run, not hang it.
	var script = load("res://tests/test_picture_truth.gd")
	if script == null or not script.can_instantiate():
		push_error("Could not load res://tests/test_picture_truth.gd")
		quit(1)
		return
	var suite = script.new()
	await suite.run(self)
	quit(0 if suite.failures.is_empty() else 1)


## Never touch a real career save or settings file from a test run.
func _isolate_saves() -> void:
	var gs = root.get_node("GameState")
	gs.autosave_enabled = false
	gs.save_path = "user://test_career.save"
	gs.settings_path = "user://test_settings.cfg"
