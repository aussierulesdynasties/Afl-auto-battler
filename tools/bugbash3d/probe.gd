extends SceneTree
## Runs one match_visual test function:  godot --headless --fixed-fps 60 --path . --script tools/bugbash3d/probe.gd -- _test_name


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	await load("res://tools/bugbash3d/probe_impl.gd").new().run(OS.get_cmdline_user_args())
	quit(0)
