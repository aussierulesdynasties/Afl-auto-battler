extends SceneTree
## The match screen with Settings > Match view on "3D oval" (row 197): a first-match career
## game as the coach watches it, saved at a few moments of play. Never touches a real save.
##   --out PREFIX  (default match3d)   --size WxH (default 540x1200, a phone's shape)
##   --club CODE (default FRE)   --seed N (default 7)   --at a,b,c  seconds of play (default 4,12,24)
##   --plan KEY  the coach's game plan (e.g. defensive: the press wash shows)
##   --replay    instead of --at: one frame 1 s into the first goal's replay (rule 2.96)
##   --film N    instead of --at: N seconds of the match screen, frame by frame, for Godot's movie
##               writer (run with --write-movie OUT.avi --fixed-fps 30); the coach taps the picture
##               1 s into the second replay. Prints each camera cut as "CUT frame shot", and each
##               change of the main camera's zoom as "ZOOM frame tv|zooming|wide".

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
	var replay := false
	var film := 0.0
	var windows: Array = []  # [a, b] frame ranges of the film saved as PNGs
	var a := OS.get_cmdline_user_args()
	for i in range(a.size()):
		match str(a[i]):
			"--out":
				out = str(a[i + 1])
			"--size":
				var wh := str(a[i + 1]).split("x")
				_w = int(wh[0])
				_h = int(wh[1])
			"--replay":
				replay = true
			"--film":
				film = float(a[i + 1])
			"--windows":
				for w in str(a[i + 1]).split(","):
					windows.append([int(w.split("-")[0]), int(w.split("-")[1])])
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
	if film > 0.0:
		var shot := ""
		var zoom := ""  # rule 2.111: "tv" height, "wide" (57 m, sky) or "zooming" between them
		var replays := 0
		var was := false
		var tap_at := -1
		for f in range(int(film * 30.0)):
			await process_frame
			var go = scene.find_child("StartQuarter", true, false)
			if go != null and go.is_visible_in_tree():
				go.pressed.emit()
			# An in-game call stops the play: the coach takes its first option, as the default.
			var sim = state.pending_sim
			var card = scene.find_child("MomentCard", true, false)
			if card != null and is_instance_valid(card) and sim != null and not sim.pending_moment.is_empty():
				print("MOMENT ", f)
				scene.call("_on_moment_choice", int(sim.pending_moment.get("default", 0)))
			var tv = pitch._tv
			var now: String = "replay" if tv.replaying else ("close" if tv._close_who >= 0 else tv.shot)
			if now != shot:
				print("CUT ", f, " ", now)
				shot = now
			var z := "wide" if tv._zoom >= 1.0 else ("tv" if tv._zoom <= 0.0 else "zooming")
			if z != zoom:
				print("ZOOM ", f, " ", z)
				zoom = z
			if tv.replaying and not was:
				replays += 1
				if replays == 2:
					tap_at = f + 30
			was = tv.replaying
			for w in windows:
				if f >= int(w[0]) and f <= int(w[1]):
					var img := root.get_viewport().get_texture().get_image()
					img.convert(Image.FORMAT_RGB8)
					img.save_png("%s_%05d.png" % [out, f])
			if f == tap_at and tv.replaying:
				print("TAP ", f)
				# A finger on the middle of the picture, through the window like a phone's touch.
				for down in [true, false]:
					var ev := InputEventMouseButton.new()
					ev.button_index = MOUSE_BUTTON_LEFT
					ev.pressed = down
					ev.position = pitch.get_global_rect().get_center()
					ev.global_position = ev.position
					root.push_input(ev)
		quit(0)
		return
	if replay:
		var t1 := -1
		while t1 < 0 or Time.get_ticks_msec() - t1 < 1000:
			await process_frame
			var go = scene.find_child("StartQuarter", true, false)
			if go != null and go.is_visible_in_tree():
				go.pressed.emit()
			if t1 < 0 and pitch._tv.replaying:
				t1 = Time.get_ticks_msec()
		var shot := root.get_viewport().get_texture().get_image()
		shot.convert(Image.FORMAT_RGBA8)
		shot.save_png("%s_replay.png" % out)
		print("wrote %s_replay.png, replaying " % out, pitch._tv.replaying)
		quit(0)
		return
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
