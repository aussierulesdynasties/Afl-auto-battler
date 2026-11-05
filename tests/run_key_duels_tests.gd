extends SceneTree
## godot --headless --path . --script tests/run_key_duels_tests.gd
## Key forward v key defender (row 94, T8.Q6; tests/test_key_duels.gd).
## Seeded by design: every match is MatchSim.new(..., 9401 + i), an explicit seed.


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	var script = load("res://tests/test_key_duels.gd")
	if script == null or not script.can_instantiate():
		push_error("Could not load res://tests/test_key_duels.gd")
		quit(1)
		return
	var suite = script.new()
	await suite.run(self)
	quit(0 if suite.failures.is_empty() else 1)
