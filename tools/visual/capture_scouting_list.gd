extends SceneTree
## The scouting list (row 130) for a look: a fresh career per club, a coach
## holding the pressing game and the father figure, three prospects listed
## (two of them watched for twelve weeks), the screen at its top and one screen
## down, then a 1280 px PC view. Needs a real renderer and a window; never
## touches a real save.
##   godot --path . --windowed --script tools/visual/capture_scouting_list.gd -- --out DIR --clubs FRE,MEL
## Writes DIR/scout_<club>.png, DIR/scout_<club>_down.png and DIR/scout_<club>_pc.png.


var SL
var _phone_window := Vector2i.ZERO


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
	SL = load("res://scripts/state/ScoutingList.gd")
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
		var pool: Array = SL.pool(state)
		var reads: Dictionary = state.prospect_reads(pool)
		var order := pool.duplicate()
		order.sort_custom(func(x, y): return int(reads[str(x["id"])]["rank"]) < int(reads[str(y["id"])]["rank"]))
		SL.add(state, str(order[2]["id"]))
		SL.add(state, str(order[9]["id"]))
		for w in range(12):
			SL.week(state)
		# Twelve rounds played, as the twelve weeks of watching say.
		state.season.round_index = 12
		SL.add(state, str(order[20]["id"]))
		for size in [Vector2i(390, 844), Vector2i(1280, 800)]:
			await _size_window(size)
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


## The window at `size` canvas pixels. The canvas is laid out in
## device-independent pixels, so on a scaled display the window grows by the
## display scale until the canvas is the size a player gets (as capture_captaincy).
func _size_window(size: Vector2i) -> void:
	if _phone_window == Vector2i.ZERO:
		_phone_window = DisplayServer.window_get_size()
	if size.x < 760:
		# A phone: the canvas itself is set, as the game sizes a phone's view.
		DisplayServer.window_set_size(_phone_window)
		root.size = size
		await _frames(10)
	else:
		DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
		DisplayServer.window_set_size(size)
		root.size = size
		await _frames(10)
		var win := Vector2(size)
		for i in range(4):
			var factor := float(size.x) / maxf(1.0, root.get_visible_rect().size.x)
			if factor <= 1.02:
				break
			win *= factor
			DisplayServer.window_set_size(Vector2i(win))
			root.size = Vector2i(win)
			await _frames(10)
	print("canvas ", root.get_visible_rect().size)


func _save(path: String) -> void:
	root.get_viewport().get_texture().get_image().save_png(path)
