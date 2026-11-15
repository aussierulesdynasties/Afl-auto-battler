extends SceneTree
## The match screen with Settings > Match view on "3D oval" (row 197): a first-match career
## game as the coach watches it, saved at a few moments of play. Never touches a real save.
##   --out PREFIX  (default match3d)   --size WxH (default 540x1200, a phone's shape)
##   --club CODE (default FRE)   --seed N (default 7)   --at a,b,c  seconds of play (default 4,12,24)
##   --plan KEY  the coach's game plan (e.g. defensive: the press wash shows)

var _w := 540
var _h := 1200


func _initialize() -> void:
	_run.call_deferred()


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame


func _run() -> void:
	OS.low_processor_usage_mode = false
	var out := "match3d"
	var club := "FRE"
	var seed := 7
	var at := [4.0, 12.0, 24.0]
	var plan := ""
	var a := OS.get_cmdline_user_args()
	for i in range(a.size()):
		match str(a[i]):
			"--out":
				out = str(a[i + 1])
			"--size":
				var wh := str(a[i + 1]).split("x")
				_w = int(wh[0])
				_h = int(wh[1])
			"--plan":
				plan = str(a[i + 1])
			"--club":
				club = str(a[i + 1])
			"--seed":
				seed = int(a[i + 1])
			"--at":
				at = []
				for s in str(a[i + 1]).split(","):
					at.append(float(s))
	await process_frame
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	state.autosave_enabled = false
	state.save_path = "user://capture_match3d.save"
	state.settings_path = "user://capture_match3d.cfg"
	state.reset()
	state.career_seed = seed
	state.replay_seed = seed
	state.set_setting("seen_training_intro", true)
	state.set_vignettes_on(false)
	state.set_match_3d_on(true)
	state.start_season(club, db.club_list(club))
	if plan != "":
		state.club_plan = plan
	if not state.prepare_interactive_match():
		push_error("no match to play")
		quit(1)
		return
	load("res://scripts/ui/UiKit.gd").apply_appearance("dark")
	DisplayServer.window_set_size(Vector2i(_w, _h))
	root.size = Vector2i(_w, _h)
	var scene = load("res://scenes/MatchScene.tscn").instantiate()
	root.add_child(scene)
	await _frames(20)
	var pitch = scene._pitch
	print("3D on: ", pitch._oval3d != null, " viewport ", pitch._vp3d.size if pitch._vp3d else Vector2i.ZERO,
			" pitch ", pitch.size)
	var t0 := Time.get_ticks_msec()
	for k in range(at.size()):
		while (Time.get_ticks_msec() - t0) / 1000.0 < float(at[k]):
			await process_frame
			# The pre-match calls (and each break's) end with Start, as the coach taps it.
			var start = scene.find_child("StartQuarter", true, false)
			if start != null and start.is_visible_in_tree():
				start.pressed.emit()
				continue
		await process_frame
		var img := root.get_viewport().get_texture().get_image()
		img.convert(Image.FORMAT_RGBA8)
		var path := "%s_%d.png" % [out, k]
		img.save_png(path)
		print("wrote ", path, " at ", at[k], " s, events ", pitch.current_index(), ", period ", pitch.period)
	quit(0)
