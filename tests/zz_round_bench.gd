extends SceneTree
## Scratch (bug bash, never commit): loads the bench body after the autoloads exist.

func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	var B = load("res://tests/zz_save_bench_body.gd").new()
	B.run(self)
	quit(0)
