extends SceneTree
## How often a scouting read's range misses the truth, and by how much, at
## each recruiting budget level (row T1.R26 L2: the budget line states it).
## godot --headless --path . --script tools/measure_scout_miss.gd


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	load("res://tools/measure_scout_miss_impl.gd").new().run(root.get_node("GameDB"))
	quit()
