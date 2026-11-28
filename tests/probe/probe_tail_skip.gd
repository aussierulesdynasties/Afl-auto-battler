extends SceneTree
## Scratch probe (never commit): runs the tail audit (tests/probe/tail_impl.gd) in this process,
## so it can be run with the suites' own environment (AFL_SKIP_OVR_ROWS=1, --fixed-fps 60).

func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	print("PROBESKIP AFL_SKIP_OVR_ROWS=%s skip=%s" % [OS.get_environment("AFL_SKIP_OVR_ROWS"),
			str(root.get_node("GameDB").skip_ovr_overrides)])
	load("res://tests/probe/tail_impl.gd").new().run()
	quit(0)
