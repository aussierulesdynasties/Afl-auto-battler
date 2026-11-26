extends SceneTree
## Bug bash for the 3D match view: plays whole career matches on the real match screen with
## Settings > Match view on 3D, at a chosen ground, weather, time and Graphics level, and checks
## every frame for what a watcher would call a bug. Never touches a real save.
##   godot --headless --fixed-fps 30 --path . --script tools/bugbash3d/play3d.gd -- \
##       --club FRE --seed 7 --ground "MCG" --weather wet --time night --quality low --speed 4
## Prints one "FAULT kind frame detail" line per fault (the first few of each kind, then a count)
## and "DONE frames=N final=true|false" at the end.

var _impl


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	_impl = load("res://tools/bugbash3d/play3d_impl.gd").new()
	await _impl.run(self)
