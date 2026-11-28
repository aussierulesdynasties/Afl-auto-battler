extends SceneTree
## Scratch probe (never commit): every event of seed ED_SEED, one line each, set up exactly as
## probe_board.gd, so two checkouts' dumps can be diffed for the first event they disagree on.

func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	var gs = root.get_node("GameState")
	gs.autosave_enabled = false
	gs.save_path = "user://test_career.save"
	gs.settings_path = "user://test_settings.cfg"
	var suite = load("res://tests/test_match_visual.gd").new()
	gs.replay_seed = 2027
	root.get_node("GameDB").reload()
	suite._result(42)
	var seed := int(OS.get_environment("ED_SEED")) if OS.get_environment("ED_SEED") != "" else 1
	var res: Dictionary = suite._result(seed)
	var evs: Array = res["events"]
	for i in range(evs.size()):
		var e: Dictionary = evs[i]
		print("ED %d %s %d %d %s | %s" % [i, str(e.get("kind", "")), int(e.get("side", -1)), int(e.get("num", 0)),
				str(e.get("name", "")), str(e.get("text", ""))])
	quit(0)
