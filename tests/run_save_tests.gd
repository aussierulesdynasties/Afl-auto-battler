extends SceneTree
## godot --headless --path . --script tests/run_save_tests.gd
## Run a headless editor import first on a fresh clone to register global classes.


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	_isolate_saves()
	# A suite that fails to compile must fail the run, not hang it.
	var script = load("res://tests/test_save.gd")
	if script == null or not script.can_instantiate():
		push_error("Could not load res://tests/test_save.gd")
		quit(1)
		return
	var suite = script.new()
	suite.run()
	CareerSave.delete(gs_save_path())
	DirAccess.remove_absolute(root.get_node("GameState").settings_path)
	quit(0 if suite.failures.is_empty() else 1)


## Never touch a real career save or settings file from a test run.
func _isolate_saves() -> void:
	var gs = root.get_node("GameState")
	gs.autosave_enabled = false
	# Its own files per process: every worktree shares one user:// folder and
	# most suites write user://test_career.save, so a suite running anywhere
	# else at the same time replaced or deleted this one's save between its
	# save and load (2026-11-03: "the season-2 save loads" failed locally).
	var tag := OS.get_process_id()
	gs.save_path = "user://test_save_suite_%d.save" % tag
	gs.settings_path = "user://test_save_suite_%d.cfg" % tag
	gs.show_real_names = false


func gs_save_path() -> String:
	return str(root.get_node("GameState").save_path)
