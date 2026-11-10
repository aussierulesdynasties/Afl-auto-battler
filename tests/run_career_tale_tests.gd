extends SceneTree
## godot --headless --path . --script tests/run_career_tale_tests.gd
## A player's career story (tests/test_career_tale.gd). Run a headless editor
## import first on a fresh clone to register global classes.


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	var script = load("res://tests/test_career_tale.gd")
	if script == null or not script.can_instantiate():
		push_error("Could not load res://tests/test_career_tale.gd")
		quit(1)
		return
	var suite = script.new()
	await suite.run(self)
	quit(0 if suite.failures.is_empty() else 1)
