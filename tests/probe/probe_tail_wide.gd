extends SceneTree
## Scratch probe (never commit): runs tests/probe/tail_wide_impl.gd in this process.

func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	load("res://tests/probe/tail_wide_impl.gd").new().run()
	quit(0)
