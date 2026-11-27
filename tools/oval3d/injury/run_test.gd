extends SceneTree
## One match_visual test function, alone:  godot --headless --fixed-fps 60 --path . --script tools/oval3d/injury/run_test.gd -- _test_name


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	var t = load("res://tests/test_match_visual.gd").new()
	root.get_node("GameState").replay_seed = t.SUITE_SEED
	root.get_node("GameDB").reload()
	for n in OS.get_cmdline_user_args():
		await t.call(str(n))
	print("PROBE checks=%d failures=%s" % [t.checks, str(t.failures)])
	quit(0)
