extends SceneTree
## How an in-match injury falls in the director's time (row 202 2e, injuries in 3D):
##   godot --headless --path . --script tools/oval3d/injury/probe_timing.gd -- SEEDS
## For every injury: the director seconds from the hurt man's last part in the play to his
## interchange, and how many events lie between. Prints INJ lines and the event keys that name a man.

func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	await load("res://tools/oval3d/injury/probe_timing_impl.gd").new().run(OS.get_cmdline_user_args())
	quit(0)
