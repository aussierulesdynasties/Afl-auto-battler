extends SceneTree
## Scratch probe (never commit): tail-seed release drift on the standard oval vs the MCG's own size.
## env FIELD=std|mcg

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
	var MM = load("res://scripts/ui/match/MatchMotion.gd")
	var GM = load("res://scripts/ui/match/GroundModels.gd")
	var VG = load("res://scripts/ui/match/VignetteGround.gd")
	var field := OS.get_environment("FIELD")
	var res42: Dictionary = suite._result(42)
	if field == "mcg":
		MM.use_field(GM.field_for(VG.ground_of(res42)))
	else:
		MM.use_field(Vector2.ZERO)
	print("PROBETF field %s half_len %.2f half_wid %.2f ground %s" % [field, MM.HALF_LEN, MM.HALF_WID, VG.ground_of(res42)])
	for seed in [1, 2, 3]:
		var t0 := Time.get_ticks_msec()
		var res: Dictionary = suite._result(seed)
		var played: Dictionary = suite._play(res, res["events"], 1.0 / 60.0 * 4.0, false)
		var worst := 0.0
		var worst_a := {}
		var over := 0
		for a in played["director"].arrivals:
			var e := absf((a["pos"] as Vector2).x - float(a["want_x"]))
			if e > 3.0:
				over += 1
			if e > worst:
				worst = e
				worst_a = a
		print("PROBETF %s seed %d worst %.1f m over3m %d of %d (%d ms) at %s" % [field, seed, worst, over,
				played["director"].arrivals.size(), Time.get_ticks_msec() - t0, str(worst_a)])
	quit(0)
