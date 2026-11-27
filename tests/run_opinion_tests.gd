extends SceneTree
## godot --headless --path . --script tests/run_opinion_tests.gd
## The opinion engine (Opinion.gd, relationship overhaul Phase 1): the permanent
## part and the live, fading marks, older saves, the marks every club's coach
## leaves after a round and morale drifting towards opinion. The checks live in
## tests/opinion_body.gd, loaded by path once the autoloads exist.
## Seeded: replay_seed 2027.


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	var suite = load("res://tests/opinion_body.gd").new()
	await suite.go(self)
	quit(1 if not suite._failures.is_empty() else 0)
