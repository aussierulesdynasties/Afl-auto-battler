extends SceneTree
## The scouting list (row 130) for a look: a fresh career per club, a coach
## holding the pressing game and the father figure, three prospects listed
## (two of them watched for twelve weeks), the screen at its top and one screen
## down, then a 1280 px PC view. Needs a real renderer and a window; never
## touches a real save.
##   godot --path . --windowed --script tools/visual/capture_scouting_list.gd -- --out DIR --clubs FRE,MEL
## Writes DIR/scout_<club>.png, DIR/scout_<club>_down.png and DIR/scout_<club>_pc.png.


func _initialize() -> void:
	_run.call_deferred()


func _frames(n := 8) -> void:
	for i in range(n):
		await process_frame


func _run() -> void:
	var out := "."
	var clubs := PackedStringArray(["FRE", "MEL"])
	var a := OS.get_cmdline_user_args()
	for i in range(a.size() - 1):
		match str(a[i]):
			"--out":
				out = str(a[i + 1])
			"--clubs":
				clubs = str(a[i + 1]).split(",")
	await process_frame
	var state: Node = root.get_node("GameState")
	var db: Node = root.get_node("GameDB")
	state.autosave_enabled = false
	state.save_path = "user://capture_scouting_list.save"
	state.settings_path = "user://capture_scouting_list.cfg"
	for club in clubs:
		state.reset()
		state.career_seed = 42
		state.replay_seed = 42
		state.start_season(club, db.club_list(club))
		state.tutorials = false
		var held := {"s": "DS", "p": "FATH"}
		state.coach_arch = {"s": {"DS": 10.0}, "p": {"FATH": 10.0}, "held": held,
				"tally": {"plans": {}, "calls": {}}}
		var pool: Array = ScoutingList.pool(state)
		var reads: Dictionary = state.prospect_reads(pool)
		var order := pool.duplicate()
		order.sort_custom(func(x, y): return int(reads[str(x["id"])]["rank"]) < int(reads[str(y["id"])]["rank"]))
		ScoutingList.add(state, str(order[2]["id"]))
		ScoutingList.add(state, str(order[9]["id"]))
		for w in range(12):
			ScoutingList.week(state)
		ScoutingList.add(state, str(order[20]["id"]))
		for size in [Vector2i(390, 844), Vector2i(1280, 800)]:
			root.size = size
			await _frames(6)
			var ui: Control = load("res://scenes/ScoutingScene.tscn").instantiate()
			root.add_child(ui)
			await _frames(30)
			var stem := "%s/scout_%s" % [out, club]
			if size.x > 800:
				_save(stem + "_pc.png")
			else:
				_save(stem + ".png")
				var sc := ui.find_child("ScoutScroll", true, false) as ScrollContainer
				if sc != null:
					sc.scroll_vertical = int(sc.size.y) - 60
					await _frames(10)
					_save(stem + "_down.png")
			print("captured ", stem, " ", size)
			ui.queue_free()
			await _frames(3)
	quit()


func _save(path: String) -> void:
	root.get_viewport().get_texture().get_image().save_png(path)
