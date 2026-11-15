extends SceneTree
## Legacy list and money probe: for each start, the first off-season's
## retirements, expiring contracts and cap per club.
##   godot --headless --path . --script tools/audit/legacy_lists_probe.gd -- 1990 2000


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	var gs = root.get_node("GameState")
	gs.autosave_enabled = false
	gs.save_path = "user://probe_career.save"
	gs.settings_path = "user://probe_settings.cfg"
	var impl = load("res://tools/audit/legacy_lists_probe_impl.gd").new()
	var sets := OS.get_cmdline_user_args()
	if sets.is_empty():
		sets = ["1990", "2000", "2010", "2020", ""]
	for ds in sets:
		impl._probe(gs, "" if str(ds) == "none" else str(ds))
	quit(0)
