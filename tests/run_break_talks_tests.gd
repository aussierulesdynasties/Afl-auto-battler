extends SceneTree
## godot --headless --path . --script tests/run_break_talks_tests.gd
## Quarter-break talks (BreakTalks, director 2026-11-21): the dice rules, the
## sim's once-a-break sit-down and half-time speech, rival clubs making the
## same calls, and the break screen on a phone with real taps. The checks live
## in tests/break_talks_body.gd, loaded by path once the autoloads exist.


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	var suite = load("res://tests/break_talks_body.gd").new()
	await suite.go(self)
	quit(1 if not suite._failures.is_empty() else 0)
